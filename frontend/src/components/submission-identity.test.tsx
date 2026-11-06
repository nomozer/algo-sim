import { beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { GEOMETRY_SAMPLES } from "../data/geometry-samples";
import { registerAllSimulations } from "../simulations";
import { __resetHistoryForTest, fromServerHistoryDto, historyIdOf, historyStore, HISTORY_SCHEMA_VERSION, type HistoryItem } from "../state/history";
import { useAppStore } from "../state/store";
import { canonicalPathForView } from "./AxoErrorExperience";
import type { SimulationEnvelope } from "../simulations/types";
import { SimulationWorkspace } from "./SimulationWorkspace";

registerAllSimulations();

type Env = SimulationEnvelope & { scene3d?: unknown };
const syncStoreForSSR = () => Object.assign(useAppStore.getInitialState(), useAppStore.getState());
const envelopeOf = (id: string) => structuredClone(GEOMETRY_SAMPLES.find(s => s.id === id)!.envelope) as unknown as Env;
const render = () => { syncStoreForSSR(); return renderToString(<SimulationWorkspace />); };
const st = () => useAppStore.getState();
const statementOf = (html: string) => html.match(/id="dock-prob-statement"[^>]*>([\s\S]*?)<\/div>/u)?.[1]?.replace(/<[^>]+>/gu, "") ?? "";
const sourceOf = (html: string) => html.match(/data-statement-source="([a-z]+)"/u)?.[1];
const item = (id: string) => historyStore.list().find(x => x.id === id)!;
const sceneKey = (env: unknown) => JSON.stringify((env as Env).scene3d ?? null);
const legacyItem = (env: Env, originalInput: string | null): HistoryItem => ({
  id: historyIdOf(env), schemaVersion: HISTORY_SCHEMA_VERSION, title: env.title ?? "", simulationId: env.simulation_id,
  domain: env.domain ?? "geometry", envelope: env, originalInput, createdAt: 1, updatedAt: 1, lastViewedAt: 1, lastCursor: null, visualMode: null,
});

/**
 * Lần gửi (attempt) ≠ chương trình biên dịch (compiled geometry). Hai lần gửi khác nhau không được dùng chung
 * một bản ghi chỉ vì cùng `simulation_id + config`; mở bài mẫu và mở lịch sử giữ đúng nguồn đề.
 */
describe("submission identity vs compiled geometry identity", () => {
  beforeEach(() => { __resetHistoryForTest(); st().reset(); });

  it("two different statements compiling to the same program keep two records; the first is not overwritten", () => {
    const env = envelopeOf("cau-the-tich");
    st().loadEnvelope(envelopeOf("cau-the-tich"), undefined, "Đề thứ nhất: mặt cầu tâm I qua A, IA = 3.");
    const first = st().activeHistoryId!;
    st().loadEnvelope(envelopeOf("cau-the-tich"), undefined, "Đề thứ hai, cách viết khác của cùng hình.");
    const second = st().activeHistoryId!;
    expect(second).not.toBe(first);
    expect(historyStore.list()).toHaveLength(2);
    expect(item(first).originalInput).toBe("Đề thứ nhất: mặt cầu tâm I qua A, IA = 3.");
    expect(sceneKey(item(first).envelope)).toBe(sceneKey(env));
    st().reopenFromHistory(first);
    expect(statementOf(render())).toContain("Đề thứ nhất");
    st().reopenFromHistory(second);
    expect(statementOf(render())).toContain("Đề thứ hai");
  });

  it("the same statement with the same result is one attempt record; with a different scene it is a new one", () => {
    st().loadEnvelope(envelopeOf("cau-the-tich"), undefined, "  Đề   lặp lại  ");
    const a = st().activeHistoryId!;
    st().loadEnvelope(envelopeOf("cau-the-tich"), undefined, "Đề lặp lại");
    expect(st().activeHistoryId).toBe(a);
    const other = { ...envelopeOf("cau-the-tich"), scene3d: envelopeOf("cau-cat-mat-phang").scene3d };
    st().loadEnvelope(other, undefined, "Đề lặp lại");
    const b = st().activeHistoryId!;
    expect(b).not.toBe(a);
    expect(sceneKey(item(a).envelope)).toBe(sceneKey(envelopeOf("cau-the-tich")));
    expect(historyStore.list()).toHaveLength(2);
  });

  it("a submission sharing a sample's program is presented as a submission: own URL, own UI snapshot key, own statement on reload", () => {
    st().loadEnvelope(envelopeOf("cau-cat-mat-phang"), undefined, "Đề học sinh, cùng chương trình với bài mẫu.");
    const id = st().activeHistoryId!;
    expect(st().activeSampleId).toBeNull();
    expect(canonicalPathForView("workspace", st().activeSampleId ?? st().activeHistoryId)).toBe(`/simulation/${id}`);
    // Reload: route `/simulation/<id>` → history_item → reopenFromHistory
    st().reset();
    st().syncLocationRoute(`/simulation/${id}`);
    expect(st().activeHistoryId).toBe(id);
    expect(st().activeSampleId).toBeNull();
    const html = render();
    expect(statementOf(html)).toContain("Đề học sinh, cùng chương trình với bài mẫu.");
    expect(sourceOf(html)).toBe("learner");
  });

  it("opening the sample never touches the submission record and shows the catalog statement", () => {
    st().loadEnvelope(envelopeOf("cau-cat-mat-phang"), undefined, "Đề học sinh, cùng chương trình với bài mẫu.");
    const sub = st().activeHistoryId!;
    const before = JSON.stringify(item(sub));
    st().loadEnvelope(envelopeOf("cau-cat-mat-phang"), "cau-cat-mat-phang");
    expect(st().activeSampleId).toBe("cau-cat-mat-phang");
    expect(st().activeHistoryId).not.toBe(sub);
    const html = render();
    expect(statementOf(html)).toContain("Cho mặt cầu tâm I bán kính 5");
    expect(sourceOf(html)).toBe("catalog");
    expect(JSON.stringify(item(sub))).toBe(before);
  });

  it("legacy records keyed by the compiled identity are read and reused, never duplicated or rewritten", () => {
    const env = envelopeOf("cau-the-tich");
    historyStore.replaceAll!([legacyItem(env, "Đề cũ đã lưu trước khi có khoá lần gửi.")]);
    const legacyId = historyIdOf(env);
    st().reopenFromHistory(legacyId);
    expect(st().activeHistoryId).toBe(legacyId);
    expect(historyStore.list()).toHaveLength(1);
    expect(statementOf(render())).toContain("Đề cũ đã lưu");
    // Gửi lại đúng đề cũ, cùng kết quả → dùng lại bản ghi cũ (không nhân bản).
    st().loadEnvelope(envelopeOf("cau-the-tich"), undefined, "Đề cũ đã lưu trước khi có khoá lần gửi.");
    expect(st().activeHistoryId).toBe(legacyId);
    expect(historyStore.list()).toHaveLength(1);
    // Một đề KHÁC cùng chương trình → bản ghi mới; bản ghi cũ giữ nguyên đề.
    st().loadEnvelope(envelopeOf("cau-the-tich"), undefined, "Đề mới khác hẳn.");
    expect(st().activeHistoryId).not.toBe(legacyId);
    expect(item(legacyId).originalInput).toBe("Đề cũ đã lưu trước khi có khoá lần gửi.");
  });

  it("a legacy non-sample record without a stored statement says so instead of showing the model description", () => {
    const env = { ...envelopeOf("cau-the-tich"), config: { ...(envelopeOf("cau-the-tich").config as object), title: "bài không thuộc thư viện" }, description: "Lời mô tả kỹ thuật XYZ." } as Env;
    historyStore.replaceAll!([legacyItem(env, null)]);
    st().reopenFromHistory(historyIdOf(env));
    const html = render();
    expect(sourceOf(html)).toBe("missing");
    // Thiếu đề được nói thẳng; mô tả kỹ thuật chỉ đi sau nhãn, không đứng thay đề.
    expect(statementOf(html).startsWith("Bản ghi này không lưu đề gốc.")).toBe(true);
    expect(statementOf(html)).toContain("Mô tả mô hình do hệ thống tạo: Lời mô tả kỹ thuật XYZ.");
  });

  it("server history with old (h…) and new (s…) keys is read and reopened with each row's own statement", () => {
    st().loadEnvelope(envelopeOf("cau-the-tich"), undefined, "Đề mới lưu bằng khoá lần gửi.");
    const fresh = item(st().activeHistoryId!);
    const env = envelopeOf("cau-cat-mat-phang");
    const rows = [
      { id: historyIdOf(env), title: env.title!, simulationId: env.simulation_id, domain: "geometry", envelope: env, originalInput: "Đề cũ trên máy chủ, khoá h…" },
      { id: fresh.id, title: fresh.title, simulationId: fresh.simulationId, domain: "geometry", envelope: fresh.envelope, originalInput: fresh.originalInput },
    ];
    __resetHistoryForTest();
    historyStore.replaceAll!(rows.map(r => fromServerHistoryDto(r)!));
    expect(fresh.id.startsWith("s")).toBe(true);
    st().reopenFromHistory(historyIdOf(env));
    expect(statementOf(render())).toContain("Đề cũ trên máy chủ");
    expect(st().activeSampleId).toBeNull();
    st().reopenFromHistory(fresh.id);
    expect(statementOf(render())).toContain("Đề mới lưu bằng khoá lần gửi.");
    expect(historyStore.list()).toHaveLength(2);
  });

  it("a stored record carrying viewer runtime flags (_auxiliaryShown, persisted by older builds) reopens to its own record", () => {
    st().loadEnvelope(envelopeOf("cau-the-tich"), undefined, "Đề có cờ chạy-thời-gian bị lưu kèm.");
    const id = st().activeHistoryId!;
    const stored = item(id);
    const polluted = structuredClone(stored);
    for (const o of (polluted.envelope as Env & { scene3d: { objects: Record<string, unknown>[] } }).scene3d.objects) o._auxiliaryShown = true;
    historyStore.replaceAll!([polluted]);
    st().reopenFromHistory(id);
    expect(st().activeHistoryId).toBe(id);
    expect(historyStore.list()).toHaveLength(1);
  });

  it("switching problems while an object is selected does not carry the selection or step to the other record", () => {
    st().loadEnvelope(envelopeOf("cau-cat-mat-phang"), undefined, "Đề A cùng chương trình mẫu.");
    const keyA = `history:${st().activeHistoryId}`;
    st().loadEnvelope(envelopeOf("cau-cat-mat-phang"), "cau-cat-mat-phang");
    expect(`sample:${st().activeSampleId}`).not.toBe(keyA);
  });
});
