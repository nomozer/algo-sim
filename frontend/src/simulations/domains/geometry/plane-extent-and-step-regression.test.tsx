import * as THREE from "three";
import { describe, expect, it } from "vitest";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { veKhongGian } from "./scene3d-chart";
import { chonHuongNhin, khungNhinSuPham } from "./scene3d-camera";
import {
  clampStep,
  diemHuuHan,
  duongKinhCanh,
  objectsAt,
  stepCount,
  toVec3,
  type Scene3D,
  type Vec3,
} from "./scene3d-model";
import {
  buildPedagogicalConstructionPlan,
  compactPlaneAnchorPoints,
  computeBoundedStudiedPlanePolygon,
  resolveAdaptivePlaneVisualization,
  resolveLineDisplaySpan,
  resolvePlaneSectionVisibility,
  resolveStepVisualRoles,
} from "./scene3d-semantic-policy";
import { withSubEntities } from "./scene3d-subentities";
import { buildObject3D, tinhTamXoayOnDinh } from "./scene3d-view";

function extractSampleScene(id: string): Scene3D {
  const sample = GEOMETRY_SAMPLES.find((s) => s.id === id);
  if (!sample) throw new Error(`Missing geometry sample: ${id}`);
  return (sample.envelope as unknown as { scene3d: Scene3D }).scene3d;
}

function maxDiagonal(pts: readonly Vec3[]): number {
  let maxD = 0;
  for (let i = 0; i < pts.length; i += 1) {
    for (let j = i + 1; j < pts.length; j += 1) {
      maxD = Math.max(
        maxD,
        Math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1], pts[i][2] - pts[j][2]),
      );
    }
  }
  return maxD;
}

function signedDistToPlane(p: Vec3, origin: Vec3, normalRaw: Vec3): number {
  const nLen = Math.hypot(normalRaw[0], normalRaw[1], normalRaw[2]) || 1;
  return (
    ((p[0] - origin[0]) * normalRaw[0]
      + (p[1] - origin[1]) * normalRaw[1]
      + (p[2] - origin[2]) * normalRaw[2]) / nLen
  );
}

