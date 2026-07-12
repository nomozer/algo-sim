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
