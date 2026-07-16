/**
 * Declarative Bounded Scan (M12) — MỘT bộ xương quét TẤT ĐỊNH, engine sở hữu,
 * chạy trên substrate TraceBuilder có sẵn.
 *
 * Ý tưởng (đã audit): nhiều bài single-pass trên mảng (find_max, count_if,
 * linear_search…) là CÙNG một vòng quét trái→phải; điểm khác nhau gói gọn trong
 * vài lựa chọn ENUM ĐÓNG. Spec chỉ CẤU HÌNH các enum đó; interpreter sở hữu
 * hoàn toàn: thứ tự lặp, tiến chỉ số, biên dừng (≤ n → non-Turing, dừng hiển
 * nhiên), sinh event, và mọi lời gọi TraceBuilder.
 *
 * KHÔNG có: while/for do spec định nghĩa, biểu thức tự do, gán tùy ý, đệ quy,
 * timeline dựng sẵn, code sinh ra. LLM (giai đoạn sau) chỉ được điền các enum +
 * hằng số đầu vào — nó KHÔNG sở hữu thuật toán, chỉ chọn cấu hình trong không
 * gian đã đóng. Đây KHÔNG phải ngôn ngữ lập trình.
 */
import { fmt, TraceBuilder, type WhatIfSwap } from "./trace-builder";
import type { ConditionOp, Trace, TraceEvent } from "./types";

export const SCAN_VERSION = "1.0";

/** Khởi tạo accumulator: từ phần tử đầu (quét từ i=1) hoặc từ hằng (quét từ i=0). */
export type ScanSeed =
  | { from: "first_element"; varName: string; trackIndexVar?: string }
  | { from: "constant"; value: number; varName: string };

/** So sánh mỗi phần tử: với accumulator đang chạy, hoặc với một hằng số. */
export type ScanCompare =
  | { kind: "to_accumulator"; op: ConditionOp }
  | { kind: "to_constant"; op: ConditionOp; value: number };

/** Cập nhật accumulator khi so sánh cho kết quả "trúng" (guard = compare). */
export type ScanUpdate =
  | { kind: "replace_with_current" } // acc := a[i]
  | { kind: "add_current" } //          acc += a[i]
  | { kind: "increment" } //            acc += 1
  | { kind: "none" }; //                không đổi acc (vd tìm kiếm)

/** Chính sách đánh dấu ô — dẫn xuất, không phải thuật toán riêng. */
export type ScanMarking = "running_winner" | "match_highlight";

/** Điều kiện dừng: hết mảng, hoặc dừng ngay lần "trúng" đầu tiên. */
export type ScanStop = "end_of_array" | "first_match";

export interface ScanSpec {
  scan_version: string;
  array: number[];
  labels?: string[] | null;
  seed: ScanSeed;
  compare: ScanCompare;
  update: ScanUpdate;
  marking: ScanMarking;
  stop: ScanStop;
}

const CONDITION_OPS: readonly ConditionOp[] = [">", ">=", "<", "<=", "==", "!="];
const UPDATE_KINDS = ["replace_with_current", "add_current", "increment", "none"] as const;
const MARKINGS = ["running_winner", "match_highlight"] as const;
const STOPS = ["end_of_array", "first_match"] as const;

export type ScanValidation = { ok: true; spec: ScanSpec } | { ok: false; error: string };

function isObj(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}
function isNum(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v);
}
function onlyKeys(o: Record<string, unknown>, allowed: readonly string[]): string | null {
  for (const k of Object.keys(o)) if (!allowed.includes(k)) return k;
  return null;
}

/**
 * Kiểm ScanSpec TRƯỚC khi chạy: mọi trường có allowlist, không khóa lạ, không
 * kiểu sai, version đúng, mảng không rỗng, và vài luật COHERENCE giữ họ = quét
 * trên GIÁ TRỊ phần tử (chống cấu hình vô nghĩa mà LLM có thể sinh sau này).
 * KHÔNG eval, KHÔNG code — chỉ dữ liệu khai báo trong không gian đóng.
 */
