import { describe, expect, it } from "vitest";
import {
  IMAGE_ACCEPT,
  MAX_ATTACHMENTS,
  MAX_ATTACHMENT_BYTES,
  acceptAttr,
  canSubmitComposer,
  extOf,
  formatAttachmentSize,
  imageMimeOf,
  isImageFile,
  kindFromFile,
  kindLabel,
  splitAttachmentName,
  validateComposerFile,
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
    expect(a).not.toContain(".pdf");
  });

  it("nhãn tiếng Việt cho từng loại", () => {
    expect(kindLabel("code")).toBe("Mã nguồn");
    expect(kindLabel("document")).toBe("Tài liệu Word");
    expect(kindLabel("image")).toBe("Ảnh đề bài");
  });
});

describe("Axo V2.7 Slice 2 — validateComposerFile & canSubmitComposer", () => {
  it("từ chối tệp PDF (.pdf) rõ ràng theo quyết định D3, không giả hỗ trợ", () => {
    const resByExt = validateComposerFile({
      name: "de-thi-hk1.pdf",
      size: 120_000,
      type: "application/pdf",
    });
    expect(resByExt.ok).toBe(false);
    if (!resByExt.ok) {
      expect(resByExt.code).toBe("pdf_unsupported");
      expect(resByExt.reason).toContain("PDF");
    }

    const resByMime = validateComposerFile({
      name: "tai-lieu",
      size: 50_000,
      type: "application/pdf",
    });
    expect(resByMime.ok).toBe(false);
    if (!resByMime.ok) {
      expect(resByMime.code).toBe("pdf_unsupported");
    }
  });

  it("từ chối định dạng lạ và không gán mặc định sang kind hợp lệ", () => {
    const res = validateComposerFile({
      name: "archive.rar",
      size: 2048,
      type: "application/octet-stream",
    });
    expect(res.ok).toBe(false);
    if (!res.ok) {
      expect(res.code).toBe("unsupported_format");
    }
  });

  it("từ chối tệp rỗng (0 B) hoặc vượt quá 10 MB", () => {
    const emptyRes = validateComposerFile({
      name: "de-toan.docx",
      size: 0,
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    expect(emptyRes.ok).toBe(false);
    if (!emptyRes.ok) {
      expect(emptyRes.code).toBe("empty_file");
    }

    const hugeRes = validateComposerFile({
      name: "anh-nang.png",
      size: MAX_ATTACHMENT_BYTES + 1,
      type: "image/png",
    });
    expect(hugeRes.ok).toBe(false);
    if (!hugeRes.ok) {
      expect(hugeRes.code).toBe("too_large");
    }
  });

  it("từ chối tệp trùng lặp và giới hạn số lượng tệp tối đa", () => {
    const dupRes = validateComposerFile(
      { name: "de-1.docx", size: 4096 },
      [{ name: "de-1.docx", size: 4096 }],
    );
    expect(dupRes.ok).toBe(false);
    if (!dupRes.ok) {
      expect(dupRes.code).toBe("duplicate_file");
    }

    const existingMax = Array.from({ length: MAX_ATTACHMENTS }, (_, i) => ({
      name: `de-${i}.png`,
      size: 1024 + i,
    }));
    const maxRes = validateComposerFile({ name: "them.png", size: 2048 }, existingMax);
    expect(maxRes.ok).toBe(false);
    if (!maxRes.ok) {
      expect(maxRes.code).toBe("too_many_files");
    }
  });

  it("chấp nhận .docx, .png, .jpg, .webp hợp lệ và từ chối .py trên Composer hình học (P5.4)", () => {
    expect(validateComposerFile({ name: "de-chop.docx", size: 18_432 })).toEqual({
      ok: true,
      kind: "document",
      ext: ".docx",
    });
    expect(validateComposerFile({ name: "hinh-chop.png", size: 95_000, type: "image/png" })).toEqual({
      ok: true,
      kind: "image",
      ext: ".png",
    });
    const pyRes = validateComposerFile({ name: "script.py", size: 1024 });
    expect(pyRes.ok).toBe(false);
    if (!pyRes.ok) {
      expect(pyRes.code).toBe("unsupported_format");
    }
  });

  it("canSubmitComposer: không áp đặt tối thiểu 10 ký tự; tắt khi rỗng/whitespace/bận, bật khi có chữ hoặc tệp", () => {
    expect(canSubmitComposer("", 0, false)).toBe(false);
    expect(canSubmitComposer("   \n\t  ", 0, false)).toBe(false);
    // Kể cả văn bản ngắn < 10 ký tự vẫn được bật nút Dựng hình →
    expect(canSubmitComposer("S.ABC", 0, false)).toBe(true);
    expect(canSubmitComposer("Cho hình chóp S.ABCD", 0, false)).toBe(true);
    // Không chữ nhưng có 1 tệp hợp lệ → bật
    expect(canSubmitComposer("", 1, false)).toBe(true);
    // Đang gửi hoặc đang đọc tệp → khóa
    expect(canSubmitComposer("Cho hình chóp S.ABCD", 1, true)).toBe(false);
    expect(canSubmitComposer("Cho hình chóp S.ABCD", 1, false, true)).toBe(false);
  });

  it("formatAttachmentSize & splitAttachmentName định dạng đúng dung lượng thật và tên tệp", () => {
    expect(formatAttachmentSize(0)).toBe("0 B");
    expect(formatAttachmentSize(512)).toBe("512 B");
    expect(formatAttachmentSize(2048)).toBe("2.0 KB");
    expect(formatAttachmentSize(245_760)).toBe("240 KB");
    expect(formatAttachmentSize(2 * 1024 * 1024)).toBe("2.00 MB");

    expect(splitAttachmentName("de-toan-hinh-chop-sabcd.docx")).toEqual({
      stem: "de-toan-hinh-chop-sabcd",
      extWithDot: ".docx",
    });
  });
});
