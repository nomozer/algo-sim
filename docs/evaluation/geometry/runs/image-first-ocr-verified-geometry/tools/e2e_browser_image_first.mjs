// Headless Chromium E2E acceptance for `image-first-ocr-verified-geometry`:
// Tests real external image uploads through the production frontend build proxied to a real local FastAPI backend
// (`HYBRID_ROUTE_MODE=local-first`, `ALLOW_LIVE_AI=0`, `LOCAL_OCR_PYTHON` + `LOCAL_OCR_TESSDATA` active, `0` Gemini calls).
import { chromium } from 'file:///D:/Documents/projects/algo-sim/frontend/node_modules/playwright/index.mjs';
import { createServer, request as httpRequest } from 'node:http';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve, join, extname } from 'node:path';

const dist = resolve(process.argv[2]);
const backendPort = Number(process.argv[3]);
const outJson = resolve(process.argv[4]);
const cacheDir = resolve(process.argv[5]);

const mime = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.svg': 'image/svg+xml',
};

const server = createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  if (pathname.startsWith('/api/')) {
    const up = httpRequest(
      { host: '127.0.0.1', port: backendPort, path: req.url, method: req.method, headers: req.headers },
      (r) => {
        res.writeHead(r.statusCode, r.headers);
        r.pipe(res);
      },
    );
    up.on('error', () => {
      res.writeHead(502);
      res.end();
    });
    req.pipe(up);
    return;
  }
  const asset = pathname.includes('.');
  const file = join(dist, asset ? pathname : 'index.html');
  if (!file.startsWith(dist) || !existsSync(file)) {
    res.writeHead(404);
    res.end();
    return;
  }
  res.setHeader('Content-Type', mime[extname(file)] ?? 'application/octet-stream');
  res.end(readFileSync(file));
});

await new Promise((r) => server.listen(0, '127.0.0.1', r));
const url = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ channel: 'chrome', headless: true });

function filePayload(filePath) {
  const buf = readFileSync(filePath);
  const isJpeg = buf[0] === 0xff && buf[1] === 0xd8;
  const isPng = buf[0] === 0x89 && buf[1] === 0x50;
  const mimeType = isJpeg ? 'image/jpeg' : isPng ? 'image/png' : 'image/webp';
  const ext = isJpeg ? '.jpg' : isPng ? '.png' : '.webp';
  const base = filePath.split(/[\\/]/).pop().replace(/\.(png|jpg|jpeg|webp)$/i, '') + ext;
  return { name: base, mimeType, buffer: buf };
}

async function measureOrbitAndState(page) {
  const st = await page.evaluate(() => {
    const s = window.__ALGO_SIM_STORE__?.getState();
    const canvas = document.querySelector('#stage-3d-box canvas');
    const r = canvas ? canvas.getBoundingClientRect() : null;
    const hp = s?.active?.envelope?.hybrid_preview ?? null;
    const allSyms = (hp?.answers ?? []).map((a) => a.symbolic);
    return {
      view: s?.view ?? null,
      active: !!s?.active,
      analysisError: s?.analysisError ?? null,
      unsupported: !!s?.unsupported,
      hasCanvas: !!r && r.width > 100 && r.height > 100,
      canvasRect: r ? { width: Math.round(r.width), height: Math.round(r.height) } : null,
      note: document.querySelector('#stage-illustrative-note')?.textContent ?? null,
      allAnswerSymbolics: allSyms,
      firstAnswerSymbolic: allSyms[0] ?? null,
      bodyHasRawTraceback: /Traceback \(most recent call last\)/.test(document.body.innerText),
    };
  });
  let orbit = null;
  if (st.hasCanvas) {
    orbit = await page.evaluate(async () => {
      const canvas = document.querySelector('#stage-3d-box canvas');
      const r = canvas.getBoundingClientRect();
      const cx = r.left + r.width / 2;
      const cy = r.top + r.height / 2;
      let frames = 0;
      let stop = false;
      const f = () => {
        frames++;
        if (!stop) requestAnimationFrame(f);
      };
      requestAnimationFrame(f);
      const t = performance.now();
      canvas.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: cx, clientY: cy, button: 0, pointerId: 1 }));
      for (let i = 1; i <= 16; i++) {
        canvas.dispatchEvent(new PointerEvent('pointermove', { bubbles: true, clientX: cx + i * 4, clientY: cy + i * 2, button: 0, pointerId: 1 }));
        await new Promise((x) => setTimeout(x, 16));
      }
      canvas.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: cx + 64, clientY: cy + 32, button: 0, pointerId: 1 }));
      await new Promise((x) => setTimeout(x, 100));
      stop = true;
      const r2 = canvas.getBoundingClientRect();
      return {
        fps: Number((frames / ((performance.now() - t) / 1000)).toFixed(1)),
        canvasStable: r2.width === r.width && r2.height === r.height,
        heapMB: performance.memory ? Number((performance.memory.usedJSHeapSize / 1048576).toFixed(2)) : null,
      };
    });
  }
  return { ...st, orbit };
}

