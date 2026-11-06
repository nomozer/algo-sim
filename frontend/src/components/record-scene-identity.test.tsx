import { beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { GEOMETRY_SAMPLES } from "../data/geometry-samples";
import { recoverCatalogScene3D } from "../data/offline-catalog";
import { registerAllSimulations } from "../simulations";
import { __resetHistoryForTest, historyIdOf, historyStore } from "../state/history";
import { useAppStore } from "../state/store";
import type { SimulationEnvelope } from "../simulations/types";
import { SimulationWorkspace } from "./SimulationWorkspace";

registerAllSimulations();

const syncStoreForSSR = () => Object.assign(useAppStore.getInitialState(), useAppStore.getState());
const envelopeOf = (id: string) => structuredClone(GEOMETRY_SAMPLES.find(s => s.id === id)!.envelope) as unknown as SimulationEnvelope & { scene3d?: unknown };
const render = () => { syncStoreForSSR(); return renderToString(<SimulationWorkspace />); };
const sceneIds = () => ((useAppStore.getState().active?.envelope as { scene3d?: { objects: { id: string }[] } })?.scene3d?.objects ?? []).map(o => o.id);

/** Đề bài và Scene3D trên màn hình phải thuộc CÙNG một bản ghi; tiêu đề không phải bằng chứng hai bài là một. */
describe("record ↔ statement ↔ Scene3D identity", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
  });

  it("a legacy record without scene3d is never given a sample scene just because the title matches", () => {
    const sample = envelopeOf("cau-cat-mat-phang");
    const legacy = { ...sample, config: { ...(sample.config as object), title: "đề tự gõ trùng tiêu đề" }, description: "Đề riêng của học sinh, khác bài mẫu." };
    delete legacy.scene3d;
    expect((recoverCatalogScene3D(legacy) as { scene3d?: unknown }).scene3d).toBeUndefined();
    // Cùng config với bài mẫu = cùng chương trình đã biên dịch ⇒ khôi phục được.
    const sameProgram = { ...sample }; delete sameProgram.scene3d;
    expect((recoverCatalogScene3D(sameProgram) as { scene3d?: unknown }).scene3d).toBeDefined();

    useAppStore.getState().loadEnvelope(legacy, undefined, "Đề riêng của học sinh, khác bài mẫu.");
    const html = render();
    expect(html).toContain("Bản ghi này chưa có dữ liệu không gian 3D hợp lệ");
    expect(html).not.toContain("Dựng đường tròn thiết diện"); // bước dựng của bài mẫu
    expect(html).not.toContain('data-step="0"');
  });

  it("two problems with the same title keep their own record, statement and scene (A → B → A)", () => {
    const a = { ...envelopeOf("cau-the-tich"), title: "Bài mặt cầu" } as SimulationEnvelope;
    const bBase = envelopeOf("cau-cat-mat-phang");
    const b = { ...bBase, title: "Bài mặt cầu" } as SimulationEnvelope;
    expect(historyIdOf(a)).not.toBe(historyIdOf(b));
    const store = useAppStore.getState();
    store.loadEnvelope(a, undefined, "Đề A: mặt cầu tâm I qua A, IA = 3.");
    const idA = useAppStore.getState().activeHistoryId!;
    store.loadEnvelope(b, undefined, "Đề B: mặt cầu bán kính 5 cắt mặt phẳng cách tâm 3.");
    const idB = useAppStore.getState().activeHistoryId!;
    expect(idA).not.toBe(idB);
    expect(historyStore.list()).toHaveLength(2);

    useAppStore.getState().reopenFromHistory(idA);
    let html = render();
    expect(html).toContain("Đề A: mặt cầu tâm I qua A"); // "IA = 3" được bọc trong span toán
    expect(html).not.toContain("Đề B:");
    expect(sceneIds()).toContain("A");
    expect(sceneIds()).not.toContain("P");

    useAppStore.getState().reopenFromHistory(idB);
    html = render();
    expect(html).toContain("Đề B: mặt cầu bán kính 5 cắt mặt phẳng cách tâm 3");
    expect(html).not.toContain("Đề A:");
    expect(sceneIds()).toContain("P");
  });

  it("opening a sample from the library shows the sample statement even if an analysis shares its record", () => {
    const env = envelopeOf("cau-cat-mat-phang");
    const desc = env.description!;
    useAppStore.getState().loadEnvelope(env, undefined, "Đề học sinh tự gõ, cùng chương trình với bài mẫu");
    const recordId = useAppStore.getState().activeHistoryId!;
    useAppStore.getState().loadEnvelope(envelopeOf("cau-cat-mat-phang"), "cau-cat-mat-phang");
    // Từ 2026-11-05 (axo-data-identity-test-hardening): lần gửi có khoá riêng, không dùng chung bản ghi với bài mẫu.
    expect(useAppStore.getState().activeHistoryId).not.toBe(recordId);
    let html = render();
    expect(html).not.toContain("Đề học sinh tự gõ");
    expect(html).toContain(desc.slice(0, 30));
    useAppStore.getState().reopenFromHistory(recordId);
    html = render();
    expect(html).toContain("Đề học sinh tự gõ, cùng chương trình với bài mẫu");
  });

  it("re-submitting into an existing record keeps statement and scene from the same submission", () => {
    // Cùng config (cùng khoá bản ghi) nhưng lần gửi sau mang scene khác: đề hiển thị phải đi cùng scene mới.
    const first = envelopeOf("cau-the-tich");
    const second = { ...envelopeOf("cau-the-tich"), scene3d: envelopeOf("cau-cat-mat-phang").scene3d };
    expect(historyIdOf(first as SimulationEnvelope)).toBe(historyIdOf(second as SimulationEnvelope));
    useAppStore.getState().loadEnvelope(first as SimulationEnvelope, undefined, "Lần gửi 1");
    useAppStore.getState().loadEnvelope(second as SimulationEnvelope, undefined, "Lần gửi 2");
    const html = render();
    expect(sceneIds()).toContain("P");
    expect(html).toContain("Lần gửi 2");
    expect(html).not.toContain("Lần gửi 1");
  });
});
