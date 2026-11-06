/**
 * Chuẩn hóa file người dùng chọn về InputPayload chung (M4).
 * Phần phân loại (kindFromFile / acceptAttr) là pure → test được;
 * fileToPayload đọc nội dung file (text hoặc base64) ở trình duyệt.
 */

export type InputKind = "text" | "code" | "document" | "image";

export interface InputPayload {
  type: InputKind;
  content: string;
  filename?: string;
  mime_type?: string;
}

const CODE_EXTS = [".py", ".js", ".ts", ".c", ".cpp", ".java", ".pas"];
const IMAGE_EXTS = [".png", ".jpg", ".jpeg", ".webp"];
const DOC_EXTS = [".docx"];

/** Đuôi file (chữ thường, kèm dấu chấm) hoặc "" nếu không có. */
export function extOf(filename: string): string {
  const i = filename.lastIndexOf(".");
  return i < 0 ? "" : filename.slice(i).toLowerCase();
}

/** Loại input suy từ tên file; null nếu đuôi không được hỗ trợ. */
export function kindFromFile(filename: string): Exclude<InputKind, "text"> | null {
  const ext = extOf(filename);
  if (CODE_EXTS.includes(ext)) return "code";
  if (IMAGE_EXTS.includes(ext)) return "image";
  if (DOC_EXTS.includes(ext)) return "document";
  return null;
}

/** Thuộc tính accept cho <input type="file">. */
export function acceptAttr(): string {
  return [...CODE_EXTS, ...IMAGE_EXTS, ...DOC_EXTS].join(",");
}

/** MIME ảnh đề bài được nhận (PHOTO_PROBLEM_TO_SCENE_END_TO_END §2).
 *  Máy chủ vẫn là thẩm quyền: nó soi NỘI DUNG tệp, không tin MIME này. */
export const IMAGE_MIME_TYPES = ["image/png", "image/jpeg", "image/webp"] as const;

/** `accept` cho hai nút "Chụp ảnh" / "Tải ảnh". */
export const IMAGE_ACCEPT = IMAGE_MIME_TYPES.join(",");

function laMimeAnh(type: string | undefined): type is (typeof IMAGE_MIME_TYPES)[number] {
  return !!type && (IMAGE_MIME_TYPES as readonly string[]).includes(type);
}

/** Tệp có phải ảnh đề bài không. MIME trình duyệt báo đi TRƯỚC đuôi tệp: ảnh
 *  chụp từ máy ảnh điện thoại có thể mang tên chung chung hoặc không có đuôi. */
export function isImageFile(file: { name: string; type?: string }): boolean {
  return laMimeAnh(file.type) || kindFromFile(file.name) === "image";
}

/** MIME khai kèm ảnh gửi đi — cùng thứ tự ưu tiên với `isImageFile`. */
export function imageMimeOf(file: { name: string; type?: string }): string | undefined {
  return laMimeAnh(file.type) ? file.type : MIME_BY_EXT[extOf(file.name)];
}

export function kindLabel(kind: InputKind): string {
  switch (kind) {
    case "code":
      return "Mã nguồn";
    case "document":
      return "Tài liệu Word";
    case "image":
      return "Ảnh đề bài";
    case "text":
      return "Văn bản";
  }
}

const MIME_BY_EXT: Record<string, string> = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
};

function readAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result ?? ""));
    r.onerror = () => reject(new Error("Không đọc được file."));
    r.readAsText(file);
  });
}

/** Đọc tệp thành chuỗi base64 THUẦN (đã bỏ tiền tố `data:<mime>;base64,`). */
export function readAsBase64(file: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => {
      const result = String(r.result ?? "");
      // data URL "data:<mime>;base64,<payload>" → lấy phần payload
      const comma = result.indexOf(",");
      resolve(comma >= 0 ? result.slice(comma + 1) : result);
    };
    r.onerror = () => reject(new Error("Không đọc được file."));
    r.readAsDataURL(file);
  });
}

/** Đọc file đã chọn thành InputPayload; ném lỗi nếu đuôi không hỗ trợ. */
export async function fileToPayload(file: File): Promise<InputPayload> {
  const kind = kindFromFile(file.name) ?? (isImageFile(file) ? "image" : null);
  if (!kind) {
    throw new Error(
      "Định dạng file không được hỗ trợ. Chọn .py (mã nguồn), .docx (Word) hoặc ảnh .png/.jpg/.webp.",
    );
  }
  const ext = extOf(file.name);
  const mime = kind === "image" ? imageMimeOf(file) : MIME_BY_EXT[ext];
  if (kind === "code") {
    return { type: "code", content: await readAsText(file), filename: file.name };
  }
  return {
    type: kind,
    content: await readAsBase64(file),
    filename: file.name,
    mime_type: mime,
  };
}

/* ── Axo V2.7 Phase A (P5.4 & Decision D3) — Kiểm tra tệp đính kèm & trạng thái nút Dựng hình → ── */

export const MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024;
export const MAX_ATTACHMENTS = 10;

/** Danh sách định dạng tệp được nhận trên Composer hình học Axo V2.7 (không bao gồm .py hoặc .pdf). */
export const COMPOSER_ACCEPT = ".png,.jpg,.jpeg,.webp,.docx";

