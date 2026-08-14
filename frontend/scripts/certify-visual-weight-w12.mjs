/**
 * certify-visual-weight-w12.mjs — MÔ PHỎNG CÓ ĐANG LÀ THỨ CHÍNH KHÔNG?
 *
 * ─── VÌ SAO CẦN PHÉP ĐO NÀY ────────────────────────────────────────────────
 *
 * Mọi tiêu chí W12 trước đó đều hỏi MỘT câu: "đổi đầu vào thì kết quả có tính
 * lại không". Câu ấy đúng nhưng KHÔNG đủ, và người dùng chỉ ra bằng cách mở hai
 * màn hình:
 *
 *   `network.packet_routing` — bốn biểu tượng đứng yên, một chấm, bốn bước chữ.
 *     Đạt mọi tiêu chí cũ. Nhìn vào thì nó là một hình minh hoạ có chú thích.
 *
 * Nên phép đo ở đây hỏi câu còn thiếu:
 *
 *     Trên sân khấu, HÌNH chiếm bao nhiêu so với CHỮ?
 *
 * ─── ĐO GÌ CHO KHỎI TỰ LỪA ────────────────────────────────────────────────
 *
 * Đếm ký tự thì một bài có nhãn dữ liệu dày (bảng mã hoá) sẽ bị phạt oan, còn
 * một bài có hình to mà rỗng nghĩa lại được thưởng. Nên đo BA thứ và để cạnh
 * nhau thay vì ép thành một điểm số:
 *
 *   1. `inkArea`  — tổng diện tích phần tử ĐỒ HOẠ (svg/canvas) trên sân khấu.
 *   2. `proseChars` — số ký tự trong các khối VĂN XUÔI (p, .notes, thuyết minh),
 *      KHÔNG tính nhãn nằm trong hình và không tính ô bảng dữ liệu.
 *   3. `glyphs` — số phần tử đồ hoạ, GHI LẠI ĐỂ ĐỌC chứ không dùng phán quyết:
 *      nó đo kích thước dữ liệu (dãy 3 phần tử có 5 hình) chứ không đo chất
 *      lượng, và nó không nhìn được vào canvas của cảnh 3D.
 *
 * ⚠️ Đây là phép đo BỀ MẶT, không phải phép đo hiểu biết. Nó trả lời "màn hình
 * này lấy hình làm chính hay lấy chữ làm chính", không trả lời "học sinh có
 * hiểu hơn không" — `LEARNER_IMPACT_NOT_EVALUATED` giữ nguyên.
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
  new URL("../../docs/evaluation/m20/w12-visual-weight.json", import.meta.url)
    .pathname.replace(/^[/]/, "")));
mkdirSync(dirname(OUT), { recursive: true });

const MEASURE = `(()=>{
  const card = document.querySelector('.workspace-card');
  if (!card) return JSON.stringify({error:'không thấy .workspace-card'});
  const vis = (el) => { const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    const r = el.getBoundingClientRect(); return r.width > 2 && r.height > 2; };
  const furniture = (el) => el.closest('.transport,.player,.predict-bar,.predict-inline');

  /* HÌNH — svg/canvas nhìn thấy được, không tính đồ đạc dùng chung. */
  let inkArea = 0, glyphs = 0;
  /* Bề mặt CƠ CHẾ không chỉ là svg: cảnh 3D là <canvas> (không đọc được bên
     trong), và mô hình trang web là DOM thật (.web-page). Bản đầu chỉ đếm svg
     nên gán 0% cho web.style_model và "1 bộ phận" cho cảnh 3D — hai kết luận
     sai về sản phẩm, do phép đo mù chứ không do màn hình nghèo.
     LẦN THỨ BA cùng lỗi ấy: protocol_encapsulation sau khi trả về 2D dựng
     bằng KHỐI HTML. Đọc encap-ui.tsx thay vì đoán selector: .encap-layer là KHỐI
     TẦNG (cơ chế thật, mỗi tầng một hộp), .encap-medium là đường truyền.
     KHÔNG đếm .encap-2d — đó là vỏ bọc, và đếm vỏ để lên điểm chính là cách
     một phép đo tự làm mình vô nghĩa.
     nên phép đo lại đọc 0.0%. Cơ chế không phải lúc nào cũng là svg. */
  for (const g of card.querySelectorAll('svg,canvas,.web-page,.web-preview,.encap-layer,.encap-medium')) {
    if (!vis(g) || furniture(g)) continue;
    const r = g.getBoundingClientRect();
    inkArea += Math.round(r.width * r.height);
    glyphs += g.querySelectorAll('rect,circle,path,line,polygon,ellipse,image').length || 1;
  }

  /* VĂN XUÔI — chỉ khối kể chuyện, KHÔNG tính nhãn trong hình, không tính ô
     bảng dữ liệu (bảng LÀ kết quả của engine, phạt nó là phạt nhầm). */
  let proseChars = 0;
  const proseSel = 'p,.notes,.hint,.stage-legend,.narration-bar,.feedback-bar,.result-banner';
  for (const el of card.querySelectorAll(proseSel)) {
    if (!vis(el) || furniture(el) || el.closest('svg')) continue;
    proseChars += (el.innerText || el.textContent || '').trim().length;
  }

  /* Diện tích thẻ để biết hình chiếm bao nhiêu phần màn. */
  const cr = card.getBoundingClientRect();
  return JSON.stringify({
    inkArea, glyphs, proseChars,
    cardArea: Math.round(cr.width * cr.height),
    inkShare: cr.width * cr.height ? +(inkArea / (cr.width * cr.height)).toFixed(3) : 0,
    tables: card.querySelectorAll('table').length,
  });
})()`;

/* NGƯỠNG khai TRƯỚC khi nhìn số.
   inkShare 0.15 = hình chiếm ít hơn 1/6 thẻ ⇒ khó gọi là "hình làm chính".
   Chỉ MỘT ngưỡng: bản đầu có thêm `MIN_GLYPHS` và nó SAI — xem lý do ở chỗ
   phán quyết. `glyphs` vẫn ghi vào artifact để đọc, không dùng để phán. */
const MIN_INK_SHARE = 0.15;

/**
 * MÃ GIẢ LÀ CƠ CHẾ — ngoại lệ có tên, **chỉ được NGẮN ĐI**.
 *
 * Cùng lí lẽ với việc miễn ngưỡng cho bài có bảng: ở những bài này thứ học sinh
 * phải đọc CHÍNH LÀ dòng lệnh, và con trỏ dòng chạy qua nó là cơ chế — giống
 * một trình gỡ lỗi. Vẽ thêm hình cho đủ tỉ lệ sẽ là trang trí, không phải dạy.
 *
 * Đây KHÔNG phải chỗ giấu nợ: mỗi mục bị kiểm ngược ở dưới (khai mà lại nhiều
 * hình thì ĐỎ), và thêm một dòng ở đây là tự khai vừa hạ một target xuống
 * chữ-làm-chính.
 */
const CODE_IS_THE_MECHANISM = {
  "algorithm.bounded_control_flow":
    "sân khấu là mã giả với con trỏ dòng — luồng điều khiển LÀ nội dung bài",
};

const session = await new BrowserSession({ viewport: 1536 }).open();
const targets = JSON.parse(await session.eval(`(async()=>{
  const c=await import(${JSON.stringify(session.mods.catalog)});
  return JSON.stringify([...new Set(c.offlineCatalog().map(e=>e.simId))].sort());})()`));

console.log(`━━ SỨC NẶNG THỊ GIÁC · ${targets.length} target · 1536px\n`);
console.log("  target                          hình%   bộ phận  chữ  bảng  phán quyết");

const rows = [];
for (const sim of targets) {
  await session.resetBetweenScenarios();
  const loaded = await session.loadTarget(sim);
  if (loaded !== "ok") { rows.push({ target: sim, error: String(loaded) }); continue; }
  await sleep(450);
  const raw = await session.eval(MEASURE);
  if (typeof raw !== "string" || !raw.startsWith("{")) {
    rows.push({ target: sim, error: `đo hỏng: ${raw}` }); continue;
  }
  const m = JSON.parse(raw);
  const problems = [];
  /* Bảng LÀ hình của bài dữ liệu — một bài có bảng thì phần hình được tính
     bằng bảng, nên không phạt inkShare ở đó. Nói ra thay vì lặng lẽ miễn. */
  if (m.tables === 0 && !(sim in CODE_IS_THE_MECHANISM) && m.inkShare < MIN_INK_SHARE) {
    problems.push(`hình chỉ chiếm ${(m.inkShare * 100).toFixed(1)}% thẻ`);
  }
  /* Ngoại lệ phải CHỨNG MINH ĐƯỢC: một target khai "mã là cơ chế" mà lại có
     nhiều hình thì lời khai ấy sai, và im lặng cho qua là mở đường cho ngoại lệ
     nuốt dần cả luật. */
  if (sim in CODE_IS_THE_MECHANISM && m.inkShare >= MIN_INK_SHARE) {
    problems.push(`khai "mã là cơ chế" nhưng hình chiếm ${(m.inkShare * 100).toFixed(1)}% — bỏ khai đi`);
  }
  /* NGƯỠNG `glyphs` ĐÃ GỠ — nó đo KÍCH THƯỚC DỮ LIỆU, không đo chất lượng.
     Một dãy 3 phần tử có 5 hình chữ nhật; một dãy 10 phần tử có 12. Phạt cái
     đầu là phạt đề bài ngắn, không phải phạt màn hình nghèo. Nó cũng không
     nhìn được vào <canvas>, nên vừa gán "tranh tĩnh" cho cảnh 3D thật.
     Giữ lại con số trong artifact để đọc, KHÔNG dùng nó để phán quyết. */
  const verdict = problems.length ? "CHỮ LÀ CHÍNH" : "HÌNH LÀ CHÍNH";
  console.log(`  ${sim.padEnd(32)}${(m.inkShare * 100).toFixed(1).padStart(6)}%` +
    `${String(m.glyphs).padStart(9)}${String(m.proseChars).padStart(6)}` +
    `${String(m.tables).padStart(6)}   ${verdict}`);
  rows.push({ target: sim, ...m, problems, verdict });
}

await session.close();
const bad = rows.filter((r) => r.verdict === "CHỮ LÀ CHÍNH");
console.log(`\n  ${rows.length - bad.length}/${rows.length} lấy HÌNH làm chính`);
for (const b of bad) console.log(`   ✘ ${b.target}: ${b.problems.join(", ")}`);

writeFileSync(OUT, JSON.stringify({
  ...provenance("certify-visual-weight-w12", { viewport: 1536 }),
  kind: "CERTIFICATION_EVIDENCE",
  question: "Trên sân khấu, HÌNH chiếm bao nhiêu so với CHỮ?",
  thresholds: { minInkShare: MIN_INK_SHARE },
  limitation: "Đo BỀ MẶT, không đo hiểu biết. LEARNER_IMPACT_NOT_EVALUATED giữ nguyên.",
  serverStarts: session.serverStarts,
  passed: rows.length - bad.length, total: rows.length, rows,
}, null, 2), "utf-8");
console.log(`\n→ ${OUT}`);
process.exit(bad.length ? 1 : 0);
