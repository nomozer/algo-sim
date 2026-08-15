/**
 * svg-affordance.ts — MỘT HÌNH SVG BẤM ĐƯỢC THÌ PHẢI BẤM ĐƯỢC BẰNG BÀN PHÍM.
 *
 * ─── LỖI CÓ THẬT MÀ FILE NÀY ĐÓNG ─────────────────────────────────────────
 *
 * Cùng một idiom — "một `<g>` có `cursor: pointer` và `onClick`" — được dựng ở
 * năm chỗ và làm ĐÚNG ở hai. Đo trên trình duyệt thật ở `1536px`:
 *
 *   logic.and_gate         13 phần tử focus được, KHÔNG cái nào là công tắc A/B
 *   binary.decimal_to_binary  bit bấm được bằng chuột, không có trong tab order
 *   generic.rule_scene     sửa đối tượng chỉ qua chuột/kéo
 *
 * Ba target ấy đều được xếp `INTERACTIVE_MODEL` hoặc công cụ có ràng buộc —
 * tức thao tác mô hình LÀ bài học, và người dùng bàn phím không vào được bài
 * học. Đây không phải chuyện trang trí: nó là mất chính cơ chế.
 *
 * ─── VÌ SAO LÀ HÀM TRẢ PROPS, KHÔNG PHẢI COMPONENT ────────────────────────
 *
 * Các chỗ gọi đang trải props vào `<g>`, `<line>`, `<rect>` khác nhau và có
 * hình học riêng. Một component bọc sẽ ép thêm một tầng `<g>` vào cây SVG và
 * làm lệch phép đo hình học đã chứng nhận (`audit-composition.mjs`,
 * `certify-visual-weight-w12.mjs` đếm phần tử theo cấu trúc). Trả props thì
 * cây SVG không đổi một nút nào.
 *
 * ─── HAI CHỖ LÀM ĐÚNG TRƯỚC ĐÓ, GIỮ NGUYÊN ────────────────────────────────
 *
 * `domains/network/ui.tsx::LinkHandle` và `domains/logic/dag-module.tsx` đã tự
 * nối đúng hợp đồng này và đã qua chứng nhận. Chúng KHÔNG bị viết lại theo
 * helper trong wave này: đổi mã đã chứng nhận để cho đẹp là đánh đổi rủi ro hồi
 * quy lấy tính đối xứng. Chúng là nguồn gốc của khuôn dưới đây.
 */
import type { CSSProperties, KeyboardEvent, MouseEvent } from "react";

export interface SvgAffordanceProps {
  className: "sim-affordance";
  role: "button";
  tabIndex: 0;
  "aria-label": string;
  "aria-pressed"?: boolean;
  onClick: (e: MouseEvent) => void;
  onKeyDown: (e: KeyboardEvent) => void;
  style: CSSProperties;
}

/**
 * @param label   TÊN ĐỌC LÊN ĐƯỢC — phải nói *bấm vào sẽ ra gì*, không phải tên
 *                hình. Trình đọc màn hình đọc đúng chuỗi này và không có gì khác.
 * @param onAct   chỉ PHÁT hành động; engine tất định mới là nơi tính lại.
 * @param pressed trạng thái bật/tắt, nếu affordance là công tắc. Có nó thì trạng
 *                thái không còn chỉ nằm ở MÀU — đúng điều kiện
 *                `STATE_NOT_COLOR_ONLY`.
 */
export function svgAffordance(
  { label, onAct, pressed }: { label: string; onAct: () => void; pressed?: boolean },
): SvgAffordanceProps {
  return {
    /* LỚP LÀ BẮT BUỘC, KHÔNG PHẢI TRANG TRÍ.
       Đo lần đầu sau khi nối bàn phím: affordance tới được bằng Tab nhưng
       `outline-style` vẫn là `none` cả trước lẫn sau khi focus — người dùng bàn
       phím vào được cơ chế mà KHÔNG THẤY mình đang ở đâu. `.dag-input` và
       `.net-link-handle` đã có luật `:focus-visible` riêng; lớp này mang cùng
       luật ấy cho mọi affordance dựng qua helper. */
    className: "sim-affordance",
    role: "button",
    tabIndex: 0,
    "aria-label": label,
    ...(pressed === undefined ? {} : { "aria-pressed": pressed }),
    onClick: (e) => {
      e.stopPropagation();
      onAct();
    },
    onKeyDown: (e) => {
      if (e.key !== "Enter" && e.key !== " ") return;
      /* `preventDefault` chặn cuộn trang khi bấm Space; `stopPropagation` là bắt
         buộc vì Space còn là phím tắt TỰ CHẠY toàn cục — thiếu nó thì một cú
         Space vừa đổi đầu vào vừa cho mô phỏng chạy, và học sinh thấy hai việc
         xảy ra từ một phím. Bài học lấy từ `network/ui.tsx::LinkHandle`. */
      e.preventDefault();
      e.stopPropagation();
      onAct();
    },
    style: { cursor: "pointer" },
  };
}
