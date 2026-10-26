import { useEffect, useMemo, useRef, useState } from "react";
import { chiaTamGiac } from "./polygon-triangulate";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  LINE_DISPLAY_HALF_LENGTH,
  PLANE_DISPLAY_SIZE,
  VONG_CHIA,
  clampStep,
  SECTION_STROKE_RATIO,
  cauTrucGocNhin,
  daGiacMatPhang,
  dayVaDinhChop,
  diemHuuHan,
  diemChoDuong,
  diemNeoNhanMatPhang,
  doanDuongThang,
  duongKinhCanh,
  geometryHighlightedAt,
  geometryNarrationAt,
  geometryStepCount,
  geometryStepOf,
  huongChanVuongGoc,
  khungMatPhang,
  measurementOnlyPlanes,
  moRongDaGiacMatPhang,
  objectsAt,
  toNumber,
  toVec3,
  type GeometryProgress,
  type Scene3D,
  type SceneObject,
  type Vec3,
} from "./scene3d-model";
import {
  type InteractionState,
  type TangNhanManh,
  TRANG_THAI_DAU,
  highlightSet,
  isVisible,
  tangNhanManh,
  visualTransformOf,
} from "./interaction-state";
import { diemTaiDinhThietDien, entitiesPresentAt, parentSolidOf } from "./scene3d-subentities";
import {
  canonicalEdgesOf,
  classifySolidEdgeVisibility,
  classifyWorldSegmentVisibility,
  createWorldPointOcclusionTest,
  curvedSurfaceTangentTurns,
  updateCurvedSolidSilhouette,
  dongBoNetDayManHinh,
  taoGiuAmNetDay,
  type CurvedSolidVolumeMeta,
  type EdgeVisibilityAudit,
  type WorldSolidOccluder,
} from "./scene3d-edge-visibility";
export { classifySolidEdgeVisibility, dongBoNetDayManHinh } from "./scene3d-edge-visibility";
import {
  BAN_KINH_NHIN,
  KHOANG_CAM_MAC_DINH,
  banKinhBamDiem,
  banKinhBamPx,
  coDauDinhPx,
  donViMoiPx,
  hangCuThe,
  nguongBamCanh,
} from "./pick-target";
import {
  kyHieu,
  kyHieuDiem,
  locNhanChongNhau,
  uuTienNhan,
  veTrenKhung,
} from "./scene3d-presentation";
import {
  type KhungNhin, chonHuongNhin, hopBaoCuaDiem, huongLenHienThi, khungNhinSuPham, khungNhinVua,
  tiLeHinhChieu,
} from "./scene3d-camera";
import { MAU_VAI_TRO, PHONG_CACH_SCENE3D, vaiTroKhoi, vaiTroMien, type VaiTroKhoi } from "./scene3d-roles";
import {
  type AnnotationView,
  type LabelRect,
  type LabelToPlace,
  type WitnessShown,
  DEFAULT_ANNOTATION_VIEW,
  annotationAnchor,
  annotationsAt,
  placeAnnotationLabels,
  projectionWitnessesAt,
  witnessesShown,
} from "./scene3d-annotations";
import { namTrenDoanDaVe, nhanChungDoanHopLe } from "./scene3d-witness-gate";
import { auxiliaryHiddenAt } from "./scene3d-auxiliary";
import { maTranKhung4 } from "./scene3d-chart";

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

const MAU = { ...PHONG_CACH_SCENE3D.colors, highlight: MAU_VAI_TRO.moi_dung };
const DO_DUC = PHONG_CACH_SCENE3D.opacity;
const NET = PHONG_CACH_SCENE3D.width;

/** Chuỗi nhân quả quanh vật đang chọn (`tangNhanManh`): đích xanh, dữ kiện số
 *  cam đậm, trung gian số cam nhạt — CÙNG bảng với bảng lời giải
 *  (`scene3d-roles.ts`). NGỮ CẢNH cấu trúc không có màu nét — giữ mực trung
 *  tính, chỉ tô nền xám nhạt. Ngoài chuỗi: làm dịu. */
const MAU_TANG: Record<Exclude<TangNhanManh, "boi_canh">, number> = {
  dich: MAU_VAI_TRO.dich,
  du_kien_so: MAU_VAI_TRO.du_kien_so,
  trung_gian: MAU_VAI_TRO.trung_gian,
};
const MAU_NEN_BOI_CANH = MAU_VAI_TRO.nen_boi_canh;
const HE_SO_LAM_DIU = DO_DUC.fade;
/** Đường VÔ HẠN (đường phụ) không được nhấn: lùi xuống, không biến mất (w11). */
const HE_SO_DUONG_PHU = DO_DUC.auxiliary;

function lamDiuVatLieu(m: THREE.Material, k: number): void {
  if ((m as THREE.Material & { colorWrite?: boolean }).colorWrite === false) return;
  m.transparent = true;
  m.opacity *= k;
}

/** Làm dịu cả một vật — trừ cạnh chuẩn đang được tô qua vật khác trong chuỗi. */
export function lamDiu(obj: THREE.Object3D, k = HE_SO_LAM_DIU): void {
  const bo = new Set<THREE.Object3D>();
  const daDiu = new Set<THREE.Material>();
  obj.traverse((x) => {
    if (x.userData?.visualOwnerId && x.userData.highlighted === true) x.traverse((y) => bo.add(y));
  });
  obj.traverse((x) => {
    if (bo.has(x)) return;
    if (x.userData?.visualOwnerId) x.userData.lamDiu = k;
    if (x.userData?.nonCanonicalSegment || x.userData?.nonCanonicalLoop) {
      x.userData.lamDiu = ((x.userData.lamDiu as number | undefined) ?? 1) * k;
    }
    if (x.userData?.sang === true) return;   // khúc tô sáng của đoạn con nằm trên cạnh (W4)
    const m = (x as THREE.Mesh).material as THREE.Material | THREE.Material[] | undefined;
    for (const vl of Array.isArray(m) ? m : m ? [m] : []) {
      if (daDiu.has(vl)) continue;
      lamDiuVatLieu(vl, k);
      daDiu.add(vl);
    }
  });
}

/** A visual owner keeps its few semantic span styles while orbit only changes their geometry. */
function spanMaterial<T extends THREE.Material>(owner: THREE.Object3D, key: string, create: () => T): T {
  const pool: Map<string, THREE.Material> = owner.userData.spanMaterialPool ??= new Map();
  if (!pool.has(key)) {
    const material = create();
    material.userData.spanPooled = true;
    pool.set(key, material);
  }
  return pool.get(key) as T;
}

/** Release both attached resources and inactive pooled styles when the owner is rebuilt or unmounted. */
export function disposeScene3DObject(root: THREE.Object3D): void {
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();
  root.traverse(node => {
    const mesh = node as THREE.Mesh;
    if (mesh.geometry) geometries.add(mesh.geometry);
    for (const g of (node.userData.spanGeoPool ?? []) as THREE.BufferGeometry[]) geometries.add(g);
    for (const m of (node.userData.spanMaterialPool as Map<string, THREE.Material> | undefined)?.values() ?? []) materials.add(m);
    for (const m of Array.isArray(mesh.material) ? mesh.material : mesh.material ? [mesh.material] : []) materials.add(m);
  });
  for (const geometry of geometries) geometry.dispose();
  for (const material of materials) material.dispose();
}

/** Toạ độ cảnh → khung THẾ GIỚI qua phép xoay hiển thị (đồng nhất thức khi đáy ngang — trả lại chính các số). */
const DONG_NHAT = new THREE.Quaternion();

function xoay(p: Vec3, q: THREE.Quaternion): Vec3 {
  if (q.equals(DONG_NHAT)) return p;
  const w = new THREE.Vector3(...p).applyQuaternion(q);
  return [w.x, w.y, w.z];
}

/** Phép xoay hiển thị của cảnh (`huongLenHienThi`): đáy chóp nghiêng về nằm ngang; đáy ngang ⇒ đồng nhất thức. */
export function quayHienThi(objects: SceneObject[]): THREE.Quaternion {
  const dc = dayVaDinhChop(objects);
  const len = dc ? huongLenHienThi(dc.day, dc.dinh) : null;
  return len
    ? new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(...len), new THREE.Vector3(0, 0, 1))
    : new THREE.Quaternion();
}

/** Đỉnh/cạnh/mặt của cảnh (`cauTrucGocNhin`) trong khung THẾ GIỚI — sau phép xoay hiển thị. */
function cauTrucTheGioi(objects: SceneObject[], q: THREE.Quaternion) {
  const ct = cauTrucGocNhin(objects);
  return { ...ct, diem: ct.diem.map((p) => xoay(p, q)) };
}

/**
 * TỈ LỆ cao/rộng của HÌNH ở góc nhìn mặc định (mobile-canvas-fit, D5) — cùng điểm, cùng phép xoay hiển thị, cùng
 * hướng `chonHuongNhin` mà khung nhìn vừa (`vuaKhungRef`) dùng; chỉ phụ thuộc cảnh, nên không đổi theo bước, lựa
 * chọn, tách khối hay bảng. `null` khi cảnh không cạnh (khung cũ ôm mặt cầu bao — không có tỉ lệ hình chiếu).
 */
export function tiLeKhungHinh(objects: SceneObject[]): number | null {
  const q = quayHienThi(objects);
  const ct = cauTrucTheGioi(objects, q);
  if (ct.canh.length === 0) return null;
  return tiLeHinhChieu(diemHuuHan(objects).map((p) => xoay(p, q)), chonHuongNhin(ct.diem, ct.canh, ct.mat));
}

function v(o: THREE.Object3D, name: string): THREE.Object3D {
  o.name = name;
  return o;
}

/* ⚠️ `VAT_LIEU_THIET_DIEN = { depthTest: false }` ĐÃ GỠ (2026-09-09).
 *
 * Nó ra đời để đường tròn thiết diện của `p3` không bị mặt cầu nuốt mất — và
 * nó làm được, bằng cách vẽ thiết diện ĐÈ LÊN MỌI THỨ. Cái giá chỉ lộ ra khi
 * hỏi câu tiếp theo: khi mọi phần đều vẽ đè, phần THẤY và phần KHUẤT hiện y
 * hệt nhau, nên hình mất luôn khả năng trả lời *"đoạn này nằm trước hay sau
 * khối"*. Với hình học không gian thì đó không phải chi tiết trang trí — đó
 * là thông tin chính.
 *
 * Nay thiết diện đi qua đúng phép kiểm chiều sâu như mọi đường khác, và phần
 * khuất vẫn đọc được vì nó **vẫn được vẽ**, chỉ ở dạng ngắt quãng và nhạt hơn.
 */

/** Vẽ sau mọi vật khác. Số lớn = vẽ sau, theo quy ước của three.js. */
export const THU_TU_VE_THIET_DIEN = 10;

/**
 * Thứ tự vẽ PHẦN TÔ thiết diện (W16, ASSUMPTION_CERTIFICATE_AMENDMENT §14.4): sau mặt khối
 * và mặt cắt (0), TRƯỚC mọi nét (`THU_TU_DUONG`). Ở 10 (W15) phần tô — không kiểm chiều sâu —
 * phủ hổ phách lên cạnh khối đi qua vùng thiết diện (ảnh cross-section W15: SA, SC nhuộm nâu).
 * `renderOrder` chỉ xếp TRONG một hàng đợi: cạnh khối chuẩn ở hàng đợi trong suốt
 * (`canonicalEdgeMaterial`) nên vẽ đè lên phần tô; nét liền ĐỤC (đoạn phụ, viền đa giác) vẫn
 * chạy trước toàn bộ hàng đợi trong suốt.
 */
export const THU_TU_TO_THIET_DIEN = 7;

/**
 * Độ đục phần TÔ của thiết diện khép kín (W15). Nhánh đa giác chung tô 0.16 — đồng phẳng
 * với miếng mặt cắt tím (0.20) và trước khối xám (0.22) thì vùng thiết diện hoà mất. Cổng
 * ảnh `SECTION_FILL_DISTINGUISHABLE` đo bật/tắt phần tô ở CÙNG khung hình theo ngưỡng
 * đăng ký trước (`ASSUMPTION_CERTIFICATE_AMENDMENT.md` §11); trượt ngưỡng thì chỉnh hằng
 * này, không chỉnh ngưỡng.
 */
export const DO_DUC_TO_THIET_DIEN = DO_DUC.section;

/* ══ NÉT LIỀN / NÉT KHUẤT THEO CAMERA ═══════════════════════════════════
 *
 * ─── VÌ SAO TRƯỚC ĐÂY KHÔNG CÓ CHE KHUẤT NÀO CẢ ────────────────────────
 *
 * **Mọi** khối trong renderer này khai `depthWrite: false` — khối đa diện,
 * khối cong, mặt, miếng mặt phẳng. Không ai ghi chiều sâu thì không gì che
 * được gì: một cạnh nằm sau quả cầu vẫn vẽ y như cạnh nằm trước nó. Đó không
 * phải "hidden-line làm chưa tốt", mà là **chưa từng có hidden-line**.
 *
 * ─── GIẢI PHÁP NHỎ NHẤT PHÙ HỢP RENDERER NÀY ───────────────────────────
 *
 * Hai mảnh, không mảnh nào cần tính hình học:
 *
 *   ① LỚP CHIỀU SÂU RIÊNG. Mỗi khối THẬT (đa diện, khối cong) kèm một bản
 *      sao vô hình chỉ ghi chiều sâu (`colorWrite:false, depthWrite:true`).
 *      Miếng mặt phẳng, nhãn và lưới **không** có bản sao ấy — chúng là vật
 *      minh hoạ, không được che gì.
 *   ② VẼ HAI LƯỢT cho mỗi đường: lượt thứ nhất `depthFunc: LessEqualDepth`
 *      (phần THẤY, nét liền), lượt thứ hai `GreaterDepth` + nét đứt (phần
 *      KHUẤT). GPU quyết định theo TỪNG ĐIỂM ẢNH, nên một cạnh tự chia thành
 *      nhiều đoạn thấy/khuất, và xoay camera thì phân loại đổi theo — không
 *      có cache nào để lỗi thời.
 *
 * Cách này rẻ hơn hẳn depth-pass đọc ngược hay phân đoạn trên CPU, và nó
 * KHÔNG sinh vật mới trong cảnh: bản sao chiều sâu vô hình, không bắt chuột,
 * không vào hộp bao, không vào `final_memory`. Nó là chi tiết TRÌNH BÀY.
 */

/** Thứ tự vẽ: khối tô bóng → lớp chiều sâu → phần tô thiết diện → đường → viền thiết diện. */
const THU_TU_CHIEU_SAU = 5;
const THU_TU_DUONG = 8;

/**
 * ĐỘ LỆCH CHIỀU SÂU của thiết diện — `units` thuần, KHÔNG có `factor`.
 *
 * ⚠️ `polygonOffsetFactor` co giãn theo ĐỘ DỐC của mặt so với hướng nhìn. Với
 * một vành nằm trong mặt cắt dốc — đúng ca `p3` và `p7` ở góc mặc định — độ
 * dốc lớn làm độ lệch bị khuếch đại tới mức CẢ vành thắng phép kiểm chiều sâu,
 * và thiết diện lại vẽ liền toàn bộ y như thời `depthTest: false`. Triệu chứng
 * đo được: `p7` 0 lần đổi nét ở góc mặc định, còn `p3` chỉ hiện nét đứt SAU
 * KHI XOAY — tức một lỗi phụ thuộc góc nhìn, thứ ảnh tĩnh một góc không bắt
 * được.
 *
 * `units` là hằng số theo đơn vị nhỏ nhất của bộ đệm chiều sâu: đủ để vành
 * không nhấp nháy khi nằm ĐÚNG trên mặt khối, và không đủ để nó nhảy ra trước
 * cả một khối.
 */
const LECH_THIET_DIEN = {
  polygonOffset: true, polygonOffsetFactor: 0, polygonOffsetUnits: -1,
} as const;

/** Chu kỳ nét đứt, theo tỉ lệ cảnh — đọc được ở mọi mức thu phóng. */
const NET_DUT_TI_LE = PHONG_CACH_SCENE3D.dash.relative;

/** Bản sao VÔ HÌNH chỉ ghi chiều sâu mặt SAU (ở hàng đợi đục, trước phần tô thiết diện ở thứ tự 7)
 *  để phần tô thiết diện nằm TRONG khối vượt qua phép kiểm `LessEqualDepth` ở chế độ thường mà vẫn bị
 *  khối khác nằm hẳn phía trước che đúng. */
function lopChieuSau(g: THREE.BufferGeometry): THREE.Mesh {
  const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({
    colorWrite: false, depthWrite: true, depthTest: true,
    side: THREE.BackSide,
    transparent: false,
    polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
  }));
  m.renderOrder = THU_TU_CHIEU_SAU;
  m.userData.chieuSau = true;      // không bắt chuột, không vào hộp bao
  return m;
}

/** Bản sao VÔ HÌNH ghi chiều sâu mặt TRƯỚC ở thứ tự 7.5 (sau phần tô thiết diện ở 7, trước mọi đường ở 8..10)
 *  để các đường/nét nằm sau mặt trước của khối bị phân loại là khuất bởi phép kiểm chiều sâu GPU. */
function lopChieuSauMatTruoc(g: THREE.BufferGeometry): THREE.Mesh {
  const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({
    colorWrite: false, depthWrite: false, depthTest: true,
    side: THREE.FrontSide,
    transparent: true, opacity: 0,
    polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
  }));
  m.renderOrder = THU_TU_TO_THIET_DIEN + 0.5;
  m.userData.chieuSauMatTruoc = true;
  m.userData.voHan = true;
  m.raycast = () => {};
  return m;
}

/** Vỏ khối SGK (`addPolyhedronShell` của HTML tham chiếu): hai lượt KHÔNG đèn — mặt SAU ở `shellBackRatio`×độ đục rồi
 *  mặt TRƯỚC ở độ đục đầy — để màu vỏ không đổi theo hướng đèn. Không ghi chiều sâu: che khuất vẫn do `lopChieuSau`.
 *  Trả mặt trước trước (vật đầu tiên là mặt "chính" mà các chỗ đọc vật liệu tìm), mặt sau thứ hai. */
function voKhoiHaiLuot(g: THREE.BufferGeometry, color: number, opacity: number): [THREE.Mesh, THREE.Mesh] {
  const tao = (side: THREE.Side, doDuc: number, thuTu: number) => {
    const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({
      color, transparent: true, opacity: doDuc, side, forceSinglePass: true, depthWrite: false,
    }));
    m.renderOrder = thuTu;
    return m;
  };
  const sau = tao(THREE.BackSide, opacity * DO_DUC.shellBackRatio, -1);
  sau.userData.voKhoiMatSau = true;
  return [tao(THREE.FrontSide, opacity, 0), sau];
}

/**
 * Một đường → HAI đường: phần thấy nét liền, phần khuất nét đứt.
 *
 * `polygonOffset` đẩy nhẹ đường về phía camera để đường **nằm trên** mặt khối
 * (vành đáy, biên thiết diện) không nhấp nháy vì sai số chiều sâu.
 */
function duongHaiLuot(
  g: THREE.BufferGeometry, mau: number, chuKy: number, ten: string,
  duongThang = false,
): THREE.Group {
  const nhom = new THREE.Group();
  const chung = {
    color: mau, polygonOffset: true,
    polygonOffsetFactor: -2, polygonOffsetUnits: -2,
  } as const;
  const Lop = duongThang ? THREE.Line : THREE.LineSegments;

  const thay = new Lop(g, new THREE.LineBasicMaterial({
    ...chung, depthFunc: THREE.LessEqualDepth, depthWrite: false,
  }));
  thay.renderOrder = THU_TU_DUONG;
  thay.name = `${ten}:thay`;
  nhom.add(thay);

  const khuat = new Lop(g, new THREE.LineDashedMaterial({
    ...chung, depthFunc: THREE.GreaterDepth, depthWrite: false,
    dashSize: chuKy, gapSize: chuKy, transparent: true, opacity: DO_DUC.hiddenEdge,
  }));
  (khuat as THREE.Line).computeLineDistances();
  khuat.renderOrder = THU_TU_DUONG;
  khuat.name = `${ten}:khuat`;
  nhom.add(khuat);
  return nhom;
}

/** Highlight chỉ đổi màu/độ dày; lớp vật liệu vẫn do hidden quyết.
 *
 *  ⚠️ CẢ HAI lớp tắt `depthTest` — phân loại CPU (thứ oracle đo) là thẩm quyền.
 *  Đoạn KHUẤT nằm sau lớp chiều sâu của chính khối: GPU kiểm lại là loại nó
 *  lần hai (w09: AB, AD phân loại đúng mà không có điểm ảnh nào). Đoạn THẤY
 *  giữa hai mặt trước thì mất một phần mẫu MSAA và nhạt đi (w10: cạnh SC). */
export function canonicalEdgeMaterial(
  hidden: boolean,
  highlighted: boolean,
  color: number = MAU.canh,
  dashSize = PHONG_CACH_SCENE3D.dash.fallback,
  highlightColor: number = MAU.highlight,
): THREE.LineBasicMaterial | THREE.LineDashedMaterial {
  const common = {
    color: highlighted ? highlightColor : hidden && color === MAU.canh ? MAU.hiddenEdge : color,
    linewidth: highlighted ? NET.selected : NET.edge,
    polygonOffset: true,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -2,
    // Hàng đợi trong suốt (opacity 1): `renderOrder` xếp nét SAU mặt tô, nếu
    // không mặt tô trong suốt vẽ đè lên nét và cạnh giữa hai mặt nhạt đi.
    transparent: true,
  } as const;
  return hidden
    ? new THREE.LineDashedMaterial({
        ...common, dashSize, gapSize: dashSize * PHONG_CACH_SCENE3D.dash.gapRatio, transparent: true, opacity: DO_DUC.hiddenEdge,
        depthTest: false, depthWrite: false,
      })
    : new THREE.LineBasicMaterial({ ...common, depthTest: false });
}

/** Khúc tô sáng trên một cạnh chuẩn (`edge_span` của đoạn con nằm trên cạnh) — tham số đo từ `edge.a`. */
export interface KhucToSang { t0: number; t1: number; mau: number }

/**
 * regular-square-pyramid-w04 — cắt các đoạn khuất/hiện của MỘT cạnh tại biên khúc tô sáng: phần trong khúc `sang`,
 * phần ngoài giữ như cũ. Không khúc ⇒ không phần nào `sang` (độ sáng cả cạnh do owner quyết như trước).
 */
export function chiaKhucToSang<S extends { t0: number; t1: number }>(
  spans: S[], khuc: { t0: number; t1: number } | undefined,
): (S & { sang: boolean })[] {
  if (!khuc) return spans.map((s) => ({ ...s, sang: false }));
  return spans.flatMap((s) => [
    { ...s, t1: Math.min(s.t1, khuc.t0), sang: false },
    { ...s, t0: Math.max(s.t0, khuc.t0), t1: Math.min(s.t1, khuc.t1), sang: true },
    { ...s, t0: Math.max(s.t0, khuc.t1), sang: false },
  ]).filter((s) => s.t1 > s.t0);
}

/**
 * Cạnh chuẩn được tô QUA vật khác: đoạn/đáy trùng cả cạnh ⇒ `ca` (cả cạnh); đoạn con trên cạnh (`edge_span`, W4) ⇒
 * `khuc` (chỉ khúc của nó). `vat` đã xếp theo độ mạnh — vật sau ghi đè vật trước.
 */
export function toSangCanhChuan(
  vat: SceneObject[], laNoiBat: (id: string) => boolean, mau: (id: string) => number,
): { ca: Map<string, number>; khuc: Map<string, KhucToSang> } {
  const ca = new Map<string, number>();
  const khuc = new Map<string, KhucToSang>();
  const canhKhoi = vat.filter((x) => x.type === "solid").flatMap((s) => canonicalEdgesOf(s));
  for (const o of vat.filter((x) => laNoiBat(x.id))) {
    if (o.edge_span) khuc.set(o.edge_span.edge_id, { t0: o.edge_span.t0, t1: o.edge_span.t1, mau: mau(o.id) });
    else if (o.boundary_edge_ids?.length) {
      for (const id of o.boundary_edge_ids) ca.set(id, mau(o.id));
    } else if (o.type === "line3" && o.point && o.direction && canhKhoi.length > 0) {
      const [px, py, pz] = toVec3(o.point);
      const [dx, dy, dz] = toVec3(o.direction);
      const dn = Math.hypot(dx, dy, dz);
      if (dn > 1e-9) {
        const ux = dx / dn, uy = dy / dn, uz = dz / dn;
        const lechDuong = (v: THREE.Vector3) => {
          const vx = v.x - px, vy = v.y - py, vz = v.z - pz;
          const t = vx * ux + vy * uy + vz * uz;
          return Math.hypot(vx - t * ux, vy - t * uy, vz - t * uz);
        };
        for (const ce of canhKhoi) {
          if (lechDuong(ce.a) <= 1e-4 && lechDuong(ce.b) <= 1e-4) {
            ca.set(ce.id, mau(o.id));
          }
        }
      }
    }
  }
  return { ca, khuc };
}

function createSpanPoolGeometry(): THREE.BufferGeometry {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(new Float32Array(6), 3));
  geo.setAttribute("lineDistance", new THREE.Float32BufferAttribute(new Float32Array(2), 1));
  return geo;
}

function preallocateSpanGeoPool(owner: THREE.Object3D, count: number): THREE.BufferGeometry[] {
  const pool = (owner.userData.spanGeoPool as THREE.BufferGeometry[] | undefined) ?? [];
  while (pool.length < count) {
    pool.push(createSpanPoolGeometry());
  }
  owner.userData.spanGeoPool = pool;
  return pool;
}

function acquireSpanGeometry(
  owner: THREE.Object3D,
  slot: number,
  a: THREE.Vector3,
  b: THREE.Vector3,
): THREE.BufferGeometry {
  const pool = preallocateSpanGeoPool(owner, slot + 1);
  const geo = pool[slot];
  const pos = geo.getAttribute("position") as THREE.BufferAttribute;
  const pa = pos.array as Float32Array;
  pa[0] = a.x; pa[1] = a.y; pa[2] = a.z;
  pa[3] = b.x; pa[4] = b.y; pa[5] = b.z;
  pos.needsUpdate = true;
  const dist = geo.getAttribute("lineDistance") as THREE.BufferAttribute;
  const da = dist.array as Float32Array;
  da[0] = 0;
  da[1] = Math.hypot(b.x - a.x, b.y - a.y, b.z - a.z);
  dist.needsUpdate = true;
  geo.boundingSphere = null;
  geo.boundingBox = null;
  return geo;
}

