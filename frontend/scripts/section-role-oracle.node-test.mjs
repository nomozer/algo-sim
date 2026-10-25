// node --test scripts/section-role-oracle.node-test.mjs — synthetic frames, no browser.
import assert from "node:assert/strict";
import { test } from "node:test";
import { assessSectionRole, NGUONG_VAI_THIET_DIEN, project, sectionBoundaryWorld } from "./section-role-oracle.mjs";

const TERRACOTTA = [200, 90, 50], COBALT = [37, 99, 235], MAGENTA = [235, 30, 235], GREY = [150, 150, 150], BG = [245, 244, 240];
const W = 200, H = 160;
const poly = [{ x: 40, y: 40 }, { x: 160, y: 40 }, { x: 160, y: 120 }, { x: 40, y: 120 }];
const edges = poly.map((a, i) => ({ a, b: poly[(i + 1) % 4], hidden: false }));

function frame({ fill = TERRACOTTA, line = COBALT, extraBlue = false, skipEdges = [] } = {}) {
  const rgba = new Uint8Array(W * H * 4);
  const put = (x, y, c) => { if (x < 0 || y < 0 || x >= W || y >= H) return; const q = (y * W + x) * 4; rgba.set([...c, 255], q); };
  for (let y = 0; y < H; y += 1) for (let x = 0; x < W; x += 1) put(x, y, BG);
  for (let y = 41; y < 120; y += 1) for (let x = 41; x < 160; x += 1) put(x, y, fill);
  edges.forEach((e, i) => {
    if (skipEdges.includes(i)) return;
    for (let t = 0; t <= 1; t += 0.002) {
      const x = Math.round(e.a.x + (e.b.x - e.a.x) * t), y = Math.round(e.a.y + (e.b.y - e.a.y) * t);
      for (let d = -1; d <= 1; d += 1) { put(x + d, y, line); put(x, y + d, line); }
    }
  });
  if (extraBlue) for (let y = 130; y < 158; y += 1) for (let x = 5; x < 195; x += 1) put(x, y, COBALT);
  return { w: W, h: H, rgba };
}
const run = (img, extra = {}) => assessSectionRole(img, { scale: 1, box: { w: W, h: H }, overlays: [], edges, ...extra });

test("policy frame passes: cobalt boundary, terracotta fill", () => {
  const r = run(frame());
  assert.equal(r.pass, true, JSON.stringify(r.reasons));
  assert.ok(r.edges.every((e) => e.coverage === 1));
});

test("missing cobalt boundary (terracotta outline) fails", () => {
  assert.deepEqual(run(frame({ line: TERRACOTTA })).reasons.includes("BOUNDARY_NOT_COBALT"), true);
});

test("wrong boundary colour (magenta) fails", () => {
  assert.equal(run(frame({ line: MAGENTA })).pass, false);
});

test("rejects an incorrect cobalt palette even within the locked blue hue band", () => {
  assert.equal(run(frame({ line: [0, 117, 222] })).pass, false);
});

test("rejects an incorrect terracotta palette even within the orange hue band", () => {
  assert.equal(run(frame({ fill: [251, 146, 60] })).pass, false);
});

test("detects a missing quarter of one visible edge", () => {
  const img = frame();
  for (let y = 38; y <= 42; y++) for (let x = 70; x <= 100; x++) img.rgba.set([...BG, 255], (y * W + x) * 4);
  assert.equal(run(img).pass, false);
});

test("does not aggregate away a missing hidden edge", () => {
  const img = frame({ skipEdges: [1] });
  const hiddenEdges = edges.map((e, i) => ({ ...e, hidden: i === 1 || i === 2 }));
  assert.equal(run(img, { edges: hiddenEdges }).pass, false);
});

