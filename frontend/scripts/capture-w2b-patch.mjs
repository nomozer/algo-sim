/**
 * capture-w2b-patch.mjs — M17 W2B-PATCH §E: REVIEW THỊ GIÁC CÓ MỤC TIÊU.
 *
 * Chỉ chụp lại những gì bản vá ĐỘNG TỚI (không chạy lại toàn bộ 42 ảnh của
 * RC1 §E): ô trống sau chuẩn hoá (L3), pipeline năm tầng + chỉ báo tầng (L4),
 * và ba thông điệp từ chối (L5 thiếu bảng · L6 hai truy vấn · thiếu bước).
 *
 * Dùng LẠI hạ tầng CDP của `visual-stress-audit.mjs` (Chrome thật + WebSocket
 * thô), nạp fixture qua module graph Vite — KHÔNG sửa production code để chụp.
 *
 * TRÁNH LẶP LỖI ĐO CỦA RC1 §E1 (VIS-003): viewport được đặt **trước khi trang
 * dựng**, và trang được nạp lại cho từng viewport — không đổi kích thước sau
 * khi layout đã tính xong rồi chụp.
 *
 * Chạy:  npm run dev  (cửa sổ khác)
 *        node scripts/capture-w2b-patch.mjs [--port 3000]
 */

import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const APP = `http://localhost:${argOf("--port", "3000")}`;
const CDP_PORT = 9341;
const OUT_DIR = resolve(argOf("--out", "../docs/evaluation/m17/w2b-patch/visual"));

const VIEWPORTS = [
  { id: "desktop", width: 1440, height: 1000 },
  { id: "narrow", width: 768, height: 900 },
];

/* ══════════════ FIXTURE — config đúng shape validator ══════════════ */
const env = (title, config) => ({
  status: "ok", simulation_id: "database.relational_table_query", domain: "database",
  visual_mode: "2d", title, description: null, notes: null, config,
});
const COL = (name, type, label = null, nullable = null) => ({ name, type, label, nullable });
const TB = (schema, rows, q = {}) =>
  ({ specVersion: "table-1.0", schema, rows, normalizations: [], ...q });

/* L3 — bảng điểm kiểm tra có HAI ô trống (đề viết chữ "trống"; validator đã
 * chuẩn hoá về null trước khi tới đây). AVG phải = 8.25 trên 4 ô có dữ liệu. */
const L3_SCHEMA = [COL("hoc_sinh", "text", "Học sinh"), COL("diem", "number", "Điểm kiểm tra")];
const L3_ROWS = [
  { hoc_sinh: "An", diem: 8 }, { hoc_sinh: "Bình", diem: null },
  { hoc_sinh: "Chi", diem: 9.5 }, { hoc_sinh: "Dũng", diem: 7 },
  { hoc_sinh: "Hà", diem: null }, { hoc_sinh: "Lan", diem: 8.5 },
];
/* L4 — bảng tổ A/B, pipeline NĂM tầng; kết quả đúng: An/Dũng/Lan, AVG 8.5. */
const L4_SCHEMA = [COL("ten", "text", "Tên"), COL("to", "text", "Tổ"),
                   COL("diem", "number", "Điểm"), COL("vang", "number", "Số buổi vắng")];
const L4_ROWS = [
  { ten: "An", to: "A", diem: 9.0, vang: 1 }, { ten: "Bình", to: "B", diem: 8.5, vang: 0 },
  { ten: "Chi", to: "A", diem: 6.0, vang: 2 }, { ten: "Dũng", to: "A", diem: 9.0, vang: 0 },
  { ten: "Hà", to: "B", diem: 7.5, vang: 3 }, { ten: "Lan", to: "A", diem: 7.5, vang: 1 },
  { ten: "Minh", to: "A", diem: 6.0, vang: 0 }, { ten: "Nga", to: "B", diem: 9.5, vang: 2 },
];

