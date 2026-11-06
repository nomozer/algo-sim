import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import { veKhongGian } from "./scene3d-chart";
import { prefersReducedMotion, type Scene3D } from "./scene3d-model";
import { withSubEntities } from "./scene3d-subentities";
import { evaluateStudentPresentationPolicy } from "./scene3d-student-presentation-policy";
import {
  buildPedagogicalConstructionPlan,
  buildStepEntityGroups,
  buildVerifiedObjectTooltip,
  computeProjectedCircleOverlapFactor,
  findLinePlaneIntersectionMidpoint,
  findPointMidpointRelation,
  formatCompactEntityChipLabel,
  pedagogicalStepList,
  registerExactSceneOrigin,
  resolveStepVisualRoles,
  resolveStudentObjectPresentation,
  verifyConstructionContinuity,
  verifySceneMathematicalConsistency,
  verifyVisualContinuity,
} from "./scene3d-semantic-policy";
import {
  COMPACT_MATH_TOKEN_RE,
  MathDisplay,
  SPHERE_FORMATION_DURATION_MS,
  computeClampedCanvasTooltipPosition,
} from "./scene3d-view";

const GLOBAL_CSS = readFileSync(
  new URL("../../../styles/global.css", import.meta.url),
  "utf-8",
);
const SIM_WORKSPACE_SRC = readFileSync(
  new URL("../../../components/SimulationWorkspace.tsx", import.meta.url),
  "utf-8",
);
const EXPLORER_SRC = readFileSync(
  new URL("./Scene3DExplorer.tsx", import.meta.url),
  "utf-8",
);

function sampleRawScene(id: string): Scene3D {
  const found = GEOMETRY_SAMPLES.find((x) => x.id === id);
  if (!found) throw new Error(`Missing sample: ${id}`);
  return (found.envelope as { scene3d?: Scene3D }).scene3d as Scene3D;
}

function prepareScene(raw: Scene3D) {
  const sub = withSubEntities(raw);
  registerExactSceneOrigin(sub, raw);
  const plan = buildPedagogicalConstructionPlan(sub);
  registerExactSceneOrigin(plan.scene, raw);
  return plan;
}

function prepareWorldScene(raw: Scene3D) {
  const plan = prepareScene(raw);
  const worldScene = registerExactSceneOrigin(veKhongGian(plan.scene), plan.scene);
  return { plan, worldScene };
}

const PURE_STANDALONE_SPHERE_SCENE: Scene3D = {
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  free_objects: ["I", "q_R"],
  objects: [
    {
      id: "I",
      type: "point3",
      label: "Tâm I",
      notation: "I",
      origin: "free",
      producer: null,
      render: "point_marker",
      depends: [],
      xyz: ["0", "0", "0"],
    },
    {
      id: "q_R",
      type: "quantity",
      label: "Bán kính R",
      notation: "R",
      origin: "free",
      producer: null,
      render: "readout",
      depends: [],
      value: "4",
      annotation: {
        kind: "radius" as unknown as "length",
        category: "measurement",
        role: "given",
        subject_ids: ["cau_ir"],
        anchor: "solid",
      },
    },
    {
      id: "cau_ir",
      type: "curved_solid",
      curved_kind: "ball",
      label: "Mặt cầu (S)",
      notation: "(S)",
      origin: "derived",
      producer: "construct_sphere",
      render: "curved_solid",
      depends: ["I", "q_R"],
      anchor: ["0", "0", "0"],
      radius_sq: "16",
    },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Đặt tâm I và bán kính R = 4." },
    { step_index: 1, action: "CREATE", object: "cau_ir", depends: ["I", "q_R"], explanation: "Dựng mặt cầu (S) tâm I bán kính R = 4." },
  ],
};

const SPHERE_EXTERNAL_X_SCENE: Scene3D = {
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  free_objects: ["I", "X_ext", "q_R"],
  objects: [
    {
      id: "I",
      type: "point3",
      label: "Tâm I",
      notation: "I",
      origin: "free",
      producer: null,
      render: "point_marker",
      depends: [],
      xyz: ["0", "0", "0"],
    },
    {
      id: "X_ext",
      type: "point3",
      label: "Điểm X",
      notation: "X",
      origin: "free",
      producer: null,
      render: "point_marker",
      depends: [],
      xyz: ["6", "0", "0"],
    },
    {
      id: "q_R",
      type: "quantity",
      label: "Bán kính R",
      notation: "R",
      origin: "free",
      producer: null,
      render: "readout",
      depends: [],
      value: "4",
    },
    {
      id: "ball_x",
      type: "curved_solid",
      curved_kind: "ball",
      label: "Mặt cầu tâm I",
      notation: null,
      origin: "derived",
      producer: "construct_sphere",
      render: "curved_solid",
      depends: ["I", "q_R"],
      anchor: ["0", "0", "0"],
      radius_sq: "16",
    },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Đặt I, điểm ngoài X và bán kính R = 4." },
    { step_index: 1, action: "CREATE", object: "ball_x", depends: ["I", "q_R"], explanation: "Dựng mặt cầu tâm I bán kính R = 4." },
  ],
};

const SPHERE_TANGENT_SCENE: Scene3D = {
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  free_objects: ["I", "q_R"],
  objects: [
    { id: "I", type: "point3", label: "I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "q_R", type: "quantity", label: "R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["cau_tan"], value: "5" },
    { id: "cau_tan", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: "construct_sphere", render: "curved_solid", depends: ["I", "q_R"], anchor: ["0", "0", "0"], radius_sq: "25" },
    { id: "mp_tan", type: "plane3", label: "Tiếp diện (P)", notation: "(P)", origin: "derived", producer: "construct_plane", render: "surface", depends: [], formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], point: ["3", "0", "4"], normal: ["3", "0", "4"] },
    { id: "T", type: "point3", label: "Tiếp điểm T", notation: "T", origin: "derived", producer: "project_point_plane", render: "point_marker", depends: ["I", "mp_tan"], xyz: ["3", "0", "4"] },
    {
      id: "IT",
      type: "segment3",
      label: "Đoạn vuông góc IT",
      notation: "IT",
      origin: "derived",
      producer: "construct_perpendicular",
      render: "segment",
      depends: ["I", "T", "mp_tan"],
      endpoint_ids: ["I", "T"],
      endpoints: [["0", "0", "0"], ["3", "0", "4"]],
      perpendicular_witness: {
        from: "I",
        foot: ["3", "0", "4"],
        foot_id: "T",
        on: "mp_tan",
        relation: "line_perp_plane",
        status: "DERIVED_VERIFIED",
        plane_directions: [["4", "0", "-3"], ["0", "1", "0"]],
        marker: { u: ["4", "0", "-3"], v: ["-3", "0", "-4"] },
      },
    },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
    { step_index: 1, action: "CREATE", object: "cau_tan", depends: ["I", "q_R"], explanation: "Dựng (S)." },
    { step_index: 2, action: "CREATE", object: "mp_tan", depends: [], explanation: "Dựng (P)." },
    { step_index: 3, action: "CREATE", object: "T", depends: ["I", "mp_tan"], explanation: "Dựng tiếp điểm T." },
    { step_index: 4, action: "CREATE", object: "IT", depends: ["I", "T", "mp_tan"], explanation: "Hạ đoạn vuông góc IT ⊥ (P) tại T." },
  ],
};

