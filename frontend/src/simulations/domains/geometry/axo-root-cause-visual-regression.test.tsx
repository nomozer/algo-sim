import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import * as THREE from "three";
import type { Exact, ExactVec3, Scene3D, SceneObject } from "./scene3d-model";
import { objectsAt, registerExactSceneOrigin, tapKetQuaCuoi, toVec3 } from "./scene3d-model";
import { veKhongGian } from "./scene3d-chart";
import { withSubEntities } from "./scene3d-subentities";
import {
  annotationsAt,
  DEFAULT_ANNOTATION_VIEW,
  type AnnotationView,
} from "./scene3d-annotations";
import { dongBoNetDayManHinh } from "./scene3d-edge-visibility";
import {
  buildObject3D,
  datCoGocVuong,
  toSangCanhChuan,
} from "./scene3d-view";
import { vaiTroMien } from "./scene3d-roles";
import { evaluateStudentPresentationPolicy } from "./scene3d-student-presentation-policy";
import {
  buildPedagogicalConstructionPlan,
  buildStepEntityGroups,
  inspectAxialCurvedOrthogonality,
  resolveSemanticObjectContract,
  resolveSolidFaceDuplicateCarrierPolygons,
  shouldShowSphereReferenceEquator,
  verifySceneMathematicalConsistency,
} from "./scene3d-semantic-policy";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";

const SAMPLES_RAW = JSON.parse(
  readFileSync(join(__dirname, "..", "..", "..", "data", "geometry-samples.json"), "utf8"),
) as { samples: { id: string; problemText: string; envelope: { title: string; scene3d: Scene3D } }[] };

function loadSample(id: string) {
  const found = SAMPLES_RAW.samples.find((s) => s.id === id);
  if (!found) throw new Error(`Missing sample ${id}`);
  return {
    title: found.envelope.title,
    problemText: found.problemText,
    scene: JSON.parse(JSON.stringify(found.envelope.scene3d)) as Scene3D,
  };
}

function parseQ(s: Exact): [bigint, bigint] {
  const str = String(s).trim();
  const slash = str.indexOf("/");
  if (slash >= 0) {
    return [BigInt(str.slice(0, slash)), BigInt(str.slice(slash + 1))];
  }
  return [BigInt(str), 1n];
}

function gcdBig(a: bigint, b: bigint): bigint {
  let x = a < 0n ? -a : a;
  let y = b < 0n ? -b : b;
  while (y !== 0n) {
    const t = x % y;
    x = y;
    y = t;
  }
  return x === 0n ? 1n : x;
}

function fmtQ(num: bigint, den: bigint): string {
  const s = den < 0n ? -1n : 1n;
  const n = num * s;
  const d = den * s;
  if (n === 0n) return "0";
  const g = gcdBig(n, d);
  const rn = n / g;
  const rd = d / g;
  return rd === 1n ? rn.toString() : `${rn.toString()}/${rd.toString()}`;
}

function addVecQ(v: ExactVec3, delta: [bigint, bigint, bigint]): ExactVec3 {
  return [0, 1, 2].map((i) => {
    const [n, d] = parseQ(v[i]);
    return fmtQ(n + delta[i] * d, d);
  }) as ExactVec3;
}

function rotZ90VecQ(v: ExactVec3): ExactVec3 {
  const [nx, dx] = parseQ(v[0]);
  const [ny, dy] = parseQ(v[1]);
  return [fmtQ(-ny, dy), fmtQ(nx, dx), String(v[2])];
}

function scaleVecQ(v: ExactVec3, k: bigint): ExactVec3 {
  return [0, 1, 2].map((i) => {
    const [n, d] = parseQ(v[i]);
    return fmtQ(n * k, d);
  }) as ExactVec3;
}

function mapSceneCoords(
  scene: Scene3D,
  mapPos: (v: ExactVec3) => ExactVec3,
  mapDir: (v: ExactVec3) => ExactVec3,
): Scene3D {
  const copy: Scene3D = JSON.parse(JSON.stringify(scene));
  const mapWitness = (w: NonNullable<SceneObject["perpendicular_witness"]>) => ({
    ...w,
    foot: mapPos(w.foot),
    ...(w.from_point ? { from_point: mapPos(w.from_point) } : {}),
    ...(w.plane_directions ? { plane_directions: w.plane_directions.map(mapDir) } : {}),
    marker: {
      ...w.marker,
      u: mapDir(w.marker.u),
      v: mapDir(w.marker.v),
    },
  });
  for (const o of copy.objects) {
    if (o.xyz) o.xyz = mapPos(o.xyz);
    if (o.point) o.point = mapPos(o.point);
    if (o.anchor) o.anchor = mapPos(o.anchor);
    if (o.apex_or_top) o.apex_or_top = mapPos(o.apex_or_top);
    if (o.rim_point) o.rim_point = mapPos(o.rim_point);
    if (o.center) o.center = mapPos(o.center);
    if (o.endpoints) o.endpoints = o.endpoints.map(mapPos);
    if (o.vertices) o.vertices = o.vertices.map(mapPos);
    if (o.polygon) o.polygon = o.polygon.map(mapPos);
    if (o.direction) o.direction = mapDir(o.direction);
    if (o.normal) o.normal = mapDir(o.normal);
    if (o.perpendicular_witness) o.perpendicular_witness = mapWitness(o.perpendicular_witness);
  }
  return copy;
}

function assertOpenOrthogonalRightAngleMarker(marker: THREE.Object3D): {
  foot: [number, number, number];
  u: [number, number, number];
  v: [number, number, number];
} {
  const line = marker as THREE.Line;
  const posAttr = line.geometry.getAttribute("position");
  // NEVER a 4-vertex closed square box (`▱`); always a 3-vertex open 90° elbow `[foot+u, foot+u+v, foot+v]`.
  expect(posAttr.count).toBe(3);
  const p0 = new THREE.Vector3().fromBufferAttribute(posAttr, 0);
  const p1 = new THREE.Vector3().fromBufferAttribute(posAttr, 1);
  const p2 = new THREE.Vector3().fromBufferAttribute(posAttr, 2);
  const legA = p0.clone().sub(p1);
  const legB = p2.clone().sub(p1);
  expect(legA.length()).toBeGreaterThan(1e-4);
  expect(legB.length()).toBeGreaterThan(1e-4);
  const cosTheta = legA.dot(legB) / (legA.length() * legB.length());
  expect(Math.abs(cosTheta)).toBeLessThan(1e-6);

  const meta = marker.userData.gocVuongDonVi as {
    foot: [number, number, number];
    u: [number, number, number];
    v: [number, number, number];
  };
  expect(meta).toBeDefined();
  const dotUV = meta.u[0] * meta.v[0] + meta.u[1] * meta.v[1] + meta.u[2] * meta.v[2];
  expect(Math.abs(dotUV)).toBeLessThan(1e-6);
  return meta;
}

