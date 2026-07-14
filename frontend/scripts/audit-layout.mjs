/**
 * audit-layout.mjs — SOÁT BỐ CỤC TRÊN BROWSER THẬT (M9-UX7)
 *
 * VÌ SAO CẦN: mắt người nhìn ra "hơi lệch", không nhìn ra "token không tồn tại nên
 * trình duyệt vứt cả dòng margin". Bug `var(--sp-2xl)` (M9-UX5) trôi im từ M9-UX1
 * qua bốn milestone — không test nào bắt được, vì CSS KHÔNG CHẠY trong vitest.
 * Chỉ khi ĐO `getBoundingClientRect` trong Chrome thật nó mới lộ ra.
 *
 * Công cụ này đo 5 thứ, trên từng route:
 *   1. ICON LỆCH   — tâm dọc của <svg class="icon"> so với tâm dòng chữ cạnh nó.
 *   2. CHỮ BỊ CẮT  — scrollWidth > clientWidth mà không khai overflow (chữ mất).
 *   3. ĐÈ NHAU     — hai phần tử anh em có hình chữ nhật giao nhau.
 *   4. TRÀN NGANG  — con rộng hơn cha (vỡ bố cục).
 *   5. KHOẢNG LẺ   — gap/margin/padding không nằm trên thang 4px của tokens.
 *
 * Chạy:  node scripts/audit-layout.mjs            (cần `npm run dev` đang chạy)
 *        node scripts/audit-layout.mjs --port 5174
 */

import { spawn } from "node:child_process";
import { existsSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const args = process.argv.slice(2);
const argOf = (name, dflt) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : dflt;
};
const APP = `http://localhost:${argOf("--port", "5173")}`;
const CDP_PORT = 9333;

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].find(existsSync);

if (!CHROME) {
  console.error("Không tìm thấy Chrome.");
  process.exit(1);
}

/* ── Kịch bản: đi qua mọi mặt trình bày ─────────────────────────────────── */
const ROUTES = [
  { name: "Trang chủ", steps: [] },
  { name: "Thư viện", steps: [{ click: "Thư viện", sel: ".nav-link" }] },
  {
    name: "Workspace",
    steps: [
      { click: "Trang chủ", sel: ".nav-link" },
      { click: "cao nhất", sel: ".starter-card" },
      { click: null, sel: 'button[title="Tiến một bước"]', times: 3 },
    ],
  },
  { name: "Lịch sử", steps: [{ click: "Lịch sử", sel: ".nav-link" }] },
];

/* ── Đoạn mã ĐO, chạy trong trang ───────────────────────────────────────── */
const PROBE = String.raw`
(() => {
  const SCALE = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 20, 24, 28, 32, 48, 64];
  const px = (v) => Math.round(parseFloat(v) || 0);
  const seen = (el) => {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== "hidden" && cs.display !== "none";
  };
  const name = (el) => {
    const cls = (el.className && typeof el.className === "string" ? el.className : "")
      .split(" ").filter(Boolean).slice(0, 2).join(".");
    return el.tagName.toLowerCase() + (cls ? "." + cls : "");
  };

  const out = { icon: [], clip: [], overlap: [], overflow: [], spacing: [] };

  /* 1 — ICON LỆCH: tâm dọc icon vs tâm dọc của phần tử chứa nó */
  for (const svg of document.querySelectorAll("svg.icon")) {
    if (!seen(svg)) continue;
    const host = svg.parentElement;
    if (!host || !seen(host)) continue;
    const cs = getComputedStyle(host);
    // chỉ xét khi icon nằm CẠNH chữ (host có text thật)
    const text = (host.textContent || "").trim();
    if (!text) continue;
    const hr = host.getBoundingClientRect();
    const sr = svg.getBoundingClientRect();
    const padTop = px(cs.paddingTop), padBot = px(cs.paddingBottom);
    const inner = { top: hr.top + padTop, bottom: hr.bottom - padBot };
    const hostMid = (inner.top + inner.bottom) / 2;
    const iconMid = (sr.top + sr.bottom) / 2;
    const off = Math.round(Math.abs(hostMid - iconMid) * 10) / 10;
    // host nhiều dòng thì tâm không phải chuẩn đúng — bỏ qua
    const lineH = px(cs.lineHeight) || 20;
    const multiline = (inner.bottom - inner.top) > lineH * 1.6;
    if (!multiline && off > 2) {
      out.icon.push(name(host) + " — icon lệch " + off + "px so với tâm chữ");
    }
  }

  /* 2 — CHỮ BỊ CẮT: nội dung rộng hơn khung mà không khai overflow */
  for (const el of document.querySelectorAll("body *")) {
    if (!seen(el)) continue;
    const cs = getComputedStyle(el);
    if (cs.overflowX !== "visible" || cs.textOverflow === "ellipsis") continue;
    if (el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0) {
      out.clip.push(name(el) + " — chữ bị cắt " + (el.scrollWidth - el.clientWidth) + "px");
    }
  }

  /* 3 — ĐÈ NHAU: hai anh em giao nhau (bỏ qua absolute/fixed và svg nội bộ) */
  for (const parent of document.querySelectorAll("main, header, section, div")) {
    const kids = [...parent.children].filter(
      (k) => seen(k) && !["absolute","fixed"].includes(getComputedStyle(k).position)
             && k.tagName !== "svg" && k.tagName !== "path",
    );
    for (let i = 0; i < kids.length; i++)
      for (let j = i + 1; j < kids.length; j++) {
        const a = kids[i].getBoundingClientRect(), b = kids[j].getBoundingClientRect();
        const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
        const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        if (ox > 2 && oy > 2) {
          out.overlap.push(name(kids[i]) + " ĐÈ " + name(kids[j]) +
            " (" + Math.round(ox) + "×" + Math.round(oy) + "px)");
        }
      }
  }

  /* 4 — TRÀN NGANG: con rộng hơn cha */
  for (const el of document.querySelectorAll("body *")) {
    if (!seen(el) || !el.parentElement) continue;
    const cs = getComputedStyle(el);
    if (["absolute","fixed"].includes(cs.position)) continue;
    const r = el.getBoundingClientRect(), p = el.parentElement.getBoundingClientRect();
    if (p.width === 0) continue;
    const over = Math.round(r.right - p.right);
    if (over > 2) out.overflow.push(name(el) + " — tràn khỏi cha " + over + "px");
  }

  /* 5 — KHOẢNG LẺ: gap/margin/padding ngoài thang 4px của tokens */
  for (const el of document.querySelectorAll("body *")) {
    if (!seen(el)) continue;
    const cs = getComputedStyle(el);
    for (const prop of ["rowGap","columnGap","marginTop","marginBottom","paddingTop","paddingBottom"]) {
      const v = cs[prop];
      if (!v || v === "normal") continue;
      const n = px(v);
      if (n > 0 && !SCALE.includes(n)) {
        out.spacing.push(name(el) + " — " + prop + ": " + n + "px (ngoài thang)");
      }
    }
  }

  const uniq = (a) => [...new Set(a)];
  return JSON.stringify({
    icon: uniq(out.icon), clip: uniq(out.clip), overlap: uniq(out.overlap),
    overflow: uniq(out.overflow), spacing: uniq(out.spacing),
  });
})()`;

