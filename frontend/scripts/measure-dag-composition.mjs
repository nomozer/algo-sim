/**
 * measure-dag-composition.mjs — ĐO KHOẢNG TRỐNG CHẾT của `logic.boolean_dag`.
 *
 * Khiếu nại: sơ đồ dồn sang trái, nửa phải sân khấu bỏ không. Trước khi sửa bố
 * cục phải ĐO, vì cùng một hình có thể "trông lệch" chỉ do thẻ rộng ra ở màn
 * lớn — và bản vá theo cảm giác đã hỏng hai lần ở đúng file này (một lần khoá
 * sơ đồ ở 432px, một lần phóng viewBox thành áp phích).
 *
 * Đo ở bốn bề rộng: hộp sân khấu, hộp SVG, phần thừa bên phải, và mép trái của
 * những thứ lẽ ra men theo cùng một đường rail dọc.
 *
 * ⚠️ Bẫy hai-instance store: URL module lấy TỪ TRANG (xem CODE_INDEX).
 */
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
/* Neo theo CHÍNH FILE NÀY, không theo cwd: chạy từ `frontend/scripts/` với
   đường dẫn tương đối cwd đã đẻ ra một cây `frontend/docs/` lạc. */
const OUT = resolve(argOf("--out",
  new URL("../../docs/evaluation/m17/w4b4d-composition/dag.json", import.meta.url).pathname.replace(/^\//, "")));
mkdirSync(dirname(OUT), { recursive: true });
const VIEWPORTS = [[1920, 1080], [1536, 864], [1366, 768], [768, 900]];
const TARGET = argOf("--target", "logic.boolean_dag");

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const RESOLVE = `(()=>{const pick=(s)=>{const h=performance.getEntriesByType('resource').map(e=>e.name).filter(n=>n.includes(s));
 return h.length?h[h.length-1]:new URL(s,location.origin).href;};
 return JSON.stringify({store:pick('/src/state/store.ts'),catalog:pick('/src/data/offline-catalog.ts'),
 registry:pick('/src/simulations/registry.ts'),sims:pick('/src/simulations/index.ts')});})()`;

const rows = [];
for (const [w, h] of VIEWPORTS) {
  const cdp = 9100 + Math.floor(Math.random() * 700);
  const profile = mkdtempSync(join(tmpdir(), "dagcomp-"));
  const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", `--remote-debugging-port=${cdp}`,
    `--user-data-dir=${profile}`, `--window-size=${w},${h}`, "--hide-scrollbars", "about:blank"], { stdio: "ignore" });
  let url;
  for (let i = 0; i < 40 && !url; i++) {
    try { const l = await (await fetch(`http://127.0.0.1:${cdp}/json/list`)).json();
      url = l.find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch { /* chưa lên */ }
    if (!url) await sleep(250);
  }
  const ws = new WebSocket(url); await new Promise((r) => (ws.onopen = r));
  let id = 0; const pend = new Map();
  ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } };
  const send = (m, p = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  const ev = async (x) => { const r = await send("Runtime.evaluate", { expression: x, awaitPromise: true, returnByValue: true });
    if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails.exception));
    return r.result?.result?.value; };
  const evj = async (x) => { let last; for (let i = 0; i < 4; i++) {
      try { const v = await ev(x); if (typeof v === "string") return JSON.parse(v); } catch (e) { last = e; }
      await sleep(900); } throw last ?? new Error("evaluate trả undefined"); };

  await send("Page.enable"); await send("Runtime.enable");
  await send("Page.navigate", { url: "http://localhost:3000" });
  await sleep(3200);
  const u = await evj(RESOLVE);
  await ev(`(async()=>{${Object.values(u).map((x) => `await import(${JSON.stringify(x)});`).join("")}return 1})()`);

  await evj(`(async()=>{
    const s=await import(${JSON.stringify(u.store)});const c=await import(${JSON.stringify(u.catalog)});
    const rg=await import(${JSON.stringify(u.sims)});const reg=await import(${JSON.stringify(u.registry)});
    if(reg.listSimulations().length===0) rg.registerAllSimulations();
    s.useAppStore.getState().reset();
    const e=c.offlineCatalog().find(x=>x.simId===${JSON.stringify(TARGET)});
    s.useAppStore.getState().loadEnvelope(e.envelope);
    return JSON.stringify({ok:true});
  })()`);
  await sleep(1200);

  /* DẤU VÂN TAY TRANG: nếu không thấy sân khấu của đúng target thì thoát != 0,
     chứ không báo "0 khoảng trống" cho một trang trống. */
  const m = await evj(`(()=>{
    const box=(el)=>{if(!el)return null;const r=el.getBoundingClientRect();
      return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
    const stage=document.querySelector('.sim-stage');
    const group=document.querySelector('.dag-stage');
    const svg=document.querySelector('.sim-stage svg[role="img"]');
    const aff=document.querySelector('.stage-affordance');
    const leg=document.querySelector('.dag-legend');
    const det=document.querySelector('details.gate-detail');
    const nodes=[...document.querySelectorAll('.sim-stage svg rect')].map(r=>{const b=r.getBoundingClientRect();
      return {x:Math.round(b.x),w:Math.round(b.width)};}).filter(n=>n.w>40);
    return JSON.stringify({stage:box(stage),group:box(group),svg:box(svg),aff:box(aff),leg:box(leg),det:box(det),
      inkRight: nodes.length?Math.max(...nodes.map(n=>n.x+n.w)):null});
  })()`);
  if (!m.stage || !m.svg) { console.error(`✗ ${w}: không thấy sân khấu DAG — trang sai?`); chrome.kill(); process.exit(2); }

  /* HAI PHÉP ĐO KHÁC NHAU, đừng lẫn:
     - `fillPct` đo MỰC (rect trong SVG) so với thẻ — nói sơ đồ to hay nhỏ;
     - `gutter` đo CỤM nội dung so với thẻ — nói hình có bị dồn về một bên không.
     Khiếu nại gốc là "dồn sang trái", tức là phép đo thứ hai; một bản vá chỉ
     kéo `fillPct` lên mà để lệch gutter thì vẫn hỏng đúng chỗ bị kêu. */
  const g = m.group ?? m.svg;
  const gutterLeft = g.x - m.stage.x;
  const gutterRight = m.stage.x + m.stage.w - (g.x + g.w);
  const skew = Math.abs(gutterLeft - gutterRight);
  const deadRight = m.stage.x + m.stage.w - (m.inkRight ?? m.svg.x + m.svg.w);
  const fill = +(((m.inkRight - m.stage.x) / m.stage.w) * 100).toFixed(1);
  rows.push({ viewport: `${w}x${h}`, stage: m.stage, group: m.group, svg: m.svg, inkRight: m.inkRight,
    deadRight, fillPct: fill, gutterLeft, gutterRight, skew,
    leftEdges: { stage: m.stage.x, svg: m.svg.x, affordance: m.aff?.x ?? null, legend: m.leg?.x ?? null, details: m.det?.x ?? null } });
  console.log(`${String(w).padStart(4)} · thẻ ${String(m.stage.w).padStart(4)}px · cụm ${String(g.w).padStart(4)}px`
    + ` · lề trái ${String(gutterLeft).padStart(4)} / phải ${String(gutterRight).padStart(4)} · LỆCH ${String(skew).padStart(4)}px · mực lấp ${fill}%`);
  chrome.kill();
}

writeFileSync(OUT, JSON.stringify({ when: new Date().toISOString(), target: TARGET, rows }, null, 2));
console.log(`\n→ ${OUT}`);
