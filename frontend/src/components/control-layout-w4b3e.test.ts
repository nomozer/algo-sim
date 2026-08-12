import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

/**
 * W4B-3E — DẢI ĐIỀU KHIỂN CÓ BỐ CỤC, KHÔNG PHẢI MỘT HÀNG PHẲNG.
 *
 * ─── ĐO ĐƯỢC TRƯỚC KHI SỬA (Chrome thật, `.player-controls`) ──────────────
 *
 *   1920: khoảng hở giữa hai phần tử CÙNG hàng = 633px
 *   1536: 421px · 1366: 251px · 768: 3 tầng, lệch 41px
 *
 * Khoảng hở đó **scale theo bề rộng màn hình** — dấu hiệu chắc chắn rằng nó là
 * PHẦN CÒN LẠI, không phải một khoảng cách ai đó chọn. Nguyên nhân:
 * `.speed-control { margin-left: auto }` — một THÀNH VIÊN quyết bố cục của cả
 * hàng, và mọi thứ đứng sau nó bị đẩy theo.
 *
 * ─── VÌ SAO KHOÁ NHƯ THẾ NÀY ──────────────────────────────────────────────
 *
 * Không khoá "phải có đúng N phần tử" hay "class phải tên X" — đó là khoá HÌNH
 * DẠNG, nó đỏ khi refactor lành và im khi bố cục hỏng. Khoá đúng hai điều đã
 * gây ra lỗi đo được:
 *
 *   (1) lệnh đẩy `margin-left:auto` chỉ được đặt trên VÙNG, không trên thành viên;
 *   (2) dải điều khiển không chứa câu văn dài thường trực.
 *
 * Phần hình học (1 hàng ở desktop, ≤2 tầng ở 768, hở ≤ 24px) do nghiệm thu
 * trình duyệt giữ — CSS không kiểm được bằng cách đọc chuỗi.
 */

const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf-8");
const tsx = readFileSync(new URL("./SimulationControls.tsx", import.meta.url), "utf-8")
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .replace(/^\s*\/\/.*$/gm, "");

/** Thân của một rule CSS theo selector chính xác. */
function ruleBody(selector: string): string {
  const i = css.indexOf(`\n${selector} {`);
  if (i < 0) return "";
  return css.slice(i, css.indexOf("}", i));
}

describe("W4B-3E · lệnh đẩy thuộc về VÙNG, không thuộc về thành viên", () => {
  it("`.speed-control` KHÔNG được tự đẩy — nó là thành viên, không phải bố cục", () => {
    /* Đây là nguyên nhân gốc của khoảng hở 633px. Đặt lại `margin-left:auto`
       vào đây là tái tạo đúng lỗi cũ. */
    expect(ruleBody(".speed-control"), "speed-control lại tự quyết bố cục cả hàng")
      .not.toMatch(/margin-left:\s*auto/);
  });

  it("chỉ VÙNG PHỤ được mang lệnh đẩy, và chỉ một chỗ", () => {
    const pushers = [...css.matchAll(/\n([.#][\w-]+(?:[^{\n]*)?)\s*\{[^}]*margin-left:\s*auto/g)]
      .map((m) => m[1].trim());
    // Phép dò phải thật sự dò: 0 kết quả trông y hệt một regex hỏng.
    expect(pushers.length, "không tìm thấy lệnh đẩy nào — regex hỏng?").toBeGreaterThan(0);
    const inControls = pushers.filter((s) => s.includes("control") || s.includes("player"));
    for (const s of inControls) {
      expect(s, `lệnh đẩy đặt trên thành viên: ${s}`).toContain("control-zone-aux");
    }
  });

  it("thanh tua ĂN chỗ thừa — nếu không, chỗ thừa quay lại thành khoảng chết", () => {
    /* Ba vùng thôi thì chưa đủ: bản đầu chỉ dời chỗ trống chứ không xoá
       (633 → 796px). Chỗ trống chỉ biến mất khi có thứ dùng được nó. */
    expect(ruleBody(".player-progress")).toMatch(/flex:\s*1/);
  });
});

describe("W4B-3E · không có văn xuôi dài thường trực trong dải điều khiển", () => {
  it("gợi ý phím tắt không còn là một phần tử hiển thị trong hàng", () => {
    expect(tsx, "chuỗi phím tắt quay lại thành nội dung hiển thị")
      .not.toMatch(/>\s*←\s*→/);
  });

  it("nội dung mô tả KHÔNG bị vứt đi — nó phải còn ở tên khả truy cập", () => {
    /* Ràng buộc đối trọng: cách rẻ nhất để "gọn" là xoá chữ, và làm thế là
       lấy bố cục đổi lấy khả dụng. Cả hai câu dài phải còn sống ở `aria-label`. */
    expect(tsx).toMatch(/aria-label="Điều khiển bước[^"]*Space/);
    expect(tsx).toMatch(/aria-label="Mô phỏng khám phá[^"]*sân khấu"/);
  });

  it("mỗi lối vào phụ vẫn tự mô tả qua tiêu đề/tên, không phải nhãn trần", () => {
    /* Nhãn HIỂN THỊ được rút gọn ("Khám phá"/"Thử thách") để hàng không xuống
       dòng, nhưng tên KHẢ TRUY CẬP phải là câu đầy đủ GHÉP với câu mời-thử.
       Rút gọn cả hai là lấy bố cục đổi lấy khả dụng — đúng thứ cần chặn. */
    expect(tsx, "câu mời không còn được ghép vào tên khả truy cập")
      .toMatch(/\[entry\.label,\s*entry\.hint\][\s\S]{0,80}join/);
    expect(tsx).toMatch(/title=\{open \? undefined : full\}/);
    expect(tsx).toMatch(/aria-label=\{open \? undefined : full\}/);
  });
});
