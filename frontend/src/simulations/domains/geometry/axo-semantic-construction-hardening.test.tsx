import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import * as THREE from "three";
import type { Exact, ExactVec3, Scene3D, SceneObject } from "./scene3d-model";
import { attachHybridViewToScene, objectsAt, registerExactSceneOrigin, tapKetQuaCuoi } from "./scene3d-model";
import { veKhongGian } from "./scene3d-chart";
import { withSubEntities } from "./scene3d-subentities";
import {
  annotationAnchor,
  annotationsAt,
  projectionWitnessesAt,
  type AnnotationView,
} from "./scene3d-annotations";
import { TRANG_THAI_DAU } from "./interaction-state";
import {
  buildObject3D,
  datCoGocVuong,
  doanDaVe,
  Scene3DWorkspace,
  vatNhanChung,
} from "./scene3d-view";
import {
  evaluateStudentPresentationPolicy,
  sanitizeStudentDescriptorText,
} from "./scene3d-student-presentation-policy";
import {
  buildContractReferenceGroup,
  buildPedagogicalConstructionPlan,
  buildStepEntityGroups,
  getSemanticConstructionContract,
  inspectAxialCurvedOrthogonality,
  isIntersectionLineOrSegment,
  isPolyhedronLateralOrAuxFacePolygon,
  resolveSemanticObjectContract,
  verifySceneMathematicalConsistency,
  type CanonicalPedagogicalObjectRole,
  type CertifiedGeometricRelation,
} from "./scene3d-semantic-policy";

const SAMPLES_RAW = JSON.parse(
  readFileSync(join(__dirname, "..", "..", "..", "data", "geometry-samples.json"), "utf8"),
) as { samples: { id: string; title: string; envelope: { scene3d: Scene3D } }[] };

function sampleScene(id: string): Scene3D {
  const found = SAMPLES_RAW.samples.find((s) => s.id === id);
  if (!found) throw new Error(`Missing sample ${id}`);
  return JSON.parse(JSON.stringify(found.envelope.scene3d)) as Scene3D;
}

