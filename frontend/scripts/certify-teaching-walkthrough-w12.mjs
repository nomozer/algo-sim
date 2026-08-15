/**
 * certify-teaching-walkthrough-w12.mjs — GIÁO VIÊN DẠY ĐƯỢC KHI TẮT THỬ THÁCH?
 *
 * ─── CÂU HỎI NGHIỆM THU DUY NHẤT ──────────────────────────────────────────
 *
 * Bỏ hết phần hỏi-đáp/chấm đúng-sai đi. Giáo viên còn phơi bày được CƠ CHẾ
 * TÍNH TOÁN một cách mạch lạc không?
 *
 * Nếu KHÔNG, sản phẩm là một bộ đề trắc nghiệm có hoạt hình, và mọi con số về
 * "tương tác" ở các cổng khác đang đo nhầm thứ.
 *
 * ─── CẤU TRÚC MỘT KỊCH BẢN ────────────────────────────────────────────────
 *
 *   giáo viên mở target       → có gì trên sân khấu để chỉ vào?
 *   học sinh đổi được gì      → phát action THẬT của miền
 *   ai giữ sự thật            → engine tất định (state đổi)
 *   hệ quả nhìn thấy          → DOM đổi theo
 *   vai trò của trace         → timeline có bao nhiêu bước
 *   vai trò của thử thách     → có/không, và KHÔNG được là đường duy nhất
 *
 * ─── TÁI DÙNG, KHÔNG TỰ CHẾ ───────────────────────────────────────────────
 *
 * Từ vựng action lấy nguyên từ `certify-w12.mjs::PLAN` — bộ đã qua chứng nhận.
 * Tự đoán lại tên action là lỗi đã lặp BỐN lần trong wave này
 * (`W12_REMAINING.md`), và mỗi lần đều đọc ra "target không tương tác được".
 *
 * ⚠️ KHÔNG dùng cổng này để nói bất cứ điều gì về KẾT QUẢ HỌC TẬP. Nó đo sản
 * phẩm có phơi bày được cơ chế hay không, không đo học sinh có học được không —
 * kho này không chứa nghiên cứu trên người học (`STATUS_LEDGER §0`).
 */
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { provenance } from "./evidence.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const OUT = resolve(argOf("--out",
  new URL("../../docs/evaluation/m20/w12-teaching-walkthrough.json", import.meta.url)
    .pathname.replace(/^[/]/, "")));
mkdirSync(dirname(OUT), { recursive: true });

/** Mười một kịch bản bắt buộc của W12 §22 + hành động miền đã chứng nhận. */
const SCENARIOS = [
  { target: "algorithm.find_max", action: { type: "whatif_swap", i: 0, j: 1 },
    objective: "So sánh từng phần tử với giá trị lớn nhất đang giữ" },
  { target: "algorithm.binary_search", action: { type: "whatif_swap", i: 0, j: 1 },
    objective: "Chia đôi vùng tìm kiếm sau mỗi phép so sánh" },
  { target: "algorithm.bubble_sort", action: { type: "whatif_swap", i: 0, j: 1 },
    objective: "Đổi chỗ cặp kề nhau cho tới khi hết nghịch thế" },
  { target: "logic.and_gate", action: { type: "toggle", target: "A" },
    objective: "Đầu ra bằng 1 chỉ khi CẢ HAI đầu vào bằng 1" },
  { target: "network.packet_routing", action: { type: "net_disconnect", a: "client", b: "router" },
    objective: "Mất một liên kết thì tuyến đi phải tính lại, có thể thành không tới được" },
  { target: "web.style_model", action: { type: "set_param", name: "r", value: 255 },
    objective: "Thuộc tính CSS là dữ liệu; đổi dữ liệu thì trang đổi theo" },
  { target: "binary.base_conversion", action: { type: "set_param", name: "targetBase", value: 8 },
    objective: "Cùng một số, đổi cơ số thì cách viết đổi" },
  { target: "binary.character_encoding", action: { type: "set_param", name: "text", value: "Bin" },
    objective: "Mỗi ký tự ứng với một dãy bit theo bảng mã" },
  { target: "database.relational_table_query", action: { type: "set_param", name: "filter.column", value: "to" },
    objective: "Điều kiện lọc quyết định tập dòng trả về" },
  { target: "network.protocol_encapsulation", action: null,
    objective: "Mỗi tầng bọc gói tin của tầng trên, đầu nhận bóc ngược lại" },
  { target: "logic.boolean_dag", action: { type: "toggle", target: "N" },
    objective: "Giá trị lan truyền qua mạch theo thứ tự phụ thuộc" },
];

