import { registerSimulation } from "../../registry";
import type { NetNode, NetworkConfig, NetworkState, NodeType } from "./model";
import { bfsRoute, buildSteps, currentStep, layout } from "./model";
import type { ConfigResult, SimulationModule } from "../../types";
import { NetworkInspector, NetworkWorkspace } from "./ui";

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

function buildState(config: NetworkConfig): NetworkState {
  const ids = config.nodes.map((n) => n.id);
  const byId = Object.fromEntries(config.nodes.map((n) => [n.id, n]));
  const route = bfsRoute(ids, config.links, config.source, config.destination);
  const steps = buildSteps(route, byId);
  const { positions } = layout(config.nodes, route);
  return {
    nodes: config.nodes,
    links: config.links,
    source: config.source,
    destination: config.destination,
    route,
    steps,
    positions,
    cursor: 0,
  };
}

export function makeNetworkModule(): SimulationModule<NetworkConfig, NetworkState> {
  return {
    id: "network.packet_routing",
    domain: "network",
    title: "Định tuyến gói tin",
    interactionMode: "progressive",
    supportedVisualModes: ["2d"],

    validateConfig: validateNetworkConfig,

    init: buildState,

    apply: (state) => state, // không what-if — điều khiển qua timeline

    // Progressive → có timeline capability (M5 §2, §4)
    timeline: {
      stepCount: (s) => s.steps.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: Math.max(0, Math.min(step, s.steps.length - 1)) }),
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
    Inspector: NetworkInspector,
  };
}

export function registerNetworkDomain(): void {
  registerSimulation(makeNetworkModule());
}
