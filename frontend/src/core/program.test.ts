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

/* Dựng spec bằng bề mặt INLINE (W2C-C1 §L2 — không còn bảng expressions). */
const iv = (n: number) => ({ kind: "int", int_value: n });
const bo = (b: boolean) => ({ kind: "bool", bool_value: b });
const vr = (n: string) => ({ kind: "var", name: n });
const val = (left: unknown, op?: string, right?: unknown) =>
  (op === undefined ? { left } : { left, op, right });
const at = (left: unknown, op?: string, right?: unknown, negated = false) => ({
  left, ...(op === undefined ? {} : { op, right }), ...(negated ? { negated: true } : {}),
});
const cd = (atoms: unknown[], op?: string) => (op === undefined ? { atoms } : { op, atoms });
/** CF-1: x = 3 ; tich = x*2 ; y = tich + 1 → y = 7 (nhiều tầng ⇒ câu lệnh trung gian). */
const CF1 = {
  program_version: "program-2.0",
  variables: [
    { name: "x", type: "integer", int_value: 3 },
    { name: "tich", type: "integer" },
    { name: "y", type: "integer" },
  ],
  statements: [
    { id: "s1", kind: "assign", target: "tich", value: val(vr("x"), "*", iv(2)) },
    { id: "s2", kind: "assign", target: "y", value: val(vr("tich"), "+", iv(1)) },
  ],
  main: ["s1", "s2"],
};

/** CF-2: x = -2 ; nếu x > 0 thì y = 1 ngược lại y = -1. `y` CHƯA khởi tạo. */
const CF2 = {
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

/** CF-3: x = 1 ; trong khi x < 5 thì x = x + 1. */
const CF3 = {
  program_version: "program-2.0",
  variables: [{ name: "x", type: "integer", int_value: 1 }],
  statements: [
    { id: "s_body", kind: "assign", target: "x", value: val(vr("x"), "+", iv(1)) },
    { id: "s_while", kind: "while", condition: cd([at(val(vr("x")), "<", val(iv(5)))]),
      body: ["s_body"], max_iterations: 10 },
  ],
  main: ["s_while"],
};

/** CF-4: a = true, b = false ; nếu a và không b thì x = 1 ngược lại x = 0. */
const CF4 = {
  program_version: "program-2.0",
  variables: [
    { name: "a", type: "boolean", bool_value: true },
    { name: "b", type: "boolean", bool_value: false },
    { name: "x", type: "integer" },
  ],
  statements: [
    { id: "s_then", kind: "assign", target: "x", value: val(iv(1)) },
    { id: "s_else", kind: "assign", target: "x", value: val(iv(0)) },
    { id: "s_if", kind: "if",
      condition: cd([at(val(vr("a"))), at(val(vr("b")), undefined, undefined, true)], "and"),
      then_body: ["s_then"], else_body: ["s_else"] },
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
    program_version: "program-2.0",
    variables: [{ name: "x", type: "integer", int_value: 1 }],
    statements: [
      { id: "s_body", kind: "assign", target: "x", value: val(vr("x"), "+", iv(1)) },
      { id: "s_while", kind: "while", condition: cd([at(val(bo(true)))]),
        body: ["s_body"], max_iterations: 5 },
    ],
    main: ["s_while"],
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
      for (const step of trace.steps.slice(0, -1)) {
        expect(step.line).toBeDefined();
        expect(step.line!).toBeGreaterThanOrEqual(1);
        expect(step.line!).toBeLessThanOrEqual(lines.length);
      }
    }
  });

  it("W2C-VR1 — bước KẾT THÚC không highlight dòng nào", () => {
    // Trước bản vá, bước done trỏ vào dòng CUỐI của mã giả; ở CF-4 dòng cuối là
    // nhánh `x ← 0` KHÔNG hề chạy, nên ảnh cho thấy nhánh sai "đang thực hiện".
    for (const raw of [CF1, CF2, CF3, CF4]) {
      const { trace } = runProgram(parse(raw));
      const last = trace.steps[trace.steps.length - 1];
      expect(last.events.some((e) => e.type === "done")).toBe(true);
      expect(last.line).toBeUndefined();
    }
  });

  it("W2C-VR1 — dòng được highlight LUÔN là câu lệnh vừa chạy", () => {
    const spec = parse(CF4);
    const { lineOf } = programLines(spec);
    const { trace } = runProgram(spec);
    const executed = new Set(
      trace.steps.filter((s) => s.line !== undefined).map((s) => s.line),
    );
    // CF-4 đi nhánh THÌ ⇒ dòng của nhánh NGƯỢC LẠI không bao giờ được highlight
    expect(executed.has(lineOf.s_else)).toBe(false);
    expect(executed.has(lineOf.s_then)).toBe(true);
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
        variables: [{ name: "x", type: "integer", int_value: "5" }],
      }).ok,
    ).toBe(false);
    expect(
      validateProgramSpec({
        ...CF1,
        variables: [{ name: "x", type: "boolean", bool_value: 1 }],
      }).ok,
    ).toBe(false);
  });

  it("while thiếu biên bị từ chối", () => {
    const noBound = {
      ...CF3,
      statements: [
        { id: "s_body", kind: "assign", target: "x", value: val(vr("x"), "+", iv(1)) },
        { id: "s_while", kind: "while", condition: cd([at(val(vr("x")), "<", val(iv(5)))]),
          body: ["s_body"] },
      ],
    };
    expect(validateProgramSpec(noBound).ok).toBe(false);
  });

  it("điều kiện không phải đúng/sai bị từ chối", () => {
    const bad = {
      ...CF2,
      statements: [
        { id: "s_then", kind: "assign", target: "y", value: val(iv(1)) },
        { id: "s_if", kind: "if", condition: cd([at(val(vr("x")))]), then_body: ["s_then"] },
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
    expect(PROGRAM_LIMITS.maxExpressionDepth).toBe(6);
    expect(PROGRAM_LIMITS.maxConditionAtoms).toBe(3);
    expect(PROGRAM_LIMITS.maxExecutionSteps).toBe(200);
    expect(PROGRAM_LIMITS.maxWhileIterations).toBe(50);
  });
});

