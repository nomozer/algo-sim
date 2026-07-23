/**
 * diagnose-responsive.mjs — M17-RC1 §E1 §2: BẰNG CHỨNG ROOT CAUSE.
 *
 * Đo hình học DOM THẬT ở từng viewport để trả lời: phần tử NÀO làm
 * scrollWidth > clientWidth ở mức TRANG, và min-width nào giữ cột không co.
 * Chạy TRƯỚC khi sửa (before) và LẠI sau khi sửa (after).
 *
 *   node scripts/diagnose-responsive.mjs --out ../docs/evaluation/m17/rc1/visual/before/VIS-003
 */
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const APP = `http://localhost:${argOf("--port", "3000")}`;
const OUT = resolve(argOf("--out", "../docs/evaluation/m17/rc1/visual/before/VIS-003"));
const CDP_PORT = 9337;
const VIEWPORTS = [
  { id: "desktop", width: 1440, height: 1000 },
  { id: "narrow", width: 768, height: 900 },
];
/* Route dùng CHUNG app shell — §5 bắt buộc kiểm cùng lúc. */
const ROUTES = [
  { id: "workspace", hash: "" },
  { id: "home", hash: "#/" },
  { id: "library", hash: "#/library" },
  { id: "history", hash: "#/history" },
];

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

const profile = mkdtempSync(join(tmpdir(), "algosim-e1-"));
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu",
  `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
  "--window-size=1440,1000", "--hide-scrollbars", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function connect() {
  for (let i = 0; i < 40; i++) {
    try {
      const l = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`)).json();
      const p = l.find((t) => t.type === "page");
      if (p) return p.webSocketDebuggerUrl;
    } catch { /* chưa lên */ }
    await sleep(250);
  }
  throw new Error("Chrome không mở được cổng debug.");
}
const ws = new WebSocket(await connect());
await new Promise((r) => (ws.onopen = r));
let id = 0; const pending = new Map();
ws.onmessage = (e) => { const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } };
const send = (method, params = {}) => new Promise((res) => {
  const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const evaluate = async (expr) => {
  const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails).slice(0, 400));
  return r.result?.result?.value;
};
await send("Page.enable"); await send("Runtime.enable");
mkdirSync(OUT, { recursive: true });

const PROBE = `(() => {
  const de = document.documentElement;
  const vw = de.clientWidth;
  const over = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    const cs = getComputedStyle(el);
    const mw = cs.minWidth;
    const spills = r.right > vw + 1 || r.left < -1;
    const rigid = mw && mw !== '0px' && mw !== 'auto' && parseFloat(mw) > vw;
    if (spills || rigid) {
      over.push({
        tag: el.tagName.toLowerCase(),
        cls: (el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className || '').toString().slice(0, 60),
        left: Math.round(r.left), right: Math.round(r.right), width: Math.round(r.width),
        min_width: mw, overflow_x: cs.overflowX, display: cs.display,
        grid_template: cs.gridTemplateColumns.slice(0, 80),
        reason: spills ? 'spills_past_viewport' : 'min_width_exceeds_viewport',
      });
    }
  }
  /* Phần tử học sinh PHẢI thấy — có nằm trong khung nhìn không? */
  const named = (sel, name) => {
    const el = document.querySelector(sel);
    if (!el) return { name, present: false };
    const r = el.getBoundingClientRect();
    return { name, present: true, left: Math.round(r.left), right: Math.round(r.right),
             width: Math.round(r.width), inside: r.right <= vw + 1 && r.left >= -1 };
  };
  /* BỊ TỔ TIÊN CẮT: phần tử nằm TRONG khung nhìn nhưng tràn khỏi vùng hiển
     thị của một tổ tiên có overflow ẩn/cuộn. Đây mới là dạng cắt thật đã thấy
     trong ảnh audit — kiểm "ngoài viewport" KHÔNG bắt được nó. */
  const clippedBy = (el) => {
    const r = el.getBoundingClientRect();
    for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
      const cs = getComputedStyle(p);
      if (!/hidden|clip|auto|scroll/.test(cs.overflowX)) continue;
      const pr = p.getBoundingClientRect();
      if (r.right > pr.right + 1 || r.left < pr.left - 1) {
        return { by: p.tagName.toLowerCase() + '.' +
                 ((p.className && p.className.baseVal !== undefined ? p.className.baseVal : p.className || '').toString().split(' ')[0]),
                 overflow_x: cs.overflowX,
                 spill_right: Math.round(r.right - pr.right) };
      }
    }
    return null;
  };
  const buttons = [...document.querySelectorAll('button')].map((b) => {
    const r = b.getBoundingClientRect();
    return { text: (b.textContent || '').trim().slice(0, 20),
             right: Math.round(r.right), inside: r.right <= vw + 1 && r.left >= -1,
             clipped_by_ancestor: clippedBy(b) };
  });
  const clippedContent = [...document.querySelectorAll(
      '.workspace-title, .sim-stage, .notes, .hint, svg, [class*="panel"]')]
    .map((el) => ({ sel: el.tagName.toLowerCase() + '.' +
        ((el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className || '').toString().split(' ')[0]),
        text: (el.textContent || '').trim().slice(0, 34), clip: clippedBy(el) }))
    .filter((x) => x.clip);
  return {
    viewport: { clientWidth: vw, scrollWidth: de.scrollWidth,
                page_overflow_x: de.scrollWidth > vw + 1 },
    key_elements: [named('.workspace-title', 'title'), named('.sim-stage', 'canvas'),
                   named('.workspace-card', 'workspace'), named('main', 'main')],
    controls: { total: buttons.length, clipped: buttons.filter((b) => !b.inside),
                clipped_by_ancestor: buttons.filter((b) => b.clipped_by_ancestor) },
    clipped_content: clippedContent.slice(0, 10),
    offenders: over.slice(0, 14),
  };
})()`;

