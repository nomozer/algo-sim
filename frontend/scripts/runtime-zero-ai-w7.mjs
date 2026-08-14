/**
 * runtime-zero-ai-w7.mjs — ĐẾM REQUEST THẬT, KHÔNG SUY TỪ CẤU TRÚC MÃ.
 *
 * ─── VÌ SAO CẦN ───────────────────────────────────────────────────────────
 *
 * Báo cáo W7 khoá ZERO-AI bằng một test tĩnh: "traceOpen là state component nên
 * không đụng store". Đó là LẬP LUẬN CẤU TRÚC, không phải phép đo. Nó không loại
 * trừ được một `useEffect` gọi fetch, một lượt `init()` chạy lại, hay một
 * renderer tự đi lấy dữ liệu. Muốn nói "ZERO AI" thì phải ĐẾM.
 *
 * Cách đo: chèn một bộ đếm quanh `window.fetch` NGAY TRƯỚC hành động, rồi so
 * số trước/sau. Cũng đếm số lần `module.init` chạy bằng cách bọc chính module
 * trong registry — sinh lại spec luôn đi qua đó.
 *
 * ⚠️ Bộ đếm phải TỰ CHỨNG MINH nó hoạt động: mỗi lượt chạy có một phép thử
 * dương tính (gọi fetch một lần có chủ đích) để chắc rằng "delta 0" nghĩa là
 * "không có gọi" chứ không phải "bộ đếm không gắn được".
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
  new URL("../../docs/evaluation/m20/w7-runtime.json", import.meta.url)
    .pathname.replace(/^[/]/, "")));
mkdirSync(dirname(OUT), { recursive: true });

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const cdp = 9800 + Math.floor(Math.random() * 150);
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu",
  `--remote-debugging-port=${cdp}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "zai-"))}`,
  "--window-size=1920,1080", "--hide-scrollbars", "about:blank"], { stdio: "ignore" });
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
if (!(await ev(`document.querySelectorAll('.app-main,.nav-bar').length`))) {
  console.error("Không nhận ra trang — sai route?"); process.exit(2);
}

const RESOLVE = `(()=>{const pick=(s)=>{const h=performance.getEntriesByType('resource').map(e=>e.name).filter(n=>n.includes(s));
 return h.length?h[h.length-1]:new URL(s,location.origin).href;};
 return JSON.stringify({store:pick('/src/state/store.ts'),catalog:pick('/src/data/offline-catalog.ts'),
 registry:pick('/src/simulations/registry.ts'),sims:pick('/src/simulations/index.ts')});})()`;
const u = JSON.parse(await ev(RESOLVE));
await ev(`(async()=>{${Object.values(u).map((x) => `await import(${JSON.stringify(x)});`).join("")}return 1})()`);

/** Gắn bộ đếm: fetch + số lần `init` của module đang dùng. */
const ARM = `(async()=>{
  const reg = await import(${JSON.stringify(u.registry)});
  const w = window;
  if (!w.__zai) {
    w.__zai = { fetch: 0, init: 0 };
    const orig = w.fetch.bind(w);
    w.fetch = (...a) => { w.__zai.fetch += 1; return orig(...a); };
  }
  /* Bọc init của MỌI module đã đăng ký. Sinh lại spec, khởi tạo lại config,
     hay một renderer tự gọi init đều phải đi qua đây. */
  for (const meta of reg.listSimulations()) {
    const m = reg.getSimulation(meta.id);
    if (m && !m.__zaiWrapped) {
      const orig = m.init.bind(m);
      m.init = (c) => { window.__zai.init += 1; return orig(c); };
      m.__zaiWrapped = true;
    }
  }
  return JSON.stringify(w.__zai);
})()`;

const READ = `JSON.stringify(window.__zai)`;
const load = (sim) => ev(`(async()=>{
  const s=await import(${JSON.stringify(u.store)});const c=await import(${JSON.stringify(u.catalog)});
  const rg=await import(${JSON.stringify(u.sims)});const reg=await import(${JSON.stringify(u.registry)});
  if(reg.listSimulations().length===0) rg.registerAllSimulations();
  s.useAppStore.getState().reset();
  const e=c.offlineCatalog().find(x=>x.simId===${JSON.stringify(sim)});
  if(!e) return 'không có mẫu';
  try { s.useAppStore.getState().loadEnvelope(e.envelope); } catch (err) { return 'lỗi: '+String(err); }
  return s.useAppStore.getState().active ? 'ok' : 'không ra active';})()`);

/** Bấm một nút theo CHỮ hiện trên nó — đi qua đúng đường học sinh đi. */
const click = (text) => ev(`(()=>{
  const b=[...document.querySelectorAll('button')].find(x=>(x.textContent||'').includes(${JSON.stringify(text)}));
  if(!b) return 'không thấy nút: ' + ${JSON.stringify(text)};
  b.click(); return 'ok';})()`);

const snapshot = () => ev(`(async()=>{
  const s=await import(${JSON.stringify(u.store)});
  const a=s.useAppStore.getState().active;
  return JSON.stringify({ moduleId: a && a.moduleId, config: a && a.config, state: a && a.state });})()`);

