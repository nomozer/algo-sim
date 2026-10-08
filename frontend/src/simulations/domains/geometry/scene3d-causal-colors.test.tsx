/**
 * W12 — MÀU KHUNG 3D theo vai trò (review NEEDS_CHANGES, lý do 4).
 *
 * Trước W12: vật ĐANG CHỌN vẽ cam đậm, dữ kiện số trong chuỗi vẽ xanh, vật
 * vừa dựng cam, điểm đề cho xanh — cam đậm và xanh mỗi màu hai nghĩa. Test
 * này đo màu THẬT của vật liệu three.js mà renderer dựng, theo khoảng sắc độ
 * (không so hằng), nên nó không phụ thuộc bảng màu đang được kiểm.
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
/** Vật mang MÀU KIỂU riêng (hổ phách, xanh két, tím, đỏ) — không phải khối. */
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
/** Màu NÉT cạnh (visual owner) của khối. */
const mauCanh = (vai: Parameters<typeof buildObject3D>[1]) => {
  const mau = gom(buildObject3D(KHOI, vai)!)
    .filter((c) => (c as THREE.Line).isLine && c.parent?.userData?.visualOwnerId)
    .map((c) => ((c as THREE.Line).material as THREE.LineBasicMaterial).color.getHex());
  expect(new Set(mau).size).toBe(1);
  return hsl(new THREE.Color(mau[0]));
};
/** Màu NỀN (mặt tô trong suốt) của khối. */
const mauNen = (vai: Parameters<typeof buildObject3D>[1]) => {
  const m = gom(buildObject3D(KHOI, vai)!).map((c) => (c as THREE.Mesh).material)
    .find((x) => x instanceof THREE.MeshStandardMaterial && x.opacity < 1) as THREE.MeshStandardMaterial;
  return hsl(m.color);
};

describe("khung 3D: mỗi màu một nghĩa", () => {
  it("vật ĐANG CHỌN (đích causal) là xanh", () => {
    const c = mauCanh("dich");
    expect(c.h).toBeGreaterThan(200);
    expect(c.h).toBeLessThan(235);
  });

  it("dữ kiện SỐ trong chuỗi là cam đậm — không còn xanh", () => {
    const c = mauCanh("du_kien_so");
    expect(c.h).toBeLessThan(35);
    expect(c.s).toBeGreaterThan(0.5);
  });

  it("đại lượng trung gian là cam nhạt — sáng hơn dữ kiện số", () => {
    const tg = mauCanh("trung_gian");
    expect(tg.h).toBeGreaterThan(15);
    expect(tg.h).toBeLessThan(45);
    expect(tg.l).toBeGreaterThan(mauCanh("du_kien_so").l);
  });

  it("vật VỪA DỰNG khi phát là xanh 'đang xét' — không phải cam", () => {
    const c = mauCanh(true);
    expect(c.h).toBeGreaterThan(200);
    expect(c.h).toBeLessThan(235);
  });

  it("ngữ cảnh cấu trúc tô nền TRUNG TÍNH, nét giữ mực", () => {
    expect(mauNen("boi_canh").s).toBeLessThan(0.25);
  });

  it("ngữ cảnh cấu trúc: thiết diện, đường, đoạn, mặt phẳng, điểm dựng cũng TRUNG TÍNH", () => {
    // Chú giải causal hứa "Hình liên quan" = xám. Bản đầu W12 chỉ đổi NỀN, nét
    // giữ MÀU KIỂU: viền thiết diện ngữ cảnh còn hổ phách — đọc thành "đại
    // lượng trung gian" (sheet cross-section, e115eede).
    for (const o of CO_MAU_KIEU) {
      const mau = gom(buildObject3D(o, "boi_canh")!)
        .flatMap((c) => {
          const m = (c as THREE.Mesh).material;
          return Array.isArray(m) ? m : m ? [m] : [];
        })
        .filter((m) => (m as THREE.Material & { colorWrite?: boolean }).colorWrite !== false)
        .map((m) => hsl((m as THREE.MeshBasicMaterial).color));
      expect(mau.length, o.id).toBeGreaterThan(0);
      for (const c of mau) expect(c.s, o.id).toBeLessThan(0.25);
    }
  });

  it("điểm đề cho không vai trò là trung tính — xanh chỉ còn nghĩa 'đang xét'", () => {
    const m = gom(buildObject3D(DIEM, false)!).map((c) => (c as THREE.Mesh).material)
      .find((x) => x instanceof THREE.MeshStandardMaterial) as THREE.MeshStandardMaterial;
    expect(hsl(m.color).s).toBeLessThan(0.25);
  });
});
