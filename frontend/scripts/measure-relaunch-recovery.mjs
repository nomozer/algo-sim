/**
 * measure-relaunch-recovery.mjs — PHIÊN CHROME MỚI CÓ GỠ ĐƯỢC KHÔNG?
 *
 * Đã đo được: ~13% phiên headless Chrome **không tải nổi** module từ Vite dev
 * (`ERR_CONNECTION_REFUSED` / `ERR_NETWORK_ACCESS_DENIED`), và **tải lại trong
 * cùng phiên KHÔNG cứu được** (0/2). Câu còn lại, và nó quyết định bản vá:
 *
 *     hỏng là thuộc tính của PHIÊN hay của thời điểm?
 *
 * Thuộc PHIÊN ⇒ mở một Chrome MỚI là gỡ được, và một lần mở lại **có đếm, có
 * báo riêng** là bản vá đúng mực. Thuộc THỜI ĐIỂM ⇒ mở lại cũng vô ích và
 * không được phép giả vờ rằng có.
 *
 * ⚠️ Số lần mở lại được ĐẾM và báo riêng (`§8`), không bao giờ gộp vào số lượt
 * đạt. Đây là phép đo, không phải cách làm đẹp kết quả.
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
const LAN = Number(arg("iters", "20"));
const BASE = arg("base", "http://localhost:3000");
const TRAN = 8000;

async function mo() {
  const port = 9100 + Math.floor(Math.random() * 250);
  const dir = mkdtempSync(join(tmpdir(), "relaunch-"));
  const proc = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${port}`,
    `--user-data-dir=${dir}`, "--window-size=1440,900", "--hide-scrollbars",
    "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
    "about:blank"], { stdio: "ignore" });
  let wsUrl;
  for (let i = 0; i < 80 && !wsUrl; i++) {
    try {
      wsUrl = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json())
        .find((t) => t.type === "page")?.webSocketDebuggerUrl;
    } catch { /* chưa lên */ }
    if (!wsUrl) await sleep(250);
  }
  const ws = new WebSocket(wsUrl);
  await new Promise((r) => (ws.onopen = r));
  let id = 0; const pend = new Map();
  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); }
  };
  const send = (M, p = {}) => new Promise((res) => {
    const i = ++id; pend.set(i, res);
    ws.send(JSON.stringify({ id: i, method: M, params: p }));
  });
  const ev = async (x) => (await send("Runtime.evaluate",
    { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
  await send("Page.enable"); await send("Runtime.enable");
  return { send, ev, dong: () => { ws.close(); proc.kill(); } };
}

async function thuMotPhien() {
  const s = await mo();
  await s.send("Page.navigate", { url: BASE });
  const t0 = Date.now();
  let ok = false;
  while (Date.now() - t0 < TRAN) {
    if (await s.ev(`!!document.querySelector('textarea')`)) { ok = true; break; }
    await sleep(100);
  }
  s.dong();
  return ok;
}

const ket = [];
for (let i = 1; i <= LAN; i++) {
  const lan1 = await thuMotPhien();
  let lan2 = null;
  if (!lan1) lan2 = await thuMotPhien();          // MỘT phiên mới, không hơn
  ket.push({ lan: i, phien_dau: lan1, phien_mo_lai: lan2 });
  console.log(`  lần ${String(i).padStart(2)} · phiên đầu ${lan1 ? "OK" : "HỎNG"}`
    + (lan2 === null ? "" : ` · mở lại ${lan2 ? "GỠ ĐƯỢC" : "vẫn hỏng"}`));
}

const hongLanDau = ket.filter((k) => !k.phien_dau).length;
const goDuoc = ket.filter((k) => k.phien_mo_lai === true).length;
const tom = {
  khai: "Phiên Chrome mới có gỡ được lỗi tải trang của Vite dev không.",
  base: BASE, ITERATIONS: LAN, TRAN_CHO_MS: TRAN,
  HONG_PHIEN_DAU: hongLanDau,
  TI_LE_HONG_PHIEN_DAU: Number((hongLanDau / LAN).toFixed(4)),
  MO_LAI_GO_DUOC: goDuoc,
  MO_LAI_VAN_HONG: ket.filter((k) => k.phien_mo_lai === false).length,
  KET_LUAN: hongLanDau === 0
    ? "Không tái hiện được trong lượt đo này."
    : (goDuoc === hongLanDau
      ? "Hỏng thuộc PHIÊN: mở một Chrome mới gỡ được 100% số ca hỏng."
      : "Mở lại KHÔNG gỡ hết — không được coi mở lại là cách chữa."),
  chi_tiet: ket,
};
writeFileSync(join(OUT, "RELAUNCH_RECOVERY.json"), JSON.stringify(tom, null, 1), "utf8");
console.log(`\n  hỏng phiên đầu ${hongLanDau}/${LAN} · mở lại gỡ được ${goDuoc}`);
console.log(`  ⇒ ${tom.KET_LUAN}`);
