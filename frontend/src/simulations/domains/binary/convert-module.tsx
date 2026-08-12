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

/**
 * Cơ chế đổi cơ số THUẦN sống ở `./base-conversion` (M17 P1a) để
 * `binary.character_encoding` dùng lại được CHÍNH cơ chế chia lấy dư, không chỉ
 * dùng lại `toBase()`. Re-export để mọi import cũ (`./convert-module`) giữ
 * nguyên — KHÔNG có bản sao thứ hai của phép đổi cơ số.
 */
export {
  BASE_NAME,
  CONV_BASES,
  CONV_MAX_VALUE,
  buildConvSteps,
  canonicalDigits,
  digitsValid,
  divideSteps,
  parseInBase,
  strategyOf,
  toBase,
  weightSteps,
} from "./base-conversion";
export type {
  BaseConvConfig,
  ConvBase,
  ConvStep,
  ConvStrategy,
  DivideStep,
} from "./base-conversion";

import {
  CONV_BASES,
  CONV_MAX_VALUE,
  buildConvSteps,
  canonicalDigits,
  digitsValid,
  parseInBase,
  strategyOf,
} from "./base-conversion";
import type { BaseConvConfig, ConvBase, ConvStep } from "./base-conversion";


export interface BaseConvState {
  readonly config: BaseConvConfig;
  /** Giá trị thập phân trung gian — engine tính, không từ LLM. */
  decimalValue: number;
  steps: ConvStep[];
  /** Kết quả CANONICAL theo target base — engine tính (authoritative). */
  result: string;
  cursor: number;
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

/** W4B-4C — giá trị, cơ số nguồn, cơ số đích: đổi cái nào cũng tính lại ngay. */
function ConvParamBar({ state, busy, dispatch }: Props) {
  const bases = CONV_BASES;
  return (
    <div className="param-bar" role="group" aria-label="Chọn giá trị và cơ số">
      <label>
        Giá trị
        <input value={state.config.inputValue} disabled={busy} aria-label="Giá trị cần đổi"
          onChange={(e) => dispatch({ type: "set_param", name: "inputValue", value: e.target.value })} />
      </label>
      <label>
        Từ cơ số
        <select value={state.config.sourceBase} disabled={busy}
          onChange={(e) => dispatch({ type: "set_param", name: "sourceBase", value: Number(e.target.value) })}>
          {bases.map((b) => <option key={b} value={b}>{b}</option>)}
        </select>
      </label>
      <label>
        Sang cơ số
        <select value={state.config.targetBase} disabled={busy}
          onChange={(e) => dispatch({ type: "set_param", name: "targetBase", value: Number(e.target.value) })}>
          {bases.map((b) => <option key={b} value={b}>{b}</option>)}
        </select>
      </label>
    </div>
  );
}

export function BaseConvWorkspace({ state, config, busy, dispatch }: Props) {
  const at = clampCursor(state, state.cursor);
  const visible = state.steps.slice(0, at + 1);
  const current = state.steps[at];
  const divides = visible.filter((s): s is Extract<ConvStep, { kind: "divide" }> => s.kind === "divide");
  const weights = visible.filter((s): s is Extract<ConvStep, { kind: "weight" }> => s.kind === "weight");
  const resultStep = visible.find((s): s is Extract<ConvStep, { kind: "result" }> => s.kind === "result");
  const collected = divides.map((d) => d.digit).reverse().join("");

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <ConvParamBar state={state} config={config} busy={busy} dispatch={dispatch} />
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
  /* W4B-3D — PANEL PHẢI ĐỌC BƯỚC HIỆN TẠI.
     Bản trước chỉ in cấu hình, nên "Giải thích" hiện y hệt nhau ở bước 1 và
     bước cuối: học sinh bấm Tiến, sân khấu đổi, panel đứng im. Lỗi này chỉ lộ
     ra khi target có mẫu offline đầu tiên (W4B-3D) — trước đó không lượt audit
     toàn-danh-mục nào chạm tới nó. */
  const step = state.steps[Math.min(state.cursor, state.steps.length - 1)];
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <p className="notes">
        Bước {state.cursor + 1} / {state.steps.length}
        {step ? ` — ${step.narration}` : ""}
      </p>
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

/**
 * W4B-4C — THAM SỐ ĐỔI CƠ SỐ TRONG MIỀN ĐÓNG. `null` = ngoài miền ⇒ giữ state.
 *
 * Ba tham số, đúng ba thứ bài học nói tới: giá trị, cơ số nguồn, cơ số đích.
 * Không ô nhập tự do nào khác, không biểu thức, không cơ số ngoài bảng.
 *
 * Đổi CƠ SỐ NGUỒN là ca tinh tế: chuỗi chữ số cũ có thể không còn hợp lệ (vd
 * "1F" ở hệ 16 chuyển sang hệ 2). Từ chối thẳng thay vì cắt bớt chữ số — cắt là
 * lặng lẽ đổi bài toán của học sinh thành một bài khác.
 */
export function withConversionParam(
  config: BaseConvConfig,
  name: string,
  value: number | string | boolean,
): BaseConvConfig | null {
  const asBase = (v: number | string | boolean): ConvBase | null => {
    const n = Number(v);
    return (CONV_BASES as readonly number[]).includes(n) ? (n as ConvBase) : null;
  };

  if (name === "sourceBase") {
    const base = asBase(value);
    if (base === null || base === config.sourceBase) return null;
    if (!digitsValid(config.inputValue, base)) return null;
    return { ...config, sourceBase: base, strategy: strategyOf(base, config.targetBase) };
  }
  if (name === "targetBase") {
    const base = asBase(value);
    if (base === null || base === config.targetBase) return null;
    return { ...config, targetBase: base, strategy: strategyOf(config.sourceBase, base) };
  }
  if (name === "inputValue") {
    if (typeof value !== "string") return null;
    const digits = canonicalDigits(value.trim());
    if (!digitsValid(digits, config.sourceBase)) return null;
    if (parseInBase(digits, config.sourceBase) > CONV_MAX_VALUE) return null;
    return { ...config, inputValue: digits };
  }
  return null;
}

export function makeBaseConvModule(): SimulationModule<BaseConvConfig, BaseConvState> {
  return {
    id: "binary.base_conversion",
    domain: "binary",
    title: "Đổi cơ số (2 · 8 · 10 · 16)",
    /* W4B-4C — `progressive` → `hybrid`: nay có CẢ dòng thời gian giải thích
       LẪN tham số học sinh đổi được bất cứ lúc nào trên sân khấu. */
    interactionMode: "hybrid",
    supportedVisualModes: ["2d"],

    validateConfig: validateBaseConvConfig,


    // Timeline sinh TẠI ĐÂY — engine tất định, không từ LLM (R0)
    init: (config) => {
      const { decimalValue, steps, result } = buildConvSteps(config);
      return { config, decimalValue, steps, result, cursor: 0 };
    },

    /* W4B-4C — ĐỔI CƠ SỐ LÀ THỨ HỌC SINH THỬ, KHÔNG PHẢI THỨ HỌC SINH XEM.
     *
     * `apply` từng là identity, nên bài đổi cơ số chỉ còn bấm Tiến qua các bước
     * chia lấy dư của MỘT phép đổi cố định. Nhưng cơ chế ở đây là QUAN HỆ giữa
     * giá trị, cơ số nguồn và cơ số đích — và quan hệ đó chỉ hiện ra khi đổi
     * được một trong ba rồi thấy hai cái kia phản ứng.
     *
     * `buildConvSteps(config)` đã là chủ sở hữu tất định và `init` vốn chỉ gọi
     * nó, nên tương tác không cần engine mới: sửa config trong MIỀN ĐÓNG rồi
     * dựng lại bằng chính hàm ấy.
     *
     * Miền đóng: cơ số ∈ `CONV_BASES` · chữ số phải HỢP LỆ trong cơ số nguồn ·
     * giá trị ≤ `CONV_MAX_VALUE`. Sai ⇒ trả nguyên state (fail-closed), không
     * kẹp, không đoán — cùng luật với validator.
     */
    apply: (state, action) => {
      if (action.type !== "set_param") return state;
      const next = withConversionParam(state.config, action.name, action.value);
      if (!next) return state;
      const { decimalValue, steps, result } = buildConvSteps(next);
      return { config: next, decimalValue, steps, result, cursor: 0 };
    },

    timeline: {
      stepCount: (s) => s.steps.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: clampCursor(s, step) }),
    },

    /* W4B-4D — mô hình chạy config NÀO ngay lúc này; shell so với bản đã
       validate để nói ra khi học sinh đã kéo mô hình rời khỏi đề bài. */
    currentConfig: (state) => state.config,

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
