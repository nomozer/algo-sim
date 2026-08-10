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

/**
 * BA LOẠI THÔNG TIN, MỖI LOẠI ĐÚNG MỘT CHỖ (UI-CLARITY W1).
 *
 * `consideration` = STATE LINE — dữ liệu hiện tại, hiện ở dải nhân quả.
 * `question`      = PROMPT — CHỈ hỏi, hiện ở PredictionBar.
 * `evidence`      = FEEDBACK — chỉ giải thích sau khi chọn.
 *
 * Trước W1, `question` nhắc lại nguyên state line ("max đang là 7,5. Xét phần
 * tử 9 (vị trí 2): …") nên chuỗi "(vị trí 2)" hiện HAI lần cùng lúc trên màn
 * hình (đo được: 2 → 1). Đừng nhét lại trạng thái vào `question`.
 */
export interface DecisionPoint {
  /** PROMPT — chỉ đặt câu hỏi, KHÔNG nhắc lại state line. */
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
    // CHỈ hỏi. Trạng thái ("đang xét gì", "max hiện tại bao nhiêu") thuộc
    // `consideration` và đã hiện ở dải nhân quả — nhắc lại ở đây là lặp.
    question: `${fmt(vi)} có làm ${mode} được cập nhật không?`,
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
        ? `${fmt(v)} có được cộng vào tổng không?`
        : `Biến đếm có tăng ở bước này không?`,
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
    question: `Ở bước này đã tìm thấy ${fmt(target)} chưa?`,
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
    question: `Sau phép so sánh này, phần nào của vùng tìm kiếm sẽ bị loại?`,
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
    question: `Hai phần tử này có đổi chỗ không?`,
    options: YES_NO,
    expectedId: swaps ? "yes" : "no",
    evidence: swaps
      ? `${fmt(vi)} và ${fmt(vj)} đang sai thứ tự ${orderText} nên hai phần tử đổi chỗ.`
      : `${fmt(vi)} rồi ${fmt(vj)} đã đúng thứ tự ${orderText} nên giữ nguyên.`,
    // Thứ tự cần sắp là dữ kiện để trả lời được câu hỏi — nó rời khỏi câu hỏi
    // thì phải có mặt ở state line, không được biến mất khỏi màn hình.
    consideration: `Đang xét cặp kề (${fmt(vi)}, ${fmt(vj)}) — vị trí ${cmp.i + 1} và ${cmp.j + 1}, sắp ${orderText}`,
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
    question: `${fmt(vj)} có bị dời sang phải một ô không?`,
    options: YES_NO,
    expectedId: shifts ? "yes" : "no",
    evidence: shifts
      ? `${fmt(vj)} ${word} ${fmt(key)} nên ${fmt(vj)} bị dời sang phải một ô.`
      : `${fmt(vj)} không ${word} ${fmt(key)} nên dừng dời — ${fmt(key)} sẽ được chèn ngay sau vị trí này.`,
    consideration: `Đang xét ${fmt(vj)} (vị trí ${cmp.i + 1}) — giá trị chèn: ${fmt(key)}`,
    expression: `${fmt(vj)} ${word} ${fmt(key)} ?`,
  };
}

function selectionDecision(state: AlgorithmSimState): DecisionPoint | null {
  const { cur, next } = steps(state);
  if (!next) return null;
  const cmp = cur.events.find((e) => e.type === "compare");
  if (!cmp || cmp.type !== "compare") return null;
  // Chỉ nhận bước so sánh của selection (có biến vị trí cực trị đang theo dõi).
  const vt = num(cur.snapshot.vars["vi_tri_cuc_tri"]);
  if (Number.isNaN(vt)) return null;

  const vCur = cur.snapshot.array[cmp.i]; // cực trị hiện tại (tại minIdx)
  const vNew = cur.snapshot.array[cmp.j]; // ứng viên đang xét
  const updates = next.events.some(
    (e) => e.type === "assign_var" && e.name === "vi_tri_cuc_tri",
  );
  const asc = (state.config.data.order ?? "asc") === "asc";
  const extremeText = asc ? "nhỏ nhất" : "lớn nhất";
  const word = asc ? "nhỏ hơn" : "lớn hơn";

  return {
    question: `Vị trí ${extremeText} có được cập nhật không?`,
    options: YES_NO,
    expectedId: updates ? "yes" : "no",
    evidence: updates
      ? `${fmt(vNew)} ${word} ${fmt(vCur)} nên vị trí ${extremeText} chuyển sang ô thứ ${cmp.j + 1}.`
      : `${fmt(vNew)} không ${word} ${fmt(vCur)} nên vị trí ${extremeText} giữ nguyên.`,
    consideration: `Đang xét ${fmt(vNew)} (vị trí ${cmp.j + 1}) — ${extremeText} hiện tại: ${fmt(vCur)}`,
    expression: `${fmt(vNew)} ${word} ${fmt(vCur)} ?`,
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
    case "selection_sort":
      return selectionDecision(state);
  }
}

