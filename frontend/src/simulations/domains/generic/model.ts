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

export const INTERACTION_TYPES = ["toggle"] as const;
export type InteractionType = (typeof INTERACTION_TYPES)[number];

export const PROCESS_TYPES = ["move_along_path", "reveal_sequence"] as const;
export type ProcessType = (typeof PROCESS_TYPES)[number];

export interface SpecObject {
  id: string;
  type: ObjectType;
  x?: number;
  y?: number;
  label?: string;
  value?: number;
  weight?: number;
  node_type?: string;
  from?: string;
  to?: string;
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

export interface SpecInteraction {
  type: InteractionType;
  target: string;
  label?: string;
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

export interface GenericState {
  readonly spec: SimulationSpec;
  /** Giá trị GỐC của các object bật/tắt được (switch...) — toggle sửa ở đây. */
  base: Record<string, number>;
  /** Timeline do engine dựng — dài 1 nếu không có process (exploratory). */
  timeline: Frame[];
  cursor: number;
}

/* ── Engine tất định ─────────────────────────────────────── */

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

function evalRule(rule: SpecRule, values: Record<string, number>): number {
  const inputs = (rule.inputs ?? []).map((id) => values[id] ?? 0);
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
  return inputs.reduce((sum, v, i) => sum + v * (weights[i] ?? 0), 0);
}

/** Giá trị đầy đủ = base + giá trị dẫn xuất (áp rule đến khi ổn định). */
export function valuesOf(spec: SimulationSpec, base: Record<string, number>): Record<string, number> {
  const values: Record<string, number> = { ...base };
  for (const t of ruleTargets(spec)) if (!(t in values)) values[t] = 0;
  // Lặp tối đa (số rule + 1) lần — đủ hội tụ cho DAG, validator đã cấm chu trình
  for (let iter = 0; iter <= spec.rules.length; iter++) {
    let changed = false;
    for (const rule of spec.rules) {
      const v = evalRule(rule, values);
      if (values[rule.target] !== v) {
        values[rule.target] = v;
        changed = true;
      }
    }
    if (!changed) break;
  }
  return values;
}

function objLabel(spec: SimulationSpec, id: string): string {
  const o = spec.objects.find((x) => x.id === id);
  return o?.label ?? id;
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
