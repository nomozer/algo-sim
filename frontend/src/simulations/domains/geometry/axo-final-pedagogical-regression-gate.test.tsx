import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import {
  annotationsAt,
  DEFAULT_ANNOTATION_VIEW,
  givenQuantitiesSummary,
} from "./scene3d-annotations";
import { veKhongGian } from "./scene3d-chart";
import { learnerTextIsSafe, objectsAt, toVec3, type Scene3D, type SceneObject } from "./scene3d-model";
import {
  buildPedagogicalConstructionPlan,
  buildPedagogicalStepNarration,
  computeBoundedStudiedPlanePolygon,
  computeOptimalInPlaneWitnessBasis,
  deriveExactPolygonMathBasis,
  getSemanticConstructionContract,
  pedagogicalStepList,
  registerExactSceneOrigin,
  resolvePlanePerpendicularLineWitness,
  resolvePlaneSectionVisibility,
  resolveSceneLocalViewRay,
  resolveStepVisualRoles,
  verifyConstructionContinuity,
  verifyVisualContinuity,
} from "./scene3d-semantic-policy";
import { withSubEntities } from "./scene3d-subentities";
import { buildObject3D, capNhatDauSongSong, datCoGocVuong } from "./scene3d-view";

function buildAtStep(
  o: SceneObject,
  scene: Scene3D,
  visibleStepObjects: readonly SceneObject[] = scene.objects,
): THREE.Object3D | null {
  return buildObject3D(
    o,
    false,
    undefined,
    [],
    undefined,
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
    undefined,
    visibleStepObjects,
  );
}

function prepareScene(rawInput: unknown): Scene3D {
  const raw = rawInput as Scene3D;
  const sub = withSubEntities(veKhongGian(raw));
  const plan = buildPedagogicalConstructionPlan(sub);
  registerExactSceneOrigin(plan.scene, raw);
  return plan.scene;
}

function loadSampleScene(sampleId: string): Scene3D {
  const sample = GEOMETRY_SAMPLES.find((s) => s.id === sampleId);
  if (!sample) throw new Error(`Missing geometry sample: ${sampleId}`);
  const raw = structuredClone((sample.envelope as unknown as { scene3d: Scene3D }).scene3d);
  return prepareScene(raw);
}

function makeHoldoutCuboidHexagonScene(): Scene3D {
  const raw = {
    schema_version: "1.0",
    coordinate_frame: "right_handed_z_up",
    free_objects: ["A", "B", "C", "D", "Ap", "Bp", "Cp", "Dp"],
    objects: [
      { id: "A", type: "point3", render: "point", origin: "free", depends: [], xyz: [0, 0, 0], notation: "A", display_group: ["given"] },
      { id: "B", type: "point3", render: "point", origin: "free", depends: [], xyz: [4, 0, 0], notation: "B", display_group: ["given"] },
      { id: "C", type: "point3", render: "point", origin: "free", depends: [], xyz: [4, 4, 0], notation: "C", display_group: ["given"] },
      { id: "D", type: "point3", render: "point", origin: "free", depends: [], xyz: [0, 4, 0], notation: "D", display_group: ["given"] },
      { id: "Ap", type: "point3", render: "point", origin: "free", depends: [], xyz: [0, 0, 4], notation: "A'", display_group: ["given"] },
      { id: "Bp", type: "point3", render: "point", origin: "free", depends: [], xyz: [4, 0, 4], notation: "B'", display_group: ["given"] },
      { id: "Cp", type: "point3", render: "point", origin: "free", depends: [], xyz: [4, 4, 4], notation: "C'", display_group: ["given"] },
      { id: "Dp", type: "point3", render: "point", origin: "free", depends: [], xyz: [0, 4, 4], notation: "D'", display_group: ["given"] },
      {
        id: "base_abcd",
        type: "polygon3",
        render: "surface",
        origin: "derived",
        depends: ["A", "B", "C", "D"],
        vertex_ids: ["A", "B", "C", "D"],
        vertices: [[0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 4, 0]],
        surface_role: "BASE_REGION",
        formation_roles: ["CONSTRUCT_BASE"],
        notation: "(ABCD)",
        display_group: ["given"],
      },
      {
        id: "cube",
        type: "solid",
        render: "mesh",
        origin: "derived",
        depends: ["A", "B", "C", "D", "Ap", "Bp", "Cp", "Dp"],
        vertex_ids: ["A", "B", "C", "D", "Ap", "Bp", "Cp", "Dp"],
        vertices: [[0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 4, 0], [0, 0, 4], [4, 0, 4], [4, 4, 4], [0, 4, 4]],
        faces: [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]],
        formation_roles: ["CONSTRUCT_SOLID"],
        display_group: ["given"],
      },
      { id: "U", type: "point3", render: "point", origin: "derived", depends: ["A", "B"], xyz: [2, 0, 0], notation: "U", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], display_group: ["given"] },
      { id: "V", type: "point3", render: "point", origin: "derived", depends: ["A", "D"], xyz: [0, 2, 0], notation: "V", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], display_group: ["given"] },
      { id: "W", type: "point3", render: "point", origin: "derived", depends: ["D", "Dp"], xyz: [0, 4, 2], notation: "W", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], display_group: ["given"] },
      {
        id: "mp_hex",
        type: "plane3",
        render: "surface",
        origin: "derived",
        depends: ["U", "V", "W"],
        point: [2, 0, 0],
        normal: [1, 1, -1],
        surface_role: "CUTTING_PLANE",
        formation_roles: ["CONSTRUCT_CUTTING_OBJECT"],
        notation: "(UVW)",
        display_group: ["auxiliary"],
      },
      { id: "X", type: "point3", render: "point", origin: "derived", depends: ["mp_hex", "Cp", "Dp"], xyz: [2, 4, 4], notation: "X", formation_roles: ["DERIVE_INTERSECTION"], display_group: ["target"] },
      { id: "Y", type: "point3", render: "point", origin: "derived", depends: ["mp_hex", "Bp", "Cp"], xyz: [4, 2, 4], notation: "Y", formation_roles: ["DERIVE_INTERSECTION"], display_group: ["target"] },
      { id: "Z", type: "point3", render: "point", origin: "derived", depends: ["mp_hex", "B", "Bp"], xyz: [4, 0, 2], notation: "Z", formation_roles: ["DERIVE_INTERSECTION"], display_group: ["target"] },
      {
        id: "sec_hex",
        type: "section",
        render: "surface",
        origin: "derived",
        depends: ["cube", "mp_hex", "U", "V", "W", "X", "Y", "Z"],
        vertex_ids: ["U", "V", "W", "X", "Y", "Z"],
        polygon: [[2, 0, 0], [0, 2, 0], [0, 4, 2], [2, 4, 4], [4, 2, 4], [4, 0, 2]],
        closed: true,
        fill_visible: true,
        semantic_role: "RESULT_SECTION",
        formation_roles: ["PRODUCE_SECTION_RESULT"],
        notation: "(UVWXYZ)",
        display_group: ["target"],
      },
    ],
    events: [
      { id: "ev0", action: "CREATE", object: "base_abcd", title: "Dựng mặt đáy (ABCD)" },
      { id: "ev1", action: "CREATE", object: "cube", title: "Dựng hình lập phương ABCD.A'B'C'D'" },
      { id: "ev2", action: "CREATE", object: "U", title: "Lấy trung điểm U của AB" },
      { id: "ev3", action: "CREATE", object: "V", title: "Lấy trung điểm V của AD" },
      { id: "ev4", action: "CREATE", object: "W", title: "Lấy trung điểm W của DD'" },
      { id: "ev5", action: "CREATE", object: "mp_hex", title: "Dựng mặt phẳng cắt (UVW)" },
      { id: "ev6", action: "CREATE", object: "X", title: "Tìm giao điểm X trên C'D'" },
      { id: "ev7", action: "CREATE", object: "Y", title: "Tìm giao điểm Y trên B'C'" },
      { id: "ev8", action: "CREATE", object: "Z", title: "Tìm giao điểm Z trên BB'" },
      { id: "ev9", action: "CREATE", object: "sec_hex", title: "Khép kín thiết diện lục giác (UVWXYZ)" },
    ],
  };
  return prepareScene(raw);
}

