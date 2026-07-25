import { describe, expect, it } from "vitest";

import {
  PROGRAM_LIMITS,
  programLines,
  runProgram,
  validateProgramSpec,
  type ProgramSpec,
} from "./program";

/**
 * M17 W2C — interpreter luồng điều khiển hữu hạn.
 *
 * MIRROR của `backend/tests/test_program_spec.py`: cùng luật, cùng con số. Đây
 * là tầng 2 của validation, và là tầng DUY NHẤT chạy khi học sinh mở lại bài từ
 * lịch sử (bất biến #17) — nhận bừa một spec sai kiểu ở đây là sai câm.
 *
 * Sáu ca CF-1..CF-6 của Wave 2C nằm trong file này (CF-5/CF-6 thuộc phần cổng ở
 * backend nên phía FE khoá bằng validator từ chối).
 */

function parse(raw: unknown): ProgramSpec {
  const v = validateProgramSpec(raw);
  if (!v.ok) throw new Error(`spec đáng lẽ hợp lệ nhưng bị từ chối: ${v.error}`);
  return v.spec;
}

/** CF-1: x = 3 ; y = x * 2 + 1 */
const CF1 = {
  program_version: "program-1.0",
  variables: [
    { name: "x", type: "integer", int_value: 3, bool_value: null },
    { name: "y", type: "integer", int_value: 0, bool_value: null },
  ],
  expressions: [
    { id: "e_x", kind: "var", name: "x" },
    { id: "e_2", kind: "int", int_value: 2 },
    { id: "e_1", kind: "int", int_value: 1 },
    { id: "e_mul", kind: "binary", op: "*", left: "e_x", right: "e_2" },
    { id: "e_sum", kind: "binary", op: "+", left: "e_mul", right: "e_1" },
  ],
  statements: [{ id: "s1", kind: "assign", target: "y", value: "e_sum" }],
  main: ["s1"],
};

