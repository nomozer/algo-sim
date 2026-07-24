import { registerSimulation } from "../../registry";
import { IconCheck, IconCross, IconPlay } from "../../../components/icons";
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

/**
 * W2B-PATCH §C — marker ô thiếu dữ liệu. MIRROR của
 * `table_query_engine.MISSING_VALUE_MARKERS`; đổi một bên thì phải đổi bên kia
 * (test parity khoá con số kết quả ở cả hai phía).
 *
 * Ô rỗng là thiếu dữ liệu ở MỌI kiểu cột; CHỮ mô tả sự thiếu chỉ áp cho cột
 * nhận null (số/đúng-sai mặc định, hoặc cột khai `nullable: true`) — ở cột chữ
 * thì "trống" có thể là dữ liệu thật.
 */
export const MISSING_VALUE_MARKERS = ["trống", "—", "–", "n/a", "null"] as const;
export const MARKER_NULLABLE_TYPES = ["number", "boolean"] as const;
/** Thứ tự tầng CỐ ĐỊNH của engine — aggregate tính SAU limit. */
export const PIPELINE_STAGE_ORDER = ["filter", "projection", "sort", "limit", "aggregate"] as const;

type Cell = string | number | boolean | null;
export interface TableColumn {
  name: string;
  type: string;
  label?: string | null;
  /** undefined/null = mặc định theo kiểu; false = cột KHÔNG nhận ô trống. */
  nullable?: boolean | null;
}
export interface CellNormalization {
  row: number;
  column: string;
  column_type: string;
  original: unknown;
  normalized: null;
  reason: string;
}
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
  normalizations: CellNormalization[];
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

/* ── W2B-PATCH §C — BIÊN chuẩn hoá ô thiếu dữ liệu (mirror backend) ──
 * Thứ tự BẮT BUỘC: ô thô → chuẩn hoá theo lược đồ → ép kiểu → validate.
 * Engine bên dưới CHỈ thấy null hoặc giá trị đã đúng kiểu — nó không bao giờ
 * phải hiểu chữ "trống" (trước bản vá, chuỗi đó lọt vào và AVG đếm luôn cả ô
 * trống ⇒ kết quả sai câm).                                                */
function markerReason(cell: unknown, type: string, nullable?: boolean | null): string | null {
  if (typeof cell !== "string") return null;
  const norm = cell.trim().replace(/\s+/g, " ");
  if (norm === "") return "empty_cell";
  const isMarker = (MISSING_VALUE_MARKERS as readonly string[]).includes(norm.toLowerCase());
  if (!isMarker) return null;
  if (nullable === null || nullable === undefined)
    return (MARKER_NULLABLE_TYPES as readonly string[]).includes(type) ? "missing_value_marker" : null;
  return "missing_value_marker";
}

