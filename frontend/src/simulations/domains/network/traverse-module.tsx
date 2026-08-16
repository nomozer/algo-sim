import { useEffect, useRef, useState } from "react";
import { registerSimulation } from "../../registry";
import { TraversalFrontier, frontierDelta } from "../../../components/TraversalFrontier";
import { statusLabel, traversalEdgeViews, usedStatuses, type EdgeStatus } from "./edge-view";
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
      /**
       * Nút mà `current` được nạp TỪ ĐÓ — tức cạnh của CÂY DUYỆT đi vào bước
       * này. `null` ở nút xuất phát.
       *
       * W4B-1B: engine vốn đã biết dữ kiện này (`entry.parent`) nhưng trước đây
       * VỨT ĐI sau khi dựng `pred`. Không có nó, renderer buộc phải đoán cạnh
       * đang đi bằng "nút thăm liền trước → nút hiện tại" — SAI ở DFS: sau khi
       * quay lui, nút thăm liền trước thường KHÔNG kề `current`, nên sẽ tô một
       * cạnh không tồn tại trong `config.edges`. Đó là renderer bịa ngữ nghĩa
       * (bất biến #6), tệ hơn hẳn lỗi không tô gì.
       */
      parent: string | null;
      /** Frontier SAU khi thăm current và nạp hàng xóm mới. */
      frontierAfter: string[];
      /** Hàng xóm THỰC SỰ được nạp ở bước này (không gồm nút đã thấy). */
      frontierAdded: string[];
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
      // Provenance do ENGINE giữ, không phải renderer suy: cạnh cây duyệt đi
      // vào bước này, và hàng xóm thực sự được nạp ở bước này.
      parent: entry.parent,
      frontierAfter: displayFrontier(),
      frontierAdded: [...added],
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

/* ── W4B-2A — BỐ CỤC ĐỒ THỊ THÍCH ỨNG THEO BỀ RỘNG KHẢ DỤNG ────────────────
 *
 * Đo được (xếp hạng lại W4B-2A): đồ thị giữ đúng 420px ở mọi sân khấu — 0,32
 * bề rộng ở 1920×1080, thấp nhất toàn danh mục, và không nhúc nhích khi đóng
 * panel Quan sát (+316px sân khấu → +0px hình).
 *
 * Chỗ dư KHÔNG dùng để phóng to nút. `NODE_R` giữ nguyên 16. Nó dùng để **tách
 * các nút ra xa nhau hơn**, tức là để đọc được: cạnh ít chồng chéo, quan hệ
 * cha→hiện tại rõ hơn, nhãn không dính nhau. Đó là cơ chế của bài, không phải
 * kích thước của đối tượng.
 *
 * CHỈ nới theo CHIỀU NGANG. Chiều cao giữ nguyên `H` vì sân khấu đang chật
 * chiều cao ở laptop 768px — nới cao sẽ tái sinh đúng lớp lỗi
 * `CONTENT_HIDDEN_IN_PANEL` mà W4B-1A vừa đóng. Vì vậy vòng tròn thành **bầu
 * dục**: bán trục ngang lớn theo `W`, bán trục dọc vẫn theo `H`.
 *
 * `viewBox` vẫn bằng đúng bề rộng hiển thị nên `scale ≈ 1` được giữ — chữ và
 * nét không phình. Hình lớn hơn vì BỐ CỤC lớn hơn.
 */
const MIN_GRAPH_W = 360;
/** Trần thiết kế hiện hành: tách thêm nữa không giúp đọc cơ chế tốt hơn. */
const MAX_GRAPH_W = 820;
const GRAPH_SAFE_PAD = 24;

export interface GraphChartLayout {
  width: number;
  height: number;
  capped: boolean;
}

/** Bố cục nội tại của sân khấu đồ thị. HÀM THUẦN — kiểm được không cần browser. */
export function graphChartLayout(available: number, long = false): GraphChartLayout {
  const height = long ? H + 28 : H;
  if (!Number.isFinite(available) || available <= 0) {
    return { width: W, height, capped: false };
  }
  const usable = Math.max(0, available - GRAPH_SAFE_PAD);
  const width = Math.max(MIN_GRAPH_W, Math.min(MAX_GRAPH_W, Math.floor(usable)));
  return { width, height, capped: width >= MAX_GRAPH_W };
}

/**
 * Mỗi trạng thái cạnh mang ÍT NHẤT HAI kênh tín hiệu (DESIGN_BRIEF §3.5: màu
 * không bao giờ là tín hiệu duy nhất): màu + độ dày, và `considering` thêm nét
 * đứt. Người không phân biệt được màu vẫn đọc được bằng độ dày/nét.
 */
