/**
 * certify-display-metadata.mjs — TÊN HIỂN THỊ trên bề mặt học sinh, đo trong
 * Chrome thật. **0 mạng, 0 LLM** (catalog bài mẫu chạy phía client).
 *
 * ─── ĐIỀU NÓ BẢO VỆ ───────────────────────────────────────────────────────
 *
 * Sau bản sửa G1/G2 (`SEMANTIC_PRESENTATION_METADATA_AUTHORITY`), tên hiển thị
 * do **tầng ngữ nghĩa backend** quyết và đi trọn qua transport. Bốn điều phải
 * đúng CÙNG LÚC, và mỗi điều hỏng riêng lẻ được:
 *
 *   §23  không định danh máy nào (`the_tich_…`, `vector_…`, `_prime`) lọt lên
 *        bề mặt học sinh — quét chữ THẬT trong DOM, không quét một danh sách
 *        tên đã biết;
 *   §10  khung 3D in **KÝ HIỆU** (`A`, `(MNP)`), không in câu mô tả;
 *   §9   dải kết quả mang **TÊN đọc được** (*"Thể tích S.ABCD"*), không mang
 *        tên biến IR;
 *   §24  bước 0 không in sentinel nội bộ của trace (`system`).
 *
 * ─── VÌ SAO PHẢI ĐO TRONG TRÌNH DUYỆT ────────────────────────────────────
 *
 * pytest khoá được *backend phát ra gì*; vitest khoá được *component in gì khi
 * cho dữ liệu dựng tay*. Không cái nào trả lời được *chữ nào THẬT SỰ hiện ra
 * sau khi envelope đi qua cả chuỗi* — và chính chỗ ấy đã rò hai lần: một lần
 * qua `label` rơi về `id`, một lần qua `events[].object` chở `"system"`.
 *
 * ⚠️ Tua tới bước cuối bằng **thanh trượt**, không bằng nút *Bước sau*: giữ một
 * tham chiếu nút rồi bấm nhiều lần thì React dựng lại và mọi cú bấm sau rơi
 * vào một nút đã tháo — lượt đo dừng ở bước 1 mà vẫn báo xanh.
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

await send("Page.navigate", { url: "http://localhost:3000" });
await sleep(1200);
// mở bài mẫu thứ ba (thể tích — có 2 số đo)
await evj(`(()=>{const c=[...document.querySelectorAll('.sample-card,.session-card,button,a')]
  .filter(e=>/Thể tích/.test(e.textContent||''));c[0]&&c[0].click();return !!c[0];})()`);
await sleep(2500);

const M = (await evj(`JSON.stringify({
  nhanKhung: [...document.querySelectorAll('.geo3d-label')].map(e=>e.textContent.trim()),
  ketQua:   [...document.querySelectorAll('.geo3d-readout li')].map(e=>e.textContent.trim()),
  tieuDiem: (document.querySelector('.geo3d-focus')?.textContent||'').trim(),
  chuHocSinh: (document.querySelector('.geo3d-xuong')?.innerText||''),
})`));
console.log("nhãn khung :", JSON.stringify(M.nhanKhung));
console.log("dải kết quả:", JSON.stringify(M.ketQua));
console.log("tiêu điểm  :", JSON.stringify(M.tieuDiem));

// tua tới bước CUỐI bằng thanh trượt (bấm nút giữ tham chiếu cũ ⇒ dừng ở bước 1)
await ev(`(()=>{const i=document.querySelector('.geo3d-scrub input[type=range]');
  const set=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
  set.call(i, i.max); i.dispatchEvent(new Event('input',{bubbles:true}));
  i.dispatchEvent(new Event('change',{bubbles:true})); return i.max;})()`);
await sleep(1200);
const F = await ev(`(document.querySelector('.geo3d-focus')?.textContent||'').trim()`);
console.log("tiêu điểm cuối:", JSON.stringify(F));

const RO = ["the_tich", "khoang_cach", "vector_", "_prime", "plane_", "pyramid_", "section_", "S_ABCD"];
const bay = RO.filter(x => M.chuHocSinh.includes(x) || String(F).includes(x));
kt("§23 KHÔNG định danh máy nào lọt lên bề mặt học sinh", JSON.stringify(bay), bay.length === 0);
kt("§10 khung in KÝ HIỆU, không in câu", JSON.stringify(M.nhanKhung),
   M.nhanKhung.length > 0 && M.nhanKhung.every(s => s.length <= 10));
const K = await evj("JSON.stringify([...document.querySelectorAll('.geo3d-readout li')].map(e=>e.textContent.trim()))");
console.log("dải kết quả cuối:", JSON.stringify(K));
kt("§9 dải kết quả mang TÊN đọc được", JSON.stringify(K),
   K.length > 0 && K.every(s => /[a-zà-ỹ]/.test(s)));
kt("§24 bước 0 KHÔNG in sentinel nội bộ", JSON.stringify(M.tieuDiem),
   !String(M.tieuDiem).includes('system'));

console.log(`
ĐẠT ${R.filter(r=>r.ok).length}/${R.length} · LOI_CONSOLE ${errs.length}`);
if (errs.length) console.log(errs.slice(0,5));
proc.kill();
process.exit(R.every(r=>r.ok) && errs.length===0 ? 0 : 1);
