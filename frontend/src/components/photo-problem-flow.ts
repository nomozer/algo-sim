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
  /** OCR local: văn bản máy đọc gốc; các chỗ chưa chắc được sửa TẠI CHỖ qua spanValues. */
  baseText: string;
  spanValues: Record<string, string>;
  spanReviewed: Record<string, boolean>;
  /** Học sinh đã sửa thẳng cả ô văn bản ⇒ vị trí các chỗ đánh dấu không còn đúng, dùng văn bản tự do. */
  freeEdit: boolean;
  /** Chỗ sửa đã được nối với chữ kế tiếp: bản gốc của chỗ ấy, các chỗ bị gộp vào và giá trị trước khi nối (để tách lại). */
  spanExtensions?: Record<string, { token: PhotoUncertainToken; value: string; absorbed: PhotoUncertainToken[]; absorbedValues: Record<string, string> }>;
  /** Thứ tự ban đầu của các chỗ đánh dấu (tách lại trả chúng về đúng vị trí trong danh sách). */
  tokenOrder?: Record<string, number>;
}

/** Từ kế tiếp có thể nối vào chỗ `spanId`: khoảng cách 1–3 dấu cách, từ ấy không phải chữ văn xuôi, không sang câu mới,
 *  và mọi chỗ đánh dấu nằm trong nó đều nằm TRỌN trong nó. Vị trí tính theo code point (khớp vị trí của backend). */
export function extendSpanTarget(
  state: UnifiedAssistState,
  spanId: string,
): { end: number; gapStart: number; wordStart: number; absorbed: PhotoUncertainToken[] } | null {
  if (state.phase !== "needs_confirmation" || state.freeEdit) return null;
  const tokens = spanTokens(state.uncertainTokens);
  const t = tokens.find((x) => x.span_id === spanId);
  if (!t) return null;
  const chars = Array.from(state.baseText);
  const gapStart = t.span_end as number;
  let wordStart = gapStart;
  while (wordStart < chars.length && (chars[wordStart] === " " || chars[wordStart] === "\t")) wordStart += 1;
  let end = wordStart;
  while (end < chars.length && !/\s/u.test(chars[end])) end += 1;
  const gap = wordStart - gapStart;
  const word = chars.slice(wordStart, end).join("");
  if (gap < 1 || gap > 3 || end === wordStart || end - wordStart > 24) return null;
  if (/\p{Ll}{2}/u.test(word)) return null;                                      // a prose word, not part of an expression
  const own = chars.slice(t.span_start as number, gapStart).join("");
  if (/[.?!]$/u.test(own) && /^\p{Lu}\p{Ll}/u.test(word)) return null;            // a new sentence starts there
  const absorbed = tokens.filter((x) => x.span_id !== spanId && (x.span_start as number) < end && (x.span_end as number) > gapStart);
  if (absorbed.some((x) => (x.span_start as number) < wordStart || (x.span_end as number) > end)) return null;
  return { end, gapStart, wordStart, absorbed };
}

export type UnifiedAssistAction =
  | { type: "reset" }
  | { type: "from-prepare"; response: UnifiedInputPrepareResponse }
  | { type: "edit-draft"; text: string }
  | { type: "toggle-confirm"; value: boolean }
  | { type: "edit-span"; spanId: string; value: string }
  | { type: "confirm-span"; spanId: string }
  | { type: "extend-span"; spanId: string }
  | { type: "restore-span"; spanId: string };

/** Chỗ cần kiểm tra có vị trí trong văn bản (sửa tại chỗ được). */
export function spanTokens(tokens: PhotoUncertainToken[]): PhotoUncertainToken[] {
  return tokens.filter(
    (t) => Boolean(t.span_id) && typeof t.span_start === "number" && typeof t.span_end === "number" && t.span_start >= 0,
  );
}