const EDGE_STYLE: Record<EdgeStatus | "path", { stroke: string; width: number; dash?: string }> = {
  idle: { stroke: "var(--ink-faint)", width: 1.5 },
  considering: { stroke: "var(--primary)", width: 2, dash: "5 4" },
  active: { stroke: "var(--accent-orange)", width: 4 },
  traversed: { stroke: "var(--accent-green)", width: 3 },
  remaining: { stroke: "var(--ink-faint)", width: 1.5 }, // không dùng ở duyệt đồ thị
  path: { stroke: "var(--accent-green)", width: 4 },
};

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

/**
 * Bố trí nút trên một BẦU DỤC, không phải vòng tròn.
 *
 * Vòng tròn lấy `r = min(W, H)/2`, nên nới bề rộng mà giữ chiều cao thì bán
 * kính vẫn bị chiều cao khoá — chỗ vừa giành được không tới tay nút nào. Bầu
 * dục tách hai bán trục: ngang theo `width`, dọc theo `height`. Nhờ vậy chỗ dư
 * theo phương ngang thành KHOẢNG CÁCH GIỮA CÁC NÚT, còn chiều cao không đổi
 * nên không đụng tới hợp đồng chiều cao của W4B-1A.
 *
 * `width`/`height` mặc định giữ đúng hằng số cũ, nên mọi lời gọi và test SSR
 * chưa truyền kích thước vẫn cho kết quả y hệt bản trước.
 */
function circleLayout(
  nodes: TraverseNode[],
  long = false,
  width: number = W,
  height: number = H,
): Map<string, { x: number; y: number }> {
  const cx = width / 2;
  const cy = height / 2;
  const inset = long ? 48 : 34;
  const rx = Math.max(NODE_R, width / 2 - inset);
  const ry = Math.max(NODE_R, height / 2 - inset);
  return new Map(
    nodes.map((n, i) => {
      const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
      return [n.id, { x: cx + rx * Math.cos(angle), y: cy + ry * Math.sin(angle) }];
    }),
  );
}

/** Nhãn hiển thị của một node — đọc từ config, không suy từ narration. */
function labelOfNode(config: TraverseConfig, id: string): string {
  return config.nodes.find((n) => n.id === id)?.label ?? id;
}

/** W4B-4C — BFS hay DFS, và xuất phát từ đâu: hai lựa chọn ĐÓNG mà engine
 *  đã tính được. Sửa tôpô KHÔNG thuộc bài này (đó là `packet_routing`). */
function TraverseParamBar({ state, busy, dispatch }: Props) {
  return (
    <div className="param-bar" role="group" aria-label="Chọn cách duyệt đồ thị">
      <label>
        Thuật toán
        <select value={state.config.variant} disabled={busy}
          onChange={(e) => dispatch({ type: "set_param", name: "variant", value: e.target.value })}>
          <option value="bfs">BFS — theo chiều rộng</option>
          <option value="dfs">DFS — theo chiều sâu</option>
        </select>
      </label>
      <label>
        Xuất phát
        <select value={state.config.start} disabled={busy}
          onChange={(e) => dispatch({ type: "set_param", name: "start", value: e.target.value })}>
          {state.config.nodes.map((n) => (
            <option key={n.id} value={n.id}>{n.label ?? n.id}</option>
          ))}
        </select>
      </label>
    </div>
  );
}

