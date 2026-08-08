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
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

import { FIXTURES as STRESS_FIXTURES } from "./fixtures.mjs";

const args = process.argv.slice(2);
const argOf = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const APP = `http://localhost:${argOf("--port", "3000")}`;
const OUT = resolve(argOf("--out", "../docs/evaluation/m17/rc1/visual/before/VIS-003"));

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

/* ── W4B-1A.1 §3A — MỖI LƯỢT CHẠY SỞ HỮU CHROME CỦA RIÊNG NÓ ────────────────
   Trước đây cổng CDP là hằng số 9337. Hai lượt chạy song song (hoặc một lượt
   trước đó ném lỗi và bỏ lại Chrome mồ côi) thì `connect()` **bám vào trình
   duyệt của lượt khác** và trả về hình học của trang khác — mà dấu vân tay cũ
   chỉ kiểm cấu trúc DOM nên không phát hiện được. Đã xảy ra thật: hai agent
   critique chạy đồng thời và sinh ra một artifact gắn nhãn sai fixture.

   Cách chữa: `--remote-debugging-port=0` để Chrome tự chọn cổng rảnh, rồi đọc
   cổng thật từ `DevToolsActivePort` trong CHÍNH profile của lượt này. Không có
   hằng số nào để đụng nhau, và không cần dò cổng rảnh (dò vẫn còn khe hở race). */
const profile = mkdtempSync(join(tmpdir(), "algosim-e1-"));
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu",
  "--remote-debugging-port=0", `--user-data-dir=${profile}`,
  "--window-size=1440,1000", "--hide-scrollbars", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* ── §3D — ĐƯỜNG DỌN DẸP ĐẢM BẢO ───────────────────────────────────────────
   Trước đây `chrome.kill()` chỉ nằm trên hai đường thoát bình thường, nên một
   assertion đỏ hay một exception giữa chừng đều bỏ lại tiến trình Chrome sống.
   Nay mọi lối ra — thành công, thoát mã != 0, throw, unhandled rejection,
   SIGINT/SIGTERM — đều đi qua `shutdown()`. Handler của 'exit' phải ĐỒNG BỘ. */
let closed = false;
function shutdown() {
  if (closed) return;
  closed = true;
  try { globalThis.__algosimWs?.close(); } catch { /* ws có thể chưa mở */ }
  try { chrome.kill(); } catch { /* đã chết */ }
}
process.on("exit", shutdown);
process.on("SIGINT", () => { shutdown(); process.exit(130); });
process.on("SIGTERM", () => { shutdown(); process.exit(143); });
for (const ev of ["uncaughtException", "unhandledRejection"]) {
  process.on(ev, (err) => {
    console.error(`\n✗ ${ev}:`, err instanceof Error ? err.stack : err);
    shutdown();
    process.exit(3);
  });
}

let CDP_PORT = null;
async function resolvePort() {
  const portFile = join(profile, "DevToolsActivePort");
  for (let i = 0; i < 80; i++) {
    if (existsSync(portFile)) {
      const first = readFileSync(portFile, "utf-8").split("\n")[0].trim();
      if (first && Number(first) > 0) return Number(first);
    }
    await sleep(125);
  }
  throw new Error("Chrome không ghi DevToolsActivePort — không xác định được cổng CDP.");
}

