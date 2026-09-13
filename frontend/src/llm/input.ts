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
  const kind = kindFromFile(file.name);
  if (!kind) {
    throw new Error(
      "Định dạng file không được hỗ trợ. Chọn .py (mã nguồn), .docx (Word) hoặc ảnh .png/.jpg/.webp.",
    );
  }
  const ext = extOf(file.name);
  const mime = MIME_BY_EXT[ext];
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
