import { describe, expect, it } from "vitest";
import { makeAlgorithmModule } from "./index";
import { activeTrace, type AlgorithmSimState } from "./model";
import { consequenceOf, decisionPointOf } from "./decision";
import type { AlgorithmId } from "../../../core/types";

/**
 * M9-S1 — ĐIỂM QUYẾT ĐỊNH THEO CƠ CHẾ ẨN của từng thuật toán.
 *
 * Nguyên tắc khoá ở đây:
 * 1. Mỗi thuật toán được hỏi ĐÚNG cơ chế của nó (cập nhật max? cộng vào tổng?
 *    nửa nào bị loại? có đổi chỗ?...), không phải một câu hỏi chung chung.
 * 2. Đáp án chuẩn (expectedId) DẪN XUẤT từ sự kiện THẬT của trace — không đoán.
 * 3. Bằng chứng (evidence) chứa SỐ LIỆU THẬT: giá trị so sánh, biến trước → sau.
 * 4. KHÔNG lộ đáp án sớm: narration của bước quyết định là CÂU HỎI, phần
 *    "chuyện gì xảy ra" thuộc bước KẾ TIẾP hoặc phản hồi sau khi dự đoán.
 * 5. Dự đoán không bao giờ đụng canonical state.
 */

function stateAt(algorithmId: AlgorithmId, data: Record<string, unknown>, cursor: number): AlgorithmSimState {
  const mod = makeAlgorithmModule(algorithmId);
  const r = mod.validateConfig({ problem: {}, algorithm_id: algorithmId, data, data_generated: false, notes: null });
  if (!r.ok) throw new Error(r.error);
  const s = mod.init(r.config);
  return mod.timeline!.goToStep(s, cursor) as AlgorithmSimState;
}

/* ── (1) find_max — cơ chế: max đang chạy có được cập nhật không ─────────── */

describe("find_max — cập nhật max đang chạy", () => {
  const DATA = { array: [7.5, 9, 6] };
  // trace: s0 init(max=7,5) · s1 compare(9 vs 7,5) · s2 cập nhật · s3 compare(6 vs 9) · s4 done

  it("ở phép so sánh CÓ cập nhật: hỏi đúng cơ chế, đáp án 'yes' từ trace", () => {
    const d = decisionPointOf(stateAt("find_max", DATA, 1))!;
    expect(d).not.toBeNull();
    expect(d.question).toContain("cập nhật");
    expect(d.question.toLowerCase()).toContain("max");
    expect(d.options.map((o) => o.id)).toEqual(["yes", "no"]);
    expect(d.expectedId).toBe("yes");
    // bằng chứng nhân quả có số liệu thật: 9 so với 7,5 và max trước → sau
    expect(d.evidence).toContain("9");
    expect(d.evidence).toContain("7,5");
    expect(d.evidence).toContain("max");
  });

  it("ở phép so sánh KHÔNG cập nhật: đáp án 'no', bằng chứng nói max giữ nguyên", () => {
    const d = decisionPointOf(stateAt("find_max", DATA, 3))!;
    expect(d.expectedId).toBe("no");
    expect(d.evidence).toContain("giữ nguyên");
    expect(d.evidence).toContain("9"); // max hiện tại
  });

  it("KHÔNG lộ đáp án: narration bước quyết định là câu hỏi, không nói 'sẽ cập nhật'", () => {
    const s = stateAt("find_max", DATA, 1);
    const narration = activeTrace(s).steps[1].narration;
    expect(narration).not.toContain("sẽ cập nhật");
    expect(narration).not.toContain("giữ nguyên");
    expect(narration.trim().endsWith("không?")).toBe(true);
  });

  it("bước không phải điểm quyết định (init, done) → null", () => {
    expect(decisionPointOf(stateAt("find_max", DATA, 0))).toBeNull();
    expect(decisionPointOf(stateAt("find_max", DATA, 4))).toBeNull();
  });
});

