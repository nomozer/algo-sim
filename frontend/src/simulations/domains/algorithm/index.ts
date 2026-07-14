import type { AlgorithmId, AnalysisData, Condition } from "../../../core/types";
import { ALGORITHM_IDS, ALGORITHM_NAMES } from "../../../core/types";
import { runAlgorithm } from "../../../core/algorithms";
import { registerSimulation } from "../../registry";
import type { ConfigResult, SimAction, SimulationModule } from "../../types";
import { activeTrace, clampStep, type AlgorithmConfig, type AlgorithmSimState } from "./model";
import { AlgorithmInspector, AlgorithmWorkspace } from "./ui";

/**
 * Domain "algorithm" — adapter mỏng quanh engine tất định hiện có
 * (core/algorithms.ts + trace-builder.ts). KHÔNG viết lại engine:
 * Trace/Step chính là timeline progressive; module chỉ bọc thành
 * interface SimulationModule chuẩn.
 */

export { activeTrace, type AlgorithmConfig, type AlgorithmSimState } from "./model";

const CONDITION_OPS: Condition["op"][] = [">", ">=", "<", "<=", "==", "!="];

/* ── M8-PRE-LIP: sinh câu hỏi dự đoán TỪ TRACE THẬT ───────────────────────── */

interface PredictionQuestion {
  question: string;
  /** Sự thật của bước KẾ TIẾP (ground truth lấy từ trace, không suy đoán). */
  actual: boolean;
  /** Mô tả hệ quả đang hỏi (dùng dựng message). */
  effect: string;
  /** Bằng chứng tất định trích từ chính sự kiện của trace. */
  evidence: string;
}

/**
 * Điểm quyết định = bước HIỆN TẠI có phép so sánh và CÒN bước kế tiếp.
 * Ground truth = sự kiện THẬT của bước kế tiếp. Không có điểm quyết định → null
 * (UI sẽ không hiện ô dự đoán — đúng tinh thần "không phán khi không có luật").
 */
function predictionQuestion(s: AlgorithmSimState): PredictionQuestion | null {
  const trace = activeTrace(s);
  const cur = clampStep(s, s.cursor);
  const step = trace.steps[cur];
  const next = trace.steps[cur + 1];
  if (!step || !next) return null;

  const cmp = step.events.find((e) => e.type === "compare" || e.type === "compare_value");
  if (!cmp) return null;

  // Trace CÓ đổi chỗ ở đâu đó → đây là bài sắp xếp → hỏi về đổi chỗ.
  const isSwapping = trace.steps.some((st) => st.events.some((e) => e.type === "swap"));
  if (isSwapping && cmp.type === "compare") {
    const swap = next.events.find((e) => e.type === "swap");
    return {
      question:
        `Engine vừa so sánh phần tử ở vị trí ${cmp.i + 1} và ${cmp.j + 1}. ` +
        `Theo em, hai phần tử này có bị ĐỔI CHỖ ở bước tiếp theo không?`,
      actual: swap !== undefined,
      effect: "đổi chỗ hai phần tử này",
      evidence: swap
        ? `bước sau là một phép đổi chỗ (vị trí ${(swap as { i: number }).i + 1} ↔ ${(swap as { j: number }).j + 1}).`
        : "bước sau không có phép đổi chỗ nào.",
    };
  }

  // Còn lại (tìm max/min, đếm/tổng, tìm kiếm, chèn) → hỏi biến có được cập nhật không.
  const assign = next.events.find((e) => e.type === "assign_var");
  const name = assign ? (assign as { name: string }).name : undefined;
  return {
    question:
      `Engine vừa thực hiện một phép so sánh. ` +
      `Theo em, ở bước tiếp theo có biến nào được CẬP NHẬT không?`,
    actual: assign !== undefined,
    effect: "cập nhật biến",
    evidence: assign
      ? `bước sau gán ${name} = ${String((assign as { value: unknown }).value)}.`
      : "bước sau không gán biến nào — engine đi tiếp mà không đổi giá trị đang theo dõi.",
  };
}

