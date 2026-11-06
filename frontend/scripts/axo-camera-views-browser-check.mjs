// Offline camera / orbit / zoom check on a production build, for the seven scene families of the Axo brief: pyramid +
// section, oblique prism, cube with a hexagonal section, sphere cut by a plane, plane tangent to a sphere, cylinder with a
// circular section, cone with an axial section. Catalog samples open by route; the other scenes are REAL Hybrid /4
// responses produced offline by the backend route (fixtures dir, 0 provider calls) and enter through the real composer.
// Per scene, at the final construction step: default view, orbit 90° and 180°, near-top view, zoom in/out to the limits,
// step change, dock collapse/reopen, reset view — with a capture of each and these invariants: the orbit target never
// moves, a step change and a dock toggle leave the camera where it was, zoom stays inside its limits with the figure still
// rendered, reset returns to the default pose, one WebGL canvas, no duplicate visual owners, no page error.
// Usage: node scripts/axo-camera-views-browser-check.mjs --dist <dir> --fixtures <dir> --out <fresh dir>
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from 'node:fs';
import { resolve, join, extname } from 'node:path';
import assert from 'node:assert/strict';

const arg = (k, d) => (process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : d);
const dist = resolve(arg('--dist', 'dist'));
const fixturesDir = resolve(arg('--fixtures'));
const out = resolve(arg('--out'));
if (existsSync(out)) throw Error('Fresh output directory required');
mkdirSync(out, { recursive: true });
const fixtures = Object.fromEntries(readdirSync(fixturesDir).filter((f) => f.endsWith('-response.json'))
  .map((f) => [f.replace(/-response\.json$/, ''), JSON.parse(readFileSync(join(fixturesDir, f), 'utf8'))]));
const byText = new Map(Object.values(fixtures).map((f) => [f.problem_text.trim(), f.response]));
const auditScenes = JSON.parse(readFileSync('../docs/evaluation/geometry/runs/geometric-visual-correctness-framing/demos/audit_scenes.json', 'utf8'));
const baseEnvelope = JSON.parse(readFileSync('src/data/geometry-samples.json', 'utf8')).samples[0].envelope;
const SCENES = [
  { id: 'pyramid-section', route: 'thiet-dien-chop' },
  { id: 'pyramid-three-point-pentagon', fixture: 'case_c_pentagon_exterior_q_on_line' },
  { id: 'oblique-prism', fixture: 'oblique_prism' },
  { id: 'cube-hexagon', fixture: 'cube_hexagon' },
  { id: 'sphere-cut-by-plane', route: 'cau-cat-mat-phang' },
  { id: 'plane-tangent-to-sphere', fixture: 'tangent-plane-sphere' },
  { id: 'cylinder-circular-section', route: 'tru-thiet-dien-tron' },
  { id: 'cone-axial-section', route: 'non-thiet-dien-truc' },
  { id: 'right-prism', audit: 'family05_prism' },
  { id: 'nested-pyramids', audit: 'family04_derived_sub_pyramid' },
].filter(s => !arg('--only', '') || arg('--only', '').split(',').includes(s.id));

const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml' };
const server = createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  if (pathname === '/api/analyze' && req.method === 'POST') {
    let raw = ''; req.on('data', (c) => { raw += c; }); req.on('end', () => {
      const r = byText.get(JSON.parse(raw).input.content.trim());
      res.setHeader('Content-Type', 'application/json'); res.statusCode = r ? 200 : 400;
      res.end(JSON.stringify(r ?? { error: 'unknown fixture' }));
    });
    return;
  }
  if (pathname.startsWith('/api/')) { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(pathname === '/api/health' ? { ok: true, hasKey: true } : { user: null })); return; }
  const file = join(dist, pathname.includes('.') ? pathname : 'index.html');
  if (!file.startsWith(dist) || !existsSync(file)) { res.writeHead(404); res.end(); return; }
  res.setHeader('Content-Type', mime[extname(file)] ?? 'application/octet-stream'); res.end(readFileSync(file));
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const url = `http://127.0.0.1:${server.address().port}`;
const report = { schema: 'axo-camera-views/1', dist, provider_calls: 0, scenes: [], forbidden: [] };
const save = () => writeFileSync(join(out, 'receipt.json'), JSON.stringify(report, null, 2));
const browser = await chromium.launch({ channel: 'chrome', headless: true });
report.browser = browser.version();
const [width, height] = arg('--viewport', '1440x900').split('x').map(Number);
report.viewport = { width, height };
const ctx = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1 });
await ctx.route('**/*', (r) => { if (new URL(r.request().url()).origin !== url) { report.forbidden.push(r.request().url()); return r.abort(); } return r.continue(); });
const page = await ctx.newPage();
const errors = []; page.on('pageerror', (e) => errors.push(e.message));

