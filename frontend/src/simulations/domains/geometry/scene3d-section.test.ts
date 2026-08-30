/**
 * THIẾT DIỆN như một vật HỌC SINH BẤM ĐƯỢC. **0 mạng, 0 LLM.**
 *
 * Cảnh là **đầu ra thật của backend** (`scene3d-section-fixture.json`, sinh từ
 * chương trình chóp S.ABCD trong `tests/geometry/test_scene3d.py` chạy qua
 * interpreter). Viết tay một cảnh thì test xanh cả khi phép dẫn xuất hỏng, và
 * chỗ dễ hỏng nhất ở đây — `steps` mang `face_index` — chỉ tồn tại vì backend
 * phát ra nó.
 *
 * Ba đỉnh của thiết diện trong cảnh này TRÙNG toạ độ với `P1`, `P2`, `P3`; đỉnh
 * thứ tư không trùng gì cả. Đó là hình dạng thật của bài toán, và là lý do
 * `cycleLabel` phải trả `null` chứ không ghép `"P2P1-đỉnh 3-P3"`.
 */
import { describe, expect, it } from "vitest";
import type { Scene3D, SceneObject } from "./scene3d-model";
import { objectsAt } from "./scene3d-model";
import {
  deriveSectionSubEntities,
  entitiesPresentAt,
  isSubEntity,
  parentSolidOf,
  sectionCycleLabel,
  sectionDetails,
  sectionEdgeId,
  sectionFaceId,
  sectionVertexId,
  sectionViewIds,
  withSubEntities,
} from "./scene3d-subentities";
import {
  explode,
  isVisible,
  isolate,
  select,
  semanticTree,
  selectableIds,
  taoTrangThai,
  visualTransformOf,
} from "./interaction-state";
import fixture from "./scene3d-section-fixture.json";

const CANH = fixture as unknown as Scene3D;
const day = withSubEntities(CANH);
const td = (s: Scene3D = day) => s.objects.find((o) => o.id === "td")!;
const lay = (id: string, s: Scene3D = day) =>
  s.objects.find((o) => o.id === id);

/** Cảnh y hệt, thêm một điểm ĐÃ ĐẶT TÊN trùng đỉnh thứ tư của thiết diện. */
const DU_TEN: Scene3D = {
  ...CANH,
  objects: [
    ...CANH.objects,
    {
      id: "P4", label: "P4", type: "point3", render: "point_marker",
      origin: "derived", producer: "construct_point.midpoint",
      depends: ["C", "S"], xyz: ["0", "1/2", "1"], parent: "chop",
      display_group: ["construction"], source: {},
    } as SceneObject,
  ],
};

// ══ P · DANH TÍNH ════════════════════════════════════════════════════════
describe("P — thiết diện có danh tính ngữ nghĩa ổn định", () => {
  it("là một vật hạng nhất trong cảnh, không phải một đa giác vô danh", () => {
    expect(td().type).toBe("section");
    expect(td().producer).toBe("construct_section");
    expect(td().parent).toBe("chop");
    expect(td().display_group).toContain("section");
  });

  it("id của thiết diện KHÔNG phải id thực thể con", () => {
    expect(isSubEntity("td")).toBe(false);
    expect(parentSolidOf(sectionVertexId("td", 0))).toBe("td");
  });

  it("id thực thể con ỔN ĐỊNH qua hai lần dẫn xuất", () => {
    const a = deriveSectionSubEntities(CANH).map((o) => o.id);
    const b = deriveSectionSubEntities(CANH).map((o) => o.id);
    expect(a).toEqual(b);
    expect(a).toContain(sectionVertexId("td", 0));
    expect(a).toContain(sectionEdgeId("td", 0));
    expect(a).toContain(sectionFaceId("td"));
  });

  it("dẫn xuất KHÔNG chạm cảnh gốc", () => {
    const truoc = CANH.objects.length;
    deriveSectionSubEntities(CANH);
    withSubEntities(CANH);
    expect(CANH.objects.length).toBe(truoc);
  });
});

