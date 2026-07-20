import type { WorkspaceProps } from "../../types";
import {
  currentStep,
  typeLabel,
  type NetNode,
  type NetworkConfig,
  type NetworkState,
  type NodeType,
} from "./model";

/**
 * UI domain network — nút + link + chấm gói tin chạy theo bước.
 * Không array/pseudocode (§7): inspector riêng cho node/route/packet.
 *
 * M7.FREEZE: BỐ CỤC thuộc renderer, không thuộc engine state. `layout2d` dưới
 * đây là chi tiết trình bày của renderer 2D (toạ độ pixel SVG); một renderer 3D
 * sẽ có bố cục riêng và dùng lại NGUYÊN state (topology + route + packetAt).
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

interface Pos2D {
  x: number;
  y: number;
}

/** Bố trí 2D: nút trên route xếp hàng ngang, nút ngoài route xếp hàng dưới.
 *  Export để test totality/parity với `layout3d` (bố cục renderer-owned). */
export function layout2d(
  nodes: NetNode[],
  route: string[],
): { positions: Record<string, Pos2D>; width: number; height: number } {
  const COL = 150;
  const X0 = 80;
  const positions: Record<string, Pos2D> = {};
  route.forEach((id, i) => {
    positions[id] = { x: X0 + i * COL, y: 70 };
  });
  const off = nodes.filter((n) => !route.includes(n.id));
  off.forEach((n, i) => {
    positions[n.id] = { x: X0 + i * COL, y: 190 };
  });
  const cols = Math.max(route.length, off.length, 1);
  return { positions, width: X0 * 2 + (cols - 1) * COL, height: off.length ? 250 : 140 };
}

export function NetworkWorkspace({ state }: Props) {
  const { positions: pos, width, height } = layout2d(state.nodes, state.route);
  const step = currentStep(state);
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
