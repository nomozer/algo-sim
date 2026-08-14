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
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
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
  /* AFFORDANCE dùng phép NHÌN THẤY khác: một số vùng bấm là <line> NGANG, và
     Chrome trả bbox hình học KHÔNG cộng stroke ⇒ 150x0. Đo bằng 'vis' sẽ vứt
     chúng đi và báo 'không có affordance' cho network.packet_routing, vốn có
     đủ ba vùng ngắt liên kết bấm được (đã dò tận nơi). Nên ở đây một CHIỀU lớn
     hơn 2px là đủ — thứ cần biết là có vật thể để trỏ vào hay không. */
  const visTarget = (el) => { if (!el) return false;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    const r = el.getBoundingClientRect();
    return r.width > 2 || r.height > 2; };

  const stage = card.querySelector('.sim-stage') || card.querySelector('.web-workspace')
    || card.querySelector('.conv-tool');
  /* AFFORDANCE CHÍNH = thứ học sinh bấm/kéo/đổi được, KHÔNG tính thanh điều
     khiển và KHÔNG tính nút thử thách — hai thứ ấy có mặt ở mọi target nên đếm
     chúng sẽ làm phép đo luôn đạt. */
  const notFurniture = (el) => !el.closest('.transport,.player,.predict-bar,.predict-inline');
  const controls = [...card.querySelectorAll(
    'input,select,button,[role=button],[role=switch],[tabindex]')]
    .filter(visTarget).filter(notFurniture);
  /* Kéo thả trên SVG KHÔNG có thẻ nào trong danh sách trên: cột của ArrayView là
     một rect gắn pointer handler, và React gắn listener ở gốc nên thuộc tính
     không lộ ra DOM. Thứ HỌC SINH thấy được là con trỏ — grab/pointer. Đếm nó
     vừa bắt đúng affordance, vừa là đúng thứ §15 gọi là DISCOVERABLE: một hành
     động không có dấu hiệu mời gọi thì không tính. */
  const cursorCues = [...card.querySelectorAll('svg *')].filter(el => {
    if (!visTarget(el) || !notFurniture(el)) return false;
    const c = getComputedStyle(el).cursor;
    return c === 'pointer' || c === 'grab' || c === 'grabbing' || c === 'move';
  });
  const affordances = controls.length + cursorCues.length;
  const challengeOpen = vis(card.querySelector('.predict-bar'));

  /* CHỒNG LẤN: sân khấu và khay điều khiển không được đè lên nhau —
     TRỪ KHI khay đang neo (sticky/fixed), vì lúc ấy nổi lên trên nội dung dài
     chính là việc của nó (quyết định W7: học sinh luôn với tới được nút tua).
     Bản đo trước không phân biệt hai ca ấy nên báo HỎNG cho web.style_model ở
     768px — target DUY NHẤT có sân khấu (1453px) cao hơn khung nhìn, tức đúng
     ca mà neo tồn tại để phục vụ. Đó là tiêu chí sai, không phải bố cục sai. */
  const dock = document.querySelector('.panel-controls');
  let overlap = false, dockPinned = false;
  if (stage && dock) {
    const dp = getComputedStyle(dock).position;
    dockPinned = dp === 'sticky' || dp === 'fixed';
    const a = stage.getBoundingClientRect(), b = dock.getBoundingClientRect();
    overlap = !dockPinned && !(a.bottom <= b.top + 1 || b.bottom <= a.top + 1);
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
    challengeOpen, overlap, dockPinned, clipped,
    overflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
  });
})()`;

/**
 * TRACE_MODEL — ĐỌC TỪ BẢNG PHÂN LOẠI, KHÔNG CHÉP TAY.
 *
 * Với target mà `module.apply` là hàm đồng nhất, "0 affordance" là ĐÚNG chứ
 * không phải hỏng: đối tượng học chính là TRÌNH TỰ (W12 §17). Bản đo trước đòi
 * affordance ở mọi target nên đọc ra HỎNG cho cả ba — tiêu chí sai, không phải
 * sản phẩm sai.
 *
 * Bản đầu của khối này là một danh sách viết tay, và nó SAI ngay lần chạy đầu:
 * tôi ghi `tree.traversal` là trace-only trong khi nó có `set_param` chọn thứ
 * tự duyệt. Nên nguồn ở đây là artifact do `interaction-semantics` sinh — nơi
 * phân loại được DÒ TỪ CHÍNH MODULE. Một danh sách người viết là một danh sách
 * sẽ lệch.
 *
 * ⚠️ Ngoại lệ này chỉ CHO PHÉP 0 affordance, KHÔNG cấm có affordance: một
 * TRACE_MODEL vẫn được có nút đổi cách biểu diễn (2D/3D, chọn tầng) — thứ ấy
 * không đổi state nên không mâu thuẫn phân loại.
 */
const SEMANTICS = JSON.parse(readFileSync(resolve(
  new URL("../../docs/evaluation/m20/w12-interaction-semantics.json", import.meta.url)
    .pathname.replace(/^[/]/, "")), "utf-8"));
const TRACE_ONLY = new Set(
  SEMANTICS.rows.filter((r) => r.primaryType === "TRACE_MODEL").map((r) => r.id));
if (TRACE_ONLY.size === 0) {
  throw new Error("bảng phân loại không có TRACE_MODEL nào — artifact hỏng hoặc đổi khoá; " +
    "một tập rỗng ở đây sẽ khiến mọi dòng ĐẠT một cách vô nghĩa");
}
console.log(`  (trace-only đọc từ bảng phân loại: ${[...TRACE_ONLY].join(", ")})`);

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
    /* W12 §6 — nguyên nhân cũ ĐÃ SỬA, nên thông điệp cũ phải đi theo.
       Ở HEAD 99548af, 52/92 dòng đọc ra 0 affordance vì ba nơi cùng chép tay
       luật "công cụ nằm sau cổng Khám phá" (kéo cột · vùng bấm liên kết · thanh
       điều kiện). Nay cả ba đi qua `tool-affordance.ts`. Còn 0 affordance sau
       khi sửa thì đó là phát hiện MỚI, không phải nguyên nhân đã biết — đừng
       dán lại nhãn cũ lên nó. */
    if (m.affordances === 0 && !TRACE_ONLY.has(sim)) {
      problems.push("không có affordance nào ngoài transport");
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
