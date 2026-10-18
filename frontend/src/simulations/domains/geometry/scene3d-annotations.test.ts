/**
 * W17 · §15.4 — SỐ ĐO TRÊN HÌNH: hợp đồng gắn đối tượng do backend sở hữu.
 *
 * Frontend chỉ đọc `annotation` (kind · category · subject_ids · anchor) mà backend phát cho
 * một đại lượng, và luật khả dụng của lớp lời giải (`solutionAt`). Nó không bao giờ suy chủ thể
 * từ tên biến (`AB_length`) và không tự tính giá trị.
 */
import { describe, expect, it } from "vitest";
import type { Scene3D } from "./scene3d-model";
import { MAU_VAI_TRO } from "./scene3d-roles";
import { mauNhanChung } from "./scene3d-view";
import {
  annotationsAt, annotationAnchor, DEFAULT_ANNOTATION_VIEW, NEO_TOI_DA, placeAnnotationLabels, projectionWitnessesAt,
  witnessesShown,
} from "./scene3d-annotations";

/** W18: "Hiện tất cả" — cùng tập nhãn khả dụng mà W17 hiện khi cả hai công tắc bật. */
const TAT_CA = { showAll: true };

const P = (id: string, xyz: [string, string, string]) => ({
  id, label: `Điểm ${id}`, notation: id, type: "point3", render: "marker",
  origin: "free", producer: null, depends: [], xyz,
});

/** Lăng trụ thu nhỏ: AB = 3 (đề cho, có annotation), XY_length (đề cho, KHÔNG annotation —
 *  tên biến nói "đoạn XY" nhưng backend không gắn được), diện tích đáy (đo), thể tích (kết quả). */
const canh = (): Scene3D => ({
  free_objects: ["A", "B", "C", "AB_length", "XY_length"],
  objects: [
    P("A", ["0", "0", "0"]), P("B", ["3", "0", "0"]), P("C", ["0", "4", "0"]), P("D", ["0", "0", "5"]),
    { id: "day_ABC", label: "Đáy ABC", notation: "ABC", type: "polygon3", render: "mesh",
      origin: "derived", producer: "construct_polygon", depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"] },
    { id: "khoi", label: "Khối ABCD", notation: "ABCD", type: "solid", render: "mesh",
      origin: "derived", producer: "construct_solid", depends: ["A", "B", "C", "D"],
      vertex_ids: ["A", "B", "C", "D"], vertices: [], faces: [] },
    { id: "AB_length", label: "AB", notation: "AB", type: "quantity", render: "readout", origin: "free",
      producer: null, depends: [], value: "3", exact: { kind: "rational", value: "3" },
      annotation: { kind: "length", category: "measurement", subject_ids: ["A", "B"], anchor: "segment" } },
    { id: "XY_length", label: "XY", notation: "XY", type: "quantity", render: "readout", origin: "free",
      producer: null, depends: [], value: "7", exact: { kind: "rational", value: "7" } },
    { id: "dien_tich", label: "Diện tích ABC", notation: "S(ABC)", type: "quantity", render: "readout",
      origin: "derived", producer: "measure.area", depends: ["day_ABC"], value: "6",
      exact: { kind: "rational", value: "6" },
      annotation: { kind: "area", category: "measurement", subject_ids: ["day_ABC"], anchor: "region" } },
    { id: "the_tich", label: "Thể tích ABCD", notation: "V(ABCD)", type: "quantity", render: "readout",
      origin: "derived", producer: "measure.volume", depends: ["khoi", "dien_tich"], value: "10",
      exact: { kind: "rational", value: "10" },
      annotation: { kind: "volume", category: "result", subject_ids: ["khoi"], anchor: "solid" } },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Dữ kiện.",
      semantic_kind: "EXPLANATION" },
    { step_index: 1, action: "CREATE", object: "day_ABC", depends: ["A", "B", "C"], explanation: "Đáy.",
      semantic_kind: "GEOMETRY_CONSTRUCTION" },
    { step_index: 2, action: "CREATE", object: "khoi", depends: ["day_ABC", "D"], explanation: "Khối.",
      semantic_kind: "GEOMETRY_CONSTRUCTION" },
    { step_index: 3, action: "MEASURE", object: "dien_tich", depends: ["day_ABC"], explanation: "Diện tích.",
      semantic_kind: "MEASUREMENT" },
    { step_index: 4, action: "MEASURE", object: "the_tich", depends: ["khoi"], explanation: "Thể tích.",
      semantic_kind: "MEASUREMENT" },
    { step_index: 5, action: "MEASURE", object: "the_tich", depends: ["khoi"], explanation: "Kết luận.",
      semantic_kind: "FINAL_RESULT" },
  ],
} as unknown as Scene3D);

const ids = (xs: { id: string }[]) => xs.map((x) => x.id).sort();
const CUOI = 5;

