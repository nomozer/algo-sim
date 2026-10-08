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
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import * as THREE from "three";
import { describe, expect, it } from "vitest";
import type { GeometryProgress, Scene3D, SceneObject } from "./scene3d-model";
import * as VIEW from "./scene3d-view";
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
      // `notation` là thứ nhãn chu trình ghép — `label` nay là câu đọc được
      // (*"Trung điểm của C và S"*), và ghép câu thì ra một chuỗi vô nghĩa.
      id: "P4", label: "Trung điểm của C và S", notation: "P4",
      type: "point3", render: "point_marker",
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

// ══ W15 · TÔ THIẾT DIỆN KHÉP KÍN ĐỌC TÁCH KHỎI MẶT CẮT VÀ KHỐI ═══════════
//
// W14 đo được: phần tô dùng nhánh đa giác chung — hổ phách 0.16, không `renderOrder`,
// không lệch chiều sâu — nằm ĐỒNG PHẲNG với miếng mặt cắt tím (0.2) và trước khối xám
// (0.22), nên vùng thiết diện hoà mất. Cổng ảnh (`SECTION_FILL_DISTINGUISHABLE`) đo trên
// trình duyệt; ở đây khoá DÂY NỐI: vật tô riêng, vẽ sau, lệch chiều sâu, không che gì,
// đúng theo tiến độ từng bước, và móc kiểm thử chỉ chạm đúng các vật tô ấy.
//
// Các hàm W15 truy qua namespace + ép kiểu để bản RED vẫn qua `tsc -b`: thiếu export ⇒
// test đỏ VÌ thiếu, không vì lỗi biên dịch.
const W15 = VIEW as unknown as {
  THU_TU_VE_THIET_DIEN?: number;
  DO_DUC_TO_THIET_DIEN?: number;
  vatThietDienTaiBuoc?: (o: SceneObject, progress?: GeometryProgress) => SceneObject | null;
  datHienToThietDien?: (goc: THREE.Object3D, on: boolean) => string[];
};

const W14_CAT = JSON.parse(readFileSync(fileURLToPath(new URL(
  "../../../../../docs/evaluation/geometry/runs/w14-generic-formation-assumption/inputs/fixtures/"
  + "cross_section_positive.json", import.meta.url)), "utf8")).envelope.scene3d as Scene3D;

function vatTo(goc: THREE.Object3D): THREE.Mesh[] {
  const ra: THREE.Mesh[] = [];
  goc.traverse((x) => { if (x.name.startsWith("section_fill:")) ra.push(x as THREE.Mesh); });
  return ra;
}

function toTaiBuoc(scene: Scene3D, k: number): THREE.Mesh[] {
  const o = scene.objects.find((x) => x.type === "section")!;
  // Như renderer: chỉ vật CÓ MẶT ở bước k (`objectsAt`) mới được dựng.
  if (!objectsAt(scene, k).some((x) => x.id === o.id)) return [];
  const p = scene.formation!.steps[k].geometry_progress?.find((g) => g.object_id === o.id);
  const ve = W15.vatThietDienTaiBuoc!(o, p);
  if (!ve) return [];
  const obj = VIEW.buildObject3D(ve, false);
  return obj ? vatTo(obj) : [];
}