function warmSpanPools(
  goc: THREE.Object3D,
  scene3: THREE.Scene,
  cam: THREE.Camera,
  renderer: THREE.WebGLRenderer,
): void {
  if (goc.userData.spanPoolsWarmed === true) return;
  goc.userData.spanPoolsWarmed = true;
  if (!scene3.userData.warmHoldGroup) {
    const hold = new THREE.Group();
    const holdGeo = createSpanPoolGeometry();
    const solidHold = new THREE.Line(
      holdGeo,
      new THREE.LineBasicMaterial({ colorWrite: false, depthWrite: false, depthTest: false, transparent: true, opacity: 0 }),
    );
    const dashedHold = new THREE.Line(
      holdGeo,
      new THREE.LineDashedMaterial({
        colorWrite: false, depthWrite: false, depthTest: false, transparent: true, opacity: 0, dashSize: 0.1, gapSize: 0.1,
      }),
    );
    solidHold.frustumCulled = false;
    dashedHold.frustumCulled = false;
    solidHold.raycast = () => {};
    dashedHold.raycast = () => {};
    hold.add(solidHold, dashedHold, ...taoGiuAmNetDay());
    scene3.add(hold);
    scene3.userData.warmHoldGroup = hold;
  }
  const warmGroup = new THREE.Group();
  const warmMat = new THREE.LineDashedMaterial({
    colorWrite: false, depthWrite: false, depthTest: false, transparent: true, opacity: 0, dashSize: 0.1, gapSize: 0.1,
  });
  goc.traverse((node) => {
    const pool = node.userData?.spanGeoPool as THREE.BufferGeometry[] | undefined;
    if (!pool) return;
    for (const geo of pool) {
      const l = new THREE.Line(geo, warmMat);
      l.frustumCulled = false;
      l.raycast = () => {};
      warmGroup.add(l);
    }
  });
  if (warmGroup.children.length > 0) {
    scene3.add(warmGroup);
    renderer.render(scene3, cam);
    scene3.remove(warmGroup);
  }
  warmMat.dispose();
}

function rebuildCanonicalEdgeOwner(
  owner: THREE.Group,
  edge: ReturnType<typeof canonicalEdgesOf>[number],
  spans: EdgeVisibilityAudit["edge_spans"],
): void {
  for (const child of [...owner.children]) {
    owner.remove(child);
    if (!child.userData?.fromSpanPool) (child as THREE.Line).geometry?.dispose();
    const material = (child as THREE.Line).material as THREE.Material | undefined;
    if (!material?.userData.spanPooled) material?.dispose();
  }
  const khuc = owner.userData.khuc as KhucToSang | undefined;
  const ownSpans = chiaKhucToSang(spans.filter((span) => span.edge_id === edge.id), khuc);
  ownSpans.forEach((span, idx) => {
    const a = edge.a.clone().lerp(edge.b, span.t0);
    const b = edge.a.clone().lerp(edge.b, span.t1);
    const geometry = acquireSpanGeometry(owner, idx, a, b);
    const isHidden = span.visibility === "HIDDEN";
    const highlighted = owner.userData.highlighted === true || span.sang;
    const highlightColor = span.sang ? khuc!.mau : owner.userData.highlightColor as number | undefined;
    const fade = span.sang ? 1 : (owner.userData.lamDiu as number | undefined) ?? 1;
    const material = spanMaterial(owner,
      [isHidden, highlighted, owner.userData.edgeColor, owner.userData.dashSize, highlightColor, fade].join("|"), () => {
        const m = canonicalEdgeMaterial(isHidden, highlighted, owner.userData.edgeColor as number,
          owner.userData.dashSize as number, highlightColor);
        if (fade !== 1) lamDiuVatLieu(m, fade);
        return m;
      });
    // Làm dịu (ngoài chuỗi nhân quả) phải sống qua lần dựng lại khi xoay — trừ KHÚC đang tô sáng (W4: chọn SM thì
    // khối ngoài chuỗi bị làm dịu, nhưng khúc S–M của nó là chính vật đang chọn).
    const line = new THREE.Line(geometry, material);
    line.userData.fromSpanPool = true;
    line.userData.hidden = isHidden;
    line.userData.sang = span.sang;
    line.userData.logicalEdgeId = edge.id;
    line.renderOrder = THU_TU_DUONG;
    owner.add(line);
  });
}

interface NonCanonicalSegmentMeta {
  prefix: string;
  objectId: string;
  a: THREE.Vector3;
  b: THREE.Vector3;
  color: number;
  dashSize: number;
  highlighted: boolean;
  yieldColinear: boolean;
  renderOrder: number;
  noRaycast?: boolean;
}

interface NonCanonicalLoopMeta {
  objectId: string;
  pts: THREE.Vector3[];
  closed: boolean;
  color: number;
  dashSize: number;
  highlighted: boolean;
  renderOrder: number;
  yieldColinear?: boolean;
  isPlaneBorder?: boolean;
}

interface CurvedRimLoopMeta {
  objectId: string;
  trong: THREE.Vector3[];
  ngoai: THREE.Vector3[];
  midpoints: THREE.Vector3[];
  sample: (turn: number) => { inner: THREE.Vector3; outer: THREE.Vector3 };
  spanCapacity?: number;
  thayMesh: THREE.Mesh;
  khuatMesh: THREE.Mesh;
  thayNet: THREE.LineSegments;
  khuatNet: THREE.LineSegments;
}

/**
 * Khối cong vẫn hiện (đường bao theo camera) nhưng KHÔNG che vật khác — khối phụ cùng khung với khối chính. Trước đây
 * siêu dữ liệu bị xoá hẳn, nên đường bao cầu không bao giờ được đặt và một vòng đơn vị hiện ở gốc toạ độ.
 */
export function datKhoiCongKhongChe(obj: THREE.Object3D): void {
  if (!obj.userData.curvedSolidVolume) return;
  obj.userData.curvedSilhouetteVolume = obj.userData.curvedSolidVolume;
  delete obj.userData.curvedSolidVolume;
}

/**
 * Một biên logic một chủ hình (OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT): khi cảnh đã có đường tròn backend trùng tâm,
 * bán kính và trục với một vành đáy mà khối cong tự vẽ (`objects`: do nơi gọi lọc — vật người dùng thấy, cùng phép dời), bỏ vành của khối — đường tròn backend hiện theo bước của chính
 * nó (#31) và một thiết diện đang chọn không bị vành xanh đậm của khối đè lên. So sánh số của dữ kiện backend, không suy.
 */
export function boVanhDayTrung(obj: THREE.Object3D, khoi: SceneObject, objects: readonly SceneObject[]): void {
  const tron = objects.filter((x) => x.id !== khoi.id && x.type === "circle3" && x.center && x.normal && x.radius_sq);
  if (!tron.length) return;
  const gan = (a: number, b: number) => Math.abs(a - b) <= 1e-9 * Math.max(1, Math.abs(a), Math.abs(b));
  const vanh: THREE.Object3D[] = [];
  obj.traverse((n) => { if (n.userData.vanhDayCua) vanh.push(n); });
  for (const n of vanh) {
    type Ba = [number, number, number];
    const { center: c, axis, radius_sq } = n.userData.vanhDayCua as { center: Ba; axis: Ba; radius_sq: string };
    const d = new THREE.Vector3(...axis).normalize().toArray();
    const cungTruc = (e: number[]) => e.every((v, i) => gan(v, d[i])) || e.every((v, i) => gan(v, -d[i]));
    const trung = tron.some((x) => gan(toNumber(x.radius_sq!), toNumber(radius_sq))
      && toVec3(x.center!).every((v, i) => gan(v, c[i]))
      && cungTruc(new THREE.Vector3(...toVec3(x.normal!)).normalize().toArray()));
    if (trung) { n.removeFromParent(); disposeScene3DObject(n); }
  }
}

/**
 * Nét 1px dọc mép ngoài vành, dùng CHUNG vật liệu với dải. Dải nằm trong mặt phẳng miền nên khi nhìn xiên nó co dưới
 * một điểm ảnh và cung khuất biến mất (đo: elip p6, góc «quarter», 390px); nét như viền đa giác thì không co.
 */
function themNetVanh(nhom: THREE.Group, thay: THREE.Mesh, khuat: THREE.Mesh): Pick<CurvedRimLoopMeta, "thayNet" | "khuatNet"> {
  const net = (dai: THREE.Mesh) => {
    const l = new THREE.LineSegments(new THREE.BufferGeometry(), dai.material as THREE.Material);
    l.renderOrder = dai.renderOrder;
    l.raycast = () => {};
    nhom.add(l);
    return l;
  };
  return { thayNet: net(thay), khuatNet: net(khuat) };
}

function capNhatHinhHocVanhCong(
  rim: CurvedRimLoopMeta,
  spans: readonly { t0: number; t1: number; hidden: boolean }[],
  useCpuDepthOverride: boolean,
): void {
  const segCount = rim.midpoints.length;
  const dinhThay: number[] = [];
  const dinhDut: number[] = [];
  const netThay: number[] = [];
  const netDut: number[] = [];
  const dashCycle = 4; // 24 uniform dashes around 96-segment loop (2 segments dash, 2 segments gap)
  const pieces = spans.length ? spans : Array.from({ length: segCount }, (_, i) => ({ t0: i, t1: i + 1, hidden: false }));
  for (const span of pieces) {
    const i = Math.floor((span.t0 + span.t1) / 2);
    const start = rim.sample(span.t0 / segCount), end = rim.sample(span.t1 / segCount);
    const [a0, b0, a1, b1] = [start.inner, start.outer, end.inner, end.outer];
    const quad = [
      a0.x, a0.y, a0.z, b0.x, b0.y, b0.z, a1.x, a1.y, a1.z,
      b0.x, b0.y, b0.z, b1.x, b1.y, b1.z, a1.x, a1.y, a1.z,
    ];
    const canh = [b0.x, b0.y, b0.z, b1.x, b1.y, b1.z];
    if (!useCpuDepthOverride) {
      dinhThay.push(...quad);
      netThay.push(...canh);
      if (i % dashCycle < 2) { dinhDut.push(...quad); netDut.push(...canh); }
    } else if (!span.hidden) {
      dinhThay.push(...quad);
      netThay.push(...canh);
    } else if (i % dashCycle < 2) {
      dinhDut.push(...quad);
      netDut.push(...canh);
    }
  }
  // Buffer cỡ TỐI ĐA (mọi đoạn) cấp một lần cho mỗi mesh, rồi ghi tại chỗ + `setDrawRange` — dựng
  // `BufferGeometry` mới mỗi lần đổi góc nhìn là một buffer GPU mới mỗi khung khi xoay (cổng
  // `scene3d-orbit-gate`, `capPhat = 0`, ca p6/p7 thiết diện elip).
  const setPos = (mesh: THREE.Mesh | THREE.LineSegments, arr: number[]) => {
    // Eight probe intervals/chord plus analytic tangent seeds; reserve independently of camera orientation.
    const cap = (rim.spanCapacity ?? segCount * 16) * (mesh instanceof THREE.LineSegments ? 6 : 18);
    let attr = mesh.geometry?.getAttribute?.("position") as THREE.BufferAttribute | undefined;
    if (!attr || attr.array.length !== cap) {
      const g = new THREE.BufferGeometry();
      attr = new THREE.BufferAttribute(new Float32Array(cap), 3);
      attr.setUsage(THREE.DynamicDrawUsage);
      g.setAttribute("position", attr);
      mesh.geometry?.dispose?.();
      mesh.geometry = g;
    }
    (attr.array as Float32Array).set(arr);
    attr.needsUpdate = true;
    mesh.geometry.setDrawRange(0, arr.length / 3);
    mesh.geometry.computeBoundingSphere();
    const mat = mesh.material as THREE.MeshBasicMaterial;
    mat.depthTest = !useCpuDepthOverride;
  };
  setPos(rim.thayMesh, dinhThay);
  setPos(rim.khuatMesh, dinhDut);
  setPos(rim.thayNet, netThay);
  setPos(rim.khuatNet, netDut);
}

function updateNonCanonicalVisibility(
  targetRoot: THREE.Object3D,
  camera: THREE.Camera,
  occluders: readonly WorldSolidOccluder[],
  worldSignature: string,
  curvedVolumes: readonly CurvedSolidVolumeMeta[],
): void {
  const worldCam = camera.position.clone();
  const prioritySegments: { id: string; a: THREE.Vector3; b: THREE.Vector3 }[] = [];
  targetRoot.traverse((node) => {
    const seg = node.userData?.nonCanonicalSegment as NonCanonicalSegmentMeta | undefined;
    if (seg && (node as THREE.Group).isGroup) {
      node.updateWorldMatrix(true, false);
      prioritySegments.push({
        id: seg.objectId,
        a: seg.a.clone().applyMatrix4(node.matrixWorld),
        b: seg.b.clone().applyMatrix4(node.matrixWorld),
      });
      return;
    }
    const loop = node.userData?.nonCanonicalLoop as NonCanonicalLoopMeta | undefined;
    if (loop && !loop.yieldColinear) {
      node.updateWorldMatrix(true, false);
      const edgeCount = loop.closed ? loop.pts.length : Math.max(0, loop.pts.length - 1);
      for (let i = 0; i < edgeCount; i += 1) {
        prioritySegments.push({
          id: `${loop.objectId}::border:${i}`,
          a: loop.pts[i].clone().applyMatrix4(node.matrixWorld),
          b: loop.pts[(i + 1) % loop.pts.length].clone().applyMatrix4(node.matrixWorld),
        });
      }
    }
  });
  targetRoot.traverse((node) => {
    const seg = node.userData?.nonCanonicalSegment as NonCanonicalSegmentMeta | undefined;
    if (seg && (node as THREE.Group).isGroup) {
      if (node.userData.nonCanonicalSig === worldSignature) return;
      if (occluders.length === 0 && curvedVolumes.length === 0) return;
      node.updateWorldMatrix(true, false);
      const worldA = seg.a.clone().applyMatrix4(node.matrixWorld);
      const worldB = seg.b.clone().applyMatrix4(node.matrixWorld);
      const res = classifyWorldSegmentVisibility(worldA, worldB, worldCam, occluders, {
        edge_id: seg.objectId,
        curved_occluders: curvedVolumes,
        yield_colinear_canonical_edges: seg.yieldColinear,
      });
      const spanSig = `${res.spans.map((s) => `${s.visibility}:${s.t0}:${s.t1}`).join("|")}|${res.colinear_canonical_edge_ids.join(",")}`;
      // Cạnh chuẩn mà đoạn này nhường nét (trùng cạnh khối): độ thấy của đoạn khi ấy nằm ở các khúc của cạnh chuẩn.
      node.userData.colinearCanonicalIds = res.colinear_canonical_edge_ids;
      if (node.userData.nonCanonicalSpanSig === spanSig) {
        node.userData.nonCanonicalSig = worldSignature;
        return;
      }
      for (const child of [...node.children]) {
        if (child.userData?.nonCanonicalSpanLine
            || child.name.endsWith(":thay")
            || child.name.endsWith(":khuat")) {
          node.remove(child);
          if (!child.userData?.fromSpanPool) (child as THREE.Line).geometry?.dispose();
          const material = (child as THREE.Line).material as THREE.Material | undefined;
          if (!material?.userData.spanPooled) material?.dispose();
        }
      }
      res.spans.forEach((span, idx) => {
        const p0 = seg.a.clone().lerp(seg.b, span.t0);
        const p1 = seg.a.clone().lerp(seg.b, span.t1);
        const isHidden = span.visibility === "HIDDEN";
        const mat = spanMaterial(node, [isHidden, seg.highlighted, seg.color, seg.dashSize, node.userData.lamDiu].join("|"), () => {
          const m = canonicalEdgeMaterial(isHidden, seg.highlighted, seg.color, seg.dashSize, seg.color);
          if (node.userData.lamDiu) lamDiuVatLieu(m, node.userData.lamDiu as number);
          return m;
        });
        const line = new THREE.Line(acquireSpanGeometry(node, idx, p0, p1), mat);
        line.name = idx === 0 && !isHidden ? `${seg.prefix}:thay` : `${seg.prefix}:span:${idx}`;
        line.userData.fromSpanPool = true;
        line.userData.nonCanonicalSpanLine = true;
        line.userData.hidden = isHidden;
        line.renderOrder = seg.renderOrder;
        if (seg.noRaycast) line.raycast = () => {};
        node.add(line);
      });
      if (seg.yieldColinear && res.colinear_canonical_edge_ids.length > 0 && !seg.noRaycast) {
        const proxy = new THREE.Line(
          acquireSpanGeometry(node, res.spans.length, seg.a, seg.b),
          spanMaterial(node, "proxy", () => new THREE.LineBasicMaterial({
            colorWrite: false, depthWrite: false, transparent: true, opacity: 0, linewidth: NET.pick,
          })),
        );
        proxy.name = `${seg.prefix}:proxy`;
        proxy.userData.fromSpanPool = true;
        proxy.userData.nonCanonicalSpanLine = true;
        node.add(proxy);
      }
      node.userData.nonCanonicalSpanSig = spanSig;
      node.userData.nonCanonicalSig = worldSignature;
      return;
    }

    const loop = node.userData?.nonCanonicalLoop as NonCanonicalLoopMeta | undefined;
    if (loop) {
      if (node.userData.nonCanonicalSig === worldSignature) return;
      if (occluders.length === 0 && curvedVolumes.length === 0 && !(loop.yieldColinear && prioritySegments.length > 0)) return;
      node.updateWorldMatrix(true, false);
      const edgeCount = loop.closed ? loop.pts.length : Math.max(0, loop.pts.length - 1);
      const edgeResults = [];
      for (let i = 0; i < edgeCount; i += 1) {
        const localA = loop.pts[i];
        const localB = loop.pts[(i + 1) % loop.pts.length];
        const worldA = localA.clone().applyMatrix4(node.matrixWorld);
        const worldB = localB.clone().applyMatrix4(node.matrixWorld);
        const res = classifyWorldSegmentVisibility(worldA, worldB, worldCam, occluders, {
          edge_id: `${loop.objectId}::border:${i}`,
          curved_occluders: curvedVolumes,
          yield_colinear_canonical_edges: Boolean(loop.yieldColinear),
          priority_segments: loop.yieldColinear ? prioritySegments : undefined,
        });
        edgeResults.push({ i, localA, localB, res });
      }
      const spanSig = edgeResults
        .map(({ i, res }) => `${i}:${res.spans.map((s) => `${s.visibility}:${s.t0}:${s.t1}`).join(",")}`)
        .join("|");
      if (node.userData.nonCanonicalSpanSig === spanSig) {
        node.userData.nonCanonicalSig = worldSignature;
        return;
      }
      for (const child of [...node.children]) {
        if (child.userData?.nonCanonicalBorderLine) {
          node.remove(child);
          if (!child.userData?.fromSpanPool) (child as THREE.Line).geometry?.dispose();
          const material = (child as THREE.Line).material as THREE.Material | undefined;
          if (!material?.userData.spanPooled) material?.dispose();
        }
      }
      let slotIdx = 0;
      for (const { i, localA, localB, res } of edgeResults) {
        res.spans.forEach((span, idx) => {
          const p0 = localA.clone().lerp(localB, span.t0);
          const p1 = localA.clone().lerp(localB, span.t1);
          // Viền mặt phẳng cũng theo phân loại thấy/khuất (liền nơi thấy, đứt nơi khối che), nét tím mảnh của mặt phẳng.
          const isHidden = span.visibility === "HIDDEN";
          const mat = spanMaterial(node,
            [isHidden, loop.highlighted, loop.color, loop.dashSize, loop.isPlaneBorder, node.userData.lamDiu].join("|"), () => {
              const m = canonicalEdgeMaterial(isHidden, loop.highlighted, loop.color, loop.dashSize, loop.color);
              if (loop.isPlaneBorder) {
                m.linewidth = NET.plane;
                const doDuc = loop.highlighted ? DO_DUC.selectedPlaneEdge : DO_DUC.standalonePlaneEdge;
                m.opacity = isHidden ? doDuc * DO_DUC.hiddenEdge : doDuc;
              } else if (!isHidden) {
                m.linewidth = loop.highlighted ? NET.selected : NET.border;
              }
              if (node.userData.lamDiu) lamDiuVatLieu(m, node.userData.lamDiu as number);
              return m;
            });
          const line = new THREE.Line(acquireSpanGeometry(node, slotIdx++, p0, p1), mat);
          line.name = loop.isPlaneBorder ? `plane_border:${loop.objectId}:${i}:${idx}` : `section_border:${loop.objectId}:${i}:${idx}`;
          line.userData.fromSpanPool = true;
          line.userData.nonCanonicalBorderLine = true;
          line.userData.hidden = isHidden;
          line.renderOrder = loop.renderOrder;
          node.add(line);
        });
      }
      node.userData.nonCanonicalSpanSig = spanSig;
      node.userData.nonCanonicalSig = worldSignature;
    }
  });
}

export function updateCanonicalEdgeVisibility(
  root: THREE.Object3D,
  camera: THREE.Camera,
  renderSignature = "",
): EdgeVisibilityAudit & {
  highlighted_render_owner_ids: string[];
  recomputed_solid_count: number;
  recomputation_ms: number;
  edge_count: number;
  span_count: number;
} {
  const started = globalThis.performance?.now?.() ?? Date.now();
  const status = new Map<string, Set<"visible" | "hidden">>();
  const counts = new Map<string, number>();
  const highlighted = new Set<string>();
  const allSpans: EdgeVisibilityAudit["edge_spans"] = [];
  const occluders: WorldSolidOccluder[] = [];
  let triangleCount = 0;
  let sampleCount = 0;
  let recomputedSolidCount = 0;
  const khoa = (v: number) => (Math.abs(v) < 1e-12 ? 0 : Number(v.toPrecision(10)));
  const solidCandidates: { candidate: THREE.Object3D; source: SceneObject }[] = [];
  const curvedVolumes: CurvedSolidVolumeMeta[] = [];
  root.traverse((candidate) => {
    const source = candidate.userData?.solidSceneObject as SceneObject | undefined;
    if (source) {
      candidate.updateWorldMatrix(true, false);
      solidCandidates.push({ candidate, source });
      occluders.push({ solid: source, matrixWorld: candidate.matrixWorld.clone() });
      return;
    }
    const curvedMeta = candidate.userData?.curvedSolidVolume as CurvedSolidVolumeMeta | undefined;
    if (!curvedMeta && !candidate.userData?.curvedSilhouetteVolume) return;
    candidate.updateWorldMatrix(true, false);
    if (curvedMeta) curvedVolumes.push({ ...curvedMeta, worldToLocal: candidate.matrixWorld.clone().invert() });
    updateCurvedSolidSilhouette(candidate, camera);
  });
  for (const { candidate, source } of solidCandidates) {
    const localCamera = candidate.worldToLocal(camera.position.clone());
    const signature = [
      ...[
        localCamera.x, localCamera.y, localCamera.z,
        ...camera.matrixWorldInverse.elements,
        ...camera.projectionMatrix.elements,
      ].map(khoa),
      renderSignature,
    ].join("|");
    let audit = candidate.userData.edgeVisibilityAudit as EdgeVisibilityAudit | undefined;
    if (!audit || candidate.userData.edgeVisibilitySignature !== signature) {
      const viewport = /^(\d+)x(\d+)@(\d+(?:\.\d+)?)$/.exec(renderSignature);
      const distinctSolids = solidCandidates.filter(
        (item, idx, arr) => arr.findIndex((x) => x.source.id === item.source.id) === idx,
      );
      const invMat = candidate.matrixWorld.clone().invert();
      const toFrac = (n: number) => {
        const scaled = Math.round(n * 1000000);
        return scaled % 1000000 === 0 ? String(scaled / 1000000) : `${scaled}/1000000`;
      };
      const localOccluders: SceneObject[] = distinctSolids.length > 1
        ? distinctSolids.map(({ candidate: otherNode, source: otherSolid }) => {
            if (otherSolid.id === source.id) return source;
            const relMat = invMat.clone().multiply(otherNode.matrixWorld);
            const isIdentity = relMat.elements.every((val, i) => Math.abs(val - (i % 5 === 0 ? 1 : 0)) < 1e-7);
            if (isIdentity) return otherSolid;
            return {
              ...otherSolid,
              vertices: (otherSolid.vertices ?? []).map((pt) => {
                const v = new THREE.Vector3(...toVec3(pt)).applyMatrix4(relMat);
                return [toFrac(v.x), toFrac(v.y), toFrac(v.z)];
              }),
            };
          })
        : [source];
      audit = classifySolidEdgeVisibility(source, localCamera, {
        // Polyhedron edges follow the solids' faces only (base and Owner reference convention): a curved solid that
        // encloses an inscribed polyhedron must not dash all of its edges. Curved solids still dash free segments.
        occluders: localOccluders,
        projected_edge_pixels: viewport
          ? (edge) => {
              const a = candidate.localToWorld(edge.a.clone()).project(camera);
              const b = candidate.localToWorld(edge.b.clone()).project(camera);
              const width = Number(viewport[1]) * Number(viewport[3]);
              const height = Number(viewport[2]) * Number(viewport[3]);
              return Math.hypot((a.x - b.x) * width / 2, (a.y - b.y) * height / 2);
            }
          : undefined,
      });
      candidate.userData.edgeVisibilityAudit = audit;
      candidate.userData.edgeVisibilitySignature = signature;
      recomputedSolidCount += 1;
    }
    triangleCount += audit.triangle_count;
    sampleCount += audit.sample_count;
    allSpans.push(...audit.edge_spans);
    const visible = new Set(audit.visible_edge_ids);
    const hidden = new Set(audit.hidden_edge_ids);
    const mixed = new Set(audit.mixed_edge_ids);
    candidate.traverse((child) => {
      const id = child.userData?.visualOwnerId as string | undefined;
      const edge = child.userData?.canonicalEdge as ReturnType<typeof canonicalEdgesOf>[number] | undefined;
      if (!id || !edge || !(child as THREE.Group).isGroup) return;
      const signature = audit.edge_spans.filter((span) => span.edge_id === id)
        .map((span) => `${span.visibility}:${span.t0}:${span.t1}`).join("|");
      if (child.userData.spanSignature !== signature) {
        rebuildCanonicalEdgeOwner(child as THREE.Group, edge, audit.edge_spans);
        child.userData.spanSignature = signature;
      }
      const values = status.get(id) ?? new Set<"visible" | "hidden">();
      if (visible.has(id) || mixed.has(id)) values.add("visible");
      if (hidden.has(id) || mixed.has(id)) values.add("hidden");
      status.set(id, values);
      counts.set(id, (counts.get(id) ?? 0) + 1);
      if (child.userData.highlighted === true) highlighted.add(id);
    });
  }

  const occluderSignature = [...occluders.flatMap(o => o.matrixWorld?.elements ?? []),
    ...curvedVolumes.flatMap(o => o.worldToLocal?.elements ?? [])].map(khoa).join(",");
  const worldSignature = [
    ...[
      camera.position.x, camera.position.y, camera.position.z,
      ...camera.matrixWorldInverse.elements,
      ...camera.projectionMatrix.elements,
    ].map(khoa),
    renderSignature,
    occluderSignature,
  ].join("|");
  updateNonCanonicalVisibility(root, camera, occluders, worldSignature, curvedVolumes);
  if (curvedVolumes.length > 0 || occluders.length > 0) {
    const worldCam = camera.position.clone();
    let hiddenAt: ((point: THREE.Vector3) => boolean) | undefined;
    root.traverse((node) => {
      const rim = node.userData?.curvedRimLoop as CurvedRimLoopMeta | undefined;
      if (!rim) return;
      node.updateWorldMatrix(true, false);
      const rimSignature = `${worldSignature}|${node.matrixWorld.elements.map(khoa).join(",")}`;
      if (node.userData.curvedRimSig === rimSignature) return;
      hiddenAt ??= createWorldPointOcclusionTest(worldCam, occluders, curvedVolumes);
      const count = rim.midpoints.length;
      rim.spanCapacity = Math.max(count * 16, count * 9 + 4 * curvedVolumes.length);
      const sampleWorld = (turn: number) => rim.sample(turn).outer.applyMatrix4(node.matrixWorld);
      const hidden = (t: number) => hiddenAt!(sampleWorld(t / count));
      const tangencies = curvedSurfaceTangentTurns(sampleWorld, worldCam, curvedVolumes).map(t => t * count);
      const spans: { t0: number; t1: number; hidden: boolean }[] = [];
      // Probe the curve itself: chord interiors lie inside curved solids even on their visible side.
      // Angular probe spacing <= 2π/384; transition bracket refined to < 2π/(96*2^20).
      for (let i = 0; i < count; i++) {
        let start = i, state = hidden(i);
        const cuts = [i, i + 0.25, i + 0.5, i + 0.75, i + 1,
          ...tangencies.filter(t => t > i && t < i + 1)].sort((a, b) => a - b);
        // Midpoints between analytic tangencies catch a tiny visible interval even if its endpoints are tangencies.
        const probes = cuts.flatMap((t, j) => j ? [(cuts[j - 1] + t) / 2, t] : [t]);
        for (let j = 1; j < probes.length; j++) {
          const end = probes[j], next = hidden(end);
          if (next === state) continue;
          let lo = probes[j - 1], hi = end;
          for (let k = 0; k < 20; k++) {
            const mid = (lo + hi) / 2;
            if (hidden(mid) === state) lo = mid; else hi = mid;
          }
          const boundary = (lo + hi) / 2;
          spans.push({ t0: start, t1: boundary, hidden: state });
          start = boundary; state = next;
        }
        spans.push({ t0: start, t1: i + 1, hidden: state });
      }
      const flagSig = spans.map(s => `${s.t0.toFixed(8)},${s.t1.toFixed(8)},${+s.hidden}`).join("|");
      if (node.userData.curvedRimFlagSig !== flagSig) {
        capNhatHinhHocVanhCong(rim, spans, true);
        node.userData.curvedRimFlagSig = flagSig;
      }
      node.userData.curvedRimSig = rimSignature;
    });
  }

  const visible = [...status].filter(([, values]) => values.size === 1 && values.has("visible"))
    .map(([id]) => id).sort();
  const hidden = [...status].filter(([, values]) => values.size === 1 && values.has("hidden"))
    .map(([id]) => id).sort();
  root.userData.hiddenCanonicalEdgeIds = new Set(hidden);   // đọc bởi `datCoGocVuong` (chọn dấu đại diện không khuất)
  const mixed = [...status].filter(([, values]) => values.size > 1)
    .map(([id]) => id).sort();
  const duplicates = [...counts].filter(([, count]) => count > 1)
    .map(([id]) => id).sort();
  return {
    visible_edge_ids: visible,
    hidden_edge_ids: hidden,
    mixed_edge_ids: mixed,
    duplicate_visual_owner_ids: duplicates,
    edge_spans: allSpans,
    triangle_count: triangleCount,
    sample_count: sampleCount,
    highlighted_render_owner_ids: [...highlighted].sort(),
    recomputed_solid_count: recomputedSolidCount,
    recomputation_ms: (globalThis.performance?.now?.() ?? Date.now()) - started,
    edge_count: status.size,
    span_count: allSpans.length,
  };
}

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

