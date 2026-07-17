/**
 * Generic rule-based simulation — DSL v1 (M6).
 * AI khai báo semantics (objects/rules/interactions/processes); engine tất định
 * tính state, giá trị dẫn xuất, timeline và render model. KHÔNG eval, KHÔNG
 * arbitrary code — mọi primitive đều có allowlist + validator.
 */

export const DSL_VERSION = "1.0";
export const SUPPORTED_DSL_VERSIONS = new Set(["1.0"]);

export const OBJECT_TYPES = [
  "switch",
  "lamp",
  "value_box",
  "node",
  "edge",
  "moving_entity",
  "label",
  // structural/textual (M7.12)
  "container",
  "group",
  "heading",
  "paragraph",
  "text",
] as const;
export type ObjectType = (typeof OBJECT_TYPES)[number];

/** Type có thể CHỨA object con (qua parent). */
export const CONTAINER_TYPES = new Set<string>(["container", "group"]);
/** Type mang nội dung chữ dài trong "text". */
export const TEXT_CONTENT_TYPES = new Set<string>(["heading", "paragraph", "text"]);
/** Type thuộc họ cấu trúc/nội dung (M7.12) — render theo luồng tài liệu. */
export const STRUCTURAL_TYPES = new Set<string>([
  "container",
  "group",
  "heading",
  "paragraph",
  "text",
]);

export const RULE_TYPES = ["boolean", "weighted_sum"] as const;
export type RuleType = (typeof RULE_TYPES)[number];

export const BOOL_OPS = ["and", "or", "not", "xor"] as const;
export type BoolOp = (typeof BOOL_OPS)[number];

export const INTERACTION_TYPES = ["toggle", "drag"] as const;
export type InteractionType = (typeof INTERACTION_TYPES)[number];

/** Type được phép làm target của drag (M7.13A) — v1 chỉ node; song song manifest. */
export const DRAG_TARGET_TYPES = new Set<string>(["node"]);

export const PROCESS_TYPES = ["move_along_path", "reveal_sequence"] as const;
export type ProcessType = (typeof PROCESS_TYPES)[number];

/** Họ process DIỄN BIẾN theo thời gian — song song manifest.temporal_process_types(). */
export const TEMPORAL_PROCESS_TYPES = new Set<string>(["move_along_path", "reveal_sequence"]);

export interface SpecObject {
  id: string;
  type: ObjectType;
  x?: number;
  y?: number;
  label?: string;
  value?: number;
  node_type?: string;
  from?: string;
  to?: string;
  /** Edge CÓ CHIỀU (luồng dữ liệu / request→response) — renderer vẽ mũi tên from → to (M8-PRE S2). */
  directed?: boolean;
  /** Nội dung chữ cho heading/paragraph/text (M7.12). */
  text?: string;
  /** id của container/group chứa object này (lồng nhau — M7.12). */
  parent?: string;
}

export interface SpecRule {
  type: RuleType;
  op?: BoolOp;
  inputs?: string[];
  weights?: number[];
  target: string;
}

/** Ràng buộc hình học của drag (M7.13A) — thuần hình học, không biết domain. */
export interface DragConstraints {
  bounds?: { min_x?: number; max_x?: number; min_y?: number; max_y?: number };
  axis?: "x" | "y";
  snap?: number;
}

export interface SpecInteraction {
  type: InteractionType;
  target: string;
  label?: string;
  /** Chỉ có nghĩa với drag. */
  constraints?: DragConstraints;
}

/** Di chuyển một thực thể dọc một đường (các node). */
export interface MoveProcess {
  type: "move_along_path";
  entity: string;
  path: string[];
}

/** Một bước hé lộ: các object bắt đầu xuất hiện ở bước này. */
export interface RevealStep {
  objects: string[];
  narration?: string;
}

/** Hình thành cảnh từng bước (M7.7): mỗi step reveal thêm object. */
export interface RevealProcess {
  type: "reveal_sequence";
  steps: RevealStep[];
}

export type SpecProcess = MoveProcess | RevealProcess;