/* ── CỤM CƠ CHẾ "QUÉT DÃY + BIẾN TÍCH LUỸ" (INTERACTION-FAMILY W1) ────────
 *
 * Bốn target `find_max` · `find_min` · `count_if` · `sum_if` cùng một cơ chế:
 * duyệt lần lượt → xét phần tử hiện tại → kiểm tra điều kiện → CẬP NHẬT hoặc
 * GIỮ NGUYÊN biến tích luỹ → sang phần tử kế.
 *
 * Ở bốn target này, cam kết của học sinh được diễn đạt bằng HÀNH ĐỘNG lên biến
 * tích luỹ chứ không bằng câu hỏi Có/Không. Đó vẫn là một dự đoán — vẫn phải
 * chốt trước khi thấy kết quả — nên nó đi qua ĐÚNG `predict.check` cũ. Không có
 * đường chấm điểm thứ hai, engine vẫn là bên duy nhất phán đúng/sai.
 *
 * VÌ SAO MODEL NÀY KHÔNG MANG ĐÁP ÁN: nếu đặt `correctActionId`/`evidence` vào
 * dữ liệu của renderer thì đáp án nằm sẵn trong DOM trước khi học sinh hành
 * động, và renderer bị mời tự phán xử. `challenge()` hiện tại cũng cố ý không
 * trả `expectedId` — giữ đúng ranh giới đó.
 */

/** Một hành động chạm thẳng vào cơ chế. `id` khớp option id của DecisionPoint. */
export interface MechanismAction {
  id: string;
  label: string;
  tone: "update" | "keep";
}

export interface ScanInteractionModel {
  /** Phần tử đang xét — nhãn và giá trị lấy từ snapshot. */
  candidateLabel: string;
  candidateValue: string;
  /** Biến tích luỹ — tên và giá trị hiện tại lấy từ `snapshot.vars`. */
  accumulatorLabel: string;
  accumulatorValue: string;
  /** Điều kiện đang xét, dạng hỏi — lấy từ `DecisionPoint.expression`. */
  expression: string;
  actions: MechanismAction[];
}

/**
 * W4B-2U2 §12 — BIẾN TÍCH LUỸ PHẢI THẤY ĐƯỢC TRÊN SÂN KHẤU, KỂ CẢ LÚC NÓ ĐỔI.
 *
 * Khoảng trống cuối cùng của ngữ pháp thị giác (audit U2-A): với `count_if` /
 * `sum_if`, biến đếm/tổng chỉ sống trong vùng hành động, nên chuyển tiếp
 * `4 → 5` hay `405 → 555` phải ĐỌC CHỮ mới biết. TRANSITION bị xếp `TEXT_ONLY`.
 *
 * ⚠️ KHÔNG ĐƯỢC ĐỌC BƯỚC SAU. Giá trị "sau" lấy từ bước HIỆN TẠI, giá trị
 * "trước" lấy từ bước ĐÃ QUA (`cursor - 1`) — đó là lịch sử, không phải tương
 * lai. Nhìn tới `cursor + 1` sẽ lộ đáp án của chính điểm quyết định đang hỏi,
 * đúng thứ `decisionPointOf` giữ kín.
 *
 * Hàm THUẦN, đọc `snapshot.vars` do engine sở hữu — renderer không tự cộng.
 */
export interface AccumulatorView {
  /** Tên biến hiển thị (max/min/tổng/biến đếm). */
  label: string;
  /** Giá trị ở bước hiện tại. */
  value: string;
  /** Giá trị ở bước liền trước; `null` khi đang ở bước đầu. */
  previous: string | null;
  /** Bước này biến vừa đổi giá trị. */
  changed: boolean;
}