/** Ép MỘT ô về kiểu cột. Không ép được → lỗi (không đoán bừa, không hoá 0). */
function coerceCell(cell: unknown, type: string): { value: Cell } | { error: string } {
  if (cell === null || cell === undefined) return { value: null };
  if (type === "number") {
    if (typeof cell === "boolean") return { error: "giá trị đúng/sai không dùng cho cột kiểu số" };
    if (typeof cell === "number") return { value: cell };
    if (typeof cell === "string") {
      const n = Number(cell);
      return Number.isFinite(n) && cell.trim() !== ""
        ? { value: n }
        : { error: `"${cell}" không phải số` };
    }
    return { error: "ô này không phải số" };
  }
  if (type === "boolean") {
    if (typeof cell === "boolean") return { value: cell };
    if (typeof cell === "string" && ["true", "false", "đúng", "sai"].includes(cell.toLowerCase()))
      return { value: ["true", "đúng"].includes(cell.toLowerCase()) };
    if (cell === 0 || cell === 1) return { value: Boolean(cell) };
    return { error: "ô này không phải giá trị đúng/sai" };
  }
  return { value: typeof cell === "string" ? cell : String(cell) };
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
  const nullables = new Map<string, boolean | null | undefined>();
  for (const c of schema as TableColumn[]) {
    if (!c || typeof c.name !== "string" || !c.name) return fail("Có cột thiếu tên.");
    if (types.has(c.name)) return fail(`Tên cột bị lặp: ${c.name}.`);
    if (!COLUMN_TYPES.includes(c.type as never)) return fail(`Cột ${c.name} sai kiểu.`);
    if (c.nullable !== undefined && c.nullable !== null && typeof c.nullable !== "boolean")
      return fail(`Cột ${c.name} khai nullable không phải đúng/sai.`);
    types.set(c.name, c.type);
    nullables.set(c.name, c.nullable);
  }

  const rows = r.rows;
  if (!Array.isArray(rows) || rows.length === 0) return fail("Bảng chưa có dòng dữ liệu nào.");
  if (rows.length > MAX_ROWS) return fail(`Bảng quá ${MAX_ROWS} dòng.`);
  const normalizations: CellNormalization[] = [];
  const normRows: Record<string, Cell>[] = [];
  for (const [i, row] of (rows as unknown[]).entries()) {
    if (!row || typeof row !== "object") return fail("Dòng dữ liệu không hợp lệ.");
    const src = row as Record<string, unknown>;
    for (const key of Object.keys(src)) {
      if (!types.has(key)) return fail(`Dòng có cột lạ: ${key}.`);
    }
    const out: Record<string, Cell> = {};
    for (const [name, type] of types) {
      const cell = src[name];
      const nullable = nullables.get(name);
      const reason = markerReason(cell, type, nullable);
      if (reason !== null) {
        if (nullable === false)
          return fail(`Dòng ${i + 1}, cột ${name}: cột này không nhận ô trống.`);
        normalizations.push({
          row: i + 1, column: name, column_type: type,
          original: cell, normalized: null, reason,
        });
        out[name] = null;
        continue;
      }
      if ((cell === null || cell === undefined) && nullable === false)
        return fail(`Dòng ${i + 1}, cột ${name}: cột này không nhận ô trống.`);
      const c = coerceCell(cell, type);
      if ("error" in c) return fail(`Dòng ${i + 1}, cột ${name}: ${c.error}.`);
      out[name] = c.value;
    }
    normRows.push(out);
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
      rows: normRows,
      normalizations,
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
// `schema` tuỳ chọn: có thì hiển thị NHÃN cột cho học sinh (không lộ id
// `diem_kt`). Engine gọi không truyền schema (narration engine không hiển thị,
// chỉ để explain/debug); renderer luôn truyền schema.
const aggLabel = (a: { func: string; column?: string | null },
                  schema?: TableColumn[]): string => {
  const col = a.column
    ? (schema?.find((c) => c.name === a.column)?.label ?? a.column) : null;
  return AGG_VI[a.func] + (col ? ` của ${col}` : " số dòng");
};

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

/** Nhãn học sinh cho một cột — KHÔNG bao giờ để lộ id kỹ thuật (`diem_kt`). */
const labelOf = (schema: TableColumn[], name: string): string =>
  schema.find((c) => c.name === name)?.label ?? name;

/** Giai đoạn nào của pipeline đã đi qua tính tới bước `at` — đọc từ trace,
 *  không tự suy. Dùng để hé lộ dần: projection chỉ mờ cột SAU khi tới bước
 *  chiếu; thứ tự sắp xếp chỉ hiện SAU bước sắp xếp. */
function stagesReached(state: TableState, at: number) {
  const seen = (kind: string) =>
    state.steps.slice(0, at + 1).some((s) => s.kind === kind);
  return {
    filtered: seen("filtered_set"),
    projected: seen("projection"),
    sorted: seen("sort"),
    limited: seen("limit"),
    aggregated: seen("accumulate") || seen("result"),
  };
}

/** Tường thuật learner-facing dựng TỪ structured detail + NHÃN cột — engine
 *  trace giữ nguyên, đây chỉ là lớp trình bày (không hiển thị id kỹ thuật). */
function narrate(step: TableStep, schema: TableColumn[],
                 aggregate: TableConfig["aggregate"]): string {
  const L = (c: unknown) => labelOf(schema, String(c));
  const d = step.detail;
  if (step.kind === "evaluate" || step.kind === "keep" || step.kind === "drop") {
    const reasons = (d.reasons as Record<string, unknown>[]) ?? [];
    const parts = reasons
      .filter((r) => r.kind === "compare")
      .map((r) => `${L(r.column)} = ${fmt(r.actual as Cell)} ${
        { "=": "bằng", "!=": "khác", ">": "lớn hơn", ">=": "≥", "<": "nhỏ hơn",
          "<=": "≤", contains: "chứa" }[r.op as string] ?? r.op
      } ${fmt(r.value as Cell)} → ${r.result ? "đúng" : "sai"}`);
    const verdict = step.kind === "keep" ? " ⇒ GIỮ LẠI"
      : step.kind === "drop" ? " ⇒ LOẠI" : "";
    const idx = step.row_index != null ? `Hàng ${step.row_index + 1}: ` : "";
    return idx + (parts.join("; ") || "không có điều kiện") + verdict;
  }
  if (step.kind === "accumulate") {
    const idx = step.row_index != null ? `Hàng ${step.row_index + 1}: ` : "";
    if (d.skipped) return `${idx}ô ${L(aggregate?.column)} còn trống → bỏ qua, không tính là 0.`;
    if (aggregate?.func === "count") return `${idx}đếm thêm 1 → ${String(d.count)}.`;
    return `${idx}${L(aggregate?.column)} = ${fmt(d.value as Cell)} → giá trị tích luỹ ${
      fmt(d.accumulator as Cell)} (đã tính ${String(d.count)} hàng).`;
  }
  if (step.kind === "sort") {
    return `Sắp xếp theo ${L(d.column)} ${d.direction === "desc" ? "giảm dần" : "tăng dần"
      } — hai hàng bằng nhau giữ nguyên thứ tự cũ (sắp xếp ổn định).`;
  }
  if (step.kind === "projection") {
    const cols = (d.columns as string[]) ?? [];
    return `Chỉ giữ lại cột: ${cols.map(L).join(", ")}.`;
  }
  if (step.kind === "read_row") {
    const row = (d.row as Record<string, Cell>) ?? {};
    return `Đọc hàng ${(step.row_index ?? 0) + 1}: ` +
      schema.slice(0, 3).map((c) => `${c.label ?? c.name} = ${fmt(row[c.name] ?? null)}`).join(", ") +
      (schema.length > 3 ? "…" : "");
  }
  // filtered_set/limit/result — narration engine không chứa id cột
  return step.narration;
}

// Trạng thái hàng — icon là component SVG (guard ui-hygiene cấm ký tự Unicode
// làm icon); phân biệt KHÔNG chỉ bằng màu (§7): có nhãn chữ + hình + viền.
const STATUS = {
  current: { label: "Đang xét", Icon: IconPlay, bg: "var(--accent-orange)", fg: "#fff" },
  keep: { label: "Giữ", Icon: IconCheck, bg: "var(--accent-green)", fg: "#fff" },
  drop: { label: "Loại", Icon: IconCross, bg: "var(--surface)", fg: "var(--ink-muted)" },
  cutoff: { label: "Không lấy", Icon: null, bg: "var(--surface)", fg: "var(--ink-muted)" },
} as const;

/**
 * W2B-PATCH §E — CHỈ BÁO TẦNG: truy vấn này gồm những bước nào, đang ở bước
 * nào. Danh sách bước DẪN XUẤT TỪ CHÍNH CONFIG (`PIPELINE_STAGE_ORDER`), nên
 * nó không bao giờ vẽ ra bước mà truy vấn không có — và một spec bỏ sót bước
 * sẽ hiện ra ngay trước mắt thay vì lặng lẽ biến mất.
 */
function stageChips(config: TableConfig, reached: ReturnType<typeof stagesReached>) {
  const present: { key: string; label: string; done: boolean }[] = [];
  if (config.filter) present.push({ key: "filter", label: "Lọc", done: reached.filtered });
  if (config.projection?.length)
    present.push({ key: "projection", label: "Chọn cột", done: reached.projected });
  if (config.sort)
    present.push({
      key: "sort",
      label: `Sắp xếp ${config.sort.direction === "desc" ? "giảm dần" : "tăng dần"}`,
      done: reached.sorted,
    });
  if (config.limit != null)
    present.push({ key: "limit", label: `Lấy ${config.limit} dòng`, done: reached.limited });
  if (config.aggregate)
    present.push({
      key: "aggregate",
      label: `Tính ${
        { count: "số dòng", sum: "tổng", avg: "trung bình", min: "nhỏ nhất", max: "lớn nhất" }[
          config.aggregate.func
        ] ?? config.aggregate.func
      }`,
      done: reached.aggregated,
    });
  return present;
}

export function TableWorkspace({ state }: WorkspaceProps<TableConfig, TableState>) {
  const at = clamp(state, state.cursor);
  const step = state.steps[at];
  const schema = state.config.schema;
  const cols = schema.map((c) => c.name);
  const projected = new Set(state.projectedColumns);
  const stage = stagesReached(state, at);

  // Phán quyết của các hàng ĐÃ ĐI QUA (không lộ kết quả từ bước 0).
  const decided = new Map<number, boolean>();
  for (let i = 0; i <= at; i++) {
    const s = state.steps[i];
    if ((s.kind === "keep" || s.kind === "drop") && s.row_index != null) {
      decided.set(s.row_index, s.kind === "keep");
    }
  }
  const isFinal = at === state.steps.length - 1;

  // Thứ tự HIỂN THỊ hàng: chỉ đổi theo thứ tự sắp xếp SAU khi đã tới bước sắp
  // xếp — trước đó giữ thứ tự gốc để lọc quan sát được trên bảng nguồn. Lấy
  // TỪ TRACE (engine đã sắp), renderer không tự sắp.
  const sortStep = state.steps.find((s) => s.kind === "sort");
  const limitStep = state.steps.find((s) => s.kind === "limit");
  const cutoff = new Set<number>();
  let order = cols.length ? state.config.rows.map((_, i) => i) : [];
  if (stage.sorted && sortStep) {
    order = [...(sortStep.detail.after as number[])];
    if (stage.limited && limitStep) {
      const after = new Set(limitStep.detail.after as number[]);
      for (const i of limitStep.detail.before as number[]) if (!after.has(i)) cutoff.add(i);
      order = [...(limitStep.detail.before as number[])]; // vẫn hiện hàng bị cắt, có nhãn
    }
  }

  const statusOf = (i: number): keyof typeof STATUS | null => {
    if (step.row_index === i && step.kind !== "result") return "current";
    if (cutoff.has(i)) return "cutoff";
    const v = decided.get(i);
    return v === true ? "keep" : v === false ? "drop" : null;
  };

  const chips = stageChips(state.config, stage);

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      {chips.length > 1 && (
        <ol className="tq-stages" style={{
          display: "flex", flexWrap: "wrap", gap: "var(--sp-xs)",
          listStyle: "none", margin: 0, padding: 0,
        }}>
          {chips.map((c, i) => (
            <li key={c.key} data-stage={c.key} data-stage-done={String(c.done)}
                style={{
                  display: "flex", alignItems: "center", gap: "var(--sp-xs)",
                  padding: "2px 10px", borderRadius: "999px", whiteSpace: "nowrap",
                  border: `1px solid ${c.done ? "var(--accent-green)" : "var(--hairline)"}`,
                  color: c.done ? "var(--ink)" : "var(--ink-muted)",
                  fontWeight: c.done ? 600 : 400,
                }}>
              {/* Số thứ tự làm chỉ dấu thứ hai — không phân biệt chỉ bằng màu. */}
              <span aria-hidden="true">{i + 1}.</span>
              {c.label}
              {c.done && <IconCheck />}
            </li>
          ))}
        </ol>
      )}
      <div className="sim-stage" style={{ overflowX: "auto" }}>
        <table className="tq-table" style={{ borderCollapse: "collapse", width: "100%", minWidth: "min-content" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", padding: "4px 8px", color: "var(--ink-muted)", whiteSpace: "nowrap" }}>
                Trạng thái
              </th>
              {cols.map((c) => {
                // Cột không được chọn CHỈ mờ SAU khi đã qua bước chọn cột.
                const dim = stage.projected && !projected.has(c);
                return (
                  <th key={c} style={{
                    textAlign: "left", padding: "4px 10px", whiteSpace: "nowrap",
                    borderBottom: "1px solid var(--hairline)",
                    opacity: dim ? 0.35 : 1, fontWeight: dim ? 400 : 700,
                    textDecoration: dim ? "line-through" : "none",
                  }}>
                    {labelOf(schema, c)}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {order.map((i) => {
              const row = state.config.rows[i];
              const st = statusOf(i);
              const badge = st ? STATUS[st] : null;
              return (
                <tr key={i} style={{
                  background: st === "current" ? "color-mix(in srgb, var(--accent-orange) 22%, transparent)"
                    : st === "keep" ? "color-mix(in srgb, var(--accent-green) 18%, transparent)" : "transparent",
                  opacity: st === "drop" || st === "cutoff" ? 0.5 : 1,
                }}>
                  <td style={{ padding: "3px 8px", whiteSpace: "nowrap" }}>
                    {badge && (
                      <span style={{
                        display: "inline-flex", alignItems: "center", gap: 4,
                        padding: "1px 8px", borderRadius: 10,
                        fontSize: 12, fontWeight: 600, background: badge.bg, color: badge.fg,
                        border: st === "drop" || st === "cutoff" ? "1px solid var(--hairline)" : "none",
                      }}>
                        {badge.Icon && <badge.Icon size={12} />}
                        {badge.label}
                      </span>
                    )}
                  </td>
                  {cols.map((c) => {
                    const dim = stage.projected && !projected.has(c);
                    const empty = row[c] === null || row[c] === undefined;
                    return (
                      <td key={c} style={{
                        padding: "3px 10px", whiteSpace: "nowrap",
                        opacity: dim ? 0.3 : 1,
                        textDecoration: st === "drop" ? "line-through" : "none",
                        fontStyle: empty ? "italic" : "normal",
                        color: empty ? "var(--ink-muted)" : "inherit",
                      }}>
                        {empty ? "— trống —" : fmt(row[c])}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Panel tích luỹ CHỈ ở bước accumulate — không hiện ở bước result
          (result không có accumulator → sẽ hiện "(trống)" gây hiểu nhầm). */}
      {state.config.aggregate && step.kind === "accumulate" && (
        <p className="notes">
          {aggLabel(state.config.aggregate, schema)} — đang cộng dồn:{" "}
          <strong>{fmt((step.detail.accumulator as Cell) ?? null)}</strong>
          {step.detail.count != null && ` (đã tính ${String(step.detail.count)} hàng hợp lệ)`}
        </p>
      )}
      {/* Bước cuối: chỉ MỘT dòng kết quả mạnh; bước khác: tường thuật learner. */}
      {isFinal ? (
        <p className="notes"><strong>
          {state.aggregateResult
            ? `${aggLabel(state.config.aggregate!, schema)} = ${fmt(state.aggregateResult.value)}`
            : `Kết quả: ${state.resultRows.length} hàng.`}
        </strong></p>
      ) : (
        <p className="notes">{narrate(step, schema, state.config.aggregate)}</p>
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
          Sắp xếp: {labelOf(state.config.schema, state.config.sort.column)}{" "}
          {state.config.sort.direction === "desc" ? "giảm dần" : "tăng dần"} (ổn định)
        </p>
      )}
      {/* Kết quả chỉ hiện Ở BƯỚC CUỐI — hé lộ sớm là làm mất phần học sinh cần nghĩ. */}
      {isFinal ? (
        <p className="notes">
          Kết quả: {state.resultRows.length} dòng
          {state.aggregateResult &&
            ` · ${aggLabel(state.config.aggregate!, state.config.schema)} = ${fmt(state.aggregateResult.value)}`}
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
