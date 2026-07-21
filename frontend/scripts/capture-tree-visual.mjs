/**
 * capture-tree-visual.mjs — CHỤP RENDERER CÂY TRÊN BROWSER THẬT (M17-VR1)
 *
 * Dùng LẠI hạ tầng CDP của audit-layout.mjs (Chrome headless + WebSocket thô),
 * KHÔNG thêm framework E2E. Nạp fixture bằng cách import module store qua
 * module graph của Vite dev (`await import('/src/state/store.ts')`) rồi gọi
 * `loadEnvelope` — KHÔNG sửa production code, không thêm dev hook.
 *
 * Mỗi fixture chụp: initial (bước 0) · mid (giữa timeline) · final (bước cuối).
 * Fixture insufficient chụp thông điệp từ chối learner-facing.
 *
 * Chạy:  node scripts/capture-tree-visual.mjs        (cần `npm run dev`)
 *        node scripts/capture-tree-visual.mjs --port 3001
 */

import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const APP = `http://localhost:${argOf("--port", "3000")}`;
const CDP_PORT = 9334;
const OUT_DIR = resolve(argOf("--out", "../docs/evaluation/m17/wave2a/visual"));

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

/* ── 6 fixture theo visual_fixtures.md ─────────────────────────────────── */
const N = (id, left = null, right = null) => ({ id, label: id, left, right });
const treeEnv = (id, title, variant, rootId, nodes) => ({
  id, title, variant,
  envelope: {
    status: "ok", simulation_id: "tree.traversal", domain: "tree", visual_mode: "2d",
    title, description: null, notes: null,
    config: { specVersion: "tree-1.0", variant, rootId, nodes, notes: null },
  },
});

const FIXTURES = [
  treeEnv("vr1-preorder-balanced", "Duyệt trước — cây cân bằng", "preorder", "A",
    [N("A", "B", "C"), N("B", "D", "E"), N("C", "F", "G"), N("D"), N("E"), N("F"), N("G")]),
  treeEnv("vr1-inorder-incomplete", "Duyệt giữa — cây khuyết", "inorder", "A",
    [N("A", "B", "C"), N("B", "D"), N("C"), N("D")]),
  treeEnv("vr1-postorder-skewed", "Duyệt sau — cây lệch trái", "postorder", "A",
    [N("A", "B"), N("B", "C"), N("C", "D"), N("D")]),
  treeEnv("vr1-levelorder-multilevel", "Duyệt theo mức — nhiều tầng", "level_order", "A",
    [N("A", "B", "C"), N("B", "D", "E"), N("C", "F", "G"), N("D", "H"), N("E"), N("F"), N("G"), N("H")]),
  treeEnv("vr1-single-node", "Cây một nút — biên", "preorder", "X", [N("X")]),
];

/* Fixture 6: thông điệp từ chối learner-facing (không phải envelope ok) */
const INSUFFICIENT = {
  id: "vr1-insufficient-message",
  reason: "Đề yêu cầu duyệt cây nhưng chưa cho cấu trúc cây cụ thể (các nút có tên và quan hệ con trái/con phải giữa chúng). Hãy mô tả rõ cây (ví dụ: gốc A, A có con trái B và con phải C…) rồi thử lại — hệ không tự dựng cây thay bạn.",
};

/* ── CDP ────────────────────────────────────────────────────────────────── */
const profile = mkdtempSync(join(tmpdir(), "algosim-vr1-"));
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
  if (ex) throw new Error(JSON.stringify(ex).slice(0, 400));
  return r.result?.result?.value;
};

await send("Page.enable");
await send("Runtime.enable");

mkdirSync(OUT_DIR, { recursive: true });

async function shot(name) {
  const r = await send("Page.captureScreenshot", { format: "png" });
  const data = r.result?.data;
  if (!data) throw new Error(`captureScreenshot thất bại: ${name}`);
  const path = join(OUT_DIR, `${name}.png`);
  writeFileSync(path, Buffer.from(data, "base64"));
  return path;
}

/** Nạp envelope qua module graph Vite (không cần dev hook trong production). */
async function loadEnvelope(envelope) {
  return evaluate(`(async () => {
    const m = await import('/src/state/store.ts');
    m.useAppStore.getState().loadEnvelope(${JSON.stringify(envelope)});
    return true;
  })()`);
}

async function loadUnsupported(reason) {
  return evaluate(`(async () => {
    const m = await import('/src/state/store.ts');
    m.useAppStore.getState().loadUnsupported({
      status: 'unsupported',
      reason: ${JSON.stringify(reason)},
      learner_reason: ${JSON.stringify(reason)},
      failure_category: 'insufficient_specification',
    });
    return true;
  })()`);
}

const goToStep = (n) => evaluate(`(async () => {
  const m = await import('/src/state/store.ts');
  m.useAppStore.getState().goToStep(${n});
  return m.useAppStore.getState().active.state.cursor;
})()`);

const stepCount = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const r = await import('/src/simulations/registry.ts');
  const st = s.useAppStore.getState();
  return r.getSimulation(st.active.moduleId).timeline.stepCount(st.active.state);
})()`);

const engineState = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const st = s.useAppStore.getState().active.state;
  const step = st.steps[st.cursor];
  return JSON.stringify({
    cursor: st.cursor, frontierKind: st.frontierKind, visitedOrder: st.visitedOrder,
    stepKind: step.kind, current: step.current, frontier: step.frontierAfter,
    visitedSoFar: step.visitedSoFar, narration: step.narration,
  });
})()`);

/* ── chạy ───────────────────────────────────────────────────────────────── */
await send("Page.navigate", { url: APP });
await sleep(2500);

const records = [];
for (const fx of FIXTURES) {
  await loadEnvelope(fx.envelope);
  await sleep(600);
  const total = await stepCount();
  const marks = [
    ["initial", 0],
    ["mid", Math.max(1, Math.floor(total / 2))],
    ["final", total - 1],
  ];
  const shots = [];
  for (const [tag, n] of marks) {
    await goToStep(n);
    await sleep(450);
    const state = JSON.parse(await engineState());
    const path = await shot(`${fx.id}-${tag}`);
    shots.push({ tag, step: n, screenshot: path.replace(/\\/g, "/"), authoritative_state: state });
    console.log(`  ${fx.id} ${tag} (bước ${n}/${total - 1}) → ${path}`);
  }
  records.push({ fixture_id: fx.id, variant: fx.variant, title: fx.title, total_steps: total, captures: shots });
}

// fixture 6 — thông điệp từ chối
await loadUnsupported(INSUFFICIENT.reason);
await sleep(600);
const msgPath = await shot(`${INSUFFICIENT.id}`);
console.log(`  ${INSUFFICIENT.id} → ${msgPath}`);
records.push({
  fixture_id: INSUFFICIENT.id, variant: null, title: "Thông điệp thiếu dữ kiện",
  total_steps: 0,
  captures: [{ tag: "refusal", step: null, screenshot: msgPath.replace(/\\/g, "/"), authoritative_state: { reason: INSUFFICIENT.reason } }],
});

writeFileSync(
  join(OUT_DIR, "captures.json"),
  JSON.stringify({ app: APP, generated_at: new Date().toISOString(), records }, null, 2) + "\n",
  "utf-8",
);
console.log(`\nĐã chụp ${records.reduce((n, r) => n + r.captures.length, 0)} ảnh → ${OUT_DIR}`);

ws.close();
chrome.kill();
