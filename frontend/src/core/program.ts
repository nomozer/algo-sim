import { TraceBuilder } from "./trace-builder";
import type { Trace, TraceEvent } from "./types";

/**
 * M17 W2C — LUỒNG ĐIỀU KHIỂN HỮU HẠN: interpreter tất định, engine-owned.
 *
 * MIRROR của `backend/app/simulation/program_spec.py` +
 * `backend/app/validation/program.py` — CÙNG LUẬT, đổi một bên thì phải đổi cả
 * hai (đúng khuôn `core/scan.ts` ↔ `simulation/scan_engine.py`). Config được
 * validate ở CẢ HAI phía; đường mở-lại-từ-lịch-sử (bất biến #17) đi THẲNG vào
 * engine này nên validator FE không phải thủ tục thừa.
 *
 * ĐÂY KHÔNG PHẢI TRÌNH THÔNG DỊCH PYTHON: không eval/exec, không hàm, không đệ
 * quy, không mảng/chuỗi/số thực/nhập-xuất, không break/continue. Vòng lặp LUÔN
 * có biên — chạm giới hạn thì dừng và nói thật là "chưa kết thúc", KHÔNG treo
 * và KHÔNG trình bày như đã chạy xong.
 *
 * MỘT NGUỒN cho mã giả: `programLines(spec)` vừa sinh dòng hiển thị vừa trả
 * bản đồ statementId → số dòng, và interpreter gắn `Step.line` từ CHÍNH bản đồ
 * đó — highlight không thể trôi khỏi câu lệnh đang chạy.
 */

export const PROGRAM_VERSION = "program-2.0";

/** MIRROR `program_spec.LIMITS` — sửa một bên phải sửa bên kia. */
export const PROGRAM_LIMITS = {
  maxStatementNodes: 12,
  maxNestingDepth: 2,
  maxVariables: 8,
  maxExpressionDepth: 6,
  maxConditionAtoms: 3,
  maxExecutionSteps: 200,
  maxWhileIterations: 50,
  maxOutputEntries: 30,
} as const;

export const INT_MIN = -10000;
export const INT_MAX = 10000;

export type ValueType = "integer" | "boolean";
export type StatementKind = "assign" | "if" | "while" | "output";
// Hằng RUNTIME + kiểu dẫn xuất TỪ NÓ — biên nhận dạng canonical cần kiểm `kind`
// lúc chạy, và derive kiểu từ hằng thì hai thứ không thể trôi khỏi nhau.
export const EXPRESSION_KINDS = [
  "int", "bool", "var", "unary", "binary", "compare", "logic",
] as const;
export type ExpressionKind = (typeof EXPRESSION_KINDS)[number];

export const ARITHMETIC_OPS = ["+", "-", "*", "//", "%"] as const;
export const COMPARE_OPS = ["==", "!=", "<", "<=", ">", ">="] as const;
export const LOGIC_OPS = ["and", "or"] as const;
export const UNARY_OPS = ["-", "not"] as const;

const ORDER_OPS = ["<", "<=", ">", ">="];
const EQUALITY_OPS = ["==", "!="];

export interface ProgramVariable {
  name: string;
  type: ValueType;
  int_value: number | null;
  bool_value: boolean | null;
  /** W2C-C1 §L1: KHAI BÁO ≠ KHỞI TẠO. false ⇒ chưa có giá trị (KHÔNG phải 0/false). */
  initialized: boolean;
}

/* ── W2C-C1 §L2 — bề mặt LLM: biểu thức INLINE, nông, PHI ĐỆ QUY ── */
export interface Operand {
  kind: "int" | "bool" | "var";
  int_value?: number | null;
  bool_value?: boolean | null;
  name?: string | null;
}
export interface InlineValue {
  left: Operand;
  op?: string | null;
  right?: Operand | null;
}
export interface InlineAtom {
  left: InlineValue;
  op?: string | null;
  right?: InlineValue | null;
  negated?: boolean | null;
}
export interface InlineCondition {
  op?: string | null;
  atoms: InlineAtom[];
}

export interface ProgramExpression {
  id: string;
  kind: ExpressionKind;
  int_value?: number | null;
  bool_value?: boolean | null;
  name?: string | null;
  op?: string | null;
  left?: string | null;
  right?: string | null;
  operand?: string | null;
}

export interface ProgramStatement {
  id: string;
  kind: StatementKind;
  target?: string | null;
  value?: string | null;
  condition?: string | null;
  then_body?: string[];
  else_body?: string[];
  body?: string[];
  max_iterations?: number | null;
}

export interface ProgramSpec {
  program_version: string;
  variables: ProgramVariable[];
  expressions: ProgramExpression[];
  statements: ProgramStatement[];
  main: string[];
  notes?: string | null;
}

export type ProgramValidation =
  | { ok: true; spec: ProgramSpec }
  | { ok: false; error: string };

/** Trạng thái kết thúc — engine sở hữu, KHÔNG nằm trong spec. */
export type CompletionState = "completed" | "limit_reached";

const NAME_RE = /^[A-Za-z][A-Za-z0-9_]*$/;
const TYPE_VI: Record<ValueType, string> = { integer: "số nguyên", boolean: "đúng/sai" };

