// Real Chromium on the production build + loopback measured_app (local-first, ALLOW_LIVE_AI=0).
// Scenario: /api/input/prepare is answered by a FIXTURE (OCR split "ABCD.A'B'C'D'" into "4BCD-" + "A'B'C'D'"), because
// no real image reproduces that split on demand; everything after it is real: the span review UI, the extend button,
// the edit, keyboard confirmation, /api/analyze on the real backend, the Scene3D canvas.
// Checks: (1) extend merges the two spans into one editable group, (2) restore splits it back, (3) the corrected text
// is served and builds a scene, (4) OBSERVED only: whether the served special angle (cos² = 1/4) appears on the page.
// Usage (worktree root): node <this> <frontend/dist> <out.json> [backendPort]
import { chromium } from 'file:///D:/Documents/projects/algo-sim/frontend/node_modules/playwright/index.mjs';
import { createServer, request } from 'node:http';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve, join, extname } from 'node:path';

const [dist, out] = process.argv.slice(2, 4).map(p => resolve(p));
const backendPort = Number(process.argv[4] ?? 8767);
const SPLIT = "Cho hình lập phương 4BCD- A'B'C'D' có cạnh bằng a. Tính góc giữa hai đường thẳng AC và A'D.";
const FIXED = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. Tính góc giữa hai đường thẳng AC và A'D.";
const cp = (s, sub) => Array.from(s.slice(0, s.indexOf(sub))).length;
const fixture = {
  schema: 'unified-input-prepare/1', status: 'needs_confirmation', source_kind: 'image', problem_text: SPLIT,
  learner_message: 'Máy đã đọc đề từ ảnh; còn 2 chỗ chưa chắc chắn được đánh dấu.', reason_code: 'LOCAL_OCR_REVIEW_REQUIRED', flag_messages: [],
  uncertain_tokens: [
    { token: '4BCD-', alternatives: [], location: 'dòng 1', reason: 'Tên khối đọc chưa chắc', kind: 'math', span_id: 'spA', span_start: cp(SPLIT, '4BCD-'), span_end: cp(SPLIT, '4BCD-') + 5, source: 'local_ocr' },
    { token: "A'B'C'D'", alternatives: [], location: 'dòng 1', reason: 'Dấu phẩy trên đọc chưa chắc', kind: 'math', span_id: 'spB', span_start: cp(SPLIT, "A'B'C'D'"), span_end: cp(SPLIT, "A'B'C'D'") + 8, source: 'local_ocr' },
  ],
  missing_regions: [], candidates: [], provenance: { input_route: 'LOCAL_OCR_NEEDS_CONFIRMATION' },
  metrics: { vlm_calls: 0, used_vlm: false, raw_input_bytes: 1, vlm_payload_bytes: 0, uncropped_baseline_bytes: 1, processing_ms: 1 },
};

const server = createServer((req, res) => {
  const path = new URL(req.url, 'http://localhost').pathname;
  if (path.startsWith('/api/')) {
    const proxy = request({ host: '127.0.0.1', port: backendPort, path: req.url, method: req.method, headers: req.headers }, up => {
      res.writeHead(up.statusCode, up.headers); up.pipe(res);
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
// A 1x1 PNG: the upload only has to reach the (fixture) prepare call.
const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
try {
  for (const [width, height] of [[1440, 900], [390, 844]]) {
    const context = await browser.newContext({ viewport: { width, height } });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.name));
    await page.route('**/api/input/prepare', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(fixture) }));
    await page.goto(`http://127.0.0.1:${server.address().port}`, { waitUntil: 'networkidle' });
    await page.locator('#home-file-input').setInputFiles({ name: 'problem.png', mimeType: 'image/png', buffer: png });
    await page.click('#btn-composer-send');
    await page.waitForSelector('#photo-span-review', { timeout: 60000 });
    const spansBefore = await page.locator('[data-span-input]').count();
    const extendShown = await page.locator('[data-span-extend="spA"]').count() === 1;
    await page.click('[data-span-extend="spA"]');
    const spansAfterExtend = await page.locator('[data-span-input]').count();
    const merged = await page.inputValue('[data-span-input="spA"]');
    await page.click('[data-span-restore="spA"]');
    const spansAfterRestore = await page.locator('[data-span-input]').count();
    const restoredDraft = await page.inputValue('#photo-problem-text');
    await page.click('[data-span-extend="spA"]');
    await page.fill('[data-span-input="spA"]', "ABCD.A'B'C'D'");
    const draft = await page.inputValue('#photo-problem-text');
    for (const b of await page.locator('.photo-span-ok').all()) { await b.focus(); await page.keyboard.press('Enter'); }
    await page.check('#chk-confirm-extracted-text');
    const solved = page.waitForResponse(r => new URL(r.url()).pathname === '/api/analyze', { timeout: 120000 });
    await page.click('#btn-confirm-extracted-build');
    const analysis = await (await solved).json();
    let canvas = false;
    try {
      await page.waitForFunction(() => { const c = document.querySelector('#stage-3d-box canvas'); return c && c.width > 0 && c.height > 0; }, null, { timeout: 30000 });
      canvas = true;
    } catch { canvas = false; }
    // Observation only: the product workspace hides the final answer (simulation first) and does not mount the
    // Scene3DExplorer analysis panel, so whether the served angle appears anywhere on the page is recorded, not required.
    const text = await page.evaluate(() => document.body.textContent ?? "");
    const mathAnalysisPanelMounted = await page.locator("button[data-mo-bang=\"phan-tich\"], [data-math-analysis-panel]").count() > 0;
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    const row = {
      viewport: `${width}x${height}`, prepare: 'FIXTURE_SPLIT_SPANS', spansBefore, extendShown, spansAfterExtend, merged, spansAfterRestore,
      restoreGivesOriginalText: restoredDraft === SPLIT, correctedDraftIsExpected: draft === FIXED,
      analyzeStatus: analysis.route_d?.status, servedAnswers: analysis.route_d?.answers ?? null, canvas, mathAnalysisPanelMounted,
      servedAngleTextOnPage: text.includes('60°') || text.includes('cos²'), horizontalOverflowPx: overflow, errors,
      angleTextSeen: [...new Set(text.match(/.{0,40}(?:cos²|°).{0,40}/g) ?? [])].slice(0, 8),
    };
    row.pass = spansBefore === 2 && extendShown && spansAfterExtend === 1 && merged === "4BCD- A'B'C'D'" && spansAfterRestore === 2
      && row.restoreGivesOriginalText && row.correctedDraftIsExpected && row.analyzeStatus === 'SERVED' && canvas
      && errors.length === 0 && overflow <= 0;
    rows.push(row);
    console.log(JSON.stringify(row));
    await context.close();
  }
} finally {
  writeFileSync(out, JSON.stringify({ browser: browser.version(), category: 'AUTOMATED_BROWSER_NOT_HUMAN_STUDY',
    evidence_kind: 'FIXTURE prepare response + real UI, real /api/analyze (local-first, no provider call)', backendPort,
    rows, passed: rows.filter(r => r.pass).length, total: rows.length }, null, 2) + '\n');
  await browser.close(); server.close();
}
if (!rows.every(r => r.pass)) process.exitCode = 1;
