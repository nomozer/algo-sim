import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";

import { runProgram, validateProgramSpec, type ProgramSpec } from "../../../core/program";
import { UnsupportedNotice } from "../../../components/SimulationWorkspace";
import { ProgramInspector, ProgramWorkspace, makeProgramModule } from "./program-module";
import type { ProgramSimState } from "./program-module";
// Sinh từ chính backend `validate_program_config` — KHÔNG chép tay.
import wireFixture from "./program-normalized-envelope.json";

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

/**
 * M17 — HỢP ĐỒNG DÂY DẪN backend → frontend (contract drift, audit 2026-08-03).
 *
 * Trước bản vá: backend validate xong thì CHUẨN HOÁ biểu thức inline thành bảng
 * `expressions[]` + tham chiếu id, và chính hình dạng đó đi vào
 * `ValidatedSimulationEnvelope`. Frontend lại luôn gọi `normalizeInlineProgram`
 * nên đòi `condition.atoms` → TỪ CHỐI mọi envelope backend phát ra. Backend báo
 * `status: ok` còn trình duyệt không dựng được gì.
 *
 * Fixture dưới đây KHÔNG chép tay: sinh từ chính `validate_program_config`
 * (xem `_comment` trong file JSON). `backend/tests/test_program_wire_contract.py`
 * khoá chiều ngược lại để backend không trôi khỏi nó.
 */
describe("hợp đồng dây dẫn: frontend tiêu thụ ĐÚNG config backend phát ra", () => {
  const WIRE = wireFixture.config as unknown;

  it("fixture đúng là dạng CANONICAL (đã chuẩn hoá), không phải inline", () => {
    const c = wireFixture.config as Record<string, unknown>;
    expect(Array.isArray(c.expressions)).toBe(true);
    const whileSt = (c.statements as Record<string, unknown>[])
      .find((s) => s.kind === "while")!;
    expect(typeof whileSt.condition).toBe("string");   // tham chiếu id, không phải {atoms}
    expect(whileSt.condition).toBe("_e3");
  });

  it("validateConfig của module CHẤP NHẬN config canonical", () => {
    const v = makeProgramModule().validateConfig(WIRE);
    expect(v.ok, v.ok ? "" : `frontend từ chối envelope backend: ${v.error}`).toBe(true);
  });

  it("engine chạy trên config canonical và khớp oracle độc lập", () => {
    const mod = makeProgramModule();
    const v = mod.validateConfig(WIRE);
    if (!v.ok) throw new Error(v.error);
    const st = mod.init(v.config) as ProgramSimState;
    expect(st.completion).toBe("completed");
    const xs = st.trace.steps
      .map((s) => s.snapshot.vars.x)
      .filter((x, i, a) => x !== undefined && x !== a[i - 1]);
    expect(xs).toEqual([2, 5, 8, 11, 14, 17]);   // oracle: x=2; while x<=14: x+=3
    expect(st.trace.steps[st.trace.steps.length - 1].snapshot.vars.x).toBe(17);
    expect(st.trace.steps.length).toBeGreaterThan(1);
  });

  it("hai đường vào cho CÙNG một trace — không sinh hai engine", () => {
    const mod = makeProgramModule();
    const inline = {
      program_version: "program-2.0",
      variables: [{ name: "x", type: "integer", int_value: 2 }],
      statements: [
        { id: "s_while", kind: "while", condition: cd([at(val(vr("x")), "<=", val(iv(14)))]),
          body: ["s_body"], max_iterations: 10 },
        { id: "s_body", kind: "assign", target: "x", value: val(vr("x"), "+", iv(3)) },
      ],
      main: ["s_while"],
    };
    const a = mod.validateConfig(inline);
    const b = mod.validateConfig(WIRE);
    if (!a.ok) throw new Error(a.error);
    if (!b.ok) throw new Error(b.error);
    const ta = (mod.init(a.config) as ProgramSimState).trace;
    const tb = (mod.init(b.config) as ProgramSimState).trace;
    // so khớp THỰC CHẤT: dãy giá trị + dòng mã giả + số bước, không so mảng rỗng
    expect(ta.steps.length).toBeGreaterThan(1);
    expect(tb.steps.map((s) => s.snapshot.vars.x))
      .toEqual(ta.steps.map((s) => s.snapshot.vars.x));
    expect(tb.steps.map((s) => s.line)).toEqual(ta.steps.map((s) => s.line));
    expect(tb.steps.map((s) => s.narration)).toEqual(ta.steps.map((s) => s.narration));
  });

  it("config canonical KHÔNG mang kết quả (R0)", () => {
    const c = wireFixture.config as Record<string, unknown>;
    for (const k of ["trace", "steps", "environment", "result", "iterations", "timeline"]) {
      expect(k in c).toBe(false);
    }
  });
});

