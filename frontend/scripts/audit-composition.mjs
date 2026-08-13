/**
 * audit-composition.mjs — SOÁT BỐ CỤC DÙNG CHUNG CHO TOÀN DANH MỤC.
 *
 * Trả lời hai câu, cho mọi target, ở mọi bề rộng:
 *
 *   A. Cơ chế nhỏ có đang trôi trong một KHUNG rỗng quá khổ không?
 *   B. Hình và chữ của CÙNG một cơ chế có men theo cùng một đường rail không?
 *
 * ─── ĐỊNH NGHĨA "MỰC CÓ NGHĨA" (bắt buộc khai — §8) ───────────────────────
 *
 * Ba lần đo trước đều trả về SỐ mà vẫn sai, nên cách chọn hộp bao phải viết ra:
 *
 *   TÍNH   `<svg>` (lấy hộp của chính nó, KHÔNG chui vào trong), và phần tử LÁ
 *          (không có phần tử con) thật sự có sơn: nền không trong suốt, hoặc có
 *          viền, hoặc có chữ.
 *   BỎ     div BỌC (có con) — chúng rộng bằng thẻ nên nuốt mọi phép đo; đây
 *          chính là lỗi khiến bản đầu báo "lấp 99.9%, lệch 0" cho bố cục đang
 *          hỏng.
 *   BỎ     đồ đạc của THẺ, không thuộc cơ chế: tiêu đề bài, chú giải, thuyết
 *          minh, bảng tra cứu gập được, thanh tham số.
 *
 * Nói cách khác: mực = thứ VẼ RA CƠ CHẾ, không phải thứ chứa nó và không phải
 * chữ mô tả nó.
 *
 * ─── BỐN RAIL ────────────────────────────────────────────────────────────
 *
 * visual · instruction · legend · explanation. `maxRailDelta` là khoảng cách
 * lớn nhất giữa mép trái của mực và mép trái của từng khối chữ. 0 = một rail.
 *
 * ─── PHÁN QUYẾT ──────────────────────────────────────────────────────────
 *
 * KHÔNG chấm bằng `fillRatio` một mình (§10): 17% là ĐÚNG nếu khung cũng ôm sát
 * 17% ấy. Lỗi là 17% mực trong một khung rộng 100%. Nên phán quyết đọc
 * `frameFill` = mực / KHUNG, chứ không phải mực / thẻ.
 *
 * ⚠️ Backtick KHÔNG được xuất hiện trong biểu thức tiêm vào trang (template
 * literal) — đã làm Node báo SyntaxError ba lần trong repo này.
 */
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const OUT = resolve(argOf("--out",
  new URL("../../docs/evaluation/m19/composition.json", import.meta.url)
    .pathname.replace(/^[/]/, "")));
mkdirSync(dirname(OUT), { recursive: true });
const ONLY = argOf("--targets", "").split(",").filter(Boolean);
const VIEWPORTS = argOf("--viewports", "1920,1536,1366,768").split(",").map(Number);
const LABEL = argOf("--label", "");

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

