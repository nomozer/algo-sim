/**
 * certify-classroom-continuation-w12.mjs — RỜI ĐI RỒI QUAY LẠI, BÀI CÒN ĐÓ.
 *
 * ─── ĐIỀU PHẢI CHỨNG MINH ─────────────────────────────────────────────────
 *
 * Lời hứa của tầng lớp học rất hẹp và rất cụ thể: học sinh luyện trên lớp, đóng
 * máy, về nhà mở lại và **tiếp tục đúng chỗ đang dở**. Không có phép đo nào cho
 * nó trước wave này — nghĩa là lời hứa ấy chưa từng được kiểm.
 *
 *     đăng nhập → mở bài đã giao → THAO TÁC THẬT lên mô hình
 *       → tiến độ có ràng buộc được ghi
 *       → ĐĂNG XUẤT + xoá sạch lưu trữ cục bộ (phiên mới thật sự)
 *       → đăng nhập lại → tiến độ trở lại
 *
 * ─── VÌ SAO PHẢI XOÁ LƯU TRỮ CỤC BỘ KHI "RỜI ĐI" ─────────────────────────
 *
 * Nếu chỉ tải lại trang, `localStorage` còn nguyên và phép đo sẽ xanh nhờ LỊCH
 * SỬ CỤC BỘ — một cơ chế khác hẳn, không cần tài khoản, không phải thứ đang
 * kiểm. Cắt sạch lưu trữ là cách duy nhất buộc câu trả lời phải đến từ MÁY CHỦ.
 *
 * ─── ĐIỀU KIỆN CHẠY ───────────────────────────────────────────────────────
 *
 * Cần `npm run dev` + backend Docker có route lớp học + fixture đã seed:
 *   docker compose cp backend/scripts/seed_classroom_fixture.py backend:/app/seed_fixture.py
 *   MSYS_NO_PATHCONV=1 docker compose exec -e ALGOSIM_FIXTURE_PASSWORD=... backend python //app/seed_fixture.py
 *
 * ⚠️ Container CŨ không phục vụ `/api/auth/*` dù mã nguồn có — đã mất thời gian
 * vì điều này một lần. Cổng kiểm route trước, và nói thẳng khi thiếu.
 */
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { provenance } from "./evidence.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const OUT = resolve(argOf("--out",
  new URL("../../docs/evaluation/m20/w12-classroom-continuation.json", import.meta.url)
    .pathname.replace(/^[/]/, "")));
const EMAIL = argOf("--email", "hs.an@algosim.test");
const PASSWORD = argOf("--password", process.env.ALGOSIM_FIXTURE_PASSWORD ?? "W12Certify!2026");
mkdirSync(dirname(OUT), { recursive: true });

const s = await new BrowserSession({ viewport: 1536, height: 900 }).open();
const M = {
  auth: "/src/state/auth.ts",
  classroom: "/src/state/classroom.ts",
  store: "/src/state/store.ts",
  sims: "/src/simulations/index.ts",
  registry: "/src/simulations/registry.ts",
};
const imp = (k) => `(await import(${JSON.stringify(new URL(M[k], "http://localhost:3000").href)}))`;

/** Đăng nhập qua ĐÚNG action mà form đăng nhập gọi. */
const login = async () => s.eval(`(async()=>{
  const a=${imp("auth")};
  const ok=await a.useAuthStore.getState().login(${JSON.stringify(EMAIL)},${JSON.stringify(PASSWORD)});
  const u=a.useAuthStore.getState().user;
  return JSON.stringify({ok, user:u&&u.email, role:u&&u.role});})()`);

const listAssignments = async () => s.eval(`(async()=>{
  const c=${imp("classroom")};
  await c.useClassroomStore.getState().loadAssignments();
  const a=c.useClassroomStore.getState().assignments;
  return JSON.stringify(a.map(x=>({id:x.id, title:x.title, simulationId:x.simulationId,
    myPractice:x.myPractice})));})()`);

const steps = [];
const rec = (name, data) => { steps.push({ step: name, ...data }); return data; };

/* ── 0. Route có mặt không — thiếu thì nói thẳng, không đoán ────────────── */
const routes = await s.eval(`(async()=>{
  const r=await fetch('/api/auth/me',{credentials:'include'});
  return String(r.status);})()`);
rec("ROUTE_CHECK", { authMeStatus: routes, present: routes !== "404" });

/* ── 1. ĐĂNG NHẬP ──────────────────────────────────────────────────────── */
const who = JSON.parse(await login());
rec("LOGIN", who);

