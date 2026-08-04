import { registerSimulation } from "../../registry";
import type { ConfigResult, SimAction, SimulationModule, WorkspaceProps } from "../../types";
import type { Bit } from "./model";

/**
 * logic.boolean_dag (M17 W1) — mạch logic NHIỀU cổng {AND, OR, NOT, XOR} nối
 * thành DAG bounded + BẢNG CHÂN TRỊ do engine sinh.
 *
 * Executor tất định sở hữu: thứ tự đánh giá topo, output từng cổng, bảng chân
 * trị đủ 2^n hàng, kết quả cuối. LLM chỉ khai cấu trúc mạch (inputs/gates/
 * output) — không bao giờ sinh giá trị/bảng (R0). Hybrid: timeline theo bước
 * đánh giá + toggle đầu vào (engine đánh giá lại tất định).
 */

export const DAG_OPS = ["AND", "OR", "NOT", "XOR"] as const;
export type DagOp = (typeof DAG_OPS)[number];
export const DAG_MAX_INPUTS = 4;
export const DAG_MAX_GATES = 8;

export interface DagInput {
  id: string;
  label: string | null;
  value: Bit;
}

export interface DagGate {
  id: string;
  op: DagOp;
  inputs: string[]; // id của input hoặc cổng khác (DAG — không cycle)
}

export interface BoolDagConfig {
  inputs: DagInput[];
  gates: DagGate[];
  /** Cổng đầu ra KHAI BÁO RÕ. */
  output: string;
  notes: string | null;
}

export type DagStep =
  | { kind: "intro"; narration: string }
  | {
      kind: "eval";
      gateId: string;
      op: DagOp;
      inputValues: Bit[];
      output: Bit;
      narration: string;
    }
  | { kind: "result"; output: Bit; narration: string };

export interface TruthRow {
  assignment: Record<string, Bit>;
  finalOutput: Bit;
}

export interface BoolDagState {
  readonly config: BoolDagConfig;
  /** Gán trị đầu vào HIỆN TẠI (state-owned — toggle sửa ở đây). */
  values: Record<string, Bit>;
  /** Thứ tự đánh giá topo — engine tính. */
  evalOrder: string[];
  /** Output từng node cho gán trị hiện tại — engine tính. */
  nodeOutputs: Record<string, Bit>;
  steps: DagStep[];
  /** Bảng chân trị đủ 2^n hàng — engine tính (authoritative). */
  truthTable: TruthRow[];
  cursor: number;
}

function applyOp(op: DagOp, vals: Bit[]): Bit {
  switch (op) {
    case "AND":
      return vals.every((v) => v === 1) ? 1 : 0;
    case "OR":
      return vals.some((v) => v === 1) ? 1 : 0;
    case "XOR":
      return vals[0] !== vals[1] ? 1 : 0;
    case "NOT":
      return vals[0] === 1 ? 0 : 1;
  }
}

/** Thứ tự topo của các cổng — trả null nếu có CYCLE (validator dùng chung). */
export function topoOrder(config: Pick<BoolDagConfig, "inputs" | "gates">): string[] | null {
  const inputIds = new Set(config.inputs.map((i) => i.id));
  const gateById = new Map(config.gates.map((g) => [g.id, g]));
  const order: string[] = [];
  const done = new Set<string>();
  const visiting = new Set<string>();

  function visit(id: string): boolean {
    if (inputIds.has(id) || done.has(id)) return true;
    if (visiting.has(id)) return false; // cycle
    const gate = gateById.get(id);
    if (!gate) return false; // ref không tồn tại (validator đã chặn)
    visiting.add(id);
    for (const ref of gate.inputs) if (!visit(ref)) return false;
    visiting.delete(id);
    done.add(id);
    order.push(id);
    return true;
  }

  for (const g of config.gates) if (!visit(g.id)) return null;
  return order;
}