describe("số đo trên hình (§15.4)", () => {
  it("ẩn chữ đáp án không xoá annotation nguồn dùng dựng nhân chứng; không sửa payload", () => {
    const scene = canh();
    const before = JSON.stringify(scene);
    const view = { showAll: true, hiddenIds: new Set(["the_tich"]) };
    expect(annotationsAt(scene, CUOI, view, "the_tich")).toEqual(annotationsAt(scene, CUOI, TAT_CA, "the_tich"));
    expect(JSON.stringify(scene)).toBe(before);
  });
  it("chỉ đại lượng CÓ annotation của backend mới có nhãn — không suy từ tên biến", () => {
    const a = annotationsAt(canh(), CUOI, TAT_CA, null);
    expect(ids(a)).toEqual(["AB_length", "dien_tich", "the_tich"]);
    expect(a.map((x) => x.id)).not.toContain("XY_length");
  });

  it("chữ nhãn = ký hiệu = giá trị của payload; đơn vị chỉ khi payload có", () => {
    const a = annotationsAt(canh(), CUOI, TAT_CA, null);
    const chu = Object.fromEntries(a.map((x) => [x.id, x.text]));
    expect(chu).toEqual({ AB_length: "AB = 3", dien_tich: "S(ABC) = 6", the_tich: "V(ABCD) = 10" });
  });

  it("không lộ trước: tiến rồi lùi, nhãn chỉ có từ bước đại lượng khả dụng và chủ thể có mặt", () => {
    const theoBuoc = [0, 1, 2, 3, 4, 5].map((k) => ids(annotationsAt(canh(), k, TAT_CA, null)));
    const lui = [5, 4, 3, 2, 1, 0].map((k) => ids(annotationsAt(canh(), k, TAT_CA, null)));
    expect(theoBuoc.slice().reverse()).toEqual(lui);
    for (const [k, a] of theoBuoc.entries()) {
      if (k < 3) expect(a).not.toContain("dien_tich");
      if (k < 5) expect(a).not.toContain("the_tich");
    }
    expect(theoBuoc[5]).toContain("the_tich");
  });

  it("dữ kiện có từ đầu nhưng chủ thể chưa dựng ⇒ chưa có nhãn (tiêm lỗi FE3, W17 Task 7)", () => {
    const s = canh();
    s.free_objects = [...s.free_objects, "AD_length"];
    (s.objects as unknown as object[]).push({ id: "AD_length", label: "AD", notation: "AD", type: "quantity",
      render: "readout", origin: "free", producer: null, depends: [], value: "5", exact: { kind: "rational", value: "5" },
      annotation: { kind: "length", category: "measurement", subject_ids: ["A", "D"], anchor: "segment" } });
    (s.events[2] as unknown as { objects?: string[] }).objects = ["D"];
    // W2 · A: chỗ bám của nhãn AD là CẠNH AD của khối dựng ở bước 2 (backend phát `edge_ownership` cho khối);
    // điểm D có mặt thôi chưa đủ.
    (s.objects.find((o) => o.id === "khoi") as unknown as { edge_ownership: object[] }).edge_ownership = [
      { edge_id: "khoi::edge:A-D", endpoint_ids: ["A", "D"], adjacent_surface_ids: [] }];
    expect([0, 1, 2, 3].map((k) => annotationsAt(s, k, TAT_CA, null)
      .some((x) => x.id === "AD_length"))).toEqual([false, false, true, true]);
  });

  it("chọn chủ thể thì nhãn liên quan được ưu tiên", () => {
    const thuong = annotationsAt(canh(), CUOI, TAT_CA, null);
    const chon = annotationsAt(canh(), CUOI, TAT_CA, "day_ABC");
    const uu = (xs: { id: string; priority: number }[], id: string) => xs.find((x) => x.id === id)!.priority;
    expect(uu(chon, "dien_tich")).toBeGreaterThan(uu(thuong, "dien_tich"));
    expect(uu(chon, "AB_length")).toBe(uu(thuong, "AB_length"));
  });

  it("cặp điểm–đường: neo ở ĐIỂM của cặp — không tự dựng chân đường vuông góc ở phía trình bày", () => {
    // `scene3d.test.tsx` (5D): suy luận hình học (chân đường cao, giao tuyến, góc) CẤM ở frontend,
    // kể cả để đặt nhãn. "d(S, BD)" đứng cạnh S; vật không phải điểm thì không có neo ở đây.
    const s = canh();
    s.objects.push({ id: "BD", label: "Đường thẳng BD", notation: "BD", type: "line3", render: "line",
      origin: "derived", producer: "line_through", depends: ["B", "D"],
      point: ["3", "0", "0"], direction: ["-3", "0", "5"] } as never);
    expect(annotationAnchor(s, { anchor: "pair", subject_ids: ["BD", "C"] })).toEqual([0, 4, 0]);
    expect(annotationAnchor(s, { anchor: "pair", subject_ids: ["BD", "day_ABC"] })).toBeNull();
  });

  it("điểm neo: trung điểm đoạn, trọng tâm miền, trọng tâm khối — chỉ từ chủ thể backend chỉ", () => {
    const s = canh();
    const [ab, dt, v] = ["AB_length", "dien_tich", "the_tich"].map(
      (id) => annotationAnchor(s, annotationsAt(s, CUOI, TAT_CA, null).find((x) => x.id === id)!));
    expect(ab).toEqual([1.5, 0, 0]);
    expect(dt).toEqual([1, 4 / 3, 0]);
    expect(v).toEqual([0.75, 1, 1.25]);
  });
});

