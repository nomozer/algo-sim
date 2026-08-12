import { describe, expect, it } from "vitest";
import {
  COMPARE_OPS,
  PROJECTION_PREFIX,
  makeTableModule,
  runTableQuery,
  withQueryParam,
  type TableConfig,
  type TableState,
} from "./table-module";

/**
 * W4B-4B — TRUY VẤN LÀ THỨ HỌC SINH ĐỔI, KHÔNG PHẢI THỨ HỌC SINH XEM.
 *
 * ─── LỖI ĐÃ ĐO ĐƯỢC ───────────────────────────────────────────────────────
 *
 * Module khai `apply: (state) => state` — identity. Bài "lọc học sinh điểm ≥ 8
 * rồi sắp theo điểm" vì thế chỉ còn MỘT việc để làm: bấm Play và xem bốn bước
 * chạy. Nhưng cơ chế của bài không phải trình tự thời gian, nó là QUAN HỆ giữa
 * câu truy vấn và tập kết quả — và quan hệ đó chỉ hiện ra khi ĐỔI được câu hỏi.
 *
 * Bài kiểm này khoá đúng vòng lặp đó, và khoá cả ranh giới: miền ĐÓNG,
 * fail-closed, engine là bên tính, renderer không được tự lọc/sắp/chiếu.
 */

const CFG = {
  specVersion: "table-1.0",
  schema: [
    { name: "ten", type: "text", label: "Họ tên" },
    { name: "diem", type: "number", label: "Điểm" },
  ],
  rows: [
    { ten: "An", diem: 8.5 },
    { ten: "Bình", diem: 6 },
    { ten: "Chi", diem: 9 },
  ],
  filter: { op: ">=", column: "diem", value: 8 },
  projection: null,
  sort: { column: "diem", direction: "desc" },
  limit: null,
  aggregate: null,
  normalizations: [],
} as unknown as TableConfig;

const mod = makeTableModule();
const init = (): TableState => mod.init(CFG) as TableState;
const names = (s: TableState) => s.resultRows.map((r) => String(r.ten));

describe("W4B-4B · đổi truy vấn ⇒ engine tính lại, KHÔNG cần Play", () => {
  it("đổi ngưỡng lọc thì tập kết quả đổi ngay", () => {
    const s0 = init();
    expect(names(s0)).toEqual(["Chi", "An"]); // >= 8, giảm dần

    const s1 = mod.apply(s0, { type: "set_param", name: "filter.value", value: "9" }) as TableState;
    expect(s1).not.toBe(s0);
    expect(names(s1), "đổi ngưỡng mà kết quả không đổi").toEqual(["Chi"]);

    const s2 = mod.apply(s1, { type: "set_param", name: "filter.value", value: "6" }) as TableState;
    expect(names(s2)).toEqual(["Chi", "An", "Bình"]);
  });

  it("đổi chiều sắp xếp thì thứ tự dòng đổi ngay", () => {
    const s = mod.apply(init(), { type: "set_param", name: "sort.direction", value: "asc" }) as TableState;
    expect(names(s)).toEqual(["An", "Chi"]);
  });

  it("bật/tắt cột thì phép chiếu đổi ngay, và không bao giờ còn 0 cột", () => {
    const s0 = init();
    expect(s0.projectedColumns).toEqual(["ten", "diem"]);
    const s1 = mod.apply(s0, { type: "set_param", name: `${PROJECTION_PREFIX}ten`, value: true }) as TableState;
    expect(s1.projectedColumns).toEqual(["diem"]);
    // Tắt nốt cột cuối ⇒ fail-closed: bảng 0 cột không còn nghĩa gì.
    const s2 = mod.apply(s1, { type: "set_param", name: `${PROJECTION_PREFIX}diem`, value: true }) as TableState;
    expect(s2, "chiếu về 0 cột lọt qua").toBe(s1);
  });

  it("bỏ sắp xếp được, và đặt lại được", () => {
    const off = mod.apply(init(), { type: "set_param", name: "sort.column", value: "" }) as TableState;
    expect(off.config.sort).toBeNull();
    const on = mod.apply(off, { type: "set_param", name: "sort.column", value: "diem" }) as TableState;
    expect(on.config.sort).toEqual({ column: "diem", direction: "asc" });
  });

  it("đổi cột lọc thì giá trị được ép lại theo KIỂU CỘT MỚI", () => {
    /* Nếu không ép lại, so một chuỗi với cột số sẽ cho kết quả vô nghĩa mà
       không ai báo lỗi — đúng loại sai câm mà bất biến #20 sinh ra để chặn. */
    const s = withQueryParam(CFG, "filter.column", "ten")!;
    expect(s.filter!.column).toBe("ten");
    expect(typeof s.filter!.value === "string" || s.filter!.value === null).toBe(true);
  });
});

