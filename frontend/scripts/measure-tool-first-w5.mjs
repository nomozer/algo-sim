/**
 * measure-tool-first-w5.mjs — CÔNG CỤ HAY HOẠT HÌNH?
 *
 * Wave 5 §0/§7 hỏi một câu duy nhất, và nó phải BÁC BỎ ĐƯỢC:
 *
 *   Ẩn thanh điều khiển đi, học sinh còn thấy được KẾT QUẢ HIỆN TẠI không?
 *
 * Cách đo: nạp target ở cursor 0 (chưa bấm gì), đếm ô dữ liệu và chữ số kết quả
 * đang hiện. Rồi tua tới bước cuối, đếm lại. Hiệu số > 0 nghĩa là câu trả lời
 * đang bị KHOÁ SAU thanh điều khiển — đúng định nghĩa "hoạt hình", không phải
 * công cụ.
 *
 * ⚠️ Vì sao KHÔNG đo bằng ảnh chụp: mắt người nhìn một bảng rỗng vẫn thấy
 * "trang có nội dung" (tiêu đề, chú giải, thanh tham số đều còn đó). Phép đếm ô
 * phân biệt được "sân khấu có chữ" với "sân khấu trả lời được câu hỏi".
 *
 * ⚠️ Backtick KHÔNG được xuất hiện trong biểu thức tiêm vào trang — đã làm Node
 * báo SyntaxError bốn lần trong repo này.
 */
import { spawn } from "node:child_process";
import { provenance } from "./evidence.mjs";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const OUT = resolve(argOf("--out",
  new URL("../../docs/evaluation/m20/tool-first-before.json", import.meta.url)
    .pathname.replace(/^[/]/, "")));
const LABEL = argOf("--label", "before");
const TARGETS = argOf("--targets",
  "web.style_model,binary.base_conversion,binary.character_encoding").split(",");
const VIEWPORT = Number(argOf("--viewport", "1920"));
mkdirSync(dirname(OUT), { recursive: true });

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

/** Đếm thứ TRẢ LỜI được câu hỏi, không đếm thứ mô tả câu hỏi. */
const PROBE = `(()=>{
  const card = document.querySelector('.workspace-card');
  if (!card) return JSON.stringify({error:'không thấy .workspace-card'});
  const vis = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    const r = el.getBoundingClientRect();
    return r.width > 2 && r.height > 2;
  };
  const dataCells = [...card.querySelectorAll('table tbody td')].filter(vis).length;
  const dataRows = [...card.querySelectorAll('table tbody tr')].filter(vis).length;
  /* ĐƠN VỊ THÔNG TIN — thước đo CHÍNH, và nó phải độc lập với thẻ HTML.
     Bản đầu chỉ đếm 'table td', nên khi bề mặt công cụ được dựng bằng lưới div
     thì phép đo báo "vẫn 0 ô" cho một trang đã hiện đủ kết quả: thước đo đang
     đo THẺ chứ không đo THÔNG TIN. Đếm phần tử LÁ có chữ, trừ đồ đạc của thẻ và
     thanh điều khiển — thứ trả lời câu hỏi, không phải thứ mô tả câu hỏi. */
  const FURNITURE = '.transport,.workspace-header,.stage-legend,.param-bar,.notes';
  const infoAtoms = [...card.querySelectorAll('*')].filter((el) => {
    if (el.children.length > 0) return false;
    if (el.closest(FURNITURE)) return false;
    if (!vis(el)) return false;
    return (el.textContent || '').trim().length > 0;
  }).length;
  /* Ô ĐIỀU KHIỂN: thứ học sinh đổi được ngay, không cần bấm Tiến. */
  const controls = [...card.querySelectorAll('input,select,button[role=switch],[role=slider]')]
    .filter(vis).filter(el => !el.closest('.transport')).length;
  /* Chữ trên sân khấu — dùng để phân biệt "trang trống" với "trang có chữ mà
     không có số". */
  const stage = card.querySelector('.sim-stage');
  const stageText = stage ? stage.textContent.replace(/\\s+/g,' ').trim() : '';
  const svgCount = [...card.querySelectorAll('svg')].filter(vis).length;
  return JSON.stringify({ dataCells, dataRows, infoAtoms, controls, svgCount,
    stageTextLen: stageText.length, stageHead: stageText.slice(0, 110) });
})()`;

const cdp = 9700 + Math.floor(Math.random() * 200);
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu",
  `--remote-debugging-port=${cdp}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "w5-"))}`,
  `--window-size=${VIEWPORT},1080`, "--hide-scrollbars", "about:blank"], { stdio: "ignore" });
