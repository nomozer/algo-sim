/**
 * diagnose-refusal-flake.mjs — CHẨN ĐOÁN, không phải nghiệm thu.
 *
 * ─── CÂU HỎI DUY NHẤT, VÀ NÓ PHÂN XỬ HAI NHÁNH ────────────────────────────
 *
 * `certify-refusal-surface.mjs` chập chờn: 1/10 lượt sạch, và mỗi lần đỏ thì
 * đỏ theo CẶP — `nhãn` rỗng **và** `có đường quay lại` sai — tức cả trang
 * trống, không phải một nhãn viết sai. Hai giả thuyết dẫn tới hai chỗ sửa
 * hoàn toàn khác nhau:
 *
 *   NHÁNH A · sản phẩm — thẻ từ chối **không bao giờ** hiện. Trạng thái nạp
 *     vào store rồi mất, hoặc React không dựng lại. Người dùng thật gặp được.
 *   NHÁNH B · bộ đo — thẻ hiện **muộn hơn** khoảng ngủ cố định của bộ kiểm
 *     (`sleep(3000)` sau `Page.navigate`, `sleep(1500)` sau khi nạp state).
 *     Sản phẩm đúng; phép đo hỏi sai thời điểm.
 *
 * Phân biệt được bằng đúng một phép: sau khi nạp trạng thái, **chờ tiếp** và
 * xem thẻ có hiện ra không. Hiện ở giây thứ 4 ⇒ nhánh B. Không bao giờ hiện ⇒
 * nhánh A.
 *
 * Script này KHÔNG khẳng định gì cả — nó ghi số. Ảnh chụp được lưu cho đúng
 * những lượt mà mốc 3,0 s + 1,5 s sẽ trượt.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const FE = fileURLToPath(new URL("..", import.meta.url));
const GOC = resolve(FE, "..");
const OUT = join(GOC, "docs", "evaluation", "geometry", "final-system-release");
const ANH = join(OUT, "flake-diagnosis");
mkdirSync(ANH, { recursive: true });

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const arg = (n, d) => {
  const i = process.argv.indexOf(`--${n}`);
  return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : d;
};
const LAN = Number(arg("iters", "12"));
const BASE = arg("base", "http://localhost:3000");

/* Mốc của bộ kiểm hiện tại — hằng số ở đây để so, KHÔNG để dùng. */
const NGU_SAU_NAVIGATE = 3000;
const NGU_SAU_NAP_STATE = 1500;

const port = 9700 + Math.floor(Math.random() * 200);
const dir = mkdtempSync(join(tmpdir(), "diag-"));
const proc = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${port}`,
  `--user-data-dir=${dir}`, "--window-size=1600,900", "--hide-scrollbars",
  "--force-device-scale-factor=2", "--use-gl=angle", "--use-angle=swiftshader",
  "--enable-unsafe-swiftshader", "about:blank"], { stdio: "ignore" });

let wsUrl;
for (let i = 0; i < 80 && !wsUrl; i++) {
  try {
    wsUrl = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json())
      .find((t) => t.type === "page")?.webSocketDebuggerUrl;
  } catch { /* chưa lên */ }
  if (!wsUrl) await sleep(300);
}
const ws = new WebSocket(wsUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pend = new Map();
/* LỖI TRANG gom từ đầu phiên. Bản đầu của script này KHÔNG gom, nên khi gặp
   một lượt `#root` rỗng suốt 60 s nó chỉ biết "kẹt" mà không biết vì sao —
   một chẩn đoán dừng ngay trước câu hỏi quan trọng nhất. */