test("detects a small second section that incorrectly has a cobalt boundary", () => {
  const img = frame();
  const points = [{ x: 8, y: 10 }, { x: 22, y: 10 }, { x: 22, y: 22 }, { x: 8, y: 22 }];
  const other = points.map((a, i) => ({ a, b: points[(i + 1) % 4], hidden: false }));
  for (const e of other) for (let t = 0; t <= 1; t += 0.01) {
    const x = Math.round(e.a.x + t * (e.b.x - e.a.x)), y = Math.round(e.a.y + t * (e.b.y - e.a.y));
    img.rgba.set([...COBALT, 255], (y * W + x) * 4);
  }
  assert.equal(run(img, { otherBoundaries: [other] }).pass, false);
});

test("cone visibility uses the sloped normal, not only the radial direction", () => {
  const scene = { objects: [
    { id: "cone", type: "curved_solid", curved_kind: "cone", anchor: ["0", "0", "0"], apex_or_top: ["0", "0", "2"], radius_sq: "4" },
    { id: "cut", type: "circle3", center: ["0", "0", "1"], normal: ["0", "0", "1"], radius_sq: "1", depends: ["cone"] },
  ] };
  const segments = sectionBoundaryWorld(scene, "cut", [0, 0, 10]);
  assert.ok(segments.every(e => !e.hidden));
});

test("camera model transform is inverted before visibility classification", () => {
  const scene = { objects: [
    { id: "ball", type: "curved_solid", curved_kind: "ball", anchor: ["0", "0", "0"], radius_sq: "1" },
    { id: "cut", type: "circle3", center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "1", depends: ["ball"] },
  ] };
  const model = [-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1];
  const expected = sectionBoundaryWorld(scene, "cut", [-10, 0, -5]);
  const actual = sectionBoundaryWorld(scene, "cut", { position: [10, 0, 5], model_matrix_column_major: model });
  assert.deepEqual(actual, expected);
});

test("one edge without cobalt fails", () => {
  assert.ok(run(frame({ skipEdges: [2] })).reasons.includes("BOUNDARY_NOT_COBALT"));
});

test("fill recoloured cobalt or grey fails", () => {
  assert.ok(run(frame({ fill: COBALT })).reasons.includes("FILL_TURNED_COBALT"));
  assert.ok(run(frame({ fill: GREY })).reasons.includes("FILL_NOT_TERRACOTTA"));
});

test("cobalt drawn on another object (wrong selection) fails", () => {
  assert.ok(run(frame({ extraBlue: true })).reasons.includes("COBALT_NOT_ON_SELECTED_BOUNDARY"));
});

test("an overlay covering a whole edge prevents full certification", () => {
  const r = run(frame({ skipEdges: [2] }), { overlays: [{ x: 30, y: 110, w: 140, h: 20 }] });
  assert.equal(r.edges[2].scored, false);
  assert.equal(r.pass, false);
  assert.ok(r.reasons.includes("BOUNDARY_NOT_FULLY_OBSERVABLE"));
  assert.equal(r.verdict, "UNCERTIFIABLE");
});

test("verdict separates a wrong frame from an unobservable one", () => {
  assert.equal(run(frame()).verdict, "PASS");
  assert.equal(run(frame({ line: TERRACOTTA })).verdict, "FAIL");
  // a fault is still a FAIL even when part of the boundary is under an overlay
  assert.equal(run(frame({ line: MAGENTA }), { overlays: [{ x: 30, y: 110, w: 140, h: 20 }] }).verdict, "FAIL");
});

