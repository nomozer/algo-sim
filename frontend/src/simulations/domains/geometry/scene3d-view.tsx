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
  khungMatPhang,
  khungDuongThang,
  narrationAt,
  objectsAt,
  stepCount,
  tienTrinhDung,
  type TienTrinhDung,
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
import { canhThietDien, entitiesPresentAt, parentSolidOf } from "./scene3d-subentities";
import {
  BAN_KINH_NHIN,
  KHOANG_CAM_MAC_DINH,
  banKinhBamDiem,
  hangCuThe,
  nguongBamCanh,
} from "./pick-target";
import {
  kyHieu,
  kyHieuHinh,
  locNhanChongNhau,
  uuTienNhan,
  veTrenKhung,
} from "./scene3d-presentation";
import {
  hopBaoCuaDiem, khungNhinVua, phuongViCuaPhapTuyen, huongNhin,
  PHUONG_VI_DO, DO_CAO_DO, HUONG_LEN_HINH_HOC,
} from "./scene3d-camera";
import {
  BE_DAY_PX, taoNet, taoVatLieuNet, capNhatDoPhanGiai, tiLeDiemAnh,
} from "./scene3d-wide-line";
import { duongBaoKhoiCong, type LoaiKhoiCong } from "./scene3d-silhouette";
import { DIEM_PX_D2, DO_MO_D2, MAU_D2 } from "./scene3d-tokens";

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
/**
 * Bảng màu — NGÔN NGỮ HÌNH HỌC, duyệt 2026-09-11 sau vòng mockup tĩnh.
 *
 * Luật của bảng này: mỗi màu mang MỘT vai, và vai đọc được mà không cần chú
 * giải. Bản trước gán màu theo *nguồn gốc* của vật (điểm tự do xanh, điểm dẫn
 * xuất đỏ) — một phân biệt đúng về kỹ thuật nhưng vô nghĩa với người học, và
 * nó tiêu mất hai màu mạnh nhất cho thứ không ai hỏi. Bản này gán theo VAI
 * TRONG HÌNH: cạnh thấy, cạnh khuất, thiết diện, đường dựng, mặt phẳng.
 *
 * ⚠️ `line` và `section` từng là MỘT (`MAU.line` dùng cho cả đường thẳng dựng
 * lẫn đường tròn/elip thiết diện). Gộp hai vai vào một màu là lý do thiết diện
 * của `p3`/`p6` đọc ngang hàng với một đường phụ.
 */
const MAU = MAU_D2;

/** Một vectơ đơn vị vuông góc với `n`. Chỉ dùng để chọn CHỖ ĐẶT NHÃN. */
function truc1VuongGoc(n: Vec3): Vec3 {
  const l = Math.hypot(...n) || 1;
  const u: Vec3 = [n[0] / l, n[1] / l, n[2] / l];
  const t: Vec3 = Math.abs(u[2]) < 0.9 ? [0, 0, 1] : [1, 0, 0];
  const e: Vec3 = [
    t[1] * u[2] - t[2] * u[1],
    t[2] * u[0] - t[0] * u[2],
    t[0] * u[1] - t[1] * u[0],
  ];
  const m = Math.hypot(...e) || 1;
  return [e[0] / m, e[1] / m, e[2] / m];
}

/** Điểm: một màu duy nhất. Nguồn gốc vật KHÔNG phải thông tin của người học. */
const MAU_DIEM = MAU.mesh;

/**
 * Độ mờ của các MẢNG TÔ, theo token đã duyệt ở vòng mockup tĩnh.
 *
 * Ba con số này là một thang bậc, không phải ba lựa chọn rời: thiết diện là
 * tiêu điểm nên đậm gấp đôi; mặt phẳng và thân khối là nền nên phải nhạt tới
 * mức không nuốt được đường nằm sau chúng. Đặt tên để lần sau ai đổi một số
 * thì thấy ngay hai số kia.
 */
const SECTION_FILL_OPACITY = DO_MO_D2.thietDien;
const PLANE_OPACITY = DO_MO_D2.matPhang;
const SOLID_OPACITY = DO_MO_D2.khoi;
/** Mảng tô của vật ĐANG ĐƯỢC CHỌN — đậm hẳn lên để thấy mình vừa bấm trúng. */
const FILL_DA_CHON = DO_MO_D2.daChon;
const SECTION_FILL_DA_CHON = DO_MO_D2.thietDienDaChon;

/**
 * Ngưỡng "thiết diện bẹp": `|d̂·n̂|` giữa hướng nhìn và pháp tuyến mặt cắt.
 * Bằng 0 ⇒ hướng nhìn NẰM TRONG mặt cắt ⇒ thiết diện chiếu ra một đoạn thẳng.
 * Tỉ lệ trục ngắn/trục dài của hình chiếu xấp xỉ chính `|d̂·n̂|`, nên ngưỡng
 * đọc thẳng ra được từ ngưỡng "bẹp" 0,12 đã dùng khi đo mockup; lấy 0,15 để
 * có biên.
 */
const NGUONG_BET = 0.15;

/** Xoay ra bao xa khỏi phương vị pháp tuyến khi guard nổ. */
const LECH_KHOI_PHAP_TUYEN_DO = 55;

/**
 * Khe chừa ở hai cực khi quay (radian, ≈ 0,29°).
 *
 * Tại cực, hướng nhìn trùng trục `up`: hệ toạ độ cầu suy biến, phương vị mất
 * nghĩa và `lookAt` không còn xác định được chiều "lên" của ảnh. Chừa một khe
 * nhỏ thì góc nhìn từ **đỉnh** và từ **đáy** vẫn tới được — chỉ đúng điểm kỳ
 * dị là không.
 */
const EPSILON_CUC = 0.005;

