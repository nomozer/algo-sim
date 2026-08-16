/**
 * M19 — KÍCH THƯỚC SVG SÂN KHẤU: MỘT LUẬT, MỘT CHỦ SỞ HỮU.
 *
 * ─── VÌ SAO PHẢI GOM VỀ ĐÂY ───────────────────────────────────────────────
 *
 * Sáu renderer cùng viết một dạng: `width="100%"` + `style={{ maxWidth: w }}`.
 * Dạng đó có hai hệ quả, cả hai đều đo được:
 *
 *   1. Nó KHÔNG khai bề rộng riêng, nên khi cha là `fit-content` (khung ôm nội
 *      dung) thì `100%` không có gì để quy chiếu và Chrome rơi về bề rộng mặc
 *      định 300px của phần tử thay thế. `logic.boolean_dag` đã dính đúng lỗi
 *      này: sơ đồ 662px bị vẽ ở 300px (W4B-4D).
 *   2. Nó buộc phải kèm `margin: 0 auto` để trông cân trong lớp bọc giãn — và
 *      chính cú căn giữa đó tạo ra RAIL THỨ HAI: hình ở giữa, chữ ở mép trái.
 *      Đo được: `and_gate` lệch 581px, `decimal_to_binary` 673px.
 *
 * Dạng đúng ngược lại: **khai bề rộng THẬT, rồi cho phép co**. Bề rộng riêng
 * làm khung `fit-content` ôm đúng cơ chế, và khi khung đã ôm đúng thì hình
 * không cần căn giữa nữa — mép trái của nó CHÍNH LÀ rail của khung.
 *
 * Tỉ lệ phóng vẫn ≤ 1 y như trước: `max-width: 100%` chỉ cho co, không cho
 * phóng. Đây là bất biến cũ của `dag-module.tsx`, nay áp cho mọi renderer.
 */

/** Props kích thước cho một `<svg>` sân khấu có `viewBox` rộng `width`. */
export function stageSvgSize(width: number): {
  width: number;
  style: { maxWidth: string; height: string; display: string; marginInline: string };
} {
  return {
    width,
    /* W5H/3 — CĂN GIỮA KHI SÂN KHẤU HẸP HƠN THẺ.
     *
     * `arrayChartLayout` kẹp bề rộng cột ở trần mật độ, nên khi thẻ rộng hơn
     * mức biểu đồ dùng được thì phần dư dồn hết sang PHẢI: đo trên sản phẩm là
     * 52px trái / 190px phải — hình đọc ra lệch.
     *
     * `margin-inline: auto` chia đều phần dư. Sân khấu nào đã lấp kín thẻ thì
     * phần dư bằng 0 nên không đổi gì.
     *
     * ⚠️ M19 từng GỠ `margin: 0 auto` khỏi đây, và việc đưa lại KHÔNG phải quên
     * bài học đó. Lúc ấy thẻ là `fit-content` — thẻ luôn bằng đúng sân khấu, nên
     * căn giữa không chia được gì mà chỉ tạo hệ căn lề thứ hai chọi với thẻ.
     * Nay thẻ lấy bề rộng từ cột chứa (W5H), thẻ RỘNG HƠN sân khấu là chuyện
     * thường, nên phần dư có thật và phải được chia.
     *
     * ⚠️ ĐÁNH ĐỔI ĐÃ CHỌN: biểu đồ thôi thẳng hàng với tiêu đề và chú giải bên
     * dưới. Chủ đề tài chọn lề cân hơn là thẳng rail. */
    style: { maxWidth: "100%", height: "auto", display: "block", marginInline: "auto" },
  };
}
