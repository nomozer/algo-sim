/**
 * scene3d-camera.ts — KHUNG NHÌN, tính từ hộp bao của vật ĐANG THẤY.
 *
 * ─── VÌ SAO TỒN TẠI ───────────────────────────────────────────────────────
 *
 * Bản đầu đặt camera bằng một hằng số (`position.set(6, 5, 8)`) cho mọi bài.
 * Với bài toạ độ nhỏ thì hình chiếm một góc khung; với bài toạ độ lớn thì hình
 * tràn ra ngoài. Ảnh chụp thật cho thấy cả hai kiểu hỏng.
 *
 * ─── HAI LỖI CỦA BẢN THỨ HAI, ĐO ĐƯỢC TRÊN CẢ BẢY CA ─────────────────────
 *
 * Bản thứ hai ôm **cầu ngoại tiếp** hộp bao và hướng nhìn cố định `[6,5,8]`
 * trong hệ của three.js. Vòng dựng mockup tĩnh (2026-09-10/11) đo lại cả bảy
 * ca P1–P7 và cho **0/7 đạt**:
 *
 *  ① **Cầu ngoại tiếp lớn hơn hình.** Cầu lấp 68 % khung ⇒ hình thật chỉ lấp
 *    `0,68/√3 ≈ 39 %` chiều. Đo được: occupancy 0,29–0,47 trên bảy ca.
 *  ② **`up` sai hệ.** Toạ độ bài toán dùng **z** làm chiều cao (`S(0;0;6)`,
 *    trụ `O→K` theo z), nhưng camera dùng `up = (0,1,0)` của three.js và
 *    `toVec3` là ánh xạ đồng nhất — nên **mọi khối nằm nghiêng**. Khối chóp
 *    `p1` đọc ra một tứ giác dẹt, không ra hình chóp.
 *
 * Bản này sửa cả hai: fit theo **hình chiếu** của tám đỉnh hộp bao (không theo
 * cầu ngoại tiếp), và `up` = **trục z của hình học**. Đo lại: **7/7 đạt**,
 * occupancy 0,66–0,685. Bằng chứng: `docs/SCENE3D_VISUAL_LANGUAGE_IMPLEMENTATION.md`.
 *
 * ⚠️ Đây là **phép tính trình bày**, không phải phép tính hình học: đầu vào là
 * các vị trí đã do nhân hình học sinh ra, đầu ra là vị trí camera tính bằng
 * đơn vị thế giới của renderer. Nó không quay lại `Scene3D`, không sinh vật
 * mới, và không đổi một toạ độ nào.
 *
 * ⚠️ **Không tự gọi khi đổi bước.** Khung nhìn phải đứng yên giữa bước k và
 * k+1, nếu không thì hoạt cảnh tua bước biến thành hoạt cảnh đổi góc máy, và
 * người xem không phân biệt được cái nào đang đổi. Chỉ gọi khi: nạp cảnh lần
 * đầu, người dùng bấm xem lại toàn hình, và khi tách/ráp khối làm kích thước
 * hình đổi hẳn.
 */

/** Hộp bao trục, đơn vị thế giới. */
export interface HopBao {
  min: [number, number, number];
  max: [number, number, number];
}

/** Kết quả đặt khung nhìn — vị trí camera, điểm nhìn vào, và trục "lên". */
export interface KhungNhin {
  viTri: [number, number, number];
  nhinVao: [number, number, number];
  /** Trục lên của camera. Là trục z CỦA HÌNH HỌC, không phải y của three.js. */
  huongLen: [number, number, number];
}

/** Phương vị và độ cao của hướng nhìn, tính TRONG HỆ CỦA HÌNH (z là trục đứng). */
export const PHUONG_VI_DO = -55;
export const DO_CAO_DO = 22;

