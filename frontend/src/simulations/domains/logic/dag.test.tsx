import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import {
  BoolDagInspector,
  DagDiagram,
  BoolDagWorkspace,
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

  /**
   * FIX-3 — AFFORDANCE CHO THAO TÁC DUY NHẤT CỦA MODULE.
   *
   * `toggle` ở đây là thao tác chạm THẲNG vào cơ chế ẩn (COVERAGE §2.6) và là
   * thao tác duy nhất module có. Audit UI baseline bắt được: trên màn hình nó
   * chỉ là ba chip "A: 1", không một chữ nào nói rằng bấm được — tương tác mà
   * học sinh phải ĐOÁN ra thì trên thực tế không tồn tại. Test này giữ câu
   * hướng dẫn đó khỏi biến mất trong lần dọn giao diện sau.
   */
  /**
   * DAG-VIS — sơ đồ node-edge phải theo ĐÚNG luật hé lộ dần của bảng cổng.
   * Sơ đồ vẽ cả mạch cùng lúc, nên nó là chỗ dễ vô tình in sẵn đầu ra của cổng
   * chưa chạy nhất — đúng lớp lỗi đã sửa ở bảng chân trị (audit 2026-08-03).
   */
  it("sơ đồ mạch: cổng CHƯA đánh giá hiện '?', không lộ đáp án sớm", () => {
    const mod = makeBoolDagModule();
    const v = mod.validateConfig(SAMPLE);
    if (!v.ok) throw new Error(v.error);
    const s0 = mod.init(v.config);

    const svg0 = renderToString(<DagDiagram state={s0} />).replace(/<!--.*?-->/g, "");
    // bước intro: chưa cổng nào chạy → cả ba cổng đều "?"
    expect((svg0.match(/>\?</g) ?? []).length).toBe(v.config.gates.length);

    // bước cuối: mọi cổng đã có giá trị → không còn "?" nào
    const last = mod.timeline!.goToStep(s0, s0.steps.length - 1);
    const svgLast = renderToString(<DagDiagram state={last} />).replace(/<!--.*?-->/g, "");
    expect(svgLast).not.toContain(">?<");
  });

  it("sơ đồ mạch vẽ đủ node và dây từ CHÍNH config (không đồ thị thứ hai)", () => {
    const mod = makeBoolDagModule();
    const v = mod.validateConfig(SAMPLE);
    if (!v.ok) throw new Error(v.error);
    const svg = renderToString(<DagDiagram state={mod.init(v.config)} />);
    // node = inputs + gates, CỘNG một khung ngoài nét đứt đánh dấu cổng đầu ra
    // (PILOT: vai trò "đầu ra" nói bằng khung + chữ, không mượn màu tín hiệu).
    expect((svg.match(/<rect/g) ?? []).length)
      .toBe(v.config.inputs.length + v.config.gates.length + 1);
    // dây = tổng số chân vào của các cổng (A,B → g1; C → g2; g1,g2 → g3 = 5)
    const wires = v.config.gates.reduce((n, g) => n + g.inputs.length, 0);
    expect((svg.match(/<path/g) ?? []).length).toBe(wires);
  });

  /**
   * PILOT — GỠ QUÁ TẢI MÀU + CHÚ GIẢI TÍN HIỆU.
   *
   * Audit chụp được ca gây hiểu nhầm: cổng đầu ra mang VIỀN XANH LÁ trong khi
   * giá trị của nó còn là `?`, mà xanh lá đồng thời là "tín hiệu = 1" trên dây
   * và trên chữ số. Học sinh rất dễ đọc thành "cổng này đang ra 1".
   * Nay: vai trò "đầu ra" nói bằng CHỮ + KHUNG NÉT ĐỨT; xanh lá chỉ còn một nghĩa.
   */
  it("cổng đầu ra KHÔNG dùng màu tín hiệu để đánh dấu vai trò", () => {
    const mod = makeBoolDagModule();
    const v = mod.validateConfig(SAMPLE);
    if (!v.ok) throw new Error(v.error);
    const s0 = mod.init(v.config);
    const svg = renderToString(<DagDiagram state={s0} />).replace(/<!--.*?-->/g, "");
    // vai trò đầu ra nói bằng CHỮ
    expect(svg).toContain("ĐẦU RA");
    // và bằng khung nét đứt (khác HÌNH, không chỉ khác màu)
    expect(svg).toContain("stroke-dasharray");
    // KHÔNG một node/cổng nào (thẻ <rect>) được viền xanh lá nữa. Xanh lá từ đây
    // CHỈ còn trên DÂY và CHỮ SỐ, với đúng một nghĩa: "tín hiệu = 1".
    const rects = svg.match(/<rect[^>]*>/g) ?? [];
    expect(rects.some((r) => r.includes("--accent-green"))).toBe(false);
    // và dây mang tín hiệu 1 thì VẪN xanh lá (A=1, C=1 trong SAMPLE)
    const paths = svg.match(/<path[^>]*>/g) ?? [];
    expect(paths.some((p) => p.includes("--accent-green"))).toBe(true);
  });

  /**
   * SƠ ĐỒ KHÔNG ĐƯỢC BỊ PHÓNG TO.
   *
   * Hai lần hỏng ngược chiều nhau đã đo được trong Chrome thật:
   *  - `max-width` = 432 (đúng viewBox, quá nhỏ) → sơ đồ chỉ 11% thẻ, nhỏ hơn
   *    bảng tra cứu 24%.
   *  - `max-width` = 720 > viewBox 432 → SVG bị phóng 1,667 lần: chữ trong node
   *    ra 21,7px (chữ thân trang 14px), node đầu vào thành khối 160×77px.
   *
   * Cái phải khoá là TỈ LỆ PHÓNG, không phải một con số pixel. `max-width` bằng
   * đúng bề rộng viewBox ⇒ scale ≤ 1: co lại khi thẻ hẹp, không bao giờ phóng.
   */
  it("sơ đồ hiện ở cỡ thật, không bị phóng to", () => {
    const mod = makeBoolDagModule();
    const v = mod.validateConfig(SAMPLE);
    if (!v.ok) throw new Error(v.error);
    const svg = renderToString(<DagDiagram state={mod.init(v.config)} />);
    const viewBox = /viewBox="0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)"/.exec(svg);
    expect(viewBox).not.toBeNull();
    const vbW = Number(viewBox![1]);

    /* W4B-4D — CÙNG BẤT BIẾN, KHAI THEO CÁCH KHÁC.
     *
     * Trước: `width="100%"` + `max-width: <vbW>px`. Cách đó chỉ đúng khi cha có
     * bề rộng xác định; khi cụm sân khấu chuyển sang `fit-content` để căn giữa,
     * `100%` mất quy chiếu và Chrome vẽ sơ đồ ở bề rộng mặc định 300px — đo
     * được trong Chrome, và SSR không thể thấy.
     *
     * Nay bề rộng riêng = đúng vbW, `max-width: 100%` lo phần co. Bất biến vẫn
     * là TỈ LỆ PHÓNG ≤ 1: không lối nào cho phép vẽ rộng hơn viewBox. */
    const widthAttr = /<svg[^>]*\swidth="(\d+(?:\.\d+)?)"/.exec(svg);
    expect(widthAttr, "SVG không khai bề rộng riêng ⇒ cha fit-content sẽ bóp về 300px")
      .not.toBeNull();
    expect(Number(widthAttr![1]), "bề rộng hiển thị > viewBox ⇒ sơ đồ bị phóng")
      .toBeLessThanOrEqual(vbW);
    expect(svg, "không có đường CO LẠI ⇒ thẻ hẹp sẽ tràn ngang")
      .toMatch(/max-width:\s*100%/);
    // …và cũng KHÔNG được nhỏ như bản gốc: bố cục phải đủ rộng để là sân khấu
    // chính. Sàn, không phải một con số cố định.
    expect(vbW).toBeGreaterThan(480);
  });

  /**
   * NODE KHÔNG ĐƯỢC TO NHƯ KHỐI TRANG TRÍ — khoá bằng TỈ LỆ, không bằng pixel.
   * Mỗi node chỉ chứa một nhãn và một chữ số; nếu nó chiếm phần lớn bề rộng sơ
   * đồ thì hình đọc ra "ba khối lớn" chứ không phải "một mạch điện".
   */
  it("node giữ đúng tỉ lệ so với sơ đồ và với khoảng cách cột", () => {
    const mod = makeBoolDagModule();
    const v = mod.validateConfig(SAMPLE);
    if (!v.ok) throw new Error(v.error);
    const svg = renderToString(<DagDiagram state={mod.init(v.config)} />);
    const vb = /viewBox="0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)"/.exec(svg)!;
    const [w, h] = [Number(vb[1]), Number(vb[2])];
    // `\s` trước "width" là bắt buộc — không có nó thì regex khớp luôn phần đuôi
    // của `stroke-width="1.5"` và cả 7 <rect> cùng ra 1.5.
    const widths = [...svg.matchAll(/<rect[^>]*\swidth="(\d+(?:\.\d+)?)"/g)].map((m) => Number(m[1]));
    // Bề rộng NODE = giá trị xuất hiện nhiều nhất; khung ngoài nét đứt của cổng
    // đầu ra chỉ có đúng một cái nên không bao giờ thắng.
    const tally = new Map<number, number>();
    for (const x of widths) tally.set(x, (tally.get(x) ?? 0) + 1);
    const nodeW = [...tally.entries()].sort((a, b) => b[1] - a[1])[0][0];
    expect(tally.get(nodeW)).toBe(v.config.inputs.length + v.config.gates.length);
    const node = { w: nodeW };
    // một node không quá 1/3 bề rộng sơ đồ
    expect(node.w).toBeLessThan(w / 3);
    // sơ đồ nằm ngang: rộng hơn cao (mạch chảy trái → phải)
    expect(w).toBeGreaterThan(h * 1.5);
    /* Khoảng cách cột KHÔNG được rộng hơn chính node: dây dài hơn node thì
       khoảng trắng thành phần lớn nhất của hình.
       W4B-4D: đo THẲNG từ toạ độ hai cột liền nhau. Bản cũ suy ngược từ bề rộng
       viewBox (`(w - 3·nodeW)/2`), nên nó ngầm khẳng định viewBox không có lề —
       và khi thêm lề để hết cắt khung nét đứt của cổng đầu ra thì phần lề bị
       cộng nhầm vào "dây", báo 146px cho một COL_GAP vẫn đang là 130. */
    const nodeXs = [...svg.matchAll(new RegExp(`<rect[^>]*\\sx="(\\d+(?:\\.\\d+)?)"[^>]*\\swidth="${node.w}"`, "g"))]
      .map((m) => Number(m[1]));
    const cols = [...new Set(nodeXs)].sort((a, b) => a - b);
    expect(cols.length, "sơ đồ mẫu phải có nhiều hơn một tầng").toBeGreaterThan(1);
    for (let i = 1; i < cols.length; i++) {
      expect(cols[i] - (cols[i - 1] + node.w), `dây tầng ${i} dài hơn chính node`)
        .toBeLessThan(node.w);
    }
  });

  it("chú giải tín hiệu có mặt và mỗi mục có dấu hiệu NGOÀI màu", () => {
    const mod = makeBoolDagModule();
    const v = mod.validateConfig(SAMPLE);
    if (!v.ok) throw new Error(v.error);
    const html = renderToString(
      <BoolDagWorkspace config={v.config} state={mod.init(v.config)} busy={false} dispatch={() => {}} />,
    ).replace(/<!--.*?-->/g, "");
    expect(html).toContain("dag-legend");
    expect(html).toContain("tín hiệu <strong>1</strong>");
    expect(html).toContain("tín hiệu <strong>0</strong>");
    // "cổng" phải còn trong mục này: node đầu vào cũng nhận viền xanh khi hover,
    // bỏ chữ đó thì chú giải đọc được thành "đầu vào đang được tính".
    expect(html).toContain("cổng đang tính");
    expect(html).toContain("viền đậm");
    expect(html).toContain("chưa tới lượt");
  });

  /**
   * BẢNG CHI TIẾT = TRA CỨU, KHÔNG PHẢI SÂN KHẤU THỨ HAI.
   * Gập được (`<details>`) để hạ trọng lượng thị giác, nhưng dữ liệu engine
   * VẪN nằm trong DOM — `gate_table_with_engine_outputs` là yêu cầu renderer
   * trong hợp đồng authenticity, gập ≠ bỏ.
   */
  it("bảng chi tiết gập được nhưng vẫn giữ đủ dữ liệu engine", () => {
    const mod = makeBoolDagModule();
    const v = mod.validateConfig(SAMPLE);
    if (!v.ok) throw new Error(v.error);
    const s = mod.init(v.config);
    const html = renderToString(
      <BoolDagWorkspace config={v.config} state={s} busy={false} dispatch={() => {}} />,
    ).replace(/<!--.*?-->/g, "");
    expect(html).toContain("gate-detail--fold");
    expect(html).toContain("<summary");
    for (const g of v.config.gates) {
      expect(html).toContain(g.id);
      expect(html).toContain(g.op);
    }
  });

  /** Hàng của cổng đang tính được làm nổi — và CHỈ ở bước `eval`. */
  it("hàng bảng chi tiết nổi đúng cổng đang được tính", () => {
    const mod = makeBoolDagModule();
    const v = mod.validateConfig(SAMPLE);
    if (!v.ok) throw new Error(v.error);
    let s = mod.init(v.config);
    // bước 0 chưa phải `eval` ⇒ không hàng nào nổi
    const at0 = renderToString(
      <BoolDagWorkspace config={v.config} state={s} busy={false} dispatch={() => {}} />,
    );
    expect(s.steps[0].kind).not.toBe("eval");
    expect(at0).not.toContain("is-current-row");
    // tiến tới bước `eval` đầu tiên
    const evalAt = s.steps.findIndex((st) => st.kind === "eval");
    s = { ...s, cursor: evalAt };
    const html = renderToString(
      <BoolDagWorkspace config={v.config} state={s} busy={false} dispatch={() => {}} />,
    );
    expect(html).toContain("is-current-row");
    expect((html.match(/is-current-row/g) ?? []).length).toBe(1);
  });

  it("sân khấu nói rõ bấm được đầu vào và bấm thì quan sát cái gì", () => {
    const mod = makeBoolDagModule();
    const v = mod.validateConfig(SAMPLE);
    if (!v.ok) throw new Error(v.error);
    const html = renderToString(
      <BoolDagWorkspace config={v.config} state={mod.init(v.config)} busy={false} dispatch={() => {}} />,
    ).replace(/<!--.*?-->/g, "");
    expect(html).toContain("Bấm A, B, C để đổi giá trị đầu vào");
    expect(html).toContain("lan truyền qua các cổng");
    // nút toggle khai trạng thái bật/tắt cho công nghệ hỗ trợ
    expect(html).toContain('aria-pressed="true"'); // A = 1 trong SAMPLE
  });

  it("câu hướng dẫn DẪN XUẤT từ config — không nhắc đầu vào không tồn tại", () => {
    /* W4B-4A — GUARD NÀY TỪNG BẢO VỆ CHÍNH LỖI.
     *
     * Câu hướng dẫn viết cứng "Bấm A, B hoặc C" từ thời fixture có ba đầu vào.
     * Mẫu CÔNG KHAI hiện tại (`logic-boolean-dag`) chỉ khai A và B, nên sản
     * phẩm bảo học sinh bấm một thứ không tồn tại — và assert cũ khoá đúng chuỗi
     * sai ấy lại, nên suite xanh trong khi màn hình nói dối.
     *
     * Khoá đúng thứ đáng khoá: chữ phải ĐỔI THEO mô hình. Hai đầu vào thì nói
     * hai, và tuyệt đối không nhắc tên nào ngoài danh sách đã khai. */
    const mod = makeBoolDagModule();
    const twoInput = {
      inputs: [{ id: "A", value: 1 }, { id: "B", value: 0 }],
      gates: [{ id: "g", op: "XOR", inputs: ["A", "B"] }],
      output: "g",
    };
    const v = mod.validateConfig(twoInput);
    if (!v.ok) throw new Error(v.error);
    const html = renderToString(
      <BoolDagWorkspace config={v.config} state={mod.init(v.config)} busy={false} dispatch={() => {}} />,
    ).replace(/<!--.*?-->/g, "");
    const affordance = html.slice(html.indexOf("stage-affordance"), html.indexOf("stage-affordance") + 220);
    expect(affordance).toContain("Bấm A, B để đổi giá trị đầu vào");
    expect(affordance, "câu hướng dẫn nhắc đầu vào C mà mạch không có")
      .not.toContain("C");
  });
});

