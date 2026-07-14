import type { AnalysisOk, Condition, Trace } from "./types";
import { TraceBuilder, fmt, type WhatIfSwap } from "./trace-builder";

/**
 * Engine tất định — Lớp 1 RULES.
 * R1.2: mỗi thuật toán cài theo phiên bản SGK mô tả; trước khi nộp cần đối
 * chiếu lại số bài + trang SGK (KNTT/Cánh diều) và ghi vào comment từng hàm.
 *
 * Tham số `line` của mỗi step trỏ vào dòng mã giả tương ứng trong
 * core/pseudocode.ts (1-based) để panel mã giả highlight đồng bộ.
 */

/** Tên phần tử trong thuyết minh: có nhãn → "Bình (9)", không → "a[1] = 9". */
function elem(b: TraceBuilder, labels: string[] | null, i: number): string {
  const v = fmt(b.at(i));
  return labels && labels[i] ? `${labels[i]} (${v})` : `a[${i}] = ${v}`;
}

export const OP_TEXT: Record<Condition["op"], string> = {
  ">": "lớn hơn",
  ">=": "lớn hơn hoặc bằng",
  "<": "nhỏ hơn",
  "<=": "nhỏ hơn hoặc bằng",
  "==": "bằng",
  "!=": "khác",
};

function testCondition(v: number, c: Condition): boolean {
  switch (c.op) {
    case ">":
      return v > c.value;
    case ">=":
      return v >= c.value;
    case "<":
      return v < c.value;
    case "<=":
      return v <= c.value;
    case "==":
      return v === c.value;
    case "!=":
      return v !== c.value;
  }
}

/* ── find_max / find_min ─────────────────────────────────── */

function runFindExtreme(a: AnalysisOk, mode: "max" | "min", whatIf?: WhatIfSwap): Trace {
  const b = new TraceBuilder(a.data.array, "engine", whatIf);
  const labels = a.data.labels;
  const varName = mode;
  const word = mode === "max" ? "lớn nhất" : "nhỏ nhất";

  b.setVar(varName, b.at(0));
  b.setVar("vt", 0);
  b.mark(0, "considering");
  b.step(
    [{ type: "assign_var", name: varName, value: b.at(0) }],
    `Bắt đầu: tạm coi phần tử đầu tiên ${elem(b, labels, 0)} là ${word}.`,
    false,
    1,
  );

  let best = 0;
  for (let i = 1; i < b.length; i++) {
    const better = mode === "max" ? b.at(i) > b.at(best) : b.at(i) < b.at(best);
    // M9-S1: narration bước quyết định là CÂU HỎI — không lộ đáp án sớm.
    // Hệ quả thuộc bước kế tiếp (cập nhật) hoặc phản hồi dự đoán/dải nhân quả.
    b.step(
      [
        {
          type: "compare",
          i,
          j: best,
          result: b.at(i) > b.at(best) ? ">" : b.at(i) < b.at(best) ? "<" : "==",
        },
      ],
      `So sánh ${elem(b, labels, i)} với ${varName} = ${fmt(b.at(best))}: ${varName} có được cập nhật không?`,
      true,
      3,
    );
    if (better) {
      // Phần tử tốt-nhất-cũ đã bị vượt qua = loại khỏi vòng ứng viên (xám) —
      // phân biệt rõ vùng ĐÃ DUYỆT với vùng chưa duyệt (M9-S1 §3.1).
      b.mark(best, "eliminated");
      best = i;
      b.setVar(varName, b.at(i));
      b.setVar("vt", i);
      b.mark(i, "considering");
      b.step(
        [
          { type: "assign_var", name: varName, value: b.at(i) },
          { type: "assign_var", name: "vt", value: i },
        ],
        `Cập nhật: ${varName} = ${fmt(b.at(i))} (tại ${elem(b, labels, i)}).`,
        false,
        4,
      );
    } else {
      // Không vượt qua → phần tử này đã duyệt xong, rời vòng ứng viên (xám).
      b.mark(i, "eliminated");
    }
  }

  b.clearMarks();
  b.mark(best, "found");
  const result = `Phần tử ${word} là ${elem(b, labels, best)}, ở vị trí thứ ${best + 1}.`;
  b.step([{ type: "done", result }], `Duyệt hết dãy. ${result}`, false, 5);
  return b.build();
}

/* ── sum_if / count_if ───────────────────────────────────── */

