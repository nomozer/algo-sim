/**
 * capture-w2c-program.mjs — M17 W2C-VR: REVIEW THỊ GIÁC `algorithm.bounded_control_flow`.
 *
 * Dùng LẠI hạ tầng CDP của `capture-w2b-patch.mjs` (Chrome thật + WebSocket thô,
 * fixture nạp qua module graph Vite) — KHÔNG sửa production code để chụp, KHÔNG
 * dựng engine fixture song song: spec đi qua CHÍNH `validateProgramSpec` +
 * `runProgram` mà sản phẩm dùng.
 *
 * TRÁNH LẶP LỖI ĐO RC1 §E1 (VIS-003): viewport đặt **trước khi trang dựng**, và
 * trang được nạp lại cho từng viewport — không resize sau khi layout đã tính.
 *
 * Chạy:  npm run dev  (cửa sổ khác)
 *        node scripts/capture-w2c-program.mjs [--port 3000]
 */

import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const APP = `http://localhost:${argOf("--port", "3000")}`;
const CDP_PORT = 9343;
const OUT_DIR = resolve(argOf("--out", "../docs/evaluation/m17/w2c/visual/bounded-control-flow"));

const TARGET = "algorithm.bounded_control_flow";
const VIEWPORTS = [
  { id: "desktop", width: 1440, height: 1000 },
  { id: "narrow", width: 768, height: 900 },
];

/* ══════════════ FIXTURE — spec đúng shape validator ══════════════ */
const env = (title, config) => ({
  status: "ok", simulation_id: TARGET, domain: "algorithm",
  visual_mode: "2d", title, description: null, notes: null, config,
});
const iv = (name, v) => ({ name, type: "integer", int_value: v, bool_value: null });
const bv = (name, v) => ({ name, type: "boolean", int_value: null, bool_value: v });
const prog = (variables, expressions, statements, main) =>
  ({ program_version: "program-1.0", variables, expressions, statements, main });

/* VR-CF-1 — gán: x = 3 ; y = x*2 + 1 → 7 */
const CF1 = prog(
  [iv("x", 3), iv("y", 0)],
  [
    { id: "e_x", kind: "var", name: "x" },
    { id: "e_2", kind: "int", int_value: 2 },
    { id: "e_1", kind: "int", int_value: 1 },
    { id: "e_mul", kind: "binary", op: "*", left: "e_x", right: "e_2" },
    { id: "e_sum", kind: "binary", op: "+", left: "e_mul", right: "e_1" },
  ],
  [{ id: "s1", kind: "assign", target: "y", value: "e_sum" }],
  ["s1"],
);

/* VR-CF-2 — rẽ nhánh: x = -2 ; nếu x > 0 thì y = 1 ngược lại y = -1 */
const CF2 = prog(
  [iv("x", -2), iv("y", 0)],
  [
    { id: "e_x", kind: "var", name: "x" },
    { id: "e_0", kind: "int", int_value: 0 },
    { id: "e_gt", kind: "compare", op: ">", left: "e_x", right: "e_0" },
    { id: "e_p1", kind: "int", int_value: 1 },
    { id: "e_m1", kind: "int", int_value: -1 },
  ],
  [
    { id: "s_then", kind: "assign", target: "y", value: "e_p1" },
    { id: "s_else", kind: "assign", target: "y", value: "e_m1" },
    { id: "s_if", kind: "if", condition: "e_gt", then_body: ["s_then"], else_body: ["s_else"] },
  ],
  ["s_if"],
);

/* VR-CF-3 — vòng lặp hoàn thành: x = 1 ; trong khi x < 5 thì x = x + 1 */
const CF3 = prog(
  [iv("x", 1)],
  [
    { id: "e_x", kind: "var", name: "x" },
    { id: "e_5", kind: "int", int_value: 5 },
    { id: "e_lt", kind: "compare", op: "<", left: "e_x", right: "e_5" },
    { id: "e_1", kind: "int", int_value: 1 },
    { id: "e_inc", kind: "binary", op: "+", left: "e_x", right: "e_1" },
  ],
  [
    { id: "s_body", kind: "assign", target: "x", value: "e_inc" },
    { id: "s_while", kind: "while", condition: "e_lt", body: ["s_body"], max_iterations: 10 },
  ],
  ["s_while"],
);

