import { beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { GEOMETRY_SAMPLES } from "../data/geometry-samples";
import { registerAllSimulations } from "../simulations";
import { __resetHistoryForTest } from "../state/history";
import { useAppStore } from "../state/store";
import type { SimulationEnvelope } from "../simulations/types";
import { SimulationWorkspace } from "./SimulationWorkspace";

registerAllSimulations();

const syncStoreForSSR = () => Object.assign(useAppStore.getInitialState(), useAppStore.getState());
const envelopeOf = (id: string) => structuredClone(GEOMETRY_SAMPLES.find(s => s.id === id)!.envelope) as unknown as SimulationEnvelope;
// Envelope Hybrid /4 (backend/app/ai/adapter4_route.py) ghi lời lưu ý chung vào `description`, không ghi đề.
const HYBRID_NOTICE = "Quan sát mô hình dựng từ dữ kiện; các kiểm tra trên hình không phải chứng minh tổng quát.";

/** "Đề bài" trong xưởng phải là đề của CHÍNH bản ghi đang mở. */
describe("workspace problem statement belongs to the open record", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
  });

  it("an analysed problem shows the learner's own text, not the envelope notice", () => {
    const env = { ...envelopeOf("cau-cat-mat-phang"), description: HYBRID_NOTICE, source: "hybrid_route_d" } as SimulationEnvelope;
    const typed = "Cho mặt cầu tâm I bán kính 5 và mặt phẳng (P) cách I một khoảng bằng 3. Tính diện tích thiết diện.";
    useAppStore.getState().loadEnvelope(env, undefined, typed);
    syncStoreForSSR();
    const html = renderToString(<SimulationWorkspace />);
    expect(html).toContain(typed);
    expect(html).not.toContain(HYBRID_NOTICE);
  });

  it("stale composer text from another problem never becomes the statement", () => {
    const stale = "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2 — đề cũ trong ô soạn";
    useAppStore.getState().setProblemText(stale);
    const env = envelopeOf("cau-the-tich");
    delete (env as { description?: string }).description;
    useAppStore.getState().loadEnvelope(env, "cau-the-tich");
    syncStoreForSSR();
    const html = renderToString(<SimulationWorkspace />);
    expect(html).not.toContain(stale);
    expect(html).toContain(env.title!);
  });

  it("an old record without a statement never borrows one from equivalent catalog geometry", () => {
    const env = { ...envelopeOf("cau-the-tich"), description: HYBRID_NOTICE };
    useAppStore.getState().loadEnvelope(env, undefined, undefined, "legacy-without-statement");
    syncStoreForSSR();
    const html = renderToString(<SimulationWorkspace />);
    expect(useAppStore.getState().activeHistoryId).toBe("legacy-without-statement");
    expect(useAppStore.getState().activeSampleId).toBeNull();
    expect(html).toContain("Bản ghi này không lưu đề gốc");
    expect(html).toContain('data-statement-source="missing"');
  });

  it("an explicit catalog open saves its original statement and reopens as that sample with the same history ID", () => {
    const sample = GEOMETRY_SAMPLES.find(s => s.id === "cau-the-tich")!;
    useAppStore.getState().loadEnvelope(envelopeOf(sample.id), sample.id);
    const id = useAppStore.getState().activeHistoryId!;
    const record = useAppStore.getState().history.find(h => h.id === id)!;
    expect(record.envelope.problem_statement).toBe(sample.problemText);
    useAppStore.getState().goHome();
    useAppStore.getState().reopenFromHistory(id);
    syncStoreForSSR();
    expect(useAppStore.getState().activeHistoryId).toBe(id);
    expect(useAppStore.getState().activeSampleId).toBe(sample.id);
    expect(useAppStore.getState().history.filter(h => h.id === id)).toHaveLength(1);
    const html = renderToString(<SimulationWorkspace />);
    expect(html).toContain("Cho mặt cầu tâm I đi qua điểm A");
    expect(html).toContain('data-statement-source="catalog"');
    expect(html).not.toContain("Bản ghi này không lưu đề gốc");
  });

  it("reopening an unstamped record keyed like a sample stays a record without a statement", () => {
    const env = { ...envelopeOf("cau-the-tich"), description: HYBRID_NOTICE };
    useAppStore.getState().loadEnvelope(env);              // no sample ID, no statement: content key only
    const id = useAppStore.getState().activeHistoryId!;
    useAppStore.getState().goHome();
    useAppStore.getState().reopenFromHistory(id);
    syncStoreForSSR();
    expect(useAppStore.getState().activeHistoryId).toBe(id);
    expect(useAppStore.getState().activeSampleId).toBeNull();
    const html = renderToString(<SimulationWorkspace />);
    expect(html).toContain('data-statement-source="missing"');
  });
});
