// LOCAL: apply the FRONTEND's own chart → world transform (veKhongGian) to each served prism Scene3D payload and
// measure the world geometry the renderer draws. Bundled with the project's esbuild; no frontend file is changed.
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { veKhongGian } from "D:/Documents/projects/algo-sim/frontend/src/simulations/domains/geometry/scene3d-chart";
import { toVec3 } from "D:/Documents/projects/algo-sim/frontend/src/simulations/domains/geometry/scene3d-model";

type V = [number, number, number];
const sub = (a: V, b: V): V => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a: V, b: V) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: V, b: V): V => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const len = (a: V) => Math.sqrt(dot(a, a));
const r3 = Math.sqrt(3);

const EXPECT: Record<string, { k: number; b: number; h: number }> = {
  X1_side_height: { k: 6, b: 2, h: 3 }, X2_side_lateral: { k: 6, b: 2, h: 3 }, X3_renamed: { k: 6, b: 1, h: 2 },
  X4_radical_side: { k: 6, b: r3, h: 2 }, X5_fractional_side: { k: 6, b: 0.5, h: 4 },
  X6_right_prism_hexagon_base: { k: 6, b: 2, h: 3 }, X7_khoi_phrasing: { k: 6, b: 2, h: 3 },
  T1_side_height: { k: 3, b: 2, h: 3 }, T2_side_lateral: { k: 3, b: 2, h: 3 },
  T3_right_prism_equilateral_base: { k: 3, b: 2, h: 3 }, T4_radical_side: { k: 3, b: 2 * r3, h: 1 },
  T5_fractional_side: { k: 3, b: 2 / 3, h: 9 }, T6_renamed: { k: 3, b: 4, h: 1 },
};
const dir = process.argv[2];
let allOk = true;
for (const f of readdirSync(dir).filter((x) => x.endsWith(".json"))) {
  const row = f.replace(/\.json$/, "");
  const chart = JSON.parse(readFileSync(join(dir, f), "utf8"));
  const world = veKhongGian(chart);
  const solid = world.objects.find((o: { type?: string }) => o.type === "solid");
  const verts: V[] = solid.vertices.map((v: never) => toVec3(v) as V);
  const e = EXPECT[row];
  const B = verts.slice(0, e.k), T = verts.slice(e.k, 2 * e.k);         // vertex_ids = base cycle, then top cycle
  const O = B.reduce((a, p) => [a[0] + p[0] / e.k, a[1] + p[1] / e.k, a[2] + p[2] / e.k] as V, [0, 0, 0] as V);
  const sides = [...B.map((p, i) => len(sub(B[(i + 1) % e.k], p))), ...T.map((p, i) => len(sub(T[(i + 1) % e.k], p)))];
  const radii = B.map((p) => len(sub(p, O)));
  const n = cross(sub(B[1], B[0]), sub(B[2], B[0]));
  const planar = [...B, ...T].every((p, i) => Math.abs(dot(sub(p, i < e.k ? B[0] : T[0]), n)) < 1e-9 * len(n));
  const lat = B.map((p, i) => sub(T[i], p));
  const translation = lat.every((v) => len(sub(v, lat[0])) < 1e-9);
  const perp = lat.map((v) => Math.abs(dot(v, n)) / (len(v) * len(n)));    // |cos| with the base normal → 1
  const tol = 1e-9 * Math.max(1, e.b, e.h);
  const R = e.k === 6 ? e.b : e.b / r3;                                    // circumradius of the regular k-gon
  const ok = sides.every((s) => Math.abs(s - e.b) < tol) && radii.every((r) => Math.abs(r - R) < tol) && planar
    && translation && perp.every((c) => Math.abs(c - 1) < 1e-9) && lat.every((v) => Math.abs(len(v) - e.h) < tol);
  allOk &&= ok;
  console.log(`${row}: chart_metric=${"chart_metric" in chart} sides=${sides[0].toFixed(9)}..${sides.at(-1)!.toFixed(9)} `
    + `circumradius=${radii[0].toFixed(9)} (want ${R.toFixed(9)}) planar=${planar} translation=${translation} `
    + `lateral⊥base=${Math.min(...perp).toFixed(12)} height=${len(lat[0]).toFixed(9)} expected b=${e.b.toFixed(9)} `
    + `h=${e.h.toFixed(9)} → ${ok ? "OK" : "MISMATCH"}`);
}
console.log(allOk ? "RENDER_TRANSFORM_OK" : "RENDER_TRANSFORM_FAILED");