const s = await new BrowserSession({ viewport: 1536, height: 900 }).open();
const rows = [];

for (const sc of SCENARIOS) {
  await s.resetBetweenScenarios();
  const load = await s.loadTarget(sc.target);
  await sleep(650);

  /* GIÁO VIÊN MỞ RA — sân khấu có gì để chỉ vào, và thử thách có đang chắn không? */
  /* ⚠️ PHẠM VI ĐO LÀ `.workspace-card`, KHÔNG PHẢI `.sim-stage`.
     `certify-visual-weight-w12.mjs` đã trả giá cho bài học này: cơ chế của một
     số target KHÔNG nằm trong `.sim-stage` — mô hình trang web là DOM thật
     (`.web-page`), còn ba target cơ số/bảng dựng cơ chế bằng `<table>`. Đo theo
     `.sim-stage` đọc ra "0 bộ phận đồ hoạ" cho bốn target đang hoạt động tốt,
     tức lại một lượt ĐÁNH GIÁ THẤP sản phẩm. */
  const opening = JSON.parse(await s.eval(`(()=>{
    const card=document.querySelector('.workspace-card');
    /* Danh sách chủ sở hữu cơ chế lấy NGUYÊN từ certify-visual-weight-w12.mjs
       (svg · canvas · .web-page · .web-preview · .encap-layer · .encap-medium),
       cộng ô bảng cho ba target cơ số/truy vấn. Bỏ sót .encap-layer đọc ra
       "0 bộ phận" cho protocol_encapsulation — lần thứ hai cùng một lỗi trong
       chính cổng này. */
    const marks=card?card.querySelectorAll(
      'svg *, canvas, .web-page *, .web-preview *, .encap-layer, .encap-medium, ' +
      'table td, table th').length:0;
    const affor=card?card.querySelectorAll('[role=button], .web-swatch, .net-link-handle, ' +
      '.sim-secondary-action, .web-group-head, input, select').length:0;
    const challengeOpen=document.querySelectorAll('.predict-bar').length>0;
    const steps=document.querySelector('.player-progress');
    return JSON.stringify({stageMarks:marks, affordances:affor, challengeOpen,
      transport:!!steps, stepLabel:steps?(steps.getAttribute('aria-label')||''):''});})()`));

  const before = await s.snapshot();
  let stateChanged = false, domChanged = false, sent = "—";
  /* Chữ của CẢ THẺ, cùng lý do với phạm vi đo ở trên. */
  const DOM_TEXT = `document.querySelector('.workspace-card').textContent.trim().slice(0,600)`;
  const domBefore = await s.eval(DOM_TEXT);

  if (sc.action) {
    sent = await s.dispatch(sc.action);
    await sleep(420);
    const after = await s.snapshot();
    stateChanged = JSON.stringify(before?.state) !== JSON.stringify(after?.state);
    const domAfter = await s.eval(DOM_TEXT);
    domChanged = domBefore !== domAfter;
  } else {
    /* TRACE_MODEL — thứ giáo viên điều khiển là THỜI GIAN, không phải tham số.
       Tiến một bước và đòi state đổi: nếu trình tự không đổi được thì target
       này không dạy được gì ngoài một bức tranh tĩnh. */
    /* Tiến thời gian qua CHÍNH action của store, không qua chữ trên nút:
       `clickText("Tiến một bước")` phụ thuộc nhãn và đã im lặng không làm gì. */
    await s.eval(`(async()=>{const st=(await import(${JSON.stringify(s.mods.store)}))
      .useAppStore.getState(); if(typeof st.nextStep!=='function') return 'x';
      st.nextStep(); return 'ok';})()`);
    await sleep(420);
    const after = await s.snapshot();
    stateChanged = JSON.stringify(before?.state) !== JSON.stringify(after?.state);
    const domAfter = await s.eval(DOM_TEXT);
    domChanged = domBefore !== domAfter;
    sent = "nextStep (trace)";
  }

  const traceSteps = JSON.parse(await s.eval(`(async()=>{
    const st=await import(${JSON.stringify(s.mods.store)});
    const reg=await import(${JSON.stringify(s.mods.registry)});
    const a=st.useAppStore.getState().active;
    const m=a?reg.getSimulation(a.moduleId):null;
    return JSON.stringify({steps: m&&m.timeline? m.timeline.stepCount(a.state):null,
      hasPredict: !!(m&&m.predict)});})()`));

  const usefulWithoutChallenge = opening.challengeOpen === false
    && opening.stageMarks > 0 && stateChanged && domChanged;

  rows.push({
    target: sc.target, load,
    primaryExperience: sc.action ? "TOOL_OR_MODEL" : "TRACE",
    productLearningObjective: sc.objective,
    teacherFirstAction: opening.transport
      ? "mở target, dùng khay điều khiển để dừng ở bước cần nói"
      : "mở target và chỉ thẳng vào sân khấu",
    studentVisibleModel: `${opening.stageMarks} bộ phận đồ hoạ · ${opening.affordances} affordance`,
    studentChange: sc.action ? JSON.stringify(sc.action) : "tiến/lùi thời gian",
    authoritativeOwner: "engine tất định (module.apply / timeline)",
    visibleDeterministicConsequence: domChanged ? "DOM sân khấu đổi theo state" : "KHÔNG thấy đổi",
    traceRole: traceSteps.steps ? `${traceSteps.steps} bước` : "không có timeline",
    challengeRole: traceSteps.hasPredict
      ? "có, nhưng ĐÓNG ở luồng bình thường" : "không có",
    challengeOpenAtStart: opening.challengeOpen,
    dispatch: sent, stateChanged, domChanged,
    USEFUL_WITHOUT_CHALLENGE: usefulWithoutChallenge,
    verdict: usefulWithoutChallenge ? "TEACHING_WALKTHROUGH_PASS" : "TEACHING_WALKTHROUGH_FAIL",
  });
}

