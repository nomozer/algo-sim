import { registerSimulation } from "../../registry";
import type { ConfigResult, SimulationModule, WorkspaceProps } from "../../types";

/**
 * tree_traversal (M17 W2A) — duyệt CÂY NHỊ PHÂN hữu hạn bằng 4 biến thể:
 * preorder / inorder / postorder (DFS, ngăn xếp) và level_order (BFS, hàng đợi).
 *
 * Deterministic executor sở hữu TOÀN BỘ: thứ tự thăm, stack/queue state,
 * timeline, kết quả, tính đúng. LLM chỉ khai variant + cấu trúc cây + labels
 * (KHÔNG sinh traversal order / correctness — R0). Renderer chuyên biệt: cây
 * phân tầng, quan hệ trái/phải, panel stack/queue đúng biến thể — KHÔNG dùng
 * điểm/đoạn nối/vật di chuyển generic.
 *
 * KHÔNG sở hữu (near-miss → gap): BST insert/search/delete, AVL/RB balancing,
 * heap, expression-tree eval, n-ary tree, general graph DFS/BFS (thuộc
 * network.graph_traversal), Dijkstra/weighted.
 */

export const TREE_VARIANTS = ["preorder", "inorder", "postorder", "level_order"] as const;
export type TreeVariant = (typeof TREE_VARIANTS)[number];
export const TREE_SPEC_VERSION = "tree-1.0";
export const TREE_MAX_NODES = 15;
export const TREE_MAX_DEPTH = 5;

export interface TreeNode {
  id: string;
  label: string;
  left: string | null;
  right: string | null;
}

export interface TreeTraversalConfig {
  specVersion: string;
  variant: TreeVariant;
  rootId: string;
  nodes: TreeNode[];
  notes: string | null;
}

export type TreeEventKind =
  | "started"
  | "push"
  | "pop"
  | "enqueue"
  | "dequeue"
  | "visit"
  | "completed";

export interface TreeStep {
  kind: TreeEventKind;
  /** Node đang là tâm điểm của bước (null cho started/completed thuần). */
  current: string | null;
  /** Frontier SAU bước: id node trong ngăn xếp (DFS) hoặc hàng đợi (level). */
  frontierAfter: string[];
  visitedSoFar: string[];
  /** Đường active từ gốc tới current (DFS = ngăn xếp; level = đường predecessor). */
  activePath: string[];
  narration: string;
}

export interface TreeTraversalState {
  readonly config: TreeTraversalConfig;
  frontierKind: "stack" | "queue";
  steps: TreeStep[];
  /** Thứ tự thăm cuối cùng — engine tính (authoritative). */
  visitedOrder: string[];
  cursor: number;
}

function nodeMap(config: TreeTraversalConfig): Map<string, TreeNode> {
  return new Map(config.nodes.map((n) => [n.id, n]));
}

function labelOf(map: Map<string, TreeNode>, id: string): string {
  return map.get(id)?.label ?? id;
}

/* ── executor: DFS pre/in/post bằng KHUNG NGĂN XẾP (mirror đệ quy) ──
 * Mỗi khung {node, stage}: stage 0 = trước khi vào con trái, 1 = giữa (sau
 * trái, trước phải), 2 = sau con phải. "Thăm" xảy ra ở stage tương ứng biến
 * thể. Ngăn xếp khung CHÍNH LÀ đường đệ quy gốc→hiện tại (hiển thị trung thực).
 */
