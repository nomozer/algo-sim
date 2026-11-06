import * as THREE from "three";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import {
  annotationAnchor,
  annotationsAt,
  DEFAULT_ANNOTATION_VIEW,
  givenQuantitiesSummary,
  placeAnnotationLabels,
} from "./scene3d-annotations";
import { veKhongGian } from "./scene3d-chart";
import type { ExactVec3, Scene3D, SceneObject } from "./scene3d-model";
import {
  buildPedagogicalConstructionPlan,
  buildPedagogicalStepNarration,
  canonicalizeSceneFaceTokensInText,
  getSemanticConstructionContract,
  inspectAxialCurvedOrthogonality,
  pedagogicalStepList,
  registerExactSceneOrigin,
  resolveStepVisualRoles,
  verifyConstructionContinuity,
  verifySceneMathematicalConsistency,
  verifyVisualContinuity,
} from "./scene3d-semantic-policy";
import {
  evaluateStudentPresentationPolicy,
  sanitizeStudentDescriptorText,
} from "./scene3d-student-presentation-policy";
import { withSubEntities } from "./scene3d-subentities";
import { buildObject3D } from "./scene3d-view";

function loadSampleScene(sampleId: string): Scene3D {
  const sample = GEOMETRY_SAMPLES.find((s) => s.id === sampleId);
  if (!sample) throw new Error(`Missing sample: ${sampleId}`);
  const raw = (sample.envelope as unknown as { scene3d: Scene3D }).scene3d;
  const sub = withSubEntities(raw);
  const plan = buildPedagogicalConstructionPlan(sub);
  registerExactSceneOrigin(plan.scene, raw);
  return plan.scene;
}

function parseFrac(raw: string): [bigint, bigint] {
  const s = raw.trim();
  const slash = s.indexOf("/");
  if (slash < 0) return [BigInt(s), 1n];
  const n = BigInt(s.slice(0, slash));
  const d = BigInt(s.slice(slash + 1));
  return d < 0n ? [-n, -d] : [n, d];
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

function fmtFrac(num: bigint, den: bigint): string {
  const sign = den < 0n ? -1n : 1n;
  const n = num * sign;
  const d = den * sign;
  const g = gcdBig(n, d);
  const rn = n / g;
  const rd = d / g;
  return rd === 1n ? String(rn) : `${rn}/${rd}`;
}

function fAdd(a: [bigint, bigint], b: [bigint, bigint]): [bigint, bigint] {
  return [a[0] * b[1] + b[0] * a[1], a[1] * b[1]];
}

function fMul(a: [bigint, bigint], b: [bigint, bigint]): [bigint, bigint] {
  return [a[0] * b[0], a[1] * b[1]];
}

function transformScene(
  scene: Scene3D,
  mapPt: (v: ExactVec3) => ExactVec3,
  mapDir: (v: ExactVec3) => ExactVec3,
  scaleSq: [bigint, bigint],
  renameId: (id: string) => string = (x) => x,
  renameText: (s: string) => string = (x) => x,
): Scene3D {
  const scaleStr = (raw: string | undefined): string | undefined => {
    if (!raw) return raw;
    const f = fMul(parseFrac(raw), scaleSq);
    return fmtFrac(f[0], f[1]);
  };
  return {
    ...scene,
    free_objects: scene.free_objects.map(renameId),
    objects: scene.objects.map((o): SceneObject => ({
      ...o,
      id: renameId(o.id),
      label: o.label ? renameText(o.label) : o.label,
      notation: o.notation ? renameText(o.notation) : o.notation,
      reference: o.reference ? renameText(o.reference) : o.reference,
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
            from: renameId(o.perpendicular_witness.from),
            on: renameId(o.perpendicular_witness.on),
            foot_id: o.perpendicular_witness.foot_id ? renameId(o.perpendicular_witness.foot_id) : undefined,
            foot: mapPt(o.perpendicular_witness.foot),
            plane_directions: o.perpendicular_witness.plane_directions?.map(mapDir) as [ExactVec3, ExactVec3] | undefined,
            marker: {
              ...o.perpendicular_witness.marker,
              u: mapDir(o.perpendicular_witness.marker.u),
              v: mapDir(o.perpendicular_witness.marker.v),
              u_to: o.perpendicular_witness.marker.u_to ? renameId(o.perpendicular_witness.marker.u_to) : undefined,
            },
          }
        : undefined,
      annotation: o.annotation
        ? {
            ...o.annotation,
            subject_ids: o.annotation.subject_ids.map(renameId),
          }
        : undefined,
    })),
    events: scene.events.map((ev) => ({
      ...ev,
      object: ev.object ? renameId(ev.object) : ev.object,
      depends: (ev.depends ?? []).map(renameId),
      justification_text: ev.justification_text ? renameText(ev.justification_text) : ev.justification_text,
    })),
  };
}

// ---------------------------------------------------------------------------
// 8 Unseen Offline Scene3D Fixtures (§9.B)
// ---------------------------------------------------------------------------

// (B1) Pyramid S.ABCD with parallelogram base & two-plane intersection line d = (SAB) ∩ (SCD)
const UNSEEN_PYRAMID_TWO_PLANE_INTERSECTION: Scene3D = {
  free_objects: ["A", "B", "C", "D", "S"],
  chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
  objects: [
    { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["4", "0", "0"] },
    { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["5", "3", "0"] },
    { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "3", "0"] },
    { id: "S", type: "point3", label: "Đỉnh S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "3/2", "4"] },
    { id: "day_ABCD", type: "polygon3", label: "Đáy hình bình hành ABCD", notation: "ABCD", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C", "D"], vertex_ids: ["A", "B", "C", "D"], vertices: [["0", "0", "0"], ["4", "0", "0"], ["5", "3", "0"], ["1", "3", "0"]], source: { fact_id: "f_para" } },
    { id: "khoi_SABCD", type: "solid", label: "Hình chóp S.ABCD", notation: "S.ABCD", shape_class: "PYRAMID_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["S", "A", "B", "C", "D"], vertex_ids: ["S", "A", "B", "C", "D"], vertices: [["2", "3/2", "4"], ["0", "0", "0"], ["4", "0", "0"], ["5", "3", "0"], ["1", "3", "0"]], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]] },
    { id: "mp_SAB", type: "plane3", label: "Mặt phẳng (SAB)", notation: "(SAB)", origin: "derived", producer: "construct_plane", render: "surface", depends: ["S", "A", "B"], point: ["2", "3/2", "4"], normal: ["0", "8", "-3"] },
    { id: "mp_SCD", type: "plane3", label: "Mặt phẳng (SCD)", notation: "(SCD)", origin: "derived", producer: "construct_plane", render: "surface", depends: ["S", "C", "D"], point: ["2", "3/2", "4"], normal: ["0", "8", "3"] },
    { id: "gt_d", type: "line3", label: "Giao tuyến d", notation: "d", origin: "derived", producer: "intersect_planes", render: "line", formation_roles: ["DERIVE_INTERSECTION"], depends: ["mp_SAB", "mp_SCD"], point: ["2", "3/2", "4"], direction: ["1", "0", "0"] },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
    { step_index: 1, action: "CREATE", object: "day_ABCD", depends: ["A", "B", "C", "D"], explanation: "" },
    { step_index: 2, action: "CREATE", object: "khoi_SABCD", depends: ["S", "A", "B", "C", "D"], explanation: "" },
    { step_index: 3, action: "CREATE", object: "mp_SAB", depends: ["S", "A", "B"], explanation: "" },
    { step_index: 4, action: "CREATE", object: "mp_SCD", depends: ["S", "C", "D"], explanation: "" },
    { step_index: 5, action: "CREATE", object: "gt_d", depends: ["mp_SAB", "mp_SCD"], explanation: "", justification_text: "(SAB) và (SCD) có điểm chung S và lần lượt chứa AB ∥ CD nên giao tuyến d qua S và song song với AB, CD." },
  ],
};

// (B2) Regular square pyramid S.EFGH with 1:2 ratio parallel section IJKL (non-midpoint parallel section!)
const UNSEEN_REGULAR_PYRAMID_RATIO_SECTION: Scene3D = {
  free_objects: ["E", "F", "G", "H", "O", "S", "q_ef", "q_so"],
  chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
  objects: [
    { id: "E", type: "point3", label: "Điểm E", notation: "E", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["-3", "-3", "0"] },
    { id: "F", type: "point3", label: "Điểm F", notation: "F", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "-3", "0"] },
    { id: "G", type: "point3", label: "Điểm G", notation: "G", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "3", "0"] },
    { id: "H", type: "point3", label: "Điểm H", notation: "H", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["-3", "3", "0"] },
    { id: "O", type: "point3", label: "Tâm đáy O", notation: "O", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "S", type: "point3", label: "Đỉnh S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "6"] },
    { id: "day_EFGH", type: "polygon3", label: "Đáy hình vuông EFGH", notation: "EFGH", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["E", "F", "G", "H"], vertex_ids: ["E", "F", "G", "H"], vertices: [["-3", "-3", "0"], ["3", "-3", "0"], ["3", "3", "0"], ["-3", "3", "0"]], source: { fact_id: "f_base" } },
    { id: "cao_SO", type: "segment3", label: "Đường cao SO", notation: "SO", origin: "derived", producer: "construct_segment", render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["S", "O"], endpoint_ids: ["S", "O"], endpoints: [["0", "0", "6"], ["0", "0", "0"]], perpendicular_witness: { from: "S", foot: ["0", "0", "0"], foot_id: "O", on: "day_EFGH", relation: "line_perp_plane", status: "GIVEN", plane_directions: [["1", "0", "0"], ["0", "1", "0"]], marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] } } },
    { id: "khoi_SEFGH", type: "solid", label: "Hình chóp đều S.EFGH", notation: "S.EFGH", shape_class: "PYRAMID_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["S", "E", "F", "G", "H"], vertex_ids: ["S", "E", "F", "G", "H"], vertices: [["0", "0", "6"], ["-3", "-3", "0"], ["3", "-3", "0"], ["3", "3", "0"], ["-3", "3", "0"]], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]] },
    { id: "I", type: "point3", label: "Điểm I trên SE (SI = SE/3)", notation: "I", origin: "derived", producer: "ratio_point", render: "point_marker", depends: ["S", "E"], xyz: ["-1", "-1", "4"] },
    { id: "J", type: "point3", label: "Điểm J trên SF (SJ = SF/3)", notation: "J", origin: "derived", producer: "ratio_point", render: "point_marker", depends: ["S", "F"], xyz: ["1", "-1", "4"] },
    { id: "K", type: "point3", label: "Điểm K trên SG (SK = SG/3)", notation: "K", origin: "derived", producer: "ratio_point", render: "point_marker", depends: ["S", "G"], xyz: ["1", "1", "4"] },
    { id: "mp_IJK", type: "plane3", label: "Mặt phẳng (IJK)", notation: "(IJK)", origin: "derived", producer: "construct_plane", render: "surface", surface_role: "CUTTING_PLANE", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: ["I", "J", "K"], point: ["-1", "-1", "4"], normal: ["0", "0", "1"] },
    { id: "canh_SH", type: "segment3", label: "Cạnh bên SH", notation: "SH", origin: "derived", producer: "construct_segment", render: "segment", depends: ["S", "H"], endpoint_ids: ["S", "H"], endpoints: [["0", "0", "6"], ["-3", "3", "0"]] },
    { id: "L", type: "point3", label: "Giao điểm L = SH ∩ (IJK)", notation: "L", origin: "derived", producer: "intersect_line_plane", render: "point_marker", formation_roles: ["DERIVE_INTERSECTION"], depends: ["canh_SH", "mp_IJK"], xyz: ["-1", "1", "4"] },
    { id: "td_IJKL", type: "section", label: "Thiết diện IJKL", notation: "IJKL", origin: "derived", producer: "intersect_plane_solid", render: "polygon", depends: ["khoi_SEFGH", "mp_IJK", "I", "J", "K", "L"], polygon: [["-1", "-1", "4"], ["1", "-1", "4"], ["1", "1", "4"], ["-1", "1", "4"]], closed: true },
    { id: "q_ef", type: "quantity", label: "Cạnh đáy EF", notation: "EF", origin: "free", producer: null, render: "readout", depends: ["E", "F"], value: "6", exact: { kind: "rational", value: "6" }, source: { fact_id: "f_ef" }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["E", "F"], anchor: "segment" } },
    { id: "q_so", type: "quantity", label: "Đường cao SO", notation: "SO", origin: "free", producer: null, render: "readout", depends: ["S", "O"], value: "6", exact: { kind: "rational", value: "6" }, source: { fact_id: "f_so" }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["S", "O"], anchor: "segment" } },
    { id: "kq_s_ijkl", type: "quantity", label: "Diện tích thiết diện IJKL", notation: "S_IJKL", origin: "derived", producer: "measure_area", render: "readout", depends: ["td_IJKL"], value: "4", symbolic: "4", annotation: { kind: "area", category: "result", role: "result", subject_ids: ["td_IJKL"], anchor: "region" } },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
    { step_index: 1, action: "CREATE", object: "day_EFGH", depends: ["E", "F", "G", "H"], explanation: "" },
    { step_index: 2, action: "CREATE", object: "cao_SO", depends: ["S", "O"], explanation: "" },
    { step_index: 3, action: "CREATE", object: "khoi_SEFGH", depends: ["S", "E", "F", "G", "H"], explanation: "" },
    { step_index: 4, action: "CREATE", object: "I", depends: ["S", "E"], explanation: "" },
    { step_index: 5, action: "CREATE", object: "J", depends: ["S", "F"], explanation: "" },
    { step_index: 6, action: "CREATE", object: "K", depends: ["S", "G"], explanation: "" },
    { step_index: 7, action: "CREATE", object: "mp_IJK", depends: ["I", "J", "K"], explanation: "" },
    { step_index: 8, action: "CREATE", object: "canh_SH", depends: ["S", "H"], explanation: "" },
    { step_index: 9, action: "CREATE", object: "L", depends: ["canh_SH", "mp_IJK"], explanation: "" },
    { step_index: 10, action: "CREATE", object: "td_IJKL", depends: ["khoi_SEFGH", "mp_IJK", "I", "J", "K", "L"], explanation: "", justification_text: "(EFS) ∩ (IJK) = IJ, (FGS) ∩ (IJK) = JK, (GHS) ∩ (IJK) = KL, (HES) ∩ (IJK) = LI." },
    { step_index: 11, action: "MEASURE", object: "kq_s_ijkl", depends: ["td_IJKL"], explanation: "", semantic_kind: "FINAL_RESULT" },
  ],
};

