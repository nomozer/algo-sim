import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { toNumber, type Scene3D, type SceneObject } from "./scene3d-model";
import { withSubEntities } from "./scene3d-subentities";
import { annotationsAt, DEFAULT_ANNOTATION_VIEW } from "./scene3d-annotations";
import {
  buildPedagogicalConstructionPlan,
  computeProjectedCircleOverlapFactor,
  formatCanonicalCircleDesignation,
  formatCompactEntityChipLabel,
  pedagogicalStepList,
  registerExactSceneOrigin,
  resolveSphereReferenceGreatCirclePolicy,
  resolveStepVisualRoles,
  verifyConstructionContinuity,
  verifySceneMathematicalConsistency,
  verifyVisualContinuity,
} from "./scene3d-semantic-policy";
import { buildObject3D } from "./scene3d-view";

function sampleRawScene(id: string): Scene3D {
  const found = GEOMETRY_SAMPLES.find((x) => x.id === id);
  if (!found) throw new Error(`Missing sample: ${id}`);
  return (found.envelope as { scene3d?: Scene3D }).scene3d as Scene3D;
}

function sampleScene(id: string): Scene3D {
  const raw = sampleRawScene(id);
  const sub = withSubEntities(raw);
  registerExactSceneOrigin(sub, raw);
  return sub;
}

// 1a. Pure standalone sphere (I, R) without any given point on the sphere
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

// 3. Sphere cut by inclined plane (Q): 3x + 4z - 15 = 0 => d = 3, r = 4
const SPHERE_INCLINED_CUT_SCENE: Scene3D = {
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
      label: "I",
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
      value: "5",
      annotation: {
        kind: "radius" as unknown as "length",
        category: "measurement",
        role: "given",
        subject_ids: ["cau_q"],
        anchor: "solid",
      },
    },
    {
      id: "cau_q",
      type: "curved_solid",
      curved_kind: "ball",
      label: "Mặt cầu (S)",
      notation: "(S)",
      origin: "derived",
      producer: "construct_sphere",
      render: "curved_solid",
      depends: ["I", "q_R"],
      anchor: ["0", "0", "0"],
      radius_sq: "25",
    },
    {
      id: "mp_Q",
      type: "plane3",
      label: "Mặt phẳng (Q)",
      notation: "(Q)",
      origin: "derived",
      producer: "construct_plane",
      render: "surface",
      depends: [],
      formation_roles: ["CONSTRUCT_CUTTING_OBJECT"],
      point: ["9/5", "0", "12/5"],
      normal: ["3", "0", "4"],
    },
    {
      id: "c_q",
      type: "circle3",
      label: "Đường tròn giao của (S) và (Q)",
      notation: null,
      origin: "derived",
      producer: "intersect_sphere_plane",
      render: "circle",
      depends: ["cau_q", "mp_Q"],
      center: ["9/5", "0", "12/5"],
      normal: ["3", "0", "4"],
      radius_sq: "16",
    },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
    { step_index: 1, action: "CREATE", object: "cau_q", depends: ["I", "q_R"], explanation: "Dựng (S)." },
    { step_index: 2, action: "CREATE", object: "mp_Q", depends: [], explanation: "Dựng (Q)." },
    { step_index: 3, action: "CREATE", object: "c_q", depends: ["cau_q", "mp_Q"], explanation: "Dựng đường tròn giao." },
  ],
};

// 4a. Plane through center I horizontally (d = 0, geometrically coincident with canonical horizontal reference great circle!)
const SPHERE_D0_HORIZONTAL_SCENE: Scene3D = {
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  free_objects: ["I", "q_R"],
  objects: [
    { id: "I", type: "point3", label: "I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "q_R", type: "quantity", label: "R", notation: "R", origin: "free", producer: null, render: "readout", depends: [], value: "5" },
    { id: "cau_d0", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: "construct_sphere", render: "curved_solid", depends: ["I", "q_R"], anchor: ["0", "0", "0"], radius_sq: "25" },
    { id: "mp_alpha", type: "plane3", label: "Mặt phẳng (α)", notation: "(α)", origin: "derived", producer: "construct_plane", render: "surface", depends: [], formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], point: ["0", "0", "0"], normal: ["0", "0", "1"] },
    { id: "c_d0", type: "circle3", label: "Đường tròn lớn giao của (S) và (α)", notation: null, origin: "derived", producer: "intersect_sphere_plane", render: "circle", depends: ["cau_d0", "mp_alpha"], center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "25" },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
    { step_index: 1, action: "CREATE", object: "cau_d0", depends: ["I", "q_R"], explanation: "Dựng (S)." },
    { step_index: 2, action: "CREATE", object: "mp_alpha", depends: [], explanation: "Dựng (α) qua I." },
    { step_index: 3, action: "CREATE", object: "c_d0", depends: ["cau_d0", "mp_alpha"], explanation: "Dựng đường tròn lớn." },
  ],
};