/**
 * Trục "lên" của HÌNH HỌC — chiều cao bài toán nằm trên z, nên camera cũng vậy.
 *
 * ⚠️ **NGUỒN DUY NHẤT. Không chép cứng `(0,0,1)` ở chỗ khác.**
 * `OrbitControls` chụp `object.up` **một lần trong hàm dựng** (`_quat`,
 * `OrbitControls.js:406`) và không bao giờ tính lại. Nên giá trị này phải tới
 * được camera **TRƯỚC** khi controls được dựng; đặt muộn hơn thì controls quay
 * quanh Y trong khi `lookAt` dựng tư thế theo Z, và trục quay trôi mỗi khung
 * (`ROTATION_AXIS_INSTABILITY` —
 * `docs/SCENE3D_INTERACTION_SMOOTHNESS_REGRESSION_DIAGNOSIS.md`).
 * Hằng số nằm ở đây để chỉ có một chỗ phải đọc khi hỏi "trục đứng là gì".
 */
export const HUONG_LEN_HINH_HOC: readonly [number, number, number] = [0, 0, 1];

const HUONG_LEN = HUONG_LEN_HINH_HOC;

/** Phần khung mà hình nên chiếm. Chỉ thị đặt khoảng 55–80%; lấy giữa dải. */
const TI_LE_LAP_KHUNG = 0.66;

/** Khoảng cách tối thiểu, chặn ca hộp bao suy biến về một điểm. */
const KHOANG_TOI_THIEU = 2.5;

export function hopBaoCuaDiem(diem: [number, number, number][]): HopBao | null {
  if (diem.length === 0) return null;
  const min: [number, number, number] = [Infinity, Infinity, Infinity];
  const max: [number, number, number] = [-Infinity, -Infinity, -Infinity];
  for (const p of diem) {
    for (let i = 0; i < 3; i++) {
      if (!Number.isFinite(p[i])) return null;
      if (p[i] < min[i]) min[i] = p[i];
      if (p[i] > max[i]) max[i] = p[i];
    }
  }
  return { min, max };
}

