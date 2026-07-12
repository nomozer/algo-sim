import { beforeEach, describe, expect, it } from "vitest";
import { SAMPLES } from "../data/samples";
import type { AlgorithmConfig, AlgorithmSimState } from "./domains/algorithm";
import { activeTrace, makeAlgorithmModule, registerAlgorithmDomain } from "./domains/algorithm";
import { fromLegacyAnalysis, toSimulationId } from "./legacy";
import { clearRegistryForTest, getSimulation, listSimulations, registerSimulation } from "./registry";
import type { SimulationModule } from "./types";

/**
 * Test tầng simulation (Milestone 1): registry, mapper legacy,
 * validateConfig, timeline capability, what-if qua apply, explain context.
 * Engine bên dưới đã có test riêng (algorithms.test.ts) — ở đây chỉ test adapter.
 */

beforeEach(() => {
  clearRegistryForTest();
});

describe("registry", () => {
  it("đăng ký đủ 8 mô phỏng domain algorithm", () => {
    registerAlgorithmDomain();
    const metas = listSimulations();
    expect(metas).toHaveLength(8);
    expect(metas.map((m) => m.id)).toContain("algorithm.find_max");
    expect(metas.map((m) => m.id)).toContain("algorithm.bubble_sort");
    expect(metas.every((m) => m.domain === "algorithm")).toBe(true);
    expect(metas.every((m) => m.interactionMode === "progressive")).toBe(true);
    // Yêu cầu #2: progressive khai báo timeline capability
    expect(metas.every((m) => m.hasTimeline)).toBe(true);
  });

  it("từ chối id trùng và id sai định dạng", () => {
    registerAlgorithmDomain();
    expect(() => registerSimulation(makeAlgorithmModule("find_max"))).toThrow(/đã được đăng ký/);
    expect(() =>
      registerSimulation({ ...makeAlgorithmModule("find_min"), id: "SaiDinhDang" }),
    ).toThrow(/dạng/);
  });

  it("getSimulation trả về module đúng id, undefined khi không có", () => {
    registerAlgorithmDomain();
    expect(getSimulation("algorithm.find_max")?.title).toBe("Tìm giá trị lớn nhất");
    expect(getSimulation("logic.and_gate")).toBeUndefined();
  });

  it("mọi module đăng ký phải có Workspace (hợp đồng UI của M2)", () => {
    registerAlgorithmDomain();
    for (const meta of listSimulations()) {
      const mod = getSimulation(meta.id)!;
      expect(mod.Workspace, `module ${meta.id} thiếu Workspace`).toBeDefined();
    }
  });
});

describe("mapper legacy algorithm_id → simulation_id", () => {
  it("toSimulationId thêm tiền tố domain", () => {
    expect(toSimulationId("find_max")).toBe("algorithm.find_max");
    expect(toSimulationId("insertion_sort")).toBe("algorithm.insertion_sort");
  });

  it("fromLegacyAnalysis nâng cả 8 bài mẫu cũ lên envelope hợp lệ", () => {
    registerAlgorithmDomain();
    for (const sample of SAMPLES) {
      const env = fromLegacyAnalysis(sample.analysis);
      expect(env.simulation_id).toBe(`algorithm.${sample.algorithmId}`);
      expect(env.domain).toBe("algorithm");
      const mod = getSimulation(env.simulation_id);
      expect(mod).toBeDefined();
      // config của envelope phải qua được chốt chặn validateConfig của module
      const result = mod!.validateConfig(env.config);
      expect(result.ok).toBe(true);
    }
  });
});

describe("validateConfig (chốt chặn config từ LLM)", () => {
  const mod = makeAlgorithmModule("linear_search");

  it("từ chối mảng quá dài", () => {
    const r = mod.validateConfig({ data: { array: Array.from({ length: 20 }, (_, i) => i), target: 3 } });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toContain("2–15");
  });

  it("từ chối thiếu target với thuật toán tìm kiếm", () => {
    const r = mod.validateConfig({ data: { array: [1, 2, 3] } });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toContain("target");
  });

  it("binary_search từ chối dãy chưa sắp", () => {
    const bin = makeAlgorithmModule("binary_search");
    const r = bin.validateConfig({ data: { array: [9, 4, 7], target: 7 } });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toContain("sắp");
  });

  it("chuẩn hóa config thiếu problem thành giá trị mặc định", () => {
    const r = mod.validateConfig({ data: { array: [5, 2, 8], target: 8 } });
    expect(r.ok).toBe(true);
    if (r.ok) {
      expect(r.config.problem.summary.length).toBeGreaterThan(0);
      expect(r.config.algorithm_id).toBe("linear_search");
    }
  });
});