/* VR-CF-4 — biểu thức logic: a=true, b=false ; nếu a và không b thì x=1 ngược lại x=0 */
const CF4 = prog(
  [bv("a", true), bv("b", false), iv("x", 0)],
  [
    { id: "e_a", kind: "var", name: "a" },
    { id: "e_b", kind: "var", name: "b" },
    { id: "e_nb", kind: "unary", op: "not", operand: "e_b" },
    { id: "e_and", kind: "logic", op: "and", left: "e_a", right: "e_nb" },
    { id: "e_1", kind: "int", int_value: 1 },
    { id: "e_0", kind: "int", int_value: 0 },
  ],
  [
    { id: "s_then", kind: "assign", target: "x", value: "e_1" },
    { id: "s_else", kind: "assign", target: "x", value: "e_0" },
    { id: "s_if", kind: "if", condition: "e_and", then_body: ["s_then"], else_body: ["s_else"] },
  ],
  ["s_if"],
);

/* VR-CF-8 — chạm biên lặp. Spec HỢP LỆ theo hợp đồng (max_iterations ≤ 50);
 * điều kiện luôn đúng nên engine dừng ở biên và phải nói THẬT là chưa kết thúc. */
const CF8 = prog(
  [iv("x", 0)],
  [
    { id: "e_t", kind: "bool", bool_value: true },
    { id: "e_x", kind: "var", name: "x" },
    { id: "e_1", kind: "int", int_value: 1 },
    { id: "e_inc", kind: "binary", op: "+", left: "e_x", right: "e_1" },
  ],
  [
    { id: "s_body", kind: "assign", target: "x", value: "e_inc" },
    { id: "s_while", kind: "while", condition: "e_t", body: ["s_body"], max_iterations: 5 },
  ],
  ["s_while"],
);

const FIXTURES = [
  {
    id: "vr-cf1-assignment", envelope: env("Gán và biểu thức", CF1),
    narrow: true,
    marks: ["initial", "first_assign", "final"],
    expect: "y=7 KHÔNG lộ ở bước đầu; dòng hiện tại đúng; biến vừa đổi rõ",
  },
  {
    id: "vr-cf2-if-else", envelope: env("Rẽ nhánh if/else", CF2),
    narrow: true,
    marks: ["initial", "first_condition", "final"],
    expect: "điều kiện SAI có CHỮ; chỉ nhánh ngược lại chạy; y=1 không xuất hiện",
  },
  {
    id: "vr-cf3-while", envelope: env("Vòng lặp while", CF3),
    narrow: true,
    marks: ["initial", "first_condition", "mid_iteration", "loop_exit", "final"],
    expect: "lượt lặp rõ; kiểm điều kiện ≠ bước gán; x=5 chỉ hiện đúng lúc",
  },
  {
    id: "vr-cf4-boolean", envelope: env("Biểu thức logic", CF4),
    narrow: false,
    marks: ["initial", "first_condition", "final"],
    expect: "AND/NOT dễ hiểu; kết quả biểu thức rõ; renderer không tự đánh giá khác trace",
  },
  {
    id: "vr-cf8-iteration-limit", envelope: env("Chạm giới hạn lặp", CF8),
    narrow: false,
    marks: ["initial", "mid_iteration", "final"],
    expect: "KHÔNG trình bày là hoàn thành; nói rõ chưa kết thúc trong giới hạn",
  },
];