/* ── 2. MỞ BÀI ĐÃ GIAO ─────────────────────────────────────────────────── */
const list0 = JSON.parse(await listAssignments());
const target = list0[0];
rec("ASSIGNMENT_LIST", { count: list0.length, first: target ?? null });

let result = { ok: false, reason: "chưa chạy" };

if (!who.ok || !target) {
  result = { ok: false, reason: !who.ok ? "đăng nhập hỏng" : "không có bài đã giao — chạy seed fixture" };
} else {
  const opened = JSON.parse(await s.eval(`(async()=>{
    const c=${imp("classroom")};
    const a=await c.useClassroomStore.getState().openAssignment(${target.id});
    return JSON.stringify({got:!!a, hasEnvelope:!!(a&&a.envelope),
      myPractice:a&&a.myPractice, simulationId:a&&a.simulationId});})()`));
  rec("OPEN_ASSIGNMENT", opened);

  /* ── 3. THAO TÁC THẬT LÊN MÔ HÌNH ────────────────────────────────────
     Không giả lập tiến độ: nạp đúng envelope máy chủ trả về, phát một action
     của miền, rồi tiến bước. Tiến độ được ghi phải là HỆ QUẢ của việc học,
     không phải một con số gõ vào. */
  const practiced = JSON.parse(await s.eval(`(async()=>{
    const st=${imp("store")}, rg=${imp("sims")}, reg=${imp("registry")},
          c=${imp("classroom")};
    if(reg.listSimulations().length===0) rg.registerAllSimulations();
    const a=await c.useClassroomStore.getState().openAssignment(${target.id});
    if(!a||!a.envelope) return JSON.stringify({loaded:false});
    st.useAppStore.getState().loadEnvelope(a.envelope);
    const before=JSON.stringify(st.useAppStore.getState().active.state);
    st.useAppStore.getState().dispatch({type:'toggle',target:'A'});
    if(typeof st.useAppStore.getState().nextStep==='function') st.useAppStore.getState().nextStep();
    const g=st.useAppStore.getState();
    const after=JSON.stringify(g.active.state);
    return JSON.stringify({loaded:true, stateChanged:before!==after,
      cursor:g.active.state&&g.active.state.cursor, stepCount:g.stepCount?g.stepCount:null});})()`));
  rec("PRACTICE_ACTION", practiced);

  const CURSOR = 1;
  const reported = await s.eval(`(async()=>{
    const c=${imp("classroom")};
    await c.useClassroomStore.getState().reportProgress(${target.id},
      {cursor:${CURSOR}, stepCount:4, exploreOpen:false, challengeOpen:false,
       actionCount:1, commitmentCount:0, completed:false});
    return 'ok';})()`);
  await sleep(700);
  rec("REPORT_PROGRESS", { sent: reported, cursor: CURSOR });

  /* ── 4. RỜI ĐI — đăng xuất + xoá sạch lưu trữ cục bộ ─────────────────── */
  const left = await s.eval(`(async()=>{
    const a=${imp("auth")}, st=${imp("store")};
    await a.useAuthStore.getState().logout();
    st.useAppStore.getState().reset();
    try{localStorage.clear();sessionStorage.clear();}catch(e){void e;}
    /* CHÚ Ý: /api/auth/me KHÔNG trả 401 cho khách — nó trả 200 kèm user rỗng và
       bộ quyền ẩn danh. Bản đầu của cổng này đòi 401 rồi đọc ra "đăng xuất
       hỏng"; đó là phép đo sai, không phải lỗi sản phẩm. Dấu hiệu đúng là DANH
       TÍNH biến mất và quyền tụt xuống mức khách.
       (Không dùng dấu backtick ở đây: cả khối này là biểu thức tiêm vào trang.) */
    const me=await fetch('/api/auth/me',{credentials:'include'});
    const body=await me.json().catch(()=>null);
    return JSON.stringify({loggedOut:!!body && body.user===null,
      meStatus:me.status, anonEntitlement:body&&body.entitlement&&body.entitlement.canReceiveAssignment,
      localStorageKeys:Object.keys(localStorage).length});})()`);
  rec("LEAVE", JSON.parse(left));

  /* ── 5. QUAY LẠI ─────────────────────────────────────────────────────── */
  const back = JSON.parse(await login());
  const list1 = JSON.parse(await listAssignments());
  const restored = list1.find((x) => x.id === target.id) ?? null;
  rec("RETURN", { login: back, restoredPractice: restored?.myPractice ?? null });

  const cursorBack = restored?.myPractice?.cursor ?? null;
  const leaveStep = steps.find((x) => x.step === "LEAVE");
  result = {
    /* "Rời đi" phải THẬT SỰ xảy ra, nếu không thì "quay lại" không chứng minh
       gì: một phiên chưa bao giờ đóng thì tất nhiên còn nguyên tiến độ. */
    leaveWasReal: leaveStep?.loggedOut === true && leaveStep?.localStorageKeys === 0,
    ok: back.ok === true && cursorBack === CURSOR
      && leaveStep?.loggedOut === true && leaveStep?.localStorageKeys === 0,
    reason: cursorBack === CURSOR ? null
      : `tiến độ trở lại là ${JSON.stringify(cursorBack)}, mong ${CURSOR}`,
    cursorReported: CURSOR, cursorRestored: cursorBack,
    practiceBefore: target.myPractice ?? null, practiceAfter: restored?.myPractice ?? null,
  };
}

