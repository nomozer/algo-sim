/** Model domain network — định tuyến gói tin (M5). Progressive: có timeline. */

export type NodeType = "client" | "router" | "server" | "switch" | "isp";

export interface NetNode {
  id: string;
  type: NodeType;
}

export interface NetworkConfig {
  nodes: NetNode[];
  links: [string, string][];
  source: string;
  destination: string;
  notes: string | null;
}

export interface NetStep {
  /** Nút mà gói tin đang ở SAU bước này. */
  packetAt: string;
  narration: string;
}

/**
 * State CHỈ chứa sự thật ngữ nghĩa của mô phỏng — RENDERER-NEUTRAL (M7.FREEZE).
 *
 * Trước đây state còn giữ `positions` (toạ độ pixel do `layout()` sinh). Đó là
 * dữ liệu TRÌNH BÀY, không phải ngữ nghĩa: vị trí gói tin được diễn đạt bằng
 * `steps[].packetAt` = **id nút** (giống `Frame.entityPos` của generic), và
 * `getExplainContext` chưa bao giờ dùng tới toạ độ. Bố cục nay thuộc renderer
 * (xem `layout2d` trong ui.tsx) — nhờ vậy một renderer 3D dùng lại được ĐÚNG
 * state này mà không phải fork module hay tự bịa ngữ nghĩa.
 */
export interface NetworkState {
  nodes: NetNode[];
  links: [string, string][];
  source: string;
  destination: string;
  /** Đường đi ngắn nhất (BFS) — engine tất định tính, KHÔNG từ LLM. */
  route: string[];
  /** Diễn biến từng bước — engine dựng, không phải LLM sinh. */
  steps: NetStep[];
  cursor: number;
}

const TYPE_LABEL: Record<NodeType, string> = {
  client: "Máy khách",
  router: "Router",
  server: "Máy chủ",
  switch: "Switch",
  isp: "ISP",
};

export function typeLabel(t: NodeType): string {
  return TYPE_LABEL[t];
}

/** Đường đi ngắn nhất nguồn→đích bằng BFS (tất định: duyệt theo thứ tự khai báo). */
export function bfsRoute(
  nodeIds: string[],
  links: [string, string][],
  source: string,
  destination: string,
): string[] {
  const adj: Record<string, string[]> = {};
  for (const id of nodeIds) adj[id] = [];
  for (const [a, b] of links) {
    adj[a].push(b);
    adj[b].push(a);
  }
  const prev: Record<string, string | null> = { [source]: null };
  const queue = [source];
  while (queue.length) {
    const cur = queue.shift()!;
    if (cur === destination) break;
    for (const nxt of adj[cur]) {
      if (!(nxt in prev)) {
        prev[nxt] = cur;
        queue.push(nxt);
      }
    }
  }
  if (!(destination in prev)) return [];
  const route: string[] = [];
  let at: string | null = destination;
  while (at !== null) {
    route.unshift(at);
    at = prev[at];
  }
  return route;
}

/** Dựng timeline diễn biến gói tin dọc theo route. */
export function buildSteps(route: string[], byId: Record<string, NetNode>): NetStep[] {
  const steps: NetStep[] = [];
  const src = byId[route[0]];
  steps.push({ packetAt: route[0], narration: `Tạo gói tin tại ${typeLabel(src.type)} (${src.id}).` });
  for (let k = 0; k < route.length - 1; k++) {
    const to = byId[route[k + 1]];
    const last = k + 1 === route.length - 1;
    steps.push({
      packetAt: route[k + 1],
      narration: last
        ? `Gói tin tới đích ${typeLabel(to.type)} (${to.id}). Hoàn tất!`
        : `Gói tin chuyển tới ${typeLabel(to.type)} (${to.id}), tiếp tục chuyển tiếp.`,
    });
  }
  return steps;
}

export function currentStep(state: NetworkState): NetStep {
  return state.steps[Math.max(0, Math.min(state.cursor, state.steps.length - 1))];
}
