import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import type { WorkspaceProps } from "../../types";
import {
  currentStep,
  typeLabel,
  type NetNode,
  type NetworkConfig,
  type NetworkState,
  type NodeType,
} from "./model";

/**
 * Renderer 3D của network.packet_routing (M8 Slice 2 — PoC).
 *
 * CÙNG module, CÙNG hợp đồng WorkspaceProps với renderer 2D: đọc CÙNG
 * NetworkState (topology + route BFS + steps + cursor) — KHÔNG có engine 3D,
 * KHÔNG có BFS thứ hai, KHÔNG có prediction riêng (PredictionBar nằm ngoài
 * renderer, dùng chung).
 *
 * SỞ HỮU DỮ LIỆU (bất biến renderer-neutral, M7.FREEZE):
 * - Engine state nói "gói tin Ở NÚT NÀO" (`steps[].packetAt` = id nút).
 * - MỌI toạ độ x/y/z, camera, mesh, material, interpolation là TRÌNH BÀY —
 *   sống trong closure/ref của component này, KHÔNG BAO GIỜ vào store/state.
 * - Renderer được phép NỘI SUY HÌNH ẢNH giữa hai bước ngữ nghĩa (gói tin lướt
 *   từ nút A sang nút B) nhưng không bịa ra trạng thái ngữ nghĩa trung gian:
 *   sự thật vẫn là `packetAt` của bước hiện tại.
 */

type Props = WorkspaceProps<NetworkConfig, NetworkState>;

export interface Pos3D {
  x: number;
  y: number;
  z: number;
}

/** Khoảng cách giữa hai nút liền kề trên một hàng (đơn vị thế giới 3D). */
const SPACING = 3;
/** Hàng nút ngoài route lùi về phía sau — chiều SÂU là giá trị 3D thêm vào. */
const OFF_ROUTE_Z = -3.5;

/**
 * Bố cục 3D — RENDERER-OWNED, tất định, thuần (export để test).
 * Cùng ngữ nghĩa với layout2d (hàng route + hàng ngoài route) nhưng dùng trục Z:
 * nút trên đường đi nằm hàng trước, nút ngoài đường đi lùi vào chiều sâu.
 */
export function layout3d(nodes: NetNode[], route: string[]): Record<string, Pos3D> {
  const pos: Record<string, Pos3D> = {};
  const half = (route.length - 1) / 2;
  route.forEach((id, i) => {
    pos[id] = { x: (i - half) * SPACING, y: 0, z: 0 };
  });
  const off = nodes.filter((n) => !route.includes(n.id));
  const offHalf = (off.length - 1) / 2;
  off.forEach((n, i) => {
    pos[n.id] = { x: (i - offHalf) * SPACING, y: 0, z: OFF_ROUTE_Z };
  });
  return pos;
}

/** Màu 3D theo LOẠI nút — hằng renderer (bản hex của palette 2D). */
const NODE_COLOR_3D: Record<NodeType, number> = {
  client: 0x38bdf8, // sky
  router: 0x8b5cf6, // purple
  server: 0x34d399, // green
  switch: 0x2dd4bf, // teal
  isp: 0xfb923c, // orange
};

const PACKET_COLOR = 0xec4899; // pink — khớp chấm gói tin 2D
const ROUTE_COLOR = 0x2563eb; // primary — cạnh trên đường đi
const LINK_COLOR = 0x9ca3af; // hairline — cạnh thường
const NODE_RADIUS = 0.55;

/** Thông điệp khi WebGL không khởi tạo được — fallback tử tế, không văng lỗi. */
export const WEBGL_FALLBACK_MESSAGE =
  "Không khởi tạo được chế độ 3D trên thiết bị này (WebGL không khả dụng). " +
  "Mô phỏng vẫn hoạt động đầy đủ ở chế độ 2D — hãy bấm nút 2D phía trên.";

/**
 * Tạo WebGLRenderer an toàn: thất bại (thiết bị không có WebGL) → null,
 * KHÔNG ném lỗi ra ngoài (export để test hành vi graceful).
 */
export function tryCreateWebGLRenderer(): THREE.WebGLRenderer | null {
  try {
    return new THREE.WebGLRenderer({ antialias: true, alpha: true });
  } catch {
    return null;
  }
}

/** Sprite nhãn chữ (canvas texture) — không cần thư viện font ngoài. */
function makeLabelSprite(title: string, sub: string): THREE.Sprite {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 96;
  const ctx = canvas.getContext("2d")!;
  ctx.textAlign = "center";
  // Viền tối + chữ sáng → đọc được trên cả nền sáng lẫn tối.
  ctx.font = "bold 34px system-ui, sans-serif";
  ctx.lineWidth = 6;
  ctx.strokeStyle = "rgba(15,23,42,0.9)";
  ctx.strokeText(title, 128, 40);
  ctx.fillStyle = "#ffffff";
  ctx.fillText(title, 128, 40);
  ctx.font = "26px system-ui, sans-serif";
  ctx.strokeText(sub, 128, 78);
  ctx.fillStyle = "#e2e8f0";
  ctx.fillText(sub, 128, 78);
  const texture = new THREE.CanvasTexture(canvas);
  const material = new THREE.SpriteMaterial({ map: texture, depthTest: false });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(2.4, 0.9, 1);
  return sprite;
}

