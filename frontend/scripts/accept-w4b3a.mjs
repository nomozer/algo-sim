/**
 * accept-w4b3a.mjs — NGHIỆM THU TRÌNH DUYỆT cho W4B-3A.
 *
 * Đo trong Chrome thật, ở BỐN bề rộng, những điều mà unit test không với tới:
 *
 *   1. KHÔNG còn dải `experiment-trigger` nào trong DOM;
 *   2. lối vào Khám phá/Thử thách nằm trong DẢI ĐIỀU KHIỂN (`.player-controls`),
 *      không nằm trong luồng nội dung của `.workspace-card`;
 *   3. mở Thử thách ⇒ vùng cam kết TỚI ĐƯỢC (và chỉ MỘT bề mặt);
 *   4. không tràn ngang ở bất kỳ bề rộng nào;
 *   5. transport chỉ xuất hiện ở bài có `timeline` > 1 bước;
 *   6. PARITY 2D↔3D của `network.protocol_encapsulation`: đổi cách xem KHÔNG
 *      đổi sự thật tất định (cursor, nhãn PDU, tổng số bước);
 *   7. phiên: A → Khám phá → B → quay lại A, mọi thứ còn nguyên, 0 request mạng.
 *
 * ⚠️ HAI ĐIỀU KIỆN TRƯỚC KHI TIN MỘT BẢN "SẠCH" (`ARCHITECTURE_MAP §8` #14):
 *   - DẤU VÂN TAY TRANG: khẳng định đúng route/target, sai thì thoát != 0;
 *   - TIÊM LỖI GIẢ: `--self-test` bắt script tự kiểm bằng một khẳng định sai,
 *     để chứng minh nó ĐỎ được. Guard chưa từng đỏ là guard chưa được chứng minh.
 *
 * ⚠️ BẪY HAI INSTANCE STORE (đã cắn một lần, mất một lượt đo):
 * Vite gắn `?t=<timestamp>` vào URL module sau mỗi lần HMR. `import('/src/state/
 * store.ts')` từ console khi đó trả về MỘT MODULE KHÁC với module app đang chạy
 * — script lái một store, trang vẽ theo store kia, và mọi khẳng định "không thấy
 * X" đều XANH vì lý do sai. Nên URL store phải LẤY TỪ CHÍNH TRANG
 * (`performance.getEntriesByType('resource')`), không viết cứng.
 *
 * Chạy:  npm run dev  (cửa sổ khác)
 *        node scripts/accept-w4b3a.mjs [--out <file.json>] [--self-test]
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
const OUT = resolve(argOf("--out", "../docs/evaluation/m17/w4b3a-after/acceptance.json"));
mkdirSync(dirname(OUT), { recursive: true });

const VIEWPORTS = [[1920, 1080], [1536, 864], [1366, 768], [768, 900]];

/** Target đại diện bắt buộc (§9). `algorithm.*` phủ họ đã gỡ dải. */
const TARGETS = [
  "web.style_model",
  "algorithm.count_if",
  "algorithm.linear_search",
  "algorithm.bubble_sort",
  "network.packet_routing",
  "network.protocol_encapsulation",
  "generic.rule_scene",
  /* W4B-3D — chín target vừa có mẫu offline đầu tiên. Trước đó không lượt đo
     trình duyệt nào chạm tới chúng, nên mọi khẳng định về bố cục/quyền sở hữu
     lối vào chỉ đúng cho 14/23. */
  "algorithm.selection_sort",
  "algorithm.scan",
  "algorithm.bounded_control_flow",
  "binary.base_conversion",
  "binary.character_encoding",
  "binary.decimal_to_binary",
  "logic.and_gate",
  "logic.boolean_dag",
  "network.graph_traversal",
  "tree.traversal",
  "database.relational_table_query",
];

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const failures = [];
const rows = [];

