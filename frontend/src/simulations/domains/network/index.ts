import { lazy } from "react";
import { registerSimulation } from "../../registry";
import type { NetNode, NetworkConfig, NetworkState, NodeType } from "./model";
import { bfsRoute, buildSteps, currentStep, hopDistance, neighborsOf, typeLabel } from "./model";
import type { ConfigResult, SimulationModule } from "../../types";
import { NetworkInspector, NetworkWorkspace } from "./ui";

/**
 * M8: renderer 3D nạp LƯỜI (code-split) — Three.js (~600KB) chỉ tải khi người
 * dùng thật sự bấm 3D; người dùng 2D không trả thêm một byte bundle nào.
 * VẪN là cùng module/config/state/timeline — chỉ khác component vẽ.
 */
const Network3DWorkspace = lazy(() =>
  import("./ui3d").then((m) => ({ default: m.Network3DWorkspace })),
);

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
  const ids = config.nodes.map((n) => n.id);
  const byId = Object.fromEntries(config.nodes.map((n) => [n.id, n]));
  const route = bfsRoute(ids, config.links, config.source, config.destination);
  return {
    nodes: config.nodes,
    links: config.links,
    source: config.source,
    destination: config.destination,
    route,
    steps: buildSteps(route, byId),
    cursor: 0,
  };
}

export function makeNetworkModule(): SimulationModule<NetworkConfig, NetworkState> {
  return {
    id: "network.packet_routing",
    domain: "network",
    title: "Định tuyến gói tin",
    interactionMode: "progressive",
    // M8: module ĐẦU TIÊN khai 3D — topology/chiều sâu là chỗ 3D thêm giá trị
    // biểu diễn thật (COVERAGE.md §8); logic/binary/algorithm CỐ Ý giữ 2D-only.
    supportedVisualModes: ["2d", "3d"],
    // M10: TRUNG THỰC — Z ở đây chỉ tách hàng route/ngoài-route (bố cục), KHÔNG
    // mang nghĩa khái niệm. Đây là PoC kiến trúc, không phải 3D sư phạm.
    threeD: {
      role: "architectural_poc",
      meaningOfZ: "phân tách nút trên/ngoài tuyến (bố cục), không mang nghĩa khái niệm",
    },

    validateConfig: validateNetworkConfig,

    init: buildState,

    apply: (state) => state, // không what-if — điều khiển qua timeline

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
      };
    },

    Workspace: NetworkWorkspace,
    // M8: renderer 3D — CÙNG WorkspaceProps, đọc CÙNG state; "2d" mặc định
    // là Workspace nên không cần khai lại.
    renderers: { "3d": Network3DWorkspace },
    Inspector: NetworkInspector,
  };
}

export function registerNetworkDomain(): void {
  registerSimulation(makeNetworkModule());
}
