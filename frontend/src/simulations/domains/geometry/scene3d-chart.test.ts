import { describe, expect, it } from "vitest";
import { maTranKhung, maTranKhung4, veKhongGian } from "./scene3d-chart";
import type { Scene3D } from "./scene3d-model";
import { toVec3 } from "./scene3d-model";

/** Khung "trục" của chóp tam giác đều cạnh đáy 6, chiều cao 4 (backend `exact-dimensions`): A=0, B=(6,0,0),
 *  C=(0,6,0), S=(2,2,4); metric khung G = [[1,½,0],[½,1,0],[0,0,1]]. */
const G = [["1", "1/2", "0"], ["1/2", "1", "0"], ["0", "0", "1"]];
const canh = (o: Partial<Scene3D> = {}): Scene3D => ({
  objects: [
    { id: "A", label: "A", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"] },
    { id: "B", label: "B", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["6", "0", "0"] },
    { id: "C", label: "C", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "6", "0"] },
    { id: "S", label: "S", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["2", "2", "4"] },
    { id: "mp", label: "(ABC)", type: "plane3", render: "surface", origin: "derived", producer: "construct_plane", depends: [],
      point: ["0", "0", "0"], normal: ["0", "0", "1"] },
  ],
  events: [], free_objects: [], ...o,
});
const d = (p: number[], q: number[]) => Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]);

describe("khung → không gian", () => {
  it("không metric ⇒ CHÍNH cảnh ấy (mọi họ khác không đổi một byte)", () => {
    const c = canh();
    expect(veKhongGian(c)).toBe(c);
    expect(maTranKhung(c)).toBeNull();
    expect(maTranKhung4(c)).toBeNull();
  });

  it("Tᵀ·T = G và hình thế giới có đúng các độ dài của đề", () => {
    const w = veKhongGian(canh({ chart_metric: G }));
    const P = Object.fromEntries(w.objects.filter((o) => o.xyz).map((o) => [o.id, toVec3(o.xyz!)]));
    for (const [p, q] of [["A", "B"], ["B", "C"], ["C", "A"]]) expect(d(P[p], P[q])).toBeCloseTo(6, 6);
    for (const p of ["A", "B", "C"]) expect(d(P.S, P[p])).toBeCloseTo(Math.sqrt(28), 6);
  });

  it("pháp tuyến đi theo T⁻ᵀ: vẫn vuông góc với đáy trong không gian", () => {
    const w = veKhongGian(canh({ chart_metric: G }));
    const P = Object.fromEntries(w.objects.filter((o) => o.xyz).map((o) => [o.id, toVec3(o.xyz!)]));
    const n = toVec3(w.objects.find((o) => o.id === "mp")!.normal!);
    for (const q of ["B", "C"]) {
      const u = [P[q][0] - P.A[0], P[q][1] - P.A[1], P[q][2] - P.A[2]];
      expect(n[0] * u[0] + n[1] * u[1] + n[2] * u[2]).toBeCloseTo(0, 6);
    }
  });

  it("FINDING-B1: biến đổi cả `perpendicular_witness` (chân H và hai phương ký hiệu góc vuông) sang không gian thế giới và lũy đẳng khi gọi lặp", () => {
    const c = canh({
      chart_metric: G,
      objects: [
        ...canh().objects,
        {
          id: "H", label: "H", type: "point3", render: "point_marker", origin: "derived",
          producer: "construct_point.project_onto", depends: ["S", "mp"],
          xyz: ["2", "2", "0"],
          perpendicular_witness: {
            from: "S", on: "mp",
            foot: ["2", "2", "0"],
            marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] },
          },
        },
      ],
    });
    const w = veKhongGian(c);
    const h = w.objects.find((o) => o.id === "H")!;
    const hXyz = toVec3(h.xyz!);
    const foot = toVec3(h.perpendicular_witness!.foot);
    expect(d(hXyz, foot)).toBeLessThan(1e-6);
    const u = toVec3(h.perpendicular_witness!.marker.u);
    const v = toVec3(h.perpendicular_witness!.marker.v);
    expect(Math.hypot(...u)).toBeCloseTo(1, 6);
    expect(Math.hypot(...v)).toBeCloseTo(1, 6);
    expect(u[0] * v[0] + u[1] * v[1] + u[2] * v[2]).toBeCloseTo(0, 6);
    // Gọi lặp `veKhongGian(veKhongGian(c))` không biến đổi lần hai
    const w2 = veKhongGian(w);
    expect(toVec3(w2.objects.find((o) => o.id === "H")!.xyz!)).toEqual(hXyz);
    expect(toVec3(w2.objects.find((o) => o.id === "H")!.perpendicular_witness!.foot)).toEqual(foot);
  });
});

