/**
 * hybrid-section-visual-check.mjs — Playwright check of Hybrid section / intersection-line scenes in the Scene3D HARNESS
 * (`scripts/hybrid-section-visual.html`), runs `hybrid-slice-review`, `hybrid-semantic-hardening`. Not the product page:
 * no store, no API, no model. The harness applies the product's frame step (`veKhongGian`) before `Scene3DWorkspace`.
 *
 * Scenes come from the REAL Hybrid route (`backend/scripts/export_hybrid_section_scenes.py`). Per case it measures, on
 * pixels decoded with `png-pixels.mjs` and on the product step model (`objectsAt`) exposed by the harness:
 *   - no console error / page error, WebGL canvas present;
 *   - section (amber, hue 38) / construction line (teal, hue 174) pixels present at the last step;
 *   - the target's OWN pixel contribution (frame with vs without it, harness `hide=`), at the default view and after the
 *     same orbit gesture — 0 means the object draws nothing;
 *   - construction order: the step where the target appears comes after its dependencies;
 *   - orbit (drag) changes the frame and settles; zoom (wheel) changes the ink extent; "Đặt lại khung nhìn" returns to
 *     the first frame;
 *   - for intersection lines: line variants through the harness `set=` (axis and oblique directions, through a vertex and
 *     an interior point) and the auxiliary layer toggled — each must draw.
 * Exit 1 when any target or variant draws 0 own pixels, a console error appears, or a camera move does not settle.
 * Needs a Vite dev server of this checkout (default :3000; `--port`). `--gpu` uses ANGLE D3D11 (hardware) instead of
 * SwiftShader. Run: node scripts/hybrid-section-visual-check.mjs --out <dir> [--port 3100] [--gpu] (refuses to overwrite).
 * `--scenes goal` reads the export of run `goal-directed-section-planning` (harness `src=goal`); `--only <id prefix>`
 * measures a subset (e.g. `--only derived-plane`).
 * `--scenes two-line` reads `two-line-plane-section` (harness `src=two-line`) and also checks refusal, the real
 * step slider and selection, the named plane and auxiliary roles. This is LOCAL harness acceptance, not API/product E2E.
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { createHash } from "node:crypto";
import { chromium } from "playwright";
import { docPNG } from "./png-pixels.mjs";

const arg = (k, d) => (process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : d);
const out = arg("--out");
if (!out) throw new Error("--out <new dir> is required");
if (existsSync(out)) { console.error(`refusing to overwrite ${out}`); process.exit(2); }
// `--host 127.0.0.1` with `vite --host 127.0.0.1`: a Vite bound to [::1] only refused the IPv4 `localhost` connections the
// browser sometimes made — the intermittent "canvas never attached" of `hybrid-slice-review`.
const URL0 = `http://${arg("--host", "localhost")}:${arg("--port", "3000")}/scripts/hybrid-section-visual.html`;
const gpu = process.argv.includes("--gpu");
// `--scenes goal`: scenes of run goal-directed-section-planning (harness `src=goal`); default: the hardening export.
const source = arg("--scenes", "hardening");
if (!["hardening", "goal", "two-line"].includes(source)) throw new Error("unknown --scenes");
const SCENES_RUN = source === "two-line" ? "two-line-plane-section" : source === "goal" ? "goal-directed-section-planning" : "hybrid-semantic-hardening";
const scenesBytes = readFileSync(new URL(`../../docs/evaluation/geometry/runs/${SCENES_RUN}/visual/scenes.json`, import.meta.url));
const rows = JSON.parse(scenesBytes.toString("utf-8"));

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
/** Fraction of pixels that differ (sum of channel deltas > 30). */
function diff(a, b) {
  const A = docPNG(a), B = docPNG(b);
  if (A.w !== B.w || A.h !== B.h) return 1;
  let d = 0;
  for (let i = 0; i < A.rgba.length; i += 4) if (Math.abs(A.rgba[i] - B.rgba[i]) + Math.abs(A.rgba[i + 1] - B.rgba[i + 1]) + Math.abs(A.rgba[i + 2] - B.rgba[i + 2]) > 30) d++;
  return d / (A.w * A.h);
}
const pixels = (a, b) => Math.round(diff(a, b) * docPNG(a).w * docPNG(a).h);

