/**
 * diagnose-responsive.mjs — M17-RC1 §E1 §2: BẰNG CHỨNG ROOT CAUSE.
 *
 * Đo hình học DOM THẬT ở từng viewport để trả lời: phần tử NÀO làm
 * scrollWidth > clientWidth ở mức TRANG, và min-width nào giữ cột không co.
 * Chạy TRƯỚC khi sửa (before) và LẠI sau khi sửa (after).
 *
 *   node scripts/diagnose-responsive.mjs --out ../docs/evaluation/m17/rc1/visual/before/VIS-003
 */
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

import { FIXTURES as STRESS_FIXTURES } from "./fixtures.mjs";

const args = process.argv.slice(2);
const argOf = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const APP = `http://localhost:${argOf("--port", "3000")}`;
const OUT = resolve(argOf("--out", "../docs/evaluation/m17/rc1/visual/before/VIS-003"));
const CDP_PORT = 9337;

/* W4B-1A — viewport THAM SỐ HOÁ. Mặc định giữ nguyên cặp cũ (1440×1000 +
   768×900) để lượt chạy RC1 cũ tái lập được y hệt. Trục CHIỀU CAO cần cặp
   trực giao (cùng rộng, khác cao) nên truyền tay:
     --viewports 1920x1080,1920x768,1366x1024,1366x768 */
const parseViewports = (spec) =>
  spec.split(",").map((s) => {
    const m = /^(\d+)x(\d+)$/.exec(s.trim());
    if (!m) { console.error(`Viewport sai định dạng: "${s}" (cần WxH).`); process.exit(2); }
    return { id: `${m[1]}x${m[2]}`, width: +m[1], height: +m[2] };
  });
const VIEWPORTS = parseViewports(argOf("--viewports", "1440x1000,768x900"));

/* Route dùng CHUNG app shell — §5 bắt buộc kiểm cùng lúc. */
const ALL_ROUTES = [
  { id: "workspace", hash: "" },
  { id: "home", hash: "#/" },
  { id: "library", hash: "#/library" },
  { id: "history", hash: "#/history" },
];
/* Probe trục chiều cao chỉ quan tâm workspace: `--routes workspace`. */
const ONLY_ROUTES = argOf("--routes", null);
const ROUTES = ONLY_ROUTES
  ? ALL_ROUTES.filter((r) => ONLY_ROUTES.split(",").includes(r.id))
  : ALL_ROUTES;

/* Fixture nạp vào workspace. Mặc định giữ tree.traversal của lượt RC1. */
const FIXTURES = {
  "tree.traversal": {
    status: "ok", simulation_id: "tree.traversal", domain: "tree", visual_mode: "2d",
    title: "Chẩn đoán bố cục", description: null, notes: null,
    config: { specVersion: "tree-1.0", variant: "preorder", rootId: "A",
              nodes: [{ id: "A", label: "A", left: "B", right: "C" },
                      { id: "B", label: "B", left: null, right: null },
                      { id: "C", label: "C", left: null, right: null }], notes: null },
  },
  /* OBSERVATION SAMPLE của W4B-1A — đúng target người dùng báo. */
  "algorithm.find_max": {
    status: "ok", simulation_id: "algorithm.find_max", domain: "algorithm", visual_mode: "2d",
    title: "Tìm giá trị lớn nhất", description: null, notes: null,
    config: {
      problem: { summary: "Tìm giá trị lớn nhất", input: "Dãy số", output: "Kết quả" },
      algorithm_id: "find_max",
      data: { array: [12, 7, 25, 9, 18], labels: null, target: null, condition: null, order: null },
      data_generated: false, notes: null,
    },
  },
  /* Nội dung CAO hơn: sân khấu đồ thị + frontier + dòng đã-thăm + chú giải 4
     mục + thuyết minh. Dùng để đo ĐỘ LỚN của phần bị giấu, không chỉ có/không. */
  "network.graph_traversal": {
    status: "ok", simulation_id: "network.graph_traversal", domain: "network", visual_mode: "2d",
    title: "Duyệt đồ thị theo chiều rộng", description: null, notes: null,
    config: {
      nodes: [{ id: "A", label: "Trạm Hải Đăng" }, { id: "B", label: "Trạm Sương Mai" },
              { id: "C", label: "Trạm Thông Xanh" }, { id: "D", label: "Trạm Suối Đá" },
              { id: "E", label: "Trạm Mây Trắng" }, { id: "F", label: "Trạm Gió Nồm" }],
      edges: [["A", "B"], ["A", "C"], ["B", "D"], ["C", "E"], ["D", "F"], ["E", "F"]],
      directed: false, start: "A", goal: "F", variant: "bfs", notes: null,
    },
  },
};
const FIXTURE_ID = argOf("--fixture", "tree.traversal");
if (!["catalog", "stress", "all"].includes(FIXTURE_ID) && !FIXTURES[FIXTURE_ID]) {
  console.error(`Fixture không có: ${FIXTURE_ID}. ` +
    `Có: catalog | stress | all | ${Object.keys(FIXTURES).join(" | ")}`);
  process.exit(2);
}

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

