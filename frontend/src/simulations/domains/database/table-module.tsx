import { registerSimulation } from "../../registry";
import type { SimulationModule, WorkspaceProps } from "../../types";

/**
 * M17 W2B — `database.relational_table_query`: TRUY VẤN MỘT BẢNG HỮU HẠN.
 *
 * Engine TẤT ĐỊNH mirror của `backend/app/simulation/table_query_engine.py`.
 * LLM chỉ đưa lược đồ + các dòng + yêu cầu; MỌI phán quyết giữ/loại, thứ tự sắp
 * xếp và giá trị tổng hợp do engine này tính (bất biến R0).
 *
 * Dấu vết 9 giai đoạn: đọc dòng → tính vị từ → giữ/loại → chốt tập lọc → chiếu
 * cột → sắp xếp ổn định → giới hạn → tích luỹ → kết quả.
 */

export const TABLE_SPEC_VERSION = "table-1.0";
export const COLUMN_TYPES = ["text", "number", "boolean"] as const;
export const COMPARE_OPS = ["=", "!=", ">", ">=", "<", "<=", "contains"] as const;
export const OPS_BY_TYPE: Record<string, readonly string[]> = {
  number: ["=", "!=", ">", ">=", "<", "<="],
  text: ["=", "!=", "contains"],
  boolean: ["=", "!="],
};
export const AGGREGATE_FUNCS = ["count", "sum", "avg", "min", "max"] as const;
export const MAX_ROWS = 30;
export const MAX_COLUMNS = 8;

type Cell = string | number | boolean | null;
export interface TableColumn { name: string; type: string; label?: string | null }
export interface Predicate {
  op: string;
  column?: string;
  value?: Cell;
  clauses?: Predicate[];
}
export interface TableConfig {
  specVersion: string;
  schema: TableColumn[];
  rows: Record<string, Cell>[];
  filter: Predicate | null;
  projection: string[] | null;
  sort: { column: string; direction: string } | null;
  limit: number | null;
  aggregate: { func: string; column?: string | null } | null;
  notes?: string | null;
}
export interface TableStep {
  kind: string;
  narration: string;
  row_index: number | null;
  detail: Record<string, unknown>;
}
export interface TableState {
  config: TableConfig;
  steps: TableStep[];
  filteredIndices: number[];
  projectedColumns: string[];
  orderedIndices: number[];
  resultRows: Record<string, Cell>[];
  aggregateResult: { func: string; column?: string | null; value: Cell; counted: number } | null;
  cursor: number;
}