function makeHoldoutObliquePrismParallelScene(): Scene3D {
  const raw = {
    schema_version: "1.0",
    coordinate_frame: "right_handed_z_up",
    free_objects: ["D", "E", "F", "Dp", "Ep", "Fp"],
    objects: [
      { id: "D", type: "point3", render: "point", origin: "free", depends: [], xyz: [0, 0, 0], notation: "D", display_group: ["given"] },
      { id: "E", type: "point3", render: "point", origin: "free", depends: [], xyz: [4, 0, 0], notation: "E", display_group: ["given"] },
      { id: "F", type: "point3", render: "point", origin: "free", depends: [], xyz: [1, 3, 0], notation: "F", display_group: ["given"] },
      { id: "Dp", type: "point3", render: "point", origin: "free", depends: [], xyz: [1, 1, 4], notation: "D'", display_group: ["given"] },
      { id: "Ep", type: "point3", render: "point", origin: "free", depends: [], xyz: [5, 1, 4], notation: "E'", display_group: ["given"] },
      { id: "Fp", type: "point3", render: "point", origin: "free", depends: [], xyz: [2, 4, 4], notation: "F'", display_group: ["given"] },
      {
        id: "base_def",
        type: "polygon3",
        render: "surface",
        origin: "derived",
        depends: ["D", "E", "F"],
        vertex_ids: ["D", "E", "F"],
        vertices: [[0, 0, 0], [4, 0, 0], [1, 3, 0]],
        surface_role: "BASE_REGION",
        formation_roles: ["CONSTRUCT_BASE"],
        notation: "(DEF)",
        display_group: ["given"],
      },
      {
        id: "prism_ob",
        type: "solid",
        render: "mesh",
        origin: "derived",
        depends: ["D", "E", "F", "Dp", "Ep", "Fp"],
        vertex_ids: ["D", "E", "F", "Dp", "Ep", "Fp"],
        vertices: [[0, 0, 0], [4, 0, 0], [1, 3, 0], [1, 1, 4], [5, 1, 4], [2, 4, 4]],
        faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]],
        formation_roles: ["CONSTRUCT_SOLID"],
        display_group: ["given"],
      },
      { id: "M", type: "point3", render: "point", origin: "derived", depends: ["D", "Dp"], xyz: ["1/2", "1/2", 2], notation: "M", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], display_group: ["given"] },
      { id: "N", type: "point3", render: "point", origin: "derived", depends: ["E", "Ep"], xyz: ["9/2", "1/2", 2], notation: "N", formation_roles: ["DERIVE_INTERSECTION"], display_group: ["target"] },
      {
        id: "seg_MN_ob",
        type: "segment3",
        render: "line",
        origin: "derived",
        producer: "intersect_planes",
        depends: ["M", "N"],
        endpoint_ids: ["M", "N"],
        endpoints: [["1/2", "1/2", 2], ["9/2", "1/2", 2]],
        formation_roles: ["DERIVE_INTERSECTION"],
        notation: "MN",
        display_group: ["target"],
      },
    ],
    events: [
      { id: "ev0", action: "CREATE", object: "base_def", title: "Dựng mặt đáy (DEF)" },
      { id: "ev1", action: "CREATE", object: "prism_ob", title: "Dựng lăng trụ xiên DEF.D'E'F'" },
      { id: "ev2", action: "CREATE", object: "M", title: "Lấy trung điểm M của cạnh bên DD'" },
      { id: "ev3", action: "CREATE", object: "N", title: "Xác định giao điểm N trên cạnh bên EE'" },
      { id: "ev4", action: "CREATE", object: "seg_MN_ob", title: "Dựng đoạn giao tuyến MN song song với DE" },
    ],
  };
  return prepareScene(raw);
}

function makeHoldoutHorizontalTangentSphereScene(): Scene3D {
  const raw = {
    schema_version: "1.0",
    coordinate_frame: "right_handed_z_up",
    free_objects: ["I", "P"],
    objects: [
      { id: "I", type: "point3", render: "point", origin: "free", depends: [], xyz: [0, 0, 4], notation: "I", display_group: ["given"] },
      {
        id: "S_ball",
        type: "curved_solid",
        curved_kind: "ball",
        render: "curved_solid",
        origin: "derived",
        depends: ["I"],
        anchor: [0, 0, 4],
        radius_sq: 16,
        formation_roles: ["CONSTRUCT_SOLID"],
        notation: "(S)",
        display_group: ["given"],
      },
      {
        id: "P",
        type: "plane3",
        render: "surface",
        origin: "free",
        depends: [],
        point: [0, 0, 0],
        normal: [0, 0, 1],
        notation: "(P)",
        display_group: ["given"],
      },
    ],
    events: [
      { id: "ev0", action: "CREATE", object: "I", title: "Xác định tâm I của mặt cầu" },
      { id: "ev1", action: "CREATE", object: "S_ball", title: "Dựng mặt cầu tâm I bán kính R = 4" },
      { id: "ev2", action: "CREATE", object: "P", title: "Dựng mặt phẳng tiếp diện (P)" },
    ],
  };
  return prepareScene(raw);
}

function makeHoldoutCollinearNormalTangentSphereScene(): Scene3D {
  const raw = {
    schema_version: "1.0",
    coordinate_frame: "right_handed_z_up",
    free_objects: ["I", "mp_R"],
    objects: [
      { id: "I", type: "point3", render: "point", origin: "free", depends: [], xyz: [3, -8, 0], notation: "I", display_group: ["given"] },
      {
        id: "S_ball",
        type: "curved_solid",
        curved_kind: "ball",
        render: "curved_solid",
        origin: "derived",
        depends: ["I"],
        anchor: [3, -8, 0],
        radius_sq: 73,
        formation_roles: ["CONSTRUCT_SOLID"],
        notation: "(S)",
        display_group: ["given"],
      },
      {
        id: "mp_R",
        type: "plane3",
        render: "surface",
        origin: "free",
        depends: [],
        point: [0, 0, 0],
        normal: [3, -8, 0],
        notation: "(R)",
        display_group: ["given"],
      },
    ],
    events: [
      { id: "ev0", action: "CREATE", object: "I", title: "Xác định tâm I của mặt cầu" },
      { id: "ev1", action: "CREATE", object: "S_ball", title: "Dựng mặt cầu tâm I" },
      { id: "ev2", action: "CREATE", object: "mp_R", title: "Dựng mặt phẳng tiếp diện (R)" },
    ],
  };
  return prepareScene(raw);
}

function makeHoldoutInclinedSphereCutScene(): Scene3D {
  const raw = {
    schema_version: "1.0",
    coordinate_frame: "right_handed_z_up",
    free_objects: ["I", "mp_Q"],
    objects: [
      { id: "I", type: "point3", render: "point", origin: "free", depends: [], xyz: [0, 0, 0], notation: "I", display_group: ["given"] },
      {
        id: "S_ball",
        type: "curved_solid",
        curved_kind: "ball",
        render: "curved_solid",
        origin: "derived",
        depends: ["I"],
        anchor: [0, 0, 0],
        radius_sq: 25,
        formation_roles: ["CONSTRUCT_SOLID"],
        notation: "(S)",
        display_group: ["given"],
      },
      {
        id: "mp_Q",
        type: "plane3",
        render: "surface",
        origin: "free",
        depends: [],
        point: [1, 2, 2],
        normal: [1, 2, 2],
        surface_role: "CUTTING_PLANE",
        formation_roles: ["CONSTRUCT_CUTTING_OBJECT"],
        notation: "(Q)",
        display_group: ["given"],
      },
      {
        id: "C_cut",
        type: "circle3",
        render: "circle",
        origin: "derived",
        depends: ["S_ball", "mp_Q"],
        center: [1, 2, 2],
        normal: [1, 2, 2],
        radius_sq: 16,
        semantic_role: "RESULT_SECTION",
        formation_roles: ["PRODUCE_SECTION_RESULT"],
        notation: "(C)",
        display_group: ["target"],
      },
    ],
    events: [
      { id: "ev0", action: "CREATE", object: "I", title: "Xác định tâm I của mặt cầu" },
      { id: "ev1", action: "CREATE", object: "S_ball", title: "Dựng mặt cầu tâm I bán kính R = 5" },
      { id: "ev2", action: "CREATE", object: "mp_Q", title: "Dựng mặt phẳng nghiêng (Q)" },
      { id: "ev3", action: "CREATE", object: "C_cut", title: "Dựng đường tròn giao tuyến (C)" },
    ],
  };
  return prepareScene(raw);
}

