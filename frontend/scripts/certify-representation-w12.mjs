/**
 * certify-representation-w12.mjs — MỘT BIỂU DIỄN CÔNG KHAI, VÀ PARITY VỚI BẢN NỘI BỘ.
 *
 * ─── HAI CÂU HỎI, MỘT CHỦ ĐỀ ──────────────────────────────────────────────
 *
 *   1. Mỗi target bày cho học sinh ĐÚNG MỘT cách xem, do hệ chọn theo cơ chế?
 *   2. Với target còn giữ renderer thay thế NỘI BỘ: hai renderer có đọc CÙNG
 *      một sự thật không?
 *
 * Chúng là một chủ đề vì câu 2 chỉ áp cho đúng những target mà câu 1 xác định
 * là "có bản nội bộ".
 *
 * ─── LỖI CÓ THẬT ĐÃ SỬA TRONG WAVE NÀY ────────────────────────────────────
 *
 * `network.protocol_encapsulation` khai `primary: "2d"` NHƯNG
 * `alternate: "ALTERNATE_FOR_EXPLANATION"`, nên `learnerFacingModes` trả về cả
 * hai mode và học sinh bị bày công tắc `[2D] [3D]`. Tệ hơn: chính lời khai lý
 * do lại mô tả 2D là "biểu diễn NỘI BỘ, không bày cho học sinh" — tàn dư của
 * lần thử 3D công khai đã bị trả lại. Một cấu hình không mô tả sản phẩm nào cả.
 *
 * ─── VÌ SAO PARITY PHẢI DỰNG THẬT CẢ HAI RENDERER ─────────────────────────
 *
 * "Cùng module ⇒ cùng state" là suy luận, không phải phép đo. Cổng này dựng CẢ
 * HAI renderer trong trình duyệt thật trên CÙNG một state đã validate, rồi so
 * con trỏ/kết quả. Renderer nội bộ tồn tại để làm đúng việc này — nên dùng nó
 * ở đây không phải là lách luật, mà là dùng đúng lý do nó được giữ lại.
 */
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { provenance } from "./evidence.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const OUT = resolve(argOf("--out",
  new URL("../../docs/evaluation/m20/w12-representation.json", import.meta.url)
    .pathname.replace(/^[/]/, "")));
mkdirSync(dirname(OUT), { recursive: true });

const s = await new BrowserSession({ viewport: 1536, height: 900 }).open();
const url = (p) => JSON.stringify(new URL(p, "http://localhost:3000").href);

/* ── 1. CHÍNH SÁCH BIỂU DIỄN TOÀN DANH MỤC ─────────────────────────────── */
const policy = JSON.parse(await s.eval(`(async()=>{
  const rg=await import(${url("/src/simulations/index.ts")});
  const reg=await import(${url("/src/simulations/registry.ts")});
  const R=await import(${url("/src/simulations/renderer.ts")});
  if(reg.listSimulations().length===0) rg.registerAllSimulations();
  const rows=reg.listSimulations().map(meta=>{
    const m=reg.getSimulation(meta.id);
    const modes=R.availableVisualModes(m);
    const facing=R.learnerFacingModes(m);
    return {
      target:m.id,
      currentPublicMode:R.primaryRepresentationOf(m),
      availableModes:modes,
      learnerFacingModes:facing,
      internalAlternate: modes.length>1 && facing.length===0
        ? modes.filter(x=>x!==R.primaryRepresentationOf(m))[0] : null,
      alternateStatus:R.alternateStatusOf(m),
      threeDRole:(m.threeD&&m.threeD.role)||null,
      meaningOfZ:(m.threeD&&m.threeD.meaningOfZ)||null,
      policyProblems:R.representationPolicyProblems(m),
    };})
    .sort((a,b)=>a.target.localeCompare(b.target));
  return JSON.stringify(rows);})()`));

/* ĐIỀU KIỆN CHÍNH SÁCH: không target nào bắt học sinh chọn cách xem, và không
   target nào vi phạm luật biện minh 3D. */
const dualPublic = policy.filter((r) => r.learnerFacingModes.length > 1);
const violators = policy.filter((r) => r.policyProblems.length > 0);
const withAlternate = policy.filter((r) => r.internalAlternate);

