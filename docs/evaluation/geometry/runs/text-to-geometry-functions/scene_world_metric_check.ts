// text-to-geometry-functions — kiểm BIẾN ĐỔI RENDERER tổng quát: với MỌI cặp điểm của cảnh, độ dài Euclid sau
// `veKhongGian` (frontend thật) phải bằng độ dài theo `chart_metric` trên toạ độ khung. Không biết họ hình, không biết
// đề — nên áp được cho mọi cảnh mà đường mới xuất ra. 0 lượt gọi model. Thoát 1 khi lệch.
//   cd frontend && npx esbuild <run>/scene_world_metric_check.ts --bundle --platform=node --format=esm --outfile=<tmp>.mjs
//   node <tmp>.mjs <thư mục scenes>
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { veKhongGian } from "../../../../../frontend/src/simulations/domains/geometry/scene3d-chart";
import { toVec3 } from "../../../../../frontend/src/simulations/domains/geometry/scene3d-model";

type V = [number, number, number];
const dir = process.argv[2];
let allOk = true;
for (const f of readdirSync(dir).filter((x) => x.endsWith(".json")).sort()) {
  const scene = JSON.parse(readFileSync(join(dir, f), "utf8"));
  const G: number[][] = scene.chart_metric.map((r: string[]) => r.map((x) => { const [p, q] = x.split("/"); return Number(p) / Number(q ?? 1); }));
  const chart = new Map<string, V>(scene.objects.filter((o: { type: string; xyz?: unknown }) => o.type === "point3" && o.xyz)
    .map((o: { id: string; xyz: never }) => [o.id, toVec3(o.xyz) as V]));
  const world = new Map<string, V>(veKhongGian(scene).objects.filter((o: { type: string; xyz?: unknown }) => o.type === "point3" && o.xyz)
    .map((o: { id: string; xyz: never }) => [o.id, toVec3(o.xyz) as V]));
  const ids = [...chart.keys()];
  let worst = 0;
  let pairs = 0;
  for (let i = 0; i < ids.length; i++) for (let j = i + 1; j < ids.length; j++) {
    const a = chart.get(ids[i])!, b = chart.get(ids[j])!;
    const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
    let g = 0;
    for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) g += d[r] * G[r][c] * d[c];
    const wa = world.get(ids[i])!, wb = world.get(ids[j])!;
    const w = (wb[0] - wa[0]) ** 2 + (wb[1] - wa[1]) ** 2 + (wb[2] - wa[2]) ** 2;
    worst = Math.max(worst, Math.abs(w - g) / Math.max(1, g));
    pairs++;
  }
  const ok = pairs > 0 && worst < 1e-9;
  allOk &&= ok;
  console.log(`${f.replace(/\.json$/, "")}: ${ids.length} points, ${pairs} pairs, max rel err ${worst.toExponential(2)} → ${ok ? "OK" : "MISMATCH"}`);
}
console.log(allOk ? "RENDER_METRIC_OK" : "RENDER_METRIC_FAILED");
process.exit(allOk ? 0 : 1);
