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
  dayVaDinhChop,
  diemHuuHan,
  duongKinhCanh,
  geometryHighlightedAt,
  geometryNarrationAt,
  geometryStepCount,
  geometryStepOf,
  khungMatPhang,
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
import { entitiesPresentAt, parentSolidOf } from "./scene3d-subentities";
import {
  canonicalEdgesOf,
  classifySolidEdgeVisibility,
  type EdgeVisibilityAudit,
} from "./scene3d-edge-visibility";
export { classifySolidEdgeVisibility } from "./scene3d-edge-visibility";
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
  locNhanChongNhau,
  uuTienNhan,
  veTrenKhung,
} from "./scene3d-presentation";
import {
  type KhungNhin, chonHuongNhin, hopBaoCuaDiem, huongLenHienThi, khungGocVuong, khungNhinSuPham, khungNhinVua,
} from "./scene3d-camera";
import { MAU_VAI_TRO } from "./scene3d-roles";
import {
  type AnnotationView,
  type LabelRect,
  type LabelToPlace,
  type WitnessShown,
  DEFAULT_ANNOTATION_VIEW,
  annotationAnchor,
  annotationsAt,
  placeAnnotationLabels,
  witnessesShown,
} from "./scene3d-annotations";
import { auxiliaryHiddenAt } from "./scene3d-auxiliary";

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

/** Màu theo KIỂU vật. Điểm đề cho trung tính (W12): xanh chỉ còn nghĩa "đang
 *  xét" — vật được chọn, hoặc vật vừa dựng ở bước đang phát. */
const MAU = {
  free: MAU_VAI_TRO.diem_de_cho,
  derived: 0xdc2626,
  line: 0x0f766e,
  surface: 0x7c3aed,
  mesh: 0x64748b,
  /** Mực cạnh khối — tách khỏi màu mặt tô, nếu không cạnh chìm vào mặt (w09). */
  canh: 0x1e293b,
  polygon: 0xf59e0b,
  /** Vật MỚI DỰNG ở bước đang phát (formation) — xanh "đang xét" (W12). Bản
   *  w11 là cam `0xea580c`, trùng họ với cam của dữ kiện số. */
  highlight: MAU_VAI_TRO.moi_dung,
} as const;

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
const HE_SO_LAM_DIU = 0.3;
/** Đường VÔ HẠN (đường phụ) không được nhấn: lùi xuống, không biến mất (w11). */
const HE_SO_DUONG_PHU = 0.45;

function lamDiuVatLieu(m: THREE.Material, k: number): void {
  if ((m as THREE.Material & { colorWrite?: boolean }).colorWrite === false) return;
  m.transparent = true;
  m.opacity *= k;
}

/** Làm dịu cả một vật — trừ cạnh chuẩn đang được tô qua vật khác trong chuỗi. */
export function lamDiu(obj: THREE.Object3D, k = HE_SO_LAM_DIU): void {
  const bo = new Set<THREE.Object3D>();
  obj.traverse((x) => {
    if (x.userData?.visualOwnerId && x.userData.highlighted === true) x.traverse((y) => bo.add(y));
  });
  obj.traverse((x) => {
    if (bo.has(x)) return;
    if (x.userData?.visualOwnerId) x.userData.lamDiu = k;
    if (x.userData?.sang === true) return;   // khúc tô sáng của đoạn con nằm trên cạnh (W4)
    const m = (x as THREE.Mesh).material as THREE.Material | THREE.Material[] | undefined;
    for (const vl of Array.isArray(m) ? m : m ? [m] : []) lamDiuVatLieu(vl, k);
  });
}

