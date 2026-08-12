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

/**
 * KHỐI trong thân trang. Tập ĐÓNG và cố định — học sinh sắp xếp lại các khối đã
 * có, không tạo thẻ mới. Đó là ranh giới giữa "thao tác trực tiếp có ràng buộc"
 * và một trình soạn thảo HTML (vẫn DEFERRED).
 */
export type WebBlock = "heading" | "paragraph";

/** Thứ có thể CHỌN: khung trang, hoặc một khối trong thân trang. */
export type WebNode = "page" | WebBlock;

export const WEB_NODES: readonly WebNode[] = ["page", "heading", "paragraph"];

/** Bộ chọn CSS ứng với từng nút — cùng chuỗi mà bảng kiểu in ra. */
export const SELECTOR_OF: Record<WebNode, string> = {
  page: ".trang",
  heading: ".trang h1",
  paragraph: ".trang p",
};

export const NODE_LABEL: Record<WebNode, string> = {
  page: "Khung trang",
  heading: "Tiêu đề",
  paragraph: "Đoạn văn",
};

export interface WebState {
  heading: string;
  paragraph: string;
  style: WebStyle;
  /**
   * THỨ TỰ TÀI LIỆU của các khối trong `.trang`. Đây là thứ HTML sở hữu mà CSS
   * không sở hữu: đổi thứ tự thì cấu trúc thẻ đổi còn bảng kiểu KHÔNG đổi — và
   * chính chỗ lệch đó là bài học.
   */
  order: WebBlock[];
  /**
   * Khối/khung đang được chọn. Nằm trong state chứ không nằm trong renderer vì
   * cả sân khấu, cột điều khiển và Inspector đều phải nói về CÙNG một nút; để
   * renderer giữ thì sẽ có ba bản chọn khác nhau của cùng một trang.
   */
  selected: WebNode;
  /** Bản gốc đã validate — "Về ban đầu" là phép toán, không phải undo log. */
  baseline: WebStyle;
  /** Thứ tự gốc, để "Về ban đầu" trả lại cả cấu trúc chứ không chỉ màu sắc. */
  baselineOrder: WebBlock[];
}
