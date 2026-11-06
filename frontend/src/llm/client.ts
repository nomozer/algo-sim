import type { AnalysisUnsupported } from "../core/types";
import { HYBRID_SIMULATION_SCHEMA, docPhanHoiHybrid } from "../simulations/domains/geometry/hybrid-preview-adapter";
import type { SimulationEnvelope } from "../simulations/types";
import type { InputPayload } from "./input";

/**
 * Client gọi backend — trình duyệt không bao giờ giữ API key.
 * Đường dẫn /api/* được vite dev server chuyển tiếp sang backend (cổng 8000).
 * /api/analyze trả ValidatedSimulationEnvelope (đã qua server-side validation).
 */

export interface ServerHealth {
  ok: boolean;
  hasKey: boolean;
  cachedProblems: number;
}

const CONNECT_HELP =
  "Không kết nối được máy chủ phân tích. Mở cửa sổ lệnh trong thư mục algo-sim và chạy: docker compose up -d --build";

export type ClientFailureCode =
  | "NETWORK_UNREACHABLE"
  | "SERVICE_UNAVAILABLE"
  | "QUOTA_EXCEEDED"
  | "MAINTENANCE_MODE"
  | "ACCOUNT_LOCKED"
  | "INVALID_INPUT"
  | "NOT_FOUND"
  | "HTTP_ERROR";

export interface ClientFailureContract {
  readonly kind: "network" | "http";
  readonly code: ClientFailureCode;
  readonly status?: number;
  readonly message: string;
}

export class AxoClientError extends Error implements ClientFailureContract {
  readonly kind: "network" | "http";
  readonly code: ClientFailureCode;
  readonly status?: number;
  readonly transient?: boolean;

  constructor(opts: {
    kind: "network" | "http";
    code: ClientFailureCode;
    message: string;
    status?: number;
    transient?: boolean;
  }) {
    super(opts.message);
    this.name = "AxoClientError";
    this.kind = opts.kind;
    this.code = opts.code;
    this.status = opts.status;
    this.transient = opts.transient;
  }

  toContract(): ClientFailureContract {
    return {
      kind: this.kind,
      code: this.code,
      status: this.status,
      message: this.message,
    };
  }
}

export interface AnalyzeRetryPolicy {
  maxRetries?: number;
  baseDelayMs?: number;
  isDocumentHidden?: () => boolean;
}

function classifyHttpFailureCode(
  status: number,
  rec: Record<string, unknown> | null,
): ClientFailureCode {
  const rawCode = String(rec?.code ?? rec?.error_code ?? "").toUpperCase();
  if (status === 404 || rawCode === "NOT_FOUND") return "NOT_FOUND";
  if (rawCode === "MAINTENANCE_MODE") return "MAINTENANCE_MODE";
  if (status === 429 || rawCode === "QUOTA_EXCEEDED" || rawCode === "RATE_LIMITED") {
    return "QUOTA_EXCEEDED";
  }
  if (status === 423 || rawCode === "ACCOUNT_LOCKED") return "ACCOUNT_LOCKED";
  if (status === 503 || rawCode === "SERVICE_UNAVAILABLE" || rawCode === "MISSING_API_KEY") {
    return "SERVICE_UNAVAILABLE";
  }
  if (status === 400 || status === 422 || rawCode === "INVALID_INPUT") {
    return "INVALID_INPUT";
  }
  return "HTTP_ERROR";
}

