import { useState } from "react";
import type { WorkspaceProps } from "../../types";
import { routeEdgeViews, type EdgeStatus } from "./edge-view";
import {
  currentStep,
  isModified,
  isReachable,
  typeLabel,
  type NetNode,
  type NetworkConfig,
  type NetworkState,
  type NodeType,
} from "./model";
import { IconExperiment, IconReset } from "../../../components/icons";

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

/**
 * Hai kênh tín hiệu cho mỗi trạng thái (DESIGN_BRIEF §3.5): màu + độ dày, và
 * đoạn chưa tới thêm nét đứt. Dùng CHUNG từ vựng `EdgeStatus` với duyệt đồ thị
 * nhưng bảng màu riêng — `packet_routing` không có trạng thái "đang cân nhắc".
 */
const ROUTE_EDGE_STYLE: Record<EdgeStatus, { stroke: string; width: number; dash?: string }> = {
  idle: { stroke: "var(--hairline)", width: 1.5 },
  considering: { stroke: "var(--hairline)", width: 1.5 }, // không dùng ở đây
  active: { stroke: "var(--accent-orange)", width: 4.5 },
  traversed: { stroke: "var(--primary)", width: 3 },
  remaining: { stroke: "var(--ink-faint)", width: 2, dash: "6 5" },
};

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

/**
 * W4B-2I — LIÊN KẾT ĐÃ NGẮT, vẽ mờ để còn NỐI LẠI được.
 *
 * Dẫn xuất từ `baseline.links \ links`; KHÔNG thêm trường nào vào state. Không
 * có nó thì ngắt là thao tác một chiều: học sinh chỉ còn đường "Về ban đầu", tức
 * không so sánh được hai cấu hình cạnh nhau — mà so sánh mới là chỗ có bài học.
 */
function removedLinks(state: NetworkState): [string, string][] {
  const key = (a: string, b: string) => (a < b ? `${a}~${b}` : `${b}~${a}`);
  const live = new Set(state.links.map(([a, b]) => key(a, b)));
  return state.baseline.links.filter(([a, b]) => !live.has(key(a, b)));
}

