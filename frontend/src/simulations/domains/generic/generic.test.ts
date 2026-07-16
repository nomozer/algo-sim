import { describe, expect, it } from "vitest";
import { makeGenericModule } from "./index";
import {
  buildTimeline,
  childrenOf,
  currentStepObjectIds,
  GenericExecutionError,
  initialBase,
  inspectorGroups,
  isObjectRenderable,
  isVisible,
  objectRole,
  structuralRoots,
  valuesOf,
  type SimulationSpec,
} from "./model";
import { validateGenericConfig } from "./validate";
import { andOutput } from "../logic/model";
import { decimalOf } from "../binary/model";
import { makeNetworkModule } from "../network";
import {
  GENERIC_AND_SPEC,
  GENERIC_BINARY_SPEC,
  GENERIC_PACKET_SPEC,
  GENERIC_REVEAL_SPEC,
  GENERIC_WEB_SPEC,
} from "../../../data/sim-samples";

/**
 * Test generic engine (M6) + BENCHMARK: hành vi generic ≡ module chuyên biệt.
 */

const mod = makeGenericModule();

function spec(raw: object): SimulationSpec {
  const r = mod.validateConfig(raw);
  if (!r.ok) throw new Error(r.error);
  return r.config;
}

function serializable(obj: unknown) {
  expect(JSON.parse(JSON.stringify(obj))).toEqual(obj);
}

describe("generic engine cơ bản", () => {
  it("boolean AND: toggle hai switch → lamp đúng", () => {
    const s0 = mod.init(spec(GENERIC_AND_SPEC));
    expect(valuesOf(s0.spec, s0.base).y).toBe(0);
    const s1 = mod.apply(s0, { type: "toggle", target: "a" });
    expect(valuesOf(s1.spec, s1.base).y).toBe(0); // 1 AND 0
    const s2 = mod.apply(s1, { type: "toggle", target: "b" });
    expect(valuesOf(s2.spec, s2.base).y).toBe(1); // 1 AND 1
    expect(valuesOf(s0.spec, s0.base).y).toBe(0); // state cũ không đổi (pure)
  });

  it("weighted_sum: init 13 → value_box = 13; toggle cập nhật", () => {
    let s = mod.init(spec(GENERIC_BINARY_SPEC));
    expect(valuesOf(s.spec, s.base).out).toBe(13); // 8+4+1
    s = mod.apply(s, { type: "toggle", target: "bit2" }); // bật thêm trọng số 2
    expect(valuesOf(s.spec, s.base).out).toBe(15);
    s = mod.apply(s, { type: "toggle", target: "bit0" }); // tắt trọng số 8
    expect(valuesOf(s.spec, s.base).out).toBe(7);
  });

  it("object.weight bị từ chối tường minh — không strip im lặng (M13 Task 2b)", () => {
    const r = mod.validateConfig({
      dsl_version: "1.0",
      title: "x",
      objects: [
        { id: "b0", type: "switch", label: "8", value: 1, weight: 8 },
        { id: "out", type: "value_box", label: "Giá trị" },
      ],
      rules: [{ type: "weighted_sum", target: "out", inputs: ["b0"], weights: [8] }],
    });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toContain("không còn được hỗ trợ");
  });

  it("move_along_path: timeline tất định theo path", () => {
    const s = mod.init(spec(GENERIC_PACKET_SPEC));
    expect(mod.timeline!.stepCount(s)).toBe(4); // create + 3 hop
    const positions = s.timeline.map((f) => f.entityPos.pkt);
    expect(positions).toEqual(["client", "router", "isp", "server"]);
  });

  it("timeline optional: có process → >1 bước; không process → 1 bước", () => {
    const withProc = mod.init(spec(GENERIC_PACKET_SPEC));
    expect(mod.timeline!.stepCount(withProc)).toBeGreaterThan(1);
    const noProc = mod.init(spec(GENERIC_AND_SPEC));
    expect(mod.timeline!.stepCount(noProc)).toBe(1); // Controls sẽ ẩn nút bước
  });

  it("goToStep pure + clamp", () => {
    const s = mod.init(spec(GENERIC_PACKET_SPEC));
    const tl = mod.timeline!;
    expect(tl.currentStep(tl.goToStep(s, 2))).toBe(2);
    expect(tl.currentStep(s)).toBe(0);
    expect(tl.currentStep(tl.goToStep(s, 99))).toBe(3);
    expect(tl.currentStep(tl.goToStep(s, -1))).toBe(0);
  });

  it("getExplainContext serializable", () => {
    serializable(mod.getExplainContext(mod.init(spec(GENERIC_AND_SPEC)), spec(GENERIC_AND_SPEC)));
    serializable(mod.getExplainContext(mod.init(spec(GENERIC_PACKET_SPEC)), spec(GENERIC_PACKET_SPEC)));
  });
});

