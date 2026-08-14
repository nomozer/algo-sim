/**
 * quiz-dominance-w12.mjs — THỬ THÁCH CÓ ĐANG LẤN ÁT CƠ CHẾ KHÔNG?
 *
 * ─── VÌ SAO GUARD W6 KHÔNG ĐỦ ─────────────────────────────────────────────
 *
 * W6 khoá `.result-banner` phải `width: fit-content`. Đúng, nhưng hẹp: băng
 * phán quyết gọn trong khi CÁI HỘP CHỨA nó — câu hỏi, dãy lựa chọn, khoảng
 * đệm — vẫn có thể cao hơn cả cơ chế. Nhìn màn hình thì thấy ngay "một bài
 * kiểm tra dán dưới một hình minh hoạ"; nhìn `.result-banner` thì thấy sạch.
 *
 * Nên phép đo ở đây lấy TOÀN BỘ bề mặt thử thách và so với CƠ CHẾ:
 *
 *     tỉ lệ = chiều cao khối thử thách / chiều cao sân khấu cơ chế
 *
 * ─── VÌ SAO ĐO CHIỀU CAO, KHÔNG ĐO BỀ RỘNG ────────────────────────────────
 *
 * Cả hai đều nằm trong cùng một cột nên bề rộng gần như luôn bằng nhau — đo bề
 * rộng sẽ cho một con số không bao giờ phân biệt được gì (đúng lỗi "luật không
 * thể sai" đã gặp ở M19). Thứ mắt đọc ra là DIỆN TÍCH DỌC: khối nào chiếm
 * nhiều màn hình hơn thì khối ấy là chính.
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
  new URL("../../docs/evaluation/m20/w12-quiz-dominance.json", import.meta.url)
    .pathname.replace(/^[/]/, "")));
const VIEWPORT = Number(argOf("--viewport", "1920"));
mkdirSync(dirname(OUT), { recursive: true });

/**
 * NGƯỠNG — khai trước khi đo, không chỉnh sau khi thấy số.
 *
 * 0.5 nghĩa là bề mặt thử thách cao bằng nửa cơ chế. Quá mức ấy thì trên một
 * màn hình bình thường hai khối đọc ngang nhau, và "cơ chế là chính" thôi đúng.
 */
const FAIL_RATIO = 0.5;
const MINOR_RATIO = 0.3;

const MEASURE = `(()=>{
  const card = document.querySelector('.workspace-card');
  if (!card) return JSON.stringify({error:'không thấy .workspace-card'});
  const box = (sel) => { const el = card.querySelector(sel); if (!el) return null;
    const r = el.getBoundingClientRect();
    return { h: Math.round(r.height), w: Math.round(r.width), rows: 0 }; };

  /* CƠ CHẾ = sân khấu, không phải cả thẻ: thẻ gồm cả tiêu đề, thuyết minh và
     chính khối thử thách, nên lấy thẻ làm mẫu số sẽ pha loãng phép so. */
  const stage = box('.sim-stage') || box('.web-workspace') || box('.conv-tool');
  const challenge = box('.predict-bar');
  const inline = box('.predict-inline');

  /* Số HÀNG của khối thử thách — đếm bằng tâm dọc có dung sai, cùng cách đã
     dùng cho khay điều khiển ở W7. */
  let rows = 0;
  const bar = card.querySelector('.predict-bar');
  if (bar) {
    const kids = [...bar.children].filter(k => k.getBoundingClientRect().height > 2);
    const centers = kids.map(k => { const r = k.getBoundingClientRect(); return r.top + r.height/2; })
      .sort((a,b) => a-b);
    const tops = [];
    for (const c of centers) if (!tops.length || c - tops[tops.length-1] > 12) tops.push(c);
    rows = tops.length;
  }
  const verdict = card.querySelector('.predict-result');
  return JSON.stringify({
    stage, challenge, inline, rows,
    verdictChars: verdict ? (verdict.textContent||'').trim().length : 0,
    cardH: Math.round(card.getBoundingClientRect().height),
  });
})()`;