function dotVec(a: Vec3, b: Vec3): number {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

describe("AXO Pha A — Geometry Plane Extent, Bisector Framing & Step Consistency Regression", () => {
  it("Problem 2 (chop-mat-cau-ngoai-tiep, Step 11/17): keeps bisector planes (α),(β),(γ) proportional, coplanar, orthogonal, on base z>=0, and never bloated by downstream sphere", () => {
    const raw = extractSampleScene("chop-mat-cau-ngoai-tiep");
    const plan = buildPedagogicalConstructionPlan(withSubEntities(raw));
    expect(plan.steps).toHaveLength(17);

    const scene = veKhongGian(plan.scene);
    const pyramid = scene.objects.find((o) => o.id === "chop" && o.type === "solid")!;
    expect(pyramid).toBeDefined();
    const pyramidDiam = duongKinhCanh(diemHuuHan([pyramid]));
    const pt = (id: string) => toVec3(scene.objects.find((o) => o.id === id)!.xyz!);
    const A = pt("A");
    const B = pt("B");
    const D = pt("D");
    const S = pt("S");
    const O = pt("O");
    const M = pt("M");
    const MAB = pt("M_AB");
    const MAD = pt("M_AD");
    const I = pt("I");

    const step11 = plan.steps[10]!;
    expect(step11.title).toContain("(α) và (β)");
    const vis11 = objectsAt(scene, step11.anchor);

    const bisectorSpecs: Array<{
      id: string;
      anchorPt: Vec3;
      perpEdge: [Vec3, Vec3];
    }> = [
      { id: "mp_tt_AB", anchorPt: MAB, perpEdge: [A, B] },
      { id: "mp_tt_AD", anchorPt: MAD, perpEdge: [A, D] },
      { id: "mp_tt_SA", anchorPt: M, perpEdge: [S, A] },
    ];

    for (const spec of bisectorSpecs) {
      const planeObj = scene.objects.find((o) => o.id === spec.id)!;
      expect(planeObj).toBeDefined();

      // Mathematical invariants preserved: point, normal, edge orthogonality, center I incidence
      const p0 = toVec3(planeObj.point!);
      const nVec = toVec3(planeObj.normal!);
      const nLen = Math.hypot(...nVec);
      expect(nLen).toBeGreaterThan(1e-6);
      expect(Math.abs(signedDistToPlane(spec.anchorPt, p0, nVec))).toBeLessThan(1e-6);
      expect(Math.abs(signedDistToPlane(I, p0, nVec))).toBeLessThan(1e-6);

      const edgeVec: Vec3 = [
        spec.perpEdge[1][0] - spec.perpEdge[0][0],
        spec.perpEdge[1][1] - spec.perpEdge[0][1],
        spec.perpEdge[1][2] - spec.perpEdge[0][2],
      ];
      const eLen = Math.hypot(...edgeVec);
      const crossSq =
        (nVec[1] * edgeVec[2] - nVec[2] * edgeVec[1]) ** 2
        + (nVec[2] * edgeVec[0] - nVec[0] * edgeVec[2]) ** 2
        + (nVec[0] * edgeVec[1] - nVec[1] * edgeVec[0]) ** 2;
      expect(Math.sqrt(crossSq) / (nLen * eLen)).toBeLessThan(1e-6);

      // Visual patch MUST come from polyhedron compact bounded patch, NEVER 2.3R sphere fallback
      const dec = resolveAdaptivePlaneVisualization(scene, planeObj, vis11);
      expect(dec.mode).toBe("COMPACT_PLANE_PATCH");
      expect(dec.reason).not.toBe("curved_solid_relation_patch");

      const poly = computeBoundedStudiedPlanePolygon(scene, planeObj, vis11);
      expect(poly.length).toBeGreaterThanOrEqual(4);

      for (const v of poly) {
        expect(Math.abs(signedDistToPlane(v, p0, nVec))).toBeLessThan(1e-5);
        expect(v[2]).toBeGreaterThanOrEqual(-1e-6);
        expect(v[2]).toBeLessThanOrEqual(3.2);
      }
      expect(maxDiagonal(poly) / pyramidDiam).toBeLessThan(0.88);
    }

    // Intersection line truc_day = (α) ∩ (β) passes through O(2,2,0) & I(2,2,2) cleanly
    const trucDay = scene.objects.find((o) => o.id === "truc_day")!;
    expect(trucDay).toBeDefined();
    expect(Math.abs(signedDistToPlane(O, toVec3(scene.objects.find((o) => o.id === "mp_tt_AB")!.point!), toVec3(scene.objects.find((o) => o.id === "mp_tt_AB")!.normal!)))).toBeLessThan(1e-6);
    expect(Math.abs(signedDistToPlane(O, toVec3(scene.objects.find((o) => o.id === "mp_tt_AD")!.point!), toVec3(scene.objects.find((o) => o.id === "mp_tt_AD")!.normal!)))).toBeLessThan(1e-6);
    const span = resolveLineDisplaySpan(scene, trucDay, vis11);
    expect(span.coreSegment).toBeDefined();
    expect(span.coreSegment![0][2]).toBeGreaterThanOrEqual(-0.01);
    expect(span.coreSegment![1][2]).toBeLessThanOrEqual(2.05);

    // Camera framing independence: auxiliary bisector planes must NOT shift camera distance or target
    const camWithoutPlanes = diemHuuHan([pyramid]);
    const camWithAll = diemHuuHan(vis11.filter((o) => o.id !== "truc_day"));
    expect(duongKinhCanh(camWithAll)).toBeCloseTo(duongKinhCanh(camWithoutPlanes), 6);
    const pivotAll = tinhTamXoayOnDinh(vis11)!;
    const pivotSolid = tinhTamXoayOnDinh([pyramid])!;
    expect(pivotAll.tamXoay[0]).toBeCloseTo(pivotSolid.tamXoay[0], 6);
    expect(pivotAll.tamXoay[1]).toBeCloseTo(pivotSolid.tamXoay[1], 6);
    expect(pivotAll.tamXoay[2]).toBeCloseTo(pivotSolid.tamXoay[2], 6);
  });

  it("Problem 1 (chop-thiet-dien-ba-diem, steps 9 -> 10 -> 11 -> 12 -> 11 -> 10 -> 9 -> 12): exact E/F/MENPF coordinates, state determinism, and camera stability", () => {
    const raw = extractSampleScene("chop-thiet-dien-ba-diem");
    const plan = buildPedagogicalConstructionPlan(withSubEntities(raw));
    expect(plan.steps).toHaveLength(12);
    const scene = veKhongGian(plan.scene);

    const pt = (id: string) => toVec3(scene.objects.find((o) => o.id === id)!.xyz!);
    const S = pt("S");
    const B = pt("B");
    const D = pt("D");
    const E = pt("E");
    const F = pt("F");
    const mpMNP = scene.objects.find((o) => o.id === "mp_MNP")!;
    const p0 = toVec3(mpMNP.point!);
    const nVec = toVec3(mpMNP.normal!);

    expect(Math.abs(signedDistToPlane(E, p0, nVec))).toBeLessThan(1e-6);
    expect(Math.abs(signedDistToPlane(F, p0, nVec))).toBeLessThan(1e-6);
    const sb: Vec3 = [B[0] - S[0], B[1] - S[1], B[2] - S[2]];
    const sd: Vec3 = [D[0] - S[0], D[1] - S[1], D[2] - S[2]];
    const tE = dotVec([E[0] - S[0], E[1] - S[1], E[2] - S[2]], sb) / dotVec(sb, sb);
    const tF = dotVec([F[0] - S[0], F[1] - S[1], F[2] - S[2]], sd) / dotVec(sd, sd);
    expect(tE).toBeCloseTo(0.75, 6);
    expect(tF).toBeCloseTo(0.75, 6);

    const sequence = [9, 10, 11, 12, 11, 10, 9, 12];
    const baselineByStep = new Map<number, string>();
    const camRadii: number[] = [];

    for (const stepNum of sequence) {
      const stepItem = plan.steps[stepNum - 1]!;
      const k = clampStep(scene, stepItem.anchor);
      const vis = objectsAt(scene, k);
      const planeVis = resolvePlaneSectionVisibility(scene, mpMNP, k, false, null, stepItem.startAnchor);
      const roles = resolveStepVisualRoles(scene, k, { auxiliaryShown: false, selectedId: null });
      const patch = computeBoundedStudiedPlanePolygon(scene, mpMNP, vis);

      if (stepNum < 12) {
        expect(planeVis.visible).toBe(true);
        expect(patch).toHaveLength(3);
      } else {
        expect(planeVis.visible).toBe(false);
        expect(planeVis.lifecycleStage).toBe("retired_scaffold");
        const sectionObj = vis.find((o) => o.type === "section")!;
        expect(sectionObj).toBeDefined();
        expect((sectionObj.polygon ?? sectionObj.vertices ?? []).length).toBe(5);
      }

      const fitPts = diemHuuHan(scene.objects);
      const fit = khungNhinSuPham(fitPts, [], [], 42, 1.35, chonHuongNhin(fitPts, [], []))!;
      camRadii.push(
        Math.hypot(
          fit.viTri[0] - fit.nhinVao[0],
          fit.viTri[1] - fit.nhinVao[1],
          fit.viTri[2] - fit.nhinVao[2],
        ),
      );

      const sig = JSON.stringify({
        ids: vis.map((o) => o.id).sort(),
        planeVisible: planeVis.visible,
        patch,
        roles: [...roles.entries()].sort(([a], [b]) => a.localeCompare(b)),
      });
      if (baselineByStep.has(stepNum)) {
        expect(sig).toBe(baselineByStep.get(stepNum));
      } else {
        baselineByStep.set(stepNum, sig);
      }
    }

    for (const r of camRadii) {
      expect(r).toBeCloseTo(camRadii[0]!, 9);
    }
  });

  it("Audits all 10 required geometry families for coplanarity, bounded plane proportions, Three.js mesh material invariants & finite framing", () => {
    const familyRepIds = [
      "chop-thiet-dien-ba-diem",
      "lap-phuong-thiet-dien-bat-ky",
      "lang-tru-tam-giac-thiet-dien",
      "mat-cau-cat-mat-phang",
      "mat-phang-tiep-xuc-mat-cau",
      "hinh-non-cat-song-song-day",
      "tru-thiet-dien-tron",
      "oxyz-giao-diem-duong-mat",
      "goc-nhi-dien-hai-mat-phang",
      "chop-mat-cau-ngoai-tiep",
    ];

    for (const id of familyRepIds) {
      const raw = extractSampleScene(id);
      const scene = veKhongGian(buildPedagogicalConstructionPlan(withSubEntities(raw)).scene);
      const primarySolid = scene.objects.find((o) => o.type === "solid" || o.type === "curved_solid");
      const refDiam = Math.max(
        duongKinhCanh(primarySolid ? diemHuuHan([primarySolid]) : diemHuuHan(scene.objects)),
        1,
      );

      for (const pl of scene.objects.filter((o) => o.type === "plane3")) {
        const total = stepCount(scene);
        const testStep = Math.max(0, Math.min(total - 1, Math.floor(total * 0.65)));
        const vis = objectsAt(scene, testStep);
        const bounded = computeBoundedStudiedPlanePolygon(scene, pl, vis);
        const compact = bounded.length < 3 ? compactPlaneAnchorPoints(scene, pl, vis) : [];
        const patch = bounded.length >= 3 ? bounded : compact;
        if (patch.length < 3) continue;

        const p0 = toVec3(pl.point!);
        const nVec = toVec3(pl.normal!);
        for (const v of patch) {
          expect(Math.abs(signedDistToPlane(v, p0, nVec)), `${id}:${pl.id}`).toBeLessThan(1e-4);
        }
        expect(maxDiagonal(patch) / refDiam, `${id}:${pl.id} proportional diag`).toBeLessThan(1.3);

        const meshGroup = buildObject3D(
          pl,
          false,
          undefined,
          diemHuuHan(vis),
          new THREE.Vector3(8, 6, 7),
          undefined,
          undefined,
          false,
          "primary",
          false,
          true,
          false,
          scene,
          undefined,
          undefined,
          bounded,
          vis,
        );
        expect(meshGroup).toBeTruthy();
        const meshes: THREE.Mesh[] = [];
        meshGroup?.traverse((node) => {
          if (node instanceof THREE.Mesh) meshes.push(node);
        });
        expect(meshes.length).toBeGreaterThanOrEqual(1);
        const mat = meshes[0]!.material as THREE.MeshBasicMaterial;
        expect(mat.transparent).toBe(true);
        expect(mat.depthWrite).toBe(false);
        expect(mat.opacity).toBeGreaterThan(0);
        expect(mat.opacity).toBeLessThanOrEqual(0.5);
      }
    }
  });
});