function makeHoldoutObliquePyramidScene(): Scene3D {
  const raw = {
    schema_version: "1.0",
    coordinate_frame: "right_handed_z_up",
    free_objects: ["U", "V", "W", "X", "T"],
    objects: [
      { id: "U", type: "point3", render: "point", origin: "free", depends: [], xyz: [0, 0, 0], notation: "U", display_group: ["given"] },
      { id: "V", type: "point3", render: "point", origin: "free", depends: [], xyz: [5, 0, 0], notation: "V", display_group: ["given"] },
      { id: "W", type: "point3", render: "point", origin: "free", depends: [], xyz: [4, 4, 0], notation: "W", display_group: ["given"] },
      { id: "X", type: "point3", render: "point", origin: "free", depends: [], xyz: [0, 3, 0], notation: "X", display_group: ["given"] },
      { id: "T", type: "point3", render: "point", origin: "free", depends: [], xyz: [1, 1, 4], notation: "T", display_group: ["given"] },
      {
        id: "base_uvwx",
        type: "polygon3",
        render: "surface",
        origin: "derived",
        depends: ["U", "V", "W", "X"],
        vertex_ids: ["U", "V", "W", "X"],
        vertices: [[0, 0, 0], [5, 0, 0], [4, 4, 0], [0, 3, 0]],
        surface_role: "BASE_REGION",
        formation_roles: ["CONSTRUCT_BASE"],
        notation: "(UVWX)",
        display_group: ["given"],
      },
      {
        id: "pyr_ob",
        type: "solid",
        render: "mesh",
        origin: "derived",
        depends: ["T", "U", "V", "W", "X"],
        vertex_ids: ["T", "U", "V", "W", "X"],
        vertices: [[1, 1, 4], [0, 0, 0], [5, 0, 0], [4, 4, 0], [0, 3, 0]],
        faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]],
        formation_roles: ["CONSTRUCT_SOLID"],
        display_group: ["given"],
      },
      {
        id: "K_foot",
        type: "point3",
        render: "point",
        origin: "derived",
        depends: ["T", "base_uvwx"],
        xyz: [1, 1, 0],
        notation: "K",
        perpendicular_witness: {
          from: "T",
          from_point: [1, 1, 4],
          on: "base_uvwx",
          foot: [1, 1, 0],
          foot_id: "K_foot",
          relation: "line_perp_plane",
          can_present_as_proven: true,
          plane_directions: [[1, 0, 0], [0, 1, 0]],
          marker: { u: [1, 0, 0], v: [0, 0, 4] },
        },
        display_group: ["target"],
      },
      {
        id: "seg_TK",
        type: "segment3",
        render: "line",
        origin: "derived",
        depends: ["T", "K_foot", "base_uvwx"],
        endpoint_ids: ["T", "K_foot"],
        endpoints: [[1, 1, 4], [1, 1, 0]],
        formation_roles: ["CONSTRUCT_HEIGHT"],
        notation: "TK",
        perpendicular_witness: {
          from: "T",
          from_point: [1, 1, 4],
          on: "base_uvwx",
          foot: [1, 1, 0],
          foot_id: "K_foot",
          relation: "line_perp_plane",
          can_present_as_proven: true,
          plane_directions: [[1, 0, 0], [0, 1, 0]],
          marker: { u: [1, 0, 0], v: [0, 0, 4] },
        },
        display_group: ["target"],
      },
    ],
    events: [
      { id: "ev0", action: "CREATE", object: "base_uvwx", title: "Dựng mặt đáy tứ giác (UVWX)" },
      { id: "ev1", action: "CREATE", object: "pyr_ob", title: "Dựng hình chóp không vuông T.UVWX" },
      { id: "ev2", action: "CREATE", object: "K_foot", title: "Xác định hình chiếu K của T trên miền trong (UVWX)" },
      { id: "ev3", action: "CREATE", object: "seg_TK", title: "Hạ đường cao TK ⊥ (UVWX) tại K" },
    ],
  };
  return prepareScene(raw);
}

