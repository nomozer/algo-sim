import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";

import { UnsupportedNotice } from "../../../components/SimulationWorkspace";
import {
  runTableQuery,
  TableWorkspace,
  validateTableConfig,
  type TableColumn,
} from "./table-module";

/**
 * M17 W2B-PATCH §C (L3) — MIRROR của
 * `backend/app/validation/table_query.py::_marker_kind`.
 *
 * Tầng 2 phải thi hành ĐÚNG luật của tầng 1, vì đường mở-lại-từ-lịch-sử (bất
 * biến #17) đi thẳng vào engine FE mà không qua backend: một config còn chữ
 * "trống" trong cột số mà FE nhận bừa sẽ cho AVG sai câm.
 *
 * Con số kỳ vọng TRÙNG `backend/tests/test_table_missing_values.py`.
 */

const L3_SCHEMA: TableColumn[] = [
  { name: "hoc_sinh", type: "text", label: "Học sinh" },
  { name: "diem", type: "number", label: "Điểm kiểm tra" },
];
const NAMES = ["An", "Bình", "Chi", "Dũng", "Hà", "Lan"];

function l3Rows(marker: unknown) {
  const diem: unknown[] = ["8", marker, "9.5", "7", marker, "8.5"];
  return NAMES.map((n, i) => ({ hoc_sinh: n, diem: diem[i] }));
}

function build(rows: unknown[], schema: TableColumn[] = L3_SCHEMA, over: Record<string, unknown> = {}) {
  return validateTableConfig({ specVersion: "table-1.0", schema, rows, ...over });
}

describe("marker ô trống ở cột số → null", () => {
  it.each(["", "   ", "trống", "Trống", "—", "N/A", "null"])("%s", (marker) => {
    const v = build(l3Rows(marker));
    if (!v.ok) throw new Error(v.error);
    expect(v.config.rows.map((r) => r.diem)).toEqual([8, null, 9.5, 7, null, 8.5]);
  });

  it("ghi lại bằng chứng từng ô đã chuẩn hoá", () => {
    const v = build(l3Rows("trống"));
    if (!v.ok) throw new Error(v.error);
    expect(v.config.normalizations).toEqual([
      { row: 2, column: "diem", column_type: "number", original: "trống", normalized: null, reason: "missing_value_marker" },
      { row: 5, column: "diem", column_type: "number", original: "trống", normalized: null, reason: "missing_value_marker" },
    ]);
  });
});

describe("KHÔNG được mất dữ liệu hợp lệ", () => {
  it("cột chữ giữ nguyên literal 'trống'", () => {
    const v = build(
      [{ ten: "An", ghi_chu: "trống" }, { ten: "Bình", ghi_chu: "—" }],
      [{ name: "ten", type: "text" }, { name: "ghi_chu", type: "text" }],
    );
    if (!v.ok) throw new Error(v.error);
    expect(v.config.rows[0].ghi_chu).toBe("trống");
    expect(v.config.normalizations).toEqual([]);
  });

  it("0 · '0' · false · 'không' KHÔNG bao giờ là ô trống", () => {
    const v = build(
      [{ diem: 0, dat: false, ghi_chu: "không" }, { diem: "0", dat: "sai", ghi_chu: "0" }],
      [{ name: "diem", type: "number" }, { name: "dat", type: "boolean" }, { name: "ghi_chu", type: "text" }],
    );
    if (!v.ok) throw new Error(v.error);
    expect(v.config.rows.map((r) => r.diem)).toEqual([0, 0]);
    expect(v.config.rows.map((r) => r.dat)).toEqual([false, false]);
    expect(v.config.rows.map((r) => r.ghi_chu)).toEqual(["không", "0"]);
    expect(v.config.normalizations).toEqual([]);
  });
});

describe("fail-closed", () => {
  it.each(["abc", "tám", "8 điểm", "không rõ"])("chữ sai kiểu %s bị từ chối", (bad) => {
    const v = build(l3Rows(bad));
    expect(v.ok).toBe(false);
  });

  it("cột khai nullable:false thì marker là lỗi", () => {
    const v = build(l3Rows("trống"), [
      { name: "hoc_sinh", type: "text" },
      { name: "diem", type: "number", nullable: false },
    ]);
    expect(v.ok).toBe(false);
  });
});