/** Tên biến tích luỹ theo target — CÙNG bảng `scanInteractionOf` dùng. */
const ACC_VAR: Record<string, { v: string; label: string }> = {
  find_max: { v: "max", label: "max" },
  find_min: { v: "min", label: "min" },
  sum_if: { v: "tong", label: "tổng" },
  count_if: { v: "dem", label: "biến đếm" },
};

export function accumulatorViewOf(state: AlgorithmSimState): AccumulatorView | null {
  const spec = ACC_VAR[state.config.algorithm_id];
  if (!spec) return null;
  const trace = activeTrace(state);
  const at = clampStep(state, state.cursor);
  const now = trace.steps[at]?.snapshot.vars[spec.v];
  if (now === undefined) return null;
  const before = at > 0 ? trace.steps[at - 1]?.snapshot.vars[spec.v] : undefined;
  const value = fmt(num(now));
  const previous = before === undefined ? null : fmt(num(before));
  return { label: spec.label, value, previous, changed: previous !== null && previous !== value };
}

/** Bốn target thuộc cụm quét dãy — gate theo ĐỊNH DANH NGỮ NGHĨA đã validate. */
const SCAN_FAMILY = new Set(["find_max", "find_min", "count_if", "sum_if"]);

export function isScanFamily(algorithmId: string): boolean {
  return SCAN_FAMILY.has(algorithmId);
}

/**
 * Mô hình tương tác cho bước quyết định của cụm quét dãy.
 *
 * `null` = bước này không phải điểm quyết định, hoặc target không thuộc cụm.
 * Mọi trường đều DẪN XUẤT từ dữ liệu canonical: renderer không dựng lại phép so
 * sánh, không tự đánh giá điều kiện, không đoán kết quả.
 */
export function scanInteractionOf(state: AlgorithmSimState): ScanInteractionModel | null {
  const id = state.config.algorithm_id;
  if (!isScanFamily(id)) return null;

  const d = decisionPointOf(state);
  if (!d) return null;

  const trace = activeTrace(state);
  const cur = trace.steps[clampStep(state, state.cursor)];
  const ev = cur.events.find((e) => e.type === "compare" || e.type === "compare_value");
  if (!ev) return null;
  const index = ev.type === "compare" ? ev.i : ev.i;
  const value = cur.snapshot.array[index];

  const isExtreme = id === "find_max" || id === "find_min";
  const varName = id === "find_max" ? "max" : id === "find_min" ? "min" : id === "sum_if" ? "tong" : "dem";
  const accValue = cur.snapshot.vars[varName];

  // Nhãn hành động nói bằng NGÔN NGỮ CỦA CƠ CHẾ, không phải "Có"/"Không":
  // học sinh đang làm đúng việc mà thuật toán làm ở bước này.
  const updateLabel = isExtreme
    ? `Đặt ${fmt(value)} làm ${varName} mới`
    : id === "sum_if"
      ? `Cộng ${fmt(value)} vào tổng`
      : `Đếm ${fmt(value)} vào nhóm`;
  const keepLabel = isExtreme
    ? `Giữ ${varName} = ${fmt(num(accValue))}`
    : "Bỏ qua phần tử này";

  /* W3B §5.2 — DỮ KIỆN CHUYỂN CHỖ, KHÔNG ĐƯỢC BIẾN MẤT.
   *
   * Khi đề có nhãn ("An", "Bình"…), câu DUY NHẤT gọi tên phần tử là narration
   * bước quyết định — mà §5.2 vừa ẩn nó đi vì trùng dữ kiện. Nếu vùng hành động
   * không nhận lấy cái tên đó thì học sinh đọc "Phần tử vị trí 2" trong khi cột
   * trên sân khấu ghi "Bình": mất luôn cầu nối giữa đề bài và sân khấu.
   * Vùng hành động sở hữu ứng viên, nên tên của ứng viên thuộc về nó.
   */
  const labels = state.config.data.labels;
  const name = labels && labels[index] ? labels[index] : null;

  return {
    candidateLabel: name ? `${name} — vị trí ${index + 1}` : `Phần tử vị trí ${index + 1}`,
    candidateValue: fmt(value),
    accumulatorLabel: isExtreme ? varName : id === "sum_if" ? "tổng" : "biến đếm",
    accumulatorValue: fmt(num(accValue)),
    expression: d.expression,
    actions: [
      // id khớp option của DecisionPoint ⇒ nộp thẳng qua `predict.check`.
      { id: d.options[0].id, label: updateLabel, tone: "update" },
      { id: d.options[1].id, label: keepLabel, tone: "keep" },
    ],
  };
}

