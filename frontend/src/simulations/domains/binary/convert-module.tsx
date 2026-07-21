import { registerSimulation } from "../../registry";
import type { ConfigResult, SimulationModule, WorkspaceProps } from "../../types";

/**
 * binary.base_conversion (M17 W1) — đổi cơ số TỔNG QUÁT giữa {2, 8, 10, 16}.
 *
 * Executor tất định sở hữu TOÀN BỘ: trace chia-lấy-dư (10 → X), trace trọng
 * số vị trí (X → 10), và đường HAI GIAI ĐOẠN tường minh X → 10 → Y khi cả
 * hai cơ số đều ≠ 10 (digit-grouping 2↔8/16 là biến thể tương lai, KHÔNG
 * trong W1). LLM chỉ điền source_base/target_base/input_value — không bao
 * giờ sinh kết quả/steps (R0). Progressive: timeline do engine dựng sẵn.
 */

export const CONV_BASES = [2, 8, 10, 16] as const;
export type ConvBase = (typeof CONV_BASES)[number];
export type ConvStrategy = "quotient_remainder" | "positional_weights" | "two_stage";

export interface BaseConvConfig {
  sourceBase: ConvBase;
  targetBase: ConvBase;
  /** Chuỗi chữ số CANONICAL theo source base (hoa, không số 0 thừa đầu). */
  inputValue: string;
  strategy: ConvStrategy;
  notes: string | null;
}

export type ConvStep =
  | { kind: "intro"; narration: string }
  | {
      kind: "weight";
      digit: string;
      digitValue: number;
      position: number; // số mũ của trọng số
      weight: number;
      product: number;
      runningSum: number;
      narration: string;
    }
  | {
      kind: "divide";
      value: number;
      base: number;
      quotient: number;
      remainder: number;
      digit: string;
      narration: string;
    }
  | { kind: "stage"; stage: 1 | 2; narration: string }
  | { kind: "result"; output: string; narration: string };

export interface BaseConvState {
  readonly config: BaseConvConfig;
  /** Giá trị thập phân trung gian — engine tính, không từ LLM. */
  decimalValue: number;
  steps: ConvStep[];
  /** Kết quả CANONICAL theo target base — engine tính (authoritative). */
  result: string;
  cursor: number;
}

const DIGITS = "0123456789ABCDEF";
export const CONV_MAX_VALUE = 65535; // bound 16 bit — bounded capability

export function digitsValid(value: string, base: ConvBase): boolean {
  if (value.length === 0 || value.length > 16) return false;
  const allowed = DIGITS.slice(0, base);
  return [...value.toUpperCase()].every((ch) => allowed.includes(ch));
}

/** Chuẩn hóa canonical: chữ HOA, bỏ số 0 thừa đầu (giữ "0" đơn). */
export function canonicalDigits(value: string): string {
  const up = value.toUpperCase().replace(/^0+(?=.)/, "");
  return up;
}

export function parseInBase(value: string, base: ConvBase): number {
  return [...value].reduce((acc, ch) => acc * base + DIGITS.indexOf(ch), 0);
}

export function toBase(value: number, base: ConvBase): string {
  if (value === 0) return "0";
  let v = value;
  let out = "";
  while (v > 0) {
    out = DIGITS[v % base] + out;
    v = Math.floor(v / base);
  }
  return out;
}

export function strategyOf(source: ConvBase, target: ConvBase): ConvStrategy {
  if (source === 10) return "quotient_remainder";
  if (target === 10) return "positional_weights";
  return "two_stage";
}

const BASE_NAME: Record<ConvBase, string> = {
  2: "nhị phân",
  8: "bát phân",
  10: "thập phân",
  16: "thập lục phân",
};

/* ── engine tất định ─────────────────────────────────────────── */

function weightSteps(digits: string, base: ConvBase, steps: ConvStep[]): number {
  let sum = 0;
  const n = digits.length;
  for (let i = 0; i < n; i++) {
    const digit = digits[i];
    const digitValue = DIGITS.indexOf(digit);
    const position = n - 1 - i;
    const weight = base ** position;
    const product = digitValue * weight;
    sum += product;
    steps.push({
      kind: "weight",
      digit,
      digitValue,
      position,
      weight,
      product,
      runningSum: sum,
      narration:
        `Chữ số ${digit} (giá trị ${digitValue}) ở vị trí trọng số ${base}^${position} = ${weight}: ` +
        `cộng ${digitValue} × ${weight} = ${product}. Tổng dồn: ${sum}.`,
    });
  }
  return sum;
}