export function TraverseWorkspace({ state, config, busy, dispatch }: Props) {
  const at = clampCursor(state, state.cursor);
  const step = state.steps[at];
  const long = hasLongLabel(state.config.nodes);
  /* Bề rộng khả dụng đo từ CHÍNH khung chứa — cùng khuôn đã dùng ở ArrayView. */
  const boxRef = useRef<HTMLDivElement>(null);
  const [available, setAvailable] = useState(0);
  useEffect(() => {
    const el = boxRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(([entry]) => setAvailable(Math.round(entry.contentRect.width)));
    ro.observe(el);
    setAvailable(Math.round(el.getBoundingClientRect().width));
    return () => ro.disconnect();
  }, []);

  const gl = graphChartLayout(available, long);
  const pos = circleLayout(state.config.nodes, long, gl.width, gl.height);
  const visited = new Set(step.visitedSoFar);
  const current = step.kind === "visit" ? step.current : null;
  const last = at === state.steps.length - 1;
  const pathEdges = new Set<string>();
  if (last && state.path) {
    for (let i = 0; i < state.path.length - 1; i++) {
      pathEdges.add(`${state.path[i]}→${state.path[i + 1]}`);
    }
  }
  // Trạng thái cạnh DẪN XUẤT từ provenance của engine (`parent`/`frontierAdded`),
  // không suy từ thứ tự thăm — xem `edge-view.ts`.
  const edgeViews = traversalEdgeViews(state.config.edges, state.config.directed, state.steps, at);
  // Chú giải khớp HAI CHIỀU với thứ đang vẽ: chỉ nêu trạng thái thật sự xuất
  // hiện ở bước này, và mọi trạng thái xuất hiện đều được nêu.
  const edgeStatuses = usedStatuses(edgeViews).filter((s) => s !== "idle");

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div className="sim-stage" ref={boxRef}>
        <svg viewBox={`0 0 ${gl.width} ${gl.height}`}
             style={{ width: "100%", maxWidth: gl.width }} role="img"
             aria-label="Đồ thị duyệt">
          {edgeViews.map((ev, i) => {
            const pa = pos.get(ev.from)!;
            const pb = pos.get(ev.to)!;
            const onPath =
              pathEdges.has(`${ev.from}→${ev.to}`) ||
              (!state.config.directed && pathEdges.has(`${ev.to}→${ev.from}`));
            // Ở bước cuối, ĐƯỜNG ĐI tới đích là kết luận của bài — giữ nguyên
            // cách tô cũ, đè lên trạng thái duyệt.
            const style = onPath ? EDGE_STYLE.path : EDGE_STYLE[ev.status];
            return (
              <line
                key={i}
                x1={pa.x} y1={pa.y} x2={pb.x} y2={pb.y}
                stroke={style.stroke}
                strokeWidth={style.width}
                strokeDasharray={style.dash}
                strokeLinecap="round"
              >
                <title>{onPath ? `Đường ${ev.from} – ${ev.to}: thuộc đường đi` : ev.accessibleLabel}</title>
              </line>
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

        {/* Chú giải TÁCH HAI NHÓM: nút và đường. Gộp 4 mục nút với 3 mục đường
            vào một hàng thành 7 mục đọc như nhiễu — hai từ vựng khác nhau cho
            hai loại đối tượng khác nhau. */}
        <p className="stage-legend">
          <span className="legend-group">Nút</span>
          <span><i className="dot is-current" /> đang xử lý</span>
          <span><i className="dot is-done" /> đã thăm</span>
          <span><i className="dot is-frontier" /> đang chờ trong {state.frontierKind === "queue" ? "hàng đợi" : "ngăn xếp"}</span>
          <span><i className="dot is-idle" /> chưa xét</span>
        </p>
        {edgeStatuses.length > 0 && (
          <p className="stage-legend">
            <span className="legend-group">Đường duyệt</span>
            {edgeStatuses.map((s) => (
              <span key={s}>
                <svg width="22" height="8" aria-hidden="true" style={{ verticalAlign: "middle" }}>
                  <line
                    x1="1" y1="4" x2="21" y2="4"
                    stroke={EDGE_STYLE[s].stroke}
                    strokeWidth={EDGE_STYLE[s].width}
                    strokeDasharray={EDGE_STYLE[s].dash}
                    strokeLinecap="round"
                  />
                </svg>{" "}
                {statusLabel(s)}
              </span>
            ))}
          </p>
        )}
      </div>
      {/* W12 §9 — CÔNG CỤ CỦA BÀI, trả về đúng cây render.
          Trước wave này dòng JSX gọi `TraverseParamBar` nằm SAU câu `return`
          của `useEffect` ở trên: cú pháp hợp lệ, TypeScript không kêu, tên
          không "unused" vì vẫn được nhắc — nên nó im lặng không bao giờ render.
          Hệ quả: `network.graph_traversal` là BOUNDED_PARAMETER_TOOL mà học
          sinh không có cách nào đổi BFS↔DFS hay điểm xuất phát. Không unit test
          nào bắt được (không test nào hỏi "control có trên màn hình không");
          chỗ phát hiện là phép đo affordance trên trình duyệt thật. */}
      <TraverseParamBar state={state} config={config} busy={busy} dispatch={dispatch} />
      <p className="notes">{step.narration}</p>
    </div>
  );
}

export function TraverseInspector({ state }: Props) {
  /**
   * HIỆN DẦN — CẤM LỘ ĐÁP ÁN (DESIGN_BRIEF §3.3).
   *
   * Bản trước in TOÀN BỘ `visitedOrder` và `path` vô điều kiện, tức là ngay ở
   * bước 1/8: học sinh đọc được thứ tự thăm và đường đi trước khi mô phỏng
   * chạy, mất sạch cơ hội tự suy luận. Module anh em `tree.traversal` đã sửa
   * đúng lỗi này ở M17-VR1 và có comment ghi lại; ở đây thì bị bỏ quên — đúng
   * hình dạng anti-pattern #10 (vá một bề mặt, quên bề mặt anh em).
   *
   * Nay inspector chỉ đọc thứ mà BƯỚC HIỆN TẠI đã tới. Kết quả cuối (thứ tự
   * đầy đủ · đường đi · đến được hay không) chỉ công bố ở bước cuối.
   *
   * Cũng bỏ chuỗi "(engine)" — thuật ngữ của lập trình viên, không phải của
   * học sinh (§3.4).
   */
  const at = clampCursor(state, state.cursor);
  const step = state.steps[at];
  const done = at === state.steps.length - 1;
  const total = state.config.nodes.length;
  const seen = step.visitedSoFar;

  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <p className="notes">
        Biến thể: {state.config.variant.toUpperCase()} (
        {state.frontierKind === "queue" ? "hàng đợi FIFO" : "ngăn xếp LIFO"})
        {state.config.directed ? " · đồ thị CÓ hướng" : " · đồ thị vô hướng"}
      </p>
      <p className="notes">
        {done
          ? `Thứ tự thăm: ${state.visitedOrder.join(" → ")}`
          : `Đã thăm ${seen.length}/${total}: ${seen.length ? seen.join(" → ") : "(chưa nút nào)"}`}
      </p>
      {done && state.reachable !== null && (
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

/**
 * W4B-4C — CHỌN THUẬT TOÁN VÀ ĐIỂM XUẤT PHÁT.
 *
 * Bài này dạy sự KHÁC NHAU giữa BFS và DFS trên cùng một đồ thị, và ảnh hưởng
 * của điểm xuất phát. Cả hai đều là lựa chọn ĐÓNG mà `buildTraversal` đã tính
 * được — nên tương tác không cần sửa tôpô (sửa tôpô là việc của
 * `packet_routing`; ở đây nó sẽ thành một trình vẽ đồ thị).
 */
export function withTraverseParam(
  config: TraverseConfig,
  name: string,
  value: number | string | boolean,
): TraverseConfig | null {
  if (typeof value !== "string") return null;
  if (name === "variant") {
    if (!(TRAVERSE_VARIANTS as readonly string[]).includes(value)) return null;
    if (value === config.variant) return null;
    return { ...config, variant: value as TraverseVariant };
  }
  if (name === "start") {
    if (!config.nodes.some((n) => n.id === value)) return null;
    if (value === config.start) return null;
    return { ...config, start: value };
  }
  return null;
}

export function makeTraverseModule(): SimulationModule<TraverseConfig, TraverseState> {
  return {
    id: "network.graph_traversal",
    domain: "network",
    /* W5Z — ô chọn ngay dưới sân khấu đã ghi "BFS — theo chiều rộng" / "DFS —
       theo chiều sâu", kèm nghĩa tiếng Việt. Phụ đề nhắc lại hai từ viết tắt
       trần là bớt thông tin đi chứ không thêm. */
    title: "Duyệt đồ thị",
    /* W4B-4C — `progressive` → `hybrid`: nay có CẢ dòng thời gian giải thích
       LẪN tham số học sinh đổi được bất cứ lúc nào trên sân khấu. */
    interactionMode: "hybrid",
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

    /* W4B-4C — đổi thuật toán / điểm xuất phát ⇒ dựng lại bằng `buildTraversal`. */
    apply: (state, action) => {
      if (action.type !== "set_param") return state;
      const next = withTraverseParam(state.config, action.name, action.value);
      if (!next) return state;
      const { steps, visitedOrder, path, reachable } = buildTraversal(next);
      return {
        ...state,
        config: next,
        frontierKind: next.variant === "bfs" ? "queue" : "stack",
        steps, visitedOrder, path, reachable, cursor: 0,
      };
    },

    timeline: {
      stepCount: (s) => s.steps.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: clampCursor(s, step) }),
    },

    /* W4B-4D — mô hình chạy config NÀO ngay lúc này; shell so với bản đã
       validate để nói ra khi học sinh đã kéo mô hình rời khỏi đề bài. */
    currentConfig: (state) => state.config,

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
