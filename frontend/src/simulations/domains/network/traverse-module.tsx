import { registerSimulation } from "../../registry";
import { TraversalFrontier, frontierDelta } from "../../../components/TraversalFrontier";
import type { ConfigResult, SimulationModule, WorkspaceProps } from "../../types";

/**
 * network.graph_traversal (M17 W1) — duyệt đồ thị TỔNG QUÁT: BFS (hàng đợi)
 * hoặc DFS (ngăn xếp), có/không hướng, tùy chọn đích (tìm đường không trọng
 * số + dựng lại đường đi; KHÔNG ĐẾN ĐƯỢC là một KẾT QUẢ hợp lệ, không phải
 * lỗi). packet_routing giữ nguyên là application variant của BFS.
 *
 * Executor tất định sở hữu: frontier (queue/stack), thứ tự thăm, predecessor
 * map, đường đi dựng lại, kết quả reachable. Tất định hóa: hàng xóm duyệt
 * THEO THỨ TỰ KHAI BÁO cạnh. State renderer-neutral (chỉ id nút — layout
 * thuộc renderer, bất biến M7.FREEZE). Weighted shortest path NGOÀI phạm vi
 * (capability_gap — future family).
 */

export const TRAVERSE_VARIANTS = ["bfs", "dfs"] as const;
export type TraverseVariant = (typeof TRAVERSE_VARIANTS)[number];
export const TRAVERSE_MAX_NODES = 10;
export const TRAVERSE_MAX_EDGES = 20;

export interface TraverseNode {
  id: string;
  label: string | null;
}

export interface TraverseConfig {
  nodes: TraverseNode[];
  edges: [string, string][];
  directed: boolean;
  start: string;
  /** Đích tùy chọn — null = duyệt toàn bộ phần liên thông. */
  goal: string | null;
  variant: TraverseVariant;
  notes: string | null;
}

export type TraverseStep =
  | { kind: "intro"; frontierAfter: string[]; visitedSoFar: string[]; narration: string }
  | {
      kind: "visit";
      current: string;
      /** Frontier SAU khi thăm current và nạp hàng xóm mới. */
      frontierAfter: string[];
      visitedSoFar: string[];
      narration: string;
    }
  | { kind: "result"; frontierAfter: string[]; visitedSoFar: string[]; narration: string };

export interface TraverseState {
  readonly config: TraverseConfig;
  /** "queue" (BFS) | "stack" (DFS) — dẫn xuất từ variant, phục vụ panel. */
  frontierKind: "queue" | "stack";
  steps: TraverseStep[];
  /** Thứ tự thăm cuối cùng — engine tính (authoritative). */
  visitedOrder: string[];
  /** Đường đi start→goal (khi có goal và đến được) — engine dựng lại. */
  path: string[] | null;
  /** null khi không có goal; true/false khi có goal. */
  reachable: boolean | null;
  cursor: number;
}

/** Danh sách kề THEO THỨ TỰ KHAI BÁO cạnh (tất định). */
function adjacency(config: TraverseConfig): Map<string, string[]> {
  const adj = new Map<string, string[]>(config.nodes.map((n) => [n.id, []]));
  for (const [a, b] of config.edges) {
    adj.get(a)!.push(b);
    if (!config.directed) adj.get(b)!.push(a);
  }
  return adj;
}