export function validateScanSpec(raw: unknown): ScanValidation {
  if (!isObj(raw)) return { ok: false, error: "Spec không phải object." };
  const unknownTop = onlyKeys(raw, [
    "scan_version",
    "array",
    "labels",
    "seed",
    "compare",
    "update",
    "marking",
    "stop",
  ]);
  if (unknownTop) return { ok: false, error: `Khóa lạ ở cấp cao nhất: "${unknownTop}".` };

  if (raw.scan_version !== SCAN_VERSION) return { ok: false, error: `scan_version phải là "${SCAN_VERSION}".` };

  if (!Array.isArray(raw.array) || raw.array.length < 1) return { ok: false, error: "array phải có ≥ 1 phần tử." };
  if (!raw.array.every(isNum)) return { ok: false, error: "array chỉ được chứa số hữu hạn." };
  const n = raw.array.length;

  if (raw.labels != null) {
    if (!Array.isArray(raw.labels) || raw.labels.length !== n || !raw.labels.every((x) => typeof x === "string")) {
      return { ok: false, error: "labels (nếu có) phải là mảng chuỗi cùng độ dài với array." };
    }
  }

  // ── seed ──
  const seed = raw.seed;
  if (!isObj(seed)) return { ok: false, error: "seed phải là object." };
  if (seed.from === "first_element") {
    const k = onlyKeys(seed, ["from", "varName", "trackIndexVar"]);
    if (k) return { ok: false, error: `Khóa lạ trong seed: "${k}".` };
    if (typeof seed.varName !== "string" || !seed.varName) return { ok: false, error: "seed.varName phải là chuỗi không rỗng." };
    if (seed.trackIndexVar !== undefined && (typeof seed.trackIndexVar !== "string" || !seed.trackIndexVar)) {
      return { ok: false, error: "seed.trackIndexVar (nếu có) phải là chuỗi không rỗng." };
    }
  } else if (seed.from === "constant") {
    const k = onlyKeys(seed, ["from", "varName", "value"]);
    if (k) return { ok: false, error: `Khóa lạ trong seed: "${k}".` };
    if (typeof seed.varName !== "string" || !seed.varName) return { ok: false, error: "seed.varName phải là chuỗi không rỗng." };
    if (!isNum(seed.value)) return { ok: false, error: "seed.value (constant) phải là số." };
  } else {
    return { ok: false, error: `seed.from lạ: ${JSON.stringify(seed.from)}.` };
  }

  // ── compare ──
  const compare = raw.compare;
  if (!isObj(compare)) return { ok: false, error: "compare phải là object." };
  if (!CONDITION_OPS.includes(compare.op as ConditionOp)) return { ok: false, error: `compare.op lạ: ${JSON.stringify(compare.op)}.` };
  if (compare.kind === "to_accumulator") {
    const k = onlyKeys(compare, ["kind", "op"]);
    if (k) return { ok: false, error: `Khóa lạ trong compare: "${k}".` };
  } else if (compare.kind === "to_constant") {
    const k = onlyKeys(compare, ["kind", "op", "value"]);
    if (k) return { ok: false, error: `Khóa lạ trong compare: "${k}".` };
    if (!isNum(compare.value)) return { ok: false, error: "compare.value (to_constant) phải là số." };
  } else {
    return { ok: false, error: `compare.kind lạ: ${JSON.stringify(compare.kind)}.` };
  }

  // ── update / marking / stop ──
  const update = raw.update;
  if (!isObj(update) || onlyKeys(update, ["kind"])) return { ok: false, error: "update phải là object chỉ có 'kind'." };
  if (!UPDATE_KINDS.includes(update.kind as (typeof UPDATE_KINDS)[number])) {
    return { ok: false, error: `update.kind lạ: ${JSON.stringify(update.kind)}.` };
  }
  if (!MARKINGS.includes(raw.marking as (typeof MARKINGS)[number])) return { ok: false, error: `marking lạ: ${JSON.stringify(raw.marking)}.` };
  if (!STOPS.includes(raw.stop as (typeof STOPS)[number])) return { ok: false, error: `stop lạ: ${JSON.stringify(raw.stop)}.` };

  // ── Coherence: giữ họ = quét trên GIÁ TRỊ phần tử ──
  if (raw.marking === "running_winner" && update.kind !== "replace_with_current") {
    return { ok: false, error: "marking running_winner đòi update replace_with_current (winner phải là phần tử đang giữ)." };
  }
  if (compare.kind === "to_accumulator" && update.kind !== "replace_with_current") {
    return { ok: false, error: "compare to_accumulator đòi update replace_with_current (accumulator phải giữ giá trị một phần tử; dùng to_constant nếu so với hằng)." };
  }

  return { ok: true, spec: raw as unknown as ScanSpec };
}

