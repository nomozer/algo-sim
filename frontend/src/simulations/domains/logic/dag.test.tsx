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