async function connect() {
  CDP_PORT = await resolvePort();
  for (let i = 0; i < 40; i++) {
    try {
      const l = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`)).json();
      const p = l.find((t) => t.type === "page");
      if (p) return p.webSocketDebuggerUrl;
    } catch { /* chưa lên */ }
    await sleep(250);
  }
  throw new Error(`Chrome không phản hồi trên cổng CDP ${CDP_PORT}.`);
}
const ws = new WebSocket(await connect());
globalThis.__algosimWs = ws;
console.log(`  phiên: chrome pid ${chrome.pid} · cổng CDP ${CDP_PORT} · profile ${profile}`);
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
             /* W4B-1A.1 §4/§5 — hợp đồng BỀ RỘNG. align-self + margin ngang là
                cặp quyết định một flex item có stretch hay co theo nội dung:
                auto margin trên trục ngang triệt tiêu stretch. */
             css_max_width: cs.maxWidth, css_width: cs.width,
             css_margin_left: cs.marginLeft, css_margin_right: cs.marginRight,
             align_self: cs.alignSelf, display: cs.display,
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
      root: box('#root'),
      /* W4B-2A — HÌNH VẼ THẬT bên trong sân khấu, không phải khung sân khấu.
         Lấy phần tử vẽ CÓ DIỆN TÍCH LỚN NHẤT trong sim-stage (svg hoặc canvas):
         một sân khấu có thể chứa nhiều svg nhỏ (ô chú giải), nên lấy phần tử
         đầu tiên theo thứ tự DOM sẽ đo nhầm cái chú giải.
         (Lưu ý: khối này nằm TRONG template literal — cấm dùng backtick.) */
      visual: (() => {
        /* W4B-2A - them 'table': renderer dang bang khong ve bang SVG, nen phep
           do "phan tu ve lon nhat" cu bat nham mot icon 12x12 va bao no chiem
           1% san khau. Bang la mot hop dong rieng, khong so ti le voi SVG. */
        const cands = [...document.querySelectorAll('.sim-stage svg, .sim-stage canvas, .sim-stage table')];
        if (!cands.length) return { sel: '.sim-stage svg|canvas', present: false };
        let best = cands[0], bestArea = -1;
        for (const el of cands) {
          const r = el.getBoundingClientRect();
          const area = r.width * r.height;
          if (area > bestArea) { bestArea = area; best = el; }
        }
        const r = best.getBoundingClientRect();
        const cs = getComputedStyle(best);
        return { sel: best.tagName.toLowerCase(), present: true,
                 top: Math.round(r.top), bottom: Math.round(r.bottom),
                 width: Math.round(r.width), height: Math.round(r.height),
                 css_max_width: cs.maxWidth, css_width: cs.width,
                 view_box: best.getAttribute && best.getAttribute('viewBox') };
      })(),
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
      has_canvas: !!document.querySelector('.sim-stage canvas'),
      workspace_title: (document.querySelector('.workspace-title') || {}).textContent || null,
    },
  };
})()`;

/* Điều khiển timeline — dùng LẠI đúng API store của visual-stress-audit.mjs,
   không thêm dev hook, không sửa production. Bước sau mới là bước có thuyết
   minh + vùng thao tác, tức là bước CAO NHẤT của nội dung. */
/* Null-safe: sau `Page.navigate` store về rỗng, và một envelope không qua được
   validator cũng để `active` = null. Ném thẳng ReferenceError ở đây thì lượt
   chạy chết không nói được đang đo mẫu nào — trả null để dấu vân tay báo đúng. */
const stepCount = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const r = await import('/src/simulations/registry.ts');
  const st = s.useAppStore.getState();
  if (!st.active) return 0;
  const mod = r.getSimulation(st.active.moduleId);
  if (!mod) return 0;
  return mod.timeline ? mod.timeline.stepCount(st.active.state) : 1;
})()`);
const goToStep = (n) => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const st = s.useAppStore.getState();
  const r = await import('/src/simulations/registry.ts');
  if (!st.active) return null;
  const m = r.getSimulation(st.active.moduleId);
  if (!m || !m.timeline) return null;
  st.goToStep(${n});
  return s.useAppStore.getState().active.state.cursor ?? null;
})()`);

/** §3 — hợp đồng vừa-khung, KHAI TỪ NGUỒN chứ không hard-code theo moduleId. */
const rendererFit = () => evaluate(`(async () => {
  const m = await import('/src/simulations/renderer-fit.ts');
  return m.currentRendererFit();
})()`);