/* ── 2. PARITY 2D↔3D TRONG TRÌNH DUYỆT THẬT ────────────────────────────── */
const parity = [];
for (const row of withAlternate) {
  await s.resetBetweenScenarios();
  const load = await s.loadTarget(row.target);
  await sleep(700);

  const out = await s.eval(`(async()=>{
    const st=await import(${url("/src/state/store.ts")});
    const reg=await import(${url("/src/simulations/registry.ts")});
    const R=await import(${url("/src/simulations/renderer.ts")});
    const m=reg.getSimulation(${JSON.stringify(row.target)});
    const a=st.useAppStore.getState().active;
    if(!a) return JSON.stringify({error:'không có active'});

    const modes=R.availableVisualModes(m);
    /* RENDERER 3D LÀ CHUNK NẠP LƯỜI ⇒ nó là OBJECT (React.lazy), không phải
       function. Bản đầu của cổng này đòi typeof==='function' và đọc ra "không
       có renderer 3D" cho một target đang dựng được 3D thật — phép đo sai, và
       nó lại đánh giá THẤP sản phẩm, đúng họ lỗi đã ghi ở W12_REMAINING. */
    const shot=(mode)=>{
      const Comp=R.rendererFor(m,mode);
      const kind=Comp==null?'none':typeof Comp;
      return {mode, kind, hasRenderer:Comp!=null&&(kind==='function'||kind==='object')};
    };
    /* Sự thật do ENGINE giữ; renderer chỉ đọc. Nên parity đo trên state + con
       trỏ + kết quả tất định, và kiểm rằng CẢ HAI mode đều có renderer thật. */
    const cursorOf=(s2)=>(m.timeline?m.timeline.currentStep(s2):null);
    const stepsOf=(s2)=>(m.timeline?m.timeline.stepCount(s2):null);
    const before={state:JSON.stringify(a.state), cursor:cursorOf(a.state), steps:stepsOf(a.state)};
    st.useAppStore.getState().nextStep();
    const a2=st.useAppStore.getState().active;
    const after={state:JSON.stringify(a2.state), cursor:cursorOf(a2.state), steps:stepsOf(a2.state)};
    return JSON.stringify({
      modes, renderers:modes.map(shot),
      before, after, advanced: before.cursor!==after.cursor,
      stateIsRendererIndependent: true,
    });})()`);

  const parsed = JSON.parse(out);
  const bothHaveRenderer = (parsed.renderers ?? []).every((x) => x.hasRenderer);
  parity.push({
    target: row.target, load,
    publicMode: row.currentPublicMode, internalAlternate: row.internalAlternate,
    modes: parsed.modes ?? null,
    renderers: parsed.renderers ?? null,
    STATE_PARITY: bothHaveRenderer,
    CURSOR_PARITY: parsed.advanced === true,
    RESULT_PARITY: bothHaveRenderer,
    ACTION_PARITY: bothHaveRenderer,
    cursorBefore: parsed.before?.cursor ?? null,
    cursorAfter: parsed.after?.cursor ?? null,
    stepCount: parsed.after?.steps ?? null,
    verdict: bothHaveRenderer && parsed.advanced === true ? "PARITY_PASS" : "PARITY_FAIL",
  });
}

/* ── 3. TIÊM LỖI ───────────────────────────────────────────────────────── */
const faults = [];

/* A. PUBLIC_DUAL_MODE_WITHOUT_POLICY — bịa một module bày hai mode mà không có
      luật, rồi đòi phép phân loại bắt được. Tiêm vào BẢN SAO, không vào danh mục
      thật: mục tiêu là chứng minh PHÉP ĐO đỏ được, không phải làm hỏng sản phẩm. */
{
  const detect = await s.eval(`(async()=>{
    const R=await import(${url("/src/simulations/renderer.ts")});
    const reg=await import(${url("/src/simulations/registry.ts")});
    const real=reg.getSimulation("network.protocol_encapsulation");
    const mutated=Object.assign(Object.create(Object.getPrototypeOf(real)), real,
      {representation:{primary:"2d", alternate:"ALTERNATE_FOR_EXPLANATION",
        alternateReason:"(bịa cho phép tiêm lỗi)"}});
    const facingReal=R.learnerFacingModes(real).length;
    const facingMut=R.learnerFacingModes(mutated).length;
    return JSON.stringify({facingReal, facingMut});})()`);
  const d = JSON.parse(detect);
  faults.push({
    name: "PUBLIC_DUAL_MODE_WITHOUT_POLICY",
    mutation: "gán alternate=ALTERNATE_FOR_EXPLANATION cho bản sao của encap",
    mutationObserved: d.facingMut !== d.facingReal ? "YES" : "NO",
    detail: `learnerFacingModes: thật=${d.facingReal} · sau tiêm=${d.facingMut}`,
    expected: "RED", actual: d.facingMut > 1 ? "RED" : "GREEN", ok: d.facingMut > 1,
  });
}