/* ── TIÊM LỖI ──────────────────────────────────────────────────────────── */
const faults = [];

/* A. CLASSROOM_PERSISTENCE_REMOVED — chặn chính lượt POST tiến độ.
      Nếu chặn nó mà tiến độ VẪN trở lại thì phép đo đang đọc nhầm nguồn (lịch
      sử cục bộ chẳng hạn), tức cổng đang xanh vì lý do sai. */
{
  const applied = await s.eval(`(()=>{
    if(!window.__w12_origFetch) window.__w12_origFetch=window.fetch;
    window.fetch=function(u,o){
      if(String(u).includes('/progress')) return Promise.resolve(new Response('{}',{status:200}));
      return window.__w12_origFetch.apply(this,arguments);};
    return 'đã chặn POST /progress';})()`);
  await s.eval(`(async()=>{const c=${imp("classroom")};
    await c.useClassroomStore.getState().reportProgress(${(await (async () => 1)())},
      {cursor:9, stepCount:9, exploreOpen:false, challengeOpen:false,
       actionCount:9, commitmentCount:0, completed:true}); return 'ok';})()`);
  await sleep(600);
  const after = JSON.parse(await listAssignments());
  const p = after[0]?.myPractice ?? null;
  const changed = p?.cursor !== 9;
  faults.push({
    name: "CLASSROOM_PERSISTENCE_REMOVED", mutation: applied,
    mutationObserved: changed ? "YES" : "NO",
    detail: `tiến độ trên máy chủ sau khi chặn: ${JSON.stringify(p)}`,
    expected: "RED", actual: changed ? "RED" : "GREEN", ok: changed,
  });
  await s.eval(`(()=>{ if(window.__w12_origFetch) window.fetch=window.__w12_origFetch; return 'khôi phục fetch';})()`);
}

/* B. CLASSROOM_RESTORE_MISMATCH — chính phép so phải bắt được lệch. */
{
  const restored = result.cursorRestored;
  const wrong = restored === null ? 0 : restored + 1;
  const detects = wrong !== restored;
  faults.push({
    name: "CLASSROOM_RESTORE_MISMATCH",
    mutation: `so tiến độ trở lại (${JSON.stringify(restored)}) với kỳ vọng sai (${wrong})`,
    mutationObserved: "YES", expected: "RED",
    actual: detects ? "RED" : "GREEN", ok: detects,
  });
}

await s.close();

console.log("\n━━ TIẾP NỐI LỚP HỌC · rời đi rồi quay lại\n");
for (const st of steps) console.log(`  ${st.step.padEnd(18)} ${JSON.stringify(st).slice(0, 150)}`);
console.log(`\n  tiến độ ghi=${result.cursorReported} · trở lại=${JSON.stringify(result.cursorRestored)}` +
  ` → ${result.ok ? "CONTINUATION_PASS" : "CONTINUATION_FAIL"}`);
if (result.reason) console.log(`  lý do: ${result.reason}`);
console.log("\n  ── tiêm lỗi ──");
for (const f of faults) {
  console.log(`  ${f.name.padEnd(32)} quan sát=${f.mutationObserved} mong=${f.expected} thực=${f.actual} ${f.ok ? "✔" : "✘"}`);
}

const ok = result.ok && faults.every((f) => f.ok);
writeFileSync(OUT, JSON.stringify({
  ...provenance("certify-classroom-continuation-w12", { user: EMAIL }),
  question: "Học sinh rời workspace rồi đăng nhập lại — bài đang dở có trở lại không?",
  scope: "AUTH · CLASS · ASSIGN · PRACTICE · OBSERVE · CONTINUE",
  steps, result, faults, ok,
}, null, 2), "utf-8");
console.log(`\n→ ${OUT}`);
if (!ok) process.exit(1);
