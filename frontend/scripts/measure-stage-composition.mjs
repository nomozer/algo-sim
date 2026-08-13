/**
 * measure-stage-composition.mjs — BỐ CỤC SÂN KHẤU CHO **MỌI** TARGET.
 *
 * Trả lời một câu duy nhất, bằng số: *"nội dung mô phỏng có bị trôi trong một
 * thẻ quá rộng không, và các thành phần trong thẻ có men theo cùng một đường
 * rail dọc không?"*
 *
 * Ba con số cho mỗi target:
 *   fillPct  — bề rộng MỰC (hộp bao của nội dung sân khấu) / bề rộng thẻ;
 *   skew     — |lề trái − lề phải| của mực trong thẻ; lệch = bị dồn một bên;
 *   railSpan — khoảng cách giữa mép trái TRÁI NHẤT và PHẢI NHẤT của các thành
 *              phần văn bản (tiêu đề · chú giải · thuyết minh) so với mực.
 *              Lớn = mắt phải nhảy giữa hai hệ căn lề trong cùng một thẻ.
 *
 * `measure-dag-composition.mjs` chỉ đo được `logic.boolean_dag` (nó hỏi
 * `.dag-stage`). File này đo được mọi target vì nó lấy hộp bao từ CHÍNH các
 * phần tử con của sân khấu, không hỏi tên lớp riêng của miền nào.
 *
 * ⚠️ Kiểm danh tính backend trước: container Docker cũ chiếm cổng 8000 thì
 * trang không nạp được mẫu và mọi số đo thành vô nghĩa.
 */
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const OUT = resolve(argOf("--out",
  new URL("../../docs/evaluation/m18/stage-composition.json", import.meta.url)
    .pathname.replace(/^[/]/, "")));
mkdirSync(dirname(OUT), { recursive: true });
const TARGETS = argOf("--targets", "").split(",").filter(Boolean);
const VIEWPORTS = argOf("--viewports", "1920,1366").split(",").map(Number);

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const RESOLVE = `(()=>{const pick=(s)=>{const h=performance.getEntriesByType('resource').map(e=>e.name).filter(n=>n.includes(s));
 return h.length?h[h.length-1]:new URL(s,location.origin).href;};
 return JSON.stringify({store:pick('/src/state/store.ts'),catalog:pick('/src/data/offline-catalog.ts'),
 registry:pick('/src/simulations/registry.ts'),sims:pick('/src/simulations/index.ts')});})()`;

/* Hộp bao của MỰC — chỉ đếm phần tử THỰC SỰ VẼ.
 *
 * ⚠️ Bản đầu duyệt `querySelectorAll('*')` và lấy min-left/max-right của mọi
 * phần tử ≥4px. Các div BỌC (`.sim-stage`, `.stack`) rộng bằng thẻ, nên mọi
 * target đều ra "lấp 99.9%, lệch 0" — tức phép đo báo SẠCH cho đúng cái bố cục
 * đang bị kêu. Đo container, không đo mực.
 *
 * Nay chỉ tính: `<svg>` (một hình, lấy hộp của chính nó, không chui vào trong),
 * và phần tử LÁ (không có con) mà thật sự có sơn — nền không trong suốt, có
 * viền, hoặc có chữ. Div bọc không có sơn nên tự rơi ra ngoài. */
const MEASURE = `(()=>{
  const card = document.querySelector('.workspace-card');
  if (!card) return JSON.stringify({error:'không thấy .workspace-card'});
  /* ĐỒ ĐẠC CỦA THẺ, không phải sân khấu: tiêu đề, chú giải, thuyết minh, và
     các bảng tra cứu gập được (thẻ details). Bản trước đếm cả bảng "Chi tiết các
     cổng" nên 'boolean_dag' báo lệch 558px trong khi sơ đồ của nó đã căn giữa
     đúng 0px — phép đo tự bịa ra một lỗi không có. */
  const TEXT = ['.workspace-header','.stage-legend','.narration-bar','.stage-affordance',
                '.notes','details','.gate-detail','.data-table','.param-bar'];
  const isText = (el) => TEXT.some(s => el.closest(s));
  const paints = (el) => {
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') return false;
    const bg = cs.backgroundColor;
    const hasBg = bg && bg !== 'transparent' && !/rgba\(0,\s*0,\s*0,\s*0\)/.test(bg);
    const hasBorder = parseFloat(cs.borderTopWidth) > 0 || parseFloat(cs.borderLeftWidth) > 0;
    const hasText = el.textContent && el.textContent.trim().length > 0;
    return hasBg || hasBorder || hasText;
  };
  let L = Infinity, R = -Infinity, n = 0;
  for (const el of card.querySelectorAll('svg, *')) {
    if (isText(el)) continue;
    if (el.closest('svg') && el.tagName.toLowerCase() !== 'svg') continue; // chỉ hộp của svg
    if (el.tagName.toLowerCase() !== 'svg' && el.children.length > 0) continue; // bỏ div bọc
    if (el.tagName.toLowerCase() !== 'svg' && !paints(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    L = Math.min(L, r.left); R = Math.max(R, r.right); n += 1;
  }
  const cb = card.getBoundingClientRect();
  const textLefts = TEXT.map(s => {
    const el = card.querySelector(s);
    return el ? Math.round(el.getBoundingClientRect().left) : null;
  }).filter(x => x !== null);
  const cs = getComputedStyle(card);
  const padL = parseFloat(cs.paddingLeft) || 0, padR = parseFloat(cs.paddingRight) || 0;
  const innerL = cb.left + padL, innerR = cb.right - padR;
  return JSON.stringify({
    card: {x: Math.round(cb.left), w: Math.round(cb.width)},
    inner: {w: Math.round(innerR - innerL)},
    ink: L === Infinity ? null : {x: Math.round(L), w: Math.round(R - L)},
    inkNodes: n,
    gutterLeft: L === Infinity ? null : Math.round(L - innerL),
    gutterRight: R === -Infinity ? null : Math.round(innerR - R),
    textLefts,
    overflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth,
  });
})()`;

