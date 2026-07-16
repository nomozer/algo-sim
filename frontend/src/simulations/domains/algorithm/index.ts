import type { AlgorithmId, AnalysisData, Condition } from "../../../core/types";
import { ALGORITHM_IDS, ALGORITHM_NAMES } from "../../../core/types";
import { runAlgorithm } from "../../../core/algorithms";
import { registerSimulation } from "../../registry";
import type { ConfigResult, SimAction, SimulationModule } from "../../types";
import { decisionPointOf } from "./decision";
import { activeTrace, clampStep, type AlgorithmConfig, type AlgorithmSimState } from "./model";
import { AlgorithmInspector, AlgorithmWorkspace } from "./ui";
import { makeScanModule } from "./scan-module";

/**
 * Domain "algorithm" — adapter mỏng quanh engine tất định hiện có
 * (core/algorithms.ts + trace-builder.ts). KHÔNG viết lại engine:
 * Trace/Step chính là timeline progressive; module chỉ bọc thành
 * interface SimulationModule chuẩn.
 */

export { activeTrace, type AlgorithmConfig, type AlgorithmSimState } from "./model";
export { makeScanModule, type ScanSimState } from "./scan-module";

const CONDITION_OPS: Condition["op"][] = [">", ">=", "<", "<=", "==", "!="];

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
     * M9-S1 — nhịp DỰ ĐOÁN THEO CƠ CHẾ, một nguồn duy nhất: `decisionPointOf`.
     *
     * Mỗi thuật toán được hỏi ĐÚNG cơ chế của nó (cập nhật max? cộng vào tổng?
     * nửa nào bị loại? có đổi chỗ? có dời không?) tại điểm quyết định thật của
     * trace; đáp án chuẩn và bằng chứng nhân quả DẪN XUẤT từ sự kiện kế tiếp.
     * Cùng nguồn dữ liệu nuôi dải nhân quả trong Workspace → hỏi, chấm và
     * trình bày không bao giờ lệch nhau. KHÔNG LLM, không network.
     */
    predict: {
      challenge: (s) => {
        const d = decisionPointOf(s);
        if (!d) return null;
        return { question: d.question, options: d.options };
      },
      check: (s, answerId) => {
        const d = decisionPointOf(s);
        if (!d) {
          return {
            verdict: "unsupported_to_verify",
            answerId,
            message: "Ở bước này không có điểm quyết định nào để dự đoán.",
          };
        }
        if (!d.options.some((o) => o.id === answerId)) {
          return {
            verdict: "unsupported_to_verify",
            answerId,
            message: "Câu trả lời không hợp lệ.",
          };
        }
        const verdict = answerId === d.expectedId ? "correct" : "incorrect";
        return {
          verdict,
          answerId,
          expectedId: d.expectedId,
          message: (verdict === "correct" ? "Chính xác. " : "Chưa đúng. ") + d.evidence,
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

/** Đăng ký 8 mô phỏng thuật toán + module scan khai báo (M12) vào registry. */
export function registerAlgorithmDomain(): void {
  for (const id of ALGORITHM_IDS) {
    registerSimulation(makeAlgorithmModule(id));
  }
  registerSimulation(makeScanModule());
}