/* ── CỤM CƠ CHẾ "TÌM KIẾM" (INTERACTION-FAMILY W2) ────────────────────────
 *
 * `linear_search` và `binary_search` cùng khuôn: xét một phần tử → so sánh với
 * giá trị cần tìm → chọn bước đi tiếp → engine xác nhận. Nhưng cơ chế ẩn của
 * hai bài KHÁC nhau, nên nhiệm vụ của học sinh cũng khác:
 *
 * - `linear_search`: quyết định từng bước gần như hiển nhiên (7 có bằng 9 không).
 *   Cơ chế đáng học là CHI PHÍ. Nên hành động vẫn là tìm-thấy/tiếp-tục, còn chi
 *   phí hiện ra như THÔNG TIN TIẾN TRÌNH bên cạnh — không phải một câu hỏi.
 * - `binary_search`: quyết định là loại bỏ nửa nào — một quyết định KHÔNG GIAN
 *   thật sự, đáng để học sinh tự chỉ tay vào.
 *
 * ĐẢO NGHĨA — CHỖ DỄ SHIP BUG NHẤT CỦA WAVE NÀY:
 * `binaryDecision` hỏi "phần nào BỊ LOẠI", nên option `left` nghĩa là *nửa trái
 * bị loại*, tức việc tìm kiếm tiếp tục ở nửa PHẢI. Vì vậy `left → search-right`
 * và `right → search-left`. Ánh xạ thẳng tên-sang-tên sẽ dạy học sinh ngược hẳn
 * cơ chế. `id` giữ nguyên của engine để `predict.check` vẫn chấm đúng.
 */

/** Vị trí trên sân khấu. KHÔNG mang nghĩa quyết định. */
export type SearchVisualRole =
  | "current-item"
  | "continue-region"
  | "left-region"
  | "middle-item"
  | "right-region";

/** Nghĩa của hành động: việc tìm kiếm ĐI TIẾP về đâu. */
export type SearchSemanticAction = "continue" | "found" | "search-left" | "search-right";

export interface SearchAction {
  /** Trùng option id của DecisionPoint ⇒ nộp thẳng qua `predict.check`. */
  id: string;
  label: string;
  visualRole: SearchVisualRole;
  semanticAction: SearchSemanticAction;
}

/** Chi phí tìm kiếm — THÔNG TIN TIẾN TRÌNH, không phải câu hỏi (W2 §1.1). */
export interface SearchCost {
  comparisonsDone: number;
  remainingCandidates: number;
  worstCaseComparisons: number;
}

export interface SearchInteractionModel {
  currentIndex: number;
  currentValue: string;
  targetValue: string;
  /** Chỉ có ở tìm kiếm nhị phân — vùng xét hiện tại, lấy từ vars trai/phai/giua. */
  activeRange?: { left: number; right: number; middle: number };
  /** Chỉ có ở tìm kiếm tuần tự (W2 §1.1). */
  cost?: SearchCost;
  /** Tiền đề phải nói ra với học sinh; null = bài này không có tiền đề nào. */
  precondition: string | null;
  actions: SearchAction[];
}

const SEARCH_FAMILY = new Set(["linear_search", "binary_search"]);

export function isSearchFamily(algorithmId: string): boolean {
  return SEARCH_FAMILY.has(algorithmId);
}

/**
 * Mô hình tương tác cho bước quyết định của cụm tìm kiếm.
 *
 * Như `scanInteractionOf`: KHÔNG mang `correctActionId`, KHÔNG mang `evidence`,
 * KHÔNG mang `resultIndex` — cả ba đều là đáp án. Chấm vẫn qua `predict.check`.
 */
