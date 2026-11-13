// Real Chromium on the production build + loopback measured_app (local-first, ALLOW_LIVE_AI=0, local OCR on): the
// learner uploads a page, chooses a problem, changes the choice, confirms the read text and builds. Pages are composed in
// the browser test from exposed VMMU crops (no image is written to Git). Automated, not a student study.
// Usage (worktree root): node <this> <frontend/dist> <out_json> <cacheDir> [backendPort]
import { chromium } from 'file:///D:/Documents/projects/algo-sim/frontend/node_modules/playwright/index.mjs';
import { createServer, request } from 'node:http';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve, join, extname } from 'node:path';

const [dist, outJson, cacheDir] = process.argv.slice(2, 5).map((p) => resolve(p));
const backendPort = Number(process.argv[5] ?? 8767);
const CROPS = {
  r273: 'r273_Math_0025_test_005_question_14_page_2_key_D_vqa.png', r298: 'r298_Math_0315_test_062_question_42_page_5_key_B_vqa.png',
  r270: 'r270_Math_0128_test_022_question_43_page_6_key_A_vqa.png',
};
const server = createServer((req, res) => {
  const path = new URL(req.url, 'http://localhost').pathname;
  if (path.startsWith('/api/')) {
    const proxy = request({ host: '127.0.0.1', port: backendPort, path: req.url, method: req.method, headers: req.headers }, (up) => {
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
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const b64 = (name) => readFileSync(join(cacheDir, name)).toString('base64');

// compose a page in the browser (canvas), return PNG bytes
async function compose(page, names, layout) {
  const data = await page.evaluate(async ({ srcs, layout }) => {
    const imgs = await Promise.all(srcs.map((s) => new Promise((ok) => { const i = new Image(); i.onload = () => ok(i); i.src = 'data:image/png;base64,' + s; })));
    const gap = 80;
    const c = document.createElement('canvas');
    if (layout === 'stack') {
      c.width = Math.max(...imgs.map((i) => i.width)); c.height = imgs.reduce((h, i) => h + i.height, 0) + gap * (imgs.length + 1);
    } else {
      const s = 0.5; c.width = imgs.reduce((w, i) => w + i.width * s, 0) + gap * (imgs.length + 1); c.height = Math.max(...imgs.map((i) => i.height * s)) + 2 * gap;
    }
    const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height);
    let x = gap, y = gap;
    for (const i of imgs) {
      if (layout === 'stack') { g.drawImage(i, 0, y); y += i.height + gap; } else { g.drawImage(i, x, gap, i.width * 0.5, i.height * 0.5); x += i.width * 0.5 + gap; }
    }
    return c.toDataURL('image/png').split(',')[1];
  }, { srcs: names.map((n) => b64(CROPS[n])), layout });
  return Buffer.from(data, 'base64');
}

const grams = (t) => { const s = (t || '').toLowerCase().replace(/[^\p{L}\p{N}]/gu, ''); const out = new Set(); for (let i = 0; i + 5 <= s.length; i++) out.add(s.slice(i, i + 5)); return out; };
const STMTS = JSON.parse(readFileSync(resolve('docs/evaluation/geometry/runs/controlled-vision-real-image-validation/new_in_scope_image_manifest.json'), 'utf8')).items
  .reduce((m, it) => ({ ...m, [it.case_id.replace('vmmu_', '')]: it.statement }), {});
const contain = (stmt, text) => { const a = grams(stmt), b = grams(text); let n = 0; for (const x of a) if (b.has(x)) n++; return a.size ? n / a.size : 0; };

async function upload(page, buf, name) {
  const input = await page.$('input[type=file]');
  await input.setInputFiles({ name, mimeType: 'image/png', buffer: buf });
  await page.waitForTimeout(300);
  const prep = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/input/prepare', { timeout: 120000 });
  await page.click('#btn-composer-send');
  return (await prep).json();
}

async function pick(page, idx) {
  const prep = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/input/prepare', { timeout: 120000 });
  await page.click(`#composer-candidate-picker .composer-candidate-btn:nth-child(${idx})`);
  return (await prep).json();
}

const VIEWPORTS = [[1920, 1080], [1366, 768], [768, 1024], [390, 844]];
const rows = [];
try {
  for (const [w, h] of VIEWPORTS) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h } });
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e.message).slice(0, 120)));
    await page.goto(ORIGIN, { waitUntil: 'networkidle' });
    // a synthetic account in the measured app's throwaway SQLite (random password per run): guests get one analysis
    await page.evaluate(async () => fetch('/api/auth/register', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: `e2e-${Date.now()}-${Math.random()}@example.invalid`, displayName: 'E2E', password: crypto.randomUUID() }) }));
    await page.reload({ waitUntil: 'networkidle' });
    const row = { viewport: `${w}x${h}` };

    // 1. two stacked problems → a choice, never a merged page
    const two = await compose(page, ['r273', 'r298'], 'stack');
    const p1 = await upload(page, two, 'two.png');
    row.two_problems = { status: p1.status, reason: p1.reason_code, candidates: (p1.candidates || []).map((c) => c.candidate_id) };
    if (p1.status === 'needs_selection' && (p1.candidates || []).length === 2) {
      await page.waitForSelector('#composer-candidate-picker', { timeout: 10000 });
      const sizes = await page.$$eval('#composer-candidate-picker .composer-candidate-btn', (bs) => bs.map((b) => { const r = b.getBoundingClientRect(); return [r.width, r.height]; }));
      row.two_problems.candidate_button_min_px = Math.min(...sizes.flat());
      const second = await pick(page, 2);
      const t2 = second.problem_text || '';
      row.two_problems.pick_2 = { status: second.status, target_r298: contain(STMTS.r298, t2), neighbour_r273: contain(STMTS.r273, t2) };
      await page.waitForSelector('#photo-span-review, #composer-extraction-confirm', { timeout: 20000 });
      const reviewText = await page.evaluate(() => document.querySelector('#composer-extraction-confirm')?.innerText || '');
      row.two_problems.review_shows_neighbour = contain(STMTS.r273, reviewText) > contain(STMTS.r298, reviewText);
      // change the choice: dismiss, upload again, pick the other problem — the review must follow the new choice
      await page.click('#composer-extraction-confirm .context-close-icon-btn').catch(() => {});
      const again = await upload(page, two, 'two.png');
      const first = again.status === 'needs_selection' ? await pick(page, 1) : again;
      const t1 = first.problem_text || '';
      row.two_problems.repick_1 = { status: first.status, target_r273: contain(STMTS.r273, t1), neighbour_r298: contain(STMTS.r298, t1) };
      // confirm the chosen problem and build: the analyzed text is the chosen problem's only
      await page.waitForSelector('#photo-span-review, #composer-extraction-confirm', { timeout: 20000 });
      await page.evaluate(() => document.querySelectorAll('#photo-span-review .photo-span-item').forEach((li) => {
        if (li.getAttribute('data-reviewed') !== 'true') li.querySelector('.photo-span-ok')?.click(); }));
      await page.waitForTimeout(150);
      const chk = await page.$('#chk-confirm-extracted-text');
      if (chk) await chk.check();
      const an = page.waitForRequest((r) => new URL(r.url()).pathname === '/api/analyze', { timeout: 30000 }).catch(() => null);
      await page.click('#btn-confirm-extracted-build').catch(() => {});
      const req = await an;
      const sent = req ? (req.postData() || '') : '';             // the whole request body: nothing of the neighbour may travel
      row.two_problems.analyze_sent = Boolean(req);
      row.two_problems.analyzed_text_target_r273 = contain(STMTS.r273, sent);
      row.two_problems.analyzed_text_neighbour_r298 = contain(STMTS.r298, sent);
      if (req) {
        const resp = await req.response();
        const body = resp ? await resp.json().catch(() => ({})) : {};
        row.two_problems.analyze_status = body?.route_d?.status ?? body?.status ?? null;
        row.two_problems.analyze_refusal = body?.route_d?.refusal?.code ?? null;
      }
    }
    // 2. side by side → ask for a tighter photo, never send the page
    await page.goto(ORIGIN, { waitUntil: 'networkidle' });
    const side = await compose(page, ['r273', 'r298'], 'side');
    const ps = await upload(page, side, 'side.png');
    row.side_by_side = { status: ps.status, reason: ps.reason_code, candidates: (ps.candidates || []).length };
    // 3. one problem with its figure → no choice asked
    await page.goto(ORIGIN, { waitUntil: 'networkidle' });
    const one = await page.evaluate((s) => s, b64(CROPS.r270));
    const po = await upload(page, Buffer.from(one, 'base64'), 'one.png');
    row.single_problem = { status: po.status, reason: po.reason_code, asked_to_choose: po.status === 'needs_selection' };
    row.horizontal_overflow_px = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    row.page_errors = errors;
    const tp = row.two_problems;
    row.pass = tp.status === 'needs_selection' && tp.candidates.length === 2 && tp.pick_2?.target_r298 > tp.pick_2?.neighbour_r273
      && tp.repick_1?.target_r273 > tp.repick_1?.neighbour_r298 && !tp.review_shows_neighbour
      && (!tp.analyze_sent || tp.analyzed_text_target_r273 > tp.analyzed_text_neighbour_r298)
      && row.side_by_side.status === 'needs_selection' && !row.single_problem.asked_to_choose
      && row.horizontal_overflow_px <= 0 && errors.length === 0 && (w > 500 || (tp.candidate_button_min_px ?? 0) >= 40);
    rows.push(row);
    console.log(JSON.stringify({ viewport: row.viewport, pass: row.pass }));
    await ctx.close();
  }
} finally {
  writeFileSync(outJson, JSON.stringify({ browser: browser.version(), headless: true,
    backend: 'measured_app loopback, HYBRID_ROUTE_MODE=local-first, ALLOW_LIVE_AI=0, local OCR on',
    category: 'AUTOMATED_BROWSER_NOT_HUMAN_STUDY', pages: 'composed in the browser from exposed VMMU crops (r273, r298, r270); no image stored',
    rows, passed: rows.filter((r) => r.pass).length, total: rows.length }, null, 2) + '\n');
  await browser.close(); server.close();
}
