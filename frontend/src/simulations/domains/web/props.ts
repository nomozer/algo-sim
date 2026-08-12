/**
 * MIỀN GIÁ TRỊ — chỗ "bounded" trở thành thật. Mirror của
 * `backend/app/simulation/catalog.py::validate_web_style_config`; hai tầng cùng
 * luật, đúng khuôn validate hai tầng của mọi domain khác.
 */
export type WebProp =
  | "backgroundColor" | "color" | "fontSize" | "padding" | "borderRadius"
  /* W4B-3F — trang có CẤU TRÚC: tiêu đề có màu và cỡ RIÊNG, nên đổi cỡ chữ
     tiêu đề khác việc đổi cỡ chữ đoạn văn. Đó chính là bài học phân cấp. */
  | "headingColor" | "headingSize";

export const COLOR_CHOICES = [
  { value: "#ffffff", label: "Trắng" },
  { value: "#fde68a", label: "Vàng" },
  { value: "#fca5a5", label: "Đỏ nhạt" },
  { value: "#a7f3d0", label: "Xanh lá nhạt" },
  { value: "#bfdbfe", label: "Xanh dương nhạt" },
  { value: "#e9d5ff", label: "Tím nhạt" },
  { value: "#1f2937", label: "Xám đậm" },
] as const;

export const TEXT_COLOR_CHOICES = [
  { value: "#1f2937", label: "Đen" },
  { value: "#b91c1c", label: "Đỏ" },
  { value: "#1d4ed8", label: "Xanh dương" },
  { value: "#047857", label: "Xanh lá" },
  { value: "#ffffff", label: "Trắng" },
] as const;

export const NUMERIC_RANGE = {
  headingSize: { min: 16, max: 56, step: 2, unit: "px", label: "Cỡ chữ tiêu đề" },
  fontSize: { min: 12, max: 48, step: 2, unit: "px", label: "Cỡ chữ đoạn văn" },
  padding: { min: 0, max: 48, step: 4, unit: "px", label: "Đệm trong" },
  borderRadius: { min: 0, max: 40, step: 2, unit: "px", label: "Bo góc" },
} as const;

export const NUMERIC_PROPS = ["headingSize", "fontSize", "padding", "borderRadius"] as const;

/** Giới hạn nội dung — khớp `_WEB_CONTENT_MAX` / `_WEB_PARAGRAPH_MAX` của BE. */
export const CONTENT_MAX_LENGTH = 120;
export const PARAGRAPH_MAX_LENGTH = 240;

/**
 * Kiểu mặc định khi spec không nói gì. Ở ĐÂY vì đây là chủ sở hữu MIỀN GIÁ TRỊ:
 * để module tự viết lại mã màu là dựng nguồn sự thật thứ hai, và bảng màu phải
 * khớp TỪNG BYTE với validator BE thì kiểm hai tầng mới có nghĩa.
 *
 * Lưu ý cho task thiết kế: các mã màu trong file này KHÔNG phải token giao
 * diện — chúng là DỮ LIỆU của bài học, tức bảng màu học sinh chọn để tô khối
 * trong trang web MÔ PHỎNG. Đổi chúng sang `var(--…)` sẽ phá kiểm hai tầng.
 */
export const DEFAULT_STYLE = {
  backgroundColor: COLOR_CHOICES[4].value,   // Xanh dương nhạt
  color: TEXT_COLOR_CHOICES[0].value,        // Đen
  headingColor: TEXT_COLOR_CHOICES[0].value, // Đen
  headingSize: 28,
  fontSize: 20,
  padding: 16,
  borderRadius: 8,
} as const;