const FIXTURES = [
  {
    id: "wp1-L3-avg-empty-markers", finding: "L3",
    envelope: env("Điểm kiểm tra trung bình (có ô trống)",
      TB(L3_SCHEMA, L3_ROWS, { aggregate: { func: "avg", column: "diem" } })),
    expect: "ô trống hiện '— trống —' (KHÔNG phải 0); accumulator bỏ qua ô trống; AVG = 8.25 trên 4 ô",
  },
  {
    id: "wp2-L4-five-stage-pipeline", finding: "L4",
    envelope: env("Tổ A → chọn cột → sắp giảm dần → lấy 3 → trung bình",
      TB(L4_SCHEMA, L4_ROWS, {
        filter: { op: "=", column: "to", value: "A" },
        projection: ["ten", "diem"],
        sort: { column: "diem", direction: "desc" },
        limit: 3,
        aggregate: { func: "avg", column: "diem" },
      })),
    expect: "chỉ báo 5 bước đủ và đánh dấu dần; kết quả 3 dòng An/Dũng/Lan; AVG 8.5 CHỈ ở bước cuối",
  },
];

/* Thông điệp từ chối learner-facing — lấy ĐÚNG chuỗi production sinh ra. */
const REFUSALS = [
  {
    id: "wp3-L5-missing-table", finding: "L5",
    category: "insufficient_specification", code: "input_insufficient",
    reason: "Đề chưa cho bảng dữ liệu cụ thể (tên các cột và các dòng dữ liệu). Em hãy chép rõ bảng vào đề — ví dụ: cột Tên, Điểm, Tổ; rồi từng dòng An 8.5 A, Bình 6.0 B… — hệ không tự tạo bảng thay em.",
    expect: "tiêu đề 'CHƯA ĐỦ DỮ KIỆN'; đòi CUNG CẤP BẢNG; TUYỆT ĐỐI không xui tách hai truy vấn",
  },
  {
    id: "wp4-L6-two-queries", finding: "L6",
    category: "semantic_incomplete", code: "multiple_operations_not_supported",
    reason: "Đề đang hỏi 2 truy vấn độc lập, nhưng mỗi lần mô phỏng chỉ trình bày được MỘT. Em hãy tách thành từng lần hỏi (giữ nguyên bảng, mỗi lần một yêu cầu) để xem đầy đủ từng bước.",
    expect: "yêu cầu TÁCH THÀNH TỪNG YÊU CẦU (đúng bản chất khi bảng ĐÃ có)",
  },
  {
    id: "wp5-stage-shortfall", finding: "L4",
    category: "semantic_incomplete", code: "pipeline_stage_incomplete",
    reason: "Mô phỏng dựng ra chưa trả lời đủ đề: chưa dựng được 2 bước (lấy số dòng đầu; tính trung bình một cột). Hệ không trả lời nửa vời. Em thử hỏi lại và nêu rõ từng bước cần làm (ví dụ: lọc gì, sắp xếp theo cột nào, lấy mấy dòng, tính gì).",
    expect: "thông điệp MỚI của bản vá: nói thiếu BƯỚC nào, KHÔNG xui tách đề",
  },
];

/* ══════════════ CDP ══════════════ */
const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

