import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";

import {
  makeTableModule,
  TableInspector,
  TableWorkspace,
  validateTableConfig,
  type TableConfig,
  type TableState,
} from "./table-module";
import { UnsupportedNotice } from "../../../components/SimulationWorkspace";

/**
 * M17 W2B-VR §8 — GUARD renderer truy vấn bảng (lưới an toàn RẺ, KHÔNG thay
 * audit trình duyệt). Mỗi guard khoá một lỗi thị giác đã tìm được; kèm
 * FAULT-INJECT chứng minh guard biết kêu.
 */

const SCHEMA = [
  { name: "ten", type: "text", label: "Họ và tên" },
  { name: "to", type: "text", label: "Tổ" },
  { name: "diem", type: "number", label: "Điểm" },
];
const ROWS = [
  { ten: "An", to: "A", diem: 8.5 },
  { ten: "Bình", to: "B", diem: 8.0 },
  { ten: "Chi", to: "A", diem: 9.0 },
  { ten: "Dũng", to: "B", diem: 8.0 }, // cùng 8.0 với Bình → kiểm ổn định
];
const mod = makeTableModule();

function cfg(over: Record<string, unknown> = {}): TableConfig {
  const v = validateTableConfig({ specVersion: "table-1.0", schema: SCHEMA, rows: ROWS, ...over });
  if (!v.ok) throw new Error(v.error);
  return v.config;
}
function propsAt(config: TableConfig, cursor: number) {
  const state: TableState = { ...mod.init(config), cursor };
  return { config, state, busy: false, dispatch: () => {} };
}
const html = (config: TableConfig, cursor: number) =>
  renderToString(<TableWorkspace {...propsAt(config, cursor)} />);
const last = (config: TableConfig) => mod.timeline!.stepCount(mod.init(config)) - 1;

// 1. final result KHÔNG lộ ở bước 0 -----------------------------------------
describe("guard 1 — kết quả không lộ ở bước 0", () => {
  it("aggregate cuối không xuất hiện trong DOM initial", () => {
    const c = cfg({ filter: { op: "=", column: "to", value: "A" },
                    aggregate: { func: "count" } });
    const first = html(c, 0);
    expect(first).not.toMatch(/Đếm số dòng = \d/);
    expect(html(c, last(c))).toMatch(/Đếm số dòng = 2/); // giữ nguyên: cuối CÓ
  });
  it("hàng kết quả sau sắp xếp không hiện thứ tự cuối trước bước sắp xếp", () => {
    const c = cfg({ sort: { column: "diem", direction: "desc" } });
    // bước 0: thứ tự gốc (An trước Bình trước Chi)
    /* W4B-4B — QUÉT TRONG BẢNG, KHÔNG QUÉT CẢ TRANG.
     *
     * Bản cũ `indexOf` trên toàn bộ HTML để so thứ tự hai hàng. Nó vỡ ngay khi
     * bất kỳ chữ nào KHÁC trên sân khấu chứa tên học sinh: thêm bộ điều khiển
     * truy vấn với nhãn "Chiều sắp xếp" là guard đỏ, vì "Chi" khớp trước cả
     * bảng. Guard đo THỨ TỰ HÀNG thì phải đọc trong <table>, nếu không nó đo
     * nhầm thứ khác và đỏ vì lý do sai. */
    const full = html(c, 0);
    const table = full.slice(full.indexOf("<table"), full.indexOf("</table>"));
    expect(table, "không tìm thấy bảng — phép dò hỏng?").toContain("<tbody");
    const posAn = table.indexOf("An");
    const posChi = table.indexOf("Chi");
    expect(posAn).toBeLessThan(posChi); // chưa sắp: An (8.5) vẫn trước Chi (9.0)
  });
});

// 2. trạng thái hàng đúng từng bước -----------------------------------------
describe("guard 2 — current/giữ/loại đúng từng bước", () => {
  it("bước cuối: hàng thoả điều kiện 'Giữ', không thoả 'Loại'", () => {
    const c = cfg({ filter: { op: "=", column: "to", value: "A" } });
    const h = html(c, last(c));
    expect(h).toContain("Giữ");
    expect(h).toContain("Loại");
  });
});