const scenarios = [];

// 1. Outcome A: Fully Automatic Local OCR -> Scene3D (100% and 110% zoom) + User-Edit Cache Invalidation
for (const [vw, vh, zoom] of [[1440, 900, 1], [1440, 900, 1.1]]) {
  const ctx = await browser.newContext({ viewport: { width: vw, height: vh }, deviceScaleFactor: zoom });
  const page = await ctx.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const apiCalls = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 200)); });
  page.on('pageerror', (e) => pageErrors.push(String(e).slice(0, 200)));
  page.on('response', (r) => {
    const p = new URL(r.url()).pathname;
    if (p.startsWith('/api/')) apiCalls.push({ path: p, status: r.status() });
  });

  await page.goto(`${url}/`, { waitUntil: 'networkidle' });
  const t0 = Date.now();
  const fileInput = await page.$('input[type=file]');
  await fileInput.setInputFiles(filePayload(join(cacheDir, 'hd_q_5259753.jpg')));
  await page.waitForTimeout(300);

  const prepProm = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/input/prepare', { timeout: 30000 });
  const analyzeProm = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/analyze', { timeout: 30000 });
  await page.click('#btn-composer-send');
  const prepResp = await prepProm;
  const prepJson = await prepResp.json();
  const analyzeResp = await analyzeProm;
  const analyzeJson = await analyzeResp.json();
  await page.waitForTimeout(900);

  const state1 = await measureOrbitAndState(page);
  const autoPass =
    prepJson?.status === 'ready' &&
    String(prepJson?.provenance?.input_route || '').toUpperCase() === 'LOCAL_OCR_VERIFIED' &&
    prepJson?.metrics?.vlm_calls === 0 &&
    analyzeJson?.route_d?.status === 'SERVED' &&
    state1.hasCanvas &&
    state1.allAnswerSymbolics.includes('a³√3/3') &&
    state1.allAnswerSymbolics.includes('a√21/21') &&
    consoleErrors.length === 0 &&
    pageErrors.length === 0;

  let cacheInvalidationCheck = null;
  if (zoom === 1) {
    // Issue a fresh guest session cookie so the 1-trial guest quota does not reject the second /api/analyze call with 402
    await ctx.clearCookies();
    await page.evaluate(() => fetch('/api/auth/me', { credentials: 'include' }));
    // Return to home view and modify 60° -> 45° in #home-problem-input without re-uploading image
    const apiCountBeforeEdit = apiCalls.length;
    await page.evaluate(() => window.__ALGO_SIM_STORE__?.getState().setView('home'));
    await page.waitForSelector('#home-problem-input', { timeout: 5000 });
    const currentText = await page.$eval('#home-problem-input', (el) => el.value);
    const editedText = currentText.replace('60°', '45°');
    await page.fill('#home-problem-input', editedText);
    const analyzeEditProm = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/analyze', { timeout: 30000 });
    await page.click('#btn-composer-send');
    const analyzeEditResp = await analyzeEditProm;
    const analyzeEditJson = await analyzeEditResp.json();
    await page.waitForTimeout(800);
    const stateAfterEdit = await measureOrbitAndState(page);
    const newApiCalls = apiCalls.slice(apiCountBeforeEdit);
    const prepareCalledAgain = newApiCalls.some((c) => c.path === '/api/input/prepare');
    cacheInvalidationCheck = {
      editedFrom: '60°',
      editedTo: '45°',
      prepareCalledAgain,
      newStatus: analyzeEditJson?.route_d?.status ?? null,
      newAnswers: stateAfterEdit.allAnswerSymbolics,
      hasCanvas: stateAfterEdit.hasCanvas,
      pass:
        !prepareCalledAgain &&
        analyzeEditJson?.route_d?.status === 'SERVED' &&
        stateAfterEdit.allAnswerSymbolics.includes('a³/3') &&
        !stateAfterEdit.allAnswerSymbolics.includes('a³√3/3'),
    };
  }

  scenarios.push({
    id: `outcome_a_local_auto_ext01_${vw}x${vh}_zoom_${zoom}`,
    outcomeCategory: 'A_LOCAL_AUTO',
    imageId: 'ext_prt_01_hd_q_5259753',
    viewport: `${vw}x${vh}@${zoom}`,
    elapsedMs: Date.now() - t0,
    prepareStatus: prepJson?.status,
    inputRoute: prepJson?.provenance?.input_route,
    vlmCalls: prepJson?.metrics?.vlm_calls,
    serverStatus: analyzeJson?.route_d?.status,
    ...state1,
    cacheInvalidationCheck,
    apiCalls,
    consoleErrors,
    pageErrors,
    pass: autoPass && (zoom !== 1 || Boolean(cacheInvalidationCheck?.pass)),
  });
  await ctx.close();
}