export interface SimulationSpec {
  dsl_version: string;
  title: string;
  objects: SpecObject[];
  rules: SpecRule[];
  interactions: SpecInteraction[];
  processes: SpecProcess[];
  notes?: string | null;
}

/** Một khung hình do engine dựng từ process (KHÔNG từ LLM). */
export interface Frame {
  /** Object đang tồn tại/hiển thị ở khung này — serializable string[] (M7.7). */
  visibleIds: string[];
  entityPos: Record<string, string>; // entityId → nodeId
  narration: string;
}

/**
 * Feedback tương tác runtime (M7.14) — kênh RIÊNG, không trộn với PatchResult
 * (docs/CORRECTNESS.md §3). Message là dẫn xuất của RULE tất định engine đang
 * có, không phải văn LLM; chỉ nói điều engine đo được (vd chạm biên vùng
 * tương tác) — TUYỆT ĐỐI không suy diễn ngữ nghĩa chưa có ("M phải thuộc BC").
 */
export interface InteractionFeedback {
  rule: "drag_bounds";
  message: string;
}

export interface GenericState {
  readonly spec: SimulationSpec;
  /** Giá trị GỐC của các object bật/tắt được (switch...) — toggle sửa ở đây. */
  base: Record<string, number>;
  /**
   * Vị trí object (tọa độ domain 0–100) — STATE-OWNED (M7.13A): khởi tạo từ
   * layout của spec, chỉ biến đổi qua action "move" (pure). Renderer ĐỌC từ
   * đây, không tự tính lại — nhờ đó edge tự bám theo hai đầu khi kéo.
   * Họ structural/textual không nằm ở đây (layout theo luồng tài liệu).
   */
  pos: Record<string, { x: number; y: number }>;
  /** Timeline do engine dựng — dài 1 nếu không có process (exploratory). */
  timeline: Frame[];
  cursor: number;
  /** Feedback tương tác gần nhất — null khi không có gì cần nói (M7.14). */
  feedback?: InteractionFeedback | null;
}

/* ── Engine tất định ─────────────────────────────────────── */

/**
 * M13 §3.4 — lỗi runtime TYPED tại ranh giới evaluator, song song
 * `GenericEvaluationError` bên `backend/app/simulation/generic_engine.py`.
 * Sự cố gốc: `weighted_sum` ăn input là id CẠNH → runtime lặng lẽ hoá 0 →
 * cảnh "chạy" 10/10 bước nhưng kết quả sai câm lặng. Từ M13, engine KHÔNG
 * BAO GIỜ hoá một giá trị thiếu/không xác định thành 0 — nó ném lỗi typed.
 */
export class GenericExecutionError extends Error {
  readonly code:
    | "invalid_numeric_source"
    | "missing_weight"
    | "unresolved_dependency_after_bound"
    | "non_finite_numeric_value";

  constructor(
    code: GenericExecutionError["code"],
    detail: string,
  ) {
    super(`${code}: ${detail}`);
    this.name = "GenericExecutionError";
    this.code = code;
  }
}

export function ruleTargets(spec: SimulationSpec): Set<string> {
  return new Set(spec.rules.map((r) => r.target));
}

/** Giá trị gốc ban đầu: object có value và KHÔNG phải target của rule nào. */
export function initialBase(spec: SimulationSpec): Record<string, number> {
  const targets = ruleTargets(spec);
  const base: Record<string, number> = {};
  for (const o of spec.objects) {
    if (o.value !== undefined && !targets.has(o.id)) base[o.id] = o.value;
  }
  return base;
}

/**
 * M13: mọi input PHẢI đã có trong `values` — thiếu là lỗi typed, không bao
 * giờ coi ngầm là 0. Nhánh `invalid_numeric_source` này KHÔNG reachable qua
 * `valuesOf` bình thường (nó chỉ gọi evalRule khi mọi input đã resolve —
 * xem vòng lặp bên dưới); giữ lại cho parity với backend + phòng thủ nếu
 * evalRule bị gọi trực tiếp từ nơi khác trong tương lai.
 */
