/**
 * measure-page-boot.mjs — TRANG CÓ DỰNG ĐƯỢC KHÔNG, và bao lâu.
 *
 * ─── VÌ SAO TÁCH RA KHỎI MỌI CỔNG NGHIỆM THU ──────────────────────────────
 *
 * `certify-refusal-surface.mjs` cho `17–19/21` và mỗi lần đỏ đều là *"nhãn
 * rỗng"* — đọc như một lỗi NỘI DUNG. Chẩn đoán cho thấy nó không phải: trang
 * **chưa từng dựng**, `#root` rỗng suốt 60 giây, `readyState = complete`, và
 * nhật ký mạng ghi `Script net::ERR_CONNECTION_REFUSED` +
 * `net::ERR_NETWORK_ACCESS_DENIED`. Tức JS chưa bao giờ tới nơi.
 *
 * Một cổng báo "nhãn sai" cho một trang chưa tải là cổng nói dối về LOẠI lỗi —
 * và đó là lỗi tệ hơn cả chập chờn, vì nó đẩy người đọc đi sửa nhầm chỗ.
 *
 * Script này đo đúng một đại lượng, trên hai máy chủ, để so:
 *   • Vite dev (`:3000`) — mỗi module một request HTTP, hàng trăm request
 *   • bản dựng sản phẩm (`vite preview`) — vài tệp tĩnh đã gộp
 *
 * Và trả lời thêm một câu cần cho bản vá: **tải lại có cứu được không.**
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const FE = fileURLToPath(new URL("..", import.meta.url));
const GOC = resolve(FE, "..");
const OUT = join(GOC, "docs", "evaluation", "geometry", "final-system-release");
mkdirSync(OUT, { recursive: true });

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const arg = (n, d) => {
  const i = process.argv.indexOf(`--${n}`);
  return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : d;
};
const LAN = Number(arg("iters", "15"));
const KIEN_NHAN_MS = Number(arg("patience", "15000"));

async function moChrome() {
  const port = 9400 + Math.floor(Math.random() * 400);
  const dir = mkdtempSync(join(tmpdir(), "boot-"));
  const proc = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${port}`,
    `--user-data-dir=${dir}`, "--window-size=1600,900", "--hide-scrollbars",
    "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
    "about:blank"], { stdio: "ignore" });
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
  let id = 0; const pend = new Map(); let loiMang = [];
  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    if (m.method === "Network.loadingFailed" && m.params?.type === "Script") {
      loiMang.push(String(m.params?.errorText));
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
  return { send, ev, close: () => { ws.close(); proc.kill(); },
           loi: () => loiMang, reset: () => { loiMang = []; } };
}

/** Chờ tới khi trang DỰNG XONG. `null` = quá kiên nhẫn vẫn chưa dựng. */
async function choTrang(s, tran = KIEN_NHAN_MS) {
  const t0 = Date.now();
  while (Date.now() - t0 < tran) {
    if (await s.ev(`!!document.querySelector('textarea')`)) return Date.now() - t0;
    await sleep(100);
  }
  return null;
}

async function doMotMayChu(base) {
  const s = await moChrome();
  const ket = [];
  for (let i = 1; i <= LAN; i++) {
    s.reset();
    await s.send("Page.navigate", { url: base });
    const t = await choTrang(s);
    let cuuDuocBangTaiLai = null;
    if (t === null) {
      // Câu hỏi cho bản vá: một lần TẢI LẠI có gỡ được không?
      await s.send("Page.reload", { ignoreCache: false });
      cuuDuocBangTaiLai = (await choTrang(s)) !== null;
    }
    ket.push({ lan: i, ms: t, dung_duoc: t !== null,
               loi_script: [...new Set(s.loi())].slice(0, 4),
               cuu_duoc_bang_tai_lai: cuuDuocBangTaiLai });
    console.log(`    lần ${String(i).padStart(2)} · `
      + (t === null ? `KẸT — tải lại ${cuuDuocBangTaiLai ? "CỨU ĐƯỢC" : "vẫn kẹt"}`
                    : `${t} ms`)
      + (s.loi().length ? ` · script lỗi: ${[...new Set(s.loi())].join(",")}` : ""));
  }
  s.close();
  const ok = ket.filter((k) => k.dung_duoc).length;
  const ms = ket.filter((k) => k.ms !== null).map((k) => k.ms);
  return {
    base, ITERATIONS: LAN, BOOT_OK: ok, BOOT_FAIL: LAN - ok,
    BOOT_FAIL_RATE: Number(((LAN - ok) / LAN).toFixed(4)),
    CUU_DUOC_BANG_TAI_LAI: ket.filter((k) => k.cuu_duoc_bang_tai_lai === true).length,
    VAN_KET_SAU_TAI_LAI: ket.filter((k) => k.cuu_duoc_bang_tai_lai === false).length,
    ms_min: ms.length ? Math.min(...ms) : null,
    ms_max: ms.length ? Math.max(...ms) : null,
    chi_tiet: ket,
  };
}

const bang = {};
for (const [ten, base] of [["vite_dev", arg("dev", "http://localhost:3000")],
                           ["ban_dung_san_pham", arg("preview", "http://localhost:4173")]]) {
  console.log(`\n  ${ten} · ${base}`);
  bang[ten] = await doMotMayChu(base);
}

const tom = {
  khai: "Trang có dựng được không, đo trên HAI máy chủ. Không phải cổng nghiệm thu.",
  KIEN_NHAN_MS,
  ...bang,
  KET_LUAN: bang.vite_dev.BOOT_FAIL > 0 && bang.ban_dung_san_pham.BOOT_FAIL === 0
    ? "Lỗi nằm ở TRANSPORT của Vite dev dưới headless Chrome, không ở sản phẩm: "
      + "bản dựng sản phẩm dựng được 100%."
    : "Chưa tách bạch được — xem chi tiết.",
};
writeFileSync(join(OUT, "PAGE_BOOT_MEASUREMENT.json"),
  JSON.stringify(tom, null, 1), "utf8");

console.log(`\n  vite dev        : kẹt ${bang.vite_dev.BOOT_FAIL}/${LAN}`
  + ` · tải lại cứu được ${bang.vite_dev.CUU_DUOC_BANG_TAI_LAI}`);
console.log(`  bản dựng sản phẩm: kẹt ${bang.ban_dung_san_pham.BOOT_FAIL}/${LAN}`);
console.log(`  ⇒ ${tom.KET_LUAN}`);
