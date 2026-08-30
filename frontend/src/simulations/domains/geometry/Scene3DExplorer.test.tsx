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
import { Scene3DExplorer, _VAI_TRO, _moTaNgan } from "./Scene3DExplorer";
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
  selectableIds,
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

// ══ CÂY PHÂN RÃ — nay là NGĂN KÉO GỌI THEO NHU CẦU ════════════════════
//
// Bản trước đòi cây có mặt trong HTML ngay từ đầu. Wave xưởng đổi điều đó có
// chủ đích: cây là bảng gọi ra khi cần, nên mặc định nó KHÔNG dựng — đó là
// cách khung 3D lấy lại phần màn hình mà một sidebar luôn mở đang chiếm.
//
// Nội dung cây vẫn phải đúng, nên phép kiểm chuyển sang `semanticTree` —
// hàm THUẦN mà chính component gọi. Kiểm ở đó là kiểm cùng một sự thật, chỉ
// không phải qua một cú bấm mà `renderToString` không làm được.
describe("cây phân rã: dữ liệu đủ, nhưng gọi ra mới hiện", () => {
  const cay = () => semanticTree(day());

  it("mặc định KHÔNG dựng cây — canvas không bị bảng chiếm chỗ", () => {
    const h = html();
    expect(h).not.toContain("geo3d-tree-item");
    expect(h).not.toContain("geo3d-ngan");
    // …nhưng lối vào thì phải nhìn thấy được.
    expect(h).toContain("Thành phần");
  });

  it("cây có đủ hạng mục Điểm, Cạnh, Mặt", () => {
    const nhan = new Set<string>();
    const di = (ns: ReturnType<typeof semanticTree>) => {
      for (const n of ns) { nhan.add(n.label); di(n.children); }
    };
    di(cay());
    for (const t of ["Điểm", "Cạnh", "Mặt"]) expect(nhan.has(t)).toBe(true);
  });

  it("bốn mặt và sáu cạnh là thực thể RIÊNG, chọn được từng cái", () => {
    const ids = selectableIds(cay());
    // 4 điểm + 1 khối + 1 đại lượng + 4 mặt + 6 cạnh = 16
    expect(ids).toHaveLength(16);
    expect(new Set(ids).size).toBe(16);
  });

  it("KHÔNG dựng hạng mục rỗng", () => {
    const nhan: string[] = [];
    const di = (ns: ReturnType<typeof semanticTree>) => {
      for (const n of ns) { nhan.push(n.label); di(n.children); }
    };
    di(cay());
    expect(nhan).not.toContain("Thiết diện");
  });

  it("cây và cảnh dày khớp nhau: mọi thực thể có đúng một nút", () => {
    const ids = day().objects.map((o) => o.id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(selectableIds(cay()).sort()).toEqual([...ids].sort());
  });
});

// ══ MỘT THẨM QUYỀN CHỌN ══════════════════════════════════════════════
describe("một thẩm quyền chọn", () => {
  it("component KHÔNG giữ selection thứ hai", () => {
    const src = readFileSync(join(__dirname, "Scene3DExplorer.tsx"), "utf8");
    // Đúng MỘT `useState`, và nó giữ `InteractionState`. Thêm
    // `treeSelected`/`viewportSelected` là mời hai bản lệch nhau.
    // Đúng MỘT `useState<InteractionState>`. Xưởng nay còn hai `useState`
    // khác — ngăn kéo nào đang mở, và bật/tắt chế độ Chi tiết — nhưng chúng
    // giữ CÁCH BÀY, không giữ *đang chọn cái gì*. Ràng buộc là một thẩm quyền
    // CHỌN, không phải một `useState` duy nhất; đếm `useState` là đếm nhầm thứ.
    expect((src.match(/useState<InteractionState>/g) ?? []).length).toBe(1);
    expect((src.match(/selected_id:/g) ?? []).length).toBe(0);
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


// ══ §16 · HỢP ĐỒNG CỦA XƯỞNG ══════════════════════════════════════════════
describe("§16 · xưởng: canvas là màn hình, chữ gọi ra khi cần", () => {
  const src = readFileSync(join(__dirname, "Scene3DExplorer.tsx"), "utf8");
  const ma = src
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/^\s*\/\/.*$/gm, "");

  it("MẶC ĐỊNH gần như không có chữ: không tiêu đề, không đoạn dẫn", () => {
    const h = html();
    expect(h).not.toContain("<h3");
    expect(h).not.toContain("<p class=\"geo3d-lead\"");
    // Ba thứ duy nhất được phép có chữ ở màn mặc định: thanh trên, nút nổi,
    // dòng bước ở đáy. Không có bảng nào mở sẵn.
    expect(h).not.toContain("geo3d-ngan");
    expect(h).not.toContain("geo3d-soi");
  });

  it("KHÔNG phơi metadata kỹ thuật ở màn mặc định", () => {
    const h = html();
    for (const cam of ["point3", "producer", "depends", "source_fact_id",
                       "origin", "construct_point", "measure."]) {
      expect(h, `màn mặc định lộ ${cam}`).not.toContain(cam);
    }
  });

  it("canvas TỒN TẠI, và ngăn kéo KHÔNG bóp nó lại", () => {
    expect(html()).toContain("geo3d-canvas");
    // Ngăn kéo và ô soi neo tuyệt đối vào sân khấu ⇒ phủ LÊN khung, không
    // chen cạnh nó. Một bảng chen cạnh là một sidebar, và sidebar là thứ
    // wave này gỡ đi.
    const css = readFileSync(join(__dirname, "../../../styles/global.css"), "utf8");
    for (const lop of [".geo3d-ngan {", ".geo3d-soi {"]) {
      const i = css.indexOf(lop);
      expect(i).toBeGreaterThan(-1);
      expect(css.slice(i, i + 220)).toContain("position: absolute");
    }
  });

  it("ngăn kéo KHÔNG giữ một bản chọn riêng", () => {
    // `ngan` chỉ giữ *bảng nào đang mở*. Nếu nó giữ thêm một id được chọn thì
    // cây và khung nhìn sẽ chỉ về hai vật khác nhau.
    expect(ma).toContain('useState<"thanh-phan" | "de" | null>');
    for (const x of ["nganSelected", "treeSelected", "viewportSelected"]) {
      expect(ma, `ngăn kéo giữ chọn riêng: ${x}`).not.toContain(x);
    }
  });

  it("ô soi là NGỮ CẢNH: không chọn gì thì không có nút thao tác nào", () => {
    const h = html();
    for (const nut of ["Chỉ xem phần này", "Xem cấu tạo", "Ẩn"]) {
      expect(h, `nút ${nut} hiện khi chưa chọn gì`).not.toContain(nut);
    }
    // …nhưng thao tác TOÀN CẢNH thì luôn có, vì chúng luôn áp dụng được.
    expect(h).toContain("Tách khối");
    expect(h).toContain("Xem lại toàn hình");
  });

  it("phát lại dùng ĐÚNG `current_step` cũ, không đẻ dòng thời gian thứ hai", () => {
    expect(ma).toContain("tt.current_step");
    expect(ma).toContain("interaction={tt}");
    // Không có state bước riêng trong xưởng.
    expect(ma).not.toMatch(/useState[^\n]*[Ss]tep/);
  });

  it("chế độ Chi tiết KHÔNG làm mất dữ liệu — chỉ đổi ai được mời đọc", () => {
    // Cùng một `scene` đi vào; `chiTiet` chỉ gác phần HIỂN THỊ.
    expect(ma).toContain("{chiTiet &&");
    expect(ma).toContain("dangChon.producer");
    // Dữ liệu vẫn nguyên trong model dù chế độ nào.
    const o = day().objects.find((x) => x.id === "chop")!;
    expect(o.producer).toBe("construct_solid");
    expect(o.depends).toEqual(["A", "B", "C", "S"]);
  });

  it("thuật ngữ của HỌC SINH, không của lập trình viên", () => {
    // DESIGN_BRIEF §3.4. `moTaNgan` dịch `producer` sang tiếng người học.
    expect(_moTaNgan({ type: "point3", producer: "construct_point.midpoint",
                       depends: ["S", "A"] }, (x) => x)).toBe("Trung điểm của S, A");
    expect(_moTaNgan({ type: "point3", producer: null, depends: [] },
                     (x) => x)).toBe("Điểm đề cho");
    expect(_VAI_TRO.point3).toBe("Điểm");
    expect(_VAI_TRO.face).toBe("Mặt");
  });
});
