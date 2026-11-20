import { describe, expect, it } from "vitest";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import {
  computeSmartLocateCamera,
  type OccluderSphereMesh,
  type OccluderTriangleMesh,
} from "./scene3d-camera";
import { veKhongGian } from "./scene3d-chart";
import { toVec3, type Scene3D, type Vec3 } from "./scene3d-model";
import { buildPedagogicalConstructionPlan, registerExactSceneOrigin, shortSym } from "./scene3d-semantic-policy";
import { withSubEntities } from "./scene3d-subentities";

function sampleRaw(id: string): { title: string; description: string; scene: Scene3D } {
  const s = GEOMETRY_SAMPLES.find((x) => x.id === id);
  if (!s) throw new Error(`Missing catalog sample: ${id}`);
  return {
    title: s.envelope.title ?? s.id,
    description: s.envelope.description ?? s.problemText ?? s.id,
    scene: (s.envelope as unknown as { scene3d: Scene3D }).scene3d,
  };
}

function prepareDisplayScene(raw: Scene3D): Scene3D {
  const sub = withSubEntities(raw);
  registerExactSceneOrigin(sub, raw);
  const plan = buildPedagogicalConstructionPlan(sub);
  return registerExactSceneOrigin(veKhongGian(plan.scene), plan.scene);
}


function projectToNdcTest(pt: Vec3, camPos: Vec3, camTarget: Vec3, fovDeg: number, aspect: number): [number, number] | null {
  const fwd: Vec3 = [camPos[0] - camTarget[0], camPos[1] - camTarget[1], camPos[2] - camTarget[2]];
  const dist = Math.hypot(fwd[0], fwd[1], fwd[2]);
  if (!(dist > 1e-9)) return null;
  const d: Vec3 = [fwd[0] / dist, fwd[1] / dist, fwd[2] / dist];
  const refUp: Vec3 = Math.abs(d[2]) > 0.999 ? [0, 1, 0] : [0, 0, 1];
  const rightRaw: Vec3 = [refUp[1] * d[2] - refUp[2] * d[1], refUp[2] * d[0] - refUp[0] * d[2], refUp[0] * d[1] - refUp[1] * d[0]];
  const rLen = Math.hypot(rightRaw[0], rightRaw[1], rightRaw[2]) || 1;
  const right: Vec3 = [rightRaw[0] / rLen, rightRaw[1] / rLen, rightRaw[2] / rLen];
  const up: Vec3 = [d[1] * right[2] - d[2] * right[1], d[2] * right[0] - d[0] * right[2], d[0] * right[1] - d[1] * right[0]];
  const rel: Vec3 = [pt[0] - camTarget[0], pt[1] - camTarget[1], pt[2] - camTarget[2]];
  const depth = dist - (rel[0] * d[0] + rel[1] * d[1] + rel[2] * d[2]);
  if (!(depth > 1e-6)) return null;
  const tanV = Math.tan((fovDeg * Math.PI) / 360);
  const tanH = tanV * aspect;
  return [(rel[0] * right[0] + rel[1] * right[1] + rel[2] * right[2]) / (depth * tanH), (rel[0] * up[0] + rel[1] * up[1] + rel[2] * up[2]) / (depth * tanV)];
}

function polygon2DAreaTest(pts: readonly [number, number][]): number {
  if (pts.length < 3) return 0;
  let s = 0;
  for (let i = 0; i < pts.length; i += 1) {
    const a = pts[i]!;
    const b = pts[(i + 1) % pts.length]!;
    s += a[0] * b[1] - b[0] * a[1];
  }
  return Math.abs(s) * 0.5;
}

function extractSampleContextAndOccluders(sampleId: string) {
  const raw = sampleRaw(sampleId).scene;
  const disp = prepareDisplayScene(raw);
  const solid = disp.objects.find((o) => o.type === "solid")!;
  const solidVerts = (solid.vertices ?? []).map(toVec3);
  const occluderMeshes: OccluderTriangleMesh[] = [{
    objectId: solid.id,
    vertices: solidVerts,
    triangles: (solid.faces ?? []).flatMap((f) => {
      const out: [number, number, number][] = [];
      for (let i = 1; i + 1 < f.length; i += 1) out.push([f[0]!, f[i]!, f[i + 1]!]);
      return out;
    }),
    isSolidFace: true,
  }];
  return { disp, solid, solidVerts, occluderMeshes };
}