export interface ComposerAttachmentItem {
  id: string;
  file: File;
  name: string;
  size: number;
  sizeFormatted: string;
  ext: string;
  kind: Exclude<InputKind, "text"> | "pdf";
  previewUrl?: string;
  status?: "loading" | "ready" | "error";
  errorMessage?: string;
}

export type ComposerFileRejectionCode =
  | "empty_file"
  | "too_large"
  | "pdf_unsupported"
  | "unsupported_format"
  | "duplicate_file"
  | "too_many_files";

export type ComposerFileValidationResult =
  | {
      ok: true;
      kind: Exclude<InputKind, "text">;
      ext: string;
    }
  | {
      ok: false;
      code: ComposerFileRejectionCode;
      reason: string;
    };

/** Định dạng dung lượng tệp thực tế từ `file.size` (không giả lập dung lượng). */
export function formatAttachmentSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";
  if (bytes < 1024) return `${Math.round(bytes)} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb < 10 ? kb.toFixed(1) : Math.round(kb)} KB`;
  const mb = kb / 1024;
  return `${mb.toFixed(2)} MB`;
}

/** Tách phần thân và phần đuôi (kèm dấu chấm) để hiển thị gọn trên thẻ tệp. */
export function splitAttachmentName(fullName: string): { stem: string; extWithDot: string } {
  const safe = (fullName || "tep-dinh-kem").trim();
  const dot = safe.lastIndexOf(".");
  if (dot <= 0 || dot === safe.length - 1) {
    return { stem: safe, extWithDot: "" };
  }
  return {
    stem: safe.slice(0, dot),
    extWithDot: safe.slice(dot).toLowerCase(),
  };
}

/**
 * Kiểm tra tệp đính kèm theo đúng khả năng xử lý thực của backend (Decision D3 & P6.4–P6.5):
 * - Từ chối rõ ràng `.pdf` vì backend hiện chưa có bộ đọc PDF.
 * - Từ chối định dạng lạ (không bao giờ gán mặc định sang một `kind` hợp lệ).
 * - Từ chối tệp rỗng (`<= 0` byte) hoặc vượt quá 10 MB.
 * - Từ chối tệp trùng lặp hoặc vượt quá số lượng tối đa.
 */
export function validateComposerFile(
  file: { name: string; size: number; type?: string },
  existingFiles: ReadonlyArray<{ name: string; size: number }> = [],
): ComposerFileValidationResult {
  const ext = extOf(file.name);
  const mime = (file.type ?? "").toLowerCase().trim();

  if (ext === ".pdf" || mime === "application/pdf") {
    return {
      ok: false,
      code: "pdf_unsupported",
      reason:
        "Chưa hỗ trợ đọc trực tiếp tệp PDF (.pdf). Vui lòng đính kèm ảnh chụp đề bài (.png, .jpg, .webp) hoặc tệp Word (.docx).",
    };
  }

  const kind: "image" | "document" | null = isImageFile(file)
    ? "image"
    : ext === ".docx"
      ? "document"
      : null;

  if (!kind) {
    return {
      ok: false,
      code: "unsupported_format",
      reason:
        "Định dạng tệp chưa được hỗ trợ. Vui lòng chọn ảnh đề bài (.png, .jpg, .webp) hoặc tệp Word (.docx).",
    };
  }

  if (!Number.isFinite(file.size) || file.size <= 0) {
    return {
      ok: false,
      code: "empty_file",
      reason: `Tệp "${file.name}" đang rỗng (0 B). Vui lòng chọn tệp có nội dung.`,
    };
  }

  if (file.size > MAX_ATTACHMENT_BYTES) {
    return {
      ok: false,
      code: "too_large",
      reason: `Tệp "${file.name}" vượt quá giới hạn 10 MB.`,
    };
  }

  if (existingFiles.some((f) => f.name === file.name && f.size === file.size)) {
    return {
      ok: false,
      code: "duplicate_file",
      reason: `Tệp "${file.name}" đã có trong danh sách đính kèm.`,
    };
  }

  if (existingFiles.length >= MAX_ATTACHMENTS) {
    return {
      ok: false,
      code: "too_many_files",
      reason: `Chỉ đính kèm tối đa ${MAX_ATTACHMENTS} tệp cho một đề toán.`,
    };
  }

  const normalizedExt =
    ext ||
    (mime === "image/png"
      ? ".png"
      : mime === "image/webp"
        ? ".webp"
        : kind === "image"
          ? ".jpg"
          : "");

  return {
    ok: true,
    kind,
    ext: normalizedExt,
  };
}

/**
 * Nguồn chân lý duy nhất cho trạng thái bật/tắt nút `Dựng hình →` (P4.1 & Decision adjustment):
 * - Không áp đặt ngưỡng tối thiểu 10 ký tự.
 * - Chỉ cần văn bản sau khi `trim()` không rỗng HOẶC có ít nhất 1 tệp hợp lệ được backend hỗ trợ.
 * - Khóa khi đang xử lý (`isSubmitting`) hoặc đang đọc tệp (`isUploading`).
 */
export function canSubmitComposer(
  problemText: string,
  acceptedAttachmentsCount: number,
  isSubmitting: boolean,
  isUploading = false,
): boolean {
  if (isSubmitting || isUploading) return false;
  return problemText.trim().length > 0 || acceptedAttachmentsCount > 0;
}
