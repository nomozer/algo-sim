import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  LINE_DISPLAY_HALF_LENGTH,
  PLANE_DISPLAY_SIZE,
  clampStep,
  highlightedAt,
  narrationAt,
  objectsAt,
  stepCount,
  toNumber,
  toVec3,
  type Scene3D,
  type SceneObject,
} from "./scene3d-model";
import {
  type InteractionState,
  TRANG_THAI_DAU,
  highlightSet,
  isVisible,
  visualTransformOf,
} from "./interaction-state";

/**
 * Renderer 3D của miền hình học không gian — `display(scene, step)`.
 *
 * Cùng khuôn `network/encap-ui3d.tsx` đã chứng minh: KHÔNG engine 3D thứ hai,
 * KHÔNG tính lại, mọi mesh/camera/vật liệu là **renderer-owned** (ref/closure),
 * KHÔNG BAO GIỜ vào store.
 *
 * ─── ĐIỀU FILE NÀY TUYỆT ĐỐI KHÔNG LÀM ────────────────────────────────────
 *
 * Không tích có hướng, không giao điểm, không suy quan hệ vuông góc/song song.
 * Mọi `point`/`normal`/`direction`/`vertices` đến từ kernel hữu tỉ ở backend.
 *
 * Chỗ dễ nhầm nhất là mặt phẳng: `plane3` VÔ HẠN, không có biên. Renderer
 * **không tính** biên từ ba điểm định nghĩa — nó đặt một `PlaneGeometry` cỡ cố
 * định tại `point` rồi xoay nó theo `normal` bằng `setFromUnitVectors`. Pháp
 * tuyến là dữ liệu đã có; xoay theo nó là dùng thư viện, không phải suy luận.
 *
 * Cùng lẽ ấy với `line3`: kéo dài `direction` ra hai phía một khoảng cố định.
 *
 * ─── VÌ SAO KHÔNG PHẢI GEOGEBRA ───────────────────────────────────────────
 *
 * Không toolbar, không click-tạo-điểm, không kéo thả, không ô nhập lệnh. Hình
 * ở đây **không dựng được bằng chuột** — nó chỉ có thể đến từ một chương trình
 * đã qua thẩm định. Thứ người học điều khiển là **thời gian** (bước dựng) và
 * **góc nhìn**, không phải nội dung hình.
 */

export const GEOMETRY_WEBGL_FALLBACK =
  "Không khởi tạo được chế độ 3D trên thiết bị này (WebGL không khả dụng). " +
  "Các bước dựng vẫn đọc được đầy đủ ở danh sách bên dưới.";

/** Tạo WebGLRenderer an toàn: thất bại → `null`, KHÔNG ném (export để test). */
export function tryCreateWebGLRenderer(): THREE.WebGLRenderer | null {
  try {
    return new THREE.WebGLRenderer({ antialias: true, alpha: true });
  } catch {
    return null;
  }
}

/** Điểm gốc (tự do) khác điểm dựng ra — người học cần thấy cái nào là dữ kiện. */
const MAU = {
  free: 0x2563eb,
  derived: 0xdc2626,
  line: 0x0f766e,
  surface: 0x7c3aed,
  mesh: 0x64748b,
  polygon: 0xf59e0b,
  highlight: 0xfbbf24,
} as const;

function v(o: THREE.Object3D, name: string): THREE.Object3D {
  o.name = name;
  return o;
}

/**
 * Một đối tượng cảnh → một `Object3D`, hoặc `null` nếu không vẽ được.
 *
 * `readout` trả `null` **có chủ đích**: một đại lượng đo được không có hình
 * trong không gian. Nó vẫn phải hiện lên — nhưng ở bảng chữ bên cạnh, không
 * phải trong khung 3D. Vẽ bừa một nhãn lơ lửng là đặt một con số vào một chỗ
 * không có nghĩa hình học.
 */