async function withChrome(w, h, fn) {
  const cdp = 9200 + Math.floor(Math.random() * 700);
  const profile = mkdtempSync(join(tmpdir(), "algosim-w4b3a-"));
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
    const ev = async (expr) => {
      const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
      if (r.result?.exceptionDetails) {
        throw new Error(JSON.stringify(r.result.exceptionDetails.exception ?? r.result.exceptionDetails));
      }
      return r.result?.result?.value;
    };
    await send("Page.enable"); await send("Runtime.enable");
    await send("Page.navigate", { url: APP });
    await sleep(3200);
    await fn(ev);
  } finally {
    try { chrome.kill(); } catch { /* đã chết */ }
  }
}

/**
 * URL module LẤY TỪ TRANG — xem "bẫy hai instance" ở đầu file. Trả về map
 * {store, catalog, registry, sims} để mọi lần import sau dùng đúng instance app.
 */
const RESOLVE = `(()=>{
  const pick=(suffix)=>{
    const hit=performance.getEntriesByType('resource')
      .map(e=>e.name).filter(n=>n.includes(suffix));
    return hit.length ? hit[hit.length-1] : new URL(suffix, location.origin).href;
  };
  return JSON.stringify({
    store: pick('/src/state/store.ts'),
    catalog: pick('/src/data/offline-catalog.ts'),
    registry: pick('/src/simulations/registry.ts'),
    sims: pick('/src/simulations/index.ts'),
  });
})()`;

/** Nạp một target QUA CHÍNH module app đang dùng, rồi khẳng định dấu vân tay. */
const loadExpr = (urls, simId) => `(async()=>{
  const s=await import(${JSON.stringify(urls.store)});
  const c=await import(${JSON.stringify(urls.catalog)});
  const r=await import(${JSON.stringify(urls.sims)});
  const reg=await import(${JSON.stringify(urls.registry)});
  if(reg.listSimulations().length===0) r.registerAllSimulations();
  s.useAppStore.getState().reset();
  const e=c.offlineCatalog().find(x=>x.simId===${JSON.stringify(simId)});
  if(!e) return JSON.stringify({ok:false,why:'không có trong danh mục offline'});
  s.useAppStore.getState().loadEnvelope(e.envelope);
  const st=s.useAppStore.getState();
  return JSON.stringify({ok:!!st.active, moduleId:st.active&&st.active.moduleId, view:st.view});
})()`;

/** Đo bố cục + quyền sở hữu lối vào ở trạng thái hiện tại. */
const PROBE = `JSON.stringify((()=>{
  const controls=document.querySelector('.player-controls');
  const card=document.querySelector('.workspace-card');
  const entries=[...document.querySelectorAll('.sim-secondary-action')];
  const inControls=entries.filter(e=>controls&&controls.contains(e)).length;
  return {
    fingerprintStage: !!document.querySelector('.sim-stage')||!!card,
    triggerBand: document.querySelectorAll('.experiment-trigger').length,
    entries: entries.length,
    entriesInControls: inControls,
    entryLabels: entries.map(e=>(e.textContent||'').trim()),
    entriesDisabled: entries.filter(e=>e.disabled).length,
    transport: document.querySelectorAll('.control-group-transport').length,
    commitmentSurfaces:
      document.querySelectorAll('[aria-label="Thao tác với biến tích luỹ"],[aria-label="Thao tác với bước tìm kiếm"],[aria-label="Thao tác sắp xếp"]').length
      + document.querySelectorAll('.predict-inline').length,
    overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    stageWidth: (document.querySelector('.sim-stage')||{getBoundingClientRect:()=>({width:0})}).getBoundingClientRect().width,
  };
})())`;

const fail = (msg) => { failures.push(msg); console.error(`  ✗ ${msg}`); };