const profile = mkdtempSync(join(tmpdir(), "algosim-e1-"));
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu",
  `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
  "--window-size=1440,1000", "--hide-scrollbars", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function connect() {
  for (let i = 0; i < 40; i++) {
    try {
      const l = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`)).json();
      const p = l.find((t) => t.type === "page");
      if (p) return p.webSocketDebuggerUrl;
    } catch { /* chưa lên */ }
    await sleep(250);
  }
  throw new Error("Chrome không mở được cổng debug.");
}
const ws = new WebSocket(await connect());
await new Promise((r) => (ws.onopen = r));
let id = 0; const pending = new Map();
ws.onmessage = (e) => { const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } };
const send = (method, params = {}) => new Promise((res) => {
  const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const evaluate = async (expr) => {
  const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails).slice(0, 400));
  return r.result?.result?.value;
};
await send("Page.enable"); await send("Runtime.enable");
mkdirSync(OUT, { recursive: true });

const PROBE = `(() => {
  const de = document.documentElement;
  const vw = de.clientWidth;
  const over = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    const cs = getComputedStyle(el);
    const mw = cs.minWidth;
    const spills = r.right > vw + 1 || r.left < -1;
    const rigid = mw && mw !== '0px' && mw !== 'auto' && parseFloat(mw) > vw;
    if (spills || rigid) {
      over.push({
        tag: el.tagName.toLowerCase(),
        cls: (el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className || '').toString().slice(0, 60),
        left: Math.round(r.left), right: Math.round(r.right), width: Math.round(r.width),
        min_width: mw, overflow_x: cs.overflowX, display: cs.display,
        grid_template: cs.gridTemplateColumns.slice(0, 80),
        reason: spills ? 'spills_past_viewport' : 'min_width_exceeds_viewport',
      });
    }
  }
  /* Phần tử học sinh PHẢI thấy — có nằm trong khung nhìn không? */
  const named = (sel, name) => {
    const el = document.querySelector(sel);
    if (!el) return { name, present: false };
    const r = el.getBoundingClientRect();
    return { name, present: true, left: Math.round(r.left), right: Math.round(r.right),
             width: Math.round(r.width), inside: r.right <= vw + 1 && r.left >= -1 };
  };
  /* BỊ TỔ TIÊN CẮT: phần tử nằm TRONG khung nhìn nhưng tràn khỏi vùng hiển
     thị của một tổ tiên có overflow ẩn/cuộn. Đây mới là dạng cắt thật đã thấy
     trong ảnh audit — kiểm "ngoài viewport" KHÔNG bắt được nó. */
  const clippedBy = (el) => {
    const r = el.getBoundingClientRect();
    for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
      const cs = getComputedStyle(p);
      if (!/hidden|clip|auto|scroll/.test(cs.overflowX)) continue;
      const pr = p.getBoundingClientRect();
      if (r.right > pr.right + 1 || r.left < pr.left - 1) {
        return { by: p.tagName.toLowerCase() + '.' +
                 ((p.className && p.className.baseVal !== undefined ? p.className.baseVal : p.className || '').toString().split(' ')[0]),
                 overflow_x: cs.overflowX,
                 spill_right: Math.round(r.right - pr.right) };
      }
    }
    return null;
  };
  const buttons = [...document.querySelectorAll('button')].map((b) => {
    const r = b.getBoundingClientRect();
    return { text: (b.textContent || '').trim().slice(0, 20),
             right: Math.round(r.right), inside: r.right <= vw + 1 && r.left >= -1,
             clipped_by_ancestor: clippedBy(b) };
  });
  const clippedContent = [...document.querySelectorAll(
      '.workspace-title, .sim-stage, .notes, .hint, svg, [class*="panel"]')]
    .map((el) => ({ sel: el.tagName.toLowerCase() + '.' +
        ((el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className || '').toString().split(' ')[0]),
        text: (el.textContent || '').trim().slice(0, 34), clip: clippedBy(el) }))
    .filter((x) => x.clip);
  /* ── W4B-1A: TRỤC CHIỀU CAO ────────────────────────────────────────────
     Chẩn đoán cũ CHỈ đo chiều rộng, nên một shell cao đúng một màn
     ('height: calc(100vh - 57px)' + panel cuộn bên trong) luôn báo "sạch"
     trong khi học sinh phải thu nhỏ browser mới đọc được cơ chế. Ba dấu hiệu
     phân biệt: trang có cuộn được không · panel có cuộn NGẦM bên trong không ·
     sân khấu còn lại bao nhiêu chiều cao. */
  const vh = de.clientHeight;
  const clsOf = (el) => (el.className && el.className.baseVal !== undefined
    ? el.className.baseVal : el.className || '').toString().split(' ')[0];
  const box = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return { sel, present: false };
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return { sel, present: true,
             top: Math.round(r.top), bottom: Math.round(r.bottom),
             height: Math.round(r.height), width: Math.round(r.width),
             client_height: el.clientHeight, scroll_height: el.scrollHeight,
             inner_scroll: el.scrollHeight > el.clientHeight + 1,
             hidden_px: Math.max(0, el.scrollHeight - el.clientHeight),
             overflow_y: cs.overflowY, css_height: cs.height,
             css_min_height: cs.minHeight, css_max_height: cs.maxHeight,
             below_fold: r.bottom > vh + 1 };
  };
  /* Hit-test THẬT tại tâm control: elementFromPoint trả về chính nút hay một
     lớp phủ? Nút nằm ngoài khung nhìn thì elementFromPoint vô nghĩa. */
  const hitTest = [...document.querySelectorAll('.panel-controls button, .panel-controls input')]
    .map((b) => {
      const r = b.getBoundingClientRect();
      const cx = Math.round(r.left + r.width / 2), cy = Math.round(r.top + r.height / 2);
      const inView = cx >= 0 && cx <= vw && cy >= 0 && cy <= vh;
      const el = inView ? document.elementFromPoint(cx, cy) : null;
      return { text: (b.textContent || b.getAttribute('aria-label') || b.type || '').trim().slice(0, 18),
               disabled: !!b.disabled, in_viewport: inView,
               hit_self: el ? (el === b || b.contains(el)) : false,
               hit_instead: el && !(el === b || b.contains(el))
                 ? el.tagName.toLowerCase() + '.' + clsOf(el) : null };
    });
  return {
    viewport: { clientWidth: vw, clientHeight: vh,
                scrollWidth: de.scrollWidth, scrollHeight: de.scrollHeight,
                page_overflow_x: de.scrollWidth > vw + 1,
                page_scrollable_y: de.scrollHeight > vh + 1,
                hidden_below_fold_px: Math.max(0, de.scrollHeight - vh) },
    key_elements: [named('.workspace-title', 'title'), named('.sim-stage', 'canvas'),
                   named('.workspace-card', 'workspace'), named('main', 'main')],
    controls: { total: buttons.length, clipped: buttons.filter((b) => !b.inside),
                clipped_by_ancestor: buttons.filter((b) => b.clipped_by_ancestor) },
    clipped_content: clippedContent.slice(0, 10),
    offenders: over.slice(0, 14),
    /* W4B-1A */
    height_axis: {
      app_layout: box('.app-layout'), panel_center: box('.panel-center'),
      panel_right: box('.panel-right'), panel_controls: box('.panel-controls'),
      stage: box('.sim-stage'), narration: box('.notes'),
    },
    hit_test: hitTest,
    fingerprint: {
      hash: location.hash,
      app_layout: !!document.querySelector('.app-layout'),
      panel_center: !!document.querySelector('.panel-center'),
      panel_controls: !!document.querySelector('.panel-controls'),
      stage: !!document.querySelector('.sim-stage'),
      workspace_title: (document.querySelector('.workspace-title') || {}).textContent || null,
    },
  };
})()`;

