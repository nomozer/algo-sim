import { registerSimulation } from "../../registry";
import type { NetNode, NetworkConfig, NetworkState, NodeType } from "./model";
import {
  bfsRoute, currentStep, hopDistance, isModified, isReachable, neighborsOf, recompute, typeLabel,
} from "./model";
import type { ConfigResult, SimAction, SimulationModule } from "../../types";
import { NetworkInspector, NetworkWorkspace } from "./ui";
import { makeEncapsulationModule } from "./encap";
import { registerTraverseModule } from "./traverse-module";

/**
 * network.packet_routing — mô phỏng TIẾN TRÌNH (progressive): có timeline.
 * Route (BFS) và diễn biến từng bước do engine tất định dựng, KHÔNG từ LLM (§6).
 */

const NODE_TYPES: NodeType[] = ["client", "router", "server", "switch", "isp"];

function validateNetworkConfig(raw: unknown): ConfigResult<NetworkConfig> {
  if (typeof raw !== "object" || raw === null) {
    return { ok: false, error: "Config không phải đối tượng JSON." };
  }
  const r = raw as Record<string, unknown>;
  const rawNodes = r.nodes;
  if (!Array.isArray(rawNodes) || rawNodes.length < 2 || rawNodes.length > 8) {
    return { ok: false, error: '"nodes" phải là danh sách 2–8 nút.' };
  }
  const ids: string[] = [];
  const nodes: NetNode[] = [];
  for (const n of rawNodes) {
    if (typeof n !== "object" || n === null) return { ok: false, error: "Nút không hợp lệ." };
    const nn = n as Record<string, unknown>;
    if (typeof nn.id !== "string" || !nn.id) return { ok: false, error: 'Mỗi nút phải có "id" là chuỗi.' };
    if (ids.includes(nn.id)) return { ok: false, error: `Trùng id nút "${nn.id}".` };
    ids.push(nn.id);
    nodes.push({ id: nn.id, type: (NODE_TYPES as string[]).includes(nn.type as string) ? (nn.type as NodeType) : "router" });
  }

  const rawLinks = r.links;
  if (!Array.isArray(rawLinks) || rawLinks.length < 1) {
    return { ok: false, error: '"links" phải có ít nhất một liên kết.' };
  }
  const links: [string, string][] = [];
  for (const lk of rawLinks) {
    if (!Array.isArray(lk) || lk.length !== 2 || !ids.includes(lk[0]) || !ids.includes(lk[1]) || lk[0] === lk[1]) {
      return { ok: false, error: "Mỗi liên kết phải là cặp id nút có thật, khác nhau." };
    }
    links.push([lk[0], lk[1]]);
  }

  const source = r.source;
  const destination = r.destination;
  if (typeof source !== "string" || typeof destination !== "string" || !ids.includes(source) || !ids.includes(destination) || source === destination) {
    return { ok: false, error: '"source" và "destination" phải là hai nút khác nhau có thật.' };
  }
  if (bfsRoute(ids, links, source, destination).length === 0) {
    return { ok: false, error: "Không có đường đi từ nguồn tới đích." };
  }

  return {
    ok: true,
    config: { nodes, links, source, destination, notes: typeof r.notes === "string" ? r.notes : null },
  };
}

/**
 * State = topology + route (BFS) + diễn biến + con trỏ bước. KHÔNG có bố cục:
 * vị trí là chuyện của renderer (M7.FREEZE — renderer-neutral state).
 */
function buildState(config: NetworkConfig): NetworkState {
  const { route, steps } = recompute(
    config.nodes, config.links, config.source, config.destination,
  );
  return {
    nodes: config.nodes,
    links: config.links,
    source: config.source,
    destination: config.destination,
    route,
    steps,
    cursor: 0,
    baseline: {
      links: config.links,
      source: config.source,
      destination: config.destination,
    },
  };
}

/* ── W4B-2I: THÍ NGHIỆM CẤU TRÚC CÓ RÀNG BUỘC ───────────────────────────────
 *
 * Hợp đồng: học sinh đổi MÔ HÌNH (nối / ngắt liên kết), engine tính lại tuyến
 * bằng đúng `recompute` mà lượt đầu đã dùng, rồi hệ quả hiện ra. Renderer không
 * tính định tuyến, không đoán tuyến mới, không dựng "đường có vẻ đúng".
 *
 * VÌ SAO CHỈ NỐI/NGẮT/VỀ-BAN-ĐẦU. Đủ để dạy trọn ý "đứt một chặng thì sao" —
 * đúng kịch bản sư phạm của bài — và mỗi phép đều tất định trên topology sẵn có.
 * Thêm/xoá NÚT thì phải kéo theo đặt kiểu nút, đặt lại nguồn/đích khi nút bị
 * xoá, và bố cục cho nút mới ở cả 2D lẫn 3D: đó là một trình soạn đồ thị, tức
 * là Packet Tracer, thứ §27 cấm. Cố ý để ngoài, không phải bỏ sót.
 *
 * FAIL-CLOSED. Mọi tham chiếu nút phải có thật, hai đầu phải khác nhau, ngắt thì
 * liên kết phải đang tồn tại, nối thì phải chưa tồn tại. Không hợp lệ ⇒ TRẢ
 * NGUYÊN state cũ (store chỉ ghi khi tham chiếu đổi), không ném, không sửa liều.
 *
 * KHÔNG ĐỤNG `baseline`: nó được chép sang nguyên vẹn ở mọi nhánh, nên "Về ban
 * đầu" luôn dựng lại được đúng đề gốc.
 */

