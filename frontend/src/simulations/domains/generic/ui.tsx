import { useEffect, useRef, useState } from "react";
import { editViaServer } from "../../../llm/client";
import { useAppStore } from "../../../state/store";
import type { WorkspaceProps } from "../../types";
import { EditBar, type EditTool } from "./EditBar";
import { editPolicyOf } from "./edit-policy";
import {
  CONTAINER_TYPES,
  STRUCTURAL_TYPES,
  TEXT_CONTENT_TYPES,
  applyEditedSpec,
  childrenOf,
  currentFrame,
  dragTargets,
  findFreePosition,
  inspectorGroups,
  isObjectRenderable,
  objectRole,
  positionOf,
  structuralRoots,
  valuesOf,
  visibleContentBounds,
  type GenericState,
  type ObjectRole,
  type SimulationSpec,
  type SpecObject,
} from "./model";
import { validateAndApplyPatch, type PatchOp } from "./patch";
import { validateGenericConfig } from "./validate";

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

export function GenericWorkspace({ config: spec, state, busy, dispatch }: Props) {
  const values = valuesOf(spec, state.base);
  const frame = currentFrame(state);
  const toggleable = new Set(Object.keys(state.base));

  // M7.13A: vị trí ĐỌC TỪ STATE (engine sở hữu) — edge/moving_entity tra cùng
  // map nên tự bám theo khi một điểm bị kéo. positionOf chỉ là fallback an toàn.
  const pos: Record<string, { x: number; y: number }> = {};
  spec.objects.forEach((o, i) => {
    const p = state.pos[o.id] ?? positionOf(o, i);
    pos[o.id] = { x: px(p.x), y: py(p.y) };
  });

  const draggable = dragTargets(spec);

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

  /* ── Viewport (M7.14): fit/reset — viewBox là hàm tất định của state ── */
  const [autoFit, setAutoFit] = useState(true);
  const FIT_PAD_X = 56; // px: đủ chứa bán kính node lớn nhất + nhãn
  const FIT_PAD_Y = 48;
  let vb = { x: 0, y: 0, w: VW, h: svgH };
  if (autoFit && !hasStructural) {
    const b = visibleContentBounds(state);
    if (b) {
      const x1 = px(b.minX) - FIT_PAD_X;
      const x2 = px(b.maxX) + FIT_PAD_X;
      const y1 = py(b.minY) - FIT_PAD_Y;
      const y2 = py(b.maxY) + FIT_PAD_Y;
      // không zoom-in quá sát (khung ≥ 60% mặc định); zoom-out tự do khi tràn
      const w = Math.max(x2 - x1, VW * 0.6);
      const h = Math.max(y2 - y1, VH * 0.6);
      vb = { x: (x1 + x2) / 2 - w / 2, y: (y1 + y2) / 2 - h / 2, w, h };
    }
  }

  /* ── Drag (M7.13A) — gesture cục bộ renderer, biến đổi qua dispatch("move");
     domainPoint đọc viewBox HIỆN HÀNH (fit đổi tỉ lệ — M7.14) ── */
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [dragging, setDragging] = useState<string | null>(null);

  function domainPoint(e: React.PointerEvent): { x: number; y: number } | null {
    const svg = svgRef.current;
    if (!svg) return null;
    const rect = svg.getBoundingClientRect();
    if (rect.width <= 0) return null;
    const scale = rect.width / vb.w; // SVG giữ tỉ lệ → cùng scale hai trục
    return {
      x: ((vb.x + (e.clientX - rect.left) / scale) / VW) * 100,
      y: ((vb.y + (e.clientY - rect.top) / scale) / VH) * 100,
    };
  }

  function onDragStart(e: React.PointerEvent<SVGGElement>, id: string) {
    if (busy || editMode || !draggable.has(id)) return;
    e.currentTarget.setPointerCapture?.(e.pointerId);
    setDragging(id);
  }

  function onDragMove(e: React.PointerEvent<SVGGElement>) {
    if (!dragging) return;
    const d = domainPoint(e);
    if (d) dispatch({ type: "move", target: dragging, x: d.x, y: d.y });
  }

  function onDragEnd() {
    setDragging(null);
  }

  /* ── Edit tăng dần (M7.14) + EditPolicy (M7.14D) ─────────────────────────
     MỌI thay đổi cấu trúc đi qua patch → validate (policy + DSL) →
     applyEditedSpec → store.replaceSimulation. UI không tự sửa scene.
     Affordance DẪN XUẤT TỪ SPEC: cảnh văn bản không có Thêm điểm/Nối; cảnh
     giá trị/logic không có công cụ cấu trúc; cảnh có move_along_path khóa topology. */
  const replaceSimulation = useAppStore((s) => s.replaceSimulation);
  const policy = editPolicyOf(spec);
  const [editMode, setEditMode] = useState(false);
  const [editTool, setEditTool] = useState<EditTool>(null);
  const [contentType, setContentType] = useState<string>(policy.addableTypes[0] ?? "paragraph");
  const [connectFrom, setConnectFrom] = useState<string | null>(null);
  const [editBusy, setEditBusy] = useState(false);
  const [editMsg, setEditMsg] = useState<string | null>(null);

  const canEdit = policy.uiActions.some((a) => a !== "edit_text") || policy.allowedOps.length > 0;

  function disarm() {
    setEditTool(null);
    setConnectFrom(null);
    setEditMsg(null);
  }

  // Esc: hủy công cụ đang lên đạn (không thoát chế độ — tránh mất ngữ cảnh)
  useEffect(() => {
    if (!editMode) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") disarm();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [editMode]);

  function applyNewSpec(newSpec: SimulationSpec) {
    replaceSimulation(newSpec, applyEditedSpec(state, newSpec));
  }

  function runLocalPatch(ops: PatchOp[]) {
    const result = validateAndApplyPatch(spec, { operations: ops });
    if (result.status === "valid") {
      applyNewSpec(result.config);
      setEditMsg(null);
    } else {
      setEditMsg(result.error); // kèm reasonCode policy.* / structure.*
    }
  }

  function nextFreeId(prefix: string): string {
    const taken = new Set(spec.objects.map((o) => o.id));
    for (let n = 1; ; n += 1) if (!taken.has(`${prefix}${n}`)) return `${prefix}${n}`;
  }

  function onCanvasClick(e: React.MouseEvent) {
    if (!editMode || editTool !== "add_node" || editBusy) return;
    const d = domainPoint(e as unknown as React.PointerEvent);
    if (!d) return;
    const taken = spec.objects
      .filter((o) => !STRUCTURAL_TYPES.has(o.type) && o.type !== "edge" && state.pos[o.id])
      .map((o) => state.pos[o.id]);
    const p = findFreePosition(taken, d);
    const id = nextFreeId("P");
    runLocalPatch([{ op: "add_object", object: { id, type: "node", label: id, x: p.x, y: p.y } }]);
  }

  /** Thêm một mục nội dung vào cuối cảnh structural (family structural). */
  function addContent() {
    if (editBusy) return;
    const id = nextFreeId(contentType.slice(0, 1).toUpperCase());
    const root = structuralRoots(spec).find((o) => CONTAINER_TYPES.has(o.type));
    const obj: Record<string, unknown> = { id, type: contentType };
    if (TEXT_CONTENT_TYPES.has(contentType)) obj.text = "Nội dung mới — hãy sửa lại cho đúng ý.";
    if (CONTAINER_TYPES.has(contentType)) obj.text = "Khung mới";
    if (root) obj.parent = root.id;
    runLocalPatch([{ op: "add_object", object: obj as PatchOp extends { object: infer O } ? O : never }]);
  }

  function onObjectEditClick(id: string) {
    if (!editMode || editBusy) return;
    if (editTool === "delete") {
      runLocalPatch([{ op: "remove_object", id }]);
      return;
    }
    if (editTool === "connect") {
      if (connectFrom === null) {
        setConnectFrom(id);
        setEditMsg(null); // hướng dẫn "chọn đối tượng thứ hai" do EditBar hiển thị
      } else if (connectFrom !== id) {
        runLocalPatch([{ op: "connect", from: connectFrom, to: id, edge_id: nextFreeId(`${connectFrom}_${id}`) }]);
        setConnectFrom(null);
      }
    }
  }

  function onPickTool(tool: EditTool) {
    setConnectFrom(null);
    setEditMsg(null);
    if (tool === "add_content" && editTool === "add_content") {
      addContent(); // bấm lần hai → chèn ngay
      return;
    }
    setEditTool(tool);
  }

  async function submitNlEdit(instruction: string) {
    setEditBusy(true);
    setEditMsg(null);
    try {
      const res = await editViaServer({ simulationId: "generic.rule_scene", config: spec, instruction });
      if (res.status === "ok") {
        // Two-tier như loadEnvelope: client tự validate lại config từ server
        const validated = validateGenericConfig(res.config);
        if (!validated.ok) {
          setEditMsg(`Cấu hình từ máy chủ không hợp lệ: ${validated.error}`);
        } else {
          applyNewSpec(validated.config);
          setEditMsg(res.note ?? "Đã cập nhật mô phỏng.");
        }
      } else {
        // unsupported_to_verify — phán quyết trung thực, hiển thị nguyên văn
        setEditMsg(res.reason);
      }
    } catch (err) {
      setEditMsg(err instanceof Error ? err.message : String(err));
    } finally {
      setEditBusy(false);
    }
  }

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
        // M7.13A: node có drag khai trong spec → kéo được (engine đã kiểm quyền)
        const canDrag = draggable.has(o.id) && !busy && !editMode;
        const isDragged = dragging === o.id;
        const editClickable = editMode && (editTool === "connect" || editTool === "delete");
        const isConnectFrom = connectFrom === o.id;
        const interactProps = canDrag
          ? {
              style: { cursor: isDragged ? "grabbing" : "grab" } as React.CSSProperties,
              onPointerDown: (e: React.PointerEvent<SVGGElement>) => onDragStart(e, o.id),
              onPointerMove: onDragMove,
              onPointerUp: onDragEnd,
              onPointerCancel: onDragEnd,
            }
          : editClickable
            ? {
                style: { cursor: "pointer" } as React.CSSProperties,
                onClick: (e: React.MouseEvent) => {
                  e.stopPropagation();
                  onObjectEditClick(o.id);
                },
              }
            : {};
        // M7.14: nhãn flip khi sát mép khung nhìn hiện hành — không bị cắt chữ
        const flipX = p.x + 11 > vb.x + vb.w - 46;
        const flipY = p.y - 9 < vb.y + 16;
        const labelX = flipX ? p.x - 11 : p.x + 11;
        const labelY = flipY ? p.y + 24 : p.y - 9;
        const labelAnchor = flipX ? "end" : "start";
        if (isPoint(o)) {
          // ĐIỂM (hình học): marker tròn rõ + nhãn lệch khỏi marker
          const r = current ? 8 : 6;
          const fill = current ? "var(--primary)" : "var(--ink)";
          return (
            <g key={o.id} className={popCls} {...interactProps}>
              {isConnectFrom && (
                <circle cx={p.x} cy={p.y} r={15} fill="transparent" stroke="var(--accent-orange)" strokeWidth={2.5} />
              )}
              {canDrag && (
                <circle cx={p.x} cy={p.y} r={13} fill={isDragged ? "var(--canvas-soft)" : "transparent"} stroke="var(--primary)" strokeWidth={1.5} strokeDasharray="3 3" opacity={0.7} />
              )}
              {editClickable && <circle cx={p.x} cy={p.y} r={14} fill="transparent" />}
              <circle cx={p.x} cy={p.y} r={r} fill={fill} stroke="#fff" strokeWidth={2} className={current ? "gen-glow" : undefined} />
              <text x={labelX} y={labelY} textAnchor={labelAnchor} fontSize={15} fontWeight={700} fill="var(--ink)">
                {o.label ?? o.id}
              </text>
            </g>
          );
        }
        // NÚT MẠNG (có node_type)
        const color = NODE_COLOR[o.node_type ?? ""] ?? "var(--primary)";
        return (
          <g key={o.id} className={popCls} {...interactProps}>
            {isConnectFrom && (
              <circle cx={p.x} cy={p.y} r={34} fill="transparent" stroke="var(--accent-orange)" strokeWidth={2.5} />
            )}
            {canDrag && (
              <circle cx={p.x} cy={p.y} r={32} fill="transparent" stroke="var(--primary)" strokeWidth={1.5} strokeDasharray="4 4" opacity={0.6} />
            )}
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

  // M7.14: các pass render theo Z-ORDER cố định — edge dưới node, label trên
  // node, object CURRENT trên object completed (không chỉ glow mà nổi thật).
  const spatialVisible = spec.objects.filter(
    (o) =>
      o.type !== "edge" &&
      o.type !== "moving_entity" &&
      o.type !== "label" &&
      !STRUCTURAL_TYPES.has(o.type) &&
      isObjectRenderable(frame, o),
  );
  const spatialCompleted = spatialVisible.filter((o) => objectRole(state, o.id) !== "current");
  const spatialCurrent = spatialVisible.filter((o) => objectRole(state, o.id) === "current");
  const labelsVisible = spec.objects.filter((o) => o.type === "label" && isObjectRenderable(frame, o));

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      {/* Stable control shell (M7.14D): hàng mode LUÔN tồn tại → chuyển chế độ
          không làm nhảy layout. Fit View chỉ có ở cảnh spatial (structural
          render theo luồng tài liệu, không cần thu khung) — không nhồi action
          vô nghĩa chỉ để lấp chỗ. */}
      <div className="player-controls" style={{ flexWrap: "wrap", gap: 6 }}>
        <button
          className={`btn-utility${!editMode ? " is-active" : ""}`}
          aria-pressed={!editMode}
          onClick={() => {
            setEditMode(false);
            disarm();
          }}
        >
          Quan sát
        </button>
        {canEdit && (
          <button
            className={`btn-utility${editMode ? " is-active" : ""}`}
            aria-pressed={editMode}
            disabled={busy}
            onClick={() => setEditMode(true)}
          >
            Chỉnh sửa
          </button>
        )}
        {!hasStructural && (
          <button
            className={`btn-utility${autoFit ? "" : " is-active"}`}
            style={{ marginLeft: "auto" }}
            onClick={() => setAutoFit(!autoFit)}
            title={autoFit ? "Đang tự thu vừa hình — bấm để về khung mặc định" : "Bấm để tự thu vừa hình"}
          >
            {autoFit ? "Khung mặc định" : "Thu vừa hình"}
          </button>
        )}
      </div>
      {editMode && (
        <EditBar
          policy={policy}
          tool={editTool}
          contentType={contentType}
          connectFrom={connectFrom}
          busy={editBusy}
          message={editMsg}
          onPickTool={onPickTool}
          onPickContentType={setContentType}
          onSubmitInstruction={submitNlEdit}
        />
      )}
      <div className="sim-stage">
        <svg
          ref={svgRef}
          viewBox={`${vb.x} ${vb.y} ${vb.w} ${vb.h}`}
          width="100%"
          style={{ maxWidth: VW, display: "block", margin: "0 auto", cursor: editMode && editTool === "add_node" ? "crosshair" : undefined }}
          onClick={onCanvasClick}
        >
          {/* 1. Cạnh (edge) — dưới cùng; chỉ khi edge + hai đầu đều visible (§6) */}
          {spec.objects
            .filter((o) => o.type === "edge" && isObjectRenderable(frame, o))
            .map((o) => {
              const a = pos[o.from ?? ""];
              const b = pos[o.to ?? ""];
              if (!a || !b) return null;
              const current = objectRole(state, o.id) === "current";
              const len = Math.hypot(b.x - a.x, b.y - a.y) || 1;
              // M7.14: nhãn cạnh ở trung điểm, dịch theo pháp tuyến (hướng lên)
              let nx = (-(b.y - a.y) / len) * 12;
              let ny = ((b.x - a.x) / len) * 12;
              if (ny > 0) {
                nx = -nx;
                ny = -ny;
              }
              const deletable = editMode && editTool === "delete";
              return (
                <g key={o.id}>
                  <line
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
                  {deletable && (
                    <line
                      x1={a.x}
                      y1={a.y}
                      x2={b.x}
                      y2={b.y}
                      stroke="transparent"
                      strokeWidth={14}
                      style={{ cursor: "pointer" }}
                      onClick={(e) => {
                        e.stopPropagation();
                        onObjectEditClick(o.id);
                      }}
                    />
                  )}
                  {o.label && (
                    <text
                      x={(a.x + b.x) / 2 + nx}
                      y={(a.y + b.y) / 2 + ny}
                      textAnchor="middle"
                      fontSize={12}
                      fontWeight={600}
                      fill="var(--ink-secondary)"
                    >
                      {o.label}
                    </text>
                  )}
                </g>
              );
            })}
          {/* 2. Họ cấu trúc/nội dung (M7.12): luồng tài liệu */}
          {structuralEls}
          {/* 3. Object spatial ĐÃ HIỆN (completed) */}
          {spatialCompleted.map((o) => renderObject(o, objectRole(state, o.id)))}
          {/* 4. Object spatial VỪA TẠO (current) — nổi trên completed */}
          {spatialCurrent.map((o) => renderObject(o, objectRole(state, o.id)))}
          {/* 5. Nhãn chữ đứng riêng — trên node/edge, không bị che */}
          {labelsVisible.map((o) => renderObject(o, objectRole(state, o.id)))}
          {/* 6. Thực thể di chuyển (packet) trên cùng */}
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
      {/* M7.14: InteractionFeedback — dẫn xuất của RULE engine, không phải chat */}
      {state.feedback && <div className="narration-bar is-user">{state.feedback.message}</div>}
      {/* Ở chế độ Chỉnh sửa, hướng dẫn thao tác do EditBar hiển thị (sát nút bấm) */}
      {!editMode && (
        <div className="narration-bar">
          {state.timeline.length > 1
            ? frame.narration
            : toggleable.size > 0
              ? "Bấm vào các công tắc để thay đổi trạng thái và quan sát kết quả."
              : draggable.size > 0
                ? "Kéo các điểm có viền đứt để thay đổi hình và quan sát các cạnh cập nhật theo."
                : spec.title}
        </div>
      )}
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