function buildDfs(config: TreeTraversalConfig, variant: TreeVariant, map: Map<string, TreeNode>) {
  const steps: TreeStep[] = [];
  const visited: string[] = [];
  interface Frame {
    id: string;
    stage: 0 | 1 | 2;
  }
  const stack: Frame[] = [{ id: config.rootId, stage: 0 }];
  const pathIds = () => stack.map((f) => f.id);
  const orderText =
    variant === "preorder" ? "trước (gốc–trái–phải)"
    : variant === "inorder" ? "giữa (trái–gốc–phải)"
    : "sau (trái–phải–gốc)";

  steps.push({
    kind: "started",
    current: config.rootId,
    frontierAfter: pathIds(),
    visitedSoFar: [],
    activePath: pathIds(),
    narration: `Duyệt thứ tự ${orderText} từ gốc ${labelOf(map, config.rootId)}. Đưa gốc vào ngăn xếp.`,
  });

  const visitAt = (variant === "preorder" ? 0 : variant === "inorder" ? 1 : 2) as 0 | 1 | 2;

  while (stack.length > 0) {
    const frame = stack[stack.length - 1];
    const node = map.get(frame.id)!;
    if (frame.stage === visitAt) {
      visited.push(frame.id);
      steps.push({
        kind: "visit",
        current: frame.id,
        frontierAfter: pathIds(),
        visitedSoFar: [...visited],
        activePath: pathIds(),
        narration: `Thăm ${labelOf(map, frame.id)} (thứ ${visited.length}).`,
      });
    }
    if (frame.stage === 0) {
      frame.stage = 1;
      if (node.left) {
        stack.push({ id: node.left, stage: 0 });
        steps.push({
          kind: "push",
          current: node.left,
          frontierAfter: pathIds(),
          visitedSoFar: [...visited],
          activePath: pathIds(),
          narration: `Đi xuống con TRÁI của ${labelOf(map, frame.id)} → ${labelOf(map, node.left)} (đẩy vào ngăn xếp).`,
        });
      }
    } else if (frame.stage === 1) {
      frame.stage = 2;
      if (node.right) {
        stack.push({ id: node.right, stage: 0 });
        steps.push({
          kind: "push",
          current: node.right,
          frontierAfter: pathIds(),
          visitedSoFar: [...visited],
          activePath: pathIds(),
          narration: `Đi xuống con PHẢI của ${labelOf(map, frame.id)} → ${labelOf(map, node.right)} (đẩy vào ngăn xếp).`,
        });
      }
    } else {
      stack.pop();
      steps.push({
        kind: "pop",
        current: frame.id,
        frontierAfter: pathIds(),
        visitedSoFar: [...visited],
        activePath: pathIds(),
        narration: `Xong nhánh của ${labelOf(map, frame.id)} — lấy ra khỏi ngăn xếp.`,
      });
    }
  }
  return { steps, visited };
}

/* ── executor: level_order bằng HÀNG ĐỢI (BFS theo tầng) ── */
function buildLevelOrder(config: TreeTraversalConfig, map: Map<string, TreeNode>) {
  const steps: TreeStep[] = [];
  const visited: string[] = [];
  const parent = new Map<string, string>();
  const queue: string[] = [config.rootId];

  const pathTo = (id: string): string[] => {
    const path = [id];
    while (parent.has(path[0])) path.unshift(parent.get(path[0])!);
    return path;
  };

  steps.push({
    kind: "started",
    current: config.rootId,
    frontierAfter: [...queue],
    visitedSoFar: [],
    activePath: [config.rootId],
    narration: `Duyệt theo MỨC (BFS) từ gốc ${labelOf(map, config.rootId)}. Đưa gốc vào hàng đợi.`,
  });

  while (queue.length > 0) {
    const id = queue.shift()!;
    visited.push(id);
    steps.push({
      kind: "dequeue",
      current: id,
      frontierAfter: [...queue],
      visitedSoFar: [...visited],
      activePath: pathTo(id),
      narration: `Lấy ${labelOf(map, id)} ra khỏi hàng đợi và THĂM (thứ ${visited.length}).`,
    });
    const node = map.get(id)!;
    for (const child of [node.left, node.right]) {
      if (child) {
        parent.set(child, id);
        queue.push(child);
        steps.push({
          kind: "enqueue",
          current: child,
          frontierAfter: [...queue],
          visitedSoFar: [...visited],
          activePath: pathTo(child),
          narration: `Nạp con ${labelOf(map, child)} của ${labelOf(map, id)} vào hàng đợi.`,
        });
      }
    }
  }
  return { steps, visited };
}

