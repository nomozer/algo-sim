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
  backgroundColor: string;
  color: string;
  fontSize: number;
  padding: number;
  borderRadius: number;
}

export interface WebConfig {
  content: string;
  style: WebStyle;
  notes: string | null;
}

export interface WebState {
  content: string;
  style: WebStyle;
  /** Bản gốc đã validate — "Về ban đầu" là phép toán, không phải undo log. */
  baseline: WebStyle;
}
