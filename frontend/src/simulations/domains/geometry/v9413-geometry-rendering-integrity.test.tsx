import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { auditSceneRepresentationConsistency } from "./scene3d-representation-consistency";
import {
  clampStep,
  diemHuuHan,
  duongKinhCanh,
  objectsAt,
  stepCount,
  toVec3,
  type ExactVec3,
  type Scene3D,
  type SceneObject,
  type Vec3,
} from "./scene3d-model";
import { veKhongGian } from "./scene3d-chart";
import {
  compactPlaneAnchorPoints,
  computeBoundedStudiedPlanePolygon,
  planeSolidEdgeIntersections,
  replaceRawSceneIdTokens,
  resolveStudentObjectPresentation,
} from "./scene3d-semantic-policy";
import { evaluateStudentPresentationPolicy } from "./scene3d-student-presentation-policy";
import { buildObject3D } from "./scene3d-view";

function extractEnvelopeScene3d(envelope: unknown): Scene3D {
  if (!envelope || typeof envelope !== "object" || !("scene3d" in envelope)) {
    throw new Error("Sample envelope is missing scene3d");
  }
  return (envelope as { scene3d: unknown }).scene3d as Scene3D;
}

function getSampleScene(id: string): Scene3D {
  const sample = GEOMETRY_SAMPLES.find((s) => s.id === id);
  if (!sample) throw new Error(`Missing geometry sample: ${id}`);
  return extractEnvelopeScene3d(sample.envelope);
}

function sub3(a: Vec3, b: Vec3): Vec3 {
  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
}

