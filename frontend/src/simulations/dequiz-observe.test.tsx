import { beforeEach, describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import {
  challengeEntry,
  challengeSurfaceVisible,
} from "../components/SimulationWorkspace";
import { useAppStore } from "../state/store";
import { registerAllSimulations } from "./index";
import { getSimulation, listSimulations } from "./registry";
import { offlineCatalog, publicCatalog } from "../data/offline-catalog";

/**
 * W4B-2U2 §13/§32 — QUAN SÁT KHÔNG PHẢI HỎI-ĐÁP.
 *
 * Sự thật đã đo ở U2-A: `PredictionBar` **chưa từng chặn** playback — nó trả
 * `null` khi `busy`, và `nextStep` không đọc `prediction`. Nên viết test kiểu
 * "gỡ cái chốt" sẽ **XANH SẴN** và chứng minh nhầm.
 *
 * Điều phải khoá là **SỰ HIỆN DIỆN**: hễ module khai `predict` là thanh dự đoán
 * nằm thường trực trong Quan sát ở cả 11 target, khiến sản phẩm đọc thành
 * hỏi-đáp. Nay nó thuộc chế độ THỬ THÁCH do học sinh chủ động mở.
 *
 * Ranh giới không đổi: dời TRÌNH BÀY, không dời SỰ THẬT — `predict.check` vẫn
 * là bên chấm duy nhất (bất biến #11).
 */

registerAllSimulations();

const modulesWithPredict = () =>
  listSimulations().map((m) => getSimulation(m.id)!).filter((m) => m.predict !== undefined);

/** Envelope chạy được offline, kèm nhãn bề mặt (§27 — không lẫn fixture nội bộ). */
const runnable = (onlyPublic: boolean) => {
  const src = onlyPublic ? publicCatalog() : offlineCatalog();
  const seen = new Set<string>();
  return src.filter((e) => {
    if (seen.has(e.simId)) return false;
    seen.add(e.simId);
    return getSimulation(e.simId)?.predict !== undefined;
  });
};

/* ⚠️ KHÔNG dùng `renderToString(<SimulationWorkspace/>)` ở đây.
   `SimulationWorkspace` đọc store; zustand v5 dùng `useSyncExternalStore` nên SSR
   trả TRẠNG THÁI ĐẦU (`ARCHITECTURE_MAP §8` #8) — màn hình sẽ là `empty-state`,
   và mọi khẳng định "không chứa X" XANH vì rỗng, không vì đúng. Luật được kiểm
   qua hàm THUẦN `challengeSurfaceVisible`/`challengeEntryVisible`. */

/** State ban đầu của một envelope chạy được — không qua store/SSR. */
function initOf(simId: string, envelope: unknown) {
  const mod = getSimulation(simId)!;
  const r = mod.validateConfig((envelope as { config: unknown }).config);
  if (!r.ok) throw new Error(`${simId}: ${r.error}`);
  return { mod, config: r.config, state: mod.init(r.config) };
}

beforeEach(() => useAppStore.getState().reset());

/* ══ 1. NĂNG LỰC VẪN CÒN, CHỈ ĐỔI CHỖ BÀY ════════════════════════════════ */

describe("W4B-2U2 · năng lực dự đoán KHÔNG bị xoá", () => {
  it("đúng 11 target khai `predict` — dời trình bày, không cắt năng lực", () => {
    expect(modulesWithPredict().map((m) => m.id).sort()).toEqual([
      "algorithm.binary_search", "algorithm.bubble_sort", "algorithm.count_if",
      "algorithm.find_max", "algorithm.find_min", "algorithm.insertion_sort",
      "algorithm.linear_search", "algorithm.selection_sort", "algorithm.sum_if",
      "network.packet_routing", "network.protocol_encapsulation",
    ]);
  });

  it("`predict.check` vẫn là bên chấm tất định — không đụng một dòng", () => {
    for (const mod of modulesWithPredict()) {
      expect(typeof mod.predict!.check, `${mod.id}`).toBe("function");
      expect(typeof mod.predict!.challenge, `${mod.id}`).toBe("function");
    }
  });
});

/* ══ 2. QUAN SÁT SẠCH BỀ MẶT HỎI-ĐÁP ═════════════════════════════════════ */

describe("W4B-2U2 · DEFAULT_OBSERVE_DEQUIZZED", () => {
  it("mặc định `challengeOpen` = false — Quan sát là chế độ mở đầu", () => {
    expect(useAppStore.getState().challengeOpen).toBe(false);
  });

  it("mọi target PUBLIC khai predict: Quan sát KHÔNG bày thanh dự đoán", () => {
    const targets = runnable(true);
    expect(targets.length, "không có target công khai nào để kiểm").toBeGreaterThan(0);
    for (const e of targets) {
      const { mod, state } = initOf(e.simId, e.envelope);
      expect(challengeSurfaceVisible(mod, state, false), `${e.simId}: bày ở Quan sát`)
        .toBe(false);
    }
  });

  /* W4B-3A — lối vào nay TRẢ VỀ CÂU MỜI thay vì một boolean, và nó có quyền
     trả `null` khi mở ra không có gì để cam kết. Nên khẳng định đúng thứ đáng
     giữ: dọc TOÀN BỘ timeline phải có ít nhất một bước mời được — mất hẳn lối
     vào ở mọi bước mới là mất năng lực. */
  it("lối vào Thử thách vẫn thấy được — không giấu mất năng lực", () => {
    for (const e of runnable(true)) {
      const { mod, config, state } = initOf(e.simId, e.envelope);
      const total = mod.timeline?.stepCount(state) ?? 1;
      let seen = 0;
      for (let i = 0; i < total; i += 1) {
        const at = mod.timeline ? mod.timeline.goToStep(state, i) : state;
        if (challengeEntry(mod, at, config)) seen += 1;
      }
      expect(seen, `${e.simId}: không bước nào mời được Thử thách`).toBeGreaterThan(0);
    }
  });

  it("mở Thử thách ⇒ thanh dự đoán xuất hiện trở lại", () => {
    for (const e of runnable(true)) {
      const { mod, state } = initOf(e.simId, e.envelope);
      expect(challengeSurfaceVisible(mod, state, true), `${e.simId}`).toBe(true);
    }
  });
});

/* ══ 3. PLAYBACK ĐỘC LẬP — LUẬT CŨ KHÔNG ĐƯỢC HỎNG ═══════════════════════ */

describe("W4B-2U2 · playback độc lập với dự đoán", () => {
  it("`nextStep` không đọc `prediction`, `submitPrediction` không đụng cursor", () => {
    const src = readFileSync(new URL("../state/store.ts", import.meta.url), "utf-8")
      .replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
    const advance = src.slice(src.indexOf("nextStep:"), src.indexOf("prevStep:"));
    expect(advance).not.toContain("prediction");
    const submit = src.slice(src.indexOf("submitPrediction:"), src.indexOf("clearPrediction:"));
    expect(submit).not.toMatch(/goToStep|nextStep|cursor/);
  });

  it("chạy trọn trace với `challengeOpen` = false, prediction vẫn null", () => {
    for (const e of runnable(true)) {
      useAppStore.getState().reset();
      useAppStore.getState().loadEnvelope(e.envelope as never);
      const st = useAppStore.getState();
      const mod = getSimulation(st.active!.moduleId)!;
      if (!mod.timeline) continue;
      const total = mod.timeline.stepCount(st.active!.state);
      for (let k = 0; k < total + 2; k += 1) useAppStore.getState().nextStep();
      const end = useAppStore.getState();
      expect(mod.timeline.currentStep(end.active!.state), `${e.simId}`).toBe(total - 1);
      expect(end.prediction, `${e.simId}: Quan sát sinh ra phán quyết`).toBeNull();
    }
  });

  it("Đặt lại đưa về Quan sát — Thử thách không dính lại", () => {
    const e = runnable(true)[0];
    useAppStore.getState().loadEnvelope(e.envelope as never);
    useAppStore.getState().setChallengeOpen(true);
    useAppStore.getState().resetSim();
    expect(useAppStore.getState().challengeOpen).toBe(false);
  });
});

/* ══ 4. DẪN XUẤT TỪ NĂNG LỰC, KHÔNG TỪ TÊN BÀI ═══════════════════════════ */

describe("W4B-2U2 · lối vào Thử thách dẫn xuất từ capability", () => {
  it("shell không rẽ nhánh theo tiêu đề/đề bài để quyết định bày Thử thách", () => {
    const src = readFileSync(new URL("../components/SimulationWorkspace.tsx", import.meta.url), "utf-8")
      .replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
    for (const bad of ["title.includes", "summary", "problem.", "description.includes"]) {
      expect(src, `rẽ nhánh theo ngữ cảnh (${bad})`).not.toContain(bad);
    }
    expect(src).toContain("mod.predict");
    // W4B-3A — lối vào Khám phá cũng phải suy từ năng lực, cùng một luật.
    expect(src).toContain("mod.explore");
  });

  it("module KHÔNG khai predict ⇒ không lối vào, không thanh dự đoán", () => {
    const noPredict = offlineCatalog().find((e) => getSimulation(e.simId)?.predict === undefined);
    if (!noPredict) return;
    const mod = getSimulation(noPredict.simId)!;
    expect(challengeEntry(mod, {}, {})).toBeNull();
    expect(challengeSurfaceVisible(mod, {}, true), "mở Thử thách vẫn không được bịa bề mặt")
      .toBe(false);
  });
});
