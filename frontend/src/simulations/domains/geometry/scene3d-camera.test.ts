import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import * as THREE from "three";
import {
  chonHuongNhin, danhGiaGocNhin, datNguong, doLuoiGocNhin, hopBaoCuaDiem, huongLenHienThi, khungGocVuong,
  khungNhinSuPham, khungNhinVua, type KhungNhin,
} from "./scene3d-camera";
import { cauTrucGocNhin, type Scene3D } from "./scene3d-model";

/**
 * GÓC NHÌN SƯ PHẠM trên sáu family đo (w10).
 *
 * Cảnh lấy nguyên từ fixture đã đóng băng của lượt cross-family — toạ độ hình
 * học của w10 không đổi, chỉ lớp trình bày đổi. Kích thước khung là khung vẽ
 * THẬT mà trình duyệt đo ở w09: desktop 1318×464, mobile 340×418, fov 50°.
 *
 * Ngưỡng điểm ảnh gắn với NHÃN ĐIỂM (`.geo3d-label`: chữ 13px × 1.2 + đệm 2px
 * ≈ 18px cao): hai đỉnh cách nhau ít hơn hai nhãn thì nhãn chồng nhau; một đỉnh
 * cách cạnh khác ít hơn một nhãn thì nhãn nằm lên cạnh.
 */
const FIXTURES = fileURLToPath(new URL(
  "../../../../../docs/evaluation/geometry/runs/"
  + "20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/inputs/fixtures/",
  import.meta.url));
const FAMILIES = ["triangular_pyramid", "triangular_prism", "rectangular_pyramid",
  "cuboid", "cube", "cross_section"] as const;
const KHUNG = { desktop: [1318, 464], mobile: [340, 418] } as const;
const FOV = 50;
const NHAN_PX = 18;

const canh = (f: string): Scene3D =>
  JSON.parse(readFileSync(`${FIXTURES}${f}_positive.json`, "utf8")).envelope.scene3d;

/** Chiếu bằng CHÍNH camera three.js mà renderer dùng (Z-up, lookAt). */
function doDiemAnh(kn: KhungNhin, w: number, h: number, f: string) {
  const { diem, canh: ds } = cauTrucGocNhin(canh(f).objects);
  const cam = new THREE.PerspectiveCamera(FOV, w / h, 0.1, 1000);
  cam.up.set(0, 0, 1);
  cam.position.set(...kn.viTri);
  cam.lookAt(...kn.nhinVao);
  cam.updateMatrixWorld();
  const px = diem.map((p) => {
    const v = new THREE.Vector3(...p).project(cam);
    return [(v.x + 1) / 2 * w, (1 - v.y) / 2 * h];
  });
  const xs = px.map((p) => p[0]);
  const ys = px.map((p) => p[1]);
  const lap = Math.max((Math.max(...xs) - Math.min(...xs)) / w, (Math.max(...ys) - Math.min(...ys)) / h);
  let dinh = Infinity;
  for (let i = 0; i < px.length; i++) {
    for (let j = i + 1; j < px.length; j++) {
      dinh = Math.min(dinh, Math.hypot(px[i][0] - px[j][0], px[i][1] - px[j][1]));
    }
  }
  const tren3 = (i: number, a: number, b: number) => {
    const A = new THREE.Vector3(...diem[a]);
    const B = new THREE.Vector3(...diem[b]);
    return new THREE.Line3(A, B).closestPointToPoint(new THREE.Vector3(...diem[i]), true, new THREE.Vector3())
      .distanceTo(new THREE.Vector3(...diem[i])) < 1e-6;
  };
  let dinhCanh = Infinity;
  for (let i = 0; i < px.length; i++) {
    for (const [a, b] of ds) {
      if (a === i || b === i || tren3(i, a, b)) continue;
      const l = new THREE.Line3(new THREE.Vector3(px[a][0], px[a][1], 0), new THREE.Vector3(px[b][0], px[b][1], 0));
      const p = new THREE.Vector3(px[i][0], px[i][1], 0);
      dinhCanh = Math.min(dinhCanh, l.closestPointToPoint(p, true, new THREE.Vector3()).distanceTo(p));
    }
  }
  const trongKhung = px.every(([x, y]) => x >= 0 && x <= w && y >= 0 && y <= h);
  return { lap, dinh, dinhCanh, trongKhung };
}