// ══ Q · ĐỈNH VÀ CẠNH ═════════════════════════════════════════════════════
describe("Q — đỉnh và cạnh dẫn xuất đúng", () => {
  const con = deriveSectionSubEntities(CANH);
  const dinh = con.filter((o) => o.type === "point3");
  const canh = con.filter((o) => o.type === "edge");

  it("đúng 4 đỉnh và 4 cạnh cho một thiết diện tứ giác", () => {
    expect(td().polygon).toHaveLength(4);
    expect(dinh).toHaveLength(4);
    expect(canh).toHaveLength(4);
  });

  it("toạ độ đỉnh CHÉP LẠI từ polygon, không tính lại", () => {
    expect(dinh.map((o) => o.xyz)).toEqual(td().polygon);
  });

  it("cạnh nối thành VÒNG KÍN theo đúng thứ tự kernel đã quyết", () => {
    for (let i = 0; i < canh.length; i++) {
      const sau = canh[(i + 1) % canh.length];
      expect(canh[i].polygon[1]).toEqual(sau.polygon[0]);
    }
  });

  it("cạnh mang MẶT SINH RA NÓ — thứ chỉ backend biết", () => {
    // `steps[].face_index` = [1,4,3,2] trong cảnh này ⇒ "mặt thứ 2,5,4,3".
    expect(canh[0].source?.instruction).toContain("mặt thứ 2 của khối");
    expect(canh[1].source?.instruction).toContain("mặt thứ 5 của khối");
  });

  it("đỉnh TRÙNG điểm có tên thì mượn tên ấy, không thì gọi theo vị trí", () => {
    expect(dinh.map((o) => o.label)).toEqual(["P2", "P1", "Đỉnh 3", "P3"]);
    expect(dinh[0].depends).toEqual(["P2"]);
    expect(dinh[2].depends).toEqual([]);
  });

  it("KHÔNG ghép nửa tên nửa số thành nhãn chu trình", () => {
    expect(sectionCycleLabel(CANH, "td")).toBeNull();
  });

  it("đủ tên thì gọi được cả chu trình", () => {
    expect(sectionCycleLabel(DU_TEN, "td")).toBe("P2P1P4P3");
  });

  it("hai điểm cùng toạ độ ⇒ KHÔNG chọn bừa một cái tên", () => {
    const mo_ho: Scene3D = {
      ...DU_TEN,
      objects: [
        ...DU_TEN.objects,
        { ...(lay("P4", DU_TEN) as SceneObject), id: "Q4", label: "Q4" },
      ],
    };
    expect(sectionCycleLabel(mo_ho, "td")).toBeNull();
  });

  it("mặt tô có đủ đỉnh của thiết diện", () => {
    const mat = con.find((o) => o.id === sectionFaceId("td"))!;
    expect(mat.type).toBe("face");
    expect(mat.polygon).toEqual(td().polygon);
  });

  it("thiết diện suy biến (<3 đỉnh) KHÔNG sinh thực thể con", () => {
    const hong: Scene3D = {
      ...CANH,
      objects: CANH.objects.map((o) =>
        o.id === "td" ? { ...o, polygon: [["0", "0", "1"], ["1", "0", "1"]] } : o,
      ),
    };
    expect(deriveSectionSubEntities(hong)).toHaveLength(0);
  });
});

// ══ R · CÔ LẬP KHÔNG ĐỔI SỰ THẬT ════════════════════════════════════════
describe("R — «Xem thiết diện» không đụng GeometryState", () => {
  it("giữ thiết diện, thực thể con của nó, VÀ khối bị cắt", () => {
    const ids = sectionViewIds(day, "td");
    expect(ids).toContain("td");
    expect(ids).toContain("chop");
    expect(ids).toContain(sectionFaceId("td"));
    expect(ids).toContain(sectionVertexId("td", 0));
    // Mặt phẳng cắt vô hạn — giữ lại là che mất chính thiết diện.
    expect(ids).not.toContain("mp");
  });

  it("cô lập KHÔNG sửa một toạ độ nào", () => {
    const truoc = JSON.stringify(day.objects);
    isolate(taoTrangThai(), sectionViewIds(day, "td"));
    expect(JSON.stringify(day.objects)).toBe(truoc);
  });

  it("cô lập chỉ đổi thứ ĐƯỢC VẼ, không đổi thứ TỒN TẠI", () => {
    const s = isolate(taoTrangThai(), sectionViewIds(day, "td"));
    const co = entitiesPresentAt(day, 99, objectsAt);
    expect(isVisible(s, "td", co)).toBe(true);
    expect(isVisible(s, "mp", co)).toBe(false);
    // "Không vẽ" ≠ "không có": `mp` vẫn nằm trong cảnh với đủ dữ liệu.
    expect(lay("mp")).toBeTruthy();
    expect(co.has("mp")).toBe(true);
  });

  it("ô soi đọc đúng khối và mặt phẳng — theo KIỂU, không theo thứ tự", () => {
    const ct = sectionDetails(day, "td")!;
    expect(ct.vertexCount).toBe(4);
    expect(ct.solidId).toBe("chop");
    expect(ct.planeId).toBe("mp");
    expect(ct.vertexNames).toEqual(["P2", "P1", "Đỉnh 3", "P3"]);
  });

  it("`depends` đảo thứ tự vẫn tra ra đúng khối và mặt phẳng", () => {
    const dao: Scene3D = {
      ...CANH,
      objects: CANH.objects.map((o) =>
        o.id === "td" ? { ...o, depends: ["mp", "chop"], parent: null } : o,
      ),
    };
    const ct = sectionDetails(dao, "td")!;
    expect(ct.solidId).toBe("chop");
    expect(ct.planeId).toBe("mp");
  });

  it("hỏi chi tiết thiết diện trên một vật KHÔNG phải thiết diện ⇒ null", () => {
    expect(sectionDetails(day, "chop")).toBeNull();
    expect(sectionViewIds(day, "chop")).toEqual([]);
  });
});