/* ══════════════ REFUSAL — đúng chuỗi production sinh ra ══════════════ */
const REFUSALS = [
  {
    id: "vr-cf5-insufficient", narrow: true,
    category: "insufficient_specification", code: "input_insufficient",
    reason: "Đề chưa cho đoạn chương trình cụ thể để chạy thử. Em hãy nêu rõ: giá trị "
          + "ban đầu của các biến (ví dụ x = 1), điều kiện (ví dụ x < 5), và các câu "
          + "lệnh trong thân (ví dụ x = x + 1) — hệ không tự nghĩ ra chương trình thay em.",
    expect: "tiêu đề CHƯA ĐỦ DỮ KIỆN; đòi biến/điều kiện/thân; KHÔNG hiện chương trình mẫu",
  },
  {
    id: "vr-cf6-unsupported-function", narrow: false,
    category: "capability_gap", code: null,
    reason: "Bài này cần chạy hàm và đệ quy — mô phỏng chạy-từng-bước hiện chỉ làm được "
          + "các câu lệnh gán, rẽ nhánh và vòng lặp trên biến đơn, chưa hỗ trợ hàm/thủ "
          + "tục hay đệ quy. Em thử một đoạn chương trình chỉ dùng gán, nếu–thì và lặp nhé.",
    expect: "từ chối rõ, nêu đúng hàm/đệ quy; KHÔNG generic; KHÔNG hiện chương trình cắt dở",
  },
  {
    id: "vr-cf7-invalid-variable", narrow: false,
    category: "capability_gap", code: null,
    reason: "Đoạn chương trình dùng một biến khi biến đó chưa có giá trị ban đầu. Em hãy "
          + "cho biết giá trị khởi đầu của biến đó rồi thử lại.",
    expect: "nói biến dùng trước khi có giá trị; KHÔNG lộ đường dẫn validator/enum",
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

const profile = mkdtempSync(join(tmpdir(), "algosim-w2c-"));
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
  await setViewport(vp);                       // TRƯỚC khi trang dựng (VIS-003)
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

/* Chỉ số bước theo LOẠI SỰ KIỆN — để chụp đúng khoảnh khắc cần soi (bước kiểm
 * điều kiện, lượt lặp giữa, bước thoát vòng lặp) thay vì đoán theo số thứ tự. */
const stepIndex = (phase) => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const t = s.useAppStore.getState().active.state;
  const steps = t.trace.steps;
  const has = (st, type, pred) => st.events.some((e) => e.type === type && (!pred || pred(e)));
  const phase = ${JSON.stringify(phase)};
  if (phase === 'initial') return 0;
  if (phase === 'final') return steps.length - 1;
  if (phase === 'first_assign') return steps.findIndex((st) => has(st, 'assign_var'));
  if (phase === 'first_condition') return steps.findIndex((st) => has(st, 'evaluate_condition'));
  if (phase === 'loop_exit')
    return steps.findIndex((st) => has(st, 'enter_branch', (e) => e.branch === 'loop_exit'));
  if (phase === 'mid_iteration') {
    const idx = steps.map((st, i) => (has(st, 'loop_iteration') ? i : -1)).filter((i) => i >= 0);
    return idx.length ? idx[Math.floor(idx.length / 2)] : Math.floor(steps.length / 2);
  }
  return Math.floor((steps.length - 1) / 2);
})()`);

const goToStep = (n) => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  s.useAppStore.getState().goToStep(${n});
  return s.useAppStore.getState().active.state.cursor ?? null;
})()`);

/* SỰ THẬT ĐỌC TỪ ENGINE STATE (không suy từ DOM): ảnh là bằng chứng trình bày,
 * state là bằng chứng ngữ nghĩa. Metadata bắt buộc của artifact nằm ở đây. */