function runAggregateIf(a: AnalysisOk, mode: "sum" | "count", whatIf?: WhatIfSwap): Trace {
  const b = new TraceBuilder(a.data.array, "engine", whatIf);
  const labels = a.data.labels;
  const cond = a.data.condition!;
  const condText = `${OP_TEXT[cond.op]} ${fmt(cond.value)}`;
  const varName = mode === "sum" ? "tong" : "dem";
  const word = mode === "sum" ? "Tổng" : "Số phần tử";

  b.setVar(varName, 0);
  b.step(
    [{ type: "assign_var", name: varName, value: 0 }],
    `Khởi tạo ${varName} = 0. Sẽ duyệt từng phần tử, xét điều kiện "${condText}".`,
    false,
    1,
  );

  let acc = 0;
  for (let i = 0; i < b.length; i++) {
    const match = testCondition(b.at(i), cond);
    // M9-S1: hỏi, không phán trước — đáp án nằm ở bước cộng/đếm kế tiếp.
    b.step(
      [
        {
          type: "compare_value",
          i,
          value: cond.value,
          result: match ? "match" : "no_match",
        },
      ],
      `Xét ${elem(b, labels, i)}: có thỏa điều kiện "${condText}" không?`,
      true,
      3,
    );
    if (!match) b.mark(i, "eliminated"); // không thỏa → xám từ bước sau
    if (match) {
      acc = mode === "sum" ? acc + b.at(i) : acc + 1;
      b.setVar(varName, acc);
      b.mark(i, "found");
      b.step(
        [{ type: "assign_var", name: varName, value: acc }],
        mode === "sum"
          ? `Cộng thêm ${fmt(b.at(i))} → ${varName} = ${fmt(acc)}.`
          : `Đếm thêm 1 → ${varName} = ${acc}.`,
        false,
        4,
      );
    }
  }

  const result = `${word} thỏa điều kiện "${condText}" là ${fmt(acc)}.`;
  b.step([{ type: "done", result }], `Duyệt hết dãy. ${result}`, false, 5);
  return b.build();
}

/* ── linear_search ───────────────────────────────────────── */

function runLinearSearch(a: AnalysisOk, whatIf?: WhatIfSwap): Trace {
  const b = new TraceBuilder(a.data.array, "engine", whatIf);
  const labels = a.data.labels;
  const target = a.data.target!;

  b.setVar("can_tim", target);
  b.step(
    [{ type: "assign_var", name: "can_tim", value: target }],
    `Cần tìm giá trị ${fmt(target)}. Duyệt lần lượt từ đầu dãy.`,
    false,
    1,
  );

  for (let i = 0; i < b.length; i++) {
    const match = b.at(i) === target;
    b.setVar("i", i);
    // M9-S1: câu hỏi thay vì phán trước "khớp!" — đáp án ở bước kế/kết quả.
    b.step(
      [
        {
          type: "compare_value",
          i,
          value: target,
          result: match ? "match" : "no_match",
        },
      ],
      `So sánh ${elem(b, labels, i)} với ${fmt(target)}: có khớp không?`,
      true,
      2,
    );
    if (!match) b.mark(i, "eliminated"); // đã xét, không khớp → xám từ bước sau
    if (match) {
      b.mark(i, "found");
      const result = `Tìm thấy ${fmt(target)} tại vị trí thứ ${i + 1}${labels && labels[i] ? ` (${labels[i]})` : ""}. Số lần so sánh: ${i + 1}.`;
      b.step([{ type: "done", result }], result, false, 3);
      return b.build();
    }
  }

  const result = `Duyệt hết dãy, không có phần tử nào bằng ${fmt(target)}. Số lần so sánh: ${b.length}.`;
  b.step([{ type: "done", result }], result, false, 4);
  return b.build();
}

/* ── binary_search ───────────────────────────────────────── */