const isInt = (v: unknown): v is number =>
  typeof v === "number" && Number.isInteger(v);
const isBool = (v: unknown): v is boolean => typeof v === "boolean";

function fail(error: string): ProgramValidation {
  return { ok: false, error };
}

/* ── §L2 — normalizer TẤT ĐỊNH: inline (bề mặt LLM) → nội bộ ─────
 * MIRROR `program_spec.normalize_inline_program`. Không đoán ý, không bù toán
 * tử thiếu, không sửa tên biến, không giá trị mặc định. Id sinh theo thứ tự
 * duyệt nên cùng input ⇒ cùng output. */

class NormalizeError extends Error {}

function normalizeInlineProgram(rawStatements: unknown): {
  expressions: ProgramExpression[];
  statements: ProgramStatement[];
} {
  if (!Array.isArray(rawStatements)) throw new NormalizeError("'statements' phải là danh sách.");
  const expressions: ProgramExpression[] = [];
  const seen = new Map<string, string>();

  const emit = (node: Omit<ProgramExpression, "id">): string => {
    const key = JSON.stringify(node);
    const hit = seen.get(key);
    if (hit) return hit;
    const id = `_e${expressions.length + 1}`;
    expressions.push({ id, ...node });
    seen.set(key, id);
    return id;
  };

  const operand = (raw: unknown, where: string): string => {
    const o = raw as Operand | undefined;
    if (!o || typeof o !== "object") throw new NormalizeError(`${where}: toán hạng phải là đối tượng.`);
    if (o.kind === "int") {
      if (!isInt(o.int_value)) throw new NormalizeError(`${where}: hằng số nguyên thiếu 'int_value'.`);
      if (o.int_value! < INT_MIN || o.int_value! > INT_MAX) {
        throw new NormalizeError(`${where}: hằng số ngoài khoảng cho phép.`);
      }
      return emit({ kind: "int", int_value: o.int_value });
    }
    if (o.kind === "bool") {
      if (!isBool(o.bool_value)) throw new NormalizeError(`${where}: hằng đúng/sai thiếu 'bool_value'.`);
      return emit({ kind: "bool", bool_value: o.bool_value });
    }
    if (o.kind === "var") {
      if (typeof o.name !== "string" || !o.name.trim()) {
        throw new NormalizeError(`${where}: tham chiếu biến thiếu 'name'.`);
      }
      return emit({ kind: "var", name: o.name });
    }
    throw new NormalizeError(`${where}: loại toán hạng không hỗ trợ: ${String((o as Operand).kind)}.`);
  };

  const value = (raw: unknown, where: string): string => {
    const v = raw as InlineValue | undefined;
    if (!v || typeof v !== "object") throw new NormalizeError(`${where}: biểu thức giá trị phải là đối tượng.`);
    const left = operand(v.left, where);
    if (v.op == null || v.op === "") {
      if (v.right != null) throw new NormalizeError(`${where}: có 'right' thì phải có toán tử.`);
      return left;
    }
    if (!(ARITHMETIC_OPS as readonly string[]).includes(v.op)) {
      throw new NormalizeError(`${where}: toán tử số học không hỗ trợ: ${v.op}.`);
    }
    return emit({ kind: "binary", op: v.op, left, right: operand(v.right, where) });
  };

  const atomNode = (raw: unknown, where: string): string => {
    const a = raw as InlineAtom | undefined;
    if (!a || typeof a !== "object") throw new NormalizeError(`${where}: vế điều kiện phải là đối tượng.`);
    const left = value(a.left, where);
    let node = left;
    if (a.op != null && a.op !== "") {
      if (!(COMPARE_OPS as readonly string[]).includes(a.op)) {
        throw new NormalizeError(`${where}: toán tử so sánh không hỗ trợ: ${a.op}.`);
      }
      node = emit({ kind: "compare", op: a.op, left, right: value(a.right, where) });
    }
    if (a.negated === true) node = emit({ kind: "unary", op: "not", operand: node });
    return node;
  };

  const condition = (raw: unknown, where: string): string => {
    const c = raw as InlineCondition | undefined;
    if (!c || typeof c !== "object" || !Array.isArray(c.atoms) || c.atoms.length === 0) {
      throw new NormalizeError(`${where}: điều kiện cần ít nhất một vế trong 'atoms'.`);
    }
    if (c.atoms.length > PROGRAM_LIMITS.maxConditionAtoms) {
      throw new NormalizeError(
        `${where}: điều kiện có ${c.atoms.length} vế, tối đa ${PROGRAM_LIMITS.maxConditionAtoms}.`,
      );
    }
    if (c.atoms.length === 1) return atomNode(c.atoms[0], where);
    if (c.op == null || !(LOGIC_OPS as readonly string[]).includes(c.op)) {
      throw new NormalizeError(`${where}: nhiều vế thì cần toán tử and/or.`);
    }
    let node = atomNode(c.atoms[0], where);
    for (const extra of c.atoms.slice(1)) {
      node = emit({ kind: "logic", op: c.op, left: node, right: atomNode(extra, where) });
    }
    return node;
  };

  const statements: ProgramStatement[] = [];
  for (const raw of rawStatements as Record<string, unknown>[]) {
    if (!raw || typeof raw !== "object") throw new NormalizeError("Mỗi câu lệnh phải là đối tượng.");
    const id = raw.id as string;
    const kind = raw.kind as StatementKind;
    const where = `câu lệnh '${id}'`;
    const st: ProgramStatement = { id, kind, then_body: [], else_body: [], body: [] };
    if (kind === "assign") {
      st.target = raw.target as string;
      st.value = value(raw.value, where);
    } else if (kind === "output") {
      st.value = value(raw.value, where);
    } else if (kind === "if") {
      st.condition = condition(raw.condition, where);
      st.then_body = (raw.then_body as string[]) ?? [];
      st.else_body = (raw.else_body as string[]) ?? [];
    } else if (kind === "while") {
      st.condition = condition(raw.condition, where);
      st.body = (raw.body as string[]) ?? [];
      st.max_iterations = (raw.max_iterations as number) ?? null;
    } else {
      throw new NormalizeError(
        `Loại câu lệnh không hỗ trợ: ${String(kind)} — không có hàm, đệ quy, break/continue.`,
      );
    }
    statements.push(st);
  }
  return { expressions, statements };
}