export function buildObject3D(o: SceneObject, noiBat: boolean): THREE.Object3D | null {
  const mau = noiBat ? MAU.highlight : undefined;

  if (o.render === "point_marker" && o.xyz) {
    const g = new THREE.SphereGeometry(0.09, 16, 12);
    const m = new THREE.MeshStandardMaterial({
      color: mau ?? (o.origin === "free" ? MAU.free : MAU.derived),
    });
    const mesh = new THREE.Mesh(g, m);
    mesh.position.set(...toVec3(o.xyz));
    return v(mesh, `point:${o.id}`);
  }

  if (o.render === "line" && o.point && o.direction) {
    // Kéo dài vector chỉ phương ĐÃ CHO ra hai phía. Không tính hướng — hướng
    // là dữ liệu từ kernel.
    const p = new THREE.Vector3(...toVec3(o.point));
    const d = new THREE.Vector3(...toVec3(o.direction)).normalize();
    const a = p.clone().addScaledVector(d, -LINE_DISPLAY_HALF_LENGTH);
    const b = p.clone().addScaledVector(d, LINE_DISPLAY_HALF_LENGTH);
    const g = new THREE.BufferGeometry().setFromPoints([a, b]);
    return v(new THREE.Line(g, new THREE.LineBasicMaterial({
      color: mau ?? MAU.line,
    })), `line:${o.id}`);
  }

  if (o.render === "surface" && o.point && o.normal) {
    // Đặt tại `point`, xoay theo `normal`. `setFromUnitVectors` là phép của thư
    // viện trên một pháp tuyến ĐÃ CÓ — không phải suy ra mặt phẳng từ ba điểm.
    const g = new THREE.PlaneGeometry(PLANE_DISPLAY_SIZE, PLANE_DISPLAY_SIZE);
    const m = new THREE.MeshStandardMaterial({
      color: mau ?? MAU.surface,
      transparent: true,
      opacity: noiBat ? 0.38 : 0.2,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    const mesh = new THREE.Mesh(g, m);
    const n = new THREE.Vector3(...toVec3(o.normal)).normalize();
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), n);
    mesh.position.set(...toVec3(o.point));
    return v(mesh, `plane:${o.id}`);
  }

  if (o.render === "mesh" && o.vertices && o.faces) {
    // Quạt tam giác trên mỗi mặt — phép chia LIST, không phải phép hình học:
    // thứ tự đỉnh quanh mặt do kernel quyết, ở đây chỉ nối chúng lại.
    const dinh = o.vertices.map(toVec3);
    const pos: number[] = [];
    for (const f of o.faces) {
      for (let i = 1; i < f.length - 1; i += 1) {
        for (const j of [f[0], f[i], f[i + 1]]) pos.push(...dinh[j]);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.computeVertexNormals();
    const nhom = new THREE.Group();
    nhom.add(new THREE.Mesh(g, new THREE.MeshStandardMaterial({
      color: mau ?? MAU.mesh,
      transparent: true,
      opacity: 0.22,
      side: THREE.DoubleSide,
      depthWrite: false,
    })));
    // Khung cạnh: khối trong suốt mà không có khung thì đọc ra một vệt mờ.
    nhom.add(new THREE.LineSegments(
      new THREE.EdgesGeometry(g),
      new THREE.LineBasicMaterial({ color: mau ?? MAU.mesh }),
    ));
    return v(nhom, `solid:${o.id}`);
  }

  if (o.render === "polygon" && (o.polygon || o.vertices)) {
    const pts = (o.polygon ?? o.vertices ?? []).map(toVec3)
      .map((p) => new THREE.Vector3(...p));
    if (pts.length < 2) return null;
    const vong = o.closed === false ? pts : [...pts, pts[0]];
    const g = new THREE.BufferGeometry().setFromPoints(vong);
    return v(new THREE.Line(g, new THREE.LineBasicMaterial({
      color: mau ?? MAU.polygon, linewidth: 2,
    })), `polygon:${o.id}`);
  }

  return null; // `readout` và mọi loại chưa vẽ được
}

/**
 * Tên `Object3D` → **id ngữ nghĩa**, hoặc `null` nếu không phải vật của cảnh.
 *
 * Mỗi `Object3D` mang tên `"<render>:<id>"` (`point:M`, `solid:chop`). Hàm này
 * là chỗ DUY NHẤT quy ước ấy được đọc ngược — tách ra để chọn-bằng-chuột kiểm
 * được mà **không cần WebGL**: raycast trả về một `Object3D`, phần còn lại
 * chỉ là bóc chuỗi.
 *
 * `id` có thể chứa dấu `:`? Không: nó là tên biến của chương trình. Nhưng hàm
 * vẫn cắt ở dấu `:` ĐẦU TIÊN để một tên lạ không làm mất phần đuôi.
 */
export function semanticIdOf(name: string | undefined | null): string | null {
  if (!name) return null;
  const i = name.indexOf(":");
  return i > 0 && i < name.length - 1 ? name.slice(i + 1) : null;
}

/** Leo lên cha cho tới khi gặp một vật có id ngữ nghĩa. */
export function pickSemanticId(o: THREE.Object3D | null): string | null {
  for (let x: THREE.Object3D | null = o; x; x = x.parent) {
    const id = semanticIdOf(x.name);
    if (id) return id;
  }
  return null;
}

interface Props {
  scene: Scene3D;
  step: number;
  /** Cách nhìn hiện tại. Vắng ⇒ hiện mọi thứ, không bung — hành vi cũ. */
  interaction?: InteractionState;
  /** Bấm vào một vật. Vắng ⇒ khung 3D chỉ để xem. */
  onSelect?: (id: string | null) => void;
}

export function Scene3DWorkspace({ scene, step, interaction, onSelect }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rootRef = useRef<THREE.Group | null>(null);
  const veRef = useRef<(() => void) | null>(null);
  const [webglFailed, setWebglFailed] = useState(false);
  const buoc = clampStep(scene, step);
  // Vắng `interaction` ⇒ trạng thái đầu, tức hành vi TRƯỚC wave này nguyên
  // vẹn: hiện mọi thứ, không bung, tô sáng theo bước.
  const tuongTac = interaction ?? TRANG_THAI_DAU;
  const chonRef = useRef(onSelect);
  chonRef.current = onSelect;

  // Dựng scene MỘT LẦN; đổi bước chỉ thay nội dung nhóm gốc.
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const renderer = tryCreateWebGLRenderer();
    if (!renderer) {
      setWebglFailed(true);
      return;
    }
    const scene3 = new THREE.Scene();
    const cam = new THREE.PerspectiveCamera(50, 1, 0.1, 200);
    cam.position.set(6, 5, 8);
    scene3.add(new THREE.AmbientLight(0xffffff, 0.75));
    const den = new THREE.DirectionalLight(0xffffff, 0.6);
    den.position.set(5, 10, 7);
    scene3.add(den);
    const goc = new THREE.Group();
    scene3.add(goc);
    rootRef.current = goc;

    const dieuKhien = new OrbitControls(cam, renderer.domElement);
    dieuKhien.enableDamping = true;
    container.appendChild(renderer.domElement);

    const chinhCo = () => {
      const w = container.clientWidth || 640;
      const h = container.clientHeight || 420;
      renderer.setSize(w, h, false);
      cam.aspect = w / h;
      cam.updateProjectionMatrix();
    };
    chinhCo();
    window.addEventListener("resize", chinhCo);

    // ── CHỌN BẰNG CHUỘT ──────────────────────────────────────────────────
    //
    // `pointerup`, không `pointerdown`: OrbitControls dùng kéo-thả để xoay
    // cảnh, và bắt ở `down` thì mỗi lần xoay cũng là một lần chọn. Chỉ tính
    // là bấm khi con trỏ gần như không di chuyển giữa hai mốc.
    let batDau: [number, number] | null = null;
    const NGUONG_KEO = 4;
    const xuongTay = (e: PointerEvent) => {
      batDau = [e.clientX, e.clientY];
    };
    const nhacTay = (e: PointerEvent) => {
      const d0 = batDau;
      batDau = null;
      if (!d0 || !chonRef.current) return;
      if (Math.hypot(e.clientX - d0[0], e.clientY - d0[1]) > NGUONG_KEO) return;
      const r = renderer.domElement.getBoundingClientRect();
      const diem = new THREE.Vector2(
        ((e.clientX - r.left) / r.width) * 2 - 1,
        -((e.clientY - r.top) / r.height) * 2 + 1,
      );
      const tia = new THREE.Raycaster();
      // Điểm và đường mảnh: cho phép trúng trong một bán kính nhỏ, nếu không
      // học sinh phải bấm đúng từng pixel của một chấm.
      tia.params.Line = { threshold: 0.08 };
      tia.params.Points = { threshold: 0.12 };
      tia.setFromCamera(diem, cam);
      const trung = tia.intersectObjects(goc.children, true);
      chonRef.current(pickSemanticId(trung[0]?.object ?? null));
    };
    renderer.domElement.addEventListener("pointerdown", xuongTay);
    renderer.domElement.addEventListener("pointerup", nhacTay);

    let song = true;
    const vong = () => {
      if (!song) return;
      dieuKhien.update();
      renderer.render(scene3, cam);
      requestAnimationFrame(vong);
    };
    veRef.current = () => renderer.render(scene3, cam);
    vong();

    return () => {
      song = false;
      renderer.domElement.removeEventListener("pointerdown", xuongTay);
      renderer.domElement.removeEventListener("pointerup", nhacTay);
      window.removeEventListener("resize", chinhCo);
      dieuKhien.dispose();
      renderer.dispose();
      container.removeChild(renderer.domElement);
      rootRef.current = null;
      veRef.current = null;
    };
  }, []);

  // Đổi bước ⇒ dựng lại nội dung nhóm gốc. Rẻ vì cảnh nhỏ (≤ vài chục mesh).
  useEffect(() => {
    const goc = rootRef.current;
    if (!goc) return;
    for (const con of [...goc.children]) {
      goc.remove(con);
      con.traverse((x) => {
        const m = x as THREE.Mesh;
        m.geometry?.dispose?.();
        const mat = m.material as THREE.Material | THREE.Material[] | undefined;
        if (Array.isArray(mat)) mat.forEach((i) => i.dispose());
        else mat?.dispose?.();
      });
    }
    const noiBat = new Set(
      tuongTac?.selected_id
        ? highlightSet(scene, tuongTac.selected_id)
        : highlightedAt(scene, buoc),
    );
    const hienTai = objectsAt(scene, buoc);
    const daTonTai = new Set(hienTai.map((o) => o.id));
    for (const o of hienTai) {
      // ẨN / CÔ LẬP quyết định CÓ DỰNG HAY KHÔNG — không dựng rồi giấu, vì
      // một mesh vô hình vẫn nằm trên đường raycast và vẫn ăn cú bấm.
      if (!isVisible(tuongTac, o.id, daTonTai)) continue;
      const obj = buildObject3D(o, noiBat.has(o.id));
      if (!obj) continue;
      // BUNG HÌNH chỉ dịch vị trí TRÌNH BÀY. Không một toạ độ nào trong
      // `scene` bị chạm — `visualTransformOf` trả về một giá trị mới.
      const bd = visualTransformOf(tuongTac, scene, o.id);
      obj.position.set(
        toNumber(bd.translate[0]),
        toNumber(bd.translate[1]),
        toNumber(bd.translate[2]),
      );
      goc.add(obj);
    }
    veRef.current?.();
  }, [scene, buoc, tuongTac]);

  const hien = objectsAt(scene, buoc);
  const soDo = hien.filter((o) => o.render === "readout");

  return (
    <div className="geo3d">
      {webglFailed ? (
        <p className="geo3d-fallback">{GEOMETRY_WEBGL_FALLBACK}</p>
      ) : (
        <div ref={containerRef} className="geo3d-canvas" />
      )}
      <p className="geo3d-narration">{narrationAt(scene, buoc)}</p>
      {/* Nội suy GỘP thành MỘT chuỗi: `{a}/{b}` làm SSR chèn marker
          `<!-- -->` vào giữa, nên chữ hiện ra đúng mà mọi phép kiểm chuỗi lại
          trượt — một lệch câm giữa thứ người đọc thấy và thứ test đọc. */}
      <p className="geo3d-progress">{`Bước ${buoc + 1}/${stepCount(scene)}`}</p>
      {soDo.length > 0 && (
        <ul className="geo3d-readout">
          {soDo.map((o) => (
            <li key={o.id}>{`${o.label} = ${o.value}`}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
