// LOCAL: apply the FRONTEND's own chart → world transform (veKhongGian) to each served hexagonal Scene3D payload and
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

const EXPECT: Record<string, { b: number; h: number }> = {
  H1_side_height: { b: 2, h: 3 }, H2_side_lateral: { b: 2, h: Math.sqrt(12) }, H3_renamed_vertices: { b: 1, h: 2 },
  H4_phrasing_chop_deu: { b: 2, h: 3 }, H5_phrasing_apex_base: { b: 2, h: 3 }, H6_radical_side: { b: Math.sqrt(3), h: 2 },
  H7_lateral_length: { b: 2, h: 3 }, H8_fractional_side: { b: 0.5, h: 6 }, N4_program_apex_off_centre: { b: 2, h: 3 },
};
const dir = process.argv[2];
let allOk = true;
for (const f of readdirSync(dir).filter((x) => x.endsWith(".json"))) {
  const row = f.replace(/\.json$/, "");
  const chart = JSON.parse(readFileSync(join(dir, f), "utf8"));
  const world = veKhongGian(chart);
  const solid = world.objects.find((o: { type?: string }) => o.type === "solid");
  const verts: V[] = solid.vertices.map((v: never) => toVec3(v) as V);
  const faces: number[][] = solid.faces;
  const base = faces.find((fc) => fc.length === 6)!;
  const apexIdx = [0, 1, 2, 3, 4, 5, 6].find((i) => !base.includes(i))!;
  const B = base.map((i) => verts[i]);
  const S = verts[apexIdx];
  const O = B.reduce((a, p) => [a[0] + p[0] / 6, a[1] + p[1] / 6, a[2] + p[2] / 6] as V, [0, 0, 0] as V);
  const sides = B.map((p, i) => len(sub(B[(i + 1) % 6], p)));
  const radii = B.map((p) => len(sub(p, O)));
  const n = cross(sub(B[1], B[0]), sub(B[2], B[0]));
  const planar = B.every((p) => Math.abs(dot(sub(p, B[0]), n)) < 1e-6 * len(n));
  const so = sub(S, O);
  const perp = Math.abs(dot(so, n)) / (len(so) * len(n));           // |cos| between SO and the normal → 1
  const laterals = B.map((p) => len(sub(S, p)));
  const e = EXPECT[row];
  const tol = 1e-6;
  const ok = sides.every((s) => Math.abs(s - e.b) < tol) && radii.every((r) => Math.abs(r - e.b) < tol) && planar
    && Math.abs(perp - 1) < tol && Math.abs(len(so) - e.h) < tol
    && laterals.every((l) => Math.abs(l - Math.sqrt(e.b * e.b + e.h * e.h)) < tol);
  allOk &&= ok;
  console.log(`${row}: chart_metric=${"chart_metric" in chart} sides=${sides.map((s) => s.toFixed(6)).join(",")} `
    + `circumradius=${radii[0].toFixed(6)} planar=${planar} apex⊥base=${perp.toFixed(9)} height=${len(so).toFixed(6)} `
    + `lateral=${laterals[0].toFixed(6)} expected b=${e.b.toFixed(6)} h=${e.h.toFixed(6)} → ${ok ? "OK" : "MISMATCH"}`);
}
console.log(allOk ? "RENDER_TRANSFORM_OK" : "RENDER_TRANSFORM_FAILED");
