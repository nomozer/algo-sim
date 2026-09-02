/**
 * scene3d-camera.ts — KHUNG NHÌN, tính từ hộp bao của vật ĐANG THẤY.
 *
 * ─── VÌ SAO TỒN TẠI ───────────────────────────────────────────────────────
 *
 * Bản trước đặt camera bằng một hằng số (`position.set(6, 5, 8)`) cho mọi bài.
 * Với bài toạ độ nhỏ thì hình chiếm một góc khung; với bài toạ độ lớn thì hình
 * tràn ra ngoài. Ảnh chụp thật cho thấy cả hai kiểu hỏng.
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

/** Kết quả đặt khung nhìn — vị trí camera và điểm nó nhìn vào. */
export interface KhungNhin {
  viTri: [number, number, number];
  nhinVao: [number, number, number];
}

/** Hướng nhìn mặc định, đã chuẩn hoá. Giữ đúng hướng cũ để hình quen mắt. */
const HUONG: readonly [number, number, number] = [6, 5, 8];

/** Phần khung mà hình nên chiếm. Chỉ thị đặt khoảng 55–80%; lấy giữa dải. */
const TI_LE_LAP_KHUNG = 0.68;

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

/**
 * Đặt khung nhìn sao cho hộp bao lấp khoảng `TI_LE_LAP_KHUNG` chiều cao khung.
 *
 * `fovDo` là góc mở dọc của camera (độ); `tiLeKhung` là rộng/cao của khung vẽ.
 * Khi khung hẹp hơn cao, chiều RỘNG mới là chiều bị bó, nên khoảng cách phải
 * lấy theo cái lớn hơn trong hai ràng buộc — bỏ qua điều này thì ở khung dọc
 * hình bị cắt hai bên.
 *
 * Trả `null` khi đầu vào không dùng được, để nơi gọi giữ nguyên khung nhìn
 * hiện tại thay vì nhảy tới một chỗ vô nghĩa. **Không bao giờ trả `NaN`.**
 */
export function khungNhinVua(
  hop: HopBao | null,
  fovDo: number,
  tiLeKhung: number,
): KhungNhin | null {
  if (!hop) return null;
  if (!Number.isFinite(fovDo) || fovDo <= 0 || fovDo >= 180) return null;
  if (!Number.isFinite(tiLeKhung) || tiLeKhung <= 0) return null;

  const tam: [number, number, number] = [
    (hop.min[0] + hop.max[0]) / 2,
    (hop.min[1] + hop.max[1]) / 2,
    (hop.min[2] + hop.max[2]) / 2,
  ];
  const nuaCanh = [
    (hop.max[0] - hop.min[0]) / 2,
    (hop.max[1] - hop.min[1]) / 2,
    (hop.max[2] - hop.min[2]) / 2,
  ];
  const banKinh = Math.hypot(nuaCanh[0], nuaCanh[1], nuaCanh[2]);
  if (!Number.isFinite(banKinh)) return null;

  const fov = (fovDo * Math.PI) / 180;
  const canDoc = banKinh / Math.sin(fov / 2);
  // Góc mở NGANG suy từ góc dọc và tỉ lệ khung.
  const fovNgang = 2 * Math.atan(Math.tan(fov / 2) * tiLeKhung);
  const canNgang = banKinh / Math.sin(fovNgang / 2);
  const can = Math.max(canDoc, canNgang) / TI_LE_LAP_KHUNG;
  const khoang = Math.max(KHOANG_TOI_THIEU, can);
  if (!Number.isFinite(khoang)) return null;

  const dai = Math.hypot(HUONG[0], HUONG[1], HUONG[2]);
  return {
    viTri: [
      tam[0] + (HUONG[0] / dai) * khoang,
      tam[1] + (HUONG[1] / dai) * khoang,
      tam[2] + (HUONG[2] / dai) * khoang,
    ],
    nhinVao: tam,
  };
}