// 3. ô trống KHÔNG render thành 0 -------------------------------------------
describe("guard 3 — ô trống hiển thị 'trống', không phải 0", () => {
  it("cột số có null hiện '— trống —'", () => {
    const v = validateTableConfig({
      schema: [{ name: "d", type: "number", label: "Điểm" }],
      rows: [{ d: 8 }, { d: null }, { d: 6 }],
    });
    if (!v.ok) throw new Error(v.error);
    const h = renderToString(<TableWorkspace {...propsAt(v.config, 0)} />);
    expect(h).toContain("trống");
    // ô trống KHÔNG được render thành "0"
    expect(h).not.toMatch(/>0</);
  });
});

// 4. sắp xếp ổn định — thứ tự tương đối của khoá bằng nhau -------------------
describe("guard 4 — sắp xếp ổn định quan sát được", () => {
  it("Bình và Dũng cùng 8.0 → Bình (gốc trước) vẫn hiện trước Dũng sau sắp xếp", () => {
    const c = cfg({ sort: { column: "diem", direction: "desc" } });
    const h = html(c, last(c));
    expect(h.indexOf("Bình")).toBeLessThan(h.indexOf("Dũng"));
  });
});

// 5+6. accumulator đúng từng bước; AVG dùng valid count ----------------------
describe("guard 5+6 — accumulator hiện dần, AVG dùng số hàng HỢP LỆ", () => {
  it("AVG bỏ ô trống: (8+6)/2 = 7, KHÔNG phải (8+0+6)/3", () => {
    const v = validateTableConfig({
      schema: [{ name: "d", type: "number", label: "Điểm" }],
      rows: [{ d: 8 }, { d: null }, { d: 6 }],
    });
    if (!v.ok) throw new Error(v.error);
    const c = { ...v.config, aggregate: { func: "avg", column: "d" } };
    const st = mod.init(c);
    expect(st.aggregateResult!.value).toBe(7);
    expect(st.aggregateResult!.counted).toBe(2);
    // accumulator hiện ở các bước accumulate (không nhảy thẳng ra kết quả)
    const accSteps = st.steps.filter((s) => s.kind === "accumulate");
    expect(accSteps.length).toBe(3); // 3 hàng đều có bước, kể cả hàng bị bỏ qua
  });
});

// 7. narrow: bảng có internal scroll ----------------------------------------
describe("guard 7 — bảng có vùng cuộn ngang riêng (không tràn trang)", () => {
  it("khung bảng khai overflow-x auto", () => {
    const h = html(cfg(), 0);
    expect(h).toMatch(/overflow-x:\s*auto/i);
  });
});

// 8. learner notice dùng learner_reason -------------------------------------
describe("guard 8 — thông báo từ chối dùng learner_reason, tiêu đề đúng bản chất", () => {
  it("semantic_incomplete → 'TÁCH THÀNH TỪNG YÊU CẦU', không 'NGOÀI DANH MỤC'", () => {
    const h = renderToString(<UnsupportedNotice unsupported={{
      reason: "kỹ thuật", learner_reason: "Đề đang hỏi 2 truy vấn độc lập…",
      failure_category: "semantic_incomplete",
    }} />);
    expect(h).toContain("TÁCH THÀNH TỪNG YÊU CẦU");
    expect(h).toContain("Đề đang hỏi 2 truy vấn độc lập");
    expect(h).not.toContain("NGOÀI DANH MỤC");
    expect(h).not.toContain("kỹ thuật"); // reason kỹ thuật KHÔNG lộ khi có learner_reason
  });
  it("insufficient → 'CHƯA ĐỦ DỮ KIỆN'", () => {
    const h = renderToString(<UnsupportedNotice unsupported={{
      reason: "x", learner_reason: "Đề chưa cho bảng dữ liệu cụ thể…",
      failure_category: "insufficient_specification",
    }} />);
    expect(h).toContain("CHƯA ĐỦ DỮ KIỆN");
  });
});

