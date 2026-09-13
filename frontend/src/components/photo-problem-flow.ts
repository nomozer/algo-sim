/**
 * Luồng ẢNH ĐỀ BÀI → XEM LẠI → DỰNG — trạng thái THUẦN: không DOM, không fetch.
 *
 * PHOTO_PROBLEM_TO_SCENE_END_TO_END §3/§6. Tách khỏi `ProblemInput.tsx` vì vitest
 * của kho chạy môi trường `node` (không DOM), nên mọi luật tương tác — chống bấm
 * lặp, bỏ phản hồi cũ khi ảnh đã đổi, chỉ cho dựng khi đã xác nhận — phải kiểm
 * được mà không cần dựng component.
 *
 * ─── BA LUẬT MÀ TRẠNG THÁI NÀY GIỮ ────────────────────────────────────────
 *
 * 1. `requestId` tăng mỗi khi ẢNH hoặc GÓC XOAY đổi, và mỗi lần bắt đầu đọc.
 *    Phản hồi mang số cũ bị BỎ — thay ảnh giữa chừng không bao giờ hiện bản
 *    trích xuất của ảnh trước.
 * 2. `read-start` / `build-start` là no-op khi chưa đủ điều kiện ⇒ bấm lặp
 *    không gửi ảnh hay đề lần hai.
 * 3. Bản trích xuất bị TỪ CHỐI hoặc cần XÁC NHẬN thì phải đánh dấu xác nhận
 *    mới dựng được — hệ không bày ra một hình 3D có vẻ chính xác từ dữ liệu
 *    người học chưa đọc lại.
 */
import type { ImageExtractionResponse, PhotoRotation, PhotoUncertainToken } from "../llm/client";

/** Trần phía trình duyệt — chỉ để báo sớm; máy chủ mới là thẩm quyền. */
export const PHOTO_MAX_BYTES = 10 * 1024 * 1024;
export const MIN_PROBLEM_CHARS = 10;

export type PhotoPhase = "empty" | "selected" | "reading" | "review" | "error" | "building";

/** `File` thoả kiểu này; test dùng bản ghi thường thay vì `File`. */
export interface PhotoFileInfo {
  name: string;
  type: string;
  size: number;
}

export interface PhotoState {
  phase: PhotoPhase;
  file: PhotoFileInfo | null;
  rotation: PhotoRotation;
  requestId: number;
  response: ImageExtractionResponse | null;
  /** Văn bản SẼ gửi đi dựng — điền sẵn từ bản trích xuất, người học sửa được. */
  text: string;
  confirmed: boolean;
  error: string | null;
}

export type PhotoAction =
  | { type: "select"; file: PhotoFileInfo }
  | { type: "rotate" }
  | { type: "remove" }
  | { type: "read-start" }
  | { type: "read-success"; requestId: number; response: ImageExtractionResponse }
  | { type: "read-failure"; requestId: number; message: string }
  | { type: "edit"; text: string }
  | { type: "confirm"; value: boolean }
  | { type: "build-start" }
  | { type: "build-failure"; message: string }
  | { type: "build-end" };

export const initialPhotoState: PhotoState = {
  phase: "empty",
  file: null,
  rotation: 0,
  requestId: 0,
  response: null,
  text: "",
  confirmed: false,
  error: null,
};

export function nextRotation(r: PhotoRotation): PhotoRotation {
  return ((r + 90) % 360) as PhotoRotation;
}

export function canRead(s: PhotoState): boolean {
  return s.file !== null && (s.phase === "selected" || s.phase === "error");
}

export function needsConfirmation(s: PhotoState): boolean {
  const a = s.response?.assessment;
  return !!a && (a.status === "rejected" || a.requires_confirmation);
}

/** Lý do CHƯA dựng được, bằng lời cho người học; `null` = dựng được. */
export function buildBlocker(s: PhotoState): string | null {
  if (s.phase !== "review" || !s.response) return "Hãy đọc đề trong ảnh trước.";
  if (s.text.trim().length < MIN_PROBLEM_CHARS) {
    return "Nội dung đề còn quá ngắn — em bổ sung đầy đủ đề bài.";
  }
  if (needsConfirmation(s) && !s.confirmed) {
    return "Em đọc lại, sửa nội dung cho khớp với ảnh rồi đánh dấu xác nhận.";
  }
  return null;
}

export function canBuild(s: PhotoState): boolean {
  return buildBlocker(s) === null;
}

export function photoReducer(s: PhotoState, a: PhotoAction): PhotoState {
  switch (a.type) {
    case "select":
      return { ...initialPhotoState, phase: "selected", file: a.file, requestId: s.requestId + 1 };
    case "rotate":
      if (!s.file || s.phase === "building") return s;
      return {
        ...s,
        phase: "selected",
        rotation: nextRotation(s.rotation),
        requestId: s.requestId + 1,
        response: null,
        text: "",
        confirmed: false,
        error: null,
      };
    case "remove":
      if (s.phase === "building") return s;
      return { ...initialPhotoState, requestId: s.requestId + 1 };
    case "read-start":
      if (!canRead(s)) return s;
      return { ...s, phase: "reading", requestId: s.requestId + 1, error: null };
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
    case "build-start":
      if (!canBuild(s)) return s;
      return { ...s, phase: "building", error: null };
    case "build-failure":
      if (s.phase !== "building") return s;
      return { ...s, phase: "review", error: a.message };
    case "build-end":
      if (s.phase !== "building") return s;
      return { ...s, phase: "review" };
  }
}

/** Trạng thái đọc bằng lời — nội dung vùng `aria-live`. */
export function photoStatusText(s: PhotoState): string {
  switch (s.phase) {
    case "selected":
      return "Kiểm tra ảnh đã đúng chiều, rồi bấm “Đọc đề trong ảnh”.";
    case "reading":
      return "Đang đọc đề trong ảnh…";
    case "review":
      return s.response?.assessment.status === "rejected"
        ? "Chưa dựng được trực tiếp từ ảnh này."
        : "Đã đọc xong. Em đọc lại nội dung bên dưới trước khi dựng.";
    case "building":
      return "Đang dựng mô phỏng…";
    default:
      return "";
  }
}

/** Kết quả dựng từ văn bản đã xác nhận. */
export type PhotoBuildOutcome = "OK" | "INSUFFICIENT_GEOMETRIC_CONSTRAINTS" | "UNSUPPORTED_PROBLEM";

const THIEU_DU_KIEN = new Set(["insufficient_specification", "semantic_incomplete"]);

export function buildOutcome(result: { status: string; failure_category?: string }): PhotoBuildOutcome {
  if (result.status === "ok") return "OK";
  return result.failure_category && THIEU_DU_KIEN.has(result.failure_category)
    ? "INSUFFICIENT_GEOMETRIC_CONSTRAINTS"
    : "UNSUPPORTED_PROBLEM";
}

/** Lời báo khi dựng không thành — ảnh và nội dung đã sửa được GIỮ LẠI để sửa tiếp. */
export function buildFailureMessage(result: {
  status: string;
  failure_category?: string;
  learner_reason?: string;
}): string {
  const dau =
    buildOutcome(result) === "INSUFFICIENT_GEOMETRIC_CONSTRAINTS"
      ? "Đề chưa đủ dữ kiện để dựng hình chính xác."
      : "Hệ thống chưa dựng được đề này.";
  return result.learner_reason ? `${dau} ${result.learner_reason}` : dau;
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