/* W18 · §16.5 — NHÃN TẬP TRUNG (thay U-W17-1). Mặc định: dữ kiện đề cho (`role = given`) khả dụng ở
 * bước đang xem. Chọn một đại lượng: nó + chuỗi số của nó (`tangNhanManh`: dữ kiện số, trung gian).
 * Chọn một vật: đại lượng có chủ thể là vật ấy. "Hiện tất cả": mọi nhãn khả dụng. Luật khả dụng và
 * "không lộ trước" giữ nguyên ở mọi chế độ. §16.6: `same_as` không có nhãn thứ hai. §16.7: nhân chứng. */
const canh18 = (): Scene3D => {
  const s = canh();
  const theoId = new Map(s.objects.map((o) => [o.id, o as unknown as Record<string, unknown>]));
  const vai = { AB_length: "given", dien_tich: "intermediate", the_tich: "result" } as const;
  for (const [id, r] of Object.entries(vai)) {
    const o = theoId.get(id)!;
    o.annotation = { ...(o.annotation as object), role: r };
  }
  theoId.get("dien_tich")!.dependency_edges = [{ source_id: "AB_length", relation: "numerical" }];
  theoId.get("the_tich")!.dependency_edges = [{ source_id: "dien_tich", relation: "numerical" }];
  theoId.get("dien_tich")!.depends = ["day_ABC", "AB_length"];
  (s.objects as unknown as object[]).push(
    // h đo lại đúng đoạn AB (cùng chủ thể với dữ kiện): backend gộp bằng `same_as`.
    { id: "h", label: "Chiều cao", notation: "h", type: "quantity", render: "readout", origin: "derived",
      producer: "measure.distance", depends: ["A", "B"], value: "3", exact: { kind: "rational", value: "3" },
      annotation: { kind: "length", category: "measurement", role: "intermediate", subject_ids: ["A", "B"],
        anchor: "segment", same_as: "AB_length" } },
    { id: "BD", label: "Đường thẳng BD", notation: "BD", type: "line3", render: "line", origin: "derived",
      producer: "construct_line", depends: ["B", "D"], point: ["3", "0", "0"], direction: ["-3", "0", "5"] },
    // d(C, BD): nhân chứng do backend phát — chân CHÍNH XÁC, frontend chỉ vẽ.
    { id: "d_C_BD", label: "Khoảng cách giữa C và BD", notation: "d(C, BD)", type: "quantity", render: "readout",
      origin: "derived", producer: "measure.distance", depends: ["C", "BD"], value: "4",
      exact: { kind: "rational", value: "4" },
      annotation: { kind: "distance", category: "measurement", role: "intermediate", subject_ids: ["C", "BD"],
        anchor: "witness", witness: { from: "C", foot: ["75/34", "0", "45/34"], on: "BD",
          marker: { u: ["-3", "0", "5"], v: ["-75/34", "4", "-45/34"] } } } },
  );
  s.events.push(
    { step_index: 6, action: "CREATE", object: "BD", depends: ["B", "D"], explanation: "Đường BD.",
      semantic_kind: "GEOMETRY_CONSTRUCTION" },
    { step_index: 7, action: "MEASURE", object: "h", depends: ["A", "B"], explanation: "h.",
      semantic_kind: "MEASUREMENT" },
    { step_index: 8, action: "MEASURE", object: "d_C_BD", depends: ["C", "BD"], explanation: "d.",
      semantic_kind: "MEASUREMENT" },
  );
  return s;
};
const CUOI18 = 8;

