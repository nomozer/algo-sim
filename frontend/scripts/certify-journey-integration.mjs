/**
 * certify-journey-integration.mjs — HÀNH TRÌNH XUYÊN TẦNG, đo trong Chrome thật.
 *
 * ─── VÌ SAO CẦN CHẠY TRONG TRÌNH DUYỆT ────────────────────────────────────
 *
 * Bốn nhóm ca dưới đây kiểm những chỗ mà **không tầng nào sở hữu một mình**:
 * `A` tua bước (chữ · thanh trượt · kết quả phải cùng nói một bước),
 * `B` chọn vật (cây → ô soi phải nói đúng vật vừa chọn),
 * `C` tách/ráp khối (nút phải kể đúng trạng thái hiện tại),
 * `D` **đổi bài** (trạng thái bài cũ không được rớt sang bài mới).
 *
 * Nhóm `D` là lý do file này tồn tại. Lỗi đo được trước bản vá: mở bài 12 bước,
 * tua tới bước 10, chọn một vật, tách khối, rồi mở bài 6 bước thì màn hình hiện
 * **“Bước 10/6”**. Nó không bắt được bằng vitest vì `SimulationWorkspace` dựng
 * `Scene3DExplorer` ở cùng vị trí cho mọi bài, nên React DÙNG LẠI component —
 * hành vi ấy chỉ hiện ra khi có một cây React thật sống qua hai lần nạp cảnh.
 *
 * **0 mạng, 0 LLM**: envelope đọc thẳng từ artifact đã niêm phong trong
 * `docs/evaluation/geometry/`, nạp vào store bằng `loadEnvelope`.
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

const dir = mkdtempSync(join(tmpdir(), "integ-"));
const proc = spawn(CHROME, ["--headless=new", "--remote-debugging-port=9895",
  `--user-data-dir=${dir}`, `--window-size=${VP.w},${VP.h}`, "--hide-scrollbars",
  "--force-device-scale-factor=2", "--use-gl=angle", "--use-angle=swiftshader",
  "--enable-unsafe-swiftshader", "about:blank"], { stdio: "ignore" });
let wsUrl;
for (let i = 0; i < 80 && !wsUrl; i++) {
  try { wsUrl = (await (await fetch("http://127.0.0.1:9895/json/list")).json())
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

const R = []; const kt = (ten, ky, thuc, ok) => {
  R.push({ ten, ky, thuc, ok }); console.log(`${ok?"✓":"✗"} ${ten} | mong=${ky} | thuc=${thuc}`);
};
const T = () => evj(`JSON.stringify({
  buocText: (document.querySelector('.geo3d-buoc-so')?.textContent||'').trim(),
  soVatVe: document.querySelectorAll('.geo3d-label').length,
  nhanHien: [...document.querySelectorAll('.geo3d-label')].filter(e=>e.style.opacity!=='0').map(e=>e.textContent.trim()),
  soiTen: (document.querySelector('.geo3d-soi-ten')?.textContent||'').trim(),
  soiKT: (document.querySelector('.geo3d-soi-ky-thuat')?.textContent||'').trim(),
  coSoi: !!document.querySelector('.geo3d-soi'),
  nutBung: (document.querySelector('.geo3d-noi-nut')?.textContent||'').trim(),
  readout: [...document.querySelectorAll('.geo3d-readout')].map(e=>e.textContent.trim()),
  scrub: Number(document.querySelector('.geo3d-scrub input')?.value ?? -1),
  scrubMax: Number(document.querySelector('.geo3d-scrub input')?.max ?? -1),
  nganMo: !!document.querySelector('.geo3d-ngan'),
  chiTietMo: !!document.querySelector('.geo3d-chip.la-mo'),
})`);

// ══ A · ĐƯỜNG THÀNH CÔNG ═════════════════════════════════════════════════
await moCa("clean-baseline-v2", "v2_04_thiet_dien_goc_va_the_tich", 0);
let t = await T();
kt("A1 cảnh đầu: bước 1", "Bước 1/12", t.buocText, t.buocText === "Bước 1/12");
kt("A2 cảnh đầu: thanh trượt ở 0", "0", String(t.scrub), t.scrub === 0);
await datBuoc(5); await sleep(1200); t = await T();
kt("A3 bước giữa: chữ khớp thanh trượt", "Bước 6/12 & scrub=5",
   `${t.buocText} & scrub=${t.scrub}`, t.buocText === "Bước 6/12" && t.scrub === 5);
await datBuoc(11); await sleep(1200); t = await T();
kt("A4 bước cuối", "Bước 12/12", t.buocText, t.buocText === "Bước 12/12");
kt("A5 kết quả hiện ở bước cuối", "có readout", JSON.stringify(t.readout), t.readout.length > 0);

// ══ B · SOI VẬT: nhãn và ô soi phải nói cùng một vật ══════════════════════
await bam(".geo3d-chip", "Chi tiết"); await sleep(500);
const chonR = await chonVat("Trung điểm N của AD");
t = await T();
kt("B1 chọn được vật qua cây", "ok", chonR, chonR === "ok");
kt("B2 ô soi nói đúng vật vừa chọn", "Trung điểm N của AD", t.soiTen,
   t.soiTen === "Trung điểm N của AD");
kt("B3 ô soi có phép dựng + dựa trên", "midpoint & A, D",
   t.soiKT, t.soiKT.includes("midpoint") && t.soiKT.includes("A, D"));

// ══ C · TÁCH KHỐI / RÁP LẠI ══════════════════════════════════════════════
await bam(".geo3d-noi-nut", "Tách khối"); await sleep(1400); t = await T();
kt("C1 tách xong nút đổi thành Ráp lại", "Ráp lại", t.nutBung, t.nutBung === "Ráp lại");
await bam(".geo3d-noi-nut", "Ráp lại"); await sleep(1400); t = await T();
kt("C2 ráp lại nút quay về Tách khối", "Tách khối", t.nutBung, t.nutBung === "Tách khối");

// ══ D · TRẠNG THÁI CŨ CÓ RỚT SANG BÀI MỚI KHÔNG ══════════════════════════
// Dựng một trạng thái "bẩn" rồi mở bài KHÁC mà KHÔNG tải lại trang — đúng
// đường người dùng đi: mở bài mới từ trong workspace.
await datBuoc(9); await sleep(900);
await bam(".geo3d-noi-nut", "Tách khối"); await sleep(1200);
const truoc = await T();
console.log("  [bẩn] " + JSON.stringify({ buoc: truoc.buocText, chon: truoc.soiTen,
  bung: truoc.nutBung, chiTiet: truoc.chiTietMo }));

await ev(`(async()=>{const m=await import('/src/state/store.ts');
  m.useAppStore.getState().loadEnvelope(${JSON.stringify(env("name-contract-probe","n1_thoi_dinh_thu_tu"))});
  return 'ok';})()`);
await sleep(4000);
const sau = await T();
console.log("  [bài mới] " + JSON.stringify({ buoc: sau.buocText, chon: sau.soiTen,
  bung: sau.nutBung, chiTiet: sau.chiTietMo, scrub: sau.scrub }));
kt("D1 bài mới bắt đầu ở bước 1", "Bước 1/…", sau.buocText, /^Bước 1\//.test(sau.buocText));
kt("D2 bài mới không giữ vật đang chọn của bài cũ", "không có ô soi",
   `coSoi=${sau.coSoi} ten="${sau.soiTen}"`, sau.coSoi === false);
kt("D3 bài mới không mở sẵn trạng thái tách khối", "Tách khối", sau.nutBung,
   sau.nutBung === "Tách khối");

writeFileSync(join(OUT, "journey.json"), JSON.stringify(
  { chayLuc: new Date().toISOString(), R, loiConsole: errs }, null, 2));
console.log(`
ĐẠT ${R.filter(x=>x.ok).length}/${R.length} · LOI_CONSOLE ${errs.length}`);
ws.close(); proc.kill();
