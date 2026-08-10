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
  /**
   * Đường đi ngắn nhất (BFS) — engine tất định tính, KHÔNG từ LLM.
   *
   * W4B-2I: `[]` NAY LÀ GIÁ TRỊ HỢP LỆ, nghĩa là "không có đường đi". Trước wave
   * này `bfsRoute` vẫn trả `[]` nhưng không chỗ nào biểu diễn được nó:
   * `validateNetworkConfig` chặn từ cổng, và `buildSteps` thì NÉ`M` lỗi
   * (`byId[route[0]]` → `undefined.type`). Nên tình huống sư phạm đắt nhất của
   * bài này — "ngắt liên kết thì gói tin còn tới được không?" — không kể được.
   */
  route: string[];
  /** Diễn biến từng bước — engine dựng, không phải LLM sinh. */
  steps: NetStep[];
  cursor: number;
  /**
   * TOPOLOGY GỐC đã validate — thí nghiệm KHÔNG BAO GIỜ ghi đè lên nó.
   *
   * `BASELINE_RESTORABLE`: mọi what-if đọc từ đây để dựng lại, nên "Về ban đầu"
   * là phép toán tất định chứ không phải cố lần ngược chuỗi thao tác đã làm.
   * Chỉ dữ liệu NGỮ NGHĨA (topology), không có gì thuộc trình bày.
   */
  baseline: { links: [string, string][]; source: string; destination: string };
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

/**
 * Dựng timeline diễn biến gói tin dọc theo route.
 *
 * W4B-2I — ROUTE RỖNG KHÔNG CÒN LÀ CA NÉM LỖI. Nó dựng ĐÚNG MỘT bước: gói tin
 * hình thành tại nguồn rồi không đi được đâu. Đó là sự thật tất định mà BFS đã
 * tính (`prev` không chạm tới đích), không phải một thông báo lỗi kỹ thuật —
 * nên nó thuộc timeline như mọi bước khác, và `packetAt` vẫn là một nodeId thật
 * để renderer 2D/3D không phải biết gì thêm (giữ nguyên M7.FREEZE).
 *
 * `source` truyền tường minh: khi route rỗng thì `route[0]` không tồn tại, và
 * đó chính là chỗ bản cũ nổ.
 */
export function buildSteps(
  route: string[],
  byId: Record<string, NetNode>,
  source: string,
  destination: string,
): NetStep[] {
  if (route.length === 0) {
    const src = byId[source];
    const dst = byId[destination];
    return [
      {
        packetAt: source,
        narration:
          `Gói tin hình thành tại ${typeLabel(src.type)} (${source}), nhưng không còn ` +
          `liên kết nào dẫn tới ${typeLabel(dst.type)} (${destination}) — gói tin không đi được.`,
      },
    ];
  }
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

/**
 * TÍNH LẠI toàn bộ diễn biến từ topology — CHỦ SỞ HỮU DUY NHẤT của phép này.
 *
 * `init` và mọi thí nghiệm what-if đều đi qua đây, nên không thể có chuyện lượt
 * đầu và lượt sau khi sửa mô hình chạy hai đường tính khác nhau. Renderer không
 * bao giờ gọi `bfsRoute` — nó chỉ đọc `route`/`steps` có sẵn trong state.
 */
export function recompute(
  nodes: NetNode[],
  links: [string, string][],
  source: string,
  destination: string,
): { route: string[]; steps: NetStep[] } {
  const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
  const route = bfsRoute(nodes.map((n) => n.id), links, source, destination);
  return { route, steps: buildSteps(route, byId, source, destination) };
}

/** Gói tin có tới được đích không — dẫn xuất, KHÔNG lưu thành cờ riêng. */
export function isReachable(state: NetworkState): boolean {
  return state.route.length > 0;
}

/** Topology hiện tại có khác bản gốc không (đang ở nhánh thí nghiệm). */
export function isModified(state: NetworkState): boolean {
  const key = (ls: [string, string][]) =>
    ls.map(([a, b]) => (a < b ? `${a}~${b}` : `${b}~${a}`)).sort().join("|");
  return (
    key(state.links) !== key(state.baseline.links) ||
    state.source !== state.baseline.source ||
    state.destination !== state.baseline.destination
  );
}

/* ── M8-PRE-LIP: nền tảng cho nhịp DỰ ĐOÁN "chặng kế tiếp" ────────────────
 * Ground truth CÓ SẴN MIỄN PHÍ: engine đã chạy BFS để dựng route. Ta chỉ ĐỌC lại,
 * không thêm engine mới, không gọi LLM.
 */

/** Các nút nối trực tiếp với `id` (theo links — vô hướng). */
export function neighborsOf(state: NetworkState, id: string): string[] {
  const out: string[] = [];
  for (const [a, b] of state.links) {
    if (a === id && !out.includes(b)) out.push(b);
    if (b === id && !out.includes(a)) out.push(a);
  }
  return out;
}

/** Số CHẶNG ngắn nhất từ `from` tới `to`; -1 nếu không có đường (BFS tất định). */
export function hopDistance(state: NetworkState, from: string, to: string): number {
  const path = bfsRoute(
    state.nodes.map((n) => n.id),
    state.links,
    from,
    to,
  );
  return path.length === 0 ? -1 : path.length - 1;
}
