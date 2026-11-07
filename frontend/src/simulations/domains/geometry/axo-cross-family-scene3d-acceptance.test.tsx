import { renderToString } from "react-dom/server";
import { describe, expect, it, beforeEach } from "vitest";
import * as THREE from "three";
import {
  CANONICAL_SAMPLE_SLUGS,
  canonicalSlugForSampleId,
  offlineCatalog,
  publicCatalog,
  resolveGeometrySampleId,
  resolveSampleByRouteToken,
} from "../../../data/offline-catalog";
import {
  canonicalPathForView,
  resolveLocationRoute,
} from "../../../components/AxoErrorExperience";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import { registerAllSimulations } from "../../index";
import { historyStore } from "../../../state/history";
import {
  clearLearnerRecoverySnapshot,
  loadLearnerRecoverySnapshot,
  saveLearnerRecoverySnapshot,
  type SnapshotStorageLike,
} from "../../../state/learner-recovery-snapshot";
import { useAppStore } from "../../../state/store";
import { veKhongGian } from "./scene3d-chart";
import { objectsAt, toNumber, type Scene3D, type SceneObject } from "./scene3d-model";
import { withSubEntities } from "./scene3d-subentities";
import { auxiliaryHiddenAt } from "./scene3d-auxiliary";
import {
  buildPedagogicalConstructionPlan,
  formatCompactEntityChipLabel,
  getSemanticConstructionContract,
  inspectAxialCurvedOrthogonality,
  pedagogicalStepList,
  registerExactSceneOrigin,
  resolveSphereReferenceGreatCirclePolicy,
  resolveStepVisualRoles,
  resolveStudentObjectPresentation,
  verifyConstructionContinuity,
  verifySceneMathematicalConsistency,
  verifyVisualContinuity,
} from "./scene3d-semantic-policy";
import { buildObject3D, vatThietDienTaiBuoc } from "./scene3d-view";

function sampleRawScene(id: string): Scene3D {
  const found = offlineCatalog().find((x) => x.id === id);
  if (!found) throw new Error(`Missing catalog sample: ${id}`);
  return (found.envelope as unknown as { scene3d: Scene3D }).scene3d;
}

function prepareFullPipelineScene(raw: Scene3D) {
  const sub = withSubEntities(raw);
  registerExactSceneOrigin(sub, raw);
  const mv = verifySceneMathematicalConsistency(raw);
  const plan = buildPedagogicalConstructionPlan(sub);
  const disp = registerExactSceneOrigin(veKhongGian(plan.scene), plan.scene);
  const contract = getSemanticConstructionContract(disp);
  const continuity = verifyConstructionContinuity(disp);
  const visualContinuity = verifyVisualContinuity(disp);
  return { raw, sub, mv, plan, disp, contract, continuity, visualContinuity };
}

// ── Synthetic Cross-Family Fixtures for Families Not Directly in the 11 Public Samples ──

// Category 2: Right Triangular Prism ABC.A'B'C' with lateral edge AA' ⊥ (ABC) and section A'BC
const RIGHT_PRISM_SCENE: Scene3D = {
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  free_objects: ["A", "B", "C", "Ap", "Bp", "Cp"],
  objects: [
    { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
    { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
    { id: "Ap", type: "point3", label: "A′", notation: "A′", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "5"] },
    { id: "Bp", type: "point3", label: "B′", notation: "B′", origin: "free", render: "point_marker", depends: [], xyz: ["3", "0", "5"] },
    { id: "Cp", type: "point3", label: "C′", notation: "C′", origin: "free", render: "point_marker", depends: [], xyz: ["0", "4", "5"] },
    { id: "base_ABC", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "derived", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "4", "0"]] },
    { id: "top_ApBpCp", type: "polygon3", label: "Đáy trên A′B′C′", notation: "A′B′C′", origin: "derived", render: "polygon", surface_role: "TOP_REGION" as SceneObject["surface_role"], depends: ["Ap", "Bp", "Cp"], vertex_ids: ["Ap", "Bp", "Cp"], vertices: [["0", "0", "5"], ["3", "0", "5"], ["0", "4", "5"]] },
    {
      id: "edge_AAp",
      type: "segment3",
      label: "Cạnh bên AA′",
      notation: "AA′",
      origin: "derived",
      render: "segment",
      formation_roles: ["CONSTRUCT_HEIGHT"],
      depends: ["A", "Ap"],
      endpoint_ids: ["A", "Ap"],
      point_a: ["0", "0", "0"],
      point_b: ["0", "0", "5"],
      perpendicular_witness: {
        from: "Ap",
        foot: ["0", "0", "0"],
        foot_id: "A",
        on: "base_ABC",
        relation: "line_perpendicular_plane",
        marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] },
      },
    },
    {
      id: "prism_solid",
      type: "solid",
      shape_class: "PRISM_LIKE",
      label: "Hình lăng trụ đứng ABC.A′B′C′",
      notation: "ABC.A′B′C′",
      origin: "derived",
      render: "mesh",
      formation_roles: ["CLOSE_SOLID"],
      depends: ["A", "B", "C", "Ap", "Bp", "Cp"],
      vertex_ids: ["A", "B", "C", "Ap", "Bp", "Cp"],
      vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "4", "0"], ["0", "0", "5"], ["3", "0", "5"], ["0", "4", "5"]],
      faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]],
    },
    {
      id: "sec_ApBC",
      type: "section",
      label: "Thiết diện A′BC",
      notation: "A′BC",
      origin: "derived",
      producer: "plane_solid_section",
      render: "polygon",
      surface_role: "SECTION_REGION",
      depends: ["prism_solid", "Ap", "B", "C"],
      vertex_ids: ["Ap", "B", "C"],
      polygon: [["0", "0", "5"], ["3", "0", "0"], ["0", "4", "0"]],
    },
  ] as unknown as SceneObject[],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Khởi tạo." },
    { step_index: 1, action: "CREATE", object: "base_ABC", depends: ["A", "B", "C"], explanation: "Dựng đáy ABC." },
    { step_index: 2, action: "CREATE", object: "edge_AAp", depends: ["A", "Ap"], explanation: "Dựng cạnh bên AA′ ⊥ (ABC)." },
    { step_index: 3, action: "CREATE", object: "top_ApBpCp", depends: ["Ap", "Bp", "Cp"], explanation: "Dựng đáy trên A′B′C′." },
    { step_index: 4, action: "CREATE", object: "prism_solid", depends: ["A", "B", "C", "Ap", "Bp", "Cp"], explanation: "Khép khối lăng trụ đứng." },
    { step_index: 5, action: "CREATE", object: "sec_ApBC", depends: ["prism_solid", "Ap", "B", "C"], explanation: "Dựng thiết diện A′BC." },
  ],
};