/**
 * FAIL-CLOSED trên đường CANONICAL. Nhận thêm một bề mặt KHÔNG được làm
 * validator dễ dãi hơn. Đặc biệt: `typeOf`/`readsOf` trong `core/program.ts`
 * đệ quy và dùng non-null assertion trên `exprById.get(id)!` — bảng có id treo
 * sẽ NÉM TypeError, có chu trình sẽ TRÀN NGĂN XẾP. Biên phải chặn trước, và
 * chặn bằng `fail()` sạch chứ không phải bằng exception.
 */
describe("đường canonical vẫn fail-closed", () => {
  const mod = makeProgramModule();
  const base = () => JSON.parse(JSON.stringify(wireFixture.config)) as Record<string, unknown>;
  const reject = (mutate: (c: Record<string, unknown>) => void): string => {
    const c = base();
    mutate(c);
    let v: ReturnType<typeof mod.validateConfig>;
    expect(() => { v = mod.validateConfig(c); }).not.toThrow();  // sạch, không ném
    expect(v!.ok).toBe(false);
    return v!.ok ? "" : v!.error;
  };

  it("tham chiếu điều kiện TREO", () => {
    expect(reject((c) => {
      (c.statements as Record<string, unknown>[])[0].condition = "_e404";
    })).toMatch(/không tồn tại/);
  });

  it("biểu thức tham chiếu con TREO", () => {
    expect(reject((c) => {
      (c.expressions as Record<string, unknown>[])[2].left = "_e404";
    })).toMatch(/không tồn tại/);
  });

  it("id biểu thức TRÙNG", () => {
    expect(reject((c) => {
      const e = c.expressions as Record<string, unknown>[];
      e.push({ ...e[0] });
    })).toMatch(/trùng id/);
  });

  it("CHU TRÌNH trong bảng biểu thức (không tràn ngăn xếp)", () => {
    expect(reject((c) => {
      const e = c.expressions as Record<string, unknown>[];
      // _e3 = compare(_e1, _e2) → trỏ ngược _e1 về chính _e3
      e[0] = { id: "_e1", kind: "unary", op: "not", operand: "_e3" };
    })).toMatch(/vòng tròn|lồng quá/);
  });

  it("loại biểu thức ngoài ngữ pháp", () => {
    expect(reject((c) => {
      (c.expressions as Record<string, unknown>[])[1].kind = "call";
    })).toMatch(/không hỗ trợ/);
  });

  it("toán tử ngoài ngữ pháp", () => {
    expect(reject((c) => {
      (c.expressions as Record<string, unknown>[])[2].op = "<=>";
    })).toMatch(/Toán tử không hợp lệ/);
  });

  it("SAI KIỂU: so sánh số nguyên với đúng/sai", () => {
    expect(reject((c) => {
      (c.expressions as Record<string, unknown>[])[1] =
        { id: "_e2", kind: "bool", bool_value: true };
    })).toMatch(/chỉ dùng cho số nguyên|cùng kiểu/);
  });

  it("while THIẾU max_iterations", () => {
    expect(reject((c) => {
      delete (c.statements as Record<string, unknown>[])[0].max_iterations;
    })).toMatch(/max_iterations/);
  });

  it("while vượt giới hạn lượt lặp", () => {
    expect(reject((c) => {
      (c.statements as Record<string, unknown>[])[0].max_iterations = 9999;
    })).toMatch(/vượt/);
  });

  it("biến chưa khai báo", () => {
    expect(reject((c) => {
      (c.expressions as Record<string, unknown>[])[0].name = "z";
    })).toMatch(/chưa được khai báo/);
  });

  it("config canonical mang KẾT QUẢ vẫn bị chặn (R0)", () => {
    expect(reject((c) => { c.trace = [{ fake: true }]; }))
      .toMatch(/KHÔNG được chứa kết quả/);
  });

  it("'expressions' không phải danh sách", () => {
    expect(reject((c) => { c.expressions = {}; })).toMatch(/phải là danh sách/);
  });
});

