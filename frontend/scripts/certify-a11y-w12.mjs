/**
 * certify-a11y-w12.mjs — KHẢ NĂNG TIẾP CẬN, ĐO BẰNG PHÍM THẬT.
 *
 * ─── VÌ SAO VITEST KHÔNG ĐỦ ───────────────────────────────────────────────
 *
 * Trong kho có sẵn nhiều assertion `aria-*` / `tabIndex` ở tầng vitest. Chúng
 * kiểm rằng THUỘC TÍNH được viết ra, không kiểm rằng người dùng bàn phím ĐI
 * ĐƯỢC. Ba thứ chỉ hiện ra trên trình duyệt thật:
 *
 *   · một `<g>` có `tabIndex` vẫn có thể nằm ngoài tab order nếu bị `display:none`
 *     hay bị phủ;
 *   · vòng tiêu điểm là kết quả CSS (`:focus-visible`), không phải thuộc tính;
 *   · Space vừa là "kích hoạt" vừa là phím tắt TỰ CHẠY toàn cục — chỉ sự kiện
 *     thật mới lộ ra rằng một cú Space làm HAI việc.
 *
 * ─── LỖI CÓ THẬT ĐÃ TÌM RA KHI DỰNG CỔNG NÀY ──────────────────────────────
 *
 * Đo ở `1536px`, `logic.and_gate`: 13 phần tử focus được trên màn, KHÔNG cái
 * nào là công tắc A hoặc B — tức toàn bộ THAO TÁC MÔ HÌNH của target nằm ngoài
 * bàn phím. Cùng họ ở `binary.decimal_to_binary` và `generic.rule_scene`. Đã
 * sửa bằng `simulations/svg-affordance.ts`; cổng này giữ cho nó không quay lại.
 *
 * ─── PHÉP ĐO LÀ "KÍCH HOẠT ĐƯỢC", KHÔNG PHẢI "CÓ THUỘC TÍNH" ──────────────
 *
 * Mỗi ca đòi đủ chuỗi: focus bằng bàn phím → Enter thật → STATE TẤT ĐỊNH ĐỔI.
 * Chỉ đọc thuộc tính thì một affordance khai `role="button"` mà quên `onKeyDown`
 * vẫn qua cửa — và đó đúng là hình dạng của lỗi vừa sửa.
 */
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { provenance } from "./evidence.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const OUT = resolve(argOf("--out",
  new URL("../../docs/evaluation/m20/w12-a11y.json", import.meta.url)
    .pathname.replace(/^[/]/, "")));
mkdirSync(dirname(OUT), { recursive: true });

/**
 * SÁU LOẠI BỀ MẶT theo yêu cầu W12 §19 — mỗi loại một đại diện.
 *
 * `stageSel` trỏ tới affordance CƠ CHẾ (thứ dạy bài học), không phải nút điều
 * khiển chung: khay transport đã có `<button>` thật và chưa bao giờ là chỗ hỏng.
 */
const CASES = [
  { kind: "INTERACTIVE_MODEL", target: "logic.and_gate",
    stageSel: '.sim-stage [role="button"]', expectPressed: true },
  { kind: "INTERACTIVE_MODEL", target: "logic.boolean_dag",
    stageSel: '.sim-stage [role="button"]', expectPressed: false },
  { kind: "BOUNDED_PARAMETER_TOOL", target: "binary.decimal_to_binary",
    stageSel: '.sim-stage [role="button"]', expectPressed: true },
  { kind: "NETWORK_INTERACTION", target: "network.packet_routing",
    stageSel: ".net-link-handle", expectPressed: false },
  { kind: "HTML_DIRECT_MANIPULATION", target: "web.style_model",
    stageSel: ".web-swatch", expectPressed: true },
  { kind: "TRACE_MODEL", target: "network.protocol_encapsulation",
    stageSel: null, expectPressed: false },
];

const s = await new BrowserSession({ viewport: 1536, height: 900 }).open();
const rows = [];