export function buildTreeTraversal(config: TreeTraversalConfig): {
  frontierKind: "stack" | "queue";
  steps: TreeStep[];
  visitedOrder: string[];
} {
  const map = nodeMap(config);
  const isLevel = config.variant === "level_order";
  const { steps, visited } = isLevel
    ? buildLevelOrder(config, map)
    : buildDfs(config, config.variant, map);
  steps.push({
    kind: "completed",
    current: null,
    frontierAfter: [],
    visitedSoFar: [...visited],
    activePath: [],
    narration: `Duyệt xong. Thứ tự thăm: ${visited.map((id) => labelOf(map, id)).join(" → ")}.`,
  });
  return { frontierKind: isLevel ? "queue" : "stack", steps, visitedOrder: visited };
}

/* ── validator hai tầng (structural + semantic), fail-closed ── */

export function validateTreeTraversalConfig(raw: unknown): ConfigResult<TreeTraversalConfig> {
  if (typeof raw !== "object" || raw === null) {
    return { ok: false, error: "Config không phải đối tượng JSON." };
  }
  const r = raw as Record<string, unknown>;
  if (r.specVersion !== TREE_SPEC_VERSION) {
    return { ok: false, error: `"specVersion" phải là "${TREE_SPEC_VERSION}".` };
  }
  if (!TREE_VARIANTS.includes(r.variant as TreeVariant)) {
    return { ok: false, error: '"variant" phải là preorder/inorder/postorder/level_order.' };
  }
  if (!Array.isArray(r.nodes) || r.nodes.length < 1 || r.nodes.length > TREE_MAX_NODES) {
    return { ok: false, error: `"nodes" phải có 1–${TREE_MAX_NODES} node.` };
  }
  const nodes: TreeNode[] = [];
  const ids = new Set<string>();
  for (const it of r.nodes) {
    const o = it as Record<string, unknown>;
    if (typeof o.id !== "string" || !o.id) return { ok: false, error: "Node thiếu id." };
    if (ids.has(o.id)) return { ok: false, error: `Id node trùng: ${o.id}.` };
    ids.add(o.id);
    const label = typeof o.label === "string" && o.label ? o.label : o.id;
    if (label.length > 24) return { ok: false, error: `Nhãn node ${o.id} quá dài (renderer).` };
    const left = o.left == null ? null : o.left;
    const right = o.right == null ? null : o.right;
    if (left !== null && typeof left !== "string") return { ok: false, error: `left của ${o.id} phải là id hoặc rỗng.` };
    if (right !== null && typeof right !== "string") return { ok: false, error: `right của ${o.id} phải là id hoặc rỗng.` };
    nodes.push({ id: o.id, label, left: left as string | null, right: right as string | null });
  }
  if (typeof r.rootId !== "string" || !ids.has(r.rootId)) {
    return { ok: false, error: '"rootId" phải là id một node có thật.' };
  }
  // ── semantic ──
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const parentOf = new Map<string, string>();
  for (const n of nodes) {
    for (const child of [n.left, n.right]) {
      if (child === null) continue;
      if (!ids.has(child)) return { ok: false, error: `Node ${n.id} tham chiếu con không tồn tại: ${child}.` };
      if (child === n.id) return { ok: false, error: `Node ${n.id} tự trỏ tới chính nó.` };
      if (parentOf.has(child)) {
        return { ok: false, error: `Node ${child} có NHIỀU cha (${parentOf.get(child)}, ${n.id}) — không phải cây.` };
      }
      parentOf.set(child, n.id);
    }
  }
  // root không có cha
  if (parentOf.has(r.rootId)) {
    return { ok: false, error: `rootId ${r.rootId} lại là con của ${parentOf.get(r.rootId)} — không phải gốc.` };
  }
  // reachable + depth (không cycle vì đã chặn multi-parent + root-no-parent, BFS xác nhận)
  const seen = new Set<string>();
  let maxDepth = 0;
  const queue: [string, number][] = [[r.rootId, 1]];
  seen.add(r.rootId);
  while (queue.length) {
    const [id, depth] = queue.shift()!;
    maxDepth = Math.max(maxDepth, depth);
    if (depth > TREE_MAX_DEPTH) return { ok: false, error: `Cây sâu quá ${TREE_MAX_DEPTH} tầng.` };
    const n = byId.get(id)!;
    for (const child of [n.left, n.right]) {
      if (child !== null && !seen.has(child)) {
        seen.add(child);
        queue.push([child, depth + 1]);
      }
    }
  }
  if (seen.size !== nodes.length) {
    const orphan = nodes.filter((n) => !seen.has(n.id)).map((n) => n.id);
    return { ok: false, error: `Node không nối tới gốc (rời rạc): ${orphan.join(", ")}.` };
  }
  return {
    ok: true,
    config: {
      specVersion: TREE_SPEC_VERSION,
      variant: r.variant as TreeVariant,
      rootId: r.rootId,
      nodes,
      notes: typeof r.notes === "string" ? r.notes : null,
    },
  };
}