/** Chốt chặn config (phía frontend — tầng validate thứ hai sau backend). */
function validateAlgorithmConfig(
  algorithmId: AlgorithmId,
  raw: unknown,
): ConfigResult<AlgorithmConfig> {
  if (typeof raw !== "object" || raw === null) {
    return { ok: false, error: "Config không phải đối tượng JSON." };
  }
  const r = raw as Record<string, unknown>;
  const data = r.data as Record<string, unknown> | undefined;
  if (!data || !Array.isArray(data.array)) {
    return { ok: false, error: 'Thiếu "data.array".' };
  }
  const array = data.array as unknown[];
  if (array.length < 2 || array.length > 15) {
    return { ok: false, error: `"data.array" phải có 2–15 phần tử (đang có ${array.length}).` };
  }
  if (!array.every((v) => typeof v === "number" && Number.isFinite(v))) {
    return { ok: false, error: '"data.array" phải toàn số hữu hạn.' };
  }
  const nums = array as number[];

  let labels: string[] | null = null;
  if (Array.isArray(data.labels) && data.labels.length > 0) {
    if (data.labels.length !== nums.length || !data.labels.every((l) => typeof l === "string")) {
      return { ok: false, error: '"data.labels" phải là mảng chuỗi khớp độ dài dãy.' };
    }
    labels = data.labels as string[];
  }

  let target: number | null = null;
  if (algorithmId === "linear_search" || algorithmId === "binary_search") {
    if (typeof data.target !== "number" || !Number.isFinite(data.target)) {
      return { ok: false, error: `"${algorithmId}" bắt buộc có "data.target" là số.` };
    }
    target = data.target;
    if (algorithmId === "binary_search" && !nums.every((v, i) => i === 0 || nums[i - 1] <= v)) {
      return { ok: false, error: "binary_search yêu cầu dãy đã sắp tăng dần." };
    }
  }

  let condition: Condition | null = null;
  if (algorithmId === "sum_if" || algorithmId === "count_if") {
    const c = data.condition as Record<string, unknown> | undefined;
    if (!c || !CONDITION_OPS.includes(c.op as Condition["op"]) || typeof c.value !== "number") {
      return { ok: false, error: `"${algorithmId}" bắt buộc có "data.condition" {op, value}.` };
    }
    condition = { op: c.op as Condition["op"], value: c.value };
  }

  let order: "asc" | "desc" | null = null;
  if (algorithmId === "bubble_sort" || algorithmId === "insertion_sort") {
    if (data.order !== "asc" && data.order !== "desc") {
      return { ok: false, error: `"${algorithmId}" bắt buộc có "data.order" asc/desc.` };
    }
    order = data.order;
  }

  const problem = (r.problem ?? {}) as Record<string, unknown>;
  const normalized: AnalysisData = { array: nums, labels, target, condition, order };
  return {
    ok: true,
    config: {
      status: "ok",
      problem: {
        summary: typeof problem.summary === "string" ? problem.summary : ALGORITHM_NAMES[algorithmId],
        input: typeof problem.input === "string" ? problem.input : "Dữ liệu dạng dãy số",
        output: typeof problem.output === "string" ? problem.output : "Kết quả sau khi chạy thuật toán",
      },
      algorithm_id: algorithmId,
      data: normalized,
      data_generated: r.data_generated === true,
      notes: typeof r.notes === "string" ? r.notes : null,
    },
  };
}

