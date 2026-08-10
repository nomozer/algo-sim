/**
 * measure-composition.mjs — W4B-2T §4: ĐO bố cục mô phỏng, không cảm nhận.
 *
 * Với mỗi target chạy được offline, đo trong Chrome thật:
 *   - hộp bao SÂN KHẤU (`.sim-stage`) và hộp bao NỘI DUNG CÓ NGHĨA bên trong
 *   - mức dùng bề ngang / bề dọc (nội dung / sân khấu)
 *   - số DẢI THÔNG TIN quanh mô phỏng (chú giải · trạng thái · thuyết minh · kết quả · teaser)
 *   - TRÙNG NGHĨA ở trạng thái cuối (kết quả và thuyết minh nói cùng một câu)
 *   - khoảng cách từ nhãn trạng thái tới đối tượng nó mô tả (nếu đo được)
 *
 * ⚠️ Tỉ lệ dùng KHÔNG phải điểm chất lượng. Cây cần khoảng thở, bit gom cụm là
 * đúng. Con số ở đây là DỮ KIỆN để phân loại, không phải mục tiêu tối ưu.
 *
 * Chạy:  npx vite --port 3000 --strictPort   (cửa sổ khác)
 *        node scripts/measure-composition.mjs [--out <file.json>] [--window W,H]
 */

import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const PORT = argOf("--port", "3000");
const APP = `http://localhost:${PORT}`;
const OUT = resolve(argOf("--out", "../docs/evaluation/m17/w4b2t-composition/measure.json"));
const SHOTS = argOf("--shots", null);
mkdirSync(dirname(OUT), { recursive: true });
if (SHOTS) mkdirSync(resolve(SHOTS), { recursive: true });

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

const CDP_PORT = 9000 + Math.floor(Math.random() * 900);
const profile = mkdtempSync(join(tmpdir(), "algosim-w4b2t-"));
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
let id = 0; const pend = new Map();
ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } };
const send = (method, params = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const once = async (expr) => {
  const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.error) { const e = new Error(r.error.message); e.cdp = true; throw e; }
  if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails.exception ?? r.result.exceptionDetails));
  return r.result?.result?.value;
};
const evaluate = async (expr) => {
  let last;
  for (let i = 0; i < 6; i++) {
    try { return await once(expr); } catch (e) { if (!e.cdp) throw e; last = e; await sleep(1200); }
  }
  throw last;
};
const warmup = async () => {
  for (let i = 0; i < 8; i++) {
    try {
      if (await once(`(async()=>{await import('/src/data/offline-catalog.ts');await import('/src/state/store.ts');await import('/src/simulations/index.ts');await import('/src/simulations/registry.ts');return true})()`)) return true;
    } catch { /* Vite reload */ }
    await sleep(1500);
  }
  return false;
};
const shot = async (name) => {
  if (!SHOTS) return;
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(resolve(SHOTS), `${name}.png`), Buffer.from(r.result.data, "base64"));
};

const load = (simId) => evaluate(`(async()=>{
  const c=await import('/src/data/offline-catalog.ts');
  const s=await import('/src/state/store.ts');
  const r=await import('/src/simulations/index.ts');
  const reg=await import('/src/simulations/registry.ts');
  if(reg.listSimulations().length===0) r.registerAllSimulations();
  s.useAppStore.getState().reset();
  const list=c.offlineCatalog();
  const i=list.findIndex(x=>x.simId===${JSON.stringify(simId)});
  if(i<0) return {ok:false};
  s.useAppStore.getState().loadEnvelope(list[i].envelope);
  return {ok:!!s.useAppStore.getState().active};
})()`);

/**
 * HỘP BAO NỘI DUNG CÓ NGHĨA: hợp của các hộp bao con TRỰC TIẾP mang nội dung
 * (svg/table/div có kích thước thật) bên trong `.sim-stage`. Không dùng chính
 * `.sim-stage` vì nó là khung chứa — đo nó là đo cái hộp, không phải cái ruột.
 */