/* ── BIÊN NHẬN dạng CANONICAL (đã chuẩn hoá) ──────────────────
 * Backend `validate_program_config` phát ra bảng `expressions[]` + câu lệnh
 * tham chiếu id; đó là dạng dây dẫn của envelope và cũng là dạng lịch sử lưu.
 * Hàm này KHÔNG chuẩn hoá lại (sẽ đánh số id lần hai) — nó KIỂM ĐỊNH bảng rồi
 * dùng nguyên văn.
 *
 * Vì sao phải kiểm dù backend đã kiểm: đây là tầng 2 của validator hai tầng.
 * Bảng tới từ dây dẫn/localStorage có thể treo id hoặc có CHU TRÌNH, mà cả
 * `typeOf` lẫn `readsOf` bên dưới đều đệ quy và dùng `exprById.get(id)!` —
 * treo thì ném TypeError, chu trình thì tràn ngăn xếp. Fail-closed ở đây để
 * chúng không bao giờ thấy bảng hỏng. Hỗ trợ hai bề mặt KHÔNG được làm
 * validator dễ dãi hơn.
 */
function adoptNormalizedProgram(
  r: Record<string, unknown>,
): { expressions: ProgramExpression[]; statements: ProgramStatement[] } | { error: string } {
  const rawExprs = r.expressions;
  if (!Array.isArray(rawExprs)) return { error: "'expressions' phải là danh sách." };
  if (!Array.isArray(r.statements)) return { error: "'statements' phải là danh sách." };

  const byId = new Map<string, ProgramExpression>();
  for (const raw of rawExprs as Record<string, unknown>[]) {
    if (!raw || typeof raw !== "object") return { error: "Mỗi biểu thức phải là một đối tượng." };
    const id = raw.id;
    if (typeof id !== "string" || !id.trim()) return { error: "Mỗi biểu thức phải có 'id'." };
    if (byId.has(id)) return { error: `Biểu thức trùng id: '${id}'.` };
    const kind = raw.kind;
    if (!(EXPRESSION_KINDS as readonly string[]).includes(kind as string)) {
      return { error: `Loại biểu thức không hỗ trợ: ${String(kind)}.` };
    }
    const k = kind as ExpressionKind;
    const op = raw.op;
    if (k === "int" && !isInt(raw.int_value)) {
      return { error: `Biểu thức '${id}' thiếu 'int_value' là số nguyên.` };
    }
    if (k === "int" && ((raw.int_value as number) < INT_MIN || (raw.int_value as number) > INT_MAX)) {
      return { error: `Hằng số ở '${id}' ngoài khoảng cho phép.` };
    }
    if (k === "bool" && !isBool(raw.bool_value)) {
      return { error: `Biểu thức '${id}' thiếu 'bool_value' là true/false.` };
    }
    if (k === "var" && (typeof raw.name !== "string" || !raw.name)) {
      return { error: `Biểu thức '${id}' thiếu tên biến.` };
    }
    const opOk =
      k === "unary" ? (UNARY_OPS as readonly string[]).includes(op as string)
      : k === "binary" ? (ARITHMETIC_OPS as readonly string[]).includes(op as string)
      : k === "compare" ? (COMPARE_OPS as readonly string[]).includes(op as string)
      : k === "logic" ? (LOGIC_OPS as readonly string[]).includes(op as string)
      : true;
    if (!opOk) return { error: `Toán tử không hợp lệ ở biểu thức '${id}': ${String(op)}.` };
    byId.set(id, raw as unknown as ProgramExpression);
  }

  // con của một nút — cùng bộ trường mà `typeOf`/`readsOf` sẽ đi theo
  const childrenOf = (n: ProgramExpression): string[] => {
    const out: string[] = [];
    for (const key of ["operand", "left", "right"] as const) {
      const child = n[key];
      if (child != null) out.push(child);
    }
    return out;
  };

  for (const [id, node] of byId) {
    const need =
      node.kind === "unary" ? ["operand"]
      : ["binary", "compare", "logic"].includes(node.kind) ? ["left", "right"]
      : [];
    for (const key of need) {
      const ref = (node as unknown as Record<string, unknown>)[key];
      if (typeof ref !== "string" || !byId.has(ref)) {
        return { error: `Biểu thức '${id}' tham chiếu tới '${String(ref)}' không tồn tại.` };
      }
    }
  }

  // CHU TRÌNH + ĐỘ SÂU trong một lượt duyệt (0=trắng, 1=đang duyệt, 2=xong).
  const mark = new Map<string, number>();
  const depthOf = new Map<string, number>();
  const visit = (id: string): string | null => {
    const state = mark.get(id) ?? 0;
    if (state === 1) return `Biểu thức '${id}' tham chiếu vòng tròn.`;
    if (state === 2) return null;
    mark.set(id, 1);
    let deepest = 0;
    for (const child of childrenOf(byId.get(id)!)) {
      const err = visit(child);
      if (err) return err;
      deepest = Math.max(deepest, depthOf.get(child) ?? 0);
    }
    mark.set(id, 2);
    const d = deepest + 1;
    depthOf.set(id, d);
    if (d > PROGRAM_LIMITS.maxExpressionDepth) {
      return `Biểu thức '${id}' lồng quá ${PROGRAM_LIMITS.maxExpressionDepth} tầng.`;
    }
    return null;
  };
  for (const id of byId.keys()) {
    const err = visit(id);
    if (err) return { error: err };
  }

  // Câu lệnh: phải là đối tượng, và mọi tham chiếu biểu thức phải có thật —
  // `typeOf` bên dưới dùng non-null assertion nên id treo sẽ ném, không fail sạch.
  const statements: ProgramStatement[] = [];
  for (const raw of r.statements as Record<string, unknown>[]) {
    if (!raw || typeof raw !== "object") return { error: "Mỗi câu lệnh phải là một đối tượng." };
    for (const key of ["value", "condition"] as const) {
      const ref = raw[key];
      if (ref != null && (typeof ref !== "string" || !byId.has(ref))) {
        return {
          error: `Câu lệnh '${String(raw.id)}' tham chiếu biểu thức '${String(ref)}' không tồn tại.`,
        };
      }
    }
    statements.push(raw as unknown as ProgramStatement);
  }

  return { expressions: rawExprs as ProgramExpression[], statements };
}