let wsUrl;
for (let i = 0; i < 40 && !wsUrl; i++) {
  try {
    const l = await (await fetch(`http://127.0.0.1:${cdp}/json/list`)).json();
    wsUrl = l.find((t) => t.type === "page")?.webSocketDebuggerUrl;
  } catch { /* chưa lên */ }
  if (!wsUrl) await sleep(250);
}
const ws = new WebSocket(wsUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pend = new Map();
ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } };
const send = (m, p = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method: m, params: p })); });
const ev = async (x) => {
  const r = await send("Runtime.evaluate", { expression: x, awaitPromise: true, returnByValue: true });
  const ex = r.result?.exceptionDetails;
  if (ex) return "LỖI: " + String(ex.exception?.description ?? ex.text ?? "?").split(String.fromCharCode(10))[0];
  return r.result?.result?.value;
};

await send("Page.enable"); await send("Runtime.enable");
await send("Page.navigate", { url: "http://localhost:3000" });
await sleep(3200);

/* DẤU VÂN TAY TRANG (§ARCHITECTURE_MAP #14): sai route thì thoát != 0, không
   im lặng báo SẠCH. Bản soát chưa từng đỏ là bản soát chưa được chứng minh. */
const fingerprint = await ev(`document.querySelectorAll('.app-main,.nav-bar').length`);
if (!fingerprint) { console.error("Không nhận ra trang — sai route?"); process.exit(2); }

const u = JSON.parse(await ev(RESOLVE));
await ev(`(async()=>{${Object.values(u).map((x) => `await import(${JSON.stringify(x)});`).join("")}return 1})()`);

const load = (sim) => ev(`(async()=>{
  const s=await import(${JSON.stringify(u.store)});const c=await import(${JSON.stringify(u.catalog)});
  const rg=await import(${JSON.stringify(u.sims)});const reg=await import(${JSON.stringify(u.registry)});
  if(reg.listSimulations().length===0) rg.registerAllSimulations();
  s.useAppStore.getState().reset();
  const e=c.offlineCatalog().find(x=>x.simId===${JSON.stringify(sim)});
  if(!e) return 'không có mẫu';
  try { s.useAppStore.getState().loadEnvelope(e.envelope); } catch (err) { return 'lỗi: '+String(err); }
  return s.useAppStore.getState().active ? 'ok' : 'không ra active';})()`);

/**
 * PHÉP ĐO CHÍNH của §7 — và nó KHÔNG phải hiệu số.
 *
 * Bản trước phán bằng "nội dung có tăng khi tua không". Sai tiêu chí: §1 nói
 * DIỄN GIẢI *nên* hiện dần theo bước, nên một target hoàn toàn lành mạnh vẫn
 * cho hiệu số dương. Đo như thế thì mọi bản sửa đều trượt, kể cả bản sửa đúng.
 *
 * Câu hỏi thật: **ở cursor 0, học sinh đọc được KẾT QUẢ HIỆN TẠI chưa?**
 *
 * Cách hỏi không vòng vo: lấy đáp án từ CHÍNH engine tất định trong store, rồi
 * kiểm chuỗi đó có nằm trong DOM đang hiện không. Đây không phải oracle tự
 * chứng minh — nó kiểm RENDERER có nói đúng thứ ENGINE đang giữ, đúng ranh giới
 * R0. Tính đúng của bản thân đáp án do oracle độc lập bên vitest lo.
 */
const ANSWER_OF = {
  "binary.base_conversion": "st.active.state.result",
  "binary.character_encoding": "st.active.state.rows.map(r=>r.binary).join(' ')",
};

const answerVisible = (sim) => ev(`(async()=>{
  const s=await import(${JSON.stringify(u.store)});
  const st=s.useAppStore.getState();
  const expr=${JSON.stringify(ANSWER_OF[sim] ?? "")};
  if(!expr) return JSON.stringify({applicable:false});
  let want; try { want=eval(expr); } catch(e){ return JSON.stringify({error:String(e)}); }
  if(want===undefined||want===null) return JSON.stringify({error:'engine không trả đáp án'});
  const card=document.querySelector('.workspace-card');
  const dom=card?card.innerText.replace(/\\s+/g,' '):'';
  const parts=String(want).split(' ').filter(Boolean);
  const missing=parts.filter(p=>!dom.includes(p));
  return JSON.stringify({applicable:true, expected:String(want),
    visible: missing.length===0, missing});})()`);

/**
 * Tua tới bước cuối QUA STORE, không qua nút — phép đo không phụ thuộc UI.
 *
 * ⚠️ Bản đầu gọi `st.next()`, một API KHÔNG TỒN TẠI. Vòng lặp `break` ngay lập
 * tức rồi vẫn trả 'ok', nên mọi target đọc ra "0 → 0 ô, không bị khoá" — một
 * kết luận SAI theo hướng có lợi. Nên hàm này phải TỰ CHỨNG MINH nó đã tua:
 * trả cursor trước/sau, và người gọi coi "cursor không đổi" là phép đo hỏng chứ
 * không phải bằng chứng.
 */
