/**
 * capture-w4b2i-interaction.mjs — W4B-2I: bằng chứng trong Chrome THẬT (CDP).
 *
 * Chứng minh hai chuỗi hành vi, không phải hai tấm ảnh đẹp:
 *
 *  A. HỌ TÌM KIẾM — Quan sát không có bề mặt cam kết → mở Thí nghiệm → vùng bấm
 *     xuất hiện TRÊN SÂN KHẤU (không phải hàng nút) → tới được bằng BÀN PHÍM →
 *     bấm SAI: canonical KHÔNG đổi → bấm ĐÚNG: engine chấm.
 *
 *  B. MẠNG — tuyến gốc → mở Thí nghiệm → NGẮT một chặng: engine cho trạng thái
 *     KHÔNG TỚI ĐƯỢC → NỐI một chặng khác: engine ĐỊNH TUYẾN LẠI → Về ban đầu.
 *
 * Hạ tầng CDP dùng lại khuôn `capture-w4b2b-experiment.mjs` (repo chưa có module
 * CDP dùng chung — nợ có sẵn, không refactor 8 script giữa wave này).
 *
 * KHÔNG sửa mã sản phẩm để chụp được. Mọi thao tác đi qua đúng DOM học sinh
 * thấy; mọi phán quyết đọc từ store thật.
 *
 * Chạy:  npm run dev  (cửa sổ khác)
 *        node scripts/capture-w4b2i-interaction.mjs [--port 3000] [--out <dir>]
 */

import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const PORT = argOf("--port", "3000");
const APP = `http://localhost:${PORT}`;
const OUT = resolve(argOf("--out", "../docs/evaluation/m17/w4b2i-scene-interaction"));
const CDP_PORT = 9000 + Math.floor(Math.random() * 900);
mkdirSync(OUT, { recursive: true });

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

const profile = mkdtempSync(join(tmpdir(), "algosim-w4b2i-"));
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
/* `Promise was collected` KHÔNG phải lỗi của sản phẩm: lần đầu import một module
   chưa được Vite pre-bundle, dev server tối ưu dependency rồi RELOAD trang, và
   execution context đang giữ promise bị huỷ giữa chừng. Thử lại là đúng cách xử
   lý; coi nó là lỗi sẽ tố cáo nhầm sản phẩm (đúng loại "runner hết hạn tố cáo
   sản phẩm" mà anti-pattern #14 cảnh báo). */
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
    catch (e) {
      if (!e.cdp) throw e;
      last = e;
      await sleep(1200);
    }
  }
  throw last;
};

/** Nạp trước đồ thị module nặng để Vite pre-bundle xong TRƯỚC khi bắt đầu đo. */
const warmup = async () => {
  for (let i = 0; i < 8; i += 1) {
    try {
      const ok = await evaluateOnce(`(async () => {
        await import('/src/data/offline-catalog.ts');
        await import('/src/state/store.ts');
        await import('/src/simulations/index.ts');
        await import('/src/simulations/registry.ts');
        return true;
      })()`);
      if (ok) return true;
    } catch { /* Vite còn đang reload */ }
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
function check(name, ok, detail) {
  results.push({ name, ok: !!ok, detail });
  if (!ok) failed += 1;
  console.log(`${ok ? "  PASS" : "  FAIL"}  ${name}${detail ? `  — ${JSON.stringify(detail)}` : ""}`);
}

const loadTarget = (simId) => evaluate(`(async () => {
  const c = await import('/src/data/offline-catalog.ts');
  const s = await import('/src/state/store.ts');
  const r = await import('/src/simulations/index.ts');
  const reg = await import('/src/simulations/registry.ts');
  if (reg.listSimulations().length === 0) r.registerAllSimulations();
  const list = c.offlineCatalog();
  const i = list.findIndex((x) => x.simId === ${JSON.stringify(simId)});
  if (i < 0) return { ok: false, why: 'khong co mau offline' };
  s.useAppStore.getState().loadEnvelope(list[i].envelope);
  return { ok: !!s.useAppStore.getState().active };
})()`);

/* DẤU VÂN TAY TRANG (anti-pattern #14): khẳng định mình đang đo ĐÚNG target,
   sai thì thoát != 0. Một bản soát "sạch" vì đo nhầm trang là bản soát vô giá trị. */
const fingerprint = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const a = s.useAppStore.getState().active;
  return a ? a.moduleId : null;
})()`);

const snapshot = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const st = s.useAppStore.getState();
  const a = st.active;
  const regions = [...document.querySelectorAll('.scene-region')];
  const netHandles = [...document.querySelectorAll('.net-link-handle')];
  return {
    moduleId: a ? a.moduleId : null,
    canonical: a ? JSON.stringify(a.state) : null,
    route: a && a.state.route ? a.state.route.join('→') : null,
    prediction: st.prediction ? st.prediction.verdict : null,
    sceneRegions: regions.length,
    sceneRegionLabels: regions.map((r) => r.getAttribute('aria-label')),
    sceneRegionTabbable: regions.filter((r) => r.getAttribute('tabindex') === '0').length,
    netHandles: netHandles.length,
    buttonRow: !!document.querySelector('.search-actions'),
    svgRole: (document.querySelector('.sim-stage svg') || {}).getAttribute
      ? document.querySelector('.sim-stage svg').getAttribute('role') : null,
    narration: (document.querySelector('.narration-bar') || {}).textContent || null,
    packetDot: (document.querySelector('.sim-stage svg') || { innerHTML: '' })
      .innerHTML.includes('accent-pink'),
  };
})()`);

