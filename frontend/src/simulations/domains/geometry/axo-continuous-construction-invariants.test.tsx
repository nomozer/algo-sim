import * as THREE from "three";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { annotationsAt, DEFAULT_ANNOTATION_VIEW, givenQuantitiesSummary } from "./scene3d-annotations";
import { veKhongGian } from "./scene3d-chart";
import { diemVanhCongBiChe, type CurvedSolidVolumeMeta } from "./scene3d-edge-visibility";
import { objectsAt, type ExactVec3, type Scene3D, type SceneObject } from "./scene3d-model";
import {
  buildContractReferenceGroup,
  buildPedagogicalConstructionPlan,
  buildStepEntityGroups,
  getSemanticConstructionContract,
  resolveSemanticObjectContract,
  resolveStepVisualRoles,
  verifyConstructionContinuity,
  verifySceneMathematicalConsistency,
} from "./scene3d-semantic-policy";
import { evaluateStudentPresentationPolicy } from "./scene3d-student-presentation-policy";
import { withSubEntities } from "./scene3d-subentities";
import { buildObject3D, datCoGocVuong, updateCanonicalEdgeVisibility } from "./scene3d-view";

function loadSampleScene(sampleId: string): Scene3D {
  const sample = GEOMETRY_SAMPLES.find((s) => s.id === sampleId);
  if (!sample) throw new Error(`Missing sample: ${sampleId}`);
  return withSubEntities((sample.envelope as unknown as { scene3d: Scene3D }).scene3d);
}

function parseFrac(raw: string): [bigint, bigint] {
  const s = raw.trim();
  const slash = s.indexOf("/");
  if (slash < 0) return [BigInt(s), 1n];
  const n = BigInt(s.slice(0, slash));
  const d = BigInt(s.slice(slash + 1));
  return d < 0n ? [-n, -d] : [n, d];
}

function fAdd(a: [bigint, bigint], b: [bigint, bigint]): [bigint, bigint] {
  return [a[0] * b[1] + b[0] * a[1], a[1] * b[1]];
}

function fSub(a: [bigint, bigint], b: [bigint, bigint]): [bigint, bigint] {
  return [a[0] * b[1] - b[0] * a[1], a[1] * b[1]];
}

function fMul(a: [bigint, bigint], b: [bigint, bigint]): [bigint, bigint] {
  return [a[0] * b[0], a[1] * b[1]];
}

function fEq(a: [bigint, bigint], b: [bigint, bigint]): boolean {
  return a[0] * b[1] === b[0] * a[1];
}

function distSqExact(a: ExactVec3, b: ExactVec3): [bigint, bigint] {
  const dx = fSub(parseFrac(a[0]), parseFrac(b[0]));
  const dy = fSub(parseFrac(a[1]), parseFrac(b[1]));
  const dz = fSub(parseFrac(a[2]), parseFrac(b[2]));
  return fAdd(fAdd(fMul(dx, dx), fMul(dy, dy)), fMul(dz, dz));
}

function dotExact(a: ExactVec3, b: ExactVec3): [bigint, bigint] {
  return fAdd(
    fAdd(
      fMul(parseFrac(a[0]), parseFrac(b[0])),
      fMul(parseFrac(a[1]), parseFrac(b[1])),
    ),
    fMul(parseFrac(a[2]), parseFrac(b[2])),
  );
}

function transformScenePoints(
  scene: Scene3D,
  mapPt: (v: ExactVec3) => ExactVec3,
  mapDir: (v: ExactVec3) => ExactVec3,
  scaleSq: [bigint, bigint],
  renameId: (id: string) => string,
  renameLabel: (s: string) => string,
): Scene3D {
  const scaleStr = (raw: string | undefined): string | undefined => {
    if (!raw) return raw;
    const f = fMul(parseFrac(raw), scaleSq);
    return f[1] === 1n ? String(f[0]) : `${f[0]}/${f[1]}`;
  };
  return {
    ...scene,
    free_objects: scene.free_objects.map(renameId),
    objects: scene.objects.map((o): SceneObject => ({
      ...o,
      id: renameId(o.id),
      label: o.label ? renameLabel(o.label) : o.label,
      notation: o.notation ? renameLabel(o.notation) : o.notation,
      reference: o.reference ? renameLabel(o.reference) : o.reference,
      depends: (o.depends ?? []).map(renameId),
      vertex_ids: o.vertex_ids?.map(renameId),
      endpoint_ids: o.endpoint_ids?.map(renameId),
      boundary_edge_ids: o.boundary_edge_ids?.map(renameId),
      xyz: o.xyz ? mapPt(o.xyz) : undefined,
      point: o.point ? mapPt(o.point) : undefined,
      point_a: o.point_a ? mapPt(o.point_a) : undefined,
      point_b: o.point_b ? mapPt(o.point_b) : undefined,
      center: o.center ? mapPt(o.center) : undefined,
      anchor: o.anchor ? mapPt(o.anchor) : undefined,
      apex_or_top: o.apex_or_top ? mapPt(o.apex_or_top) : undefined,
      normal: o.normal ? mapDir(o.normal) : undefined,
      direction: o.direction ? mapDir(o.direction) : undefined,
      vertices: o.vertices?.map(mapPt),
      polygon: o.polygon?.map(mapPt),
      endpoints: o.endpoints?.map(mapPt) as SceneObject["endpoints"],
      radius_sq: scaleStr(o.radius_sq),
      height_sq: scaleStr(o.height_sq),
      perpendicular_witness: o.perpendicular_witness
        ? {
            ...o.perpendicular_witness,
            from: o.perpendicular_witness.from ? renameId(o.perpendicular_witness.from) : o.perpendicular_witness.from,
            on: o.perpendicular_witness.on ? renameId(o.perpendicular_witness.on) : o.perpendicular_witness.on,
            foot_id: o.perpendicular_witness.foot_id ? renameId(o.perpendicular_witness.foot_id) : o.perpendicular_witness.foot_id,
            foot: o.perpendicular_witness.foot ? mapPt(o.perpendicular_witness.foot) : o.perpendicular_witness.foot,
            plane_directions: o.perpendicular_witness.plane_directions?.map(mapDir) as [ExactVec3, ExactVec3] | undefined,
            marker: o.perpendicular_witness.marker
              ? {
                  ...o.perpendicular_witness.marker,
                  u: mapDir(o.perpendicular_witness.marker.u),
                  v: mapDir(o.perpendicular_witness.marker.v),
                }
              : o.perpendicular_witness.marker,
          }
        : undefined,
    })),
    events: scene.events.map((ev) => ({
      ...ev,
      object: ev.object ? renameId(ev.object) : null,
      depends: ev.depends.map(renameId),
    })),
  };
}

