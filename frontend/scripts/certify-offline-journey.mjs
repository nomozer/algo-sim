/**
 * certify-offline-journey.mjs — HÀNH TRÌNH NGƯỜI DÙNG THẬT, không khoá API.
 *
 * ─── KHÁC GÌ `certify-journey-integration.mjs` ────────────────────────────
 *
 * File kia nạp envelope thẳng vào store để cô lập từng tầng. File này đi
 * **đúng đường người dùng đi**: trang chủ → bấm thẻ bài mẫu → xưởng 3D →
 * thao tác → quay ra → mở bài thứ hai. Nó bắt được những thứ chỉ hỏng khi có
 * điều hướng thật — ví dụ chip “Menu” bấm được nhưng không mở được gì, vì cột
 * điều hướng chỉ mount khi đã đăng nhập còn xưởng thì không biết điều đó.
 *
 * Catalog bài mẫu chạy hoàn toàn phía client (`src/data/offline-catalog.ts`),
 * nên toàn bộ lượt này **0 API call, 0 backend** — chạy được khi chỉ có
 * `npm run dev`.
 */
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const REPO = fileURLToPath(new URL("../..", import.meta.url));
const OUT = join(REPO, "docs/evaluation/integration");
mkdirSync(OUT, { recursive: true });
const VP = { w: 1600, h: 900 };
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const env = (d, id) => JSON.parse(readFileSync(
  join(REPO, `docs/evaluation/geometry/${d}/spot-envelopes.json`), "utf-8"))
  .cases.find((x) => x.id === id).envelope;

const dir = mkdtempSync(join(tmpdir(), "offl-"));
const proc = spawn(CHROME, ["--headless=new", "--remote-debugging-port=9897",
  `--user-data-dir=${dir}`, `--window-size=${VP.w},${VP.h}`, "--hide-scrollbars",
  "--force-device-scale-factor=2", "--use-gl=angle", "--use-angle=swiftshader",
  "--enable-unsafe-swiftshader", "about:blank"], { stdio: "ignore" });
let wsUrl;
for (let i = 0; i < 80 && !wsUrl; i++) {
  try { wsUrl = (await (await fetch("http://127.0.0.1:9897/json/list")).json())
    .find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch {}
  if (!wsUrl) await sleep(300);
}
const ws = new WebSocket(wsUrl); await new Promise((r) => (ws.onopen = r));
let id = 0; const pend = new Map(); const errs = [];
ws.onmessage = (e) => { const m = JSON.parse(e.data);
  if (m.method === "Runtime.consoleAPICalled" && m.params?.type === "error")
    errs.push((m.params.args ?? []).map((a) => a.value).join(" "));
  if (m.method === "Runtime.exceptionThrown")
    errs.push(m.params?.exceptionDetails?.text ?? "exception");
  if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } };
const send = (M, p = {}) => new Promise((res) => { const i = ++id; pend.set(i, res);
  ws.send(JSON.stringify({ id: i, method: M, params: p })); });