function evalRule(rule: SpecRule, values: Record<string, number>): number {
  const inputs: number[] = [];
  for (const id of rule.inputs ?? []) {
    if (!(id in values)) {
      throw new GenericExecutionError("invalid_numeric_source", `input "${id}" chưa có giá trị`);
    }
    inputs.push(values[id]);
  }
  if (rule.type === "boolean") {
    const bits = inputs.map((v) => (v >= 1 ? 1 : 0));
    switch (rule.op) {
      case "and":
        return bits.every((b) => b === 1) ? 1 : 0;
      case "or":
        return bits.some((b) => b === 1) ? 1 : 0;
      case "xor":
        return bits.reduce<number>((s, b) => s + b, 0) % 2;
      case "not":
        return bits[0] === 1 ? 0 : 1;
      default:
        return 0;
    }
  }
  // weighted_sum
  const weights = rule.weights ?? [];
  if (weights.length !== inputs.length) {
    throw new GenericExecutionError("missing_weight", `rule "${rule.target}" thiếu weight`);
  }
  const result = inputs.reduce((sum, v, i) => sum + v * weights[i], 0);
  if (!Number.isFinite(result)) {
    throw new GenericExecutionError("non_finite_numeric_value", `rule "${rule.target}" ra ${result}`);
  }
  return result;
}

/**
 * Giá trị đầy đủ = base + giá trị dẫn xuất, áp rule đến khi ổn định.
 *
 * M13 §3.4 — BA TRẠNG THÁI: KHÔNG seed target = 0 nữa (trước đây xoá nhòa
 * "chưa resolve" với "đã tính ra 0" — đúng gốc sự cố "Dijkstra" giả). Một
 * target chưa resolve là UNRESOLVED (vắng mặt trong `values`); rule chỉ
 * chạy khi MỌI input đã resolve. DAG hợp lệ hội tụ trong ≤ len(rules) lượt
 * (validator đã cấm chu trình); còn sót sau bound → lỗi typed thay vì hoá 0
 * im lặng.
 *
 * Thuật toán PORT ĐÚNG bản Python đã merge (`generic_engine.py:values_of`,
 * đã qua review Task 4 — bản snippet cũ trong plan có bug `pending = still`
 * đặt SAU `if (!pending.length) break`, khiến MỌI spec có ≥1 rule bắn oan
 * `unresolved_dependency_after_bound`). Ở đây `pending = still` luôn chạy
 * TRƯỚC break/progress check.
 */
export function valuesOf(spec: SimulationSpec, base: Record<string, number>): Record<string, number> {
  const values: Record<string, number> = { ...base };
  const rules = spec.rules;
  let pending: SpecRule[] = [...rules];
  for (let iter = 0; iter <= rules.length; iter++) {
    const still: SpecRule[] = [];
    for (const rule of pending) {
      const inputs = rule.inputs ?? [];
      if (inputs.every((id) => id in values)) {
        values[rule.target] = evalRule(rule, values);
      } else {
        still.push(rule);
      }
    }
    const progressed = still.length < pending.length;
    pending = still; // PHẢI cập nhật TRƯỚC break/progress check (Task 4 bug fix)
    if (pending.length === 0) break;
    if (!progressed) {
      const missing = new Set<string>();
      for (const r of pending) {
        for (const id of r.inputs ?? []) if (!(id in values)) missing.add(id);
      }
      throw new GenericExecutionError(
        "unresolved_dependency_after_bound",
        `không resolve được: ${[...missing].sort().join(", ")}`,
      );
    }
  }
  if (pending.length > 0) {
    throw new GenericExecutionError("unresolved_dependency_after_bound", "vượt bound evaluation");
  }
  return values;
}

/** M13 workstream C: tên hiển thị learner-facing — id nội bộ KHÔNG BAO GIỜ là nhãn chính. */
const TYPE_DISPLAY_VI: Record<string, string> = {
  switch: "Công tắc", lamp: "Đèn", value_box: "Ô giá trị", node: "Điểm",
  edge: "Đoạn nối", moving_entity: "Vật di chuyển", label: "Nhãn", container: "Khung",
  group: "Nhóm", heading: "Tiêu đề", paragraph: "Đoạn văn", text: "Chữ",
};

