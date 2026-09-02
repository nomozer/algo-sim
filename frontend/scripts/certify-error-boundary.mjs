/**
 * certify-error-boundary.mjs — LƯỚI CHẶN NGOẠI LỆ, đo trong Chrome thật.
 * **0 mạng, 0 LLM.**
 *
 * ─── VÌ SAO PHẢI ĐO Ở ĐÂY, KHÔNG Ở VITEST ────────────────────────────────
 *
 * `renderToString` **KHÔNG chạy error boundary**: SSR không có pha commit, nên
 * `getDerivedStateFromError` không bao giờ được gọi và ngoại lệ lan thẳng ra
 * ngoài. Kho lại không có `@testing-library/react` và không có jsdom. Vậy câu
 * *"một cây SỐNG ném thì có bị chặn không"* chỉ trả lời được bằng một trình
 * duyệt thật.
 *
 * ─── TIÊM LỖI THẾ NÀO MÀ KHÔNG ĐỂ LẠI CÔNG TẮC TRONG SẢN PHẨM ───────────
 *
 * Không thêm cờ nào vào mã sản phẩm. Lượt đo vá **một prototype của React**
 * ngay trong trang đang chạy: bọc `Array.prototype.map` để nó ném đúng một lần
 * khi cây con của xưởng dựng lại. Vá sống, chỉ trong tab của lượt đo, gỡ ngay
 * sau đó — không dòng nào của nó tồn tại trong bản dựng.
 *
 * Bốn điều được khẳng định:
 *   §27  không trắng màn — `#root` còn nội dung, thanh điều hướng còn đó;
 *   §11  không lộ vết ngăn xếp cho người học;
 *   §28  hành động phục hồi là THẬT — bấm xong dựng lại được;
 *   §8   mở bài khác sau sự cố ⇒ lưới QUÊN lỗi cũ (`resetKey`).
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

async function moThuVien(khop) {
  await send("Page.navigate", { url: "http://localhost:3000" });
  await sleep(3000);
  await ev(`(()=>{const b=[...document.querySelectorAll('button,a')]
    .find(e=>/Xem thư viện|Thư viện/i.test(e.textContent||'')); b&&b.click(); return !!b;})()`);
  await sleep(2000);
  const co = await evj(`(()=>{const c=[...document.querySelectorAll('.sample-card,.session-card,article,li,button,a')]
    .filter(e=>${khop}.test(e.textContent||''));
    const n=c[c.length-1]; if(n) n.click(); return JSON.stringify({co:!!n});})()`);
  await sleep(3000);
  return !!co?.co;
}

const T = () => evj(`JSON.stringify({
  rootCon: (document.querySelector('#root')?.innerText||'').trim().length,
  dieuHuong: !!document.querySelector('.nav-bar'),
  fallback: !!document.querySelector('.loi-chan'),
  nhan: (document.querySelector('.loi-chan-nhan')?.textContent||'').trim(),
  canvas: document.querySelectorAll('.geo3d-canvas canvas').length,
  chu: (document.querySelector('#root')?.innerText||''),
})`);

kt("§0 mở được một bài hình học", "", await moThuVien("/mặt phẳng chéo/i"));
let t = await T();
kt("§0 trạng thái đầu bình thường", `canvas=${t.canvas} fallback=${t.fallback}`,
   t.canvas === 1 && !t.fallback);

/* ── TIÊM: ném trong lúc DỰNG, ở chỗ chắc chắn được đọc ────────────────
 *
 * Đặt một getter ném trên `scene.objects`. Mọi lượt dựng của xưởng đều đọc
 * trường ấy (`objectsAt`, dải kết quả, cây thành phần), nên ngoại lệ rơi đúng
 * vào pha RENDER — đúng lớp mà error boundary bắt được, và đúng lớp mà một bất
 * biến bị phá sẽ rơi vào.
 *
 * Vá SỐNG trong tab của lượt đo, gỡ ngay sau đó. Không dòng nào của nó tồn tại
 * trong bản dựng: một "chế độ gây lỗi" trong sản phẩm là một bề mặt tấn công. */
await ev(`(()=>{
  const st = window.__ALGO_SIM_STORE__?.getState?.();
  const env = st?.active?.envelope;
  const canh = env?.scene3d;
  if (!canh) return "khong-co-canh";
  // Đầu độc một TRƯỜNG mà vòng dựng buộc phải đọc: \`objectsAt\` lọc theo
  // \`o.id\`, và \`deriveVisualSubEntities\` cũng đọc nó. Cổng \`hopLeScene3D\`
  // thì chỉ nhìn hình dạng mảng nên envelope vẫn qua được cửa vào.
  const vat = canh.objects[canh.objects.length - 1];
  const gocId = vat.id;
  Object.defineProperty(vat, "id", {
    configurable: true,
    get() { throw new Error("tiêm lỗi có kiểm soát"); },
  });
  window.__goTiem = () => Object.defineProperty(vat, "id", {
    configurable: true, writable: true, enumerable: true, value: gocId,
  });
  // Nạp lại với MỘT CẢNH MỚI (cùng mảng vật): \`useMemo([scene])\` của xưởng
  // chỉ tính lại khi danh tính \`scene\` đổi. Giữ nguyên mảng thì phép tiêm
  // không bao giờ được đọc, và lượt đo sẽ xanh mà chưa chứng minh gì.
  st.loadEnvelope({ ...env, scene3d: { ...canh } });
  return "da-tiem";})()`);
await sleep(1500);
t = await T();
kt("§27 KHÔNG trắng màn — `#root` còn nội dung",
   `ký tự=${t.rootCon}`, t.rootCon > 0);
kt("§27 thanh điều hướng SỐNG SÓT — lưới trong giữ được vỏ",
   `nav=${t.dieuHuong} fallback=${t.fallback}`, t.dieuHuong);
kt("§11 KHÔNG lộ vết ngăn xếp cho người học", "",
   !/at [A-Za-z]+ \(|componentStack|Error: tiêm lỗi/.test(t.chu));

const daChan = t.fallback;
await ev(`window.__goTiem && window.__goTiem()`);

if (daChan) {
  kt("§28 hành động phục hồi có thật", JSON.stringify(t.nhan), t.nhan.length > 0);
  await ev(`(()=>{const b=[...document.querySelectorAll('.loi-chan button')][0]; b&&b.click(); return !!b;})()`);
  await sleep(1500);
  t = await T();
  kt("§28 bấm phục hồi ⇒ dựng lại được", `canvas=${t.canvas} fallback=${t.fallback}`,
     !t.fallback && t.canvas === 1);
} else {
  /* Không chặn được nghĩa là phép tiêm không chạm tới đường dựng — lượt đo
   * KHÔNG được báo xanh, vì lúc ấy nó chưa chứng minh gì. */
  kt("§15 phép tiêm phải chạm tới đường dựng", "fallback không hiện", false);
}

/* ── §8 ĐỔI BÀI SAU SỰ CỐ: lưới phải QUÊN lỗi cũ ────────────────────── */
kt("§8 mở bài khác sau sự cố", "", await moThuVien("/vuông góc với đường thẳng cho trước/i"));
t = await T();
kt("§8 bài mới dựng SẠCH, lưới đã quên lỗi cũ",
   `canvas=${t.canvas} fallback=${t.fallback}`, t.canvas === 1 && !t.fallback);

console.log(`\nĐẠT ${R.filter((r) => r.ok).length}/${R.length}`);
proc.kill();
process.exit(R.every((r) => r.ok) ? 0 : 1);
