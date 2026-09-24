import { describe, expect, it } from "vitest";
import {
  IMAGE_ACCEPT,
  acceptAttr,
  extOf,
  imageMimeOf,
  isImageFile,
  kindFromFile,
  kindLabel,
} from "./input";

describe("ảnh đề bài (PHOTO_PROBLEM_TO_SCENE_END_TO_END)", () => {
  it("accept của Chụp ảnh / Tải ảnh chỉ gồm ba MIME ảnh", () => {
    expect(IMAGE_ACCEPT).toBe("image/png,image/jpeg,image/webp");
  });

  it("nhận ảnh theo MIME TRƯỚC — ảnh máy ảnh có thể không có đuôi", () => {
    expect(isImageFile({ name: "image", type: "image/jpeg" })).toBe(true);
    expect(isImageFile({ name: "a.webp", type: "" })).toBe(true);
    expect(isImageFile({ name: "de.pdf", type: "application/pdf" })).toBe(false);
    expect(isImageFile({ name: "hinh.gif", type: "image/gif" })).toBe(false);
  });

  it("MIME khai kèm theo cùng thứ tự ưu tiên", () => {
    expect(imageMimeOf({ name: "x", type: "image/png" })).toBe("image/png");
    expect(imageMimeOf({ name: "x.JPG", type: "" })).toBe("image/jpeg");
    expect(imageMimeOf({ name: "x.bin", type: "" })).toBeUndefined();
  });
});

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