/** Hình trụ nối hai điểm — cạnh route cần "dày" (WebGL line luôn 1px). */
function makeRouteEdge(a: Pos3D, b: Pos3D): THREE.Mesh {
  const from = new THREE.Vector3(a.x, a.y, a.z);
  const to = new THREE.Vector3(b.x, b.y, b.z);
  const dir = new THREE.Vector3().subVectors(to, from);
  const geometry = new THREE.CylinderGeometry(0.06, 0.06, dir.length(), 8);
  const material = new THREE.MeshLambertMaterial({ color: ROUTE_COLOR });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.copy(from).add(dir.multiplyScalar(0.5));
  mesh.quaternion.setFromUnitVectors(
    new THREE.Vector3(0, 1, 0),
    new THREE.Vector3().subVectors(to, from).normalize(),
  );
  return mesh;
}

/** Handle renderer-owned — sống trong ref, KHÔNG BAO GIỜ vào store. */
interface SceneHandles {
  renderer: THREE.WebGLRenderer;
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  positions: Record<string, Pos3D>;
  packet: THREE.Mesh;
  packetTarget: THREE.Vector3;
  highlight: THREE.Mesh;
  raf: number;
  observer: ResizeObserver;
  home: { position: THREE.Vector3; target: THREE.Vector3 };
}

function disposeScene(h: SceneHandles, container: HTMLElement): void {
  cancelAnimationFrame(h.raf);
  h.observer.disconnect();
  h.controls.dispose();
  h.scene.traverse((obj) => {
    if (obj instanceof THREE.Mesh || obj instanceof THREE.Line) {
      obj.geometry.dispose();
      const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
      for (const m of mats) m.dispose();
    }
    if (obj instanceof THREE.Sprite) {
      obj.material.map?.dispose();
      obj.material.dispose();
    }
  });
  h.renderer.dispose();
  if (h.renderer.domElement.parentElement === container) {
    container.removeChild(h.renderer.domElement);
  }
}

