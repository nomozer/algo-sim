import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";

import { runProgram, validateProgramSpec, type ProgramSpec } from "../../../core/program";
import { ProgramInspector, ProgramWorkspace, makeProgramModule } from "./program-module";
import type { ProgramSimState } from "./program-module";

/**
 * M17 W2C — renderer của luồng điều khiển hữu hạn.
 *
 * Bất biến khoá ở đây:
 * - renderer KHÔNG tự đánh giá điều kiện (đọc sự kiện engine, kể cả khi sự kiện
 *   "trái với trực giác" — đó chính là phép thử);
 * - kết quả cuối KHÔNG lộ ở bước đầu;
 * - nhánh không chạy KHÔNG được hiển thị như đã thực thi;
 * - mã giả + biến + điều kiện/lượt lặp đều có mặt.
 */

const CF2_RAW = {
  program_version: "program-1.0",
  variables: [
    { name: "x", type: "integer", int_value: -2, bool_value: null },
    { name: "y", type: "integer", int_value: 0, bool_value: null },
  ],
  expressions: [
    { id: "e_x", kind: "var", name: "x" },
    { id: "e_0", kind: "int", int_value: 0 },
    { id: "e_gt", kind: "compare", op: ">", left: "e_x", right: "e_0" },
    { id: "e_p1", kind: "int", int_value: 1 },
    { id: "e_m1", kind: "int", int_value: -1 },
  ],
  statements: [
    { id: "s_then", kind: "assign", target: "y", value: "e_p1" },
    { id: "s_else", kind: "assign", target: "y", value: "e_m1" },
    { id: "s_if", kind: "if", condition: "e_gt", then_body: ["s_then"], else_body: ["s_else"] },
  ],
  main: ["s_if"],
};

const CF3_RAW = {
  program_version: "program-1.0",
  variables: [{ name: "x", type: "integer", int_value: 1, bool_value: null }],
  expressions: [
    { id: "e_x", kind: "var", name: "x" },
    { id: "e_5", kind: "int", int_value: 5 },
    { id: "e_lt", kind: "compare", op: "<", left: "e_x", right: "e_5" },
    { id: "e_1", kind: "int", int_value: 1 },
    { id: "e_inc", kind: "binary", op: "+", left: "e_x", right: "e_1" },
  ],
  statements: [
    { id: "s_body", kind: "assign", target: "x", value: "e_inc" },
    { id: "s_while", kind: "while", condition: "e_lt", body: ["s_body"], max_iterations: 10 },
  ],
  main: ["s_while"],
};

function stateOf(raw: unknown, cursor = 0): ProgramSimState {
  const v = validateProgramSpec(raw);
  if (!v.ok) throw new Error(v.error);
  const spec: ProgramSpec = v.spec;
  const run = runProgram(spec);
  return { spec, trace: run.trace, cursor, completion: run.completion };
}

const noop = () => {};

function workspace(state: ProgramSimState): string {
  return renderToString(
    <ProgramWorkspace state={state} config={state.spec} busy={false} dispatch={noop} />,
  );
}

describe("module hợp đồng", () => {
  const mod = makeProgramModule();

  it("khai đúng id, 2D-only, có timeline", () => {
    expect(mod.id).toBe("algorithm.bounded_control_flow");
    expect(mod.domain).toBe("algorithm");
    expect(mod.supportedVisualModes).toEqual(["2d"]);
    expect(mod.timeline).toBeTruthy();
    expect(mod.interactionMode).toBe("progressive");
  });

  it("KHÔNG khai 3D — chiều sâu không mã hoá biến nào của chương trình", () => {
    expect(mod.supportedVisualModes).not.toContain("3d");
    expect(mod.renderers?.["3d"]).toBeUndefined();
  });

  it("init chạy engine tất định, timeline khớp số bước", () => {
    const state = mod.init(stateOf(CF3_RAW).spec);
    expect(mod.timeline!.stepCount(state)).toBe(state.trace.steps.length);
    expect(mod.timeline!.currentStep(state)).toBe(0);
  });

  it("validateConfig từ chối spec ngoài ngữ pháp", () => {
    const bad = { ...CF2_RAW, statements: [{ id: "s1", kind: "call" }] };
    expect(mod.validateConfig(bad).ok).toBe(false);
  });
});