const ev = async (x) => (await send("Runtime.evaluate",
  { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
const evj = async (x) => { const v = await ev(x); return v ? JSON.parse(v) : null; };
await send("Page.enable"); await send("Runtime.enable");
await send("Emulation.setDeviceMetricsOverride",
  { width: VP.w, height: VP.h, deviceScaleFactor: 2, mobile: false });

const KQ = []; const ghi = (o) => { KQ.push(o); console.log(JSON.stringify(o)); };

async function moCa(d, id_, buoc) {
  await send("Page.navigate", { url: "http://localhost:3000" });
  await sleep(3200);
  const van = await evj(`JSON.stringify({root:!!document.querySelector('#root')})`);
  if (!van?.root) throw new Error("dấu vân tay trang hỏng");
  await ev(`(async()=>{const m=await import('/src/state/store.ts');
    m.useAppStore.getState().loadEnvelope(${JSON.stringify(env(d, id_))}); return 'ok';})()`);
  await sleep(4200);
  await ev(`(()=>{const i=document.querySelector('.geo3d-scrub input[type=range]');
    const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
    s.call(i, ${buoc === "cuoi" ? "i.max" : JSON.stringify(String(buoc))});
    i.dispatchEvent(new Event('input',{bubbles:true})); return 'ok';})()`);
  await sleep(1300);
}
const bam = (sel, chu) => ev(`(()=>{const b=[...document.querySelectorAll(${JSON.stringify(sel)})]
  .find(x=>x.textContent.includes(${JSON.stringify(chu)}));
  if(!b) return 'KHONG_THAY'; if(b.disabled) return 'BI_KHOA'; b.click(); return 'ok';})()`);
const datBuoc = (k) => ev(`(()=>{const i=document.querySelector('.geo3d-scrub input[type=range]');
  const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
  s.call(i,String(${k})); i.dispatchEvent(new Event('input',{bubbles:true})); return 'ok';})()`);
async function xoay(dx, dy) {
  const b = await evj(`(()=>{const c=document.querySelector('.geo3d-canvas canvas');
    const r=c.getBoundingClientRect(); return JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2});})()`);
  const p = { button: "left", clickCount: 1 };
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x: b.x, y: b.y, ...p });
  for (let i = 1; i <= 10; i++) { await send("Input.dispatchMouseEvent", { type: "mouseMoved",
    x: b.x + (dx*i)/10, y: b.y + (dy*i)/10, button: "left" }); await sleep(25); }
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: b.x+dx, y: b.y+dy, ...p });
  await sleep(900);
}
async function chonVat(ten) {
  await bam(".geo3d-chip", "Thành phần"); await sleep(800);
  const r = await ev(`(()=>{const n=[...document.querySelectorAll('.geo3d-tree-item .geo3d-tree-nhan')]
    .find(x=>x.textContent.trim()===${JSON.stringify(ten)});
    if(!n) return 'KHONG_THAY'; const b=n.closest('.geo3d-tree-item');
    if(b.disabled) return 'BI_KHOA'; b.click(); return 'ok';})()`);
  await sleep(600);
  await bam(".geo3d-chip", "Thành phần"); await sleep(800);
  return r;
}
async function chup(name, sel) {
  await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: 3, y: 3 });
  await sleep(600);
  let clip;
  if (sel) clip = await evj(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});
    if(!e) return null; const r=e.getBoundingClientRect();
    return JSON.stringify({x:Math.round(r.x),y:Math.round(r.y),width:Math.round(r.width),height:Math.round(r.height)});})()`);
  const r = await send("Page.captureScreenshot", clip
    ? { format: "png", clip: { ...clip, scale: 2 }, captureBeyondViewport: true }
    : { format: "png" });
  writeFileSync(join(OUT, name), Buffer.from(r.result.data, "base64"));
  return { file: name, clip };
}
const trangThai = () => evj(`JSON.stringify({
  canvas: document.querySelectorAll('.geo3d-canvas canvas').length,
  buoc: (document.querySelector('.geo3d-buoc-so')?.textContent||'').trim(),
  soiTen: (document.querySelector('.geo3d-soi-ten')?.textContent||'').trim(),
  kyThuat: (document.querySelector('.geo3d-soi-ky-thuat')?.textContent||'').trim(),
  nganMo: !!document.querySelector('.geo3d-ngan'),
})`);

const R=[]; const kt=(t,th,ok)=>{R.push({t,th,ok});console.log(`${ok?"✓":"✗"} ${t} | ${th}`);};
const T = () => evj(`JSON.stringify({
  buoc:(document.querySelector('.geo3d-buoc-so')?.textContent||'').trim(),
  canvas: document.querySelectorAll('.geo3d-canvas canvas').length,
  xuong: !!document.querySelector('.geo3d-xuong'),
  duPhong: !!document.querySelector('.geo3d-fallback'),
  soiTen:(document.querySelector('.geo3d-soi-ten')?.textContent||'').trim(),
  bung:(document.querySelector('.geo3d-noi-nut')?.textContent||'').trim(),
  scrub:Number(document.querySelector('.geo3d-scrub input')?.value ?? -1),
  readout:[...document.querySelectorAll('.geo3d-readout')].map(e=>e.textContent.trim()),
})`);

// ══ §11 · LUỒNG NGOẠI TUYẾN, ĐI BẰNG GIAO DIỆN THẬT ═════════════════════
await send("Page.navigate", { url: "http://localhost:3000" }); await sleep(3200);
const goiY = await evj(`JSON.stringify([...document.querySelectorAll('button,a')]
  .map(e=>e.textContent.trim()).filter(t=>/thiết diện|vuông góc|thể tích/i.test(t)).slice(0,4))`);
kt("§11 trang chủ có thẻ bài mẫu hình học", JSON.stringify(goiY), goiY.length > 0);

const moMau = await ev(`(()=>{const b=[...document.querySelectorAll('button,a')]
  .find(e=>/thiết diện của hình chóp/i.test(e.textContent)); if(!b) return 'KHONG_THAY';
  b.click(); return 'ok';})()`);
await sleep(4500);
let t = await T();
kt("§11 mở bài mẫu → xưởng 3D dựng được (0 khoá API)",
   `mo=${moMau} canvas=${t.canvas} xuong=${t.xuong} duPhong=${t.duPhong}`,
   moMau === "ok" && t.canvas === 1 && t.xuong === true && t.duPhong === false);
kt("§11 bắt đầu ở bước 1", t.buoc, /^Bước 1\//.test(t.buoc));

// ══ §5 · TUA BƯỚC: chữ, thanh trượt, và kết quả cùng nói một điều ═══════
await bam(".geo3d-btn", "Bước sau"); await sleep(900);
t = await T();
kt("§5 bấm Bước sau → chữ và thanh trượt cùng tiến", `${t.buoc} scrub=${t.scrub}`,
   /^Bước 2\//.test(t.buoc) && t.scrub === 1);
await datBuoc(99); await sleep(1200); t = await T();
const tong = Number((t.buoc.match(/\/(\d+)/)||[])[1] ?? -1);
kt("§5 kéo quá cuối vẫn kẹp đúng, không ra bước không tồn tại", t.buoc,
   t.buoc === `Bước ${tong}/${tong}` && t.scrub === tong - 1);

// ══ §9 · RESET VÀ ĐIỀU HƯỚNG ════════════════════════════════════════════
await chonVat("A"); await bam(".geo3d-noi-nut", "Tách khối"); await sleep(1400);
const truoc = await T();
await bam(".geo3d-noi-nut", "Xem lại toàn hình"); await sleep(1400);
t = await T();
kt("§9 Xem lại toàn hình bỏ chọn và hiện đủ vật",
   `truoc="${truoc.soiTen}" sau="${t.soiTen}"`, t.soiTen === "");
kt("§9 Xem lại toàn hình KHÔNG tự ráp khối (tách là ý người dùng)",
   `bung=${t.bung}`, t.bung === "Ráp lại");
await bam(".geo3d-noi-nut", "Ráp lại"); await sleep(1200); t = await T();
kt("§9 Ráp lại đưa về trạng thái xác định", t.bung, t.bung === "Tách khối");

// Đường VỀ trong workspace. Khi CHƯA đăng nhập không có cột điều hướng, nên
// hai lối là dấu hiệu sản phẩm (wordmark) và chip "Menu" — kiểm cả hai.
const coMenu = await ev(`(()=>{const b=[...document.querySelectorAll('button')]
  .find(e=>e.getAttribute('aria-label')==='Mở điều hướng'); if(!b) return 'KHONG_THAY';
  b.click(); return 'ok';})()`);
await sleep(1200);
const menu = await evj(`JSON.stringify({
  mo: !!document.querySelector('.app-nav-shell.is-drawer-open, .app-nav-shell'),
  muc: [...document.querySelectorAll('.app-nav-item, .app-nav-shell button, .app-nav-shell a')]
        .map(e=>e.textContent.trim().slice(0,24)).filter(Boolean).slice(0,8),
})`);
kt("§9 khách KHÔNG thấy chip Menu chết (không có cột để mở)",
   `bam=${coMenu}`, coMenu === "KHONG_THAY");

const veHome = await ev(`(()=>{const b=[...document.querySelectorAll('button')]
  .find(e=>/^AlgoSim$/.test(e.textContent.trim())); if(!b) return 'KHONG_THAY';
  b.click(); return 'ok';})()`);
await sleep(2500);
const home = await evj(`JSON.stringify({
  coO: !!document.querySelector('textarea'),
  conXuong: !!document.querySelector('.geo3d-xuong'),
})`);
kt("§9 wordmark đưa về màn nhập đề",
   `bam=${veHome} coO=${home.coO} conXuong=${home.conXuong}`,
   veHome === "ok" && home.coO === true && home.conXuong === false);

const mo2 = await ev(`(()=>{const b=[...document.querySelectorAll('button,a')]
  .find(e=>/thể tích khối chóp/i.test(e.textContent)); if(!b) return 'KHONG_THAY';
  b.click(); return 'ok';})()`);
await sleep(4500); t = await T();
kt("§4 bài thứ hai mở sạch: bước 1, không chọn, không tách",
   `mo=${mo2} ${t.buoc} chon="${t.soiTen}" bung=${t.bung}`,
   mo2 === "ok" && /^Bước 1\//.test(t.buoc) && t.soiTen === "" && t.bung === "Tách khối");

writeFileSync(join(OUT, "offline-journey.json"), JSON.stringify({ R, loiConsole: errs }, null, 2));
console.log(`
ĐẠT ${R.filter(x=>x.ok).length}/${R.length} · LOI_CONSOLE ${errs.length}`);
ws.close(); proc.kill();
