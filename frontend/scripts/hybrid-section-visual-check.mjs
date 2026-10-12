/**
 * hybrid-section-visual-check.mjs — Playwright check of Hybrid section / intersection-line scenes in the Scene3D HARNESS
 * (`scripts/hybrid-section-visual.html`), run `hybrid-slice-review`. Not the product page: no store, no API, no model.
 *
 * Scenes come from the REAL Hybrid route (`backend/scripts/export_hybrid_section_scenes.py`). Per case it measures, on
 * pixels decoded with `png-pixels.mjs` and on the product step model (`objectsAt`) exposed by the harness:
 *   - no console error / page error, WebGL canvas present;
 *   - section (amber, hue 38) / construction line (teal, hue 174) pixels present at the last step;
 *   - construction order: the step where the section / line appears comes after its dependencies, and its pixels are
 *     absent one step earlier;
 *   - orbit (drag) changes the frame and settles; zoom (wheel) changes the ink extent; "Đặt lại khung nhìn" returns
 *     close to the first frame.
 * Needs a Vite dev server of this checkout (default :3000; `--port` when 3000 belongs to another checkout).
 * Run: node scripts/hybrid-section-visual-check.mjs --out <dir> [--port 3100] (refuses to overwrite).
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { chromium } from "playwright";
import { docPNG } from "./png-pixels.mjs";

const out = process.argv[process.argv.indexOf("--out") + 1];
if (!process.argv.includes("--out") || !out) throw new Error("--out <new dir> is required");
if (existsSync(out)) { console.error(`refusing to overwrite ${out}`); process.exit(2); }
const port = process.argv.includes("--port") ? process.argv[process.argv.indexOf("--port") + 1] : "3000";
const URL0 = `http://localhost:${port}/scripts/hybrid-section-visual.html`;
const rows = JSON.parse(readFileSync(new URL("../../docs/evaluation/geometry/runs/hybrid-slice-review/visual/scenes.json", import.meta.url), "utf-8"));

// Hues mirrored from `scene3d-view.tsx` MAU / `scene3d-roles.ts`: polygon/section amber, construction line teal, and the
// "just built at this step" blue (MAU_VAI_TRO.moi_dung 0x2563eb) that replaces an object's own colour at its own step.
const HUE = { section: 38, line: 174, highlight: 221 };
function hue(r, g, b) {
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  if (d === 0) return { h: 0, s: 0 };
  const h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return { h: (h * 60 + 360) % 360, s: mx === 0 ? 0 : d / mx };
}
function measure(png) {
  const { w, h, rgba } = docPNG(png);
  const n = { section: 0, line: 0, highlight: 0 };
  // Ink = pixels far from the frame's dominant (background) colour — not a fixed brightness threshold.
  const counts = new Map();
  for (let i = 0; i < rgba.length; i += 16) { const k = `${rgba[i] >> 3},${rgba[i + 1] >> 3},${rgba[i + 2] >> 3}`; counts.set(k, (counts.get(k) ?? 0) + 1); }
  const [bg] = [...counts.entries()].sort((a, b) => b[1] - a[1])[0][0].split(",").map((v) => Number(v) << 3);
  let x0 = w, y0 = h, x1 = -1, y1 = -1;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = (y * w + x) * 4, r = rgba[i], g = rgba[i + 1], b = rgba[i + 2];
    if (Math.abs(r - bg) + Math.abs(g - bg) + Math.abs(b - bg) > 60) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
    const { h: hh, s } = hue(r, g, b);
    if (s < 0.25) continue;
    for (const k of Object.keys(HUE)) if (Math.min(Math.abs(hh - HUE[k]), 360 - Math.abs(hh - HUE[k])) < 14) n[k]++;
  }
  return { ...n, ink: x1 < 0 ? null : [x0, y0, x1, y1] };
}
function diff(a, b) {
  const A = docPNG(a), B = docPNG(b);
  if (A.w !== B.w || A.h !== B.h) return 1;
  let d = 0;
  for (let i = 0; i < A.rgba.length; i += 4) if (Math.abs(A.rgba[i] - B.rgba[i]) + Math.abs(A.rgba[i + 1] - B.rgba[i + 1]) + Math.abs(A.rgba[i + 2] - B.rgba[i + 2]) > 30) d++;
  return d / (A.w * A.h);
}

const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
const errors = [];
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
page.on("pageerror", (e) => errors.push(String(e)));
const shot = async () => page.getByTestId("khung").screenshot();
const settle = async () => { let a = await shot(); for (let i = 0; i < 40; i++) { await page.waitForTimeout(250); const b = await shot(); if (diff(a, b) === 0) return { settled: true, b }; a = b; } return { settled: false, b: a }; };
const waitCanvas = async (url) => {
  try { await page.waitForSelector("canvas", { state: "attached", timeout: 90000 }); }
  catch (e) { console.error(JSON.stringify({ url, errors, body: (await page.content()).slice(0, 2000) })); throw e; }
};
const open = async (i, step) => { const u = `${URL0}?i=${i}${step === undefined ? "" : `&step=${step}`}`; await page.goto(u); await waitCanvas(u); return (await settle()).b; };

mkdirSync(out, { recursive: true });
const report = [];
for (const [i, row] of rows.entries()) {
  const e0 = errors.length;
  const last = await open(i);
  const m = measure(last);
  const h = await page.evaluate(() => window.__hybrid);
  writeFileSync(join(out, `${row.id}.png`), last);
  const target = h.objects.find((o) => o.type === "section") ?? h.objects.find((o) => o.id.startsWith("gt_"));
  let order = null;
  if (target) {
    const steps = await page.evaluate((n) => Array.from({ length: n }, (_, k) => window.__hybrid.presentAt(k)), h.stepCount);
    const first = steps.findIndex((ids) => ids.includes(target.id));
    const depsBefore = target.depends.every((d) => steps[first].includes(d));
    const kind = target.type === "section" ? "section" : "line";
    // Absent one step earlier; at its own step it is drawn either in its colour or in the "just built" blue.
    const mb = first > 0 ? measure(await open(i, first - 1)) : null;
    const ma = measure(await open(i, first));
    // Own pixel contribution: frames with vs without the target (harness `hide=`), at the last step. 0 ⇒ not visible.
    const uh = `${URL0}?i=${i}&hide=${target.id}`; await page.goto(uh); await waitCanvas(uh);
    const sansTarget = (await settle()).b;
    const own = Math.round(diff(last, sansTarget) * docPNG(last).w * docPNG(last).h);
    order = { target: target.id, own_pixel_contribution: own, first_step: first, steps: h.stepCount, depends_present: depsBefore,
              pixels_before: mb && { [kind]: mb[kind], highlight: mb.highlight }, pixels_at: { [kind]: ma[kind], highlight: ma.highlight } };
  }
  // interaction on the final step: orbit, settle, zoom, reset
  const start = await open(i);
  const box = await page.getByTestId("khung").boundingBox();
  const cx = box.x + box.width / 2, cy = box.y + box.height / 2;
  await page.mouse.move(cx, cy); await page.mouse.down(); await page.mouse.move(cx + box.height * 0.4, cy + 30, { steps: 12 }); await page.mouse.up();
  const orbit = await settle();
  await page.mouse.move(cx, cy); await page.mouse.wheel(0, -600);
  const zoom = await settle();
  await page.getByRole("button", { name: "Đặt lại khung nhìn" }).click();
  const reset = await settle();
  const ink = (p) => { const k = measure(p).ink; return k ? (k[2] - k[0]) * (k[3] - k[1]) : 0; };
  report.push({
    id: row.id, served: row.served, section_vertices_model: row.section_vertices, pixels_last_step: m,
    order, console_errors: errors.slice(e0),
    orbit: { changed: diff(start, orbit.b), settled: orbit.settled },
    zoom: { changed: diff(orbit.b, zoom.b), ink_ratio: ink(zoom.b) / Math.max(1, ink(orbit.b)), settled: zoom.settled },
    rendered_ids: await page.evaluate(() => window.__geo3d_rendered_object_ids),
    reset: { residual_vs_start: diff(start, reset.b), settled: reset.settled },
  });
  console.log(JSON.stringify(report.at(-1)));
}
await browser.close();
writeFileSync(join(out, "browser-check.json"), JSON.stringify({ harness: "scripts/hybrid-section-visual.html (Scene3D harness, not product UI)",
  scenes: "real Hybrid route output, backend/scripts/export_hybrid_section_scenes.py", browser: "Playwright chromium, SwiftShader WebGL",
  report }, null, 1));
