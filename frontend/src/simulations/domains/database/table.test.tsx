import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";

import {
  makeTableModule,
  runTableQuery,
  TableWorkspace,
  validateTableConfig,
  type TableConfig,
} from "./table-module";

/**
 * M17 W2B — engine FE đối chiếu ORACLE ĐỘC LẬP (viết tay trong test, không gọi
 * lại engine) + validator mirror fail-closed.
 *
 * Các con số kỳ vọng ở đây TRÙNG với `backend/tests/test_table_query_engine.py`
 * trên cùng bộ dữ liệu — đó là cách khoá parity BE↔FE mà không cần chạy Python
 * trong vitest.
 */

const SCHEMA = [
  { name: "ten", type: "text" },
  { name: "diem", type: "number" },
  { name: "to", type: "text" },
];
const ROWS = [
  { ten: "An", diem: 8.5, to: "A" },
  { ten: "Bình", diem: 6.0, to: "B" },
  { ten: "Chi", diem: 9.0, to: "A" },
  { ten: "Dũng", diem: 6.0, to: "C" },
  { ten: "Hà", diem: 7.25, to: "B" },
];

function cfg(over: Record<string, unknown> = {}): TableConfig {
  const v = validateTableConfig({ specVersion: "table-1.0", schema: SCHEMA, rows: ROWS, ...over });
  if (!v.ok) throw new Error(v.error);
  return v.config;
}

describe("dấu vết 9 giai đoạn", () => {
  it("đủ giai đoạn, đúng thứ tự, mỗi dòng đọc một lần", () => {
    const res = runTableQuery(cfg({
      filter: { op: ">", column: "diem", value: 6.5 },
      projection: ["ten", "diem"],
      sort: { column: "diem", direction: "desc" },
      limit: 2,
      aggregate: { func: "avg", column: "diem" },
    }));
    const k = res.steps.map((s) => s.kind);
    const order = ["read_row", "evaluate", "filtered_set", "projection", "sort",
                   "limit", "accumulate", "result"];
    const pos = order.map((x) => k.indexOf(x));
    expect(pos).toEqual([...pos].sort((a, b) => a - b));
    expect(k.filter((x) => x === "read_row").length).toBe(ROWS.length);
    expect(k[k.length - 1]).toBe("result");
  });

  it("bước đầu KHÔNG lộ kết quả cuối", () => {
    const res = runTableQuery(cfg({ aggregate: { func: "count" } }));
    expect(res.steps[0].kind).toBe("read_row");
    expect(res.steps[0].detail.aggregateResult).toBeUndefined();
    expect(res.steps[0].detail.rows).toBeUndefined();
  });
});

describe("lọc khớp oracle độc lập", () => {
  const cases: [Record<string, unknown>, (r: (typeof ROWS)[number]) => boolean][] = [
    [{ op: ">", column: "diem", value: 6.5 }, (r) => r.diem > 6.5],
    [{ op: "=", column: "to", value: "A" }, (r) => r.to === "A"],
    [{ op: "contains", column: "ten", value: "n" }, (r) => r.ten.toLowerCase().includes("n")],
    [{ op: "and", clauses: [
        { op: ">=", column: "diem", value: 7 }, { op: "=", column: "to", value: "A" }] },
      (r) => r.diem >= 7 && r.to === "A"],
    [{ op: "or", clauses: [
        { op: "<", column: "diem", value: 6.5 }, { op: "=", column: "to", value: "B" }] },
      (r) => r.diem < 6.5 || r.to === "B"],
  ];
  it.each(cases)("vị từ %#", (pred, oracle) => {
    const res = runTableQuery(cfg({ filter: pred }));
    expect(res.filteredIndices).toEqual(
      ROWS.map((r, i) => (oracle(r) ? i : -1)).filter((i) => i >= 0),
    );
  });
});

describe("sắp xếp ổn định", () => {
  it("hai dòng bằng nhau giữ nguyên thứ tự gốc (tăng dần)", () => {
    const res = runTableQuery(cfg({ sort: { column: "diem", direction: "asc" } }));
    // Bình (idx 1) và Dũng (idx 3) cùng 6.0
    expect(res.orderedIndices.indexOf(1)).toBeLessThan(res.orderedIndices.indexOf(3));
    expect(res.orderedIndices).toEqual([...ROWS.keys()].sort((a, b) => ROWS[a].diem - ROWS[b].diem));
  });

  it("giảm dần vẫn ổn định", () => {
    const res = runTableQuery(cfg({ sort: { column: "diem", direction: "desc" } }));
    expect(res.orderedIndices.indexOf(1)).toBeLessThan(res.orderedIndices.indexOf(3));
  });
});

