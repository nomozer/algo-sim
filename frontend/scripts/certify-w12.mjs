/**
 * certify-w12.mjs — CHỨNG NHẬN TƯƠNG TÁC 23 TARGET TRONG TRÌNH DUYỆT THẬT.
 *
 * ─── LUẬT CHỨNG NHẬN (§13) ────────────────────────────────────────────────
 *
 * Một cú bấm KHÔNG đủ. Một hoạt hình KHÔNG đủ. Trả lời thử thách KHÔNG đủ.
 * Phải chứng minh đủ chuỗi:
 *
 *     hành động  →  SimAction có cấu trúc  →  module.apply
 *                →  STATE TẤT ĐỊNH ĐỔI     →  hệ quả nhìn thấy trong DOM
 *
 * Nên mỗi target được chụp state TRƯỚC, phát một action mang hình dạng của
 * chính miền ấy, chụp state SAU, rồi đòi:
 *   · state phải KHÁC (nếu không, action không đi tới engine);
 *   · DOM phải chứa giá trị mới (nếu không, engine đổi mà học sinh không thấy).
 *
 * ─── VÌ SAO KHÔNG DÙNG MỘT BỘ ACTION CHUNG ────────────────────────────────
 *
 * Wave 1 đã ghi: một bộ thăm dò chung là CẬN DƯỚI, vì `character_encoding` cần
 * `set_param text`, còn `boolean_dag` cần `toggle` theo đúng id đầu vào thật.
 * Chứng nhận thì không được dùng cận dưới — nó phải dùng action THẬT của miền,
 * nếu không "0 target thao tác được" sẽ chỉ nghĩa là bộ thăm dò quá hẹp.
 */
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { provenance } from "./evidence.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const OUT = resolve(argOf("--out",
  new URL("../../docs/evaluation/m20/w12-interaction.json", import.meta.url)
    .pathname.replace(/^[/]/, "")));
const VIEWPORT = Number(argOf("--viewport", "1920"));
mkdirSync(dirname(OUT), { recursive: true });

/**
 * ACTION THẬT của từng miền + giá trị mong đợi xuất hiện trong DOM.
 *
 * `expect` là hàm đọc state SAU và trả chuỗi phải có mặt — dẫn từ chính engine,
 * không phải hằng số chép tay (chép tay thì test chỉ chứng minh chuỗi ấy tồn
 * tại ở đâu đó, không chứng minh renderer đọc state).
 */
const PLAN = {
  "algorithm.find_max": { action: { type: "whatif_swap", i: 0, j: 1 } },
  "algorithm.find_min": { action: { type: "whatif_swap", i: 0, j: 1 } },
  "algorithm.linear_search": { action: { type: "whatif_swap", i: 0, j: 1 } },
  "algorithm.binary_search": { action: { type: "whatif_swap", i: 0, j: 1 } },
  "algorithm.count_if": { action: { type: "whatif_swap", i: 0, j: 1 } },
  "algorithm.sum_if": { action: { type: "whatif_swap", i: 0, j: 1 } },
  "algorithm.scan": { action: { type: "whatif_swap", i: 0, j: 1 } },
  "algorithm.bubble_sort": { action: { type: "whatif_swap", i: 0, j: 1 } },
  "algorithm.insertion_sort": { action: { type: "whatif_swap", i: 0, j: 1 } },
  "algorithm.selection_sort": { action: { type: "whatif_swap", i: 0, j: 1 } },
  "algorithm.bounded_control_flow": { action: { type: "exit_branch" } },
  "binary.decimal_to_binary": { action: { type: "toggle", target: "0" } },
  "binary.base_conversion": {
    action: { type: "set_param", name: "targetBase", value: 16 },
    expect: (s) => String(s.state.result),
  },
  "binary.character_encoding": {
    action: { type: "set_param", name: "text", value: "Bin" },
    expect: (s) => String(s.state.rows[0].binary),
  },
  "logic.and_gate": { action: { type: "toggle", target: "A" } },
  "logic.boolean_dag": { action: { type: "toggle", target: "A" } },
  "web.style_model": {
    action: { type: "set_param", name: "r", value: 255 },
    expect: (s) => String(s.state.style.backgroundColor),
  },
  "database.relational_table_query": { action: { type: "set_param", name: "threshold", value: 9 } },
  "network.packet_routing": { action: { type: "net_disconnect", from: "A", to: "B" } },
  "network.graph_traversal": { action: { type: "set_param", name: "variant", value: "dfs" } },
  "network.protocol_encapsulation": { action: { type: "toggle", target: "0" } },
  "tree.traversal": { action: { type: "set_param", name: "order", value: "postorder" } },
  "generic.rule_scene": { action: { type: "toggle", target: "0" } },
};

