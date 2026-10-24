// SECTION_FILL_DISTINGUISHABLE probe: same frame/camera, product hook toggles ONLY the section fill; ΔE76 at
// samples inside the projected section polygon (≥ margin_px from its edges), thresholds from the gate's own lib.
// Usage: node section-fill-probe.mjs <worktree> <fixtures.json> <outJson>
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const wt = resolve(process.argv[2]);
const lib = await import(pathToFileURL(join(wt, 'frontend/scripts/compiler-scene-replay-lib.mjs')).href);
const { deltaE76, NGUONG_TO_THIET_DIEN: T } = lib;
const { chromium } = createRequire(join(wt, 'frontend/package.json'))('playwright');
const { PNG } = await import(pathToFileURL(join(wt, 'frontend/scripts/png-pixels.mjs')).href).catch(() => ({}));
const raw = JSON.parse(readFileSync(join(wt, 'frontend/src/data/geometry-samples.json'), 'utf8'));
const samples = Array.isArray(raw) ? raw : (raw.samples ?? Object.values(raw));
const fixtures = JSON.parse(readFileSync(resolve(process.argv[3]), 'utf8')).fixtures;
const CASES = [['sample', 'thiet-dien-chop'], ['fixture', 'CORPUS-DEV01-construct'], ['fixture', 'CORPUS-DEV03-construct'],
  ['fixture', 'CORPUS-DEV10-prism-area'], ['fixture', 'PERP-square-third'], ['fixture', 'PARA-0']];
