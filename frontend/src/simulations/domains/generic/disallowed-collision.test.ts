import { describe, expect, it } from "vitest";
import { checkDisallowedCollisions } from "./disallowed-collision";
import type { SimulationSpec } from "./model";

describe("Disallowed Pairwise Collision Verifier", () => {
  it("C02 Stack bracket verification has 0 disallowed collisions", () => {
    const spec: SimulationSpec = {
      dsl_version: "1.0",
      title: "Kiểm tra đóng mở ngoặc hợp lệ bằng Stack",
      objects: [
        { id: "input_strip", type: "array_strip", items: ["{", "[", "(", ")", "]", "}"], label: "Chuỗi ký tự đầu vào" },
        { id: "char_box", type: "value_box", value: "{", label: "Ký tự hiện tại" },
        { id: "stack", type: "stack_view", items: [], capacity: 6, label: "Ngăn xếp (Stack)" },
        { id: "result_box", type: "value_box", value: "Đang kiểm tra...", label: "Kết quả kiểm tra" },
      ],
      rules: [],
      interactions: [],
      processes: [],
    };

    const violations = checkDisallowedCollisions(spec);
    expect(violations).toHaveLength(0);
  });

  it("C01 Temperature scan has 0 disallowed collisions", () => {
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

    const violations = checkDisallowedCollisions(spec);
    expect(violations).toHaveLength(0);
  });

  it("Detects synthetic box-on-box collision when coordinates overlap", () => {
    const spec: SimulationSpec = {
      dsl_version: "1.0",
      title: "Cảnh lỗi chồng chéo",
      objects: [
        { id: "box1", type: "value_box", x: 50, y: 50, value: 10 },
        { id: "box2", type: "value_box", x: 51, y: 51, value: 20 },
      ],
      rules: [],
      interactions: [],
      processes: [],
    };

    const violations = checkDisallowedCollisions(spec);
    expect(violations.length).toBeGreaterThan(0);
    expect(violations[0].kind).toBe("BOX_ON_BOX");
    expect(violations[0].id1).toBe("box1");
    expect(violations[0].id2).toBe("box2");
  });

  it("Detects canvas overflow when object is placed out of bounds", () => {
    const spec: SimulationSpec = {
      dsl_version: "1.0",
      title: "Cảnh tràn biên",
      objects: [
        { id: "box1", type: "value_box", x: 2, y: 50, value: 10 },
      ],
      rules: [],
      interactions: [],
      processes: [],
    };

    const violations = checkDisallowedCollisions(spec);
    expect(violations.length).toBeGreaterThan(0);
    expect(violations[0].kind).toBe("CANVAS_OVERFLOW");
  });
});