/** Toạ độ cảnh → khung THẾ GIỚI qua phép xoay hiển thị (đồng nhất thức khi đáy ngang — trả lại chính các số). */
function xoay(p: Vec3, q: THREE.Quaternion): Vec3 {
  if (q.x === 0 && q.y === 0 && q.z === 0) return p;
  const w = new THREE.Vector3(...p).applyQuaternion(q);
  return [w.x, w.y, w.z];
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
export const DO_DUC_TO_THIET_DIEN = 0.45;

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
const NET_DUT_TI_LE = 0.022;

/** Bản sao VÔ HÌNH chỉ ghi chiều sâu, để đường biết mình có bị che không. */
function lopChieuSau(g: THREE.BufferGeometry): THREE.Mesh {
  const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({
    colorWrite: false, depthWrite: true, depthTest: true,
    side: THREE.DoubleSide,
    /* ⚠️ ĐỤC, KHÔNG `transparent` — và đây là bản sửa của một lỗi đã đo được.
     *
     * Bản đầu khai `transparent: true, opacity: 0` để lớp này nằm cùng hàng
     * đợi với khối tô bóng và tôn trọng `renderOrder`. Nhưng hàng đợi TRONG
     * SUỐT còn sắp theo KHOẢNG CÁCH, nên ở một số góc lớp chiều sâu ghi SAU
     * khi vành thiết diện đã hỏi — lượt "thấy" vì thế vẫn vẽ trên cung khuất,
     * và cung ấy đọc ra LIỀN.
     *
     * Chẩn đoán: tô tạm lượt khuất màu đỏ rồi chụp `p3` ở góc mặc định — ảnh
     * cho thấy ĐỎ và HỔ PHÁCH nằm chồng nhau trên cùng một cung, tức cả hai
     * lượt cùng vẽ. Không có phép thử ấy thì triệu chứng ("cung khuất vẫn
     * liền") trỏ nhầm sang phép kiểm chiều sâu hoặc sang độ lệch.
     *
     * Hàng đợi ĐỤC luôn chạy trước TOÀN BỘ hàng đợi trong suốt, nên chiều sâu
     * chắc chắn có mặt trước khi bất kỳ đường nào hỏi. `colorWrite: false` giữ
     * nó vô hình, nên khối vẫn trong suốt y như trước.
     */
    transparent: false,
    /* ⚠️ Lùi chiều sâu một chút (w10). `polygonOffset` của ĐƯỜNG không có tác
     * dụng — WebGL chỉ áp nó cho đa giác — nên cạnh nằm đúng trên mặt khối
     * tranh chiều sâu với chính mặt ấy và hiện lấm tấm (ảnh: cạnh SC). Đẩy
     * lớp này (một đa giác) ra sau thì đường trên mặt luôn thắng. */
    polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
  }));
  m.renderOrder = THU_TU_CHIEU_SAU;
  m.userData.chieuSau = true;      // không bắt chuột, không vào hộp bao
  return m;
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
    ...chung, depthFunc: THREE.LessEqualDepth,
  }));
  thay.renderOrder = THU_TU_DUONG;
  thay.name = `${ten}:thay`;
  nhom.add(thay);

  const khuat = new Lop(g, new THREE.LineDashedMaterial({
    ...chung, depthFunc: THREE.GreaterDepth, depthWrite: false,
    dashSize: chuKy, gapSize: chuKy, transparent: true, opacity: 0.75,
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
  dashSize = 0.16,
  highlightColor: number = MAU.highlight,
): THREE.LineBasicMaterial | THREE.LineDashedMaterial {
  const common = {
    color: highlighted ? highlightColor : color,
    linewidth: highlighted ? 3 : 1,
    polygonOffset: true,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -2,
    // Hàng đợi trong suốt (opacity 1): `renderOrder` xếp nét SAU mặt tô, nếu
    // không mặt tô trong suốt vẽ đè lên nét và cạnh giữa hai mặt nhạt đi.
    transparent: true,
  } as const;
  return hidden
    ? new THREE.LineDashedMaterial({
        ...common, dashSize, gapSize: dashSize * 0.75, transparent: true, opacity: 0.9,
        depthTest: false, depthWrite: false,
      })
    // ponytail: phân loại CPU chỉ xét mặt của CHÍNH khối; cảnh nhiều khối chồng
    // nhau sẽ cần truyền `occluders` vào `classifySolidEdgeVisibility`.
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
  for (const o of vat.filter((x) => laNoiBat(x.id))) {
    if (o.edge_span) khuc.set(o.edge_span.edge_id, { t0: o.edge_span.t0, t1: o.edge_span.t1, mau: mau(o.id) });
    else for (const id of o.boundary_edge_ids ?? []) ca.set(id, mau(o.id));
  }
  return { ca, khuc };
}

function rebuildCanonicalEdgeOwner(
  owner: THREE.Group,
  edge: ReturnType<typeof canonicalEdgesOf>[number],
  spans: EdgeVisibilityAudit["edge_spans"],
): void {
  for (const child of [...owner.children]) {
    owner.remove(child);
    (child as THREE.Line).geometry?.dispose();
    const material = (child as THREE.Line).material as THREE.Material | undefined;
    material?.dispose();
  }
  const khuc = owner.userData.khuc as KhucToSang | undefined;
  const ownSpans = chiaKhucToSang(spans.filter((span) => span.edge_id === edge.id), khuc);
  for (const span of ownSpans) {
    const a = edge.a.clone().lerp(edge.b, span.t0);
    const b = edge.a.clone().lerp(edge.b, span.t1);
    const geometry = new THREE.BufferGeometry().setFromPoints([a, b]);
    const isHidden = span.visibility === "HIDDEN";
    const material = canonicalEdgeMaterial(
      isHidden,
      owner.userData.highlighted === true || span.sang,
      owner.userData.edgeColor as number,
      owner.userData.dashSize as number,
      span.sang ? khuc!.mau : owner.userData.highlightColor as number | undefined,
    );
    // Làm dịu (ngoài chuỗi nhân quả) phải sống qua lần dựng lại khi xoay — trừ KHÚC đang tô sáng (W4: chọn SM thì
    // khối ngoài chuỗi bị làm dịu, nhưng khúc S–M của nó là chính vật đang chọn).
    if (owner.userData.lamDiu && !span.sang) lamDiuVatLieu(material, owner.userData.lamDiu as number);
    const line = new THREE.Line(geometry, material);
    if (isHidden) line.computeLineDistances();
    line.userData.hidden = isHidden;
    line.userData.sang = span.sang;
    line.userData.logicalEdgeId = edge.id;
    line.renderOrder = THU_TU_DUONG;
    owner.add(line);
  }
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
  let triangleCount = 0;
  let sampleCount = 0;
  let recomputedSolidCount = 0;
  root.traverse((candidate) => {
    const source = candidate.userData?.solidSceneObject as SceneObject | undefined;
    if (!source) return;
    const localCamera = candidate.worldToLocal(camera.position.clone());
    // `OrbitControls` (damping) round-trips the pose through spherical
    // coordinates every frame, so an idle camera walks in its last ULPs and an
    // exact-float key recomputed every mobile frame. 10 significant digits move
    // a projected point by ~1e-6 physical px here — far below the 0.5 px
    // product↔oracle tolerance; ±0 and sub-1e-12 noise collapse to 0.
    const khoa = (v: number) => (Math.abs(v) < 1e-12 ? 0 : Number(v.toPrecision(10)));
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
      audit = classifySolidEdgeVisibility(source, localCamera, {
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
  });
  const visible = [...status].filter(([, values]) => values.size === 1 && values.has("visible"))
    .map(([id]) => id).sort();
  const hidden = [...status].filter(([, values]) => values.size === 1 && values.has("hidden"))
    .map(([id]) => id).sort();
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
export function diemKhungNhin(goc: THREE.Object3D): [number, number, number][] {
  const diem: [number, number, number][] = [];
  const p = new THREE.Vector3();
  // Cờ nằm trên NHÓM (đường vô hạn là một nhóm hai nét): hỏi cả tổ tiên, không
  // chỉ chính nút — bỏ sót thì nét con kéo khung theo đoạn do renderer tự chọn
  // (w11: "Xem lại toàn hình" ở bước cuối bài thiết diện dời hẳn tâm nhìn).
  const boQua = (vat: THREE.Object3D) => {
    for (let x: THREE.Object3D | null = vat; x && x !== goc; x = x.parent) {
      if (x.userData?.voHan || x.userData?.chieuSau) return true;
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
  return new Set(dung.filter((o) => o.type === "segment3" && o.boundary_edge_ids?.length
    && o.boundary_edge_ids.every((id) => chu.get(id) === bienDoi(o.id))).map((o) => o.id));
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
  noiBat: boolean | TangNhanManh,
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
  const nen = (macDinh: number) => mau ?? (boiCanh ? MAU_NEN_BOI_CANH : macDinh);
  const net = (macDinh: number) => mau ?? (boiCanh ? MAU_VAI_TRO.boi_canh : macDinh);

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
    // là dữ liệu từ kernel.
    const p = new THREE.Vector3(...toVec3(o.point));
    const d = new THREE.Vector3(...toVec3(o.direction)).normalize();
    const a = p.clone().addScaledVector(d, -LINE_DISPLAY_HALF_LENGTH);
    const b = p.clone().addScaledVector(d, LINE_DISPLAY_HALF_LENGTH);
    const g = new THREE.BufferGeometry().setFromPoints([a, b]);
    const duong = duongHaiLuot(g, net(MAU.line),
      beDayNet(diemNen, 1) / SECTION_STROKE_RATIO * NET_DUT_TI_LE,
      `line:${o.id}`, true);
    // Cùng lẽ với mặt phẳng: `line3` vô hạn, hai đầu mút là quyết định trình
    // bày. Ở `p1`, đường `BD` kéo dài vượt ra ngoài khối chóp; để nó tham gia
    // auto-fit thì camera phải lùi ra và khối thật bé đi vì một đoạn thẳng do
    // chính renderer bịa ra độ dài.
    duong.userData.voHan = true;
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
    // Nhường nét cho cạnh chuẩn của khối (`doanNhuongCanh`): chỉ còn vùng bấm.
    const duong: THREE.Object3D = o.display_role === "hit_proxy"
      ? v(new THREE.Line(g, new THREE.LineBasicMaterial({
          colorWrite: false, depthWrite: false, transparent: true, opacity: 0, linewidth: 6,
        })), `segment:${o.id}:proxy`)
      : duongHaiLuot(
          g,
          net(MAU.line),
          (beDayNet(diemNen, 1) / SECTION_STROKE_RATIO) * NET_DUT_TI_LE,
          `segment:${o.id}`,
          true,
        );
    duong.userData.voHan = false;

    // Ký hiệu góc vuông (perpendicular marker) tại chân đường cao nếu là chiều cao
    const laChieuCao =
      o.id.includes("cao") ||
      (o.label && /chiều cao/i.test(o.label)) ||
      (o.role && /chiều cao/i.test(o.role));
    const chan = a.z <= b.z ? a : b;
    const k = laChieuCao ? khungGocVuong(chan.toArray(), (chan === a ? b : a).toArray()) : null;
    if (k) {
      const s = 0.35;
      // Theo khung của chính đoạn (`khungGocVuong`): đoạn thẳng đứng ⇒ đúng các điểm trục cũ.
      const diem = (...cac: [Vec3, number][]) => new THREE.Vector3(...[0, 1, 2].map((i) =>
        chan.getComponent(i) + cac.reduce((t, [u, h]) => t + u[i] * h, 0)) as Vec3);
      const ptsMarker = [
        diem([k.e1, s]),
        diem([k.e1, s], [k.d, s]),
        diem([k.d, s]),
        diem([k.e2, s], [k.d, s]),
        diem([k.e2, s]),
      ];
      const gMarker = new THREE.BufferGeometry().setFromPoints(ptsMarker);
      const lineMarker = new THREE.Line(
        gMarker,
        new THREE.LineBasicMaterial({
          color: net(MAU.line),
          linewidth: 1.5,
        }),
      );
      lineMarker.name = `perp_marker:${o.id}`;

      const nhom = new THREE.Group();
      nhom.add(duong);
      nhom.add(lineMarker);
      return v(nhom, `segment:${o.id}`);
    }

    return v(duong, `segment:${o.id}`);
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
      color: net(MAU.surface),
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
    const trong = Math.max(0, r - day / 2), ngoai = r + day / 2;
    const chungVanh = {
      color: net(MAU.line), side: THREE.DoubleSide,
      ...LECH_THIET_DIEN,
    } as const;
    // Cùng lối với elip: phần THẤY là vành đầy, phần KHUẤT là vành ngắt quãng
    // (`thetaLength` một nửa mỗi chu kỳ) — nét đứt bám đúng đường tròn.
    const nhomVanh = new THREE.Group();
    const thay = new THREE.Mesh(
      new THREE.RingGeometry(trong, ngoai, VONG_CHIA),
      new THREE.MeshBasicMaterial({ ...chungVanh, depthFunc: THREE.LessEqualDepth }));
    thay.renderOrder = THU_TU_VE_THIET_DIEN;
    nhomVanh.add(thay);
    const soNet = VONG_CHIA / 4;             // xem chú thích ở nhánh elip
    const buoc = (Math.PI * 2) / soNet;
    for (let i = 0; i < soNet; i += 1) {
      const cung = new THREE.Mesh(
        new THREE.RingGeometry(trong, ngoai, 2, 1, i * buoc, buoc / 2),
        new THREE.MeshBasicMaterial({
          ...chungVanh, depthFunc: THREE.GreaterDepth, depthWrite: false,
          transparent: true, opacity: 0.7,
        }));
      cung.renderOrder = THU_TU_VE_THIET_DIEN;
      nhomVanh.add(cung);
    }
    const n = new THREE.Vector3(...toVec3(o.normal)).normalize();
    nhomVanh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), n);
    nhomVanh.position.set(...toVec3(o.center));
    return v(nhomVanh, `circle:${o.id}`);
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
    /* HAI hình học từ CÙNG một vành: bản đầy đủ cho phần THẤY, bản bỏ đoạn
       xen kẽ cho phần KHUẤT. Vành vốn đã chia sẵn `VONG_CHIA` đoạn, nên "nét
       đứt" ở đây là bỏ bớt đoạn — không cần vật liệu nét đứt cho mesh, và chu
       kỳ đứt bám đúng đường cong thay vì bám độ dài chiếu. */
    const dinhDay: number[] = [];
    const dinhDut: number[] = [];
    for (let i = 0; i < VONG_CHIA; i += 1) {
      const [a0, b0, a1, b1] = [trong[i], ngoai[i], trong[i + 1], ngoai[i + 1]];
      const sau = [a0.x, a0.y, a0.z, b0.x, b0.y, b0.z, a1.x, a1.y, a1.z,
        b0.x, b0.y, b0.z, b1.x, b1.y, b1.z, a1.x, a1.y, a1.z];
      dinhDay.push(...sau);
      /* Chu kỳ 4 đoạn (2 vẽ, 2 bỏ), không phải 2. Đo được: với elip nhỏ như
         `p7`, 24 nét trên một vành ~120px cho khe đứt ~2,5px — không đọc ra là
         nét đứt, và cũng không đo được. Thưa gấp đôi thì khe rộng gấp đôi. */
      if (i % 4 < 2) dinhDut.push(...sau);
    }
    const hh = (ds: number[]) => {
      const bg = new THREE.BufferGeometry();
      bg.setAttribute("position", new THREE.Float32BufferAttribute(ds, 3));
      return bg;
    };
    const chungVanh = {
      color: net(MAU.line), side: THREE.DoubleSide,
      ...LECH_THIET_DIEN,
    } as const;
    const nhomVanh = new THREE.Group();
    /* ⚠️ `depthTest: false` ĐÃ BỎ Ở ĐÂY. Nó làm thiết diện luôn vẽ đè lên mọi
       thứ — tiện để "nhìn thấy", nhưng khi ấy phần khuất và phần thấy hiện y
       hệt nhau, và câu *"đường này nằm trước hay sau khối"* mất luôn câu trả
       lời. Nay thiết diện đi qua đúng phép kiểm chiều sâu như mọi đường khác;
       phần khuất vẫn đọc được vì nó được vẽ, chỉ ở dạng đứt và nhạt hơn. */
    const thay = new THREE.Mesh(hh(dinhDay), new THREE.MeshBasicMaterial({
      ...chungVanh, depthFunc: THREE.LessEqualDepth,
    }));
    thay.renderOrder = THU_TU_VE_THIET_DIEN;
    const khuat = new THREE.Mesh(hh(dinhDut), new THREE.MeshBasicMaterial({
      ...chungVanh, depthFunc: THREE.GreaterDepth, depthWrite: false,
      transparent: true, opacity: 0.7,
    }));
    khuat.renderOrder = THU_TU_VE_THIET_DIEN;
    nhomVanh.add(thay, khuat);
    nhomVanh.position.set(...toVec3(o.center));
    return v(nhomVanh, `ellipse:${o.id}`);
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
      color: net(MAU.surface),
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
    /* Khối cong cũng phải CHE được đường nằm sau nó. Bản sao chiều sâu dùng
       CHUNG hình học và CHÉP phép biến đổi từ chính `mesh` — dựng lại phép
       quay ở đây là mở đường cho hai bản trôi khỏi nhau. */
    const nhomCong = new THREE.Group();
    const bong = lopChieuSau(g);
    bong.quaternion.copy(mesh.quaternion);
    bong.position.copy(mesh.position);
    nhomCong.add(mesh, bong);
    return v(nhomCong, `curved:${o.id}:${o.curved_kind}`);
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
      color: nen(MAU.mesh),
      transparent: true,
      opacity: 0.22,
      side: THREE.DoubleSide,
      depthWrite: false,
    })));
    // Lớp chiều sâu: chính khối này che các cạnh nằm sau nó.
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
    return v(new THREE.Mesh(g, new THREE.MeshStandardMaterial({
      color: nen(MAU.polygon),
      transparent: true,
      opacity: noiBat ? 0.55 : 0.14,
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
      linewidth: 6,
    } : {
      color: net(MAU.line), linewidth: 2,
    })), `edge:${o.id}`);
  }

  if (o.render === "polygon" && (o.polygon || o.vertices)) {
    const rawPts = (o.polygon ?? o.vertices ?? []).map(toVec3);
    if (rawPts.length < 2) return null;
    const pts = rawPts.map((p) => new THREE.Vector3(...p));
    const vong = o.closed === false ? pts : [...pts, pts[0]];
    const gLine = new THREE.BufferGeometry().setFromPoints(vong);
    const line = new THREE.Line(gLine, new THREE.LineBasicMaterial({
      color: net(MAU.polygon), linewidth: 2,
    }));
    const ownsBoundary = !(
      o.surface_role === "BASE_REGION"
      && o.occludes_edges === false
      && (o.boundary_edge_ids?.length ?? 0) > 0
    );

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
        // ⚠️ Và KHÔNG kiểm chiều sâu (W15, đo ở trình duyệt). Thiết diện nằm TRONG khối, nên
        // mọi điểm trong của nó ở SAU mặt trước của khối; lớp chiều sâu đục của khối chạy
        // trước toàn bộ hàng đợi trong suốt, nên một vật tô có kiểm chiều sâu bị loại ở MỌI
        // điểm ảnh — có mặt trong cảnh mà không bao giờ hiện (bật/tắt: ΔE = 0). Nét viền
        // thiết diện vẫn hai lượt thấy/khuất; chỉ vùng tô xuyên qua khối trong suốt.
        //
        // W16: thứ tự `THU_TU_TO_THIET_DIEN` — sau mặt, TRƯỚC nét: cạnh khối đi qua vùng
        // tô vẫn đọc rõ (§14.4), thay vì bị phủ hổ phách như ở thứ tự 10 của W15.
        const thietDien = o.type === "section";
        const mesh = new THREE.Mesh(gMesh, new THREE.MeshStandardMaterial({
          color: nen(MAU.polygon),
          transparent: true,
          opacity: thietDien ? DO_DUC_TO_THIET_DIEN : noiBat ? 0.35 : 0.16,
          side: THREE.DoubleSide,
          depthWrite: false,
          ...(thietDien ? { ...LECH_THIET_DIEN, depthTest: false } : {}),
        }));
        mesh.name = `${thietDien ? "section_fill" : "polygon_fill"}:${o.id}`;
        if (thietDien) mesh.renderOrder = THU_TU_TO_THIET_DIEN;
        const nhom = new THREE.Group();
        if (ownsBoundary) nhom.add(line);
        nhom.add(mesh);
        return v(nhom, `polygon:${o.id}`);
      }
    }

    return ownsBoundary ? v(line, `polygon:${o.id}`) : v(new THREE.Group(), `polygon:${o.id}`);
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
}

