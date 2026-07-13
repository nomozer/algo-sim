import { STRUCTURE_INVALID, checkOpsAgainstPolicy } from "./edit-policy";
import {
  TEMPORAL_PROCESS_TYPES,
  buildTimeline,
  initialBase,
  valuesOf,
  type SimulationSpec,
  type SpecObject,
} from "./model";
import { validateGenericConfig } from "./validate";

/**
 * SimulationPatch v1 phía frontend (M7.14) — song song app/simulation/patch.py,
 * phục vụ manual edit local (click thêm điểm/nối/xóa) không cần mạng.
 *
 * PatchResult.status TÁCH BẠCH với InteractionFeedback (docs/CORRECTNESS.md §3):
 * - "valid" / "structurally_invalid" do tầng patch quyết;
 * - "unsupported_to_verify" do TẦNG EDIT backend quyết (gap roles) — client
 *   nhận qua /api/edit, không tự sinh;
 * - "invalid_with_feedback" reserved (chờ semantic rules M7.15).
 * Patch fail → spec hiện tại NGUYÊN VẸN (áp trên bản sao).
 */

export type PatchOp =
  | { op: "add_object"; object: Partial<SpecObject> & { id: string; type: string } }
  | { op: "remove_object"; id: string }
  | { op: "update_object"; id: string; fields: Record<string, unknown> }
  | { op: "connect"; from: string; to: string; edge_id: string; label?: string }
  | { op: "disconnect"; edge_id: string };

export type PatchResult =
  | { status: "valid"; config: SimulationSpec }
  | { status: "structurally_invalid"; reasonCode: string; error: string };

export const MAX_OPS = 10;
const UPDATE_FIELDS = new Set(["text", "label", "x", "y", "value"]);
const ADD_FIELDS = new Set(["id", "type", "x", "y", "label", "text", "parent", "value", "weight", "node_type", "from", "to"]);

type Work = {
  dsl_version: string;
  title: string;
  objects: Record<string, unknown>[];
  rules: Record<string, unknown>[];
  interactions: Record<string, unknown>[];
  processes: Record<string, unknown>[];
  notes: string | null;
};

function invalid(error: string, reasonCode: string = STRUCTURE_INVALID): PatchResult {
  return { status: "structurally_invalid", reasonCode, error };
}

function ids(work: Work): Set<string> {
  return new Set(work.objects.map((o) => o.id as string));
}

function semanticDependents(work: Work, oid: string): string | null {
  for (const r of work.rules) {
    if (r.target === oid || ((r.inputs as string[]) ?? []).includes(oid)) {
      return `"${oid}" đang là target/input của một rule — hãy sửa rule trước khi xóa.`;
    }
  }
  for (const p of work.processes) {
    if (p.entity === oid) return `"${oid}" đang là entity của một process — không thể xóa.`;
    if (((p.path as string[]) ?? []).includes(oid)) {
      return `"${oid}" đang nằm trong path của move_along_path — không thể xóa.`;
    }
  }
  const children = work.objects.filter((o) => o.parent === oid).map((o) => o.id);
  if (children.length > 0) {
    return `"${oid}" đang chứa các object con (${children.join(", ")}) — hãy xóa/di chuyển các object con trước.`;
  }
  return null;
}

/** Gỡ dependents THUẦN HÌNH của các id đã xóa (interactions + reveal steps). */
function cascadeRemove(work: Work, removed: Set<string>): void {
  work.interactions = work.interactions.filter((it) => !removed.has(it.target as string));
  const procs: Record<string, unknown>[] = [];
  for (const p of work.processes) {
    if (p.type !== "reveal_sequence") {
      procs.push(p);
      continue;
    }
    const steps: Record<string, unknown>[] = [];
    for (const st of (p.steps as Record<string, unknown>[]) ?? []) {
      const objs = ((st.objects as string[]) ?? []).filter((o) => !removed.has(o));
      if (objs.length > 0) steps.push({ ...st, objects: objs });
    }
    if (steps.length > 0) procs.push({ ...p, steps });
  }
  work.processes = procs;
}

function removeObject(work: Work, oid: string): string | null {
  if (!ids(work).has(oid)) return `remove_object: "${oid}" không tồn tại.`;
  const dep = semanticDependents(work, oid);
  if (dep) return dep;
  const removed = new Set([oid]);
  for (const o of work.objects) {
    if (o.type === "edge" && (o.from === oid || o.to === oid)) removed.add(o.id as string);
  }
  work.objects = work.objects.filter((o) => !removed.has(o.id as string));
  cascadeRemove(work, removed);
  return null;
}