type V3 = [number, number, number];
const tru = (a: V3, b: V3): V3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const cong = (a: V3, b: V3): V3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const nhan = (a: V3, k: number): V3 => [a[0] * k, a[1] * k, a[2] * k];
const cham = (a: V3, b: V3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const nhanCheo = (a: V3, b: V3): V3 =>
  [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const dai = (a: V3) => Math.hypot(a[0], a[1], a[2]);
function chuanHoa(a: V3): V3 {
  const l = dai(a);
  return l === 0 ? [0, 0, 0] : [a[0] / l, a[1] / l, a[2] / l];
}

/** Hướng nhìn từ phương vị/độ cao, trong hệ của hình (z đứng). */
export function huongNhin(phuongViDo: number, doCaoDo: number): V3 {
  const a = (phuongViDo * Math.PI) / 180;
  const e = (doCaoDo * Math.PI) / 180;
  return chuanHoa([Math.cos(e) * Math.cos(a), Math.cos(e) * Math.sin(a), Math.sin(e)]);
}

/**
 * Phương vị của một pháp tuyến, chiếu xuống mặt phẳng ngang. `null` khi pháp
 * tuyến gần như thẳng đứng — lúc ấy phương vị không xác định và người gọi phải
 * giữ nguyên góc mặc định thay vì lấy một số vô nghĩa.
 */
export function phuongViCuaPhapTuyen(n: V3): number | null {
  if (!n.every(Number.isFinite)) return null;
  if (Math.hypot(n[0], n[1]) < 1e-9) return null;
  return (Math.atan2(n[1], n[0]) * 180) / Math.PI;
}

/** Tám đỉnh của hộp bao. Fit theo chúng, không theo cầu ngoại tiếp. */
function dinhHop(hop: HopBao): V3[] {
  const out: V3[] = [];
  for (const x of [hop.min[0], hop.max[0]]) {
    for (const y of [hop.min[1], hop.max[1]]) {
      for (const z of [hop.min[2], hop.max[2]]) out.push([x, y, z]);
    }
  }
  return out;
}

/**
 * Đặt khung nhìn sao cho HÌNH CHIẾU của hộp bao lấp `TI_LE_LAP_KHUNG` chiều
 * bị bó hẹp hơn.
 *
 * `fovDo` là góc mở dọc của camera (độ); `tiLeKhung` là rộng/cao của khung vẽ.
 * `phuongViDo` cho phép người gọi ghi đè phương vị — dùng cho GUARD thiết diện
 * bẹp (xem `phuongViCuaPhapTuyen`); bỏ trống thì lấy `PHUONG_VI_DO`.
 *
 * Trả `null` khi đầu vào không dùng được, để nơi gọi giữ nguyên khung nhìn
 * hiện tại thay vì nhảy tới một chỗ vô nghĩa. **Không bao giờ trả `NaN`.**
 */
export function khungNhinVua(
  hop: HopBao | null,
  fovDo: number,
  tiLeKhung: number,
  phuongViDo: number = PHUONG_VI_DO,
): KhungNhin | null {
  if (!hop) return null;
  if (!Number.isFinite(fovDo) || fovDo <= 0 || fovDo >= 180) return null;
  if (!Number.isFinite(tiLeKhung) || tiLeKhung <= 0) return null;
  if (!Number.isFinite(phuongViDo)) return null;

  const tam: V3 = [
    (hop.min[0] + hop.max[0]) / 2,
    (hop.min[1] + hop.max[1]) / 2,
    (hop.min[2] + hop.max[2]) / 2,
  ];
  if (!tam.every(Number.isFinite)) return null;

  const dinh = dinhHop(hop);
  const huong = huongNhin(phuongViDo, DO_CAO_DO);
  const fov = (fovDo * Math.PI) / 180;
  const f = 1 / Math.tan(fov / 2);

  /** Phần khung bị hình chiếm, ở một khoảng cách cho trước. */
  const doPhu = (khoang: number): number => {
    const mat = cong(tam, nhan(huong, khoang));
    const truocSau = chuanHoa(tru(mat, tam));
    let ngang = nhanCheo(HUONG_LEN as V3, truocSau);
    if (dai(ngang) < 1e-9) ngang = nhanCheo([1, 0, 0], truocSau);
    ngang = chuanHoa(ngang);
    const doc = nhanCheo(truocSau, ngang);
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (const p of dinh) {
      const d = tru(p, mat);
      const sau = -cham(d, truocSau);
      if (sau <= 1e-6) return Infinity;          // đỉnh ở sau lưng camera
      const nx = (f / tiLeKhung) * (cham(d, ngang) / sau);
      const ny = f * (cham(d, doc) / sau);
      x0 = Math.min(x0, nx); x1 = Math.max(x1, nx);
      y0 = Math.min(y0, ny); y1 = Math.max(y1, ny);
    }
    // NDC chạy trong [−1, 1] ⇒ chia 2 để ra tỉ lệ khung.
    return Math.max((x1 - x0) / 2, (y1 - y0) / 2);
  };

  // Độ phủ giảm đơn điệu theo khoảng cách ⇒ chia đôi được.
  let thap = KHOANG_TOI_THIEU, cao = KHOANG_TOI_THIEU;
  for (let i = 0; i < 200 && doPhu(cao) > TI_LE_LAP_KHUNG; i++) cao *= 2;
  if (doPhu(cao) > TI_LE_LAP_KHUNG) return null;
  for (let i = 0; i < 80; i++) {
    const giua = (thap + cao) / 2;
    if (doPhu(giua) > TI_LE_LAP_KHUNG) thap = giua; else cao = giua;
  }
  const khoang = Math.max(KHOANG_TOI_THIEU, cao);
  if (!Number.isFinite(khoang)) return null;

  const viTri = cong(tam, nhan(huong, khoang));
  if (!viTri.every(Number.isFinite)) return null;
  return { viTri, nhinVao: tam, huongLen: [...HUONG_LEN] as V3 };
}
