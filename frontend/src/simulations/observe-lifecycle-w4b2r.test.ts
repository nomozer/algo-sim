import { beforeAll, describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { OFFLINE_SAMPLES } from "../data/sim-samples";
import { offlineCatalog } from "../data/offline-catalog";
import { useAppStore } from "../state/store";
import { registerAllSimulations } from "./index";
import { getSimulation, listSimulations } from "./registry";

/**
 * W4B-2R — VÒNG ĐỜI QUAN SÁT, ĐO TRÊN TOÀN DANH MỤC.
 *
 * Ba luật, và cả ba đo được mà không cần trình duyệt:
 *   LEARNER_INITIATES_FIRST_RUN            — nạp xong là DỪNG, không tự chạy
 *   CANONICAL_RUN_CAN_COMPLETE_WITHOUT_PREDICTION — chạy hết trace mà không đụng predict
 *   OBSERVE_REQUIRES_NO_ANSWER             — không có đường nào từ prediction sang timeline
 *
 * Danh sách target DẪN XUẤT TỪ REGISTRY (§44). Chép tay sẽ vẫn xanh khi target
 * thứ 23 ra đời mà không ai kiểm nó — im lặng đúng lúc cần nói nhất.
 */

beforeAll(() => {
  if (listSimulations().length === 0) registerAllSimulations();
});

/** Mọi envelope chạy được offline — gồm cả bài mẫu lẫn catalog phân tích sẵn. */
const runnable = () => {
  const seen = new Set<string>();
  const out: { id: string; envelope: unknown }[] = [];
  for (const s of OFFLINE_SAMPLES) {
    if (seen.has(s.envelope.simulation_id)) continue;
    seen.add(s.envelope.simulation_id);
    out.push({ id: s.envelope.simulation_id, envelope: s.envelope });
  }
  for (const e of offlineCatalog()) {
    if (seen.has(e.simId)) continue;
    seen.add(e.simId);
    out.push({ id: e.simId, envelope: e.envelope });
  }
  return out;
};

describe("W4B-2R · LEARNER_INITIATES_FIRST_RUN", () => {
  it("`playing` chỉ được bật bởi setPlaying — không đường nạp nào tự chạy", () => {
    /* Kiểm ở NGUỒN thay vì thử từng envelope: một `playing: true` lọt vào bất kỳ
       nhánh nạp nào cũng là autoplay, kể cả nhánh chưa có fixture. */
    const src = readFileSync(new URL("../state/store.ts", import.meta.url), "utf-8");
    const writes = [...src.matchAll(/playing:\s*(true|false|[a-z])/g)].map((m) => m[1]);
    expect(writes.length).toBeGreaterThan(0);
    for (const w of writes) {
      expect(w, `store ghi playing = ${w} ở đâu đó ngoài setPlaying`).not.toBe("true");
    }
    // …và `setPlaying` vẫn là cửa duy nhất nhận giá trị từ ngoài.
    expect(src).toContain("setPlaying: (v) => set({ playing: v })");
  });

  it("mọi target nạp xong đều ở trạng thái DỪNG, con trỏ ở bước đầu", () => {
    for (const { id, envelope } of runnable()) {
      useAppStore.getState().reset();
      useAppStore.getState().loadEnvelope(envelope as never);
      const st = useAppStore.getState();
      expect(st.playing, `${id}: tự chạy ngay sau khi nạp`).toBe(false);
      if (!st.active) continue;
      const mod = getSimulation(st.active.moduleId)!;
      if (mod.timeline) {
        expect(mod.timeline.currentStep(st.active.state), `${id}: không bắt đầu ở bước đầu`).toBe(0);
      }
    }
  });
});

describe("W4B-2R · CANONICAL_RUN_CAN_COMPLETE_WITHOUT_PREDICTION", () => {
  it("mọi target có timeline chạy TRỌN VẸN mà không gọi predict một lần nào", () => {
    for (const { id, envelope } of runnable()) {
      useAppStore.getState().reset();
      useAppStore.getState().loadEnvelope(envelope as never);
      const st0 = useAppStore.getState();
      if (!st0.active) continue;
      const mod = getSimulation(st0.active.moduleId)!;
      if (!mod.timeline) continue;

      const total = mod.timeline.stepCount(st0.active.state);
      // Đi hết bằng ĐÚNG hành động của nút "Tiến" — không đụng submitPrediction.
      for (let k = 0; k < total + 2; k += 1) useAppStore.getState().nextStep();

      const end = useAppStore.getState();
      const cursor = mod.timeline.currentStep(end.active!.state);
      expect(cursor, `${id}: không tới được bước cuối nếu không trả lời`).toBe(total - 1);
      expect(end.prediction, `${id}: chạy trọn trace mà vẫn sinh prediction`).toBeNull();
      // Tới cuối thì trình phát tự dừng — không treo ở trạng thái "đang chạy".
      expect(end.playing, `${id}: còn playing sau khi hết trace`).toBe(false);
    }
  });
});

describe("W4B-2R · OBSERVE_REQUIRES_NO_ANSWER", () => {
  it("không có đường nào từ `prediction` sang timeline trong store", () => {
    const src = readFileSync(new URL("../state/store.ts", import.meta.url), "utf-8")
      .replace(/\/\*[\s\S]*?\*\//g, "")
      .replace(/^\s*\/\/.*$/gm, "");
    const advance = src.slice(src.indexOf("nextStep:"), src.indexOf("prevStep:"));
    expect(advance, "nextStep đọc prediction ⇒ cổng quiz trong Observe")
      .not.toContain("prediction");
    // …và chấm điểm không được đụng con trỏ bước.
    const submit = src.slice(src.indexOf("submitPrediction:"), src.indexOf("clearPrediction:"));
    expect(submit).not.toMatch(/goToStep|nextStep|cursor/);
  });

  it("PREDICTION_IS_OPTIONAL_WHERE_PRESENT — predict là capability, không bắt buộc", () => {
    const withPredict = listSimulations()
      .map((m) => getSimulation(m.id)!)
      .filter((m) => m.predict !== undefined);
    // Có thật (nếu 0 thì test này vô nghĩa và phải biết ngay).
    expect(withPredict.length).toBeGreaterThan(0);
    for (const m of withPredict) {
      // Module không được đòi hỏi gì để `timeline` chạy: hai capability rời nhau.
      expect(m.timeline, `${m.id}`).toBeDefined();
    }
  });
});

describe("W4B-2R · RENDERER_DOES_NOT_OWN_RESULT", () => {
  it("không renderer nào tự chấm hay tự dựng kết quả", () => {
    const files = [
      "../components/ArrayView.tsx",
      "../components/SearchActionZone.tsx",
      "../components/ScanActionZone.tsx",
      "../components/SortActionZone.tsx",
      "./domains/network/ui.tsx",
      "./domains/algorithm/ui.tsx",
    ];
    for (const f of files) {
      const src = readFileSync(new URL(f, import.meta.url), "utf-8")
        .replace(/\/\*[\s\S]*?\*\//g, "")
        .replace(/^\s*\/\/.*$/gm, "");
      for (const forbidden of ["correctActionId", "isCorrect(", "checkAnswer(", "bfsRoute("]) {
        expect(src, `${f}: renderer sở hữu kết quả (${forbidden})`).not.toContain(forbidden);
      }
    }
  });
});
