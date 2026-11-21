// Real Chromium Student Pilot E2E for simulation-first-mvp-stabilization (`Phase D & E3`).
// Exercises production `frontend/dist` against isolated loopback `uvicorn`
// (`HYBRID_ROUTE_MODE=local-first`, `ALLOW_LIVE_AI=0`, `GEMINI_API_KEY=""`, zero live AI calls, temp SQLite DB).
// Automated browser E2E verification, NOT a human learner study (`AUTOMATED_BROWSER_NOT_HUMAN_STUDY`).
//
// Usage (from worktree root):
//   node docs/evaluation/geometry/runs/simulation-first-mvp-stabilization/tools/student_pilot_e2e.mjs

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
const tempDbPath = join(tmpdir(), `axo_pilot_e2e_${runStamp}.sqlite3`);
const tempOcrR537JpgPath = join(tmpdir(), `axo_pilot_r537_${runStamp}.jpg`);
const tempMultiSheetPngPath = join(tmpdir(), `axo_pilot_multisheet_${runStamp}.png`);

const VIEWPORTS = [
  [1920, 1080],
  [1366, 768],
  [768, 1024],
  [390, 844],
];

const TECH =
  /[a-z]+_[a-z_]+|[A-Z]{2,}_[A-Z_]+|\$\.|[{}]|Traceback|\bError\b|__|ALLOW_LIVE_AI|GEMINI|reason_code|\bc\d+\b/;
const MISSING_DATA_CLAIM_RE = /thiếu\s+dữ\s+kiện|chưa\s+đủ\s+dữ\s+kiện|chưa\s+đủ\s+kích\s+thước/iu;
const REWRITE_ADVICE_RE =
  /viết\s+phần\s+đó\s+rõ\s+hơn|bổ\s+sung.*(?:dữ\s+kiện|kích\s+thước|giả\s+thiết)|thêm.*giả\s+thiết/iu;

