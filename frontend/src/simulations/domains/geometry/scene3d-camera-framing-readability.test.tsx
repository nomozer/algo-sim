import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  chonHuongNhin,
  khungAnToanCanDoiTam,
  khungNhinQuanhTam,
  tiLeHinhChieu,
} from "./scene3d-camera";
import {
  diemHuuHan,
  diemNeoDuongThang,
  objectsAt,
  toNumber,
  type ExactVec3,
  type Scene3D,
  type SceneObject,
  type Vec3,
} from "./scene3d-model";
import {
  cauTrucSuPham,
  compactPlaneAnchorPoints,
  resolveLineDisplaySpan,
} from "./scene3d-semantic-policy";
import { laDiemPhuDungMatPhang } from "./scene3d-subentities";
import { datKhungNhin, tinhTamXoayOnDinh, tinhViTriNhanDiem } from "./scene3d-view";

const rawAdvanced = JSON.parse(
  readFileSync(new URL("../../../data/advanced-geometry-samples.json", import.meta.url), "utf8"),
) as { samples: Array<{ id: string; title: string; envelope: { scene3d: Scene3D } }> };

const ADVANCED_SAMPLES = rawAdvanced.samples;

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

function finiteFramingPointsOf(scene: Scene3D): Vec3[] {
  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const pts: Vec3[] = [];
  for (const o of scene.objects) {
    if (laDiemPhuDungMatPhang(scene, o, byId)) continue;
    for (const p of diemHuuHan([o])) pts.push(p);
  }
  return pts;
}

function densePrimarySurfacePoints(scene: Scene3D): Vec3[] {
  const pts: Vec3[] = [];
  const toV = (v: ExactVec3): Vec3 => [toNumber(v[0]), toNumber(v[1]), toNumber(v[2])];
  for (const o of scene.objects) {
    if (o.type === "solid" && o.vertices) {
      for (const v of o.vertices) pts.push(toV(v));
    } else if (o.type === "curved_solid" && o.anchor && o.radius_sq) {
      const c = toV(o.anchor);
      const r = Math.sqrt(Math.max(0, toNumber(o.radius_sq)));
      if (o.curved_kind === "ball") {
        for (let i = 0; i <= 16; i += 1) {
          const th = (i * Math.PI) / 16;
          for (let j = 0; j < 32; j += 1) {
            const ph = (j * 2 * Math.PI) / 32;
            pts.push([
              c[0] + r * Math.sin(th) * Math.cos(ph),
              c[1] + r * Math.sin(th) * Math.sin(ph),
              c[2] + r * Math.cos(th),
            ]);
          }
        }
      } else {
        const h = o.height_sq ? Math.sqrt(Math.max(0, toNumber(o.height_sq))) : 0;
        const top: Vec3 = o.apex_or_top ? toV(o.apex_or_top) : [c[0], c[1], c[2] + h];
        pts.push(top);
        const ax: Vec3 = [top[0] - c[0], top[1] - c[1], top[2] - c[2]];
        const al = Math.hypot(...ax) || 1;
        const u: Vec3 = [ax[0] / al, ax[1] / al, ax[2] / al];
        const ref: Vec3 = Math.abs(u[0]) < 0.9 ? [1, 0, 0] : [0, 1, 0];
        const e1Raw: Vec3 = [
          u[1] * ref[2] - u[2] * ref[1],
          u[2] * ref[0] - u[0] * ref[2],
          u[0] * ref[1] - u[1] * ref[0],
        ];
        const e1l = Math.hypot(...e1Raw) || 1;
        const e1: Vec3 = [e1Raw[0] / e1l, e1Raw[1] / e1l, e1Raw[2] / e1l];
        const e2: Vec3 = [
          u[1] * e1[2] - u[2] * e1[1],
          u[2] * e1[0] - u[0] * e1[2],
          u[0] * e1[1] - u[1] * e1[0],
        ];
        for (let j = 0; j < 32; j += 1) {
          const ph = (j * 2 * Math.PI) / 32;
          pts.push([
            c[0] + r * (Math.cos(ph) * e1[0] + Math.sin(ph) * e2[0]),
            c[1] + r * (Math.cos(ph) * e1[1] + Math.sin(ph) * e2[1]),
            c[2] + r * (Math.cos(ph) * e1[2] + Math.sin(ph) * e2[2]),
          ]);
        }
      }
    } else if (o.type === "section" || o.type === "polygon3") {
      for (const v of o.polygon ?? o.vertices ?? []) pts.push(toV(v));
    } else if (o.type === "point3" && o.xyz) {
      if (o.label !== "Điểm dựng phụ" && !(o.authoritative === false && o.semantic_role === "AUXILIARY_CONSTRUCTION")) {
        pts.push(toV(o.xyz));
      }
    }
  }
  return pts;
}