describe("nhãn tập trung (§16.5–16.7)", () => {
  it("mặc định chỉ dữ kiện đề cho — không đáp số, không đại lượng trung gian", () => {
    expect(DEFAULT_ANNOTATION_VIEW).toEqual({ showAll: false });
    expect(ids(annotationsAt(canh18(), CUOI18, DEFAULT_ANNOTATION_VIEW, null))).toEqual(["AB_length"]);
  });

  it("Hiện tất cả: mọi nhãn khả dụng; đáp số vẫn chỉ từ bước kết luận", () => {
    expect(ids(annotationsAt(canh18(), CUOI18, TAT_CA, null))).toEqual(["AB_length", "d_C_BD", "dien_tich", "the_tich"]);
    expect(ids(annotationsAt(canh18(), 4, TAT_CA, null))).not.toContain("the_tich");
  });

  it("chọn một đại lượng: nó và chuỗi số của nó (dữ kiện số, trung gian) — không hơn", () => {
    const a = annotationsAt(canh18(), CUOI18, DEFAULT_ANNOTATION_VIEW, "the_tich");
    expect(ids(a)).toEqual(["AB_length", "dien_tich", "the_tich"]);
    expect(a.find((x) => x.id === "the_tich")!.related).toBe(true);
    // chọn trước bước kết luận: đáp số vẫn chưa được lộ
    expect(ids(annotationsAt(canh18(), 4, DEFAULT_ANNOTATION_VIEW, "the_tich"))).not.toContain("the_tich");
  });

  it("chọn một vật: các đại lượng có chủ thể là vật ấy", () => {
    expect(ids(annotationsAt(canh18(), CUOI18, DEFAULT_ANNOTATION_VIEW, "day_ABC"))).toEqual(["AB_length", "dien_tich"]);
  });

  it("same_as: không có nhãn thứ hai; chọn nó là đưa nhãn của dữ kiện lên", () => {
    expect(ids(annotationsAt(canh18(), CUOI18, TAT_CA, null))).not.toContain("h");
    const a = annotationsAt(canh18(), CUOI18, DEFAULT_ANNOTATION_VIEW, "h");
    expect(ids(a)).toEqual(["AB_length"]);
    expect(a[0].related).toBe(true);
  });

  it("envelope v109 không có `role`: suy từ category và origin (dữ kiện vẫn hiện mặc định)", () => {
    const a = annotationsAt(canh(), CUOI, DEFAULT_ANNOTATION_VIEW, null);
    expect(ids(a)).toEqual(["AB_length"]);
  });

  it("nhân chứng: neo ở trung điểm đoạn từ điểm tới CHÂN backend phát", () => {
    const s = canh18();
    const d = annotationsAt(s, CUOI18, TAT_CA, null).find((x) => x.id === "d_C_BD")!;
    const p = annotationAnchor(s, d)!;
    [75 / 68, 2, 45 / 68].forEach((v, i) => expect(p[i]).toBeCloseTo(v, 12));
  });

  it("nhân chứng chỉ được vẽ khi nhãn khoảng cách của nó đang hiện", () => {
    const s = canh18();
    expect(witnessesShown(s, annotationsAt(s, CUOI18, DEFAULT_ANNOTATION_VIEW, null))).toEqual([]);
    const w = witnessesShown(s, annotationsAt(s, CUOI18, DEFAULT_ANNOTATION_VIEW, "d_C_BD"));
    expect(w.map((x) => x.id)).toEqual(["d_C_BD"]);
    expect(w[0].vai).toBe("khoang_cach");
    expect(w[0].from).toEqual([0, 4, 0]);
    [75 / 34, 0, 45 / 34].forEach((v, i) => expect(w[0].foot[i]).toBeCloseTo(v, 12));
    expect(w[0].u).toEqual([-3, 0, 5]);
  });
});

/* §15.5 — luật HỘP NHÃN mà bộ đo trình duyệt kiểm: trong khung, không đè nhãn điểm/nút điều khiển,
 * điểm gần nhất của hộp cách điểm neo chiếu ≤ 24 px. Hàm thuần: vị trí px vào, hộp ra. */
describe("đặt nhãn số đo (§15.5)", () => {
  const KHUNG = { w: 400, h: 300 };
  const n = (id: string, ax: number, ay: number, priority = 1) => ({ id, ax, ay, w: 60, h: 18, priority });
  const gan = (r: { x: number; y: number; w: number; h: number }, ax: number, ay: number) =>
    Math.hypot(Math.max(r.x - ax, 0, ax - r.x - r.w), Math.max(r.y - ay, 0, ay - r.y - r.h));

  it("khung trống ⇒ nhãn nằm ngay TRÊN điểm neo", () => {
    expect(placeAnnotationLabels([n("a", 200, 150)], [], KHUNG).get("a")).toEqual({ x: 170, y: 126, w: 60, h: 18 });
  });

  it("chỗ trên đã có nhãn điểm ⇒ xuống dưới, không đè", () => {
    const r = placeAnnotationLabels([n("a", 200, 150)], [{ x: 160, y: 120, w: 80, h: 26 }], KHUNG).get("a")!;
    expect(r.y).toBe(156);
  });

  it("điểm neo sát mép ⇒ hộp kẹp vào trong khung mà vẫn gần neo", () => {
    const r = placeAnnotationLabels([n("a", 4, 150)], [], KHUNG).get("a")!;
    expect(r.x).toBeGreaterThanOrEqual(0);
    expect(gan(r, 4, 150)).toBeLessThanOrEqual(NEO_TOI_DA);
  });

  it("bốn phía đã kín ⇒ thử bốn góc (lượt trình duyệt T7: S(ABC) kẹp giữa AB = 3 và AC = 4 bị ẩn)", () => {
    const hai = [{ x: 135, y: 135, w: 50, h: 18 }, { x: 215, y: 140, w: 50, h: 20 }];
    const r = placeAnnotationLabels([n("a", 200, 150)], hai, KHUNG).get("a");
    expect(r).toEqual({ x: 134, y: 156, w: 60, h: 18 });
    expect(gan(r!, 200, 150)).toBeLessThanOrEqual(NEO_TOI_DA);
  });

  it("tám chỗ sát neo đều chạm ⇒ lùi ra vòng xa hơn, vẫn ≤ 24 px (lượt xác nhận T7: S(ABC) chạm AB = 3 nửa px)", () => {
    const n85 = { id: "a", ax: 200, ay: 150, w: 85, h: 20, priority: 1 };
    const hai = [{ x: 110, y: 136, w: 52, h: 20.5 }, { x: 230, y: 140, w: 52, h: 20 }];
    const r = placeAnnotationLabels([n85], hai, KHUNG).get("a");
    expect(r).toEqual({ x: 157.5, y: 162, w: 85, h: 20 });
    expect(gan(r!, 200, 150)).toBe(12);
  });

  it("không còn chỗ trong 24 px ⇒ ẩn — nhãn không bao giờ trôi xa vật nó gọi tên", () => {
    expect(placeAnnotationLabels([n("a", 200, 150)], [{ x: 0, y: 0, w: 400, h: 300 }], KHUNG).size).toBe(0);
  });

  it("điểm neo ngoài khung ⇒ không đặt", () => {
    expect(placeAnnotationLabels([n("a", -10, 150), n("b", 200, 320)], [], KHUNG).size).toBe(0);
  });

  it("ưu tiên cao đặt trước; nhãn sau tránh nhãn trước", () => {
    const m = placeAnnotationLabels([n("thap", 200, 150, 1), n("cao", 200, 150, 5)], [], KHUNG);
    expect(m.get("cao")!.y).toBe(126);
    expect(m.get("thap")!.y).toBe(156);
  });
});