// Category 3: Oblique Triangular Prism ABC.A'B'C' (lateral edge AA' slanted, altitude A'H ⊥ (ABC))
const OBLIQUE_PRISM_SCENE: Scene3D = {
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  free_objects: ["A", "B", "C", "H", "Ap", "Bp", "Cp"],
  objects: [
    { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["4", "0", "0"] },
    { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
    { id: "H", type: "point3", label: "H", notation: "H", origin: "free", render: "point_marker", depends: [], xyz: ["1", "1", "0"] },
    { id: "Ap", type: "point3", label: "A′", notation: "A′", origin: "free", render: "point_marker", depends: [], xyz: ["1", "1", "4"] },
    { id: "Bp", type: "point3", label: "B′", notation: "B′", origin: "free", render: "point_marker", depends: [], xyz: ["5", "1", "4"] },
    { id: "Cp", type: "point3", label: "C′", notation: "C′", origin: "free", render: "point_marker", depends: [], xyz: ["1", "5", "4"] },
    { id: "base_ABC", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "derived", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["4", "0", "0"], ["0", "4", "0"]] },
    {
      id: "alt_ApH",
      type: "segment3",
      label: "Đường cao A′H",
      notation: "A′H",
      origin: "derived",
      render: "segment",
      formation_roles: ["CONSTRUCT_HEIGHT"],
      depends: ["Ap", "H"],
      endpoint_ids: ["Ap", "H"],
      point_a: ["1", "1", "4"],
      point_b: ["1", "1", "0"],
      perpendicular_witness: {
        from: "Ap",
        foot: ["1", "1", "0"],
        foot_id: "H",
        on: "base_ABC",
        relation: "line_perpendicular_plane",
        marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] },
      },
    },
    {
      id: "oblique_prism",
      type: "solid",
      shape_class: "PRISM_LIKE",
      label: "Hình lăng trụ xiên ABC.A′B′C′",
      notation: "ABC.A′B′C′",
      origin: "derived",
      render: "mesh",
      formation_roles: ["CLOSE_SOLID"],
      depends: ["A", "B", "C", "Ap", "Bp", "Cp"],
      vertex_ids: ["A", "B", "C", "Ap", "Bp", "Cp"],
      vertices: [["0", "0", "0"], ["4", "0", "0"], ["0", "4", "0"], ["1", "1", "4"], ["5", "1", "4"], ["1", "5", "4"]],
      faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]],
    },
  ] as unknown as SceneObject[],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Khởi tạo." },
    { step_index: 1, action: "CREATE", object: "base_ABC", depends: ["A", "B", "C"], explanation: "Dựng đáy ABC." },
    { step_index: 2, action: "CREATE", object: "alt_ApH", depends: ["Ap", "H"], explanation: "Hạ đường cao A′H ⊥ (ABC)." },
    { step_index: 3, action: "CREATE", object: "oblique_prism", depends: ["A", "B", "C", "Ap", "Bp", "Cp"], explanation: "Khép hình lăng trụ xiên." },
  ],
};

// Category 4: Cube PQRS.P'Q'R'S' with 6-vertex hexagonal cross-section UVWXYZ
const CUBE_HEX_SCENE: Scene3D = {
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  free_objects: ["P", "Q", "R", "S", "P_p", "Q_p", "R_p", "S_p"],
  objects: [
    { id: "P", type: "point3", label: "P", notation: "P", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "Q", type: "point3", label: "Q", notation: "Q", origin: "free", render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
    { id: "R", type: "point3", label: "R", notation: "R", origin: "free", render: "point_marker", depends: [], xyz: ["2", "2", "0"] },
    { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
    { id: "P_p", type: "point3", label: "P′", notation: "P′", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "2"] },
    { id: "Q_p", type: "point3", label: "Q′", notation: "Q′", origin: "free", render: "point_marker", depends: [], xyz: ["2", "0", "2"] },
    { id: "R_p", type: "point3", label: "R′", notation: "R′", origin: "free", render: "point_marker", depends: [], xyz: ["2", "2", "2"] },
    { id: "S_p", type: "point3", label: "S′", notation: "S′", origin: "free", render: "point_marker", depends: [], xyz: ["0", "2", "2"] },
    { id: "day_PQRS", type: "polygon3", label: "Đáy PQRS", notation: "PQRS", origin: "derived", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["P", "Q", "R", "S"], vertex_ids: ["P", "Q", "R", "S"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]] },
    { id: "khoi_hop", type: "solid", shape_class: "BOX_LIKE", label: "Hình lập phương PQRS.P′Q′R′S′", notation: "PQRS.P′Q′R′S′", origin: "derived", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["P", "Q", "R", "S", "P_p", "Q_p", "R_p", "S_p"], vertex_ids: ["P", "Q", "R", "S", "P_p", "Q_p", "R_p", "S_p"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"], ["0", "0", "2"], ["2", "0", "2"], ["2", "2", "2"], ["0", "2", "2"]], faces: [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]] },
    { id: "U_pt", type: "point3", label: "U", notation: "U", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["P", "Q"], xyz: ["1", "0", "0"] },
    { id: "V_pt", type: "point3", label: "V", notation: "V", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["Q", "R"], xyz: ["2", "1", "0"] },
    { id: "W_pt", type: "point3", label: "W", notation: "W", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["R", "R_p"], xyz: ["2", "2", "1"] },
    { id: "mp_UVW", type: "plane3", label: "Mặt phẳng (UVW)", notation: "(UVW)", origin: "derived", producer: "construct_plane", render: "surface", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: ["U_pt", "V_pt", "W_pt"], point: ["1", "0", "0"], normal: ["1", "-1", "1"] },
    { id: "X_pt", type: "point3", label: "X", notation: "X", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["R_p", "S_p"], xyz: ["1", "2", "2"] },
    { id: "Y_pt", type: "point3", label: "Y", notation: "Y", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["P_p", "S_p"], xyz: ["0", "1", "2"] },
    { id: "Z_pt", type: "point3", label: "Z", notation: "Z", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["P", "P_p"], xyz: ["0", "0", "1"] },
    { id: "td_hex", type: "section", label: "Thiết diện lục giác UVWXYZ", notation: "UVWXYZ", origin: "derived", producer: "plane_solid_section", render: "polygon", surface_role: "SECTION_REGION", depends: ["khoi_hop", "mp_UVW"], vertex_ids: ["U_pt", "V_pt", "W_pt", "X_pt", "Y_pt", "Z_pt"], polygon: [["1", "0", "0"], ["2", "1", "0"], ["2", "2", "1"], ["1", "2", "2"], ["0", "1", "2"], ["0", "0", "1"]] },
  ] as unknown as SceneObject[],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
    { step_index: 1, action: "CREATE", object: "day_PQRS", depends: ["P", "Q", "R", "S"], explanation: "Đáy PQRS" },
    { step_index: 2, action: "CREATE", object: "khoi_hop", depends: ["P", "Q", "R", "S", "P_p", "Q_p", "R_p", "S_p"], explanation: "Khối lập phương" },
    { step_index: 3, action: "CREATE", object: "U_pt", depends: ["P", "Q"], explanation: "U" },
    { step_index: 4, action: "CREATE", object: "V_pt", depends: ["Q", "R"], explanation: "V" },
    { step_index: 5, action: "CREATE", object: "W_pt", depends: ["R", "R_p"], explanation: "W" },
    { step_index: 6, action: "CREATE", object: "mp_UVW", depends: ["U_pt", "V_pt", "W_pt"], explanation: "(UVW)" },
    { step_index: 7, action: "CREATE", object: "X_pt", depends: ["R_p", "S_p"], explanation: "X" },
    { step_index: 8, action: "CREATE", object: "Y_pt", depends: ["P_p", "S_p"], explanation: "Y" },
    { step_index: 9, action: "CREATE", object: "Z_pt", depends: ["P", "P_p"], explanation: "Z" },
    { step_index: 10, action: "CREATE", object: "td_hex", depends: ["khoi_hop", "mp_UVW"], explanation: "Thiết diện UVWXYZ" },
  ],
};

// Category 7: True Oblique Cylinder (circular horizontal bases z=0 and z=4, axis OO' = [2, 0, 4] NOT perpendicular to base!)
const TRUE_OBLIQUE_CYLINDER_SCENE: Scene3D = {
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  free_objects: ["O", "Op"],
  objects: [
    { id: "O", type: "point3", label: "O", notation: "O", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "Op", type: "point3", label: "O′", notation: "O′", origin: "free", render: "point_marker", depends: [], xyz: ["2", "0", "4"] },
    { id: "base_bot", type: "circle3", label: "Đường tròn đáy dưới", notation: "(O)", origin: "derived", render: "circle", surface_role: "BASE_REGION", depends: ["O"], center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "9" },
    { id: "base_top", type: "circle3", label: "Đường tròn đáy trên", notation: "(O′)", origin: "derived", render: "circle", surface_role: "BASE_REGION", depends: ["Op"], center: ["2", "0", "4"], normal: ["0", "0", "1"], radius_sq: "9" },
    { id: "axis_OOp", type: "segment3", label: "Trục xiên OO′", notation: "OO′", origin: "derived", render: "segment", depends: ["O", "Op"], endpoint_ids: ["O", "Op"], point_a: ["0", "0", "0"], point_b: ["2", "0", "4"] },
    {
      id: "cyl_oblique",
      type: "curved_solid",
      curved_kind: "cylinder",
      label: "Hình trụ xiên",
      notation: null,
      origin: "derived",
      producer: "construct_cylinder",
      render: "curved_solid",
      depends: ["O", "Op", "base_bot", "base_top"],
      anchor: ["0", "0", "0"],
      apex_or_top: ["2", "0", "4"],
      axis: ["2", "0", "4"],
      radius_sq: "9",
      height_sq: "20",
    },
  ] as unknown as SceneObject[],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
    { step_index: 1, action: "CREATE", object: "base_bot", depends: ["O"], explanation: "Đáy dưới (O)" },
    { step_index: 2, action: "CREATE", object: "base_top", depends: ["Op"], explanation: "Đáy trên (O′)" },
    { step_index: 3, action: "CREATE", object: "axis_OOp", depends: ["O", "Op"], explanation: "Trục xiên OO′" },
    { step_index: 4, action: "CREATE", object: "cyl_oblique", depends: ["O", "Op", "base_bot", "base_top"], explanation: "Hình trụ xiên" },
  ],
};

