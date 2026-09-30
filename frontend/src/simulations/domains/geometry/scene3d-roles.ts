/**
 * BẢNG MÀU VAI TRÒ — mỗi màu MỘT nghĩa, trên canvas và ở bảng lời giải (W12).
 *
 * ─── VÌ SAO TÁCH THÀNH MỘT MODULE ────────────────────────────────────────
 *
 * Review người (W12, NEEDS_CHANGES): cam đậm mang HAI nghĩa — "dữ kiện số"
 * trong hàng số đo và "vật đang chọn" trên canvas; còn xanh vừa là điểm đề
 * cho, vừa là đích của causal ở hàng số. Hai bảng màu viết tay ở hai chỗ là
 * cách chắc chắn để chúng trôi khỏi nhau, nên cả renderer lẫn CSS đọc về đây
 * (CSS giữ bản sao `--geo3d-vai-tro-*`, khoá bằng test đồng bộ).
 *
 *   xanh        thứ ĐANG XÉT — vật được chọn, hoặc vật vừa dựng khi phát
 *   cam đậm     dữ kiện SỐ đề cho
 *   cam nhạt    đại lượng TRUNG GIAN suy ra
 *   xám         ngữ cảnh cấu trúc/tô-pô của chuỗi nhân quả
 *   mờ          ngoài chuỗi (độ trong, không phải một màu)
 *
 * Điểm đề cho không còn xanh (quyết định W12): xanh chỉ còn nghĩa "đang xét".
 */
export const MAU_VAI_TRO = {
  /** Đích causal — vật người học chọn (canvas lẫn bảng). */
  dich: 0x2563eb,
  /** Vật vừa dựng ở bước đang phát: cũng là thứ đang xét. */
  moi_dung: 0x2563eb,
  /** Dữ kiện số đề cho trong chuỗi nhân quả. */
  du_kien_so: 0xc2410c,
  /** Đại lượng trung gian suy ra trong chuỗi nhân quả. */
  trung_gian: 0xfb923c,
  /** Nét của ngữ cảnh cấu trúc/tô-pô — trung tính. */
  boi_canh: 0x6b7280,
  /** Nền (mặt, khối) của ngữ cảnh cấu trúc — trung tính, nhạt. */
  nen_boi_canh: 0xd1d5db,
  /** Chấm điểm đề cho khi không có vai trò nào — trung tính đậm. */
  diem_de_cho: 0x374151,
} as const;

/** Tên biến CSS mang cùng giá trị — bảng lời giải và chú giải đọc chúng. */
export const BIEN_CSS_VAI_TRO = {
  dich: "--geo3d-vai-tro-dich",
  du_kien_so: "--geo3d-vai-tro-du-kien-so",
  trung_gian: "--geo3d-vai-tro-trung-gian",
  boi_canh: "--geo3d-vai-tro-boi-canh",
} as const satisfies Partial<Record<keyof typeof MAU_VAI_TRO, string>>;

/** `0x2563eb` → `#2563eb` — để test đồng bộ so với CSS. */
export function hexCss(mau: number): string {
  return `#${mau.toString(16).padStart(6, "0")}`;
}
