import { PseudocodeView } from "../../../components/PseudocodeView";
import { VarsView } from "../../../components/VarsView";
import { IconCheck } from "../../../components/icons";
import {
  programLines,
  runProgram,
  validateProgramSpec,
  type CompletionState,
  type ProgramSpec,
} from "../../../core/program";
import type { Step, Trace } from "../../../core/types";
import type { ConfigResult, SimulationModule, WorkspaceProps } from "../../types";

/**
 * Module `algorithm.bounded_control_flow` (M17 W2C) — adapter MỎNG quanh
 * interpreter tất định `core/program.ts`, cùng khuôn với `algorithm.scan`.
 *
 * Renderer KHÔNG tính lại gì: kết quả điều kiện, nhánh được chọn và số lượt lặp
 * đều đọc từ SỰ KIỆN của bước hiện tại. Đây là điều kiện để 2D là trình bày
 * thuần — nếu renderer tự đánh giá biểu thức thì nó đã sở hữu sự thật.
 *
 * V1 hoãn có chủ đích: prediction (điểm quyết định theo cơ chế cần thiết kế
 * riêng) và what-if — tương tác trang trí không được admit (COVERAGE §2.6).
 */

export interface ProgramSimState {
  spec: ProgramSpec;
  trace: Trace;
  cursor: number;
  completion: CompletionState;
}

function clampCursor(state: ProgramSimState, step: number): number {
  return Math.max(0, Math.min(step, state.trace.steps.length - 1));
}

/** Sự kiện của MỘT bước — renderer chỉ đọc, không suy diễn. */
function readStep(step: Step) {
  let condition: { expression: string; result: boolean } | null = null;
  let branch: string | null = null;
  let iteration: number | null = null;
  let done: string | null = null;
  const changed: string[] = [];

  for (const ev of step.events) {
    if (ev.type === "evaluate_condition") condition = { expression: ev.expression, result: ev.result };
    else if (ev.type === "enter_branch") branch = ev.branch;
    else if (ev.type === "loop_iteration") iteration = ev.iteration;
    else if (ev.type === "assign_var") changed.push(ev.name);
    else if (ev.type === "done") done = ev.result;
  }
  return { condition, branch, iteration, done, changed };
}

const BRANCH_LABEL: Record<string, string> = {
  then: "nhánh THÌ",
  else: "nhánh NGƯỢC LẠI",
  loop_body: "vào thân vòng lặp",
  loop_exit: "thoát vòng lặp",
};

/** Output hiện DẦN theo bước — không bao giờ lộ kết quả cuối ở bước đầu. */
function outputsUpTo(trace: Trace, cursor: number): string[] {
  const out: string[] = [];
  for (let i = 0; i <= cursor && i < trace.steps.length; i += 1) {
    for (const ev of trace.steps[i].events) {
      if (ev.type === "output") out.push(ev.text);
    }
  }
  return out;
}

type Props = WorkspaceProps<ProgramSpec, ProgramSimState>;

export function ProgramWorkspace({ state }: Props) {
  const cursor = clampCursor(state, state.cursor);
  const step = state.trace.steps[cursor];
  const { condition, branch, iteration, done } = readStep(step);
  const outputs = outputsUpTo(state.trace, cursor);
  const last = cursor >= state.trace.steps.length - 1;

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div className="sim-stage">
        <PseudocodeView lines={programLines(state.spec).lines} currentLine={step.line} />
      </div>

      {condition && (
        <div className="stack" style={{ gap: "var(--sp-xs)" }}>
          <div>
            Điều kiện <strong>{condition.expression}</strong> →{" "}
            <strong>{condition.result ? "ĐÚNG" : "SAI"}</strong>
          </div>
          {branch && <div>{`Chạy: ${BRANCH_LABEL[branch] ?? branch}`}</div>}
          {iteration !== null && <div>{`Lượt lặp thứ ${iteration}`}</div>}
        </div>
      )}

      {outputs.length > 0 && (
        <div className="stack" style={{ gap: "var(--sp-xs)" }}>
          <div>Kết quả hiển thị:</div>
          <ul>
            {outputs.map((text, i) => (
              <li key={i}>{text}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="narration-bar">{step.narration}</div>

      {last && done && (
        <div className="result-banner">
          <IconCheck size={15} /> {done}
        </div>
      )}
    </div>
  );
}

export function ProgramInspector({ state }: Props) {
  const cursor = clampCursor(state, state.cursor);
  const step = state.trace.steps[cursor];
  const { changed } = readStep(step);
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <VarsView step={step} />
      {changed.length > 0 && <div>{`Biến vừa đổi: ${changed.join(", ")}`}</div>}
    </div>
  );
}

export function makeProgramModule(): SimulationModule<ProgramSpec, ProgramSimState> {
  return {
    id: "algorithm.bounded_control_flow",
    domain: "algorithm",
    title: "Chạy từng bước đoạn chương trình",
    interactionMode: "progressive",
    supportedVisualModes: ["2d"],

    validateConfig: (raw): ConfigResult<ProgramSpec> => {
      const v = validateProgramSpec(raw);
      return v.ok ? { ok: true, config: v.spec } : { ok: false, error: v.error };
    },

    // Timeline sinh TẠI ĐÂY bởi interpreter tất định — không phải từ LLM (R0).
    init: (spec) => {
      const run = runProgram(spec);
      return { spec, trace: run.trace, cursor: 0, completion: run.completion };
    },

    apply: (state) => state, // v1: không action nào — thao tác qua timeline

    timeline: {
      stepCount: (s) => s.trace.steps.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: clampCursor(s, step) }),
    },

    getExplainContext: (state) => {
      const cursor = clampCursor(state, state.cursor);
      const step = state.trace.steps[cursor];
      const { condition, branch, iteration } = readStep(step);
      return {
        simulation_id: "algorithm.bounded_control_flow",
        pseudocode: programLines(state.spec).lines,
        current_step: cursor + 1,
        total_steps: state.trace.steps.length,
        current_line: step.line ?? null,
        narration: step.narration,
        variables: step.snapshot.vars,
        condition: condition ? `${condition.expression} → ${condition.result}` : null,
        branch,
        loop_iteration: iteration,
        outputs: outputsUpTo(state.trace, cursor),
        completion: state.completion,
      };
    },

    Workspace: ProgramWorkspace,
    Inspector: ProgramInspector,
  };
}