/** Dạng định danh kỹ thuật theo HÌNH THỨC (không keyword): snake/kebab-case
 * chuỗi ASCII — bắt node_A, edge_AB, calc_path_ABC; cho qua "Đường A-B-C"
 * (có dấu cách/ký tự tiếng Việt), "AB" (không có _/-). */
const TECHNICAL_ID_FORM = /^[A-Za-z0-9]+([_-][A-Za-z0-9]+)+$/;

function isTechnicalLabel(label: string | undefined, id: string): boolean {
  if (!label) return true; // thiếu
  if (label === id) return true; // LLM điền label = id (ca Dijkstra thật)
  return TECHNICAL_ID_FORM.test(label) && !label.includes(" ");
}

export function displayLabel(spec: SimulationSpec, id: string): string {
  const o = spec.objects.find((x) => x.id === id);
  if (!o) return id; // sau validate không xảy ra; giữ để total
  if (!isTechnicalLabel(o.label, id)) return o.label!;
  const sameType = spec.objects.filter((x) => x.type === o.type);
  const base = TYPE_DISPLAY_VI[o.type] ?? o.type;
  return sameType.length > 1 ? `${base} ${sameType.findIndex((x) => x.id === id) + 1}` : base;
}

function objLabel(spec: SimulationSpec, id: string): string {
  return displayLabel(spec, id);
}

/** Object được quản lý bởi reveal (chỉ xuất hiện ở step của nó). */
function managedByReveal(spec: SimulationSpec): Set<string> {
  const managed = new Set<string>();
  for (const proc of spec.processes) {
    if (proc.type === "reveal_sequence") {
      for (const step of proc.steps) for (const id of step.objects) managed.add(id);
    }
  }
  return managed;
}

/**
 * Dựng timeline từ processes (M7.7).
 * - Không có process → một khung TĨNH, mọi object visible (tương thích ngược).
 * - Có reveal_sequence → visibility hình thành từng bước, TÍCH LŨY tất định:
 *   visible(k) = visible(k-1) ∪ objects(step k). Object KHÔNG nằm trong reveal
 *   nào là "nền", visible ngay từ đầu.
 * - Process chạy theo ĐÚNG thứ tự khai báo trong spec.
 * visibleIds luôn sắp theo thứ tự khai báo object → serializable, tất định.
 */
export function buildTimeline(spec: SimulationSpec): Frame[] {
  const allIds = spec.objects.map((o) => o.id);
  const orderVisible = (set: Set<string>): string[] => allIds.filter((id) => set.has(id));

  if (spec.processes.length === 0) {
    return [{ visibleIds: [...allIds], entityPos: {}, narration: spec.title }];
  }

  const managed = managedByReveal(spec);
  const hasReveal = managed.size > 0;
  // Nền: nếu không có reveal → tất cả; nếu có → object không bị reveal quản lý
  const visible = new Set(hasReveal ? allIds.filter((id) => !managed.has(id)) : allIds);
  const entityPos: Record<string, string> = {};
  const frames: Frame[] = [];

  for (const proc of spec.processes) {
    if (proc.type === "reveal_sequence") {
      for (const step of proc.steps) {
        for (const id of step.objects) visible.add(id); // tích lũy
        frames.push({
          visibleIds: orderVisible(visible),
          entityPos: { ...entityPos },
          narration: step.narration ?? `Hé lộ: ${step.objects.map((id) => objLabel(spec, id)).join(", ")}.`,
        });
      }
    } else {
      // move_along_path — thực thể phải visible khi di chuyển
      visible.add(proc.entity);
      const path = proc.path;
      entityPos[proc.entity] = path[0];
      frames.push({
        visibleIds: orderVisible(visible),
        entityPos: { ...entityPos },
        narration: `Tạo ${objLabel(spec, proc.entity)} tại ${objLabel(spec, path[0])}.`,
      });
      for (let k = 1; k < path.length; k++) {
        const last = k === path.length - 1;
        entityPos[proc.entity] = path[k];
        frames.push({
          visibleIds: orderVisible(visible),
          entityPos: { ...entityPos },
          narration: last
            ? `${objLabel(spec, proc.entity)} tới đích ${objLabel(spec, path[k])}. Hoàn tất!`
            : `${objLabel(spec, proc.entity)} chuyển tới ${objLabel(spec, path[k])}.`,
        });
      }
    }
  }
  return frames;
}

