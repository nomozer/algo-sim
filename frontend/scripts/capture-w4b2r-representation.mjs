/**
 * capture-w4b2r-representation.mjs — W4B-2R: chính sách biểu diễn + vòng đời
 * Quan sát, đo trong Chrome THẬT qua CDP.
 *
 * Chứng minh cho MỖI bài làm chứng (chọn theo CƠ CHẾ, §31 — không theo ảnh ai gửi):
 *   READY/PAUSED sau khi nạp   — không tự chạy
 *   toggle 2D/3D CHỈ khi chính sách là 2d_and_3d_justified
 *   chạy trọn canonical bằng nút Tiến, KHÔNG trả lời gì, prediction vẫn null
 *
 * Hạ tầng CDP dùng lại khuôn `capture-w4b2i-interaction.mjs` (repo chưa có module
 * CDP dùng chung — nợ có sẵn, không refactor 9 script giữa wave này), gồm cả
 * `warmup()` + thử lại `Promise was collected` (Vite pre-bundle làm reload trang).
 *
 * Chạy:  npm run dev  (cửa sổ khác, strictPort, tiến trình MỚI)
 *        node scripts/capture-w4b2r-representation.mjs [--port 3000] [--out <dir>]
 */

import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const PORT = argOf("--port", "3000");
const APP = `http://localhost:${PORT}`;
const OUT = resolve(argOf("--out", "../docs/evaluation/m17/w4b2r-representation"));
const CDP_PORT = 9000 + Math.floor(Math.random() * 900);
mkdirSync(OUT, { recursive: true });

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

const profile = mkdtempSync(join(tmpdir(), "algosim-w4b2r-"));
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", `--remote-debugging-port=${CDP_PORT}`,
  `--user-data-dir=${profile}`, `--window-size=${argOf("--window", "1920,1080")}`,
  "--hide-scrollbars", "about:blank",
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const shutdown = () => { try { chrome.kill(); } catch { /* đã chết */ } };
process.on("SIGINT", () => { shutdown(); process.exit(130); });

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
const evaluateOnce = async (expr) => {
  const r = await send("Runtime.evaluate", {
    expression: expr, awaitPromise: true, returnByValue: true,
  });
  if (r.error) { const e = new Error(r.error.message); e.cdp = true; throw e; }
  if (r.result?.exceptionDetails) {
    throw new Error(JSON.stringify(r.result.exceptionDetails.exception ?? r.result.exceptionDetails));
  }
  return r.result?.result?.value;
};
const evaluate = async (expr) => {
  let last;
  for (let i = 0; i < 6; i += 1) {
    try { return await evaluateOnce(expr); }
    catch (e) { if (!e.cdp) throw e; last = e; await sleep(1200); }
  }
  throw last;
};
const warmup = async () => {
  for (let i = 0; i < 8; i += 1) {
    try {
      if (await evaluateOnce(`(async () => {
        await import('/src/data/offline-catalog.ts');
        await import('/src/state/store.ts');
        await import('/src/simulations/index.ts');
        await import('/src/simulations/registry.ts');
        await import('/src/simulations/renderer.ts');
        return true;
      })()`)) return true;
    } catch { /* Vite còn reload */ }
    await sleep(1500);
  }
  return false;
};
const shot = async (name) => {
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(OUT, `${name}.png`), Buffer.from(r.result.data, "base64"));
};

const results = [];
let failed = 0;
const check = (name, ok, detail) => {
  results.push({ name, ok: !!ok, detail });
  if (!ok) failed += 1;
  console.log(`${ok ? "  PASS" : "  FAIL"}  ${name}${detail !== undefined ? `  — ${JSON.stringify(detail)}` : ""}`);
};

/* BÀI LÀM CHỨNG CHỌN THEO CƠ CHẾ (§31), không theo ảnh người dùng gửi. */
const PILOTS = [
  { id: "algorithm.binary_search", mechanism: "tìm kiếm — thu hẹp khoảng" },
  { id: "algorithm.insertion_sort", mechanism: "sắp xếp — giữ/dời/chèn" },
  { id: "logic.and_gate", mechanism: "logic — tín hiệu qua cổng" },
  { id: "binary.decimal_to_binary", mechanism: "hệ cơ số — trọng số vị trí" },
  { id: "generic.rule_scene", mechanism: "cảnh do DSL mô tả" },
  { id: "network.packet_routing", mechanism: "mạng — topology + đường đi (ĐỔI chính sách)" },
  { id: "network.protocol_encapsulation", mechanism: "mạng — tầng giao thức (3D SƯ PHẠM)" },
];

const load = (simId) => evaluate(`(async () => {
  const c = await import('/src/data/offline-catalog.ts');
  const s = await import('/src/state/store.ts');
  const r = await import('/src/simulations/index.ts');
  const reg = await import('/src/simulations/registry.ts');
  if (reg.listSimulations().length === 0) r.registerAllSimulations();
  s.useAppStore.getState().reset();
  const list = c.offlineCatalog();
  const i = list.findIndex((x) => x.simId === ${JSON.stringify(simId)});
  if (i < 0) return { ok: false, why: 'khong co mau offline' };
  s.useAppStore.getState().loadEnvelope(list[i].envelope);
  return { ok: !!s.useAppStore.getState().active };
})()`);

