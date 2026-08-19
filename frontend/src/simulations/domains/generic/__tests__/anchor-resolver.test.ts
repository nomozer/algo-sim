import { describe, it, expect } from "vitest";
import { resolveSemanticAnchor } from "../anchor-resolver";

describe("Semantic Anchor System (G5)", () => {
  it("resolves array_strip cell center correctly", () => {
    const arrayObj = {
      id: "arr_1",
      type: "array_strip",
      items: ["A", "B", "C", "D"],
    };
    const targetPos = { x: 300, y: 150 };
    // Array: 4 cells of 34px = 136px. startX = 300 - 68 = 232.
    // Index 0: cellCenterX = 232 + 17 = 249.
    // Index 2: cellCenterX = 232 + 2*34 + 17 = 317.
    const anchor0 = resolveSemanticAnchor(arrayObj, targetPos, 0, "top-center");
    expect(anchor0.x).toBe(249);
    expect(anchor0.y).toBe(150 - 17 - 4); // 129
    expect(anchor0.direction).toBe("down");

    const anchor2 = resolveSemanticAnchor(arrayObj, targetPos, 2, "top-center");
    expect(anchor2.x).toBe(317);
  });

  it("resolves stack_view item position from top edge correctly", () => {
    const stackObj = {
      id: "stack_1",
      type: "stack_view",
      items: ["(", "["],
      capacity: 5,
    };
    const targetPos = { x: 450, y: 120 };
    const anchor = resolveSemanticAnchor(stackObj, targetPos, 1);
    expect(anchor.x).toBeGreaterThan(450); // trỏ từ bên phải vào top item
    expect(anchor.direction).toBe("left");
  });

  it("handles out-of-bounds target_index gracefully", () => {
    const arrayObj = {
      id: "arr_1",
      type: "array_strip",
      items: [10, 20, 30],
    };
    const targetPos = { x: 300, y: 150 };
    // Index 99 clamped to index 2 (last cell)
    const anchor = resolveSemanticAnchor(arrayObj, targetPos, 99);
    expect(anchor.x).toBe(300 - 51 + 2 * 34 + 17);
  });
});
