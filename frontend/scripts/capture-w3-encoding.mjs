/**
 * capture-w3-encoding.mjs — M17 W3-VR: REVIEW THỊ GIÁC `binary.character_encoding`.
 *
 * Dùng LẠI hạ tầng CDP của `capture-w2c-program.mjs` (Chrome thật + WebSocket
 * thô, fixture nạp qua module graph Vite). KHÔNG sửa production để chụp, KHÔNG
 * dựng engine fixture song song: spec đi qua CHÍNH `validateCharEncodingSpec` +
 * `runCharacterEncoding` mà sản phẩm dùng.
 *
 * Viewport đặt TRƯỚC khi trang dựng, nạp lại trang cho từng viewport (bài học
 * VIS-003, RC1 §E1).
 *
 * Chạy:  npm run dev  (cửa sổ khác)
 *        node scripts/capture-w3-encoding.mjs [--port 3000]
 */

import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const APP = `http://localhost:${argOf("--port", "3000")}`;
const CDP_PORT = 9345;
const OUT_DIR = resolve(argOf("--out", "../docs/evaluation/m17/w3-sim/visual/character-encoding"));

const TARGET = "binary.character_encoding";
const VIEWPORTS = [
  { id: "desktop", width: 1440, height: 1000 },
  { id: "narrow", width: 768, height: 900 },
];

const env = (title, config) => ({
  status: "ok", simulation_id: TARGET, domain: "binary",
  visual_mode: "2d", title, description: null, notes: null, config,
});
const spec = (text, encoding) =>
  ({ spec_version: "charenc-1.0", text, encoding });

/*
 * M17 W3-SIM — mốc chụp giải theo TÊN PHASE, không phải chỉ số cứng. Bản cũ ghi
 * `["convert_to_binary", 2]`: đúng khi mỗi ký tự cố định 4 phase, sai ngay khi
 * số bước chia thay đổi theo giá trị mã. Nay hỏi engine "phase này ở bước nào".
 */
const FIXTURES = [
  {
    id: "sim-enc1-ascii-one-char",
    envelope: env("Mã hoá ký tự", spec("A", "ascii")),
    narrow: true,
    marks: [
      ["initial", { phase: "select_character" }],
      ["first_division", { phase: "divide_step", nth: 0 }],
      ["middle_division", { phase: "divide_step", nth: 3 }],
      ["read_remainders", { phase: "read_remainders" }],
      ["final", { last: true }],
    ],
    expect: "thấy PHÉP CHIA thật: 65:2=32 dư 1, rồi 32:2=16 dư 0…; dãy bit chỉ "
          + "xuất hiện SAU khi đọc ngược số dư",
  },
  {
    id: "sim-enc2-unicode-bmp",
    envelope: env("Mã hoá ký tự", spec("ế", "unicode_codepoint")),
    narrow: false,
    marks: [
      ["mapped_code_point", { phase: "map_to_code" }],
      ["division_over_255", { phase: "divide_step", nth: 0 }],
      ["final", { last: true }],
    ],
    expect: "ế → U+1EBF → 7871; chuỗi chia bắt đầu từ 7871 (vượt xa trần 255 "
          + "của decimal_to_binary)",
  },
  {
    id: "sim-enc3-multi-char",
    envelope: env("Mã hoá ký tự", spec("Tin", "ascii")),
    narrow: false,
    marks: [
      ["first_char_detail", { phase: "divide_step", nth: 2 }],
      ["compact_second_char", { phase: "convert_compact" }],
      ["final", { last: true }],
    ],
    expect: "ký tự ĐẦU bung đầy đủ chuỗi chia; ký tự sau rút gọn và NÓI RÕ "
          + "'áp dụng CÙNG quy tắc chia lấy dư'",
  },
];

/*
 * Emoji refusal: UI từ chối KHÔNG đổi trong W3-SIM ⇒ dùng lại bằng chứng
 * `docs/evaluation/m17/w3/visual/character-encoding/vr-enc4-emoji-refusal-*.png`.
 * Chụp lại chỉ để tăng số lượng là lãng phí (§13).
 */
const REFUSALS = [];

/* ══════════════ CDP ══════════════ */
const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

const profile = mkdtempSync(join(tmpdir(), "algosim-w3-"));
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
  await setViewport(vp);                      // TRƯỚC khi trang dựng (VIS-003)
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

const stepTotal = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  return s.useAppStore.getState().active.state.trace.steps.length;
})()`);

const goToStep = (n) => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  s.useAppStore.getState().goToStep(${n});
  return s.useAppStore.getState().active.state.cursor ?? null;
})()`);

/* SỰ THẬT ĐỌC TỪ ENGINE STATE — ảnh là bằng chứng trình bày, state là bằng
 * chứng ngữ nghĩa. Metadata bắt buộc của artifact nằm ở đây. */
