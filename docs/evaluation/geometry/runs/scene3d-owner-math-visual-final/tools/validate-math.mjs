// Exact (BigInt rational) checks of the backend geometry the renderer draws for the reviewed scenes. Reads source data
// only; independent of the renderer. node .../tools/validate-math.mjs  (run from the worktree root)
import { readFileSync } from "node:fs";
const read = (p) => JSON.parse(readFileSync(p, "utf8"));
// ── exact rationals ──
const gcd = (a, b) => { a = a < 0n ? -a : a; b = b < 0n ? -b : b; while (b) [a, b] = [b, a % b]; return a; };
const Q = (n, d = 1n) => { if (d < 0n) { n = -n; d = -d; } const g = gcd(n, d) || 1n; return [n / g, d / g]; };
const q = (s) => { const [a, b] = String(s).split("/"); return Q(BigInt(a), BigInt(b ?? "1")); };
const add = (x, y) => Q(x[0] * y[1] + y[0] * x[1], x[1] * y[1]);
const sub = (x, y) => Q(x[0] * y[1] - y[0] * x[1], x[1] * y[1]);
const mul = (x, y) => Q(x[0] * y[0], x[1] * y[1]);
const isZero = (x) => x[0] === 0n;
const V = (p) => p.map(q);
const vsub = (a, b) => a.map((x, i) => sub(x, b[i]));
const dot = (a, b) => a.reduce((s, x, i) => add(s, mul(x, b[i])), Q(0n));
const cross = (a, b) => [sub(mul(a[1], b[2]), mul(a[2], b[1])), sub(mul(a[2], b[0]), mul(a[0], b[2])), sub(mul(a[0], b[1]), mul(a[1], b[0]))];
const zeroVec = (a) => a.every(isZero);
// ── scenes ──
const samples = read("frontend/src/data/geometry-samples.json").samples;
const fx = (f) => read(`docs/evaluation/geometry/runs/visual-closure-hybrid-readiness/visual/final-inputs/fixtures/${f}.json`).envelope.scene3d;
const scenes = [...samples.map((s) => [s.id, s.envelope.scene3d]),
  ...["cuboid_positive", "triangular_prism_positive", "cross_section_positive", "w18_projection_line"].map((f) => [f, fx(f)])];
const rows = [];
const check = (scene, name, ok, detail = "") => rows.push({ scene, check: name, ok, detail });
for (const [id, sc] of scenes) {
  const byId = new Map(sc.objects.map((o) => [o.id, o]));
  const pointOf = (oid) => byId.get(oid)?.xyz ? V(byId.get(oid).xyz) : null;
  for (const o of sc.objects) {
    const w = o.perpendicular_witness ?? o.annotation?.witness;
    if (w?.marker && w.foot) {
      const u = V(w.marker.u), v = V(w.marker.v), foot = V(w.foot);
      check(id, `${o.id}: marker u ⊥ v`, isZero(dot(u, v)));
      const from = typeof w.from === "string" ? pointOf(w.from) : null;
      if (from) check(id, `${o.id}: (from − foot) ∥ v`, zeroVec(cross(vsub(from, foot), v)));
      const on = byId.get(w.on);
      if (on?.type === "plane3" && on.point && on.normal) {
        check(id, `${o.id}: foot on plane ${w.on}`, isZero(dot(V(on.normal), vsub(foot, V(on.point)))));
        if (from) check(id, `${o.id}: (from − foot) ∥ normal of ${w.on}`, zeroVec(cross(vsub(from, foot), V(on.normal))));
      } else if (on && (on.type === "line3" || on.type === "segment3")) {
        const pts = (on.depends ?? []).map(pointOf).filter(Boolean);
        if (pts.length >= 2) {
          const d = vsub(pts[1], pts[0]);
          check(id, `${o.id}: foot on line ${w.on}`, zeroVec(cross(vsub(foot, pts[0]), d)));
          if (from) check(id, `${o.id}: (from − foot) ⊥ ${w.on}`, isZero(dot(vsub(from, foot), d)));
        }
      } else if (on && (on.type === "polygon3" || on.type === "section")) {
        const P = (on.polygon ?? []).map(V);
        if (P.length >= 3) {
          const n = cross(vsub(P[1], P[0]), vsub(P[2], P[0]));
          check(id, `${o.id}: foot on face ${w.on}`, isZero(dot(n, vsub(foot, P[0]))));
        }
      }
    }
    if ((o.type === "section" || o.type === "polygon3") && Array.isArray(o.polygon) && o.polygon.length >= 4) {
      const P = o.polygon.map(V), n = cross(vsub(P[1], P[0]), vsub(P[2], P[0]));
      check(id, `${o.id}: polygon vertices coplanar`, P.every((p) => isZero(dot(n, vsub(p, P[0])))));
    }
    // Section boundary on the solid's boundary: each section edge lies in (at least) one face plane of its solid.
    if (o.type === "section" && Array.isArray(o.polygon) && o.polygon.length >= 3) {
      const khoi = sc.objects.find((s) => s.type === "solid" && (o.depends ?? []).some((d) => d === s.id || (s.depends ?? []).includes(d)));
      if (khoi?.vertices && khoi.faces) {
        const KV = khoi.vertices.map(V);
        const mat = khoi.faces.map((f) => ({ p: KV[f[0]], n: cross(vsub(KV[f[1]], KV[f[0]]), vsub(KV[f[2]], KV[f[0]])) }));
        const P = o.polygon.map(V);
        P.forEach((a, i) => {
          const b = P[(i + 1) % P.length];
          const tren = mat.some(({ p, n }) => isZero(dot(n, vsub(a, p))) && isZero(dot(n, vsub(b, p))));
          check(id, `${o.id}: edge ${i} lies in a face plane of ${khoi.id}`, tren);
        });
      }
    }
    if (o.type === "plane3" && o.point && o.normal) {
      for (const dep of o.depends ?? []) {
        const p = pointOf(dep);
        if (p) check(id, `${o.id}: depends point ${dep} on the plane`, isZero(dot(V(o.normal), vsub(p, V(o.point)))));
      }
    }
  }
}
const failed = rows.filter((r) => !r.ok);
console.log(JSON.stringify({ checks: rows.length, failed: failed.length, failures: failed, rows }, null, 1));
process.exitCode = failed.length ? 1 : 0;