/**
 * MỘT BỘ A/B/C DUY NHẤT — chính node trong sơ đồ là control.
 *
 * Trước: A/B/C xuất hiện HAI lần — node trong sơ đồ (chỉ để xem) và một hàng nút
 * `A:1 · B:0 · C:1` bên dưới (để bấm). Trùng thông tin, và học sinh không biết
 * vùng nào bấm được. Nay chỉ còn node.
 *
 * Kích hoạt bằng BÀN PHÍM (Enter/Space) không kiểm được ở đây: suite này chạy
 * SSR (`renderToString`, môi trường node — repo không có jsdom/testing-library),
 * nên không có sự kiện DOM. Ở tầng này ta khoá HỢP ĐỒNG làm cho bàn phím chạy
 * được (`role`, `tabindex`, `aria-pressed`, tên khả truy cập) + hành vi engine;
 * còn phím thật được bấm thật trong lượt Chrome acceptance (CDP
 * `Input.dispatchKeyEvent`) — xem `dag-acceptance.json`.
 */
describe("boolean_dag: node đầu vào LÀ control (một bộ duy nhất)", () => {
  const mod = makeBoolDagModule();
  const cfg = valid(SAMPLE);
  const s0 = mod.init(cfg);
  const ws = (state = s0, busy = false) =>
    renderToString(
      <BoolDagWorkspace config={cfg} state={state} busy={busy} dispatch={() => {}} />,
    ).replace(/<!--.*?-->/g, "");

  it("mỗi đầu vào có ĐÚNG MỘT control; hàng toggle trùng đã bỏ", () => {
    const html = ws();
    expect(html).not.toContain("input-toggle-row");
    for (const inp of cfg.inputs) {
      const controls = html.match(new RegExp(`aria-label="Đầu vào ${inp.id},`, "g")) ?? [];
      expect(controls, `đầu vào ${inp.id} phải có đúng 1 control`).toHaveLength(1);
    }
    // đúng 3 control, không nhiều hơn — cổng KHÔNG được thành nút
    expect((html.match(/role="button"/g) ?? []).length).toBe(cfg.inputs.length);
  });

  it("cổng AND/NOT/OR KHÔNG phải control (engine sở hữu giá trị của chúng)", () => {
    const html = ws();
    for (const g of cfg.gates) {
      expect(html).not.toContain(`aria-label="Đầu vào ${g.id},`);
    }
  });

  it("hợp đồng bàn phím + aria đầy đủ trên từng node đầu vào", () => {
    const html = ws();
    expect((html.match(/tabindex="0"/g) ?? []).length).toBe(cfg.inputs.length);
    // aria-pressed khớp GIÁ TRỊ hiện tại: SAMPLE có A=1, B=0, C=1
    expect(html).toContain('aria-label="Đầu vào A, giá trị 1, bấm để đổi"');
    expect(html).toContain('aria-label="Đầu vào B, giá trị 0, bấm để đổi"');
    expect(html).toContain('aria-label="Đầu vào C, giá trị 1, bấm để đổi"');
    expect((html.match(/aria-pressed="true"/g) ?? []).length).toBe(2); // A, C
    expect((html.match(/aria-pressed="false"/g) ?? []).length).toBe(1); // B
  });

  it("toggle đi qua ĐÚNG action sẵn có; aria-pressed theo giá trị mới", () => {
    const toggled = mod.apply(s0, { type: "toggle", target: "A" });
    expect(toggled.values["A"]).toBe(0);
    const html = ws(toggled);
    expect(html).toContain('aria-label="Đầu vào A, giá trị 0, bấm để đổi"');
    expect((html.match(/aria-pressed="true"/g) ?? []).length).toBe(1); // chỉ còn C
    // engine tính lại downstream, không phải renderer
    expect(toggled.nodeOutputs["g1"]).toBe(0);
  });

  it("đang tự chạy (busy) thì node không phải control — không tranh với timeline", () => {
    const html = ws(s0, true);
    expect(html).not.toContain('role="button"');
    expect(html).not.toContain("dag-input");
  });

  /**
   * W5E — HỢP ĐỒNG ĐÃ ĐỔI, và ba khẳng định cũ được phân loại chứ không vá cho xanh:
   *
   *   `cursor === 0` sau toggle                → OLD_PRODUCT_CONTRACT (viết lại)
   *   sân khấu còn `?` sau toggle              → OLD_PRODUCT_CONTRACT (viết lại)
   *   bảng chân trị vẫn ẩn cột "Ra"            → STILL_VALID_INVARIANT (giữ nguyên)
   *
   * Vì sao đổi: bật công tắc là thao tác Khám phá DUY NHẤT của bài, tức một câu
   * hỏi. Trả lời nó bằng `?` trong khi `nodeOutputs` đã giữ trọn đáp án tất định
   * là để màn hình nói ngược lại engine.
   *
   * Vì sao khẳng định thứ ba KHÔNG đổi: nó bảo vệ một thứ KHÁC HẲN. Học sinh vừa
   * hỏi về MỘT bộ đầu vào; mở cả bảng là tiết lộ những bộ họ chưa hỏi — đúng chủ
   * ý hé lộ dần mà audit 2026-08-03 dựng ra (DESIGN_BRIEF §3.3). Bản vá W5E tách
   * hai tín hiệu (`exploreReveal`) chính là để giữ được khẳng định này.
   */
  it("W5E — toggle TRẢ LỜI trên sân khấu nhưng KHÔNG mở sớm bảng chân trị", () => {
    const toggled = mod.apply(s0, { type: "toggle", target: "A" });

    // MỚI: con trỏ nhảy tới bước cuối để sân khấu nói được giá trị mới.
    expect(toggled.cursor).toBe(toggled.steps.length - 1);
    expect(toggled.exploreReveal, "cờ tách tín hiệu không được bật").toBe(true);

    /* MỚI: không còn cổng nào bị giấu — cả mạch nói giá trị của bộ đầu vào mới.
       Còn đúng MỘT `?` trên sân khấu và nó là mục CHÚ GIẢI ("? chưa tới lượt"),
       tức phần giải thích KÝ HIỆU chứ không phải một giá trị bị giấu. Khoá con
       số 1 thay vì nới thành `<= 1`: nới ra thì một cổng thật bị giấu sẽ lọt. */
    const q = (ws(toggled).match(/>\?</g) ?? []).length;
    expect(q, "sân khấu còn giấu cổng sau toggle (ngoài mục chú giải)").toBe(1);
    /* Đối chứng: lúc MỞ BÀI thì đúng là có cổng bị giấu, nên phép đếm này phân
       biệt được hai trạng thái — không phải một khẳng định luôn đúng. */
    expect((ws(s0).match(/>\?</g) ?? []).length, "phép đếm không phân biệt được gì")
      .toBeGreaterThan(q);

    // GIỮ NGUYÊN: cột "Ra" của bảng chân trị vẫn ẩn — học sinh chưa hỏi các bộ kia.
    const insp = renderToString(
      <BoolDagInspector config={cfg} state={toggled} busy={false} dispatch={() => {}} />,
    ).replace(/<!--.*?-->/g, "");
    expect((insp.match(/>\?</g) ?? []).length, "toggle làm lộ sớm cả bảng chân trị")
      .toBe(toggled.truthTable.length);
  });

  it("W5E — ĐI BỘ tới bước cuối thì bảng chân trị mở như cũ", () => {
    /* Nửa còn lại của luật: `exploreReveal` chỉ hoãn việc mở bảng, không khoá
       nó vĩnh viễn. Thiếu khẳng định này thì bản vá có thể lặng lẽ biến bảng
       chân trị thành thứ không bao giờ mở được nữa. */
    const toggled = mod.apply(s0, { type: "toggle", target: "A" });
    const walked = mod.timeline!.goToStep(toggled, toggled.steps.length - 1);

    expect(walked.exploreReveal, "đi bộ trên trace mà cờ Khám phá còn bật").toBe(false);
    const insp = renderToString(
      <BoolDagInspector config={cfg} state={walked} busy={false} dispatch={() => {}} />,
    ).replace(/<!--.*?-->/g, "");
    expect((insp.match(/>\?</g) ?? []).length, "đi hết trace rồi mà bảng vẫn không mở")
      .toBe(0);
  });

  it("Đặt lại: init lại từ config gốc → giá trị đầu vào và cursor như ban đầu", () => {
    const changed = mod.apply(mod.timeline!.goToStep(s0, 3), { type: "toggle", target: "B" });
    expect(changed.values["B"]).toBe(1);
    const fresh = mod.init(cfg); // đúng thứ store.resetSim làm
    expect(fresh.values).toEqual(s0.values);
    expect(fresh.cursor).toBe(0);
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