describe("tô thiết diện khép kín đọc tách khỏi mặt cắt và khối", () => {
  it("các export tô thiết diện khép kín tồn tại", () => {
    expect(typeof W15.THU_TU_VE_THIET_DIEN).toBe("number");
    expect(typeof W15.DO_DUC_TO_THIET_DIEN).toBe("number");
    expect(typeof W15.vatThietDienTaiBuoc).toBe("function");
    expect(typeof W15.datHienToThietDien).toBe("function");
  });

  it("khép kín + fill_visible ⇒ một vật tô section_fill:<id>: vẽ sau mặt (trước nét — W16), lệch chiều sâu, đục đủ, không ghi chiều sâu, không phải vật che", () => {
    const obj = VIEW.buildObject3D({ ...td(CANH), closed: true, fill_visible: true }, false)!;
    const to = vatTo(obj);
    expect(to.map((m) => m.name)).toEqual(["section_fill:td"]);
    const m = to[0].material as THREE.MeshStandardMaterial;
    // W15 đòi `>= THU_TU_VE_THIET_DIEN` (vẽ sau MỌI vật, kể cả nét) — chính điều làm cạnh khối
    // đi qua vùng tô bị nhuộm. W16 (§14.4): thứ tự riêng, sau mặt và TRƯỚC nét; quan hệ với
    // mặt/nét thật của cảnh khoá ở describe W16 bên dưới.
    expect(to[0].renderOrder).toBe(VIEW.THU_TU_TO_THIET_DIEN);
    expect(VIEW.THU_TU_TO_THIET_DIEN).toBeLessThan(W15.THU_TU_VE_THIET_DIEN!);
    expect(m.polygonOffset).toBe(true);
    expect(m.polygonOffsetUnits).toBeLessThan(0);
    expect(m.opacity).toBe(W15.DO_DUC_TO_THIET_DIEN);
    expect(W15.DO_DUC_TO_THIET_DIEN!).toBeGreaterThan(0.16);
    expect(m.depthWrite).toBe(false);
    let chieuSau = 0;
    obj.traverse((x) => { if (x.userData.chieuSau) chieuSau += 1; });
    expect(chieuSau).toBe(0);
    expect(obj.getObjectByName("polygon_fill:td")).toBeUndefined();
  });

  it("tô KHÔNG qua phép kiểm chiều sâu: lớp chiều sâu ĐỤC của khối chạy trước, mà thiết diện nằm TRONG khối", () => {
    // Đo ở trình duyệt (W15 Task 10, BROWSER-1 tại c1638891): bật/tắt phần tô ở bước khép
    // cho ΔE = 0 tại MỌI mẫu, desktop lẫn mobile — vật tô có mặt nhưng không điểm ảnh nào
    // được vẽ. Lớp chiều sâu của khối (đục, ghi chiều sâu) chạy trước toàn bộ hàng đợi trong
    // suốt, và mọi điểm trong của thiết diện nằm SAU mặt trước của khối lồi, nên phép kiểm
    // chiều sâu loại phần tô ở mọi điểm ảnh, dù đục bao nhiêu hay vẽ muộn tới đâu.
    const khoi = VIEW.buildObject3D(W14_CAT.objects.find((o) => o.type === "solid")!, false)!;
    const lop: THREE.Mesh[] = [];
    khoi.traverse((x) => { if (x.userData.chieuSau) lop.push(x as THREE.Mesh); });
    expect(lop.length).toBeGreaterThan(0);
    for (const l of lop) {
      expect((l.material as THREE.Material).transparent).toBe(false);
      expect((l.material as THREE.Material).depthWrite).toBe(true);
    }
    const to = vatTo(VIEW.buildObject3D({ ...td(CANH), closed: true, fill_visible: true }, false)!);
    expect((to[0].material as THREE.Material).depthTest).toBe(false);
  });

  it("chưa khép hoặc chưa tới bước tô ⇒ không có vật tô", () => {
    for (const over of [{ closed: false }, { closed: true, fill_visible: false }]) {
      const obj = VIEW.buildObject3D({ ...td(CANH), ...over }, false)!;
      expect(vatTo(obj)).toEqual([]);
    }
  });

  it("đa giác không phải thiết diện giữ nguyên tô chung (polygon_fill)", () => {
    const da: SceneObject = { ...td(CANH), id: "day", type: "polygon3", closed: true, fill_visible: true };
    const obj = VIEW.buildObject3D(da, false)!;
    expect(vatTo(obj)).toEqual([]);
    expect(obj.getObjectByName("polygon_fill:day")).toBeDefined();
  });

  it("theo tiến độ từng bước của cảnh thật: chỉ tô từ bước khép-và-tô; tua ngược là mất", () => {
    const buoc = W14_CAT.formation!.steps;
    const tienDo = (k: number) => buoc[k].geometry_progress?.find((g) => g.object_id === "T");
    const coTo = buoc.map((_s, k) => toTaiBuoc(W14_CAT, k).length > 0);
    const kTo = buoc.findIndex((_s, k) => tienDo(k)?.closed && tienDo(k)?.fill_visible);
    expect(kTo).toBeGreaterThan(0);
    expect(coTo.slice(0, kTo).some(Boolean)).toBe(false);
    expect(coTo[kTo]).toBe(true);
    // tua ngược: từ bước tô quay về bước khép-chưa-tô rồi bước còn hở — không còn vật tô
    expect(toTaiBuoc(W14_CAT, kTo - 1)).toEqual([]);
    expect(toTaiBuoc(W14_CAT, kTo - 2)).toEqual([]);
  });

  it("móc kiểm thử tắt/bật ĐÚNG các vật tô thiết diện, không chạm gì khác", () => {
    const goc = new THREE.Group();
    goc.add(VIEW.buildObject3D({ ...td(CANH), closed: true, fill_visible: true }, false)!);
    goc.add(VIEW.buildObject3D({ ...td(CANH), id: "day", type: "polygon3", closed: true, fill_visible: true }, false)!);
    const truoc = new Map<string, boolean>();
    goc.traverse((x) => truoc.set(x.uuid, x.visible));
    expect(W15.datHienToThietDien!(goc, false)).toEqual(["section_fill:td"]);
    goc.traverse((x) => {
      expect(x.visible).toBe(x.name.startsWith("section_fill:") ? false : truoc.get(x.uuid));
    });
    expect(W15.datHienToThietDien!(goc, true)).toEqual(["section_fill:td"]);
    goc.traverse((x) => expect(x.visible).toBe(truoc.get(x.uuid)));
  });
});