let loiTrang = [];
const loiMang = [];
ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.method === "Runtime.exceptionThrown") {
    loiTrang.push(String(m.params?.exceptionDetails?.exception?.description
      ?? m.params?.exceptionDetails?.text ?? "?").split("\n").slice(0, 3).join(" ⏎ "));
  }
  if (m.method === "Runtime.consoleAPICalled"
      && ["error", "warning"].includes(m.params?.type)) {
    loiTrang.push(`${m.params.type}: ` + (m.params.args ?? [])
      .map((a) => String(a.value ?? a.description ?? "")).join(" ").slice(0, 300));
  }
  if (m.method === "Network.loadingFailed") {
    loiMang.push(`${m.params?.type} ${m.params?.errorText}`);
  }
  if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); }
};
const send = (M, p = {}) => new Promise((res) => {
  const i = ++id; pend.set(i, res);
  ws.send(JSON.stringify({ id: i, method: M, params: p }));
});
const ev = async (x) => (await send("Runtime.evaluate",
  { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;

await send("Page.enable"); await send("Runtime.enable"); await send("Network.enable");
await send("Emulation.setDeviceMetricsOverride",
  { width: 1600, height: 900, deviceScaleFactor: 2, mobile: false });

const U = {
  status: "unsupported", failure_category: "out_of_scope",
  error_code: "gate_out_of_scope", reason: "ngoài phạm vi",
  learner_reason: "Hệ thống này mô phỏng HÌNH HỌC KHÔNG GIAN (Toán 11–12).",
};

const ket = [];
for (let i = 1; i <= LAN; i++) {
  const t0 = Date.now();
  loiTrang = [];
  await send("Page.navigate", { url: BASE });

  /* ① Bao lâu tới khi TRANG dựng xong (textarea của màn nhập đề là dấu hiệu)?
     ⚠️ KIÊN NHẪN 60 s, không phải 12 s. Phân biệt *chậm* với *kẹt* là toàn bộ
     việc của script này, và một cửa sổ chờ ngắn sẽ trả lời "kẹt" cho cả hai —
     tức tự dựng ra kết luận nhánh A mà không có quyền. */
  let tTrang = null;
  const dauVet = [];
  for (let k = 0; k < 600 && tTrang === null; k++) {
    const co = await ev(`!!document.querySelector('textarea')`);
    if (co) { tTrang = Date.now() - t0; break; }
    if (k === 0 || k === 30 || k === 100 || k === 300) {
      dauVet.push(await ev(`JSON.stringify({t:Date.now(),
        readyState:document.readyState, url:location.href,
        rootCon:(document.getElementById('root')?.children.length ?? -1),
        bodyLen:(document.body?.innerText||'').length})`));
    }
    await sleep(100);
  }

  // ② Nạp trạng thái từ chối ĐÚNG cách bộ kiểm đang làm.
  const tNap0 = Date.now();
  const nap = await ev(`(async()=>{const m=await import('/src/state/store.ts');
    m.useAppStore.getState().loadUnsupported(${JSON.stringify(U)}); return 'ok';})()`);

  // ③ Bao lâu tới khi THẺ TỪ CHỐI hiện ra?
  let tThe = null;
  for (let k = 0; k < 120 && tThe === null; k++) {
    const co = await ev(
      `(document.querySelector('.eyebrow')?.textContent||'').trim().length>0`);
    if (co) tThe = Date.now() - tNap0;
    else await sleep(100);
  }

  const truot = tTrang === null || tTrang > NGU_SAU_NAVIGATE
    || tThe === null || tThe > NGU_SAU_NAP_STATE;

  const nhan = await ev(`(document.querySelector('.eyebrow')?.textContent||'').trim()`);
  ket.push({
    lan: i, nap,
    ms_toi_khi_trang_dung: tTrang,
    ms_toi_khi_the_hien: tThe,
    the_co_hien_ra_khong: tThe !== null,
    nhan_cuoi_cung: nhan,
    moc_bo_kiem_se_truot: truot,
    loi_trang: loiTrang.slice(0,8),
    loi_mang: loiMang.slice(-5),
    dau_vet_khi_cho: dauVet.map((x) => { try { return JSON.parse(x); } catch { return x; } }),
  });
  console.log(`  lần ${String(i).padStart(2)} · trang ${tTrang ?? "KHÔNG"} ms `
    + `· thẻ ${tThe ?? "KHÔNG"} ms · ${truot ? "TRƯỢT mốc bộ kiểm" : "kịp"}`
    + ` · nhãn="${nhan}"`);

  if (truot) {
    const a = await send("Page.captureScreenshot", { format: "png" });
    writeFileSync(join(ANH, `truot-lan-${i}.png`),
      Buffer.from(a.result.data, "base64"));
  }
}

const hienDuoc = ket.filter((k) => k.the_co_hien_ra_khong).length;
const truot = ket.filter((k) => k.moc_bo_kiem_se_truot).length;
const tTrangs = ket.map((k) => k.ms_toi_khi_trang_dung).filter((x) => x !== null);
const tThes = ket.map((k) => k.ms_toi_khi_the_hien).filter((x) => x !== null);

const tom = {
  khai: "Chẩn đoán flake `certify-refusal-surface.mjs`. Không phải cổng nghiệm thu.",
  ITERATIONS: LAN,
  moc_bo_kiem_hien_tai: { sau_navigate_ms: NGU_SAU_NAVIGATE,
                          sau_nap_state_ms: NGU_SAU_NAP_STATE },
  THE_HIEN_RA_DUOC: `${hienDuoc}/${LAN}`,
  SO_LAN_TRUOT_MOC: truot,
  ms_toi_khi_trang_dung: { min: Math.min(...tTrangs), max: Math.max(...tTrangs),
                           tat_ca: tTrangs },
  ms_toi_khi_the_hien: { min: Math.min(...tThes), max: Math.max(...tThes),
                         tat_ca: tThes },
  PHAN_XU: hienDuoc === LAN
    ? "NHÁNH B — thẻ LUÔN hiện ra; chỉ là muộn hơn khoảng ngủ cố định của bộ kiểm"
    : "NHÁNH A — có lần thẻ KHÔNG BAO GIỜ hiện; lỗi trạng thái sản phẩm",
  chi_tiet: ket,
};
writeFileSync(join(OUT, "FLAKE_DIAGNOSIS.json"),
  JSON.stringify(tom, null, 1), "utf8");

console.log(`\n  THẺ HIỆN RA ĐƯỢC ${hienDuoc}/${LAN} · TRƯỢT MỐC ${truot}/${LAN}`);
console.log(`  trang dựng: ${Math.min(...tTrangs)}–${Math.max(...tTrangs)} ms `
  + `(mốc bộ kiểm ${NGU_SAU_NAVIGATE})`);
console.log(`  thẻ hiện  : ${Math.min(...tThes)}–${Math.max(...tThes)} ms `
  + `(mốc bộ kiểm ${NGU_SAU_NAP_STATE})`);
console.log(`  ⇒ ${tom.PHAN_XU}`);

ws.close(); proc.kill();