/** Đặt camera về một khung nhìn — và HUỶ đà xoay còn lại của cú kéo trước.
 *  Damping giữ phần xoay chưa áp trong OrbitControls; chỉ đặt pose thì đà ấy
 *  đẩy camera đi tiếp, và "Xem lại toàn hình" không về trạng thái trung tính.
 *  Một lần `update()` với damping tắt tiêu hết đà (xoá delta), rồi mới đặt. */
export function datKhungNhin(
  cam: THREE.PerspectiveCamera, dieuKhien: OrbitControls, kn: KhungNhin,
): void {
  const damping = dieuKhien.enableDamping;
  dieuKhien.enableDamping = false;
  dieuKhien.update();
  cam.position.set(...kn.viTri);
  dieuKhien.target.set(...kn.nhinVao);
  dieuKhien.update();
  dieuKhien.enableDamping = damping;
  cam.updateProjectionMatrix();
}

/**
 * Điểm thế giới mà khung nhìn phải ôm — đỉnh THẬT của những gì đang dựng.
 *
 * ⚠️ BỎ VẬT VÔ HẠN KHỎI PHÉP TÍNH KHUNG NHÌN. `setFromObject(goc)` ôm trọn mọi
 * thứ đang dựng — kể cả miếng mặt phẳng và đoạn đại diện của đường thẳng, hai
 * thứ có cỡ do CHÍNH tầng trình bày chọn. Để chúng vào thì quyết định trình
 * bày tự khuếch đại: miếng to ra ⇒ hộp bao to ra ⇒ camera lùi ⇒ hình thật bé
 * lại. ĐỈNH THẬT (toạ độ thế giới, đã tính tách khối), không phải góc hộp bao:
 * khung vừa theo HÌNH CHIẾU, và góc hộp bao chiếu ra ngoài hình.
 */
export function diemKhungNhin(goc: THREE.Object3D, daCoDiemCanh = false): [number, number, number][] {
  const diem: [number, number, number][] = [];
  const p = new THREE.Vector3();
  // Cờ nằm trên NHÓM (đường vô hạn là một nhóm hai nét): hỏi cả tổ tiên, không
  // chỉ chính nút — bỏ sót thì nét con kéo khung theo đoạn do renderer tự chọn
  // (w11: "Xem lại toàn hình" ở bước cuối bài thiết diện dời hẳn tâm nhìn).
  const boQua = (vat: THREE.Object3D) => {
    for (let x: THREE.Object3D | null = vat; x && x !== goc; x = x.parent) {
      if (x.userData?.voHan || x.userData?.chieuSau) return true;
      if (daCoDiemCanh && (x.userData?.curvedRimLoop || x.userData?.curvedSolidVolume)) return true;
    }
    return false;
  };
  goc.updateMatrixWorld(true);
  goc.traverse((vat) => {
    if (boQua(vat)) return;
    if (!(vat as THREE.Mesh).isMesh && !(vat as THREE.Line).isLine) return;
    // Hình cầu bắt chuột và chấm đỉnh (co giãn theo zoom) không phải hình; toạ
    // độ điểm đã vào khung qua `diemHuuHan`.
    if (vat.name === "pick-proxy" || vat.userData?.dauDinh) return;
    const pos = (vat as THREE.Mesh).geometry?.getAttribute?.("position");
    for (let i = 0; pos && i < pos.count; i++) {
      p.fromBufferAttribute(pos, i).applyMatrix4(vat.matrixWorld);
      diem.push([p.x, p.y, p.z]);
    }
  });
  return diem;
}

/**
 * Điểm khung nhìn ôm: hình đang dựng (`diemKhungNhin`) + toàn cảnh (`diemCanh`, đã xoay hiển thị). Hộp bao đầy đủ
 * chỉ là dự phòng cho cảnh CHỈ có mặt phẳng/đường — xét nó sau khi gộp toàn cảnh (regular-triangular-pyramid-w01:
 * ở bước 0 chỉ có điểm, vùng bấm lọt vào hai góc hộp bao ⇒ hình lệch 65–100 px, tâm quỹ đạo lệch khỏi hình).
 */
export function diemVuaKhung(goc: THREE.Object3D, diemCanh: Vec3[]): Vec3[] {
  const diem: Vec3[] = [...diemKhungNhin(goc, diemCanh.length > 0), ...diemCanh];
  if (diem.length === 0) {
    const hop = new THREE.Box3().setFromObject(goc);
    if (!hop.isEmpty()) diem.push([hop.min.x, hop.min.y, hop.min.z], [hop.max.x, hop.max.y, hop.max.z]);
  }
  return diem;
}

/**
 * Cỡ chấm đỉnh và vùng bấm theo ĐIỂM ẢNH CSS — gọi mỗi khung (w11, W10-H5).
 *
 * Lưới giữ bán kính gốc; ở đây chỉ co giãn cho hình chiếu bằng đúng token
 * `DAU_DINH_PX`, bất kể camera xa gần, hình to nhỏ hay DPR (tính theo px CSS).
 */
export function datCoDauDinh(
  goc: THREE.Object3D, cam: THREE.PerspectiveCamera, rongCss: number, caoCss: number,
): void {
  const p = new THREE.Vector3();
  const s = new THREE.Vector3();
  goc.updateMatrixWorld(true);
  goc.traverse((x) => {
    const loai = x.userData?.dauDinh ?? (x.userData?.vungBam ? "bam" : null);
    if (!loai) return;
    x.getWorldPosition(p).applyMatrix4(cam.matrixWorldInverse);
    const banKinhPx = loai === "bam" ? banKinhBamPx(rongCss) : coDauDinhPx(loai === "chon", rongCss) / 2;
    const goc0 = ((x as THREE.Mesh).geometry as THREE.SphereGeometry).parameters.radius;
    x.parent?.getWorldScale(s);
    x.scale.setScalar((banKinhPx * donViMoiPx(-p.z, cam.fov, caoCss)) / (goc0 * (s.x || 1)));
  });
}

/**
 * Đoạn thẳng nào NHƯỜNG NÉT cho cạnh chuẩn của một khối đang dựng — một cạnh,
 * một nét. `dung` là các vật SẼ dựng ở bước này; `bienDoi(id)` là khoá vị trí
 * trình bày (tách khối dời khối đi thì cạnh ấy không còn trùng đoạn nữa).
 */
export function doanNhuongCanh(
  dung: SceneObject[], bienDoi: (id: string) => string,
): Set<string> {
  const chu = new Map<string, string>();
  for (const o of dung) {
    if (o.type !== "solid") continue;
    for (const e of o.edge_ownership ?? []) chu.set(e.edge_id, bienDoi(o.id));
  }
  const ra = new Set(dung.filter((o) => o.type === "segment3" && o.boundary_edge_ids?.length
    && o.boundary_edge_ids.every((id) => chu.get(id) === bienDoi(o.id))).map((o) => o.id));
  const canhMien: { a: Vec3; b: Vec3; dich: string }[] = [];
  for (const o of dung) {
    if ((o.type !== "section" && !(o.type === "polygon3" && vaiTroMien(o) === "section")) || o.closed === false) continue;
    const pts = (o.polygon ?? o.vertices ?? []).map(toVec3);
    if (pts.length < 3) continue;
    const dich = bienDoi(o.id);
    for (let i = 0; i < pts.length; i += 1) {
      canhMien.push({ a: pts[i], b: pts[(i + 1) % pts.length], dich });
    }
  }
  if (canhMien.length > 0) {
    const trenDoan = (p: Vec3, a: Vec3, b: Vec3) => {
      const abx = b[0] - a[0], aby = b[1] - a[1], abz = b[2] - a[2];
      const lenSq = abx * abx + aby * aby + abz * abz;
      if (lenSq < 1e-12) return false;
      const apx = p[0] - a[0], apy = p[1] - a[1], apz = p[2] - a[2];
      const t = (apx * abx + apy * aby + apz * abz) / lenSq;
      if (t < -1e-4 || t > 1 + 1e-4) return false;
      return Math.hypot(a[0] + abx * t - p[0], a[1] + aby * t - p[1], a[2] + abz * t - p[2]) <= 1e-4;
    };
    for (const o of dung) {
      if (ra.has(o.id)) continue;
      if (o.type === "polygon3" && vaiTroMien(o) !== "section" && o.closed !== false) {
        const pts = (o.polygon ?? o.vertices ?? []).map(toVec3);
        const dich = bienDoi(o.id);
        if (
          pts.length >= 3
          && pts.every((p, idx) => {
            const q = pts[(idx + 1) % pts.length];
            return canhMien.some((c) => c.dich === dich && trenDoan(p, c.a, c.b) && trenDoan(q, c.a, c.b));
          })
        ) {
          ra.add(o.id);
        }
        continue;
      }
      if (o.type !== "segment3" || o.perpendicular_witness || o.annotation?.witness) continue;
      const ptA = o.point_a ?? o.endpoints?.[0];
      const ptB = o.point_b ?? o.endpoints?.[1];
      if (!ptA || !ptB) continue;
      const a = toVec3(ptA), b = toVec3(ptB);
      const dich = bienDoi(o.id);
      if (canhMien.some((c) => c.dich === dich && trenDoan(a, c.a, c.b) && trenDoan(b, c.a, c.b))) {
        ra.add(o.id);
      }
    }
  }
  return ra;
}

/**
 * Thiết diện ở MỘT bước: chỉ các cạnh `geometry_progress` đã cho hiện, khép và tô theo
 * cờ CỦA BƯỚC ẤY — tua ngược về bước chưa tô là mất phần tô. `null` ⇔ chưa cạnh nào hiện.
 * Vật không phải thiết diện, hoặc không có tiến độ, giữ nguyên.
 */
export function vatThietDienTaiBuoc(o: SceneObject, progress?: GeometryProgress): SceneObject | null {
  if (o.type !== "section" || !progress || !o.polygon) return o;
  const count = progress.visible_edge_ids.length;
  if (count === 0) return null;
  return {
    ...o,
    polygon: progress.closed ? o.polygon : o.polygon.slice(0, count + 1),
    closed: progress.closed,
    fill_visible: progress.fill_visible,
  };
}

