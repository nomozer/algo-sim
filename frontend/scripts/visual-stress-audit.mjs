/**
 * visual-stress-audit.mjs — M17-RC1 §E: AUDIT THỊ GIÁC TOÀN DANH MỤC
 *
 * Dùng LẠI hạ tầng CDP của audit-layout.mjs / capture-tree-visual.mjs (Chrome
 * headless + WebSocket thô), KHÔNG thêm framework E2E. Nạp fixture qua module
 * graph của Vite dev (`import('/src/state/store.ts')`) — không sửa production,
 * không thêm dev hook.
 *
 * Mỗi fixture chụp initial · mid · final ở 2 viewport (desktop + hẹp), kèm
 * ASSERTION TỰ ĐỘNG chạy TRONG TRÌNH DUYỆT THẬT (computed style, hình học,
 * chồng lấn, thuật ngữ) — không dùng SSR làm bằng chứng.
 *
 * Chạy:  npm run dev  (cửa sổ khác)
 *        node scripts/visual-stress-audit.mjs [--only network] [--port 3000]
 */

import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const APP = `http://localhost:${argOf("--port", "3000")}`;
const CDP_PORT = 9336;
const OUT_DIR = resolve(argOf("--out", "../docs/evaluation/m17/rc1/visual"));
const ONLY = argOf("--only", null);

const VIEWPORTS = [
  { id: "desktop", width: 1440, height: 1000 },
  { id: "narrow", width: 768, height: 900 },
];

/* ══════════════ FIXTURE ══════════════
 * W4B-1A: bộ fixture đã TÁCH sang `fixtures.mjs` để bản soát responsive dùng
 * chung đúng dữ liệu này (app chỉ có mẫu offline cho 13/22 target). Dữ liệu
 * không đổi một dòng — chỉ đổi nơi ở. */
import { FIXTURES, REFUSALS } from "./fixtures.mjs";

/* ══════════════ CDP ══════════════ */
const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

const profile = mkdtempSync(join(tmpdir(), "algosim-rc1e-"));
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", `--remote-debugging-port=${CDP_PORT}`,
  `--user-data-dir=${profile}`, "--window-size=1440,1000", "--hide-scrollbars", "about:blank",
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function connect() {
  for (let i = 0; i < 40; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`)).json();
      const page = list.find((t) => t.type === "page");
      if (page) return page.webSocketDebuggerUrl;
    } catch { /* chưa lên */ }
    await sleep(250);
  }
  throw new Error("Chrome không mở được cổng debug.");
}

const ws = new WebSocket(await connect());
await new Promise((r) => (ws.onopen = r));
let id = 0;
const pending = new Map();
ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
};
const send = (method, params = {}) => new Promise((res) => {
  const i = ++id; pending.set(i, res);
  ws.send(JSON.stringify({ id: i, method, params }));
});
const evaluate = async (expr) => {
  const r = await send("Runtime.evaluate", {
    expression: expr, returnByValue: true, awaitPromise: true,
  });
  const ex = r.result?.exceptionDetails;
  if (ex) throw new Error(JSON.stringify(ex).slice(0, 500));
  return r.result?.result?.value;
};

await send("Page.enable");
await send("Runtime.enable");
mkdirSync(OUT_DIR, { recursive: true });

async function shot(renderer, name) {
  const dir = join(OUT_DIR, renderer);
  mkdirSync(dir, { recursive: true });
  const r = await send("Page.captureScreenshot", { format: "png" });
  const data = r.result?.data;
  if (!data) throw new Error(`captureScreenshot thất bại: ${name}`);
  const path = join(dir, `${name}.png`);
  writeFileSync(path, Buffer.from(data, "base64"));
  return path.replace(/\\/g, "/");
}

const setViewport = (vp) => send("Emulation.setDeviceMetricsOverride", {
  width: vp.width, height: vp.height, deviceScaleFactor: 1, mobile: false,
});

const loadEnvelope = (envelope) => evaluate(`(async () => {
  const m = await import('/src/state/store.ts');
  m.useAppStore.getState().loadEnvelope(${JSON.stringify(envelope)});
  return true;
})()`);

const loadUnsupported = (reason, category = "insufficient_specification") =>
  evaluate(`(async () => {
  const m = await import('/src/state/store.ts');
  m.useAppStore.getState().loadUnsupported({
    status: 'unsupported', reason: ${JSON.stringify(reason)},
    learner_reason: ${JSON.stringify(reason)},
    failure_category: ${JSON.stringify(category)},
  });
  return true;
})()`);

/** stepCount qua capability timeline; module exploratory → 1. */
const stepCount = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const r = await import('/src/simulations/registry.ts');
  const st = s.useAppStore.getState();
  const mod = r.getSimulation(st.active.moduleId);
  if (!mod.timeline) return 1;
  return mod.timeline.stepCount(st.active.state);
})()`);

const goToStep = (n) => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const st = s.useAppStore.getState();
  const r = await import('/src/simulations/registry.ts');
  if (!r.getSimulation(st.active.moduleId).timeline) return null;
  st.goToStep(${n});
  return s.useAppStore.getState().active.state.cursor ?? null;
})()`);

/** Trạng thái AUTHORITATIVE — đọc thẳng engine state, không suy từ DOM. */
const engineState = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const st = s.useAppStore.getState().active;
  const keys = ['cursor','frontierKind','visitedOrder','path','reachable','result',
                'decimalValue','bits','bitWidth','values','nodeOutputs','route','pos'];
  const out = { moduleId: st.moduleId };
  for (const k of keys) if (st.state && st.state[k] !== undefined) out[k] = st.state[k];
  const steps = st.state?.steps ?? st.state?.trace ?? st.state?.timeline;
  if (Array.isArray(steps)) {
    out.step_total = steps.length;
    const cur = steps[st.state.cursor ?? 0];
    if (cur) out.current_step = { kind: cur.kind ?? cur.type ?? null,
                                 narration: cur.narration ?? null };
  }
  return JSON.stringify(out);
})()`);