const results = [];
const say = (name, ok, detail) => {
  results.push({ scenario: name, pass: ok, ...detail });
  console.log(`  ${ok ? "✔" : "✘"} ${name}${detail?.note ? " — " + detail.note : ""}`);
};

console.log(`━━ ZERO-AI RUNTIME  HEAD ${provenance("runtime-zero-ai-w7").head.slice(0, 8)}`);

// ── 0. BỘ ĐẾM PHẢI TỰ CHỨNG MINH NÓ GẮN ĐƯỢC ────────────────────────────────
await ev(ARM);
const armBefore = JSON.parse(await ev(READ));
await ev(`fetch('/api/health').catch(()=>{})`);
await sleep(300);
const armAfter = JSON.parse(await ev(READ));
say("bộ đếm fetch thật sự đếm được (phép thử dương tính)",
  armAfter.fetch > armBefore.fetch,
  { note: `${armBefore.fetch} → ${armAfter.fetch}` });

// ── A3. MỞ/ĐÓNG DÒNG THỜI GIAN ──────────────────────────────────────────────
for (const sim of ["binary.base_conversion", "binary.character_encoding"]) {
  let ok = await load(sim);
  if (ok !== "ok") { await sleep(1200); ok = await load(sim); }
  if (ok !== "ok") { say(`${sim} — nạp được`, false, { note: String(ok) }); continue; }
  await sleep(600);
  await ev(ARM);
  const before = JSON.parse(await ev(READ));
  const snapBefore = await snapshot();

  const open1 = await click("Xem cách thực hiện");
  await sleep(400);
  const close1 = await click("Ẩn các bước");
  await sleep(400);
  const open2 = await click("Xem cách thực hiện");
  await sleep(400);

  const after = JSON.parse(await ev(READ));
  const snapAfter = await snapshot();
  const clicksOk = open1 === "ok" && close1 === "ok" && open2 === "ok";
  say(`${sim} — mở/đóng/mở dòng thời gian: ZERO fetch`,
    clicksOk && after.fetch === before.fetch,
    { note: `fetch ${before.fetch} → ${after.fetch}${clicksOk ? "" : " (bấm hỏng: " + [open1, close1, open2].join("/") + ")"}`,
      fetchDelta: after.fetch - before.fetch });
  say(`${sim} — mở/đóng KHÔNG khởi tạo lại module`,
    after.init === before.init, { note: `init ${before.init} → ${after.init}`, initDelta: after.init - before.init });
  say(`${sim} — state công cụ giữ NGUYÊN`,
    snapBefore === snapAfter, { note: snapBefore === snapAfter ? "trùng khớp" : "state đã đổi" });
}

// ── A4. TRACE PHẢI THEO THAM SỐ HIỆN TẠI ────────────────────────────────────
{
  await load("binary.base_conversion"); await sleep(600);
  await ev(ARM);
  const before = JSON.parse(await ev(READ));
  const setParam = (name, value) => ev(`(async()=>{
    const s=await import(${JSON.stringify(u.store)});
    s.useAppStore.getState().dispatch({type:'set_param',name:${JSON.stringify(name)},value:${JSON.stringify(value)}});
    return 'ok';})()`);
  await setParam("inputValue", "26");
  await setParam("targetBase", 16);
  await sleep(400);
  await click("Xem cách thực hiện");
  await sleep(500);
  const dom = await ev(`document.querySelector('.workspace-card').innerText.replace(/\\s+/g,' ')`);
  const after = JSON.parse(await ev(READ));
  const oracle = (26).toString(16).toUpperCase();
  say("base_conversion — trace theo tham số MỚI (26 → cơ số 16)",
    typeof dom === "string" && dom.includes(oracle) && dom.includes("16"),
    { note: `mong đợi "${oracle}" trong DOM` });
  say("base_conversion — KHÔNG còn dấu vết 13/cơ số 2",
    typeof dom === "string" && !/1101/.test(dom), { note: "không thấy 1101" });
  /* LỖ NÀY DO TIÊM LỖI TÌM RA (§A1 #8).
     Hai khẳng định trên chỉ soi BẢNG CÔNG CỤ, mà bảng ấy tính lại tươi từ
     config nên nó đúng kể cả khi `steps` giữ nguyên bộ cũ. Phép tiêm "giữ
     state.steps sau khi đổi tham số" vì thế đi qua sạch 22/22.
     Phải soi chính DÒNG THỜI GIAN: sau khi đổi sang 26 → cơ số 16, bảng chia
     phải nói "26 : 16", tuyệt đối không còn "13 : 2". */
  const link = await ev(`(async()=>{
    const s=await import(${JSON.stringify(u.store)});
    const st=s.useAppStore.getState().active.state;
    const div=(st.steps||[]).find(x=>x.kind==='divide');
    const wt=(st.steps||[]).find(x=>x.kind==='weight');
    return JSON.stringify({ decimal: st.decimalValue, targetBase: st.config.targetBase,
      sourceBase: st.config.sourceBase, firstDivideValue: div?div.value:null,
      firstDivideBase: div?div.base:null, firstWeightBase: wt?wt.weight:null,
      count: (st.steps||[]).length });})()`);
  const L = typeof link === "string" ? JSON.parse(link) : {};
  /* Nối DÒNG THỜI GIAN với GIÁ TRỊ HIỆN TẠI, không so với một hằng số.
     Bản trước tìm dấu vết "cơ số 2" trong bước — nhưng mẫu offline vốn đã là
     cơ số 16, nên phép so ấy không bao giờ kích hoạt và phép tiêm "giữ
     state.steps" đi qua sạch. Ràng buộc đúng: phép chia ĐẦU TIÊN phải bắt đầu
     từ chính giá trị thập phân hiện tại và chia cho chính cơ số đích hiện tại. */
  const linked = L.firstDivideValue === null
    ? L.firstWeightBase !== null
    : (L.firstDivideValue === L.decimal && L.firstDivideBase === L.targetBase);
  say("base_conversion — DÒNG THỜI GIAN nối với tham số hiện tại",
    linked, { note: `decimal ${L.decimal}, bước chia đầu ${L.firstDivideValue} : ${L.firstDivideBase}, đích ${L.targetBase}` });
  say("base_conversion — đổi tham số + mở trace: ZERO fetch",
    after.fetch === before.fetch, { note: `fetch ${before.fetch} → ${after.fetch}` });
}
{
  await load("binary.character_encoding"); await sleep(600);
  await ev(ARM);
  const before = JSON.parse(await ev(READ));
  await ev(`(async()=>{
    const s=await import(${JSON.stringify(u.store)});
    s.useAppStore.getState().dispatch({type:'set_param',name:'text',value:'Bin'});
    return 'ok';})()`);
  await sleep(400);
  await click("Xem cách thực hiện");
  await sleep(500);
  const dom = await ev(`document.querySelector('.workspace-card').innerText.replace(/\\s+/g,' ')`);
  const after = JSON.parse(await ev(READ));
  const binB = "B".codePointAt(0).toString(2);
  const binT = "T".codePointAt(0).toString(2);
  say("character_encoding — bảng theo chuỗi MỚI (Bin)",
    typeof dom === "string" && dom.includes(binB), { note: `mong đợi ${binB}` });
  say("character_encoding — KHÔNG còn hàng của Tin",
    typeof dom === "string" && !dom.includes(binT), { note: `không thấy ${binT}` });
  say("character_encoding — đổi đầu vào + mở trace: ZERO fetch",
    after.fetch === before.fetch, { note: `fetch ${before.fetch} → ${after.fetch}` });
}