function runBinarySearch(a: AnalysisOk, whatIf?: WhatIfSwap): Trace {
  const b = new TraceBuilder(a.data.array, "engine", whatIf);
  const labels = a.data.labels;
  const target = a.data.target!;

  let left = 0;
  let right = b.length - 1;
  let compares = 0;

  b.setVar("can_tim", target);
  b.setVar("trai", left);
  b.setVar("phai", right);
  b.step(
    [{ type: "set_range", left, right }],
    `Cần tìm ${fmt(target)} trong dãy đã sắp thứ tự. Vùng xét ban đầu: từ vị trí 1 đến ${b.length}.`,
    false,
    1,
  );

  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    b.setVar("giua", mid);
    b.step(
      [{ type: "assign_var", name: "giua", value: mid }],
      `Lấy phần tử giữa vùng xét: ${elem(b, labels, mid)} (vị trí thứ ${mid + 1}).`,
      false,
      3,
    );

    compares++;
    if (b.at(mid) === target) {
      b.step(
        [{ type: "compare_value", i: mid, value: target, result: "match" }],
        `So sánh ${fmt(b.at(mid))} với ${fmt(target)}: bằng nhau — tìm thấy!`,
        true,
        4,
      );
      b.mark(mid, "found");
      const result = `Tìm thấy ${fmt(target)} tại vị trí thứ ${mid + 1}. Chỉ mất ${compares} lần so sánh (tuần tự có thể mất tới ${b.length}).`;
      b.step([{ type: "done", result }], result, false, 4);
      return b.build();
    }

    const goRight = b.at(mid) < target;
    b.step(
      [
        {
          type: "compare_value",
          i: mid,
          value: target,
          result: goRight ? "<" : ">",
        },
      ],
      `So sánh ${fmt(b.at(mid))} với ${fmt(target)}: ${
        goRight
          ? `${fmt(b.at(mid))} nhỏ hơn → giá trị cần tìm (nếu có) nằm ở nửa PHẢI. Loại bỏ nửa trái.`
          : `${fmt(b.at(mid))} lớn hơn → giá trị cần tìm (nếu có) nằm ở nửa TRÁI. Loại bỏ nửa phải.`
      }`,
      true,
      goRight ? 5 : 6,
    );

    if (goRight) {
      for (let k = left; k <= mid; k++) b.mark(k, "eliminated");
      left = mid + 1;
    } else {
      for (let k = mid; k <= right; k++) b.mark(k, "eliminated");
      right = mid - 1;
    }
    b.setVar("trai", left);
    b.setVar("phai", right);
    if (left <= right) {
      b.step(
        [{ type: "set_range", left, right }],
        `Vùng xét thu hẹp còn: vị trí ${left + 1} đến ${right + 1}.`,
        false,
        2,
      );
    }
  }

  const result = `Vùng xét rỗng — dãy không chứa ${fmt(target)}. Số lần so sánh: ${compares}.`;
  b.step([{ type: "done", result }], result, false, 7);
  return b.build();
}

/* ── bubble_sort ─────────────────────────────────────────── */

function runBubbleSort(a: AnalysisOk, whatIf?: WhatIfSwap): Trace {
  const b = new TraceBuilder(a.data.array, "engine", whatIf);
  const order = a.data.order ?? "asc";
  const orderText = order === "asc" ? "tăng dần" : "giảm dần";
  const n = b.length;
  let swaps = 0;

  b.step(
    [],
    `Sắp xếp nổi bọt ${orderText}: lặp lại việc so sánh từng cặp kề nhau, đổi chỗ nếu sai thứ tự.`,
    false,
    1,
  );

  for (let i = 0; i < n - 1; i++) {
    b.setVar("luot", i + 1);
    for (let j = 0; j < n - 1 - i; j++) {
      const wrong = order === "asc" ? b.at(j) > b.at(j + 1) : b.at(j) < b.at(j + 1);
      // M9-S1: narration hỏi — quyết định đổi chỗ thuộc bước kế tiếp.
      b.step(
        [
          {
            type: "compare",
            i: j,
            j: j + 1,
            result: b.at(j) > b.at(j + 1) ? ">" : b.at(j) < b.at(j + 1) ? "<" : "==",
          },
        ],
        `So sánh cặp kề (${fmt(b.at(j))}, ${fmt(b.at(j + 1))}): có cần đổi chỗ không?`,
        true,
        3,
      );
      if (wrong) {
        b.swap(j, j + 1);
        swaps++;
        b.step(
          [{ type: "swap", i: j, j: j + 1 }],
          `Đổi chỗ: dãy bây giờ có ${fmt(b.at(j))} đứng trước ${fmt(b.at(j + 1))}.`,
          false,
          4,
        );
      }
    }
    b.mark(n - 1 - i, "sorted");
    b.step(
      [{ type: "mark", index: n - 1 - i, status: "sorted" }],
      `Hết lượt ${i + 1}: phần tử ${fmt(b.at(n - 1 - i))} đã "nổi" về đúng vị trí cuối vùng chưa sắp.`,
      false,
      5,
    );
  }

  b.mark(0, "sorted");
  const result = `Dãy đã sắp xếp ${orderText} xong sau ${swaps} lần đổi chỗ.`;
  b.step([{ type: "done", result }], result, false, 6);
  return b.build();
}

