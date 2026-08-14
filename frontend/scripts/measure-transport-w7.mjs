/**
 * measure-transport-w7.mjs — KHAY ĐIỀU KHIỂN THUỘC VỀ AI?
 *
 * Wave 7 §1 hỏi một câu bác bỏ được:
 *
 *   Cơ chế to nhỏ khác nhau thì khay điều khiển có ĐỔI BỀ RỘNG THEO không?
 *
 * Nếu có, khay đang thuộc về KHUNG CƠ CHẾ. Học sinh đổi bài là dải điều khiển
 * co giãn theo, và không có mặt phẳng ổn định nào để tì tay vào.
 *
 * Cách đo: nạp lần lượt một cơ chế HẸP, một VỪA, một RỘNG ở cùng một bề rộng
 * cửa sổ, rồi so bề rộng khung với bề rộng khay. Cơ chế lệch nhiều mà khay lệch
 * theo ⇒ quyền sở hữu sai. Cơ chế lệch nhiều mà khay đứng yên ⇒ đúng.
 *
 * Cũng đo KHOẢNG TRỐNG CHẾT lớn nhất giữa hai cụm điều khiển liền nhau — đó là
 * khiếm khuyết "dải thưa" mà §13 cấm tái diễn.
 *
 * ⚠️ Backtick KHÔNG được xuất hiện trong biểu thức tiêm vào trang.
 */
import { spawn } from "node:child_process";
import { provenance } from "./evidence.mjs";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const OUT = resolve(argOf("--out",
  new URL("../../docs/evaluation/m20/transport-before.json", import.meta.url)
    .pathname.replace(/^[/]/, "")));
const LABEL = argOf("--label", "before");
const TARGETS = argOf("--targets",
  "logic.and_gate,algorithm.binary_search,tree.traversal,binary.base_conversion," +
  "binary.character_encoding,web.style_model").split(",");
const VIEWPORTS = argOf("--viewports", "1920").split(",").map(Number);
mkdirSync(dirname(OUT), { recursive: true });

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

const MEASURE = `(()=>{
  const card = document.querySelector('.workspace-card');
  const dock = document.querySelector('.panel-controls');
  const shell = document.querySelector('.app-layout');
  if (!card || !dock || !shell) return JSON.stringify({error:'thiếu card/dock/shell'});
  const box = (el) => { const r = el.getBoundingClientRect();
    return { x: Math.round(r.left), w: Math.round(r.width), h: Math.round(r.height) }; };

  /* HÀNG điều khiển: đếm bằng TÂM DỌC có dung sai, KHÔNG bằng mép trên.
     Bản đầu đếm theo mép trên và báo 3 hàng ở 1920 cho một dải rõ ràng một
     hàng: align-items center khiến ba cụm khác chiều cao (nút Chạy 40px so với
     chữ) có mép trên lệch nhau vài pixel dù cùng nằm trên một hàng. Đếm mép
     trên là đếm CHIỀU CAO CỤM chứ không đếm hàng. */
  const zones = [...dock.querySelectorAll('.control-zone, .player-track')]
    .filter(z => z.getBoundingClientRect().width > 2);
  const centers = zones.map(z => { const r = z.getBoundingClientRect(); return r.top + r.height / 2; });
  const tops = [];
  for (const c of centers.sort((a, b) => a - b)) {
    if (!tops.length || c - tops[tops.length - 1] > 12) tops.push(c);
  }

  /* KHOẢNG TRỐNG CHẾT: kẽ hở lớn nhất giữa hai cụm liền nhau TRÊN CÙNG MỘT
     HÀNG. Đây là khiếm khuyết "dải thưa": tốc độ bị đẩy sang mép phải và giữa
     dải là một mảng rỗng. */
  let maxGap = 0;
  for (const top of tops) {
    const row = zones.filter(z => { const r = z.getBoundingClientRect();
        return Math.abs((r.top + r.height / 2) - top) <= 12; })
      .map(z => z.getBoundingClientRect()).sort((a,b) => a.left - b.left);
    for (let i = 1; i < row.length; i++) {
      maxGap = Math.max(maxGap, Math.round(row[i].left - row[i-1].right));
    }
  }

  const has = (sel) => Boolean(dock.querySelector(sel));
  return JSON.stringify({
    mechanism: box(card),
    dock: box(dock),
    shell: box(shell),
    rows: tops.length,
    zones: zones.length,
    maxDeadGap: maxGap,
    controls: {
      play: has('.btn-play'),
      step: dock.querySelectorAll('.control-zone-primary .btn-icon').length,
      reset: [...dock.querySelectorAll('button')].some(b => /Đặt lại|đầu/.test(b.textContent||'')),
      seek: has('.player-progress'),
      speed: has('.speed-control'),
      stepCount: has('.step-indicator'),
    },
    overflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
  });
})()`;