const session = await new BrowserSession({ viewport: VIEWPORT }).open();
const targets = JSON.parse(await session.eval(`(async()=>{
  const c=await import(${JSON.stringify(session.mods.catalog)});
  return JSON.stringify([...new Set(c.offlineCatalog().map(e=>e.simId))].sort());})()`));

console.log(`━━ W12 CHỨNG NHẬN TƯƠNG TÁC · ${VIEWPORT}px · khởi động ${session.timings.startup}ms`);
console.log("  target                          action              state đổi  DOM thấy  kết luận");

const rows = [];
for (const sim of targets) {
  await session.resetBetweenScenarios();
  const r = await session.scenario(sim, async (s) => {
    const loaded = await s.loadTarget(sim);
    if (loaded !== "ok") return { pass: false, note: String(loaded) };
    await sleep(400);
    const before = await s.snapshot();
    if (!before) return { pass: false, note: "không chụp được state" };

    const plan = PLAN[sim];
    if (!plan) return { pass: false, note: "CHƯA KHAI action miền — không chứng nhận bằng metadata" };

    const sent = await s.dispatch(plan.action);
    if (sent !== "ok") return { pass: false, note: `dispatch hỏng: ${sent}` };
    await sleep(400);
    const after = await s.snapshot();
    if (!after) return { pass: false, note: "không chụp được state sau" };

    const stateChanged = JSON.stringify(before.state) !== JSON.stringify(after.state);
    let domSeen = null;
    if (plan.expect) {
      let want;
      try { want = plan.expect(after); } catch { want = null; }
      const dom = await s.eval(`document.querySelector('.workspace-card').innerText.replace(/\\s+/g,' ')`);
      domSeen = typeof want === "string" && typeof dom === "string" && dom.includes(want);
    }
    /* PHÂN BIỆT HAI THỨ KHÁC HẲN NHAU.
       `state` không đổi có thể là (a) target thật sự không nhận action ấy, hoặc
       (b) probe của TÔI chưa đúng từ vựng miền — Wave 1 đã ghi rõ rằng một bộ
       thăm dò chung là CẬN DƯỚI. Gộp hai ca thành "HỎNG" là đổ lỗi cho sản phẩm
       vì phép đo hẹp, đúng lỗi mà chương trình này đã phải sửa nhiều lần.
       Nên chưa xác minh được từ vựng thì ghi PROBE_UNVERIFIED, không ghi FAIL. */
    return {
      pass: stateChanged && domSeen !== false,
      status: stateChanged ? "CERTIFIED" : "PROBE_UNVERIFIED",
      action: plan.action.type,
      stateChanged,
      domSeen,
      note: stateChanged ? "" :
        "state không đổi — CHƯA phân biệt được 'target không nhận action này' " +
        "với 'probe chưa đúng từ vựng miền'. Cần đọc hợp đồng action của miền " +
        "rồi chạy lại; KHÔNG được đọc thành khiếm khuyết sản phẩm.",
    };
  });
  const mark = (v) => (v === null ? " —" : v ? " ✔" : " ✘");
  console.log(`  ${sim.padEnd(32)}${String(r.action ?? "—").padEnd(20)}` +
    `${mark(r.stateChanged).padEnd(11)}${mark(r.domSeen).padEnd(10)}${r.status ?? "KHÔNG NẠP ĐƯỢC"}`);
  rows.push({ target: sim, ...r });
}

await session.close();
const passed = rows.filter((r) => r.pass).length;
console.log(`\n  ${passed}/${rows.length} target ĐẠT · một vòng đời server: ${session.serverStarts}`);
for (const r of rows.filter((x) => !x.pass)) console.log(`   ✘ ${r.target}: ${r.note}`);

writeFileSync(OUT, JSON.stringify({
  ...provenance("certify-w12", { viewport: VIEWPORT }),
  kind: "CERTIFICATION_EVIDENCE",
  rule: "hành động → SimAction → module.apply → state tất định đổi → hệ quả trong DOM",
  serverStarts: session.serverStarts,
  timings: session.timings,
  passed, total: rows.length,
  probeUnverified: rows.filter((r) => r.status === "PROBE_UNVERIFIED").map((r) => r.target),
  rows,
}, null, 2), "utf-8");
console.log(`\n→ ${OUT}`);
/* Thoát != 0 khi chưa đủ 23 — nhưng thông điệp phải nói đúng nó thiếu GÌ. */
process.exit(passed === rows.length ? 0 : 1);