/**
 * Mặt cắt có bị nhìn nghiêng cạnh ở phương vị `phuongViDo` không.
 *
 * ⚠️ Phép so phải là **ba chiều**. Bản đầu so hiệu PHƯƠNG VỊ với 90°, và một
 * ca tổng hợp đã bác nó ngay: với pháp tuyến `(−0,705; 0; 1)` nhìn từ
 * `−55°/22°`, thiết diện chiếu ra tỉ lệ trục **0** — bẹp tuyệt đối — trong khi
 * hiệu phương vị là **125°**, cách 90° tới 35° nên guard đã KHÔNG nổ. Hiệu
 * phương vị chỉ đúng khi cả hướng nhìn lẫn pháp tuyến đều nằm ngang.
 */
export function matCatBet(
  n: [number, number, number], phuongViDo: number,
): boolean {
  const d = huongNhin(phuongViDo, DO_CAO_DO);
  const dai = Math.hypot(n[0], n[1], n[2]);
  if (!Number.isFinite(dai) || dai < 1e-9) return false;
  const cos = (d[0] * n[0] + d[1] * n[1] + d[2] * n[2]) / dai;
  return Math.abs(cos) < NGUONG_BET;
}

/**
 * Pháp tuyến của mặt cắt trong cảnh, hoặc `null` khi cảnh không có mặt cắt.
 * Ưu tiên pháp tuyến của chính thiết diện; không có thì lấy của mặt phẳng.
 */