// 4b. Near-center horizontal cut (d = 1, R = 5 => r² = 24)
const SPHERE_NEAR_CENTER_SCENE: Scene3D = {
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  free_objects: ["I", "q_R"],
  objects: [
    { id: "I", type: "point3", label: "I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "q_R", type: "quantity", label: "R", notation: "R", origin: "free", producer: null, render: "readout", depends: [], value: "5" },
    { id: "cau_nc", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: "construct_sphere", render: "curved_solid", depends: ["I", "q_R"], anchor: ["0", "0", "0"], radius_sq: "25" },
    { id: "mp_nc", type: "plane3", label: "Mặt phẳng (β)", notation: "(β)", origin: "derived", producer: "construct_plane", render: "surface", depends: [], formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], point: ["0", "0", "1"], normal: ["0", "0", "1"] },
    { id: "c_nc", type: "circle3", label: "Đường tròn giao của (S) và (β)", notation: null, origin: "derived", producer: "intersect_sphere_plane", render: "circle", depends: ["cau_nc", "mp_nc"], center: ["0", "0", "1"], normal: ["0", "0", "1"], radius_sq: "24" },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
    { step_index: 1, action: "CREATE", object: "cau_nc", depends: ["I", "q_R"], explanation: "Dựng (S)." },
    { step_index: 2, action: "CREATE", object: "mp_nc", depends: [], explanation: "Dựng (β)." },
    { step_index: 3, action: "CREATE", object: "c_nc", depends: ["cau_nc", "mp_nc"], explanation: "Dựng đường tròn giao." },
  ],
};

// 5. Tangent plane (d = R = 5, including future perpendicular witness IT ⊥ (P) at Step 4)
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

// 6. Disjoint plane (d = 7 > R = 5)
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

// 9b. Regular square pyramid S.EFGH with interior center O and polygonal section IJKL
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
    { id: "L_pt", type: "point3", label: "L", notation: "L", origin: "derived", producer: "intersect_line_plane", render: "point_marker", depends: ["canh_SH", "mp_IJK"], xyz: ["-4/3", "4/3", "4/3"] },
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

// 10. Cube PQRS.P'Q'R'S' with hexagonal section UVWXYZ
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