export function currentFrame(state: GenericState): Frame {
  return state.timeline[Math.max(0, Math.min(state.cursor, state.timeline.length - 1))];
}

/** Object có được render ở khung này không (gating hiển thị — M7.7). */
export function isVisible(frame: Frame, id: string): boolean {
  return frame.visibleIds.includes(id);
}

/**
 * Object có nên vẽ không: phải visible; riêng edge/relation cần CẢ HAI đầu
 * (from/to) cũng visible — tránh đường lơ lửng (ràng buộc §6). Object có parent
 * chỉ vẽ khi container cha cũng visible — tránh nội dung lơ lửng ngoài khung (M7.12).
 */
export function isObjectRenderable(frame: Frame, obj: SpecObject): boolean {
  if (!isVisible(frame, obj.id)) return false;
  if (obj.type === "edge") {
    return !!obj.from && !!obj.to && isVisible(frame, obj.from) && isVisible(frame, obj.to);
  }
  if (obj.parent) return isVisible(frame, obj.parent);
  return true;
}

/** Object con trực tiếp của một container/group, theo thứ tự khai báo (M7.12). */
export function childrenOf(spec: SimulationSpec, parentId: string): SpecObject[] {
  return spec.objects.filter((o) => o.parent === parentId);
}

/** Root của họ cấu trúc (type structural/textual, không có parent) — điểm bắt đầu luồng render. */
export function structuralRoots(spec: SimulationSpec): SpecObject[] {
  return spec.objects.filter((o) => STRUCTURAL_TYPES.has(o.type) && !o.parent);
}

/** Vị trí object để vẽ: dùng x,y nếu có; nếu thiếu, auto-grid theo index. */
export function positionOf(obj: SpecObject, index: number): { x: number; y: number } {
  if (typeof obj.x === "number" && typeof obj.y === "number") return { x: obj.x, y: obj.y };
  const perRow = 4;
  return { x: 12 + (index % perRow) * 26, y: 20 + Math.floor(index / perRow) * 30 };
}

/* ── Vị trí state-owned + drag (M7.13A) ───────────────────────── */

/**
 * Layout khởi tạo (tọa độ domain 0–100) cho mọi object KHÔNG thuộc họ
 * structural (họ đó layout theo luồng tài liệu, không có tọa độ tự do).
 * Đây là logic dựng map `pos` cũ của renderer, dời vào engine để state sở hữu.
 */
export function layoutPositions(spec: SimulationSpec): Record<string, { x: number; y: number }> {
  const pos: Record<string, { x: number; y: number }> = {};
  spec.objects.forEach((o, i) => {
    if (!STRUCTURAL_TYPES.has(o.type)) pos[o.id] = positionOf(o, i);
  });
  return pos;
}

/** Các object có interaction drag khai trong spec. */
export function dragTargets(spec: SimulationSpec): Set<string> {
  return new Set(spec.interactions.filter((it) => it.type === "drag").map((it) => it.target));
}

function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}

/**
 * Action "move" (pure) — engine là nơi DUY NHẤT quyết định một cú kéo có hợp
 * lệ không (điều chỉnh #3): target tồn tại + có drag khai trong spec + type
 * thuộc allowlist + đang visible ở frame hiện tại; rồi snap/axis/clamp theo
 * constraints. Không hợp lệ → trả state cũ (no-op), không ném lỗi.
 */