export function NetworkWorkspace({ state, busy, dispatch }: Props) {
  const { positions: pos, width, height } = layout2d(state.nodes, state.route);
  const step = currentStep(state);
  const packetPos = pos[step.packetAt];
  const edgeViews = routeEdgeViews(state.links, state.route, state.cursor);

  /* Cùng khuôn cổng với họ thuật toán: Quan sát chỉ có mô phỏng, công cụ do học
     sinh CHỦ ĐỘNG mở. `labOpen` là trạng thái TRÌNH BÀY cục bộ — không vào store,
     không vào engine state. */
  const [labOpen, setLabOpen] = useState(false);
  const gone = removedLinks(state);
  const modified = isModified(state);
  const editable = labOpen && !busy;

  /** Một liên kết bấm được. `onAct` chỉ PHÁT action — engine tính lại, không phải đây. */
  const LinkHandle = ({ a, b, label, onAct }: {
    a: string; b: string; label: string; onAct: () => void;
  }) => (
    <g
      className="net-link-handle"
      role="button"
      tabIndex={0}
      aria-label={label}
      onClick={onAct}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          e.stopPropagation(); // Space cũng là phím tắt Tự chạy toàn cục.
          onAct();
        }
      }}
      style={{ cursor: "pointer" }}
    >
      <title>{label}</title>
      <line
        x1={pos[a].x} y1={pos[a].y} x2={pos[b].x} y2={pos[b].y}
        stroke="transparent" strokeWidth={18} strokeLinecap="round"
      />
    </g>
  );

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div className="sim-stage">
        <svg viewBox={`0 0 ${width} ${height}`} width="100%" style={{ maxWidth: width, display: "block", margin: "0 auto" }}>
          {/* Liên kết — trạng thái theo TIẾN TRÌNH gói tin, không phải tĩnh.
              Trước W4B-1B mọi cạnh trên tuyến tô như nhau ở MỌI bước, nên bước
              1 và bước cuối vẽ giống hệt: học sinh không thấy đoạn nào đã đi,
              đoạn nào còn lại — mà đó chính là nội dung bài. Dẫn xuất thuần từ
              `route` + `cursor`, KHÔNG thêm trường nào vào state. */}
          {edgeViews.map((ev, i) => {
            const st = ROUTE_EDGE_STYLE[ev.status];
            return (
              <line
                key={i}
                x1={pos[ev.from].x}
                y1={pos[ev.from].y}
                x2={pos[ev.to].x}
                y2={pos[ev.to].y}
                stroke={st.stroke}
                strokeWidth={st.width}
                strokeDasharray={st.dash}
                strokeLinecap="round"
              >
                <title>{ev.accessibleLabel}</title>
              </line>
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
          {/* LIÊN KẾT ĐÃ NGẮT — vẽ mờ, nét đứt; chỉ hiện khi có. */}
          {gone.map(([a, b]) => (
            <line
              key={`gone-${a}-${b}`}
              x1={pos[a].x} y1={pos[a].y} x2={pos[b].x} y2={pos[b].y}
              stroke="var(--ink-faint)" strokeWidth={1.5}
              strokeDasharray="3 6" opacity={0.55}
            />
          ))}
          {/* Gói tin — KHÔNG vẽ khi không có đường đi: một chấm đứng im ở nguồn
              đọc thành "gói tin đang chờ", trong khi sự thật là nó không đi được. */}
          {isReachable(state) && (
            <circle
              cx={packetPos.x}
              cy={packetPos.y - NODE_R - 10}
              r={9}
              fill="var(--accent-pink)"
              stroke="#fff"
              strokeWidth={2}
              style={{ transition: "cx 0.4s ease, cy 0.4s ease" }}
            />
          )}

          {/* VÙNG BẤM — vẽ SAU cùng để nằm trên trong thứ tự hit-test. Chỉ dựng
              khi công cụ đang mở: ở Quan sát sân khấu không được bấm được. */}
          {editable && state.links.map(([a, b]) => (
            <LinkHandle
              key={`cut-${a}-${b}`} a={a} b={b}
              label={`Ngắt liên kết ${a} — ${b}`}
              onAct={() => dispatch({ type: "net_disconnect", a, b })}
            />
          ))}
          {editable && gone.map(([a, b]) => (
            <LinkHandle
              key={`join-${a}-${b}`} a={a} b={b}
              label={`Nối lại liên kết ${a} — ${b}`}
              onAct={() => dispatch({ type: "net_connect", a, b })}
            />
          ))}
        </svg>
      </div>

      {/* KHÔNG dựng thêm một dải "không có đường đi" ở đây.
          Ảnh `B3-network-disconnected-unreachable.png` của chính wave này bắt
          được: dải đó và khe thuyết minh nói CÙNG một điều, ngay cạnh nhau —
          đúng loại trùng lặp W4B-2V đã gỡ ở họ tìm kiếm. Chủ sở hữu của câu
          "gói tin không đi được" là `narrate()` (SHELL-N: một khe chữ cho mỗi
          bước); trạng thái không-tới-được đọc được trên SÂN KHẤU bằng liên kết
          nét đứt + vắng chấm gói tin. */}

      {/* CỔNG THÍ NGHIỆM — cùng khuôn với họ thuật toán. */}
      {!labOpen && (
        <button
          className="btn-utility experiment-trigger"
          onClick={() => setLabOpen(true)}
          title="Mạng thật vẫn đứt cáp — thử xem gói tin có đường khác để đi không."
          aria-expanded={false}
        >
          <IconExperiment size={14} />
          Thí nghiệm: tự đổi đường mạng
        </button>
      )}
      {labOpen && (
        <div className="experiment-tool" role="group" aria-label="Thí nghiệm với đường mạng">
          <IconExperiment size={14} />
          <span className="scene-bound-note">
            Bấm vào một liên kết trên sân khấu để ngắt hoặc nối lại.
          </span>
          {modified && (
            <button
              className="btn-utility"
              onClick={() => dispatch({ type: "net_reset" })}
            >
              <IconReset size={13} />
              Về mạng ban đầu
            </button>
          )}
          <button
            className="btn-utility experiment-tool-close"
            onClick={() => setLabOpen(false)}
            aria-label="Đóng thí nghiệm"
            aria-expanded
          >
            ×
          </button>
        </div>
      )}
      {/* (SHELL-N) Thuyết minh do shell dựng — xem `narrate` ở `index.ts`. */}
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
