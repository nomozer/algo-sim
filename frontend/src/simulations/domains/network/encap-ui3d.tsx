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

const ROLE_COLOR_3D: Record<string, number> = {
  payload: 0x1aae39, // green — khớp --accent-green
  header: 0x62aef0, // sky — khớp --accent-sky
  trailer: 0xdd5b00, // orange — khớp --accent-orange
};

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
  raf: number;
  observer: ResizeObserver;
  home: { position: THREE.Vector3; target: THREE.Vector3 };
}

/** Dựng lại nhóm PDU (các hộp phân đoạn) theo state.pdu — thứ tự từ engine. */
function buildPduGroup(pdu: PduComponent[]): THREE.Group {
  const group = new THREE.Group();
  const W = 0.9;
  const total = pdu.length * W;
  pdu.forEach((c, i) => {
    const box = new THREE.Mesh(
      new THREE.BoxGeometry(W * 0.92, 0.6, 0.6),
      new THREE.MeshLambertMaterial({ color: ROLE_COLOR_3D[c.role] }),
    );
    box.position.x = -total / 2 + W * (i + 0.5);
    group.add(box);
    const label = makeLabelSprite(c.label);
    label.position.set(box.position.x, 0.7, 0);
    label.scale.set(1.2, 0.4, 1);
    group.add(label);
  });
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
    scene.add(new THREE.AmbientLight(0xffffff, 1.1));
    const sun = new THREE.DirectionalLight(0xffffff, 1.5);
    sun.position.set(6, 10, 8);
    scene.add(sun);

    // Bốn phiến tầng (slab) ở mỗi độ sâu Z — nhãn tầng ở cạnh trái.
    for (const layer of LAYERS) {
      const z = layerDepth(layer);
      const slab = new THREE.Mesh(
        new THREE.BoxGeometry(16, 0.08, 2.6),
        new THREE.MeshLambertMaterial({ color: 0x94a3b8, transparent: true, opacity: 0.18 }),
      );
      slab.position.set(0, -0.5, z);
      scene.add(slab);
      const label = makeLabelSprite(LAYER_LABEL[layer]);
      label.position.set(-7.4, 0, z);
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

    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
    camera.position.set(0, 9, 12);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 0, -6);
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
      renderer, scene, camera, controls, pduGroup,
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
