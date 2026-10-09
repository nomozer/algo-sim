// G05 real-model pilot — kiểm BIẾN ĐỔI RENDERER: áp chính `veKhongGian` của frontend lên cảnh dựng lại offline
// (`backend/scripts/g05_pilot_scene_replay.py` ghi <lượt>/scenes/<id>.json) và đo hình thế giới renderer vẽ.
// Bundle bằng esbuild sẵn có; không sửa file frontend nào. 0 lượt gọi model.
//   cd frontend && npx esbuild <run>/scene_world_check.ts --bundle --platform=node --format=esm --outfile=<tmp>.mjs
//   node <tmp>.mjs <thư mục scenes> <PILOT_CASES.json>
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { veKhongGian } from "../../../../../frontend/src/simulations/domains/geometry/scene3d-chart";
import { toVec3 } from "../../../../../frontend/src/simulations/domains/geometry/scene3d-model";

type V = [number, number, number];
const sub = (a: V, b: V): V => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a: V, b: V) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: V, b: V): V => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const len = (a: V) => Math.sqrt(dot(a, a));
const mean = (ps: V[]): V => ps.reduce((s, p) => [s[0] + p[0] / ps.length, s[1] + p[1] / ps.length, s[2] + p[2] / ps.length] as V, [0, 0, 0] as V);

function so(s: string): number {                       // "3√3/4", "√3", "2/3", "12"
  const m = /^(\d+(?:\/\d+)?)?(?:√(\d+))?(?:\/(\d+))?$/.exec(s.trim());
  if (!m) throw new Error(`không phải số: ${s}`);
  const [p, q] = (m[1] ?? "1").split("/");
  return (Number(p) / Number(q ?? 1)) * Math.sqrt(Number(m[2] ?? 1)) / Number(m[3] ?? 1);
}

type Case = { id: string; family: string; k: number; base_side: string; dims: Record<string, string> };
const [dir, corpus] = process.argv.slice(2);
const cases: Case[] = JSON.parse(readFileSync(corpus, "utf8")).cases;
const tol = 1e-9;
let allOk = true;
for (const f of readdirSync(dir).filter((x) => x.endsWith(".json"))) {
  const c = cases.find((x) => x.id === f.replace(/\.json$/, ""))!;
  const world = veKhongGian(JSON.parse(readFileSync(join(dir, f), "utf8")));
  const solid = world.objects.find((o: { type?: string }) => o.type === "solid");
  const P: V[] = solid.vertices.map((v: never) => toVec3(v) as V);
  const faces: number[][] = solid.faces;
  const b = so(c.base_side);
  const R = c.k === 6 ? b : b / Math.sqrt(3);
  const h = c.dims.height ? so(c.dims.height)
    : c.family === "prism" ? so(c.dims.lateral) : c.dims.lateral ? Math.sqrt(so(c.dims.lateral) ** 2 - R * R) : NaN;
  const near = (x: number, y: number) => Math.abs(x - y) < tol * Math.max(1, Math.abs(y));
  let ok = false;
  let note = "";
  if (c.family === "tetrahedron") {
    const e: number[] = [];
    for (let i = 0; i < P.length; i++) for (let j = i + 1; j < P.length; j++) e.push(len(sub(P[i], P[j])));
    ok = e.length === 6 && e.every((x) => near(x, b));
    note = `edges=${e.map((x) => x.toFixed(9)).join(",")}`;
  } else if (c.family === "prism") {
    const [A, B] = faces.filter((fc) => fc.length === c.k);
    // cạnh bên = cạnh KỀ trên một mặt tứ giác nối đáy với mặt trên (không phải đường chéo của mặt ấy)
    const ke = (fc: number[], x: number, y: number) => fc.some((v, t) => v === x && (fc[(t + 1) % fc.length] === y || fc[(t + fc.length - 1) % fc.length] === y));
    const lat = A.map((i) => { const j = B.find((q) => faces.some((fc) => fc.length === 4 && ke(fc, i, q)))!; return sub(P[j], P[i]); });
    const n = cross(sub(P[A[1]], P[A[0]]), sub(P[A[2]], P[A[0]]));
    const sides = [A, B].flatMap((F) => F.map((p, i) => len(sub(P[F[(i + 1) % c.k]], P[p]))));
    const O = mean(A.map((i) => P[i]));
    ok = sides.every((s) => near(s, b)) && A.every((i) => near(len(sub(P[i], O)), R))
      && lat.every((v) => near(len(v), h) && near(Math.abs(dot(v, n)) / (len(v) * len(n)), 1));
    note = `side=${sides[0].toFixed(9)} R=${len(sub(P[A[0]], O)).toFixed(9)} h=${len(lat[0]).toFixed(9)}`;
  } else {
    for (let s = 0; s < P.length && !ok; s++) {
      const A = faces.find((fc) => fc.length === c.k && !fc.includes(s));
      if (!A) continue;
      const O = mean(A.map((i) => P[i]));
      const n = cross(sub(P[A[1]], P[A[0]]), sub(P[A[2]], P[A[0]]));
      const so_ = sub(P[s], O);
      ok = A.every((p, i) => near(len(sub(P[A[(i + 1) % c.k]], P[p])), b)) && A.every((i) => near(len(sub(P[i], O)), R))
        && near(Math.abs(dot(so_, n)) / (len(so_) * len(n)), 1) && near(len(so_), h);
      note = `apex=${s} side=${len(sub(P[A[1]], P[A[0]])).toFixed(9)} R=${len(sub(P[A[0]], O)).toFixed(9)} h=${len(so_).toFixed(9)}`;
    }
  }
  allOk &&= ok;
  console.log(`${c.id}: family=${c.family} k=${c.k} expected b=${b.toFixed(9)} h=${Number.isNaN(h) ? "-" : h.toFixed(9)} ${note} → ${ok ? "OK" : "MISMATCH"}`);
}
console.log(allOk ? "RENDER_TRANSFORM_OK" : "RENDER_TRANSFORM_FAILED");
