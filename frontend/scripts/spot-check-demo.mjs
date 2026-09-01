/**
 * spot-check-demo.mjs — TẬP DEMO KHOÁ LUẬN dựng trong Chrome THẬT.
 *
 * ─── HỎI GÌ, VÀ VÌ SAO CÂU ẤY KHÔNG THAY THẾ ĐƯỢC ────────────────────────
 *
 * `replay_demo_cases.py` đã chứng minh chuỗi tất định chạy và `build_scene3d`
 * ra JSON hợp lệ. Câu còn lại là câu duy nhất JSON không trả lời được: **nó có
 * dựng lên màn hình không**. WebGL, tua bước, 0 lỗi console.
 *
 * Đây là SMOKE cho tập demo, không phải bản chứng nhận đầy đủ — `certify-*.mjs`
 * mới là chứng nhận. Phạm vi hẹp là có chủ đích (§13).
 *
 * ─── NẠP QUA STORE ───────────────────────────────────────────────────────
 *
 * `loadEnvelope` là ĐÚNG cửa mà Thư viện và bài giáo viên giao đều đi qua — nó
 * gọi `module.validateConfig` rồi `module.init` như mọi lượt mở bài. Cửa sau
 * là chèn thẳng `active` vào store, và script này KHÔNG làm thế.
 *
 * Cần: `npm run dev` (:3000) ở cửa sổ khác.
 */
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const p = (r) => resolve(new URL(r, import.meta.url).pathname.replace(/^[/]/, ""));
const NGUON = [
  ["name-contract-probe", p("../../docs/evaluation/geometry/name-contract-probe/spot-envelopes.json")],
  ["translation-probe", p("../../docs/evaluation/geometry/translation-probe/spot-envelopes.json")],
];
const OUT = p("../../docs/evaluation/geometry/DEMO_SPOT_CHECK.json");

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

const dir = mkdtempSync(join(tmpdir(), "spot-demo-"));
const proc = spawn(CHROME, ["--headless=new", "--disable-gpu",
  "--remote-debugging-port=9871", `--user-data-dir=${dir}`,
  "--window-size=1600,900", "--hide-scrollbars",
  "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-shader",
  "--enable-unsafe-swiftshader", "about:blank"], { stdio: "ignore" });

let wsUrl;
for (let i = 0; i < 60 && !wsUrl; i++) {
  try {
    const l = await (await fetch("http://127.0.0.1:9871/json/list")).json();
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

const cases = [];
for (const [nhan, f] of NGUON) {
  if (!existsSync(f)) { console.error(`✗ thiếu ${f}`); process.exit(4); }
  for (const c of JSON.parse(readFileSync(f, "utf-8")).cases) {
    cases.push({ ...c, nguon: nhan });
  }
}
console.log(`━━ SPOT CHECK DEMO · ${cases.length} cảnh ━━`);

for (const c of cases) {
  await send("Page.navigate", { url: "http://localhost:3000" });
  await sleep(3000);

  // ⚠️ DẤU VÂN TAY TRANG trước mọi phép khẳng định (ARCHITECTURE_MAP §8 #14).
  // Một lượt soát "SẠCH" trên trang SAI là một lượt soát vô nghĩa, và kho này
  // đã dính một lần.
  const van = await evj(`JSON.stringify({
    root: !!document.querySelector('#root'),
    url: location.pathname,
  })`);
  if (!van?.root) { ghi(c.id, "dấu vân tay trang", "#root", "KHÔNG THẤY", false); continue; }

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
    buoc: document.querySelectorAll('.geo3d-thanh-nut button').length,
  })`);
  ghi(c.id, "nạp envelope → xưởng 3D dựng được", ".geo3d-xuong + canvas ≥ 1",
    `nạp=${nap} xuong=${d?.xuong} canvas=${d?.canvas} dựPhòng=${d?.duPhong}`,
    d?.xuong === true && d?.canvas >= 1 && d?.duPhong === false);

  // ⚠️ PHÉP KIỂM NÀY TỪNG NÓI DỐI. Bản đầu bấm `.geo3d-thanh-nut button` rồi
  // gọi mình là "tua bước" — nhưng đó là thanh CHIP (Xem đề / Thành phần), và
  // `tien=false` ở cả bốn ca trong khi phép kiểm vẫn XANH vì nó chỉ đếm nút.
  // Một phép kiểm xanh mà không chạm thứ nó khai là tệ hơn không có.
  //
  // Thứ thật sự chứng minh trace tất định lên được màn hình là ô đọc bước:
  // số bước + lời kể của ĐÚNG bước ấy — bất biến #31 (`frame k ⇔ trace[k]`)
  // hiện ra ở bề mặt học sinh.
  const buoc = await evj(`JSON.stringify({
    co: !!document.querySelector('.geo3d-buoc'),
    so: (document.querySelector('.geo3d-buoc-so')?.textContent||'').trim(),
    loi: (document.querySelector('.geo3d-buoc-loi')?.textContent||'').trim().length,
  })`);
  ghi(c.id, "ô đọc bước hiện trace tất định", "có số bước + lời kể",
    `số="${buoc?.so}" lờiKể=${buoc?.loi} ký tự`,
    buoc?.co === true && !!buoc?.so && (buoc?.loi ?? 0) > 0);

  const moi = consoleErrors.length - truoc;
  ghi(c.id, "0 lỗi console", "0", String(moi), moi === 0);
}

const pass = rows.filter((r) => r.pass).length;
writeFileSync(OUT, JSON.stringify({
  khai: "SMOKE trình duyệt cho TẬP DEMO khoá luận. Không phải bản chứng nhận "
    + "đầy đủ — xem `certify-*.mjs`.",
  chayLuc: new Date().toISOString(),
  cases: cases.map((c) => ({ id: c.id, nguon: c.nguon })),
  pass, total: rows.length, consoleErrors, rows,
}, null, 2), "utf-8");

console.log(`\n  DEMO_BROWSER_SMOKE  ${pass}/${rows.length}`);
console.log(`  lỗi console          ${consoleErrors.length}`);
console.log(`→ ${OUT}`);
ws.close(); proc.kill();
process.exit(pass === rows.length && consoleErrors.length === 0 ? 0 : 1);