const rows = [];
for (const vw of VIEWPORTS) {
  const cdp = 9500 + Math.floor(Math.random() * 200);
  const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu",
    `--remote-debugging-port=${cdp}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "w7-"))}`,
    `--window-size=${vw},1080`, "--hide-scrollbars", "about:blank"], { stdio: "ignore" });
  let wsUrl;
  for (let i = 0; i < 40 && !wsUrl; i++) {
    try {
      const l = await (await fetch(`http://127.0.0.1:${cdp}/json/list`)).json();
      wsUrl = l.find((t) => t.type === "page")?.webSocketDebuggerUrl;
    } catch { /* chưa lên */ }
    if (!wsUrl) await sleep(250);
  }
  const ws = new WebSocket(wsUrl);
  await new Promise((r) => (ws.onopen = r));
  let id = 0; const pend = new Map();
  ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } };
  const send = (m, p = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  const ev = async (x) => {
    const r = await send("Runtime.evaluate", { expression: x, awaitPromise: true, returnByValue: true });
    const ex = r.result?.exceptionDetails;
    if (ex) return "LỖI: " + String(ex.exception?.description ?? ex.text ?? "?").split(String.fromCharCode(10))[0];
    return r.result?.result?.value;
  };

  await send("Page.enable"); await send("Runtime.enable");
  await send("Page.navigate", { url: "http://localhost:3000" });
  await sleep(3200);
  const fingerprint = await ev(`document.querySelectorAll('.app-main,.nav-bar').length`);
  if (!fingerprint) { console.error("Không nhận ra trang — sai route?"); process.exit(2); }

  const u = JSON.parse(await ev(RESOLVE));
  await ev(`(async()=>{${Object.values(u).map((x) => `await import(${JSON.stringify(x)});`).join("")}return 1})()`);
  const load = (sim) => ev(`(async()=>{
    const s=await import(${JSON.stringify(u.store)});const c=await import(${JSON.stringify(u.catalog)});
    const rg=await import(${JSON.stringify(u.sims)});const reg=await import(${JSON.stringify(u.registry)});
    if(reg.listSimulations().length===0) rg.registerAllSimulations();
    s.useAppStore.getState().reset();
    const e=c.offlineCatalog().find(x=>x.simId===${JSON.stringify(sim)});
    if(!e) return 'không có mẫu';
    try { s.useAppStore.getState().loadEnvelope(e.envelope); } catch (err) { return 'lỗi: '+String(err); }
    return s.useAppStore.getState().active ? 'ok' : 'không ra active';})()`);

  console.log(`\n━━ ${vw}px  [${LABEL}]  HEAD ${provenance("measure-transport-w7").head.slice(0, 8)}`);
  console.log("  target                          cơ chế   khay  khay/shell  hàng  hở  tràn");
  for (const sim of TARGETS) {
    let loaded = await load(sim);
    if (loaded !== "ok") { await sleep(1200); loaded = await load(sim); }
    if (loaded !== "ok") {
      console.log(`  ${sim.padEnd(32)} ${loaded ?? "(không trả lời)"}`);
      rows.push({ viewport: vw, target: sim, error: loaded ?? "no-response" });
      continue;
    }
    await sleep(650);
    const raw = await ev(MEASURE);
    if (typeof raw !== "string") { console.log(`  ${sim.padEnd(32)} đo hỏng: ${raw}`); continue; }
    const m = JSON.parse(raw);
    if (m.error) { console.log(`  ${sim.padEnd(32)} ${m.error}`); continue; }
    const ratio = ((m.dock.w / m.shell.w) * 100).toFixed(1);
    console.log(`  ${sim.padEnd(32)}${String(m.mechanism.w).padStart(7)}${String(m.dock.w).padStart(7)}` +
      `${(ratio + "%").padStart(11)}${String(m.rows).padStart(6)}${String(m.maxDeadGap).padStart(5)}` +
      `${(m.overflowX ? "  CÓ" : "   ·")}`);
    rows.push({ viewport: vw, target: sim, ...m, dockShellRatio: Number(ratio) });
  }
  ws.close(); chrome.kill();
}

/* PHÁN QUYẾT §10 — quyền sở hữu đo bằng ĐỘ LỆCH, không bằng một con số ma.
   Cơ chế lệch nhiều mà khay lệch theo ⇒ khay đang thuộc khung cơ chế. */
for (const vw of VIEWPORTS) {
  const at = rows.filter((r) => r.viewport === vw && r.dock);
  if (at.length < 2) continue;
  const mech = at.map((r) => r.mechanism.w);
  const dock = at.map((r) => r.dock.w);
  const spread = (a) => Math.max(...a) - Math.min(...a);
  console.log(`\n  ${vw}px — độ lệch bề rộng: cơ chế ${spread(mech)}px · khay ${spread(dock)}px`);
  console.log(spread(dock) <= 24
    ? "  ✔ KHAY ĐỘC LẬP với cơ chế (lệch ≤ 24px)"
    : `  ✘ KHAY BÁM THEO CƠ CHẾ — lệch ${spread(dock)}px, quyền sở hữu sai`);
}

writeFileSync(OUT, JSON.stringify({
  ...provenance("measure-transport-w7", { label: LABEL }),
  question: "Cơ chế to nhỏ khác nhau thì khay điều khiển có đổi bề rộng theo không?",
  rows,
}, null, 2), "utf-8");
console.log(`\n→ ${OUT}`);
process.exit(0);
