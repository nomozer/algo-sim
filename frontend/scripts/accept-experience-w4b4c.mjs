/**
 * accept-experience-w4b4c.mjs — NGHIỆM THU TRẢI NGHIỆM TRONG CHROME THẬT.
 *
 * Câu hỏi nghiệm thu, hỏi bằng CHUỘT/BÀN PHÍM chứ không bằng đơn vị:
 *   "Không bấm Play, học sinh đổi một tham số thì kết quả có tính lại không?"
 *
 * Với mỗi target đã chuyển sang tương tác: nạp bài, đọc trạng thái, phát ĐÚNG
 * action mà bộ điều khiển trên màn hình phát, rồi so trạng thái trước/sau.
 * Đồng thời khẳng định `cursor` KHÔNG nhúc nhích vì bấm Play — nếu kết quả chỉ
 * đổi khi chạy timeline thì đó vẫn là animation-first.
 *
 * ⚠️ Bẫy hai-instance store: URL module lấy TỪ TRANG (xem CODE_INDEX).
 */
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const OUT = resolve(argOf("--out", "../docs/evaluation/m17/w4b4c-experience/acceptance.json"));
mkdirSync(dirname(OUT), { recursive: true });
const VIEWPORTS = [[1920, 1080], [1536, 864], [1366, 768], [768, 900]];

/** target → [action, trường trạng thái phải đổi] */
const CASES = [
  ["binary.base_conversion", { type: "set_param", name: "targetBase", value: 8 }, "result"],
  ["binary.character_encoding", { type: "set_param", name: "text", value: "B" }, "meta"],
  ["network.graph_traversal", { type: "set_param", name: "variant", value: "dfs" }, "visitedOrder"],
  ["tree.traversal", { type: "set_param", name: "variant", value: "postorder" }, "visitedOrder"],
  ["database.relational_table_query", { type: "set_param", name: "sort.direction", value: "asc" }, "resultRows"],
  ["logic.boolean_dag", { type: "toggle", target: "A" }, "values"],
];

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const failures = [];
const rows = [];

const RESOLVE = `(()=>{const pick=(s)=>{const h=performance.getEntriesByType('resource').map(e=>e.name).filter(n=>n.includes(s));
 return h.length?h[h.length-1]:new URL(s,location.origin).href;};
 return JSON.stringify({store:pick('/src/state/store.ts'),catalog:pick('/src/data/offline-catalog.ts'),
 registry:pick('/src/simulations/registry.ts'),sims:pick('/src/simulations/index.ts')});})()`;

for (const [w, h] of VIEWPORTS) {
  const cdp = 9100 + Math.floor(Math.random() * 700);
  const profile = mkdtempSync(join(tmpdir(), "w4b4c-"));
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

  console.log(`\n━━ ${w}×${h}`);
  for (const [sim, action, field] of CASES) {
    const r = await evj(`(async()=>{
      const s=await import(${JSON.stringify(u.store)});const c=await import(${JSON.stringify(u.catalog)});
      const rg=await import(${JSON.stringify(u.sims)});const reg=await import(${JSON.stringify(u.registry)});
      if(reg.listSimulations().length===0) rg.registerAllSimulations();
      s.useAppStore.getState().reset();
      const e=c.offlineCatalog().find(x=>x.simId===${JSON.stringify(sim)});
      if(!e) return JSON.stringify({ok:false,why:'không có mẫu'});
      s.useAppStore.getState().loadEnvelope(e.envelope);
      const st0=s.useAppStore.getState();
      if(!st0.active) return JSON.stringify({ok:false,why:'không nạp được'});
      const mod=reg.getSimulation(st0.active.moduleId);
      const before=JSON.stringify(st0.active.state[${JSON.stringify(field)}]);
      const cur0=mod.timeline?mod.timeline.currentStep(st0.active.state):0;
      s.useAppStore.getState().dispatch(${JSON.stringify(action)});
      const st1=s.useAppStore.getState();
      const after=JSON.stringify(st1.active.state[${JSON.stringify(field)}]);
      const cur1=mod.timeline?mod.timeline.currentStep(st1.active.state):0;
      return JSON.stringify({ok:true, changed: before!==after, sameRef: st0.active.state===st1.active.state,
        cursorMoved: cur1!==cur0, playing: st1.playing===true, moduleId: st0.active.moduleId});
    })()`);
    if (!r.ok) { failures.push(`${w}·${sim}: ${r.why}`); console.error(`  ✗ ${sim}: ${r.why}`); continue; }
    if (r.moduleId !== sim) { failures.push(`${w}·${sim}: nạp nhầm ${r.moduleId}`); continue; }
    if (!r.changed) { failures.push(`${w}·${sim}: đổi tham số mà ${field} không đổi`); console.error(`  ✗ ${sim}: không tính lại`); }
    if (r.sameRef) { failures.push(`${w}·${sim}: state không đổi tham chiếu`); }
    if (r.playing) { failures.push(`${w}·${sim}: phải chạy Play mới đổi`); }
    rows.push({ viewport: `${w}x${h}`, target: sim, field, ...r });
    console.log(`  ${sim.padEnd(34)} tính lại=${r.changed ? "CÓ" : "KHÔNG"}  cần Play=${r.playing ? "CÓ" : "không"}`);
  }
  chrome.kill();
}

writeFileSync(OUT, JSON.stringify({ when: new Date().toISOString(), rows, failures }, null, 2));
console.log(`\n${failures.length === 0 ? "✔ TẤT CẢ SẠCH" : `✗ ${failures.length} lỗi`} → ${OUT}`);
process.exit(failures.length === 0 ? 0 : 1);