export function Network3DWorkspace({ state }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const handlesRef = useRef<SceneHandles | null>(null);
  const [webglFailed, setWebglFailed] = useState(false);

  const step = currentStep(state);

  // ── Dựng scene khi TOPOLOGY đổi (goToStep giữ nguyên tham chiếu nodes/links
  // nên bước đi KHÔNG rebuild scene — chỉ effect gói tin phía dưới chạy).
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const renderer = tryCreateWebGLRenderer();
    if (!renderer) {
      setWebglFailed(true);
      return;
    }

    const scene = new THREE.Scene();
    const positions = layout3d(state.nodes, state.route);

    // Ánh sáng tối giản
    scene.add(new THREE.AmbientLight(0xffffff, 1.1));
    const sun = new THREE.DirectionalLight(0xffffff, 1.6);
    sun.position.set(5, 10, 7);
    scene.add(sun);

    // Lưới nền mờ — mốc không gian để chiều sâu đọc được
    const grid = new THREE.GridHelper(24, 24, 0x94a3b8, 0xcbd5e1);
    (grid.material as THREE.Material).opacity = 0.35;
    (grid.material as THREE.Material).transparent = true;
    grid.position.y = -1;
    scene.add(grid);

    // Nút: cầu màu theo loại; nguồn/đích thêm vòng đế phân biệt
    for (const n of state.nodes) {
      const p = positions[n.id];
      const isEnd = n.id === state.source || n.id === state.destination;
      const sphere = new THREE.Mesh(
        new THREE.SphereGeometry(NODE_RADIUS, 24, 24),
        new THREE.MeshLambertMaterial({ color: NODE_COLOR_3D[n.type] }),
      );
      sphere.position.set(p.x, p.y, p.z);
      scene.add(sphere);
      if (isEnd) {
        const ring = new THREE.Mesh(
          new THREE.TorusGeometry(NODE_RADIUS + 0.25, 0.06, 10, 40),
          new THREE.MeshLambertMaterial({
            color: n.id === state.source ? 0x38bdf8 : 0x34d399,
          }),
        );
        ring.rotation.x = Math.PI / 2;
        ring.position.set(p.x, p.y - 0.7, p.z);
        scene.add(ring);
      }
      const label = makeLabelSprite(
        n.id,
        `${typeLabel(n.type)}${n.id === state.source ? " · nguồn" : n.id === state.destination ? " · đích" : ""}`,
      );
      label.position.set(p.x, p.y + 1.35, p.z);
      scene.add(label);
    }

    // Liên kết: cạnh trên route = trụ màu primary (nổi bật), cạnh thường = line mảnh
    const routeIdx = new Map(state.route.map((id, i) => [id, i]));
    for (const [a, b] of state.links) {
      const ia = routeIdx.get(a);
      const ib = routeIdx.get(b);
      const onRoute = ia !== undefined && ib !== undefined && Math.abs(ia - ib) === 1;
      if (onRoute) {
        scene.add(makeRouteEdge(positions[a], positions[b]));
      } else {
        const geometry = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(positions[a].x, positions[a].y, positions[a].z),
          new THREE.Vector3(positions[b].x, positions[b].y, positions[b].z),
        ]);
        scene.add(
          new THREE.Line(geometry, new THREE.LineBasicMaterial({ color: LINK_COLOR })),
        );
      }
    }

    // Gói tin: cầu hồng lơ lửng trên nút hiện tại (khớp ngôn ngữ 2D)
    const packet = new THREE.Mesh(
      new THREE.SphereGeometry(0.28, 20, 20),
      new THREE.MeshLambertMaterial({ color: PACKET_COLOR, emissive: 0x9d174d }),
    );
    const start = positions[currentStep(state).packetAt];
    packet.position.set(start.x, start.y + 1.0, start.z);
    scene.add(packet);

    // Vòng sáng đánh dấu NÚT HIỆN TẠI của gói tin
    const highlight = new THREE.Mesh(
      new THREE.TorusGeometry(NODE_RADIUS + 0.12, 0.05, 10, 40),
      new THREE.MeshLambertMaterial({ color: PACKET_COLOR }),
    );
    highlight.rotation.x = Math.PI / 2;
    highlight.position.set(start.x, start.y, start.z);
    scene.add(highlight);

    // Camera + orbit controls TỐI GIẢN (xoay + zoom, khoá pan) — thuần trình bày
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
    const span = Math.max(state.route.length, 2) * SPACING;
    camera.position.set(0, span * 0.45, span * 0.85);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 0, OFF_ROUTE_Z / 2);
    controls.enablePan = false;
    controls.minDistance = 3;
    controls.maxDistance = span * 2.5;
    controls.enableDamping = true;
    const home = { position: camera.position.clone(), target: controls.target.clone() };

    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    const resize = () => {
      const w = container.clientWidth || 600;
      const h = container.clientHeight || 320;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(container);

    const handles: SceneHandles = {
      renderer,
      scene,
      camera,
      controls,
      positions,
      packet,
      packetTarget: packet.position.clone(),
      highlight,
      raf: 0,
      observer,
      home,
    };

    // Vòng vẽ: nội suy HÌNH ẢNH vị trí gói tin về đích ngữ nghĩa hiện tại.
    const tick = () => {
      handles.raf = requestAnimationFrame(tick);
      packet.position.lerp(handles.packetTarget, 0.12);
      controls.update();
      renderer.render(scene, camera);
    };
    tick();

    handlesRef.current = handles;
    return () => {
      handlesRef.current = null;
      disposeScene(handles, container);
    };
    // Topology + endpoints là các THAM CHIẾU bất biến trong một mô phỏng;
    // goToStep chỉ đổi cursor nên effect này không chạy lại theo bước.
  }, [state.nodes, state.links, state.route, state.source, state.destination]);

  // ── Bước đổi → chỉ dời ĐÍCH nội suy của gói tin + vòng highlight.
  useEffect(() => {
    const h = handlesRef.current;
    if (!h) return;
    const p = h.positions[step.packetAt];
    if (!p) return;
    h.packetTarget.set(p.x, p.y + 1.0, p.z);
    h.highlight.position.set(p.x, p.y, p.z);
  }, [step.packetAt]);

  if (webglFailed) {
    return (
      <div className="stack" style={{ gap: "var(--sp-md)" }}>
        <div className="sim-stage">
          <p className="notes" role="alert" style={{ padding: "var(--sp-lg)" }}>
            {WEBGL_FALLBACK_MESSAGE}
          </p>
        </div>
        <div className="narration-bar">{step.narration}</div>
      </div>
    );
  }

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div className="sim-stage sim-stage-3d">
        <div ref={containerRef} className="three-container" />
        <button
          type="button"
          className="btn-utility three-reset-view"
          title="Đưa camera về góc nhìn ban đầu — KHÔNG ảnh hưởng mô phỏng"
          onClick={() => {
            const h = handlesRef.current;
            if (!h) return;
            h.camera.position.copy(h.home.position);
            h.controls.target.copy(h.home.target);
            h.controls.update();
          }}
        >
          ⌂ Góc nhìn
        </button>
      </div>
      <div className="narration-bar">{step.narration}</div>
    </div>
  );
}
