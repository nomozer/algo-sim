import { fmt } from "../../../core/trace-builder";
import { OP_TEXT } from "../../../core/algorithms";
import type { Step } from "../../../core/types";
import { activeTrace, clampStep, type AlgorithmSimState } from "./model";

/**
 * ĐIỂM QUYẾT ĐỊNH (M9-S1) — trái tim của "tương tác nhắm vào cơ chế ẩn".
 *
 * Một điểm quyết định là bước mà thuật toán SẮP đưa ra quyết định theo cơ chế
 * riêng của nó: cập nhật max? cộng vào tổng? loại nửa nào? có đổi chỗ?
 * `decisionPointOf` sinh ra — cho ĐÚNG bước đó — câu hỏi dự đoán, các lựa chọn,
 * đáp án chuẩn và BẰNG CHỨNG nhân quả. Cả `module.predict` (hỏi–chấm) lẫn dải
 * nhân quả trong Workspace cùng đọc MỘT nguồn này, nên câu hỏi, phản hồi và
 * phần trình bày không bao giờ lệch nhau.
 *
 * RÀNG BUỘC (CORRECTNESS.md §1.6, §4):
 * - Đáp án chuẩn DẪN XUẤT TỪ SỰ KIỆN THẬT của trace (bước kế tiếp / result của
 *   event) — không suy đoán lại thuật toán, không LLM.
 * - Bằng chứng là chuỗi tất định dựng từ số liệu thật (giá trị so sánh, biến
 *   trước → sau) — template cố định, không văn tự do.
 * - Phân nhánh theo `algorithm_id` (định danh NGỮ NGHĨA trong config đã
 *   validate) vì cùng một hình dạng trace có thể mang nghĩa khác nhau;
 *   nhưng SỰ THẬT luôn lấy từ trace, không từ nhãn.
 * - KHÔNG lộ đáp án sớm: narration bước quyết định là câu hỏi (engine đã sửa
 *   theo); phần "chuyện gì xảy ra" thuộc bước kế tiếp + `consequenceOf`.
 */

export interface DecisionOption {
  id: string;
  label: string;
}

export interface DecisionPoint {
  /** Câu hỏi dự đoán — nêu rõ đang xét gì, cơ chế nào. */
  question: string;
  options: DecisionOption[];
  /** Đáp án chuẩn — dẫn xuất từ trace, không đoán. */
  expectedId: string;
  /** Câu nhân quả với số liệu thật — dùng cho phản hồi VÀ dải hệ quả. */
  evidence: string;
  /** Đang xét gì (cho dải nhân quả). */
  consideration: string;
  /** Phép so sánh dạng hỏi, vd "9 > 7,5 ?". */
  expression: string;
}

const YES_NO: DecisionOption[] = [
  { id: "yes", label: "Có" },
  { id: "no", label: "Không" },
];

function steps(state: AlgorithmSimState): { cur: Step; next: Step | undefined } {
  const trace = activeTrace(state);
  const at = clampStep(state, state.cursor);
  return { cur: trace.steps[at], next: trace.steps[at + 1] };
}

function num(v: unknown): number {
  return typeof v === "number" ? v : NaN;
}

/* ── từng cơ chế ──────────────────────────────────────────────────────────── */

function extremeDecision(state: AlgorithmSimState, mode: "max" | "min"): DecisionPoint | null {
  const { cur, next } = steps(state);
  if (!next) return null;
  const cmp = cur.events.find((e) => e.type === "compare");
  if (!cmp || cmp.type !== "compare") return null;

  const vi = cur.snapshot.array[cmp.i];
  const best = num(cur.snapshot.vars[mode]);
  const updates = next.events.some((e) => e.type === "assign_var" && e.name === mode);
  const word = mode === "max" ? "lớn hơn" : "nhỏ hơn";

  return {
    question:
      `${mode} đang là ${fmt(best)}. Xét phần tử ${fmt(vi)} (vị trí ${cmp.i + 1}): ` +
      `${mode} có được cập nhật không?`,
    options: YES_NO,
    expectedId: updates ? "yes" : "no",
    evidence: updates
      ? `${fmt(vi)} ${word} ${fmt(best)} nên ${mode} được cập nhật: ${fmt(best)} → ${fmt(vi)}.`
      : `${fmt(vi)} không ${word} ${fmt(best)} nên ${mode} giữ nguyên ${fmt(best)}.`,
    consideration: `Đang xét ${fmt(vi)} (vị trí ${cmp.i + 1}) — ${mode} hiện tại: ${fmt(best)}`,
    expression: `${fmt(vi)} ${mode === "max" ? ">" : "<"} ${fmt(best)} ?`,
  };
}