// (B3) Right triangular prism ABC.A′B′C′ cut by inclined plane (A′MN)
const UNSEEN_RIGHT_PRISM_SECTION: Scene3D = {
  free_objects: ["A", "B", "C", "A1", "B1", "C1", "q_ab", "q_ac", "q_aa1"],
  chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
  objects: [
    { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
    { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
    { id: "A1", type: "point3", label: "Điểm A′", notation: "A′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
    { id: "B1", type: "point3", label: "Điểm B′", notation: "B′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "4"] },
    { id: "C1", type: "point3", label: "Điểm C′", notation: "C′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "4"] },
    { id: "day_ABC", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "4", "0"]] },
    { id: "canh_AA1", type: "segment3", label: "Cạnh bên AA′", notation: "AA′", origin: "derived", producer: "construct_segment", render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["A", "A1"], endpoint_ids: ["A", "A1"], endpoints: [["0", "0", "0"], ["0", "0", "4"]], perpendicular_witness: { from: "A1", foot: ["0", "0", "0"], foot_id: "A", on: "day_ABC", relation: "line_perp_plane", status: "GIVEN", plane_directions: [["3", "0", "0"], ["0", "4", "0"]], marker: { u: ["3", "0", "0"], v: ["0", "0", "4"] } } },
    { id: "day_A1B1C1", type: "polygon3", label: "Đáy A′B′C′", notation: "A′B′C′", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_TRANSLATED_FACE"], depends: ["A1", "B1", "C1"], vertex_ids: ["A1", "B1", "C1"], vertices: [["0", "0", "4"], ["3", "0", "4"], ["0", "4", "4"]] },
    { id: "lt_dung", type: "solid", label: "Lăng trụ đứng ABC.A′B′C′", notation: "ABC.A′B′C′", shape_class: "PRISM_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["A", "B", "C", "A1", "B1", "C1"], vertex_ids: ["A", "B", "C", "A1", "B1", "C1"], vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "4", "0"], ["0", "0", "4"], ["3", "0", "4"], ["0", "4", "4"]], faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]] },
    { id: "M", type: "point3", label: "Trung điểm M của AB", notation: "M", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["A", "B"], xyz: ["3/2", "0", "0"] },
    { id: "N", type: "point3", label: "Trung điểm N của AC", notation: "N", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["A", "C"], xyz: ["0", "2", "0"] },
    { id: "mp_cut", type: "plane3", label: "Mặt phẳng cắt (A′MN)", notation: "(A′MN)", origin: "derived", producer: "construct_plane", render: "surface", surface_role: "CUTTING_PLANE", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: ["A1", "M", "N"], point: ["0", "0", "4"], normal: ["8", "6", "3"] },
    { id: "td_lt", type: "section", label: "Thiết diện A′MN", notation: "A′MN", origin: "derived", producer: "intersect_plane_solid", render: "polygon", depends: ["lt_dung", "mp_cut", "A1", "M", "N"], polygon: [["0", "0", "4"], ["3/2", "0", "0"], ["0", "2", "0"]], closed: true },
    { id: "q_ab", type: "quantity", label: "Cạnh AB", notation: "AB", origin: "free", producer: null, render: "readout", depends: ["A", "B"], value: "3", exact: { kind: "rational", value: "3" }, source: { fact_id: "f_ab" }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "B"], anchor: "segment" } },
    { id: "q_ac", type: "quantity", label: "Cạnh AC", notation: "AC", origin: "free", producer: null, render: "readout", depends: ["A", "C"], value: "4", exact: { kind: "rational", value: "4" }, source: { fact_id: "f_ac" }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "C"], anchor: "segment" } },
    { id: "q_aa1", type: "quantity", label: "Cạnh bên AA′", notation: "AA′", origin: "free", producer: null, render: "readout", depends: ["A", "A1"], value: "4", exact: { kind: "rational", value: "4" }, source: { fact_id: "f_aa1" }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "A1"], anchor: "segment" } },
    { id: "kq_s", type: "quantity", label: "Diện tích thiết diện", notation: "S_A′MN", origin: "derived", producer: "measure_area", render: "readout", depends: ["td_lt"], value: "√109/2", symbolic: "√109/2", annotation: { kind: "area", category: "result", role: "result", subject_ids: ["td_lt"], anchor: "region" } },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
    { step_index: 1, action: "CREATE", object: "day_ABC", depends: ["A", "B", "C"], explanation: "" },
    { step_index: 2, action: "CREATE", object: "canh_AA1", depends: ["A", "A1"], explanation: "" },
    { step_index: 3, action: "CREATE", object: "day_A1B1C1", depends: ["A1", "B1", "C1"], explanation: "" },
    { step_index: 4, action: "CREATE", object: "lt_dung", depends: ["A", "B", "C", "A1", "B1", "C1"], explanation: "" },
    { step_index: 5, action: "CREATE", object: "M", depends: ["A", "B"], explanation: "" },
    { step_index: 6, action: "CREATE", object: "N", depends: ["A", "C"], explanation: "" },
    { step_index: 7, action: "CREATE", object: "mp_cut", depends: ["A1", "M", "N"], explanation: "" },
    { step_index: 8, action: "CREATE", object: "td_lt", depends: ["lt_dung", "mp_cut", "A1", "M", "N"], explanation: "" },
    { step_index: 9, action: "MEASURE", object: "kq_s", depends: ["td_lt"], explanation: "", semantic_kind: "FINAL_RESULT" },
  ],
};

// (B4) Sphere cut by inclined plane (Q): x + 2y + 2z - 12 = 0 (d = 3 < R = 5)
const UNSEEN_SPHERE_INCLINED_PLANE: Scene3D = {
  free_objects: ["I", "q_r", "q_d"],
  chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
  objects: [
    { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "-1", "2"] },
    { id: "q_r", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["ball_i"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f_r" } },
    { id: "q_d", type: "quantity", label: "Khoảng cách d(I,(Q))", notation: "d(I,(Q))", origin: "free", producer: null, render: "readout", depends: ["I", "mp_q"], value: "3", exact: { kind: "rational", value: "3" }, source: { fact_id: "f_d" }, annotation: { kind: "distance", category: "measurement", role: "given", subject_ids: ["I", "H_q"], anchor: "segment" } },
    { id: "ball_i", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: "construct_curved_solid", render: "curved_solid", depends: ["I", "q_r"], anchor: ["1", "-1", "2"], radius_sq: "25" },
    { id: "mp_q", type: "plane3", label: "Mặt phẳng nghiêng (Q)", notation: "(Q)", origin: "derived", producer: "construct_plane", render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["2", "1", "4"], normal: ["1", "2", "2"] },
    { id: "H_q", type: "point3", label: "Hình chiếu H của I lên (Q)", notation: "H", origin: "derived", producer: "project_onto", render: "point_marker", depends: ["I", "mp_q"], xyz: ["2", "1", "4"] },
    { id: "doan_IH", type: "segment3", label: "Đoạn vuông góc IH", notation: "IH", origin: "derived", producer: "construct_segment", render: "segment", depends: ["I", "H_q"], endpoint_ids: ["I", "H_q"], endpoints: [["1", "-1", "2"], ["2", "1", "4"]], perpendicular_witness: { from: "I", foot: ["2", "1", "4"], foot_id: "H_q", on: "mp_q", relation: "line_perp_plane", status: "DERIVED_VERIFIED", plane_directions: [["2", "-1", "0"], ["2", "0", "-1"]], marker: { u: ["2", "-1", "0"], v: ["-1", "-2", "-2"] } } },
    { id: "vong_q", type: "circle3", label: "Đường tròn giao tuyến (C)", notation: "(C)", origin: "derived", producer: "intersect_plane_sphere", render: "circle", surface_role: "SECTION_REGION", depends: ["ball_i", "mp_q", "H_q"], center: ["2", "1", "4"], normal: ["1", "2", "2"], radius_sq: "16" },
    { id: "kq_s", type: "quantity", label: "Diện tích thiết diện", notation: "S_(C)", origin: "derived", producer: "measure_area", render: "readout", depends: ["vong_q"], value: "16π", symbolic: "16π", annotation: { kind: "area", category: "result", role: "result", subject_ids: ["vong_q"], anchor: "region" } },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
    { step_index: 1, action: "CREATE", object: "ball_i", depends: ["I", "q_r"], explanation: "" },
    { step_index: 2, action: "CREATE", object: "mp_q", depends: [], explanation: "" },
    { step_index: 3, action: "CREATE", object: "H_q", depends: ["I", "mp_q"], explanation: "" },
    { step_index: 4, action: "CREATE", object: "doan_IH", depends: ["I", "H_q"], explanation: "" },
    { step_index: 5, action: "CREATE", object: "vong_q", depends: ["ball_i", "mp_q", "H_q"], explanation: "" },
    { step_index: 6, action: "MEASURE", object: "kq_s", depends: ["vong_q"], explanation: "", semantic_kind: "FINAL_RESULT" },
  ],
};

// (B5) Cylinder R = 3, h = 8 cut by perpendicular plane (β) at M (OM = 2) + tangent sphere d = R = 5
const UNSEEN_CYLINDER_PERP_CUT: Scene3D = {
  free_objects: ["O", "O1", "q_r", "q_h"],
  chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
  objects: [
    { id: "O", type: "point3", label: "Tâm đáy O", notation: "O", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "O1", type: "point3", label: "Tâm đáy O′", notation: "O′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "8"] },
    { id: "q_r", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["tru_c"], value: "3", exact: { kind: "rational", value: "3" }, source: { fact_id: "f_r" } },
    { id: "q_h", type: "quantity", label: "Chiều cao h", notation: "h", origin: "free", producer: null, render: "readout", depends: ["tru_c"], value: "8", exact: { kind: "rational", value: "8" }, source: { fact_id: "f_h" } },
    { id: "day_duoi", type: "circle3", label: "Đáy dưới (O)", notation: "(O)", origin: "derived", producer: null, render: "circle", surface_role: "BASE_REGION", depends: ["O"], center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "9" },
    { id: "truc_oo1", type: "segment3", label: "Trục OO′", notation: "OO′", origin: "derived", producer: null, render: "segment", role: "axis", formation_roles: ["CONSTRUCT_AXIS"], depends: ["O", "O1"], endpoint_ids: ["O", "O1"], endpoints: [["0", "0", "0"], ["0", "0", "8"]], perpendicular_witness: { from: "O1", foot: ["0", "0", "0"], foot_id: "O", on: "day_duoi", relation: "line_perp_plane", status: "GIVEN", plane_directions: [["1", "0", "0"], ["0", "1", "0"]], marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] } } },
    { id: "day_tren", type: "circle3", label: "Đáy trên (O′)", notation: "(O′)", origin: "derived", producer: null, render: "circle", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_TRANSLATED_FACE"], depends: ["O1"], center: ["0", "0", "8"], normal: ["0", "0", "1"], radius_sq: "9" },
    { id: "tru_c", type: "curved_solid", curved_kind: "cylinder", label: "Hình trụ", notation: "(T)", origin: "derived", producer: null, render: "curved_solid", depends: ["O", "O1", "day_duoi", "day_tren", "q_r", "q_h"], anchor: ["0", "0", "0"], apex_or_top: ["0", "0", "8"], radius_sq: "9", height_sq: "64" },
    { id: "M_c", type: "point3", label: "Điểm M trên trục OO′", notation: "M", origin: "derived", producer: "ratio_point", render: "point_marker", depends: ["truc_oo1"], xyz: ["0", "0", "2"] },
    { id: "mp_beta", type: "plane3", label: "Mặt phẳng (β)", notation: "(β)", origin: "derived", producer: "construct_plane", render: "surface", surface_role: "CUTTING_PLANE", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: ["M_c", "truc_oo1"], point: ["0", "0", "2"], normal: ["0", "0", "1"], perpendicular_witness: { from: "O1", foot: ["0", "0", "2"], foot_id: "M_c", on: "mp_beta", relation: "line_perp_plane", status: "GIVEN", plane_directions: [["1", "0", "0"], ["0", "1", "0"]], marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] } } },
    { id: "c_sec", type: "circle3", label: "Đường tròn thiết diện", notation: "(C)", origin: "derived", producer: "intersect_plane_cylinder", render: "circle", surface_role: "SECTION_REGION", depends: ["tru_c", "mp_beta", "M_c"], center: ["0", "0", "2"], normal: ["0", "0", "1"], radius_sq: "9" },
    { id: "kq_area", type: "quantity", label: "Diện tích thiết diện", notation: "S_(C)", origin: "derived", producer: "measure_area", render: "readout", depends: ["c_sec"], value: "9π", symbolic: "9π", annotation: { kind: "area", category: "result", role: "result", subject_ids: ["c_sec"], anchor: "region" } },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
    { step_index: 1, action: "CREATE", object: "day_duoi", depends: ["O"], explanation: "" },
    { step_index: 2, action: "CREATE", object: "truc_oo1", depends: ["O", "O1"], explanation: "" },
    { step_index: 3, action: "CREATE", object: "day_tren", depends: ["O1"], explanation: "" },
    { step_index: 4, action: "CREATE", object: "tru_c", depends: ["O", "O1", "day_duoi", "day_tren"], explanation: "" },
    { step_index: 5, action: "CREATE", object: "M_c", depends: ["truc_oo1"], explanation: "" },
    { step_index: 6, action: "CREATE", object: "mp_beta", depends: ["M_c", "truc_oo1"], explanation: "" },
    { step_index: 7, action: "CREATE", object: "c_sec", depends: ["tru_c", "mp_beta", "M_c"], explanation: "" },
    { step_index: 8, action: "MEASURE", object: "kq_area", depends: ["c_sec"], explanation: "", semantic_kind: "FINAL_RESULT" },
  ],
};