/** Ký hiệu phép so sánh cho mã giả (khớp giọng PSEUDOCODE kiểu SGK). */
const OP_SYMBOL: Record<ConditionOp, string> = {
  ">": ">",
  ">=": "≥",
  "<": "<",
  "<=": "≤",
  "==": "=",
  "!=": "≠",
};

/**
 * Mã giả DẪN XUẤT TỪ SPEC — skeleton 5 dòng cố định (seed / lặp / so sánh /
 * hành-động-khi-trúng / trả về), nội dung từng dòng điền theo enum của spec.
 * runScan gắn Step.line theo CÙNG layout này (một nguồn, chống highlight trôi):
 *   1 = seed · 3 = so sánh · 4 = cập nhật / trả-về-khi-trúng · 5 = kết thúc.
 * Đây là TEMPLATE ĐÓNG trên không gian enum đã validate — không phải renderer
 * chương trình tổng quát.
 */
export function scanPseudocode(spec: ScanSpec): string[] {
  const { seed, compare, update, stop } = spec;
  const v = seed.varName;
  const ivar = seed.from === "first_element" ? seed.trackIndexVar : undefined;

  const seedLine =
    seed.from === "first_element"
      ? `${v} ← a[1]${ivar ? `; ${ivar} ← 1` : ""}`
      : `${v} ← ${fmt(seed.value)}`;
  const start = seed.from === "first_element" ? 2 : 1;
  const loopLine = `với mỗi i từ ${start} đến n:`;
  const rhs = compare.kind === "to_accumulator" ? v : fmt(compare.value);
  const compareLine = `   nếu a[i] ${OP_SYMBOL[compare.op]} ${rhs} thì`;

  let hitLine: string;
  if (update.kind === "replace_with_current") hitLine = `      ${v} ← a[i]${ivar ? `; ${ivar} ← i` : ""}`;
  else if (update.kind === "add_current") hitLine = `      ${v} ← ${v} + a[i]`;
  else if (update.kind === "increment") hitLine = `      ${v} ← ${v} + 1`;
  else hitLine = stop === "first_match" ? "      trả về vị trí i" : "      đánh dấu a[i]";
  if (stop === "first_match" && update.kind !== "none") hitLine += "; trả về vị trí i";

  const doneLine =
    stop === "first_match" ? "trả về “không tìm thấy”" : `trả về ${v}${ivar ? ` và vị trí ${ivar}` : ""}`;

  return [seedLine, loopLine, compareLine, hitLine, doneLine];
}

function relation(x: number, y: number): "<" | ">" | "==" {
  return x > y ? ">" : x < y ? "<" : "==";
}

function opHolds(x: number, y: number, op: ConditionOp): boolean {
  switch (op) {
    case ">":
      return x > y;
    case ">=":
      return x >= y;
    case "<":
      return x < y;
    case "<=":
      return x <= y;
    case "==":
      return x === y;
    case "!=":
      return x !== y;
  }
}

/**
 * Chạy một ScanSpec đã hợp lệ → Trace (cùng shape mọi engine specialized).
 * whatIf tùy chọn để tương thích khung can thiệp học sinh của TraceBuilder.
 *
 * Vòng lặp DUY NHẤT, biên `i < n` — interpreter sở hữu; spec không định nghĩa
 * điều khiển. Dừng hiển nhiên (≤ n bước) → non-Turing, tất định.
 */
