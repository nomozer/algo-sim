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
 * canonical · boundary · stress cho MỖI renderer riêng biệt.
 * Config lấy đúng shape đã qua validator backend (không đoán).
 */
const env = (simulation_id, domain, title, config, extra = {}) => ({
  status: "ok", simulation_id, domain, visual_mode: "2d",
  title, description: null, notes: null, config, ...extra,
});
const N = (id, left = null, right = null, label = id) => ({ id, label, left, right });
const tree = (variant, rootId, nodes) =>
  ({ specVersion: "tree-1.0", variant, rootId, nodes, notes: null });
const gnode = (id, label = null) => ({ id, label });

/** Nhãn tiếng Việt DÀI + dấu — stress thật, không phải A–G. */
const VN = {
  a: "Trạm Hải Đăng", b: "Trạm Sương Mai", c: "Trạm Thông Xanh",
  d: "Trạm Suối Đá Vọng", e: "Trạm Mây Trắng Đỉnh Trời",
};

const FIXTURES = [
  /* ── A. network — RỦI RO CAO NHẤT (từng phantom token → cạnh vô hình) ── */
  {
    id: "graph-bfs-branching", renderer: "network", target: "network.graph_traversal",
    kind: "canonical", title: "BFS — đồ thị phân nhánh",
    envelope: env("network.graph_traversal", "network", "BFS — đồ thị phân nhánh", {
      nodes: ["A", "B", "C", "D", "E", "F"].map((i) => gnode(i)),
      edges: [["A", "B"], ["A", "C"], ["B", "D"], ["B", "E"], ["C", "F"]],
      directed: false, start: "A", goal: null, variant: "bfs", notes: null,
    }),
  },
  {
    id: "graph-dfs-same-topology", renderer: "network", target: "network.graph_traversal",
    kind: "canonical", title: "DFS — CÙNG topology để so sánh",
    envelope: env("network.graph_traversal", "network", "DFS — cùng topology", {
      nodes: ["A", "B", "C", "D", "E", "F"].map((i) => gnode(i)),
      edges: [["A", "B"], ["A", "C"], ["B", "D"], ["B", "E"], ["C", "F"]],
      directed: false, start: "A", goal: null, variant: "dfs", notes: null,
    }),
  },
  {
    id: "graph-cycle", renderer: "network", target: "network.graph_traversal",
    kind: "boundary", title: "Đồ thị có chu trình",
    envelope: env("network.graph_traversal", "network", "Đồ thị có chu trình", {
      nodes: ["A", "B", "C", "D"].map((i) => gnode(i)),
      edges: [["A", "B"], ["B", "C"], ["C", "D"], ["D", "A"], ["A", "C"]],
      directed: false, start: "A", goal: null, variant: "bfs", notes: null,
    }),
  },
  {
    id: "graph-unreachable", renderer: "network", target: "network.graph_traversal",
    kind: "boundary", title: "Đích KHÔNG thể tới (hai phần rời)",
    envelope: env("network.graph_traversal", "network", "Đích không thể tới", {
      nodes: ["A", "B", "X", "Y"].map((i) => gnode(i)),
      edges: [["A", "B"], ["X", "Y"]],
      directed: false, start: "A", goal: "Y", variant: "bfs", notes: null,
    }),
  },
  {
    id: "graph-vietnamese-long-labels", renderer: "network", target: "network.graph_traversal",
    kind: "stress", title: "Nhãn tiếng Việt dài",
    envelope: env("network.graph_traversal", "network", "Mạng trạm quan trắc", {
      nodes: [gnode("A", VN.a), gnode("B", VN.b), gnode("C", VN.c),
              gnode("D", VN.d), gnode("E", VN.e)],
      edges: [["A", "B"], ["A", "C"], ["B", "D"], ["C", "E"]],
      directed: false, start: "A", goal: null, variant: "bfs", notes: null,
    }),
  },
  {
    id: "graph-directed-dense", renderer: "network", target: "network.graph_traversal",
    kind: "stress", title: "Có hướng, nhiều cạnh",
    envelope: env("network.graph_traversal", "network", "Đồ thị có hướng dày", {
      nodes: ["A", "B", "C", "D", "E", "F", "G"].map((i) => gnode(i)),
      edges: [["A", "B"], ["A", "C"], ["A", "D"], ["B", "E"], ["C", "E"],
              ["D", "F"], ["E", "G"], ["F", "G"], ["B", "F"]],
      directed: true, start: "A", goal: null, variant: "dfs", notes: null,
    }),
  },
  {
    id: "routing-canonical", renderer: "network", target: "network.packet_routing",
    kind: "canonical", title: "Định tuyến gói tin",
    envelope: env("network.packet_routing", "network", "Đường đi gói tin", {
      nodes: [{ id: "pc", type: "client" }, { id: "sw", type: "switch" },
              { id: "r1", type: "router" }, { id: "isp", type: "isp" },
              { id: "srv", type: "server" }],
      links: [["pc", "sw"], ["sw", "r1"], ["r1", "isp"], ["isp", "srv"]],
      source: "pc", destination: "srv", notes: null,
    }),
  },
  {
    id: "encap-canonical", renderer: "network", target: "network.protocol_encapsulation",
    kind: "canonical", title: "Đóng gói dữ liệu qua các tầng",
    envelope: env("network.protocol_encapsulation", "network", "Đóng gói PDU", {
      payloadLabel: "Dữ liệu ứng dụng", appProtocol: null, notes: null,
    }),
  },

  /* ── B. tree — regression sau bản sửa nhãn dài ── */
  {
    id: "tree-balanced-short", renderer: "tree", target: "tree.traversal",
    kind: "canonical", title: "Cây cân bằng, nhãn ngắn",
    envelope: env("tree.traversal", "tree", "Duyệt trước — cây cân bằng",
      tree("preorder", "A", [N("A", "B", "C"), N("B", "D", "E"), N("C", "F", "G"),
                             N("D"), N("E"), N("F"), N("G")])),
  },
  {
    id: "tree-single-node", renderer: "tree", target: "tree.traversal",
    kind: "boundary", title: "Cây một nút",
    envelope: env("tree.traversal", "tree", "Cây một nút", tree("preorder", "X", [N("X")])),
  },
  {
    id: "tree-skewed-deep", renderer: "tree", target: "tree.traversal",
    kind: "boundary", title: "Cây lệch sâu",
    envelope: env("tree.traversal", "tree", "Cây lệch trái sâu",
      tree("postorder", "A", [N("A", "B"), N("B", "C"), N("C", "D"), N("D", "E"), N("E")])),
  },
  {
    id: "tree-vietnamese-11-nodes", renderer: "tree", target: "tree.traversal",
    kind: "stress", title: "11 nút, nhãn tiếng Việt dài",
    envelope: env("tree.traversal", "tree", "Mạng lưới trạm — nhãn dài",
      tree("preorder", "hai-dang", [
        { id: "hai-dang", label: "Hải Đăng", left: "suong-mai", right: "hoang-hon" },
        { id: "suong-mai", label: "Sương Mai", left: "thong-xanh", right: "suoi-da" },
        { id: "thong-xanh", label: "Thông Xanh", left: null, right: null },
        { id: "suoi-da", label: "Suối Đá", left: "may-trang", right: null },
        { id: "may-trang", label: "Mây Trắng", left: null, right: "da-vong" },
        { id: "da-vong", label: "Đá Vọng", left: null, right: null },
        { id: "hoang-hon", label: "Hoàng Hôn", left: null, right: "doi-gio" },
        { id: "doi-gio", label: "Đồi Gió", left: "thac-bac", right: "rung-sau" },
        { id: "thac-bac", label: "Thác Bạc", left: null, right: null },
        { id: "rung-sau", label: "Rừng Sâu", left: "trang-khuyet", right: null },
        { id: "trang-khuyet", label: "Trăng Khuyết", left: null, right: null },
      ])),
  },
  {
    id: "tree-levelorder", renderer: "tree", target: "tree.traversal",
    kind: "canonical", title: "Duyệt theo mức (hàng đợi)",
    envelope: env("tree.traversal", "tree", "Duyệt theo mức",
      tree("level_order", "A", [N("A", "B", "C"), N("B", "D", "E"), N("C", "F"),
                                N("D"), N("E"), N("F")])),
  },

  /* ── C. generic — engine authenticity vẫn PARTIAL, KHÔNG được nâng ── */
  {
    id: "generic-reveal-scene", renderer: "generic", target: "generic.rule_scene",
    kind: "canonical", title: "Cảnh hiện dần (biểu diễn khai báo)",
    envelope: env("generic.rule_scene", "generic", "Dựng tam giác ABC từng bước", {
      dsl_version: "1.0", title: "Dựng tam giác ABC từng bước",
      objects: [
        { id: "A", type: "node", label: "A" }, { id: "B", type: "node", label: "B" },
        { id: "C", type: "node", label: "C" },
        { id: "AB", type: "edge", from: "A", to: "B" },
        { id: "AC", type: "edge", from: "A", to: "C" },
        { id: "BC", type: "edge", from: "B", to: "C" },
      ],
      rules: [], interactions: [],
      processes: [{ type: "reveal_sequence", steps: [
        { objects: ["A", "B", "AB"], narration: "Vẽ đoạn AB" },
        { objects: ["C"], narration: "Thêm điểm C" },
        { objects: ["AC", "BC"], narration: "Nối C với A và B" },
      ] }],
    }),
  },
  {
    id: "generic-vietnamese-labels", renderer: "generic", target: "generic.rule_scene",
    kind: "stress", title: "Nhãn tiếng Việt dài trong cảnh generic",
    envelope: env("generic.rule_scene", "generic", "Sơ đồ trạm quan trắc", {
      dsl_version: "1.0", title: "Sơ đồ trạm quan trắc",
      objects: [
        { id: "s1", type: "node", label: VN.a }, { id: "s2", type: "node", label: VN.b },
        { id: "s3", type: "node", label: VN.e },
        { id: "e1", type: "edge", from: "s1", to: "s2" },
        { id: "e2", type: "edge", from: "s2", to: "s3" },
      ],
      rules: [], interactions: [],
      processes: [{ type: "reveal_sequence", steps: [
        { objects: ["s1", "s2", "e1"], narration: "Nối trạm Hải Đăng với trạm Sương Mai" },
        { objects: ["s3", "e2"], narration: "Nối tiếp tới trạm Mây Trắng Đỉnh Trời" },
      ] }],
    }),
  },

  /* ── D. renderer còn lại theo registry ── */
  {
    id: "algorithm-find-max", renderer: "algorithm", target: "algorithm.find_max",
    kind: "canonical", title: "Tìm giá trị lớn nhất",
    envelope: env("algorithm.find_max", "algorithm", "Tìm giá trị lớn nhất", {
      problem: { summary: "Tìm giá trị lớn nhất", input: "Dãy số", output: "Kết quả" },
      algorithm_id: "find_max",
      data: { array: [12, 7, 25, 9, 18], labels: null, target: null, condition: null, order: null },
      data_generated: false, notes: null,
    }),
  },
  {
    id: "algorithm-negative-decimal", renderer: "algorithm", target: "algorithm.find_max",
    kind: "stress", title: "Số âm và thập phân",
    envelope: env("algorithm.find_max", "algorithm", "Nhiệt độ thấp nhất trong tuần", {
      problem: { summary: "Tìm nhiệt độ cao nhất", input: "Dãy nhiệt độ", output: "Kết quả" },
      algorithm_id: "find_max",
      data: { array: [-12.5, -3.25, -40, 7.75, -0.5], labels: null, target: null,
              condition: null, order: null },
      data_generated: false, notes: null,
    }),
  },
  {
    id: "algorithm-binary-search", renderer: "algorithm", target: "algorithm.binary_search",
    kind: "boundary", title: "Tìm kiếm nhị phân (thu hẹp khoảng)",
    envelope: env("algorithm.binary_search", "algorithm", "Tìm kiếm nhị phân", {
      problem: { summary: "Tìm kiếm nhị phân", input: "Dãy số", output: "Kết quả" },
      algorithm_id: "binary_search",
      data: { array: [3, 8, 15, 22, 30, 41, 55], labels: null, target: 30,
              condition: null, order: null },
      data_generated: false, notes: null,
    }),
  },
  {
    id: "algorithm-sort-labels", renderer: "algorithm", target: "algorithm.bubble_sort",
    kind: "stress", title: "Sắp xếp có nhãn tiếng Việt",
    envelope: env("algorithm.bubble_sort", "algorithm", "Sắp xếp điểm các bạn", {
      problem: { summary: "Sắp xếp tăng dần", input: "Dãy điểm", output: "Dãy đã sắp" },
      algorithm_id: "bubble_sort",
      data: { array: [9, 4, 7, 2, 6],
              labels: ["Nguyễn Vân", "Trần Bảo", "Lê Hoàng", "Phạm Chi", "Đỗ Quân"],
              target: null, condition: null, order: "asc" },
      data_generated: false, notes: null,
    }),
  },
  {
    id: "binary-decimal-to-binary", renderer: "binary", target: "binary.decimal_to_binary",
    kind: "canonical", title: "Đổi thập phân sang nhị phân",
    envelope: env("binary.decimal_to_binary", "binary", "Đổi 156 sang nhị phân", {
      decimalValue: 156, bitWidth: 8, notes: null,
    }),
  },
  {
    id: "binary-base-conversion-hex", renderer: "binary", target: "binary.base_conversion",
    kind: "stress", title: "Đổi cơ số tổng quát (giá trị lớn)",
    envelope: env("binary.base_conversion", "binary", "Đổi 2026 sang thập lục phân", {
      sourceBase: 10, targetBase: 16, inputValue: "2026",
      strategy: "quotient_remainder", notes: null,
    }),
  },
  {
    id: "logic-and-gate", renderer: "logic", target: "logic.and_gate",
    kind: "canonical", title: "Một cổng AND (khám phá)",
    envelope: env("logic.and_gate", "logic", "Cổng AND", { inputA: 1, inputB: 1, notes: null }),
  },
  {
    id: "logic-boolean-dag", renderer: "logic", target: "logic.boolean_dag",
    kind: "stress", title: "Mạch nhiều cổng + bảng chân trị",
    envelope: env("logic.boolean_dag", "logic", "Mạch (A AND B) OR NOT C", {
      inputs: [{ id: "A", label: null, value: 1 }, { id: "B", label: null, value: 0 },
               { id: "C", label: null, value: 1 }],
      gates: [{ id: "g1", op: "AND", inputs: ["A", "B"] },
              { id: "g2", op: "NOT", inputs: ["C"] },
              { id: "g3", op: "OR", inputs: ["g1", "g2"] }],
      output: "g3", notes: null,
    }),
  },
];

