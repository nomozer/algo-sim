/**
 * Luồng ẢNH ĐỀ BÀI → KHOANH VÙNG → ĐỌC → XEM LẠI → ĐƯA VÀO Ô NHẬP — trạng thái THUẦN: không DOM, không fetch.
 *
 * PHOTO_PROBLEM_TO_SCENE_END_TO_END §3/§6 + run `image-capture-crop-extraction`. Tách khỏi component vì vitest của kho
 * chạy môi trường `node` (không DOM), nên mọi luật tương tác phải kiểm được mà không dựng component.
 *
 * Các pha ↔ màn của hộp thoại: `empty` = CHỌN ẢNH · `selected` = CHỈNH ẢNH (khoanh vùng/xoay) · `prepared` = XEM ẢNH SẼ
 * GỬI · `reading` = ĐANG ĐỌC · `review` = XEM LẠI VĂN BẢN · `error` = LỖI.
 *
 * ─── BỐN LUẬT MÀ TRẠNG THÁI NÀY GIỮ ───────────────────────────────────────
 *
 * 1. `requestId` tăng mỗi khi ẢNH, GÓC XOAY hay ẢNH SẼ GỬI đổi, và mỗi lần bắt đầu đọc. Phản hồi mang số cũ bị BỎ —
 *    thay/khoanh lại ảnh giữa chừng không bao giờ hiện bản trích xuất của ảnh trước.
 * 2. `read-start` là no-op khi chưa đủ điều kiện ⇒ bấm lặp không gửi ảnh lần hai. Chọn ảnh KHÔNG tự đọc.
 * 3. Bản trích xuất bị TỪ CHỐI hoặc cần XÁC NHẬN thì phải đánh dấu xác nhận mới dùng được văn bản.
 * 4. Văn bản chỉ RỜI hộp thoại khi người học bấm dùng nó; nó vào Ô NHẬP ĐỀ — không tự gửi `/api/analyze`.
 */
import type { ImageExtractionResponse, PhotoRotation, PhotoUncertainToken } from "../llm/client";
import { AxoClientError } from "../llm/client";
import { rotateLeft, rotateRight } from "./photo-image-tools";

/** Trần phía trình duyệt — chỉ để báo sớm; máy chủ mới là thẩm quyền (`MAX_IMAGE_BYTES`). */
export const PHOTO_MAX_BYTES = 10 * 1024 * 1024;
export const MIN_PROBLEM_CHARS = 10;

export type PhotoPhase = "empty" | "selected" | "prepared" | "reading" | "review" | "error";

/** `File` thoả kiểu này; test dùng bản ghi thường thay vì `File`. */
export interface PhotoFileInfo {
  name: string;
  type: string;
  size: number;
}

/** Ảnh SẼ GỬI: tệp gốc + góc xoay để máy chủ xoay, hoặc tệp đã cắt/xoay ở trình duyệt (`rotation = 0`). */
export interface PhotoUpload {
  file: PhotoFileInfo;
  rotation: PhotoRotation;
  cropped: boolean;
}

export interface PhotoState {
  phase: PhotoPhase;
  /** Ảnh người học chọn/chụp — nguồn của mọi lần khoanh vùng. */
  file: PhotoFileInfo | null;
  rotation: PhotoRotation;
  upload: PhotoUpload | null;
  requestId: number;
  response: ImageExtractionResponse | null;
  /** Văn bản SẼ đưa vào ô nhập — điền sẵn từ bản trích xuất, người học sửa được. */
  text: string;
  confirmed: boolean;
  error: string | null;
}

export type PhotoAction =
  | { type: "select"; file: PhotoFileInfo }
  | { type: "rotate"; direction?: "left" | "right" }
  | { type: "prepare"; upload: PhotoUpload }
  | { type: "edit-image" }
  | { type: "image-invalid"; message: string }
  | { type: "remove" }
  | { type: "read-start" }
  | { type: "read-cancel" }
  | { type: "read-success"; requestId: number; response: ImageExtractionResponse }
  | { type: "read-failure"; requestId: number; message: string }
  | { type: "edit"; text: string }
  | { type: "confirm"; value: boolean };

export const initialPhotoState: PhotoState = {
  phase: "empty",
  file: null,
  rotation: 0,
  upload: null,
  requestId: 0,
  response: null,
  text: "",
  confirmed: false,
  error: null,
};

export function nextRotation(r: PhotoRotation): PhotoRotation {
  return rotateRight(r);
}

export function canRead(s: PhotoState): boolean {
  return s.upload !== null && (s.phase === "prepared" || s.phase === "error");
}

export function needsConfirmation(s: PhotoState): boolean {
  const a = s.response?.assessment;
  return !!a && (a.status === "rejected" || a.requires_confirmation);
}

/** Lý do CHƯA dùng được văn bản, bằng lời cho người học; `null` = dùng được. */
export function acceptBlocker(s: PhotoState): string | null {
  if (s.phase !== "review" || !s.response) return "Hãy đọc đề trong ảnh trước.";
  if (s.text.trim().length < MIN_PROBLEM_CHARS) {
    return "Nội dung đề còn quá ngắn — em bổ sung đầy đủ đề bài.";
  }
  if (needsConfirmation(s) && !s.confirmed) {
    return "Em đọc lại, sửa nội dung cho khớp với ảnh rồi đánh dấu xác nhận.";
  }
  return null;
}

export function canAccept(s: PhotoState): boolean {
  return acceptBlocker(s) === null;
}