function divideSteps(value: number, base: ConvBase, steps: ConvStep[]): string {
  if (value === 0) {
    steps.push({
      kind: "divide",
      value: 0,
      base,
      quotient: 0,
      remainder: 0,
      digit: "0",
      narration: `0 chia ${base} được 0 dư 0 — chữ số duy nhất là 0.`,
    });
    return "0";
  }
  let v = value;
  let out = "";
  while (v > 0) {
    const quotient = Math.floor(v / base);
    const remainder = v % base;
    const digit = DIGITS[remainder];
    out = digit + out;
    steps.push({
      kind: "divide",
      value: v,
      base,
      quotient,
      remainder,
      digit,
      narration:
        `${v} : ${base} = ${quotient} dư ${remainder} → chữ số ${digit}. ` +
        `Các số dư đọc NGƯỢC từ dưới lên sẽ thành kết quả.`,
    });
    v = quotient;
  }
  return out;
}

export function buildConvSteps(config: BaseConvConfig): {
  decimalValue: number;
  steps: ConvStep[];
  result: string;
} {
  const { sourceBase, targetBase, inputValue } = config;
  const steps: ConvStep[] = [];
  steps.push({
    kind: "intro",
    narration:
      `Đổi ${inputValue} từ hệ ${BASE_NAME[sourceBase]} (cơ số ${sourceBase}) ` +
      `sang hệ ${BASE_NAME[targetBase]} (cơ số ${targetBase}).`,
  });

  let decimalValue: number;
  let result: string;

  if (sourceBase === 10) {
    decimalValue = parseInBase(inputValue, 10);
    result = divideSteps(decimalValue, targetBase, steps);
  } else if (targetBase === 10) {
    steps.push({
      kind: "stage",
      stage: 1,
      narration: `Tính giá trị theo TRỌNG SỐ VỊ TRÍ của hệ cơ số ${sourceBase}.`,
    });
    decimalValue = weightSteps(inputValue, sourceBase, steps);
    result = String(decimalValue);
  } else {
    steps.push({
      kind: "stage",
      stage: 1,
      narration:
        `Giai đoạn 1: đổi ${inputValue} (cơ số ${sourceBase}) về thập phân bằng trọng số vị trí.`,
    });
    decimalValue = weightSteps(inputValue, sourceBase, steps);
    steps.push({
      kind: "stage",
      stage: 2,
      narration:
        `Giai đoạn 2: đổi ${decimalValue} (thập phân) sang cơ số ${targetBase} bằng chia lấy dư.`,
    });
    result = divideSteps(decimalValue, targetBase, steps);
  }

  steps.push({
    kind: "result",
    output: result,
    narration: `Kết quả: ${inputValue} (cơ số ${sourceBase}) = ${result} (cơ số ${targetBase}).`,
  });
  return { decimalValue, steps, result };
}

/* ── validator (tầng FE — tầng validate thứ hai sau backend) ── */

export function validateBaseConvConfig(raw: unknown): ConfigResult<BaseConvConfig> {
  if (typeof raw !== "object" || raw === null) {
    return { ok: false, error: "Config không phải đối tượng JSON." };
  }
  const r = raw as Record<string, unknown>;
  const src = r.sourceBase;
  const tgt = r.targetBase;
  if (!CONV_BASES.includes(src as ConvBase) || !CONV_BASES.includes(tgt as ConvBase)) {
    return { ok: false, error: '"sourceBase"/"targetBase" phải thuộc {2, 8, 10, 16}.' };
  }
  if (src === tgt) {
    return { ok: false, error: "sourceBase phải KHÁC targetBase." };
  }
  if (typeof r.inputValue !== "string" || !digitsValid(r.inputValue, src as ConvBase)) {
    return {
      ok: false,
      error: `"inputValue" phải là chuỗi chữ số hợp lệ của cơ số ${String(src)} (tối đa 16 ký tự).`,
    };
  }
  const canonical = canonicalDigits(r.inputValue);
  const value = parseInBase(canonical, src as ConvBase);
  if (value > CONV_MAX_VALUE) {
    return { ok: false, error: `Giá trị vượt giới hạn ${CONV_MAX_VALUE} — nằm ngoài phạm vi mô phỏng.` };
  }
  const derived = strategyOf(src as ConvBase, tgt as ConvBase);
  if (r.strategy !== undefined && r.strategy !== null && r.strategy !== derived) {
    return {
      ok: false,
      error: `"strategy" (nếu có) phải là "${derived}" — dẫn xuất tất định từ cặp cơ số.`,
    };
  }
  return {
    ok: true,
    config: {
      sourceBase: src as ConvBase,
      targetBase: tgt as ConvBase,
      inputValue: canonical,
      strategy: derived,
      notes: typeof r.notes === "string" ? r.notes : null,
    },
  };
}