// (B6) Cone with diameter MN, generators SM, SN, and axial section SMN
const UNSEEN_CONE_GENERATORS_AXIAL: Scene3D = {
  free_objects: ["O", "S", "M", "N", "q_r", "q_h"],
  chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
  objects: [
    { id: "O", type: "point3", label: "Tâm đáy O", notation: "O", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "S", type: "point3", label: "Đỉnh nón S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
    { id: "M", type: "point3", label: "Điểm M trên đường tròn đáy", notation: "M", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["-3", "0", "0"] },
    { id: "N", type: "point3", label: "Điểm N đối xứng M qua O", notation: "N", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
    { id: "day_O", type: "circle3", label: "Đáy nón (O)", notation: "(O)", origin: "derived", producer: null, render: "circle", surface_role: "BASE_REGION", depends: ["O"], center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "9" },
    { id: "truc_SO", type: "segment3", label: "Trục SO", notation: "SO", origin: "derived", producer: null, render: "segment", role: "axis", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["S", "O"], endpoint_ids: ["S", "O"], endpoints: [["0", "0", "4"], ["0", "0", "0"]], perpendicular_witness: { from: "S", foot: ["0", "0", "0"], foot_id: "O", on: "day_O", relation: "line_perp_plane", status: "GIVEN", plane_directions: [["1", "0", "0"], ["0", "1", "0"]], marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] } } },
    { id: "non_S", type: "curved_solid", curved_kind: "cone", label: "Hình nón", notation: "(N)", origin: "derived", producer: null, render: "curved_solid", depends: ["S", "O", "day_O", "q_r", "q_h"], anchor: ["0", "0", "0"], apex_or_top: ["0", "0", "4"], radius_sq: "9", height_sq: "16" },
    { id: "dk_MN", type: "segment3", label: "Đường kính MN", notation: "MN", origin: "derived", producer: "construct_segment", render: "segment", depends: ["M", "N"], endpoint_ids: ["M", "N"], endpoints: [["-3", "0", "0"], ["3", "0", "0"]] },
    { id: "ds_SM", type: "segment3", label: "Đường sinh SM", notation: "SM", origin: "derived", producer: "construct_segment", render: "segment", depends: ["S", "M"], endpoint_ids: ["S", "M"], endpoints: [["0", "0", "4"], ["-3", "0", "0"]] },
    { id: "ds_SN", type: "segment3", label: "Đường sinh SN", notation: "SN", origin: "derived", producer: "construct_segment", render: "segment", depends: ["S", "N"], endpoint_ids: ["S", "N"], endpoints: [["0", "0", "4"], ["3", "0", "0"]] },
    { id: "td_SMN", type: "section", label: "Thiết diện qua trục SMN", notation: "SMN", origin: "derived", producer: "intersect_plane_cone", render: "polygon", depends: ["non_S", "S", "M", "N", "dk_MN", "ds_SM", "ds_SN"], polygon: [["0", "0", "4"], ["-3", "0", "0"], ["3", "0", "0"]], closed: true },
    { id: "q_r", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["non_S"], value: "3", exact: { kind: "rational", value: "3" }, source: { fact_id: "f_r" } },
    { id: "q_h", type: "quantity", label: "Chiều cao h", notation: "h", origin: "free", producer: null, render: "readout", depends: ["S", "O"], value: "4", exact: { kind: "rational", value: "4" }, source: { fact_id: "f_h" }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["S", "O"], anchor: "segment" } },
    { id: "kq_l", type: "quantity", label: "Độ dài đường sinh l", notation: "l", origin: "derived", producer: "measure_length", render: "readout", depends: ["ds_SM"], value: "5", symbolic: "5", annotation: { kind: "length", category: "result", role: "result", subject_ids: ["S", "M"], anchor: "segment" } },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
    { step_index: 1, action: "CREATE", object: "day_O", depends: ["O"], explanation: "" },
    { step_index: 2, action: "CREATE", object: "truc_SO", depends: ["S", "O"], explanation: "" },
    { step_index: 3, action: "CREATE", object: "non_S", depends: ["S", "O", "day_O"], explanation: "" },
    { step_index: 4, action: "CREATE", object: "dk_MN", depends: ["M", "N"], explanation: "" },
    { step_index: 5, action: "CREATE", object: "ds_SM", depends: ["S", "M"], explanation: "" },
    { step_index: 6, action: "CREATE", object: "ds_SN", depends: ["S", "N"], explanation: "" },
    { step_index: 7, action: "CREATE", object: "td_SMN", depends: ["non_S", "S", "M", "N", "dk_MN", "ds_SM", "ds_SN"], explanation: "" },
    { step_index: 8, action: "MEASURE", object: "kq_l", depends: ["ds_SM"], explanation: "", semantic_kind: "FINAL_RESULT" },
  ],
};

// (B7) Point-to-plane distance with co-existing perpendicular & parallel relations
const UNSEEN_POINT_PLANE_DISTANCE: Scene3D = {
  free_objects: ["A", "B", "C", "D", "S", "q_ab", "q_sa"],
  chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
  objects: [
    { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
    { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "2", "0"] },
    { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
    { id: "S", type: "point3", label: "Đỉnh S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "2"] },
    { id: "day_ABCD", type: "polygon3", label: "Đáy hình vuông ABCD", notation: "ABCD", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C", "D"], vertex_ids: ["A", "B", "C", "D"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]], source: { fact_id: "f_sq" } },
    { id: "cao_SA", type: "segment3", label: "Đường cao SA", notation: "SA", origin: "derived", producer: "construct_segment", render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["S", "A"], endpoint_ids: ["S", "A"], endpoints: [["0", "0", "2"], ["0", "0", "0"]], perpendicular_witness: { from: "S", foot: ["0", "0", "0"], foot_id: "A", on: "day_ABCD", relation: "line_perp_plane", status: "GIVEN", plane_directions: [["2", "0", "0"], ["0", "2", "0"]], marker: { u: ["2", "0", "0"], v: ["0", "0", "2"] } } },
    { id: "khoi_SABCD", type: "solid", label: "Hình chóp S.ABCD", notation: "S.ABCD", shape_class: "PYRAMID_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["S", "A", "B", "C", "D"], vertex_ids: ["S", "A", "B", "C", "D"], vertices: [["0", "0", "2"], ["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]] },
    { id: "mp_SBC", type: "polygon3", label: "Mặt phẳng (SBC)", notation: "(SBC)", origin: "derived", producer: "construct_polygon", render: "polygon", depends: ["S", "B", "C"], vertex_ids: ["S", "B", "C"], vertices: [["0", "0", "2"], ["2", "0", "0"], ["2", "2", "0"]] },
    { id: "H", type: "point3", label: "Hình chiếu H của A lên (SBC)", notation: "H", origin: "derived", producer: "foot_of_perpendicular", render: "point_marker", depends: ["A", "mp_SBC"], xyz: ["1", "0", "1"] },
    { id: "doan_AH", type: "segment3", label: "Đoạn vuông góc AH", notation: "AH", origin: "derived", producer: "construct_perpendicular", render: "segment", depends: ["A", "H", "mp_SBC"], endpoint_ids: ["A", "H"], endpoints: [["0", "0", "0"], ["1", "0", "1"]], perpendicular_witness: { from: "A", foot: ["1", "0", "1"], foot_id: "H", on: "mp_SBC", relation: "line_perp_plane", status: "DERIVED_VERIFIED", plane_directions: [["2", "0", "-2"], ["0", "2", "0"]], marker: { u: ["-1", "0", "1"], v: ["-1", "0", "-1"] } } },
    { id: "q_ab", type: "quantity", label: "Cạnh đáy AB", notation: "AB", origin: "free", producer: null, render: "readout", depends: ["A", "B"], value: "2", exact: { kind: "rational", value: "2" }, source: { fact_id: "f_ab" }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "B"], anchor: "segment" } },
    { id: "q_sa", type: "quantity", label: "Chiều cao SA", notation: "SA", origin: "free", producer: null, render: "readout", depends: ["S", "A"], value: "2", exact: { kind: "rational", value: "2" }, source: { fact_id: "f_sa" }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["S", "A"], anchor: "segment" } },
    { id: "kq_d", type: "quantity", label: "Khoảng cách d(A,(SBC))", notation: "d(A,(SBC))", origin: "derived", producer: "measure_distance", render: "readout", depends: ["doan_AH"], value: "√2", symbolic: "√2", annotation: { kind: "distance", category: "result", role: "result", subject_ids: ["A", "H"], anchor: "segment" } },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
    { step_index: 1, action: "CREATE", object: "day_ABCD", depends: ["A", "B", "C", "D"], explanation: "" },
    { step_index: 2, action: "CREATE", object: "cao_SA", depends: ["S", "A"], explanation: "" },
    { step_index: 3, action: "CREATE", object: "khoi_SABCD", depends: ["S", "A", "B", "C", "D"], explanation: "" },
    { step_index: 4, action: "CREATE", object: "mp_SBC", depends: ["S", "B", "C"], explanation: "" },
    { step_index: 5, action: "CREATE", object: "H", depends: ["A", "mp_SBC"], explanation: "" },
    { step_index: 6, action: "CREATE", object: "doan_AH", depends: ["A", "H", "mp_SBC"], explanation: "" },
    { step_index: 7, action: "MEASURE", object: "kq_d", depends: ["doan_AH"], explanation: "", semantic_kind: "FINAL_RESULT" },
  ],
};