describe("tổng hợp khớp oracle — cùng số với backend", () => {
  it("count/sum/min/max", () => {
    expect(runTableQuery(cfg({ aggregate: { func: "count" } })).aggregateResult!.value).toBe(5);
    expect(runTableQuery(cfg({ aggregate: { func: "sum", column: "diem" } })).aggregateResult!.value)
      .toBeCloseTo(36.75, 4);
    expect(runTableQuery(cfg({ aggregate: { func: "min", column: "diem" } })).aggregateResult!.value).toBe(6);
    expect(runTableQuery(cfg({ aggregate: { func: "max", column: "diem" } })).aggregateResult!.value).toBe(9);
  });

  it("avg sau lọc + tích luỹ TỪNG bước", () => {
    const res = runTableQuery(cfg({
      filter: { op: ">", column: "diem", value: 6.5 },
      aggregate: { func: "avg", column: "diem" },
    }));
    const kept = ROWS.filter((r) => r.diem > 6.5);
    expect(res.aggregateResult!.value as number).toBeCloseTo(
      kept.reduce((a, r) => a + r.diem, 0) / kept.length, 4);
    expect(res.steps.filter((s) => s.kind === "accumulate").length).toBe(kept.length);
  });

  it("ô trống KHÔNG bị coi là 0", () => {
    const v = validateTableConfig({
      schema: [{ name: "d", type: "number" }],
      rows: [{ d: 10 }, { d: null }, { d: 20 }],
    });
    if (!v.ok) throw new Error(v.error);
    const res = runTableQuery({ ...v.config, aggregate: { func: "avg", column: "d" } });
    expect(res.aggregateResult!.value).toBe(15);   // KHÔNG phải 10
    expect(res.aggregateResult!.counted).toBe(2);
  });
});

describe("validator mirror fail-closed", () => {
  const bad: [Record<string, unknown>, string][] = [
    [{ rows: [] }, "chưa có dòng"],
    [{ schema: [] }, "Thiếu lược đồ"],
    [{ filter: { op: ">", column: "ten", value: 5 } }, "không dùng được"],
    [{ filter: { op: "like", column: "ten", value: "A" } }, "không hỗ trợ"],
    [{ projection: ["khong_co"] }, "Cột lạ"],
    [{ limit: 0 }, "≥1"],
    [{ limit: 999 }, "lớn hơn số dòng"],
    [{ aggregate: { func: "sum", column: "ten" } }, "kiểu số"],
    [{ aggregate: { func: "median", column: "diem" } }, "lạ"],
  ];
  it.each(bad)("từ chối %#", (over, fragment) => {
    const v = validateTableConfig({ schema: SCHEMA, rows: ROWS, ...over });
    expect(v.ok).toBe(false);
    if (!v.ok) expect(v.error).toContain(fragment);
  });
});

describe("renderer", () => {
  const mod = makeTableModule();
  const props = (over: Record<string, unknown>, cursor: number) => {
    const config = cfg(over);
    const state = { ...mod.init(config), cursor };
    return { config, state, busy: false, dispatch: () => {} };
  };

  it("hiện bảng nguồn với mọi dòng ngay từ bước 0", () => {
    const html = renderToString(<TableWorkspace {...props({}, 0)} />);
    for (const r of ROWS) expect(html).toContain(r.ten);
  });

  it("KHÔNG lộ kết quả tổng hợp ở bước 0, có ở bước cuối", () => {
    const over = { aggregate: { func: "count" } };
    const total = mod.timeline!.stepCount(mod.init(cfg(over)));
    const first = renderToString(<TableWorkspace {...props(over, 0)} />);
    const last = renderToString(<TableWorkspace {...props(over, total - 1)} />);
    expect(first).not.toContain("Đếm số dòng = 5");
    expect(last).toContain("Đếm số dòng = 5");
  });
});