const linkKey = (a: string, b: string) => (a < b ? `${a}~${b}` : `${b}~${a}`);

function applyTopology(state: NetworkState, links: [string, string][]): NetworkState {
  const { route, steps } = recompute(state.nodes, links, state.source, state.destination);
  // cursor về 0: diễn biến mới là một câu chuyện khác, giữ con trỏ cũ sẽ trỏ
  // vào một bước không còn tồn tại.
  return { ...state, links, route, steps, cursor: 0 };
}

export function applyNetworkAction(state: NetworkState, action: SimAction): NetworkState {
  if (action.type === "net_reset") {
    return applyTopology({ ...state, ...state.baseline }, state.baseline.links);
  }
  if (action.type !== "net_connect" && action.type !== "net_disconnect") return state;

  const { a, b } = action;
  const known = new Set(state.nodes.map((n) => n.id));
  if (!known.has(a) || !known.has(b) || a === b) return state;

  const key = linkKey(a, b);
  const exists = state.links.some(([x, y]) => linkKey(x, y) === key);

  if (action.type === "net_disconnect") {
    if (!exists) return state;
    return applyTopology(state, state.links.filter(([x, y]) => linkKey(x, y) !== key));
  }
  if (exists) return state;
  return applyTopology(state, [...state.links, [a, b]]);
}