/** §16.7 — cạnh góc vuông của ký hiệu tại chân, theo độ dài đoạn tới chân, có trần (đơn vị cảnh). */
const NHAN_CHUNG_GOC = { tiLe: 0.15, toiDa: 0.5 };

/** Nhân chứng một khoảng cách: đoạn nét đứt từ điểm tới CHÂN backend phát + ký hiệu vuông góc dựng từ
 *  hai phương backend phát (`u`, `v`) — chỉ đổi độ dài để có cỡ ký hiệu, không suy luận hình học nào. */
function vatNhanChung(w: WitnessShown): THREE.Group {
  const g = new THREE.Group();
  const tu = new THREE.Vector3(...w.from);
  const chan = new THREE.Vector3(...w.foot);
  const v = new THREE.Vector3(...w.v);
  const s = Math.min(v.length() * NHAN_CHUNG_GOC.tiLe, NHAN_CHUNG_GOC.toiDa);
  const u1 = new THREE.Vector3(...w.u).normalize().multiplyScalar(s);
  const v1 = v.normalize().multiplyScalar(s);
  const doan = new THREE.Line(new THREE.BufferGeometry().setFromPoints([tu, chan]),
    new THREE.LineDashedMaterial({ color: MAU_VAI_TRO.dich, dashSize: 0.16, gapSize: 0.1, depthTest: false }));
  doan.computeLineDistances();
  const goc = new THREE.Line(new THREE.BufferGeometry().setFromPoints(
    [chan.clone().add(u1), chan.clone().add(u1).add(v1), chan.clone().add(v1)]),
  new THREE.LineBasicMaterial({ color: MAU_VAI_TRO.dich, depthTest: false }));
  for (const x of [doan, goc]) {
    x.renderOrder = 10;
    x.raycast = () => {};                 // trình bày thuần: không bao giờ bắt cú bấm chọn vật
    g.add(x);
  }
  g.userData = { nhanChung: w.id };
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

export function Scene3DWorkspace({
  scene, step, interaction, onSelect, fitToken = 0, annotationView = DEFAULT_ANNOTATION_VIEW,
  auxiliaryShown = false, gridShown = false,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rootRef = useRef<THREE.Group | null>(null);
  const veRef = useRef<(() => void) | null>(null);
  //: Đặt lại khung nhìn cho vừa hình. Giữ trong ref vì nó do vòng dựng cảnh
  //: tạo ra (cần `cam`, `controls`) nhưng được gọi từ ngoài vòng ấy.
  const vuaKhungRef = useRef<(() => void) | null>(null);
  const [webglFailed, setWebglFailed] = useState(false);
  /* regular-triangular-pyramid-w01 — XOAY HIỂN THỊ: đáy chóp nghiêng (§18.2) về nằm ngang. Đồng nhất thức cho mọi cảnh
     có đáy ngang (mọi họ trước), nên các họ ấy không đổi một điểm ảnh. Áp lên nhóm gốc + nhóm nhân chứng; vị trí THẾ GIỚI
     của nhãn/khung nhìn/lưới đi qua cùng phép quay (`xoay`). Toạ độ cảnh không đổi. */
  const qHienThi = useMemo(() => {
    const dc = dayVaDinhChop(scene.objects);
    const len = dc ? huongLenHienThi(dc.day, dc.dinh) : null;
    return len
      ? new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(...len), new THREE.Vector3(0, 0, 1))
      : new THREE.Quaternion();
  }, [scene]);
  const qRef = useRef(qHienThi);
  qRef.current = qHienThi;
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
  // W17 · §15.4 / W18 · §16.5: nhãn số đo của bước — gọn mặc định, tập trung theo lựa chọn. Chủ thể
  // phải đang hiện — ẩn/cô lập theo cùng luật nhãn điểm. "Hiện tất cả" chỉ đổi danh sách này (và nhân
  // chứng của nó): hình, camera, bước, chuỗi nhân quả, nét đứt không đọc nó.
  const coMatNhan = useMemo(() => new Set(objectsAt(scene, buoc).map((o) => o.id)), [scene, buoc]);
  const nhanSoDo = useMemo(
    () => annotationsAt(scene, buoc, annotationView, tuongTac.selected_id ?? null)
      .filter((a) => a.subject_ids.every((id) => isVisible(tuongTac, id, coMatNhan))),
    [scene, buoc, annotationView, tuongTac, coMatNhan],
  );
  const chonHienTai = useRef<string | null>(null);
  chonHienTai.current = tuongTac.selected_id ?? null;
  useEffect(() => {
    // Điểm neo THẾ GIỚI + độ dời trình bày của chủ thể (tách khối), đọc trong vòng vẽ qua ref.
    const m = new Map<string, THREE.Vector3>();
    for (const a of nhanSoDo) {
      const p = annotationAnchor(scene, a);
      if (!p) continue;
      const doi = a.subject_ids.map((id) => visualTransformOf(tuongTac, scene, id).translate);
      const tb = [0, 1, 2].map((i) => doi.reduce((s, t) => s + t[i], 0) / doi.length);
      m.set(a.id, new THREE.Vector3(p[0] + tb[0], p[1] + tb[1], p[2] + tb[2]));
    }
    viTriSoDo.current = m;
  }, [scene, nhanSoDo, tuongTac]);
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
    scene3.add(new THREE.AmbientLight(0xffffff, 0.75));
    const den = new THREE.DirectionalLight(0xffffff, 0.6);
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
        // Lớp chiều sâu là bản sao VÔ HÌNH của khối; để nó bắt chuột thì một
        // cú bấm vào cạnh sẽ trúng khối trước, và phép chọn đổi hành vi vì
        // một chi tiết trình bày.
        .filter((h) => !h.object.userData?.chieuSau)
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
        const p3 = v.clone().applyQuaternion(qRef.current).project(cam);
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

      // ── W17 · NHÃN SỐ ĐO — đặt sau nhãn điểm, tránh chúng và các lớp phủ che khung ─────
      // Luật hộp nhãn (§15.5) ở hàm thuần `placeAnnotationLabels`; đây chỉ đo cỡ chữ và chiếu.
      const lopSo = soDoRef.current;
      if (!lopSo) return;
      const hopDiem = dat.filter((d) => giu.has(d.id)).map((d) => ({
        id: d.id, x: d.x - d.el.offsetWidth / 2, y: d.y - 1.4 * d.el.offsetHeight,
        w: d.el.offsetWidth, h: d.el.offsetHeight,
      }));
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
      const daDat = placeAnnotationLabels(canDat,
        [...hopDiem, ...vungCheKhung(renderer.domElement.getBoundingClientRect())], { w, h });
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
      if (typeof window !== "undefined") {
        // Móc ĐO của bộ kiểm trình duyệt (§15.5): hộp nhãn số đo đang hiện + hộp nhãn điểm đang hiện.
        (window as any).__geo3d_annotation_boxes = hopSo;
        // W2 · A: nhãn hợp lệ ở bước này mà không đặt được vì thiếu chỗ.
        (window as any).__geo3d_annotation_unplaced = canDat.filter((c) => !daDat.has(c.id)).map((c) => c.id);
        (window as any).__geo3d_point_label_boxes = hopDiem;
      }
    };

    let song = true;
    const vong = () => {
      if (!song) return;
      dieuKhien.update();
      cam.updateMatrixWorld();
      datCoDauDinh(goc, cam, renderer.domElement.clientWidth || 1,
        renderer.domElement.clientHeight || 1);
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
        const coXoay = !(qRef.current.x === 0 && qRef.current.y === 0 && qRef.current.z === 0);
        (window as any).__geo3d_camera_snapshot = {
          position: cam.position.toArray(),
          // Bộ đo chiếu TOẠ ĐỘ CẢNH: khi có phép xoay hiển thị (đáy nghiêng, §18.2), ma trận phát là view × model để
          // phép chiếu của bộ đo trùng hình trên khung. Đáy ngang ⇒ đúng ma trận view như trước (không nhân).
          view_matrix_column_major: [...(coXoay
            ? new THREE.Matrix4().multiplyMatrices(cam.matrixWorldInverse, goc.matrixWorld)
            : cam.matrixWorldInverse).elements],
          // Cảnh → thế giới (chỉ khi có xoay): bộ đo mô phỏng cử chỉ quỹ đạo trong khung THẾ GIỚI (`cameraSauCuChi`).
          ...(coXoay ? { model_matrix_column_major: [...goc.matrixWorld.elements] } : {}),
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
      renderer.render(scene3, cam);
      chieuNhan();
      requestAnimationFrame(vong);
    };
    veRef.current = () => renderer.render(scene3, cam);
    // Móc ĐO của cổng ảnh `SECTION_FILL_DISTINGUISHABLE` — chỉ harness gọi, người học không
    // thấy (mặc định bật). Tắt/bật phần tô rồi vẽ lại ĐÚNG khung hình này; trả tên các vật
    // đã chạm — rỗng thì không có gì để đo, cổng phải tự đỏ.
    (window as any).__geo3d_set_section_fill_visible = (on: boolean) => {
      const ten = datHienToThietDien(goc, on);
      renderer.render(scene3, cam);
      return ten;
    };

    // ── ĐẶT KHUNG NHÌN CHO VỪA HÌNH ────────────────────────────────────
    //
    // Đọc hộp bao của những gì ĐANG dựng trong nhóm gốc, không đọc `scene` —
    // ẩn/cô lập/tách khối đều đã phản ánh vào nhóm, nên một nguồn là đủ.
    vuaKhungRef.current = () => {
      const diem = diemKhungNhin(goc);
      // Cảnh CHỈ có mặt phẳng/đường thẳng: thà lấy hộp bao đầy đủ còn hơn
      // không đặt được khung nhìn nào.
      if (diem.length === 0) {
        const hop = new THREE.Box3().setFromObject(goc);
        if (!hop.isEmpty()) diem.push([hop.min.x, hop.min.y, hop.min.z], [hop.max.x, hop.max.y, hop.max.z]);
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
      for (const p of diemHuuHan(scene.objects)) diem.push(xoay(p, qRef.current));
      if (diem.length === 0) return;
      const w = renderer.domElement.clientWidth || 1;
      const h = renderer.domElement.clientHeight || 1;
      // Hướng nhìn chọn theo số đo của TOÀN cảnh (cùng lẽ trên: hình cuối),
      // không theo tên bài — xem `chonHuongNhin`. Cảnh không cạnh ⇒ khung cũ.
      // Cấu trúc đo trong khung THẾ GIỚI (sau phép xoay hiển thị): hướng nhìn chọn cho hình người học thấy.
      const ct0 = cauTrucGocNhin(scene.objects);
      const ct = { ...ct0, diem: ct0.diem.map((p) => xoay(p, qRef.current)) };
      const kn = ct.canh.length > 0
        ? khungNhinSuPham(diem, [], [], cam.fov, w / h, chonHuongNhin(ct.diem, ct.canh, ct.mat))
        : khungNhinVua(hopBaoCuaDiem(diem), cam.fov, w / h);
      if (!kn) return;   // đầu vào không dùng được ⇒ giữ nguyên khung nhìn
      datKhungNhin(cam, dieuKhien, kn);
    };

    vong();

    return () => {
      song = false;
      renderer.domElement.removeEventListener("pointerdown", xuongTay);
      renderer.domElement.removeEventListener("pointerup", nhacTay);
      window.removeEventListener("resize", chinhCo);
      roKhung?.disconnect();
      dieuKhien.dispose();
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
        const m = x as THREE.Line;
        m.geometry?.dispose?.();
        (m.material as THREE.Material | undefined)?.dispose?.();
      });
    }
    const ds = witnessesShown(scene, nhanSoDo);
    for (const w of ds) nhom.add(vatNhanChung(w));
    if (typeof window !== "undefined") (window as any).__geo3d_witness_ids = ds.map((w) => w.id);
    veRef.current?.();
  }, [scene, nhanSoDo]);

  // W2 · F — LƯỚI NỀN tuỳ chọn: mảnh, nhạt, nằm dưới đáy hình (mặt z thấp nhất của cảnh), ô theo cỡ cảnh — không
  // số toạ độ, không đơn vị. Bật/tắt chỉ thêm/bớt nhóm này rồi vẽ lại một khung: camera, bước, lựa chọn không đổi.
  useEffect(() => {
    const nhom = luoiRef.current;
    if (!nhom) return;
    for (const con of [...nhom.children]) {
      nhom.remove(con);
      const l = con as THREE.LineSegments;
      l.geometry?.dispose?.();
      (l.material as THREE.Material | undefined)?.dispose?.();
    }
    // Lưới nằm dưới hình NGƯỜI HỌC THẤY: lấy toạ độ sau phép xoay hiển thị (nhóm lưới không xoay).
    const diem = diemHuuHan(scene.objects).map((p) => xoay(p, qHienThi));
    if (gridShown && diem.length > 0) {
      const lo = [0, 1, 2].map((i) => Math.min(...diem.map((p) => p[i])));
      const hi = [0, 1, 2].map((i) => Math.max(...diem.map((p) => p[i])));
      const canh = Math.max(hi[0] - lo[0], hi[1] - lo[1], 1) * 2;
      const l = new THREE.GridHelper(canh, 16, 0xc8cdd3, 0xdde1e5);
      l.rotation.x = Math.PI / 2;             // GridHelper nằm trong XZ; trục lên của bài là z
      // Hạ lưới một chút dưới đáy: nằm đúng mặt đáy thì tranh độ sâu với mặt đáy (nhấp nháy).
      l.position.set((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2] - canh * 0.002);
      const m = l.material as THREE.Material;
      m.transparent = true;
      m.opacity = 0.55;
      m.depthWrite = false;
      l.raycast = () => {};
      nhom.add(l);
    }
    if (typeof window !== "undefined") (window as any).__geo3d_grid_visible = nhom.children.length > 0;
    veRef.current?.();
  }, [scene, gridShown, qHienThi]);

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
    const noiBat = tapNoiBat;
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
    const anPhu = auxiliaryHiddenAt(scene, buoc, auxiliaryShown, tuongTac.selected_id ?? null);
    const seDung = hienTai.filter((o) => isVisible(tuongTac, o.id, daTonTai) && veTrenKhung(o) && !anPhu.has(o.id));
    const nhuong = doanNhuongCanh(seDung,
      (id) => visualTransformOf(tuongTac, scene, id).translate.join(","));
    for (const o of seDung) {
      const progress = progressById.get(o.id);
      let renderObject = nhuong.has(o.id) ? { ...o, display_role: "hit_proxy" } as SceneObject : o;
      if (o.type === "section" && progress && o.polygon) {
        const theoBuoc = vatThietDienTaiBuoc(o, progress);
        if (!theoBuoc) continue;
        renderObject = theoBuoc;
      }
      const obj = buildObject3D(renderObject, tang ? tang.get(o.id) ?? false : noiBat.has(o.id),
        banKinhBamDiem(KHOANG_CAM_MAC_DINH), diemNen, undefined, canonicalHighlights, khucToSang);
      if (!obj) continue;
      if (tang && !tang.has(o.id)) lamDiu(obj);   // ngoài chuỗi nhân quả
      const bd = visualTransformOf(tuongTac, scene, o.id);
      datViTriTrinhBay(obj, bd);
      goc.add(obj);
      daDung.push(renderObject.polygon && o.type === "section"
        ? `${o.id}#${renderObject.polygon.length}${renderObject.closed ? "c" : ""}`
          + `${renderObject.fill_visible ? "f" : ""}` : o.id);
      // Chỉ ĐIỂM mang nhãn. Gắn nhãn cho cạnh và mặt nữa thì một tứ diện đã
      // có 19 chữ chồng lên nhau, và hình thành một mớ chữ có hình.
      if (o.type === "point3" && o.xyz) {
        const [x, y, z] = toVec3(o.xyz);
        viTriNhan.current.set(o.id, new THREE.Vector3(
          x + bd.translate[0], y + bd.translate[1], z + bd.translate[2]));
      }
    }
    if (typeof window !== "undefined") {
      (window as any).__geo3d_rendered_object_ids = daDung;
      (window as any).__geo3d_auxiliary_hidden_ids = [...anPhu].sort();
      (window as any).__geo3d_causal_tiers = tang ? Object.fromEntries(tang) : null;
    }
    veRef.current?.();
  }, [scene, buoc, tuongTac, tapNoiBat, tang, auxiliaryShown]);

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
  const nhanDiem = hien.filter(
    (o) => o.type === "point3"
      && veTrenKhung(o)
      && kyHieu(o) !== null
      && isVisible(tuongTac, o.id, new Set(hien.map((x) => x.id))),
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
                className={`geo3d-label${
                  tuongTac.selected_id === o.id ? " la-chon" : tang && !tang.has(o.id) ? " la-diu" : ""
                }`}
                data-uu-tien={uuTienNhan(o, tuongTac.selected_id)}
                title={o.label}
              >
                {kyHieu(o)}
              </span>
            ))}
          </div>
          {/* W17 · SỐ ĐO TRÊN HÌNH. W12 gỡ dải số nổi vì một con số không chủ thể đặt ở đâu cũng
              vô nghĩa. Nhãn ở đây khác ở đúng chỗ ấy: mỗi nhãn đứng cạnh CHỦ THỂ backend gắn
              (đoạn, miền, khối, điểm của cặp, nhân chứng), chỉ từ bước đại lượng khả dụng.
              W18 §16.5: mặc định chỉ dữ kiện; nhãn là NÚT (bấm/Enter/Space ⇒ chọn đại lượng, chi
              tiết mở ở ô soi), nên lớp này không còn giấu khỏi trình đọc màn hình. */}
          <div ref={soDoRef} className="geo3d-so-do-lop" aria-label="Số đo trên hình">
            {nhanSoDo.map((a) => {
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