export function searchInteractionOf(state: AlgorithmSimState): SearchInteractionModel | null {
  const id = state.config.algorithm_id;
  if (!isSearchFamily(id)) return null;

  const d = decisionPointOf(state);
  if (!d) return null;

  const trace = activeTrace(state);
  const cur = trace.steps[clampStep(state, state.cursor)];
  const target = state.config.data.target;
  if (target === null) return null;

  if (id === "linear_search") {
    const ev = cur.events.find((e) => e.type === "compare_value");
    if (!ev || ev.type !== "compare_value") return null;
    const n = state.config.data.array.length;
    // `vars.i` là canonical; chi phí chỉ là số học trên nó, KHÔNG chạy lại thuật toán.
    const done = num(cur.snapshot.vars["i"]) + 1;
    return {
      currentIndex: ev.i,
      currentValue: fmt(cur.snapshot.array[ev.i]),
      targetValue: fmt(target),
      cost: {
        comparisonsDone: done,
        remainingCandidates: Math.max(n - done, 0),
        worstCaseComparisons: n,
      },
      precondition: null,
      actions: [
        {
          id: d.options[0].id,
          label: "Đây là phần tử cần tìm",
          visualRole: "current-item",
          semanticAction: "found",
        },
        {
          id: d.options[1].id,
          label: "Kiểm tra phần tử kế tiếp",
          visualRole: "continue-region",
          semanticAction: "continue",
        },
      ],
    };
  }

  // ── binary_search ──
  const mid = num(cur.snapshot.vars["giua"]);
  const left = num(cur.snapshot.vars["trai"]);
  const right = num(cur.snapshot.vars["phai"]);
  if ([mid, left, right].some(Number.isNaN)) return null;

  const byId = new Map(d.options.map((o) => [o.id, o]));
  const actions: SearchAction[] = [];
  // Xem chú thích ĐẢO NGHĨA ở đầu khối: option "left" = nửa TRÁI bị loại.
  if (byId.has("right")) {
    actions.push({
      id: "right",
      label: "Tìm tiếp ở nửa TRÁI",
      visualRole: "left-region",
      semanticAction: "search-left",
    });
  }
  if (byId.has("found")) {
    actions.push({
      id: "found",
      label: "Chính là phần tử giữa",
      visualRole: "middle-item",
      semanticAction: "found",
    });
  }
  if (byId.has("left")) {
    actions.push({
      id: "left",
      label: "Tìm tiếp ở nửa PHẢI",
      visualRole: "right-region",
      semanticAction: "search-right",
    });
  }

  return {
    currentIndex: mid,
    currentValue: fmt(cur.snapshot.array[mid]),
    targetValue: fmt(target),
    activeRange: { left, right, middle: mid },
    // Tiền đề phải nói ra: SGK nhấn mạnh nhị phân chỉ đúng trên dãy có thứ tự.
    precondition: "Thuật toán này chỉ đúng khi dãy đã được sắp xếp tăng dần.",
    actions,
  };
}

/* ── W4B-2I: HÀNH ĐỘNG GẮN VÀO SÂN KHẤU ──────────────────────────────────────
 *
 * `SearchAction.visualRole` tồn tại từ W2 nhưng tới nay chỉ được tiêu vào một
 * tên class CSS trên một cái nút (`SearchActionZone.tsx`). Nó vốn là một TỪ VỰNG
 * VỊ TRÍ: "nửa trái", "phần tử giữa", "nửa phải", "phần tử đang xét", "phần còn
 * lại". Wave này chỉ làm một việc — nối từ vựng đó vào chỉ số cột thật, để học
 * sinh bấm vào CHÍNH VÙNG mà hành động tác động, thay vì bấm một nút rời mô tả
 * vùng đó bằng lời.
 *
 * VÌ SAO ÁNH XẠ NẰM Ở ĐÂY, KHÔNG Ở RENDERER. Câu "nửa trái của vùng đang xét là
 * các cột trai..giua-1" là NGỮ NGHĨA của thuật toán, không phải bố cục. Để
 * `ArrayView` tự suy ra nghĩa là renderer bắt đầu sở hữu sự thật thuật toán —
 * đúng thứ bất biến #6 và `SIMULATION_VS_ILLUSTRATION_CONTRACT §3` cấm. Renderer
 * chỉ nhận danh sách chỉ số + nhãn + `id`, vẽ vùng bấm, và phát lại `id` nguyên
 * văn. `id` vẫn là option id của `DecisionPoint` ⇒ chấm vẫn đi qua đúng
 * `predict.check`, không sinh đường chấm thứ hai.
 *
 * TẤT CẢ-HOẶC-KHÔNG. Trả `null` khi có bất kỳ hành động nào không ánh xạ được
 * sang một vùng KHÔNG RỖNG (vd nửa trái rỗng khi `giua === trai`). Nửa vùng bấm
 * nửa nút sẽ là HAI bề mặt cam kết trên cùng một bước — vi phạm
 * `COMMITMENT_SURFACE_COUNT <= 1`. Thà lùi hẳn về hàng nút cho bước đó.
 */