const envOf = ([k, id]) => k === 'sample' ? samples.find(s => s.id === id).envelope : fixtures.find(f => f.id === id).envelope;
const url = 'http://127.0.0.1:3117';
const out = { thresholds: T, rows: [] };
const browser = await chromium.launch({ channel: 'chrome', headless: true,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
try {
  for (const c of CASES) {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
    await ctx.addInitScript(() => {
      window.__scenes = [];
      const hub = new EventTarget();
      hub.addEventListener('observe', e => { const d = e.detail; if (d?.isScene) window.__scenes.push(d);
        if (d?.isWebGLRenderer) { const r = d.render.bind(d); d.render = (s, cam) => { window.__lastCam = cam; return r(s, cam); }; } });
      window.__THREE_DEVTOOLS__ = hub;
    });
    await ctx.route('**/*', route => {
      const u = new URL(route.request().url());
      if (u.pathname === '/api/health') return route.fulfill({ json: { status: 'ok', allow_live_ai: false } });
      if (u.pathname === '/api/auth/me') return route.fulfill({ json: null });
      if (u.origin === url && !u.pathname.startsWith('/api/')) return route.continue();
      return route.abort();
    });
    const page = await ctx.newPage();
    await page.goto(url);
    await page.evaluate(async env => { const { useAppStore } = await import('/src/state/store.ts'); localStorage.clear(); useAppStore.getState().loadEnvelope(env); }, envOf(c));
    await page.locator('.geo3d-canvas canvas').waitFor();
    const slider = page.locator('.geo3d-scrub input[type=range]');
    await slider.fill(await slider.getAttribute('max'));
    await page.waitForTimeout(1200);
    // Projected section polygon (screen px, relative to the canvas) from the section_fill mesh vertices.
    const info = await page.evaluate(() => {
      const scene = window.__scenes.at(-1), cam = window.__lastCam;
      const canvas = document.querySelector('.geo3d-canvas canvas'); const r = canvas.getBoundingClientRect();
      let poly = null, name = null;
      scene.traverse(n => {
        if (poly || !n.isMesh || !/^section_fill:/.test(n.name)) return;
        n.updateMatrixWorld(true);
        const p = n.geometry.getAttribute('position'); const pts = [];
        for (let i = 0; i < p.count; i++) {
          const v = new cam.position.constructor().fromBufferAttribute(p, i).applyMatrix4(n.matrixWorld).project(cam);
          pts.push([(v.x + 1) / 2 * r.width, (1 - v.y) / 2 * r.height]);
        }
        poly = pts; name = n.name;
      });
      // Obstacles, as the gate's own sampler excludes them: every visible fat-line segment and every label box.
      const proj = (v) => { const q = v.clone().project(cam); return [(q.x + 1) / 2 * r.width, (1 - q.y) / 2 * r.height]; };
      const lines = [];
      scene.traverse(n => {
        if (!n.isLine2 || !n.visible || !n.geometry?.attributes?.instanceStart) return;
        let p = n; while (p) { if (!p.visible) return; p = p.parent; }
        const s = n.geometry.attributes.instanceStart, e = n.geometry.attributes.instanceEnd;
        for (let i = 0; i < s.count; i++) {
          const a = new cam.position.constructor().fromBufferAttribute(s, i), b = new cam.position.constructor().fromBufferAttribute(e, i);
          lines.push([proj(a), proj(b), (n.material.linewidth ?? 2) / 2]);
        }
      });
      const boxes = [...document.querySelectorAll('.geo3d-label, .geo3d-nhan-mp, .geo3d-so-do')]
        .filter(el => getComputedStyle(el).opacity !== '0')
        .map(el => { const b = el.getBoundingClientRect(); return [b.left - r.left, b.top - r.top, b.right - r.left, b.bottom - r.top]; });
      return { poly, name, w: r.width, h: r.height, lines, boxes };
    });
    const row = { case: c[1], fill_mesh: info.name };
    if (!info.poly) { row.verdict = 'NO_SECTION_FILL'; out.rows.push(row); await ctx.close(); continue; }
    const shot = async () => page.locator('.geo3d-canvas canvas').screenshot();
    await page.evaluate(() => window.__geo3d_set_section_fill_visible(true)); await page.waitForTimeout(150);
    const on = await shot();
    await page.evaluate(() => window.__geo3d_set_section_fill_visible(false)); await page.waitForTimeout(150);
    const off = await shot();
    await page.evaluate(() => window.__geo3d_set_section_fill_visible(true));
    row.on_png = on.toString('base64').length; // presence only
    // Triangles (fan of the fill mesh) → sample a grid inside, at ≥ margin from every triangle-fan outer edge.
    const tris = []; for (let i = 0; i + 2 < info.poly.length; i += 3) tris.push(info.poly.slice(i, i + 3));
    const inTri = (p, [a, b, cc]) => { const s = (u, v, w) => (u[0] - w[0]) * (v[1] - w[1]) - (v[0] - w[0]) * (u[1] - w[1]);
      const d1 = s(p, a, b), d2 = s(p, b, cc), d3 = s(p, cc, a); return !((d1 < 0 || d2 < 0 || d3 < 0) && (d1 > 0 || d2 > 0 || d3 > 0)); };
    const edges = []; const key = (a, b) => [a, b].map(p => p.map(x => x.toFixed(1)).join(',')).sort().join('|');
    const cnt = new Map(); for (const t of tris) for (let i = 0; i < 3; i++) { const k = key(t[i], t[(i + 1) % 3]); cnt.set(k, (cnt.get(k) ?? 0) + 1); edges.push([t[i], t[(i + 1) % 3], k]); }
    const boundary = edges.filter(e => cnt.get(e[2]) === 1);
    const distSeg = (p, a, b) => { const dx = b[0] - a[0], dy = b[1] - a[1]; const t = Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy || 1)));
      return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy); };
    const decode = (await import(pathToFileURL(join(wt, 'frontend/scripts/png-pixels.mjs')).href)).docPNG;
    const A = decode(on), B = decode(off);
    const px = (img, x, y) => { const i = (y * img.w + x) * 4; return [img.rgba[i], img.rgba[i + 1], img.rgba[i + 2]]; };
    const des = [];
    const xs = info.poly.map(p => p[0]), ys = info.poly.map(p => p[1]);
    for (let y = Math.ceil(Math.min(...ys)); y < Math.max(...ys); y += 3) for (let x = Math.ceil(Math.min(...xs)); x < Math.max(...xs); x += 3) {
      const p = [x, y];
      if (!tris.some(t => inTri(p, t))) continue;
      if (boundary.some(([a, b]) => distSeg(p, a, b) < T.margin_px)) continue;
      if (info.lines.some(([a, b, hw]) => distSeg(p, a, b) < hw + T.margin_px)) continue;
      if (info.boxes.some(([l, t, rr, bb]) => x >= l - T.margin_px && x <= rr + T.margin_px && y >= t - T.margin_px && y <= bb + T.margin_px)) continue;
      des.push(deltaE76(px(A, x, y), px(B, x, y)));
      if (!row.pixel_pair) row.pixel_pair = { on: px(A, x, y), off: px(B, x, y) };
    }
    row.samples = des.length;
    row.mean_dE = des.length ? +(des.reduce((s, v) => s + v, 0) / des.length).toFixed(2) : null;
    row.min_dE = des.length ? +Math.min(...des).toFixed(2) : null;
    row.verdict = des.length && row.mean_dE >= T.T_ON && row.min_dE >= T.T_ON_MIN ? 'PASS' : 'FAIL';
    out.rows.push(row);
    console.log(c[1], JSON.stringify(row));
    await ctx.close();
  }
} finally { await browser.close(); writeFileSync(resolve(process.argv[4]), JSON.stringify(out, null, 2) + '\n'); }