const probe = await fetch("http://localhost:8000/api/health").catch(() => null);
if (!probe) console.warn("(cảnh báo: :8000 không trả lời — mẫu offline vẫn chạy được)");

const rows = [];
for (const w of VIEWPORTS) {
  const cdp = 9900 + Math.floor(Math.random() * 90);
  const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu",
    `--remote-debugging-port=${cdp}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "comp-"))}`,
    `--window-size=${w},900`, "--hide-scrollbars", "about:blank"], { stdio: "ignore" });
  let url;
  for (let i = 0; i < 40 && !url; i++) {
    try { const l = await (await fetch(`http://127.0.0.1:${cdp}/json/list`)).json();
      url = l.find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch { /* chưa lên */ }
    if (!url) await sleep(250);
  }
  const ws = new WebSocket(url); await new Promise((r) => (ws.onopen = r));
  let id = 0; const pend = new Map();
  ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } };
  const send = (m, p = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  const ev = async (x) => (await send("Runtime.evaluate",
    { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;

  await send("Page.enable"); await send("Runtime.enable");
  await send("Page.navigate", { url: "http://localhost:3000" });
  await sleep(3200);
  const u = JSON.parse(await ev(RESOLVE));
  await ev(`(async()=>{${Object.values(u).map((x) => `await import(${JSON.stringify(x)});`).join("")}return 1})()`);

  const list = TARGETS.length ? TARGETS : JSON.parse(await ev(`(async()=>{
    const c=await import(${JSON.stringify(u.catalog)});
    return JSON.stringify([...new Set(c.offlineCatalog().map(e=>e.simId))]);})()`));

  console.log(`\n━━ ${w}px`);
  for (const sim of list) {
    const ok = await ev(`(async()=>{
      const s=await import(${JSON.stringify(u.store)});const c=await import(${JSON.stringify(u.catalog)});
      const rg=await import(${JSON.stringify(u.sims)});const reg=await import(${JSON.stringify(u.registry)});
      if(reg.listSimulations().length===0) rg.registerAllSimulations();
      s.useAppStore.getState().reset();
      const e=c.offlineCatalog().find(x=>x.simId===${JSON.stringify(sim)});
      if(!e) return 'không có mẫu';
      try { s.useAppStore.getState().loadEnvelope(e.envelope); }
      catch (err) { return 'nạp lỗi: ' + String(err); }
      return s.useAppStore.getState().active ? 'ok' : 'nạp không ra active';})()`);
    if (ok !== "ok") { console.log(`  ${sim.padEnd(34)} ${ok ?? "(không trả lời)"}`); continue; }
    await sleep(700);
    const m = JSON.parse(await ev(MEASURE));
    if (m.error || !m.ink) { console.log(`  ${sim.padEnd(34)} ${m.error ?? "không đo được mực"}`); continue; }
    const fill = +((m.ink.w / m.inner.w) * 100).toFixed(1);
    const skew = Math.abs(m.gutterLeft - m.gutterRight);
    // Chữ có men theo mép MỰC không? (0 = cùng một rail)
    const railSpan = m.textLefts.length
      ? Math.round(Math.max(...m.textLefts.map((x) => Math.abs(x - m.ink.x)))) : null;
    rows.push({ viewport: w, target: sim, cardW: m.card.w, innerW: m.inner.w,
      inkW: m.ink.w, fillPct: fill, gutterLeft: m.gutterLeft, gutterRight: m.gutterRight,
      skew, railSpan, overflowX: m.overflowX });
    console.log(`  ${sim.padEnd(34)} thẻ ${String(m.inner.w).padStart(4)} · mực ${String(m.ink.w).padStart(4)}`
      + ` · lấp ${String(fill).padStart(5)}% · lệch ${String(skew).padStart(4)} · rail ${String(railSpan).padStart(4)}`);
  }
  chrome.kill();
}

writeFileSync(OUT, JSON.stringify({ when: new Date().toISOString(), rows }, null, 2));
console.log(`\n→ ${OUT}`);