describe("W2C-C1 §L1 — khai báo ≠ khởi tạo (mirror backend)", () => {
  it("biến khai báo mà chưa có giá trị là HỢP LỆ và KHÔNG bị bịa giá trị", () => {
    const spec = parse(CF2);
    const y = spec.variables.find((v) => v.name === "y")!;
    expect(y.initialized).toBe(false);
    expect(y.int_value).toBeNull();
  });

  it("biến chưa khởi tạo KHÔNG xuất hiện trong vars ở bước đầu", () => {
    const { trace } = runProgram(parse(CF2));
    expect(Object.keys(trace.steps[0].snapshot.vars)).not.toContain("y");
    expect(Object.keys(trace.steps[0].snapshot.vars)).toContain("x");
  });

  it("đọc biến chưa chắc có giá trị bị TỪ CHỐI", () => {
    const bad = {
      program_version: "program-2.0",
      variables: [{ name: "y", type: "integer" }, { name: "z", type: "integer" }],
      statements: [
        { id: "b", kind: "assign", target: "z", value: val(vr("y"), "+", iv(1)) },
      ],
      main: ["b"],
    };
    const v = validateProgramSpec(bad);
    expect(v.ok).toBe(false);
    if (!v.ok) expect(v.error).toContain("chưa chắc chắn có giá trị");
  });

  it("chỉ nhánh then gán thì CHƯA chắc chắn", () => {
    const bad = {
      program_version: "program-2.0",
      variables: [{ name: "x", type: "integer", int_value: 1 }, { name: "y", type: "integer" }],
      statements: [
        { id: "t", kind: "assign", target: "y", value: val(iv(1)) },
        { id: "s", kind: "if", condition: cd([at(val(vr("x")), ">", val(iv(0)))]),
          then_body: ["t"] },
        { id: "u", kind: "output", value: val(vr("y")) },
      ],
      main: ["s", "u"],
    };
    expect(validateProgramSpec(bad).ok).toBe(false);
  });
});

describe("W2C-C1 §L2 — biểu thức inline (mirror backend)", () => {
  it("spec kiểu CŨ (tham chiếu id) không còn được chấp nhận", () => {
    const old = {
      program_version: "program-2.0",
      variables: [{ name: "x", type: "integer", int_value: 1 }],
      expressions: [{ id: "e1", kind: "int", int_value: 2 }],
      statements: [{ id: "s1", kind: "assign", target: "x", value: "e1" }],
      main: ["s1"],
    };
    expect(validateProgramSpec(old).ok).toBe(false);
  });

  it("normalize TẤT ĐỊNH — cùng input cùng biểu diễn nội bộ", () => {
    const a = parse(CF3);
    const b = parse(CF3);
    expect(a.expressions).toEqual(b.expressions);
  });

  it("toán tử ngoài ngữ pháp bị từ chối", () => {
    const bad = { ...CF3, statements: [
      { id: "s_body", kind: "assign", target: "x", value: val(vr("x"), "**", iv(2)) },
      { id: "s_while", kind: "while", condition: cd([at(val(vr("x")), "<", val(iv(5)))]),
        body: ["s_body"], max_iterations: 3 },
    ] };
    expect(validateProgramSpec(bad).ok).toBe(false);
  });
});
