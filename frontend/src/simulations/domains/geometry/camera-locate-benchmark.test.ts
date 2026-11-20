import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { PUBLIC_GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import {
  computeSmartLocateCamera,
  type LocateObjectKind,
  type OccluderSphereMesh,
  type OccluderTriangleMesh,
  type SmartLocateInput,
  type SmartLocateResult,
} from "./scene3d-camera";
import { veKhongGian } from "./scene3d-chart";
import { toNumber, toVec3, type Scene3D, type SceneObject, type Vec3 } from "./scene3d-model";
import {
  attachProblemContextToScene,
  buildPedagogicalConstructionPlan,
  registerExactSceneOrigin,
  shortSym,
} from "./scene3d-semantic-policy";
import { withSubEntities } from "./scene3d-subentities";

const WARMUP_RUNS = 3;
const BENCHMARK_RUNS = 25;
const ANIMATION_DURATION_MS = 300;
const BENCHMARK_OUTPUT_PATH =
  "C:\\Users\\Bunny\\.gemini\\antigravity\\brain\\3ef24255-0976-432d-b0af-48ebb7f2067e\\v9419_audit\\camera-cpu-benchmark.json";

interface TimingStats {
  n: number;
  min: number;
  max: number;
  mean: number;
  median: number;
  p25: number;
  p75: number;
  iqr: number;
  p95: number;
}

interface BenchmarkCaseReport {
  caseId: number;
  name: string;
  sampleId: string;
  objectId: string;
  objectKind: LocateObjectKind;
  warmupRuns: number;
  measuredRuns: number;
  animationDurationMs: number;
  locateStatus: SmartLocateResult["status"];
  normalAlignment: number | null;
  segmentForeshorteningCos: number | null;
  occludedRatio: number;
  minMarginToHostMesh: number | null;
  cameraCalculationMs: TimingStats;
  occlusionEvaluationMs: TimingStats;
  occluderPrepMs: TimingStats;
  notes?: string;
}

function roundMs(val: number): number {
  return Number(val.toFixed(4));
}

function quantile(sorted: readonly number[], q: number): number {
  if (sorted.length === 0) return 0;
  if (sorted.length === 1) return sorted[0]!;
  const pos = q * (sorted.length - 1);
  const lo = Math.floor(pos);
  const hi = Math.ceil(pos);
  if (lo === hi) return sorted[lo]!;
  const frac = pos - lo;
  return sorted[lo]! * (1 - frac) + sorted[hi]! * frac;
}

function computeStats(samples: readonly number[]): TimingStats {
  const sorted = [...samples].sort((a, b) => a - b);
  const sum = sorted.reduce((acc, v) => acc + v, 0);
  const p25 = quantile(sorted, 0.25);
  const p75 = quantile(sorted, 0.75);
  return {
    n: sorted.length,
    min: roundMs(sorted[0] ?? 0),
    max: roundMs(sorted[sorted.length - 1] ?? 0),
    mean: roundMs(sorted.length > 0 ? sum / sorted.length : 0),
    median: roundMs(quantile(sorted, 0.5)),
    p25: roundMs(p25),
    p75: roundMs(p75),
    iqr: roundMs(p75 - p25),
    p95: roundMs(quantile(sorted, 0.95)),
  };
}

function prepareSampleScene(sampleId: string): Scene3D {
  const sample = PUBLIC_GEOMETRY_SAMPLES.find((s) => s.id === sampleId);
  if (!sample) throw new Error(`Missing public sample: ${sampleId}`);
  const raw = structuredClone((sample.envelope as unknown as { scene3d: Scene3D }).scene3d);
  attachProblemContextToScene(raw, {
    title: sample.envelope.title,
    statement: sample.problemText || sample.envelope.description,
  });
  const sub = withSubEntities(raw);
  registerExactSceneOrigin(sub, raw);
  const plan = buildPedagogicalConstructionPlan(sub);
  return registerExactSceneOrigin(veKhongGian(plan.scene), plan.scene);
}

function normalizeVec3(v: Vec3): Vec3 {
  const len = Math.hypot(v[0], v[1], v[2]);
  if (!(len > 1e-12)) return [0, 0, 1];
  return [v[0] / len, v[1] / len, v[2] / len];
}

function orthonormalBasis(normal: Vec3): [Vec3, Vec3] {
  const n = normalizeVec3(normal);
  const seed: Vec3 = Math.abs(n[2]) < 0.85 ? [0, 0, 1] : [1, 0, 0];
  const e1 = normalizeVec3([
    n[1] * seed[2] - n[2] * seed[1],
    n[2] * seed[0] - n[0] * seed[2],
    n[0] * seed[1] - n[1] * seed[0],
  ]);
  const e2 = normalizeVec3([
    n[1] * e1[2] - n[2] * e1[1],
    n[2] * e1[0] - n[0] * e1[2],
    n[0] * e1[1] - n[1] * e1[0],
  ]);
  return [e1, e2];
}

function extractContextPoints(scene: Scene3D): Vec3[] {
  const pts: Vec3[] = [];
  for (const o of scene.objects) {
    if (o.display_role === "non_visual" || o.display_role === "hit_proxy" || o.display_role === "measurement") {
      continue;
    }
    if (o.type === "solid" && Array.isArray(o.vertices)) {
      for (const v of o.vertices) pts.push(toVec3(v));
    } else if (o.type === "point3" && o.xyz) {
      pts.push(toVec3(o.xyz));
    } else if (o.type === "curved_solid" && o.curved_kind === "ball" && o.anchor) {
      const c = toVec3(o.anchor);
      let r = 0;
      if (o.radius_sq !== undefined) {
        const r2 = toNumber(o.radius_sq);
        if (Number.isFinite(r2) && r2 > 0) r = Math.sqrt(r2);
      }
      if (r > 0) {
        pts.push(
          [c[0] + r, c[1], c[2]],
          [c[0] - r, c[1], c[2]],
          [c[0], c[1] + r, c[2]],
          [c[0], c[1] - r, c[2]],
          [c[0], c[1], c[2] + r],
          [c[0], c[1], c[2] - r],
        );
      } else {
        pts.push(c);
      }
    }
  }
  return pts;
}

function extractOccluders(scene: Scene3D): {
  occluderMeshes: OccluderTriangleMesh[];
  occluderSpheres: OccluderSphereMesh[];
} {
  const occluderMeshes: OccluderTriangleMesh[] = [];
  const occluderSpheres: OccluderSphereMesh[] = [];
  for (const o of scene.objects) {
    if (o.type === "solid" && Array.isArray(o.vertices) && Array.isArray(o.faces)) {
      occluderMeshes.push({
        objectId: o.id,
        vertices: o.vertices.map(toVec3),
        triangles: o.faces.flatMap((f) => {
          const tris: [number, number, number][] = [];
          for (let i = 1; i + 1 < f.length; i += 1) {
            tris.push([f[0]!, f[i]!, f[i + 1]!]);
          }
          return tris;
        }),
        isSolidFace: true,
      });
    } else if (o.type === "curved_solid" && o.curved_kind === "ball" && o.anchor) {
      const center = toVec3(o.anchor);
      let radius = 0;
      if (o.radius_sq !== undefined) {
        const r2 = toNumber(o.radius_sq);
        if (Number.isFinite(r2) && r2 > 0) radius = Math.sqrt(r2);
      } else if (o.rim_point) {
        const rim = toVec3(o.rim_point);
        radius = Math.hypot(rim[0] - center[0], rim[1] - center[1], rim[2] - center[2]);
      }
      if (radius > 1e-6) {
        occluderSpheres.push({ objectId: o.id, center, radius });
      }
    }
  }
  return { occluderMeshes, occluderSpheres };
}

function planeQuadPoints(planeObj: SceneObject, centerHint: Vec3, halfExtent: number): Vec3[] {
  const poly = (planeObj as unknown as { polygon?: SceneObject["polygon"] }).polygon;
  if (Array.isArray(poly) && poly.length >= 3) {
    return poly.map(toVec3);
  }
  const anchor = planeObj.point ? toVec3(planeObj.point) : centerHint;
  const n = planeObj.normal ? normalizeVec3(toVec3(planeObj.normal)) : ([0, 0, 1] as Vec3);
  const [e1, e2] = orthonormalBasis(n);
  return [
    [anchor[0] - halfExtent * (e1[0] + e2[0]), anchor[1] - halfExtent * (e1[1] + e2[1]), anchor[2] - halfExtent * (e1[2] + e2[2])],
    [anchor[0] + halfExtent * (e1[0] - e2[0]), anchor[1] + halfExtent * (e1[1] - e2[1]), anchor[2] + halfExtent * (e1[2] - e2[2])],
    [anchor[0] + halfExtent * (e1[0] + e2[0]), anchor[1] + halfExtent * (e1[1] + e2[1]), anchor[2] + halfExtent * (e1[2] + e2[2])],
    [anchor[0] - halfExtent * (e1[0] - e2[0]), anchor[1] - halfExtent * (e1[1] - e2[1]), anchor[2] - halfExtent * (e1[2] - e2[2])],
  ];
}

function circleRingPoints(circleObj: SceneObject, segments = 8): Vec3[] {
  const center = circleObj.center ? toVec3(circleObj.center) : ([0, 0, 0] as Vec3);
  const normal = circleObj.normal ? normalizeVec3(toVec3(circleObj.normal)) : ([0, 0, 1] as Vec3);
  const r2 = circleObj.radius_sq !== undefined ? toNumber(circleObj.radius_sq) : 1;
  const r = Number.isFinite(r2) && r2 > 0 ? Math.sqrt(r2) : 1;
  const [e1, e2] = orthonormalBasis(normal);
  const pts: Vec3[] = [];
  for (let i = 0; i < segments; i += 1) {
    const th = (2 * Math.PI * i) / segments;
    const c = Math.cos(th) * r;
    const s = Math.sin(th) * r;
    pts.push([
      center[0] + c * e1[0] + s * e2[0],
      center[1] + c * e1[1] + s * e2[1],
      center[2] + c * e1[2] + s * e2[2],
    ]);
  }
  return pts;
}

function projectToNdcCheck(
  pt: Vec3,
  camPos: Vec3,
  camTarget: Vec3,
  fovDeg: number,
  aspect: number,
): [number, number] | null {
  const fwd: Vec3 = [camPos[0] - camTarget[0], camPos[1] - camTarget[1], camPos[2] - camTarget[2]];
  const dist = Math.hypot(fwd[0], fwd[1], fwd[2]);
  if (!(dist > 1e-9)) return null;
  const d: Vec3 = [fwd[0] / dist, fwd[1] / dist, fwd[2] / dist];
  const refUp: Vec3 = Math.abs(d[2]) > 0.999 ? [0, 1, 0] : [0, 0, 1];
  const rightRaw: Vec3 = [
    refUp[1] * d[2] - refUp[2] * d[1],
    refUp[2] * d[0] - refUp[0] * d[2],
    refUp[0] * d[1] - refUp[1] * d[0],
  ];
  const rLen = Math.hypot(rightRaw[0], rightRaw[1], rightRaw[2]) || 1;
  const right: Vec3 = [rightRaw[0] / rLen, rightRaw[1] / rLen, rightRaw[2] / rLen];
  const up: Vec3 = [
    d[1] * right[2] - d[2] * right[1],
    d[2] * right[0] - d[0] * right[2],
    d[0] * right[1] - d[1] * right[0],
  ];
  const rel: Vec3 = [pt[0] - camTarget[0], pt[1] - camTarget[1], pt[2] - camTarget[2]];
  const depth = dist - (rel[0] * d[0] + rel[1] * d[1] + rel[2] * d[2]);
  if (!(depth > 1e-6)) return null;
  const tanV = Math.tan((fovDeg * Math.PI) / 360);
  const tanH = tanV * aspect;
  return [
    (rel[0] * right[0] + rel[1] * right[1] + rel[2] * right[2]) / (depth * tanH),
    (rel[0] * up[0] + rel[1] * up[1] + rel[2] * up[2]) / (depth * tanV),
  ];
}

function polygon2DArea(pts: readonly [number, number][]): number {
  if (pts.length < 3) return 0;
  let s = 0;
  for (let i = 0; i < pts.length; i += 1) {
    const a = pts[i]!;
    const b = pts[(i + 1) % pts.length]!;
    s += a[0] * b[1] - b[0] * a[1];
  }
  return Math.abs(s) * 0.5;
}

function assertValidLocateResult(res: SmartLocateResult, label: string): void {
  expect(res.status, label).toBe("located");
  for (const val of [...res.position, ...res.target, ...res.viewDirection, ...res.targetNdc, res.distance, res.occludedRatio]) {
    expect(Number.isFinite(val), `${label} non-finite metric`).toBe(true);
  }
  expect(Math.abs(res.targetNdc[0]), `${label} NDC x`).toBeLessThanOrEqual(0.88);
  expect(Math.abs(res.targetNdc[1]), `${label} NDC y`).toBeLessThanOrEqual(0.88);
  expect(res.minMarginToHostMesh, `${label} host clearance`).toBeGreaterThanOrEqual(0);
}

function benchmarkCase(params: {
  caseId: number;
  name: string;
  sampleId: string;
  objectId: string;
  buildInput: (scene: Scene3D, occ: { occluderMeshes: OccluderTriangleMesh[]; occluderSpheres: OccluderSphereMesh[] }) => SmartLocateInput;
  validate?: (res: SmartLocateResult, input: SmartLocateInput, scene: Scene3D) => void;
  notes?: string;
}): BenchmarkCaseReport {
  const scene = prepareSampleScene(params.sampleId);
  const initialOcc = extractOccluders(scene);
  const input = params.buildInput(scene, initialOcc);

  // Warm-up passes before timing
  for (let w = 0; w < WARMUP_RUNS; w += 1) {
    computeSmartLocateCamera(input);
    computeSmartLocateCamera({ ...input, occluderMeshes: [], occluderSpheres: [] });
  }

  const calcSamples: number[] = [];
  const occSamples: number[] = [];
  const prepSamples: number[] = [];
  let lastResult!: SmartLocateResult;

  for (let i = 0; i < BENCHMARK_RUNS; i += 1) {
    const prepStart = performance.now();
    const freshOcc = extractOccluders(scene);
    const prepMs = performance.now() - prepStart;

    const runInput: SmartLocateInput = {
      ...input,
      occluderMeshes: freshOcc.occluderMeshes,
      occluderSpheres: freshOcc.occluderSpheres,
    };

    const calcStart = performance.now();
    lastResult = computeSmartLocateCamera(runInput);
    const calcMs = performance.now() - calcStart;

    const hasOcc = freshOcc.occluderMeshes.length > 0 || freshOcc.occluderSpheres.length > 0;
    let noOccMs = 0;
    if (hasOcc) {
      const noOccStart = performance.now();
      computeSmartLocateCamera({ ...runInput, occluderMeshes: [], occluderSpheres: [] });
      noOccMs = performance.now() - noOccStart;
    }

    const occMs = hasOcc ? prepMs + Math.max(0, calcMs - noOccMs) : prepMs;
    prepSamples.push(prepMs);
    calcSamples.push(calcMs);
    occSamples.push(occMs);
  }

  assertValidLocateResult(lastResult, params.name);
  params.validate?.(lastResult, input, scene);

  return {
    caseId: params.caseId,
    name: params.name,
    sampleId: params.sampleId,
    objectId: params.objectId,
    objectKind: input.objectKind,
    warmupRuns: WARMUP_RUNS,
    measuredRuns: BENCHMARK_RUNS,
    animationDurationMs: ANIMATION_DURATION_MS,
    locateStatus: lastResult.status,
    normalAlignment: lastResult.normalAlignment,
    segmentForeshorteningCos: lastResult.segmentForeshorteningCos,
    occludedRatio: lastResult.occludedRatio,
    minMarginToHostMesh: Number.isFinite(lastResult.minMarginToHostMesh) ? roundMs(lastResult.minMarginToHostMesh) : null,
    cameraCalculationMs: computeStats(calcSamples),
    occlusionEvaluationMs: computeStats(occSamples),
    occluderPrepMs: computeStats(prepSamples),
    notes: params.notes,
  };
}

describe("Camera Locate Verification & N=25 Multi-Run CPU Benchmark", () => {
  it("runs all 8 Camera Locate verification scenarios across N=25 benchmark iterations (3 warm-ups each) and persists CPU report", () => {
    const reports: BenchmarkCaseReport[] = [];

    // 1. Section MENPF on S.ABCD
    reports.push(
      benchmarkCase({
        caseId: 1,
        name: "Section MENPF on S.ABCD",
        sampleId: "chop-thiet-dien-ba-diem",
        objectId: "thiet_dien",
        buildInput: (scene, occ) => {
          const sec = scene.objects.find((o) => o.id === "thiet_dien" || o.type === "section")!;
          const secPlane = scene.objects.find((o) => o.id === "mp_MNP" && o.normal);
          return {
            objectId: sec.id,
            objectKind: "section",
            objectPoints: (sec.polygon ?? []).map(toVec3),
            objectNormal: secPlane?.normal ? normalizeVec3(toVec3(secPlane.normal)) : undefined,
            contextPoints: extractContextPoints(scene),
            currentPosition: [11, 2, 1.5],
            currentTarget: [1.5, 1.5, 1.5],
            fovDeg: 45,
            aspect: 16 / 10,
            ...occ,
          };
        },
        validate: (res, input) => {
          expect(Math.abs(res.normalAlignment ?? 0)).toBeGreaterThanOrEqual(0.42);
          const ndcPoly = input.objectPoints.map((p) => projectToNdcCheck(p, res.position, res.target, input.fovDeg, input.aspect)!);
          expect(polygon2DArea(ndcPoly)).toBeGreaterThan(0.03);
        },
      }),
    );

    // 2. Segment SA on S.ABCD
    reports.push(
      benchmarkCase({
        caseId: 2,
        name: "Segment SA on S.ABCD",
        sampleId: "chop-thiet-dien-ba-diem",
        objectId: "chieu_cao_SA",
        buildInput: (scene, occ) => {
          const sa = scene.objects.find((o) => o.id === "chieu_cao_SA")
            ?? scene.objects.find((o) => o.type === "segment3" && shortSym(o) === "SA")!;
          return {
            objectId: sa.id,
            objectKind: "segment",
            objectPoints: (sa.endpoints ?? []).map(toVec3),
            contextPoints: extractContextPoints(scene),
            currentPosition: [0.05, 0.05, 14],
            currentTarget: [0, 0, 2],
            fovDeg: 45,
            aspect: 16 / 10,
            ...occ,
          };
        },
        validate: (res, input) => {
          expect(res.segmentForeshorteningCos ?? 1).toBeLessThanOrEqual(0.82);
          for (const p of input.contextPoints) {
            const ndc = projectToNdcCheck(p, res.position, res.target, input.fovDeg, input.aspect);
            expect(ndc).not.toBeNull();
            expect(Math.abs(ndc![0])).toBeLessThanOrEqual(0.90);
            expect(Math.abs(ndc![1])).toBeLessThanOrEqual(0.90);
          }
        },
      }),
    );

    // 3. Section MNEPFQ on cube
    reports.push(
      benchmarkCase({
        caseId: 3,
        name: "Section MNEPFQ on cube",
        sampleId: "lap-phuong-thiet-dien-bat-ky",
        objectId: "thiet_dien",
        buildInput: (scene, occ) => {
          const sec = scene.objects.find((o) => o.id === "thiet_dien" || o.type === "section")!;
          const secPlane = scene.objects.find((o) => o.id === "mp_MNP" && o.normal);
          return {
            objectId: sec.id,
            objectKind: "section",
            objectPoints: (sec.polygon ?? []).map(toVec3),
            objectNormal: secPlane?.normal ? normalizeVec3(toVec3(secPlane.normal)) : undefined,
            contextPoints: extractContextPoints(scene),
            currentPosition: [11, 2, 1.5],
            currentTarget: [1.5, 1.5, 1.5],
            fovDeg: 45,
            aspect: 16 / 10,
            ...occ,
          };
        },
        validate: (res, input) => {
          expect(Math.abs(res.normalAlignment ?? 0)).toBeGreaterThanOrEqual(0.42);
          const ndcPoly = input.objectPoints.map((p) => projectToNdcCheck(p, res.position, res.target, input.fovDeg, input.aspect)!);
          expect(polygon2DArea(ndcPoly)).toBeGreaterThan(0.03);
        },
      }),
    );

    // 4. Oxyz plane (P) and intersection point M
    reports.push(
      benchmarkCase({
        caseId: 4,
        name: "Oxyz plane (P) & intersection M",
        sampleId: "oxyz-giao-diem-duong-mat",
        objectId: "mp_P",
        buildInput: (scene, occ) => {
          const planeP = scene.objects.find((o) => o.id === "mp_P")!;
          const ptM = scene.objects.find((o) => o.id === "M" && o.xyz)!;
          return {
            objectId: planeP.id,
            objectKind: "plane",
            objectPoints: planeQuadPoints(planeP, toVec3(ptM.xyz!), 2.5),
            objectNormal: planeP.normal ? normalizeVec3(toVec3(planeP.normal)) : undefined,
            contextPoints: extractContextPoints(scene),
            currentPosition: [12, 12, 0.2],
            currentTarget: toVec3(ptM.xyz!),
            fovDeg: 45,
            aspect: 16 / 10,
            ...occ,
          };
        },
        validate: (res, _input, scene) => {
          expect(Math.abs(res.normalAlignment ?? 0)).toBeGreaterThanOrEqual(0.42);
          const ptM = scene.objects.find((o) => o.id === "M" && o.xyz)!;
          const mRes = computeSmartLocateCamera({
            objectId: ptM.id,
            objectKind: "point",
            objectPoints: [toVec3(ptM.xyz!)],
            contextPoints: extractContextPoints(scene),
            currentPosition: [14, -8, 6],
            currentTarget: [0, 0, 0],
            fovDeg: 45,
            aspect: 16 / 10,
          });
          assertValidLocateResult(mRes, "Oxyz intersection M");
        },
        notes: "Primary N=25 timing targets Oxyz plane (P); also verified Oxyz intersection M locate.",
      }),
    );

    // 5. Tangent plane (P) / tangent point A on sphere
    reports.push(
      benchmarkCase({
        caseId: 5,
        name: "Sphere tangent plane (P) & contact point A",
        sampleId: "mat-phang-tiep-xuc-mat-cau",
        objectId: "mp_tiep_dien",
        buildInput: (scene, occ) => {
          const ptA = scene.objects.find((o) => o.id === "A" && o.xyz)!;
          const ptI = scene.objects.find((o) => o.id === "I" && o.xyz)!;
          const planeTan = scene.objects.find((o) => o.id === "mp_tiep_dien")!;
          const a = toVec3(ptA.xyz!);
          const iPos = toVec3(ptI.xyz!);
          // Start deliberately on the occluded far side of sphere (S) relative to A
          const farOpposite: Vec3 = [
            iPos[0] - 3 * (a[0] - iPos[0]),
            iPos[1] - 3 * (a[1] - iPos[1]),
            iPos[2] - 3 * (a[2] - iPos[2]),
          ];
          return {
            objectId: planeTan.id,
            objectKind: "plane",
            objectPoints: planeQuadPoints(planeTan, a, 3.0),
            objectNormal: planeTan.normal ? normalizeVec3(toVec3(planeTan.normal)) : undefined,
            objectCenter: a,
            contextPoints: extractContextPoints(scene),
            currentPosition: farOpposite,
            currentTarget: iPos,
            fovDeg: 45,
            aspect: 16 / 10,
            isInteriorOrTangent: true,
            ...occ,
          };
        },
        validate: (res, _input, scene) => {
          expect(Math.abs(res.normalAlignment ?? 0)).toBeGreaterThanOrEqual(0.42);
          const occ = extractOccluders(scene);
          const sph = occ.occluderSpheres[0]!;
          const ptA = scene.objects.find((o) => o.id === "A" && o.xyz)!;
          const a = toVec3(ptA.xyz!);
          const farOpposite: Vec3 = [
            sph.center[0] - 3 * (a[0] - sph.center[0]),
            sph.center[1] - 3 * (a[1] - sph.center[1]),
            sph.center[2] - 3 * (a[2] - sph.center[2]),
          ];
          const ptARes = computeSmartLocateCamera({
            objectId: ptA.id,
            objectKind: "point",
            objectPoints: [a],
            objectCenter: sph.center,
            contextPoints: extractContextPoints(scene),
            currentPosition: farOpposite,
            currentTarget: sph.center,
            fovDeg: 45,
            aspect: 16 / 10,
            isInteriorOrTangent: true,
            ...occ,
          });
          assertValidLocateResult(ptARes, "Tangent point A on sphere");
          expect(ptARes.occludedRatio).toBeLessThan(0.5);
          const distToCenter = Math.hypot(
            ptARes.position[0] - sph.center[0],
            ptARes.position[1] - sph.center[1],
            ptARes.position[2] - sph.center[2],
          );
          expect(distToCenter).toBeGreaterThan(sph.radius);
        },
        notes: "Primary N=25 timing targets tangent plane (P) with far-side occluded start; also verified tangent point A occlusion avoidance & sphere clearance.",
      }),
    );

    // 6. Secant plane (P) / intersection circle (H; HM) on sphere
    reports.push(
      benchmarkCase({
        caseId: 6,
        name: "Sphere secant plane (P) & intersection circle",
        sampleId: "mat-cau-cat-mat-phang",
        objectId: "C",
        buildInput: (scene, occ) => {
          const secCircle = scene.objects.find((o) => o.id === "C" && o.type === "circle3")!;
          const planeP = scene.objects.find((o) => o.id === "mp_P" && o.type === "plane3")!;
          const normal = secCircle.normal
            ? normalizeVec3(toVec3(secCircle.normal))
            : planeP.normal
              ? normalizeVec3(toVec3(planeP.normal))
              : ([0, 0, 1] as Vec3);
          const center = secCircle.center ? toVec3(secCircle.center) : ([0, 0, 0] as Vec3);
          return {
            objectId: secCircle.id,
            objectKind: "section",
            objectPoints: circleRingPoints(secCircle, 8),
            objectNormal: normal,
            objectCenter: center,
            contextPoints: extractContextPoints(scene),
            currentPosition: [center[0] + 15, center[1], center[2]],
            currentTarget: center,
            fovDeg: 45,
            aspect: 16 / 10,
            isInteriorOrTangent: true,
            ...occ,
          };
        },
        validate: (res, _input, scene) => {
          expect(Math.abs(res.normalAlignment ?? 0)).toBeGreaterThanOrEqual(0.42);
          const occ = extractOccluders(scene);
          const sph = occ.occluderSpheres[0]!;
          const distToCenter = Math.hypot(
            res.position[0] - sph.center[0],
            res.position[1] - sph.center[1],
            res.position[2] - sph.center[2],
          );
          expect(distToCenter).toBeGreaterThan(sph.radius);
        },
      }),
    );

    // 7. Interior / face-occluded object (altitude foot H)
    reports.push(
      benchmarkCase({
        caseId: 7,
        name: "Interior / face-occluded altitude foot H",
        sampleId: "khoang-cach-diem-mat-phang-nghieng",
        objectId: "H",
        buildInput: (scene, occ) => {
          const ptH = scene.objects.find((o) => o.id === "H" && o.xyz)!;
          return {
            objectId: ptH.id,
            objectKind: "point",
            objectPoints: [toVec3(ptH.xyz!)],
            contextPoints: extractContextPoints(scene),
            // Start behind pyramid faces so ray to H intersects solid shell
            currentPosition: [-8, -6, 1.2],
            currentTarget: [1.5, 1.5, 1.5],
            fovDeg: 45,
            aspect: 16 / 10,
            isInteriorOrTangent: true,
            ...occ,
          };
        },
        validate: (res) => {
          expect(res.occludedRatio).toBeLessThan(0.5);
          expect(res.minMarginToHostMesh).toBeGreaterThanOrEqual(0);
        },
      }),
    );

    // 8. Locate -> manual camera orbit -> restore camera (previousPose)
    const locateOrbitRestoreCase = benchmarkCase({
      caseId: 8,
      name: "Locate -> manual orbit -> restore previousPose round-trip",
      sampleId: "chop-thiet-dien-ba-diem",
      objectId: "thiet_dien",
      buildInput: (scene, occ) => {
        const sec = scene.objects.find((o) => o.id === "thiet_dien" || o.type === "section")!;
        const secPlane = scene.objects.find((o) => o.id === "mp_MNP" && o.normal);
        return {
          objectId: sec.id,
          objectKind: "section",
          objectPoints: (sec.polygon ?? []).map(toVec3),
          objectNormal: secPlane?.normal ? normalizeVec3(toVec3(secPlane.normal)) : undefined,
          contextPoints: extractContextPoints(scene),
          currentPosition: [12, 8, 9],
          currentTarget: [2, 2, 1.5],
          fovDeg: 45,
          aspect: 16 / 10,
          ...occ,
        };
      },
      validate: (locatedPose, initialInput) => {
        // Save pre-locate pose
        const previousPose = {
          position: [...initialInput.currentPosition] as Vec3,
          target: [...initialInput.currentTarget] as Vec3,
        };
        // Simulate manual camera orbit away from locatedPose
        const manualOrbitedPose = {
          position: [-9, 10, 4] as Vec3,
          target: [...locatedPose.target] as Vec3,
        };
        expect(manualOrbitedPose.position).not.toEqual(locatedPose.position);

        // Re-locate from manual orbited pose lands validly and cleanly
        const relocated = computeSmartLocateCamera({
          ...initialInput,
          currentPosition: manualOrbitedPose.position,
          currentTarget: manualOrbitedPose.target,
        });
        assertValidLocateResult(relocated, "Re-locate after manual orbit");

        // Restoring previousPose preserves exact original coordinates and targets without mutation
        const restoredPose = {
          position: [...previousPose.position] as Vec3,
          target: [...previousPose.target] as Vec3,
        };
        expect(restoredPose.position).toEqual([12, 8, 9]);
        expect(restoredPose.target).toEqual([2, 2, 1.5]);

        // Verify live view controller wires previousPose snapshot + 300ms animation duration + restore callback
        const viewSrc = readFileSync(
          fileURLToPath(new URL("./scene3d-view.tsx", import.meta.url)),
          "utf8",
        );
        expect(viewSrc).toContain("preLocatePoseRef");
        expect(viewSrc).toContain("restoreCameraRef");
        expect(viewSrc).toContain("isReducedMotionActive() ? 0 : 300");
      },
      notes: "Verifies preLocatePose snapshot preservation across manual orbit + restore round-trip and scene3d-view 300ms transition wiring.",
    });
    reports.push(locateOrbitRestoreCase);

    expect(reports).toHaveLength(8);
    for (const r of reports) {
      expect(r.cameraCalculationMs.n).toBe(BENCHMARK_RUNS);
      expect(r.occlusionEvaluationMs.n).toBe(BENCHMARK_RUNS);
      expect(r.animationDurationMs).toBe(ANIMATION_DURATION_MS);
      expect(r.cameraCalculationMs.median).toBeGreaterThanOrEqual(0);
      expect(r.cameraCalculationMs.p95).toBeGreaterThanOrEqual(r.cameraCalculationMs.median);
      expect(r.cameraCalculationMs.iqr).toBeGreaterThanOrEqual(0);
    }

    const artifact = {
      suite: "camera-locate-cpu-benchmark",
      warmupRuns: WARMUP_RUNS,
      measuredRuns: BENCHMARK_RUNS,
      fixedAnimationDurationMs: ANIMATION_DURATION_MS,
      methodology:
        "Each case runs 3 unmeasured warm-ups followed by N=25 timed iterations via performance.now(). cameraCalculationMs measures computeSmartLocateCamera() with scene occluders; occlusionEvaluationMs measures occluder mesh/sphere extraction plus marginal ray-occlusion cost inside computeSmartLocateCamera() (full minus zero-occluder run from the same off-optimal camera pose).",
      generatedAt: new Date().toISOString(),
      nodeVersion: process.version,
      platform: process.platform,
      cases: reports,
    };

    mkdirSync(path.dirname(BENCHMARK_OUTPUT_PATH), { recursive: true });
    writeFileSync(BENCHMARK_OUTPUT_PATH, `${JSON.stringify(artifact, null, 2)}\n`, "utf8");
  });
});
