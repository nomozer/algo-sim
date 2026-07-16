import { beforeEach, describe, expect, it } from "vitest";
import { useAppStore } from "./store";
import { __resetHistoryForTest, historyStore } from "./history";
import { clearRegistryForTest, registerSimulation } from "../simulations/registry";
import type { SimulationEnvelope, SimulationModule } from "../simulations/types";

/**
 * M13 Task 6 — store phải FAIL-CLOSED khi `module.init()` ném lỗi. Sự cố gốc:
 * cảnh "Dijkstra" giả qua được validateConfig (Task 3/5 hai tầng) nhưng
 * runtime phát hiện không evaluate được (Task 6 evalRule/valuesOf) — TRƯỚC
 * đây init không được bọc nên lỗi này sẽ crash cả app. Store MÙ DOMAIN: khoá
 * hành vi "bắt Error bất kỳ", KHÔNG import GenericExecutionError ở đây — nếu
 * import thì test không còn khoá được tính domain-blind của store nữa.
 */

function fakeThrowingModule(id: string): SimulationModule<unknown, unknown> {
  return {
    id,
    domain: "generic",
    title: "Fake module (init ném lỗi)",
    interactionMode: "exploratory",
    supportedVisualModes: ["2d"],
    validateConfig: (raw) => ({ ok: true, config: raw }),
    init: () => {
      throw new Error("boom: runtime không evaluate được");
    },
    apply: (s) => s,
    getExplainContext: () => ({}),
    Workspace: () => null,
  };
}

function fakeOkModule(id: string): SimulationModule<unknown, unknown> {
  return {
    id,
    domain: "generic",
    title: "Fake module (init OK)",
    interactionMode: "exploratory",
    supportedVisualModes: ["2d"],
    validateConfig: (raw) => ({ ok: true, config: raw }),
    init: (config) => ({ config }),
    apply: (s) => s,
    getExplainContext: () => ({}),
    Workspace: () => null,
  };
}

function envelope(id: string): SimulationEnvelope {
  return {
    status: "ok",
    simulation_id: id,
    domain: "generic",
    visual_mode: "2d",
    title: "Cảnh hỏng",
    description: null,
    config: {},
    notes: null,
  };
}

beforeEach(() => {
  __resetHistoryForTest();
  clearRegistryForTest();
  useAppStore.getState().reset();
});

describe("M13: loadEnvelope fail-closed khi module.init() ném lỗi", () => {
  it("init ném lỗi → analysisError thân thiện, active===null, không crash, không ghi lịch sử", () => {
    registerSimulation(fakeThrowingModule("generic.rule_scene"));

    expect(() => useAppStore.getState().loadEnvelope(envelope("generic.rule_scene"))).not.toThrow();

    const s = useAppStore.getState();
    expect(s.active).toBeNull();
    expect(s.analysisError).toContain("Mô phỏng này không còn mở được");
    // envelope hỏng KHÔNG được ghi vào lịch sử (record phải nằm SAU init thành công).
    expect(s.history).toHaveLength(0);
    expect(historyStore.list()).toHaveLength(0);
  });

  it("init OK vẫn hoạt động bình thường: active có state, lịch sử được ghi (không phá đường hạnh phúc)", () => {
    registerSimulation(fakeOkModule("generic.rule_scene"));

    useAppStore.getState().loadEnvelope(envelope("generic.rule_scene"));

    const s = useAppStore.getState();
    expect(s.active).not.toBeNull();
    expect(s.analysisError).toBeNull();
    expect(s.history).toHaveLength(1);
  });
});
