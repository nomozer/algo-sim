import type { WorkspaceProps } from "../../types";
import {
  STRUCTURAL_TYPES,
  childrenOf,
  currentFrame,
  inspectorGroups,
  isObjectRenderable,
  objectRole,
  positionOf,
  structuralRoots,
  valuesOf,
  type GenericState,
  type ObjectRole,
  type SimulationSpec,
  type SpecObject,
} from "./model";

/**
 * Renderer 2D tổng quát — vẽ theo primitive của SimulationSpec đã validate.
 * Chỉ ĐỌC spec + state; toggle phát qua dispatch; KHÔNG business logic.
 * Trạng thái hiển thị (current/completed/hidden) do engine quyết định qua
 * objectRole — renderer chỉ ánh xạ trạng thái → style (M7.10). Dùng lại cho 3D.
 */

type Props = WorkspaceProps<SimulationSpec, GenericState>;

const VW = 600;
const VH = 340;
const px = (nx: number) => (nx / 100) * VW;
const py = (ny: number) => (ny / 100) * VH;

const NODE_COLOR: Record<string, string> = {
  client: "var(--accent-sky)",
  router: "var(--accent-purple)",
  server: "var(--accent-green)",
  switch: "var(--accent-teal)",
  isp: "var(--accent-orange)",
};

/** node không có node_type → coi là "điểm" (geometry); có node_type → nút mạng. */
function isPoint(o: SpecObject): boolean {
  return o.type === "node" && !o.node_type;
}

/* ── Structural/textual flow (M7.12) — bố cục tài liệu theo chiều dọc ── */

/** Ngắt chữ thành nhiều dòng theo số ký tự tối đa/dòng (SVG không tự wrap). */
function wrapText(text: string, maxChars: number): string[] {
  const words = (text ?? "").split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let cur = "";
  for (const w of words) {
    const next = cur ? `${cur} ${w}` : w;
    if (next.length > maxChars && cur) {
      lines.push(cur);
      cur = w;
    } else {
      cur = next;
    }
  }
  if (cur) lines.push(cur);
  return lines.length ? lines : [""];
}

/** Ước lượng số ký tự vừa một dòng theo bề rộng + cỡ chữ. */
function charsPerLine(width: number, fontSize: number): number {
  return Math.max(6, Math.floor(width / (fontSize * 0.56)));
}

const FLOW_MARGIN = 16;
const FLOW_GAP = 10;