export function buildTraversal(config: TraverseConfig): {
  steps: TraverseStep[];
  visitedOrder: string[];
  path: string[] | null;
  reachable: boolean | null;
} {
  const adj = adjacency(config);
  const steps: TraverseStep[] = [];
  const visited: string[] = [];
  const visitedSet = new Set<string>();
  const pred = new Map<string, string>();
  const isBfs = config.variant === "bfs";
  const frontierName = isBfs ? "hàng đợi" : "ngăn xếp";

  // frontier mang cặp {node, parent}. Chính sách đánh dấu KHÁC nhau theo biến
  // thể để CẢ HAI trung thực với định nghĩa giáo khoa:
  // - BFS: đánh dấu khi NẠP (mark-on-enqueue) → không trùng trong hàng đợi +
  //   đường đi ngắn nhất đúng;
  // - DFS: đánh dấu khi THĂM (mark-on-pop) → khớp DFS ĐỆ QUY (đi sâu nhánh
  //   khai báo trước tới tận cùng), predecessor theo đúng cây DFS.
  type Entry = { node: string; parent: string | null };
  const frontier: Entry[] = [{ node: config.start, parent: null }];
  const bfsEnqueued = new Set<string>([config.start]);
  const displayFrontier = (): string[] => frontier.map((e) => e.node);

  steps.push({
    kind: "intro",
    frontierAfter: displayFrontier(),
    visitedSoFar: [],
    narration:
      `Duyệt ${isBfs ? "theo chiều rộng (BFS)" : "theo chiều sâu (DFS)"} từ ${config.start}` +
      (config.goal ? `, tìm đường tới ${config.goal}` : "") +
      `. Đưa ${config.start} vào ${frontierName}.`,
  });

  let found = false;
  while (frontier.length > 0 && !found) {
    const entry = isBfs ? frontier.shift()! : frontier.pop()!;
    const current = entry.node;
    // DFS: một nút có thể nằm nhiều lần trong ngăn xếp — lần pop sau khi đã
    // thăm thì bỏ qua lặng lẽ (không ghi bước).
    if (visitedSet.has(current)) continue;
    visitedSet.add(current);
    visited.push(current);
    if (entry.parent !== null && !pred.has(current)) pred.set(current, entry.parent);

    const added: string[] = [];
    if (current === config.goal) {
      found = true;
    } else {
      const neighbors = adj.get(current)!;
      // DFS: đẩy NGƯỢC thứ tự khai báo để nút khai báo trước được pop trước.
      const order = isBfs ? neighbors : [...neighbors].reverse();
      for (const nb of order) {
        if (isBfs) {
          if (!bfsEnqueued.has(nb)) {
            bfsEnqueued.add(nb);
            pred.set(nb, current);
            frontier.push({ node: nb, parent: current });
            added.push(nb);
          }
        } else if (!visitedSet.has(nb)) {
          frontier.push({ node: nb, parent: current });
          added.push(nb);
        }
      }
    }
    steps.push({
      kind: "visit",
      current,
      frontierAfter: displayFrontier(),
      visitedSoFar: [...visited],
      narration:
        `Lấy ${current} ra khỏi ${frontierName} và THĂM nó` +
        (found
          ? ` — đây chính là đích ${config.goal}!`
          : added.length > 0
            ? `; nạp hàng xóm chưa thấy: ${added.join(", ")}.`
            : `; không còn hàng xóm mới.`),
    });
  }

  let path: string[] | null = null;
  let reachable: boolean | null = null;
  if (config.goal !== null) {
    reachable = found;
    if (found) {
      path = [config.goal];
      while (path[0] !== config.start) path.unshift(pred.get(path[0])!);
    }
  }

  steps.push({
    kind: "result",
    frontierAfter: [],
    visitedSoFar: [...visited],
    narration:
      config.goal === null
        ? `Duyệt xong. Thứ tự thăm: ${visited.join(" → ")}.`
        : found
          ? `Tìm thấy đích. Đường đi: ${path!.join(" → ")} (${path!.length - 1} cạnh).`
          : `KHÔNG đến được ${config.goal} từ ${config.start} — hai nút không liên thông (đây là một kết quả hợp lệ).`,
  });
  return { steps, visitedOrder: visited, path, reachable };
}

/* ── validator (tầng FE) ─────────────────────────────────────── */

export function validateTraverseConfig(raw: unknown): ConfigResult<TraverseConfig> {
  if (typeof raw !== "object" || raw === null) {
    return { ok: false, error: "Config không phải đối tượng JSON." };
  }
  const r = raw as Record<string, unknown>;
  if (!Array.isArray(r.nodes) || r.nodes.length < 2 || r.nodes.length > TRAVERSE_MAX_NODES) {
    return { ok: false, error: `"nodes" phải có 2–${TRAVERSE_MAX_NODES} nút.` };
  }
  const nodes: TraverseNode[] = [];
  const ids = new Set<string>();
  for (const it of r.nodes) {
    const o = it as Record<string, unknown>;
    if (typeof o.id !== "string" || !o.id) return { ok: false, error: "Nút thiếu id." };
    if (ids.has(o.id)) return { ok: false, error: `Id nút trùng: ${o.id}.` };
    ids.add(o.id);
    nodes.push({ id: o.id, label: typeof o.label === "string" ? o.label : null });
  }
  if (!Array.isArray(r.edges) || r.edges.length > TRAVERSE_MAX_EDGES) {
    return { ok: false, error: `"edges" phải là mảng tối đa ${TRAVERSE_MAX_EDGES} cạnh.` };
  }
  const edges: [string, string][] = [];
  for (const e of r.edges) {
    if (!Array.isArray(e) || e.length !== 2 || typeof e[0] !== "string" || typeof e[1] !== "string") {
      return { ok: false, error: "Mỗi cạnh phải là cặp [idA, idB]." };
    }
    if (!ids.has(e[0]) || !ids.has(e[1])) {
      return { ok: false, error: `Cạnh [${e[0]}, ${e[1]}] tham chiếu nút không tồn tại.` };
    }
    if (e[0] === e[1]) return { ok: false, error: "Không nhận cạnh tự nối (self-loop)." };
    edges.push([e[0], e[1]]);
  }
  if (typeof r.start !== "string" || !ids.has(r.start)) {
    return { ok: false, error: '"start" phải là id một nút có thật.' };
  }
  let goal: string | null = null;
  if (r.goal !== undefined && r.goal !== null) {
    if (typeof r.goal !== "string" || !ids.has(r.goal)) {
      return { ok: false, error: '"goal" (nếu có) phải là id một nút có thật.' };
    }
    if (r.goal === r.start) return { ok: false, error: '"goal" phải khác "start".' };
    goal = r.goal;
  }
  if (!TRAVERSE_VARIANTS.includes(r.variant as TraverseVariant)) {
    return { ok: false, error: '"variant" phải là "bfs" hoặc "dfs".' };
  }
  return {
    ok: true,
    config: {
      nodes,
      edges,
      directed: r.directed === true,
      start: r.start,
      goal,
      variant: r.variant as TraverseVariant,
      notes: typeof r.notes === "string" ? r.notes : null,
    },
  };
}

