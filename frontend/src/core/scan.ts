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
import { TraceBuilder, type WhatIfSwap } from "./trace-builder";
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
  let acc: number;
  let accIndex = 0;
  let start: number;
  if (seed.from === "first_element") {
    acc = b.at(0);
    accIndex = 0;
    b.setVar(seed.varName, acc);
    if (seed.trackIndexVar) b.setVar(seed.trackIndexVar, 0);
    if (marking === "running_winner") b.mark(0, "considering");
    b.step([{ type: "assign_var", name: seed.varName, value: acc }], `Khởi tạo ${seed.varName} = ${acc}.`, false);
    start = 1;
  } else {
    acc = seed.value;
    b.setVar(seed.varName, acc);
    b.step([{ type: "assign_var", name: seed.varName, value: acc }], `Khởi tạo ${seed.varName} = ${acc}.`, false);
    start = 0;
  }

  // ── Quét ──
  for (let i = start; i < n; i++) {
    const cur = b.at(i);
    let hit: boolean;
    if (compare.kind === "to_accumulator") {
      hit = opHolds(cur, acc, compare.op);
      b.step([{ type: "compare", i, j: accIndex, result: relation(cur, acc) }], "So sánh phần tử với giá trị đang giữ.", true);
    } else {
      hit = opHolds(cur, compare.value, compare.op);
      b.step([{ type: "compare_value", i, value: compare.value, result: hit ? "match" : "no_match" }], "Xét điều kiện của phần tử.", true);
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
    if (events.length) b.step(events, `Cập nhật ${seed.varName} = ${acc}.`, false);

    if (stop === "first_match") {
      const result = `Tìm thấy tại vị trí thứ ${i + 1}.`;
      b.step([{ type: "done", result }], result, false);
      return b.build();
    }
  }

  // ── Kết thúc ──
  if (marking === "running_winner") {
    b.clearMarks();
    b.mark(accIndex, "found");
  }
  const result = `Duyệt hết dãy. Kết quả: ${acc}.`;
  b.step([{ type: "done", result }], result, false);
  return b.build();
}