describe("validateConfig từ chối spec sai (§5)", () => {
  it("object type lạ", () => {
    expect(mod.validateConfig({ title: "x", objects: [{ id: "a", type: "hologram" }] }).ok).toBe(false);
  });
  it("rule type lạ", () => {
    const r = mod.validateConfig({
      title: "x",
      objects: [{ id: "a", type: "switch", value: 0 }, { id: "y", type: "lamp" }],
      rules: [{ type: "quantum", inputs: ["a"], target: "y" }],
    });
    expect(r.ok).toBe(false);
  });
  it("tham chiếu treo (dangling ref)", () => {
    const r = mod.validateConfig({
      title: "x",
      objects: [{ id: "a", type: "switch", value: 0 }],
      rules: [{ type: "boolean", op: "and", inputs: ["khong-co"], target: "a" }],
    });
    expect(r.ok).toBe(false);
  });
  it("khóa bị cấm (timeline)", () => {
    expect(mod.validateConfig({ title: "x", objects: [{ id: "a", type: "switch" }], timeline: [] }).ok).toBe(false);
  });
  it("chu trình rule", () => {
    const r = mod.validateConfig({
      title: "x",
      objects: [{ id: "p", type: "value_box" }, { id: "q", type: "value_box" }],
      rules: [
        { type: "weighted_sum", inputs: ["q"], weights: [1], target: "p" },
        { type: "weighted_sum", inputs: ["p"], weights: [1], target: "q" },
      ],
    });
    expect(r.ok).toBe(false);
  });
  // M11: rule lồng (target làm input rule khác) hợp lệ; trùng target thì không —
  // rule sau thắng mỗi vòng quét điểm bất động → phụ thuộc thứ tự khai báo.
  it("rule lồng qua trung gian hợp lệ (M11)", () => {
    const r = mod.validateConfig({
      dsl_version: "1.0",
      title: "Đèn A và (B hoặc C)",
      objects: [
        { id: "a", type: "switch", value: 0 },
        { id: "b", type: "switch", value: 0 },
        { id: "c", type: "switch", value: 0 },
        { id: "t", type: "lamp", label: "B hoặc C" },
        { id: "y", type: "lamp" },
      ],
      rules: [
        { type: "boolean", op: "or", inputs: ["b", "c"], target: "t" },
        { type: "boolean", op: "and", inputs: ["a", "t"], target: "y" },
      ],
      interactions: [
        { type: "toggle", target: "a" },
        { type: "toggle", target: "b" },
        { type: "toggle", target: "c" },
      ],
    });
    expect(r.ok).toBe(true);
  });
  it("hai rule cùng ghi một target bị reject (M11)", () => {
    const r = mod.validateConfig({
      dsl_version: "1.0",
      title: "x",
      objects: [
        { id: "a", type: "switch", value: 0 },
        { id: "b", type: "switch", value: 0 },
        { id: "y", type: "lamp" },
      ],
      rules: [
        { type: "boolean", op: "and", inputs: ["a", "b"], target: "y" },
        { type: "boolean", op: "or", inputs: ["a", "b"], target: "y" },
      ],
    });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toContain("y");
  });
  it("vượt giới hạn số object", () => {
    const objects = Array.from({ length: 21 }, (_, i) => ({ id: `o${i}`, type: "label" }));
    expect(mod.validateConfig({ title: "x", objects }).ok).toBe(false);
  });

  it("dsl_version không hỗ trợ bị reject (§9)", () => {
    const r = mod.validateConfig({
      dsl_version: "2.0",
      title: "x",
      objects: [{ id: "a", type: "switch", value: 0 }],
    });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toContain("dsl_version");
    // "1.0" vẫn chạy
    expect(mod.validateConfig({ dsl_version: "1.0", title: "x", objects: [{ id: "a", type: "label" }] }).ok).toBe(true);
  });
});

describe("BENCHMARK — generic ≡ specialized (§6)", () => {
  it("AND: generic khớp andOutput chuyên biệt cho cả 4 tổ hợp", () => {
    const combos: [0 | 1, 0 | 1][] = [
      [0, 0],
      [0, 1],
      [1, 0],
      [1, 1],
    ];
    for (const [a, b] of combos) {
      let s = mod.init(spec(GENERIC_AND_SPEC));
      if (a === 1) s = mod.apply(s, { type: "toggle", target: "a" });
      if (b === 1) s = mod.apply(s, { type: "toggle", target: "b" });
      const genericY = valuesOf(s.spec, s.base).y;
      const specialized = andOutput({ inputA: a, inputB: b });
      expect(genericY).toBe(specialized);
    }
  });

  it("binary: generic value_box khớp decimalOf chuyên biệt", () => {
    const g = mod.init(spec(GENERIC_BINARY_SPEC));
    const genericDecimal = valuesOf(g.spec, g.base).out;
    // binary chuyên biệt: 13 = bits [1,1,0,1] với 4 bit
    const specializedDecimal = decimalOf({ bits: [1, 1, 0, 1], bitWidth: 4 });
    expect(genericDecimal).toBe(specializedDecimal);
    expect(genericDecimal).toBe(13);
  });

  it("packet: generic path khớp route BFS chuyên biệt", () => {
    const g = mod.init(spec(GENERIC_PACKET_SPEC));
    const genericPath = g.timeline.map((f) => f.entityPos.pkt);

    const net = makeNetworkModule();
    const ns = net.init({
      nodes: [
        { id: "client", type: "client" },
        { id: "router", type: "router" },
        { id: "isp", type: "isp" },
        { id: "server", type: "server" },
      ],
      links: [
        ["client", "router"],
        ["router", "isp"],
        ["isp", "server"],
      ],
      source: "client",
      destination: "server",
      notes: null,
    });
    expect(genericPath).toEqual(ns.route);
  });
});