/** Sidecar §46 — đọc từ STORE + POLICY thật, không suy từ DOM. */
const snapshot = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const reg = await import('/src/simulations/registry.ts');
  const rend = await import('/src/simulations/renderer.ts');
  const st = s.useAppStore.getState();
  const a = st.active;
  if (!a) return { active: false };
  const mod = reg.getSimulation(a.moduleId);
  return {
    active: true,
    target: a.moduleId,
    representationPolicy: rend.representationPolicyOf(mod),
    availableModes: rend.availableVisualModes(mod),
    rendererOwner: rend.rendererFor(mod, rend.effectiveVisualMode(mod, st.visualMode))?.name ?? null,
    playing: st.playing,
    timelineIndex: mod.timeline ? mod.timeline.currentStep(a.state) : null,
    timelineTotal: mod.timeline ? mod.timeline.stepCount(a.state) : null,
    predictionCapability: mod.predict !== undefined,
    whatIfCapability: mod.apply(a.state, { type: 'noop' }) !== a.state,
    prediction: st.prediction ? st.prediction.verdict : null,
    resultOwner: 'engine:' + a.moduleId,
    toggleInDom: !!document.querySelector('.visual-mode-toggle'),
    modeButtons: [...document.querySelectorAll('.visual-mode-toggle button')].map((b) => b.textContent),
  };
})()`);

const nextStep = () => evaluate(`(() => {
  const b = [...document.querySelectorAll('button')]
    .find((x) => (x.getAttribute('title') || '') === 'Tiến một bước' && !x.disabled);
  if (!b) return false; b.click(); return true;
})()`);

await send("Page.enable");
await send("Runtime.enable");
await send("Page.navigate", { url: APP });
await sleep(2500);
if (!(await warmup())) { console.error("Vite không pre-bundle xong."); shutdown(); process.exit(2); }
await sleep(800);

const sidecars = [];
for (const pilot of PILOTS) {
  console.log(`\n── ${pilot.id}  (${pilot.mechanism}) ──`);
  const okLoad = await load(pilot.id);
  if (!okLoad?.ok) { check(`${pilot.id}: nạp được mẫu offline`, false, okLoad); continue; }
  await sleep(500);

  const ready = await snapshot();
  check(`${pilot.id}: dấu vân tay đúng target`, ready.target === pilot.id, ready.target);
  check(`${pilot.id}: READY/PAUSED — không tự chạy`, ready.playing === false, { playing: ready.playing });
  check(`${pilot.id}: con trỏ ở bước đầu`, ready.timelineIndex === null || ready.timelineIndex === 0,
    ready.timelineIndex);

  // §22 — toggle CHỈ khi chính sách cho phép
  const wantToggle = ready.representationPolicy === "2d_and_3d_justified";
  check(`${pilot.id}: chính sách ${ready.representationPolicy} ⇒ toggle ${wantToggle ? "CÓ" : "KHÔNG"}`,
    ready.toggleInDom === wantToggle,
    { policy: ready.representationPolicy, toggle: ready.toggleInDom, buttons: ready.modeButtons });

  await shot(`${pilot.id.replace(/\./g, "_")}-1-ready`);

  // Canonical chạy trọn bằng nút Tiến, KHÔNG trả lời gì
  if (ready.timelineTotal && ready.timelineTotal > 1) {
    const mid = Math.floor(ready.timelineTotal / 2);
    for (let k = 0; k < mid; k += 1) { await nextStep(); await sleep(90); }
    await shot(`${pilot.id.replace(/\./g, "_")}-2-midrun`);
    for (let k = 0; k < ready.timelineTotal + 2; k += 1) { await nextStep(); await sleep(70); }
    const end = await snapshot();
    await shot(`${pilot.id.replace(/\./g, "_")}-3-baseline-complete`);
    check(`${pilot.id}: chạy TRỌN canonical mà không trả lời gì`,
      end.timelineIndex === end.timelineTotal - 1, { at: end.timelineIndex, total: end.timelineTotal });
    check(`${pilot.id}: prediction vẫn null suốt lượt Quan sát`,
      end.prediction === null, end.prediction);
    sidecars.push({ ...pilot, ready, end });
  } else {
    check(`${pilot.id}: cảnh khám phá (1 khung) — không có bước để chạy`, true,
      { total: ready.timelineTotal });
    sidecars.push({ ...pilot, ready, end: null });
  }
}

writeFileSync(join(OUT, "sidecar.json"), JSON.stringify({
  wave: "W4B-2R",
  when: new Date().toISOString(),
  app: APP,
  viewport: argOf("--window", "1920,1080"),
  pilots: sidecars,
  checks: results,
  passed: results.length - failed,
  total: results.length,
}, null, 2));
console.log(`\n${results.length - failed}/${results.length} PASS · ảnh + sidecar → ${OUT}`);
shutdown();
process.exit(failed === 0 ? 0 : 1);