/**
 * VISIBILITY — thuyết minh bước xét điều kiện phải mang GIÁ TRỊ hiện tại.
 *
 * Audit tương tác 2026-08-03: ở 768×900 panel Quan sát đóng mặc định, nên bước
 * xét điều kiện là chỗ DUY NHẤT học sinh không thấy giá trị biến — đúng lúc câu
 * hỏi là "x còn ≤ 14 không?". Bước GÁN vốn đã nêu ("x ← x + 3 = 5.").
 *
 * Chỉ đổi CHỮ. Engine/state/timeline/bố cục/tương tác không đụng: dãy trace và
 * số bước phải y nguyên (khoá ở test dưới cùng).
 */
describe("thuyết minh bước điều kiện nêu giá trị hiện tại", () => {
  const mod = makeProgramModule();
  const run = () => {
    const v = mod.validateConfig(wireFixture.config as unknown);
    if (!v.ok) throw new Error(v.error);
    return mod.init(v.config) as ProgramSimState;
  };
  /** Các bước có sự kiện xét điều kiện — chính là bước cần sửa. */
  const condSteps = (st: ProgramSimState) =>
    st.trace.steps.filter((s) => s.events.some((e) => e.type === "evaluate_condition"));

  it("bước điều kiện ĐẦU nêu x = 2 và phép so sánh đầy đủ", () => {
    const first = condSteps(run())[0];
    expect(first.narration).toContain("x = 2");
    expect(first.narration).toContain("2 <= 14");
    expect(first.narration).toContain("ĐÚNG");
    expect(first.narration).toMatch(/vào thân vòng lặp/);
  });

  it("bước điều kiện GIỮA nêu đúng giá trị tại thời điểm đó", () => {
    const cs = condSteps(run());
    // lượt 1..5 xét x = 2,5,8,11,14 rồi lượt thoát xét x = 17
    expect(cs.map((s) => s.narration.match(/x = (-?\d+)/)![1]))
      .toEqual(["2", "5", "8", "11", "14", "17"]);
    expect(cs[3].narration).toContain("11 <= 14");
  });

  it("bước điều kiện CUỐI nêu x = 17, điều kiện SAI và lý do thoát", () => {
    const last = condSteps(run()).at(-1)!;
    expect(last.narration).toContain("x = 17");
    expect(last.narration).toContain("17 <= 14");
    expect(last.narration).toContain("SAI");
    expect(last.narration).toContain("thoát vòng lặp sau 5 lượt");
  });

  it("thuyết minh KHỚP snapshot engine ở mọi bước điều kiện", () => {
    for (const s of condSteps(run())) {
      const shown = s.narration.match(/x = (-?\d+)/)![1];
      expect(Number(shown)).toBe(s.snapshot.vars.x);   // chữ không được lệch state
    }
  });

  it("không lộ id biểu thức nội bộ trong thuyết minh", () => {
    for (const s of run().trace.steps) expect(s.narration).not.toMatch(/_e\d/);
  });

  it("KHÔNG đổi engine: số bước và dãy x giữ nguyên", () => {
    const st = run();
    expect(st.trace.steps.length).toBe(12);
    expect(st.completion).toBe("completed");
    expect(st.trace.steps.map((s) => s.snapshot.vars.x)
      .filter((x, i, a) => x !== a[i - 1])).toEqual([2, 5, 8, 11, 14, 17]);
  });
});
