import {
  CHANNEL_MAX,
  cssColorOf,
  hexOf,
  isChannelValue,
  type Channel,
  type Rgb,
} from "../../color-channels";

/**
 * color.rgb_model — MÔ HÌNH MÀU RGB.
 *
 * ─── CƠ CHẾ ẨN ĐANG DẠY ────────────────────────────────────────────────────
 *
 * Một màu trên màn hình KHÔNG phải một thuộc tính nguyên khối; nó là tổng của
 * ba nguồn sáng độc lập, mỗi nguồn một byte. Bảng mã màu in trong sách giấu
 * đúng điều đó đi: nó ghép sẵn từng cặp `#ffcc00` ↔ một ô màu, nên "vàng = đỏ +
 * lục" mãi là một câu phải học thuộc chứ không phải thứ nhìn thấy được.
 *
 * ─── VÌ SAO KHÔNG PHẢI `generic.rule_scene` ────────────────────────────────
 *
 * Cảnh generic dựng đối tượng và hé lộ chúng theo luật — nó chở được câu chuyện
 * VỀ màu nhưng không chở được phép TRỘN màu: không có đại lượng liên tục nào để
 * kéo, và không có ô màu nào là kết quả tất định của ba đại lượng ấy. Định
 * tuyến đề RGB sang đó là `SEMANTIC_MISUSE` (W5A / Phase M).
 *
 * ─── SỞ HỮU ────────────────────────────────────────────────────────────────
 *
 * State giữ ĐÚNG ba số. Mọi cách viết khác của cùng một màu (`rgb(...)`, `#hex`,
 * tên màu) đều DẪN XUẤT ở đây — không lưu song song. Hai bản của cùng một sự
 * thật là hai cơ hội để màn hình tự mâu thuẫn về màu đang hiện.
 */

export interface ColorConfig {
  red: number;
  green: number;
  blue: number;
  notes: string | null;
}

export interface ColorState {
  red: number;
  green: number;
  blue: number;
}

/** Tên trường trong config/state cho mỗi kênh — một bảng, không viết tay ba nơi. */
export const CHANNEL_FIELD: Record<Channel, keyof ColorState> = {
  r: "red",
  g: "green",
  b: "blue",
};

export function rgbOfState(s: ColorState): Rgb {
  return { r: s.red, g: s.green, b: s.blue };
}

/** `rgb(r, g, b)` — cách viết học sinh gặp trong CSS. */
export function cssColorOfState(s: ColorState): string {
  return cssColorOf(rgbOfState(s));
}

/** `#rrggbb` — cách viết vị trí của cùng ba số đó (mỗi kênh một cặp chữ số hex). */
export function hexColorOfState(s: ColorState): string {
  return hexOf(s.red, s.green, s.blue) ?? "#000000";
}

/**
 * TÊN MÀU — chỉ cho những điểm mốc mà cả ba kênh đều ở 0 hoặc 255.
 *
 * Cố ý KHÔNG đoán tên cho màu trộn bất kỳ. Gọi `rgb(200, 90, 40)` là "nâu" nghe
 * thân thiện nhưng đó là một phán quyết thẩm mỹ do renderer bịa ra, trong khi
 * cả bài học dựng trên nguyên tắc mọi thứ hiện ra đều phải dẫn xuất tất định từ
 * ba con số. Tám đỉnh của khối lập phương màu thì khác: chúng là ĐỊNH NGHĨA.
 */
const CORNER_NAMES: Record<string, string> = {
  "0,0,0": "đen",
  "255,255,255": "trắng",
  "255,0,0": "đỏ",
  "0,255,0": "lục",
  "0,0,255": "lam",
  "255,255,0": "vàng",
  "0,255,255": "lơ (cyan)",
  "255,0,255": "hồng sẫm (magenta)",
};

export function cornerNameOf(s: ColorState): string | null {
  return CORNER_NAMES[`${s.red},${s.green},${s.blue}`] ?? null;
}

/**
 * MỨC XÁM: ba kênh bằng nhau. Nêu ra vì đây là quan hệ học sinh khám phá được
 * mà không cần ai dạy trước — kéo ba thanh về cùng một chỗ thì màu mất hẳn sắc.
 */
export function isGray(s: ColorState): boolean {
  return s.red === s.green && s.green === s.blue;
}

/** Kênh mạnh nhất — dùng cho thuyết minh khi màu không rơi vào điểm mốc nào. */
export function dominantChannel(s: ColorState): Channel | null {
  const c = rgbOfState(s);
  const top = Math.max(c.r, c.g, c.b);
  if (top === 0) return null;
  const winners = (["r", "g", "b"] as Channel[]).filter((ch) => c[ch] === top);
  return winners.length === 1 ? winners[0] : null;
}

/** Ba kênh có hợp lệ không — mirror của `validate_color_config` bên backend. */
export function channelsValid(s: ColorState): boolean {
  return isChannelValue(s.red) && isChannelValue(s.green) && isChannelValue(s.blue);
}

export { CHANNEL_MAX };