/* Thông điệp từ chối learner-facing (không phải envelope ok) */
const REFUSALS = [
  {
    id: "refusal-tree-insufficient", renderer: "tree",
    reason: "Đề yêu cầu duyệt cây nhưng chưa cho cấu trúc cây cụ thể (các nút có tên và quan hệ con trái/con phải giữa chúng). Hãy mô tả rõ cây (ví dụ: gốc A, A có con trái B và con phải C…) rồi thử lại — hệ không tự dựng cây thay bạn.",
  },
  {
    id: "refusal-sequence-insufficient", renderer: "algorithm",
    reason: "Đề chưa cho dãy số cụ thể để mô phỏng. Em hãy nêu rõ dãy (ví dụ: 12, 7, 25, 9) rồi thử lại — hệ không tự nghĩ ra số liệu thay em.",
  },
];

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

const loadUnsupported = (reason) => evaluate(`(async () => {
  const m = await import('/src/state/store.ts');
  m.useAppStore.getState().loadUnsupported({
    status: 'unsupported', reason: ${JSON.stringify(reason)},
    learner_reason: ${JSON.stringify(reason)},
    failure_category: 'insufficient_specification',
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
  const vw = window.innerWidth, vh = window.innerHeight;
  const bodyOverflowX = document.documentElement.scrollWidth > vw + 1;
  const offViewport = [...root.querySelectorAll('button, [role="button"], input, select')]
    .filter(vis).filter((el) => { const r = el.getBoundingClientRect();
      return r.right < 0 || r.left > vw || r.bottom < 0 || r.top > vh; })
    .map((el) => (el.textContent || el.tagName).trim().slice(0, 30));

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
                  'undefined','NaN','[object Object]','specVersion','capability_gap'];
  const banned = BANNED.filter((w) => text.includes(w));

  return {
    viewport: { w: vw, h: vh },
    css_svg: { edge_elements: edgeEls.length, invisible_strokes: strokeIssues.length,
               invisible_stroke_samples: strokeIssues.slice(0, 4), unresolved_var: unresolvedVar },
    geometry: { nan_or_infinity: nanGeom, zero_size_elements: zeroSize,
                body_overflow_x: bodyOverflowX, controls_off_viewport: offViewport,
                covered_by_overlay: covered },
    overlap: { threshold_ratio: OVERLAP_RATIO, count: overlaps.length, items: overlaps.slice(0, 6) },
    terminology: { banned_found: banned },
    text_length: text.length,
  };
})()`;

/* ══════════════ CHẠY ══════════════ */
await send("Page.navigate", { url: APP });
await sleep(2500);

const selected = ONLY ? FIXTURES.filter((f) => f.renderer === ONLY) : FIXTURES;
const selectedRefusals = ONLY ? REFUSALS.filter((f) => f.renderer === ONLY) : REFUSALS;
const records = [];

for (const fx of selected) {
  await loadEnvelope(fx.envelope);
  await sleep(650);
  const total = (await stepCount()) || 1;
  const marks = total > 1
    ? [["initial", 0], ["mid", Math.max(1, Math.floor(total / 2))], ["final", total - 1]]
    : [["initial", 0]];
  const captures = [];
  for (const vp of VIEWPORTS) {
    await setViewport(vp);
    await sleep(350);
    for (const [tag, n] of marks) {
      await goToStep(n);
      await sleep(400);
      const state = JSON.parse(await engineState());
      const audit = await evaluate(AUDIT_JS);
      const path = await shot(fx.renderer, `${fx.id}-${tag}-${vp.id}`);
      captures.push({ tag, step: n, viewport: vp.id, screenshot: path,
                      authoritative_state: state, assertions: audit });
      const flags = [
        audit.css_svg.invisible_strokes && `stroke vô hình ${audit.css_svg.invisible_strokes}`,
        audit.geometry.nan_or_infinity && `NaN ${audit.geometry.nan_or_infinity}`,
        audit.overlap.count && `chồng lấn ${audit.overlap.count}`,
        audit.geometry.covered_by_overlay.length && `bị che ${audit.geometry.covered_by_overlay.length}`,
        audit.terminology.banned_found.length && `thuật ngữ ${audit.terminology.banned_found}`,
      ].filter(Boolean);
      console.log(`  ${fx.id} ${tag}/${vp.id} (b${n}/${total - 1})` +
                  (flags.length ? `  ⚠ ${flags.join(" · ")}` : "  ok"));
    }
  }
  records.push({ fixture_id: fx.id, renderer_id: fx.renderer, target_id: fx.target,
                 fixture_kind: fx.kind, title: fx.title, total_steps: total, captures });
}

for (const rf of selectedRefusals) {
  await loadUnsupported(rf.reason);
  await sleep(600);
  const captures = [];
  for (const vp of VIEWPORTS) {
    await setViewport(vp);
    await sleep(300);
    const audit = await evaluate(AUDIT_JS);
    const path = await shot(rf.renderer, `${rf.id}-refusal-${vp.id}`);
    captures.push({ tag: "refusal", step: null, viewport: vp.id, screenshot: path,
                    authoritative_state: { reason: rf.reason }, assertions: audit });
    console.log(`  ${rf.id} refusal/${vp.id}` +
                (audit.terminology.banned_found.length ? `  ⚠ ${audit.terminology.banned_found}` : "  ok"));
  }
  records.push({ fixture_id: rf.id, renderer_id: rf.renderer, target_id: null,
                 fixture_kind: "refusal", title: "Thông điệp từ chối", total_steps: 0, captures });
}

const shots = records.reduce((n, r) => n + r.captures.length, 0);
writeFileSync(join(OUT_DIR, "captures.json"),
  JSON.stringify({ app: APP, generated_at: new Date().toISOString(),
                   viewports: VIEWPORTS, only: ONLY, records }, null, 2) + "\n", "utf-8");
console.log(`\nĐã chụp ${shots} ảnh / ${records.length} fixture → ${OUT_DIR}`);

ws.close();
chrome.kill();
