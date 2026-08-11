import { useEffect, useRef, useState } from "react";
import type { WorkspaceProps } from "../../types";
import { routeEdgeViews, type EdgeStatus } from "./edge-view";
import { GLYPH_BOX, endpointRoleOf, nodeGlyph } from "./node-glyph";
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
import { useAppStore } from "../../../state/store";

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
/* W4B-2T — BỀ RỘNG CỘT THÍCH ỨNG, dùng lại khuôn `arrayChartLayout` (W4B-2A).
 *
 * Đo được: topology dựng đúng 610px bất kể sân khấu rộng bao nhiêu (mức dùng bề
 * ngang 37.6% ở 1920). Họ mảng đã giải bài này từ W4B-2A bằng "suy bề rộng từ
 * chỗ THẬT SỰ có, kẹp giữa MIN và MAX"; network thì chưa — nó là renderer duy
 * nhất còn tự khai một hằng số pixel. Đây là ÁP LẠI khuôn đã có, không phải
 * khuôn mới, và MAX giữ cho thiết bị không phình to lố (§7).
 */
const COL_MIN = 150;
const COL_MAX = 240;

export function layout2d(
  nodes: NetNode[],
  route: string[],
  available = 0,
): { positions: Record<string, Pos2D>; width: number; height: number } {
  const X0 = 80;
  const cols0 = Math.max(route.length, nodes.filter((n) => !route.includes(n.id)).length, 1);
  // Bề rộng cần cho `cols0` cột ở khoảng cách `c`: X0*2 + (cols0-1)*c.
  const fit = cols0 > 1 ? (available - X0 * 2) / (cols0 - 1) : COL_MIN;
  const COL = available > 0
    ? Math.max(COL_MIN, Math.min(COL_MAX, Math.floor(fit)))
    : COL_MIN;
  const positions: Record<string, Pos2D> = {};
  route.forEach((id, i) => {
    positions[id] = { x: X0 + i * COL, y: 70 };
  });
  const off = nodes.filter((n) => !route.includes(n.id));
  off.forEach((n, i) => {
    positions[n.id] = { x: X0 + i * COL, y: 190 };
  });
  const cols = Math.max(route.length, off.length, 1);
  /* W4B-2S: thiết bị nay là hình có nhãn nằm DƯỚI (tới y+66 kể từ tâm), thay vì
     hình tròn có chữ bên trong. Chiều cao cũ 140/250 cắt mất dòng loại thiết bị
     ở hàng cuối — đo được trong Chrome, không suy từ code. */
  return { positions, width: X0 * 2 + (cols - 1) * COL, height: off.length ? 270 : 160 };
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
  /* Đo bề rộng từ CHÍNH khung chứa (không phải `window.innerWidth`): sân khấu co
     theo panel Giải thích mở/đóng chứ không theo cửa sổ. Cùng khuôn ArrayView. */
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

  const { positions: pos, width, height } = layout2d(state.nodes, state.route, available);
  const step = currentStep(state);
  const packetPos = pos[step.packetAt];
  const edgeViews = routeEdgeViews(state.links, state.route, state.cursor);

  /* W4B-3A — CHẾ ĐỘ KHÁM PHÁ, do shell sở hữu.
   *
   * Ở bài này cổng gác đúng MỘT việc: sửa tôpô (ngắt/nối liên kết) rồi để engine
   * định tuyến lại. Không có `predict.check` nào can dự — nên nó là KHÁM PHÁ,
   * không phải Thử thách. Bài này CÓ `predict` riêng ("chặng kế tiếp là nút
   * nào?") và lối vào đó là một nút KHÁC, cũng ở dải hành động phụ.
   *
   * Trước wave này cờ là `useState` cục bộ tên `labOpen` và nút mở nó nằm ngay
   * dưới sân khấu — đo được là dải `experimentTrigger` (bandCount 2 ở
   * `network.packet_routing`, cả bốn bề rộng). */
  const exploreOpen = useAppStore((s) => s.exploreOpen);
  const setExploreOpen = useAppStore((s) => s.setExploreOpen);
  const gone = removedLinks(state);
  const modified = isModified(state);
  const editable = exploreOpen && !busy;

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
      <div className="sim-stage" ref={boxRef}>
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
          {/* THIẾT BỊ — hình dạng theo VAI TRÒ do engine khai (`n.type`), không
              phải theo nhãn/đề bài. Chữ nằm DƯỚI hình và chỉ xác nhận danh tính. */}
          {state.nodes.map((n) => {
            const p = pos[n.id];
            const glyph = nodeGlyph(n.type);
            const endpoint = endpointRoleOf(n.id, state.source, state.destination);
            const color = NODE_COLOR[n.type];
            // Hộp glyph 48×48 → đường kính nút; đặt tâm glyph trùng tâm nút.
            const k = (NODE_R * 2) / GLYPH_BOX;
            const gx = p.x - NODE_R;
            const gy = p.y - NODE_R;
            return (
              <g key={n.id}>
                <title>{`${glyph.role} (${n.id})${
                  endpoint === "source" ? " — nguồn"
                  : endpoint === "destination" ? " — đích" : ""}`}</title>

                {/* Dấu hiệu NGUỒN/ĐÍCH: vai trò trong phiên truyền, tách khỏi loại
                    thiết bị (một mạng có thể có hai máy chủ). Đích = vòng ngắm
                    kép; nguồn = cung phát. Hình khác nhau, không chỉ khác màu. */}
                {endpoint === "destination" && (
                  <>
                    <circle cx={p.x} cy={p.y} r={NODE_R + 7} fill="none"
                      stroke="var(--primary)" strokeWidth={2} />
                    <circle cx={p.x} cy={p.y} r={NODE_R + 11} fill="none"
                      stroke="var(--primary)" strokeWidth={1} strokeDasharray="3 4" />
                  </>
                )}
                {endpoint === "source" && (
                  <path
                    d={`M ${p.x - NODE_R - 6} ${p.y + 8} a ${NODE_R + 6} ${NODE_R + 6} 0 0 1 0 -16`}
                    fill="none" stroke={color} strokeWidth={2.5} strokeLinecap="round"
                  />
                )}

                <g transform={`translate(${gx} ${gy}) scale(${k})`}>
                  <path d={glyph.outline} fill="var(--surface)" stroke={color}
                    strokeWidth={2.2 / k} strokeLinejoin="round" />
                  {glyph.details.map((d, i) => (
                    <path key={i} d={d} fill="none" stroke={color}
                      strokeWidth={1.8 / k} strokeLinecap="round" strokeLinejoin="round" />
                  ))}
                </g>

                {/* Chữ XÁC NHẬN hình, không thay hình — nên nằm ngoài, dưới thiết bị.
                    Lùi qua KHỎI vòng ngắm đích (bán kính ngoài NODE_R + 11): ảnh
                    lượt chụp đầu cho thấy nhãn "server" dính vào vòng ngắm, tức
                    hai tín hiệu đè nhau đúng ở nút quan trọng nhất. */}
                <text x={p.x} y={p.y + NODE_R + 24} textAnchor="middle"
                  fontSize={11} fontWeight={600} fill="var(--ink)">
                  {n.id}
                </text>
                <text x={p.x} y={p.y + NODE_R + 36} textAnchor="middle"
                  fontSize={9} fill="var(--ink-muted)">
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

      {/* W4B-3A — CỔNG ĐÃ RỜI KHỎI ĐÂY, sang dải hành động phụ của
          `SimulationControls`. Câu mời ("tự đổi đường mạng" + teaser đứt cáp)
          nay do module khai ở `explore.entry`, nên nó vẫn là câu của bài này —
          chỉ không còn chiếm một dải riêng ngay dưới sân khấu. */}
      {exploreOpen && (
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
            onClick={() => setExploreOpen(false)}
            aria-label="Đóng khám phá"
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