function makePlanePlaneIntersectionScene(): Scene3D {
  return {
    free_objects: ["A", "B", "C", "D", "S"],
    chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
    objects: [
      { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
      { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["4", "0", "0"] },
      { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["5", "3", "0"] },
      { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "3", "0"] },
      { id: "S", type: "point3", label: "Đỉnh S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "3/2", "4"] },
      { id: "day_ABCD", type: "polygon3", label: "Đáy hình bình hành ABCD", notation: "ABCD", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C", "D"], vertex_ids: ["A", "B", "C", "D"], vertices: [["0", "0", "0"], ["4", "0", "0"], ["5", "3", "0"], ["1", "3", "0"]], source: { fact_id: "f_para", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"] },
      { id: "khoi_SABCD", type: "solid", label: "Hình chóp S.ABCD", notation: "S.ABCD", shape_class: "PYRAMID_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["S", "A", "B", "C", "D"], vertex_ids: ["S", "A", "B", "C", "D"], vertices: [["2", "3/2", "4"], ["0", "0", "0"], ["4", "0", "0"], ["5", "3", "0"], ["1", "3", "0"]], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]] },
      { id: "mp_SAB", type: "plane3", label: "Mặt phẳng (SAB)", notation: "(SAB)", origin: "derived", producer: "construct_plane", render: "surface", depends: ["S", "A", "B"], point: ["2", "3/2", "4"], normal: ["0", "8", "-3"] },
      { id: "mp_SCD", type: "plane3", label: "Mặt phẳng (SCD)", notation: "(SCD)", origin: "derived", producer: "construct_plane", render: "surface", depends: ["S", "C", "D"], point: ["2", "3/2", "4"], normal: ["0", "8", "3"] },
      { id: "gt_d", type: "line3", label: "Đường thẳng d", notation: "d", origin: "derived", producer: "intersect_planes", render: "line", formation_roles: ["DERIVE_INTERSECTION"], depends: ["mp_SAB", "mp_SCD"], point: ["2", "3/2", "4"], direction: ["1", "0", "0"] },
    ] as unknown as SceneObject[],
    events: [
      { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
      { step_index: 1, action: "CREATE", object: "day_ABCD", depends: ["A", "B", "C", "D"], explanation: "" },
      { step_index: 2, action: "CREATE", object: "khoi_SABCD", depends: ["S", "A", "B", "C", "D"], explanation: "" },
      { step_index: 3, action: "CREATE", object: "mp_SAB", depends: ["S", "A", "B"], explanation: "" },
      { step_index: 4, action: "CREATE", object: "mp_SCD", depends: ["S", "C", "D"], explanation: "" },
      { step_index: 5, action: "CREATE", object: "gt_d", depends: ["mp_SAB", "mp_SCD"], explanation: "" },
    ],
  };
}

describe("AXO Root-Cause Repair & Cross-Family Pedagogical Visual Regression (§4–§10)", () => {
  describe("1. Family 1 — Mặt cầu (d = 0, 0 < d < R, d = R, d > R & Standalone Reference Equator)", () => {
    it("retains attenuated REFERENCE_GREAT_CIRCLE on sphere–plane scenes across Steps 1–5, keeps open 90° IH ⊥ (P) elbow + in-plane ray, places (C) strictly on (P), and rotates reference plane on coincident great-circle cuts", () => {
      const { scene: secantRaw } = loadSample("cau-cat-mat-phang");
      const plan = buildPedagogicalConstructionPlan(withSubEntities(secantRaw));
      const world = registerExactSceneOrigin(veKhongGian(plan.scene), plan.scene);
      expect(plan.steps.length).toBe(5);

      const ball = world.objects.find((o) => o.curved_kind === "ball")!;
      // Steps 1..5: REFERENCE_GREAT_CIRCLE stays visible with monotonic attenuation so sphere retains 3D depth cues without competing with (P) or (C)
      for (const st of plan.steps) {
        const vis = objectsAt(world, st.anchor);
        expect(shouldShowSphereReferenceEquator(world, ball, false, vis)).toBe(true);
        expect(shouldShowSphereReferenceEquator(world, ball, true, vis)).toBe(true);
        // Never mislabels secant d = 3 < R = 5 as "tiếp điểm"
        expect(st.title).not.toMatch(/tiếp\s+điểm|tiếp\s+xúc/iu);
        expect(st.subtitle).not.toMatch(/tiếp\s+điểm|tiếp\s+xúc/iu);
      }

      // Step 3 (H, IH): IH ⊥ (P) uses open 3-point elbow + dashed in-plane ray (never a 4-sided box)
      const distSeg = world.objects.find((o) => o.id === "C__dist")!;
      const step3Vis = objectsAt(world, plan.steps[2]!.anchor);
      const step5Vis = objectsAt(world, plan.steps[4]!.anchor);
      const builtStep2 = buildObject3D(
        distSeg, false, 0.1, [], new THREE.Vector3(8, -6, 5),
        undefined, undefined, false, "primary", false, true, false, world,
        undefined, undefined, undefined, step3Vis,
      )!;
      expect(builtStep2.getObjectByName("perp_marker:C__dist")).toBeUndefined();
      expect(builtStep2.getObjectByName("perp_plane_ray:C__dist")).toBeUndefined();
      const fatStep2 = new THREE.Group();
      dongBoNetDayManHinh([builtStep2], fatStep2, 1440, 900, true);
      expect(fatStep2.children.some((c) => c.name === "fat:perp_plane_ray:C__dist")).toBe(false);

      // Step 5 (C): intersection circle (C) lies strictly on plane (P) (z = 3), radius = 4, and HM grounds perp_marker
      const builtStep3 = buildObject3D(
        distSeg, false, 0.1, [], new THREE.Vector3(8, -6, 5),
        undefined, undefined, false, "primary", true, true, false, world,
        undefined, undefined, undefined, step5Vis,
      )!;
      const m3 = builtStep3.getObjectByName("perp_marker:C__dist")!;
      assertOpenOrthogonalRightAngleMarker(m3);
      expect(builtStep3.getObjectByName("perp_plane_ray:C__dist")).toBeUndefined();

      const cutCircle = world.objects.find((o) => o.id === "C")!;
      const builtCircle = buildObject3D(
        cutCircle, "dich", 0.1, [], new THREE.Vector3(8, -6, 5),
        undefined, undefined, false, "primary", true, true, false, world,
      )!;
      builtCircle.updateMatrixWorld(true);
      const rimSample = builtCircle.userData.curvedRimLoop;
      for (let k = 0; k < 16; k += 1) {
        const samp = rimSample.sample(k / 16) as { outer: THREE.Vector3; inner: THREE.Vector3 };
        const pt = builtCircle.localToWorld(samp.outer.clone());
        expect(Math.abs(pt.z - 3)).toBeLessThan(1e-6);
        expect(Math.abs(Math.hypot(pt.x, pt.y) - 4)).toBeLessThan(1e-5);
      }

      // Great circle (d = 0): reference great circle switches to orthogonal plane so it never overlaps (C)
      const greatScene: Scene3D = {
        free_objects: ["I"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "ball_0", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: null, render: "curved_solid", depends: ["I"], anchor: ["0", "0", "0"], radius_sq: "25" },
          { id: "mp_0", type: "plane3", label: "Mặt phẳng (P)", notation: "(P)", origin: "derived", producer: null, render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["0", "0", "0"], normal: ["0", "0", "1"] },
          { id: "c_great", type: "circle3", label: "Đường tròn lớn (C)", notation: "(C)", origin: "derived", producer: null, render: "circle", surface_role: "SECTION_REGION", depends: ["ball_0", "mp_0"], center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "25" },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "ball_0", depends: ["I"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "mp_0", depends: [], explanation: "" },
          { step_index: 3, action: "CREATE", object: "c_great", depends: ["ball_0", "mp_0"], explanation: "" },
        ],
      };
      const greatBall = greatScene.objects.find((o) => o.id === "ball_0")!;
      expect(shouldShowSphereReferenceEquator(greatScene, greatBall, false, objectsAt(greatScene, 1))).toBe(true);
      expect(shouldShowSphereReferenceEquator(greatScene, greatBall, true, objectsAt(greatScene, 3))).toBe(false);

      // Tangent sphere (d = R = 5): no positive-radius circle, open 90° elbow + in-plane ray at H, attenuated reference great circle retained
      const tangentScene: Scene3D = {
        free_objects: ["I"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "ball_t", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: null, render: "curved_solid", depends: ["I"], anchor: ["0", "0", "0"], radius_sq: "25" },
          { id: "mp_t", type: "plane3", label: "Mặt phẳng (P)", notation: "(P)", origin: "derived", producer: null, render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["0", "0", "5"], normal: ["0", "0", "1"] },
          { id: "H_t", type: "point3", label: "Tiếp điểm H", notation: "H", origin: "derived", producer: "project_onto", render: "point_marker", depends: ["I", "mp_t"], xyz: ["0", "0", "5"], perpendicular_witness: { from: "I", foot: ["0", "0", "5"], foot_id: "H_t", on: "mp_t", relation: "line_perp_plane", status: "DERIVED_VERIFIED", plane_directions: [["1", "0", "0"], ["0", "1", "0"]], marker: { u: ["1", "0", "0"], v: ["0", "0", "-1"] } } },
          { id: "IH_t", type: "segment3", label: "Bán kính IH", notation: "IH", origin: "derived", producer: "construct_segment", render: "segment", depends: ["I", "H_t"], endpoint_ids: ["I", "H_t"], endpoints: [["0", "0", "0"], ["0", "0", "5"]], perpendicular_witness: { from: "I", foot: ["0", "0", "5"], foot_id: "H_t", on: "mp_t", relation: "line_perp_plane", status: "DERIVED_VERIFIED", plane_directions: [["1", "0", "0"], ["0", "1", "0"]], marker: { u: ["1", "0", "0"], v: ["0", "0", "-1"] } } },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "ball_t", depends: ["I"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "mp_t", depends: [], explanation: "" },
          { step_index: 3, action: "CREATE", object: "H_t", depends: ["I", "mp_t"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "IH_t", depends: ["I", "H_t"], explanation: "" },
        ],
      };
      const tanPlan = buildPedagogicalConstructionPlan(withSubEntities(tangentScene));
      expect(tanPlan.scene.objects.some((o) => o.type === "circle3")).toBe(false);
      expect(shouldShowSphereReferenceEquator(tanPlan.scene, tanPlan.scene.objects.find((o) => o.id === "ball_t")!, false)).toBe(true);
      const ihBuilt = buildObject3D(
        tanPlan.scene.objects.find((o) => o.id === "IH_t")!,
        false, 0.1, [], new THREE.Vector3(8, -6, 5),
        undefined, undefined, false, "primary", true, true, false, tanPlan.scene,
        undefined, undefined, undefined, tanPlan.scene.objects,
      )!;
      expect(ihBuilt.getObjectByName("perp_marker:IH_t")).toBeUndefined();
      expect(ihBuilt.getObjectByName("perp_plane_ray:IH_t")).toBeUndefined();

      // Standalone sphere (`cau-the-tich`): retains subtle slate reference equator (`0.24 / 0.14`)
      const { scene: standRaw } = loadSample("cau-the-tich");
      const standBall = standRaw.objects.find((o) => o.curved_kind === "ball")!;
      expect(shouldShowSphereReferenceEquator(standRaw, standBall, false, standRaw.objects)).toBe(true);
      const standBuilt = buildObject3D(standBall, false, 0.1, [], new THREE.Vector3(8, -6, 5), undefined, undefined, false, "primary", true, true, false, standRaw)!;
      const standRef = standBuilt.getObjectByName("sphere_reference:cau")!;
      expect(standRef.userData.curvedRimLoop.thayMesh.material.opacity).toBeCloseTo(0.24, 5);
      expect(standRef.userData.curvedRimLoop.khuatMesh.material.opacity).toBeCloseTo(0.14, 5);
    });
  });

  describe("2. Family 2 — Hình chóp: (SAB) ∩ (SCD), Mặt phẳng qua B ⊥ SC, Hình chiếu A lên (SBC), Góc đường-mặt", () => {
    it("renders (SAB) & (SCD) carrier planes in an explicit step before intersection line d, attaches d ∥ AB ∥ CD parallel relations, and renders infinite-line dashed tails without ConeGeometry", () => {
      const ppScene = withSubEntities(makePlanePlaneIntersectionScene());
      const plan = buildPedagogicalConstructionPlan(ppScene);
      const carrierStepIdx = plan.steps.findIndex(
        (s) => s.targetIds.includes("mp_SAB") && s.targetIds.includes("mp_SCD"),
      );
      const lineStepIdx = plan.steps.findIndex((s) => s.targetIds.includes("gt_d"));
      expect(carrierStepIdx).toBeGreaterThanOrEqual(0);
      expect(lineStepIdx).toBe(carrierStepIdx + 1);
      expect(plan.steps[carrierStepIdx]!.title).toContain("(SAB)");
      expect(plan.steps[carrierStepIdx]!.title).toContain("(SCD)");

      // Carrier face overlays are active on BOTH the carrier step ("primary") and the intersection line step ("context")
      const carrierOverlays = resolveSolidFaceDuplicateCarrierPolygons(plan.scene, plan.steps[carrierStepIdx]!.anchor, null);
      expect(carrierOverlays.map((x) => x.planeId).sort()).toEqual(["mp_SAB", "mp_SCD"]);
      expect(carrierOverlays.every((x) => x.vertices.length === 3)).toBe(true);
      const carrierChips = buildStepEntityGroups(plan.scene, plan.steps[carrierStepIdx]!.anchor, { steps: plan.steps });
      expect(carrierChips.primary.map((c) => c.id).sort()).toEqual(["mp_SAB", "mp_SCD"]);

      const lineOverlays = resolveSolidFaceDuplicateCarrierPolygons(plan.scene, plan.steps[lineStepIdx]!.anchor, null);
      expect(lineOverlays.map((x) => x.planeId).sort()).toEqual(["mp_SAB", "mp_SCD"]);
      const lineChips = buildStepEntityGroups(plan.scene, plan.steps[lineStepIdx]!.anchor, { steps: plan.steps });
      expect(lineChips.primary.map((c) => c.id)).toContain("gt_d");
      expect(lineChips.context.map((c) => c.id)).toEqual(expect.arrayContaining(["mp_SAB", "mp_SCD"]));

      // Exact parallel relation to canonical solid edges AB and CD
      const dContract = resolveSemanticObjectContract(plan.scene, "gt_d")!;
      const parTargets = dContract.verifiedRelations
        .filter((r) => r.kind === "parallel" && r.exactVerified)
        .flatMap((r) => r.targetIds);
      expect(parTargets).toContain("khoi_SABCD::edge:A-B");
      expect(parTargets).toContain("khoi_SABCD::edge:C-D");

      // Infinite line renders central solid segment + 2 forceDashed outer extensions and zero ConeGeometry
      const dObj = plan.scene.objects.find((o) => o.id === "gt_d")!;
      const visFinal = objectsAt(plan.scene, plan.steps[lineStepIdx]!.anchor);
      const diemNen = visFinal.filter((o) => o.type === "point3" && o.xyz).map((o) => toVec3(o.xyz!));
      const builtLine = buildObject3D(
        dObj, "dich", 0.1, diemNen, new THREE.Vector3(10, -8, 7),
        undefined, undefined, false, "primary", true, true, false, plan.scene,
      )!;
      const ext0 = builtLine.getObjectByName("line_ext:gt_d:0")!;
      const ext1 = builtLine.getObjectByName("line_ext:gt_d:1")!;
      expect(ext0.userData.nonCanonicalSegment?.forceDashed).toBe(true);
      expect(ext1.userData.nonCanonicalSegment?.forceDashed).toBe(true);
      let hasCone = false;
      builtLine.traverse((node) => {
        if ((node as THREE.Mesh).geometry instanceof THREE.ConeGeometry) hasCone = true;
      });
      expect(hasCone).toBe(false);

      // Even when dashedHiddenShown is toggled OFF, unoccluded infinite-line extensions stay visible as dashed Line2 overlays
      const fatGroup = new THREE.Group();
      dongBoNetDayManHinh([builtLine], fatGroup, 1440, 900, false);
      expect(fatGroup.children.filter((c) => c.visible).length).toBeGreaterThanOrEqual(3);

      // Catalog `vuong-goc-chop` (with solid face sub-entities `chop::face:*`) still shades carrier face `(SAB)` and surfaces chip `(SAB)`
      const { scene: vgcRaw } = loadSample("vuong-goc-chop");
      const vgcPlan = buildPedagogicalConstructionPlan(withSubEntities(vgcRaw));
      const vgcWorld = registerExactSceneOrigin(veKhongGian(vgcPlan.scene), vgcPlan.scene);
      const vgcFinalIdx = vgcPlan.steps.length - 1;
      const vgcCarriers = resolveSolidFaceDuplicateCarrierPolygons(vgcWorld, vgcPlan.steps[vgcFinalIdx]!.anchor);
      expect(vgcCarriers.map((c) => c.planeId)).toContain("sab");
      const vgcGroups = buildStepEntityGroups(vgcWorld, vgcPlan.steps[vgcFinalIdx]!.anchor, { steps: vgcPlan.steps });
      expect(vgcGroups.context.map((c) => c.id)).toContain("sab");
    });

    it("highlights collinear sub-segment SH on SC, draws witness leg HB (u_to: 'B'), and anchors open 90° elbow at H in mp-vuong-goc-duong", () => {
      const { scene: raw } = loadSample("mp-vuong-goc-duong");
      const plan = buildPedagogicalConstructionPlan(withSubEntities(raw));
      const world = registerExactSceneOrigin(veKhongGian(plan.scene), plan.scene);
      const finalAnchor = plan.steps[plan.steps.length - 1]!.anchor;
      const vis = objectsAt(world, finalAnchor);

      // Mathematical verification: B ∈ (α), H ∈ (α), SC ∥ normal(α), SH ⊥ HB
      const alpha = world.objects.find((o) => o.id === "mpb")!;
      const ptB = toVec3(world.objects.find((o) => o.id === "B")!.xyz!);
      const ptS = toVec3(world.objects.find((o) => o.id === "S")!.xyz!);
      const ptC = toVec3(world.objects.find((o) => o.id === "C")!.xyz!);
      const ptH = toVec3(world.objects.find((o) => o.type === "point3" && (o.id === "H" || o.notation === "H"))!.xyz!);
      const p0 = toVec3(alpha.point!);
      const nVec = toVec3(alpha.normal!);
      const dotPlane = (p: number[]) => (p[0] - p0[0]) * nVec[0] + (p[1] - p0[1]) * nVec[1] + (p[2] - p0[2]) * nVec[2];
      expect(Math.abs(dotPlane(ptB))).toBeLessThan(1e-6);
      expect(Math.abs(dotPlane(ptH))).toBeLessThan(1e-6);

      const scVec = [ptC[0] - ptS[0], ptC[1] - ptS[1], ptC[2] - ptS[2]];
      const crossSCn = Math.hypot(
        scVec[1] * nVec[2] - scVec[2] * nVec[1],
        scVec[2] * nVec[0] - scVec[0] * nVec[2],
        scVec[0] * nVec[1] - scVec[1] * nVec[0],
      );
      expect(crossSCn).toBeLessThan(1e-6);

      // Partial collinear highlight on canonical edge S-C: SH is strictly < |SC|
      const shSeg = vis.find((o) => o.type === "segment3" && o.perpendicular_witness?.on === "mpb")!;
      expect(shSeg).toBeDefined();
      const mapToSang = toSangCanhChuan(vis, (id) => id === shSeg.id, () => 0xd97706);
      const scHighlight = mapToSang.khuc.get("chop::edge:C-S") ?? mapToSang.khuc.get("chop::edge:S-C");
      expect(scHighlight).toBeDefined();
      expect(scHighlight!.t1 - scHighlight!.t0).toBeGreaterThan(0.5);
      expect(scHighlight!.t1 - scHighlight!.t0).toBeLessThan(0.9);

      // Witness leg HB + open 90° elbow at H pointing along HB and HS
      const builtSH = buildObject3D(
        shSeg, "dich", 0.1, [], new THREE.Vector3(9, -8, 6),
        undefined, undefined, false, "primary", true, true, false, world,
        undefined, undefined, undefined, vis,
      )!;
      const hbLeg = builtSH.getObjectByName(`witness_leg:${shSeg.id}`)!;
      expect(hbLeg).toBeDefined();
      const shMarker = builtSH.getObjectByName(`perp_marker:${shSeg.id}`)!;
      const meta = assertOpenOrthogonalRightAngleMarker(shMarker);
      const hbDir = new THREE.Vector3(ptB[0] - ptH[0], ptB[1] - ptH[1], ptB[2] - ptH[2]).normalize();
      expect(Math.abs(hbDir.x * meta.u[0] + hbDir.y * meta.u[1] + hbDir.z * meta.u[2])).toBeGreaterThan(0.9999);
    });

    it("keeps H on edge SB when A projects onto (SBC), shades sab carrier in vuong-goc-chop, and never leaks angle/distance answers", () => {
      const { scene: vgRaw, problemText: vgDe, title: vgTitle } = loadSample("vuong-goc-chop");
      const vgPlan = buildPedagogicalConstructionPlan(withSubEntities(vgRaw));
      const vgFinal = vgPlan.steps[vgPlan.steps.length - 1]!.anchor;
      const vgCarriers = resolveSolidFaceDuplicateCarrierPolygons(vgPlan.scene, vgFinal, null);
      expect(vgCarriers.map((c) => c.planeId)).toContain("sab");
      const vgHtml = renderToString(<AxoWorkspaceV62 scene={vgRaw} de={vgDe} tieuDe={vgTitle} />);
      expect(vgHtml).not.toContain('id="dock-math-results"');
      expect(vgHtml).not.toContain("KẾT QUẢ TOÁN HỌC");
    });
  });

  describe("3. Family 3 — Lăng trụ (Right & Oblique Prism Opposite Top Base vs Section)", () => {
    it("classifies CONSTRUCT_TRANSLATED_FACE top base as 'base' (never 'section') on both right and oblique prisms", () => {
      for (const topShiftX of ["0", "2"]) {
        const prismScene: Scene3D = {
          free_objects: ["A", "B", "C", "A1", "B1", "C1"],
          chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
          objects: [
            { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
            { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
            { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
            { id: "A1", type: "point3", label: "A′", notation: "A′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: [topShiftX, "0", "4"] },
            { id: "B1", type: "point3", label: "B′", notation: "B′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: [String(3 + Number(topShiftX)), "0", "4"] },
            { id: "C1", type: "point3", label: "C′", notation: "C′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: [topShiftX, "4", "4"] },
            { id: "day_ABC", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "4", "0"]] },
            { id: "day_A1B1C1", type: "polygon3", label: "Đáy A′B′C′", notation: "A′B′C′", origin: "derived", producer: "construct_polygon", render: "polygon", formation_roles: ["CONSTRUCT_TRANSLATED_FACE"], depends: ["A1", "B1", "C1"], vertex_ids: ["A1", "B1", "C1"], vertices: [[topShiftX, "0", "4"], [String(3 + Number(topShiftX)), "0", "4"], [topShiftX, "4", "4"]] },
            { id: "lt", type: "solid", label: "Lăng trụ ABC.A′B′C′", notation: "ABC.A′B′C′", shape_class: "PRISM_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", depends: ["A", "B", "C", "A1", "B1", "C1"], vertex_ids: ["A", "B", "C", "A1", "B1", "C1"], vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "4", "0"], [topShiftX, "0", "4"], [String(3 + Number(topShiftX)), "0", "4"], [topShiftX, "4", "4"]], faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]] },
          ] as unknown as SceneObject[],
          events: [
            { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
            { step_index: 1, action: "CREATE", object: "day_ABC", depends: ["A", "B", "C"], explanation: "" },
            { step_index: 2, action: "CREATE", object: "day_A1B1C1", depends: ["A1", "B1", "C1"], explanation: "" },
            { step_index: 3, action: "CREATE", object: "lt", depends: ["A", "B", "C", "A1", "B1", "C1"], explanation: "" },
          ],
        };
        const topPoly = prismScene.objects.find((o) => o.id === "day_A1B1C1")!;
        expect(vaiTroMien(topPoly)).toBe("base");
        const builtTop = buildObject3D(
          topPoly, false, 0.1, [], new THREE.Vector3(10, -8, 6),
          undefined, undefined, false, "primary", true, true, false, prismScene,
          undefined, undefined, undefined, prismScene.objects,
        )!;
        // Boundary uses slate base styling (0x1e293b, never terracotta section 0xc85a32) and yields to canonical solid edges
        expect(builtTop.userData.nonCanonicalLoop?.color).not.toBe(0xc85a32);
        expect(builtTop.userData.nonCanonicalLoop?.yieldColinear).toBe(true);
      }
    });
  });

  describe("4. Families 4 & 5 — Hình trụ (Tilted Right vs Genuine Oblique) & Hình nón (Axis Orthogonality & Generatrix)", () => {
    it("synthesizes exact 90° axis witness for tilted right cylinder (tru-truc-xien) and right cone (non-duong-sinh), omits it on genuine oblique cylinder, and normalizes misleading title", () => {
      // Tilted right cylinder `tru-truc-xien`
      const { scene: truRaw, problemText: truDe, title: truTitle } = loadSample("tru-truc-xien");
      const truPlan = buildPedagogicalConstructionPlan(withSubEntities(truRaw));
      const truWorld = registerExactSceneOrigin(veKhongGian(truPlan.scene), truPlan.scene);
      const truAxis = truWorld.objects.find((o) => o.id === "tru__axis")!;
      expect(truAxis.perpendicular_witness?.relation).toBe("line_perp_plane");
      const truAxisBuilt = buildObject3D(
        truAxis, false, 0.1, [], new THREE.Vector3(8, -8, 6),
        undefined, undefined, false, "primary", true, true, false, truWorld,
        undefined, undefined, undefined, truWorld.objects,
      )!;
      assertOpenOrthogonalRightAngleMarker(truAxisBuilt.getObjectByName("perp_marker:tru__axis")!);

      const truHtml = renderToString(<AxoWorkspaceV62 scene={truRaw} de={truDe} tieuDe={truTitle} />);
      expect(truHtml).toContain("Hình trụ tròn xoay có trục đặt nghiêng");
      expect(truHtml).not.toContain('id="dock-goal-reveal"');
      expect(truHtml).not.toContain('id="dock-goal-conclusion"');
      expect(truHtml).not.toContain("15π");
      expect(truHtml).not.toContain("6π√5");

      // Genuine oblique cylinder (`OO' = (2,0,4)` ∦ `n = (0,0,1)`) -> NO perpendicular_witness on axis, invariant across 3 cameras
      const obScene: Scene3D = {
        free_objects: ["O", "O_prime"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "O", type: "point3", label: "Tâm O", notation: "O", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "O_prime", type: "point3", label: "Tâm O′", notation: "O′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "4"] },
          { id: "day_duoi", type: "circle3", label: "Đáy (O)", notation: "(O)", origin: "derived", producer: null, render: "circle", surface_role: "BASE_REGION", depends: ["O"], center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "4" },
          { id: "day_tren", type: "circle3", label: "Đáy (O′)", notation: "(O′)", origin: "derived", producer: null, render: "circle", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_TRANSLATED_FACE"], depends: ["O_prime"], center: ["2", "0", "4"], normal: ["0", "0", "1"], radius_sq: "4" },
          { id: "tru_xien", type: "curved_solid", curved_kind: "cylinder", label: "Hình trụ xiên", notation: "(T)", origin: "derived", producer: null, render: "curved_solid", depends: ["O", "O_prime", "day_duoi", "day_tren"], anchor: ["0", "0", "0"], apex_or_top: ["2", "0", "4"], radius_sq: "4", height_sq: "16" },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_duoi", depends: ["O"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "day_tren", depends: ["O_prime"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "tru_xien", depends: ["O", "O_prime", "day_duoi", "day_tren"], explanation: "" },
        ],
      };
      const obPlan = buildPedagogicalConstructionPlan(withSubEntities(obScene));
      const obAxis = obPlan.scene.objects.find((o) => o.id === "tru_xien__axis");
      expect(obAxis?.perpendicular_witness).toBeUndefined();
      const obCyl = obPlan.scene.objects.find((o) => o.id === "tru_xien")!;
      for (const cam of [new THREE.Vector3(9, -7, 6), new THREE.Vector3(-8, 10, 4), new THREE.Vector3(2, 0, 14)]) {
        expect(inspectAxialCurvedOrthogonality(obPlan.scene, obCyl).isOblique).toBe(true);
        const builtOb = buildObject3D(obCyl, false, 0.1, [], cam, undefined, undefined, false, "primary", true, true, false, obPlan.scene)!;
        expect(builtOb.visible).toBe(true);
      }

      // Right cone `non-duong-sinh`: `non__axis` (SO) carries exact 90° witness onto base (O), generatrix SA stays visible, zero l=5/12π/15π leak
      const { scene: coneRaw, problemText: coneDe, title: coneTitle } = loadSample("non-duong-sinh");
      const conePlan = buildPedagogicalConstructionPlan(withSubEntities(coneRaw));
      const coneWorld = registerExactSceneOrigin(veKhongGian(conePlan.scene), conePlan.scene);
      const coneAxis = coneWorld.objects.find((o) => o.id === "non__axis")!;
      expect(coneAxis.perpendicular_witness?.relation).toBe("line_perp_plane");
      const coneAxisBuilt = buildObject3D(
        coneAxis, false, 0.1, [], new THREE.Vector3(8, -8, 6),
        undefined, undefined, false, "primary", true, true, false, coneWorld,
        undefined, undefined, undefined, coneWorld.objects,
      )!;
      assertOpenOrthogonalRightAngleMarker(coneAxisBuilt.getObjectByName("perp_marker:non__axis")!);
      expect(objectsAt(coneWorld, conePlan.steps[conePlan.steps.length - 1]!.anchor).some((o) => o.id === "doan_SA")).toBe(true);
      const coneHtml = renderToString(<AxoWorkspaceV62 scene={coneRaw} de={coneDe} tieuDe={coneTitle} />);
      expect(coneHtml).not.toContain('id="dock-goal-reveal"');
      expect(coneHtml).not.toContain('id="dock-goal-conclusion"');
      expect(coneHtml).not.toContain("12π");
      expect(coneHtml).not.toContain("15π");

      // Cylinder circular section `tru-thiet-dien-tron`: emits zero synthetic perp_plane_ray or ungrounded perp_marker when no radial segment is drawn at O or M
      const { scene: cSecRaw } = loadSample("tru-thiet-dien-tron");
      const cSecPlan = buildPedagogicalConstructionPlan(withSubEntities(cSecRaw));
      const cSecWorld = registerExactSceneOrigin(veKhongGian(cSecPlan.scene), cSecPlan.scene);
      const cSecAxis = cSecWorld.objects.find((o) => o.id === "tru__axis")!;
      const cSecAxisBuilt = buildObject3D(
        cSecAxis, false, 0.1, [], new THREE.Vector3(8, -8, 6),
        undefined, undefined, false, "primary", true, true, false, cSecWorld,
        undefined, undefined, undefined, cSecWorld.objects,
      )!;
      expect(cSecAxisBuilt.getObjectByName("perp_plane_ray:tru__axis")).toBeUndefined();
      expect(cSecAxisBuilt.getObjectByName("perp_marker:tru__axis")).toBeUndefined();

      const pContract = resolveSemanticObjectContract(cSecWorld, "P")!;
      expect(pContract.verifiedRelations.some((r) => r.kind === "line_perp_plane" && r.canDisplaySymbol)).toBe(true);
      const pBuilt = buildObject3D(
        cSecWorld.objects.find((o) => o.id === "P")!, false, 0.1,
        cSecWorld.objects.filter((o) => o.type === "point3" && o.xyz).map((o) => toVec3(o.xyz!)),
        new THREE.Vector3(8, -8, 6),
        undefined, undefined, false, "primary", true, true, false, cSecWorld,
        undefined, undefined, undefined, cSecWorld.objects,
      )!;
      expect(pBuilt.getObjectByName("perp_marker:P")).toBeUndefined();
      expect(pBuilt.getObjectByName("perp_plane_ray:P")).toBeUndefined();
    });
  });

  describe("5. Family 6 & All 10 Metamorphic Invariants (Rename, Translate, Rotate, Scale, Permute, Non-Identity chart_metric, Replay & Toggles)", () => {
    it("preserves carrier planes, parallel relations, infinite-line tails, exact 90° world-space elbows under non-identity chart_metric, and deterministic step replay", () => {
      const basePP = makePlanePlaneIntersectionScene();
      const basePlan = buildPedagogicalConstructionPlan(withSubEntities(basePP));

      // (1) Vertex & ID rename: S,A,B,C,D -> P,E,F,G,H
      const renameId: Record<string, string> = {
        S: "P", A: "E", B: "F", C: "G", D: "H",
        day_ABCD: "day_EFGH", khoi_SABCD: "khoi_PEFGH", mp_SAB: "mp_PEF", mp_SCD: "mp_PGH", gt_d: "duong_m",
      };
      const renamedPP: Scene3D = JSON.parse(
        JSON.stringify(basePP)
          .replace(/"(S|A|B|C|D|day_ABCD|khoi_SABCD|mp_SAB|mp_SCD|gt_d)"/g, (_, k: string) => `"${renameId[k] ?? k}"`),
      );
      for (const o of renamedPP.objects) {
        if (o.notation && renameId[o.notation]) o.notation = renameId[o.notation];
      }
      const renPlan = buildPedagogicalConstructionPlan(withSubEntities(renamedPP));
      expect(renPlan.steps.length).toBe(basePlan.steps.length);
      const renCarriers = resolveSolidFaceDuplicateCarrierPolygons(
        renPlan.scene,
        renPlan.steps[renPlan.steps.length - 1]!.anchor,
        null,
      );
      expect(renCarriers.map((c) => c.planeId).sort()).toEqual(["mp_PEF", "mp_PGH"]);
      const renLineContract = resolveSemanticObjectContract(renPlan.scene, "duong_m")!;
      expect(renLineContract.verifiedRelations.some((r) => r.kind === "parallel" && r.targetIds.includes("khoi_PEFGH::edge:E-F"))).toBe(true);

      // (2) Translation +(5, -3, 7), (3) 90° Z-rotation, (4) Uniform scale ×2, (5) Event permutation
      const translatedPP = mapSceneCoords(basePP, (v) => addVecQ(v, [5n, -3n, 7n]), (v) => v);
      const rotatedPP = mapSceneCoords(basePP, rotZ90VecQ, rotZ90VecQ);
      const scaledPP = mapSceneCoords(basePP, (v) => scaleVecQ(v, 2n), (v) => scaleVecQ(v, 2n));
      const permutedPP: Scene3D = {
        ...JSON.parse(JSON.stringify(basePP)),
        events: [
          basePP.events[0]!,
          { ...basePP.events[4]!, step_index: 1 },
          { ...basePP.events[3]!, step_index: 2 },
          { ...basePP.events[5]!, step_index: 3 },
          { ...basePP.events[2]!, step_index: 4 },
          { ...basePP.events[1]!, step_index: 5 },
        ],
      };

      for (const variant of [translatedPP, rotatedPP, scaledPP, permutedPP]) {
        expect(verifySceneMathematicalConsistency(variant).valid).toBe(true);
        const vp = buildPedagogicalConstructionPlan(withSubEntities(variant));
        const cIdx = vp.steps.findIndex((s) => s.targetIds.includes("mp_SAB") || s.targetIds.includes("mp_SCD"));
        const lIdx = vp.steps.findIndex((s) => s.targetIds.includes("gt_d"));
        expect(cIdx).toBeGreaterThanOrEqual(0);
        expect(lIdx).toBeGreaterThan(cIdx);
        const overlays = resolveSolidFaceDuplicateCarrierPolygons(vp.scene, vp.steps[lIdx]!.anchor, null);
        expect(overlays.map((o) => o.planeId).sort()).toEqual(["mp_SAB", "mp_SCD"]);
      }

      // (7) Non-identity chart_metric (`[[1, 1/2, 0], [1/2, 1, 0], [0, 0, 1]]`) right cone: world-space elbow is exact 90.000°!
      const skewChartCone: Scene3D = {
        free_objects: ["O", "A", "S"],
        chart_metric: [["1", "1/2", "0"], ["1/2", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "O", type: "point3", label: "O", notation: "O", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
          { id: "S", type: "point3", label: "S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
          { id: "non_skew_chart", type: "curved_solid", curved_kind: "cone", label: "Hình nón", notation: "(N)", origin: "derived", producer: "construct_cone", render: "curved_solid", depends: ["O", "A", "S"], anchor: ["0", "0", "0"], apex_or_top: ["0", "0", "4"], rim_point: ["3", "0", "0"], radius_sq: "9", height_sq: "16" },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "non_skew_chart", depends: ["O", "A", "S"], explanation: "" },
        ],
      };
      const skewPlan = buildPedagogicalConstructionPlan(withSubEntities(skewChartCone));
      const skewWorld = registerExactSceneOrigin(veKhongGian(skewPlan.scene), skewPlan.scene);
      const skewAxis = skewWorld.objects.find((o) => o.id === "non_skew_chart__axis")!;
      const skewAxisBuilt = buildObject3D(
        skewAxis, false, 0.1, [], new THREE.Vector3(9, -7, 6),
        undefined, undefined, false, "primary", true, true, false, skewWorld,
        undefined, undefined, undefined, skewWorld.objects,
      )!;
      const skewMarker = skewAxisBuilt.getObjectByName("perp_marker:non_skew_chart__axis")!;
      assertOpenOrthogonalRightAngleMarker(skewMarker);
      // Verify across 3 distinct camera angles + edge-on foreshortening without allocating GPU buffers
      for (const [cx, cy, cz] of [[9, -7, 6], [-10, 5, 4], [3, 11, 8]] as const) {
        const cam = new THREE.PerspectiveCamera(45, 16 / 9, 0.1, 200);
        cam.position.set(cx, cy, cz);
        cam.lookAt(0, 0, 1);
        cam.updateMatrixWorld(true);
        expect(datCoGocVuong([skewAxisBuilt], cam, 720)).toBe(1);
        expect(skewMarker.visible).toBe(true);
      }

      // (8) Forward / backward replay determinism `0 -> N -> 0 -> k`
      const snapAt = (idx: number) => {
        const st = basePlan.steps[idx]!;
        const vis = objectsAt(basePlan.scene, st.anchor).map((o) => o.id).sort();
        const chips = buildStepEntityGroups(basePlan.scene, st.anchor, { steps: basePlan.steps }).all.map((c) => c.id);
        const carriers = resolveSolidFaceDuplicateCarrierPolygons(basePlan.scene, st.anchor, null).map((c) => `${c.planeId}:${c.rank}`);
        return JSON.stringify({ vis, chips, carriers });
      };
      const forward = basePlan.steps.map((_, i) => snapAt(i));
      const backward = [...basePlan.steps.keys()].reverse().map((i) => snapAt(i)).reverse();
      expect(backward).toEqual(forward);
      expect(snapAt(basePlan.steps.length - 2)).toBe(forward[basePlan.steps.length - 2]);

      // Family 6: Skew-line common perpendicular dual open 3-point elbows
      const skewLinesScene: Scene3D = {
        free_objects: ["M", "N", "P1", "P2"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "M", type: "point3", label: "M", notation: "M", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "P1", type: "point3", label: "P1", notation: "P1", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
          { id: "N", type: "point3", label: "N", notation: "N", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
          { id: "P2", type: "point3", label: "P2", notation: "P2", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "3", "4"] },
          { id: "d1", type: "line3", label: "d₁", notation: "d₁", origin: "derived", producer: "construct_line", render: "line", depends: ["M", "P1"], point: ["0", "0", "0"], direction: ["1", "0", "0"] },
          { id: "d2", type: "line3", label: "d₂", notation: "d₂", origin: "derived", producer: "construct_line", render: "line", depends: ["N", "P2"], point: ["0", "0", "4"], direction: ["0", "1", "0"] },
          { id: "seg_MN", type: "segment3", label: "MN", notation: "MN", origin: "derived", producer: "common_perpendicular", render: "segment", display_group: ["perp_witness"], depends: ["d1", "d2", "M", "N"], endpoint_ids: ["M", "N"], endpoints: [["0", "0", "0"], ["0", "0", "4"]], perpendicular_witness: { from: "N", foot: ["0", "0", "0"], foot_id: "M", on: "d1", relation: "common_perpendicular", status: "DERIVED_VERIFIED", line_direction: ["1", "0", "0"], marker: { u: ["1", "0", "0"], v: ["0", "0", "4"] }, second: { foot: ["0", "0", "4"], foot_id: "N", on: "d2", line_direction: ["0", "1", "0"], marker: { u: ["0", "1", "0"], v: ["0", "0", "-4"] } } } },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "d1", depends: ["M", "P1"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "d2", depends: ["N", "P2"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "seg_MN", depends: ["d1", "d2", "M", "N"], explanation: "" },
        ],
      };
      const builtMN = buildObject3D(
        skewLinesScene.objects.find((o) => o.id === "seg_MN")!,
        "dich", 0.1, [], new THREE.Vector3(8, -7, 6),
        undefined, undefined, false, "primary", true, true, false, skewLinesScene,
        undefined, undefined, undefined, skewLinesScene.objects,
      )!;
      assertOpenOrthogonalRightAngleMarker(builtMN.getObjectByName("perp_marker:seg_MN")!);
      assertOpenOrthogonalRightAngleMarker(builtMN.getObjectByName("perp_marker_2:seg_MN")!);

      // Clean evaluation policy check across all catalog samples
      for (const s of SAMPLES_RAW.samples) {
        const sc = JSON.parse(JSON.stringify(s.envelope.scene3d)) as Scene3D;
        const pl = buildPedagogicalConstructionPlan(withSubEntities(sc));
        const pol = evaluateStudentPresentationPolicy(pl.scene, pl.goalCompletion);
        expect(pol.showMathResultsPanel).toBe(false);
        const hidden = tapKetQuaCuoi(pl.scene);
        const view: AnnotationView = { ...DEFAULT_ANNOTATION_VIEW, hiddenIds: hidden };
        for (const st of pl.steps) {
          for (const ann of annotationsAt(pl.scene, st.anchor, view, null)) {
            if (!hidden.has(ann.id)) {
              expect(ann.role).toBe("given");
            }
          }
        }
      }
    });
  });
});