const SPHERE_DISJOINT_SCENE: Scene3D = {
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  free_objects: ["I", "q_R"],
  objects: [
    { id: "I", type: "point3", label: "I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "q_R", type: "quantity", label: "R", notation: "R", origin: "free", producer: null, render: "readout", depends: [], value: "5" },
    { id: "cau_dis", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: "construct_sphere", render: "curved_solid", depends: ["I", "q_R"], anchor: ["0", "0", "0"], radius_sq: "25" },
    { id: "mp_dis", type: "plane3", label: "Mặt phẳng (Δ)", notation: "(Δ)", origin: "derived", producer: "construct_plane", render: "surface", depends: [], point: ["0", "0", "7"], normal: ["0", "0", "1"] },
    { id: "H", type: "point3", label: "Hình chiếu H", notation: "H", origin: "derived", producer: "project_point_plane", render: "point_marker", depends: ["I", "mp_dis"], xyz: ["0", "0", "7"] },
    { id: "doan_IH", type: "segment3", label: "IH", notation: "IH", origin: "derived", producer: "construct_segment", render: "segment", depends: ["I", "H"], endpoint_ids: ["I", "H"], point_a: ["0", "0", "0"], point_b: ["0", "0", "7"], perpendicular_witness: { foot: ["0", "0", "7"], foot_id: "H", from: "I", on: "mp_dis", relation: "line_perpendicular_plane", marker: { u: ["1", "0", "0"], v: ["0", "0", "-1"] } } },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
    { step_index: 1, action: "CREATE", object: "cau_dis", depends: ["I", "q_R"], explanation: "Dựng (S)." },
    { step_index: 2, action: "CREATE", object: "mp_dis", depends: [], explanation: "Dựng (Δ)." },
    { step_index: 3, action: "CREATE", object: "H", depends: ["I", "mp_dis"], explanation: "Hạ H." },
    { step_index: 4, action: "CREATE", object: "doan_IH", depends: ["I", "H"], explanation: "Nối IH ⊥ (Δ)." },
  ],
};

const REGULAR_PYRAMID_SECTION_SCENE: Scene3D = {
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  free_objects: ["E", "F", "G", "H", "O", "S"],
  objects: [
    { id: "E", type: "point3", label: "E", notation: "E", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["-2", "-2", "0"] },
    { id: "F", type: "point3", label: "F", notation: "F", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "-2", "0"] },
    { id: "G", type: "point3", label: "G", notation: "G", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "2", "0"] },
    { id: "H", type: "point3", label: "H", notation: "H", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["-2", "2", "0"] },
    { id: "O", type: "point3", label: "O", notation: "O", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "S", type: "point3", label: "S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
    { id: "day_EFGH", type: "polygon3", label: "Đáy EFGH", notation: "EFGH", origin: "derived", producer: null, render: "surface", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["E", "F", "G", "H"], vertex_ids: ["E", "F", "G", "H"], vertices: [["-2", "-2", "0"], ["2", "-2", "0"], ["2", "2", "0"], ["-2", "2", "0"]] },
    { id: "cao_SO", type: "segment3", label: "SO", notation: "SO", origin: "derived", producer: null, render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["S", "O"], endpoint_ids: ["S", "O"], point_a: ["0", "0", "4"], point_b: ["0", "0", "0"], perpendicular_witness: { foot: ["0", "0", "0"], foot_id: "O", from: "S", on: "day_EFGH", relation: "line_perpendicular_plane", marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] } } },
    { id: "khoi_SEFGH", type: "solid", label: "Hình chóp S.EFGH", notation: "S.EFGH", origin: "derived", producer: null, render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["E", "F", "G", "H", "S"], vertex_ids: ["E", "F", "G", "H", "S"], vertices: [["-2", "-2", "0"], ["2", "-2", "0"], ["2", "2", "0"], ["-2", "2", "0"], ["0", "0", "4"]], faces: [[0, 1, 2, 3], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]] },
    { id: "I_pt", type: "point3", label: "I", notation: "I", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["S", "E"], xyz: ["-1", "-1", "2"] },
    { id: "J_pt", type: "point3", label: "J", notation: "J", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["S", "F"], xyz: ["1", "-1", "2"] },
    { id: "K_pt", type: "point3", label: "K", notation: "K", origin: "derived", producer: "divide_segment", render: "point_marker", depends: ["S", "G"], xyz: ["4/3", "4/3", "4/3"] },
    { id: "mp_IJK", type: "plane3", label: "Mặt phẳng (IJK)", notation: "(IJK)", origin: "derived", producer: "construct_plane", render: "surface", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: ["I_pt", "J_pt", "K_pt"], point: ["-1", "-1", "2"], normal: ["0", "2", "7"] },
    { id: "canh_SH", type: "segment3", label: "SH", notation: "SH", origin: "derived", producer: null, render: "segment", depends: ["S", "H"], endpoint_ids: ["S", "H"], point_a: ["0", "0", "4"], point_b: ["-2", "2", "0"] },
    {
      id: "L_pt",
      type: "point3",
      label: "Giao điểm L = SH ∩ (IJK)",
      notation: "L",
      role: "Giao điểm của cạnh bên SH với mặt phẳng cắt (IJK) để khép kín thiết diện",
      origin: "derived",
      producer: "intersect_line_plane",
      render: "point_marker",
      depends: ["canh_SH", "mp_IJK"],
      xyz: ["-4/3", "4/3", "4/3"],
    },
    { id: "td_IJKL", type: "section", label: "Thiết diện IJKL", notation: "IJKL", origin: "derived", producer: "plane_solid_section", render: "surface", surface_role: "SECTION_REGION", depends: ["khoi_SEFGH", "mp_IJK"], vertex_ids: ["I_pt", "J_pt", "K_pt", "L_pt"], polygon: [["-1", "-1", "2"], ["1", "-1", "2"], ["4/3", "4/3", "4/3"], ["-4/3", "4/3", "4/3"]] },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
    { step_index: 1, action: "CREATE", object: "day_EFGH", depends: ["E", "F", "G", "H"], explanation: "Đáy EFGH" },
    { step_index: 2, action: "CREATE", object: "cao_SO", depends: ["S", "O"], explanation: "Đường cao SO" },
    { step_index: 3, action: "CREATE", object: "khoi_SEFGH", depends: ["E", "F", "G", "H", "S"], explanation: "Khối chóp" },
    { step_index: 4, action: "CREATE", object: "I_pt", depends: ["S", "E"], explanation: "Trung điểm I" },
    { step_index: 5, action: "CREATE", object: "J_pt", depends: ["S", "F"], explanation: "Trung điểm J" },
    { step_index: 6, action: "CREATE", object: "K_pt", depends: ["S", "G"], explanation: "Điểm K" },
    { step_index: 7, action: "CREATE", object: "mp_IJK", depends: ["I_pt", "J_pt", "K_pt"], explanation: "Mặt phẳng (IJK)" },
    { step_index: 8, action: "CREATE", object: "canh_SH", depends: ["S", "H"], explanation: "Cạnh SH" },
    { step_index: 9, action: "CREATE", object: "L_pt", depends: ["canh_SH", "mp_IJK"], explanation: "Giao điểm L" },
    { step_index: 10, action: "CREATE", object: "td_IJKL", depends: ["khoi_SEFGH", "mp_IJK"], explanation: "Thiết diện IJKL" },
  ],
};

