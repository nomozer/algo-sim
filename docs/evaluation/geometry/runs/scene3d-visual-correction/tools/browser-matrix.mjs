import { createRequire } from 'node:module';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
const { chromium } = createRequire(resolve('frontend/package.json'))('playwright');
const arg = (key, fallback) => process.argv.includes(key) ? process.argv[process.argv.indexOf(key) + 1] : fallback;
const url = arg('--url', 'http://127.0.0.1:3156'), phase = arg('--phase', 'after');
const out = resolve(arg('--out', `docs/evaluation/geometry/runs/scene3d-visual-correction/verification/${phase}`));
if (existsSync(out)) throw Error('Fresh output required');
mkdirSync(out, { recursive: true });
const read = file => JSON.parse(readFileSync(file, 'utf8'));
const samples = read('frontend/src/data/geometry-samples.json').samples;
const fixtures = [];
if (phase !== 'before') for (const family of ['triangular_pyramid', 'triangular_prism', 'rectangular_pyramid', 'cuboid', 'regular_square_pyramid', 'regular_triangular_pyramid', 'cross_section']) {
  const file = `docs/evaluation/geometry/runs/visual-closure-hybrid-readiness/visual/final-inputs/fixtures/${family}_positive.json`;
  fixtures.push({ id: family, envelope: read(file).envelope, source: file, scope: 'OFFLINE_BACKEND_ENVELOPE_NOT_LIVE_EXTRACTION' });
}
for (const id of phase === 'before' ? ['cau-cat-mat-phang', 'tru-truc-xien', 'non-duong-sinh']
  : ['cau-cat-mat-phang', 'tru-truc-xien', 'tru-thiet-dien-tron', 'non-duong-sinh', 'non-thiet-dien-truc']) {
  fixtures.push({ id, envelope: samples.find(s => s.id === id).envelope, source: 'frontend/src/data/geometry-samples.json', scope: 'LEGACY_OFFLINE_SAMPLE_NOT_CANONICAL_HYBRID' });
}
if (phase !== 'before') {
  const source = 'docs/evaluation/geometry/runs/geometric-visual-correctness-framing/demos/audit_scenes.json';
  for (const row of read(source).filter(r => /oxyz|oblique|xien|coordinate|overlap/i.test(r.id))) fixtures.push({ id: row.id,
    envelope: { ...samples[0].envelope, scene3d: row.scene }, source, scope: 'DISPLAY_ONLY_AUTHORED_SCENE' });
}
const sha = b => createHash('sha256').update(b).digest('hex');
const receipt = { phase, url, source_head: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
  baseline_source: phase === 'before' ? 'fe5f40b7 original product modules via Vite load plugin' : null,
  provider_calls: 0, human_visual_review: 'NOT_APPROVED', rows: [], errors: [], forbidden: [] };
