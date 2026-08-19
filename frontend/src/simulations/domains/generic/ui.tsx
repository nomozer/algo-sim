import { useEffect, useRef, useState } from "react";
import { editViaServer } from "../../../llm/client";
import { svgAffordance } from "../../svg-affordance";
import { useAppStore } from "../../../state/store";
import type { WorkspaceProps } from "../../types";
import { EditBar, type EditTool } from "./EditBar";
import { editPolicyOf, hasMeaningfulEditAffordance } from "./edit-policy";
import {
  CONTAINER_TYPES,
  STRUCTURAL_TYPES,
  TEXT_CONTENT_TYPES,
  applyEditedSpec,
  childrenOf,
  currentFrame,
  displayLabel,
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
import { resolveSemanticAnchor } from "./anchor-resolver";

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
  // mạng máy tính
  client: "var(--accent-sky)",
  router: "var(--accent-purple)",
  server: "var(--accent-green)",
  switch: "var(--accent-teal)",
  isp: "var(--accent-orange)",
  // hệ thống thông tin (M8-PRE S2) — cùng primitive node, vai trò khác nhau phải
  // PHÂN BIỆT ĐƯỢC bằng mắt, nếu không sơ đồ mất ý nghĩa.
  actor: "var(--accent-sky)",
  process: "var(--accent-purple)",
  data_store: "var(--accent-teal)",
  input: "var(--accent-green)",
  output: "var(--accent-orange)",
};

/** node không có node_type → "điểm" (geometry); có node_type → nút mạng / thành phần hệ thống. */
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

// M17-RC1 §E — nhãn dài hơn ngần này của hai đối tượng kề nhau sẽ đè lên nhau
// khi chúng nằm cùng hàng ngang; so le đường cơ sở để vẫn đọc được cả hai.
const LABEL_STAGGER_MIN_LEN = 8;
const LABEL_STAGGER_DY = 16;
const LABEL_STAGGER_ROWS = 3;

