import { stageSvgSize } from "../../stage-size";
import { PseudocodeView } from "../../../components/PseudocodeView";
import { VarsView, formatVarValue } from "../../../components/VarsView";
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

/* ── SÂN KHẤU VÒNG LẶP (LOOP-VIS) ─────────────────────────────────────────
 *
 * Vì sao có khối này: audit cơ chế chấm target này **B− (trình xem trace)** —
 * sân khấu chỉ có hai dòng mã giả, ba dòng chữ và một chip biến. Học sinh không
 * thấy `x` đã đi qua những giá trị nào, còn cách biên bao xa, vì sao vòng lặp
 * QUAY LẠI, và khi nào dừng. Trace đúng không cứu được điều đó.
 *
 * RÀNG BUỘC GIỮ NGUYÊN — không đụng engine/state/schema:
 * - `loopShape` đọc CẤU TRÚC spec (bảng expressions) để biết biến lặp / phép so
 *   sánh / biên. Đây là đọc CONFIG, không phải tính lại kết quả.
 * - Quỹ đạo giá trị đọc từ `snapshot.vars` của các bước ĐÃ QUA — engine đã ghi.
 * - Pha hiện tại đọc từ SỰ KIỆN của bước hiện tại. Renderer KHÔNG BAO GIỜ tự
 *   đánh giá lại điều kiện: `ĐÚNG/SAI` luôn lấy từ `evaluate_condition.result`.
 * - Spec không phải dạng `while (biến op hằng)` → trả null → sân khấu cũ giữ
 *   nguyên (fail-soft, không vỡ).
 */
interface LoopShape {
  varName: string;
  op: string;
  bound: number;
  maxIterations: number | null;
}

function loopShape(spec: ProgramSpec): LoopShape | null {
  const expr = new Map(spec.expressions.map((e) => [e.id, e]));
  for (const st of spec.statements) {
    if (st.kind !== "while" || !st.condition) continue;
    const cond = expr.get(st.condition);
    if (!cond || cond.kind !== "compare" || !cond.left || !cond.right) continue;
    const left = expr.get(cond.left);
    const right = expr.get(cond.right);
    if (left?.kind !== "var" || !left.name) continue;
    if (right?.kind !== "int" || typeof right.int_value !== "number") continue;
    return {
      varName: left.name,
      op: cond.op ?? "?",
      bound: right.int_value,
      maxIterations: st.max_iterations ?? null,
    };
  }
  return null;
}

/** Bốn pha của một vòng lặp — suy từ SỰ KIỆN của bước, không từ số thứ tự. */
type LoopPhase = "check" | "body" | "update" | "back" | "exit" | null;

function loopPhase(step: Step, prev: Step | null, shape: LoopShape): LoopPhase {
  const { condition, branch, changed } = readStep(step);
  if (branch === "loop_exit") return "exit";
  if (condition && branch === "loop_body") {
    // Vừa quay lại kiểm tra sau một lượt? Bước trước là cập nhật biến lặp.
    const prevChanged = prev ? readStep(prev).changed : [];
    return prevChanged.includes(shape.varName) ? "back" : "check";
  }
  if (condition) return "check";
  if (changed.includes(shape.varName)) return "update";
  if (changed.length > 0) return "body";
  return null;
}

/** Quỹ đạo giá trị biến lặp qua các bước ĐÃ ĐI (bỏ lặp liên tiếp). */
function trajectory(trace: Trace, cursor: number, varName: string): number[] {
  const out: number[] = [];
  for (let i = 0; i <= cursor && i < trace.steps.length; i += 1) {
    const v = trace.steps[i].snapshot.vars[varName];
    if (typeof v !== "number") continue;
    if (out.length === 0 || out[out.length - 1] !== v) out.push(v);
  }
  return out;
}

const PHASE_LABEL: Record<Exclude<LoopPhase, null>, string> = {
  check: "Kiểm tra điều kiện",
  body: "Thực hiện thân",
  update: "Cập nhật biến",
  back: "Quay lại kiểm tra",
  exit: "Thoát vòng lặp",
};

/**
 * Trục giá trị: các giá trị ĐÃ đi qua + biên dừng. Không vẽ mọi số nguyên —
 * chỉ những giá trị engine thật sự đã tạo ra, cộng vạch biên để thấy khoảng
 * cách tới lúc dừng.
 */
