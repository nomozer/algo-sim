/**
 * certify-experience-w12.mjs — 23 TARGET: CÔNG CỤ DẠY HỌC hay CHỈ LỘ DẦN?
 *
 * ─── CÂU HỎI ──────────────────────────────────────────────────────────────
 *
 * `interaction-semantics.test.ts` đã hỏi "module NHẬN action gì" — hợp đồng.
 * `certify-viewports-w12.mjs` đã hỏi "affordance có NHÌN THẤY không" — bề mặt.
 * Còn thiếu đúng câu người dùng hỏi:
 *
 *     ĐÓNG thử thách rồi, học sinh làm được gì có nghĩa trên màn này?
 *
 * ─── PHÂN BIỆT THẾ NÀO CHO KHỎI TỰ LỪA ────────────────────────────────────
 *
 * "Tua từng bước thì màn hình đổi" KHÔNG phân biệt được gì: một bản trình chiếu
 * cũng đổi. Nên phép đo ở đây tách hai kiểu đổi:
 *
 *   THÊM DỒN (append-only) — bước sau chứa trọn bước trước. Đây là hình dạng
 *     của một bảng in dần từng dòng: đáp án có sẵn, chỉ lộ ra từ từ.
 *   THAY THẾ — giá trị bị đổi, con trỏ dời, vùng xét co lại. Đây là hình dạng
 *     của một cơ chế đang chạy.
 *
 * Và câu hỏi mạnh hơn cả hai: ĐỔI ĐẦU VÀO thì kết quả có tính lại không. Nếu
 * có, target là CÔNG CỤ và không cần bàn tiếp (W12 §19).
 *
 * ─── PHÂN LOẠI ────────────────────────────────────────────────────────────
 *
 *   đổi đầu vào → kết quả đổi              ⇒ TOOL_PASS
 *   không đổi được, nhưng tua THAY THẾ     ⇒ TRACE_PASS   (§17: tiến trình LÀ cơ chế)
 *   không đổi được, tua chỉ THÊM DỒN       ⇒ EXPERIENCE_FAIL
 *
 * ⚠️ Backtick KHÔNG được xuất hiện trong biểu thức tiêm vào trang.
 */
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { provenance } from "./evidence.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const OUT = resolve(argOf("--out",
  new URL("../../docs/evaluation/m20/w12-experience-audit.json", import.meta.url)
    .pathname.replace(/^[/]/, "")));
const ONLY = argOf("--target", null);
mkdirSync(dirname(OUT), { recursive: true });

/**
 * DẤU VÂN của bề mặt học sinh nhìn thấy — CHỮ cộng THUỘC TÍNH THỊ GIÁC.
 *
 * Hai lần sửa, cả hai vì phép đo cắt mất chỗ có thay đổi:
 *
 * 1. Chỉ lấy .sim-stage thì mất dải quan sát. Ở binary_search/linear_search,
 *    các chip đổi theo bước (phần tử giữa · vùng xét · đã so sánh) sống trong
 *    .search-observe, vốn là ANH EM của .sim-stage chứ không nằm trong nó. Đo
 *    kiểu ấy cho ra "13 bước engine, 1 bước màn" — một kết luận sai về sản phẩm.
 * 2. Chỉ lấy chữ thì mất màu. ScanWorkspace chỉ vẽ ArrayView: giá trị và chỉ số
 *    đứng yên, thứ đổi là CỘT NÀO ĐANG XÉT — mã bằng fill/class. Với một bài mà
 *    nội dung học là "duyệt tới đâu rồi", màu CHÍNH LÀ nội dung.
 *
 * Nên lấy cả thẻ (trừ đồ đạc dùng chung) và nối thêm fill/class của mọi phần tử
 * SVG. Vẫn không bắt được vị trí/kích thước — ghi rõ giới hạn thay vì lờ đi.
 */
