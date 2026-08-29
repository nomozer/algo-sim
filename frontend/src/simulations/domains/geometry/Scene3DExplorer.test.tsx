/**
 * KHỐI THĂM DÒ — cây, ô soi, chọn hai chiều. **0 mạng, 0 LLM, 0 WebGL.**
 *
 * ─── VÌ SAO KHÔNG DÙNG `fireEvent` ──────────────────────────────────────
 *
 * Kho này **không có** `@testing-library/react`, không có jsdom: mọi test
 * component đi qua `renderToString`. §11 của chỉ thị nói thẳng — đừng cài cả
 * một bộ hạ tầng test chỉ để tick vài ca. Nên phần "quyết định" được TÁCH RA
 * thành hàm thuần (`semanticTree`, `entitiesPresentAt`, `select`, `isolate`,
 * `visualTransformOf`) và kiểm thẳng ở đó, còn ở đây kiểm CẤU TRÚC đã dựng
 * ra và các ràng buộc đọc được từ mã nguồn.
 *
 * Phần duy nhất không kiểm tự động được: bấm chuột thật vào một mặt trong
 * khung 3D (cần WebGL + raycast). Nó khai là MANUAL_UI_DEMO, không tính là
 * test tự động.
 */
import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Scene3D } from "./scene3d-model";
import { objectsAt } from "./scene3d-model";
import { Scene3DExplorer } from "./Scene3DExplorer";
import {
  entitiesPresentAt,
  faceId,
  withSubEntities,
} from "./scene3d-subentities";
import {
  hide,
  isolate,
  reset,
  select,
  semanticTree,
  taoTrangThai,
} from "./interaction-state";