// (B8) Multi-auxiliary construction configuration (tetrahedron S.ABC with auxiliary carrier lines retired after intersection)
const UNSEEN_MULTI_AUXILIARY_CONSTRUCTION: Scene3D = {
  free_objects: ["A", "B", "C", "S"],
  chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
  objects: [
    { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["4", "0", "0"] },
    { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
    { id: "S", type: "point3", label: "Đỉnh S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
    { id: "khoi_SABC", type: "solid", label: "Tứ diện S.ABC", notation: "S.ABC", shape_class: "PYRAMID_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["S", "A", "B", "C"], vertex_ids: ["S", "A", "B", "C"], vertices: [["0", "0", "4"], ["0", "0", "0"], ["4", "0", "0"], ["0", "4", "0"]], faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]] },
    { id: "M", type: "point3", label: "Điểm M trên SA", notation: "M", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["S", "A"], xyz: ["0", "0", "2"] },
    { id: "N", type: "point3", label: "Điểm N trên SB", notation: "N", origin: "derived", producer: "ratio_point", render: "point_marker", depends: ["S", "B"], xyz: ["3", "0", "1"] },
    { id: "P", type: "point3", label: "Điểm P trên BC", notation: "P", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["B", "C"], xyz: ["2", "2", "0"] },
    { id: "aux_line_MN", type: "line3", label: "Đường thẳng MN", notation: "MN", origin: "derived", producer: "construct_line", render: "line", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], depends: ["M", "N"], point: ["0", "0", "2"], direction: ["3", "0", "-1"] },
    { id: "aux_line_AB", type: "line3", label: "Đường thẳng AB", notation: "AB", origin: "derived", producer: "construct_line", render: "line", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], depends: ["A", "B"], point: ["0", "0", "0"], direction: ["1", "0", "0"] },
    { id: "E_int", type: "point3", label: "Giao điểm E = MN ∩ AB", notation: "E", origin: "derived", producer: "intersect_lines", render: "point_marker", formation_roles: ["DERIVE_INTERSECTION"], depends: ["aux_line_MN", "aux_line_AB"], xyz: ["6", "0", "0"] },
    { id: "aux_line_EP", type: "line3", label: "Đường thẳng EP", notation: "EP", origin: "derived", producer: "construct_line", render: "line", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], depends: ["E_int", "P"], point: ["6", "0", "0"], direction: ["-2", "1", "0"] },
    { id: "aux_line_AC", type: "line3", label: "Đường thẳng AC", notation: "AC", origin: "derived", producer: "construct_line", render: "line", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], depends: ["A", "C"], point: ["0", "0", "0"], direction: ["0", "1", "0"] },
    { id: "Q_int", type: "point3", label: "Giao điểm Q = EP ∩ AC", notation: "Q", origin: "derived", producer: "intersect_lines", render: "point_marker", formation_roles: ["DERIVE_INTERSECTION"], depends: ["aux_line_EP", "aux_line_AC"], xyz: ["0", "3", "0"] },
    { id: "td_MNPQ", type: "section", label: "Thiết diện MNPQ", notation: "MNPQ", origin: "derived", producer: "intersect_plane_solid", render: "polygon", depends: ["khoi_SABC", "M", "N", "P", "Q_int"], polygon: [["0", "0", "2"], ["3", "0", "1"], ["2", "2", "0"], ["0", "3", "0"]], closed: true },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
    { step_index: 1, action: "CREATE", object: "khoi_SABC", depends: ["S", "A", "B", "C"], explanation: "" },
    { step_index: 2, action: "CREATE", object: "M", depends: ["S", "A"], explanation: "" },
    { step_index: 3, action: "CREATE", object: "N", depends: ["S", "B"], explanation: "" },
    { step_index: 4, action: "CREATE", object: "P", depends: ["B", "C"], explanation: "" },
    { step_index: 5, action: "CREATE", object: "aux_line_MN", depends: ["M", "N"], explanation: "" },
    { step_index: 6, action: "CREATE", object: "aux_line_AB", depends: ["A", "B"], explanation: "" },
    { step_index: 7, action: "CREATE", object: "E_int", depends: ["aux_line_MN", "aux_line_AB"], explanation: "" },
    { step_index: 8, action: "CREATE", object: "aux_line_EP", depends: ["E_int", "P"], explanation: "" },
    { step_index: 9, action: "CREATE", object: "aux_line_AC", depends: ["A", "C"], explanation: "" },
    { step_index: 10, action: "CREATE", object: "Q_int", depends: ["aux_line_EP", "aux_line_AC"], explanation: "" },
    { step_index: 11, action: "CREATE", object: "td_MNPQ", depends: ["khoi_SABC", "M", "N", "P", "Q_int"], explanation: "" },
  ],
};