/** Một vùng bấm được trên sân khấu. KHÔNG mang đáp án — chỉ vị trí + nhãn + id. */
export interface SceneRegion {
  /** Option id của `DecisionPoint` — renderer phát lại NGUYÊN VĂN, không diễn giải. */
  id: string;
  /** Tên khả truy cập (đọc màn hình) cho vùng này. */
  label: string;
  /** Các cột hợp thành vùng. Luôn không rỗng. */
  indices: number[];
}

const range = (from: number, to: number): number[] =>
  from > to ? [] : Array.from({ length: to - from + 1 }, (_, k) => from + k);

/**
 * Ánh xạ hành động tìm kiếm → vùng cột trên sân khấu.
 *
 * `arrayLength` truyền vào tường minh thay vì moi từ `cost.worstCaseComparisons`
 * (vốn TÌNH CỜ bằng n ở tìm tuần tự): một hằng số trùng nhau không phải một hợp
 * đồng, và nó không tồn tại ở nhị phân.
 */
export function searchSceneRegions(
  model: SearchInteractionModel,
  arrayLength: number,
): SceneRegion[] | null {
  const regions: SceneRegion[] = [];
  for (const a of model.actions) {
    let indices: number[];
    switch (a.visualRole) {
      case "current-item":
      case "middle-item":
        indices = [model.currentIndex];
        break;
      case "continue-region":
        // Tuần tự: "xét tiếp" = toàn bộ phần CHƯA duyệt sau phần tử hiện tại.
        indices = range(model.currentIndex + 1, arrayLength - 1);
        break;
      case "left-region":
        if (!model.activeRange) return null;
        indices = range(model.activeRange.left, model.activeRange.middle - 1);
        break;
      case "right-region":
        if (!model.activeRange) return null;
        indices = range(model.activeRange.middle + 1, model.activeRange.right);
        break;
    }
    if (indices.length === 0) return null;
    regions.push({ id: a.id, label: a.label, indices });
  }
  // Hai hành động cùng trỏ một cột thì học sinh không thể phân biệt bằng cách
  // bấm — cũng là một ca "không gắn được vào sân khấu", không phải ca hiếm bỏ qua.
  const touched = regions.flatMap((r) => r.indices);
  if (new Set(touched).size !== touched.length) return null;
  return regions.length > 0 ? regions : null;
}

/* ── CỤM CƠ CHẾ "SẮP XẾP" (W3B §8) ────────────────────────────────────────────
 *
 * Ba thuật toán sắp xếp cùng một khuôn — duyệt, so sánh, rồi HÀNH ĐỘNG hoặc
 * GIỮ NGUYÊN — nhưng hành động của mỗi bài là một cơ chế khác nhau, nên không
 * gộp thành một nhãn chung:
 * - `compare-pair`     (nổi bọt): cặp kề có đổi chỗ không;
 * - `select-candidate` (chọn):    có ghi nhớ vị trí cực trị mới không;
 * - `shift-or-stop`    (chèn):    phần tử này có bị dời sang phải không.
 *
 * VÌ SAO CAM KẾT LÀ NÚT, KHÔNG PHẢI KÉO (quyết định B của wave):
 * kéo cột ĐÃ có nghĩa từ trước — thí nghiệm what-if, fork sang nhánh. Dùng lại
 * đúng cử chỉ ấy cho cam kết thì cùng một thao tác, trên cùng hai cột, ở cùng
 * một bước lại mang hai nghĩa và cho hai kết cục khác nhau. Nút giữ hai nghĩa
 * tách bạch, và dùng lại đúng primitive mà cụm quét dãy/tìm kiếm đã chứng minh.
 *
 * Như hai cụm trước: model KHÔNG mang `expectedId`/`evidence`/kết quả cuối, và
 * `id` của hành động chính là option id của `DecisionPoint` nên chấm vẫn đi qua
 * đúng `predict.check`.
 */

export type SortInteractionKind = "compare-pair" | "select-candidate" | "shift-or-stop";