/** Đánh giá mạch cho MỘT gán trị — engine tất định (test oracle đối chiếu). */
export function evaluateDag(
  config: BoolDagConfig,
  values: Record<string, Bit>,
  evalOrder: string[],
): Record<string, Bit> {
  const out: Record<string, Bit> = { ...values };
  const gateById = new Map(config.gates.map((g) => [g.id, g]));
  for (const id of evalOrder) {
    const gate = gateById.get(id)!;
    out[id] = applyOp(gate.op, gate.inputs.map((r) => out[r]));
  }
  return out;
}

function buildTruthTable(config: BoolDagConfig, evalOrder: string[]): TruthRow[] {
  const n = config.inputs.length;
  const rows: TruthRow[] = [];
  for (let mask = 0; mask < 2 ** n; mask++) {
    const assignment: Record<string, Bit> = {};
    config.inputs.forEach((inp, i) => {
      assignment[inp.id] = ((mask >> (n - 1 - i)) & 1) as Bit;
    });
    const outputs = evaluateDag(config, assignment, evalOrder);
    rows.push({ assignment, finalOutput: outputs[config.output] });
  }
  return rows;
}

function buildSteps(
  config: BoolDagConfig,
  evalOrder: string[],
  nodeOutputs: Record<string, Bit>,
): DagStep[] {
  const steps: DagStep[] = [
    {
      kind: "intro",
      narration:
        `Mạch có ${config.inputs.length} đầu vào và ${config.gates.length} cổng — ` +
        `đánh giá lần lượt theo thứ tự phụ thuộc (topo).`,
    },
  ];
  const gateById = new Map(config.gates.map((g) => [g.id, g]));
  for (const id of evalOrder) {
    const gate = gateById.get(id)!;
    const inputValues = gate.inputs.map((r) => nodeOutputs[r]);
    steps.push({
      kind: "eval",
      gateId: id,
      op: gate.op,
      inputValues,
      output: nodeOutputs[id],
      narration:
        `Cổng ${id} (${gate.op}) nhận [${inputValues.join(", ")}] → ra ${nodeOutputs[id]}.`,
    });
  }
  steps.push({
    kind: "result",
    output: nodeOutputs[config.output],
    narration: `Đầu ra của mạch (cổng ${config.output}): ${nodeOutputs[config.output]}.`,
  });
  return steps;
}

/* ── validator (tầng FE) ─────────────────────────────────────── */