// An ellipse seen almost edge-on: semi-minor 1.5 px, so its front (lower) and hidden (upper) halves overlap on screen.
function edgeOnCase(ink, N = NGUONG_VAI_THIET_DIEN) {
  const pts = Array.from({ length: 97 }, (_, k) => ({ x: 100 + 60 * Math.cos((2 * Math.PI * k) / 96), y: 80 + 1.5 * Math.sin((2 * Math.PI * k) / 96) }));
  const segs = pts.slice(0, 96).map((a, k) => ({ a, b: pts[k + 1], hidden: Math.sin((2 * Math.PI * (k + 0.5)) / 96) < 0, curve: true }));
  const rgba = new Uint8Array(W * H * 4);
  for (let q = 0; q < W * H; q += 1) rgba.set([...BG, 255], q * 4);
  for (const s of segs) for (let t = 0; t <= 1; t += 0.1) {
    const x = Math.round(s.a.x + (s.b.x - s.a.x) * t), y = Math.round(s.a.y + (s.b.y - s.a.y) * t);
    for (let d = -1; d <= 1; d += 1) rgba.set([...ink, 255], ((y + d) * W + x) * 4);
  }
  return assessSectionRole({ w: W, h: H, rgba }, { scale: 1, box: { w: W, h: H }, edges: segs }, N);
}

test("an edge-on curve is uncertifiable, not passed, when its arcs cannot be separated", () => {
  const r = edgeOnCase(COBALT);
  assert.equal(r.verdict, "UNCERTIFIABLE");
  assert.ok(r.reasons.includes("BOUNDARY_NOT_OBSERVABLE"), JSON.stringify(r.reasons));
  assert.ok(r.hidden_arcs.every((a) => a.pass === null));            // the front ink is never credited to the hidden arc
  // control: without the separation rule the same pixels would "certify" the hidden arc from the front ink
  assert.ok(edgeOnCase(COBALT, { ...NGUONG_VAI_THIET_DIEN, separationCss: 0 }).hidden_arcs.every((a) => a.pass === true));
});

test("an edge-on curve with no cobalt at all still fails", () => {
  assert.equal(edgeOnCase(TERRACOTTA).verdict, "FAIL");
});

test("a hidden edge keeps the dashed-ink threshold without borrowing coverage from another edge", () => {
  const img = frame({ skipEdges: [1] });
  const half = edges.map((e, i) => (i === 1 ? { ...e, hidden: true } : e));
  // Sparse dash on edge 1 (3 on / 11 off): partial coverage passes as hidden (≥0.4), fails as front (≥0.75).
  const put = (x, y) => { const q = (y * W + x) * 4; img.rgba.set([...COBALT, 255], q); };
  for (let y = 40; y <= 120; y += 1) if ((y - 40) % 14 < 3) for (let d = -1; d <= 1; d += 1) put(160 + d, y);
  const asHidden = assessSectionRole(img, { scale: 1, box: { w: W, h: H }, edges: half });
  assert.ok(asHidden.hidden_coverage >= 0.4 && asHidden.hidden_coverage < 0.75, String(asHidden.hidden_coverage));
  assert.equal(asHidden.pass, true, JSON.stringify(asHidden.reasons));
  assert.equal(run(img).edges[1].pass, false);
  assert.ok(run(img).reasons.includes("BOUNDARY_NOT_COBALT"));
});

test("project + sectionBoundaryWorld place a circle on a sphere", () => {
  const scene = { objects: [
    { id: "cau", type: "curved_solid", curved_kind: "ball", anchor: ["0", "0", "0"] },
    { id: "C", type: "circle3", center: ["0", "0", "3"], normal: ["0", "0", "1"], radius_sq: "16", depends: ["P", "cau"] },
  ] };
  const eye = [10, -10, 10];
  const segs = sectionBoundaryWorld(scene, "C", eye);
  assert.equal(segs.length, 96);                       // one oracle segment per renderer rim segment
  assert.ok(segs.every((s) => s.curve));
  assert.ok(segs.some((s) => s.hidden) && segs.some((s) => !s.hidden));
  for (const s of segs) assert.ok(Math.abs(Math.hypot(...s.a) - 5) < 1e-9);   // on the sphere: 3² + 4² = 5²
  const I = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
  assert.deepEqual(project([0, 0, 0], { view_matrix_column_major: I, projection_matrix_column_major: I }, { w: 100, h: 80 }),
    { x: 50, y: 40 });
});