/** Mục cần học sinh tự xác nhận (gồm cả "hình vẽ không có thêm dữ kiện"). */
export function reviewTokens(tokens: PhotoUncertainToken[]): PhotoUncertainToken[] {
  return tokens.filter((t) => Boolean(t.span_id) && (t.kind === "diagram" || (t.span_start ?? -1) >= 0));
}

/** Ghép văn bản: thay từng khoảng [span_start, span_end) bằng giá trị học sinh xác nhận (từ cuối về đầu). */
export function applySpanValues(base: string, tokens: PhotoUncertainToken[], values: Record<string, string>): string {
  // Backend offsets count Unicode code points; JS string slices count UTF-16 units.
  const out = Array.from(base);
  const sorted = [...spanTokens(tokens)].sort((a, b) => (b.span_start ?? 0) - (a.span_start ?? 0));
  for (const t of sorted) {
    const v = values[t.span_id as string];
    if (typeof v !== "string") continue;
    out.splice(t.span_start as number, (t.span_end as number) - (t.span_start as number), ...Array.from(v));
  }
  return out.join("");
}

/** Số chỗ học sinh thực sự đổi so với bản máy đọc (đo "số thao tác sửa"). */
export function assistCorrectionCount(state: UnifiedAssistState): number {
  return spanTokens(state.uncertainTokens).filter((t) => (state.spanValues[t.span_id as string] ?? t.token) !== t.token)
    .length;
}

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
  baseText: "",
  spanValues: {},
  spanReviewed: {},
  freeEdit: false,
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
          baseText: "",
          spanValues: {},
          spanReviewed: {},
          freeEdit: false,
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
          baseText: r.problem_text,
          spanValues: Object.fromEntries(spanTokens(r.uncertain_tokens).map((t) => [t.span_id as string, t.token])),
          spanReviewed: {},
          freeEdit: false,
          spanExtensions: {},
          tokenOrder: Object.fromEntries(r.uncertain_tokens.map((t, i) => [t.span_id ?? `#${i}`, i])),
        };
      }
      return initialUnifiedAssistState;
    }
    case "edit-draft":
      if (state.phase !== "needs_confirmation") return state;
      return { ...state, draftText: action.text, freeEdit: true, confirmed: false };
    case "edit-span": {
      if (state.phase !== "needs_confirmation" || state.freeEdit) return state;
      const spanValues = { ...state.spanValues, [action.spanId]: action.value };
      return {
        ...state,
        confirmed: false,
        spanValues,
        spanReviewed: { ...state.spanReviewed, [action.spanId]: true },
        draftText: applySpanValues(state.baseText, state.uncertainTokens, spanValues),
      };
    }
    case "confirm-span":
      if (state.phase !== "needs_confirmation") return state;
      return { ...state, spanReviewed: { ...state.spanReviewed, [action.spanId]: true } };
    case "extend-span": {
      const target = extendSpanTarget(state, action.spanId);
      if (!target) return state;
      const t = spanTokens(state.uncertainTokens).find((x) => x.span_id === action.spanId) as PhotoUncertainToken;
      const chars = Array.from(state.baseText);
      // The appended word keeps whatever the student already typed into chỗ it absorbs.
      const word = applySpanValues(
        chars.slice(target.wordStart, target.end).join(""),
        target.absorbed.map((x) => ({ ...x, span_start: (x.span_start as number) - target.wordStart, span_end: (x.span_end as number) - target.wordStart })),
        state.spanValues,
      );
      const value = `${state.spanValues[action.spanId] ?? t.token}${chars.slice(target.gapStart, target.wordStart).join("")}${word}`;
      const extended: PhotoUncertainToken = { ...t, span_end: target.end, token: chars.slice(t.span_start as number, target.end).join("") };
      const gone = new Set(target.absorbed.map((x) => x.span_id as string));
      const prev = state.spanExtensions?.[action.spanId];
      const spanValues = Object.fromEntries(Object.entries(state.spanValues).filter(([k]) => !gone.has(k)));
      spanValues[action.spanId] = value;
      const spanReviewed = Object.fromEntries(Object.entries(state.spanReviewed).filter(([k]) => !gone.has(k)));
      spanReviewed[action.spanId] = false;
      const uncertainTokens = state.uncertainTokens.filter((x) => !gone.has(x.span_id as string)).map((x) => (x.span_id === action.spanId ? extended : x));
      return {
        ...state,
        confirmed: false,
        uncertainTokens,
        spanValues,
        spanReviewed,
        spanExtensions: {
          ...state.spanExtensions,
          [action.spanId]: prev
            ? { ...prev, absorbed: [...prev.absorbed, ...target.absorbed],
                absorbedValues: { ...prev.absorbedValues, ...Object.fromEntries(target.absorbed.map((x) => [x.span_id as string, state.spanValues[x.span_id as string] ?? x.token])) } }
            : { token: t, value: state.spanValues[action.spanId] ?? t.token, absorbed: target.absorbed,
                absorbedValues: Object.fromEntries(target.absorbed.map((x) => [x.span_id as string, state.spanValues[x.span_id as string] ?? x.token])) },
        },
        draftText: applySpanValues(state.baseText, uncertainTokens, spanValues),
      };
    }
    case "restore-span": {
      const ext = state.spanExtensions?.[action.spanId];
      if (state.phase !== "needs_confirmation" || state.freeEdit || !ext) return state;
      const order = state.tokenOrder ?? {};
      const uncertainTokens = [...state.uncertainTokens.map((x) => (x.span_id === action.spanId ? ext.token : x)), ...ext.absorbed]
        .sort((a, b) => (order[a.span_id as string] ?? 0) - (order[b.span_id as string] ?? 0));
      const spanValues = { ...state.spanValues, [action.spanId]: ext.value, ...ext.absorbedValues };
      const spanReviewed = { ...state.spanReviewed, [action.spanId]: false };
      for (const x of ext.absorbed) spanReviewed[x.span_id as string] = false;
      const spanExtensions = { ...state.spanExtensions };
      delete spanExtensions[action.spanId];
      return { ...state, confirmed: false, uncertainTokens, spanValues, spanReviewed, spanExtensions,
               draftText: applySpanValues(state.baseText, uncertainTokens, spanValues) };
    }
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
  if (!state.freeEdit) {
    const left = reviewTokens(state.uncertainTokens).filter((t) => !state.spanReviewed[t.span_id as string]).length;
    if (left > 0) {
      return `Còn ${left} chỗ được đánh dấu — em bấm “Đúng rồi” hoặc sửa từng chỗ.`;
    }
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

/**
 * Lời báo khi `/api/analyze` (đề ĐÃ là văn bản) lỗi hạ tầng. Run `real-world-end-to-end-reliability`: lỗi này từng
 * dùng chung lời của luồng ảnh ("trích xuất ảnh … Em gõ đề vào ô nhập") dù người học vừa gõ đề — sai ngữ cảnh.
 * `null` = huỷ chủ động. Không lộ mã/biến kỹ thuật.
 */
export function analyzeErrorMessage(err: unknown): string | null {
  if ((err as { name?: string } | null)?.name === "AbortError") return null;
  if (err instanceof AxoClientError) {
    if (err.reasonCode === "LIVE_AI_DISABLED") {
      return "Đề này cần bước phân tích bằng AI, nhưng bước đó đang tạm tắt trên máy chủ. Hệ chỉ tự giải được các dạng "
        + "đề quen thuộc khi không có AI — em thử diễn đạt lại theo cách trong sách giáo khoa, hoặc quay lại sau.";
    }
    if (err.reasonCode === "MISSING_API_KEY" || (err.status === 503 && !err.reasonCode)) {
      return "Máy chủ chưa sẵn sàng phân tích đề này lúc này. Em thử lại sau ít phút nhé.";
    }
    return err.message;
  }
  return err instanceof Error && err.message ? err.message : "Chưa phân tích được đề. Em thử lại nhé.";
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
