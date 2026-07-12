import { registerSimulation } from "../../registry";
import type { ConfigResult, SimAction, SimulationModule } from "../../types";
import {
  BOOL_OPS,
  CONTAINER_TYPES,
  INTERACTION_TYPES,
  OBJECT_TYPES,
  PROCESS_TYPES,
  RULE_TYPES,
  SUPPORTED_DSL_VERSIONS,
  TEXT_CONTENT_TYPES,
  buildTimeline,
  currentFrame,
  initialBase,
  valuesOf,
  type BoolOp,
  type GenericState,
  type ObjectType,
  type RuleType,
  type SimulationSpec,
  type SpecInteraction,
  type SpecObject,
  type SpecProcess,
  type SpecRule,
  type RevealStep,
} from "./model";
import { GenericInspector, GenericWorkspace } from "./ui";

/**
 * generic.rule_scene — engine tổng quát chạy SimulationSpec (DSL v1) do AI
 * compose. Timeline optional (có process → progressive; không → exploratory).
 * KHÔNG eval/Function/arbitrary code — mọi primitive qua allowlist + validator.
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

function validateGenericConfig(raw: unknown): ConfigResult<SimulationSpec> {
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
    if (targets.has(it.target)) {
      return { ok: false, error: `Không thể toggle "${it.target}" vì nó là giá trị dẫn xuất từ rule.` };
    }
    interactions.push({ type: "toggle", target: it.target, ...(typeof it.label === "string" ? { label: it.label } : {}) });
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

export function makeGenericModule(): SimulationModule<SimulationSpec, GenericState> {
  return {
    id: "generic.rule_scene",
    domain: "generic",
    title: "Mô phỏng tổng quát (AI tự dựng)",
    interactionMode: "hybrid",
    supportedVisualModes: ["2d"],

    validateConfig: validateGenericConfig,

    init: (spec) => ({ spec, base: initialBase(spec), timeline: buildTimeline(spec), cursor: 0 }),

    apply: (state, action: SimAction) => {
      if (action.type === "toggle") {
        if (action.target in state.base) {
          const cur = state.base[action.target];
          return { ...state, base: { ...state.base, [action.target]: cur >= 1 ? 0 : 1 } };
        }
      }
      return state;
    },

    // Luôn khai timeline; SimulationControls chỉ hiện nút bước khi stepCount > 1
    timeline: {
      stepCount: (s) => s.timeline.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: Math.max(0, Math.min(step, s.timeline.length - 1)) }),
    },

    getExplainContext: (state, spec) => {
      const values = valuesOf(spec, state.base);
      const frame = currentFrame(state);
      return {
        simulation_id: "generic.rule_scene",
        title: spec.title,
        values,
        objects: spec.objects.map((o) => ({ id: o.id, type: o.type, value: values[o.id] })),
        ...(state.timeline.length > 1
          ? {
              current_step: state.cursor + 1,
              total_steps: state.timeline.length,
              narration: frame.narration,
              entity_positions: frame.entityPos,
              visible_objects: frame.visibleIds,
            }
          : {}),
      };
    },

    Workspace: GenericWorkspace,
    Inspector: GenericInspector,
  };
}

export function registerGenericDomain(): void {
  registerSimulation(makeGenericModule());
}
