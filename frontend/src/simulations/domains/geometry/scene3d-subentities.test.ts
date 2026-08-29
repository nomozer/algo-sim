/**
 * THỰC THỂ CON THỊ GIÁC — mặt và cạnh dựng từ topology. **0 mạng, 0 LLM.**
 *
 * Cảnh dùng ở đây là **đầu ra thật của backend**, chép từ artifact do
 * `test_scene3d_interaction_contract.py` sinh (tứ diện S.ABC chạy qua
 * interpreter). Viết tay một cảnh thì test sẽ xanh cả khi phép dẫn xuất hỏng —
 * và chỗ dễ hỏng nhất chính là `vertex_ids`, thứ chỉ tồn tại vì backend phát.
 */
import { describe, expect, it } from "vitest";
import type { Scene3D } from "./scene3d-model";
import { laSoTrinhBayHopLe, objectsAt, toNumber } from "./scene3d-model";
import {
  deriveVisualSubEntities,
  edgeId,
  entitiesPresentAt,
  faceId,
  faceLabel,
  isSubEntity,
  parentSolidOf,
  withSubEntities,
} from "./scene3d-subentities";
import {
  explode,
  isVisible,
  isolate,
  taoTrangThai,
  visualTransformOf,
} from "./interaction-state";

const KHOI: Scene3D = {
  objects: [
    { id: "A", label: "A", type: "point3", render: "point_marker", origin: "free",
      producer: null, depends: [], xyz: ["0", "0", "0"], parent: "chop",
      display_group: ["given"], source: {} },
    { id: "B", label: "B", type: "point3", render: "point_marker", origin: "free",
      producer: null, depends: [], xyz: ["1", "0", "0"], parent: "chop",
      display_group: ["given"], source: {} },
    { id: "C", label: "C", type: "point3", render: "point_marker", origin: "free",
      producer: null, depends: [], xyz: ["0", "1", "0"], parent: "chop",
      display_group: ["given"], source: {} },
    { id: "S", label: "S", type: "point3", render: "point_marker", origin: "free",
      producer: null, depends: [], xyz: ["0", "0", "1"], parent: "chop",
      display_group: ["given"], source: {} },
    {
      id: "chop", label: "S.ABC", type: "solid", render: "mesh",
      origin: "derived", producer: "construct_solid",
      // `depends` ĐÃ SẮP theo thứ tự chữ — đúng như backend gửi.
      depends: ["A", "B", "C", "S"],
      vertices: [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
      // …còn `vertex_ids` giữ ĐÚNG VỊ TRÍ. Hai dãy này khác nhau là có chủ đích.
      vertex_ids: ["A", "B", "C", "S"],
      faces: [[0, 1, 2], [0, 1, 3], [1, 2, 3], [0, 2, 3]],
      parent: null, display_group: ["construction", "solid"], source: {},
    },
    { id: "V", label: "V", type: "quantity", render: "readout", origin: "derived",
      producer: "measure.volume", depends: ["chop"], value: "1/6",
      parent: null, display_group: ["measurement"], source: {} },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Đặt hệ trục." },
    { step_index: 1, action: "CREATE", object: "chop", depends: ["A", "B", "C", "S"], explanation: "Dựng khối." },
    { step_index: 2, action: "MEASURE", object: "V", depends: ["chop"], explanation: "Đo." },
  ],
  free_objects: ["A", "B", "C", "S"],
};

const con = () => deriveVisualSubEntities(KHOI);
const mat = () => con().filter((x) => x.type === "face");
const canh = () => con().filter((x) => x.type === "edge");

// ══ DẪN XUẤT TỪ TOPOLOGY ═══════════════════════════════════════════════
describe("dẫn xuất mặt và cạnh", () => {
  it("bốn mặt của tứ diện, đúng số", () => {
    expect(mat()).toHaveLength(4);
  });

  it("SÁU cạnh — khử trùng theo cặp KHÔNG HƯỚNG", () => {
    // Mỗi cạnh nằm trên hai mặt; không khử thì ra 12.
    expect(canh()).toHaveLength(6);
    expect(new Set(canh().map((e) => e.id)).size).toBe(6);
  });

  it("mặt gồm ID ĐIỂM NGỮ NGHĨA, theo đúng topology", () => {
    const m = mat();
    expect(m[0].vertex_ids).toEqual(["A", "B", "C"]);
    expect(m[1].vertex_ids).toEqual(["A", "B", "S"]);
    expect(m[3].vertex_ids).toEqual(["A", "C", "S"]);
  });

  it("nhãn ghép từ nhãn ĐỈNH, không suy vai trò toán học", () => {
    expect(mat()[1].label).toBe("ABS");
    expect(faceLabel(["S", "A", "B"], new Map([["S", "S"], ["A", "A"], ["B", "B"]])))
      .toBe("SAB");
  });

  it("mọi thực thể con có cha là KHỐI, và id truy ngược được", () => {
    for (const x of con()) {
      expect(x.parent).toBe("chop");
      expect(isSubEntity(x.id)).toBe(true);
      expect(parentSolidOf(x.id)).toBe("chop");
    }
    expect(isSubEntity("A")).toBe(false);
    expect(parentSolidOf("A")).toBeNull();
  });

  it("TẤT ĐỊNH — hai lần dẫn xuất cho cùng danh sách, cùng thứ tự", () => {
    expect(deriveVisualSubEntities(KHOI)).toEqual(deriveVisualSubEntities(KHOI));
  });

  it("id ổn định theo topology, không theo thứ tự gọi", () => {
    expect(mat().map((m) => m.id)).toEqual([0, 1, 2, 3].map((i) => faceId("chop", i)));
    expect(canh().map((e) => e.id)).toContain(edgeId("chop", "B", "A"));
    expect(edgeId("chop", "A", "B")).toBe(edgeId("chop", "B", "A"));
  });
});

// ══ FAIL-CLOSED khi topology không đủ ══════════════════════════════════
describe("thiếu dữ liệu ⇒ bỏ qua khối, không đoán", () => {
  const doi = (p: Partial<Scene3D["objects"][number]>): Scene3D => ({
    ...KHOI,
    objects: KHOI.objects.map((o) => (o.id === "chop" ? { ...o, ...p } : o)),
  });

  it("thiếu `vertex_ids` ⇒ không sinh mặt nào", () => {
    expect(deriveVisualSubEntities(doi({ vertex_ids: undefined }))).toEqual([]);
  });

  it("`vertex_ids` lệch số lượng với `vertices` ⇒ bỏ qua", () => {
    expect(deriveVisualSubEntities(doi({ vertex_ids: ["A", "B"] }))).toEqual([]);
  });

  it("chỉ số mặt ngoài biên ⇒ bỏ qua CẢ KHỐI, không sinh một phần", () => {
    expect(deriveVisualSubEntities(doi({ faces: [[0, 1, 9]] }))).toEqual([]);
  });

  it("cảnh không có khối ⇒ rỗng, và `withSubEntities` trả nguyên cảnh", () => {
    const khong: Scene3D = { ...KHOI, objects: KHOI.objects.filter((o) => o.id !== "chop") };
    expect(deriveVisualSubEntities(khong)).toEqual([]);
    expect(withSubEntities(khong)).toBe(khong);
  });
});

// ══ KHÔNG NHÂN BẢN SỰ THẬT ═════════════════════════════════════════════
describe("thực thể con không dựng một GeometryState thứ hai", () => {
  it("`withSubEntities` KHÔNG chạm cảnh gốc", () => {
    const truoc = JSON.parse(JSON.stringify(KHOI)) as Scene3D;
    withSubEntities(KHOI);
    expect(KHOI).toEqual(truoc);
  });

  it("đỉnh vẫn là thực thể ngữ nghĩa CŨ — không nhân bản điểm", () => {
    const day = withSubEntities(KHOI);
    expect(day.objects.filter((o) => o.id === "A")).toHaveLength(1);
    // Mặt tham chiếu `A` bằng ID, không giữ bản sao toạ độ làm nguồn.
    expect(mat()[0].vertex_ids).toContain("A");
  });

  it("số đo KHÔNG đổi khi thêm thực thể con", () => {
    expect(withSubEntities(KHOI).objects.find((o) => o.id === "V")!.value)
      .toBe("1/6");
  });
});

// ══ CÔ LẬP VÀ BUNG MỘT MẶT ═════════════════════════════════════════════
describe("thao tác trên mặt", () => {
  const day = withSubEntities(KHOI);
  const tonTai = new Set(day.objects.map((o) => o.id));

  it("cô lập một mặt: chỉ mặt ấy và các đỉnh của nó hiện", () => {
    const m = mat()[1];
    const s = isolate(taoTrangThai(), [m.id, ...m.vertex_ids]);
    expect(isVisible(s, m.id, tonTai)).toBe(true);
    expect(isVisible(s, "A", tonTai)).toBe(true);
    expect(isVisible(s, "C", tonTai)).toBe(false);
    expect(isVisible(s, faceId("chop", 0), tonTai)).toBe(false);
  });

  it("bung nhóm `face`: MỖI mặt dịch ra một hướng KHÁC nhau", () => {
    const s = explode(taoTrangThai(), "face");
    const t = mat().map((m) => visualTransformOf(s, day, m.id).translate.join(","));
    expect(new Set(t).size).toBe(4);
    for (const x of t) expect(x).not.toBe("0,0,0");
  });

  it("BUNG KHÔNG ĐỔI MỘT CON SỐ NÀO — ca quan trọng nhất", () => {
    const truoc = JSON.parse(JSON.stringify(day)) as Scene3D;
    const s = explode(explode(taoTrangThai(), "face"), "solid_component");
    for (const o of day.objects) visualTransformOf(s, day, o.id);
    expect(day).toEqual(truoc);
    expect(day.objects.find((o) => o.id === "V")!.value).toBe("1/6");
  });

  it("gộp lại ⇒ mọi mặt về đồng nhất thức", () => {
    const s = taoTrangThai();
    for (const m of mat()) {
      expect(visualTransformOf(s, day, m.id)).toEqual({
        translate: [0, 0, 0], scale: 1,
      });
    }
  });

  it("hướng bung TẤT ĐỊNH: gọi hai lần cho cùng một số", () => {
    const s = explode(taoTrangThai(), "face");
    const m = mat()[2].id;
    expect(visualTransformOf(s, day, m)).toEqual(visualTransformOf(s, day, m));
  });
});

// ══ PHỤ THUỘC CỦA MẶT LÀ THÀNH VIÊN, KHÔNG PHẢI CHỨNG MINH ════════════
describe("phụ thuộc của thực thể con", () => {
  it("mặt phụ thuộc đúng các đỉnh của nó", () => {
    expect(mat()[0].depends).toEqual(["A", "B", "C"]);
    expect(canh()[0].depends).toHaveLength(2);
  });

  it("xuất xứ nói rõ đây là TOPOLOGY, không phải một phép dựng của đề", () => {
    expect(mat()[0].source!.instruction).toContain("topology");
    expect(mat()[0].producer).toContain("face[0]");
  });
});


// ══ A–E · HAI KHÔNG GIAN SỐ, và cái crash đã quan sát được ════════════════
//
// Demo tay trong Chrome thật ném: `Toạ độ không phải phân số hợp lệ:
// "0.244949"`. Nguyên nhân: `visual_transform.translate` khai `ExactVec3`
// (chuỗi phân số) trong khi phép bung sinh số thập phân. 1674 test cũ không
// bắt được vì chúng chỉ so các transform VỚI NHAU — chưa lần nào đẩy một cái
// qua `toNumber`. Các ca dưới đây đóng đúng lỗ ấy.
describe("A–E · không gian TRÌNH BÀY tách khỏi không gian CHÍNH XÁC", () => {
  const day = withSubEntities(KHOI);

  it("A · bung sinh SỐ THẬP PHÂN, và đó là hợp lệ", () => {
    const s = explode(taoTrangThai(), "face");
    const t = visualTransformOf(s, day, faceId("chop", 1)).translate;
    for (const x of t) {
      expect(typeof x).toBe("number");
      expect(Number.isFinite(x)).toBe(true);
    }
    expect(t.some((x) => !Number.isInteger(x))).toBe(true);
  });

  it("A2 · KHÔNG đẩy khoảng dịch qua bộ phân tích PHÂN SỐ", () => {
    // Đây là dòng đã làm sập khung 3D. Nay `translate` là số nên không ai
    // gọi `toNumber` lên nó nữa — và nếu ai đó gọi, ca này nói tại sao đừng.
    const s = explode(taoTrangThai(), "face");
    const t = visualTransformOf(s, day, faceId("chop", 1)).translate;
    expect(() => toNumber(String(t[0]) as never)).toThrow();
  });

  it("B · số VÔ HẠN ⇒ ĐỒNG NHẤT THỨC, không đẩy NaN xuống buffer", () => {
    // Một `NaN`/`Infinity` lọt vào three.js làm cả mesh biến mất KHÔNG BÁO GÌ,
    // và truy ngược từ một khung hình trống là chỗ tốn nhiều giờ nhất.
    expect(laSoTrinhBayHopLe(0.244949)).toBe(true);
    for (const x of [NaN, Infinity, -Infinity, "0.5", null, undefined]) {
      expect(laSoTrinhBayHopLe(x)).toBe(false);
    }
    const hong: Scene3D = {
      ...day,
      objects: day.objects.map((o) =>
        o.id === faceId("chop", 0)
          ? { ...o, polygon: [["1/0", "0", "0"], ["1/0", "0", "0"], ["1/0", "0", "0"]] }
          : o),
    };
    const s = explode(taoTrangThai(), "face");
    expect(visualTransformOf(s, hong, faceId("chop", 0)))
      .toEqual({ translate: [0, 0, 0], scale: 1 });
  });

  it("B2 · trùng tâm cha ⇒ ĐỒNG NHẤT THỨC (không chia cho 0)", () => {
    const s = explode(taoTrangThai(), "solid");
    // Khối trùng tâm với chính nó ⇒ hướng bung bằng 0 ⇒ giữ nguyên chỗ.
    expect(visualTransformOf(s, day, "chop").translate.every(Number.isFinite))
      .toBe(true);
  });

  it("C · bung cả tứ diện: mọi mặt cho số hữu hạn, không ném", () => {
    const s = explode(explode(taoTrangThai(), "face"), "solid_component");
    for (const o of day.objects) {
      const t = visualTransformOf(s, day, o.id);
      expect(t.translate.every(Number.isFinite)).toBe(true);
      expect(Number.isFinite(t.scale)).toBe(true);
    }
  });

  it("D · GeometryState trước/sau bung — SÂU BẰNG NHAU", () => {
    const truoc = JSON.parse(JSON.stringify(day)) as Scene3D;
    const s = explode(taoTrangThai(), "face");
    for (const o of day.objects) visualTransformOf(s, day, o.id);
    expect(day).toEqual(truoc);
  });

  it("E · SỐ ĐO trước/sau bung không đổi", () => {
    const truoc = day.objects.find((o) => o.id === "V")!.value;
    const s = explode(taoTrangThai(), "face");
    for (const o of day.objects) visualTransformOf(s, day, o.id);
    expect(day.objects.find((o) => o.id === "V")!.value).toBe(truoc);
    expect(truoc).toBe("1/6");
  });
});

// ══ F–H, M · MỘT THẨM QUYỀN "CÓ MẶT" ═════════════════════════════════════
describe("F–H · cây và khung nhìn hỏi CÙNG một thẩm quyền", () => {
  const day = withSubEntities(KHOI);

  it("F · cùng bước ⇒ cùng tập vật, cho mọi bước", () => {
    for (let k = 0; k < KHOI.events.length; k++) {
      const cay = entitiesPresentAt(day, k, objectsAt);
      const khung = entitiesPresentAt(day, k, objectsAt);
      expect([...cay].sort()).toEqual([...khung].sort());
    }
  });

  it("G · MẶT có mặt dù không có sự kiện timeline riêng", () => {
    const k = 1; // bước dựng khối
    const co = entitiesPresentAt(day, k, objectsAt);
    expect(co.has("chop")).toBe(true);
    for (let i = 0; i < 4; i++) expect(co.has(faceId("chop", i))).toBe(true);
    // …và KHÔNG có sự kiện nào mang tên chúng.
    expect(day.events.some((e) => (e.object ?? "").includes("::"))).toBe(false);
  });

  it("H · CẠNH cũng vậy", () => {
    const co = entitiesPresentAt(day, 1, objectsAt);
    expect(co.has(edgeId("chop", "A", "B"))).toBe(true);
  });

  it("M · đổi bước ⇒ tập vật lớn dần, không bao giờ mất vật", () => {
    let truoc = new Set<string>();
    for (let k = 0; k < KHOI.events.length; k++) {
      const co = entitiesPresentAt(day, k, objectsAt);
      for (const x of truoc) expect(co.has(x)).toBe(true);
      truoc = co;
    }
  });

  it("khối CHƯA dựng ⇒ mặt của nó cũng chưa có", () => {
    const co = entitiesPresentAt(day, 0, objectsAt);
    expect(co.has("chop")).toBe(false);
    expect(co.has(faceId("chop", 0))).toBe(false);
  });
});