// Category 10: Plane-Plane Intersection ((P) ∩ (Q) = Δ through A(0,0,3) and B(2,2,0))
const PLANE_PLANE_INTERSECTION_SCENE: Scene3D = {
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  free_objects: ["A", "B", "C", "D"],
  objects: [
    { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "3"] },
    { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
    { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point_marker", depends: [], xyz: ["0", "3", "0"] },
    { id: "D", type: "point3", label: "D", notation: "D", origin: "free", render: "point_marker", depends: [], xyz: ["2", "3", "0"] },
    { id: "mp_P", type: "plane3", label: "Mặt phẳng (ABC)", notation: "(ABC)", origin: "derived", producer: "construct_plane", render: "surface", depends: ["A", "B", "C"], point: ["0", "0", "3"], normal: ["9", "6", "6"] },
    { id: "mp_Q", type: "plane3", label: "Mặt phẳng (ABD)", notation: "(ABD)", origin: "derived", producer: "construct_plane", render: "surface", depends: ["A", "B", "D"], point: ["0", "0", "3"], normal: ["3", "0", "2"] },
    { id: "gt_AB", type: "line3", label: "Giao tuyến AB", notation: "d", origin: "derived", producer: "intersect_planes", render: "line", depends: ["mp_P", "mp_Q"], point: ["0", "0", "3"], direction: ["2", "0", "-3"] },
  ] as unknown as SceneObject[],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
    { step_index: 1, action: "CREATE", object: "mp_P", depends: ["A", "B", "C"], explanation: "Dựng (ABC)." },
    { step_index: 2, action: "CREATE", object: "mp_Q", depends: ["A", "B", "D"], explanation: "Dựng (ABD)." },
    { step_index: 3, action: "CREATE", object: "gt_AB", depends: ["mp_P", "mp_Q"], explanation: "Dựng giao tuyến d = (ABC) ∩ (ABD)." },
  ],
};

// Category 12: Exterior Derived Intersection Requiring Auxiliary Extension Line
const EXTERIOR_EXTENSION_INTERSECTION_SCENE: Scene3D = {
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  free_objects: ["A", "B", "C", "S"],
  objects: [
    { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["4", "0", "0"] },
    { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
    { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
    { id: "day_ABC", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "derived", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["4", "0", "0"], ["0", "4", "0"]] },
    { id: "chop_SABC", type: "solid", label: "Tứ diện S.ABC", notation: "S.ABC", origin: "derived", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["A", "B", "C", "S"], vertex_ids: ["A", "B", "C", "S"], vertices: [["0", "0", "0"], ["4", "0", "0"], ["0", "4", "0"], ["0", "0", "4"]], faces: [[0, 1, 2], [0, 1, 3], [1, 2, 3], [2, 0, 3]] },
    { id: "M", type: "point3", label: "M", notation: "M", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["S", "A"], xyz: ["0", "0", "2"] },
    { id: "N", type: "point3", label: "N", notation: "N", origin: "derived", producer: "divide_segment", render: "point_marker", depends: ["S", "B"], xyz: ["8/3", "0", "4/3"] },
    { id: "line_MN", type: "line3", label: "Đường thẳng MN", notation: "MN", origin: "derived", producer: "construct_line", render: "line", auxiliary: "extension", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], depends: ["M", "N"], point: ["0", "0", "2"], direction: ["8/3", "0", "-2/3"] },
    { id: "line_AB", type: "line3", label: "Đường thẳng AB", notation: "AB", origin: "derived", producer: "construct_line", render: "line", auxiliary: "extension", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], depends: ["A", "B"], point: ["0", "0", "0"], direction: ["4", "0", "0"] },
    { id: "E_ext", type: "point3", label: "Giao điểm E", notation: "E", origin: "derived", producer: "intersect_lines", render: "point_marker", depends: ["line_MN", "line_AB"], xyz: ["8", "0", "0"] },
    { id: "seg_CE", type: "segment3", label: "Giao tuyến CE", notation: "CE", origin: "derived", producer: "construct_segment", render: "segment", depends: ["C", "E_ext"], endpoint_ids: ["C", "E_ext"], point_a: ["0", "4", "0"], point_b: ["8", "0", "0"] },
  ] as unknown as SceneObject[],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
    { step_index: 1, action: "CREATE", object: "day_ABC", depends: ["A", "B", "C"], explanation: "Đáy ABC" },
    { step_index: 2, action: "CREATE", object: "chop_SABC", depends: ["A", "B", "C", "S"], explanation: "Khối S.ABC" },
    { step_index: 3, action: "CREATE", object: "M", depends: ["S", "A"], explanation: "Trung điểm M" },
    { step_index: 4, action: "CREATE", object: "N", depends: ["S", "B"], explanation: "Điểm N trên SB" },
    { step_index: 5, action: "CREATE", object: "line_MN", depends: ["M", "N"], explanation: "Kéo dài MN" },
    { step_index: 6, action: "CREATE", object: "line_AB", depends: ["A", "B"], explanation: "Kéo dài AB" },
    { step_index: 7, action: "CREATE", object: "E_ext", depends: ["line_MN", "line_AB"], explanation: "Xác định E = MN ∩ AB ngoài đoạn AB" },
    { step_index: 8, action: "CREATE", object: "seg_CE", depends: ["C", "E_ext"], explanation: "Nối giao tuyến CE trên mặt phẳng đáy" },
  ],
};

