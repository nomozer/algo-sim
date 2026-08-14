/**
 * certify-viewports-w12.mjs — 23 TARGET × 4 BỀ RỘNG, MỘT VÒNG ĐỜI SERVER.
 *
 * ─── HỎI GÌ ───────────────────────────────────────────────────────────────
 *
 * `audit-composition.mjs` đã hỏi "cơ chế có trôi trong khung rỗng không" và
 * "hình với chữ có cùng một rail không". Câu hỏi ở đây KHÁC:
 *
 *   Ở bề rộng này, học sinh có DÙNG ĐƯỢC target không?
 *
 * Tức: cơ chế có hiện không · affordance chính có thấy được không · thử thách
 * có đóng sẵn không · có tràn/cắt/chồng không.
 *
 * Nên nó là artifact CHỨNG NHẬN, không phải bản mô tả — và nó dùng lại
 * `browser-runner.mjs` thay vì dựng vòng đời Chrome thứ hai.
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
  new URL("../../docs/evaluation/m20/w12-viewport-matrix.json", import.meta.url)
    .pathname.replace(/^[/]/, "")));
const VIEWPORTS = argOf("--viewports", "1920,1536,1366,768").split(",").map(Number);
mkdirSync(dirname(OUT), { recursive: true });

const MEASURE = `(()=>{
  const card = document.querySelector('.workspace-card');
  if (!card) return JSON.stringify({error:'không thấy .workspace-card'});
  const vis = (el) => { if (!el) return false;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    const r = el.getBoundingClientRect();
    return r.width > 2 && r.height > 2; };

  const stage = card.querySelector('.sim-stage') || card.querySelector('.web-workspace')
    || card.querySelector('.conv-tool');
  /* AFFORDANCE CHÍNH = thứ học sinh bấm/kéo/đổi được, KHÔNG tính thanh điều
     khiển và KHÔNG tính nút thử thách — hai thứ ấy có mặt ở mọi target nên đếm
     chúng sẽ làm phép đo luôn đạt. */
  const notFurniture = (el) => !el.closest('.transport,.player,.predict-bar,.predict-inline');
  const controls = [...card.querySelectorAll(
    'input,select,button,[role=button],[role=switch],[tabindex]')]
    .filter(vis).filter(notFurniture);
  /* Kéo thả trên SVG KHÔNG có thẻ nào trong danh sách trên: cột của ArrayView là
     một rect gắn pointer handler, và React gắn listener ở gốc nên thuộc tính
     không lộ ra DOM. Thứ HỌC SINH thấy được là con trỏ — grab/pointer. Đếm nó
     vừa bắt đúng affordance, vừa là đúng thứ §15 gọi là DISCOVERABLE: một hành
     động không có dấu hiệu mời gọi thì không tính. */
  const cursorCues = [...card.querySelectorAll('svg *')].filter(el => {
    if (!vis(el) || !notFurniture(el)) return false;
    const c = getComputedStyle(el).cursor;
    return c === 'pointer' || c === 'grab' || c === 'grabbing' || c === 'move';
  });
  const affordances = controls.length + cursorCues.length;
  const challengeOpen = vis(card.querySelector('.predict-bar'));

  /* CHỒNG LẤN: sân khấu và khay điều khiển không được đè lên nhau. */
  const dock = document.querySelector('.panel-controls');
  let overlap = false;
  if (stage && dock) {
    const a = stage.getBoundingClientRect(), b = dock.getBoundingClientRect();
    overlap = !(a.bottom <= b.top + 1 || b.bottom <= a.top + 1);
  }
  /* CẮT: svg tràn khỏi cha nó. */
  const clipped = [...card.querySelectorAll('svg')].some(s => {
    const p = s.parentElement; if (!p) return false;
    return s.getBoundingClientRect().right > p.getBoundingClientRect().right + 1;
  });
  return JSON.stringify({
    stageVisible: vis(stage),
    stageH: stage ? Math.round(stage.getBoundingClientRect().height) : 0,
    affordances, controlAffordances: controls.length, dragAffordances: cursorCues.length,
    challengeOpen, overlap, clipped,
    overflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
  });
})()`;

const rows = [];
let totalStarts = 0;
for (const vw of VIEWPORTS) {
  const session = await new BrowserSession({ viewport: vw }).open();
  totalStarts += session.serverStarts;
  const targets = JSON.parse(await session.eval(`(async()=>{
    const c=await import(${JSON.stringify(session.mods.catalog)});
    return JSON.stringify([...new Set(c.offlineCatalog().map(e=>e.simId))].sort());})()`));

  console.log(`\n━━ ${vw}px · khởi động ${session.timings.startup}ms`);
  console.log("  target                          sân khấu  affordance  TT mở  tràn  cắt  chồng  kết luận");
  for (const sim of targets) {
    await session.resetBetweenScenarios();
    const loaded = await session.loadTarget(sim);
    if (loaded !== "ok") {
      console.log(`  ${sim.padEnd(32)} ${loaded}`);
      rows.push({ viewport: vw, target: sim, error: String(loaded), verdict: "KHÔNG ĐO ĐƯỢC" });
      continue;
    }
    await sleep(420);
    const raw = await session.eval(MEASURE);
    if (typeof raw !== "string" || !raw.startsWith("{")) {
      rows.push({ viewport: vw, target: sim, error: `đo hỏng: ${raw}`, verdict: "KHÔNG ĐO ĐƯỢC" });
      continue;
    }
    const m = JSON.parse(raw);
    /* PHÁN QUYẾT — mỗi điều kiện là một câu hỏi riêng, không gộp thành điểm số. */
    const problems = [];
    if (!m.stageVisible) problems.push("sân khấu không hiện");
    /* NGUYÊN NHÂN ĐÃ TRUY ĐƯỢC, ghi đúng tên nó.
       Họ `algorithm` đọc ra 0 affordance vì `whatIfDragAllowed`
       (`interaction-policy.ts`, luật W3B §15) CỐ Ý hoãn kéo khi còn một cam kết
       đang chờ ở bước hiện tại. Đó là hành vi được thiết kế, không phải renderer
       hỏng — nhưng hệ quả cho học sinh là: ở bước mặc định, thứ duy nhất nhìn
       thấy được là ô dự đoán. Gọi nó là "không có affordance" thì mất mất
       nguyên nhân; gọi là "ĐẠT" thì giấu mất hệ quả. */
    if (m.affordances === 0) {
      problems.push(sim.startsWith("algorithm.")
        ? "affordance kéo bị hoãn theo luật cam kết (interaction-policy §15) — bước mặc định chỉ còn ô dự đoán nhìn thấy được"
        : "không có affordance nào ngoài transport");
    }
    if (m.challengeOpen) problems.push("thử thách MỞ SẴN");
    if (m.overflowX) problems.push("tràn ngang");
    if (m.clipped) problems.push("bị cắt");
    if (m.overlap) problems.push("sân khấu chồng khay");
    const verdict = problems.length ? "HỎNG" : "ĐẠT";
    const y = (b) => (b ? " CÓ" : "  ·");
    console.log(`  ${sim.padEnd(32)}${(m.stageVisible ? "  ✔" : "  ✘").padEnd(10)}` +
      `${String(m.affordances).padStart(10)}${y(m.challengeOpen).padStart(7)}` +
      `${y(m.overflowX).padStart(6)}${y(m.clipped).padStart(5)}${y(m.overlap).padStart(7)}  ` +
      `${verdict}${problems.length ? " — " + problems.join(", ") : ""}`);
    rows.push({ viewport: vw, target: sim, ...m, problems, verdict });
  }
  await session.close();
}

const bad = rows.filter((r) => r.verdict !== "ĐẠT");
console.log(`\n  ${rows.length - bad.length}/${rows.length} dòng ĐẠT · ` +
  `${VIEWPORTS.length} vòng đời server (một cho mỗi bề rộng — cửa sổ không đổi kích thước được sau khi mở)`);
for (const b of bad) console.log(`   ✘ ${b.viewport}px ${b.target}: ${(b.problems ?? [b.error]).join(", ")}`);

writeFileSync(OUT, JSON.stringify({
  ...provenance("certify-viewports-w12", { viewports: VIEWPORTS.join(",") }),
  kind: "CERTIFICATION_EVIDENCE",
  question: "Ở bề rộng này, học sinh có DÙNG ĐƯỢC target không?",
  serverStarts: totalStarts,
  passed: rows.length - bad.length, total: rows.length, rows,
}, null, 2), "utf-8");
console.log(`\n→ ${OUT}`);
process.exit(bad.length ? 1 : 0);