// 2. Outcome C: Span-Level Student Confirmation UI (#photo-span-review) on ext_prt_12 -> Scene3D
{
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const apiCalls = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 200)); });
  page.on('pageerror', (e) => pageErrors.push(String(e).slice(0, 200)));
  page.on('response', (r) => {
    const p = new URL(r.url()).pathname;
    if (p.startsWith('/api/')) apiCalls.push({ path: p, status: r.status() });
  });

  await page.goto(`${url}/`, { waitUntil: 'networkidle' });
  const t0 = Date.now();
  const fileInput = await page.$('input[type=file]');
  await fileInput.setInputFiles(filePayload(join(cacheDir, 'vmmu_page_r11_Math_0303_test_059_question_39_page_4_key_B_vqa.png')));
  await page.waitForTimeout(300);

  const prepProm = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/input/prepare', { timeout: 30000 });
  await page.click('#btn-composer-send');
  const prepResp = await prepProm;
  const prepJson = await prepResp.json();
  await page.waitForSelector('#photo-span-review', { timeout: 10000 });

  const uiBeforeConfirm = await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('#photo-span-review .photo-span-item'));
    const crops = Array.from(document.querySelectorAll('#photo-span-review .photo-span-crop'));
    const confirmBtn = document.querySelector('#btn-confirm-extracted-build');
    return {
      spanItemCount: items.length,
      cropImageCount: crops.filter((img) => (img.getAttribute('src') || '').startsWith('data:image/')).length,
      confirmBtnInitiallyDisabled: confirmBtn ? confirmBtn.disabled : null,
      spans: items.map((li) => ({
        spanId: li.getAttribute('data-span-id'),
        reviewed: li.getAttribute('data-reviewed'),
        reason: li.querySelector('.photo-span-reason')?.textContent ?? '',
        inputValue: li.querySelector('.photo-span-input')?.value ?? null,
        alts: Array.from(li.querySelectorAll('.photo-span-alt')).map((b) => b.textContent),
      })),
    };
  });

  // Edit the truncated prism notation span `ABC.A'B'C` -> `ABC.A'B'C'` via its span input, and click `.photo-span-ok` on any unreviewed spans
  for (const sp of uiBeforeConfirm.spans) {
    if (sp.inputValue && sp.inputValue.includes("ABC.A'B'C") && !sp.inputValue.endsWith("'")) {
      await page.fill(`[data-span-input="${sp.spanId}"]`, "ABC.A'B'C'");
    } else {
      await page.click(`[data-span-ok="${sp.spanId}"]`);
    }
  }
  await page.waitForTimeout(200);
  await page.check('#chk-confirm-extracted-text');
  await page.waitForTimeout(100);

  const canConfirmNow = await page.$eval('#btn-confirm-extracted-build', (btn) => !btn.disabled);
  const analyzeProm = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/analyze', { timeout: 30000 });
  await page.click('#btn-confirm-extracted-build');
  const analyzeResp = await analyzeProm;
  const analyzeJson = await analyzeResp.json();
  await page.waitForTimeout(900);

  const stateAfterConfirm = await measureOrbitAndState(page);
  const pass =
    prepJson?.status === 'needs_confirmation' &&
    uiBeforeConfirm.spanItemCount >= 1 &&
    uiBeforeConfirm.cropImageCount >= 1 &&
    uiBeforeConfirm.confirmBtnInitiallyDisabled === true &&
    canConfirmNow === true &&
    analyzeJson?.route_d?.status === 'SERVED' &&
    stateAfterConfirm.hasCanvas &&
    stateAfterConfirm.allAnswerSymbolics.includes('2√3') &&
    consoleErrors.length === 0 &&
    pageErrors.length === 0;

  scenarios.push({
    id: 'outcome_c_span_confirmation_ext12',
    outcomeCategory: 'C_USER_CORRECTED',
    imageId: 'ext_prt_12_vmmu_page_r11',
    viewport: '1440x900@1',
    elapsedMs: Date.now() - t0,
    prepareStatus: prepJson?.status,
    uiBeforeConfirm,
    canConfirmNow,
    serverStatus: analyzeJson?.route_d?.status,
    ...stateAfterConfirm,
    apiCalls,
    consoleErrors,
    pageErrors,
    pass,
  });
  await ctx.close();
}