const engineFacts = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const e = await import('/src/simulations/domains/binary/encoding-module.ts' +
                         'x'.replace('x','x'));
  const st = s.useAppStore.getState().active;
  const t = st.state;
  const m = t.meta[Math.max(0, Math.min(t.cursor, t.meta.length - 1))];
  return JSON.stringify({
    target_id: st.moduleId,
    text: t.spec.text,
    encoding: t.spec.encoding,
    cursor: t.cursor,
    step_total: t.trace.steps.length,
    phase: m.phase,
    char_index: m.charIndex,
    detailed: m.detailed,
    division: m.division ?? null,
    committed_rows: m.committed,
    rows_total: t.rows.length,
    rows: t.rows.map((r) => ({ char: r.char, label: r.label, cp: r.codePoint,
                               dec: r.decimal, bin: r.binary })),
    narration: t.trace.steps[t.cursor].narration,
  });
})()`);

/**
 * Giải mốc chụp thành CHỈ SỐ BƯỚC bằng cách hỏi chính `state.meta` của engine.
 * Không đoán, không số học trên cursor — nếu phase không tồn tại thì báo lỗi to
 * chứ không âm thầm chụp nhầm bước.
 */
const resolveMark = (mark) => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const t = s.useAppStore.getState().active.state;
  const spec = ${JSON.stringify(mark)};
  if (spec.last) return String(t.trace.steps.length - 1);
  const hits = t.meta
    .map((m, i) => ({ m, i }))
    .filter((x) => x.m.phase === spec.phase);
  if (!hits.length) return 'ERR:không có phase ' + spec.phase;
  const pick = hits[Math.min(spec.nth ?? 0, hits.length - 1)];
  return String(pick.i);
})()`);

/* ĐO TRONG TRÌNH DUYỆT THẬT — hợp đồng thị giác §7 + responsive §8. */
const AUDIT_JS = `(() => {
  const root = document.querySelector('main') || document.body;
  const txt = (root.innerText || '').replace(/\\s+/g, ' ');
  const rows = [...root.querySelectorAll('tbody tr')];
  const current = rows.filter((r) => r.classList.contains('is-current'));
  const table = root.querySelector('table');
  const controls = [...root.querySelectorAll('.player-controls button')];
  const visibleControls = controls.filter((el) => {
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.right <= window.innerWidth + 1;
  });
  const clipped = [...root.querySelectorAll('*')].filter((el) => {
    const r = el.getBoundingClientRect();
    return r.width > 0 && (r.right > window.innerWidth + 1 || r.left < -1);
  });
  let tableOverflows = false;
  if (table) {
    const tr = table.getBoundingClientRect();
    tableOverflows = tr.right > window.innerWidth + 1;
  }
  const TECH = ['CharacterEncodingSpec', 'binary.character_encoding', 'InputKind',
                'TEXT_AND_ENCODING', 'charenc-1.0', 'spec_version', 'code_point',
                'select_character', 'map_to_code', 'begin_conversion', 'divide_step',
                'read_remainders', 'convert_compact', 'commit_row', 'charIndex',
                'capability_gap', 'undefined', 'null', 'NaN'];
  return JSON.stringify({
    row_count_dom: rows.length,
    current_row_count: current.length,
    current_row_text: current[0]?.innerText?.replace(/\\s+/g, ' ').trim() ?? null,
    table_present: !!table,
    shows_completion: /Đã mã hoá/.test(txt),
    shows_placeholder: /…/.test(txt),
    notice_present: !!root.querySelector('.eyebrow'),
    notice_eyebrow: root.querySelector('.eyebrow')?.innerText?.trim() ?? null,
    simulation_mounted: !!table,
    leaked_tech_tokens: TECH.filter((t) => txt.includes(t)),
    controls_total: controls.length,
    controls_visible: visibleControls.length,
    page_overflows_horizontally:
      document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    table_overflows_viewport: tableOverflows,
    clipped_elements: clipped.length,
    text_sample: txt.slice(0, 1200),
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
    const total = await stepTotal();
    // 768px chỉ cần MỘT ảnh: panel chia là thứ duy nhất có nguy cơ tràn (§13)
    const marks = vp.id === "narrow"
      ? fx.marks.filter(([name]) => name === "first_division")
      : fx.marks;
    for (const [phase, mark] of marks) {
      const raw = await resolveMark(mark);
      if (raw.startsWith("ERR:")) throw new Error(`${fx.id}/${phase}: ${raw.slice(4)}`);
      const idx = Math.min(Number(raw), total - 1);
      await goToStep(idx);
      await sleep(300);
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
      failure_category: rf.category, reason: rf.reason,
      audit: JSON.parse(await evaluate(AUDIT_JS)),
      expect: rf.expect,
    });
    console.log(`  ✓ ${rf.id} ${vp.id}`);
  }
}

writeFileSync(join(resolve(OUT_DIR, ".."), "captures.json"),
  JSON.stringify({
    wave: "M17 W3-SIM",
    target: TARGET,
    generated_at: new Date().toISOString(),
    note: "Viewport đặt TRƯỚC khi trang dựng, nạp lại trang cho từng viewport "
        + "(VIS-003). Spec đi qua CHÍNH validateCharEncodingSpec + "
        + "runCharacterEncoding của sản phẩm; nhị phân DẪN RA từ chuỗi số dư "
        + "của divideSteps() (base_conversion). Phán quyết REAL/PARTIAL/BROKEN do NGƯỜI xem PNG.",
    app: APP, viewports: VIEWPORTS, records,
  }, null, 2) + "\n", "utf8");

console.log(`\n${records.length} bản ghi → ${OUT_DIR}`);
ws.close();
chrome.kill();
