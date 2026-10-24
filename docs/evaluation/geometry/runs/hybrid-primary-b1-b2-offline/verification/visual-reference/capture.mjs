// Owner visual-reference comparison. Loads ACTUAL B1/B2 service wrappers into the unmodified product (dev server
// on the candidate worktree) and screenshots each scene. "after"/"shell-*" variants override material colors and
// opacities at runtime only — no product file is changed. Usage: node capture.mjs <worktree> <outDir>
import { createRequire } from 'node:module';
import { readFileSync, mkdirSync, existsSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';

const wt = resolve(process.argv[2]);
const out = resolve(process.argv[3]);
if (existsSync(out)) throw Error('fresh output directory required');
const { chromium } = createRequire(join(wt, 'frontend/package.json'))('playwright');
const fixturesPath = join(wt, 'docs/evaluation/geometry/runs/hybrid-primary-b1-b2-offline/results/offline/fixtures.json');
const bytes = readFileSync(fixturesPath);
const all = JSON.parse(bytes).fixtures;
const CASES = [
  ['CORPUS-DEV01-construct', 'pyramid S.ABCD, quadrilateral section'],
  ['CORPUS-DEV03-construct', 'pyramid S.ABC, triangular section'],
  ['CORPUS-DEV10-prism-area', 'right prism with section'],
  ['PARA-0', 'section with DERIVED_FRESH vertices + derived pyramid'],
  ['PERP-square-third', 'perpendicular/altitude with hidden edges'],
  ['NEG-missing-height', 'refusal'],
];
const VARIANTS = ['before', 'after', 'shell-0.04', 'shell-0.12', 'shell-0.20', 'shell-0.30'];
const commit = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: wt, encoding: 'utf8' }).trim();
const treeClean = execFileSync('git', ['status', '--porcelain'], { cwd: wt, encoding: 'utf8' }).trim() === '';
mkdirSync(out, { recursive: true });
const url = 'http://127.0.0.1:3116';
const receipt = { schema: 'scene3d-visual-reference-capture/1', commit, tree_clean: treeClean,
  fixtures_file: 'docs/evaluation/geometry/runs/hybrid-primary-b1-b2-offline/results/offline/fixtures.json',
  fixtures_sha256: createHash('sha256').update(bytes).digest('hex'),
  product_code_modified: false, override_mode: 'RUNTIME_MATERIAL_OVERRIDE_ONLY', rows: [], errors: [], forbidden: [] };

// Runs in page. Finds the live product scene via three's devtools hook and applies a variant.
function applyVariant(variant) {
  const scene = window.__scenes?.at(-1);
  if (!scene) return { error: 'no scene' };
  const n = { shell: 0, sectionFill: 0, sectionLine: 0, plane: 0, derived: 0 };
  const shellTarget = variant === 'after' ? 0.12 : variant.startsWith('shell-') ? Number(variant.slice(6)) : null;
  const recolor = variant === 'after';
  scene.traverse(o => {
    const mats = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : [];
    for (const m of mats) {
      if (!m.color || m.colorWrite === false) continue;
      const hex = m.color.getHex();
      if (o.isMesh && hex === 0x647a96 && shellTarget !== null) {
        m.opacity = shellTarget; if (recolor) m.color.setHex(0x7c8b9e); n.shell++;
      } else if (!recolor) continue;
      else if (o.isMesh && o.name.startsWith('section_fill:')) { m.color.setHex(0xc85a32); m.opacity = 0.27; n.sectionFill++; }
      else if (hex === 0xf59e0b) { m.color.setHex(0xc85a32); n.sectionLine++; }
      else if (hex === 0x7c3aed) { m.color.setHex(0x6d28d9); n.plane++; }
      else if (hex === 0xdc2626) { m.color.setHex(0xc85a32); n.derived++; }
    }
    const loop = o.userData?.nonCanonicalLoop;
    if (recolor && loop) {
      if (loop.color === 0xf59e0b) loop.color = 0xc85a32;
      if (loop.color === 0x7c3aed) loop.color = 0x6d28d9;
    }
  });
  if (recolor) document.querySelector('.geo3d-canvas')?.style.setProperty('background', 'radial-gradient(circle at 50% 44%, #FFFFFF 0%, #F8F6F1 68%, #EFECE4 100%)');
  return n;
}

