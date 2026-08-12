import type { WebProp } from "./props";
export type { WebProp };

/**
 * BOUNDED INTERACTIVE ARTIFACT — mô hình thuộc tính trình bày CÓ RÀNG BUỘC.
 *
 * ĐÂY KHÔNG PHẢI `code_experiment` (vẫn DEFERRED — `ARCHITECTURE_MAP §10`):
 *
 *   code playground : học sinh gõ mã tuỳ ý → TRÌNH DUYỆT diễn giải
 *   bounded artifact: học sinh đổi THUỘC TÍNH ĐÃ KHAI → MÔ HÌNH TẤT ĐỊNH sở hữu
 *                     sự thật, trình duyệt chỉ VẼ LẠI state đó
 *
 * Về kiến trúc nó giống hệt `logic.and_gate`: bật một công tắc → state đổi →
 * biểu diễn đổi. "Công tắc" ở đây là màu nền, cỡ chữ, đệm trong.
 *
 * Tập thuộc tính ĐÓNG. Không CSS passthrough, không chuỗi style thô, không
 * `eval`, không `new Function`, không iframe, không JS. Tên lạ ⇒ no-op.
 */
export interface WebStyle {
  /** `.trang` — khung trang */
  backgroundColor: string;
  padding: number;
  borderRadius: number;
  /** `.trang h1` — tiêu đề */
  headingColor: string;
  headingSize: number;
  /** `.trang p` — đoạn văn */
  color: string;
  fontSize: number;
}

export interface WebConfig {
  /** `<h1>` — tiêu đề trang */
  heading: string;
  /** `<p>` — đoạn văn (có thể rỗng) */
  paragraph: string;
  style: WebStyle;
  notes: string | null;
}

export interface WebState {
  heading: string;
  paragraph: string;
  style: WebStyle;
  /** Bản gốc đã validate — "Về ban đầu" là phép toán, không phải undo log. */
  baseline: WebStyle;
}