describe("progressive reveal (M7.7)", () => {
  const mod = makeGenericModule();

  it("KHÔNG có reveal → mọi object visible ngay từ đầu (backward compatible)", () => {
    // AND/binary không có process → 1 frame, visibleIds = tất cả
    const s = mod.init(spec(GENERIC_AND_SPEC));
    expect(s.timeline).toHaveLength(1);
    expect(new Set(s.timeline[0].visibleIds)).toEqual(new Set(["a", "b", "y"]));
    // packet: chỉ move_along_path (không reveal) → mọi object visible mọi frame
    const p = mod.init(spec(GENERIC_PACKET_SPEC));
    for (const f of p.timeline) {
      expect(new Set(f.visibleIds)).toEqual(new Set(spec(GENERIC_PACKET_SPEC).objects.map((o) => o.id)));
    }
  });

  it("reveal tích lũy đúng: visible(k) = visible(k-1) ∪ objects(k)", () => {
    const s = mod.init(spec(GENERIC_REVEAL_SPEC));
    const vis = s.timeline.map((f) => f.visibleIds);
    expect(vis[0]).toEqual(["A", "B"]); // bước 1
    expect(vis[1]).toEqual(["A", "B", "AB"]); // + AB
    expect(vis[2]).toEqual(["A", "B", "C", "AB"]); // + C (thứ tự theo khai báo object)
    expect(vis[3]).toEqual(["A", "B", "C", "AB", "AC"]); // + AC
    expect(vis[4]).toEqual(["A", "B", "C", "AB", "AC", "BC"]); // đủ tam giác
    // Tích lũy: mỗi frame ⊇ frame trước
    for (let i = 1; i < vis.length; i++) {
      for (const id of vis[i - 1]) expect(vis[i]).toContain(id);
    }
    // Frame đầu KHÔNG hiện hết
    expect(vis[0].length).toBeLessThan(spec(GENERIC_REVEAL_SPEC).objects.length);
  });

  it("previous/next/seek giữ đúng visibleIds theo cursor", () => {
    const s0 = mod.init(spec(GENERIC_REVEAL_SPEC));
    const tl = mod.timeline!;
    expect(tl.currentStep(tl.goToStep(s0, 0))).toBe(0);
    const at3 = tl.goToStep(s0, 3);
    const frame3 = at3.timeline[at3.cursor];
    expect(frame3.visibleIds).toContain("AC");
    expect(frame3.visibleIds).not.toContain("BC"); // chưa tới bước cuối
    // seek pure — s0 không đổi
    expect(s0.cursor).toBe(0);
  });

  it("edge KHÔNG render khi endpoint chưa visible (§6)", () => {
    const s = mod.init(spec(GENERIC_REVEAL_SPEC));
    const specObj = spec(GENERIC_REVEAL_SPEC);
    const abEdge = specObj.objects.find((o) => o.id === "AB")!;
    const acEdge = specObj.objects.find((o) => o.id === "AC")!;
    // Frame 0: chỉ A,B visible → AB chưa visible (chưa reveal) → không render
    expect(isObjectRenderable(s.timeline[0], abEdge)).toBe(false);
    // Frame 1: AB revealed + A,B visible → render
    expect(isObjectRenderable(s.timeline[1], abEdge)).toBe(true);
    // Frame 1: AC chưa reveal → không render (dù A visible, C chưa)
    expect(isObjectRenderable(s.timeline[1], acEdge)).toBe(false);
  });

  it("object thường: chỉ render khi visible", () => {
    const s = mod.init(spec(GENERIC_REVEAL_SPEC));
    const cNode = spec(GENERIC_REVEAL_SPEC).objects.find((o) => o.id === "C")!;
    expect(isObjectRenderable(s.timeline[0], cNode)).toBe(false); // C chưa reveal ở bước 1
    expect(isObjectRenderable(s.timeline[2], cNode)).toBe(true); // bước 3 reveal C
    expect(isVisible(s.timeline[2], "C")).toBe(true);
  });

  it("reveal duplicate là idempotent (reveal lại object đã visible không đổi)", () => {
    // Spec gọn: mọi object đều được reveal quản lý (không có object nền)
    const dup = {
      dsl_version: "1.0",
      title: "dup",
      objects: [
        { id: "A", type: "node", x: 20, y: 50 },
        { id: "B", type: "node", x: 80, y: 50 },
        { id: "AB", type: "edge", from: "A", to: "B" },
      ],
      rules: [],
      interactions: [],
      processes: [
        { type: "reveal_sequence", steps: [{ objects: ["A", "B"] }, { objects: ["A", "AB"] }] },
      ],
    };
    const s = mod.init(spec(dup));
    expect(s.timeline[0].visibleIds).toEqual(["A", "B"]);
    expect(s.timeline[1].visibleIds).toEqual(["A", "B", "AB"]); // A lặp lại không nhân đôi
  });

  it("reveal + move_along_path kết hợp tất định (theo thứ tự khai báo)", () => {
    const combo = {
      dsl_version: "1.0",
      title: "combo",
      objects: [
        { id: "n1", type: "node", x: 20, y: 50 },
        { id: "n2", type: "node", x: 80, y: 50 },
        { id: "e", type: "edge", from: "n1", to: "n2" },
        { id: "pkt", type: "moving_entity" },
      ],
      rules: [],
      interactions: [],
      processes: [
        { type: "reveal_sequence", steps: [{ objects: ["n1", "n2"] }, { objects: ["e"] }] },
        { type: "move_along_path", entity: "pkt", path: ["n1", "n2"] },
      ],
    };
    const frames = buildTimeline(spec(combo));
    // 2 frame reveal + 2 frame move = 4
    expect(frames).toHaveLength(4);
    // pkt không nằm trong reveal → là object "nền", visible từ đầu
    expect(frames[0].visibleIds).toEqual(["n1", "n2", "pkt"]);
    expect(frames[1].visibleIds).toContain("e");
    // move frames: entity ở n1 rồi n2
    expect(frames[2].entityPos.pkt).toBe("n1");
    expect(frames[2].visibleIds).toContain("pkt");
    expect(frames[3].entityPos.pkt).toBe("n2");
  });

  it("validator reject reveal step tham chiếu object không tồn tại", () => {
    const bad = {
      ...GENERIC_REVEAL_SPEC,
      processes: [{ type: "reveal_sequence", steps: [{ objects: ["KHONG_CO"] }] }],
    };
    expect(mod.validateConfig(bad).ok).toBe(false);
  });

  it("validator reject reveal step có field lạ", () => {
    const bad = {
      ...GENERIC_REVEAL_SPEC,
      processes: [{ type: "reveal_sequence", steps: [{ objects: ["A"], color: "red" }] }],
    };
    expect(mod.validateConfig(bad).ok).toBe(false);
  });

  it("getExplainContext có visible_objects và serializable", () => {
    const s = mod.init(spec(GENERIC_REVEAL_SPEC));
    const ctx = mod.getExplainContext(s, spec(GENERIC_REVEAL_SPEC));
    expect(JSON.parse(JSON.stringify(ctx))).toEqual(ctx);
    expect(ctx.visible_objects).toEqual(["A", "B"]);
  });
});