/** §3B — danh tính AUTHORITATIVE: hỏi engine store, không suy từ DOM. */
const activeIdentity = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const a = s.useAppStore.getState().active;
  return a ? { moduleId: a.moduleId } : null;
})()`);

const CHECKPOINTS = argOf("--checkpoints", "initial").split(",").map((s) => s.trim());
const SHOOT_ALL = args.includes("--shoot-all");

/* W4B-2A §2 — CHẾ ĐỘ HIỂN THỊ do runner yêu cầu tường minh.
   Một bản render 2D bị lưu thành artifact 3D là lỗi NẶNG, nên chế độ phải nằm
   trong dấu vân tay chứ không phải giả định. */
const ONLY_TARGET = argOf("--only-target", null);
const VISUAL_MODE = argOf("--visual-mode", null);
if (VISUAL_MODE && !["2d", "3d"].includes(VISUAL_MODE)) {
  console.error(`--visual-mode phải là 2d hoặc 3d (nhận: ${VISUAL_MODE})`);
  process.exit(2);
}

/** Đổi chế độ rồi CHỜ ĐIỀU KIỆN THẬT — không ngủ một khoảng tuỳ tiện. */
const requestVisualMode = (mode) => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const st = s.useAppStore.getState();
  if (typeof st.setVisualMode !== 'function') return { ok: false, why: 'no_api' };
  st.setVisualMode('${mode}');
  return { ok: true };
})()`);

const visualModeState = (mode) => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const st = s.useAppStore.getState();
  const wanted = '${mode}';
  const canvas = !!document.querySelector('.sim-stage canvas');
  const svg = !!document.querySelector('.sim-stage svg');
  /* Voi 3D, be mat WebGL PHAI ton tai; voi 2D thi phai co SVG hoac bang. */
  const rootOk = wanted === '3d'
    ? canvas
    : (svg || !!document.querySelector('.sim-stage table'));
  return { mode: st.visualMode ?? null, moduleId: st.active ? st.active.moduleId : null,
           canvas, svg, ready: st.visualMode === wanted && rootOk };
})()`);

/* W4B-2A — trạng thái panel Quan sát. Đóng panel là phép thử QUYẾT ĐỊNH cho
   lớp ADAPTIVE_LAYOUT: sân khấu rộng thêm ~300px thì hình vẽ có lớn theo không,
   hay chỉ đẻ thêm khoảng trắng. Chạy hai lượt riêng (open/closed) thay vì lồng
   thêm một vòng lặp nữa vào runner. */
const OBSERVATION = argOf("--observation", "open");
if (!["open", "closed"].includes(OBSERVATION)) {
  console.error(`--observation phải là open hoặc closed (nhận: ${OBSERVATION})`);
  process.exit(2);
}
const setObservation = (open) => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const st = s.useAppStore.getState();
  if (st.rightOpen !== ${open}) st.toggleRight();
  return s.useAppStore.getState().rightOpen;
})()`);
/* §3D — TIÊM LỖI TÁI LẬP ĐƯỢC cho cổng dọn dẹp. Ném đúng sau khi Chrome đã
   chạy và đã nối CDP: nếu `shutdown()` không nằm trên đường thoát ngoại lệ thì
   tiến trình Chrome sẽ sống sót và lượt sau bám vào nó. Chứng minh guard đỏ
   được mà không phải sửa tạm file rồi hoàn tác. */
