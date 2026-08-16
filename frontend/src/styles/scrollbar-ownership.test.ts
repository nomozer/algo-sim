/**
 * scrollbar-ownership.test.ts — W12 §4/§5: THANH CUỘN PHẢI THẤY ĐƯỢC.
 *
 * ─── VÌ SAO CẦN MỘT CỔNG RIÊNG ─────────────────────────────────────────────
 *
 * "Thanh cuộn mảnh, chìm" là một ý đúng, nhưng nó trượt được — và đã trượt: bản
 * trước đặt `scrollbar-color: transparent transparent` cùng thumb webkit
 * `background: transparent`, tức mặc định KHÔNG NHÌN THẤY GÌ. Không có gì đỏ ở
 * đâu cả, vì CSS không có lỗi cú pháp và không test nào hỏi câu này.
 *
 * Hệ quả nhìn thấy được trên ảnh chụp: `scrollbar-gutter: stable` vẫn giữ chỗ,
 * nên cạnh header có một dải dọc RỖNG chạy suốt tài liệu — đọc ra là khe hở
 * chứ không phải máng cuộn.
 *
 * Nên test này khoá đúng một câu: **mức mặc định có khác `transparent` không.**
 * Nó KHÔNG khoá giá trị cụ thể — đổi tông là việc của thiết kế, biến mất thì
 * không.
 */
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const css = (name: string) =>
  readFileSync(fileURLToPath(new URL(`./${name}`, import.meta.url)), "utf-8");

const GLOBAL = css("global.css");
const TOKENS = css("tokens.css");

/**
 * Đọc một khai báo trong CÁC khối CSS khớp selector.
 *
 * ⚠️ Quét MỌI khối, không chỉ khối đầu: bản đầu của hàm này dùng `indexOf` nên
 * với selector `*` nó rơi vào reset `box-sizing` ở đầu file rồi trả `null` —
 * tức guard báo "không tìm thấy" cho một khai báo đang tồn tại. Lần này sai
 * theo hướng an toàn (đỏ), nhưng cùng cái sai ấy đi hướng ngược là một guard
 * khớp rỗng rồi ĐẠT.
 */
function declOf(source: string, selector: string, prop: string): string | null {
  const needle = selector + " {";
  const re = new RegExp(`(?:^|\\n)\\s*${prop}\\s*:\\s*([^;]+);`);
  for (let at = source.indexOf(needle); at !== -1; at = source.indexOf(needle, at + 1)) {
    const end = source.indexOf("}", at);
    const m = re.exec(source.slice(at, end === -1 ? source.length : end));
    if (m) return m[1].trim();
  }
  return null;
}

describe("W12 §4 — thanh cuộn không được tàng hình", () => {
  /**
   * W6B — HỢP ĐỒNG ĐỔI: thanh cuộn nay dùng MẶC ĐỊNH của trình duyệt.
   *
   * Bất biến gốc — "thanh cuộn không được tàng hình" — KHÔNG đổi, nhưng nó nay
   * được bảo đảm bởi hệ điều hành thay vì bởi CSS của ta. Hai khẳng định cũ
   * (thumb webkit phải có màu · `scrollbar-color` không được trong suốt) vì thế
   * HẾT ĐỐI TƯỢNG: không còn khai báo nào để kiểm.
   *
   * Khoá điều đúng cho hợp đồng mới: KHÔNG được có bất kỳ ghi đè nào có thể làm
   * thanh cuộn tàng hình trở lại. Đó mới là thứ từng hỏng — bản trước W12 đặt
   * `scrollbar-color: transparent transparent` và thumb webkit trong suốt, nên
   * máng đã giữ chỗ đọc ra thành một khe hở trống.
   */
  it("KHÔNG ghi đè nào có thể làm thanh cuộn tàng hình trở lại", () => {
    const thumb = declOf(GLOBAL, "::-webkit-scrollbar-thumb", "background-color")
      ?? declOf(GLOBAL, "::-webkit-scrollbar-thumb", "background");
    expect(thumb, "đã vẽ lại thumb — nếu cố ý thì phải khoá lại màu mặc định ở đây")
      .toBeNull();

    const color = declOf(GLOBAL, "*", "scrollbar-color");
    expect(color, "đã ghi đè `scrollbar-color` — chính là đường làm nó tàng hình")
      .toBeNull();

    /* Nút mũi tên hai đầu là tín hiệu "cuộn được" của hệ điều hành. Bản trước
       ẩn chúng đi cho gọn; nay không được ẩn nữa. */
    /* Bóc chú thích trước khi khớp — cùng quy ước với mọi guard quét nguồn
       khác trong repo. Không bóc thì chính đoạn chú thích mô tả BẢN CŨ sẽ làm
       guard đỏ, tức guard tự vấp vào tài liệu của mình. */
    const code = GLOBAL.replace(/\/\*[\s\S]*?\*\//g, "");
    expect(code, "vẫn ẩn nút mũi tên của thanh cuộn hệ điều hành")
      .not.toMatch(/::-webkit-scrollbar-button\s*\{[^}]*display:\s*none/);
  });

  it("ba mức đậm dần đều có định nghĩa (var() trỏ hụt là lỗi IM LẶNG)", () => {
    for (const token of ["--scroll-thumb", "--scroll-thumb-strong", "--scroll-thumb-hover"]) {
      expect(TOKENS, `${token} chưa được định nghĩa`).toContain(`${token}:`);
    }
  });

  it("máng vẫn giữ chỗ ⇒ nội dung không nhảy khi trang trở nên cuộn được", () => {
    /* §5: "no width jump between short and long pages". Giữ chỗ là việc của
       `scrollbar-gutter`; bỏ nó đi để "hết khe hở" sẽ đổi một lỗi thị giác lấy
       một lỗi bố cục nặng hơn. */
    expect(declOf(GLOBAL, "html", "scrollbar-gutter")).toBe("stable");
  });

  /**
   * ĐỐI CHỨNG DƯƠNG — một guard chưa từng đỏ là một guard chưa được chứng minh.
   * Dựng lại đúng bản CSS cũ và bắt chính hàm đọc ở trên phải bắt được nó.
   */
  it("(đối chứng) bản CSS cũ (thumb transparent) bị guard này bắt", () => {
    const oldCss = "::-webkit-scrollbar-thumb {\n  background: transparent;\n  border-radius: 999px;\n}";
    expect(declOf(oldCss, "::-webkit-scrollbar-thumb", "background")).toBe("transparent");
  });
});