export function applyMove(state: GenericState, target: string, x: number, y: number): GenericState {
  const obj = state.spec.objects.find((o) => o.id === target);
  if (!obj || !DRAG_TARGET_TYPES.has(obj.type)) return state;
  const interaction = state.spec.interactions.find((it) => it.type === "drag" && it.target === target);
  if (!interaction) return state;
  if (!isVisible(currentFrame(state), target)) return state;
  const prev = state.pos[target];
  if (!prev) return state;

  const c = interaction.constraints ?? {};
  let nx = c.axis === "y" ? prev.x : x;
  let ny = c.axis === "x" ? prev.y : y;
  if (c.snap && c.snap > 0) {
    nx = Math.round(nx / c.snap) * c.snap;
    ny = Math.round(ny / c.snap) * c.snap;
  }
  const cx = clamp(nx, c.bounds?.min_x ?? 0, c.bounds?.max_x ?? 100);
  const cy = clamp(ny, c.bounds?.min_y ?? 0, c.bounds?.max_y ?? 100);
  // M7.14: chạm biên bounds KHAI TRONG SPEC → feedback từ rule tất định.
  // Message chỉ nói điều engine đo được — không suy diễn ngữ nghĩa hình học.
  const hitBounds = c.bounds !== undefined && (cx !== nx || cy !== ny);
  const feedback: InteractionFeedback | null = hitBounds
    ? { rule: "drag_bounds", message: "Đối tượng này chỉ di chuyển được trong vùng tương tác cho phép." }
    : null;
  const samePos = cx === prev.x && cy === prev.y;
  const sameFeedback = (state.feedback ?? null) === null ? feedback === null : state.feedback?.rule === feedback?.rule;
  if (samePos && sameFeedback) return state;
  return {
    ...state,
    pos: samePos ? state.pos : { ...state.pos, [target]: { x: cx, y: cy } },
    feedback,
  };
}

/* ── Edit tăng dần (M7.14) — vị trí trống + chuyển state sang spec mới ── */

/**
 * Vị trí trống tất định cho object mới: quét lưới 10×10 trong domain 0–100,
 * ưu tiên ô gần trọng tâm các vị trí hiện có, cách mọi object ≥ MIN_DIST.
 * Không cần layout hoàn hảo — chỉ cần không đè rõ ràng lên object cũ.
 */
export function findFreePosition(
  taken: { x: number; y: number }[],
  hint?: { x: number; y: number },
): { x: number; y: number } {
  const MIN_DIST = 12;
  const free = (x: number, y: number) => taken.every((p) => Math.hypot(p.x - x, p.y - y) >= MIN_DIST);
  if (hint) {
    const hx = clamp(hint.x, 5, 95);
    const hy = clamp(hint.y, 5, 95);
    if (free(hx, hy)) return { x: hx, y: hy };
  }
  const center = taken.length
    ? {
        x: taken.reduce((s, p) => s + p.x, 0) / taken.length,
        y: taken.reduce((s, p) => s + p.y, 0) / taken.length,
      }
    : { x: 50, y: 50 };
  const candidates: { x: number; y: number }[] = [];
  for (let y = 10; y <= 90; y += 10) for (let x = 10; x <= 90; x += 10) candidates.push({ x, y });
  candidates.sort((a, b) => {
    const da = Math.hypot(a.x - center.x, a.y - center.y);
    const db = Math.hypot(b.x - center.x, b.y - center.y);
    return da - db || a.y - b.y || a.x - b.x; // tie-break tất định
  });
  for (const cnd of candidates) if (free(cnd.x, cnd.y)) return cnd;
  return { x: 50, y: 50 };
}

/**
 * Dựng state MỚI từ spec đã patch (M7.14) — config bất biến được THAY THẾ
 * nguyên khối, state rebuild nhưng GIỮ những gì người học đã làm:
 * - pos của id còn sống (vị trí đã kéo không mất);
 * - base (giá trị toggle) của id còn sống;
 * - cursor clamp vào timeline mới.
 * Object mới: dùng x/y trong spec nếu có (LLM/click đã chọn), không thì
 * findFreePosition — không đè lên object cũ.
 */
