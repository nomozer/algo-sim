/**
 * W12 — dòng thời gian HÌNH HỌC tách khỏi dòng TÍNH TOÁN (review NEEDS_CHANGES).
 *
 * Review người: timeline trộn bước dựng hình với bước chỉ tính số/kết luận;
 * nhiều bước tăng chỉ số mà hình không đổi (slideshow lời giải). Test chạy
 * trên SÁU cảnh thật của run w11 (bất biến, đã commit).
 *
 * Kỳ vọng về SỐ BƯỚC DỰNG đọc từ một phép đếm ĐỘC LẬP (`buocDungDocLap`: chữ
 * ký hình của snapshot formation), không từ hàm đang được kiểm.
 */
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { renderToString } from "react-dom/server";
import type { Scene3D } from "./scene3d-model";
import {
  geometryAnchor,
  geometryStepCount,
  geometryTimeline,
  nextGeometryStep,
  objectsAt,
  prevGeometryStep,
  quantityChoices,
  solutionAt,
} from "./scene3d-model";
import { Scene3DPlayer } from "./scene3d-playback";
import { Scene3DExplorer } from "./Scene3DExplorer";
import { Scene3DWorkspace } from "./scene3d-view";

const FIXTURES = fileURLToPath(new URL(
  "../../../../../docs/evaluation/geometry/runs/w11-pedagogical-polish/inputs/fixtures/",
  import.meta.url));
const FAMILIES = ["triangular_pyramid", "triangular_prism", "rectangular_pyramid",
  "cuboid", "cube", "cross_section"] as const;
const canh = (f: string): Scene3D =>
  JSON.parse(readFileSync(`${FIXTURES}${f}_positive.json`, "utf8")).envelope.scene3d;

/** Chữ ký HÌNH của một snapshot formation — vật vẽ được + tiến độ thiết diện. */
function hinh(scene: Scene3D, k: number): string {
  const s = scene.formation!.steps[k];
  const ve = new Set(scene.objects.filter((o) => o.render !== "readout" && o.render !== "non_visual")
    .map((o) => o.id));
  return JSON.stringify([s.visible_ids.filter((id) => ve.has(id)).sort(),
    (s.geometry_progress ?? []).map((p) => [p.object_id, p.visible_edge_ids, p.fill_visible])]);
}

/** Số bước dựng, đếm độc lập: bước 0 + mỗi sự kiện DỰNG làm đổi hình. */
function buocDungDocLap(scene: Scene3D): number {
  return 1 + scene.events.slice(1).filter((e, i) =>
    e.semantic_kind === "GEOMETRY_CONSTRUCTION" && hinh(scene, i + 1) !== hinh(scene, i)).length;
}

describe("W12 · bước dựng CHỈ là bước hình học", () => {
  it.each(FAMILIES)("%s: phân hoạch liên tiếp, đủ, không chồng lấn", (f) => {
    const s = canh(f);
    const t = geometryTimeline(s);
    expect(t.length).toBe(geometryStepCount(s));
    expect(t.length).toBe(buocDungDocLap(s));
    expect(t[0].start).toBe(0);
    expect(t.at(-1)!.end).toBe(s.events.length - 1);
    t.forEach((g, i) => {
      expect(g.index).toBe(i);
      if (i > 0) expect(g.start).toBe(t[i - 1].end + 1);
      expect(g.anchor).toBe(g.end);
    });
  });

  it.each(FAMILIES)("%s: bước ĐO / KẾT LUẬN không mở bước dựng (0 khung tĩnh)", (f) => {
    const s = canh(f);
    const t = geometryTimeline(s);
    for (const g of t.slice(1)) {
      expect(s.events[g.start].semantic_kind).toBe("GEOMETRY_CONSTRUCTION");
    }
    // Mỗi bước dựng đổi HÌNH so với bước trước — không có khung tĩnh nào.
    const tinh = t.slice(1).filter((g, i) => hinh(s, g.anchor) === hinh(s, t[i].anchor));
    expect(tinh.map((g) => g.index)).toEqual([]);
    // Và dòng thời gian thật sự NGẮN HƠN dãy sự kiện khi có bước chỉ tính số.
    const chiTinh = s.events.filter((e) =>
      e.semantic_kind === "MEASUREMENT" || e.semantic_kind === "FINAL_RESULT").length;
    expect(t.length).toBeLessThanOrEqual(s.events.length - chiTinh);
  });

  it("kết luận nằm trong bước dựng cuối, không tạo bước riêng (chóp tam giác)", () => {
    const s = canh("triangular_pyramid");
    const t = geometryTimeline(s);
    const ketLuan = s.events.findIndex((e) => e.semantic_kind === "FINAL_RESULT");
    expect(ketLuan).toBeGreaterThan(0);
    expect(t.at(-1)!.results).toContain(ketLuan);
    expect(t.every((g) => g.start !== ketLuan)).toBe(true);
  });
});