function phapTuyenMatCat(scene: Scene3D): [number, number, number] | null {
  const co = (o: SceneObject) => Array.isArray(o.normal) && o.normal.length === 3;
  const td = scene.objects.find((o) =>
    (o.type === "ellipse3" || o.type === "circle3") && co(o));
  const mp = scene.objects.find((o) => o.type === "plane3" && co(o));
  const nguon = td ?? mp;
  if (!nguon?.normal) return null;
  const n = toVec3(nguon.normal);
  return n.every(Number.isFinite) ? n : null;
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
const THU_TU_VE_THIET_DIEN = 10;

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

/** Thứ tự vẽ: khối tô bóng → lớp chiều sâu → đường → thiết diện. */
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
  /* Màu phần KHUẤT. Mặc định trùng màu phần thấy — giữ đúng hành vi cũ cho
     thiết diện, nơi cả hai phần phải cùng một màu để đọc ra "cùng một vật".
     Cạnh khối thì truyền màu xám riêng: khuất là một VAI, không phải một bản
     mờ của cạnh thấy. */
  mauKhuat = mau,
  /* Bề dày THEO VAI, pixel CSS. Mặc định là vai "cạnh khối"; nơi gọi nào có
     vai khác (thiết diện, đường dựng, viền mặt phẳng) thì truyền tường minh.
     ⚠️ Trước bản này cả ba vai đều vẽ ra 1 px vì WebGL bỏ qua `linewidth` của
     `LineBasicMaterial` — xem `scene3d-wide-line.ts`. */
  beDay: { thay: number; khuat: number }
    = { thay: BE_DAY_PX.canhThay, khuat: BE_DAY_PX.canhKhuat },
): THREE.Group {
  const nhom = new THREE.Group();

  const thay = taoNet(g, duongThang, taoVatLieuNet({
    mau, beDayPx: beDay.thay, depthFunc: THREE.LessEqualDepth,
  }));
  thay.renderOrder = THU_TU_DUONG;
  thay.name = `${ten}:thay`;
  nhom.add(thay);

  const khuat = taoNet(g, duongThang, taoVatLieuNet({
    mau: mauKhuat, beDayPx: beDay.khuat,
    dut: true, chuKy,
    /* ⚠️ KHÔNG `opacity` — nét khuất là xám ĐẶC, không phải bản mờ của nét
     * thấy. Lý do là THỊ GIÁC: mockup đã duyệt vẽ nó đặc, và một nét 1,6 px
     * mờ 0,75 trên nền sáng đọc gần như biến mất.
     *
     * ⚠️ KHÔNG phải lý do hiệu năng. Giả thuyết ban đầu là bỏ `transparent`
     * sẽ rút nét khỏi hàng đợi trong suốt và rẻ đi; đo lại thì p95 ở 390×844
     * đi từ 12,1 lên 12,6 ms — tức KHÔNG giảm. Ghi lại ở đây để lần sau không
     * ai đi tối ưu theo hướng này nữa. */
    depthFunc: THREE.GreaterDepth, depthWrite: false,
  }));
  khuat.renderOrder = THU_TU_DUONG;
  khuat.name = `${ten}:khuat`;
  nhom.add(khuat);
  return nhom;
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
  /**
   * Người học ĐÃ BẤM CHỌN vật này (hoặc nó thuộc tập phụ thuộc của vật đang
   * chọn). Đây là trạng thái **tương tác**, không phải vai ngữ nghĩa.
   *
   * ⚠️ Tham số này từng tên `noiBat` và nơi gọi nhét cả `highlightedAt(scene,
   * buoc)` vào — tức "vật vừa dựng ở bước này". Hai khái niệm bị gộp, và hậu
   * quả là mặt phẳng cùng các điểm của bước hiện tại tự chuyển xanh khi chưa
   * ai bấm gì. Giữ tên này đúng nghĩa hẹp của nó.
   */
  daChonVat: boolean,
  banKinhBam = banKinhBamDiem(KHOANG_CAM_MAC_DINH),
  /**
   * Điểm CÓ BIÊN của cả cảnh — chỉ mặt phẳng dùng tới, để cắt phần đáng vẽ ra
   * khỏi một mặt phẳng vô hạn. Mặc định rỗng ⇒ rơi về cỡ cố định, nên mọi nơi
   * gọi cũ (test, ô soi) giữ nguyên hành vi.
   */
  diemNen: Vec3[] = [],
  /**
   * Tiến trình DỰNG của vật tại bước đang xem — chỉ thiết diện dùng tới.
   *
   * Mặc định `null` ⇒ dựng trọn hình, đúng hành vi cũ, nên mọi nơi gọi cũ
   * (test, ô soi) không đổi. Xem `tienTrinhDung` ở `scene3d-model.ts`.
   */
  tienTrinh: TienTrinhDung | null = null,
): THREE.Object3D | null {
  const mau = daChonVat ? MAU.highlight : undefined;

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
      color: mau ?? MAU_DIEM,
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
    /* Cắt đoạn đại diện quanh vùng hình học của cảnh thay vì dùng một nửa
     * chiều dài cố định — nếu không, ở p1 đường BD chạy thẳng ra khỏi mép
     * canvas, còn ở cảnh to hơn thì đoạn lại ngắn hơn vật nó đi qua. */
    const khungDt = khungDuongThang(toVec3(o.point), toVec3(o.direction), diemNen);
    const nuaDai = khungDt ? khungDt.nua : LINE_DISPLAY_HALF_LENGTH;
    const tamDt = khungDt ? new THREE.Vector3(...khungDt.tam) : p;
    const a = tamDt.clone().addScaledVector(d, -nuaDai);
    const b = tamDt.clone().addScaledVector(d, nuaDai);
    const g = new THREE.BufferGeometry().setFromPoints([a, b]);
    const duong = duongHaiLuot(g, mau ?? MAU.line,
      beDayNet(diemNen, 1) / SECTION_STROKE_RATIO * NET_DUT_TI_LE,
      `line:${o.id}`, true, mau ?? MAU.line,
      { thay: BE_DAY_PX.duongDung, khuat: BE_DAY_PX.duongDung });
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
      opacity: daChonVat ? FILL_DA_CHON : PLANE_OPACITY,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    const mesh = new THREE.Mesh(g, m);
    /* VIỀN MIẾNG — mockup đã duyệt có nó, bản trước thì không.
     * Mảng tô 0,07 là quá nhạt để đọc ra đâu là mép miếng, nên mặt phẳng hiện
     * ra như một vệt sáng không biên. Viền 1,2 px cùng màu vai đủ để thấy mép
     * mà không tranh chấp với cạnh khối 2,8 px. */
    const b = canh / 2;
    const gVien = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-b, -b, 0), new THREE.Vector3(b, -b, 0),
      new THREE.Vector3(b, b, 0), new THREE.Vector3(-b, b, 0),
      new THREE.Vector3(-b, -b, 0),
    ]);
    const vien = taoNet(gVien, true, taoVatLieuNet({
      mau: mau ?? MAU.surface, beDayPx: BE_DAY_PX.vienMatPhang,
      depthWrite: false,
    }));
    vien.name = `plane-vien:${o.id}`;
    const nhomMP = new THREE.Group();
    nhomMP.add(mesh);
    nhomMP.add(vien);
    const n = new THREE.Vector3(...toVec3(o.normal)).normalize();
    nhomMP.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), n);
    nhomMP.position.set(...(khung ? khung.tam : toVec3(o.point)));
    // Mặt phẳng VÔ HẠN: miếng vẽ ra là đại diện do tầng trình bày chọn cỡ, nên
    // nó KHÔNG được tham gia tính khung nhìn — xem `vuaKhungRef`.
    nhomMP.userData.voHan = true;
    mesh.userData.voHan = true;
    vien.userData.voHan = true;
    return v(nhomMP, `plane:${o.id}`);
  }

  if (o.render === "circle" && o.center && o.normal && o.radius_sq) {
    // Chia lưới CHỈ ĐỂ VẼ. `radius_sq` là số chính xác backend gửi; căn bậc
    // hai lấy ở ĐÂY, tại biên hiển thị — không sớm hơn một tầng nào.
    const r = Math.sqrt(Math.max(0, toNumber(o.radius_sq)));
    const day = beDayNet(diemNen, r);
    const trong = Math.max(0, r - day / 2), ngoai = r + day / 2;
    const chungVanh = {
      color: mau ?? MAU.section, side: THREE.DoubleSide,
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
          ...chungVanh, color: mau ?? MAU.sectionKhuat,
          depthFunc: THREE.GreaterDepth, depthWrite: false,
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
      color: mau ?? MAU.section, side: THREE.DoubleSide,
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
      ...chungVanh, color: mau ?? MAU.sectionKhuat,
      depthFunc: THREE.GreaterDepth, depthWrite: false,
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
      color: mau ?? MAU.surface,
      transparent: true,
      opacity: daChonVat ? FILL_DA_CHON : SOLID_OPACITY,
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

    /* ─── ĐƯỜNG BAO — thứ làm nên hình dáng của mặt trơn ───────────────────
     *
     * `EdgesGeometry` vô dụng ở đây: mặt trơn không có cạnh thật. Trước bản
     * này p4/p5 dựng ra một vệt xám **không một nét nào** — không vành, không
     * đường sinh, không trục. Xem `scene3d-silhouette.ts`.
     *
     * Vành là hình học cố định (hai lượt chiều sâu lo phần khuất); hai đường
     * sinh bao và đường bao mặt cầu đổi theo camera nên `capNhat` chạy trong
     * vòng vẽ. Tham chiếu gắn vào `userData` để vòng vẽ tìm được mà không cần
     * một sổ đăng ký riêng. */
    const bao = duongBaoKhoiCong(
      { kind: o.curved_kind as LoaiKhoiCong, tam, dinh, r, h },
      { thay: mau ?? MAU.mesh, khuat: mau ?? MAU.khuat },
      beDayNet(diemNen, r) / SECTION_STROKE_RATIO * NET_DUT_TI_LE,
      o.id,
    );
    if (bao) {
      nhomCong.add(bao.nhom);
      nhomCong.userData.capNhatBao = bao.capNhat;
    }

    /* TRỤC OK / OS — hai đầu mút đều CÓ SẴN trong payload (`anchor` và
     * `apex_or_top`), nên vẽ đoạn nối chúng không phát minh dữ liệu nào. Nhãn
     * thì ghép từ nhãn của hai điểm đã có trong cảnh; nơi gọi lo việc ấy. */
    if (dinh) {
      const gTruc = new THREE.BufferGeometry().setFromPoints([tam, dinh]);
      /* ⚠️ HAI LƯỢT, không một lượt. Trục nằm TRỌN trong lòng khối, nên một
       * lượt `LessEqualDepth` không bao giờ vẽ được nét nào: lớp chiều sâu của
       * khối luôn đứng trước nó. Triệu chứng đo được ở p4 — nhãn "OK" hiện lên
       * giữa hình mà không có đường nào dưới chữ. Lượt `GreaterDepth` mới là
       * lượt vẽ ra nó, đúng vai một đường dựng bị che. */
      const truc = duongHaiLuot(gTruc, mau ?? MAU.line,
        beDayNet(diemNen, r) / SECTION_STROKE_RATIO * NET_DUT_TI_LE,
        `truc:${o.id}`, true, mau ?? MAU.line,
        { thay: BE_DAY_PX.duongDung, khuat: BE_DAY_PX.duongDung });
      nhomCong.add(truc);
    }
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
      color: mau ?? MAU.mesh,
      transparent: true,
      opacity: daChonVat ? FILL_DA_CHON : SOLID_OPACITY,
      side: THREE.DoubleSide,
      depthWrite: false,
    })));
    // Lớp chiều sâu: chính khối này che các cạnh nằm sau nó.
    nhom.add(lopChieuSau(g));
    // Khung cạnh: khối trong suốt mà không có khung thì đọc ra một vệt mờ.
    // Hai lượt ⇒ cạnh khuất thành nét đứt, cập nhật theo camera.
    nhom.add(duongHaiLuot(new THREE.EdgesGeometry(g), mau ?? MAU.mesh,
      beDayNet(diemNen, 1) / SECTION_STROKE_RATIO * NET_DUT_TI_LE,
      `canh:${o.id}`, false, mau ?? MAU.khuat));
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
      opacity: daChonVat ? SECTION_FILL_DA_CHON : SECTION_FILL_OPACITY,
      side: THREE.DoubleSide,
      depthWrite: false,
    })), `face:${o.id}`);
  }

  if (o.type === "edge" && o.polygon && o.polygon.length === 2) {
    const g = new THREE.BufferGeometry().setFromPoints(
      o.polygon.map((x) => new THREE.Vector3(...toVec3(x))));
    return v(taoNet(g, true, taoVatLieuNet({
      mau: mau ?? MAU.line, beDayPx: BE_DAY_PX.duongDung,
    })), `edge:${o.id}`);
  }

  if (o.render === "polygon" && (o.polygon || o.vertices)) {
    const pts = (o.polygon ?? o.vertices ?? []).map(toVec3)
      .map((p) => new THREE.Vector3(...p));
    if (pts.length < 2) return null;
    const vong = o.closed === false ? pts : [...pts, pts[0]];
    const g = new THREE.BufferGeometry().setFromPoints(vong);
    /* THIẾT DIỆN đi hai lượt như mọi đường nằm trên khối: phần bị khối che
     * phải đọc ra là khuất. Bản trước vẽ nó bằng MỘT `THREE.Line` liền, nên
     * cạnh sau của thiết diện `p1` hiện y hệt cạnh trước — hình mất đúng câu
     * trả lời "đoạn này nằm trước hay sau khối". Đa giác KHÔNG phải thiết diện
     * (đáy, mặt được nêu tên) giữ vai phụ và giữ màu xám. */
    if (o.type === "section") {
      const nhom = new THREE.Group();
      /* ─── DỰNG LUỸ TIẾN: đúng số cạnh mà trace đã nối tới bước này ──────
       *
       * `tienTrinh.soCanh === null` ⇒ vật không dựng luỹ tiến, rơi xuống lối
       * cũ bên dưới. Có luỹ tiến mà chưa đóng hình ⇒ vẽ từng đoạn RỜI
       * (`duongThang = false`), vì các cạnh chưa khép thành một chu trình.
       * Khi đã đóng hình thì đi đúng lối cũ — nhờ vậy khung hình CUỐI giống
       * hệt trước bản này, từng điểm ảnh.
       *
       * Cạnh lấy từ `canhThietDien` — cùng thẩm quyền với cây phân rã, không
       * dựng một phép suy hình học thứ hai. */
      const luyTien = tienTrinh?.soCanh ?? null;
      if (luyTien !== null && !tienTrinh?.daDong) {
        const canh = canhThietDien(o).slice(0, luyTien);
        if (canh.length === 0) return null;      // chưa nối cạnh nào ⇒ chưa có gì để vẽ
        const doan: THREE.Vector3[] = [];
        for (const c of canh) {
          doan.push(new THREE.Vector3(...toVec3(c.a)), new THREE.Vector3(...toVec3(c.b)));
        }
        const gDoan = new THREE.BufferGeometry().setFromPoints(doan);
        nhom.add(duongHaiLuot(gDoan, mau ?? MAU.section,
          beDayNet(diemNen, 1) / SECTION_STROKE_RATIO * NET_DUT_TI_LE,
          `polygon:${o.id}`, false, mau ?? MAU.sectionKhuat,
          { thay: BE_DAY_PX.thietDienThay, khuat: BE_DAY_PX.thietDienKhuat }));
        return v(nhom, `polygon:${o.id}`);
      }
      /* NỀN THIẾT DIỆN — mockup đã duyệt có nó, renderer thì chưa.
       *
       * Trước bản này KHÔNG thiết diện nào có nền: đa giác (p1) vẽ bằng một
       * đường khép kín, tròn/elip (p3/p6/p7) vẽ bằng vành. Miếng cắt vì thế
       * đọc ra như một khung dây lơ lửng chứ không ra một MẶT — so với
       * `mockup/p1-mockup.png` thì thiếu hẳn mảng tô cam nhạt.
       *
       * Ở đây mới lấp cho đa giác. Thiết diện tròn/elip vẫn chỉ có vành: nền
       * cho chúng cần một hình quạt/elip đặc và một lượt đo riêng, không gộp
       * vào đây. `depthWrite: false` để nền không nuốt cạnh khuất nằm sau. */
      if (pts.length >= 3 && o.closed !== false) {
        const gNen = new THREE.BufferGeometry();
        const p3 = pts.map((p) => [p.x, p.y, p.z] as Vec3);
        const pos: number[] = [];
        for (const [a, b, c] of chiaTamGiac(p3)) {
          for (const j of [a, b, c]) pos.push(...p3[j]);
        }
        gNen.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
        gNen.computeVertexNormals();
        nhom.add(new THREE.Mesh(gNen, new THREE.MeshStandardMaterial({
          color: mau ?? MAU.section,
          transparent: true,
          opacity: daChonVat ? SECTION_FILL_DA_CHON : SECTION_FILL_OPACITY,
          side: THREE.DoubleSide,
          depthWrite: false,
        })));
      }
      /* Phần KHUẤT của thiết diện có vai màu RIÊNG (`sectionKhuat`). Bảng cũ
       * để nó trùng màu phần thấy, nên hình mất đúng câu trả lời "đoạn này
       * nằm trước hay sau khối" — ở chính cái hình mà bài đang hỏi. */
      nhom.add(duongHaiLuot(g, mau ?? MAU.section,
        beDayNet(diemNen, 1) / SECTION_STROKE_RATIO * NET_DUT_TI_LE,
        `polygon:${o.id}`, true, mau ?? MAU.sectionKhuat,
        { thay: BE_DAY_PX.thietDienThay, khuat: BE_DAY_PX.thietDienKhuat }));
      return v(nhom, `polygon:${o.id}`);
    }
    return v(taoNet(g, true, taoVatLieuNet({
      mau: mau ?? MAU.polygon, beDayPx: BE_DAY_PX.duongDung,
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
  //: Người dùng đang xoay/pan/zoom bằng chuột. Khớp khung phải nhường.
  const dangKeoRef = useRef(false);
  //: Người dùng ĐÃ TỪNG tương tác. Từ lúc ấy khung nhìn thuộc về họ, và một
  //: lần đổi cỡ khung không được giành lại nó.
  const daTuongTacRef = useRef(false);
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
    /* ⚠️ THỨ TỰ VÒNG ĐỜI, KHÔNG PHẢI SỞ THÍCH — xem `HUONG_LEN_HINH_HOC`.
     *
     *   camera dựng → ĐẶT up → dựng OrbitControls → khớp khung → người dùng kéo
     *
     * `OrbitControls` chụp `object.up` một lần trong hàm dựng và không có
     * đường làm tươi. Đặt `up` sau constructor thì controls quay quanh Y còn
     * `lookAt` dựng tư thế theo Z: trục quay trôi mỗi khung, và cùng một cú kéo
     * chỉ quay được ~60 % biên độ. Đo được ở `truc/` — chuẩn trục 0,608–0,680
     * khi đặt muộn, 1,000 khi đặt ở đây. Khoá bằng
     * `scene3d-orbit-lifecycle.test.tsx`. */
    cam.up.set(...HUONG_LEN_HINH_HOC);
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
    /* PHẠM VI QUAY — khai tường minh, không dựa vào mặc định của thư viện.
     *
     * Phương vị KHÔNG chặn: học sinh phải quay được nhiều vòng liên tục để đi
     * hết mặt trước → phải → sau → trái mà không đụng tường vô hình.
     * Cực chừa đúng `EPSILON_CUC`: tại cực, hướng nhìn trùng `up` và hệ toạ độ
     * cầu suy biến (azimuth mất nghĩa) — chừa một khe nhỏ giữ được cả góc nhìn
     * từ đỉnh lẫn từ đáy mà không rơi vào điểm kỳ dị. */
    dieuKhien.minAzimuthAngle = -Infinity;
    dieuKhien.maxAzimuthAngle = Infinity;
    dieuKhien.minPolarAngle = EPSILON_CUC;
    dieuKhien.maxPolarAngle = Math.PI - EPSILON_CUC;
    /* CỜ ĐANG KÉO — bất biến "không tự khớp khung khi người dùng đang xoay".
     *
     * Khớp khung đặt lại cả `position`, `target` và `projectionMatrix`. Chạy
     * giữa một cú kéo thì hình giật về chỗ khác ngay dưới ngón tay. Hiện danh
     * sách phụ thuộc của effect khớp khung không chứa thao tác kéo nên việc ấy
     * chưa xảy ra — cờ này giữ cho nó **không thể** xảy ra khi ai đó thêm một
     * dịp khớp khung mới mà không nghĩ tới tương tác. */
    dieuKhien.addEventListener("start", () => {
      dangKeoRef.current = true;
      daTuongTacRef.current = true;
    });
    dieuKhien.addEventListener("end", () => { dangKeoRef.current = false; });
    container.appendChild(renderer.domElement);

    const chinhCo = () => {
      const w = container.clientWidth || 640;
      const h = container.clientHeight || 420;
      /* ─── ĐỘ PHÂN GIẢI THẬT CỦA MÀN HÌNH ────────────────────────────────
       *
       * `updateStyle = true` là ĐIỀU KIỆN ĐI KÈM của `setPixelRatio`, không
       * phải một tuỳ chọn. Thẻ `<canvas>` không có luật CSS nào ràng cỡ (chỉ
       * `.geo3d-canvas` bao ngoài mới có), nên cỡ bố cục của nó bám theo thuộc
       * tính `width/height`. Giữ `false` như bản trước thì ở DPR 2 canvas
       * phình thành 2636×1220 px CSS trong một khung 1318×610 — đã dựng lại và
       * đo được — và `overflow: hidden` của khung bao GIẤU chỗ vỡ đi, nên nó
       * sẽ ship dưới dạng "hình bị cắt" chứ không dưới dạng một lỗi. */
      renderer.setPixelRatio(tiLeDiemAnh(window.devicePixelRatio));
      renderer.setSize(w, h, true);
      cam.aspect = w / h;
      cam.updateProjectionMatrix();
      /* Bề dày nét tính theo `resolution` của `LineMaterial`, và setter của nó
       * `.copy()` chứ không giữ tham chiếu — nên mọi vật liệu phải được gán
       * lại ở đây. Truyền kích thước **CSS**: xem `scene3d-wide-line.ts` về
       * lý do việc ấy đúng ở mọi `devicePixelRatio`. */
      capNhatDoPhanGiai(scene3, w, h);
    };
    chinhCo();
    window.addEventListener("resize", chinhCo);

    /* ─── DPR ĐỔI GIỮA PHIÊN ─────────────────────────────────────────────
     *
     * Kéo cửa sổ sang màn hình khác, hoặc đổi mức thu phóng của hệ điều hành,
     * làm `devicePixelRatio` đổi mà **`resize` không nhất thiết phát** và kích
     * thước CSS của khung cũng không đổi — nên không ResizeObserver nào bắt
     * được. Khung vẽ khi ấy giữ tỉ lệ cũ và hình hoặc mờ đi hoặc tốn gấp bốn
     * mà không ai biết.
     *
     * `matchMedia("(resolution: Xdppx)")` khớp ĐÚNG giá trị hiện tại, nên khi
     * nó thôi khớp là DPR đã đổi; lúc ấy đăng ký lại ở giá trị mới. */
    let boDpr: (() => void) | null = null;
    const theoDoiDpr = () => {
      const mq = window.matchMedia?.(`(resolution: ${window.devicePixelRatio}dppx)`);
      if (!mq) return;
      const doi = () => { boDpr?.(); chinhCo(); theoDoiDpr(); };
      mq.addEventListener("change", doi, { once: true });
      boDpr = () => mq.removeEventListener("change", doi);
    };
    theoDoiDpr();

    /* ─── KHUNG ĐỔI CỠ SAU KHI GẮN — và khớp khung phải theo kịp ───────────
     *
     * `chinhCo()` chạy ngay lúc gắn, nhưng lúc ấy `container.clientWidth` có
     * thể còn 0 (bố cục chưa xong) ⇒ rơi về `640×420`, tỉ lệ 1,52 thay vì
     * 2,42 thật. Khớp khung chạy sau đó với tỉ lệ sai thì camera lùi quá xa:
     * đo được hình trụ p4 chiếm 0,22 khung thay vì 0,565 — và nó **chập
     * chờn**, cùng một bản dựng lúc đúng lúc sai tuỳ thời điểm bố cục xong.
     * `window.resize` không bắt được vì cửa sổ có đổi cỡ đâu.
     *
     * ⚠️ Chỉ khớp lại khi người dùng CHƯA tương tác. Sau cú kéo đầu tiên,
     * khung nhìn thuộc về người dùng — đổi cỡ cửa sổ không được giành lại nó.
     */
    const doCo = new ResizeObserver(() => {
      chinhCo();
      if (!daTuongTacRef.current) vuaKhungRef.current?.();
    });
    doCo.observe(container);

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

    /* Đường bao của mặt trơn ĐỔI THEO CAMERA, nên phải tính lại trước mỗi lần
     * vẽ. Quét nhóm gốc thay vì giữ một sổ đăng ký: cảnh chỉ vài chục vật, và
     * một sổ đăng ký phải được gỡ tay lúc dựng lại cảnh — quên gỡ là giữ tham
     * chiếu tới vật đã huỷ. `capNhat` KHÔNG cấp phát (xem
     * `scene3d-silhouette.ts`), nên chạy mỗi khung là rẻ. */
    const capNhatBao = () => {
      goc.traverse((vat) => {
        const f = vat.userData?.capNhatBao as ((c: THREE.Vector3) => void) | undefined;
        if (f) f(cam.position);
      });
    };

    let song = true;
    /* ─── CHẤM ĐIỂM CỠ MÀN HÌNH ─────────────────────────────────────────
     *
     * Chấm dựng bằng `SphereGeometry(BAN_KINH_NHIN)` — bán kính trong TOẠ ĐỘ
     * THẾ GIỚI. Hệ quả đo được: cùng một bài, chấm là 10 px ở 1440×900 và
     * 15 px ở 1920×1080; và một bài có toạ độ lớn gấp mười cho chấm nhỏ gấp
     * mười. Cỡ chấm vì thế không phải một quyết định thiết kế mà là hệ quả
     * của đơn vị bài toán.
     *
     * Quy nó về PIXEL: bán kính thế giới cần để chiếu ra `P` px ở khoảng cách
     * `d` là `P·d·tan(fov/2)/H`. `pick-proxy` KHÔNG đụng tới — nó là hình bắt
     * chuột, cỡ của nó là chuyện của ngón tay, không phải của mắt. */
    const _vtDiem = new THREE.Vector3();
    const chinhCoDiem = () => {
      const H = renderer.domElement.clientHeight || 1;
      const k = ((DIEM_PX_D2 / 2) * Math.tan((cam.fov * Math.PI) / 360)) / (H / 2);
      goc.traverse((vat) => {
        if (!vat.name.startsWith("point:")) return;
        /* ĐỘ SÂU TRONG KHÔNG GIAN CAMERA, không phải khoảng cách Euclid tới
         * camera. Cỡ chiếu của một vật dưới phép chiếu phối cảnh tỉ lệ với
         * `1/(−z)` sau khi đổi sang hệ camera; lấy khoảng cách Euclid sẽ
         * phóng to chấm ở rìa khung, nơi hai đại lượng ấy lệch nhau nhiều
         * nhất. Đây cũng là lý do không cần tới hàm đo khoảng cách của
         * `Vector3` — hàm ấy bị guard ở `scene3d.test.tsx` cấm trong file này,
         * và ở đây nó vừa thừa vừa kém đúng. */
        _vtDiem.setFromMatrixPosition(vat.matrixWorld).applyMatrix4(cam.matrixWorldInverse);
        const sau = Math.max(1e-6, -_vtDiem.z);
        const tiLe = (k * sau) / BAN_KINH_NHIN;
        for (const con of vat.children) {
          if (con.name === "pick-proxy") continue;
          con.scale.setScalar(tiLe);
        }
      });
    };

    const vong = () => {
      if (!song) return;
      dieuKhien.update();
      capNhatBao();
      chinhCoDiem();
      renderer.render(scene3, cam);
      chieuNhan();
      requestAnimationFrame(vong);
    };
    veRef.current = () => renderer.render(scene3, cam);

    // ── ĐẶT KHUNG NHÌN CHO VỪA HÌNH ────────────────────────────────────
    //
    // Đọc hộp bao của những gì ĐANG dựng trong nhóm gốc, không đọc `scene` —
    // ẩn/cô lập/tách khối đều đã phản ánh vào nhóm, nên một nguồn là đủ.
    /**
     * GUARD THIẾT DIỆN BẸP — phương vị khung nhìn.
     *
     * Nhìn gần vuông góc với pháp tuyến mặt cắt thì thiết diện chiếu ra một
     * ĐOẠN THẲNG, và bài "tính diện tích thiết diện" mất chính cái hình nó
     * đang hỏi. Khi góc mặc định rơi vào vùng ấy, xoay phương vị về `55°` so
     * với pháp tuyến — đủ xa để không bẹp, đủ gần để vẫn thấy mặt cắt nghiêng.
     *
     * ⚠️ `IMPLEMENTED_NOT_VALIDATED` trên bộ ca thật: đo trên cả bảy ca P1–P7,
     * guard **không kích hoạt lần nào** (p6/p7 lệch 55°, p1/p3 pháp tuyến
     * thẳng đứng nên phương vị không xác định). Nó chỉ được chứng minh bằng
     * một ca TỔNG HỢP dựng riêng — xem báo cáo wave. Không tuyên bố nó đã cải
     * thiện một ca thật nào.
     */
    const phuongViKhung = (): number => {
      const n = phapTuyenMatCat(scene);
      if (!n) return PHUONG_VI_DO;
      const goc = phuongViCuaPhapTuyen(n);
      if (goc === null) return PHUONG_VI_DO;
      return matCatBet(n, PHUONG_VI_DO) ? goc - LECH_KHOI_PHAP_TUYEN_DO : PHUONG_VI_DO;
    };

    vuaKhungRef.current = () => {
      /* Người dùng đang xoay ⇒ NHƯỜNG. Khớp khung đặt lại `position`,
       * `target` và `projectionMatrix`; chạy giữa một cú kéo thì hình giật
       * khỏi ngón tay. Xem cờ `dangKeoRef` ở chỗ dựng controls. */
      if (dangKeoRef.current) return;
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
        if (vat.userData?.voHan || vat.userData?.chieuSau) return;
        /* Đường bao ĐỘNG cũng đứng ngoài: lúc dựng bộ đệm của nó toàn số 0
         * (hộp bao ôm gốc toạ độ), và kể cả khi đã có toạ độ thật thì nó là
         * hệ quả của vị trí camera — để nó quyết định vị trí camera là một
         * vòng lặp phản hồi. Xem `scene3d-silhouette.ts`. */
        if (vat.userData?.baoDong) return;
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
      const kn = khungNhinVua(hopBaoCuaDiem(diem), cam.fov, w / h, phuongViKhung());
      if (!kn) return;   // đầu vào không dùng được ⇒ giữ nguyên khung nhìn
      /* ⚠️ KHÔNG đặt `cam.up` ở đây — đó chính là con bọ đã sửa.
       *
       * `cam.up` được đặt MỘT LẦN lúc dựng camera, trước `new OrbitControls`.
       * Gán lại ở đây thì `OrbitControls._quat` (chụp lúc dựng) lệch khỏi
       * `cam.up` và trục quay trôi. `kn.huongLen` vẫn là cùng một hằng số
       * `HUONG_LEN_HINH_HOC`, nên không có gì để đồng bộ lại. */
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
      boDpr?.();
      doCo.disconnect();
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
    /* ─── CHỌN ≠ VỪA DỰNG. Hai khái niệm, không được gộp làm một. ──────────
     *
     * Bản trước: không có vật nào đang chọn thì rơi về `highlightedAt(scene,
     * buoc)` — tập vật *vừa được dựng ở bước này, kèm phụ thuộc của nó* — rồi
     * tô cả tập ấy bằng `MAU.highlight`. Hệ quả đo được trên sản phẩm thật
     * (`af.mp4`): ở p1 **mặt phẳng (α) hiện màu xanh** và ba trong năm điểm
     * hiện xanh, dù người học chưa bấm vào đâu cả; ở p4/p5 thân khối chuyển
     * xanh đục. Ngôn ngữ thị giác đã duyệt **không có** kênh màu nào cho
     * "vừa dựng" — xem `mockup/p1-mockup.png`, `p4-mockup.png`.
     *
     * Nên `MAU.highlight` chỉ bật khi có `selected_id` THẬT. Không chọn gì thì
     * mọi vật giữ đúng màu VAI của nó: thiết diện đỏ cam, cạnh thấy đen, cạnh
     * khuất xám, mặt phẳng xám nhạt.
     *
     * `highlightedAt` vẫn còn và vẫn đúng việc của nó — chỉ là nó không phải
     * một nguồn MÀU. */
    const daChon = new Set(
      tuongTac?.selected_id ? highlightSet(scene, tuongTac.selected_id) : [],
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
      const obj = buildObject3D(o, daChon.has(o.id),
        banKinhBamDiem(KHOANG_CAM_MAC_DINH), diemNen,
        tienTrinhDung(scene, o.id, buoc));
      if (!obj) continue;
      const bd = visualTransformOf(tuongTac, scene, o.id);
      datViTriTrinhBay(obj, bd);
      goc.add(obj);
      /* Nhãn: ĐIỂM, cộng đúng ba vai hình có ký hiệu (thiết diện, đường
       * tròn, elip) và TRỤC khối cong. Không gắn nhãn cho cạnh và mặt — một
       * tứ diện sẽ có 19 chữ chồng lên nhau và hình thành một mớ chữ có hình. */
      const doi = new THREE.Vector3(...bd.translate);
      const dat = (id: string, v: [number, number, number]) =>
        viTriNhan.current.set(id, new THREE.Vector3(...v).add(doi));
      if (o.type === "point3" && o.xyz) {
        dat(o.id, toVec3(o.xyz));
      } else if (o.type === "section" && o.polygon && o.polygon.length > 0) {
        // Trọng tâm miếng cắt — chỗ mockup đã duyệt đặt chữ "T".
        const pts = o.polygon.map(toVec3);
        dat(o.id, [
          pts.reduce((t, q) => t + q[0], 0) / pts.length,
          pts.reduce((t, q) => t + q[1], 0) / pts.length,
          pts.reduce((t, q) => t + q[2], 0) / pts.length,
        ]);
      } else if (o.render === "circle" && o.center && o.normal && o.radius_sq) {
        // MỘT ĐIỂM TRÊN đường tròn, không phải tâm: tâm của thiết diện `p3`
        // nằm ngay chỗ điểm `I` đã có nhãn, hai chữ sẽ đè nhau.
        const r = Math.sqrt(Math.max(0, toNumber(o.radius_sq)));
        const e = truc1VuongGoc(toVec3(o.normal));
        const c = toVec3(o.center);
        dat(o.id, [c[0] + r * e[0], c[1] + r * e[1], c[2] + r * e[2]]);
      } else if (o.render === "ellipse" && o.center && o.major_dir && o.semi_major_sq) {
        const a = Math.sqrt(Math.max(0, toNumber(o.semi_major_sq)));
        const m = toVec3(o.major_dir);
        const n = Math.hypot(...m) || 1;
        const c = toVec3(o.center);
        dat(o.id, [c[0] + (a * m[0]) / n, c[1] + (a * m[1]) / n,
          c[2] + (a * m[2]) / n]);
      } else if (o.render === "curved_solid" && o.anchor && o.apex_or_top) {
        // TRỤC: giữa đoạn nối hai đầu mút, cả hai đều CÓ SẴN trong payload.
        const a = toVec3(o.anchor), b = toVec3(o.apex_or_top);
        dat(`truc:${o.id}`, [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2]);
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
  const idHien = new Set(hien.map((x) => x.id));
  const thay = (o: SceneObject) => veTrenKhung(o) && isVisible(tuongTac, o.id, idHien);

  /** Một nhãn trên khung: id để tra vị trí, ký hiệu để in. */
  interface MotNhan { id: string; ky: string; uuTien: number; tieuDe: string; laChon: boolean }
  const nhan: MotNhan[] = [];
  for (const o of hien) {
    if (!thay(o)) continue;
    const laChonNay = tuongTac.selected_id === o.id;
    if (o.type === "point3") {
      const k = kyHieu(o);
      if (k !== null) {
        nhan.push({ id: o.id, ky: k, uuTien: uuTienNhan(o, tuongTac.selected_id),
          tieuDe: o.label, laChon: laChonNay });
      }
      continue;
    }
    /* Ba vai HÌNH có ký hiệu — thiết diện, đường tròn, elip. `kyHieuHinh` chỉ
     * nhận `id` khi bản thân `id` ĐÃ LÀ ký hiệu; xem chú thích của nó. */
    if (o.type === "section" || o.render === "circle" || o.render === "ellipse") {
      const k = kyHieuHinh(o);
      if (k !== null && viTriNhan.current.has(o.id)) {
        nhan.push({ id: o.id, ky: k, uuTien: uuTienNhan(o, tuongTac.selected_id),
          tieuDe: o.label, laChon: laChonNay });
      }
      continue;
    }
    /* TRỤC khối cong: ký hiệu ghép từ ký hiệu của HAI ĐIỂM đã có trong cảnh,
     * khớp theo toạ độ. Không có đủ hai điểm ⇒ không in gì — trục vẫn được vẽ,
     * chỉ là nó không có tên trong dữ liệu để mà in. */
    if (o.render === "curved_solid" && o.anchor && o.apex_or_top) {
      const kyTai = (v: Vec3): string | null => {
        for (const d of hien) {
          if (d.type !== "point3" || !d.xyz) continue;
          const q = toVec3(d.xyz);
          if (Math.hypot(q[0] - v[0], q[1] - v[1], q[2] - v[2]) < 1e-9) return kyHieu(d);
        }
        return null;
      };
      const a = kyTai(toVec3(o.anchor));
      const b = kyTai(toVec3(o.apex_or_top));
      const id = `truc:${o.id}`;
      if (a && b && viTriNhan.current.has(id)) {
        nhan.push({ id, ky: `${a}${b}`, uuTien: 0, tieuDe: `Trục ${a}${b}`,
          laChon: false });
      }
    }
  }
  /* Nhãn TRÙNG KÝ HIỆU thì chỉ giữ một. Ở p4 backend phát HAI khối trụ cùng
   * hình (`khối trụ` và `hình trụ`, cùng `anchor`/`apex_or_top`), nên nếu
   * không lọc thì chữ "OK" được in hai lần chồng khít lên nhau — dày lên gấp
   * đôi và trông như lỗi phông. */
  const daCo = new Set<string>();
  const nhanHien = nhan.filter((n) => {
    const khoa = `${n.ky}@${n.id.startsWith("truc:") ? "truc" : n.id}`;
    if (daCo.has(khoa)) return false;
    daCo.add(khoa);
    return true;
  });

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
            {nhanHien.map((n) => (
              <span
                key={n.id}
                data-id={n.id}
                className={`geo3d-label${n.laChon ? " la-chon" : ""}`}
                data-uu-tien={n.uuTien}
                title={n.tieuDe}
              >
                {n.ky}
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
