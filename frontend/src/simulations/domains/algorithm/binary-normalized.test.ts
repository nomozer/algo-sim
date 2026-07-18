import { describe, expect, it } from "vitest";
import { makeAlgorithmModule } from "./index";

/**
 * M15 Task 8 — proof thứ tư của khóa 7 (binary_search normalize-not-refuse):
 * trace CHẠY TRÊN normalized input. Backend đã chuẩn hoá dãy chưa sắp trước
 * khi phát envelope (xem test_algo_entry_policy_locks.py — 3 proof kia: normalize
 * tất định, label giữ liên kết theo giá trị, annotation sư phạm). Test này khoá
 * phần còn lại ở FE: config ĐÃ NORMALIZE (array [3,7,9], target 7) → engine hiện
 * có (core/algorithms.ts, không sửa) chạy trace trên dãy đã sắp, mọi snapshot
 * đều thấy dãy đã sắp (binary_search không đổi chỗ phần tử — chỉ mark/thu hẹp
 * vùng xét), và tìm thấy 7.
 */

function normalizedBinarySearchConfig() {
  return {
    problem: { summary: "Tìm kiếm nhị phân", input: "Dãy đã sắp", output: "Vị trí tìm thấy" },
    // Đây là output ĐÃ NORMALIZE của validate_algorithm_config (backend) —
    // dãy gốc [9,3,7]/labels ["chin","ba","bay"] → sắp theo giá trị.
    data: { array: [3, 7, 9], labels: ["ba", "bay", "chin"], target: 7 },
  };
}

describe("M15 Task 8 — binary_search trace trên normalized input (khóa 7, proof 4/4)", () => {
  it("config normalized qua validateConfig + init, trace tồn tại", () => {
    const mod = makeAlgorithmModule("binary_search");
    const r = mod.validateConfig(normalizedBinarySearchConfig());
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    const state = mod.init(r.config);
    expect(state.trace.steps.length).toBeGreaterThan(0);
  });

  it("MỌI step snapshot.array == [3,7,9] — trace chạy trên dãy đã sắp, không tự đổi chỗ", () => {
    const mod = makeAlgorithmModule("binary_search");
    const r = mod.validateConfig(normalizedBinarySearchConfig());
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    const state = mod.init(r.config);
    for (const step of state.trace.steps) {
      expect(step.snapshot.array).toEqual([3, 7, 9]);
    }
  });

  it("tìm thấy 7: bước cuối mark vị trí giá trị 7 là \"found\"", () => {
    const mod = makeAlgorithmModule("binary_search");
    const r = mod.validateConfig(normalizedBinarySearchConfig());
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    const state = mod.init(r.config);
    const lastStep = state.trace.steps.at(-1)!;
    const targetIndex = state.config.data.array.indexOf(7); // = 1 trong [3,7,9]
    expect(lastStep.snapshot.marks[targetIndex]).toBe("found");
  });
});
