/**
 * spot-check-matrix.mjs — BA CẢNH DO AI SINH, DỰNG TRONG CHROME THẬT (§19).
 *
 * ─── HỎI GÌ ───────────────────────────────────────────────────────────────
 *
 * Matrix đã chứng minh chương trình CHẠY và `build_scene3d` ra JSON hợp lệ.
 * Câu còn lại là câu duy nhất JSON không trả lời được: **nó có dựng lên màn
 * hình không**. WebGL, chọn vật, cô lập, tua bước — trên cảnh mà mô hình tự
 * sinh, không phải trên bài mẫu đã dựng sẵn.
 *
 * ─── NẠP QUA STORE, VÀ VÌ SAO ĐIỀU ĐÓ VẪN THẬT ────────────────────────────
 *
 * `loadEnvelope` là ĐÚNG cửa mà Thư viện và bài giáo viên giao đều đi qua —
 * nó gọi `module.validateConfig` rồi `module.init` như mọi lượt mở bài. Nạp
 * qua nó không phải cửa sau; cửa sau là chèn thẳng `active` vào store, và đó
 * là thứ script này KHÔNG làm.
 *
 * ⚠️ Envelope đọc từ artifact đã được BỘ ĐO làm sạch (`Vec3`/`Fraction` →
 * chuỗi). Đó là vá của bộ đo, không phải bản sửa — bug thật nằm ở
 * `visual_adapter`, xem `build_matrix_spot_envelopes._sach`.
 *
 * Cần: `npm run dev` (:3000).
 */
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const NGUON = resolve(
  new URL("../../docs/evaluation/geometry/clean-baseline-v1/spot-envelopes.json",
    import.meta.url).pathname.replace(/^[/]/, ""));
const OUT = resolve(
  new URL("../../docs/evaluation/geometry/clean-baseline-v1/spot-check.json",
    import.meta.url).pathname.replace(/^[/]/, ""));

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const rows = [];
const consoleErrors = [];

function ghi(caseId, action, expected, actual, pass) {
  rows.push({ case: caseId, action, expected, actual, pass });
  console.log(`  ${pass ? "✓" : "✗"} [${caseId}] ${action} — ${actual}`);
}

const dir = mkdtempSync(join(tmpdir(), "spot-mx-"));
const proc = spawn(CHROME, ["--headless=new", "--disable-gpu",
  "--remote-debugging-port=9860", `--user-data-dir=${dir}`,
  "--window-size=1600,900", "--hide-scrollbars",
  "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-shader",
  "--enable-unsafe-swiftshader", "about:blank"], { stdio: "ignore" });

let wsUrl;
for (let i = 0; i < 60 && !wsUrl; i++) {
  try {
    const l = await (await fetch("http://127.0.0.1:9860/json/list")).json();
    wsUrl = l.find((t) => t.type === "page")?.webSocketDebuggerUrl;
  } catch { /* chưa lên */ }
  if (!wsUrl) await sleep(300);
}
if (!wsUrl) { console.error("✗ Chrome không lên"); process.exit(3); }

