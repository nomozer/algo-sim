import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import { analyzeViaServer } from "../llm/client";
import { registerAllSimulations } from "../simulations";
import {
  __resetHistoryForTest,
  createHistoryStore,
  fromServerHistoryDto,
  historyStore,
  memoryStorage,
  newAttemptId,
  type StorageLike,
} from "../state/history";
import { useAppStore } from "../state/store";
import { canonicalPathForView } from "./AxoErrorExperience";
import { runComposerSubmit } from "./ProblemInput";
import { SimulationWorkspace } from "./SimulationWorkspace";

registerAllSimulations();

/** Phản hồi Hybrid /4 THẬT đã đóng băng của main (run hybrid-master-backend-replacement), không dựng tay. */
type Row = { id: string; problem_text: string; response: Record<string, unknown> & { route_d?: { status?: string } } };
const bundle = JSON.parse(readFileSync(resolve(__dirname,
  "../../../docs/evaluation/geometry/runs/hybrid-master-backend-replacement/product-integration-frontend-fixtures.json"), "utf8")) as { fixtures: Row[] };
const row = bundle.fixtures.find((f) => f.response.route_d?.status === "SERVED")!;

const st = () => useAppStore.getState();
const render = () => { Object.assign(useAppStore.getInitialState(), st()); return renderToString(<SimulationWorkspace />); };
const statementOf = (html: string) => html.match(/id="dock-prob-statement"[^>]*>([\s\S]*?)<\/div>/u)?.[1]?.replace(/<[^>]+>/gu, "") ?? "";
const ok = (body: unknown) => new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
const submit = (text: string, analyzeFn?: typeof analyzeViaServer) =>
  runComposerSubmit({ canSubmit: true, lockRef: { current: false }, problemText: text, attachment: null, health: null,
    analyzeFn: analyzeFn ?? ((p, s, _r, id) => analyzeViaServer(p, s, { maxRetries: 0, baseDelayMs: 1 }, id)) });

/**
 * Lần học (attempt) = một lần bấm gửi. Kiểm qua ĐƯỜNG GỬI THẬT (`runComposerSubmit` → `analyzeViaServer` → `fetch`
 * giả trả phản hồi Hybrid /4 thật → `loadEnvelope` → `historyStore`), rồi mở lại/khôi phục.
 */