const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
try {
  for (const width of [1440, 390]) {
    const context = await browser.newContext({ viewport: { width, height: width === 390 ? 844 : 900 }, deviceScaleFactor: 1 });
    await context.route('**/*', route => {
      const u = new URL(route.request().url());
      if (u.origin !== url) { receipt.forbidden.push(u.origin); return route.abort(); }
      if (u.pathname.startsWith('/api/')) return route.fulfill({ json: u.pathname === '/api/health' ? { status: 'ok', allow_live_ai: false } : null });
      return route.continue();
    });
    const page = await context.newPage();
    page.setDefaultTimeout(15000);
    page.on('pageerror', e => receipt.errors.push(e.message.split('\n')[0]));
    for (const fixture of fixtures) {
      const row = { id: fixture.id, width, source: fixture.source, scope: fixture.scope, frames: [], checks: {} };
      receipt.rows.push(row);
      try {
        await page.goto(url);
        await page.evaluate(async envelope => { const { useAppStore } = await import('/src/state/store.ts'); useAppStore.getState().loadEnvelope(envelope); }, fixture.envelope);
        const canvas = page.locator('.geo3d-canvas canvas');
        await canvas.waitFor();
        await page.locator('.geo3d-scrub input').evaluate(el => {
          Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, el.max);
          el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true }));
        });
        const original = await page.evaluate(() => JSON.stringify(window.__ALGO_SIM_STORE__.getState().active.envelope.scene3d));
        const capture = async state => {
          await page.mouse.move(0, 0);
          await page.waitForFunction(() => { const s = JSON.stringify(window.__geo3d_camera_snapshot);
            window.__matrixStable = s === window.__matrixLast ? (window.__matrixStable ?? 0) + 1 : 0;
            window.__matrixLast = s; return window.__matrixStable >= 4; }, null, { polling: 'raf', timeout: 20000 });
          const metadata = await page.evaluate(() => ({ camera: window.__geo3d_camera_snapshot,
            target: window.__geo3d_camera_target, selected: window.__geo3d_selected_id,
            visible: window.__geo3d_visible_edge_ids, hidden: window.__geo3d_hidden_edge_ids,
            mixed: window.__geo3d_mixed_edge_ids, duplicates: window.__geo3d_duplicate_visual_owner_ids,
            labels: [...document.querySelectorAll('.geo3d-label,.geo3d-nhan-mp')].filter(el => getComputedStyle(el).visibility !== 'hidden').map(el => ({ text: el.textContent, id: el.dataset.id ?? el.dataset.planeId })),
            final_canvas_labels: [...document.querySelectorAll('.geo3d-so-do.la-ket-qua')].map(el => el.textContent),
            overflow: document.documentElement.scrollWidth > innerWidth + 1 }));
          const image = await page.screenshot(), file = `${fixture.id}-${width}-${state}.png`;
          writeFileSync(join(out, file), image);
          row.frames.push({ state, file, sha256: sha(image), ...metadata });
        };
        await capture('default-unselected-mode-a');
        row.checks.mode_a_hidden = !row.frames[0].final_canvas_labels.length;
        const cameras = phase === 'before' ? ['default', 'quarter', 'half', 'high', 'low'] : ['default', 'quarter', 'half', 'high', 'low'];
        for (const camera of cameras) {
          if (camera !== 'default') {
            if (camera === 'high' || camera === 'low') await page.getByRole('button', { name: 'Xem lại toàn hình', exact: true }).click();
            const box = await canvas.boundingBox(), dx = ['quarter', 'half'].includes(camera) ? box.height * 0.25 : 0;
            const dy = camera === 'high' ? box.height * 0.15 : camera === 'low' ? -box.height * 0.15 : 0;
            await page.mouse.move(box.x + box.width * 0.2, box.y + box.height * 0.5); await page.mouse.down();
            await page.mouse.move(box.x + box.width * 0.2 + dx, box.y + box.height * 0.5 + dy, { steps: 16 }); await page.mouse.up();
          }
          await capture(`${camera}-unselected`);
        }
        await page.getByRole('button', { name: 'Xem lại toàn hình', exact: true }).click();
        await page.getByRole('button', { name: 'Phân tích toán học', exact: true }).click();
        const item = page.locator('[data-analysis-item] button').first();
        if (await item.count()) { await item.click(); await capture('default-selected-mode-b'); }
        row.checks.geometry_unchanged = original === await page.evaluate(() => JSON.stringify(window.__ALGO_SIM_STORE__.getState().active.envelope.scene3d));
        row.checks.no_duplicate_edge_owners = row.frames.every(f => !f.duplicates?.length);
        row.checks.no_overflow = row.frames.every(f => !f.overflow);
        row.checks.multiple_cameras = new Set(row.frames.map(f => JSON.stringify(f.camera?.position))).size >= 4;
        row.pass = Object.values(row.checks).every(Boolean);
      } catch (e) { row.failure = e.message.split('\n')[0]; row.pass = false; }
      console.log(`${fixture.id} ${width}: ${row.pass ? 'PASS' : 'GAP'} ${row.failure ?? JSON.stringify(row.checks)}`);
      writeFileSync(join(out, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n');
    }
    await context.close();
  }
} finally { await browser.close(); }
receipt.summary = { rows: receipt.rows.length, passed: receipt.rows.filter(r => r.pass).length, images: receipt.rows.reduce((n, r) => n + r.frames.length, 0) };
writeFileSync(join(out, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n');
console.log(JSON.stringify(receipt.summary));
process.exitCode = receipt.rows.every(r => r.pass) && !receipt.errors.length && !receipt.forbidden.length ? 0 : 1;