/** Móc đo `__geo3d_set_section_fill_visible`: bật/tắt ĐÚNG các vật `section_fill:<id>`. */
export function datHienToThietDien(goc: THREE.Object3D, on: boolean): string[] {
  const ten: string[] = [];
  goc.traverse((x) => {
    if (x.name.startsWith("section_fill:")) {
      x.visible = on;
      ten.push(x.name);
    }
  });
  return ten;
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
  /** `true` = tô sáng theo bước; một tầng = chuỗi nhân quả quanh vật đang chọn. */
  noiBat: boolean | TangNhanManh | "hover",
  banKinhBam = banKinhBamDiem(KHOANG_CAM_MAC_DINH),
  /**
   * Điểm CÓ BIÊN của cả cảnh — chỉ mặt phẳng dùng tới, để cắt phần đáng vẽ ra
   * khỏi một mặt phẳng vô hạn. Mặc định rỗng ⇒ rơi về cỡ cố định, nên mọi nơi
   * gọi cũ (test, ô soi) giữ nguyên hành vi.
   */
  diemNen: Vec3[] = [],
  cameraPosition = new THREE.Vector3(8, 3, 6),
  /** Cạnh chuẩn được tô qua vật khác (đoạn/đáy trùng cạnh) → màu tô. */
  highlightedEdgeIds: ReadonlySet<string> | ReadonlyMap<string, number> = new Set(),
  /** W4: khúc tô sáng của đoạn con nằm trên cạnh chuẩn (`toSangCanhChuan().khuc`). */
  khucToSang: ReadonlyMap<string, KhucToSang> = new Map(),
  xray = false,
  vaiKhoi: VaiTroKhoi = "primary",
  coThietDienDong = true,
  sphereReference = true,
): THREE.Object3D | null {
  // Ngữ cảnh cấu trúc: KHÔNG phải nhấn mạnh — nền xám nhạt, nét xám trung tính.
  // Cạnh khối vốn đã là mực trung tính nên giữ nguyên; còn MÀU KIỂU (hổ phách
  // thiết diện, tím mặt phẳng, xanh két đường, đỏ điểm dựng) phải nhường, vì chú
  // giải causal hứa "Hình liên quan" = xám (W12: viền thiết diện hổ phách đọc
  // thành "đại lượng trung gian").
  const boiCanh = noiBat === "boi_canh";
  if (boiCanh) noiBat = false;
  const mau = noiBat === true ? MAU.highlight
    : noiBat ? MAU_TANG[noiBat as Exclude<TangNhanManh, "boi_canh">] : undefined;
  const nen = (macDinh: number) => boiCanh ? MAU_NEN_BOI_CANH : macDinh;
  const net = (macDinh: number) => mau ?? (boiCanh ? MAU_VAI_TRO.boi_canh : macDinh);
  const mauKhoi = vaiKhoi === "secondary" ? MAU.secondaryMesh : MAU.mesh;
  const doDucKhoi = noiBat ? DO_DUC.selectedSolid : vaiKhoi === "secondary" ? DO_DUC.secondarySolid : DO_DUC.solid;
  const vaiMien = vaiTroMien(o);
  const laThietDien = vaiMien === "section";
  // Giữ màu ngữ nghĩa của vùng tô; chỉ viền thiết diện đang xét chuyển sang xanh.
  const netMien = (macDinh: number) => boiCanh ? MAU_VAI_TRO.boi_canh
    : laThietDien && noiBat === "hover" ? MAU.line
    : laThietDien && (noiBat === "dich" || noiBat === true) ? 0x2563eb : macDinh;
  const mauToMien = laThietDien ? MAU.polygon : vaiMien === "base" ? MAU.mesh : MAU.surface;
  const mauVienMien = laThietDien ? MAU.sectionOutline : vaiMien === "base" ? MAU.canh : MAU.planeOutline;
  const doDucMien = laThietDien ? (noiBat && noiBat !== "hover" ? DO_DUC.selectedSection : DO_DUC.section)
    : vaiMien === "base" ? (noiBat ? DO_DUC.selectedBase : DO_DUC.base)
    : (noiBat ? DO_DUC.selectedPlane : DO_DUC.plane);

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
      color: o.origin === "free" ? mau ?? MAU.free : net(MAU.derived),
    });
    const mesh = new THREE.Mesh(new THREE.SphereGeometry(BAN_KINH_NHIN, 16, 12), m);
    // Cỡ THẬT theo px màn hình đặt mỗi khung (`datCoDauDinh`, w11).
    mesh.userData.dauDinh = noiBat === "dich" ? "chon" : "thuong";
    nhom.add(mesh);
    const proxy = new THREE.Mesh(
      new THREE.SphereGeometry(banKinhBam, 8, 6),
      new THREE.MeshBasicMaterial({
        colorWrite: false, depthWrite: false, transparent: true, opacity: 0,
      }),
    );
    proxy.name = "pick-proxy";
    proxy.userData.vungBam = true;
    nhom.add(proxy);
    nhom.position.set(...toVec3(o.xyz));
    return v(nhom, `point:${o.id}`);
  }

  if (o.render === "line" && o.point && o.direction) {
    // Kéo dài vector chỉ phương ĐÃ CHO ra hai phía. Không tính hướng — hướng
    // là dữ liệu từ kernel. Phần được vẽ ôm vùng hình (`doanDuongThang`), như
    // miếng mặt phẳng; không có điểm nền thì rơi về độ dài cố định.
    const p = new THREE.Vector3(...toVec3(o.point));
    const d = new THREE.Vector3(...toVec3(o.direction)).normalize();
    const doan = doanDuongThang(toVec3(o.point), toVec3(o.direction), diemNen);
    const a = doan ? new THREE.Vector3(...doan[0]) : p.clone().addScaledVector(d, -LINE_DISPLAY_HALF_LENGTH);
    const b = doan ? new THREE.Vector3(...doan[1]) : p.clone().addScaledVector(d, LINE_DISPLAY_HALF_LENGTH);
    const g = new THREE.BufferGeometry().setFromPoints([a, b]);
    const mauDuong = net(MAU.line);
    const coNetDut = beDayNet(diemNen, 1) / SECTION_STROKE_RATIO * NET_DUT_TI_LE;
    const duong = duongHaiLuot(g, mauDuong, coNetDut, `line:${o.id}`, true);
    // Cùng lẽ với mặt phẳng: `line3` vô hạn, hai đầu mút là quyết định trình
    // bày. Ở `p1`, đường `BD` kéo dài vượt ra ngoài khối chóp; để nó tham gia
    // auto-fit thì camera phải lùi ra và khối thật bé đi vì một đoạn thẳng do
    // chính renderer bịa ra độ dài.
    duong.userData.voHan = true;
    preallocateSpanGeoPool(duong, 6);
    duong.userData.nonCanonicalSegment = {
      prefix: `line:${o.id}`,
      objectId: o.id,
      a,
      b,
      color: mauDuong,
      dashSize: coNetDut,
      highlighted: Boolean(noiBat),
      yieldColinear: true,
      renderOrder: THU_TU_DUONG,
    } satisfies NonCanonicalSegmentMeta;
    // Đường phụ: rõ ở bước dựng nó (formation tô) hay khi được chọn; mọi lúc
    // khác lùi xuống để thiết diện và kết quả làm trọng tâm (review W10-H7).
    if (!noiBat) lamDiu(duong, HE_SO_DUONG_PHU);
    return v(duong, `line:${o.id}`);
  }

  if (o.render === "segment" && ((o.point_a && o.point_b) || (o.endpoints && o.endpoints.length >= 2))) {
    // Đoạn thẳng HỮU HẠN nối đúng hai đầu mút — không vô hạn, không kéo dài.
    const ptA = o.point_a ?? o.endpoints![0];
    const ptB = o.point_b ?? o.endpoints![1];
    const a = new THREE.Vector3(...toVec3(ptA));
    const b = new THREE.Vector3(...toVec3(ptB));
    const g = new THREE.BufferGeometry().setFromPoints([a, b]);
    const mauDoan = net(MAU.line);
    const coNetDut = (beDayNet(diemNen, 1) / SECTION_STROKE_RATIO) * NET_DUT_TI_LE;
    // Nhường nét cho cạnh chuẩn của khối (`doanNhuongCanh`): chỉ còn vùng bấm.
    const duong: THREE.Object3D = o.display_role === "hit_proxy"
      ? v(new THREE.Line(g, new THREE.LineBasicMaterial({
          colorWrite: false, depthWrite: false, transparent: true, opacity: 0, linewidth: NET.pick,
        })), `segment:${o.id}:proxy`)
      : duongHaiLuot(
          g,
          mauDoan,
          coNetDut,
          `segment:${o.id}`,
          true,
        );
    duong.userData.voHan = false;
    if (o.display_role !== "hit_proxy") {
      preallocateSpanGeoPool(duong, 6);
      duong.userData.nonCanonicalSegment = {
        prefix: `segment:${o.id}`,
        objectId: o.id,
        a,
        b,
        color: mauDoan,
        dashSize: coNetDut,
        highlighted: Boolean(noiBat),
        yieldColinear: true,
        renderOrder: THU_TU_DUONG,
      } satisfies NonCanonicalSegmentMeta;
    }

    // Ký hiệu góc vuông (perpendicular marker) CHỈ khi vật mang chứng chỉ vuông góc tường minh từ backend
    // (`perpendicular_witness` hoặc `annotation.witness`) với hai phương u, v thực sự vuông góc.
    const chungChi = o.perpendicular_witness ?? o.annotation?.witness;
    if (chungChi?.foot && chungChi.marker?.u && chungChi.marker?.v
        && nhanChungDoanHopLe(chungChi, [a.x, a.y, a.z], [b.x, b.y, b.z])) {
      const [cx, cy, cz] = toVec3(chungChi.foot);
      const [ux, uy, uz] = toVec3(chungChi.marker.u);
      const [vx, vy, vz] = toVec3(chungChi.marker.v);
      const du = Math.hypot(ux, uy, uz);
      const dv = Math.hypot(vx, vy, vz);
      {
        // `s` là cỡ world TRẦN; `datCoGocVuong` co dấu quanh chân về ~16–22 px mỗi khung (HTML tham chiếu:
        // ô vuông hai đoạn nhỏ) — trần còn bị chặn bởi một phần đoạn mang chứng chỉ để dấu không vượt ra ngoài nó.
        const daiDoan = Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
        const s = Math.min(0.35, Math.max(0.12, 0.22 * daiDoan), PHONG_CACH_SCENE3D.rightAngle.maxLegRatio * daiDoan);
        const lineMarker = dauGocVuong(
          [cx, cy, cz], [ux / du, uy / du, uz / du], [vx / dv, vy / dv, vz / dv], s,
          PHONG_CACH_SCENE3D.rightAngle.maxLegRatio * daiDoan, net(MAU.line),
        );
        lineMarker.name = `perp_marker:${o.id}`;
        lineMarker.userData.perpMarker = true;
        const pw = o.perpendicular_witness;
        if (pw?.relation && pw.on) {
          (lineMarker.userData.gocVuongDonVi as GocVuongDonVi).nhomQuanHe = [pw.relation, pw.rule ?? "", pw.on].join("|");
        }
        if (pw?.from && pw.foot_id) (lineMarker.userData.gocVuongDonVi as GocVuongDonVi).dauMut = [pw.from, pw.foot_id];

        const nhom = new THREE.Group();
        nhom.add(duong);
        nhom.add(lineMarker);
        return v(nhom, `segment:${o.id}`);
      }
    }

    return v(duong, `segment:${o.id}`);
  }

  if (o.render === "surface" && o.point && o.normal) {
    // Xoay theo `normal` — `setFromUnitVectors` là phép của thư viện trên một
    // pháp tuyến ĐÃ CÓ, không phải suy ra mặt phẳng từ ba điểm.
    //
    // ⚠️ TÂM VÀ CỠ lấy từ vùng hình học liên quan (`khungMatPhang`), không còn
    // là ô vuông cố định đặt tại `point`. Khi trên mặt phẳng có ≥ 3 điểm không
    // thẳng hàng của hình (`daGiacMatPhang`), dựng cả miền đa giác gốc lẫn tấm
    // mặt phẳng mở rộng (`moRongDaGiacMatPhang`, đã cắt theo mặt đáy z ≥ z_min)
    // kèm viền mảnh rõ nét để mặt phẳng toán học không hoà lẫn vào mặt bên của khối.
    const diemMp = toVec3(o.point);
    const phapTuyen = toVec3(o.normal);
    const daGiac = daGiacMatPhang(diemMp, phapTuyen, diemNen);
    const daGiacMoRong = moRongDaGiacMatPhang(diemMp, phapTuyen, diemNen, daGiac);
    const mauMp = nen(MAU.surface);
    const mauVienMp = net(MAU.planeOutline);
    const laMatPhangDocLap = !coThietDienDong;
    const laChonTrucTiepMp = noiBat === true || noiBat === "dich";
    const doDucTamMp = laChonTrucTiepMp
      ? DO_DUC.selectedPlane
      : laMatPhangDocLap
        ? DO_DUC.standalonePlane
        : DO_DUC.plane;
    const doDucVienMp = laChonTrucTiepMp
      ? DO_DUC.selectedPlaneEdge
      : laMatPhangDocLap
        ? DO_DUC.standalonePlaneEdge
        : DO_DUC.planeEdge;
    const coNetDut = (beDayNet(diemNen, 1) / SECTION_STROKE_RATIO) * NET_DUT_TI_LE;
    // Viền miếng mặt phẳng (Owner 2026-10-26, như `addRepresentedPlane` của HTML tham chiếu): nét LIỀN tím mảnh nơi
    // thấy, nét ĐỨT chỉ nơi khối che — phân loại bằng cùng bộ che khuất với cạnh thật (lượt `nonCanonicalLoop`), không
    // đứt cả viền. Viền vẫn là màu/nét riêng của mặt phẳng (tím, mảnh, nhạt) nên không đọc nhầm thành cạnh khối.
    const ganVienMatPhang = (target: THREE.Mesh, daGiacVien: Vec3[]) => {
      const ptsVien = daGiacVien.map((p) => new THREE.Vector3(...p));
      const vongVien = [...ptsVien, ptsVien[0]];
      const vienBanDau = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(vongVien),
        new THREE.LineBasicMaterial({
          color: mauVienMp,
          linewidth: NET.plane,
          transparent: true,
          opacity: doDucVienMp,
          depthTest: false,
        }),
      );
      vienBanDau.userData.hidden = false;
      vienBanDau.name = `plane_border:${o.id}`;
      vienBanDau.userData.nonCanonicalBorderLine = true;
      vienBanDau.renderOrder = THU_TU_DUONG;
      target.add(vienBanDau);
      preallocateSpanGeoPool(target, Math.max(8, daGiacVien.length * 4));
      target.userData.nonCanonicalLoop = {
        objectId: o.id,
        pts: ptsVien,
        closed: true,
        color: mauVienMp,
        dashSize: coNetDut,
        highlighted: laChonTrucTiepMp,
        renderOrder: THU_TU_DUONG,
        yieldColinear: true,
        isPlaneBorder: true,
      } satisfies NonCanonicalLoopMeta;
    };
    if (daGiac && daGiac.length >= 3) {
      const pos: number[] = [];
      for (const [a, b, c] of chiaTamGiac(daGiac)) {
        for (const j of [a, b, c]) pos.push(...daGiac[j]);
      }
      if (pos.length > 0) {
        const coMoRong = Boolean(daGiacMoRong && daGiacMoRong.length >= 3);
        const g = new THREE.BufferGeometry();
        g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
        g.computeVertexNormals();
        const m = new THREE.MeshBasicMaterial({
          color: mauMp,
          transparent: true,
          opacity: coMoRong ? 0 : (noiBat ? DO_DUC.selectedPlaneCore : laMatPhangDocLap ? DO_DUC.standalonePlane : DO_DUC.planeCore),
          forceSinglePass: true,
          colorWrite: !coMoRong,
          side: THREE.DoubleSide,
          depthWrite: false,
          depthTest: false,
        });
        const mesh = new THREE.Mesh(g, m);
        mesh.renderOrder = 1;
        mesh.userData.voHan = true;
        if (daGiacMoRong && daGiacMoRong.length >= 3) {
          const posMoRong: number[] = [];
          for (const [a, b, c] of chiaTamGiac(daGiacMoRong)) {
            for (const j of [a, b, c]) posMoRong.push(...daGiacMoRong[j]);
          }
          if (posMoRong.length > 0) {
            const gMoRong = new THREE.BufferGeometry();
            gMoRong.setAttribute("position", new THREE.Float32BufferAttribute(posMoRong, 3));
            gMoRong.computeVertexNormals();
            const mMoRong = new THREE.MeshBasicMaterial({
              color: mauMp,
              transparent: true,
              opacity: doDucTamMp,
              forceSinglePass: true,
              side: THREE.DoubleSide,
              depthWrite: false,
              depthTest: false,
            });
            const mienMoRong = new THREE.Mesh(gMoRong, mMoRong);
            mienMoRong.name = `plane_sheet:${o.id}`;
            mienMoRong.renderOrder = 1;
            mienMoRong.userData.voHan = true;
            ganVienMatPhang(mienMoRong, daGiacMoRong);
            mesh.add(mienMoRong);
          }
        } else {
          ganVienMatPhang(mesh, daGiac);
        }
        return v(mesh, `plane:${o.id}`);
      }
    }
    if (daGiacMoRong && daGiacMoRong.length >= 3) {
      const posMoRong: number[] = [];
      for (const [a, b, c] of chiaTamGiac(daGiacMoRong)) {
        for (const j of [a, b, c]) posMoRong.push(...daGiacMoRong[j]);
      }
      if (posMoRong.length > 0) {
        const gMoRong = new THREE.BufferGeometry();
        gMoRong.setAttribute("position", new THREE.Float32BufferAttribute(posMoRong, 3));
        gMoRong.computeVertexNormals();
        const mMoRong = new THREE.MeshBasicMaterial({
          color: mauMp,
          transparent: true,
          opacity: doDucTamMp,
          forceSinglePass: true,
          side: THREE.DoubleSide,
          depthWrite: false,
          depthTest: false,
        });
        const mesh = new THREE.Mesh(gMoRong, mMoRong);
        mesh.renderOrder = 1;
        mesh.userData.voHan = true;
        ganVienMatPhang(mesh, daGiacMoRong);
        return v(mesh, `plane:${o.id}`);
      }
    }
    const khung = khungMatPhang(diemMp, phapTuyen, diemNen);
    const canh = khung ? khung.canh : PLANE_DISPLAY_SIZE;
    const g = new THREE.PlaneGeometry(canh, canh);
    const m = new THREE.MeshBasicMaterial({
      color: mauMp,
      transparent: true,
      opacity: noiBat ? DO_DUC.selectedPlane : DO_DUC.plane,
      forceSinglePass: true,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    const mesh = new THREE.Mesh(g, m);
    const n = new THREE.Vector3(...phapTuyen).normalize();
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), n);
    mesh.position.set(...(khung ? khung.tam : diemMp));
    // Mặt phẳng VÔ HẠN: miếng vẽ ra là đại diện do tầng trình bày chọn cỡ, nên
    // nó KHÔNG được tham gia tính khung nhìn — xem `vuaKhungRef`.
    mesh.userData.voHan = true;
    return v(mesh, `plane:${o.id}`);
  }

  if (o.render === "circle" && o.center && o.normal && o.radius_sq) {
    const r = Math.sqrt(Math.max(0, toNumber(o.radius_sq)));
    const duongTronDay = vaiMien === "base";
    // Đường tham chiếu (xích đạo minh hoạ của mặt cầu): đường PHỤ — nhẹ hơn đường bao và mọi vành thật.
    const thamChieu = o.display_role === "presentation_reference";
    const heSoDay = thamChieu ? 0.2 : (noiBat ? 1.25 : 1) * (duongTronDay ? 0.36 : 0.46);
    const day = beDayNet(diemNen, r) * heSoDay;
    const ngoaiR = r;
    const trongR = Math.max(0, r - day);
    const mauVanh = thamChieu ? net(MAU.hiddenEdge) : netMien(mauVienMien);
    const chungVanh = {
      color: mauVanh, side: THREE.DoubleSide,
      forceSinglePass: true,
      ...LECH_THIET_DIEN,
    } as const;
    const nhomVanh = new THREE.Group();
    if (o.fill_visible !== false) {
      const bkTo = Math.max(2e-5, trongR);
      const to = new THREE.Mesh(
        new THREE.RingGeometry(1e-5, bkTo, VONG_CHIA),
        new THREE.MeshBasicMaterial(
          duongTronDay
            ? {
                color: nen(mauToMien),
                transparent: true,
                opacity: doDucMien,
                forceSinglePass: true,
                side: THREE.DoubleSide,
                depthWrite: false,
              }
            : {
                color: nen(mauToMien),
                transparent: true,
                opacity: doDucMien,
                forceSinglePass: true,
                side: THREE.DoubleSide,
                depthWrite: false,
                depthTest: !xray,
                depthFunc: THREE.LessEqualDepth,
                ...LECH_THIET_DIEN,
              },
        ),
      );
      to.name = `${duongTronDay ? "polygon_fill" : "section_fill"}:${o.id}`;
      if (!duongTronDay) to.renderOrder = THU_TU_TO_THIET_DIEN;
      nhomVanh.add(to);
    }
    const soDoanVanh = 96;
    const trongPts: THREE.Vector3[] = [];
    const ngoaiPts: THREE.Vector3[] = [];
    const midpoints: THREE.Vector3[] = [];
    for (let i = 0; i <= soDoanVanh; i += 1) {
      const t = (i / soDoanVanh) * Math.PI * 2;
      const cs = Math.cos(t), sn = Math.sin(t);
      trongPts.push(new THREE.Vector3(trongR * cs, trongR * sn, 0));
      ngoaiPts.push(new THREE.Vector3(ngoaiR * cs, ngoaiR * sn, 0));
      if (i < soDoanVanh) {
        const tm = ((i + 0.5) / soDoanVanh) * Math.PI * 2;
        midpoints.push(new THREE.Vector3(ngoaiR * Math.cos(tm), ngoaiR * Math.sin(tm), 0));
      }
    }
    // Hàng đợi trong suốt (opacity 1) như `canonicalEdgeMaterial`: chỉ vậy `renderOrder` mới đặt vành trên nét khối.
    const thay = new THREE.Mesh(
      new THREE.BufferGeometry(),
      new THREE.MeshBasicMaterial({ ...chungVanh, depthFunc: THREE.LessEqualDepth, transparent: true }),
    );
    thay.renderOrder = THU_TU_VE_THIET_DIEN;
    const khuat = new THREE.Mesh(
      new THREE.BufferGeometry(),
      new THREE.MeshBasicMaterial({
        ...chungVanh, depthFunc: THREE.GreaterDepth, depthWrite: false,
        transparent: true, opacity: DO_DUC.hiddenRim,
      }),
    );
    khuat.renderOrder = THU_TU_VE_THIET_DIEN;
    nhomVanh.add(thay, khuat);
    const rimMeta: CurvedRimLoopMeta = {
      objectId: o.id,
      trong: trongPts,
      ngoai: ngoaiPts,
      midpoints,
      sample: turn => {
        const angle = turn * 2 * Math.PI, cs = Math.cos(angle), sn = Math.sin(angle);
        return { inner: new THREE.Vector3(trongR * cs, trongR * sn, 0), outer: new THREE.Vector3(ngoaiR * cs, ngoaiR * sn, 0) };
      },
      thayMesh: thay,
      khuatMesh: khuat,
      ...themNetVanh(nhomVanh, thay, khuat),
    };
    capNhatHinhHocVanhCong(rimMeta, [], false);
    nhomVanh.userData.curvedRimLoop = rimMeta;
    const n = new THREE.Vector3(...toVec3(o.normal)).normalize();
    nhomVanh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), n);
    nhomVanh.position.set(...toVec3(o.center));
    return v(nhomVanh, `circle:${o.id}`);
  }

  if (
    o.render === "ellipse" && o.center && o.normal &&
    o.major_dir && o.minor_dir && o.semi_major_sq && o.semi_minor_sq
  ) {
    const a = Math.sqrt(Math.max(0, toNumber(o.semi_major_sq)));
    const b = Math.sqrt(Math.max(0, toNumber(o.semi_minor_sq)));
    const M = new THREE.Vector3(...toVec3(o.major_dir)).normalize();
    const m = new THREE.Vector3(...toVec3(o.minor_dir)).normalize();
    // Pháp tuyến định hướng theo (M, m): `tt × n` khi ấy luôn chỉ RA NGOÀI, nên dải viền nằm trong elip dù envelope
    // gửi `normal` ngược chiều (khung tay trái) — trước đó dải lật ra ngoài và cung trước mất màu viền.
    const n = new THREE.Vector3().crossVectors(M, m).normalize();
    const day = beDayNet(diemNen, Math.max(a, b)) * (noiBat ? 0.56 : 0.46);
    const soDoanVanh = 96;
    const trong: THREE.Vector3[] = [];
    const ngoai: THREE.Vector3[] = [];
    const mepTo: THREE.Vector3[] = [];
    const midpoints: THREE.Vector3[] = [];
    for (let i = 0; i <= soDoanVanh; i += 1) {
      const t = (i / soDoanVanh) * Math.PI * 2;
      const P = new THREE.Vector3()
        .addScaledVector(M, a * Math.cos(t))
        .addScaledVector(m, b * Math.sin(t));
      const tt = new THREE.Vector3()
        .addScaledVector(M, -a * Math.sin(t))
        .addScaledVector(m, b * Math.cos(t))
        .normalize();
      const ra = new THREE.Vector3().crossVectors(tt, n).normalize()
        .multiplyScalar(day);
      const pTrong = P.clone().sub(ra);
      trong.push(pTrong);
      ngoai.push(P);
      mepTo.push(pTrong);
      if (i < soDoanVanh) {
        const tm = ((i + 0.5) / soDoanVanh) * Math.PI * 2;
        midpoints.push(
          new THREE.Vector3()
            .addScaledVector(M, a * Math.cos(tm))
            .addScaledVector(m, b * Math.sin(tm)),
        );
      }
    }
    const dinhTo: number[] = [];
    for (let i = 0; i < soDoanVanh; i += 1) {
      const [t0, t1] = [mepTo[i], mepTo[i + 1]];
      dinhTo.push(0, 0, 0, t0.x, t0.y, t0.z, t1.x, t1.y, t1.z);
    }
    const hh = (ds: number[]) => {
      const bg = new THREE.BufferGeometry();
      bg.setAttribute("position", new THREE.Float32BufferAttribute(ds, 3));
      return bg;
    };
    const chungVanh = {
      color: netMien(mauVienMien), side: THREE.DoubleSide,
      forceSinglePass: true,
      ...LECH_THIET_DIEN,
    } as const;
    const nhomVanh = new THREE.Group();
    if (o.fill_visible !== false) {
      const gTo = hh(dinhTo);
      gTo.computeVertexNormals();
      const to = new THREE.Mesh(
        gTo,
        new THREE.MeshBasicMaterial({
          color: nen(mauToMien),
          transparent: true,
          opacity: doDucMien,
          forceSinglePass: true,
          side: THREE.DoubleSide,
          depthWrite: false,
          depthTest: !xray,
          depthFunc: THREE.LessEqualDepth,
          ...LECH_THIET_DIEN,
        }),
      );
      to.name = `section_fill:${o.id}`;
      to.renderOrder = THU_TU_TO_THIET_DIEN;
      nhomVanh.add(to);
    }
    const thay = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({
      ...chungVanh, depthFunc: THREE.LessEqualDepth, transparent: true,
    }));
    thay.renderOrder = THU_TU_VE_THIET_DIEN;
    const khuat = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({
      ...chungVanh, depthFunc: THREE.GreaterDepth, depthWrite: false,
      transparent: true, opacity: DO_DUC.hiddenRim,
    }));
    khuat.renderOrder = THU_TU_VE_THIET_DIEN;
    nhomVanh.add(thay, khuat);
    const rimMeta: CurvedRimLoopMeta = {
      objectId: o.id,
      trong,
      ngoai,
      midpoints,
      sample: turn => {
        const angle = turn * 2 * Math.PI, cs = Math.cos(angle), sn = Math.sin(angle);
        const outer = M.clone().multiplyScalar(a * cs).addScaledVector(m, b * sn);
        const tangent = M.clone().multiplyScalar(-a * sn).addScaledVector(m, b * cs).normalize();
        return { outer, inner: outer.clone().sub(new THREE.Vector3().crossVectors(tangent, n).normalize().multiplyScalar(day)) };
      },
      thayMesh: thay,
      khuatMesh: khuat,
      ...themNetVanh(nhomVanh, thay, khuat),
    };
    capNhatHinhHocVanhCong(rimMeta, [], false);
    nhomVanh.userData.curvedRimLoop = rimMeta;
    nhomVanh.position.set(...toVec3(o.center));
    return v(nhomVanh, `ellipse:${o.id}`);
  }

  if (o.render === "curved_solid" && o.anchor && (o.rim_point || o.radius_sq) && o.curved_kind) {
    const tam = new THREE.Vector3(...toVec3(o.anchor));
    const r = Math.sqrt(Math.max(0, toNumber(o.radius_sq ?? "0")));
    const h = Math.sqrt(Math.max(0, toNumber(o.height_sq ?? "0")));
    const dinh = o.apex_or_top
      ? new THREE.Vector3(...toVec3(o.apex_or_top))
      : o.curved_kind !== "ball" && h > 0
        ? new THREE.Vector3(tam.x, tam.y, tam.z + h)
      : null;
    // Không đèn như vỏ đa diện (HTML tham chiếu: mặt cầu/nón/trụ đều MeshBasicMaterial).
    const m = new THREE.MeshBasicMaterial({
      color: nen(mauKhoi),
      transparent: true,
      opacity: doDucKhoi,
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
      const truc = dinh.clone().sub(tam).normalize();
      mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), truc);
      mesh.position.copy(tam).addScaledVector(truc, h / 2);
    } else {
      mesh.position.copy(tam);
    }
    const nhomCong = new THREE.Group();
    const bong = lopChieuSau(g);
    bong.quaternion.copy(mesh.quaternion);
    bong.position.copy(mesh.position);
    const bongTruoc = lopChieuSauMatTruoc(g);
    bongTruoc.quaternion.copy(mesh.quaternion);
    bongTruoc.position.copy(mesh.position);
    nhomCong.add(mesh, bong, bongTruoc);
    nhomCong.userData.curvedSolidVolume = {
      id: o.id,
      kind: o.curved_kind as "cylinder" | "cone" | "ball",
      anchor: tam.clone(),
      top: dinh ? dinh.clone() : null,
      radius: r,
      height: h,
    } satisfies CurvedSolidVolumeMeta;
    if (o.curved_kind === "ball") {
      // The perspective silhouette is presentation geometry, never an equator or a new scene entity. A closed unit
      // circle LINE (placed per camera by `updateCurvedSolidSilhouette`) so the screen-space pass draws it at the
      // visible-edge pixel width: a world-space ring was 0.6 % of the radius thick (≈1 px, uneven tone on mobile) and
      // could lose arcs to the sphere's own depth layer at the tangent. A convex body never hides its own outline.
      const vongBao = Array.from({ length: 193 }, (_, i) => {
        const t = (i % 192) / 192 * Math.PI * 2;
        return new THREE.Vector3(Math.cos(t), Math.sin(t), 0);
      });
      const outline = new THREE.Line(new THREE.BufferGeometry().setFromPoints(vongBao), new THREE.LineBasicMaterial({
        color: net(MAU.canh), transparent: true, opacity: 1, depthTest: false, depthWrite: false,
      }));
      outline.name = `sphere_silhouette:${o.id}`;
      outline.visible = false; // until `updateCurvedSolidSilhouette` places it for a camera
      outline.renderOrder = THU_TU_DUONG;
      outline.raycast = () => {};
      nhomCong.add(outline);
      if (sphereReference) {
        const reference = buildObject3D({ ...o, type: "circle3", render: "circle", center: o.anchor,
          normal: ["0", "0", "1"], surface_role: "BASE_REGION", fill_visible: false,
          display_role: "presentation_reference" }, false,
          banKinhBam, diemNen, cameraPosition);
        if (reference) {
          reference.name = `sphere_reference:${o.id}`;
          reference.userData.presentationReference = { role: "REFERENCE_CURVE", source_object_id: o.id, authoritative: false };
          reference.traverse(child => { child.raycast = () => {}; });
          nhomCong.add(reference);
        }
      }
    } else if (dinh) {
      // Reuse the existing circle rim primitive for physical boundaries; no synthetic points/names enter the scene.
      // Toạ độ dựng vành phải là phân số hợp lệ cho `toVec3` (`String(1.5)` thì không): chuỗi chính xác của backend khi
      // có, còn lại (đỉnh trên suy từ `height_sq`, pháp tuyến chỉ mang HƯỚNG) là phân số 1e-6. So trùng (`boVanhDayTrung`)
      // dùng số CHƯA làm tròn.
      const phanSo = (v: THREE.Vector3) => v.toArray().map((x) => `${Math.round(x * 1e6)}/1000000`) as [string, string, string];
      const truc = dinh.clone().sub(tam);
      const tamVanh: [[string, string, string], THREE.Vector3][] = [[o.anchor, tam]];
      if (o.curved_kind === "cylinder") tamVanh.push([o.apex_or_top ?? phanSo(dinh), dinh]);
      for (const [center, tamSo] of tamVanh) {
        const rim = buildObject3D({ ...o, type: "circle3", render: "circle", center, normal: phanSo(truc),
          surface_role: "BASE_REGION", formation_roles: [], fill_visible: false }, noiBat,
          banKinhBam, diemNen, cameraPosition);
        if (!rim) continue;
        rim.raycast = () => {};
        rim.userData.vanhDayCua = { center: tamSo.toArray(), axis: truc.toArray(), radius_sq: o.radius_sq };
        nhomCong.add(rim);
      }
      const outline = new THREE.Group();
      outline.name = `curved_silhouette:${o.id}`;
      outline.visible = false; // until `updateCurvedSolidSilhouette` places it for a camera
      for (let i = 0; i < 2; i++) {
        const line = new THREE.Line(createSpanPoolGeometry(), new THREE.LineBasicMaterial({
          color: net(MAU.canh), transparent: true, opacity: 1, depthWrite: false,
        }));
        line.name = `curved_generator:${o.id}:${i}`;
        line.renderOrder = THU_TU_DUONG;
        line.raycast = () => {};
        outline.add(line);
      }
      nhomCong.add(outline);
    }
    return v(nhomCong, `curved:${o.id}:${o.curved_kind}`);
  }

  if (o.render === "mesh" && o.vertices && o.faces) {
    const dinh = o.vertices.map(toVec3);
    const tamKhoi: Vec3 = dinh.length > 0
      ? [
          dinh.reduce((s, p) => s + p[0], 0) / dinh.length,
          dinh.reduce((s, p) => s + p[1], 0) / dinh.length,
          dinh.reduce((s, p) => s + p[2], 0) / dinh.length,
        ]
      : [0, 0, 0];
    const pos: number[] = [];
    for (const f of o.faces) {
      const mat = f.map((j) => dinh[j]);
      for (const [a, b, c] of chiaTamGiac(mat)) {
        const pA = mat[a], pB = mat[b], pC = mat[c];
        const ux = pB[0] - pA[0], uy = pB[1] - pA[1], uz = pB[2] - pA[2];
        const vx = pC[0] - pA[0], vy = pC[1] - pA[1], vz = pC[2] - pA[2];
        const nx = uy * vz - uz * vy;
        const ny = uz * vx - ux * vz;
        const nz = ux * vy - uy * vx;
        const ox = pA[0] - tamKhoi[0], oy = pA[1] - tamKhoi[1], oz = pA[2] - tamKhoi[2];
        const tri = nx * ox + ny * oy + nz * oz < 0 ? [a, c, b] : [a, b, c];
        for (const k of tri) pos.push(...mat[k]);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.computeVertexNormals();
    const nhom = new THREE.Group();
    nhom.add(...voKhoiHaiLuot(g, nen(mauKhoi), doDucKhoi));
    // Lớp chiều sâu riêng: mọi đường sau khối thấy được khối này dù vật liệu
    // mặt trên khai `depthWrite: false`.
    nhom.add(lopChieuSau(g));
    // Mỗi cạnh topology có đúng MỘT visual owner. Derived edge trong cây chỉ
    // là hit proxy, nên không thể tạo lớp solid/dashed chồng lên owner này.
    const audit = classifySolidEdgeVisibility(o, cameraPosition);
    const dashSize = beDayNet(diemNen, 1) / SECTION_STROKE_RATIO * NET_DUT_TI_LE;
    for (const edge of canonicalEdgesOf(o)) {
      const mauQua = highlightedEdgeIds instanceof Map ? highlightedEdgeIds.get(edge.id) : undefined;
      const edgeHighlighted = Boolean(noiBat) || highlightedEdgeIds.has(edge.id);
      const owner = new THREE.Group();
      owner.name = `edge:${edge.id}`;
      owner.userData.visualOwnerId = edge.id;
      owner.userData.canonicalEdge = edge;
      owner.userData.highlighted = edgeHighlighted;
      owner.userData.edgeColor = MAU.canh;
      owner.userData.highlightColor = mau ?? mauQua ?? MAU.highlight;
      owner.userData.dashSize = dashSize;
      owner.userData.khuc = khucToSang.get(edge.id);
      preallocateSpanGeoPool(owner, 6);
      rebuildCanonicalEdgeOwner(owner, edge, audit.edge_spans);
      owner.userData.spanSignature = audit.edge_spans.filter((span) => span.edge_id === edge.id)
        .map((span) => `${span.visibility}:${span.t0}:${span.t1}`).join("|");
      nhom.add(owner);
    }
    nhom.userData.solidSceneObject = o;
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
    const hitProxy = o.display_role === "hit_proxy" && !noiBat;
    return v(new THREE.Mesh(g, new THREE.MeshBasicMaterial(hitProxy ? {
      colorWrite: false,
      depthWrite: false,
      transparent: true,
      opacity: 0,
      side: THREE.DoubleSide,
    } : {
      color: nen(mauKhoi),
      transparent: true,
      opacity: noiBat ? DO_DUC.selectedFace : DO_DUC.face,
      forceSinglePass: true,
      side: THREE.DoubleSide,
      depthWrite: false,
    })), `face:${o.id}`);
  }

  if (o.type === "edge" && o.polygon && o.polygon.length === 2) {
    const g = new THREE.BufferGeometry().setFromPoints(
      o.polygon.map((x) => new THREE.Vector3(...toVec3(x))));
    const hitProxy = o.display_role === "hit_proxy";
    return v(new THREE.Line(g, new THREE.LineBasicMaterial(hitProxy ? {
      colorWrite: false, depthWrite: false, transparent: true, opacity: 0,
      linewidth: NET.pick,
    } : {
      color: net(MAU.line), linewidth: NET.border,
    })), `edge:${o.id}`);
  }

  if (o.render === "polygon" && (o.polygon || o.vertices)) {
    const rawPts = (o.polygon ?? o.vertices ?? []).map(toVec3);
    if (rawPts.length < 2) return null;
    if (o.display_role === "hit_proxy" && !noiBat) {
      const nhomProxy = new THREE.Group();
      if (rawPts.length >= 3) {
        const posProxy: number[] = [];
        for (const [a, b, c] of chiaTamGiac(rawPts)) {
          for (const j of [a, b, c]) posProxy.push(...rawPts[j]);
        }
        const gProxy = new THREE.BufferGeometry();
        gProxy.setAttribute("position", new THREE.Float32BufferAttribute(posProxy, 3));
        nhomProxy.add(new THREE.Mesh(gProxy, new THREE.MeshBasicMaterial({
          colorWrite: false, depthWrite: false, transparent: true, opacity: 0, side: THREE.DoubleSide,
        })));
      }
      return v(nhomProxy, `polygon:${o.id}`);
    }
    const pts = rawPts.map((p) => new THREE.Vector3(...p));
    const vong = o.closed === false ? pts : [...pts, pts[0]];
    const gLine = new THREE.BufferGeometry().setFromPoints(vong);
    const mauVien = netMien(mauVienMien);
    const coNetDut = (beDayNet(diemNen, 1) / SECTION_STROKE_RATIO) * NET_DUT_TI_LE;
    const thietDien = o.type === "section";
    // Same role as the fill color: a section-role polygon3 (tagged or metadata-free) gets section depth/X-ray order.
    const daGiacPhu = o.type === "polygon3" && laThietDien;
    const toXuyenKhoi = thietDien || daGiacPhu;
    const thuTuVien = toXuyenKhoi ? THU_TU_VE_THIET_DIEN : THU_TU_DUONG;
    const doDayVien = noiBat ? NET.selected : NET.border;
    const chungVien = {
      color: mauVien,
      polygonOffset: true,
      polygonOffsetFactor: -2,
      polygonOffsetUnits: -2,
    } as const;
    const line = new THREE.Line(gLine, new THREE.LineBasicMaterial({
      ...chungVien, linewidth: doDayVien, depthFunc: THREE.LessEqualDepth, depthWrite: false,
    }));
    line.name = `polygon_border:${o.id}:thay`;
    line.userData.nonCanonicalBorderLine = true;
    line.renderOrder = thuTuVien;
    const lineKhuat = new THREE.Line(gLine.clone(), new THREE.LineDashedMaterial({
      ...chungVien, linewidth: doDayVien, depthFunc: THREE.GreaterDepth, depthWrite: false,
      dashSize: coNetDut, gapSize: coNetDut, transparent: true, opacity: DO_DUC.hiddenEdge,
    }));
    lineKhuat.computeLineDistances();
    lineKhuat.name = `polygon_border:${o.id}:khuat`;
    lineKhuat.userData.nonCanonicalBorderLine = true;
    lineKhuat.userData.hidden = true;
    lineKhuat.renderOrder = thuTuVien;
    const ownsBoundary = !(
      o.surface_role === "BASE_REGION"
      && o.occludes_edges === false
      && (o.boundary_edge_ids?.length ?? 0) > 0
    );
    const nhom = new THREE.Group();
    if (ownsBoundary) {
      nhom.add(line, lineKhuat);
      preallocateSpanGeoPool(nhom, Math.max(8, pts.length * 4));
      nhom.userData.nonCanonicalLoop = {
        objectId: o.id,
        pts,
        closed: o.closed !== false,
        color: mauVien,
        dashSize: coNetDut,
        highlighted: Boolean(noiBat),
        renderOrder: thuTuVien,
      } satisfies NonCanonicalLoopMeta;
    }

    if (o.closed !== false && o.fill_visible !== false && rawPts.length >= 3) {
      const pos: number[] = [];
      for (const [a, b, c] of chiaTamGiac(rawPts)) {
        for (const j of [a, b, c]) pos.push(...rawPts[j]);
      }
      if (pos.length > 0) {
        const gMesh = new THREE.BufferGeometry();
        gMesh.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
        gMesh.computeVertexNormals();
        // Thiết diện: vật tô RIÊNG, vẽ sau mặt cắt và khối, lệch chiều sâu như nét thiết
        // diện để không hoà vào miếng mặt cắt đồng phẳng; vẫn không ghi chiều sâu, không
        // lớp chiều sâu — vùng tô không che nét nào.
        //
        // Interior fills respect solid depth by default. Only an explicit x-ray choice
        // reveals them through the shell; hidden-line passes keep their own depth semantics.
        //
        // W16: thứ tự `THU_TU_TO_THIET_DIEN` — sau mặt, TRƯỚC nét: cạnh khối đi qua vùng
        // tô vẫn đọc rõ (§14.4), thay vì bị phủ hổ phách như ở thứ tự 10 của W15.
        const mesh = new THREE.Mesh(gMesh, new THREE.MeshBasicMaterial({
          color: nen(mauToMien),
          transparent: true,
          opacity: doDucMien,
          forceSinglePass: true,
          side: THREE.DoubleSide,
          depthWrite: false,
          ...(toXuyenKhoi ? { ...LECH_THIET_DIEN, depthTest: !xray } : {}),
        }));
        mesh.name = `${thietDien ? "section_fill" : "polygon_fill"}:${o.id}`;
        if (toXuyenKhoi) mesh.renderOrder = THU_TU_TO_THIET_DIEN;
        nhom.add(mesh);
      }
    }

    return v(nhom, `polygon:${o.id}`);
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
  /** W18 §16.5: chế độ nhãn số đo trên hình. Vắng ⇒ gọn (dữ kiện + lựa chọn). */
  annotationView?: AnnotationView;
  /** W2 · D: công tắc «Hình phụ» — vắng/false ⇒ hình phụ xong nhiệm vụ và mặt phẳng chỉ để đo ẩn (`scene3d-auxiliary`). */
  auxiliaryShown?: boolean;
  /** W2 · F: lưới nền mảnh, mặc định TẮT; ngoài nhóm gốc ⇒ không vào occlusion, raycast hay khung nhìn. */
  gridShown?: boolean;
  xray?: boolean;
}

/** §16.7 — cạnh góc vuông của ký hiệu tại chân, theo độ dài đoạn tới chân, có trần (đơn vị cảnh). */
const NHAN_CHUNG_GOC = { tiLe: 0.12, toiDa: 0.24 };

/** Màu nhân chứng theo VAI: nhãn khoảng cách đang xét mang xanh "đang xét" (W12); đoạn vuông góc của điểm hình chiếu
 *  luôn hiện nên là ĐƯỜNG PHỤ — cùng màu với các đường phụ khác, không giành nghĩa "đang xét" (review, 2026-10-11). */
export function mauNhanChung(vai: WitnessShown["vai"]): number {
  return vai === "hinh_chieu" ? MAU.line : MAU_VAI_TRO.dich;
}

interface GocVuongDonVi {
  foot: Vec3; u: Vec3; v: Vec3; s0: number; maxWorld: number; cornerOwner: THREE.Object3D;
  /** Một quan hệ backend (`relation|rule|on`, vd mọi cạnh bên ⊥ đáy): mặc định chỉ một dấu đại diện (`datCoGocVuong`). */
  nhomQuanHe?: string;
  /** Id thực thể hai đầu mút của đoạn mang chứng chỉ (`from`, `foot_id`) — để đọc độ thấy của cạnh khối trùng nó. */
  dauMut?: [string, string];
}

/** Ký hiệu góc vuông dạng ô vuông HAI đoạn (`addRightAngleMarker` của HTML tham chiếu): `foot + s0·u`,
 *  `foot + s0·(u+v)`, `foot + s0·v` ở toạ độ cảnh. `u`, `v` là hai phương ĐƠN VỊ backend đã chứng nhận vuông góc —
 *  không suy luận gì ở đây. `s0` là cỡ dựng; `datCoGocVuong` co/giãn quanh chân theo pixel, không vượt `maxWorld`
 *  (một phần đoạn liên quan) để dấu không lấn ra ngoài cạnh của nó. */
function dauGocVuong(
  foot: Vec3, u: Vec3, v: Vec3, s0: number, maxWorld: number, color: number, cornerOwner?: THREE.Object3D,
): THREE.Line {
  const p = (a: number, b: number) =>
    new THREE.Vector3(foot[0] + s0 * (a * u[0] + b * v[0]), foot[1] + s0 * (a * u[1] + b * v[1]),
      foot[2] + s0 * (a * u[2] + b * v[2]));
  const line = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([p(1, 0), p(1, 1), p(0, 1)]),
    new THREE.LineBasicMaterial({ color, linewidth: NET.perpendicular, transparent: true }),
  );
  const goc = p(1, 1);
  line.userData = { foot, corner: [goc.x, goc.y, goc.z] as Vec3 };
  line.userData.gocVuongDonVi = { foot, u, v, s0, maxWorld: Math.max(s0, maxWorld), cornerOwner: cornerOwner ?? line } satisfies GocVuongDonVi;
  return line;
}

/** Khoá trùng của một dấu ở toạ độ THẾ GIỚI (sau phép tách/cô lập của cha): chân + cặp phương không phân biệt dấu. */
function khoaGocVuong(d: GocVuongDonVi, cha: THREE.Matrix4): string {
  const chuan = (p: Vec3) => {
    const q = new THREE.Vector3(...p).transformDirection(cha).toArray();
    const k = q.find((x) => Math.abs(x) > 1e-6) ?? 1;
    return q.map((x) => (Math.sign(k) * x).toFixed(3)).join(",");
  };
  const chan = new THREE.Vector3(...d.foot).applyMatrix4(cha).toArray();
  return [chan.map((x) => x.toFixed(4)).join(","), ...[chuan(d.u), chuan(d.v)].sort()].join("|");
}

/**
 * Cỡ ký hiệu vuông góc theo MÀN HÌNH: cạnh dấu ≈ `rightAngle.perCanvasHeight` × chiều cao khung, kẹp
 * [`minPx`, `maxPx`] (16–22 px). Co/giãn quanh chân, nhưng cỡ world không vượt `maxWorld` (một phần đoạn liên quan).
 * Cỡ điểm ảnh tỉ lệ nghịch với ĐỘ SÂU view-space của chân — phép chiếu của camera, không phép hình học nào trên
 * cảnh. Có `tamNhin` (đích OrbitControls): chỉ tính lại khi độ sâu của TÂM NHÌN đổi (thu phóng, đặt khung) — lúc chỉ
 * XOAY, cỡ world giữ nguyên nên toạ độ dấu đứng yên và nét dày không cấp phát lại buffer GPU mỗi khung (cổng
 * `scene3d-orbit-gate`, `capPhat = 0`). Hai dấu cùng chân và cùng cặp phương (toạ độ thế giới) ⇒ giữ dấu ĐẬM nhất
 * (dấu đang nhấn / không bị làm dịu), ẩn các dấu lặp; dấu dưới một tổ tiên ẩn không tranh khoá. Trả số dấu đang hiện.
 */
/** Đại diện đang hiện của mỗi nhóm quan hệ (theo gốc cảnh) — chỉ để giữ ổn định giữa các khung. */
const _daiDienGocVuong = new WeakMap<THREE.Object3D, Map<string, string>>();
/** Độ "mở" tối thiểu (diện tích chiếu / diện tích không co) để dấu đại diện còn đọc được: 0.15 ≈ cos 81°. */
export const DO_MO_TOI_THIEU = 0.15;

export function datCoGocVuong(
  roots: readonly THREE.Object3D[], cam: THREE.Camera, hCss: number, tamNhin?: THREE.Vector3,
): number {
  const pc = cam as THREE.PerspectiveCamera;
  if (!pc.isPerspectiveCamera || !(hCss > 0)) return 0;
  const cfg = PHONG_CACH_SCENE3D.rightAngle;
  const px = Math.min(cfg.maxPx, Math.max(cfg.minPx, cfg.perCanvasHeight * hCss));
  const f = hCss / (2 * Math.tan((pc.fov * Math.PI) / 360));
  pc.updateMatrixWorld();
  const chan = new THREE.Vector3();
  const doSauTam = tamNhin ? -chan.copy(tamNhin).applyMatrix4(pc.matrixWorldInverse).z : null;
  const DONG_NHAT_MT = new THREE.Matrix4();
  // Lượt 1: gom ứng viên (khoá thế giới, độ đậm, tổ tiên có hiện không).
  const ungVien: { node: THREE.Object3D; d: GocVuongDonVi; khoa: string; dam: number; toTienHien: boolean }[] = [];
  for (const r of roots) {
    r.updateMatrixWorld(true);
    r.traverse((node) => {
      const d = node.userData?.gocVuongDonVi as GocVuongDonVi | undefined;
      if (!d) return;
      let toTienHien = true;
      for (let p = node.parent; p; p = p.parent) if (!p.visible) { toTienHien = false; break; }
      const mat = (node as THREE.Line).material as THREE.Material | undefined;
      ungVien.push({ node, d, khoa: khoaGocVuong(d, node.parent?.matrixWorld ?? DONG_NHAT_MT),
        dam: mat?.opacity ?? 1, toTienHien });
    });
  }
  // Lượt 2: mỗi khoá giữ MỘT dấu — dấu đậm nhất trong số dấu có tổ tiên hiện (hoà ⇒ dấu gặp trước).
  const thang = new Map<string, (typeof ungVien)[number]>();
  for (const c of ungVien) {
    if (!c.toTienHien) continue;
    const cu = thang.get(c.khoa);
    if (!cu || c.dam > cu.dam) thang.set(c.khoa, c);
  }
  // Lượt 3 (Owner 2026-10-26: ít dấu hơn, không xoá quan hệ): các dấu của CÙNG một quan hệ backend (`nhomQuanHe`,
  // vd bốn cạnh bên ⊥ đáy) ⇒ mặc định một dấu. Dấu của đoạn đang nhấn (bước hiện tại / đang chọn) luôn hiện; không
  // đoạn nào nhấn ⇒ một đại diện dễ đọc nhất: ưu tiên đoạn không khuất hoàn toàn, rồi ô vuông 3D THẬT chiếu ra "mở"
  // nhất (diện tích chiếu / diện tích không co ≈ |cos| giữa mặt phẳng dấu và tia nhìn — không đổi hình dấu). GIỮ đại
  // diện cũ trừ khi ứng viên khác mở hơn rõ (25 %), để dấu không nhảy góc khi xoay.
  const laNhanManh = (n: THREE.Object3D) =>
    Boolean(n.parent?.children.some((x) => (x.userData?.nonCanonicalSegment as { highlighted?: boolean } | undefined)?.highlighted));
  // Cạnh chuẩn KHUẤT HẲN theo phân loại của chính lượt thấy/khuất (`updateCanonicalEdgeVisibility` ghi lên gốc) — đoạn
  // trùng cạnh khối nhường nét cho cạnh ấy (`colinearCanonicalIds`), nên độ thấy của nó là của cạnh chuẩn.
  const canhKhuat = new Set(roots.flatMap((r) => [...((r.userData.hiddenCanonicalEdgeIds as Set<string> | undefined) ?? [])]));
  const capDinhKhuat = [...canhKhuat].flatMap((id) => {
    const cap = id.split("::edge:")[1]?.split("-");
    return cap?.length === 2 ? [cap.slice().sort().join("|")] : [];
  });
  const khuatHet = (c: (typeof ungVien)[number]) => {
    const duong = c.node.parent?.children.find((x) => x.userData?.nonCanonicalSegment);
    const khuc = duong?.children.filter((x) => x.userData?.nonCanonicalSpanLine && !x.name.endsWith(":proxy")) ?? [];
    if (khuc.length > 0) return khuc.every((x) => x.userData.hidden === true);
    const trung = (duong?.userData.colinearCanonicalIds as string[] | undefined) ?? [];
    if (trung.length > 0) return trung.every((id) => canhKhuat.has(id));
    // Đoạn đã nhường hẳn nét cho cạnh khối (vùng bấm, không tự phân loại): đọc cạnh khối có CÙNG hai đầu mút (id thực
    // thể backend `from`/`foot_id` của chứng chỉ) trong phân loại của lượt thấy/khuất.
    const dau = c.d.dauMut;
    return dau !== undefined && capDinhKhuat.includes(dau.slice().sort().join("|"));
  };
  const wCss = hCss * (pc.aspect || 1);
  const doMo = (c: (typeof ungVien)[number]) => {
    const m = c.node.parent?.matrixWorld ?? DONG_NHAT_MT;
    const F = new THREE.Vector3(...c.d.foot).applyMatrix4(m);
    const sau = -F.clone().applyMatrix4(pc.matrixWorldInverse).z;
    if (!(sau > 0)) return 0;
    const eps = 1e-3 * sau;                         // probe ≪ depth: the perspective linearisation error stays ≈ 0.1 %
    const diem = [F, new THREE.Vector3(...c.d.u).transformDirection(m).multiplyScalar(eps).add(F),
      new THREE.Vector3(...c.d.v).transformDirection(m).multiplyScalar(eps).add(F)]
      .map((p) => { const q = p.project(pc); return [(q.x * wCss) / 2, (q.y * hCss) / 2]; });
    const dt = Math.abs((diem[1][0] - diem[0][0]) * (diem[2][1] - diem[0][1]) - (diem[1][1] - diem[0][1]) * (diem[2][0] - diem[0][0]));
    return dt / (f * 1e-3) ** 2;
  };
  const theoNhom = new Map<string, (typeof ungVien)[number][]>();
  for (const c of thang.values()) {
    const k = c.d.nhomQuanHe;
    if (k) theoNhom.set(k, [...(theoNhom.get(k) ?? []), c]);
  }
  // Chân đã mang một dấu RIÊNG (không thuộc nhóm, vd đoạn vuông góc chung chân A): đại diện của một nhóm tránh chỗ đó —
  // hai ô vuông ở một đỉnh đọc như rác, không như một quan hệ. Khoá chân = phần đầu của `khoa` (toạ độ thế giới).
  const chanRieng = new Set([...thang.values()].filter((c) => !c.d.nhomQuanHe).map((c) => c.khoa.split("|")[0]));
  const truoc = roots[0] ? (_daiDienGocVuong.get(roots[0]) ?? new Map<string, string>()) : new Map<string, string>();
  if (roots[0]) _daiDienGocVuong.set(roots[0], truoc);
  const anTheoNhom = new Set<(typeof ungVien)[number]>();
  for (const [k, ds] of theoNhom) {
    if (ds.length < 2) continue;
    const nhan = ds.filter((c) => laNhanManh(c.node));
    let giu: (typeof ungVien)[number][];
    if (nhan.length > 0) giu = nhan;
    else {
      const hang = new Map(ds.map((c) => [c, { thay: khuatHet(c) ? 0 : 1, rieng: chanRieng.has(c.khoa.split("|")[0]) ? 0 : 1,
        mo: doMo(c) }]));
      const hon = (a: (typeof ds)[number], b: (typeof ds)[number]) => {
        const x = hang.get(a)!, y = hang.get(b)!;
        return x.thay !== y.thay ? x.thay > y.thay : x.rieng !== y.rieng ? x.rieng > y.rieng : x.mo > y.mo;
      };
      const tot = ds.reduce((a, b) => (hon(b, a) ? b : a));
      const cu = ds.find((c) => c.node.uuid === truoc.get(k));
      const giuCu = cu !== undefined && hang.get(cu)!.thay === hang.get(tot)!.thay && hang.get(cu)!.rieng === hang.get(tot)!.rieng
        && hang.get(tot)!.mo <= hang.get(cu)!.mo * 1.25;
      const chon = giuCu ? cu! : tot;
      truoc.set(k, chon.node.uuid);
      // Ngay cả dấu dễ đọc nhất cũng gần như nằm dọc tia nhìn (mặt phẳng dấu lệch < ~9° so với tia) ⇒ ô vuông bẹp thành
      // một vạch, không còn đọc được là góc vuông: mặc định không vẽ (không bao giờ thay bằng góc vuông màn hình giả).
      giu = hang.get(chon)!.mo >= DO_MO_TOI_THIEU ? [chon] : [];
    }
    for (const c of ds) if (!giu.includes(c)) anTheoNhom.add(c);
  }
  let hien = 0;
  for (const c of ungVien) {
    const { node, d } = c;
    node.visible = thang.get(c.khoa) === c && !anTheoNhom.has(c);
    if (!node.visible) continue;
    hien += 1;
    // Chỉ XOAY (độ sâu tâm nhìn, cỡ khung và vị trí cha không đổi) ⇒ giữ cỡ world đã đặt: không ghi toạ độ mới.
    const e = node.parent?.matrixWorld.elements;
    const khoaCo = doSauTam === null ? null
      : `${doSauTam.toFixed(6)}|${hCss}|${e ? [e[12], e[13], e[14]].map((x) => x.toFixed(6)).join(",") : ""}`;
    if (khoaCo !== null && node.userData.khoaCoGocVuong === khoaCo) continue;
    node.userData.khoaCoGocVuong = khoaCo;
    const doSau = -chan.set(...d.foot).applyMatrix4(node.parent?.matrixWorld ?? DONG_NHAT_MT)
      .applyMatrix4(pc.matrixWorldInverse).z;
    const k = doSau > 0 ? Math.min(d.maxWorld, (px * doSau) / f) / d.s0 : 1;
    node.scale.setScalar(k);
    node.position.set(d.foot[0] * (1 - k), d.foot[1] * (1 - k), d.foot[2] * (1 - k));
    node.updateMatrixWorld(true);
    const s = k * d.s0;
    d.cornerOwner.userData.corner = [d.foot[0] + (d.u[0] + d.v[0]) * s, d.foot[1] + (d.u[1] + d.v[1]) * s,
      d.foot[2] + (d.u[2] + d.v[2]) * s];
  }
  return hien;
}

/** Đoạn HỮU HẠN đã vẽ của cảnh (cạnh khối, cạnh đa giác, đoạn thẳng) — để đoạn chứng minh không vẽ chồng lên chúng. */
export function doanDaVe(objects: readonly SceneObject[]): [Vec3, Vec3][] {
  return objects.flatMap((o): [Vec3, Vec3][] => {
    if (o.type === "segment3" && o.endpoints?.length === 2) return [[toVec3(o.endpoints[0]), toVec3(o.endpoints[1])]];
    const dinh = o.vertices?.map(toVec3);
    if (!dinh) return [];
    const vong = o.type === "solid" ? (o.faces ?? []) : o.type === "polygon3" ? [dinh.map((_, i) => i)] : [];
    return vong.flatMap((f) => f.map((i, k): [Vec3, Vec3] => [dinh[i], dinh[f[(k + 1) % f.length]]]));
  });
}

/** Nhân chứng một khoảng cách: đoạn nét đứt từ điểm tới CHÂN backend phát + ký hiệu vuông góc dựng từ
 *  hai phương backend phát (`u`, `v`) — chỉ đổi độ dài để có cỡ ký hiệu, không suy luận hình học nào.
 *  Có `uTo` (Owner 2026-10-26): cạnh trong vật nhận của dấu chĩa ĐÚNG tới điểm có tên ấy, và đoạn chứng minh
 *  chân → điểm được vẽ (trừ khi nó đã là một đoạn của hình) — dấu nằm giữa hai đường thật, không lơ lửng.
 *  Chân trùng một điểm có tên đang vẽ (`diemCoTen`, vd chân A của SA ⊥ (ABCD)) ⇒ không thêm chấm chân: chấm thứ hai
 *  chồng lên góc dấu và tô đỉnh đề cho bằng màu điểm dẫn xuất. */
export function vatNhanChung(
  w: WitnessShown,
  diemNen: Vec3[] = [],
  mau?: number,
  diu = false,
  doanCo: readonly [Vec3, Vec3][] = [],
  diemCoTen: readonly Vec3[] = [],
): THREE.Group {
  const g = new THREE.Group();
  const tu = new THREE.Vector3(...w.from);
  const chan = new THREE.Vector3(...w.foot);
  const v = new THREE.Vector3(...w.v);
  const uHuong: Vec3 = w.uTo
    ? [w.uTo[0] - w.foot[0], w.uTo[1] - w.foot[1], w.uTo[2] - w.foot[2]]
    : huongChanVuongGoc(w.foot, w.u, diemNen, w.v);
  const dk = duongKinhCanh(diemNen);
  const s = dk > 0
    ? Math.min(v.length() * 0.18, Math.max(v.length() * NHAN_CHUNG_GOC.tiLe, dk * 0.032), dk * 0.042, NHAN_CHUNG_GOC.toiDa)
    : Math.min(v.length() * NHAN_CHUNG_GOC.tiLe, NHAN_CHUNG_GOC.toiDa);
  const chuKy = dk > 0 ? Math.max(0.045, Math.min(0.16, dk * 0.034), s * 1.05) : Math.max(0.12, s * 1.05);
  const uDon = new THREE.Vector3(...uHuong).normalize();
  const vDon = v.clone().normalize();
  const mauNet = mau ?? mauNhanChung(w.vai);
  const doan = new THREE.Line(new THREE.BufferGeometry().setFromPoints([chan, tu]),
    new THREE.LineDashedMaterial({ color: mauNet, dashSize: chuKy, gapSize: chuKy * PHONG_CACH_SCENE3D.dash.witnessGapRatio, depthTest: false, transparent: true, opacity: DO_DUC.witness }));
  doan.computeLineDistances();
  // Ký hiệu vuông góc dựng ở cỡ `s`; `datCoGocVuong` co/giãn về pixel và cập nhật `corner` của nhóm.
  const daiNhanChung = Math.hypot(tu.x - chan.x, tu.y - chan.y, tu.z - chan.z);
  const goc = dauGocVuong([chan.x, chan.y, chan.z], [uDon.x, uDon.y, uDon.z], [vDon.x, vDon.y, vDon.z], s,
    PHONG_CACH_SCENE3D.rightAngle.maxLegRatio * daiNhanChung, mauNet, g);
  (goc.material as THREE.LineBasicMaterial).depthTest = false;
  (goc.material as THREE.LineBasicMaterial).opacity = DO_DUC.witness;
  const gocDinh = chan.clone().addScaledVector(uDon, s).addScaledVector(vDon, s);
  const mauChan = mau ?? (w.vai === "khoang_cach" ? mauNet : MAU.derived);
  const chamChan = new THREE.Mesh(
    new THREE.SphereGeometry(BAN_KINH_NHIN, 16, 12),
    new THREE.MeshBasicMaterial({ color: mauChan, depthTest: false, transparent: true, opacity: DO_DUC.foot }),
  );
  chamChan.position.copy(chan);
  chamChan.userData.dauDinh = "thuong";
  const canhPhu: THREE.Line[] = [];
  if (w.uTo && !namTrenDoanDaVe(w.foot, w.uTo, doanCo)) {
    const chanToi = new THREE.Line(new THREE.BufferGeometry().setFromPoints([chan, new THREE.Vector3(...w.uTo)]),
      (doan.material as THREE.LineDashedMaterial).clone());
    chanToi.computeLineDistances();
    chanToi.name = `witness_leg:${w.id}`;
    canhPhu.push(chanToi);
  }
  // Đoạn chân → điểm đã là một đoạn của hình (góc vuông BC ⊥ (SAB) đặt trên cạnh BC): không vẽ bản nét đứt thứ hai.
  const doanCanVe = w.khongVeDoan || namTrenDoanDaVe(w.from, w.foot, doanCo) ? [] : [doan];
  const chanLaDiemCoTen = diemCoTen.some((p) => Math.hypot(p[0] - w.foot[0], p[1] - w.foot[1], p[2] - w.foot[2]) < 1e-9);
  for (const x of [...doanCanVe, ...canhPhu, goc, ...(chanLaDiemCoTen ? [] : [chamChan])]) {
    x.renderOrder = x === chamChan ? 11 : 10;
    x.raycast = () => {};                 // trình bày thuần: không bao giờ bắt cú bấm chọn vật
    g.add(x);
  }
  g.userData = {
    nhanChung: w.id,
    from: w.from,
    foot: w.foot,
    corner: [gocDinh.x, gocDinh.y, gocDinh.z] as Vec3,
  };
  if (diu) lamDiu(g, HE_SO_LAM_DIU);
  return g;
}

/** Vùng một lớp phủ khác đang che khung (`data-che-khung`: nút nổi, ô soi, ngăn kéo) — nhãn
 *  số đo không được nằm dưới nó. Toạ độ px trong khung `goc`. */
function vungCheKhung(goc: DOMRect): LabelRect[] {
  return Array.from(document.querySelectorAll<HTMLElement>("[data-che-khung]")).flatMap((el) => {
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 ? [{ x: r.left - goc.left, y: r.top - goc.top, w: r.width, h: r.height }] : [];
  });
}

/**
 * Lưới định hướng không gian sư phạm (`Lưới nền`): thưa (`8×8` ô), nhạt dần từ tâm ra biên theo 3 vành bán kính
 * để không tạo viền cứng cắt khung và không có hai trục đậm giả hệ trục toạ độ ở giữa đáy.
 * Khi cảnh có mặt phẳng toán học đang hiện/được chọn, `heSoDiu < 1` hạ thêm độ đậm để mặt phẳng bài toán luôn nổi bật hơn.
 */
export function dungLuoiNenSuPham(diem: Vec3[], heSoDiu = 1): THREE.Group {
  const nhom = new THREE.Group();
  nhom.name = "luoi_nen_su_pham";
  if (diem.length === 0) return nhom;
  const lo = [0, 1, 2].map((i) => Math.min(...diem.map((p) => p[i])));
  const hi = [0, 1, 2].map((i) => Math.max(...diem.map((p) => p[i])));
  const spanXY = Math.max(hi[0] - lo[0], hi[1] - lo[1], 1);
  const spanZ = Math.max(hi[2] - lo[2], spanXY, 1);
  const banKinh = spanXY * 0.92;
  const cx = (lo[0] + hi[0]) / 2;
  const cy = (lo[1] + hi[1]) / 2;
  const z0 = lo[2] - spanZ * 0.012;
  const soO = 8;
  const soKhuc = 16;
  const vanh0: number[] = [];
  const vanh1: number[] = [];
  const vanh2: number[] = [];
  const themDoan = (x0: number, y0: number, x1: number, y1: number) => {
    for (let s = 0; s < soKhuc; s++) {
      const t0 = s / soKhuc;
      const t1 = (s + 1) / soKhuc;
      const ax = x0 + (x1 - x0) * t0;
      const ay = y0 + (y1 - y0) * t0;
      const bx = x0 + (x1 - x0) * t1;
      const by = y0 + (y1 - y0) * t1;
      const mx = (ax + bx) / 2 - cx;
      const my = (ay + by) / 2 - cy;
      const r = Math.hypot(mx, my) / banKinh;
      if (r > 1.06) continue;
      const mang = r <= 0.52 ? vanh0 : r <= 0.82 ? vanh1 : vanh2;
      mang.push(ax, ay, z0, bx, by, z0);
    }
  };
  for (let i = 0; i <= soO; i++) {
    const u = -banKinh + (2 * banKinh * i) / soO;
    themDoan(cx - banKinh, cy + u, cx + banKinh, cy + u);
    themDoan(cx + u, cy - banKinh, cx + u, cy + banKinh);
  }
  const taoVanh = (ten: string, ds: number[], mau: number, doDucGoc: number) => {
    if (ds.length === 0) return;
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(ds, 3));
    const m = new THREE.LineBasicMaterial({
      color: mau,
      transparent: true,
      opacity: Number((doDucGoc * heSoDiu).toFixed(4)),
      depthWrite: false,
    });
    const l = new THREE.LineSegments(g, m);
    l.name = ten;
    l.renderOrder = -2;
    l.raycast = () => {};
    nhom.add(l);
  };
  taoVanh("luoi:trong", vanh0, MAU.grid, DO_DUC.gridInner);
  taoVanh("luoi:giua", vanh1, MAU.grid, DO_DUC.gridMiddle);
  taoVanh("luoi:ngoai", vanh2, MAU.gridOuter, DO_DUC.gridOuter);
  nhom.userData = {
    divisions: soO,
    z0,
    heSoDiu,
  };
  return nhom;
}