describe("AXO — Final Pedagogical Geometry Hardening & Acceptance Gate (§1–§5)", () => {
  describe("§1 — Sphere Construction Determination (I → IX/IA → Sphere)", () => {
    it("1a. Pure (I, R) sphere creates a real non-authoritative reference point X on the sphere + radius IX coalesced into Step 1, with R badge on IX and zero floating rays", () => {
      const sub = withSubEntities(PURE_STANDALONE_SPHERE_SCENE);
      registerExactSceneOrigin(sub, PURE_STANDALONE_SPHERE_SCENE);
      const plan = buildPedagogicalConstructionPlan(sub);
      const step0 = plan.steps[0]!;

      const refPt = plan.scene.objects.find((o) => o.id === "cau_ir__ref_pt");
      const radSeg = plan.scene.objects.find((o) => o.id === "cau_ir__radius");
      expect(refPt).toBeDefined();
      expect(refPt?.origin).toBe("derived");
      expect(refPt?.authoritative).toBe(false);
      expect(refPt?.semantic_role).toBe("AUXILIARY_CONSTRUCTION");
      expect(radSeg).toBeDefined();
      expect(radSeg?.endpoint_ids).toEqual(["I", "cau_ir__ref_pt"]);

      // Exact |IX|^2 = 16 = R^2
      const xyz = refPt!.xyz!.map(toNumber);
      expect(xyz[0]! ** 2 + xyz[1]! ** 2 + xyz[2]! ** 2).toBeCloseTo(16, 9);

      // Step 1 contains I, X, IX, and sphere together
      expect(step0.visibleIds).toEqual(expect.arrayContaining(["I", "cau_ir__ref_pt", "cau_ir__radius", "cau_ir"]));
      expect(plan.steps).toHaveLength(1);

      // Given R = 4 badge anchors onto [I, X]
      const anns = annotationsAt(plan.scene, step0.anchor, DEFAULT_ANNOTATION_VIEW, null);
      expect(anns.some((a) => a.text.includes("4") && a.subject_ids.includes("I") && a.subject_ids.includes("cau_ir__ref_pt"))).toBe(true);
    });

    it("1b. Sphere with given point A on the sphere (cau-the-tich) prioritizes IA in Step 1 without creating X and without leaking target results", () => {
      const plan = buildPedagogicalConstructionPlan(sampleScene("cau-the-tich"));
      expect(plan.steps).toHaveLength(1);
      const step0 = plan.steps[0]!;
      expect(plan.scene.objects.some((o) => o.id === "cau__ref_pt")).toBe(false);
      const radSeg = plan.scene.objects.find((o) => o.id === "cau__radius");
      expect(radSeg).toBeDefined();
      expect(new Set(radSeg!.endpoint_ids)).toEqual(new Set(["I", "A"]));
      expect(step0.visibleIds).toEqual(expect.arrayContaining(["I", "A", "cau__radius", "cau"]));

      // R = 3 and V = 36π are FINAL_RESULT targets in cau-the-tich — never leaked onto canvas
      const anns = annotationsAt(plan.scene, step0.anchor, DEFAULT_ANNOTATION_VIEW, null);
      expect(anns).toHaveLength(0);
    });

    it("1c. Sphere cut by plane (cau-cat-mat-phang) keeps X distinct from H and M, keeps coordinates invariant across all steps, and never duplicates R = 5", () => {
      const plan = buildPedagogicalConstructionPlan(sampleScene("cau-cat-mat-phang"));
      const step0 = plan.steps[0]!;
      const refPt = plan.scene.objects.find((o) => o.id === "cau__ref_pt")!;
      const rimPt = plan.scene.objects.find((o) => o.id === "C__rim_pt")!;
      const footPt = plan.scene.objects.find((o) => o.id === "C__center")!;
      expect(refPt).toBeDefined();
      expect(refPt.xyz).not.toEqual(rimPt.xyz);
      expect(refPt.xyz).not.toEqual(footPt.xyz);
      expect(step0.title).not.toContain("(S)"); // notation is null in cau-cat-mat-phang

      // Step 1 shows R = 5 on IX; Step 4+ shows R = 5 once (never twice)
      const annsStep0 = annotationsAt(plan.scene, step0.anchor, DEFAULT_ANNOTATION_VIEW, null);
      expect(annsStep0.filter((a) => a.text.includes("5"))).toHaveLength(1);
      const finalStep = plan.steps[plan.steps.length - 1]!;
      const annsFinal = annotationsAt(plan.scene, finalStep.anchor, DEFAULT_ANNOTATION_VIEW, null);
      expect(annsFinal.filter((a) => a.text.includes("5"))).toHaveLength(1);
    });

    it("1d. Tangent-plane sphere (d = R) still synthesizes X and IX at Step 1 even when perpendicular IT ⊥ (P) of length R is derived at Step 4", () => {
      const sub = withSubEntities(SPHERE_TANGENT_SCENE);
      registerExactSceneOrigin(sub, SPHERE_TANGENT_SCENE);
      const plan = buildPedagogicalConstructionPlan(sub);
      const step0 = plan.steps[0]!;
      const refPt = plan.scene.objects.find((o) => o.id === "cau_tan__ref_pt");
      const radSeg = plan.scene.objects.find((o) => o.id === "cau_tan__radius");
      expect(refPt).toBeDefined();
      expect(radSeg).toBeDefined();
      expect(step0.visibleIds).toEqual(expect.arrayContaining(["I", "cau_tan__ref_pt", "cau_tan__radius", "cau_tan"]));
      expect(step0.visibleIds).not.toContain("T");
      expect(step0.visibleIds).not.toContain("IT");
      expect(refPt!.xyz).not.toEqual(["3", "0", "4"]);

      // Irrational radius R = √3 (R² = 3, not a sum of two rational squares in z = 0) still finds exact 3D lattice point X on sphere
      const rSq3Scene: Scene3D = {
        ...PURE_STANDALONE_SPHERE_SCENE,
        objects: PURE_STANDALONE_SPHERE_SCENE.objects.map((o) =>
          o.id === "cau_ir" ? { ...o, radius_sq: "3" } : o.id === "q_R" ? { ...o, value: "√3" } : o,
        ),
      };
      const rSq3Sub = withSubEntities(rSq3Scene);
      registerExactSceneOrigin(rSq3Sub, rSq3Scene);
      const rSq3Plan = buildPedagogicalConstructionPlan(rSq3Sub);
      const rSq3Ref = rSq3Plan.scene.objects.find((o) => o.id === "cau_ir__ref_pt");
      expect(rSq3Ref).toBeDefined();
      const xyz3 = rSq3Ref!.xyz!.map(toNumber);
      expect(xyz3[0]! ** 2 + xyz3[1]! ** 2 + xyz3[2]! ** 2).toBeCloseTo(3, 9);
    });
  });

  describe("§2 — Unified Sphere Reference Great Circle vs Intersection Circle vs Projected Ellipse Policy", () => {
    it("2a. NEVER switches reference great circle normal to [0,1,0] or [1,0,0] across any plane regime", () => {
      for (const raw of [
        sampleScene("cau-cat-mat-phang"),
        SPHERE_INCLINED_CUT_SCENE,
        SPHERE_D0_HORIZONTAL_SCENE,
        SPHERE_NEAR_CENTER_SCENE,
        SPHERE_TANGENT_SCENE,
        SPHERE_DISJOINT_SCENE,
      ]) {
        const sub = withSubEntities(raw);
        registerExactSceneOrigin(sub, raw);
        const plan = buildPedagogicalConstructionPlan(sub);
        const ball = plan.scene.objects.find((o) => o.type === "curved_solid" && o.curved_kind === "ball")!;
        for (const st of plan.steps) {
          const vis = st.visibleIds
            .map((id) => plan.scene.objects.find((o) => o.id === id))
            .filter((o): o is SceneObject => Boolean(o));
          const pol = resolveSphereReferenceGreatCirclePolicy(plan.scene, ball, vis, false);
          expect(pol.normal).toEqual(["0", "0", "1"]);
        }
      }
    });

    it("2b. Geometric coincidence (d = 0 horizontal through I) transitions role from REFERENCE_GREAT_CIRCLE to single RESULT_SECTION circle without duplicate stroke", () => {
      const sub = withSubEntities(SPHERE_D0_HORIZONTAL_SCENE);
      registerExactSceneOrigin(sub, SPHERE_D0_HORIZONTAL_SCENE);
      const plan = buildPedagogicalConstructionPlan(sub);
      const ball = plan.scene.objects.find((o) => o.id === "cau_d0")!;

      const step0Objs = plan.steps[0]!.visibleIds
        .map((id) => plan.scene.objects.find((o) => o.id === id))
        .filter((o): o is SceneObject => Boolean(o));
      const polStep0 = resolveSphereReferenceGreatCirclePolicy(plan.scene, ball, step0Objs, false);
      expect(polStep0.visible).toBe(true);
      expect(polStep0.role).toBe("REFERENCE_GREAT_CIRCLE");

      const finalStep = plan.steps[plan.steps.length - 1]!;
      const finalObjs = finalStep.visibleIds
        .map((id) => plan.scene.objects.find((o) => o.id === id))
        .filter((o): o is SceneObject => Boolean(o));
      const polFinal = resolveSphereReferenceGreatCirclePolicy(plan.scene, ball, finalObjs, false);
      expect(polFinal.visible).toBe(false);
      expect(polFinal.roleTransitionedToObjectId).toBe("c_d0");
      expect(polFinal.reason).toBe("coincident_role_transition_to_intersection_circle");
    });

    it("2c. Near-center cut (d = 1, R = 5) hides reference circle when intersection circle is active without altering 3D geometry", () => {
      const sub = withSubEntities(SPHERE_NEAR_CENTER_SCENE);
      registerExactSceneOrigin(sub, SPHERE_NEAR_CENTER_SCENE);
      const plan = buildPedagogicalConstructionPlan(sub);
      const ball = plan.scene.objects.find((o) => o.id === "cau_nc")!;

      const step0Objs = plan.steps[0]!.visibleIds
        .map((id) => plan.scene.objects.find((o) => o.id === id))
        .filter((o): o is SceneObject => Boolean(o));
      expect(resolveSphereReferenceGreatCirclePolicy(plan.scene, ball, step0Objs, false).visible).toBe(true);

      const finalObjs = plan.steps[plan.steps.length - 1]!.visibleIds
        .map((id) => plan.scene.objects.find((o) => o.id === id))
        .filter((o): o is SceneObject => Boolean(o));
      const polFinal = resolveSphereReferenceGreatCirclePolicy(plan.scene, ball, finalObjs, false);
      expect(polFinal.normal).toEqual(["0", "0", "1"]);
      expect(polFinal.visible).toBe(false);
      expect(polFinal.reason).toBe("hidden_near_coincident_with_intersection_circle");
    });

    it("2d. 2D screen-projected ellipse near-coincidence attenuates reference great circle under edge-on overlap and restores under clear 3D orbit", () => {
      // Reference great circle: center (0,0,0), normal (0,0,1), R = 5
      // Inclined section through/near center: center (0,0,0.4), normal (0, 0.25, 0.968), r = 4.98
      const grazingCam = new THREE.PerspectiveCamera(35, 1440 / 900, 0.1, 1000);
      grazingCam.up.set(0, 0, 1);
      grazingCam.position.set(0, 18, 0.12); // looking along Y where both circles project to near-collinear horizontal ellipses!
      grazingCam.lookAt(0, 0, 0);
      grazingCam.updateMatrixWorld(true);
      grazingCam.updateProjectionMatrix();

      const overlapScale = computeProjectedCircleOverlapFactor(
        [0, 0, 0],
        [0, 0, 1],
        5,
        [{ center: [0, 0, 0.15], normal: [0, 0.08, 0.9968], radius: Math.sqrt(25 - 0.0225) }],
        grazingCam,
        1440,
        900,
      );
      expect(overlapScale).toBeLessThan(0.35);

      const clearCam = new THREE.PerspectiveCamera(35, 1440 / 900, 0.1, 1000);
      clearCam.up.set(0, 0, 1);
      clearCam.position.set(11, -11, 9);
      clearCam.lookAt(0, 0, 0);
      clearCam.updateMatrixWorld(true);
      clearCam.updateProjectionMatrix();

      const clearScale = computeProjectedCircleOverlapFactor(
        [0, 0, 0],
        [0, 0, 1],
        5,
        [{ center: [0.9 * 2, 0, 1.2 * 2], normal: [0.6, 0, 0.8], radius: 4 }],
        clearCam,
        1440,
        900,
      );
      expect(clearScale).toBeGreaterThan(0.85);
    });
  });

  describe("§3 — Mathematical Symbols & Canonical (Center; Radius) Circle Naming", () => {
    it("3a. Names every circle by (Center; Radius) without bare center ambiguity and without leaking target results, and names polygon3 sections with vertices", () => {
      // Sphere horizontal cut -> Đường tròn (H; HM)
      const cutPlan = buildPedagogicalConstructionPlan(sampleScene("cau-cat-mat-phang"));
      const cutCircle = cutPlan.scene.objects.find((o) => o.id === "C")!;
      expect(formatCompactEntityChipLabel(cutPlan.scene, cutCircle)).toBe("Đường tròn (H; HM)");
      expect(formatCanonicalCircleDesignation(cutPlan.scene, cutCircle)).toBe("Đường tròn (H; HM)");

      // Sphere d = 0 great circle -> Đường tròn lớn (I; IM)
      const d0Sub = withSubEntities(SPHERE_D0_HORIZONTAL_SCENE);
      registerExactSceneOrigin(d0Sub, SPHERE_D0_HORIZONTAL_SCENE);
      const d0Plan = buildPedagogicalConstructionPlan(d0Sub);
      const d0Circle = d0Plan.scene.objects.find((o) => o.id === "c_d0")!;
      expect(formatCompactEntityChipLabel(d0Plan.scene, d0Circle)).toBe("Đường tròn lớn (I; IM)");

      // Cylinder cross-section tru-thiet-dien-tron -> Đáy tròn (O; OA) or Đáy tròn (O; R = 2), and section Đường tròn (M; r) (NO leak of target radius 2!)
      const cylPlan = buildPedagogicalConstructionPlan(sampleScene("tru-thiet-dien-tron"));
      const cylSec = cylPlan.scene.objects.find((o) => o.id === "C")!;
      const cylSecLabel = formatCompactEntityChipLabel(cylPlan.scene, cylSec);
      expect(cylSecLabel).toBe("Đường tròn (M; r)");
      expect(cylSecLabel).not.toContain("2");

      for (const bObj of cylPlan.scene.objects.filter((o) => o.type === "circle3" && o.surface_role === "BASE_REGION")) {
        const bChip = formatCompactEntityChipLabel(cylPlan.scene, bObj);
        expect(bChip).toMatch(/^Đáy tròn \([^;]+;\s*[^)]+\)$/u);
      }

      // Cone axial section non-thiet-dien-truc -> Thiết diện (SAB)
      const conePlan = buildPedagogicalConstructionPlan(sampleScene("non-thiet-dien-truc"));
      const coneSec = conePlan.scene.objects.find((o) => o.id === "td")!;
      expect(formatCompactEntityChipLabel(conePlan.scene, coneSec)).toBe("Thiết diện (SAB)");
    });

    it("3b. Preserves certified ⊥ symbols on visible foundation altitudes/axes (subordinated, never deleted) across pyramid, cube, and cylinder sections", () => {
      // Pyramid section thiet-dien-chop -> SA keeps ⊥ at A
      const chopPlan = buildPedagogicalConstructionPlan(sampleScene("thiet-dien-chop"));
      const chopFinal = chopPlan.steps[chopPlan.steps.length - 1]!.anchor;
      const chopRoles = resolveStepVisualRoles(chopPlan.scene, chopFinal, { auxiliaryShown: false, selectedId: null });
      const saObj = chopPlan.scene.objects.find((o) => Boolean(o.perpendicular_witness))!;
      expect(chopRoles.get(saObj.id)?.showPerpWitnessSymbol).toBe(true);
      expect(chopRoles.get(saObj.id)?.perpWitnessOpacityScale).toBeGreaterThanOrEqual(0.4);

      // Cube hexagonal section -> PP' keeps ⊥ at P
      const cubeSub = withSubEntities(CUBE_HEXAGONAL_SECTION_SCENE);
      registerExactSceneOrigin(cubeSub, CUBE_HEXAGONAL_SECTION_SCENE);
      const cubePlan = buildPedagogicalConstructionPlan(cubeSub);
      const cubeFinal = cubePlan.steps[cubePlan.steps.length - 1]!.anchor;
      const cubeRoles = resolveStepVisualRoles(cubePlan.scene, cubeFinal, { auxiliaryShown: false, selectedId: null });
      expect(cubeRoles.get("canh_PPp")?.showPerpWitnessSymbol).toBe(true);

      // Cylinder section -> axis keeps ⊥ at base
      const cylPlan = buildPedagogicalConstructionPlan(sampleScene("tru-thiet-dien-tron"));
      const cylFinal = cylPlan.steps[cylPlan.steps.length - 1]!.anchor;
      const cylRoles = resolveStepVisualRoles(cylPlan.scene, cylFinal, { auxiliaryShown: false, selectedId: null });
      expect(cylRoles.get("tru__axis")?.showPerpWitnessSymbol).toBe(true);
    });

    it("3c. Inclined and near-center sphere cuts emit zero synthetic perp_plane_ray stubs at Step 3 and align 0° grounded perp_marker with HM at Step 4", () => {
      const incSub = withSubEntities(SPHERE_INCLINED_CUT_SCENE);
      registerExactSceneOrigin(incSub, SPHERE_INCLINED_CUT_SCENE);
      const incPlan = buildPedagogicalConstructionPlan(incSub);
      const ihObj = incPlan.scene.objects.find((o) => o.id === "c_q__dist")!;
      const hmObj = incPlan.scene.objects.find((o) => o.id === "c_q__sec_rad")!;
      const step3 = incPlan.steps.find((st) => st.targetIds.includes("c_q__dist"))!;
      const step4 = incPlan.steps.find((st) => st.targetIds.includes("c_q__sec_rad"))!;
      const visStep3 = incPlan.scene.objects.filter((o) => step3.visibleIds.includes(o.id));
      const visStep4 = incPlan.scene.objects.filter((o) => step4.visibleIds.includes(o.id));
      const built3 = buildObject3D(
        ihObj,
        false,
        0.1,
        [[0, 0, 0], [5, 5, 5]],
        new THREE.Vector3(10, -10, 8),
        undefined,
        undefined,
        false,
        "primary",
        true,
        true,
        false,
        incPlan.scene,
        undefined,
        undefined,
        undefined,
        visStep3,
      )!;
      expect(built3.getObjectByName(`perp_plane_ray:${ihObj.id}`)).toBeUndefined();
      expect(built3.getObjectByName(`perp_marker:${ihObj.id}`)).toBeUndefined();

      const built4 = buildObject3D(
        ihObj,
        false,
        0.1,
        [[0, 0, 0], [5, 5, 5]],
        new THREE.Vector3(10, -10, 8),
        undefined,
        undefined,
        false,
        "primary",
        true,
        true,
        false,
        incPlan.scene,
        undefined,
        undefined,
        undefined,
        visStep4,
      )!;
      expect(built4.getObjectByName(`perp_plane_ray:${ihObj.id}`)).toBeUndefined();
      const incMarker4 = built4.getObjectByName(`perp_marker:${ihObj.id}`)!;
      expect(incMarker4).toBeDefined();
      const markerU = new THREE.Vector3(...(incMarker4.userData.gocVuongDonVi.u as [number, number, number])).normalize();
      const hmDir = new THREE.Vector3(
        toNumber(hmObj.point_b![0]) - toNumber(hmObj.point_a![0]),
        toNumber(hmObj.point_b![1]) - toNumber(hmObj.point_a![1]),
        toNumber(hmObj.point_b![2]) - toNumber(hmObj.point_a![2]),
      ).normalize();
      expect(Math.abs(markerU.dot(hmDir))).toBeGreaterThan(0.9999);

      // Short IH = 1 in SPHERE_NEAR_CENTER_SCENE (r² = 24, no rational HM): zero ungrounded perp_plane_ray / perp_marker
      const ncSub = withSubEntities(SPHERE_NEAR_CENTER_SCENE);
      registerExactSceneOrigin(ncSub, SPHERE_NEAR_CENTER_SCENE);
      const ncPlan = buildPedagogicalConstructionPlan(ncSub);
      const ncDist = ncPlan.scene.objects.find((o) => o.id === "c_nc__dist")!;
      const ncStepFinal = ncPlan.steps[ncPlan.steps.length - 1]!;
      const builtNc = buildObject3D(
        ncDist,
        false,
        0.1,
        [[0, 0, 0], [5, 5, 5]],
        new THREE.Vector3(10, -10, 8),
        undefined,
        undefined,
        false,
        "primary",
        true,
        true,
        false,
        ncPlan.scene,
        undefined,
        undefined,
        undefined,
        ncPlan.scene.objects.filter((o) => ncStepFinal.visibleIds.includes(o.id)),
      )!;
      expect(builtNc.getObjectByName(`perp_plane_ray:${ncDist.id}`)).toBeUndefined();
      expect(builtNc.getObjectByName(`perp_marker:${ncDist.id}`)).toBeUndefined();

      // Near-center cut with rational radius (d = 7/5, R = 5 => r² = 576/25, r = 24/5): HM grounds perp_marker at Step 4 with bounded s0
      const ncRatRaw: Scene3D = {
        ...SPHERE_NEAR_CENTER_SCENE,
        objects: SPHERE_NEAR_CENTER_SCENE.objects.map((o) =>
          o.id === "mp_nc"
            ? { ...o, point: ["0", "0", "7/5"] }
            : o.id === "c_nc"
              ? { ...o, center: ["0", "0", "7/5"], radius_sq: "576/25" }
              : o,
        ),
      };
      const ncRatSub = withSubEntities(ncRatRaw);
      registerExactSceneOrigin(ncRatSub, ncRatRaw);
      const ncRatPlan = buildPedagogicalConstructionPlan(ncRatSub);
      const ncRatDist = ncRatPlan.scene.objects.find((o) => o.id === "c_nc__dist")!;
      const ncRatStep4 = ncRatPlan.steps.find((st) => st.targetIds.includes("c_nc__sec_rad"))!;
      const builtNcRat = buildObject3D(
        ncRatDist,
        false,
        0.1,
        [[0, 0, 0], [5, 5, 5]],
        new THREE.Vector3(10, -10, 8),
        undefined,
        undefined,
        false,
        "primary",
        true,
        true,
        false,
        ncRatPlan.scene,
        undefined,
        undefined,
        undefined,
        ncRatPlan.scene.objects.filter((o) => ncRatStep4.visibleIds.includes(o.id)),
      )!;
      expect(builtNcRat.getObjectByName(`perp_plane_ray:${ncRatDist.id}`)).toBeUndefined();
      let s0 = 0;
      builtNcRat.traverse((ch) => {
        if (ch.userData?.gocVuongDonVi?.s0) s0 = ch.userData.gocVuongDonVi.s0;
      });
      expect(s0).toBeGreaterThan(0);
      expect(s0).toBeLessThanOrEqual(0.35 * 1.4 + 1e-6);
    });
  });

  describe("§4 & §5 — Cross-Family Continuity & Non-Disappearing Auxiliary Lines Across All 10 Representative Scenarios", () => {
    it("4a. Regular pyramid S.EFGH synthesizes base diagonals EG and FH for center O, keeps them as active evidence during foundation, and retires them to COMPLETED_AUXILIARY on post-foundation steps without deleting from Scene3D", () => {
      const pyrSub = withSubEntities(REGULAR_PYRAMID_SECTION_SCENE);
      registerExactSceneOrigin(pyrSub, REGULAR_PYRAMID_SECTION_SCENE);
      const pyrPlan = buildPedagogicalConstructionPlan(pyrSub);
      const diag1 = pyrPlan.scene.objects.find((o) => o.id === "O__diag_1");
      const diag2 = pyrPlan.scene.objects.find((o) => o.id === "O__diag_2");
      expect(diag1).toBeDefined();
      expect(diag2).toBeDefined();

      const stepSO = pyrPlan.steps.find((s) => s.targetIds.includes("cao_SO"))!;
      const soRoles = resolveStepVisualRoles(pyrPlan.scene, stepSO.anchor, { auxiliaryShown: false, selectedId: null });
      expect(soRoles.get("O__diag_1")?.visible).toBe(true);
      expect(soRoles.get("O__diag_1")?.opacityScale).toBeLessThanOrEqual(0.45);
      expect(soRoles.get("O__diag_2")?.visible).toBe(true);
      expect(soRoles.get("O__diag_2")?.opacityScale).toBeLessThanOrEqual(0.45);

      const finalAnchor = pyrPlan.steps[pyrPlan.steps.length - 1]!.anchor;
      const finalRoles = resolveStepVisualRoles(pyrPlan.scene, finalAnchor, { auxiliaryShown: false, selectedId: null });
      expect(finalRoles.get("O__diag_1")?.presentationTier).toBe("COMPLETED_AUXILIARY");
      expect(finalRoles.get("O__diag_1")?.visible).toBe(false);
      expect(finalRoles.get("O__diag_2")?.presentationTier).toBe("COMPLETED_AUXILIARY");
      expect(finalRoles.get("O__diag_2")?.visible).toBe(false);
      expect(finalRoles.get("cao_SO")?.visible).toBe(true);
      expect(finalRoles.get("cao_SO")?.showPerpWitnessSymbol).toBe(true);

      const finalRolesAuxShown = resolveStepVisualRoles(pyrPlan.scene, finalAnchor, { auxiliaryShown: true, selectedId: null });
      expect(finalRolesAuxShown.get("O__diag_1")?.visible).toBe(true);
      expect(finalRolesAuxShown.get("O__diag_2")?.visible).toBe(true);
    });

    it("4b. Verifies mathematical consistency, construction continuity, visual continuity, and forward/backward/jump determinism across all 10 scenarios", () => {
      const scenarios: { name: string; raw: Scene3D }[] = [
        { name: "1a-sphere-pure-IR", raw: PURE_STANDALONE_SPHERE_SCENE },
        { name: "1b-sphere-given-A", raw: sampleRawScene("cau-the-tich") },
        { name: "2-sphere-horizontal-cut", raw: sampleRawScene("cau-cat-mat-phang") },
        { name: "3-sphere-inclined-cut", raw: SPHERE_INCLINED_CUT_SCENE },
        { name: "4-sphere-through-center", raw: SPHERE_D0_HORIZONTAL_SCENE },
        { name: "4b-sphere-near-center", raw: SPHERE_NEAR_CENTER_SCENE },
        { name: "5-sphere-tangent", raw: SPHERE_TANGENT_SCENE },
        { name: "6-sphere-disjoint", raw: SPHERE_DISJOINT_SCENE },
        { name: "7-cylinder-perp-section", raw: sampleRawScene("tru-thiet-dien-tron") },
        { name: "8-cone-axial-section", raw: sampleRawScene("non-thiet-dien-truc") },
        { name: "9a-pyramid-section-sample", raw: sampleRawScene("thiet-dien-chop") },
        { name: "9b-regular-pyramid-section", raw: REGULAR_PYRAMID_SECTION_SCENE },
        { name: "10-cube-hexagonal-section", raw: CUBE_HEXAGONAL_SECTION_SCENE },
      ];

      // Also assert fail-closed when a disjoint plane (d > R) falsely claims CONSTRUCT_CUTTING_OBJECT
      const badDisjoint: Scene3D = {
        ...SPHERE_DISJOINT_SCENE,
        objects: SPHERE_DISJOINT_SCENE.objects.map((o) =>
          o.id === "mp_dis" ? { ...o, formation_roles: ["CONSTRUCT_CUTTING_OBJECT"] } : o,
        ),
      };
      expect(verifySceneMathematicalConsistency(badDisjoint).valid).toBe(false);

      for (const sc of scenarios) {
        const sub = withSubEntities(sc.raw);
        registerExactSceneOrigin(sub, sc.raw);
        const plan = buildPedagogicalConstructionPlan(sub);
        const mathCheck = verifySceneMathematicalConsistency(plan.scene);
        expect(mathCheck.valid, `${sc.name} math: ${JSON.stringify(mathCheck.contradictions)}`).toBe(true);

        const contCheck = verifyConstructionContinuity(plan.scene);
        expect(contCheck.valid, `${sc.name} continuity: ${JSON.stringify(contCheck.violations)}`).toBe(true);

        const visCheck = verifyVisualContinuity(plan.scene);
        expect(visCheck.valid, `${sc.name} visual: ${JSON.stringify(visCheck.violations)}`).toBe(true);

        const steps = pedagogicalStepList(plan.scene);
        const forwardRoles = steps.map((st) => [...resolveStepVisualRoles(plan.scene, st.anchor, { auxiliaryShown: false, selectedId: null }).entries()]);
        const backwardRoles = [...steps]
          .reverse()
          .map((st) => [...resolveStepVisualRoles(plan.scene, st.anchor, { auxiliaryShown: false, selectedId: null }).entries()])
          .reverse();
        expect(backwardRoles, `${sc.name} forward/backward determinism`).toEqual(forwardRoles);
      }
    });
  });
});