/* ── validator (mirror backend) ─────────────────────────────── */

export function validateProgramSpec(raw: unknown): ProgramValidation {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    return fail("Config phải là một đối tượng.");
  }
  const r = raw as Record<string, unknown>;

  for (const key of ["trace", "steps", "environment", "final_environment", "result", "iterations"]) {
    if (key in r) return fail(`Config KHÔNG được chứa kết quả hay diễn biến chạy: ${key}.`);
  }
  const version = (r.program_version as string) || PROGRAM_VERSION;
  if (version !== PROGRAM_VERSION) return fail(`program_version phải là '${PROGRAM_VERSION}'.`);

  // ── §L1: biến — KHAI BÁO ≠ KHỞI TẠO ──
  const rawVars = r.variables;
  if (!Array.isArray(rawVars) || rawVars.length === 0) return fail("Cần ít nhất một biến.");
  if (rawVars.length > PROGRAM_LIMITS.maxVariables) {
    return fail(`Tối đa ${PROGRAM_LIMITS.maxVariables} biến.`);
  }
  const variables: ProgramVariable[] = [];
  const varTypes = new Map<string, ValueType>();
  for (const item of rawVars as Record<string, unknown>[]) {
    const name = item?.name;
    if (typeof name !== "string" || !NAME_RE.test(name)) return fail(`Tên biến không hợp lệ: ${String(name)}.`);
    if (varTypes.has(name)) return fail(`Biến '${name}' được khai báo hai lần.`);
    const type = item.type;
    if (type !== "integer" && type !== "boolean") return fail(`Kiểu của biến '${name}' không hợp lệ.`);
    const iv = item.int_value ?? null;
    const bv = item.bool_value ?? null;
    if (iv === null && bv === null) {
      // Khai báo mà CHƯA khởi tạo — hệ KHÔNG bịa 0/false thay đề.
      variables.push({ name, type, int_value: null, bool_value: null, initialized: false });
    } else if (type === "integer") {
      if (!isInt(iv)) return fail(`Biến '${name}' cần 'int_value' là số nguyên.`);
      if (iv < INT_MIN || iv > INT_MAX) return fail(`Giá trị của '${name}' ngoài khoảng cho phép.`);
      variables.push({ name, type, int_value: iv, bool_value: null, initialized: true });
    } else {
      if (!isBool(bv)) return fail(`Biến '${name}' cần 'bool_value' là true/false.`);
      variables.push({ name, type, int_value: null, bool_value: bv, initialized: true });
    }
    varTypes.set(name, type);
  }

  // ── BIÊN NHẬN: hai bề mặt vào, MỘT biểu diễn ra ──
  // CANONICAL (dạng dây dẫn của `ValidatedSimulationEnvelope`) = đã chuẩn hoá:
  // bảng `expressions[]` + câu lệnh tham chiếu bằng id. Đây là thứ backend phát
  // ra sau `validate_program_config`, và là thứ lịch sử lưu lại.
  // INLINE = bề mặt ỨNG VIÊN (LLM sinh, fixture test) — chuẩn hoá ĐÚNG MỘT LẦN
  // tại đây rồi đi tiếp cùng một đường.
  // Đã chuẩn hoá thì KHÔNG chuẩn hoá lại (id sẽ bị đánh số lần hai).
  let normalized: { expressions: ProgramExpression[]; statements: ProgramStatement[] };
  if (r.expressions !== undefined) {
    const adopted = adoptNormalizedProgram(r);
    if ("error" in adopted) return fail(adopted.error);
    normalized = adopted;
  } else {
    try {
      normalized = normalizeInlineProgram(r.statements);
    } catch (e) {
      return fail((e as Error).message);
    }
  }
  const expressions = normalized.expressions;
  const exprById = new Map(expressions.map((e) => [e.id, e]));
  for (const node of expressions) {
    if (node.kind === "var" && !varTypes.has(node.name!)) {
      return fail(`Chương trình dùng biến '${node.name}' chưa được khai báo.`);
    }
  }

  // ── câu lệnh ──
  const rawStmts = normalized.statements;
  if (rawStmts.length === 0) return fail("Cần ít nhất một câu lệnh.");
  if (rawStmts.length > PROGRAM_LIMITS.maxStatementNodes) {
    return fail(`Tối đa ${PROGRAM_LIMITS.maxStatementNodes} câu lệnh.`);
  }
  const statements: ProgramStatement[] = [];
  const stmtById = new Map<string, ProgramStatement>();
  for (const st of rawStmts) {
    if (typeof st.id !== "string" || !st.id.trim()) return fail("Mỗi câu lệnh phải có 'id'.");
    if (stmtById.has(st.id)) return fail(`Câu lệnh trùng id: '${st.id}'.`);
    if (st.kind === "assign" && (typeof st.target !== "string" || !varTypes.has(st.target))) {
      return fail(`Câu lệnh '${st.id}' gán cho biến chưa khai báo.`);
    }
    if (st.kind === "if" && (st.then_body ?? []).length === 0) {
      return fail(`Rẽ nhánh '${st.id}' phải có nhánh đúng.`);
    }
    if (st.kind === "while") {
      if ((st.body ?? []).length === 0) return fail(`Vòng lặp '${st.id}' phải có thân.`);
      if (!isInt(st.max_iterations)) return fail(`Vòng lặp '${st.id}' phải khai 'max_iterations'.`);
      if (st.max_iterations! < 1 || st.max_iterations! > PROGRAM_LIMITS.maxWhileIterations) {
        return fail(`'max_iterations' của '${st.id}' vượt ${PROGRAM_LIMITS.maxWhileIterations}.`);
      }
    }
    statements.push(st);
    stmtById.set(st.id, st);
  }

  const main = r.main;
  if (!Array.isArray(main) || main.length === 0 || !main.every((x) => typeof x === "string")) {
    return fail("'main' phải là danh sách id câu lệnh.");
  }
  const used = new Map<string, number>();
  const bump = (id: string) => used.set(id, (used.get(id) ?? 0) + 1);
  (main as string[]).forEach(bump);
  for (const st of statements) {
    [...(st.then_body ?? []), ...(st.else_body ?? []), ...(st.body ?? [])].forEach(bump);
  }
  for (const [id, count] of used) {
    if (!stmtById.has(id)) return fail(`Tham chiếu tới câu lệnh '${id}' không tồn tại.`);
    if (count > 1) return fail(`Câu lệnh '${id}' bị dùng ở nhiều khối.`);
  }
  for (const st of statements) {
    if (!used.has(st.id)) return fail(`Câu lệnh '${st.id}' không nằm trong chương trình.`);
  }

  const nestingError = (ids: string[], level: number): string | null => {
    for (const id of ids) {
      const st = stmtById.get(id)!;
      const children = [...(st.then_body ?? []), ...(st.else_body ?? []), ...(st.body ?? [])];
      if (children.length > 0) {
        if (level + 1 > PROGRAM_LIMITS.maxNestingDepth) {
          return `Câu lệnh '${id}' lồng quá ${PROGRAM_LIMITS.maxNestingDepth} tầng.`;
        }
        const err = nestingError(children, level + 1);
        if (err) return err;
      }
    }
    return null;
  };
  const nestErr = nestingError(main as string[], 0);
  if (nestErr) return fail(nestErr);

  // kiểu
  const typeCache = new Map<string, ValueType>();
  let typeError: string | null = null;
  const typeOf = (id: string): ValueType | null => {
    const cached = typeCache.get(id);
    if (cached) return cached;
    const node = exprById.get(id)!;
    let t: ValueType | null = null;
    if (node.kind === "int") t = "integer";
    else if (node.kind === "bool") t = "boolean";
    else if (node.kind === "var") t = varTypes.get(node.name!)!;
    else if (node.kind === "unary") {
      const inner = typeOf(node.operand!);
      if (!inner) return null;
      const want: ValueType = node.op === "-" ? "integer" : "boolean";
      if (inner !== want) {
        typeError = `Toán tử '${node.op}' ở '${id}' cần ${TYPE_VI[want]}.`;
        return null;
      }
      t = want;
    } else {
      const lt = typeOf(node.left!);
      const rt = typeOf(node.right!);
      if (!lt || !rt) return null;
      if (node.kind === "binary") {
        if (lt !== "integer" || rt !== "integer") {
          typeError = `Phép '${node.op}' ở '${id}' chỉ dùng cho số nguyên.`;
          return null;
        }
        if (node.op === "//" || node.op === "%") {
          const right = exprById.get(node.right!)!;
          if (right.kind === "int" && right.int_value === 0) {
            typeError = `Phép '${node.op}' ở '${id}' chia cho 0.`;
            return null;
          }
        }
        t = "integer";
      } else if (node.kind === "compare") {
        if (ORDER_OPS.includes(node.op!) && (lt !== "integer" || rt !== "integer")) {
          typeError = `So sánh '${node.op}' ở '${id}' chỉ dùng cho số nguyên.`;
          return null;
        }
        if (EQUALITY_OPS.includes(node.op!) && lt !== rt) {
          typeError = `So sánh '${node.op}' ở '${id}' cần hai vế cùng kiểu.`;
          return null;
        }
        t = "boolean";
      } else {
        if (lt !== "boolean" || rt !== "boolean") {
          typeError = `Phép '${node.op}' ở '${id}' cần hai vế đúng/sai.`;
          return null;
        }
        t = "boolean";
      }
    }
    typeCache.set(id, t!);
    return t;
  };
  for (const st of statements) {
    if (st.kind === "assign") {
      const t = typeOf(st.value!);
      if (!t) return fail(typeError ?? "Biểu thức sai kiểu.");
      const want = varTypes.get(st.target!)!;
      if (t !== want) {
        return fail(`Biến '${st.target}' là ${TYPE_VI[want]} nhưng câu lệnh '${st.id}' gán ${TYPE_VI[t]}.`);
      }
    } else if (st.kind === "output") {
      if (!typeOf(st.value!)) return fail(typeError ?? "Biểu thức sai kiểu.");
    } else {
      const t = typeOf(st.condition!);
      if (!t) return fail(typeError ?? "Biểu thức sai kiểu.");
      if (t !== "boolean") {
        return fail(`Điều kiện của '${st.id}' phải là đúng/sai, đang là ${TYPE_VI[t]}.`);
      }
    }
  }


  // ── §L1: DEFINITE ASSIGNMENT — đọc biến chưa chắc có giá trị là TỪ CHỐI ──
  const readsOf = (eid: string): string[] => {
    const n = exprById.get(eid)!;
    if (n.kind === "var") return [n.name!];
    const out: string[] = [];
    for (const k of ["operand", "left", "right"] as const) {
      const child = n[k];
      if (child != null) out.push(...readsOf(child));
    }
    return out;
  };
  let daError: string | null = null;
  const checkRead = (eid: string, init: Set<string>, where: string) => {
    if (daError) return;
    const missing = readsOf(eid).filter((v) => !init.has(v));
    if (missing.length > 0) {
      daError = `${where} đọc biến ${missing.join(", ")} khi biến đó chưa chắc chắn có giá trị.`;
    }
  };
  const walkDA = (ids: string[], init: Set<string>): Set<string> => {
    let cur = new Set(init);
    for (const id of ids) {
      if (daError) return cur;
      const st = stmtById.get(id)!;
      if (st.kind === "assign") {
        checkRead(st.value!, cur, `Câu lệnh gán '${id}'`);
        cur.add(st.target!);
      } else if (st.kind === "output") {
        checkRead(st.value!, cur, `Câu lệnh hiển thị '${id}'`);
      } else if (st.kind === "if") {
        checkRead(st.condition!, cur, `Điều kiện của '${id}'`);
        const afterThen = walkDA(st.then_body ?? [], cur);
        if ((st.else_body ?? []).length > 0) {
          const afterElse = walkDA(st.else_body ?? [], cur);
          cur = new Set([...afterThen].filter((v) => afterElse.has(v)));
        }
      } else {
        checkRead(st.condition!, cur, `Điều kiện của vòng lặp '${id}'`);
        walkDA(st.body ?? [], cur);   // while có thể chạy 0 lượt ⇒ KHÔNG mở rộng
      }
    }
    return cur;
  };
  walkDA(main as string[], new Set(variables.filter((v) => v.initialized).map((v) => v.name)));
  if (daError) return fail(daError);

  return {
    ok: true,
    spec: {
      program_version: PROGRAM_VERSION,
      variables,
      expressions,
      statements,
      main: main as string[],
      ...(typeof r.notes === "string" ? { notes: r.notes } : {}),
    },
  };
}