const profile = mkdtempSync(join(tmpdir(), "algosim-w2bpatch-"));
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", `--remote-debugging-port=${CDP_PORT}`,
  `--user-data-dir=${profile}`, "--window-size=1440,1000", "--hide-scrollbars", "about:blank",
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function connect() {
  for (let i = 0; i < 40; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`)).json();
      const page = list.find((t) => t.type === "page");
      if (page) return page.webSocketDebuggerUrl;
    } catch { /* chưa lên */ }
    await sleep(250);
  }
  throw new Error("Chrome không mở được cổng debug.");
}

const ws = new WebSocket(await connect());
await new Promise((r) => (ws.onopen = r));
let id = 0;
const pending = new Map();
ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
};
const send = (method, params = {}) => new Promise((res) => {
  const i = ++id; pending.set(i, res);
  ws.send(JSON.stringify({ id: i, method, params }));
});
const evaluate = async (expr) => {
  const r = await send("Runtime.evaluate", {
    expression: expr, returnByValue: true, awaitPromise: true,
  });
  const ex = r.result?.exceptionDetails;
  if (ex) throw new Error(JSON.stringify(ex).slice(0, 600));
  return r.result?.result?.value;
};

await send("Page.enable");
await send("Runtime.enable");
mkdirSync(OUT_DIR, { recursive: true });

const setViewport = (vp) => send("Emulation.setDeviceMetricsOverride", {
  width: vp.width, height: vp.height, deviceScaleFactor: 1, mobile: false,
});

async function freshPage(vp) {
  // Viewport TRƯỚC khi trang dựng — đúng bài học VIS-003 của RC1 §E1.
  await setViewport(vp);
  await send("Page.navigate", { url: APP });
  await sleep(1200);
}

async function shot(name) {
  const r = await send("Page.captureScreenshot", { format: "png" });
  const data = r.result?.data;
  if (!data) throw new Error(`captureScreenshot thất bại: ${name}`);
  const path = join(OUT_DIR, `${name}.png`);
  writeFileSync(path, Buffer.from(data, "base64"));
  return path.replace(/\\/g, "/");
}

const loadEnvelope = (envelope) => evaluate(`(async () => {
  const m = await import('/src/state/store.ts');
  m.useAppStore.getState().loadEnvelope(${JSON.stringify(envelope)});
  return true;
})()`);

/* `error_code` PHẢI được truyền: production gắn nó vào envelope unsupported, và
 * notice dùng nó để chọn tiêu đề khi một `failure_category` gộp nhiều ca (bỏ
 * trường này đi thì ảnh chụp KHÔNG phản ánh sản phẩm thật). */
const loadUnsupported = (reason, category, errorCode) => evaluate(`(async () => {
  const m = await import('/src/state/store.ts');
  m.useAppStore.getState().loadUnsupported({
    status: 'unsupported', reason: ${JSON.stringify(reason)},
    learner_reason: ${JSON.stringify(reason)},
    failure_category: ${JSON.stringify(category)},
    error_code: ${JSON.stringify(errorCode ?? null)},
  });
  return true;
})()`);

const stepCount = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const r = await import('/src/simulations/registry.ts');
  const st = s.useAppStore.getState();
  const mod = r.getSimulation(st.active.moduleId);
  return mod.timeline ? mod.timeline.stepCount(st.active.state) : 1;
})()`);

const goToStep = (n) => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  s.useAppStore.getState().goToStep(${n});
  return s.useAppStore.getState().active.state.cursor ?? null;
})()`);

/* Sự thật ĐỌC TỪ ENGINE STATE, không suy từ DOM — dùng để chứng minh ảnh
 * đang chụp đúng trạng thái nào (ảnh là bằng chứng trình bày, state là bằng
 * chứng ngữ nghĩa). */
const engineFacts = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const st = s.useAppStore.getState().active;
  const t = st.state;
  return JSON.stringify({
    moduleId: st.moduleId,
    cursor: t.cursor,
    step_total: (t.steps || []).length,
    current_kind: (t.steps || [])[t.cursor]?.kind ?? null,
    result_rows: (t.resultRows || []).length,
    aggregate: t.aggregateResult
      ? { value: t.aggregateResult.value, counted: t.aggregateResult.counted } : null,
    normalizations: (t.config?.normalizations || []).length,
    empty_cells: (t.config?.rows || []).filter((r) =>
      Object.values(r).some((v) => v === null)).length,
    zero_cells: (t.config?.rows || []).filter((r) =>
      Object.values(r).some((v) => v === 0)).length,
  });
})()`);