describe("Smart Camera Locate Framing & Visibility", () => {
  it("8. computeSmartLocateCamera avoids grazing edge-on views on planes and sections while staying centered & outside meshes", () => {
    const contextPts: Vec3[] = [
      [0, 0, 0],
      [4, 0, 0],
      [4, 4, 0],
      [0, 4, 0],
      [0, 0, 4],
    ];
    const locatePlane = computeSmartLocateCamera({
      objectId: "P",
      objectKind: "plane",
      objectPoints: contextPts.slice(0, 4),
      objectNormal: [0, 0, 1],
      contextPoints: contextPts,
      currentPosition: [10, 2, 0.05],
      currentTarget: [2, 2, 0],
      fovDeg: 45,
      aspect: 16 / 10,
    });
    expect(locatePlane.status).toBe("located");
    expect(Math.abs(locatePlane.normalAlignment ?? 0)).toBeGreaterThanOrEqual(0.42);
    expect(Math.abs(locatePlane.targetNdc[0])).toBeLessThanOrEqual(0.88);
    expect(Math.abs(locatePlane.targetNdc[1])).toBeLessThanOrEqual(0.88);

    const secNorm: Vec3 = [1 / Math.SQRT2, 0, 1 / Math.SQRT2];
    const secPts: Vec3[] = [[0, 0, 2], [2, 0, 0], [2, 2, 0], [0, 2, 2]];
    const locateSec = computeSmartLocateCamera({
      objectId: "sec",
      objectKind: "section",
      objectPoints: secPts,
      objectNormal: secNorm,
      contextPoints: contextPts,
      currentPosition: [10, -8, 10],
      currentTarget: [1, 1, 1],
      fovDeg: 45,
      aspect: 16 / 10,
    });
    expect(Math.abs(locateSec.normalAlignment ?? 0)).toBeGreaterThanOrEqual(0.42);
  });

  it("9. computeSmartLocateCamera avoids severe foreshortening when locating a segment", () => {
    const contextPts: Vec3[] = [[0, 0, 0], [4, 0, 0], [0, 4, 0], [0, 0, 4]];
    const locateSeg = computeSmartLocateCamera({
      objectId: "SA",
      objectKind: "segment",
      objectPoints: [[0, 0, 0], [0, 0, 4]],
      contextPoints: contextPts,
      currentPosition: [0.05, 0.05, 12],
      currentTarget: [0, 0, 2],
      fovDeg: 45,
      aspect: 16 / 10,
    });
    expect(locateSeg.status).toBe("located");
    expect(locateSeg.segmentForeshorteningCos).not.toBeNull();
    expect(locateSeg.segmentForeshorteningCos ?? 1).toBeLessThanOrEqual(0.82);
  });

  it("10. computeSmartLocateCamera minimizes occlusion on interior/tangent objects and keeps camera outside solid & sphere meshes", () => {
    const boxVerts: Vec3[] = [
      [-1, -1, 0],
      [1, -1, 0],
      [1, 1, 0],
      [-1, 1, 0],
      [-1, -1, 2],
      [1, -1, 2],
      [1, 1, 2],
      [-1, 1, 2],
    ];
    const wallOccluder: OccluderTriangleMesh = {
      objectId: "wall",
      vertices: [[-2, 2, -2], [2, 2, -2], [2, 2, 2], [-2, 2, 2]],
      triangles: [[0, 1, 2], [0, 2, 3]],
      isSolidFace: true,
    };
    const resInterior = computeSmartLocateCamera({
      objectId: "H",
      objectKind: "point",
      objectPoints: [[0, 0, 1]],
      contextPoints: boxVerts,
      currentPosition: [0, 9, 1],
      currentTarget: [0, 0, 1],
      fovDeg: 45,
      aspect: 1.5,
      occluderMeshes: [wallOccluder],
      isInteriorOrTangent: true,
    });
    expect(resInterior.status).toBe("located");
    expect(resInterior.occludedRatio).toBeLessThan(0.5);
    expect(resInterior.minMarginToHostMesh).toBeGreaterThanOrEqual(0);

    const sphereOccluder: OccluderSphereMesh = {
      objectId: "ball",
      center: [0, 0, 0],
      radius: 3,
    };
    const resTangent = computeSmartLocateCamera({
      objectId: "T",
      objectKind: "curved_surface",
      objectPoints: [[0, 0, 3]],
      objectCenter: [0, 0, 0],
      contextPoints: [[0, 0, 3], [3, 0, 0], [-3, 0, 0], [0, 3, 0]],
      currentPosition: [0, 0, -9],
      currentTarget: [0, 0, 0],
      fovDeg: 45,
      aspect: 1.5,
      occluderSpheres: [sphereOccluder],
      isInteriorOrTangent: true,
    });
    expect(resTangent.status).toBe("located");
    expect(resTangent.minMarginToHostMesh).toBeGreaterThanOrEqual(0);
    expect(Math.hypot(...resTangent.position)).toBeGreaterThan(3);
  });

  it("11. computeSmartLocateCamera returns 'unchanged' when current view is already optimal and 'fallback_unchanged' on degenerate input", () => {
    const contextPts: Vec3[] = [[0, 0, 0], [4, 0, 0], [0, 4, 0], [0, 0, 4]];
    const first = computeSmartLocateCamera({
      objectId: "S",
      objectKind: "point",
      objectPoints: [[0, 0, 4]],
      contextPoints: contextPts,
      currentPosition: [12, 10, 9],
      currentTarget: [1, 1, 1],
      fovDeg: 45,
      aspect: 1.6,
    });
    expect(first.status).toBe("located");

    const second = computeSmartLocateCamera({
      objectId: "S",
      objectKind: "point",
      objectPoints: [[0, 0, 4]],
      contextPoints: contextPts,
      currentPosition: first.position,
      currentTarget: first.target,
      fovDeg: 45,
      aspect: 1.6,
    });
    expect(second.status).toBe("unchanged");
    expect(second.reason).toBe("current_view_already_optimal");

    const fbEmpty = computeSmartLocateCamera({
      objectId: "bad",
      objectKind: "point",
      objectPoints: [],
      contextPoints: contextPts,
      currentPosition: [8, 6, 5],
      currentTarget: [0, 0, 0],
      fovDeg: 45,
      aspect: 1.6,
    });
    expect(fbEmpty.status).toBe("fallback_unchanged");
    expect(fbEmpty.position).toEqual([8, 6, 5]);
  });

  it("12. V9.4.18 locating SA on chop-thiet-dien-ba-diem keeps all 5 S.ABCD vertices unclipped in NDC and avoids foreshortening", () => {
    const { disp, solidVerts, occluderMeshes } = extractSampleContextAndOccluders("chop-thiet-dien-ba-diem");
    const segSa = disp.objects.find((o) => o.id === "chieu_cao_SA")
      ?? disp.objects.find((o) => o.type === "segment3" && shortSym(o) === "SA")!;
    const saPts = (segSa.endpoints ?? []).map(toVec3);
    const fov = 45;
    const aspect = 16 / 10;
    const res = computeSmartLocateCamera({
      objectId: segSa.id,
      objectKind: "segment",
      objectPoints: saPts,
      contextPoints: solidVerts,
      currentPosition: [0.05, 0.05, 14],
      currentTarget: saPts[0]!,
      fovDeg: fov,
      aspect,
      occluderMeshes,
    });
    expect(res.status).toBe("located");
    expect(res.segmentForeshorteningCos ?? 1).toBeLessThanOrEqual(0.82);
    const projected = solidVerts.map((v) => projectToNdcTest(v, res.position, res.target, fov, aspect));
    for (const ndc of projected) {
      expect(ndc).not.toBeNull();
      expect(Math.abs(ndc![0])).toBeLessThanOrEqual(0.90);
      expect(Math.abs(ndc![1])).toBeLessThanOrEqual(0.90);
    }
    const xs = projected.map((p) => p![0]);
    const ys = projected.map((p) => p![1]);
    expect(Math.max(...xs) - Math.min(...xs)).toBeGreaterThan(0.18);
    expect(Math.max(...ys) - Math.min(...ys)).toBeGreaterThan(0.18);
  });

  it("13. V9.4.18 locating MENPF and MNEPFQ sections preserves normal alignment and non-collapsed 2D polygon area without solid-face grazing", () => {
    for (const sampleId of ["chop-thiet-dien-ba-diem", "lap-phuong-thiet-dien-bat-ky"]) {
      const { disp, solidVerts, occluderMeshes } = extractSampleContextAndOccluders(sampleId);
      const sec = disp.objects.find((o) => o.type === "section")!;
      const secPts = (sec.polygon ?? []).map(toVec3);
      const secPlane = disp.objects.find((o) => o.id === "mp_MNP" && o.normal);
      const nRaw = secPlane?.normal ? toVec3(secPlane.normal) : [0, 0, 1] as Vec3;
      const nLen = Math.hypot(...nRaw) || 1;
      const normal: Vec3 = [nRaw[0] / nLen, nRaw[1] / nLen, nRaw[2] / nLen];
      const fov = 45;
      const aspect = 16 / 10;
      const res = computeSmartLocateCamera({
        objectId: sec.id,
        objectKind: "section",
        objectPoints: secPts,
        objectNormal: normal,
        contextPoints: solidVerts,
        currentPosition: [11, 2, 1.5],
        currentTarget: [1.5, 1.5, 1.5],
        fovDeg: fov,
        aspect,
        occluderMeshes,
      });
      expect(res.status, sampleId).toBe("located");
      expect(Math.abs(res.normalAlignment ?? 0), sampleId).toBeGreaterThanOrEqual(0.42);
      const ndcPoly = secPts.map((p) => projectToNdcTest(p, res.position, res.target, fov, aspect)!);
      expect(polygon2DAreaTest(ndcPoly), sampleId).toBeGreaterThan(0.03);
      expect(res.minMarginToHostMesh, sampleId).toBeGreaterThanOrEqual(0);
    }
  });

  it("14. V9.4.18 re-calling computeSmartLocateCamera from located view on SA and MENPF returns unchanged", () => {
    const { disp, solidVerts, occluderMeshes } = extractSampleContextAndOccluders("chop-thiet-dien-ba-diem");
    const segSa = disp.objects.find((o) => o.id === "chieu_cao_SA")!;
    const sec = disp.objects.find((o) => o.type === "section")!;
    const secPlane = disp.objects.find((o) => o.id === "mp_MNP")!;
    const nRaw = toVec3(secPlane.normal!);
    const nLen = Math.hypot(...nRaw) || 1;
    const normal: Vec3 = [nRaw[0] / nLen, nRaw[1] / nLen, nRaw[2] / nLen];

    const firstSa = computeSmartLocateCamera({
      objectId: segSa.id, objectKind: "segment", objectPoints: (segSa.endpoints ?? []).map(toVec3),
      contextPoints: solidVerts, currentPosition: [11, 10, 14], currentTarget: [0, 0, 2], fovDeg: 45, aspect: 1.6, occluderMeshes,
    });
    expect(firstSa.status).toBe("located");
    const secondSa = computeSmartLocateCamera({
      objectId: segSa.id, objectKind: "segment", objectPoints: (segSa.endpoints ?? []).map(toVec3),
      contextPoints: solidVerts, currentPosition: firstSa.position, currentTarget: firstSa.target, fovDeg: 45, aspect: 1.6, occluderMeshes,
    });
    expect(secondSa.status).toBe("unchanged");
    expect(secondSa.reason).toBe("current_view_already_optimal");

    const firstSec = computeSmartLocateCamera({
      objectId: sec.id, objectKind: "section", objectPoints: (sec.polygon ?? []).map(toVec3), objectNormal: normal,
      contextPoints: solidVerts, currentPosition: [11, -7, 8], currentTarget: [1.5, 1.5, 1.5], fovDeg: 45, aspect: 1.6, occluderMeshes,
    });
    expect(firstSec.status).toBe("located");
    const secondSec = computeSmartLocateCamera({
      objectId: sec.id, objectKind: "section", objectPoints: (sec.polygon ?? []).map(toVec3), objectNormal: normal,
      contextPoints: solidVerts, currentPosition: firstSec.position, currentTarget: firstSec.target, fovDeg: 45, aspect: 1.6, occluderMeshes,
    });
    expect(secondSec.status).toBe("unchanged");
    expect(secondSec.reason).toBe("current_view_already_optimal");
  });
});