export function GenericWorkspace({
  config: spec,
  state,
  busy,
  dispatch,
}: Props) {
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
  function laidOutNode(
    obj: SpecObject,
    x: number,
    y: number,
    width: number,
  ): { height: number; els: React.ReactElement[] } {
    const current = objectRole(state, obj.id) === "current";
    const pop = current ? "gen-pop" : undefined;

    if (obj.type === "heading") {
      const fs = 18;
      const lines = wrapText(obj.text ?? "", charsPerLine(width, fs));
      const els = lines.map((ln, i) => (
        <text
          key={`${obj.id}-${i}`}
          className={pop}
          x={x}
          y={y + 18 + i * 24}
          fontSize={fs}
          fontWeight={700}
          fill="var(--ink)"
        >
          {ln}
        </text>
      ));
      return { height: lines.length * 24 + 6, els };
    }
    if (obj.type === "paragraph" || obj.type === "text") {
      const fs = 14;
      const lines = wrapText(obj.text ?? "", charsPerLine(width, fs));
      const els = lines.map((ln, i) => (
        <text
          key={`${obj.id}-${i}`}
          className={pop}
          x={x}
          y={y + 13 + i * 19}
          fontSize={fs}
          fill="var(--ink-secondary)"
        >
          {ln}
        </text>
      ));
      return { height: lines.length * 19 + 6, els };
    }
    // container | group — khung chứa các con (childrenOf theo parent)
    const isContainer = obj.type === "container";
    const PAD = isContainer ? 14 : 8;
    const kids = childrenOf(spec, obj.id).filter((k) =>
      isObjectRenderable(frame, k),
    );
    const childEls: React.ReactElement[] = [];
    let cursor = y + PAD;
    if (obj.text) {
      childEls.push(
        <text
          key={`${obj.id}-title`}
          className={pop}
          x={x + PAD}
          y={cursor + 15}
          fontSize={15}
          fontWeight={700}
          fill="var(--ink)"
        >
          {obj.text}
        </text>,
      );
      cursor += 24;
    }
    for (const kid of kids) {
      const r = laidOutNode(kid, x + PAD, cursor, width - 2 * PAD);
      childEls.push(...r.els);
      cursor += r.height + FLOW_GAP;
    }
    const height = Math.max(
      cursor - (kids.length ? FLOW_GAP : 0) + PAD - y,
      isContainer ? 34 : 24,
    );
    const box = isContainer ? (
      <rect
        key={`${obj.id}-box`}
        className={pop}
        x={x}
        y={y}
        width={width}
        height={height}
        rx={10}
        fill="var(--surface)"
        stroke={current ? "var(--primary)" : "var(--ink-faint)"}
        strokeWidth={current ? 2.5 : 1.5}
      />
    ) : (
      <rect
        key={`${obj.id}-box`}
        x={x}
        y={y}
        width={width}
        height={height}
        rx={6}
        fill="var(--canvas-soft)"
        stroke="none"
      />
    );
    return { height, els: [box, ...childEls] };
  }

  const hasInteractive = spec.objects.some(
    (o) => !STRUCTURAL_TYPES.has(o.type) && o.type !== "label",
  );
  const structuralRootsVisible = structuralRoots(spec)
    .filter((o) => isObjectRenderable(frame, o))
    .filter((o) => !(hasInteractive && o.type === "heading"));
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
  /* W12 — CHẾ ĐỘ SỬA ĐẶC TẢ KHÔNG CÒN LỐI VÀO TRÊN BỀ MẶT HỌC SINH.
     Hằng số `false` thay cho `useState`: mọi nhánh sửa đặc tả bên dưới còn
     nguyên (chúng thuộc về vai trò SOẠN BÀI), nhưng không có cửa nào để học
     sinh rơi vào. Xem chú thích tại chỗ dựng dải điều khiển. */
  const editMode = false;
  const [editTool, setEditTool] = useState<EditTool>(null);
  const [contentType, setContentType] = useState<string>(
    policy.addableTypes[0] ?? "paragraph",
  );
  const [connectFrom, setConnectFrom] = useState<string | null>(null);
  const [editBusy, setEditBusy] = useState(false);
  const [editMsg, setEditMsg] = useState<string | null>(null);

  // M7.14D.1: không quảng bá chế độ Chỉnh sửa RỖNG. Cảnh value_only/observation
  // chỉ có edit_text → không có công cụ nào trên sân khấu → ẩn nút Chỉnh sửa;
  // tương tác trực tiếp (toggle/kéo) vẫn chạy bình thường. Suy từ policy thật.
  /* Giữ lời gọi để `edit-policy` vẫn là chủ sở hữu câu hỏi "cảnh này có công cụ
     sửa nào có nghĩa không" — vai trò soạn bài sẽ đọc lại nó. */
  void hasMeaningfulEditAffordance(policy);

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
    for (let n = 1; ; n += 1)
      if (!taken.has(`${prefix}${n}`)) return `${prefix}${n}`;
  }

  function onCanvasClick(e: React.MouseEvent) {
    if (!editMode || editTool !== "add_node" || editBusy) return;
    const d = domainPoint(e as unknown as React.PointerEvent);
    if (!d) return;
    const taken = spec.objects
      .filter(
        (o) =>
          !STRUCTURAL_TYPES.has(o.type) && o.type !== "edge" && state.pos[o.id],
      )
      .map((o) => state.pos[o.id]);
    const p = findFreePosition(taken, d);
    const id = nextFreeId("P");
    runLocalPatch([
      {
        op: "add_object",
        object: { id, type: "node", label: id, x: p.x, y: p.y },
      },
    ]);
  }

  /** Thêm một mục nội dung vào cuối cảnh structural (family structural). */
  function addContent() {
    if (editBusy) return;
    const id = nextFreeId(contentType.slice(0, 1).toUpperCase());
    const root = structuralRoots(spec).find((o) => CONTAINER_TYPES.has(o.type));
    const obj: Record<string, unknown> = { id, type: contentType };
    if (TEXT_CONTENT_TYPES.has(contentType))
      obj.text = "Nội dung mới — hãy sửa lại cho đúng ý.";
    if (CONTAINER_TYPES.has(contentType)) obj.text = "Khung mới";
    if (root) obj.parent = root.id;
    runLocalPatch([
      {
        op: "add_object",
        object: obj as PatchOp extends { object: infer O } ? O : never,
      },
    ]);
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
        runLocalPatch([
          {
            op: "connect",
            from: connectFrom,
            to: id,
            edge_id: nextFreeId(`${connectFrom}_${id}`),
          },
        ]);
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
      const res = await editViaServer({
        simulationId: "generic.rule_scene",
        config: spec,
        instruction,
      });
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
    const p = pos[o.id] ?? { x: 50, y: 50 };
    const v = values[o.id] !== undefined ? values[o.id] : (o.value ?? 0);
    const current = role === "current";
    const popCls = current ? "gen-pop" : undefined;
    // M13 Task 11: nhãn CHÍNH không bao giờ là id kỹ thuật thô (xem displayLabel).
    const dl = displayLabel(spec, o.id);
    // Thứ tự khai báo — ổn định, dùng để so le nhãn dài (§E).
    const idx = spec.objects.findIndex((x) => x.id === o.id);

    switch (o.type) {
      case "switch": {
        const on = v >= 1;
        const clickable = toggleable.has(o.id);
        return (
          <g
            key={o.id}
            className={popCls}
            style={{ cursor: clickable ? "pointer" : "default" }}
            onClick={() =>
              clickable && dispatch({ type: "toggle", target: o.id })
            }
          >
            {o.label && (
              <text
                x={p.x}
                y={p.y - 28}
                textAnchor="middle"
                fontSize={13}
                fontWeight={600}
                fill="var(--ink-secondary)"
              >
                {dl}
              </text>
            )}
            <rect
              x={p.x - 30}
              y={p.y - 17}
              width={60}
              height={34}
              rx={17}
              fill={on ? "var(--primary)" : "var(--canvas-soft)"}
              stroke={on ? "var(--primary)" : "var(--ink-faint)"}
              strokeWidth={2}
              style={{ transition: "fill 0.15s ease" }}
            />
            <circle
              cx={p.x + (on ? 13 : -13)}
              cy={p.y}
              r={13}
              fill="#fff"
              style={{ transition: "cx 0.15s ease" }}
            />
            <text
              x={p.x + (on ? -14 : 14)}
              y={p.y + 5}
              textAnchor="middle"
              fontSize={13}
              fontWeight={700}
              fill={on ? "#fff" : "var(--ink-muted)"}
            >
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
              <text
                x={p.x}
                y={p.y + 44}
                textAnchor="middle"
                fontSize={12}
                fill="var(--ink-secondary)"
              >
                {dl}
              </text>
            )}
            <circle
              cx={p.x}
              cy={p.y}
              r={26}
              fill={on ? "var(--accent-green)" : "var(--canvas-soft)"}
              stroke={on ? "var(--accent-green)" : "var(--ink-faint)"}
              strokeWidth={current ? 3.5 : 2}
              style={{ transition: "fill 0.2s ease" }}
            />
            <text
              x={p.x}
              y={p.y + 6}
              textAnchor="middle"
              fontSize={18}
              fontWeight={700}
              fill={on ? "#fff" : "var(--ink-muted)"}
            >
              {v}
            </text>
          </g>
        );
      }
      case "value_box": {
        const strV = String(v ?? "");
        const fontSize = strV.length > 8 ? 12 : strV.length > 4 ? 15 : 20;
        return (
          <g key={o.id} className={popCls}>
            {o.label && (
              <text
                x={p.x}
                y={p.y - 26}
                textAnchor="middle"
                fontSize={12}
                fill="var(--ink-secondary)"
              >
                {dl}
              </text>
            )}
            <rect
              x={p.x - 42}
              y={p.y - 20}
              width={84}
              height={40}
              rx={8}
              fill="var(--surface)"
              stroke="var(--primary)"
              strokeWidth={current ? 3 : 2}
            />
            <text
              x={p.x}
              y={p.y + 7}
              textAnchor="middle"
              fontSize={fontSize}
              fontWeight={700}
              fill="var(--ink)"
            >
              {strV}
            </text>
          </g>
        );
      }
      case "slider": {
        const min = o.min ?? 0;
        const max = o.max ?? 100;
        const numV = typeof v === "number" ? v : Number(v) || min;
        const pct = Math.max(0, Math.min(1, (numV - min) / (max - min || 1)));
        const sliderWidth = 140;
        const trackX = p.x - sliderWidth / 2;
        const thumbX = trackX + pct * sliderWidth;
        return (
          <g key={o.id} className={popCls}>
            {o.label && (
              <text
                x={p.x}
                y={p.y - 18}
                textAnchor="middle"
                fontSize={13}
                fontWeight={600}
                fill="var(--ink-secondary)"
              >
                {dl}
              </text>
            )}
            <rect
              x={trackX}
              y={p.y - 4}
              width={sliderWidth}
              height={8}
              rx={4}
              fill="var(--canvas-soft)"
              stroke="var(--ink-faint)"
              strokeWidth={1}
            />
            <rect
              x={trackX}
              y={p.y - 4}
              width={pct * sliderWidth}
              height={8}
              rx={4}
              fill="var(--primary)"
            />
            <circle
              cx={thumbX}
              cy={p.y}
              r={10}
              fill="#fff"
              stroke="var(--primary)"
              strokeWidth={3}
              style={{ cursor: "ew-resize" }}
            />
            <text
              x={p.x}
              y={p.y + 24}
              textAnchor="middle"
              fontSize={12}
              fontWeight={700}
              fill="var(--ink)"
            >
              {numV} {o.unit ?? ""}
            </text>
          </g>
        );
      }
      case "color_swatch": {
        const colorStr = typeof v === "string" ? v : (o.color ?? "#3b82f6");
        const swatchW = 110;
        const swatchH = 80;
        return (
          <g key={o.id} className={popCls}>
            {o.label && (
              <text
                x={p.x}
                y={p.y - swatchH / 2 - 10}
                textAnchor="middle"
                fontSize={13}
                fontWeight={600}
                fill="var(--ink-secondary)"
              >
                {dl}
              </text>
            )}
            <rect
              x={p.x - swatchW / 2}
              y={p.y - swatchH / 2}
              width={swatchW}
              height={swatchH}
              rx={12}
              fill={colorStr}
              stroke="var(--ink-faint)"
              strokeWidth={2}
              style={{
                transition: "fill 0.15s ease",
                filter: "drop-shadow(0 4px 12px rgba(0,0,0,0.15))",
              }}
            />
            <rect
              x={p.x - swatchW / 2}
              y={p.y + swatchH / 2 - 26}
              width={swatchW}
              height={26}
              rx={6}
              fill="rgba(0,0,0,0.65)"
            />
            <text
              x={p.x}
              y={p.y + swatchH / 2 - 9}
              textAnchor="middle"
              fontSize={12}
              fontWeight={700}
              fontFamily="monospace"
              fill="#ffffff"
            >
              {colorStr.toUpperCase()}
            </text>
          </g>
        );
      }
      case "array_strip": {
        const items = Array.isArray(o.items)
          ? o.items
          : typeof o.text === "string"
            ? Array.from(o.text)
            : v !== undefined && v !== 0
              ? [v]
              : [" "];
        const count = Math.max(1, items.length);
        const cellW = Math.min(
          38,
          Math.max(28, Math.floor((VW * 0.7) / count)),
        );
        const cellH = 34;
        const totalW = count * cellW;
        const startX = p.x - totalW / 2;
        return (
          <g key={o.id} className={popCls}>
            {o.label && (
              <text
                x={p.x}
                y={p.y - cellH / 2 - 8}
                textAnchor="middle"
                fontSize={12}
                fontWeight={600}
                fill="var(--ink-secondary)"
              >
                {dl}
              </text>
            )}
            {items.map((item, i) => {
              const strVal = String(item ?? "");
              const isChar = strVal.length === 1 && !/\d/.test(strVal);
              return (
                <g
                  key={i}
                  transform={`translate(${startX + i * cellW}, ${p.y - cellH / 2})`}
                >
                  <rect
                    width={cellW}
                    height={cellH}
                    rx={4}
                    fill={isChar ? "var(--canvas-soft)" : "var(--surface)"}
                    stroke="var(--primary)"
                    strokeWidth={1.5}
                  />
                  <text
                    x={cellW / 2}
                    y={cellH / 2 + 5}
                    textAnchor="middle"
                    fontSize={isChar ? 14 : 12}
                    fontWeight={700}
                    fill="var(--ink)"
                  >
                    {strVal}
                  </text>
                  <text
                    x={cellW / 2}
                    y={cellH + 12}
                    textAnchor="middle"
                    fontSize={9}
                    fill="var(--ink-muted)"
                  >
                    [{i}]
                  </text>
                </g>
              );
            })}
          </g>
        );
      }
      case "metric_gauge": {
        const min = o.min ?? 0;
        const max = o.max ?? 100;
        const numV = typeof v === "number" ? v : Number(v) || min;
        const pct = Math.max(0, Math.min(1, (numV - min) / (max - min || 1)));
        const gaugeW = 120;
        const gaugeH = 14;
        return (
          <g key={o.id} className={popCls}>
            {o.label && (
              <text
                x={p.x}
                y={p.y - gaugeH - 4}
                textAnchor="middle"
                fontSize={12}
                fontWeight={600}
                fill="var(--ink-secondary)"
              >
                {dl}
              </text>
            )}
            <rect
              x={p.x - gaugeW / 2}
              y={p.y}
              width={gaugeW}
              height={gaugeH}
              rx={gaugeH / 2}
              fill="var(--canvas-soft)"
              stroke="var(--ink-faint)"
              strokeWidth={1}
            />
            <rect
              x={p.x - gaugeW / 2}
              y={p.y}
              width={pct * gaugeW}
              height={gaugeH}
              rx={gaugeH / 2}
              fill="var(--accent-teal)"
            />
            <text
              x={p.x}
              y={p.y + gaugeH + 16}
              textAnchor="middle"
              fontSize={12}
              fontWeight={700}
              fill="var(--ink)"
            >
              {numV} {o.unit ?? ""} ({Math.round(pct * 100)}%)
            </text>
          </g>
        );
      }
      case "bar_chart": {
        const bars =
          o.bars && o.bars.length > 0
            ? o.bars
            : [{ id: "b0", value: typeof v === "number" ? v : 50, label: dl }];
        const maxVal =
          o.max_val ?? Math.max(10, ...bars.map((b) => Number(b.value) || 0));
        const chartW = Math.min(320, bars.length * 44 + 40);
        const chartH = 120;
        const barW = Math.max(16, Math.floor((chartW - 40) / bars.length) - 8);
        const stepAct = frame.stepAction;
        return (
          <g
            key={o.id}
            className={popCls}
            transform={`translate(${p.x - chartW / 2}, ${p.y - chartH / 2})`}
          >
            {o.label && (
              <text
                x={chartW / 2}
                y={-10}
                textAnchor="middle"
                fontSize={13}
                fontWeight={600}
                fill="var(--ink-secondary)"
              >
                {dl}
              </text>
            )}
            <line
              x1={10}
              y1={chartH - 20}
              x2={chartW - 10}
              y2={chartH - 20}
              stroke="var(--ink-faint)"
              strokeWidth={2}
            />
            {bars.map((b, i) => {
              const bVal = Number(b.value) || 0;
              const bH = Math.max(4, (bVal / maxVal) * (chartH - 40));
              const bx = 20 + i * (barW + 8);
              const by = chartH - 20 - bH;
              const isTargeted =
                stepAct?.targets?.includes(o.id) &&
                stepAct?.indices?.includes(i);
              let barColor = b.color ?? "var(--primary)";
              if (isTargeted) {
                if (stepAct?.action === "swap")
                  barColor = "var(--accent-purple)";
                else if (stepAct?.state === "comparing")
                  barColor = "var(--accent-orange)";
                else if (stepAct?.state === "sorted")
                  barColor = "var(--accent-green)";
              }
              return (
                <g key={b.id ?? i}>
                  <rect
                    x={bx}
                    y={by}
                    width={barW}
                    height={bH}
                    rx={4}
                    fill={barColor}
                    stroke={isTargeted ? "#fff" : "transparent"}
                    strokeWidth={isTargeted ? 2 : 0}
                    style={{ transition: "all 0.25s ease" }}
                  />
                  <text
                    x={bx + barW / 2}
                    y={by - 5}
                    textAnchor="middle"
                    fontSize={11}
                    fontWeight={700}
                    fill="var(--ink)"
                  >
                    {bVal}
                  </text>
                  <text
                    x={bx + barW / 2}
                    y={chartH - 6}
                    textAnchor="middle"
                    fontSize={10}
                    fill="var(--ink-muted)"
                  >
                    {b.label ?? `[${i}]`}
                  </text>
                </g>
              );
            })}
          </g>
        );
      }
      case "table_grid": {
        const headers = o.headers ?? ["Cột 1", "Cột 2"];
        const rows = o.rows ?? [];
        const cellW = 60;
        const cellH = 24;
        const gridW = headers.length * cellW;
        const gridH = (rows.length + 1) * cellH;
        return (
          <g
            key={o.id}
            className={popCls}
            transform={`translate(${p.x - gridW / 2}, ${p.y - gridH / 2})`}
          >
            {o.label && (
              <text
                x={gridW / 2}
                y={-10}
                textAnchor="middle"
                fontSize={13}
                fontWeight={600}
                fill="var(--ink-secondary)"
              >
                {dl}
              </text>
            )}
            {headers.map((h, ci) => (
              <g key={`h-${ci}`} transform={`translate(${ci * cellW}, 0)`}>
                <rect
                  width={cellW}
                  height={cellH}
                  fill="var(--canvas-soft)"
                  stroke="var(--ink-faint)"
                  strokeWidth={1}
                />
                <text
                  x={cellW / 2}
                  y={cellH / 2 + 4}
                  textAnchor="middle"
                  fontSize={11}
                  fontWeight={700}
                  fill="var(--ink)"
                >
                  {h}
                </text>
              </g>
            ))}
            {rows.map((row, ri) =>
              (Array.isArray(row) ? row : [row]).map((cell, ci) => {
                const isHighlight = o.highlighted_cells?.some(
                  (hc) => hc.row === ri && hc.col === ci,
                );
                const highlightColor =
                  o.highlighted_cells?.find(
                    (hc) => hc.row === ri && hc.col === ci,
                  )?.color ?? "var(--accent-teal)";
                return (
                  <g
                    key={`r-${ri}-${ci}`}
                    transform={`translate(${ci * cellW}, ${(ri + 1) * cellH})`}
                  >
                    <rect
                      width={cellW}
                      height={cellH}
                      fill={isHighlight ? highlightColor : "var(--surface)"}
                      fillOpacity={isHighlight ? 0.35 : 1}
                      stroke="var(--ink-faint)"
                      strokeWidth={1}
                    />
                    <text
                      x={cellW / 2}
                      y={cellH / 2 + 4}
                      textAnchor="middle"
                      fontSize={11}
                      fill="var(--ink)"
                    >
                      {String(cell)}
                    </text>
                  </g>
                );
              }),
            )}
          </g>
        );
      }
      case "stack_view": {
        const items = Array.isArray(o.items)
          ? o.items
          : v !== undefined && v !== 0
            ? [v]
            : [];
        const itemH = 22;
        const boxW = 80;
        const capacity = o.capacity ?? Math.max(4, items.length);
        const boxH = Math.max(80, capacity * itemH + 20);
        const safeY = Math.max(boxH / 2 + 28, p.y);
        return (
          <g
            key={o.id}
            className={popCls}
            transform={`translate(${p.x - boxW / 2}, ${safeY - boxH / 2})`}
          >
            {o.label && (
              <text
                x={boxW / 2}
                y={-10}
                textAnchor="middle"
                fontSize={13}
                fontWeight={600}
                fill="var(--ink-secondary)"
              >
                {dl}
              </text>
            )}
            <path
              d={`M 0,0 L 0,${boxH} L ${boxW},${boxH} L ${boxW},0`}
              fill="none"
              stroke="var(--primary)"
              strokeWidth={2.5}
            />
            {items.map((it, i) => {
              const iy = boxH - (i + 1) * itemH - 4;
              return (
                <g key={i} transform={`translate(6, ${iy})`}>
                  <rect
                    width={boxW - 12}
                    height={itemH - 3}
                    rx={3}
                    fill="var(--surface)"
                    stroke="var(--primary)"
                    strokeWidth={1}
                  />
                  <text
                    x={(boxW - 12) / 2}
                    y={(itemH - 3) / 2 + 4}
                    textAnchor="middle"
                    fontSize={11}
                    fontWeight={600}
                    fill="var(--ink)"
                  >
                    {String(it)}
                  </text>
                  {i === items.length - 1 && (
                    <text
                      x={boxW + 6}
                      y={(itemH - 3) / 2 + 4}
                      fontSize={10}
                      fontWeight={700}
                      fill="var(--accent-orange)"
                    >
                      ← TOP
                    </text>
                  )}
                </g>
              );
            })}
          </g>
        );
      }
      case "queue_view": {
        const items = Array.isArray(o.items)
          ? o.items
          : v !== undefined && v !== 0
            ? [v]
            : [];
        const itemW = 34;
        const boxH = 36;
        const capacity = o.capacity ?? Math.max(4, items.length);
        const boxW = Math.max(120, capacity * itemW + 20);
        const safeY = Math.max(boxH / 2 + 28, p.y);
        return (
          <g
            key={o.id}
            className={popCls}
            transform={`translate(${p.x - boxW / 2}, ${safeY - boxH / 2})`}
          >
            {o.label && (
              <text
                x={boxW / 2}
                y={-10}
                textAnchor="middle"
                fontSize={13}
                fontWeight={600}
                fill="var(--ink-secondary)"
              >
                {dl}
              </text>
            )}
            <line
              x1={0}
              y1={0}
              x2={boxW}
              y2={0}
              stroke="var(--primary)"
              strokeWidth={2}
            />
            <line
              x1={0}
              y1={boxH}
              x2={boxW}
              y2={boxH}
              stroke="var(--primary)"
              strokeWidth={2}
            />
            <text
              x={-6}
              y={boxH / 2 + 4}
              textAnchor="end"
              fontSize={9}
              fontWeight={700}
              fill="var(--accent-teal)"
            >
              FRONT
            </text>
            <text
              x={boxW + 6}
              y={boxH / 2 + 4}
              textAnchor="start"
              fontSize={9}
              fontWeight={700}
              fill="var(--accent-teal)"
            >
              REAR
            </text>
            {items.map((it, i) => (
              <g key={i} transform={`translate(${10 + i * itemW}, 4)`}>
                <rect
                  width={itemW - 4}
                  height={boxH - 8}
                  rx={4}
                  fill="var(--surface)"
                  stroke="var(--accent-teal)"
                  strokeWidth={1}
                />
                <text
                  x={(itemW - 4) / 2}
                  y={(boxH - 8) / 2 + 4}
                  textAnchor="middle"
                  fontSize={11}
                  fontWeight={600}
                  fill="var(--ink)"
                >
                  {String(it)}
                </text>
              </g>
            ))}
          </g>
        );
      }
      case "tree_element": {
        const valStr = o.value !== undefined ? String(o.value) : dl || "Node";
        const leftPos = o.left && pos[o.left] ? pos[o.left] : null;
        const rightPos = o.right && pos[o.right] ? pos[o.right] : null;
        return (
          <g key={o.id} className={popCls}>
            {leftPos && (
              <line
                x1={p.x}
                y1={p.y}
                x2={leftPos.x}
                y2={leftPos.y}
                stroke="var(--primary)"
                strokeWidth={2}
              />
            )}
            {rightPos && (
              <line
                x1={p.x}
                y1={p.y}
                x2={rightPos.x}
                y2={rightPos.y}
                stroke="var(--primary)"
                strokeWidth={2}
              />
            )}
            <circle
              cx={p.x}
              cy={p.y}
              r={20}
              fill="var(--surface)"
              stroke="var(--primary)"
              strokeWidth={2.5}
            />
            <text
              x={p.x}
              y={p.y + 5}
              textAnchor="middle"
              fontSize={12}
              fontWeight={700}
              fill="var(--ink)"
            >
              {valStr}
            </text>
            {o.label && (
              <text
                x={p.x}
                y={p.y - 24}
                textAnchor="middle"
                fontSize={11}
                fill="var(--ink-secondary)"
              >
                {dl}
              </text>
            )}
          </g>
        );
      }
      case "bit_register": {
        const numVal = typeof v === "number" ? v : Number(v) || 0;
        const size = o.size === 16 ? 16 : 8;
        const bits: number[] =
          Array.isArray(o.bits) && o.bits.length === size
            ? o.bits
            : Array.from(
                { length: size },
                (_, i) => (numVal >> (size - 1 - i)) & 1,
              );
        const cellW = 20;
        const cellH = 26;
        const regW = size * cellW;
        return (
          <g
            key={o.id}
            className={popCls}
            transform={`translate(${p.x - regW / 2}, ${p.y - cellH / 2})`}
          >
            {o.label && (
              <text
                x={regW / 2}
                y={-10}
                textAnchor="middle"
                fontSize={13}
                fontWeight={600}
                fill="var(--ink-secondary)"
              >
                {dl}
              </text>
            )}
            {bits.map((b, i) => (
              <g key={i} transform={`translate(${i * cellW}, 0)`}>
                <rect
                  width={cellW}
                  height={cellH}
                  fill={b === 1 ? "var(--primary)" : "var(--surface)"}
                  stroke="var(--ink-faint)"
                  strokeWidth={1}
                />
                <text
                  x={cellW / 2}
                  y={cellH / 2 + 5}
                  textAnchor="middle"
                  fontSize={12}
                  fontWeight={700}
                  fill={b === 1 ? "#fff" : "var(--ink)"}
                >
                  {b}
                </text>
                <text
                  x={cellW / 2}
                  y={cellH + 12}
                  textAnchor="middle"
                  fontSize={8}
                  fill="var(--ink-muted)"
                >
                  {size - 1 - i}
                </text>
              </g>
            ))}
            {(o.show_decimal !== false || o.show_hex) && (
              <text
                x={regW / 2}
                y={cellH + 28}
                textAnchor="middle"
                fontSize={11}
                fontWeight={600}
                fill="var(--ink-secondary)"
              >
                {o.show_decimal !== false ? `Dec: ${numVal} ` : ""}
                {o.show_hex
                  ? ` Hex: 0x${numVal.toString(16).toUpperCase()}`
                  : ""}
              </text>
            )}
          </g>
        );
      }
      case "logic_gate": {
        const gateType = (o.gate_type ?? "and").toLowerCase();
        const gateW = 60;
        const gateH = 40;
        return (
          <g
            key={o.id}
            className={popCls}
            transform={`translate(${p.x - gateW / 2}, ${p.y - gateH / 2})`}
          >
            {o.label && (
              <text
                x={gateW / 2}
                y={-8}
                textAnchor="middle"
                fontSize={12}
                fontWeight={600}
                fill="var(--ink-secondary)"
              >
                {dl}
              </text>
            )}
            <rect
              width={gateW}
              height={gateH}
              rx={8}
              fill="var(--surface)"
              stroke="var(--primary)"
              strokeWidth={2}
            />
            <text
              x={gateW / 2}
              y={gateH / 2 + 5}
              textAnchor="middle"
              fontSize={13}
              fontWeight={700}
              fill="var(--primary)"
            >
              {gateType.toUpperCase()}
            </text>
          </g>
        );
      }
      case "pointer": {
        const ptrLabel = o.label ?? "ptr";
        return (
          <g
            key={o.id}
            className={popCls}
            transform={`translate(${p.x}, ${p.y})`}
          >
            <path
              d="M 0,-10 L -6,-20 L 6,-20 Z"
              fill={o.color ?? "var(--accent-orange)"}
            />
            <rect
              x={-14}
              y={-38}
              width={28}
              height={18}
              rx={4}
              fill={o.color ?? "var(--accent-orange)"}
            />
            <text
              x={0}
              y={-25}
              textAnchor="middle"
              fontSize={11}
              fontWeight={700}
              fill="#fff"
            >
              {ptrLabel}
            </text>
          </g>
        );
      }
      case "coordinate_plane": {
        const planeW = 180;
        const planeH = 180;
        const cx = planeW / 2;
        const cy = planeH / 2;
        return (
          <g
            key={o.id}
            className={popCls}
            transform={`translate(${p.x - planeW / 2}, ${p.y - planeH / 2})`}
          >
            {o.label && (
              <text
                x={planeW / 2}
                y={-10}
                textAnchor="middle"
                fontSize={13}
                fontWeight={600}
                fill="var(--ink-secondary)"
              >
                {dl}
              </text>
            )}
            <rect
              width={planeW}
              height={planeH}
              fill="var(--canvas-soft)"
              stroke="var(--ink-faint)"
              strokeWidth={1}
              rx={6}
            />
            <line
              x1={10}
              y1={cy}
              x2={planeW - 10}
              y2={cy}
              stroke="var(--ink-secondary)"
              strokeWidth={1.5}
            />
            <line
              x1={cx}
              y1={planeH - 10}
              x2={cx}
              y2={10}
              stroke="var(--ink-secondary)"
              strokeWidth={1.5}
            />
            <text
              x={planeW - 8}
              y={cy + 4}
              fontSize={11}
              fontWeight={700}
              fill="var(--ink)"
            >
              x
            </text>
            <text
              x={cx + 5}
              y={14}
              fontSize={11}
              fontWeight={700}
              fill="var(--ink)"
            >
              y
            </text>
            <text x={cx - 8} y={cy + 12} fontSize={9} fill="var(--ink-muted)">
              O
            </text>
          </g>
        );
      }
      case "node": {
        // M7.13A: node có drag khai trong spec → kéo được (engine đã kiểm quyền)
        const canDrag = draggable.has(o.id) && !busy && !editMode;
        const isDragged = dragging === o.id;
        const editClickable =
          editMode && (editTool === "connect" || editTool === "delete");
        const isConnectFrom = connectFrom === o.id;
        const interactProps = canDrag
          ? {
              style: {
                cursor: isDragged ? "grabbing" : "grab",
              } as React.CSSProperties,
              onPointerDown: (e: React.PointerEvent<SVGGElement>) =>
                onDragStart(e, o.id),
              onPointerMove: onDragMove,
              onPointerUp: onDragEnd,
              onPointerCancel: onDragEnd,
            }
          : editClickable
            ? /* W12 §19 — nối/xoá là THAO TÁC LÊN MÔ HÌNH, nên phải có đường bàn
                 phím. (Kéo ở nhánh trên chỉ đổi `state.pos` — vị trí trình bày —
                 nên nó không cần bản tương đương ngữ nghĩa; điều đó được ghi
                 thẳng vào artifact là `DRAG_IS_PRESENTATION_ONLY` thay vì khai
                 khống một đường bàn phím không tồn tại.) */
              svgAffordance({
                label:
                  editTool === "connect"
                    ? `Nối từ ${dl || o.id}`
                    : `Xoá ${dl || o.id}`,
                onAct: () => onObjectEditClick(o.id),
                pressed: isConnectFrom,
              })
            : {};
        // M7.14: nhãn flip khi sát mép khung nhìn hiện hành — không bị cắt chữ
        const flipX = p.x + 11 > vb.x + vb.w - 46;
        const flipY = p.y - 9 < vb.y + 16;
        const labelX = flipX ? p.x - 11 : p.x + 11;
        // M17-RC1 §E — nhãn DÀI của các đối tượng nằm cùng một hàng ngang sẽ
        // đè lên nhau thành khối chữ không đọc được (audit trình duyệt thật
        // bắt được ở cảnh "Sơ đồ trạm quan trắc"). So le nhãn dài theo thứ tự
        // để hai nhãn kề nhau không dùng chung một đường cơ sở. Chỉ đổi TRÌNH
        // BÀY — vị trí ngữ nghĩa (state.pos) không đụng tới.
        // BA hàng so le (không phải hai): với ba đối tượng nhãn dài cùng nằm
        // trên một đường ngang, so le hai hàng vẫn để hai nhãn chung hàng đè
        // nhau. Đẩy RA XA điểm (lên trên khi nhãn ở trên, xuống dưới khi đã
        // flip) nên chữ không bao giờ chồng lên chính marker.
        const longLabel = String(dl ?? "").length > LABEL_STAGGER_MIN_LEN;
        const row = longLabel ? idx % LABEL_STAGGER_ROWS : 0;
        const stagger = row * LABEL_STAGGER_DY * (flipY ? 1 : -1);
        const labelY = (flipY ? p.y + 24 : p.y - 9) + stagger;
        const labelAnchor = flipX ? "end" : "start";
        if (isPoint(o)) {
          // ĐIỂM (hình học): marker tròn rõ + nhãn lệch khỏi marker
          const r = current ? 8 : 6;
          const fill = current ? "var(--primary)" : "var(--ink)";
          return (
            <g key={o.id} className={popCls} {...interactProps}>
              {isConnectFrom && (
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={15}
                  fill="transparent"
                  stroke="var(--accent-orange)"
                  strokeWidth={2.5}
                />
              )}
              {canDrag && (
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={13}
                  fill={isDragged ? "var(--canvas-soft)" : "transparent"}
                  stroke="var(--primary)"
                  strokeWidth={1.5}
                  strokeDasharray="3 3"
                  opacity={0.7}
                />
              )}
              {editClickable && (
                <circle cx={p.x} cy={p.y} r={14} fill="transparent" />
              )}
              <circle
                cx={p.x}
                cy={p.y}
                r={r}
                fill={fill}
                stroke="#fff"
                strokeWidth={2}
                className={current ? "gen-glow" : undefined}
              />
              <text
                x={labelX}
                y={labelY}
                textAnchor={labelAnchor}
                fontSize={15}
                fontWeight={700}
                fill="var(--ink)"
              >
                {dl}
              </text>
            </g>
          );
        }
        // NÚT MẠNG (có node_type)
        const color = NODE_COLOR[o.node_type ?? ""] ?? "var(--primary)";
        return (
          <g key={o.id} className={popCls} {...interactProps}>
            {isConnectFrom && (
              <circle
                cx={p.x}
                cy={p.y}
                r={34}
                fill="transparent"
                stroke="var(--accent-orange)"
                strokeWidth={2.5}
              />
            )}
            {canDrag && (
              <circle
                cx={p.x}
                cy={p.y}
                r={32}
                fill="transparent"
                stroke="var(--primary)"
                strokeWidth={1.5}
                strokeDasharray="4 4"
                opacity={0.6}
              />
            )}
            <circle
              cx={p.x}
              cy={p.y}
              r={26}
              fill="var(--surface)"
              stroke={color}
              strokeWidth={current ? 4 : 2.5}
              className={current ? "gen-glow" : undefined}
            />
            {/* M8-PRE: hợp đồng bảo node dùng "label"; LLM đôi khi đặt "text" — nút
                KHÔNG TÊN thì sơ đồ mất nghĩa, nên fallback thay vì bỏ trống.
                M13 Task 11: label kỹ thuật (thiếu/=id/dạng snake-kebab) đi qua
                displayLabel để sanitize trước khi rơi ra UI học sinh. */}
            <text
              x={p.x}
              y={p.y - 1}
              textAnchor="middle"
              fontSize={11}
              fontWeight={600}
              fill="var(--ink)"
            >
              {o.label ? dl : (o.text ?? dl)}
            </text>
            {o.node_type && (
              <text
                x={p.x}
                y={p.y + 11}
                textAnchor="middle"
                fontSize={9}
                fill="var(--ink-muted)"
              >
                {o.node_type}
              </text>
            )}
          </g>
        );
      }
      case "label":
        return (
          <text
            key={o.id}
            className={popCls}
            x={p.x}
            y={p.y}
            textAnchor="middle"
            fontSize={14}
            fontWeight={current ? 700 : 400}
            fill="var(--ink-secondary)"
          >
            {dl}
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
  const spatialCompleted = spatialVisible.filter(
    (o) => objectRole(state, o.id) !== "current",
  );
  const spatialCurrent = spatialVisible.filter(
    (o) => objectRole(state, o.id) === "current",
  );
  const labelsVisible = spec.objects.filter(
    (o) => o.type === "label" && isObjectRenderable(frame, o),
  );

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      {/* Stable control shell (M7.14D): hàng mode LUÔN tồn tại → chuyển chế độ
          không làm nhảy layout. Fit View chỉ có ở cảnh spatial (structural
          render theo luồng tài liệu, không cần thu khung) — không nhồi action
          vô nghĩa chỉ để lấp chỗ. */}
      {/* W12 — BỎ CẶP TAB [Quan sát][Chỉnh sửa] KHỎI BỀ MẶT HỌC SINH.
       *
       * Đây là hệ mô phỏng TƯƠNG TÁC. Hai nhãn cũ nói ngược với việc chúng làm:
       * chỗ học sinh thao tác thật lại mang tên "Quan sát" — đúng cái từ bảo
       * các em chỉ được nhìn — còn "Chỉnh sửa" thì TẮT tương tác học tập để bật
       * công cụ sửa đặc tả (thêm nút, nối, xoá). Gõ vào để thêm/sửa đặc tả là
       * việc SOẠN BÀI, không phải việc học; bày nó cho học sinh là sai bản chất
       * đề tài.
       *
       * Nên bỏ CHẾ ĐỘ, không bỏ năng lực: `editMode` giữ nguyên trong state và
       * mặc định `false`, nên toàn bộ nhánh sửa đặc tả (`editClickable`,
       * `EditBar`, patch flow) còn nguyên cho vai trò soạn bài về sau. Thao tác
       * học tập — bật/tắt, kéo — vốn đã chạy khi `!editMode`, nên nay nó LUÔN
       * bật, không còn cửa nào để lỡ tắt.
       *
       * Cùng khuôn với cách `protocol_encapsulation` lùi 3D về nội bộ: giữ khả
       * năng, thôi bắt người học chọn. */}
      <div className="player-controls" style={{ flexWrap: "wrap", gap: 6 }}>
        {!hasStructural && (
          <button
            /* W4B-3E — `marginLeft:auto` ĐÃ GỠ. Cùng lỗi, khác chủ sở hữu: một
               THÀNH VIÊN đẩy mình sang mép phải thì phần còn lại thành khoảng
               chết — đo được 1390px @1920 trên `gen-rule-library`. "Thu vừa
               hình" thuộc cùng nhóm hành động với "Quan sát/Chỉnh sửa", nên nó
               đứng liền nhóm; muốn tách thì tách bằng NHÓM, không bằng lề. */
            className={`btn-utility${autoFit ? "" : " is-active"}`}
            onClick={() => setAutoFit(!autoFit)}
            title={
              autoFit
                ? "Đang tự thu vừa hình — bấm để về khung mặc định"
                : "Bấm để tự thu vừa hình"
            }
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
          connectFrom={connectFrom ? displayLabel(spec, connectFrom) : null}
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
          style={{
            maxWidth: VW,
            display: "block",
            margin: "0 auto",
            cursor:
              editMode && editTool === "add_node" ? "crosshair" : undefined,
          }}
          onClick={onCanvasClick}
        >
          {/* M8-PRE (S2): đầu mũi tên cho edge CÓ CHIỀU (luồng dữ liệu). Hai biến thể
              màu vì marker không kế thừa stroke của line. userSpaceOnUse → kích thước
              mũi tên không đổi theo strokeWidth. */}
          <defs>
            <marker
              id="gen-arrow"
              viewBox="0 0 10 10"
              refX="10"
              refY="5"
              markerWidth={12}
              markerHeight={12}
              orient="auto-start-reverse"
              markerUnits="userSpaceOnUse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--ink-secondary)" />
            </marker>
            <marker
              id="gen-arrow-current"
              viewBox="0 0 10 10"
              refX="10"
              refY="5"
              markerWidth={12}
              markerHeight={12}
              orient="auto-start-reverse"
              markerUnits="userSpaceOnUse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--primary)" />
            </marker>
          </defs>
          {/* 0. QUAN HỆ DO `rules` KHAI — dưới cùng, dưới cả edge.
           *
           * W4B-2U §12. Trước wave này, một cảnh AND dựng ra ba widget rời:
           * công tắc A, công tắc B, đèn Đầu ra — không gì trên sân khấu nói ba
           * thứ đó liên quan nhau. Quan hệ CÓ tồn tại và ĐÃ được validate, nhưng
           * chỉ hiện dưới dạng CHỮ trong mục "QUY TẮC" của Giải thích
           * (`y = AND(A, B)`), tức đúng lỗi "quan hệ chở bằng prose".
           *
           * Đây KHÔNG phải renderer bịa quan hệ (thứ
           * `SIMULATION_VS_ILLUSTRATION_CONTRACT` cấm): mỗi đường vẽ ra đọc
           * thẳng từ `rule.inputs → rule.target` — cùng dữ liệu mà engine dùng
           * để TÍNH. Nếu spec không khai rule thì không có đường nào.
           *
           * Vẽ mảnh và nét đứt để phân biệt với `edge` — edge là đối tượng CÓ
           * THẬT trong mô hình (dây nối, đoạn thẳng), còn đây là PHỤ THUỘC TÍNH
           * TOÁN. Hai thứ khác loại thì không được trông giống nhau. */}
          {spec.rules.flatMap((r, ri) => {
            const t = pos[r.target];
            if (!t) return [];
            return (r.inputs ?? []).map((inputId) => {
              const s = pos[inputId];
              if (!s) return null;
              return (
                <line
                  key={`rule-${ri}-${inputId}`}
                  x1={s.x}
                  y1={s.y}
                  x2={t.x}
                  y2={t.y}
                  stroke="var(--ink-faint)"
                  strokeWidth={1.5}
                  strokeDasharray="4 5"
                  opacity={0.7}
                >
                  <title>{`${displayLabel(spec, inputId)} → ${displayLabel(spec, r.target)}`}</title>
                </line>
              );
            });
          })}
          {/* Toán tử đặt cạnh đích — nói QUAN HỆ LÀ GÌ, không chỉ "có liên quan". */}
          {spec.rules.map((r, ri) => {
            const t = pos[r.target];
            if (!t || !(r.inputs ?? []).some((i) => pos[i])) return null;
            const label =
              r.type === "boolean" ? (r.op ?? "").toUpperCase() : "Σ";
            if (!label) return null;
            return (
              <text
                key={`op-${ri}`}
                x={t.x}
                y={t.y - 34}
                textAnchor="middle"
                fontSize={11}
                fontWeight={600}
                fill="var(--ink-muted)"
              >
                {label}
              </text>
            );
          })}
          {/* 1. Cạnh (edge) — dưới cùng; chỉ khi edge + hai đầu đều visible (§6) */}
          {spec.objects
            .filter((o) => o.type === "edge" && isObjectRenderable(frame, o))
            .map((o) => {
              const a = pos[o.from ?? ""];
              const b = pos[o.to ?? ""];
              if (!a || !b) return null;
              const current = objectRole(state, o.id) === "current";
              const len = Math.hypot(b.x - a.x, b.y - a.y) || 1;
              // M8-PRE (S2): edge có chiều → lùi điểm cuối ra khỏi hình đích để
              // mũi tên không bị nút (r=26) che; điểm hình học nhỏ hơn nên lùi ít.
              const target = spec.objects.find((t) => t.id === o.to);
              const pad = o.directed
                ? target?.type === "node" && target.node_type
                  ? 28
                  : 16
                : 0;
              const ex = b.x - ((b.x - a.x) / len) * pad;
              const ey = b.y - ((b.y - a.y) / len) * pad;
              const drawLen = Math.hypot(ex - a.x, ey - a.y) || 1;
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
                    x2={ex}
                    y2={ey}
                    stroke={current ? "var(--primary)" : "var(--ink-secondary)"}
                    strokeWidth={current ? 4 : 2.5}
                    strokeLinecap={o.directed ? "butt" : "round"}
                    markerEnd={
                      o.directed
                        ? current
                          ? "url(#gen-arrow-current)"
                          : "url(#gen-arrow)"
                        : undefined
                    }
                    className={current ? "gen-edge-draw" : undefined}
                    style={
                      current
                        ? ({
                            ["--len" as string]: drawLen,
                            strokeDasharray: drawLen,
                          } as React.CSSProperties)
                        : undefined
                    }
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
                      {displayLabel(spec, o.id)}
                    </text>
                  )}
                </g>
              );
            })}
          {/* 2. Họ cấu trúc/nội dung (M7.12): luồng tài liệu */}
          {structuralEls}
          {/* 3. Object spatial ĐÃ HIỆN (completed) */}
          {spatialCompleted.map((o) =>
            renderObject(o, objectRole(state, o.id)),
          )}
          {/* 4. Object spatial VỪA TẠO (current) — nổi trên completed */}
          {spatialCurrent.map((o) => renderObject(o, objectRole(state, o.id)))}
          {/* 5. Nhãn chữ đứng riêng — trên node/edge, không bị che */}
          {labelsVisible.map((o) => renderObject(o, objectRole(state, o.id)))}
          {/* 6. Thực thể di chuyển (packet) trên cùng */}
          {spec.objects
            .filter(
              (o) => o.type === "moving_entity" && isObjectRenderable(frame, o),
            )
            .map((o) => {
              const nodeId = frame.entityPos[o.id];
              const np = nodeId ? pos[nodeId] : undefined;
              if (!np) return null;
              return (
                <circle
                  key={o.id}
                  cx={np.x}
                  cy={np.y - 38}
                  r={9}
                  fill="var(--accent-pink)"
                  stroke="#fff"
                  strokeWidth={2}
                  style={{ transition: "cx 0.4s ease, cy 0.4s ease" }}
                />
              );
            })}
        </svg>
      </div>
      {/* M7.14: InteractionFeedback — dẫn xuất của RULE engine, không phải chat.
          (SHELL-N) KHÔNG phải thuyết minh bước: đây là phản hồi cho THAO TÁC vừa
          rồi, một vai trò khác, nên nó giữ lớp riêng thay vì mượn `.narration-bar`. */}
      {state.feedback && (
        <div className="feedback-bar">{state.feedback.message}</div>
      )}
      {/* (SHELL-N) THUYẾT MINH BƯỚC đã về khe của shell (`narrate` ở `index.ts`).
          Còn lại ở đây là HƯỚNG DẪN THAO TÁC cho cảnh KHÔNG có timeline — vai trò
          khác (affordance, không phải tường thuật) và chỉ đúng khi KHÔNG ở chế độ
          Chỉnh sửa. `editMode` là trạng thái TRÌNH BÀY cục bộ của renderer, không
          nằm trong engine state (luật renderer-neutral, M7.FREEZE) — nên shell
          không thể biết, và câu này phải ở lại đây. */}
      {!editMode && state.timeline.length <= 1 && (
        <p className="stage-affordance">
          {toggleable.size > 0
            ? "Bấm vào các công tắc để thay đổi trạng thái và quan sát kết quả."
            : draggable.size > 0
              ? "Kéo các điểm có viền đứt để thay đổi hình và quan sát các cạnh cập nhật theo."
              : spec.title}
        </p>
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
  slider: "thanh trượt",
  color_swatch: "mẫu màu",
  array_strip: "dải mảng",
  metric_gauge: "đồng hồ đo",
  bar_chart: "biểu đồ cột",
  table_grid: "bảng dữ liệu",
  stack_view: "ngăn xếp",
  queue_view: "hàng đợi",
  tree_element: "nút cây",
  bit_register: "thanh ghi bit",
  logic_gate: "cổng logic",
  pointer: "con trỏ",
  coordinate_plane: "hệ tọa độ",
  moving_entity: "vật di chuyển",
  label: "nhãn",
  container: "khung chứa",
  group: "nhóm",
  heading: "tiêu đề",
  paragraph: "đoạn văn",
  text: "chữ",
};

/**
 * Tên hiển thị của object trong inspector: nội dung chữ (rút gọn, cho họ
 * structural/textual — heading/paragraph/... vốn không mang `.label`) >
 * displayLabel (M13 Task 11: id kỹ thuật thô KHÔNG BAO GIỜ là nhãn chính).
 */
function chipName(spec: SimulationSpec, o: SpecObject): string {
  if (STRUCTURAL_TYPES.has(o.type) && o.text) {
    return o.text.length > 32 ? `${o.text.slice(0, 32)}…` : o.text;
  }
  return displayLabel(spec, o.id);
}

function ObjChips({
  spec,
  objs,
}: {
  spec: SimulationSpec;
  objs: SpecObject[];
}) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
      {objs.map((o) => (
        <span key={o.id} className="obj-chip">
          {chipName(spec, o)}
          <span className="obj-chip-type">{TYPE_LABEL[o.type] ?? o.type}</span>
        </span>
      ))}
    </div>
  );
}

