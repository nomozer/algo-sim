import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { khungNhinQuanhTam } from "./scene3d-camera";
import { diemHuuHan, type Scene3D } from "./scene3d-model";
import { datKhungNhin, tinhTamXoayOnDinh } from "./scene3d-view";

const inCircum = JSON.parse(
  readFileSync(new URL("./scene3d-inscribed-circumscribed-fixtures.json", import.meta.url), "utf8"),
);
const correctedRows = JSON.parse(
  readFileSync(
    new URL(
      "../../../../../docs/evaluation/geometry/runs/geometric-visual-correctness-framing/demos/audit_scenes.json",
      import.meta.url,
    ),
    "utf8",
  ),
);

function sampleScene(id: string): Scene3D {
  const found = GEOMETRY_SAMPLES.find((s) => s.id === id);
  const scene3d = (found?.envelope as { scene3d?: Scene3D } | undefined)?.scene3d;
  if (!scene3d) throw new Error(`Missing sample ${id}`);
  return scene3d;
}

function makeControlsStub(cam: THREE.PerspectiveCamera): OrbitControls {
  const docStub = { addEventListener() {}, removeEventListener() {} };
  const domStub = {
    style: {},
    ownerDocument: docStub,
    addEventListener() {},
    removeEventListener() {},
    getRootNode() {
      return docStub;
    },
  } as unknown as HTMLElement;
  return new OrbitControls(cam, domStub);
}