/* ── validator MIRROR (hai tầng: BE đã kiểm, FE kiểm lại) ─────────── */
export function validateTableConfig(
  raw: unknown,
): { ok: true; config: TableConfig } | { ok: false; error: string } {
  const fail = (e: string) => ({ ok: false as const, error: e });
  if (!raw || typeof raw !== "object") return fail("Cấu hình truy vấn bảng không hợp lệ.");
  const r = raw as Record<string, unknown>;

  const schema = r.schema;
  if (!Array.isArray(schema) || schema.length === 0) return fail("Thiếu lược đồ bảng.");
  if (schema.length > MAX_COLUMNS) return fail(`Bảng quá ${MAX_COLUMNS} cột.`);
  const types = new Map<string, string>();
  for (const c of schema as TableColumn[]) {
    if (!c || typeof c.name !== "string" || !c.name) return fail("Có cột thiếu tên.");
    if (types.has(c.name)) return fail(`Tên cột bị lặp: ${c.name}.`);
    if (!COLUMN_TYPES.includes(c.type as never)) return fail(`Cột ${c.name} sai kiểu.`);
    types.set(c.name, c.type);
  }

  const rows = r.rows;
  if (!Array.isArray(rows) || rows.length === 0) return fail("Bảng chưa có dòng dữ liệu nào.");
  if (rows.length > MAX_ROWS) return fail(`Bảng quá ${MAX_ROWS} dòng.`);
  for (const row of rows) {
    if (!row || typeof row !== "object") return fail("Dòng dữ liệu không hợp lệ.");
    for (const key of Object.keys(row)) {
      if (!types.has(key)) return fail(`Dòng có cột lạ: ${key}.`);
    }
  }

  const checkPred = (p: unknown, depth: number): string | null => {
    if (!p || typeof p !== "object") return "điều kiện lọc không hợp lệ";
    const q = p as Predicate;
    if (q.op === "and" || q.op === "or") {
      if (depth >= 2) return "điều kiện lồng quá 2 tầng";
      if (!Array.isArray(q.clauses) || q.clauses.length < 2) return "phép logic cần ≥2 vế";
      for (const sub of q.clauses) {
        const e = checkPred(sub, depth + 1);
        if (e) return e;
      }
      return null;
    }
    if (!COMPARE_OPS.includes(q.op as never)) return `toán tử không hỗ trợ: ${q.op}`;
    if (!q.column || !types.has(q.column)) return `cột không có trong bảng: ${q.column}`;
    const allowed = OPS_BY_TYPE[types.get(q.column)!];
    if (!allowed.includes(q.op)) return `toán tử "${q.op}" không dùng được với cột ${q.column}`;
    return null;
  };
  if (r.filter != null) {
    const e = checkPred(r.filter, 0);
    if (e) return fail(`Điều kiện lọc không hợp lệ: ${e}.`);
  }
  if (r.projection != null) {
    if (!Array.isArray(r.projection) || r.projection.length === 0)
      return fail("Danh sách cột hiển thị rỗng.");
    for (const c of r.projection) if (!types.has(c as string)) return fail(`Cột lạ: ${c}.`);
  }
  if (r.sort != null) {
    const st = r.sort as { column?: string; direction?: string };
    if (!st.column || !types.has(st.column)) return fail(`Sắp xếp theo cột lạ: ${st.column}.`);
    if (st.direction && !["asc", "desc"].includes(st.direction))
      return fail("Chiều sắp xếp không hợp lệ.");
  }
  if (r.limit != null) {
    if (typeof r.limit !== "number" || !Number.isInteger(r.limit) || r.limit < 1)
      return fail("Giới hạn phải là số nguyên ≥1.");
    if (r.limit > (rows as unknown[]).length) return fail("Giới hạn lớn hơn số dòng.");
  }
  if (r.aggregate != null) {
    const a = r.aggregate as { func?: string; column?: string | null };
    if (!AGGREGATE_FUNCS.includes(a.func as never)) return fail(`Hàm tổng hợp lạ: ${a.func}.`);
    if (a.func !== "count") {
      if (!a.column || !types.has(a.column)) return fail(`Hàm ${a.func} cần một cột có thật.`);
      if ((a.func === "sum" || a.func === "avg") && types.get(a.column) !== "number")
        return fail(`Hàm ${a.func} chỉ dùng với cột kiểu số.`);
    }
  }

  return {
    ok: true,
    config: {
      specVersion: TABLE_SPEC_VERSION,
      schema: schema as TableColumn[],
      rows: rows as Record<string, Cell>[],
      filter: (r.filter as Predicate) ?? null,
      projection: (r.projection as string[]) ?? null,
      sort: (r.sort as TableState["config"]["sort"]) ?? null,
      limit: (r.limit as number) ?? null,
      aggregate: (r.aggregate as TableState["config"]["aggregate"]) ?? null,
      notes: (r.notes as string) ?? null,
    },
  };
}

/* ── engine TẤT ĐỊNH ──────────────────────────────────────────────── */
const fmt = (v: Cell): string =>
  typeof v === "boolean" ? (v ? "đúng" : "sai") : v === null || v === undefined ? "(trống)" : String(v);

function compare(op: string, left: Cell, right: Cell): boolean {
  if (op === "=") return left === right;
  if (op === "!=") return left !== right;
  if (op === "contains") return String(left).toLowerCase().includes(String(right).toLowerCase());
  if (left === null || right === null) return false;
  if (op === ">") return left > right;
  if (op === ">=") return left >= right;
  if (op === "<") return left < right;
  return left <= right;
}