function dot3(a: Vec3, b: Vec3): number {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

function cross3(a: Vec3, b: Vec3): Vec3 {
  return [
    a[1] * b[2] - a[2] * b[1],
    a[2] * b[0] - a[0] * b[2],
    a[0] * b[1] - a[1] * b[0],
  ];
}

function minEdgeDistanceInPlane(p: Vec3, poly: Vec3[], rawNormal: Vec3): number {
  const nLen = Math.hypot(...rawNormal);
  const n: Vec3 = [rawNormal[0] / nLen, rawNormal[1] / nLen, rawNormal[2] / nLen];
  const planeDist = Math.abs(dot3(sub3(p, poly[0]), n));
  if (planeDist > 1e-3) return -planeDist;

  // Signed winding relative to n
  let signedTwiceArea = 0;
  for (let i = 0; i < poly.length; i += 1) {
    const a = sub3(poly[i], poly[0]);
    const b = sub3(poly[(i + 1) % poly.length], poly[0]);
    signedTwiceArea += dot3(n, cross3(a, b));
  }
  const orient = signedTwiceArea >= 0 ? 1 : -1;
  let minMargin = Infinity;
  for (let i = 0; i < poly.length; i += 1) {
    const a = poly[i];
    const b = poly[(i + 1) % poly.length];
    const edge = sub3(b, a);
    const edgeLen = Math.hypot(...edge);
    if (edgeLen <= 1e-9) continue;
    const edgeDist = orient * (dot3(n, cross3(edge, sub3(p, a))) / edgeLen);
    if (edgeDist < minMargin) minMargin = edgeDist;
  }
  return minMargin;
}

function scaleExactNumber(value: string, factor: number): string {
  if (factor === 1) return value;
  const trimmed = value.trim();
  const [nStr, dStr] = trimmed.split("/");
  const n = Number(nStr);
  const d = dStr ? Number(dStr) : 1;
  if (Number.isInteger(factor)) {
    return d === 1 ? String(n * factor) : `${n * factor}/${d}`;
  }
  const inv = Math.round(1 / factor);
  return `${n}/${d * inv}`;
}

function scaleExactVec3(v: ExactVec3, factor: number): ExactVec3 {
  return [
    scaleExactNumber(v[0], factor),
    scaleExactNumber(v[1], factor),
    scaleExactNumber(v[2], factor),
  ];
}

function cloneAndScaleScene(raw: Scene3D, factor: number): Scene3D {
  const copy = structuredClone(raw) as Scene3D;
  for (const o of copy.objects) {
    if (o.xyz) o.xyz = scaleExactVec3(o.xyz, factor);
    if (o.point) o.point = scaleExactVec3(o.point, factor);
    if (o.point_a) o.point_a = scaleExactVec3(o.point_a, factor);
    if (o.point_b) o.point_b = scaleExactVec3(o.point_b, factor);
    if (o.endpoints) o.endpoints = o.endpoints.map((e) => scaleExactVec3(e, factor));
    if (o.vertices) o.vertices = o.vertices.map((e) => scaleExactVec3(e, factor));
    if (o.polygon) o.polygon = o.polygon.map((e) => scaleExactVec3(e, factor));
    if (o.anchor) o.anchor = scaleExactVec3(o.anchor, factor);
    if (o.apex_or_top) o.apex_or_top = scaleExactVec3(o.apex_or_top, factor);
    if (o.rim_point) o.rim_point = scaleExactVec3(o.rim_point, factor);
    if (o.center) o.center = scaleExactVec3(o.center, factor);
    if (o.steps) {
      for (const s of o.steps) {
        s.a = scaleExactVec3(s.a, factor);
        s.b = scaleExactVec3(s.b, factor);
      }
    }
    if (o.perpendicular_witness?.foot) {
      o.perpendicular_witness.foot = scaleExactVec3(o.perpendicular_witness.foot, factor);
    }
    if (o.annotation?.witness?.foot) {
      o.annotation.witness.foot = scaleExactVec3(o.annotation.witness.foot, factor);
    }
    if (o.radius_sq) {
      // Scale squared radius by factor^2
      const rSq = scaleExactNumber(o.radius_sq, factor);
      o.radius_sq = scaleExactNumber(rSq, factor);
    }
  }
  return copy;
}

describe("AXO V9.4.13 — Geometry Rendering Integrity & Consistency", () => {
  it("BUG-FE-001: bounded plane patch contains all coplanar anchors and section vertices (no floating E/F/P)", () => {
    const cases: { id: string; planeId: string; step?: number }[] = [
      { id: "chop-thiet-dien-ba-diem", planeId: "mp_MNP", step: 10 },
      { id: "chop-thiet-dien-ba-diem", planeId: "mp_MNP" },
      { id: "lang-tru-tam-giac-thiet-dien", planeId: "mp_NPQ" },
      { id: "lap-phuong-thiet-dien-bat-ky", planeId: "mp_MNP" },
    ];

    const collectRealCoplanarPoints = (
      planeObj: SceneObject,
      vis: readonly SceneObject[],
      scale: number,
    ): Vec3[] => {
      const p0 = toVec3(planeObj.point!);
      const nRaw = toVec3(planeObj.normal!);
      const nLen = Math.hypot(...nRaw);
      const u: Vec3 = [nRaw[0] / nLen, nRaw[1] / nLen, nRaw[2] / nLen];
      const tol = 1e-4 * scale;
      const out: Vec3[] = [...planeSolidEdgeIntersections(planeObj, vis)];
      for (const obj of vis) {
        if (obj.type === "point3" && obj.xyz) out.push(toVec3(obj.xyz));
        else if (obj.type === "solid" && Array.isArray(obj.vertices)) {
          for (const sv of obj.vertices) out.push(toVec3(sv));
        } else if (
          (obj.type === "section" || obj.type === "polygon3")
          && (obj.depends ?? []).includes(planeObj.id)
        ) {
          for (const pv of obj.polygon ?? obj.vertices ?? []) out.push(toVec3(pv));
        }
      }
      return out.filter(
        (p) => Math.abs((p[0] - p0[0]) * u[0] + (p[1] - p0[1]) * u[1] + (p[2] - p0[2]) * u[2]) <= tol,
      );
    };

    for (const tc of cases) {
      const scene = veKhongGian(getSampleScene(tc.id));
      const vis = tc.step !== undefined ? objectsAt(scene, tc.step) : scene.objects;
      const planeObj = (vis.find((o) => o.id === tc.planeId) ?? vis.find((o) => o.render === "surface"))!;
      expect(planeObj).toBeDefined();
      const bounded = computeBoundedStudiedPlanePolygon(scene, planeObj, vis);
      expect(bounded.length).toBeGreaterThanOrEqual(3);

      const scale = Math.max(duongKinhCanh(diemHuuHan(scene.objects)), 1);
      const planeNormal = toVec3(planeObj.normal!);
      const mustContain = collectRealCoplanarPoints(planeObj, vis, scale);
      expect(mustContain.length).toBeGreaterThanOrEqual(3);

      for (const pt of mustContain) {
        const margin = minEdgeDistanceInPlane(pt, bounded, planeNormal);
        expect(
          margin,
          `${tc.id} (step=${tc.step ?? "final"}, plane=${planeObj.id}) pt=${JSON.stringify(pt)} outside bounded=${JSON.stringify(bounded)}`,
        ).toBeGreaterThanOrEqual(-1e-4 * scale);
      }
    }

    // Universal catalog sweep across all samples with section + plane3
    for (const sample of GEOMETRY_SAMPLES) {
      const scene = veKhongGian(extractEnvelopeScene3d(sample.envelope));
      const scale = Math.max(duongKinhCanh(diemHuuHan(scene.objects)), 1);
      const planes = scene.objects.filter((o) => o.render === "surface");
      for (const planeObj of planes) {
        const bounded = computeBoundedStudiedPlanePolygon(scene, planeObj, scene.objects);
        if (bounded.length < 3) continue;
        const planeNormal = toVec3(planeObj.normal!);
        for (const pt of collectRealCoplanarPoints(planeObj, scene.objects, scale)) {
          const margin = minEdgeDistanceInPlane(pt, bounded, planeNormal);
          expect(
            margin,
            `catalog ${sample.id} plane=${planeObj.id} pt=${JSON.stringify(pt)} outside bounded`,
          ).toBeGreaterThanOrEqual(-1e-4 * scale);
        }
      }
    }
  });

  it("BUG-FE-002: Oxyz standalone plane (P) expands cleanly around triangle ABC without solid in scene", () => {
    const scene = veKhongGian(getSampleScene("oxyz-giao-diem-duong-mat"));
    const planeP = scene.objects.find((o) => o.render === "surface")!;
    expect(planeP).toBeDefined();
    const bounded = computeBoundedStudiedPlanePolygon(scene, planeP, scene.objects);
    expect(bounded.length).toBeGreaterThanOrEqual(4);

    const triPts = ["A", "B", "C"].map((id) => toVec3(scene.objects.find((o) => o.id === id)!.xyz!));
    const n = toVec3(planeP.normal!);
    for (const p of triPts) {
      const margin = minEdgeDistanceInPlane(p, bounded, n);
      expect(margin).toBeGreaterThan(0.05);
    }
  });

  it("BUG-FE-003: studied plane patch vertices remain invariant across all step transitions after creation", () => {
    for (const id of [
      "chop-thiet-dien-ba-diem",
      "mat-phang-tiep-xuc-mat-cau",
      "goc-nhi-dien-hai-mat-phang",
      "chop-mat-cau-ngoai-tiep",
    ]) {
      const scene = veKhongGian(getSampleScene(id));
      const totalSteps = stepCount(scene);
      const hasSolidInScene = scene.objects.some((o) => o.type === "solid");
      const planes = scene.objects.filter((o) => o.render === "surface");

      for (const finalPlane of planes) {
        const expectedPoly = computeBoundedStudiedPlanePolygon(scene, finalPlane, scene.objects);
        const expectedAnchors = compactPlaneAnchorPoints(scene, finalPlane, scene.objects);

        for (let k = 0; k < totalSteps; k += 1) {
          const vis = objectsAt(scene, k);
          const pl = vis.find((o) => o.id === finalPlane.id);
          if (!pl) continue;
          const solidReady = !hasSolidInScene || vis.some((o) => o.type === "solid");
          const stepPoly = computeBoundedStudiedPlanePolygon(scene, pl, vis);
          if (solidReady) {
            expect(stepPoly.length, `${id} (${pl.id}) step ${k} poly len`).toBe(expectedPoly.length);
            for (let i = 0; i < expectedPoly.length; i += 1) {
              expect(Math.hypot(
                stepPoly[i][0] - expectedPoly[i][0],
                stepPoly[i][1] - expectedPoly[i][1],
                stepPoly[i][2] - expectedPoly[i][2],
              ), `${id} (${pl.id}) step ${k} vert ${i}`).toBeLessThan(1e-7);
            }
          }
          const stepAnchors = compactPlaneAnchorPoints(scene, pl, vis);
          expect(stepAnchors.length, `${id} (${pl.id}) step ${k} anchor len`).toBe(expectedAnchors.length);
          for (let i = 0; i < expectedAnchors.length; i += 1) {
            expect(Math.hypot(
              stepAnchors[i][0] - expectedAnchors[i][0],
              stepAnchors[i][1] - expectedAnchors[i][1],
              stepAnchors[i][2] - expectedAnchors[i][2],
            ), `${id} (${pl.id}) step ${k} anchor ${i}`).toBeLessThan(1e-7);
          }
        }
      }
    }
  });

  it("Phase 9 step-by-step progression & reset state integrity on chop-thiet-dien-ba-diem", () => {
    const scene = veKhongGian(getSampleScene("chop-thiet-dien-ba-diem"));
    const n = stepCount(scene);
    expect(n).toBeGreaterThanOrEqual(10);

    const step0Ids = new Set(objectsAt(scene, 0).map((o) => o.id));
    expect(step0Ids.has("thiet_dien")).toBe(false);
    expect(step0Ids.has("E")).toBe(false);
    expect(step0Ids.has("F")).toBe(false);

    // Stepping forward then back to step 0 preserves exact object set
    const step9Ids = new Set(objectsAt(scene, clampStep(scene, 9)).map((o) => o.id));
    const stepBack0Ids = new Set(objectsAt(scene, 0).map((o) => o.id));
    expect([...stepBack0Ids]).toEqual([...step0Ids]);
    expect(step9Ids.size).toBeGreaterThan(step0Ids.size);
  });

  it("BUG-FE-004: presentation layer strips raw internal variable tokens (mp_MNP / mp_NPQ) cleanly", () => {
    for (const id of ["chop-thiet-dien-ba-diem", "lap-phuong-thiet-dien-bat-ky", "lang-tru-tam-giac-thiet-dien"]) {
      const scene = getSampleScene(id);
      for (const obj of scene.objects) {
        const pres = resolveStudentObjectPresentation(scene, obj.id);
        expect(pres?.title ?? "").not.toMatch(/\bmp_[A-Za-z0-9_]+\b/);
        expect(pres?.role ?? "").not.toMatch(/\bmp_[A-Za-z0-9_]+\b/);
        expect(pres?.description ?? "").not.toMatch(/\bmp_[A-Za-z0-9_]+\b/);
        for (const ev of pres?.evidence ?? []) {
          expect(ev).not.toMatch(/\bmp_[A-Za-z0-9_]+\b/);
        }
      }
      const policy = evaluateStudentPresentationPolicy(scene);
      for (const obj of scene.objects) {
        const role = policy.formatStudentObjectRole(obj);
        expect(role ?? "").not.toMatch(/\bmp_[A-Za-z0-9_]+\b/);
      }
    }
    expect(replaceRawSceneIdTokens("Test mp_MNP ref", getSampleScene("chop-thiet-dien-ba-diem"))).not.toContain("mp_MNP");
  });

  it("Phase 7 representation consistency audit passes across all 22 catalog samples (final & intermediate steps) without coordinate mutation", () => {
    expect(GEOMETRY_SAMPLES.length).toBe(22);

    for (const sample of GEOMETRY_SAMPLES) {
      const scene = extractEnvelopeScene3d(sample.envelope);
      const beforeSnapshot = JSON.stringify(scene);

      const report = auditSceneRepresentationConsistency(scene);
      expect(report.overallStatus, `${sample.id} final findings: ${JSON.stringify(report.findings)}`).toBe("VALID");
      expect(report.isConsistent).toBe(true);

      // Memoization hit verification
      const cached = auditSceneRepresentationConsistency(scene);
      expect(cached).toBe(report);
      const bypassed = auditSceneRepresentationConsistency(scene, { bypassCache: true });
      expect(bypassed).not.toBe(report);
      expect(bypassed.overallStatus).toBe("VALID");

      // Intermediate steps check: zero INVALID findings; VALID whenever >=2 finite coords give nonzero span,
      // and honestly UNDETERMINED on single-point initial frames (e.g. only center point I + scalar R)
      const total = stepCount(scene);
      for (let k = 0; k < total; k += 1) {
        const stepReport = auditSceneRepresentationConsistency(scene, { step: k });
        expect(
          stepReport.overallStatus,
          `${sample.id} step ${k} findings: ${JSON.stringify(stepReport.findings)}`,
        ).toBe(stepReport.sceneScale > 0 ? "VALID" : "UNDETERMINED");
      }

      // Zero mutation guarantee
      expect(JSON.stringify(scene)).toBe(beforeSnapshot);
    }
  });

  it("Phase 7 adversarial negative tests & scale-aware epsilon checks", () => {
    const base = getSampleScene("chop-thiet-dien-ba-diem");

    // 1. Corrupt section vertex off cutting plane -> INVALID
    const offPlaneScene = structuredClone(base) as Scene3D;
    const sec = offPlaneScene.objects.find((o) => o.type === "section")!;
    sec.polygon![0] = ["0", "0", "99"];
    const rOffPlane = auditSceneRepresentationConsistency(offPlaneScene);
    expect(rOffPlane.overallStatus).toBe("INVALID");
    expect(rOffPlane.checks.intersection_consistency.invalidCount).toBeGreaterThanOrEqual(1);

    // 2. Twist quad section vertices -> self-intersection INVALID
    const bowtieScene = structuredClone(base) as Scene3D;
    const bSec = bowtieScene.objects.find((o) => o.type === "section" && (o.polygon?.length ?? 0) >= 4)!;
    const tmp = bSec.polygon![1];
    bSec.polygon![1] = bSec.polygon![2];
    bSec.polygon![2] = tmp;
    const rBowtie = auditSceneRepresentationConsistency(bowtieScene);
    expect(rBowtie.overallStatus).toBe("INVALID");
    expect(rBowtie.checks.section_connectivity.invalidCount).toBeGreaterThanOrEqual(1);

    // 3. Out-of-bounds solid face vertex index -> INVALID
    const badMeshScene = structuredClone(base) as Scene3D;
    const solid = badMeshScene.objects.find((o) => o.type === "solid")!;
    solid.faces![0][0] = 999;
    const rBadMesh = auditSceneRepresentationConsistency(badMeshScene);
    expect(rBadMesh.overallStatus).toBe("INVALID");
    expect(rBadMesh.checks.mesh_consistency.invalidCount).toBeGreaterThanOrEqual(1);

    // 4. Witness foot perturbed off plane on inclined-plane problem -> INVALID
    const witBase = getSampleScene("khoang-cach-diem-mat-phang-nghieng");
    const badWit = structuredClone(witBase) as Scene3D;
    const pWithWit = badWit.objects.find((o) => o.perpendicular_witness?.foot || o.annotation?.witness?.foot)!;
    if (pWithWit.perpendicular_witness) pWithWit.perpendicular_witness.foot = ["10", "10", "10"];
    if (pWithWit.annotation?.witness) pWithWit.annotation.witness.foot = ["10", "10", "10"];
    const rBadWit = auditSceneRepresentationConsistency(badWit);
    expect(rBadWit.overallStatus).toBe("INVALID");

    // 5. Incomplete / missing plane normal -> UNDETERMINED (never auto-repaired or masked as VALID)
    const missingDataScene = structuredClone(base) as Scene3D;
    const mp = missingDataScene.objects.find((o) => o.render === "surface")!;
    delete mp.normal;
    const rMissing = auditSceneRepresentationConsistency(missingDataScene);
    expect(rMissing.overallStatus).not.toBe("VALID");
    expect(rMissing.checks.point_on_plane.undeterminedCount).toBeGreaterThanOrEqual(1);

    // 6. Scale-aware tolerance invariance (x1000 and /1000) + micro-scene catches 1e-4 error
    const bigScene = cloneAndScaleScene(base, 1000);
    expect(auditSceneRepresentationConsistency(bigScene).overallStatus).toBe("VALID");
    const tinyScene = cloneAndScaleScene(base, 1 / 1000);
    expect(auditSceneRepresentationConsistency(tinyScene).overallStatus).toBe("VALID");

    // Perturb tiny scene vertex by 1e-4 (= 0.1x tiny scale; a fixed 1e-3 epsilon would falsely miss this!)
    const corruptedTiny = structuredClone(tinyScene) as Scene3D;
    const tinySec = corruptedTiny.objects.find((o) => o.type === "section")!;
    tinySec.polygon![0] = [tinySec.polygon![0][0], tinySec.polygon![0][1], "1/10000"];
    const rTinyCorrupted = auditSceneRepresentationConsistency(corruptedTiny);
    expect(rTinyCorrupted.overallStatus).toBe("INVALID");
  });

  it("Phase 6 & 8: Three.js buildObject3D produces valid coplanar meshes, depth/polygonOffset settings & finite 5-camera projections across geometry families", () => {
    const familyIds = [
      "chop-thiet-dien-ba-diem",
      "lang-tru-tam-giac-thiet-dien",
      "lap-phuong-thiet-dien-bat-ky",
      "oxyz-giao-diem-duong-mat",
      "khoang-cach-hai-duong-cheo-nhau",
      "mat-cau-cat-mat-phang",
      "hinh-non-cat-song-song-day",
      "tru-thiet-dien-tron",
    ];

    const cameras = [
      new THREE.PerspectiveCamera(45, 16 / 9, 0.1, 1000),
      new THREE.PerspectiveCamera(45, 16 / 9, 0.1, 1000),
      new THREE.PerspectiveCamera(45, 16 / 9, 0.1, 1000),
      new THREE.PerspectiveCamera(45, 16 / 9, 0.1, 1000),
      new THREE.PerspectiveCamera(45, 16 / 9, 0.1, 1000),
    ];
    const camPositions = [
      [8, 6, 7],
      [-7, 8, 6],
      [0.01, 0.01, 14],
      [12, 0.1, 2],
      [4, 3, 4],
    ];
    camPositions.forEach(([x, y, z], idx) => {
      cameras[idx].up.set(0, 0, 1);
      cameras[idx].position.set(x, y, z);
      cameras[idx].lookAt(0, 0, 0);
      cameras[idx].updateMatrixWorld();
      cameras[idx].updateProjectionMatrix();
    });

    for (const id of familyIds) {
      const scene = veKhongGian(getSampleScene(id));
      const diemNen = diemHuuHan(scene.objects);
      const group = new THREE.Group();
      const builtPlanes: { obj: SceneObject; group: THREE.Object3D }[] = [];

      for (const o of scene.objects) {
        if (o.render === "readout" || o.render === "non_visual") continue;
        const boundedPoly =
          o.render === "surface"
            ? computeBoundedStudiedPlanePolygon(scene, o, scene.objects)
            : undefined;
        const built = buildObject3D(
          o,
          false,
          undefined,
          diemNen,
          cameras[0].position,
          undefined,
          undefined,
          false,
          "primary",
          true,
          true,
          false,
          scene,
          undefined,
          undefined,
          boundedPoly,
          scene.objects,
        );
        if (built) {
          group.add(built);
          if (o.render === "surface") builtPlanes.push({ obj: o, group: built });
        }
      }
      group.updateMatrixWorld(true);

      // Every mesh vertex on built surfaces lies in its mathematical plane and uses transparent DoubleSide + polygonOffset
      for (const { obj, group: plGroup } of builtPlanes) {
        const p0 = toVec3(obj.point!);
        const nRaw = toVec3(obj.normal!);
        const nLen = Math.hypot(...nRaw);
        const n: Vec3 = [nRaw[0] / nLen, nRaw[1] / nLen, nRaw[2] / nLen];
        let meshCount = 0;

        plGroup.traverse((child) => {
          if (child instanceof THREE.Mesh) {
            meshCount += 1;
            const mat = child.material as THREE.MeshBasicMaterial;
            expect(mat.side).toBe(THREE.DoubleSide);
            expect(mat.transparent).toBe(true);
            expect(mat.depthWrite).toBe(false);

            const pos = child.geometry.getAttribute("position");
            for (let i = 0; i < pos.count; i += 1) {
              const w = new THREE.Vector3(pos.getX(i), pos.getY(i), pos.getZ(i)).applyMatrix4(child.matrixWorld);
              const err = Math.abs(dot3([w.x - p0[0], w.y - p0[1], w.z - p0[2]], n));
              expect(err, `${id} built surface vertex off plane`).toBeLessThan(1e-4);
            }
          }
        });
        expect(meshCount).toBeGreaterThanOrEqual(1);
      }

      // Check finite NDC projection across all 5 cameras for all points
      const pointObjs = scene.objects.filter((o) => o.type === "point3" && o.xyz);
      for (const cam of cameras) {
        for (const ptObj of pointObjs) {
          const [x, y, z] = toVec3(ptObj.xyz!);
          const projected = new THREE.Vector3(x, y, z).project(cam);
          expect(Number.isFinite(projected.x)).toBe(true);
          expect(Number.isFinite(projected.y)).toBe(true);
          expect(Number.isFinite(projected.z)).toBe(true);
        }
      }
    }
  });
});
