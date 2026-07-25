/**
 * Các kiểu dữ liệu lõi của hệ thống — bám docs/RULES.md.
 * Lớp 2: hợp đồng JSON giữa LLM và hệ thống (AnalysisResult).
 * Lớp 3: định dạng trace chung cho mọi nguồn (Step, TraceEvent).
 */

/* ── Lớp 2 — Kết quả phân tích đề ─────────────────────────── */

export const ALGORITHM_IDS = [
  "find_max",
  "find_min",
  "sum_if",
  "count_if",
  "linear_search",
  "binary_search",
  "bubble_sort",
  "insertion_sort",
  "selection_sort",
] as const;

export type AlgorithmId = (typeof ALGORITHM_IDS)[number];

export const ALGORITHM_NAMES: Record<AlgorithmId, string> = {
  find_max: "Tìm giá trị lớn nhất",
  find_min: "Tìm giá trị nhỏ nhất",
  sum_if: "Tính tổng theo điều kiện",
  count_if: "Đếm theo điều kiện",
  linear_search: "Tìm kiếm tuần tự",
  binary_search: "Tìm kiếm nhị phân",
  bubble_sort: "Sắp xếp nổi bọt",
  insertion_sort: "Sắp xếp chèn",
  selection_sort: "Sắp xếp chọn",
};

export type ConditionOp = ">" | ">=" | "<" | "<=" | "==" | "!=";

export interface Condition {
  op: ConditionOp;
  value: number;
}

export interface AnalysisData {
  array: number[];
  labels: string[] | null;
  target: number | null;
  condition: Condition | null;
  order: "asc" | "desc" | null;
}

export interface AnalysisOk {
  status: "ok";
  problem: {
    summary: string;
    input: string;
    output: string;
  };
  algorithm_id: AlgorithmId;
  data: AnalysisData;
  data_generated: boolean;
  notes: string | null;
}

export interface AnalysisUnsupported {
  status: "unsupported";
  reason: string;
  /** (M17 W0) Thông điệp THÂN THIỆN cho học sinh — server gắn ở biên API;
   * FE ưu tiên hiển thị nó thay cho `reason` kỹ thuật khi có. */
  learner_reason?: string;
  /** (M17-VR1) Loại từ chối — CHỈ để chọn tiêu đề/gợi ý đúng bản chất:
   * "insufficient_specification" = chủ đề CÓ hỗ trợ nhưng đề thiếu dữ kiện
   * (nói "ngoài danh mục" là sai và làm học sinh hiểu nhầm). */
  failure_category?: string;
  /** (M17 W2B-PATCH) Mã lỗi chi tiết — chỉ để chọn tiêu đề/gợi ý khi một
   * `failure_category` gộp nhiều ca cần lời khuyên khác nhau (vd
   * "pipeline_stage_incomplete" vs "multiple_operations_not_supported" đều là
   * `semantic_incomplete`). KHÔNG BAO GIỜ hiển thị mã này cho học sinh. */
  error_code?: string;
}

export type AnalysisResult = AnalysisOk | AnalysisUnsupported;

/* ── Lớp 3 — Trace ─────────────────────────────────────────── */

export type Mark = "considering" | "sorted" | "found" | "eliminated";

export type TraceEvent =
  | { type: "compare"; i: number; j: number; result: "<" | ">" | "==" }
  | {
      type: "compare_value";
      i: number;
      value: number;
      result: "<" | ">" | "==" | "match" | "no_match";
    }
  | { type: "swap"; i: number; j: number }
  | { type: "shift"; from: number; to: number }
  | { type: "insert"; index: number; value: number }
  | { type: "assign_var"; name: string; value: number | string | boolean | null }
  | { type: "set_range"; left: number; right: number }
  | { type: "mark"; index: number; status: Mark }
  /* M17 W2C — luồng điều khiển hữu hạn. Engine phát KẾT QUẢ điều kiện và
   * NHÁNH ĐƯỢC CHỌN thành dữ liệu, để renderer chỉ việc đọc: renderer không
   * bao giờ được tự đánh giá lại biểu thức (bất biến renderer-không-sở-hữu). */
  | { type: "evaluate_condition"; expression: string; result: boolean }
  | { type: "enter_branch"; branch: "then" | "else" | "loop_body" | "loop_exit" }
  | { type: "loop_iteration"; statementId: string; iteration: number }
  | { type: "output"; text: string }
  | { type: "done"; result: string };

export interface Snapshot {
  array: number[];
  /**
   * Định danh bền của phần tử tại từng vị trí (id gốc 0..n-1 đi theo giá trị
   * khi đổi chỗ/dời) — renderer dùng làm key để hoạt cảnh trượt cột.
   */
  ids: number[];
  vars: Record<string, number | string | boolean | null>;
  marks: Record<number, Mark>;
}

export interface Step {
  index: number;
  snapshot: Snapshot;
  events: TraceEvent[];
  /** Thuyết minh sinh từ template tất định — R3.1b, không gọi LLM. */
  narration: string;
  /** Bước quyết định cho nhịp dự đoán — R3.4c. */
  checkpoint?: boolean;
  /** Bước do học sinh can thiệp (kéo thả what-if) — R3.3, không phải của thuật toán. */
  userAction?: boolean;
  /** Dòng mã giả đang thực hiện (1-based, theo PSEUDOCODE của thuật toán). */
  line?: number;
}

export type TraceSource = "engine" | "code_exec" | "llm_script";

export interface Trace {
  source: TraceSource;
  steps: Step[];
}