function applyOne(work: Work, op: PatchOp): string | null {
  switch (op.op) {
    case "add_object": {
      const obj = op.object;
      if (!obj || typeof obj.id !== "string" || !obj.id) return 'add_object cần "object" có "id" chuỗi.';
      if (ids(work).has(obj.id)) return `add_object: id "${obj.id}" đã tồn tại.`;
      const clean: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(obj)) {
        if (ADD_FIELDS.has(k) && v !== null && v !== undefined) clean[k] = v;
      }
      work.objects.push(clean);
      return null;
    }
    case "remove_object":
      if (typeof op.id !== "string") return 'remove_object cần "id" chuỗi.';
      return removeObject(work, op.id);
    case "update_object": {
      if (typeof op.id !== "string" || !ids(work).has(op.id)) return `update_object: "${op.id}" không tồn tại.`;
      const fields = op.fields;
      if (!fields || Object.keys(fields).length === 0) return 'update_object cần "fields" không rỗng.';
      const bad = Object.keys(fields).filter((k) => !UPDATE_FIELDS.has(k));
      if (bad.length > 0) {
        return `update_object chỉ đổi được ${[...UPDATE_FIELDS].sort().join("/")} — trường "${bad.sort()[0]}" là cấu trúc, hãy remove + add.`;
      }
      for (const o of work.objects) {
        if (o.id === op.id) {
          for (const [k, v] of Object.entries(fields)) {
            if (v === null || v === undefined) delete o[k];
            else o[k] = v;
          }
        }
      }
      return null;
    }
    case "connect": {
      const { from, to, edge_id: eid } = op;
      if (typeof from !== "string" || typeof to !== "string" || typeof eid !== "string" || !eid) {
        return 'connect cần "from"/"to"/"edge_id" chuỗi.';
      }
      const cur = ids(work);
      if (!cur.has(from) || !cur.has(to)) return `connect: hai đầu phải tồn tại ("${from}" → "${to}").`;
      if (cur.has(eid)) return `connect: edge_id "${eid}" đã tồn tại.`;
      const edge: Record<string, unknown> = { id: eid, type: "edge", from, to };
      if (typeof op.label === "string" && op.label) edge.label = op.label;
      work.objects.push(edge);
      return null;
    }
    case "disconnect": {
      const eid = op.edge_id;
      if (typeof eid !== "string") return 'disconnect cần "edge_id" chuỗi.';
      const target = work.objects.find((o) => o.id === eid);
      if (!target || target.type !== "edge") return `disconnect: "${eid}" không phải một edge đang tồn tại.`;
      work.objects = work.objects.filter((o) => o.id !== eid);
      cascadeRemove(work, new Set([eid]));
      return null;
    }
    default:
      return `Operation không hợp lệ: "${(op as { op?: unknown }).op}".`;
  }
}

/**
 * Trả PatchResult. spec đầu vào KHÔNG BAO GIỜ bị mutate.
 * M7.14D: kiểm EditPolicy TRƯỚC khi áp (ẩn UI là không đủ) — thao tác/loại
 * object không hợp năng lực cảnh → reason_code `policy.*`.
 */
export function validateAndApplyPatch(
  spec: SimulationSpec,
  patch: { operations: PatchOp[] },
  enforcePolicy = true,
): PatchResult {
  const ops = patch?.operations;
  if (!Array.isArray(ops) || ops.length < 1 || ops.length > MAX_OPS) {
    return invalid(`Patch cần "operations" có 1–${MAX_OPS} thao tác.`);
  }

  if (enforcePolicy) {
    const violation = checkOpsAgainstPolicy(spec, ops as { op?: string; object?: { type?: string } }[]);
    if (violation) return invalid(violation.error, violation.reasonCode);
  }

  const work = JSON.parse(JSON.stringify(spec)) as Work;

  for (const op of ops) {
    const err = applyOne(work, op);
    if (err) return invalid(err);
  }

  // Chốt chặn cuối: TOÀN BỘ luật DSL qua validator nguồn chân lý
  const result = validateGenericConfig(work);
  if (!result.ok) return invalid(result.error);
  const config = result.config;

  // Bảo toàn tiến trình: cảnh đang có diễn biến thì patch không được làm mất
  const had = spec.processes.some((p) => TEMPORAL_PROCESS_TYPES.has(p.type));
  const has = config.processes.some((p) => TEMPORAL_PROCESS_TYPES.has(p.type));
  if (had && !has) {
    return invalid(
      "Patch làm mất toàn bộ tiến trình diễn biến của cảnh — hãy giữ lại ít nhất một bước hình thành hoặc xóa ít object hơn.",
    );
  }

  // Engine build smoke — patch không bypass engine success
  try {
    const frames = buildTimeline(config);
    valuesOf(config, initialBase(config));
    if (frames.length === 0) return invalid("Engine không dựng được timeline từ spec sau patch.");
  } catch (exc) {
    return invalid(`Engine lỗi với spec sau patch: ${String(exc)}`);
  }

  return { status: "valid", config };
}