describe("visual state helpers (M7.10)", () => {
  const mod = makeGenericModule();
  const tri = () => mod.init(spec(GENERIC_REVEAL_SPEC));
  const tl = mod.timeline!;

  it("currentStepObjectIds = visible(cursor) − visible(cursor−1)", () => {
    const s = tri();
    expect(currentStepObjectIds(s)).toEqual(["A", "B"]); // bước 1: A,B vừa hiện
    expect(currentStepObjectIds(tl.goToStep(s, 1))).toEqual(["AB"]);
    expect(currentStepObjectIds(tl.goToStep(s, 2))).toEqual(["C"]);
    expect(currentStepObjectIds(tl.goToStep(s, 3))).toEqual(["AC"]);
  });

  it("cảnh tĩnh (AND) → không có object vừa hiện", () => {
    expect(currentStepObjectIds(mod.init(spec(GENERIC_AND_SPEC)))).toEqual([]);
  });

  it("objectRole: current / completed / hidden đúng", () => {
    const at1 = tl.goToStep(tri(), 1);
    expect(objectRole(at1, "AB")).toBe("current"); // vừa hiện
    expect(objectRole(at1, "A")).toBe("completed"); // đã hiện trước
    expect(objectRole(at1, "C")).toBe("hidden"); // chưa reveal
    // cảnh tĩnh → mọi object completed (không glow lung tung)
    const and = mod.init(spec(GENERIC_AND_SPEC));
    expect(objectRole(and, "a")).toBe("completed");
  });

  it("previous/next cập nhật currentStepObjectIds đúng", () => {
    const s = tl.goToStep(tri(), 2);
    expect(currentStepObjectIds(s)).toEqual(["C"]);
    const back = tl.goToStep(s, 1);
    expect(currentStepObjectIds(back)).toEqual(["AB"]);
    const fwd = tl.goToStep(s, 3);
    expect(currentStepObjectIds(fwd)).toEqual(["AC"]);
  });

  it("inspectorGroups KHÔNG trống — phân nhóm current/completed/hidden", () => {
    const at1 = tl.goToStep(tri(), 1);
    const g = inspectorGroups(at1);
    expect(g.current.map((o) => o.id)).toEqual(["AB"]);
    expect(g.completed.map((o) => o.id)).toEqual(["A", "B"]);
    expect(g.hidden.map((o) => o.id)).toEqual(["C", "AC", "BC"]);
    // AND (tĩnh): tất cả completed, panel không trống
    const gAnd = inspectorGroups(mod.init(spec(GENERIC_AND_SPEC)));
    expect(gAnd.completed.length).toBe(3);
    expect(gAnd.current).toEqual([]);
    expect(gAnd.hidden).toEqual([]);
  });

  it("invisible object có role hidden (không render)", () => {
    const s0 = tri(); // bước 1: chỉ A,B
    expect(objectRole(s0, "BC")).toBe("hidden");
    expect(isObjectRenderable(s0.timeline[0], spec(GENERIC_REVEAL_SPEC).objects.find((o) => o.id === "BC")!)).toBe(false);
  });
});

describe("structural/textual primitives (M7.12)", () => {
  const mod = makeGenericModule();

  it("web spec (container+heading+paragraph) validate + hierarchy đúng", () => {
    const s = spec(GENERIC_WEB_SPEC);
    expect(structuralRoots(s).map((o) => o.id)).toEqual(["page"]); // container là root
    expect(childrenOf(s, "page").map((o) => o.id)).toEqual(["h", "p"]); // heading + paragraph
  });

  it("heading/paragraph mang nội dung qua text; container không cần", () => {
    const s = spec(GENERIC_WEB_SPEC);
    const h = s.objects.find((o) => o.id === "h")!;
    expect(h.type).toBe("heading");
    expect(h.text).toContain("Xin chào");
    expect(h.parent).toBe("page");
  });

  it("reveal structural: container hiện trước, con tích lũy theo bước", () => {
    const s = mod.init(spec(GENERIC_WEB_SPEC));
    const vis = s.timeline.map((f) => f.visibleIds);
    expect(vis[0]).toEqual(["page"]); // khung trước
    expect(vis[1]).toEqual(["page", "h"]); // + tiêu đề
    expect(vis[2]).toEqual(["page", "h", "p"]); // + đoạn văn
  });

  it("con KHÔNG render khi container cha chưa visible (§6 mở rộng)", () => {
    const s = mod.init(spec(GENERIC_WEB_SPEC));
    const h = spec(GENERIC_WEB_SPEC).objects.find((o) => o.id === "h")!;
    // bước 0: chỉ 'page' visible, 'h' chưa → không render
    expect(isObjectRenderable(s.timeline[0], h)).toBe(false);
    // bước 1: page + h visible → render
    expect(isObjectRenderable(s.timeline[1], h)).toBe(true);
  });

  it("validator reject heading thiếu text", () => {
    const bad = { title: "x", objects: [{ id: "c", type: "container" }, { id: "h", type: "heading", parent: "c" }] };
    expect(mod.validateConfig(bad).ok).toBe(false);
  });

  it("validator reject parent không phải container/group", () => {
    const bad = {
      title: "x",
      objects: [
        { id: "h1", type: "heading", text: "A" },
        { id: "h2", type: "heading", text: "B", parent: "h1" },
      ],
    };
    const r = mod.validateConfig(bad);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toContain("parent");
  });

  it("validator reject chu trình chứa", () => {
    const bad = {
      title: "x",
      objects: [
        { id: "c1", type: "container", parent: "c2" },
        { id: "c2", type: "container", parent: "c1" },
      ],
    };
    const r = mod.validateConfig(bad);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toContain("chu trình");
  });

  it("validator reject text quá dài", () => {
    const bad = { title: "x", objects: [{ id: "p", type: "paragraph", text: "x".repeat(501) }] };
    expect(mod.validateConfig(bad).ok).toBe(false);
  });

  it("getExplainContext của web spec serializable", () => {
    serializable(mod.getExplainContext(mod.init(spec(GENERIC_WEB_SPEC)), spec(GENERIC_WEB_SPEC)));
  });
});