/**
 * Ảnh chụp một phần tử.
 *
 * ⚠️ BA LẦN SỬA PHÉP ĐO, cả ba đều ĐÁNH GIÁ THẤP sản phẩm — đúng họ lỗi đã ghi
 * ở `W12_REMAINING.md` ("khi bản soát báo có lỗi, nghi phép đo trước"):
 *
 *   1. Tên: bản đầu chỉ đọc `aria-label`/`textContent`, nên khay điều khiển
 *      dùng `title="Về đầu"` bị đọc thành KHÔNG TÊN. `title` là nguồn tên dự
 *      phòng hợp lệ theo HTML-AAM — bỏ nó là bịa ra một lỗi không có thật.
 *   2. Bàn phím: bản đầu đòi `role="button"` + `tabindex="0"`, nên `<button>`
 *      GỐC (`.web-swatch`) bị xếp "không tới được bằng bàn phím" — trong khi nó
 *      là thứ tới được tốt nhất có thể.
 *   3. Tiêu điểm: xem mục `focusVisible` bên dưới.
 */
const NAME_OF = `(e)=>((e.getAttribute('aria-label')||e.getAttribute('title')||
  (e.querySelector&&e.querySelector('title')&&e.querySelector('title').textContent)||
  (e.labels&&e.labels.length?e.labels[0].textContent:'')||
  (e.textContent||'')).trim())`;

const NATIVE_FOCUSABLE = "button,a[href],input,select,textarea,summary";

const INSPECT = (sel) => `(()=>{
  const name=${NAME_OF};
  const e=document.querySelector(${JSON.stringify(sel)});
  if(!e) return JSON.stringify({found:false});
  const r=e.getBoundingClientRect(), cs=getComputedStyle(e);
  return JSON.stringify({found:true, name:name(e), role:e.getAttribute('role'),
    tabindex:e.getAttribute('tabindex'),
    nativeFocusable:e.matches(${JSON.stringify(NATIVE_FOCUSABLE)}),
    pressed:e.getAttribute('aria-pressed'),
    w:Math.round(r.width), h:Math.round(r.height),
    outlineStyle:cs.outlineStyle, outlineWidth:cs.outlineWidth,
    shadow:cs.boxShadow.slice(0,40), focused:document.activeElement===e});})()`;

for (const c of CASES) {
  await s.resetBetweenScenarios();
  const load = await s.loadTarget(c.target);
  await sleep(750);

  const row = { target: c.target, kind: c.kind, load };

  if (c.stageSel) {
    const before = JSON.parse(await s.eval(INSPECT(c.stageSel)));
    row.affordance = c.stageSel;
    row.found = before.found;
    if (before.found) {
      row.accessibleName = before.name;
      row.ACCESSIBLE_NAME = before.name.length > 0;
      /* `<button>` gốc tới được bằng bàn phím mà không cần khai gì thêm; một
         hình SVG thì phải TỰ nối `role` + `tabindex`. Hai đường đều hợp lệ. */
      row.KEYBOARD_REACHABLE = before.nativeFocusable
        || (before.role === "button" && before.tabindex === "0");
      /* Trạng thái không được chỉ nằm ở MÀU. `aria-pressed` là đường đọc được;
         với affordance không phải công tắc (liên kết mạng) thì nhãn tự mang
         trạng thái ("Ngắt liên kết …"), nên điều kiện là "có MỘT trong hai". */
      row.STATE_NOT_COLOR_ONLY = c.expectPressed
        ? before.pressed !== null
        : before.name.length > 0;
      row.hitW = before.w; row.hitH = before.h;

      /* VÒNG TIÊU ĐIỂM — TIÊU CHÍ DƯƠNG, KHÔNG PHẢI "CÓ GÌ ĐÓ ĐỔI".
       *
       * Bản đầu chỉ so CSS trước/sau và coi "khác nhau" là đạt. Nó xanh cho
       * `boolean_dag` trong khi `outline-style` của target ấy là `none` ở CẢ HAI
       * lần đo — tức cổng xanh vì một khác biệt không liên quan. Một cổng xanh
       * nhầm còn tệ hơn không có cổng.
       *
       * Nay đòi thẳng: sau khi focus, `outline-style` KHÁC `none`. Và phải bấm
       * một phím THẬT trước, vì `:focus-visible` chỉ khớp khi trình duyệt đang ở
       * chế độ bàn phím — `.focus()` bằng script sau một lượt chuột thì không
       * khớp, và cổng sẽ đỏ oan. */
      await s.pressKey("Tab");
      const focusRes = await s.focusSelector(c.stageSel);
      await sleep(120);
      const after = JSON.parse(await s.eval(INSPECT(c.stageSel)));
      row.focusResult = focusRes;
      row.VISIBLE_FOCUS = after.focused && after.outlineStyle !== "none";
      row.focusBefore = `${before.outlineStyle} ${before.outlineWidth}`;
      row.focusAfter = `${after.outlineStyle} ${after.outlineWidth}`;

      /* KÍCH HOẠT THẬT — Enter qua CDP rồi đòi STATE TẤT ĐỊNH đổi. */
      const st0 = JSON.stringify((await s.snapshot())?.state ?? null);
      await s.pressKey("Enter");
      await sleep(420);
      const st1 = JSON.stringify((await s.snapshot())?.state ?? null);
      row.stateChangedByKeyboard = st0 !== st1;
      row.KEYBOARD_ACTIVATES = row.stateChangedByKeyboard;
    }
  } else {
    row.note = "TRACE_MODEL — không có affordance cơ chế; chỉ kiểm khay điều khiển";
    row.KEYBOARD_REACHABLE = true; row.ACCESSIBLE_NAME = true;
    row.STATE_NOT_COLOR_ONLY = true; row.VISIBLE_FOCUS = true; row.KEYBOARD_ACTIVATES = true;
  }

  /* KHAY ĐIỀU KHIỂN — mọi target đều phải điều khiển được bằng bàn phím. */
  const tray = JSON.parse(await s.eval(`(()=>{
    const name=${NAME_OF};
    const b=[...document.querySelectorAll('.btn-icon,.btn-play,.btn-utility')]
      .filter(e=>e.offsetParent!==null);
    const unnamed=b.filter(e=>!name(e));
    return JSON.stringify({n:b.length, unnamed:unnamed.length,
      unnamedCls:unnamed.map(e=>e.className).slice(0,4),
      minSide:b.length?Math.min(...b.map(e=>Math.min(e.getBoundingClientRect().width,
        e.getBoundingClientRect().height))):0});})()`));
  row.trayButtons = tray.n;
  row.trayUnnamed = tray.unnamed;
  row.TRAY_ALL_NAMED = tray.unnamed === 0;

  row.verdict = ["ACCESSIBLE_NAME", "KEYBOARD_REACHABLE", "STATE_NOT_COLOR_ONLY",
    "VISIBLE_FOCUS", "KEYBOARD_ACTIVATES", "TRAY_ALL_NAMED"]
    .every((k) => row[k] === true) ? "A11Y_PASS" : "A11Y_FAIL";
  rows.push(row);
}