// 3. Multi-Problem Selection + Alternative Chip Click on ext_prt_03_hd_q_7907931 -> Scene3D
{
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const apiCalls = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 200)); });
  page.on('pageerror', (e) => pageErrors.push(String(e).slice(0, 200)));
  page.on('response', (r) => {
    const p = new URL(r.url()).pathname;
    if (p.startsWith('/api/')) apiCalls.push({ path: p, status: r.status() });
  });

  await page.goto(`${url}/`, { waitUntil: 'networkidle' });
  const t0 = Date.now();
  const fileInput = await page.$('input[type=file]');
  await fileInput.setInputFiles(filePayload(join(cacheDir, 'hd_q_7907931.jpg')));
  await page.waitForTimeout(300);

  const prep1Prom = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/input/prepare', { timeout: 30000 });
  await page.click('#btn-composer-send');
  const prep1Json = await (await prep1Prom).json();
  await page.waitForSelector('#composer-candidate-picker', { timeout: 10000 });

  const candidateCount = await page.$$eval('#composer-candidate-picker .composer-candidate-btn', (btns) => btns.length);
  const prep2Prom = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/input/prepare', { timeout: 30000 });
  await page.click('#composer-candidate-picker .composer-candidate-btn:first-child');
  const prep2Json = await (await prep2Prom).json();
  await page.waitForSelector('#photo-span-review', { timeout: 10000 });

  // Exercise 1-click `.photo-span-alt` chip selection on `sp23` (`B` -> `8`, verifying DOM input + reviewed state update),
  // then restore `B` and confirm remaining spans with `.photo-span-ok`
  const firstAltText = await page.$eval('#photo-span-review .photo-span-alt', (b) => b.textContent || '');
  const firstAltSpanId = await page.$eval('#photo-span-review .photo-span-alt', (b) =>
    b.closest('.photo-span-item')?.getAttribute('data-span-id') || '',
  );
  const origVal = await page.$eval(`[data-span-input="${firstAltSpanId}"]`, (el) => el.value);
  await page.click('#photo-span-review .photo-span-alt');
  const valAfterAltClick = await page.$eval(`[data-span-input="${firstAltSpanId}"]`, (el) => el.value);
  const clickedAltChip = valAfterAltClick === firstAltText && valAfterAltClick !== origVal;
  await page.fill(`[data-span-input="${firstAltSpanId}"]`, origVal);
  await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('#photo-span-review .photo-span-item'));
    for (const li of items) {
      if (li.getAttribute('data-reviewed') !== 'true') {
        li.querySelector('.photo-span-ok')?.click();
      }
    }
  });
  await page.waitForTimeout(150);
  await page.check('#chk-confirm-extracted-text');
  const analyzeProm = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/analyze', { timeout: 30000 });
  await page.click('#btn-confirm-extracted-build');
  const analyzeJson = await (await analyzeProm).json();
  await page.waitForTimeout(900);

  const stateAfterConfirm = await measureOrbitAndState(page);
  const pass =
    prep1Json?.status === 'needs_selection' &&
    candidateCount === 2 &&
    prep2Json?.status === 'needs_confirmation' &&
    clickedAltChip === true &&
    analyzeJson?.route_d?.status === 'SERVED' &&
    stateAfterConfirm.hasCanvas &&
    Boolean(stateAfterConfirm.note) &&
    stateAfterConfirm.allAnswerSymbolics.includes('a√2/2') &&
    consoleErrors.length === 0 &&
    pageErrors.length === 0;

  scenarios.push({
    id: 'outcome_c_multi_problem_alt_chip_ext03_cand1',
    outcomeCategory: 'C_USER_CORRECTED',
    imageId: 'ext_prt_03_hd_q_7907931#1',
    viewport: '1440x900@1',
    elapsedMs: Date.now() - t0,
    candidateCount,
    clickedAltChip,
    serverStatus: analyzeJson?.route_d?.status,
    ...stateAfterConfirm,
    apiCalls,
    consoleErrors,
    pageErrors,
    pass,
  });
  await ctx.close();
}