const measure = () => evaluate(`(async()=>{
  const s=await import('/src/state/store.ts');
  const reg=await import('/src/simulations/registry.ts');
  const st=s.useAppStore.getState(); const a=st.active;
  if(!a) return {active:false};
  const mod=reg.getSimulation(a.moduleId);
  const card=document.querySelector('.workspace-card');
  const stage=document.querySelector('.sim-stage');
  const R=(el)=>{const b=el.getBoundingClientRect();return{x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)};};
  // nội dung có nghĩa = mọi svg/table trong sân khấu (hoặc trong card nếu không có .sim-stage)
  const host = stage || card;
  const nodes=[...host.querySelectorAll('svg,table')];
  let box=null;
  for(const n of nodes){const b=n.getBoundingClientRect(); if(b.width<4||b.height<4) continue;
    box = box ? {l:Math.min(box.l,b.left),t:Math.min(box.t,b.top),r:Math.max(box.r,b.right),b:Math.max(box.b,b.bottom)}
              : {l:b.left,t:b.top,r:b.right,b:b.bottom};}
  const content = box ? {x:Math.round(box.l),y:Math.round(box.t),w:Math.round(box.r-box.l),h:Math.round(box.b-box.t)} : null;
  const hostBox=R(host);
  // DẢI THÔNG TIN quanh mô phỏng
  const band=(sel)=>document.querySelectorAll(sel).length;
  const bands={
    legend:band('.stage-legend'),
    narration:band('.narration-bar'),
    decisionStrip:band('.decision-strip'),
    searchObserve:band('.search-observe'),
    result:band('.result-banner'),
    experimentTrigger:band('.experiment-trigger'),
    experimentTool:band('.experiment-tool'),
    predictInline:band('.predict-inline'),
    holdTray:band('.hold-tray'),
  };
  const txt=(sel)=>{const e=document.querySelector(sel);return e?e.textContent.trim():null;};
  return {
    active:true, target:a.moduleId,
    cardW:R(card).w,
    stage:hostBox,
    content,
    hUse: content? +(content.w/hostBox.w*100).toFixed(1) : null,
    vUse: content? +(content.h/hostBox.h*100).toFixed(1) : null,
    bandCount:Object.values(bands).reduce((n,v)=>n+v,0),
    bands,
    resultText:txt('.result-banner'),
    narrationText:txt('.narration-bar'),
    timelineTotal: mod.timeline? mod.timeline.stepCount(a.state):null,
  };
})()`);

const toEnd = () => evaluate(`(()=>{const b=[...document.querySelectorAll('button')].find(x=>(x.getAttribute('title')||'')==='Đến cuối'&&!x.disabled); if(!b) return false; b.click(); return true;})()`);

await send("Page.enable"); await send("Runtime.enable");
await send("Page.navigate", { url: APP });
await sleep(2500);
if (!(await warmup())) { console.error("Vite chưa sẵn sàng."); shutdown(); process.exit(2); }
await sleep(800);

const TARGETS = await evaluate(`(async()=>{const c=await import('/src/data/offline-catalog.ts');return [...new Set(c.offlineCatalog().map(x=>x.simId))];})()`);

const rows = [];
for (const t of TARGETS) {
  const ok = await load(t);
  if (!ok?.ok) { rows.push({ target: t, runnable: false }); continue; }
  await sleep(420);
  const ready = await measure();
  await shot(`${t.replace(/\./g, "_")}-ready`);
  let terminal = null;
  if (ready.timelineTotal && ready.timelineTotal > 1) {
    await toEnd(); await sleep(420);
    terminal = await measure();
    await shot(`${t.replace(/\./g, "_")}-terminal`);
  }
  /* TRÙNG NGHĨA CUỐI: kết quả và thuyết minh nói cùng một điều. So bằng tập từ
     chung ≥ 60% chứ không so chuỗi — hai câu diễn đạt khác nhau vẫn là trùng. */
  let dupTerminal = false;
  const end = terminal ?? ready;
  if (end.resultText && end.narrationText) {
    const w = (s) => new Set(s.toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, " ").split(/\s+/).filter((x) => x.length > 2));
    const A = w(end.resultText), B = w(end.narrationText);
    const inter = [...A].filter((x) => B.has(x)).length;
    dupTerminal = inter / Math.max(1, Math.min(A.size, B.size)) >= 0.6;
  }
  rows.push({ target: t, runnable: true, ready, terminal, dupTerminal });
  console.log(
    `${t.padEnd(34)} hUse=${String(ready.hUse).padStart(5)}% vUse=${String(ready.vUse).padStart(5)}%` +
    ` bands=${ready.bandCount}${dupTerminal ? "  DUP_TERMINAL" : ""}`,
  );
}

writeFileSync(OUT, JSON.stringify({ when: new Date().toISOString(), viewport: argOf("--window", "1920,1080"), rows }, null, 2));
console.log(`\n${rows.filter((r) => r.runnable).length}/${rows.length} target đo được → ${OUT}`);
shutdown();