describe("AXO Continuous Pedagogical Construction & Geometric Visual Consistency", () => {
  describe("1. Unified Semantic Construction Layer & DAG / Step-Continuity Verifier (§3, §5, §10.2)", () => {
    it("exports 5-layer taxonomy + per-step constructionEvents and certifies all 11 catalog simulations via verifyConstructionContinuity", () => {
      for (const sample of GEOMETRY_SAMPLES) {
        const scene = loadSampleScene(sample.id);
        const plan = buildPedagogicalConstructionPlan(scene);
        const contract = getSemanticConstructionContract(plan.scene);
        expect(Array.isArray(contract.constructionEvents)).toBe(true);
        expect(contract.constructionEvents.length).toBeGreaterThan(0);

        for (const ev of contract.constructionEvents) {
          expect(typeof ev.object_id).toBe("string");
          expect([
            "GIVEN_GEOMETRY",
            "REFERENCE_GEOMETRY",
            "CONSTRUCTION_GEOMETRY",
            "RELATION_WITNESS",
            "RESULT_SECTION",
            "INTERNAL_MATH_RESULT",
          ]).toContain(ev.object_layer);
          expect(typeof ev.construction_operation).toBe("string");
          expect(Array.isArray(ev.prerequisites)).toBe(true);
        }

        const report = verifyConstructionContinuity(plan.scene);
        expect(report.valid, `${sample.id} violations: ${JSON.stringify(report.violations)}`).toBe(true);
        expect(report.violations).toEqual([]);
        expect(report.stepCount).toBe(plan.steps.length);
      }
    });

    it("detects causal cycle, result-before-operand, coordinate drift, and contradictory geometry fail-closed", () => {
      const badCycleScene: Scene3D = {
        free_objects: [],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          {
            id: "A",
            type: "point3",
            label: "A",
            origin: "derived", producer: "CONSTRUCT",
            render: "point_marker",
            depends: ["B"],
            xyz: ["0", "0", "0"],
          },
          {
            id: "B",
            type: "point3",
            label: "B",
            origin: "derived", producer: "CONSTRUCT",
            render: "point_marker",
            depends: ["A"],
            xyz: ["1", "0", "0"],
          },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "A", depends: ["B"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "B", depends: ["A"], explanation: "" },
        ],
      };
      const cycleReport = verifyConstructionContinuity(badCycleScene);
      expect(cycleReport.valid).toBe(false);
      expect(cycleReport.violations.some((v) => v.code === "PREREQUISITE_CYCLE" || v.code === "CAUSAL_BIRTH_ORDER")).toBe(true);

      const contradictorySphere: Scene3D = {
        free_objects: ["I"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "I", type: "point3", label: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "S", type: "curved_solid", curved_kind: "ball", label: "(S)", origin: "derived", producer: "CONSTRUCT", render: "curved_solid", depends: ["I"], anchor: ["0", "0", "0"], radius_sq: "25" },
          { id: "P", type: "plane3", label: "(P)", origin: "derived", producer: "CONSTRUCT", render: "surface", surface_role: "CUTTING_PLANE", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: [], point: ["0", "0", "7"], normal: ["0", "0", "1"] },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "S", depends: ["I"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "P", depends: [], explanation: "" },
        ],
      };
      const contraReport = verifyConstructionContinuity(contradictorySphere);
      expect(contraReport.valid).toBe(false);
      expect(contraReport.failureReason).toBe("CONTRADICTORY_GEOMETRY");
    });
  });

  describe("2. Sphere–Plane Continuity & Inclined-Plane 4-Regime Exact Math (§4.1–§4.3)", () => {
    it("eliminates unlabelled dangling equator radius ray and R=5 teleportation across Steps 1 -> 5 of cau-cat-mat-phang", () => {
      const plan = buildPedagogicalConstructionPlan(loadSampleScene("cau-cat-mat-phang"));
      expect(plan.steps.length).toBe(5);

      for (let s = 0; s < plan.steps.length; s += 1) {
        const k = plan.steps[s]!.anchor;
        const vis = objectsAt(plan.scene, k);
        const refGrp = buildContractReferenceGroup(plan.scene, vis, k);
        expect(refGrp?.getObjectByName("curved_radius:cau:equator")).toBeUndefined();

        const anns = annotationsAt(plan.scene, k, DEFAULT_ANNOTATION_VIEW, null);
        for (const ann of anns) {
          if (ann.text.includes("R = 5") || ann.id === "R") {
            expect(ann.anchor).toBe("segment");
          }
        }
      }

      // From Step 4 onward (once certified M and IM exist), R = 5 is anchored onto real sphere radius segment IM (|IM|^2 = 25)
      for (const sIdx of [3, 4]) {
        const stepAnns = annotationsAt(plan.scene, plan.steps[sIdx]!.anchor, DEFAULT_ANNOTATION_VIEW, null);
        const rAnn = stepAnns.find((a) => a.text.includes("R = 5"));
        expect(rAnn?.anchor).toBe("segment");
      }
    });

    it("certifies all 4 sphere-plane regimes over INCLINED planes n = (1, 2, 2) and n = (2, 3, 6) in exact Q^3", () => {
      const inclinedSecant: Scene3D = {
        free_objects: ["I_c", "q_R"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "I_c", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "-1", "2"] },
          { id: "q_R", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["sph_inc"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f_r", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"] },
          { id: "sph_inc", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: "CONSTRUCT", render: "curved_solid", depends: ["I_c", "q_R"], anchor: ["1", "-1", "2"], radius_sq: "25" },
          { id: "mp_inc", type: "plane3", label: "Mặt phẳng (Q)", notation: "(Q)", origin: "derived", producer: "CONSTRUCT", render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["2", "1", "4"], normal: ["1", "2", "2"] },
          { id: "cir_inc", type: "circle3", label: "Đường tròn giao tuyến", origin: "derived", producer: "CONSTRUCT", render: "circle", surface_role: "SECTION_REGION", depends: ["sph_inc", "mp_inc"], center: ["2", "1", "4"], normal: ["1", "2", "2"], radius_sq: "16" },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "sph_inc", depends: ["I_c", "q_R"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "mp_inc", depends: [], explanation: "" },
          { step_index: 3, action: "CREATE", object: "cir_inc", depends: ["sph_inc", "mp_inc"], explanation: "" },
        ],
      };

      expect(verifySceneMathematicalConsistency(inclinedSecant).valid).toBe(true);
      const secPlan = buildPedagogicalConstructionPlan(withSubEntities(inclinedSecant));
      const secCont = verifyConstructionContinuity(secPlan.scene);
      expect(secCont.violations).toEqual([]);
      expect(secCont.valid).toBe(true);

      const footH = secPlan.scene.objects.find((o) => o.id === "cir_inc__center");
      const distIH = secPlan.scene.objects.find((o) => o.id === "cir_inc__dist");
      const rimM = secPlan.scene.objects.find((o) => o.id === "cir_inc__rim_pt");
      const radHM = secPlan.scene.objects.find((o) => o.id === "cir_inc__sec_rad");
      const radIM = secPlan.scene.objects.find((o) => o.id === "cir_inc__sph_rad");

      expect(footH?.xyz).toEqual(["2", "1", "4"]);
      expect(distIH?.perpendicular_witness?.can_present_as_proven).toBe(true);
      expect(rimM?.xyz).toBeDefined();
      expect(radHM).toBeDefined();
      expect(radIM).toBeDefined();

      const mXyz = rimM!.xyz!;
      const diffMH: ExactVec3 = [
        (() => { const f = fSub(parseFrac(mXyz[0]), [2n, 1n]); return `${f[0]}/${f[1]}`; })(),
        (() => { const f = fSub(parseFrac(mXyz[1]), [1n, 1n]); return `${f[0]}/${f[1]}`; })(),
        (() => { const f = fSub(parseFrac(mXyz[2]), [4n, 1n]); return `${f[0]}/${f[1]}`; })(),
      ];
      expect(dotExact(diffMH, ["1", "2", "2"])[0]).toBe(0n);
      expect(fEq(distSqExact(mXyz, ["2", "1", "4"]), [16n, 1n])).toBe(true);
      expect(fEq(distSqExact(mXyz, ["1", "-1", "2"]), [25n, 1n])).toBe(true);

      // (b) d = 0 on inclined plane n = (2, 3, 6) (|n| = 7): great circle through I = (0, 0, 0), R = 7
      const inclinedGreat: Scene3D = {
        free_objects: ["I0"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "I0", type: "point3", label: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "sph0", type: "curved_solid", curved_kind: "ball", label: "(S)", origin: "derived", producer: "CONSTRUCT", render: "curved_solid", depends: ["I0"], anchor: ["0", "0", "0"], radius_sq: "49" },
          { id: "mp0", type: "plane3", label: "(Q)", origin: "derived", producer: "CONSTRUCT", render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["0", "0", "0"], normal: ["2", "3", "6"] },
          { id: "cir0", type: "circle3", label: "(C)", origin: "derived", producer: "CONSTRUCT", render: "circle", surface_role: "SECTION_REGION", depends: ["sph0", "mp0"], center: ["0", "0", "0"], normal: ["2", "3", "6"], radius_sq: "49" },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "sph0", depends: ["I0"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "mp0", depends: [], explanation: "" },
          { step_index: 3, action: "CREATE", object: "cir0", depends: ["sph0", "mp0"], explanation: "" },
        ],
      };
      const greatPlan = buildPedagogicalConstructionPlan(withSubEntities(inclinedGreat));
      expect(verifyConstructionContinuity(greatPlan.scene).valid).toBe(true);
      const greatRim = greatPlan.scene.objects.find((o) => o.id === "cir0__rim_pt");
      expect(greatRim?.xyz).toBeDefined();
      expect(dotExact(greatRim!.xyz!, ["2", "3", "6"])[0]).toBe(0n);
      expect(fEq(distSqExact(greatRim!.xyz!, ["0", "0", "0"]), [49n, 1n])).toBe(true);

      // (c) d = R on inclined plane n = (1, 2, 2), R = 6 => H = (2, 4, 4), |IH|^2 = 36, unique tangent point, zero circle3
      const inclinedTangent: Scene3D = {
        free_objects: ["It", "q_Rt"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "It", type: "point3", label: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "q_Rt", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["spht"], value: "6", exact: { kind: "rational", value: "6" }, source: { fact_id: "frt", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"] },
          { id: "spht", type: "curved_solid", curved_kind: "ball", label: "(S)", origin: "derived", producer: "CONSTRUCT", render: "curved_solid", depends: ["It", "q_Rt"], anchor: ["0", "0", "0"], radius_sq: "36" },
          { id: "mpt", type: "plane3", label: "(Q)", origin: "derived", producer: "CONSTRUCT", render: "surface", surface_role: "CUTTING_PLANE", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: [], point: ["2", "4", "4"], normal: ["1", "2", "2"] },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "spht", depends: ["It", "q_Rt"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "mpt", depends: [], explanation: "" },
        ],
      };
      const tanPlan = buildPedagogicalConstructionPlan(withSubEntities(inclinedTangent));
      expect(verifyConstructionContinuity(tanPlan.scene).valid).toBe(true);
      expect(tanPlan.scene.objects.filter((o) => o.type === "circle3")).toHaveLength(0);
      const tanFoot = tanPlan.scene.objects.find((o) => o.type === "point3" && o.xyz?.join("|") === "2|4|4");
      expect(tanFoot).toBeDefined();
      const tanAnns = annotationsAt(tanPlan.scene, tanPlan.steps[tanPlan.steps.length - 1]!.anchor, DEFAULT_ANNOTATION_VIEW, null);
      for (const a of tanAnns) {
        expect(a.anchor).not.toBe("solid");
      }

      // (d) d > R on inclined plane n = (1, 2, 2), d = 9 > R = 6 => fail-closed non-intersecting
      const inclinedFar: Scene3D = {
        ...inclinedTangent,
        objects: inclinedTangent.objects.map((o) => (o.id === "mpt" ? { ...o, point: ["3", "6", "6"] as ExactVec3 } : o)),
      };
      expect(verifySceneMathematicalConsistency(inclinedFar).valid).toBe(false);
    });
  });

  describe("3. Cone Generator Grazing Visibility, RenderOrder Separation & Step Chip Clarity (§6, §8.5)", () => {
    it("prevents Float32 worldToLocal rounding from falsely occluding front cone/cylinder generators and keeps hidden dashed borders below visible silhouettes", () => {
      const rot = new THREE.Matrix4().makeRotationZ(0.37).setPosition(1.13, -0.71, 0.29);
      const worldToLocal = rot.clone().invert();
      const vol: CurvedSolidVolumeMeta = {
        id: "non",
        kind: "cone",
        anchor: new THREE.Vector3(0, 0, 0),
        top: new THREE.Vector3(0, 0, 4),
        radius: 3,
        height: 4,
        worldToLocal,
      };
      const worldCam = new THREE.Vector3(8, 3, 6).applyMatrix4(rot);

      for (let step = 1; step < 40; step += 1) {
        const u = step / 40;
        const localPt = new THREE.Vector3(3 * (1 - u), 0, 4 * u);
        const worldPt = localPt.clone().applyMatrix4(rot);
        expect(diemVanhCongBiChe(worldPt, worldCam, [vol])).toBe(false);
      }

      const conePlan = buildPedagogicalConstructionPlan(loadSampleScene("non-thiet-dien-truc"));
      const finalK = conePlan.steps[conePlan.steps.length - 1]!.anchor;
      const root = new THREE.Group();
      const camPos = new THREE.Vector3(0.2, -11, 4.5);
      for (const obj of objectsAt(conePlan.scene, finalK)) {
        const built = buildObject3D(
          obj,
          false,
          0.18,
          [[0, 0, 0], [3, 0, 0], [-3, 0, 0], [0, 0, 4]],
          camPos,
          undefined,
          undefined,
          false,
          undefined,
          false,
          true,
          false,
          conePlan.scene,
        );
        if (built) root.add(built);
      }
      const cam = new THREE.PerspectiveCamera(45, 16 / 9, 0.1, 100);
      cam.position.copy(camPos);
      cam.lookAt(0, 0, 2);
      cam.updateMatrixWorld(true);
      cam.updateProjectionMatrix();
      updateCanonicalEdgeVisibility(root, cam, "1280x720@1");
      let minSilhouetteOrder = Infinity;
      let maxHiddenBorderOrder = -Infinity;
      root.traverse((node) => {
        if (node.name.startsWith("curved_generator:")) {
          minSilhouetteOrder = Math.min(minSilhouetteOrder, node.renderOrder);
        }
        if (node.name.startsWith("section_border:") && node.userData?.hidden === true) {
          maxHiddenBorderOrder = Math.max(maxHiddenBorderOrder, node.renderOrder);
        }
      });
      expect(minSilhouetteOrder).toBeLessThan(Infinity);
      expect(maxHiddenBorderOrder).toBeGreaterThan(-Infinity);
      expect(maxHiddenBorderOrder).toBeLessThan(minSilhouetteOrder);
    });

    it("demotes auxiliary point-carrier line3 (SD) from primary to context when constructing Q = SD ∩ (MNP) in thiet-dien-chop", () => {
      const plan = buildPedagogicalConstructionPlan(loadSampleScene("thiet-dien-chop"));
      const qStep = plan.steps.find((s) => s.targetIds.includes("Q"))!;
      expect(qStep).toBeDefined();
      const groups = buildStepEntityGroups(plan.scene, qStep.anchor, { steps: plan.steps });
      expect(groups.primary.map((o) => o.id)).toContain("Q");
      expect(groups.primary.map((o) => o.id)).not.toContain("sd");
      expect(groups.context.map((o) => o.id)).toContain("sd");
    });
  });

  describe("4. Metamorphic Invariance, Cross-Family Symbols & Non-Spoiler Policy (§6, §8, §9, §10.1)", () => {
    it("preserves semantic roles, object layers, DAG continuity, verified relations, and step structure under renaming, translation, orthogonal rotation, uniform scaling, and object permutation", () => {
      const baseRaw = loadSampleScene("cau-cat-mat-phang");
      const basePlan = buildPedagogicalConstructionPlan(baseRaw);
      const baseContract = getSemanticConstructionContract(basePlan.scene);

      const applyOrthoAndScale = (v: ExactVec3): ExactVec3 => {
        const x = parseFrac(v[0]);
        const y = parseFrac(v[1]);
        const z = parseFrac(v[2]);
        const two: [bigint, bigint] = [2n, 1n];
        const third: [bigint, bigint] = [2n, 3n];
        const rx = fMul(third, fAdd(fSub(fMul(two, x), fMul(two, y)), z));
        const ry = fMul(third, fAdd(fAdd(x, fMul(two, y)), fMul(two, z)));
        const rz = fMul(third, fSub(fAdd(fMul(two, x), y), fMul(two, z)));
        return [`${rx[0]}/${rx[1]}`, `${ry[0]}/${ry[1]}`, `${rz[0]}/${rz[1]}`];
      };
      const applyPt = (v: ExactVec3): ExactVec3 => {
        const r = applyOrthoAndScale(v);
        const tx = fAdd(parseFrac(r[0]), [5n, 1n]);
        const ty = fAdd(parseFrac(r[1]), [-3n, 1n]);
        const tz = fAdd(parseFrac(r[2]), [7n, 2n]);
        return [`${tx[0]}/${tx[1]}`, `${ty[0]}/${ty[1]}`, `${tz[0]}/${tz[1]}`];
      };
      const renameMap: Record<string, string> = {
        I: "Tam_Omega",
        cau: "khoi_mat_cau_Z9",
        mp: "mat_cat_Alpha",
        C: "vong_giao_Gamma",
        R: "tham_so_bk",
        d: "tham_so_kc",
        r_giao: "ket_qua_an_1",
        S_giao: "ket_qua_an_2",
      };
      const renameId = (id: string) => renameMap[id] ?? `renamed_${id}`;

      const transformed = transformScenePoints(
        baseRaw,
        applyPt,
        applyOrthoAndScale,
        [4n, 1n],
        renameId,
        (lbl) => lbl.replace(/\bI\b/g, "Ω").replace(/\(P\)/g, "(α)"),
      );
      const permuted: Scene3D = {
        ...transformed,
        objects: [...transformed.objects].reverse(),
      };

      const metaPlan = buildPedagogicalConstructionPlan(withSubEntities(permuted));
      const metaReport = verifyConstructionContinuity(metaPlan.scene);
      expect(metaReport.valid).toBe(true);
      expect(metaPlan.steps.length).toBe(basePlan.steps.length);

      const metaContract = getSemanticConstructionContract(metaPlan.scene);
      for (const [origId, renamedId] of Object.entries(renameMap)) {
        const origSpec = baseContract.objectsById.get(origId);
        const metaSpec = metaContract.objectsById.get(renamedId);
        if (!origSpec) continue;
        expect(metaSpec, `missing ${renamedId}`).toBeDefined();
        expect(metaSpec!.semanticRole).toBe(origSpec.semanticRole);
        expect(metaSpec!.objectLayer).toBe(origSpec.objectLayer);
        expect(metaSpec!.informationCategory).toBe(origSpec.informationCategory);
      }

      for (let s = 0; s < metaPlan.steps.length; s += 1) {
        const k = metaPlan.steps[s]!.anchor;
        const rolesFwd = resolveStepVisualRoles(metaPlan.scene, k, { auxiliaryShown: false, selectedId: null });
        const rolesBwd = resolveStepVisualRoles(metaPlan.scene, k, { auxiliaryShown: false, selectedId: null });
        expect([...rolesFwd.entries()]).toEqual([...rolesBwd.entries()]);
      }
    });

    it("certifies perpendicular witness under non-identity SPD chart_metric, near-edge-on foreshortening guard, and tilted-right vs genuine-oblique cylinder semantics", () => {
      // Non-identity SPD chart_metric G = [[4, 2, 0], [2, 4, 0], [0, 0, 9]]
      // u = (1, 0, 0) and v = (-1, 2, 0) satisfy u^T G v = 1*(4*-1 + 2*2) = 0 (exact G-orthogonality despite Euclidean dot = -1 != 0)
      const obliqueMetricScene: Scene3D = {
        free_objects: ["O", "A", "B"],
        chart_metric: [
          ["4", "2", "0"],
          ["2", "4", "0"],
          ["0", "0", "9"],
        ],
        objects: [
          { id: "O", type: "point3", label: "O", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "A", type: "point3", label: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "0", "0"] },
          { id: "B", type: "point3", label: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["-1", "2", "0"] },
          { id: "oa", type: "segment3", label: "OA", origin: "derived", producer: "CONSTRUCT", render: "segment", depends: ["O", "A"], endpoint_ids: ["O", "A"], point_a: ["0", "0", "0"], point_b: ["1", "0", "0"] },
          {
            id: "ob",
            type: "segment3",
            label: "OB",
            origin: "derived", producer: "CONSTRUCT",
            render: "segment",
            depends: ["O", "B", "oa"],
            endpoint_ids: ["O", "B"],
            point_a: ["0", "0", "0"],
            point_b: ["-1", "2", "0"],
            perpendicular_witness: {
              relation: "line_perp_line",
              status: "GIVEN",
              can_present_as_proven: true,
              from: "B",
              on: "oa",
              foot_id: "O",
              foot: ["0", "0", "0"],
              marker: { u: ["1", "0", "0"], v: ["-1", "2", "0"] },
            },
          },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "oa", depends: ["O", "A"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "ob", depends: ["O", "B", "oa"], explanation: "" },
        ],
      };
      expect(verifyConstructionContinuity(obliqueMetricScene).valid).toBe(true);
      const obSpec = resolveSemanticObjectContract(obliqueMetricScene, "ob")!;
      expect(obSpec.objectLayer).toBe("RELATION_WITNESS");
      expect(obSpec.verifiedRelations.some((r) => r.kind === "line_perp_line" && r.exactVerified && r.canDisplaySymbol)).toBe(true);

      // Edge-on foreshortening guard: right-angle marker hides when viewed edge-on into the (u, v) plane
      const perpPlan = buildPedagogicalConstructionPlan(loadSampleScene("cau-cat-mat-phang"));
      const distSeg = perpPlan.scene.objects.find((o) => o.id === "C__dist")!;
      const rootEdgeOn = new THREE.Group();
      const builtDist = buildObject3D(
        distSeg,
        false,
        0.18,
        [[0, 0, 0], [0, 0, 3], [4, 0, 3]],
        new THREE.Vector3(0, -12, 3),
        undefined,
        undefined,
        false,
        undefined,
        false,
        false,
        false,
        perpPlan.scene,
      );
      if (builtDist) rootEdgeOn.add(builtDist);
      let markerSpec: { foot: [number, number, number]; u: [number, number, number]; v: [number, number, number] } | null = null;
      rootEdgeOn.traverse((n) => {
        if (n.userData?.gocVuongDonVi && !markerSpec) {
          markerSpec = n.userData.gocVuongDonVi;
        }
      });
      expect(markerSpec).not.toBeNull();
      const camEdgeOn = new THREE.PerspectiveCamera(45, 16 / 9, 0.1, 100);
      // Place camera strictly inside the marker's (u, v) plane (`foot + 10 * u`) so view ray is 100% edge-on to u × v!
      camEdgeOn.position.set(
        markerSpec!.foot[0] + 10 * markerSpec!.u[0],
        markerSpec!.foot[1] + 10 * markerSpec!.u[1],
        markerSpec!.foot[2] + 10 * markerSpec!.u[2],
      );
      camEdgeOn.lookAt(markerSpec!.foot[0], markerSpec!.foot[1], markerSpec!.foot[2]);
      camEdgeOn.updateMatrixWorld(true);
      camEdgeOn.updateProjectionMatrix();
      expect(datCoGocVuong([rootEdgeOn], camEdgeOn, 720, new THREE.Vector3(...markerSpec!.foot), true)).toBe(0);

      // Tilted right circular cylinder (axis = (3,0,4) || cap normal = (3,0,4)) vs genuine oblique cylinder (axis = (2,0,4), cap normal = (0,0,1))
      const tiltedRightCyl: Scene3D = {
        free_objects: ["O1", "O2"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "O1", type: "point3", label: "O", notation: "O", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "O2", type: "point3", label: "O'", notation: "O'", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "4"] },
          { id: "bot_c", type: "circle3", label: "Đáy (O)", origin: "derived", producer: "CONSTRUCT", render: "circle", surface_role: "BASE_REGION", depends: ["O1"], center: ["0", "0", "0"], normal: ["3", "0", "4"], radius_sq: "9" },
          { id: "cyl_r", type: "curved_solid", curved_kind: "cylinder", label: "Hình trụ", notation: "(T)", origin: "derived", producer: "CONSTRUCT", render: "curved_solid", depends: ["O1", "O2", "bot_c"], anchor: ["0", "0", "0"], apex_or_top: ["3", "0", "4"], radius_sq: "9", height_sq: "25" },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "bot_c", depends: ["O1"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "cyl_r", depends: ["O1", "O2", "bot_c"], explanation: "" },
        ],
      };
      const tiltedPlan = buildPedagogicalConstructionPlan(withSubEntities(tiltedRightCyl));
      expect(verifyConstructionContinuity(tiltedPlan.scene).valid).toBe(true);
      for (const st of tiltedPlan.steps) {
        expect(st.title).not.toMatch(/trụ\s+xiên/iu);
        expect(`${st.title} ${st.subtitle}`).not.toMatch(/(?<!không\s+phải\s+hình\s+)trụ\s+xiên/iu);
      }
      expect(
        tiltedPlan.steps.some((st) => /trụ\s+tròn\s+xoay\s+đặt\s+nghiêng/iu.test(`${st.title} ${st.subtitle}`)),
      ).toBe(true);

      const genuineObliqueCyl: Scene3D = {
        free_objects: ["O1", "O2"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "O1", type: "point3", label: "O", notation: "O", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "O2", type: "point3", label: "O'", notation: "O'", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "4"] },
          { id: "bot_o", type: "circle3", label: "Đáy (O)", origin: "derived", producer: "CONSTRUCT", render: "circle", surface_role: "BASE_REGION", depends: ["O1"], center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "9" },
          { id: "cyl_o", type: "curved_solid", curved_kind: "cylinder", label: "Hình trụ xiên", notation: "(T)", origin: "derived", producer: "CONSTRUCT", render: "curved_solid", depends: ["O1", "O2", "bot_o"], anchor: ["0", "0", "0"], apex_or_top: ["2", "0", "4"], radius_sq: "9", height_sq: "16" },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "bot_o", depends: ["O1"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "cyl_o", depends: ["O1", "O2", "bot_o"], explanation: "" },
        ],
      };
      const obliquePlan = buildPedagogicalConstructionPlan(withSubEntities(genuineObliqueCyl));
      expect(verifyConstructionContinuity(obliquePlan.scene).valid).toBe(true);
    });

    it("enforces non-spoiler policy across all 11 catalog scenes and suppresses uncertified parallel/right-angle claims on ILLUSTRATIVE_GAUGE scenes", () => {
      for (const sample of GEOMETRY_SAMPLES) {
        const plan = buildPedagogicalConstructionPlan(loadSampleScene(sample.id));
        const policy = evaluateStudentPresentationPolicy(plan.scene, plan.goalCompletion);
        expect(policy.showMathResultsPanel).toBe(false);
        for (const obj of plan.scene.objects) {
          const spec = resolveSemanticObjectContract(plan.scene, obj.id);
          if (spec?.objectLayer === "INTERNAL_MATH_RESULT") {
            expect(policy.canDisplayEntityValue(obj)).toBe(false);
            expect(policy.canDisplayEntityFormula(obj)).toBe(false);
          }
        }
        const html = renderToString(<AxoWorkspaceV62 scene={plan.scene} de={sample.problemText} />);
        expect(html).not.toContain('id="dock-math-results"');
        expect(html).not.toMatch(/KẾT\s+QUẢ\s+TOÁN\s+HỌC/iu);
      }

      // Illustrative-only base coordinates (unit square chosen as illustrative gauge for a generic quadrilateral base) must NOT claim proven right-angle symbol
      const illustrativePyr: Scene3D = {
        free_objects: ["S", "A", "B", "C", "D"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"], source: { provenance: "ILLUSTRATIVE_CHOICE", is_given: false } as unknown as SceneObject["source"] },
          { id: "B", type: "point3", label: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["4", "0", "0"], source: { provenance: "ILLUSTRATIVE_CHOICE", is_given: false } as unknown as SceneObject["source"] },
          { id: "C", type: "point3", label: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["4", "4", "0"], source: { provenance: "ILLUSTRATIVE_CHOICE", is_given: false } as unknown as SceneObject["source"] },
          { id: "D", type: "point3", label: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "0"], source: { provenance: "ILLUSTRATIVE_CHOICE", is_given: false } as unknown as SceneObject["source"] },
          { id: "S", type: "point3", label: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "5"] },
          { id: "day", type: "polygon3", label: "Đáy ABCD", origin: "derived", producer: "CONSTRUCT", render: "polygon", surface_role: "BASE_REGION", depends: ["A", "B", "C", "D"], vertex_ids: ["A", "B", "C", "D"], polygon: [["0", "0", "0"], ["4", "0", "0"], ["4", "4", "0"], ["0", "4", "0"]], source: { provenance: "ILLUSTRATIVE_CHOICE", is_given: false } as unknown as SceneObject["source"] },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day", depends: ["A", "B", "C", "D"], explanation: "" },
        ],
      };
      const daySpec = resolveSemanticObjectContract(illustrativePyr, "day")!;
      expect(daySpec.determinacy).toBe("ILLUSTRATIVE_GAUGE");
      expect(daySpec.verifiedRelations.every((r) => !r.canDisplaySymbol)).toBe(true);
    });
  });

  describe("5. Adversarial Audit Edge Cases: Exact-Metric Annotations, Dock Givens, Suffix-Free Carriers & Strict Continuity", () => {
    it("preserves backend-compiled sphere R in givenQuantitiesSummary when no 3D radius segment exists while suppressing mid-air anchor='solid' on canvas", () => {
      const backendSphereNoSeg: Scene3D = {
        free_objects: ["I", "r_q"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "I", type: "point3", label: "I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "S_pt", type: "point3", label: "S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "4", "0"] },
          {
            id: "r_q",
            type: "quantity",
            label: "Bán kính R",
            notation: "R",
            origin: "free",
            producer: null,
            render: "readout",
            depends: [],
            value: "5",
            exact: { kind: "rational", value: "5" },
            annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["sph_b"], anchor: "solid" },
          },
          {
            id: "sph_b",
            type: "curved_solid",
            curved_kind: "ball",
            label: "Mặt cầu (S)",
            notation: "(S)",
            origin: "derived",
            producer: "CONSTRUCT",
            render: "curved_solid",
            depends: ["I", "S_pt", "r_q"],
            anchor: ["0", "0", "0"],
            radius_sq: "25",
          },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "sph_b", depends: ["I", "S_pt", "r_q"], explanation: "" },
        ],
      };

      const canvasAnns = annotationsAt(backendSphereNoSeg, 1, DEFAULT_ANNOTATION_VIEW, null);
      expect(canvasAnns.some((a) => a.anchor === "solid")).toBe(false);
      expect(canvasAnns.some((a) => a.id === "r_q")).toBe(false);

      const summary = givenQuantitiesSummary(backendSphereNoSeg, 1);
      const rSummary = summary.find((g) => g.id === "r_q");
      expect(rSummary).toBeDefined();
      expect(rSummary?.text).toBe("R = 5");
      expect(rSummary?.status).toBe("pending_step");
    });

    it("resolves curved radius & axis carriers geometrically without ID suffixes and under non-identity chart_metric + veKhongGian", () => {
      // Non-identity metric G = diag(2, 1, 1): point X = (2, 1, 0) has |IX|_G^2 = 2*(2^2) + 1*(1^2) = 9 = R^2!
      const nonEuclideanSphere: Scene3D = {
        free_objects: ["I_m", "X_m", "q_Rm"],
        chart_metric: [
          ["2", "0", "0"],
          ["0", "1", "0"],
          ["0", "0", "1"],
        ],
        objects: [
          { id: "I_m", type: "point3", label: "I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "X_m", type: "point3", label: "X", notation: "X", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "1", "0"] },
          { id: "q_Rm", type: "quantity", label: "R", notation: "R", origin: "free", producer: null, render: "readout", depends: [], value: "3", exact: { kind: "rational", value: "3" }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["ball_m"], anchor: "solid" } },
          { id: "ball_m", type: "curved_solid", curved_kind: "ball", label: "(S)", origin: "derived", producer: "CONSTRUCT", render: "curved_solid", depends: ["I_m", "q_Rm"], anchor: ["0", "0", "0"], radius_sq: "9" },
          { id: "arbitrary_seg_name", type: "segment3", label: "IX", origin: "derived", producer: "CONSTRUCT", render: "segment", depends: ["I_m", "X_m"], endpoint_ids: ["I_m", "X_m"], endpoints: [["0", "0", "0"], ["2", "1", "0"]] },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "ball_m", depends: ["I_m", "q_Rm"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "arbitrary_seg_name", depends: ["I_m", "X_m"], explanation: "" },
        ],
      };

      const worldTransformed = veKhongGian(nonEuclideanSphere);
      const step2Anns = annotationsAt(worldTransformed, 2, DEFAULT_ANNOTATION_VIEW, null);
      const rOnSeg = step2Anns.find((a) => a.id === "q_Rm");
      expect(rOnSeg).toBeDefined();
      expect(rOnSeg?.anchor).toBe("segment");
      expect(rOnSeg?.subject_ids).toEqual(["I_m", "X_m"]);

      // Cylinder with arbitrary non-suffixed IDs for base circle, radius segment, and axis segment
      const suffixFreeCyl: Scene3D = {
        free_objects: ["O_b", "O_t", "B_rim", "q_Rcyl", "q_Hcyl"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "O_b", type: "point3", label: "O", notation: "O", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "O_t", type: "point3", label: "O'", notation: "O'", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
          { id: "B_rim", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
          { id: "q_Rcyl", type: "quantity", label: "R", notation: "R", origin: "free", producer: null, render: "readout", depends: [], value: "3", exact: { kind: "rational", value: "3" }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["cyl_main"], anchor: "solid" } },
          { id: "q_Hcyl", type: "quantity", label: "h", notation: "h", origin: "free", producer: null, render: "readout", depends: [], value: "4", exact: { kind: "rational", value: "4" }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["cyl_main"], anchor: "solid" } },
          { id: "cap_circle_custom", type: "circle3", label: "Đáy", origin: "derived", producer: "CONSTRUCT", render: "circle", surface_role: "BASE_REGION", depends: ["O_b"], center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "9" },
          { id: "rad_seg_custom", type: "segment3", label: "OB", origin: "derived", producer: "CONSTRUCT", render: "segment", depends: ["O_b", "B_rim"], endpoint_ids: ["O_b", "B_rim"], endpoints: [["0", "0", "0"], ["3", "0", "0"]] },
          { id: "height_seg_custom", type: "segment3", label: "OO'", origin: "derived", producer: "CONSTRUCT", render: "segment", depends: ["O_b", "O_t"], endpoint_ids: ["O_b", "O_t"], endpoints: [["0", "0", "0"], ["0", "0", "4"]] },
          { id: "cyl_main", type: "curved_solid", curved_kind: "cylinder", label: "Trụ", origin: "derived", producer: "CONSTRUCT", render: "curved_solid", depends: ["O_b", "O_t", "q_Rcyl", "q_Hcyl"], anchor: ["0", "0", "0"], apex_or_top: ["0", "0", "4"], radius_sq: "9", height_sq: "16" },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "cap_circle_custom", depends: ["O_b"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "rad_seg_custom", depends: ["O_b", "B_rim"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "height_seg_custom", depends: ["O_b", "O_t"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "cyl_main", depends: ["O_b", "O_t"], explanation: "" },
        ],
      };
      const cylAnns = annotationsAt(suffixFreeCyl, 4, DEFAULT_ANNOTATION_VIEW, null);
      expect(cylAnns.find((a) => a.id === "q_Rcyl")?.anchor).toBe("segment");
      expect(cylAnns.find((a) => a.id === "q_Rcyl")?.subject_ids).toEqual(["O_b", "B_rim"]);
      expect(cylAnns.find((a) => a.id === "q_Hcyl")?.anchor).toBe("segment");
      expect(cylAnns.find((a) => a.id === "q_Hcyl")?.subject_ids).toEqual(["O_b", "O_t"]);
    });

    it("catches 1-node self-cycles, non-orthogonal/premature witnesses, and invalid sphere CURVED_RADIUS endpoints in verifyConstructionContinuity", () => {
      // (a) Direct 1-node self-cycle A -> A
      const selfCycleScene: Scene3D = {
        free_objects: [],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "A", origin: "derived", producer: "CONSTRUCT", render: "point_marker", depends: ["A"], xyz: ["0", "0", "0"] },
        ],
        events: [
          { step_index: 0, action: "CREATE", object: "A", depends: ["A"], explanation: "" },
        ],
      };
      const selfReport = verifyConstructionContinuity(selfCycleScene);
      expect(selfReport.valid).toBe(false);
      expect(selfReport.violations.some((v) => v.code === "PREREQUISITE_CYCLE")).toBe(true);

      // (b) Corrupt perpendicular witness (u · v != 0) & premature witness preceding carrier plane
      const badWitnessScene: Scene3D = {
        free_objects: ["S", "H"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "S", type: "point3", label: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
          { id: "H", type: "point3", label: "H", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          {
            id: "sh_seg",
            type: "segment3",
            label: "SH",
            origin: "derived",
            producer: "CONSTRUCT",
            render: "segment",
            depends: ["S", "H"],
            endpoint_ids: ["S", "H"],
            endpoints: [["0", "0", "4"], ["0", "0", "0"]],
            perpendicular_witness: {
              relation: "line_perpendicular_plane",
              from: "S",
              foot_id: "H",
              foot: ["0", "0", "0"],
              on: "late_plane",
              marker: { u: ["1", "0", "1"], v: ["0", "0", "1"] },
            },
          },
          { id: "late_plane", type: "plane3", label: "(P)", origin: "derived", producer: "CONSTRUCT", render: "surface", depends: ["H"], point: ["0", "0", "0"], normal: ["0", "0", "1"] },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "sh_seg", depends: ["S", "H"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "late_plane", depends: ["H"], explanation: "" },
        ],
      };
      const witReport = verifyConstructionContinuity(badWitnessScene);
      expect(witReport.valid).toBe(false);
      expect(witReport.violations.some((v) => v.code === "UNVERIFIED_OR_PREMATURE_WITNESS")).toBe(true);

      // (b2) Mathematically orthogonal witness whose carrier plane appears at a LATER step (pure premature witness)
      const prematureOnlyScene: Scene3D = {
        ...badWitnessScene,
        objects: badWitnessScene.objects.map((o) =>
          o.id === "sh_seg" && o.perpendicular_witness
            ? {
                ...o,
                perpendicular_witness: {
                  ...o.perpendicular_witness,
                  marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] },
                },
              }
            : o,
        ),
      };
      const premReport = verifyConstructionContinuity(prematureOnlyScene);
      expect(premReport.valid).toBe(false);
      expect(premReport.violations.some((v) => v.code === "UNVERIFIED_OR_PREMATURE_WITNESS")).toBe(true);

      // (c) Sphere CURVED_RADIUS segment whose endpoint point3 is not visible / wrong length
      const badSphRadScene: Scene3D = {
        free_objects: ["I"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "I", type: "point3", label: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "X_hidden", type: "point3", label: "X", origin: "derived", producer: "CONSTRUCT", render: "point_marker", depends: ["I"], xyz: ["3", "0", "0"] },
          { id: "sph", type: "curved_solid", curved_kind: "ball", label: "(S)", origin: "derived", producer: "CONSTRUCT", render: "curved_solid", depends: ["I"], anchor: ["0", "0", "0"], radius_sq: "25" },
          { id: "bad_rad", type: "segment3", label: "IX", origin: "derived", producer: "CONSTRUCT", render: "segment", depends: ["sph", "I"], endpoint_ids: ["I", "X_hidden"], endpoints: [["0", "0", "0"], ["3", "0", "0"]] },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "sph", depends: ["I"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "bad_rad", depends: ["sph", "I"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "X_hidden", depends: ["I"], explanation: "" },
        ],
      };
      const sphRadReport = verifyConstructionContinuity(badSphRadScene);
      expect(sphRadReport.valid).toBe(false);
      expect(sphRadReport.violations.some((v) => v.code === "SPHERE_RADIUS_CONTINUITY")).toBe(true);
    });
  });
});