export function GenericInspector({ config: spec, state, dispatch }: Props) {
  const values = valuesOf(spec, state.base);
  const groups = inspectorGroups(state);
  const progressive = state.timeline.length > 1;
  const sliders = spec.objects.filter((o) => o.type === "slider");
  const buttons = spec.interactions.filter((it) => it.type === "button_action");
  const withValue = spec.objects.filter(
    (o) =>
      o.type !== "slider" &&
      (o.value !== undefined ||
        o.type === "lamp" ||
        o.type === "value_box" ||
        o.type === "color_swatch" ||
        o.type === "metric_gauge" ||
        o.type === "bit_register"),
  );

  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      {buttons.length > 0 && (
        <section className="card" style={{ padding: "var(--sp-md)" }}>
          <span className="eyebrow">THAO TÁC / HÀNH ĐỘNG</span>
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: 8,
              marginTop: "var(--sp-sm)",
            }}
          >
            {buttons.map((it, i) => (
              <button
                key={i}
                className="btn-primary"
                onClick={() => dispatch({ type: "step", delta: 1 })}
              >
                {it.label ?? `Thực hiện ${displayLabel(spec, it.target)}`}
              </button>
            ))}
          </div>
        </section>
      )}

      {sliders.length > 0 && (
        <section className="card" style={{ padding: "var(--sp-md)" }}>
          <span className="eyebrow">ĐIỀU KHIỂN THAM SỐ</span>
          <div
            className="stack"
            style={{ gap: "var(--sp-sm)", marginTop: "var(--sp-sm)" }}
          >
            {sliders.map((s) => {
              const curVal = Number(values[s.id] ?? s.min ?? 0);
              return (
                <div
                  key={s.id}
                  style={{ display: "flex", flexDirection: "column", gap: 4 }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      fontSize: 13,
                      fontWeight: 600,
                    }}
                  >
                    <span>{displayLabel(spec, s.id)}</span>
                    <span style={{ color: "var(--primary)" }}>
                      {curVal} {s.unit ?? ""}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={s.min ?? 0}
                    max={s.max ?? 100}
                    step={s.step ?? 1}
                    value={curVal}
                    onChange={(e) =>
                      dispatch({
                        type: "set_param",
                        name: s.id,
                        value: Number(e.target.value),
                      })
                    }
                    style={{ width: "100%", cursor: "pointer" }}
                  />
                </div>
              );
            })}
          </div>
        </section>
      )}

      <section className="card" style={{ padding: "var(--sp-md)" }}>
        <span className="eyebrow">ĐỐI TƯỢNG</span>
        {progressive ? (
          <div
            className="stack"
            style={{ gap: "var(--sp-sm)", marginTop: "var(--sp-sm)" }}
          >
            {groups.current.length > 0 && (
              <div>
                <span
                  className="obj-group-label"
                  style={{ color: "var(--primary)" }}
                >
                  Vừa tạo
                </span>
                <ObjChips spec={spec} objs={groups.current} />
              </div>
            )}
            {groups.completed.length > 0 && (
              <div>
                <span className="obj-group-label">Đã hiện</span>
                <ObjChips spec={spec} objs={groups.completed} />
              </div>
            )}
            {groups.hidden.length > 0 && (
              <div>
                <span
                  className="obj-group-label"
                  style={{ color: "var(--ink-faint)" }}
                >
                  Chưa xuất hiện
                </span>
                <ObjChips spec={spec} objs={groups.hidden} />
              </div>
            )}
          </div>
        ) : withValue.length > 0 ? (
          <div className="analysis-grid" style={{ marginTop: "var(--sp-sm)" }}>
            {withValue.map((o) => (
              <FragmentRow
                key={o.id}
                label={displayLabel(spec, o.id)}
                value={values[o.id] ?? 0}
              />
            ))}
          </div>
        ) : (
          <div style={{ marginTop: "var(--sp-sm)" }}>
            <ObjChips spec={spec} objs={spec.objects} />
          </div>
        )}
      </section>

      {spec.rules.length > 0 && (
        <section className="card" style={{ padding: "var(--sp-md)" }}>
          <span className="eyebrow">QUY TẮC</span>
          <ul
            style={{
              margin: "var(--sp-xs) 0 0 var(--sp-md)",
              fontSize: 14,
              color: "var(--ink-secondary)",
            }}
          >
            {spec.rules.map((r, i) => {
              const targetLabel = displayLabel(spec, r.target);
              const inputLabels = (r.inputs ?? []).map((id) =>
                displayLabel(spec, id),
              );
              return (
                <li key={i}>
                  {targetLabel} ={" "}
                  {r.type === "boolean"
                    ? `${r.op?.toUpperCase()}(${inputLabels.join(", ")})`
                    : r.type === "formula"
                      ? `${r.expression}`
                      : `Σ(${inputLabels.join(", ")} × trọng số)`}
                </li>
              );
            })}
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

function FragmentRow({
  label,
  value,
}: {
  label: string;
  value: number | string;
}) {
  const isColor = typeof value === "string" && value.startsWith("#");
  return (
    <>
      <span className="analysis-label">{label}</span>
      <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
        {isColor && (
          <span
            style={{
              display: "inline-block",
              width: 14,
              height: 14,
              borderRadius: 3,
              backgroundColor: value,
              border: "1px solid var(--ink-faint)",
            }}
          />
        )}
        <strong>{value}</strong>
      </span>
    </>
  );
}