describe("góc nhìn sư phạm — sáu family", () => {
  it("cấu trúc cảnh: đỉnh khử trùng, cạnh và mặt lấy từ topology", () => {
    const s = cauTrucGocNhin(canh("rectangular_pyramid").objects);
    expect([s.diem.length, s.canh.length, s.mat.length]).toEqual([5, 8, 5]);
    const t = cauTrucGocNhin(canh("cross_section").objects);
    // 5 đỉnh chóp + 4 đỉnh thiết diện; tứ giác thiết diện là một mặt nữa
    expect(t.diem.length).toBe(9);
    expect(t.mat.length).toBe(6);
  });

  it.each(FAMILIES)("%s: hướng chọn đạt đủ ngưỡng", (f) => {
    const { diem, canh: ds, mat } = cauTrucGocNhin(canh(f).objects);
    const { tran } = doLuoiGocNhin(diem, ds, mat);
    expect(datNguong(danhGiaGocNhin(diem, ds, mat, chonHuongNhin(diem, ds, mat)), tran)).toBe(true);
  });

  it.each(FAMILIES.flatMap((f) => (["desktop", "mobile"] as const).map((k) => [f, k] as const)))(
    "%s @ %s: hình lấp 55–80% khung, nhãn không chồng nhãn, không nằm lên cạnh",
    (f, k) => {
      const [w, h] = KHUNG[k];
      const { diem, canh: ds, mat } = cauTrucGocNhin(canh(f).objects);
      const r = doDiemAnh(khungNhinSuPham(diem, ds, mat, FOV, w / h)!, w, h, f);
      expect(r.trongKhung).toBe(true);
      expect(r.lap).toBeGreaterThanOrEqual(0.55);
      expect(r.lap).toBeLessThanOrEqual(0.8);
      expect(r.dinh).toBeGreaterThanOrEqual(2 * NHAN_PX);
      expect(r.dinhCanh).toBeGreaterThanOrEqual(NHAN_PX);
    },
  );

  /* Hai khuyết tật của ảnh w09 mà bộ chọn mới phải sửa — khoá để không quay lại. */
  it("khung cũ (mặt cầu bao, hướng cố định): hình chóp chỉ choán < 55% khung mobile", () => {
    const { diem } = cauTrucGocNhin(canh("rectangular_pyramid").objects);
    const [w, h] = KHUNG.mobile;
    expect(doDiemAnh(khungNhinVua(hopBaoCuaDiem(diem), FOV, w / h)!, w, h, "rectangular_pyramid").lap)
      .toBeLessThan(0.55);
  });

  it("khung cũ: nhãn thiết diện nằm lên cạnh (< 1 nhãn) — khung mới thì không", () => {
    const { diem, canh: ds, mat } = cauTrucGocNhin(canh("cross_section").objects);
    const [w, h] = KHUNG.desktop;
    expect(doDiemAnh(khungNhinVua(hopBaoCuaDiem(diem), FOV, w / h)!, w, h, "cross_section").dinhCanh)
      .toBeLessThan(NHAN_PX);
    expect(doDiemAnh(khungNhinSuPham(diem, ds, mat, FOV, w / h)!, w, h, "cross_section").dinhCanh)
      .toBeGreaterThanOrEqual(NHAN_PX);
  });

  it("cảnh không có cạnh nào (chỉ điểm/khối cong) giữ hướng mặc định cũ", () => {
    const diem: [number, number, number][] = [[0, 0, 0], [0, 0, 4], [3, 0, 0]];
    const cu = khungNhinVua(hopBaoCuaDiem(diem), FOV, 2)!;
    const moi = khungNhinSuPham(diem, [], [], FOV, 2)!;
    const huong = (k: KhungNhin) => new THREE.Vector3(...k.viTri).sub(new THREE.Vector3(...k.nhinVao)).normalize();
    expect(huong(moi).angleTo(huong(cu))).toBeLessThan(1e-9);
  });
});

describe("hướng lên trình bày (regular-triangular-pyramid-w01)", () => {
  it("đáy NGANG (mọi họ trước) ⇒ null: không xoay, hình không đổi một điểm ảnh", () => {
    expect(huongLenHienThi([[0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 4, 0]], [2, 2, 3])).toBeNull();
    expect(huongLenHienThi([[0, 0, 0], [3, 0, 0], [0, 4, 0]], [0, 0, 5])).toBeNull();
  });

  it("đáy nghiêng x+y+z=3 ⇒ pháp tuyến đơn vị (1,1,1)/√3 quay về phía đỉnh, bất kể thứ tự đỉnh đáy", () => {
    const day: [number, number, number][] = [[3, 0, 0], [0, 3, 0], [0, 0, 3]];
    const k = 1 / Math.sqrt(3);
    for (const d of [day, [...day].reverse()]) {
      const n = huongLenHienThi(d, [2, 2, 2])!;
      n.forEach((x) => expect(x).toBeCloseTo(k, 12));
    }
    huongLenHienThi(day, [0, 0, 0])!.forEach((x) => expect(x).toBeCloseTo(-k, 12));
  });

  it("đáy suy biến ⇒ null", () => {
    expect(huongLenHienThi([[0, 0, 0], [1, 1, 1], [2, 2, 2]], [0, 0, 5])).toBeNull();
  });

  it("ký hiệu góc vuông: đoạn thẳng đứng ⇒ đúng x̂, ẑ, ŷ (ký hiệu cũ); đoạn nghiêng ⇒ khung trực chuẩn theo đoạn", () => {
    expect(khungGocVuong([2, 2, 0], [2, 2, 3])).toEqual({ e1: [1, 0, 0], d: [0, 0, 1], e2: [0, 1, 0] });
    const k = khungGocVuong([1, 1, 1], [2, 2, 2])!;
    const tich = (a: number[], b: number[]) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    for (const [a, b] of [[k.e1, k.d], [k.e1, k.e2], [k.d, k.e2]]) expect(tich(a, b)).toBeCloseTo(0, 12);
    for (const u of [k.e1, k.d, k.e2]) expect(tich(u, u)).toBeCloseTo(1, 12);
    expect(khungGocVuong([1, 1, 1], [1, 1, 1])).toBeNull();
  });
});