const MEASURE = `(()=>{
  const card = document.querySelector('.workspace-card');
  if (!card) return JSON.stringify({error:'không thấy .workspace-card'});
  const frame = card.querySelector('.mechanism-frame') || card;

  const FURNITURE = ['.workspace-header','.stage-legend','.narration-bar',
                     '.stage-affordance','.notes','details','.gate-detail',
                     '.data-table','.param-bar','.prediction-bar'];
  const isFurniture = (el) => FURNITURE.some(s => el.closest(s));
  const paints = (el) => {
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') return false;
    const bg = cs.backgroundColor;
    const hasBg = bg && bg !== 'transparent' && bg !== 'rgba(0, 0, 0, 0)';
    const hasBorder = parseFloat(cs.borderTopWidth) > 0 || parseFloat(cs.borderLeftWidth) > 0;
    const hasText = el.textContent && el.textContent.trim().length > 0;
    return hasBg || hasBorder || hasText;
  };

  let L = Infinity, R = -Infinity, nodes = 0;
  for (const el of card.querySelectorAll('*')) {
    if (isFurniture(el)) continue;
    const tag = el.tagName.toLowerCase();
    if (el.closest('svg') && tag !== 'svg') continue;
    if (tag !== 'svg' && el.children.length > 0) continue;
    if (tag !== 'svg' && !paints(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    L = Math.min(L, r.left); R = Math.max(R, r.right); nodes += 1;
  }

  const leftOf = (sel) => {
    const el = card.querySelector(sel);
    return el ? Math.round(el.getBoundingClientRect().left) : null;
  };
  const box = (el) => { const r = el.getBoundingClientRect();
    return {x: Math.round(r.left), w: Math.round(r.width)}; };
  const inner = (el) => { const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
    return {x: Math.round(r.left + (parseFloat(cs.paddingLeft)||0)),
            w: Math.round(r.width - (parseFloat(cs.paddingLeft)||0) - (parseFloat(cs.paddingRight)||0))}; };

  /* KHẢ DỤNG = bề rộng lưới, KHÔNG phải cột. Sau khi cột co theo nội dung,
     '.panel-center' CHÍNH LÀ khung, nên lấy nó làm mẫu số biến "khung chiếm
     >90% sân khấu" thành luôn đúng và phán quyết A tự vô hiệu. */
  const stageEl = document.querySelector('.app-layout') || card.parentElement;
  /* Chữ CŨNG là nội dung cơ chế và nó có quyền quyết bề rộng khung (một câu
     thuyết minh dài hơn hình là chuyện bình thường). Nên mẫu số của "khung có
     rỗng không" phải là max(hình, khối chữ rộng nhất), không phải hình một mình. */
  let textW = 0;
  for (const sel of ['.stage-affordance','.narration-bar','.stage-legend','.workspace-header']) {
    const el = card.querySelector(sel);
    if (el) textW = Math.max(textW, Math.round(el.getBoundingClientRect().width));
  }
  const clipped = [...card.querySelectorAll('svg')].some(s => {
    const p = s.parentElement; if (!p) return false;
    return s.getBoundingClientRect().right > p.getBoundingClientRect().right + 1;
  });

  return JSON.stringify({
    stage: inner(stageEl),
    card: inner(card),
    frame: inner(frame),
    hasFrame: frame !== card,
    ink: L === Infinity ? null : {x: Math.round(L), w: Math.round(R - L)},
    inkNodes: nodes,
    textW,
    rails: {
      /* KHỐI tiêu đề, KHÔNG phải thẻ h2: tiêu đề nằm SAU huy hiệu miền trên
         cùng một dòng nên mép trái của nó thụt 60-79px một cách hợp lệ. Lấy h2
         làm rail khiến audit báo lệch ở gần như mọi target vì lý do sai. */
      instruction: leftOf('.stage-affordance') ?? leftOf('.workspace-header'),
      legend: leftOf('.stage-legend'),
      explanation: leftOf('.narration-bar'),
    },
    overflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    clipped,
  });
})()`;

/**
 * NGOẠI LỆ RAIL — §7 cho phép "documented mechanism-specific reason".
 *
 * Chỉ MỘT mục, và nó phải nói về CƠ CHẾ chứ không phải "renderer đang thế".
 * Thêm dòng ở đây = tự khai vừa nới một bất biến, nên phải giải trình.
 */
/**
 * NGOẠI LỆ KHUNG — §12/§13. Khung được phép BÁM CỬA SỔ nếu chính bề rộng khả
 * dụng là thứ cơ chế đang trình bày. Lý do phải nói về CƠ CHẾ; "renderer đang
 * để width:100%" KHÔNG phải lý do.
 */
const FRAME_EXCEPTIONS = {
  "web.style_model":
    "Sân khấu là một TRANG WEB trong khung xem trước. Bề rộng khả dụng chính " +
    "là thứ trang phải lấp — đó là hành vi đang được dạy, không phải khoảng " +
    "trống thừa. Khung chia đôi (điều khiển trái · xem trước phải) cũng cần bề " +
    "ngang để hai vế 'giá trị em đặt ↔ kết quả nhìn thấy' nằm cùng tầm mắt " +
    "(§13). Đây là ngoại lệ DUY NHẤT của luật khung-không-bám-cửa-sổ.",
};

const RAIL_EXCEPTIONS = {
  "logic.boolean_dag":
    "Chú giải tín hiệu đặt CẠNH sơ đồ, không đặt dưới: sơ đồ mạch có bề rộng " +
    "cố định do bố cục mạch quyết định (không co giãn), nên ở màn rộng nó luôn " +
    "ngắn hơn khung. Đặt chú giải bên phải lấp đúng dải trống ấy và rút ngắn " +
    "sân khấu một hàng — đo được ở W4B-4D: lệch lề 0px ở cả bốn bề rộng. " +
    "Đặt chú giải xuống dưới sẽ trả lại khoảng trống bên phải.",
};