const CUBE_HEXAGONAL_SECTION_SCENE: Scene3D = {
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  free_objects: ["P", "Q", "R", "S", "P_p", "Q_p", "R_p", "S_p"],
  objects: [
    { id: "P", type: "point3", label: "P", notation: "P", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "Q", type: "point3", label: "Q", notation: "Q", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
    { id: "R", type: "point3", label: "R", notation: "R", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "2", "0"] },
    { id: "S", type: "point3", label: "S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
    { id: "P_p", type: "point3", label: "P′", notation: "P′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "2"] },
    { id: "Q_p", type: "point3", label: "Q′", notation: "Q′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "2"] },
    { id: "R_p", type: "point3", label: "R′", notation: "R′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "2", "2"] },
    { id: "S_p", type: "point3", label: "S′", notation: "S′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "2"] },
    { id: "day_PQRS", type: "polygon3", label: "Đáy PQRS", notation: "PQRS", origin: "derived", producer: null, render: "surface", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["P", "Q", "R", "S"], vertex_ids: ["P", "Q", "R", "S"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]] },
    { id: "canh_PPp", type: "segment3", label: "PP′", notation: "PP′", origin: "derived", producer: null, render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["P", "P_p"], endpoint_ids: ["P", "P_p"], point_a: ["0", "0", "0"], point_b: ["0", "0", "2"], perpendicular_witness: { foot: ["0", "0", "0"], foot_id: "P", from: "P_p", on: "day_PQRS", relation: "line_perpendicular_plane", marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] } } },
    { id: "khoi_hop", type: "solid", label: "Hình lập phương PQRS.P′Q′R′S′", notation: "PQRS.P′Q′R′S′", origin: "derived", producer: null, render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["P", "Q", "R", "S", "P_p", "Q_p", "R_p", "S_p"], vertex_ids: ["P", "Q", "R", "S", "P_p", "Q_p", "R_p", "S_p"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"], ["0", "0", "2"], ["2", "0", "2"], ["2", "2", "2"], ["0", "2", "2"]], faces: [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]] },
    { id: "U_pt", type: "point3", label: "U", notation: "U", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["P", "Q"], xyz: ["1", "0", "0"] },
    { id: "V_pt", type: "point3", label: "V", notation: "V", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["Q", "R"], xyz: ["2", "1", "0"] },
    { id: "W_pt", type: "point3", label: "W", notation: "W", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["R", "R_p"], xyz: ["2", "2", "1"] },
    { id: "mp_UVW", type: "plane3", label: "Mặt phẳng (UVW)", notation: "(UVW)", origin: "derived", producer: "construct_plane", render: "surface", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: ["U_pt", "V_pt", "W_pt"], point: ["1", "0", "0"], normal: ["1", "-1", "1"] },
    { id: "X_pt", type: "point3", label: "X", notation: "X", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["R_p", "S_p"], xyz: ["1", "2", "2"] },
    { id: "Y_pt", type: "point3", label: "Y", notation: "Y", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["P_p", "S_p"], xyz: ["0", "1", "2"] },
    { id: "Z_pt", type: "point3", label: "Z", notation: "Z", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["P", "P_p"], xyz: ["0", "0", "1"] },
    { id: "td_hex", type: "section", label: "Thiết diện lục giác UVWXYZ", notation: "UVWXYZ", origin: "derived", producer: "plane_solid_section", render: "surface", surface_role: "SECTION_REGION", depends: ["khoi_hop", "mp_UVW"], vertex_ids: ["U_pt", "V_pt", "W_pt", "X_pt", "Y_pt", "Z_pt"], polygon: [["1", "0", "0"], ["2", "1", "0"], ["2", "2", "1"], ["1", "2", "2"], ["0", "1", "2"], ["0", "0", "1"]] },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
    { step_index: 1, action: "CREATE", object: "day_PQRS", depends: ["P", "Q", "R", "S"], explanation: "Đáy PQRS" },
    { step_index: 2, action: "CREATE", object: "canh_PPp", depends: ["P", "P_p"], explanation: "Cạnh bên PP′" },
    { step_index: 3, action: "CREATE", object: "khoi_hop", depends: ["P", "Q", "R", "S", "P_p", "Q_p", "R_p", "S_p"], explanation: "Khối lập phương" },
    { step_index: 4, action: "CREATE", object: "U_pt", depends: ["P", "Q"], explanation: "U" },
    { step_index: 5, action: "CREATE", object: "V_pt", depends: ["Q", "R"], explanation: "V" },
    { step_index: 6, action: "CREATE", object: "W_pt", depends: ["R", "R_p"], explanation: "W" },
    { step_index: 7, action: "CREATE", object: "mp_UVW", depends: ["U_pt", "V_pt", "W_pt"], explanation: "(UVW)" },
    { step_index: 8, action: "CREATE", object: "X_pt", depends: ["R_p", "S_p"], explanation: "X" },
    { step_index: 9, action: "CREATE", object: "Y_pt", depends: ["P_p", "S_p"], explanation: "Y" },
    { step_index: 10, action: "CREATE", object: "Z_pt", depends: ["P", "P_p"], explanation: "Z" },
    { step_index: 11, action: "CREATE", object: "td_hex", depends: ["khoi_hop", "mp_UVW"], explanation: "Thiết diện UVWXYZ" },
  ],
};

const TRIANGULAR_PRISM_SCENE: Scene3D = {
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  free_objects: ["A", "B", "C", "A_p", "B_p", "C_p"],
  objects: [
    { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
    { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
    { id: "A_p", type: "point3", label: "A′", notation: "A′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "3"] },
    { id: "B_p", type: "point3", label: "B′", notation: "B′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "3"] },
    { id: "C_p", type: "point3", label: "C′", notation: "C′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "3"] },
    { id: "day_ABC", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "derived", producer: null, render: "surface", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]] },
    { id: "canh_AAp", type: "segment3", label: "AA′", notation: "AA′", origin: "derived", producer: null, render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["A", "A_p"], endpoint_ids: ["A", "A_p"], point_a: ["0", "0", "0"], point_b: ["0", "0", "3"], perpendicular_witness: { foot: ["0", "0", "0"], foot_id: "A", from: "A_p", on: "day_ABC", relation: "line_perpendicular_plane", marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] } } },
    { id: "day_ApBpCp", type: "polygon3", label: "Đáy A′B′C′", notation: "A′B′C′", origin: "derived", producer: null, render: "surface", formation_roles: ["CONSTRUCT_TRANSLATED_FACE"], depends: ["A_p", "B_p", "C_p"], vertex_ids: ["A_p", "B_p", "C_p"], vertices: [["0", "0", "3"], ["2", "0", "3"], ["0", "2", "3"]] },
    { id: "khoi_lt", type: "solid", label: "Lăng trụ ABC.A′B′C′", notation: "ABC.A′B′C′", origin: "derived", producer: null, render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["A", "B", "C", "A_p", "B_p", "C_p"], vertex_ids: ["A", "B", "C", "A_p", "B_p", "C_p"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"], ["0", "0", "3"], ["2", "0", "3"], ["0", "2", "3"]], faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]] },
    { id: "M_lt", type: "point3", label: "M", notation: "M", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["A", "A_p"], xyz: ["0", "0", "3/2"] },
    { id: "mp_MBC", type: "plane3", label: "Mặt phẳng (MBC)", notation: "(MBC)", origin: "derived", producer: "construct_plane", render: "surface", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: ["M_lt", "B", "C"], point: ["0", "0", "3/2"], normal: ["3", "3", "4"] },
    { id: "td_MBC", type: "section", label: "Thiết diện MBC", notation: "MBC", origin: "derived", producer: "plane_solid_section", render: "surface", surface_role: "SECTION_REGION", depends: ["khoi_lt", "mp_MBC"], vertex_ids: ["M_lt", "B", "C"], polygon: [["0", "0", "3/2"], ["2", "0", "0"], ["0", "2", "0"]] },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
    { step_index: 1, action: "CREATE", object: "day_ABC", depends: ["A", "B", "C"], explanation: "Đáy ABC" },
    { step_index: 2, action: "CREATE", object: "canh_AAp", depends: ["A", "A_p"], explanation: "Cạnh bên AA′" },
    { step_index: 3, action: "CREATE", object: "day_ApBpCp", depends: ["A_p", "B_p", "C_p"], explanation: "Đáy trên A′B′C′" },
    { step_index: 4, action: "CREATE", object: "khoi_lt", depends: ["A", "B", "C", "A_p", "B_p", "C_p"], explanation: "Khối lăng trụ" },
    { step_index: 5, action: "CREATE", object: "M_lt", depends: ["A", "A_p"], explanation: "Trung điểm M" },
    { step_index: 6, action: "CREATE", object: "mp_MBC", depends: ["M_lt", "B", "C"], explanation: "Mặt phẳng (MBC)" },
    { step_index: 7, action: "CREATE", object: "td_MBC", depends: ["khoi_lt", "mp_MBC"], explanation: "Thiết diện MBC" },
  ],
};

describe("AXO — System-Wide UI/UX Hardening & Final Pedagogical Presentation Audit (§3–§8)", () => {
  it("§8.1, §8.3, §8.4 — Standardizes geometric object presentation contract (title, concise categorical role, non-duplicating description, math-preserving evidence) across X, IX, sphere, (H; HM), IH, SO, EG, L, and sections", () => {
    const spherePlan = prepareScene(sampleRawScene("cau-cat-mat-phang"));
    const step0 = spherePlan.steps[0]!;
    const finalAnchor = spherePlan.steps[spherePlan.steps.length - 1]!.anchor;

    // 1. Mandatory repro object: Điểm tham chiếu X
    const presX = resolveStudentObjectPresentation(spherePlan.scene, "cau__ref_pt", step0.anchor);
    expect(presX).not.toBeNull();
    expect(presX!.title).toBe("Điểm tham chiếu X");
    expect(presX!.role).toBe("Điểm phụ trợ");
    expect(presX!.role.length).toBeLessThanOrEqual(26);
    expect(presX!.description).toBe("X thuộc mặt cầu tâm I, dùng để biểu diễn bán kính IX = R.");
    expect(presX!.description).not.toBe(presX!.title);
    expect(presX!.description).not.toBe(presX!.role);

    // 2. Reference radius IX
    const presIX = resolveStudentObjectPresentation(spherePlan.scene, "cau__radius", step0.anchor);
    expect(presIX).not.toBeNull();
    expect(presIX!.title).toMatch(/Bán kính.*IX/u);
    expect(presIX!.role).toBe("Bán kính tham chiếu");
    expect(presIX!.role.length).toBeLessThanOrEqual(26);
    expect(presIX!.description).not.toBe(presIX!.role);
    expect(presIX!.description).not.toBe(presIX!.title);

    // 3. Sphere solid without invented (S) when notation is null
    const presSphere = resolveStudentObjectPresentation(spherePlan.scene, "cau", step0.anchor);
    expect(presSphere).not.toBeNull();
    expect(presSphere!.title).toBe("Mặt cầu tâm I");
    expect(presSphere!.title).not.toContain("(S)");
    expect(presSphere!.role).toBe("Mặt cầu");
    expect(presSphere!.description).not.toBe(presSphere!.role);

    // 4. Intersection circle (H; HM) uses canonical designation instead of legacy raw "(S)"
    const presCircle = resolveStudentObjectPresentation(spherePlan.scene, "C", finalAnchor);
    expect(presCircle).not.toBeNull();
    expect(presCircle!.title).toBe("Đường tròn (H; HM)");
    expect(presCircle!.role).toBe("Giao tuyến tròn");
    expect(presCircle!.description).not.toContain("(S)");
    expect(presCircle!.description).not.toBe(presCircle!.role);

    // 5. Distance segment IH is "Đoạn vuông góc IH" (NOT mislabeled as "Đường cao IH")
    const presIH = resolveStudentObjectPresentation(spherePlan.scene, "C__dist", finalAnchor);
    expect(presIH).not.toBeNull();
    expect(presIH!.title).toBe("Đoạn vuông góc IH");
    expect(presIH!.role).toBe("Đoạn vuông góc");
    const tipIH = buildVerifiedObjectTooltip(spherePlan.scene, "C__dist", finalAnchor);
    expect(tipIH?.header).toBe("Đoạn vuông góc IH");

    // 6. Regular pyramid altitude SO, diagonal EG, long-math intersection L, and section (IJKL)
    const pyrPlan = prepareScene(REGULAR_PYRAMID_SECTION_SCENE);
    const pyrFinal = pyrPlan.steps[pyrPlan.steps.length - 1]!.anchor;

    const presSO = resolveStudentObjectPresentation(pyrPlan.scene, "cao_SO", pyrFinal);
    expect(presSO?.title).toBe("Đường cao SO");
    expect(presSO?.role).toBe("Đường cao");

    const presEG = resolveStudentObjectPresentation(pyrPlan.scene, "O__diag_1", pyrFinal);
    expect(presEG?.title).toContain("EG");
    expect(presEG?.role.length).toBeLessThanOrEqual(26);

    const presL = resolveStudentObjectPresentation(pyrPlan.scene, "L_pt", pyrFinal);
    expect(presL?.title).toBe("Giao điểm L");
    expect(presL?.role).toBe("Giao điểm");
    expect(presL?.role.length).toBeLessThanOrEqual(26);
    expect(`${presL?.description ?? ""} ${presL?.evidence ?? ""}`).toContain("SH ∩ (IJK)");

    const presSec = resolveStudentObjectPresentation(pyrPlan.scene, "td_IJKL", pyrFinal);
    expect(presSec?.title).toMatch(/Thiết diện.*IJKL/u);
    expect(presSec?.role).toBe("Thiết diện");

    // 7. Adversarial 120-char role sentence never leaks as a long badge in policy or SSR card
    const policy = evaluateStudentPresentationPolicy(pyrPlan.scene, null);
    const longRoleObj = pyrPlan.scene.objects.find((o) => o.id === "L_pt")!;
    const shortBadge = policy.formatStudentObjectRole(longRoleObj);
    expect(shortBadge).not.toBeNull();
    expect(shortBadge!.length).toBeLessThanOrEqual(26);

    const ssrCardHtml = renderToString(
      <AxoWorkspaceV62
        scene={sampleRawScene("cau-cat-mat-phang")}
        tieuDe="Đường tròn giao của mặt phẳng và mặt cầu"
        initialStep={step0.anchor}
        initialSelectedId="cau__ref_pt"
      />,
    );
    expect(ssrCardHtml).toContain("Điểm tham chiếu X");
    expect(ssrCardHtml).toContain("Điểm phụ trợ");
    expect(ssrCardHtml).not.toContain("Điểm tham chiếu X thuộc mặt cầu dùng để mở bán kính từ tâm I");
  });

  it("§8.1, §8.2, §8.5, §8.6 — Enforces responsive CSS & canvas tooltip edge-clamping contract (zero overflow, visible close icon, unbroken math tokens, no overflow:hidden masking)", () => {
    // 1. Close button SVG has explicit dimensions so it never collapses to 0px width
    expect(GLOBAL_CSS).toMatch(/\.context-card-close\s*\{[^}]*width:\s*\d+px/s);
    expect(GLOBAL_CSS).toMatch(/\.context-card-close\s+svg\s*\{[^}]*width:\s*\d+px/s);

    // 2. Role badge wraps / stays bounded and never forces horizontal scroll or overflow:hidden clipping on card body
    const cardBlock = /\.context-object-card\s*\{([^}]*)\}/s.exec(GLOBAL_CSS)?.[1] ?? "";
    expect(cardBlock).not.toMatch(/overflow\s*:\s*hidden/);
    const bodyBlock = /\.context-card-body\s*\{([^}]*)\}/s.exec(GLOBAL_CSS)?.[1] ?? "";
    expect(bodyBlock).not.toMatch(/overflow\s*:\s*hidden/);
    expect(GLOBAL_CSS).toContain(".math-nowrap");

    // 3. Canvas tooltip clamping helper keeps real measured tooltip inside stage at left/right/top/bottom edges and avoids floating toolbars
    const stageW = 1080;
    const stageH = 854;
    const tipW = 268;
    const tipH = 62;
    const obstacles = [
      { left: 14, top: 804, right: 213, bottom: 842 }, // #playback-pa-capsule
      { left: 843, top: 802, right: 1066, bottom: 842 }, // #floating-toolbar-3d
    ];

    // Right edge (exact repro of Before overflowStageRightPx = 16px when pointer at x = 1012)
    const rightPos = computeClampedCanvasTooltipPosition(1012, 420, tipW, tipH, stageW, stageH, obstacles);
    expect(rightPos.x).toBeGreaterThanOrEqual(8);
    expect(rightPos.x + tipW).toBeLessThanOrEqual(stageW - 8);

    // Left edge
    const leftPos = computeClampedCanvasTooltipPosition(4, 300, tipW, tipH, stageW, stageH, obstacles);
    expect(leftPos.x).toBeGreaterThanOrEqual(8);
    expect(leftPos.x + tipW).toBeLessThanOrEqual(stageW - 8);

    // Top edge
    const topPos = computeClampedCanvasTooltipPosition(300, 6, tipW, tipH, stageW, stageH, obstacles);
    expect(topPos.y).toBeGreaterThanOrEqual(8);
    expect(topPos.y + tipH).toBeLessThanOrEqual(stageH - 8);

    // Bottom edge over floating toolbar -> lifts cleanly above toolbar without overflowing bottom
    const bottomPos = computeClampedCanvasTooltipPosition(920, 835, tipW, tipH, stageW, stageH, obstacles);
    expect(bottomPos.y).toBeGreaterThanOrEqual(8);
    expect(bottomPos.y + tipH).toBeLessThanOrEqual(802);

    // Narrow 360px mobile stage with stacked bottom obstacles (#playback-pa-box + #floating-toolbar-3d)
    const stackedMobileObstaclesForward = [
      { left: 6, top: 363, right: 354, bottom: 403 }, // #floating-toolbar-3d (upper bar)
      { left: 8, top: 409, right: 352, bottom: 443 }, // #playback-pa-box (lower bar)
    ];
    const stackedMobileObstaclesReverse = [...stackedMobileObstaclesForward].reverse();
    for (const obsList of [stackedMobileObstaclesForward, stackedMobileObstaclesReverse]) {
      const mobilePos = computeClampedCanvasTooltipPosition(348, 430, 248, 68, 360, 460, obsList);
      expect(mobilePos.x).toBeGreaterThanOrEqual(8);
      expect(mobilePos.x + 248).toBeLessThanOrEqual(360 - 8);
      expect(mobilePos.y).toBeGreaterThanOrEqual(8);
      // Must lift clear above BOTH stacked bars (upper bar top = 363)
      expect(mobilePos.y + 68).toBeLessThanOrEqual(363 - 4);
    }

    // 4. Shared MathDisplay keeps compact math tokens unbroken via .math-nowrap without splitting Vietnamese words
    expect(SIM_WORKSPACE_SRC).not.toContain("const COMPACT_MATH_TOKEN_RE");
    expect(EXPLORER_SRC).not.toContain("const COMPACT_MATH_TOKEN_RE");
    const mathCases: { input: string; expectedTokens: string[] }[] = [
      { input: "X thuộc mặt cầu tâm I, dùng để biểu diễn bán kính IX = R.", expectedTokens: ['<span class="math-nowrap">IX = R</span>'] },
      { input: "Đoạn vuông góc hạ từ tâm I đến (P) tại H (IH ⊥ (P)).", expectedTokens: ['<span class="math-nowrap">IH ⊥ (P)</span>'] },
      { input: "Đường tròn (H; HM) với r = √(R^2 - IH^2)", expectedTokens: ['<span class="math-nowrap">(H; HM)</span>', '<span class="math-nowrap">r = √(R<sup>2</sup> - IH<sup>2</sup>)</span>'] },
      { input: "Dựng điểm K = SH ∩ (IJK) trên đường cao.", expectedTokens: ['<span class="math-nowrap">K = SH ∩ (IJK)</span>'] },
      { input: "Cho SA = 4a và d(I, (P)) = a trong không gian.", expectedTokens: ['<span class="math-nowrap">SA = 4a</span>', '<span class="math-nowrap">d(I, (P)) = a</span>'] },
      { input: "Ta có IM = R = 2a và r = 4.", expectedTokens: ['<span class="math-nowrap">IM = R = 2a</span>', '<span class="math-nowrap">r = 4</span>'] },
      { input: "Tỉ số L = S_tp / S_xq = (3 + √5)/2.", expectedTokens: ['<span class="math-nowrap">L = S_tp / S_xq = (3 + √5)/2</span>'] },
      { input: "Điểm M chia đoạn theo tỉ số BM/BC = 1/2.", expectedTokens: ['<span class="math-nowrap">BM/BC = 1/2</span>'] },
      { input: "cos²(BC, (SAB)) = 0", expectedTokens: ['<span class="math-nowrap">cos²(BC, (SAB)) = 0</span>'] },
      { input: "Ghi nhận Sxq = 6π√5.", expectedTokens: ['<span class="math-nowrap">Sxq = 6π√5</span>'] },
    ];
    for (const mc of mathCases) {
      const rendered = renderToString(<MathDisplay text={mc.input} />);
      for (const tok of mc.expectedTokens) {
        expect(rendered, mc.input).toContain(tok);
      }
    }
    for (const noSplitProse of [
      "R = bán kính mặt cầu tâm I.",
      "Bán kính mặt cầu = 5",
      "Bán kính đường tròn = 4",
      "Bán kính đáy = 2",
      "Bán kính khối cong = 3",
      "Tỉ số phần còn lại = 1/2",
    ]) {
      const proseHtml = renderToString(<MathDisplay text={noSplitProse} />);
      expect(proseHtml, noSplitProse).not.toContain("math-nowrap");
      expect(proseHtml, noSplitProse).toBe(noSplitProse);
    }

    // Universal mid-word boundary invariant across every string in GEOMETRY_SAMPLES
    const wordCharRe = /[\p{L}\p{N}²³]/u;
    const assertNoMidWordSplit = (str: string, ctx: string) => {
      for (const m of str.matchAll(COMPACT_MATH_TOKEN_RE)) {
        const idx = m.index ?? 0;
        const end = idx + m[0].length;
        if (idx > 0) {
          expect(wordCharRe.test(str[idx - 1]!), `${ctx}: left split in "${str}" -> "${m[0]}"`).toBe(false);
        }
        if (end < str.length) {
          expect(wordCharRe.test(str[end]!), `${ctx}: right split in "${str}" -> "${m[0]}"`).toBe(false);
        }
      }
    };
    for (const s of GEOMETRY_SAMPLES) {
      const raw = (s.envelope as { scene3d?: Scene3D }).scene3d;
      if (!raw) continue;
      for (const o of raw.objects) {
        if (o.label) assertNoMidWordSplit(o.label, `${s.id}/${o.id}/label`);
        if (o.role) assertNoMidWordSplit(o.role, `${s.id}/${o.id}/role`);
        if (o.formula?.text) assertNoMidWordSplit(o.formula.text, `${s.id}/${o.id}/formula`);
      }
      for (const ev of raw.events) {
        if (ev.explanation) assertNoMidWordSplit(ev.explanation, `${s.id}/ev${ev.step_index}/exp`);
        if (ev.learner_text) assertNoMidWordSplit(ev.learner_text, `${s.id}/ev${ev.step_index}/lt`);
      }
    }
  });

  it("§8.7 — Exposes accessible full labels (aria-label + title), keyboard focusable step rows, and Step-1 reference point X in direct-context entity chips", () => {
    const spherePlan = prepareScene(sampleRawScene("cau-cat-mat-phang"));
    const step0 = spherePlan.steps[0]!;
    const groups0 = buildStepEntityGroups(spherePlan.scene, step0.anchor, {
      pedagogicalSteps: spherePlan.steps,
    });
    // X (cau__ref_pt) must be directly reachable in primary/context at Step 1 alongside I and IX
    const foregroundIds = new Set([...groups0.primary.map((x) => x.id), ...groups0.context.map((x) => x.id)]);
    expect(foregroundIds.has("cau__ref_pt")).toBe(true);
    expect(foregroundIds.has("cau__radius")).toBe(true);

    const html = renderToString(
      <AxoWorkspaceV62
        scene={sampleRawScene("cau-cat-mat-phang")}
        tieuDe="Đường tròn giao của mặt phẳng và mặt cầu"
        initialStep={step0.anchor}
        initialSelectedId="cau__ref_pt"
      />,
    );
    // Every rendered dock-entity-chip carries aria-label and aria-pressed
    const chipMatches = [...html.matchAll(/<button[^>]*class="[^"]*dock-entity-chip[^"]*"[^>]*>/g)];
    expect(chipMatches.length).toBeGreaterThanOrEqual(4);
    for (const m of chipMatches) {
      expect(m[0]).toContain("aria-label=");
      expect(m[0]).toContain("aria-pressed=");
    }
    expect(html).toContain('id="btn-clear-pick"');
    expect(html).toContain('aria-current="step"');

    // Mutual exclusion of #tb-display-pop / #tb-geo-custom-pop, Escape dismissal, Step-1 #pa-play replay, and prefers-reduced-motion
    expect(SIM_WORKSPACE_SRC).toMatch(/if\s*\(!dangPhat\s*&&\s*buocHinh\s*===\s*0\)\s*\{\s*setReplayNonce\(\(n\)\s*=>\s*n\s*\+\s*1\);/s);
    expect(SIM_WORKSPACE_SRC).toMatch(/setGeoCustomOpen\(false\);\s*setDisplayPopOpen\(\(v\)\s*=>\s*!v\)/s);
    expect(SIM_WORKSPACE_SRC).toMatch(/setDisplayPopOpen\(false\);\s*setGeoCustomOpen\(\(v\)\s*=>\s*!v\)/s);
    expect(SIM_WORKSPACE_SRC).toMatch(/if\s*\(e\.key\s*===\s*"Escape"\)\s*\{\s*if\s*\(geoCustomOpen\)\s*\{\s*setGeoCustomOpen\(false\);/s);

    const displayOpenHtml = renderToString(
      <AxoWorkspaceV62 scene={sampleRawScene("cau-cat-mat-phang")} initialDisplayPopOpen />,
    );
    expect(displayOpenHtml).toMatch(/id="tb-display-pop"[^>]*aria-hidden="false"/);
    expect(displayOpenHtml).toMatch(/id="tb-geo-custom-pop"[^>]*aria-hidden="true"/);

    const prevWindow = (globalThis as { window?: unknown }).window;
    try {
      (globalThis as { window?: unknown }).window = {
        matchMedia: (q: string) => ({ matches: q.includes("reduce") }),
      };
      expect(prefersReducedMotion()).toBe(true);
      (globalThis as { window?: unknown }).window = {
        matchMedia: () => ({ matches: false }),
      };
      expect(prefersReducedMotion()).toBe(false);
    } finally {
      if (prevWindow === undefined) {
        delete (globalThis as { window?: unknown }).window;
      } else {
        (globalThis as { window?: unknown }).window = prevWindow;
      }
    }
  });

  it("§8.8, §8.9 — Preserves object IDs, coordinates, and prerequisites, avoids X identifier collision, prevents future-step leakage, and provides observable Step-1 sphere formation duration", () => {
    // 1. Observable sphere formation duration (~1.2s–1.6s, not 480ms flash)
    expect(SPHERE_FORMATION_DURATION_MS).toBeGreaterThanOrEqual(1200);
    expect(SPHERE_FORMATION_DURATION_MS).toBeLessThanOrEqual(1800);

    // 2. External X collision check: sphere picks K instead of colliding with problem's X
    const extPlan = prepareScene(SPHERE_EXTERNAL_X_SCENE);
    const refPt = extPlan.scene.objects.find((o) => o.id === "ball_x__ref_pt");
    expect(refPt).toBeDefined();
    expect(refPt!.notation).not.toBe("X");
    expect(refPt!.notation).toBe("K");

    // 3. Future-step non-leakage & coordinate invariance across all steps of cau-cat-mat-phang and SPHERE_TANGENT_SCENE
    for (const raw of [sampleRawScene("cau-cat-mat-phang"), SPHERE_TANGENT_SCENE]) {
      const plan = prepareScene(raw);
      const step0Anchor = plan.steps[0]!.anchor;
      const ball = plan.scene.objects.find((o) => o.type === "curved_solid" && o.curved_kind === "ball")!;
      const presAt0 = resolveStudentObjectPresentation(plan.scene, `${ball.id}__ref_pt`, step0Anchor);
      expect(presAt0).not.toBeNull();
      // Step 1 presentation must NOT mention future cutting plane (P), foot H/T, or intersection point M
      const combined0 = `${presAt0!.title} ${presAt0!.role} ${presAt0!.description} ${presAt0!.evidence ?? ""}`;
      expect(combined0).not.toContain("(P)");
      expect(combined0).not.toContain("(H; HM)");
      expect(combined0).not.toContain("IT");

      const baselineCoords = new Map(
        plan.scene.objects
          .filter((o) => o.xyz)
          .map((o) => [o.id, o.xyz!.join("|")]),
      );
      for (const st of plan.steps) {
        for (const o of plan.scene.objects) {
          if (o.xyz) expect(o.xyz.join("|")).toBe(baselineCoords.get(o.id));
        }
        // No future object appears in step entity groups before its birth
        const groups = buildStepEntityGroups(plan.scene, st.anchor, { pedagogicalSteps: plan.steps });
        const presentSet = new Set(st.visibleIds);
        for (const chip of groups.all) {
          expect(presentSet.has(chip.id)).toBe(true);
        }
      }
    }
  });

  it("§8.10 — Enforces 4-tier auxiliary presentation policy (ACTIVE_PRIMARY, ACTIVE_EVIDENCE, ORIENTATION_CONTEXT, COMPLETED_AUXILIARY) without deleting objects from Scene3D", () => {
    // A. Regular pyramid S.EFGH: diagonals EG & FH construct O, stay visible during foundation (SO, S.EFGH), then transition to COMPLETED_AUXILIARY on section steps
    const pyrPlan = prepareScene(REGULAR_PYRAMID_SECTION_SCENE);
    const stepO = pyrPlan.steps.find((s) => s.targetIds.includes("O__diag_1") || s.visibleIds.includes("O__diag_1"))!;
    const rolesAtO = resolveStepVisualRoles(pyrPlan.scene, stepO.anchor, { auxiliaryShown: false, selectedId: null });
    expect(rolesAtO.get("O__diag_1")?.visible).toBe(true);
    expect(["ACTIVE_PRIMARY", "ACTIVE_EVIDENCE"]).toContain(rolesAtO.get("O__diag_1")?.presentationTier);

    const stepSO = pyrPlan.steps.find((s) => s.targetIds.includes("cao_SO"))!;
    const rolesAtSO = resolveStepVisualRoles(pyrPlan.scene, stepSO.anchor, { auxiliaryShown: false, selectedId: null });
    expect(rolesAtSO.get("O__diag_1")?.visible).toBe(true);
    expect(rolesAtSO.get("O__diag_1")?.presentationTier).toBe("ACTIVE_EVIDENCE");

    const finalAnchor = pyrPlan.steps[pyrPlan.steps.length - 1]!.anchor;
    const rolesFinalNeutral = resolveStepVisualRoles(pyrPlan.scene, finalAnchor, { auxiliaryShown: false, selectedId: null });
    expect(rolesFinalNeutral.get("O__diag_1")?.presentationTier).toBe("COMPLETED_AUXILIARY");
    expect(rolesFinalNeutral.get("O__diag_1")?.visible).toBe(false);
    expect(rolesFinalNeutral.get("O__diag_2")?.presentationTier).toBe("COMPLETED_AUXILIARY");
    expect(rolesFinalNeutral.get("O__diag_2")?.visible).toBe(false);
    // Altitude SO remains ORIENTATION_CONTEXT with subordinated ⊥ witness
    expect(rolesFinalNeutral.get("cao_SO")?.visible).toBe(true);
    expect(rolesFinalNeutral.get("cao_SO")?.presentationTier).toBe("ORIENTATION_CONTEXT");
    expect(rolesFinalNeutral.get("cao_SO")?.showPerpWitnessSymbol).toBe(true);
    // Toggling Hình phụ restores completed auxiliaries immediately, and objects remain in scene.objects
    expect(pyrPlan.scene.objects.some((o) => o.id === "O__diag_1")).toBe(true);
    const rolesFinalAuxOn = resolveStepVisualRoles(pyrPlan.scene, finalAnchor, { auxiliaryShown: true, selectedId: null });
    expect(rolesFinalAuxOn.get("O__diag_1")?.visible).toBe(true);

    // B. Secant sphere cut (cau-cat-mat-phang): X & IX are ACTIVE_PRIMARY at Step 1, ORIENTATION_CONTEXT at Step 2-3, and COMPLETED_AUXILIARY once IM takes over R = 5 at Step 4-5; IH & HM are ACTIVE_EVIDENCE
    const secSpherePlan = prepareScene(sampleRawScene("cau-cat-mat-phang"));
    const s0 = secSpherePlan.steps[0]!.anchor;
    const s1 = secSpherePlan.steps[1]!.anchor;
    const sFinal = secSpherePlan.steps[secSpherePlan.steps.length - 1]!.anchor;

    const r0 = resolveStepVisualRoles(secSpherePlan.scene, s0, { auxiliaryShown: false, selectedId: null });
    expect(r0.get("cau__radius")?.visible).toBe(true);
    expect(r0.get("cau__radius")?.presentationTier).toBe("ACTIVE_PRIMARY");

    const r1 = resolveStepVisualRoles(secSpherePlan.scene, s1, { auxiliaryShown: false, selectedId: null });
    expect(r1.get("cau__radius")?.visible).toBe(true);
    expect(r1.get("cau__radius")?.presentationTier).toBe("ORIENTATION_CONTEXT");

    const rFinal = resolveStepVisualRoles(secSpherePlan.scene, sFinal, { auxiliaryShown: false, selectedId: null });
    expect(rFinal.get("cau__radius")?.presentationTier).toBe("COMPLETED_AUXILIARY");
    expect(rFinal.get("cau__radius")?.visible).toBe(false);
    expect(rFinal.get("cau__ref_pt")?.presentationTier).toBe("COMPLETED_AUXILIARY");
    expect(rFinal.get("cau__ref_pt")?.visible).toBe(false);
    expect(rFinal.get("C__dist")?.visible).toBe(true);
    expect(rFinal.get("C__dist")?.presentationTier).toBe("ACTIVE_EVIDENCE");
    expect(rFinal.get("C__sec_rad")?.visible).toBe(true);
    expect(rFinal.get("C__sec_rad")?.presentationTier).toBe("ACTIVE_EVIDENCE");

    // C. Tangent & Disjoint sphere-plane: no IM exists, so IX & X stay visible as ACTIVE_EVIDENCE to compare d(I,(P)) against R
    for (const raw of [SPHERE_TANGENT_SCENE, SPHERE_DISJOINT_SCENE]) {
      const p = prepareScene(raw);
      const ball = p.scene.objects.find((o) => o.type === "curved_solid" && o.curved_kind === "ball")!;
      const lastA = p.steps[p.steps.length - 1]!.anchor;
      const rf = resolveStepVisualRoles(p.scene, lastA, { auxiliaryShown: false, selectedId: null });
      expect(rf.get(`${ball.id}__radius`)?.visible).toBe(true);
      expect(rf.get(`${ball.id}__radius`)?.presentationTier).toBe("ACTIVE_EVIDENCE");
    }
  });

  it("§8.11 — Guarantees continuous C1 projected circle overlap attenuation during 180-frame continuous camera rotation with zero jump discontinuity or flicker", () => {
    const cam = new THREE.PerspectiveCamera(35, 1440 / 900, 0.1, 1000);
    cam.up.set(0, 0, 1);
    const section = [{ center: [0, 0, 0.5] as [number, number, number], normal: [0, 0.36, 0.933] as [number, number, number], radius: Math.sqrt(25 - 0.25) }];

    const samples: number[] = [];
    for (let i = 0; i <= 180; i += 1) {
      const u = i / 180;
      const elev = -0.22 + 0.98 * u; // sweeps continuously across grazing angle up to isometric 43°!
      const az = 0.5 * Math.PI;
      const dist = 18;
      cam.position.set(
        dist * Math.cos(elev) * Math.cos(az),
        dist * Math.cos(elev) * Math.sin(az),
        dist * Math.sin(elev),
      );
      cam.lookAt(0, 0, 0);
      cam.updateMatrixWorld(true);
      cam.updateProjectionMatrix();
      samples.push(
        computeProjectedCircleOverlapFactor([0, 0, 0], [0, 0, 1], 5, section, cam, 1440, 900),
      );
    }

    const minScale = Math.min(...samples);
    const maxScale = Math.max(...samples);
    expect(minScale).toBeLessThan(0.05);
    expect(maxScale).toBeGreaterThan(0.95);

    let maxStepDelta = 0;
    for (let i = 1; i < samples.length; i += 1) {
      maxStepDelta = Math.max(maxStepDelta, Math.abs(samples[i]! - samples[i - 1]!));
    }
    // Eliminates the old 0.16 -> 0 step discontinuity at hideDistPx!
    expect(maxStepDelta).toBeLessThanOrEqual(0.08);
  });

  it("§8.12 — Passes mathematical, construction, visual, and presentation-contract gates across all 6 solid families (pyramid, prism, cube, cone, cylinder, sphere)", () => {
    const familyFixtures: { family: string; raw: Scene3D }[] = [
      { family: "pyramid-sample", raw: sampleRawScene("thiet-dien-chop") },
      { family: "pyramid-regular", raw: REGULAR_PYRAMID_SECTION_SCENE },
      { family: "prism-triangular", raw: TRIANGULAR_PRISM_SCENE },
      { family: "cube-hexagon", raw: CUBE_HEXAGONAL_SECTION_SCENE },
      { family: "cone-axial", raw: sampleRawScene("non-thiet-dien-truc") },
      { family: "cylinder-cross", raw: sampleRawScene("tru-thiet-dien-tron") },
      { family: "sphere-volume", raw: sampleRawScene("cau-the-tich") },
      { family: "sphere-secant", raw: sampleRawScene("cau-cat-mat-phang") },
      { family: "sphere-pure", raw: PURE_STANDALONE_SPHERE_SCENE },
      { family: "sphere-tangent", raw: SPHERE_TANGENT_SCENE },
      { family: "sphere-disjoint", raw: SPHERE_DISJOINT_SCENE },
    ];

    for (const { family, raw } of familyFixtures) {
      const { plan, worldScene } = prepareWorldScene(raw);
      expect(verifySceneMathematicalConsistency(plan.scene).valid, `${family}: math consistency`).toBe(true);
      expect(verifyConstructionContinuity(plan.scene).valid, `${family}: construction continuity`).toBe(true);
      const visReport = verifyVisualContinuity(plan.scene);
      expect(visReport.valid, `${family}: visual continuity -> ${JSON.stringify(visReport.violations)}`).toBe(true);

      const steps = pedagogicalStepList(worldScene);
      expect(steps.length).toBeGreaterThan(0);
      const lastAnchor = steps[steps.length - 1]!.anchor;
      const groups = buildStepEntityGroups(worldScene, lastAnchor, { pedagogicalSteps: steps });
      for (const item of groups.all) {
        const pres = resolveStudentObjectPresentation(worldScene, item.id, lastAnchor);
        expect(pres, `${family}/${item.id}: presentation exists`).not.toBeNull();
        expect(pres!.title.length, `${family}/${item.id}: non-empty title`).toBeGreaterThan(0);
        expect(pres!.role.length, `${family}/${item.id}: concise role badge (${pres!.role})`).toBeLessThanOrEqual(26);
        expect(pres!.title.toLowerCase(), `${family}/${item.id}: title != role`).not.toBe(pres!.role.toLowerCase());
        expect(pres!.description, `${family}/${item.id}: description != title`).not.toBe(pres!.title);
        expect(pres!.description, `${family}/${item.id}: description != role`).not.toBe(pres!.role);
      }
    }

    // Non-identity chart_metric & full GEOMETRY_SAMPLES sweep after Cholesky veKhongGian:
    // - Zero 10-digit float ratio leaks (e.g. 1118033989/2236067977)
    // - Exact midpoint / collinear ratio preserved identically between plan.scene and worldScene
    // - Universal title !== role across every object of every catalog sample + unnamed synthetic objects
    const floatLeakRe = /\d{7,}\/\d{7,}/u;
    for (const sample of GEOMETRY_SAMPLES) {
      const raw = (sample.envelope as { scene3d?: Scene3D }).scene3d;
      if (!raw) continue;
      const { plan, worldScene } = prepareWorldScene(raw);
      const steps = pedagogicalStepList(worldScene);
      const lastAnchor = steps[steps.length - 1]?.anchor ?? Math.max(0, worldScene.events.length - 1);
      for (const obj of worldScene.objects) {
        if (obj.type === "point3") {
          const exactObj = plan.scene.objects.find((o) => o.id === obj.id) ?? obj;
          expect(findPointMidpointRelation(worldScene, obj), `${sample.id}/${obj.id}: midpoint rel`).toEqual(
            findPointMidpointRelation(plan.scene, exactObj),
          );
          expect(findLinePlaneIntersectionMidpoint(worldScene, obj), `${sample.id}/${obj.id}: line-plane rel`).toEqual(
            findLinePlaneIntersectionMidpoint(plan.scene, exactObj),
          );
        }
        const chipLbl = formatCompactEntityChipLabel(worldScene, obj);
        expect(chipLbl, `${sample.id}/${obj.id}: chip float leak`).not.toMatch(floatLeakRe);
        const pres = resolveStudentObjectPresentation(worldScene, obj.id, lastAnchor);
        if (!pres) continue;
        expect(pres.title.toLowerCase(), `${sample.id}/${obj.id}: title != role`).not.toBe(pres.role.toLowerCase());
        expect(pres.role.length, `${sample.id}/${obj.id}: role <= 26`).toBeLessThanOrEqual(26);
        const allText = `${pres.title} | ${pres.role} | ${pres.description} | ${pres.evidence ?? ""}`;
        expect(allText, `${sample.id}/${obj.id}: presentation float leak`).not.toMatch(floatLeakRe);
      }
    }

    // Unnamed / special synthetic objects never collapse to title === role
    const unnamedEdgeScene: Scene3D = {
      chart_metric: [
        ["1", "0", "0"],
        ["0", "1", "0"],
        ["0", "0", "1"],
      ],
      free_objects: [],
      objects: [
        { id: "u_ball", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu", notation: null, origin: "derived", producer: null, render: "curved_solid", depends: [], anchor: ["0", "0", "0"], radius_sq: "9" },
        { id: "u_cyl", type: "curved_solid", curved_kind: "cylinder", label: "Hình trụ", notation: null, origin: "derived", producer: null, render: "curved_solid", depends: [], anchor: ["0", "0", "0"], apex_or_top: ["0", "0", "4"], radius_sq: "4" },
        { id: "u_cone", type: "curved_solid", curved_kind: "cone", label: "Hình nón", notation: null, origin: "derived", producer: null, render: "curved_solid", depends: [], anchor: ["0", "0", "0"], apex_or_top: ["0", "0", "4"], radius_sq: "4" },
        { id: "u_solid", type: "solid", label: "Khối đa diện", notation: null, origin: "derived", producer: null, render: "mesh", depends: [], vertices: [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]], faces: [[0, 1, 2], [0, 1, 3], [1, 2, 3], [0, 2, 3]] },
        { id: "u_sec", type: "section", label: "Thiết diện", notation: null, origin: "derived", producer: null, render: "surface", depends: [], polygon: [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"]] },
      ],
      events: [{ step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" }],
    };
    for (const o of unnamedEdgeScene.objects) {
      const pres = resolveStudentObjectPresentation(unnamedEdgeScene, o.id, 0);
      expect(pres).not.toBeNull();
      expect(pres!.title.toLowerCase(), `unnamed/${o.id}`).not.toBe(pres!.role.toLowerCase());
      expect(pres!.description, `unnamed/${o.id} desc`).not.toBe(pres!.title);
    }
  });
});
