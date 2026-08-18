import type { AlgorithmId, AnalysisData, Condition } from "../../../core/types";
import { ALGORITHM_IDS, ALGORITHM_NAMES } from "../../../core/types";
import { runAlgorithm } from "../../../core/algorithms";
import { registerSimulation } from "../../registry";
import type { ConfigResult, SimAction, SimulationModule } from "../../types";
import {
  hasStageInteraction,
  narrationWithoutPrompt,
  processLeadOf,
} from "./decision";
import { hasCondition, withConditionParam } from "./condition-param";
import { exploreEntryOf, whatIfPolicyOf } from "./interaction-policy";
import { activeTrace, clampStep, type AlgorithmConfig, type AlgorithmSimState } from "./model";
import { AlgorithmInspector, AlgorithmWorkspace } from "./ui";
import { makeScanModule } from "./scan-module";
import { makeProgramModule } from "./program-module";

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
  if (
    algorithmId === "bubble_sort" ||
    algorithmId === "insertion_sort" ||
    algorithmId === "selection_sort"
  ) {
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
        /* W4B-4D — ĐỔI ĐIỀU KIỆN rồi để engine chạy lại từ đầu.
           Khác `whatif_swap` ở chỗ đây KHÔNG đẻ nhánh: đổi điều kiện là đổi
           chính bài toán, nên không có "dòng chính" nào để quay về. Con trỏ về
           0 vì trace cũ nói về một câu hỏi khác. */
        case "set_param": {
          const next = withConditionParam(state.config, action.name, action.value);
          if (!next) return state;
          return { config: next, trace: runAlgorithm(next), branch: null, cursor: 0 };
        }
        case "exit_branch":
          return state.branch ? { ...state, branch: null, cursor: state.branch.fromStep } : state;
        default:
          return state; // action không hỗ trợ → no-op
      }
    },

    /* W13 — KHỐI `predict` ĐÃ GỠ.
     *
     * Từ M9-S1 tới W12, mỗi thuật toán được HỎI đúng cơ chế của nó tại điểm
     * quyết định (`decisionPointOf`), rồi engine chấm đúng/sai. Nay bỏ: đây là
     * hệ mô phỏng tương tác, học sinh tác động lên mô hình và đọc hệ quả tất
     * định, chứ không trả lời câu hỏi để lấy phán quyết.
     *
     * `decisionPointOf` KHÔNG mất — nó vẫn là nguồn duy nhất của dải dữ kiện cơ
     * chế trên sân khấu (`title` / `facts` / `expression`). Thứ bị gỡ là
     * `options` / `expectedId` / `evidence` — tức phần đáp án.
     */

    /* W4B-3A — KHÁM PHÁ: đổi mô hình rồi để `apply` tính lại. Không đi qua
       `predict.check`, nên không có đúng/sai nào được phát ngôn ở đây. */
    explore: {
      entry: (s, config) =>
        exploreEntryOf(whatIfPolicyOf((config as AlgorithmConfig).algorithm_id), {
          /* Hết bài thì không còn gì để chạy tiếp trên nhánh — mời kéo lúc đó là
             mời một thao tác không sinh hệ quả nào.
             W4B-4D: bài có ĐIỀU KIỆN thì mở được ở MỌI bước — đổi ngưỡng chạy
             lại cả bài từ đầu chứ không rẽ nhánh từ con trỏ, nên "đã tới bước
             cuối" không phải lý do đóng cửa. */
          canManipulate: hasCondition(config as AlgorithmConfig)
            || s.cursor < activeTrace(s).steps.length - 1,
        }),
    },

    // Yêu cầu #2: capability timeline — domain này là progressive nên có
    timeline: {
      stepCount: (s) => activeTrace(s).steps.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: clampStep(s, step) }),
    },

    // (SHELL-N) Chữ thuyết minh; khe do shell dựng. `userAction` = câu nói về
    // thao tác what-if của HỌC SINH, không phải bước canonical.
    narrate: (state) => {
      const t = activeTrace(state);
      const step = t.steps[clampStep(state, state.cursor)];

      /* W3B §5.2 — DỮ KIỆN QUYẾT ĐỊNH CHỈ THUỘC MỘT CHỖ.
       *
       * Ở bước có vùng hành động, vùng đó đã sở hữu ứng viên, phép so sánh và
       * biến tích luỹ. Khe thuyết minh kể lại đúng ba thứ ấy ("So sánh vị trí 3
       * (giá trị 2) với max = 9." ngay trên "Phần tử vị trí 3 · 2 · 2 > 9 ? ·
       * max 9") nên cùng một dữ kiện hiện hai lần trên một màn hình.
       *
       * Trả `null` chứ không trả chuỗi rỗng: shell KHÔNG dựng khe khi null
       * (`NarrationSlot`), còn chuỗi rỗng để lại một khe trắng vô nghĩa.
       * `step.narration` của engine không đổi một ký tự — `getExplainContext`
       * vẫn gửi đi chuỗi gốc.
       *
       * Bước THAO TÁC CỦA HỌC SINH (what-if) luôn giữ lời kể: nó nói về việc em
       * vừa làm, không phải dữ kiện canonical mà vùng hành động đang mang.
       */
      if (!step.userAction && hasStageInteraction(state)) return null;

      /* W4B-2T — CÙNG MỘT LUẬT, ÁP CHO BƯỚC CUỐI: KẾT QUẢ CHỈ THUỘC MỘT CHỖ.
       *
       * Đo được ở cả 8 target thuật toán (`measure-composition.mjs`): ở bước
       * cuối, dải kết quả và khe thuyết minh nói ĐÚNG một câu — bốn bài trùng
       * từng ký tự, bốn bài chỉ khác tiền tố "Duyệt hết dãy.". Học sinh đọc hai
       * lần cùng một điều ngay tại khoảnh khắc đáng nhớ nhất của bài.
       *
       * `.result-banner` là chủ sở hữu: nó có biểu tượng, có tông kết thúc, và
       * còn chở thêm dãy gốc khi đang ở nhánh what-if. Nên khe thuyết minh nhả
       * phần KẾT QUẢ ra và chỉ giữ phần TIẾN TRÌNH ("Duyệt hết dãy.") — thứ mà
       * dải kết quả không nói. Không còn gì để nói thì trả `null`, y như luật
       * vùng hành động ở trên (shell không dựng khe rỗng).
       *
       * Engine KHÔNG đổi: `step.narration` nguyên vẹn, `getExplainContext` vẫn
       * gửi chuỗi gốc. Đây là cắt ở tầng trình bày.
       */
      const text = narrationWithoutPrompt(step.narration);
      const done = step.events.find((e) => e.type === "done");
      if (done && done.type === "done" && !step.userAction) {
        const lead = processLeadOf(text, done.result);
        return lead === null ? null : { text: lead, fromLearner: false };
      }

      // W1: khe thuyết minh MÔ TẢ bước đang diễn ra; việc HỎI là của
      // PredictionBar. Chỉ cắt ở tầng trình bày — `step.narration` không đổi.
      return {
        text,
        fromLearner: Boolean(step.userAction),
      };
    },

    // Yêu cầu #4: snapshot JSON sạch cho /api/explain — trạng thái THẬT của engine
    /* W4B-4D — chỉ `count_if`/`sum_if` đổi được config (qua điều kiện), nhưng
       khai chung cả họ là đúng: hàm trả `state.config`, và ở bài không đổi được
       thì nó luôn bằng bản gốc nên không nhãn nào hiện. Khai theo từng bài sẽ
       là một danh sách phải nhớ cập nhật. */
    currentConfig: (state) => state.config,

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
  registerSimulation(makeProgramModule());
}