/**
 * Đặt vị trí nhãn điểm hướng ra ngoài tâm hình chiếu, đồng thời tránh các cạnh đi qua đỉnh
 * và ký hiệu góc vuông tại chân đường cao (như đỉnh A trong family04_derived_sub_pyramid).
 */
const THUONG_GIU_HUONG = 10;

/**
 * Owner 2026-10-26 (P5): khi va chạm THẬT buộc nhãn đổi chỗ, nhãn TRƯỢT tới chỗ mới thay vì nhảy — mỗi khung đi
 * `k` phần quãng còn lại của ĐỘ LỆCH so với điểm neo (điểm neo vẫn bám đúng điểm 3D), khớp hẳn khi còn < 0.5 px.
 * Nhãn mới xuất hiện (chưa có lệch cũ) đặt thẳng vào chỗ.
 */
export function lamMuotLechNhan(
  truoc: { dx: number; dy: number } | undefined, dich: { dx: number; dy: number }, k = 0.5,
): { dx: number; dy: number } {
  if (!truoc || Math.hypot(dich.dx - truoc.dx, dich.dy - truoc.dy) < 0.5) return dich;
  return { dx: truoc.dx + (dich.dx - truoc.dx) * k, dy: truoc.dy + (dich.dy - truoc.dy) * k };
}

