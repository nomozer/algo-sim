/**
 * color-channels.ts — CHỦ SỞ HỮU DUY NHẤT của phép toán BA KÊNH ↔ MỘT MÀU.
 *
 * ─── VÌ SAO FILE NÀY RA ĐỜI (W5A) ──────────────────────────────────────────
 *
 * Phép đổi hex ↔ RGB đã có sẵn và đã đúng — nhưng nó nằm trong
 * `domains/web/props.ts`, tức thuộc sở hữu của MỘT miền. Khi `color.rgb_model`
 * ra đời, có đúng ba lối đi và hai trong số đó sai:
 *
 *   (1) miền `color` import từ `domains/web/`  → hai miền dính nhau, và hướng
 *       phụ thuộc `domains/* ← shared` bị đảo (ARCHITECTURE_MAP §4);
 *   (2) chép lại phép toán sang miền mới       → hai bản `hexOf`, và ngày nào
 *       chúng lệch nhau thì hai màn hình nói hai giá trị khác nhau về CÙNG một
 *       màu — đúng lỗi #4 trong danh sách tiêm lỗi của W5, chỉ là ở quy mô lớn hơn;
 *   (3) NÂNG lên chủ sở hữu dùng chung          ← file này.
 *
 * Cùng khuôn `tool-affordance.ts`: luật/phép toán dùng chung sống ở tầng
 * `simulations/`, miền nào cần thì đọc xuống. `domains/web/props.ts` nay
 * RE-EXPORT từ đây chứ không giữ bản thứ hai.
 *
 * ─── RANH GIỚI ─────────────────────────────────────────────────────────────
 *
 * File này chỉ biết SỐ và CHUỖI. Nó không biết `web.style_model` hay
 * `color.rgb_model` tồn tại, không đọc store, không dựng JSX — nên nó kiểm được
 * bằng bảng giá trị, không cần trình duyệt.
 */

export type Channel = "r" | "g" | "b";
export const CHANNELS: readonly Channel[] = ["r", "g", "b"];
export const CHANNEL_LABEL: Record<Channel, string> = { r: "Đỏ", g: "Lục", b: "Lam" };
export const CHANNEL_MAX = 255;

export interface Rgb {
  r: number;
  g: number;
  b: number;
}

/**
 * W5 §2 — MIỀN MÀU LÀ 24 BIT, KHÔNG PHẢI BẢY Ô.
 *
 * ⚠️ VẪN ĐÓNG: tập hợp lệ đúng bằng các chuỗi khớp mẫu này, tức chỉ có thể là
 * MỘT MÀU. Không phải "chuỗi CSS bất kỳ" — nới sang tên màu, hàm màu hay biến
 * CSS sẽ mở đúng cánh cửa mà tập đóng đang giữ.
 */
export const HEX_COLOR = /^#[0-9a-f]{6}$/i;

/** Một trị kênh hợp lệ: NGUYÊN và nằm trong 0..255. */
export function isChannelValue(v: unknown): v is number {
  return typeof v === "number" && Number.isInteger(v) && v >= 0 && v <= CHANNEL_MAX;
}

/**
 * Kẹp về miền hợp lệ. Dùng ở BIÊN NHẬN (thanh trượt, ô số) — không dùng để
 * "chữa" một config sai: config sai là việc của validator, và kẹp im lặng ở đó
 * sẽ biến một đề hỏng thành một mô phỏng trông như đúng.
 */
export function clampChannel(v: number): number {
  if (!Number.isFinite(v)) return 0;
  return Math.max(0, Math.min(CHANNEL_MAX, Math.round(v)));
}

export function rgbOf(hex: string): Rgb | null {
  if (!HEX_COLOR.test(hex)) return null;
  const n = parseInt(hex.slice(1), 16);
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
}

export function hexOf(r: number, g: number, b: number): string | null {
  if (!isChannelValue(r) || !isChannelValue(g) || !isChannelValue(b)) return null;
  return `#${[r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

/** Chuỗi `rgb(r, g, b)` — DẪN XUẤT, không lưu song song với hex. */
export function rgbTextOf(hex: string): string | null {
  const c = rgbOf(hex);
  return c ? `rgb(${c.r}, ${c.g}, ${c.b})` : null;
}

/** Cách viết `rgb(...)` đi thẳng từ ba số — không phải vòng qua hex rồi ngược lại. */
export function cssColorOf(c: Rgb): string {
  return `rgb(${c.r}, ${c.g}, ${c.b})`;
}

/**
 * VỆT MÀU CỦA MỘT THANH TRƯỢT: kênh này chạy 0 → 255, hai kênh kia GIỮ NGUYÊN.
 *
 * Đây không phải trang trí. Nó trả lời trước câu "kéo thanh này thì màu đi về
 * đâu" ngay khi học sinh chưa kéo — tức chính thanh trượt đã mang bài học, thay
 * vì phải thử rồi mới biết. Giữ hai kênh kia cố định là ĐIỀU KIỆN để câu trả lời
 * ấy đúng: một vệt đỏ-thuần cố định sẽ nói dối về màu sắp nhận được.
 */
export function channelRamp(c: Rgb, ch: Channel): string {
  const at = (v: number): string =>
    hexOf(
      ch === "r" ? v : c.r,
      ch === "g" ? v : c.g,
      ch === "b" ? v : c.b,
    ) ?? "#000000";
  return `linear-gradient(to right, ${at(0)}, ${at(CHANNEL_MAX)})`;
}

/**
 * ĐỘ SÁNG CẢM NHẬN (ITU-R BT.601) — dùng để chọn màu CHỮ đặt trên ô màu.
 *
 * Vì sao cần: ô màu là kết quả của bài học, nên nhãn đặt trên nó phải đọc được
 * ở CẢ 16,7 triệu giá trị mà học sinh kéo tới được. Một màu chữ cố định sẽ biến
 * mất ở một đầu của miền — và nó biến mất đúng lúc học sinh kéo tới đó, tức
 * đúng lúc đang học.
 */
export function readableInkOn(c: Rgb): string {
  const luma = (0.299 * c.r + 0.587 * c.g + 0.114 * c.b) / CHANNEL_MAX;
  return luma > 0.55 ? "#111827" : "#ffffff";
}