export function applyEditedSpec(state: GenericState, newSpec: SimulationSpec): GenericState {
  const base = initialBase(newSpec);
  for (const id of Object.keys(base)) {
    if (id in state.base) base[id] = state.base[id];
  }
  const pos: Record<string, { x: number; y: number }> = {};
  const taken: { x: number; y: number }[] = [];
  newSpec.objects.forEach((o, i) => {
    if (STRUCTURAL_TYPES.has(o.type)) return;
    let p = state.pos[o.id];
    if (!p && typeof o.x === "number" && typeof o.y === "number") p = { x: o.x, y: o.y };
    if (!p && o.type !== "edge") p = findFreePosition(taken);
    if (!p) p = positionOf(o, i); // edge: vị trí không dùng để vẽ (derive từ hai đầu)
    pos[o.id] = p;
    if (o.type !== "edge") taken.push(p);
  });
  const timeline = buildTimeline(newSpec);
  return {
    spec: newSpec,
    base,
    pos,
    timeline,
    cursor: Math.max(0, Math.min(state.cursor, timeline.length - 1)),
    feedback: null,
  };
}

/**
 * Bao (domain 0–100) của các object spatial ĐANG VISIBLE — nguyên liệu cho
 * fit-view (M7.14). null khi không có gì để fit (cảnh structural flow hoặc
 * chưa object nào hiện). Chỉ tính tâm vị trí — renderer tự cộng padding pixel.
 */
export function visibleContentBounds(
  state: GenericState,
): { minX: number; minY: number; maxX: number; maxY: number } | null {
  const frame = currentFrame(state);
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const o of state.spec.objects) {
    if (o.type === "edge" || STRUCTURAL_TYPES.has(o.type)) continue;
    if (!isVisible(frame, o.id)) continue;
    const p = state.pos[o.id];
    if (!p) continue;
    minX = Math.min(minX, p.x);
    minY = Math.min(minY, p.y);
    maxX = Math.max(maxX, p.x);
    maxY = Math.max(maxY, p.y);
  }
  if (!Number.isFinite(minX)) return null;
  return { minX, minY, maxX, maxY };
}

/* ── Trạng thái hiển thị theo bước (M7.10) — dữ liệu THUẦN, dùng lại cho 2D lẫn 3D ── */

export type ObjectRole = "current" | "completed" | "hidden";

/**
 * Object VỪA XUẤT HIỆN ở bước hiện tại = visible(cursor) − visible(cursor−1).
 * Dẫn xuất trực tiếp từ timeline, không lưu state thừa (§3, §9).
 * Cảnh tĩnh (timeline 1 khung) → không có "bước vừa hiện" → rỗng.
 */
export function currentStepObjectIds(state: GenericState): string[] {
  if (state.timeline.length <= 1) return [];
  const cur = currentFrame(state).visibleIds;
  const prev = state.cursor > 0 ? state.timeline[state.cursor - 1].visibleIds : [];
  const prevSet = new Set(prev);
  return cur.filter((id) => !prevSet.has(id));
}

/** Vai trò hiển thị của một object ở bước hiện tại (engine quyết định, không phải renderer). */
export function objectRole(state: GenericState, id: string): ObjectRole {
  if (!isVisible(currentFrame(state), id)) return "hidden";
  if (state.timeline.length <= 1) return "completed";
  return currentStepObjectIds(state).includes(id) ? "current" : "completed";
}

/** Nhóm object cho Inspector: vừa tạo / đã hiện / chưa xuất hiện. */
export function inspectorGroups(state: GenericState): {
  current: SpecObject[];
  completed: SpecObject[];
  hidden: SpecObject[];
} {
  const visible = new Set(currentFrame(state).visibleIds);
  const cur = new Set(currentStepObjectIds(state));
  const groups = { current: [] as SpecObject[], completed: [] as SpecObject[], hidden: [] as SpecObject[] };
  for (const o of state.spec.objects) {
    if (!visible.has(o.id)) groups.hidden.push(o);
    else if (cur.has(o.id)) groups.current.push(o);
    else groups.completed.push(o);
  }
  return groups;
}