describe("kết quả cuối KHÔNG lộ ở bước đầu", () => {
  it("bước 0 không chứa câu kết luận", () => {
    const html = workspace(stateOf(CF3_RAW, 0));
    expect(html).not.toContain("Chương trình kết thúc");
  });

  it("bước cuối mới hiện kết luận", () => {
    const state = stateOf(CF3_RAW);
    const html = workspace({ ...state, cursor: state.trace.steps.length - 1 });
    expect(html).toContain("Chương trình kết thúc");
  });
});

describe("nhánh không chạy không được trình bày như đã thực thi", () => {
  it("chỉ nhánh ĐƯỢC CHỌN xuất hiện", () => {
    const state = stateOf(CF2_RAW);
    const condIdx = state.trace.steps.findIndex((s) =>
      s.events.some((e) => e.type === "evaluate_condition"),
    );
    const html = workspace({ ...state, cursor: condIdx });
    expect(html).toContain("NGƯỢC LẠI");
    expect(html).not.toContain("nhánh THÌ");
  });
});

describe("renderer KHÔNG tự tính lại điều kiện", () => {
  it("hiển thị đúng KẾT QUẢ ENGINE PHÁT RA, kể cả khi trái trực giác", () => {
    // Bịa một bước có sự kiện nói "x > 0 → ĐÚNG" dù x = -2. Nếu renderer tự
    // đánh giá biểu thức, nó sẽ hiện SAI và test này đỏ — đó là mục đích.
    const state = stateOf(CF2_RAW);
    const forged = {
      ...state,
      trace: {
        ...state.trace,
        steps: state.trace.steps.map((s, i) =>
          i === 0
            ? {
                ...s,
                events: [
                  { type: "evaluate_condition" as const, expression: "x > 0", result: true },
                  { type: "enter_branch" as const, branch: "then" as const },
                ],
              }
            : s,
        ),
      },
      cursor: 0,
    };
    const html = workspace(forged);
    expect(html).toContain("ĐÚNG");
    expect(html).toContain("nhánh THÌ");
  });
});

describe("thông tin học sinh cần thấy", () => {
  it("mã giả có mặt và thụt cấp", () => {
    const html = workspace(stateOf(CF2_RAW));
    expect(html).toContain("nếu");
    expect(html).toContain("ngược lại");
  });

  it("số lượt lặp hiện ra ở bước trong thân vòng lặp", () => {
    const state = stateOf(CF3_RAW);
    const idx = state.trace.steps.findIndex((s) =>
      s.events.some((e) => e.type === "loop_iteration"),
    );
    const html = workspace({ ...state, cursor: idx });
    expect(html).toContain("Lượt lặp thứ 1");
  });

  it("inspector hiện biến và đánh dấu biến vừa đổi", () => {
    const state = stateOf(CF3_RAW);
    const idx = state.trace.steps.findIndex((s) =>
      s.events.some((e) => e.type === "assign_var"),
    );
    const html = renderToString(
      <ProgramInspector
        state={{ ...state, cursor: idx }}
        config={state.spec}
        busy={false}
        dispatch={noop}
      />,
    );
    expect(html).toContain("x");
    expect(html).toContain("Biến vừa đổi");
  });
});

describe("getExplainContext — ảnh chụp state THẬT", () => {
  it("không chứa mã nguồn nội bộ, có đủ bước/biến/điều kiện", () => {
    const mod = makeProgramModule();
    const state = stateOf(CF2_RAW);
    const condIdx = state.trace.steps.findIndex((s) =>
      s.events.some((e) => e.type === "evaluate_condition"),
    );
    const ctx = mod.getExplainContext({ ...state, cursor: condIdx }, state.spec);
    expect(ctx.simulation_id).toBe("algorithm.bounded_control_flow");
    expect(Array.isArray(ctx.pseudocode)).toBe(true);
    expect(ctx.condition).toContain("x > 0");
    expect(ctx.branch).toBe("else");
    expect(ctx.total_steps).toBe(state.trace.steps.length);
  });
});