/* ══════════════ ASSERTION TRONG TRÌNH DUYỆT THẬT ══════════════ */
const AUDIT_JS = `(() => {
  const root = document.querySelector('main') || document.body;
  const vis = (el) => {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' &&
           cs.display !== 'none' && Number(cs.opacity) > 0.05;
  };
  const rectOf = (el) => { const r = el.getBoundingClientRect();
    return { x: r.x, y: r.y, w: r.width, h: r.height }; };
  const inter = (a, b) => {
    const w = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
    const h = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
    return w > 0 && h > 0 ? w * h : 0;
  };

  /* A. TÍNH TOÀN VẸN CSS/SVG — đọc COMPUTED STYLE THẬT trong Chrome.
     Phantom token (var(--khong-ton-tai)) làm khai báo bị BỎ, nên stroke rơi
     về 'none'/trong suốt → cạnh VÔ HÌNH. Đây đúng lỗi đã xảy ra ở VR1. */
  const strokeIssues = [];
  const edgeEls = [...root.querySelectorAll('svg line, svg path, svg polyline')];
  for (const el of edgeEls) {
    const cs = getComputedStyle(el);
    const stroke = cs.stroke;
    const sw = parseFloat(cs.strokeWidth) || 0;
    const isMarker = el.closest('marker') !== null;
    const filled = cs.fill && cs.fill !== 'none' && !/rgba\\(0, 0, 0, 0\\)/.test(cs.fill);
    if (isMarker || filled) continue;
    if (!stroke || stroke === 'none' || /rgba\\(0, 0, 0, 0\\)/.test(stroke) || sw === 0) {
      strokeIssues.push({ tag: el.tagName, stroke, strokeWidth: cs.strokeWidth,
                          d: (el.getAttribute('d') || '').slice(0, 40) });
    }
  }
  /* var() chưa phân giải trong thuộc tính inline */
  const unresolvedVar = [...root.querySelectorAll('*')]
    .filter((el) => ['stroke','fill','style'].some((a) => (el.getAttribute(a) || '').includes('var(')))
    .filter((el) => {
      const cs = getComputedStyle(el);
      return !cs.stroke || cs.stroke === 'none' || !cs.color;
    }).length;

  /* B. HÌNH HỌC */
  const nanGeom = [...root.querySelectorAll('svg *')].filter((el) =>
    ['x','y','x1','y1','x2','y2','cx','cy','r','width','height','d','points']
      .some((a) => /NaN|Infinity/.test(el.getAttribute(a) || ''))).length;
  const zeroSize = [...root.querySelectorAll('svg circle, svg rect, svg text')]
    .filter((el) => { const r = el.getBoundingClientRect();
      return getComputedStyle(el).display !== 'none' && (r.width === 0 || r.height === 0); }).length;
  const de = document.documentElement;
  const vw = de.clientWidth, vh = window.innerHeight;
  /* §7 — tràn ngang Ở MỨC TRANG. Đây mới là thứ VIS-003 phải chứng minh. */
  const pageOverflowX = de.scrollWidth > vw + 1;
  const bodyOverflowX = pageOverflowX;
  const offViewport = [...root.querySelectorAll('button, [role="button"], input, select')]
    .filter(vis).filter((el) => { const r = el.getBoundingClientRect();
      return r.right < 0 || r.left > vw || r.bottom < 0 || r.top > vh; })
    .map((el) => (el.textContent || el.tagName).trim().slice(0, 30));

  /* §7 — BỊ TỔ TIÊN CẮT: phần tử nằm trong khung nhìn nhưng tràn khỏi vùng
     hiển thị của một tổ tiên overflow ẩn/cuộn. Kiểm "ngoài viewport" KHÔNG bắt
     được dạng này, nên bản assertion đầu của tôi bỏ lọt. */
  const clippedBy = (el) => {
    const r = el.getBoundingClientRect();
    for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
      const cs = getComputedStyle(p);
      if (!/hidden|clip/.test(cs.overflowX)) continue;   // auto/scroll = cuộn được, hợp lệ
      const pr = p.getBoundingClientRect();
      if (r.right > pr.right + 1 || r.left < pr.left - 1) {
        return { by: p.tagName.toLowerCase(), overflow_x: cs.overflowX,
                 spill_right: Math.round(r.right - pr.right) };
      }
    }
    return null;
  };
  const clippedContent = [...root.querySelectorAll(
      '.workspace-title, .sim-stage, .notes, .hint, svg, button')]
    .filter(vis)
    .map((el) => ({ tag: el.tagName.toLowerCase(),
                    text: (el.textContent || '').trim().slice(0, 34), clip: clippedBy(el) }))
    .filter((x) => x.clip).slice(0, 8);

  /* §7 — min-width CỨNG vượt viewport (nguyên nhân kinh điển làm bung layout) */
  const rigidMinWidth = [...root.querySelectorAll('*')].filter(vis).filter((el) => {
    const mw = getComputedStyle(el).minWidth;
    return mw && mw.endsWith('px') && parseFloat(mw) > vw;
  }).length;

  /* §7 — phần tử học sinh PHẢI thấy: tiêu đề, canvas, và nút "Đặt lại" */
  const named = (sel) => {
    const el = root.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { w: Math.round(r.w || r.width), inside: r.right <= vw + 1 && r.left >= -1,
             clipped: !!clippedBy(el) };
  };
  const resetBtn = [...root.querySelectorAll('button')]
    .find((b) => /Đặt lại/.test(b.textContent || ''));
  const keyElements = {
    title: named('.workspace-title'),
    canvas: named('.sim-stage'),
    reset_button: resetBtn
      ? { inside: resetBtn.getBoundingClientRect().right <= vw + 1,
          clipped: !!clippedBy(resetBtn) }
      : null,
  };

  /* C. CHỒNG LẤN — ngưỡng MÁY-ĐỌC, có lý do:
     chỉ tính khi giao > 25% diện tích phần tử NHỎ HƠN. Giao nhỏ (viền chạm
     nhau, nhãn sát cạnh) KHÔNG phải lỗi trình bày. */
  const OVERLAP_RATIO = 0.25;
  const nodes = [...root.querySelectorAll('svg circle, svg rect[data-node], [data-node]')].filter(vis);
  const labels = [...root.querySelectorAll('svg text')].filter(vis);
  const pairOverlap = (list, kind) => {
    const out = [];
    for (let i = 0; i < list.length; i++) for (let j = i + 1; j < list.length; j++) {
      const a = rectOf(list[i]), b = rectOf(list[j]);
      const area = inter(a, b);
      if (!area) continue;
      const ratio = area / Math.max(1, Math.min(a.w * a.h, b.w * b.h));
      if (ratio > OVERLAP_RATIO)
        out.push({ kind, ratio: Math.round(ratio * 100) / 100,
                   a: (list[i].textContent || list[i].tagName).trim().slice(0, 24),
                   b: (list[j].textContent || list[j].tagName).trim().slice(0, 24) });
    }
    return out;
  };
  /* node-label: nhãn ĐÈ LÊN nút (chữ nằm chồng hình tròn) — §5C liệt kê rõ,
     bản assertion đầu của tôi THIẾU nên bỏ lọt lỗi nhãn dài của graph. Nhãn
     NẰM TRONG nút (một chữ cái căn giữa) là hợp lệ; nhãn RỘNG HƠN nút mà vẫn
     căn giữa thì tràn ra hai bên và bị nút che — đó mới là lỗi. */
  const crossOverlap = (as, bs, kind, pred) => {
    const out = [];
    for (const a of as) for (const b of bs) {
      if (a === b) continue;
      const ra = rectOf(a), rb = rectOf(b);
      const area = inter(ra, rb);
      if (!area) continue;
      if (pred && !pred(ra, rb)) continue;
      const ratio = area / Math.max(1, Math.min(ra.w * ra.h, rb.w * rb.h));
      if (ratio > OVERLAP_RATIO)
        out.push({ kind, ratio: Math.round(ratio * 100) / 100,
                   a: (a.textContent || a.tagName).trim().slice(0, 28),
                   b: (b.textContent || b.tagName).trim().slice(0, 28) });
    }
    return out;
  };
  const overlaps = [
    ...pairOverlap(nodes, 'node-node'),
    ...pairOverlap(labels, 'label-label'),
    // chỉ tính khi nhãn RỘNG HƠN nút → nhãn tràn ra ngoài và bị nút cắt ngang
    ...crossOverlap(labels, nodes, 'node-label', (rl, rn) => rl.w > rn.w * 1.1),
  ];

  /* Bị PHỦ bởi lớp khác (panel overlay ở viewport hẹp che mất canvas/điều
     khiển). elementFromPoint tại tâm phần tử trả về thứ KHÁC ⇒ bị che. */
  const covered = [...root.querySelectorAll('svg, [data-panel], button')].filter(vis)
    .filter((el) => {
      const r = el.getBoundingClientRect();
      const cx = Math.round(r.x + r.w / 2), cy = Math.round(r.y + r.h / 2);
      if (!Number.isFinite(cx) || !Number.isFinite(cy)) return false;
      if (cx < 0 || cy < 0 || cx > vw || cy > vh) return false;
      const top = document.elementFromPoint(cx, cy);
      return top && top !== el && !el.contains(top) && !top.contains(el);
    })
    .map((el) => (el.textContent || el.tagName).trim().slice(0, 30));

  /* F. THUẬT NGỮ — không để lộ id kỹ thuật / từ vựng generic cho học sinh */
  const text = (root.innerText || '');
  const BANNED = ['GENERIC','JSON','schema','rule_scene','simulation_id','dsl_version',
                  'undefined','NaN','[object Object]','specVersion','capability_gap',
                  // W2B-VR: id cột kỹ thuật snake_case KHÔNG được lộ cho học sinh
                  // (phải dùng nhãn "Điểm kiểm tra" thay id "diem_kt").
                  'diem_kt','aggregateResult','table-1.0','table_schema','goal_id',
                  'query_group','filter_op','table.aggregate',
                  'ho_ten','diem_tb','chenh_lech','ghi_chu','noi_tru','so_buoi_vang'];
  const banned = BANNED.filter((w) => text.includes(w));

  return {
    viewport: { w: vw, h: vh },
    css_svg: { edge_elements: edgeEls.length, invisible_strokes: strokeIssues.length,
               invisible_stroke_samples: strokeIssues.slice(0, 4), unresolved_var: unresolvedVar },
    geometry: { nan_or_infinity: nanGeom, zero_size_elements: zeroSize,
                body_overflow_x: bodyOverflowX, page_overflow_x: pageOverflowX,
                client_width: vw, scroll_width: de.scrollWidth,
                controls_off_viewport: offViewport, covered_by_overlay: covered,
                clipped_content: clippedContent, rigid_min_width: rigidMinWidth,
                key_elements: keyElements },
    overlap: { threshold_ratio: OVERLAP_RATIO, count: overlaps.length, items: overlaps.slice(0, 6) },
    terminology: { banned_found: banned },
    text_length: text.length,
  };
})()`;