/* ── renderer: layout cây (in-order x, depth y) ── */

const RW = 460;
const RH = 300;

function treeLayout(config: TreeTraversalConfig): Map<string, { x: number; y: number; depth: number }> {
  const map = nodeMap(config);
  const pos = new Map<string, { x: number; y: number; depth: number }>();
  let inorderIndex = 0;
  const depths: number[] = [];
  const place = (id: string, depth: number) => {
    const n = map.get(id)!;
    if (n.left) place(n.left, depth + 1);
    const idx = inorderIndex++;
    pos.set(id, { x: idx, y: depth, depth });
    depths.push(depth);
    if (n.right) place(n.right, depth + 1);
  };
  place(config.rootId, 0);
  const n = inorderIndex;
  const maxDepth = Math.max(1, ...depths);
  for (const [id, p] of pos) {
    pos.set(id, {
      x: 30 + (p.x + 0.5) * ((RW - 60) / Math.max(1, n)),
      y: 30 + p.y * ((RH - 60) / maxDepth),
      depth: p.depth,
    });
  }
  return pos;
}

function clampCursor(state: TreeTraversalState, step: number): number {
  return Math.max(0, Math.min(step, state.steps.length - 1));
}

type Props = WorkspaceProps<TreeTraversalConfig, TreeTraversalState>;

export function TreeWorkspace({ state }: Props) {
  const at = clampCursor(state, state.cursor);
  const step = state.steps[at];
  const map = nodeMap(state.config);
  const pos = treeLayout(state.config);
  const visited = new Set(step.visitedSoFar);
  const activePath = new Set(step.activePath);
  const last = at === state.steps.length - 1;

  const edges: { from: string; to: string; side: "L" | "R" }[] = [];
  for (const n of state.config.nodes) {
    if (n.left) edges.push({ from: n.id, to: n.left, side: "L" });
    if (n.right) edges.push({ from: n.id, to: n.right, side: "R" });
  }

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div className="sim-stage">
        <svg viewBox={`0 0 ${RW} ${RH}`} style={{ width: "100%", maxWidth: RW }} role="img"
             aria-label="Cây nhị phân">
          {edges.map((e, i) => {
            const a = pos.get(e.from)!;
            const b = pos.get(e.to)!;
            const onPath = activePath.has(e.from) && activePath.has(e.to);
            return (
              <g key={i}>
                <line x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                      stroke={onPath ? "var(--accent-orange)" : "var(--ink-faint)"}
                      strokeWidth={onPath ? 3 : 1.5} />
                <text x={(a.x + b.x) / 2} y={(a.y + b.y) / 2 - 3} textAnchor="middle" fontSize={9}
                      fill="var(--ink-muted)">{e.side === "L" ? "trái" : "phải"}</text>
              </g>
            );
          })}
          {state.config.nodes.map((n) => {
            const p = pos.get(n.id)!;
            const isCur = n.id === step.current;
            const isVisited = visited.has(n.id);
            return (
              <g key={n.id}>
                <circle cx={p.x} cy={p.y} r={16}
                        fill={isCur ? "var(--accent-orange)" : isVisited ? "var(--accent-green)" : "var(--surface)"}
                        stroke={n.id === state.config.rootId ? "var(--primary)" : "var(--ink-faint)"}
                        strokeWidth={n.id === state.config.rootId ? 2.5 : 1.5} />
                <text x={p.x} y={p.y + 4} textAnchor="middle" fontSize={11}>{n.label}</text>
              </g>
            );
          })}
        </svg>
        <p className="notes">
          {state.frontierKind === "stack" ? "Ngăn xếp" : "Hàng đợi"}:{" "}
          {step.frontierAfter.length > 0 ? step.frontierAfter.map((id) => labelOf(map, id)).join(", ") : "(rỗng)"}
          {" · "}Đã thăm: {step.visitedSoFar.length > 0 ? step.visitedSoFar.map((id) => labelOf(map, id)).join(" → ") : "(chưa)"}
        </p>
      </div>
      <p className="notes">{step.narration}</p>
      {last && (
        <p><strong>Thứ tự duyệt {state.config.variant}: {state.visitedOrder.map((id) => labelOf(map, id)).join(" → ")}</strong></p>
      )}
    </div>
  );
}