describe("drag interaction — M7.13A", () => {
  const TRIANGLE_DRAG = {
    dsl_version: "1.0",
    title: "Tam giác kéo được",
    objects: [
      { id: "A", type: "node", x: 20, y: 70 },
      { id: "B", type: "node", x: 80, y: 70 },
      { id: "C", type: "node", x: 50, y: 20 },
      { id: "AB", type: "edge", from: "A", to: "B" },
      { id: "AC", type: "edge", from: "A", to: "C" },
      { id: "BC", type: "edge", from: "B", to: "C" },
    ],
    rules: [],
    interactions: [
      { type: "drag", target: "A" },
      { type: "drag", target: "B", constraints: { bounds: { min_x: 10, max_x: 90 }, snap: 5 } },
      { type: "drag", target: "C", constraints: { axis: "x" } },
    ],
    processes: [
      {
        type: "reveal_sequence",
        steps: [{ objects: ["A", "B"] }, { objects: ["AB"] }, { objects: ["C"] }, { objects: ["AC", "BC"] }],
      },
    ],
  };

  it("validate: drag trên node hợp lệ, constraints được chuẩn hóa", () => {
    const s = spec(TRIANGLE_DRAG);
    const drags = s.interactions.filter((i) => i.type === "drag");
    expect(drags).toHaveLength(3);
    expect(drags[0].constraints).toBeUndefined();
    expect(drags[1].constraints).toEqual({ bounds: { min_x: 10, max_x: 90 }, snap: 5 });
    expect(drags[2].constraints).toEqual({ axis: "x" });
    serializable(s);
  });

  it("validate: drag ngoài allowlist (edge/switch) bị reject — v1 chỉ node", () => {
    const onEdge = { ...TRIANGLE_DRAG, interactions: [{ type: "drag", target: "AB" }] };
    const r1 = mod.validateConfig(onEdge);
    expect(r1.ok).toBe(false);
    if (!r1.ok) expect(r1.error).toContain("drag");
    const onSwitch = {
      ...TRIANGLE_DRAG,
      objects: [...TRIANGLE_DRAG.objects, { id: "sw", type: "switch", value: 0 }],
      interactions: [{ type: "drag", target: "sw" }],
    };
    const r2 = mod.validateConfig(onSwitch);
    expect(r2.ok).toBe(false);
    if (!r2.ok) expect(r2.error).toContain("switch");
  });

  it("validate: constraints sai bị reject (axis lạ, snap ≤ 0, bounds ngược, khóa lạ)", () => {
    const cases = [
      { axis: "z" },
      { snap: 0 },
      { bounds: { min_x: 80, max_x: 20 } },
      { bounds: { left: 0 } },
      { gravity: 1 },
    ];
    for (const constraints of cases) {
      const bad = { ...TRIANGLE_DRAG, interactions: [{ type: "drag", target: "A", constraints }] };
      expect(mod.validateConfig(bad).ok, JSON.stringify(constraints)).toBe(false);
    }
  });

  it("validate: ownership — drag vật đang bị process điều khiển bị reject; node waypoint thì OK", () => {
    const graph = {
      dsl_version: "1.0",
      title: "gói tin",
      objects: [
        { id: "c", type: "node", node_type: "client" },
        { id: "s", type: "node", node_type: "server" },
        { id: "pkt", type: "moving_entity" },
      ],
      rules: [],
      interactions: [{ type: "drag", target: "c" }], // waypoint → hợp lệ
      processes: [{ type: "move_along_path", entity: "pkt", path: ["c", "s"] }],
    };
    expect(mod.validateConfig(graph).ok).toBe(true);
    // drag chính entity của process → allowlist chặn trước (moving_entity không phải node)
    const onEntity = { ...graph, interactions: [{ type: "drag", target: "pkt" }] };
    expect(mod.validateConfig(onEntity).ok).toBe(false);
  });

  it("init: pos thuộc state (0–100), spec bất biến; structural không vào pos", () => {
    const s0 = mod.init(spec(TRIANGLE_DRAG));
    expect(s0.pos.A).toEqual({ x: 20, y: 70 });
    expect(s0.pos.C).toEqual({ x: 50, y: 20 });
    serializable(s0.pos);
    const web = mod.init(spec(GENERIC_WEB_SPEC));
    for (const o of web.spec.objects) expect(web.pos[o.id]).toBeUndefined();
  });

  it("apply move: cập nhật pos (pure), spec.x/y KHÔNG đổi — edge derive từ pos nên tự bám", () => {
    let s = mod.init(spec(TRIANGLE_DRAG));
    s = { ...s, cursor: s.timeline.length - 1 }; // dựng xong mới kéo
    const s1 = mod.apply(s, { type: "move", target: "A", x: 30, y: 60 });
    expect(s1.pos.A).toEqual({ x: 30, y: 60 });
    expect(s.pos.A).toEqual({ x: 20, y: 70 }); // state cũ nguyên vẹn (pure)
    const specA = s1.spec.objects.find((o) => o.id === "A");
    expect(specA?.x).toBe(20); // config bất biến — reset về layout gốc
    expect(specA?.y).toBe(70);
  });

  it("apply move: clamp bounds + snap + axis lock", () => {
    let s = mod.init(spec(TRIANGLE_DRAG));
    s = { ...s, cursor: s.timeline.length - 1 };
    // B: bounds [10,90] + snap 5 → 93.2 clamp về 90; 61.2 snap về 60
    const sB = mod.apply(s, { type: "move", target: "B", x: 93.2, y: 61.2 });
    expect(sB.pos.B).toEqual({ x: 90, y: 60 });
    // C: axis x → y giữ nguyên 20
    const sC = mod.apply(s, { type: "move", target: "C", x: 10, y: 99 });
    expect(sC.pos.C).toEqual({ x: 10, y: 20 });
    // mặc định: clamp về canvas 0–100
    const sA = mod.apply(s, { type: "move", target: "A", x: -50, y: 150 });
    expect(sA.pos.A).toEqual({ x: 0, y: 100 });
  });

  it("apply move: từ chối khi chưa visible / không khai drag / action lạ (điều chỉnh #3)", () => {
    const s0 = mod.init(spec(TRIANGLE_DRAG)); // cursor 0: chỉ A, B đã hiện
    // C chưa xuất hiện ở bước 0 → move no-op
    expect(mod.apply(s0, { type: "move", target: "C", x: 60, y: 30 })).toBe(s0);
    // A đã hiện ở bước 0 → move được ngay cả giữa chừng reveal
    expect(mod.apply(s0, { type: "move", target: "A", x: 25, y: 65 }).pos.A).toEqual({ x: 25, y: 65 });
    // edge không khai drag (và không phải node) → no-op
    expect(mod.apply(s0, { type: "move", target: "AB", x: 1, y: 1 })).toBe(s0);
    // spec KHÔNG khai drag cho node → no-op dù là node hợp lệ
    const noDrag = spec({ ...TRIANGLE_DRAG, interactions: [] });
    const sN = mod.init(noDrag);
    expect(mod.apply(sN, { type: "move", target: "A", x: 1, y: 1 })).toBe(sN);
  });

  it("goToStep không phá pos đã kéo; init lại (Reset) mới về layout gốc", () => {
    let s = mod.init(spec(TRIANGLE_DRAG));
    s = mod.timeline!.goToStep(s, s.timeline.length - 1);
    s = mod.apply(s, { type: "move", target: "A", x: 40, y: 50 });
    s = mod.timeline!.goToStep(s, 0);
    expect(s.pos.A).toEqual({ x: 40, y: 50 }); // điều hướng bước không reset pos
    const fresh = mod.init(s.spec);
    expect(fresh.pos.A).toEqual({ x: 20, y: 70 });
  });

  it("getExplainContext kèm draggable_positions (serializable)", () => {
    let s = mod.init(spec(TRIANGLE_DRAG));
    s = { ...s, cursor: s.timeline.length - 1 };
    s = mod.apply(s, { type: "move", target: "A", x: 33, y: 44 });
    const ctx = mod.getExplainContext(s, s.spec);
    serializable(ctx);
    expect((ctx.draggable_positions as Record<string, unknown>).A).toEqual({ x: 33, y: 44 });
  });
});

