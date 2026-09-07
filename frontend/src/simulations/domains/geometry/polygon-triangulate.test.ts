import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { chiaTamGiac, dienTichCoDau, type Diem3 } from "./polygon-triangulate";

/**
 * `NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION` §9 — phần lõm phải TRỐNG.
 *
 * Đáy lõm chuẩn của wave, đúng bộ toạ độ mà kernel dùng:
 *
 *     A(0,0,0) B(4,0,0) C(4,4,0) D(2,1,0) E(0,4,0)
 *
 * Diện tích thật `10`. Quạt tam giác từ đỉnh 0 phủ `14` — chênh `4`, đúng
 * bằng phần lõm bị lấp.
 */
const LOM: Diem3[] = [[0, 0, 0], [4, 0, 0], [4, 4, 0], [2, 1, 0], [0, 4, 0]];
const VUONG: Diem3[] = [[0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0]];

/** Diện tích 3D của một tam giác — nửa độ dài tích có hướng. */
function dienTich(a: Diem3, b: Diem3, c: Diem3): number {
  const u = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
  const v = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
  const n = [u[1] * v[2] - u[2] * v[1],
             u[2] * v[0] - u[0] * v[2],
             u[0] * v[1] - u[1] * v[0]];
  return Math.hypot(n[0], n[1], n[2]) / 2;
}

function tongDienTich(pts: Diem3[]): number {
  return chiaTamGiac(pts)
    .reduce((s, [a, b, c]) => s + dienTich(pts[a], pts[b], pts[c]), 0);
}

/** Quạt tam giác — đường CŨ, giữ lại để so. */
function quatCu(pts: Diem3[]): number {
  let s = 0;
  for (let i = 1; i < pts.length - 1; i += 1) s += dienTich(pts[0], pts[i], pts[i + 1]);
  return s;
}

describe("chia tam giác đa giác phẳng ĐƠN, kể cả LÕM", () => {
  it("mặt lõm: diện tích phủ đúng 10, không lấp phần lõm", () => {
    expect(tongDienTich(LOM)).toBeCloseTo(10, 9);
  });

  it("quạt CŨ phủ 14 — chênh đúng bằng phần lõm bị lấp", () => {
    // Ô này là BẰNG CHỨNG của lỗi, không phải một kỳ vọng. Nó giữ lại con số
    // để lần sau ai đó quay về quạt thì thấy ngay cái giá.
    expect(quatCu(LOM)).toBeCloseTo(14, 9);
    expect(quatCu(LOM) - tongDienTich(LOM)).toBeCloseTo(4, 9);
  });

  it("số tam giác đúng n−2", () => {
    expect(chiaTamGiac(LOM)).toHaveLength(3);
    expect(chiaTamGiac(VUONG)).toHaveLength(2);
  });

  it("mọi tam giác dùng CHỈ SỐ có thật — không sinh đỉnh mới", () => {
    for (const t of chiaTamGiac(LOM)) {
      for (const j of t) {
        expect(Number.isInteger(j)).toBe(true);
        expect(j).toBeGreaterThanOrEqual(0);
        expect(j).toBeLessThan(LOM.length);
      }
      expect(new Set(t).size).toBe(3);
    }
  });

  it("mặt LỒI: diện tích giữ nguyên, cùng số tam giác như quạt", () => {
    expect(tongDienTich(VUONG)).toBeCloseTo(4, 9);
    expect(quatCu(VUONG)).toBeCloseTo(4, 9);
  });

  it("bất biến với cyclic-shift của biên", () => {
    for (let k = 0; k < LOM.length; k += 1) {
      const xoay = [...LOM.slice(k), ...LOM.slice(0, k)];
      expect(tongDienTich(xoay)).toBeCloseTo(10, 9);
    }
  });

  it("bất biến với chiều duyệt biên", () => {
    expect(tongDienTich([...LOM].reverse())).toBeCloseTo(10, 9);
  });

  it("bất biến với tịnh tiến", () => {
    const doi = LOM.map(([x, y, z]) => [x + 7, y - 3, z + 11] as Diem3);
    expect(tongDienTich(doi)).toBeCloseTo(10, 9);
  });

  it("mặt KHÔNG nằm trong mặt phẳng Oxy vẫn đúng", () => {
    // Cùng đa giác, dựng đứng trong mặt phẳng x = 5.
    const dung = LOM.map(([x, y]) => [5, x, y] as Diem3);
    expect(tongDienTich(dung)).toBeCloseTo(10, 9);
  });

  it("tam giác trả về CHÍNH nó", () => {
    expect(chiaTamGiac([[0, 0, 0], [1, 0, 0], [0, 1, 0]])).toEqual([[0, 1, 2]]);
  });

  it("suy biến ⇒ KHÔNG vẽ gì, thay vì vẽ một thứ vô nghĩa", () => {
    expect(chiaTamGiac([[0, 0, 0], [1, 0, 0]])).toEqual([]);
    // Mọi đỉnh thẳng hàng.
    expect(chiaTamGiac([[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]])).toEqual([]);
  });

  it("đa giác TỰ CẮT (bow-tie) ⇒ từ chối, không đoán", () => {
    const noBuom: Diem3[] = [[0, 0, 0], [2, 2, 0], [2, 0, 0], [0, 2, 0]];
    expect(chiaTamGiac(noBuom)).toEqual([]);
  });

  it("shoelace có dấu: đổi chiều biên đổi dấu, không đổi độ lớn", () => {
    const xy = LOM.map(([x, y]) => [x, y] as [number, number]);
    const nguoc = [...xy].reverse();
    expect(dienTichCoDau(xy)).toBeCloseTo(-dienTichCoDau(nguoc), 9);
    expect(Math.abs(dienTichCoDau(xy))).toBeCloseTo(10, 9);
  });
});

describe("module THUẦN — không three, không toán hình học của kernel", () => {
  const src = readFileSync(join(__dirname, "polygon-triangulate.ts"), "utf8");

  it("KHÔNG nhập gì cả — không three, không model, không kernel", () => {
    // Cùng khuôn với `pick-target` và `scene3d-presentation`: guard biên ở
    // `scene3d.test.tsx` cho module này vào danh sách nguồn được phép, và cái
    // giá của quyền ấy là ô dưới đây.
    expect([...src.matchAll(/from ["']([^"']+)["']/g)].map((m) => m[1]))
      .toEqual([]);
    expect(src).not.toMatch(/\brequire\(/);
  });

  it("không tự QUYẾT hình: chỉ trả CHỈ SỐ, không dựng toạ độ mới", () => {
    // Kiểu trả về nói ra điều đó, và nó phải ở lại trong chữ ký hàm.
    expect(src).toContain("[number, number, number][]");
    // Không đọc `Scene3D`, không suy quan hệ hình học nào.
    expect(src).not.toMatch(/\b(Scene3D|SceneObject|intersect|Raycaster)\b/);
  });
});
