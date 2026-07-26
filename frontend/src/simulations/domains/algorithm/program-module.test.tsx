import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";

import { runProgram, validateProgramSpec, type ProgramSpec } from "../../../core/program";
import { UnsupportedNotice } from "../../../components/SimulationWorkspace";
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

const iv = (n: number) => ({ kind: "int", int_value: n });
const vr = (n: string) => ({ kind: "var", name: n });
const val = (left: unknown, op?: string, right?: unknown) =>
  (op === undefined ? { left } : { left, op, right });
const at = (left: unknown, op?: string, right?: unknown) => ({ left, op, right });
const cd = (atoms: unknown[]) => ({ atoms });

const CF2_RAW = {
  program_version: "program-2.0",
  variables: [
    { name: "x", type: "integer", int_value: -2 },
    { name: "y", type: "integer" },
  ],
  statements: [
    { id: "s_then", kind: "assign", target: "y", value: val(iv(1)) },
    { id: "s_else", kind: "assign", target: "y", value: val(iv(-1)) },
    { id: "s_if", kind: "if", condition: cd([at(val(vr("x")), ">", val(iv(0)))]),
      then_body: ["s_then"], else_body: ["s_else"] },
  ],
  main: ["s_if"],
};

const CF3_RAW = {
  program_version: "program-2.0",
  variables: [{ name: "x", type: "integer", int_value: 1 }],
  statements: [
    { id: "s_body", kind: "assign", target: "x", value: val(vr("x"), "+", iv(1)) },
    { id: "s_while", kind: "while", condition: cd([at(val(vr("x")), "<", val(iv(5)))]),
      body: ["s_body"], max_iterations: 10 },
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

describe("W2C-C1 §L3 — tiêu đề từ chối đúng bản chất", () => {
  const notice = (failure_category?: string) =>
    renderToString(
      <UnsupportedNotice
        unsupported={{
          status: "unsupported",
          reason: "Đề chưa cho đoạn chương trình cụ thể.",
          learner_reason: "Đề chưa cho đoạn chương trình cụ thể để chạy thử.",
          ...(failure_category ? { failure_category } : {}),
        }}
      />,
    );

  it("thiếu dữ kiện ⇒ tiêu đề CHƯA ĐỦ DỮ KIỆN", () => {
    expect(notice("insufficient_specification")).toContain("CHƯA ĐỦ DỮ KIỆN");
  });

  it("ngoài danh mục ⇒ KHÔNG bị gắn nhầm CHƯA ĐỦ DỮ KIỆN", () => {
    const html = notice();
    expect(html).not.toContain("CHƯA ĐỦ DỮ KIỆN");
    expect(html).toContain("NGOÀI DANH MỤC");
  });

  it("không lộ enum kỹ thuật cho học sinh", () => {
    expect(notice("insufficient_specification")).not.toContain("insufficient_specification");
  });
});