/* ── (2) find_min — gương của find_max quanh min ──────────────────────────── */

describe("find_min — cập nhật min đang chạy", () => {
  const DATA = { array: [5, 3, 4] };

  it("hỏi về min; đáp án từ trace ở cả hai nhánh", () => {
    const dYes = decisionPointOf(stateAt("find_min", DATA, 1))!;
    expect(dYes.question.toLowerCase()).toContain("min");
    expect(dYes.expectedId).toBe("yes");

    const dNo = decisionPointOf(stateAt("find_min", DATA, 3))!;
    expect(dNo.expectedId).toBe("no");
  });
});

/* ── (3) sum_if — cơ chế: giá trị có được CỘNG vào tổng không ─────────────── */

describe("sum_if — cộng vào biến tích luỹ", () => {
  const DATA = { array: [5, 8, 3], condition: { op: ">", value: 4 } };
  // s0 init(tong=0) · s1 xét 5 · s2 tong=5 · s3 xét 8 · s4 tong=13 · s5 xét 3 · s6 done

  it("giá trị thỏa điều kiện: hỏi 'có được cộng vào tổng không', đáp 'yes', evidence tổng trước → sau", () => {
    const d = decisionPointOf(stateAt("sum_if", DATA, 3))!;
    expect(d.question).toContain("cộng vào tổng");
    expect(d.expectedId).toBe("yes");
    expect(d.evidence).toContain("8");
    expect(d.evidence).toContain("5"); // tổng trước
    expect(d.evidence).toContain("13"); // tổng sau
  });

  it("giá trị KHÔNG thỏa: đáp 'no', evidence nói tổng giữ nguyên với số thật", () => {
    const d = decisionPointOf(stateAt("sum_if", DATA, 5))!;
    expect(d.expectedId).toBe("no");
    expect(d.evidence).toContain("13");
    expect(d.evidence).toContain("giữ nguyên");
  });

  it("narration bước xét là câu hỏi — không nói trước 'thỏa/không thỏa'", () => {
    const narration = activeTrace(stateAt("sum_if", DATA, 1)).steps[1].narration;
    expect(narration).not.toContain("thỏa điều kiện.");
    expect(narration).not.toContain("bỏ qua");
    expect(narration.trim().endsWith("không?")).toBe(true);
  });
});

/* ── (4) count_if — cơ chế: biến đếm có tăng không ────────────────────────── */

describe("count_if — biến đếm tăng hay giữ nguyên", () => {
  const DATA = { array: [9, 2], condition: { op: ">=", value: 8 } };
  // s0 init(dem=0) · s1 xét 9 · s2 dem=1 · s3 xét 2 · s4 done

  it("hỏi về biến đếm; hai nhánh đáp án đều từ trace; evidence đếm trước → sau", () => {
    const dYes = decisionPointOf(stateAt("count_if", DATA, 1))!;
    expect(dYes.question).toContain("đếm");
    expect(dYes.expectedId).toBe("yes");
    expect(dYes.evidence).toContain("0");
    expect(dYes.evidence).toContain("1");

    const dNo = decisionPointOf(stateAt("count_if", DATA, 3))!;
    expect(dNo.expectedId).toBe("no");
  });
});

/* ── (5) linear_search — cơ chế: đã tìm thấy chưa ─────────────────────────── */

describe("linear_search — kiểm tra tuần tự từng phần tử", () => {
  const DATA = { array: [4, 9, 7], target: 9 };
  // s0 init · s1 xét a[0]=4 · s2 xét a[1]=9 (khớp) · s3 done

  it("phần tử không khớp: đáp 'no'; phần tử khớp: đáp 'yes' — đều từ trace", () => {
    const dNo = decisionPointOf(stateAt("linear_search", DATA, 1))!;
    expect(dNo.question).toContain("tìm");
    expect(dNo.expectedId).toBe("no");

    const dYes = decisionPointOf(stateAt("linear_search", DATA, 2))!;
    expect(dYes.expectedId).toBe("yes");
    expect(dYes.evidence).toContain("9");
  });

  it("narration bước xét không nói trước 'khớp!'", () => {
    const narration = activeTrace(stateAt("linear_search", DATA, 2)).steps[2].narration;
    expect(narration).not.toContain("khớp!");
    expect(narration.trim().endsWith("không?")).toBe(true);
  });
});