const CANH: Scene3D = {
  objects: [
    { id: "A", label: "A", type: "point3", render: "point_marker", origin: "free",
      producer: null, depends: [], xyz: ["0", "0", "0"], parent: "chop",
      display_group: ["given"], source: { assumption: "chọn A làm gốc" } },
    { id: "B", label: "B", type: "point3", render: "point_marker", origin: "free",
      producer: null, depends: [], xyz: ["1", "0", "0"], parent: "chop",
      display_group: ["given"], source: { fact_id: "ab_length" } },
    { id: "C", label: "C", type: "point3", render: "point_marker", origin: "free",
      producer: null, depends: [], xyz: ["0", "1", "0"], parent: "chop",
      display_group: ["given"], source: {} },
    { id: "S", label: "S", type: "point3", render: "point_marker", origin: "free",
      producer: null, depends: [], xyz: ["0", "0", "1"], parent: "chop",
      display_group: ["given"], source: {} },
    { id: "chop", label: "S.ABC", type: "solid", render: "mesh", origin: "derived",
      producer: "construct_solid", depends: ["A", "B", "C", "S"],
      vertices: [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
      vertex_ids: ["A", "B", "C", "S"],
      faces: [[0, 1, 2], [0, 1, 3], [1, 2, 3], [0, 2, 3]],
      parent: null, display_group: ["solid"], source: {} },
    { id: "V", label: "V", type: "quantity", render: "readout", origin: "derived",
      producer: "measure.volume", depends: ["chop"], value: "1/6",
      parent: null, display_group: ["measurement"], source: {} },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Đặt hệ trục." },
    { step_index: 1, action: "CREATE", object: "chop", depends: ["A", "B", "C", "S"], explanation: "Dựng khối." },
    { step_index: 2, action: "MEASURE", object: "V", depends: ["chop"], explanation: "Đo thể tích." },
  ],
  free_objects: ["A", "B", "C", "S"],
};

const html = () => renderToString(<Scene3DExplorer scene={CANH} />);
const day = () => withSubEntities(CANH);

// ══ CÂY PHÂN RÃ — dựng thật, không phải mô hình ═══════════════════════
describe("cây phân rã hiện đủ khối → mặt → cạnh → điểm", () => {
  it("hiện hạng mục Điểm, Cạnh, Mặt", () => {
    const h = html();
    for (const t of ["Điểm", "Cạnh", "Mặt", "Các thành phần của hình"]) {
      expect(h).toContain(t);
    }
  });

  it("bốn mặt và sáu cạnh đều là nút BẤM ĐƯỢC riêng", () => {
    const h = html();
    for (const nhan of ["ABC", "ABS", "BCS", "ACS"]) expect(h).toContain(nhan);
    // Mỗi mặt/cạnh là một `<button>` riêng, không phải một dòng chữ.
    const soNut = (h.match(/geo3d-tree-item/g) ?? []).length;
    // 4 điểm + 1 khối + 1 đại lượng + 4 mặt + 6 cạnh = 16
    expect(soNut).toBe(16);
  });

  it("KHÔNG dựng hạng mục rỗng", () => {
    expect(html()).not.toContain("Thiết diện");
  });

  it("cây và cảnh dày khớp nhau: mọi thực thể có đúng một nút", () => {
    const ids = day().objects.map((o) => o.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});

// ══ MỘT THẨM QUYỀN CHỌN ══════════════════════════════════════════════
describe("một thẩm quyền chọn", () => {
  it("component KHÔNG giữ selection thứ hai", () => {
    const src = readFileSync(join(__dirname, "Scene3DExplorer.tsx"), "utf8");
    // Đúng MỘT `useState`, và nó giữ `InteractionState`. Thêm
    // `treeSelected`/`viewportSelected` là mời hai bản lệch nhau.
    // Đếm LỜI GỌI, không đếm chữ: dòng `import` cũng chứa `useState`.
    expect((src.match(/useState[<(]/g) ?? []).length).toBe(1);
    expect(src).toContain("useState<InteractionState>");
    // BỎ CHÚ THÍCH trước khi soi tên cấm — docstring của chính file ấy NHẮC
    // `treeSelected`/`viewportSelected` để nói *đừng làm thế*, và một phép so
    // chuỗi thô sẽ bắt đúng lời cảnh báo. Kho này đã vấp lớp lỗi ấy một lần
    // với chữ `three` trong văn xuôi.
    const ma = src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
    for (const cam of ["treeSelected", "viewportSelected", "setSelected"]) {
      expect(ma, `giữ selection thứ hai: ${cam}`).not.toContain(cam);
    }
    // Phép bỏ chú thích phải THẬT SỰ bỏ được — nếu không, test trên xanh vì
    // một lý do sai.
    expect(ma).not.toContain("mời hai bản lệch nhau");
  });

  it("cả cây lẫn khung nhìn đều báo về CÙNG một hàm `chon`", () => {
    const src = readFileSync(join(__dirname, "Scene3DExplorer.tsx"), "utf8");
    expect(src).toContain("onSelect={chon}");
    expect(src).toContain("onChon={chon}");
  });

  it("chọn là phép THUẦN — đổi id thì id cũ thôi được chọn", () => {
    const a = select(taoTrangThai(), "A");
    const b = select(a, faceId("chop", 1));
    expect(a.selected_id).toBe("A");
    expect(b.selected_id).toBe("chop::face:1");
  });
});

// ══ PHÁT LẠI — mặt có mặt cùng lúc với khối cha ══════════════════════
describe("bước dựng quyết định cái gì bấm được", () => {
  it("bước 0: khối và mặt của nó CHƯA có", () => {
    const co = entitiesPresentAt(day(), 0, objectsAt);
    expect(co.has("A")).toBe(true);
    expect(co.has("chop")).toBe(false);
    expect(co.has(faceId("chop", 0))).toBe(false);
  });

  it("bước 1: khối và MỌI mặt/cạnh của nó cùng có", () => {
    const co = entitiesPresentAt(day(), 1, objectsAt);
    expect(co.has("chop")).toBe(true);
    for (let i = 0; i < 4; i++) expect(co.has(faceId("chop", i))).toBe(true);
  });

  it("KHÔNG có timeline thứ hai: mặt không tự sinh sự kiện", () => {
    const ev = day().events;
    expect(ev).toHaveLength(CANH.events.length);
    expect(ev.some((e) => e.object?.includes("::"))).toBe(false);
  });
});

// ══ Ô SOI — đủ trả lời "vật này ở đâu ra" ════════════════════════════
describe("ô soi", () => {
  it("mặt biết cha và các đỉnh của nó", () => {
    const m = day().objects.find((o) => o.id === faceId("chop", 1))!;
    expect(m.parent).toBe("chop");
    expect(m.depends).toEqual(["A", "B", "S"]);
    expect(m.producer).toContain("face[1]");
  });

  it("điểm giữ được dữ kiện và giả thiết của đề", () => {
    const b = day().objects.find((o) => o.id === "B")!;
    expect(b.source!.fact_id).toBe("ab_length");
    const a = day().objects.find((o) => o.id === "A")!;
    expect(a.source!.assumption).toContain("gốc");
  });

  it("bề mặt học sinh KHÔNG lộ định danh kỹ thuật của hệ", () => {
    const h = html();
    for (const cam of ["simulation_id", "source_fact_id", "display_group",
                       "InteractionState", "visual_transform"]) {
      expect(h, `UI lộ ${cam}`).not.toContain(cam);
    }
  });
});

// ══ THAO TÁC XEM KHÔNG ĐỔI DỮ LIỆU ═══════════════════════════════════
describe("thao tác xem là phép thuần trên trạng thái nhìn", () => {
  it("cô lập rồi về mặc định ⇒ đúng trạng thái đầu", () => {
    let s = select(taoTrangThai(), faceId("chop", 1));
    s = isolate(s, [faceId("chop", 1), "A", "B", "S"]);
    s = hide(s, "C");
    expect(reset()).toEqual(taoTrangThai());
  });

  it("dựng cây hai lần cho cùng kết quả (tất định)", () => {
    expect(semanticTree(day())).toEqual(semanticTree(day()));
  });

  it("render KHÔNG chạm cảnh gốc", () => {
    const truoc = JSON.parse(JSON.stringify(CANH)) as Scene3D;
    html();
    expect(CANH).toEqual(truoc);
  });
});

// ══ KHÔNG GỌI MẠNG / LLM ═════════════════════════════════════════════
describe("tương tác không gọi gì ra ngoài", () => {
  it("không `fetch`, không `axios`, không client nào", () => {
    for (const f of ["Scene3DExplorer.tsx", "interaction-state.ts",
                     "scene3d-subentities.ts"]) {
      const src = readFileSync(join(__dirname, f), "utf8");
      for (const cam of ["fetch(", "axios", "XMLHttpRequest", "/api/"]) {
        expect(src, `${f} gọi ${cam}`).not.toContain(cam);
      }
    }
  });
});
