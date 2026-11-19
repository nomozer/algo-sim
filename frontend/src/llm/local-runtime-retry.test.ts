import { afterEach, describe, expect, it, vi } from "vitest";
import { AxoClientError, analyzeViaServer } from "./client";

// /10 live: a LOCAL_SLM_TIMEOUT (45 s on the server) was retried twice by the client => ~135 s of "Đang dựng hình…".
// A failure the backend has already classified as local-runtime timeout/busy is not retried; a bare gateway 502/504
// keeps its bounded retry. Fault injection happens here only (fetch stub); the server timeout is untouched.
const INPUT = { type: "text" as const, content: "Cho hình chóp S.ABC có đáy là tam giác đều cạnh a." };
const POLICY = { maxRetries: 2, baseDelayMs: 1 };

function stub(status: number, body: Record<string, unknown>) {
  let calls = 0;
  vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
    calls += 1;
    return new Response(JSON.stringify(body), { status });
  });
  return () => calls;
}

async function fail(): Promise<AxoClientError> {
  try {
    await analyzeViaServer(INPUT, undefined, POLICY);
  } catch (e) {
    return e as AxoClientError;
  }
  throw new Error("expected a failure");
}

describe("local runtime failures are not retried blindly", () => {
  afterEach(() => vi.restoreAllMocks());

  it("504 LOCAL_SLM_TIMEOUT: one request, message shown at once", async () => {
    const calls = stub(504, { reason_code: "LOCAL_SLM_TIMEOUT", error: "Quá trình phân tích đề mất nhiều thời gian hơn dự kiến." });
    const err = await fail();
    expect(calls()).toBe(1);
    expect(err.code).toBe("HTTP_ERROR");
    expect(err.reasonCode).toBe("LOCAL_SLM_TIMEOUT");
  });

  it("503 LOCAL_SLM_BUSY: one request", async () => {
    const calls = stub(503, { reason_code: "LOCAL_SLM_BUSY", error: "đang bận" });
    await fail();
    expect(calls()).toBe(1);
  });

  it("502 LOCAL_SLM_RESPONSE_INVALID: one request", async () => {
    const calls = stub(502, { reason_code: "LOCAL_SLM_RESPONSE_INVALID", error: "x" });
    await fail();
    expect(calls()).toBe(1);
  });

  it("a bare gateway 504 / 502 keeps the bounded retry (1 + 2)", async () => {
    let calls = stub(504, { detail: "Gateway Timeout" });
    await fail();
    expect(calls()).toBe(3);
    vi.restoreAllMocks();
    calls = stub(502, { detail: "Bad Gateway" });
    await fail();
    expect(calls()).toBe(3);
  });

  it("cancellation stops a retry chain without a second request", async () => {
    let calls = 0;
    const ctl = new AbortController();
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
      calls += 1;
      ctl.abort();
      return new Response(JSON.stringify({ detail: "Bad Gateway" }), { status: 502 });
    });
    await expect(analyzeViaServer(INPUT, ctl.signal, { maxRetries: 2, baseDelayMs: 50 })).rejects.toBeTruthy();
    expect(calls).toBe(1);
  });
});
