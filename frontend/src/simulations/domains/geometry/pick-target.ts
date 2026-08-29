/**
 * ĐÍCH BẤM — to hơn thứ nhìn thấy, và **chỉ** để bấm.
 *
 * ─── VÌ SAO TÁCH KHỎI KÍCH THƯỚC NHÌN ───────────────────────────────────
 *
 * Demo tay đo bằng lưới 625 điểm ảnh: mặt trúng 26 lần, đường thẳng 10, đa
 * giác 7 — còn **điểm 0 và cạnh 0**. Cơ chế chọn không hỏng (đường thẳng `SA`
 * cũng là `THREE.Line` mà trúng 10 lần); cái hỏng là ĐÍCH BẤM: chấm đánh dấu
 * bán kính `0.09` và cạnh là nét 1px.
 *
 * Cách sửa sai sẽ là phóng to chấm cho dễ bấm. Nhưng chấm to thì hình xấu đi
 * và một điểm bắt đầu trông như một quả cầu — hệ đang dạy hình học, không
 * được đổi thứ học sinh NHÌN THẤY chỉ để chuột dễ hơn. Nên hai đại lượng tách
 * hẳn: **cỡ nhìn** giữ nguyên, **cỡ bấm** rộng ra và vô hình.
 *
 * ⚠️ Không đại lượng nào ở đây đi vào `GeometryState`, kernel, checker hay
 * phép đo. Chúng chỉ trả lời *"con trỏ có đủ gần vật này không"*.
 *
 * ─── VÌ SAO PHỤ THUỘC CAMERA ───────────────────────────────────────────
 *
 * `Raycaster` đo ngưỡng trong KHÔNG GIAN THẾ GIỚI, còn ngón tay người dùng đo
 * bằng ĐIỂM ẢNH. Một ngưỡng cố định vừa tay ở góc nhìn mặc định sẽ thành hạt
 * bụi khi phóng to và thành cả một vùng khi thu nhỏ. Nên ngưỡng dẫn từ khoảng
 * cách camera: xa thì rộng ra, gần thì hẹp lại, và vùng bấm theo điểm ảnh gần
 * như không đổi.
 */

/** Bán kính chấm NHÌN THẤY. Đổi nó là đổi hình học trông thế nào. */
export const BAN_KINH_NHIN = 0.09;

/**
 * Vùng bấm quy ra ĐIỂM ẢNH, ở góc nhìn mặc định.
 *
 * `12px` cho điểm và `8px` cho cạnh — nằm trong khoảng mà một ngón tay hay
 * một con chuột với tay được, và vẫn đủ nhỏ để hai đỉnh cạnh nhau không nuốt
 * lẫn nhau. Không cố đúng từng điểm ảnh: `Raycaster` làm việc ở không gian
 * thế giới nên đây là phép quy đổi xấp xỉ, và nó chỉ cần đúng cỡ.
 */
export const DICH_DIEM_PX = 12;
export const DICH_CANH_PX = 8;

/**
 * Khoảng camera → thế giới, ở góc nhìn mặc định của khung hình học.
 *
 * `cam.position` khởi tạo ở `(6, 5, 8)` nhìn về gốc, tức `|cam| ≈ 11.2`, và
 * khung cao 549px với FOV 50°. Một điểm ảnh khi ấy ứng với khoảng
 * `2·|cam|·tan(25°) / 549 ≈ 0.019` đơn vị thế giới. Hằng số dưới đây là con
 * số ấy, viết ra để đọc lại được thay vì một số ma.
 */
export const DON_VI_MOI_PX = 0.019;

/**
 * Ngưỡng bấm theo khoảng cách camera — giữ vùng bấm gần như không đổi trên
 * màn hình khi phóng to / thu nhỏ.
 *
 * `khoangCam` là `|cam.position|` (camera luôn nhìn về gốc), nên phép này
 * **không** dùng `distanceTo` — vốn bị guard cấm trong tầng view vì nó là một
 * phép đo hình học. Ở đây đại lượng vào là một độ dài vector của CAMERA, và
 * đại lượng ra chỉ dùng cho `Raycaster`.
 *
 * Fail-safe: đầu vào không hữu hạn hoặc ≤ 0 ⇒ trả ngưỡng mặc định. Một
 * `NaN` lọt vào `params.Line.threshold` làm raycast im lặng không trúng gì —
 * và một cổng không bao giờ trúng đọc y hệt một cổng không có lỗi.
 */
/** `|(6,5,8)|` — vị trí camera lúc khởi tạo. MỘT nguồn, không hai. */
export const KHOANG_CAM_MAC_DINH = Math.hypot(6, 5, 8);

export function nguongBam(px: number, khoangCam: number): number {
  // Cả HAI đầu vào đều fail-safe. Chỉ chốt `khoangCam` là bỏ sót một nửa: một
  // `px` hỏng cũng cho `NaN`, và `NaN` trong `params.Line.threshold` làm
  // raycast im lặng không trúng gì.
  const d = Number.isFinite(khoangCam) && khoangCam > 0
    ? khoangCam
    : KHOANG_CAM_MAC_DINH;
  const v = Number.isFinite(px) && px > 0 ? px : DICH_CANH_PX;
  return (v * DON_VI_MOI_PX * d) / KHOANG_CAM_MAC_DINH;
}

/** Bán kính hình cầu VÔ HÌNH bọc quanh một điểm, chỉ để bắt con trỏ. */
export function banKinhBamDiem(khoangCam: number): number {
  return Math.max(BAN_KINH_NHIN, nguongBam(DICH_DIEM_PX, khoangCam));
}

/** Ngưỡng bấm của một đoạn thẳng. */
export function nguongBamCanh(khoangCam: number): number {
  return nguongBam(DICH_CANH_PX, khoangCam);
}

/**
 * Hạng CỤ THỂ của một vật khi tia trúng nhiều lớp. Nhỏ hơn = cụ thể hơn.
 *
 *     điểm → cạnh → mặt → (vật khác) → khối
 *
 * Khối xếp cuối vì nó **chứa** mọi thứ kia: bấm vào mặt SAB mà nhận cả hình
 * chóp là câu trả lời đúng về mặt hình học nhưng vô dụng với người đang học.
 */
export const HANG_CU_THE: Record<string, number> = {
  point3: 0, edge: 1, face: 2, polygon3: 3, line3: 3, plane3: 3,
  quantity: 4, section: 3, solid: 5,
};

export function hangCuThe(loai: string | undefined): number {
  return HANG_CU_THE[loai ?? ""] ?? 4;
}