export function GenericWorkspace({ config: spec, state, dispatch }: Props) {
  const values = valuesOf(spec, state.base);
  const frame = currentFrame(state);
  const toggleable = new Set(Object.keys(state.base));

  const pos: Record<string, { x: number; y: number }> = {};
  spec.objects.forEach((o, i) => {
    const p = positionOf(o, i);
    pos[o.id] = { x: px(p.x), y: py(p.y) };
  });

  // M7.12: bố cục tài liệu (container/heading/paragraph/text) — layout dọc đệ quy,
  // container vẽ khung TRƯỚC (sau đó tới con) để đúng thứ tự z. Vai trò hiển thị
  // (current/…) do engine quyết định qua objectRole — renderer chỉ ánh xạ style.
  function laidOutNode(obj: SpecObject, x: number, y: number, width: number): { height: number; els: React.ReactElement[] } {
    const current = objectRole(state, obj.id) === "current";
    const pop = current ? "gen-pop" : undefined;

    if (obj.type === "heading") {
      const fs = 18;
      const lines = wrapText(obj.text ?? "", charsPerLine(width, fs));
      const els = lines.map((ln, i) => (
        <text key={`${obj.id}-${i}`} className={pop} x={x} y={y + 18 + i * 24} fontSize={fs} fontWeight={700} fill="var(--ink)">{ln}</text>
      ));
      return { height: lines.length * 24 + 6, els };
    }
    if (obj.type === "paragraph" || obj.type === "text") {
      const fs = 14;
      const lines = wrapText(obj.text ?? "", charsPerLine(width, fs));
      const els = lines.map((ln, i) => (
        <text key={`${obj.id}-${i}`} className={pop} x={x} y={y + 13 + i * 19} fontSize={fs} fill="var(--ink-secondary)">{ln}</text>
      ));
      return { height: lines.length * 19 + 6, els };
    }
    // container | group — khung chứa các con (childrenOf theo parent)
    const isContainer = obj.type === "container";
    const PAD = isContainer ? 14 : 8;
    const kids = childrenOf(spec, obj.id).filter((k) => isObjectRenderable(frame, k));
    const childEls: React.ReactElement[] = [];
    let cursor = y + PAD;
    if (obj.text) {
      childEls.push(
        <text key={`${obj.id}-title`} className={pop} x={x + PAD} y={cursor + 15} fontSize={15} fontWeight={700} fill="var(--ink)">{obj.text}</text>,
      );
      cursor += 24;
    }
    for (const kid of kids) {
      const r = laidOutNode(kid, x + PAD, cursor, width - 2 * PAD);
      childEls.push(...r.els);
      cursor += r.height + FLOW_GAP;
    }
    const height = Math.max(cursor - (kids.length ? FLOW_GAP : 0) + PAD - y, isContainer ? 34 : 24);
    const box = isContainer ? (
      <rect key={`${obj.id}-box`} className={pop} x={x} y={y} width={width} height={height} rx={10} fill="var(--surface)" stroke={current ? "var(--primary)" : "var(--ink-faint)"} strokeWidth={current ? 2.5 : 1.5} />
    ) : (
      <rect key={`${obj.id}-box`} x={x} y={y} width={width} height={height} rx={6} fill="var(--canvas-soft)" stroke="none" />
    );
    return { height, els: [box, ...childEls] };
  }

  const structuralRootsVisible = structuralRoots(spec).filter((o) => isObjectRenderable(frame, o));
  const structuralEls: React.ReactElement[] = [];
  let flowY = FLOW_MARGIN;
  for (const root of structuralRootsVisible) {
    const r = laidOutNode(root, FLOW_MARGIN, flowY, VW - FLOW_MARGIN * 2);
    structuralEls.push(...r.els);
    flowY += r.height + FLOW_GAP;
  }
  const hasStructural = structuralRootsVisible.length > 0;
  const svgH = hasStructural ? Math.max(VH, flowY + FLOW_MARGIN) : VH;

  function renderObject(o: SpecObject, role: ObjectRole) {
    const p = pos[o.id];
    const v = values[o.id] ?? 0;
    const current = role === "current";
    const popCls = current ? "gen-pop" : undefined;

    switch (o.type) {
      case "switch": {
        const on = v >= 1;
        const clickable = toggleable.has(o.id);
        return (
          <g key={o.id} className={popCls} style={{ cursor: clickable ? "pointer" : "default" }} onClick={() => clickable && dispatch({ type: "toggle", target: o.id })}>
            {o.label && (
              <text x={p.x} y={p.y - 28} textAnchor="middle" fontSize={13} fontWeight={600} fill="var(--ink-secondary)">
                {o.label}
              </text>
            )}
            <rect x={p.x - 30} y={p.y - 17} width={60} height={34} rx={17} fill={on ? "var(--primary)" : "var(--canvas-soft)"} stroke={on ? "var(--primary)" : "var(--ink-faint)"} strokeWidth={2} style={{ transition: "fill 0.15s ease" }} />
            <circle cx={p.x + (on ? 13 : -13)} cy={p.y} r={13} fill="#fff" style={{ transition: "cx 0.15s ease" }} />
            <text x={p.x + (on ? -14 : 14)} y={p.y + 5} textAnchor="middle" fontSize={13} fontWeight={700} fill={on ? "#fff" : "var(--ink-muted)"}>
              {v}
            </text>
          </g>
        );
      }
      case "lamp": {
        const on = v >= 1;
        return (
          <g key={o.id} className={popCls}>
            {o.label && (
              <text x={p.x} y={p.y + 44} textAnchor="middle" fontSize={12} fill="var(--ink-secondary)">
                {o.label}
              </text>
            )}
            <circle cx={p.x} cy={p.y} r={26} fill={on ? "var(--accent-green)" : "var(--canvas-soft)"} stroke={on ? "var(--accent-green)" : "var(--ink-faint)"} strokeWidth={current ? 3.5 : 2} style={{ transition: "fill 0.2s ease" }} />
            <text x={p.x} y={p.y + 6} textAnchor="middle" fontSize={18} fontWeight={700} fill={on ? "#fff" : "var(--ink-muted)"}>
              {v}
            </text>
          </g>
        );
      }
      case "value_box":
        return (
          <g key={o.id} className={popCls}>
            {o.label && (
              <text x={p.x} y={p.y - 26} textAnchor="middle" fontSize={12} fill="var(--ink-secondary)">
                {o.label}
              </text>
            )}
            <rect x={p.x - 34} y={p.y - 20} width={68} height={40} rx={8} fill="var(--surface)" stroke="var(--primary)" strokeWidth={current ? 3 : 2} />
            <text x={p.x} y={p.y + 7} textAnchor="middle" fontSize={20} fontWeight={700} fill="var(--ink)">
              {v}
            </text>
          </g>
        );
      case "node": {
        if (isPoint(o)) {
          // ĐIỂM (hình học): marker tròn rõ + nhãn lệch khỏi marker
          const r = current ? 8 : 6;
          const fill = current ? "var(--primary)" : "var(--ink)";
          return (
            <g key={o.id} className={popCls}>
              <circle cx={p.x} cy={p.y} r={r} fill={fill} stroke="#fff" strokeWidth={2} className={current ? "gen-glow" : undefined} />
              <text x={p.x + 11} y={p.y - 9} fontSize={15} fontWeight={700} fill="var(--ink)">
                {o.label ?? o.id}
              </text>
            </g>
          );
        }
        // NÚT MẠNG (có node_type)
        const color = NODE_COLOR[o.node_type ?? ""] ?? "var(--primary)";
        return (
          <g key={o.id} className={popCls}>
            <circle cx={p.x} cy={p.y} r={26} fill="var(--surface)" stroke={color} strokeWidth={current ? 4 : 2.5} className={current ? "gen-glow" : undefined} />
            <text x={p.x} y={p.y - 1} textAnchor="middle" fontSize={11} fontWeight={600} fill="var(--ink)">
              {o.label ?? o.id}
            </text>
            {o.node_type && (
              <text x={p.x} y={p.y + 11} textAnchor="middle" fontSize={9} fill="var(--ink-muted)">
                {o.node_type}
              </text>
            )}
          </g>
        );
      }
      case "label":
        return (
          <text key={o.id} className={popCls} x={p.x} y={p.y} textAnchor="middle" fontSize={14} fontWeight={current ? 700 : 400} fill="var(--ink-secondary)">
            {o.label ?? ""}
          </text>
        );
      default:
        return null;
    }
  }

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div className="sim-stage">
        <svg viewBox={`0 0 ${VW} ${svgH}`} width="100%" style={{ maxWidth: VW, display: "block", margin: "0 auto" }}>
          {/* Cạnh (edge) vẽ trước; chỉ khi edge + hai đầu đều visible (§6) */}
          {spec.objects
            .filter((o) => o.type === "edge" && isObjectRenderable(frame, o))
            .map((o) => {
              const a = pos[o.from ?? ""];
              const b = pos[o.to ?? ""];
              if (!a || !b) return null;
              const current = objectRole(state, o.id) === "current";
              const len = Math.hypot(b.x - a.x, b.y - a.y);
              return (
                <line
                  key={o.id}
                  x1={a.x}
                  y1={a.y}
                  x2={b.x}
                  y2={b.y}
                  stroke={current ? "var(--primary)" : "var(--ink-secondary)"}
                  strokeWidth={current ? 4 : 2.5}
                  strokeLinecap="round"
                  className={current ? "gen-edge-draw" : undefined}
                  style={current ? ({ ["--len" as string]: len, strokeDasharray: len } as React.CSSProperties) : undefined}
                />
              );
            })}
          {/* Object thường (legacy spatial) — trừ họ cấu trúc (render theo luồng riêng) */}
          {spec.objects
            .filter(
              (o) =>
                o.type !== "edge" &&
                o.type !== "moving_entity" &&
                !STRUCTURAL_TYPES.has(o.type) &&
                isObjectRenderable(frame, o),
            )
            .map((o) => renderObject(o, objectRole(state, o.id)))}
          {/* Họ cấu trúc/nội dung (M7.12): container/heading/paragraph/text theo luồng dọc */}
          {structuralEls}
          {/* Thực thể di chuyển (packet) trên cùng */}
          {spec.objects
            .filter((o) => o.type === "moving_entity" && isObjectRenderable(frame, o))
            .map((o) => {
              const nodeId = frame.entityPos[o.id];
              const np = nodeId ? pos[nodeId] : undefined;
              if (!np) return null;
              return (
                <circle key={o.id} cx={np.x} cy={np.y - 38} r={9} fill="var(--accent-pink)" stroke="#fff" strokeWidth={2} style={{ transition: "cx 0.4s ease, cy 0.4s ease" }} />
              );
            })}
        </svg>
      </div>
      <div className="narration-bar">
        {state.timeline.length > 1
          ? frame.narration
          : toggleable.size > 0
            ? "Bấm vào các công tắc để thay đổi trạng thái và quan sát kết quả."
            : spec.title}
      </div>
    </div>
  );
}