export function tinhViTriNhanDiem(
  diem: readonly { id: string; x: number; y: number; w: number; h: number }[],
  canh2d: readonly { ax: number; ay: number; bx: number; by: number }[],
  gocVuong: readonly { fx: number; fy: number; cx: number; cy: number; tx?: number; ty?: number }[],
  /** Hướng (rad, màn hình) đã chọn ở khung trước, theo id — được cập nhật tại chỗ. Owner 2026-10-26 (P5): ứng viên gần
   *  hướng cũ được cộng tối đa `THUONG_GIU_HUONG` điểm, đủ để hai phía tương đương không đổi qua lại giữa các khung khi
   *  xoay, quá nhỏ để thắng một va chạm thật (phạt tới ~77 điểm khi đè lên nét). */
  huongTruoc?: Map<string, number>,
): Map<string, { x: number; y: number; duoi: boolean }> {
  const ra = new Map<string, { x: number; y: number; duoi: boolean }>();
  if (diem.length === 0) return ra;
  const cx = diem.reduce((s, p) => s + p.x, 0) / diem.length;
  const cy = diem.reduce((s, p) => s + p.y, 0) / diem.length;

  const kcDiemDoan = (px: number, py: number, ax: number, ay: number, bx: number, by: number) => {
    const abx = bx - ax, aby = by - ay;
    const lenSq = abx * abx + aby * aby;
    if (lenSq < 1e-6) return Math.hypot(px - ax, py - ay);
    const t = Math.max(0, Math.min(1, ((px - ax) * abx + (py - ay) * aby) / lenSq));
    return Math.hypot(ax + abx * t - px, ay + aby * t - py);
  };

  const deltas = [0, -0.36, 0.36, -0.74, 0.74, -1.14, 1.14, -1.57, 1.57, -2.05, 2.05, Math.PI];

  for (const p of diem) {
    const cw = Math.max(14, p.w || 18);
    const ch = Math.max(14, p.h || 18);
    let rx = p.x - cx;
    let ry = p.y - cy;
    const rLen = Math.hypot(rx, ry);
    if (rLen < 1e-3) {
      rx = 0;
      ry = -1;
    } else {
      rx /= rLen;
      ry /= rLen;
    }
    for (const g of gocVuong) {
      if (Math.hypot(g.fx - p.x, g.fy - p.y) < 10) {
        const gx = g.cx - p.x;
        const gy = g.cy - p.y;
        const gLen = Math.hypot(gx, gy) || 1;
        rx -= (gx / gLen) * 1.45;
        ry -= (gy / gLen) * 1.45;
      }
    }
    const norm = Math.hypot(rx, ry) || 1;
    rx /= norm;
    ry /= norm;

    const theta0 = Math.atan2(ry, rx);
    const dist = Math.hypot(cw * 0.5, ch * 0.5) + 7.5;
    let bestLx = p.x - cw / 2;
    let bestLy = p.y - 1.4 * ch;
    let bestScore = -Infinity;
    let bestTheta = theta0;
    const cu = huongTruoc?.get(p.id);

    for (const dTheta of deltas) {
      const theta = theta0 + dTheta;
      const ux = Math.cos(theta);
      const uy = Math.sin(theta);
      const mx = p.x + ux * dist;
      const my = p.y + uy * dist;
      const lx = mx - cw / 2;
      const ly = my - ch / 2;

      let score = (ux * rx + uy * ry) * 16;
      if (cu !== undefined) {
        const lech = Math.abs(Math.atan2(Math.sin(theta - cu), Math.cos(theta - cu)));
        score += THUONG_GIU_HUONG * Math.max(0, 1 - lech / 0.6);
      }

      for (const s of canh2d) {
        const dSeg = kcDiemDoan(mx, my, s.ax, s.ay, s.bx, s.by);
        if (dSeg < 16) {
          score -= (16 - dSeg) * 4.8;
        }
      }

      for (const g of gocVuong) {
        const dCorner = Math.hypot(mx - g.cx, my - g.cy);
        const dMid = Math.hypot(mx - (g.fx + g.cx) * 0.5, my - (g.fy + g.cy) * 0.5);
        const dMin = Math.min(dCorner, dMid);
        if (dMin < 20) {
          score -= (20 - dMin) * 7.5;
        }
        if (Math.hypot(g.fx - p.x, g.fy - p.y) < 10) {
          const gx = g.cx - p.x;
          const gy = g.cy - p.y;
          const gLen = Math.hypot(gx, gy) || 1;
          score -= (ux * (gx / gLen) + uy * (gy / gLen)) * 22;
        }
      }

      for (const q of diem) {
        if (q.id === p.id) continue;
        const dq = Math.hypot(mx - q.x, my - q.y);
        if (dq < 24) {
          score -= (24 - dq) * 4.0;
        }
      }

      if (score > bestScore) {
        bestScore = score;
        bestLx = lx;
        bestLy = ly;
        bestTheta = theta;
      }
    }

    huongTruoc?.set(p.id, bestTheta);
    ra.set(p.id, { x: bestLx, y: bestLy, duoi: bestLy > p.y });
  }
  return ra;
}