const toEnd = () => ev(`(async()=>{
  const s=await import(${JSON.stringify(u.store)});
  const cur=()=>{const a=s.useAppStore.getState().active; return a&&a.state&&typeof a.state.cursor==='number'?a.state.cursor:null;};
  const before=cur();
  const st=s.useAppStore.getState();
  if (typeof st.toEnd !== 'function') return JSON.stringify({error:'store không có toEnd()'});
  st.toEnd();
  return JSON.stringify({cursorBefore:before, cursorAfter:cur()});})()`);

const rows = [];
console.log(`━━ ${VIEWPORT}px  [${LABEL}]  HEAD ${provenance("measure-tool-first-w5").head.slice(0, 8)}`);
console.log("  target                         tin@cursor0 tin@cuối  đ.khiển  ĐÁP ÁN Ở CURSOR 0?");
for (const sim of TARGETS) {
  /* THỬ LẠI MỘT LẦN — lượt nạp đầu tiên hay trả undefined vì CDP không kịp trả
     kết quả cho lượt import nặng (đã ghi trong audit-composition.mjs). Bỏ qua
     thì bảng thiếu dòng mà vẫn trông sạch. */
  let loaded = await load(sim);
  if (loaded !== "ok") { await sleep(1200); loaded = await load(sim); }
  if (loaded !== "ok") {
    console.log(`  ${sim.padEnd(32)} ${loaded ?? "(không trả lời sau 2 lượt)"}`);
    rows.push({ target: sim, error: loaded ?? "no-response" }); continue;
  }
  await sleep(600);
  const beforeRaw = await ev(PROBE);
  if (typeof beforeRaw !== "string") {
    console.log(`  ${sim.padEnd(32)} probe hỏng: ${beforeRaw}`);
    rows.push({ target: sim, error: `probe: ${beforeRaw}` }); continue;
  }
  const before = JSON.parse(beforeRaw);
  const ans = JSON.parse(await answerVisible(sim));
  const move = JSON.parse(await toEnd());
  await sleep(600);
  const after = JSON.parse(await ev(PROBE));
  // Cursor không nhúc nhích ⇒ phép đo HỎNG, không phải "không bị khoá".
  /* BA kết cục, không hai. Gộp "target không có dòng thời gian" vào "phép đo
     hỏng" sẽ giấu mất việc target ấy VỐN ĐÃ là công cụ; gộp vào "không bị khoá"
     thì ngược lại, cho không nó một lời khen nó chưa chứng minh. */
  const noTimeline = move.cursorBefore === null && move.cursorAfter === null;
  const moved = !noTimeline && move.cursorAfter !== move.cursorBefore;
  const gated = (after.infoAtoms ?? 0) - (before.infoAtoms ?? 0);
  /* PHÁN QUYẾT §7 đọc `ans`, KHÔNG đọc hiệu số. Hiệu số chỉ còn là số phụ. */
  const verdict = ans.error ? `LỖI: ${ans.error}`
    : !ans.applicable ? "không có đáp án đơn trị (công cụ thuần)"
    : ans.visible ? "ĐỌC ĐƯỢC ở cursor 0"
    : `KHOÁ SAU PLAY (thiếu: ${(ans.missing || []).slice(0, 3).join(",")})`;
  console.log(`  ${sim.padEnd(32)} ${String(before.infoAtoms).padStart(8)} ${String(after.infoAtoms).padStart(7)} ${String(before.controls).padStart(10)}   ${verdict}`);
  rows.push({ target: sim, answerAtCursor0: ans, atCursor0: before, atEnd: after, cursor: move,
    hasTimeline: !noTimeline, measurementValid: noTimeline || moved,
    gatedCells: moved ? gated : null,
    gatedBehindTransport: moved ? gated > 0 : (noTimeline ? false : null) });
}

writeFileSync(OUT, JSON.stringify({
  ...provenance("measure-tool-first-w5", { viewport: VIEWPORT, label: LABEL }),
  question: "Ở cursor 0, DOM có hiện đúng đáp án mà engine tất định đang giữ không?",
  note: "Hiệu số tin@cursor0 → tin@cuối KHÔNG phải tiêu chí: §1 nói diễn giải NÊN " +
        "hiện dần theo bước, nên một target lành mạnh vẫn cho hiệu số dương.",
  rows,
}, null, 2), "utf-8");
console.log(`\n→ ${OUT}`);
ws.close(); chrome.kill();
process.exit(0);
