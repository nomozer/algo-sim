import { describe, expect, it } from "vitest";
import { AxoClientError } from "../llm/client";
import { analyzeErrorMessage, photoReadErrorMessage } from "./photo-problem-flow";

/** Run `real-world-end-to-end-reliability`: a TEXT analysis failing with `LIVE_AI_DISABLED` must not tell the learner
 *  to "type the problem" (they just did) or talk about image extraction. Found in real-browser E2E. */
function err(reasonCode: string | null, status = 503): AxoClientError {
  const e = Object.create(AxoClientError.prototype) as AxoClientError & Record<string, unknown>;
  Object.assign(e, { name: "AxoClientError", message: "raw", status, reasonCode });
  return e;
}

describe("analysis vs photo infrastructure messages", () => {
  it("text analysis LIVE_AI_DISABLED speaks about analysis, not image extraction", () => {
    const m = analyzeErrorMessage(err("LIVE_AI_DISABLED"))!;
    expect(m).not.toMatch(/ảnh/);
    expect(m).not.toMatch(/gõ đề vào ô nhập/);
    expect(m).not.toMatch(/LIVE_AI_DISABLED|ALLOW_LIVE_AI/);
  });

  it("photo read LIVE_AI_DISABLED keeps the photo guidance", () => {
    expect(photoReadErrorMessage(err("LIVE_AI_DISABLED"))).toMatch(/ảnh/);
  });

  it("abort is silent for both", () => {
    const abort = Object.assign(new Error("x"), { name: "AbortError" });
    expect(analyzeErrorMessage(abort)).toBeNull();
    expect(photoReadErrorMessage(abort)).toBeNull();
  });
});