// 4. Unseen External Image (`new_ext_01_vmmu_full_r313`) -> Span Edit (`AABC'` -> `ΔABC`) -> Scene3D (`2a√57/19`)
{
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const apiCalls = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 200)); });
  page.on('pageerror', (e) => pageErrors.push(String(e).slice(0, 200)));
  page.on('response', (r) => {
    const p = new URL(r.url()).pathname;
    if (p.startsWith('/api/')) apiCalls.push({ path: p, status: r.status() });
  });

  await page.goto(`${url}/`, { waitUntil: 'networkidle' });
  const t0 = Date.now();
  const fileInput = await page.$('input[type=file]');
  await fileInput.setInputFiles(filePayload(join(cacheDir, 'vmmu_full_r313_Math_0311_test_062_question_30_page_3_key_A_vqa.png')));
  await page.waitForTimeout(300);

  const prepProm = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/input/prepare', { timeout: 30000 });
  await page.click('#btn-composer-send');
  const prepJson = await (await prepProm).json();
  await page.waitForSelector('#photo-span-review', { timeout: 10000 });

  const spans01 = await page.evaluate(() =>
    Array.from(document.querySelectorAll('#photo-span-review .photo-span-item')).map((li) => ({
      spanId: li.getAttribute('data-span-id'),
      inputValue: li.querySelector('.photo-span-input')?.value ?? null,
    })),
  );
  for (const sp of spans01) {
    if (sp.inputValue && sp.inputValue.includes('AABC')) {
      await page.fill(`[data-span-input="${sp.spanId}"]`, 'ΔABC');
    } else {
      await page.click(`[data-span-ok="${sp.spanId}"]`);
    }
  }
  await page.waitForTimeout(150);
  await page.check('#chk-confirm-extracted-text');
  const analyzeProm = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/analyze', { timeout: 30000 });
  await page.click('#btn-confirm-extracted-build');
  const analyzeJson = await (await analyzeProm).json();
  await page.waitForTimeout(900);

  const stateAfterConfirm = await measureOrbitAndState(page);
  const pass =
    prepJson?.status === 'needs_confirmation' &&
    analyzeJson?.route_d?.status === 'SERVED' &&
    stateAfterConfirm.hasCanvas &&
    stateAfterConfirm.allAnswerSymbolics.includes('2a√57/19') &&
    consoleErrors.length === 0 &&
    pageErrors.length === 0;

  scenarios.push({
    id: 'outcome_c_unseen_external_new_ext_01',
    outcomeCategory: 'C_USER_CORRECTED',
    imageId: 'new_ext_01_vmmu_full_r313',
    viewport: '1440x900@1',
    elapsedMs: Date.now() - t0,
    prepareStatus: prepJson?.status,
    serverStatus: analyzeJson?.route_d?.status,
    ...stateAfterConfirm,
    apiCalls,
    consoleErrors,
    pageErrors,
    pass,
  });
  await ctx.close();
}

