import { afterEach, describe, expect, it } from "vitest";
import { analyzeViaServer, extractImageViaServer } from "./client";

/**
 * `session_required` (backend `reserve_analysis_usage` / `_cong_luot_thu`): a request without a valid session runs
 * nothing, and the server issues a guest session cookie on that refusal. The client sends the SAME request once more
 * (same attempt ID), never more — a client that keeps losing its cookie gets the refusal, not a loop. 0 network calls.
 */
const realFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = realFetch; });

function scripted(...responses: (() => Response)[]) {
  const calls: RequestInit[] = [];
  globalThis.fetch = (async (_url: RequestInfo | URL, init?: RequestInit) => {
    calls.push(init ?? {});
    return (responses[calls.length - 1] ?? responses[responses.length - 1])();
  }) as typeof fetch;
  return calls;
}
const json = (status: number, body: unknown) => () => new Response(JSON.stringify(body), { status });
const SESSION_REQUIRED = json(401, { error: "x", reason_code: "session_required" });

describe("session_required", () => {
  it("analysis is sent once more with the same attempt ID after the server issued a session", async () => {
    const calls = scripted(SESSION_REQUIRED, json(200, { status: "unsupported", reason: "r" }));
    const out = await analyzeViaServer({ type: "text", content: "Cho hình chóp S.ABC." }, undefined, { maxRetries: 0 }, "a" + "1".repeat(32));
    expect(out).toMatchObject({ status: "unsupported" });
    expect(calls).toHaveLength(2);
    const key = (c: RequestInit) => (c.headers as Record<string, string>)["Idempotency-Key"];
    expect(key(calls[0])).toBe(key(calls[1]));
    expect(calls.every((c) => c.credentials === "include")).toBe(true);
  });

  it("a second session_required is the answer, not a loop", async () => {
    const calls = scripted(SESSION_REQUIRED);
    await expect(analyzeViaServer({ type: "text", content: "Cho hình chóp S.ABC." }, undefined, { maxRetries: 0 }))
      .rejects.toMatchObject({ status: 401 });
    expect(calls).toHaveLength(2);
  });

  it("image extraction is sent once more too", async () => {
    const calls = scripted(SESSION_REQUIRED, json(200, { status: "ok" }));
    await extractImageViaServer({ content: "AAAA", mime_type: "image/png", rotation: 0 });
    expect(calls).toHaveLength(2);
  });
});