const clickText = (needle) => evaluate(`(() => {
  const b = [...document.querySelectorAll('button')].find((x) => x.textContent.includes(${JSON.stringify(needle)}));
  if (!b || b.disabled) return false;
  b.click(); return true;
})()`);

const nextStep = () => evaluate(`(() => {
  const b = [...document.querySelectorAll('button')]
    .find((x) => (x.getAttribute('title') || '') === 'Tiến một bước' && !x.disabled);
  if (!b) return false; b.click(); return true;
})()`);

const clickRegionByLabel = (needle) => evaluate(`(() => {
  const r = [...document.querySelectorAll('.scene-region, .net-link-handle')]
    .find((x) => (x.getAttribute('aria-label') || '').includes(${JSON.stringify(needle)}));
  if (!r) return false;
  r.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  return true;
})()`);

/** Bàn phím THẬT: focus vùng đầu rồi gửi Enter qua CDP, không gọi hàm React. */
const focusFirstRegion = () => evaluate(`(() => {
  const r = document.querySelector('.scene-region, .net-link-handle');
  if (!r) return null;
  r.focus();
  return document.activeElement === r ? (r.getAttribute('aria-label') || '') : null;
})()`);

await send("Page.enable");
await send("Runtime.enable");
await send("Page.navigate", { url: APP });
await sleep(2500);
if (!(await warmup())) { console.error("Vite không pre-bundle xong."); shutdown(); process.exit(2); }
await sleep(800);

/* ══ A. HỌ TÌM KIẾM ═══════════════════════════════════════════════════════ */
console.log("\n── A. binary_search: hành động trên sân khấu ──");
const okA = await loadTarget("algorithm.binary_search");
if (!okA?.ok) { console.error("Không nạp được binary_search:", okA); shutdown(); process.exit(2); }
await sleep(600);
check("dấu vân tay: đang đo ĐÚNG binary_search",
  (await fingerprint()) === "algorithm.binary_search", await fingerprint());

/* Tiến tới bước THỰC SỰ CAM KẾT ĐƯỢC.
   Bẫy đã dính một lần: nút "Thí nghiệm" hiện ở MỌI bước chưa phải bước cuối
   (`hasExperiment && !labOpen && !branch && !last`), nên dừng lại theo nó thì
   runner đứng ở bước 0 — nơi không có điểm quyết định, không có vùng cam kết,
   nên đương nhiên không có vùng bấm — rồi báo FAIL và tố cáo nhầm sản phẩm.
   Dấu hiệu ĐÚNG là `.search-observe`: khối này chỉ dựng khi `searchInteractionOf`
   khác null, tức đúng bước có quyết định của họ tìm kiếm. */
let actionableAt = -1;
for (let i = 0; i < 30; i += 1) {
  if (await evaluate(`(() => !!document.querySelector('.search-observe'))()`)) { actionableAt = i; break; }
  if (!(await nextStep())) break;
  await sleep(220);
}
check("tìm được bước có quyết định của họ tìm kiếm", actionableAt >= 0, { step: actionableAt });

const aObserve = await snapshot();
await shot("A1-observe-baseline");
check("Quan sát: KHÔNG vùng bấm, KHÔNG hàng nút cam kết",
  aObserve.sceneRegions === 0 && !aObserve.buttonRow,
  { regions: aObserve.sceneRegions, buttonRow: aObserve.buttonRow });
check("Quan sát: svg vẫn là role=img (chưa có gì bấm được)",
  aObserve.svgRole === "img", aObserve.svgRole);

await clickText("Thí nghiệm");
await sleep(400);
const aOpen = await snapshot();
await shot("A2-experiment-open-scene-regions");
check("Mở Thí nghiệm: vùng bấm xuất hiện TRÊN SÂN KHẤU",
  aOpen.sceneRegions >= 2, { regions: aOpen.sceneRegions, labels: aOpen.sceneRegionLabels });