const rows = [];
for (const w of VIEWPORTS) {
  const cdp = 9300 + Math.floor(Math.random() * 400);
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
  /* Nổi LỖI lên thay vì trả undefined: bản trước im lặng, nên bốn target hỏng
     bị in ra là "(không trả lời)" và người đọc tưởng là thiếu mẫu. */
  const ev = async (x) => {
    const r = await send("Runtime.evaluate",
      { expression: x, awaitPromise: true, returnByValue: true });
    const ex = r.result?.exceptionDetails;
    if (ex) return "LỖI: " + String(ex.exception?.description ?? ex.text ?? "?").split(String.fromCharCode(10))[0];
    return r.result?.result?.value;
  };

  await send("Page.enable"); await send("Runtime.enable");
  await send("Page.navigate", { url: "http://localhost:3000" });
  await sleep(3200);
  const u = JSON.parse(await ev(RESOLVE));
  await ev(`(async()=>{${Object.values(u).map((x) => `await import(${JSON.stringify(x)});`).join("")}return 1})()`);

  const list = ONLY.length ? ONLY : JSON.parse(await ev(`(async()=>{
    const c=await import(${JSON.stringify(u.catalog)});
    return JSON.stringify([...new Set(c.offlineCatalog().map(e=>e.simId))].sort());})()`));

  console.log(`\n━━ ${w}px${LABEL ? "  [" + LABEL + "]" : ""}`);
  const loadOne = (sim) => ev(`(async()=>{
    const s=await import(${JSON.stringify(u.store)});const c=await import(${JSON.stringify(u.catalog)});
    const rg=await import(${JSON.stringify(u.sims)});const reg=await import(${JSON.stringify(u.registry)});
    if(reg.listSimulations().length===0) rg.registerAllSimulations();
    s.useAppStore.getState().reset();
    const e=c.offlineCatalog().find(x=>x.simId===${JSON.stringify(sim)});
    if(!e) return 'không có mẫu';
    try { s.useAppStore.getState().loadEnvelope(e.envelope); } catch (err) { return 'lỗi: '+String(err); }
    return s.useAppStore.getState().active ? 'ok' : 'không ra active';})()`);

  console.log("  target                              stage  khung   mực  lấp/khung  rail  tràn cắt");
  for (const sim of list) {
    let loaded = await loadOne(sim);
    if (loaded !== "ok") {
      /* THỬ LẠI MỘT LẦN. Bốn target lẻ tẻ trả về undefined ở lượt đầu (CDP
         không trả kết quả kịp cho lượt nạp nặng), và mỗi lượt chạy lại rơi vào
         target khác — dấu hiệu của flake chứ không phải lỗi sản phẩm. Bỏ qua
         chúng thì bảng thiếu dòng mà vẫn trông "sạch", nên phải thử lại và nếu
         vẫn hỏng thì IN RA, không im lặng. */
      await sleep(1200);
      loaded = await loadOne(sim);
      if (loaded !== "ok") {
        console.log(`  ${sim.padEnd(34)} ${loaded ?? "(không trả lời sau 2 lượt)"}`);
        rows.push({ viewport: w, target: sim, error: loaded ?? "no-response", verdict: "KHÔNG ĐO ĐƯỢC" });
        continue;
      }
    }
    await sleep(650);
    const m = JSON.parse(await ev(MEASURE));
    if (m.error || !m.ink) { console.log(`  ${sim.padEnd(34)} ${m.error ?? "không đo được mực"}`); continue; }

    const contentW = Math.max(m.ink.w, m.textW || 0);
    const frameFill = +((contentW / m.frame.w) * 100).toFixed(1);
    const inkFill = +((m.ink.w / m.frame.w) * 100).toFixed(1);
    const stageFill = +((m.frame.w / m.stage.w) * 100).toFixed(1);
    const exception = RAIL_EXCEPTIONS[sim] ?? null;
    const rails = { ...m.rails };
    // Ngoại lệ chỉ miễn ĐÚNG rail chú giải, không miễn cả target.
    if (exception) rails.legend = null;
    const deltas = Object.values(rails).filter((x) => x !== null)
      .map((x) => Math.abs(x - m.ink.x));
    const maxRailDelta = deltas.length ? Math.max(...deltas) : 0;
    /* PHÁN QUYẾT — hai lỗi tách bạch, không gộp thành một điểm số.
       A: khung rộng hơn nhiều so với mực nó bọc (mực < 70% khung) VÀ khung
          chiếm gần hết sân khấu ⇒ cơ chế nhỏ trôi trong khung quá khổ.
       B: rail lệch > 24px (một bậc spacing) ⇒ hình và chữ hai hệ căn lề. */
    /* LỖI A đo bằng một câu FALSIFIABLE: **khung có bám theo cửa sổ không?**
       Bản trước so mực/khung, và khi đưa chữ vào mẫu số thì chữ luôn giãn đầy
       khung nên tỉ lệ luôn ~100% — luật A trở thành không thể sai, tức vô dụng.
       Khung do NỘI DUNG quyết thì bề rộng của nó GIỐNG NHAU ở 1920 và 1366;
       khung do MÀN HÌNH quyết thì nó nở ra theo. So chéo bề rộng là dấu hiệu
       trực tiếp, và nó đỏ được (tiêm lỗi cột `1fr` ⇒ 1624 vs 1242). Phép so
       chạy ở lượt tổng hợp cuối, nên ở đây chỉ ghi nhận số. */
    const failA = false;
    const failB = maxRailDelta > 24;
    const verdict = m.overflowX ? "TRÀN" : m.clipped ? "CẮT"
      : failA && failB ? "A+B" : failA ? "A" : failB ? "B" : "OK";

    rows.push({ viewport: w, target: sim, stageW: m.stage.w, frameW: m.frame.w,
      hasFrame: m.hasFrame, inkW: m.ink.w, inkX: m.ink.x, frameFill, stageFill,
      rails: m.rails, railException: exception, maxRailDelta, overflowX: m.overflowX, clipped: m.clipped, verdict });
    console.log(`  ${sim.padEnd(34)} ${String(m.stage.w).padStart(5)} ${String(m.frame.w).padStart(6)}`
      + ` ${String(m.ink.w).padStart(5)} ${String(frameFill).padStart(7)}%`
      + ` ${String(maxRailDelta).padStart(5)} ${m.overflowX ? " CÓ " : "  · "} ${m.clipped ? "CÓ" : " ·"}  ${verdict}`);
  }
  chrome.kill();
}