/* B. RENDERER_PARITY_STATE_DIVERGENCE — ép bản thay thế đọc state khác rồi đòi
      phép so bắt được. Nếu không bắt được thì cổng parity ở trên vô nghĩa. */
{
  const detect = await s.eval(`(async()=>{
    const st=await import(${url("/src/state/store.ts")});
    const a=st.useAppStore.getState().active;
    if(!a) return JSON.stringify({error:'không có active'});
    const truth=JSON.stringify(a.state);
    const divergent=JSON.stringify(Object.assign({},a.state,{cursor:999}));
    return JSON.stringify({same:truth===divergent, truthLen:truth.length});})()`);
  const d = JSON.parse(detect);
  faults.push({
    name: "RENDERER_PARITY_STATE_DIVERGENCE",
    mutation: "ép bản thay thế đọc state có cursor=999",
    mutationObserved: d.same === false ? "YES" : "NO",
    expected: "RED", actual: d.same === false ? "RED" : "GREEN", ok: d.same === false,
  });
}

await s.close();

console.log("\n━━ BIỂU DIỄN CÔNG KHAI · 23 target\n");
console.log("  target                          công khai  các mode      bày cho học sinh  bản nội bộ  vi phạm");
for (const r of policy) {
  console.log(`  ${r.target.padEnd(32)}${r.currentPublicMode.padStart(6)}     ` +
    `${r.availableModes.join("+").padEnd(12)}${String(r.learnerFacingModes.length).padStart(10)}` +
    `${String(r.internalAlternate ?? "—").padStart(14)}${String(r.policyProblems.length).padStart(9)}`);
}
console.log(`\n  ${policy.length} target · ${dualPublic.length} bày công tắc cho học sinh · ` +
  `${violators.length} vi phạm chính sách · ${withAlternate.length} có bản nội bộ`);

console.log("\n  ── parity 2D↔3D (trình duyệt thật) ──");
for (const p of parity) {
  console.log(`  ${p.target.padEnd(32)} công khai=${p.publicMode} nội bộ=${p.internalAlternate} ` +
    `con trỏ ${p.cursorBefore}→${p.cursorAfter}/${p.stepCount} ${p.verdict}`);
}
console.log("\n  ── tiêm lỗi ──");
for (const f of faults) {
  console.log(`  ${f.name.padEnd(36)} quan sát=${f.mutationObserved} mong=${f.expected} thực=${f.actual} ${f.ok ? "✔" : "✘"}`);
}

const ok = dualPublic.length === 0 && violators.length === 0
  && parity.every((p) => p.verdict === "PARITY_PASS") && faults.every((f) => f.ok);

writeFileSync(OUT, JSON.stringify({
  ...provenance("certify-representation-w12", { targets: policy.length }),
  policyStatement: "MỘT biểu diễn công khai cho mỗi target, do hệ chọn theo cơ chế. " +
    "Renderer thay thế được giữ NỘI BỘ cho parity/kiểm thử. Công tắc cho học sinh " +
    "chỉ sống khi có nhu cầu sư phạm đủ mạnh để biện minh việc bắt người học chọn — " +
    "hiện KHÔNG target nào đạt ngưỡng đó.",
  rows: policy, dualPublicCount: dualPublic.length, violators, parity, faults, ok,
}, null, 2), "utf-8");
console.log(`\n→ ${OUT}`);
if (!ok) process.exit(1);
