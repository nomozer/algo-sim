import { registerSimulation } from "../../registry";
import type { Bit, LogicConfig, LogicState } from "./model";
import { AND_RULE, andOutput } from "./model";
import type { ConfigResult, SimAction, SimulationModule } from "../../types";
import { LogicInspector, LogicWorkspace } from "./ui";

/**
 * logic.and_gate — mô phỏng KHÁM PHÁ (exploratory): không timeline.
 * Output do engine tính (andOutput), KHÔNG đến từ LLM (M5 §6).
 */

function asBit(v: unknown): Bit | null {
  if (v === 1 || v === true) return 1;
  if (v === 0 || v === false) return 0;
  return null;
}

function validateLogicConfig(raw: unknown): ConfigResult<LogicConfig> {
  if (typeof raw !== "object" || raw === null) {
    return { ok: false, error: "Config không phải đối tượng JSON." };
  }
  const r = raw as Record<string, unknown>;
  const a = asBit(r.inputA);
  const b = asBit(r.inputB);
  if (a === null || b === null) {
    return { ok: false, error: '"inputA" và "inputB" phải là 0 hoặc 1.' };
  }
  return {
    ok: true,
    config: { inputA: a, inputB: b, notes: typeof r.notes === "string" ? r.notes : null },
  };
}

export function makeAndGateModule(): SimulationModule<LogicConfig, LogicState> {
  return {
    id: "logic.and_gate",
    domain: "logic",
    title: "Cổng logic AND",
    interactionMode: "exploratory",
    supportedVisualModes: ["2d"],
    applications: [
      "Cửa an toàn chỉ mở khi CÓ thẻ VÀ đúng mã PIN",
      "Đèn báo lỗi sáng khi cả hai cảm biến cùng kích hoạt",
    ],

    validateConfig: validateLogicConfig,

    init: (config) => ({ inputA: config.inputA, inputB: config.inputB }),

    apply: (state, action: SimAction) => {
      if (action.type === "toggle") {
        if (action.target === "A") return { ...state, inputA: state.inputA === 1 ? 0 : 1 };
        if (action.target === "B") return { ...state, inputB: state.inputB === 1 ? 0 : 1 };
      }
      return state; // exploratory: không hỗ trợ action khác → no-op
    },

    // KHÔNG có timeline (M5 §2) — Controls chỉ hiện Reset

    getExplainContext: (state) => ({
      simulation_id: "logic.and_gate",
      inputA: state.inputA,
      inputB: state.inputB,
      output: andOutput(state),
      rule: AND_RULE,
    }),

    Workspace: LogicWorkspace,
    Inspector: LogicInspector,
  };
}

export function registerLogicDomain(): void {
  registerSimulation(makeAndGateModule());
}