/* ── THỬ THÁCH: Escape đóng, tiêu điểm quay về nút mở ───────────────────── */
await s.resetBetweenScenarios();
await s.loadTarget("network.packet_routing");
await sleep(600);
const challenge = { case: "CHALLENGE_ESCAPE", target: "network.packet_routing" };
/* ĐƯỜNG MỞ THỬ THÁCH LÀ ĐƯỜNG ĐÃ ĐƯỢC CHỨNG NHẬN Ở `quiz-dominance-w12.mjs`,
   chép nguyên: `predict.challenge(state)` trả null ở phần lớn các bước, nên
   phải tiến từng bước tới khi lối vào hiện ra. Bản đầu của cổng này bấm
   "Tiến một bước" rồi tìm thẳng nút mở, và đọc ra "không có thử thách" ở một
   target mà cổng khác đã đo được bề mặt thử thách cao 61px. */
challenge.openClick = "không có lối vào";
for (let step = 0; step < 12; step++) {
  await s.clickText("Thử thách");
  await sleep(150);
  const r = await s.clickText("Dự đoán bước này");
  if (r === "ok") { challenge.openClick = `ok (mở ở bước ${step})`; break; }
  const next = await s.eval(`(async()=>{
    const st=(await import(${JSON.stringify(s.mods.store)})).useAppStore.getState();
    if (typeof st.nextStep !== 'function') return 'không tua được';
    st.nextStep(); return 'ok';})()`);
  if (next !== "ok") break;
  await sleep(190);
}
await sleep(420);
challenge.opened = (await s.eval(`document.querySelectorAll('.predict-bar').length`)) > 0;
if (challenge.opened) {
  await s.focusSelector(".predict-close");
  await s.pressKey("Escape");
  await sleep(450);
  challenge.closedByEscape = (await s.eval(`document.querySelectorAll('.predict-bar').length`)) === 0;
  challenge.focusAfter = await s.eval(
    `(()=>{const a=document.activeElement; return a? a.className+'|'+(a.textContent||'').trim().slice(0,26):'none';})()`);
  challenge.FOCUS_RETURNS_TO_LAUNCHER = String(challenge.focusAfter).includes("predict-open");
}
challenge.ESC_CLOSES_CHALLENGE = challenge.opened === true && challenge.closedByEscape === true;

