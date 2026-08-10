import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";

/**
 * W4B-2Y — KẾT QUẢ MÔ PHỎNG KHÔNG PHẢI PHẢN HỒI QUIZ, VÀ KHÔNG CHIẾM MỘT DẢI.
 *
 * Lỗi cấu trúc: kết quả tất định chiếm trọn một hàng nội dung, có nền thẻ và
 * vạch xanh lá cạnh trái — đọc thành "Đúng rồi!" trong khi học sinh chưa trả
 * lời gì. Sửa ở cấu trúc (`fit-content`, bỏ vạch cạnh), không ở màu.
 */

const css = () =>
  readFileSync(new URL("../styles/global.css", import.meta.url), "utf-8");

const blockOf = (name: string) => {
  const c = css();
  const i = c.indexOf(`${name} {`);
  return i < 0 ? "" : c.slice(i, c.indexOf("}", i));
};

describe("W4B-2Y · kết quả mô phỏng là CHÚ THÍCH, không phải DẢI", () => {
  it("không còn chiếm trọn một hàng nội dung", () => {
    expect(blockOf(".result-banner")).toMatch(/width:\s*fit-content/);
  });

  it("không còn ngữ pháp 'thẻ thông báo' (vạch màu cạnh trái)", () => {
    expect(blockOf(".result-banner")).not.toMatch(/border-left/);
  });

  it("KHÔNG mặc áo thành công: không viền/nền xanh lá báo đúng", () => {
    const b = blockOf(".result-banner");
    expect(b).not.toContain("--accent-green");
  });

  it("vẫn PHÂN BIỆT với phản hồi thử thách — hai ngữ nghĩa, hai chủ sở hữu", () => {
    /* `.predict-result` là phán quyết về HỌC SINH; `.result-banner` là đầu ra
       của ENGINE. Gộp chúng lại chính là thứ làm mô phỏng trông như bài kiểm. */
    expect(css()).toContain(".predict-result");
    expect(blockOf(".result-banner")).not.toContain("predict");
  });
});
