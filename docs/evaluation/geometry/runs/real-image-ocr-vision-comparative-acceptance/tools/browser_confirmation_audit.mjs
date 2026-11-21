// Actual production build + API, scripted corrections; no human usability claim.
import { chromium } from 'file:///D:/Documents/projects/algo-sim/frontend/node_modules/playwright/index.mjs';
import { createServer, request } from 'node:http';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { resolve, join, extname } from 'node:path';
import { createHash } from 'node:crypto';

const dist = resolve(process.argv[2]);
const out = resolve(process.argv[3]);
const cache = resolve(process.argv[4]);
const backendPort = Number(process.argv[5] ?? 8767);
const captures = resolve('.superpowers/offline-logs/comparative-browser');
mkdirSync(captures, { recursive: true });
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
function filePayload(path) {
  const buffer = readFileSync(path);
  const jpeg = buffer[0] === 0xff && buffer[1] === 0xd8;
  return { name: jpeg ? 'problem.jpg' : 'problem.png', mimeType: jpeg ? 'image/jpeg' : 'image/png', buffer };
}
try {
  for (const [width, height, zoom] of [[1440, 900, 1], [1440, 900, 1.1], [390, 844, 1]]) {
    const context = await browser.newContext({ viewport: { width, height } });
    const page = await context.newPage();
    const errors = [];
    const calls = [];
    page.on('pageerror', error => errors.push(error.name));
    page.on('response', response => {
      const path = new URL(response.url()).pathname;
      if (path.startsWith('/api/')) calls.push({ path, status: response.status() });
    });
    const url = `http://127.0.0.1:${server.address().port}`;
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.evaluate(value => { document.documentElement.style.zoom = String(value); }, zoom);
    const image = join(cache, 'vmmu_page_r11_Math_0303_test_059_question_39_page_4_key_B_vqa.png');
    const upload = async () => {
      await page.locator('#home-file-input').setInputFiles(filePayload(image));
      const ready = page.waitForResponse(r => new URL(r.url()).pathname === '/api/input/prepare', { timeout: 120000 });
      await page.click('#btn-composer-send');
      return (await ready).json();
    };
    const started = performance.now();
    const prepared = await upload();
    await page.waitForSelector('#photo-span-review');
    const cropCheck = await page.locator('.photo-span-crop').evaluateAll(images => images.map(img => ({
      loaded: img.complete && img.naturalWidth > 0, source: img.src.startsWith('data:image/'),
    })));
    const spans = await page.locator('[data-span-input]').evaluateAll(elements => elements.map(el => ({ id: el.dataset.spanInput, value: el.value })));
    for (const span of spans) {
      if (span.value.includes("ABC.A'B'C") && !span.value.endsWith("'"))
        await page.locator(`[data-span-input="${span.id}"]`).fill("ABC.A'B'C'");
    }
    for (const button of await page.locator('.photo-span-ok').all()) {
      await button.focus(); await page.keyboard.press('Enter');
    }
    await page.check('#chk-confirm-extracted-text');
    const input = page.locator('[data-span-input]').first();
    const original = await input.inputValue();
    await input.fill(original + ' ');
    const invalidated = !(await page.isChecked('#chk-confirm-extracted-text')) && await page.isDisabled('#btn-confirm-extracted-build');
    await input.fill(original);
    await page.check('#chk-confirm-extracted-text');
    const snapshot = join(captures, `confirmation-${width}-${zoom}.png`);
    await page.screenshot({ path: snapshot, fullPage: true });
    const overflow = await page.evaluate(() => ({ innerWidth, scrollWidth: document.documentElement.scrollWidth }));
    const solved = page.waitForResponse(r => new URL(r.url()).pathname === '/api/analyze', { timeout: 120000 });
    await page.click('#btn-confirm-extracted-build');
    const analysis = await (await solved).json();
    await page.waitForSelector('#stage-3d-box canvas', { timeout: 30000 });
    await page.waitForFunction(() => { const canvas = document.querySelector('#stage-3d-box canvas'); return canvas && canvas.width > 0 && canvas.height > 0; });
    const rendered = await page.evaluate(() => ({
      answers: window.__ALGO_SIM_STORE__?.getState().active?.envelope?.hybrid_preview?.answers?.map(a => a.symbolic),
      canvas: Boolean(document.querySelector('#stage-3d-box canvas')),
    }));
    const firstUsableSceneMs = performance.now() - started;
    rows.push({ width, height, cssZoom: zoom, zoomKind: 'CSS_ZOOM_REFLOW_NOT_BROWSER_CHROME_ZOOM',
      category: 'USER_CORRECTED_SIMULATED', prepareStatus: prepared.status, crops: cropCheck,
      keyboardConfirmation: true, confirmationInvalidatedAfterEdit: invalidated, overflow,
      apiStatus: analysis.route_d?.status, ...rendered, uploadToFirstUsableSceneMs: firstUsableSceneMs,
      screenshotSha256: createHash('sha256').update(readFileSync(snapshot)).digest('hex'),
      screenshotStorage: 'IGNORED_LOCAL_ONLY_SOURCE_IMAGE_LICENSE_LIMITATION', errors, calls,
      pass: invalidated && cropCheck.length > 0 && cropCheck.every(c => c.loaded && c.source)
        && analysis.route_d?.status === 'SERVED' && rendered.answers?.includes('2√3') && errors.length === 0,
    });
    await context.close();
  }
  // Cancellation must prevent analyze and permit a new upload.
  const context = await browser.newContext();
  const page = await context.newPage();
  let analyzeCalls = 0;
  page.on('request', r => { if (new URL(r.url()).pathname === '/api/analyze') analyzeCalls++; });
  await page.goto(`http://127.0.0.1:${server.address().port}`, { waitUntil: 'networkidle' });
  await page.locator('#home-file-input').setInputFiles(filePayload(join(cache, 'vmmu_page_r11_Math_0303_test_059_question_39_page_4_key_B_vqa.png')));
  await page.click('#btn-composer-send');
  await page.waitForSelector('#photo-span-review');
  await page.getByRole('button', { name: 'Huỷ', exact: true }).click();
  const hidden = await page.locator('#photo-span-review').count() === 0;
  rows.push({ id: 'cancel_confirmation', analyzeCalls, pass: hidden && analyzeCalls === 0 });
  await context.close();
} finally {
  writeFileSync(out, JSON.stringify({ browser: browser.version(), category: 'AUTOMATED_BROWSER_HEURISTIC_NOT_HUMAN_STUDY',
    rows, passed: rows.filter(r => r.pass).length, total: rows.length }, null, 2));
  await browser.close(); server.close();
}
console.log(JSON.stringify({ passed: rows.filter(r => r.pass).length, total: rows.length }));
if (!rows.every(r => r.pass)) process.exitCode = 1;