/** Ô nhập đã có nội dung KHÁC ⇒ hỏi trước khi thay (không mất chữ người học đang gõ). */
export function needsReplaceConfirmation(composerText: string, photoText: string): boolean {
  const cu = composerText.trim();
  return cu.length > 0 && cu !== photoText.trim();
}

const editableAgain = (s: PhotoState) => s.file !== null && s.phase !== "reading";

export function photoReducer(s: PhotoState, a: PhotoAction): PhotoState {
  switch (a.type) {
    case "select":
      return { ...initialPhotoState, phase: "selected", file: a.file, requestId: s.requestId + 1 };
    case "rotate":
      if (!s.file || s.phase !== "selected") return s;
      return {
        ...s,
        rotation: a.direction === "left" ? rotateLeft(s.rotation) : rotateRight(s.rotation),
        requestId: s.requestId + 1,
      };
    case "prepare":
      if (!s.file || s.phase !== "selected") return s;
      return { ...s, phase: "prepared", upload: a.upload, requestId: s.requestId + 1, error: null };
    case "edit-image":
      if (!editableAgain(s)) return s;
      return {
        ...s,
        phase: "selected",
        upload: null,
        response: null,
        text: "",
        confirmed: false,
        error: null,
        requestId: s.requestId + 1,
      };
    case "image-invalid":
      return { ...initialPhotoState, phase: "error", error: a.message, requestId: s.requestId + 1 };
    case "remove":
      return { ...initialPhotoState, requestId: s.requestId + 1 };
    case "read-start":
      if (!canRead(s)) return s;
      return { ...s, phase: "reading", requestId: s.requestId + 1, error: null };
    case "read-cancel":
      // Huỷ chủ động: về ảnh sẽ gửi, và phản hồi về muộn của lượt đã huỷ bị bỏ (requestId đổi).
      if (s.phase !== "reading") return s;
      return { ...s, phase: "prepared", requestId: s.requestId + 1 };
    case "read-success":
      if (a.requestId !== s.requestId || s.phase !== "reading") return s;
      return {
        ...s,
        phase: "review",
        response: a.response,
        text: a.response.assessment.problem_text,
        confirmed: false,
        error: null,
      };
    case "read-failure":
      if (a.requestId !== s.requestId || s.phase !== "reading") return s;
      return { ...s, phase: "error", error: a.message || null };
    case "edit":
      if (s.phase !== "review") return s;
      return { ...s, text: a.text, error: null };
    case "confirm":
      if (s.phase !== "review") return s;
      return { ...s, confirmed: a.value };
  }
}

/** Trạng thái đọc bằng lời — nội dung vùng `aria-live`. */
export function photoStatusText(s: PhotoState): string {
  switch (s.phase) {
    case "selected":
      return "Kéo trên ảnh để khoanh vùng đề bài (gồm cả hình vẽ nếu có), hoặc dùng cả ảnh.";
    case "prepared":
      return s.upload?.cropped
        ? "Đây là vùng sẽ gửi đi đọc. Kiểm tra đủ đề và hình rồi bấm “Đọc đề trong ảnh”."
        : "Ảnh sẽ được gửi nguyên vẹn. Bấm “Đọc đề trong ảnh”.";
    case "reading":
      return "Đang đọc nội dung đề bài…";
    case "review":
      return s.response?.assessment.status === "rejected"
        ? "Chưa dùng được trực tiếp nội dung đọc từ ảnh này."
        : "Đã đọc xong. Em đọc lại, sửa nếu cần, rồi bấm “Dùng đề này”.";
    default:
      return "";
  }
}

/**
 * Lỗi của `/api/image/extract` → lời cho người học. `null` = huỷ chủ động (im lặng).
 * Máy chủ trả thông điệp tiếng Việt cho lỗi ảnh/provider; nhưng hai câu trả lời của nó nhắc tên cấu hình kĩ thuật
 * (`ALLOW_LIVE_AI=0`, `GEMINI_API_KEY`) — chúng được nói lại bằng lời của người học, không bao giờ hiện nguyên văn.
 */
export function photoReadErrorMessage(err: unknown): string | null {
  if ((err as { name?: string } | null)?.name === "AbortError") return null;
  if (err instanceof AxoClientError) {
    if (err.reasonCode === "LIVE_AI_DISABLED") {
      return "Chức năng đọc ảnh đang tạm tắt trên máy chủ. Em gõ đề vào ô nhập, hoặc thử lại sau.";
    }
    if (err.status === 503 && !err.reasonCode) {
      return "Máy chủ chưa sẵn sàng đọc ảnh. Em gõ đề vào ô nhập, hoặc thử lại sau.";
    }
    return err.message;
  }
  return err instanceof Error && err.message ? err.message : "Chưa đọc được ảnh. Em thử lại nhé.";
}

export function clientFileProblem(file: PhotoFileInfo): string | null {
  if (file.size === 0) return "Tệp ảnh rỗng.";
  if (file.size > PHOTO_MAX_BYTES) {
    return "Ảnh quá lớn (tối đa 10MB). Em chụp lại hoặc giảm độ phân giải.";
  }
  return null;
}

export function describeUncertainToken(t: PhotoUncertainToken): string {
  const thay = t.alternatives.length
    ? ` có thể là ${t.alternatives.map((x) => `“${x}”`).join(" hoặc ")}`
    : " đọc chưa chắc";
  const o = t.location ? ` — ở “${t.location}”` : "";
  return `“${t.token}”${thay}${o}`;
}
