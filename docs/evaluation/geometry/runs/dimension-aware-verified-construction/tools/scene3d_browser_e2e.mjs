// Real Chromium E2E across all 4 required viewports on the production frontend build + isolated loopback uvicorn
// (`HYBRID_ROUTE_MODE=local-first`, `ALLOW_LIVE_AI=0`, `GEMINI_API_KEY=""`, zero live AI calls, isolated temp SQLite DB).
// Run `dimension-aware-verified-construction` — Wave 3B Step 27 (`#27 scene3d_browser_e2e.json` ONLY).
// Automated browser E2E verification, NOT a human learner study (`AUTOMATED_BROWSER_NOT_HUMAN_STUDY`).
//
// Usage (from worktree root):
//   node docs/evaluation/geometry/runs/dimension-aware-verified-construction/tools/scene3d_browser_e2e.mjs [frontend/dist] [out_dir]

import { chromium } from 'file:///D:/Documents/projects/algo-sim/frontend/node_modules/playwright/index.mjs';
import { createServer, request } from 'node:http';
import { createServer as createNetServer } from 'node:net';
import { spawn, execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, copyFileSync, existsSync, unlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, resolve, join, extname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const WORKTREE_ROOT = resolve(__dirname, '../../../../../..');
const PYTHON_EXE = 'D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe';
const LOCAL_OCR_PYTHON = resolve(WORKTREE_ROOT, '.superpowers/ocr-venv/Scripts/python.exe');
const LOCAL_OCR_TESSDATA = resolve(WORKTREE_ROOT, '.superpowers/tessdata_fast');
const R537_IMAGE_PATH = resolve(
  WORKTREE_ROOT,
  '.superpowers/external_image_cache/controlled-vision-vmmu/r537_Math_0264_test_048_question_39_page_4_key_C_vqa.png',
);

const dist = resolve(process.argv[2] ?? join(WORKTREE_ROOT, 'frontend/dist'));
const outDir = resolve(
  process.argv[3] ?? join(WORKTREE_ROOT, 'docs/evaluation/geometry/runs/dimension-aware-verified-construction'),
);

const runStamp = `${process.pid}_${Date.now()}`;
const tempDbPath = join(tmpdir(), `algosim_scene3d_e2e_${runStamp}.sqlite3`);
const tempOcrR537JpgPath = join(tmpdir(), `algosim_scene3d_ocr_r537_${runStamp}.jpg`);
const tempOcrA3Path = join(tmpdir(), `algosim_scene3d_ocr_a3_${runStamp}.png`);

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

function querySystemProvenanceAndRenderTempOcrPng(a3PngPath) {
  const pyCode = `
import json, pathlib, subprocess, sys
sys.path.insert(0, "backend")
sys.path.insert(0, "backend/scripts")
from PIL import Image, ImageDraw, ImageFont
import freeze_evaluation_candidate as fec
from app.main import CACHE_VERSION, ROUTE_D_CACHE_POLICY

wt = pathlib.Path(".").resolve()
im = Image.new("RGB", (1520, 260), "white")
draw = ImageDraw.Draw(im)
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 34)
draw.text((40, 45), "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a,", fill="black", font=font)
draw.text((40, 105), "SA vuông góc với mặt phẳng (ABCD) và thể tích khối chóp S.ABCD bằng a³.", fill="black", font=font)
draw.text((40, 165), "Tính độ dài đoạn thẳng SA.", fill="black", font=font)
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
  const raw = execFileSync(PYTHON_EXE, ['-B', '-c', pyCode, a3PngPath], {
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
  } catch {
    // already exited
  }
}

const P = 'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a';
const T = 'Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC) và SA = a. ';
const R1 = 'Cho hình chóp S.ABC có đáy là tam giác vuông tại B, SA vuông góc với đáy và SA = AB. ';

const VIEWPORTS = [[1920, 1080], [1366, 768], [768, 1024], [390, 844]];

// All 14 required §15.1 flows (executed on ALL 4 required viewports) + sub-variants & prior regression cases.
const CASES = {
  // ── §15.1 Required 14 Flows (4 viewports each) ─────────────────────────────
  f01_area_a2: {
    section15_flow: 1,
    allViewports: true,
    goal: 'distance',
    expectedAnswer: 'a√6/3',
    text: 'Cho hình chóp tứ giác đều S.ABCD có độ dài cạnh bên bằng a và diện tích đáy bằng a². Tính khoảng cách từ A đến mặt phẳng (SBC).',
  },
  f02_volume_a3: {
    section15_flow: 2,
    allViewports: true,
    goal: 'segment_length',
    expectedAnswer: '3a',
    text: 'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng (ABCD) và thể tích khối chóp S.ABCD bằng a³. Tính độ dài đoạn thẳng SA.',
  },
  f03_edge_2a: {
    section15_flow: 3,
    allViewports: true,
    goal: 'volume',
    expectedAnswer: '8a³/3',
    text: 'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA vuông góc với mặt phẳng (ABCD) và SA = 2a. Tính thể tích khối chóp S.ABCD.',
  },
  f04_radical_a_sqrt3: {
    section15_flow: 4,
    allViewports: true,
    goal: 'angle',
    expectedAnswer: 'cos²=1/4',
    text: 'Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC) và SA = a√3. Tính góc giữa SB và mặt phẳng (ABC).',
  },
  f05_segment_ratio: {
    section15_flow: 5,
    allViewports: true,
    goal: 'distance',
    expectedAnswer: 'a',
    requireRenderedPointIds: ['M'],
    text: 'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng (ABCD) và SA = 3a. Điểm M thuộc đoạn thẳng SA sao cho SM = 2MA. Tính khoảng cách từ M đến mặt phẳng (ABCD).',
  },
  f06_height_from_angle: {
    section15_flow: 6,
    allViewports: true,
    goal: 'volume',
    expectedAnswer: 'a³√3/8',
    requireRenderedPointIds: ['H'],
    requireHeightSegmentEndpoints: ['S', 'H'],
    text: 'Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, H là trung điểm của BC, SH vuông góc với mặt phẳng (ABC), góc giữa SA và mặt phẳng (ABC) bằng 60°. Tính thể tích khối chóp S.ABC.',
  },
  f07_leg_from_hypotenuse: {
    section15_flow: 7,
    allViewports: true,
    goal: 'volume',
    expectedAnswer: 'a³√2/3',
    text: 'Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân ở B, cạnh AC = 2a. Cạnh SA vuông góc với mặt đáy (ABC), tam giác SAB cân. Tính thể tích khối chóp S.ABC.',
  },
  f08_true_missing_data: {
    section15_flow: 8,
    allViewports: true,
    goal: 'refusal',
    http: 200,
    expectedFailureCategory: 'insufficient_specification',
    expect: /chưa xác định duy nhất|dữ kiện|Thiếu/i,
    text: 'Cho hình chóp S.ABCD có đáy ABCD là hình vuông, SA vuông góc với mặt phẳng đáy. Tính thể tích khối chóp S.ABCD.',
  },
  f09_capability_unsupported: {
    section15_flow: 9,
    allViewports: true,
    goal: 'refusal',
    http: 200,
    expectedFailureCategory: 'capability_gap',
    expect: /chưa hỗ trợ/i,
    forbidMissingDataClaim: true,
    noRewrite: true,
    text: 'Cho hình chóp S.ABC có SA vuông góc với mặt phẳng (ABC), SA = 3, AB = 3, BC = 4 và góc ABC bằng 30°. Tính thể tích khối chóp S.ABC.',
  },
  f10_contradiction: {
    section15_flow: 10,
    allViewports: true,
    goal: 'refusal',
    http: 200,
    expectedFailureCategory: 'geometry_generation_failed',
    expect: /mâu thuẫn/i,
    text: 'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy, SA = a và SA = 2a. Tính thể tích khối chóp S.ABCD.',
  },
  f11_wrong_dimension: {
    section15_flow: 11,
    allViewports: true,
    goal: 'refusal',
    http: 200,
    expectedFailureCategory: 'geometry_generation_failed',
    expect: /mâu thuẫn|suy biến|không hợp lệ/i,
    text: 'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a², SA vuông góc với mặt phẳng (ABCD) và SA = a. Tính thể tích khối chóp S.ABCD.',
  },
  f12_ocr_exponent_upload_a2: {
    section15_flow: 12,
    allViewports: true,
    goal: 'distance',
    ocrImagePath: tempOcrR537JpgPath,
    expectedOcrToken: 'a²',
    expectedAnswer: 'a√6/3',
    text: '',
  },
  f13_multi_goal: {
    section15_flow: 13,
    allViewports: true,
    goal: 'distance',
    expectedAnswerCount: 2,
    text: P + '. Tính thể tích khối chóp S.ABCD và tính khoảng cách từ A đến mặt phẳng (SBD).',
  },
  f14_proved_right_angle_hidden_marker: {
    section15_flow: 14,
    allViewports: true,
    goal: 'hidden_answer_marker',
    scale: true,
    shape: true,
    text: R1 + 'Tính góc giữa đường thẳng SA và mặt phẳng (ABC).',
  },

  // ── §15.1 Sub-variants (1366x768) ──────────────────────────────────────────
  f05b_edge_ratio_2ab: {
    section15_flow: 5,
    goal: 'volume',
    expectedAnswer: '2a³/3',
    text: 'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng (ABCD) và SA = 2AB. Tính thể tích khối chóp S.ABCD.',
  },
  f06b_r463_prism_height_from_angle: {
    section15_flow: 6,
    goal: 'volume',
    expectedAnswer: '4a³√3',
    text: "Câu 43. Cho khối lăng trụ đứng ABCDA'B'C'D' có đáy ABCD là hình thoi, ∠BAD = 60°, cạnh bên AA' = 2a và AC' hợp với đáy góc 30°. Thể tích khối lăng trụ đã cho bằng",
  },
  f09b_unproved_invariance_capability: {
    section15_flow: 9,
    goal: 'refusal',
    http: 200,
    expectedFailureCategory: 'capability_gap',
    expect: /chưa có chứng chỉ bất biến|chưa hỗ trợ/i,
    forbidMissingDataClaim: true,
    noRewrite: true,
    text: 'Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật có AB = a, SA vuông góc với mặt phẳng đáy và SA = a. Tính khoảng cách từ B đến mặt phẳng (SAD).',
  },
  f11b_wrong_unit_cm2: {
    section15_flow: 11,
    goal: 'refusal',
    http: 200,
    expectedFailureCategory: 'geometry_generation_failed',
    expect: /mâu thuẫn|suy biến|không hợp lệ/i,
    text: 'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 3cm², SA vuông góc với mặt phẳng (ABCD) và SA = a. Tính thể tích khối chóp S.ABCD.',
  },
  f12b_ocr_exponent_upload_a3: {
    section15_flow: 12,
    goal: 'segment_length',
    ocrImagePath: tempOcrA3Path,
    expectedOcrToken: 'a³',
    expectedAnswer: '3a',
    text: '',
  },

  // ── Preserved Prior Regression Cases (1366x768) ────────────────────────────
  reg_section_one_sentence: {
    goal: 'section',
    text: P + ', M là trung điểm của SA, mặt phẳng (P) đi qua M và song song với mặt đáy. Xác định thiết diện của hình chóp bởi (P).',
  },
  reg_section_plane_after_goal: {
    goal: 'section',
    text: P + '. Gọi M là trung điểm của SA. Xác định thiết diện của hình chóp bởi mặt phẳng (P), biết (P) đi qua M và song song với mặt đáy.',
  },
  reg_cos_line_plane: {
    goal: 'angle',
    numeric: 'cos',
    text: T + 'Tính cosin của góc giữa SB và mặt phẳng (ABC).',
  },
  reg_tan_line_plane: {
    goal: 'angle',
    numeric: 'tan',
    text: T + 'Tính tang của góc giữa SB và mặt phẳng (ABC).',
  },
  reg_cos_two_planes: {
    goal: 'angle',
    numeric: 'cos',
    text: "Cho hình lăng trụ tứ giác đều ABCD.A'B'C'D' có cạnh đáy bằng a, cạnh bên bằng a√3. Tính cosin của góc giữa hai mặt phẳng (ABCD) và (ABC').",
  },
  reg_scale_iso_tan: {
    goal: 'angle',
    scale: true,
    numeric: 'tan',
    text: 'Cho hình chóp S.ABC có đáy là tam giác vuông cân tại A, SA vuông góc với đáy và SA = AB. Tang của góc giữa hai mặt phẳng (SBC) và (SBA) bằng',
  },
  reg_shape_free_tan: {
    goal: 'angle',
    scale: true,
    shape: true,
    numeric: 'tan',
    text: 'Cho hình chóp S.ABC có đáy là tam giác vuông tại B, SA vuông góc với đáy và SA = AB. Tang của góc giữa hai mặt phẳng (SBC) và (ABC) bằng',
  },
  reg_regular_tetra_cos: {
    goal: 'angle',
    scale: true,
    numeric: 'cos',
    text: 'Cho tứ diện đều ABCD. Gọi M là trung điểm của CD. Côsin của góc giữa hai đường thẳng AC và BM bằng',
  },
  reg_section_trace_pentagon: {
    goal: 'section',
    why: 'gọi I là giao điểm',
    text: P + '. Gọi M, N, P lần lượt là trung điểm của SA, BC, CD. Xác định thiết diện của hình chóp cắt bởi mặt phẳng (MNP).',
  },
  reg_gv_unnamed_base_face_distance: {
    goal: 'distance',
    text: 'Cho hình chóp S.ABCD có đáy là hình vuông cạnh a, mặt bên SAB là tam giác đều và nằm trong mặt phẳng vuông góc với mặt phẳng đáy. Tính khoảng cách từ A đến mặt phẳng (SBD).',
  },
  reg_gv_refuse_construction: {
    goal: 'refusal',
    http: 503,
    expect: /phép dựng điểm mà hệ thống chưa hỗ trợ/,
    quote: 'Gọi M là điểm đối xứng của A qua C',
    noRewrite: true,
    text: P + '. Gọi M là điểm đối xứng của A qua C. Tính khoảng cách từ M đến (SBD).',
  },
  reg_gv_refuse_goal: {
    goal: 'refusal',
    http: 503,
    expect: /chưa xác định được đề hỏi gì/,
    quote: 'Tính tổng bình phương các cạnh',
    text: P + '. Tính tổng bình phương các cạnh.',
  },
  reg_gv_refuse_premise: {
    goal: 'refusal',
    http: 503,
    expect: /chưa đọc được một quan hệ hoặc số đo/,
    quote: 'chu vi tam giác SAB bằng 5',
    text: 'Cho hình chóp S.ABC có SA vuông góc với đáy, tam giác ABC đều cạnh a, chu vi tam giác SAB bằng 5. Tính thể tích khối chóp S.ABC.',
  },
  reg_gv_refuse_proof: {
    goal: 'refusal',
    http: 200,
    expectedFailureCategory: 'capability_gap',
    expect: /chưa (?:được )?hỗ trợ/,
    forbidMissingDataClaim: true,
    noRewrite: true,
    text: P + '. Chứng minh rằng BD vuông góc với mặt phẳng (SAC).',
  },
};

// Learner-visible text must carry no machine token: snake/screaming case codes, ids like c3, env names, traces, JSON
const TECH = /[a-z]+_[a-z_]+|[A-Z]{2,}_[A-Z_]+|\$\.|[{}]|Traceback|\bError\b|__|ALLOW_LIVE_AI|GEMINI|reason_code|\bc\d+\b/;
const MISSING_DATA_CLAIM_RE = /thiếu\s+dữ\s+kiện|chưa\s+đủ\s+dữ\s+kiện|chưa\s+đủ\s+kích\s+thước/iu;
const REWRITE_OR_ADD_PREMISE_ADVICE_RE = /viết\s+phần\s+đó\s+rõ\s+hơn|bổ\s+sung.*(?:dữ\s+kiện|kích\s+thước|giả\s+thiết)|thêm.*giả\s+thiết/iu;

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
const rows = [];
const switchRows = [];
let healthPayload = null;
let fatalError = null;
let liveProviderRequestCount = 0;

try {
  copyFileSync(R537_IMAGE_PATH, tempOcrR537JpgPath);
  sysMeta = querySystemProvenanceAndRenderTempOcrPng(tempOcrA3Path);
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
        LOCAL_OCR_PYTHON: LOCAL_OCR_PYTHON,
        LOCAL_OCR_TESSDATA: LOCAL_OCR_TESSDATA,
        PYTHONIOENCODING: 'utf-8',
      },
      stdio: 'ignore',
    },
  );
  healthPayload = await waitForHealth(backendPort, 45000);

  server = createServer((req, res) => {
    const path = new URL(req.url, 'http://localhost').pathname;
    if (path.startsWith('/api/')) {
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
    const file = join(dist, path.includes('.') ? path : 'index.html');
    if (!file.startsWith(dist) || !existsSync(file)) {
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
        const f = (i) => (i ? requestAnimationFrame(() => f(i - 1)) : ok());
        f(k);
      }),
      n,
    );

  const textIfPresent = async (loc) => ((await loc.count()) ? await loc.first().innerText().catch(() => null) : null);

  const counter = async (page) => {
    const raw = (await textIfPresent(page.locator('#pa-counter'))) ?? '';
    const t = raw.match(/(\d+)\s*\/\s*(\d+)/);
    return t ? [Number(t[1]), Number(t[2])] : null;
  };

  async function registerFreshAccount(page, reloadAfter = true) {
    const status = await page.evaluate(async () => {
      const r = await fetch('/api/auth/register', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: `e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.invalid`,
          displayName: 'E2E',
          password: crypto.randomUUID(),
        }),
      });
      return r.status;
    });
    if (reloadAfter) await page.reload({ waitUntil: 'networkidle' });
    return status;
  }

  async function ensureHomeComposer(page) {
    const box = page.getByRole('textbox', { name: 'Đề bài hình học không gian', exact: true });
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
      await page.waitForTimeout(120);
    }
    const resp = page.waitForResponse(
      (r) => new URL(r.url()).pathname === '/api/analyze' && r.request().method() === 'POST',
      { timeout: 120000 },
    );
    const t0 = Date.now();
    await page.getByRole('button', { name: 'Phân tích đề bằng AI', exact: true }).click();
    const body = await (await resp).json();
    await page.waitForSelector('#pa-counter', { timeout: 60000 });
    await page.waitForFunction(
      () => [...document.querySelectorAll('canvas')].some((c) => c.width > 0 && c.height > 0 && c.offsetParent),
      null,
      { timeout: 60000 },
    );
    await frames(page, 3);
    return { body, firstModelMs: Date.now() - t0, effectiveProblemText: text, ocrCheck: null };
  }

  async function loadOcrUpload(page, imagePath, expectedToken) {
    await ensureHomeComposer(page);
    await page.locator('#home-file-input').setInputFiles(imagePath);
    await page.locator('.file-preview-card:not(.is-loading)').first().waitFor({ timeout: 15000 });
    await page.locator('#btn-composer-send:not([disabled])').waitFor({ timeout: 15000 });

    const prepRespPromise = page.waitForResponse(
      (r) => new URL(r.url()).pathname === '/api/input/prepare' && r.request().method() === 'POST',
      { timeout: 120000 },
    );
    const t0 = Date.now();
    await page.locator('#btn-composer-send').click();
    const prepResp = await prepRespPromise;
    const prepHttp = prepResp.status();
    const prepBody = await prepResp.json();
    if (prepHttp !== 200) {
      throw new Error(`OCR /api/input/prepare returned HTTP ${prepHttp}: ${JSON.stringify(prepBody).slice(0, 240)}`);
    }
    if (Number(prepBody?.metrics?.vlm_calls ?? 0) > 0) {
      liveProviderRequestCount += Number(prepBody.metrics.vlm_calls);
    }

    let draftText = prepBody.problem_text ?? '';
    let confirmationPanelOpened = false;
    let reviewedSpanCount = 0;

    if (prepBody.status === 'needs_selection') {
      await page.locator('#composer-candidate-picker [data-candidate-id]').first().waitFor({ timeout: 15000 });
      const nextPrepPromise = page.waitForResponse(
        (r) => new URL(r.url()).pathname === '/api/input/prepare' && r.request().method() === 'POST',
        { timeout: 60000 },
      );
      await page.locator('#composer-candidate-picker [data-candidate-id]').first().click();
      const nextPrep = await (await nextPrepPromise).json();
      Object.assign(prepBody, nextPrep);
      draftText = prepBody.problem_text ?? '';
    }

    if (prepBody.status === 'needs_confirmation') {
      await page.locator('#composer-extraction-confirm').waitFor({ timeout: 20000 });
      confirmationPanelOpened = true;
      draftText = await page.locator('#photo-problem-text').inputValue();
      const spanBtns = page.locator('#composer-extraction-confirm [data-span-ok]');
      const nSpans = await spanBtns.count();
      for (let idx = 0; idx < nSpans; idx++) {
        const btn = spanBtns.nth(idx);
        if ((await btn.getAttribute('aria-pressed')) !== 'true') {
          await btn.click();
          reviewedSpanCount += 1;
        }
      }
      const chk = page.locator('#chk-confirm-extracted-text');
      if (!(await chk.isChecked())) {
        await chk.check();
      }
      await frames(page, 2);
      const analyzeRespPromise = page.waitForResponse(
        (r) => new URL(r.url()).pathname === '/api/analyze' && r.request().method() === 'POST',
        { timeout: 120000 },
      );
      await page.locator('#btn-confirm-extracted-build').click();
      const body = await (await analyzeRespPromise).json();
      await page.waitForSelector('#pa-counter', { timeout: 60000 });
      await page.waitForFunction(
        () => [...document.querySelectorAll('canvas')].some((c) => c.width > 0 && c.height > 0 && c.offsetParent),
        null,
        { timeout: 60000 },
      );
      await frames(page, 3);
      return {
        body,
        firstModelMs: Date.now() - t0,
        effectiveProblemText: draftText,
        ocrCheck: {
          prepare_http_status: prepHttp,
          prepare_status: prepBody.status,
          vlm_calls: prepBody?.metrics?.vlm_calls ?? 0,
          confirmation_panel_opened: confirmationPanelOpened,
          reviewed_span_count: reviewedSpanCount,
          expected_exponent_token: expectedToken,
          draft_preserves_exponent: draftText.includes(expectedToken),
        },
      };
    }

    if (prepBody.status !== 'ready') {
      throw new Error(`Unexpected /api/input/prepare status=${prepBody.status} reason=${prepBody.reason_code}`);
    }
    // If prepare returned `ready` directly, `ProblemInput` immediately calls `/api/analyze`
    const analyzeResp = await page.waitForResponse(
      (r) => new URL(r.url()).pathname === '/api/analyze' && r.request().method() === 'POST',
      { timeout: 30000 },
    );
    const body = await analyzeResp.json();
    await page.waitForSelector('#pa-counter', { timeout: 60000 });
    await frames(page, 3);
    return {
      body,
      firstModelMs: Date.now() - t0,
      effectiveProblemText: draftText,
      ocrCheck: {
        prepare_http_status: prepHttp,
        prepare_status: prepBody.status,
        vlm_calls: prepBody?.metrics?.vlm_calls ?? 0,
        confirmation_panel_opened: confirmationPanelOpened,
        reviewed_span_count: reviewedSpanCount,
        expected_exponent_token: expectedToken,
        draft_preserves_exponent: draftText.includes(expectedToken),
      },
    };
  }

  async function loadRefusal(page, text) {
    const box = await ensureHomeComposer(page);
    for (let k = 0; k < 3 && (await box.inputValue()) !== text; k++) {
      await box.fill(text);
      await page.waitForTimeout(120);
    }
    const before = await page.evaluate(() => document.body.innerText);
    const resp = page.waitForResponse(
      (r) => new URL(r.url()).pathname === '/api/analyze' && r.request().method() === 'POST',
      { timeout: 120000 },
    );
    await page.getByRole('button', { name: 'Phân tích đề bằng AI', exact: true }).click();
    const r = await resp;
    const body = await r.json();
    await page.waitForFunction((b) => document.body.innerText !== b, before, { timeout: 15000 }).catch(() => {});
    await frames(page, 4);
    const after = await page.evaluate(() => document.body.innerText);
    const added = after
      .split('\n')
      .filter((l) => l.trim() && !before.includes(l) && !l.includes(text.slice(0, 40)))
      .join('\n');
    return { body, httpStatus: r.status(), notice: added, timeline: await page.locator('#pa-counter').count() };
  }

  const has = (ids, id) => Boolean(ids?.some((x) => x === id || x.startsWith(id + '#') || x.startsWith(id + '__')));

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
      steps.push({
        step: c?.[0],
        of: c?.[1],
        angle_construction_ids: await page.evaluate(() => window.__geo3d_angle_construction_ids ?? []),
        altitude_construction_ids: await page.evaluate(() => window.__geo3d_altitude_construction_ids ?? []),
        rendered_ids: await page.evaluate(() => window.__geo3d_rendered_object_ids ?? []),
        witness_ids: await page.evaluate(() => window.__geo3d_witness_ids ?? []),
        why: await (async () => {
          const t = page.locator('.step-evidence-toggle[aria-expanded="false"]').first();
          if ((await t.count()) && (await t.isVisible().catch(() => false))) {
            await t.click().catch(() => {});
            await frames(page);
          }
          return (await page.locator('.geo3d-cac-buoc-vi-sao').allInnerTexts().catch(() => [])).join(' ');
        })(),
        rendered: (await page.evaluate(() => window.__geo3d_rendered_object_ids ?? [])).length,
      });
      if (!c || c[0] >= c[1] || (await page.isDisabled('#pa-next'))) break;
      const t0 = await page.evaluate(() => performance.now());
      await page.click('#pa-next');
      await frames(page);
      steps.at(-1).next_ms = (await page.evaluate(() => performance.now())) - t0;
    }
    return steps;
  }

  async function cameraChecks(page) {
    const snap = () => page.evaluate(() => JSON.stringify(window.__geo3d_camera_snapshot ?? null));
    const canvas = page.locator('canvas').first();
    await canvas.scrollIntoViewIfNeeded().catch(() => {});
    await frames(page, 2);
    const box = await canvas.boundingBox();
    const startX = box.x + Math.round(box.width * 0.32);
    const startY = box.y + Math.round(box.height * 0.35);
    const s0 = await snap();
    await page.mouse.move(startX, startY);
    await page.mouse.down();
    const t0 = await page.evaluate(() => performance.now());
    await page.mouse.move(startX + 100, startY + 28, { steps: 8 });
    await page.mouse.up();
    await frames(page, 3);
    const orbitMs = (await page.evaluate(() => performance.now())) - t0;
    const s1 = await snap();
    await page.mouse.wheel(0, -300);
    await frames(page, 4);
    const s2 = await snap();
    const reset = page.getByRole('button', { name: /Đặt lại|Khôi phục/ }).first();
    let s3 = null;
    if ((await reset.count()) && (await reset.isVisible())) {
      await reset.click();
      await frames(page, 4);
      s3 = await snap();
    }
    return {
      snapshot_available: s0 !== 'null',
      orbit_changes_camera: s1 !== s0,
      zoom_changes_camera: s2 !== s1,
      reset_available: s3 !== null,
      reset_returns_to_initial: s3 === null ? null : s3 === s0,
      orbit_ms: orbitMs,
    };
  }

  async function panAndAuxiliary(page) {
    const snap = () => page.evaluate(() => JSON.stringify(window.__geo3d_camera_snapshot ?? null));
    const canvas = page.locator('canvas').first();
    await canvas.scrollIntoViewIfNeeded().catch(() => {});
    const box = await canvas.boundingBox();
    const startX = box.x + Math.round(box.width * 0.32);
    const startY = box.y + Math.round(box.height * 0.35);
    const p0 = await snap();
    await page.mouse.move(startX, startY);
    await page.mouse.down({ button: 'right' });
    await page.mouse.move(startX + 80, startY + 35, { steps: 8 });
    await page.mouse.up({ button: 'right' });
    await frames(page, 3);
    const p1 = await snap();
    const out = { pan_changes_camera: p1 !== p0 };
    const btn = page.locator('#btn-display-pop');
    if ((await btn.count()) && (await btn.isVisible())) {
      await btn.click();
      await frames(page);
      const chk = page.locator('#chk-aux');
      const hidden0 = await page.evaluate(() => (window.__geo3d_auxiliary_hidden_ids ?? []).length);
      const rendered0 = await page.evaluate(() => (window.__geo3d_rendered_object_ids ?? []).length);
      if ((await chk.count()) && (await chk.isVisible())) {
        await chk.click();
        await frames(page, 3);
        const hidden1 = await page.evaluate(() => (window.__geo3d_auxiliary_hidden_ids ?? []).length);
        const rendered1 = await page.evaluate(() => (window.__geo3d_rendered_object_ids ?? []).length);
        await chk.click();
        await frames(page, 3);
        const hidden2 = await page.evaluate(() => (window.__geo3d_auxiliary_hidden_ids ?? []).length);
        Object.assign(out, {
          aux_toggle_available: true,
          aux_hidden_before: hidden0,
          aux_hidden_toggled: hidden1,
          aux_hidden_restored: hidden2,
          rendered_before: rendered0,
          rendered_toggled: rendered1,
          aux_toggle_changes_rendering: hidden1 !== hidden0 || rendered1 !== rendered0,
          aux_toggle_restores: hidden2 === hidden0,
        });
      } else {
        out.aux_toggle_available = false;
      }
      await page.keyboard.press('Escape');
      await frames(page);
    } else {
      out.aux_toggle_available = false;
    }
    return out;
  }

  // §12.4 item 5 (object selection) + item 8 (source-to-scene binding: problem statement + given param pills + context card)
  async function selectionAndSourceBindingCheck(page, goalId, effectiveText) {
    const probStatementText = ((await textIfPresent(page.locator('#dock-prob-statement'))) ?? '').trim();
    const normWs = (s) => s.replace(/\s+/g, ' ').trim();
    const statementBound =
      probStatementText.length >= 15 &&
      normWs(probStatementText).includes(normWs(effectiveText).slice(0, 16));

    let chip =
      goalId && (await page.locator(`[data-entity-chip="${goalId}"]`).count())
        ? page.locator(`[data-entity-chip="${goalId}"]`).first()
        : page.locator('[data-entity-chip]').first();
    if (goalId && !(await chip.isVisible().catch(() => false))) {
      const more = page.locator('#btn-dock-entities-more');
      if ((await more.count()) && (await more.isVisible().catch(() => false))) {
        await more.click();
        await frames(page);
      }
    }
    if (!(await chip.count()) || !(await chip.isVisible().catch(() => false))) {
      return { chip_available: false, statement_bound_in_dock: statementBound, source_to_scene_bound: false };
    }
    const id = await chip.getAttribute('data-entity-chip');
    await chip.click({ timeout: 5000 });
    await frames(page, 2);
    const sel = await page.evaluate(() => window.__geo3d_selected_id ?? null);
    const ctxTitle = ((await textIfPresent(page.locator('#ctx-obj-title'))) ?? '').trim();
    const ctxMountObj = (await page.locator('#dock-context-object-mount').count())
      ? await page.locator('#dock-context-object-mount').getAttribute('data-context-object')
      : null;
    const ownerRoot = (s) => (s ? String(s).split('__')[0].split('#')[0] : null);
    const contextCardMounted =
      Boolean(ctxMountObj) && ownerRoot(ctxMountObj) === ownerRoot(id) && ctxTitle.length > 0;
    const ctxTechToken = (ctxTitle.match(TECH) ?? [null])[0];

    const givenParamsVisibleCount = await page.locator('[data-given-param-id]').count();
    const clearBtn = page.locator('#btn-clear-pick');
    if ((await clearBtn.count()) && (await clearBtn.isVisible().catch(() => false))) {
      await clearBtn.click({ timeout: 3000 }).catch(() => {});
      await frames(page);
    }

    return {
      chip_available: true,
      chip_id: id,
      selected_id: sel,
      selects: sel === id,
      context_card_mounted: contextCardMounted,
      context_card_tech_token: ctxTechToken,
      statement_bound_in_dock: statementBound,
      given_params_visible_count: givenParamsVisibleCount,
      source_to_scene_bound: statementBound && sel === id && contextCardMounted && !ctxTechToken,
    };
  }

  const onlyFilter = process.env.ONLY_CASES ? new Set(process.env.ONLY_CASES.split(',').map((s) => s.trim())) : null;

  // ── 1. Execute All 14 §15.1 Flows Across 4 Viewports + Sub-variants & Regressions ──
  for (const [name, c] of Object.entries(CASES)) {
    if (onlyFilter && !onlyFilter.has(name)) continue;
    for (const [w, h] of VIEWPORTS) {
      if (!c.allViewports && !(w === 1366 && h === 768)) continue;
      if (onlyFilter && process.env.ONLY_VP && `${w}x${h}` !== process.env.ONLY_VP) continue;
      const ctx = await browser.newContext({ viewport: { width: w, height: h } });
      const page = await ctx.newPage();
      const errors = [];
      page.on('pageerror', (e) => errors.push(e.name + ': ' + String(e.message).slice(0, 120)));
      await page.goto(ORIGIN, { waitUntil: 'networkidle' });
      // Register synthetic throwaway account for OCR upload flows (file preparation requires authenticated session)
      if (c.ocrImagePath) {
        await registerFreshAccount(page, true);
      }

      if (c.goal === 'refusal') {
        const r = await loadRefusal(page, c.text);
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
        const fcat = r.body?.envelope?.failure_category ?? null;
        const missingDataClaim = MISSING_DATA_CLAIM_RE.test(r.notice);
        const rewriteOrAddPremiseAdvice = REWRITE_OR_ADD_PREMISE_ADVICE_RE.test(r.notice);
        const row = {
          case: name,
          section15_flow: c.section15_flow ?? null,
          goal: 'refusal',
          viewport: `${w}x${h}`,
          http_status: r.httpStatus,
          status: r.body?.route_d?.status ?? null,
          failure_category: fcat,
          refusal_cause: r.body?.route_d?.refusal_cause ?? null,
          notice: r.notice,
          expected: String(c.expect),
          expected_visible: c.expect.test(r.notice),
          quote_expected: c.quote ?? null,
          quote_visible: c.quote ? r.notice.includes(`«${c.quote}»`) : null,
          missing_data_claim_visible: missingDataClaim,
          rewrite_or_add_premise_advice_visible: rewriteOrAddPremiseAdvice,
          technical_token: (r.notice.match(TECH) ?? [null])[0],
          scene_built: r.timeline > 0,
          horizontal_overflow_px: overflow,
          page_errors: errors,
        };
        row.pass =
          r.httpStatus === c.http &&
          (!c.expectedFailureCategory || fcat === c.expectedFailureCategory) &&
          row.expected_visible &&
          (!c.quote || row.quote_visible) &&
          (!c.forbidMissingDataClaim || !missingDataClaim) &&
          (!c.noRewrite || !rewriteOrAddPremiseAdvice) &&
          !row.technical_token &&
          !row.scene_built &&
          overflow <= 0 &&
          errors.length === 0;
        rows.push(row);
        console.log(JSON.stringify({ case: name, viewport: row.viewport, pass: row.pass, http: r.httpStatus, fcat }));
        await ctx.close();
        continue;
      }

      const loaded = c.ocrImagePath
        ? await loadOcrUpload(page, c.ocrImagePath, c.expectedOcrToken)
        : await loadText(page, c.text);
      const { body, firstModelMs, effectiveProblemText, ocrCheck } = loaded;
      const status = body.route_d?.status;
      const answers = Object.values(body.route_d?.answers ?? {});
      const steps = status === 'SERVED' ? await walkTimeline(page) : [];
      const last = steps.at(-1);
      const before = steps.slice(0, -1);
      const cam = status === 'SERVED' ? await cameraChecks(page) : null;
      const panAux = status === 'SERVED' ? await panAndAuxiliary(page) : null;
      const objs = body.envelope?.scene3d?.objects ?? [];

      const goalId =
        c.goal === 'section'
          ? objs.find((o) => o.type === 'section')?.id
          : c.goal === 'intersection'
            ? objs.find((o) => o.producer === 'intersect_plane_plane')?.id
            : c.goal === 'distance'
              ? objs.find((o) => o.type === 'quantity' && o.producer === 'measure.distance')?.id
              : null;

      const sel = status === 'SERVED' ? await selectionAndSourceBindingCheck(page, goalId, effectiveProblemText) : null;
      const fullPageText = await page.evaluate(() => document.body.innerText);
      const dockProbText = (await textIfPresent(page.locator('#dock-prob-statement'))) ?? '';
      // Strip the learner's own problem statement (which in OCR exam sheets like r537 may list MC choices A..D)
      // so we detect whether Axo printed any final answer anywhere outside the learner's input statement.
      let pageOutsideStatement = fullPageText;
      if (dockProbText.trim()) pageOutsideStatement = pageOutsideStatement.replaceAll(dockProbText, '');
      if (effectiveProblemText.trim()) pageOutsideStatement = pageOutsideStatement.replaceAll(effectiveProblemText, '');

      const note = await textIfPresent(page.locator('#stage-numeric-goal-note'));
      const illus = await textIfPresent(page.locator('#stage-illustrative-note'));
      const sgc = body.route_d?.source_goal_completion ?? null;
      const leaked = answers.filter((a) => {
        const v = String(a).replace(/^cos²=/, '').replace(/\s/g, '');
        return v.length >= 2 && pageOutsideStatement.replace(/\s/g, '').includes(v);
      });
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      const minTarget = await page.evaluate(() =>
        Math.min(
          ...['#pa-prev', '#pa-next'].map((s) => {
            const r = document.querySelector(s)?.getBoundingClientRect();
            return r ? Math.min(r.width, r.height) : 0;
          }),
        ),
      );

      // Specific Flow 5 / Flow 6 geometric construction checks (e.g. point M, foot H, height segment SH)
      const requiredPointsOk =
        !c.requireRenderedPointIds ||
        c.requireRenderedPointIds.every(
          (pid) => objs.some((o) => o.id === pid && o.type === 'point3') && has(last?.rendered_ids, pid),
        );
      let heightSegmentCheck = null;
      if (c.requireHeightSegmentEndpoints) {
        const [u, v] = c.requireHeightSegmentEndpoints;
        const segObj = objs.find(
          (o) =>
            o.type === 'segment3' &&
            ((Array.isArray(o.endpoint_ids) && o.endpoint_ids.includes(u) && o.endpoint_ids.includes(v)) ||
              o.notation === `${u}${v}` ||
              o.notation === `${v}${u}`),
        );
        heightSegmentCheck = {
          segment_id: segObj?.id ?? null,
          present_in_scene: Boolean(segObj),
          rendered_on_canvas: Boolean(segObj && has(last?.rendered_ids, segObj.id)),
          has_perpendicular_witness: Boolean(segObj?.perpendicular_witness),
        };
      }

      const constructionOnlyAtConclusion =
        c.goal === 'hidden_answer_marker'
          ? steps.every((s) => (s.witness_ids?.length ?? 0) === 0)
          : c.goal === 'angle'
            ? last?.angle_construction_ids?.length === 1 && before.every((s) => s.angle_construction_ids.length === 0)
            : c.goal === 'altitude'
              ? last?.altitude_construction_ids?.length === 1 && before.every((s) => s.altitude_construction_ids.length === 0)
              : c.goal === 'distance'
                ? Boolean(goalId) && has(last?.rendered_ids, goalId) && before.every((s) => !has(s.rendered_ids, goalId))
                : c.goal === 'volume' || c.goal === 'segment_length'
                  ? steps.length >= 2 && (last?.rendered ?? 0) >= (steps[0]?.rendered ?? 1)
                  : Boolean(goalId) && has(last?.rendered_ids, goalId) && !has(steps[0]?.rendered_ids, goalId);

      // Per-step causal order in the browser: visual prerequisites must appear at or before the dependent object
      const pre = new Map(objs.map((o) => [o.id, o.visible_prerequisites ?? []]));
      const visual = new Set(
        objs.filter((o) => !['non_visual', 'readout'].includes(o.render) && o.type !== 'quantity').map((o) => o.id),
      );
      const seen = new Set();
      const latePrerequisites = [];
      steps.forEach((s, k) => {
        (s.rendered_ids ?? []).forEach((x) => seen.add(x));
        for (const x of s.rendered_ids ?? []) {
          for (const p of pre.get(x) ?? []) {
            if (visual.has(p) && !seen.has(p)) latePrerequisites.push([k + 1, x, p]);
          }
        }
      });

      const whyTexts = [...new Set(steps.map((s) => s.why).filter(Boolean))];
      const whyOk = !c.why || whyTexts.some((t) => t.includes(c.why));
      const answerOracleOk =
        (!c.expectedAnswer || answers.includes(c.expectedAnswer)) &&
        (!c.expectedAnswerCount || answers.length === c.expectedAnswerCount);
      const ocrOk =
        !c.ocrImagePath ||
        (ocrCheck?.prepare_http_status === 200 &&
          ocrCheck?.vlm_calls === 0 &&
          ocrCheck?.draft_preserves_exponent === true);

      const row = {
        case: name,
        section15_flow: c.section15_flow ?? null,
        goal: c.goal,
        viewport: `${w}x${h}`,
        status,
        answers_count: answers.length,
        answer_matches_oracle: answerOracleOk,
        first_model_ms: firstModelMs,
        timeline_steps: steps.length,
        goal_object_id: goalId ?? null,
        construction_only_at_conclusion: constructionOnlyAtConclusion,
        required_points_rendered: requiredPointsOk,
        height_segment_check: heightSegmentCheck,
        ocr_check: ocrCheck,
        camera: cam,
        pan_and_auxiliary: panAux,
        selection_and_source_binding: sel,
        answer_text_on_page: leaked,
        cos2_text_on_page: /cos²/.test(pageOutsideStatement),
        illustrative_note: illus,
        scale_configuration: body.route_d?.scene_configuration?.kind ?? null,
        numeric_goal_note: note,
        numeric_goal_note_has_digit: note ? /\d/.test(note) : null,
        source_goal_completion: sgc
          ? { fully_satisfied: sgc.source_goal_fully_satisfied, goals: sgc.goals.map((g) => [g.function, g.numeric_source_goal]) }
          : null,
        trig_value_on_page: /(?:c[oô]sin|cos|tang|tan|sin)\s*(?:của\s+góc[^.]*?)?\s*(?:=|bằng)\s*[-\d√]/i.test(pageOutsideStatement),
        late_prerequisites: latePrerequisites,
        why_ok: whyOk,
        horizontal_overflow_px: overflow,
        step_button_min_px: minTarget,
        page_errors: errors,
      };

      row.pass =
        status === 'SERVED' &&
        answerOracleOk &&
        ocrOk &&
        requiredPointsOk &&
        (!heightSegmentCheck || (heightSegmentCheck.present_in_scene && heightSegmentCheck.rendered_on_canvas)) &&
        latePrerequisites.length === 0 &&
        whyOk &&
        steps.length >= 2 &&
        constructionOnlyAtConclusion !== false &&
        Boolean(cam?.orbit_changes_camera) &&
        Boolean(cam?.zoom_changes_camera) &&
        cam?.reset_returns_to_initial === true &&
        Boolean(panAux?.pan_changes_camera) &&
        panAux?.aux_toggle_available === true &&
        panAux?.aux_toggle_restores === true &&
        sel?.selects === true &&
        sel?.source_to_scene_bound === true &&
        leaked.length === 0 &&
        !row.cos2_text_on_page &&
        (c.numeric
          ? sgc?.source_goal_fully_satisfied === false && Boolean(note) && !row.numeric_goal_note_has_digit
          : !note && !sgc) &&
        !row.trig_value_on_page &&
        (!c.scale ||
          ((c.shape
            ? row.scale_configuration === 'TARGET_INVARIANT_ILLUSTRATIVE' && /không xác định duy nhất/.test(illus ?? '')
            : row.scale_configuration === 'SIMILARITY_SCALE_ILLUSTRATIVE' && /không cho độ dài/.test(illus ?? '')) &&
            !/\d/.test(illus ?? ''))) &&
        overflow <= 0 &&
        errors.length === 0 &&
        (w > 500 || minTarget >= 40);

      rows.push(row);
      console.log(JSON.stringify({ case: name, viewport: row.viewport, pass: row.pass, steps: steps.length, ms: firstModelMs }));
      await ctx.close();
    }
  }

  // ── 2. §15.3 Consecutive Problem Switching & Responsive Isolation Across ALL 4 Viewports ──
  const SWITCH_SEQUENCE = [
    { key: 'reg_cos_line_plane', expectNumericNote: true, expectIllusNote: false, forbidPrevSnippet: null },
    { key: 'f01_area_a2', expectNumericNote: false, expectIllusNote: false, forbidPrevSnippet: 'Tính cosin của góc giữa SB' },
    { key: 'f06_height_from_angle', expectNumericNote: false, expectIllusNote: false, forbidPrevSnippet: 'diện tích đáy bằng a²' },
    { key: 'reg_shape_free_tan', expectNumericNote: true, expectIllusNote: true, forbidPrevSnippet: 'H là trung điểm của BC' },
    { key: 'f02_volume_a3', expectNumericNote: false, expectIllusNote: false, forbidPrevSnippet: 'Tang của góc giữa hai mặt phẳng' },
  ];

  for (const [w, h] of onlyFilter ? [] : VIEWPORTS) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h } });
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.name + ': ' + String(e.message).slice(0, 120)));
    await page.goto(ORIGIN, { waitUntil: 'networkidle' });
    const signupStatus = await registerFreshAccount(page, true);

    const transitions = [];
    for (const stepSpec of SWITCH_SEQUENCE) {
      const c = CASES[stepSpec.key];
      const loaded = await loadText(page, c.text);
      await walkTimeline(page);
      const renderedIds = await page.evaluate(() => window.__geo3d_rendered_object_ids ?? []);
      const validIds = new Set((loaded.body?.envelope?.scene3d?.objects ?? []).map((o) => o.id));
      const foreignIds = renderedIds.filter((x) => {
        const root = String(x).split('::')[0].split('#')[0].split('__')[0];
        return !validIds.has(root);
      });
      const numericNotePresent = (await page.locator('#stage-numeric-goal-note').count()) > 0;
      const illusNotePresent = (await page.locator('#stage-illustrative-note').count()) > 0;
      const pageText = await page.evaluate(() => document.body.innerText);
      const staleSnippetPresent = stepSpec.forbidPrevSnippet ? pageText.includes(stepSpec.forbidPrevSnippet) : false;
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      const canvasCount = await page.locator('canvas').count();

      const tPass =
        loaded.body?.route_d?.status === 'SERVED' &&
        foreignIds.length === 0 &&
        numericNotePresent === stepSpec.expectNumericNote &&
        illusNotePresent === stepSpec.expectIllusNote &&
        !staleSnippetPresent &&
        canvasCount === 1 &&
        overflow <= 0 &&
        errors.length === 0;

      transitions.push({
        case: stepSpec.key,
        status: loaded.body?.route_d?.status ?? null,
        foreign_rendered_ids: foreignIds,
        numeric_note_present: numericNotePresent,
        numeric_note_expected: stepSpec.expectNumericNote,
        illustrative_note_present: illusNotePresent,
        illustrative_note_expected: stepSpec.expectIllusNote,
        stale_previous_premise_present: staleSnippetPresent,
        canvas_count: canvasCount,
        horizontal_overflow_px: overflow,
        pass: tPass,
      });
    }

    const vpRow = {
      viewport: `${w}x${h}`,
      synthetic_signup_status: signupStatus,
      transitions,
      page_errors: errors,
      pass: signupStatus === 200 && transitions.every((t) => t.pass) && errors.length === 0,
    };
    switchRows.push(vpRow);
    console.log(JSON.stringify({ consecutive_switch_viewport: vpRow.viewport, pass: vpRow.pass, count: transitions.length }));
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

  for (const f of [tempDbPath, `${tempDbPath}-wal`, `${tempDbPath}-shm`, tempOcrR537JpgPath, tempOcrA3Path]) {
    if (existsSync(f)) {
      try { unlinkSync(f); } catch { /* ignore */ }
    }
  }
  const tempCleanedUp = !existsSync(tempDbPath) && !existsSync(tempOcrR537JpgPath) && !existsSync(tempOcrA3Path);

  const section15FlowsCovered = [...new Set(rows.filter((r) => r.section15_flow != null && r.pass).map((r) => r.section15_flow))].sort(
    (a, b) => a - b,
  );
  const servedRows = rows.filter((r) => r.goal !== 'refusal');
  const refusalRows = rows.filter((r) => r.goal === 'refusal');
  const allRowsPass = rows.length > 0 && rows.every((r) => r.pass);
  const allSwitchesPass = switchRows.length === 4 && switchRows.every((s) => s.pass);
  const all14FlowsAcross4ViewportsPass =
    section15FlowsCovered.length === 14 &&
    Array.from({ length: 14 }, (_, idx) => idx + 1).every((flowNo) => {
      const flowRows4Vp = rows.filter((r) => r.section15_flow === flowNo && VIEWPORTS.some(([w, h]) => r.viewport === `${w}x${h}`));
      const distinctVps = new Set(flowRows4Vp.filter((r) => r.pass).map((r) => r.viewport));
      return distinctVps.size === 4;
    });

  const overallPass =
    fatalError === null &&
    allRowsPass &&
    allSwitchesPass &&
    all14FlowsAcross4ViewportsPass &&
    liveProviderRequestCount === 0 &&
    healthPayload?.hasKey === false &&
    tempCleanedUp;

  const receipt = {
    schema: 'algosim-scene3d-browser-e2e/2',
    run_id: 'dimension-aware-verified-construction',
    phase: 'wave_3b_step_27_scene3d_browser_e2e',
    generated_at_utc: new Date().toISOString().replace(/\.\d{3}Z$/, 'Z'),
    git_head_sha: sysMeta.git_head_sha,
    product_commit: sysMeta.product_commit,
    measured_system_hash: sysMeta.measured_system_hash,
    measured_system_file_count: sysMeta.measured_system_file_count,
    cache_version: sysMeta.cache_version,
    route_d_cache_policy: sysMeta.route_d_cache_policy,
    category: 'AUTOMATED_BROWSER_NOT_HUMAN_STUDY',
    physical_low_end: 'PHYSICAL_LOW_END_NOT_MEASURED',
    dataset_partition:
      'DEVELOPMENT_EXPOSED_AND_SYNTHETIC_E2E_PROBES_ONLY (14 §15.1 flows across 4 viewports + exposed VMMU r537 OCR image + r460/r463-class geometry probes + preserved regression suite; zero access to sealed H-1 or locked W2/W3)',
    test_command:
      'node docs/evaluation/geometry/runs/dimension-aware-verified-construction/tools/scene3d_browser_e2e.mjs',
    expected_behavior:
      'All 14 §15.1 end-to-end flows pass on real Chromium across all 4 required viewports (1920x1080, 1366x768, 768x1024, 390x844) against production frontend/dist and loopback uvicorn (HYBRID_ROUTE_MODE=local-first, ALLOW_LIVE_AI=0, GEMINI_API_KEY="", 0 provider calls): (1) output-policy/1 hides all final numeric/symbolic answers and asked right-angle markers; (2) all 8 §12.4 interactions (orbit, zoom, pan, reset, entity selection, causal construction timeline + «Vì sao», auxiliary visibility toggle, and source-to-scene binding) succeed; (3) §15.2 diagnostic UX distinguishes true missing data, capability gaps (never called "thiếu dữ kiện" and never advising premise edits), contradictions, wrong-dimension assignments, and unread clauses with zero machine tokens; (4) Flow 12 OCR image upload + confirmation preserves superscripts a²/a³ and builds Scene3D; (5) §15.3 consecutive 5-problem switching across all 4 viewports leaves zero foreign Scene3D objects, zero stale notes/premises, and <= 0px horizontal overflow.',
    actual_behavior: overallPass
      ? `PASSED ${rows.filter((r) => r.pass).length}/${rows.length} single-flow browser E2E runs (including all 14/14 §15.1 flows across all 4 viewports = 56/56 viewport-flow runs, 5 sub-variants, and 14 regression cases) plus ${switchRows.filter((s) => s.pass).length}/${switchRows.length} 4-viewport 5-step consecutive switching suites (20/20 transitions) with 0 live AI calls, 0 answer leaks, 0 foreign Scene3D objects, 0 machine-token leaks, <= 0px horizontal overflow, and verified temp SQLite/OCR cleanup.`
      : `FAILED: fatalError=${fatalError}; passedRows=${rows.filter((r) => r.pass).length}/${rows.length}; switchPassed=${switchRows.filter((s) => s.pass).length}/${switchRows.length}; tempCleanedUp=${tempCleanedUp}`,
    mathematical_oracle:
      'Exact algebraic & geometric verification contracts per flow: Flow 1 S_ABCD=a² -> AB=a -> d(A,(SBC))=a√6/3; Flow 2 V=a³ -> SA=3a; Flow 3 edge=2a -> V=8a³/3; Flow 4 SA=a√3 -> cos²(SB,(ABC))=1/4; Flow 5 SM=2MA on SA=3a -> d(M,(ABCD))=a; Flow 6 ∠((SA),(ABC))=60° with midpoint H of BC and SH⊥(ABC) -> foot H and height segment SH rendered + V=a³√3/8 (plus r463 V=4a³√3); Flow 7 AC=2a in right isosceles ABC at B -> AB=BC=a√2 -> V=a³√2/3; Flows 8-11 & 14 enforce 4-way taxonomy separation, dimensional homogeneity (dim(AB)=L != L²), and output-policy/1 non-spoiler rendering.',
    source_provenance: {
      e2e_harness: 'docs/evaluation/geometry/runs/dimension-aware-verified-construction/tools/scene3d_browser_e2e.mjs',
      prior_e2e_harness: 'docs/evaluation/geometry/runs/grounded-vietnamese-geometry-understanding/tools/scene3d_goal_e2e.mjs',
      frontend_bundle_dir: 'frontend/dist',
      ocr_vmmu_dev_image: '.superpowers/external_image_cache/controlled-vision-vmmu/r537_Math_0264_test_048_question_39_page_4_key_C_vqa.png',
      loopback_backend_mode: 'HYBRID_ROUTE_MODE=local-first, ALLOW_LIVE_AI=0, GEMINI_API_KEY=""',
      health_has_key: healthPayload?.hasKey ?? null,
      live_provider_calls: liveProviderRequestCount,
      temp_sqlite_cleaned_up: tempCleanedUp,
    },
    verdict: overallPass ? 'PASS' : 'FAIL',
    summary: {
      viewports_tested: VIEWPORTS.map(([w, h]) => `${w}x${h}`),
      section_15_1_flows_covered: section15FlowsCovered,
      section_15_1_all_14_across_4_viewports_pass: all14FlowsAcross4ViewportsPass,
      total_flow_viewport_runs: rows.length,
      passed_flow_viewport_runs: rows.filter((r) => r.pass).length,
      served_runs_count: servedRows.length,
      served_runs_passed: servedRows.filter((r) => r.pass).length,
      refusal_runs_count: refusalRows.length,
      refusal_runs_passed: refusalRows.filter((r) => r.pass).length,
      section_12_4_interactions_all_pass: servedRows.every(
        (r) =>
          r.camera?.orbit_changes_camera &&
          r.camera?.zoom_changes_camera &&
          r.camera?.reset_returns_to_initial === true &&
          r.pan_and_auxiliary?.pan_changes_camera &&
          r.pan_and_auxiliary?.aux_toggle_available &&
          r.pan_and_auxiliary?.aux_toggle_restores &&
          r.selection_and_source_binding?.selects &&
          r.selection_and_source_binding?.source_to_scene_bound &&
          r.late_prerequisites.length === 0,
      ),
      section_15_2_diagnostics_all_pass: refusalRows.every((r) => r.pass),
      section_15_3_switching_viewports_passed: switchRows.filter((s) => s.pass).length,
      section_15_3_switching_transitions_passed: switchRows.reduce(
        (acc, s) => acc + s.transitions.filter((t) => t.pass).length,
        0,
      ),
      zero_answer_leaks: servedRows.every((r) => r.answer_text_on_page.length === 0 && !r.cos2_text_on_page && !r.trig_value_on_page),
      zero_machine_token_leaks: refusalRows.every((r) => r.technical_token === null),
      zero_horizontal_overflow:
        rows.every((r) => r.horizontal_overflow_px <= 0) &&
        switchRows.every((s) => s.transitions.every((t) => t.horizontal_overflow_px <= 0)),
      zero_page_errors: rows.every((r) => r.page_errors.length === 0) && switchRows.every((s) => s.page_errors.length === 0),
    },
    rows,
    consecutive_switching_by_viewport: switchRows,
  };

  writeFileSync(join(outDir, 'scene3d_browser_e2e.json'), JSON.stringify(receipt, null, 2) + '\n', 'utf-8');
  if (!overallPass) process.exitCode = 1;
}
