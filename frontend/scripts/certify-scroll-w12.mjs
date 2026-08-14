/**
 * certify-scroll-w12.mjs — QUYỀN SỞ HỮU CUỘN CỦA VỎ ỨNG DỤNG (W12 §A).
 *
 * ─── HỎI GÌ ───────────────────────────────────────────────────────────────
 *
 * Ảnh chụp thật cho thấy ba triệu chứng: thanh cuộn gần như tàng hình · một khe
 * dọc xấu cạnh header · mép trang và mép header không đọc thành MỘT vỏ liền.
 *
 * ─── KHÔNG ĐẢO QUYẾT ĐỊNH CŨ ───────────────────────────────────────────────
 *
 * Mẫu "vỏ cố định + vùng main tự cuộn" nghe đúng, nhưng W4B-1A đã ĐO và cố ý đi
 * hướng ngược: một vùng cuộn nội bộ giấu mất nội dung học mà không để lại tín
 * hiệu nào ở mức trang (1920×768: 170px bị giấu, `page_scrollable_y` = false ở
 * cả bốn cấu hình). Nên chủ sở hữu cuộn ĐÚNG ở đây vẫn là TÀI LIỆU — và W12 §3
 * nói thẳng: dùng kiến trúc hiện có nếu đã có chủ sở hữu đúng.
 *
 * Vậy khiếm khuyết hẹp hơn nhiều, và đó là thứ script này đo:
 *
 *   1. header có trải hết bề rộng nội dung không (mép liền, không khe);
 *   2. máng giữ chỗ có ỔN ĐỊNH giữa trang ngắn và trang dài không (không nhảy);
 *   3. có tràn ngang không.
 *
 * ⚠️ Thumb có nhìn thấy được không thì KHÔNG đo được ở đây: CDP không đọc được
 * computed style của `::-webkit-scrollbar-thumb`. Việc ấy do
 * `styles/scrollbar-ownership.test.ts` khoá ở mức mã nguồn. Nói rõ ranh giới
 * còn hơn để một con số trông-như-đã-phủ.
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
  new URL("../../docs/evaluation/m20/w12-scroll-shell.json", import.meta.url)
    .pathname.replace(/^[/]/, "")));
const VIEWPORTS = argOf("--viewports", "1920,1536,1366,768").split(",").map(Number);
mkdirSync(dirname(OUT), { recursive: true });

/** Màn phải phủ: ngắn hơn khung nhìn · dài hơn · và một mô phỏng rất dài. */
const SCENES = [
  { id: "home", kind: "ngắn", setup: null },
  { id: "library", kind: "danh sách dài", setup: "library" },
  { id: "history", kind: "danh sách rỗng/ngắn", setup: "history" },
  { id: "workspace-ngắn", kind: "mô phỏng gọn", sim: "algorithm.find_max" },
  { id: "workspace-dài", kind: "mô phỏng rất dài", sim: "web.style_model" },
];

const MEASURE = `(()=>{
  const de = document.documentElement;
  const header = document.querySelector('.nav-bar');
  const hr = header ? header.getBoundingClientRect() : null;
  /* MÁNG = phần khung nhìn mà tài liệu KHÔNG dùng được. Nó phải giống nhau ở
     trang ngắn và trang dài, nếu không nội dung sẽ nhảy ngang khi trang vừa đủ
     dài để cuộn — đúng lỗi 'width jump' mà §5 cấm. */
  const body = document.body.getBoundingClientRect();
  /* MÁNG phải đo bằng BODY, không bằng de.clientWidth.
     'scrollbar-gutter: stable' trên html thu hẹp CONTENT BOX của html, nhưng
     de.clientWidth là padding-box nên KHÔNG phản ánh việc giữ chỗ. Đo sai chỗ
     thì kết luận sai: bản đầu của script này đòi header rộng bằng
     de.clientWidth, tức đòi header phủ luôn cả máng cuộn — điều không một trang
     cuộn-tài-liệu nào làm được. Câu hỏi đúng là header có trải hết VỎ không. */
  const gutter = Math.round(de.clientWidth - body.width);
  return JSON.stringify({
    gutter,
    contentW: Math.round(body.width),
    headerW: hr ? Math.round(hr.width) : 0,
    headerLeft: hr ? Math.round(hr.left) : -1,
    headerSpansContent: hr ? Math.abs(hr.width - body.width) <= 1 : false,
    scrollable: de.scrollHeight > de.clientHeight + 1,
    docH: de.scrollHeight,
    overflowX: de.scrollWidth > de.clientWidth + 1,
  });
})()`;

/* Khai ở `global.css`: `::-webkit-scrollbar { width: 10px }`. Giữ ở đây để
   phép đo có một kì vọng ĐỘC LẬP thay vì chấp nhận bất cứ số nào trang trả về. */
const SCROLLBAR_W = 10;