/* CHALLENGE_ESCAPE_BROKEN — tiêm lỗi cho chính đường Escape.
   Thay khối thử thách bằng một BẢN SAO: bản sao trông y hệt nhưng không còn nối
   với cây fiber của React, nên `onKeyDown` của `<section>` không chạy nữa. Đây
   đúng là hình dạng của lỗi cần chặn (khối còn đó, phím hết tác dụng), và nó
   quan sát được — nếu Escape vẫn đóng thì phép tiêm đã không xảy ra. */
challenge.faultEscape = { name: "CHALLENGE_ESCAPE_BROKEN", expected: "RED" };
if (challenge.opened) {
  await s.resetBetweenScenarios();
  await s.loadTarget("network.packet_routing");
  await sleep(500);
  for (let step = 0; step < 12; step++) {
    await s.clickText("Thử thách"); await sleep(140);
    if ((await s.clickText("Dự đoán bước này")) === "ok") break;
    const n = await s.eval(`(async()=>{const st=(await import(${JSON.stringify(s.mods.store)}))
      .useAppStore.getState(); if(typeof st.nextStep!=='function') return 'x'; st.nextStep(); return 'ok';})()`);
    if (n !== "ok") break;
    await sleep(180);
  }
  await sleep(380);
  challenge.faultEscape.mutation = await s.eval(`(()=>{
    const b=document.querySelector('.predict-bar');
    if(!b) return 'không thấy khối thử thách';
    b.replaceWith(b.cloneNode(true));
    return document.querySelector('.predict-bar') ? 'đã thay bằng bản sao rời fiber' : 'mất khối';})()`);
  await s.focusSelector(".predict-close");
  await s.pressKey("Escape");
  await sleep(400);
  const stillOpen = (await s.eval(`document.querySelectorAll('.predict-bar').length`)) > 0;
  challenge.faultEscape.mutationObserved = stillOpen ? "YES" : "NO";
  challenge.faultEscape.actual = stillOpen ? "RED" : "GREEN";
  challenge.faultEscape.ok = stillOpen;
}
challenge.verdict = challenge.ESC_CLOSES_CHALLENGE && challenge.FOCUS_RETURNS_TO_LAUNCHER
  ? "A11Y_PASS" : "A11Y_FAIL";

/* ── TIÊM LỖI — cổng chưa từng đỏ là cổng chưa được chứng minh ──────────── */
const faults = [];
await s.resetBetweenScenarios();
await s.loadTarget("logic.and_gate");
await sleep(700);
const SEL = '.sim-stage [role="button"]';

const observe = (expr) => s.eval(expr);
async function fault(name, mutate, check, expected) {
  const before = await observe(check);
  const applied = await observe(mutate);
  const after = await observe(check);
  faults.push({
    name, mutation: applied, mutationObserved: before !== after ? "YES" : "NO",
    before, after, expected, actual: after === "OK" ? "GREEN" : "RED",
    ok: (after === "OK" ? "GREEN" : "RED") === expected,
  });
  /* Hoàn nguyên bằng cách nạp lại target — không tin vào undo thủ công. */
  await s.resetBetweenScenarios();
  await s.loadTarget("logic.and_gate");
  await sleep(600);
}

const CHECK_NAME = `(()=>{const e=document.querySelector(${JSON.stringify(SEL)});
  return e&&(e.getAttribute('aria-label')||'').trim() ? 'OK':'THIẾU TÊN';})()`;
const CHECK_KEY = `(()=>{const e=document.querySelector(${JSON.stringify(SEL)});
  return e&&e.getAttribute('tabindex')==='0' ? 'OK':'NGOÀI TAB ORDER';})()`;

/* KIỂM SOÁT DƯƠNG TÍNH trước — nếu bản gốc đã đỏ thì mọi ca tiêm vô nghĩa. */
faults.push({
  name: "CONTROL", mutation: "(không đổi gì)", mutationObserved: "YES",
  before: await observe(CHECK_NAME), after: await observe(CHECK_NAME),
  expected: "GREEN", actual: (await observe(CHECK_NAME)) === "OK" ? "GREEN" : "RED",
  ok: (await observe(CHECK_NAME)) === "OK",
});

await fault("A11Y_NAME_REMOVED",
  `(()=>{const e=document.querySelector(${JSON.stringify(SEL)});
    if(!e) return 'không thấy'; e.removeAttribute('aria-label'); return 'đã gỡ aria-label';})()`,
  CHECK_NAME, "RED");

