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

describe("W12 · khung 3D: mỗi màu một nghĩa", () => {
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

  it("điểm đề cho không vai trò là trung tính — xanh chỉ còn nghĩa 'đang xét'", () => {
    const m = gom(buildObject3D(DIEM, false)!).map((c) => (c as THREE.Mesh).material)
      .find((x) => x instanceof THREE.MeshStandardMaterial) as THREE.MeshStandardMaterial;
    expect(hsl(m.color).s).toBeLessThan(0.25);
  });
});