/* Điều khiển timeline — dùng LẠI đúng API store của visual-stress-audit.mjs,
   không thêm dev hook, không sửa production. Bước sau mới là bước có thuyết
   minh + vùng thao tác, tức là bước CAO NHẤT của nội dung. */
const stepCount = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const r = await import('/src/simulations/registry.ts');
  const st = s.useAppStore.getState();
  const mod = r.getSimulation(st.active.moduleId);
  return mod.timeline ? mod.timeline.stepCount(st.active.state) : 1;
})()`);
const goToStep = (n) => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const st = s.useAppStore.getState();
  const r = await import('/src/simulations/registry.ts');
  if (!r.getSimulation(st.active.moduleId).timeline) return null;
  st.goToStep(${n});
  return s.useAppStore.getState().active.state.cursor ?? null;
})()`);

const CHECKPOINTS = argOf("--checkpoints", "initial").split(",").map((s) => s.trim());
const SHOOT_ALL = args.includes("--shoot-all");

/* `--fixture catalog` — quét TOÀN DANH MỤC bằng chính `offlineCatalog()` của
   app. Không chép fixture sang script: nguồn duy nhất vẫn là dữ liệu mà học
   sinh thật sự mở được, nên danh mục lớn lên thì phép đo tự lớn theo. */