const STAGE_TEXT = `(()=>{
  const card = document.querySelector('.workspace-card');
  if (!card) return '';
  const clone = card.cloneNode(true);
  for (const el of clone.querySelectorAll('.transport,.player,.predict-bar,.predict-inline')) {
    el.remove();
  }
  const text = (clone.innerText || clone.textContent || '').replace(/\s+/g, ' ').trim();
  const paint = [...clone.querySelectorAll('svg *')]
    .map((el) => (el.getAttribute('fill') || '') + '/' + (el.getAttribute('class') || ''))
    .join(',');
  return text + ' ¶ ' + paint;
})()`;

/* Ứng viên action KHÔNG sống ở đây — chủ sở hữu là
   `src/simulations/action-probe.ts`, cùng bộ mà `experience-gate.test.ts` dùng.
   Giữ một bản sao trong file này là tái lập đúng lỗi vừa sửa ở
   `tool-affordance.ts`: một luật chép tay hai nơi thì lệch ở một nơi. */

const session = await new BrowserSession({ viewport: 1536 }).open();
const targets = JSON.parse(await session.eval(`(async()=>{
  const c=await import(${JSON.stringify(session.mods.catalog)});
  return JSON.stringify([...new Set(c.offlineCatalog().map(e=>e.simId))].sort());})()`))
  .filter((t) => !ONLY || t === ONLY);

console.log(`━━ SOÁT TRẢI NGHIỆM · ${targets.length} target · khởi động ${session.timings.startup}ms\n`);
console.log("  target                          đổi đầu vào   engine  màn   phán quyết");

const rows = [];
for (const sim of targets) {
  await session.resetBetweenScenarios();
  const loaded = await session.loadTarget(sim);
  if (loaded !== "ok") { rows.push({ target: sim, error: String(loaded) }); continue; }
  await sleep(400);

  const before = await session.eval(STAGE_TEXT);

  /* ── 1. ĐỔI ĐẦU VÀO CÓ TÍNH LẠI KHÔNG ─────────────────────────────────── */
  const tried = JSON.parse(await session.eval(`(async()=>{
    const s=await import(${JSON.stringify(session.mods.store)});
    const p=await import(${JSON.stringify(session.mods.probe)});
    const st=s.useAppStore.getState();
    const cfg=st.active && st.active.config;
    return JSON.stringify(p.candidateActions(cfg||{}));})()`));

  let accepted = null;
  let after = before;
  for (const action of tried) {
    await session.dispatch(action);
    await sleep(260);
    const txt = await session.eval(STAGE_TEXT);
    if (txt !== before) { accepted = action; after = txt; break; }
    /* Không đổi ⇒ trả lại hiện trường trước khi thử ứng viên kế, nếu không một
       action bị nuốt vẫn có thể để lại state lệch cho phép thử sau. */
    await session.loadTarget(sim);
    await sleep(200);
  }

  /* ── 2. TUA LÀ THAY THẾ HAY CHỈ THÊM DỒN ──────────────────────────────── */
  await session.loadTarget(sim);
  await sleep(300);
  /* SỐ BƯỚC ENGINE KHAI — khác hẳn số chữ phân biệt trên màn. Chênh giữa hai
     con số này chính là thứ phát hiện được "trace có mà không hiện". */
  const traceSteps = Number(await session.eval(`(async()=>{
    const s=await import(${JSON.stringify(session.mods.store)});
    const a=s.useAppStore.getState().active;
    const st=a && a.state;
    if(!st) return 0;
    if(st.trace && Array.isArray(st.trace.steps)) return st.trace.steps.length;
    if(Array.isArray(st.steps)) return st.steps.length;
    return 0;})()`)) || 0;
  const texts = [];
  for (let step = 0; step < 14; step += 1) {
    texts.push(await session.eval(STAGE_TEXT));
    const next = await session.eval(`(async()=>{
      const s=await import(${JSON.stringify(session.mods.store)});
      const st=s.useAppStore.getState();
      if (typeof st.nextStep !== 'function') return 'không tua được';
      /* So chính STATE, không so 'st.cursor': con trỏ sống trong active.state,
         nên 'st.cursor' là undefined và phép so undefined===undefined luôn báo
         'hết' ngay bước đầu — đúng lỗi đã gặp ở W12-A với 'st.next()'. Một vòng
         lặp thoát ngay lập tức vẫn trả về một con số trông hợp lệ. */
      const b=JSON.stringify(st.active && st.active.state);
      st.nextStep();
      const a=JSON.stringify(s.useAppStore.getState().active.state);
      return a===b ? 'hết' : 'ok';})()`);
    if (next !== "ok") break;
    await sleep(170);
  }
  const distinct = [...new Set(texts)];
  /* THÊM DỒN = mọi bước sau chứa trọn bước trước. Cần ≥3 bước phân biệt mới
     kết luận được; ít hơn thì không đủ dữ kiện, và nói thế còn hơn đoán. */
  let appendOnly = distinct.length >= 3;
  for (let i = 1; i < distinct.length && appendOnly; i += 1) {
    if (!distinct[i].includes(distinct[i - 1])) appendOnly = false;
  }

  /* "KHÔNG ĐỦ DỮ KIỆN" là một chỗ TRỐN nếu để nguyên: hai target rơi vào đó và
     cả hai đều có câu trả lời rõ khi hỏi thêm một câu. Nên tách ra theo ĐÚNG
     cái thiếu, và mỗi nhãn là một việc phải làm chứ không phải một dấu hỏi:

       không đổi được + KHÔNG có timeline      ⇒ STATIC_ILLUSTRATION
         (một bức hình, không phải mô phỏng — decimal_to_binary: state chỉ có
          {bits, bitWidth}, không trace, apply không nhận gì)
       không đổi được + CÓ timeline nhưng sân khấu không đổi ⇒ TRACE_NOT_VISIBLE
         (engine có 4 bước, màn hình có 1 — tiến trình KHÔNG tới được mắt học
          sinh, nên lý do tồn tại của một TRACE_MODEL không thành lập) */
  const verdict = accepted ? "TOOL_PASS"
    : traceSteps < 2 ? "STATIC_ILLUSTRATION"
    : distinct.length < 2 ? "TRACE_NOT_VISIBLE"
    : distinct.length < 3 ? "KHÔNG ĐỦ DỮ KIỆN"
    : appendOnly ? "EXPERIENCE_FAIL"
    : "TRACE_PASS";

  console.log(`  ${sim.padEnd(32)}${(accepted ? " ✔ " + accepted.type : " ✘").padEnd(14)}` +
    `${String(traceSteps).padStart(6)}${String(distinct.length).padStart(7)}   ${verdict}`);
  rows.push({
    target: sim, verdict,
    inputAccepted: accepted, candidatesTried: tried.length,
    stepsDistinct: distinct.length, traceSteps, appendOnly,
    stageAtStart: texts[0] ? texts[0].slice(0, 220) : "",
  });
}