/* ── UI (renderer đọc state — không business logic) ─────────── */

function clampCursor(state: BaseConvState, step: number): number {
  return Math.max(0, Math.min(step, state.steps.length - 1));
}

type Props = WorkspaceProps<BaseConvConfig, BaseConvState>;

export function BaseConvWorkspace({ state }: Props) {
  const at = clampCursor(state, state.cursor);
  const visible = state.steps.slice(0, at + 1);
  const current = state.steps[at];
  const divides = visible.filter((s): s is Extract<ConvStep, { kind: "divide" }> => s.kind === "divide");
  const weights = visible.filter((s): s is Extract<ConvStep, { kind: "weight" }> => s.kind === "weight");
  const resultStep = visible.find((s): s is Extract<ConvStep, { kind: "result" }> => s.kind === "result");
  const collected = divides.map((d) => d.digit).reverse().join("");

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div className="sim-stage">
        {weights.length > 0 && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Chữ số</th>
                <th>Trọng số</th>
                <th>Tích</th>
                <th>Tổng dồn</th>
              </tr>
            </thead>
            <tbody>
              {weights.map((w, i) => (
                <tr key={i}>
                  <td>{w.digit}</td>
                  <td>
                    {state.config.sourceBase}^{w.position} = {w.weight}
                  </td>
                  <td>{w.product}</td>
                  <td>{w.runningSum}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {divides.length > 0 && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Phép chia</th>
                <th>Thương</th>
                <th>Dư</th>
                <th>Chữ số</th>
              </tr>
            </thead>
            <tbody>
              {divides.map((d, i) => (
                <tr key={i}>
                  <td>
                    {d.value} : {d.base}
                  </td>
                  <td>{d.quotient}</td>
                  <td>{d.remainder}</td>
                  <td>{d.digit}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {collected && !resultStep && (
          <p className="notes">Chữ số đã thu (đọc ngược số dư): {collected}</p>
        )}
        {resultStep && (
          <p>
            <strong>
              {state.config.inputValue} (cơ số {state.config.sourceBase}) = {resultStep.output} (cơ số{" "}
              {state.config.targetBase})
            </strong>
          </p>
        )}
      </div>
      <p className="notes">{current.narration}</p>
    </div>
  );
}

export function BaseConvInspector({ state }: Props) {
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <p className="notes">
        Cơ số nguồn: {state.config.sourceBase} · Cơ số đích: {state.config.targetBase}
      </p>
      <p className="notes">Giá trị vào: {state.config.inputValue}</p>
      <p className="notes">Giá trị thập phân trung gian: {state.decimalValue}</p>
      <p className="notes">
        Chiến lược:{" "}
        {state.config.strategy === "quotient_remainder"
          ? "chia lấy dư"
          : state.config.strategy === "positional_weights"
            ? "trọng số vị trí"
            : "hai giai đoạn (về thập phân rồi chia lấy dư)"}
      </p>
    </div>
  );
}

/* ── module ─────────────────────────────────────────────────── */

export function makeBaseConvModule(): SimulationModule<BaseConvConfig, BaseConvState> {
  return {
    id: "binary.base_conversion",
    domain: "binary",
    title: "Đổi cơ số (2 · 8 · 10 · 16)",
    interactionMode: "progressive",
    supportedVisualModes: ["2d"],

    validateConfig: validateBaseConvConfig,

    // Timeline sinh TẠI ĐÂY — engine tất định, không từ LLM (R0)
    init: (config) => {
      const { decimalValue, steps, result } = buildConvSteps(config);
      return { config, decimalValue, steps, result, cursor: 0 };
    },

    apply: (state) => state, // không what-if trong v1 (có chủ đích)

    timeline: {
      stepCount: (s) => s.steps.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: clampCursor(s, step) }),
    },

    getExplainContext: (state) => {
      const at = clampCursor(state, state.cursor);
      return {
        simulation_id: "binary.base_conversion",
        source_base: state.config.sourceBase,
        target_base: state.config.targetBase,
        input_value: state.config.inputValue,
        strategy: state.config.strategy,
        decimal_value: state.decimalValue,
        result: state.result,
        current_step: at + 1,
        total_steps: state.steps.length,
        narration: state.steps[at].narration,
      };
    },

    Workspace: BaseConvWorkspace,
    Inspector: BaseConvInspector,
  };
}

export function registerBaseConvModule(): void {
  registerSimulation(makeBaseConvModule());
}
