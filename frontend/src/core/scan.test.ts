import { describe, expect, it } from "vitest";
import { runScan, validateScanSpec, type ScanSpec } from "./scan";
import { runAlgorithm } from "./algorithms";
import type { AlgorithmId, AnalysisOk, Condition, Mark, Trace } from "./types";

/**
 * M12 — Declarative Bounded Scan Proof.
 *
 * Chứng minh MỘT interpreter quét (engine sở hữu) tái tạo ĐÚNG NGỮ NGHĨA của
 * ba engine specialized (find_max, count_if, linear_search) — các engine đó
 * giữ nguyên làm ORACLE. Parity định nghĩa TƯỜNG MINH trên phần ngữ nghĩa,
 * KHÔNG đòi trùng narration/line (đó là trình bày, không phải chân lý):
 *   - decisions: chuỗi kết quả so sánh mỗi phần tử;
 *   - finalMarks: vùng đã-loại / tìm-thấy ở bước cuối;
 *   - stepCount: số bước (cấu trúc trace khớp).
 * Cộng với đối chứng ĐỘC LẬP (max/count/index tính tay).
 */

function analysis(id: AlgorithmId, array: number[], extra: Partial<{ target: number; condition: Condition }> = {}): AnalysisOk {
  return {
    status: "ok",
    problem: { summary: "", input: "", output: "" },
    algorithm_id: id,
    data: {
      array,
      labels: null,
      target: extra.target ?? null,
      condition: extra.condition ?? null,
      order: null,
    },
    data_generated: false,
    notes: null,
  };
}

/** Chuỗi quyết định so sánh theo thứ tự (name/narration-agnostic). */
function decisions(t: Trace): string[] {
  const out: string[] = [];
  for (const s of t.steps)
    for (const e of s.events) {
      if (e.type === "compare") out.push(e.result);
      else if (e.type === "compare_value") out.push(e.result);
    }
  return out;
}

/** Marks ở bước cuối, sắp theo chỉ số — vùng đã-loại / tìm-thấy. */
function finalMarks(t: Trace): [number, Mark][] {
  const marks = t.steps[t.steps.length - 1].snapshot.marks;
  return Object.entries(marks)
    .map(([k, v]) => [Number(k), v] as [number, Mark])
    .sort((a, b) => a[0] - b[0]);
}

/** Bộ ba chiều parity đã định nghĩa. */
function parity(t: Trace) {
  return { decisions: decisions(t), finalMarks: finalMarks(t), stepCount: t.steps.length };
}

describe("M12 bounded scan — parity với engine specialized (oracle)", () => {
  it("find_max: interpreter khớp ngữ nghĩa runAlgorithm(find_max)", () => {
    const array = [3, 7, 2, 9, 4];
    const oracle = runAlgorithm(analysis("find_max", array));
    const spec: ScanSpec = {
      scan_version: "1.0",
      array,
      seed: { from: "first_element", varName: "max", trackIndexVar: "vt" },
      compare: { kind: "to_accumulator", op: ">" },
      update: { kind: "replace_with_current" },
      marking: "running_winner",
      stop: "end_of_array",
    };
    const got = runScan(spec);

    expect(parity(got)).toEqual(parity(oracle));
    // đối chứng độc lập: đỉnh ở đúng vị trí max
    const maxIdx = array.indexOf(Math.max(...array));
    expect(finalMarks(got)).toEqual([[maxIdx, "found"]]);
  });

  it("count_if: interpreter khớp ngữ nghĩa runAlgorithm(count_if)", () => {
    const array = [5, 9, 6, 8, 4, 10, 7];
    const condition: Condition = { op: ">=", value: 8 };
    const oracle = runAlgorithm(analysis("count_if", array, { condition }));
    const spec: ScanSpec = {
      scan_version: "1.0",
      array,
      seed: { from: "constant", value: 0, varName: "dem" },
      compare: { kind: "to_constant", op: ">=", value: 8 },
      update: { kind: "increment" },
      marking: "match_highlight",
      stop: "end_of_array",
    };
    const got = runScan(spec);

    expect(parity(got)).toEqual(parity(oracle));
    // đối chứng độc lập: số phần tử ≥ 8 được đánh dấu "found"
    const want = array.filter((x) => x >= 8).length;
    expect(finalMarks(got).filter(([, m]) => m === "found").length).toBe(want);
  });

  it("sum_if: cùng interpreter, khác update (add_current) khớp runAlgorithm(sum_if)", () => {
    const array = [5, 9, 6, 8, 4, 10, 7];
    const condition: Condition = { op: ">=", value: 8 };
    const oracle = runAlgorithm(analysis("sum_if", array, { condition }));
    const spec: ScanSpec = {
      scan_version: "1.0",
      array,
      seed: { from: "constant", value: 0, varName: "tong" },
      compare: { kind: "to_constant", op: ">=", value: 8 },
      update: { kind: "add_current" },
      marking: "match_highlight",
      stop: "end_of_array",
    };
    expect(parity(runScan(spec))).toEqual(parity(oracle));
  });

  it("linear_search (tìm thấy): stop=first_match khớp runAlgorithm(linear_search)", () => {
    const array = [4, 8, 15, 16, 23, 42];
    const target = 16;
    const oracle = runAlgorithm(analysis("linear_search", array, { target }));
    const spec: ScanSpec = {
      scan_version: "1.0",
      array,
      seed: { from: "constant", value: target, varName: "can_tim" },
      compare: { kind: "to_constant", op: "==", value: target },
      update: { kind: "none" },
      marking: "match_highlight",
      stop: "first_match",
    };
    const got = runScan(spec);

    expect(parity(got)).toEqual(parity(oracle));
    expect(finalMarks(got)).toEqual([
      [0, "eliminated"],
      [1, "eliminated"],
      [2, "eliminated"],
      [3, "found"],
    ]);
  });

  it("linear_search (không thấy): quét hết, mọi ô eliminated", () => {
    const array = [4, 8, 15, 16, 23, 42];
    const target = 99;
    const oracle = runAlgorithm(analysis("linear_search", array, { target }));
    const spec: ScanSpec = {
      scan_version: "1.0",
      array,
      seed: { from: "constant", value: target, varName: "can_tim" },
      compare: { kind: "to_constant", op: "==", value: target },
      update: { kind: "none" },
      marking: "match_highlight",
      stop: "first_match",
    };
    expect(parity(runScan(spec))).toEqual(parity(oracle));
  });
});