const browser = await chromium.launch({ channel: 'chrome', headless: true,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
try {
  for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    for (const [id, what] of CASES) {
      const fx = all.find(f => f.id === id);
      for (const variant of VARIANTS) {
        if (fx.route_d.status !== 'SERVED' && variant !== 'before') continue;
        const context = await browser.newContext({ viewport, deviceScaleFactor: 1 });
        await context.addInitScript(() => {
          window.__scenes = []; window.__cams = [];
          const hub = new EventTarget();
          hub.addEventListener('observe', e => {
            const d = e.detail;
            if (d?.isScene) window.__scenes.push(d);
            if (d?.isWebGLRenderer) {
              const r = d.render.bind(d);
              d.render = (s, c) => { window.__lastCam = c; return r(s, c); };
            }
          });
          window.__THREE_DEVTOOLS__ = hub;
        });
        await context.route('**/*', route => {
          const u = new URL(route.request().url());
          if (u.origin === url && u.pathname === '/api/health') return route.fulfill({ json: { status: 'ok', allow_live_ai: false } });
          if (u.origin === url && u.pathname === '/api/auth/me') return route.fulfill({ json: null });
          if (u.origin === url && !u.pathname.startsWith('/api/')) return route.continue();
          receipt.forbidden.push({ origin: u.origin, path: u.pathname });
          return route.abort();
        });
        const page = await context.newPage();
        page.setDefaultTimeout(20000);
        page.on('pageerror', e => receipt.errors.push({ id, variant, type: 'exception', message: e.message }));
        page.on('console', m => { if (m.type() === 'error') receipt.errors.push({ id, variant, type: 'console', message: m.text() }); });
        await page.goto(url);
        const loaded = await page.evaluate(async fx => {
          const a = await import('/src/simulations/domains/geometry/hybrid-preview-adapter.ts');
          const { useAppStore } = await import('/src/state/store.ts');
          const r = a.docPhanHoiHybrid(fx);
          if (!r.ok) return r;
          localStorage.clear();
          if (r.envelope.status === 'ok') useAppStore.getState().loadEnvelope(r.envelope);
          else useAppStore.getState().loadUnsupported(r.envelope);
          return { ok: true, active: !!useAppStore.getState().active };
        }, fx);
        const row = { id, what, viewport: `${viewport.width}x${viewport.height}`, variant, status: fx.route_d.status, loaded };
        if (fx.route_d.status === 'SERVED') {
          await page.locator('.geo3d-canvas canvas').waitFor();
          const slider = page.locator('.geo3d-scrub input[type=range]');
          await slider.waitFor();
          const max = await slider.getAttribute('max');
          await slider.fill(max);
          row.step = Number(max);
          await page.waitForTimeout(900);
          row.overrides = await page.evaluate(applyVariant, variant);
          await page.waitForTimeout(400);
          row.camera = await page.evaluate(() => {
            const c = window.__lastCam; if (!c) return null;
            const r = v => Number(v.toFixed(4));
            return { position: c.position.toArray().map(r), quaternion: c.quaternion.toArray().map(r), fov: c.fov, zoom: c.zoom, type: c.type };
          });
          await page.locator('.geo3d-canvas').scrollIntoViewIfNeeded();
          row.canvas_png = `${id}-${viewport.width}-${variant}-canvas.png`;
          const buf = await page.locator('.geo3d-canvas').screenshot({ path: join(out, row.canvas_png) });
          row.canvas_sha256 = createHash('sha256').update(buf).digest('hex');
        } else {
          await page.waitForTimeout(600);
          row.refusal_visible = !(await page.locator('canvas').count());
        }
        if (variant === 'before' || variant === 'after') {
          row.page_png = `${id}-${viewport.width}-${variant}-page.png`;
          await page.screenshot({ path: join(out, row.page_png) });
        }
        receipt.rows.push(row);
        console.log(id, row.viewport, variant, JSON.stringify(row.overrides ?? row.refusal_visible));
        await context.close();
      }
    }
  }
} finally {
  await browser.close();
  writeFileSync(join(out, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n');
}
console.log('ERRORS', receipt.errors.length, 'FORBIDDEN', receipt.forbidden.length);
