import {
  CHANNELS, HEX_COLOR, NUMERIC_RANGE, NUMERIC_PROPS,
  hexOf, rgbOf, type Channel, type WebProp,
} from "./props";
import { WEB_NODES, type WebBlock, type WebNode, type WebState, type WebStyle } from "./model";

/**
 * W5 §2 — THUỘC TÍNH MÀU mà một nút đang sở hữu.
 *
 * §2 nói học sinh chọn TEXT hay BACKGROUND. Mô hình đã có sẵn phép chọn nút
 * (khung trang · tiêu đề · đoạn văn), nên ánh xạ vào đó thay vì dựng một bộ chọn
 * thứ hai song song — hai bộ chọn cho cùng một câu hỏi là hai bản chọn sẽ lệch
 * nhau (đúng lý do `selected` được đưa vào state chứ không để renderer giữ).
 */
export function colorPropOf(node: WebNode): WebProp {
  if (node === "page") return "backgroundColor";
  return node === "heading" ? "headingColor" : "color";
}

/**
 * Đổi MỘT kênh, giữ nguyên hai kênh kia — đúng thao tác §2A đòi hỏi.
 *
 * Trả `null` khi ngoài miền ⇒ người gọi giữ state cũ. KHÔNG kẹp về biên: kẹp im
 * lặng dạy học sinh rằng em đã đặt được giá trị đó (cùng luật với thuộc tính số).
 */
export function applyChannelChange(
  style: WebStyle, node: WebNode, channel: string, value: number | string | boolean,
): WebStyle | null {
  if (!(CHANNELS as readonly string[]).includes(channel)) return null;
  if (typeof value !== "number" || !Number.isInteger(value)) return null;
  const prop = colorPropOf(node);
  const current = rgbOf(style[prop] as string);
  if (!current) return null;
  const next = { ...current, [channel as Channel]: value };
  const hex = hexOf(next.r, next.g, next.b);
  return hex ? { ...style, [prop]: hex } : null;
}

/**
 * Áp một thay đổi CÓ RÀNG BUỘC. `null` = không hợp lệ ⇒ người gọi giữ state cũ.
 * KHÔNG bao giờ nhận một chuỗi CSS thô — chỉ (tên thuộc tính đã khai, giá trị
 * trong miền đã khai).
 */
export function applyStyleChange(
  style: WebStyle, name: string, value: number | string | boolean,
): WebStyle | null {
  if (name === "backgroundColor" || name === "color" || name === "headingColor") {
    /* W5: miền là MỌI mã hex 6 chữ số, không còn là bảy ô gợi ý — bài học T12.CD4
       là quan hệ ba kênh ↔ màu, và bảy ô không có cách nào giữ hai kênh cố định
       để xem kênh thứ ba làm gì. Chuẩn hoá chữ thường để hai tầng so được từng
       byte. Vẫn ĐÓNG: chỉ có thể là một màu, không phải chuỗi CSS tuỳ ý. */
    return typeof value === "string" && HEX_COLOR.test(value)
      ? { ...style, [name]: value.toLowerCase() } : null;
  }
  if ((NUMERIC_PROPS as readonly string[]).includes(name)) {
    if (typeof value !== "number" || !Number.isInteger(value)) return null;
    const r = NUMERIC_RANGE[name as (typeof NUMERIC_PROPS)[number]];
    /* TỪ CHỐI chứ KHÔNG kẹp về biên — cùng luật với validator BE. Kẹp im lặng
       nói dối hai lần: người gọi tưởng đã đặt được giá trị đó, và học sinh thấy
       một con số mình không hề chọn. Thanh trượt vốn không ra ngoài miền. */
    return value >= r.min && value <= r.max ? { ...style, [name]: value } : null;
  }
  return null; // ngoài tập đóng ⇒ fail-closed
}

/**
 * Chọn một nút. Tên ngoài tập ⇒ `null` ⇒ người gọi giữ nguyên state, cùng luật
 * fail-closed với mọi thứ khác trong miền này.
 */
export function selectNode(name: string): WebNode | null {
  return (WEB_NODES as readonly string[]).includes(name) ? (name as WebNode) : null;
}