// ── A5. RESET ───────────────────────────────────────────────────────────────
for (const [sim, param, value] of [
  ["algorithm.binary_search", null, null],
  ["binary.base_conversion", "targetBase", 16],
  ["web.style_model", "r", 255],
]) {
  let ok = await load(sim);
  if (ok !== "ok") { await sleep(1200); ok = await load(sim); }
  if (ok !== "ok") { say(`${sim} — nạp được`, false, { note: String(ok) }); continue; }
  await sleep(600);
  const initial = await snapshot();
  if (param) {
    await ev(`(async()=>{const s=await import(${JSON.stringify(u.store)});
      s.useAppStore.getState().dispatch({type:'set_param',name:${JSON.stringify(param)},value:${JSON.stringify(value)}});
      return 'ok';})()`);
  } else {
    await ev(`(async()=>{const s=await import(${JSON.stringify(u.store)});
      s.useAppStore.getState().nextStep(); return 'ok';})()`);
  }
  await sleep(300);
  await ev(ARM);
  const before = JSON.parse(await ev(READ));
  const moduleBefore = JSON.parse(await snapshot()).moduleId;
  const clicked = await click("Đặt lại");
  await sleep(500);
  const after = JSON.parse(await ev(READ));
  const restored = await snapshot();
  const moduleAfter = JSON.parse(restored).moduleId;
  say(`${sim} — Đặt lại: ZERO fetch`,
    clicked === "ok" && after.fetch === before.fetch,
    { note: `fetch ${before.fetch} → ${after.fetch}`, fetchDelta: after.fetch - before.fetch });
  say(`${sim} — Đặt lại KHÔNG đổi target/module`,
    moduleBefore === moduleAfter, { note: `${moduleBefore} → ${moduleAfter}` });
  say(`${sim} — Đặt lại trả về trạng thái ban đầu đã khai`,
    restored === initial, { note: restored === initial ? "trùng khớp" : "khác trạng thái ban đầu" });
}

const failed = results.filter((r) => !r.pass);
console.log(`\n  ${results.length - failed.length}/${results.length} kịch bản ĐẠT`);
if (failed.length) for (const f of failed) console.log(`   ✘ ${f.scenario} — ${f.note ?? ""}`);

writeFileSync(OUT, JSON.stringify({
  ...provenance("runtime-zero-ai-w7"),
  question: "Mở/đóng dòng thời gian và Đặt lại có gây gọi AI/khởi tạo lại không? — ĐẾM, không suy từ mã.",
  results,
}, null, 2), "utf-8");
console.log(`\n→ ${OUT}`);
ws.close(); chrome.kill();
process.exit(failed.length ? 1 : 0);