/* HẬU KIỂM CHÉO BỀ RỘNG — lỗi A. Chỉ so hai bề rộng RỘNG (1920 vs 1366): ở
   768 khung co lại là đúng (`max-width: 100%`), không phải bám cửa sổ. */
const WIDE = [1920, 1366];
if (VIEWPORTS.includes(WIDE[0]) && VIEWPORTS.includes(WIDE[1])) {
  const byTarget = new Map();
  for (const r of rows) {
    if (!WIDE.includes(r.viewport) || !r.frameW) continue;
    if (!byTarget.has(r.target)) byTarget.set(r.target, {});
    byTarget.get(r.target)[r.viewport] = r.frameW;
  }
  for (const [target, w] of byTarget) {
    const delta = Math.abs((w[1920] ?? 0) - (w[1366] ?? 0));
    if (delta > 24 && FRAME_EXCEPTIONS[target]) {
      for (const r of rows) {
        if (r.target === target && WIDE.includes(r.viewport)) {
          r.frameTracksViewport = delta;
          r.frameException = FRAME_EXCEPTIONS[target];
        }
      }
      console.log(`  ~ ${target}: khung bám cửa sổ ${delta}px — NGOẠI LỆ ĐÃ KHAI`);
    } else if (delta > 24) {
      for (const r of rows) {
        if (r.target === target && WIDE.includes(r.viewport)) {
          r.frameTracksViewport = delta;
          r.verdict = r.verdict === "OK" ? "A" : r.verdict + "+A";
        }
      }
      console.log(`  ✗ ${target}: khung bám cửa sổ (1920 vs 1366 lệch ${delta}px)`);
    }
  }
}

const bad = rows.filter((r) => r.verdict !== "OK");
writeFileSync(OUT, JSON.stringify({ when: new Date().toISOString(), label: LABEL, rows,
  failing: bad.length, total: rows.length }, null, 2));
console.log(`\n${bad.length === 0 ? "✔ TẤT CẢ OK" : `✗ ${bad.length}/${rows.length} dòng chưa đạt`} → ${OUT}`);