describe("Scene3D camera, orbit pivot & zoom reliability", () => {
  it("anchors S.ABCD orbit pivot to primary solid geometry (never P=[1,1,2] or section centroid) and stays invariant across S.ABCD problems", () => {
    const chop = sampleScene("thiet-dien-chop");
    const res = tinhTamXoayOnDinh(chop.objects);
    expect(res).not.toBeNull();
    // S.ABCD has base [0,2]x[0,2]x{0} and apex S=(0,0,4): G_vol=(0.75,0.75,1), C_aabb=(1,1,2) => pivot=(0.875,0.875,1.5)
    expect(res!.tamXoay[0]).toBeCloseTo(0.875, 6);
    expect(res!.tamXoay[1]).toBeCloseTo(0.875, 6);
    expect(res!.tamXoay[2]).toBeCloseTo(1.5, 6);

    const distToP = Math.hypot(res!.tamXoay[0] - 1, res!.tamXoay[1] - 1, res!.tamXoay[2] - 2);
    expect(distToP).toBeGreaterThan(0.5);

    const distToSectionCentroid = Math.hypot(res!.tamXoay[0] - 0.5, res!.tamXoay[1] - 0.5, res!.tamXoay[2] - 2);
    expect(distToSectionCentroid).toBeGreaterThan(0.7);

    // Every sample sharing the same primary solid S.ABCD produces the exact same canonical pivot
    for (const siblingId of ["mat-cheo-sac", "vuong-goc-chop", "mp-vuong-goc-duong", "the-tich-chop"]) {
      const sib = tinhTamXoayOnDinh(sampleScene(siblingId).objects)!;
      expect(sib.tamXoay[0]).toBeCloseTo(res!.tamXoay[0], 9);
      expect(sib.tamXoay[1]).toBeCloseTo(res!.tamXoay[1], 9);
      expect(sib.tamXoay[2]).toBeCloseTo(res!.tamXoay[2], 9);
    }
  });

  it("keeps symmetric pyramids, spheres, cylinders, and cones strictly on their central symmetry axes despite off-center auxiliary/section points", () => {
    const insphereScene: Scene3D = inCircum.insphere_square_pyramid.scene3d;
    const baseCirScene: Scene3D = inCircum.base_circles_square_pyramid.scene3d;

    const insPivot = tinhTamXoayOnDinh(insphereScene.objects)!;
    expect(insPivot.tamXoay[0]).toBeCloseTo(0, 9);
    expect(insPivot.tamXoay[1]).toBeCloseTo(0, 9);

    const baseCirPivot = tinhTamXoayOnDinh(baseCirScene.objects)!;
    expect(baseCirPivot.tamXoay[0]).toBeCloseTo(0, 9);
    expect(baseCirPivot.tamXoay[1]).toBeCloseTo(0, 9);

    const spherePivot = tinhTamXoayOnDinh(sampleScene("cau-cat-mat-phang").objects)!;
    expect(spherePivot.tamXoay).toEqual([0, 0, 0]);
    expect(spherePivot.banKinhKhoi).toBeCloseTo(5, 5);

    const cylPivot = tinhTamXoayOnDinh(sampleScene("tru-thiet-dien-tron").objects)!;
    expect(cylPivot.tamXoay[0]).toBeCloseTo(0, 9);
    expect(cylPivot.tamXoay[1]).toBeCloseTo(0, 9);
    expect(cylPivot.tamXoay[2]).toBeCloseTo(2, 9);

    const conePivot = tinhTamXoayOnDinh(sampleScene("non-thiet-dien-truc").objects)!;
    expect(conePivot.tamXoay[0]).toBeCloseTo(0, 9);
    expect(conePivot.tamXoay[1]).toBeCloseTo(0, 9);
    expect(conePivot.tamXoay[2]).toBeCloseTo(1.5, 9);
  });

  it("computes combined bounds for disjoint multi-solid compositions, excludes interior sub-solids, and falls back to finite-only geometry when no solid exists", () => {
    const multiRow = correctedRows.find((r: { id: string }) => r.id === "family07_multi_solid_composition");
    const upperSolid = multiRow.scene.objects.find((o: { id: string }) => o.id === "khoi_S_ABC");
    // In family07, D1=(0,0,1) lies inside outer S.ABC (S=(0,0,3)), so enclosed D1.ABC must NOT pull S.ABC's pivot down
    const onlyUpper = tinhTamXoayOnDinh([upperSolid])!;
    expect(tinhTamXoayOnDinh(multiRow.scene.objects)!.tamXoay).toEqual(onlyUpper.tamXoay);

    // True disjoint/adjacent multi-solid bipyramid: S=(0,0,3) above ABC and S2=(0,0,-2) below ABC
    const lowerSolid: Scene3D["objects"][number] = {
      ...upperSolid,
      id: "khoi_S2_ABC",
      vertices: [["0", "0", "-2"], ["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"]],
    };
    const onlyLower = tinhTamXoayOnDinh([lowerSolid])!;
    const biPyramidPivot = tinhTamXoayOnDinh([upperSolid, lowerSolid])!;
    expect(biPyramidPivot.diemKhoiChinh.length).toBe(onlyUpper.diemKhoiChinh.length + onlyLower.diemKhoiChinh.length);
    expect(biPyramidPivot.banKinhKhoi).toBeGreaterThan(onlyUpper.banKinhKhoi);
    expect(biPyramidPivot.banKinhKhoi).toBeGreaterThan(onlyLower.banKinhKhoi);
    expect(biPyramidPivot.tamXoay[2]).toBeGreaterThan(onlyLower.tamXoay[2]);
    expect(biPyramidPivot.tamXoay[2]).toBeLessThan(onlyUpper.tamXoay[2]);

    // Sub-pyramid inside outer pyramid (family04) must NOT pull pivot toward the upper sub-pyramid
    const subPyrRow = correctedRows.find((r: { id: string }) => r.id === "family04_derived_sub_pyramid");
    const outerOnly = subPyrRow.scene.objects.filter((o: { id: string }) => o.id !== "khoi_S_MI1I2I3");
    expect(tinhTamXoayOnDinh(subPyrRow.scene.objects)!.tamXoay).toEqual(tinhTamXoayOnDinh(outerOnly)!.tamXoay);

    // Cone frustum upper sub-cone (family10) must NOT pull pivot off the main cone's canonical pivot
    const coneCutRow = correctedRows.find((r: { id: string }) => r.id === "family10_cone_frustum_cut");
    const mainConeOnly = coneCutRow.scene.objects.filter((o: { id: string }) => o.id !== "khoi_cone_upper");
    expect(tinhTamXoayOnDinh(coneCutRow.scene.objects)!.tamXoay).toEqual(tinhTamXoayOnDinh(mainConeOnly)!.tamXoay);

    // Circumsphere around tetrahedron OABC (I = [1,1,1]) centers cleanly on [1,1,1]
    const circumScene: Scene3D = JSON.parse(
      readFileSync(new URL("./scene3d-circumsphere-fixture.json", import.meta.url), "utf8"),
    );
    const circumPivot = tinhTamXoayOnDinh(circumScene.objects)!;
    expect(circumPivot.tamXoay[0]).toBeCloseTo(1, 9);
    expect(circumPivot.tamXoay[1]).toBeCloseTo(1, 9);
    expect(circumPivot.tamXoay[2]).toBeCloseTo(1, 9);

    // No-solid scene with finite points + infinite line3 + infinite plane3: infinite objects must never pull pivot
    const noSolidObjects: Scene3D["objects"] = [
      { id: "A", type: "point3", label: "A", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"] },
      { id: "B", type: "point3", label: "B", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["4", "0", "0"] },
      { id: "C", type: "point3", label: "C", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "4", "0"] },
      {
        id: "far_line",
        type: "line3",
        label: "d",
        render: "line",
        origin: "derived",
        producer: "line",
        depends: [],
        point: ["100", "100", "100"],
        direction: ["1", "0", "0"],
      },
      {
        id: "far_plane",
        type: "plane3",
        label: "(P)",
        render: "surface",
        origin: "derived",
        producer: "plane",
        depends: [],
        point: ["-200", "-200", "50"],
        normal: ["0", "0", "1"],
      },
    ];
    const fb = tinhTamXoayOnDinh(noSolidObjects)!;
    expect(fb.tamXoay[0]).toBeGreaterThan(1);
    expect(fb.tamXoay[0]).toBeLessThan(2.5);
    expect(fb.tamXoay[2]).toBeCloseTo(0, 9);
  });

  it("frames all finite points inside asymmetric safe NDC bounds via khungNhinQuanhTam without mutating nhinVao (orbit pivot)", () => {
    const chop = sampleScene("thiet-dien-chop");
    const pivot = tinhTamXoayOnDinh(chop.objects)!;
    const pts = diemHuuHan(chop.objects);
    const safe = { xMin: -0.68, xMax: 0.48, yMin: -0.52, yMax: 0.66 };
    const kn = khungNhinQuanhTam(pts, pivot.tamXoay, 50, 1080 / 854, [8, 5, 6], safe);
    expect(kn).not.toBeNull();
    // Orbit pivot must remain 100% locked — zero world-space drift
    expect(kn!.nhinVao).toEqual(pivot.tamXoay);

    const cam = new THREE.PerspectiveCamera(50, 1080 / 854, 0.1, 200);
    cam.up.set(0, 0, 1);
    cam.position.set(...kn!.viTri);
    cam.lookAt(...kn!.nhinVao);
    cam.updateMatrixWorld();

    for (const p of pts) {
      const ndc = new THREE.Vector3(...p).project(cam);
      expect(ndc.x).toBeGreaterThanOrEqual(safe.xMin - 1e-6);
      expect(ndc.x).toBeLessThanOrEqual(safe.xMax + 1e-6);
      expect(ndc.y).toBeGreaterThanOrEqual(safe.yMin - 1e-6);
      expect(ndc.y).toBeLessThanOrEqual(safe.yMax + 1e-6);
    }
  });

  it("scales zoom minDistance/maxDistance from solid bounding radius so mobile viewports can inspect details without piercing the solid", () => {
    const cam = new THREE.PerspectiveCamera(50, 390 / 414, 0.1, 200);
    cam.up.set(0, 0, 1);
    const controls = makeControlsStub(cam);

    // Narrow viewport where fitted distance is larger (dist = 10) for a solid of radius R = 2.79
    datKhungNhin(cam, controls, { viTri: [10.875, 0.875, 1.5], nhinVao: [0.875, 0.875, 1.5] }, { banKinhKhoi: 2.789 });
    // Must stay strictly outside the solid (minDistance > R) yet allow closer detail inspection than 0.42 * 10 = 4.2
    expect(controls.minDistance).toBeGreaterThan(2.789 * 1.04);
    expect(controls.minDistance).toBeLessThan(3.4);
    expect(controls.maxDistance).toBeGreaterThanOrEqual(28);
    expect(controls.target.toArray()).toEqual([0.875, 0.875, 1.5]);

    // Legacy 3-argument call keeps exact proportional bounds
    datKhungNhin(cam, controls, { viTri: [10, 0, 0], nhinVao: [0, 0, 0] });
    expect(controls.minDistance).toBeCloseTo(4.2, 5);
    expect(controls.maxDistance).toBeCloseTo(28, 5);
    controls.dispose();
  });
});
