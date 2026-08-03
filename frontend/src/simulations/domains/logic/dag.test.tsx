import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import {
  BoolDagInspector,
  evaluateDag,
  makeBoolDagModule,
  topoOrder,
  validateBoolDagConfig,
  type BoolDagConfig,
  type DagOp,
} from "./dag-module";
import type { Bit } from "./model";

/**
 * M17 W1 — logic.boolean_dag: oracle ĐỘC LẬP (đánh giá đệ quy viết riêng trong
 * test, không dùng code engine) đối chiếu mọi gán trị; validator fail-closed
 * (cycle, arity, ref, dangling); bảng chân trị đủ 2^n hàng; toggle tất định.
 */

/** Oracle đệ quy độc lập — KHÔNG dùng topo/evaluateDag của engine. */
function oracleEval(config: BoolDagConfig, values: Record<string, Bit>, id: string): Bit {
  if (id in values) return values[id];
  const gate = config.gates.find((g) => g.id === id)!;
  const vals = gate.inputs.map((r) => oracleEval(config, values, r));
  const table: Record<DagOp, (v: Bit[]) => Bit> = {
    AND: (v) => (v[0] === 1 && v[1] === 1 ? 1 : 0),
    OR: (v) => (v[0] === 1 || v[1] === 1 ? 1 : 0),
    XOR: (v) => (v[0] !== v[1] ? 1 : 0),
    NOT: (v) => (v[0] === 1 ? 0 : 1),
  };
  return table[gate.op](vals);
}

function valid(raw: unknown): BoolDagConfig {
  const v = validateBoolDagConfig(raw);
  if (!v.ok) throw new Error(v.error);
  return v.config;
}

// (A AND B) OR (NOT C) — 3 đầu vào, 3 cổng
const SAMPLE = {
  inputs: [
    { id: "A", value: 1 },
    { id: "B", value: 0 },
    { id: "C", value: 1 },
  ],
  gates: [
    { id: "g1", op: "AND", inputs: ["A", "B"] },
    { id: "g2", op: "NOT", inputs: ["C"] },
    { id: "g3", op: "OR", inputs: ["g1", "g2"] },
  ],
  output: "g3",
};

describe("engine DAG — oracle đệ quy độc lập trên MỌI gán trị", () => {
  it("mọi 2^3 gán trị: output từng cổng + đầu ra khớp oracle", () => {
    const config = valid(SAMPLE);
    const order = topoOrder(config)!;
    for (let mask = 0; mask < 8; mask++) {
      const values: Record<string, Bit> = {
        A: ((mask >> 2) & 1) as Bit,
        B: ((mask >> 1) & 1) as Bit,
        C: (mask & 1) as Bit,
      };
      const got = evaluateDag(config, values, order);
      for (const g of config.gates) {
        expect(got[g.id], `gán ${JSON.stringify(values)} cổng ${g.id}`).toBe(
          oracleEval(config, values, g.id),
        );
      }
    }
  });

  it("XOR đúng bán tổng: 0⊕0=0, 0⊕1=1, 1⊕0=1, 1⊕1=0", () => {
    const config = valid({
      inputs: [{ id: "x", value: 0 }, { id: "y", value: 0 }],
      gates: [{ id: "g", op: "XOR", inputs: ["x", "y"] }],
      output: "g",
    });
    const order = topoOrder(config)!;
    const rows: [Bit, Bit, Bit][] = [[0, 0, 0], [0, 1, 1], [1, 0, 1], [1, 1, 0]];
    for (const [x, y, want] of rows) {
      expect(evaluateDag(config, { x, y }, order)["g"]).toBe(want);
    }
  });

  it("bảng chân trị đủ 2^n hàng và cột cuối khớp oracle", () => {
    const mod = makeBoolDagModule();
    const v = mod.validateConfig(SAMPLE);
    if (!v.ok) throw new Error(v.error);
    const state = mod.init(v.config);
    expect(state.truthTable).toHaveLength(8);
    for (const row of state.truthTable) {
      expect(row.finalOutput).toBe(oracleEval(v.config, row.assignment, "g3"));
    }
  });
});