/* ── mã giả: MỘT NGUỒN cho hiển thị và cho Step.line ─────────── */

const INDENT = "   ";

export function renderExpression(spec: ProgramSpec, id: string): string {
  const by = new Map(spec.expressions.map((e) => [e.id, e]));
  const walk = (eid: string): string => {
    const n = by.get(eid);
    if (!n) return "?";
    switch (n.kind) {
      case "int":
        return String(n.int_value);
      case "bool":
        return n.bool_value ? "đúng" : "sai";
      case "var":
        return n.name!;
      case "unary":
        return n.op === "not" ? `không (${walk(n.operand!)})` : `-${walk(n.operand!)}`;
      case "logic":
        return `${walk(n.left!)} ${n.op === "and" ? "và" : "hoặc"} ${walk(n.right!)}`;
      default:
        return `${walk(n.left!)} ${n.op} ${walk(n.right!)}`;
    }
  };
  return walk(id);
}

export interface ProgramLayout {
  lines: string[];
  /** statementId → số dòng 1-based (chính là `Step.line`). */
  lineOf: Record<string, number>;
}

/**
 * Sinh mã giả TỪ CHÍNH `statements[]` và bản đồ dòng dùng chung với
 * interpreter. Không có bảng mã giả viết tay nào để trôi khỏi AST.
 */