describe("toggle cần value — M7.13A", () => {
  it("toggle trên node (không value) bị reject, thông báo chỉ sang drag", () => {
    const bad = {
      dsl_version: "1.0",
      title: "toggle chết",
      objects: [{ id: "A", type: "node", x: 10, y: 10 }],
      rules: [],
      interactions: [{ type: "toggle", target: "A" }],
      processes: [],
    };
    const r = mod.validateConfig(bad);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toContain("drag");
  });
});

/**
 * M13 §3.2 + blocker 3 — operand coherence với role-typing, mirror TS của
 * backend `validator.py:369-408` (parity Task 3). validate.ts TIÊU THỤ
 * `dsl-contract.json` (sinh từ manifest — Task 2), KHÔNG hardcode allowlist.
 * Sự cố gốc: "mô phỏng Dijkstra" cho weighted_sum ăn input là id CẠNH — cạnh
 * không mang giá trị số → runtime lặng lẽ ra 0.
 */
describe("M13 operand coherence", () => {
  it("weighted_sum input là edge bị từ chối — tồn tại id là KHÔNG đủ, cạnh không mang giá trị số", () => {
    const res = validateGenericConfig({
      dsl_version: "1.0",
      title: "t",
      objects: [
        { id: "a", type: "node", label: "A" },
        { id: "b", type: "node", label: "B" },
        { id: "e1", type: "edge", label: "AB", from: "a", to: "b" },
        { id: "kq", type: "value_box", label: "Tổng" },
      ],
      rules: [{ type: "weighted_sum", target: "kq", inputs: ["e1"], weights: [1] }],
      interactions: [],
      processes: [],
    });
    expect(res.ok).toBe(false);
    if (!res.ok) expect(res.error).toContain("không có nguồn giá trị");
  });

  it("chuỗi dẫn xuất khai báo đảo (kq trước mid) vẫn hợp lệ — UNRESOLVED_DERIVED_SOURCE, thứ tự khai báo tự do", () => {
    const res = validateGenericConfig({
      dsl_version: "1.0",
      title: "t",
      objects: [
        { id: "x", type: "switch", label: "X", value: 1 },
        { id: "mid", type: "value_box", label: "Trung gian" },
        { id: "kq", type: "value_box", label: "Kết quả" },
      ],
      rules: [
        // kq phụ thuộc mid — mid được rule SAU định nghĩa: phải hợp lệ.
        { type: "weighted_sum", target: "kq", inputs: ["mid"], weights: [2] },
        { type: "weighted_sum", target: "mid", inputs: ["x"], weights: [3] },
      ],
      interactions: [],
      processes: [],
    });
    expect(res.ok).toBe(true);
  });

  it("value_box nuôi boolean rule bị từ chối — value_box chỉ numeric, không logical", () => {
    const res = validateGenericConfig({
      dsl_version: "1.0",
      title: "t",
      objects: [
        { id: "v", type: "value_box", label: "V", value: 5 },
        { id: "den", type: "lamp", label: "Đèn" },
      ],
      rules: [{ type: "boolean", op: "not", target: "den", inputs: ["v"] }],
      interactions: [],
      processes: [],
    });
    expect(res.ok).toBe(false);
    if (!res.ok) expect(res.error).toContain("không có nguồn giá trị");
  });

  it("provider hợp lệ nhưng thiếu value bị từ chối — switch không khai value, không là rule target", () => {
    const res = validateGenericConfig({
      dsl_version: "1.0",
      title: "t",
      objects: [
        { id: "s", type: "switch", label: "S" }, // không value
        { id: "kq", type: "value_box", label: "KQ" },
      ],
      rules: [{ type: "weighted_sum", target: "kq", inputs: ["s"], weights: [1] }],
      interactions: [],
      processes: [],
    });
    expect(res.ok).toBe(false);
    if (!res.ok) expect(res.error).toContain("không có nguồn giá trị");
  });

  it("weighted_sum-target (numeric) nuôi boolean input bị từ chối — role mismatch, coercion DENY mặc định", () => {
    const res = validateGenericConfig({
      dsl_version: "1.0",
      title: "t",
      objects: [
        { id: "v", type: "value_box", label: "V", value: 5 },
        { id: "tong", type: "value_box", label: "Tổng" },
        { id: "den", type: "lamp", label: "Đèn" },
      ],
      rules: [
        { type: "weighted_sum", target: "tong", inputs: ["v"], weights: [1] },
        { type: "boolean", op: "not", target: "den", inputs: ["tong"] },
      ],
      interactions: [],
      processes: [],
    });
    expect(res.ok).toBe(false);
    if (!res.ok) expect(res.error).toContain("vai trò");
  });

  it("chuỗi weighted_sum → weighted_sum (numeric → numeric) hợp lệ", () => {
    const res = validateGenericConfig({
      dsl_version: "1.0",
      title: "t",
      objects: [
        { id: "x", type: "switch", label: "X", value: 1 },
        { id: "mid", type: "value_box", label: "TG" },
        { id: "kq", type: "value_box", label: "KQ" },
      ],
      rules: [
        { type: "weighted_sum", target: "mid", inputs: ["x"], weights: [3] },
        { type: "weighted_sum", target: "kq", inputs: ["mid"], weights: [2] },
      ],
      interactions: [],
      processes: [],
    });
    expect(res.ok).toBe(true);
  });

  it("weighted_sum ghi vào node bị từ chối — node chỉ relational, không nhận numeric (Ràng buộc 2)", () => {
    const res = validateGenericConfig({
      dsl_version: "1.0",
      title: "t",
      objects: [
        { id: "v", type: "value_box", label: "V", value: 3 },
        { id: "n1", type: "node", label: "N1" },
      ],
      rules: [{ type: "weighted_sum", target: "n1", inputs: ["v"], weights: [1] }],
      interactions: [],
      processes: [],
    });
    expect(res.ok).toBe(false);
    if (!res.ok) expect(res.error).toContain("không nhận được");
  });

  it("boolean ghi vào lamp hợp lệ — lamp chấp nhận logical", () => {
    const res = validateGenericConfig({
      dsl_version: "1.0",
      title: "t",
      objects: [
        { id: "s", type: "switch", label: "S", value: 0 },
        { id: "den", type: "lamp", label: "Đèn" },
      ],
      rules: [{ type: "boolean", op: "not", target: "den", inputs: ["s"] }],
      interactions: [],
      processes: [],
    });
    expect(res.ok).toBe(true);
  });
});