const CASES = {
  r537_pyramid_distance: {
    text:
      'Cho hình chóp tứ giác đều S.ABCD có độ dài cạnh bên bằng a và diện tích đáy bằng a². ' +
      'Tính khoảng cách từ A đến mặt phẳng (SBC).',
    expectedAnswer: 'a√6/3',
    expectedNumericNote: false,
    expectedIllusNote: false,
    forbiddenAnswersInUi: ['a√6/3', '√6/3'],
  },
  r463_undotted_prism_volume: {
    text:
      "Câu 43. Cho khối lăng trụ đứng ABCDA'B'C'D' có đáy ABCD là hình thoi, ∠BAD = 60°, " +
      "cạnh bên AA' = 2a và AC' hợp với đáy góc 30°. Thể tích khối lăng trụ đã cho bằng",
    expectedAnswer: '4a³√3',
    expectedObjects: ['day_ABCD', 'day_A_primeB_primeC_primeD_prime', 'canh_ben_A_A_prime', 'canh_ben_C_C_prime'],
    expectedMinScenePerpWitnesses: 4,
    forbiddenAnswersInUi: ['4a³√3', '4√3'],
  },
  cos_line_plane: {
    text:
      'Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC) ' +
      'và SA = a. Tính cosin của góc giữa SB và mặt phẳng (ABC).',
    expectedAnswer: '√2/2',
    expectedNumericNote: true,
    expectedIllusNote: false,
    forbiddenAnswersInUi: ['cos=√2/2'],
  },
  multi_top_cuboid: {
    text:
      'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, ' +
      'SA vuông góc với mặt phẳng (ABCD) và SA = 2a. Tính thể tích khối chóp S.ABCD.',
    expectedAnswer: '8a³/3',
    forbiddenAnswersInUi: ['8a³/3'],
  },
  cap_oblique_triangle: {
    text:
      'Cho hình chóp S.ABC có SA vuông góc với mặt phẳng (ABC), SA = 3, AB = 3, BC = 4 ' +
      'và góc ABC bằng 30°. Tính thể tích khối chóp S.ABC.',
  },
  cap_non_special_70deg: {
    text:
      'Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC), ' +
      'góc giữa SB và mặt phẳng (ABC) bằng 70°. Tính thể tích khối chóp S.ABC.',
  },
  true_missing_dimension: {
    text:
      'Cho hình chóp S.ABCD có đáy ABCD là hình vuông, SA vuông góc với mặt phẳng đáy. ' +
      'Tính thể tích khối chóp S.ABCD.',
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

function querySystemProvenanceAndPrepareImages(multiPngPath) {
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

function stats(arr) {
  const clean = arr.filter((x) => typeof x === 'number' && Number.isFinite(x)).sort((a, b) => a - b);
  if (clean.length === 0) return { count: 0, median: null, min: null, max: null };
  const mid = Math.floor(clean.length / 2);
  const median = clean.length % 2 === 1 ? clean[mid] : Math.round(((clean[mid - 1] + clean[mid]) / 2) * 100) / 100;
  return { count: clean.length, median, min: clean[0], max: clean[clean.length - 1] };
}

let sysMeta = {
  git_head_sha: null,
  product_commit: null,
  measured_system_hash: null,
  measured_system_file_count: null,
  cache_version: null,
  route_d_cache_policy: null,
};
let uvicornProc = null;
let server = null;
let browser = null;
let healthPayload = null;
let fatalError = null;
let liveProviderRequestCount = 0;

const report = {
  schema: 'axo-student-pilot-e2e/1',
  run_id: 'simulation-first-mvp-stabilization',
  phase: 'phase_d_e3_real_chromium_student_pilot_e2e',
  generated_at_utc: null,
  category: 'AUTOMATED_BROWSER_NOT_HUMAN_STUDY',
  physical_low_end: 'PHYSICAL_LOW_END_NOT_MEASURED',
  dataset_partition: 'DEVELOPMENT_EXPOSED_AND_SYNTHETIC_E2E_PROBES_ONLY',
  provenance: null,
  d1_complete_student_journey: null,
  d2_image_ocr_and_multiproblem: null,
  d3_responsive_4_viewports: [],
  d4_refusal_honesty: [],
  d5_zero_solver_spoiler_summary: null,
  e3_latency_telemetry: null,
  verdict: 'FAIL',
};

try {
  copyFileSync(R537_IMAGE_PATH, tempOcrR537JpgPath);
  sysMeta = querySystemProvenanceAndPrepareImages(tempMultiSheetPngPath);

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
    res.end(readFileSync(file));
  });
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const ORIGIN = `http://127.0.0.1:${server.address().port}`;

  browser = await chromium.launch({
    channel: 'chrome',
    headless: true,
    args: ['--js-flags=--expose-gc', '--enable-precise-memory-info'],
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

  async function registerFreshAccount(page, reloadAfter = true) {
    const status = await page.evaluate(async () => {
      const r = await fetch('/api/auth/register', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: `pilot-e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.invalid`,
          displayName: 'PilotStudent',
          password: crypto.randomUUID(),
        }),
      });
      return r.status;
    });
    if (reloadAfter) await page.reload({ waitUntil: 'networkidle' });
    return status;
  }

  async function checkLightMode(page) {
    return page.evaluate(() => {
      const parseRgb = (s) => {
        const m = String(s).match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
        if (!m) return null;
        return [Number(m[1]), Number(m[2]), Number(m[3]), m[4] === undefined ? 1 : Number(m[4])];
      };
      const lum = ([r, g, b]) => (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
      for (const el of [document.querySelector('.axo-shell'), document.body, document.documentElement]) {
        if (!el) continue;
        const bg = getComputedStyle(el).backgroundColor;
        const rgb = parseRgb(bg);
        if (rgb && rgb[3] > 0.1) {
          return { selector: el.tagName, bg, luminance: Math.round(lum(rgb) * 1000) / 1000, is_light: lum(rgb) >= 0.85 };
        }
      }
      return { selector: 'none', bg: null, luminance: null, is_light: false };
    });
  }

  async function ensureHomeComposer(page) {
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
    return box;
  }

  async function loadText(page, text) {
    const box = await ensureHomeComposer(page);
    for (let k = 0; k < 3 && (await box.inputValue()) !== text; k++) {
      await box.fill(text);
      await page.waitForTimeout(100);
    }
    const resp = page.waitForResponse(
      (r) => new URL(r.url()).pathname === '/api/analyze' && r.request().method() === 'POST',
      { timeout: 120000 },
    );
    const t0 = Date.now();
    await page.locator('#btn-composer-send').click();
    const r = await resp;
    const body = await r.json();
    await page.waitForSelector('#pa-counter', { timeout: 60000 });
    await page.waitForFunction(
      () => [...document.querySelectorAll('canvas')].some((c) => c.width > 0 && c.height > 0 && c.offsetParent),
      null,
      { timeout: 60000 },
    );
    await frames(page, 3);
    return { body, httpStatus: r.status(), firstModelMs: Date.now() - t0 };
  }

  async function walkTimeline(page) {
    let c = await counter(page);
    for (let i = 0; i < 60 && c && c[0] > 1; i++) {
      await page.click('#pa-prev');
      await frames(page);
      c = await counter(page);
    }
    const steps = [];
    for (let i = 0; i < 60; i++) {
      c = await counter(page);
      const t = page.locator('.step-evidence-toggle[aria-expanded="false"]').first();
      if ((await t.count()) && (await t.isVisible().catch(() => false))) {
        await t.click().catch(() => {});
        await frames(page);
      }
      const stepSub = (await page.locator('#dock-steps-ul .step-detail-sub').allInnerTexts().catch(() => [])).join(' ');
      const stepRows = (await page.locator('#dock-steps-ul li').allInnerTexts().catch(() => [])).join(' ');
      const whyDrawer = (await page.locator('.geo3d-cac-buoc-vi-sao').allInnerTexts().catch(() => [])).join(' ');
      const explainText = `${stepSub} ${whyDrawer} ${stepRows}`.trim();
      steps.push({
        step: c?.[0],
        of: c?.[1],
        rendered_ids: await page.evaluate(() => window.__geo3d_rendered_object_ids ?? []),
        witness_ids: await page.evaluate(() => window.__geo3d_witness_ids ?? []),
        angle_construction_ids: await page.evaluate(() => window.__geo3d_angle_construction_ids ?? []),
        altitude_construction_ids: await page.evaluate(() => window.__geo3d_altitude_construction_ids ?? []),
        step_sub_len: stepSub.trim().length,
        why_drawer_len: whyDrawer.trim().length,
        why_drawer_text: whyDrawer.trim(),
        has_explanation: explainText.length > 0 && !TECH.test(explainText),
      });
      if (!c || c[0] >= c[1] || (await page.isDisabled('#pa-next'))) break;
      const t0 = await page.evaluate(() => performance.now());
      await page.click('#pa-next');
      await frames(page);
      steps.at(-1).next_ms = Math.round(((await page.evaluate(() => performance.now())) - t0) * 100) / 100;
    }
    return steps;
  }

  function checkPrematurePrerequisites(body, steps) {
    const events = body?.envelope?.scene3d?.events ?? [];
    const objs = body?.envelope?.scene3d?.objects ?? [];
    const prereqsById = new Map();
    for (const o of objs) {
      prereqsById.set(o.id, new Set(o.visible_prerequisites ?? []));
    }
    for (const ev of events) {
      const id = ev?.object?.id;
      if (id) {
        const s = prereqsById.get(id) ?? new Set();
        for (const d of ev.depends ?? []) s.add(d);
        prereqsById.set(id, s);
      }
    }
    const firstSeen = new Map();
    for (const st of steps) {
      for (const id of st.rendered_ids ?? []) {
        const root = String(id).split('::')[0].split('#')[0].split('__')[0];
        if (!firstSeen.has(root)) firstSeen.set(root, st.step);
      }
    }
    const objById = new Map(objs.map((o) => [o.id, o]));
    const late = [];
    for (const [root, shownStep] of firstSeen.entries()) {
      for (const dep of prereqsById.get(root) ?? []) {
        const depObj = objById.get(dep);
        if (!depObj || depObj.type === 'quantity' || depObj.type === 'solid') continue;
        const depShown = firstSeen.get(dep);
        if (depShown != null && depShown > shownStep) {
          late.push({ object: root, shownStep, missingPrereq: dep, depShown });
        }
      }
    }
    return late;
  }

  async function cameraOrbitZoomPanReset(page) {
    const snap = () => page.evaluate(() => JSON.stringify(window.__geo3d_camera_snapshot ?? null));
    const canvas = page.locator('canvas').first();
    await canvas.scrollIntoViewIfNeeded().catch(() => {});
    await frames(page, 2);
    const box = await canvas.boundingBox();
    const cx = box.x + Math.round(box.width * 0.35);
    const cy = box.y + Math.round(box.height * 0.38);
    const s0 = await snap();

    // Orbit
    await page.mouse.move(cx, cy);
    await page.mouse.down();
    const t0 = await page.evaluate(() => performance.now());
    await page.mouse.move(cx + 95, cy + 25, { steps: 8 });
    await page.mouse.up();
    await frames(page, 3);
    const orbitMs = Math.round(((await page.evaluate(() => performance.now())) - t0) * 100) / 100;
    const sOrbit = await snap();

    // Zoom
    await page.mouse.wheel(0, -320);
    await frames(page, 3);
    const sZoom = await snap();

    // Pan
    await page.mouse.move(cx, cy);
    await page.mouse.down({ button: 'right' });
    await page.mouse.move(cx + 75, cy + 32, { steps: 8 });
    await page.mouse.up({ button: 'right' });
    await frames(page, 3);
    const sPan = await snap();

    // Reset
    const resetBtn = page.locator('#btn-reset-pos');
    let resetOk = false;
    let sReset = null;
    if ((await resetBtn.count()) && (await resetBtn.isVisible().catch(() => false))) {
      await resetBtn.click();
      await frames(page, 4);
      sReset = await snap();
      resetOk = sReset === s0;
    }

    return {
      snapshot_available: s0 !== 'null',
      orbit_changes_camera: sOrbit !== s0,
      zoom_changes_camera: sZoom !== sOrbit,
      pan_changes_camera: sPan !== sZoom,
      reset_returns_to_initial: resetOk,
      orbit_ms: orbitMs,
      canvas_box: box,
    };
  }

  async function selectChipsByKind(page, sceneObjects) {
    const typeById = new Map((sceneObjects ?? []).map((o) => [o.id, o.type]));
    const more = page.locator('#btn-dock-entities-more');
    if ((await more.count()) && (await more.isVisible().catch(() => false))) {
      await more.click();
      await frames(page);
    }
    const chips = page.locator('[data-entity-chip]');
    const n = await chips.count();
    const pickedByKind = {};
    for (let i = 0; i < n; i++) {
      const chip = chips.nth(i);
      if (!(await chip.isVisible().catch(() => false))) continue;
      const id = await chip.getAttribute('data-entity-chip');
      const baseId = id?.includes('__perp_seg') ? id : id;
      const otype = typeById.get(id) ?? (id?.includes('__perp_seg') ? 'segment3' : id?.includes('__foot') ? 'point3' : 'unknown');
      const bucket =
        otype === 'point3' || otype === 'point'
          ? 'point'
          : otype === 'segment3' || otype === 'line3' || otype === 'ray3' || otype === 'segment'
            ? 'edge'
            : otype === 'polygon3' || otype === 'plane3' || otype === 'section' || otype === 'polygon' || otype === 'face'
              ? 'face'
              : null;
      if (!bucket || pickedByKind[bucket]) continue;
      await chip.click({ timeout: 5000 });
      await frames(page, 2);
      const sel = await page.evaluate(() => window.__geo3d_selected_id ?? null);
      const ctxTitle = ((await textIfPresent(page.locator('#ctx-obj-title'))) ?? '').trim();
      const ctxMountObj = (await page.locator('#dock-context-object-mount').count())
        ? await page.locator('#dock-context-object-mount').getAttribute('data-context-object')
        : null;
      const ownerRoot = (s) => (s ? String(s).split('__')[0].split('#')[0] : null);
      pickedByKind[bucket] = {
        id,
        otype,
        selected_id: sel,
        selects: sel === id,
        ctx_title: ctxTitle,
        ctx_mounted: Boolean(ctxMountObj) && ownerRoot(ctxMountObj) === ownerRoot(id) && ctxTitle.length > 0,
        ctx_tech_token: (ctxTitle.match(TECH) ?? [null])[0],
      };
      if (pickedByKind.point && pickedByKind.edge && pickedByKind.face) break;
    }
    const clearBtn = page.locator('#btn-clear-pick');
    if ((await clearBtn.count()) && (await clearBtn.isVisible().catch(() => false))) {
      await clearBtn.click().catch(() => {});
      await frames(page);
    }
    const probText = ((await textIfPresent(page.locator('#dock-prob-statement'))) ?? '').trim();
    return {
      point: pickedByKind.point ?? null,
      edge: pickedByKind.edge ?? null,
      face: pickedByKind.face ?? null,
      statement_len: probText.length,
    };
  }

  async function toggleDisplayControls(page) {
    const popBtn = page.locator('#btn-display-pop');
    const out = { aux_ok: false, axes_ok: false, grid_checkbox_ok: false, xray_ok: false };
    if ((await popBtn.count()) && (await popBtn.isVisible().catch(() => false))) {
      await popBtn.click();
      await frames(page);
      const chkAux = page.locator('#chk-aux');
      if ((await chkAux.count()) && (await chkAux.isVisible().catch(() => false))) {
        const h0 = await page.evaluate(() => (window.__geo3d_auxiliary_hidden_ids ?? []).length);
        const r0 = await page.evaluate(() => (window.__geo3d_rendered_object_ids ?? []).length);
        await chkAux.click();
        await frames(page, 2);
        const h1 = await page.evaluate(() => (window.__geo3d_auxiliary_hidden_ids ?? []).length);
        const r1 = await page.evaluate(() => (window.__geo3d_rendered_object_ids ?? []).length);
        await chkAux.click();
        await frames(page, 2);
        const h2 = await page.evaluate(() => (window.__geo3d_auxiliary_hidden_ids ?? []).length);
        out.aux_ok = (h1 !== h0 || r1 !== r0) && h2 === h0;
        out.aux = { h0, h1, h2, r0, r1 };
      }
      const chkAxes = page.locator('#chk-axes');
      if ((await chkAxes.count()) && (await chkAxes.isVisible().catch(() => false))) {
        const a0 = await page.evaluate(() => window.__geo3d_axes_visible ?? null);
        await chkAxes.click();
        await frames(page, 2);
        const a1 = await page.evaluate(() => window.__geo3d_axes_visible ?? null);
        await chkAxes.click();
        await frames(page, 2);
        const a2 = await page.evaluate(() => window.__geo3d_axes_visible ?? null);
        out.axes_ok = a0 !== null && a1 !== a0 && a2 === a0;
        out.axes = { a0, a1, a2 };
      }
      const chkGrid = page.locator('#chk-grid');
      if ((await chkGrid.count()) && (await chkGrid.isVisible().catch(() => false))) {
        const g0 = await chkGrid.isChecked();
        await chkGrid.click();
        await frames(page, 2);
        const g1 = await chkGrid.isChecked();
        await chkGrid.click();
        await frames(page, 2);
        const g2 = await chkGrid.isChecked();
        out.grid_checkbox_ok = g1 !== g0 && g2 === g0;
        out.grid = { g0, g1, g2, workspace_hardcoded_gridShown: false };
      }
      await page.keyboard.press('Escape');
      await frames(page);
    }
    const xrayBtn = page.locator('#btn-xray');
    if ((await xrayBtn.count()) && (await xrayBtn.isVisible().catch(() => false))) {
      const p0 = await xrayBtn.getAttribute('aria-pressed');
      await xrayBtn.click();
      await frames(page, 2);
      const p1 = await xrayBtn.getAttribute('aria-pressed');
      await xrayBtn.click();
      await frames(page, 2);
      const p2 = await xrayBtn.getAttribute('aria-pressed');
      out.xray_ok = p0 === 'false' && p1 === 'true' && p2 === 'false';
      out.xray = { p0, p1, p2 };
    }
    return out;
  }

  async function checkZeroSpoilerLeak(page, forbiddenAnswers) {
    const outsideStatement = await page.evaluate(() => {
      const clone = document.body.cloneNode(true);
      clone.querySelectorAll('#dock-prob-statement, #home-problem-input').forEach((n) => n.remove());
      return clone.innerText;
    });
    const leakedAnswers = (forbiddenAnswers ?? []).filter((a) => outsideStatement.includes(a));
    const cos2Leak = /cos²\s*=\s*\d/.test(outsideStatement);
    const abcdPickerCount = await page.locator('[data-abcd-choice], .mcq-answer-picker, input[name="abcd-answer"]').count();
    const witnessIds = await page.evaluate(() => window.__geo3d_witness_ids ?? []);
    const angleCtorIds = await page.evaluate(() => window.__geo3d_angle_construction_ids ?? []);
    return {
      leaked_answers: leakedAnswers,
      cos2_leak: cos2Leak,
      abcd_picker_count: abcdPickerCount,
      witness_count: witnessIds.length,
      angle_ctor_count: angleCtorIds.length,
      pass: leakedAnswers.length === 0 && !cos2Leak && abcdPickerCount === 0,
    };
  }

  const allFirstModelMs = [];
  const allOrbitMs = [];
  const allNextMs = [];
  const allSpoilerChecks = [];

  // ── D1: Complete 14-step Student Journey at 1920x1080 ───────────────────────
  {
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.name + ': ' + String(e.message).slice(0, 120)));
    await page.goto(ORIGIN, { waitUntil: 'networkidle' });
    const signupStatus = await registerFreshAccount(page, true);
    const lightMode = await checkLightMode(page);

    // Problem 1 (r537)
    const c1 = CASES.r537_pyramid_distance;
    const loaded1 = await loadText(page, c1.text);
    allFirstModelMs.push(loaded1.firstModelMs);
    const cam1 = await cameraOrbitZoomPanReset(page);
    allOrbitMs.push(cam1.orbit_ms);

    const sel1 = await selectChipsByKind(page, loaded1.body?.envelope?.scene3d?.objects ?? []);
    const steps1 = await walkTimeline(page);
    steps1.forEach((s) => { if (s.next_ms != null) allNextMs.push(s.next_ms); });
    const late1 = checkPrematurePrerequisites(loaded1.body, steps1);
    const spoiler1 = await checkZeroSpoilerLeak(page, c1.forbiddenAnswersInUi);
    allSpoilerChecks.push({ case: 'd1_p1_r537', ...spoiler1 });
    const disp1 = await toggleDisplayControls(page);

    // Problem 2 (undotted prism r463)
    const c2 = CASES.r463_undotted_prism_volume;
    const loaded2 = await loadText(page, c2.text);
    allFirstModelMs.push(loaded2.firstModelMs);
    const steps2 = await walkTimeline(page);
    steps2.forEach((s) => { if (s.next_ms != null) allNextMs.push(s.next_ms); });
    const late2 = checkPrematurePrerequisites(loaded2.body, steps2);
    const sceneObjs2 = loaded2.body?.envelope?.scene3d?.objects ?? [];
    const validIds2 = new Set(sceneObjs2.map((o) => o.id));
    const renderedIds2 = await page.evaluate(() => window.__geo3d_rendered_object_ids ?? []);
    const foreignIds2 = renderedIds2.filter((x) => !validIds2.has(String(x).split('::')[0].split('#')[0].split('__')[0]));
    const pageText2 = await page.evaluate(() => document.body.innerText);
    const stalePrevText = pageText2.includes('diện tích đáy bằng a²');
    const hasExpectedPrismObjects = c2.expectedObjects.every((id) => validIds2.has(id));
    const scenePerpWitnesses2 = sceneObjs2.filter((o) => o.perpendicular_witness?.status === 'ENGINE_VERIFIED').map((o) => o.id);
    const angleCtorUnion2 = new Set(steps2.flatMap((s) => s.angle_construction_ids ?? []));
    const spoiler2 = await checkZeroSpoilerLeak(page, c2.forbiddenAnswersInUi);
    allSpoilerChecks.push({ case: 'd1_p2_r463_undotted_prism', ...spoiler2 });

    const traceSectionText =
      'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. ' +
      'Gọi M, N, P lần lượt là trung điểm của SA, BC, CD. Xác định thiết diện của hình chóp cắt bởi mặt phẳng (MNP).';
    const loaded3 = await loadText(page, traceSectionText);
    allFirstModelMs.push(loaded3.firstModelMs);
    const steps3 = await walkTimeline(page);
    steps3.forEach((s) => { if (s.next_ms != null) allNextMs.push(s.next_ms); });
    const late3 = checkPrematurePrerequisites(loaded3.body, steps3);
    const whyAuxJoined = steps3.map((s) => s.why_drawer_text).join(' ');
    const traceAuxExplained = /gọi\s+[A-Z]\s+là\s+giao\s+điểm/i.test(whyAuxJoined);

    const d1Pass =
      signupStatus === 200 &&
      lightMode.is_light &&
      loaded1.body?.route_d?.status === 'SERVED' &&
      loaded1.body?.route_d?.answers?.q1 === c1.expectedAnswer &&
      cam1.snapshot_available &&
      cam1.orbit_changes_camera &&
      cam1.zoom_changes_camera &&
      cam1.pan_changes_camera &&
      cam1.reset_returns_to_initial &&
      Boolean(sel1.point?.selects && sel1.point?.ctx_mounted && !sel1.point?.ctx_tech_token) &&
      Boolean(sel1.edge?.selects && sel1.edge?.ctx_mounted && !sel1.edge?.ctx_tech_token) &&
      Boolean(sel1.face?.selects && sel1.face?.ctx_mounted && !sel1.face?.ctx_tech_token) &&
      steps1.length >= 3 &&
      steps1.every((s) => s.has_explanation) &&
      late1.length === 0 &&
      disp1.aux_ok &&
      disp1.axes_ok &&
      disp1.grid_checkbox_ok &&
      disp1.xray_ok &&
      spoiler1.pass &&
      (spoiler1.witness_count > 0 || spoiler1.angle_ctor_count > 0) &&
      loaded2.body?.route_d?.status === 'SERVED' &&
      loaded2.body?.route_d?.answers?.q1 === c2.expectedAnswer &&
      hasExpectedPrismObjects &&
      scenePerpWitnesses2.length >= c2.expectedMinScenePerpWitnesses &&
      steps2.every((s) => s.has_explanation) &&
      foreignIds2.length === 0 &&
      !stalePrevText &&
      late2.length === 0 &&
      spoiler2.pass &&
      loaded3.body?.route_d?.status === 'SERVED' &&
      traceAuxExplained &&
      late3.length === 0 &&
      errors.length === 0;

    report.d1_complete_student_journey = {
      pass: d1Pass,
      viewport: '1920x1080',
      signup_status: signupStatus,
      light_mode: lightMode,
      problem1_r537: {
        status: loaded1.body?.route_d?.status,
        answer_q1_verified_hidden: loaded1.body?.route_d?.answers?.q1 ?? null,
        first_model_ms: loaded1.firstModelMs,
        camera: cam1,
        selections: sel1,
        timeline_steps: steps1.length,
        explanation_step_count: steps1.filter((s) => s.has_explanation).length,
        late_prerequisites: late1,
        display_controls: disp1,
        spoiler: spoiler1,
      },
      problem2_r463_undotted_prism: {
        status: loaded2.body?.route_d?.status,
        answer_q1_verified_hidden: loaded2.body?.route_d?.answers?.q1 ?? null,
        first_model_ms: loaded2.firstModelMs,
        scene_object_count: validIds2.size,
        has_expected_prism_topology: hasExpectedPrismObjects,
        scene_verified_perp_witness_ids: scenePerpWitnesses2,
        timeline_angle_ctor_ids: [...angleCtorUnion2],
        explanation_step_count: steps2.filter((s) => s.has_explanation).length,
        foreign_rendered_ids: foreignIds2,
        stale_previous_text: stalePrevText,
        late_prerequisites: late2,
        spoiler: spoiler2,
      },
      problem3_trace_section_why_drawer: {
        status: loaded3.body?.route_d?.status,
        first_model_ms: loaded3.firstModelMs,
        trace_aux_explained: traceAuxExplained,
        why_drawer_excerpt: whyAuxJoined.slice(0, 200),
        late_prerequisites: late3,
      },
      page_errors: errors,
    };
    console.log(JSON.stringify({ gate: 'D1', pass: d1Pass }));
    await ctx.close();
  }

  // ── D2: Image OCR & Multi-Problem Sheet Selection at 1366x768 (0 VLM calls) ──
  {
    const ctx = await browser.newContext({ viewport: { width: 1366, height: 768 } });
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.name + ': ' + String(e.message).slice(0, 120)));
    await page.goto(ORIGIN, { waitUntil: 'networkidle' });
    await registerFreshAccount(page, true);

    async function completePrepareAfterResponse(prepBody, editOverrideText) {
      let cur = prepBody;
      let candidateCount = 0;
      let pickedStatus = null;
      if (cur.status === 'needs_selection') {
        await page.locator('#composer-candidate-picker [data-candidate-id]').first().waitFor({ timeout: 15000 });
        candidateCount = await page.locator('#composer-candidate-picker [data-candidate-id]').count();
        const nextPrepPromise = page.waitForResponse(
          (r) => new URL(r.url()).pathname === '/api/input/prepare' && r.request().method() === 'POST',
          { timeout: 120000 },
        );
        await page.locator('#composer-candidate-picker [data-candidate-id]').first().click();
        cur = await (await nextPrepPromise).json();
        pickedStatus = cur.status;
        if (Number(cur?.metrics?.vlm_calls ?? 0) > 0) liveProviderRequestCount += Number(cur.metrics.vlm_calls);
      }

      if (cur.status === 'needs_confirmation') {
        await page.locator('#composer-extraction-confirm').waitFor({ timeout: 20000 });
        const draft = await page.locator('#photo-problem-text').inputValue();
        if (editOverrideText) {
          await page.locator('#photo-problem-text').fill(editOverrideText);
        }
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
        const anBody = await (await anPromise).json();
        await page.waitForSelector('#pa-counter', { timeout: 60000 });
        await page.waitForFunction(
          () => [...document.querySelectorAll('canvas')].some((c) => c.width > 0 && c.height > 0 && c.offsetParent),
          null,
          { timeout: 60000 },
        );
        await frames(page, 3);
        return { draft, candidateCount, pickedStatus, finalPrepareStatus: cur.status, anBody };
      }

      if (cur.status === 'ready') {
        const anPromise = page.waitForResponse(
          (r) => new URL(r.url()).pathname === '/api/analyze' && r.request().method() === 'POST',
          { timeout: 120000 },
        );
        // ProblemInput auto-analyzes on `ready`; await that response cleanly (or already started before await)
        const anResp = await anPromise.catch(() => null);
        const anBody = anResp ? await anResp.json() : null;
        await page.waitForSelector('#pa-counter', { timeout: 60000 });
        await page.waitForFunction(
          () => [...document.querySelectorAll('canvas')].some((c) => c.width > 0 && c.height > 0 && c.offsetParent),
          null,
          { timeout: 60000 },
        );
        await frames(page, 3);
        return {
          draft: cur.problem_text ?? '',
          candidateCount,
          pickedStatus,
          finalPrepareStatus: cur.status,
          anBody,
        };
      }
      throw new Error(`Unexpected prepare status=${cur.status} reason=${cur.reason_code}`);
    }

    // D2a: Real VMMU r537 image (as .jpg)
    await ensureHomeComposer(page);
    await page.locator('#home-file-input').setInputFiles(tempOcrR537JpgPath);
    await page.locator('.file-preview-card:not(.is-loading)').first().waitFor({ timeout: 15000 });
    await page.locator('#btn-composer-send:not([disabled])').waitFor({ timeout: 15000 });
    const prep1Promise = page.waitForResponse(
      (r) => new URL(r.url()).pathname === '/api/input/prepare' && r.request().method() === 'POST',
      { timeout: 120000 },
    );
    const t0a = Date.now();
    await page.locator('#btn-composer-send').click();
    const prep1Resp = await prep1Promise;
    const prep1Body = await prep1Resp.json();
    if (Number(prep1Body?.metrics?.vlm_calls ?? 0) > 0) liveProviderRequestCount += Number(prep1Body.metrics.vlm_calls);
    const res1 = await completePrepareAfterResponse(prep1Body, null);
    const ms1 = Date.now() - t0a;
    allFirstModelMs.push(ms1);
    const spoilerOcr1 = await checkZeroSpoilerLeak(page, ['a√6/3']);
    allSpoilerChecks.push({ case: 'd2a_r537_ocr', ...spoilerOcr1 });

    // D2b: Multi-problem stacked sheet (needs_selection -> pick band 1, zero MNPQ bleed -> auto or confirmed -> Scene3D)
    await ensureHomeComposer(page);
    await page.locator('#home-file-input').setInputFiles(tempMultiSheetPngPath);
    await page.locator('.file-preview-card:not(.is-loading)').first().waitFor({ timeout: 15000 });
    await page.locator('#btn-composer-send:not([disabled])').waitFor({ timeout: 15000 });

    let an2BodyDirect = null;
    page.on('response', async (resp) => {
      if (new URL(resp.url()).pathname === '/api/analyze' && resp.request().method() === 'POST') {
        try { an2BodyDirect = await resp.json(); } catch { /* ignore */ }
      }
    });
    const prep2Promise = page.waitForResponse(
      (r) => new URL(r.url()).pathname === '/api/input/prepare' && r.request().method() === 'POST',
      { timeout: 120000 },
    );
    const t0b = Date.now();
    await page.locator('#btn-composer-send').click();
    const prep2Resp = await prep2Promise;
    const prep2Body = await prep2Resp.json();
    if (Number(prep2Body?.metrics?.vlm_calls ?? 0) > 0) liveProviderRequestCount += Number(prep2Body.metrics.vlm_calls);

    let candidateCount = 0;
    let pick2Body = prep2Body;
    if (prep2Body.status === 'needs_selection') {
      await page.locator('#composer-candidate-picker [data-candidate-id]').first().waitFor({ timeout: 15000 });
      candidateCount = await page.locator('#composer-candidate-picker [data-candidate-id]').count();
      an2BodyDirect = null;
      const nextPrepPromise = page.waitForResponse(
        (r) => new URL(r.url()).pathname === '/api/input/prepare' && r.request().method() === 'POST',
        { timeout: 120000 },
      );
      await page.locator('#composer-candidate-picker [data-candidate-id]').first().click();
      pick2Body = await (await nextPrepPromise).json();
      if (Number(pick2Body?.metrics?.vlm_calls ?? 0) > 0) liveProviderRequestCount += Number(pick2Body.metrics.vlm_calls);
    }

    let rawDraft2 = pick2Body.problem_text ?? '';
    if (pick2Body.status === 'needs_confirmation') {
      await page.locator('#composer-extraction-confirm').waitFor({ timeout: 20000 });
      rawDraft2 = await page.locator('#photo-problem-text').inputValue();
      const spanBtns2 = page.locator('#composer-extraction-confirm [data-span-ok]');
      for (let i = 0; i < await spanBtns2.count(); i++) {
        const b = spanBtns2.nth(i);
        if ((await b.getAttribute('aria-pressed')) !== 'true') await b.click();
      }
      const chk2 = page.locator('#chk-confirm-extracted-text');
      if (!(await chk2.isChecked())) await chk2.check();
      await frames(page, 2);
      await page.locator('#btn-confirm-extracted-build').click();
    }
    await page.waitForSelector('#pa-counter', { timeout: 60000 });
    await page.waitForFunction(
      () => [...document.querySelectorAll('canvas')].some((c) => c.width > 0 && c.height > 0 && c.offsetParent),
      null,
      { timeout: 60000 },
    );
    await frames(page, 3);
    const ms2 = Date.now() - t0b;
    allFirstModelMs.push(ms2);
    const zeroNeighborBleed = !rawDraft2.includes('MNPQ') && !rawDraft2.includes('Câu 2');
    const spoilerOcr2 = await checkZeroSpoilerLeak(page, CASES.multi_top_cuboid.forbiddenAnswersInUi);
    allSpoilerChecks.push({ case: 'd2b_multisheet_band1', ...spoilerOcr2 });

    const d2Pass =
      prep1Resp.status() === 200 &&
      prep1Body.status === 'needs_confirmation' &&
      res1.draft.includes('a²') &&
      res1.anBody?.route_d?.status === 'SERVED' &&
      res1.anBody?.route_d?.answers?.q1 === 'a√6/3' &&
      spoilerOcr1.pass &&
      prep2Resp.status() === 200 &&
      prep2Body.status === 'needs_selection' &&
      candidateCount >= 2 &&
      (pick2Body?.status === 'ready' || pick2Body?.status === 'needs_confirmation') &&
      zeroNeighborBleed &&
      an2BodyDirect?.route_d?.status === 'SERVED' &&
      an2BodyDirect?.route_d?.answers?.q1 === CASES.multi_top_cuboid.expectedAnswer &&
      spoilerOcr2.pass &&
      liveProviderRequestCount === 0 &&
      errors.length === 0;

    report.d2_image_ocr_and_multiproblem = {
      pass: d2Pass,
      viewport: '1366x768',
      vlm_calls: liveProviderRequestCount,
      r537_ocr: {
        prepare_status: prep1Body.status,
        preserves_a2: res1.draft.includes('a²'),
        route_status: res1.anBody?.route_d?.status ?? null,
        answer_q1_verified_hidden: res1.anBody?.route_d?.answers?.q1 ?? null,
        elapsed_ms: ms1,
        spoiler: spoilerOcr1,
      },
      multisheet_ocr: {
        prepare_status: prep2Body.status,
        candidate_count: candidateCount,
        picked_status: pick2Body?.status ?? null,
        raw_draft_preview: rawDraft2.slice(0, 140),
        zero_neighbor_bleed: zeroNeighborBleed,
        route_status: an2BodyDirect?.route_d?.status ?? null,
        answer_q1_verified_hidden: an2BodyDirect?.route_d?.answers?.q1 ?? null,
        elapsed_ms: ms2,
        spoiler: spoilerOcr2,
      },
      page_errors: errors,
    };
    console.log(JSON.stringify({ gate: 'D2', pass: d2Pass }));
    await ctx.close();
  }

  // ── D3: Responsive 4-Viewport Audit & Consecutive Switching ────────────────
  for (const [w, h] of VIEWPORTS) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h } });
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.name + ': ' + String(e.message).slice(0, 120)));
    await page.goto(ORIGIN, { waitUntil: 'networkidle' });
    await registerFreshAccount(page, true);
    const lightMode = await checkLightMode(page);

    const switchSpec = [
      { key: 'cos_line_plane', forbid: null },
      { key: 'r537_pyramid_distance', forbid: 'Tính cosin của góc giữa SB' },
      { key: 'r463_undotted_prism_volume', forbid: 'diện tích đáy bằng a²' },
    ];
    const transitions = [];
    for (const sp of switchSpec) {
      const c = CASES[sp.key];
      const loaded = await loadText(page, c.text);
      allFirstModelMs.push(loaded.firstModelMs);
      const steps = await walkTimeline(page);
      steps.forEach((s) => { if (s.next_ms != null) allNextMs.push(s.next_ms); });
      const late = checkPrematurePrerequisites(loaded.body, steps);

      const canvasMetrics = await page.evaluate(() => {
        const cvs = document.querySelector('canvas');
        const tb = document.querySelector('#floating-toolbar-3d');
        const cRect = cvs ? cvs.getBoundingClientRect() : null;
        const tbRect = tb ? tb.getBoundingClientRect() : null;
        let overlapPct = 0;
        if (cRect && tbRect && cRect.width > 0 && cRect.height > 0 && tbRect.width > 0 && tbRect.height > 0) {
          const ix = Math.max(0, Math.min(cRect.right, tbRect.right) - Math.max(cRect.left, tbRect.left));
          const iy = Math.max(0, Math.min(cRect.bottom, tbRect.bottom) - Math.max(cRect.top, tbRect.top));
          overlapPct = Math.round(((ix * iy) / (cRect.width * cRect.height)) * 1000) / 10;
        }
        const prevBtn = document.querySelector('#pa-prev');
        const nextBtn = document.querySelector('#pa-next');
        const minTarget = [prevBtn, nextBtn]
          .filter(Boolean)
          .map((el) => el.getBoundingClientRect())
          .reduce((m, r) => Math.min(m, r.width, r.height), 999);
        return {
          canvas_count: document.querySelectorAll('canvas').length,
          canvas_w: cRect?.width ?? 0,
          canvas_h: cRect?.height ?? 0,
          toolbar_overlap_pct: overlapPct,
          step_btn_min_px: Math.round(minTarget),
          horizontal_overflow_px: document.documentElement.scrollWidth - window.innerWidth,
        };
      });

      const renderedIds = await page.evaluate(() => window.__geo3d_rendered_object_ids ?? []);
      const validIds = new Set((loaded.body?.envelope?.scene3d?.objects ?? []).map((o) => o.id));
      const foreignIds = renderedIds.filter((x) => !validIds.has(String(x).split('::')[0].split('#')[0].split('__')[0]));
      const pageText = await page.evaluate(() => document.body.innerText);
      const stalePrev = sp.forbid ? pageText.includes(sp.forbid) : false;
      const numericNotePresent = (await page.locator('#stage-numeric-goal-note').count()) > 0;
      const spoiler = await checkZeroSpoilerLeak(page, c.forbiddenAnswersInUi);
      allSpoilerChecks.push({ case: `${w}x${h}_${sp.key}`, ...spoiler });

      const tPass =
        loaded.body?.route_d?.status === 'SERVED' &&
        canvasMetrics.canvas_count === 1 &&
        canvasMetrics.canvas_w >= 200 &&
        canvasMetrics.canvas_h >= 180 &&
        canvasMetrics.toolbar_overlap_pct <= 25 &&
        canvasMetrics.horizontal_overflow_px <= 0 &&
        (w > 500 || canvasMetrics.step_btn_min_px >= 40) &&
        foreignIds.length === 0 &&
        !stalePrev &&
        late.length === 0 &&
        (c.expectedNumericNote == null || numericNotePresent === c.expectedNumericNote) &&
        spoiler.pass;

      transitions.push({
        case: sp.key,
        pass: tPass,
        status: loaded.body?.route_d?.status,
        ...canvasMetrics,
        foreign_rendered_ids: foreignIds,
        stale_previous_premise: stalePrev,
        late_prerequisites: late,
        spoiler,
      });
    }

    const camVp = await cameraOrbitZoomPanReset(page);
    allOrbitMs.push(camVp.orbit_ms);

    const vpRow = {
      viewport: `${w}x${h}`,
      light_mode: lightMode,
      camera: camVp,
      transitions,
      page_errors: errors,
      pass:
        lightMode.is_light &&
        camVp.orbit_changes_camera &&
        camVp.zoom_changes_camera &&
        transitions.every((t) => t.pass) &&
        errors.length === 0,
    };
    report.d3_responsive_4_viewports.push(vpRow);
    console.log(JSON.stringify({ gate: 'D3', viewport: vpRow.viewport, pass: vpRow.pass }));
    await ctx.close();
  }

  // ── D4: Refusal & Capability-Gap Honesty at 1366x768 ───────────────────────
  {
    const ctx = await browser.newContext({ viewport: { width: 1366, height: 768 } });
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.name + ': ' + String(e.message).slice(0, 120)));
    await page.goto(ORIGIN, { waitUntil: 'networkidle' });
    await registerFreshAccount(page, true);

    const refusalSpecs = [
      { key: 'cap_oblique_triangle', kind: 'capability_gap', expectRe: /chưa\s+(?:được\s+)?hỗ\s+trợ/i, forbidMissingClaim: true },
      { key: 'cap_non_special_70deg', kind: 'capability_gap', expectRe: /chưa\s+(?:được\s+)?hỗ\s+trợ/i, forbidMissingClaim: true },
      { key: 'true_missing_dimension', kind: 'insufficient_specification', expectRe: /thiếu|chưa\s+xác\s+định|dữ\s+kiện/i, forbidMissingClaim: false },
    ];

    for (const sp of refusalSpecs) {
      const box = await ensureHomeComposer(page);
      const txt = CASES[sp.key].text;
      await box.fill(txt);
      const resp = page.waitForResponse(
        (r) => new URL(r.url()).pathname === '/api/analyze' && r.request().method() === 'POST',
        { timeout: 60000 },
      );
      await page.locator('#btn-composer-send').click();
      const r = await resp;
      const body = await r.json();
      await page.locator('[data-toast-id="composer-refusal"]').waitFor({ timeout: 10000 }).catch(() => {});
      await frames(page, 2);

      const toastText = (await textIfPresent(page.locator('[data-toast-id="composer-refusal"]'))) ?? '';
      const canvasCount = await page.locator('canvas').count();
      const timelineCount = await page.locator('#pa-counter').count();
      const techToken = (toastText.match(TECH) ?? [null])[0];
      const missingClaim = MISSING_DATA_CLAIM_RE.test(toastText);
      const rewriteAdvice = REWRITE_ADVICE_RE.test(toastText);

      const env = body?.envelope ?? body ?? {};
      const actualStatus = env.status ?? body?.status ?? null;
      const actualCategory = env.failure_category ?? body?.failure_category ?? null;
      const actualReason = env.reason_code ?? body?.reason_code ?? null;
      const pass =
        r.status() === 200 &&
        actualStatus === 'unsupported' &&
        actualCategory === sp.kind &&
        canvasCount === 0 &&
        timelineCount === 0 &&
        toastText.length > 10 &&
        sp.expectRe.test(toastText) &&
        techToken === null &&
        (!sp.forbidMissingClaim || (!missingClaim && !rewriteAdvice && env?.local_understanding?.learner_summary?.rewrite_may_help !== true)) &&
        errors.length === 0;

      report.d4_refusal_honesty.push({
        case: sp.key,
        expected_category: sp.kind,
        actual_category: actualCategory,
        reason_code: actualReason,
        http_status: r.status(),
        canvas_count: canvasCount,
        timeline_count: timelineCount,
        toast_text: toastText,
        machine_token: techToken,
        claimed_missing_data: missingClaim,
        advised_rewrite: rewriteAdvice,
        pass,
      });
      console.log(JSON.stringify({ gate: 'D4', case: sp.key, pass }));
    }
    await ctx.close();
  }

  // ── Aggregate D5 & E3 ───────────────────────────────────────────────────────
  report.d5_zero_solver_spoiler_summary = {
    checks_run: allSpoilerChecks.length,
    all_passed: allSpoilerChecks.length > 0 && allSpoilerChecks.every((x) => x.pass),
    any_answer_leak: allSpoilerChecks.some((x) => x.leaked_answers.length > 0 || x.cos2_leak),
    any_abcd_picker_ui: allSpoilerChecks.some((x) => x.abcd_picker_count > 0),
    checks_with_stage_witnesses: allSpoilerChecks.filter((x) => x.witness_count > 0 || x.angle_ctor_count > 0).length,
  };

  report.e3_latency_telemetry = {
    measurement_tag: 'INCONCLUSIVE_SHARED_HOST_SWIFTSHADER',
    physical_low_end: 'PHYSICAL_LOW_END_NOT_MEASURED',
    first_model_ms: stats(allFirstModelMs),
    orbit_ms: stats(allOrbitMs),
    timeline_next_ms: stats(allNextMs),
  };
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
    Boolean(report.d1_complete_student_journey?.pass) &&
    Boolean(report.d2_image_ocr_and_multiproblem?.pass) &&
    report.d3_responsive_4_viewports.length === 4 &&
    report.d3_responsive_4_viewports.every((v) => v.pass) &&
    report.d4_refusal_honesty.length === 3 &&
    report.d4_refusal_honesty.every((r) => r.pass) &&
    Boolean(report.d5_zero_solver_spoiler_summary?.all_passed);

  report.verdict = overallPass ? 'PASS' : 'FAIL';
  writeFileSync(join(RUN_DIR, 'STUDENT_PILOT_E2E.json'), JSON.stringify(report, null, 2) + '\n', 'utf-8');
  console.log(JSON.stringify({ verdict: report.verdict, tempCleanedUp, liveProviderRequestCount }));
  if (!overallPass) process.exitCode = 1;
}
