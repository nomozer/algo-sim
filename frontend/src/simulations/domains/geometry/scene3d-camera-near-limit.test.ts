import { describe, expect, it } from "vitest";
import { khoangGanToiThieu, khoangTuaTheoHuong, tinhTamXoayTuKhoi, type Diem3 } from "./scene3d-camera";

/**
 * Near zoom limit follows the main solid's real surface along the view direction (support distance), not only its
 * bounding sphere: a curved surface IS its bounding sphere, so `1.08·R` put the camera against the sphere and pushed
 * the section circle out of frame (run axo-end-to-end-authority-scene3d-usability). Oracles by hand.
 */
const cube: Diem3[] = [[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]];
const cubeFaces = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]];
const ball = (r: number) => tinhTamXoayTuKhoi([{ loai: "curved_solid", curvedKind: "ball", anchor: [0, 0, 0], radius: r,
  apexOrTop: [0, 0, 0], pts: [[r, 0, 0], [-r, 0, 0], [0, r, 0], [0, -r, 0], [0, 0, r], [0, 0, -r]] }], [])!;
const cylinder = tinhTamXoayTuKhoi([{ loai: "curved_solid", curvedKind: "cylinder", anchor: [0, 0, -2], radius: 2,
  apexOrTop: [0, 0, 2], pts: [[2, 0, -2], [-2, 0, -2], [0, 2, -2], [0, -2, -2], [2, 0, 2], [-2, 0, 2], [0, 2, 2], [0, -2, 2]] }], [])!;
const cubeInfo = tinhTamXoayTuKhoi([{ loai: "solid", vertices: cube, faces: cubeFaces }], [])!;

describe("support distance of the main solid along the view direction", () => {
  it("is the radius for a ball in every direction", () => {
    for (const d of [[0, 0, 1], [1, 1, 1], [-3, 2, 0.5]] as Diem3[]) expect(khoangTuaTheoHuong(ball(5), d)).toBeCloseTo(5, 9);
  });
  it("is the face distance face-on and the half diagonal corner-on for a cube", () => {
    expect(khoangTuaTheoHuong(cubeInfo, [0, 0, 1])).toBeCloseTo(1, 9);
    expect(khoangTuaTheoHuong(cubeInfo, [1, 1, 1])).toBeCloseTo(Math.sqrt(3), 9);
  });
  it("uses the end disks of a cylinder: half height along the axis, rim plus offset obliquely", () => {
    expect(khoangTuaTheoHuong(cylinder, [0, 0, 1])).toBeCloseTo(2, 9);
    expect(khoangTuaTheoHuong(cylinder, [1, 0, 0])).toBeCloseTo(2, 9);
    // u = (1,0,1)/√2: top disk centre 2/√2 + rim 2·√(1 − 1/2) = 2√2
    expect(khoangTuaTheoHuong(cylinder, [1, 0, 1])).toBeCloseTo(2 * Math.SQRT2, 9);
  });
});

describe("near zoom limit", () => {
  it("keeps a ball's near surface at most half way to the orbit centre", () => {
    expect(khoangGanToiThieu(ball(5), [0, 0, 1], 16.9)).toBeCloseTo(10, 9);   // was 1.08·5 = 5.4
  });
  it("leaves polyhedral close-up practically unchanged face-on", () => {
    expect(khoangGanToiThieu(cubeInfo, [0, 0, 1], 5.81)).toBeCloseTo(2, 9);   // was 1.08·√3 ≈ 1.87
  });
  it("never removes close-up: capped at 0.8 of the fitted distance", () => {
    expect(khoangGanToiThieu(ball(5), [0, 0, 1], 8)).toBeCloseTo(6.4, 9);
  });
  it("keeps the old rule without an orbit centre", () => {
    expect(khoangGanToiThieu(null, [0, 0, 1], 10)).toBeCloseTo(4.2, 9);
  });
});