function aggregateDecision(state: AlgorithmSimState, mode: "sum" | "count"): DecisionPoint | null {
  const { cur, next } = steps(state);
  if (!next) return null;
  const ev = cur.events.find((e) => e.type === "compare_value");
  if (!ev || ev.type !== "compare_value") return null;
  const cond = state.config.data.condition;
  if (!cond) return null;

  const varName = mode === "sum" ? "tong" : "dem";
  const label = mode === "sum" ? "tổng" : "biến đếm";
  const v = cur.snapshot.array[ev.i];
  const before = num(cur.snapshot.vars[varName]);
  const includes = next.events.some((e) => e.type === "assign_var" && e.name === varName);
  const after = num(next.snapshot.vars[varName]);
  const condText = `${OP_TEXT[cond.op]} ${fmt(cond.value)}`;

  return {
    question:
      mode === "sum"
        ? `Giá trị đang xét là ${fmt(v)}, điều kiện là "${condText}". ${fmt(v)} có được cộng vào tổng không?`
        : `Giá trị đang xét là ${fmt(v)}, điều kiện là "${condText}". Biến đếm có tăng ở bước này không?`,
    options: YES_NO,
    expectedId: includes ? "yes" : "no",
    evidence: includes
      ? mode === "sum"
        ? `${fmt(v)} ${condText} → Đúng, nên ${fmt(v)} được cộng vào tổng: ${fmt(before)} → ${fmt(after)}.`
        : `${fmt(v)} ${condText} → Đúng, nên biến đếm tăng: ${fmt(before)} → ${fmt(after)}.`
      : `${fmt(v)} ${condText} → Sai, nên ${label} giữ nguyên ${fmt(before)}.`,
    consideration: `Đang xét ${fmt(v)} (vị trí ${ev.i + 1}) — ${label}: ${fmt(before)}`,
    expression: `${fmt(v)} ${cond.op} ${fmt(cond.value)} ?`,
  };
}

function linearDecision(state: AlgorithmSimState): DecisionPoint | null {
  const { cur, next } = steps(state);
  if (!next) return null;
  const ev = cur.events.find((e) => e.type === "compare_value");
  if (!ev || ev.type !== "compare_value") return null;
  const target = state.config.data.target;
  if (target === null) return null;

  const v = cur.snapshot.array[ev.i];
  const found = ev.result === "match";

  return {
    question:
      `Đang xét ${fmt(v)} (vị trí ${ev.i + 1}), cần tìm ${fmt(target)}. ` +
      `Ở bước này đã tìm thấy giá trị cần tìm chưa?`,
    options: [
      { id: "yes", label: "Đã tìm thấy" },
      { id: "no", label: "Chưa" },
    ],
    expectedId: found ? "yes" : "no",
    evidence: found
      ? `${fmt(v)} bằng ${fmt(target)} — tìm thấy tại vị trí thứ ${ev.i + 1}.`
      : `${fmt(v)} khác ${fmt(target)} nên chưa tìm thấy — tiếp tục với phần tử kế tiếp.`,
    consideration: `Đang xét ${fmt(v)} (vị trí ${ev.i + 1}) — cần tìm: ${fmt(target)}`,
    expression: `${fmt(v)} = ${fmt(target)} ?`,
  };
}

function binaryDecision(state: AlgorithmSimState): DecisionPoint | null {
  const { cur, next } = steps(state);
  if (!next) return null;
  // Điểm quyết định là bước LẤY MID (narration trung lập) — kết quả so sánh
  // thuộc bước kế tiếp, nên câu hỏi chưa bị lộ.
  const giua = cur.events.find((e) => e.type === "assign_var" && e.name === "giua");
  if (!giua || giua.type !== "assign_var") return null;
  const reveal = next.events.find((e) => e.type === "compare_value");
  if (!reveal || reveal.type !== "compare_value") return null;
  const target = state.config.data.target;
  if (target === null) return null;

  const mid = num(giua.value);
  const midVal = cur.snapshot.array[mid];
  const expectedId =
    reveal.result === "match" ? "found" : reveal.result === "<" ? "left" : "right";

  const evidence =
    reveal.result === "match"
      ? `${fmt(midVal)} bằng ${fmt(target)} — tìm thấy ngay tại vị trí giữa.`
      : reveal.result === "<"
        ? `${fmt(midVal)} < ${fmt(target)} nên giá trị cần tìm (nếu có) nằm bên PHẢI — nửa trái bị loại.`
        : `${fmt(midVal)} > ${fmt(target)} nên giá trị cần tìm (nếu có) nằm bên TRÁI — nửa phải bị loại.`;

  return {
    question:
      `Phần tử giữa vùng xét là ${fmt(midVal)} (vị trí ${mid + 1}); cần tìm ${fmt(target)}. ` +
      `Sau phép so sánh này, phần nào của vùng tìm kiếm sẽ bị loại?`,
    options: [
      { id: "left", label: "Nửa trái" },
      { id: "right", label: "Nửa phải" },
      { id: "found", label: "Đã tìm thấy" },
    ],
    expectedId,
    evidence,
    consideration: `Vùng xét thu về phần tử giữa ${fmt(midVal)} (vị trí ${mid + 1}) — cần tìm: ${fmt(target)}`,
    expression: `${fmt(midVal)} so với ${fmt(target)} ?`,
  };
}