// ══ W16 · PHẦN TÔ NẰM DƯỚI CÁC CẠNH KHỐI (ASSUMPTION_CERTIFICATE_AMENDMENT §14.4) ═══════
//
// Ảnh W15 (cross-section, desktop, bước cuối) cho thấy cạnh SA (đứt) và SC đi qua vùng hổ
// phách bị nhuộm nâu: phần tô (thứ tự 10, không kiểm chiều sâu) vẽ SAU cạnh khối chuẩn (8).
// three.js vẽ hết hàng đợi ĐỤC trước hàng đợi TRONG SUỐT; `renderOrder` chỉ xếp TRONG mỗi
// hàng đợi — nên phép so có nghĩa là so trong hàng đợi trong suốt, nơi cả phần tô lẫn cạnh
// khối chuẩn (`canonicalEdgeMaterial`, `transparent: true`) cùng nằm.
describe("phần tô thiết diện nằm DƯỚI các cạnh khối, TRÊN các mặt", () => {
  it("trong hàng đợi trong suốt: mọi mặt < phần tô < mọi nét; cạnh khối chuẩn thuộc hàng đợi ấy", () => {
    const goc = new THREE.Group();
    for (const o of W14_CAT.objects) {
      const obj = VIEW.buildObject3D(o.type === "section" ? { ...o, closed: true, fill_visible: true } : o, false);
      if (obj) goc.add(obj);
    }
    const [to] = vatTo(goc);
    expect(to).toBeDefined();
    const vl = (x: THREE.Object3D) => (x as THREE.Mesh).material as THREE.Material | undefined;
    const net: THREE.Object3D[] = [];
    const mat: THREE.Object3D[] = [];
    let canhKhoi = 0;
    goc.traverse((x) => {
      const m = vl(x);
      if (x === to || x.userData.chieuSau || !m || m.colorWrite === false || !m.transparent) return;
      if ((x as THREE.Line).isLine) {
        net.push(x);
        if (x.userData.logicalEdgeId) canhKhoi += 1;
      } else if ((x as THREE.Mesh).isMesh) mat.push(x);
    });
    expect(canhKhoi).toBeGreaterThan(0);
    expect(mat.length).toBeGreaterThan(0);
    expect(Math.max(...mat.map((x) => x.renderOrder))).toBeLessThan(to.renderOrder);
    expect(Math.min(...net.map((x) => x.renderOrder))).toBeGreaterThan(to.renderOrder);
  });
});