const CATALOG_MODE = ["catalog", "stress", "all"].includes(FIXTURE_ID);
const USE_APP_CATALOG = FIXTURE_ID === "catalog" || FIXTURE_ID === "all";
const USE_STRESS = FIXTURE_ID === "stress" || FIXTURE_ID === "all";
const catalogList = () => evaluate(`(async () => {
  const c = await import('/src/data/offline-catalog.ts');
  return c.offlineCatalog().map((e, i) => ({ i, id: e.id, simId: e.simId, title: e.title }));
})()`);
const loadCatalogEntry = (i) => evaluate(`(async () => {
  const c = await import('/src/data/offline-catalog.ts');
  const s = await import('/src/state/store.ts');
  const e = c.offlineCatalog()[${i}];
  s.useAppStore.getState().loadEnvelope(e.envelope);
  return e.simId;
})()`);

const results = [];
for (const vp of VIEWPORTS) {
  await send("Emulation.setDeviceMetricsOverride",
    { width: vp.width, height: vp.height, deviceScaleFactor: 1, mobile: false });
  for (const route of ROUTES) {
    await send("Page.navigate", { url: APP + route.hash });
    await sleep(1400);

    /* Danh sách "chủ thể" đo: một fixture đơn, hoặc từng mục của danh mục. */
    let subjects = [{ key: FIXTURE_ID, simId: FIXTURE_ID, index: null }];
    if (route.id === "workspace" && CATALOG_MODE) {
      subjects = [];
      if (USE_APP_CATALOG) {
        subjects.push(...(await catalogList()).map((e) => ({ key: e.id, simId: e.simId, index: e.i })));
      }
      if (USE_STRESS) {
        /* Bù đúng phần app không có mẫu offline — dùng CHUNG fixtures.mjs. */
        const seen = new Set(subjects.map((s) => s.simId));
        for (const f of STRESS_FIXTURES) {
          if (seen.has(f.target)) continue;
          seen.add(f.target);
          subjects.push({ key: f.id, simId: f.target, index: null, envelope: f.envelope });
        }
      }
      console.log(`  chủ thể: ${subjects.length} mẫu · ${new Set(subjects.map((s) => s.simId)).size} target`);
    }

  for (const subject of subjects) {
    let points = [["n/a", null]];
    if (route.id === "workspace") {
      if (subject.index !== null) {
        await loadCatalogEntry(subject.index);
      } else {
        const envelope = subject.envelope ?? FIXTURES[FIXTURE_ID];
        await evaluate(`(async () => {
          const m = await import('/src/state/store.ts');
          m.useAppStore.getState().loadEnvelope(${JSON.stringify(envelope)});
          return true; })()`);
      }
      await sleep(700);
      const total = await stepCount();
      points = CHECKPOINTS.map((name) => {
        if (name === "initial") return [name, 0];
        if (name === "mid") return [name, Math.max(0, Math.floor((total - 1) / 2))];
        if (name === "final") return [name, total - 1];
        return [name, Number.parseInt(name, 10)];
      });
    }
  for (const [cpName, cpIndex] of points) {
    if (cpIndex !== null) { await goToStep(cpIndex); await sleep(400); }
    const probe = await evaluate(PROBE);

    /* §5 DẤU VÂN TAY — một bản soát bố cục chỉ đáng tin khi nó CHỨNG MINH
       mình đứng đúng trang. audit-layout.mjs từng báo "TẤT CẢ SẠCH" vì đo
       nhầm trang (ARCHITECTURE_MAP §8 #14). Sai → thoát != 0, KHÔNG ghi PASS. */
    if (route.id === "workspace") {
      const fp = probe.fingerprint;
      const missing = ["app_layout", "panel_center", "panel_controls", "stage"].filter((k) => !fp[k]);
      if (missing.length) {
        writeFileSync(join(OUT, "WRONG_PAGE_OR_FIXTURE.json"),
          JSON.stringify({ verdict: "WRONG_PAGE_OR_FIXTURE", viewport: vp.id,
                           fixture: FIXTURE_ID, missing, fingerprint: fp }, null, 2) + "\n", "utf-8");
        console.error(`\n✗ WRONG_PAGE_OR_FIXTURE @ ${vp.id} — thiếu: ${missing.join(", ")}`);
        ws.close(); chrome.kill();
        process.exit(2);
      }
    }
    const label = cpIndex === null ? route.id
      : `${CATALOG_MODE ? subject.key : route.id}-${cpName}`;
    /* Quét toàn danh mục sinh hàng trăm khung hình — hình học JSON đã đủ chấm
       acceptance, nên chỉ chụp khi CÓ vi phạm hoặc khi được yêu cầu (§14). */
    const failedHere = probe.viewport.page_overflow_x
      || (probe.height_axis.panel_center.present && probe.height_axis.panel_center.inner_scroll)
      || probe.hit_test.some((t) => !t.hit_self) || probe.clipped_content.length > 0;
    let png = null;
    if (!CATALOG_MODE || failedHere || SHOOT_ALL) {
      const shot = await send("Page.captureScreenshot", { format: "png" });
      png = join(OUT, `${label}-${vp.id}.png`);
      if (shot.result?.data) writeFileSync(png, Buffer.from(shot.result.data, "base64"));
    }
    /* `viewport_id` chứ không phải `viewport`: `...probe` mang theo khoá
       `viewport` (object hình học) và sẽ ghi đè chuỗi nhãn. */
    results.push({ route: route.id, subject: subject.key, simulation_id: subject.simId,
                   checkpoint: cpName, cursor: cpIndex,
                   viewport_id: vp.id, screenshot: png ? png.replace(/\\/g, "/") : null, ...probe });
    const bad = probe.viewport.page_overflow_x || probe.controls.clipped.length
      || probe.controls.clipped_by_ancestor.length || probe.clipped_content.length
      || probe.key_elements.some((k) => k.present && !k.inside);
    /* Quét danh mục chỉ in ra ca CÓ vấn đề — 22 mẫu × 2 bước × 2 viewport mà in
       hết thì bảng kết quả không đọc được. */
    if (!CATALOG_MODE || failedHere) {
      console.log(`  ${label}/${vp.id}  scrollW ${probe.viewport.scrollWidth}/${probe.viewport.clientWidth}` +
        `  nút-bị-cắt ${probe.controls.clipped_by_ancestor.length}` +
        `  nội-dung-bị-cắt ${probe.clipped_content.length}  ${bad ? "⚠" : "ok"}`);
      if (route.id === "workspace") {
        const h = probe.height_axis;
        const noHit = probe.hit_test.filter((t) => !t.hit_self).length;
        console.log(`      CAO  sân-khấu ${h.stage.present ? h.stage.height : "—"}px` +
          `  center ${h.panel_center.client_height}/${h.panel_center.scroll_height}` +
          (h.panel_center.inner_scroll ? ` GIẤU ${h.panel_center.hidden_px}px` : " vừa") +
          `  trang-cuộn-được ${probe.viewport.page_scrollable_y ? "có" : "KHÔNG"}` +
          `  control-không-bấm-được ${noHit}`);
      }
    }
  }
  }
  }
  if (CATALOG_MODE) console.log(`  → xong ${vp.id}`);
}
/* ── §10 ACCEPTANCE — chấm máy, có mã thoát ────────────────────────────────
   Một bản soát chỉ là bằng chứng khi nó ĐỎ ĐƯỢC. Bốn điều kiện dưới đây đều
   suy từ hình học đo được, không từ ảnh chụp. */