/* ── insertion_sort ──────────────────────────────────────── */

function runInsertionSort(a: AnalysisOk, whatIf?: WhatIfSwap): Trace {
  const b = new TraceBuilder(a.data.array, "engine", whatIf);
  const order = a.data.order ?? "asc";
  const orderText = order === "asc" ? "tăng dần" : "giảm dần";
  const n = b.length;

  b.mark(0, "sorted");
  b.step(
    [{ type: "mark", index: 0, status: "sorted" }],
    `Sắp xếp chèn ${orderText}: coi phần tử đầu là "phần đã sắp"; lần lượt chèn từng phần tử sau vào đúng chỗ.`,
    false,
    1,
  );

  for (let i = 1; i < n; i++) {
    const key = b.at(i);
    const keyId = b.idAt(i); // định danh "quân bài" đang rút ra khỏi dãy
    b.setVar("gia_tri_chen", key);
    b.step(
      [{ type: "assign_var", name: "gia_tri_chen", value: key }],
      `Lấy phần tử a[${i}] = ${fmt(key)} để chèn vào phần đã sắp bên trái.`,
      true,
      3,
    );

    let j = i - 1;
    while (j >= 0 && (order === "asc" ? b.at(j) > key : b.at(j) < key)) {
      // M9-S1: hỏi trước — việc dời hiện ra ở bước shift kế tiếp.
      b.step(
        [
          {
            type: "compare",
            i: j,
            j: i,
            result: b.at(j) > key ? ">" : "<",
          },
        ],
        `So sánh ${fmt(b.at(j))} với giá trị chèn ${fmt(key)}: có phải dời ${fmt(b.at(j))} sang phải không?`,
        false,
        4,
      );
      b.set(j + 1, b.at(j));
      // "ô trống" (mang định danh quân bài đang rút) lùi từ j+1 về j —
      // giữ ids là hoán vị để renderer hoạt cảnh đúng, không trùng key
      b.moveId(j, j + 1);
      b.setIdAt(j, keyId);
      b.step([{ type: "shift", from: j, to: j + 1 }], `Dời xong, ô trống lùi về vị trí ${j + 1}.`, false, 5);
      j--;
    }
    if (j >= 0) {
      // Cùng dạng câu hỏi — đáp án ("dừng dời") hiện ở bước chèn kế tiếp.
      b.step(
        [
          {
            type: "compare",
            i: j,
            j: i,
            result: b.at(j) > key ? ">" : b.at(j) < key ? "<" : "==",
          },
        ],
        `So sánh ${fmt(b.at(j))} với giá trị chèn ${fmt(key)}: có phải dời ${fmt(b.at(j))} sang phải không?`,
        false,
        4,
      );
    }
    b.set(j + 1, key);
    b.setIdAt(j + 1, keyId);
    for (let k = 0; k <= i; k++) b.mark(k, "sorted");
    b.step(
      [{ type: "insert", index: j + 1, value: key }],
      `Chèn ${fmt(key)} vào vị trí thứ ${j + 2}. Phần đã sắp dài thêm một phần tử.`,
      false,
      6,
    );
  }

  const result = `Dãy đã sắp xếp ${orderText} xong bằng phương pháp chèn.`;
  b.step([{ type: "done", result }], result, false, 7);
  return b.build();
}

/* ── dispatch ────────────────────────────────────────────── */

export function runAlgorithm(analysis: AnalysisOk, whatIf?: WhatIfSwap): Trace {
  switch (analysis.algorithm_id) {
    case "find_max":
      return runFindExtreme(analysis, "max", whatIf);
    case "find_min":
      return runFindExtreme(analysis, "min", whatIf);
    case "sum_if":
      return runAggregateIf(analysis, "sum", whatIf);
    case "count_if":
      return runAggregateIf(analysis, "count", whatIf);
    case "linear_search":
      return runLinearSearch(analysis, whatIf);
    case "binary_search":
      return runBinarySearch(analysis, whatIf);
    case "bubble_sort":
      return runBubbleSort(analysis, whatIf);
    case "insertion_sort":
      return runInsertionSort(analysis, whatIf);
  }
}