/**
 * ĐỔI CHỖ MỘT KHỐI trong thân trang — miền là một HOÁN VỊ của tập khối đã có.
 *
 * Không thêm khối, không xoá khối, không đặt khối vào khung khác. Một trình
 * soạn thảo HTML sẽ cho phép cả ba; ở đây `order` chỉ đi từ hoán vị này sang
 * hoán vị khác, nên mọi state sinh ra đều là một trang hợp lệ.
 *
 * `slot` là CHỈ SỐ Ô ĐÍCH tuyệt đối (không phải delta), cùng ngữ nghĩa với cú
 * kéo của `generic`: action nói "đặt nó vào đây", engine quyết định hợp lệ.
 * Dòng chảy tài liệu chỉ có MỘT trục nên không có toạ độ ngang.
 */
export function moveBlock(
  order: readonly WebBlock[], target: string, slot: number,
): WebBlock[] | null {
  const from = order.indexOf(target as WebBlock);
  if (from < 0) return null;                                  // khối không có trong trang
  if (!Number.isInteger(slot) || slot < 0 || slot >= order.length) return null;
  if (slot === from) return null;                             // không nhúc nhích ⇒ không state mới
  const next = order.filter((_, i) => i !== from);
  next.splice(slot, 0, order[from]);
  return next;
}

const CSS_NAME: Record<WebProp, string> = {
  backgroundColor: "background-color",
  color: "color",
  headingColor: "color",
  headingSize: "font-size",
  fontSize: "font-size",
  padding: "padding",
  borderRadius: "border-radius",
};

/**
 * Bản xem DẠNG MÃ — SINH RA từ state, không phải nguồn sự thật thứ hai.
 * Học sinh nối được thao tác với cú pháp thật mà hệ vẫn không chạy CSS tuỳ ý.
 */
export function cssTextOf(style: WebStyle): string {
  const px = (n: number) => `${n}px`;
  /* W4B-3F — BA BỘ CHỌN, và đó là điểm của cả wave.
   *
   * Một khối chữ chỉ đẻ ra được MỘT luật, nên bài "HTML/CSS" trước đây không có
   * gì để nói về quan hệ thẻ ↔ hiển thị. Có `h1`/`p` bên trong `.trang` thì bộ
   * chọn HẬU DUỆ trở thành thật, và học sinh đọc ra vì sao đổi `font-size` ở
   * hai chỗ lại cho hai kết quả khác nhau. */
  return [
    ".trang {",
    `  ${CSS_NAME.backgroundColor}: ${style.backgroundColor};`,
    `  ${CSS_NAME.padding}: ${px(style.padding)};`,
    `  ${CSS_NAME.borderRadius}: ${px(style.borderRadius)};`,
    "}",
    "",
    ".trang h1 {",
    `  ${CSS_NAME.headingColor}: ${style.headingColor};`,
    `  ${CSS_NAME.headingSize}: ${px(style.headingSize)};`,
    "}",
    "",
    ".trang p {",
    `  ${CSS_NAME.color}: ${style.color};`,
    `  ${CSS_NAME.fontSize}: ${px(style.fontSize)};`,
    "}",
  ].join("\n");
}

/**
 * Bản xem DẠNG THẺ — cũng SINH RA từ state, đặt cạnh `cssTextOf` cho cân.
 *
 * Nó ở đây chứ không ở JSX vì đúng chỗ này từng là một lỗ: nếu renderer tự ghép
 * chuỗi HTML thì nó thành nguồn sự thật thứ hai về cấu trúc trang, và một cú
 * đổi thứ tự có thể hiện ra ở sân khấu mà không hiện ra ở mã (hoặc ngược lại).
 */
export function htmlTextOf(state: WebState): string {
  const line = (b: WebBlock) =>
    b === "heading" ? `  <h1>${state.heading}</h1>` : `  <p>${state.paragraph}</p>`;
  return [`<div class="trang">`, ...state.order.map(line), "</div>"].join("\n");
}

/** Đã khác bản gốc chưa — dẫn xuất, không lưu cờ. */
export function isModified(state: WebState): boolean {
  const styleChanged = (Object.keys(state.baseline) as WebProp[])
    .some((k) => state.style[k] !== state.baseline[k]);
  /* Thứ tự cũng là thứ học sinh đổi được, nên "Về ban đầu" phải hiện ra khi mới
     chỉ đảo khối — nếu chỉ soi `style` thì cú đổi cấu trúc không có đường lùi. */
  const orderChanged = state.order.join(",") !== state.baselineOrder.join(",");
  return styleChanged || orderChanged;
}