export function validateBoolDagConfig(raw: unknown): ConfigResult<BoolDagConfig> {
  if (typeof raw !== "object" || raw === null) {
    return { ok: false, error: "Config không phải đối tượng JSON." };
  }
  const r = raw as Record<string, unknown>;
  if (!Array.isArray(r.inputs) || r.inputs.length < 1 || r.inputs.length > DAG_MAX_INPUTS) {
    return { ok: false, error: `"inputs" phải có 1–${DAG_MAX_INPUTS} đầu vào.` };
  }
  if (!Array.isArray(r.gates) || r.gates.length < 1 || r.gates.length > DAG_MAX_GATES) {
    return { ok: false, error: `"gates" phải có 1–${DAG_MAX_GATES} cổng.` };
  }
  const inputs: DagInput[] = [];
  const ids = new Set<string>();
  for (const it of r.inputs) {
    const o = it as Record<string, unknown>;
    if (typeof o.id !== "string" || !o.id) return { ok: false, error: "Đầu vào thiếu id." };
    if (ids.has(o.id)) return { ok: false, error: `Id trùng: ${o.id}.` };
    ids.add(o.id);
    const v = o.value === 1 ? 1 : o.value === 0 ? 0 : null;
    if (v === null) return { ok: false, error: `Đầu vào ${o.id}: "value" phải là 0 hoặc 1.` };
    inputs.push({ id: o.id, label: typeof o.label === "string" ? o.label : null, value: v });
  }
  const gates: DagGate[] = [];
  for (const it of r.gates) {
    const o = it as Record<string, unknown>;
    if (typeof o.id !== "string" || !o.id) return { ok: false, error: "Cổng thiếu id." };
    if (ids.has(o.id)) return { ok: false, error: `Id trùng: ${o.id}.` };
    ids.add(o.id);
    if (!DAG_OPS.includes(o.op as DagOp)) {
      return { ok: false, error: `Cổng ${o.id}: "op" phải thuộc {AND, OR, NOT, XOR}.` };
    }
    if (!Array.isArray(o.inputs) || !o.inputs.every((x) => typeof x === "string")) {
      return { ok: false, error: `Cổng ${o.id}: "inputs" phải là mảng id.` };
    }
    const need = o.op === "NOT" ? 1 : 2;
    if (o.inputs.length !== need) {
      return { ok: false, error: `Cổng ${o.id} (${String(o.op)}) cần đúng ${need} đầu vào.` };
    }
    gates.push({ id: o.id, op: o.op as DagOp, inputs: o.inputs as string[] });
  }
  for (const g of gates) {
    for (const ref of g.inputs) {
      if (!ids.has(ref)) return { ok: false, error: `Cổng ${g.id} tham chiếu id không tồn tại: ${ref}.` };
      if (ref === g.id) return { ok: false, error: `Cổng ${g.id} tự tham chiếu (cycle).` };
    }
  }
  if (typeof r.output !== "string" || !gates.some((g) => g.id === r.output)) {
    return { ok: false, error: '"output" phải là id của MỘT cổng trong mạch.' };
  }
  const config: BoolDagConfig = {
    inputs,
    gates,
    output: r.output,
    notes: typeof r.notes === "string" ? r.notes : null,
  };
  const order = topoOrder(config);
  if (order === null) {
    return { ok: false, error: "Mạch chứa CYCLE — phải là DAG (không vòng)." };
  }
  // mọi cổng phải góp vào output (không cổng rác lơ lửng)
  const used = new Set<string>([config.output]);
  for (const id of [...order].reverse()) {
    if (!used.has(id)) continue;
    for (const ref of gates.find((g) => g.id === id)!.inputs) used.add(ref);
  }
  const dangling = gates.filter((g) => !used.has(g.id)).map((g) => g.id);
  if (dangling.length > 0) {
    return { ok: false, error: `Cổng không góp vào đầu ra: ${dangling.join(", ")}.` };
  }
  return { ok: true, config };
}

/* ── UI ─────────────────────────────────────────────────────── */

function clampCursor(state: BoolDagState, step: number): number {
  return Math.max(0, Math.min(step, state.steps.length - 1));
}

type Props = WorkspaceProps<BoolDagConfig, BoolDagState>;

