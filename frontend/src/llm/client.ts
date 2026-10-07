import type { AnalysisUnsupported } from "../core/types";
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

async function postJson<T>(url: string, payload: unknown, signal?: AbortSignal): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    });
  } catch (err) {
    // Huỷ CHỦ ĐỘNG (người học thay/xoá ảnh) không phải lỗi kết nối — ném nguyên
    // để nơi gọi nhận ra và im lặng, thay vì hiện lời nhắc bật máy chủ.
    if ((err as { name?: string } | null)?.name === "AbortError") throw err;
    throw new Error(CONNECT_HELP);
  }

  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    /* rơi xuống nhánh lỗi bên dưới */
  }

  if (!res.ok) {
    const msg =
      body && typeof body === "object" && "error" in body
        ? String((body as { error: unknown }).error)
        : `Máy chủ trả lỗi HTTP ${res.status}.`;
    throw new Error(msg);
  }
  return body as T;
}

export async function fetchHealth(): Promise<ServerHealth | null> {
  try {
    const res = await fetch("/api/health");
    if (!res.ok) return null;
    return (await res.json()) as ServerHealth;
  } catch {
    return null;
  }
}

/** Pipeline phân tích: đầu vào chuẩn hóa text/document/code/image (M4). */
export async function analyzeViaServer(
  input: InputPayload,
): Promise<SimulationEnvelope | AnalysisUnsupported> {
  return postJson("/api/analyze", { input });
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
 * người gọi duy nhất là `AIHelpPanel` không còn gắn vào giao diện) đã gỡ cùng route backend. */
