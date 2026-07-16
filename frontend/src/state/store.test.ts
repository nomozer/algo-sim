import { beforeEach, describe, expect, it } from "vitest";
import { useAppStore } from "./store";
import { __resetHistoryForTest, historyStore } from "./history";
import { clearRegistryForTest, registerSimulation } from "../simulations/registry";
import { registerGenericDomain } from "../simulations/domains/generic";
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

/**
 * M13 Task 7 — regression lock hai phía, nhánh frontend: bản TS của
 * `backend/tests/fixtures/m13_dijkstra_pseudo_algorithm.json` (artifact gốc:
 * đề "mô phỏng thuật toán Dijkstra" bị định tuyến vào generic.rule_scene,
 * render 2 ô weighted_sum lấy input là id CẠNH edge_AB/edge_BC/edge_AC — cạnh
 * không mang giá trị số nên runtime lặng lẽ ra 0, cảnh vẫn chạy đủ 10/10 bước
 * và báo "Hoàn tất!"). Ở đây dùng module generic THẬT (không fake) để khoá
 * đường mở lại từ lịch sử end-to-end: validateConfig (Task 5, cùng thông điệp
 * với validator backend Task 3) phải chặn TRƯỚC init — loadEnvelope không được
 * throw, active phải null, analysisError phải là tiếng Việt, và lịch sử KHÔNG
 * được ghi thêm item (record nằm sau init thành công — cảnh hỏng không được
 * lên sân khấu, cũng không bị ghi lại).
 */
const DIJKSTRA_PSEUDO_CONFIG = {
  dsl_version: "1.0",
  title: "Mô phỏng so sánh đường đi trong thuật toán Dijkstra",
  objects: [
    { id: "node_A", type: "node", label: "node_A" },
    { id: "node_B", type: "node", label: "node_B" },
    { id: "node_C", type: "node", label: "node_C" },
    { id: "edge_AB", type: "edge", label: "edge_AB", from: "node_A", to: "node_B" },
    { id: "edge_BC", type: "edge", label: "edge_BC", from: "node_B", to: "node_C" },
    { id: "edge_AC", type: "edge", label: "edge_AC", from: "node_A", to: "node_C" },
    { id: "runner_ABC", type: "moving_entity", label: "Đường A-B-C" },
    { id: "runner_AC", type: "moving_entity", label: "Đường A-C" },
    { id: "calc_path_ABC", type: "value_box", label: "calc_path_ABC" },
    { id: "calc_path_AC", type: "value_box", label: "calc_path_AC" },
  ],
  rules: [
    { type: "weighted_sum", target: "calc_path_ABC", inputs: ["edge_AB", "edge_BC"], weights: [1, 1] },
    { type: "weighted_sum", target: "calc_path_AC", inputs: ["edge_AC"], weights: [1] },
  ],
  interactions: [] as unknown[],
  processes: [
    { type: "move_along_path", entity: "runner_ABC", path: ["node_A", "node_B", "node_C"] },
    { type: "move_along_path", entity: "runner_AC", path: ["node_A", "node_C"] },
  ],
};

function dijkstraPseudoEnvelope(): SimulationEnvelope {
  return {
    status: "ok",
    simulation_id: "generic.rule_scene",
    domain: "generic",
    visual_mode: "2d",
    title: DIJKSTRA_PSEUDO_CONFIG.title,
    description: null,
    config: DIJKSTRA_PSEUDO_CONFIG,
    notes: null,
  };
}

describe("M13 Task 7: regression lock frontend — mở lại artifact pseudo-Dijkstra từ lịch sử", () => {
  it("loadEnvelope với module generic THẬT → validateConfig chặn trước init, không throw, active null, analysisError tiếng Việt, lịch sử không tăng", () => {
    registerGenericDomain();

    expect(() => useAppStore.getState().loadEnvelope(dijkstraPseudoEnvelope())).not.toThrow();

    const s = useAppStore.getState();
    expect(s.active).toBeNull();
    expect(typeof s.analysisError).toBe("string");
    const err = s.analysisError as string;
    expect(
      err.includes("không còn mở được") || err.includes("không hợp lệ"),
    ).toBe(true);
    // Xác nhận đúng LÝ DO bị chặn (edge không phải nguồn giá trị numeric) —
    // không phải một lỗi ngẫu nhiên khác trùng hợp cũng khiến active null.
    expect(err).toContain("không có nguồn giá trị");
    expect(s.history).toHaveLength(0);
    expect(historyStore.list()).toHaveLength(0);
  });
});
