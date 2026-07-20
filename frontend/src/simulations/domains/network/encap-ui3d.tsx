import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import type { WorkspaceProps } from "../../types";
import {
  currentStep, LAYERS, LAYER_LABEL,
  type EncapConfig, type EncapState, type LayerId, type PduComponent, type Side,
} from "./encap-model";

/**
 * Renderer 3D của network.protocol_encapsulation (M10 — 3D SƯ PHẠM).
 *
 * CÙNG module/CÙNG EncapState với renderer 2D: KHÔNG engine 3D, KHÔNG tính lại
 * PDU, KHÔNG prediction riêng (PredictionBar dùng chung, nằm ngoài renderer).
 *
 * TUYÊN BỐ TRUNG TÂM: trục Z = TẦNG GIAO THỨC (nghĩa khái niệm thật), trục X =
 * chiều truyền (gửi → nhận). PDU đi XUỐNG các tầng khi đóng gói, băng NGANG khi
 * truyền, đi LÊN khi mở gói. Mọi toạ độ/camera/mesh là renderer-owned (ref/closure),
 * KHÔNG BAO GIỜ vào store/state (M7.FREEZE).
 */

type Props = WorkspaceProps<EncapConfig, EncapState>;

const LAYER_GAP = 4;
/** Z = độ sâu TẦNG: Application 0 → Network Access -12. Đây là nghĩa của trục sâu. */
export function layerDepth(layer: LayerId): number {
  const z = -LAYERS.indexOf(layer) * LAYER_GAP;
  return z === 0 ? 0 : z; // chuẩn hoá -0 → +0 (Application ở đúng độ sâu 0)
}
/** X = chiều truyền: gửi (-6) → đường truyền (0) → nhận (+6). */
export function sideX(side: Side): number {
  return side === "sender" ? -6 : side === "receiver" ? 6 : 0;
}

/**
 * Sắc riêng từng tầng — để BỐN phiến ĐỌC RA thành bốn mặt phẳng phân biệt thay
 * vì bốn vệt xám mờ đồng nhất (Mayer coherence: chiều sâu phải mang nghĩa đọc
 * được, không phải trang trí). Phiến của tầng đang hoạt động được làm đục hơn.
 */
const LAYER_TINT: Record<LayerId, number> = {
  application: 0x34d399, // green
  transport: 0x60a5fa, // blue
  internet: 0xa78bfa, // violet
  network_access: 0xfbbf24, // amber
};
const SLAB_OPACITY_BASE = 0.2;
const SLAB_OPACITY_ACTIVE = 0.58;

export const ROLE_COLOR_3D: Record<string, number> = {
  payload: 0x1aae39, // green — khớp --accent-green
  header: 0x62aef0, // sky — khớp --accent-sky
  trailer: 0xdd5b00, // orange — khớp --accent-orange
};

/** Bề rộng một hộp phân đoạn PDU (đơn vị thế giới 3D). */
const PDU_SEG_W = 0.9;

/** Mô tả một hộp phân đoạn 3D — vị trí X derive từ THỨ TỰ trong PDU. */
export interface PduSeg3D {
  id: string;
  label: string;
  role: string;
  color: number;
  x: number;
}

/**
 * Bố cục PDU 3D — PURE, tất định, KHÔNG cần WebGL/canvas (export để test parity).
 * Đây là SỰ THẬT NGỮ NGHĨA mà renderer 3D vẽ: một hộp mỗi phân đoạn, theo đúng
 * thứ tự `state.pdu`, tô màu theo vai trò. `buildPduGroup` chỉ dựng mesh từ đây.
 */
export function pduLayout3d(pdu: PduComponent[]): PduSeg3D[] {
  const total = pdu.length * PDU_SEG_W;
  return pdu.map((c, i) => ({
    id: c.id,
    label: c.label,
    role: c.role,
    color: ROLE_COLOR_3D[c.role],
    x: -total / 2 + PDU_SEG_W * (i + 0.5),
  }));
}

export const ENCAP_WEBGL_FALLBACK =
  "Không khởi tạo được chế độ 3D trên thiết bị này (WebGL không khả dụng). " +
  "Mô phỏng vẫn hoạt động đầy đủ ở chế độ 2D — hãy bấm nút 2D phía trên.";

