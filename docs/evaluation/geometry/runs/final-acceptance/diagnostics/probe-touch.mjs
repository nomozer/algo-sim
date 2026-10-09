// Throwaway probe: emulated TOUCH input (CDP Input.dispatchTouchEvent) on phone sizes. 0 model calls.
// Automated SUPPORT for E-R6 / F-R7 only — emulated touch in headless Chrome is not a real phone.
// usage: node probe-touch.mjs <repo> <dist> <out.json>
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const [REPO, DIST, OUT] = process.argv.slice(2);
const imp = (p) => import(pathToFileURL(join(REPO, "frontend/scripts", p)).href);
const { sleep } = await imp("browser-runner.mjs");
const { phucVu } = await imp("scene3d-orbit-gate.mjs");
const { openFixture } = await imp("compiler-scene-suite.mjs");
const { pollUntil } = await imp("compiler-scene-replay-lib.mjs");
const FIX = join(REPO, "docs/evaluation/geometry/runs/phone-landscape-layout/inputs/fixtures");
const FAMILIES = ["regular_square_pyramid", "cross_section"];
const VIEWPORTS = {
  portrait: { width: 390, height: 844 }, portrait_small: { width: 360, height: 640 },
  landscape: { width: 844, height: 390 }, landscape_640: { width: 640, height: 360 },
};

const j = async (s, e) => JSON.parse(await s.eval(`JSON.stringify(${e})`));
const rect = (s, expr) => j(s, `(()=>{const e=${expr};if(!e)return null;const r=e.getBoundingClientRect();`
  + "return {x:r.left,y:r.top,w:r.width,h:r.height}})()");
const btn = (label) => `document.querySelector('.geo3d-controls [aria-label="${label}"]')`;
const step = (s) => j(s, "(document.querySelector('.geo3d-controls .geo3d-buoc-so')?.textContent||'').trim()");
const cam = (s) => j(s, "(window.__geo3d_camera_snapshot||{}).position||null");
const sel = (s) => j(s, "window.__geo3d_selected_id||null");
const same = (a, b) => !!a && !!b && a.every((x, i) => Math.abs(x - b[i]) < 1e-6);

async function touch(s, type, pts) {
  await s._send("Input.dispatchTouchEvent", { type, touchPoints: pts.map(([x, y], id) => ({ x, y, id })) });
}
/** Tap the element's centre — only if the element itself is what a finger would hit there. */
async function tap(s, expr) {
  const r = await rect(s, expr);
  if (!r || r.w <= 0) return "MISSING";
  const x = r.x + r.w / 2, y = r.y + r.h / 2;
  if (x < 0 || y < 0 || x > (await j(s, "innerWidth")) || y > (await j(s, "innerHeight"))) return "OUTSIDE_VIEWPORT";
  if (!await j(s, `(()=>{const e=${expr},h=document.elementFromPoint(${x},${y});return !!h&&(h===e||e.contains(h))})()`)) return "COVERED";
  await touch(s, "touchStart", [[x, y]]); await sleep(60); await touch(s, "touchEnd", []);
  await sleep(400);
  return "OK";
}
async function drag(s, x, y, dx, dy) {
  await touch(s, "touchStart", [[x, y]]);
  for (let i = 1; i <= 12; i += 1) { await touch(s, "touchMove", [[x + (dx * i) / 12, y + (dy * i) / 12]]); await sleep(16); }
  await touch(s, "touchEnd", []);
  await sleep(700);
}

