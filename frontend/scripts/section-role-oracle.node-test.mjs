// node --test scripts/section-role-oracle.node-test.mjs — synthetic frames, no browser.
import assert from "node:assert/strict";
import { test } from "node:test";
import { assessSectionRole, project, sectionBoundaryWorld } from "./section-role-oracle.mjs";

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

test("an overlay covering an edge removes it from scoring instead of failing it", () => {
  const r = run(frame({ skipEdges: [2] }), { overlays: [{ x: 30, y: 110, w: 140, h: 20 }] });
  assert.equal(r.edges[2].scored, false);
  assert.equal(r.pass, true, JSON.stringify(r.reasons));
});

test("hidden edges are scored in aggregate with the lower threshold", () => {
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
  assert.equal(segs.length, 32);
  assert.ok(segs.some((s) => s.hidden) && segs.some((s) => !s.hidden));
  for (const s of segs) assert.ok(Math.abs(Math.hypot(...s.a) - 5) < 1e-9);   // on the sphere: 3² + 4² = 5²
  const I = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
  assert.deepEqual(project([0, 0, 0], { view_matrix_column_major: I, projection_matrix_column_major: I }, { w: 100, h: 80 }),
    { x: 50, y: 40 });
});
