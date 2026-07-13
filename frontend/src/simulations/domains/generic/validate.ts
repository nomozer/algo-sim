import type { ConfigResult } from "../../types";
import {
  BOOL_OPS,
  CONTAINER_TYPES,
  DRAG_TARGET_TYPES,
  INTERACTION_TYPES,
  OBJECT_TYPES,
  PROCESS_TYPES,
  RULE_TYPES,
  SUPPORTED_DSL_VERSIONS,
  TEXT_CONTENT_TYPES,
  type BoolOp,
  type DragConstraints,
  type InteractionType,
  type ObjectType,
  type RevealStep,
  type RuleType,
  type SimulationSpec,
  type SpecInteraction,
  type SpecObject,
  type SpecProcess,
  type SpecRule,
} from "./model";

/**
 * Validator SimulationSpec (DSL v1) phía frontend — song song validator Python
 * (app/simulation/dsl/validator.py). Tách khỏi index.ts (M7.14) để patch.ts
 * dùng lại mà không tạo vòng import (index → ui → patch → validate).
 * KHÔNG eval/Function/arbitrary code — mọi primitive qua allowlist.
 */

const MAX_OBJECTS = 20;
const MAX_RULES = 20;
const MAX_INTERACTIONS = 20;
const MAX_PROCESSES = 8;
const MAX_PATH = 12;
const MAX_REVEAL_STEPS = 20;
const MAX_TEXT_LEN = 500;
const MAX_NESTING_DEPTH = 4;
const TOP_KEYS = new Set(["dsl_version", "title", "objects", "rules", "interactions", "processes", "notes"]);
const FORBIDDEN = ["steps", "timeline", "state", "frames", "transitions", "animations"];

function isObj(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function isNum(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v);
}

const DRAG_CONSTRAINT_KEYS = new Set(["bounds", "axis", "snap"]);
const DRAG_BOUND_KEYS = ["min_x", "max_x", "min_y", "max_y"] as const;

/** Kiểm "constraints" của drag (M7.13A) — trả constraints chuẩn hóa | null | thông báo lỗi. */
function validateDragConstraints(raw: unknown): DragConstraints | null | string {
  if (raw === undefined || raw === null) return null;
  if (!isObj(raw)) return 'drag "constraints" phải là đối tượng JSON.';
  for (const k of Object.keys(raw)) {
    if (!DRAG_CONSTRAINT_KEYS.has(k)) return `Trường lạ trong drag constraints: "${k}" (chỉ nhận bounds/axis/snap).`;
  }
  const out: DragConstraints = {};
  if (raw.bounds !== undefined) {
    if (!isObj(raw.bounds)) return `drag "bounds" chỉ nhận các khóa ${DRAG_BOUND_KEYS.join("/")}.`;
    const bounds: NonNullable<DragConstraints["bounds"]> = {};
    for (const k of Object.keys(raw.bounds)) {
      if (!(DRAG_BOUND_KEYS as readonly string[]).includes(k)) {
        return `drag "bounds" chỉ nhận các khóa ${DRAG_BOUND_KEYS.join("/")}.`;
      }
    }
    for (const k of DRAG_BOUND_KEYS) {
      const v = raw.bounds[k];
      if (v === undefined || v === null) continue;
      if (!isNum(v) || v < 0 || v > 100) return `drag bounds "${k}" phải là số trong 0–100.`;
      bounds[k] = v;
    }
    if ((bounds.min_x ?? 0) > (bounds.max_x ?? 100) || (bounds.min_y ?? 0) > (bounds.max_y ?? 100)) {
      return "drag bounds có min lớn hơn max.";
    }
    if (Object.keys(bounds).length > 0) out.bounds = bounds;
  }
  if (raw.axis !== undefined) {
    if (raw.axis !== "x" && raw.axis !== "y") return 'drag "axis" phải là x/y.';
    out.axis = raw.axis;
  }
  if (raw.snap !== undefined) {
    if (!isNum(raw.snap) || raw.snap <= 0) return 'drag "snap" phải là số dương.';
    out.snap = raw.snap;
  }
  return Object.keys(out).length > 0 ? out : null;
}

// Ownership rule (M7.13A, điều chỉnh #2): một thuộc tính biến đổi không được
// có HAI chủ điều khiển (interaction + process) khi chưa có arbitration policy.
const INTERACTION_CONTROLS: Record<string, string> = { drag: "position", toggle: "value" };
const PROCESS_CONTROLS: Record<string, { prop: string; field: "entity" }> = {
  move_along_path: { prop: "position", field: "entity" },
};

