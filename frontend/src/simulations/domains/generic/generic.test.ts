import { describe, expect, it } from "vitest";
import { makeGenericModule } from "./index";
import {
  buildTimeline,
  childrenOf,
  currentStepObjectIds,
  inspectorGroups,
  isObjectRenderable,
  isVisible,
  objectRole,
  structuralRoots,
  valuesOf,
  type SimulationSpec,
} from "./model";
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
