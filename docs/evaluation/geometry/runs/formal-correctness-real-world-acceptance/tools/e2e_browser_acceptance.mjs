// Real end-to-end browser acceptance (run `formal-correctness-real-world-acceptance`): production frontend build served
// statically, every `/api/*` request PROXIED to a real local backend (uvicorn, HYBRID_ROUTE_MODE=local-first,
// ALLOW_LIVE_AI=0). Types problems into the real composer, submits, and records request/response status, console
// errors, page errors, scene presence, the illustrative-scene note, output_policy exact+display preservation,
// orbit/zoom stability and JS heap across 100% and 110% zoom. 0 model calls.
import { chromium } from 'file:///D:/Documents/projects/algo-sim/frontend/node_modules/playwright/index.mjs';
import { createServer, request as httpRequest } from 'node:http';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve, join, extname } from 'node:path';

const dist = resolve(process.argv[2]);
const backendPort = Number(process.argv[3]);
const outJson = resolve(process.argv[4]);
const imagePath = process.argv[5] ? resolve(process.argv[5]) : null;

const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml' };
const server = createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  if (pathname.startsWith('/api/')) {
    const up = httpRequest({ host: '127.0.0.1', port: backendPort, path: req.url, method: req.method, headers: req.headers }, (r) => {
      res.writeHead(r.statusCode, r.headers); r.pipe(res);
    });
    up.on('error', () => { res.writeHead(502); res.end(); });
    req.pipe(up);
    return;
  }
  const asset = pathname.includes('.');
  const file = join(dist, asset ? pathname : 'index.html');
  if (!file.startsWith(dist) || !existsSync(file)) { res.writeHead(404); res.end(); return; }
  res.setHeader('Content-Type', mime[extname(file)] ?? 'application/octet-stream');
  res.end(readFileSync(file));
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const url = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ channel: 'chrome', headless: true });

