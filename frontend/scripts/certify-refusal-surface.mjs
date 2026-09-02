/**
 * certify-refusal-surface.mjs — BỀ MẶT TỪ CHỐI, đo trong Chrome thật.
 *
 * ─── ĐIỀU ĐANG ĐƯỢC BẢO VỆ ────────────────────────────────────────────────
 *
 * Hệ **fail-closed**: từ chối là mặc định. Nhưng một lượt từ chối chỉ đúng nếu
 * bề mặt cũng đúng, và bề mặt thì có bốn cách hỏng độc lập nhau:
 *   1. sai nhãn — nói “ngoài danh mục” cho một bài hình học dựng hụt,
 *   2. vẫn dựng cảnh — hiện khung 3D rỗng bên dưới lời từ chối,
 *   3. lộ mã kỹ thuật — `grounding_failure`, `simulation_id` lọt lên UI,
 *   4. cụt đường — từ chối xong không còn lối nào đi tiếp.
 *
 * Phần cuối nạp envelope **hỏng** (`{}`, thiếu `simulation_id`, `scene3d` sai
 * kiểu, không có `scene3d`) để khẳng định không ca nào ném lỗi hay làm trắng
 * màn — kho **không có** error boundary nào, nên một lần ném là mất cả trang.
 *
 * **0 mạng, 0 LLM**: mọi envelope dựng tại chỗ trong kịch bản.
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

const dir = mkdtempSync(join(tmpdir(), "refus-"));
const proc = spawn(CHROME, ["--headless=new", "--remote-debugging-port=9896",
  `--user-data-dir=${dir}`, `--window-size=${VP.w},${VP.h}`, "--hide-scrollbars",
  "--force-device-scale-factor=2", "--use-gl=angle", "--use-angle=swiftshader",
  "--enable-unsafe-swiftshader", "about:blank"], { stdio: "ignore" });
let wsUrl;
for (let i = 0; i < 80 && !wsUrl; i++) {
  try { wsUrl = (await (await fetch("http://127.0.0.1:9896/json/list")).json())
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

const R = []; const kt = (t,k,th,ok)=>{R.push({t,k,th,ok});console.log(`${ok?"✓":"✗"} ${t} | ${th}`);};

// Năm loại từ chối mà sản phẩm PHÁT RA THẬT. `learner_reason` lấy nguyên văn
// từ `backend/app/learner_messages.py`; không câu nào do bộ kiểm viết.
const LOAI = [
  ["OUT_OF_DOMAIN", { failure_category:"out_of_scope", error_code:"gate_out_of_scope",
    reason:"ngoài phạm vi", learner_reason:"Hệ thống này mô phỏng HÌNH HỌC KHÔNG GIAN (Toán 11–12). Đề bạn gửi không thuộc phạm vi ấy." }],
  ["UNSUPPORTED_CAPABILITY", { failure_category:"not_simulation_suitable", error_code:"gate_not_simulatable",
    reason:"không có cơ chế", learner_reason:"Nội dung này đọc hiểu là đủ." }],
  ["GROUNDING_FAILURE", { failure_category:"geometry_generation_failed", error_code:"input_not_grounded",
    reason:"A: source_fact_id 'A(0; 0; 0)' không có trong RequestContract",
    learner_reason:"AlgoSim đã nhận ra đây là bài hình học không gian và đã thử dựng chương trình mô phỏng, nhưng chương trình sinh ra chưa qua được khâu kiểm chứng." }],
  ["INVALID_PROGRAM", { failure_category:"geometry_generation_failed", error_code:"ir_static_check_failed",
    reason:"statements.3.construct_point.expr: toán hạng chưa dựng",
    learner_reason:"AlgoSim đã nhận ra đây là bài hình học không gian và đã thử dựng chương trình mô phỏng, nhưng chương trình sinh ra chưa qua được khâu kiểm chứng." }],
  ["CHECK_FAILURE", { failure_category:"geometry_generation_failed", error_code:"postcondition_failed",
    reason:"hậu điều kiện distance sai",
    learner_reason:"AlgoSim đã nhận ra đây là bài hình học không gian và đã thử dựng chương trình mô phỏng, nhưng chương trình sinh ra chưa qua được khâu kiểm chứng." }],
];

for (const [ten, u] of LOAI) {
  await send("Page.navigate", { url: "http://localhost:3000" }); await sleep(3000);
  await ev(`(async()=>{const m=await import('/src/state/store.ts');
    m.useAppStore.getState().loadUnsupported(${JSON.stringify({status:"unsupported", ...u})}); return 'ok';})()`);
  await sleep(1500);
  const d = await evj(`JSON.stringify({
    eyebrow:(document.querySelector('.eyebrow')?.textContent||'').trim(),
    than:(document.querySelector('.card p')?.textContent||'').trim().slice(0,60),
    goiY:(document.querySelector('.card .notes')?.textContent||'').trim().slice(0,60),
    soCanvas: document.querySelectorAll('canvas').length,
    coXuong3D: !!document.querySelector('.geo3d-xuong'),
    loKyThuat: ['input_not_grounded','geometry_generation_failed','out_of_scope',
      'not_simulation_suitable','ir_static_check_failed','postcondition_failed',
      'source_fact_id','statements.','Traceback','at Object.'].filter(k=>document.body.innerText.includes(k)),
    coDuongVe: !!document.querySelector('textarea, input[type=text]')
      || [...document.querySelectorAll('a,button')].some(e=>/thư viện|mô phỏng mới|trang chủ/i.test(e.textContent)),
  })`);
  kt(`${ten} · nhãn`, "có nhãn", `"${d.eyebrow}"`, d.eyebrow.length > 0);
  kt(`${ten} · KHÔNG dựng cảnh`, "0 canvas", `canvas=${d.soCanvas} xuong3D=${d.coXuong3D}`,
     d.soCanvas === 0 && d.coXuong3D === false);
  kt(`${ten} · KHÔNG lộ mã kỹ thuật`, "[]", JSON.stringify(d.loKyThuat), d.loKyThuat.length === 0);
  kt(`${ten} · có đường quay lại`, "true", String(d.coDuongVe), d.coDuongVe === true);
  console.log(`     nhãn="${d.eyebrow}" gợi ý="${d.goiY}"`);
}

// ══ Biên lỗi: envelope hỏng / thiếu cảnh / trạng thái tương tác lạ ═══════
await send("Page.navigate", { url: "http://localhost:3000" }); await sleep(3000);
const xau = await ev(`(async()=>{
  const m = await import('/src/state/store.ts');
  const kq = [];
  for (const [ten, env] of [
      ["envelope rỗng", {}],
      ["thiếu simulation_id", { status:"ok", scene3d:{ objects:[], steps:[] } }],
      ["scene3d hỏng", { status:"ok", simulation_id:"generic.semantic_program", config:{}, scene3d:{ objects:"KHONG PHAI MANG" } }],
      ["scene3d thiếu hẳn", { status:"ok", simulation_id:"generic.semantic_program", config:{} }],
  ]) {
    try { m.useAppStore.getState().loadEnvelope(env); kq.push([ten, "khong nem"]); }
    catch (e) { kq.push([ten, "NEM: " + String(e).slice(0,60)]); }
  }
  return JSON.stringify(kq);
})()`);
await sleep(1200);
const sauXau = await evj(`JSON.stringify({
  trangTrong: (document.body.innerText||'').trim().length < 40,
  coRoot: !!document.querySelector('#root')?.firstElementChild,
})`);
console.log("  [envelope xấu] " + xau);
kt("Biên lỗi · không trắng màn", "còn nội dung",
   `trangTrong=${sauXau.trangTrong} coRoot=${sauXau.coRoot}`,
   sauXau.trangTrong === false && sauXau.coRoot === true);

writeFileSync(join(OUT, "refusal-surface.json"), JSON.stringify({ R, loiConsole: errs }, null, 2));
console.log(`
ĐẠT ${R.filter(x=>x.ok).length}/${R.length} · LOI_CONSOLE ${errs.length}`);
ws.close(); proc.kill();