const cam = () => page.evaluate(() => ({ p: window.__geo3d_camera_snapshot?.position ?? null, t: window.__geo3d_camera_target ?? null,
  rendered: (window.__geo3d_rendered_object_ids ?? []).length, dup: window.__geo3d_duplicate_visual_owner_ids ?? [],
  hidden: (window.__geo3d_hidden_edge_ids ?? []).length, visible: (window.__geo3d_visible_edge_ids ?? []).length,
  support: window.__geo3d_camera_snapshot?.support_along_view ?? null, minD: window.__geo3d_camera_snapshot?.min_distance ?? null,
  canvases: document.querySelectorAll('canvas').length }));
const d3 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
// Observability at the near limit: the main solid's near surface (support along the view) is at most half way to the
// orbit centre, unless the 0.8 × fitted-distance cap keeps close-up available.
const observe = (v, dDefault, label) => {
  const d = d3(v.p, v.t), need = Math.min(2 * v.support, 0.8 * dDefault);
  assert.ok(Math.abs(d - v.minD) <= 0.02 * v.minD, `${label}: zoom did not reach the near limit (${d.toFixed(3)} vs ${v.minD})`);
  assert.ok(v.support > 0 && d >= need - 1e-2, `${label}: camera ${d.toFixed(3)} closer than ${need.toFixed(3)} (support ${v.support})`);
  return { distance: d, support: v.support, ratio: d / v.support };
};
const settle = async () => {          // camera at rest: identical pose over two reads 300 ms apart (bounded)
  let prev = await cam();
  for (let i = 0; i < 40; i++) {
    await page.waitForTimeout(300);
    const now = await cam();
    if (prev.p && now.p && d3(prev.p, now.p) < 1e-9) return now;
    prev = now;
  }
  throw Error('camera never came to rest');
};
const canvasBox = () => page.locator('.geo3d-canvas canvas').boundingBox();
const drag = async (dx, dy) => {
  const b = await canvasBox();
  const x0 = b.x + b.width / 2 - dx / 2, y0 = b.y + b.height / 2 - dy / 2;
  await page.mouse.move(x0, y0); await page.mouse.down();
  for (let i = 1; i <= 40; i++) await page.mouse.move(x0 + (dx * i) / 40, y0 + (dy * i) / 40);
  await page.mouse.up();
};
// Wheel over the 3D canvas, as a user would: after a long drag the pointer can rest on a dock/toolbar overlay
// (mobile), where the wheel scrolls the panel instead of zooming.
const wheelOnCanvas = async (dy, times) => {
  const b = await canvasBox(); await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2);
  for (let i = 0; i < times; i++) await page.mouse.wheel(0, dy);
};
const shot = (sid, name) => !process.argv.includes('--compact') || /default|orbit-180|near-top|zoom-in|reset-view/.test(name)
  ? page.screenshot({ path: join(out, `${sid}-${name}.png`) }) : Promise.resolve();

