/**
 * Hợp đồng bảo toàn màu ngữ nghĩa toán học trong khung 3D:
 *
 * Theo chính sách biểu diễn ngữ nghĩa thống nhất và HTML hình học tham chiếu:
 * - Mỗi đối tượng mang màu theo vai trò toán học của nó (cạnh khối #1E293B,
 *   thiết diện #C85A32, mặt phẳng #6D28D9, đường/quan hệ #0F766E, nội tiếp #D97706,
 *   ngoại tiếp #2563EB).
 * - Khi hover, chọn đối tượng, tô sáng theo bước hoặc làm bối cảnh nhân quả,
 *   họ màu ngữ nghĩa (hue) được bảo toàn tuyệt đối (|Δhue| < 2°); trạng thái nhấn
 *   mạnh thể hiện qua bề dày nét, điều biến độ sáng cùng họ màu và làm dịu độ đục.
 */
import { describe, expect, it } from "vitest";
import * as THREE from "three";
import type { SceneObject } from "./scene3d-model";
import { buildObject3D } from "./scene3d-view";

const KHOI: SceneObject = {
  id: "K", label: "Khối", type: "solid", render: "mesh",
  origin: "derived", producer: "construct_solid", depends: [],
  vertices: [["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"], ["0", "0", "2"]],
  vertex_ids: ["A", "B", "C", "S"],
  faces: [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]],
};
const DIEM: SceneObject = {
  id: "A", label: "A", type: "point3", render: "point_marker",
  origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"],
};
const CO_MAU_KIEU: SceneObject[] = [
  { id: "T", label: "Thiết diện", type: "section", render: "polygon", origin: "derived",
    producer: "section", depends: [], closed: true, surface_role: "SECTION_REGION",
    polygon: [["0", "0", "1"], ["1", "0", "1"], ["1", "1", "1"], ["0", "1", "1"]] },
  { id: "BD", label: "Đường thẳng BD", type: "line3", render: "line", origin: "derived",
    producer: "line_through", depends: [], point: ["0", "0", "0"], direction: ["1", "1", "0"] },
  { id: "SH", label: "SH", type: "segment3", render: "segment", origin: "derived",
    producer: "segment", depends: [], point_a: ["0", "0", "0"], point_b: ["0", "0", "2"] },
  { id: "alpha", label: "(α)", type: "plane", render: "surface", origin: "derived",
    producer: "plane", depends: [], point: ["0", "0", "1"], normal: ["0", "0", "1"] },
  { id: "M", label: "M", type: "point3", render: "point_marker", origin: "derived",
    producer: "midpoint", depends: [], xyz: ["1", "0", "0"] },
];

const gom = (o: THREE.Object3D) => {
  const ra: THREE.Object3D[] = [];
  o.traverse((c) => ra.push(c));
  return ra;
};
const hsl = (c: THREE.Color) => {
  const x = { h: 0, s: 0, l: 0 };
  c.getHSL(x, THREE.SRGBColorSpace);
  return { h: x.h * 360, s: x.s, l: x.l };
};
const hueDiff = (a: number, b: number) => {
  const d = Math.abs(a - b);
  return d > 180 ? 360 - d : d;
};
/** Màu NÉT cạnh thấy (visual owner) của khối. */
const mauCanh = (vai: Parameters<typeof buildObject3D>[1]) => {
  const mau = gom(buildObject3D(KHOI, vai)!)
    .filter((c) => (c as THREE.Line).isLine && c.parent?.userData?.visualOwnerId && !c.userData?.hidden)
    .map((c) => ((c as THREE.Line).material as THREE.LineBasicMaterial).color.getHex());
  expect(new Set(mau).size).toBe(1);
  return hsl(new THREE.Color(mau[0]));
};
/** Màu NỀN (mặt tô trong suốt) của khối. */
const mauNen = (vai: Parameters<typeof buildObject3D>[1]) => {
  const m = gom(buildObject3D(KHOI, vai)!).map((c) => (c as THREE.Mesh).material)
    .find((x) => x instanceof THREE.MeshBasicMaterial && x.colorWrite !== false && x.opacity > 0 && x.opacity < 1) as THREE.MeshBasicMaterial;
  return hsl(m.color);
};

describe("khung 3D: bảo toàn màu ngữ nghĩa toán học qua mọi trạng thái tương tác", () => {
  it("cạnh khối chính giữ họ màu mực đá phiến trung tính (#1E293B) khi chọn đích", () => {
    const c = mauCanh("dich");
    expect(c.h).toBeGreaterThan(200);
    expect(c.h).toBeLessThan(235);
    expect(hueDiff(c.h, mauCanh(false).h)).toBeLessThan(2);
  });

  it("cạnh khối trong chuỗi nhân quả (dữ kiện số, trung gian, mới dựng, hover) không bị nhuộm cam hay xanh ngọc", () => {
    const baseH = mauCanh(false).h;
    for (const state of ["du_kien_so", "trung_gian", true, "hover"] as const) {
      const c = mauCanh(state);
      expect(hueDiff(c.h, baseH)).toBeLessThan(2);
      expect(c.h).toBeGreaterThan(200);
      expect(c.h).toBeLessThan(235);
    }
  });

  it("ngữ cảnh cấu trúc tô nền trung tính, nét giữ mực", () => {
    expect(mauNen("boi_canh").s).toBeLessThan(0.25);
  });

  it("thiết diện, đường, đoạn, mặt phẳng và điểm dựng giữ nguyên họ màu ngữ nghĩa khi hover, chọn và làm bối cảnh", () => {
    for (const o of CO_MAU_KIEU) {
      const layMau = (state: Parameters<typeof buildObject3D>[1]) =>
        gom(buildObject3D(o, state)!)
          .flatMap((c) => {
            const m = (c as THREE.Mesh).material;
            return Array.isArray(m) ? m : m ? [m] : [];
          })
          .filter((m) => (m as THREE.Material & { colorWrite?: boolean }).colorWrite !== false)
          .map((m) => ({
            ...hsl((m as THREE.MeshBasicMaterial).color),
            opacity: (m as THREE.Material).opacity,
          }));

      const base = layMau(false);
      expect(base.length, o.id).toBeGreaterThan(0);
      for (const state of ["hover", "dich", true, "boi_canh"] as const) {
        const cur = layMau(state);
        expect(cur.length, `${o.id}:${String(state)}`).toBe(base.length);
        cur.forEach((item, idx) => {
          if (base[idx].s >= 0.05) {
            expect(hueDiff(item.h, base[idx].h), `${o.id}:${String(state)}`).toBeLessThan(2);
          }
        });
      }
      const ctx = layMau("boi_canh");
      expect(ctx.some((item, idx) => item.opacity <= base[idx].opacity), o.id).toBe(true);
    }
  });

  it("điểm đề cho là mực trung tính", () => {
    const m = gom(buildObject3D(DIEM, false)!).map((c) => (c as THREE.Mesh).material)
      .find((x) => x instanceof THREE.MeshStandardMaterial) as THREE.MeshStandardMaterial;
    expect(hsl(m.color).s).toBeLessThan(0.25);
  });
});