if (args.includes("--self-test-throw")) {
  throw new Error("SELF_TEST: lỗi giả sau khi Chrome khởi động (kiểm đường dọn dẹp).");
}

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
  /* BẮT BUỘC: bảo đảm registry ĐÃ ĐĂNG KÝ trên chính nhánh module này.
     'loadEnvelope' tra 'getSimulation(simulation_id)'; không thấy module thì nó
     đặt 'analysisError' rồi THOÁT IM LẶNG — 'active' giữ null và 'error' vẫn
     null, nên nhìn từ ngoài giống hệt "nạp xong mà không có gì". Nhánh nạp một
     fixture đơn không dính vì nó chỉ chạm 'store' (cùng thể hiện app đã khởi
     tạo), còn nhánh catalog kéo theo 'offline-catalog' và có thể chạm một thể
     hiện registry chưa chạy đăng ký. 'registerAllSimulations' idempotent nên
     gọi thừa vô hại. */
  const r = await import('/src/simulations/index.ts');
  r.registerAllSimulations();
  const e = c.offlineCatalog()[${i}];
  s.useAppStore.getState().loadEnvelope(e.envelope);
  const after = s.useAppStore.getState();
  return { simId: e.simId, appliedNow: !!after.active,
           activeId: after.active ? after.active.moduleId : null, err: after.error ?? null };
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
      /* Loc theo target: can thiet de do rieng mot target o che do 3D ma khong
         bat moi target 2D-only phai doi sang 3D roi that bai. */
      if (ONLY_TARGET) subjects = subjects.filter((s) => s.simId === ONLY_TARGET);
      console.log(`  chủ thể: ${subjects.length} mẫu · ${new Set(subjects.map((s) => s.simId)).size} target`);
    }

  for (const subject of subjects) {
    let points = [["n/a", null]];
    if (route.id === "workspace") {
      if (subject.index !== null) {
        const res = await loadCatalogEntry(subject.index);
        if (!res || !res.appliedNow) {
          console.error(`  ! loadEnvelope không có hiệu lực ngay: ${JSON.stringify(res)}`);
        }
      } else {
        const envelope = subject.envelope ?? FIXTURES[FIXTURE_ID];
        /* Cùng lý do như nhánh catalog: loadEnvelope tra registry, registry
           rỗng thì nó đặt analysisError rồi thoát im lặng. Nhánh này trước đây
           "may thì chạy" — phụ thuộc app đã kịp đăng ký hay chưa. Ép đăng ký ở
           đây làm phép đo tất định thay vì phụ thuộc thời điểm. */
        await evaluate(`(async () => {
          const m = await import('/src/state/store.ts');
          const r = await import('/src/simulations/index.ts');
          r.registerAllSimulations();
          m.useAppStore.getState().loadEnvelope(${JSON.stringify(envelope)});
          return true; })()`);
      }
      /* Chờ store THẬT SỰ có mô phỏng trước khi đo. Lượt đầu của mỗi tiến trình
         luôn chậm hơn: Vite dev biên dịch module theo yêu cầu, nên `loadEnvelope`
         trả về trước khi `active` kịp có. Trước khi có vòng chờ này, dấu vân tay
         danh tính bắt đúng ca đó và thoát 2 — guard làm đúng việc, nhưng cái sai
         nằm ở chỗ đo quá sớm chứ không phải ở trang. */
      let ready = null;
      for (let tries = 0; tries < 24 && !ready; tries++) {
        await sleep(250);
        ready = await activeIdentity();
      }
      if (!ready) {
        /* Không đoán vì sao nạp hỏng — HỎI store. `loadEnvelope` fail-closed:
           config không qua validator thì `active` giữ null và lỗi nằm ở `error`. */
        const why = await evaluate(`(async () => {
          const s = await import('/src/state/store.ts');
          const st = s.useAppStore.getState();
          /* analysisError chu khong phai error - day chinh la truong ma
             loadEnvelope dat khi khong tra duoc module. (Khoi nay nam TRONG
             template literal: cam backtick.) */
          return { analysisError: st.analysisError ?? null, error: st.error ?? null,
                   view: st.view ?? null, hasActive: !!st.active };
        })()`);
        console.error(`  ✗ nạp hỏng: ${subject.key} (${subject.simId}) → ${JSON.stringify(why)}`);
      }
      /* §3 — đổi chế độ hiển thị và CHỜ ĐIỀU KIỆN, không ngủ tuỳ tiện. */
      if (VISUAL_MODE) {
        await requestVisualMode(VISUAL_MODE);
        let vm = null;
        for (let tries = 0; tries < 40; tries++) {
          await sleep(250);
          vm = await visualModeState(VISUAL_MODE);
          if (vm && vm.ready) break;
        }
        if (!vm || !vm.ready) {
          writeFileSync(join(OUT, "WRONG_VISUAL_MODE_OR_RENDERER.json"),
            JSON.stringify({ verdict: "WRONG_VISUAL_MODE_OR_RENDERER",
                             subject: subject.key, expected_simulation_id: subject.simId,
                             expected_visual_mode: VISUAL_MODE, actual: vm,
                             viewport: vp.id }, null, 2) + "\n", "utf-8");
          console.error(`\n✗ WRONG_VISUAL_MODE_OR_RENDERER — chờ ${VISUAL_MODE}, gặp ${JSON.stringify(vm)}`);
          shutdown();
          process.exit(2);
        }
      }
      await setObservation(OBSERVATION === "open");
      await sleep(250);
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

      /* §3B — DẤU VÂN TAY DANH TÍNH, không chỉ hình dạng DOM.
         Bản cũ chỉ hỏi "có phải một workspace không". Một Chrome bị bám nhầm
         vẫn là workspace hợp lệ — chỉ là của mô phỏng KHÁC. Nay hỏi thẳng
         engine store xem đang mở ĐÚNG mô phỏng nào. */
      const identity = await activeIdentity();
      const expected = subject.simId;
      const idMismatch = expected && (!identity || identity.moduleId !== expected);

      if (missing.length || idMismatch) {
        const verdict = idMismatch ? "WRONG_SIMULATION_OR_FIXTURE" : "WRONG_PAGE_OR_FIXTURE";
        writeFileSync(join(OUT, `${verdict}.json`),
          JSON.stringify({ verdict, viewport: vp.id, checkpoint: cpName,
                           fixture: FIXTURE_ID, subject: subject.key,
                           expected_simulation_id: expected,
                           actual_simulation_id: identity ? identity.moduleId : null,
                           workspace_title: fp.workspace_title,
                           chrome_pid: chrome.pid, cdp_port: CDP_PORT,
                           missing, fingerprint: fp }, null, 2) + "\n", "utf-8");
        console.error(`\n✗ ${verdict} @ ${vp.id}` +
          (idMismatch ? ` — chờ "${expected}", gặp "${identity ? identity.moduleId : "(không có)"}"` : "") +
          (missing.length ? ` — thiếu: ${missing.join(", ")}` : ""));
        shutdown();
        process.exit(2);
      }
    }
    const fit = route.id === "workspace" ? await rendererFit() : null;
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
                   checkpoint: cpName, cursor: cpIndex, observation: OBSERVATION,
                   requested_visual_mode: VISUAL_MODE,
                   renderer_fit: fit,
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
/** Ca ĐẠT của hợp đồng vừa-khung, kèm LÝ DO — artifact phải phân biệt được
    "lớn lên đúng" với "đã chạm trần" với "cố ý giữ nguyên kích thước". */
const fitPasses = [];
for (const r of results) {
  if (r.route !== "workspace") continue;
  const where = `${r.simulation_id ?? r.subject}  ${r.viewport_id}/${r.checkpoint}`;
  if (r.viewport.page_overflow_x) {
    failures.push({ where, type: "HORIZONTAL_OVERFLOW",
                    detail: `scrollWidth ${r.viewport.scrollWidth} > clientWidth ${r.viewport.clientWidth}` });
  }
  /* §5 LAYOUT_NOT_USING_VIEWPORT — bố cục bỏ không màn hình.
     Guard W4B-1A chỉ hỏi "có tràn / có bị giấu / có bị che". Không điều kiện nào
     hỏi "app có DÙNG màn hình không", nên một shell bỏ trống 46% bề rộng vẫn
     PASS sạch. Bề rộng mong đợi DẪN XUẤT từ hợp đồng CSS đo được — không phải
     một tỉ lệ cố định áp cho mọi breakpoint:
       màn hẹp hơn max-width  → phải dùng gần trọn bề rộng khung cha;
       màn rộng hơn max-width → phải đạt đúng max-width đã khai. */
  const al = r.height_axis.app_layout, root = r.height_axis.root;
  if (al.present && root && root.present) {
    const declared = Number.parseFloat(al.css_max_width);
    const cap = Number.isFinite(declared) ? declared : Infinity;
    const expected = Math.min(root.width, cap);
    const deadMargin = root.width - al.width;
    if (al.width < expected - 4) {
      failures.push({ where, type: "LAYOUT_NOT_USING_VIEWPORT",
                      detail: `.app-layout ${al.width}px < mong đợi ${Math.round(expected)}px ` +
                              `(khung cha ${root.width}px · max-width ${al.css_max_width}) ` +
                              `⇒ lề chết ${Math.round(deadMargin)}px` });
    }
  }

  /* §3 VISUAL_FIT_OUT_OF_RANGE — hợp đồng vừa-khung, CÓ Ý THỨC VỀ LỚP.
     Cố ý KHÔNG phải "hình phải chiếm ≥ X% sân khấu": luật đó thưởng cho hướng
     hỏng thứ hai (phình quá mức) — mà đó là lỗi đã xảy ra thật ở milestone này.
     Ba phán quyết: UNDER_UTILIZED · ACCEPTABLE · OVER_EXPANDED. */
  const stage = r.height_axis.stage, vis = r.height_axis.visual, fit = r.renderer_fit;
  if (fit && stage && stage.present && vis && vis.present) {
    const TOL = 6;
    if (fit.cls === "adaptive_layout" && fit.semanticMaxWidth) {
      const room = Math.max(0, stage.width - 24);
      const expected = Math.min(fit.semanticMaxWidth, room);
      if (vis.width < expected - TOL) {
        failures.push({ where, type: "VISUAL_FIT_OUT_OF_RANGE",
                        detail: `UNDER_UTILIZED — hình ${vis.width}px < mong đợi ${Math.round(expected)}px ` +
                                `(sân khấu ${stage.width}px · trần ngữ nghĩa ${fit.semanticMaxWidth}px)` });
      } else if (fit.maxWidthPerItem && fit.itemCount &&
                 vis.width / fit.itemCount > fit.maxWidthPerItem) {
        failures.push({ where, type: "VISUAL_FIT_OUT_OF_RANGE",
                        detail: `OVER_EXPANDED — ${Math.round(vis.width / fit.itemCount)}px/phần tử ` +
                                `> trần mật độ ${fit.maxWidthPerItem}px (hình ${vis.width}px, ${fit.itemCount} phần tử)` });
      } else {
        fitPasses.push({ where, verdict: "ACCEPTABLE",
                         reason: vis.width >= fit.semanticMaxWidth - TOL
                           ? "SEMANTIC_MAX_REACHED" : "RESPONSIVE_GROWTH" });
      }
    } else if (fit.cls === "canvas_fill") {
      const room = Math.max(0, stage.width - 24);
      if (vis.width < room * 0.9) {
        failures.push({ where, type: "VISUAL_FIT_OUT_OF_RANGE",
                        detail: `UNDER_UTILIZED — canvas ${vis.width}px không bám khung sân khấu ${stage.width}px` });
      } else {
        fitPasses.push({ where, verdict: "ACCEPTABLE", reason: "CANVAS_FILL" });
      }
    } else if (fit.cls === "fixed_semantic_size") {
      // Phản ứng 0px theo bề rộng là CHỦ ĐÍCH ở lớp này — không đòi hình lớn lên.
      fitPasses.push({ where, verdict: "ACCEPTABLE", reason: "FIXED_SEMANTIC_SIZE" });
    }
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
                   /* §3A/§3C — danh tính PHIÊN: hai lượt song song phải khác cả
                      hai giá trị này thì mới chứng minh được không bám chéo. */
                   session: { chrome_pid: chrome.pid, cdp_port: CDP_PORT, profile },
                   viewports: VIEWPORTS, verdict, failures, fit_passes: fitPasses, results }, null, 2) + "\n", "utf-8");
console.log(`\n${verdict === "PASS" ? "✓ PASS" : `✗ FAIL — ${failures.length} vi phạm`}`);
for (const f of failures) console.log(`   ${f.where}  ${f.type}  ${f.detail}`);
console.log(`→ ${OUT}`);
shutdown();
process.exit(verdict === "PASS" ? 0 : 1);