async function postJson<T>(
  url: string,
  payload: unknown,
  signal?: AbortSignal,
  extraHeaders?: Record<string, string>,
  sessionRetried = false,
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json", ...extraHeaders },
      body: JSON.stringify(payload),
      signal,
    });
  } catch (err) {
    // Huỷ CHỦ ĐỘNG (người học thay/xoá ảnh) không phải lỗi kết nối — ném nguyên
    // để nơi gọi nhận ra và im lặng, thay vì hiện lời nhắc bật máy chủ.
    if ((err as { name?: string } | null)?.name === "AbortError") throw err;
    throw new AxoClientError({
      kind: "network",
      code: "NETWORK_UNREACHABLE",
      message: CONNECT_HELP,
      transient: err instanceof TypeError,
    });
  }

  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    /* rơi xuống nhánh lỗi bên dưới */
  }

  if (!res.ok) {
    const rec = body && typeof body === "object" ? (body as Record<string, unknown>) : null;
    // No valid session: the server ran nothing and set a fresh guest session cookie on this refusal. Send the same
    // request (same attempt ID) exactly once more; a second refusal is the answer.
    if (res.status === 401 && rec?.reason_code === "session_required" && !sessionRetried && !signal?.aborted) {
      return postJson<T>(url, payload, signal, extraHeaders, true);
    }
    const rawMsg = rec?.error ?? rec?.detail;
    const msg =
      typeof rawMsg === "string" && rawMsg.trim().length > 0
        ? rawMsg
        : `Máy chủ trả lỗi HTTP ${res.status}.`;
    throw new AxoClientError({
      kind: "http",
      code: classifyHttpFailureCode(res.status, rec),
      status: res.status,
      message: msg,
      transient: res.status === 502 || res.status === 504,
    });
  }
  return body as T;
}

function defaultDocumentHidden(): boolean {
  return typeof document !== "undefined" && document.visibilityState === "hidden";
}

function waitBackoff(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(Object.assign(new Error("Aborted"), { name: "AbortError" }));
      return;
    }
    const timer = setTimeout(() => {
      signal?.removeEventListener("abort", onAbort);
      resolve();
    }, ms);
    const onAbort = () => {
      clearTimeout(timer);
      reject(Object.assign(new Error("Aborted"), { name: "AbortError" }));
    };
    signal?.addEventListener("abort", onAbort, { once: true });
  });
}

async function postJsonWithBoundedRetry<T>(
  url: string,
  payload: unknown,
  signal?: AbortSignal,
  policy?: AnalyzeRetryPolicy,
  extraHeaders?: Record<string, string>,
): Promise<T> {
  const rawMaxRetries = policy?.maxRetries ?? 2;
  const maxRetries = Number.isFinite(rawMaxRetries)
    ? Math.max(0, Math.min(3, Math.trunc(rawMaxRetries)))
    : 2;
  const rawBaseDelayMs = policy?.baseDelayMs ?? 180;
  const baseDelayMs = Number.isFinite(rawBaseDelayMs)
    ? Math.max(1, Math.min(2000, Math.trunc(rawBaseDelayMs)))
    : 180;
  const isHidden = policy?.isDocumentHidden ?? defaultDocumentHidden;

  let attempt = 0;
  for (;;) {
    try {
      return await postJson<T>(url, payload, signal, extraHeaders);
    } catch (err) {
      if (
        !(err instanceof AxoClientError)
        || !err.transient
        || attempt >= maxRetries
        || signal?.aborted
        || isHidden()
      ) {
        throw err;
      }
      const delayMs = baseDelayMs * 2 ** attempt;
      attempt += 1;
      await waitBackoff(delayMs, signal);
      if (signal?.aborted || isHidden()) {
        throw err;
      }
    }
  }
}

export async function fetchHealth(): Promise<ServerHealth | null> {
  try {
    const res = await fetch("/api/health", { credentials: "include" });
    if (!res.ok) return null;
    return (await res.json()) as ServerHealth;
  } catch {
    return null;
  }
}

/** Pipeline phân tích: đầu vào chuẩn hóa text/document/code/image (M4), có retry giới hạn cho lỗi mạng/gateway tạm thời.
 *  `attemptId` (một lần bấm gửi) đi thành `Idempotency-Key`; mọi lần thử lại trong lời gọi này dùng CHUNG nó, nên máy chủ
 *  chạy tuyến tối đa một lần cho lượt gửi ấy (`backend/app/idempotency.py`). */
export async function analyzeViaServer(
  input: InputPayload,
  signal?: AbortSignal,
  retryPolicy?: AnalyzeRetryPolicy,
  attemptId?: string,
): Promise<SimulationEnvelope | AnalysisUnsupported> {
  return docPhanHoiPhanTich(
    await postJsonWithBoundedRetry<unknown>(
      "/api/analyze",
      { input },
      signal,
      retryPolicy,
      attemptId ? { "Idempotency-Key": attemptId } : undefined,
    ),
  );
}

