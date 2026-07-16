import type { ConfigResult } from "../../types";
import dslContract from "./dsl-contract.json";
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
/** Vai trò node HỆ THỐNG THÔNG TIN — mirror `node_type_vocabulary()["system"]` của manifest. */
const SYSTEM_NODE_TYPES = new Set(["actor", "process", "data_store", "input", "output"]);
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

const normText = (s: unknown): string =>
  typeof s === "string" ? s.split(/\s+/).filter(Boolean).join(" ").toLowerCase() : "";

/**
 * Mirror backend `compact_redundant_labels` (M8-PRE plan C).
 *
 * Gỡ object `label` RỜI mà nội dung TRÙNG HỆT nhãn inline của một node/edge có thật
 * — renderer đã vẽ chữ đó rồi nên gỡ đi KHÔNG mất thông tin. Không đoán theo khoảng
 * cách, không gỡ chữ có nghĩa, không gỡ label đang bị tham chiếu cấu trúc.
 */
function compactRedundantLabels(rawObjects: Record<string, unknown>[], raw: Record<string, unknown>): Record<string, unknown>[] {
  const inline = new Set<string>();
  for (const o of rawObjects) {
    if (o.type === "node" || o.type === "edge") {
      for (const key of ["label", "text"]) {
        const t = normText(o[key]);
        if (t) inline.add(t);
      }
    }
  }
  if (inline.size === 0) return rawObjects;

  const hard = new Set<string>();
  for (const r of (raw.rules as Record<string, unknown>[] | undefined) ?? []) {
    for (const i of (r?.inputs as string[] | undefined) ?? []) if (typeof i === "string") hard.add(i);
    if (typeof r?.target === "string") hard.add(r.target);
  }
  for (const it of (raw.interactions as Record<string, unknown>[] | undefined) ?? []) {
    if (typeof it?.target === "string") hard.add(it.target);
  }
  for (const p of (raw.processes as Record<string, unknown>[] | undefined) ?? []) {
    if (typeof p?.entity === "string") hard.add(p.entity);
    for (const n of (p?.path as string[] | undefined) ?? []) if (typeof n === "string") hard.add(n);
  }
  for (const o of rawObjects) if (typeof o.parent === "string") hard.add(o.parent);

  const drop = new Set<string>();
  for (const o of rawObjects) {
    if (o.type === "label" && typeof o.id === "string" && !hard.has(o.id) && inline.has(normText(o.label))) {
      drop.add(o.id);
    }
  }
  if (drop.size === 0) return rawObjects;

  const procs = (raw.processes as Record<string, unknown>[] | undefined) ?? [];
  for (const p of procs) {
    if (p?.type !== "reveal_sequence") continue;
    const steps = ((p.steps as Record<string, unknown>[] | undefined) ?? [])
      .map((st) => ({ ...st, objects: (((st?.objects as string[]) ?? []).filter((i) => !drop.has(i))) }))
      .filter((st) => st.objects.length > 0);
    p.steps = steps;
  }
  raw.processes = procs.filter(
    (p) => !(p?.type === "reveal_sequence" && ((p.steps as unknown[]) ?? []).length === 0),
  );
  return rawObjects.filter((o) => !drop.has(o.id as string));
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

  const objectsField = raw.objects;
  if (!Array.isArray(objectsField) || objectsField.length < 1) {
    return { ok: false, error: `"objects" phải có 1–${MAX_OBJECTS} phần tử.` };
  }
  // M8-PRE (plan C): CHỈ khi vượt hạn mức mới nén phần dư thừa chứng minh được.
  // Cảnh trong hạn mức KHÔNG bị đụng → 0 bề mặt regression. Mirror backend.
  let rawObjects: unknown[] = objectsField;
  if (rawObjects.length > MAX_OBJECTS && rawObjects.every((o) => isObj(o))) {
    rawObjects = compactRedundantLabels(rawObjects as Record<string, unknown>[], raw);
  }
  if (rawObjects.length > MAX_OBJECTS) {
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
    // M13 Task 2b: "weight" cấp OBJECT là silent semantic no-op — không engine
    // nào đọc nó (trọng số THẬT của weighted_sum luôn là "weights" TRÊN RULE).
    // Reject tường minh, KHÔNG strip im lặng — LLM phải biết mô hình của nó sai.
    if ("weight" in o) {
      return {
        ok: false,
        error:
          `Object "${o.id}" khai "weight" — trường này không còn được hỗ trợ ` +
          `(không engine nào đọc nó). Trọng số của weighted_sum khai bằng mảng ` +
          `"weights" TRÊN RULE, vd {"type": "weighted_sum", "inputs": [...], "weights": [8,4,2,1]}.`,
      };
    }
    const obj: SpecObject = { id: o.id, type: o.type as ObjectType };
    for (const key of ["x", "y", "value"] as const) {
      if (typeof o[key] === "number" && Number.isFinite(o[key])) obj[key] = o[key] as number;
    }
    for (const key of ["label", "node_type", "from", "to", "text", "parent"] as const) {
      if (typeof o[key] === "string") obj[key] = o[key] as string;
    }
    // M8-PRE (S2): mirror backend — chỉ edge, chỉ bool THẬT (không nhận 0/1/chuỗi).
    if (o.type === "edge" && typeof o.directed === "boolean") obj.directed = o.directed;
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
  // M8-PRE (S2): mirror backend — CHIỀU luồng dữ liệu được SUY từ from/to giữa hai
  // node vai trò hệ thống (LLM không đáng tin cho việc khai `directed`). Hai tầng
  // validator phải suy ra CÙNG một spec, nếu không spec sửa cục bộ sẽ lệch server.
  const sysNodes = new Set(
    objects.filter((o) => o.type === "node" && o.node_type && SYSTEM_NODE_TYPES.has(o.node_type)).map((o) => o.id),
  );
  for (const o of objects) {
    if (o.type === "edge" && o.directed === undefined && o.from && o.to && sysNodes.has(o.from) && sysNodes.has(o.to)) {
      o.directed = true;
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
  // M11: mỗi giá trị dẫn xuất đúng MỘT rule sở hữu — hai rule cùng target thì
  // rule sau thắng mỗi vòng quét điểm bất động → phụ thuộc thứ tự khai báo.
  const seenTargets = new Set<string>();
  for (const r of rules) {
    if (seenTargets.has(r.target)) {
      return {
        ok: false,
        error: `Hai rule cùng ghi vào target "${r.target}" — mỗi giá trị dẫn xuất chỉ được đúng MỘT rule sở hữu. Hãy gộp điều kiện vào một rule hoặc dùng thêm một object trung gian làm target riêng.`,
      };
    }
    seenTargets.add(r.target);
  }
  // Cấm chu trình phụ thuộc rule (target ← input là target khác)
  const cycleErr = detectCycle(rules);
  if (cycleErr) return { ok: false, error: cycleErr };

  // M13 §3.2 + blocker 3: operand coherence với role-typing — contract SINH từ
  // manifest backend (dsl-contract.json), sync-lock test backend chống drift.
  // Mirror `backend/app/simulation/dsl/validator.py:369-408` (Task 3).
  const ruleIo = dslContract.rule_io as Record<string, { input_role: string; output_role: string }>;
  const targetOutputRole = new Map(rules.map((r) => [r.target, ruleIo[r.type].output_role]));
  const coercions = new Set(
    (dslContract.role_coercions as { from: string; to: string }[]).map((c) => `${c.from}->${c.to}`),
  );
  const objectRoles = dslContract.object_roles as Record<string, string[]>;
  for (const r of rules) {
    // Ràng buộc 2: target phải chấp nhận output role của rule (parity backend).
    const outRole = ruleIo[r.type].output_role;
    const targetObj = byId[r.target];
    if (!objectRoles[targetObj.type]?.includes(outRole)) {
      return {
        ok: false,
        error:
          `Rule ${r.type} sinh giá trị vai trò "${outRole}" nhưng target "${r.target}" ` +
          `(${targetObj.type}) không nhận được vai trò đó — dùng object type có vai trò ` +
          `${outRole} làm target (vd value_box/lamp).`,
      };
    }
    const need = ruleIo[r.type].input_role;
    const providers: string[] = (dslContract.value_providers as Record<string, string[]>)[need];
    for (const inp of r.inputs ?? []) {
      const out = targetOutputRole.get(inp);
      if (out !== undefined) {
        if (out !== need && !coercions.has(`${out}->${need}`)) {
          return {
            ok: false,
            error:
              `Rule "${r.target}" dùng input "${inp}" là kết quả rule khác có vai trò "${out}", ` +
              `nhưng rule ${r.type} cần vai trò "${need}" — không có coercion được khai. ` +
              `Dùng nguồn đúng vai trò.`,
          };
        }
        continue; // derived + đúng role → defer theo bound lúc chạy
      }
      const o = byId[inp];
      if (!providers.includes(o.type) || o.value === undefined) {
        return {
          ok: false,
          error:
            `Rule "${r.target}" dùng input "${inp}" (${o.type}) không có nguồn giá trị ` +
            `${need} theo hợp đồng DSL — chỉ chấp nhận: ${providers.join(", ")} có "value", ` +
            `hoặc target của một rule cùng vai trò. Đừng dùng node/edge làm toán hạng.`,
        };
      }
    }
  }

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