function evalPredicate(p: Predicate, row: Record<string, Cell>): [boolean, Record<string, unknown>[]] {
  if (p.op === "and" || p.op === "or") {
    const why: Record<string, unknown>[] = [];
    const values: boolean[] = [];
    for (const sub of p.clauses ?? []) {
      const [ok, w] = evalPredicate(sub, row);
      values.push(ok);
      why.push(...w);
    }
    const result = p.op === "and" ? values.every(Boolean) : values.some(Boolean);
    why.push({ kind: "logic", op: p.op, result });
    return [result, why];
  }
  const actual = row[p.column!] ?? null;
  const ok = compare(p.op, actual, p.value ?? null);
  return [ok, [{ kind: "compare", column: p.column, op: p.op, value: p.value, actual, result: ok }]];
}

const explain = (why: Record<string, unknown>[]): string =>
  why
    .map((w) =>
      w.kind === "compare"
        ? `${w.column}=${fmt(w.actual as Cell)} ${w.op} ${fmt(w.value as Cell)} → ${w.result ? "đúng" : "sai"}`
        : `${w.op === "and" ? "VÀ" : "HOẶC"} → ${w.result ? "đúng" : "sai"}`,
    )
    .join("; ");

const AGG_VI: Record<string, string> = {
  count: "Đếm", sum: "Tổng", avg: "Trung bình", min: "Nhỏ nhất", max: "Lớn nhất",
};
const aggLabel = (a: { func: string; column?: string | null }): string =>
  AGG_VI[a.func] + (a.column ? ` của ${a.column}` : " số dòng");

/** Khoá sắp xếp toàn phần — null luôn xuống cuối (mirror `_sort_key`). */
const sortRank = (v: Cell): [number, number | string] =>
  v === null || v === undefined ? [1, ""] : typeof v === "boolean" ? [0, v ? 1 : 0] : [0, v as number | string];

