/**
 * W17 · §15.4 — SỐ ĐO TRÊN HÌNH: hợp đồng gắn đối tượng do backend sở hữu.
 *
 * Frontend chỉ đọc `annotation` (kind · category · subject_ids · anchor) mà backend phát cho
 * một đại lượng, và luật khả dụng của lớp lời giải (`solutionAt`). Nó không bao giờ suy chủ thể
 * từ tên biến (`AB_length`) và không tự tính giá trị.
 */
import { describe, expect, it } from "vitest";
import type { Scene3D } from "./scene3d-model";
import {
  annotationsAt, annotationAnchor, DEFAULT_ANNOTATION_TOGGLES, NEO_TOI_DA, placeAnnotationLabels,
} from "./scene3d-annotations";

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

describe("W17 · số đo trên hình (§15.4)", () => {
  it("mặc định BẬT cả Số đo và Kết quả (U-W17-1)", () => {
    expect(DEFAULT_ANNOTATION_TOGGLES).toEqual({ measurements: true, results: true });
  });

  it("chỉ đại lượng CÓ annotation của backend mới có nhãn — không suy từ tên biến", () => {
    const a = annotationsAt(canh(), CUOI, DEFAULT_ANNOTATION_TOGGLES, null);
    expect(ids(a)).toEqual(["AB_length", "dien_tich", "the_tich"]);
    expect(a.map((x) => x.id)).not.toContain("XY_length");
  });

  it("chữ nhãn = ký hiệu = giá trị của payload; đơn vị chỉ khi payload có", () => {
    const a = annotationsAt(canh(), CUOI, DEFAULT_ANNOTATION_TOGGLES, null);
    const chu = Object.fromEntries(a.map((x) => [x.id, x.text]));
    expect(chu).toEqual({ AB_length: "AB = 3", dien_tich: "S(ABC) = 6", the_tich: "V(ABCD) = 10" });
  });

  it("tắt Số đo ⇒ mất dữ kiện và số đo trung gian; tắt Kết quả ⇒ mất đáp số", () => {
    expect(ids(annotationsAt(canh(), CUOI, { measurements: false, results: true }, null))).toEqual(["the_tich"]);
    expect(ids(annotationsAt(canh(), CUOI, { measurements: true, results: false }, null)))
      .toEqual(["AB_length", "dien_tich"]);
    expect(annotationsAt(canh(), CUOI, { measurements: false, results: false }, null)).toEqual([]);
  });

  it("không lộ trước: tiến rồi lùi, nhãn chỉ có từ bước đại lượng khả dụng và chủ thể có mặt", () => {
    const theoBuoc = [0, 1, 2, 3, 4, 5].map((k) => ids(annotationsAt(canh(), k, DEFAULT_ANNOTATION_TOGGLES, null)));
    const lui = [5, 4, 3, 2, 1, 0].map((k) => ids(annotationsAt(canh(), k, DEFAULT_ANNOTATION_TOGGLES, null)));
    expect(theoBuoc.slice().reverse()).toEqual(lui);
    for (const [k, a] of theoBuoc.entries()) {
      if (k < 3) expect(a).not.toContain("dien_tich");
      if (k < 5) expect(a).not.toContain("the_tich");
    }
    expect(theoBuoc[5]).toContain("the_tich");
  });

  it("chọn chủ thể thì nhãn liên quan được ưu tiên", () => {
    const thuong = annotationsAt(canh(), CUOI, DEFAULT_ANNOTATION_TOGGLES, null);
    const chon = annotationsAt(canh(), CUOI, DEFAULT_ANNOTATION_TOGGLES, "day_ABC");
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
      (id) => annotationAnchor(s, annotationsAt(s, CUOI, DEFAULT_ANNOTATION_TOGGLES, null).find((x) => x.id === id)!));
    expect(ab).toEqual([1.5, 0, 0]);
    expect(dt).toEqual([1, 4 / 3, 0]);
    expect(v).toEqual([0.75, 1, 1.25]);
  });
});

/* §15.5 — luật HỘP NHÃN mà bộ đo trình duyệt kiểm: trong khung, không đè nhãn điểm/nút điều khiển,
 * điểm gần nhất của hộp cách điểm neo chiếu ≤ 24 px. Hàm thuần: vị trí px vào, hộp ra. */
describe("W17 · đặt nhãn số đo (§15.5)", () => {
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
