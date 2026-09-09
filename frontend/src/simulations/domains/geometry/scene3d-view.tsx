import { useEffect, useRef, useState } from "react";
import { chiaTamGiac } from "./polygon-triangulate";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  LINE_DISPLAY_HALF_LENGTH,
  PLANE_DISPLAY_SIZE,
  VONG_CHIA,
  clampStep,
  SECTION_STROKE_RATIO,
  diemHuuHan,
  duongKinhCanh,
  hienSo,
  highlightedAt,
  khungMatPhang,
  narrationAt,
  objectsAt,
  stepCount,
  toNumber,
  toVec3,
  type Scene3D,
  type SceneObject,
  type Vec3,
} from "./scene3d-model";
import {
  type InteractionState,
  TRANG_THAI_DAU,
  highlightSet,
  isVisible,
  visualTransformOf,
} from "./interaction-state";
import { entitiesPresentAt, parentSolidOf } from "./scene3d-subentities";
import {
  BAN_KINH_NHIN,
  KHOANG_CAM_MAC_DINH,
  banKinhBamDiem,
  hangCuThe,
  nguongBamCanh,
} from "./pick-target";
import {
  kyHieu,
  locNhanChongNhau,
  uuTienNhan,
  veTrenKhung,
} from "./scene3d-presentation";
import { hopBaoCuaDiem, khungNhinVua } from "./scene3d-camera";

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
 * THIẾT DIỆN LUÔN NHÌN THẤY ĐƯỢC, kể cả khi nằm TRONG một khối.
 *
 * ─── LỖI ĐƯỢC SỬA ────────────────────────────────────────────────────────
 *
 * Ở `p3`, đường tròn thiết diện nằm **trong lòng** mặt cầu bán kính 15. Khối
 * cong vẽ mờ (`opacity 0.3`) nhưng vẫn ghi chiều sâu theo thứ tự vẽ, nên nửa
 * đường tròn phía xa bị mặt cầu nuốt mất. Học sinh nhìn thấy một quả cầu và
 * một cung hở — trong khi thứ cả bài nói về là **đường tròn giao tuyến**.
 *
 * Cách sửa nhỏ nhất giữ được cảm nhận khối: khối vẫn tô bóng như cũ, chỉ
 * thiết diện thôi bị kiểm chiều sâu và được vẽ SAU cùng. Không đụng opacity
 * của khối, nên hình vẫn đọc ra là một vật đặc chứ không thành khung dây.
 *
 * Đây là chính sách trình bày dùng chung cho MỌI thiết diện cong, không nêu
 * tên ca nào.
 */
const VAT_LIEU_THIET_DIEN = { depthTest: false } as const;

/** Vẽ sau mọi vật khác. Số lớn = vẽ sau, theo quy ước của three.js. */
const THU_TU_VE_THIET_DIEN = 10;

/**
 * Bề dày nét của thiết diện, tính từ TỈ LỆ CẢNH.
 *
 * Không có nền hình học (ô soi dựng một vật lẻ) thì lùi về tỉ lệ của chính
 * vật ấy — nét vẫn cân đối, chỉ mất tương quan với phần còn lại của cảnh.
 */
function beDayNet(diemNen: Vec3[], coVat: number): number {
  const d = duongKinhCanh(diemNen);
  return (d > 0 ? d : Math.max(coVat, 1) * 2) * SECTION_STROKE_RATIO;
}

/**
 * Một đối tượng cảnh → một `Object3D`, hoặc `null` nếu không vẽ được.
 *
 * `readout` trả `null` **có chủ đích**: một đại lượng đo được không có hình
 * trong không gian. Nó vẫn phải hiện lên — nhưng ở bảng chữ bên cạnh, không
 * phải trong khung 3D. Vẽ bừa một nhãn lơ lửng là đặt một con số vào một chỗ
 * không có nghĩa hình học.
 */