describe("M12 validateScanSpec — chặn spec lạ/không an toàn/mơ hồ", () => {
  const VALID: ScanSpec = {
    scan_version: "1.0",
    array: [3, 7, 2],
    seed: { from: "first_element", varName: "max", trackIndexVar: "vt" },
    compare: { kind: "to_accumulator", op: ">" },
    update: { kind: "replace_with_current" },
    marking: "running_winner",
    stop: "end_of_array",
  };
  const bad = (o: unknown) => expect(validateScanSpec(o).ok).toBe(false);

  it("spec hợp lệ được chấp nhận", () => {
    expect(validateScanSpec(VALID).ok).toBe(true);
  });
  it("scan_version lạ bị reject", () => bad({ ...VALID, scan_version: "2.0" }));
  it("mảng rỗng bị reject", () => bad({ ...VALID, array: [] }));
  it("mảng chứa phần tử không phải số bị reject", () => bad({ ...VALID, array: [1, "x", 3] }));
  it("khóa lạ ở cấp cao nhất bị reject", () => bad({ ...VALID, secret: 1 }));
  it("op so sánh lạ bị reject", () => bad({ ...VALID, compare: { kind: "to_accumulator", op: "≈" } }));
  it("marking lạ bị reject", () => bad({ ...VALID, marking: "rainbow" }));
  it("stop lạ bị reject", () => bad({ ...VALID, stop: "forever" }));
  it("update kind lạ bị reject", () => bad({ ...VALID, update: { kind: "explode" } }));
  it("seed.from lạ bị reject", () => bad({ ...VALID, seed: { from: "middle", varName: "m" } }));
  it("to_constant thiếu value số bị reject", () =>
    bad({ ...VALID, compare: { kind: "to_constant", op: "==" } }));
  it("seed constant thiếu value số bị reject", () =>
    bad({ ...VALID, seed: { from: "constant", varName: "x" } }));
  it("khóa lạ trong seed bị reject", () =>
    bad({ ...VALID, seed: { from: "first_element", varName: "m", junk: 1 } }));
  it("varName rỗng bị reject", () =>
    bad({ ...VALID, seed: { from: "first_element", varName: "" } }));
  it("labels sai độ dài bị reject", () => bad({ ...VALID, labels: ["chỉ một"] }));

  // ── Coherence: giữ họ = quét trên GIÁ TRỊ phần tử, chống cấu hình vô nghĩa ──
  it("running_winner mà update không phải replace bị reject (winner vô nghĩa)", () =>
    bad({ ...VALID, update: { kind: "increment" } }));
  it("to_accumulator mà update none bị reject (so với hằng cố định = nên dùng to_constant)", () =>
    bad({ ...VALID, update: { kind: "none" } }));

  it("spec count_if / linear_search hợp lệ được chấp nhận", () => {
    expect(
      validateScanSpec({
        scan_version: "1.0",
        array: [5, 9, 6],
        seed: { from: "constant", value: 0, varName: "dem" },
        compare: { kind: "to_constant", op: ">=", value: 8 },
        update: { kind: "increment" },
        marking: "match_highlight",
        stop: "end_of_array",
      }).ok,
    ).toBe(true);
    expect(
      validateScanSpec({
        scan_version: "1.0",
        array: [4, 8, 15],
        seed: { from: "constant", value: 16, varName: "can_tim" },
        compare: { kind: "to_constant", op: "==", value: 16 },
        update: { kind: "none" },
        marking: "match_highlight",
        stop: "first_match",
      }).ok,
    ).toBe(true);
  });
});

describe("M12 tất định + biên non-Turing", () => {
  const spec: ScanSpec = {
    scan_version: "1.0",
    array: [3, 7, 2, 9, 4, 9, 1],
    seed: { from: "first_element", varName: "max", trackIndexVar: "vt" },
    compare: { kind: "to_accumulator", op: ">" },
    update: { kind: "replace_with_current" },
    marking: "running_winner",
    stop: "end_of_array",
  };
  it("chạy lại cùng spec → Trace y hệt (tất định)", () => {
    expect(runScan(spec)).toEqual(runScan(spec));
  });
  it("số bước bị chặn: ≤ 2·n + 2 (một compare + tối đa một update mỗi phần tử)", () => {
    const t = runScan(spec);
    expect(t.steps.length).toBeLessThanOrEqual(2 * spec.array.length + 2);
  });
});