/**
 * M13 Step 5 — regression lock nhánh matrix §8 phía frontend (duyệt 2026-07-17).
 * Task 5 mổ validateGenericConfig; các nhánh dưới đây ĐÃ đúng sẵn trong source
 * TRƯỚC khi thêm coherence — test này KHOÁ lại, không phải RED.
 */
describe("M13 regression lock — matrix §8 (frontend)", () => {
  it("toggle nhắm vào target của rule bị từ chối (giá trị dẫn xuất không toggle được)", () => {
    // "den" khai value:0 CÓ CHỦ ĐÍCH — nếu để trống (như ví dụ trong brief),
    // fault-injection cho thấy check "toggle vô nghĩa vì thiếu value" (dòng
    // dưới, lý do khác) cũng reject cùng spec, khiến test không cô lập được
    // nhánh "target là giá trị dẫn xuất" mà tên test khẳng định đang khoá.
    // Khai value:0 loại bỏ nhánh phụ đó — chỉ còn nhánh rule-target reject được.
    const res = validateGenericConfig({
      dsl_version: "1.0",
      title: "t",
      objects: [
        { id: "s", type: "switch", label: "S", value: 1 },
        { id: "den", type: "lamp", label: "Đèn", value: 0 },
      ],
      rules: [{ type: "boolean", op: "not", target: "den", inputs: ["s"] }],
      interactions: [{ type: "toggle", target: "den" }],
      processes: [],
    });
    expect(res.ok).toBe(false);
  });

  it("move_along_path path trỏ id không phải node bị từ chối", () => {
    const res = validateGenericConfig({
      dsl_version: "1.0",
      title: "t",
      objects: [
        { id: "n1", type: "node", label: "A" },
        { id: "v1", type: "value_box", label: "V", value: 1 },
        { id: "e", type: "moving_entity", label: "Gói" },
      ],
      rules: [],
      processes: [{ type: "move_along_path", entity: "e", path: ["n1", "v1"] }],
    });
    expect(res.ok).toBe(false);
  });

  it("edge.from/to trỏ object không tồn tại bị từ chối", () => {
    const res = validateGenericConfig({
      dsl_version: "1.0",
      title: "t",
      objects: [
        { id: "n1", type: "node", label: "A" },
        { id: "e1", type: "edge", label: "AB", from: "n1", to: "khong_ton_tai" },
      ],
      rules: [],
      processes: [],
    });
    expect(res.ok).toBe(false);
  });
});