describe("validator fail-closed", () => {
  it("cycle bị từ chối", () => {
    const r = validateBoolDagConfig({
      inputs: [{ id: "A", value: 0 }],
      gates: [
        { id: "g1", op: "AND", inputs: ["A", "g2"] },
        { id: "g2", op: "NOT", inputs: ["g1"] },
      ],
      output: "g2",
    });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toContain("CYCLE");
  });

  it("arity sai bị từ chối (NOT 2 vào, AND 1 vào)", () => {
    expect(
      validateBoolDagConfig({
        inputs: [{ id: "A", value: 0 }, { id: "B", value: 0 }],
        gates: [{ id: "g", op: "NOT", inputs: ["A", "B"] }],
        output: "g",
      }).ok,
    ).toBe(false);
    expect(
      validateBoolDagConfig({
        inputs: [{ id: "A", value: 0 }],
        gates: [{ id: "g", op: "AND", inputs: ["A"] }],
        output: "g",
      }).ok,
    ).toBe(false);
  });

  it("ref không tồn tại / id trùng / output không phải cổng — từ chối", () => {
    expect(
      validateBoolDagConfig({
        inputs: [{ id: "A", value: 0 }],
        gates: [{ id: "g", op: "NOT", inputs: ["Z"] }],
        output: "g",
      }).ok,
    ).toBe(false);
    expect(
      validateBoolDagConfig({
        inputs: [{ id: "A", value: 0 }, { id: "A", value: 1 }],
        gates: [{ id: "g", op: "NOT", inputs: ["A"] }],
        output: "g",
      }).ok,
    ).toBe(false);
    expect(
      validateBoolDagConfig({
        inputs: [{ id: "A", value: 0 }],
        gates: [{ id: "g", op: "NOT", inputs: ["A"] }],
        output: "A",
      }).ok,
    ).toBe(false);
  });

  it("cổng lơ lửng không góp vào đầu ra bị từ chối", () => {
    const r = validateBoolDagConfig({
      inputs: [{ id: "A", value: 0 }, { id: "B", value: 0 }],
      gates: [
        { id: "g1", op: "AND", inputs: ["A", "B"] },
        { id: "g2", op: "OR", inputs: ["A", "B"] }, // không ai dùng
      ],
      output: "g1",
    });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toContain("g2");
  });

  it("quá 4 đầu vào / quá 8 cổng bị từ chối", () => {
    const many = Array.from({ length: 5 }, (_, i) => ({ id: `i${i}`, value: 0 }));
    expect(
      validateBoolDagConfig({ inputs: many, gates: [{ id: "g", op: "NOT", inputs: ["i0"] }], output: "g" }).ok,
    ).toBe(false);
  });
});

describe("module: toggle tất định + timeline + inspector đọc sự thật engine", () => {
  it("toggle đầu vào → engine đánh giá lại; hai lần toggle trở về ban đầu", () => {
    const mod = makeBoolDagModule();
    const v = mod.validateConfig(SAMPLE);
    if (!v.ok) throw new Error(v.error);
    const s0 = mod.init(v.config);
    const s1 = mod.apply(s0, { type: "toggle", target: "B" });
    // A=1,B=1 → g1=1 → g3=1 (bất kể NOT C)
    expect(s1.nodeOutputs["g3"]).toBe(1);
    const s2 = mod.apply(s1, { type: "toggle", target: "B" });
    expect(s2.nodeOutputs).toEqual(s0.nodeOutputs);
  });

  it("timeline: intro + mỗi cổng một bước eval + result", () => {
    const mod = makeBoolDagModule();
    const v = mod.validateConfig(SAMPLE);
    if (!v.ok) throw new Error(v.error);
    const state = mod.init(v.config);
    expect(state.steps).toHaveLength(1 + 3 + 1);
    expect(state.steps[0].kind).toBe("intro");
    expect(state.steps[state.steps.length - 1].kind).toBe("result");
  });

  it("inspector render đủ 8 hàng chân trị từ engine", () => {
    const mod = makeBoolDagModule();
    const v = mod.validateConfig(SAMPLE);
    if (!v.ok) throw new Error(v.error);
    const state = mod.init(v.config);
    const html = renderToString(
      <BoolDagInspector config={v.config} state={state} busy={false} dispatch={() => {}} />,
    ).replace(/<!--.*?-->/g, "");
    expect(html).toContain("8 hàng");
  });
});

