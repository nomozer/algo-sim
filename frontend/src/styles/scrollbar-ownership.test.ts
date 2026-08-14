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
  it("thumb webkit có màu ở trạng thái MẶC ĐỊNH, không chỉ khi hover", () => {
    const bg = declOf(GLOBAL, "::-webkit-scrollbar-thumb", "background-color")
      ?? declOf(GLOBAL, "::-webkit-scrollbar-thumb", "background");
    /* Trống nghĩa là selector đã đổi tên — phải ĐỎ, không được lặng lẽ đạt.
       Đây là cùng cái bẫy đã làm ba guard W8 "đạt" khi chúng khớp rỗng. */
    expect(bg, "không tìm thấy ::-webkit-scrollbar-thumb — selector đã đổi?").not.toBeNull();
    expect(bg, "thumb trong suốt ⇒ máng đã giữ chỗ sẽ đọc thành khe hở").not.toBe("transparent");
  });

  it("Firefox: `scrollbar-color` mặc định cũng không trong suốt", () => {
    const color = declOf(GLOBAL, "*", "scrollbar-color");
    expect(color, "không tìm thấy khai báo scrollbar-color").not.toBeNull();
    expect(color, "Firefox vẫn tàng hình dù webkit đã sửa — đúng hình dạng "
      + "anti-pattern #10: vá một bề mặt, quên bề mặt anh em")
      .not.toMatch(/^transparent\s+transparent$/);
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