describe("chỉ báo tầng pipeline (W2B-PATCH §E)", () => {
  const L4_SCHEMA: TableColumn[] = [
    { name: "ten", type: "text", label: "Tên" },
    { name: "to", type: "text", label: "Tổ" },
    { name: "diem", type: "number", label: "Điểm" },
  ];
  const L4_ROWS = [
    { ten: "An", to: "A", diem: 9 }, { ten: "Bình", to: "B", diem: 8.5 },
    { ten: "Chi", to: "A", diem: 6 }, { ten: "Dũng", to: "A", diem: 9 },
    { ten: "Lan", to: "A", diem: 7.5 }, { ten: "Minh", to: "A", diem: 6 },
  ];
  const FULL = {
    filter: { op: "=", column: "to", value: "A" },
    projection: ["ten", "diem"],
    sort: { column: "diem", direction: "desc" },
    limit: 3,
    aggregate: { func: "avg", column: "diem" },
  };

  const render = (over: Record<string, unknown>, cursor: number) => {
    const v = build(L4_ROWS, L4_SCHEMA, over);
    if (!v.ok) throw new Error(v.error);
    const state = { config: v.config, ...runTableQuery(v.config), cursor };
    return renderToString(
      <TableWorkspace config={v.config} state={state} busy={false} dispatch={() => {}} />,
    );
  };

  it("hiện ĐỦ năm bước của truy vấn năm tầng", () => {
    const html = render(FULL, 0);
    for (const label of ["Lọc", "Chọn cột", "Sắp xếp", "Lấy", "Tính"]) {
      expect(html).toContain(label);
    }
  });

  it("KHÔNG bịa bước mà truy vấn không có", () => {
    const html = render({ filter: FULL.filter, sort: FULL.sort }, 0);
    expect(html).toContain("Lọc");
    expect(html).toContain("Sắp xếp");
    expect(html).not.toContain("Chọn cột");
    expect(html).not.toContain("Lấy 3 dòng");
    expect(html).not.toContain("Tính trung bình");
  });

  it("truy vấn MỘT bước không dựng chỉ báo quy trình (không có gì để nối)", () => {
    const html = render({ sort: FULL.sort }, 0);
    expect(html).not.toContain("tq-stages");
  });

  it("bước đã đi qua được đánh dấu, bước chưa tới thì chưa", () => {
    const early = render(FULL, 0);
    const v = build(L4_ROWS, L4_SCHEMA, FULL);
    if (!v.ok) throw new Error(v.error);
    const total = runTableQuery(v.config).steps.length;
    const late = render(FULL, total - 1);
    const done = (h: string) => (h.match(/data-stage-done="true"/g) ?? []).length;
    expect(done(early)).toBe(0);
    expect(done(late)).toBe(5);
  });
});

describe("tiêu đề thông báo từ chối phải khớp bản chất (W2B-PATCH §E)", () => {
  /* Lỗi PHÁT HIỆN KHI XEM ẢNH (unit + SSR đều xanh trước đó): spec bỏ sót bước
   * dùng chung `failure_category: "semantic_incomplete"` với ca "đề hỏi hai
   * truy vấn", nên notice gắn tiêu đề "TÁCH THÀNH TỪNG YÊU CẦU" + gợi ý "mỗi
   * lần hỏi một yêu cầu". Với đề MỘT truy vấn nhiều bước thì lời khuyên đó SAI:
   * tách ra cũng không giúp gì, lỗi là hệ chưa dựng đủ bước. */
  const shortfall = {
    reason: "kỹ thuật",
    learner_reason: "Mô phỏng dựng ra chưa trả lời đủ đề: chưa dựng được 2 bước "
      + "(lấy số dòng đầu; tính trung bình một cột).",
    failure_category: "semantic_incomplete",
    error_code: "pipeline_stage_incomplete",
  };

  it("thiếu BƯỚC → không xui học sinh tách yêu cầu", () => {
    const h = renderToString(<UnsupportedNotice unsupported={shortfall} />);
    expect(h).not.toContain("TÁCH THÀNH TỪNG YÊU CẦU");
    expect(h).not.toContain("Mỗi lần hỏi một yêu cầu");
    expect(h).toContain("CHƯA DỰNG ĐỦ CÁC BƯỚC");
  });

  it("hai truy vấn độc lập VẪN giữ lời khuyên tách yêu cầu", () => {
    const h = renderToString(<UnsupportedNotice unsupported={{
      reason: "kỹ thuật", learner_reason: "Đề đang hỏi 2 truy vấn độc lập…",
      failure_category: "semantic_incomplete",
      error_code: "multiple_operations_not_supported",
    }} />);
    expect(h).toContain("TÁCH THÀNH TỪNG YÊU CẦU");
  });

  it("thiếu dữ kiện vẫn là CHƯA ĐỦ DỮ KIỆN", () => {
    const h = renderToString(<UnsupportedNotice unsupported={{
      reason: "kỹ thuật", learner_reason: "Đề chưa cho bảng dữ liệu cụ thể…",
      failure_category: "insufficient_specification",
      error_code: "input_insufficient",
    }} />);
    expect(h).toContain("CHƯA ĐỦ DỮ KIỆN");
  });
});

describe("L3 đầu-cuối", () => {
  it("AVG bỏ qua ô trống: 4 ô, 8.25", () => {
    const v = build(l3Rows("trống"), L3_SCHEMA, {
      aggregate: { func: "avg", column: "diem" },
    });
    if (!v.ok) throw new Error(v.error);
    const out = runTableQuery(v.config);
    expect(out.aggregateResult?.counted).toBe(4);
    expect(out.aggregateResult?.value).toBeCloseTo(8.25, 6);
  });

  it("renderer hiện ô trống là '— trống —', KHÔNG hiện 0", () => {
    const v = build(l3Rows("trống"), L3_SCHEMA, {
      aggregate: { func: "avg", column: "diem" },
    });
    if (!v.ok) throw new Error(v.error);
    const state = { config: v.config, ...runTableQuery(v.config), cursor: 0 };
    const html = renderToString(
      <TableWorkspace config={v.config} state={state} busy={false} dispatch={() => {}} />,
    );
    expect(html).toContain("trống");
    expect(html).not.toMatch(/>\s*0\s*</);
  });
});