export function makeNetworkModule(): SimulationModule<NetworkConfig, NetworkState> {
  return {
    id: "network.packet_routing",
    domain: "network",
    title: "Định tuyến gói tin",
    interactionMode: "progressive",
    /* W4B-2R — 2D_ONLY, quyết định bằng CƠ CHẾ chứ không bằng lịch sử kiến trúc.
     *
     * M8 dựng 3D ở đây, M10 khai trung thực `role: "architectural_poc"` +
     * `meaningOfZ: "bố cục, KHÔNG mang nghĩa khái niệm"`. Lời khai đó chính là
     * bằng chứng kết tội: cơ chế của bài là TOPOLOGY + ĐƯỜNG ĐI + KHẢ NĂNG TỚI
     * ĐƯỢC, cả ba đọc trọn trên mặt phẳng, còn trục Z chỉ tách hàng cho đẹp.
     * Giữ toggle vì "sản phẩm đã có renderer 3D" đúng là lý do mà chính sách
     * biểu diễn liệt vào `2D_AND_3D_BY_DEFAULT`.
     *
     * KHÔNG mất gì về kiến trúc: `network.protocol_encapsulation` vẫn chứng minh
     * 2D/3D dùng chung một state (Z = tầng giao thức — nghĩa khái niệm thật), nên
     * bất biến #16/#18 vẫn có bài làm chứng.
     */
    supportedVisualModes: ["2d"],

    validateConfig: validateNetworkConfig,

    init: buildState,

    apply: applyNetworkAction,

    // Progressive → có timeline capability (M5 §2, §4)
    timeline: {
      stepCount: (s) => s.steps.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: Math.max(0, Math.min(step, s.steps.length - 1)) }),
    },

    /**
     * M8-PRE-LIP — nhịp DỰ ĐOÁN: "chặng kế tiếp là nút nào?"
     *
     * Trước đây domain này KHÔNG có tương tác nào (apply = identity): học sinh chỉ
     * bấm Play và xem. Nay có một hành động THẬT, chấm bằng chính BFS engine đã chạy.
     *
     * NGUYÊN TẮC PHÁT NGÔN (chỉ nói điều engine CHỨNG MINH được):
     * - Sai ⇒ chỉ được nói "không phải chặng kế tiếp trên đường đi ngắn nhất mà
     *   engine BFS đã chọn". TUYỆT ĐỐI không nói "đi lối đó là không thể".
     * - Nếu nút học sinh chọn CŨNG nằm trên một đường ngắn nhất khác (bằng chặng),
     *   phải NÓI RÕ điều đó — không được để học sinh hiểu nhầm là lựa chọn tồi.
     * - Route canonical BẤT BIẾN: check là hàm thuần, không đụng state.
     */
    predict: {
      challenge: (s) => {
        // Chỉ hỏi khi gói tin còn chặng phía trước.
        if (s.route.length < 2 || s.cursor >= s.route.length - 1) return null;
        const here = s.route[s.cursor];
        const options = neighborsOf(s, here).map((id) => {
          const n = s.nodes.find((x) => x.id === id)!;
          return { id, label: `${typeLabel(n.type)} (${id})` };
        });
        if (options.length === 0) return null;
        const cur = s.nodes.find((x) => x.id === here)!;
        return {
          question:
            `Gói tin đang ở ${typeLabel(cur.type)} (${here}), cần tới ${s.destination}. ` +
            `Theo em, chặng KẾ TIẾP trên đường đi ngắn nhất là nút nào?`,
          options,
        };
      },

      check: (s, answerId) => {
        if (s.route.length < 2 || s.cursor >= s.route.length - 1) {
          return {
            verdict: "unsupported_to_verify",
            answerId,
            message: "Gói tin đã tới đích — không còn chặng nào để dự đoán.",
          };
        }
        const here = s.route[s.cursor];
        const expectedId = s.route[s.cursor + 1];
        if (!neighborsOf(s, here).includes(answerId)) {
          return {
            verdict: "incorrect",
            answerId,
            expectedId,
            message: `Nút "${answerId}" không nối trực tiếp với "${here}" nên gói tin không thể nhảy thẳng tới đó.`,
          };
        }
        if (answerId === expectedId) {
          return {
            verdict: "correct",
            answerId,
            expectedId,
            message:
              `Chính xác. Engine BFS cũng chọn "${expectedId}" làm chặng kế tiếp trên ` +
              `đường đi ngắn nhất tới "${s.destination}".`,
          };
        }
        // SAI so với đường chuẩn — nhưng chỉ được nói ĐÚNG điều engine tính được.
        const remaining = hopDistance(s, here, s.destination); // số chặng còn lại theo đường ngắn nhất
        const viaAnswer = hopDistance(s, answerId, s.destination);
        let consequence: string;
        if (viaAnswer < 0) {
          consequence = `Từ "${answerId}" thì KHÔNG còn đường nào tới "${s.destination}" — gói tin sẽ mắc kẹt.`;
        } else if (1 + viaAnswer === remaining) {
          // Trung thực: đây cũng là MỘT đường ngắn nhất, chỉ không phải đường engine chọn.
          consequence =
            `Lưu ý: đi qua "${answerId}" CŨNG cho một đường ngắn nhất (${1 + viaAnswer} chặng, ` +
            `bằng đường chuẩn). Engine BFS chọn "${expectedId}" vì duyệt các liên kết theo thứ tự khai báo.`;
        } else {
          consequence =
            `Đi qua "${answerId}" thì còn ${1 + viaAnswer} chặng tới đích, ` +
            `dài hơn đường ngắn nhất (${remaining} chặng).`;
        }
        return {
          verdict: "incorrect",
          answerId,
          expectedId,
          message:
            `Đây không phải chặng kế tiếp trên đường đi ngắn nhất mà engine BFS đã tính ` +
            `(chặng chuẩn là "${expectedId}"). ${consequence}`,
        };
      },
    },

    // (SHELL-N) MỘT nguồn chữ cho CẢ 2D lẫn 3D — trước đây `ui.tsx` và
    // `ui3d.tsx` mỗi bên tự dựng một dòng narration giống hệt nhau.
    narrate: (state) => ({ text: currentStep(state).narration }),

    getExplainContext: (state) => {
      const step = currentStep(state);
      return {
        simulation_id: "network.packet_routing",
        source: state.source,
        destination: state.destination,
        route: state.route,
        current_step: state.cursor + 1,
        total_steps: state.steps.length,
        packet_at: step.packetAt,
        narration: step.narration,
        /* W4B-2I: sau một thí nghiệm cấu trúc có thể KHÔNG còn đường đi. Không
           nói ra thì Explain nhận `route: []` mà không có gì phân biệt "chưa
           chạy" với "không tới được", và sẽ giải thích một tuyến không tồn tại. */
        reachable: isReachable(state),
        topology_modified: isModified(state),
      };
    },

    Workspace: NetworkWorkspace,
    Inspector: NetworkInspector,
  };
}

export function registerNetworkDomain(): void {
  registerSimulation(makeNetworkModule());
  // M10: module THỨ HAI của domain network — đóng gói/mở gói TCP/IP (3D sư phạm).
  registerSimulation(makeEncapsulationModule());
  // M17 W1: duyệt đồ thị BFS/DFS tổng quát (packet_routing = application variant).
  registerTraverseModule();
}
