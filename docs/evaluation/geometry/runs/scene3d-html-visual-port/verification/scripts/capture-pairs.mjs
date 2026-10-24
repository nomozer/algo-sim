// HTML reference ↔ AlgoSim at the SAME view direction relative to the figure. The view direction of the HTML
// "Góc SGK" camera is expressed in an orthonormal frame built on the labelled base triangle A,B,C (z toward the apex),
// then re-expressed in AlgoSim's frame of the same labels; each renderer keeps its own framing distance.
// Usage: node capture-pairs.mjs <worktree> <html> <b1b2-fixtures.json> <outDir> <label>
import { createRequire } from 'node:module';
import { readFileSync, mkdirSync, existsSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';

const [wt, html, fxPath, out, label] = [resolve(process.argv[2]), resolve(process.argv[3]), resolve(process.argv[4]), resolve(process.argv[5]), process.argv[6] ?? 'pair'];
if (existsSync(out)) throw Error('fresh output directory required');
mkdirSync(out, { recursive: true });
const { chromium } = createRequire(join(wt, 'frontend/package.json'))('playwright');
const raw = JSON.parse(readFileSync(join(wt, 'frontend/src/data/geometry-samples.json'), 'utf8'));
const samples = Array.isArray(raw) ? raw : (raw.samples ?? Object.values(raw));
const fxBytes = readFileSync(fxPath);
const fixtures = JSON.parse(fxBytes).fixtures;
const PAIRS = [
  { html: 'chop_sa_vuong_day_vuong', alg: ['fixture', 'PERP-square-third'], apex: 'S', what: 'S.ABCD, SA ⊥ (ABCD), section' },
  { html: 'chop_sa_vuong_abc', alg: ['fixture', 'CORPUS-DEV03-construct'], apex: 'S', what: 'S.ABC, SA ⊥ (ABC), section' },
  { html: 'lang_tru_tam_giac_deu', alg: ['fixture', 'CORPUS-DEV10-prism-area'], apex: 'A′', what: 'right prism ABC.A′B′C′, section' },
  { html: 'chop_tu_giac_deu', alg: ['sample', 'thiet-dien-chop'], apex: 'S', what: 'S.ABCD, section MNPQ' },
];
const envOf = ([k, id]) => k === 'sample' ? samples.find(s => s.id === id).envelope : fixtures.find(f => f.id === id).envelope;
const norm = s => String(s).replace(/'/g, '′').replace(/\s+/g, '');
// Frame helpers (plain arrays) — injected into both pages.
const FRAME_SRC = `
  const sub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]], dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
  const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  const unit=a=>{const l=Math.hypot(...a)||1;return a.map(x=>x/l)};
  window.__frame=(A,B,C,apex)=>{const x=unit(sub(B,A));let z=unit(cross(sub(B,A),sub(C,A)));if(dot(z,sub(apex,A))<0)z=z.map(v=>-v);const y=cross(z,x);return {x,y,z};};
`;
const git = (...a) => execFileSync('git', a, { cwd: wt, encoding: 'utf8' }).trim();
const receipt = { schema: 'html-vs-algosim-pairs/1', label, algosim_commit: git('rev-parse', 'HEAD'),
  algosim_tracked_changes: git('status', '--porcelain', '--untracked-files=no'),
  html_sha256: createHash('sha256').update(readFileSync(html)).digest('hex'),
  fixtures_sha256: createHash('sha256').update(fxBytes).digest('hex'), html_radius: 15.5, rows: [], errors: [] };
const url = 'http://127.0.0.1:3117';
const browser = await chromium.launch({ channel: 'chrome', headless: true,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
try {
  for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    for (const pair of PAIRS) {
      let stage = "html";
      try {
      // ── HTML: official SGK angles, radius widened so the whole figure is in frame (receipt records it).
      const hctx = await browser.newContext({ viewport, deviceScaleFactor: 1 });
      const hp = await hctx.newPage();
      hp.on('pageerror', e => receipt.errors.push({ side: 'html', id: pair.html, message: e.message }));
      await hp.goto(pathToFileURL(html).href, { waitUntil: 'networkidle' });
      // Wait for window.onload → initThreeJS (mainGroup/camera exist), not just for function declarations.
      await hp.waitForFunction(() => typeof THREE !== 'undefined' && typeof mainGroup !== 'undefined' && !!mainGroup
        && typeof camera !== 'undefined' && !!camera && activeLabels.length > 0);
      await hp.addScriptTag({ content: FRAME_SRC });
      const h = await hp.evaluate(({ id, r }) => {
        selectShape(id); setCameraPreset('sgk'); camSpherical.radius = r; updateCameraPosition(); setConstructionStep(4);
        const pts = {};
        for (const l of activeLabels) if (l.el.classList.contains('main-vertex')) pts[l.el.textContent.trim()] = l.pos.toArray();
        return { pts, cam: camera.position.toArray(), target: camSpherical.target.toArray(), fov: camera.fov,
          spherical: { theta: camSpherical.theta, phi: camSpherical.phi, radius: camSpherical.radius }, opacity: state.opacity };
      }, { id: pair.html, r: receipt.html_radius });
      await hp.waitForTimeout(500);
      const hfile = `${label}-HTML-${pair.html}-${viewport.width}.png`;
      const hbuf = await hp.locator('#canvasContainer').screenshot({ path: join(out, hfile) });
      const hp2 = Object.fromEntries(Object.entries(h.pts).map(([k, v]) => [norm(k), v]));
      const dirHtml = (() => { const d = h.cam.map((v, i) => v - h.target[i]); const l = Math.hypot(...d); return d.map(v => v / l); })();
      const fH = await hp.evaluate(({ p, apex }) => window.__frame(p.A, p.B, p.C, p[apex]), { p: hp2, apex: pair.apex });
      const local = ['x', 'y', 'z'].map(k => fH[k].reduce((s, v, i) => s + v * dirHtml[i], 0));
      await hctx.close();

      // ── AlgoSim: product page, default fit, then camera rotated to the same figure-relative direction.
      stage = "algosim";
      const actx = await browser.newContext({ viewport, deviceScaleFactor: 1 });
      await actx.addInitScript(() => {
        window.__scenes = [];
        const hub = new EventTarget();
        hub.addEventListener('observe', e => {
          const d = e.detail;
          if (d?.isScene) window.__scenes.push(d);
          if (d?.isWebGLRenderer) { const rr = d.render.bind(d); d.render = (s, c) => { window.__lastCam = c; return rr(s, c); }; }
        });
        window.__THREE_DEVTOOLS__ = hub;
      });
      await actx.route('**/*', route => {
        const u = new URL(route.request().url());
        if (u.origin === url && u.pathname === '/api/health') return route.fulfill({ json: { status: 'ok', allow_live_ai: false } });
        if (u.origin === url && u.pathname === '/api/auth/me') return route.fulfill({ json: null });
        if (u.origin === url && !u.pathname.startsWith('/api/')) return route.continue();
        receipt.errors.push({ side: 'algosim', forbidden: u.pathname }); return route.abort();
      });
      const ap = await actx.newPage();
      ap.setDefaultTimeout(20000);
      ap.on('pageerror', e => receipt.errors.push({ side: 'algosim', id: pair.alg[1], message: e.message }));
      ap.on('console', m => { if (m.type() === 'error') receipt.errors.push({ side: 'algosim', id: pair.alg[1], console: m.text() }); });
      await ap.goto(url);
      await ap.addScriptTag({ content: FRAME_SRC });
      const env = envOf(pair.alg);
      await ap.evaluate(async env => {
        const { useAppStore } = await import('/src/state/store.ts');
        localStorage.clear(); useAppStore.getState().loadEnvelope(env);
      }, env);
      await ap.locator('.geo3d-canvas canvas').waitFor();
      const slider = ap.locator('.geo3d-scrub input[type=range]');
      await slider.waitFor();
      const max = await slider.getAttribute('max');
      await slider.fill(max);
      // Learner action "Hiển thị → Hình phụ": show finished auxiliary planes/lines (the HTML always shows (α) at step 4).
      let hinhPhu = false;
      const menu = ap.getByRole('button', { name: 'Hiển thị' });
      if (await menu.count()) {
        await menu.first().click();
        const item = ap.getByText('Hình phụ', { exact: true });
        if (await item.count()) { await item.first().click(); hinhPhu = true; }
        await ap.keyboard.press('Escape');
      }
      await ap.waitForTimeout(1200);
      const names = Object.fromEntries(env.scene3d.objects.filter(o => o.type === 'point3').map(o => [o.id, norm(o.notation ?? o.label)]));
      const a = await ap.evaluate(({ names, local, apex }) => {
        const scene = window.__scenes.at(-1), cam = window.__lastCam;
        const pts = {};
        scene.traverse(n => {
          const m = /^point:(.+)$/.exec(n.name ?? '');
          if (!m || !names[m[1]] || pts[names[m[1]]]) return;
          const box = new cam.position.constructor(); // Vector3
          const b = { min: [Infinity, Infinity, Infinity], max: [-Infinity, -Infinity, -Infinity] };
          n.updateMatrixWorld(true);
          n.traverse(c => { if (!c.isMesh || !c.geometry) return; c.geometry.computeBoundingBox(); const bb = c.geometry.boundingBox.clone().applyMatrix4(c.matrixWorld);
            ['x', 'y', 'z'].forEach((k, i) => { b.min[i] = Math.min(b.min[i], bb.min[k]); b.max[i] = Math.max(b.max[i], bb.max[k]); }); });
          if (Number.isFinite(b.min[0])) pts[names[m[1]]] = b.min.map((v, i) => (v + b.max[i]) / 2);
          void box;
        });
        if (!pts.A || !pts.B || !pts.C || !pts[apex]) return { error: 'labels missing', have: Object.keys(pts) };
        const f = window.__frame(pts.A, pts.B, pts.C, pts[apex]);
        const d = [0, 1, 2].map(i => local[0] * f.x[i] + local[1] * f.y[i] + local[2] * f.z[i]);
        const ids = Object.values(pts);
        const c = [0, 1, 2].map(i => ids.reduce((s, p) => s + p[i], 0) / ids.length);
        const dist = Math.hypot(...[0, 1, 2].map(i => cam.position.getComponent(i) - c[i]));
        const before = cam.position.toArray();
        cam.position.set(c[0] + d[0] * dist, c[1] + d[1] * dist, c[2] + d[2] * dist);
        cam.lookAt(c[0], c[1], c[2]);
        return { labels: Object.keys(pts), before, after: cam.position.toArray(), centroid: c, dir: d,
          elevation_deg: +(Math.asin(d[2]) * 180 / Math.PI).toFixed(2) };
      }, { names, local, apex: pair.apex });
      await ap.waitForTimeout(900);
      const fat = await ap.evaluate(() => window.__geo3d_fat_line_summary ?? null);
      const afile = `${label}-ALG-${pair.alg[1]}-${viewport.width}.png`;
      await ap.locator('.geo3d-canvas').scrollIntoViewIfNeeded();
      const abuf = await ap.locator('.geo3d-canvas').screenshot({ path: join(out, afile) });
      receipt.rows.push({ pair: pair.what, viewport: `${viewport.width}x${viewport.height}`,
        html: { shape: pair.html, file: hfile, sha256: createHash('sha256').update(hbuf).digest('hex'), camera: h.cam, target: h.target,
          spherical: h.spherical, fov: h.fov, shell_opacity: h.opacity, step: 4, frame_local_view_dir: local },
        algosim: { case: pair.alg[1], auxiliary_shown: hinhPhu, file: afile, sha256: createHash('sha256').update(abuf).digest('hex'), step: Number(max), camera: a, fat_lines: fat } });
      console.log(pair.html, viewport.width, 'labels', JSON.stringify(a.labels ?? a), 'elev', a.elevation_deg);
      await actx.close();
      } catch (e) {
        const msg = String(e.message).split('\n')[0];
        receipt.errors.push({ pair: pair.html, viewport: viewport.width, stage, message: msg });
        console.log('FAIL', pair.html, viewport.width, stage, msg);
      }
    }
  }
} finally {
  await browser.close();
  writeFileSync(join(out, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n');
}
console.log('ERRORS', receipt.errors.length);