const rows = [];
let totalStarts = 0;
for (const vw of VIEWPORTS) {
  const session = await new BrowserSession({ viewport: vw }).open();
  totalStarts += session.serverStarts;
  console.log(`\n━━ ${vw}px`);
  console.log("  màn                   máng  nội dung  header  trải hết  cuộn được  cao   tràn");
  for (const sc of SCENES) {
    await session.resetBetweenScenarios();
    if (sc.sim) {
      const loaded = await session.loadTarget(sc.sim);
      if (loaded !== "ok") { rows.push({ viewport: vw, scene: sc.id, error: String(loaded) }); continue; }
    } else if (sc.setup) {
      await session.eval(`(async()=>{
        const s=await import(${JSON.stringify(session.mods.store)});
        s.useAppStore.getState().setView(${JSON.stringify(sc.setup)});
        return 'ok';})()`);
    }
    await sleep(420);
    const raw = await session.eval(MEASURE);
    if (typeof raw !== "string" || !raw.startsWith("{")) {
      rows.push({ viewport: vw, scene: sc.id, error: `đo hỏng: ${raw}` }); continue;
    }
    const m = JSON.parse(raw);
    const problems = [];
    if (!m.headerSpansContent) {
      problems.push(`header rộng ${m.headerW} nhưng vỏ rộng ${m.contentW} — mép hở`);
    }
    /* Máng phải là ĐÚNG bề rộng thanh cuộn đã khai, không phải một khoảng lạ:
       `::-webkit-scrollbar { width: 10px }`. Lệch nghĩa là có phần tử khác đang
       ăn bớt bề rộng, và lúc ấy dải cạnh header đúng là một khe hở thật. */
    if (m.gutter !== SCROLLBAR_W) {
      problems.push(`máng ${m.gutter}px ≠ bề rộng thanh cuộn đã khai ${SCROLLBAR_W}px`);
    }
    if (m.headerLeft !== 0) problems.push(`header lệch trái ${m.headerLeft}px`);
    if (m.overflowX) problems.push("tràn ngang");
    console.log(`  ${sc.id.padEnd(20)}${String(m.gutter).padStart(6)}` +
      `${String(m.contentW).padStart(10)}${String(m.headerW).padStart(8)}` +
      `${(m.headerSpansContent ? " ✔" : " ✘").padStart(10)}` +
      `${(m.scrollable ? " CÓ" : "  ·").padStart(11)}${String(m.docH).padStart(6)}` +
      `${(m.overflowX ? " CÓ" : "  ·").padStart(7)}`);
    rows.push({ viewport: vw, scene: sc.id, kind: sc.kind, ...m, problems,
      verdict: problems.length ? "HỎNG" : "ĐẠT" });
  }
  await session.close();
}

/* KHÔNG NHẢY NGANG: ở mỗi bề rộng, máng của màn CUỘN ĐƯỢC phải bằng máng của
   màn KHÔNG cuộn. So sánh này mới là câu hỏi thật; đo một màn thì không bao giờ
   phát hiện được nhảy. */
const jumps = [];
for (const vw of VIEWPORTS) {
  const at = rows.filter((r) => r.viewport === vw && !r.error);
  const gutters = [...new Set(at.map((r) => r.gutter))];
  if (gutters.length > 1) {
    jumps.push({ viewport: vw, gutters, scenes: at.map((r) => `${r.scene}:${r.gutter}`) });
  }
}

const bad = rows.filter((r) => r.verdict !== "ĐẠT");
console.log(`\n  ${rows.length - bad.length}/${rows.length} dòng ĐẠT · ` +
  `${jumps.length === 0 ? "máng ổn định ở mọi bề rộng (không nhảy ngang)" : "CÓ NHẢY NGANG"}`);
for (const b of bad) console.log(`   ✘ ${b.viewport}px ${b.scene}: ${(b.problems ?? [b.error]).join(", ")}`);
for (const j of jumps) console.log(`   ✘ ${j.viewport}px máng không đồng nhất: ${j.scenes.join(", ")}`);

writeFileSync(OUT, JSON.stringify({
  ...provenance("certify-scroll-w12", { viewports: VIEWPORTS.join(",") }),
  kind: "CERTIFICATION_EVIDENCE",
  question: "Vỏ ứng dụng có đọc thành một khối liền, và máng cuộn có ổn định không?",
  notCoveredHere: "Thumb có nhìn thấy được không — CDP không đọc được computed style của "
    + "::-webkit-scrollbar-thumb. Khoá ở styles/scrollbar-ownership.test.ts.",
  serverStarts: totalStarts,
  passed: rows.length - bad.length, total: rows.length, widthJumps: jumps, rows,
}, null, 2), "utf-8");
console.log(`\n→ ${OUT}`);
process.exit(bad.length || jumps.length ? 1 : 0);