const session = await new BrowserSession({ viewport: VIEWPORT }).open();
const targets = JSON.parse(await session.eval(`(async()=>{
  const c=await import(${JSON.stringify(session.mods.catalog)});
  return JSON.stringify([...new Set(c.offlineCatalog().map(e=>e.simId))].sort());})()`));

console.log(`━━ W12-A MÙI QUIZ · ${VIEWPORT}px · khởi động ${session.timings.startup}ms`);
console.log("  target                          cơ chế  thử thách  tỉ lệ  hàng  chữ  phán quyết");

const rows = [];
for (const sim of targets) {
  await session.resetBetweenScenarios();
  const loaded = await session.loadTarget(sim);
  if (loaded !== "ok") { rows.push({ target: sim, error: String(loaded) }); continue; }
  await sleep(350);

  /* TÌM MỘT ĐIỂM CÓ THỬ THÁCH TRƯỚC KHI ĐO.
     `predict.challenge(state)` trả null ở phần lớn các bước, nên đo ngay ở
     cursor 0 chỉ chạm được 2/23 target — một bản quét như thế không kết luận
     được gì cho 21 target còn lại, và đọc nhầm thành "không có thử thách".
     Nên tiến từng bước tới khi lối vào hiện ra, tối đa 12 bước. */
  let opened = "không có lối vào";
  for (let step = 0; step < 12; step++) {
    await session.clickText("Thử thách");
    await sleep(150);
    const r = await session.clickText("Dự đoán bước này");
    if (r === "ok") { opened = `mở ở bước ${step}`; break; }
    const next = await session.eval(`(async()=>{
      const s=await import(${JSON.stringify(session.mods.store)});
      const st=s.useAppStore.getState();
      if (typeof st.nextStep !== 'function') return 'không tua được';
      st.nextStep(); return 'ok';})()`);
    if (next !== "ok") break;
    await sleep(200);
  }
  await sleep(350);

  const raw = await session.eval(MEASURE);
  if (typeof raw !== "string" || !raw.startsWith("{")) {
    rows.push({ target: sim, error: `đo hỏng: ${raw}` }); continue;
  }
  const m = JSON.parse(raw);
  const hasChallenge = Boolean(m.challenge);
  const ratio = hasChallenge && m.stage?.h
    ? +(m.challenge.h / m.stage.h).toFixed(2) : null;
  const verdictState = !hasChallenge ? "KHÔNG CÓ THỬ THÁCH"
    : ratio === null ? "KHÔNG ĐO ĐƯỢC"
    : ratio > FAIL_RATIO ? "FAIL"
    : ratio > MINOR_RATIO ? "MINOR" : "NONE";

  console.log(`  ${sim.padEnd(32)}${String(m.stage?.h ?? "—").padStart(7)}` +
    `${String(m.challenge?.h ?? "—").padStart(10)}${String(ratio ?? "—").padStart(7)}` +
    `${String(m.rows).padStart(6)}${String(m.verdictChars).padStart(5)}  ${verdictState}`);
  rows.push({ target: sim, opened, ...m, ratio, quizDominance: verdictState });
}

await session.close();
const fails = rows.filter((r) => r.quizDominance === "FAIL");
const withChallenge = rows.filter((r) => r.challenge);
console.log(`\n  ${withChallenge.length}/${rows.length} target có bề mặt thử thách · ` +
  `${fails.length} FAIL (tỉ lệ > ${FAIL_RATIO})`);
for (const f of fails) console.log(`   ✘ ${f.target}: thử thách ${f.challenge.h}px / cơ chế ${f.stage?.h}px = ${f.ratio}`);

writeFileSync(OUT, JSON.stringify({
  ...provenance("quiz-dominance-w12", { viewport: VIEWPORT }),
  kind: "CERTIFICATION_EVIDENCE",
  question: "Khi mở thử thách, cơ chế còn là khối lớn nhất trên màn hình không?",
  thresholds: { fail: FAIL_RATIO, minor: MINOR_RATIO },
  serverStarts: session.serverStarts,
  rows,
}, null, 2), "utf-8");
console.log(`\n→ ${OUT}`);
process.exit(0);