for (const sc of SCENES) {
  const row = { id: sc.id, views: {} }; report.scenes.push(row);
  const errs = errors.length;
  try {
    if (sc.route) {
      await page.goto(`${url}/simulation/${sc.route}`);
    } else if (sc.audit) {
      const f = auditScenes.find(x => x.id === sc.audit); assert.ok(f, 'audit scene missing');
      await page.goto(`${url}/library`); await page.waitForFunction(() => !!window.__ALGO_SIM_STORE__);
      await page.evaluate(env => window.__ALGO_SIM_STORE__.getState().loadEnvelope(env),
        { ...baseEnvelope, title: 'Hình không gian', config: { ...baseEnvelope.config, title: sc.id }, description: f.problem_text, scene3d: f.scene });
    } else {
      const f = fixtures[sc.fixture]; assert.ok(f, `missing fixture ${sc.fixture}`);
      await page.goto(`${url}/`); await page.waitForSelector('#home-problem-input');
      await page.locator('#home-problem-input').fill(f.problem_text);
      await page.waitForFunction(() => !document.querySelector('#btn-composer-send')?.hasAttribute('disabled'));
      await page.locator('#btn-composer-send').click();
    }
    await page.waitForSelector('#dock-steps-ul [data-step]', { timeout: 30000 });
    const n = await page.locator('#dock-steps-ul [data-step]').count();
    await page.locator(`#dock-steps-ul [data-step="${n - 1}"]`).click();
    const base = await settle();
    assert.ok(base.rendered > 0 && base.canvases === 1, `rendered ${base.rendered}, canvases ${base.canvases}`);
    row.views.default = base; await shot(sc.id, '0-default');
    const b = await canvasBox();
    const keepTarget = (v, name) => assert.ok(d3(v.t, base.t) < 1e-6, `${name}: orbit target moved ${JSON.stringify(v.t)} vs ${JSON.stringify(base.t)}`);
    await drag(b.height / 4, 0); row.views.orbit90 = await settle(); keepTarget(row.views.orbit90, 'orbit 90°'); await shot(sc.id, '1-orbit-90');
    await drag(b.height / 4, 0); row.views.orbit180 = await settle(); keepTarget(row.views.orbit180, 'orbit 180°'); await shot(sc.id, '2-orbit-180');
    await drag(0, Math.min(b.height - 40, 600)); row.views.top = await settle(); keepTarget(row.views.top, 'top view'); await shot(sc.id, '3-near-top');
    for (const [k, v] of Object.entries(row.views)) {
      assert.deepEqual(v.dup, [], `${k}: duplicate visual owners`);
      assert.ok(v.rendered > 0, `${k}: nothing rendered`);
    }
    await wheelOnCanvas(-400, 25);
    row.views.zoomIn = await settle(); keepTarget(row.views.zoomIn, 'zoom in');
    const dIn = d3(row.views.zoomIn.p, row.views.zoomIn.t);
    assert.ok(dIn > 0.4 && row.views.zoomIn.rendered > 0, `zoom in reached distance ${dIn}`); await shot(sc.id, '4-zoom-in-limit');
    const dDefault = d3(base.p, base.t);
    row.observability = { nearTopZoomIn: observe(row.views.zoomIn, dDefault, 'near-top zoom in') };
    await wheelOnCanvas(400, 40);
    row.views.zoomOut = await settle(); keepTarget(row.views.zoomOut, 'zoom out');
    const dOut = d3(row.views.zoomOut.p, row.views.zoomOut.t);
    assert.ok(Number.isFinite(dOut) && dOut > dIn && row.views.zoomOut.rendered > 0, `zoom out distance ${dOut}`); await shot(sc.id, '5-zoom-out-limit');
    row.zoom = { min: dIn, max: dOut };
    await page.locator('#dock-steps-ul [data-step="0"]').click(); const step0 = await settle();
    await page.locator(`#dock-steps-ul [data-step="${n - 1}"]`).click(); const stepN = await settle();
    assert.ok(d3(step0.p, row.views.zoomOut.p) < 1e-6 && d3(stepN.p, row.views.zoomOut.p) < 1e-6, 'a step change moved the camera');
    keepTarget(stepN, 'step change'); await shot(sc.id, '6-after-step-change');
    await page.locator('#btn-collapse-dock').click(); const collapsed = await settle(); await shot(sc.id, '7-dock-collapsed');
    await page.locator('#btn-reopen-dock-capsule').click(); const reopened = await settle(); await shot(sc.id, '8-dock-reopened');
    assert.ok(d3(collapsed.p, stepN.p) < 1e-6 && d3(reopened.p, stepN.p) < 1e-6, 'dock toggle moved the camera');
    keepTarget(reopened, 'dock toggle');
    await page.locator('#btn-reset-pos').click(); const reset = await settle(); await shot(sc.id, '9-reset-view');
    assert.ok(d3(reset.p, base.p) < 1e-3 && d3(reset.t, base.t) < 1e-6, `reset view ${JSON.stringify(reset.p)} vs default ${JSON.stringify(base.p)}`);
    row.views.reset = reset;
    await drag(b.height / 5, b.height / 7);                       // an oblique view, then the near limit from there
    await wheelOnCanvas(-400, 25);
    row.views.obliqueZoomIn = await settle(); keepTarget(row.views.obliqueZoomIn, 'oblique zoom in');
    row.observability.obliqueZoomIn = observe(row.views.obliqueZoomIn, dDefault, 'oblique zoom in');
    await shot(sc.id, '10-oblique-zoom-in');
    await page.locator('#btn-reset-pos').click(); await settle();
    if (!process.argv.includes('--skip-recovery')) {
    await drag(30, 12); const saved = await settle();
    await page.waitForTimeout(250); await page.reload();
    await page.waitForSelector('#dock-steps-ul [data-step]');
    await page.locator(`#dock-steps-ul [data-step="${n - 1}"]`).click();
    const restored = await settle();
    assert.ok(d3(restored.p, saved.p) < 1e-3 && d3(restored.t, saved.t) < 1e-6, 'reload lost camera pose');
    const rb = await canvasBox(); await page.mouse.move(rb.x + rb.width * .5, rb.y + rb.height * .5);
    for (let i = 0; i < 25; i++) await page.mouse.wheel(0, -400);
    const restoredNear = await settle();
    const restoredMin = d3(restoredNear.p, restoredNear.t);
    row.recovery = { saved, restored, originalMin: dIn, restoredMin };
    // The restored pose keeps the scene-derived near limit (not OrbitControls' 0..Infinity), for ITS view direction.
    assert.ok(Math.abs(restoredMin - restoredNear.minD) < 1e-3, `reload lost the zoom limit: ${restoredMin} vs ${restoredNear.minD}`);
    row.observability.restoredZoomIn = observe(restoredNear, dDefault, 'restored zoom in');
    }
    assert.deepEqual(errors.slice(errs), [], 'page errors');
    row.status = 'PASS';
  } catch (e) {
    row.status = 'FAIL'; row.error = e.message.slice(0, 800);
    await shot(sc.id, 'failure').catch(() => {});
  }
  save(); console.log(`${row.status} ${sc.id}${row.error ? `: ${row.error}` : ''}`);
}
report.summary = { pass: report.scenes.filter((s) => s.status === 'PASS').length, total: report.scenes.length };
save(); await browser.close(); server.close();
console.log(JSON.stringify(report.summary));
if (report.forbidden.length || report.summary.pass !== report.summary.total) process.exitCode = 1;