async function run(family, vpKey) {
  const vp = VIEWPORTS[vpKey];
  const fixture = JSON.parse(readFileSync(join(FIX, `${family}_positive.json`), "utf8"));
  const { sv, cong } = await phucVu(DIST);
  const { session: s } = await openFixture({ port: cong, viewport: vp, fixture });
  const o = { family, viewport: vpKey, checks: {} };
  const ck = (k, pass, detail) => { o.checks[k] = { pass, ...detail }; };
  try {
    await s._send("Emulation.setDeviceMetricsOverride", { width: vp.width, height: vp.height, deviceScaleFactor: 2, mobile: true });
    await s._send("Emulation.setTouchEmulationEnabled", { enabled: true, maxTouchPoints: 5 });
    await pollUntil(() => j(s, "!!document.querySelector('.geo3d-canvas canvas')"), Boolean, { timeoutMs: 20000 });
    await j(s, "(scrollTo(0,0),true)");
    await sleep(1500);

    // 1. one-finger drag on the canvas rotates the camera, page does not scroll
    const c = await rect(s, "document.querySelector('.geo3d-canvas canvas')");
    const cam0 = await cam(s), sy0 = await j(s, "scrollY");
    await drag(s, c.x + c.w * 0.5, c.y + c.h * 0.5, 120, 30);
    const cam1 = await cam(s);
    ck("orbit_by_touch", !!cam1 && !same(cam0, cam1) && (await j(s, "scrollY")) === sy0,
      { camera_changed: !same(cam0, cam1), page_scrolled: (await j(s, "scrollY")) !== sy0 });

    // 2. «Xem lại toàn hình» by tap returns the initial camera
    const tv = await tap(s, "[...document.querySelectorAll('.geo3d-noi-nut')].find(b=>b.textContent.includes('Xem lại toàn hình'))");
    await sleep(1200);
    ck("overview_by_tap", tv === "OK" && same(await cam(s), cam0), { tap: tv, camera_restored: same(await cam(s), cam0) });

    // 3. step back / forward by tap
    const st0 = await step(s);
    // Scenes open at step 1, where «Bước trước» is a no-op — go forward first.
    const tf = await tap(s, btn("Bước sau"));
    const st1 = await step(s);
    const tb = await tap(s, btn("Bước trước"));
    const st2 = await step(s);
    ck("step_by_tap", tb === "OK" && tf === "OK" && st1 !== st0 && st2 === st0, { back: tb, fwd: tf, steps: [st0, st1, st2] });

    // 4. play then pause by tap
    await tap(s, btn("Bước trước")); await tap(s, btn("Bước trước"));
    const p0 = await step(s);
    const tp = await tap(s, "document.querySelector('.geo3d-controls [aria-label=\"Phát lại quá trình dựng\"],.geo3d-controls [aria-label=\"Xem lại quá trình dựng\"]')");
    await sleep(1800);
    const playing = await j(s, "!!document.querySelector('.geo3d-controls [aria-label=\"Tạm dừng\"]')");
    const tz = playing ? await tap(s, btn("Tạm dừng")) : "NOT_PLAYING";
    const p1 = await step(s); await sleep(1500); const p2 = await step(s);
    ck("play_pause_by_tap", tp === "OK" && tz === "OK" && p1 === p2,
      { play: tp, pause: tz, started_at: p0, paused_at: p1, after_1500ms: p2 });

    // 5. select on the figure by tap (midpoint of two visible point labels — an edge), selection survives a step change
    const pts = await j(s, "(window.__geo3d_point_label_boxes||[]).slice(0,8).map(b=>({id:b.id||b.point_id||null,...(b.box||b)}))");
    const cb = await rect(s, "document.querySelector('.geo3d-canvas')");
    let selected = null;
    for (let i = 0; i + 1 < pts.length && !selected; i += 1) {
      const a = pts[i], b = pts[i + 1];
      const x = cb.x + (a.x + a.w / 2 + b.x + b.w / 2) / 2, y = cb.y + (a.y + a.h / 2 + b.y + b.h / 2) / 2;
      await touch(s, "touchStart", [[x, y]]); await sleep(60); await touch(s, "touchEnd", []); await sleep(500);
      selected = await sel(s);
    }
    ck("select_by_tap", !!selected, { selected, tries_on_label_midpoints: Math.max(0, pts.length - 1) });

    // 6. open «Các bước dựng», collapse, expand, close — by tap
    const to = await tap(s, "document.querySelector('.geo3d-cac-buoc-mo')");
    const panel = "document.querySelector('.geo3d-bang-noi[data-panel=\"cac-buoc\"]')";
    const opened = await j(s, `!!${panel}`);
    const tg = opened ? await tap(s, `${panel}.querySelector('.geo3d-bang-noi-gon')`) : "NO_PANEL";
    const collapsed = await j(s, `!!${panel}&&${panel}.classList.contains('la-thu-gon')`);
    const te = opened ? await tap(s, `${panel}.querySelector('.geo3d-bang-noi-gon')`) : "NO_PANEL";
    const floating = await j(s, `!!${panel}&&getComputedStyle(${panel}).position==='absolute'`);
    // 7. drag a floating panel by its header (only where panels float — landscape)
    let moved = null;
    if (floating) {
      const h0 = await rect(s, `${panel}.querySelector('.geo3d-bang-noi-dau')`);
      await drag(s, h0.x + 12, h0.y + h0.h / 2, -60, 20);
      const h1 = await rect(s, `${panel}.querySelector('.geo3d-bang-noi-dau')`);
      moved = Math.abs(h1.x - h0.x) > 20 || Math.abs(h1.y - h0.y) > 10;
      ck("drag_floating_panel_by_touch", moved, { from: h0, to: h1 });
    }
    const tc = opened ? await tap(s, `${panel}.querySelector('.geo3d-bang-noi-dong')`) : "NO_PANEL";
    ck("panel_open_collapse_close_by_tap", to === "OK" && opened && tg === "OK" && collapsed && te === "OK"
      && tc === "OK" && !(await j(s, `!!${panel}`)), { open: to, collapse: tg, collapsed, expand: te, close: tc, floating });

    o.pass = Object.values(o.checks).every((x) => x.pass);
  } catch (e) {
    o.pass = false; o.error = String(e?.message || e);
  } finally { await s.close(); sv.close(); }
  return o;
}

const rows = [];
for (const f of FAMILIES) for (const v of Object.keys(VIEWPORTS)) {
  const r = await run(f, v);
  rows.push(r);
  const bad = Object.entries(r.checks).filter(([, x]) => !x.pass).map(([k]) => k);
  console.log(`${r.pass ? "✓" : "✗"} ${f} ${v} ${r.error ?? bad.join(",")}`);
}
writeFileSync(OUT, JSON.stringify({ schema: "touch-proxy-probe/1", note: "emulated touch, headless Chrome; NOT a real-device check",
  application_llm_calls: 0, rows }, null, 2));
console.log(`${rows.filter((r) => r.pass).length}/${rows.length} pass`);