const CASES = [
  { id: 'ext02_height_invariant', expect: 'SERVED', illustrative: true, expectedSym: '6', expectedExactSym: null,
    text: "Câu 10: Cho hình lăng trụ đứng ABC.A'B'C', có đáy là tam giác vuông cân tại B và AB = 6. Tính khoảng cách từ điểm C đến mặt phẳng (ABB'A')" },
  { id: 'ext03_1_height_invariant', expect: 'SERVED', illustrative: true, expectedSym: 'a√2/2', expectedExactSym: null,
    text: "Câu 32: Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). Tính khoảng cách từ điểm B đến mp(SAC)." },
  { id: 'ext04_affine_length_ratio', expect: 'SERVED', illustrative: true, expectedSym: '1/2', expectedExactSym: null,
    text: "Câu 6. Cho hình chóp S.ABCD có đáy ABCD là hình thang với AD song song BC và AD = 2BC. Gọi I là trung điểm cạnh AD. Mặt phẳng (P) qua I và song song với hai đường thẳng SA, SC. Gọi K là giao điểm của BC với (P). Khi đó tính tỉ số KC/KB." },
  { id: 'ext05_section_area_ratio', expect: 'SERVED', illustrative: true, expectedSym: '6/5', expectedExactSym: null,
    text: "Câu 24: (2,5 điểm) Cho hình chóp S.ABCD có đáy ABCD là hình bình hành tâm O. M là trung điểm của SB. Gọi E là điểm thuộc cạnh SC sao cho SE = 3EC. Mặt phẳng (SAD) và đường thẳng ME cắt nhau tại I. Gọi S1; S2 lần lượt là diện tích tam giác SMI và tứ giác BCEM. Tính S1/S2." },
  { id: 'ext06_inverse_angle_compound', expect: 'SERVED', illustrative: false, expectedSym: 'a³√15/4', expectedExactSym: null,
    text: "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác cân tại C, AB = AA' = a. Góc tạo bởi đường thẳng BC' với mặt phẳng (ABB'A') bằng 60°. Gọi M, N, P lần lượt là trung điểm của các cạnh BB', CC' và BC. Tính thể tích khối lăng trụ ABC.A'B'C' và khoảng cách giữa hai đường thẳng AM và NP theo a." },
  { id: 'ext07_rounded_and_exact', expect: 'SERVED', illustrative: true, expectedSym: '4,7', expectedExactSym: '15√93/31',
    text: "Câu 3: Cho hình lăng trụ đứng ABC.A'B'C' có AB = 5, AC = 6, Â = 60°. Khoảng cách giữa hai đường thẳng AA' và BC (làm tròn kết quả đến hàng phần mười)" },
  { id: 'ext11_degree_and_exact', expect: 'SERVED', illustrative: false, expectedSym: '30°', expectedExactSym: 'cos²=3/4',
    text: "Câu 36: Cho khối lăng trụ tam giác đều ABC.A'B'C' có cạnh đáy bằng 2a, chiều cao bằng a. Tính số đo góc tạo bởi hai mặt phẳng (AB'C') và (ABC)? A. 60°. B. 45°. C. 30°. D. 90°." },
  { id: 'ext12_face_area_premise', expect: 'SERVED', illustrative: false, expectedSym: '2√3', expectedExactSym: null,
    text: "Câu 22: Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B và diện tích của hình vuông ABB'A' bằng 12(cm²). Khoảng cách từ C đến mặt phẳng (ABB'A') bằng A. 12(cm). B. 2√3(cm). C. 6(cm). D. 4√3(cm)." },
  { id: 'refused_missing_dimension', expect: 'REFUSED', illustrative: false, expectedSym: null, expectedExactSym: null,
    text: 'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). Tính thể tích khối chóp S.ABCD.' },
  { id: 'refused_non_unique_foot', expect: 'REFUSED', illustrative: false, expectedSym: null, expectedExactSym: null,
    text: 'Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, cạnh bên SA = 2a và SA tạo với mặt phẳng đáy một góc 30°. Tính thể tích khối chóp S.ABC.' },
  { id: 'refused_out_of_scope_vector', expect: 'REFUSED', illustrative: false, expectedSym: null, expectedExactSym: null,
    text: 'Câu 10. Cho hình chóp S.ABCD có đáy là hình bình hành tâm O. Tính tổng vectơ SA + SB + SC + SD.' },
];

