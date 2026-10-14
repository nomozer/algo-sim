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
 * `--scenes two-line --playback` replaces those checks with the per-step construction audit (run `scene3d-construction-audit`):
 * every learner step screenshotted and projection-checked, revisit, second view, H/H1 selection, contact sheet per scene;
 * its receipt feeds `backend/scripts/audit_scene3d_construction.py --browser`.
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { createHash } from "node:crypto";
import { pathToFileURL } from "node:url";
import { execFileSync } from "node:child_process";
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
// `sequencing` = the two-line problems re-exported after the learner construction order; checked like `two-line`.
const twoLine = source === "two-line" || source === "sequencing";
if (!["hardening", "goal", "two-line", "sequencing"].includes(source)) throw new Error("unknown --scenes");
const SCENES_RUN = source === "sequencing" ? "pedagogical-construction-sequencing" : source === "two-line" ? "two-line-plane-section" : source === "goal" ? "goal-directed-section-planning" : "hybrid-semantic-hardening";
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
// `--playback` (two-line only): walk EVERY learner step of the product scrubber with the real slider (camera fixed, as in
// the product), one neutral screenshot per step, and check each frame against the payload: rendered ids ⊆ objects present
// at that step, every drawable present object drawn, vertex markers and point labels at the projection of the EXACT payload
// coordinates through the live camera (`__geo3d_camera_snapshot` is view × model, model = display rotation · chart T).
// Then: revisit a step (pixel-identical), a second view (orbit) with the same projection checks, H/H1 selection, contact sheet.
const playback = process.argv.includes("--playback");
const playbackReport = [];
const num = (s) => { const [a, b] = String(s).split("/"); return b === undefined ? Number(a) : Number(a) / Number(b); };
const project = (cam, p) => {
  const mul = (M, v) => [0, 1, 2, 3].map((r) => M[r] * v[0] + M[4 + r] * v[1] + M[8 + r] * v[2] + M[12 + r] * v[3]);
  const c = mul(cam.projection_matrix_column_major, mul(cam.view_matrix_column_major, [...p, 1]));
  return [((c[0] / c[3] + 1) / 2) * cam.viewport_width, ((1 - c[1] / c[3]) / 2) * cam.viewport_height];
};
const probe = () => page.evaluate(() => ({
  step: window.__hybrid.step, rendered: window.__geo3d_rendered_object_ids ?? [], highlighted: window.__geo3d_highlighted_ids ?? [],
  aux_hidden: window.__geo3d_auxiliary_hidden_ids ?? [], hidden_edges: (window.__geo3d_hidden_edge_ids ?? []).slice().sort(),
  markers: window.__geo3d_vertex_markers ?? [], camera: window.__geo3d_camera_snapshot,
  labels: [...document.querySelectorAll(".geo3d-label")].map((e) => {
    const m = /translate\(([-\d.e]+)px,\s*([-\d.e]+)px\)\s*$/.exec(e.style.transform);
    return { id: e.dataset.id, text: e.textContent, shown: e.style.opacity === "1", anchor: m ? [Number(m[1]), Number(m[2])] : null,
      w: e.offsetWidth, h: e.offsetHeight };
  }),
}));
function projectionCheck(row, f) {
  const xyz = Object.fromEntries(row.scene.objects.filter((o) => o.type === "point3").map((o) => [o.id, o.xyz.map(num)]));
  let chart = 0, marker = 0, label = 0;
  const bad = [];
  const markerIds = new Set();
  for (const mk of f.markers) {
    if (!mk.id || !xyz[mk.id]) continue;
    markerIds.add(mk.id);
    chart = Math.max(chart, Math.hypot(...mk.center.map((v, j) => v - xyz[mk.id][j])));
    const a = project(f.camera, mk.center), b = project(f.camera, xyz[mk.id]);
    marker = Math.max(marker, Math.hypot(a[0] - b[0], a[1] - b[1]));
  }
  for (const l of f.labels) {
    if (!l.shown) continue;
    if (!l.anchor || !xyz[l.id]) { bad.push(`label ${l.id} without anchor/payload point`); continue; }
    const b = project(f.camera, xyz[l.id]);
    label = Math.max(label, Math.hypot(l.anchor[0] - b[0], l.anchor[1] - b[1]));
  }
  // A label hidden by the overlap filter must really overlap a shown label: its box is `translate(-50%,-140%)` from the anchor.
  const box = (l) => [l.anchor[0] - l.w / 2, l.anchor[1] - 1.4 * l.h, l.anchor[0] + l.w / 2, l.anchor[1] - 0.4 * l.h];
  const meets = (a, b) => a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3];
  const shown = f.labels.filter((l) => l.shown && l.anchor).map(box);
  const hiddenFree = f.labels.filter((l) => !l.shown && l.anchor && l.w > 0 && !shown.some((b) => meets(box(l), b))).map((l) => l.id);
  if (hiddenFree.length) bad.push(`labels hidden without overlapping a shown label: ${hiddenFree}`);
  // ... and the reverse: shown labels never overlap each other (a filter that hides nothing would pass the check above)
  const overlapping = shown.flatMap((a, i) => shown.slice(i + 1).filter((b) => meets(a, b)).map(() => i));
  if (overlapping.length) bad.push(`${overlapping.length} pairs of shown labels overlap`);
  if (chart > 1e-6) bad.push(`marker chart coordinates off by ${chart}`);
  if (marker > 0.5) bad.push(`marker projection off by ${marker}px`);
  if (label > 1) bad.push(`label anchor off by ${label}px`);
  return { max_chart_error: chart, max_marker_px: marker, max_label_px: label, marker_ids: [...markerIds].sort(),
    labels_hidden_without_overlap: hiddenFree, failures: bad };
}
async function playbackAudit() {
  if (!twoLine) throw new Error("--playback needs --scenes two-line or sequencing");
  for (const [i, row] of rows.entries()) {
    const dir = join(out, row.id);
    mkdirSync(dir);
    const e0 = errors.length;
    if (!row.served) {
      await goto(`i=${i}`, true);
      await page.screenshot({ path: join(dir, "refused.png") });
      const text = await page.getByTestId("refusal").innerText();
      const r = { id: row.id, served: false, screenshot: `${row.id}/refused.png`, text, canvas_count: await page.locator("canvas").count(),
        console_errors: errors.slice(e0) };
      if (r.canvas_count || !text.includes(row.code) || r.console_errors.length) failures.push(`${row.id}: refusal surface`);
      playbackReport.push(r);
      continue;
    }
    await goto(`i=${i}`);
    const h = await page.evaluate(() => window.__hybrid);
    const objs = new Map(row.scene.objects.map((o) => [o.id, o]));
    const slider = page.getByRole("slider", { name: "Bước dựng" });
    await slider.focus(); await page.keyboard.press("Home");
    let cur = 0;
    const toStep = async (k) => {
      await slider.focus();
      if (k < cur) { await page.keyboard.press("Home"); cur = 0; }
      while (cur < k) { await page.keyboard.press("ArrowRight"); cur++; }
      return settle();
    };
    const steps = [];
    const shots = new Map();
    for (const g of h.timeline) {
      const s = await toStep(g.anchor);
      const f = await probe();
      const present = await page.evaluate((k) => window.__hybrid.presentAt(k), g.anchor);
      const name = `step-${String(g.index + 1).padStart(2, "0")}.png`;
      writeFileSync(join(dir, name), s.b);
      shots.set(g.index, s.b);
      const base = f.rendered.map((x) => x.split("#")[0]);
      const drawable = present.filter((id) => !["non_visual", "readout"].includes(objs.get(id).render) && !f.aux_hidden.includes(id));
      const proj = projectionCheck(row, f);
      const pointsDrawn = drawable.filter((id) => objs.get(id).type === "point3");
      const st = {
        index: g.index, start: g.start, end: g.end, anchor: g.anchor, screenshot: `${row.id}/${name}`, settled: s.settled,
        learner_text: row.scene.formation.steps.slice(g.start, g.end + 1).map((x) => x.learner_text),
        present, rendered: f.rendered, highlighted: f.highlighted, aux_hidden: f.aux_hidden, hidden_edges: f.hidden_edges,
        labels_shown: f.labels.filter((l) => l.shown).map((l) => l.id), labels_suppressed: f.labels.filter((l) => !l.shown).map((l) => l.id),
        label_anchors: Object.fromEntries(f.labels.filter((l) => l.shown).map((l) => [l.id, l.anchor])),
        projection: proj,
        failures: [
          ...(f.step === g.anchor ? [] : [`harness step ${f.step} != anchor ${g.anchor}`]),
          // frontend step model (objectsAt) = backend formation snapshot at this frame
          ...(JSON.stringify([...present].sort()) === JSON.stringify([...row.scene.formation.steps[g.anchor].visible_ids].sort())
            ? [] : ["objectsAt differs from formation visible_ids"]),
          ...base.filter((id) => !present.includes(id)).map((id) => `${id} rendered before it exists`),
          ...drawable.filter((id) => !base.includes(id)).map((id) => `${id} present but not drawn`),
          ...pointsDrawn.filter((id) => !proj.marker_ids.includes(id)).map((id) => `${id} drawn without a vertex marker`),
          ...proj.failures, ...(s.settled ? [] : ["frame did not settle"]),
        ],
      };
      steps.push(st);
      failures.push(...st.failures.map((x) => `${row.id} step ${g.index + 1}: ${x}`));
    }
    // camera is fixed while stepping ⇒ a label keeps its pixel anchor, and the solid's hidden-edge set does not change
    const drift = {};
    for (const st of steps) for (const [id, a] of Object.entries(st.label_anchors)) {
      const first = steps.find((x) => x.label_anchors[id]).label_anchors[id];
      drift[id] = Math.max(drift[id] ?? 0, Math.hypot(a[0] - first[0], a[1] - first[1]));
    }
    const solidId = row.scene.objects.find((o) => o.type === "solid").id;
    const solidEdges = (st) => st.hidden_edges.filter((e) => e.startsWith(`${solidId}::edge:`)).join(",");
    const withSolid = steps.filter((st) => st.present.includes(solidId));
    const occlusion = { stable: withSolid.every((st) => solidEdges(st) === solidEdges(withSolid[0])),
      hidden_solid_edges: withSolid[0] ? solidEdges(withSolid[0]).split(",").filter(Boolean) : [] };
    if (Object.values(drift).some((d) => d > 0.5)) failures.push(`${row.id}: label moved between steps ${JSON.stringify(drift)}`);
    if (!occlusion.stable) failures.push(`${row.id}: hidden solid edges change between steps at a fixed camera`);
    // revisit: leave the middle step, come back with the slider ⇒ identical pixels
    const mid = h.timeline[Math.floor(h.timeline.length / 2)];
    await page.keyboard.press("End"); cur = h.stepCount - 1; await settle();
    const back = await toStep(mid.anchor);
    const revisit = { step: mid.index + 1, changed_pixels: pixels(shots.get(mid.index), back.b) };
    if (revisit.changed_pixels !== 0) failures.push(`${row.id}: revisiting step ${mid.index + 1} changed ${revisit.changed_pixels} px`);
    // second view at the last step: same projection checks under an orbited camera
    await toStep(h.stepCount - 1);
    const orbit = await orbitGesture();
    writeFileSync(join(dir, "final-orbit.png"), orbit.b);
    const fo = await probe();
    const second = { screenshot: `${row.id}/final-orbit.png`, settled: orbit.settled, projection: projectionCheck(row, fo),
      labels_shown: fo.labels.filter((l) => l.shown).map((l) => l.id), labels_suppressed: fo.labels.filter((l) => !l.shown).map((l) => l.id) };
    failures.push(...second.projection.failures.map((x) => `${row.id} orbit: ${x}`));
    await page.getByRole("button", { name: "Đặt lại khung nhìn" }).click();
    await settle();
    // selection of each auxiliary point (H, H1) at the last step
    const selected = [];
    for (const o of row.scene.objects.filter((x) => x.source?.binding === "AUXILIARY")) {
      await page.getByRole("combobox", { name: "Chọn đối tượng" }).selectOption(o.id);
      const s = await settle();
      writeFileSync(join(dir, `selected-${o.id}.png`), s.b);
      const fs = await probe();
      selected.push({ id: o.id, screenshot: `${row.id}/selected-${o.id}.png`, details: await page.getByTestId("selection-details").innerText(),
        selected_id: await page.evaluate(() => window.__geo3d_selected_id), highlighted: fs.highlighted, labels_shown: fs.labels.filter((l) => l.shown).map((l) => l.id) });
      if (selected.at(-1).selected_id !== o.id) failures.push(`${row.id}: selecting ${o.id} failed`);
      await page.getByRole("combobox", { name: "Chọn đối tượng" }).selectOption(""); await settle();
    }
    // contact sheet: the step screenshots in order, captions from the trace (no image editing)
    const esc = (t) => String(t).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]);
    writeFileSync(join(dir, "contact-sheet.html"), `<!doctype html><meta charset="utf-8"><title>${row.id}</title>
<style>body{font:13px system-ui;margin:12px;background:#fff}div.g{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
figure{margin:0;border:1px solid #ccc;padding:4px}img{width:100%}figcaption{padding-top:4px}</style>
<h1 style="font-size:16px">${esc(row.id)} — ${h.timeline.length} learner steps / ${h.stepCount} trace steps</h1><div class="g">
${steps.map((st) => `<figure><img src="${st.screenshot.split("/")[1]}"><figcaption><b>Bước ${st.index + 1}/${steps.length}</b> · trace ${st.start}${st.end > st.start ? `–${st.end}` : ""}<br>${esc(st.learner_text.join(" · "))}</figcaption></figure>`).join("\n")}
</div>`);
    const sheet = await browser.newPage({ viewport: { width: 1600, height: 900 } });
    await sheet.goto(pathToFileURL(join(dir, "contact-sheet.html")).href);
    await sheet.screenshot({ path: join(dir, "contact-sheet.png"), fullPage: true });
    await sheet.close();
    const r = { id: row.id, served: true, learner_steps: h.timeline.length, trace_steps: h.stepCount, steps, world_points: h.world,
      label_drift_px: drift, occlusion, revisit, second_view: second, selected, final_neutral: steps.at(-1).screenshot,
      plane_name_on_canvas: steps.at(-1).labels_shown.includes("mp_td_q"), console_errors: errors.slice(e0) };
    if (r.console_errors.length) failures.push(`${row.id}: console errors`);
    playbackReport.push(r);
    console.log(JSON.stringify({ id: row.id, steps: steps.length, failures: failures.filter((x) => x.startsWith(row.id)) }));
  }
}
// `--only <id prefix>`: measure those cases only; the harness index `i` stays the case's position in scenes.json.
const only = arg("--only");
if (playback) await playbackAudit();
else for (const [i, row] of rows.entries()) {
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
  if (twoLine && !target) failures.push(`${row.id}: served scene missing section target`);
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
    if (twoLine && !order.depends_before) failures.push(`${row.id}: section dependencies not built earlier`);
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
  if (twoLine && target) {
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
  browser_version: browser.version(), browser_pid: browserPid,
  git_head: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf-8" }).trim(),
  git_dirty_paths: execFileSync("git", ["status", "--porcelain"], { encoding: "utf-8" }).split(/\r?\n/).filter(Boolean).length,
  browser_stopped: server.process().exitCode !== null,
  scenes_sha256: createHash("sha256").update(scenesBytes).digest("hex"),
  failures, console_errors: errors, net_retries: netRetries, dev_server_noise: devServerNoise.length, report,
  ...(playback ? { playback: playbackReport } : {}) }, null, 1));
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