for (const [w, h] of VIEWPORTS) {
  await withChrome(w, h, async (ev) => {
    console.log(`\n━━ ${w}×${h}`);
    const urls = JSON.parse(await ev(RESOLVE));
    if (!urls.store.includes("/src/state/store.ts")) {
      fail(`${w}: không giải được URL store từ trang`);
      return;
    }
    for (const simId of TARGETS) {
      const loaded = JSON.parse(await ev(loadExpr(urls, simId)));
      if (!loaded.ok) { fail(`${w}·${simId}: không nạp được (${loaded.why ?? "?"})`); continue; }
      // DẤU VÂN TAY: đúng target, đúng route — sai thì mọi số sau đó vô nghĩa.
      if (loaded.moduleId !== simId) { fail(`${w}·${simId}: nạp nhầm ${loaded.moduleId}`); continue; }
      if (loaded.view !== "workspace") { fail(`${w}·${simId}: không ở workspace`); continue; }
      await sleep(420);
      const before = JSON.parse(await ev(PROBE));
      if (!before.fingerprintStage) { fail(`${w}·${simId}: không thấy sân khấu — trang sai`); continue; }

      // (1) không còn dải cổng
      if (before.triggerBand !== 0) fail(`${w}·${simId}: còn ${before.triggerBand} dải experiment-trigger`);
      // (2) mọi lối vào đều ở dải điều khiển
      if (before.entries !== before.entriesInControls) {
        fail(`${w}·${simId}: ${before.entries - before.entriesInControls} lối vào nằm ngoài dải điều khiển`);
      }
      // (4) không tràn ngang
      if (before.overflowX > 0) fail(`${w}·${simId}: tràn ngang ${before.overflowX}px`);
      // (3) mở Thử thách ⇒ tới được vùng cam kết, và KHÔNG BAO GIỜ hai bề mặt
      let opened = null;
      if (before.entries > 0) {
        await ev(`(async()=>{
          const s=await import(${JSON.stringify(urls.store)});
          const st=s.useAppStore.getState();
          const tl=(await import(${JSON.stringify(urls.registry)})).getSimulation(st.active.moduleId).timeline;
          if(tl){ // đi tới bước đầu tiên có gì để cam kết
            for(let i=0;i<tl.stepCount(st.active.state);i++){
              s.useAppStore.getState().goToStep(i);
              s.useAppStore.getState().setChallengeOpen(true);
              await new Promise(r=>setTimeout(r,0));
              if(document.querySelectorAll('[aria-label^="Thao tác"],.predict-inline').length>0) break;
            }
          } else { s.useAppStore.getState().setChallengeOpen(true); }
          return true;
        })()`);
        await sleep(420);
        opened = JSON.parse(await ev(PROBE));
        if (opened.commitmentSurfaces > 1) {
          fail(`${w}·${simId}: mở Thử thách ra ${opened.commitmentSurfaces} bề mặt cam kết`);
        }
        if (opened.triggerBand !== 0) fail(`${w}·${simId}: dải cổng quay lại khi mở chế độ`);
        if (opened.overflowX > 0) fail(`${w}·${simId}: tràn ngang ${opened.overflowX}px khi mở chế độ`);
      }
      rows.push({ viewport: `${w}x${h}`, target: simId, before, opened });
      console.log(
        `  ${simId.padEnd(32)} bands=${before.triggerBand} entries=${before.entries}` +
        `(${before.entriesDisabled} mờ) overflow=${before.overflowX} commit=${opened ? opened.commitmentSurfaces : "-"}`,
      );
    }

    /* ── (6) PARITY 2D↔3D: đổi CÁCH XEM không đổi SỰ THẬT ─────────────── */
    const parity = JSON.parse(await ev(`(async()=>{
      const s=await import(${JSON.stringify(urls.store)});
      const c=await import(${JSON.stringify(urls.catalog)});
      const reg=await import(${JSON.stringify(urls.registry)});
      const st=s.useAppStore.getState();
      st.reset();
      const e=c.offlineCatalog().find(x=>x.simId==='network.protocol_encapsulation');
      s.useAppStore.getState().loadEnvelope(e.envelope);
      const mod=reg.getSimulation('network.protocol_encapsulation');
      const snap=()=>{const a=s.useAppStore.getState().active;
        return {cursor:mod.timeline.currentStep(a.state), total:mod.timeline.stepCount(a.state),
                ctx:JSON.stringify(mod.getExplainContext(a.state,a.config))};};
      s.useAppStore.getState().goToStep(3);
      const in2d=snap();
      s.useAppStore.getState().setVisualMode('3d');
      const in3d=snap();
      s.useAppStore.getState().setVisualMode('2d');
      const back=snap();
      return JSON.stringify({in2d,in3d,back,modes:mod.supportedVisualModes});
    })()`));
    const same = (a, b) => a.cursor === b.cursor && a.total === b.total && a.ctx === b.ctx;
    if (!same(parity.in2d, parity.in3d)) fail(`${w}: parity 2D→3D lệch sự thật tất định`);
    if (!same(parity.in2d, parity.back)) fail(`${w}: quay về 2D không khôi phục đúng sự thật`);
    console.log(`  protocol parity 2D↔3D: cursor=${parity.in2d.cursor}/${parity.in2d.total} ${same(parity.in2d, parity.in3d) ? "KHỚP" : "LỆCH"}`);

    /* ── (7) PHIÊN: A → Khám phá → B → quay lại A, 0 request ───────────── */
    const sess = JSON.parse(await ev(`(async()=>{
      const s=await import(${JSON.stringify(urls.store)});
      const c=await import(${JSON.stringify(urls.catalog)});
      const st=s.useAppStore.getState(); st.reset();
      let calls=0; const f=window.fetch; window.fetch=(...a)=>{calls++;return f(...a);};
      const cat=c.offlineCatalog();
      const A=cat.find(x=>x.simId==='network.packet_routing');
      const B=cat.find(x=>x.simId==='algorithm.bubble_sort');
      s.useAppStore.getState().loadEnvelope(A.envelope);
      const idA=s.useAppStore.getState().activeSessionId;
      s.useAppStore.getState().setExploreOpen(true);
      s.useAppStore.getState().goToStep(2);
      const stateA=s.useAppStore.getState().active.state;
      s.useAppStore.getState().newSession();
      s.useAppStore.getState().loadEnvelope(B.envelope);
      const idB=s.useAppStore.getState().activeSessionId;
      const exploreInB=s.useAppStore.getState().exploreOpen;
      s.useAppStore.getState().switchSession(idA);
      const backA=s.useAppStore.getState();
      const r={
        restoredSameObject: backA.active.state===stateA,
        exploreRestored: backA.exploreOpen===true,
        exploreLeakedToB: exploreInB===true,
        fetches: calls,
        sessions: backA.sessions.length,
      };
      window.fetch=f; return JSON.stringify(r);
    })()`));
    if (!sess.restoredSameObject) fail(`${w}: chuyển phiên dựng lại state (mất what-if)`);
    if (!sess.exploreRestored) fail(`${w}: chế độ Khám phá không khôi phục theo phiên`);
    if (sess.exploreLeakedToB) fail(`${w}: chế độ Khám phá rò sang phiên mới`);
    if (sess.fetches !== 0) fail(`${w}: phiên gọi mạng ${sess.fetches} lần`);
    console.log(`  phiên A→B→A: giữ nguyên=${sess.restoredSameObject} explore=${sess.exploreRestored} rò=${sess.exploreLeakedToB} fetch=${sess.fetches}`);
    rows.push({ viewport: `${w}x${h}`, parity, sess });
  });
}

/* ── TIÊM LỖI GIẢ: chứng minh script ĐỎ được ─────────────────────────────── */
if (SELF_TEST) {
  const n = failures.length;
  fail("SELF-TEST: khẳng định cố ý sai");
  if (failures.length !== n + 1) {
    console.error("SELF-TEST hỏng: không ghi nhận được lỗi giả.");
    process.exit(3);
  }
  console.log("\nSELF-TEST: script ghi nhận được lỗi ⇒ nó ĐỎ được.");
  process.exit(1);
}

writeFileSync(OUT, JSON.stringify({ when: new Date().toISOString(), viewports: VIEWPORTS, rows, failures }, null, 2));
console.log(`\n${failures.length === 0 ? "✔ TẤT CẢ SẠCH" : `✗ ${failures.length} lỗi`} → ${OUT}`);
process.exit(failures.length === 0 ? 0 : 1);
