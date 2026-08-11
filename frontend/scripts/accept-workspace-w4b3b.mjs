/**
 * accept-workspace-w4b3b.mjs — NGHIỆM THU BỐ CỤC KHÔNG-GIAN-LÀM-VIỆC.
 *
 * Đo trong Chrome thật, BỐN bề rộng, ở các trạng thái mà unit test không với tới:
 *
 *   1. KHÔNG có cột điều hướng phiên thường trực (sân khấu bắt đầu ở lề nội
 *      dung bình thường, không phải sau một cột ~208–280px);
 *   2. sân khấu nhận trọn bề ngang không-gian-làm-việc ở MỌI số phiên;
 *   3. điều hướng phiên KHÔNG sinh tràn ngang trang;
 *   4. tiêu đề phiên MỘT DÒNG (cắt ellipsis), phiên đang xem rõ ràng;
 *   5. nút đóng và "Mô phỏng mới" luôn tới được (kể cả khi CHỈ CÓ MỘT phiên —
 *      đó là lỗi chức năng của bản cũ);
 *   6. dải điều khiển KHÔNG xuống dòng thành băng thứ hai trên desktop;
 *   7. chuyển phiên giữ nguyên state, 0 request mạng;
 *   8. trùng tiêu đề vẫn phân biệt được;
 *   9. nhiều phiên (> sức chứa) không ép sân khấu — gộp vào `+N`;
 *  10. ở 768: không ép tab desktop, bộ chọn gọn hoạt động.
 *
 * ⚠️ Hai điều kiện trước khi tin một bản "SẠCH" (`ARCHITECTURE_MAP §8` #14):
 * DẤU VÂN TAY TRANG (đúng route/target, sai thì thoát != 0) và `--self-test`.
 *
 * ⚠️ Bẫy hai-instance store: URL module lấy TỪ TRANG, không viết cứng — xem
 * `accept-w4b3a.mjs`.
 *
 * Chạy:  npm run dev  (cửa sổ khác)
 *        node scripts/accept-workspace-w4b3b.mjs [--out <f.json>] [--self-test]
 */

import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const SELF_TEST = args.includes("--self-test");
const PORT = argOf("--port", "3000");
const APP = `http://localhost:${PORT}`;
const OUT = resolve(argOf("--out", "../docs/evaluation/m17/w4b3b-workspace/acceptance.json"));
const LABEL = argOf("--label", "after");
mkdirSync(dirname(OUT), { recursive: true });

const VIEWPORTS = [[1920, 1080], [1536, 864], [1366, 768], [768, 900]];
/** Dưới bề rộng này sản phẩm dùng bộ chọn gọn thay hàng tab (CSS `max-width: 860px`). */
const NARROW_MAX = 860;

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const failures = [];
const rows = [];
const fail = (m) => { failures.push(m); console.error(`  ✗ ${m}`); };