export function buildObject3D(
  o: SceneObject,
  noiBat: boolean,
  banKinhBam = banKinhBamDiem(KHOANG_CAM_MAC_DINH),
  /**
   * Điểm CÓ BIÊN của cả cảnh — chỉ mặt phẳng dùng tới, để cắt phần đáng vẽ ra
   * khỏi một mặt phẳng vô hạn. Mặc định rỗng ⇒ rơi về cỡ cố định, nên mọi nơi
   * gọi cũ (test, ô soi) giữ nguyên hành vi.
   */
  diemNen: Vec3[] = [],
): THREE.Object3D | null {
  const mau = noiBat ? MAU.highlight : undefined;

  if (o.render === "point_marker" && o.xyz) {
    // HAI hình, một vật: chấm NHÌN THẤY giữ nguyên cỡ, cộng một hình cầu VÔ
    // HÌNH rộng hơn chỉ để bắt con trỏ. Phóng to chấm cho dễ bấm thì một điểm
    // hình học bắt đầu trông như quả cầu — đổi thứ học sinh NHÌN THẤY để
    // chuột dễ hơn là cái giá không được trả.
    //
    // `visible = false` KHÔNG dùng được: `Raycaster` bỏ qua vật vô hình. Nên
    // proxy phải "được vẽ" mà không để lại gì — `colorWrite: false` +
    // `depthWrite: false`.
    const nhom = new THREE.Group();
    const m = new THREE.MeshStandardMaterial({
      color: mau ?? (o.origin === "free" ? MAU.free : MAU.derived),
    });
    const mesh = new THREE.Mesh(new THREE.SphereGeometry(BAN_KINH_NHIN, 16, 12), m);
    nhom.add(mesh);
    const proxy = new THREE.Mesh(
      new THREE.SphereGeometry(banKinhBam, 8, 6),
      new THREE.MeshBasicMaterial({
        colorWrite: false, depthWrite: false, transparent: true, opacity: 0,
      }),
    );
    proxy.name = "pick-proxy";
    nhom.add(proxy);
    nhom.position.set(...toVec3(o.xyz));
    return v(nhom, `point:${o.id}`);
  }

  if (o.render === "line" && o.point && o.direction) {
    // Kéo dài vector chỉ phương ĐÃ CHO ra hai phía. Không tính hướng — hướng
    // là dữ liệu từ kernel.
    const p = new THREE.Vector3(...toVec3(o.point));
    const d = new THREE.Vector3(...toVec3(o.direction)).normalize();
    const a = p.clone().addScaledVector(d, -LINE_DISPLAY_HALF_LENGTH);
    const b = p.clone().addScaledVector(d, LINE_DISPLAY_HALF_LENGTH);
    const g = new THREE.BufferGeometry().setFromPoints([a, b]);
    const duong = new THREE.Line(g, new THREE.LineBasicMaterial({
      color: mau ?? MAU.line,
    }));
    // Cùng lẽ với mặt phẳng: `line3` vô hạn, hai đầu mút là quyết định trình
    // bày. Ở `p1`, đường `BD` kéo dài vượt ra ngoài khối chóp; để nó tham gia
    // auto-fit thì camera phải lùi ra và khối thật bé đi vì một đoạn thẳng do
    // chính renderer bịa ra độ dài.
    duong.userData.voHan = true;
    return v(duong, `line:${o.id}`);
  }

  if (o.render === "surface" && o.point && o.normal) {
    // Xoay theo `normal` — `setFromUnitVectors` là phép của thư viện trên một
    // pháp tuyến ĐÃ CÓ, không phải suy ra mặt phẳng từ ba điểm.
    //
    // ⚠️ TÂM VÀ CỠ lấy từ vùng hình học liên quan (`khungMatPhang`), không còn
    // là ô vuông cố định đặt tại `point`. `point` chỉ là MỘT điểm bất kỳ trên
    // một mặt phẳng vô hạn: ở `p7` nó nằm ngoài hẳn hình nón, nên miếng cũ trôi
    // ra khỏi thiết diện. Xem `khungMatPhang` để biết vì sao đây là quyết định
    // TRÌNH BÀY chứ không phải một mệnh đề toán học.
    const khung = khungMatPhang(toVec3(o.point), toVec3(o.normal), diemNen);
    const canh = khung ? khung.canh : PLANE_DISPLAY_SIZE;
    const g = new THREE.PlaneGeometry(canh, canh);
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
    mesh.position.set(...(khung ? khung.tam : toVec3(o.point)));
    // Mặt phẳng VÔ HẠN: miếng vẽ ra là đại diện do tầng trình bày chọn cỡ, nên
    // nó KHÔNG được tham gia tính khung nhìn — xem `vuaKhungRef`.
    mesh.userData.voHan = true;
    return v(mesh, `plane:${o.id}`);
  }

  if (o.render === "circle" && o.center && o.normal && o.radius_sq) {
    // Chia lưới CHỈ ĐỂ VẼ. `radius_sq` là số chính xác backend gửi; căn bậc
    // hai lấy ở ĐÂY, tại biên hiển thị — không sớm hơn một tầng nào.
    const r = Math.sqrt(Math.max(0, toNumber(o.radius_sq)));
    const day = beDayNet(diemNen, r);
    const g = new THREE.RingGeometry(Math.max(0, r - day / 2), r + day / 2, VONG_CHIA);
    const mesh = new THREE.Mesh(g, new THREE.MeshBasicMaterial({
      color: mau ?? MAU.line, side: THREE.DoubleSide,
      ...VAT_LIEU_THIET_DIEN,
    }));
    mesh.renderOrder = THU_TU_VE_THIET_DIEN;
    const n = new THREE.Vector3(...toVec3(o.normal)).normalize();
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), n);
    mesh.position.set(...toVec3(o.center));
    return v(mesh, `circle:${o.id}`);
  }

  if (
    o.render === "ellipse" && o.center && o.normal &&
    o.major_dir && o.minor_dir && o.semi_major_sq && o.semi_minor_sq
  ) {
    // Chia lưới CHỈ ĐỂ VẼ. Bốn số backend gửi đều CHÍNH XÁC; căn bậc hai và
    // chuẩn hoá độ dài lấy ở ĐÂY, tại biên hiển thị — không sớm hơn một tầng
    // nào. Backend không chuẩn hoá được: nó sẽ đá hai phương ra khỏi ℚ³.
    const a = Math.sqrt(Math.max(0, toNumber(o.semi_major_sq)));
    const b = Math.sqrt(Math.max(0, toNumber(o.semi_minor_sq)));
    const M = new THREE.Vector3(...toVec3(o.major_dir)).normalize();
    const m = new THREE.Vector3(...toVec3(o.minor_dir)).normalize();
    const n = new THREE.Vector3(...toVec3(o.normal)).normalize();
    // Vành elip: dựng trong mặt phẳng (M, m) rồi đặt vào không gian. Không
    // dùng `RingGeometry` + scale không đều — scale ấy bóp méo cả bề rộng nét.
    //
    // ⚠️ DẢI, KHÔNG PHẢI ĐƯỜNG. `THREE.Line` luôn dày một điểm ảnh vì WebGL bỏ
    // qua `linewidth`; đo được là 10–13 điểm ảnh có màu cho cả một elip. Nên
    // vành được dựng thành một dải hai mép, dày theo TỈ LỆ CẢNH.
    const day = beDayNet(diemNen, Math.max(a, b));
    const trong: THREE.Vector3[] = [];
    const ngoai: THREE.Vector3[] = [];
    for (let i = 0; i <= VONG_CHIA; i += 1) {
      const t = (i / VONG_CHIA) * Math.PI * 2;
      const P = new THREE.Vector3()
        .addScaledVector(M, a * Math.cos(t))
        .addScaledVector(m, b * Math.sin(t));
      // Pháp tuyến TRONG MẶT PHẲNG của elip: tiếp tuyến quay 90° quanh `n`.
      const tt = new THREE.Vector3()
        .addScaledVector(M, -a * Math.sin(t))
        .addScaledVector(m, b * Math.cos(t))
        .normalize();
      const ra = new THREE.Vector3().crossVectors(tt, n).normalize()
        .multiplyScalar(day / 2);
      trong.push(P.clone().sub(ra));
      ngoai.push(P.clone().add(ra));
    }
    const dinh: number[] = [];
    for (let i = 0; i < VONG_CHIA; i += 1) {
      const [a0, b0, a1, b1] = [trong[i], ngoai[i], trong[i + 1], ngoai[i + 1]];
      dinh.push(a0.x, a0.y, a0.z, b0.x, b0.y, b0.z, a1.x, a1.y, a1.z);
      dinh.push(b0.x, b0.y, b0.z, b1.x, b1.y, b1.z, a1.x, a1.y, a1.z);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(dinh, 3));
    const vanh = new THREE.Mesh(g, new THREE.MeshBasicMaterial({
      color: mau ?? MAU.line, side: THREE.DoubleSide, ...VAT_LIEU_THIET_DIEN,
    }));
    vanh.renderOrder = THU_TU_VE_THIET_DIEN;
    vanh.position.set(...toVec3(o.center));
    return v(vanh, `ellipse:${o.id}`);
  }

  if (o.render === "curved_solid" && o.anchor && o.rim_point && o.curved_kind) {
    // ⚠️ MỘT tuyến vẽ cho ba hình. Điều phối theo `curved_kind` nằm ở đây và
    // CHỈ ở đây — nó là bảng TRÌNH BÀY, không phải một thẩm quyền ngữ nghĩa
    // thứ hai: mọi số ở dưới đều đọc thẳng từ payload, không công thức nào
    // được tính lại ở phía này.
    // ⚠️ `r` và `h` KHÔNG đo ở đây. Backend gửi `radius_sq`/`height_sq` — số
    // hữu tỉ CHÍNH XÁC — và phía này chỉ lấy căn ở biên hiển thị.
    //
    // Bản đầu tự đo khoảng cách giữa hai điểm neo để có `r` và `h`. Đó là tầng
    // vẽ đang LÀM HÌNH HỌC, và `scene3d.test.tsx` bắt được ngay — cổng ấy
    // chứng minh mình có răng ở đúng lần đầu tiên nó cần.
    const tam = new THREE.Vector3(...toVec3(o.anchor));
    const r = Math.sqrt(Math.max(0, toNumber(o.radius_sq ?? "0")));
    const h = Math.sqrt(Math.max(0, toNumber(o.height_sq ?? "0")));
    const dinh = o.apex_or_top
      ? new THREE.Vector3(...toVec3(o.apex_or_top))
      : null;
    const m = new THREE.MeshStandardMaterial({
      color: mau ?? MAU.surface,
      transparent: true,
      opacity: noiBat ? 0.5 : 0.3,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    let g: THREE.BufferGeometry;
    if (o.curved_kind === "ball") {
      g = new THREE.SphereGeometry(r, VONG_CHIA, Math.round(VONG_CHIA / 2));
    } else if (o.curved_kind === "cylinder") {
      g = new THREE.CylinderGeometry(r, r, h, VONG_CHIA);
    } else {
      g = new THREE.ConeGeometry(r, h, VONG_CHIA);
    }
    const mesh = new THREE.Mesh(g, m);
    if (dinh) {
      // Ba.js dựng trụ/nón quanh trục Y, tâm ở giữa chiều cao. Đưa về đúng
      // trục và đúng chỗ bằng phép quay trên một trục ĐÃ CÓ trong payload.
      const truc = dinh.clone().sub(tam).normalize();
      mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), truc);
      mesh.position.copy(tam).addScaledVector(truc, h / 2);
    } else {
      mesh.position.copy(tam);
    }
    return v(mesh, `curved:${o.id}:${o.curved_kind}`);
  }

  if (o.render === "mesh" && o.vertices && o.faces) {
    // Chia tam giác trên mỗi mặt — phép chia LIST, không phải phép hình học:
    // thứ tự đỉnh quanh mặt do kernel quyết, ở đây chỉ nối chúng lại.
    //
    // ⚠️ QUẠT TAM GIÁC ĐÃ THAY (2026-09-07, `NONCONVEX_POLYHEDRON_VOLUME_
    // FOUNDATION`). Quạt chỉ đúng với mặt LỒI; với mặt lõm nó **lấp mất phần
    // lõm** — hình vẽ ra trông hợp lý mà sai. Sửa thể tích mà để renderer lấp
    // phần lõm là chữa nửa bệnh: con số đúng, thứ học sinh NHÌN THẤY vẫn sai.
    const dinh = o.vertices.map(toVec3);
    const pos: number[] = [];
    for (const f of o.faces) {
      const mat = f.map((j) => dinh[j]);
      for (const [a, b, c] of chiaTamGiac(mat)) {
        for (const k of [a, b, c]) pos.push(...mat[k]);
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

  // ── MẶT của khối: hình ĐẶC, để bấm trúng được ─────────────────────────
  //
  // `polygon` bình thường vẽ bằng đường viền, và một đường viền dày 1px gần
  // như không bấm trúng. Mặt thì phải bấm được — đó là toàn bộ điểm của việc
  // sinh ra nó. Phép chia tam giác ở đây là phép chia LIST trên thứ tự đỉnh do
  // kernel quyết, cùng khuôn với nhánh `mesh`; không có phép hình học nào —
  // và nó xử lý được mặt LÕM, xem `polygon-triangulate.ts`.
  if (o.type === "face" && o.polygon && o.polygon.length >= 3) {
    const pts = o.polygon.map(toVec3);
    const pos: number[] = [];
    for (const [a, b, c] of chiaTamGiac(pts)) {
      for (const j of [a, b, c]) pos.push(...pts[j]);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.computeVertexNormals();
    return v(new THREE.Mesh(g, new THREE.MeshStandardMaterial({
      color: mau ?? MAU.polygon,
      transparent: true,
      opacity: noiBat ? 0.55 : 0.14,
      side: THREE.DoubleSide,
      depthWrite: false,
    })), `face:${o.id}`);
  }

  if (o.type === "edge" && o.polygon && o.polygon.length === 2) {
    const g = new THREE.BufferGeometry().setFromPoints(
      o.polygon.map((x) => new THREE.Vector3(...toVec3(x))));
    return v(new THREE.Line(g, new THREE.LineBasicMaterial({
      color: mau ?? MAU.line, linewidth: 2,
    })), `edge:${o.id}`);
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

/**
 * Trong danh sách va chạm (đã sắp theo KHOẢNG CÁCH), chọn vật CỤ THỂ NHẤT.
 *
 * ─── HAI LẦN SAI, HAI LÝ DO KHÁC NHAU ───────────────────────────────────
 *
 * ① Bản đầu lấy thẳng `ids[0]`. Mặt của khối nằm ĐÚNG trên bề mặt khối nên
 *    tia trúng cả hai, và học sinh bấm vào mặt SAB thì hệ trả về cả hình chóp.
 * ② Bản sửa lấy "vật con đầu tiên" — và thế là ĐIỂM không bao giờ chọn được:
 *    một đỉnh nằm trên mặt khối, tia trúng cả điểm (gần hơn) lẫn mặt, mà luật
 *    ấy nhảy qua điểm để lấy mặt. Demo tay đo được: 0/144 cú bấm trúng điểm.
 *
 * Luật đúng giữ NGUYÊN thứ tự khoảng cách và chỉ **hạ bệ đúng một thứ**: một
 * KHỐI bị bỏ qua khi chính mặt/cạnh của nó cũng nằm trong danh sách. Không có
 * vật con nào thì khối vẫn chọn được như thường.
 */
export function chonCuThe(
  ids: string[],
  loaiCua?: (id: string) => string | undefined,
): string | null {
  if (ids.length === 0) return null;
  const cha = new Set(
    ids.map((x) => parentSolidOf(x)).filter((x): x is string => !!x),
  );
  if (!loaiCua) return ids.find((x) => !cha.has(x)) ?? ids[0];
  // Xếp theo HẠNG CỤ THỂ, giữ thứ tự khoảng cách trong cùng hạng. Một vật
  // chỉ vào danh sách khi tia THẬT SỰ trúng vùng bấm của nó, nên "ưu tiên
  // điểm" không bao giờ cướp được một mặt ở xa con trỏ.
  let tot = ids[0];
  let hang = hangCuThe(loaiCua(ids[0]));
  for (const x of ids.slice(1)) {
    const h = hangCuThe(loaiCua(x));
    if (h < hang) { tot = x; hang = h; }
  }
  return tot;
}

/**
 * Đặt vị trí TRÌNH BÀY = **vị trí gốc của vật CỘNG khoảng dịch bung hình**.
 *
 * ─── LỖI ĐÃ QUAN SÁT, VÀ NÓ LÀ CỦA TÔI ──────────────────────────────────
 *
 * Bản trước viết `obj.position.set(bd.translate…)` — **GHI ĐÈ**, không cộng.
 * Với hầu hết đối tượng điều đó vô hại: đường, mặt, khối, đa giác đều nướng
 * toạ độ vào `BufferGeometry`, nên `position` của chúng vốn là gốc.
 *
 * Nhưng ĐIỂM thì không: `buildObject3D` đặt cả nhóm tại `o.xyz`. Ghi đè bằng
 * đồng nhất thức `(0,0,0)` kéo **mọi điểm về gốc toạ độ**. `plane3` cũng vậy
 * (`mesh.position.set(...o.point)`).
 *
 * Triệu chứng khớp chính xác với thứ demo tay đo được: `A(0,0,0)` bấm được —
 * vì nó vốn ở gốc — còn `B(2,0,0)`, `C(2,2,0)`, `D(0,2,0)`, `S(0,0,2)` thì
 * không, và 2907 lượt bấm nhắm cũng không cứu được, vì chúng KHÔNG NẰM Ở CHỖ
 * lẽ ra chúng phải nằm. Đó không phải chuyện đích bấm nhỏ.
 *
 * ⚠️ MỘT thẩm quyền đặt vị trí, áp cho CẢ NHÓM: chấm nhìn thấy và hình cầu
 * bắt con trỏ là hai con của cùng một nhóm, nên chúng không thể lệch nhau.
 */
export function datViTriTrinhBay(
  obj: THREE.Object3D,
  bd: { translate: [number, number, number] },
): void {
  obj.position.set(
    obj.position.x + bd.translate[0],
    obj.position.y + bd.translate[1],
    obj.position.z + bd.translate[2],
  );
}

interface Props {
  scene: Scene3D;
  step: number;
  /** Cách nhìn hiện tại. Vắng ⇒ hiện mọi thứ, không bung — hành vi cũ. */
  interaction?: InteractionState;
  /** Bấm vào một vật. Vắng ⇒ khung 3D chỉ để xem. */
  onSelect?: (id: string | null) => void;
  /**
   * Tăng giá trị này để yêu cầu ĐẶT LẠI KHUNG NHÌN cho vừa hình.
   *
   * Là một con số chứ không phải một hàm, vì nơi gọi (nút "Xem lại toàn hình")
   * nằm ở component cha còn camera thuộc renderer. Truyền hàm xuống sẽ buộc
   * cha giữ một ref vào ruột renderer — đúng kiểu đảo hướng phụ thuộc mà bản
   * đồ kiến trúc cấm.
   */
  fitToken?: number;
}

export function Scene3DWorkspace({ scene, step, interaction, onSelect, fitToken = 0 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rootRef = useRef<THREE.Group | null>(null);
  const veRef = useRef<(() => void) | null>(null);
  //: Đặt lại khung nhìn cho vừa hình. Giữ trong ref vì nó do vòng dựng cảnh
  //: tạo ra (cần `cam`, `controls`) nhưng được gọi từ ngoài vòng ấy.
  const vuaKhungRef = useRef<(() => void) | null>(null);
  const [webglFailed, setWebglFailed] = useState(false);
  const buoc = clampStep(scene, step);
  // Vắng `interaction` ⇒ trạng thái đầu, tức hành vi TRƯỚC wave này nguyên
  // vẹn: hiện mọi thứ, không bung, tô sáng theo bước.
  const tuongTac = interaction ?? TRANG_THAI_DAU;
  const chonRef = useRef(onSelect);
  chonRef.current = onSelect;
  // `id → type`, để luật chọn biết cái nào cụ thể hơn. `ref` vì vòng lặp
  // raycast sống trong một `useEffect` chạy MỘT LẦN.
  const loaiRef = useRef(new Map<string, string>());
  loaiRef.current = new Map(scene.objects.map((o) => [o.id, o.type]));
  const nhanRef = useRef<HTMLDivElement>(null);
  //: `id → vị trí THẾ GIỚI` của nhãn. Ghi trong vòng dựng cảnh, đọc trong
  //: vòng vẽ — hai nhịp khác nhau nên phải đi qua `ref`, không qua state.
  const viTriNhan = useRef(new Map<string, THREE.Vector3>());

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
      // NGƯỠNG DẪN TỪ CAMERA, không phải hằng số. `Raycaster` đo ở không gian
      // THẾ GIỚI còn ngón tay đo bằng ĐIỂM ẢNH: một ngưỡng vừa tay ở góc nhìn
      // mặc định thành hạt bụi khi phóng to. `cam.position.length()` — camera
      // luôn nhìn về gốc — chứ KHÔNG một phép đo khoảng cách hình học nào, vốn
      // bị guard cấm ở tầng này.
      const kc = cam.position.length();
      tia.params.Line = { threshold: nguongBamCanh(kc) };
      tia.params.Points = { threshold: nguongBamCanh(kc) };
      tia.setFromCamera(diem, cam);
      const trung = tia.intersectObjects(goc.children, true);
      const ids = trung
        .map((h) => pickSemanticId(h.object))
        .filter((x): x is string => typeof x === "string" && x.length > 0);
      chonRef.current(chonCuThe(ids, (id) => loaiRef.current.get(id)));
    };
    renderer.domElement.addEventListener("pointerdown", xuongTay);
    renderer.domElement.addEventListener("pointerup", nhacTay);

    // ── NHÃN ĐIỂM, CHIẾU RA MÀN HÌNH MỖI KHUNG ──────────────────────────
    //
    // Học sinh đọc hình bằng TÊN ĐIỂM: "AB", "SAB", "trung điểm M". Một khối
    // 3D không nhãn buộc họ tra sang bảng bên cạnh rồi quay lại — và chính chỗ
    // quay đi quay lại ấy là nơi hình mất nghĩa.
    //
    // Nhãn là DOM, không phải sprite: chữ nét thật, ăn theo token màu, đọc
    // được bởi trình đọc màn hình, và không tốn một texture nào. Cập nhật
    // bằng cách ghi thẳng `style` trong vòng vẽ — đi qua state React thì mỗi
    // khung là một lần dựng lại cây.
    //
    // `cam.project` ở đây là phép CHIẾU TRÌNH BÀY, không phải suy luận hình
    // học: đầu ra là vị trí điểm ảnh của một nhãn, không quay lại `GeometryState`.
    const chieuNhan = () => {
      const lop = nhanRef.current;
      if (!lop) return;
      const w = renderer.domElement.clientWidth || 1;
      const h = renderer.domElement.clientHeight || 1;
      // Chiếu trước, LỌC CHỒNG sau. Bản trước hiện mọi nhãn, và ảnh chụp thật
      // cho thấy bốn câu mô tả đè lên nhau ngay giữa hình. Lọc ở đây chứ
      // không ở lúc dựng cảnh, vì hai nhãn có chồng nhau hay không phụ thuộc
      // GÓC NHÌN — thứ chỉ biết được sau phép chiếu.
      const dat: { el: HTMLElement; id: string; x: number; y: number; uuTien: number }[] = [];
      for (const el of Array.from(lop.children) as HTMLElement[]) {
        const id = el.dataset.id;
        const v = id ? viTriNhan.current.get(id) : undefined;
        if (!v || !id) { el.style.opacity = "0"; continue; }
        const p3 = v.clone().project(cam);
        // Sau lưng camera ⇒ giấu. Không có phép kiểm này thì nhãn của mặt
        // khuất lộn ngược lên trước hình.
        const hien = p3.z < 1 && p3.x > -1.1 && p3.x < 1.1 && p3.y > -1.1 && p3.y < 1.1;
        if (!hien) { el.style.opacity = "0"; continue; }
        const x = ((p3.x + 1) / 2) * w;
        const y = ((1 - p3.y) / 2) * h;
        el.style.transform = `translate(-50%,-140%) translate(${x}px,${y}px)`;
        dat.push({ el, id, x, y, uuTien: Number(el.dataset.uuTien ?? "1") });
      }
      const giu = locNhanChongNhau(dat);
      for (const d of dat) d.el.style.opacity = giu.has(d.id) ? "1" : "0";
    };

    let song = true;
    const vong = () => {
      if (!song) return;
      dieuKhien.update();
      renderer.render(scene3, cam);
      chieuNhan();
      requestAnimationFrame(vong);
    };
    veRef.current = () => renderer.render(scene3, cam);

    // ── ĐẶT KHUNG NHÌN CHO VỪA HÌNH ────────────────────────────────────
    //
    // Đọc hộp bao của những gì ĐANG dựng trong nhóm gốc, không đọc `scene` —
    // ẩn/cô lập/tách khối đều đã phản ánh vào nhóm, nên một nguồn là đủ.
    vuaKhungRef.current = () => {
      const diem: [number, number, number][] = [];
      // ⚠️ BỎ VẬT VÔ HẠN KHỎI PHÉP TÍNH KHUNG NHÌN.
      //
      // `setFromObject(goc)` ôm trọn mọi thứ đang dựng — kể cả miếng mặt phẳng
      // và đoạn đại diện của đường thẳng, hai thứ có cỡ do CHÍNH tầng trình bày
      // chọn. Để chúng vào thì quyết định trình bày tự khuếch đại: miếng to ra
      // ⇒ hộp bao to ra ⇒ camera lùi ⇒ hình thật bé lại. Vòng lặp ấy không có
      // điểm dừng nào ngoài may rủi.
      const hop = new THREE.Box3();
      const hopVat = new THREE.Box3();
      goc.traverse((vat) => {
        if (vat.userData?.voHan) return;
        if (!(vat as THREE.Mesh).isMesh && !(vat as THREE.Line).isLine) return;
        if (vat.name === "pick-proxy") return;   // hình cầu bắt chuột, không phải hình
        hopVat.setFromObject(vat);
        if (!hopVat.isEmpty()) hop.union(hopVat);
      });
      // Cảnh CHỈ có mặt phẳng/đường thẳng: thà lấy hộp bao đầy đủ còn hơn
      // không đặt được khung nhìn nào.
      if (hop.isEmpty()) hop.setFromObject(goc);
      if (!hop.isEmpty()) {
        diem.push([hop.min.x, hop.min.y, hop.min.z],
          [hop.max.x, hop.max.y, hop.max.z]);
      }
      /* ⚠️ VÀ CẢ VẬT CHƯA XUẤT HIỆN — đây là bản sửa của một lỗi đo được.
       *
       * Khung nhìn cố ý **đứng yên** giữa các bước (nếu không, tua bước biến
       * thành đổi góc máy). Nhưng nó được tính từ những gì đang dựng ở lúc
       * gọi, tức **bước 0** — khi cảnh mới chỉ có vài điểm tự do. Ở `p3`, hộp
       * bao lúc ấy là hai điểm cách nhau 15 đơn vị; tới bước cuối mặt cầu bán
       * kính 15 xuất hiện và **tràn ra ngoài khung**, bị cắt cả trên lẫn dưới.
       *
       * Sửa bằng cách khung nhìn ôm **toàn cảnh** ngay từ đầu: camera vẫn đứng
       * yên (bất biến giữ nguyên), nhưng nó đứng ở chỗ nhìn được hình CUỐI.
       * Hợp với hộp bao đang dựng để phép tách khối vẫn đúng. */
      for (const p of diemHuuHan(scene.objects)) diem.push(p);
      if (diem.length === 0) return;
      const w = renderer.domElement.clientWidth || 1;
      const h = renderer.domElement.clientHeight || 1;
      const kn = khungNhinVua(hopBaoCuaDiem(diem), cam.fov, w / h);
      if (!kn) return;   // đầu vào không dùng được ⇒ giữ nguyên khung nhìn
      cam.position.set(...kn.viTri);
      dieuKhien.target.set(...kn.nhinVao);
      dieuKhien.update();
      cam.updateProjectionMatrix();
    };

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
      vuaKhungRef.current = null;
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
    viTriNhan.current.clear();
    const noiBat = new Set(
      tuongTac?.selected_id
        ? highlightSet(scene, tuongTac.selected_id)
        : highlightedAt(scene, buoc),
    );
    // MỘT thẩm quyền "vật nào đang có mặt", dùng chung với cây phân rã.
    //
    // Bản trước hỏi thẳng `objectsAt` ở đây còn cây hỏi `entitiesPresentAt`.
    // Hai phép khác nhau: mặt và cạnh KHÔNG có sự kiện timeline riêng, nên
    // `objectsAt` bỏ chúng ra — cây liệt kê được mặt mà khung nhìn không dựng
    // mặt nào, và raycast chỉ còn trúng khối. Demo tay bắt đúng chuyện đó.
    const daTonTai = entitiesPresentAt(scene, buoc, objectsAt);
    const hienTai = scene.objects.filter((o) => daTonTai.has(o.id));
    /* Nền hình học để cắt mặt phẳng vô hạn: lấy từ vật ĐANG HIỆN, không từ cả
       cảnh. Bước 1 chưa có khối thì miếng mặt phẳng cũng chưa được phình ra
       ôm một khối chưa xuất hiện — mắt đọc đúng thứ tự dựng. */
    const diemNen = diemHuuHan(hienTai);
    for (const o of hienTai) {
      // ẨN / CÔ LẬP quyết định CÓ DỰNG HAY KHÔNG — không dựng rồi giấu, vì
      // một mesh vô hình vẫn nằm trên đường raycast và vẫn ăn cú bấm.
      if (!isVisible(tuongTac, o.id, daTonTai)) continue;
      // Backend NÓI vật nào không có hình trên khung (`render: "non_visual"` —
      // hiện là vectơ, vì một vectơ tự do không có vị trí). Phía này chỉ tuân
      // theo; nó không còn đoán bằng `producer` như bản trước.
      if (!veTrenKhung(o)) continue;
      const obj = buildObject3D(o, noiBat.has(o.id),
        banKinhBamDiem(KHOANG_CAM_MAC_DINH), diemNen);
      if (!obj) continue;
      const bd = visualTransformOf(tuongTac, scene, o.id);
      datViTriTrinhBay(obj, bd);
      goc.add(obj);
      // Chỉ ĐIỂM mang nhãn. Gắn nhãn cho cạnh và mặt nữa thì một tứ diện đã
      // có 19 chữ chồng lên nhau, và hình thành một mớ chữ có hình.
      if (o.type === "point3" && o.xyz) {
        const [x, y, z] = toVec3(o.xyz);
        viTriNhan.current.set(o.id, new THREE.Vector3(
          x + bd.translate[0], y + bd.translate[1], z + bd.translate[2]));
      }
    }
    veRef.current?.();
  }, [scene, buoc, tuongTac]);

  // ── KHI NÀO ĐẶT LẠI KHUNG NHÌN ────────────────────────────────────────
  //
  // Cố ý **không** có `buoc` trong danh sách phụ thuộc. Đặt lại khung nhìn ở
  // mỗi bước sẽ biến việc tua bước thành việc đổi góc máy: người xem thấy hình
  // nhúc nhích và không phân biệt được đâu là vật mới dựng, đâu là camera vừa
  // dịch. Hai hình so sánh bước 5 với bước 12 chỉ có nghĩa khi khung nhìn đứng
  // yên giữa hai bước.
  //
  // Ba dịp được đặt lại, và cả ba đều là lúc TẬP VẬT ĐANG THẤY đổi hẳn:
  // nạp cảnh khác · người dùng bấm xem lại toàn hình (`fitToken`) · tách hoặc
  // ráp khối (`exploded_groups`).
  const daBung = tuongTac.exploded_groups.join("|");
  useEffect(() => {
    vuaKhungRef.current?.();
  }, [scene, fitToken, daBung]);

  const hien = objectsAt(scene, buoc);
  const soDo = hien.filter((o) => o.render === "readout");
  // Chỉ in nhãn cho vật CÓ ký hiệu do backend phát. Vật không có ký hiệu thì
  // khung không in gì cho nó — trước bản này phía đây tự rút một ký hiệu từ
  // `id`, nên `plane_MNP` hiện thành `MNP` và `V_AMNP` hiện nguyên si.
  const nhanDiem = hien.filter(
    (o) => o.type === "point3"
      && veTrenKhung(o)
      && kyHieu(o) !== null
      && isVisible(tuongTac, o.id, new Set(hien.map((x) => x.id))),
  );

  return (
    <div className="geo3d">
      {webglFailed ? (
        <p className="geo3d-fallback">{GEOMETRY_WEBGL_FALLBACK}</p>
      ) : (
        <div ref={containerRef} className="geo3d-canvas">
          {/* Lớp NHÃN nằm trên canvas và KHÔNG bắt chuột (`pointer-events`
              tắt trong CSS) — nếu bắt, một chữ "B" sẽ nuốt cú bấm vào chính
              điểm B nằm ngay dưới nó. */}
          <div ref={nhanRef} className="geo3d-labels" aria-hidden="true">
            {nhanDiem.map((o) => (
              <span
                key={o.id}
                data-id={o.id}
                className={`geo3d-label${
                  tuongTac.selected_id === o.id ? " la-chon" : ""
                }`}
                data-uu-tien={uuTienNhan(o, tuongTac.selected_id)}
                title={o.label}
              >
                {kyHieu(o)}
              </span>
            ))}
          </div>
        </div>
      )}
      {/* Số đo là CÂU TRẢ LỜI của bài — nó ở lại trong khung, nổi trên hình,
          chứ không tụt xuống một danh sách dưới chân trang. */}
      {soDo.length > 0 && (
        <ul className="geo3d-readout">
          {soDo.map((o) => (
            <li key={o.id}>
              <span className="geo3d-readout-ten">{o.label}</span>
              {/* Định dạng từ CẤU TRÚC (`exact`), lùi về chuỗi backend dựng
                  chỉ khi envelope cũ không có. Hai bên định dạng độc lập là
                  cách duy nhất phát hiện khi chúng lệch nhau. */}
              <span className="geo3d-readout-gt">{hienSo(o.exact, o.value)}</span>
            </li>
          ))}
        </ul>
      )}
      {/* Nội suy GỘP thành MỘT chuỗi: `{a}/{b}` làm SSR chèn marker
          `<!-- -->` vào giữa, nên chữ hiện ra đúng mà mọi phép kiểm chuỗi lại
          trượt — một lệch câm giữa thứ người đọc thấy và thứ test đọc. */}
      <p className="geo3d-progress geo3d-sr">
        {`Bước ${buoc + 1}/${stepCount(scene)}`}
      </p>
      <p className="geo3d-narration geo3d-sr">{narrationAt(scene, buoc)}</p>
    </div>
  );
}
