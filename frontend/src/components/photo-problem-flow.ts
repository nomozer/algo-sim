/**
 * Trạng thái thuần cho luồng hỗ trợ đầu vào thống nhất sau khi bấm "Dựng hình" (§14, §16, §17):
 * - Mặc định (`idle`): không hiện bất kỳ bảng xác nhận hay khoanh vùng trung gian nào.
 * - Khi tài liệu/ảnh có nhiều bài toán độc lập mà chưa rõ bài cần dựng (`needs_selection`):
 *   hiển thị danh sách bài ứng viên để học sinh chạm chọn 1 bước (không kéo khung crop).
 * - Khi trích xuất có ký hiệu chưa chắc chắn hoặc vùng nghi thiếu (`needs_confirmation`):
 *   hiển thị đúng phần văn bản cần chỉnh/xác nhận ngay dưới ô nhập đề trước khi gửi dựng 3D.
 */
import type {
  PhotoUncertainToken,
  UnifiedCandidateProblem,
  UnifiedInputPrepareResponse,
} from "../llm/client";
import { AxoClientError } from "../llm/client";

export const PHOTO_MAX_BYTES = 10 * 1024 * 1024;
export const MIN_PROBLEM_CHARS = 10;

export interface PhotoFileInfo {
  name: string;
  type: string;
  size: number;
}

export type UnifiedAssistPhase = "idle" | "needs_selection" | "needs_confirmation";

export interface UnifiedAssistState {
  phase: UnifiedAssistPhase;
  sourceKind: "image" | "pdf" | "docx" | null;
  learnerMessage: string | null;
  candidates: UnifiedCandidateProblem[];
  draftText: string;
  flagMessages: string[];
  uncertainTokens: PhotoUncertainToken[];
  missingRegions: string[];
  confirmed: boolean;
}

export type UnifiedAssistAction =
  | { type: "reset" }
  | { type: "from-prepare"; response: UnifiedInputPrepareResponse }
  | { type: "edit-draft"; text: string }
  | { type: "toggle-confirm"; value: boolean };

export const initialUnifiedAssistState: UnifiedAssistState = {
  phase: "idle",
  sourceKind: null,
  learnerMessage: null,
  candidates: [],
  draftText: "",
  flagMessages: [],
  uncertainTokens: [],
  missingRegions: [],
  confirmed: false,
};

export function unifiedAssistReducer(
  state: UnifiedAssistState,
  action: UnifiedAssistAction,
): UnifiedAssistState {
  switch (action.type) {
    case "reset":
      return initialUnifiedAssistState;
    case "from-prepare": {
      const r = action.response;
      if (r.status === "needs_selection") {
        return {
          phase: "needs_selection",
          sourceKind: r.source_kind,
          learnerMessage:
            r.learner_message ??
            "Có nhiều bài toán độc lập trong tệp đính kèm. Em chạm chọn bài muốn dựng nhé.",
          candidates: r.candidates,
          draftText: "",
          flagMessages: [],
          uncertainTokens: [],
          missingRegions: [],
          confirmed: false,
        };
      }
      if (r.status === "needs_confirmation") {
        return {
          phase: "needs_confirmation",
          sourceKind: r.source_kind,
          learnerMessage:
            r.learner_message ??
            "Có ký hiệu đọc chưa chắc chắn — em kiểm tra nhanh nội dung trước khi dựng hình.",
          candidates: [],
          draftText: r.problem_text,
          flagMessages: r.flag_messages,
          uncertainTokens: r.uncertain_tokens,
          missingRegions: r.missing_regions,
          confirmed: false,
        };
      }
      return initialUnifiedAssistState;
    }
    case "edit-draft":
      if (state.phase !== "needs_confirmation") return state;
      return { ...state, draftText: action.text };
    case "toggle-confirm":
      if (state.phase !== "needs_confirmation") return state;
      return { ...state, confirmed: action.value };
  }
}

export function assistBlocker(state: UnifiedAssistState): string | null {
  if (state.phase !== "needs_confirmation") {
    return "Chưa có nội dung cần xác nhận.";
  }
  if (state.draftText.trim().length < MIN_PROBLEM_CHARS) {
    return "Nội dung đề còn quá ngắn — em bổ sung đầy đủ giả thiết và câu hỏi.";
  }
  if (!state.confirmed) {
    return "Em kiểm tra lại ký hiệu rồi đánh dấu xác nhận để dựng hình.";
  }
  return null;
}

export function canConfirmAssistText(state: UnifiedAssistState): boolean {
  return assistBlocker(state) === null;
}

/**
 * Chuẩn hóa thông báo lỗi từ `/api/input/prepare` hoặc `/api/image/extract` sang lời dành cho người học.
 * `null` = huỷ chủ động (AbortError). Không lộ tên biến môi trường kỹ thuật (`ALLOW_LIVE_AI`, `GEMINI_API_KEY`).
 */
export function photoReadErrorMessage(err: unknown): string | null {
  if ((err as { name?: string } | null)?.name === "AbortError") return null;
  if (err instanceof AxoClientError) {
    if (err.reasonCode === "LIVE_AI_DISABLED") {
      return "Chức năng trích xuất ảnh trực tiếp đang tạm tắt trên máy chủ. Em gõ đề vào ô nhập, hoặc đính kèm tệp PDF/DOCX có sẵn văn bản.";
    }
    if (err.reasonCode === "MISSING_API_KEY" || (err.status === 503 && !err.reasonCode)) {
      return "Máy chủ chưa sẵn sàng đọc ảnh chụp lúc này. Em gõ đề vào ô nhập, hoặc đính kèm tệp PDF/DOCX có văn bản.";
    }
    return err.message;
  }
  return err instanceof Error && err.message ? err.message : "Chưa xử lý được tệp đính kèm. Em thử lại nhé.";
}

export function clientFileProblem(file: PhotoFileInfo): string | null {
  if (file.size === 0) return "Tệp đính kèm đang rỗng (0 B).";
  if (file.size > PHOTO_MAX_BYTES) {
    return "Tệp quá lớn (tối đa 10 MB). Em chọn tệp gọn hơn hoặc chụp lại phần đề bài.";
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