async function withChrome(w, h, fn) {
  const cdp = 9400 + Math.floor(Math.random() * 500);
  const profile = mkdtempSync(join(tmpdir(), "algosim-w4b3b-"));
  const chrome = spawn(CHROME, [
    "--headless=new", "--disable-gpu", `--remote-debugging-port=${cdp}`,
    `--user-data-dir=${profile}`, `--window-size=${w},${h}`, "--hide-scrollbars", "about:blank",
  ], { stdio: "ignore" });
  try {
    let url;
    for (let i = 0; i < 40 && !url; i++) {
      try {
        const l = await (await fetch(`http://127.0.0.1:${cdp}/json/list`)).json();
        url = l.find((t) => t.type === "page")?.webSocketDebuggerUrl;
      } catch { /* chưa lên */ }
      if (!url) await sleep(250);
    }
    if (!url) throw new Error("Chrome không mở được cổng debug.");
    const ws = new WebSocket(url);
    await new Promise((r) => (ws.onopen = r));
    let id = 0; const pend = new Map();
    ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } };
    const send = (method, params = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
    const once = async (expr) => {
      const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
      /* "Promise was collected" = Vite tối ưu deps rồi RELOAD giữa lúc đang
         await, ngữ cảnh thực thi bị huỷ. Không phải lỗi của trang — thử lại.
         Cùng khuôn `measure-composition.mjs`, đừng phát minh cách khác. */
      if (r.error) { const e = new Error(r.error.message); e.cdp = true; throw e; }
      if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails.exception ?? r.result.exceptionDetails));
      const v = r.result?.result?.value;
      /* `undefined` mà KHÔNG có exception là ca khó chẩn nhất: biểu thức chạy
         xong nhưng không trả gì. Ném kèm đầu biểu thức, khỏi phải đoán. */
      if (v === undefined) throw new Error(`biểu thức trả undefined: ${expr.slice(0, 120)}…`);
      return v;
    };
    const ev = async (expr) => {
      let last;
      for (let i = 0; i < 6; i++) {
        try { return await once(expr); } catch (e) { if (!e.cdp) throw e; last = e; await sleep(1200); }
      }
      throw last;
    };
    await send("Page.enable"); await send("Runtime.enable");
    await send("Page.navigate", { url: APP });
    await sleep(2500);
    /* WARMUP: nạp trước đúng những module sẽ dùng, để lần tối ưu-deps + reload
       của Vite xảy ra Ở ĐÂY chứ không xảy ra giữa một phép đo.
       ⚠️ PHẢI dùng URL ĐÃ GIẢI TỪ TRANG, không dùng đường dẫn trần. Warmup bằng
       `import('/src/state/store.ts')` sẽ ĐĂNG KÝ chính URL trần đó vào
       `performance.getEntriesByType('resource')`, nên `pick()` sau đó chọn nó
       thay vì URL `?t=…` mà app đang chạy — và ta lại lái một store thứ hai
       trong khi trang vẽ theo store kia. Đúng cái bẫy script này viết ra để
       tránh; nó cắn lần thứ hai vì warmup được thêm vào SAU. */
    const warm = JSON.parse(await once(RESOLVE));
    for (let i = 0; i < 8; i++) {
      try {
        await once(`(async()=>{${Object.values(warm).map((u) => `await import(${JSON.stringify(u)});`).join("")}return true})()`);
        break;
      } catch { await sleep(1500); }
    }
    await sleep(600);
    await fn(ev, send);
  } finally {
    try { chrome.kill(); } catch { /* đã chết */ }
  }
}

const RESOLVE = `(()=>{
  const pick=(s)=>{const h=performance.getEntriesByType('resource').map(e=>e.name).filter(n=>n.includes(s));
    return h.length?h[h.length-1]:new URL(s,location.origin).href;};
  return JSON.stringify({store:pick('/src/state/store.ts'),catalog:pick('/src/data/offline-catalog.ts'),
    sims:pick('/src/simulations/index.ts'),registry:pick('/src/simulations/registry.ts')});
})()`;

/** Mở N phiên từ danh mục offline (lặp lại `dupIds` để tạo trùng tiêu đề). */
const openSessions = (u, ids) => `(async()=>{
  const s=await import(${JSON.stringify(u.store)});
  const c=await import(${JSON.stringify(u.catalog)});
  const r=await import(${JSON.stringify(u.sims)});
  const reg=await import(${JSON.stringify(u.registry)});
  if(reg.listSimulations().length===0) r.registerAllSimulations();
  s.useAppStore.getState().reset();
  const cat=c.offlineCatalog();
  for(const id of ${JSON.stringify(ids)}){
    const e=cat.find(x=>x.simId===id);
    if(!e) return JSON.stringify({ok:false,why:'thiếu '+id});
    s.useAppStore.getState().newSession();
    s.useAppStore.getState().loadEnvelope(e.envelope);
  }
  const st=s.useAppStore.getState();
  return JSON.stringify({ok:true,sessions:st.sessions.length,view:st.view,active:st.active&&st.active.moduleId});
})()`;