const failures = [];
for (const r of results) {
  if (r.route !== "workspace") continue;
  const where = `${r.simulation_id ?? r.subject}  ${r.viewport_id}/${r.checkpoint}`;
  if (r.viewport.page_overflow_x) {
    failures.push({ where, type: "HORIZONTAL_OVERFLOW",
                    detail: `scrollWidth ${r.viewport.scrollWidth} > clientWidth ${r.viewport.clientWidth}` });
  }
  const pc = r.height_axis.panel_center;
  if (pc.present && pc.inner_scroll) {
    failures.push({ where, type: "CONTENT_HIDDEN_IN_PANEL",
                    detail: `.panel-center giấu ${pc.hidden_px}px sau thanh cuộn nội bộ` });
  }
  const occluded = r.hit_test.filter((t) => t.in_viewport && !t.hit_self);
  if (occluded.length) {
    failures.push({ where, type: "CONTROL_OCCLUDED",
                    detail: occluded.map((o) => `${o.text} ← ${o.hit_instead}`).join(" · ") });
  }
  const offscreen = r.hit_test.filter((t) => !t.in_viewport);
  if (offscreen.length) {
    failures.push({ where, type: "CONTROL_OFFSCREEN",
                    detail: offscreen.map((o) => o.text).join(" · ") });
  }
  if (r.clipped_content.length) {
    failures.push({ where, type: "TEXT_CLIPPED",
                    detail: r.clipped_content.map((c) => c.sel).join(" · ") });
  }
}
const verdict = failures.length ? "FAIL" : "PASS";
writeFileSync(join(OUT, "responsive-diagnosis.json"),
  JSON.stringify({ app: APP, generated_at: new Date().toISOString(),
                   fixture: FIXTURE_ID, zoom: "100% (deviceScaleFactor=1, mobile=false)",
                   viewports: VIEWPORTS, verdict, failures, results }, null, 2) + "\n", "utf-8");
console.log(`\n${verdict === "PASS" ? "✓ PASS" : `✗ FAIL — ${failures.length} vi phạm`}`);
for (const f of failures) console.log(`   ${f.where}  ${f.type}  ${f.detail}`);
console.log(`→ ${OUT}`);
ws.close(); chrome.kill();
process.exit(verdict === "PASS" ? 0 : 1);
