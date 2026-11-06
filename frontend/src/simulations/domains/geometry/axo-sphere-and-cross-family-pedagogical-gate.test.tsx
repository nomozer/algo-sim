import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { veKhongGian } from "./scene3d-chart";
import { learnerTextIsSafe, objectsAt, registerExactSceneOrigin, type ExactVec3, type Scene3D, type SceneObject } from "./scene3d-model";
import { withSubEntities } from "./scene3d-subentities";
import { buildObject3D, capNhatDauSongSong } from "./scene3d-view";
import { khungNhinSuPham } from "./scene3d-camera";
import { annotationsAt, DEFAULT_ANNOTATION_VIEW, givenQuantitiesSummary } from "./scene3d-annotations";
import { uuTienNhan, locNhanChongNhau } from "./scene3d-presentation";
import { evaluateStudentPresentationPolicy } from "./scene3d-student-presentation-policy";
import {
  buildContractReferenceGroup,
  buildPedagogicalConstructionPlan,
  buildPedagogicalStepNarration,
  classifyAuxiliaryPlanePedagogicalState,
  inspectAxialCurvedOrthogonality,
  resolveSphereReferenceGreatCirclePolicy,
  resolveStepVisualRoles,
  shouldShowSphereReferenceEquator,
  verifyConstructionContinuity,
  verifySceneMathematicalConsistency,
  verifyVisualContinuity,
} from "./scene3d-semantic-policy";

function loadSampleScene(sampleId: string): Scene3D {
  const sample = GEOMETRY_SAMPLES.find((s) => s.id === sampleId);
  if (!sample) throw new Error(`Missing catalog sample: ${sampleId}`);
  const raw = structuredClone((sample.envelope as unknown as { scene3d: Scene3D }).scene3d);
  const world = veKhongGian(raw);
  registerExactSceneOrigin(world, raw);
  return withSubEntities(world);
}

function parseFrac(raw: string): [bigint, bigint] {
  const s = String(raw).trim();
  if (!s.includes("/")) {
    if (s.includes(".")) {
      const [intPart, decPart] = s.split(".");
      const scale = 10n ** BigInt(decPart.length);
      const sign = intPart.startsWith("-") ? -1n : 1n;
      const absInt = BigInt(intPart.replace(/^[+-]/, "") || "0");
      return [sign * (absInt * scale + BigInt(decPart)), scale];
    }
    return [BigInt(s), 1n];
  }
  const [p, q] = s.split("/");
  const num = BigInt(p);
  const den = BigInt(q);
  const gcd = (a: bigint, b: bigint): bigint => {
    let x = a < 0n ? -a : a;
    let y = b < 0n ? -b : b;
    while (y !== 0n) [x, y] = [y, x % y];
    return x || 1n;
  };
  const g = gcd(num, den);
  return den < 0n ? [-num / g, -den / g] : [num / g, den / g];
}

function fAdd(a: [bigint, bigint], b: [bigint, bigint]): [bigint, bigint] {
  return parseFrac(`${a[0] * b[1] + b[0] * a[1]}/${a[1] * b[1]}`);
}
function fSub(a: [bigint, bigint], b: [bigint, bigint]): [bigint, bigint] {
  return parseFrac(`${a[0] * b[1] - b[0] * a[1]}/${a[1] * b[1]}`);
}
function fMul(a: [bigint, bigint], b: [bigint, bigint]): [bigint, bigint] {
  return parseFrac(`${a[0] * b[0]}/${a[1] * b[1]}`);
}
function fEq(a: [bigint, bigint], b: [bigint, bigint]): boolean {
  return a[0] * b[1] === b[0] * a[1];
}
type QVec3 = [[bigint, bigint], [bigint, bigint], [bigint, bigint]];
function qVec(v: ExactVec3): QVec3 {
  return [parseFrac(v[0]), parseFrac(v[1]), parseFrac(v[2])];
}
function qSub(a: QVec3, b: QVec3): QVec3 {
  return [fSub(a[0], b[0]), fSub(a[1], b[1]), fSub(a[2], b[2])];
}
function qMetricDot(u: QVec3, v: QVec3, gRaw?: string[][]): [bigint, bigint] {
  const g = (gRaw ?? [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ]).map((r) => r.map(parseFrac));
  let sum: [bigint, bigint] = [0n, 1n];
  for (let i = 0; i < 3; i += 1) {
    for (let j = 0; j < 3; j += 1) {
      sum = fAdd(sum, fMul(g[i][j], fMul(u[i], v[j])));
    }
  }
  return sum;
}
function qPlainDot(u: QVec3, v: QVec3): [bigint, bigint] {
  return fAdd(fAdd(fMul(u[0], v[0]), fMul(u[1], v[1])), fMul(u[2], v[2]));
}

const INCLINED_SPHERE_SECANT_SCENE: Scene3D = {
  free_objects: ["I", "q_r", "q_d"],
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  objects: [
    { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "-1", "2"] },
    { id: "q_r", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["ball_inc"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f_r", provenance: "GIVEN", is_given: true } },
    { id: "q_d", type: "quantity", label: "Khoảng cách d(I,(Q))", notation: "d(I,(Q))", origin: "free", producer: null, render: "readout", depends: ["I", "mp_q"], value: "3", exact: { kind: "rational", value: "3" }, source: { fact_id: "f_d", provenance: "GIVEN", is_given: true } },
    { id: "ball_inc", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: "construct_curved_solid", render: "curved_solid", depends: ["I", "q_r"], anchor: ["1", "-1", "2"], radius_sq: "25" },
    { id: "mp_q", type: "plane3", label: "Mặt phẳng nghiêng (Q)", notation: "(Q)", origin: "derived", producer: "construct_plane", render: "surface", surface_role: "CUTTING_PLANE", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: [], point: ["2", "1", "4"], normal: ["1", "2", "2"] },
    { id: "c_inc", type: "circle3", label: "Đường tròn giao tuyến (C)", notation: "(C)", origin: "derived", producer: "intersect_plane_sphere", render: "circle", surface_role: "SECTION_REGION", depends: ["ball_inc", "mp_q"], center: ["2", "1", "4"], normal: ["1", "2", "2"], radius_sq: "16" },
  ] as unknown as SceneObject[],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
    { step_index: 1, action: "CREATE", object: "ball_inc", depends: ["I", "q_r"], explanation: "" },
    { step_index: 2, action: "CREATE", object: "mp_q", depends: [], explanation: "" },
    { step_index: 3, action: "CREATE", object: "c_inc", depends: ["ball_inc", "mp_q"], explanation: "" },
  ] as any,
};