/** Đo bố cục không-gian-làm-việc ở trạng thái hiện tại. */
const PROBE = `JSON.stringify((()=>{
  const R=(el)=>{const b=el.getBoundingClientRect();return{x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)};};
  const layout=document.querySelector('.app-layout');
  const center=document.querySelector('.panel-center');
  const card=document.querySelector('.workspace-card');
  const controls=document.querySelector('.player-controls');
  const tabs=document.querySelector('.session-tabs');
  const tabBtns=[...document.querySelectorAll('.session-tab')];
  const active=document.querySelector('.session-tab.is-active');
  const more=document.querySelector('.session-more');
  const moreVisible=more? getComputedStyle(more).display!=='none' : false;
  const tabListVisible=(()=>{const l=document.querySelector('.session-tab-list');
    return l? getComputedStyle(l).display!=='none' : false;})();
  /* SO DONG THAT cua dai dieu khien.
     KHONG dem bang so gia tri top khac nhau: trong mot flex row co
     align-items:center, con CAO THAP KHAC NHAU thi top cung khac nhau, nen
     phep dem do bao 5-7 dong cho mot hang phang. Dem bang CHONG LAN DOC: di
     theo thu tu DOM, chi mo dong moi khi con hien tai khong chong lan dai doc
     cua dong dang mo.
     (Chu thich trong template literal KHONG duoc dung dau backtick.) */
  const ctrlRows = (()=>{
    if(!controls) return 0;
    const kids=[...controls.children].map(e=>e.getBoundingClientRect()).filter(b=>b.width>0&&b.height>0);
    let rows=0, top=0, bot=-1;
    for(const b of kids){
      if(b.top >= bot){ rows++; top=b.top; bot=b.bottom; }
      else { top=Math.min(top,b.top); bot=Math.max(bot,b.bottom); }
    }
    return rows;
  })();
  const titleLines=(()=>{
    const t=document.querySelector('.session-tab.is-active .session-tab-open');
    if(!t) return null;
    const cs=getComputedStyle(t);
    const lh=parseFloat(cs.lineHeight)||parseFloat(cs.fontSize)*1.4;
    return Math.round(t.getBoundingClientRect().height/lh);
  })();
  return {
    fingerprintStage: !!document.querySelector('.sim-stage')||!!card,
    // Cột điều hướng thường trực: có phần tử nào chiếm bề ngang BÊN TRÁI sân khấu không.
    railPresent: !!document.querySelector('.session-rail,[class*="rail"]'),
    layout: layout?R(layout):null,
    center: center?R(center):null,
    card: card?R(card):null,
    controls: controls?R(controls):null,
    tabs: tabs?R(tabs):null,
    tabCount: tabBtns.length,
    tabListVisible, moreVisible,
    moreLabel: more? (more.textContent||'').trim() : null,
    activeTabLabel: active? (active.textContent||'').trim() : null,
    activeTabCount: document.querySelectorAll('.session-tab.is-active').length,
    closeButtons: document.querySelectorAll('.session-tab-close,.session-more-close').length,
    newSessionReachable: [...document.querySelectorAll('button')].some(b=>/Mô phỏng mới/.test(b.textContent||'')),
    titleLines,
    ctrlRows,
    overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  };
})())`;