export function Scene3DWorkspace({
  scene, step, interaction, onSelect, fitToken = 0, annotationView = DEFAULT_ANNOTATION_VIEW,
  auxiliaryShown = false, gridShown = false, xray = false,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rootRef = useRef<THREE.Group | null>(null);
  const veRef = useRef<(() => void) | null>(null);
  //: Đặt lại khung nhìn cho vừa hình. Giữ trong ref vì nó do vòng dựng cảnh
  //: tạo ra (cần `cam`, `controls`) nhưng được gọi từ ngoài vòng ấy.
  const vuaKhungRef = useRef<(() => void) | null>(null);
  const sceneRef = useRef(scene);
  sceneRef.current = scene;
  //: Hướng nhãn điểm của khung trước (`tinhViTriNhanDiem`), để nhãn không nhảy qua lại khi xoay; xoá khi đổi cảnh.
  const huongNhanRef = useRef(new Map<string, number>());
  //: Độ lệch nhãn ĐANG vẽ so với điểm neo (`lamMuotLechNhan`): nhãn trượt thay vì nhảy; xoá khi đổi cảnh.
  const lechNhanRef = useRef(new Map<string, { dx: number; dy: number }>());
  useEffect(() => { huongNhanRef.current.clear(); lechNhanRef.current.clear(); }, [scene]);
  const vaiKhoiTheoId = useMemo(() => vaiTroKhoi(scene), [scene]);
  const [webglFailed, setWebglFailed] = useState(false);
  const [hoveredSection, setHoveredSection] = useState<string | null>(null);
  useEffect(() => { setHoveredSection(null); }, [scene]);
  /* regular-triangular-pyramid-w01 — XOAY HIỂN THỊ: đáy chóp nghiêng (§18.2) về nằm ngang. Đồng nhất thức cho mọi cảnh
     có đáy ngang (mọi họ trước), nên các họ ấy không đổi một điểm ảnh. Áp lên nhóm gốc + nhóm nhân chứng; vị trí THẾ GIỚI
     của nhãn/khung nhìn/lưới đi qua cùng phép quay (`xoay`). Toạ độ cảnh không đổi. */
  const qHienThi = useMemo(() => quayHienThi(scene.objects), [scene]);
  const qRef = useRef(qHienThi);
  qRef.current = qHienThi;
  // exact-dimensions: T khung (cột-chính 4×4) của cảnh có `chart_metric` — chỉ cho ảnh chụp camera của bộ đo.
  const tRef = useRef<number[] | null>(null);
  tRef.current = maTranKhung4(scene);
  const buoc = clampStep(scene, step);
  // Vắng `interaction` ⇒ trạng thái đầu, tức hành vi TRƯỚC wave này nguyên
  // vẹn: hiện mọi thứ, không bung, tô sáng theo bước.
  const tuongTac = interaction ?? TRANG_THAI_DAU;
  const tapNoiBat = useMemo(
    () =>
      new Set(
        tuongTac?.selected_id
          ? highlightSet(scene, tuongTac.selected_id, true)
          : geometryHighlightedAt(scene, buoc),
      ),
    [scene, tuongTac.selected_id, buoc],
  );
  // Chỉ khi NGƯỜI DÙNG chọn: phân tầng chuỗi nhân quả; null = trung tính.
  const tang = useMemo(
    () => (tuongTac.selected_id ? tangNhanManh(scene, tuongTac.selected_id) : null),
    [scene, tuongTac.selected_id],
  );
  const anPhu = useMemo(
    () => auxiliaryHiddenAt(scene, buoc, auxiliaryShown, tuongTac.selected_id ?? null),
    [scene, buoc, auxiliaryShown, tuongTac.selected_id],
  );
  // W17 · §15.4 / W18 · §16.5: nhãn số đo của bước — gọn mặc định, tập trung theo lựa chọn. Chủ thể
  // phải đang hiện — ẩn/cô lập theo cùng luật nhãn điểm. "Hiện tất cả" chỉ đổi danh sách này (và nhân
  // chứng của nó): hình, camera, bước, chuỗi nhân quả, nét đứt không đọc nó.
  const coMatNhan = useMemo(
    () => new Set(objectsAt(scene, buoc).filter((o) => !anPhu.has(o.id)).map((o) => o.id)),
    [scene, buoc, anPhu],
  );
  const nhanSoDo = useMemo(
    () => annotationsAt(scene, buoc, annotationView, tuongTac.selected_id ?? null)
      .filter((a) => a.subject_ids.every((id) => isVisible(tuongTac, id, coMatNhan))),
    [scene, buoc, annotationView, tuongTac, coMatNhan],
  );
  // Disclosure hides text and hit targets, while distance witnesses still use all certified entries.
  const nhanChu = useMemo(() => nhanSoDo.filter((a) => !annotationView.hiddenIds?.has(a.id)),
    [nhanSoDo, annotationView.hiddenIds]);
  const chonHienTai = useRef<string | null>(null);
  chonHienTai.current = tuongTac.selected_id ?? null;
  useEffect(() => {
    // Điểm neo THẾ GIỚI + độ dời trình bày của chủ thể (tách khối), đọc trong vòng vẽ qua ref.
    const m = new Map<string, THREE.Vector3>();
    for (const a of nhanChu) {
      const p = annotationAnchor(scene, a);
      if (!p) continue;
      const doi = a.subject_ids.map((id) => visualTransformOf(tuongTac, scene, id).translate);
      const tb = [0, 1, 2].map((i) => doi.reduce((s, t) => s + t[i], 0) / doi.length);
      m.set(a.id, new THREE.Vector3(p[0] + tb[0], p[1] + tb[1], p[2] + tb[2]));
    }
    viTriSoDo.current = m;
  }, [scene, nhanChu, tuongTac]);
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
  const nhanMpRef = useRef<HTMLDivElement>(null);
  const viTriMatPhang = useRef(new Map<string, THREE.Vector3>());
  //: W17 · nhãn SỐ ĐO: lớp DOM thứ hai, cùng vòng chiếu — đặt SAU nhãn điểm để tránh chúng.
  const soDoRef = useRef<HTMLDivElement>(null);
  const viTriSoDo = useRef(new Map<string, THREE.Vector3>());
  /** §16.7: nhóm nhân chứng — ngoài nhóm gốc, nên đổi bước/đổi lựa chọn không dựng lại nó và nó không
   *  dựng lại hình; chỉ đổi khi danh sách nhãn khoảng cách đang hiện đổi. */
  const nhanChungRef = useRef<THREE.Group | null>(null);
  /** W2 · F: nhóm lưới nền — ngoài nhóm gốc như nhân chứng: không dựng lại hình, không vào occlusion/raycast. */
  const luoiRef = useRef<THREE.Group | null>(null);

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
    /* ─── TRỤC LÊN LÀ Z, VÀ PHẢI ĐẶT TRƯỚC `OrbitControls` ─────────────────
     *
     * Toạ độ bài toán dùng **z làm chiều cao** (S(0;0;6), trục trụ O→K theo z),
     * còn mặc định của three.js là `up = (0,1,0)`. Để nguyên mặc định thì quỹ
     * đạo quay bám trục Y: hình vẫn xoay tự do và trục vẫn CỐ ĐỊNH tuyệt đối
     * (đo được ‖trục‖ = 1,000), nhưng nó xoay quanh một trục **không phải
     * chiều cao của bài** — nên người học không bao giờ nhìn được khối từ trên
     * xuống hay từ dưới lên. Đo trên ba ca: `cos` giữa hướng nhìn và trục z
     * chỉ chạy trong [−0,35; 0,00], không bao giờ tới gần ±1. Sau dòng này nó
     * chạm đúng ±1,000.
     *
     * ⚠️ **Thứ tự là toàn bộ vấn đề, không phải giá trị.** `OrbitControls`
     * chụp `camera.up` NGAY TRONG CONSTRUCTOR để dựng quaternion đưa trục ấy
     * về Y nội bộ. Đặt `cam.up` SAU khi tạo controls thì controls vẫn tin trục
     * quỹ đạo là Y trong khi camera dựng khung theo Z — hợp của hai phép quay
     * quanh hai trục không trùng nhau là một phép quay có **trục đổi theo từng
     * khung**. Đó chính là con bọ `56350f7`: đo được ‖trục‖ 0,59–0,66, và trên
     * màn hình nó đọc ra như hình bị lộn nhào.
     *
     * Nên dòng này phải đứng trước `new OrbitControls(...)` bên dưới. Khoá bởi
     * `scene3d-zup-lifecycle.test.tsx`, kiểm bằng HÀNH VI (dựng controls thật
     * rồi hỏi `getPolarAngle`) và bằng **AST** của chính tệp này, không bằng
     * phép tìm chuỗi.
     */
    cam.up.set(0, 0, 1);
    cam.position.set(8, 3, 6);
    scene3.add(new THREE.AmbientLight(MAU.light, PHONG_CACH_SCENE3D.light.ambient));
    const den = new THREE.DirectionalLight(MAU.light, PHONG_CACH_SCENE3D.light.directional);
    den.position.set(5, 10, 7);
    scene3.add(den);
    const goc = new THREE.Group();
    scene3.add(goc);
    rootRef.current = goc;
    const nhanChung = new THREE.Group();
    scene3.add(nhanChung);
    nhanChungRef.current = nhanChung;
    const luoi = new THREE.Group();
    scene3.add(luoi);
    luoiRef.current = luoi;
    const netDay = new THREE.Group();
    netDay.name = "net_day_man_hinh";
    scene3.add(netDay);

    const dieuKhien = new OrbitControls(cam, renderer.domElement);
    dieuKhien.enableDamping = true;
    dieuKhien.minAzimuthAngle = -Infinity;
    dieuKhien.maxAzimuthAngle = Infinity;
    dieuKhien.minPolarAngle = 0.005;
    dieuKhien.maxPolarAngle = Math.PI - 0.005;
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
    // W4: khung đổi cỡ KHÔNG qua sự kiện cửa sổ (chiều cao canvas theo `--geo3d-cao-khung` đo lại khi trang ổn định)
    // ⇒ theo dõi chính khung chứa, không thì <canvas> giữ cỡ cũ và tràn khỏi khung (đo mobile W4: 503 px trong 456).
    const roKhung = typeof ResizeObserver !== "undefined" ? new ResizeObserver(chinhCo) : null;
    roKhung?.observe(container);

    // ── CHỌN BẰNG CHUỘT ──────────────────────────────────────────────────
    //
    // `pointerup`, không `pointerdown`: OrbitControls dùng kéo-thả để xoay
    // cảnh, và bắt ở `down` thì mỗi lần xoay cũng là một lần chọn. Chỉ tính
    // là bấm khi con trỏ gần như không di chuyển giữa hai mốc.
    let batDau: [number, number] | null = null;
    const NGUONG_KEO = 4;
    const xuongTay = (e: PointerEvent) => {
      batDau = [e.clientX, e.clientY];
      setHoveredSection(null);
    };
    const vatTaiConTro = (e: PointerEvent, chiThietDien = false) => {
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
        // Lớp chiều sâu là bản sao VÔ HÌNH của khối; để nó bắt chuột thì một
        // cú bấm vào cạnh sẽ trúng khối trước, và phép chọn đổi hành vi vì
        // một chi tiết trình bày.
        .filter((h) => !h.object.userData?.chieuSau)
        .map((h) => pickSemanticId(h.object))
        .filter((x): x is string => typeof x === "string" && x.length > 0);
      return chiThietDien ? ids.find((id) => {
        const object = sceneRef.current.objects.find((o) => o.id === id);
        return object && vaiTroMien(object) === "section";
      }) ?? null : chonCuThe(ids, (id) => loaiRef.current.get(id));
    };
    const nhacTay = (e: PointerEvent) => {
      const d0 = batDau;
      batDau = null;
      if (!d0 || !chonRef.current) return;
      if (Math.hypot(e.clientX - d0[0], e.clientY - d0[1]) > NGUONG_KEO) return;
      chonRef.current(vatTaiConTro(e));
    };
    const roiConTro = () => setHoveredSection(null);
    const diConTro = (e: PointerEvent) => {
      if (e.pointerType === "touch" || e.buttons || batDau) return;
      const id = vatTaiConTro(e, true);
      const object = sceneRef.current.objects.find((o) => o.id === id);
      setHoveredSection(object && vaiTroMien(object) === "section" ? id : null);
    };
    renderer.domElement.addEventListener("pointerdown", xuongTay);
    renderer.domElement.addEventListener("pointerup", nhacTay);
    renderer.domElement.addEventListener("pointermove", diConTro);
    renderer.domElement.addEventListener("pointerleave", roiConTro);

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
      const gocVuongNodes: THREE.Object3D[] = [...(nhanChungRef.current?.children ?? [])];
      goc.traverse((node) => {
        if (node.userData?.perpMarker) gocVuongNodes.push(node);
      });
      const gocVuongPts = gocVuongNodes.flatMap((child) => {
        const ud = child.userData as { foot?: Vec3; corner?: Vec3; from?: Vec3 } | undefined;
        if (!ud?.foot || !ud?.corner) return [];
        const f3 = new THREE.Vector3(...ud.foot).applyQuaternion(qRef.current).project(cam);
        const c3 = new THREE.Vector3(...ud.corner).applyQuaternion(qRef.current).project(cam);
        const t3 = ud.from ? new THREE.Vector3(...ud.from).applyQuaternion(qRef.current).project(cam) : null;
        if (!(f3.z < 1) || !(c3.z < 1)) return [];
        return [{
          fx: ((f3.x + 1) / 2) * w, fy: ((1 - f3.y) / 2) * h,
          cx: ((c3.x + 1) / 2) * w, cy: ((1 - c3.y) / 2) * h,
          ...(t3 && t3.z < 1 ? { tx: ((t3.x + 1) / 2) * w, ty: ((1 - t3.y) / 2) * h } : {}),
        }];
      });
      const canh2d: { ax: number; ay: number; bx: number; by: number }[] = [];
      const chieuDoan3 = (a3: THREE.Vector3, b3: THREE.Vector3, matW: THREE.Matrix4) => {
        const pa = a3.clone().applyMatrix4(matW).project(cam);
        const pb = b3.clone().applyMatrix4(matW).project(cam);
        if (pa.z < 1 && pb.z < 1) {
          canh2d.push({
            ax: ((pa.x + 1) / 2) * w,
            ay: ((1 - pa.y) / 2) * h,
            bx: ((pb.x + 1) / 2) * w,
            by: ((1 - pb.y) / 2) * h,
          });
        }
      };
      goc.updateMatrixWorld(true);
      goc.traverse((node) => {
        if (!node.visible) return;
        const ce = node.userData?.canonicalEdge as { a: THREE.Vector3; b: THREE.Vector3 } | undefined;
        if (ce) {
          chieuDoan3(ce.a, ce.b, node.matrixWorld);
          return;
        }
        const seg = node.userData?.nonCanonicalSegment as { a: THREE.Vector3; b: THREE.Vector3 } | undefined;
        if (seg) {
          chieuDoan3(seg.a, seg.b, node.matrixWorld);
          return;
        }
        const loop = node.userData?.nonCanonicalLoop as { pts: THREE.Vector3[]; closed: boolean; isPlaneBorder?: boolean } | undefined;
        if (loop && !loop.isPlaneBorder && loop.pts.length >= 2) {
          const n = loop.closed ? loop.pts.length : loop.pts.length - 1;
          for (let i = 0; i < n; i += 1) {
            chieuDoan3(loop.pts[i], loop.pts[(i + 1) % loop.pts.length], node.matrixWorld);
          }
        }
      });

      const dat: { el: HTMLElement; id: string; x: number; y: number; lx: number; ly: number; duoi?: boolean; uuTien: number; w: number; h: number }[] = [];
      // Cỡ hộp nhãn cho phép lọc chồng: ĐỌC hết trước khi GHI style nào — đọc xen giữa các lần ghi ép trình duyệt
      // tính lại bố cục cho từng nhãn ở mỗi khung (transform/opacity không đổi offsetWidth/Height).
      const co = new Map((Array.from(lop.children) as HTMLElement[]).map((el) => [el, [el.offsetWidth, el.offsetHeight]]));
      const ungVienDiem2d: { el: HTMLElement; id: string; x: number; y: number; w: number; h: number; uuTien: number }[] = [];
      for (const el of Array.from(lop.children) as HTMLElement[]) {
        const id = el.dataset.id;
        const v = id ? viTriNhan.current.get(id) : undefined;
        if (!v || !id) { el.style.opacity = "0"; continue; }
        const p3 = v.clone().applyQuaternion(qRef.current).project(cam);
        // Sau lưng camera ⇒ giấu. Không có phép kiểm này thì nhãn của mặt
        // khuất lộn ngược lên trước hình.
        const hien = p3.z < 1 && p3.x > -1.1 && p3.x < 1.1 && p3.y > -1.1 && p3.y < 1.1;
        if (!hien) { el.style.opacity = "0"; continue; }
        const x = ((p3.x + 1) / 2) * w;
        const y = ((1 - p3.y) / 2) * h;
        const [cw, ch] = co.get(el)!;
        ungVienDiem2d.push({ el, id, x, y, w: cw, h: ch, uuTien: Number(el.dataset.uuTien ?? "1") });
      }
      const viTriToiUu = tinhViTriNhanDiem(ungVienDiem2d, canh2d, gocVuongPts, huongNhanRef.current);
      for (const u of ungVienDiem2d) {
        const dich = viTriToiUu.get(u.id) ?? { x: u.x - (u.w || 18) / 2, y: u.y - 1.4 * (u.h || 18), duoi: false };
        const lech = lamMuotLechNhan(lechNhanRef.current.get(u.id), { dx: dich.x - u.x, dy: dich.y - u.y });
        lechNhanRef.current.set(u.id, lech);
        const pos = { x: u.x + lech.dx, y: u.y + lech.dy, duoi: dich.duoi };
        u.el.style.transform = `translate(${Math.round(pos.x)}px,${Math.round(pos.y)}px)`;
        dat.push({
          el: u.el,
          id: u.id,
          x: u.x,
          y: u.y,
          lx: pos.x,
          ly: pos.y,
          duoi: pos.duoi,
          uuTien: u.uuTien,
          w: u.w,
          h: u.h,
        });
      }
      const giu = locNhanChongNhau(dat);
      for (const d of dat) d.el.style.opacity = giu.has(d.id) ? "1" : "0";

      // ── W17 · NHÃN SỐ ĐO — đặt sau nhãn điểm, tránh chúng và các lớp phủ che khung ─────
      // Luật hộp nhãn (§15.5) ở hàm thuần `placeAnnotationLabels`; đây chỉ đo cỡ chữ và chiếu.
      const lopSo = soDoRef.current;
      if (!lopSo) return;
      const hopDiem = dat.filter((d) => giu.has(d.id)).map((d) => ({
        id: d.id, x: d.lx,
        y: d.ly,
        w: d.el.offsetWidth, h: d.el.offsetHeight,
      }));
      const chamDiem: LabelRect[] = dat.filter((d) => giu.has(d.id)).map((d) => ({
        x: d.x - 7, y: d.y - 7, w: 14, h: 14,
      }));
      const gocVuongRects: LabelRect[] = gocVuongPts.flatMap((g) => {
        const ra: LabelRect[] = [
          { x: g.fx - 8, y: g.fy - 8, w: 16, h: 16 },
          { x: g.cx - 8, y: g.cy - 8, w: 16, h: 16 },
        ];
        if (g.tx !== undefined && g.ty !== undefined) {
          const dx = g.fx - g.tx, dy = g.fy - g.ty, d = Math.hypot(dx, dy);
          if (d > 24) {
            const mx = (g.fx + g.tx) / 2, my = (g.fy + g.ty) / 2;
            const ux = (dx / d) * 10, uy = (dy / d) * 10;
            ra.push({ x: mx + ux - 2, y: my + uy - 2, w: 4, h: 4 }, { x: mx - ux - 2, y: my - uy - 2, w: 4, h: 4 });
          }
        }
        return ra;
      });
      const canDat: LabelToPlace[] = [];
      const theTheoId = new Map<string, HTMLElement>();
      for (const el of Array.from(lopSo.children) as HTMLElement[]) {
        const id = el.dataset.annId;
        const v = id ? viTriSoDo.current.get(id) : undefined;
        const p3 = v?.clone().applyQuaternion(qRef.current).project(cam);
        if (!id || !p3 || !(p3.z < 1)) { el.style.opacity = "0"; continue; }
        canDat.push({ id, ax: ((p3.x + 1) / 2) * w, ay: ((1 - p3.y) / 2) * h,
          w: el.offsetWidth, h: el.offsetHeight, priority: Number(el.dataset.uuTien ?? "1") });
        theTheoId.set(id, el);
      }
      const vungChe = vungCheKhung(renderer.domElement.getBoundingClientRect());
      const daDat = placeAnnotationLabels(canDat,
        [...hopDiem, ...chamDiem, ...gocVuongRects, ...vungChe], { w, h });
      for (const c of canDat) {
        if (!daDat.has(c.id)) {
          const r2 = placeAnnotationLabels([c], [...hopDiem, ...chamDiem, ...vungChe, ...daDat.values()], { w, h }).get(c.id)
            ?? placeAnnotationLabels([c], [...hopDiem, ...vungChe, ...daDat.values()], { w, h }).get(c.id);
          if (r2) daDat.set(c.id, r2);
        }
      }
      const hopSo: { id: string; box: LabelRect; anchor: { x: number; y: number } }[] = [];
      for (const c of canDat) {
        const el = theTheoId.get(c.id)!;
        const r = daDat.get(c.id);
        el.style.opacity = r ? "1" : "0";
        // W2 · A: nhãn HỢP LỆ ở bước này nhưng thiếu chỗ — khác nhãn chưa hợp lệ (không có trong lớp này). Giá
        // trị vẫn ở ngăn «Đại lượng» và ô soi.
        el.dataset.thieuCho = r ? "" : "1";
        // Nhãn chưa đặt được thì không bắt chuột, không nhận Tab — giá trị vẫn ở ô soi và lời giải.
        el.style.pointerEvents = r ? "auto" : "none";
        el.tabIndex = r ? 0 : -1;
        if (!r) continue;
        el.style.transform = `translate(${r.x}px,${r.y}px)`;
        hopSo.push({ id: c.id, box: r, anchor: { x: c.ax, y: c.ay } });
      }
      // ── NHÃN KÝ HIỆU MẶT PHẲNG (`.geo3d-nhan-mp`) — đặt ở diềm mở rộng của mặt phẳng, tránh nhãn điểm & số đo ──
      const lopMp = nhanMpRef.current;
      const hopMatPhang: { id: string; box: LabelRect; anchor: { x: number; y: number } }[] = [];
      if (lopMp) {
        const canDatMp: LabelToPlace[] = [];
        const theMpTheoId = new Map<string, HTMLElement>();
        for (const el of Array.from(lopMp.children) as HTMLElement[]) {
          const id = el.dataset.planeId;
          const v = id ? viTriMatPhang.current.get(id) : undefined;
          const p3 = v?.clone().applyQuaternion(qRef.current).project(cam);
          if (!id || !p3 || !(p3.z < 1) || p3.x <= -1.08 || p3.x >= 1.08 || p3.y <= -1.08 || p3.y >= 1.08) {
            el.style.opacity = "0";
            continue;
          }
          canDatMp.push({
            id,
            ax: ((p3.x + 1) / 2) * w,
            ay: ((1 - p3.y) / 2) * h,
            w: el.offsetWidth || 44,
            h: el.offsetHeight || 20,
            priority: Number(el.dataset.uuTien ?? "1"),
          });
          theMpTheoId.set(id, el);
        }
        const vatCanMp: LabelRect[] = [
          ...hopDiem,
          ...chamDiem,
          ...gocVuongRects,
          ...vungChe,
          ...hopSo.map((x) => x.box),
        ];
        const daDatMp = placeAnnotationLabels(canDatMp, vatCanMp, { w, h });
        for (const c of canDatMp) {
          const el = theMpTheoId.get(c.id)!;
          const r = daDatMp.get(c.id);
          el.style.opacity = r ? "1" : "0";
          if (!r) continue;
          el.style.transform = `translate(${r.x}px,${r.y}px)`;
          hopMatPhang.push({ id: c.id, box: r, anchor: { x: c.ax, y: c.ay } });
        }
      }
      if (typeof window !== "undefined") {
        // Móc ĐO của bộ kiểm trình duyệt (§15.5): hộp nhãn số đo đang hiện + hộp nhãn điểm đang hiện.
        (window as any).__geo3d_annotation_boxes = hopSo;
        // W2 · A: nhãn hợp lệ ở bước này mà không đặt được vì thiếu chỗ.
        (window as any).__geo3d_annotation_unplaced = canDat.filter((c) => !daDat.has(c.id)).map((c) => c.id);
        (window as any).__geo3d_point_label_boxes = hopDiem;
        (window as any).__geo3d_plane_label_boxes = hopMatPhang;
      }
    };

    let song = true;
    const vong = () => {
      if (!song) return;
      const truocPos = cam.position.clone();
      const truocQuat = cam.quaternion.clone();
      if (!dieuKhien.update()) {
        cam.position.copy(truocPos);
        cam.quaternion.copy(truocQuat);
      }
      cam.updateMatrixWorld();
      const wCss = renderer.domElement.clientWidth || 1;
      const hCss = renderer.domElement.clientHeight || 1;
      datCoDauDinh(goc, cam, wCss, hCss);
      datCoDauDinh(nhanChung, cam, wCss, hCss);
      const edgeAudit = updateCanonicalEdgeVisibility(
        goc,
        cam,
        `${renderer.domElement.clientWidth}x${renderer.domElement.clientHeight}`
          + `@${renderer.getPixelRatio()}`,
      );
      if (typeof window !== "undefined") {
        (window as any).__geo3d_visible_edge_ids = edgeAudit.visible_edge_ids;
        (window as any).__geo3d_hidden_edge_ids = edgeAudit.hidden_edge_ids;
        (window as any).__geo3d_mixed_edge_ids = edgeAudit.mixed_edge_ids;
        (window as any).__geo3d_duplicate_visual_owner_ids =
          edgeAudit.duplicate_visual_owner_ids;
        (window as any).__geo3d_edge_spans = edgeAudit.edge_spans;
        // Tâm quỹ đạo: bộ đo mô phỏng đúng camera SAU cử chỉ xoay/lùi (w11).
        (window as any).__geo3d_camera_target = dieuKhien.target.toArray();
        // exact-dimensions: cảnh có metric khung ⇒ toạ độ PAYLOAD (khung) → thế giới = xoay hiển thị · T (`scene3d-chart`).
        const khungT = tRef.current;
        const coXoay = !qRef.current.equals(DONG_NHAT) || khungT !== null;
        const model = khungT ? new THREE.Matrix4().fromArray(khungT).premultiply(goc.matrixWorld) : goc.matrixWorld;
        (window as any).__geo3d_camera_snapshot = {
          position: cam.position.toArray(),
          // Bộ đo chiếu TOẠ ĐỘ PAYLOAD: khi có xoay hiển thị (đáy nghiêng, §18.2) hay metric khung, ma trận phát là
          // view × model để phép chiếu của bộ đo trùng hình trên khung. Không có cả hai ⇒ đúng ma trận view như trước.
          view_matrix_column_major: [...(coXoay
            ? new THREE.Matrix4().multiplyMatrices(cam.matrixWorldInverse, model)
            : cam.matrixWorldInverse).elements],
          // Payload → thế giới: bộ đo mô phỏng cử chỉ quỹ đạo trong khung THẾ GIỚI (`cameraSauCuChi`).
          ...(coXoay ? { model_matrix_column_major: [...model.elements] } : {}),
          projection_matrix_column_major: [...cam.projectionMatrix.elements],
          viewport_width: renderer.domElement.clientWidth,
          viewport_height: renderer.domElement.clientHeight,
          device_pixel_ratio: renderer.getPixelRatio(),
        };
        (window as any).__geo3d_highlighted_render_owner_ids =
          edgeAudit.highlighted_render_owner_ids;
        const dashSignature: Record<string, string[]> = {};
        goc.traverse((node) => {
          const ownerId = node.userData?.visualOwnerId as string | undefined;
          if (!ownerId || !(node as THREE.Group).isGroup) return;
          dashSignature[ownerId] = node.children.map((child) =>
            child.userData?.hidden === true ? "HIDDEN_DASHED" : "VISIBLE_SOLID");
        });
        (window as any).__geo3d_edge_dash_signature = dashSignature;
        // Chấm đỉnh cho bộ đo (w11): tâm + bán kính THẾ GIỚI; bộ đo tự chiếu
        // bằng ma trận camera để kiểm cỡ px — không tin con số renderer tự báo.
        const cham: { id: string | null; state: string; center: number[]; radius_world: number }[] = [];
        const tam = new THREE.Vector3();
        const ti = new THREE.Vector3();
        goc.traverse((node) => {
          if (!node.userData?.dauDinh) return;
          node.getWorldPosition(tam);
          // Toạ độ CẢNH như mọi đầu vào khác của bộ đo (ma trận phát ở trên là cảnh → camera khi có xoay).
          if (coXoay) goc.worldToLocal(tam);
          if (khungT) tam.applyMatrix4(new THREE.Matrix4().fromArray(khungT).invert());   // → toạ độ khung
          node.getWorldScale(ti);
          cham.push({ id: pickSemanticId(node), state: node.userData.dauDinh, center: tam.toArray(),
            radius_world: ((node as THREE.Mesh).geometry as THREE.SphereGeometry).parameters.radius * ti.x });
        });
        (window as any).__geo3d_vertex_markers = cham;
        const perf = goc.userData.occlusionPerformance ?? {
          frame_count: 0, recompute_count: 0, recomputation_times_ms: [],
          edge_count: 0, triangle_count: 0, sample_count: 0, span_count: 0,
        };
        perf.frame_count += 1;
        perf.recompute_count += edgeAudit.recomputed_solid_count;
        if (edgeAudit.recomputed_solid_count > 0) {
          perf.recomputation_times_ms.push(edgeAudit.recomputation_ms);
        }
        perf.edge_count = edgeAudit.edge_count;
        perf.triangle_count = edgeAudit.triangle_count;
        perf.sample_count = edgeAudit.sample_count;
        perf.span_count = edgeAudit.span_count;
        goc.userData.occlusionPerformance = perf;
        (window as any).__geo3d_occlusion_performance = { ...perf };
        (window as any).__geo3d_reset_occlusion_performance = () => {
          goc.userData.occlusionPerformance = {
            frame_count: 0, recompute_count: 0, recomputation_times_ms: [],
            edge_count: 0, triangle_count: 0, sample_count: 0, span_count: 0,
          };
        };
      }
      warmSpanPools(goc, scene3, cam, renderer);
      datCoGocVuong([goc, nhanChung], cam, hCss, dieuKhien.target);
      const fatSummary = dongBoNetDayManHinh([goc, nhanChung], netDay, wCss, hCss);
      if (typeof window !== "undefined") {
        (window as any).__geo3d_fat_line_summary = {
          totalLines: fatSummary.totalLines,
          maxSectionBorderWidth: fatSummary.maxSectionBorderWidth,
          maxVisibleEdgeWidth: fatSummary.maxVisibleEdgeWidth,
          minHiddenEdgeWidth: fatSummary.minHiddenEdgeWidth,
        };
      }
      for (const l of fatSummary.sourceLines) l.visible = false;
      renderer.render(scene3, cam);
      for (const l of fatSummary.sourceLines) l.visible = true;
      chieuNhan();
      requestAnimationFrame(vong);
    };
    veRef.current = () => {
      cam.updateMatrixWorld();
      const wCss = renderer.domElement.clientWidth || 1;
      const hCss = renderer.domElement.clientHeight || 1;
      datCoDauDinh(goc, cam, wCss, hCss);
      datCoDauDinh(nhanChung, cam, wCss, hCss);
      updateCanonicalEdgeVisibility(
        goc,
        cam,
        `${renderer.domElement.clientWidth}x${renderer.domElement.clientHeight}`
          + `@${renderer.getPixelRatio()}`,
      );
      warmSpanPools(goc, scene3, cam, renderer);
      datCoGocVuong([goc, nhanChung], cam, hCss, dieuKhien.target);
      const fatSummary = dongBoNetDayManHinh([goc, nhanChung], netDay, wCss, hCss);
      for (const l of fatSummary.sourceLines) l.visible = false;
      renderer.render(scene3, cam);
      for (const l of fatSummary.sourceLines) l.visible = true;
    };
    // Móc ĐO của cổng ảnh `SECTION_FILL_DISTINGUISHABLE` — chỉ harness gọi, người học không
    // thấy (mặc định bật). Tắt/bật phần tô rồi vẽ lại ĐÚNG khung hình này; trả tên các vật
    // đã chạm — rỗng thì không có gì để đo, cổng phải tự đỏ.
    (window as any).__geo3d_set_section_fill_visible = (on: boolean) => {
      const ten = datHienToThietDien(goc, on);
      const wCss = renderer.domElement.clientWidth || 1;
      const hCss = renderer.domElement.clientHeight || 1;
      datCoGocVuong([goc, nhanChung], cam, hCss, dieuKhien.target);
      const fatSummary = dongBoNetDayManHinh([goc, nhanChung], netDay, wCss, hCss);
      for (const l of fatSummary.sourceLines) l.visible = false;
      renderer.render(scene3, cam);
      for (const l of fatSummary.sourceLines) l.visible = true;
      return ten;
    };

    const tinhTuyChonKhung = (diem: Vec3[], huong: [number, number, number], w: number, _h: number) => {
      const tiLeCR = tiLeHinhChieu(diem, huong) ?? 1;
      const dsVat = sceneRef.current.objects;
      const coMatCat = dsVat.some(
        (o) => o.type === "plane3" || o.type === "section" || o.type === "circle3" || o.type === "ellipse3",
      );
      const cRect = container.getBoundingClientRect();
      const panelEl = typeof document !== "undefined" ? document.getElementById("geo3d-bang-phan-tich") : null;
      const pRect = panelEl?.getBoundingClientRect();
      const coPanelPhai = Boolean(
        pRect && pRect.width > 0 && cRect.width > 0 && pRect.left < cRect.right && pRect.left > cRect.left,
      );
      const safeLeft = cRect.left + 24;
      const safeRight = coPanelPhai ? Math.max(cRect.left + w * 0.36, pRect!.left - 28) : cRect.right - 24;
      const safeWidthRatio = cRect.width > 0
        ? Math.max(0.32, Math.min(1, (safeRight - safeLeft) / Math.max(1, w)))
        : 1;
      const safeCenterX = (safeLeft + safeRight) / 2;
      const dichTamNgang = coPanelPhai && cRect.width > 0
        ? (safeCenterX - (cRect.left + w / 2)) / Math.max(1, w / 2)
        : 0;
      let tiLeDoc = 0.67;
      if (tiLeCR > 1.15) tiLeDoc = 0.64;
      if (coMatCat) tiLeDoc = Math.min(tiLeDoc, 0.65);
      if (w < 900) tiLeDoc = Math.min(tiLeDoc, 0.58);
      if (coPanelPhai) tiLeDoc = Math.min(tiLeDoc, 0.62);
      const tiLeNgang = coPanelPhai
        ? Math.min(0.58, safeWidthRatio * 0.78)
        : Math.min(0.72, tiLeDoc * 1.12);
      return {
        tiLeDoc,
        tiLeNgang,
        dichTamNgang,
        dichTamDoc: 0.02,
      };
    };

    const datLaiVungAnToan = () => {
      const diem = diemVuaKhung(goc, diemHuuHan(sceneRef.current.objects).map((p) => xoay(p, qRef.current)));
      if (diem.length === 0) return;
      chinhCo();
      const w = renderer.domElement.clientWidth || 1;
      const h = renderer.domElement.clientHeight || 1;
      const vHuong = cam.position.clone().sub(dieuKhien.target);
      const dLen = vHuong.length() || 1;
      const huongHienTai: [number, number, number] = [vHuong.x / dLen, vHuong.y / dLen, vHuong.z / dLen];
      const kn = khungNhinSuPham(
        diem, [], [], cam.fov, w / h, huongHienTai, tinhTuyChonKhung(diem, huongHienTai, w, h),
      );
      if (!kn) return;
      datKhungNhin(cam, dieuKhien, kn);
      veRef.current?.();
      chieuNhan();
    };

    const sanKhau = container.closest(".geo3d-san") ?? container.parentElement;
    let trangThaiPanelTruoc = Boolean(
      typeof document !== "undefined" && document.getElementById("geo3d-bang-phan-tich"),
    );
    const moPanel = typeof MutationObserver !== "undefined" && sanKhau
      ? new MutationObserver(() => {
          const hienTaiPanel = Boolean(document.getElementById("geo3d-bang-phan-tich"));
          if (hienTaiPanel !== trangThaiPanelTruoc) {
            trangThaiPanelTruoc = hienTaiPanel;
            datLaiVungAnToan();
          }
        })
      : null;
    if (moPanel && sanKhau) {
      moPanel.observe(sanKhau, { childList: true, subtree: true });
    }

    // ── ĐẶT KHUNG NHÌN CHO VỪA HÌNH ────────────────────────────────────
    //
    // Đọc hộp bao của những gì ĐANG dựng trong nhóm gốc, không đọc `scene` —
    // ẩn/cô lập/tách khối đều đã phản ánh vào nhóm, nên một nguồn là đủ.
    vuaKhungRef.current = () => {
      const dsVat = sceneRef.current.objects;
      const diem = diemVuaKhung(goc, diemHuuHan(dsVat).map((p) => xoay(p, qRef.current)));
      if (diem.length === 0) return;
      chinhCo();
      const w = renderer.domElement.clientWidth || 1;
      const h = renderer.domElement.clientHeight || 1;
      const ct = cauTrucTheGioi(dsVat, qRef.current);
      const huong = ct.canh.length > 0
        ? chonHuongNhin(ct.diem, ct.canh, ct.mat)
        : ([8, 5, 6] as [number, number, number]);
      const kn = khungNhinSuPham(diem, [], [], cam.fov, w / h, huong, tinhTuyChonKhung(diem, huong, w, h))
        ?? khungNhinVua(hopBaoCuaDiem(diem), cam.fov, w / h);
      if (!kn) return;   // đầu vào không dùng được ⇒ giữ nguyên khung nhìn
      datKhungNhin(cam, dieuKhien, kn);
      veRef.current?.();
      chieuNhan();
    };

    vong();

    return () => {
      song = false;
      renderer.domElement.removeEventListener("pointerdown", xuongTay);
      renderer.domElement.removeEventListener("pointerup", nhacTay);
      renderer.domElement.removeEventListener("pointermove", diConTro);
      renderer.domElement.removeEventListener("pointerleave", roiConTro);
      window.removeEventListener("resize", chinhCo);
      roKhung?.disconnect();
      moPanel?.disconnect();
      dieuKhien.dispose();
      const warmHold = scene3.userData.warmHoldGroup as THREE.Group | undefined;
      warmHold?.traverse((x) => {
        const l = x as THREE.Line;
        l.geometry?.dispose?.();
        (l.material as THREE.Material | undefined)?.dispose?.();
      });
      for (const group of [goc, nhanChung, luoi, netDay]) disposeScene3DObject(group);
      renderer.dispose();
      container.removeChild(renderer.domElement);
      rootRef.current = null;
      nhanChungRef.current = null;
      luoiRef.current = null;
      veRef.current = null;
      vuaKhungRef.current = null;
      delete (window as any).__geo3d_set_section_fill_visible;
    };
  }, []);

  // §16.7 — nhân chứng của các nhãn khoảng cách ĐANG HIỆN (chọn, hoặc "Hiện tất cả"): đoạn tới chân
  // + ký hiệu vuông góc. Không thêm bước dựng, không chạm nhóm gốc, nét đứt hay camera.
  useEffect(() => {
    const nhom = nhanChungRef.current;
    if (!nhom) return;
    for (const con of [...nhom.children]) {
      nhom.remove(con);
      con.traverse((x) => {
        const m = x as THREE.Line | THREE.Mesh;
        m.geometry?.dispose?.();
        (m.material as THREE.Material | undefined)?.dispose?.();
      });
    }
    // Review I1: cộng đoạn vuông góc PHỤ của điểm hình chiếu đã có mặt ở bước này — cùng cách vẽ, chân do backend phát.
    const diemToanCanh = diemHuuHan(scene.objects);
    // Mặt phẳng "chỉ để đo" (`measurementOnlyPlanes`: mặt của chính khối, ẩn khỏi khung vì đã có trên hình) vẫn là chủ
    // thể HIỆN của nhân chứng: SA ⊥ (ABCD), BC ⊥ (SAB) đặt dấu trên mặt khối đang thấy. Ẩn/cô lập của người xem vẫn áp.
    const mpDo = measurementOnlyPlanes(scene);
    const coMatNhanChung = new Set([...coMatNhan,
      ...objectsAt(scene, buoc).filter((o) => mpDo.has(o.id)).map((o) => o.id)]);
    const hienNhanChung = new Set([...coMatNhanChung].filter((id) => isVisible(tuongTac, id, coMatNhanChung)));
    const tuSoDo = witnessesShown(scene, nhanSoDo);
    const daCoSoDo = new Set(tuSoDo.map((w) => w.id));
    const tuChieu = projectionWitnessesAt(scene, hienNhanChung, !tang ? buoc : undefined)
      .filter((w) => !daCoSoDo.has(w.id.slice("perpendicular:".length)));
    // Chế độ A không lộ đáp số: dấu vuông góc của một GÓC đo được CHÍNH LÀ đáp số (90°), nên ẩn cùng nhãn của nó.
    // Nhân chứng khoảng cách thì không — chân đường vuông góc là cách dựng, không phải con số.
    const laDapSoAn = (id: string) => annotationView.hiddenIds?.has(id) === true
      && scene.objects.some((o) => o.id === id && o.annotation?.kind === "angle");
    const ds = [...tuSoDo, ...tuChieu]
      .filter((w) => !laDapSoAn(w.vai === "hinh_chieu" ? w.id.slice("perpendicular:".length) : w.id));
    const doanCo = doanDaVe(scene.objects);
    const diemCoTen = objectsAt(scene, buoc).flatMap((o) => (o.type === "point3" && o.xyz ? [toVec3(o.xyz)] : []));
    for (const w of ds) {
      const chuId = w.vai === "hinh_chieu" ? w.id.slice("perpendicular:".length) : w.id;
      const t = tang?.get(chuId);
      const dangDungDiem = !tang && tapNoiBat.has(chuId) && loaiRef.current.get(chuId) === "point3";
      const mau = t && t !== "boi_canh" ? MAU_TANG[t] : (dangDungDiem ? MAU.highlight : undefined);
      const diu = Boolean(tang && !t);
      nhom.add(vatNhanChung(w, diemToanCanh, mau, diu, doanCo, diemCoTen));
    }
    if (typeof window !== "undefined") (window as any).__geo3d_witness_ids = ds.map((w) => w.id);
    veRef.current?.();
  }, [scene, buoc, nhanSoDo, coMatNhan, tuongTac, tang, tapNoiBat, annotationView.hiddenIds]);

  const heSoDiuLuoi = useMemo(() => {
    const daTonTai = entitiesPresentAt(scene, buoc, objectsAt);
    const matPhangHien = scene.objects.filter(
      (o) => o.type === "plane3" && daTonTai.has(o.id) && isVisible(tuongTac, o.id, daTonTai) && !anPhu.has(o.id),
    );
    if (matPhangHien.length === 0) return 1;
    const coMpNgang = matPhangHien.some((o) => {
      if (!o.normal) return false;
      const n = xoay(toVec3(o.normal), qHienThi);
      return Math.hypot(n[0], n[1]) <= 1e-4 * Math.abs(n[2]);
    });
    if (coMpNgang) return 0.38;
    const dangNhanMp = matPhangHien.some(
      (o) => tuongTac.selected_id === o.id || tapNoiBat.has(o.id) || (tang?.has(o.id) && tang.get(o.id) !== "boi_canh"),
    );
    return dangNhanMp ? 0.55 : 0.78;
  }, [scene, buoc, tuongTac, anPhu, qHienThi, tapNoiBat, tang]);

  // W2 · F — LƯỚI NỀN tuỳ chọn: mảnh, nhạt, nằm dưới đáy hình (mặt z thấp nhất của cảnh), ô theo cỡ cảnh — không
  // số toạ độ, không đơn vị. Bật/tắt chỉ thêm/bớt nhóm này rồi vẽ lại một khung: camera, bước, lựa chọn không đổi.
  useEffect(() => {
    const nhom = luoiRef.current;
    if (!nhom) return;
    for (const con of [...nhom.children]) {
      nhom.remove(con);
      con.traverse((x) => {
        const l = x as THREE.LineSegments;
        l.geometry?.dispose?.();
        (l.material as THREE.Material | undefined)?.dispose?.();
      });
    }
    // Lưới nằm dưới hình NGƯỜI HỌC THẤY: lấy toạ độ sau phép xoay hiển thị (nhóm lưới không xoay).
    const diem = diemHuuHan(scene.objects).map((p) => xoay(p, qHienThi));
    if (gridShown && diem.length > 0) {
      nhom.add(dungLuoiNenSuPham(diem, heSoDiuLuoi));
    }
    if (typeof window !== "undefined") {
      (window as any).__geo3d_grid_visible = nhom.children.length > 0;
      (window as any).__geo3d_grid_subordinated = heSoDiuLuoi < 1;
    }
    veRef.current?.();
  }, [scene, gridShown, qHienThi, heSoDiuLuoi]);

  // §16.5 — nhãn số đo BẤM ĐƯỢC (chuột, Enter/Space): bấm là chọn đại lượng, bấm lại là bỏ chọn.
  // Listener gắn bằng lệnh (lớp này không dùng prop sự kiện trong JSX — khoá ở `scene3d.test.tsx`).
  useEffect(() => {
    const lop = soDoRef.current;
    if (!lop) return;
    const chonNhan = (e: Event) => {
      const id = (e.target as HTMLElement | null)?.closest<HTMLElement>("[data-ann-id]")?.dataset.annId;
      if (!id || !chonRef.current) return;
      if (e instanceof KeyboardEvent) {
        if (e.key !== "Enter" && e.key !== " ") return;
        e.preventDefault();
      }
      chonRef.current(chonHienTai.current === id ? null : id);
    };
    lop.addEventListener("click", chonNhan);
    lop.addEventListener("keydown", chonNhan);
    return () => {
      lop.removeEventListener("click", chonNhan);
      lop.removeEventListener("keydown", chonNhan);
    };
  }, [webglFailed]);

  // Đổi bước ⇒ dựng lại nội dung nhóm gốc. Rẻ vì cảnh nhỏ (≤ vài chục mesh).
  useEffect(() => {
    const goc = rootRef.current;
    if (!goc) return;
    goc.quaternion.copy(qHienThi);
    nhanChungRef.current?.quaternion.copy(qHienThi);
    goc.userData.spanPoolsWarmed = false;
    for (const con of [...goc.children]) {
      goc.remove(con);
      disposeScene3DObject(con);
    }
    viTriNhan.current.clear();
    viTriMatPhang.current.clear();
    const noiBat = tapNoiBat;
    // MỘT thẩm quyền "vật nào đang có mặt", dùng chung với cây phân rã.
    //
    // Bản trước hỏi thẳng `objectsAt` ở đây còn cây hỏi `entitiesPresentAt`.
    // Hai phép khác nhau: mặt và cạnh KHÔNG có sự kiện timeline riêng, nên
    // `objectsAt` bỏ chúng ra — cây liệt kê được mặt mà khung nhìn không dựng
    // mặt nào, và raycast chỉ còn trúng khối. Demo tay bắt đúng chuyện đó.
    const daTonTai = entitiesPresentAt(scene, buoc, objectsAt);
    const hienTai = scene.objects.filter((o) => daTonTai.has(o.id));
    const progressById = new Map(
      (scene.formation?.steps[buoc]?.geometry_progress ?? [])
        .map((progress) => [progress.object_id, progress]),
    );
    // Cạnh chuẩn tô QUA vật khác (đoạn/đáy trùng cạnh) mang màu tầng của vật ấy;
    // hai vật cùng trỏ một cạnh thì tầng mạnh hơn thắng. Ngữ cảnh cấu trúc
    // không tô cạnh nào — nét của nó giữ mực trung tính (w11).
    const tangCua = (id: string) => tang?.get(id);
    const mucMau = (id: string) => (tang
      ? MAU_TANG[(tangCua(id) ?? "trung_gian") as Exclude<TangNhanManh, "boi_canh">] : MAU.highlight);
    const doManh = (id: string) => ["trung_gian", "du_kien_so", "dich"].indexOf(tangCua(id) ?? "");
    const { ca: canonicalHighlights, khuc: khucToSang } = toSangCanhChuan(
      [...hienTai].sort((a, b) => doManh(a.id) - doManh(b.id)),
      (id) => noiBat.has(id) && tangCua(id) !== "boi_canh", mucMau);
    // Quan sát cho bằng chứng playback: vật nào THỰC SỰ được dựng lên khung ở
    // bước này (thiết diện đang hình thành kèm số cạnh đã hiện).
    const daDung: string[] = [];
    // ẨN / CÔ LẬP quyết định CÓ DỰNG HAY KHÔNG — không dựng rồi giấu, vì một
    // mesh vô hình vẫn nằm trên đường raycast và vẫn ăn cú bấm. Backend NÓI vật
    // nào không có hình trên khung (`render: "non_visual"`); phía này chỉ tuân.
    // W2 · D: hình phụ đã xong nhiệm vụ / mặt phẳng chỉ để đo — không dựng (dữ liệu, xuất xứ, timeline giữ nguyên).
    const seDung = hienTai.filter((o) => isVisible(tuongTac, o.id, daTonTai) && veTrenKhung(o) && !anPhu.has(o.id));
    /* Nền hình học để cắt mặt phẳng vô hạn: lấy từ vật ĐANG HIỆN, không từ cả
       cảnh. Bước 1 chưa có khối thì miếng mặt phẳng cũng chưa được phình ra
       ôm một khối chưa xuất hiện — mắt đọc đúng thứ tự dựng. */
    const diemNen = diemHuuHan(seDung);
    const coHinhCong = seDung.some((x) => x.render === "circle" || x.render === "ellipse" || x.render === "curved_solid");
    const idSeDung = new Set(seDung.map((o) => o.id));
    const khoaDich = (id: string) => visualTransformOf(tuongTac, scene, id).translate.join(",");
    const nhuong = doanNhuongCanh(seDung, khoaDich);
    const dsKhoiId = seDung.filter((x) => x.type === "solid" || x.type === "curved_solid").map((x) => x.id);
    const canhKhoiDaDung: { a: THREE.Vector3; b: THREE.Vector3; dich: string }[] = [];
    const canhThietDienDaDung: { a: THREE.Vector3; b: THREE.Vector3; dich: string }[] = [];
    for (const secObj of seDung) {
      if (secObj.type !== "section" || secObj.closed === false) continue;
      const progSec = progressById.get(secObj.id);
      if (progSec && !progSec.closed) continue;
      const ptsSec = (secObj.polygon ?? secObj.vertices ?? []).map((p) => new THREE.Vector3(...toVec3(p)));
      if (ptsSec.length < 3) continue;
      const dichSec = khoaDich(secObj.id);
      for (let i = 0; i < ptsSec.length; i += 1) {
        canhThietDienDaDung.push({ a: ptsSec[i], b: ptsSec[(i + 1) % ptsSec.length], dich: dichSec });
      }
    }
    for (const o of seDung) {
      const progress = progressById.get(o.id);
      const progressCha = o.parent ? progressById.get(o.parent) : undefined;
      if (o.type === "face" && progressCha && (!progressCha.closed || !progressCha.fill_visible)) continue;
      if (o.type === "edge" && progressCha && !progressCha.visible_edge_ids.includes(o.id)) continue;
      if (o.type === "point3" && o.parent && o.id.includes("::vertex:")) {
        if (progressCha && !progressCha.closed && Number(o.id.split(":vertex:")[1]) > progressCha.visible_edge_ids.length) {
          continue;
        }
        if ((o.depends ?? []).some((d) => idSeDung.has(d)) && !noiBat.has(o.id)) continue;
      }
      let renderObject = (nhuong.has(o.id) && !noiBat.has(o.id)) ? { ...o, display_role: "hit_proxy" } as SceneObject : o;
      if (o.type === "face" && o.parent && idSeDung.has(o.parent) && khoaDich(o.id) === khoaDich(o.parent)) {
        renderObject = { ...renderObject, display_role: "hit_proxy" };
      }
      if (o.type === "section" && progress && o.polygon) {
        const theoBuoc = vatThietDienTaiBuoc(o, progress);
        if (!theoBuoc) continue;
        renderObject = theoBuoc;
      }
      const sangBuoc = noiBat.has(o.id)
        || (o.type === "point3" && Boolean(o.parent && noiBat.has(o.parent) && progressCha && !progressCha.closed));
      const coThietDienDong = o.render === "surface" && tuongTac.selected_id !== o.id && seDung.some((x) =>
        (x.type === "section" || x.type === "circle3" || x.type === "ellipse3")
        && x.depends.includes(o.id)
        && x.closed !== false && (progressById.get(x.id)?.closed ?? true),
      );
      const diemMp = o.render === "surface"
        ? (coHinhCong || coThietDienDong
            ? diemHuuHan(seDung.filter((x) => o.depends.includes(x.id) || (x.type === "section" && x.depends.includes(o.id))))
            : diemHuuHan(seDung.filter((x) => o.depends.includes(x.id) || x.type === "solid" || (x.type === "section" && x.depends.includes(o.id)))))
        : [];
      const diemChoVat = o.render === "line"
        ? diemChoDuong(scene.objects, o.id)
        : o.render === "surface" && diemMp.length >= 3
          ? diemMp
          : diemNen;
      const emphasis = tang ? tang.get(o.id) ?? false : sangBuoc;
      const obj = buildObject3D(renderObject,
        o.id === hoveredSection && o.id !== tuongTac.selected_id && emphasis !== "dich" ? "hover" : emphasis,
        banKinhBamDiem(KHOANG_CAM_MAC_DINH), diemChoVat, undefined, canonicalHighlights, khucToSang, xray,
        vaiKhoiTheoId.get(o.id) ?? vaiKhoiTheoId.get(o.parent ?? "") ?? "primary",
        coThietDienDong, dsKhoiId.length === 1 && !seDung.some(x => x.type === "plane3"
          || ((x.type === "circle3" || x.type === "ellipse3" || x.type === "section") && x.depends.includes(o.id))));
      if (!obj) continue;
      // All steps (the circle's own step decides, #31), but only circles the user has not hidden or isolated away and
      // drawn at the same display translation: otherwise the solid would lose a cap nobody draws.
      if (o.type === "curved_solid") boVanhDayTrung(obj, o, scene.objects.filter((x) => !tuongTac.hidden_ids.includes(x.id)
        && (!tuongTac.isolated_ids.length || tuongTac.isolated_ids.includes(x.id)) && khoaDich(x.id) === khoaDich(o.id)));
      const chiSoKhoi = dsKhoiId.indexOf(o.id);
      const dichVat = khoaDich(o.id);
      if (dsKhoiId.length > 1 && chiSoKhoi >= 0) {
        const laKhoiPhu = chiSoKhoi > 0;
        if (laKhoiPhu) {
          if (o.type === "curved_solid" && dichVat === khoaDich(dsKhoiId[0])) {
            datKhoiCongKhongChe(obj);
            for (const c of [...obj.children]) {
              if (c.userData?.chieuSau || c.userData?.chieuSauMatTruoc) obj.remove(c);
            }
          }
        }
        if (o.type === "solid") {
          const diemTrenDoan = (p: THREE.Vector3, a: THREE.Vector3, b: THREE.Vector3) => {
            const abx = b.x - a.x, aby = b.y - a.y, abz = b.z - a.z;
            const lenSq = abx * abx + aby * aby + abz * abz;
            if (lenSq < 1e-12) return false;
            const apx = p.x - a.x, apy = p.y - a.y, apz = p.z - a.z;
            const t = (apx * abx + apy * aby + apz * abz) / lenSq;
            if (t < -1e-4 || t > 1 + 1e-4) return false;
            return Math.hypot(a.x + abx * t - p.x, a.y + aby * t - p.y, a.z + abz * t - p.z) <= 1e-4;
          };
          if (laKhoiPhu && dichVat === khoaDich(dsKhoiId[0]) && !sangBuoc && (o.vertices?.length ?? 0) > 0) {
            const namTrongKhoiChinh = (o.vertices ?? []).every((vRaw) => {
              const vp = new THREE.Vector3(...toVec3(vRaw));
              return canhKhoiDaDung.some((c) => c.dich === dichVat && diemTrenDoan(vp, c.a, c.b));
            });
            if (namTrongKhoiChinh) {
              for (const c of [...obj.children]) {
                if (c.userData?.chieuSau) {
                  obj.remove(c);
                } else if ((c as THREE.Mesh).isMesh) {
                  const mat = (c as THREE.Mesh).material as THREE.MeshStandardMaterial;
                  mat.colorWrite = false;
                  mat.opacity = 0;
                }
              }
            }
          }
          obj.traverse((child) => {
            const edge = child.userData?.canonicalEdge as ReturnType<typeof canonicalEdgesOf>[number] | undefined;
            if (!edge || !(child as THREE.Group).isGroup) return;
            if (!laKhoiPhu) {
              canhKhoiDaDung.push({ a: edge.a.clone(), b: edge.b.clone(), dich: dichVat });
              return;
            }
            const trungCanhChinh = canhKhoiDaDung.some(
              (c) => c.dich === dichVat && diemTrenDoan(edge.a, c.a, c.b) && diemTrenDoan(edge.b, c.a, c.b),
            );
            const trungCanhThietDien = canhThietDienDaDung.some(
              (c) => c.dich === dichVat && diemTrenDoan(edge.a, c.a, c.b) && diemTrenDoan(edge.b, c.a, c.b),
            );
            if ((trungCanhChinh || trungCanhThietDien) && !child.userData.highlighted && !child.userData.khuc) {
              child.visible = false;
            }
          });
        }
      }
      if (tang && !tang.has(o.id)) lamDiu(obj);   // ngoài chuỗi nhân quả
      const bd = visualTransformOf(tuongTac, scene, o.id);
      datViTriTrinhBay(obj, bd);
      goc.add(obj);
      daDung.push(renderObject.polygon && o.type === "section"
        ? `${o.id}#${renderObject.polygon.length}${renderObject.closed ? "c" : ""}`
          + `${renderObject.fill_visible ? "f" : ""}` : o.id);
      // Chỉ ĐIỂM mang nhãn `.geo3d-label`. Mặt phẳng có ký hiệu (`notation`) do backend phát
      // được gắn nhãn `.geo3d-nhan-mp` riêng ở diềm mở rộng của tấm mặt phẳng.
      if (o.type === "point3" && o.xyz) {
        const [x, y, z] = toVec3(o.xyz);
        viTriNhan.current.set(o.id, new THREE.Vector3(
          x + bd.translate[0], y + bd.translate[1], z + bd.translate[2]));
      }
      if (o.type === "plane3" && o.point && o.normal && kyHieu(o) !== null) {
        const neo = diemNeoNhanMatPhang(toVec3(o.point), toVec3(o.normal), diemChoVat);
        if (neo) {
          viTriMatPhang.current.set(o.id, new THREE.Vector3(
            neo[0] + bd.translate[0], neo[1] + bd.translate[1], neo[2] + bd.translate[2]));
        }
      }
    }
    if (typeof window !== "undefined") {
      (window as any).__geo3d_rendered_object_ids = daDung;
      (window as any).__geo3d_auxiliary_hidden_ids = [...anPhu].sort();
      (window as any).__geo3d_causal_tiers = tang ? Object.fromEntries(tang) : null;
    }
    veRef.current?.();
  }, [scene, buoc, tuongTac, tapNoiBat, tang, anPhu, xray, vaiKhoiTheoId, hoveredSection]);

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
  // Chỉ in nhãn cho vật CÓ ký hiệu do backend phát. Vật không có ký hiệu thì
  // khung không in gì cho nó — trước bản này phía đây tự rút một ký hiệu từ
  // `id`, nên `plane_MNP` hiện thành `MNP` và `V_AMNP` hiện nguyên si.
  const tapHienId = new Set(hien.map((x) => x.id));
  const ungVienNhan = hien.filter(
    (o) => o.type === "point3"
      && veTrenKhung(o)
      && kyHieu(o) !== null
      && !anPhu.has(o.id)
      && isVisible(tuongTac, o.id, tapHienId),
  );
  const chuNhanDiem = kyHieuDiem(ungVienNhan);
  // Kiểu nhãn SGK theo vai trò (HTML tham chiếu: main-vertex / section-vertex / aux-vertex) — chỉ trình bày.
  // Chỉ các vật CÓ MẶT ở bước đang xem (frame k ⇔ trace[k]): M chưa mang vai đỉnh thiết diện trước khi thiết diện dựng.
  const dinhThietDien = useMemo(() => diemTaiDinhThietDien({ objects: objectsAt(scene, buoc) }), [scene, buoc]);
  const vaiNhan = (o: SceneObject) => dinhThietDien.has(o.id) ? " vai-thiet-dien"
    : o.origin === "derived" ? " vai-phu" : "";
  const nhanDiem = ungVienNhan.filter((o) => chuNhanDiem.has(o.id));
  const nhanMatPhang = hien.filter(
    (o) => o.type === "plane3"
      && veTrenKhung(o)
      && kyHieu(o) !== null
      && !anPhu.has(o.id)
      && isVisible(tuongTac, o.id, tapHienId),
  );

  useEffect(() => {
    if (typeof window !== "undefined") {
      (window as any).__geo3d_selected_id = tuongTac?.selected_id || null;
      (window as any).__geo3d_highlighted_ids = [...tapNoiBat].sort();
    }
  }, [tuongTac?.selected_id, tapNoiBat]);

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
                className={`geo3d-label${vaiNhan(o)}${
                  tuongTac.selected_id === o.id ? " la-chon" : tang && !tang.has(o.id) ? " la-diu" : ""
                }`}
                data-uu-tien={uuTienNhan(o, tuongTac.selected_id)}
                title={o.label}
              >
                {chuNhanDiem.get(o.id) ?? kyHieu(o)}
              </span>
            ))}
          </div>
          <div ref={nhanMpRef} className="geo3d-plane-labels" aria-hidden="true">
            {nhanMatPhang.map((o) => {
              const t = tang?.get(o.id);
              const chon = tuongTac.selected_id === o.id || t === "dich" || (!tang && tapNoiBat.has(o.id));
              const diu = tang !== null && !tang.has(o.id);
              return (
                <span
                  key={o.id}
                  data-plane-id={o.id}
                  className={`geo3d-nhan-mp${chon ? " la-chon" : diu ? " la-diu" : ""}`}
                  data-uu-tien={uuTienNhan(o, tuongTac.selected_id)}
                  title={o.label}
                >
                  {kyHieu(o)}
                </span>
              );
            })}
          </div>
          {/* W17 · SỐ ĐO TRÊN HÌNH. W12 gỡ dải số nổi vì một con số không chủ thể đặt ở đâu cũng
              vô nghĩa. Nhãn ở đây khác ở đúng chỗ ấy: mỗi nhãn đứng cạnh CHỦ THỂ backend gắn
              (đoạn, miền, khối, điểm của cặp, nhân chứng), chỉ từ bước đại lượng khả dụng.
              W18 §16.5: mặc định chỉ dữ kiện; nhãn là NÚT (bấm/Enter/Space ⇒ chọn đại lượng, chi
              tiết mở ở ô soi), nên lớp này không còn giấu khỏi trình đọc màn hình. */}
          <div ref={soDoRef} className="geo3d-so-do-lop" aria-label="Số đo trên hình">
            {nhanChu.map((a) => {
              const diu = !a.related && tang !== null && !tang.has(a.id)
                && !a.subject_ids.some((id) => tang.has(id));
              return (
                <span
                  key={a.id}
                  role="button"
                  tabIndex={0}
                  aria-pressed={tuongTac.selected_id === a.id}
                  data-ann-id={a.id}
                  data-uu-tien={a.priority}
                  className={`geo3d-so-do${a.role === "result" ? " la-ket-qua" : ""}${
                    a.related ? " la-lien-quan" : diu ? " la-diu" : ""}`}
                >
                  {a.text}
                </span>
              );
            })}
          </div>
        </div>
      )}
      {/* Mọi con số — dữ kiện, bước tính, kết quả — có đủ ở bảng lời giải dưới thanh bước
          (`scene3d-solution.tsx`); nhãn trên hình (W17) chỉ là lối tắt đọc cạnh chủ thể.

          Nội suy GỘP thành MỘT chuỗi: `{a}/{b}` làm SSR chèn marker
          `<!-- -->` vào giữa, nên chữ hiện ra đúng mà mọi phép kiểm chuỗi lại
          trượt — một lệch câm giữa thứ người đọc thấy và thứ test đọc. */}
      <p className="geo3d-progress geo3d-sr">
        {`Bước ${geometryStepOf(scene, buoc) + 1}/${geometryStepCount(scene)}`}
      </p>
      {/* W4: dòng lời kể nhìn thấy dưới thanh đã gỡ — đây là nơi trình đọc màn hình NGHE bước mới. */}
      <p className="geo3d-narration geo3d-sr" aria-live="polite">{geometryNarrationAt(scene, buoc)}</p>
    </div>
  );
}