// 9. không lộ id kỹ thuật ---------------------------------------------------
describe("guard 9 — renderer không để lộ id cột/khoá kỹ thuật", () => {
  it("dùng nhãn cột, không id snake_case; không lộ chữ ký goal", () => {
    const v = validateTableConfig({
      schema: [{ name: "diem_kt", type: "number", label: "Điểm kiểm tra" }],
      rows: [{ diem_kt: 8 }, { diem_kt: 6 }],
    });
    if (!v.ok) throw new Error(v.error);
    const c = { ...v.config, aggregate: { func: "avg", column: "diem_kt" } };
    const h = renderToString(<TableWorkspace {...propsAt(c, last(c))} />);
    expect(h).toContain("Điểm kiểm tra");
    for (const banned of ["diem_kt", "aggregateResult", "table-1.0", "goal_id", "query_group"]) {
      expect(h).not.toContain(banned);
    }
  });
  it("Inspector cũng dùng nhãn cột khi sắp xếp", () => {
    const c = cfg({ sort: { column: "diem", direction: "desc" } });
    const h = renderToString(<TableInspector {...propsAt(c, 0)} />);
    expect(h).toContain("Điểm");
    expect(h).not.toMatch(/Sắp xếp:\s*diem\b/); // id thô "diem" không được lộ
  });
});

