// Real Chromium on the production build + the loopback API: upload in-scope corpus images, confirm every flagged
// span with the keyboard (no edits), build, and wait for the Scene3D canvas. Scripted, not a student.
// Usage (from the worktree root): node <this> <frontend/dist> <out.json> <manifest.json> <backendPort>
import { chromium } from 'file:///D:/Documents/projects/algo-sim/frontend/node_modules/playwright/index.mjs';
import { createServer, request } from 'node:http';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve, join, extname } from 'node:path';

const [dist, out, manifestPath] = process.argv.slice(2, 5).map(p => resolve(p));
const backendPort = Number(process.argv[5] ?? 8767);
const CASES = ['vmmu_r476', 'vmmu_r273', 'vmmu_r492'];  // the corpus items served after confirmation in api_acceptance_*.json
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
const items = CASES.map(id => manifest.items.find(i => i.case_id === id));

const server = createServer((req, res) => {
  const path = new URL(req.url, 'http://localhost').pathname;
  if (path.startsWith('/api/')) {
    const proxy = request({ host: '127.0.0.1', port: backendPort, path: req.url, method: req.method, headers: req.headers }, upstream => {
      res.writeHead(upstream.statusCode, upstream.headers); upstream.pipe(res);
    });
    proxy.on('error', () => { res.writeHead(502); res.end(); });
    req.pipe(proxy); return;
  }
  const file = join(dist, path.includes('.') ? path : 'index.html');
  if (!file.startsWith(dist) || !existsSync(file)) { res.writeHead(404); res.end(); return; }
  res.setHeader('Content-Type', { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml' }[extname(file)] ?? 'application/octet-stream');
  res.end(readFileSync(file));
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const rows = [];
try {
  for (const item of items) {
    for (const [width, height] of [[1440, 900], [390, 844]]) {
      const context = await browser.newContext({ viewport: { width, height } });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', e => errors.push(e.name));
      await page.goto(`http://127.0.0.1:${server.address().port}`, { waitUntil: 'networkidle' });
      const buffer = readFileSync(resolve(item.cache_path));
      // Cached dataset files keep the dataset's .png name but some are JPEG bytes; declare what the bytes are,
      // as a student's own file would be (the server rejects a mismatch with FILE_TYPE_MISMATCH).
      const jpeg = buffer[0] === 0xff && buffer[1] === 0xd8;
      await page.locator('#home-file-input').setInputFiles({ name: jpeg ? 'problem.jpg' : 'problem.png', mimeType: jpeg ? 'image/jpeg' : 'image/png', buffer });
      const prepared = page.waitForResponse(r => new URL(r.url()).pathname === '/api/input/prepare', { timeout: 120000 });
      const started = Date.now();
      await page.click('#btn-composer-send');
      const prep = await (await prepared).json();
      const reviewShownMs = await page.waitForSelector('#photo-span-review', { timeout: 60000 }).then(() => Date.now() - started);
      const crops = await page.locator('.photo-span-crop').evaluateAll(imgs => imgs.map(i => i.complete && i.naturalWidth > 0));
      const buttons = await page.locator('.photo-span-ok').all();
      for (const b of buttons) { await b.focus(); await page.keyboard.press('Enter'); }
      await page.check('#chk-confirm-extracted-text');
      const enabled = !(await page.isDisabled('#btn-confirm-extracted-build'));
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      const solved = page.waitForResponse(r => new URL(r.url()).pathname === '/api/analyze', { timeout: 120000 });
      await page.click('#btn-confirm-extracted-build');
      const analysis = await (await solved).json();
      let canvas = false;
      try {
        await page.waitForFunction(() => { const c = document.querySelector('#stage-3d-box canvas'); return c && c.width > 0 && c.height > 0; }, null, { timeout: 30000 });
        canvas = true;
      } catch { canvas = false; }
      const firstUsableSceneMs = Date.now() - started;
      const answers = await page.evaluate(() => window.__ALGO_SIM_STORE__?.getState().active?.envelope?.hybrid_preview?.answers?.map(a => a.symbolic) ?? null);
      rows.push({ case_id: item.case_id, partition: item.partition, viewport: `${width}x${height}`, category: 'C2_USER_CORRECTED_SIMULATED_CONFIRM_ONLY',
        prepareStatus: prep.status, spansConfirmedByKeyboard: buttons.length, cropsLoaded: crops.every(Boolean) && crops.length > 0,
        buildEnabledAfterConfirm: enabled, horizontalOverflowPx: overflow, analyzeStatus: analysis.route_d?.status, answers, expected: item.expected_answer,
        canvas, uploadToReviewMs: reviewShownMs, uploadToFirstUsableSceneMs: firstUsableSceneMs, studentDwell: 'scripted keyboard, near zero; real reading time NOT_MEASURED',
        errors, pass: prep.status === 'needs_confirmation' && enabled && analysis.route_d?.status === 'SERVED' && canvas && errors.length === 0 && overflow <= 0 });
      console.log(JSON.stringify({ id: item.case_id, viewport: `${width}x${height}`, pass: rows.at(-1).pass, ms: firstUsableSceneMs }));
      await context.close();
    }
  }
} finally {
  writeFileSync(out, JSON.stringify({ browser: browser.version(), category: 'AUTOMATED_BROWSER_NOT_HUMAN_STUDY', backendPort,
    answers_graded_in: 'api_acceptance_*.json (same images, same server)', rows,
    passed: rows.filter(r => r.pass).length, total: rows.length }, null, 2));
  await browser.close(); server.close();
}
if (!rows.every(r => r.pass)) process.exitCode = 1;