/** CF-2: x = -2 ; nếu x > 0 thì y = 1 ngược lại y = -1 */
const CF2 = {
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

/** CF-3: x = 1 ; trong khi x < 5 thì x = x + 1 */
const CF3 = {
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

/** CF-4: a = true, b = false ; nếu a và không b thì x = 1 ngược lại x = 0 */
const CF4 = {
  program_version: "program-1.0",
  variables: [
    { name: "a", type: "boolean", int_value: null, bool_value: true },
    { name: "b", type: "boolean", int_value: null, bool_value: false },
    { name: "x", type: "integer", int_value: 0, bool_value: null },
  ],
  expressions: [
    { id: "e_a", kind: "var", name: "a" },
    { id: "e_b", kind: "var", name: "b" },
    { id: "e_nb", kind: "unary", op: "not", operand: "e_b" },
    { id: "e_and", kind: "logic", op: "and", left: "e_a", right: "e_nb" },
    { id: "e_1", kind: "int", int_value: 1 },
    { id: "e_0", kind: "int", int_value: 0 },
  ],
  statements: [
    { id: "s_then", kind: "assign", target: "x", value: "e_1" },
    { id: "s_else", kind: "assign", target: "x", value: "e_0" },
    { id: "s_if", kind: "if", condition: "e_and", then_body: ["s_then"], else_body: ["s_else"] },
  ],
  main: ["s_if"],
};

const lastVars = (spec: ProgramSpec) => {
  const { trace } = runProgram(spec);
  return trace.steps[trace.steps.length - 1].snapshot.vars;
};

describe("CF-1 — gán và biểu thức số học", () => {
  it("y = x*2 + 1 = 7", () => {
    expect(lastVars(parse(CF1)).y).toBe(7);
  });

  it("trace thể hiện phép gán, không nhảy thẳng tới kết quả", () => {
    const { trace } = runProgram(parse(CF1));
    const assign = trace.steps.find((s) =>
      s.events.some((e) => e.type === "assign_var" && e.name === "y"),
    );
    expect(assign).toBeTruthy();
    expect(assign!.narration).toContain("7");
  });
});

describe("CF-2 — rẽ nhánh if/else", () => {
  it("điều kiện SAI ⇒ chỉ nhánh ngược lại chạy, y = -1", () => {
    const spec = parse(CF2);
    const { trace } = runProgram(spec);
    expect(lastVars(spec).y).toBe(-1);

    const cond = trace.steps.flatMap((s) =>
      s.events.filter((e) => e.type === "evaluate_condition"),
    );
    expect(cond).toHaveLength(1);
    expect(cond[0]).toMatchObject({ result: false });

    const branches = trace.steps.flatMap((s) =>
      s.events.filter((e) => e.type === "enter_branch"),
    );
    expect(branches.map((b) => (b as { branch: string }).branch)).toEqual(["else"]);
  });

  it("nhánh KHÔNG chạy không để lại phép gán nào", () => {
    const { trace } = runProgram(parse(CF2));
    const assigned = trace.steps.flatMap((s) =>
      s.events.filter((e) => e.type === "assign_var").map((e) => (e as { value: unknown }).value),
    );
    expect(assigned).toEqual([-1]); // 1 (nhánh thì) không bao giờ xuất hiện
  });
});

describe("CF-3 — vòng lặp while", () => {
  it("lặp đúng 4 lượt và x cuối = 5", () => {
    const spec = parse(CF3);
    const { trace, completion } = runProgram(spec);
    expect(lastVars(spec).x).toBe(5);
    expect(completion).toBe("completed");

    const iters = trace.steps.flatMap((s) =>
      s.events.filter((e) => e.type === "loop_iteration"),
    );
    expect(iters.map((e) => (e as { iteration: number }).iteration)).toEqual([1, 2, 3, 4]);
  });

  it("có bước THOÁT vòng lặp với điều kiện SAI", () => {
    const { trace } = runProgram(parse(CF3));
    const exit = trace.steps.find((s) =>
      s.events.some((e) => e.type === "enter_branch" && e.branch === "loop_exit"),
    );
    expect(exit).toBeTruthy();
  });
});

describe("CF-4 — điều kiện logic", () => {
  it("a AND NOT b = ĐÚNG ⇒ x = 1", () => {
    const spec = parse(CF4);
    expect(lastVars(spec).x).toBe(1);
    const { trace } = runProgram(spec);
    const cond = trace.steps.flatMap((s) =>
      s.events.filter((e) => e.type === "evaluate_condition"),
    );
    expect(cond[0]).toMatchObject({ result: true });
  });
});

describe("vòng lặp KHÔNG BAO GIỜ treo", () => {
  const infinite = {
    ...CF3,
    expressions: [
      { id: "e_x", kind: "var", name: "x" },
      { id: "e_5", kind: "int", int_value: 5 },
      { id: "e_lt", kind: "compare", op: "<", left: "e_x", right: "e_5" },
      { id: "e_1", kind: "int", int_value: 1 },
      { id: "e_inc", kind: "binary", op: "+", left: "e_x", right: "e_1" },
      { id: "e_t", kind: "bool", bool_value: true },
    ],
    statements: [
      { id: "s_body", kind: "assign", target: "x", value: "e_inc" },
      { id: "s_while", kind: "while", condition: "e_t", body: ["s_body"], max_iterations: 5 },
    ],
  };

  it("chạm biên thì DỪNG và báo chưa kết thúc — không giả vờ chạy xong", () => {
    const { trace, completion } = runProgram(parse(infinite));
    expect(completion).toBe("limit_reached");
    const done = trace.steps[trace.steps.length - 1].events.find((e) => e.type === "done");
    expect((done as { result: string }).result).toContain("chưa kết thúc");
  });

  it("số bước luôn hữu hạn và trong ngân sách", () => {
    const { trace } = runProgram(parse(infinite));
    expect(trace.steps.length).toBeLessThanOrEqual(PROGRAM_LIMITS.maxExecutionSteps + 1);
  });
});

describe("mã giả và Step.line KHÔNG trôi khỏi nhau", () => {
  it("mọi Step.line trỏ vào một dòng có thật", () => {
    for (const raw of [CF1, CF2, CF3, CF4]) {
      const spec = parse(raw);
      const { lines } = programLines(spec);
      const { trace } = runProgram(spec);
      for (const step of trace.steps) {
        expect(step.line).toBeDefined();
        expect(step.line!).toBeGreaterThanOrEqual(1);
        expect(step.line!).toBeLessThanOrEqual(lines.length);
      }
    }
  });

  it("mã giả sinh TỪ statements[] — đổi chương trình thì đổi theo", () => {
    const { lines, lineOf } = programLines(parse(CF2));
    expect(lines.some((l) => l.includes("nếu"))).toBe(true);
    expect(lines.some((l) => l.includes("ngược lại"))).toBe(true);
    // câu lệnh trong nhánh được thụt vào
    expect(lines[lineOf.s_then - 1].startsWith(" ")).toBe(true);
  });

  it("bước xét điều kiện highlight ĐÚNG dòng của câu lệnh if", () => {
    const spec = parse(CF2);
    const { lineOf } = programLines(spec);
    const { trace } = runProgram(spec);
    const condStep = trace.steps.find((s) =>
      s.events.some((e) => e.type === "evaluate_condition"),
    );
    expect(condStep!.line).toBe(lineOf.s_if);
  });
});

describe("validator mirror — fail-closed", () => {
  it("từ chối loại câu lệnh ngoài ngữ pháp (hàm/đệ quy)", () => {
    const v = validateProgramSpec({
      ...CF1,
      statements: [{ id: "s1", kind: "call", target: "y", value: "e_sum" }],
    });
    expect(v.ok).toBe(false);
  });

  it("không coercion: '5' không thành 5, 1 không thành true", () => {
    expect(
      validateProgramSpec({
        ...CF1,
        variables: [{ name: "x", type: "integer", int_value: "5", bool_value: null }],
      }).ok,
    ).toBe(false);
    expect(
      validateProgramSpec({
        ...CF1,
        variables: [{ name: "x", type: "boolean", int_value: null, bool_value: 1 }],
      }).ok,
    ).toBe(false);
  });

  it("while thiếu biên bị từ chối", () => {
    const noBound = {
      ...CF3,
      statements: [
        { id: "s_body", kind: "assign", target: "x", value: "e_inc" },
        { id: "s_while", kind: "while", condition: "e_lt", body: ["s_body"] },
      ],
    };
    expect(validateProgramSpec(noBound).ok).toBe(false);
  });

  it("điều kiện không phải đúng/sai bị từ chối", () => {
    const bad = {
      ...CF2,
      statements: [
        { id: "s_then", kind: "assign", target: "y", value: "e_p1" },
        { id: "s_if", kind: "if", condition: "e_x", then_body: ["s_then"] },
      ],
      main: ["s_if"],
    };
    expect(validateProgramSpec(bad).ok).toBe(false);
  });

  it("spec mang kết quả/diễn biến bị từ chối (R0)", () => {
    expect(validateProgramSpec({ ...CF1, trace: { steps: [] } }).ok).toBe(false);
    expect(validateProgramSpec({ ...CF1, final_environment: { y: 7 } }).ok).toBe(false);
  });

  it("giới hạn khớp hợp đồng backend", () => {
    expect(PROGRAM_LIMITS.maxStatementNodes).toBe(12);
    expect(PROGRAM_LIMITS.maxNestingDepth).toBe(2);
    expect(PROGRAM_LIMITS.maxVariables).toBe(8);
    expect(PROGRAM_LIMITS.maxExpressionDepth).toBe(4);
    expect(PROGRAM_LIMITS.maxExecutionSteps).toBe(200);
    expect(PROGRAM_LIMITS.maxWhileIterations).toBe(50);
  });
});