function bubbleDecision(state: AlgorithmSimState): DecisionPoint | null {
  const { cur, next } = steps(state);
  if (!next) return null;
  const cmp = cur.events.find((e) => e.type === "compare");
  if (!cmp || cmp.type !== "compare") return null;

  const vi = cur.snapshot.array[cmp.i];
  const vj = cur.snapshot.array[cmp.j];
  const swaps = next.events.some((e) => e.type === "swap");
  const orderText = (state.config.data.order ?? "asc") === "asc" ? "tăng dần" : "giảm dần";

  return {
    question: `So sánh cặp kề ${fmt(vi)} và ${fmt(vj)} (sắp ${orderText}). Hai phần tử này có đổi chỗ không?`,
    options: YES_NO,
    expectedId: swaps ? "yes" : "no",
    evidence: swaps
      ? `${fmt(vi)} và ${fmt(vj)} đang sai thứ tự ${orderText} nên hai phần tử đổi chỗ.`
      : `${fmt(vi)} rồi ${fmt(vj)} đã đúng thứ tự ${orderText} nên giữ nguyên.`,
    consideration: `Đang xét cặp kề (${fmt(vi)}, ${fmt(vj)}) — vị trí ${cmp.i + 1} và ${cmp.j + 1}`,
    expression: `${fmt(vi)} ${cmp.result} ${fmt(vj)} ?`,
  };
}

function insertionDecision(state: AlgorithmSimState): DecisionPoint | null {
  const { cur, next } = steps(state);
  if (!next) return null;
  const cmp = cur.events.find((e) => e.type === "compare");
  if (!cmp || cmp.type !== "compare") return null;
  const key = num(cur.snapshot.vars["gia_tri_chen"]);
  if (Number.isNaN(key)) return null;

  const vj = cur.snapshot.array[cmp.i];
  const shifts = next.events.some((e) => e.type === "shift");
  const word = (state.config.data.order ?? "asc") === "asc" ? "lớn hơn" : "nhỏ hơn";

  return {
    question:
      `So sánh ${fmt(vj)} với giá trị chèn ${fmt(key)}. ` +
      `Phần tử ${fmt(vj)} có bị dời sang phải một ô không?`,
    options: YES_NO,
    expectedId: shifts ? "yes" : "no",
    evidence: shifts
      ? `${fmt(vj)} ${word} ${fmt(key)} nên ${fmt(vj)} bị dời sang phải một ô.`
      : `${fmt(vj)} không ${word} ${fmt(key)} nên dừng dời — ${fmt(key)} sẽ được chèn ngay sau vị trí này.`,
    consideration: `Đang xét ${fmt(vj)} (vị trí ${cmp.i + 1}) — giá trị chèn: ${fmt(key)}`,
    expression: `${fmt(vj)} ${word} ${fmt(key)} ?`,
  };
}

/* ── API ──────────────────────────────────────────────────────────────────── */

/** Điểm quyết định ở BƯỚC HIỆN TẠI, hoặc null nếu bước này không có gì để hỏi. */
export function decisionPointOf(state: AlgorithmSimState): DecisionPoint | null {
  switch (state.config.algorithm_id) {
    case "find_max":
      return extremeDecision(state, "max");
    case "find_min":
      return extremeDecision(state, "min");
    case "sum_if":
      return aggregateDecision(state, "sum");
    case "count_if":
      return aggregateDecision(state, "count");
    case "linear_search":
      return linearDecision(state);
    case "binary_search":
      return binaryDecision(state);
    case "bubble_sort":
      return bubbleDecision(state);
    case "insertion_sort":
      return insertionDecision(state);
  }
}

/**
 * Câu nhân quả cho BƯỚC HỆ QUẢ (bước ngay sau một điểm quyết định) — cùng chuỗi
 * `evidence` mà phản hồi dự đoán dùng, nên hai bề mặt không bao giờ kể khác nhau.
 */
export function consequenceOf(state: AlgorithmSimState): string | null {
  const at = clampStep(state, state.cursor);
  if (at === 0) return null;
  const prev: AlgorithmSimState = { ...state, cursor: at - 1 };
  return decisionPointOf(prev)?.evidence ?? null;
}