const results = [];
for (const [vw, vh, zoom] of [[1440, 900, 1], [1440, 900, 1.1]]) {
  for (const c of CASES) {
    const ctx = await browser.newContext({ viewport: { width: vw, height: vh }, deviceScaleFactor: zoom });
    const page = await ctx.newPage();
    const consoleErrors = [], pageErrors = [], api = [];
    page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 200)); });
    page.on('pageerror', (e) => pageErrors.push(String(e).slice(0, 200)));
    page.on('response', (r) => { const p = new URL(r.url()).pathname; if (p.startsWith('/api/analyze')) api.push({ path: p, status: r.status() }); });
    await page.goto(`${url}/`, { waitUntil: 'networkidle' });
    const t0 = Date.now();
    await page.fill('#home-problem-input', c.text);
    const respPromise = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/analyze', { timeout: 30000 });
    await page.click('#btn-composer-send');
    const resp = await respPromise;
    const body = await resp.json().catch(() => null);
    await page.waitForTimeout(1000);
    const serverStatus = body?.route_d?.status ?? body?.envelope?.status ?? null;
    const st = await page.evaluate(() => {
      const s = window.__ALGO_SIM_STORE__?.getState();
      const canvas = document.querySelector('#stage-3d-box canvas');
      const r = canvas ? canvas.getBoundingClientRect() : null;
      const hp = s?.active?.envelope?.hybrid_preview ?? null;
      const allSyms = (hp?.answers ?? []).map((a) => a.symbolic);
      const firstAns = hp?.answers?.[0] ?? null;
      return {
        view: s?.view ?? null,
        active: !!s?.active,
        analysisError: s?.analysisError ?? null,
        unsupported: !!s?.unsupported,
        hasCanvas: !!r && r.width > 100 && r.height > 100,
        note: document.querySelector('#stage-illustrative-note')?.textContent ?? null,
        allAnswerSymbolics: allSyms,
        firstAnswerSymbolic: firstAns?.symbolic ?? null,
        firstAnswerExactSymbolic: firstAns?.exact_symbolic ?? null,
        answerCount: hp?.answers?.length ?? 0,
        bodyHasRawTraceback: /Traceback \(most recent call last\)/.test(document.body.innerText),
        bodyHasRawReasonCode: /\b(MISSING_DIMENSION|UNDERDETERMINED_POINT|LIVE_AI_DISABLED)\b/.test(document.body.innerText),
        bodyHasPhotoCopy: /trích xuất ảnh/i.test(document.body.innerText) || /trích xuất ảnh/i.test(s?.analysisError ?? ''),
        bodyHasAnalyzeAiCopy: /phân tích bằng AI|phân tích đề hiện chưa sẵn sàng/.test(document.body.innerText),
      };
    });
    let orbit = null;
    if (st.hasCanvas) {
      orbit = await page.evaluate(async () => {
        const canvas = document.querySelector('#stage-3d-box canvas');
        const r = canvas.getBoundingClientRect(); const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
        let frames = 0, stop = false; const f = () => { frames++; if (!stop) requestAnimationFrame(f); }; requestAnimationFrame(f);
        const t = performance.now();
        canvas.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: cx, clientY: cy, button: 0, pointerId: 1 }));
        for (let i = 1; i <= 20; i++) { canvas.dispatchEvent(new PointerEvent('pointermove', { bubbles: true, clientX: cx + i * 4, clientY: cy + i * 2, button: 0, pointerId: 1 })); await new Promise((x) => setTimeout(x, 16)); }
        canvas.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: cx + 80, clientY: cy + 40, button: 0, pointerId: 1 }));
        for (let i = 0; i < 4; i++) canvas.dispatchEvent(new WheelEvent('wheel', { bubbles: true, deltaY: i % 2 ? 120 : -120, clientX: cx, clientY: cy }));
        await new Promise((x) => setTimeout(x, 150));
        stop = true;
        const r2 = canvas.getBoundingClientRect();
        return { fps: Number((frames / ((performance.now() - t) / 1000)).toFixed(1)), canvasStable: r2.width === r.width && r2.height === r.height,
                 heapMB: performance.memory ? Number((performance.memory.usedJSHeapSize / 1048576).toFixed(2)) : null };
      });
    }
    const symMatch = !c.expectedSym || (st.allAnswerSymbolics ?? []).includes(c.expectedSym);
    const exactMatch = !c.expectedExactSym || st.firstAnswerExactSymbolic === c.expectedExactSym;
    const pass = c.expect === 'SERVED'
      ? serverStatus === 'SERVED' && st.active && st.hasCanvas && (c.illustrative ? !!st.note : !st.note) && symMatch && exactMatch && consoleErrors.length === 0 && pageErrors.length === 0
      : serverStatus !== 'SERVED' && !st.hasCanvas && !st.note && !st.bodyHasRawTraceback && !st.bodyHasPhotoCopy
        && (resp.status() !== 503 || st.bodyHasAnalyzeAiCopy) && pageErrors.length === 0;
    results.push({ id: c.id, viewport: `${vw}x${vh}@${zoom}`, expected: c.expect, serverStatus, httpStatus: resp.status(),
                   elapsedMs: Date.now() - t0, ...st, orbit, api, consoleErrors, pageErrors, pass });
    await ctx.close();
  }
}