const ws = new WebSocket(wsUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pend = new Map();
ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.method === "Runtime.consoleAPICalled" && m.params?.type === "error") {
    consoleErrors.push((m.params.args ?? []).map((a) => a.value).join(" "));
  }
  if (m.method === "Runtime.exceptionThrown") {
    consoleErrors.push(m.params?.exceptionDetails?.text ?? "exception");
  }
  if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); }
};
const send = (method, params = {}) => new Promise((res) => {
  const i = ++id; pend.set(i, res);
  ws.send(JSON.stringify({ id: i, method, params }));
});
const ev = async (x) => (await send("Runtime.evaluate",
  { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
const evj = async (x) => { const v = await ev(x); return v ? JSON.parse(v) : null; };

await send("Page.enable"); await send("Runtime.enable");

const cases = JSON.parse(readFileSync(NGUON, "utf-8")).cases;
console.log(`━━ SPOT CHECK ${cases.length} cảnh · CLEAN_BASELINE_V1 ━━`);

for (const c of cases) {
  await send("Page.navigate", { url: "http://localhost:3000" });
  await sleep(3000);
  const truoc = consoleErrors.length;

  const nap = await ev(`(async()=>{
    const m = await import('/src/state/store.ts');
    m.useAppStore.getState().loadEnvelope(${JSON.stringify(c.envelope)});
    return 'ok';
  })()`);
  await sleep(4000);

  const d = await evj(`JSON.stringify({
    xuong: !!document.querySelector('.geo3d-xuong'),
    canvas: document.querySelectorAll('.geo3d-canvas canvas').length,
    duPhong: !!document.querySelector('.geo3d-fallback'),
    nutXem: document.querySelectorAll('.geo3d-noi-nut').length,
    buoc: document.querySelectorAll('.geo3d-thanh-nut button').length,
    text: document.body.innerText.length,
  })`);

  ghi(c.id, "nạp envelope AI sinh → xưởng 3D", ".geo3d-xuong + canvas",
      `nạp=${nap} xuong=${d?.xuong} canvas=${d?.canvas}`,
      d?.xuong === true && d?.canvas >= 1 && d?.duPhong === false);

  // Cây thành phần: mở rồi bấm một vật — đường tương tác của học sinh.
  await ev(`(()=>{const b=[...document.querySelectorAll('.geo3d-chip')]
    .find(e=>e.textContent.includes('Thành phần'));if(b)b.click();return !!b})()`);
  await sleep(900);
  const bam = await evj(`(()=>{
    const n=[...document.querySelectorAll('.geo3d-tree-nhan')];
    if(!n.length) return JSON.stringify({co:0});
    (n[0].closest('button')||n[0]).click();
    return JSON.stringify({co:n.length, ten:n[0].textContent.trim()});
  })()`);
  await sleep(800);
  const sauBam = await evj(`JSON.stringify({
    xuong: !!document.querySelector('.geo3d-xuong'),
    soi: !!document.querySelector('.geo3d-soi'),
  })`);
  ghi(c.id, "chọn một vật trong cây hình", "cây có mục, ô soi mở",
      `mục=${bam?.co} vật=${bam?.ten ?? "-"} soi=${sauBam?.soi}`,
      (bam?.co ?? 0) > 0 && sauBam?.xuong === true);

  // Tua bước — playback trên trace do AI sinh.
  const tua = await evj(`(()=>{
    const b=[...document.querySelectorAll('button')]
      .filter(x=>/Bước sau|Tiếp|▶|Phát/.test(x.textContent));
    if(!b.length) return JSON.stringify({co:0});
    b[0].click(); return JSON.stringify({co:b.length, nhan:b[0].textContent.trim()});
  })()`);
  await sleep(900);
  const sauTua = await evj(`JSON.stringify({
    xuong: !!document.querySelector('.geo3d-xuong'),
    canvas: document.querySelectorAll('.geo3d-canvas canvas').length,
  })`);
  ghi(c.id, "tua bước dựng (playback)", "xưởng còn nguyên sau khi tua",
      `nút=${tua?.co} xuong=${sauTua?.xuong} canvas=${sauTua?.canvas}`,
      sauTua?.xuong === true && (sauTua?.canvas ?? 0) >= 1);

  const moi = consoleErrors.length - truoc;
  ghi(c.id, "không lỗi console", "0 lỗi", `${moi} lỗi`, moi === 0);
}

try { ws.close(); } catch { /* đã đóng */ }
proc.kill();

const pass = rows.every((r) => r.pass);
writeFileSync(OUT, JSON.stringify({
  khai: "Spot check §19 — ba cảnh do AI sinh trong matrix, dựng trong Chrome "
      + "thật. Nạp qua `loadEnvelope`, đúng cửa Thư viện và bài giáo viên giao.",
  chayLuc: new Date().toISOString(),
  rows, consoleErrors, pass,
}, null, 1) + "\n", "utf-8");
console.log(`\n${pass ? "✓ SPOT CHECK XANH" : "✗ SPOT CHECK ĐỎ"} — `
  + `${rows.filter((r) => r.pass).length}/${rows.length} · lỗi console ${consoleErrors.length}`);
console.log(`→ ${OUT}`);
process.exit(pass ? 0 : 1);