/** Một dữ kiện hiện trạng — nhãn + giá trị, lấy từ snapshot/vars canonical. */
export interface SortFact {
  label: string;
  value: string;
}

export interface SortInteractionModel {
  kind: SortInteractionKind;
  /** Việc đang làm ở bước này. KHÔNG phải câu hỏi, không mang đáp án. */
  title: string;
  /** Ứng viên / cặp / quân bài đang giữ / ranh giới vùng chưa sắp. */
  facts: SortFact[];
  /** Phép so sánh dạng hỏi — lấy nguyên từ `DecisionPoint.expression`. */
  expression: string;
  actions: MechanismAction[];
}

const SORT_FAMILY = new Set(["bubble_sort", "selection_sort", "insertion_sort"]);

export function isSortFamily(algorithmId: string): boolean {
  return SORT_FAMILY.has(algorithmId);
}

/**
 * Ranh giới vùng CHƯA SẮP — đọc `set_range` gần nhất ĐÃ ĐI QUA.
 *
 * Quét LÙI, không quét tới: bước đã qua là chuyện đã xảy ra, còn đọc bước sau
 * là đọc đáp án. `insertionHold` trong `ui.tsx` đã dùng đúng khuôn này.
 */
function lastRange(state: AlgorithmSimState, at: number): { left: number; right: number } | null {
  const trace = activeTrace(state);
  for (let i = at; i >= 0; i -= 1) {
    for (const ev of trace.steps[i].events) {
      if (ev.type === "set_range") return { left: ev.left, right: ev.right };
    }
  }
  return null;
}

export function sortInteractionOf(state: AlgorithmSimState): SortInteractionModel | null {
  const id = state.config.algorithm_id;
  if (!isSortFamily(id)) return null;

  const d = decisionPointOf(state);
  if (!d) return null;

  const trace = activeTrace(state);
  const at = clampStep(state, state.cursor);
  const cur = trace.steps[at];
  const cmp = cur.events.find((e) => e.type === "compare");
  if (!cmp || cmp.type !== "compare") return null;

  const asc = (state.config.data.order ?? "asc") === "asc";
  const orderText = asc ? "tăng dần" : "giảm dần";
  // Quy ước chung ba cụm: option[0] = HÀNH ĐỘNG, option[1] = GIỮ NGUYÊN.
  const act = (label: string, keep: string): MechanismAction[] => [
    { id: d.options[0].id, label, tone: "update" },
    { id: d.options[1].id, label: keep, tone: "keep" },
  ];

  if (id === "bubble_sort") {
    const vi = fmt(cur.snapshot.array[cmp.i]);
    const vj = fmt(cur.snapshot.array[cmp.j]);
    return {
      kind: "compare-pair",
      title: "Cặp kề đang xét",
      facts: [
        { label: `Vị trí ${cmp.i + 1}`, value: vi },
        { label: `Vị trí ${cmp.j + 1}`, value: vj },
        { label: "Cần sắp", value: orderText },
      ],
      expression: d.expression,
      actions: act("Đổi chỗ hai phần tử này", "Giữ nguyên thứ tự"),
    };
  }

  if (id === "selection_sort") {
    // `cmp.i` = ô đang giữ vai cực trị, `cmp.j` = ứng viên đang xét (engine).
    const extremeText = asc ? "nhỏ nhất" : "lớn nhất";
    const range = lastRange(state, at);
    const facts: SortFact[] = [
      { label: "Đang xét", value: `${fmt(cur.snapshot.array[cmp.j])} (vị trí ${cmp.j + 1})` },
      { label: `${extremeText} hiện tại`, value: `${fmt(cur.snapshot.array[cmp.i])} (vị trí ${cmp.i + 1})` },
    ];
    // Ranh giới là dữ kiện phải nói ra: cơ chế của bài là "chỉ chọn TRONG phần
    // chưa sắp", mà ranh giới đó nằm im trong event nên học sinh không thấy.
    if (range) {
      facts.push({ label: "Phần chưa sắp", value: `vị trí ${range.left + 1}–${range.right + 1}` });
    }
    return {
      kind: "select-candidate",
      title: `Tìm phần tử ${extremeText} của phần chưa sắp`,
      facts,
      expression: d.expression,
      actions: act(
        `Chọn phần tử này làm ${extremeText} mới`,
        `Giữ ${extremeText} hiện tại`,
      ),
    };
  }

  // ── insertion_sort ──
  const key = cur.snapshot.vars["gia_tri_chen"];
  if (typeof key !== "number") return null;
  return {
    kind: "shift-or-stop",
    title: "Tìm chỗ cho quân bài đang giữ",
    facts: [
      { label: "Đang giữ", value: fmt(key) },
      { label: "Đang xét", value: `${fmt(cur.snapshot.array[cmp.i])} (vị trí ${cmp.i + 1})` },
    ],
    expression: d.expression,
    actions: act("Dời phần tử này sang phải", "Dừng dịch chuyển"),
  };
}

