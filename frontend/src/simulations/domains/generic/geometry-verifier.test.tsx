import { describe, expect, it } from "vitest";
import { computeSemanticLayout } from "./layout-compiler";
import type { SimulationSpec } from "./model";

describe("Semantic Layout & Browser Geometry Verifier", () => {
  it("C02 Stack bracket verification: All objects placed in non-overlapping zones", () => {
    const spec: SimulationSpec = {
      dsl_version: "1.0",
      title: "Kiểm tra đóng mở ngoặc hợp lệ bằng Stack",
      objects: [
        { id: "input_strip", type: "array_strip", items: ["{", "[", "(", ")", "]", "}"], label: "Chuỗi ký tự đầu vào" },
        { id: "ptr", type: "pointer", target: "input_strip", index: 0, label: "Con trỏ i" },
        { id: "char_box", type: "value_box", value: "{", label: "Ký tự hiện tại" },
        { id: "stack", type: "stack_view", items: [], capacity: 6, label: "Ngăn xếp (Stack)" },
        { id: "result_box", type: "value_box", value: "Đang kiểm tra...", label: "Kết quả kiểm tra" },
      ],
      rules: [],
      interactions: [],
      processes: [],
    };

    const pos = computeSemanticLayout(spec);

    // Input strip on the top/middle-left
    expect(pos.input_strip.y).toBeLessThan(30);
    expect(pos.input_strip.x).toBeLessThan(50);

    // Stack on the right side
    expect(pos.stack.x).toBeGreaterThan(65);
    expect(pos.stack.y).toBeGreaterThan(25);

    // State box (char_box) on the middle-left
    expect(pos.char_box.x).toBeLessThan(40);
    expect(pos.char_box.y).toBeGreaterThan(40);

    // Result box on the bottom-left
    expect(pos.result_box.y).toBeGreaterThan(pos.char_box.y);

    // Bounding distance check: No two major objects share the same center
    const majorIds = ["input_strip", "char_box", "stack", "result_box"];
    for (let i = 0; i < majorIds.length; i++) {
      for (let j = i + 1; j < majorIds.length; j++) {
        const id1 = majorIds[i];
        const id2 = majorIds[j];
        const p1 = pos[id1];
        const p2 = pos[id2];
        const dist = Math.hypot(p1.x - p2.x, p1.y - p2.y);
        expect(dist).toBeGreaterThanOrEqual(18); // Minimum distance in domain units >= 18%
      }
    }
  });

  it("C01 Temperature scan: Bar chart centered at top, result and stats at bottom", () => {
    const spec: SimulationSpec = {
      dsl_version: "1.0",
      title: "Tìm ngày đầu tiên có nhiệt độ cao hơn trung bình tuần",
      objects: [
        {
          id: "temp_chart",
          type: "bar_chart",
          bars: [
            { id: "d1", value: 24 },
            { id: "d2", value: 26 },
            { id: "d3", value: 25 },
            { id: "d4", value: 29 },
            { id: "d5", value: 28 },
            { id: "d6", value: 31 },
            { id: "d7", value: 27 },
          ],
        },
        { id: "avg_box", type: "value_box", value: 27.14, label: "Nhiệt độ TB" },
        { id: "result_box", type: "value_box", value: 0, label: "Kết quả" },
      ],
      rules: [],
      interactions: [],
      processes: [],
    };

    const pos = computeSemanticLayout(spec);

    expect(pos.temp_chart.x).toBe(50);
    expect(pos.temp_chart.y).toBeLessThan(30);
    expect(pos.avg_box.y).toBeGreaterThan(50);
    expect(pos.result_box.y).toBeGreaterThan(50);
  });
});