await fault("A11Y_KEYBOARD_PATH_REMOVED",
  `(()=>{const e=document.querySelector(${JSON.stringify(SEL)});
    if(!e) return 'không thấy'; e.removeAttribute('tabindex'); return 'đã gỡ tabindex';})()`,
  CHECK_KEY, "RED");

/* ── 768px — điều khiển còn dùng được không ─────────────────────────────── */
await s.close();
const s768 = await new BrowserSession({ viewport: 768, height: 900 }).open();
const narrow = [];
for (const c of CASES) {
  await s768.resetBetweenScenarios();
  await s768.loadTarget(c.target);
  await sleep(700);
  const m = JSON.parse(await s768.eval(`(()=>{
    const b=[...document.querySelectorAll('.btn-icon,.btn-play,.btn-utility')]
      .filter(e=>e.offsetParent!==null);
    if(!b.length) return JSON.stringify({n:0,minSide:0,offscreen:0});
    const R=b.map(e=>e.getBoundingClientRect());
    return JSON.stringify({n:b.length,
      minSide:Math.round(Math.min(...R.map(r=>Math.min(r.width,r.height)))),
      offscreen:R.filter(r=>r.right>768+1||r.left<-1).length});})()`));
  /* 24px là sàn thực dụng cho con trỏ chuột trên màn hẹp; nút chính của khay là
     40px. Ngưỡng này ĐO ĐƯỢC, không phải cảm nhận. */
  narrow.push({ target: c.target, ...m,
    verdict: m.n > 0 && m.minSide >= 24 && m.offscreen === 0 ? "USABLE_768" : "FAIL_768" });
}
await s768.close();

const pass = rows.filter((r) => r.verdict === "A11Y_PASS").length;
console.log("\n━━ KHẢ NĂNG TIẾP CẬN · phím thật qua CDP\n");
console.log("  target                          loại                       tên  bàn phím  kích hoạt  tiêu điểm  phán quyết");
for (const r of rows) {
  console.log(`  ${r.target.padEnd(32)}${(r.kind ?? "").padEnd(26)}` +
    `${(r.ACCESSIBLE_NAME ? "✔" : "✘").padStart(4)}${(r.KEYBOARD_REACHABLE ? "✔" : "✘").padStart(9)}` +
    `${(r.KEYBOARD_ACTIVATES ? "✔" : "✘").padStart(11)}${(r.VISIBLE_FOCUS ? "✔" : "✘").padStart(11)}` +
    `  ${r.verdict}`);
}
console.log(`\n  ${pass}/${rows.length} bề mặt ĐẠT`);
console.log(`  thử thách: Escape đóng=${challenge.ESC_CLOSES_CHALLENGE} · ` +
  `tiêu điểm về nút mở=${challenge.FOCUS_RETURNS_TO_LAUNCHER} → ${challenge.verdict}`);
console.log("\n  ── tiêm lỗi ──");
for (const f of faults) {
  console.log(`  ${f.name.padEnd(30)} quan sát=${f.mutationObserved} mong=${f.expected} thực=${f.actual} ${f.ok ? "✔" : "✘"}`);
}
console.log("\n  ── 768px ──");
for (const n of narrow) console.log(`  ${n.target.padEnd(32)} nút=${n.n} cạnh nhỏ nhất=${n.minSide}px tràn=${n.offscreen} ${n.verdict}`);

console.log(`  ${(challenge.faultEscape?.name ?? "CHALLENGE_ESCAPE_BROKEN").padEnd(30)} ` +
  `quan sát=${challenge.faultEscape?.mutationObserved ?? "—"} mong=RED ` +
  `thực=${challenge.faultEscape?.actual ?? "—"} ${challenge.faultEscape?.ok ? "✔" : "✘"}`);

const ok = pass === rows.length && challenge.verdict === "A11Y_PASS"
  && challenge.faultEscape?.ok === true
  && faults.every((f) => f.ok) && narrow.every((n) => n.verdict === "USABLE_768");

writeFileSync(OUT, JSON.stringify({
  ...provenance("certify-a11y-w12", { viewports: "1536,768" }),
  question: "Người dùng bàn phím có vào được CƠ CHẾ không, hay chỉ vào được khay điều khiển?",
  rows, challenge, faults, narrow768: narrow, ok,
}, null, 2), "utf-8");
console.log(`\n→ ${OUT}`);
if (!ok) process.exit(1);