export function makeAlgorithmModule(
  algorithmId: AlgorithmId,
): SimulationModule<AlgorithmConfig, AlgorithmSimState> {
  return {
    id: `algorithm.${algorithmId}`,
    domain: "algorithm",
    title: ALGORITHM_NAMES[algorithmId],
    interactionMode: "progressive",
    supportedVisualModes: ["2d"], // "3d" bổ sung ở Milestone 6 (Three.js)

    validateConfig: (raw) => validateAlgorithmConfig(algorithmId, raw),

    // Yêu cầu #1: timeline sinh TẠI ĐÂY (engine tất định), không phải từ LLM
    init: (config) => ({ config, trace: runAlgorithm(config), branch: null, cursor: 0 }),

    apply: (state, action: SimAction) => {
      switch (action.type) {
        case "whatif_swap": {
          if (state.branch) return state; // không nhánh lồng nhánh (R3.3)
          const n = state.config.data.array.length;
          if (state.cursor >= state.trace.steps.length - 1) return state;
          if (action.i === action.j) return state;
          if (action.i < 0 || action.i >= n || action.j < 0 || action.j >= n) return state;
          const branchTrace = runAlgorithm(state.config, {
            afterStep: state.cursor,
            i: action.i,
            j: action.j,
          });
          return {
            ...state,
            branch: { trace: branchTrace, fromStep: state.cursor, i: action.i, j: action.j },
            cursor: state.cursor + 1,
          };
        }
        case "exit_branch":
          return state.branch ? { ...state, branch: null, cursor: state.branch.fromStep } : state;
        default:
          return state; // action không hỗ trợ → no-op
      }
    },

    /**
     * M8-PRE-LIP — nhịp DỰ ĐOÁN, GẮN CHẶT vào trace thật.
     *
     * Trước đây tương tác duy nhất là kéo-thả what-if (đúng nhưng KHÓ THẤY) nên
     * cảm giác "chỉ chạy cho em xem". Nay ở mỗi ĐIỂM QUYẾT ĐỊNH (bước có phép so
     * sánh) hệ hỏi học sinh HỆ QUẢ của phép so sánh đó — rồi so với sự kiện THẬT
     * của bước kế tiếp. KHÔNG bịa hành vi ngoài trace, KHÔNG gọi LLM.
     *
     * Hai kiểu câu hỏi, chọn TẤT ĐỊNH theo bản chất trace (không hard-code tên
     * thuật toán): trace có `swap` → hỏi "có đổi chỗ không?"; còn lại → hỏi
     * "biến theo dõi có được cập nhật không?".
     */
    predict: {
      challenge: (s) => {
        const q = predictionQuestion(s);
        if (!q) return null;
        return {
          question: q.question,
          options: [
            { id: "yes", label: "Có" },
            { id: "no", label: "Không" },
          ],
        };
      },
      check: (s, answerId) => {
        const q = predictionQuestion(s);
        if (!q) {
          return {
            verdict: "unsupported_to_verify",
            answerId,
            message: "Ở bước này không có phép so sánh nào để dự đoán hệ quả.",
          };
        }
        if (answerId !== "yes" && answerId !== "no") {
          return {
            verdict: "unsupported_to_verify",
            answerId,
            message: "Câu trả lời không hợp lệ.",
          };
        }
        const expectedId = q.actual ? "yes" : "no";
        const verdict = answerId === expectedId ? "correct" : "incorrect";
        return {
          verdict,
          answerId,
          expectedId,
          message:
            (verdict === "correct" ? "Chính xác. " : "Chưa đúng. ") +
            `Ở bước tiếp theo, engine ${q.actual ? "CÓ" : "KHÔNG"} ${q.effect} — ${q.evidence}`,
        };
      },
    },

    // Yêu cầu #2: capability timeline — domain này là progressive nên có
    timeline: {
      stepCount: (s) => activeTrace(s).steps.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: clampStep(s, step) }),
    },

    // Yêu cầu #4: snapshot JSON sạch cho /api/explain — trạng thái THẬT của engine
    getExplainContext: (state, config) => {
      const t = activeTrace(state);
      const step = t.steps[clampStep(state, state.cursor)];
      return {
        simulation_id: `algorithm.${config.algorithm_id}`,
        algorithm: ALGORITHM_NAMES[config.algorithm_id],
        problem_summary: config.problem.summary,
        current_step: state.cursor + 1,
        total_steps: t.steps.length,
        narration: step.narration,
        array: step.snapshot.array,
        variables: step.snapshot.vars,
        marks: step.snapshot.marks,
        in_whatif_branch: state.branch !== null,
        ...(state.branch
          ? {
              branch: {
                from_step: state.branch.fromStep + 1,
                swapped_positions: [state.branch.i + 1, state.branch.j + 1],
              },
            }
          : {}),
      };
    },

    // UI adapter — nơi duy nhất biết ArrayView/VarsView/PseudocodeView (M2 #3)
    Workspace: AlgorithmWorkspace,
    Inspector: AlgorithmInspector,
  };
}

/** Đăng ký cả 8 mô phỏng thuật toán vào registry. */
export function registerAlgorithmDomain(): void {
  for (const id of ALGORITHM_IDS) {
    registerSimulation(makeAlgorithmModule(id));
  }
}