const results = [];
for (const vp of VIEWPORTS) {
  await send("Emulation.setDeviceMetricsOverride",
    { width: vp.width, height: vp.height, deviceScaleFactor: 1, mobile: false });
  for (const route of ROUTES) {
    await send("Page.navigate", { url: APP + route.hash });
    await sleep(1400);
    if (route.id === "workspace") {
      await evaluate(`(async () => {
        const m = await import('/src/state/store.ts');
        m.useAppStore.getState().loadEnvelope(${JSON.stringify({
          status: "ok", simulation_id: "tree.traversal", domain: "tree", visual_mode: "2d",
          title: "Chẩn đoán bố cục", description: null, notes: null,
          config: { specVersion: "tree-1.0", variant: "preorder", rootId: "A",
                    nodes: [{ id: "A", label: "A", left: "B", right: "C" },
                            { id: "B", label: "B", left: null, right: null },
                            { id: "C", label: "C", left: null, right: null }], notes: null },
        })});
        return true; })()`);
      await sleep(700);
    }
    const probe = await evaluate(PROBE);
    const shot = await send("Page.captureScreenshot", { format: "png" });
    const png = join(OUT, `${route.id}-${vp.id}.png`);
    if (shot.result?.data) writeFileSync(png, Buffer.from(shot.result.data, "base64"));
    results.push({ route: route.id, viewport: vp.id, screenshot: png.replace(/\\/g, "/"), ...probe });
    const bad = probe.viewport.page_overflow_x || probe.controls.clipped.length
      || probe.controls.clipped_by_ancestor.length || probe.clipped_content.length
      || probe.key_elements.some((k) => k.present && !k.inside);
    console.log(`  ${route.id}/${vp.id}  scrollW ${probe.viewport.scrollWidth}/${probe.viewport.clientWidth}` +
      `  nút-bị-cắt ${probe.controls.clipped_by_ancestor.length}` +
      `  nội-dung-bị-cắt ${probe.clipped_content.length}  ${bad ? "⚠" : "ok"}`);
  }
}
writeFileSync(join(OUT, "responsive-diagnosis.json"),
  JSON.stringify({ app: APP, generated_at: new Date().toISOString(), results }, null, 2) + "\n", "utf-8");
console.log(`\n→ ${OUT}`);
ws.close(); chrome.kill();