/* ── UI — layout thuộc renderer (vòng tròn), state chỉ id nút ── */

function clampCursor(state: TraverseState, step: number): number {
  return Math.max(0, Math.min(step, state.steps.length - 1));
}

type Props = WorkspaceProps<TraverseConfig, TraverseState>;

const W = 420;
const H = 260;
const NODE_R = 16;

// M17-RC1 §E — nhãn DÀI hơn ngần này không vẽ lọt trong hình tròn r=16: chữ
// tràn ra hai bên và bị chính nút cắt ngang (audit trình duyệt thật đo được 5
// chồng lấn node-label ở fixture nhãn tiếng Việt). Nhãn dài vẽ BÊN DƯỚI nút,
// giữ id trong nút để không mất danh tính — cùng quy ước với renderer cây.
const INLINE_LABEL_MAX = 3;
// Chừa chỗ cho nhãn dưới nút: bán kính vòng bố cục co lại, và canvas cao thêm.
const LABEL_DY = NODE_R + 14;

function hasLongLabel(nodes: TraverseNode[]): boolean {
  return nodes.some((n) => (n.label ?? n.id).length > INLINE_LABEL_MAX);
}

function circleLayout(nodes: TraverseNode[], long = false): Map<string, { x: number; y: number }> {
  const cx = W / 2;
  const cy = H / 2;
  const r = Math.min(W, H) / 2 - (long ? 48 : 34);
  return new Map(
    nodes.map((n, i) => {
      const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
      return [n.id, { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) }];
    }),
  );
}

/** Nhãn hiển thị của một node — đọc từ config, không suy từ narration. */
function labelOfNode(config: TraverseConfig, id: string): string {
  return config.nodes.find((n) => n.id === id)?.label ?? id;
}