/* ── CDP ────────────────────────────────────────────────────────────────── */
const profile = mkdtempSync(join(tmpdir(), "algosim-audit-"));
const chrome = spawn(
  CHROME,
  [
    "--headless=new",
    "--disable-gpu",
    `--remote-debugging-port=${CDP_PORT}`,
    `--user-data-dir=${profile}`,
    "--window-size=1600,1000",
    "about:blank",
  ],
  { stdio: "ignore" },
);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function connect() {
  for (let i = 0; i < 40; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`)).json();
      const page = list.find((t) => t.type === "page");
      if (page) return page.webSocketDebuggerUrl;
    } catch {
      /* chưa lên */
    }
    await sleep(250);
  }
  throw new Error("Chrome không mở được cổng debug.");
}

const wsUrl = await connect();
const ws = new WebSocket(wsUrl);
await new Promise((r) => (ws.onopen = r));

let id = 0;
const pending = new Map();
ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) {
    pending.get(m.id)(m);
    pending.delete(m.id);
  }
};
const send = (method, params = {}) =>
  new Promise((res) => {
    const i = ++id;
    pending.set(i, res);
    ws.send(JSON.stringify({ id: i, method, params }));
  });
const evaluate = async (expr) => {
  const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true });
  if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails).slice(0, 300));
  return r.result?.result?.value;
};

await send("Page.enable");
await send("Runtime.enable");

const LABELS = {
  icon: "ICON LỆCH TÂM",
  clip: "CHỮ BỊ CẮT",
  overlap: "PHẦN TỬ ĐÈ NHAU",
  overflow: "TRÀN KHỎI KHUNG CHA",
  spacing: "KHOẢNG CÁCH NGOÀI THANG 4px",
};

let total = 0;

for (const route of ROUTES) {
  await send("Page.navigate", { url: APP });
  await sleep(1400);

  for (const step of route.steps) {
    const times = step.times ?? 1;
    for (let k = 0; k < times; k++) {
      await evaluate(`(() => {
        const els = [...document.querySelectorAll(${JSON.stringify(step.sel)})];
        const el = ${step.click === null ? "els[0]" : `els.find(e => e.textContent.includes(${JSON.stringify(step.click)}))`};
        if (el) el.click();
        return !!el;
      })()`);
      await sleep(450);
    }
  }
  await sleep(400);

  /* DẤU VÂN TAY: chứng minh ta đo ĐÚNG TRANG. Một bản soát "sạch" vì đo nhầm
     trang thì vô giá trị — đúng loại lỗi guard-SSR đã mắc (anti-pattern #13). */
  const fingerprint = await evaluate(`(() => {
    const q = (s) => !!document.querySelector(s);
    if (q(".app-layout")) return "workspace";
    if (q(".library-view")) return "library";
    if (q(".history-view")) return "history";
    if (q(".home-view")) return "home";
    return "UNKNOWN";
  })()`);
  const EXPECT = { "Trang chủ": "home", "Thư viện": "library", Workspace: "workspace", "Lịch sử": "history" };
  if (fingerprint !== EXPECT[route.name]) {
    console.error(
      `
✖ KHÔNG TỚI ĐƯỢC "${route.name}" — đang ở "${fingerprint}". Bản soát này KHÔNG hợp lệ.`,
    );
    ws.close();
    chrome.kill();
    process.exit(2);
  }

  const found = JSON.parse(await evaluate(PROBE));
  const count = Object.values(found).reduce((a, b) => a + b.length, 0);
  total += count;

  console.log(`\n━━ ${route.name} ${count === 0 ? "✔ sạch" : `— ${count} vấn đề`}`);
  for (const [key, label] of Object.entries(LABELS)) {
    if (!found[key].length) continue;
    console.log(`  ${label}:`);
    for (const line of found[key].slice(0, 12)) console.log(`    · ${line}`);
    if (found[key].length > 12) console.log(`    · … và ${found[key].length - 12} nữa`);
  }
}

console.log(`\n${total === 0 ? "✔ TẤT CẢ SẠCH" : `✖ TỔNG: ${total} vấn đề bố cục`}`);

ws.close();
chrome.kill();
process.exit(total === 0 ? 0 : 1);