/* ── VÙNG HÀNH ĐỘNG SÂN KHẤU: ĐẾM ĐƯỢC, VÀ PHẢI ≤ 1 (W3B §5.2, §14) ────────
 *
 * Ba cụm cơ chế đều có thể dựng vùng hành động ngay trên sân khấu. Bất biến:
 * một bước có TỐI ĐA MỘT mô hình — hai vùng cùng lúc nghĩa là hỏi học sinh hai
 * câu cho cùng một quyết định. Gom phép đếm về một chỗ để `presentedInStage`,
 * khe thuyết minh và test cùng đọc MỘT nguồn, không ai tự suy lại.
 */

/** Các mô hình tương tác sân khấu đang tồn tại ở bước hiện tại. */
export function stageInteractionsOf(state: AlgorithmSimState): string[] {
  const present: string[] = [];
  if (scanInteractionOf(state) !== null) present.push("scan");
  if (searchInteractionOf(state) !== null) present.push("search");
  if (sortInteractionOf(state) !== null) present.push("sort");
  return present;
}

/** Bước này có vùng hành động trên sân khấu không. */
export function hasStageInteraction(state: AlgorithmSimState): boolean {
  return stageInteractionsOf(state).length > 0;
}

/**
 * W4B-2T — TÁCH PHẦN TIẾN TRÌNH KHỎI PHẦN KẾT QUẢ ở bước cuối.
 *
 * Ở bước `done`, engine kể `"<tiến trình>. <kết quả>"` (vd `"Duyệt hết dãy.
 * Phần tử lớn nhất là Bình (9), ở vị trí 2."`) trong khi `.result-banner` in
 * đúng vế sau. Hàm trả về **chỉ vế tiến trình**, hoặc `null` khi thuyết minh
 * không nói gì ngoài kết quả (4/8 bài rơi vào ca này — chuỗi trùng từng ký tự).
 *
 * So bằng CHUỖI CON thay vì tách theo dấu chấm: `result` có thể chứa dấu chấm
 * bên trong (số thập phân, "9,5.") nên cắt theo dấu câu sẽ vỡ. Hàm THUẦN, kiểm
 * được không cần trình duyệt.
 */
export function processLeadOf(narration: string, result: string): string | null {
  const i = narration.indexOf(result);
  if (i < 0) return narration; // engine đổi cách kể ⇒ giữ nguyên, không đoán
  const lead = narration.slice(0, i).trim();
  return lead.length > 0 ? lead : null;
}

/**
 * Bỏ phần HỎI khỏi thuyết minh, giữ lại phần MÔ TẢ (UI-CLARITY W1).
 *
 * Engine kể bước quyết định theo khuôn `"<mô tả>: <câu hỏi>?"`, ví dụ
 * `"So sánh a[1] = 9 với max = 7,5: max có được cập nhật không?"`. Khuôn đó có
 * lý do lịch sử: khe thuyết minh từng là nơi DUY NHẤT nêu câu hỏi nên nó phải
 * hỏi mà không được lộ đáp án.
 *
 * Từ W1, câu hỏi có nhà riêng là PredictionBar, nên để nguyên thì cùng một câu
 * hỏi hiện hai chỗ cùng lúc (đo được trong Chrome). Ở đây chỉ CẮT PHẦN TRÌNH
 * BÀY: `step.narration` của engine, timeline và mọi kết quả tất định giữ nguyên
 * từng ký tự — `getExplainContext` vẫn gửi đi chuỗi gốc.
 */
export function narrationWithoutPrompt(narration: string): string {
  if (!narration.trimEnd().endsWith("?")) return narration;
  const cut = narration.lastIndexOf(": ");
  if (cut < 0) return narration;
  return `${narration.slice(0, cut)}.`;
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