export function runTableQuery(config: TableConfig): Omit<TableState, "config" | "cursor"> {
  const { schema, rows } = config;
  const colNames = schema.map((c) => c.name);
  const steps: TableStep[] = [];
  const push = (kind: string, narration: string, row_index: number | null = null,
                detail: Record<string, unknown> = {}) =>
    steps.push({ kind, narration, row_index, detail });

  // 1–3 đọc · tính vị từ · giữ hoặc loại
  const kept: number[] = [];
  rows.forEach((row, i) => {
    push("read_row",
      `Đọc dòng ${i + 1}: ` + colNames.slice(0, 3).map((c) => `${c}=${fmt(row[c] ?? null)}`).join(", ") +
      (colNames.length > 3 ? "…" : ""), i, { row: { ...row } });
    if (!config.filter) {
      kept.push(i);
      push("keep", `Không có điều kiện lọc → giữ dòng ${i + 1}.`, i, { reasons: [] });
      return;
    }
    const [ok, why] = evalPredicate(config.filter, row);
    push("evaluate", `Xét điều kiện trên dòng ${i + 1}: ${explain(why)}`, i, { reasons: why, result: ok });
    if (ok) kept.push(i);
    push(ok ? "keep" : "drop",
      `Dòng ${i + 1} ` + (ok ? "THOẢ điều kiện → giữ lại." : "KHÔNG thoả → loại."), i, { reasons: why });
  });

  // 4 chốt tập lọc
  push("filtered_set", `Sau khi lọc còn ${kept.length}/${rows.length} dòng.`, null,
    { kept_indices: [...kept] });

  // 5 chiếu cột
  const projection = config.projection ?? colNames;
  push("projection",
    config.projection ? `Chỉ giữ lại cột: ${projection.join(", ")}.` : "Giữ nguyên mọi cột.",
    null, { columns: [...projection] });

  // 6 sắp xếp ỔN ĐỊNH — Array.prototype.sort của JS là ổn định (ES2019+)
  let ordered = [...kept];
  if (config.sort) {
    const before = [...ordered];
    const dir = config.sort.direction === "desc" ? -1 : 1;
    ordered.sort((a, b) => {
      const [ra, va] = sortRank(rows[a][config.sort!.column] ?? null);
      const [rb, vb] = sortRank(rows[b][config.sort!.column] ?? null);
      if (ra !== rb) return ra - rb;          // null xuống cuối ở CẢ hai chiều
      return va < vb ? -dir : va > vb ? dir : 0;
    });
    push("sort",
      `Sắp xếp theo ${config.sort.column} ${config.sort.direction === "desc" ? "giảm dần" : "tăng dần"}` +
      " (ổn định: hai dòng bằng nhau giữ nguyên thứ tự cũ).", null,
      { before, after: [...ordered], column: config.sort.column, direction: config.sort.direction });
  }

  // 7 giới hạn
  if (config.limit != null) {
    const before = [...ordered];
    ordered = ordered.slice(0, config.limit);
    push("limit", `Chỉ lấy ${config.limit} dòng đầu (còn ${ordered.length}).`, null,
      { before, after: [...ordered], limit: config.limit });
  }

  // 8 tích luỹ
  let aggregateResult: TableState["aggregateResult"] = null;
  if (config.aggregate) {
    const { func, column } = config.aggregate;
    let acc: number | null = null;
    let count = 0;
    for (const i of ordered) {
      const value = column ? rows[i][column] ?? null : null;
      if (func !== "count" && value === null) {
        push("accumulate", `Dòng ${i + 1} không có giá trị ${column} → bỏ qua.`, i,
          { skipped: true, accumulator: acc, count });
        continue;
      }
      count += 1;
      const n = value as number;
      if (func === "count") acc = count;
      else if (func === "sum" || func === "avg") acc = (acc ?? 0) + n;
      else if (func === "min") acc = acc === null ? n : Math.min(acc, n);
      else acc = acc === null ? n : Math.max(acc, n);
      const shown = func === "avg" ? Math.round((acc! / count) * 10000) / 10000 : acc;
      push("accumulate",
        `Dòng ${i + 1}: ` + (func === "count"
          ? `đếm thêm 1 → ${count}`
          : `${column}=${fmt(value)} → ${aggLabel(config.aggregate).toLowerCase()} tạm thời ${fmt(shown as Cell)}`),
        i, { value, accumulator: acc, count });
    }
    const value: Cell =
      func === "avg" ? (count ? Math.round((acc! / count) * 10000) / 10000 : null)
      : func === "count" ? count : acc;
    aggregateResult = { func, column, value, counted: count };
  }

  // 9 kết quả
  const resultRows = ordered.map((i) => {
    const o: Record<string, Cell> = {};
    for (const c of projection) o[c] = rows[i][c] ?? null;
    return o;
  });
  push("result",
    aggregateResult
      ? `${aggLabel(config.aggregate!)} = ${fmt(aggregateResult.value)}`
      : `Kết quả: ${resultRows.length} dòng.`,
    null, { rows: resultRows, aggregateResult });

  return { steps, filteredIndices: kept, projectedColumns: [...projection],
           orderedIndices: ordered, resultRows, aggregateResult };
}

/* ── renderer ─────────────────────────────────────────────────────── */
const clamp = (s: TableState, n: number) => Math.max(0, Math.min(n, s.steps.length - 1));