/* Review I1 — điểm dựng bằng hình chiếu vuông góc mang đoạn vuông góc PHỤ + ký hiệu tại CHÂN do backend phát
 * (`perpendicular_witness`). Hiện đúng khi điểm chiếu đã có mặt ở bước đang xem (bất biến #31). */
describe("nhân chứng hình chiếu (review I1)", () => {
  const canhChieu = (): Scene3D => ({
    free_objects: ["A", "B", "C", "S"],
    objects: [
      P("A", ["0", "0", "0"]), P("B", ["1", "0", "0"]), P("C", ["0", "1", "0"]), P("S", ["0", "0", "1"]),
      { ...P("K", ["3/8", "3/8", "1/4"]), origin: "derived", producer: "construct_point", depends: ["A"],
        perpendicular_witness: { from: "A", foot: ["3/8", "3/8", "1/4"], on: "derived_K_plane",
          marker: { u: ["-3/8", "-3/8", "3/4"], v: ["-3/8", "-3/8", "-1/4"] } } },
    ],
  } as unknown as Scene3D);

  it("điểm chiếu chưa có mặt ở bước này ⇒ không vẽ đoạn vuông góc", () => {
    expect(projectionWitnessesAt(canhChieu(), new Set(["A", "B", "C", "S"]))).toEqual([]);
  });

  it("ẩn điểm gốc hoặc chân thì không để lại nhân chứng của điểm đã ẩn", () => {
    expect(projectionWitnessesAt(canhChieu(), new Set(["B", "C", "S", "K"]))).toEqual([]);
    expect(projectionWitnessesAt(canhChieu(), new Set(["A", "B", "C", "S"]))).toEqual([]);
  });

  it("đoạn vuông góc của hình chiếu là ĐƯỜNG PHỤ, không mang xanh 'đang xét' (W12) — chỉ nhân chứng khoảng cách mới mang", () => {
    const [w] = projectionWitnessesAt(canhChieu(), new Set(["A", "B", "C", "S", "K"]));
    expect(w.vai).toBe("hinh_chieu");
    expect(mauNhanChung("hinh_chieu")).not.toBe(MAU_VAI_TRO.dich);
    expect(mauNhanChung("hinh_chieu")).not.toBe(MAU_VAI_TRO.moi_dung);
    expect(mauNhanChung("khoang_cach")).toBe(MAU_VAI_TRO.dich);
  });

  it("điểm chiếu có mặt ⇒ đoạn từ điểm gốc tới chân, ký hiệu dựng tại CHÍNH chân backend phát", () => {
    const [w, ...con] = projectionWitnessesAt(canhChieu(), new Set(["A", "B", "C", "S", "K"]));
    expect(con).toEqual([]);
    expect(w.id).toBe("perpendicular:K");
    expect(w.from).toEqual([0, 0, 0]);
    expect(w.foot).toEqual([3 / 8, 3 / 8, 1 / 4]);
    expect(w.u).toEqual([-3 / 8, -3 / 8, 3 / 4]);
    expect(w.v).toEqual([-3 / 8, -3 / 8, -1 / 4]);
  });

  it("đại lượng khoảng cách neo vào đoạn nhân chứng hình chiếu (d(A, K)) hiện nhãn khi điểm chiếu K và đoạn vuông góc đã có mặt", () => {
    const s = canhChieu();
    s.objects.push({
      id: "d_A_K", label: "Khoảng cách giữa A và K", notation: "d(A, K)", type: "quantity", render: "readout",
      origin: "derived", producer: "measure.distance", depends: ["A", "K"], value: "√22/8",
      exact: { kind: "radical", coefficient: "1/8", radicand: 22 },
      annotation: { kind: "length", category: "result", role: "result", subject_ids: ["A", "K"], anchor: "segment" },
    } as never);
    s.events = [
      { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Đầu.", semantic_kind: "EXPLANATION" },
      { step_index: 1, action: "CREATE", object: "K", depends: ["A"], explanation: "Dựng K.", semantic_kind: "GEOMETRY_CONSTRUCTION" },
      { step_index: 2, action: "MEASURE", object: "d_A_K", depends: ["A", "K"], explanation: "Kết luận.", semantic_kind: "FINAL_RESULT" },
    ];
    // Bước 0 (K chưa dựng): chưa hiện
    expect(annotationsAt(s, 0, TAT_CA, "d_A_K")).toEqual([]);
    // Bước 2 (K đã dựng kèm perpendicular_witness từ A, và d_A_K đã kết luận): hiện nhãn d(A, K) = √22/8
    const a = annotationsAt(s, 2, DEFAULT_ANNOTATION_VIEW, "d_A_K");
    expect(a.map((x) => x.id)).toEqual(["d_A_K"]);
    expect(a[0].text).toBe("d(A, K) = √22/8");
  });

  it("đại lượng khoảng cách kết quả có witness trên mặt phẳng (không có point3 chân riêng) hiện đoạn vuông góc ở bước kết luận", () => {
    const s: Scene3D = {
      free_objects: ["A", "B", "S"],
      objects: [
        P("A", ["0", "0", "0"]), P("B", ["1", "0", "0"]), P("S", ["0", "0", "1"]),
        { ...P("M", ["1/2", "1/2", "1/2"]), origin: "derived" },
        { id: "mp_SAB", label: "Mặt phẳng (SAB)", type: "plane3", render: "surface", origin: "derived", depends: ["S", "A", "B"] },
        {
          id: "kq_q", label: "Khoảng cách từ M đến (SAB)", notation: "d(M, (SAB))", type: "quantity", render: "readout",
          origin: "derived", producer: "measure.distance", depends: ["M", "mp_SAB"], value: "1",
          annotation: {
            kind: "distance", category: "result", role: "result", subject_ids: ["M", "mp_SAB"], anchor: "witness",
            witness: { from: "M", foot: ["1/2", "0", "1/2"], on: "mp_SAB", marker: { u: ["-1/2", "0", "1/2"], v: ["0", "1/2", "0"] } },
          },
        },
      ],
      events: [
        { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Đầu.", semantic_kind: "EXPLANATION" },
        { step_index: 1, action: "CREATE", object: "mp_SAB", depends: ["S", "A", "B"], explanation: "Mặt phẳng.", semantic_kind: "GEOMETRY_CONSTRUCTION" },
        { step_index: 2, action: "MEASURE", object: "kq_q", depends: ["M", "mp_SAB"], explanation: "Kết luận.", semantic_kind: "FINAL_RESULT" },
      ],
    } as unknown as Scene3D;
    const present = new Set(["A", "B", "S", "M", "mp_SAB", "kq_q"]);
    expect(projectionWitnessesAt(s, present, 1)).toEqual([]);
    const [w] = projectionWitnessesAt(s, present, 2);
    expect(w.id).toBe("perpendicular:kq_q");
    expect(w.vai).toBe("hinh_chieu");
    expect(w.from).toEqual([0.5, 0.5, 0.5]);
    expect(w.foot).toEqual([0.5, 0, 0.5]);
  });

  it("P2-5: nhãn số đo neo tại trung điểm đoạn nhân chứng dốc đứng tránh đè lên chính đoạn nét đứt MH khi có hộp cản dọc đoạn", () => {
    const tx = 200, ty = 150, fx = 200, fy = 230;
    const mx = (tx + fx) / 2, my = (ty + fy) / 2;
    const d = Math.hypot(fx - tx, fy - ty);
    const ux = ((fx - tx) / d) * 10, uy = ((fy - ty) / d) * 10;
    const chan = [
      { x: fx - 8, y: fy - 8, w: 16, h: 16 },
      { x: mx + ux - 2, y: my + uy - 2, w: 4, h: 4 },
      { x: mx - ux - 2, y: my - uy - 2, w: 4, h: 4 },
    ];
    const dat = placeAnnotationLabels(
      [{ id: "d_M_H", ax: mx, ay: my, w: 96, h: 22, priority: 12 }],
      chan,
      { w: 600, h: 400 },
    );
    const r = dat.get("d_M_H");
    expect(r).toBeDefined();
    // Hộp nhãn phải nằm lệch sang bên phải hoặc bên trái đoạn đứng x = 200, không cắt qua x = 200
    expect(r!.x >= 206 || r!.x + r!.w <= 194).toBe(true);
  });

  it("bài toán chứng minh đường thẳng vuông góc với mặt phẳng (BC ⊥ (SAB) tại B) chỉ sinh 1 ký hiệu góc vuông rõ ràng ở bước kết luận sau khi xác minh đủ 2 hướng gốc trong mặt phẳng", () => {
    const s: Scene3D = {
      free_objects: ["A", "B", "C", "D", "S"],
      objects: [
        P("A", ["0", "0", "0"]),
        P("B", ["4", "0", "0"]),
        P("C", ["4", "3", "0"]),
        P("D", ["0", "3", "0"]),
        P("S", ["0", "0", "4"]),
        {
          id: "sab", label: "Mặt phẳng (SAB)", notation: "(SAB)", type: "plane3", render: "surface",
          origin: "derived", producer: "plane_through", depends: ["S", "A", "B"],
          point: ["0", "0", "0"], normal: ["0", "-1", "0"],
        },
        {
          id: "bc", label: "Cạnh BC", notation: "BC", type: "segment3", render: "segment",
          origin: "derived", producer: "segment", depends: ["B", "C"],
          endpoints: [["4", "0", "0"], ["4", "3", "0"]],
        },
        {
          id: "kl", label: "BC ⊥ (SAB)", notation: "BC ⊥ (SAB)", render: "non_visual",
          origin: "derived", producer: "perpendicular_check", depends: ["bc", "sab"], value: "90°",
        } as never,
      ],
      events: [
        { step_index: 0, action: "INIT", object: null, depends: ["A", "B", "C", "D", "S"], explanation: "Đầu." },
        { step_index: 1, action: "CREATE", object: "sab", depends: ["S", "A", "B"], explanation: "Xét (SAB)." },
        { step_index: 2, action: "CREATE", object: "bc", depends: ["B", "C"], explanation: "Xét BC." },
        { step_index: 3, action: "MEASURE", object: "kl", depends: ["bc", "sab"], explanation: "Kết luận BC ⊥ (SAB)." },
      ],
    } as unknown as Scene3D;
    const presentStep1 = new Set(["A", "B", "C", "D", "S", "sab"]);
    const presentStep2 = new Set(["A", "B", "C", "D", "S", "sab", "bc"]);
    const presentStep3 = new Set(["A", "B", "C", "D", "S", "sab", "bc", "kl"]);
    // Bước 1 (chưa dựng BC) và Bước 2 (mới dựng BC, chưa tới bước kết luận BC ⊥ (SAB)): chưa sinh ký hiệu góc vuông
    expect(projectionWitnessesAt(s, presentStep1, 1)).toEqual([]);
    expect(projectionWitnessesAt(s, presentStep2, 2)).toEqual([]);
    // Bước 3 (đã có kết luận chứng nhận kl): sinh đúng 1 ký hiệu góc vuông rõ ràng tại B, không chồng 2 dấu lên nhau
    const ws = projectionWitnessesAt(s, presentStep3, 3);
    expect(ws).toHaveLength(1);
    const [w] = ws;
    expect(w.id).toBe("perpendicular:bc");
    expect(w.foot).toEqual([4, 0, 0]);
    const dotUV = w.u[0] * w.v[0] + w.u[1] * w.v[1] + w.u[2] * w.v[2];
    expect(Math.abs(dotUV)).toBeLessThan(1e-9);
    expect(Math.abs(w.u[1])).toBeLessThan(1e-9);
    expect(w.v[1]).toBeGreaterThan(0);
  });

  it("không dùng phép chiếu đại số để giả tạo hướng vuông góc và không phát sinh dấu góc vuông giả cho đường nằm trong mặt phẳng, đường nghiêng, quan hệ chưa chứng nhận hoặc hình suy biến", () => {
    // 1. Phản ví dụ chiếu Gram-Schmidt: điểm S_lech = (0, 2, 4) khiến BS_lech = (-4, 2, 4) KHÔNG vuông góc với BC = (0, 3, 0).
    // Nếu dùng phép chiếu lên mặt phẳng vuông góc với BC sẽ tự tạo hướng (-4, 0, 4) và sinh dấu góc vuông giả.
    const canhLech: Scene3D = {
      free_objects: ["A", "B", "C", "S_lech"],
      objects: [
        P("A", ["0", "0", "0"]),
        P("B", ["4", "0", "0"]),
        P("C", ["4", "3", "0"]),
        P("S_lech", ["0", "2", "4"]),
        {
          id: "sab", label: "(SAB)", type: "plane3", render: "surface",
          origin: "derived", producer: "plane_through", depends: ["S_lech", "A", "B"],
          point: ["0", "0", "0"], normal: ["0", "-1", "0"],
        },
        {
          id: "bc", label: "BC", type: "line3", render: "line",
          origin: "derived", producer: "construct_line", depends: ["B", "C"],
          point: ["4", "0", "0"], direction: ["0", "3", "0"],
        },
        {
          id: "kl", label: "cos²(BC, (SAB))", type: "quantity", render: "readout",
          origin: "derived", producer: "measure.angle_cos_sq", depends: ["bc", "sab"], value: "0",
        },
      ],
      events: [
        { step_index: 0, action: "MEASURE", object: "kl", depends: ["bc", "sab"], explanation: "Kết luận." },
      ],
    } as unknown as Scene3D;
    expect(projectionWitnessesAt(canhLech, new Set(["A", "B", "C", "S_lech", "sab", "bc", "kl"]), 0)).toEqual([]);

    // 2. Đường nằm trong mặt phẳng (AB nằm trong (SAB)) và đường nghiêng (SC không vuông góc với (SAB)): không sinh dấu góc vuông
    const canhNghieng: Scene3D = {
      free_objects: ["A", "B", "C", "S"],
      objects: [
        P("A", ["0", "0", "0"]),
        P("B", ["2", "0", "0"]),
        P("C", ["2", "2", "0"]),
        P("S", ["0", "0", "4"]),
        {
          id: "sab", label: "(SAB)", type: "plane3", render: "surface",
          origin: "derived", producer: "construct_plane", depends: ["A", "B", "S"],
          point: ["0", "0", "4"], normal: ["0", "-8", "0"],
        },
        {
          id: "ab", label: "AB", type: "line3", render: "line",
          origin: "derived", producer: "construct_line", depends: ["A", "B"],
          point: ["0", "0", "0"], direction: ["2", "0", "0"],
        },
        {
          id: "sc", label: "SC", type: "line3", render: "line",
          origin: "derived", producer: "construct_line", depends: ["S", "C"],
          point: ["0", "0", "4"], direction: ["2", "2", "-4"],
        },
        {
          id: "goc_sc", label: "cos²(SC, (SAB))", type: "quantity", render: "readout",
          origin: "derived", producer: "measure.angle_cos_sq", depends: ["sc", "sab"], value: "1/6",
        },
      ],
      events: [
        { step_index: 0, action: "MEASURE", object: "goc_sc", depends: ["sc", "sab"], explanation: "Góc." },
      ],
    } as unknown as Scene3D;
    expect(projectionWitnessesAt(canhNghieng, new Set(["A", "B", "C", "S", "sab", "ab", "sc", "goc_sc"]), 0)).toEqual([]);

    // 3. Quan hệ chưa được chứng nhận (BC ⊥ (SAB) về tọa độ nhưng bài toán không có kết luận/chứng chỉ vuông góc giữa BC và (SAB))
    const canhChuaChungNhan: Scene3D = {
      free_objects: ["A", "B", "C", "S"],
      objects: [
        P("A", ["0", "0", "0"]),
        P("B", ["2", "0", "0"]),
        P("C", ["2", "2", "0"]),
        P("S", ["0", "0", "4"]),
        {
          id: "sab", label: "(SAB)", type: "plane3", render: "surface",
          origin: "derived", producer: "construct_plane", depends: ["A", "B", "S"],
          point: ["0", "0", "4"], normal: ["0", "-8", "0"],
        },
        {
          id: "bc", label: "BC", type: "line3", render: "line",
          origin: "derived", producer: "construct_line", depends: ["B", "C"],
          point: ["2", "0", "0"], direction: ["0", "2", "0"],
        },
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "bc", depends: ["B", "C"], explanation: "Dựng BC." },
      ],
    } as unknown as Scene3D;
    expect(projectionWitnessesAt(canhChuaChungNhan, new Set(["A", "B", "C", "S", "sab", "bc"]), 0)).toEqual([]);

    // 4. Hình học suy biến: 3 điểm xác định mặt phẳng thẳng hàng (A, B, M cùng nằm trên trục Ox)
    const canhSuyBien: Scene3D = {
      free_objects: ["A", "B", "M", "C"],
      objects: [
        P("A", ["0", "0", "0"]),
        P("B", ["2", "0", "0"]),
        P("M", ["1", "0", "0"]),
        P("C", ["2", "2", "0"]),
        {
          id: "sab_suy_bien", label: "(ABM)", type: "plane3", render: "surface",
          origin: "derived", producer: "construct_plane", depends: ["A", "B", "M"],
          point: ["0", "0", "0"], normal: ["0", "-1", "0"],
        },
        {
          id: "bc", label: "BC", type: "line3", render: "line",
          origin: "derived", producer: "construct_line", depends: ["B", "C"],
          point: ["2", "0", "0"], direction: ["0", "2", "0"],
        },
        {
          id: "kl", label: "BC ⊥ (ABM)", type: "quantity", render: "readout",
          origin: "derived", producer: "perpendicular_check", depends: ["bc", "sab_suy_bien"], value: "90°",
        },
      ],
      events: [
        { step_index: 0, action: "MEASURE", object: "kl", depends: ["bc", "sab_suy_bien"], explanation: "Kết luận." },
      ],
    } as unknown as Scene3D;
    expect(projectionWitnessesAt(canhSuyBien, new Set(["A", "B", "M", "C", "sab_suy_bien", "bc", "kl"]), 0)).toEqual([]);
  });
});