function LoopAxis({
  values, current, shape, exited,
}: { values: number[]; current: number | null; shape: LoopShape; exited: boolean }) {
  const marks = [...new Set([...values, shape.bound])].sort((a, b) => a - b);
  if (marks.length === 0) return null;
  const lo = marks[0];
  const hi = marks[marks.length - 1];
  const span = hi - lo || 1;
  const W = 560;
  const PAD = 28;
  const x = (v: number) => PAD + ((v - lo) / span) * (W - 2 * PAD);
  const boundX = x(shape.bound);

  return (
    <svg viewBox={`0 0 ${W} 96`} {...stageSvgSize(W)}
         role="img" aria-label={`Trục giá trị của ${shape.varName}, biên dừng ${shape.bound}`}>
      {/* vùng còn thoả điều kiện (bên trái biên với <=/<) — nền rất nhạt */}
      <rect x={PAD} y={30} width={Math.max(0, boundX - PAD)} height={16}
            fill="var(--canvas-soft)" rx={8} />
      <line x1={PAD} y1={38} x2={W - PAD} y2={38} stroke="var(--hairline)" strokeWidth={2} />

      {/* BIÊN DỪNG — vạch + nhãn chữ, không chỉ bằng màu */}
      <line x1={boundX} y1={20} x2={boundX} y2={56} stroke="var(--accent-orange)" strokeWidth={2.5} />
      <text x={boundX} y={16} textAnchor="middle" fontSize={11} fontWeight={700}
            fill="var(--accent-orange-deep)">biên {shape.bound}</text>

      {marks.map((v) => {
        const isCurrent = current === v;
        const visited = values.includes(v);
        return (
          <g key={v}>
            <circle cx={x(v)} cy={38} r={isCurrent ? 9 : 5}
                    fill={isCurrent ? "var(--primary)" : visited ? "var(--accent-green)" : "var(--surface)"}
                    stroke={isCurrent ? "var(--primary)" : visited ? "var(--accent-green)" : "var(--hairline)"}
                    strokeWidth={2} />
            <text x={x(v)} y={70} textAnchor="middle" fontSize={12}
                  fontWeight={isCurrent ? 700 : 500}
                  fill={isCurrent ? "var(--primary)" : "var(--ink-muted)"}>{v}</text>
          </g>
        );
      })}

      {/* mũi tên bước nhảy gần nhất — "cập nhật" là thứ XẢY RA, không phải câu kể */}
      {values.length >= 2 && (() => {
        const from = values[values.length - 2];
        const to = values[values.length - 1];
        return (
          <path d={`M${x(from)} 26 Q ${(x(from) + x(to)) / 2} 6 ${x(to)} 26`}
                fill="none" stroke="var(--primary)" strokeWidth={2} markerEnd="url(#loop-arrow)" />
        );
      })()}
      <defs>
        <marker id="loop-arrow" markerWidth="8" markerHeight="8" refX="6" refY="3"
                orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L0,6 L7,3 z" fill="var(--primary)" />
        </marker>
      </defs>
      {exited && (
        <text x={W - PAD} y={88} textAnchor="end" fontSize={12} fontWeight={600}
              fill="var(--accent-green-deep)">đã thoát vòng lặp</text>
      )}
    </svg>
  );
}

/** Bốn ô pha + cạnh QUAY LẠI — cái làm vòng lặp *là* vòng lặp. */
function LoopCycle({ phase }: { phase: LoopPhase }) {
  const cells: { id: Exclude<LoopPhase, null>; text: string }[] = [
    { id: "check", text: "Kiểm tra" },
    { id: "body", text: "Thực hiện" },
    { id: "update", text: "Cập nhật" },
  ];
  const activeBack = phase === "back";
  return (
    <div className="loop-cycle">
      {cells.map((c, i) => {
        const active = phase === c.id || (phase === "back" && c.id === "check");
        return (
          <span key={c.id} className={`loop-phase${active ? " is-active" : ""}`}>
            {c.text}
            {i < cells.length - 1 && <span className="loop-arrow" aria-hidden="true">→</span>}
          </span>
        );
      })}
      <span className={`loop-back${activeBack ? " is-active" : ""}`}>
        ↩ quay lại kiểm tra
      </span>
      <span className={`loop-exit${phase === "exit" ? " is-active" : ""}`}>
        ⇥ thoát
      </span>
    </div>
  );
}

function LoopStage({ state, cursor }: { state: ProgramSimState; cursor: number }) {
  const shape = loopShape(state.spec);
  if (!shape) return null;
  const step = state.trace.steps[cursor];
  const prev = cursor > 0 ? state.trace.steps[cursor - 1] : null;
  const { condition, iteration } = readStep(step);
  const phase = loopPhase(step, prev, shape);
  const values = trajectory(state.trace, cursor, shape.varName);
  const cur = step.snapshot.vars[shape.varName];
  const current = typeof cur === "number" ? cur : null;
  const exited = phase === "exit";

  return (
    <div className="loop-stage">
      <div className="loop-head">
        <span className="loop-var">
          {shape.varName} = <strong>{current ?? "—"}</strong>
        </span>
        {iteration !== null && <span className="loop-iter">lượt {iteration}</span>}
        {phase && <span className="loop-now">{PHASE_LABEL[phase]}</span>}
      </div>

      <LoopAxis values={values} current={current} shape={shape} exited={exited} />

      {/* Kết quả điều kiện: CHỮ + màu, lấy thẳng từ sự kiện engine. */}
      {condition && (
        <div className={`loop-cond${condition.result ? " is-true" : " is-false"}`}>
          <span className="loop-cond-expr">{condition.expression}</span>
          <span className="loop-cond-verdict">{condition.result ? "ĐÚNG" : "SAI"}</span>
          <span className="loop-cond-then">
            {condition.result ? "→ vào thân vòng lặp" : "→ dừng, thoát vòng lặp"}
          </span>
        </div>
      )}

      <LoopCycle phase={phase} />

      <p className="stage-legend">
        <span><i className="dot is-current" /> đang xét</span>
        <span><i className="dot is-done" /> đã đi qua</span>
        <span><i className="dot is-bound" /> biên dừng</span>
      </p>
    </div>
  );
}