/* ── (6) binary_search — cơ chế: nửa nào bị loại ──────────────────────────── */

describe("binary_search — loại nửa vùng tìm kiếm", () => {
  const DATA = { array: [1, 3, 5, 7, 9, 11, 13], target: 3 };
  // s0 set_range · s1 giua=3 (giá trị 7) · s2 so sánh (7>3 → loại nửa PHẢI)
  // · s3 set_range(0..2) · s4 giua=1 (giá trị 3) · s5 so sánh match · ...

  it("điểm quyết định là bước LẤY MID (narration trung lập sẵn); 3 lựa chọn", () => {
    const d = decisionPointOf(stateAt("binary_search", DATA, 1))!;
    expect(d).not.toBeNull();
    expect(d.question).toContain("bị loại");
    expect(d.options.map((o) => o.id).sort()).toEqual(["found", "left", "right"]);
  });

  it("mid > target → loại nửa PHẢI (đáp án từ sự kiện compare_value kế tiếp)", () => {
    const d = decisionPointOf(stateAt("binary_search", DATA, 1))!;
    expect(d.expectedId).toBe("right");
    expect(d.evidence).toContain("7");
    expect(d.evidence).toContain("3");
  });

  it("mid == target → 'found'", () => {
    const d = decisionPointOf(stateAt("binary_search", DATA, 4))!;
    expect(d.expectedId).toBe("found");
  });

  it("mid < target → loại nửa TRÁI", () => {
    const d = decisionPointOf(stateAt("binary_search", { array: [1, 3, 5, 7, 9, 11, 13], target: 11 }, 1))!;
    expect(d.expectedId).toBe("left");
  });

  it("bước so sánh (đã lộ kết quả trong narration) KHÔNG phải điểm hỏi", () => {
    expect(decisionPointOf(stateAt("binary_search", DATA, 2))).toBeNull();
  });
});

/* ── (7) bubble_sort — cơ chế: cặp kề có đổi chỗ không ────────────────────── */

describe("bubble_sort — quyết định đổi chỗ cặp kề", () => {
  const DATA = { array: [1, 3, 2], order: "asc" };
  // s0 intro · s1 compare(1,3): đúng thứ tự · s2 compare(3,2): sai → s3 swap · ...

  it("hỏi 'có đổi chỗ không'; cả hai nhánh đáp án từ sự kiện swap kế tiếp", () => {
    const dNo = decisionPointOf(stateAt("bubble_sort", DATA, 1))!;
    expect(dNo.question).toContain("đổi chỗ");
    expect(dNo.expectedId).toBe("no");

    const dYes = decisionPointOf(stateAt("bubble_sort", DATA, 2))!;
    expect(dYes.expectedId).toBe("yes");
    expect(dYes.evidence).toContain("3");
    expect(dYes.evidence).toContain("2");
  });

  it("narration bước so sánh là câu hỏi — không nói trước 'đổi chỗ.'/'giữ nguyên.'", () => {
    const narration = activeTrace(stateAt("bubble_sort", DATA, 2)).steps[2].narration;
    expect(narration).not.toContain("sai thứ tự");
    expect(narration).not.toContain("giữ nguyên");
    expect(narration.trim().endsWith("không?")).toBe(true);
  });
});

/* ── (8) insertion_sort — cơ chế: dời sang phải hay dừng để chèn ──────────── */