describe("W12 · tua tiến/lùi và dừng ở bước hình học cuối", () => {
  it.each(FAMILIES)("%s: tới rồi lùi trả ĐÚNG snapshot của mỗi bước", (f) => {
    const s = canh(f);
    const t = geometryTimeline(s);
    let k = geometryAnchor(s, 0);
    expect(k).toBe(t[0].anchor);
    for (const g of t.slice(1)) {
      k = nextGeometryStep(s, k);
      expect(k).toBe(g.anchor);
      expect(objectsAt(s, k).map((o) => o.id).sort())
        .toEqual([...s.formation!.steps[g.anchor].visible_ids].sort());
    }
    expect(nextGeometryStep(s, k)).toBe(k); // bước cuối: đứng yên
    for (const g of [...t].reverse().slice(1)) {
      k = prevGeometryStep(s, k);
      expect(k).toBe(g.anchor);
    }
    expect(prevGeometryStep(s, k)).toBe(k);
  });

  it.each(FAMILIES)("%s: thanh bước của trình phát đếm bước DỰNG, không đếm bước tính", (f) => {
    const s = canh(f);
    const html = renderToString(<Scene3DPlayer scene={s} />);
    const max = Number(/type="range"[^>]*max="(\d+)"/.exec(html)?.[1]
      ?? /max="(\d+)"[^>]*type="range"/.exec(html)?.[1]);
    expect(max).toBe(buocDungDocLap(s) - 1);
  });

  it.each(FAMILIES)("%s: dòng Bước ở đáy xưởng nói số bước DỰNG", (f) => {
    const s = canh(f);
    const html = renderToString(<Scene3DExplorer scene={s} />);
    expect(html).toContain(`Bước 1/${buocDungDocLap(s)}`);
  });
});

describe("W12 · lớp lời giải giữ công thức và nguồn", () => {
  it("chóp tam giác ở bước cuối: dữ kiện, bước tính có nguồn số, kết quả có công thức", () => {
    const s = canh("triangular_pyramid");
    const lg = solutionAt(s, geometryAnchor(s, s.events.length - 1));
    expect(lg.givens.map((x) => x.id).sort()).toEqual(["AB_length", "AC_length", "SA_length"]);
    const dt = lg.steps.find((x) => x.id === "dien_tich_day_ABC")!;
    expect(dt.basis).toEqual(["AB_length", "AC_length"]);
    expect(lg.results.map((x) => x.id)).toEqual(["the_tich_khoi_chop"]);
    expect(lg.results[0].formula).toBe("V = 1/3 × S(ABC) × SA = 10");
    // Đáp số xuất hiện ĐÚNG một lần trong lớp lời giải.
    const moi = [...lg.givens, ...lg.steps, ...lg.results].map((x) => x.id);
    expect(moi.filter((id) => id === "the_tich_khoi_chop")).toHaveLength(1);
  });

  it.each(FAMILIES)("%s: mọi công thức của cảnh đều còn trong lời giải ở bước cuối", (f) => {
    const s = canh(f);
    const lg = solutionAt(s, s.events.length - 1);
    const coCongThuc = [...lg.steps, ...lg.results].filter((x) => x.formula).map((x) => x.id);
    const trongCanh = s.objects.filter((o) => o.formula?.references?.length).map((o) => o.id);
    for (const id of trongCanh) expect(coCongThuc).toContain(id);
  });

  it("lời giải ĐỒNG BỘ với bước dựng: bước đầu chưa có kết quả", () => {
    const s = canh("triangular_pyramid");
    expect(solutionAt(s, geometryAnchor(s, 0)).results).toEqual([]);
  });

  it("W05 · E: không còn bảng lời giải dưới thanh bước — đáp số MỘT mục ở «Đại lượng», công thức ở ô soi", () => {
    // W18 §16.6 thu gọn lời giải; W05 gỡ hẳn thẻ ấy: nó lặp tập `quantityChoices` mà bảng «Đại lượng» liệt kê.
    const s = canh("triangular_pyramid");
    const html = renderToString(<Scene3DPlayer scene={s} initialStep={s.events.length - 1} />);
    expect(html).not.toContain("V = 1/3 × S(ABC) × SA = 10");
    expect(html).not.toContain("Các bước tính");
    const q = quantityChoices(s, geometryAnchor(s, s.events.length - 1));
    expect([...q.results, ...q.steps, ...q.givens].filter((id) => id === "the_tich_khoi_chop")).toHaveLength(1);
  });

  it("khung 3D không còn dải số đo nổi trên hình", () => {
    const s = canh("triangular_pyramid");
    const html = renderToString(<Scene3DWorkspace scene={s} step={s.events.length - 1} />);
    expect(html).not.toContain("geo3d-readout");
  });
});
