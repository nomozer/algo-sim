// AlgoSim screenshots of real product envelopes (offline samples + B1/B2 service fixtures), unmodified page code.
// Usage: node capture-algosim.mjs <worktree> <b1b2-fixtures.json> <outDir> <label>
import { createRequire } from 'node:module';
import { readFileSync, mkdirSync, existsSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';

const wt = resolve(process.argv[2]);
const fxPath = resolve(process.argv[3]);
const out = resolve(process.argv[4]);
const label = process.argv[5] ?? 'algosim';
if (existsSync(out)) throw Error('fresh output directory required');
const { chromium } = createRequire(join(wt, 'frontend/package.json'))('playwright');
const rawSamples = JSON.parse(readFileSync(join(wt, 'frontend/src/data/geometry-samples.json'), 'utf8'));
const samples = Array.isArray(rawSamples) ? rawSamples : (rawSamples.samples ?? Object.values(rawSamples));
const fxBytes = readFileSync(fxPath);
const fixtures = JSON.parse(fxBytes).fixtures;
const CASES = [
  ['sample', 'thiet-dien-chop', 'S.ABCD + section (offline sample)'],
  ['sample', 'mp-vuong-goc-duong', 'S.ABCD + perpendicular plane (offline sample)'],
  ['fixture', 'CORPUS-DEV01-construct', 'S.ABCD quadrilateral section (B1/B2 service)'],
  ['fixture', 'CORPUS-DEV03-construct', 'S.ABC triangular section, SA ⊥ base (B1/B2 service)'],
  ['fixture', 'CORPUS-DEV10-prism-area', 'right prism + section (B1/B2 service)'],
  ['fixture', 'PERP-square-third', 'S.ABCD SA ⊥ base, right-angle marks (B1/B2 service)'],
];
const envOf = ([kind, id]) => kind === 'sample' ? samples.find(s => s.id === id).envelope : fixtures.find(f => f.id === id).envelope;
const git = (...a) => execFileSync('git', a, { cwd: wt, encoding: 'utf8' }).trim();
mkdirSync(out, { recursive: true });
const url = 'http://127.0.0.1:3117';
const receipt = { schema: 'algosim-visual-capture/1', label, commit: git('rev-parse', 'HEAD'),
  tracked_changes: git('status', '--porcelain', '--untracked-files=no'), fixtures_sha256: createHash('sha256').update(fxBytes).digest('hex'),
  rows: [], errors: [], forbidden: [] };
const browser = await chromium.launch({ channel: 'chrome', headless: true,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
try {
  for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    for (const c of CASES) {
      const ctx = await browser.newContext({ viewport, deviceScaleFactor: 1 });
      await ctx.addInitScript(() => {
        const hub = new EventTarget();
        hub.addEventListener('observe', e => {
          const d = e.detail;
          if (d?.isWebGLRenderer) { const r = d.render.bind(d); d.render = (s, cam) => { window.__lastCam = cam; return r(s, cam); }; }
        });
        window.__THREE_DEVTOOLS__ = hub;
      });
      await ctx.route('**/*', route => {
        const u = new URL(route.request().url());
        if (u.origin === url && u.pathname === '/api/health') return route.fulfill({ json: { status: 'ok', allow_live_ai: false } });
        if (u.origin === url && u.pathname === '/api/auth/me') return route.fulfill({ json: null });
        if (u.origin === url && !u.pathname.startsWith('/api/')) return route.continue();
        receipt.forbidden.push(u.pathname); return route.abort();
      });
      const page = await ctx.newPage();
      page.setDefaultTimeout(20000);
      page.on('pageerror', e => receipt.errors.push({ id: c[1], message: e.message }));
      page.on('console', m => { if (m.type() === 'error') receipt.errors.push({ id: c[1], console: m.text() }); });
      await page.goto(url);
      const loaded = await page.evaluate(async env => {
        const { useAppStore } = await import('/src/state/store.ts');
        localStorage.clear();
        useAppStore.getState().loadEnvelope(env);
        return { active: !!useAppStore.getState().active, error: useAppStore.getState().analysisError ?? null };
      }, envOf(c));
      const row = { kind: c[0], id: c[1], what: c[2], viewport: `${viewport.width}x${viewport.height}`, loaded };
      await page.locator('.geo3d-canvas canvas').waitFor();
      const slider = page.locator('.geo3d-scrub input[type=range]');
      await slider.waitFor();
      const max = await slider.getAttribute('max');
      await slider.fill(max);
      row.step = Number(max);
      await page.waitForTimeout(1200);
      row.camera = await page.evaluate(() => {
        const cam = window.__lastCam; if (!cam) return null;
        const r = v => Number(v.toFixed(4));
        return { position: cam.position.toArray().map(r), fov: cam.fov, up: cam.up.toArray().map(r) };
      });
      row.fat_lines = await page.evaluate(() => window.__geo3d_fat_line_summary ?? null);
      row.canvas_css = await page.evaluate(() => { const r = document.querySelector('.geo3d-canvas').getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; });
      await page.locator('.geo3d-canvas').scrollIntoViewIfNeeded();
      row.file = `${label}-${c[1]}-${viewport.width}.png`;
      const buf = await page.locator('.geo3d-canvas').screenshot({ path: join(out, row.file) });
      row.sha256 = createHash('sha256').update(buf).digest('hex');
      receipt.rows.push(row);
      console.log(c[1], row.viewport, 'step', row.step, 'fat', JSON.stringify(row.fat_lines), 'err', receipt.errors.length);
      await ctx.close();
    }
  }
} finally {
  await browser.close();
  writeFileSync(join(out, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n');
}
console.log('ERRORS', receipt.errors.length, 'FORBIDDEN', receipt.forbidden.length);
