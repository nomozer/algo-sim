import {
  COLOR_CHOICES, NUMERIC_RANGE, NUMERIC_PROPS, TEXT_COLOR_CHOICES, type WebProp,
} from "./props";
import type { WebState, WebStyle } from "./model";

/**
 * Áp một thay đổi CÓ RÀNG BUỘC. `null` = không hợp lệ ⇒ người gọi giữ state cũ.
 * KHÔNG bao giờ nhận một chuỗi CSS thô — chỉ (tên thuộc tính đã khai, giá trị
 * trong miền đã khai).
 */
export function applyStyleChange(
  style: WebStyle, name: string, value: number | string | boolean,
): WebStyle | null {
  if (name === "backgroundColor") {
    return typeof value === "string" && COLOR_CHOICES.some((c) => c.value === value)
      ? { ...style, backgroundColor: value } : null;
  }
  if (name === "color" || name === "headingColor") {
    return typeof value === "string" && TEXT_COLOR_CHOICES.some((c) => c.value === value)
      ? { ...style, [name]: value } : null;
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
  return [
    ".khoi {",
    `  ${CSS_NAME.backgroundColor}: ${style.backgroundColor};`,
    `  ${CSS_NAME.color}: ${style.color};`,
    `  ${CSS_NAME.fontSize}: ${px(style.fontSize)};`,
    `  ${CSS_NAME.padding}: ${px(style.padding)};`,
    `  ${CSS_NAME.borderRadius}: ${px(style.borderRadius)};`,
    "}",
  ].join("\n");
}

/** Đã khác bản gốc chưa — dẫn xuất, không lưu cờ. */
export function isModified(state: WebState): boolean {
  return (Object.keys(state.baseline) as WebProp[])
    .some((k) => state.style[k] !== state.baseline[k]);
}