export function TraverseWorkspace({ state }: Props) {
  const at = clampCursor(state, state.cursor);
  const step = state.steps[at];
  const long = hasLongLabel(state.config.nodes);
  const pos = circleLayout(state.config.nodes, long);
  const visited = new Set(step.visitedSoFar);
  const current = step.kind === "visit" ? step.current : null;
  const last = at === state.steps.length - 1;
  const pathEdges = new Set<string>();
  if (last && state.path) {
    for (let i = 0; i < state.path.length - 1; i++) {
      pathEdges.add(`${state.path[i]}→${state.path[i + 1]}`);
    }
  }

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div className="sim-stage">
        <svg viewBox={`0 0 ${W} ${long ? H + 28 : H}`}
             style={{ width: "100%", maxWidth: long ? W + 120 : W }} role="img"
             aria-label="Đồ thị duyệt">
          {state.config.edges.map(([a, b], i) => {
            const pa = pos.get(a)!;
            const pb = pos.get(b)!;
            const onPath = pathEdges.has(`${a}→${b}`) || (!state.config.directed && pathEdges.has(`${b}→${a}`));
            return (
              <line
                key={i}
                x1={pa.x} y1={pa.y} x2={pb.x} y2={pb.y}
                stroke={onPath ? "var(--accent-green)" : "var(--ink-faint)"}
                strokeWidth={onPath ? 3 : 1.5}
              />
            );
          })}
          {state.config.nodes.map((n) => {
            const p = pos.get(n.id)!;
            const isCur = n.id === current;
            const isVisited = visited.has(n.id);
            const inFrontier = step.frontierAfter.includes(n.id);
            return (
              <g key={n.id}>
                <circle
                  cx={p.x} cy={p.y} r={NODE_R}
                  fill={isCur ? "var(--accent-orange)" : isVisited ? "var(--accent-green)" : inFrontier ? "var(--primary)" : "var(--surface)"}
                  stroke="var(--ink-faint)"
                />
                {/* Nhãn ngắn nằm TRONG nút; nhãn dài xuống DƯỚI nút để chữ
                    không bị chính nút cắt ngang (M17-RC1 §E). */}
                <text x={p.x} y={p.y + 4} textAnchor="middle" fontSize={11}>
                  {long ? n.id : (n.label ?? n.id)}
                </text>
                {long && (n.label ?? n.id) !== n.id && (
                  <text x={p.x} y={p.y + LABEL_DY} textAnchor="middle" fontSize={10}
                        fill="var(--ink-muted)">
                    {n.label}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* FRONTIER-VIS: hàng đợi/ngăn xếp là ĐỐI TƯỢNG CƠ CHẾ, nằm ngay trên
            sân khấu cạnh đồ thị — không đẩy xuống panel Quan sát, vì nó chính là
            thứ quyết định thứ tự duyệt. Dòng chữ "Hàng đợi: C, D" cũ đã bỏ: nó
            lặp lại đúng thông tin này mà không cho thấy đầu/cuối. */}
        <TraversalFrontier
          mode={state.frontierKind}
          items={step.frontierAfter.map((id) => ({ id, label: labelOfNode(state.config, id) }))}
          delta={frontierDelta(at > 0 ? state.steps[at - 1].frontierAfter : null, step.frontierAfter)}
          activeId={current}
          label={state.frontierKind === "queue" ? "Hàng đợi (FIFO)" : "Ngăn xếp (LIFO)"}
        />

        <p className="frontier-visited">
          <span className="frontier-tag is-done">đã thăm</span>
          {step.visitedSoFar.length > 0 ? step.visitedSoFar.join(" → ") : "(chưa có)"}
        </p>

        <p className="stage-legend">
          <span><i className="dot is-current" /> đang xử lý</span>
          <span><i className="dot is-done" /> đã thăm</span>
          <span><i className="dot is-frontier" /> đang chờ trong {state.frontierKind === "queue" ? "hàng đợi" : "ngăn xếp"}</span>
          <span><i className="dot is-idle" /> chưa xét</span>
        </p>
      </div>
      <p className="notes">{step.narration}</p>
    </div>
  );
}

export function TraverseInspector({ state }: Props) {
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <p className="notes">
        Biến thể: {state.config.variant.toUpperCase()} (
        {state.frontierKind === "queue" ? "hàng đợi FIFO" : "ngăn xếp LIFO"})
        {state.config.directed ? " · đồ thị CÓ hướng" : " · đồ thị vô hướng"}
      </p>
      <p className="notes">Thứ tự thăm (engine): {state.visitedOrder.join(" → ")}</p>
      {state.reachable !== null && (
        <p className="notes">
          {state.reachable
            ? `Đường đi: ${state.path!.join(" → ")}`
            : "Không đến được đích — kết quả hợp lệ (không liên thông)."}
        </p>
      )}
    </div>
  );
}

/* ── module ─────────────────────────────────────────────────── */

export function makeTraverseModule(): SimulationModule<TraverseConfig, TraverseState> {
  return {
    id: "network.graph_traversal",
    domain: "network",
    title: "Duyệt đồ thị (BFS · DFS)",
    interactionMode: "progressive",
    supportedVisualModes: ["2d"],

    validateConfig: validateTraverseConfig,

    init: (config) => {
      const { steps, visitedOrder, path, reachable } = buildTraversal(config);
      return {
        config,
        frontierKind: config.variant === "bfs" ? "queue" : "stack",
        steps,
        visitedOrder,
        path,
        reachable,
        cursor: 0,
      };
    },

    apply: (state) => state, // v1 không what-if (có chủ đích — M9-S3 là việc khác)

    timeline: {
      stepCount: (s) => s.steps.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: clampCursor(s, step) }),
    },

    getExplainContext: (state) => {
      const at = clampCursor(state, state.cursor);
      const step = state.steps[at];
      return {
        simulation_id: "network.graph_traversal",
        variant: state.config.variant,
        directed: state.config.directed,
        start: state.config.start,
        goal: state.config.goal,
        visited_order: state.visitedOrder,
        path: state.path,
        reachable: state.reachable,
        frontier: step.frontierAfter,
        visited_so_far: step.visitedSoFar,
        current_step: at + 1,
        total_steps: state.steps.length,
        narration: step.narration,
      };
    },

    Workspace: TraverseWorkspace,
    Inspector: TraverseInspector,
  };
}

export function registerTraverseModule(): void {
  registerSimulation(makeTraverseModule());
}