export function programLines(spec: ProgramSpec): ProgramLayout {
  const byId = new Map(spec.statements.map((s) => [s.id, s]));
  const lines: string[] = [];
  const lineOf: Record<string, number> = {};

  const emit = (text: string, depth: number): number => {
    lines.push(INDENT.repeat(depth) + text);
    return lines.length; // 1-based
  };

  const walk = (ids: string[], depth: number): void => {
    for (const id of ids) {
      const st = byId.get(id);
      if (!st) continue;
      if (st.kind === "assign") {
        lineOf[id] = emit(`${st.target} ← ${renderExpression(spec, st.value!)}`, depth);
      } else if (st.kind === "output") {
        lineOf[id] = emit(`hiển thị ${renderExpression(spec, st.value!)}`, depth);
      } else if (st.kind === "if") {
        lineOf[id] = emit(`nếu ${renderExpression(spec, st.condition!)} thì`, depth);
        walk(st.then_body ?? [], depth + 1);
        if ((st.else_body ?? []).length > 0) {
          emit("ngược lại:", depth);
          walk(st.else_body ?? [], depth + 1);
        }
      } else {
        lineOf[id] = emit(`trong khi ${renderExpression(spec, st.condition!)} lặp:`, depth);
        walk(st.body ?? [], depth + 1);
      }
    }
  };

  walk(spec.main, 0);
  return { lines, lineOf };
}