await session.close();

const fails = rows.filter((r) => r.verdict === "EXPERIENCE_FAIL");
const thin = rows.filter((r) => r.verdict === "KHÔNG ĐỦ DỮ KIỆN");
const tally = rows.reduce((a, r) => ((a[r.verdict] = (a[r.verdict] || 0) + 1), a), {});
console.log(`\n  ${JSON.stringify(tally)}`);
for (const f of fails) console.log(`   ✘ ${f.target}: không đổi được đầu vào (${f.candidatesTried} ứng viên) và tua chỉ THÊM DỒN`);
for (const t of thin) console.log(`   ? ${t.target}: chỉ ${t.stepsDistinct} bước phân biệt — chưa kết luận được`);

writeFileSync(OUT, JSON.stringify({
  ...provenance("certify-experience-w12", {}),
  kind: "CERTIFICATION_EVIDENCE",
  question: "ĐÓNG thử thách rồi, học sinh làm được gì có nghĩa trên màn này?",
  method: "đổi đầu vào ⇒ TOOL_PASS · tua THAY THẾ ⇒ TRACE_PASS · tua chỉ THÊM DỒN ⇒ EXPERIENCE_FAIL",
  serverStarts: session.serverStarts,
  tally, rows,
}, null, 2), "utf-8");
console.log(`\n→ ${OUT}`);
process.exit(fails.length ? 1 : 0);
