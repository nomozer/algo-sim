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

export const PROGRAM_VERSION = "program-1.0";

/** MIRROR `program_spec.LIMITS` — sửa một bên phải sửa bên kia. */
export const PROGRAM_LIMITS = {
  maxStatementNodes: 12,
  maxNestingDepth: 2,
  maxVariables: 8,
  maxExpressionDepth: 4,
  maxExecutionSteps: 200,
  maxWhileIterations: 50,
  maxOutputEntries: 30,
} as const;

export const INT_MIN = -10000;
export const INT_MAX = 10000;

export type ValueType = "integer" | "boolean";
export type StatementKind = "assign" | "if" | "while" | "output";
export type ExpressionKind = "int" | "bool" | "var" | "unary" | "binary" | "compare" | "logic";

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

  // biến
  const rawVars = r.variables;
  if (!Array.isArray(rawVars) || rawVars.length === 0) return fail("Cần ít nhất một biến ban đầu.");
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
    if (type === "integer") {
      if (!isInt(item.int_value)) return fail(`Biến '${name}' cần 'int_value' là số nguyên.`);
      if (item.int_value < INT_MIN || item.int_value > INT_MAX) {
        return fail(`Giá trị của '${name}' ngoài khoảng cho phép.`);
      }
      variables.push({ name, type, int_value: item.int_value, bool_value: null });
    } else {
      if (!isBool(item.bool_value)) return fail(`Biến '${name}' cần 'bool_value' là true/false.`);
      variables.push({ name, type, int_value: null, bool_value: item.bool_value });
    }
    varTypes.set(name, type);
  }

  // biểu thức
  const rawExprs = Array.isArray(r.expressions) ? (r.expressions as Record<string, unknown>[]) : [];
  const expressions: ProgramExpression[] = [];
  const exprById = new Map<string, ProgramExpression>();
  for (const item of rawExprs) {
    const id = item?.id;
    if (typeof id !== "string" || !id.trim()) return fail("Mỗi biểu thức phải có 'id'.");
    if (exprById.has(id)) return fail(`Biểu thức trùng id: '${id}'.`);
    const kind = item.kind as ExpressionKind;
    const node: ProgramExpression = { id, kind };
    switch (kind) {
      case "int":
        if (!isInt(item.int_value)) return fail(`Biểu thức '${id}' cần 'int_value' là số nguyên.`);
        node.int_value = item.int_value;
        break;
      case "bool":
        if (!isBool(item.bool_value)) return fail(`Biểu thức '${id}' cần 'bool_value'.`);
        node.bool_value = item.bool_value;
        break;
      case "var":
        if (typeof item.name !== "string" || !varTypes.has(item.name)) {
          return fail(`Biểu thức '${id}' dùng biến chưa được khai báo.`);
        }
        node.name = item.name;
        break;
      case "unary":
        if (!UNARY_OPS.includes(item.op as never)) return fail(`Toán tử một ngôi không hỗ trợ ở '${id}'.`);
        if (typeof item.operand !== "string") return fail(`Biểu thức '${id}' cần 'operand'.`);
        node.op = item.op as string;
        node.operand = item.operand;
        break;
      case "binary":
      case "compare":
      case "logic": {
        const allowed: readonly string[] =
          kind === "binary" ? ARITHMETIC_OPS : kind === "compare" ? COMPARE_OPS : LOGIC_OPS;
        if (typeof item.op !== "string" || !allowed.includes(item.op)) {
          return fail(`Toán tử không dùng được với loại '${kind}' ở '${id}'.`);
        }
        if (typeof item.left !== "string" || typeof item.right !== "string") {
          return fail(`Biểu thức '${id}' cần 'left' và 'right'.`);
        }
        node.op = item.op;
        node.left = item.left;
        node.right = item.right;
        break;
      }
      default:
        return fail(`Loại biểu thức không hỗ trợ: ${String(kind)}.`);
    }
    expressions.push(node);
    exprById.set(id, node);
  }
  for (const node of expressions) {
    for (const ref of [node.operand, node.left, node.right]) {
      if (ref != null && !exprById.has(ref)) return fail(`Biểu thức '${node.id}' tham chiếu '${ref}' không tồn tại.`);
    }
  }

  // độ sâu + vòng
  const depth = new Map<string, number>();
  const visiting = new Set<string>();
  const walkDepth = (id: string): number | null => {
    const cached = depth.get(id);
    if (cached !== undefined) return cached;
    if (visiting.has(id)) return null;
    visiting.add(id);
    const node = exprById.get(id)!;
    let best = 0;
    for (const child of [node.operand, node.left, node.right]) {
      if (child == null) continue;
      const d = walkDepth(child);
      if (d === null) return null;
      best = Math.max(best, d);
    }
    visiting.delete(id);
    depth.set(id, best + 1);
    return best + 1;
  };
  for (const node of expressions) {
    const d = walkDepth(node.id);
    if (d === null) return fail(`Biểu thức '${node.id}' tham chiếu vòng.`);
    if (d > PROGRAM_LIMITS.maxExpressionDepth) {
      return fail(`Biểu thức '${node.id}' lồng quá ${PROGRAM_LIMITS.maxExpressionDepth} tầng.`);
    }
  }

  // câu lệnh
  const rawStmts = r.statements;
  if (!Array.isArray(rawStmts) || rawStmts.length === 0) return fail("Cần ít nhất một câu lệnh.");
  if (rawStmts.length > PROGRAM_LIMITS.maxStatementNodes) {
    return fail(`Tối đa ${PROGRAM_LIMITS.maxStatementNodes} câu lệnh.`);
  }
  const statements: ProgramStatement[] = [];
  const stmtById = new Map<string, ProgramStatement>();
  for (const item of rawStmts as Record<string, unknown>[]) {
    const id = item?.id;
    if (typeof id !== "string" || !id.trim()) return fail("Mỗi câu lệnh phải có 'id'.");
    if (stmtById.has(id)) return fail(`Câu lệnh trùng id: '${id}'.`);
    const kind = item.kind as StatementKind;
    const node: ProgramStatement = { id, kind, then_body: [], else_body: [], body: [] };
    if (kind === "assign") {
      if (typeof item.target !== "string" || !varTypes.has(item.target)) {
        return fail(`Câu lệnh '${id}' gán cho biến chưa khai báo.`);
      }
      if (typeof item.value !== "string" || !exprById.has(item.value)) {
        return fail(`Câu lệnh '${id}' cần 'value' là id biểu thức.`);
      }
      node.target = item.target;
      node.value = item.value;
    } else if (kind === "output") {
      if (typeof item.value !== "string" || !exprById.has(item.value)) {
        return fail(`Câu lệnh '${id}' cần 'value' là id biểu thức.`);
      }
      node.value = item.value;
    } else if (kind === "if" || kind === "while") {
      if (typeof item.condition !== "string" || !exprById.has(item.condition)) {
        return fail(`Câu lệnh '${id}' cần 'condition' là id biểu thức.`);
      }
      node.condition = item.condition;
      if (kind === "if") {
        node.then_body = Array.isArray(item.then_body) ? (item.then_body as string[]) : [];
        node.else_body = Array.isArray(item.else_body) ? (item.else_body as string[]) : [];
        if (node.then_body.length === 0) return fail(`Rẽ nhánh '${id}' phải có nhánh đúng.`);
      } else {
        node.body = Array.isArray(item.body) ? (item.body as string[]) : [];
        if (node.body.length === 0) return fail(`Vòng lặp '${id}' phải có thân.`);
        if (!isInt(item.max_iterations) || item.max_iterations < 1) {
          return fail(`Vòng lặp '${id}' phải khai 'max_iterations'.`);
        }
        if (item.max_iterations > PROGRAM_LIMITS.maxWhileIterations) {
          return fail(`'max_iterations' của '${id}' vượt ${PROGRAM_LIMITS.maxWhileIterations}.`);
        }
        node.max_iterations = item.max_iterations;
      }
    } else {
      return fail(`Loại câu lệnh không hỗ trợ: ${String(kind)}.`);
    }
    statements.push(node);
    stmtById.set(id, node);
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

  // độ sâu lồng
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
  for (const v of spec.variables) {
    env.set(v.name, v.type === "integer" ? (v.int_value as number) : (v.bool_value as boolean));
    b.setVar(v.name, v.type === "integer" ? (v.int_value as number) : (v.bool_value as boolean));
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
      case "var":
        return env.get(n.name!)!;
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
    .map((v) => `${v.name} = ${fmtValue(env.get(v.name)!)}`)
    .join(", ");
  const result =
    completion === "completed"
      ? `Chương trình kết thúc. ${finalVars}.`
      : `Chương trình chưa kết thúc trong giới hạn mô phỏng (${PROGRAM_LIMITS.maxExecutionSteps} bước). ` +
        "Hệ dừng lại thay vì chạy mãi — em hãy kiểm tra điều kiện lặp xem nó có bao giờ sai không.";
  b.step([{ type: "done", result }], result, false, layout.lines.length);

  return { trace: b.build(), completion, outputs };
}