const engineFacts = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const p = await import('/src/core/program.ts');
  const st = s.useAppStore.getState().active;
  const t = st.state;
  const step = t.trace.steps[t.cursor];
  const layout = p.programLines(t.spec);
  const lineToStmt = {};
  for (const [sid, ln] of Object.entries(layout.lineOf)) lineToStmt[ln] = sid;
  let condition = null, branch = null, iteration = null, output = null;
  const changed = [];
  for (const e of step.events) {
    if (e.type === 'evaluate_condition') condition = { expression: e.expression, result: e.result };
    else if (e.type === 'enter_branch') branch = e.branch;
    else if (e.type === 'loop_iteration') iteration = e.iteration;
    else if (e.type === 'assign_var') changed.push(e.name);
    else if (e.type === 'output') output = e.text;
  }
  return JSON.stringify({
    target_id: st.moduleId,
    cursor: t.cursor,
    step_total: t.trace.steps.length,
    current_line: step.line ?? null,
    statement_id: lineToStmt[step.line] ?? null,
    vars: step.snapshot.vars,
    condition, branch, iteration, output,
    changed_vars: changed,
    completion: t.completion,
    pseudocode_lines: layout.lines.length,
  });
})()`);

/* ĐO TRONG TRÌNH DUYỆT THẬT — hợp đồng thị giác §5 + responsive §7. */
const AUDIT_JS = `(() => {
  const root = document.querySelector('main') || document.body;
  const txt = (root.innerText || '').replace(/\\s+/g, ' ');
  const lines = [...root.querySelectorAll('.pseudo-line')];
  const current = lines.filter((el) => el.classList.contains('is-current'));
  const curRect = current[0]?.getBoundingClientRect() ?? null;
  const controls = [...root.querySelectorAll('.player-controls button')];
  const visibleControls = controls.filter((el) => {
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.right <= window.innerWidth + 1;
  });
  const clipped = [...root.querySelectorAll('*')].filter((el) => {
    const r = el.getBoundingClientRect();
    return r.width > 0 && (r.right > window.innerWidth + 1 || r.left < -1);
  });
  // ancestor nào cắt mất mã giả?
  const panel = root.querySelector('.pseudo-panel');
  let clippedByAncestor = false;
  if (panel) {
    const pr = panel.getBoundingClientRect();
    let el = panel.parentElement;
    while (el && el !== document.body) {
      const cs = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      if (cs.overflow === 'hidden' && (pr.bottom > r.bottom + 1 || pr.right > r.right + 1)) {
        clippedByAncestor = true; break;
      }
      el = el.parentElement;
    }
  }
  const TECH = ['ProgramSpec', 'statement_id', 'program_version', 'algorithm.bounded',
                'semantic_incomplete', 'input_insufficient', 'capability_gap',
                'then_body', 'else_body', 'max_iterations', 'expressions',
                'InputKind', 'validate_program', 'undefined', 'null'];
  return JSON.stringify({
    pseudocode_lines_dom: lines.length,
    current_line_count: current.length,
    current_line_text: current[0]?.innerText?.trim() ?? null,
    current_line_in_view: curRect
      ? curRect.top >= -1 && curRect.bottom <= window.innerHeight + 1 : null,
    indentation_present: lines.some((el) =>
      /^\\s{2,}/.test(el.querySelector('.pseudo-text')?.textContent ?? '')),
    condition_has_words: /\\b(ĐÚNG|SAI)\\b/.test(txt),
    shows_branch_text: /Chạy:/.test(txt),
    shows_iteration_text: /Lượt lặp thứ/.test(txt),
    shows_changed_var_text: /Biến vừa đổi/.test(txt),
    shows_completion: /Chương trình kết thúc/.test(txt),
    shows_limit_message: /chưa kết thúc trong giới hạn/.test(txt),
    notice_title: root.querySelector('.notice-title')?.innerText?.trim()
      ?? root.querySelector('h2')?.innerText?.trim() ?? null,
    leaked_tech_tokens: TECH.filter((t) => txt.includes(t)),
    controls_total: controls.length,
    controls_visible: visibleControls.length,
    page_overflows_horizontally:
      document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    clipped_elements: clipped.length,
    pseudocode_clipped_by_ancestor: clippedByAncestor,
    text_sample: txt.slice(0, 1100),
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
  const fixtures = vp.id === "desktop" ? FIXTURES : FIXTURES.filter((f) => f.narrow);
  const refusals = vp.id === "desktop" ? REFUSALS : REFUSALS.filter((r) => r.narrow);

  for (const fx of fixtures) {
    await freshPage(vp);
    await loadEnvelope(fx.envelope);
    await sleep(400);
    for (const phase of fx.marks) {
      const idx = await stepIndex(phase);
      if (idx === null || idx < 0) {
        records.push({ fixture: fx.id, viewport: vp.id, phase, error: "không tìm thấy bước" });
        continue;
      }
      await goToStep(idx);
      await sleep(320);
      const png = await shot(`${fx.id}-${vp.id}-${phase}`);
      records.push({
        fixture_id: fx.id, target_id: TARGET, viewport: vp.id, phase, png,
        engine: JSON.parse(await engineFacts()),
        audit: JSON.parse(await evaluate(AUDIT_JS)),
        expect: fx.expect,
      });
      console.log(`  ✓ ${fx.id} ${vp.id}/${phase}`);
    }
  }

  for (const rf of refusals) {
    await freshPage(vp);
    await loadUnsupported(rf.reason, rf.category, rf.code);
    await sleep(400);
    const png = await shot(`${rf.id}-${vp.id}`);
    records.push({
      fixture_id: rf.id, target_id: TARGET, viewport: vp.id, phase: "notice", png,
      failure_category: rf.category, error_code: rf.code, reason: rf.reason,
      audit: JSON.parse(await evaluate(AUDIT_JS)),
      expect: rf.expect,
    });
    console.log(`  ✓ ${rf.id} ${vp.id}`);
  }
}

writeFileSync(join(resolve(OUT_DIR, ".."), "captures.json"),
  JSON.stringify({
    wave: "M17 W2C-VR",
    target: TARGET,
    generated_at: new Date().toISOString(),
    note: "Viewport đặt TRƯỚC khi trang dựng, nạp lại trang cho từng viewport "
        + "(bài học VIS-003, RC1 §E1). Spec đi qua CHÍNH validateProgramSpec + "
        + "runProgram của sản phẩm — không có engine fixture song song. Phán "
        + "quyết REAL/PARTIAL/BROKEN do NGƯỜI xem PNG chấm; assertion chỉ hỗ trợ.",
    app: APP, viewports: VIEWPORTS, records,
  }, null, 2) + "\n", "utf8");

console.log(`\n${records.length} bản ghi → ${OUT_DIR}`);
ws.close();
chrome.kill();