/**
 * Audit độc lập 2026-08-03 — HÉ LỘ DẦN (DESIGN_BRIEF §3.3).
 *
 * Sân khấu đã giấu đầu ra từng cổng bằng "?", nhưng panel Quan sát in NGUYÊN
 * cột "Ra" của cả 8 hàng chân trị ngay từ bước 0 — trong đó có hàng ứng với
 * chính bộ đầu vào đang chạy. Học sinh mất cơ hội tự suy luận. Cùng lớp lỗi đã
 * được coi là defect thật và đã sửa ở inspector cây (M17-VR1 #2).
 *
 * Cách sửa nhỏ nhất: cột "Ra" dùng lại ĐÚNG idiom "?" của bảng cổng và chỉ mở ở
 * BƯỚC CUỐI. Dẫn xuất thuần từ `cursor` + `steps` — không thêm state trình bày,
 * không đụng engine, `truthTable` chuẩn giữ nguyên.
 */
describe("bảng chân trị không lộ đáp án trước bước cuối", () => {
  const mod = makeBoolDagModule();
  const setup = (cursor: number) => {
    const v = mod.validateConfig(SAMPLE);
    if (!v.ok) throw new Error(v.error);
    const base = mod.init(v.config);
    const state = { ...base, cursor };
    return {
      state,
      last: base.steps.length - 1,
      html: renderToString(
        <BoolDagInspector config={v.config} state={state} busy={false} dispatch={() => {}} />,
      ).replace(/<!--.*?-->/g, ""),
    };
  };
  /** Ô của cột "Ra" — lấy ô CUỐI mỗi hàng <tr> trong <tbody>. */
  const outputCells = (html: string): string[] => {
    const body = html.slice(html.indexOf("<tbody>"));
    return [...body.matchAll(/<tr[^>]*>([\s\S]*?)<\/tr>/g)].map((m) => {
      const tds = [...m[1].matchAll(/<td[^>]*>([\s\S]*?)<\/td>/g)].map((t) => t[1].trim());
      return tds[tds.length - 1] ?? "";
    });
  };

  it("engine vẫn sinh đủ bảng chân trị chuẩn (không đụng ngữ nghĩa)", () => {
    const { state } = setup(0);
    expect(state.truthTable).toHaveLength(8);
    // A=1,B=0,C=1 → g1=0, g2=NOT 1=0, g3=OR(0,0)=0
    const row = state.truthTable.find(
      (r) => r.assignment.A === 1 && r.assignment.B === 0 && r.assignment.C === 1,
    )!;
    expect(row.finalOutput).toBe(0);
  });

  it("bước 0: KHÔNG hàng nào lộ giá trị đầu ra", () => {
    const { html } = setup(0);
    const cells = outputCells(html);
    expect(cells).toHaveLength(8);
    expect(cells.every((c) => c === "?")).toBe(true);
  });

  it("bước 0: các cột ĐẦU VÀO vẫn hiện đủ để học sinh suy luận", () => {
    const { html } = setup(0);
    const body = html.slice(html.indexOf("<tbody>"));
    const rows = [...body.matchAll(/<tr[^>]*>([\s\S]*?)<\/tr>/g)];
    expect(rows).toHaveLength(8);
    // mỗi hàng vẫn có đủ 3 ô đầu vào + 1 ô đầu ra
    for (const r of rows) {
      expect([...r[1].matchAll(/<td[^>]*>/g)]).toHaveLength(4);
    }
    // và tổ hợp đầu vào phải đa dạng, không bị che
    expect(body).toMatch(/>0</);
    expect(body).toMatch(/>1</);
  });

  it("bước giữa (đã đánh giá vài cổng) vẫn chưa mở cột Ra", () => {
    const { html } = setup(2);
    expect(outputCells(html).every((c) => c === "?")).toBe(true);
  });

  it("bước CUỐI: cột Ra mở đủ 8 hàng, khớp truthTable của engine", () => {
    const { state, html } = setup(99); // clamp về bước cuối
    const cells = outputCells(html);
    expect(cells).toEqual(state.truthTable.map((r) => String(r.finalOutput)));
    expect(cells.some((c) => c === "?")).toBe(false);
  });

  it("trạng thái ẩn/hiện KHÔNG chỉ bằng màu — dùng ký tự '?' đọc được", () => {
    const { html } = setup(0);
    expect(html).toContain("?");
  });
});