/**
 * Migration Stage 2 (run `scene3d-to-hybrid-v2-replacement`): khi máy chủ bật tay tuyến Hybrid V2 cục bộ, `/api/analyze`
 * trả phản hồi Adapter /4 (`hybrid-route-d-simulation/4`). Nó đi qua ĐÚNG bộ đọc đã kiểm của tuyến ấy
 * (`docPhanHoiHybrid`): phục vụ ⇒ envelope mang view đã kiểm; từ chối ⇒ envelope từ chối nguyên vẹn. Phản hồi /4 không
 * qua được bộ đọc ⇒ một lời từ chối của HỆ (không phải lỗi đề), không bao giờ là cảnh. Phản hồi tuyến mặc định đi nguyên.
 */
export function docPhanHoiPhanTich(raw: unknown): SimulationEnvelope | AnalysisUnsupported {
  if (typeof raw !== "object" || raw === null || (raw as { schema_version?: unknown }).schema_version !== HYBRID_SIMULATION_SCHEMA) {
    return raw as SimulationEnvelope | AnalysisUnsupported;
  }
  const r = docPhanHoiHybrid(raw);
  if (!r.ok) {
    return {
      status: "unsupported",
      reason: "Kết quả của tuyến Hybrid không qua được bước kiểm tra nên không được hiển thị.",
      failure_category: "verification_gap",
      error_code: "HYBRID_RESPONSE_INVALID",
    };
  }
  return r.envelope as unknown as SimulationEnvelope | AnalysisUnsupported;
}

/* ── Đọc ảnh đề bài — TẦNG A (PHOTO_PROBLEM_TO_SCENE_END_TO_END) ─────────────
 *
 * `/api/image/extract` KHÔNG dựng mô phỏng. Nó trả bản chép + chỗ đọc không
 * chắc + phán quyết tất định của máy chủ; người học sửa rồi mới gửi VĂN BẢN qua
 * `analyzeViaServer` — đúng đường gõ tay. Hình dạng dưới đây khớp
 * `ImageProblemExtraction` / `ExtractionResult.to_response` phía backend. */

export type PhotoRotation = 0 | 90 | 180 | 270;

export interface PhotoMathExpression {
  verbatim: string;
  normalized: string;
}

export interface PhotoUncertainToken {
  token: string;
  alternatives: string[];
  location: string;
  reason: string;
}

export interface PhotoExtraction {
  problem_text_verbatim: string;
  problem_text_normalized: string;
  math_expressions: PhotoMathExpression[];
  named_points: string[];
  named_lines: string[];
  named_planes: string[];
  named_solids: string[];
  given_relations: string[];
  has_diagram: boolean;
  diagram_observations: string[];
  text_diagram_conflicts: string[];
  uncertain_tokens: PhotoUncertainToken[];
  missing_regions: string[];
  confidence: number;
}

export interface PhotoAssessment {
  status: "ready_for_review" | "rejected";
  /** Mã máy đọc — CHỈ để chọn hành vi, KHÔNG BAO GIỜ hiển thị. */
  rejection_code: string | null;
  review_flags: string[];
  requires_confirmation: boolean;
  problem_text: string;
  learner_message: string | null;
  flag_messages: string[];
}

export interface ImageExtractionResponse {
  status: "ok";
  extraction: PhotoExtraction;
  assessment: PhotoAssessment;
  image: {
    sha256: string;
    width: number;
    height: number;
    source_mime: string;
    exif_orientation: number;
    rotation_applied: number;
    downscaled: boolean;
    metadata_removed: boolean;
    source_had_gps: boolean;
  };
  provenance?: Record<string, unknown>;
  cached: boolean;
}

export interface ImageExtractionRequest {
  content: string;
  mime_type?: string;
  filename?: string;
  rotation: PhotoRotation;
}

/** Gửi ảnh đề bài cho máy chủ đọc. `signal` huỷ được khi người học thay ảnh. */
export async function extractImageViaServer(
  req: ImageExtractionRequest,
  signal?: AbortSignal,
): Promise<ImageExtractionResponse> {
  return postJson("/api/image/extract", req, signal);
}

/* repo-cleanup: `editViaServer` (`/api/edit`, gỡ ở LEGACY_INFORMATICS_REMOVAL) và `explainViaServer` (`/api/explain`,
   gỡ ở M13 — không còn người gọi trực tiếp) đã xoá cùng 2 endpoint backend không người gọi. */