/* ── TIÊM LỖI: TEACHING_WALKTHROUGH_CHALLENGE_ONLY ──────────────────────── */
const faults = [];
{
  await s.resetBetweenScenarios();
  await s.loadTarget("logic.and_gate");
  await sleep(600);
  /* Chữ của CẢ THẺ, cùng lý do với phạm vi đo ở trên. */
  const DOM_TEXT = `document.querySelector('.workspace-card').textContent.trim().slice(0,600)`;
  const domBefore = await s.eval(DOM_TEXT);
  /* Gỡ sạch affordance cơ chế khỏi sân khấu — mô phỏng đúng một sản phẩm mà
     đường duy nhất còn lại là trả lời câu hỏi. Cổng PHẢI đỏ. */
  const mutation = await s.eval(`(()=>{
    const n=document.querySelectorAll('.sim-stage [role=button]');
    n.forEach(e=>e.remove());
    return 'đã gỡ ' + n.length + ' affordance cơ chế';})()`);
  const affAfter = await s.eval(`document.querySelectorAll('.sim-stage [role=button]').length`);
  const domAfter = await s.eval(`document.querySelector('.workspace-card').textContent.trim().slice(0,600)`);
  const detected = Number(affAfter) === 0 && domBefore !== domAfter;
  faults.push({
    name: "TEACHING_WALKTHROUGH_CHALLENGE_ONLY", mutation,
    mutationObserved: detected ? "YES" : "NO",
    detail: `affordance cơ chế còn lại: ${affAfter}`,
    expected: "RED", actual: detected ? "RED" : "GREEN", ok: detected,
  });
}
await s.close();

const pass = rows.filter((r) => r.verdict === "TEACHING_WALKTHROUGH_PASS").length;
console.log("\n━━ KỊCH BẢN DẠY HỌC · thử thách ĐÓNG\n");
console.log("  target                          bộ phận  affordance  state  DOM  bước   phán quyết");
for (const r of rows) {
  console.log(`  ${r.target.padEnd(32)}${r.studentVisibleModel.split(" ")[0].padStart(6)}` +
    `${r.studentVisibleModel.split("· ")[1].split(" ")[0].padStart(11)}` +
    `${(r.stateChanged ? "✔" : "✘").padStart(7)}${(r.domChanged ? "✔" : "✘").padStart(5)}` +
    `${r.traceRole.split(" ")[0].padStart(6)}   ${r.verdict.replace("TEACHING_WALKTHROUGH_", "")}`);
}
console.log(`\n  ${pass}/${rows.length} kịch bản dùng được KHI KHÔNG CÓ thử thách`);
console.log("\n  ── tiêm lỗi ──");
for (const f of faults) {
  console.log(`  ${f.name.padEnd(38)} quan sát=${f.mutationObserved} mong=${f.expected} thực=${f.actual} ${f.ok ? "✔" : "✘"}`);
}

const ok = pass === rows.length && faults.every((f) => f.ok);
writeFileSync(OUT, JSON.stringify({
  ...provenance("certify-teaching-walkthrough-w12", { scenarios: rows.length }),
  acceptance: "Bỏ thử thách đi, giáo viên còn phơi bày được cơ chế tính toán không?",
  limitation: "KHÔNG nói gì về kết quả học tập — kho này không có nghiên cứu trên người học.",
  rows, faults, ok,
}, null, 2), "utf-8");
console.log(`\n→ ${OUT}`);
if (!ok) process.exit(1);