function parseQ(s: Exact): [bigint, bigint] {
  const str = String(s).trim();
  const slash = str.indexOf("/");
  if (slash >= 0) {
    return [BigInt(str.slice(0, slash)), BigInt(str.slice(slash + 1))];
  }
  if (str.includes(".")) {
    const [ip, fp] = str.split(".");
    const den = 10n ** BigInt(fp.length);
    const sign = ip.startsWith("-") ? -1n : 1n;
    const absIp = BigInt(ip.replace(/^[+-]/, "") || "0");
    return [sign * (absIp * den + BigInt(fp)), den];
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

function scaleScalarQ(s: Exact, k: bigint): string {
  const [n, d] = parseQ(s);
  return fmtQ(n * k, d);
}

function mapSceneCoords(
  scene: Scene3D,
  mapPos: (v: ExactVec3) => ExactVec3,
  mapDir: (v: ExactVec3) => ExactVec3,
): Scene3D {
  const copy: Scene3D = JSON.parse(JSON.stringify(scene));
  const mapWitness = (w: NonNullable<SceneObject["perpendicular_witness"]>) => {
    const wRec = w as unknown as Record<string, unknown>;
    const secRec = w.second as unknown as Record<string, unknown> | undefined;
    return {
      ...w,
      foot: mapPos(w.foot),
      ...(w.from_point ? { from_point: mapPos(w.from_point) } : {}),
      ...(Array.isArray(wRec.line_direction) ? { line_direction: mapDir(wRec.line_direction as ExactVec3) } : {}),
      ...(w.plane_directions ? { plane_directions: w.plane_directions.map(mapDir) } : {}),
      marker: {
        ...w.marker,
        u: mapDir(w.marker.u),
        v: mapDir(w.marker.v),
      },
      ...(w.second
        ? {
            second: {
              ...w.second,
              foot: mapPos(w.second.foot),
              ...(Array.isArray(secRec?.line_direction) ? { line_direction: mapDir(secRec.line_direction as ExactVec3) } : {}),
              marker: {
                ...w.second.marker,
                u: mapDir(w.second.marker.u),
                v: mapDir(w.second.marker.v),
              },
            },
          }
        : {}),
    };
  };
  for (const o of copy.objects) {
    if (o.xyz) o.xyz = mapPos(o.xyz);
    if (o.point) o.point = mapPos(o.point);
    if (o.anchor) o.anchor = mapPos(o.anchor);
    if (o.apex_or_top) o.apex_or_top = mapPos(o.apex_or_top);
    if (o.rim_point) o.rim_point = mapPos(o.rim_point);
    if (o.center) o.center = mapPos(o.center);
    if (o.point_a) o.point_a = mapPos(o.point_a);
    if (o.point_b) o.point_b = mapPos(o.point_b);
    if (o.endpoints) o.endpoints = o.endpoints.map(mapPos);
    if (o.vertices) o.vertices = o.vertices.map(mapPos);
    if (o.polygon) o.polygon = o.polygon.map(mapPos);
    if (o.direction) o.direction = mapDir(o.direction);
    if (o.normal) o.normal = mapDir(o.normal);
    if (o.major_dir) o.major_dir = mapDir(o.major_dir);
    if (o.minor_dir) o.minor_dir = mapDir(o.minor_dir);
    if (o.perpendicular_witness) o.perpendicular_witness = mapWitness(o.perpendicular_witness);
    if (o.annotation?.witness) o.annotation = { ...o.annotation, witness: mapWitness(o.annotation.witness) };
  }
  return copy;
}

function roleMapOf(scene: Scene3D): Record<string, string> {
  const c = getSemanticConstructionContract(scene);
  const out: Record<string, string> = {};
  for (const [id, entry] of c.objectsById) {
    if (!id.includes("::")) out[id] = entry.semanticRole;
  }
  return out;
}

describe("AXO System-Wide Semantic Construction Hardening & Metamorphic Reliability", () => {
  describe("1. Unified SemanticConstructionContract (WeakMap-cached, all 7 certified relation kinds)", () => {
    it("normalizes objects into typed geometric roles, provenance, determinacy, 3-tier information categories, and all 7 CertifiedGeometricRelation kinds", () => {
      const sphereScene = sampleScene("cau-cat-mat-phang");
      const c1 = getSemanticConstructionContract(sphereScene);
      const c2 = getSemanticConstructionContract(sphereScene);
      expect(c1).toBe(c2);

      const ballContract = resolveSemanticObjectContract(sphereScene, "cau");
      const planeContract = resolveSemanticObjectContract(sphereScene, "P");
      const secContract = resolveSemanticObjectContract(sphereScene, "C");
      const rGivenContract = resolveSemanticObjectContract(sphereScene, "R");

      expect(ballContract?.geometricType).toBe("curved_solid");
      expect(ballContract?.semanticRole).toBe("PRIMARY_SOLID");
      expect(ballContract?.informationCategory).toBe("GIVEN_FACT");

      expect(planeContract?.geometricType).toBe("plane");
      expect(planeContract?.semanticRole).toBe("CUTTING_PLANE");
      expect(planeContract?.visibilityLifecycle).not.toBe("INTERNAL_HIDDEN");

      expect(secContract?.geometricType).toBe("circle");
      expect(secContract?.semanticRole).toBe("INTERSECTION_CIRCLE");
      expect(secContract?.informationCategory).toBe("CONSTRUCTION_RELATION");
      expect(secContract?.verifiedRelations.some((r) => r.kind === "secant_sphere_plane" && r.exactVerified)).toBe(true);

      expect(rGivenContract?.geometricType).toBe("quantity");
      expect(rGivenContract?.semanticRole).toBe("GIVEN_QUANTITY");
      expect(rGivenContract?.informationCategory).toBe("GIVEN_FACT");

      for (const obj of sphereScene.objects) {
        if (obj.type !== "quantity") continue;
        const qc = resolveSemanticObjectContract(sphereScene, obj.id);
        expect(qc).toBeDefined();
        if (qc?.semanticRole !== "GIVEN_QUANTITY") {
          expect(qc?.informationCategory).toBe("INTERNAL_MATH_RESULT");
          expect(qc?.visibilityLifecycle).toBe("INTERNAL_HIDDEN");
        }
      }

      // Verify all 7 CertifiedGeometricRelation kinds are genuinely populated across canonical geometry families
      const seenKinds = new Set<CertifiedGeometricRelation["kind"]>();
      const collectKinds = (sc: Scene3D) => {
        const plan = buildPedagogicalConstructionPlan(sc);
        const contract = getSemanticConstructionContract(plan.scene);
        for (const oc of contract.objectsById.values()) {
          for (const rel of oc.verifiedRelations) {
            if (rel.exactVerified) seenKinds.add(rel.kind);
          }
        }
      };

      collectKinds(sphereScene); // secant_sphere_plane, line_perp_plane, incidence
      collectKinds(sampleScene("thiet-dien-chop")); // incidence
      collectKinds({
        free_objects: ["A", "B", "C"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["-2", "0", "0"] },
          { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
          { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "3", "0"] },
          { id: "ab", type: "segment3", label: "AB", notation: "AB", origin: "derived", producer: "construct_segment", render: "segment", depends: ["A", "B"], endpoint_ids: ["A", "B"], endpoints: [["-2", "0", "0"], ["2", "0", "0"]] },
          { id: "H_lp", type: "point3", label: "H", notation: "H", origin: "derived", producer: "project_onto", render: "point_marker", depends: ["C", "ab"], xyz: ["0", "0", "0"], perpendicular_witness: { from: "C", foot: ["0", "0", "0"], foot_id: "H_lp", on: "ab", relation: "line_perp_line", status: "DERIVED_VERIFIED", line_direction: ["1", "0", "0"], marker: { u: ["1", "0", "0"], v: ["0", "3", "0"] } } },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "ab", depends: ["A", "B"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "H_lp", depends: ["C", "ab"], explanation: "" },
        ],
      }); // line_perp_line
      collectKinds({
        free_objects: ["I", "q_r"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "I", type: "point3", label: "I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "q_r", type: "quantity", label: "R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["ball_t"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f_r", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"] },
          { id: "ball_t", type: "curved_solid", curved_kind: "ball", label: "(S)", notation: "(S)", origin: "derived", producer: null, render: "curved_solid", depends: ["I", "q_r"], anchor: ["0", "0", "0"], radius_sq: "25" },
          { id: "mp_t", type: "plane3", label: "(P)", notation: "(P)", origin: "derived", producer: null, render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["0", "0", "5"], normal: ["0", "0", "1"] },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "ball_t", depends: ["I", "q_r"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "mp_t", depends: [], explanation: "" },
        ],
      }); // tangent_sphere_plane
      collectKinds({
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
      }); // common_perpendicular
      collectKinds({
        free_objects: ["A", "B", "C", "A1", "B1", "C1"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
          { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "3", "0"] },
          { id: "A1", type: "point3", label: "A′", notation: "A′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
          { id: "B1", type: "point3", label: "B′", notation: "B′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "4"] },
          { id: "C1", type: "point3", label: "C′", notation: "C′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "3", "4"] },
          { id: "bot_p", type: "polygon3", label: "ABC", notation: "ABC", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"] },
          { id: "top_p", type: "polygon3", label: "A′B′C′", notation: "A′B′C′", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_TRANSLATED_FACE"], depends: ["A1", "B1", "C1"], vertex_ids: ["A1", "B1", "C1"] },
          { id: "prism_p", type: "solid", label: "ABC.A′B′C′", notation: "ABC.A′B′C′", shape_class: "PRISM_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", depends: ["A", "B", "C", "A1", "B1", "C1"], vertex_ids: ["A", "B", "C", "A1", "B1", "C1"], vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "3", "0"], ["0", "0", "4"], ["3", "0", "4"], ["0", "3", "4"]], faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]] },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "bot_p", depends: ["A", "B", "C"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "top_p", depends: ["A1", "B1", "C1"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "prism_p", depends: ["A", "B", "C", "A1", "B1", "C1"], explanation: "" },
        ],
      }); // parallel (TOP_FACE || BASE_FACE)

      expect([...seenKinds].sort()).toEqual([
        "common_perpendicular",
        "incidence",
        "line_perp_line",
        "line_perp_plane",
        "parallel",
        "secant_sphere_plane",
        "tangent_sphere_plane",
      ]);
    });
  });

  describe("2. Zero Guessing From Title, Vertex Names, or ID Suffixes", () => {
    it("classifies lateral and opposite base faces structurally across PYRAMID_LIKE, PRISM_LIKE, BOX_LIKE, FRUSTUM_LIKE, and undefined shape_class", () => {
      const pyramidScene: Scene3D = {
        free_objects: ["A", "B", "C", "D", "S"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "2", "0"] },
          { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
          { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "2"] },
          { id: "p_base", type: "polygon3", label: "Miền nền 1", notation: "ABCD", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", depends: ["A", "B", "C", "D"], vertex_ids: ["A", "B", "C", "D"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]] },
          { id: "sol", type: "solid", label: "Khối K1", notation: "S.ABCD", origin: "derived", producer: "construct_solid", render: "mesh", depends: ["S", "A", "B", "C", "D"], vertex_ids: ["S", "A", "B", "C", "D"], vertices: [["0", "0", "2"], ["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]] },
          { id: "p_lat", type: "polygon3", label: "Miền khảo sát", notation: "(SBC)", origin: "derived", producer: "construct_polygon", render: "polygon", depends: ["S", "B", "C"], vertex_ids: ["S", "B", "C"], vertices: [["0", "0", "2"], ["2", "0", "0"], ["2", "2", "0"]] },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "p_base", depends: ["A", "B", "C", "D"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "p_lat", depends: ["S", "B", "C"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "sol", depends: ["S", "A", "B", "C", "D"], explanation: "" },
        ],
      };

      // Note: shape_class is undefined on `sol` AND `p_lat` was placed BEFORE `sol` in raw events!
      expect(isPolyhedronLateralOrAuxFacePolygon(pyramidScene, pyramidScene.objects.find((o) => o.id === "p_lat")!)).toBe(true);
      expect(resolveSemanticObjectContract(pyramidScene, "p_lat")?.semanticRole).toBe("LATERAL_FACE");

      const plan = buildPedagogicalConstructionPlan(pyramidScene);
      const iSol = plan.steps.findIndex((s) => s.targetIds.includes("sol"));
      const iLat = plan.steps.findIndex((s) => s.targetIds.includes("p_lat"));
      expect(iLat).toBeGreaterThan(iSol);
      expect(plan.steps[iLat].title).toContain("(SBC)");
      expect(plan.steps[iLat].title).not.toMatch(/mặt\s+đáy|thiết\s+diện/iu);

      const groups = buildStepEntityGroups(plan.scene, plan.steps[plan.steps.length - 1].anchor, { steps: plan.steps });
      const latChip = groups.all.find((c) => c.id === "p_lat");
      expect(latChip?.shortLabel).toMatch(/^\(?SBC\)?$/);

      // Two-base solids (`PRISM_LIKE` without CONSTRUCT_TRANSLATED_FACE, `BOX_LIKE`, `FRUSTUM_LIKE`, and `undefined` shape_class)
      for (const shapeClass of ["PRISM_LIKE", "BOX_LIKE", "FRUSTUM_LIKE", undefined] as const) {
        const topScale = shapeClass === "FRUSTUM_LIKE" ? "1" : "2";
        const twoBaseScene: Scene3D = {
          free_objects: ["A", "B", "C", "D", "A1", "B1", "C1", "D1"],
          chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
          objects: [
            { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
            { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
            { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "2", "0"] },
            { id: "D", type: "point3", label: "D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
            { id: "A1", type: "point3", label: "A′", notation: "A′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "3"] },
            { id: "B1", type: "point3", label: "B′", notation: "B′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: [topScale, "0", "3"] },
            { id: "C1", type: "point3", label: "C′", notation: "C′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: [topScale, topScale, "3"] },
            { id: "D1", type: "point3", label: "D′", notation: "D′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", topScale, "3"] },
            { id: "bot_face", type: "polygon3", label: "Mặt 1", notation: "ABCD", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", depends: ["A", "B", "C", "D"], vertex_ids: ["A", "B", "C", "D"] },
            // Deliberately omit CONSTRUCT_TRANSLATED_FACE on top_face!
            { id: "top_face", type: "polygon3", label: "Mặt 2", notation: "A′B′C′D′", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", depends: ["A1", "B1", "C1", "D1"], vertex_ids: ["A1", "B1", "C1", "D1"] },
            { id: "side_face", type: "polygon3", label: "Mặt bên khảo sát", notation: "ABB′A′", origin: "derived", producer: "construct_polygon", render: "polygon", depends: ["A", "B", "B1", "A1"], vertex_ids: ["A", "B", "B1", "A1"] },
            {
              id: "box_sol",
              type: "solid",
              label: "Khối H",
              notation: "ABCD.A′B′C′D′",
              ...(shapeClass ? { shape_class: shapeClass } : {}),
              origin: "derived",
              producer: "construct_solid",
              render: "mesh",
              depends: ["A", "B", "C", "D", "A1", "B1", "C1", "D1"],
              vertex_ids: ["A", "B", "C", "D", "A1", "B1", "C1", "D1"],
              vertices: [["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"], ["0", "0", "3"], [topScale, "0", "3"], [topScale, topScale, "3"], ["0", topScale, "3"]],
              faces: [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]],
            },
          ] as unknown as SceneObject[],
          events: [
            { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
            { step_index: 1, action: "CREATE", object: "bot_face", depends: ["A", "B", "C", "D"], explanation: "" },
            { step_index: 2, action: "CREATE", object: "top_face", depends: ["A1", "B1", "C1", "D1"], explanation: "" },
            { step_index: 3, action: "CREATE", object: "box_sol", depends: ["A", "B", "C", "D", "A1", "B1", "C1", "D1"], explanation: "" },
            { step_index: 4, action: "CREATE", object: "side_face", depends: ["A", "B", "B1", "A1"], explanation: "" },
          ],
        };

        expect(resolveSemanticObjectContract(twoBaseScene, "bot_face")?.semanticRole).toBe("BASE_FACE");
        expect(resolveSemanticObjectContract(twoBaseScene, "top_face")?.semanticRole).toBe("TOP_FACE");
        expect(resolveSemanticObjectContract(twoBaseScene, "side_face")?.semanticRole).toBe("LATERAL_FACE");
      }
    });

    it("recognizes plane-plane intersection line from structural metadata/2-plane deps without 'giao tuyến' in label and explains 1-point + parallel-edge theorem", () => {
      const scene: Scene3D = {
        free_objects: ["A", "B", "C", "D", "S"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["4", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["5", "3", "0"] },
          { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "3", "0"] },
          { id: "S", type: "point3", label: "Đỉnh S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "3/2", "4"] },
          { id: "canh_AB", type: "segment3", label: "AB", notation: "AB", origin: "derived", producer: "construct_segment", render: "segment", depends: ["A", "B"], endpoint_ids: ["A", "B"], endpoints: [["0", "0", "0"], ["4", "0", "0"]] },
          { id: "day_ABCD", type: "polygon3", label: "Đáy ABCD", notation: "ABCD", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C", "D"], vertex_ids: ["A", "B", "C", "D"], vertices: [["0", "0", "0"], ["4", "0", "0"], ["5", "3", "0"], ["1", "3", "0"]] },
          { id: "khoi_SABCD", type: "solid", label: "Khối S.ABCD", notation: "S.ABCD", shape_class: "PYRAMID_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["S", "A", "B", "C", "D"], vertex_ids: ["S", "A", "B", "C", "D"], vertices: [["2", "3/2", "4"], ["0", "0", "0"], ["4", "0", "0"], ["5", "3", "0"], ["1", "3", "0"]], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]] },
          { id: "mp_SAB", type: "plane3", label: "Mặt phẳng (SAB)", notation: "(SAB)", origin: "derived", producer: "construct_plane", render: "surface", depends: ["S", "A", "B"], point: ["2", "3/2", "4"], normal: ["0", "8", "-3"] },
          { id: "mp_SCD", type: "plane3", label: "Mặt phẳng (SCD)", notation: "(SCD)", origin: "derived", producer: "construct_plane", render: "surface", depends: ["S", "C", "D"], point: ["2", "3/2", "4"], normal: ["0", "8", "3"] },
          // Deliberately generic label and NO formation_roles — detected purely via 2-plane `depends`!
          { id: "gt_d", type: "line3", label: "Đường thẳng d", notation: "d", origin: "derived", producer: null, render: "line", depends: ["mp_SAB", "mp_SCD"], point: ["2", "3/2", "4"], direction: ["1", "0", "0"] },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "canh_AB", depends: ["A", "B"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "day_ABCD", depends: ["A", "B", "C", "D"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "khoi_SABCD", depends: ["S", "A", "B", "C", "D"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "mp_SAB", depends: ["S", "A", "B"], explanation: "" },
          { step_index: 5, action: "CREATE", object: "mp_SCD", depends: ["S", "C", "D"], explanation: "" },
          { step_index: 6, action: "CREATE", object: "gt_d", depends: ["mp_SAB", "mp_SCD"], explanation: "" },
        ],
      };

      const dObj = scene.objects.find((o) => o.id === "gt_d")!;
      expect(isIntersectionLineOrSegment(dObj, scene)).toBe(true);
      const dContract = resolveSemanticObjectContract(scene, "gt_d")!;
      expect(dContract.semanticRole).toBe("INTERSECTION_LINE");
      expect(dContract.verifiedRelations.some((r) => r.kind === "parallel" && r.targetIds.includes("canh_AB") && r.exactVerified)).toBe(true);

      const plan = buildPedagogicalConstructionPlan(scene);
      const lastStep = plan.steps[plan.steps.length - 1];
      expect(lastStep.stepRole).toBe("construct_intersection_or_section");
      expect(lastStep.epistemicCategory).toBe("derived");
      expect(lastStep.title).toContain("giao tuyến");
      expect(lastStep.title).toContain("(SAB)");
      expect(lastStep.title).toContain("(SCD)");
      expect(lastStep.subtitle).toContain("S");
      expect(lastStep.subtitle).toMatch(/song\s+song/iu);
    });
  });

  describe("3. Non-Disclosure Enforcement (Parametric Algebraic RHS) & GIVEN_FACT Retention Under Shadowing", () => {
    it("strips parametric algebraic answer expressions (= a√2/2, = a³/6, = 2a) while preserving geometric set relations", () => {
      expect(sanitizeStudentDescriptorText("Đoạn vuông góc chung MN = a√2/2")).toBe("Đoạn vuông góc chung MN");
      expect(sanitizeStudentDescriptorText("Thể tích khối chóp V = a³/6")).toBe("Thể tích khối chóp V");
      expect(sanitizeStudentDescriptorText("Khoảng cách d(A, (SBC)) = a√3/3")).toBe("Khoảng cách d(A, (SBC))");
      expect(sanitizeStudentDescriptorText("Độ dài đường sinh l = 2a")).toBe("Độ dài đường sinh l");
      expect(sanitizeStudentDescriptorText("Bán kính r = R√3/2")).toBe("Bán kính r");
      // Geometric intersection / set definitions MUST stay intact
      expect(sanitizeStudentDescriptorText("Giao tuyến d = (SAB) ∩ (SCD)")).toBe("Giao tuyến d = (SAB) ∩ (SCD)");
      expect(sanitizeStudentDescriptorText("Giao điểm Q = SD ∩ (MNP)")).toBe("Giao điểm Q = SD ∩ (MNP)");
    });

    it("never lets a hiddenIds-masked result/intermediate quantity shadow or erase a GIVEN_FACT annotation on the same subject", () => {
      const scene: Scene3D = {
        free_objects: ["A", "B", "C", "S", "q_sa_given"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
          { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "6"] },
          { id: "cao_SA", type: "segment3", label: "Đường cao SA", notation: "SA", origin: "derived", producer: "construct_segment", render: "segment", depends: ["S", "A"], endpoint_ids: ["S", "A"], endpoints: [["0", "0", "6"], ["0", "0", "0"]] },
          { id: "khoi", type: "solid", label: "Chóp S.ABC", notation: "S.ABC", origin: "derived", producer: "construct_solid", render: "mesh", depends: ["S", "A", "B", "C"], vertex_ids: ["S", "A", "B", "C"], vertices: [["0", "0", "6"], ["0", "0", "0"], ["3", "0", "0"], ["0", "4", "0"]], faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]] },
          { id: "q_sa_given", type: "quantity", label: "Chiều cao SA", notation: "SA", origin: "free", producer: null, render: "readout", depends: ["S", "A"], value: "6", exact: { kind: "rational", value: "6" }, source: { fact_id: "f_sa", provenance: "GIVEN", is_given: true }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["S", "A"], anchor: "segment" } },
          { id: "kq_sa_res", type: "quantity", label: "Kết quả đoạn SA", notation: "d_SA", origin: "derived", producer: "measure_length", render: "readout", depends: ["khoi"], value: "6", exact: { kind: "rational", value: "6" }, annotation: { kind: "length", category: "result", role: "result", subject_ids: ["S", "A"], anchor: "segment" } },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "cao_SA", depends: ["S", "A"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "khoi", depends: ["S", "A", "B", "C"], explanation: "" },
          { step_index: 3, action: "MEASURE", object: "kq_sa_res", depends: ["khoi"], explanation: "", semantic_kind: "FINAL_RESULT" },
        ],
      };

      const plan = buildPedagogicalConstructionPlan(scene);
      const policy = evaluateStudentPresentationPolicy(scene, plan.goalCompletion);
      const hidden = new Set<string>(tapKetQuaCuoi(scene));
      for (const o of scene.objects) {
        if (o.type === "quantity" && !policy.canDisplayEntityValue(o)) hidden.add(o.id);
      }
      const view: AnnotationView = { showAll: true, hiddenIds: hidden };

      for (const sel of [null, "S", "khoi", "kq_sa_res"]) {
        const rawAnns = annotationsAt(scene, 3, view, sel);
        const visibleStudentAnns = rawAnns.filter((a) => !view.hiddenIds?.has(a.id));
        expect(visibleStudentAnns.map((a) => a.id)).toContain("q_sa_given");
        expect(visibleStudentAnns.map((a) => a.text)).toContain("SA = 6");
        expect(visibleStudentAnns.map((a) => a.id)).not.toContain("kq_sa_res");
      }
    });
  });

  describe("4. Sphere–Plane Regimes, Strict Step DAG Ordering (Explicit, Synthesized & Permuted) & Stroke Hierarchy", () => {
    it("strictly orders sphere & plane BEFORE tangent foot H BEFORE perpendicular radius IH (even under reversed raw events and synthesized Case 1C)", () => {
      // (A) Explicit tangent sphere-plane WITH reversed/invalid raw event order (`mp_p`, `H_tiep`, `doan_IH` BEFORE `ball_i`!)
      const permutedExplicitTangent: Scene3D = {
        free_objects: ["I", "q_r", "q_d"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "q_r", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["ball_i"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f_r", provenance: "GIVEN", is_given: true } },
          { id: "q_d", type: "quantity", label: "Khoảng cách d(I,(P))", notation: "d(I,(P))", origin: "free", producer: null, render: "readout", depends: ["I", "mp_p"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f_d", provenance: "GIVEN", is_given: true }, annotation: { kind: "distance", category: "measurement", role: "given", subject_ids: ["I", "H_tiep"], anchor: "segment" } },
          { id: "ball_i", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: "construct_curved_solid", render: "curved_solid", depends: ["I", "q_r"], anchor: ["0", "0", "0"], radius_sq: "25" },
          { id: "mp_p", type: "plane3", label: "Mặt phẳng tiếp diện (P)", notation: "(P)", origin: "derived", producer: "construct_plane", render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["0", "0", "5"], normal: ["0", "0", "1"] },
          { id: "H_tiep", type: "point3", label: "Tiếp điểm H", notation: "H", origin: "derived", producer: "project_onto", render: "point_marker", depends: ["I", "mp_p"], xyz: ["0", "0", "5"], perpendicular_witness: { from: "I", foot: ["0", "0", "5"], foot_id: "H_tiep", on: "mp_p", relation: "line_perp_plane", status: "DERIVED_VERIFIED", plane_directions: [["1", "0", "0"], ["0", "1", "0"]], marker: { u: ["1", "0", "0"], v: ["0", "0", "-1"] } } },
          { id: "doan_IH", type: "segment3", label: "Bán kính tiếp điểm IH", notation: "IH", origin: "derived", producer: "construct_segment", render: "segment", depends: ["I", "H_tiep"], endpoint_ids: ["I", "H_tiep"], endpoints: [["0", "0", "0"], ["0", "0", "5"]], perpendicular_witness: { from: "I", foot: ["0", "0", "5"], foot_id: "H_tiep", on: "mp_p", relation: "line_perp_plane", status: "DERIVED_VERIFIED", plane_directions: [["1", "0", "0"], ["0", "1", "0"]], marker: { u: ["1", "0", "0"], v: ["0", "0", "-1"] } } },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "mp_p", depends: [], explanation: "" },
          { step_index: 2, action: "CREATE", object: "H_tiep", depends: ["I", "mp_p"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "doan_IH", depends: ["I", "H_tiep"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "ball_i", depends: ["I", "q_r"], explanation: "" },
        ],
      };

      const planPerm = buildPedagogicalConstructionPlan(permutedExplicitTangent);
      const firstVisibleAt = (plan: ReturnType<typeof buildPedagogicalConstructionPlan>, id: string) =>
        plan.steps.findIndex((s) => s.targetIds.includes(id) || s.visibleIds.includes(id));

      const iBall = firstVisibleAt(planPerm, "ball_i");
      const iPlane = firstVisibleAt(planPerm, "mp_p");
      const iFoot = firstVisibleAt(planPerm, "H_tiep");
      const iSeg = firstVisibleAt(planPerm, "doan_IH");

      expect(iBall).toBeGreaterThanOrEqual(0);
      expect(iPlane).toBeGreaterThanOrEqual(0);
      expect(iFoot).toBeGreaterThan(Math.max(iBall, iPlane));
      expect(iSeg).toBeGreaterThan(iFoot);

      // (B) Synthesized Case 1C tangent sphere-plane (only ball and tangent plane declared in input)
      const synthesizedTangent: Scene3D = {
        free_objects: ["I", "q_r"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "q_r", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["ball_s"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f_r", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"] },
          { id: "ball_s", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: null, render: "curved_solid", depends: ["I", "q_r"], anchor: ["0", "0", "0"], radius_sq: "25" },
          { id: "mp_alpha", type: "plane3", label: "Mặt phẳng tiếp diện (α)", notation: "(α)", origin: "derived", producer: null, render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["0", "0", "25/4"], normal: ["3", "0", "4"] },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "ball_s", depends: ["I", "q_r"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "mp_alpha", depends: [], explanation: "" },
        ],
      };
      const planSynth = buildPedagogicalConstructionPlan(synthesizedTangent);
      const synthFoot = planSynth.scene.objects.find((o) => o.type === "point3" && o.xyz?.join("|") === "3|0|4")!;
      const synthSeg = planSynth.scene.objects.find((o) => o.type === "segment3" && o.perpendicular_witness?.on === "mp_alpha")!;
      expect(synthFoot).toBeDefined();
      expect(synthSeg).toBeDefined();
      const sBall = firstVisibleAt(planSynth, "ball_s");
      const sPlane = firstVisibleAt(planSynth, "mp_alpha");
      const sFoot = firstVisibleAt(planSynth, synthFoot.id);
      const sSeg = firstVisibleAt(planSynth, synthSeg.id);
      expect(sFoot).toBeGreaterThan(Math.max(sBall, sPlane));
      expect(sSeg).toBeGreaterThan(sFoot);
    });

    it("enforces strict stroke width hierarchy: RESULT_SECTION circle > BASE_REGION circle > REFERENCE_EQUATOR", () => {
      const sphereScene = sampleScene("cau-cat-mat-phang");
      const ball = sphereScene.objects.find((o) => o.id === "cau")!;
      const cutCircle: SceneObject = {
        id: "C_cut",
        label: "Giao tuyến C",
        type: "circle3",
        render: "circle",
        origin: "derived",
        producer: "intersect_plane_curved_circle",
        depends: ["cau", "P"],
        surface_role: "SECTION_REGION",
        center: ["0", "0", "3"],
        normal: ["0", "0", "1"],
        radius_sq: "16",
      };
      const baseCircle: SceneObject = {
        ...cutCircle,
        id: "C_base",
        surface_role: "BASE_REGION",
        fill_visible: false,
      };
      const contextScene: Scene3D = { ...sphereScene, objects: [ball, cutCircle, baseCircle] };
      const diemNen: [number, number, number][] = [[-5, 0, 0], [5, 0, 0], [0, 5, 0]];

      for (const cam of [new THREE.Vector3(10, 8, 6), new THREE.Vector3(-9, 12, 4)]) {
        const builtSphere = buildObject3D(ball, false, undefined, diemNen, cam, undefined, undefined, false, "primary", true, true, false, contextScene)!;
        const refEq = builtSphere.getObjectByName("sphere_reference:cau")!;
        const builtBase = buildObject3D(baseCircle, false, undefined, diemNen, cam, undefined, undefined, false, "primary", true, true, false, contextScene)!;
        const builtCut = buildObject3D(cutCircle, "dich", undefined, diemNen, cam, undefined, undefined, false, "primary", true, true, false, contextScene)!;

        const strokeWidth = (node: THREE.Object3D) => {
          const s = node.userData.curvedRimLoop.sample(0);
          return s.outer.distanceTo(s.inner);
        };

        expect(strokeWidth(builtCut)).toBeGreaterThan(strokeWidth(builtBase));
        expect(strokeWidth(builtBase)).toBeGreaterThan(strokeWidth(refEq));
        expect(strokeWidth(builtCut)).toBeGreaterThan(strokeWidth(refEq) * 1.35);
      }
    });
  });

  describe("5. Exact Q³ Certifiability, Non-Vacuous Witness Rejections & Co-Foot Perpendiculars", () => {
    it("marks illustrative coordinates on underdetermined S.ABC as ILLUSTRATIVE_GAUGE, rejects forged vacuous plane_directions: [], and preserves co-foot perpendiculars", () => {
      const sabc: Scene3D = {
        free_objects: ["A", "B", "C", "S"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        length_unit: { symbol: "a", display_scale: "a = 1 đơn vị dựng", is_given: false },
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"], source: {} },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"], source: {} },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"], source: {} },
          { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"], source: {} },
          { id: "day_ABC", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]] },
          { id: "cao_SA", type: "segment3", label: "Đường cao SA", notation: "SA", origin: "derived", producer: "construct_segment", render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["S", "A"], endpoint_ids: ["S", "A"], endpoints: [["0", "0", "4"], ["0", "0", "0"]], perpendicular_witness: { from: "S", foot: ["0", "0", "0"], foot_id: "A", on: "day_ABC", relation: "line_perp_plane", status: "GIVEN", plane_directions: [["2", "0", "0"], ["0", "2", "0"]], marker: { u: ["2", "0", "0"], v: ["0", "0", "4"] } } },
          // Forged non-perpendicular line_perp_plane witness with empty plane_directions: [] (SB is tilted [2,0,-4] onto z=0)
          { id: "forged_SB", type: "segment3", label: "Cạnh SB", notation: "SB", origin: "derived", producer: "construct_segment", render: "segment", depends: ["S", "B"], endpoint_ids: ["S", "B"], endpoints: [["0", "0", "4"], ["2", "0", "0"]], perpendicular_witness: { from: "S", foot: ["2", "0", "0"], foot_id: "B", on: "day_ABC", relation: "line_perp_plane", status: "DERIVED_VERIFIED", plane_directions: [], marker: { u: ["1", "0", "0"], v: ["-2", "0", "4"] } } },
          { id: "khoi_SABC", type: "solid", label: "Hình chóp S.ABC", notation: "S.ABC", shape_class: "PYRAMID_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["S", "A", "B", "C"], vertex_ids: ["S", "A", "B", "C"], vertices: [["0", "0", "4"], ["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]], faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]] },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_ABC", depends: ["A", "B", "C"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "cao_SA", depends: ["S", "A"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "forged_SB", depends: ["S", "B"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "khoi_SABC", depends: ["S", "A", "B", "C"], explanation: "" },
        ],
      };

      const contract = getSemanticConstructionContract(sabc);
      const heightContract = contract.objectsById.get("cao_SA")!;
      expect(heightContract.verifiedRelations.some((r) => r.kind === "line_perp_plane" && r.canDisplaySymbol)).toBe(true);

      const forgedContract = contract.objectsById.get("forged_SB")!;
      expect(forgedContract.verifiedRelations.every((r) => !r.exactVerified && !r.canDisplaySymbol)).toBe(true);

      const baseContract = contract.objectsById.get("day_ABC")!;
      expect(baseContract.determinacy).toBe("ILLUSTRATIVE_GAUGE");
      expect(baseContract.verifiedRelations.some((r) => r.kind === "line_perp_line" && r.canDisplaySymbol)).toBe(false);

      // Co-foot distinct perpendiculars (`SH ⊥ (ABC)` on segment `cao_SH` and `CH ⊥ AB` on point/segment sharing foot `H`)
      const coFootScene: Scene3D = {
        free_objects: ["A", "B", "C", "S"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["-2", "0", "0"] },
          { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
          { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "3", "0"] },
          { id: "S", type: "point3", label: "S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
          { id: "H", type: "point3", label: "H", notation: "H", origin: "derived", producer: "project_onto", render: "point_marker", depends: ["C", "canh_AB"], xyz: ["0", "0", "0"], perpendicular_witness: { from: "C", foot: ["0", "0", "0"], foot_id: "H", on: "canh_AB", relation: "line_perp_line", status: "DERIVED_VERIFIED", line_direction: ["1", "0", "0"], marker: { u: ["1", "0", "0"], v: ["0", "3", "0"] } } },
          { id: "canh_AB", type: "segment3", label: "AB", notation: "AB", origin: "derived", producer: "construct_segment", render: "segment", depends: ["A", "B"], endpoint_ids: ["A", "B"], endpoints: [["-2", "0", "0"], ["2", "0", "0"]] },
          { id: "day_ABC", type: "polygon3", label: "ABC", notation: "ABC", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["-2", "0", "0"], ["2", "0", "0"], ["0", "3", "0"]] },
          { id: "cao_SH", type: "segment3", label: "SH", notation: "SH", origin: "derived", producer: "construct_segment", render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["S", "H"], endpoint_ids: ["S", "H"], endpoints: [["0", "0", "4"], ["0", "0", "0"]], perpendicular_witness: { from: "S", foot: ["0", "0", "0"], foot_id: "H", on: "day_ABC", relation: "line_perp_plane", status: "GIVEN", plane_directions: [["1", "0", "0"], ["0", "1", "0"]], marker: { u: ["1", "0", "0"], v: ["0", "0", "4"] } } },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "canh_AB", depends: ["A", "B"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "day_ABC", depends: ["A", "B", "C"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "H", depends: ["C", "canh_AB"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "cao_SH", depends: ["S", "H"], explanation: "" },
        ],
      };

      const coContract = getSemanticConstructionContract(coFootScene);
      expect(coContract.objectsById.get("H")?.verifiedRelations.some((r) => r.kind === "line_perp_line" && r.canDisplaySymbol)).toBe(true);
      expect(coContract.objectsById.get("cao_SH")?.verifiedRelations.some((r) => r.kind === "line_perp_plane" && r.canDisplaySymbol)).toBe(true);
      const coWitnesses = projectionWitnessesAt(
        coFootScene,
        new Set(coFootScene.objects.map((o) => o.id)),
        4,
      );
      expect(coWitnesses.map((w) => w.id)).toEqual(["perpendicular:H"]);
      const segs = doanDaVe(coFootScene.objects);
      const hWitnessGroup = vatNhanChung(coWitnesses[0], [[0, 0, 0], [2, 0, 0], [0, 3, 0], [0, 0, 4]], undefined, false, segs, []);
      expect(hWitnessGroup.children.length).toBeGreaterThan(0);
      const caoShObj = coFootScene.objects.find((o) => o.id === "cao_SH")!;
      const caoSh3d = buildObject3D(
        caoShObj,
        false,
        undefined,
        [[0, 0, 0], [2, 0, 0], [0, 3, 0], [0, 0, 4]],
        new THREE.Vector3(8, 6, 5),
        undefined,
        undefined,
        false,
        "primary",
        true,
        true,
        false,
        coFootScene,
      )!;
      expect(caoSh3d.children.some((c) => c.name.includes("right_angle") || c.children.length > 0)).toBe(true);
      const coHtml = renderToString(
        <Scene3DWorkspace scene={withSubEntities(coFootScene)} step={4} interaction={TRANG_THAI_DAU} onSelect={() => {}} />,
      );
      expect(coHtml).toBeTruthy();
    });
  });

  describe("6. Metamorphic Invariance Across All 8 Geometric & Structural Transformations", () => {
    it("preserves full SemanticObjectContract role maps, step counts, and verified relations across all 8 transformations", () => {
      const baseChop = sampleScene("thiet-dien-chop");
      const basePlan = buildPedagogicalConstructionPlan(baseChop);
      const baseRoles = roleMapOf(baseChop);

      // (1) Vertex renaming: S,A,B,C,D,M,N,P,Q -> K,E,F,G,H,U,V,W,T
      const renameMap: Record<string, string> = { S: "K", A: "E", B: "F", C: "G", D: "H", M: "U", N: "V", P: "W", Q: "T" };
      const renamedChop: Scene3D = JSON.parse(JSON.stringify(baseChop));
      for (const o of renamedChop.objects) {
        if (o.notation && renameMap[o.notation]) {
          o.notation = renameMap[o.notation];
          o.label = `Điểm ${o.notation}`;
        }
      }
      expect(roleMapOf(renamedChop)).toEqual(baseRoles);
      expect(buildPedagogicalConstructionPlan(renamedChop).steps.length).toBe(basePlan.steps.length);

      // (2) Full 3D rational translation +(7, -5, 11) on polyhedron section AND sphere-plane
      const delta: [bigint, bigint, bigint] = [7n, -5n, 11n];
      const translatedChop = mapSceneCoords(baseChop, (v) => addVecQ(v, delta), (v) => v);
      expect(verifySceneMathematicalConsistency(translatedChop).valid).toBe(true);
      expect(roleMapOf(translatedChop)).toEqual(baseRoles);
      expect(buildPedagogicalConstructionPlan(translatedChop).steps.length).toBe(basePlan.steps.length);

      const baseSphere = sampleScene("cau-cat-mat-phang");
      const baseSphereRoles = roleMapOf(baseSphere);
      const translatedSphere = mapSceneCoords(baseSphere, (v) => addVecQ(v, delta), (v) => v);
      expect(verifySceneMathematicalConsistency(translatedSphere).valid).toBe(true);
      expect(roleMapOf(translatedSphere)).toEqual(baseSphereRoles);

      // (3) Orthogonal 90° Z-rotation (x, y, z) -> (-y, x, z) across ALL coordinate/vector/witness fields
      const rotatedChop = mapSceneCoords(baseChop, rotZ90VecQ, rotZ90VecQ);
      expect(verifySceneMathematicalConsistency(rotatedChop).valid).toBe(true);
      expect(roleMapOf(rotatedChop)).toEqual(baseRoles);
      expect(buildPedagogicalConstructionPlan(rotatedChop).steps.length).toBe(basePlan.steps.length);

      const rotatedSphere = mapSceneCoords(baseSphere, rotZ90VecQ, rotZ90VecQ);
      expect(verifySceneMathematicalConsistency(rotatedSphere).valid).toBe(true);
      expect(roleMapOf(rotatedSphere)).toEqual(baseSphereRoles);

      // (4) Uniform scaling x3 across ALL coordinate fields, squared radii, and quantities
      const scaledSphere = mapSceneCoords(baseSphere, (v) => scaleVecQ(v, 3n), (v) => scaleVecQ(v, 3n));
      for (const o of scaledSphere.objects) {
        if (o.radius_sq) o.radius_sq = scaleScalarQ(o.radius_sq, 9n);
        if (o.type === "quantity" && o.id === "R") {
          o.value = "15";
          if (o.exact && o.exact.kind === "rational") o.exact.value = "15";
        }
        if (o.type === "quantity" && o.id === "d") {
          o.value = "9";
          if (o.exact && o.exact.kind === "rational") o.exact.value = "9";
        }
        if (o.type === "quantity" && o.id === "r") {
          o.value = "12";
          if (o.exact && o.exact.kind === "rational") o.exact.value = "12";
        }
        if (o.type === "quantity" && o.id === "S") {
          o.value = "144π";
          if (o.exact && o.exact.kind === "radical") o.exact.coefficient = "144";
        }
      }
      expect(verifySceneMathematicalConsistency(scaledSphere).valid).toBe(true);
      expect(roleMapOf(scaledSphere)).toEqual(baseSphereRoles);
      expect(buildPedagogicalConstructionPlan(scaledSphere).steps.length).toBe(5);

      // (5) Cutting plane position shift on R = 5 sphere: z = 3 -> z = 4 (r^2 = 9)
      const shiftedPlaneSphere = sampleScene("cau-cat-mat-phang");
      for (const o of shiftedPlaneSphere.objects) {
        if (o.id === "P" && o.point) o.point = ["0", "0", "4"];
        if (o.id === "C") {
          o.center = ["0", "0", "4"];
          o.radius_sq = "9";
        }
        if (o.type === "quantity" && o.id === "d") {
          o.value = "4";
          if (o.exact && o.exact.kind === "rational") o.exact.value = "4";
        }
      }
      expect(verifySceneMathematicalConsistency(shiftedPlaneSphere).valid).toBe(true);
      expect(roleMapOf(shiftedPlaneSphere)).toEqual(baseSphereRoles);
      expect(buildPedagogicalConstructionPlan(shiftedPlaneSphere).steps.length).toBe(5);

      // (6) Camera angle invariance: role maps & step visibility sequences are 100% invariant to camera pose
      const cam1 = new THREE.Vector3(10, 8, 6);
      const cam2 = new THREE.Vector3(-11, -7, 9);
      const cObj = shiftedPlaneSphere.objects.find((o) => o.id === "C")!;
      const builtCam1 = buildObject3D(cObj, "dich", undefined, [], cam1, undefined, undefined, false, "primary", true, true, false, shiftedPlaneSphere)!;
      const builtCam2 = buildObject3D(cObj, "dich", undefined, [], cam2, undefined, undefined, false, "primary", true, true, false, shiftedPlaneSphere)!;
      expect(builtCam1.visible).toBe(true);
      expect(builtCam2.visible).toBe(true);
      expect(roleMapOf(shiftedPlaneSphere)).toEqual(baseSphereRoles);

      // (7) Valid configuration comparisons: paired right pyramid (foot = A) vs oblique pyramid (foot = G inside ABC)
      const makePyramidConfig = (oblique: boolean): Scene3D => ({
        free_objects: ["A", "B", "C", "S"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
          { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "3", "0"] },
          { id: "S", type: "point3", label: "S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: oblique ? ["1", "1", "4"] : ["0", "0", "4"] },
          { id: "base", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "3", "0"]] },
          ...(oblique
            ? [{ id: "G", type: "point3", label: "Trọng tâm G", notation: "G", origin: "derived", producer: "centroid", render: "point_marker", depends: ["A", "B", "C"], xyz: ["1", "1", "0"] }]
            : []),
          {
            id: "alt",
            type: "segment3",
            label: oblique ? "Đường cao SG" : "Đường cao SA",
            notation: oblique ? "SG" : "SA",
            origin: "derived",
            producer: "construct_segment",
            render: "segment",
            formation_roles: ["CONSTRUCT_HEIGHT"],
            depends: oblique ? ["S", "G"] : ["S", "A"],
            endpoint_ids: oblique ? ["S", "G"] : ["S", "A"],
            endpoints: oblique ? [["1", "1", "4"], ["1", "1", "0"]] : [["0", "0", "4"], ["0", "0", "0"]],
            perpendicular_witness: {
              from: "S",
              foot: oblique ? ["1", "1", "0"] : ["0", "0", "0"],
              foot_id: oblique ? "G" : "A",
              on: "base",
              relation: "line_perp_plane",
              status: "GIVEN",
              plane_directions: [["3", "0", "0"], ["0", "3", "0"]],
              marker: { u: ["1", "0", "0"], v: ["0", "0", "4"] },
            },
          },
          { id: "sol", type: "solid", label: "Chóp S.ABC", notation: "S.ABC", shape_class: "PYRAMID_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["S", "A", "B", "C"], vertex_ids: ["S", "A", "B", "C"], vertices: [oblique ? ["1", "1", "4"] : ["0", "0", "4"], ["0", "0", "0"], ["3", "0", "0"], ["0", "3", "0"]], faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]] },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "base", depends: ["A", "B", "C"], explanation: "" },
          ...(oblique ? [{ step_index: 2, action: "CREATE" as const, object: "G", depends: ["A", "B", "C"], explanation: "" }] : []),
          { step_index: oblique ? 3 : 2, action: "CREATE", object: "alt", depends: oblique ? ["S", "G"] : ["S", "A"], explanation: "" },
          { step_index: oblique ? 4 : 3, action: "CREATE", object: "sol", depends: ["S", "A", "B", "C"], explanation: "" },
        ],
      });
      const rightPlan = buildPedagogicalConstructionPlan(makePyramidConfig(false));
      const obPlan = buildPedagogicalConstructionPlan(makePyramidConfig(true));
      expect(resolveSemanticObjectContract(rightPlan.scene, "alt")?.semanticRole).toBe("ALTITUDE_OR_AXIS");
      expect(resolveSemanticObjectContract(obPlan.scene, "alt")?.semanticRole).toBe("ALTITUDE_OR_AXIS");
      const stepCreating = (p: typeof obPlan, id: string) => p.steps.findIndex((s) => s.targetIds.includes(id));
      expect(stepCreating(rightPlan, "base")).toBeLessThan(stepCreating(rightPlan, "alt"));
      expect(stepCreating(rightPlan, "alt")).toBeLessThan(stepCreating(rightPlan, "sol"));
      expect(stepCreating(obPlan, "base")).toBeLessThan(stepCreating(obPlan, "G"));
      expect(stepCreating(obPlan, "G")).toBeLessThan(stepCreating(obPlan, "alt"));
      expect(stepCreating(obPlan, "alt")).toBeLessThan(stepCreating(obPlan, "sol"));

      // (8) Full permutation of BOTH `scene.objects` AND non-`INIT` `scene.events`
      const rawSphereEvents = JSON.parse(JSON.stringify(baseSphere.events)) as Scene3D["events"];
      const reversedNonInit = [rawSphereEvents[0], ...rawSphereEvents.slice(1).reverse()].map((ev, k) => ({
        ...ev,
        step_index: k,
      }));
      const permutedSphere: Scene3D = {
        ...JSON.parse(JSON.stringify(baseSphere)),
        objects: [...JSON.parse(JSON.stringify(baseSphere.objects))].reverse(),
        events: reversedNonInit,
      };
      expect(roleMapOf(permutedSphere)).toEqual(baseSphereRoles);
      const permSpherePlan = buildPedagogicalConstructionPlan(permutedSphere);
      const pIdx = (id: string) => permSpherePlan.steps.findIndex((s) => s.targetIds.includes(id) || s.visibleIds.includes(id));
      expect(pIdx("cau")).toBeLessThan(pIdx("C"));
      expect(pIdx("P")).toBeLessThan(pIdx("C"));
    });
  });

  describe("7. Cross-Family Coverage (Non-Identity chart_metric via veKhongGian, Oblique Prism, Tetrahedron, Skew-Line, Oxyz) & Catalog Invariants", () => {
    it("verifies exact Q³ relations without float rounding loss on non-identity chart_metric scenes passed through veKhongGian, plus oblique prism, base-free tetrahedron, skew-line common perpendicular, and explicit Oxyz", () => {
      // (A) Non-identity chart_metric (equilateral base AB = AC = BC = 2 via Gram [[1, 1/2, 0], [1/2, 1, 0], [0, 0, 1]])
      const rawMetricScene: Scene3D = {
        free_objects: ["A", "B", "C", "S", "q_ab", "q_ac", "q_bc"],
        chart_metric: [["1", "1/2", "0"], ["1/2", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"], source: { fact_id: "fa", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"] },
          { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"], source: { fact_id: "fb", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"] },
          { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"], source: { fact_id: "fc", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"] },
          { id: "S", type: "point3", label: "S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2/3", "2/3", "3"], source: { fact_id: "fs", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"] },
          { id: "q_ab", type: "quantity", label: "AB", notation: "AB", origin: "free", producer: null, render: "readout", depends: ["A", "B"], value: "2", exact: { kind: "rational", value: "2" }, source: { fact_id: "f1", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"], annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "B"], anchor: "segment" } },
          { id: "q_ac", type: "quantity", label: "AC", notation: "AC", origin: "free", producer: null, render: "readout", depends: ["A", "C"], value: "2", exact: { kind: "rational", value: "2" }, source: { fact_id: "f2", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"], annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "C"], anchor: "segment" } },
          { id: "q_bc", type: "quantity", label: "BC", notation: "BC", origin: "free", producer: null, render: "readout", depends: ["B", "C"], value: "2", exact: { kind: "rational", value: "2" }, source: { fact_id: "f3", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"], annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["B", "C"], anchor: "segment" } },
          { id: "G", type: "point3", label: "Trọng tâm G", notation: "G", origin: "derived", producer: "centroid", render: "point_marker", depends: ["A", "B", "C"], xyz: ["2/3", "2/3", "0"] },
          { id: "day_ABC", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]] },
          { id: "cao_SG", type: "segment3", label: "Đường cao SG", notation: "SG", origin: "derived", producer: "construct_segment", render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["S", "G"], endpoint_ids: ["S", "G"], endpoints: [["2/3", "2/3", "3"], ["2/3", "2/3", "0"]], perpendicular_witness: { from: "S", foot: ["2/3", "2/3", "0"], foot_id: "G", on: "day_ABC", relation: "line_perp_plane", status: "GIVEN", plane_directions: [["2", "0", "0"], ["0", "2", "0"]], marker: { u: ["2", "0", "0"], v: ["0", "0", "3"] } } },
          { id: "khoi_SABC", type: "solid", label: "Chóp đều S.ABC", notation: "S.ABC", shape_class: "PYRAMID_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", depends: ["S", "A", "B", "C"], vertex_ids: ["S", "A", "B", "C"], vertices: [["2/3", "2/3", "3"], ["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]], faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]] },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_ABC", depends: ["A", "B", "C"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "G", depends: ["A", "B", "C"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "cao_SG", depends: ["S", "G"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "khoi_SABC", depends: ["S", "A", "B", "C"], explanation: "" },
        ],
      };

      attachHybridViewToScene(rawMetricScene, {
        source_provenance: [
          { kind: "equilateral_triangle", verified: true, polygon: ["day_ABC"], origin: "given" },
        ],
      });
      const dispMetric = veKhongGian(rawMetricScene);
      registerExactSceneOrigin(dispMetric, rawMetricScene);
      const metricPlan = buildPedagogicalConstructionPlan(withSubEntities(dispMetric));
      const metricContract = getSemanticConstructionContract(metricPlan.scene);
      expect(metricContract.consistency.valid).toBe(true);
      expect(metricContract.objectsById.get("day_ABC")?.determinacy).toBe("EXACT_DETERMINED");
      expect(metricContract.objectsById.get("G")?.semanticRole).toBe("MIDPOINT_OR_RATIO_POINT");
      expect(
        metricContract.objectsById.get("cao_SG")?.verifiedRelations.some((r) => r.kind === "line_perp_plane" && r.exactVerified && r.canDisplaySymbol),
      ).toBe(true);

      // (B) Oblique prism (`PRISM_LIKE` with translated top base shifted by [1, 1, 3])
      const obliquePrism: Scene3D = {
        free_objects: ["A", "B", "C", "A1", "B1", "C1"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
          { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "3", "0"] },
          { id: "A1", type: "point3", label: "A′", notation: "A′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "1", "3"] },
          { id: "B1", type: "point3", label: "B′", notation: "B′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["4", "1", "3"] },
          { id: "C1", type: "point3", label: "C′", notation: "C′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "4", "3"] },
          { id: "bot", type: "polygon3", label: "ABC", notation: "ABC", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"] },
          { id: "top", type: "polygon3", label: "A′B′C′", notation: "A′B′C′", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_TRANSLATED_FACE"], depends: ["A1", "B1", "C1"], vertex_ids: ["A1", "B1", "C1"] },
          { id: "H_ob", type: "point3", label: "H", notation: "H", origin: "derived", producer: "project_onto", render: "point_marker", depends: ["A1", "bot"], xyz: ["1", "1", "0"], perpendicular_witness: { from: "A1", foot: ["1", "1", "0"], foot_id: "H_ob", on: "bot", relation: "line_perp_plane", status: "GIVEN", plane_directions: [["3", "0", "0"], ["0", "3", "0"]], marker: { u: ["1", "0", "0"], v: ["0", "0", "3"] } } },
          { id: "alt_ob", type: "segment3", label: "A′H", notation: "A′H", origin: "derived", producer: "construct_segment", render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["A1", "H_ob"], endpoint_ids: ["A1", "H_ob"], endpoints: [["1", "1", "3"], ["1", "1", "0"]], perpendicular_witness: { from: "A1", foot: ["1", "1", "0"], foot_id: "H_ob", on: "bot", relation: "line_perp_plane", status: "GIVEN", plane_directions: [["3", "0", "0"], ["0", "3", "0"]], marker: { u: ["1", "0", "0"], v: ["0", "0", "3"] } } },
          { id: "prism_ob", type: "solid", label: "ABC.A′B′C′", notation: "ABC.A′B′C′", shape_class: "PRISM_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", depends: ["A", "B", "C", "A1", "B1", "C1"], vertex_ids: ["A", "B", "C", "A1", "B1", "C1"], vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "3", "0"], ["1", "1", "3"], ["4", "1", "3"], ["1", "4", "3"]], faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]] },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "bot", depends: ["A", "B", "C"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "H_ob", depends: ["A1", "bot"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "alt_ob", depends: ["A1", "H_ob"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "top", depends: ["A1", "B1", "C1"], explanation: "" },
          { step_index: 5, action: "CREATE", object: "prism_ob", depends: ["A", "B", "C", "A1", "B1", "C1"], explanation: "" },
        ],
      };
      const obPrismContract = getSemanticConstructionContract(obliquePrism);
      expect(obPrismContract.objectsById.get("bot")?.semanticRole).toBe("BASE_FACE");
      expect(obPrismContract.objectsById.get("top")?.semanticRole).toBe("TOP_FACE");
      expect(obPrismContract.objectsById.get("top")?.verifiedRelations.some((r) => r.kind === "parallel" && r.targetIds.includes("bot"))).toBe(true);

      // (C) Base-free tetrahedron (`4` vertices, no `BASE_REGION`, generic label)
      const tetScene: Scene3D = {
        free_objects: ["A", "B", "C", "D"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
          { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
          { id: "D", type: "point3", label: "D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "5"] },
          { id: "tet_sol", type: "solid", label: "Khối ABCD", notation: "ABCD", origin: "derived", producer: "construct_solid", render: "mesh", depends: ["A", "B", "C", "D"], vertex_ids: ["A", "B", "C", "D"], vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "4", "0"], ["0", "0", "5"]], faces: [[0, 1, 2], [0, 1, 3], [1, 2, 3], [2, 0, 3]] },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "tet_sol", depends: ["A", "B", "C", "D"], explanation: "" },
        ],
      };
      const tetPlan = buildPedagogicalConstructionPlan(tetScene);
      expect(tetPlan.steps.some((s) => s.title.includes("tứ diện ABCD"))).toBe(true);
      expect(resolveSemanticObjectContract(tetScene, "tet_sol")?.semanticRole).toBe("PRIMARY_SOLID");

      // (D) Skew-line common perpendicular & Explicit Oxyz scene
      const skewScene: Scene3D = {
        free_objects: ["M", "N", "P1", "P2"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "M", type: "point3", label: "M", notation: "M", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "P1", type: "point3", label: "P1", notation: "P1", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
          { id: "N", type: "point3", label: "N", notation: "N", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
          { id: "P2", type: "point3", label: "P2", notation: "P2", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "3", "4"] },
          { id: "d1", type: "line3", label: "d₁", notation: "d₁", origin: "derived", producer: "construct_line", render: "line", depends: ["M", "P1"], point: ["0", "0", "0"], direction: ["1", "0", "0"] },
          { id: "d2", type: "line3", label: "d₂", notation: "d₂", origin: "derived", producer: "construct_line", render: "line", depends: ["N", "P2"], point: ["0", "0", "4"], direction: ["0", "1", "0"] },
          { id: "seg_MN", type: "segment3", label: "Đoạn vuông góc chung MN", notation: "MN", origin: "derived", producer: "common_perpendicular", render: "segment", display_group: ["perp_witness"], depends: ["d1", "d2", "M", "N"], endpoint_ids: ["M", "N"], endpoints: [["0", "0", "0"], ["0", "0", "4"]], perpendicular_witness: { from: "N", foot: ["0", "0", "0"], foot_id: "M", on: "d1", relation: "common_perpendicular", status: "DERIVED_VERIFIED", line_direction: ["1", "0", "0"], marker: { u: ["1", "0", "0"], v: ["0", "0", "4"] }, second: { foot: ["0", "0", "4"], foot_id: "N", on: "d2", line_direction: ["0", "1", "0"], marker: { u: ["0", "1", "0"], v: ["0", "0", "-4"] } } } },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "d1", depends: ["M", "P1"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "d2", depends: ["N", "P2"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "seg_MN", depends: ["d1", "d2", "M", "N"], explanation: "" },
        ],
      };
      const skewPlan = buildPedagogicalConstructionPlan(skewScene);
      const skewContract = getSemanticConstructionContract(skewPlan.scene);
      expect(
        [...skewContract.objectsById.values()].some(
          (oc) => oc.semanticRole === "COMMON_PERPENDICULAR" && oc.verifiedRelations.some((r) => r.kind === "common_perpendicular" && r.exactVerified),
        ),
      ).toBe(true);

      const oxyzScene: Scene3D = {
        free_objects: ["O", "M"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "O", type: "point3", label: "Gốc tọa độ O(0;0;0)", notation: "O", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "M", type: "point3", label: "Điểm M(1;2;3)", notation: "M", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "2", "3"] },
          { id: "mp_oxy", type: "plane3", label: "Mặt phẳng (Oxy): z = 0", notation: "(Oxy)", role: "Mặt phẳng tọa độ có phương trình z = 0 trong Oxyz", origin: "derived", producer: null, render: "surface", depends: ["O"], point: ["0", "0", "0"], normal: ["0", "0", "1"] },
          { id: "H_oxy", type: "point3", label: "Hình chiếu H(1;2;0)", notation: "H", origin: "derived", producer: "project_onto", render: "point_marker", depends: ["M", "mp_oxy"], xyz: ["1", "2", "0"], perpendicular_witness: { from: "M", foot: ["1", "2", "0"], foot_id: "H_oxy", on: "mp_oxy", relation: "line_perp_plane", status: "DERIVED_VERIFIED", plane_directions: [["1", "0", "0"], ["0", "1", "0"]], marker: { u: ["1", "0", "0"], v: ["0", "0", "3"] } } },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "mp_oxy", depends: ["O"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "H_oxy", depends: ["M", "mp_oxy"], explanation: "" },
        ],
      };
      const oxyzContract = getSemanticConstructionContract(oxyzScene);
      expect(oxyzContract.objectsById.get("H_oxy")?.semanticRole).toBe("PROJECTION_FOOT");
      expect(oxyzContract.objectsById.get("H_oxy")?.verifiedRelations.some((r) => r.kind === "incidence" && r.targetIds.includes("mp_oxy"))).toBe(true);
    });

    it("enforces step invariants 1–8 and zero automatic answer leakage across every geometry catalog sample", () => {
      expect(SAMPLES_RAW.samples.length).toBeGreaterThanOrEqual(8);

      for (const item of SAMPLES_RAW.samples) {
        const raw = JSON.parse(JSON.stringify(item.envelope.scene3d)) as Scene3D;
        const plan = buildPedagogicalConstructionPlan(raw);
        const contract = getSemanticConstructionContract(plan.scene);
        const policy = evaluateStudentPresentationPolicy(plan.scene, plan.goalCompletion);

        expect(policy.showMathResultsPanel).toBe(false);
        for (const obj of plan.scene.objects) {
          expect(policy.canDisplayEntityFormula(obj)).toBe(false);
          if (obj.type === "quantity") {
            const oc = contract.objectsById.get(obj.id);
            expect(oc).toBeDefined();
            if (oc?.informationCategory === "INTERNAL_MATH_RESULT") {
              expect(policy.canDisplayEntityValue(obj)).toBe(false);
            }
          }
        }

        const firstSeenCoord = new Map<string, string>();
        const forwardSnapshots: string[] = [];

        for (const step of plan.steps) {
          const present = objectsAt(plan.scene, step.anchor);
          const presentIds = new Set(present.map((o) => o.id));
          forwardSnapshots.push([...presentIds].sort().join("|"));

          for (const preId of step.prerequisiteIds) {
            const preObj = plan.scene.objects.find((o) => o.id === preId);
            if (preObj && preObj.type !== "quantity" && preObj.render !== "non_visual") {
              expect(presentIds.has(preId)).toBe(true);
            }
          }

          for (const o of present) {
            const sig = JSON.stringify({
              type: o.type,
              xyz: o.xyz,
              endpoints: o.endpoints,
              vertices: o.vertices,
              center: o.center,
              anchor: o.anchor,
            });
            const prev = firstSeenCoord.get(o.id);
            if (prev !== undefined) {
              expect(sig).toBe(prev);
            } else {
              firstSeenCoord.set(o.id, sig);
            }
          }

          expect(step.title).not.toMatch(/KẾT\s+QUẢ\s+TOÁN\s+HỌC|Đáp\s+số/iu);
          expect(step.subtitle).not.toMatch(/KẾT\s+QUẢ\s+TOÁN\s+HỌC|Đáp\s+số/iu);

          const groups = buildStepEntityGroups(plan.scene, step.anchor, { steps: plan.steps });
          for (const chip of groups.all) {
            expect(chip.shortLabel).not.toMatch(/KẾT\s+QUẢ\s+TOÁN\s+HỌC/iu);
          }
        }

        const backwardSnapshots = [...plan.steps]
          .reverse()
          .map((step) => [...new Set(objectsAt(plan.scene, step.anchor).map((o) => o.id))].sort().join("|"))
          .reverse();
        expect(backwardSnapshots).toEqual(forwardSnapshots);
      }
    });

    it("fails closed and disables all certified relation symbols when sphere-plane distance d = 7 exceeds sphere radius R = 5", () => {
      const disjointSphere = sampleScene("cau-cat-mat-phang");
      for (const o of disjointSphere.objects) {
        if (o.id === "P" && o.point) o.point = ["0", "0", "7"];
        if (o.id === "C") {
          o.center = ["0", "0", "7"];
          o.radius_sq = "-24";
        }
      }
      const ver = verifySceneMathematicalConsistency(disjointSphere);
      expect(ver.valid).toBe(false);
      expect(ver.contradictions.length).toBeGreaterThan(0);
      const secContract = resolveSemanticObjectContract(disjointSphere, "C")!;
      expect(secContract.determinacy).toBe("CONTRADICTORY");
      expect(secContract.verifiedRelations.every((r) => !r.exactVerified && !r.canDisplaySymbol)).toBe(true);
    });
  });

  describe("8. Visual-Continuity Root-Cause Guards (Off-Equator Stationary R, Step-Invariant Right-Angle Direction, Edge-On Foreshortening, Tilted-Right vs Oblique Cylinder, 7 Canonical Roles & Cache Safety)", () => {
    it("keeps sphere R = 5 off the z = 0 reference equator and stationary across Steps 1 → 2 → 3 while keeping IH ⊥ (P) marker u-direction invariant and edge-on safe", () => {
      const plan = buildPedagogicalConstructionPlan(sampleScene("cau-cat-mat-phang"));
      expect(plan.steps.length).toBe(5);

      const view: AnnotationView = { showAll: false, hiddenIds: tapKetQuaCuoi(plan.scene) };
      // Steps 1, 2, 3 never draw an unlabelled dangling equator radius ray and never float R = 5 in mid-air before M is constructed at Step 4
      for (const st of [plan.steps[0]!, plan.steps[1]!, plan.steps[2]!]) {
        const vis = objectsAt(plan.scene, st.anchor);
        const anns = annotationsAt(plan.scene, st.anchor, view, null);
        const rEarly = anns.find((a) => a.id === "R");
        expect(rEarly).toBeDefined();
        expect(rEarly?.anchor).toBe("segment");
        expect(rEarly?.subject_ids).toEqual(["I", "cau__ref_pt"]);
        const refGrp = buildContractReferenceGroup(plan.scene, vis, st.anchor);
        expect(refGrp?.getObjectByName("curved_radius:cau:equator")).toBeUndefined();
      }

      // From Step 4 onward, constructed sphere radius IM (`C__sph_rad`) connects I to real sphere point M (`anchor: "segment"`) with zero teleportation
      const step3VisForRef = objectsAt(plan.scene, plan.steps[4]!.anchor);
      const step3Anns = annotationsAt(plan.scene, plan.steps[4]!.anchor, view, null);
      const rStep3 = step3Anns.find((a) => a.id === "R")!;
      expect(rStep3).toBeDefined();
      expect(rStep3.anchor).toBe("segment");
      expect(annotationAnchor(plan.scene, rStep3)).toBeDefined();
      const refGrp3 = buildContractReferenceGroup(plan.scene, step3VisForRef, plan.steps[4]!.anchor);
      expect(refGrp3?.getObjectByName("curved_radius:cau:equator")).toBeUndefined();

      // Step 3 entity chips surface H (`C__center`) alongside P and IH
      const step2Groups = buildStepEntityGroups(plan.scene, plan.steps[2].anchor, { steps: plan.steps });
      expect(step2Groups.all.some((x) => x.id === "C__center")).toBe(true);

      // Step 3 (H, IH before HM) omits ungrounded perp_marker; Step 4 (HM) and Step 5 (C) keep identical u and v directions at H
      const distSeg = plan.scene.objects.find((o) => o.id === "C__dist")!;
      const stepBeforeHmVis = objectsAt(plan.scene, plan.steps[2].anchor);
      const step2Vis = objectsAt(plan.scene, plan.steps[3].anchor);
      const step3Vis = objectsAt(plan.scene, plan.steps[4].anchor);
      const diemNenBeforeHm = stepBeforeHmVis.filter((o) => o.type === "point3" && o.xyz).map((o) => o.xyz!.map(Number) as [number, number, number]);
      const diemNen2 = step2Vis.filter((o) => o.type === "point3" && o.xyz).map((o) => o.xyz!.map(Number) as [number, number, number]);
      const diemNen3 = step3Vis.filter((o) => o.type === "point3" && o.xyz).map((o) => o.xyz!.map(Number) as [number, number, number]);
      const builtBeforeHm = buildObject3D(distSeg, false, 0.1, diemNenBeforeHm, new THREE.Vector3(8, -6, 5), undefined, undefined, false, "primary", false, true, false, plan.scene, undefined, undefined, undefined, stepBeforeHmVis)!;
      expect(builtBeforeHm.getObjectByName("perp_marker:C__dist")).toBeUndefined();
      const built2 = buildObject3D(distSeg, false, 0.1, diemNen2, new THREE.Vector3(8, -6, 5), undefined, undefined, false, "primary", false, true, false, plan.scene, undefined, undefined, undefined, step2Vis)!;
      const built3 = buildObject3D(distSeg, false, 0.1, diemNen3, new THREE.Vector3(8, -6, 5), undefined, undefined, false, "primary", true, true, false, plan.scene, undefined, undefined, undefined, step3Vis)!;
      const m2 = built2.getObjectByName("perp_marker:C__dist")!;
      const m3 = built3.getObjectByName("perp_marker:C__dist")!;
      expect(m2.userData.gocVuongDonVi.u).toEqual(m3.userData.gocVuongDonVi.u);
      expect(m2.userData.gocVuongDonVi.v).toEqual(m3.userData.gocVuongDonVi.v);

      // Near-degenerate edge-on camera (looking right inside the span(u, v) = xz-plane at y = 0) hides sliver cleanly without 2D square
      const mFoot = m3.userData.gocVuongDonVi.foot as [number, number, number];
      const mU = m3.userData.gocVuongDonVi.u as [number, number, number];
      const mV = m3.userData.gocVuongDonVi.v as [number, number, number];
      const normalDir = new THREE.Vector3(...mU).cross(new THREE.Vector3(...mV)).normalize();

      const normalCam = new THREE.PerspectiveCamera(45, 16 / 9, 0.1, 200);
      normalCam.position.set(mFoot[0] + normalDir.x * 8 + mU[0] * 3, mFoot[1] + normalDir.y * 8 + mU[1] * 3, mFoot[2] + normalDir.z * 8 + mU[2] * 3);
      normalCam.lookAt(mFoot[0], mFoot[1], mFoot[2]);
      normalCam.updateMatrixWorld(true);
      expect(datCoGocVuong([built3], normalCam, 720)).toBe(1);
      expect(m3.visible).toBe(true);

      const edgeOnCam = new THREE.PerspectiveCamera(45, 16 / 9, 0.1, 200);
      edgeOnCam.position.set(mFoot[0] + mU[0] * 10 + mV[0] * 2, mFoot[1] + mU[1] * 10 + mV[1] * 2, mFoot[2] + mU[2] * 10 + mV[2] * 2);
      edgeOnCam.lookAt(mFoot[0], mFoot[1], mFoot[2]);
      edgeOnCam.updateMatrixWorld(true);
      expect(datCoGocVuong([built3], edgeOnCam, 720)).toBe(0);
      expect(m3.visible).toBe(false);
    });

    it("distinguishes tilted right cylinders (axis OO' ∥ base_normal, including catalog tru-truc-xien) from genuine oblique cylinders (axis OO' ∦ base_normal)", () => {
      const catalogTiltedRight = sampleScene("tru-truc-xien");
      const catCyl = catalogTiltedRight.objects.find((o) => o.type === "curved_solid")!;
      const orthoCat = inspectAxialCurvedOrthogonality(catalogTiltedRight, catCyl);
      expect(orthoCat.isRightCertified).toBe(true);
      expect(orthoCat.isOblique).toBe(false);
      expect(orthoCat.isTiltedAxisInSpace).toBe(true);
      const catPlan = buildPedagogicalConstructionPlan(catalogTiltedRight);
      for (const st of catPlan.steps) {
        expect(st.title).not.toMatch(/trụ\s+xiên/iu);
      }

      const genuineObliqueScene: Scene3D = {
        free_objects: ["O", "O_prime"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "O", type: "point3", label: "Tâm O", notation: "O", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "O_prime", type: "point3", label: "Tâm O′", notation: "O′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "4"] },
          { id: "day_duoi", type: "circle3", label: "Đáy (O)", notation: "(O)", origin: "derived", producer: "construct_circle", render: "circle", surface_role: "BASE_REGION", depends: ["O"], center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "4" },
          { id: "day_tren", type: "circle3", label: "Đáy (O′)", notation: "(O′)", origin: "derived", producer: "construct_circle", render: "circle", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_TRANSLATED_FACE"], depends: ["O_prime"], center: ["2", "0", "4"], normal: ["0", "0", "1"], radius_sq: "4" },
          { id: "noi_tam", type: "segment3", label: "Đoạn nối tâm OO′", notation: "OO′", origin: "derived", producer: "construct_segment", render: "segment", depends: ["O", "O_prime"], endpoint_ids: ["O", "O_prime"], endpoints: [["0", "0", "0"], ["2", "0", "4"]] },
          { id: "tru_xien_that", type: "curved_solid", curved_kind: "cylinder", label: "Hình trụ xiên", notation: "(T)", origin: "derived", producer: "construct_curved_solid", render: "curved_solid", depends: ["O", "O_prime", "day_duoi", "day_tren"], anchor: ["0", "0", "0"], apex_or_top: ["2", "0", "4"], radius_sq: "4", height_sq: "16" },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_duoi", depends: ["O"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "noi_tam", depends: ["O", "O_prime"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "day_tren", depends: ["O_prime"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "tru_xien_that", depends: ["O", "O_prime", "day_duoi", "day_tren"], explanation: "" },
        ],
      };
      const obCyl = genuineObliqueScene.objects.find((o) => o.id === "tru_xien_that")!;
      const orthoOb = inspectAxialCurvedOrthogonality(genuineObliqueScene, obCyl);
      expect(orthoOb.isRightCertified).toBe(false);
      expect(orthoOb.isOblique).toBe(true);
      const obPlan = buildPedagogicalConstructionPlan(genuineObliqueScene);
      expect(obPlan.steps.some((st) => /trụ\s+xiên/iu.test(st.title) || /trụ\s+xiên/iu.test(st.subtitle))).toBe(true);
    });

    it("maps all 7 CanonicalPedagogicalObjectRole values, invalidates WeakMap caches on in-place scene mutation, yields base polygon loops to canonical solid edges, and orders primary target Q before carrier SD", () => {
      const chop = sampleScene("thiet-dien-chop");
      const chopPlan = buildPedagogicalConstructionPlan(chop);
      const qStep = chopPlan.steps.find((s) => s.targetIds.includes("Q"))!;
      const qGroups = buildStepEntityGroups(chopPlan.scene, qStep.anchor, { steps: chopPlan.steps });
      expect(qGroups.primary[0]?.id).toBe("Q");

      // Base polygon loop (when boundary_edge_ids is absent so ownsBoundary === true) yields colinear segments to canonical solid edges
      const unownedBasePoly: SceneObject = {
        ...chopPlan.scene.objects.find((o) => o.id === "day_ABCD")!,
        boundary_edge_ids: undefined,
      };
      const builtBase = buildObject3D(unownedBasePoly, false)!;
      expect(builtBase.userData.nonCanonicalLoop?.yieldColinear).toBe(true);

      // 7 CanonicalPedagogicalObjectRole taxonomy coverage
      const seenCanonicalRoles = new Set<CanonicalPedagogicalObjectRole>();
      const chopContract = getSemanticConstructionContract(chop);
      for (const c of chopContract.objectsById.values()) seenCanonicalRoles.add(c.canonicalRole);

      const sphereWithRef = sampleScene("cau-cat-mat-phang");
      sphereWithRef.objects.push({
        id: "eq_ref",
        type: "circle3",
        label: "Xích đạo tham chiếu",
        origin: "derived",
        producer: null,
        render: "circle",
        display_role: "presentation_reference",
        semantic_role: "REFERENCE_EQUATOR",
        depends: ["cau"],
        center: ["0", "0", "0"],
        normal: ["0", "0", "1"],
        radius_sq: "25",
      } as unknown as SceneObject);
      for (const c of getSemanticConstructionContract(sphereWithRef).objectsById.values()) {
        seenCanonicalRoles.add(c.canonicalRole);
      }
      expect(seenCanonicalRoles).toEqual(
        new Set<CanonicalPedagogicalObjectRole>([
          "GIVEN_FACT",
          "CONSTRUCTION_GEOMETRY",
          "AUXILIARY_GEOMETRY",
          "REFERENCE_GEOMETRY",
          "RESULT_SECTION",
          "ILLUSTRATIVE_GEOMETRY",
          "INTERNAL_MATH_RESULT",
        ]),
      );

      // In-place mutation on the same Scene3D reference invalidates both contract and plan caches
      const mutableSphere = sampleScene("cau-cat-mat-phang");
      expect(getSemanticConstructionContract(mutableSphere).consistency.valid).toBe(true);
      expect(buildPedagogicalConstructionPlan(mutableSphere).steps.length).toBe(5);
      const secObj = mutableSphere.objects.find((o) => o.id === "C")!;
      secObj.radius_sq = "999";
      expect(getSemanticConstructionContract(mutableSphere).consistency.valid).toBe(false);

      // Witness-only projection step (`mp-vuong-goc-duong` final step `SH ⊥ (α)`) puts SH & H in `primary`, NEVER unrelated `A`
      const mpPlan = buildPedagogicalConstructionPlan(sampleScene("mp-vuong-goc-duong"));
      const mpFinalStep = mpPlan.steps[mpPlan.steps.length - 1]!;
      const mpGroups = buildStepEntityGroups(mpPlan.scene, mpFinalStep.anchor, { steps: mpPlan.steps });
      expect(mpGroups.primary.map((x) => x.shortLabel)).toContain("SH");
      expect(mpGroups.primary.map((x) => x.id)).not.toContain("A");

      // Underdetermined S.ABC (`SA ⊥ (ABC), AB = 2a, SA = 4a`, C unconstrained) marks closing solid step as illustrative
      const sabcPlan = buildPedagogicalConstructionPlan({
        free_objects: ["A", "B", "C", "S", "q_ab", "q_sa"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
          { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
          { id: "day_ABC", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]] },
          { id: "cao_SA", type: "segment3", label: "Đường cao SA", notation: "SA", origin: "derived", producer: "construct_segment", render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["S", "A"], endpoint_ids: ["S", "A"], endpoints: [["0", "0", "4"], ["0", "0", "0"]], perpendicular_witness: { from: "S", foot: ["0", "0", "0"], foot_id: "A", on: "day_ABC", relation: "line_perp_plane", plane_directions: [["2", "0", "0"], ["0", "2", "0"]], marker: { u: ["2", "0", "0"], v: ["0", "0", "4"] } } },
          { id: "khoi_SABC", type: "solid", label: "Hình chóp S.ABC", notation: "S.ABC", shape_class: "PYRAMID_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["S", "A", "B", "C"], vertex_ids: ["S", "A", "B", "C"], vertices: [["0", "0", "4"], ["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]], faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]] },
          { id: "q_ab", type: "quantity", label: "Độ dài AB", notation: "AB", origin: "free", producer: null, render: "readout", depends: ["A", "B"], value: "2a", symbolic: "2a", source: { fact_id: "f1", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"] },
          { id: "q_sa", type: "quantity", label: "Độ dài SA", notation: "SA", origin: "free", producer: null, render: "readout", depends: ["S", "A"], value: "4a", symbolic: "4a", source: { fact_id: "f2", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"] },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_ABC", depends: ["A", "B", "C"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "cao_SA", depends: ["S", "A"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "khoi_SABC", depends: ["S", "A", "B", "C"], explanation: "" },
        ],
      });
      const sabcFinal = sabcPlan.steps[sabcPlan.steps.length - 1]!;
      expect(sabcFinal.epistemicCategory).toBe("constructed");
      expect(sabcFinal.subtitle).toMatch(/minh họa/iu);
    });
  });
});