export function TreeInspector({ state }: Props) {
  const map = nodeMap(state.config);
  const at = clampCursor(state, state.cursor);
  const step = state.steps[at];
  const done = at === state.steps.length - 1;
  const total = state.config.nodes.length;
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <p className="notes">Biến thể: {state.config.variant} ({state.frontierKind === "stack" ? "ngăn xếp – DFS" : "hàng đợi – BFS theo mức"})</p>
      <p className="notes">Gốc: {labelOf(map, state.config.rootId)} · {total} node</p>
      {/* HIỆN DẦN (M17-VR1): trước khi duyệt xong CHỈ nêu phần đã thăm — KHÔNG
          lộ thứ tự cuối ngay từ bước 0 (học sinh mất cơ hội tự suy luận). */}
      <p className="notes">
        {done
          ? `Thứ tự thăm (engine): ${state.visitedOrder.map((id) => labelOf(map, id)).join(" → ")}`
          : `Đã thăm ${step.visitedSoFar.length}/${total}: ${
              step.visitedSoFar.length
                ? step.visitedSoFar.map((id) => labelOf(map, id)).join(" → ")
                : "(chưa nút nào)"
            }`}
      </p>
    </div>
  );
}

/* ── module ── */

export function makeTreeTraversalModule(): SimulationModule<TreeTraversalConfig, TreeTraversalState> {
  return {
    id: "tree.traversal",
    domain: "tree",
    title: "Duyệt cây nhị phân (preorder · inorder · postorder · level-order)",
    interactionMode: "progressive",
    supportedVisualModes: ["2d"],

    validateConfig: validateTreeTraversalConfig,

    init: (config) => {
      const { frontierKind, steps, visitedOrder } = buildTreeTraversal(config);
      return { config, frontierKind, steps, visitedOrder, cursor: 0 };
    },

    apply: (state) => state, // v1 không what-if

    timeline: {
      stepCount: (s) => s.steps.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: clampCursor(s, step) }),
    },

    getExplainContext: (state) => {
      const at = clampCursor(state, state.cursor);
      const step = state.steps[at];
      return {
        simulation_id: "tree.traversal",
        variant: state.config.variant,
        root: state.config.rootId,
        node_count: state.config.nodes.length,
        visited_order: state.visitedOrder,
        frontier_kind: state.frontierKind,
        frontier: step.frontierAfter,
        visited_so_far: step.visitedSoFar,
        current_step: at + 1,
        total_steps: state.steps.length,
        narration: step.narration,
      };
    },

    Workspace: TreeWorkspace,
    Inspector: TreeInspector,
  };
}

export function registerTreeDomain(): void {
  registerSimulation(makeTreeTraversalModule());
}
