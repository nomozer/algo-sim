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

/**
 * W5 §2 — MIỀN MÀU LÀ 24 BIT, KHÔNG PHẢI BẢY Ô.
 *
 * Mirror của `_WEB_HEX_COLOR` bên backend (kiểm hai tầng, khoá bởi
 * `web-contract-parity.test.ts`).
 *
 * ⚠️ VẪN ĐÓNG: tập hợp lệ đúng bằng các chuỗi khớp mẫu này, tức chỉ có thể là
 * MỘT MÀU. Không phải "chuỗi CSS bất kỳ" — nới sang tên màu, hàm màu hay biến
 * CSS sẽ mở đúng cánh cửa mà tập đóng đang giữ.
 */
export const HEX_COLOR = /^#[0-9a-f]{6}$/i;

export type Channel = "r" | "g" | "b";
export const CHANNELS: readonly Channel[] = ["r", "g", "b"];
export const CHANNEL_LABEL: Record<Channel, string> = { r: "Đỏ", g: "Lục", b: "Lam" };
export const CHANNEL_MAX = 255;

/**
 * CHỦ SỞ HỮU DUY NHẤT của phép đổi hex ↔ RGB.
 *
 * Đặt ở đây vì cả ba nơi đều cần đúng con số này: thanh trượt, dòng
 * `rgb(r, g, b)` in ra cho học sinh, và bảng CSS. Ba nơi tự tính là ba cơ hội
 * để chúng nói ba giá trị khác nhau về cùng một màu — và học sinh sẽ tin cái
 * nào? Đây chính là lỗi #4 trong danh sách tiêm lỗi của W5.
 */
export function rgbOf(hex: string): { r: number; g: number; b: number } | null {
  if (!HEX_COLOR.test(hex)) return null;
  const n = parseInt(hex.slice(1), 16);
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
}

export function hexOf(r: number, g: number, b: number): string | null {
  const ok = (v: number) => Number.isInteger(v) && v >= 0 && v <= CHANNEL_MAX;
  if (!ok(r) || !ok(g) || !ok(b)) return null;
  return `#${[r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

/** Chuỗi `rgb(r, g, b)` — DẪN XUẤT, không lưu song song với hex. */
export function rgbTextOf(hex: string): string | null {
  const c = rgbOf(hex);
  return c ? `rgb(${c.r}, ${c.g}, ${c.b})` : null;
}

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

/**
 * Mỗi thuộc tính số khai LUÔN nó thuộc BỘ CHỌN nào.
 *
 * ─── VÌ SAO `node` NẰM Ở ĐÂY, KHÔNG NẰM Ở `ui.tsx` ────────────────────────
 *
 * Trước W12, `ui.tsx` giữ một hằng số `GROUPS` viết tay liệt kê lại đúng những
 * thuộc tính này kèm bộ chọn của chúng. Hệ quả: bề mặt công cụ KHÔNG dẫn từ
 * đăng kí — thêm một thuộc tính vào `NUMERIC_PROPS` mà quên sửa `GROUPS` thì
 * học sinh không có ô điều khiển nào cho nó, và không gì báo.
 *
 * Điều đó chạm thẳng luận điểm đề tài: nếu bề mặt tương tác là hằng số viết
 * tay thì một đặc tả do LLM đề xuất KHÔNG quyết định được gì ở tầng ấy — nó chỉ
 * điền vào một khuôn cứng. Người dùng hỏi đúng câu này: "mô phỏng sinh sau có
 * ra được các tính năng như vậy không?"
 *
 * Nay `node` là dữ kiện của chính đăng kí, `ui.tsx` nhóm theo nó, và
 * `web-prop-registry.test.ts` khoá: mọi thuộc tính phải có đúng một ô điều khiển.
 */
export const NUMERIC_RANGE = {
  headingSize: { node: "heading", min: 16, max: 56, step: 2, unit: "px", label: "Cỡ chữ tiêu đề" },
  fontSize: { node: "paragraph", min: 12, max: 48, step: 2, unit: "px", label: "Cỡ chữ đoạn văn" },
  padding: { node: "page", min: 0, max: 48, step: 4, unit: "px", label: "Đệm trong" },
  borderRadius: { node: "page", min: 0, max: 40, step: 2, unit: "px", label: "Bo góc" },
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