describe("submission attempt identity through the real submit path", () => {
  beforeEach(() => { __resetHistoryForTest(); st().reset(); });
  afterEach(() => vi.restoreAllMocks());

  it("same statement, same geometry, two independent sends ⇒ two attempts, both reopen intact", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => ok(row.response));
    await submit(row.problem_text);
    const first = st().activeHistoryId!;
    await submit(row.problem_text);
    const second = st().activeHistoryId!;
    expect(first).toMatch(/^a[0-9a-f]{32}$/u);
    expect(second).toMatch(/^a[0-9a-f]{32}$/u);
    expect(second).not.toBe(first);
    expect(historyStore.list().map((x) => x.id).sort()).toEqual([first, second].sort());
    for (const id of [first, second]) {
      st().reopenFromHistory(id);
      expect(st().activeHistoryId).toBe(id);
      expect(statementOf(render())).toContain(row.problem_text.slice(0, 25));
    }
    expect(historyStore.list()).toHaveLength(2);
  });

  it("a network retry inside one send never creates a second attempt", async () => {
    let calls = 0;
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
      calls += 1;
      return calls === 1 ? new Response(JSON.stringify({ detail: "Bad Gateway" }), { status: 502 }) : ok(row.response);
    });
    await submit(row.problem_text, (p, s, _r, id) => analyzeViaServer(p, s, { maxRetries: 2, baseDelayMs: 1 }, id));
    expect(calls).toBe(2);
    expect(historyStore.list()).toHaveLength(1);
    expect(st().activeHistoryId).toMatch(/^a[0-9a-f]{32}$/u);
  });

  it("the attempt id is the server Idempotency-Key: shared by retries of one send, new for the next send", async () => {
    const keys: (string | null)[] = [];
    let calls = 0;
    vi.spyOn(globalThis, "fetch").mockImplementation(async (_u, init) => {
      calls += 1;
      keys.push(new Headers(init?.headers).get("Idempotency-Key"));
      return calls === 1 ? new Response(JSON.stringify({ detail: "Bad Gateway" }), { status: 502 }) : ok(row.response);
    });
    await submit(row.problem_text, (p, s, _r, id) => analyzeViaServer(p, s, { maxRetries: 2, baseDelayMs: 1 }, id));
    const first = st().activeHistoryId!;
    await submit(row.problem_text);
    expect(keys).toEqual([first, first, st().activeHistoryId]);
    expect(keys[2]).not.toBe(first);
  });

  it("a backend error on the next send never brings back the previous scene", async () => {
    let calls = 0;
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
      calls += 1;
      return calls === 1
        ? ok(row.response)
        : new Response(JSON.stringify({ error: "x", reason_code: "PROVIDER_UNAVAILABLE", failure_kind: "INFRASTRUCTURE_FAILURE" }), { status: 503 });
    });
    await submit(row.problem_text);
    expect(st().active).not.toBeNull();
    await submit(`${row.problem_text} (lần khác)`);
    expect(st().active).toBeNull();
    expect(st().activeHistoryId).toBeNull();
    expect(st().analysisError).toBeTruthy();
    expect(historyStore.list()).toHaveLength(1);
  });

  it("reload (route) and reopen keep the attempt id and the attempt's statement", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => ok(row.response));
    await submit(row.problem_text);
    const id = st().activeHistoryId!;
    expect(canonicalPathForView("workspace", st().activeSampleId ?? st().activeHistoryId)).toBe(`/simulation/${id}`);
    st().reset();
    st().syncLocationRoute(`/simulation/${id}`);
    expect(st().activeHistoryId).toBe(id);
    expect(statementOf(render())).toContain(row.problem_text.slice(0, 25));
    expect(historyStore.list()).toHaveLength(1);
  });

  it("server history rows keyed by attempt ids reopen as their own attempts", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => ok(row.response));
    await submit(row.problem_text);
    const a = historyStore.list()[0]!;
    // Hàng máy chủ đúng dạng `/api/history` (mốc thời gian ISO), không phải HistoryItem cục bộ.
    const dto = (x: typeof a, id: string, originalInput: string | null) => ({
      id, title: x.title, simulationId: x.simulationId, domain: x.domain, envelope: x.envelope, originalInput,
      createdAt: new Date(x.createdAt).toISOString(), updatedAt: new Date(x.updatedAt).toISOString(),
      lastViewedAt: new Date(x.lastViewedAt).toISOString(),
    });
    const b = { id: newAttemptId(), originalInput: `${row.problem_text} (lần gửi khác)` };
    __resetHistoryForTest();
    historyStore.replaceAll!([dto(a, a.id, a.originalInput), dto(a, b.id, b.originalInput)].map((x) => fromServerHistoryDto(x)!));
    st().reopenFromHistory(b.id);
    expect(st().activeHistoryId).toBe(b.id);
    expect(statementOf(render())).toContain("(lần gửi khác)");
    st().reopenFromHistory(a.id);
    expect(statementOf(render())).not.toContain("(lần gửi khác)");
  });

  it("two tabs sharing storage keep each other's attempts", () => {
    const storage: StorageLike = memoryStorage();
    const tabA = createHistoryStore(storage);
    const tabB = createHistoryStore(storage);
    const env = row.response.envelope as Parameters<typeof tabA.record>[0];
    const idA = newAttemptId();
    const idB = newAttemptId();
    tabA.record(env, row.problem_text, idA);
    tabB.record(env, row.problem_text, idB);
    tabA.touch(idA, { lastCursor: 2 });
    const ids = tabA.list().map((x) => x.id);
    expect(ids).toContain(idA);
    expect(ids).toContain(idB);
    expect(tabB.list().find((x) => x.id === idA)?.lastCursor).toBe(2);
  });
});