function ownershipConflict(interactions: SpecInteraction[], processes: SpecProcess[]): string | null {
  const ownedByProcess = new Set<string>();
  for (const p of processes) {
    const control = PROCESS_CONTROLS[p.type];
    if (control) ownedByProcess.add(`${control.prop}:${(p as { entity?: string })[control.field] ?? ""}`);
  }
  for (const it of interactions) {
    const prop = INTERACTION_CONTROLS[it.type];
    if (prop && ownedByProcess.has(`${prop}:${it.target}`)) {
      return `"${it.target}" đã được một process điều khiển (${prop}) — không thể vừa ${it.type} vừa chạy process trên cùng thuộc tính.`;
    }
  }
  return null;
}

export function validateGenericConfig(raw: unknown): ConfigResult<SimulationSpec> {
  if (!isObj(raw)) return { ok: false, error: "Spec không phải đối tượng JSON." };

  for (const k of FORBIDDEN) {
    if (k in raw) {
      return { ok: false, error: `Spec chứa khóa bị cấm "${k}" — diễn biến do engine tự sinh.` };
    }
  }
  for (const k of Object.keys(raw)) {
    if (!TOP_KEYS.has(k)) return { ok: false, error: `Trường lạ ở cấp cao nhất: "${k}".` };
  }
  // §9: reject phiên bản DSL không hỗ trợ (không âm thầm default)
  if (raw.dsl_version !== undefined && !SUPPORTED_DSL_VERSIONS.has(raw.dsl_version as string)) {
    return { ok: false, error: `dsl_version "${String(raw.dsl_version)}" không được hỗ trợ.` };
  }
  if (typeof raw.title !== "string" || !raw.title) {
    return { ok: false, error: '"title" phải là chuỗi.' };
  }

  const rawObjects = raw.objects;
  if (!Array.isArray(rawObjects) || rawObjects.length < 1 || rawObjects.length > MAX_OBJECTS) {
    return { ok: false, error: `"objects" phải có 1–${MAX_OBJECTS} phần tử.` };
  }
  const ids = new Set<string>();
  const objects: SpecObject[] = [];
  const byId: Record<string, SpecObject> = {};
  for (const o of rawObjects) {
    if (!isObj(o) || typeof o.id !== "string" || !o.id) return { ok: false, error: 'Mỗi object cần "id" chuỗi.' };
    if (ids.has(o.id)) return { ok: false, error: `Trùng object id "${o.id}".` };
    if (!(OBJECT_TYPES as readonly string[]).includes(o.type as string)) {
      return { ok: false, error: `Object type không hợp lệ: "${String(o.type)}".` };
    }
    ids.add(o.id);
    const obj: SpecObject = { id: o.id, type: o.type as ObjectType };
    for (const key of ["x", "y", "value", "weight"] as const) {
      if (typeof o[key] === "number" && Number.isFinite(o[key])) obj[key] = o[key] as number;
    }
    for (const key of ["label", "node_type", "from", "to", "text", "parent"] as const) {
      if (typeof o[key] === "string") obj[key] = o[key] as string;
    }
    objects.push(obj);
    byId[o.id] = obj;
  }
  // edge tham chiếu node có thật
  for (const o of objects) {
    if (o.type === "edge") {
      if (!o.from || !o.to || !ids.has(o.from) || !ids.has(o.to)) {
        return { ok: false, error: `edge "${o.id}" phải nối hai object có thật (from/to).` };
      }
    }
  }
  // M7.12: nội dung chữ + lồng nhau (structural/textual)
  for (const o of objects) {
    if (TEXT_CONTENT_TYPES.has(o.type)) {
      if (typeof o.text !== "string" || !o.text.trim()) {
        return { ok: false, error: `${o.type} "${o.id}" cần "text" (nội dung) không rỗng.` };
      }
      if (o.text.length > MAX_TEXT_LEN) {
        return { ok: false, error: `"text" của "${o.id}" quá dài (tối đa ${MAX_TEXT_LEN} ký tự).` };
      }
    }
    if (o.parent !== undefined) {
      if (!byId[o.parent] || !CONTAINER_TYPES.has(byId[o.parent].type)) {
        return { ok: false, error: `"${o.id}" có "parent" phải là id của container/group hợp lệ.` };
      }
    }
  }
  // chu trình chứa + độ sâu lồng nhau
  for (const o of objects) {
    let depth = 0;
    let cur: string | undefined = o.id;
    const seen = new Set<string>([o.id]);
    while (cur !== undefined && byId[cur].parent !== undefined) {
      cur = byId[cur].parent;
      depth += 1;
      if (cur === undefined) break;
      if (seen.has(cur)) return { ok: false, error: `Chuỗi "parent" của "${o.id}" tạo chu trình chứa.` };
      seen.add(cur);
      if (depth > MAX_NESTING_DEPTH) {
        return { ok: false, error: `Lồng nhau vượt độ sâu tối đa ${MAX_NESTING_DEPTH}.` };
      }
    }
  }

  const rawRules = Array.isArray(raw.rules) ? raw.rules : [];
  if (rawRules.length > MAX_RULES) return { ok: false, error: `Tối đa ${MAX_RULES} rule.` };
  const rules: SpecRule[] = [];
  for (const r of rawRules) {
    if (!isObj(r) || !(RULE_TYPES as readonly string[]).includes(r.type as string)) {
      return { ok: false, error: `Rule type không hợp lệ: "${String((r as Record<string, unknown>)?.type)}".` };
    }
    if (typeof r.target !== "string" || !ids.has(r.target)) {
      return { ok: false, error: `Rule tham chiếu target không tồn tại.` };
    }
    const inputs = Array.isArray(r.inputs) ? r.inputs : [];
    for (const inp of inputs) {
      if (typeof inp !== "string" || !ids.has(inp)) return { ok: false, error: `Rule tham chiếu input không tồn tại: "${String(inp)}".` };
    }
    const rule: SpecRule = { type: r.type as RuleType, target: r.target, inputs: inputs as string[] };
    if (rule.type === "boolean") {
      if (!(BOOL_OPS as readonly string[]).includes(r.op as string)) {
        return { ok: false, error: `boolean rule cần "op" thuộc ${BOOL_OPS.join("/")}.` };
      }
      rule.op = r.op as BoolOp;
    } else {
      const weights = Array.isArray(r.weights) ? r.weights : [];
      if (weights.length !== inputs.length || !weights.every((w) => typeof w === "number")) {
        return { ok: false, error: `weighted_sum cần "weights" cùng độ dài với "inputs".` };
      }
      rule.weights = weights as number[];
    }
    rules.push(rule);
  }
  // Cấm chu trình phụ thuộc rule (target ← input là target khác)
  const cycleErr = detectCycle(rules);
  if (cycleErr) return { ok: false, error: cycleErr };

  const rawInter = Array.isArray(raw.interactions) ? raw.interactions : [];
  if (rawInter.length > MAX_INTERACTIONS) return { ok: false, error: `Tối đa ${MAX_INTERACTIONS} interaction.` };
  const targets = ruleTargetsOf(rules);
  const interactions: SpecInteraction[] = [];
  for (const it of rawInter) {
    if (!isObj(it) || !(INTERACTION_TYPES as readonly string[]).includes(it.type as string)) {
      return { ok: false, error: `Interaction type không hợp lệ.` };
    }
    if (typeof it.target !== "string" || !ids.has(it.target)) {
      return { ok: false, error: `Interaction tham chiếu target không tồn tại.` };
    }
    const inter: SpecInteraction = {
      type: it.type as InteractionType,
      target: it.target,
      ...(typeof it.label === "string" ? { label: it.label } : {}),
    };
    if (it.type === "toggle") {
      if (targets.has(it.target)) {
        return { ok: false, error: `Không thể toggle "${it.target}" vì nó là giá trị dẫn xuất từ rule.` };
      }
      // M7.13A: toggle chỉ có nghĩa trên object CÓ value (0/1) — toggle một
      // node/điểm là interaction chết; muốn di chuyển điểm phải dùng drag.
      if (byId[it.target].value === undefined) {
        return {
          ok: false,
          error: `toggle "${it.target}" vô nghĩa vì object không có "value" khởi tạo — muốn học sinh DI CHUYỂN/KÉO điểm thì dùng interaction drag.`,
        };
      }
    } else {
      // drag (M7.13A) — allowlist target + constraints, song song validator Python
      const targetType = byId[it.target].type;
      if (!DRAG_TARGET_TYPES.has(targetType)) {
        return {
          ok: false,
          error: `drag chỉ áp cho object type ${[...DRAG_TARGET_TYPES].sort().join("/")} — "${it.target}" là ${targetType}.`,
        };
      }
      const c = validateDragConstraints(it.constraints);
      if (typeof c === "string") return { ok: false, error: c };
      if (c) inter.constraints = c;
    }
    interactions.push(inter);
  }

  const rawProc = Array.isArray(raw.processes) ? raw.processes : [];
  if (rawProc.length > MAX_PROCESSES) return { ok: false, error: `Tối đa ${MAX_PROCESSES} process.` };
  const processes: SpecProcess[] = [];
  for (const p of rawProc) {
    if (!isObj(p) || !(PROCESS_TYPES as readonly string[]).includes(p.type as string)) {
      return { ok: false, error: `Process type không hợp lệ.` };
    }
    if (p.type === "reveal_sequence") {
      const steps = p.steps;
      if (!Array.isArray(steps) || steps.length < 1 || steps.length > MAX_REVEAL_STEPS) {
        return { ok: false, error: `reveal_sequence "steps" phải có 1–${MAX_REVEAL_STEPS} bước.` };
      }
      const revealSteps: RevealStep[] = [];
      for (const st of steps) {
        if (!isObj(st) || !Array.isArray(st.objects) || st.objects.length < 1) {
          return { ok: false, error: `Mỗi reveal step cần "objects" không rỗng.` };
        }
        for (const oid of st.objects) {
          if (typeof oid !== "string" || !ids.has(oid)) {
            return { ok: false, error: `reveal step tham chiếu object không tồn tại: "${String(oid)}".` };
          }
        }
        // chặn field lạ trong step
        for (const k of Object.keys(st)) {
          if (k !== "objects" && k !== "narration") {
            return { ok: false, error: `Trường lạ trong reveal step: "${k}".` };
          }
        }
        revealSteps.push({
          objects: st.objects as string[],
          ...(typeof st.narration === "string" ? { narration: st.narration } : {}),
        });
      }
      processes.push({ type: "reveal_sequence", steps: revealSteps });
      continue;
    }
    // move_along_path
    if (typeof p.entity !== "string" || byId[p.entity]?.type !== "moving_entity") {
      return { ok: false, error: `Process cần "entity" là một moving_entity có thật.` };
    }
    if (!Array.isArray(p.path) || p.path.length < 2 || p.path.length > MAX_PATH) {
      return { ok: false, error: `Process "path" phải có 2–${MAX_PATH} nút.` };
    }
    for (const nid of p.path) {
      if (typeof nid !== "string" || byId[nid]?.type !== "node") {
        return { ok: false, error: `Process "path" phải toàn id của object type node.` };
      }
    }
    processes.push({ type: "move_along_path", entity: p.entity, path: p.path as string[] });
  }

  // M7.13A: ownership rule — một thuộc tính không có hai chủ điều khiển
  const ownErr = ownershipConflict(interactions, processes);
  if (ownErr) return { ok: false, error: ownErr };

  return {
    ok: true,
    config: {
      dsl_version: typeof raw.dsl_version === "string" && raw.dsl_version ? raw.dsl_version : "1.0",
      title: raw.title,
      objects,
      rules,
      interactions,
      processes,
      notes: typeof raw.notes === "string" ? raw.notes : null,
    },
  };
}

function ruleTargetsOf(rules: SpecRule[]): Set<string> {
  return new Set(rules.map((r) => r.target));
}

function detectCycle(rules: SpecRule[]): string | null {
  const targets = new Set(rules.map((r) => r.target));
  const deps: Record<string, string[]> = {};
  for (const r of rules) {
    deps[r.target] = (r.inputs ?? []).filter((i) => targets.has(i));
  }
  const state: Record<string, 0 | 1 | 2> = {};
  const visit = (n: string): boolean => {
    if (state[n] === 1) return true; // đang trong ngăn xếp → chu trình
    if (state[n] === 2) return false;
    state[n] = 1;
    for (const d of deps[n] ?? []) if (visit(d)) return true;
    state[n] = 2;
    return false;
  };
  for (const t of targets) if (visit(t)) return "Rule có phụ thuộc vòng (circular dependency).";
  return null;
}