function buildDefaultFramedCamera(scene: Scene3D, w: number, h: number, uiDichDoc = 0.03) {
  const diem = finiteFramingPointsOf(scene);
  const infoTam = tinhTamXoayOnDinh(scene.objects);
  expect(infoTam).not.toBeNull();
  const ct = cauTrucSuPham(scene.objects);
  const huong: [number, number, number] = ct.canh.length > 0
    ? chonHuongNhin(ct.diem, ct.canh, ct.mat, ct.tuyChon)
    : [8, 5, 6];
  const tiLeCR = tiLeHinhChieu(diem, huong) ?? 1;
  const laKhungHep = w <= 680;
  let tiLeDoc = tiLeCR > 1.20 ? 0.60 : 0.62;
  if (w < 900) tiLeDoc = Math.min(tiLeDoc, laKhungHep ? 0.62 : 0.60);
  const tiLeNgang = laKhungHep ? 0.66 : 0.65;
  const canDoi = khungAnToanCanDoiTam(diem, infoTam!.tamXoay, 50, w / h, huong, {
    tiLeDoc,
    tiLeNgang,
    dichTamNgang: 0,
    dichTamDoc: uiDichDoc,
  });
  const kn = khungNhinQuanhTam(diem, infoTam!.tamXoay, 50, w / h, huong, canDoi.vungAnToanNdc);
  expect(kn).not.toBeNull();

  const cam = new THREE.PerspectiveCamera(50, w / h, 0.1, 200);
  cam.up.set(0, 0, 1);
  if (Math.abs(canDoi.lechOngKinhNgang) > 1e-4 || Math.abs(canDoi.lechOngKinhDoc) > 1e-4) {
    cam.setViewOffset(
      w,
      h,
      -canDoi.lechOngKinhNgang * (w * 0.5),
      canDoi.lechOngKinhDoc * (h * 0.5),
      w,
      h,
    );
  }
  cam.updateProjectionMatrix();
  const ctrl = makeControlsStub(cam);
  datKhungNhin(cam, ctrl, kn!, { banKinhKhoi: infoTam!.banKinhKhoi, tam: infoTam! });
  cam.updateMatrixWorld(true);
  return { cam, ctrl, kn: kn!, infoTam: infoTam!, canDoi, diem };
}

function measureProjectedSpan(cam: THREE.PerspectiveCamera, pts: readonly Vec3[]) {
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  let clipped = 0;
  const v = new THREE.Vector3();
  for (const p of pts) {
    v.set(p[0], p[1], p[2]).project(cam);
    if (!Number.isFinite(v.x) || !Number.isFinite(v.y) || !Number.isFinite(v.z) || v.z >= 1 || v.z < -1) {
      clipped += 1;
      continue;
    }
    if (Math.abs(v.x) > 0.98 || Math.abs(v.y) > 0.98) clipped += 1;
    if (v.x < minX) minX = v.x;
    if (v.x > maxX) maxX = v.x;
    if (v.y < minY) minY = v.y;
    if (v.y > maxY) maxY = v.y;
  }
  return {
    widthPct: ((maxX - minX) / 2) * 100,
    heightPct: ((maxY - minY) / 2) * 100,
    minX,
    maxX,
    minY,
    maxY,
    clipped,
  };
}