/* ── interpreter tất định ────────────────────────────────────── */

type Value = number | boolean;

export interface ProgramRunResult {
  trace: Trace;
  completion: CompletionState;
  outputs: string[];
}

function fmtValue(v: Value): string {
  return typeof v === "boolean" ? (v ? "đúng" : "sai") : String(v);
}

/**
 * Chạy chương trình, sinh TOÀN BỘ bước. Renderer chỉ đọc kết quả — mọi phép
 * tính, kết quả điều kiện, nhánh được chọn và số lượt lặp đều được phát thành
 * dữ liệu ở đây.
 */
export function runProgram(spec: ProgramSpec): ProgramRunResult {
  const layout = programLines(spec);
  const byStmt = new Map(spec.statements.map((s) => [s.id, s]));
  const byExpr = new Map(spec.expressions.map((e) => [e.id, e]));

  const b = new TraceBuilder([]);
  const env = new Map<string, Value>();
  // §L1: CHỈ nạp biến đã khởi tạo. Biến khai báo mà chưa có giá trị KHÔNG xuất
  // hiện trong `Snapshot.vars` — renderer không được hiểu nhầm là có giá trị thật.
  for (const v of spec.variables) {
    if (!v.initialized) continue;
    const seed = v.type === "integer" ? (v.int_value as number) : (v.bool_value as boolean);
    env.set(v.name, seed);
    b.setVar(v.name, seed);
  }

  const outputs: string[] = [];
  let steps = 0;
  let completion: CompletionState = "completed";

  const evalExpr = (id: string): Value => {
    const n = byExpr.get(id)!;
    switch (n.kind) {
      case "int":
        return n.int_value as number;
      case "bool":
        return n.bool_value as boolean;
      case "var": {
        // Lưới an toàn runtime: spec sai lọt qua validator vẫn KHÔNG được đọc
        // biến chưa có giá trị (thà dừng còn hơn tính bằng undefined).
        if (!env.has(n.name!)) {
          throw new Error(`Biến '${n.name}' chưa có giá trị tại bước này.`);
        }
        return env.get(n.name!)!;
      }
      case "unary": {
        const v = evalExpr(n.operand!);
        return n.op === "not" ? !(v as boolean) : -(v as number);
      }
      case "logic": {
        const l = evalExpr(n.left!) as boolean;
        // Ngắn mạch: giữ đúng ngữ nghĩa Python mà học sinh sẽ gặp.
        if (n.op === "and") return l ? (evalExpr(n.right!) as boolean) : false;
        return l ? true : (evalExpr(n.right!) as boolean);
      }
      case "compare": {
        const l = evalExpr(n.left!);
        const r = evalExpr(n.right!);
        switch (n.op) {
          case "==":
            return l === r;
          case "!=":
            return l !== r;
          case "<":
            return (l as number) < (r as number);
          case "<=":
            return (l as number) <= (r as number);
          case ">":
            return (l as number) > (r as number);
          default:
            return (l as number) >= (r as number);
        }
      }
      default: {
        const l = evalExpr(n.left!) as number;
        const r = evalExpr(n.right!) as number;
        switch (n.op) {
          case "+":
            return l + r;
          case "-":
            return l - r;
          case "*":
            return l * r;
          case "//":
            return r === 0 ? 0 : Math.floor(l / r);
          default:
            return r === 0 ? 0 : ((l % r) + r) % r;
        }
      }
    }
  };

  const budgetLeft = () => steps < PROGRAM_LIMITS.maxExecutionSteps;

  const step = (events: TraceEvent[], narration: string, line: number, checkpoint = false) => {
    steps += 1;
    b.step(events, narration, checkpoint, line);
  };

  const runBlock = (ids: string[]): void => {
    for (const id of ids) {
      if (!budgetLeft()) {
        completion = "limit_reached";
        return;
      }
      const st = byStmt.get(id)!;
      const line = layout.lineOf[id] ?? 1;

      if (st.kind === "assign") {
        const value = evalExpr(st.value!);
        env.set(st.target!, value);
        b.setVar(st.target!, value);
        step(
          [{ type: "assign_var", name: st.target!, value }],
          `${st.target} ← ${renderExpression(spec, st.value!)} = ${fmtValue(value)}.`,
          line,
        );
      } else if (st.kind === "output") {
        const value = evalExpr(st.value!);
        const text = fmtValue(value);
        if (outputs.length < PROGRAM_LIMITS.maxOutputEntries) outputs.push(text);
        step([{ type: "output", text }], `Hiển thị: ${text}.`, line);
      } else if (st.kind === "if") {
        const text = renderExpression(spec, st.condition!);
        const result = evalExpr(st.condition!) as boolean;
        const branch: "then" | "else" = result ? "then" : "else";
        step(
          [
            { type: "evaluate_condition", expression: text, result },
            { type: "enter_branch", branch },
          ],
          `Xét điều kiện ${text} → ${result ? "ĐÚNG" : "SAI"}, chạy nhánh ${result ? "thì" : "ngược lại"}.`,
          line,
          true,
        );
        runBlock(result ? st.then_body ?? [] : st.else_body ?? []);
        if (completion === "limit_reached") return;
      } else {
        const text = renderExpression(spec, st.condition!);
        const maxIter = st.max_iterations ?? PROGRAM_LIMITS.maxWhileIterations;
        let iteration = 0;
        for (;;) {
          if (!budgetLeft()) {
            completion = "limit_reached";
            return;
          }
          const result = evalExpr(st.condition!) as boolean;
          if (!result) {
            step(
              [
                { type: "evaluate_condition", expression: text, result: false },
                { type: "enter_branch", branch: "loop_exit" },
              ],
              `Xét ${text} → SAI, thoát vòng lặp sau ${iteration} lượt.`,
              line,
              true,
            );
            break;
          }
          if (iteration >= maxIter) {
            // Chạm biên: nói THẬT là chưa kết thúc, không im lặng cắt ngang.
            completion = "limit_reached";
            step(
              [{ type: "evaluate_condition", expression: text, result: true }],
              `Đã lặp ${iteration} lượt — chạm giới hạn mô phỏng, dừng lại.`,
              line,
              true,
            );
            return;
          }
          iteration += 1;
          step(
            [
              { type: "evaluate_condition", expression: text, result: true },
              { type: "enter_branch", branch: "loop_body" },
              { type: "loop_iteration", statementId: st.id, iteration },
            ],
            `Xét ${text} → ĐÚNG, vào thân vòng lặp (lượt ${iteration}).`,
            line,
            true,
          );
          runBlock(st.body ?? []);
          if (completion === "limit_reached") return;
        }
      }
    }
  };

  runBlock(spec.main);

  const finalVars = spec.variables
    .map((v) => (env.has(v.name)
      ? `${v.name} = ${fmtValue(env.get(v.name)!)}`
      : `${v.name} chưa có giá trị`))
    .join(", ");
  const result =
    completion === "completed"
      ? `Chương trình kết thúc. ${finalVars}.`
      : `Chương trình chưa kết thúc trong giới hạn mô phỏng (${PROGRAM_LIMITS.maxExecutionSteps} bước). ` +
        "Hệ dừng lại thay vì chạy mãi — em hãy kiểm tra điều kiện lặp xem nó có bao giờ sai không.";
  // W2C-VR1: bước kết thúc KHÔNG trỏ vào dòng nào. Trước đây nó trỏ vào dòng
  // CUỐI của mã giả, mà dòng cuối thường là nhánh KHÔNG chạy (ảnh vr-cf4 final:
  // highlight `x ← 0` trong khi x = 1) — học sinh đọc thành "nhánh đó đã chạy".
  // Không có câu lệnh nào đang thực hiện ⇒ không highlight gì.
  b.step([{ type: "done", result }], result, false);

  return { trace: b.build(), completion, outputs };
}