export function TableWorkspace({ state }: WorkspaceProps<TableConfig, TableState>) {
  const at = clamp(state, state.cursor);
  const step = state.steps[at];
  const cols = state.config.schema.map((c) => c.name);
  const projected = new Set(state.projectedColumns);
  // Chỉ hé lộ phán quyết của những dòng ĐÃ ĐI QUA — không lộ kết quả từ bước 0.
  const decided = new Map<number, boolean>();
  for (let i = 0; i <= at; i++) {
    const s = state.steps[i];
    if ((s.kind === "keep" || s.kind === "drop") && s.row_index != null) {
      decided.set(s.row_index, s.kind === "keep");
    }
  }
  const isFinal = at === state.steps.length - 1;

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div className="sim-stage" style={{ overflowX: "auto" }}>
        <table className="tq-table" style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "right", padding: "4px 8px", color: "var(--ink-muted)" }}>#</th>
              {cols.map((c) => (
                <th key={c} style={{
                  textAlign: "left", padding: "4px 10px",
                  borderBottom: "1px solid var(--hairline)",
                  opacity: projected.has(c) ? 1 : 0.4,
                  fontWeight: projected.has(c) ? 700 : 400,
                }}>
                  {state.config.schema.find((s) => s.name === c)?.label ?? c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {state.config.rows.map((row, i) => {
              const current = step.row_index === i;
              const verdict = decided.get(i);
              const bg = current ? "var(--accent-orange)"
                : verdict === true ? "var(--accent-green)"
                : verdict === false ? "var(--surface)" : "transparent";
              return (
                <tr key={i} style={{
                  background: bg,
                  opacity: verdict === false && !current ? 0.45 : 1,
                  textDecoration: verdict === false ? "line-through" : "none",
                }}>
                  <td style={{ textAlign: "right", padding: "3px 8px", color: "var(--ink-muted)" }}>{i + 1}</td>
                  {cols.map((c) => (
                    <td key={c} style={{ padding: "3px 10px", opacity: projected.has(c) ? 1 : 0.35 }}>
                      {fmt(row[c] ?? null)}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {state.config.aggregate && (
        <p className="notes">
          {aggLabel(state.config.aggregate)} — đang cộng dồn:{" "}
          {fmt((step.detail.accumulator as Cell) ?? null)}
          {step.detail.count != null && ` (đã tính ${String(step.detail.count)} dòng)`}
        </p>
      )}
      <p className="notes">{step.narration}</p>
      {isFinal && state.aggregateResult && (
        <p className="notes"><strong>
          {aggLabel(state.config.aggregate!)} = {fmt(state.aggregateResult.value)}
        </strong></p>
      )}
    </div>
  );
}

export function TableInspector({ state }: WorkspaceProps<TableConfig, TableState>) {
  const at = clamp(state, state.cursor);
  const isFinal = at === state.steps.length - 1;
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <p className="notes">
        Bảng: {state.config.rows.length} dòng · {state.config.schema.length} cột
      </p>
      {state.config.sort && (
        <p className="notes">
          Sắp xếp: {state.config.sort.column}{" "}
          {state.config.sort.direction === "desc" ? "giảm dần" : "tăng dần"} (ổn định)
        </p>
      )}
      {/* Kết quả chỉ hiện Ở BƯỚC CUỐI — hé lộ sớm là làm mất phần học sinh cần nghĩ. */}
      {isFinal ? (
        <p className="notes">
          Kết quả: {state.resultRows.length} dòng
          {state.aggregateResult && ` · ${aggLabel(state.config.aggregate!)} = ${fmt(state.aggregateResult.value)}`}
        </p>
      ) : (
        <p className="notes">Kết quả hiện dần theo từng bước…</p>
      )}
    </div>
  );
}

export function makeTableModule(): SimulationModule<TableConfig, TableState> {
  return {
    id: "database.relational_table_query",
    domain: "database",
    title: "Truy vấn bảng dữ liệu",
    interactionMode: "progressive",
    supportedVisualModes: ["2d"],
    renderers: { "2d": TableWorkspace },
    validateConfig: validateTableConfig,
    init: (config) => ({ config, ...runTableQuery(config), cursor: 0 }),
    apply: (state) => state,
    timeline: {
      stepCount: (state) => state.steps.length,
      currentStep: (state) => state.cursor,
      goToStep: (state, n) => ({ ...state, cursor: clamp(state, n) }),
    },
    Workspace: TableWorkspace,
    Inspector: TableInspector,
    getExplainContext: (state) => ({
      simulation: "database.relational_table_query",
      columns: state.config.schema.map((c) => `${c.name}:${c.type}`),
      rowCount: state.config.rows.length,
      step: state.steps[clamp(state, state.cursor)]?.narration ?? "",
      filteredCount: state.filteredIndices.length,
      resultCount: state.resultRows.length,
      aggregate: state.aggregateResult,
    }),
  };
}


export function registerDatabaseDomain(): void {
  registerSimulation(makeTableModule());
}