/**
 * M13 Task 6 — runtime BA TRẠNG THÁI ở valuesOf: mirror 3 test Task 4
 * (backend/tests/test_generic_engine_m13.py) sang vitest, thuật toán PHẢI
 * khớp bản Python đã merge (generic_engine.py: pending/still, `pending = still`
 * TRƯỚC break/progress check). Đây là LƯỚI SAU CÙNG — validator (Task 3/5) đã
 * chặn các spec này ở tầng validate; ở đây gọi thẳng valuesOf trên SimulationSpec
 * dựng tay (bỏ qua validateConfig) để khoá hành vi ENGINE khi lưới validate bị
 * vượt qua (defense in depth, giống test Python bypass validator).
 */
describe("M13: valuesOf ba trạng thái (unresolved / resolved / lỗi typed)", () => {
  it("chuỗi rule khai báo đảo thứ tự vẫn hội tụ đúng giá trị (song song test_chuoi_dao_thu_tu_hoi_tu_dung_gia_tri)", () => {
    const s: SimulationSpec = {
      dsl_version: "1.0",
      title: "t",
      objects: [
        { id: "x", type: "switch", value: 1 },
        { id: "mid", type: "value_box" },
        { id: "kq", type: "value_box" },
      ],
      rules: [
        // kq phụ thuộc mid — mid được rule SAU định nghĩa (thứ tự khai báo đảo).
        { type: "weighted_sum", target: "kq", inputs: ["mid"], weights: [2] },
        { type: "weighted_sum", target: "mid", inputs: ["x"], weights: [3] },
      ],
      interactions: [],
      processes: [],
    };
    const values = valuesOf(s, initialBase(s));
    expect(values.mid).toBe(3);
    expect(values.kq).toBe(6);
  });

  it("operand vắng mặt trong values → GenericExecutionError code unresolved_dependency_after_bound (song song test_toan_hang_khong_ton_tai_trong_values_nem_typed_error)", () => {
    // Validator (Task 3/5) đã chặn "edge làm input numeric" từ trước — đây là
    // LƯỚI SAU CÙNG: dựng thẳng SimulationSpec bỏ qua validateConfig, mô
    // phỏng đúng tình huống gốc M13 (weighted_sum ăn input là id CẠNH, cạnh
    // không mang giá trị số nên không bao giờ có trong `values`).
    const s: SimulationSpec = {
      dsl_version: "1.0",
      title: "t",
      objects: [
        { id: "e1", type: "edge" },
        { id: "kq", type: "value_box" },
      ],
      rules: [{ type: "weighted_sum", target: "kq", inputs: ["e1"], weights: [1] }],
      interactions: [],
      processes: [],
    };
    let caught: unknown;
    try {
      valuesOf(s, initialBase(s));
    } catch (e) {
      caught = e;
    }
    expect(caught).toBeInstanceOf(GenericExecutionError);
    expect((caught as GenericExecutionError).code).toBe("unresolved_dependency_after_bound");
  });

  it("kết quả non-finite → GenericExecutionError code non_finite_numeric_value (song song test_ket_qua_non_finite_nem_typed_error)", () => {
    const s: SimulationSpec = {
      dsl_version: "1.0",
      title: "t",
      objects: [
        { id: "v", type: "value_box", value: 1e308 },
        { id: "kq", type: "value_box" },
      ],
      rules: [{ type: "weighted_sum", target: "kq", inputs: ["v"], weights: [1e308] }],
      interactions: [],
      processes: [],
    };
    let caught: unknown;
    try {
      valuesOf(s, initialBase(s));
    } catch (e) {
      caught = e;
    }
    expect(caught).toBeInstanceOf(GenericExecutionError);
    expect((caught as GenericExecutionError).code).toBe("non_finite_numeric_value");
  });

  it("weight thiếu (số weight ≠ số input) → GenericExecutionError code missing_weight", () => {
    // Defense in depth song song backend `_eval_rule` — validator chuyên biệt
    // (Task 3/5) không kiểm độ dài weights/inputs khớp nhau, engine phải tự vệ.
    const s: SimulationSpec = {
      dsl_version: "1.0",
      title: "t",
      objects: [
        { id: "a", type: "switch", value: 1 },
        { id: "b", type: "switch", value: 1 },
        { id: "kq", type: "value_box" },
      ],
      rules: [{ type: "weighted_sum", target: "kq", inputs: ["a", "b"], weights: [1] }],
      interactions: [],
      processes: [],
    };
    let caught: unknown;
    try {
      valuesOf(s, initialBase(s));
    } catch (e) {
      caught = e;
    }
    expect(caught).toBeInstanceOf(GenericExecutionError);
    expect((caught as GenericExecutionError).code).toBe("missing_weight");
  });

  it("init module ném GenericExecutionError khi spec không evaluate được (fail-fast tại init, không tới render)", () => {
    const badSpec: SimulationSpec = {
      dsl_version: "1.0",
      title: "t",
      objects: [
        { id: "e1", type: "edge" },
        { id: "kq", type: "value_box" },
      ],
      rules: [{ type: "weighted_sum", target: "kq", inputs: ["e1"], weights: [1] }],
      interactions: [],
      processes: [],
    };
    expect(() => mod.init(badSpec)).toThrow(GenericExecutionError);
  });
});