// ══ S · CHỌN ĐỒNG BỘ CÂY ↔ KHUNG NHÌN ═══════════════════════════════════
describe("S — chọn thiết diện đồng bộ giữa cây và khung nhìn", () => {
  it("thiết diện và mọi thực thể con của nó đều CHỌN ĐƯỢC từ cây", () => {
    const chon = new Set(selectableIds(semanticTree(day)));
    expect(chon.has("td")).toBe(true);
    for (const o of deriveSectionSubEntities(CANH)) {
      expect(chon.has(o.id), `${o.id} phải bấm được trong cây`).toBe(true);
    }
  });

  it("MỘT thẩm quyền chọn — cùng một id dù bấm ở cây hay ở khung", () => {
    const idCanh = sectionEdgeId("td", 2);
    expect(select(taoTrangThai(), idCanh).selected_id)
      .toBe(select(taoTrangThai(), idCanh).selected_id);
    expect(lay(idCanh)).toBeTruthy();
  });

  it("thực thể con treo dưới ĐÚNG thiết diện trong cây", () => {
    for (const o of deriveSectionSubEntities(CANH)) {
      expect(o.parent).toBe("td");
    }
  });
});

// ══ T · PHÁT LẠI ═════════════════════════════════════════════════════════
describe("T — thiết diện chỉ hiện sau bước dựng ra nó", () => {
  it("chưa tới bước dựng thì KHÔNG có thiết diện, cũng không có đỉnh/cạnh", () => {
    const truoc = entitiesPresentAt(day, 8, objectsAt);
    expect(truoc.has("chop")).toBe(true);
    expect(truoc.has("td")).toBe(false);
    expect(truoc.has(sectionVertexId("td", 0))).toBe(false);
    expect(truoc.has(sectionFaceId("td"))).toBe(false);
  });

  it("tới bước dựng thì thiết diện VÀ thực thể con cùng có mặt", () => {
    const sau = entitiesPresentAt(day, 9, objectsAt);
    expect(sau.has("td")).toBe(true);
    for (const o of deriveSectionSubEntities(CANH)) {
      expect(sau.has(o.id), `${o.id} phải có mặt cùng thiết diện`).toBe(true);
    }
  });

  it("thực thể con KHÔNG có sự kiện riêng trong dòng thời gian", () => {
    const idCon = new Set(deriveSectionSubEntities(CANH).map((o) => o.id));
    for (const e of day.events) {
      expect(idCon.has(e.object ?? "")).toBe(false);
    }
  });

  it("có một bước KHÉP nói kết quả, sau các bước vẽ cạnh", () => {
    const cua_td = day.events.filter((e) => e.object === "td");
    expect(cua_td.length).toBeGreaterThan(1);
    const cuoi = cua_td[cua_td.length - 1];
    expect(cuoi.explanation).toContain("4 đỉnh");
    expect(cuoi.explanation).toContain("chop");
    expect(cuoi.explanation).toContain("mp");
  });
});

// ══ U · BUNG KHỐI ════════════════════════════════════════════════════════
describe("U — bung khối không đổi sự thật của thiết diện", () => {
  const bung = explode(taoTrangThai(), "face");

  it("id ngữ nghĩa của thiết diện KHÔNG đổi khi bung", () => {
    const ids = day.objects.map((o) => o.id);
    expect(ids).toContain("td");
    expect(ids).toContain(sectionFaceId("td"));
    expect(bung.exploded_groups).toContain("face");
  });

  it("toạ độ CHÍNH XÁC của thiết diện không đổi khi bung", () => {
    const truoc = JSON.stringify(td().polygon);
    visualTransformOf(bung, day, "td");
    expect(JSON.stringify(td().polygon)).toBe(truoc);
  });

  it("bung chỉ sinh phép dịch TRÌNH BÀY — số thường, không phải phân số", () => {
    for (const id of ["td", sectionFaceId("td")]) {
      const bd = visualTransformOf(bung, day, id);
      for (const x of bd.translate) {
        expect(Number.isFinite(x)).toBe(true);
        expect(typeof x).toBe("number");
      }
    }
  });
});

// ══ V · KHÔNG MẠNG, KHÔNG LLM ═══════════════════════════════════════════
describe("V — đường này hoàn toàn tất định", () => {
  it("không module nào ở đây gọi mạng", async () => {
    const { readFileSync } = await import("node:fs");
    const src = ["scene3d-subentities.ts", "interaction-state.ts"]
      .map((f) => readFileSync(new URL(f, import.meta.url), "utf-8"))
      .join("\n");
    for (const cam of ["fetch(", "XMLHttpRequest", "/api/", "WebSocket"]) {
      expect(src.includes(cam), `${cam} không được có ở tầng này`).toBe(false);
    }
  });

  it("cùng cảnh ⇒ cùng kết quả, không phụ thuộc thứ tự gọi", () => {
    const a = JSON.stringify(withSubEntities(CANH).objects.map((o) => o.id));
    void deriveSectionSubEntities(DU_TEN);
    const b = JSON.stringify(withSubEntities(CANH).objects.map((o) => o.id));
    expect(a).toBe(b);
  });
});
