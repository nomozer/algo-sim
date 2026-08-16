/**
 * capture-phase-evidence.mjs — ẢNH TRƯỚC/SAU CHO MỘT PHA SẢN PHẨM.
 *
 * ─── VÌ SAO CÓ FILE NÀY ────────────────────────────────────────────────────
 *
 * Một pha KHÔNG được tính là đã sửa chỉ vì hợp đồng, chủ sở hữu chung hay test
 * đã đổi. Hạ tầng xong không thay được cải thiện mà HỌC SINH NHÌN THẤY.
 *
 * Script này chụp đúng thẻ mô phỏng ở một trạng thái xác định. Kết hợp với
 * `git checkout <ref> -- <file>` (Vite HMR nạp lại ngay, không cần dựng lại) thì
 * có được cặp TRƯỚC/SAU trên CÙNG một máy, cùng một bề rộng, cùng một đề —
 * tức khác biệt duy nhất là bản vá.
 *
 * ─── DÙNG ──────────────────────────────────────────────────────────────────
 *
 *   node scripts/capture-phase-evidence.mjs \
 *     --target logic.boolean_dag --name e-truoc --out ../docs/evaluation/m20/phase-evidence
 *
 * `--act` nhận một biểu thức JS chạy SAU khi nạp đề (để chụp trạng thái sau
 * thao tác), ví dụ phát một `SimAction` qua store.
 *
 * ⚠️ Chụp CLIP theo `.workspace-card` chứ không chụp cả trang: ảnh cả trang bị
 * chi phối bởi chrome trình duyệt và vị trí cuộn, nên hai lượt chụp khác nhau ở
 * những thứ không liên quan tới bản vá.
 */
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const PORT = argOf("--port", "3000");
const CDP_PORT = argOf("--cdp", "9391");
const OUT = resolve(argOf("--out", "../docs/evaluation/m20/phase-evidence"));
const TARGET = argOf("--target", "");
const NAME = argOf("--name", "shot");
const ACT = argOf("--act", "");
const VIEWPORT = argOf("--viewport", "1536,864");

if (!TARGET) { console.error("Thiếu --target"); process.exit(2); }
if (!existsSync(OUT)) mkdirSync(OUT, { recursive: true });

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
].find((p) => existsSync(p));
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

const profile = mkdtempSync(join(tmpdir(), "algosim-evidence-"));
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", `--remote-debugging-port=${CDP_PORT}`,
  `--user-data-dir=${profile}`, `--window-size=${VIEWPORT.replace(",", ",")}`,
  "--hide-scrollbars", "about:blank",
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const shutdown = () => { try { chrome.kill(); } catch { /* đã chết */ } };
process.on("SIGINT", () => { shutdown(); process.exit(130); });

async function connect() {
  for (let i = 0; i < 40; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`)).json();
      const page = list.find((t) => t.type === "page");
      if (page) return page.webSocketDebuggerUrl;
    } catch { /* chưa lên */ }
    await sleep(250);
  }
  throw new Error("Chrome không mở được cổng debug.");
}

const ws = new WebSocket(await connect());
await new Promise((r) => (ws.onopen = r));
let id = 0;
const pending = new Map();
ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
};
const send = (method, params = {}) => new Promise((res) => {
  const i = ++id; pending.set(i, res);
  ws.send(JSON.stringify({ id: i, method, params }));
});
const ev = async (expr) => {
  const r = await send("Runtime.evaluate", {
    expression: expr, awaitPromise: true, returnByValue: true,
  });
  const ex = r.result?.exceptionDetails;
  if (ex) return "LỖI: " + String(ex.exception?.description ?? ex.text ?? "?").split("\n")[0];
  return r.result?.result?.value;
};

const [w, h] = VIEWPORT.split(",").map(Number);
await send("Page.enable"); await send("Runtime.enable");
await send("Emulation.setDeviceMetricsOverride", {
  width: w, height: h, deviceScaleFactor: 1, mobile: false,
});
await send("Page.navigate", { url: `http://localhost:${PORT}` });
await sleep(3400);

/* Vite băm URL module theo phiên, nên `import('/src/…')` trần KHÔNG trúng bản
   trang đã nạp (nó tạo một instance thứ hai, store rỗng). Lấy URL THẬT từ
   `performance.getEntriesByType('resource')` — cùng cách `audit-composition.mjs`
   đã dùng và đã chạy được. */
const u = JSON.parse(await ev(`(()=>{const pick=(s)=>{const h=performance.getEntriesByType('resource').map(e=>e.name).filter(n=>n.includes(s));
 return h.length?h[h.length-1]:new URL(s,location.origin).href;};
 return JSON.stringify({store:pick('/src/state/store.ts'),catalog:pick('/src/data/offline-catalog.ts'),
 registry:pick('/src/simulations/registry.ts'),sims:pick('/src/simulations/index.ts')});})()`));

/* Nạp trước bốn module rồi mới dùng — cùng lý do `audit-composition.mjs` phải
   làm thế: lượt `import()` ĐẦU TIÊN của một module nặng có thể chưa trả kịp qua
   CDP, và khi ấy `Runtime.evaluate` trả `undefined` chứ không ném. */
await ev(`(async()=>{${Object.values(u).map((x) => `await import(${JSON.stringify(x)});`).join("")}return 1})()`);
await sleep(600);

const loadExpr = `(async()=>{
  const s=await import(${JSON.stringify(u.store)});
  const c=await import(${JSON.stringify(u.catalog)});
  const rg=await import(${JSON.stringify(u.sims)});
  const reg=await import(${JSON.stringify(u.registry)});
  if(reg.listSimulations().length===0) rg.registerAllSimulations();
  s.useAppStore.getState().reset();
  const e=c.offlineCatalog().find(x=>x.simId===${JSON.stringify(TARGET)});
  if(!e) return 'không có mẫu offline';
  s.useAppStore.getState().loadEnvelope(e.envelope);
  return s.useAppStore.getState().active ? 'ok' : 'không ra active';
})()`;

let load = await ev(loadExpr);
if (load !== "ok") { await sleep(1500); load = await ev(loadExpr); }
if (load !== "ok") { console.error(`Không nạp được ${TARGET}: ${load}`); shutdown(); process.exit(3); }
await sleep(700);

if (ACT) {
  const r = await ev(`(async()=>{${ACT}})()`);
  console.log(`  thao tác → ${r}`);
  await sleep(700);
}

/* CLIP theo thẻ mô phỏng: ảnh cả trang lẫn cả chrome trình duyệt và vị trí
   cuộn, nên hai lượt chụp sẽ khác nhau ở thứ không liên quan tới bản vá. */
const box = JSON.parse(await ev(`(()=>{
  const el=document.querySelector('.workspace-card');
  if(!el) return 'null';
  const r=el.getBoundingClientRect();
  return JSON.stringify({x:Math.max(0,r.x-12),y:Math.max(0,r.y-12),
                         width:Math.min(${w},r.width+24),height:r.height+24});
})()`));
if (!box) { console.error("Không thấy .workspace-card"); shutdown(); process.exit(4); }

const shot = await send("Page.captureScreenshot", {
  format: "png", clip: { ...box, scale: 1 }, captureBeyondViewport: true,
});
const file = join(OUT, `${NAME}.png`);
writeFileSync(file, Buffer.from(shot.result.data, "base64"));
console.log(`  ✔ ${TARGET} @${VIEWPORT} → ${file}  (${Math.round(box.width)}×${Math.round(box.height)})`);

shutdown();
process.exit(0);