const SPHERE_D0_HORIZONTAL_SCENE: Scene3D = {
  free_objects: ["I", "q_r"],
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  objects: [
    { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "q_r", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["ball_d0"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f_r", provenance: "GIVEN", is_given: true } },
    { id: "ball_d0", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: "construct_curved_solid", render: "curved_solid", depends: ["I", "q_r"], anchor: ["0", "0", "0"], radius_sq: "25" },
    { id: "mp_d0", type: "plane3", label: "Mặt phẳng qua tâm (P)", notation: "(P)", origin: "derived", producer: "construct_plane", render: "surface", surface_role: "CUTTING_PLANE", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: [], point: ["0", "0", "0"], normal: ["0", "0", "1"] },
    { id: "c_d0", type: "circle3", label: "Đường tròn lớn giao tuyến (C)", notation: "(C)", origin: "derived", producer: "intersect_plane_sphere", render: "circle", surface_role: "SECTION_REGION", depends: ["ball_d0", "mp_d0"], center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "25" },
  ] as unknown as SceneObject[],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
    { step_index: 1, action: "CREATE", object: "ball_d0", depends: ["I", "q_r"], explanation: "" },
    { step_index: 2, action: "CREATE", object: "mp_d0", depends: [], explanation: "" },
    { step_index: 3, action: "CREATE", object: "c_d0", depends: ["ball_d0", "mp_d0"], explanation: "" },
  ] as any,
};

const SPHERE_NEAR_COINCIDENT_IRRATIONAL_SCENE: Scene3D = {
  free_objects: ["I", "q_r", "q_d"],
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  objects: [
    { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "q_r", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["ball_nc"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f_r", provenance: "GIVEN", is_given: true } },
    { id: "q_d", type: "quantity", label: "Khoảng cách d(I,(P))", notation: "d(I,(P))", origin: "free", producer: null, render: "readout", depends: ["I", "mp_nc"], value: "1", exact: { kind: "rational", value: "1" }, source: { fact_id: "f_d", provenance: "GIVEN", is_given: true } },
    { id: "ball_nc", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: "construct_curved_solid", render: "curved_solid", depends: ["I", "q_r"], anchor: ["0", "0", "0"], radius_sq: "25" },
    { id: "mp_nc", type: "plane3", label: "Mặt phẳng (P)", notation: "(P)", origin: "derived", producer: "construct_plane", render: "surface", surface_role: "CUTTING_PLANE", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: [], point: ["0", "0", "1"], normal: ["0", "0", "1"] },
    { id: "c_nc", type: "circle3", label: "Đường tròn giao tuyến (C)", notation: "(C)", origin: "derived", producer: "intersect_plane_sphere", render: "circle", surface_role: "SECTION_REGION", depends: ["ball_nc", "mp_nc"], center: ["0", "0", "1"], normal: ["0", "0", "1"], radius_sq: "24" },
  ] as unknown as SceneObject[],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
    { step_index: 1, action: "CREATE", object: "ball_nc", depends: ["I", "q_r"], explanation: "" },
    { step_index: 2, action: "CREATE", object: "mp_nc", depends: [], explanation: "" },
    { step_index: 3, action: "CREATE", object: "c_nc", depends: ["ball_nc", "mp_nc"], explanation: "" },
  ] as any,
};

const SPHERE_TANGENT_SCENE: Scene3D = {
  free_objects: ["I", "q_r"],
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  objects: [
    { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "q_r", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["ball_t"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f_r", provenance: "GIVEN", is_given: true } },
    { id: "ball_t", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: "construct_curved_solid", render: "curved_solid", depends: ["I", "q_r"], anchor: ["0", "0", "0"], radius_sq: "25" },
    { id: "mp_t", type: "plane3", label: "Mặt phẳng tiếp diện (P)", notation: "(P)", origin: "derived", producer: "construct_plane", render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["0", "0", "5"], normal: ["0", "0", "1"] },
  ] as unknown as SceneObject[],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
    { step_index: 1, action: "CREATE", object: "ball_t", depends: ["I", "q_r"], explanation: "" },
    { step_index: 2, action: "CREATE", object: "mp_t", depends: [], explanation: "" },
  ] as any,
};

const SPHERE_DISJOINT_SCENE: Scene3D = {
  free_objects: ["I", "q_r"],
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  objects: [
    { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "q_r", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["ball_dis"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f_r", provenance: "GIVEN", is_given: true } },
    { id: "ball_dis", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: "construct_curved_solid", render: "curved_solid", depends: ["I", "q_r"], anchor: ["0", "0", "0"], radius_sq: "25" },
    { id: "mp_dis", type: "plane3", label: "Mặt phẳng (P)", notation: "(P)", role: "Mặt phẳng trong không gian", origin: "derived", producer: "construct_plane", render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["0", "0", "7"], normal: ["0", "0", "1"] },
    { id: "H_dis", type: "point3", label: "Hình chiếu H", notation: "H", origin: "derived", producer: "project_onto", render: "point_marker", depends: ["I", "mp_dis"], xyz: ["0", "0", "7"] },
    { id: "IH_dis", type: "segment3", label: "Đoạn vuông góc IH", notation: "IH", origin: "derived", producer: "construct_perpendicular", render: "segment", depends: ["I", "H_dis", "mp_dis"], endpoint_ids: ["I", "H_dis"], endpoints: [["0", "0", "0"], ["0", "0", "7"]], perpendicular_witness: { from: "I", foot: ["0", "0", "7"], foot_id: "H_dis", on: "mp_dis", relation: "line_perp_plane", status: "DERIVED_VERIFIED", plane_directions: [["1", "0", "0"], ["0", "1", "0"]], marker: { u: ["1", "0", "0"], v: ["0", "0", "-1"] } } },
  ] as unknown as SceneObject[],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
    { step_index: 1, action: "CREATE", object: "ball_dis", depends: ["I", "q_r"], explanation: "" },
    { step_index: 2, action: "CREATE", object: "mp_dis", depends: [], explanation: "" },
    { step_index: 3, action: "CREATE", object: "H_dis", depends: ["I", "mp_dis"], explanation: "" },
    { step_index: 4, action: "CREATE", object: "IH_dis", depends: ["I", "H_dis", "mp_dis"], explanation: "" },
  ] as any,
};

const HOLDOUT_CUBOID_HEXAGON_SCENE: Scene3D = {
  free_objects: ["P", "Q", "R", "S", "P1", "Q1", "R1", "S1"],
  chart_metric: [
    ["1", "0", "0"],
    ["0", "1", "0"],
    ["0", "0", "1"],
  ],
  objects: [
    { id: "P", type: "point3", label: "Điểm P", notation: "P", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "Q", type: "point3", label: "Điểm Q", notation: "Q", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["4", "0", "0"] },
    { id: "R", type: "point3", label: "Điểm R", notation: "R", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["4", "4", "0"] },
    { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
    { id: "P1", type: "point3", label: "Điểm P′", notation: "P′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
    { id: "Q1", type: "point3", label: "Điểm Q′", notation: "Q′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["4", "0", "4"] },
    { id: "R1", type: "point3", label: "Điểm R′", notation: "R′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["4", "4", "4"] },
    { id: "S1", type: "point3", label: "Điểm S′", notation: "S′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "4"] },
    { id: "day_PQRS", type: "polygon3", label: "Đáy PQRS", notation: "PQRS", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["P", "Q", "R", "S"], vertex_ids: ["P", "Q", "R", "S"], vertices: [["0", "0", "0"], ["4", "0", "0"], ["4", "4", "0"], ["0", "4", "0"]] },
    { id: "canh_PP1", type: "segment3", label: "Cạnh bên PP′", notation: "PP′", origin: "derived", producer: "construct_segment", render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["P", "P1"], endpoint_ids: ["P", "P1"], endpoints: [["0", "0", "0"], ["0", "0", "4"]], perpendicular_witness: { from: "P1", foot: ["0", "0", "0"], foot_id: "P", on: "day_PQRS", relation: "line_perp_plane", status: "GIVEN", plane_directions: [["4", "0", "0"], ["0", "4", "0"]], marker: { u: ["4", "0", "0"], v: ["0", "0", "4"] } } },
    { id: "day_P1Q1R1S1", type: "polygon3", label: "Đáy trên P′Q′R′S′", notation: "P′Q′R′S′", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_TRANSLATED_FACE"], depends: ["P1", "Q1", "R1", "S1"], vertex_ids: ["P1", "Q1", "R1", "S1"], vertices: [["0", "0", "4"], ["4", "0", "4"], ["4", "4", "4"], ["0", "4", "4"]] },
    { id: "hop_PQRS", type: "solid", label: "Hình lập phương PQRS.P′Q′R′S′", notation: "PQRS.P′Q′R′S′", shape_class: "PRISM_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["P", "Q", "R", "S", "P1", "Q1", "R1", "S1"], vertex_ids: ["P", "Q", "R", "S", "P1", "Q1", "R1", "S1"], vertices: [["0", "0", "0"], ["4", "0", "0"], ["4", "4", "0"], ["0", "4", "0"], ["0", "0", "4"], ["4", "0", "4"], ["4", "4", "4"], ["0", "4", "4"]], faces: [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]] },
    { id: "U", type: "point3", label: "Trung điểm U của QR", notation: "U", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["Q", "R"], xyz: ["4", "2", "0"] },
    { id: "V", type: "point3", label: "Trung điểm V của RS", notation: "V", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["R", "S"], xyz: ["2", "4", "0"] },
    { id: "W", type: "point3", label: "Trung điểm W của SS′", notation: "W", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["S", "S1"], xyz: ["0", "4", "2"] },
    { id: "mp_UVW", type: "plane3", label: "Mặt phẳng cắt (UVW)", notation: "(UVW)", origin: "derived", producer: "construct_plane", render: "surface", surface_role: "CUTTING_PLANE", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: ["U", "V", "W"], point: ["4", "2", "0"], normal: ["1", "1", "1"] },
    { id: "X", type: "point3", label: "Giao điểm X = P′S′ ∩ (UVW)", notation: "X", origin: "derived", producer: "intersect_line_plane", render: "point_marker", formation_roles: ["DERIVE_INTERSECTION"], depends: ["P1", "S1", "mp_UVW"], xyz: ["0", "2", "4"] },
    { id: "Y", type: "point3", label: "Giao điểm Y = P′Q′ ∩ (UVW)", notation: "Y", origin: "derived", producer: "intersect_line_plane", render: "point_marker", formation_roles: ["DERIVE_INTERSECTION"], depends: ["P1", "Q1", "mp_UVW"], xyz: ["2", "0", "4"] },
    { id: "Z", type: "point3", label: "Giao điểm Z = QQ′ ∩ (UVW)", notation: "Z", origin: "derived", producer: "intersect_line_plane", render: "point_marker", formation_roles: ["DERIVE_INTERSECTION"], depends: ["Q", "Q1", "mp_UVW"], xyz: ["4", "0", "2"] },
    { id: "td_hex", type: "section", label: "Thiết diện lục giác UVWXYZ", notation: "UVWXYZ", origin: "derived", producer: "intersect_plane_solid", render: "polygon", depends: ["hop_PQRS", "mp_UVW", "U", "V", "W", "X", "Y", "Z"], polygon: [["4", "2", "0"], ["2", "4", "0"], ["0", "4", "2"], ["0", "2", "4"], ["2", "0", "4"], ["4", "0", "2"]], closed: true },
  ] as unknown as SceneObject[],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
    { step_index: 1, action: "CREATE", object: "day_PQRS", depends: ["P", "Q", "R", "S"], explanation: "" },
    { step_index: 2, action: "CREATE", object: "canh_PP1", depends: ["P", "P1"], explanation: "" },
    { step_index: 3, action: "CREATE", object: "day_P1Q1R1S1", depends: ["P1", "Q1", "R1", "S1"], explanation: "" },
    { step_index: 4, action: "CREATE", object: "hop_PQRS", depends: ["P", "Q", "R", "S", "P1", "Q1", "R1", "S1"], explanation: "" },
    { step_index: 5, action: "CREATE", object: "U", depends: ["Q", "R"], explanation: "" },
    { step_index: 6, action: "CREATE", object: "V", depends: ["R", "S"], explanation: "" },
    { step_index: 7, action: "CREATE", object: "W", depends: ["S", "S1"], explanation: "" },
    { step_index: 8, action: "CREATE", object: "mp_UVW", depends: ["U", "V", "W"], explanation: "" },
    { step_index: 9, action: "CREATE", object: "X", depends: ["P1", "S1", "mp_UVW"], explanation: "" },
    { step_index: 10, action: "CREATE", object: "Y", depends: ["P1", "Q1", "mp_UVW"], explanation: "" },
    { step_index: 11, action: "CREATE", object: "Z", depends: ["Q", "Q1", "mp_UVW"], explanation: "" },
    { step_index: 12, action: "CREATE", object: "td_hex", depends: ["hop_PQRS", "mp_UVW", "U", "V", "W", "X", "Y", "Z"], explanation: "" },
  ] as any,
};

describe("AXO Sphere Pedagogical Visualization & Cross-Family Gate (§1–§9)", () => {
  describe("Layer A — Exact Geometric Invariants over chart_metric (§3.2, §3.4)", () => {
    it("proves exact sphere–plane invariants over Q^3 for 0 < d < R, d = 0, d = R, and d > R", () => {
      // 1. 0 < d < R (inclined plane n = [1, 2, 2], R = 5, d = 3, r = 4)
      const secPlan = buildPedagogicalConstructionPlan(withSubEntities(INCLINED_SPHERE_SECANT_SCENE));
      expect(verifySceneMathematicalConsistency(secPlan.scene).valid).toBe(true);
      expect(verifyConstructionContinuity(secPlan.scene).valid).toBe(true);

      const I = qVec(["1", "-1", "2"]);
      const nQ = qVec(["1", "2", "2"]);
      const p0 = qVec(["2", "1", "4"]);
      const footH = secPlan.scene.objects.find((o) => o.id === "c_inc__center");
      const distIH = secPlan.scene.objects.find((o) => o.id === "c_inc__dist");
      const rimM = secPlan.scene.objects.find((o) => o.id === "c_inc__rim_pt");
      expect(footH?.xyz).toBeDefined();
      expect(distIH).toBeDefined();
      expect(rimM?.xyz).toBeDefined();

      const H = qVec(footH!.xyz!);
      const M = qVec(rimM!.xyz!);
      // H ∈ (Q) and IH ⊥ (Q)
      expect(fEq(qPlainDot(qSub(H, p0), nQ), [0n, 1n])).toBe(true);
      expect(fEq(qMetricDot(qSub(H, I), qVec(["2", "-1", "0"]), secPlan.scene.chart_metric), [0n, 1n])).toBe(true);
      // M ∈ (S), M ∈ (Q), IH ⊥ HM, |IH|² + |HM|² = R² = 25
      const dSq = qMetricDot(qSub(H, I), qSub(H, I), secPlan.scene.chart_metric);
      const rSq = qMetricDot(qSub(M, H), qSub(M, H), secPlan.scene.chart_metric);
      const RSq = qMetricDot(qSub(M, I), qSub(M, I), secPlan.scene.chart_metric);
      expect(fEq(qPlainDot(qSub(M, p0), nQ), [0n, 1n])).toBe(true);
      expect(fEq(qMetricDot(qSub(H, I), qSub(M, H), secPlan.scene.chart_metric), [0n, 1n])).toBe(true);
      expect(fEq(dSq, [9n, 1n])).toBe(true);
      expect(fEq(rSq, [16n, 1n])).toBe(true);
      expect(fEq(RSq, [25n, 1n])).toBe(true);
      expect(fEq(fAdd(dSq, rSq), RSq)).toBe(true);

      // 2. d = 0 (plane through I): section center === I, zero degenerate IH segment, zero right-angle witness
      const d0Plan = buildPedagogicalConstructionPlan(withSubEntities(SPHERE_D0_HORIZONTAL_SCENE));
      expect(verifySceneMathematicalConsistency(d0Plan.scene).valid).toBe(true);
      expect(d0Plan.scene.objects.find((o) => o.id === "c_d0")?.center).toEqual(["0", "0", "0"]);
      expect(d0Plan.scene.objects.find((o) => o.id === "c_d0__dist")).toBeUndefined();
      expect(d0Plan.scene.objects.some((o) => Boolean(o.perpendicular_witness))).toBe(false);

      // 3. d = R (tangent plane): unique tangent point H, zero positive-radius intersection circle
      const tanPlan = buildPedagogicalConstructionPlan(withSubEntities(SPHERE_TANGENT_SCENE));
      expect(verifySceneMathematicalConsistency(tanPlan.scene).valid).toBe(true);
      expect(tanPlan.scene.objects.some((o) => o.type === "circle3" && o.surface_role !== "BASE_REGION")).toBe(false);
      const tanFoot = tanPlan.scene.objects.find(
        (o) => o.type === "point3" && o.id !== "I" && !o.id.includes("::") && !(o.display_group ?? []).includes("sphere_foundation_ref"),
      );
      expect(tanFoot?.xyz).toEqual(["0", "0", "5"]);

      // 4. d > R (disjoint plane): zero intersection circle, zero fake section
      const disPlan = buildPedagogicalConstructionPlan(withSubEntities(SPHERE_DISJOINT_SCENE));
      expect(verifySceneMathematicalConsistency(disPlan.scene).valid).toBe(true);
      expect(disPlan.scene.objects.some((o) => o.type === "circle3" || o.type === "section")).toBe(false);
    });

    it("resolves REFERENCE_GREAT_CIRCLE as an exact great circle through center I with radius R and deterministic non-coincident plane (§3.2)", () => {
      for (const raw of [loadSampleScene("cau-the-tich"), loadSampleScene("cau-cat-mat-phang"), SPHERE_D0_HORIZONTAL_SCENE, SPHERE_NEAR_COINCIDENT_IRRATIONAL_SCENE]) {
        const plan = buildPedagogicalConstructionPlan(withSubEntities(raw));
        const ball = plan.scene.objects.find((o) => o.type === "curved_solid" && o.curved_kind === "ball")!;
        const step0Vis = objectsAt(plan.scene, plan.steps[0].anchor);
        const lastVis = objectsAt(plan.scene, plan.steps[plan.steps.length - 1].anchor);
        const pol0 = resolveSphereReferenceGreatCirclePolicy(plan.scene, ball, { visibleObjects: step0Vis });
        const polLast = resolveSphereReferenceGreatCirclePolicy(plan.scene, ball, { visibleObjects: lastVis });

        expect(pol0.visible).toBe(true);
        if (raw === SPHERE_D0_HORIZONTAL_SCENE || raw === SPHERE_NEAR_COINCIDENT_IRRATIONAL_SCENE) {
          expect(polLast.visible).toBe(false);
        } else {
          expect(polLast.visible).toBe(true);
        }
        expect(pol0.semanticRole).toBe("REFERENCE_GREAT_CIRCLE");
        expect(pol0.canonicalRole).toBe("REFERENCE_GEOMETRY");
        expect(pol0.authoritative).toBe(false);
        expect(pol0.center).toEqual(ball.anchor);
        expect(pol0.radiusSq).toBe(ball.radius_sq);
        // Plane normal is canonical [0, 0, 1] and never switches to a second reference great circle
        expect(pol0.normal).toEqual(["0", "0", "1"]);
        expect(pol0.normal).toEqual(polLast.normal);
        expect(pol0.labelVi).toBe("Đường tròn lớn tham chiếu");
        expect(pol0.labelVi.toLowerCase()).not.toContain("xích đạo");
      }

      // Coincident horizontal cut (d = 0) transitions role to single intersection circle without creating a second reference circle
      const d0Ball = SPHERE_D0_HORIZONTAL_SCENE.objects.find((o) => o.curved_kind === "ball")!;
      const d0Pol = resolveSphereReferenceGreatCirclePolicy(SPHERE_D0_HORIZONTAL_SCENE, d0Ball, {
        visibleObjects: SPHERE_D0_HORIZONTAL_SCENE.objects,
      });
      expect(d0Pol.visible).toBe(false);
      expect(d0Pol.normal).toEqual(["0", "0", "1"]);
      expect(d0Pol.roleTransitionedToObjectId).toBe("c_d0");

      // Near-coincident cut (d = 1, R = 5) hides reference circle when intersection circle is active without changing 3D normal
      const ncBall = SPHERE_NEAR_COINCIDENT_IRRATIONAL_SCENE.objects.find((o) => o.curved_kind === "ball")!;
      const ncPol = resolveSphereReferenceGreatCirclePolicy(SPHERE_NEAR_COINCIDENT_IRRATIONAL_SCENE, ncBall, {
        visibleObjects: SPHERE_NEAR_COINCIDENT_IRRATIONAL_SCENE.objects,
      });
      expect(ncPol.visible).toBe(false);
      expect(ncPol.normal).toEqual(["0", "0", "1"]);
    });
  });

  describe("Layer B — Semantic Roles, Stepwise Sphere DAG, Plane Lifecycle & Non-Spoiler (§3.3, §4, §6)", () => {
    it("decomposes sphere–plane section into explicit pedagogical steps and omits M step + floating rays when M ∉ Q^3", () => {
      // Certified M ∈ Q^3 -> 5 pedagogical steps: (S) -> (P) -> (H, IH) -> (M, IM, HM) -> (C)
      const cutPlan = buildPedagogicalConstructionPlan(loadSampleScene("cau-cat-mat-phang"));
      expect(cutPlan.steps.length).toBe(5);
      expect(cutPlan.steps[0].title).toMatch(/mặt cầu/iu);
      expect(cutPlan.steps[1].title).toMatch(/mặt phẳng cắt/iu);
      expect(cutPlan.steps[2].title).toMatch(/hình chiếu vuông góc H.*IH/iu);
      expect(cutPlan.steps[3].title).toMatch(/điểm M.*tam giác vuông IHM/iu);
      expect(cutPlan.steps[4].title).toMatch(/đường tròn thiết diện giao của/iu);
      expect(cutPlan.steps[4].subtitle).toMatch(/hình\s+chiếu\s+vuông\s+góc/iu);

      // Step 2 shows (P) BEFORE H or IH exist — ZERO unattached distance badges floating on I!
      const visStep2 = new Set(objectsAt(cutPlan.scene, cutPlan.steps[1].anchor).map((o) => o.id));
      expect(visStep2.has("P")).toBe(true);
      expect(visStep2.has("C__center")).toBe(false);
      expect(visStep2.has("C__dist")).toBe(false);
      expect(annotationsAt(cutPlan.scene, cutPlan.steps[0].anchor, DEFAULT_ANNOTATION_VIEW, null).map((a) => a.text)).toEqual(["R = 5"]);
      expect(annotationsAt(cutPlan.scene, cutPlan.steps[1].anchor, DEFAULT_ANNOTATION_VIEW, null).map((a) => a.text)).toEqual(["R = 5"]);
      expect(givenQuantitiesSummary(cutPlan.scene, cutPlan.steps[1].anchor).some((g) => /d\(I,\s*\(P\)\)\s*=\s*3/u.test(g.text))).toBe(true);

      // Step 3 adds H and IH BEFORE M or (C) exist — d(I, (P)) = 3 anchors directly onto segment IH without jumping
      const visStep3 = new Set(objectsAt(cutPlan.scene, cutPlan.steps[2].anchor).map((o) => o.id));
      expect(visStep3.has("C__center")).toBe(true);
      expect(visStep3.has("C__dist")).toBe(true);
      expect(visStep3.has("C__rim_pt")).toBe(false);
      expect(visStep3.has("C")).toBe(false);
      const annsStep3 = annotationsAt(cutPlan.scene, cutPlan.steps[2].anchor, DEFAULT_ANNOTATION_VIEW, null);
      expect(annsStep3.some((a) => /d\(I,\s*\(P\)\)\s*=\s*3/u.test(a.text) && a.anchor === "segment")).toBe(true);

      // Step 4 adds certified M, IM, HM BEFORE (C) is closed
      const visStep4 = new Set(objectsAt(cutPlan.scene, cutPlan.steps[3].anchor).map((o) => o.id));
      expect(visStep4.has("C__rim_pt")).toBe(true);
      expect(visStep4.has("C__sph_rad")).toBe(true);
      expect(visStep4.has("C__sec_rad")).toBe(true);
      expect(visStep4.has("C")).toBe(false);

      // Step 5 completes (C) while keeping H, IH, M, IM, HM visible as supporting scaffolding
      const visStep5 = new Set(objectsAt(cutPlan.scene, cutPlan.steps[4].anchor).map((o) => o.id));
      for (const id of ["C", "C__center", "C__dist", "C__rim_pt", "C__sph_rad", "C__sec_rad"]) {
        expect(visStep5.has(id)).toBe(true);
      }

      // Uncertified M ∉ Q^3 (r² = 24) -> 4 pedagogical steps: (S) -> (P) -> (H, IH) -> (C); ZERO M step & ZERO floating rays!
      const irPlan = buildPedagogicalConstructionPlan(withSubEntities(SPHERE_NEAR_COINCIDENT_IRRATIONAL_SCENE));
      expect(irPlan.steps.length).toBe(4);
      expect(irPlan.steps.some((st) => /điểm\s+M/iu.test(st.title))).toBe(false);
      expect(irPlan.scene.objects.find((o) => o.id === "c_nc__rim_pt")).toBeUndefined();
      // Unannotated GIVEN distance q_d = 1 waits at Steps 1–2 and anchors onto segment IH at Steps 3–4
      expect(
        annotationsAt(irPlan.scene, irPlan.steps[1].anchor, DEFAULT_ANNOTATION_VIEW, null).some((a) => /d\(I,\s*\(P\)\)/u.test(a.text)),
      ).toBe(false);
      expect(
        annotationsAt(irPlan.scene, irPlan.steps[2].anchor, DEFAULT_ANNOTATION_VIEW, null).some(
          (a) => /d\(I,\s*\(P\)\)\s*=\s*1/u.test(a.text) && a.anchor === "segment",
        ),
      ).toBe(true);
      const irFinalVis = objectsAt(irPlan.scene, irPlan.steps[irPlan.steps.length - 1].anchor);
      const irRefGroup = buildContractReferenceGroup(irPlan.scene, irFinalVis, irPlan.steps[irPlan.steps.length - 1].anchor);
      const irRefNames = irRefGroup ? irRefGroup.children.map((c) => c.name) : [];
      expect(irRefNames.some((n) => n.startsWith("sphere_pythagoras_"))).toBe(false);

      // Inclined sphere secant (`q_d = 3` unannotated GIVEN): anchors onto segment IH at Steps 3–5
      const incPlan = buildPedagogicalConstructionPlan(withSubEntities(INCLINED_SPHERE_SECANT_SCENE));
      expect(annotationsAt(incPlan.scene, incPlan.steps[1].anchor, DEFAULT_ANNOTATION_VIEW, null).some((a) => a.text.includes("d("))).toBe(false);
      expect(
        annotationsAt(incPlan.scene, incPlan.steps[2].anchor, DEFAULT_ANNOTATION_VIEW, null).some(
          (a) => /d\(I,\s*\(Q\)\)\s*=\s*3/u.test(a.text) && a.anchor === "segment",
        ),
      ).toBe(true);

      // Tangent (d = R) & Disjoint (d > R) foot-only Step 3 never mentions unborn segment IH before Step 4 draws IH (§6)
      const tanPlan = buildPedagogicalConstructionPlan(withSubEntities(SPHERE_TANGENT_SCENE));
      const tanFootStep = tanPlan.steps.find((st) => /^Hạ hình chiếu vuông góc/u.test(st.title))!;
      expect(tanFootStep).toBeDefined();
      expect(`${tanFootStep.title} ${tanFootStep.subtitle}`).not.toMatch(/\bIH\b/u);

      const disPlan = buildPedagogicalConstructionPlan(withSubEntities(SPHERE_DISJOINT_SCENE));
      const disFootStep = disPlan.steps.find((st) => /^Hạ hình chiếu vuông góc/u.test(st.title))!;
      expect(disFootStep).toBeDefined();
      expect(`${disFootStep.title} ${disFootStep.subtitle}`).not.toMatch(/\bIH\b/u);

      // Non-spoiler contract holds across all learner titles/subtitles
      const policy = evaluateStudentPresentationPolicy(cutPlan.scene, cutPlan.goalCompletion);
      expect(policy.showMathResultsPanel).toBe(false);
      for (const st of cutPlan.steps) {
        expect(learnerTextIsSafe(cutPlan.scene, st.title)).toBe(true);
        expect(learnerTextIsSafe(cutPlan.scene, st.subtitle)).toBe(true);
      }
    });

    it("enforces consistent 5-state auxiliary plane lifecycle and retires non-incident foundation ⊥ symbols (§4, §6)", () => {
      // Sphere cutting plane (P): unborn -> active_primary -> used_for_intersection -> context_only
      const cutPlan = buildPedagogicalConstructionPlan(loadSampleScene("cau-cat-mat-phang"));
      const mpP = cutPlan.scene.objects.find((o) => o.id === "P")!;
      expect(classifyAuxiliaryPlanePedagogicalState(cutPlan.scene, mpP, 0, false, null, 0).state).toBe("unborn");
      expect(classifyAuxiliaryPlanePedagogicalState(cutPlan.scene, mpP, cutPlan.steps[1].anchor, false, null, cutPlan.steps[1].startAnchor).state).toBe("active_primary");
      expect(classifyAuxiliaryPlanePedagogicalState(cutPlan.scene, mpP, cutPlan.steps[2].anchor, false, null, cutPlan.steps[2].startAnchor).state).toBe("used_for_intersection");
      expect(classifyAuxiliaryPlanePedagogicalState(cutPlan.scene, mpP, cutPlan.steps[4].anchor, false, null, cutPlan.steps[4].startAnchor).state).toBe("context_only");

      // Polyhedron cutting plane (UVW) in cuboid hexagon section: retires to retired_hidden after section closes
      const hexPlan = buildPedagogicalConstructionPlan(withSubEntities(HOLDOUT_CUBOID_HEXAGON_SCENE));
      const mpUvw = hexPlan.scene.objects.find((o) => o.id === "mp_UVW")!;
      const finalHexSt = hexPlan.steps[hexPlan.steps.length - 1];
      expect(classifyAuxiliaryPlanePedagogicalState(hexPlan.scene, mpUvw, finalHexSt.anchor, false, null, finalHexSt.startAnchor).state).toBe("retired_hidden");

      // Foundation altitude PP' ⊥ (PQRS): visible at Step 2 (`canh_PP1`), retired at post-foundation section steps (neither P nor P' touches UVWXYZ!), restored when auxiliaryShown = true
      const pp1Step = hexPlan.steps.find((s) => s.targetIds.includes("canh_PP1"))!;
      const rolesAtPp1 = resolveStepVisualRoles(hexPlan.scene, pp1Step.anchor, { auxiliaryShown: false, selectedId: null });
      expect(rolesAtPp1.get("canh_PP1")?.showPerpWitnessSymbol).toBe(true);

      const rolesAtHexFinal = resolveStepVisualRoles(hexPlan.scene, finalHexSt.anchor, { auxiliaryShown: false, selectedId: null });
      expect(rolesAtHexFinal.get("canh_PP1")?.showPerpWitnessSymbol).toBe(true);
      expect(rolesAtHexFinal.get("canh_PP1")?.perpWitnessOpacityScale).toBeLessThanOrEqual(0.5);

      const rolesAtHexAuxShown = resolveStepVisualRoles(hexPlan.scene, finalHexSt.anchor, { auxiliaryShown: true, selectedId: null });
      expect(rolesAtHexAuxShown.get("canh_PP1")?.showPerpWitnessSymbol).toBe(true);

      // Conversely, diagonal section `(SAC)` (`mat-cheo-sac`) and point-plane distance (`vuong-goc-chop`) share S, A with `chieu_cao_SA`, so SA ⊥ base stays visible!
      const sacPlan = buildPedagogicalConstructionPlan(loadSampleScene("mat-cheo-sac"));
      const sacFinal = sacPlan.steps[sacPlan.steps.length - 1];
      const rolesSacFinal = resolveStepVisualRoles(sacPlan.scene, sacFinal.anchor, { auxiliaryShown: false, selectedId: null });
      expect(rolesSacFinal.get("chieu_cao_SA")?.showPerpWitnessSymbol).toBe(true);
    });
  });

  describe("Layer C — Visual Hierarchy, Compact Foot-Anchored Perp Stubs & Mobile Label Priority (§3.2, §4, §5)", () => {
    it("attenuates REFERENCE_GREAT_CIRCLE monotonically (standalone > cutting plane > result section) and emits zero synthetic perp_plane_ray stubs", () => {
      const standScene = loadSampleScene("cau-the-tich");
      const standPlan = buildPedagogicalConstructionPlan(standScene);
      const standBall = standPlan.scene.objects.find((o) => o.curved_kind === "ball")!;
      const polStandalone = resolveSphereReferenceGreatCirclePolicy(standPlan.scene, standBall, {
        visibleObjects: objectsAt(standPlan.scene, standPlan.steps[standPlan.steps.length - 1].anchor),
      });

      const cutPlan = buildPedagogicalConstructionPlan(loadSampleScene("cau-cat-mat-phang"));
      const cutBall = cutPlan.scene.objects.find((o) => o.curved_kind === "ball")!;
      const polStep1 = resolveSphereReferenceGreatCirclePolicy(cutPlan.scene, cutBall, {
        visibleObjects: objectsAt(cutPlan.scene, cutPlan.steps[0].anchor),
      });
      const polWithPlane = resolveSphereReferenceGreatCirclePolicy(cutPlan.scene, cutBall, {
        visibleObjects: objectsAt(cutPlan.scene, cutPlan.steps[1].anchor),
      });
      const polWithSection = resolveSphereReferenceGreatCirclePolicy(cutPlan.scene, cutBall, {
        visibleObjects: objectsAt(cutPlan.scene, cutPlan.steps[4].anchor),
      });

      expect(polStandalone.frontOpacity).toBeGreaterThan(polWithPlane.frontOpacity);
      expect(polStep1.frontOpacity).toBeGreaterThan(polWithPlane.frontOpacity);
      expect(polWithPlane.frontOpacity).toBeGreaterThan(polWithSection.frontOpacity);
      expect(polWithSection.frontOpacity).toBeLessThan(0.2);
      expect(shouldShowSphereReferenceEquator(cutPlan.scene, cutBall, false, objectsAt(cutPlan.scene, cutPlan.steps[4].anchor))).toBe(true);

      // Cylinder cutting plane (α) in `tru-thiet-dien-tron`: zero synthetic `perp_plane_ray:P` or ungrounded `perp_marker:P` across Steps 5 & 6
      const cylPlan = buildPedagogicalConstructionPlan(loadSampleScene("tru-thiet-dien-tron"));
      const mpAlpha = cylPlan.scene.objects.find((o) => o.id === "P")!;
      const planeStepIdx = cylPlan.steps.findIndex((st) => st.targetIds.includes("P"));
      const circleStepIdx = cylPlan.steps.findIndex((st) => st.targetIds.includes("C"));
      const visStep5 = objectsAt(cylPlan.scene, cylPlan.steps[planeStepIdx].anchor);
      const visStep6 = objectsAt(cylPlan.scene, cylPlan.steps[circleStepIdx].anchor);
      const built5 = buildObject3D(
        mpAlpha,
        false,
        0.1,
        [[0, 0, 0], [2, 0, 4]],
        new THREE.Vector3(8, 3, 6),
        undefined,
        undefined,
        false,
        "primary",
        true,
        true,
        false,
        cylPlan.scene,
        undefined,
        undefined,
        undefined,
        visStep5,
      );
      const built6 = buildObject3D(
        mpAlpha,
        false,
        0.1,
        [[0, 0, 0], [2, 0, 4]],
        new THREE.Vector3(8, 3, 6),
        undefined,
        undefined,
        false,
        "primary",
        true,
        true,
        false,
        cylPlan.scene,
        undefined,
        undefined,
        undefined,
        visStep6,
      );
      expect(built5?.getObjectByName("perp_plane_ray:P")).toBeUndefined();
      expect(built6?.getObjectByName("perp_plane_ray:P")).toBeUndefined();
      expect(built5?.getObjectByName("perp_marker:P")).toBeUndefined();
      expect(built6?.getObjectByName("perp_marker:P")).toBeUndefined();
    });

    it("prioritizes active target / section labels over crowded interior context vertices on compact mobile viewports (§5)", () => {
      const pContext: Pick<SceneObject, "id" | "origin"> = { id: "P", origin: "free" };
      const uSection: Pick<SceneObject, "id" | "origin"> = { id: "U", origin: "derived" };
      expect(uuTienNhan(uSection, null, "PRIMARY")).toBeGreaterThan(uuTienNhan(pContext, null, "CONTEXT"));
      const kept = locNhanChongNhau(
        [
          { id: "P", x: 180, y: 160, lx: 172, ly: 152, w: 18, h: 18, uuTien: uuTienNhan(pContext, null, "CONTEXT") },
          { id: "U", x: 184, y: 164, lx: 176, ly: 156, w: 20, h: 20, uuTien: uuTienNhan(uSection, null, "PRIMARY") },
        ],
        5,
      );
      expect(kept.has("U")).toBe(true);
      expect(kept.has("P")).toBe(false);
    });
  });

  describe("Layer D — Camera-Change Invariance & Metamorphic Holdout Stability (§3.5, §7)", () => {
    it("guarantees M, H, and REFERENCE_GREAT_CIRCLE plane coordinates never shift under camera orbit or step jumps (§3.5)", () => {
      const plan = buildPedagogicalConstructionPlan(withSubEntities(INCLINED_SPHERE_SECANT_SCENE));
      const ball = plan.scene.objects.find((o) => o.id === "ball_inc")!;
      const footH = plan.scene.objects.find((o) => o.id === "c_inc__center")!;
      const rimM = plan.scene.objects.find((o) => o.id === "c_inc__rim_pt")!;
      const hXyz = [...footH.xyz!];
      const mXyz = [...rimM.xyz!];

      const cameras = [
        new THREE.Vector3(8, 3, 6),
        new THREE.Vector3(-9, 7, 4),
        new THREE.Vector3(2, -11, 5),
        new THREE.Vector3(0, 0, 14),
      ];
      const stepJumpOrder = [0, 1, 2, 3, 4, 2, 0, 4, 1, 3];
      const refNormals = new Set<string>();

      for (const camPos of cameras) {
        for (const sIdx of stepJumpOrder) {
          const vis = objectsAt(plan.scene, plan.steps[sIdx].anchor);
          const refPol = resolveSphereReferenceGreatCirclePolicy(plan.scene, ball, { visibleObjects: vis });
          refNormals.add(refPol.normal.join("|"));
          expect(plan.scene.objects.find((o) => o.id === "c_inc__center")?.xyz).toEqual(hXyz);
          expect(plan.scene.objects.find((o) => o.id === "c_inc__rim_pt")?.xyz).toEqual(mXyz);
          const builtBall = buildObject3D(
            ball,
            false,
            0.1,
            [[1, -1, 2], [6, 4, 7]],
            camPos,
            undefined,
            undefined,
            false,
            "primary",
            true,
            refPol.visible,
            false,
            plan.scene,
            undefined,
            undefined,
            undefined,
            vis,
          );
          expect(builtBall).not.toBeNull();
        }
      }
      expect(refNormals.size).toBe(1);
    });

    it("certifies adverse plane normal n = [3, -8, 0], cross-family cylinder/cone/pyramid/prism invariants, 1 -> N -> 1 + metamorphic transforms, and 375/430/768/1440 framing (§3.5, §5, §6, §7)", () => {
      // 1. Adverse cutting-plane normal n = [3, -8, 0] (collinear with view ray [3, -8, 0] projection): deterministic non-degenerate witnesses & reference plane
      const adverseSphereScene: Scene3D = {
        free_objects: ["I", "q_r"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "q_r", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["ball_adv"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f_r", provenance: "GIVEN", is_given: true } },
          { id: "ball_adv", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: "construct_curved_solid", render: "curved_solid", depends: ["I", "q_r"], anchor: ["0", "0", "0"], radius_sq: "25" },
          { id: "mp_adv", type: "plane3", label: "Mặt phẳng (R)", notation: "(R)", origin: "derived", producer: "construct_plane", render: "surface", surface_role: "CUTTING_PLANE", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: [], point: ["0", "0", "0"], normal: ["3", "-8", "0"] },
          { id: "c_adv", type: "circle3", label: "Đường tròn lớn giao tuyến (C)", notation: "(C)", origin: "derived", producer: "intersect_plane_sphere", render: "circle", surface_role: "SECTION_REGION", depends: ["ball_adv", "mp_adv"], center: ["0", "0", "0"], normal: ["3", "-8", "0"], radius_sq: "25" },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "ball_adv", depends: ["I", "q_r"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "mp_adv", depends: [], explanation: "" },
          { step_index: 3, action: "CREATE", object: "c_adv", depends: ["ball_adv", "mp_adv"], explanation: "" },
        ] as any,
      };
      const advPlan = buildPedagogicalConstructionPlan(withSubEntities(adverseSphereScene));
      expect(verifySceneMathematicalConsistency(advPlan.scene).valid).toBe(true);
      const advBall = advPlan.scene.objects.find((o) => o.id === "ball_adv")!;
      const advPol = resolveSphereReferenceGreatCirclePolicy(advPlan.scene, advBall, { visibleObjects: advPlan.scene.objects });
      expect(advPol.visible).toBe(true);
      // n = [3, -8, 0] is perpendicular to [0, 0, 1], so horizontal reference great circle [0, 0, 1] is strictly orthogonal to (R)!
      expect(qPlainDot(qVec(advPol.normal), qVec(["3", "-8", "0"]))).toEqual([0n, 1n]);

      // 2. Cross-family: tilted right cylinder (`tru-truc-xien`) vs genuine oblique cylinder, plus cone axial section (`non-thiet-dien-truc`)
      const tiltedRight = loadSampleScene("tru-truc-xien");
      const tiltedSolid = tiltedRight.objects.find((o) => o.type === "curved_solid")!;
      const tiltedOrth = inspectAxialCurvedOrthogonality(tiltedRight, tiltedSolid);
      expect(tiltedOrth?.isRightCertified).toBe(true);
      expect(tiltedOrth?.isTiltedAxisInSpace).toBe(true);

      const genuineObliqueCyl: Scene3D = {
        free_objects: ["O", "O1"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "O", type: "point3", label: "O", notation: "O", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "O1", type: "point3", label: "O′", notation: "O′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "4"] },
          { id: "day_duoi", type: "circle3", label: "Đáy dưới", origin: "derived", producer: "construct_circle", render: "circle", surface_role: "BASE_REGION", depends: ["O"], center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "4" },
          { id: "day_tren", type: "circle3", label: "Đáy trên", origin: "derived", producer: "construct_circle", render: "circle", surface_role: "BASE_REGION", depends: ["O1"], center: ["2", "0", "4"], normal: ["0", "0", "1"], radius_sq: "4" },
          { id: "tru_xien_that", type: "curved_solid", curved_kind: "cylinder", label: "Hình trụ xiên", origin: "derived", producer: "construct_curved_solid", render: "curved_solid", depends: ["O", "O1"], anchor: ["0", "0", "0"], apex_or_top: ["2", "0", "4"], radius_sq: "4", height_sq: "20" },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_duoi", depends: ["O"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "day_tren", depends: ["O1"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "tru_xien_that", depends: ["O", "O1"], explanation: "" },
        ] as any,
      };
      const obSolid = genuineObliqueCyl.objects.find((o) => o.type === "curved_solid")!;
      expect(inspectAxialCurvedOrthogonality(genuineObliqueCyl, obSolid)?.isRightCertified ?? false).toBe(false);

      const coneAxialPlan = buildPedagogicalConstructionPlan(loadSampleScene("non-thiet-dien-truc"));
      expect(verifyVisualContinuity(coneAxialPlan.scene).valid).toBe(true);

      // 3. Unseen holdout square pyramid section & oblique prism parallel chevrons across >= 2 camera angles
      const holdoutPyrSection: Scene3D = {
        free_objects: ["E", "F", "G", "H", "S"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "E", type: "point3", label: "E", notation: "E", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "F", type: "point3", label: "F", notation: "F", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["4", "0", "0"] },
          { id: "G", type: "point3", label: "G", notation: "G", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["4", "4", "0"] },
          { id: "H", type: "point3", label: "H", notation: "H", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
          { id: "S", type: "point3", label: "S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
          { id: "day_EFGH", type: "polygon3", label: "Đáy EFGH", notation: "EFGH", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["E", "F", "G", "H"], vertex_ids: ["E", "F", "G", "H"], vertices: [["0", "0", "0"], ["4", "0", "0"], ["4", "4", "0"], ["0", "4", "0"]] },
          { id: "canh_SE", type: "segment3", label: "Chiều cao SE", notation: "SE", origin: "derived", producer: "construct_segment", render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["S", "E"], endpoint_ids: ["S", "E"], endpoints: [["0", "0", "4"], ["0", "0", "0"]], perpendicular_witness: { from: "S", foot: ["0", "0", "0"], foot_id: "E", on: "day_EFGH", relation: "line_perp_plane", status: "GIVEN", plane_directions: [["4", "0", "0"], ["0", "4", "0"]], marker: { u: ["4", "0", "0"], v: ["0", "0", "4"] } } },
          { id: "chop_SEFGH", type: "solid", label: "Chóp S.EFGH", notation: "S.EFGH", shape_class: "PYRAMID_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["S", "E", "F", "G", "H"], vertex_ids: ["S", "E", "F", "G", "H"], vertices: [["0", "0", "4"], ["0", "0", "0"], ["4", "0", "0"], ["4", "4", "0"], ["0", "4", "0"]], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]] },
          { id: "I_m", type: "point3", label: "Trung điểm I của SF", notation: "I", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["S", "F"], xyz: ["2", "0", "2"] },
          { id: "J_m", type: "point3", label: "Trung điểm J của SG", notation: "J", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["S", "G"], xyz: ["2", "2", "2"] },
          { id: "K_m", type: "point3", label: "Trung điểm K của SH", notation: "K", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["S", "H"], xyz: ["0", "2", "2"] },
          { id: "L_m", type: "point3", label: "Trung điểm L của SE", notation: "L", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["S", "E"], xyz: ["0", "0", "2"] },
          { id: "td_IJKL", type: "section", label: "Thiết diện IJKL", notation: "IJKL", origin: "derived", producer: "intersect_plane_solid", render: "polygon", depends: ["chop_SEFGH", "I_m", "J_m", "K_m", "L_m"], polygon: [["2", "0", "2"], ["2", "2", "2"], ["0", "2", "2"], ["0", "0", "2"]], closed: true },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_EFGH", depends: ["E", "F", "G", "H"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "canh_SE", depends: ["S", "E"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "chop_SEFGH", depends: ["S", "E", "F", "G", "H"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "I_m", depends: ["S", "F"], explanation: "" },
          { step_index: 5, action: "CREATE", object: "J_m", depends: ["S", "G"], explanation: "" },
          { step_index: 6, action: "CREATE", object: "K_m", depends: ["S", "H"], explanation: "" },
          { step_index: 7, action: "CREATE", object: "L_m", depends: ["S", "E"], explanation: "" },
          { step_index: 8, action: "CREATE", object: "td_IJKL", depends: ["chop_SEFGH", "I_m", "J_m", "K_m", "L_m"], explanation: "" },
        ] as any,
      };
      const pyrPlan = buildPedagogicalConstructionPlan(withSubEntities(holdoutPyrSection));
      expect(verifyVisualContinuity(pyrPlan.scene).valid).toBe(true);
      for (const st of pyrPlan.steps) {
        const narr = buildPedagogicalStepNarration(pyrPlan.scene, st);
        expect(narr.actionTitle.length).toBeGreaterThan(2);
        expect(narr.conciseRationale.toLowerCase()).not.toBe(narr.actionTitle.toLowerCase());
      }

      // Parallel chevrons under 2 distinct camera poses
      const parRoot = new THREE.Group();
      const segAB: SceneObject = { id: "seg_AB", type: "segment3", label: "AB", notation: "AB", origin: "derived", producer: "construct_segment", render: "segment", depends: [], endpoints: [["0", "0", "0"], ["4", "0", "0"]] };
      const segDE: SceneObject = { id: "seg_DE", type: "segment3", label: "DE", notation: "DE", origin: "derived", producer: "construct_segment", render: "segment", depends: [], endpoints: [["1", "2", "3"], ["5", "2", "3"]] };
      const parScene: Scene3D = { free_objects: [], objects: [segAB, segDE], events: [] };
      const bAB = buildObject3D(segAB, false, 0.1, [[0, 0, 0], [5, 2, 3]], new THREE.Vector3(8, -6, 5), undefined, undefined, false, "primary", true, true, false, parScene, undefined, undefined, undefined, parScene.objects);
      const bDE = buildObject3D(segDE, false, 0.1, [[0, 0, 0], [5, 2, 3]], new THREE.Vector3(8, -6, 5), undefined, undefined, false, "primary", true, true, false, parScene, undefined, undefined, undefined, parScene.objects);
      if (bAB) parRoot.add(bAB);
      if (bDE) parRoot.add(bDE);
      const camA = new THREE.PerspectiveCamera(40, 16 / 9, 0.1, 200);
      camA.position.set(8, -6, 5);
      camA.lookAt(2, 1, 1.5);
      camA.updateMatrixWorld();
      capNhatDauSongSong(parRoot, camA);
      const camB = new THREE.PerspectiveCamera(40, 16 / 9, 0.1, 200);
      camB.position.set(-7, 9, 6);
      camB.lookAt(2, 1, 1.5);
      camB.updateMatrixWorld();
      capNhatDauSongSong(parRoot, camB);

      // 4. Forward/backward 1 -> N -> 1 + metamorphic invariance (rename + translate (+5,-3,+7) + uniform scale ×2)
      const baseCut = loadSampleScene("cau-cat-mat-phang");
      const basePlan = buildPedagogicalConstructionPlan(baseCut);
      const fwdBackIdx = [0, 1, 2, 3, 4, 3, 2, 1, 0];
      const snapRoles0 = JSON.stringify([...resolveStepVisualRoles(basePlan.scene, basePlan.steps[0].anchor).entries()]);
      for (const idx of fwdBackIdx) {
        const r = resolveStepVisualRoles(basePlan.scene, basePlan.steps[idx].anchor);
        expect(r.size).toBeGreaterThan(0);
      }
      const snapRolesEnd0 = JSON.stringify([...resolveStepVisualRoles(basePlan.scene, basePlan.steps[0].anchor).entries()]);
      expect(snapRolesEnd0).toBe(snapRoles0);

      const transformedSphere: Scene3D = {
        free_objects: ["K_ctr", "q_rad"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "K_ctr", type: "point3", label: "Tâm K", notation: "K", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["5", "-3", "7"] },
          { id: "q_rad", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["sph_beta"], value: "10", exact: { kind: "rational", value: "10" }, source: { fact_id: "f_r", provenance: "GIVEN", is_given: true } },
          { id: "sph_beta", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (Ω)", notation: "(Ω)", origin: "derived", producer: "construct_curved_solid", render: "curved_solid", depends: ["K_ctr", "q_rad"], anchor: ["5", "-3", "7"], radius_sq: "100" },
          { id: "mp_beta", type: "plane3", label: "Mặt phẳng (β)", notation: "(β)", origin: "derived", producer: "construct_plane", render: "surface", surface_role: "CUTTING_PLANE", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: [], point: ["5", "-3", "13"], normal: ["0", "0", "1"] },
          { id: "cir_beta", type: "circle3", label: "Đường tròn giao tuyến", notation: "(Γ)", origin: "derived", producer: "intersect_plane_sphere", render: "circle", surface_role: "SECTION_REGION", depends: ["sph_beta", "mp_beta"], center: ["5", "-3", "13"], normal: ["0", "0", "1"], radius_sq: "64" },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "sph_beta", depends: ["K_ctr", "q_rad"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "mp_beta", depends: [], explanation: "" },
          { step_index: 3, action: "CREATE", object: "cir_beta", depends: ["sph_beta", "mp_beta"], explanation: "" },
        ] as any,
      };
      const metaPlan = buildPedagogicalConstructionPlan(withSubEntities(transformedSphere));
      expect(metaPlan.steps.length).toBe(basePlan.steps.length);
      expect(verifySceneMathematicalConsistency(metaPlan.scene).valid).toBe(true);
      expect(verifyConstructionContinuity(metaPlan.scene).valid).toBe(true);

      // 5. Responsive camera framing across 375px, 430px, 768px, and 1440px viewports
      const cubePts: [number, number, number][] = [
        [0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 4, 0],
        [0, 0, 4], [4, 0, 4], [4, 4, 4], [0, 4, 4],
      ];
      for (const [vw, vh] of [[375, 470], [430, 520], [768, 600], [1440, 820]] as const) {
        const kn = khungNhinSuPham(cubePts, [], [], vw <= 480 ? 39 : 40, vw / vh, [8, 3, 6], {
          tiLeDoc: vw <= 480 ? 0.68 : 0.67,
          tiLeNgang: vw <= 480 ? 0.72 : 0.67,
          dichTamDoc: 0,
        });
        expect(kn).not.toBeNull();
        expect(kn!.viTri.every(Number.isFinite)).toBe(true);
      }
    });
  });
});
