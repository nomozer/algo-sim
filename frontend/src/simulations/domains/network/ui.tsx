import type { WorkspaceProps } from "../../types";
import {
  currentStep,
  layout,
  typeLabel,
  type NetworkConfig,
  type NetworkState,
  type NodeType,
} from "./model";

/**
 * UI domain network — nút + link + chấm gói tin chạy theo bước.
 * Không array/pseudocode (§7): inspector riêng cho node/route/packet.
 */

type Props = WorkspaceProps<NetworkConfig, NetworkState>;

const NODE_COLOR: Record<NodeType, string> = {
  client: "var(--accent-sky)",
  router: "var(--accent-purple)",
  server: "var(--accent-green)",
  switch: "var(--accent-teal)",
  isp: "var(--accent-orange)",
};

const NODE_R = 30;

export function NetworkWorkspace({ state }: Props) {
  const { width, height } = layout(state.nodes, state.route);
  const step = currentStep(state);
  const pos = state.positions;
  const packetPos = pos[step.packetAt];
  const onRoute = new Set(state.route);

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div className="sim-stage">
        <svg viewBox={`0 0 ${width} ${height}`} width="100%" style={{ maxWidth: width, display: "block", margin: "0 auto" }}>
          {/* Liên kết */}
          {state.links.map(([a, b], i) => {
            const routeEdge =
              onRoute.has(a) && onRoute.has(b) &&
              Math.abs(state.route.indexOf(a) - state.route.indexOf(b)) === 1;
            return (
              <line
                key={i}
                x1={pos[a].x}
                y1={pos[a].y}
                x2={pos[b].x}
                y2={pos[b].y}
                stroke={routeEdge ? "var(--primary)" : "var(--hairline)"}
                strokeWidth={routeEdge ? 3 : 1.5}
              />
            );
          })}
          {/* Nút */}
          {state.nodes.map((n) => {
            const p = pos[n.id];
            const isEnd = n.id === state.source || n.id === state.destination;
            return (
              <g key={n.id}>
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={NODE_R}
                  fill="var(--surface)"
                  stroke={NODE_COLOR[n.type]}
                  strokeWidth={isEnd ? 3.5 : 2}
                />
                <text x={p.x} y={p.y - 2} textAnchor="middle" fontSize={11} fontWeight={600} fill="var(--ink)">
                  {n.id}
                </text>
                <text x={p.x} y={p.y + 11} textAnchor="middle" fontSize={9} fill="var(--ink-muted)">
                  {typeLabel(n.type)}
                </text>
              </g>
            );
          })}
          {/* Gói tin */}
          <circle
            cx={packetPos.x}
            cy={packetPos.y - NODE_R - 10}
            r={9}
            fill="var(--accent-pink)"
            stroke="#fff"
            strokeWidth={2}
            style={{ transition: "cx 0.4s ease, cy 0.4s ease" }}
          />
        </svg>
      </div>
      <div className="narration-bar">{step.narration}</div>
    </div>
  );
}

export function NetworkInspector({ state }: Props) {
  const step = currentStep(state);
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <section className="card" style={{ padding: "var(--sp-md)" }}>
        <span className="eyebrow">GÓI TIN</span>
        <div className="analysis-grid" style={{ marginTop: "var(--sp-sm)" }}>
          <span className="analysis-label">Nguồn</span>
          <span>{state.source}</span>
          <span className="analysis-label">Đích</span>
          <span>{state.destination}</span>
          <span className="analysis-label">Đang ở</span>
          <span>
            <strong>{step.packetAt}</strong>
          </span>
          <span className="analysis-label">Đường đi</span>
          <span>{state.route.join(" → ")}</span>
          <span className="analysis-label">Bước</span>
          <span>
            {state.cursor + 1} / {state.steps.length}
          </span>
        </div>
      </section>
    </div>
  );
}
