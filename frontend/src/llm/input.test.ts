import { describe, expect, it } from "vitest";
import { acceptAttr, extOf, kindFromFile, kindLabel } from "./input";

/**
 * Test phần phân loại file (pure) — M4 §13 frontend:
 * nhận đúng loại từ đuôi, từ chối đuôi không hỗ trợ.
 */

describe("extOf", () => {
  it("lấy đuôi chữ thường, rỗng khi không có", () => {
    expect(extOf("bai.PY")).toBe(".py");
    expect(extOf("de.docx")).toBe(".docx");
    expect(extOf("anh.JPEG")).toBe(".jpeg");
    expect(extOf("khongduoi")).toBe("");
    expect(extOf("a.b.c.py")).toBe(".py");
  });
});

describe("kindFromFile", () => {
  it("code từ .py và các đuôi lập trình", () => {
    expect(kindFromFile("sol.py")).toBe("code");
    expect(kindFromFile("a.ts")).toBe("code");
    expect(kindFromFile("Main.java")).toBe("code");
  });

  it("document từ .docx", () => {
    expect(kindFromFile("de.docx")).toBe("document");
  });

  it("image từ png/jpg/jpeg/webp", () => {
    expect(kindFromFile("a.png")).toBe("image");
    expect(kindFromFile("b.JPG")).toBe("image");
    expect(kindFromFile("c.jpeg")).toBe("image");
    expect(kindFromFile("d.webp")).toBe("image");
  });

  it("từ chối đuôi không hỗ trợ", () => {
    expect(kindFromFile("virus.exe")).toBeNull();
    expect(kindFromFile("data.csv")).toBeNull();
    expect(kindFromFile("a.pdf")).toBeNull();
    expect(kindFromFile("khongduoi")).toBeNull();
  });
});

describe("acceptAttr / kindLabel", () => {
  it("accept chứa các đuôi hỗ trợ", () => {
    const a = acceptAttr();
    expect(a).toContain(".py");
    expect(a).toContain(".docx");
    expect(a).toContain(".png");
    expect(a).not.toContain(".exe");
  });

  it("nhãn tiếng Việt cho từng loại", () => {
    expect(kindLabel("code")).toBe("Mã nguồn");
    expect(kindLabel("document")).toBe("Tài liệu Word");
    expect(kindLabel("image")).toBe("Ảnh đề bài");
  });
});