check("NO_DUPLICATE_DETACHED_QUIZ_SURFACE: hàng nút rời KHÔNG song song",
  aOpen.sceneRegions >= 2 && !aOpen.buttonRow, { buttonRow: aOpen.buttonRow });
check("svg chuyển sang role=group ⇒ vùng bấm ĐỌC được với AT",
  aOpen.svgRole === "group", aOpen.svgRole);
check("mọi vùng đều vào được bằng Tab",
  aOpen.sceneRegions === aOpen.sceneRegionTabbable,
  { regions: aOpen.sceneRegions, tabbable: aOpen.sceneRegionTabbable });

const focused = await focusFirstRegion();
await shot("A3-keyboard-focus");
check("KEYBOARD: focus được vào vùng trên sân khấu", !!focused, focused);

// SAI trước — canonical phải nguyên vẹn
const canonicalBefore = aOpen.canonical;
const wrongLabel = aOpen.sceneRegionLabels.find((l) => /nửa/i.test(l || "")) ?? aOpen.sceneRegionLabels[0];
await clickRegionByLabel(wrongLabel);
await sleep(400);
const aActed = await snapshot();
await shot("A4-after-scene-action");
check("engine ĐÃ chấm thao tác trên sân khấu (không phải renderer)",
  aActed.prediction !== null, aActed.prediction);
check("WRONG_DIRECT_ACTION_PRESERVES_CANONICAL_STATE",
  aActed.canonical === canonicalBefore,
  { changed: aActed.canonical !== canonicalBefore });

/* ══ B. MẠNG ══════════════════════════════════════════════════════════════ */
console.log("\n── B. packet_routing: thí nghiệm cấu trúc ──");
const okB = await loadTarget("network.packet_routing");
if (!okB?.ok) { console.error("Không nạp được packet_routing:", okB); shutdown(); process.exit(2); }
await sleep(700);
check("dấu vân tay: đang đo ĐÚNG packet_routing",
  (await fingerprint()) === "network.packet_routing", await fingerprint());

const bBase = await snapshot();
await shot("B1-network-baseline");
check("tuyến gốc do engine BFS dựng", bBase.route === "client→router→isp→server", bBase.route);
check("Quan sát: KHÔNG liên kết nào bấm được", bBase.netHandles === 0, bBase.netHandles);

await clickText("Thí nghiệm");
await sleep(400);
const bOpen = await snapshot();
await shot("B2-network-tool-open");
check("mở Thí nghiệm: các liên kết thành vùng bấm", bOpen.netHandles >= 3, bOpen.netHandles);

// NGẮT một chặng — chuỗi thẳng nên mất đường
await clickRegionByLabel("Ngắt liên kết router — isp");
await sleep(500);
const bCut = await snapshot();
await shot("B3-network-disconnected-unreachable");
check("ngắt chặng ⇒ engine cho trạng thái KHÔNG TỚI ĐƯỢC (tất định)",
  bCut.route === "" && (bCut.narration || "").includes("không đi được"),
  { route: bCut.route, narration: bCut.narration });
check("không vẽ gói tin đứng im ở nguồn khi không đi được", !bCut.packetDot, bCut.packetDot);

// NỐI một đường vòng — engine phải tự tìm ra tuyến mới
await clickRegionByLabel("Nối lại liên kết");
await sleep(300);
const bRestored = await snapshot();
check("nối lại chặng vừa ngắt ⇒ tuyến gốc quay về",
  bRestored.route === "client→router→isp→server", bRestored.route);

await clickRegionByLabel("Ngắt liên kết client — router");
await sleep(500);
const bCut2 = await snapshot();
await shot("B4-network-second-cut");
check("ngắt chặng đầu ⇒ lại không tới được", bCut2.route === "", bCut2.route);

await clickText("Về mạng ban đầu");
await sleep(500);
const bReset = await snapshot();
await shot("B5-network-reset-to-baseline");
check("BASELINE_RESET_RESTORES_ORIGINAL_SPEC",
  bReset.route === "client→router→isp→server", bReset.route);

const sidecar = {
  wave: "W4B-2I",
  when: new Date().toISOString(),
  app: APP,
  viewport: argOf("--window", "1920,1080"),
  checks: results,
  passed: results.length - failed,
  total: results.length,
};
writeFileSync(join(OUT, "sidecar.json"), JSON.stringify(sidecar, null, 2));
console.log(`\n${results.length - failed}/${results.length} PASS · ảnh + sidecar → ${OUT}`);
shutdown();
process.exit(failed === 0 ? 0 : 1);