/* ══════════════ CHẠY ══════════════ */
const selected = ONLY ? FIXTURES.filter((f) => f.renderer === ONLY) : FIXTURES;
const selectedRefusals = ONLY ? REFUSALS.filter((f) => f.renderer === ONLY) : REFUSALS;

/* VIEWPORT LÀ VÒNG NGOÀI, và NẠP LẠI TRANG sau khi đổi kích thước.
   Bản đầu đổi viewport SAU khi trang đã dựng ở 1440 → ảnh ra khung 768 nhưng
   bố cục vẫn của 1440, trông như bị cắt. Đó là ARTEFACT CỦA PHÉP ĐO: chẩn đoán
   DOM (§E1 §2, diagnose-responsive.mjs) đo được 0 phần tử bị cắt ở mọi route.
   Đặt kích thước TRƯỚC rồi mới nạp thì bố cục phản ánh đúng viewport. */
const byFixture = new Map();   // fixture_id → captures[] (gộp qua các viewport)

for (const vp of VIEWPORTS) {
  await setViewport(vp);
  await send("Page.navigate", { url: APP });
  await sleep(2400);

  for (const fx of selected) {
    await loadEnvelope(fx.envelope);
    await sleep(650);
    const total = (await stepCount()) || 1;
    const marks = total > 1
      ? [["initial", 0], ["mid", Math.max(1, Math.floor(total / 2))], ["final", total - 1]]
      : [["initial", 0]];
    if (!byFixture.has(fx.id)) byFixture.set(fx.id, { fx, total, captures: [] });
    const slot = byFixture.get(fx.id);

    for (const [tag, n] of marks) {
      await goToStep(n);
      await sleep(400);
      const state = JSON.parse(await engineState());
      const audit = await evaluate(AUDIT_JS);
      const path = await shot(fx.renderer, `${fx.id}-${tag}-${vp.id}`);
      slot.captures.push({ tag, step: n, viewport: vp.id, screenshot: path,
                           authoritative_state: state, assertions: audit });
      const flags = [
        audit.css_svg.invisible_strokes && `stroke vô hình ${audit.css_svg.invisible_strokes}`,
        audit.geometry.nan_or_infinity && `NaN ${audit.geometry.nan_or_infinity}`,
        audit.geometry.page_overflow_x && "tràn ngang trang",
        audit.geometry.clipped_content.length && `nội dung bị cắt ${audit.geometry.clipped_content.length}`,
        audit.overlap.count && `chồng lấn ${audit.overlap.count}`,
        audit.terminology.banned_found.length && `thuật ngữ ${audit.terminology.banned_found}`,
      ].filter(Boolean);
      console.log(`  ${fx.id} ${tag}/${vp.id} (b${n}/${total - 1})` +
                  (flags.length ? `  ⚠ ${flags.join(" · ")}` : "  ok"));
    }
  }

  for (const rf of selectedRefusals) {
    await loadUnsupported(rf.reason, rf.failure_category ?? "insufficient_specification");
    await sleep(600);
    if (!byFixture.has(rf.id)) byFixture.set(rf.id, { fx: rf, total: 0, captures: [] });
    const slot = byFixture.get(rf.id);
    const audit = await evaluate(AUDIT_JS);
    const path = await shot(rf.renderer, `${rf.id}-refusal-${vp.id}`);
    slot.captures.push({ tag: "refusal", step: null, viewport: vp.id, screenshot: path,
                         authoritative_state: { reason: rf.reason }, assertions: audit });
    const flags = [
      audit.geometry.page_overflow_x && "tràn ngang trang",
      audit.geometry.clipped_content.length && `nội dung bị cắt ${audit.geometry.clipped_content.length}`,
      audit.terminology.banned_found.length && `thuật ngữ ${audit.terminology.banned_found}`,
    ].filter(Boolean);
    console.log(`  ${rf.id} refusal/${vp.id}` + (flags.length ? `  ⚠ ${flags.join(" · ")}` : "  ok"));
  }
}

const records = [...byFixture.values()].map(({ fx, total, captures }) => ({
  fixture_id: fx.id, renderer_id: fx.renderer, target_id: fx.target ?? null,
  fixture_kind: fx.kind ?? "refusal", title: fx.title ?? "Thông điệp từ chối",
  total_steps: total, captures,
}));

const shots = records.reduce((n, r) => n + r.captures.length, 0);
writeFileSync(join(OUT_DIR, "captures.json"),
  JSON.stringify({ app: APP, generated_at: new Date().toISOString(),
                   viewports: VIEWPORTS, only: ONLY, records }, null, 2) + "\n", "utf-8");
console.log(`\nĐã chụp ${shots} ảnh / ${records.length} fixture → ${OUT_DIR}`);

ws.close();
chrome.kill();