describe("insertion_sort — quyết định dời phần tử", () => {
  const DATA = { array: [5, 2, 4], order: "asc" };
  // i=1 (key=2): s2 compare(5 vs key) → s3 shift → s4 insert
  // i=2 (key=4): s6 compare(5 vs key) → s7 shift → s8 compare(2 vs key, dừng) → s9 insert

  it("hỏi về việc DỜI sang phải; đáp án từ sự kiện shift kế tiếp", () => {
    const dYes = decisionPointOf(stateAt("insertion_sort", DATA, 2))!;
    expect(dYes.question).toContain("dời");
    expect(dYes.expectedId).toBe("yes");
  });

  it("phép so sánh DỪNG dời (kế tiếp là chèn) → đáp 'no'", () => {
    const d = decisionPointOf(stateAt("insertion_sort", DATA, 8))!;
    expect(d.expectedId).toBe("no");
    expect(d.evidence).toContain("chèn");
  });

  it("narration bước so sánh không nói trước 'dời sang phải'", () => {
    const narration = activeTrace(stateAt("insertion_sort", DATA, 2)).steps[2].narration;
    expect(narration).not.toContain("→ dời");
    expect(narration.trim().endsWith("không?")).toBe(true);
  });
});

/* ── (9)(10)(13)(18) qua module.predict — hợp đồng và độ thuần ───────────── */

describe("module.predict dùng decisionPointOf — thuần, đúng trace, có mặc định an toàn", () => {
  const mod = makeAlgorithmModule("binary_search");
  const DATA = { array: [1, 3, 5, 7, 9, 11, 13], target: 3 };

  function init(cursor: number): AlgorithmSimState {
    const r = mod.validateConfig({ problem: {}, algorithm_id: "binary_search", data: DATA, data_generated: false, notes: null });
    if (!r.ok) throw new Error(r.error);
    return mod.timeline!.goToStep(mod.init(r.config), cursor) as AlgorithmSimState;
  }

  it("challenge/check khớp decisionPointOf; đúng và sai đều KHÔNG đụng canonical state", () => {
    const s = init(1);
    const before = JSON.stringify(s);

    const ch = mod.predict!.challenge(s)!;
    expect(ch.options.map((o) => o.id).sort()).toEqual(["found", "left", "right"]);

    const good = mod.predict!.check(s, "right");
    expect(good.verdict).toBe("correct");
    const bad = mod.predict!.check(s, "left");
    expect(bad.verdict).toBe("incorrect");
    expect(bad.expectedId).toBe("right");
    // phản hồi mang bằng chứng nhân quả tất định
    expect(bad.message).toContain("7");

    expect(JSON.stringify(s)).toBe(before);
  });

  it("không có điểm quyết định → không có challenge (không hỏi vu vơ)", () => {
    expect(mod.predict!.challenge(init(0))).toBeNull();
    const done = init(999); // clamp về bước cuối (done)
    expect(mod.predict!.challenge(done)).toBeNull();
  });
});

/* ── consequenceOf — mặt "chuyện gì vừa xảy ra" của cùng dữ liệu ──────────── */

describe("consequenceOf — câu nhân quả cho bước hệ quả", () => {
  it("find_max: bước cập nhật nói rõ vì-sao với số liệu thật (7,5 → 9)", () => {
    const c = consequenceOf(stateAt("find_max", { array: [7.5, 9, 6] }, 2))!;
    expect(c).toContain("9");
    expect(c).toContain("7,5");
    expect(c).toContain("max");
  });

  it("bubble_sort: bước swap nói rõ vì sao đổi chỗ", () => {
    const c = consequenceOf(stateAt("bubble_sort", { array: [1, 3, 2], order: "asc" }, 3))!;
    expect(c).toContain("đổi chỗ");
  });

  it("bước không phải hệ quả của quyết định → null", () => {
    expect(consequenceOf(stateAt("find_max", { array: [7.5, 9, 6] }, 0))).toBeNull();
  });
});