/** Tạo WebGLRenderer an toàn: thất bại → null, KHÔNG ném lỗi (export để test). */
export function tryCreateWebGLRenderer(): THREE.WebGLRenderer | null {
  try {
    return new THREE.WebGLRenderer({ antialias: true, alpha: true });
  } catch {
    return null;
  }
}

function makeLabelSprite(text: string): THREE.Sprite {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 64;
  const ctx = canvas.getContext("2d")!;
  ctx.textAlign = "center";
  ctx.font = "bold 28px system-ui, sans-serif";
  ctx.lineWidth = 6;
  ctx.strokeStyle = "rgba(15,23,42,0.9)";
  ctx.strokeText(text, 128, 40);
  ctx.fillStyle = "#ffffff";
  ctx.fillText(text, 128, 40);
  const sprite = new THREE.Sprite(
    new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(canvas), depthTest: false }),
  );
  sprite.scale.set(2.6, 0.65, 1);
  return sprite;
}

interface SceneHandles {
  renderer: THREE.WebGLRenderer;
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  pduGroup: THREE.Group;
  pduTarget: THREE.Vector3;
  slabs: Record<LayerId, THREE.Mesh>; // phiến mỗi tầng — để làm nổi tầng đang hoạt động
  raf: number;
  observer: ResizeObserver;
  home: { position: THREE.Vector3; target: THREE.Vector3 };
}

/** Dựng lại nhóm PDU (các hộp phân đoạn) theo state.pdu — bố cục từ `pduLayout3d`. */
function buildPduGroup(pdu: PduComponent[]): THREE.Group {
  const group = new THREE.Group();
  for (const seg of pduLayout3d(pdu)) {
    const box = new THREE.Mesh(
      new THREE.BoxGeometry(PDU_SEG_W * 0.92, 0.6, 0.6),
      new THREE.MeshLambertMaterial({ color: seg.color }),
    );
    box.position.x = seg.x;
    group.add(box);
    const label = makeLabelSprite(seg.label);
    label.position.set(seg.x, 0.7, 0);
    label.scale.set(1.2, 0.4, 1);
    group.add(label);
  }
  return group;
}

function disposeGroup(group: THREE.Group): void {
  group.traverse((obj) => {
    if (obj instanceof THREE.Mesh) {
      obj.geometry.dispose();
      const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
      for (const m of mats) m.dispose();
    }
    if (obj instanceof THREE.Sprite) {
      obj.material.map?.dispose();
      obj.material.dispose();
    }
  });
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
  if (h.renderer.domElement.parentElement === container) container.removeChild(h.renderer.domElement);
}

/** Vị trí ngữ nghĩa của PDU: X theo side, Z theo tầng (truyền tin → độ sâu khung). */
function pduPosition(state: EncapState): THREE.Vector3 {
  const step = currentStep(state);
  const layer = step.activeLayer ?? "network_access";
  return new THREE.Vector3(sideX(step.side), 0.4, layerDepth(layer));
}