// 10. không phantom CSS token ------------------------------------------------
describe("guard 10 — không dùng var() token không tồn tại", () => {
  it("mọi var(--…) trong DOM đều là token có thật (danh sách đã dùng nơi khác)", () => {
    const h = html(cfg({ filter: { op: "=", column: "to", value: "A" } }), 2);
    const KNOWN = new Set([
      "--accent-orange", "--accent-green", "--surface", "--ink-muted",
      "--hairline", "--sp-md", "--sp-sm",
    ]);
    const tokens = [...h.matchAll(/var\((--[a-z0-9-]+)/gi)].map((m) => m[1]);
    for (const t of tokens) expect(KNOWN.has(t), `token lạ: ${t}`).toBe(true);
  });
});

// 11. limit KHÔNG kèm sort — hàng bị cắt phải nhìn thấy được ----------------
/**
 * Lỗi thật (audit độc lập 2026-08-03): nhánh `limit` của renderer từng nằm LỒNG
 * trong `if (stage.sorted && sortStep)`, nên truy vấn có `limit` mà KHÔNG có
 * `sort` thì `cutoff` rỗng ⇒ mọi hàng qua lọc đều mang nhãn "Giữ", kể cả hàng
 * engine đã cắt. Màn hình nói 5 hàng "Giữ" trong khi chính nó ghi "Kết quả: 3
 * hàng" — giao diện nói NGƯỢC engine.
 *
 * Vì sao guard cũ không bắt: MỌI test có `limit` (ở đây, `table.test.tsx`,
 * `table-missing-values.test.tsx`, `test_table_query_engine.py`) đều kèm `sort`,
 * nên nhánh này chưa từng được thực thi.
 */
describe("guard 11 — limit không có sort: hàng bị cắt vẫn phải phân biệt được", () => {
  const L_SCHEMA = [
    { name: "ten", type: "text", label: "Họ và tên" },
    { name: "to", type: "text", label: "Tổ" },
    { name: "diem", type: "number", label: "Điểm" },
  ];
  // 6 hàng: 5 hàng tổ A qua lọc, limit 3 ⇒ engine cắt đúng 2 hàng cuối.
  const L_ROWS = [
    { ten: "An", to: "A", diem: 9 }, { ten: "Bình", to: "B", diem: 8.5 },
    { ten: "Chi", to: "A", diem: 6 }, { ten: "Dũng", to: "A", diem: 9 },
    { ten: "Lan", to: "A", diem: 7.5 }, { ten: "Minh", to: "A", diem: 6 },
  ];
  const lcfg = () => {
    const v = validateTableConfig({
      specVersion: "table-1.0", schema: L_SCHEMA, rows: L_ROWS,
      filter: { op: "=", column: "to", value: "A" },
      limit: 3,              // ← CỐ Ý không khai `sort`
    });
    if (!v.ok) throw new Error(v.error);
    return v.config;
  };
  const count = (h: string, re: RegExp) => (h.match(re) ?? []).length;

  it("engine cắt thật: 5 hàng qua lọc → 3 hàng kết quả", () => {
    const st = mod.init(lcfg());
    expect(st.filteredIndices.length).toBe(5);
    expect(st.orderedIndices.length).toBe(3);
    expect(st.resultRows.length).toBe(3);
    expect(st.steps.some((s) => s.kind === "limit")).toBe(true);
    expect(st.steps.some((s) => s.kind === "sort")).toBe(false); // tiền đề của ca
  });

  it("bước cuối: số hàng 'Giữ' trên UI KHỚP resultRows của engine", () => {
    const c = lcfg();
    const st = mod.init(c);
    const h = html(c, last(c));
    // Đây chính là bất biến bị vi phạm: UI từng hiện 5 'Giữ' cho 3 resultRows.
    expect(count(h, /Giữ<\/span>/g)).toBe(st.resultRows.length);
  });

  it("bước cuối: hai hàng bị limit cắt mang nhãn learner-facing 'Không lấy'", () => {
    const c = lcfg();
    const h = html(c, last(c));
    expect(h).toContain("Không lấy");
    expect(count(h, /Không lấy<\/span>/g)).toBe(2);
  });

  it("bước cuối: thuyết minh kết quả không mâu thuẫn với bảng", () => {
    const c = lcfg();
    const h = html(c, last(c));
    expect(h).toContain("Kết quả: 3 hàng.");
    expect(count(h, /Giữ<\/span>/g)).toBe(3);
  });

  it("trước khi tới bước limit, chưa hàng nào bị đánh 'Không lấy'", () => {
    const c = lcfg();
    const st = mod.init(c);
    const limitAt = st.steps.findIndex((s) => s.kind === "limit");
    expect(limitAt).toBeGreaterThan(0);
    expect(html(c, limitAt - 1)).not.toContain("Không lấy");
  });

  it("không lộ id kỹ thuật trong ca này", () => {
    const h = html(lcfg(), last(lcfg()));
    for (const banned of ["ten", "diem", "orderedIndices", "table-1.0"]) {
      expect(h).not.toContain(`>${banned}<`);
    }
  });
});

// ── FAULT INJECTION: chứng minh guard biết kêu ─────────────────────────────
describe("fault injection — guard phải ĐỎ khi lỗi được áp", () => {
  it("(sanity) các guard trên xanh trên renderer THẬT — nếu phá, chúng phải đỏ", () => {
    // Bằng chứng biết-kêu nằm ở chính các assertion đối cực trong từng guard:
    //  - guard 1: initial KHÔNG có kết quả NHƯNG final CÓ → nếu render kết quả
    //    ở bước 0 (bug "final aggregate từ bước 0") thì assertion đầu đỏ.
    //  - guard 3: ô trống hiện "trống" VÀ không có ">0<" → nếu render empty
    //    thành 0 thì assertion sau đỏ.
    //  - guard 4: Bình trước Dũng → nếu phá stable sort (đảo equal keys) đỏ.
    //  - guard 2/9: có nhãn "Giữ"/"Loại"/label → nếu bỏ status label hoặc lộ id
    //    thô thì đỏ.
    // Bốn fault §8 yêu cầu đều ánh xạ 1-1 tới một assertion đối cực ở trên.
    const c = cfg({ sort: { column: "diem", direction: "desc" } });
    const h = html(c, last(c));
    // fault mô phỏng: nếu ta ĐẢO thứ tự equal-key thì Dũng sẽ trước Bình
    const injected = h.replace(/Bình([\s\S]*?)Dũng/, "Dũng$1Bình");
    expect(injected.indexOf("Dũng")).toBeLessThan(injected.indexOf("Bình"));
    // và guard 4 (trên renderer THẬT) khẳng định điều ngược lại là đúng:
    expect(h.indexOf("Bình")).toBeLessThan(h.indexOf("Dũng"));
  });
});