describe("AXO Final Pedagogical Visual Audit, Root-Cause Hardening & Regression Gate (§2–§12)", () => {
  describe("§3.1 & §3.3 — Optimal Orthonormal Witness Basis, Zero Backward Stub, Cylinder Step Invariance & Polygon Clamping", () => {
    it("replaces hardcoded [3, -8, 0] with optimal orthonormal witness basis that never collapses on n = (3, -8, 0) or face-on planes and is sign-invariant under n -> -n", () => {
      const normals: [number, number, number][] = [
        [0, 0, 1],
        [3, -8, 0],
        [-3, 8, 0],
        [8, 3, 6],
        [1, 2, 2],
        [2, -5, 3],
      ];
      const viewLen = Math.hypot(8, 3, 6);
      const rHat: [number, number, number] = [8 / viewLen, 3 / viewLen, 6 / viewLen];

      for (const n of normals) {
        const u = computeOptimalInPlaneWitnessBasis(n);
        const uNeg = computeOptimalInPlaneWitnessBasis([-n[0], -n[1], -n[2]]);
        const nLen = Math.hypot(n[0], n[1], n[2]);
        const nHat: [number, number, number] = [n[0] / nLen, n[1] / nLen, n[2] / nLen];

        expect(Math.hypot(u[0], u[1], u[2])).toBeCloseTo(1, 6);
        expect(Math.abs(u[0] * nHat[0] + u[1] * nHat[1] + u[2] * nHat[2])).toBeLessThan(1e-7);

        expect(u[0]).toBeCloseTo(uNeg[0], 6);
        expect(u[1]).toBeCloseTo(uNeg[1], 6);
        expect(u[2]).toBeCloseTo(uNeg[2], 6);

        const crossRN = Math.hypot(
          rHat[1] * nHat[2] - rHat[2] * nHat[1],
          rHat[2] * nHat[0] - rHat[0] * nHat[2],
          rHat[0] * nHat[1] - rHat[1] * nHat[0],
        );
        if (crossRN > 1e-3) {
          const cx = u[1] * nHat[2] - u[2] * nHat[1];
          const cy = u[2] * nHat[0] - u[0] * nHat[2];
          const cz = u[0] * nHat[1] - u[1] * nHat[0];
          const openness = Math.abs(cx * rHat[0] + cy * rHat[1] + cz * rHat[2]);
          expect(openness).toBeCloseTo(crossRN, 5);
        }
      }

      const colScene = makeHoldoutCollinearNormalTangentSphereScene();
      const distSeg = colScene.objects.find((o) => o.type === "segment3" && Boolean(o.perpendicular_witness));
      expect(distSeg).toBeDefined();
      const built = buildAtStep(distSeg!, colScene)!;
      expect(built.getObjectByName(`perp_plane_ray:${distSeg!.id}`)).toBeUndefined();
      expect(built.getObjectByName(`perp_marker:${distSeg!.id}`)).toBeUndefined();
      const vRaw = toVec3(distSeg!.perpendicular_witness!.marker!.v!);
      const vLen = Math.hypot(vRaw[0], vRaw[1], vRaw[2]);
      const vVec: [number, number, number] = [vRaw[0] / vLen, vRaw[1] / vLen, vRaw[2] / vLen];
      const uVec = computeOptimalInPlaneWitnessBasis(vVec, resolveSceneLocalViewRay(colScene));
      const crossUV = [
        uVec[1] * vVec[2] - uVec[2] * vVec[1],
        uVec[2] * vVec[0] - uVec[0] * vVec[2],
        uVec[0] * vVec[1] - uVec[1] * vVec[0],
      ];
      const opennessCol = Math.abs(crossUV[0] * rHat[0] + crossUV[1] * rHat[1] + crossUV[2] * rHat[2]);
      expect(opennessCol).toBeGreaterThan(0.95);
    });

    it("emits zero synthetic perp_plane_ray stubs when no in-plane segment exists, synthesizes grounded base diagonals on regular pyramids, and preserves real witness_leg on point-plane distance", () => {
      // 1. Cylinder cutting plane (`tru-thiet-dien-tron`): zero synthetic `perp_plane_ray` or ungrounded `perp_marker` on `P`
      const cylScene = loadSampleScene("tru-thiet-dien-tron");
      const cylSteps = pedagogicalStepList(cylScene);
      const planeP = cylScene.objects.find((o) => o.id === "P")!;
      const stepPlaneIdx = cylSteps.findIndex((st) => st.targetIds.includes("P"));
      const stepCircleIdx = cylSteps.findIndex((st) => st.targetIds.includes("C"));
      expect(stepPlaneIdx).toBeGreaterThanOrEqual(0);
      expect(stepCircleIdx).toBeGreaterThan(stepPlaneIdx);

      const builtStepPlane = buildAtStep(planeP, cylScene, objectsAt(cylScene, cylSteps[stepPlaneIdx]!.anchor))!;
      const builtStepCircle = buildAtStep(planeP, cylScene, objectsAt(cylScene, cylSteps[stepCircleIdx]!.anchor))!;
      expect(builtStepPlane.getObjectByName("perp_plane_ray:P")).toBeUndefined();
      expect(builtStepCircle.getObjectByName("perp_plane_ray:P")).toBeUndefined();
      expect(builtStepPlane.getObjectByName("perp_marker:P")).toBeUndefined();
      expect(builtStepCircle.getObjectByName("perp_marker:P")).toBeUndefined();

      // 2. Interior polygon foot without drawn diagonal (`TK ⊥ UVWX` at K = (1, 1, 0)): zero synthetic ray
      const obPyr = makeHoldoutObliquePyramidScene();
      const segTK = obPyr.objects.find((o) => o.id === "seg_TK")!;
      const builtTK = buildAtStep(segTK, obPyr)!;
      expect(builtTK.getObjectByName("perp_plane_ray:seg_TK")).toBeUndefined();
      expect(builtTK.getObjectByName("perp_marker:seg_TK")).toBeUndefined();

      // 2b. Regular square pyramid (`SO ⊥ EFGH` at center O = (0,0,0)): synthesizes `O__diag_1` & `O__diag_2` so `perp_marker:cao_SO` is grounded on real diagonals
      const regPyrRaw = {
        free_objects: ["E", "F", "G", "H", "O", "S"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "E", type: "point3", render: "point_marker", origin: "free", depends: [], xyz: ["-3", "-3", "0"], notation: "E" },
          { id: "F", type: "point3", render: "point_marker", origin: "free", depends: [], xyz: ["3", "-3", "0"], notation: "F" },
          { id: "G", type: "point3", render: "point_marker", origin: "free", depends: [], xyz: ["3", "3", "0"], notation: "G" },
          { id: "H", type: "point3", render: "point_marker", origin: "free", depends: [], xyz: ["-3", "3", "0"], notation: "H" },
          { id: "O", type: "point3", render: "point_marker", origin: "free", depends: [], xyz: ["0", "0", "0"], notation: "O" },
          { id: "S", type: "point3", render: "point_marker", origin: "free", depends: [], xyz: ["0", "0", "4"], notation: "S" },
          { id: "day_EFGH", type: "polygon3", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], origin: "derived", depends: ["E", "F", "G", "H"], vertex_ids: ["E", "F", "G", "H"], vertices: [["-3", "-3", "0"], ["3", "-3", "0"], ["3", "3", "0"], ["-3", "3", "0"]] },
          { id: "cao_SO", type: "segment3", render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], origin: "derived", depends: ["S", "O"], endpoint_ids: ["S", "O"], endpoints: [["0", "0", "4"], ["0", "0", "0"]], perpendicular_witness: { from: "S", foot: ["0", "0", "0"], foot_id: "O", on: "day_EFGH", relation: "line_perp_plane", status: "GIVEN", plane_directions: [["1", "0", "0"], ["0", "1", "0"]], marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] } } },
          { id: "khoi_SEFGH", type: "solid", shape_class: "PYRAMID_LIKE", render: "mesh", formation_roles: ["CLOSE_SOLID"], origin: "derived", depends: ["S", "E", "F", "G", "H"], vertex_ids: ["S", "E", "F", "G", "H"], vertices: [["0", "0", "4"], ["-3", "-3", "0"], ["3", "-3", "0"], ["3", "3", "0"], ["-3", "3", "0"]], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]] },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_EFGH", depends: ["E", "F", "G", "H"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "cao_SO", depends: ["S", "O"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "khoi_SEFGH", depends: ["S", "E", "F", "G", "H"], explanation: "" },
        ],
      };
      const regPyr = prepareScene(regPyrRaw as unknown as Scene3D);
      expect(regPyr.objects.some((o) => o.id === "O__diag_1")).toBe(true);
      expect(regPyr.objects.some((o) => o.id === "O__diag_2")).toBe(true);
      const regCaoSO = regPyr.objects.find((o) => o.id === "cao_SO")!;
      const builtRegSO = buildAtStep(regCaoSO, regPyr, objectsAt(regPyr, 2))!;
      expect(builtRegSO.getObjectByName("perp_marker:cao_SO")).toBeDefined();
      expect(builtRegSO.getObjectByName("perp_plane_ray:cao_SO")).toBeUndefined();

      const offCenterPyrRaw = {
        ...regPyrRaw,
        objects: regPyrRaw.objects.map((o) => {
          if (o.id === "O") return { ...o, xyz: ["1", "0", "0"] };
          if (o.id === "S") return { ...o, xyz: ["1", "0", "4"] };
          if (o.id === "cao_SO") {
            return {
              ...o,
              endpoints: [["1", "0", "4"], ["1", "0", "0"]],
              perpendicular_witness: {
                ...o.perpendicular_witness,
                foot: ["1", "0", "0"],
              },
            };
          }
          if (o.id === "khoi_SEFGH") {
            return {
              ...o,
              vertices: [["1", "0", "4"], ["-3", "-3", "0"], ["3", "-3", "0"], ["3", "3", "0"], ["-3", "3", "0"]],
            };
          }
          return o;
        }),
      };
      const offCenterPyr = prepareScene(offCenterPyrRaw as unknown as Scene3D);
      const caoSO = offCenterPyr.objects.find((o) => o.id === "cao_SO")!;
      const builtSO = buildAtStep(caoSO, offCenterPyr, objectsAt(offCenterPyr, 2))!;
      expect(builtSO.getObjectByName("perp_plane_ray:cao_SO")).toBeUndefined();
      expect(builtSO.getObjectByName("perp_marker:cao_SO")).toBeUndefined();

      // 3. Tangent sphere (`IH ⊥ (P)`) emits zero synthetic ray, while Point-plane distance (`mp-vuong-goc-duong` SH ⊥ (α)) keeps real `witness_leg`
      const tanSphere = makeHoldoutHorizontalTangentSphereScene();
      const ihObj = tanSphere.objects.find((o) => o.type === "segment3" && Boolean(o.perpendicular_witness))!;
      const builtIH = buildAtStep(ihObj, tanSphere)!;
      expect(builtIH.getObjectByName(`perp_plane_ray:${ihObj.id}`)).toBeUndefined();
      expect(builtIH.getObjectByName(`perp_marker:${ihObj.id}`)).toBeUndefined();

      const perpPlaneScene = loadSampleScene("mp-vuong-goc-duong");
      const shObj = perpPlaneScene.objects.find(
        (o) => o.type === "segment3" && Boolean(o.perpendicular_witness) && o.id !== "chieu_cao_SA",
      )!;
      const builtSH = buildAtStep(shObj, perpPlaneScene)!;
      expect(builtSH.getObjectByName(`perp_plane_ray:${shObj.id}`)).toBeUndefined();
      expect(builtSH.getObjectByName(`perp_marker:${shObj.id}`)).toBeDefined();
      let legSH: THREE.Line | null = null;
      builtSH.traverse((ch) => {
        if (ch.name === `witness_leg:${shObj.id}`) {
          legSH = ch as THREE.Line;
        }
      });
      expect(legSH).not.toBeNull();
      const posSH = (legSH as unknown as THREE.Line).geometry.getAttribute("position") as THREE.BufferAttribute;
      const footSH = toVec3(shObj.perpendicular_witness!.foot!);
      expect(
        Math.hypot(
          posSH.getX(0) - footSH[0],
          posSH.getY(0) - footSH[1],
          posSH.getZ(0) - footSH[2],
        ),
      ).toBeLessThan(1e-5);
    });

    it("selects a wide-open exact rational rim point M on inclined sphere-plane sections (`n = (1, 2, 2)`) while keeping `cau-cat-mat-phang` C__dist invariant across steps", () => {
      const incSphere = makeHoldoutInclinedSphereCutScene();
      const distSeg = incSphere.objects.find((o) => o.id === "C_cut__dist");
      expect(distSeg).toBeDefined();
      const builtInc = buildAtStep(distSeg!, incSphere)!;
      let markerInc: THREE.Line | null = null;
      builtInc.traverse((ch) => {
        if (ch.name === "perp_marker:C_cut__dist") markerInc = ch as THREE.Line;
      });
      expect(markerInc).not.toBeNull();
      const u = (markerInc as unknown as THREE.Line).userData.gocVuongDonVi.u as [number, number, number];
      const v = (markerInc as unknown as THREE.Line).userData.gocVuongDonVi.v as [number, number, number];
      const viewLen = Math.hypot(8, 3, 6);
      const rHat: [number, number, number] = [8 / viewLen, 3 / viewLen, 6 / viewLen];
      const maxOpenness = Math.hypot(
        rHat[1] * v[2] - rHat[2] * v[1],
        rHat[2] * v[0] - rHat[0] * v[2],
        rHat[0] * v[1] - rHat[1] * v[0],
      );
      const crossDot = Math.abs(
        (u[1] * v[2] - u[2] * v[1]) * rHat[0]
        + (u[2] * v[0] - u[0] * v[2]) * rHat[1]
        + (u[0] * v[1] - u[1] * v[0]) * rHat[2],
      );
      expect(crossDot).toBeGreaterThan(0.88 * maxOpenness);

      const catSphere = loadSampleScene("cau-cat-mat-phang");
      const catSteps = pedagogicalStepList(catSphere);
      const cDist = catSphere.objects.find((o) => o.id === "C__dist")!;
      const stepDistIdx = catSteps.findIndex((st) => objectsAt(catSphere, st.anchor).some((o) => o.id === "C__dist"));
      const stepRadIdx = catSteps.findIndex((st) => objectsAt(catSphere, st.anchor).some((o) => o.id === "C__sec_rad"));
      const stepCircleIdx = catSteps.findIndex((st) => objectsAt(catSphere, st.anchor).some((o) => o.id === "C"));
      expect(stepDistIdx).toBeGreaterThanOrEqual(0);
      expect(stepRadIdx).toBeGreaterThan(stepDistIdx);
      expect(stepCircleIdx).toBeGreaterThan(stepRadIdx);
      const bBeforeRad = buildAtStep(cDist, catSphere, objectsAt(catSphere, catSteps[stepDistIdx]!.anchor))!;
      expect(bBeforeRad.getObjectByName("perp_marker:C__dist")).toBeUndefined();
      const bStep3 = buildAtStep(cDist, catSphere, objectsAt(catSphere, catSteps[stepRadIdx]!.anchor))!;
      const bStep4 = buildAtStep(cDist, catSphere, objectsAt(catSphere, catSteps[stepCircleIdx]!.anchor))!;
      let m2: THREE.Line | null = null;
      let m3: THREE.Line | null = null;
      bStep3.traverse((ch) => { if (ch.name === "perp_marker:C__dist") m2 = ch as THREE.Line; });
      bStep4.traverse((ch) => { if (ch.name === "perp_marker:C__dist") m3 = ch as THREE.Line; });
      expect((m2 as unknown as THREE.Line).userData.gocVuongDonVi.u).toEqual(
        (m3 as unknown as THREE.Line).userData.gocVuongDonVi.u,
      );
    });
  });

  describe("§3.2 — Parallel (`∥`) Chevrons: `endpoints` Support, Scale Invariance, Multi-Family Ticks & Camera Edge-On Hiding", () => {
    it("certifies parallel relation on `endpoints`-based `segment3` (`seg_MN_ob`), governs step relevance via `showParallelWitnessSymbol`, and hides edge-on chevrons in `capNhatDauSongSong`", () => {
      const obPrism = makeHoldoutObliquePrismParallelScene();
      const contract = getSemanticConstructionContract(obPrism);
      const mnSpec = contract.objectsById.get("seg_MN_ob");
      expect(mnSpec).toBeDefined();
      const parRel = mnSpec!.verifiedRelations.find((r) => r.kind === "parallel" && r.canDisplaySymbol);
      expect(parRel).toBeDefined();
      expect(parRel!.targetIds.length).toBeGreaterThanOrEqual(2);

      // Closing-edge regression (`DD'` & `FF'` midpoints -> `MN || DF || D'F'` where `F -> D` wraps around `f.length - 1 -> 0`):
      const closingEdgeRaw = {
        schema_version: "1.0",
        coordinate_frame: "right_handed_z_up",
        free_objects: ["D", "E", "F", "D1", "E1", "F1"],
        objects: [
          { id: "D", type: "point3", render: "point", origin: "free", depends: [], xyz: [0, 0, 0], notation: "D", display_group: ["given"] },
          { id: "E", type: "point3", render: "point", origin: "free", depends: [], xyz: [4, 0, 0], notation: "E", display_group: ["given"] },
          { id: "F", type: "point3", render: "point", origin: "free", depends: [], xyz: [2, 3, 0], notation: "F", display_group: ["given"] },
          { id: "D1", type: "point3", render: "point", origin: "free", depends: [], xyz: [1, 1, 3], notation: "D′", display_group: ["given"] },
          { id: "E1", type: "point3", render: "point", origin: "free", depends: [], xyz: [5, 1, 3], notation: "E′", display_group: ["given"] },
          { id: "F1", type: "point3", render: "point", origin: "free", depends: [], xyz: [3, 4, 3], notation: "F′", display_group: ["given"] },
          {
            id: "lt_xien",
            type: "solid",
            render: "mesh",
            origin: "derived",
            depends: ["D", "E", "F", "D1", "E1", "F1"],
            vertices: [[0, 0, 0], [4, 0, 0], [2, 3, 0], [1, 1, 3], [5, 1, 3], [3, 4, 3]],
            vertex_ids: ["D", "E", "F", "D1", "E1", "F1"],
            faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]],
            formation_roles: ["CONSTRUCT_SOLID"],
            notation: "DEF.D′E′F′",
            display_group: ["given"],
          },
          { id: "M_cl", type: "point3", render: "point", origin: "derived", depends: ["D", "D1"], xyz: ["1/2", "1/2", "3/2"], notation: "M", display_group: ["target"] },
          { id: "P_cl", type: "point3", render: "point", origin: "derived", depends: ["F", "F1"], xyz: ["5/2", "7/2", "3/2"], notation: "P", display_group: ["target"] },
          {
            id: "seg_MP_cl",
            type: "segment3",
            render: "line",
            origin: "derived",
            producer: "intersect_planes",
            formation_roles: ["DERIVE_INTERSECTION"],
            depends: ["M_cl", "P_cl"],
            endpoints: [["1/2", "1/2", "3/2"], ["5/2", "7/2", "3/2"]],
            endpoint_ids: ["M_cl", "P_cl"],
            notation: "MP",
            role: "Giao tuyến MP",
            display_group: ["target"],
          },
          // Collinear sub-segment on the exact same line MP: must NOT be certified as parallel to MP!
          {
            id: "seg_collinear_MP",
            type: "segment3",
            render: "line",
            origin: "derived",
            depends: ["M_cl", "P_cl"],
            endpoints: [["1/2", "1/2", "3/2"], ["3/2", 2, "3/2"]],
            notation: "MQ",
            display_group: ["auxiliary"],
          },
        ],
        events: [
          { id: "ev0", action: "CREATE", object: "lt_xien", title: "Dựng lăng trụ DEF.D′E′F′" },
          { id: "ev1", action: "CREATE", object: "M_cl", title: "Trung điểm M" },
          { id: "ev2", action: "CREATE", object: "P_cl", title: "Trung điểm P" },
          { id: "ev3", action: "CREATE", object: "seg_MP_cl", title: "Dựng giao tuyến MP" },
        ],
      };
      const closingScene = prepareScene(closingEdgeRaw);
      const closingContract = getSemanticConstructionContract(closingScene);
      const mpRel = closingContract.objectsById.get("seg_MP_cl")?.verifiedRelations.find((r) => r.kind === "parallel");
      expect(mpRel).toBeDefined();
      expect(mpRel!.targetIds).toContain("lt_xien::edge:D-F");
      expect(mpRel!.targetIds).toContain("lt_xien::edge:D1-F1");
      expect(mpRel!.targetIds).not.toContain("lt_xien::edge:F-D");
      expect(mpRel!.targetIds).not.toContain("seg_collinear_MP");

      const finalAnchor = obPrism.events.length - 1;
      const roles = resolveStepVisualRoles(obPrism, finalAnchor, { auxiliaryShown: false, selectedId: null });
      expect(roles.get("seg_MN_ob")?.showParallelWitnessSymbol).toBe(true);

      const parRoot = new THREE.Group();
      const chevLine = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(0, 0, 0),
          new THREE.Vector3(0.1, 0, 0),
          new THREE.Vector3(0, 0.1, 0),
        ]),
        new THREE.LineBasicMaterial(),
      );
      chevLine.userData.parallelChevron = {
        center: [0, 0, 0],
        dirUnit: [1, 0, 0],
        scale: 0.12,
      };
      parRoot.add(chevLine);

      const edgeOnCam = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
      edgeOnCam.position.set(10, 0, 0);
      edgeOnCam.lookAt(0, 0, 0);
      capNhatDauSongSong(parRoot, edgeOnCam);
      expect(chevLine.visible).toBe(false);

      const broadsideCam = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
      broadsideCam.position.set(0, -8, 6);
      broadsideCam.lookAt(0, 0, 0);
      capNhatDauSongSong(parRoot, broadsideCam);
      expect(chevLine.visible).toBe(true);
    });
  });

  describe("§2 & §4 — Semantic Lifecycle Decoupling & 1-to-1 Witness Symbol Synchronization", () => {
    it("exposes explicit `lifecycleStage` & `showPlaneLabel` on `PlaneSectionVisibilityDecision` and synchronizes `showPerpWitnessSymbol` without opacity thresholds", () => {
      const chopScene = loadSampleScene("thiet-dien-chop");
      const chopSteps = pedagogicalStepList(chopScene);
      const mpObj = chopScene.objects.find((o) => o.id === "mp")!;
      const finalStep = chopSteps[chopSteps.length - 1]!;

      const pVisFinal = resolvePlaneSectionVisibility(
        chopScene,
        mpObj,
        finalStep.anchor,
        false,
        null,
        finalStep.startAnchor,
      );
      expect(pVisFinal.visible).toBe(true);
      expect(pVisFinal.lifecycleStage).toBe("consolidated_section_support");
      expect(pVisFinal.showPlaneLabel).toBe(false);

      const pVisAux = resolvePlaneSectionVisibility(
        chopScene,
        mpObj,
        finalStep.anchor,
        true,
        null,
        finalStep.startAnchor,
      );
      expect(pVisAux.showPlaneLabel).toBe(true);

      const mvgd = loadSampleScene("mp-vuong-goc-duong");
      const mvgdFinal = mvgd.events.length - 1;
      const mvgdRoles = resolveStepVisualRoles(mvgd, mvgdFinal, { auxiliaryShown: false, selectedId: null });
      const visList = objectsAt(mvgd, mvgdFinal);
      for (const o of mvgd.objects) {
        const entry = mvgdRoles.get(o.id);
        if (!entry?.visible) continue;
        if (o.type === "point3") {
          expect(entry.showPerpWitnessSymbol).toBe(false);
        }
        if (o.type === "plane3") {
          const hasPlaneWitness = resolvePlanePerpendicularLineWitness(mvgd, o, visList) !== null;
          expect(entry.showPerpWitnessSymbol).toBe(hasPlaneWitness);
        }
      }
    });
  });

  describe("§5 & §6 — Cutting-Plane Collar Bounds, Non-Repeating Narration, Specific Section Math & Non-Redundant `detailedEvidence`", () => {
    it("keeps `mat-cheo-sac` cutting plane top collar centered on section apex without breaking standalone studied planes", () => {
      const sacScene = loadSampleScene("mat-cheo-sac");
      const sacMp = sacScene.objects.find((o) => o.type === "plane3")!;
      const poly = computeBoundedStudiedPlanePolygon(sacScene, sacMp, sacScene.objects);
      expect(poly.length).toBeGreaterThanOrEqual(4);
      const xs = poly.map((p) => p[0]);
      const ys = poly.map((p) => p[1]);
      const topVerts = poly.filter((p) => p[2] > 2.5);
      expect(topVerts.length).toBeGreaterThanOrEqual(2);
      const topSpan = Math.hypot(
        Math.max(...topVerts.map((p) => p[0])) - Math.min(...topVerts.map((p) => p[0])),
        Math.max(...topVerts.map((p) => p[1])) - Math.min(...topVerts.map((p) => p[1])),
      );
      expect(topSpan).toBeLessThan(1.4);
      expect(Math.max(...xs) - Math.min(...xs)).toBeLessThan(6.5);
      expect(Math.max(...ys) - Math.min(...ys)).toBeLessThan(6.5);
    });

    it("produces non-repeating, mathematically specific `conciseRationale` across tangent sphere, point-plane distance, cone axial section, diagonal section, 6-gon cuboid section, and oblique prism parallel intersection", () => {
      // 1. Tangent sphere (`makeHoldoutHorizontalTangentSphereScene`): must NOT repeat "Kẻ IH ⊥ (P) tại H" in conciseRationale
      const tanSphere = makeHoldoutHorizontalTangentSphereScene();
      for (const st of pedagogicalStepList(tanSphere)) {
        const nar = buildPedagogicalStepNarration(tanSphere, st);
        if (nar.actionTitle.includes("IH ⊥ (P)")) {
          expect(nar.conciseRationale.startsWith(nar.actionTitle)).toBe(false);
          expect(nar.conciseRationale).not.toMatch(/^Kẻ\s+/iu);
          expect(nar.conciseRationale).toContain("(P)");
          expect(nar.detailedEvidence).toHaveLength(0);
        }
      }

      // 2. Point-plane distance (`mp-vuong-goc-duong`): must NOT repeat "Kẻ SH ⊥ (α) tại H" in conciseRationale
      const perpLinePlane = loadSampleScene("mp-vuong-goc-duong");
      for (const st of pedagogicalStepList(perpLinePlane)) {
        const nar = buildPedagogicalStepNarration(perpLinePlane, st);
        if (nar.actionTitle.includes("SH ⊥ (α)")) {
          expect(nar.conciseRationale.startsWith(nar.actionTitle)).toBe(false);
          expect(nar.conciseRationale).not.toMatch(/^Kẻ\s+/iu);
          expect(nar.conciseRationale).toContain("(α)");
          expect(nar.detailedEvidence).toHaveLength(0);
        }
      }

      // 3. Cone axial section (`non-thiet-dien-truc`): specific diameter + generator rationale (not generic "Nối các đỉnh để hoàn thiện...")
      const coneAxial = loadSampleScene("non-thiet-dien-truc");
      const coneSteps = pedagogicalStepList(coneAxial);
      const coneFinalNar = buildPedagogicalStepNarration(coneAxial, coneSteps[coneSteps.length - 1]!);
      expect(coneFinalNar.conciseRationale).not.toMatch(/^Nối các đỉnh để hoàn thiện/u);
      expect(coneFinalNar.conciseRationale).toMatch(/đường kính|đường sinh/u);

      // 4. Diagonal polyhedral section (`mat-cheo-sac`): specific shared edges SA, SC + base trace AC
      const sacScene = loadSampleScene("mat-cheo-sac");
      const sacSteps = pedagogicalStepList(sacScene);
      const sacFinalNar = buildPedagogicalStepNarration(sacScene, sacSteps[sacSteps.length - 1]!);
      expect(sacFinalNar.conciseRationale).not.toBe("Nối các đoạn giao tuyến trên từng mặt của khối để khép kín miền thiết diện (SAC).");
      expect(sacFinalNar.conciseRationale).toContain("SA");
      expect(sacFinalNar.conciseRationale).toContain("SC");
      expect(sacFinalNar.conciseRationale).toContain("AC");

      // 5. 6-gon hexagonal cuboid section (`UVWXYZ`): `deriveExactPolygonMathBasis` certifies opposite parallel edges UV ∥ XY, VW ∥ YZ, WX ∥ ZU
      const hexScene = makeHoldoutCuboidHexagonScene();
      const hexSec = hexScene.objects.find((o) => o.id === "sec_hex")!;
      const hexBasis = deriveExactPolygonMathBasis(hexScene, hexSec);
      expect(hexBasis).not.toBeNull();
      expect(hexBasis!.parallelPairs).toEqual(
        expect.arrayContaining(["UV ∥ XY", "VW ∥ YZ", "WX ∥ ZU"]),
      );
      const hexSteps = pedagogicalStepList(hexScene);
      const hexFinalNar = buildPedagogicalStepNarration(hexScene, hexSteps[hexSteps.length - 1]!);
      expect(hexFinalNar.conciseRationale).toContain("UV ∥ XY");
      expect(hexFinalNar.conciseRationale).toContain("VW ∥ YZ");
      expect(hexFinalNar.conciseRationale).toContain("WX ∥ ZU");

      // 6. Oblique prism parallel intersection (`seg_MN_ob`): specific parallel rationale (not generic "Xác định đường thẳng chung...")
      const obPrism = makeHoldoutObliquePrismParallelScene();
      const obSteps = pedagogicalStepList(obPrism);
      const obFinalNar = buildPedagogicalStepNarration(obPrism, obSteps[obSteps.length - 1]!);
      expect(obFinalNar.conciseRationale).toMatch(/song song|∥/u);
      expect(obFinalNar.detailedEvidence).toHaveLength(0);
    });
  });

  describe("§7 & §8 — Unseen Holdout Suite & Declaration-Order / Plane-Normal-Flip / Uniform-Scale Metamorphic Gate", () => {
    it("passes 4-dimensional verifyVisualContinuity and non-spoiler checks across all 6 Group C unseen holdout scenes", () => {
      const holdouts = [
        makeHoldoutCuboidHexagonScene(),
        makeHoldoutObliquePrismParallelScene(),
        makeHoldoutHorizontalTangentSphereScene(),
        makeHoldoutCollinearNormalTangentSphereScene(),
        makeHoldoutInclinedSphereCutScene(),
        makeHoldoutObliquePyramidScene(),
      ];

      for (const scene of holdouts) {
        const geo = verifyConstructionContinuity(scene);
        expect(geo.valid).toBe(true);
        const vis = verifyVisualContinuity(scene);
        expect(vis.violations).toEqual([]);
        expect(vis.valid).toBe(true);

        for (const st of pedagogicalStepList(scene)) {
          const nar = buildPedagogicalStepNarration(scene, st);
          expect(learnerTextIsSafe(scene, nar.actionTitle)).toBe(true);
          expect(learnerTextIsSafe(scene, nar.conciseRationale)).toBe(true);
          for (const ev of nar.detailedEvidence) {
            expect(ev.trim()).not.toBe(nar.actionTitle.trim());
            expect(ev.trim()).not.toBe(nar.conciseRationale.trim());
          }
        }
        for (const g of givenQuantitiesSummary(scene, scene.events.length - 1)) {
          expect(g.text.length).toBeGreaterThan(0);
        }
        for (const ann of annotationsAt(scene, scene.events.length - 1, DEFAULT_ANNOTATION_VIEW, null)) {
          expect(ann.role).toBe("given");
        }
      }
    });

    it("preserves semantic roles, certified relations, and perpendicular witness geometry under object-order permutation, plane normal flip (n -> -n + anchor shift), and uniform scaling (1/4x, 4x)", () => {
      const baseScene = makeHoldoutObliquePrismParallelScene();
      const rawPermuted = {
        schema_version: "1.0",
        coordinate_frame: "right_handed_z_up",
        free_objects: ["Fp", "Ep", "Dp", "F", "E", "D"],
        objects: [
          {
            id: "seg_MN_ob",
            type: "segment3",
            render: "line",
            origin: "derived",
            producer: "intersect_planes",
            depends: ["M", "N"],
            endpoint_ids: ["M", "N"],
            endpoints: [["1/2", "1/2", 2], ["9/2", "1/2", 2]],
            formation_roles: ["DERIVE_INTERSECTION"],
            notation: "MN",
            display_group: ["target"],
          },
          { id: "N", type: "point3", render: "point", origin: "derived", depends: ["E", "Ep"], xyz: ["9/2", "1/2", 2], notation: "N", formation_roles: ["DERIVE_INTERSECTION"], display_group: ["target"] },
          { id: "M", type: "point3", render: "point", origin: "derived", depends: ["D", "Dp"], xyz: ["1/2", "1/2", 2], notation: "M", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], display_group: ["given"] },
          {
            id: "prism_ob",
            type: "solid",
            render: "mesh",
            origin: "derived",
            depends: ["D", "E", "F", "Dp", "Ep", "Fp"],
            vertex_ids: ["D", "E", "F", "Dp", "Ep", "Fp"],
            vertices: [[0, 0, 0], [4, 0, 0], [1, 3, 0], [1, 1, 4], [5, 1, 4], [2, 4, 4]],
            faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]],
            formation_roles: ["CONSTRUCT_SOLID"],
            display_group: ["given"],
          },
          {
            id: "base_def",
            type: "polygon3",
            render: "surface",
            origin: "derived",
            depends: ["D", "E", "F"],
            vertex_ids: ["D", "E", "F"],
            vertices: [[0, 0, 0], [4, 0, 0], [1, 3, 0]],
            surface_role: "BASE_REGION",
            formation_roles: ["CONSTRUCT_BASE"],
            notation: "(DEF)",
            display_group: ["given"],
          },
          { id: "Fp", type: "point3", render: "point", origin: "free", depends: [], xyz: [2, 4, 4], notation: "F'", display_group: ["given"] },
          { id: "Ep", type: "point3", render: "point", origin: "free", depends: [], xyz: [5, 1, 4], notation: "E'", display_group: ["given"] },
          { id: "Dp", type: "point3", render: "point", origin: "free", depends: [], xyz: [1, 1, 4], notation: "D'", display_group: ["given"] },
          { id: "F", type: "point3", render: "point", origin: "free", depends: [], xyz: [1, 3, 0], notation: "F", display_group: ["given"] },
          { id: "E", type: "point3", render: "point", origin: "free", depends: [], xyz: [4, 0, 0], notation: "E", display_group: ["given"] },
          { id: "D", type: "point3", render: "point", origin: "free", depends: [], xyz: [0, 0, 0], notation: "D", display_group: ["given"] },
        ],
        events: [
          { id: "ev0", action: "CREATE", object: "base_def", title: "Dựng mặt đáy (DEF)" },
          { id: "ev1", action: "CREATE", object: "prism_ob", title: "Dựng lăng trụ xiên DEF.D'E'F'" },
          { id: "ev2", action: "CREATE", object: "M", title: "Lấy trung điểm M của cạnh bên DD'" },
          { id: "ev3", action: "CREATE", object: "N", title: "Xác định giao điểm N trên cạnh bên EE'" },
          { id: "ev4", action: "CREATE", object: "seg_MN_ob", title: "Dựng đoạn giao tuyến MN song song với DE" },
        ],
      };
      const permutedScene = prepareScene(rawPermuted);

      const cBase = getSemanticConstructionContract(baseScene);
      const cPerm = getSemanticConstructionContract(permutedScene);
      for (const [id, spec] of cBase.objectsById.entries()) {
        if (id.includes("::")) continue;
        const permSpec = cPerm.objectsById.get(id);
        expect(permSpec?.semanticRole).toBe(spec.semanticRole);
        expect(permSpec?.determinacy).toBe(spec.determinacy);
        expect(permSpec?.verifiedRelations.map((r) => r.kind).sort()).toEqual(
          spec.verifiedRelations.map((r) => r.kind).sort(),
        );
      }

      const baseSphere = makeHoldoutCollinearNormalTangentSphereScene();
      const flippedRaw = {
        schema_version: "1.0",
        coordinate_frame: "right_handed_z_up",
        free_objects: ["I", "mp_R"],
        objects: [
          { id: "I", type: "point3", render: "point", origin: "free", depends: [], xyz: [3, -8, 0], notation: "I", display_group: ["given"] },
          {
            id: "S_ball",
            type: "curved_solid",
            curved_kind: "ball",
            render: "curved_solid",
            origin: "derived",
            depends: ["I"],
            anchor: [3, -8, 0],
            radius_sq: 73,
            formation_roles: ["CONSTRUCT_SOLID"],
            notation: "(S)",
            display_group: ["given"],
          },
          {
            id: "mp_R",
            type: "plane3",
            render: "surface",
            origin: "free",
            depends: [],
            point: [8, 3, 5],
            normal: [-3, 8, 0],
            notation: "(R)",
            display_group: ["given"],
          },
        ],
        events: [
          { id: "ev0", action: "CREATE", object: "I", title: "Xác định tâm I của mặt cầu" },
          { id: "ev1", action: "CREATE", object: "S_ball", title: "Dựng mặt cầu tâm I" },
          { id: "ev2", action: "CREATE", object: "mp_R", title: "Dựng mặt phẳng tiếp diện (R)" },
        ],
      };
      const flippedSphere = prepareScene(flippedRaw);
      const segA = baseSphere.objects.find((o) => o.type === "segment3" && Boolean(o.perpendicular_witness))!;
      const segB = flippedSphere.objects.find((o) => o.type === "segment3" && Boolean(o.perpendicular_witness))!;
      expect(segB.perpendicular_witness?.foot).toEqual(segA.perpendicular_witness?.foot);
      const vARaw = toVec3(segA.perpendicular_witness!.marker!.v!);
      const vBRaw = toVec3(segB.perpendicular_witness!.marker!.v!);
      const vALen = Math.hypot(vARaw[0], vARaw[1], vARaw[2]);
      const vBLen = Math.hypot(vBRaw[0], vBRaw[1], vBRaw[2]);
      const uA = computeOptimalInPlaneWitnessBasis(
        [vARaw[0] / vALen, vARaw[1] / vALen, vARaw[2] / vALen],
        resolveSceneLocalViewRay(baseSphere),
      );
      const uB = computeOptimalInPlaneWitnessBasis(
        [vBRaw[0] / vBLen, vBRaw[1] / vBLen, vBRaw[2] / vBLen],
        resolveSceneLocalViewRay(flippedSphere),
      );
      expect(uB[0]).toBeCloseTo(uA[0], 5);
      expect(uB[1]).toBeCloseTo(uA[1], 5);
      expect(uB[2]).toBeCloseTo(uA[2], 5);

      for (const spec of [
        { scale: 0.25, rSq: "25/16", zCut: "3/4", secRSq: "1" },
        { scale: 4, rSq: 400, zCut: 12, secRSq: 256 },
      ]) {
        const { scale, rSq, zCut, secRSq } = spec;
        const scaledRaw = {
          schema_version: "1.0",
          coordinate_frame: "right_handed_z_up",
          free_objects: ["I", "mp_R"],
          objects: [
            { id: "I", type: "point3", render: "point", origin: "free", depends: [], xyz: [0, 0, 0], notation: "I", display_group: ["given"] },
            {
              id: "S_ball",
              type: "curved_solid",
              curved_kind: "ball",
              render: "curved_solid",
              origin: "derived",
              depends: ["I"],
              anchor: [0, 0, 0],
              radius_sq: rSq,
              formation_roles: ["CONSTRUCT_SOLID"],
              notation: "(S)",
              display_group: ["given"],
            },
            {
              id: "mp_R",
              type: "plane3",
              render: "surface",
              surface_role: "CUTTING_PLANE",
              origin: "free",
              depends: [],
              point: [0, 0, zCut],
              normal: [0, 0, 1],
              notation: "(R)",
              display_group: ["given"],
            },
            {
              id: "C_sec",
              type: "circle3",
              render: "circle",
              surface_role: "SECTION_REGION",
              origin: "derived",
              depends: ["S_ball", "mp_R"],
              center: [0, 0, zCut],
              normal: [0, 0, 1],
              radius_sq: secRSq,
              notation: "(C)",
            },
          ],
          events: [
            { id: "ev0", action: "CREATE", object: "I", title: "Xác định tâm I" },
            { id: "ev1", action: "CREATE", object: "S_ball", title: "Dựng mặt cầu" },
            { id: "ev2", action: "CREATE", object: "mp_R", title: "Dựng mặt phẳng (R)" },
            { id: "ev3", action: "CREATE", object: "C_sec", title: "Dựng giao tuyến (C)" },
          ],
        };
        const scaledScene = prepareScene(scaledRaw);
        const sSeg = scaledScene.objects.find((o) => o.type === "segment3" && Boolean(o.perpendicular_witness))!;
        const sBuilt = buildAtStep(sSeg, scaledScene)!;
        const root = new THREE.Group();
        root.add(sBuilt);
        const defaultCam = new THREE.PerspectiveCamera(40, 1, 0.1, 400);
        defaultCam.position.set(8 * scale, 3 * scale, 6 * scale);
        defaultCam.lookAt(0, 0, 0);
        expect(datCoGocVuong([root], defaultCam, 600)).toBe(1);

        let markerNode: THREE.Line | null = null;
        sBuilt.traverse((ch) => { if (ch.name === `perp_marker:${sSeg.id}`) markerNode = ch as THREE.Line; });
        const gv = (markerNode as unknown as THREE.Line).userData.gocVuongDonVi;
        const edgeCam = new THREE.PerspectiveCamera(40, 1, 0.1, 400);
        edgeCam.position.set(
          gv.foot[0] + gv.u[0] * 10 * scale,
          gv.foot[1] + gv.u[1] * 10 * scale,
          gv.foot[2] + gv.u[2] * 10 * scale,
        );
        edgeCam.lookAt(gv.foot[0], gv.foot[1], gv.foot[2]);
        expect(datCoGocVuong([root], edgeCam, 600)).toBe(0);
      }
    });
  });
});