// A curve: 96 short chords on a circle of radius 60 around (100, 80); the left half is hidden (dashed).
function curveCase({ hiddenInk = "dashed" } = {}) {
  const pts = Array.from({ length: 97 }, (_, k) => ({ x: 100 + 60 * Math.cos((2 * Math.PI * k) / 96), y: 80 + 60 * Math.sin((2 * Math.PI * k) / 96) }));
  const segs = pts.slice(0, 96).map((a, k) => ({ a, b: pts[k + 1], hidden: Math.cos((2 * Math.PI * (k + 0.5)) / 96) < 0, curve: true }));
  const rgba = new Uint8Array(W * H * 4);
  const put = (x, y, c) => { if (x >= 0 && y >= 0 && x < W && y < H) rgba.set([...c, 255], (y * W + x) * 4); };
  for (let y = 0; y < H; y += 1) for (let x = 0; x < W; x += 1) put(x, y, BG);
  for (let y = 0; y < H; y += 1) for (let x = 0; x < W; x += 1) if (Math.hypot(x - 100, y - 80) < 58) put(x, y, TERRACOTTA);
  segs.forEach((s) => {
    for (let t = 0; t <= 1; t += 0.05) {
      const x = s.a.x + (s.b.x - s.a.x) * t, y = s.a.y + (s.b.y - s.a.y) * t;
      const arc = Math.atan2(y - 80, x - 100) * 60;                      // arc length, for a dash phase
      const ink = !s.hidden || (hiddenInk === "dashed" && ((arc % 16) + 16) % 16 < 3);
      if (ink) for (let d = -1; d <= 1; d += 1) { put(Math.round(x) + d, Math.round(y), COBALT); put(Math.round(x), Math.round(y) + d, COBALT); }
    }
  });
  return { img: { w: W, h: H, rgba }, segs };
}

test("a dashed hidden arc of a curve passes as one arc even where a short chord falls in a dash gap", () => {
  const { img, segs } = curveCase();
  const r = assessSectionRole(img, { scale: 1, box: { w: W, h: H }, edges: segs });
  assert.ok(r.edges.some((e) => e.hidden && e.coverage < 0.4), "some chords fall in gaps");
  assert.equal(r.hidden_arcs.length, 1);
  assert.equal(r.pass, true, JSON.stringify(r.reasons));
});

test("a hidden arc with 40% of its dashes missing fails (internal review I3: 0.4 let ~55% go missing)", () => {
  const { img, segs } = curveCase();
  const hidden = segs.map((s, i) => (s.hidden ? i : -1)).filter((i) => i >= 0);
  for (const i of hidden.slice(0, Math.round(hidden.length * 0.4))) {           // erase one contiguous 40% of the arc
    const s = segs[i];
    for (let t = 0; t <= 1; t += 0.05) {
      const x = Math.round(s.a.x + (s.b.x - s.a.x) * t), y = Math.round(s.a.y + (s.b.y - s.a.y) * t);
      for (let dy = -2; dy <= 2; dy += 1) for (let dx = -2; dx <= 2; dx += 1) {
        const q = ((y + dy) * W + x + dx) * 4;
        if (img.rgba[q + 2] > 200 && img.rgba[q] < 60) img.rgba.set([...BG, 255], q);
      }
    }
  }
  const r = assessSectionRole(img, { scale: 1, box: { w: W, h: H }, edges: segs });
  assert.equal(r.verdict, "FAIL", JSON.stringify(r.hidden_arcs));
});

test("a curve whose hidden arc is not drawn at all still fails", () => {
  const { img, segs } = curveCase({ hiddenInk: "none" });
  const r = assessSectionRole(img, { scale: 1, box: { w: W, h: H }, edges: segs });
  assert.ok(r.reasons.includes("BOUNDARY_NOT_COBALT"), JSON.stringify(r.reasons));
});
