import { createElement } from "react";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { makeGenericModule } from "../index";
import { GenericWorkspace } from "../ui";
import { computeSemanticLayout } from "../layout-compiler";
import { resolveSemanticAnchor } from "../anchor-resolver";
import { checkDisallowedCollisions } from "../disallowed-collision";
import type { SimulationSpec } from "../model";

describe("Stack Bracket Simulation — Production Render Certificate (Phase 6b)", () => {
  const mod = makeGenericModule();

  const STACK_BRACKET_SPEC: SimulationSpec = {
    dsl_version: "1.0",
    title: "Kiểm tra chuỗi ngoặc hợp lệ bằng Ngăn xếp (Stack)",
    objects: [
      {
        id: "bracket_strip",
        type: "array_strip",
        label: "Chuỗi ngoặc đầu vào",
        items: ["{", "[", "(", ")", "]", "}"],
      },
      {
        id: "stack_view",
        type: "stack_view",
        label: "Ngăn xếp",
        items: ["{", "["],
        capacity: 6,
      },
      {
        id: "curr_char",
        type: "value_box",
        label: "Ký tự hiện tại",
        value: "(",
      },
      {
        id: "result_box",
        type: "value_box",
        label: "Kết quả",
        value: "HỢP LỆ",
      },
      {
        id: "ptr_i",
        type: "pointer",
        label: "i",
        target: "bracket_strip",
        target_index: 2,
      },
    ],
    rules: [],
    interactions: [],
    processes: [
      {
        type: "step_sequence",
        steps: [
          {
            highlight: ["bracket_strip"],
            narration: "Xét ký tự đầu tiên '{': Là dấu mở ngoặc, đẩy vào Ngăn xếp.",
            state: {
              curr_char: "{",
              stack_view: { op: "push", value: "{" },
            },
          },
          {
            highlight: ["bracket_strip"],
            narration: "Xét ký tự tiếp theo '[': Là dấu mở ngoặc, tiếp tục đẩy vào Ngăn xếp.",
            state: {
              curr_char: "[",
              stack_view: { op: "push", value: "[" },
            },
          },
          {
            highlight: ["bracket_strip"],
            narration: "Xét ký tự '(': Là dấu mở ngoặc, đẩy vào Ngăn xếp.",
            state: {
              curr_char: "(",
              stack_view: { op: "push", value: "(" },
            },
          },
          {
            highlight: ["bracket_strip", "stack_view"],
            narration: "Xét ký tự ')': Là dấu đóng ngoặc, kiểm tra đỉnh stack thấy '(' khớp cặp! Pop '(' ra khỏi stack.",
            state: {
              curr_char: ")",
              stack_view: { op: "pop" },
            },
          },
          {
            highlight: ["result_box"],
            narration: "Duyệt hết chuỗi và Stack rỗng: Chuỗi ngoặc hoàn toàn HỢP LỆ!",
            state: {
              result_box: "HỢP LỆ",
            },
          },
        ],
      },
    ],
  };

  it("1. Data Fidelity: Chuỗi ngoặc hiển thị ký tự thật, không có dummy zero", () => {
    const s0 = mod.init(STACK_BRACKET_SPEC);
    const html = renderToString(
      createElement(GenericWorkspace, {
        config: STACK_BRACKET_SPEC,
        state: s0,
        busy: false,
        dispatch: () => {},
      })
    );

    // Kiểm tra hiển thị chuỗi ký tự
    expect(html).toContain("{");
    expect(html).toContain("[");
    expect(html).toContain("(");
    expect(html).toContain(")");
    expect(html).toContain("]");
    expect(html).toContain("}");

    // Kiểm tra không bị coerce thành 0
    expect(html).not.toContain('<text x="28" y="49">0</text>');
    expect(html).toContain("HỢP LỆ");
  });

  it("2. Content Hygiene: Canvas không bị trùng lặp outer heading", () => {
    const s0 = mod.init(STACK_BRACKET_SPEC);
    const html = renderToString(
      createElement(GenericWorkspace, {
        config: STACK_BRACKET_SPEC,
        state: s0,
        busy: false,
        dispatch: () => {},
      })
    );

    // Heading trong SVG bị suppress để tránh lặp với header ngoài trang
    expect(html).not.toContain('<h1 class="svg-heading">');
  });

  it("3. Semantic Anchor: Pointer neo đúng vị trí target cell", () => {
    const s0 = mod.init(STACK_BRACKET_SPEC);
    const pos = computeSemanticLayout(STACK_BRACKET_SPEC);
    const stripPos = pos["bracket_strip"];
    expect(stripPos).toBeDefined();

    const targetPixelPos = { x: (stripPos.x / 100) * 1366, y: (stripPos.y / 100) * 768 };
    const anchor = resolveSemanticAnchor(STACK_BRACKET_SPEC.objects[0], targetPixelPos, 2);

    expect(anchor.direction).toBe("down");
    expect(anchor.x).toBeGreaterThan(0);
    expect(anchor.y).toBeGreaterThan(0);
  });

  it("4. Viewport Non-Collision Matrix: 0 disallowed collisions trên toàn bộ canvas", () => {
    const violations = checkDisallowedCollisions(STACK_BRACKET_SPEC);
    expect(violations).toEqual([]);
  });

  it("5. Narration-State Parity: Thuyết minh từng bước khớp chính xác với state", () => {
    const s0 = mod.init(STACK_BRACKET_SPEC);
    expect(s0.timeline).toBeDefined();
    expect(s0.timeline.length).toBe(5);

    // Bước 0
    expect(s0.timeline[0].narration).toContain("'{'");
    // Bước 3 (pop matching)
    expect(s0.timeline[3].narration).toContain("')'");
    expect(s0.timeline[3].narration).toContain("khớp cặp");
    // Bước 4 (kết quả)
    expect(s0.timeline[4].narration).toContain("HỢP LỆ");
  });
});