export function BoolDagWorkspace({ state, dispatch, busy }: Props) {
  const at = clampCursor(state, state.cursor);
  const evaluated = new Set(
    state.steps.slice(0, at + 1).filter((s) => s.kind === "eval").map((s) => (s as { gateId: string }).gateId),
  );

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div className="sim-stage">
        <div className="stack" style={{ gap: "var(--sp-sm)" }}>
          <div>
            {state.config.inputs.map((inp) => (
              <button
                key={inp.id}
                type="button"
                className="btn-utility"
                disabled={busy}
                onClick={() => dispatch({ type: "toggle", target: inp.id })}
              >
                {inp.label ?? inp.id}: {state.values[inp.id]}
              </button>
            ))}
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Cổng</th>
                <th>Phép</th>
                <th>Vào</th>
                <th>Ra</th>
              </tr>
            </thead>
            <tbody>
              {state.evalOrder.map((id) => {
                const gate = state.config.gates.find((g) => g.id === id)!;
                const done = evaluated.has(id);
                return (
                  <tr key={id}>
                    <td>{id}{state.config.output === id ? " (đầu ra)" : ""}</td>
                    <td>{gate.op}</td>
                    <td>{gate.inputs.join(", ")}</td>
                    <td>{done ? state.nodeOutputs[id] : "?"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      {/* (SHELL-N) Thuyết minh đã rời `.notes` (lớp dành cho ghi chú phụ) để về
          khe chung của shell — xem `narrate` bên dưới. */}
    </div>
  );
}

export function BoolDagInspector({ state }: Props) {
  // HÉ LỘ DẦN (DESIGN_BRIEF §3.3): cột "Ra" của bảng chân trị chứa sẵn đáp án
  // của MỌI tổ hợp — kể cả tổ hợp đang chạy. In nó từ bước 0 thì sân khấu giấu
  // đầu ra bằng "?" cũng vô nghĩa. Mở ở BƯỚC CUỐI, dùng lại đúng idiom "?" của
  // bảng cổng. Dẫn xuất thuần từ cursor — không thêm state trình bày.
  const at = clampCursor(state, state.cursor);
  const revealed = at === state.steps.length - 1;
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <p className="notes">Bảng chân trị (engine sinh đủ {state.truthTable.length} hàng):</p>
      {!revealed && (
        <p className="notes">Cột “Ra” mở ở bước cuối — em thử tự suy luận trước.</p>
      )}
      <table className="data-table">
        <thead>
          <tr>
            {state.config.inputs.map((i) => (
              <th key={i.id}>{i.label ?? i.id}</th>
            ))}
            <th>Ra</th>
          </tr>
        </thead>
        <tbody>
          {state.truthTable.map((row, i) => (
            <tr key={i}>
              {state.config.inputs.map((inp) => (
                <td key={inp.id}>{row.assignment[inp.id]}</td>
              ))}
              <td>{revealed ? row.finalOutput : "?"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ── module ─────────────────────────────────────────────────── */

function initFromValues(config: BoolDagConfig, values: Record<string, Bit>): BoolDagState {
  const evalOrder = topoOrder(config)!; // validator đã chặn cycle
  const nodeOutputs = evaluateDag(config, values, evalOrder);
  return {
    config,
    values,
    evalOrder,
    nodeOutputs,
    steps: buildSteps(config, evalOrder, nodeOutputs),
    truthTable: buildTruthTable(config, evalOrder),
    cursor: 0,
  };
}

export function makeBoolDagModule(): SimulationModule<BoolDagConfig, BoolDagState> {
  return {
    id: "logic.boolean_dag",
    domain: "logic",
    title: "Mạch logic nhiều cổng (AND · OR · NOT · XOR)",
    interactionMode: "hybrid",
    supportedVisualModes: ["2d"],

    validateConfig: validateBoolDagConfig,

    init: (config) =>
      initFromValues(
        config,
        Object.fromEntries(config.inputs.map((i) => [i.id, i.value])) as Record<string, Bit>,
      ),

    apply: (state, action: SimAction) => {
      if (action.type === "toggle" && typeof action.target === "string") {
        if (state.config.inputs.some((i) => i.id === action.target)) {
          const values = {
            ...state.values,
            [action.target]: (state.values[action.target] === 1 ? 0 : 1) as Bit,
          };
          return initFromValues(state.config, values);
        }
      }
      return state;
    },

    timeline: {
      stepCount: (s) => s.steps.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: clampCursor(s, step) }),
    },

    // (SHELL-N) chữ thuyết minh; khe do shell dựng
    narrate: (state) => ({ text: state.steps[clampCursor(state, state.cursor)].narration }),

    getExplainContext: (state) => {
      const at = clampCursor(state, state.cursor);
      return {
        simulation_id: "logic.boolean_dag",
        inputs: state.config.inputs.map((i) => ({ id: i.id, value: state.values[i.id] })),
        gates: state.config.gates,
        output_gate: state.config.output,
        eval_order: state.evalOrder,
        node_outputs: state.nodeOutputs,
        final_output: state.nodeOutputs[state.config.output],
        truth_table_rows: state.truthTable.length,
        current_step: at + 1,
        total_steps: state.steps.length,
        narration: state.steps[at].narration,
      };
    },

    Workspace: BoolDagWorkspace,
    Inspector: BoolDagInspector,
  };
}

export function registerBoolDagModule(): void {
  registerSimulation(makeBoolDagModule());
}