const TYPE_LABEL: Record<string, string> = {
  node: "điểm/nút",
  edge: "đoạn/cạnh",
  switch: "công tắc",
  lamp: "đèn",
  value_box: "ô giá trị",
  moving_entity: "vật di chuyển",
  label: "nhãn",
  container: "khung chứa",
  group: "nhóm",
  heading: "tiêu đề",
  paragraph: "đoạn văn",
  text: "chữ",
};

/** Tên hiển thị của object trong inspector: nhãn > nội dung chữ (rút gọn) > id. */
function chipName(o: SpecObject): string {
  if (o.label) return o.label;
  if (o.text) return o.text.length > 32 ? `${o.text.slice(0, 32)}…` : o.text;
  return o.id;
}

function ObjChips({ objs }: { objs: SpecObject[] }) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
      {objs.map((o) => (
        <span key={o.id} className="obj-chip">
          {chipName(o)}
          <span className="obj-chip-type">{TYPE_LABEL[o.type] ?? o.type}</span>
        </span>
      ))}
    </div>
  );
}

export function GenericInspector({ config: spec, state }: Props) {
  const values = valuesOf(spec, state.base);
  const groups = inspectorGroups(state);
  const progressive = state.timeline.length > 1;
  const withValue = spec.objects.filter((o) => o.value !== undefined || o.type === "lamp" || o.type === "value_box");

  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <section className="card" style={{ padding: "var(--sp-md)" }}>
        <span className="eyebrow">ĐỐI TƯỢNG</span>
        {progressive ? (
          <div className="stack" style={{ gap: "var(--sp-sm)", marginTop: "var(--sp-sm)" }}>
            {groups.current.length > 0 && (
              <div>
                <span className="obj-group-label" style={{ color: "var(--primary)" }}>Vừa tạo</span>
                <ObjChips objs={groups.current} />
              </div>
            )}
            {groups.completed.length > 0 && (
              <div>
                <span className="obj-group-label">Đã hiện</span>
                <ObjChips objs={groups.completed} />
              </div>
            )}
            {groups.hidden.length > 0 && (
              <div>
                <span className="obj-group-label" style={{ color: "var(--ink-faint)" }}>Chưa xuất hiện</span>
                <ObjChips objs={groups.hidden} />
              </div>
            )}
          </div>
        ) : withValue.length > 0 ? (
          <div className="analysis-grid" style={{ marginTop: "var(--sp-sm)" }}>
            {withValue.map((o) => (
              <FragmentRow key={o.id} label={o.label ?? o.id} value={values[o.id] ?? 0} />
            ))}
          </div>
        ) : (
          <div style={{ marginTop: "var(--sp-sm)" }}>
            <ObjChips objs={spec.objects} />
          </div>
        )}
      </section>

      {spec.rules.length > 0 && (
        <section className="card" style={{ padding: "var(--sp-md)" }}>
          <span className="eyebrow">QUY TẮC</span>
          <ul style={{ margin: "var(--sp-xs) 0 0 var(--sp-md)", fontSize: 14, color: "var(--ink-secondary)" }}>
            {spec.rules.map((r, i) => (
              <li key={i}>
                {r.target} = {r.type === "boolean" ? `${r.op?.toUpperCase()}(${(r.inputs ?? []).join(", ")})` : `Σ(${(r.inputs ?? []).join(", ")} × trọng số)`}
              </li>
            ))}
          </ul>
        </section>
      )}

      {progressive && (
        <section className="card" style={{ padding: "var(--sp-md)" }}>
          <span className="eyebrow">TIẾN TRÌNH</span>
          <p style={{ marginTop: "var(--sp-xs)", fontSize: 14 }}>
            Bước {state.cursor + 1} / {state.timeline.length}
          </p>
          <p className="hint">{currentFrame(state).narration}</p>
        </section>
      )}
    </div>
  );
}

function FragmentRow({ label, value }: { label: string; value: number }) {
  return (
    <>
      <span className="analysis-label">{label}</span>
      <span>
        <strong>{value}</strong>
      </span>
    </>
  );
}