/* Đo trong TRÌNH DUYỆT THẬT: chỉ báo tầng, ô trống, và tràn ngang. */
const AUDIT_JS = `(() => {
  const root = document.querySelector('main') || document.body;
  const txt = root.innerText || '';
  const chips = [...root.querySelectorAll('[data-stage]')].map((el) => ({
    stage: el.getAttribute('data-stage'),
    done: el.getAttribute('data-stage-done') === 'true',
    text: (el.innerText || '').trim(),
  }));
  const edges = [...root.querySelectorAll('svg [stroke]')].map((el) =>
    getComputedStyle(el).stroke).filter((v) => v === 'none');
  const overflow = document.documentElement.scrollWidth > window.innerWidth + 1;
  const clipped = [...root.querySelectorAll('*')].filter((el) => {
    const r = el.getBoundingClientRect();
    return r.width > 0 && (r.right > window.innerWidth + 1 || r.left < -1);
  }).length;
  return JSON.stringify({
    stage_chips: chips,
    shows_empty_marker: /trống/i.test(txt),
    shows_zero_for_empty: /=\\s*0(\\D|$)/.test(txt) && /trống/i.test(txt) === false,
    phantom_stroke_none: edges.length,
    page_overflows_horizontally: overflow,
    clipped_elements: clipped,
    text_sample: txt.replace(/\\s+/g, ' ').slice(0, 900),
  });
})()`;

/* ══════════════ CHẠY ══════════════ */
const records = [];
try {
  await fetch(APP);
} catch {
  console.error(`Không mở được ${APP}. Hãy chạy \`npm run dev\` trước.`);
  chrome.kill();
  process.exit(2);
}

for (const vp of VIEWPORTS) {
  for (const fx of FIXTURES) {
    await freshPage(vp);
    await loadEnvelope(fx.envelope);
    await sleep(400);
    const total = await stepCount();
    const marks = [
      ["initial", 0],
      ["mid", Math.max(0, Math.floor((total - 1) / 2))],
      ["final", Math.max(0, total - 1)],
    ];
    for (const [phase, step] of marks) {
      await goToStep(step);
      await sleep(320);
      const png = await shot(`${fx.id}-${vp.id}-${phase}`);
      records.push({
        fixture: fx.id, finding: fx.finding, viewport: vp.id, phase,
        step, step_total: total, png,
        engine: JSON.parse(await engineFacts()),
        audit: JSON.parse(await evaluate(AUDIT_JS)),
        expect: fx.expect,
      });
      console.log(`  ✓ ${fx.id} ${vp.id}/${phase}`);
    }
  }
  for (const rf of REFUSALS) {
    await freshPage(vp);
    await loadUnsupported(rf.reason, rf.category, rf.code);
    await sleep(400);
    const png = await shot(`${rf.id}-${vp.id}`);
    records.push({
      fixture: rf.id, finding: rf.finding, viewport: vp.id, phase: "notice",
      png, failure_category: rf.category, error_code: rf.code, reason: rf.reason,
      audit: JSON.parse(await evaluate(AUDIT_JS)),
      expect: rf.expect,
    });
    console.log(`  ✓ ${rf.id} ${vp.id}`);
  }
}

writeFileSync(join(OUT_DIR, "captures.json"),
  JSON.stringify({
    wave: "M17 W2B-PATCH §E",
    generated_at: new Date().toISOString(),
    note: "Viewport đặt TRƯỚC khi trang dựng và nạp lại trang cho từng viewport "
        + "— không lặp lại artefact phép đo VIS-003 của RC1 §E1. Phán quyết "
        + "REAL/PARTIAL/BROKEN do NGƯỜI xem PNG chấm, assertion chỉ hỗ trợ.",
    app: APP, viewports: VIEWPORTS, records,
  }, null, 2) + "\n", "utf8");

console.log(`\n${records.length} ảnh → ${OUT_DIR}`);
ws.close();
chrome.kill();