// 5. Diagram-Only Facts Guard (`ext_prt_15_vmmu_page_r28`) -> Blocks Automatic Solve, No False Scene3D
{
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 200)); });
  page.on('pageerror', (e) => pageErrors.push(String(e).slice(0, 200)));

  await page.goto(`${url}/`, { waitUntil: 'networkidle' });
  const fileInput = await page.$('input[type=file]');
  await fileInput.setInputFiles(filePayload(join(cacheDir, 'vmmu_page_r28_Math_0399_test_080_question_35_page_5_key_A_vqa.png')));
  await page.waitForTimeout(300);

  const prepProm = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/input/prepare', { timeout: 30000 });
  await page.click('#btn-composer-send');
  const prepJson = await (await prepProm).json();
  await page.waitForSelector('#photo-span-review', { timeout: 10000 });
  const stateBlocked = await measureOrbitAndState(page);
  const pass =
    prepJson?.status === 'needs_confirmation' &&
    !stateBlocked.hasCanvas &&
    !stateBlocked.active &&
    consoleErrors.length === 0 &&
    pageErrors.length === 0;

  scenarios.push({
    id: 'diagram_dependency_guard_ext15',
    outcomeCategory: 'BLOCKED_FOR_CONFIRMATION',
    imageId: 'ext_prt_15_vmmu_page_r28',
    viewport: '1440x900@1',
    prepareStatus: prepJson?.status,
    reasonCode: prepJson?.reason_code,
    ...stateBlocked,
    consoleErrors,
    pageErrors,
    pass,
  });
  await ctx.close();
}

const summary = {
  total_scenarios: scenarios.length,
  passed_scenarios: scenarios.filter((s) => s.pass).length,
  all_passed: scenarios.every((s) => s.pass),
  provider_calls: 0,
};

const out = {
  browser: browser.version(),
  summary,
  scenarios,
};

writeFileSync(outJson, JSON.stringify(out, null, 2));
await browser.close();
server.close();
console.log(JSON.stringify(summary));
for (const s of scenarios) {
  console.log(s.id, 'pass:', s.pass, 'ans:', s.allAnswerSymbolics, 'canvas:', s.hasCanvas);
}
