/**
 * certify-display-authority.mjs — MỘT THẨM QUYỀN ĐẶT TÊN, và nó ở backend.
 * **0 mạng, 0 LLM.**
 *
 * ─── ĐIỀU NÓ BẢO VỆ ───────────────────────────────────────────────────────
 *
 * `display_names.py` phát bốn trường — `label` · `notation` · `reference` ·
 * `role`. Frontend chỉ được BÀY chúng ra. Trước 2026-09-03 nó còn giữ một bảng
 * `producer → tiếng Việt` thứ hai để dựng dòng vai trò, và bảng ấy im lặng
 * thiếu khoá khi G4 thêm một phép dựng.
 *
 * Lượt này đo trên bề mặt THẬT, ở đúng nơi hai vấn đề từng lộ ra:
 *
 *   §11  bốn vùng — tên · vai trò · "Đang dựng" · "Dựa trên" — cùng nói một
 *        thứ tiếng, và không vùng nào in định danh máy;
 *   §26  câu LỒNG NHAU có cấu trúc: toán hạng nhiều chữ được bọc «…» nên tách
 *        được, thay vì ba chữ "và" dính vào nhau;
 *   §23  ký hiệu ghép của thiết diện KHÔNG phải chuỗi tên dài
 *        ("Điểm AĐiểm CĐiểm S" = 0 lần);
 *   §28  chế độ chi tiết (giáo viên) vẫn xem được `producer`/`depends`.
 *
 * ⚠️ Chọn vật SAU khi tua tới bước cuối — một vật chỉ có mặt từ bước dựng nó
 * trở đi (bất biến #31).
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

const DINH_DANH_MAY = /construct_[a-z_]+|measure\.[a-z_]+|intersect_[a-z_]+|plane_perpendicular_to_line|project_onto|vector_from_points|point3|line3|plane3|polygon3|solid\b|quantity\b/;

async function moBai(khop) {
  await send("Page.navigate", { url: "http://localhost:3000" });
  await sleep(3000);
  await ev(`(()=>{const b=[...document.querySelectorAll('button,a')]
    .find(e=>/Xem thư viện|Thư viện/i.test(e.textContent||'')); b&&b.click(); return !!b;})()`);
  await sleep(2200);
  const co = await evj(`(()=>{const c=[...document.querySelectorAll('.sample-card,.session-card,article,li,button,a')]
    .filter(e=>${khop}.test(e.textContent||''));
    const n=c[c.length-1]; if(n) n.click(); return JSON.stringify({co:!!n});})()`);
  await sleep(3200);
  await ev(`(()=>{const b=[...document.querySelectorAll('.geo3d-chip')]
    .find(e=>/Thành phần/i.test(e.textContent||'')); b&&b.click(); return !!b;})()`);
  await sleep(700);
  await ev(`(()=>{const i=document.querySelector('.geo3d-scrub input[type=range]');
    const set=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
    set.call(i, i.max); i.dispatchEvent(new Event('input',{bubbles:true}));
    i.dispatchEvent(new Event('change',{bubbles:true})); return i.max;})()`);
  await sleep(1200);
  return !!co?.co;
}

const D = () => evj(`JSON.stringify({
  chu: document.querySelector('.geo3d-xuong')?.innerText || '',
  tieuDiem: [...document.querySelectorAll('.geo3d-focus dd')].map(e=>e.textContent.trim()),
  cay: [...document.querySelectorAll('.geo3d-tree-nhan')].map(e=>e.textContent.trim()),
  soiTen: (document.querySelector('.geo3d-soi-ten')?.textContent||'').trim(),
  soiVai: (document.querySelector('.geo3d-soi-vai')?.textContent||'').trim(),
  ketQua: [...document.querySelectorAll('.geo3d-readout li')].map(e=>e.textContent.trim()),
})`);

// ══ A · CHUỖI G4: mặt ⊥ đường, rồi đo ═══════════════════════════════════
kt("§14 mở được bài G4", "", await moBai("/vuông góc với đường thẳng cho trước/i"));
await ev(`(()=>{const n=[...document.querySelectorAll('.geo3d-tree-nhan')]
  .find(e=>/Mặt phẳng qua .* vuông góc/i.test(e.textContent||''));
  (n?.closest('button')||n)?.click(); return 1;})()`);
await sleep(700);
let d = await D();
kt("§11 bốn vùng KHÔNG in định danh máy nào",
   JSON.stringify((d.chu.match(DINH_DANH_MAY) || []).slice(0, 3)),
   !DINH_DANH_MAY.test(d.chu));
kt("§14 vai trò do BACKEND đặt, không rỗng và không lặp tên",
   JSON.stringify([d.soiTen, d.soiVai]),
   !!d.soiVai && d.soiVai !== d.soiTen);
kt("§26 câu lồng nhau: toán hạng nhiều chữ được BỌC",
   JSON.stringify(d.ketQua),
   d.ketQua.length === 1 && d.ketQua[0].includes("«") && d.ketQua[0].includes("»"));
/* Hai dòng, hai vai — và đây chính là chỗ phân biệt phải nhìn thấy được:
 *   "Đang dựng" nói MỘT vật  ⇒ TÊN đầy đủ, được phép mang «…» khi nó nhắc
 *                              tới một vật khác bên trong;
 *   "Dựa trên"  là DANH SÁCH ⇒ CÁCH GỌI NGẮN, không bao giờ nhúng câu. */
kt("§10 `Đang dựng` dùng tên đầy đủ · `Dựa trên` dùng cách gọi ngắn",
   JSON.stringify(d.tieuDiem),
   d.tieuDiem.length === 2 && d.tieuDiem[0].includes("«")
   && !d.tieuDiem[1].includes("«"));

// ══ B · THIẾT DIỆN: ký hiệu ghép, không phải chuỗi tên dài ══════════════
kt("§23 mở được bài thiết diện mặt chéo", "", await moBai("/mặt phẳng chéo/i"));
await ev(`(()=>{const n=[...document.querySelectorAll('.geo3d-tree-nhan')]
  .find(e=>/thiết diện/i.test(e.textContent||''));
  (n?.closest('button')||n)?.click(); return 1;})()`);
await sleep(700);
d = await D();
kt("§23 KHÔNG có chuỗi tên dài ghép làm ký hiệu", JSON.stringify(d.soiTen),
   !/Điểm\s*[A-Z]Điểm/.test(d.chu) && /^[A-Z][A-Z′']*$/.test(d.soiTen));

// ══ C · CHẾ ĐỘ CHI TIẾT — giáo viên vẫn xem được xuất xứ ═══════════════
await ev(`(()=>{const b=[...document.querySelectorAll('button,label')]
  .find(e=>/Chi tiết|kỹ thuật/i.test(e.textContent||'')); (b?.querySelector('input')||b)?.click(); return !!b;})()`);
await sleep(700);
const kyThuat = await ev(`(document.querySelector('.geo3d-soi-ky-thuat')?.textContent||'').trim()`);
kt("§28 chế độ chi tiết VẪN xem được producer/depends", JSON.stringify(kyThuat),
   (kyThuat || "").length > 0);

console.log(`\nĐẠT ${R.filter((r) => r.ok).length}/${R.length} · LOI_CONSOLE ${errs.length}`);
if (errs.length) console.log(errs.slice(0, 5));
proc.kill();
process.exit(R.every((r) => r.ok) && errs.length === 0 ? 0 : 1);
