import { registerSimulation } from "../../registry";
import type { BinaryConfig, BinaryState } from "./model";
import { binaryString, bitsOf, decimalOf, placeValues } from "./model";
import type { ConfigResult, SimAction, SimulationModule } from "../../types";
import { BinaryInspector, BinaryWorkspace } from "./ui";

/**
 * binary.decimal_to_binary — mô phỏng KHÁM PHÁ (exploratory): không timeline.
 * Các bit và giá trị thập phân do engine tính, KHÔNG đến từ LLM (M5 §6).
 */

function validateBinaryConfig(raw: unknown): ConfigResult<BinaryConfig> {
  if (typeof raw !== "object" || raw === null) {
    return { ok: false, error: "Config không phải đối tượng JSON." };
  }
  const r = raw as Record<string, unknown>;
  const dec = r.decimalValue;
  if (typeof dec !== "number" || !Number.isInteger(dec) || dec < 0 || dec > 255) {
    return { ok: false, error: '"decimalValue" phải là số nguyên từ 0 đến 255.' };
  }
  const rawWidth = r.bitWidth;
  if (typeof rawWidth !== "number" || !Number.isInteger(rawWidth) || rawWidth < 1 || rawWidth > 8) {
    return { ok: false, error: '"bitWidth" phải là số nguyên từ 1 đến 8.' };
  }
  const needed = Math.max(1, dec === 0 ? 1 : Math.floor(Math.log2(dec)) + 1);
  const width = Math.max(rawWidth, needed);
  return {
    ok: true,
    config: { decimalValue: dec, bitWidth: width, notes: typeof r.notes === "string" ? r.notes : null },
  };
}

export function makeBinaryModule(): SimulationModule<BinaryConfig, BinaryState> {
  return {
    id: "binary.decimal_to_binary",
    domain: "binary",
    title: "Đổi thập phân sang nhị phân",
    interactionMode: "exploratory",
    supportedVisualModes: ["2d"],

    validateConfig: validateBinaryConfig,

    init: (config) => ({
      bits: bitsOf(config.decimalValue, config.bitWidth),
      bitWidth: config.bitWidth,
    }),

    apply: (state, action: SimAction) => {
      if (action.type === "toggle") {
        const idx = Number(action.target);
        if (Number.isInteger(idx) && idx >= 0 && idx < state.bits.length) {
          const bits = [...state.bits];
          bits[idx] = bits[idx] === 1 ? 0 : 1;
          return { ...state, bits };
        }
      }
      if (action.type === "set_param" && action.name === "decimal" && typeof action.value === "number") {
        const v = Math.max(0, Math.min(255, Math.floor(action.value)));
        const max = 2 ** state.bitWidth - 1;
        if (v <= max) return { ...state, bits: bitsOf(v, state.bitWidth) };
      }
      return state;
    },

    // KHÔNG có timeline (M5 §2)

    getExplainContext: (state) => ({
      simulation_id: "binary.decimal_to_binary",
      decimal_value: decimalOf(state),
      binary: binaryString(state),
      bit_width: state.bitWidth,
      place_values: placeValues(state.bitWidth),
      active_bits: placeValues(state.bitWidth).filter((_, i) => state.bits[i] === 1),
    }),

    Workspace: BinaryWorkspace,
    Inspector: BinaryInspector,
  };
}

export function registerBinaryDomain(): void {
  registerSimulation(makeBinaryModule());
}
