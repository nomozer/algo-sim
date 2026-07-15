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

async function postJson<T>(url: string, payload: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
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

/** Kết quả edit tăng dần (M7.14A) — status theo docs/CORRECTNESS.md §3. */
export type EditResponse =
  | { status: "ok"; config: unknown; patch: { operations: unknown[] }; note?: string }
  | { status: "unsupported_to_verify"; reason: string };

/**
 * Chỉnh sửa TĂNG DẦN mô phỏng generic hiện có — KHÔNG chạy full pipeline.
 * Server sinh patch (1 call LLM nhỏ) + validate; lỗi cấu trúc → throw (422).
 */
export async function editViaServer(params: {
  simulationId: string;
  config: unknown;
  instruction: string;
}): Promise<EditResponse> {
  return postJson("/api/edit", {
    simulation_id: params.simulationId,
    config: params.config,
    instruction: params.instruction,
  });
}

export interface ExplainTurn {
  role: "user" | "assistant";
  text: string;
}

/** Giải thích trạng thái thật của engine — context từ module.getExplainContext. */
export async function explainViaServer(params: {
  simulationId: string;
  explainContext: Record<string, unknown>;
  question: string;
  recentHistory: ExplainTurn[];
}): Promise<string> {
  const body = await postJson<{ reply: string }>("/api/explain", {
    simulation_id: params.simulationId,
    explain_context: params.explainContext,
    question: params.question,
    recent_history: params.recentHistory.slice(-8),
  });
  return body.reply;
}