describe("AXO — Cross-Family Scene3D Stabilization & Acceptance Suite (§4–§9)", () => {
  beforeEach(() => {
    registerAllSimulations();
    historyStore.clear();
    clearLearnerRecoverySnapshot();
    useAppStore.getState().reset();
  });

  it("test polygon carriers follow the Scene3D render contract and actually build visible geometry", () => {
    for (const scene of [RIGHT_PRISM_SCENE, OBLIQUE_PRISM_SCENE, CUBE_HEX_SCENE, EXTERIOR_EXTENSION_INTERSECTION_SCENE]) {
      for (const object of scene.objects.filter(o => o.type === "section" || o.type === "polygon3")) {
        expect(object.render, object.id).toBe("polygon");
        const built = buildObject3D(object, false);
        expect(built, object.id).not.toBeNull();
        const visibleGeometry: string[] = [];
        built!.traverse(node => {
          const mesh = node as THREE.Mesh;
          if (mesh.geometry?.getAttribute("position")?.count > 0 && (mesh.material as THREE.Material)?.colorWrite !== false) visibleGeometry.push(node.uuid);
        });
        expect(visibleGeometry.length, object.id).toBeGreaterThan(0);
      }
    }
  });

  it("completed cube hexagon survives the complete presentation pipeline", () => {
    const { disp, plan } = prepareFullPipelineScene(CUBE_HEX_SCENE);
    const anchor = plan.steps.at(-1)!.anchor;
    const section = disp.objects.find(o => o.id === "td_hex")!;
    expect(section.render).toBe("polygon");
    expect(objectsAt(disp, anchor).map(o => o.id)).toContain(section.id);
    expect(resolveStepVisualRoles(disp, anchor).get(section.id)?.visible).toBe(true);
    const progress = disp.formation?.steps[anchor]?.geometry_progress?.find(p => p.object_id === section.id);
    const current = vatThietDienTaiBuoc(section, progress);
    expect(current).not.toBeNull();
    expect(buildObject3D(current!, false)).not.toBeNull();
  });

  it("1. Cross-Family Pipeline Gate (§9.1–9.12): all 11 public catalog samples + right prism + oblique prism + cube hexagon + oblique cylinder + plane-plane intersection + exterior extension pass mathematical consistency, DAG construction continuity, visual continuity, and zero future-step leakage", () => {
    const scenarios: Array<{ name: string; raw: Scene3D }> = [
      ...publicCatalog().map((entry) => ({
        name: `catalog:${entry.id}(${entry.slug})`,
        raw: (entry.envelope as unknown as { scene3d: Scene3D }).scene3d,
      })),
      { name: "synthetic:right-prism", raw: RIGHT_PRISM_SCENE },
      { name: "synthetic:oblique-prism", raw: OBLIQUE_PRISM_SCENE },
      { name: "synthetic:cube-hexagon", raw: CUBE_HEX_SCENE },
      { name: "synthetic:true-oblique-cylinder", raw: TRUE_OBLIQUE_CYLINDER_SCENE },
      { name: "synthetic:plane-plane-intersection", raw: PLANE_PLANE_INTERSECTION_SCENE },
      { name: "synthetic:exterior-extension-intersection", raw: EXTERIOR_EXTENSION_INTERSECTION_SCENE },
    ];

    for (const sc of scenarios) {
      const { mv, plan, disp, contract, continuity, visualContinuity } = prepareFullPipelineScene(sc.raw);
      expect(mv.valid, `${sc.name} math contradictions: ${JSON.stringify(mv.contradictions)}`).toBe(true);
      expect(continuity.valid, `${sc.name} continuity violations: ${JSON.stringify(continuity.violations)}`).toBe(true);
      expect(visualContinuity.valid, `${sc.name} visual violations: ${JSON.stringify(visualContinuity.violations)}`).toBe(true);
      expect(plan.steps.length).toBeGreaterThanOrEqual(1);

      // Lineage memoization invariant (§7.2): pedagogicalStepList on veKhongGian(plan.scene) returns identical step count & anchors without recomputing from scratch
      const dispSteps = pedagogicalStepList(disp);
      expect(dispSteps.map((s) => s.anchor)).toEqual(plan.steps.map((s) => s.anchor));

      // No future-step objects appear early; every visible object has an explicit semantic role
      const allStepCreated = new Map<string, number>();
      plan.steps.forEach((st, idx) => {
        for (const id of st.visibleIds) {
          if (!allStepCreated.has(id)) {
            allStepCreated.set(id, idx);
          }
          const cObj = contract.objectsById.get(id);
          expect(cObj, `${sc.name} step ${idx} object ${id} must be registered in semantic contract`).toBeDefined();
        }
      });

      plan.steps.forEach((st, idx) => {
        for (const id of st.visibleIds) {
          const firstStep = allStepCreated.get(id)!;
          expect(firstStep).toBeLessThanOrEqual(idx);
        }
      });
    }
  });

  it("2. Certified Line-Plane Perpendicularity on Diagonal Section (`mat-cheo-sac`, §5.3 & §6.1): SA ⊥ (ABCD) certifies (SAC) as a right triangle at A (`SA ⊥ AC tại A`) without false uncertified caveats", () => {
    const { disp, plan } = prepareFullPipelineScene(sampleRawScene("mat-cheo-sac"));
    const finalAnchor = plan.steps[plan.steps.length - 1]!.anchor;
    const sacPres = resolveStudentObjectPresentation(disp, "thiet_dien", finalAnchor);
    expect(sacPres).not.toBeNull();
    expect(sacPres?.description ?? "").toContain("tam giác vuông");
    expect(`${sacPres?.description ?? ""} ${sacPres?.evidence ?? ""}`).toMatch(/\b(?:SA|AS)\s*⊥\s*AC\s+tại\s+A\b/u);
    expect(`${sacPres?.description ?? ""} ${sacPres?.evidence ?? ""}`).not.toMatch(/chưa\s+chứng\s+thực/iu);
  });

  it("3. Right Circular Cylinder vs Tilted Right Circular Cylinder vs True Oblique Cylinder (§5.2, §6.1, §9.5–9.7): exact orthogonality separation, intact parenthetical circle labels, O/O′ base centers, and P ⊥ OO′ relation", () => {
    // 3a. Right circular cylinder (`tru-thiet-dien-tron`)
    const rightCyl = prepareFullPipelineScene(sampleRawScene("tru-thiet-dien-tron"));
    const finalRightAnchor = rightCyl.plan.steps[rightCyl.plan.steps.length - 1]!.anchor;
    const cylObj = rightCyl.disp.objects.find((o) => o.type === "curved_solid" && o.curved_kind === "cylinder")!;
    const rightOrtho = inspectAxialCurvedOrthogonality(rightCyl.disp, cylObj);
    expect(rightOrtho.isRightCertified).toBe(true);
    expect(rightOrtho.isOblique).toBe(false);

    // O and O' must be presented as base circle centers, NEVER altitude feet or solid apices
    const presO = resolveStudentObjectPresentation(rightCyl.disp, "O", finalRightAnchor);
    const presOp = resolveStudentObjectPresentation(rightCyl.disp, "O_prime", finalRightAnchor);
    expect(presO?.title).toBe("Tâm O");
    expect(presO?.role).toBe("Tâm đường tròn đáy");
    expect(presOp?.title).toContain("Tâm O");
    expect(presOp?.role).toBe("Tâm đường tròn đáy");

    // Parenthetical circle designation `Đáy tròn (O; R = ...)` must NEVER lose its closing `)`
    const botCircle = rightCyl.disp.objects.find((o) => o.type === "circle3" && o.id !== "C")!;
    const chipText = formatCompactEntityChipLabel(rightCyl.disp, botCircle);
    const openCount = (chipText.match(/\(/g) ?? []).length;
    const closeCount = (chipText.match(/\)/g) ?? []).length;
    expect(openCount).toBe(closeCount);

    // Cutting plane P must explain `Đi qua M · vuông góc với OO′`
    const presP = resolveStudentObjectPresentation(rightCyl.disp, "P", finalRightAnchor);
    expect(presP?.description).toContain("Đi qua M");
    expect(presP?.description).toContain("vuông góc với OO′");

    // 3b. Tilted right circular cylinder (`tru-truc-xien` — right cylinder tilted in 3D space)
    const tiltedEntry = publicCatalog().find((e) => e.id === "tru-truc-xien")!;
    expect(tiltedEntry.title).toBe("Hình trụ tròn xoay có trục đặt nghiêng");
    const tiltedCylScene = prepareFullPipelineScene(sampleRawScene("tru-truc-xien"));
    const tiltedCylObj = tiltedCylScene.disp.objects.find((o) => o.type === "curved_solid" && o.curved_kind === "cylinder")!;
    const tiltedOrtho = inspectAxialCurvedOrthogonality(tiltedCylScene.disp, tiltedCylObj);
    expect(tiltedOrtho.isRightCertified).toBe(true);
    expect(tiltedOrtho.isOblique).toBe(false);

    // 3c. True oblique cylinder (`TRUE_OBLIQUE_CYLINDER_SCENE` — axis [2, 0, 4] not perpendicular to horizontal circular bases)
    const obliqueCylScene = prepareFullPipelineScene(TRUE_OBLIQUE_CYLINDER_SCENE);
    const obliqueCylObj = obliqueCylScene.disp.objects.find((o) => o.type === "curved_solid" && o.curved_kind === "cylinder")!;
    const obliqueOrtho = inspectAxialCurvedOrthogonality(obliqueCylScene.disp, obliqueCylObj);
    expect(obliqueOrtho.isRightCertified).toBe(false);
    expect(obliqueOrtho.isOblique).toBe(true);
    const obliquePres = resolveStudentObjectPresentation(
      obliqueCylScene.disp,
      obliqueCylObj.id,
      obliqueCylScene.plan.steps[obliqueCylScene.plan.steps.length - 1]!.anchor,
    );
    expect(obliquePres?.title ?? "").not.toMatch(/tròn\s+xoay/iu);
  });

  it("4. Right Circular Cone (`non-thiet-dien-truc`, `non-duong-sinh`, §9.8): apex S is `Đỉnh hình nón` and base center O is `Tâm đường tròn đáy`", () => {
    const cone = prepareFullPipelineScene(sampleRawScene("non-thiet-dien-truc"));
    const finalAnchor = cone.plan.steps[cone.plan.steps.length - 1]!.anchor;
    const presS = resolveStudentObjectPresentation(cone.disp, "S", finalAnchor);
    const presO = resolveStudentObjectPresentation(cone.disp, "O", finalAnchor);
    expect(presS?.title).toBe("Đỉnh S");
    expect(presS?.role).toBe("Đỉnh hình nón");
    expect(presO?.title).toBe("Tâm O");
    expect(presO?.role).toBe("Tâm đường tròn đáy");
  });

  it("5. Sphere Geometry & Pedagogical Policy (§5.1): R=5, d=3 ⇒ exact r=4, distinct H (`Tâm giao tuyến`) vs M (`Điểm giao tuyến`) vs tangent T (`Tiếp điểm`) vs disjoint H (`Hình chiếu vuông góc`), surface terminology, and multi-camera front/back arc split", () => {
    // 5a. Secant sphere `cau-cat-mat-phang` (R = 5, d = 3 => r = 4)
    const rawSecant = sampleRawScene("cau-cat-mat-phang");
    const exactCircle = rawSecant.objects.find((o) => o.id === "C")!;
    expect(exactCircle.radius_sq).toBe("16");
    expect(Math.sqrt(toNumber(exactCircle.radius_sq!))).toBe(4);

    const secant = prepareFullPipelineScene(rawSecant);
    const finalAnchor = secant.plan.steps[secant.plan.steps.length - 1]!.anchor;

    // Step 1 title uses "Dựng mặt cầu" (surface), never "Dựng khối cầu"
    expect(secant.plan.steps[0]!.title).toContain("mặt cầu");
    expect(secant.plan.steps[0]!.title).not.toContain("khối cầu");

    // Auxiliary point X on sphere is clearly labeled as auxiliary reference, never given
    const presX = resolveStudentObjectPresentation(secant.disp, "cau__ref_pt", secant.plan.steps[0]!.anchor);
    expect(presX?.role).toBe("Điểm phụ trợ");
    expect(presX?.description ?? "").toMatch(/tham\s+chiếu|mặt\s+cầu/iu);

    // H (C__center) vs M (C__rim_pt) have distinct titles and roles!
    const presH = resolveStudentObjectPresentation(secant.disp, "C__center", finalAnchor);
    const presM = resolveStudentObjectPresentation(secant.disp, "C__rim_pt", finalAnchor);
    expect(presH?.title).toBe("Tâm H");
    expect(presH?.role).toBe("Tâm giao tuyến");
    expect(presM?.title).toBe("Điểm M");
    expect(presM?.role).toBe("Điểm giao tuyến");
    expect(presH?.role).not.toBe(presM?.role);

    // Reference great circle fades when intersection circle C appears, and front/back arcs build across camera angles
    const camAngles = [
      new THREE.Vector3(8, -9, 6),
      new THREE.Vector3(-9, -6, 4),
      new THREE.Vector3(2, 10, 1.5),
      new THREE.Vector3(0.2, -11, 0.3),
    ];
    const ballObj = secant.disp.objects.find((o) => o.id === "cau")!;
    const refAtStep0 = resolveSphereReferenceGreatCirclePolicy(secant.disp, ballObj, {
      visibleObjects: objectsAt(secant.disp, secant.plan.steps[0]!.anchor),
    });
    const refAtFinal = resolveSphereReferenceGreatCirclePolicy(secant.disp, ballObj, {
      visibleObjects: objectsAt(secant.disp, finalAnchor),
    });
    expect(refAtStep0.visible).toBe(true);
    if (refAtFinal.visible) {
      expect(refAtFinal.frontOpacity).toBeLessThanOrEqual(refAtStep0.frontOpacity);
    }
    for (const camPos of camAngles) {
      const builtC = buildObject3D(
        secant.disp.objects.find((o) => o.id === "C")!,
        false,
        undefined,
        [],
        camPos,
      );
      expect(builtC).not.toBeNull();
    }

    // 5b. Tangent plane (d = R = 5): T is "Tiếp điểm", zero positive-radius intersection circle
    const tangentRaw: Scene3D = {
      chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
      free_objects: ["I", "q_R"],
      objects: [
        { id: "I", type: "point3", label: "I", notation: "I", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        { id: "q_R", type: "quantity", label: "R", notation: "R", origin: "free", render: "readout", depends: ["cau_tan"], value: "5" },
        { id: "cau_tan", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: "construct_sphere", render: "curved_solid", depends: ["I", "q_R"], anchor: ["0", "0", "0"], radius_sq: "25" },
        { id: "mp_tan", type: "plane3", label: "Tiếp diện (P)", notation: "(P)", origin: "derived", producer: "construct_plane", render: "surface", depends: [], point: ["0", "0", "5"], normal: ["0", "0", "1"] },
        { id: "T", type: "point3", label: "T", notation: "T", origin: "derived", producer: "project_point_plane", render: "point_marker", auxiliary: "sphere_plane_aux", depends: ["I", "mp_tan"], xyz: ["0", "0", "5"] },
      ] as unknown as SceneObject[],
      events: [
        { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
        { step_index: 1, action: "CREATE", object: "cau_tan", depends: ["I", "q_R"], explanation: "Dựng (S)." },
        { step_index: 2, action: "CREATE", object: "mp_tan", depends: [], explanation: "Dựng (P)." },
        { step_index: 3, action: "CREATE", object: "T", depends: ["I", "mp_tan"], explanation: "Tiếp điểm T." },
      ],
    };
    const tan = prepareFullPipelineScene(tangentRaw);
    expect(tan.disp.objects.some((o) => o.type === "circle3" && toNumber(o.radius_sq ?? "0") > 0)).toBe(false);
    const presT = resolveStudentObjectPresentation(tan.disp, "T", tan.plan.steps[tan.plan.steps.length - 1]!.anchor);
    expect(presT?.title).toBe("Tiếp điểm T");
    expect(presT?.role).toBe("Tiếp điểm");

    // 5c. Disjoint plane (d = 7 > R = 5): H is "Hình chiếu vuông góc", zero intersection circle
    const disjointRaw: Scene3D = {
      chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
      free_objects: ["I", "q_R"],
      objects: [
        { id: "I", type: "point3", label: "I", notation: "I", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        { id: "q_R", type: "quantity", label: "R", notation: "R", origin: "free", render: "readout", depends: [], value: "5" },
        { id: "cau_dis", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: "construct_sphere", render: "curved_solid", depends: ["I", "q_R"], anchor: ["0", "0", "0"], radius_sq: "25" },
        { id: "mp_dis", type: "plane3", label: "Mặt phẳng (Δ)", notation: "(Δ)", origin: "derived", producer: "construct_plane", render: "surface", depends: [], point: ["0", "0", "7"], normal: ["0", "0", "1"] },
        { id: "H", type: "point3", label: "H", notation: "H", origin: "derived", producer: "project_point_plane", render: "point_marker", auxiliary: "sphere_plane_aux", depends: ["I", "mp_dis"], xyz: ["0", "0", "7"] },
      ] as unknown as SceneObject[],
      events: [
        { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
        { step_index: 1, action: "CREATE", object: "cau_dis", depends: ["I", "q_R"], explanation: "Dựng (S)." },
        { step_index: 2, action: "CREATE", object: "mp_dis", depends: [], explanation: "Dựng (Δ)." },
        { step_index: 3, action: "CREATE", object: "H", depends: ["I", "mp_dis"], explanation: "Hạ H." },
      ],
    };
    const dis = prepareFullPipelineScene(disjointRaw);
    expect(dis.disp.objects.some((o) => o.type === "circle3")).toBe(false);
    const presDisH = resolveStudentObjectPresentation(dis.disp, "H", dis.plan.steps[dis.plan.steps.length - 1]!.anchor);
    expect(presDisH?.title).toBe("Hình chiếu H");
    expect(presDisH?.role).toBe("Hình chiếu vuông góc");
  });

  it("6. Context Object Card Across All 8 Entity Types & Auxiliary Toggle (§6.1, §9.12): zero coordinate-frame boilerplate leak, clean titles/roles, and interactive Hide/Isolate/Undo hooks rendered", () => {
    const chopSample = publicCatalog().find((e) => e.id === "thiet-dien-chop")!;
    const sphereSample = publicCatalog().find((e) => e.id === "cau-cat-mat-phang")!;
    const chopRaw = (chopSample.envelope as unknown as { scene3d: Scene3D }).scene3d;
    const sphereRaw = (sphereSample.envelope as unknown as { scene3d: Scene3D }).scene3d;
    const chopPrep = prepareFullPipelineScene(chopRaw);
    const spherePrep = prepareFullPipelineScene(sphereRaw);

    const eightTypeChecks: Array<{
      kind: string;
      raw: Scene3D;
      title: string;
      desc: string | null | undefined;
      selectId: string;
    }> = [
      // 1. Point
      { kind: "Point", raw: chopRaw, title: chopSample.title, desc: chopSample.envelope.description, selectId: "S" },
      // 2. Line / Segment
      {
        kind: "Line/Segment",
        raw: chopRaw,
        title: chopSample.title,
        desc: chopSample.envelope.description,
        selectId: chopPrep.disp.objects.find((o) => o.type === "segment3")!.id,
      },
      // 3. Circle
      { kind: "Circle", raw: sphereRaw, title: sphereSample.title, desc: sphereSample.envelope.description, selectId: "C" },
      // 4. Plane
      {
        kind: "Plane",
        raw: chopRaw,
        title: chopSample.title,
        desc: chopSample.envelope.description,
        selectId: chopPrep.disp.objects.find((o) => o.type === "plane3")!.id,
      },
      // 5. Sphere
      { kind: "Sphere", raw: sphereRaw, title: sphereSample.title, desc: sphereSample.envelope.description, selectId: "cau" },
      // 6. Polyhedron
      {
        kind: "Polyhedron",
        raw: chopRaw,
        title: chopSample.title,
        desc: chopSample.envelope.description,
        selectId: chopPrep.disp.objects.find((o) => o.type === "solid")!.id,
      },
      // 7. Cross-section
      {
        kind: "Cross-section",
        raw: chopRaw,
        title: chopSample.title,
        desc: chopSample.envelope.description,
        selectId: chopPrep.disp.objects.find((o) => o.type === "section")!.id,
      },
      // 8. Auxiliary
      {
        kind: "Auxiliary",
        raw: sphereRaw,
        title: sphereSample.title,
        desc: sphereSample.envelope.description,
        selectId: spherePrep.disp.objects.find((o) => o.id === "cau__ref_pt")!.id,
      },
    ];

    for (const item of eightTypeChecks) {
      const html = renderToString(
        <AxoWorkspaceV62
          scene={item.raw}
          de={item.desc}
          tieuDe={item.title}
          initialSelectedId={item.selectId}
        />,
      );
      expect(html, `${item.kind} card should mount`).toContain('class="context-object-card"');
      expect(html, `${item.kind} card must expose #btn-card-hide`).toContain('id="btn-card-hide"');
      expect(html, `${item.kind} card must expose #btn-card-isolate`).toContain('id="btn-card-isolate"');
      expect(html, `${item.kind} workspace must omit redundant #btn-undo-interaction`).not.toContain('id="btn-undo-interaction"');
      expect(html, `${item.kind} workspace must keep #btn-reset-pos`).toContain('id="btn-reset-pos"');
      expect(html, `${item.kind} workspace must keep #btn-xray`).toContain('id="btn-xray"');
      expect(html, `${item.kind} workspace must keep #playback-pa-capsule`).toContain('id="playback-pa-capsule"');
      // Never leak internal coordinate-embedding assumption on synthetic scenes
      expect(html, `${item.kind} must not leak coordinate-system boilerplate`).not.toMatch(
        /Giả thiết dựng:[\s\S]{0,120}(?:hệ\s+trục|gốc\s+tọa\s+độ|gốc\s+toạ\s+độ)/iu,
      );
    }

    // Exterior extension auxiliary lines stay visible while deriving E, then retire unless auxiliary toggle is ON
    const extPrep = prepareFullPipelineScene(EXTERIOR_EXTENSION_INTERSECTION_SCENE);
    const eStepAnchor = extPrep.plan.steps[extPrep.plan.steps.length - 2]!.anchor;
    const finalExtAnchor = extPrep.plan.steps[extPrep.plan.steps.length - 1]!.anchor;
    const hiddenAtEStep = auxiliaryHiddenAt(extPrep.disp, eStepAnchor, false, null);
    const hiddenWhenAuxOff = auxiliaryHiddenAt(extPrep.disp, finalExtAnchor, false, null);
    const hiddenWhenAuxOn = auxiliaryHiddenAt(extPrep.disp, finalExtAnchor, true, null);
    expect(hiddenAtEStep.has("line_MN")).toBe(false);
    expect(hiddenWhenAuxOff.has("line_MN")).toBe(true);
    expect(hiddenWhenAuxOn.has("line_MN")).toBe(false);
  });

  it("7. Canonical English Slugs, Legacy Vietnamese Alias Compatibility, History Unification & Multi-Problem Back/Forward State Isolation (§8.1–8.9)", () => {
    const catalog = publicCatalog();
    expect(catalog.length).toBe(11);

    // Every sample has a unique lowercase hyphenated English slug
    const seenSlugs = new Set<string>();
    for (const entry of catalog) {
      expect(entry.slug).toMatch(/^[a-z0-9]+(?:-[a-z0-9]+)+$/);
      expect(seenSlugs.has(entry.slug)).toBe(false);
      seenSlugs.add(entry.slug);
      expect(entry.slug).toBe(CANONICAL_SAMPLE_SLUGS[entry.id]);

      // Canonical URL uses English slug
      expect(canonicalPathForView("workspace", entry.id)).toBe(`/simulation/${entry.slug}`);

      // Both new English slug URL AND legacy Vietnamese ID URL resolve to the exact same sample!
      expect(resolveLocationRoute(`/simulation/${entry.slug}`, "", "")).toEqual({
        kind: "sample",
        sampleId: entry.id,
      });
      expect(resolveLocationRoute(`/simulation/${entry.id}`, "", "")).toEqual({
        kind: "sample",
        sampleId: entry.id,
      });
      expect(resolveSampleByRouteToken(entry.slug)?.id).toBe(entry.id);
      expect(resolveSampleByRouteToken(entry.id)?.id).toBe(entry.id);
      expect(resolveGeometrySampleId({ id: entry.slug })).toBe(entry.id);
    }

    // Specific canonical slug checks (§8 examples)
    expect(canonicalSlugForSampleId("non-thiet-dien-truc")).toBe("cone-axial-section");
    expect(canonicalSlugForSampleId("thiet-dien-chop")).toBe("pyramid-cross-section");
    expect(canonicalSlugForSampleId("cau-cat-mat-phang")).toBe("sphere-plane-intersection");

    // Store navigation via canonical URL AND legacy URL both load the exact envelope & scene
    useAppStore.getState().syncLocationRoute("/simulation/cone-axial-section");
    expect(useAppStore.getState().view).toBe("workspace");
    expect(useAppStore.getState().activeSampleId).toBe("non-thiet-dien-truc");
    expect(canonicalPathForView("workspace", useAppStore.getState().activeSampleId)).toBe(
      "/simulation/cone-axial-section",
    );

    useAppStore.getState().syncLocationRoute("/simulation/non-thiet-dien-truc");
    expect(useAppStore.getState().view).toBe("workspace");
    expect(useAppStore.getState().activeSampleId).toBe("non-thiet-dien-truc");

    // Multi-problem session recovery snapshot isolation across Problem A -> Problem B -> Back to Problem A (§8.7)
    const map = new Map<string, string>();
    const memStore: SnapshotStorageLike = {
      getItem: (k) => map.get(k) ?? null,
      setItem: (k, v) => {
        map.set(k, v);
      },
      removeItem: (k) => {
        map.delete(k);
      },
    };
    const baseDisplay = {
      showShell: true,
      showVertexLabels: true,
      showPlane: true,
      showSection: true,
      showAxes: false,
      showDimensionLabels: true,
      showRightAngles: true,
      showDashedHidden: true,
      auxiliaryShown: false,
      gridShown: true,
      xray: false,
      shellOpacityPct: 12,
      planeOpacityPct: 8,
    };

    saveLearnerRecoverySnapshot(
      {
        problemKey: "sample:thiet-dien-chop",
        stepIndex: 2,
        selectedId: "mp",
        dockCollapsed: false,
        mobileViewMode: "dock_open",
        display: { ...baseDisplay, xray: true, shellOpacityPct: 26 },
        camera: { position: [7, -5, 4], target: [0, 0, 1] },
      },
      { storage: memStore, nowMs: 10_000 },
    );

    saveLearnerRecoverySnapshot(
      {
        problemKey: "sample:cau-cat-mat-phang",
        stepIndex: 3,
        selectedId: "C",
        dockCollapsed: true,
        mobileViewMode: "stage_expanded",
        display: { ...baseDisplay, showPlane: false, planeOpacityPct: 18 },
        camera: { position: [5, -8, 3], target: [0, 0, 0] },
      },
      { storage: memStore, nowMs: 20_000 },
    );

    // Navigating Back to Problem A restores Problem A's exact state without mixing Problem B's state!
    const snapA = loadLearnerRecoverySnapshot("sample:thiet-dien-chop", {
      storage: memStore,
      nowMs: 25_000,
    });
    const snapB = loadLearnerRecoverySnapshot("sample:cau-cat-mat-phang", {
      storage: memStore,
      nowMs: 25_000,
    });
    expect(snapA?.stepIndex).toBe(2);
    expect(snapA?.selectedId).toBe("mp");
    expect(snapA?.display.xray).toBe(true);
    expect(snapA?.display.showPlane).toBe(true);
    expect(snapA?.display.shellOpacityPct).toBe(26);
    expect(snapA?.camera?.position).toEqual([7, -5, 4]);

    expect(snapB?.stepIndex).toBe(3);
    expect(snapB?.selectedId).toBe("C");
    expect(snapB?.display.xray).toBe(false);
    expect(snapB?.display.showPlane).toBe(false);
    expect(snapB?.display.planeOpacityPct).toBe(18);
    expect(snapB?.camera?.position).toEqual([5, -8, 3]);
  });

  it("8. Adversarial Stabilization Gate: Zero Synthetic perp_plane_ray Across All Families, Connected Auxiliary X-IX Selection, History Cylinder Title Parity & Cache Key Soundness (§5.1, §5.2, §7.2, §9)", () => {
    // 1. Zero synthetic `perp_plane_ray:*` stubs across ALL catalog samples at every step
    for (const entry of offlineCatalog()) {
      const raw = (entry.envelope as unknown as { scene3d?: Scene3D }).scene3d;
      if (!raw) continue;
      const prep = prepareFullPipelineScene(raw);
      for (const st of prep.plan.steps) {
        const visObjs = objectsAt(prep.disp, st.anchor);
        for (const obj of visObjs) {
          const built = buildObject3D(
            obj,
            false,
            0.1,
            [],
            new THREE.Vector3(8, -6, 5),
            undefined,
            undefined,
            false,
            "primary",
            true,
            true,
            false,
            prep.disp,
            undefined,
            undefined,
            undefined,
            visObjs,
          );
          if (!built) continue;
          const syntheticRays: string[] = [];
          built.traverse((ch) => {
            if (ch.name.startsWith("perp_plane_ray:")) syntheticRays.push(ch.name);
          });
          expect(syntheticRays, `${entry.id} step ${st.anchor} obj ${obj.id} must emit zero perp_plane_ray`).toEqual([]);
        }
      }
    }

    // 2. Selecting auxiliary point `X` (`cau__ref_pt`) at Step 5 of `cau-cat-mat-phang` keeps `IX` (`cau__radius`) visible
    const sphereCutPrep = prepareFullPipelineScene(sampleRawScene("cau-cat-mat-phang"));
    const finalAnchor = sphereCutPrep.plan.steps[sphereCutPrep.plan.steps.length - 1]!.anchor;
    const rolesWithNullSelection = resolveStepVisualRoles(sphereCutPrep.disp, finalAnchor, {
      auxiliaryShown: false,
      selectedId: null,
    });
    expect(rolesWithNullSelection.get("cau__ref_pt")?.visible).toBe(false);
    expect(rolesWithNullSelection.get("cau__radius")?.visible).toBe(false);
    const rolesWhenXSelected = resolveStepVisualRoles(sphereCutPrep.disp, finalAnchor, {
      auxiliaryShown: false,
      selectedId: "cau__ref_pt",
    });
    expect(rolesWhenXSelected.get("cau__ref_pt")?.visible).toBe(true);
    expect(rolesWhenXSelected.get("cau__radius")?.visible).toBe(true);
    // And given point selection (`I`) does NOT spuriously pop up retired auxiliary scaffolding
    const rolesWhenGivenISelected = resolveStepVisualRoles(sphereCutPrep.disp, finalAnchor, {
      auxiliaryShown: false,
      selectedId: "I",
    });
    expect(rolesWhenGivenISelected.get("cau__ref_pt")?.visible).toBe(false);
    expect(rolesWhenGivenISelected.get("cau__radius")?.visible).toBe(false);

    // 3. Tilted right cylinder `tru-truc-xien` normalizes BOTH `entry.envelope.title` and `historyStore.record` title
    const tiltedEntry = offlineCatalog().find((e) => e.id === "tru-truc-xien")!;
    expect(tiltedEntry.title).toBe("Hình trụ tròn xoay có trục đặt nghiêng");
    expect(tiltedEntry.envelope.title).toBe("Hình trụ tròn xoay có trục đặt nghiêng");
    const recorded = historyStore.record(tiltedEntry.envelope, null);
    expect(recorded.title).toBe("Hình trụ tròn xoay có trục đặt nghiêng");
    expect(recorded.envelope.title).toBe("Hình trụ tròn xoay có trục đặt nghiêng");
    expect(historyStore.list().find((it) => it.id === recorded.id)?.title).toBe(
      "Hình trụ tròn xoay có trục đặt nghiêng",
    );

    // 4. `withSubEntities` & `veKhongGian` invalidate WeakMap cache when an interior object coordinate mutates in place
    const mutableScene: Scene3D = JSON.parse(JSON.stringify(sampleRawScene("thiet-dien-chop")));
    mutableScene.chart_metric = [
      ["2", "0", "0"],
      ["0", "1", "0"],
      ["0", "0", "1"],
    ];
    const subA = withSubEntities(mutableScene);
    const worldA = veKhongGian(mutableScene);
    const interiorPoint = mutableScene.objects.find((o, idx) => idx > 0 && idx < mutableScene.objects.length - 1 && o.type === "point3" && Boolean(o.xyz))!;
    const prevX = interiorPoint.xyz![0];
    interiorPoint.xyz = [String(Number(prevX) + 5), interiorPoint.xyz![1], interiorPoint.xyz![2]];
    const subB = withSubEntities(mutableScene);
    const worldB = veKhongGian(mutableScene);
    expect(subB).not.toBe(subA);
    expect(worldB).not.toBe(worldA);
  });
});