// Launch explicitly so the receipt can name the owned browser PID. Playwright closes its whole process tree.
const server = await chromium.launchServer({ args: gpu ? ["--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist"]
  : ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const browserPid = server.process().pid;
const browser = await chromium.connect(server.wsEndpoint());
mkdirSync(out, { recursive: true });
let completed = false;
try {
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
const errors = [];
// Vite dev-client HMR socket messages are dev-server infrastructure, not the page under test: counted, not failed on.
const devServerNoise = [];
const VITE_HMR = /^\[vite\]|WebSocket connection to 'ws:\/\//;
page.on("console", (m) => { if (m.type() === "error") (VITE_HMR.test(m.text()) ? devServerNoise : errors).push(m.text()); });
page.on("pageerror", (e) => errors.push(String(e)));
const shot = async () => page.getByTestId("khung").screenshot();
const settle = async () => { let a = await shot(); for (let i = 0; i < 40; i++) { await page.waitForTimeout(250); const b = await shot(); if (diff(a, b) === 0) return { settled: true, b }; a = b; } return { settled: false, b: a }; };
// Transient local-network failures (`net::ERR_NETWORK_ACCESS_DENIED`, a refused dev-server socket) were seen on this
// Windows machine between page loads; a load is retried at most 6 times (growing pause) and every retry is reported, never hidden.
const netRetries = [];
const goto = async (qs, refused = false) => {
  const u = `${URL0}?${qs}${source !== "hardening" ? `&src=${source}` : ""}`;
  for (let k = 0; ; k++) {
    const e0 = errors.length;
    try {
      await page.goto(u);
      await page.waitForSelector(refused ? '[data-testid="refusal"]' : "canvas", { state: "attached", timeout: 30000 });
      // A denied sub-resource (e.g. the stylesheet) still lets the canvas appear but changes the layout — a failed load.
      if (errors.slice(e0).some((x) => /ERR_NETWORK_ACCESS_DENIED|ERR_CONNECTION_REFUSED/.test(x))) throw new Error("denied sub-resource");
      break;
    } catch (e) {
      const net = /ERR_NETWORK_ACCESS_DENIED|ERR_CONNECTION_REFUSED/.test(String(e) + errors.slice(e0).join(" "));
      if (!net || k >= 6) { console.error(JSON.stringify({ url: u, errors, body: (await page.content()).slice(0, 2000) })); throw e; }
      netRetries.push({ url: u, error: String(e).split("\n")[0] });
      errors.splice(e0);
      await page.waitForTimeout(2000 * (k + 1));
    }
  }
  if (refused) return null;
  const frame = await settle();
  if (!frame.settled) throw new Error(`initial frame did not settle: ${u}`);
  return frame.b;
};
const orbitGesture = async () => {
  const box = await page.getByTestId("khung").boundingBox();
  const cx = box.x + box.width / 2, cy = box.y + box.height / 2;
  await page.mouse.move(cx, cy); await page.mouse.down(); await page.mouse.move(cx + box.height * 0.4, cy + 30, { steps: 12 }); await page.mouse.up();
  return { cx, cy, ...(await settle()) };
};
/** Own pixels of `id` under the query `qs`: default view and after the same orbit gesture. */
const own = async (qs, id) => {
  const withT = await goto(qs), withO = (await orbitGesture()).b;
  const sans = await goto(`${qs}&hide=${id}`), sansO = (await orbitGesture()).b;
  return { default_view: pixels(withT, sans), after_orbit: pixels(withO, sansO) };
};

// Warm-up: the first load of a cold Vite server can exceed the canvas wait (seen in `hybrid-slice-review`); not measured.
await goto("i=0");
const renderer = await page.evaluate(() => {
  const gl = document.createElement("canvas").getContext("webgl2");
  const e = gl && gl.getExtension("WEBGL_debug_renderer_info");
  return e ? gl.getParameter(e.UNMASKED_RENDERER_WEBGL) : "unknown";
});

// Directions / points in PAYLOAD coordinates (before the frame step), all through scene points or the interior.
const VARIANTS = [
  ["dir-x", ["direction", ["1", "0", "0"]]], ["dir-y", ["direction", ["0", "1", "0"]]], ["dir-z", ["direction", ["0", "0", "1"]]],
  ["dir-xy", ["direction", ["1", "1", "0"]]], ["dir-xz", ["direction", ["1", "0", "1"]]],
  ["through-A-dir-x", ["point", ["0", "0", "0"]], ["direction", ["1", "0", "0"]]],
  ["interior-dir-x", ["point", ["1/2", "1/2", "1/2"]], ["direction", ["1", "0", "0"]]],
];
const setQs = (id, sets) => sets.map(([f, v]) => `&set=${id}.${f}=${encodeURIComponent(JSON.stringify(v))}`).join("");

const report = [];
const failures = [];
// `--only <id prefix>`: measure those cases only; the harness index `i` stays the case's position in scenes.json.
const only = arg("--only");
for (const [i, row] of rows.entries()) {
  if (only && !row.id.startsWith(only)) continue;
  const e0 = errors.length;
  if (!row.served) {
    await goto(`i=${i}`, true);
    const refusal = { id: row.id, served: false, code: row.code, canvas_count: await page.locator("canvas").count(),
      scene_objects: await page.evaluate(() => window.__hybrid.objects.length), text: await page.getByTestId("refusal").innerText(),
      console_errors: errors.slice(e0) };
    await page.screenshot({ path: join(out, `${row.id}.png`) });
    if (row.scene || refusal.canvas_count || refusal.scene_objects || !refusal.text.includes(row.code) || refusal.console_errors.length)
      failures.push(`${row.id}: refusal has a scene/canvas, missing reason or console error`);
    report.push(refusal);
    continue;
  }
  const last = await goto(`i=${i}`);
  const m = measure(last);
  const h = await page.evaluate(() => window.__hybrid);
  writeFileSync(join(out, `${row.id}.png`), last);
  const target = h.objects.find((o) => o.type === "section") ?? h.objects.find((o) => o.id.startsWith("gt_"));
  if (source === "two-line" && !target) failures.push(`${row.id}: served scene missing section target`);
  let order = null, variants = null;
  if (target) {
    const steps = await page.evaluate((n) => Array.from({ length: n }, (_, k) => window.__hybrid.presentAt(k)), h.stepCount);
    const first = steps.findIndex((ids) => ids.includes(target.id));
    const kind = target.type === "section" ? "section" : "line";
    // Absent one step earlier; at its own step it is drawn either in its colour or in the "just built" blue.
    const mb = first > 0 ? measure(await goto(`i=${i}&step=${first - 1}`)) : null;
    const ma = measure(await goto(`i=${i}&step=${first}`));
    order = { target: target.id, own_pixels: await own(`i=${i}`, target.id), first_step: first, steps: h.stepCount,
              depends_present: first >= 0 && target.depends.every((d) => steps[first].includes(d)),
              depends_before: first > 0 && target.depends.every((d) => steps[first - 1].includes(d)),
              pixels_before: mb && { [kind]: mb[kind], highlight: mb.highlight }, pixels_at: { [kind]: ma[kind], highlight: ma.highlight } };
    if (order.own_pixels.default_view === 0 || order.own_pixels.after_orbit === 0) failures.push(`${row.id}: ${target.id} draws 0 own pixels`);
    if (!order.depends_present) failures.push(`${row.id}: ${target.id} appears before its dependencies`);
    if (source === "two-line" && !order.depends_before) failures.push(`${row.id}: section dependencies not built earlier`);
    if (kind === "line") {
      variants = {};
      for (const [tag, ...sets] of [...VARIANTS, ["aux-shown"]]) {
        const qs = `i=${i}${setQs(target.id, sets)}${tag === "aux-shown" ? "&aux=1" : ""}`;
        variants[tag] = await own(qs, target.id);
        if (variants[tag].default_view === 0 || variants[tag].after_orbit === 0) failures.push(`${row.id}/${tag}: 0 own pixels`);
      }
    }
  }
  // interaction on the final step: orbit, settle, zoom, reset
  const start = await goto(`i=${i}`);
  const orbit = await orbitGesture();
  await page.mouse.move(orbit.cx, orbit.cy); await page.mouse.wheel(0, -600);
  const zoom = await settle();
  await page.getByRole("button", { name: "Đặt lại khung nhìn" }).click();
  const reset = await settle();
  let scrubber = null, selection = null, naming = null;
  if (source === "two-line" && target) {
    const slider = page.getByRole("slider", { name: "Bước dựng" });
    await slider.focus(); await page.keyboard.press("Home"); await settle();
    const first = await page.evaluate(() => ({ step: window.__hybrid.step, ids: window.__geo3d_rendered_object_ids }));
    await page.keyboard.press("End"); await settle();
    const last = await page.evaluate(() => ({ step: window.__hybrid.step, ids: window.__geo3d_rendered_object_ids }));
    const rendersTarget = ids => ids.some(id => id === target.id || id.startsWith(`${target.id}#`));
    scrubber = { first, last, passed: first.step === 0 && !rendersTarget(first.ids) && last.step === h.stepCount - 1 && rendersTarget(last.ids) };
    const before = await shot();
    await page.getByRole("combobox", { name: "Chọn đối tượng" }).selectOption(target.id);
    const selected = await settle();
    selection = { selected_id: await page.evaluate(() => window.__geo3d_selected_id), changed: diff(before, selected.b),
      highlighted_ids: await page.evaluate(() => window.__geo3d_highlighted_render_owner_ids) };
    await page.getByRole("combobox", { name: "Chọn đối tượng" }).selectOption(""); await settle();
    selection.cleared_id = await page.evaluate(() => window.__geo3d_selected_id);
    if (!scrubber.passed) failures.push(`${row.id}: step scrubber failed`);
    if (selection.selected_id !== target.id || selection.changed === 0 || selection.cleared_id !== null || !selected.settled)
      failures.push(`${row.id}: section selection failed`);
    const plane = h.objects.find(o => o.type === "plane3");
    const aux = h.objects.filter(o => o.type === "point3" && o.source?.instruction === "construct_point.translate");
    const options = await page.getByRole("combobox", { name: "Chọn đối tượng" }).locator("option").evaluateAll(nodes =>
      nodes.map(o => ({ id: o.value, text: o.textContent })));
    naming = { plane: plane?.label, section: target.label,
      plane_option: options.find(o => o.id === plane?.id)?.text,
      auxiliaries: aux.map(o => ({ id: o.id, role: o.role, binding: o.source?.binding,
        option: options.find(p => p.id === o.id)?.text,
        distinct_section_identity: !(target.endpoint_entities ?? []).some(e => e.entity_id === o.id) })) };
    if (naming.plane !== "(P)" || naming.plane_option !== "(P)" || !naming.section?.includes("(P)") ||
      aux.length !== 2 || naming.auxiliaries.some(o => o.role !== "Điểm dựng phụ" || o.binding !== "AUXILIARY" ||
        !o.option?.includes("Điểm dựng phụ") || !o.distinct_section_identity)) failures.push(`${row.id}: plane/auxiliary naming failed`);
    if (aux.length) {
      await page.getByRole("combobox", { name: "Chọn đối tượng" }).selectOption(aux[0].id); await settle();
      naming.selected_auxiliary = { id: await page.evaluate(() => window.__geo3d_selected_id),
        details: await page.getByTestId("selection-details").innerText() };
      await page.screenshot({ path: join(out, `${row.id}-selected-auxiliary.png`) });
      if (naming.selected_auxiliary.id !== aux[0].id || !naming.selected_auxiliary.details.includes("Điểm dựng phụ"))
        failures.push(`${row.id}: auxiliary selection classification failed`);
      await page.getByRole("combobox", { name: "Chọn đối tượng" }).selectOption(""); await settle();
    }
  }
  const ink = (p) => { const k = measure(p).ink; return k ? (k[2] - k[0]) * (k[3] - k[1]) : 0; };
  const r = {
    id: row.id, served: row.served, section_vertices_model: row.section_vertices, pixels_last_step: m,
    order, variants, scrubber, selection, naming, console_errors: errors.slice(e0),
    orbit: { changed: diff(start, orbit.b), settled: orbit.settled },
    zoom: { changed: diff(orbit.b, zoom.b), ink_ratio: ink(zoom.b) / Math.max(1, ink(orbit.b)), settled: zoom.settled },
    rendered_ids: await page.evaluate(() => window.__geo3d_rendered_object_ids),
    reset: { residual_vs_start: diff(start, reset.b), settled: reset.settled },
  };
  if (r.console_errors.length) failures.push(`${row.id}: console errors`);
  if (!r.orbit.settled || !r.zoom.settled || !r.reset.settled || r.orbit.changed === 0) failures.push(`${row.id}: camera move did not change or settle`);
  if (r.zoom.changed === 0 || !Number.isFinite(r.zoom.ink_ratio) || Math.abs(r.zoom.ink_ratio - 1) < 0.01) failures.push(`${row.id}: zoom did not change ink extent`);
  if (r.reset.residual_vs_start > 0.005) failures.push(`${row.id}: reset did not restore initial view`);
  report.push(r);
  console.log(JSON.stringify(r));
}
await browser.close();
await server.close();
if (errors.length && !failures.some(f => f.includes("console errors"))) failures.push("browser console errors");
if (gpu && !/Intel.*Direct3D11|Intel.*D3D11/i.test(renderer)) failures.push("Intel D3D11 renderer unavailable");
writeFileSync(join(out, "browser-check.json"), JSON.stringify({ harness: "scripts/hybrid-section-visual.html (Scene3D harness, not product UI)",
  scenes: "real Hybrid route output, backend/scripts/export_hybrid_section_scenes.py; product frame step veKhongGian applied",
  browser: `Playwright chromium, ${gpu ? "ANGLE D3D11 requested" : "SwiftShader WebGL requested"}`, renderer,
  browser_version: browser.version(), browser_pid: browserPid, browser_stopped: server.process().exitCode !== null,
  scenes_sha256: createHash("sha256").update(scenesBytes).digest("hex"),
  failures, console_errors: errors, net_retries: netRetries, dev_server_noise: devServerNoise.length, report }, null, 1));
console.log(JSON.stringify({ renderer, failures, net_retries: netRetries.length }));
completed = true;
process.exitCode = failures.length ? 1 : 0;
} catch (error) {
  writeFileSync(join(out, "browser-failure.json"), JSON.stringify({ error: String(error).split("\n")[0], browser_pid: browserPid }, null, 2));
  process.exitCode = 1;
  console.error(String(error).split("\n")[0]);
} finally {
  await browser.close().catch(() => undefined);
  await server.close().catch(() => undefined);
  if (!completed) console.error(`Browser ${browserPid} stopped: ${server.process().exitCode !== null}`);
}