type Props = WorkspaceProps<ProgramSpec, ProgramSimState>;

export function ProgramWorkspace({ state }: Props) {
  const cursor = clampCursor(state, state.cursor);
  const step = state.trace.steps[cursor];
  const { condition, branch, iteration, done } = readStep(step);
  const outputs = outputsUpTo(state.trace, cursor);
  const last = cursor >= state.trace.steps.length - 1;
  const hasLoop = loopShape(state.spec) !== null;

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      {/* LOOP-VIS: chương trình CÓ vòng lặp thì sân khấu chính là cơ chế lặp;
          mã giả lùi xuống thành phần đối chiếu. Chương trình không có vòng lặp
          giữ nguyên bố cục cũ. */}
      <div className="sim-stage">
        {hasLoop
          ? <LoopStage state={state} cursor={cursor} />
          : <PseudocodeView lines={programLines(state.spec).lines} currentLine={step.line} />}
      </div>

      {hasLoop && (
        <section className="gate-detail">
          <p className="detail-heading">Mã giả</p>
          <PseudocodeView lines={programLines(state.spec).lines} currentLine={step.line} />
        </section>
      )}

      {condition && !hasLoop && (
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

      {/* (SHELL-N) Thuyết minh đã chuyển lên khe của shell — luật ẩn ở bước cuối
          (W2C-VR3) nay sống trong `narrate` bên dưới, cùng một luật, một chỗ. */}

      {last && done && (
        <div className="result-banner">
          <IconCheck size={15} /> {done}
        </div>
      )}
    </div>
  );
}

/**
 * Giá trị các biến NGAY TRƯỚC bước hiện tại — đọc từ dữ liệu có thẩm quyền:
 * snapshot của bước liền trước, hoặc (ở bước đầu) chính `variables` ban đầu của
 * spec đã validate. KHÔNG suy diễn, KHÔNG tự chạy lại gì.
 */
function varsBefore(state: ProgramSimState, cursor: number): Record<string, unknown> {
  if (cursor > 0) return state.trace.steps[cursor - 1].snapshot.vars;
  const initial: Record<string, unknown> = {};
  for (const v of state.spec.variables) {
    initial[v.name] = v.type === "integer" ? v.int_value : v.bool_value;
  }
  return initial;
}

export function ProgramInspector({ state }: Props) {
  const cursor = clampCursor(state, state.cursor);
  const step = state.trace.steps[cursor];
  const { changed } = readStep(step);
  const before = varsBefore(state, cursor);

  // W2C-C1 §L1: biến ĐÃ KHAI BÁO mà CHƯA có giá trị không nằm trong
  // `Snapshot.vars`. Nói thẳng "chưa có giá trị" thay vì im lặng (học sinh cần
  // biết biến tồn tại) và tuyệt đối KHÔNG hiện 0/null như một kết quả tính.
  const notYet = state.spec.variables
    .filter((v) => !(v.name in step.snapshot.vars))
    .map((v) => v.name);

  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <VarsView step={step} />
      {notYet.length > 0 && <div>{`Chưa có giá trị: ${notYet.join(", ")}`}</div>}
      {/* W2C-VR2: thấy được TRƯỚC → SAU. Chương trình một câu lệnh trước đây chỉ
          hiện giá trị sau, nên phép tính không quan sát được — học sinh mở lên
          đã thấy đáp án mà không thấy nó từ đâu ra. */}
      {changed.map((name) => (
        <div key={name}>
          {`${name}: ${formatVarValue(before[name] as never)} → ` +
            `${formatVarValue(step.snapshot.vars[name])}`}
        </div>
      ))}
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

    // (SHELL-N) W2C-VR3: ở bước cuối, thuyết minh TRÙNG y hệt băng kết quả —
    // hiện hai lần cùng một câu làm học sinh tưởng là hai thông tin khác nhau.
    // Trả `null` để shell không dựng khe.
    narrate: (state) => {
      const cursor = clampCursor(state, state.cursor);
      const step = state.trace.steps[cursor];
      const { done } = readStep(step);
      const last = cursor >= state.trace.steps.length - 1;
      if (last && done && step.narration === done) return null;
      return { text: step.narration };
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