describe("W4B-4B · miền ĐÓNG — fail-closed, không SQL tự do", () => {
  it("tên tham số lạ ⇒ null, state giữ nguyên", () => {
    expect(withQueryParam(CFG, "rows", 5 as never)).toBeNull();
    expect(withQueryParam(CFG, "filter.expression", "1=1")).toBeNull();
    const s0 = init();
    expect(mod.apply(s0, { type: "set_param", name: "filter.expression", value: "1=1" })).toBe(s0);
  });

  it("cột ngoài lược đồ ⇒ null", () => {
    expect(withQueryParam(CFG, "filter.column", "luong")).toBeNull();
    expect(withQueryParam(CFG, "sort.column", "luong")).toBeNull();
    expect(withQueryParam(CFG, `${PROJECTION_PREFIX}luong`, true)).toBeNull();
  });

  it("toán tử ngoài bảng ⇒ null; mọi toán tử TRONG bảng đều nhận", () => {
    expect(withQueryParam(CFG, "filter.op", "LIKE")).toBeNull();
    expect(withQueryParam(CFG, "filter.op", "; DROP TABLE")).toBeNull();
    for (const op of COMPARE_OPS) {
      expect(withQueryParam(CFG, "filter.op", op), `toán tử hợp lệ bị chặn: ${op}`).not.toBeNull();
    }
  });

  it("giá trị không ép được về kiểu cột ⇒ null (không hoá 0 im lặng)", () => {
    expect(withQueryParam(CFG, "filter.value", "tám phẩy năm")).toBeNull();
  });

  it("chiều sắp xếp ngoài {asc,desc} ⇒ null", () => {
    expect(withQueryParam(CFG, "sort.direction", "random")).toBeNull();
  });
});

describe("W4B-4B · ENGINE là bên tính, renderer chỉ đọc", () => {
  it("state sau `apply` KHỚP y hệt `runTableQuery` của config mới", () => {
    /* Đây là bất biến trung tâm: nếu một ngày `apply` tự lọc/sắp lấy thì hai vế
       này lệch nhau, và sản phẩm có hai nguồn sự thật. */
    const s = mod.apply(init(), { type: "set_param", name: "filter.value", value: "6" }) as TableState;
    const expected = runTableQuery(s.config);
    expect(s.resultRows).toEqual(expected.resultRows);
    expect(s.filteredIndices).toEqual(expected.filteredIndices);
    expect(s.orderedIndices).toEqual(expected.orderedIndices);
    expect(s.projectedColumns).toEqual(expected.projectedColumns);
  });

  it("renderer KHÔNG tự lọc/sắp/chiếu — nguồn không chứa đường tắt", () => {
    /* Quét nguồn: renderer được phép ĐỌC `resultRows`/`orderedIndices`, nhưng
       không được tự gọi sort/filter trên dữ liệu thô. */
    const src = readSource();
    const body = src.slice(src.indexOf("export function TableWorkspace"));
    expect(body, "renderer tự sắp xếp").not.toMatch(/\brows\s*\.\s*sort\s*\(/);
    expect(body, "renderer tự lọc").not.toMatch(/config\.rows\s*\.\s*filter\s*\(/);
  });

  it("đổi truy vấn thì trace kể lại CHÍNH câu vừa đặt, và con trỏ về đầu", () => {
    const s = mod.apply(init(), { type: "set_param", name: "filter.value", value: "6" }) as TableState;
    expect(s.cursor, "đứng lại ở bước của câu hỏi cũ").toBe(0);
    expect(s.steps.length).toBeGreaterThan(1);
    expect(runTableQuery(s.config).steps.length).toBe(s.steps.length);
  });
});

function readSource(): string {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { readFileSync } = require("node:fs") as typeof import("node:fs");
  return readFileSync(new URL("./table-module.tsx", import.meta.url), "utf-8");
}