describe("AXO System-Wide Pedagogical Presentation Hardening & Regression Audit (§3–§11)", () => {
  describe("§3, §7, §8 & §9.A — Full 11-Sample Catalog Sweep: Step Lifecycle, Visual Continuity & Non-Spoiler Gate", () => {
    it("certifies all 11 catalog scenes across first, intermediate, and final steps under verifyConstructionContinuity and 4D verifyVisualContinuity", () => {
      expect(GEOMETRY_SAMPLES.length).toBeGreaterThanOrEqual(11);
      for (const sample of GEOMETRY_SAMPLES) {
        const scene = loadSampleScene(sample.id);
        const geoCont = verifyConstructionContinuity(scene);
        expect(geoCont.valid, `${sample.id}: ${geoCont.violations.map((v) => v.detail).join("; ")}`).toBe(true);

        const visCont = verifyVisualContinuity(scene);
        expect(visCont.valid, `${sample.id}: ${visCont.violations.map((v) => v.detail).join("; ")}`).toBe(true);
        expect(visCont.dimensions).toEqual({
          geometric: true,
          semantic: true,
          visual: true,
          pedagogical: true,
        });

        const steps = pedagogicalStepList(scene);
        expect(steps.length).toBeGreaterThan(0);

        const policy = evaluateStudentPresentationPolicy(scene);
        expect(policy.showMathResultsPanel).toBe(false);

        for (const st of steps) {
          const roles = resolveStepVisualRoles(scene, st.anchor, { auxiliaryShown: false, selectedId: null });
          for (const entry of roles.values()) {
            expect(entry.objectId).toBeTruthy();
            expect(entry.semanticLayer).toBeTruthy();
            expect(entry.semanticRole).toBeTruthy();
            expect(typeof entry.birthStep).toBe("number");
            expect(Array.isArray(entry.prerequisites)).toBe(true);
            expect([
              "active_target",
              "direct_prerequisite",
              "spatial_carrier",
              "explanatory_witness",
              "completed_scaffold",
              "inactive",
            ]).toContain(entry.relationToActiveTarget);
            expect(typeof entry.visualPriority).toBe("number");
            expect((entry.keepCondition ?? "").length).toBeGreaterThan(0);
            expect((entry.attenuateCondition ?? "").length).toBeGreaterThan(0);
            expect((entry.hideCondition ?? "").length).toBeGreaterThan(0);
            expect(entry.restorableOnBackwardScrub).toBe(true);
          }

          const nar = buildPedagogicalStepNarration(scene, st);
          expect(nar.actionTitle.length).toBeGreaterThan(0);
          expect(nar.conciseRationale.includes("Giao tuyến trên từng mặt:")).toBe(false);
        }

        const html = renderToString(
          <AxoWorkspaceV62
            scene={(sample.envelope as unknown as { scene3d: Scene3D }).scene3d}
            de={sample.problemText}
            tieuDe={sample.id}
          />,
        );
        expect(html).not.toContain("KẾT QUẢ TOÁN HỌC");
        if (sample.id === "cau-cat-mat-phang") {
          // Luồng dựng hình không trình bày đáp án (scene3d-no-answer-surface.test.tsx).
          expect(html).not.toContain('id="dock-goal-reveal"');
          expect(html).not.toContain('id="dock-goal-conclusion"');
          expect(html).not.toContain("16π");
        }
      }
    });
  });

  describe("§4 & §5 — Reference Case 1: Cylinder Section Perpendicular to Axis (`tru-thiet-dien-tron`) & Curved-Solid Distinction", () => {
    it("retires obsolete foundation OO′ ⊥ (O) witness and fallback R/h badges on Steps 5–6 while keeping OO′ ⊥ (α) at M, Dock givens, and deterministic backward restoration", () => {
      const scene = loadSampleScene("tru-thiet-dien-tron");
      const steps = pedagogicalStepList(scene);
      expect(steps.length).toBe(6);

      // Step 1: R = 2 on base circle day_duoi
      const annsStep1 = annotationsAt(scene, steps[0]!.anchor, DEFAULT_ANNOTATION_VIEW, null);
      expect(annsStep1.map((a) => a.text)).toContain("R = 2");

      // Step 2: Foundation axis OO′ ⊥ (O) witness IS active on tru__axis
      const rolesStep2 = resolveStepVisualRoles(scene, steps[1]!.anchor, { auxiliaryShown: false, selectedId: null });
      const axisStep2 = rolesStep2.get("tru__axis");
      expect(axisStep2?.showPerpWitnessSymbol).toBe(true);
      expect(axisStep2?.perpWitnessOpacityScale).toBe(1);

      // Step 5 (cutting plane α) & Step 6 (circular section): foundation OO′ ⊥ (O) stays subordinated (never deleted), cutting plane OO′ ⊥ (α) at M active!
      for (const sIdx of [4, 5]) {
        const anchor = steps[sIdx]!.anchor;
        const roles = resolveStepVisualRoles(scene, anchor, { auxiliaryShown: false, selectedId: null });
        expect(roles.get("tru__axis")?.showPerpWitnessSymbol).toBe(true);
        expect(roles.get("tru__axis")?.perpWitnessOpacityScale).toBeLessThanOrEqual(0.5);
        expect(roles.get("P")?.showPerpWitnessSymbol).toBe(true);

        // Fallback R=2 retired from default canvas once cylinder body exists
        const annsDefault = annotationsAt(scene, anchor, DEFAULT_ANNOTATION_VIEW, null);
        expect(annsDefault).toHaveLength(0);

        // Preserved & clickable in #dock-given-params
        const summary = givenQuantitiesSummary(scene, anchor);
        expect(summary.map((g) => g.text)).toContain("R = 2");
        expect(summary.every((g) => g.status === "unattached_scalar")).toBe(true);

        // Clicking R = 2 pill in #dock-given-params reveals R = 2 on base circle
        const rId = summary.find((g) => g.text === "R = 2")!.id;
        const annsPicked = annotationsAt(scene, anchor, DEFAULT_ANNOTATION_VIEW, rId);
        expect(annsPicked.map((a) => a.text)).toContain("R = 2");
      }

      // Backward scrub Step 6 -> Step 2 restores foundation OO′ ⊥ (O) deterministically
      const rolesStep2Back = resolveStepVisualRoles(scene, steps[1]!.anchor, { auxiliaryShown: false, selectedId: null });
      expect(rolesStep2Back.get("tru__axis")?.showPerpWitnessSymbol).toBe(true);

      // Verify zero synthetic perp_plane_ray:P or ungrounded perp_marker:P on cylinder cutting plane P
      const planeP = scene.objects.find((o) => o.id === "P")!;
      const groupP = buildObject3D(
        planeP,
        false,
        0.1,
        [],
        new THREE.Vector3(8, 3, 6),
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
        scene.objects,
      );
      expect(groupP).not.toBeNull();
      expect(groupP!.getObjectByName("perp_plane_ray:P")).toBeUndefined();
      expect(groupP!.getObjectByName("perp_marker:P")).toBeUndefined();
    });

    it("preserves mathematical & visual distinction between tilted right circular cylinder (`tru-truc-xien`) and genuine oblique cylinder", () => {
      const tiltedRight = loadSampleScene("tru-truc-xien");
      const tiltedSolid = tiltedRight.objects.find((o) => o.type === "curved_solid")!;
      const tiltedOrth = inspectAxialCurvedOrthogonality(tiltedRight, tiltedSolid);
      expect(tiltedOrth?.isRightCertified).toBe(true);
      expect(tiltedOrth?.isTiltedAxisInSpace).toBe(true);

      const tiltedSteps = pedagogicalStepList(tiltedRight);
      const tiltedFinalRoles = resolveStepVisualRoles(tiltedRight, tiltedSteps[tiltedSteps.length - 1]!.anchor, {
        auxiliaryShown: false,
        selectedId: null,
      });
      const anyActivePerpOnTilted = [...tiltedFinalRoles.values()].some((r) => r.showPerpWitnessSymbol === true);
      expect(anyActivePerpOnTilted).toBe(true);

      const genuineOblique: Scene3D = withSubEntities({
        free_objects: ["O", "O_prime", "q_r"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "O", type: "point3", label: "Tâm O", notation: "O", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "O_prime", type: "point3", label: "Tâm O′", notation: "O′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "4"] },
          { id: "q_r", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["tru_xien"], value: "2", exact: { kind: "rational", value: "2" }, source: { fact_id: "f_r" } },
          { id: "day_duoi", type: "circle3", label: "Đáy (O)", notation: "(O)", origin: "derived", producer: null, render: "circle", surface_role: "BASE_REGION", depends: ["O"], center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "4" },
          { id: "noi_tam", type: "segment3", label: "Đoạn nối tâm OO′", notation: "OO′", origin: "derived", producer: null, render: "segment", depends: ["O", "O_prime"], endpoint_ids: ["O", "O_prime"], endpoints: [["0", "0", "0"], ["2", "0", "4"]] },
          { id: "day_tren", type: "circle3", label: "Đáy (O′)", notation: "(O′)", origin: "derived", producer: null, render: "circle", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_TRANSLATED_FACE"], depends: ["O_prime"], center: ["2", "0", "4"], normal: ["0", "0", "1"], radius_sq: "4" },
          { id: "tru_xien", type: "curved_solid", curved_kind: "cylinder", label: "Hình trụ xiên", notation: "(T)", origin: "derived", producer: null, render: "curved_solid", depends: ["O", "O_prime", "day_duoi", "day_tren"], anchor: ["0", "0", "0"], apex_or_top: ["2", "0", "4"], radius_sq: "4", height_sq: "16" },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_duoi", depends: ["O"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "noi_tam", depends: ["O", "O_prime"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "day_tren", depends: ["O_prime"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "tru_xien", depends: ["O", "O_prime", "day_duoi", "day_tren"], explanation: "" },
        ],
      });
      const obliqueSolid = genuineOblique.objects.find((o) => o.type === "curved_solid")!;
      const obliqueOrth = inspectAxialCurvedOrthogonality(genuineOblique, obliqueSolid);
      expect(obliqueOrth?.isOblique).toBe(true);
      expect(obliqueOrth?.isRightCertified).toBe(false);
      const obliqueSteps = pedagogicalStepList(genuineOblique);
      const obliqueFinalRoles = resolveStepVisualRoles(genuineOblique, obliqueSteps[obliqueSteps.length - 1]!.anchor, {
        auxiliaryShown: false,
        selectedId: null,
      });
      expect([...obliqueFinalRoles.values()].some((r) => r.showPerpWitnessSymbol === true)).toBe(false);
    });
  });

  describe("§6 — Root-Cause `PedagogicalNarrationPolicy` for Verbose Step Cards (`thiet-dien-chop` & General Polyhedral Sections)", () => {
    it("separates actionTitle, exact-verified conciseRationale, and lossless canonicalized detailedEvidence with collapsed [data-step-evidence-toggle] drawer", () => {
      const sample = GEOMETRY_SAMPLES.find((s) => s.id === "thiet-dien-chop")!;
      const scene = loadSampleScene("thiet-dien-chop");
      const steps = pedagogicalStepList(scene);
      const finalStep = steps[steps.length - 1]!;

      const nar = buildPedagogicalStepNarration(scene, finalStep);
      expect(nar.actionTitle).toContain("(MNPQ)");
      expect(nar.conciseRationale).toBe(
        "Thiết diện (MNPQ) đi qua trung điểm của bốn cạnh bên và song song với mặt đáy (ABCD).",
      );
      expect(nar.detailedEvidence.length).toBeGreaterThanOrEqual(2);

      const joinedEvidence = nar.detailedEvidence.join(" | ");
      // Canonical face tokens: (SAB), (SBC), (SCD), (SDA) — never raw inverted (ABS)!
      expect(joinedEvidence).toContain("(SAB)");
      expect(joinedEvidence).toContain("(SBC)");
      expect(joinedEvidence).toContain("(SCD)");
      expect(joinedEvidence).not.toContain("(ABS)");
      // Lossless preservation of parallel segment relations
      expect(joinedEvidence).toContain("MN ∥ AB");
      expect(joinedEvidence).toContain("NP ∥ BC");
      expect(joinedEvidence).toContain("PQ ∥ CD");

      // Consolidated plane (MNP) attenuated & host pyramid edge dimension pills retired on final section canvas
      const finalRoles = resolveStepVisualRoles(scene, finalStep.anchor, { auxiliaryShown: false, selectedId: null });
      const cutPlaneEntry = [...finalRoles.values()].find((r) => r.semanticRole === "CUTTING_PLANE");
      expect(cutPlaneEntry).toBeDefined();
      expect(cutPlaneEntry!.opacityScale).toBeLessThanOrEqual(0.32);

      const annsFinal = annotationsAt(scene, finalStep.anchor, DEFAULT_ANNOTATION_VIEW, null);
      expect(annsFinal).toHaveLength(0);

      // SSR workspace renders concise rationale + collapsed "Xem giải thích" button, NOT dumping detailedEvidence inline
      const ssrHtml = renderToString(
        <AxoWorkspaceV62
          scene={(sample.envelope as unknown as { scene3d: Scene3D }).scene3d}
          de={sample.problemText}
          tieuDe={sample.id}
        />,
      );
      expect(ssrHtml).toContain("Thiết diện (MNPQ) đi qua trung điểm của bốn cạnh bên và song song với mặt đáy (ABCD).");
      expect(ssrHtml).toContain("data-step-evidence-toggle");
      expect(ssrHtml).toContain("Xem giải thích");
      expect(ssrHtml).not.toContain("step-evidence-drawer");
    });
  });

  describe("§9.B — 8 Unseen Offline Scene3D Problems Across Diverse Families", () => {
    const unseenCases: { name: string; raw: Scene3D }[] = [
      { name: "B1-pyramid-two-plane-intersection", raw: UNSEEN_PYRAMID_TWO_PLANE_INTERSECTION },
      { name: "B2-regular-pyramid-1-to-2-ratio-section", raw: UNSEEN_REGULAR_PYRAMID_RATIO_SECTION },
      { name: "B3-right-prism-inclined-section", raw: UNSEEN_RIGHT_PRISM_SECTION },
      { name: "B4-sphere-inclined-plane-section", raw: UNSEEN_SPHERE_INCLINED_PLANE },
      { name: "B5-cylinder-perp-cut-section", raw: UNSEEN_CYLINDER_PERP_CUT },
      { name: "B6-cone-generators-axial-section", raw: UNSEEN_CONE_GENERATORS_AXIAL },
      { name: "B7-point-to-plane-distance", raw: UNSEEN_POINT_PLANE_DISTANCE },
      { name: "B8-multi-auxiliary-construction", raw: UNSEEN_MULTI_AUXILIARY_CONSTRUCTION },
    ];

    it("certifies all 8 unseen problems across families under exact verification, DAG continuity, 4D visual continuity, and non-spoiler policy", () => {
      for (const c of unseenCases) {
        const scene = withSubEntities(c.raw);
        registerExactSceneOrigin(scene, c.raw);
        const mathCons = verifySceneMathematicalConsistency(scene);
        expect(mathCons.valid, `${c.name}: ${mathCons.contradictions.map((v) => v.explanation).join("; ")}`).toBe(true);

        const geoCont = verifyConstructionContinuity(scene);
        expect(geoCont.valid, `${c.name}: ${geoCont.violations.map((v) => v.detail).join("; ")}`).toBe(true);

        const visCont = verifyVisualContinuity(scene);
        expect(visCont.valid, `${c.name}: ${visCont.violations.map((v) => v.detail).join("; ")}`).toBe(true);
      }

      // Specific family assertions:
      // B2: non-midpoint parallel section IJKL ∥ (EFGH) gets non-midpoint parallel conciseRationale & retires un-anchored SO ⊥ (EFGH) at Step 9
      const b2 = withSubEntities(UNSEEN_REGULAR_PYRAMID_RATIO_SECTION);
      registerExactSceneOrigin(b2, UNSEEN_REGULAR_PYRAMID_RATIO_SECTION);
      const b2Steps = pedagogicalStepList(b2);
      const b2Final = b2Steps[b2Steps.length - 1]!;
      const b2Nar = buildPedagogicalStepNarration(b2, b2Final);
      expect(b2Nar.conciseRationale).toContain("song song với mặt đáy (EFGH)");
      expect(b2Nar.conciseRationale).not.toContain("trung điểm");
      expect(b2Nar.detailedEvidence.join(" ")).toContain("(SEF)");
      expect(b2Nar.detailedEvidence.join(" ")).not.toContain("(EFS)");
      const b2Roles = resolveStepVisualRoles(b2, b2Final.anchor, { auxiliaryShown: false, selectedId: null });
      expect(b2Roles.get("cao_SO")?.showPerpWitnessSymbol).toBe(true);
      expect(b2Roles.get("cao_SO")?.perpWitnessOpacityScale).toBeLessThanOrEqual(0.5);

      // B6: Cone axial section SMN preserves SO ⊥ MN at O because MN is a real visible diameter segment through O!
      const b6 = withSubEntities(UNSEEN_CONE_GENERATORS_AXIAL);
      registerExactSceneOrigin(b6, UNSEEN_CONE_GENERATORS_AXIAL);
      const b6Steps = pedagogicalStepList(b6);
      const b6Roles = resolveStepVisualRoles(b6, b6Steps[b6Steps.length - 1]!.anchor, {
        auxiliaryShown: false,
        selectedId: null,
      });
      expect(b6Roles.get("truc_SO")?.showPerpWitnessSymbol).toBe(true);

      // B7: Point-plane distance keeps AH ⊥ (SBC) at primary opacity 1.0 and subordinates SA ⊥ (ABCD) to 0.45, hiding √2
      const b7 = withSubEntities(UNSEEN_POINT_PLANE_DISTANCE);
      registerExactSceneOrigin(b7, UNSEEN_POINT_PLANE_DISTANCE);
      const b7Steps = pedagogicalStepList(b7);
      const b7Roles = resolveStepVisualRoles(b7, b7Steps[b7Steps.length - 1]!.anchor, {
        auxiliaryShown: false,
        selectedId: null,
      });
      expect(b7Roles.get("doan_AH")?.showPerpWitnessSymbol).toBe(true);
      expect(b7Roles.get("doan_AH")?.perpWitnessOpacityScale).toBe(1);
      expect(b7Roles.get("cao_SA")?.showPerpWitnessSymbol).toBe(true);
      expect(b7Roles.get("cao_SA")?.perpWitnessOpacityScale).toBeLessThanOrEqual(0.5);
      expect(annotationsAt(b7, b7Steps[b7Steps.length - 1]!.anchor, DEFAULT_ANNOTATION_VIEW, null).some((a) => a.text.includes("√2"))).toBe(
        false,
      );

      // B8: Multi-auxiliary lines retire once intersection vertices E and Q are constructed
      const b8 = withSubEntities(UNSEEN_MULTI_AUXILIARY_CONSTRUCTION);
      const b8Steps = pedagogicalStepList(b8);
      const b8FinalRoles = resolveStepVisualRoles(b8, b8Steps[b8Steps.length - 1]!.anchor, {
        auxiliaryShown: false,
        selectedId: null,
      });
      expect(b8FinalRoles.get("aux_line_MN")?.visible).toBe(true);
      expect(b8FinalRoles.get("aux_line_MN")?.opacityScale).toBeLessThanOrEqual(0.45);
      expect(b8FinalRoles.get("aux_line_EP")?.visible).toBe(true);
      expect(b8FinalRoles.get("aux_line_EP")?.opacityScale).toBeLessThanOrEqual(0.45);
      expect(b8FinalRoles.get("td_MNPQ")?.visible).toBe(true);
      expect(b8FinalRoles.get("td_MNPQ")?.role).toBe("PRIMARY");
    });
  });

  describe("§9.C — 10 Metamorphic Invariance Transformations", () => {
    it("preserves presentation policy, narration structure, 4D visual continuity, camera/viewport non-overlap, and metric invariance across all 10 metamorphic transforms", () => {
      const baseRaw = UNSEEN_REGULAR_PYRAMID_RATIO_SECTION;
      const baseScene = withSubEntities(baseRaw);
      registerExactSceneOrigin(baseScene, baseRaw);

      // (1) Vertex renaming: S,E,F,G,H,O,I,J,K,L -> T,A,B,C,D,U,M,N,P,Q
      const renameMap: Record<string, string> = {
        S: "T", E: "A", F: "B", G: "C", H: "D", O: "U", I: "M", J: "N", K: "P", L: "Q",
        day_EFGH: "day_ABCD", cao_SO: "cao_TU", khoi_SEFGH: "khoi_TABCD", mp_IJK: "mp_MNP", canh_SH: "canh_TD", td_IJKL: "td_MNPQ",
      };
      const renameTokens = (s: string) =>
        s.replace(/S\.EFGH/g, "T.ABCD")
         .replace(/EFGH/g, "ABCD")
         .replace(/IJKL/g, "MNPQ")
         .replace(/IJK/g, "MNP")
         .replace(/\b(S|E|F|G|H|O|I|J|K|L)\b/g, (m) => renameMap[m] ?? m);
      const renamedRaw = transformScene(
        baseRaw,
        (v) => v,
        (v) => v,
        [1n, 1n],
        (id) => renameMap[id] ?? id,
        renameTokens,
      );
      const renamedScene = withSubEntities(renamedRaw);
      registerExactSceneOrigin(renamedScene, renamedRaw);
      expect(verifyVisualContinuity(renamedScene).valid).toBe(true);
      const renamedSteps = pedagogicalStepList(renamedScene);
      const renamedNar = buildPedagogicalStepNarration(renamedScene, renamedSteps[renamedSteps.length - 1]!);
      expect(renamedNar.conciseRationale).toContain("song song với mặt đáy (ABCD)");

      // (2) Exact rational translation + (7/2, -5/3, 4)
      const shift: [bigint, bigint][] = [[7n, 2n], [-5n, 3n], [4n, 1n]];
      const translatedRaw = transformScene(
        baseRaw,
        (v) => [
          fmtFrac(...fAdd(parseFrac(v[0]), shift[0]!)),
          fmtFrac(...fAdd(parseFrac(v[1]), shift[1]!)),
          fmtFrac(...fAdd(parseFrac(v[2]), shift[2]!)),
        ],
        (v) => v,
        [1n, 1n],
      );
      const translatedScene = withSubEntities(translatedRaw);
      registerExactSceneOrigin(translatedScene, translatedRaw);
      expect(verifyVisualContinuity(translatedScene).valid).toBe(true);

      // (3) Exact 3D orthogonal rotation (x, y, z) -> (-y, x, z)
      const rotPt = (v: ExactVec3): ExactVec3 => {
        const fx = parseFrac(v[0]);
        const fy = parseFrac(v[1]);
        return [fmtFrac(-fy[0], fy[1]), fmtFrac(fx[0], fx[1]), v[2]];
      };
      const rotatedRaw = transformScene(baseRaw, rotPt, rotPt, [1n, 1n]);
      const rotatedScene = withSubEntities(rotatedRaw);
      registerExactSceneOrigin(rotatedScene, rotatedRaw);
      expect(verifyVisualContinuity(rotatedScene).valid).toBe(true);

      // (4) Uniform rational scaling × 3/2 (scaleSq = 9/4)
      const scaleVec = (v: ExactVec3): ExactVec3 =>
        v.map((c) => {
          const fc = fMul(parseFrac(c), [3n, 2n]);
          return fmtFrac(fc[0], fc[1]);
        }) as ExactVec3;
      const scaledRaw = transformScene(baseRaw, scaleVec, scaleVec, [9n, 4n]);
      const scaledScene = withSubEntities(scaledRaw);
      registerExactSceneOrigin(scaledScene, scaledRaw);
      expect(verifyVisualContinuity(scaledScene).valid).toBe(true);

      // (5) Camera orbit angles & (6) Viewports 375px, 430px, 768px, 1440px: zero overlapping placed labels + Study Dock guarantee
      const step3Anchor = pedagogicalStepList(baseScene)[2]!.anchor;
      const step3Anns = annotationsAt(baseScene, step3Anchor, DEFAULT_ANNOTATION_VIEW, null);
      const camAngles: [number, number, number][] = [
        [8, -9, 6],
        [-9, -7, 5],
        [6, 8, 7],
      ];
      const viewports = [
        { w: 375, h: 667 },
        { w: 430, h: 932 },
        { w: 768, h: 1024 },
        { w: 1440, h: 900 },
      ];
      for (const camPos of camAngles) {
        const cam = new THREE.PerspectiveCamera(42, 1.5, 0.1, 200);
        cam.position.set(...camPos);
        cam.up.set(0, 0, 1);
        cam.lookAt(0, 0, 1.5);
        cam.updateMatrixWorld(true);
        for (const vp of viewports) {
          cam.aspect = vp.w / vp.h;
          cam.updateProjectionMatrix();
          const items = step3Anns.flatMap((a) => {
            const world = annotationAnchor(baseScene, a);
            if (!world) return [];
            const ndc = new THREE.Vector3(...world).project(cam);
            return [{
              id: a.id,
              ax: ((ndc.x + 1) * 0.5) * vp.w,
              ay: ((-ndc.y + 1) * 0.5) * vp.h,
              w: 64,
              h: 24,
              priority: a.priority,
            }];
          });
          const placed = [...placeAnnotationLabels(items, [], vp).values()];
          for (let i = 0; i < placed.length; i += 1) {
            for (let j = i + 1; j < placed.length; j += 1) {
              const A = placed[i]!;
              const B = placed[j]!;
              const overlap = A.x < B.x + B.w && B.x < A.x + A.w && A.y < B.y + B.h && B.y < A.y + A.h;
              expect(overlap).toBe(false);
            }
          }
          // Even on narrow 375px viewport, givenQuantitiesSummary keeps 100% of certified givens accessible in Dock
          expect(givenQuantitiesSummary(baseScene, step3Anchor).length).toBeGreaterThanOrEqual(step3Anns.length);
        }
      }

      // (7) Valid non-identity SPD chart_metric G = diag(4, 1, 9) via veKhongGian
      const metricSceneRaw: Scene3D = {
        ...UNSEEN_POINT_PLANE_DISTANCE,
        chart_metric: [["4", "0", "0"], ["0", "1", "0"], ["0", "0", "9"]],
        objects: UNSEEN_POINT_PLANE_DISTANCE.objects.map((o) => {
          const mapCoord = (v: ExactVec3): ExactVec3 => [
            fmtFrac(...fMul(parseFrac(v[0]), [1n, 2n])),
            v[1],
            fmtFrac(...fMul(parseFrac(v[2]), [1n, 3n])),
          ];
          return {
            ...o,
            xyz: o.xyz ? mapCoord(o.xyz) : undefined,
            vertices: o.vertices?.map(mapCoord),
            endpoints: o.endpoints?.map(mapCoord) as SceneObject["endpoints"],
            perpendicular_witness: o.perpendicular_witness
              ? {
                  ...o.perpendicular_witness,
                  foot: mapCoord(o.perpendicular_witness.foot),
                  plane_directions: o.perpendicular_witness.plane_directions?.map(mapCoord) as [ExactVec3, ExactVec3] | undefined,
                  marker: {
                    ...o.perpendicular_witness.marker,
                    u: mapCoord(o.perpendicular_witness.marker.u),
                    v: mapCoord(o.perpendicular_witness.marker.v),
                  },
                }
              : undefined,
          };
        }),
      };
      const metricCharted = withSubEntities(veKhongGian(metricSceneRaw));
      registerExactSceneOrigin(metricCharted, metricSceneRaw);
      expect(verifyVisualContinuity(metricCharted).valid).toBe(true);

      // (8) Reversed & interleaved step access order determinism
      const steps = pedagogicalStepList(baseScene);
      const fwd = steps.map((st) => [...resolveStepVisualRoles(baseScene, st.anchor).entries()]);
      const rev = [...steps].reverse().map((st) => [...resolveStepVisualRoles(baseScene, st.anchor).entries()]).reverse();
      expect(rev).toEqual(fwd);

      // (9) Multiple co-role objects at the same step (symmetric generators ds_SM & ds_SN in B6)
      const b6 = withSubEntities(UNSEEN_CONE_GENERATORS_AXIAL);
      const b6FinalAnchor = pedagogicalStepList(b6).slice(-1)[0]!.anchor;
      const b6Roles = resolveStepVisualRoles(b6, b6FinalAnchor);
      expect(b6Roles.get("ds_SM")?.role).toBe(b6Roles.get("ds_SN")?.role);
      expect(b6Roles.get("ds_SM")?.opacityScale).toBe(b6Roles.get("ds_SN")?.opacityScale);

      // (10) Multiple co-existing ⊥ and ∥ relations in a single scene (SA ⊥ ABCD, AH ⊥ SBC, MN ∥ BC)
      const multiRelRaw: Scene3D = {
        ...UNSEEN_POINT_PLANE_DISTANCE,
        objects: [
          ...UNSEEN_POINT_PLANE_DISTANCE.objects,
          { id: "M_mid", type: "point3", label: "Trung điểm M của SB", notation: "M", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["S", "B"], xyz: ["1", "0", "1"] },
          { id: "N_mid", type: "point3", label: "Trung điểm N của SC", notation: "N", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["S", "C"], xyz: ["1", "1", "1"] },
          { id: "seg_MN", type: "segment3", label: "Giao tuyến MN", notation: "MN", origin: "derived", producer: "intersect_planes", render: "segment", formation_roles: ["DERIVE_INTERSECTION"], depends: ["M_mid", "N_mid"], endpoint_ids: ["M_mid", "N_mid"], endpoints: [["1", "0", "1"], ["1", "1", "1"]] },
        ],
        events: [
          ...UNSEEN_POINT_PLANE_DISTANCE.events.slice(0, -1),
          { step_index: 7, action: "CREATE", object: "M_mid", depends: ["S", "B"], explanation: "" },
          { step_index: 8, action: "CREATE", object: "N_mid", depends: ["S", "C"], explanation: "" },
          { step_index: 9, action: "CREATE", object: "seg_MN", depends: ["M_mid", "N_mid"], explanation: "", justification_text: "MN là đường trung bình tam giác SBC nên MN ∥ BC." },
          { step_index: 10, action: "MEASURE", object: "kq_d", depends: ["doan_AH"], explanation: "", semantic_kind: "FINAL_RESULT" },
        ],
      };
      const multiRel = withSubEntities(multiRelRaw);
      registerExactSceneOrigin(multiRel, multiRelRaw);
      expect(verifyVisualContinuity(multiRel).valid).toBe(true);
      const mrContract = getSemanticConstructionContract(multiRel);
      const allRels = [...mrContract.objectsById.values()].flatMap((spec) => spec.verifiedRelations);
      expect(allRels.some((r) => r.kind.includes("perp"))).toBe(true);
      expect(allRels.some((r) => r.kind.includes("parallel"))).toBe(true);
    });
  });

  describe("§11 — 8 Negative / Fault-Injection Detection Gates", () => {
    it("detects (1) obsolete transient auxiliary, (2) premature/non-orthogonal witness, (3) duplicate segment dimension deduplication, (4) verbose derivation condensation, (5) preserved parallel relation, (6) spoiler sanitization, (7) canonical face tokens, and (8) internal result exposure guard", () => {
      // (1) Auxiliary construction lines stay visible in subordinated context (opacityScale <= 0.45) while auxiliary cutting planes retire after closure
      const chop = loadSampleScene("thiet-dien-chop");
      const chopSteps = pedagogicalStepList(chop);
      const finalRoles = resolveStepVisualRoles(chop, chopSteps[chopSteps.length - 1]!.anchor);
      const auxLines = chop.objects.filter((o) => o.type === "line3");
      for (const al of auxLines) {
        expect(finalRoles.get(al.id)?.visible).toBe(true);
        expect(finalRoles.get(al.id)?.opacityScale).toBeLessThanOrEqual(0.45);
      }
      const measPlanes = chop.objects.filter((o) => o.type === "plane3" && o.surface_role !== "CUTTING_PLANE");
      for (const mp of measPlanes) {
        expect(finalRoles.get(mp.id)?.visible).toBe(false);
      }

      // (2) Non-orthogonal perpendicular_witness flagged by verifyVisualContinuity as UNVERIFIED_WITNESS_SYMBOL_SHOWN
      const fakePerpScene: Scene3D = withSubEntities({
        free_objects: ["A", "B", "C", "S"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
          { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
          { id: "S", type: "point3", label: "S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "1", "2"] },
          { id: "day_ABC", type: "polygon3", label: "ABC", notation: "ABC", origin: "derived", producer: null, render: "polygon", surface_role: "BASE_REGION", depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]] },
          { id: "fake_SA", type: "segment3", label: "SA", notation: "SA", origin: "derived", producer: null, render: "segment", depends: ["S", "A"], endpoint_ids: ["S", "A"], endpoints: [["1", "1", "2"], ["0", "0", "0"]], perpendicular_witness: { from: "S", foot: ["0", "0", "0"], foot_id: "A", on: "day_ABC", relation: "line_perp_plane", status: "GIVEN", plane_directions: [["2", "0", "0"], ["0", "2", "0"]], marker: { u: ["1", "0", "0"], v: ["1", "1", "2"] } } },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_ABC", depends: ["A", "B", "C"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "fake_SA", depends: ["S", "A"], explanation: "" },
        ],
      });
      const fakeRep = verifyVisualContinuity(fakePerpScene);
      expect(fakeRep.valid).toBe(false);
      expect(fakeRep.dimensions.semantic).toBe(false);
      expect(fakeRep.violations.some((v) => v.code === "UNVERIFIED_WITNESS_SYMBOL_SHOWN")).toBe(true);

      // (3) Tangent sphere (d = R = 5 on IH): deduplicates spatial segment badge to single d(I,(P)) = 5 on canvas while keeping both R = 5 and d(I,(P)) = 5 in #dock-given-params
      const tangentSphere: Scene3D = withSubEntities({
        free_objects: ["I", "q_r", "q_d"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "q_r", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["ball_t"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f_r" } },
          { id: "q_d", type: "quantity", label: "Khoảng cách d(I,(P))", notation: "d(I,(P))", origin: "free", producer: null, render: "readout", depends: ["I", "mp_t"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f_d" }, annotation: { kind: "distance", category: "measurement", role: "given", subject_ids: ["I", "H_t"], anchor: "segment" } },
          { id: "ball_t", type: "curved_solid", curved_kind: "ball", label: "(S)", notation: "(S)", origin: "derived", producer: null, render: "curved_solid", depends: ["I", "q_r"], anchor: ["0", "0", "0"], radius_sq: "25" },
          { id: "mp_t", type: "plane3", label: "(P)", notation: "(P)", origin: "derived", producer: null, render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["0", "0", "5"], normal: ["0", "0", "1"] },
          { id: "H_t", type: "point3", label: "H", notation: "H", origin: "derived", producer: null, render: "point_marker", depends: ["I", "mp_t"], xyz: ["0", "0", "5"] },
          { id: "doan_IH", type: "segment3", label: "IH", notation: "IH", origin: "derived", producer: null, render: "segment", depends: ["I", "H_t"], endpoint_ids: ["I", "H_t"], endpoints: [["0", "0", "0"], ["0", "0", "5"]], perpendicular_witness: { from: "I", foot: ["0", "0", "5"], foot_id: "H_t", on: "mp_t", relation: "line_perp_plane", status: "DERIVED_VERIFIED", plane_directions: [["1", "0", "0"], ["0", "1", "0"]], marker: { u: ["1", "0", "0"], v: ["0", "0", "-1"] } } },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "ball_t", depends: ["I", "q_r"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "mp_t", depends: [], explanation: "" },
          { step_index: 3, action: "CREATE", object: "H_t", depends: ["I", "mp_t"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "doan_IH", depends: ["I", "H_t"], explanation: "" },
        ],
      });
      expect(verifyVisualContinuity(tangentSphere).valid).toBe(true);
      const tanAnns = annotationsAt(tangentSphere, 4, DEFAULT_ANNOTATION_VIEW, null);
      expect(tanAnns).toHaveLength(1);
      expect(tanAnns[0]!.text).toBe("d(I,(P)) = 5");
      const tanDock = givenQuantitiesSummary(tangentSphere, 4);
      expect(tanDock.map((g) => g.text)).toEqual(expect.arrayContaining(["R = 5", "d(I,(P)) = 5"]));

      // (4) Verbose >=3 semicolon clauses in non-section subtitle condensed cleanly while preserving full text in detailedEvidence
      const verboseNar = buildPedagogicalStepNarration(chop, {
        index: 1,
        startAnchor: 1,
        anchor: 1,
        label: "Bước thử",
        title: "Xác định giao điểm phụ",
        subtitle: "Mệnh đề hình học thứ nhất; Mệnh đề song song MN ∥ AB; Mệnh đề bổ trợ thứ ba; Mệnh đề thứ tư",
        targetIds: ["A"],
        prerequisiteIds: [],
      });
      expect(verboseNar.conciseRationale).toBe("Mệnh đề hình học thứ nhất; Mệnh đề song song MN ∥ AB");
      expect(verboseNar.detailedEvidence.join(" ")).toContain("Mệnh đề thứ tư");

      // (5) Canonical face token normalization turns (ABS) -> (SAB) in learner text
      expect(canonicalizeSceneFaceTokensInText(chop, "(MNP) ∩ (ABS) = MN")).toBe("(MNP) ∩ (SAB) = MN");

      // (6) Spoiler sanitization strips numeric/symbolic answer assignments while keeping geometric intersections
      expect(sanitizeStudentDescriptorText("Diện tích thiết diện = 16π")).toBe("Diện tích thiết diện");
      expect(sanitizeStudentDescriptorText("Khoảng cách d = a√3/3")).toBe("Khoảng cách d");
      expect(sanitizeStudentDescriptorText("Giao điểm Q = SD ∩ (MNP)")).toBe("Giao điểm Q = SD ∩ (MNP)");

      // (7) Build plan certifies zero spoiler leaks in step titles/subtitles
      const plan = buildPedagogicalConstructionPlan(loadSampleScene("cau-cat-mat-phang"));
      for (const s of plan.steps) {
        expect(s.title).not.toContain("16π");
        expect(s.subtitle).not.toContain("16π");
      }

      // (8) Hidden active prerequisite flagged by verifyVisualContinuity as HIDDEN_ACTIVE_PREREQUISITE
      const hiddenPrereqScene: Scene3D = withSubEntities({
        free_objects: ["P1", "P2"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "P1", type: "point3", label: "P1", notation: "P1", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "P2", type: "point3", label: "P2", notation: "P2", origin: "free", producer: null, render: "non_visual", depends: [], xyz: ["2", "0", "0"] },
          { id: "seg_12", type: "segment3", label: "P1P2", notation: "P1P2", origin: "derived", producer: "construct_segment", render: "segment", depends: ["P1", "P2"], endpoint_ids: ["P1", "P2"], endpoints: [["0", "0", "0"], ["2", "0", "0"]] },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "seg_12", depends: ["P1", "P2"], explanation: "" },
        ],
      });
      const hiddenPrereqRep = verifyVisualContinuity(hiddenPrereqScene);
      expect(hiddenPrereqRep.valid).toBe(false);
      expect(hiddenPrereqRep.dimensions.visual).toBe(false);
      expect(hiddenPrereqRep.violations.some((v) => v.code === "HIDDEN_ACTIVE_PREREQUISITE")).toBe(true);
    });

    it("covers adversarial edge cases: (A) section-boundary GIVEN edge preserved, (B) open EXTEND partial section never leaks future vertex, (C) triangular prism base vs lateral rectangle discrimination, and (D) interior-polygon foot wide-open projection", () => {
      // (A) Diagonal section SAC on S.ABCD shares GIVEN edge SA = 4 while retiring non-section host edge AB = 2
      const diagSecRaw: Scene3D = {
        free_objects: ["A", "B", "C", "D", "S", "q_ab", "q_sa"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "2", "0"] },
          { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
          { id: "S", type: "point3", label: "Đỉnh S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
          { id: "day_ABCD", type: "polygon3", label: "Đáy ABCD", notation: "ABCD", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C", "D"], vertex_ids: ["A", "B", "C", "D"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]] },
          { id: "cao_SA", type: "segment3", label: "Cạnh SA", notation: "SA", origin: "derived", producer: "construct_segment", render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["S", "A"], endpoint_ids: ["S", "A"], endpoints: [["0", "0", "4"], ["0", "0", "0"]] },
          { id: "khoi_SABCD", type: "solid", label: "Chóp S.ABCD", notation: "S.ABCD", shape_class: "PYRAMID_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["S", "A", "B", "C", "D"], vertex_ids: ["S", "A", "B", "C", "D"], vertices: [["0", "0", "4"], ["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]] },
          { id: "mp_SAC", type: "plane3", label: "Mặt phẳng (SAC)", notation: "(SAC)", origin: "derived", producer: "construct_plane", render: "surface", surface_role: "CUTTING_PLANE", depends: ["S", "A", "C"], point: ["0", "0", "0"], normal: ["1", "-1", "0"] },
          { id: "td_SAC", type: "section", label: "Thiết diện SAC", notation: "SAC", origin: "derived", producer: "intersect_plane_solid", render: "polygon", depends: ["khoi_SABCD", "mp_SAC"], polygon: [["0", "0", "4"], ["0", "0", "0"], ["2", "2", "0"]], closed: true },
          { id: "q_ab", type: "quantity", label: "Cạnh AB", notation: "AB", origin: "free", producer: null, render: "readout", depends: ["A", "B"], value: "2", exact: { kind: "rational", value: "2" }, source: { fact_id: "f_ab" }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "B"], anchor: "segment" } },
          { id: "q_sa", type: "quantity", label: "Cạnh SA", notation: "SA", origin: "free", producer: null, render: "readout", depends: ["S", "A"], value: "4", exact: { kind: "rational", value: "4" }, source: { fact_id: "f_sa" }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["S", "A"], anchor: "segment" } },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_ABCD", depends: ["A", "B", "C", "D"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "cao_SA", depends: ["S", "A"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "khoi_SABCD", depends: ["S", "A", "B", "C", "D"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "mp_SAC", depends: ["S", "A", "C"], explanation: "" },
          { step_index: 5, action: "CREATE", object: "td_SAC", depends: ["khoi_SABCD", "mp_SAC"], explanation: "" },
        ],
      };
      const diagSec = withSubEntities(diagSecRaw);
      registerExactSceneOrigin(diagSec, diagSecRaw);
      const diagAnnsBeforeSec = annotationsAt(diagSec, 3, DEFAULT_ANNOTATION_VIEW, null);
      expect(diagAnnsBeforeSec.map((a) => a.text)).toEqual(expect.arrayContaining(["SA = 4", "AB = 2"]));
      const diagAnnsFinal = annotationsAt(diagSec, 5, DEFAULT_ANNOTATION_VIEW, null);
      expect(diagAnnsFinal.map((a) => a.text)).toContain("SA = 4");
      expect(diagAnnsFinal.map((a) => a.text)).not.toContain("AB = 2");
      expect(givenQuantitiesSummary(diagSec, 5).map((g) => g.text)).toEqual(expect.arrayContaining(["SA = 4", "AB = 2"]));

      // (B) Open partial EXTEND section step (M, N, P before Q exists) never leaks future vertex Q or (MNPQ)
      const progressiveSecRaw: Scene3D = {
        free_objects: ["A", "B", "C", "D", "S"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["-2", "-2", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "-2", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "2", "0"] },
          { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["-2", "2", "0"] },
          { id: "S", type: "point3", label: "Đỉnh S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
          { id: "day_ABCD", type: "polygon3", label: "Đáy ABCD", notation: "ABCD", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C", "D"], vertex_ids: ["A", "B", "C", "D"], vertices: [["-2", "-2", "0"], ["2", "-2", "0"], ["2", "2", "0"], ["-2", "2", "0"]] },
          { id: "khoi_SABCD", type: "solid", label: "Chóp S.ABCD", notation: "S.ABCD", shape_class: "PYRAMID_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["S", "A", "B", "C", "D"], vertex_ids: ["S", "A", "B", "C", "D"], vertices: [["0", "0", "4"], ["-2", "-2", "0"], ["2", "-2", "0"], ["2", "2", "0"], ["-2", "2", "0"]], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]] },
          { id: "M", type: "point3", label: "Trung điểm M của SA", notation: "M", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["S", "A"], xyz: ["-1", "-1", "2"] },
          { id: "N", type: "point3", label: "Trung điểm N của SB", notation: "N", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["S", "B"], xyz: ["1", "-1", "2"] },
          { id: "P", type: "point3", label: "Trung điểm P của SC", notation: "P", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["S", "C"], xyz: ["1", "1", "2"] },
          { id: "mp_MNP", type: "plane3", label: "Mặt phẳng (MNP)", notation: "(MNP)", origin: "derived", producer: "construct_plane", render: "surface", surface_role: "CUTTING_PLANE", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: ["M", "N", "P"], point: ["-1", "-1", "2"], normal: ["0", "0", "1"] },
          { id: "Q", type: "point3", label: "Giao điểm Q = SD ∩ (MNP)", notation: "Q", origin: "derived", producer: "intersect_line_plane", render: "point_marker", formation_roles: ["DERIVE_INTERSECTION"], depends: ["S", "D", "mp_MNP"], xyz: ["-1", "1", "2"] },
          { id: "td_MNPQ", type: "section", label: "Thiết diện", notation: "", origin: "derived", producer: "intersect_plane_solid", render: "polygon", depends: ["khoi_SABCD", "mp_MNP"], polygon: [["-1", "-1", "2"], ["1", "-1", "2"], ["1", "1", "2"], ["-1", "1", "2"]], closed: true },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_ABCD", depends: ["A", "B", "C", "D"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "khoi_SABCD", depends: ["S", "A", "B", "C", "D"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "M", depends: ["S", "A"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "N", depends: ["S", "B"], explanation: "" },
          { step_index: 5, action: "CREATE", object: "P", depends: ["S", "C"], explanation: "" },
          { step_index: 6, action: "CREATE", object: "mp_MNP", depends: ["M", "N", "P"], explanation: "" },
          { step_index: 7, action: "EXTEND", object: "td_MNPQ", depends: ["khoi_SABCD", "mp_MNP"], explanation: "Nối các đoạn giao tuyến đầu tiên MN và NP" },
          { step_index: 8, action: "CREATE", object: "Q", depends: ["S", "D", "mp_MNP"], explanation: "" },
          { step_index: 9, action: "EXTEND", object: "td_MNPQ", depends: ["khoi_SABCD", "mp_MNP", "Q"], explanation: "Khép kín thiết diện (MNPQ)" },
        ],
        formation: {
          steps: [
            { step_index: 0, visible_ids: ["A", "B", "C", "D", "S"], readout_ids: [], geometry_progress: [] },
            { step_index: 1, visible_ids: ["A", "B", "C", "D", "S", "day_ABCD"], readout_ids: [], geometry_progress: [] },
            { step_index: 2, visible_ids: ["A", "B", "C", "D", "S", "day_ABCD", "khoi_SABCD"], readout_ids: [], geometry_progress: [] },
            { step_index: 3, visible_ids: ["A", "B", "C", "D", "S", "day_ABCD", "khoi_SABCD", "M"], readout_ids: [], geometry_progress: [] },
            { step_index: 4, visible_ids: ["A", "B", "C", "D", "S", "day_ABCD", "khoi_SABCD", "M", "N"], readout_ids: [], geometry_progress: [] },
            { step_index: 5, visible_ids: ["A", "B", "C", "D", "S", "day_ABCD", "khoi_SABCD", "M", "N", "P"], readout_ids: [], geometry_progress: [] },
            { step_index: 6, visible_ids: ["A", "B", "C", "D", "S", "day_ABCD", "khoi_SABCD", "M", "N", "P", "mp_MNP"], readout_ids: [], geometry_progress: [] },
            { step_index: 7, visible_ids: ["A", "B", "C", "D", "S", "day_ABCD", "khoi_SABCD", "M", "N", "P", "mp_MNP", "td_MNPQ"], readout_ids: [], geometry_progress: [{ object_id: "td_MNPQ", visible_edge_ids: ["e0", "e1"], closed: false, fill_visible: false }] },
            { step_index: 8, visible_ids: ["A", "B", "C", "D", "S", "day_ABCD", "khoi_SABCD", "M", "N", "P", "mp_MNP", "td_MNPQ", "Q"], readout_ids: [], geometry_progress: [{ object_id: "td_MNPQ", visible_edge_ids: ["e0", "e1"], closed: false, fill_visible: false }] },
            { step_index: 9, visible_ids: ["A", "B", "C", "D", "S", "day_ABCD", "khoi_SABCD", "M", "N", "P", "mp_MNP", "td_MNPQ", "Q"], readout_ids: [], geometry_progress: [{ object_id: "td_MNPQ", visible_edge_ids: ["e0", "e1", "e2", "e3"], closed: true, fill_visible: true }] },
          ],
        } as unknown as Scene3D["formation"],
      };
      const progSec = withSubEntities(progressiveSecRaw);
      registerExactSceneOrigin(progSec, progressiveSecRaw);
      const partialNar = buildPedagogicalStepNarration(progSec, {
        index: 5,
        startAnchor: 7,
        anchor: 7,
        label: "Bước mở",
        title: "Nối các đoạn giao tuyến đầu tiên MN và NP",
        subtitle: "Xác định hai giao tuyến trên các mặt bên (SAB) và (SBC).",
        targetIds: ["td_MNPQ"],
        prerequisiteIds: ["M", "N", "P"],
      });
      expect(partialNar.conciseRationale).not.toContain("MNPQ");
      expect(partialNar.conciseRationale).not.toContain("Q");
      expect(verifyVisualContinuity(progSec).valid).toBe(true);

      // (C) Triangular prism base vs lateral rectangle discrimination
      const triPrismMidRaw: Scene3D = {
        free_objects: ["A", "B", "C", "A1", "B1", "C1"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
          { id: "A1", type: "point3", label: "Điểm A′", notation: "A′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
          { id: "B1", type: "point3", label: "Điểm B′", notation: "B′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "4"] },
          { id: "C1", type: "point3", label: "Điểm C′", notation: "C′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "4"] },
          { id: "lt_abc", type: "solid", label: "Lăng trụ ABC.A′B′C′", notation: "ABC.A′B′C′", shape_class: "PRISM_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["A", "B", "C", "A1", "B1", "C1"], vertex_ids: ["A", "B", "C", "A1", "B1", "C1"], vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "4", "0"], ["0", "0", "4"], ["3", "0", "4"], ["0", "4", "4"]], faces: [[0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5], [0, 1, 2], [3, 4, 5]] },
          { id: "D_m", type: "point3", label: "Trung điểm D của AA′", notation: "D", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["A", "A1"], xyz: ["0", "0", "2"] },
          { id: "E_m", type: "point3", label: "Trung điểm E của BB′", notation: "E", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["B", "B1"], xyz: ["3", "0", "2"] },
          { id: "F_m", type: "point3", label: "Trung điểm F của CC′", notation: "F", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["C", "C1"], xyz: ["0", "4", "2"] },
          { id: "td_DEF", type: "section", label: "Thiết diện DEF", notation: "DEF", origin: "derived", producer: "intersect_plane_solid", render: "polygon", depends: ["lt_abc", "D_m", "E_m", "F_m"], polygon: [["0", "0", "2"], ["3", "0", "2"], ["0", "4", "2"]], closed: true },
          // Section parallel to lateral rectangle ABB′A′ (normal [0, 1, 0]): NOT parallel to triangular base!
          { id: "U1", type: "point3", label: "U1", notation: "U", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["A", "C"], xyz: ["0", "2", "0"] },
          { id: "U2", type: "point3", label: "U2", notation: "V", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["B", "C"], xyz: ["3/2", "2", "0"] },
          { id: "U3", type: "point3", label: "U3", notation: "V′", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["B1", "C1"], xyz: ["3/2", "2", "4"] },
          { id: "U4", type: "point3", label: "U4", notation: "U′", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["A1", "C1"], xyz: ["0", "2", "4"] },
          { id: "td_lat", type: "section", label: "Thiết diện UVV′U′", notation: "UVV′U′", origin: "derived", producer: "intersect_plane_solid", render: "polygon", depends: ["lt_abc", "U1", "U2", "U3", "U4"], polygon: [["0", "2", "0"], ["3/2", "2", "0"], ["3/2", "2", "4"], ["0", "2", "4"]], closed: true },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "lt_abc", depends: ["A", "B", "C", "A1", "B1", "C1"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "D_m", depends: ["A", "A1"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "E_m", depends: ["B", "B1"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "F_m", depends: ["C", "C1"], explanation: "" },
          { step_index: 5, action: "CREATE", object: "td_DEF", depends: ["lt_abc", "D_m", "E_m", "F_m"], explanation: "" },
          { step_index: 6, action: "CREATE", object: "U1", depends: ["A", "C"], explanation: "" },
          { step_index: 7, action: "CREATE", object: "U2", depends: ["B", "C"], explanation: "" },
          { step_index: 8, action: "CREATE", object: "U3", depends: ["B1", "C1"], explanation: "" },
          { step_index: 9, action: "CREATE", object: "U4", depends: ["A1", "C1"], explanation: "" },
          { step_index: 10, action: "CREATE", object: "td_lat", depends: ["lt_abc", "U1", "U2", "U3", "U4"], explanation: "" },
        ],
      };
      const triPrismMid = withSubEntities(triPrismMidRaw);
      registerExactSceneOrigin(triPrismMid, triPrismMidRaw);
      const defNar = buildPedagogicalStepNarration(triPrismMid, {
        index: 4,
        startAnchor: 5,
        anchor: 5,
        label: "Bước DEF",
        title: "Khép kín thiết diện (DEF)",
        subtitle: "Nối D, E, F.",
        targetIds: ["td_DEF"],
        prerequisiteIds: ["D_m", "E_m", "F_m"],
      });
      expect(defNar.conciseRationale).toContain("trung điểm của ba cạnh bên");
      expect(defNar.conciseRationale).toContain("song song với mặt đáy (ABC)");

      const latNar = buildPedagogicalStepNarration(triPrismMid, {
        index: 9,
        startAnchor: 10,
        anchor: 10,
        label: "Bước bên",
        title: "Khép kín thiết diện (UVV′U′)",
        subtitle: "Nối U, V, V′, U′.",
        targetIds: ["td_lat"],
        prerequisiteIds: ["U1", "U2", "U3", "U4"],
      });
      expect(latNar.conciseRationale).not.toContain("song song với mặt đáy");

      // (D) Interior-polygon altitude foot SO ⊥ EFGH at center O anchors perp_marker on base diagonals while corner SA ⊥ ABCD keeps [1, 0, 0]
      const sefghSub = withSubEntities(UNSEEN_REGULAR_PYRAMID_RATIO_SECTION);
      registerExactSceneOrigin(sefghSub, UNSEEN_REGULAR_PYRAMID_RATIO_SECTION);
      const sefgh = buildPedagogicalConstructionPlan(sefghSub).scene;
      registerExactSceneOrigin(sefgh, UNSEEN_REGULAR_PYRAMID_RATIO_SECTION);
      const caoSO = sefgh.objects.find((o) => o.id === "cao_SO")!;
      const sefghStep2Objs = sefgh.objects.filter((o) => ["E", "F", "G", "H", "O", "O__diag_1", "O__diag_2", "S", "day_EFGH", "cao_SO"].includes(o.id));
      const grpSO = buildObject3D(caoSO, false, undefined, [], undefined, undefined, undefined, false, "primary", true, true, false, sefgh, undefined, undefined, undefined, sefghStep2Objs) as THREE.Group;
      const soMarker = grpSO.children.find((c) => c.name === "perp_marker:cao_SO") as THREE.Line | undefined;
      expect(soMarker).toBeDefined();
      const soPos = soMarker!.geometry.getAttribute("position") as THREE.BufferAttribute;
      expect(Math.abs(soPos.getY(0))).toBeGreaterThan(0.05);

      const sabcd = withSubEntities(UNSEEN_POINT_PLANE_DISTANCE);
      registerExactSceneOrigin(sabcd, UNSEEN_POINT_PLANE_DISTANCE);
      const caoSA = sabcd.objects.find((o) => o.id === "cao_SA")!;
      const sabcdStep2Objs = sabcd.objects.filter((o) => ["A", "B", "C", "D", "S", "day_ABCD", "cao_SA"].includes(o.id));
      const grpSA = buildObject3D(caoSA, false, undefined, [], undefined, undefined, undefined, false, "primary", true, true, false, sabcd, undefined, undefined, undefined, sabcdStep2Objs) as THREE.Group;
      const saMarker = grpSA.children.find((c) => c.name === "perp_marker:cao_SA") as THREE.Line | undefined;
      expect(saMarker).toBeDefined();
      const saPos = saMarker!.geometry.getAttribute("position") as THREE.BufferAttribute;
      expect(Math.abs(saPos.getY(0))).toBeLessThan(1e-6);
      expect(saPos.getX(0)).toBeGreaterThan(0.05);
    });
  });
});