// Image upload with live AI disabled -> no false scene; then edit transcription -> re-solve -> renders 3D scene cleanly.
let imageCase = null;
if (imagePath) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const consoleErrors = [], pageErrors = [], api = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 200)); });
  page.on('pageerror', (e) => pageErrors.push(String(e).slice(0, 200)));
  page.on('response', (r) => { const p = new URL(r.url()).pathname; if (p.startsWith('/api/')) api.push({ path: p, status: r.status() }); });
  await page.goto(`${url}/`, { waitUntil: 'networkidle' });
  const input = await page.$('input[type=file]');
  if (input) {
    await input.setInputFiles(imagePath);
    await page.waitForTimeout(800);
    await page.click('#btn-composer-send').catch(() => {});
    await page.waitForTimeout(3000);
  }
  const stAfterUpload = await page.evaluate(() => ({
    active: !!window.__ALGO_SIM_STORE__?.getState().active,
    hasCanvas: !!document.querySelector('#stage-3d-box canvas'),
    bodyHasRawTraceback: /Traceback \(most recent call last\)/.test(document.body.innerText),
  }));
  // Now verify user-edit -> re-solve flow (change problem text and re-submit -> 0 stale cache)
  await ctx.clearCookies();
  await page.goto(`${url}/`, { waitUntil: 'networkidle' });
  await page.fill('#home-problem-input', "Câu 10: Cho hình lăng trụ đứng ABC.A'B'C', có đáy là tam giác vuông cân tại B và AB = 6. Tính khoảng cách từ điểm C đến mặt phẳng (ABB'A')");
  const respFirst = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/analyze', { timeout: 30000 });
  await page.click('#btn-composer-send');
  await respFirst;
  await page.waitForTimeout(800);
  await ctx.clearCookies();
  await page.goto(`${url}/`, { waitUntil: 'networkidle' });
  await page.fill('#home-problem-input', "Câu 22: Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B và diện tích của hình vuông ABB'A' bằng 12(cm²). Khoảng cách từ C đến mặt phẳng (ABB'A') bằng A. 12(cm). B. 2√3(cm). C. 6(cm). D. 4√3(cm).");
  const respEditPromise = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/analyze', { timeout: 30000 });
  await page.click('#btn-composer-send');
  await respEditPromise;
  await page.waitForTimeout(1000);
  const stAfterEdit = await page.evaluate(() => ({
    active: !!window.__ALGO_SIM_STORE__?.getState().active,
    hasCanvas: !!document.querySelector('#stage-3d-box canvas'),
    firstAnswerSymbolic: window.__ALGO_SIM_STORE__?.getState().active?.envelope?.hybrid_preview?.answers?.[0]?.symbolic ?? null,
  }));
  imageCase = {
    fileInputFound: !!input,
    afterUploadWithAiOff: stAfterUpload,
    afterUserEditResolve: stAfterEdit,
    api,
    consoleErrors,
    pageErrors,
    pass: !!input && !stAfterUpload.active && !stAfterUpload.hasCanvas && !stAfterUpload.bodyHasRawTraceback
      && stAfterEdit.active && stAfterEdit.hasCanvas && stAfterEdit.firstAnswerSymbolic === '2√3'
      && pageErrors.length === 0,
  };
  await ctx.close();
}

const report = { browser: browser.version(), provider_calls: 0, results, imageCase,
                 summary: { pass: results.filter((r) => r.pass).length, total: results.length, imagePass: imageCase?.pass ?? null } };
writeFileSync(outJson, JSON.stringify(report, null, 2));
await browser.close(); server.close();
console.log(JSON.stringify(report.summary));
for (const r of results) console.log(r.id, r.viewport, r.serverStatus, r.pass, r.firstAnswerSymbolic, r.firstAnswerExactSymbolic ?? '', r.note ? 'NOTE' : '', r.consoleErrors.length, r.pageErrors.length);
if (imageCase) console.log('image', JSON.stringify({ pass: imageCase.pass, afterUpload: imageCase.afterUploadWithAiOff, afterEdit: imageCase.afterUserEditResolve }));
