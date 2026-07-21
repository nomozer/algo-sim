import { describe, expect, it } from "vitest";
import { SAMPLES } from "../data/samples";
import { runAlgorithm } from "./algorithms";

/**
 * Test engine tất định: chạy cả 8 bài mẫu, đối chiếu kết quả cuối
 * với đáp án tính độc lập; kiểm tra bất biến của trace (index liên tục,
 * ids là hoán vị) và cơ chế fork what-if (R3.3).
 */

describe("engine 8 thuật toán (bài mẫu)", () => {
  for (const sample of SAMPLES) {
    it(`${sample.algorithmId} (${sample.id})`, () => {
      const trace = runAlgorithm(sample.analysis);
      const steps = trace.steps;
      const last = steps[steps.length - 1];
      const a = sample.analysis;

      // Bất biến chung của trace
      expect(steps.length).toBeGreaterThan(2);
      expect(last.events.some((e) => e.type === "done")).toBe(true);
      steps.forEach((s, i) => expect(s.index).toBe(i));
      for (const s of steps) {
        expect(s.snapshot.array).toHaveLength(a.data.array.length);
        // ids luôn là hoán vị của 0..n-1 — nuôi hoạt cảnh trượt cột
        expect(new Set(s.snapshot.ids).size).toBe(a.data.array.length);
      }

      // Kết quả cuối đối chiếu với đáp án tính độc lập
      const finalArr = last.snapshot.array;
      switch (a.algorithm_id) {
        case "bubble_sort":
        case "insertion_sort": {
          expect(finalArr).toEqual([...a.data.array].sort((x, y) => x - y));
          break;
        }
        case "find_max":
          expect(last.snapshot.vars["max"]).toBe(Math.max(...a.data.array));
          break;
        case "find_min":
          expect(last.snapshot.vars["min"]).toBe(Math.min(...a.data.array));
          break;
        case "sum_if":
          expect(last.snapshot.vars["tong"]).toBe(
            a.data.array.filter((v) => v >= a.data.condition!.value).reduce((s, v) => s + v, 0),
          );
          break;
        case "count_if":
          expect(last.snapshot.vars["dem"]).toBe(
            a.data.array.filter((v) => v >= a.data.condition!.value).length,
          );
          break;
        case "linear_search":
        case "binary_search": {
          const foundIdx = Object.entries(last.snapshot.marks).find(([, m]) => m === "found");
          expect(foundIdx).toBeDefined();
          expect(Number(foundIdx![0])).toBe(a.data.array.indexOf(a.data.target!));
          break;
        }
      }
    });
  }
});

describe("selection_sort (M17 W1) — oracle độc lập + bất biến trace", () => {
  const cfg = (array: number[], order: "asc" | "desc"): Parameters<typeof runAlgorithm>[0] => ({
    status: "ok",
    problem: { summary: "Sắp xếp chọn", input: "Dãy số", output: "Dãy đã sắp" },
    algorithm_id: "selection_sort",
    data: { array, labels: null, target: null, condition: null, order },
    data_generated: false,
    notes: null,
  });

  const CASES: { array: number[]; order: "asc" | "desc" }[] = [
    { array: [9, 4, 7, 2, 6], order: "asc" },
    { array: [5, 3, 5, 2, 3], order: "asc" }, // phần tử trùng
    { array: [1, 2, 3, 4], order: "asc" }, // đã sắp sẵn — 0 lần đổi chỗ
    { array: [3, 8, 1, 9, 5], order: "desc" },
    { array: [2, 1], order: "asc" }, // biên nhỏ nhất cho phép
  ];

  for (const c of CASES) {
    it(`[${c.array.join(",")}] ${c.order}: kết quả cuối khớp oracle sort()`, () => {
      const trace = runAlgorithm(cfg(c.array, c.order));
      const steps = trace.steps;
      const last = steps[steps.length - 1];
      // oracle độc lập
      const expected = [...c.array].sort((x, y) => (c.order === "asc" ? x - y : y - x));
      expect(last.snapshot.array).toEqual(expected);
      // bất biến trace: index liên tục, ids là hoán vị, done tồn tại
      steps.forEach((s, i) => expect(s.index).toBe(i));
      for (const s of steps) expect(new Set(s.snapshot.ids).size).toBe(c.array.length);
      expect(last.events.some((e) => e.type === "done")).toBe(true);
      // toàn bộ phần tử được đánh dấu sorted ở bước cuối
      expect(Object.keys(last.snapshot.marks)).toHaveLength(c.array.length);
    });
  }

  it("trace mang đủ event cơ chế: set_range, compare, assign_var, swap, mark", () => {
    const trace = runAlgorithm(cfg([9, 4, 7, 2, 6], "asc"));
    const types = new Set(trace.steps.flatMap((s) => s.events.map((e) => e.type)));
    for (const t of ["set_range", "compare", "assign_var", "swap", "mark", "done"]) {
      expect(types.has(t as never), `thiếu event ${t}`).toBe(true);
    }
  });

  it("dãy đã sắp: không có swap nào (chọn xong đứng nguyên)", () => {
    const trace = runAlgorithm(cfg([1, 2, 3, 4], "asc"));
    expect(trace.steps.some((s) => s.events.some((e) => e.type === "swap"))).toBe(false);
  });
});

describe("fork what-if (R3.3)", () => {
  const sample = SAMPLES.find((s) => s.algorithmId === "bubble_sort")!;
  const k = 5;
  const n = sample.analysis.data.array.length;

  it("đoạn trước bước k trùng khớp dòng chính (tất định)", () => {
    const main = runAlgorithm(sample.analysis);
    const fork = runAlgorithm(sample.analysis, { afterStep: k, i: 0, j: n - 1 });
    for (let s = 0; s <= k; s++) {
      expect(fork.steps[s].snapshot).toEqual(main.steps[s].snapshot);
    }
  });

  it("bước k+1 là can thiệp của học sinh, đổi chỗ đúng hai phần tử", () => {
    const main = runAlgorithm(sample.analysis);
    const fork = runAlgorithm(sample.analysis, { afterStep: k, i: 0, j: n - 1 });
    const before = main.steps[k].snapshot.array;
    const after = fork.steps[k + 1].snapshot.array;
    expect(fork.steps[k + 1].userAction).toBe(true);
    expect(after[0]).toBe(before[n - 1]);
    expect(after[n - 1]).toBe(before[0]);
  });

  it("nhánh chạy tiếp đến done với index liên tục", () => {
    const fork = runAlgorithm(sample.analysis, { afterStep: k, i: 0, j: n - 1 });
    expect(fork.steps.length).toBeGreaterThan(k + 2);
    expect(fork.steps[fork.steps.length - 1].events.some((e) => e.type === "done")).toBe(true);
    fork.steps.forEach((s, i) => expect(s.index).toBe(i));
  });
});
