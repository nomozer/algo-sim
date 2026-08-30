/**
 * ĐỌC MÃ NGUỒN CHO GUARD — bóc chú thích trước khi quét.
 *
 * ─── VÌ SAO TỒN TẠI: MỘT LỚP LỖI ĐÃ LẶP BỐN LẦN ─────────────────────────
 *
 * Guard "file X không được chạm Y" quét thẳng nội dung file, rồi ĐỎ vì chính
 * **chú thích giải thích rằng nó không chạm Y**. Bốn lần, bốn wave khác nhau:
 *
 *   `scene3d-page.test.tsx`      — chú thích *"vì sao không dùng visual_mode"*
 *   `canvas-first-shell.test.tsx`— cùng câu ấy
 *   `test_live_session_api.py`   — docstring *"GeometryState do kernel sở hữu"*
 *   `live-classroom.test.tsx`    — *"«đang gặp khó» thì không"*
 *
 * Mỗi lần đều vá tại chỗ, nên lần sau lại xảy ra. Guard khoá **chính tả** thay
 * vì khoá **ý định** thì nói dối theo cả hai chiều: đỏ oan như trên, và xanh
 * oan khi ai đó viết đúng thứ bị cấm bên trong một chuỗi.
 *
 * ⚠️ KHÔNG dùng hàm này khi thứ bị cấm không được phép xuất hiện **kể cả trong
 * lời bàn** — ví dụ một nguyên thuỷ chiếu màn hình. Ở đó quét cả chú thích mới
 * đúng, và đó là một quyết định khác, không phải một cách dùng khác.
 */
import { readFileSync } from "node:fs";

/**
 * Nội dung file, đã bóc chú thích khối và chú thích dòng.
 *
 * Bóc bằng biểu thức chính quy, không phải bằng trình phân tích cú pháp: một
 * `//` nằm trong chuỗi (`"https://…"`) sẽ bị cắt oan. Chấp nhận được vì guard
 * chỉ hỏi *"chuỗi cấm có xuất hiện trong mã không"* — cắt thừa làm guard chặt
 * hơn chứ không lỏng hơn, và một guard chặt quá thì đỏ và có người đọc, còn
 * một guard lỏng thì xanh và không ai biết.
 */
export function docMa(url: URL | string): string {
  return readFileSync(url as never, "utf-8")
    .replace(/\/\*[\s\S]*?\*\//g, " ")
    .replace(/^\s*\/\/.*$/gm, " ");
}

/**
 * Rỗng-là-hỏng: bóc sai thì mọi `not.toContain` bên dưới xanh vô nghĩa.
 *
 * Gọi nó ngay sau `docMa` trong mỗi guard. Một dòng, và nó là khác biệt giữa
 * "đã kiểm" với "tưởng đã kiểm".
 */
export function maConDu(ma: string, moc: string, toiThieu = 500): boolean {
  return ma.includes(moc) && ma.length >= toiThieu;
}