describe("timeline capability + apply (engine là source of truth)", () => {
  function initFindMax(): {
    mod: SimulationModule<AlgorithmConfig, AlgorithmSimState>;
    state: AlgorithmSimState;
  } {
    const mod = makeAlgorithmModule("find_max");
    const sample = SAMPLES.find((s) => s.algorithmId === "find_max")!;
    return { mod, state: mod.init(sample.analysis) };
  }

  it("init tính sẵn toàn bộ timeline, bắt đầu ở bước 0", () => {
    const { mod, state } = initFindMax();
    expect(mod.timeline).toBeDefined();
    expect(mod.timeline!.stepCount(state)).toBeGreaterThan(2);
    expect(mod.timeline!.currentStep(state)).toBe(0);
  });

  it("goToStep là pure function và tự clamp", () => {
    const { mod, state } = initFindMax();
    const tl = mod.timeline!;
    const s2 = tl.goToStep(state, 3);
    expect(tl.currentStep(s2)).toBe(3);
    expect(tl.currentStep(state)).toBe(0); // state cũ không bị sửa
    expect(tl.currentStep(tl.goToStep(state, 999))).toBe(tl.stepCount(state) - 1);
    expect(tl.currentStep(tl.goToStep(state, -5))).toBe(0);
  });

  it("apply whatif_swap tạo nhánh, exit_branch quay về đúng bước", () => {
    const { mod, state } = initFindMax();
    const tl = mod.timeline!;
    const atStep2 = tl.goToStep(state, 2);
    const branched = mod.apply(atStep2, { type: "whatif_swap", i: 0, j: 4 });
    expect(branched.branch).not.toBeNull();
    expect(tl.currentStep(branched)).toBe(3); // đứng tại bước can thiệp
    expect(activeTrace(branched).steps[3].userAction).toBe(true);
    // nhánh không được sửa dòng chính
    expect(branched.trace).toBe(state.trace);

    const back = mod.apply(branched, { type: "exit_branch" });
    expect(back.branch).toBeNull();
    expect(tl.currentStep(back)).toBe(2);
  });

  it("apply chặn what-if không hợp lệ (i=j, ngoài mảng, nhánh lồng nhánh)", () => {
    const { mod, state } = initFindMax();
    expect(mod.apply(state, { type: "whatif_swap", i: 1, j: 1 })).toBe(state);
    expect(mod.apply(state, { type: "whatif_swap", i: 0, j: 99 })).toBe(state);
    const branched = mod.apply(state, { type: "whatif_swap", i: 0, j: 1 });
    expect(mod.apply(branched, { type: "whatif_swap", i: 2, j: 3 })).toBe(branched);
  });

  it("action không hỗ trợ là no-op, không ném lỗi", () => {
    const { mod, state } = initFindMax();
    expect(mod.apply(state, { type: "toggle", target: "x" })).toBe(state);
  });
});

describe("getExplainContext (yêu cầu #4)", () => {
  it("trả JSON sạch, serializable, phản ánh đúng trạng thái engine", () => {
    const mod = makeAlgorithmModule("bubble_sort");
    const sample = SAMPLES.find((s) => s.algorithmId === "bubble_sort")!;
    let state = mod.init(sample.analysis);
    state = mod.timeline!.goToStep(state, 5);

    const ctx = mod.getExplainContext(state, sample.analysis);
    // Serializable — không hàm, không object lạ (Zustand/React/Three.js)
    const roundTrip = JSON.parse(JSON.stringify(ctx));
    expect(roundTrip).toEqual(ctx);

    expect(ctx.simulation_id).toBe("algorithm.bubble_sort");
    expect(ctx.current_step).toBe(6);
    expect(ctx.total_steps).toBe(state.trace.steps.length);
    expect(ctx.narration).toBe(state.trace.steps[5].narration);
    expect(Array.isArray(ctx.array)).toBe(true);
    expect(ctx.in_whatif_branch).toBe(false);
  });
});
