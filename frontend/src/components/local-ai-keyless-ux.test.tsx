import { describe, expect, it } from "vitest";
import { AxoClientError, isAiAvailable, type ServerHealth } from "../llm/client";
import { describeComposerError } from "./ProblemInput";

// /api/health under HYBRID_ROUTE_MODE=local-only-scoped without GEMINI_API_KEY (backend/app/main.py::health).
const localReady: ServerHealth = {
  ok: true,
  hasKey: false,
  cachedProblems: 0,
  routeMode: "local-only-scoped",
  localOnlyMode: true,
  localSlmReady: true,
  localSlmModel: "qwen3-0.6b-axo-v9-q4_k_m",
  aiAvailable: true,
};
const localMissing: ServerHealth = { ...localReady, localSlmReady: false, aiAvailable: false };
const cloudNoKey: ServerHealth = { ok: true, hasKey: false, cachedProblems: 0 };

function serviceUnavailable(message: string) {
  return new AxoClientError({ kind: "http", code: "SERVICE_UNAVAILABLE", status: 503, message }).toContract();
}

describe("local-only keyless UX", () => {
  it("treats a ready local model as available without a cloud key", () => {
    expect(isAiAvailable(localReady)).toBe(true);
    expect(isAiAvailable(localMissing)).toBe(false);
    expect(isAiAvailable(cloudNoKey)).toBe(false);
    expect(isAiAvailable({ ok: true, hasKey: true, cachedProblems: 0 })).toBe(true);
  });

  it("does not show a missing-key notice when the local model is ready", () => {
    const shown = describeComposerError("Không kết nối được máy chủ phân tích.", localReady);
    expect(shown?.title).toBe("Không kết nối được máy chủ");
    expect(JSON.stringify(shown)).not.toMatch(/khóa|API key|Gemini/i);
  });

  it("shows the server's local-model message instead of the cloud-key text", () => {
    const msg =
      "Mô hình xử lý trên máy chưa được cài đặt đầy đủ hoặc chưa bật. Em vẫn có thể xem các bài mô phỏng mẫu.";
    const shown = describeComposerError(msg, localMissing, serviceUnavailable(msg));
    expect(shown?.title).toBe("Bộ đọc đề trên máy chưa sẵn sàng");
    expect(shown?.description).toBe(msg);
    expect(JSON.stringify(shown)).not.toMatch(/kết nối AI|khóa|API key|Gemini|MODEL_|LOCAL_SLM/i);
  });

  it("keeps the cloud wording in live mode", () => {
    const shown = describeComposerError("x", cloudNoKey, serviceUnavailable("Thiếu khóa (503)."));
    expect(shown?.title).toBe("Dịch vụ phân tích đề hiện chưa sẵn sàng");
  });
});