describe("Root-cause Scene3D camera framing & visual readability", () => {
  it("frames all 11 THPT advanced simulations at balanced default proportions (~55-65% height, <70% width/height) with zero clipping on desktop 1080x854", () => {
    expect(ADVANCED_SAMPLES).toHaveLength(11);
    for (const sample of ADVANCED_SAMPLES) {
      const scene = sample.envelope.scene3d;
      const { cam, ctrl, infoTam } = buildDefaultFramedCamera(scene, 1080, 854, 0.065);
      const primaryPts = densePrimarySurfacePoints(scene);
      const span = measureProjectedSpan(cam, primaryPts);

      expect(span.clipped, `${sample.id} clipped points`).toBe(0);
      expect(span.widthPct, `${sample.id} width <= 70%`).toBeLessThanOrEqual(69.5);
      expect(span.heightPct, `${sample.id} height <= 70%`).toBeLessThanOrEqual(69.5);
      // Every problem either hits 55-65% height or is horizontally constrained around 65% width (#06 wide prism)
      const dominantFill = Math.max(span.heightPct, span.widthPct);
      expect(dominantFill, `${sample.id} dominant fill >= 55%`).toBeGreaterThanOrEqual(55.0);
      expect(span.heightPct, `${sample.id} height >= 54.5%`).toBeGreaterThanOrEqual(54.5);

      // Orbit target strictly equals canonical pivot of primary solid(s)
      expect(ctrl.target.x).toBeCloseTo(infoTam.tamXoay[0], 9);
      expect(ctrl.target.y).toBeCloseTo(infoTam.tamXoay[1], 9);
      expect(ctrl.target.z).toBeCloseTo(infoTam.tamXoay[2], 9);
    }
  });

  it("prevents infinite line3 axes and auxiliary plane3 patches from inflating camera distance or skewering sphere poles", () => {
    const circum = ADVANCED_SAMPLES.find((s) => s.id === "chop-mat-cau-ngoai-tiep")!.envelope.scene3d;
    const withoutLinesAndPlanes: Scene3D = {
      ...circum,
      objects: circum.objects.filter((o) => o.type !== "line3" && o.type !== "plane3"),
    };
    const fullFit = buildDefaultFramedCamera(circum, 1080, 854);
    const strippedFit = buildDefaultFramedCamera(withoutLinesAndPlanes, 1080, 854);

    // Adding infinite line3 (`truc_day`) and auxiliary plane3 (`mp_trung_truc`) MUST NOT push camera further away
    const dFull = fullFit.cam.position.distanceTo(fullFit.ctrl.target);
    const dStripped = strippedFit.cam.position.distanceTo(strippedFit.ctrl.target);
    expect(dFull).toBeCloseTo(dStripped, 6);

    // `truc_day` through O(2,2,0) and I(2,2,2) must NOT latch onto synthetic sphere poles [2, 2, 2 ± sqrt(12)]
    const trucDay = circum.objects.find((o) => o.id === "truc_day")!;
    const anchors = diemNeoDuongThang(circum.objects, trucDay.id);
    const onAxis = anchors.filter((p) => Math.hypot(p[0] - 2, p[1] - 2) < 1e-4);
    const maxZOnAxis = Math.max(...onAxis.map((p) => p[2]));
    expect(maxZOnAxis).toBeLessThanOrEqual(2.001);

    const span = resolveLineDisplaySpan(circum, trucDay, circum.objects);
    expect(span.coreSegment).toBeDefined();
    expect(span.coreSegment![0][2]).toBeGreaterThanOrEqual(-0.01);
    expect(span.coreSegment![1][2]).toBeLessThanOrEqual(2.01);
  });

  it("bounds sphere tangent planes tightly around coplanar points without shrinking secant sphere-cut planes", () => {
    const tangentScene = ADVANCED_SAMPLES.find((s) => s.id === "mat-phang-tiep-xuc-mat-cau")!.envelope.scene3d;
    const tangentPlane = tangentScene.objects.find((o) => o.type === "plane3")!;
    const tangentAnchors = compactPlaneAnchorPoints(tangentScene, tangentPlane, tangentScene.objects);
    expect(tangentAnchors.length).toBe(4);
    const maxTangentSpan = Math.max(
      ...tangentAnchors.flatMap((a) =>
        tangentAnchors.map((b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2])),
      ),
    );
    // Previously 2 * hypot(5.9, 5.6) = 16.27; now snugly bounds A(3,0,4), B(3,5,4), C(-1,0,7) (~10.09 diagonal)
    expect(maxTangentSpan).toBeLessThan(11.2);

    // Secant cut (`mat-cau-cat-mat-phang`, R=5, rCut=4) still spans > 2 * R * 1.10 across full sphere diameter
    const secantScene = ADVANCED_SAMPLES.find((s) => s.id === "mat-cau-cat-mat-phang")!.envelope.scene3d;
    const secantPlane = secantScene.objects.find((o) => o.type === "plane3")!;
    const secantAnchors = compactPlaneAnchorPoints(secantScene, secantPlane, secantScene.objects);
    const xs = secantAnchors.map((p) => p[0]);
    const ys = secantAnchors.map((p) => p[1]);
    expect(Math.max(...xs) - Math.min(...xs)).toBeGreaterThan(11.0);
    expect(Math.max(...ys) - Math.min(...ys)).toBeGreaterThan(11.0);
  });

  it("adapts cleanly across desktop, tablet, and narrow/short mobile aspect ratios without clipping or NaN", () => {
    const stageSizes: Array<[string, number, number]> = [
      ["desktop-1920x1080", 1540, 1034],
      ["desktop-1440x900", 1080, 854],
      ["desktop-1280x800", 920, 754],
      ["tablet-768x1024", 768, 620],
      ["mobile-390x844", 390, 480],
      ["mobile-390x500", 390, 260],
    ];
    for (const id of [
      "chop-mat-cau-ngoai-tiep",
      "mat-phang-tiep-xuc-mat-cau",
      "lang-tru-tam-giac-thiet-dien",
      "khoang-cach-hai-duong-cheo-nhau",
      "hinh-non-cat-song-song-day",
    ]) {
      const scene = ADVANCED_SAMPLES.find((s) => s.id === id)!.envelope.scene3d;
      const primaryPts = densePrimarySurfacePoints(scene);
      for (const [label, w, h] of stageSizes) {
        const { cam, ctrl } = buildDefaultFramedCamera(scene, w, h);
        const dist = cam.position.distanceTo(ctrl.target);
        expect(Number.isFinite(dist) && dist > 0, `${id}@${label} finite dist`).toBe(true);
        const span = measureProjectedSpan(cam, primaryPts);
        expect(span.clipped, `${id}@${label} zero clipping`).toBe(0);
        expect(span.widthPct, `${id}@${label} width <= 72%`).toBeLessThanOrEqual(72);
        expect(span.heightPct, `${id}@${label} height <= 72%`).toBeLessThanOrEqual(72);
      }
    }
  });

  it("maintains exact Orbit Target stability across construction steps and under 90°, 180°, and 360° azimuth rotation", () => {
    for (const id of ["chop-mat-cau-ngoai-tiep", "lap-phuong-thiet-dien-bat-ky", "mat-phang-tiep-xuc-mat-cau"]) {
      const scene = ADVANCED_SAMPLES.find((s) => s.id === id)!.envelope.scene3d;
      const stepCount = scene.formation?.steps?.length ?? 1;
      const fullPivot = tinhTamXoayOnDinh(scene.objects)!;
      for (let step = 0; step < stepCount; step += 1) {
        const stepObjs = objectsAt(scene, step);
        const stepPivot = tinhTamXoayOnDinh(stepObjs);
        if (stepPivot) {
          // Once primary solid(s) are present, pivot matches canonical pivot
          if (stepObjs.filter((o) => o.type === "solid" || o.type === "curved_solid").length ===
              scene.objects.filter((o) => o.type === "solid" || o.type === "curved_solid").length) {
            expect(stepPivot.tamXoay[0]).toBeCloseTo(fullPivot.tamXoay[0], 6);
            expect(stepPivot.tamXoay[1]).toBeCloseTo(fullPivot.tamXoay[1], 6);
            expect(stepPivot.tamXoay[2]).toBeCloseTo(fullPivot.tamXoay[2], 6);
          }
        }
      }

      const { cam, ctrl } = buildDefaultFramedCamera(scene, 1080, 854);
      const primaryPts = densePrimarySurfacePoints(scene);
      const baseOffset = cam.position.clone().sub(ctrl.target);
      for (const deg of [90, 180, 270, 360]) {
        const rad = (deg * Math.PI) / 180;
        const rotatedOffset = baseOffset.clone().applyAxisAngle(new THREE.Vector3(0, 0, 1), rad);
        cam.position.copy(ctrl.target).add(rotatedOffset);
        cam.lookAt(ctrl.target);
        cam.updateMatrixWorld(true);
        const span = measureProjectedSpan(cam, primaryPts);
        expect(span.clipped, `${id} rotated ${deg}deg no clip`).toBe(0);
      }
      // At 360 deg, camera returns identically to initial pose
      expect(cam.position.distanceTo(ctrl.target.clone().add(baseOffset))).toBeLessThan(1e-9);
    }
  });

  it("handles degenerate inputs, NaN/Infinity coordinates, and unseen synthetic composite scenes safely without hardcoding", () => {
    expect(
      khungAnToanCanDoiTam([], [0, 0, 0], 50, 1.25, [8, 5, 6], { tiLeNgang: 0.65, tiLeDoc: 0.62 }),
    ).toEqual({
      vungAnToanNdc: { xMin: -0.65, xMax: 0.65, yMin: -0.62, yMax: 0.62 },
      lechOngKinhNgang: 0,
      lechOngKinhDoc: 0,
    });
    expect(
      khungNhinQuanhTam([[NaN, 0, 0]], [0, 0, 0], 50, 1.25, [8, 5, 6]),
    ).not.toBeNull();
    expect(
      khungNhinQuanhTam([[1, 2, 3]], [0, 0, 0], 0, 1.25, [8, 5, 6]),
    ).toBeNull();
    expect(
      khungNhinQuanhTam([[1, 2, 3]], [0, 0, 0], 50, 0, [8, 5, 6]),
    ).toBeNull();

    // Unseen synthetic composite scene: off-origin tetrahedron + circumscribed sphere + infinite axis line + auxiliary plane
    const novelObjects: SceneObject[] = [
      {
        id: "tet_novel",
        type: "solid",
        render: "solid",
        label: "Tứ diện KLMN",
        vertices: [
          ["10", "10", "0"],
          ["16", "10", "0"],
          ["10", "16", "0"],
          ["10", "10", "6"],
        ],
        faces: [
          [0, 1, 2],
          [0, 1, 3],
          [1, 2, 3],
          [0, 2, 3],
        ],
        depends: [],
      } as unknown as SceneObject,
      {
        id: "sph_novel",
        type: "curved_solid",
        render: "curved_solid",
        curved_kind: "ball",
        label: "Mặt cầu (S_novel)",
        anchor: ["13", "13", "3"],
        radius_sq: "27",
        depends: ["tet_novel"],
      } as unknown as SceneObject,
      {
        id: "axis_novel",
        type: "line3",
        render: "line",
        label: "d_novel",
        point: ["13", "13", "0"],
        direction: ["0", "0", "1"],
        depends: ["tet_novel"],
      } as unknown as SceneObject,
      {
        id: "plane_novel",
        type: "plane3",
        render: "surface",
        label: "(Q_novel)",
        point: ["50", "-40", "3"],
        normal: ["0", "0", "1"],
        depends: ["tet_novel"],
      } as unknown as SceneObject,
    ];
    const novelScene: Scene3D = { objects: novelObjects } as Scene3D;
    const { cam, ctrl } = buildDefaultFramedCamera(novelScene, 1080, 854);
    const span = measureProjectedSpan(cam, densePrimarySurfacePoints(novelScene));
    expect(ctrl.target.x).toBeCloseTo(13, 5);
    expect(ctrl.target.y).toBeCloseTo(13, 5);
    expect(ctrl.target.z).toBeCloseTo(3, 5);
    expect(span.clipped).toBe(0);
    expect(span.heightPct).toBeGreaterThanOrEqual(58);
    expect(span.heightPct).toBeLessThanOrEqual(66);
    expect(span.widthPct).toBeLessThanOrEqual(66);
  });

  it("keeps vertex labels separated from neighboring labels, viewport edges, and floating UI obstacles", () => {
    const placed = tinhViTriNhanDiem(
      [
        { id: "O", x: 520, y: 420, w: 18, h: 18 },
        { id: "I", x: 524, y: 416, w: 16, h: 18 },
        { id: "TopEdge", x: 300, y: 12, w: 18, h: 18 },
      ],
      [],
      [],
      undefined,
      { w: 600, h: 500 },
      [{ x: 240, y: 0, w: 120, h: 36 }],
    );
    const oBox = placed.get("O")!;
    const iBox = placed.get("I")!;
    const topBox = placed.get("TopEdge")!;
    const overlapX = Math.min(oBox.x + 18, iBox.x + 16) - Math.max(oBox.x, iBox.x);
    const overlapY = Math.min(oBox.y + 18, iBox.y + 18) - Math.max(oBox.y, iBox.y);
    expect(overlapX > 2 && overlapY > 2).toBe(false);
    // TopEdge avoids both y < 6 border and the top obstacle [240..360, 0..36]
    expect(topBox.y).toBeGreaterThanOrEqual(6);
  });
});
