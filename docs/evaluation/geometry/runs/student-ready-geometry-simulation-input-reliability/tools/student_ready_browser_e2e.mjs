// Real Chromium 4-Viewport Student Experience E2E for `student-ready-geometry-simulation-input-reliability`.
// Runs against unchanged built `frontend/dist` + isolated loopback `uvicorn`
// (`HYBRID_ROUTE_MODE=local-first`, `ALLOW_LIVE_AI=0`, `GEMINI_API_KEY=""`, real local OCR worker, temp SQLite DB).
// Automated browser E2E verification, NOT a human learner study (`AUTOMATED_BROWSER_NOT_HUMAN_STUDY`).
// `FRONTEND_INTEGRATION = BLOCKED_OWNERSHIP` · `Gate C = BLOCKED_OWNERSHIP`.

import { chromium } from 'file:///D:/Documents/projects/algo-sim/frontend/node_modules/playwright/index.mjs';
import { createServer, request } from 'node:http';
import { createServer as createNetServer } from 'node:net';
import { spawn, execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, copyFileSync, existsSync, unlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, resolve, join, extname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const RUN_DIR = resolve(__dirname, '..');
const WORKTREE_ROOT = resolve(__dirname, '../../../../../..');
const PYTHON_EXE = 'D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe';
const LOCAL_OCR_PYTHON = resolve(WORKTREE_ROOT, '.superpowers/ocr-venv/Scripts/python.exe');
const LOCAL_OCR_TESSDATA = resolve(WORKTREE_ROOT, '.superpowers/tessdata_fast');
const R537_IMAGE_PATH = resolve(
  WORKTREE_ROOT,
  '.superpowers/external_image_cache/controlled-vision-vmmu/r537_Math_0264_test_048_question_39_page_4_key_C_vqa.png',
);
const DIST_DIR = resolve(WORKTREE_ROOT, 'frontend/dist');

const runStamp = `${process.pid}_${Date.now()}`;
const tempDbPath = join(tmpdir(), `axo_student_ready_e2e_${runStamp}.sqlite3`);
const tempOcrR537JpgPath = join(tmpdir(), `axo_student_ready_r537_${runStamp}.jpg`);
const tempMultiSheetPngPath = join(tmpdir(), `axo_student_ready_multisheet_${runStamp}.png`);

const VIEWPORTS = [
  [1920, 1080],
  [1366, 768],
  [768, 1024],
  [390, 844],
];

const TECH_TOKEN_RE =
  /(?:@[A-Za-z0-9_]+|\b[scqpfgd]\d+\b|[a-z]+_[a-z_]+|[A-Z]{2,}_[A-Z_]+|\$\.|[{}]|Traceback|(?:Key|Value|Type|Runtime|Assertion|Geometry)Error\b|__|ALLOW_LIVE_AI|GEMINI)/;

const CASES = {
  vmmu_r254: {
    text:
      "Câu 45: Cho hình lăng trụ ABC.A'B'C' có AA' = 2√13a, tam giác ABC vuông tại C và ∠ABC = 30°, " +
      "góc giữa cạnh bên CC' và mặt đáy (ABC) bằng 60°. Hình chiếu vuông góc của B' lên mặt phẳng (ABC) " +
      "trùng với trọng tâm của tam giác ABC. Thể tích của khối tứ diện A'ABC theo a bằng",
    expectedAnswer: '9a³√13/2',
    forbiddenAnswersInUi: ['9a³√13/2', '9√13/2'],
  },
  vmmu_r277: {
    text:
      'Câu 44. Cho tứ diện OABC vuông tại O có OA = 2a, OB = 3a, OC = 4a. ' +
      'Gọi M, N, P lần lượt là điểm đối xứng với điểm O qua trung điểm ba cạnh AB, BC, CA của tam giác ABC. ' +
      'Thể tích của tứ diện OMNP bằng',
    expectedAnswer: '8a³',
    forbiddenAnswersInUi: ['8a³'],
  },
  mode_a_trig: {
    text:
      'Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC) và SA = a. ' +
      'Tính cosin của góc giữa SB và mặt phẳng (ABC).',
    expectedAnswer: '√2/2',
    forbiddenAnswersInUi: ['cos=√2/2', '√2/2'],
  },
  refusal_cap_70deg: {
    text:
      'Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC), ' +
      'góc giữa SB và mặt phẳng (ABC) bằng 70°. Tính thể tích khối chóp S.ABC.',
    expectedCategory: 'capability_gap',
    expectedReason: 'EXACT_DOMAIN_EXCEEDED',
    expectTextRe: /chưa\s+(?:được\s+)?hỗ\s+trợ/i,
  },
};

function getFreePort() {
  return new Promise((ok, fail) => {
    const srv = createNetServer();
    srv.listen(0, '127.0.0.1', () => {
      const { port } = srv.address();
      srv.close((err) => (err ? fail(err) : ok(port)));
    });
    srv.on('error', fail);
  });
}

function queryProvenanceAndPrepareMultiPng(multiPngPath) {
  const pyCode = `
import json, pathlib, subprocess, sys
sys.path.insert(0, "backend")
sys.path.insert(0, "backend/scripts")
from PIL import Image, ImageDraw, ImageFont
import freeze_evaluation_candidate as fec
from app.main import CACHE_VERSION, ROUTE_D_CACHE_POLICY

wt = pathlib.Path(".").resolve()
im = Image.new("RGB", (1750, 1020), "white")
draw = ImageDraw.Draw(im)
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 40)
draw.text((60, 50), "Câu 1. Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a,", fill="black", font=font)
draw.text((60, 115), "SA vuông góc với mặt phẳng (ABCD) và SA = 2a.", fill="black", font=font)
draw.text((60, 180), "Tính thể tích khối chóp S.ABCD.", fill="black", font=font)
draw.text((60, 260), "A. 8a³/3          B. 4a³          C. 2a³          D. a³", fill="black", font=font)

draw.text((60, 620), "Câu 2. Cho hình lập phương MNPQ.M'N'P'Q' cạnh 3a.", fill="black", font=font)
draw.text((60, 685), "Tính thể tích khối lập phương MNPQ.M'N'P'Q'.", fill="black", font=font)
draw.text((60, 765), "A. 27a³           B. 9a³          C. 6a³          D. 3a³", fill="black", font=font)
im.save(sys.argv[1], format="PNG")

head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=wt, text=True).strip()
p_commit = fec.product_commit()
m_hash, m_count = fec.measured_system_hash()
print(json.dumps({
    "git_head_sha": head_sha,
    "product_commit": p_commit,
    "measured_system_hash": m_hash,
    "measured_system_file_count": int(m_count),
    "cache_version": str(CACHE_VERSION),
    "route_d_cache_policy": str(ROUTE_D_CACHE_POLICY),
}))
`;
  const raw = execFileSync(PYTHON_EXE, ['-B', '-c', pyCode, multiPngPath], {
    cwd: WORKTREE_ROOT,
    env: {
      ...process.env,
      PYTHONPATH: 'backend',
      ALLOW_LIVE_AI: '0',
      GEMINI_API_KEY: '',
      HYBRID_ROUTE_MODE: 'local-first',
      PYTHONIOENCODING: 'utf-8',
    },
    encoding: 'utf-8',
  });
  return JSON.parse(raw.trim().split('\n').at(-1));
}

async function waitForHealth(port, timeoutMs = 45000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const res = await new Promise((ok) => {
      const req = request({ host: '127.0.0.1', port, path: '/api/health', method: 'GET' }, (up) => {
        let data = '';
        up.on('data', (chunk) => { data += chunk; });
        up.on('end', () => ok({ status: up.statusCode, body: data }));
      });
      req.on('error', () => ok(null));
      req.end();
    });
    if (res && res.status === 200) {
      try { return JSON.parse(res.body); } catch { /* retry */ }
    }
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error(`Loopback uvicorn on 127.0.0.1:${port} did not pass /api/health within ${timeoutMs}ms`);
}

function killProcessTree(proc) {
  if (!proc || proc.pid == null) return;
  try {
    if (process.platform === 'win32') {
      execFileSync('taskkill', ['/PID', String(proc.pid), '/T', '/F'], { stdio: 'ignore' });
    } else {
      proc.kill('SIGTERM');
    }
  } catch { /* ignore */ }
}

let sysMeta = null;
let uvicornProc = null;
let server = null;
let browser = null;
let healthPayload = null;
let fatalError = null;
let liveProviderRequestCount = 0;

const report = {
  schema: 'axo-student-ready-browser-e2e/1',
  run_id: 'student-ready-geometry-simulation-input-reliability',
  generated_at_utc: null,
  category: 'AUTOMATED_BROWSER_NOT_HUMAN_STUDY',
  frontend_integration: 'BLOCKED_OWNERSHIP',
  gate_c: 'BLOCKED_OWNERSHIP',
  provenance: null,
  viewports: [],
  multi_problem_sheet_1366x768: null,
  camera_orbit_1920x1080: null,
  verdict: 'FAIL',
};

try {
  copyFileSync(R537_IMAGE_PATH, tempOcrR537JpgPath);
  sysMeta = queryProvenanceAndPrepareMultiPng(tempMultiSheetPngPath);

  const backendPort = await getFreePort();
  const sqliteUrl = `sqlite:///${tempDbPath.replace(/\\/g, '/')}`;

  uvicornProc = spawn(
    PYTHON_EXE,
    ['-B', '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(backendPort), '--log-level', 'warning'],
    {
      cwd: WORKTREE_ROOT,
      env: {
        ...process.env,
        PYTHONPATH: 'backend',
        HYBRID_ROUTE_MODE: 'local-first',
        ALLOW_LIVE_AI: '0',
        GEMINI_API_KEY: '',
        DATABASE_URL: sqliteUrl,
        LOCAL_OCR_PYTHON,
        LOCAL_OCR_TESSDATA,
        PYTHONIOENCODING: 'utf-8',
      },
      stdio: 'ignore',
    },
  );
  healthPayload = await waitForHealth(backendPort, 45000);

  server = createServer((req, res) => {
    const pathname = new URL(req.url, 'http://localhost').pathname;
    if (pathname.startsWith('/api/')) {
      const proxy = request(
        { host: '127.0.0.1', port: backendPort, path: req.url, method: req.method, headers: req.headers },
        (up) => {
          res.writeHead(up.statusCode, up.headers);
          up.pipe(res);
        },
      );
      proxy.on('error', () => {
        if (!res.headersSent) res.writeHead(502);
        res.end();
      });
      req.pipe(proxy);
      return;
    }
    const file = join(DIST_DIR, pathname.includes('.') ? pathname : 'index.html');
    if (!file.startsWith(DIST_DIR) || !existsSync(file)) {
      res.writeHead(404);
      res.end();
      return;
    }
    res.setHeader(
      'Content-Type',
      { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml' }[extname(file)] ??
        'application/octet-stream',
    );
    const buf = readFileSync(file);
    res.setHeader('Content-Length', buf.length);
    if (pathname.startsWith('/assets/')) {
      res.setHeader('Cache-Control', 'public, max-age=3600');
    }
    res.end(buf);
  });
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const ORIGIN = `http://127.0.0.1:${server.address().port}`;

  browser = await chromium.launch({
    channel: 'chrome',
    headless: true,
    args: ['--js-flags=--expose-gc'],
  });

  const frames = (page, n = 2) =>
    page.evaluate(
      (k) => new Promise((ok) => {
        const step = (i) => (i ? requestAnimationFrame(() => step(i - 1)) : ok());
        step(k);
      }),
      n,
    );

  const textIfPresent = async (loc) => ((await loc.count()) ? await loc.first().innerText().catch(() => null) : null);

  const counter = async (page) => {
    const raw = (await textIfPresent(page.locator('#pa-counter'))) ?? '';
    const m = raw.match(/(\d+)\s*\/\s*(\d+)/);
    return m ? [Number(m[1]), Number(m[2])] : null;
  };

  async function registerFreshAccount(page) {
    const status = await page.evaluate(async () => {
      const r = await fetch('/api/auth/register', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: `sr-e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.invalid`,
          displayName: 'StudentReadyE2E',
          password: crypto.randomUUID(),
        }),
      });
      return r.status;
    });
    await page.reload({ waitUntil: 'networkidle' });
    return status;
  }

  async function ensureHomeComposer(page, { clearAttachments = false, clearText = false } = {}) {
    const box = page.locator('#home-problem-input');
    if (!(await box.isVisible().catch(() => false))) {
      const changeBtn = page.locator('#btn-header-change-prob');
      if (await changeBtn.count()) {
        await changeBtn.first().click();
      } else {
        await page.getByRole('button', { name: 'Đổi đề toán' }).first().click();
      }
      await box.waitFor({ timeout: 15000 });
    }
    if (clearAttachments) {
      for (let i = 0; i < 10; i++) {
        const rm = page.locator('.file-card-remove').first();
        if (!(await rm.count())) break;
        await rm.click().catch(() => {});
        await frames(page);
      }
    }
    if (clearText) {
      await box.waitFor({ state: 'visible', timeout: 10000 });
      await page.waitForFunction(
        () => {
          const el = document.querySelector('#home-problem-input');
          return el && !el.hasAttribute('readonly');
        },
        null,
        { timeout: 15000 },
      );
      await box.fill('');
    }
    return box;
  }

  async function loadTextAndWaitScene(page, text) {
    const box = await ensureHomeComposer(page, { clearAttachments: true, clearText: true });
    await box.fill(text);
    const respPromise = page.waitForResponse(
      (r) => new URL(r.url()).pathname === '/api/analyze' && r.request().method() === 'POST',
      { timeout: 120000 },
    );
    const t0 = Date.now();
    await page.locator('#btn-composer-send').click();
    const r = await respPromise;
    const body = await r.json();
    await page.waitForSelector('#pa-counter', { timeout: 60000 });
    await page.waitForFunction(
      () => [...document.querySelectorAll('canvas')].some((c) => c.width > 0 && c.height > 0 && c.offsetParent),
      null,
      { timeout: 60000 },
    );
    await frames(page, 3);
    return { body, httpStatus: r.status(), ms: Date.now() - t0 };
  }

  async function walkTimeline(page) {
    let c = await counter(page);
    for (let i = 0; i < 40 && c && c[0] > 1; i++) {
      await page.click('#pa-prev');
      await frames(page);
      c = await counter(page);
    }
    const steps = [];
    for (let i = 0; i < 40; i++) {
      c = await counter(page);
      const stepRows = (await page.locator('#dock-steps-ul li').allInnerTexts().catch(() => [])).join(' ');
      steps.push({
        step: c?.[0] ?? null,
        of: c?.[1] ?? null,
        has_tech_leak: TECH_TOKEN_RE.test(stepRows),
      });
      if (!c || c[0] >= c[1] || (await page.isDisabled('#pa-next'))) break;
      await page.click('#pa-next');
      await frames(page);
    }
    return steps;
  }

  async function checkZeroSpoiler(page, forbiddenAnswers) {
    const visibleOutside = await page.evaluate(() => {
      const clone = document.body.cloneNode(true);
      clone.querySelectorAll('#dock-prob-statement, #home-problem-input').forEach((n) => n.remove());
      return clone.innerText;
    });
    const leaked = (forbiddenAnswers ?? []).filter((a) => visibleOutside.includes(a));
    const cos2Leak = /cos²\s*=\s*\d/.test(visibleOutside);
    const abcdCount = await page.locator('[data-abcd-choice], .mcq-answer-picker, input[name="abcd-answer"]').count();
    return {
      leaked,
      cos2_leak: cos2Leak,
      abcd_picker_count: abcdCount,
      pass: leaked.length === 0 && !cos2Leak && abcdCount === 0,
    };
  }

  for (const [w, h] of VIEWPORTS) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h } });
    const page = await ctx.newPage();
    const pageErrors = [];
    const consoleErrors = [];
    const failedRequests = [];
    page.on('pageerror', (e) => pageErrors.push(e.name + ': ' + String(e.message).slice(0, 140)));
    page.on('requestfailed', (req) => {
      failedRequests.push({ url: req.url(), error: req.failure()?.errorText ?? null });
    });
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const txt = msg.text();
        if (!txt.includes('401') && !txt.includes('favicon')) {
          consoleErrors.push(txt.slice(0, 160));
        }
      }
    });

    await page.goto(ORIGIN, { waitUntil: 'networkidle' });
    const regStatus = await registerFreshAccount(page);

    // 1. Promoted vmmu_r254 + timeline walk + spoiler check
    const r254 = await loadTextAndWaitScene(page, CASES.vmmu_r254.text);
    const steps254 = await walkTimeline(page);
    const spoiler254 = await checkZeroSpoiler(page, CASES.vmmu_r254.forbiddenAnswersInUi);
    const cMetrics254 = await page.evaluate(() => {
      const cvs = document.querySelector('canvas');
      const r = cvs ? cvs.getBoundingClientRect() : null;
      return {
        canvas_w: r?.width ?? 0,
        canvas_h: r?.height ?? 0,
        overflow_px: document.documentElement.scrollWidth - window.innerWidth,
      };
    });

    // Camera orbit check once at 1920x1080
    if (w === 1920) {
      const snap = () => page.evaluate(() => JSON.stringify(window.__geo3d_camera_snapshot ?? null));
      const cvs = page.locator('canvas').first();
      const box = await cvs.boundingBox();
      const cx = box.x + Math.round(box.width * 0.4);
      const cy = box.y + Math.round(box.height * 0.4);
      const s0 = await snap();
      await page.mouse.move(cx, cy);
      await page.mouse.down();
      await page.mouse.move(cx + 85, cy + 20, { steps: 6 });
      await page.mouse.up();
      await frames(page, 3);
      const s1 = await snap();
      report.camera_orbit_1920x1080 = { changed: s0 !== null && s1 !== null && s0 !== s1 };
    }

    // 2. Promoted vmmu_r277 (point_reflection) + timeline walk + stale check
    const r277 = await loadTextAndWaitScene(page, CASES.vmmu_r277.text);
    const steps277 = await walkTimeline(page);
    const spoiler277 = await checkZeroSpoiler(page, CASES.vmmu_r277.forbiddenAnswersInUi);
    const staleIn277 = await page.evaluate(() => document.body.innerText.includes('2√13a'));

    // 3. Mode A trig problem -> Scene3D + numeric-goal note + zero trig answer leak
    const rTrig = await loadTextAndWaitScene(page, CASES.mode_a_trig.text);
    const spoilerTrig = await checkZeroSpoiler(page, CASES.mode_a_trig.forbiddenAnswersInUi);
    const numericNoteCount = await page.locator('#stage-numeric-goal-note').count();

    // 4. OCR image upload & span confirmation flow -> Scene3D
    await ensureHomeComposer(page, { clearAttachments: true, clearText: true });
    await page.locator('#home-file-input').setInputFiles(tempOcrR537JpgPath);
    await page.locator('.file-preview-card:not(.is-loading)').first().waitFor({ timeout: 15000 });
    await page.locator('#btn-composer-send:not([disabled])').waitFor({ timeout: 15000 });
    const prepPromise = page.waitForResponse(
      (r) => new URL(r.url()).pathname === '/api/input/prepare' && r.request().method() === 'POST',
      { timeout: 120000 },
    );
    await page.locator('#btn-composer-send').click();
    const prepBody = await (await prepPromise).json();
    if (Number(prepBody?.metrics?.vlm_calls ?? 0) > 0) liveProviderRequestCount += Number(prepBody.metrics.vlm_calls);
    let ocrAnalyzeBody = null;
    if (prepBody.status === 'needs_confirmation') {
      await page.locator('#composer-extraction-confirm').waitFor({ timeout: 20000 });
      const spanBtns = page.locator('#composer-extraction-confirm [data-span-ok]');
      for (let i = 0; i < await spanBtns.count(); i++) {
        const b = spanBtns.nth(i);
        if ((await b.getAttribute('aria-pressed')) !== 'true') await b.click();
      }
      const chk = page.locator('#chk-confirm-extracted-text');
      if (!(await chk.isChecked())) await chk.check();
      await frames(page, 2);
      const anPromise = page.waitForResponse(
        (r) => new URL(r.url()).pathname === '/api/analyze' && r.request().method() === 'POST',
        { timeout: 120000 },
      );
      await page.locator('#btn-confirm-extracted-build').click();
      ocrAnalyzeBody = await (await anPromise).json();
      await page.waitForSelector('#pa-counter', { timeout: 60000 });
      await page.waitForFunction(
        () => [...document.querySelectorAll('canvas')].some((c) => c.width > 0 && c.height > 0 && c.offsetParent),
        null,
        { timeout: 60000 },
      );
      await frames(page, 2);
    }

    // Multi-problem sheet test once on 1366x768
    if (w === 1366) {
      await ensureHomeComposer(page, { clearAttachments: true, clearText: true });
      await page.locator('#home-file-input').setInputFiles(tempMultiSheetPngPath);
      await page.locator('.file-preview-card:not(.is-loading)').first().waitFor({ timeout: 15000 });
      await page.locator('#btn-composer-send:not([disabled])').waitFor({ timeout: 15000 });
      const mpPrepPromise = page.waitForResponse(
        (r) => new URL(r.url()).pathname === '/api/input/prepare' && r.request().method() === 'POST',
        { timeout: 120000 },
      );
      await page.locator('#btn-composer-send').click();
      const mpPrep = await (await mpPrepPromise).json();
      await page.locator('#composer-candidate-picker [data-candidate-id]').first().waitFor({ timeout: 15000 });
      const candCount = await page.locator('#composer-candidate-picker [data-candidate-id]').count();
      const nextPrepP = page.waitForResponse(
        (r) => new URL(r.url()).pathname === '/api/input/prepare' && r.request().method() === 'POST',
        { timeout: 120000 },
      );
      const mpAnP = page.waitForResponse(
        (r) => new URL(r.url()).pathname === '/api/analyze' && r.request().method() === 'POST',
        { timeout: 120000 },
      );
      await page.locator('#composer-candidate-picker [data-candidate-id]').first().click();
      const picked = await (await nextPrepP).json();
      if (picked.status === 'ready') {
        await mpAnP.catch(() => null);
        await page.waitForSelector('#pa-counter', { timeout: 60000 }).catch(() => {});
      }
      const isolatedFromQ2 = !(picked.problem_text ?? '').includes('MNPQ') && !(picked.problem_text ?? '').includes('Câu 2');
      report.multi_problem_sheet_1366x768 = {
        prepare_status: mpPrep.status,
        candidate_count: candCount,
        picked_status: picked.status,
        zero_neighbor_bleed: isolatedFromQ2,
        pass: mpPrep.status === 'needs_selection' && candCount >= 2 && isolatedFromQ2,
      };
    }

    // 5. Honest refusal check
    const refBox = await ensureHomeComposer(page, { clearAttachments: true, clearText: true });
    await refBox.fill(CASES.refusal_cap_70deg.text);
    const refRespP = page.waitForResponse(
      (r) => new URL(r.url()).pathname === '/api/analyze' && r.request().method() === 'POST',
      { timeout: 60000 },
    );
    await page.locator('#btn-composer-send').click();
    const refBody = await (await refRespP).json();
    await page.locator('[data-toast-id="composer-refusal"]').waitFor({ timeout: 10000 }).catch(() => {});
    await frames(page, 2);
    const toastText = (await textIfPresent(page.locator('[data-toast-id="composer-refusal"]'))) ?? '';
    const refCanvas = await page.locator('canvas').count();
    const refEnv = refBody?.envelope ?? refBody ?? {};
    const refClean = !TECH_TOKEN_RE.test(toastText) && CASES.refusal_cap_70deg.expectTextRe.test(toastText);

    const vpResult = {
      viewport: `${w}x${h}`,
      reg_status: regStatus,
      vmmu_r254: {
        served: r254.body?.route_d?.status === 'SERVED',
        answer_verified_hidden: r254.body?.route_d?.answers?.q1 ?? null,
        steps: steps254.length,
        spoiler_pass: spoiler254.pass,
        ...cMetrics254,
      },
      vmmu_r277: {
        served: r277.body?.route_d?.status === 'SERVED',
        answer_verified_hidden: r277.body?.route_d?.answers?.q1 ?? null,
        steps: steps277.length,
        spoiler_pass: spoiler277.pass,
        stale_prev: staleIn277,
      },
      mode_a_trig: {
        served: rTrig.body?.route_d?.status === 'SERVED',
        numeric_goal_note: numericNoteCount > 0,
        spoiler_pass: spoilerTrig.pass,
      },
      ocr_confirmation: {
        prepare_status: prepBody.status,
        served: ocrAnalyzeBody?.route_d?.status === 'SERVED',
        answer_verified_hidden: ocrAnalyzeBody?.route_d?.answers?.q1 ?? null,
      },
      honest_refusal: {
        status: refEnv.status,
        category: refEnv.failure_category,
        reason_code: refEnv.reason_code,
        canvas_count: refCanvas,
        toast_clean: refClean,
        toast_text: toastText,
      },
      page_errors: pageErrors,
      console_errors: consoleErrors,
      failed_requests: failedRequests,
      pass:
        regStatus === 200 &&
        r254.body?.route_d?.status === 'SERVED' &&
        r254.body?.route_d?.answers?.q1 === CASES.vmmu_r254.expectedAnswer &&
        steps254.length > 0 &&
        steps254.every((s) => !s.has_tech_leak) &&
        cMetrics254.canvas_w >= 200 &&
        cMetrics254.canvas_h >= 180 &&
        cMetrics254.overflow_px <= 0 &&
        spoiler254.pass &&
        r277.body?.route_d?.status === 'SERVED' &&
        r277.body?.route_d?.answers?.q1 === CASES.vmmu_r277.expectedAnswer &&
        steps277.length > 0 &&
        !staleIn277 &&
        spoiler277.pass &&
        rTrig.body?.route_d?.status === 'SERVED' &&
        numericNoteCount > 0 &&
        spoilerTrig.pass &&
        prepBody.status === 'needs_confirmation' &&
        ocrAnalyzeBody?.route_d?.status === 'SERVED' &&
        refEnv.status === 'unsupported' &&
        refEnv.failure_category === CASES.refusal_cap_70deg.expectedCategory &&
        refEnv.reason_code === CASES.refusal_cap_70deg.expectedReason &&
        refCanvas === 0 &&
        refClean &&
        pageErrors.length === 0 &&
        consoleErrors.length === 0,
    };
    report.viewports.push(vpResult);
    console.log(JSON.stringify({ viewport: vpResult.viewport, pass: vpResult.pass, errs: pageErrors.length + consoleErrors.length }));
    await ctx.close();
  }
} catch (err) {
  fatalError = String(err?.stack ?? err);
  console.error(fatalError);
} finally {
  if (browser) await browser.close().catch(() => {});
  if (server) await new Promise((r) => server.close(() => r())).catch(() => {});
  killProcessTree(uvicornProc);
  await new Promise((r) => setTimeout(r, 400));

  for (const f of [tempDbPath, `${tempDbPath}-wal`, `${tempDbPath}-shm`, tempOcrR537JpgPath, tempMultiSheetPngPath]) {
    if (existsSync(f)) {
      try { unlinkSync(f); } catch { /* ignore */ }
    }
  }
  const tempCleanedUp = !existsSync(tempDbPath) && !existsSync(tempOcrR537JpgPath) && !existsSync(tempMultiSheetPngPath);

  report.generated_at_utc = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
  report.provenance = {
    ...sysMeta,
    frontend_dist_dir: 'frontend/dist',
    loopback_mode: 'HYBRID_ROUTE_MODE=local-first, ALLOW_LIVE_AI=0, GEMINI_API_KEY=""',
    health_has_key: healthPayload?.hasKey ?? null,
    live_provider_calls: liveProviderRequestCount,
    temp_files_cleaned_up: tempCleanedUp,
    fatal_error: fatalError,
  };

  const overallPass =
    fatalError === null &&
    liveProviderRequestCount === 0 &&
    healthPayload?.hasKey === false &&
    tempCleanedUp &&
    report.viewports.length === 4 &&
    report.viewports.every((v) => v.pass) &&
    Boolean(report.multi_problem_sheet_1366x768?.pass) &&
    Boolean(report.camera_orbit_1920x1080?.changed);

  report.verdict = overallPass ? 'PASS' : 'FAIL';
  writeFileSync(join(RUN_DIR, 'browser_e2e_4viewports.json'), JSON.stringify(report, null, 2) + '\n', 'utf-8');
  console.log(JSON.stringify({ verdict: report.verdict, tempCleanedUp, liveProviderRequestCount }));
  if (!overallPass) process.exitCode = 1;
}