export function Encap3DWorkspace({ state }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const handlesRef = useRef<SceneHandles | null>(null);
  const [webglFailed, setWebglFailed] = useState(false);
  const step = currentStep(state);

  // Dựng scene MỘT LẦN cho một mô phỏng (số tầng/side bất biến; đổi bước chỉ dời PDU).
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const renderer = tryCreateWebGLRenderer();
    if (!renderer) {
      setWebglFailed(true);
      return;
    }
    const scene = new THREE.Scene();
    scene.add(new THREE.AmbientLight(0xffffff, 1.15));
    const sun = new THREE.DirectionalLight(0xffffff, 1.5);
    sun.position.set(6, 10, 8);
    scene.add(sun);

    // Lưới nền mờ — mốc không gian để CHIỀU SÂU (trục tầng) đọc được (như routing 3D).
    const grid = new THREE.GridHelper(30, 30, 0x94a3b8, 0xcbd5e1);
    (grid.material as THREE.Material).opacity = 0.25;
    (grid.material as THREE.Material).transparent = true;
    grid.position.y = -1.4;
    scene.add(grid);

    // Bốn phiến tầng (slab) ở mỗi độ sâu Z — sắc riêng + nhãn tầng lớn ở cạnh trái.
    const slabs = {} as Record<LayerId, THREE.Mesh>;
    for (const layer of LAYERS) {
      const z = layerDepth(layer);
      const slab = new THREE.Mesh(
        new THREE.BoxGeometry(16, 0.22, 3.0),
        new THREE.MeshLambertMaterial({
          color: LAYER_TINT[layer],
          transparent: true,
          opacity: SLAB_OPACITY_BASE,
        }),
      );
      slab.position.set(0, -0.6, z);
      scene.add(slab);
      slabs[layer] = slab;
      const label = makeLabelSprite(LAYER_LABEL[layer]);
      label.position.set(-9.2, 0.15, z);
      label.scale.set(3.6, 0.9, 1); // to hơn để đọc được, không chồng lên nhau
      scene.add(label);
    }
    // Nhãn hai đầu trục X (chiều truyền).
    const gtx = makeLabelSprite("MÁY GỬI");
    gtx.position.set(sideX("sender"), 1.6, 0);
    scene.add(gtx);
    const rcv = makeLabelSprite("MÁY NHẬN");
    rcv.position.set(sideX("receiver"), 1.6, 0);
    scene.add(rcv);

    const pduGroup = buildPduGroup(currentStep(state).pdu);
    const startPos = pduPosition(state);
    pduGroup.position.copy(startPos);
    scene.add(pduGroup);

    // Camera nghiêng-CẠNH (không phải nhìn từ trên xuống): lộ trục Z = tầng để
    // thấy PDU đi XUỐNG qua các phiến khi đóng gói, không bị bóp dẹp.
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
    camera.position.set(12, 7.5, 13);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, -0.3, -6);
    controls.enablePan = false;
    controls.minDistance = 6;
    controls.maxDistance = 40;
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
      renderer, scene, camera, controls, pduGroup, slabs,
      pduTarget: startPos.clone(), raf: 0, observer, home,
    };
    const tick = () => {
      handles.raf = requestAnimationFrame(tick);
      pduGroup.position.lerp(handles.pduTarget, 0.14);
      controls.update();
      renderer.render(scene, camera);
    };
    tick();
    handlesRef.current = handles;
    return () => {
      handlesRef.current = null;
      disposeScene(handles, container);
    };
    // Chỉ payloadLabel (định danh mô phỏng) là bất biến trong một phiên; đổi bước
    // KHÔNG rebuild scene — effect dưới lo việc rebuild nhóm PDU + dời vị trí.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.payloadLabel]);

  // Đổi bước → rebuild nhóm PDU (thành phần đổi) + dời tới đích ngữ nghĩa mới.
  useEffect(() => {
    const h = handlesRef.current;
    if (!h) return;
    h.scene.remove(h.pduGroup);
    disposeGroup(h.pduGroup);
    const group = buildPduGroup(step.pdu);
    group.position.copy(h.pduGroup.position); // lướt từ vị trí cũ
    h.scene.add(group);
    h.pduGroup = group;
    h.pduTarget = pduPosition(state);
    // Làm NỔI tầng đang hoạt động: phiến đục hơn để thấy PDU đang ở tầng nào
    // (bước truyền tin activeLayer = null → mọi phiến trở lại mức nền).
    for (const layer of LAYERS) {
      const mat = h.slabs[layer].material as THREE.MeshLambertMaterial;
      mat.opacity = step.activeLayer === layer ? SLAB_OPACITY_ACTIVE : SLAB_OPACITY_BASE;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.cursor]);

  if (webglFailed) {
    return (
      <div className="stack" style={{ gap: "var(--sp-md)" }}>
        <div className="sim-stage">
          <p className="notes" role="alert" style={{ padding: "var(--sp-lg)" }}>
            {ENCAP_WEBGL_FALLBACK}
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
        <div className="three-caption">Trục sâu = tầng giao thức · trục ngang = chiều truyền</div>
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