for (const [w, h] of VIEWPORTS) {
  await withChrome(w, h, async (ev) => {
    console.log(`\n━━ ${w}×${h}`);
    const u = JSON.parse(await ev(RESOLVE));
    if (!u.store.includes("/src/state/store.ts")) { fail(`${w}: không giải được URL store`); return; }
    const narrow = w <= NARROW_MAX;

    /* ── A. MỘT phiên: không hàng điều hướng, nhưng vẫn mở được bài thứ hai ── */
    let r = JSON.parse(await ev(openSessions(u, ["algorithm.find_max"])));
    if (!r.ok) { fail(`${w}: ${r.why}`); return; }
    await sleep(400);
    let p = JSON.parse(await ev(PROBE));
    if (!p.fingerprintStage) { fail(`${w}: không thấy sân khấu — trang sai`); return; }
    if (p.railPresent) fail(`${w}·1 phiên: còn cột phiên thường trực`);
    if (p.tabs) fail(`${w}·1 phiên: dựng hàng điều hướng chỉ để lặp lại một tiêu đề`);
    if (!p.newSessionReachable) fail(`${w}·1 phiên: KHÔNG có đường mở mô phỏng thứ hai`);
    if (p.overflowX > 0) fail(`${w}·1 phiên: tràn ngang ${p.overflowX}px`);
    if (!narrow && p.ctrlRows > 1) fail(`${w}·1 phiên: dải điều khiển xuống ${p.ctrlRows} dòng`);
    const oneSessionCard = p.card;
    rows.push({ viewport: `${w}x${h}`, state: "1-session", probe: p });
    console.log(`  1 phiên        card.w=${p.card?.w} ctrlRows=${p.ctrlRows} overflow=${p.overflowX} newSession=${p.newSessionReachable}`);

    /* ── B. HAI phiên TRÙNG TIÊU ĐỀ ────────────────────────────────────── */
    r = JSON.parse(await ev(openSessions(u, ["algorithm.find_max", "algorithm.find_max"])));
    if (!r.ok) { fail(`${w}: ${r.why}`); return; }
    await sleep(400);
    p = JSON.parse(await ev(PROBE));
    if (p.railPresent) fail(`${w}·2 phiên: cột phiên thường trực quay lại`);
    if (p.overflowX > 0) fail(`${w}·2 phiên: tràn ngang ${p.overflowX}px`);
    if (!narrow) {
      if (!p.tabs) fail(`${w}·2 phiên: không có hàng điều hướng`);
      if (p.activeTabCount !== 1) fail(`${w}·2 phiên: ${p.activeTabCount} tab đang-xem (phải đúng 1)`);
      if (p.titleLines !== null && p.titleLines > 1) fail(`${w}·2 phiên: tiêu đề ${p.titleLines} dòng`);
      if (p.closeButtons < 2) fail(`${w}·2 phiên: thiếu nút đóng`);
      if (p.ctrlRows > 1) fail(`${w}·2 phiên: dải điều khiển xuống ${p.ctrlRows} dòng`);
      // Sân khấu KHÔNG được hẹp đi vì có điều hướng phiên.
      if (oneSessionCard && p.card && p.card.w < oneSessionCard.w) {
        fail(`${w}·2 phiên: sân khấu hẹp đi ${oneSessionCard.w - p.card.w}px so với 1 phiên`);
      }
      if (oneSessionCard && p.card && p.card.x !== oneSessionCard.x) {
        fail(`${w}·2 phiên: sân khấu bị đẩy sang phải (x ${oneSessionCard.x}→${p.card.x})`);
      }
      // Trùng tiêu đề phải phân biệt được.
      const labels = JSON.parse(await ev(`JSON.stringify([...document.querySelectorAll('.session-tab-open')].map(e=>(e.textContent||'').trim()))`));
      if (new Set(labels).size !== labels.length) fail(`${w}·2 phiên: hai tab trùng nhãn ${JSON.stringify(labels)}`);
    } else {
      if (p.tabListVisible) fail(`${w}·hẹp: ép hàng tab desktop vào màn hẹp`);
      if (!p.moreVisible) fail(`${w}·hẹp: không có bộ chọn phiên`);
    }
    rows.push({ viewport: `${w}x${h}`, state: "2-sessions-duplicate-title", probe: p });
    console.log(`  2 phiên (trùng) card.w=${p.card?.w} tabs=${p.tabCount} more=${p.moreVisible} ctrlRows=${p.ctrlRows} overflow=${p.overflowX}`);

    /* ── C. NHIỀU phiên (quá sức chứa) ─────────────────────────────────── */
    const many = ["algorithm.find_max", "algorithm.binary_search", "algorithm.bubble_sort",
                  "algorithm.count_if", "logic.and_gate", "network.packet_routing"];
    r = JSON.parse(await ev(openSessions(u, many)));
    if (!r.ok) { fail(`${w}: ${r.why}`); return; }
    await sleep(400);
    p = JSON.parse(await ev(PROBE));
    if (p.overflowX > 0) fail(`${w}·${many.length} phiên: tràn ngang ${p.overflowX}px`);
    if (p.railPresent) fail(`${w}·${many.length} phiên: cột phiên quay lại`);
    if (!narrow) {
      if (p.tabCount > 4) fail(`${w}·${many.length} phiên: ${p.tabCount} tab hiện thẳng (chặn ở 4)`);
      if (!p.moreVisible) fail(`${w}·${many.length} phiên: thiếu affordance gộp phần dư`);
      if (oneSessionCard && p.card && p.card.w < oneSessionCard.w) {
        fail(`${w}·${many.length} phiên: sân khấu hẹp đi ${oneSessionCard.w - p.card.w}px`);
      }
      if (p.ctrlRows > 1) fail(`${w}·${many.length} phiên: dải điều khiển xuống ${p.ctrlRows} dòng`);
    }
    rows.push({ viewport: `${w}x${h}`, state: `${many.length}-sessions`, probe: p });
    console.log(`  ${many.length} phiên       card.w=${p.card?.w} tabs=${p.tabCount} more="${p.moreLabel}" overflow=${p.overflowX}`);

    /* ── D. CHUYỂN PHIÊN: giữ nguyên + 0 mạng ──────────────────────────── */
    const sw = JSON.parse(await ev(`(async()=>{
      const s=await import(${JSON.stringify(u.store)});
      let calls=0; const f=window.fetch; window.fetch=(...a)=>{calls++;return f(...a);};
      const st=s.useAppStore.getState();
      const ids=st.sessions.map(x=>x.id);
      s.useAppStore.getState().switchSession(ids[0]);
      s.useAppStore.getState().goToStep(2);
      const stA=s.useAppStore.getState().active.state;
      s.useAppStore.getState().switchSession(ids[2]);
      s.useAppStore.getState().switchSession(ids[0]);
      const back=s.useAppStore.getState();
      window.fetch=f;
      return JSON.stringify({same: back.active.state===stA, fetches: calls, id: back.activeSessionId===ids[0]});
    })()`));
    if (!sw.same) fail(`${w}: chuyển phiên dựng lại state (mất what-if)`);
    if (!sw.id) fail(`${w}: chuyển phiên không về đúng phiên`);
    if (sw.fetches !== 0) fail(`${w}: chuyển phiên gọi mạng ${sw.fetches} lần`);
    console.log(`  chuyển phiên   giữ nguyên=${sw.same} fetch=${sw.fetches}`);
    rows.push({ viewport: `${w}x${h}`, state: "switch", switch: sw });
  });
}

if (SELF_TEST) {
  const n = failures.length;
  fail("SELF-TEST: khẳng định cố ý sai");
  if (failures.length !== n + 1) { console.error("SELF-TEST hỏng."); process.exit(3); }
  console.log("\nSELF-TEST: script ĐỎ được.");
  process.exit(1);
}

writeFileSync(OUT, JSON.stringify({ when: new Date().toISOString(), label: LABEL, viewports: VIEWPORTS, rows, failures }, null, 2));
console.log(`\n${failures.length === 0 ? "✔ TẤT CẢ SẠCH" : `✗ ${failures.length} lỗi`} → ${OUT}`);
process.exit(failures.length === 0 ? 0 : 1);
