/**
 * Refusal screens of the 25 Adapter /4 refusal fixtures, offline (0 model calls, no backend).
 *
 * Each refusal is loaded right AFTER a served scene (`PARA-0`) on the same page, so "canvas detached" proves the old
 * scene was removed, not that none was ever drawn. Injection is the Session 5 harness path
 * (`frontend/scripts/check-adapter4-browser.mjs`): `docPhanHoiHybrid` → `loadUnsupported`. One screenshot per refusal
 * code per viewport; every refusal is checked by machine.
 *
 * Usage (repo root, Vite dev on :3115 serving this checkout): node <this file> <fresh-output-dir>
 */
import { readFileSync, mkdirSync, existsSync, writeFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const root = resolve(import.meta.dirname, '../../../../..');
const { chromium } = await import(pathToFileURL(join(root, 'frontend/node_modules/playwright/index.mjs')).href);
const source = join(root, 'docs/evaluation/geometry/runs/hybrid-offline-consumer/results/fixtures.json');
const bytes = readFileSync(source), data = JSON.parse(bytes);
const sha = b => createHash('sha256').update(b).digest('hex');
const canonical = x => x === null || typeof x !== 'object' ? JSON.stringify(x)
  : Array.isArray(x) ? `[${x.map(canonical).join(',')}]`
    : `{${Object.keys(x).sort().map(k => `${JSON.stringify(k)}:${canonical(x[k])}`).join(',')}}`;
const withEnvelope = row => {
  if (!row.reference) return row;
  const bundle = readFileSync(join(root, row.reference.file));
  if (sha(bundle) !== data.original_fixture_sha256) throw Error('historical fixture hash mismatch');
  const envelope = JSON.parse(bundle).fixtures[row.reference.index].envelope;
  if (sha(canonical(envelope)) !== row.reference.envelope_sha256) throw Error('fresh envelope mismatch');
  return { ...row, envelope };
};
const fixtures = data.fixtures.map(withEnvelope);
const served = fixtures.find(f => f.id === 'PARA-0');
const refusals = fixtures.filter(f => f.route_d.status !== 'SERVED');
const out = resolve(process.argv[2] ?? '');
if (!process.argv[2] || existsSync(out)) throw Error('fresh output directory required');
const treeClean = execFileSync('git', ['status', '--porcelain'], { cwd: root, encoding: 'utf8' }).trim() === '';
const head = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim();
mkdirSync(out, { recursive: true });
const url = 'http://127.0.0.1:3115';
const assert = (value, message) => { if (!value) throw Error(message); };
const load = (page, fx) => page.evaluate(async fx => {
  const a = await import('/src/simulations/domains/geometry/hybrid-preview-adapter.ts');
  const { useAppStore } = await import('/src/state/store.ts');
  const r = a.docPhanHoiHybrid(fx);
  if (!r.ok) return r;
  if (r.envelope.status === 'ok') useAppStore.getState().loadEnvelope(r.envelope);
  else useAppStore.getState().loadUnsupported(r.envelope);
  return { ok: true, active: !!useAppStore.getState().active, error: useAppStore.getState().analysisError };
}, fx);

const rows = [], errors = [], forbidden = [], shot = new Set();
const browser = await chromium.launch({ channel: 'chrome', headless: true,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
let code = 0;
try {
  for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    const context = await browser.newContext({ viewport });
    await context.route('**/*', route => {
      const u = new URL(route.request().url());
      if (u.origin === url && u.pathname === '/api/health') return route.fulfill({ json: { status: 'ok', allow_live_ai: false } });
      if (u.origin === url && u.pathname === '/api/auth/me') return route.fulfill({ json: null });
      if (u.origin === url && !u.pathname.startsWith('/api/')) return route.continue();
      forbidden.push({ origin: u.origin, path: u.pathname });
      return route.abort();
    });
    const page = await context.newPage();
    page.setDefaultTimeout(15000);
    page.on('pageerror', e => errors.push({ type: 'exception', message: e.message }));
    page.on('console', m => { if (m.type() === 'error') errors.push({ type: 'console', message: m.text() }); });
    for (const fx of refusals) {
      await page.goto(url);
      const before = await load(page, served);
      assert(before.ok && before.active, `${fx.id}: served precondition failed`);
      await page.locator('.geo3d-canvas canvas').waitFor();
      const loaded = await load(page, fx);
      assert(loaded.ok && !loaded.error, `${fx.id}: consumer ${JSON.stringify(loaded)}`);
      await page.locator('canvas').waitFor({ state: 'detached' });
      assert(!loaded.active, `${fx.id}: refusal left active simulation`);
      const text = await page.locator('body').innerText();
      const row = { id: fx.id, code: fx.route_d.refusal.code, viewport,
        canvas_after: await page.locator('canvas').count(),
        learner_reason_shown: text.includes(fx.envelope.learner_reason),
        code_leaked: text.includes(fx.route_d.refusal.code),
        internal_name_leaked: /\b[\p{L}\p{N}]+_[\p{L}\p{N}_]+\b|::/u.test(text),
        served_title_left: text.includes('Thiết diện MNPQ'),
        overflow: await page.evaluate(() => document.documentElement.scrollWidth) > viewport.width + 1 };
      assert(row.canvas_after === 0 && row.learner_reason_shown && !row.code_leaked && !row.internal_name_leaked
        && !row.served_title_left && !row.overflow, `${fx.id} ${viewport.width}: ${JSON.stringify(row)}`);
      const key = `${row.code}-${viewport.width}`;
      if (!shot.has(key)) {
        shot.add(key);
        const file = `${fx.id}-${viewport.width}.png`, png = await page.screenshot();
        writeFileSync(join(out, file), png); row.image = { file, sha256: sha(png) };
      }
      rows.push(row);
      console.log(`${fx.id} ${viewport.width} PASS`);
    }
    await context.close();
  }
  if (errors.length || forbidden.length) code = 1;
} catch (e) {
  code = 1; errors.push({ type: 'harness', message: String(e?.message ?? e).slice(0, 300) });
} finally {
  await browser.close();
  writeFileSync(join(out, 'receipt.json'), JSON.stringify({
    status: code ? 'REFUSAL_SCREEN_CHECK_FAIL' : 'REFUSAL_SCREEN_CHECK_PASS', source_commit: head, tree_clean: treeClean,
    fixtures_sha256: sha(bytes), harness_sha256: sha(readFileSync(import.meta.filename)), provider_calls: 0,
    browser: 'Chrome headless / SwiftShader', precondition: 'served PARA-0 canvas present before every refusal',
    human_visual_review: 'PENDING', refusals: refusals.length, rows: rows.length, errors, forbidden, results: rows,
  }, null, 1) + '\n');
}
process.exit(code);
