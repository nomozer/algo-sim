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
  style: { maxWidth: string; height: string; display: string };
} {
  return {
    width,
    style: { maxWidth: "100%", height: "auto", display: "block" },
  };
}
