/**
 * faultcheck-visual-weight-w12.mjs — PHÉP ĐO SỨC NẶNG THỊ GIÁC CÓ ĐỎ ĐƯỢC KHÔNG?
 *
 * ─── VÌ SAO CẦN ───────────────────────────────────────────────────────────
 *
 * `certify-visual-weight-w12.mjs` vừa được NỚI ba lần để nhìn thấy canvas, DOM
 * thật, rồi khối HTML của đóng gói giao thức. Mỗi lần nới là một lần phép đo dễ
 * xanh hơn. Sau lần thứ ba nó cho 23/23 — và **một con số đạt sau khi nới tiêu
 * chí thì chưa đáng tin cho tới khi chứng minh nó vẫn đỏ được**.
 *
 * Ba câu hỏi, đúng ba nhánh của NHIỆM VỤ 1–3:
 *
 *   A. Giấu KHỐI CƠ CHẾ thật (.encap-layer) ⇒ phải ĐỎ.
 *   B. Phình một VỎ RỖNG (.encap-2d) ⇒ **không được** thành xanh.
 *   C. Trả lại nguyên trạng ⇒ XANH.
 *
 * Trước mỗi phán quyết phải chứng minh `MUTATION_OBSERVED` — một phép tiêm
 * không chạm tới đối tượng thì kết quả đỏ/xanh của nó vô nghĩa.
 *
 * ⚠️ Backtick KHÔNG được xuất hiện trong biểu thức tiêm vào trang.
 */
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { provenance } from "./evidence.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

const OUT = resolve(new URL("../../docs/evaluation/m20/w12-visual-weight-faults.json",
  import.meta.url).pathname.replace(/^[/]/, ""));
mkdirSync(dirname(OUT), { recursive: true });

const TARGET = "network.protocol_encapsulation";
const MIN_INK_SHARE = 0.15; // cùng ngưỡng với bản chứng nhận

/** CÙNG công thức với bản chứng nhận — nếu lệch thì phép thử này vô nghĩa. */
const INK = `(()=>{
  const card = document.querySelector('.workspace-card');
  if (!card) return JSON.stringify({error:'không thấy .workspace-card'});
  const vis = (el) => { const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    const r = el.getBoundingClientRect(); return r.width > 2 && r.height > 2; };
  const furniture = (el) => el.closest('.transport,.player,.predict-bar,.predict-inline');
  let inkArea = 0, owners = 0;
  for (const g of card.querySelectorAll('svg,canvas,.web-page,.web-preview,.encap-layer,.encap-medium')) {
    if (!vis(g) || furniture(g)) continue;
    const r = g.getBoundingClientRect();
    inkArea += Math.round(r.width * r.height);
    owners += 1;
  }
  const cr = card.getBoundingClientRect();
  return JSON.stringify({ inkArea, owners,
    inkShare: cr.width*cr.height ? +(inkArea/(cr.width*cr.height)).toFixed(3) : 0 });
})()`;

const session = await new BrowserSession({ viewport: 1536 }).open();
await session.loadTarget(TARGET);
await sleep(600);

const rows = [];
const read = async () => JSON.parse(await session.eval(INK));

/* ── ĐỐI CHỨNG C: nguyên trạng ─────────────────────────────────────────── */
const base = await read();
rows.push({ case: "CONTROL", mutation: "không", mutationObserved: true,
  owners: base.owners, inkShare: base.inkShare,
  expected: "GREEN", actual: base.inkShare >= MIN_INK_SHARE ? "GREEN" : "RED" });

/* ── LỖI A: giấu khối cơ chế thật ──────────────────────────────────────── */
const hidA = JSON.parse(await session.eval(`(()=>{
  const els=[...document.querySelectorAll('.encap-layer')];
  const before=els.length;
  for (const e of els) e.style.display='none';
  const after=[...document.querySelectorAll('.encap-layer')]
    .filter(e=>getComputedStyle(e).display!=='none').length;
  return JSON.stringify({before, after});})()`));
await sleep(250);
const faultA = await read();
rows.push({ case: "FAULT_A_hide_mechanism",
  mutation: `.encap-layer display:none (${hidA.before} → ${hidA.after} còn hiện)`,
  mutationObserved: hidA.before > 0 && hidA.after === 0,
  owners: faultA.owners, inkShare: faultA.inkShare,
  expected: "RED", actual: faultA.inkShare >= MIN_INK_SHARE ? "GREEN" : "RED" });

/* ── LỖI B: phình VỎ RỖNG, cơ chế vẫn đang bị giấu ─────────────────────── */
const infl = JSON.parse(await session.eval(`(()=>{
  const w=document.querySelector('.encap-2d');
  if(!w) return JSON.stringify({found:false});
  const b=w.getBoundingClientRect().height;
  w.style.minHeight='900px'; w.style.background='#eef';
  return JSON.stringify({found:true, before:Math.round(b),
    after:Math.round(w.getBoundingClientRect().height)});})()`));
await sleep(250);
const faultB = await read();
rows.push({ case: "FAULT_B_inflate_blank_wrapper",
  mutation: infl.found ? `.encap-2d minHeight ${infl.before} → ${infl.after}` : "không thấy vỏ",
  mutationObserved: Boolean(infl.found && infl.after > infl.before),
  owners: faultB.owners, inkShare: faultB.inkShare,
  expected: "NOT_GREEN", actual: faultB.inkShare >= MIN_INK_SHARE ? "GREEN" : "NOT_GREEN" });

await session.close();

for (const r of rows) {
  console.log(`  ${r.case.padEnd(30)} owners=${String(r.owners).padStart(3)} ` +
    `ink=${String(r.inkShare).padStart(6)}  quan sát=${r.mutationObserved ? "CÓ" : "KHÔNG"}  ` +
    `mong=${r.expected} thực=${r.actual}`);
}
const bad = rows.filter((r) => !r.mutationObserved || r.expected !== r.actual);
console.log(`\n  ${rows.length - bad.length}/${rows.length} đúng kì vọng`);
for (const b of bad) console.log(`   ✘ ${b.case}: mong ${b.expected}, thực ${b.actual}`);

writeFileSync(OUT, JSON.stringify({
  ...provenance("faultcheck-visual-weight-w12", { target: TARGET }),
  kind: "CERTIFICATION_EVIDENCE",
  question: "Phép đo sức nặng thị giác có còn ĐỎ được sau ba lần nới selector không?",
  threshold: MIN_INK_SHARE, rows,
}, null, 2), "utf-8");
console.log(`\n→ ${OUT}`);
process.exit(bad.length ? 1 : 0);
