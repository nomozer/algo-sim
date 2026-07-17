import { describe, expect, it } from "vitest";
import { makeAlgorithmModule } from "./index";

/**
 * M14 Task 12 §I1(10) — EXECUTOR TRACE PRESERVATION.
 *
 * Adapter backend (selector.resolve) sinh config AnalysisOk-shape
 * {problem, data:{array, order, labels?}} rồi trả envelope mang concrete id
 * (algorithm.bubble_sort / algorithm.insertion_sort). FE module + engine sắp xếp
 * KHÔNG bị M14 đụng tới. Test này chốt: config dạng adapter chạy đúng qua
 * validateConfig + init hiện có, và trace TẤT ĐỊNH (cùng input → cùng trace).
 * Nếu ai đó lỡ đổi executor/shape, test đỏ.
 */

// Đúng shape mà `resolve` trong backend families/sorting.py phát ra.
function adapterConfig(variant: "bubble" | "insertion", array: number[], order: "asc" | "desc") {
  return {
    problem: { summary: "Sắp xếp dãy số", input: "Dãy số", output: "Dãy đã sắp xếp" },
    data: { array, order },
    _variant: variant, // chỉ để đọc test — module bỏ qua field lạ
  };
}

describe("M14 — executor trace preservation (adapter → engine hiện có)", () => {
  it("config dạng adapter (bubble) qua validateConfig + init, trace không rỗng", () => {
    const mod = makeAlgorithmModule("bubble_sort");
    const r = mod.validateConfig(adapterConfig("bubble", [5, 2, 9, 1], "asc"));
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    const state = mod.init(r.config);
    expect(state.trace.steps.length).toBeGreaterThan(1);
  });

  it("insertion cũng chạy qua engine hiện có", () => {
    const mod = makeAlgorithmModule("insertion_sort");
    const r = mod.validateConfig(adapterConfig("insertion", [8, 3, 5, 2], "asc"));
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(mod.init(r.config).trace.steps.length).toBeGreaterThan(1);
  });

  it("trace TẤT ĐỊNH: cùng array/order → trace GIỐNG HỆT (adapter vs config trực tiếp)", () => {
    const mod = makeAlgorithmModule("bubble_sort");
    const fromAdapter = mod.validateConfig(adapterConfig("bubble", [3, 1, 2], "desc"));
    // config "trực tiếp" kiểu cũ (không đi qua family) — cùng data
    const direct = mod.validateConfig({
      problem: { summary: "x", input: "i", output: "o" },
      data: { array: [3, 1, 2], order: "desc" },
    });
    expect(fromAdapter.ok && direct.ok).toBe(true);
    if (!fromAdapter.ok || !direct.ok) return;
    const t1 = mod.init(fromAdapter.config).trace;
    const t2 = mod.init(direct.config).trace;
    expect(t1).toEqual(t2); // engine tất định — nguồn config không đổi trace
  });

  it("order được tôn trọng: desc khác asc", () => {
    const mod = makeAlgorithmModule("bubble_sort");
    const asc = mod.validateConfig(adapterConfig("bubble", [3, 1, 2], "asc"));
    const desc = mod.validateConfig(adapterConfig("bubble", [3, 1, 2], "desc"));
    if (!asc.ok || !desc.ok) return;
    const lastAsc = mod.init(asc.config).trace.steps.at(-1)!;
    const lastDesc = mod.init(desc.config).trace.steps.at(-1)!;
    expect(lastAsc.snapshot.array).not.toEqual(lastDesc.snapshot.array);
  });
});