export function runScan(spec: ScanSpec, whatIf?: WhatIfSwap): Trace {
  const b = new TraceBuilder(spec.array, "engine", whatIf);
  const n = b.length;
  const { seed, compare, update, marking, stop } = spec;

  // ── Seed accumulator + chỉ số bắt đầu ──
  // Line theo CÙNG layout scanPseudocode: 1=seed · 3=so sánh · 4=cập nhật/trả-về-khi-trúng · 5=kết thúc.
  let acc: number;
  let accIndex = 0;
  let start: number;
  if (seed.from === "first_element") {
    acc = b.at(0);
    accIndex = 0;
    b.setVar(seed.varName, acc);
    if (seed.trackIndexVar) b.setVar(seed.trackIndexVar, 0);
    if (marking === "running_winner") b.mark(0, "considering");
    b.step(
      [{ type: "assign_var", name: seed.varName, value: acc }],
      `Bắt đầu: tạm coi phần tử đầu tiên là ${seed.varName} = ${fmt(acc)}.`,
      false,
      1,
    );
    start = 1;
  } else {
    acc = seed.value;
    b.setVar(seed.varName, acc);
    b.step([{ type: "assign_var", name: seed.varName, value: acc }], `Khởi tạo ${seed.varName} = ${fmt(acc)}.`, false, 1);
    start = 0;
  }

  // ── Quét ──
  for (let i = start; i < n; i++) {
    const cur = b.at(i);
    let hit: boolean;
    if (compare.kind === "to_accumulator") {
      hit = opHolds(cur, acc, compare.op);
      // M9-S1: bước quyết định là CÂU HỎI — không lộ đáp án sớm.
      b.step(
        [{ type: "compare", i, j: accIndex, result: relation(cur, acc) }],
        `So sánh a[${i + 1}] = ${fmt(cur)} với ${seed.varName} = ${fmt(acc)}: ${seed.varName} có được cập nhật không?`,
        true,
        3,
      );
    } else {
      hit = opHolds(cur, compare.value, compare.op);
      b.step(
        [{ type: "compare_value", i, value: compare.value, result: hit ? "match" : "no_match" }],
        `Xét a[${i + 1}] = ${fmt(cur)}: có thỏa điều kiện "${OP_SYMBOL[compare.op]} ${fmt(compare.value)}" không?`,
        true,
        3,
      );
    }

    if (!hit) {
      b.mark(i, "eliminated");
      continue;
    }

    // Trúng: cập nhật accumulator + đánh dấu theo policy
    if (marking === "running_winner") b.mark(accIndex, "eliminated"); // hạ winner cũ
    if (update.kind === "replace_with_current") {
      acc = cur;
      accIndex = i;
    } else if (update.kind === "add_current") {
      acc += cur;
    } else if (update.kind === "increment") {
      acc += 1;
    }
    if (marking === "running_winner") b.mark(i, "considering");
    else b.mark(i, "found");

    const events: TraceEvent[] = [];
    if (update.kind !== "none") {
      b.setVar(seed.varName, acc);
      events.push({ type: "assign_var", name: seed.varName, value: acc });
      if (seed.from === "first_element" && seed.trackIndexVar && update.kind === "replace_with_current") {
        b.setVar(seed.trackIndexVar, i);
        events.push({ type: "assign_var", name: seed.trackIndexVar, value: i });
      }
    }
    if (events.length) b.step(events, `Cập nhật: ${seed.varName} = ${fmt(acc)}.`, false, 4);

    if (stop === "first_match") {
      const result = `Tìm thấy tại vị trí thứ ${i + 1}. Số lần so sánh: ${i + 1}.`;
      b.step([{ type: "done", result }], result, false, 4);
      return b.build();
    }
  }

  // ── Kết thúc ──
  if (marking === "running_winner") {
    b.clearMarks();
    b.mark(accIndex, "found");
  }
  const result =
    stop === "first_match"
      ? `Duyệt hết dãy, không phần tử nào thỏa điều kiện. Số lần so sánh: ${n - start}.`
      : marking === "running_winner"
        ? `Duyệt hết dãy. ${seed.varName} = ${fmt(acc)}, tại vị trí thứ ${accIndex + 1}.`
        : `Duyệt hết dãy. ${seed.varName} = ${fmt(acc)}.`;
  b.step([{ type: "done", result }], result, false, 5);
  return b.build();
}
