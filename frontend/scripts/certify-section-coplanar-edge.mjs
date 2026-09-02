/**
 * certify-section-coplanar-edge.mjs — THIẾT DIỆN THEO MẶT CHÉO, đo trong Chrome
 * thật. **0 mạng, 0 LLM** (bài mẫu chạy phía client).
 *
 * ─── ĐIỀU NÓ BẢO VỆ ───────────────────────────────────────────────────────
 *
 * `SECTION_COPLANAR_EDGE_GAP`: mặt phẳng (SAC) chứa trọn hai cạnh `SA`, `SC`
 * của khối; hai mặt kề cùng báo một cạnh, vòng nối vấp bản sao, và bản trước
 * ném `MALFORMED_SOLID` — đổ lỗi cho một bảng mặt hoàn toàn đúng.
 *
 * `tests/geometry/test_section_coplanar_edge.py` chứng minh kernel và cả chuỗi
 * backend đã đúng. Lượt này trả lời câu còn lại và chỉ trình duyệt trả lời
 * được: **học sinh có thật sự thấy thiết diện ấy không** — canvas dựng được,
 * tua bước chạy, ô soi mở đúng vật, 0 lỗi bảng điều khiển.
 *
 * ⚠️ Bài này nằm ở THƯ VIỆN, không ở bộ gợi ý trang chủ: bộ gợi ý cố ý nhỏ và
 * phủ ba loại hoạt động, không phủ mọi bài. Lượt đo đi đúng đường ấy.
 *
 * ⚠️ Tua bằng thanh trượt, không bằng nút *Bước sau* — xem
 * `certify-display-metadata.mjs` để biết vì sao.
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
await sleep(3000);
await ev(`(()=>{const b=[...document.querySelectorAll('button,a')]
  .find(e=>/Xem thư viện|Thư viện/i.test(e.textContent||''));
  b&&b.click(); return !!b;})()`);
await sleep(2200);
const mo = await evj(`(()=>{const c=[...document.querySelectorAll('.sample-card,.session-card,article,li,button,a')]
  .filter(e=>/mặt phẳng chéo/i.test(e.textContent||''));
  const n=c[c.length-1]; if(n) n.click(); return JSON.stringify({co:!!n});})()`);
kt("§30 thư viện có bài thiết diện mặt chéo", JSON.stringify(mo), !!mo?.co);
await sleep(3200);

const T = () => evj(`JSON.stringify({
  canvas: document.querySelectorAll('.geo3d-canvas canvas').length,
  duPhong: !!document.querySelector('.geo3d-fallback'),
  buoc: (document.querySelector('.geo3d-buoc-so')?.textContent||'').trim(),
  cay: [...document.querySelectorAll('.geo3d-tree-nhan,.geo3d-tree-catname')].map(e=>e.textContent.trim()),
  tieuDiem: (document.querySelector('.geo3d-focus')?.textContent||'').trim(),
  soiTen: (document.querySelector('.geo3d-soi-ten')?.textContent||'').trim(),
  chu: document.querySelector('.geo3d-xuong')?.innerText || '',
})`);

// Cây thành phần sống trong một NGĂN, mặc định đóng. Mở nó ra rồi mới soi —
// không mở mà quét thì được một mảng rỗng và một lượt xanh vô nghĩa.
await ev(`(()=>{const b=[...document.querySelectorAll('.geo3d-chip')]
  .find(e=>/Thành phần/i.test(e.textContent||'')); b&&b.click(); return !!b;})()`);
await sleep(800);

let t = await T();
kt("§30 xưởng 3D dựng được, không rơi bản dự phòng",
   `canvas=${t.canvas} duPhong=${t.duPhong}`, t.canvas === 1 && !t.duPhong);
kt("§30 bắt đầu ở bước 1", t.buoc, /^Bước 1\//.test(t.buoc));
kt("§21 thiết diện có mặt trong cây thành phần",
   JSON.stringify(t.cay.filter((x) => /thiết diện/i.test(x))),
   t.cay.some((x) => /thiết diện/i.test(x)));

await ev(`(()=>{const i=document.querySelector('.geo3d-scrub input[type=range]');
  const set=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
  set.call(i, i.max); i.dispatchEvent(new Event('input',{bubbles:true}));
  i.dispatchEvent(new Event('change',{bubbles:true})); return i.max;})()`);
await sleep(1200);
t = await T();
kt("§21 tua tới bước cuối vẫn dựng được", `${t.buoc} canvas=${t.canvas}`,
   t.canvas === 1 && /\/\d+$/.test(t.buoc));
kt("§18 KHÔNG chỗ nào nói khối hỏng", JSON.stringify(t.tieuDiem),
   !/MALFORMED|bảng mặt|KHÔNG LỒI/i.test(t.chu + t.tieuDiem));

await ev(`(()=>{const n=[...document.querySelectorAll('.geo3d-tree-nhan')]
  .find(e=>/thiết diện/i.test(e.textContent||''));
  (n?.closest('button')||n)?.click(); return 1;})()`);
await sleep(800);
t = await T();
/* Ô soi gọi thiết diện bằng CHU TRÌNH — `"ACS"` — đúng cách đề bài gọi nó
 * (*"thiết diện MNPQ"*). Đây là phép kiểm mạnh hơn việc tìm chữ "thiết diện":
 * nó chỉ ra được khi ô soi đã tra ngược cả ba đỉnh sang ký hiệu của chúng.
 * Ghép `label` thay vì `notation` sẽ cho `"Điểm AĐiểm CĐiểm S"` — đúng hồi quy
 * mà lượt đo này bắt được lần đầu. */
kt("§30 ô soi gọi thiết diện bằng chu trình ký hiệu", JSON.stringify(t.soiTen),
   /^[A-Z][A-Z′']*$/.test((t.soiTen || "").trim())
   && (t.soiTen || "").trim().length === 3);

console.log(`\nĐẠT ${R.filter((r) => r.ok).length}/${R.length} · LOI_CONSOLE ${errs.length}`);
if (errs.length) console.log(errs.slice(0, 5));
proc.kill();
process.exit(R.every((r) => r.ok) && errs.length === 0 ? 0 : 1);
