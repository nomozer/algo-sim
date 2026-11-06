import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import samplesData from "../../../data/geometry-samples.json";
import { diemChoDuong, objectsAt, type ExactVec3, type Scene3D } from "./scene3d-model";
import { withSubEntities } from "./scene3d-subentities";
import { veKhongGian } from "./scene3d-chart";
import { auxiliaryHiddenAt } from "./scene3d-auxiliary";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import { stepCountOfEnvelope } from "../../../components/SessionCard";
import { historyStore } from "../../../state/history";

type ExactScalar = string;
import {
  buildContractReferenceGroup,
  buildPedagogicalConstructionPlan,
  buildStepEntityGroups,
  buildVerifiedObjectTooltip,
  classifyCurvedSegmentRole,
  classifyExactPolygonShape,
  classifySceneObjectSemantics,
  computeBoundedStudiedPlanePolygon,
  computeStepHighlightTargets,
  deriveExactPolygonMathBasis,
  findParallelBaseForPlane,
  isIntersectionLineOrSegment,
  pedagogicalStepList,
  registerExactSceneOrigin,
  resolveLineDisplaySpan,
  resolvePlaneSectionVisibility,
  resolveStudiedPlaneVisualStyle,
  verifySceneMathematicalConsistency,
} from "./scene3d-semantic-policy";
import { buildObject3D } from "./scene3d-view";
import { computeAdaptiveHeaderState } from "../../../components/TopNav";

type Frac = [bigint, bigint];

function gcd(a: bigint, b: bigint): bigint {
  let x = a < 0n ? -a : a;
  let y = b < 0n ? -b : b;
  while (y !== 0n) {
    const t = x % y;
    x = y;
    y = t;
  }
  return x === 0n ? 1n : x;
}

function norm([n, d]: Frac): Frac {
  if (d < 0n) return norm([-n, -d]);
  if (n === 0n) return [0n, 1n];
  const g = gcd(n, d);
  return [n / g, d / g];
}

function parseF(s: ExactScalar): Frac {
  const t = String(s).trim();
  if (t.includes("/")) {
    const [a, b] = t.split("/");
    return norm([BigInt(a), BigInt(b)]);
  }
  return [BigInt(t), 1n];
}

function fmtF([n, d]: Frac): ExactScalar {
  return d === 1n ? n.toString() : `${n.toString()}/${d.toString()}`;
}

function fAdd(a: Frac, b: Frac): Frac {
  return norm([a[0] * b[1] + b[0] * a[1], a[1] * b[1]]);
}

function fMul(a: Frac, b: Frac): Frac {
  return norm([a[0] * b[0], a[1] * b[1]]);
}

/**
 * Exact rational 3D rigid motion (det(R) = +1, R^T R = I) with non-axis-aligned orientation:
 * R = R_x(arcsin(4/5)) * R_z(arcsin(4/5)), entries in Q with denominator 25, plus translation T.
 */
function applyExactRigidMotionToVec(v: ExactVec3, translate = true): ExactVec3 {
  const [x, y, z] = v.map(parseF);
  // R1 (around Z): [[3/5, -4/5, 0], [4/5, 3/5, 0], [0, 0, 1]]
  const x1 = fAdd(fMul([3n, 5n], x), fMul([-4n, 5n], y));
  const y1 = fAdd(fMul([4n, 5n], x), fMul([3n, 5n], y));
  const z1 = z;
  // R2 (around X): [[1, 0, 0], [0, 3/5, -4/5], [0, 4/5, 3/5]]
  const rx = x1;
  const ry = fAdd(fMul([3n, 5n], y1), fMul([-4n, 5n], z1));
  const rz = fAdd(fMul([4n, 5n], y1), fMul([3n, 5n], z1));
  if (!translate) {
    return [fmtF(rx), fmtF(ry), fmtF(rz)];
  }
  const tx: Frac = [7n, 3n];
  const ty: Frac = [-5n, 2n];
  const tz: Frac = [11n, 4n];
  return [fmtF(fAdd(rx, tx)), fmtF(fAdd(ry, ty)), fmtF(fAdd(rz, tz))];
}

function applyExactRigidMotionToScene(scene: Scene3D): Scene3D {
  const clone: Scene3D = JSON.parse(JSON.stringify(scene));
  for (const o of clone.objects) {
    if (o.xyz) o.xyz = applyExactRigidMotionToVec(o.xyz, true);
    if (o.point) o.point = applyExactRigidMotionToVec(o.point, true);
    if (o.point_a) o.point_a = applyExactRigidMotionToVec(o.point_a, true);
    if (o.point_b) o.point_b = applyExactRigidMotionToVec(o.point_b, true);
    if (o.anchor) o.anchor = applyExactRigidMotionToVec(o.anchor, true);
    if (o.apex_or_top) o.apex_or_top = applyExactRigidMotionToVec(o.apex_or_top, true);
    if (o.center) o.center = applyExactRigidMotionToVec(o.center, true);
    if (o.direction) o.direction = applyExactRigidMotionToVec(o.direction, false);
    if (o.normal) o.normal = applyExactRigidMotionToVec(o.normal, false);
    if (o.vertices) o.vertices = o.vertices.map((pt) => applyExactRigidMotionToVec(pt, true));
    if (o.polygon) o.polygon = o.polygon.map((pt) => applyExactRigidMotionToVec(pt, true));
    if (o.endpoints) {
      o.endpoints = [
        applyExactRigidMotionToVec(o.endpoints[0], true),
        applyExactRigidMotionToVec(o.endpoints[1], true),
      ];
    }
    if (o.steps) {
      o.steps = o.steps.map((st) => ({
        ...st,
        a: applyExactRigidMotionToVec(st.a, true),
        b: applyExactRigidMotionToVec(st.b, true),
      }));
    }
    if (o.perpendicular_witness) {
      const w = o.perpendicular_witness;
      if (w.foot) w.foot = applyExactRigidMotionToVec(w.foot, true);
      if (w.plane_directions) {
        w.plane_directions = [
          applyExactRigidMotionToVec(w.plane_directions[0], false),
          applyExactRigidMotionToVec(w.plane_directions[1], false),
        ];
      }
      if (w.marker) {
        w.marker = {
          u: applyExactRigidMotionToVec(w.marker.u, false),
          v: applyExactRigidMotionToVec(w.marker.v, false),
        };
      }
    }
  }
  return clone;
}

function buildExteriorQPentagonScene(): Scene3D {
  return {
    version: 1,
    free_objects: ["A", "B", "C", "D", "S"],
    objects: [
      { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"], display_group: ["given"] },
      { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", render: "point", depends: [], xyz: ["2", "0", "0"], display_group: ["given"] },
      { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", render: "point", depends: [], xyz: ["2", "2", "0"], display_group: ["given"] },
      { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", render: "point", depends: [], xyz: ["0", "2", "0"], display_group: ["given"] },
      { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", render: "point", depends: [], xyz: ["0", "0", "4"], display_group: ["given"] },
      {
        id: "day",
        type: "polygon3",
        label: "Đáy ABCD",
        notation: "ABCD",
        origin: "derived",
        render: "polygon",
        surface_role: "BASE_REGION",
        formation_roles: ["CONSTRUCT_BASE"],
        depends: ["A", "B", "C", "D"],
        polygon: [["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]],
        closed: true,
      },
      {
        id: "chieu_cao_SA",
        type: "segment3",
        label: "Đường cao SA",
        notation: "SA",
        origin: "derived",
        render: "line",
        formation_roles: ["CONSTRUCT_HEIGHT"],
        depends: ["A", "S"],
        point_a: ["0", "0", "0"],
        point_b: ["0", "0", "4"],
        perpendicular_witness: {
          relation: "line_perp_plane",
          from: "S",
          on: "day",
          foot_id: "A",
          foot: ["0", "0", "0"],
          plane_directions: [["1", "0", "0"], ["0", "1", "0"]],
          marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] },
        },
      },
      {
        id: "chop",
        type: "solid",
        label: "Hình chóp S.ABCD",
        notation: "S.ABCD",
        origin: "derived",
        render: "mesh",
        formation_roles: ["CLOSE_SOLID"],
        depends: ["A", "B", "C", "D", "S"],
        vertex_ids: ["A", "B", "C", "D", "S"],
        vertices: [["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"], ["0", "0", "4"]],
        faces: [[0, 1, 2, 3], [4, 0, 1], [4, 1, 2], [4, 2, 3], [4, 3, 0]],
      },
      { id: "M", type: "point3", label: "Điểm M", notation: "M", origin: "derived", render: "point", depends: ["S", "A"], xyz: ["0", "0", "2"] },
      { id: "N", type: "point3", label: "Điểm N", notation: "N", origin: "derived", render: "point", depends: ["S", "B"], xyz: ["1", "0", "2"] },
      { id: "P", type: "point3", label: "Điểm P", notation: "P", origin: "derived", render: "point", depends: ["S", "C"], xyz: ["4/3", "4/3", "4/3"] },
      {
        id: "mp_mnp",
        type: "plane3",
        label: "Mặt phẳng (MNP)",
        notation: "(MNP)",
        origin: "derived",
        render: "surface",
        surface_role: "CUTTING_PLANE",
        formation_roles: ["CONSTRUCT_CUTTING_OBJECT"],
        depends: ["M", "N", "P"],
        point: ["0", "0", "2"],
        normal: ["0", "2", "3"],
      },
      {
        id: "line_sd",
        type: "line3",
        label: "Đường thẳng SD",
        notation: "SD",
        origin: "derived",
        render: "line",
        formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
        depends: ["S", "D"],
        point: ["0", "0", "4"],
        direction: ["0", "2", "-4"],
      },
      {
        id: "Q",
        type: "point3",
        label: "Điểm Q",
        notation: "Q",
        origin: "derived",
        render: "point",
        depends: ["line_sd", "mp_mnp"],
        xyz: ["0", "3", "-2"],
      },
      {
        id: "thiet_dien",
        type: "section",
        label: "Thiết diện",
        origin: "derived",
        render: "polygon",
        surface_role: "SECTION_REGION",
        formation_roles: ["PRODUCE_SECTION_RESULT"],
        depends: ["chop", "mp_mnp"],
        polygon: [
          ["0", "0", "2"],
          ["1", "0", "2"],
          ["4/3", "4/3", "4/3"],
          ["2", "3", "0"], // placeholder replaced below with exact pentagon on (MNP) 0*x + 2*y + 3*z = 6
        ],
        closed: true,
      },
    ],
    events: [
      { step_index: 0, action: "INIT", label: "Khởi tạo" },
      { step_index: 1, action: "CREATE", object: "day", label: "Đáy ABCD" },
      { step_index: 2, action: "CREATE", object: "chieu_cao_SA", label: "Đường cao SA" },
      { step_index: 3, action: "CREATE", object: "chop", label: "Hình chóp S.ABCD" },
      { step_index: 4, action: "CREATE", object: "M", label: "M" },
      { step_index: 5, action: "CREATE", object: "N", label: "N" },
      { step_index: 6, action: "CREATE", object: "P", label: "P" },
      { step_index: 7, action: "CREATE", object: "mp_mnp", label: "(MNP)" },
      { step_index: 8, action: "CREATE", object: "line_sd", label: "SD" },
      { step_index: 9, action: "CREATE", object: "Q", label: "Q" },
      { step_index: 10, action: "EXTEND", object: "thiet_dien", label: "Giao tuyến" },
      { step_index: 11, action: "STEP", object: "thiet_dien", label: "Thiết diện" },
    ],
  } as unknown as Scene3D;
}

describe("AXO Hybrid Generalization — Scene3D Mathematical Guard, Curved Families & Adaptive Header", () => {
  it("Case C (BUG S1): distinguishes exterior line-plane intersection Q from bounded 5-gon solid section and blocks exterior Q falsely placed inside section.polygon", () => {
    const validScene = buildExteriorQPentagonScene();
    // Plane (MNP): M=(0,0,2), N=(1,0,2), P=(4/3, 4/3, 1)? Check: with M=(0,0,2), N=(1,0,2), P=(3/2, 3/2, 1):
    // Plane equation: 0*x + 2*y + 3*z = 6 -> M: 6=6, N: 6=6, P=(3/2, 3/2, 1): 3+3=6!
    // Line SD: (0, 2t, 4 - 4t) -> 4t + 12 - 12t = 6 -> 8t = 6 -> Wait: for exterior t > 1, take M=(0,0,1), N=(1,0,2), P=(3/2,3/2,1), normal=(-1,1,1), -x+y+z=1!
    const mObj = validScene.objects.find((o) => o.id === "M")!;
    mObj.xyz = ["0", "0", "1"];
    const pObj = validScene.objects.find((o) => o.id === "P")!;
    pObj.xyz = ["3/2", "3/2", "1"];
    const mpObj = validScene.objects.find((o) => o.id === "mp_mnp")!;
    mpObj.point = ["0", "0", "1"];
    mpObj.normal = ["-1", "1", "1"];
    const qObj = validScene.objects.find((o) => o.id === "Q")!;
    qObj.xyz = ["0", "3", "-2"];
    const secObj = validScene.objects.find((o) => o.id === "thiet_dien")!;
    secObj.polygon = [
      ["0", "0", "1"],
      ["1", "0", "2"],
      ["3/2", "3/2", "1"],
      ["1", "2", "0"],
      ["0", "1", "0"],
    ];

    expect(verifySceneMathematicalConsistency(validScene).valid).toBe(true);

    const steps = pedagogicalStepList(validScene);
    const qStep = steps.find((s) => s.targetIds.includes("Q"))!;
    expect(qStep.epistemicCategory).toBe("derived");
    expect(qStep.subtitle).toMatch(/không phải đỉnh của thiết diện|ngoài miền khối/iu);

    const tipQ = buildVerifiedObjectTooltip(validScene, "Q", steps[steps.length - 1].anchor);
    expect(tipQ).not.toBeNull();
    expect(tipQ!.body).toMatch(/không phải đỉnh của thiết diện|ngoài miền khối/iu);

    // Corrupt section.polygon by replacing bounded base trace [(1,2,0), (0,1,0)] with exterior coplanar Q=(0,3,-2)!
    const corrupted: Scene3D = JSON.parse(JSON.stringify(validScene));
    const badSec = corrupted.objects.find((o) => o.id === "thiet_dien")!;
    badSec.polygon = [
      ["0", "0", "1"],
      ["1", "0", "2"],
      ["3/2", "3/2", "1"],
      ["0", "3", "-2"],
    ];
    const guard = verifySceneMathematicalConsistency(corrupted);
    expect(guard.valid).toBe(false);
    expect(guard.contradictions.some((c) => /ngoài miền khối/iu.test(c.title + " " + c.explanation))).toBe(true);
  });

  it("Curved Cone Frustum & Axial Section (BUG S2, S3, S5): hides intrinsic base plane, absorbs cap circle, distinguishes axis/radius/generator, and classifies sub-cone as derived", () => {
    const coneScene: Scene3D = {
      version: 1,
      free_objects: ["O", "R", "h", "S", "A", "O_prime", "r"],
      objects: [
        { id: "O", type: "point3", label: "Điểm O", notation: "O", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", render: "point", depends: [], xyz: ["0", "0", "4"] },
        { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["3", "0", "0"] },
        { id: "O_prime", type: "point3", label: "Điểm O′", notation: "O′", origin: "free", render: "point", depends: [], xyz: ["0", "0", "2"] },
        { id: "R", type: "quantity", label: "R", notation: "R", origin: "free", render: "non_visual", depends: [], value: "3" },
        { id: "h", type: "quantity", label: "h", notation: "h", origin: "free", render: "non_visual", depends: [], value: "4" },
        { id: "r", type: "quantity", label: "r", notation: "r", origin: "free", render: "non_visual", depends: [], value: "3/2" },
        {
          id: "khoi_cone1",
          type: "curved_solid",
          curved_kind: "cone",
          label: "Hình nón tròn xoay S.O đỉnh S",
          role: "Hình nón đáy tâm O, đỉnh S, qua A",
          origin: "derived",
          render: "curved_solid",
          formation_roles: ["CLOSE_SOLID"],
          depends: ["A", "O", "S"],
          anchor: ["0", "0", "0"],
          apex_or_top: ["0", "0", "4"],
          radius_sq: "9",
          height_sq: "16",
        },
        {
          id: "mp_day_cone1",
          type: "plane3",
          label: "Mặt phẳng đáy (O)",
          notation: "(O)",
          origin: "derived",
          render: "surface",
          surface_role: "CUTTING_PLANE",
          formation_roles: ["CONSTRUCT_CUTTING_OBJECT"],
          depends: [],
          point: ["0", "0", "0"],
          normal: ["0", "0", "1"],
        },
        {
          id: "duong_tron_day_cone1",
          type: "circle3",
          label: "Đường tròn giao của «Hình nón đáy tâm O, đỉnh S, qua A» và (O)",
          origin: "derived",
          render: "circle",
          surface_role: "BASE_REGION",
          formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
          depends: ["khoi_cone1", "mp_day_cone1"],
          center: ["0", "0", "0"],
          normal: ["0", "0", "4"],
          radius_sq: "9",
        },
        {
          id: "truc_O_S",
          type: "segment3",
          label: "Trục OS",
          notation: "OS",
          role: "Đoạn thẳng nối O và S",
          origin: "derived",
          render: "line",
          formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
          depends: ["O", "S"],
          point_a: ["0", "0", "0"],
          point_b: ["0", "0", "4"],
        },
        {
          id: "ban_kinh_O_A",
          type: "segment3",
          label: "Bán kính đáy OA",
          notation: "OA",
          role: "Đoạn thẳng nối O và A",
          origin: "derived",
          render: "line",
          formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
          depends: ["A", "O"],
          point_a: ["0", "0", "0"],
          point_b: ["3", "0", "0"],
        },
        {
          id: "duong_sinh_S_A",
          type: "segment3",
          label: "Đường sinh SA",
          notation: "SA",
          role: "Đoạn thẳng nối S và A",
          origin: "derived",
          render: "line",
          formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
          depends: ["A", "S"],
          point_a: ["0", "0", "4"],
          point_b: ["3", "0", "0"],
        },
        {
          id: "mp_sec_par",
          type: "plane3",
          label: "Mặt phẳng (α)",
          notation: "(α)",
          origin: "derived",
          render: "surface",
          surface_role: "CUTTING_PLANE",
          formation_roles: ["CONSTRUCT_CUTTING_OBJECT"],
          depends: [],
          point: ["0", "0", "2"],
          normal: ["0", "0", "1"],
        },
        {
          id: "td_sec_par",
          type: "circle3",
          label: "Đường tròn giao của «Hình nón đáy tâm O, đỉnh S, qua A» và (α)",
          origin: "derived",
          render: "circle",
          surface_role: "SECTION_REGION",
          formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
          depends: ["khoi_cone1", "mp_sec_par"],
          center: ["0", "0", "2"],
          normal: ["0", "0", "4"],
          radius_sq: "9/4",
        },
        {
          id: "khoi_cone_upper",
          type: "curved_solid",
          curved_kind: "cone",
          label: "Hình nón nhỏ đỉnh S cắt bởi (α)",
          role: "Hình nón đáy tâm O′, đỉnh S",
          origin: "derived",
          render: "curved_solid",
          formation_roles: ["CLOSE_SOLID"],
          depends: ["O_prime", "S", "r"],
          anchor: ["0", "0", "2"],
          apex_or_top: ["0", "0", "4"],
          radius_sq: "9/4",
          height_sq: "4",
        },
      ],
      events: [
        { step_index: 0, action: "INIT", label: "Bước dựng hình" },
        { step_index: 1, action: "CREATE", object: "khoi_cone1", display_label: "Hình nón tròn xoay S.O đỉnh S" },
        { step_index: 2, action: "CREATE", object: "mp_day_cone1", display_label: "Mặt phẳng đáy (O)" },
        { step_index: 3, action: "CREATE", object: "duong_tron_day_cone1", display_label: "Đường tròn đáy" },
        { step_index: 4, action: "CREATE", object: "truc_O_S", objects: ["truc_O_S"], display_label: "Trục OS" },
        { step_index: 5, action: "CREATE", object: "ban_kinh_O_A", objects: ["ban_kinh_O_A"], display_label: "Bán kính đáy OA" },
        { step_index: 6, action: "CREATE", object: "duong_sinh_S_A", objects: ["duong_sinh_S_A"], display_label: "Đường sinh SA" },
        { step_index: 7, action: "CREATE", object: "mp_sec_par", display_label: "Mặt phẳng (α)" },
        { step_index: 8, action: "CREATE", object: "td_sec_par", display_label: "Đường tròn thiết diện" },
        { step_index: 9, action: "CREATE", object: "khoi_cone_upper", display_label: "Hình nón nhỏ đỉnh S cắt bởi (α)" },
      ],
    } as unknown as Scene3D;

    const basePlaneVis = resolvePlaneSectionVisibility(coneScene, coneScene.objects.find((o) => o.id === "mp_day_cone1")!, 9, false, null);
    expect(basePlaneVis.subRole).toBe("SOLID_FACE_DUPLICATE_PLANE");
    expect(basePlaneVis.visible).toBe(false);

    const cutPlaneVis = resolvePlaneSectionVisibility(coneScene, coneScene.objects.find((o) => o.id === "mp_sec_par")!, 9, false, null);
    expect(cutPlaneVis.visible).toBe(true);

    const steps = pedagogicalStepList(coneScene);
    const titles = steps.map((s) => s.title);
    expect(titles.some((t) => t.includes("«"))).toBe(false);
    expect(titles.some((t) => /Mặt phẳng đáy/iu.test(t))).toBe(false);

    const osStep = steps.find((s) => s.targetIds.includes("truc_O_S"))!;
    expect(osStep.title).not.toMatch(/đường sinh/iu);
    expect(osStep.title).toMatch(/trục|đường cao/iu);

    const oaStep = steps.find((s) => s.targetIds.includes("ban_kinh_O_A"))!;
    expect(oaStep.title).not.toMatch(/đường sinh/iu);
    expect(oaStep.title).toMatch(/bán kính/iu);

    const saStep = steps.find((s) => s.targetIds.includes("duong_sinh_S_A"))!;
    expect(saStep.title).toMatch(/đường sinh SA/iu);

    const upperConeStep = steps.find((s) => s.targetIds.includes("khoi_cone_upper"))!;
    expect(upperConeStep.epistemicCategory).toBe("derived");
  });

  it("Curved Cylinder Axial Section (BUG S2, S4, S5): hides both cap planes, certifies axial section (ABB′A′) as rectangle, and cleans sphere/ellipse narration", () => {
    const cylScene: Scene3D = {
      version: 1,
      free_objects: ["O", "O_prime", "A", "A_prime", "B_prime"],
      objects: [
        { id: "O", type: "point3", label: "Điểm O", notation: "O", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "O_prime", type: "point3", label: "Điểm O′", notation: "O′", origin: "free", render: "point", depends: [], xyz: ["0", "0", "3"] },
        { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["2", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "derived", render: "point", depends: ["A", "O"], xyz: ["-2", "0", "0"] },
        { id: "A_prime", type: "point3", label: "Điểm A′", notation: "A′", origin: "free", render: "point", depends: [], xyz: ["2", "0", "3"] },
        { id: "B_prime", type: "point3", label: "Điểm B′", notation: "B′", origin: "free", render: "point", depends: [], xyz: ["-2", "0", "3"] },
        {
          id: "khoi_cyl",
          type: "curved_solid",
          curved_kind: "cylinder",
          label: "Hình trụ tròn xoay O.O' tâm O",
          origin: "derived",
          render: "curved_solid",
          formation_roles: ["CLOSE_SOLID"],
          depends: ["A", "O", "O_prime"],
          anchor: ["0", "0", "0"],
          apex_or_top: ["0", "0", "3"],
          radius_sq: "4",
          height_sq: "9",
        },
        {
          id: "mp_day_cyl",
          type: "plane3",
          label: "Mặt phẳng đáy (O)",
          notation: "(O)",
          origin: "derived",
          render: "surface",
          surface_role: "CUTTING_PLANE",
          formation_roles: ["CONSTRUCT_CUTTING_OBJECT"],
          depends: [],
          point: ["0", "0", "0"],
          normal: ["0", "0", "1"],
        },
        {
          id: "duong_tron_day_cyl",
          type: "circle3",
          label: "Đường tròn giao của «Hình trụ» và (O)",
          origin: "derived",
          render: "circle",
          surface_role: "BASE_REGION",
          depends: ["khoi_cyl", "mp_day_cyl"],
          center: ["0", "0", "0"],
          normal: ["0", "0", "3"],
          radius_sq: "4",
        },
        {
          id: "mp_day_tren_cyl",
          type: "plane3",
          label: "Mặt phẳng đáy trên (O')",
          notation: "(β)",
          origin: "derived",
          render: "surface",
          surface_role: "CUTTING_PLANE",
          formation_roles: ["CONSTRUCT_CUTTING_OBJECT"],
          depends: [],
          point: ["0", "0", "3"],
          normal: ["0", "0", "1"],
        },
        {
          id: "duong_tron_day_tren_cyl",
          type: "circle3",
          label: "Đường tròn giao của «Hình trụ» và (β)",
          origin: "derived",
          render: "circle",
          surface_role: "BASE_REGION",
          depends: ["khoi_cyl", "mp_day_tren_cyl"],
          center: ["0", "0", "3"],
          normal: ["0", "0", "3"],
          radius_sq: "4",
        },
        {
          id: "td_sec_axial",
          type: "polygon3",
          label: "Thiết diện qua trục hình trụ",
          notation: "ABB′A′",
          origin: "derived",
          render: "polygon",
          surface_role: "SECTION_REGION",
          depends: ["A", "B", "B_prime", "A_prime"],
          polygon: [["2", "0", "0"], ["-2", "0", "0"], ["-2", "0", "3"], ["2", "0", "3"]],
          closed: true,
        },
      ],
      events: [
        { step_index: 0, action: "INIT", label: "Khởi tạo" },
        { step_index: 1, action: "CREATE", object: "khoi_cyl", display_label: "Hình trụ" },
        { step_index: 2, action: "CREATE", object: "mp_day_cyl", display_label: "Mặt phẳng đáy (O)" },
        { step_index: 3, action: "CREATE", object: "duong_tron_day_cyl", display_label: "Đường tròn đáy" },
        { step_index: 4, action: "CREATE", object: "mp_day_tren_cyl", display_label: "Mặt phẳng đáy trên" },
        { step_index: 5, action: "CREATE", object: "duong_tron_day_tren_cyl", display_label: "Đường tròn đáy trên" },
        { step_index: 6, action: "CREATE", object: "B", display_label: "B" },
        { step_index: 7, action: "CREATE", object: "td_sec_axial", display_label: "Thiết diện qua trục" },
      ],
    } as unknown as Scene3D;

    expect(resolvePlaneSectionVisibility(cylScene, cylScene.objects.find((o) => o.id === "mp_day_cyl")!, 7, false, null).visible).toBe(false);
    expect(resolvePlaneSectionVisibility(cylScene, cylScene.objects.find((o) => o.id === "mp_day_tren_cyl")!, 7, false, null).visible).toBe(false);

    const axialBasis = deriveExactPolygonMathBasis(cylScene, cylScene.objects.find((o) => o.id === "td_sec_axial")!);
    expect(axialBasis).not.toBeNull();
    expect(axialBasis!.shape).toBe("hình chữ nhật");
    expect(axialBasis!.epistemicLevel).toBe("DERIVED");

    const cylSteps = pedagogicalStepList(cylScene);
    expect(cylSteps.some((s) => s.title.includes("«"))).toBe(false);
    expect(cylSteps[cylSteps.length - 1].title).toBe("Dựng thiết diện (ABB′A′)");
    expect(cylSteps[cylSteps.length - 1].title).not.toContain("hình chữ nhật");

    // Sphere narration deduplication & non-visual readout quantity absorption
    const sphScene: Scene3D = {
      version: 1,
      free_objects: ["I", "R"],
      objects: [
        { id: "I", type: "point3", label: "Điểm I", notation: "I", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "R", type: "quantity", label: "R", notation: "R", origin: "free", render: "non_visual", depends: [], value: "5" },
        {
          id: "khoi_sph",
          type: "curved_solid",
          curved_kind: "ball",
          label: "Mặt cầu (S) tâm I",
          role: "Khối cầu tâm I",
          origin: "derived",
          render: "curved_solid",
          depends: ["I", "R"],
          anchor: ["0", "0", "0"],
          radius_sq: "25",
        },
        {
          id: "mp_alpha",
          type: "plane3",
          label: "Mặt phẳng alpha",
          notation: "Mặt phẳng alpha",
          origin: "derived",
          render: "surface",
          surface_role: "CUTTING_PLANE",
          formation_roles: ["CONSTRUCT_CUTTING_OBJECT"],
          depends: [],
          point: ["0", "0", "3"],
          normal: ["0", "0", "1"],
        },
        {
          id: "td_sph",
          type: "circle3",
          label: "Đường tròn giao của «Khối cầu tâm I» và (α)",
          origin: "derived",
          render: "circle",
          surface_role: "SECTION_REGION",
          depends: ["khoi_sph", "mp_alpha"],
          center: ["0", "0", "3"],
          normal: ["0", "0", "1"],
          radius_sq: "16",
        },
        {
          id: "kq_sec",
          type: "quantity",
          label: "Diện tích «Đường tròn giao của khối cong và mặt phẳng»",
          origin: "derived",
          render: "readout",
          depends: ["td_sph"],
          value: "16*pi",
        },
      ],
      events: [
        { step_index: 0, action: "INIT", label: "Khởi tạo" },
        { step_index: 1, action: "CREATE", object: "khoi_sph", display_label: "Mặt cầu (S) tâm I" },
        { step_index: 2, action: "CREATE", object: "mp_alpha", display_label: "Mặt phẳng alpha" },
        { step_index: 3, action: "CREATE", object: "td_sph", display_label: "Đường tròn thiết diện" },
        { step_index: 4, action: "CREATE", object: "kq_sec", display_label: "Tính Diện tích «Đường tròn giao của khối cong và mặt phẳng»." },
      ],
    } as unknown as Scene3D;

    const sphSteps = pedagogicalStepList(sphScene);
    expect(sphSteps[0].title).not.toMatch(/Khối cầu tâm I tâm I/iu);
    expect(sphSteps.some((s) => /Mặt phẳng cắt Mặt phẳng/iu.test(s.title))).toBe(false);
    expect(sphSteps.some((s) => s.title.includes("«"))).toBe(false);
  });

  it("Case D: geometric verification & section classification are invariant under non-axis-aligned 3D rigid rotation + translation", () => {
    const baseScene = buildExteriorQPentagonScene();
    baseScene.objects.find((o) => o.id === "day")!.label = "Đáy ABCD là hình vuông";
    // Configure as right trapezoid (MAB) with M midpoint SC and SA ⊥ (ABCD)
    const mObj = baseScene.objects.find((o) => o.id === "M")!;
    mObj.xyz = ["1", "1", "2"];
    const secObj = baseScene.objects.find((o) => o.id === "thiet_dien")!;
    secObj.polygon = [
      ["0", "0", "0"],
      ["2", "0", "0"],
      ["1", "1", "2"],
      ["0", "1", "2"],
    ];
    // Add N=(0,1,2) midpoint SD so (ABMN) is a certified right trapezoid
    const nObj = baseScene.objects.find((o) => o.id === "N")!;
    nObj.depends = ["S", "D"];
    nObj.xyz = ["0", "1", "2"];
    baseScene.objects = baseScene.objects.filter((o) => o.id !== "P" && o.id !== "Q" && o.id !== "line_sd");
    const mpObj = baseScene.objects.find((o) => o.id === "mp_mnp")!;
    mpObj.depends = ["A", "B", "M"];
    mpObj.point = ["0", "0", "0"];
    mpObj.normal = ["0", "2", "-1"];
    baseScene.events = baseScene.events.filter((e) => !["P", "Q", "line_sd"].includes(e.object ?? ""));

    const rotated = applyExactRigidMotionToScene(baseScene);
    expect(verifySceneMathematicalConsistency(baseScene).valid).toBe(true);
    expect(verifySceneMathematicalConsistency(rotated).valid).toBe(true);

    const basisOrig = deriveExactPolygonMathBasis(baseScene, baseScene.objects.find((o) => o.id === "thiet_dien")!)!;
    const basisRot = deriveExactPolygonMathBasis(rotated, rotated.objects.find((o) => o.id === "thiet_dien")!)!;
    expect(basisOrig.shape).toBe("hình thang vuông");
    expect(basisRot.shape).toBe(basisOrig.shape);
    expect(basisRot.epistemicLevel).toBe(basisOrig.epistemicLevel);
    expect(basisRot.cycleNotation).toBe(basisOrig.cycleNotation);
    expect(buildPedagogicalConstructionPlan(rotated).steps.map((s) => s.title)).toEqual(
      buildPedagogicalConstructionPlan(baseScene).steps.map((s) => s.title),
    );
  });

  it("Global UI/UX (Adaptive Header): computeAdaptiveHeaderState applies 8px/20px surface hysteresis without shrinking at any scroll depth", () => {
    let state = computeAdaptiveHeaderState(undefined, 0);
    expect(state.isScrolled).toBe(false);

    // Sub-threshold scroll (14px < 20px enter threshold) keeps header seamlessly blended with page
    state = computeAdaptiveHeaderState(state, 14);
    expect(state.isScrolled).toBe(false);

    // Downward scroll >= 20px activates elevated surface
    state = computeAdaptiveHeaderState(state, 20);
    expect(state.isScrolled).toBe(true);

    // Hovering back into hysteresis band (8px < 14px < 20px) keeps isScrolled=true (no threshold flicker)
    state = computeAdaptiveHeaderState(state, 14);
    expect(state.isScrolled).toBe(true);

    // Deep downward and upward scrolling keeps isScrolled=true with zero compact/shrink mode
    for (const y of [64, 96, 220, 140, 74, 9]) {
      state = computeAdaptiveHeaderState(state, y);
      expect(state.isScrolled).toBe(true);
      expect("isCompact" in (state as unknown as Record<string, unknown>)).toBe(false);
    }

    // Returning to top zone (<= 8px) restores seamless page-blended state
    state = computeAdaptiveHeaderState(state, 8);
    expect(state.isScrolled).toBe(false);
    state = computeAdaptiveHeaderState(state, 0);
    expect(state.isScrolled).toBe(false);
  });

  it("Section I: Guided Practice is cleanly removed while 'Xem mô phỏng', step-count parity, zero future leakage, and history sync are preserved across all 11 samples", () => {
    type SampleItem = { id: string; title: string; envelope: { description: string; scene3d: Scene3D } };
    const items = ((samplesData as unknown as { samples?: SampleItem[] }).samples ?? []) as SampleItem[];
    expect(items.length).toBe(11);

    for (const sample of items) {
      const check = verifySceneMathematicalConsistency(sample.envelope.scene3d);
      expect(check.valid, `${sample.id}: ${check.contradictions.map((c) => c.title).join("; ")}`).toBe(true);

      const enriched = withSubEntities(sample.envelope.scene3d);
      const pedPlan = buildPedagogicalConstructionPlan(enriched);
      const displayScene = registerExactSceneOrigin(veKhongGian(pedPlan.scene), pedPlan.scene);
      const viewSteps = pedagogicalStepList(displayScene);

      // Step-count parity across SessionCard, SimulationWorkspace, and Scene3DView
      const cardCount = stepCountOfEnvelope(
        sample.envelope as unknown as Parameters<typeof stepCountOfEnvelope>[0],
      );
      expect(cardCount).toBe(pedPlan.steps.length);
      expect(viewSteps.map((s) => s.title)).toEqual(pedPlan.steps.map((s) => s.title));

      // Zero future-object leakage across every pedagogical step
      const firstSeenStep = new Map<string, number>();
      for (let i = 0; i < pedPlan.steps.length; i++) {
        for (const obj of objectsAt(pedPlan.scene, pedPlan.steps[i].anchor)) {
          if (!firstSeenStep.has(obj.id)) firstSeenStep.set(obj.id, i);
        }
      }
      for (let i = 0; i < pedPlan.steps.length; i++) {
        const presentIds = new Set(objectsAt(pedPlan.scene, pedPlan.steps[i].anchor).map((o) => o.id));
        for (const [oid, firstIdx] of firstSeenStep.entries()) {
          if (firstIdx > i) {
            expect(presentIds.has(oid), `${sample.id} leaked ${oid} at step ${i} before ${firstIdx}`).toBe(false);
          }
        }
      }
    }

    // SSR check on representative polyhedral + curved samples: zero Guided Practice remnants, opens at completed model
    for (const sampleId of ["thiet-dien-chop", "tru-truc-xien", "cau-cat-mat-phang", "non-thiet-dien-truc"]) {
      const sample = items.find((s) => s.id === sampleId)!;
      const html = renderToString(
        <AxoWorkspaceV62
          scene={sample.envelope.scene3d}
          de={sample.envelope.description}
          tieuDe={sample.title}
        />,
      );
      expect(html).not.toContain("dock-learning-mode-switch");
      expect(html).not.toContain("dock-guided-practice-card");
      expect(html).not.toContain("Thực hành có hướng dẫn");
      expect(html).not.toContain("Kiểm chứng lựa chọn");
      expect(html).not.toContain("Bỏ qua bước này");
      expect(html).toContain("pa-prev");
      expect(html).toContain("pa-play");
      expect(html).toContain("pa-next");
      expect(html).toContain("floating-toolbar-3d");
      expect(html).toContain("dock-steps-ul");
    }

    // History store sync updates cursor without creating duplicate entries
    historyStore.clear();
    const s0 = items[0];
    const rec = historyStore.record(
      s0.envelope as unknown as Parameters<typeof historyStore.record>[0],
      s0.envelope.description,
    );
    historyStore.touch(rec.id, { lastCursor: 0 });
    historyStore.touch(rec.id, { lastCursor: 3 });
    expect(historyStore.list().length).toBe(1);
    expect(historyStore.list()[0].lastCursor).toBe(3);
    historyStore.clear();
  });

  it("Sections II–IV: curved foundation ('tru-truc-xien' 1->4 steps, sphere, cone, cylinder), prisms, undeclared & regular tetrahedra, hexagonal pyramid, centroid, carrier hiding, and plane-plane intersection line", () => {
    const items = ((samplesData as unknown as { samples?: Array<{ id: string; envelope: { scene3d: Scene3D } }> }).samples ?? []);
    const byId = new Map(items.map((s) => [s.id, s.envelope.scene3d]));

    // 1. Tilted-axis right cylinder ('tru-truc-xien'): grouped non-floating curved foundation + lateral surface (no pure answer step in timeline)
    const truXienPlan = buildPedagogicalConstructionPlan(withSubEntities(byId.get("tru-truc-xien")!));
    expect(truXienPlan.steps.length).toBe(3);
    expect(truXienPlan.steps.map((s) => s.title)).toEqual([
      "Dựng đường tròn đáy tâm O, bán kính OA của hình trụ",
      "Xác định tâm O′, dựng trục OO′ và đường tròn đáy tâm O′ của hình trụ",
      "Hoàn thiện mặt xung quanh hình trụ trục OO′",
    ]);
    for (const segId of ["tru__axis", "tru__radius"]) {
      const segObj = truXienPlan.scene.objects.find((o) => o.id === segId);
      expect(segObj?.render).toBe("segment");
      expect(segObj?.endpoints?.length).toBe(2);
    }

    // Other curved samples have grounded multi-step decompositions without fake steps, floating radii, or pure answer steps
    const cauVolPlan = buildPedagogicalConstructionPlan(withSubEntities(byId.get("cau-the-tich")!));
    const cauVolSteps = cauVolPlan.steps;
    expect(cauVolSteps.length).toBe(1);
    expect(cauVolSteps[0].title).toMatch(/Dựng mặt cầu.*tâm I.*đi qua A/iu);
    expect(cauVolSteps.some((s) => /^Tính /iu.test(s.title))).toBe(false);
    expect(cauVolPlan.scene.objects.find((o) => o.id === "cau__radius")?.render).toBe("segment");
    const truSecSteps = buildPedagogicalConstructionPlan(withSubEntities(byId.get("tru-thiet-dien-tron")!)).steps;
    expect(truSecSteps.length).toBeGreaterThanOrEqual(4);
    expect(truSecSteps[0].title).toBe("Dựng đường tròn đáy tâm O của hình trụ");
    const nonGenPlan = buildPedagogicalConstructionPlan(withSubEntities(byId.get("non-duong-sinh")!));
    expect(nonGenPlan.steps.length).toBe(4);
    expect(nonGenPlan.steps[0].title).toBe("Dựng đường tròn đáy tâm O, bán kính OA của hình nón");
    expect(nonGenPlan.steps[1].title).toMatch(/dựng đường cao.*SO của hình nón/iu);
    expect(nonGenPlan.steps[2].title).toMatch(/^Dựng đường sinh SA/u);
    expect(nonGenPlan.steps[3].title).toMatch(/^Hoàn thiện mặt xung quanh hình nón/u);
    expect(nonGenPlan.steps.some((s) => /^Tính /iu.test(s.title))).toBe(false);
    const nonAxialPlan = buildPedagogicalConstructionPlan(withSubEntities(byId.get("non-thiet-dien-truc")!));
    expect(nonAxialPlan.steps.length).toBeGreaterThanOrEqual(4);
    expect(nonAxialPlan.steps[0].title).toBe("Dựng đường tròn đáy tâm O, bán kính OA của hình nón");
    expect(nonAxialPlan.scene.objects.find((o) => o.id === "non__axis")?.render).toBe("segment");
    expect(nonAxialPlan.scene.objects.find((o) => o.id === "non__radius")?.render).toBe("segment");

    // 2. Regular tetrahedron ABCD (Gram chart_metric != I3) + auxiliary triangle ABM + workspace badge 'Tứ diện'
    const regTetScene: Scene3D = {
      version: 1,
      chart_metric: [
        ["36", "18", "18"],
        ["18", "36", "18"],
        ["18", "18", "36"],
      ],
      free_objects: ["A", "B", "C", "D"],
      objects: [
        { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", render: "point", depends: [], xyz: ["1", "0", "0"] },
        { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", render: "point", depends: [], xyz: ["0", "1", "0"] },
        { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", render: "point", depends: [], xyz: ["0", "0", "1"] },
        {
          id: "khoi_D_ABC",
          type: "solid",
          label: "Khối chóp D.ABC",
          role: "Tứ diện đều ABCD",
          notation: "D.ABC",
          origin: "derived",
          render: "polyhedron",
          depends: ["A", "B", "C", "D"],
          vertices: [["0", "0", "1"], ["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"]],
          faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]],
        },
        {
          id: "M",
          type: "point3",
          label: "Trung điểm M của CD",
          notation: "M",
          origin: "derived",
          producer: "construct_point.midpoint",
          render: "point",
          depends: ["C", "D"],
          xyz: ["0", "1/2", "1/2"],
        },
        {
          id: "da_giac_rt4",
          type: "polygon3",
          label: "Đa giác ABM",
          notation: "ABM",
          origin: "derived",
          render: "polygon",
          surface_role: "AUXILIARY_SURFACE",
          depends: ["A", "B", "M"],
          polygon: [["0", "0", "0"], ["1", "0", "0"], ["0", "1/2", "1/2"]],
          closed: true,
        },
      ],
      events: [
        { step_index: 0, action: "INIT", label: "Khởi tạo" },
        { step_index: 1, action: "CREATE", object: "khoi_D_ABC", display_label: "Khối chóp D.ABC" },
        { step_index: 2, action: "CREATE", object: "M", display_label: "Trung điểm M của CD" },
        { step_index: 3, action: "CREATE", object: "da_giac_rt4", display_label: "Đa giác ABM" },
      ],
    } as unknown as Scene3D;
    expect(verifySceneMathematicalConsistency(regTetScene).valid).toBe(true);
    const regTetPlan = buildPedagogicalConstructionPlan(withSubEntities(regTetScene));
    expect(regTetPlan.steps.map((s) => s.title)).toEqual([
      "Dựng tứ diện đều ABCD",
      "Xác định trung điểm M của CD",
      "Dựng tam giác ABM",
    ]);
    const tetHtml = renderToString(<AxoWorkspaceV62 scene={regTetScene} tieuDe="Tứ diện đều ABCD" />);
    expect(tetHtml).toContain("Tứ diện");

    // 3. Centroid G narration & tooltip + Prism badge 'Hình lăng trụ'
    const prismCentroidScene: Scene3D = {
      version: 1,
      free_objects: ["A", "B", "C", "A'", "B'", "C'"],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point", depends: [], xyz: ["6", "0", "0"] },
        { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point", depends: [], xyz: ["0", "6", "0"] },
        { id: "A'", type: "point3", label: "A'", notation: "A'", origin: "free", render: "point", depends: [], xyz: ["2", "2", "4"] },
        { id: "B'", type: "point3", label: "B'", notation: "B'", origin: "free", render: "point", depends: [], xyz: ["8", "2", "4"] },
        { id: "C'", type: "point3", label: "C'", notation: "C'", origin: "free", render: "point", depends: [], xyz: ["2", "8", "4"] },
        {
          id: "day",
          type: "polygon3",
          label: "Đáy ABC",
          notation: "ABC",
          origin: "derived",
          render: "polygon",
          surface_role: "BASE_REGION",
          formation_roles: ["CONSTRUCT_BASE"],
          depends: ["A", "B", "C"],
          polygon: [["0", "0", "0"], ["6", "0", "0"], ["0", "6", "0"]],
          closed: true,
        },
        {
          id: "day_tren",
          type: "polygon3",
          label: "Đáy trên A'B'C'",
          notation: "A'B'C'",
          origin: "derived",
          render: "polygon",
          surface_role: "TOP_BASE_REGION",
          formation_roles: ["CONSTRUCT_TRANSLATED_FACE"],
          depends: ["A'", "B'", "C'"],
          polygon: [["2", "2", "4"], ["8", "2", "4"], ["2", "8", "4"]],
          closed: true,
        },
        {
          id: "khoi_lang_tru",
          type: "solid",
          label: "Lăng trụ ABC.A'B'C'",
          notation: "ABC.A'B'C'",
          shape_class: "PRISM_LIKE",
          origin: "derived",
          render: "polyhedron",
          depends: ["A", "B", "C", "A'", "B'", "C'", "day", "day_tren"],
          faces: [["A", "B", "C"], ["A'", "B'", "C'"], ["A", "B", "B'", "A'"], ["B", "C", "C'", "B'"], ["C", "A", "A'", "C'"]],
        },
        {
          id: "G",
          type: "point3",
          label: "Trọng tâm G của tam giác ABC",
          notation: "G",
          origin: "derived",
          producer: "construct_point.centroid",
          render: "point",
          depends: ["A", "B", "C"],
          xyz: ["2", "2", "0"],
        },
      ],
      events: [
        { step_index: 0, action: "INIT", label: "Khởi tạo" },
        { step_index: 1, action: "CREATE", object: "day", display_label: "Đáy ABC" },
        { step_index: 2, action: "CREATE", object: "day_tren", display_label: "Đáy trên A'B'C'" },
        { step_index: 3, action: "CREATE", object: "khoi_lang_tru", display_label: "Lăng trụ ABC.A'B'C'" },
        { step_index: 4, action: "CREATE", object: "G", display_label: "Trọng tâm G" },
      ],
    } as unknown as Scene3D;
    const prismSteps = buildPedagogicalConstructionPlan(withSubEntities(prismCentroidScene)).steps;
    expect(prismSteps.some((s) => /Xác định trọng tâm G của (tam giác|Δ)\s*ABC/iu.test(s.title))).toBe(true);
    const gTooltip = buildVerifiedObjectTooltip(prismCentroidScene, "G", prismSteps[prismSteps.length - 1].anchor)!;
    expect(gTooltip.body).toMatch(/Trọng tâm.*ABC/iu);
    expect(renderToString(<AxoWorkspaceV62 scene={prismCentroidScene} tieuDe="Lăng trụ ABC.A'B'C'" />)).toContain(
      "Hình lăng trụ",
    );

    // 4. Regular hexagon classification in exact Q (using Gram metric for 60° equilateral lattice)
    const hexPts: ExactVec3[] = [
      ["1", "0", "0"],
      ["0", "1", "0"],
      ["-1", "1", "0"],
      ["-1", "0", "0"],
      ["0", "-1", "0"],
      ["1", "-1", "0"],
    ];
    const hexMetric: ExactScalar[][] = [
      ["4", "2", "0"],
      ["2", "4", "0"],
      ["0", "0", "4"],
    ];
    expect(classifyExactPolygonShape(hexPts, hexMetric)).toBe("lục giác đều");

    // 5. Auxiliary projection carrier plane hidden vs target studied plane visible + intersect_plane_plane terracotta & auxiliary-safe
    const interScene: Scene3D = {
      version: 1,
      free_objects: ["A", "B", "C", "D", "S"],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point", depends: [], xyz: ["4", "0", "0"] },
        { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point", depends: [], xyz: ["4", "4", "0"] },
        { id: "D", type: "point3", label: "D", notation: "D", origin: "free", render: "point", depends: [], xyz: ["0", "4", "0"] },
        { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point", depends: [], xyz: ["0", "0", "4"] },
        {
          id: "khoi",
          type: "solid",
          label: "Khối chóp S.ABCD",
          notation: "S.ABCD",
          origin: "derived",
          render: "polyhedron",
          depends: ["A", "B", "C", "D", "S"],
          vertex_ids: ["A", "B", "C", "D", "S"],
          vertices: [["0", "0", "0"], ["4", "0", "0"], ["4", "4", "0"], ["0", "4", "0"], ["0", "0", "4"]],
          faces: [[0, 1, 2, 3], [4, 0, 1], [4, 1, 2], [4, 2, 3], [4, 3, 0]],
        },
        {
          id: "derived_K_plane",
          type: "plane3",
          label: "(SBC)",
          notation: "(SBC)",
          origin: "derived",
          render: "plane",
          surface_role: "CUTTING_PLANE",
          depends: ["S", "B", "C"],
          point: ["4", "0", "0"],
          normal: ["1", "0", "1"],
        },
        {
          id: "K",
          type: "point3",
          label: "Hình chiếu K của A trên (SBC)",
          notation: "K",
          origin: "derived",
          producer: "construct_point.project_onto",
          render: "point",
          depends: ["A", "derived_K_plane"],
          xyz: ["2", "0", "2"],
        },
        {
          id: "mp_sac",
          type: "plane3",
          label: "(SAC)",
          notation: "(SAC)",
          origin: "derived",
          render: "plane",
          surface_role: "CUTTING_PLANE",
          display_group: ["target"],
          depends: ["S", "A", "C"],
          point: ["0", "0", "0"],
          normal: ["1", "-1", "0"],
        },
        {
          id: "mp_sbd",
          type: "plane3",
          label: "(SBD)",
          notation: "(SBD)",
          origin: "derived",
          render: "plane",
          surface_role: "CUTTING_PLANE",
          display_group: ["target"],
          depends: ["S", "B", "D"],
          point: ["4", "0", "0"],
          normal: ["1", "1", "1"],
        },
        {
          id: "gt_sac_sbd",
          type: "line3",
          label: "Giao tuyến của (SAC) và (SBD)",
          origin: "derived",
          producer: "intersect_plane_plane",
          render: "line",
          display_group: ["target"],
          depends: ["mp_sac", "mp_sbd"],
          point: ["0", "0", "4"],
          direction: ["2", "2", "-4"],
        },
      ],
      events: [
        { step_index: 0, action: "INIT", label: "Khởi tạo" },
        { step_index: 1, action: "CREATE", object: "khoi", display_label: "Khối chóp S.ABCD" },
        { step_index: 2, action: "CREATE", object: "derived_K_plane", display_label: "(SBC)" },
        { step_index: 3, action: "CREATE", object: "K", display_label: "K" },
        { step_index: 4, action: "CREATE", object: "mp_sac", display_label: "(SAC)" },
        { step_index: 5, action: "CREATE", object: "mp_sbd", display_label: "(SBD)" },
        { step_index: 6, action: "CREATE", object: "gt_sac_sbd", display_label: "Giao tuyến" },
      ],
    } as unknown as Scene3D;
    expect(
      resolvePlaneSectionVisibility(interScene, interScene.objects.find((o) => o.id === "derived_K_plane")!, 6),
    ).toMatchObject({
      subRole: "SOLID_FACE_DUPLICATE_PLANE",
      visible: false,
    });
    expect(
      resolvePlaneSectionVisibility(interScene, interScene.objects.find((o) => o.id === "mp_sac")!, 6),
    ).toMatchObject({
      subRole: "MANDATORY_STUDIED_PLANE",
      visible: true,
    });
    const gtLine = interScene.objects.find((o) => o.id === "gt_sac_sbd")!;
    expect(isIntersectionLineOrSegment(gtLine)).toBe(true);
    const gtSem = classifySceneObjectSemantics(interScene, gtLine, 6);
    expect(gtSem.role).toBe("RESULT_SECTION");
    expect(gtSem.strokeColor).toBe(0xc85a32);
    expect(auxiliaryHiddenAt(interScene, 6, false, null).has("gt_sac_sbd")).toBe(false);

    const interSteps = buildPedagogicalConstructionPlan(withSubEntities(interScene)).steps;
    const idxSac = interSteps.findIndex((s) => s.title.includes("(SAC)") && !s.title.includes("∩"));
    const idxSbd = interSteps.findIndex((s) => s.title.includes("(SBD)") && !s.title.includes("∩"));
    const idxGt = interSteps.findIndex((s) => s.title.includes("giao tuyến"));
    expect(idxSac).toBeGreaterThan(-1);
    expect(idxSbd).toBeGreaterThan(-1);
    expect(idxGt).toBeGreaterThan(idxSac);
    expect(idxGt).toBeGreaterThan(idxSbd);
  });

  it("Section V (Cases 1–5): exact mathematical verification & epistemic honesty independent of accidental coordinates", () => {
    const items = ((samplesData as unknown as { samples?: Array<{ id: string; envelope: { scene3d: Scene3D } }> }).samples ?? []);

    // Case 1: Midpoint section (M, N, P midpoints of SA, SB, SC => (MNP) || (ABCD) and Q is midpoint of SD)
    const midSample = JSON.parse(
      JSON.stringify(items.find((s) => s.id === "thiet-dien-chop")!.envelope.scene3d),
    ) as Scene3D;
    expect(verifySceneMathematicalConsistency(midSample).valid).toBe(true);
    const midSteps = pedagogicalStepList(midSample);
    const qTooltip = buildVerifiedObjectTooltip(midSample, "Q", midSteps[midSteps.length - 1].anchor)!;
    expect(qTooltip.body).toMatch(/trung điểm/iu);
    const midTampered: Scene3D = JSON.parse(JSON.stringify(midSample));
    const qTampered = midTampered.objects.find((o) => o.id === "Q")!;
    qTampered.xyz = ["0", "6", "-2"]; // Exterior point on line SD (t = 3/2 > 1) contradicting plane (MNP)
    expect(verifySceneMathematicalConsistency(midTampered).valid).toBe(false);

    // Case 2: Oblique pyramid WITHOUT SA ⊥ (ABCD) premise, even when S=[0,0,4] sits vertically above A=[0,0,0] in coordinates!
    const uncertifiedCoordScene = buildExteriorQPentagonScene();
    uncertifiedCoordScene.objects = uncertifiedCoordScene.objects.filter(
      (o) => !["chieu_cao_SA", "P", "Q", "line_sd"].includes(o.id),
    );
    uncertifiedCoordScene.events = uncertifiedCoordScene.events.filter(
      (e) => !["chieu_cao_SA", "P", "Q", "line_sd"].includes(e.object ?? ""),
    );
    uncertifiedCoordScene.objects.find((o) => o.id === "M")!.xyz = ["1", "1", "2"];
    const nMid = uncertifiedCoordScene.objects.find((o) => o.id === "N")!;
    nMid.depends = ["S", "D"];
    nMid.xyz = ["0", "1", "2"];
    const mpUncert = uncertifiedCoordScene.objects.find((o) => o.id === "mp_mnp")!;
    mpUncert.depends = ["A", "B", "M"];
    mpUncert.point = ["0", "0", "0"];
    mpUncert.normal = ["0", "2", "-1"];
    const secUncert = uncertifiedCoordScene.objects.find((o) => o.id === "thiet_dien")!;
    secUncert.polygon = [["0", "0", "0"], ["2", "0", "0"], ["1", "1", "2"], ["0", "1", "2"]];

    const uncertBasis = deriveExactPolygonMathBasis(uncertifiedCoordScene, secUncert)!;
    // Must downgrade 'hình thang vuông' -> 'hình thang' because right angle comes only from uncertified coordinates,
    // while keeping 'hình thang' (MN || CD || AB from midpoints + square base) as DERIVED!
    expect(uncertBasis.shape).toBe("hình thang");
    expect(uncertBasis.epistemicLevel).toBe("DERIVED");
    expect(uncertBasis.coordinateOnlyFacts.length).toBeGreaterThan(0);
    const uncertSteps = buildPedagogicalConstructionPlan(uncertifiedCoordScene).steps;
    expect(uncertSteps.some((s) => /SA\s*⊥|vuông góc đáy|hình thang vuông/iu.test(s.title + " " + s.subtitle))).toBe(false);

    // Case 3: Exterior intersection Q on extended carrier line SD (extended_ray vs clamped_segment)
    const extScene = buildExteriorQPentagonScene();
    const lineSd = extScene.objects.find((o) => o.id === "line_sd")!;
    expect(resolveLineDisplaySpan(extScene, lineSd)?.mode).toBe("extended_ray");

    // Case 4: Curved sections — sphere Pythagoras, cylinder circle, cone parallel circle similarity, and cylinder oblique ellipse
    const coneParScene: Scene3D = {
      version: 1,
      free_objects: ["O", "S", "A"],
      objects: [
        { id: "O", type: "point3", label: "O", notation: "O", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point", depends: [], xyz: ["0", "0", "4"] },
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["3", "0", "0"] },
        {
          id: "khoi_non",
          type: "curved_solid",
          curved_kind: "cone",
          label: "Hình nón S.O",
          origin: "derived",
          render: "cone",
          depends: ["O", "S", "A"],
          anchor: ["0", "0", "0"],
          apex_or_top: ["0", "0", "4"],
          radius_sq: "9",
        },
        {
          id: "mp_alpha",
          type: "plane3",
          label: "Mặt phẳng (α)",
          origin: "derived",
          render: "plane",
          surface_role: "CUTTING_PLANE",
          depends: [],
          point: ["0", "0", "2"],
          normal: ["0", "0", "1"],
        },
        {
          id: "td_non",
          type: "circle3",
          label: "Thiết diện tròn",
          origin: "derived",
          render: "circle",
          surface_role: "SECTION_REGION",
          depends: ["khoi_non", "mp_alpha"],
          center: ["0", "0", "2"],
          normal: ["0", "0", "1"],
          radius_sq: "9/4",
        },
      ],
      events: [
        { step_index: 0, action: "INIT", label: "Khởi tạo" },
        { step_index: 1, action: "CREATE", object: "khoi_non", display_label: "Hình nón" },
        { step_index: 2, action: "CREATE", object: "mp_alpha", display_label: "(α)" },
        { step_index: 3, action: "CREATE", object: "td_non", display_label: "Thiết diện tròn" },
      ],
    } as unknown as Scene3D;
    expect(verifySceneMathematicalConsistency(coneParScene).valid).toBe(true);
    const badConePar: Scene3D = JSON.parse(JSON.stringify(coneParScene));
    badConePar.objects.find((o) => o.id === "td_non")!.radius_sq = "4";
    expect(
      verifySceneMathematicalConsistency(badConePar)
        .contradictions.map((c) => c.title)
        .join(" "),
    ).toContain("Mâu thuẫn tỉ số đồng dạng khi cắt hình nón song song đáy");

    const cylEllipseScene: Scene3D = {
      version: 1,
      free_objects: ["O", "O'"],
      objects: [
        { id: "O", type: "point3", label: "O", notation: "O", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "O'", type: "point3", label: "O'", notation: "O'", origin: "free", render: "point", depends: [], xyz: ["0", "0", "20"] },
        {
          id: "khoi_tru",
          type: "curved_solid",
          curved_kind: "cylinder",
          label: "Hình trụ O.O'",
          origin: "derived",
          render: "cylinder",
          depends: ["O", "O'"],
          anchor: ["0", "0", "0"],
          apex_or_top: ["0", "0", "20"],
          radius_sq: "9",
        },
        {
          id: "mp_xien",
          type: "plane3",
          label: "Mặt phẳng (α)",
          origin: "derived",
          render: "plane",
          surface_role: "CUTTING_PLANE",
          depends: [],
          point: ["0", "0", "10"],
          normal: ["1", "0", "-1"],
        },
        {
          id: "td_elip",
          type: "ellipse3",
          label: "Thiết diện elip",
          origin: "derived",
          render: "ellipse",
          surface_role: "SECTION_REGION",
          depends: ["khoi_tru", "mp_xien"],
          center: ["0", "0", "10"],
          normal: ["1", "0", "-1"],
          major_dir: ["1", "0", "1"],
          minor_dir: ["0", "1", "0"],
          semi_minor_sq: "9",
          semi_major_sq: "18",
        },
      ],
      events: [
        { step_index: 0, action: "INIT", label: "Khởi tạo" },
        { step_index: 1, action: "CREATE", object: "khoi_tru", display_label: "Hình trụ" },
        { step_index: 2, action: "CREATE", object: "mp_xien", display_label: "(α)" },
        { step_index: 3, action: "CREATE", object: "td_elip", display_label: "Thiết diện elip" },
      ],
    } as unknown as Scene3D;
    expect(verifySceneMathematicalConsistency(cylEllipseScene).valid).toBe(true);
    const cylElSteps = buildPedagogicalConstructionPlan(withSubEntities(cylEllipseScene)).steps;
    expect(
      cylElSteps.some(
        (s) =>
          s.subtitle.includes("đường elip khép kín")
          && !s.subtitle.includes("3√2")
          && !s.subtitle.includes("b = R"),
      ),
    ).toBe(true);
    const badCylEllipse: Scene3D = JSON.parse(JSON.stringify(cylEllipseScene));
    badCylEllipse.objects.find((o) => o.id === "td_elip")!.semi_minor_sq = "4";
    expect(
      verifySceneMathematicalConsistency(badCylEllipse)
        .contradictions.map((c) => c.title)
        .join(" "),
    ).toContain("Mâu thuẫn bán trục nhỏ elip khi cắt xiên hình trụ đứng");

    // Case 5: Oblique Cylinder vs Right Cylinder — distinguish center-connecting line OO', lateral generator AB, and perpendicular altitude O'H
    const obliqueCylScene: Scene3D = {
      version: 1,
      free_objects: ["O", "O'", "A", "B", "H"],
      objects: [
        { id: "O", type: "point3", label: "O", notation: "O", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "O'", type: "point3", label: "O'", notation: "O'", origin: "free", render: "point", depends: [], xyz: ["2", "0", "4"] },
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["3", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point", depends: [], xyz: ["5", "0", "4"] },
        { id: "H", type: "point3", label: "H", notation: "H", origin: "free", render: "point", depends: [], xyz: ["2", "0", "0"] },
        {
          id: "day_duoi",
          type: "circle3",
          label: "Đường tròn đáy tâm O",
          origin: "derived",
          render: "circle",
          surface_role: "BASE_REGION",
          depends: ["O", "A"],
          center: ["0", "0", "0"],
          normal: ["0", "0", "1"],
          radius_sq: "9",
        },
        {
          id: "day_tren",
          type: "circle3",
          label: "Đường tròn đáy tâm O'",
          origin: "derived",
          render: "circle",
          surface_role: "TOP_BASE_REGION",
          depends: ["O'", "B"],
          center: ["2", "0", "4"],
          normal: ["0", "0", "1"],
          radius_sq: "9",
        },
        {
          id: "noi_tam",
          type: "segment3",
          label: "Đường nối tâm OO'",
          origin: "derived",
          render: "segment",
          depends: ["O", "O'"],
          endpoints: [["0", "0", "0"], ["2", "0", "4"]],
        },
        {
          id: "duong_sinh_ab",
          type: "segment3",
          label: "Đường sinh AB",
          origin: "derived",
          render: "segment",
          depends: ["A", "B"],
          endpoints: [["3", "0", "0"], ["5", "0", "4"]],
        },
        {
          id: "chieu_cao_o_h",
          type: "segment3",
          label: "Đường cao O'H",
          origin: "derived",
          render: "segment",
          formation_roles: ["CONSTRUCT_HEIGHT"],
          depends: ["O'", "H"],
          endpoints: [["2", "0", "4"], ["2", "0", "0"]],
          perpendicular_witness: {
            foot: ["2", "0", "0"],
            plane_directions: [["1", "0", "0"], ["0", "1", "0"]],
          },
        },
        {
          id: "khoi_tru_xien",
          type: "curved_solid",
          curved_kind: "cylinder",
          label: "Hình trụ xiên O.O'",
          origin: "derived",
          render: "cylinder",
          depends: ["O", "O'", "A"],
          anchor: ["0", "0", "0"],
          apex_or_top: ["2", "0", "4"],
          radius_sq: "9",
        },
        {
          id: "td_qua_truc",
          type: "polygon3",
          label: "Thiết diện OABB'O'",
          origin: "derived",
          render: "polygon",
          surface_role: "SECTION_REGION",
          depends: ["O", "A", "B", "O'"],
          polygon: [["0", "0", "0"], ["3", "0", "0"], ["5", "0", "4"], ["2", "0", "4"]],
          closed: true,
        },
      ],
      events: [
        { step_index: 0, action: "INIT", label: "Khởi tạo" },
        { step_index: 1, action: "CREATE", object: "day_duoi", display_label: "Đáy dưới" },
        { step_index: 2, action: "CREATE", object: "day_tren", display_label: "Đáy trên" },
        { step_index: 3, action: "CREATE", object: "noi_tam", display_label: "OO'" },
        { step_index: 4, action: "CREATE", object: "chieu_cao_o_h", display_label: "O'H" },
        { step_index: 5, action: "CREATE", object: "khoi_tru_xien", display_label: "Hình trụ xiên" },
        { step_index: 6, action: "CREATE", object: "duong_sinh_ab", display_label: "Đường sinh AB" },
        { step_index: 7, action: "CREATE", object: "td_qua_truc", display_label: "Thiết diện" },
      ],
    } as unknown as Scene3D;
    expect(verifySceneMathematicalConsistency(obliqueCylScene).valid).toBe(true);
    expect(classifyCurvedSegmentRole(obliqueCylScene, obliqueCylScene.objects.find((o) => o.id === "noi_tam")!)?.kind).toBe(
      "center_line",
    );
    expect(
      classifyCurvedSegmentRole(obliqueCylScene, obliqueCylScene.objects.find((o) => o.id === "duong_sinh_ab")!)?.kind,
    ).toBe("generator");
    expect(
      classifyCurvedSegmentRole(obliqueCylScene, obliqueCylScene.objects.find((o) => o.id === "chieu_cao_o_h")!)?.kind,
    ).toBe("altitude");
    expect(deriveExactPolygonMathBasis(obliqueCylScene, obliqueCylScene.objects.find((o) => o.id === "td_qua_truc")!)?.shape).toBe(
      "hình bình hành",
    );
    const obSteps = buildPedagogicalConstructionPlan(withSubEntities(obliqueCylScene)).steps;
    expect(obSteps.some((s) => /đường nối.*OO['′]/iu.test(s.title))).toBe(true);
    expect(obSteps.some((s) => s.title.includes("hình chữ nhật"))).toBe(false);

    const badObliqueCyl: Scene3D = JSON.parse(JSON.stringify(obliqueCylScene));
    badObliqueCyl.objects.find((o) => o.id === "noi_tam")!.formation_roles = ["CONSTRUCT_HEIGHT"];
    expect(
      verifySceneMathematicalConsistency(badObliqueCyl)
        .contradictions.map((c) => c.title)
        .join(" "),
    ).toContain("Mâu thuẫn tính chất hình trụ xiên");
  });

  describe("Visual Scaffolding & Construction Semantic Reliability (Parts II–VII)", () => {
    it("bounds multi-plane studied patches (e.g. (SAC) & (SBD)), exposes verified common point O = AC ∩ BD, and bounds intersection line display span without mutating plane equations", () => {
      const intersectionScene: Scene3D = {
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "2", "0"] },
          { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
          { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "3"] },
          {
            id: "day_ABCD",
            type: "polygon3",
            label: "Đáy ABCD",
            notation: "ABCD",
            origin: "derived",
            producer: null,
            render: "polygon",
            depends: ["A", "B", "C", "D"],
            vertices: [["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]],
            vertex_ids: ["A", "B", "C", "D"],
            formation_roles: ["CONSTRUCT_BASE"],
          },
          {
            id: "khoi_S_ABCD",
            type: "solid",
            label: "Hình chóp S.ABCD",
            notation: "S.ABCD",
            origin: "derived",
            producer: null,
            render: "mesh",
            depends: ["A", "B", "C", "D", "S"],
            vertices: [["0", "0", "3"], ["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]],
            vertex_ids: ["S", "A", "B", "C", "D"],
            faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]],
            formation_roles: ["CLOSE_SOLID"],
          },
          {
            id: "mp_sac",
            type: "plane3",
            label: "(SAC)",
            notation: "(SAC)",
            origin: "derived",
            producer: null,
            render: "surface",
            depends: ["A", "C", "S"],
            point: ["0", "0", "3"],
            normal: ["1", "-1", "0"],
            formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
          },
          {
            id: "mp_sbd",
            type: "plane3",
            label: "(SBD)",
            notation: "(SBD)",
            origin: "derived",
            producer: null,
            render: "surface",
            depends: ["B", "D", "S"],
            point: ["0", "0", "3"],
            normal: ["3", "3", "2"],
            formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
          },
          {
            id: "gt_so",
            type: "line3",
            label: "Giao tuyến của (SAC) và (SBD)",
            notation: null,
            role: "Đường thẳng",
            origin: "derived",
            producer: null,
            render: "line",
            depends: ["mp_sac", "mp_sbd"],
            source: { instruction: "intersect_plane_plane" },
            point: ["0", "0", "3"],
            direction: ["-1", "-1", "3"],
            formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
          },
        ],
        events: [
          { step_index: 0, action: "INIT", label: "Khởi tạo" },
          { step_index: 1, action: "CREATE", object: "day_ABCD" },
          { step_index: 2, action: "CREATE", object: "khoi_S_ABCD" },
          { step_index: 3, action: "CREATE", object: "mp_sac" },
          { step_index: 4, action: "CREATE", object: "mp_sbd" },
          { step_index: 5, action: "CREATE", object: "gt_so" },
        ],
        free_objects: ["A", "B", "C", "D", "S"],
      } as unknown as Scene3D;

      const plan = buildPedagogicalConstructionPlan(withSubEntities(intersectionScene));
      const plannedScene = plan.scene;
      const finalAnchor = plan.steps[plan.steps.length - 1].anchor;
      const visObjs = objectsAt(plannedScene, finalAnchor);

      // 1. Original plane equations are strictly unmutated
      const sac = plannedScene.objects.find((o) => o.id === "mp_sac")!;
      const sbd = plannedScene.objects.find((o) => o.id === "mp_sbd")!;
      expect(sac.point).toEqual(["0", "0", "3"]);
      expect(sac.normal).toEqual(["1", "-1", "0"]);
      expect(sbd.point).toEqual(["0", "0", "3"]);
      expect(sbd.normal).toEqual(["3", "3", "2"]);

      // 2. Option 3: Adaptive Bounded 4-gon Plane Patch — extends visibly past △SAC / △SBD without turning into a giant banner
      const sacPoly = computeBoundedStudiedPlanePolygon(plannedScene, sac, visObjs);
      const sbdPoly = computeBoundedStudiedPlanePolygon(plannedScene, sbd, visObjs);
      expect(sacPoly.length).toBe(4);
      expect(sbdPoly.length).toBe(4);
      for (const poly of [sacPoly, sbdPoly]) {
        for (const p of poly) {
          expect(p[2]).toBeGreaterThanOrEqual(-1e-5);
          expect(p[2]).toBeLessThanOrEqual(3.68);
          expect(p[0]).toBeGreaterThanOrEqual(-0.72);
          expect(p[0]).toBeLessThanOrEqual(2.72);
          expect(p[1]).toBeGreaterThanOrEqual(-0.72);
          expect(p[1]).toBeLessThanOrEqual(2.72);
        }
        // Must have a genuine upper top edge above or spanning S(z=3) so it is a 4-gon sheet, NOT a 3-gon triangle peaking at a single point S
        const aboveShoulder = poly.filter((p) => p[2] > 2.65);
        expect(aboveShoulder.length).toBeGreaterThanOrEqual(2);
      }
      // Dual violet distinction + continuous border on coexisting studied planes
      const sacStyle = resolveStudiedPlaneVisualStyle(plannedScene, sac, visObjs);
      const sbdStyle = resolveStudiedPlaneVisualStyle(plannedScene, sbd, visObjs);
      expect(sacStyle.coexistingCount).toBe(2);
      expect(sbdStyle.coexistingCount).toBe(2);
      expect(sacStyle.continuousPlaneBorder).toBe(true);
      expect(sbdStyle.continuousPlaneBorder).toBe(true);
      expect(sacStyle.strokeColor).not.toBe(sbdStyle.strokeColor);

      // 3. Multi-plane opacity scale is attenuated (< 1) when >= 2 studied planes coexist unselected
      const sacVis = resolvePlaneSectionVisibility(plannedScene, sac, finalAnchor, false, null);
      const sbdVis = resolvePlaneSectionVisibility(plannedScene, sbd, finalAnchor, false, null);
      expect(sacVis.visible).toBe(true);
      expect(sbdVis.visible).toBe(true);
      expect(sacVis.opacityScale).toBeLessThan(0.85);
      expect(sbdVis.opacityScale).toBeLessThan(0.85);

      // 4. Verified common point O = (1, 1, 0) on Q^3 exists as AUXILIARY/DERIVED (never GIVEN), and narration names S & O
      const ptO = plannedScene.objects.find(
        (o) => o.type === "point3" && o.xyz?.join("|") === "1|1|0",
      );
      expect(ptO).toBeDefined();
      expect(ptO!.origin).toBe("derived");
      expect(ptO!.authoritative).toBe(false);
      expect(ptO!.display_group ?? []).not.toContain("given");
      expect((ptO!.depends ?? []).length).toBeGreaterThanOrEqual(2);
      expect(ptO!.source).toBeDefined();

      const lastStep = plan.steps[plan.steps.length - 1];
      expect(lastStep.title).toMatch(/SO|\(SAC\).*\(SBD\)/u);
      expect(lastStep.premise).toMatch(/S.*O|điểm chung/u);

      // 5. Intersection line display span pierces S(0,0,3) and O(1,1,0) cleanly without shooting far below z = 0
      const gt = plannedScene.objects.find((o) => o.id === "gt_so")!;
      const span = resolveLineDisplaySpan(plannedScene, gt, visObjs);
      expect(span.endpoints).not.toBeNull();
      const [e0, e1] = span.endpoints!;
      expect(Math.min(e0[2], e1[2])).toBeGreaterThanOrEqual(-0.35);
      expect(Math.max(e0[2], e1[2])).toBeLessThanOrEqual(3.65);

      // 6. Toggling auxiliary off NEVER hides target intersection line gt_so
      const hiddenAux = auxiliaryHiddenAt(plannedScene, finalAnchor, false, null);
      expect(hiddenAux.has("gt_so")).toBe(false);
    });

    it("scaffolds sphere-plane R² = d² + r² with verified DERIVED/AUXILIARY H, IH, r, R across arbitrary radii (and irrational r fallback) without fabricating GIVEN facts", () => {
      // 1. Catalog sample cau-cat-mat-phang (R=5, d=3 => r=4)
      const catSample = (samplesData.samples as any[]).find((s) => s.id === "cau-cat-mat-phang")!;
      const catPlan = buildPedagogicalConstructionPlan(
        withSubEntities(veKhongGian(catSample.envelope.scene3d)),
      );
      expect(catPlan.steps.length).toBe(5);
      const catFinalObjs = objectsAt(catPlan.scene, catPlan.steps[4].anchor);
      const catStep1Objs = objectsAt(catPlan.scene, catPlan.steps[0].anchor);

      // Step 1 must NOT leak H or IH
      expect(catStep1Objs.some((o) => o.id.includes("__center") || o.id.includes("__dist"))).toBe(false);

      // Final step (Step 3) exposes H, perpendicular IH (with certified witness), and radial legs r, R
      const hObj = catFinalObjs.find((o) => o.id === "C__center");
      const ihObj = catFinalObjs.find((o) => o.id === "C__dist");
      const hmObj = catFinalObjs.find((o) => o.id === "C__sec_rad");
      const imObj = catFinalObjs.find((o) => o.id === "C__sph_rad");
      expect(hObj).toBeDefined();
      expect(ihObj).toBeDefined();
      expect(hmObj).toBeDefined();
      expect(imObj).toBeDefined();
      expect(ihObj!.perpendicular_witness?.can_present_as_proven).toBe(true);

      for (const aux of [hObj!, ihObj!, hmObj!, imObj!]) {
        expect(aux.origin).toBe("derived");
        expect(aux.authoritative).toBe(false);
        expect(aux.display_group ?? []).not.toContain("given");
        expect(aux.depends.length).toBeGreaterThanOrEqual(2);
        expect(aux.source).toBeDefined();
      }
      // Target circle C and step-explanatory H, IH, r, R are visible at the sphere-cut step anchor (even with trailing quantity readouts)
      const hiddenAtStep3 = auxiliaryHiddenAt(catPlan.scene, catPlan.steps[4].anchor, false, null);
      expect(hiddenAtStep3.has("C")).toBe(false);
      expect(hiddenAtStep3.has("C__center")).toBe(false);
      expect(hiddenAtStep3.has("C__dist")).toBe(false);
      expect(hiddenAtStep3.has("C__sec_rad")).toBe(false);
      expect(hiddenAtStep3.has("C__sph_rad")).toBe(false);

      // 2. Novel non-hardcoded rational sphere cut: I=(1,2,-1), R=10, plane z=5 => d=6, r=8
      const customSphereCut: Scene3D = {
        objects: [
          { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "2", "-1"] },
          { id: "S_ball", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: null, render: "curved_solid", depends: ["I"], anchor: ["1", "2", "-1"], radius_sq: "100" },
          { id: "Q_mp", type: "plane3", label: "Mặt phẳng (Q)", notation: "(Q)", origin: "derived", producer: null, render: "surface", depends: [], point: ["0", "0", "5"], normal: ["0", "0", "1"] },
          { id: "sec_c", type: "circle3", label: "Thiết diện tròn", origin: "derived", producer: null, render: "circle", surface_role: "SECTION_REGION", depends: ["S_ball", "Q_mp"], center: ["1", "2", "5"], normal: ["0", "0", "1"], radius_sq: "64" },
        ],
        events: [
          { step_index: 0, action: "INIT" },
          { step_index: 1, action: "CREATE", object: "S_ball" },
          { step_index: 2, action: "CREATE", object: "Q_mp" },
          { step_index: 3, action: "CREATE", object: "sec_c" },
        ],
        free_objects: ["I"],
      } as unknown as Scene3D;
      const customPlan = buildPedagogicalConstructionPlan(withSubEntities(customSphereCut));
      expect(verifySceneMathematicalConsistency(customPlan.scene).valid).toBe(true);
      expect(customPlan.steps[customPlan.steps.length - 1].premise).toMatch(/hình\s+chiếu\s+vuông\s+góc/iu);
      expect(customPlan.steps[customPlan.steps.length - 1].premise).not.toContain("R² = d² + r²");
      expect(customPlan.steps[customPlan.steps.length - 1].premise).not.toContain("10² = 6² + 8²");
      expect(customPlan.scene.objects.find((o) => o.id === "sec_c__center")?.xyz).toEqual(["1", "2", "5"]);
      expect(customPlan.scene.objects.find((o) => o.id === "sec_c__sec_rad")).toBeDefined();
      expect(customPlan.scene.objects.find((o) => o.id === "sec_c__sph_rad")).toBeDefined();

      // 3. Irrational section radius: I=(0,0,0), R=5, plane z=2 => d=2, r²=21 (no Q^3 rim point forged; reference group draws r & R!)
      const irratSphereCut: Scene3D = {
        objects: [
          { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "S_ball", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: null, render: "curved_solid", depends: ["I"], anchor: ["0", "0", "0"], radius_sq: "25" },
          { id: "Q_mp", type: "plane3", label: "Mặt phẳng (Q)", notation: "(Q)", origin: "derived", producer: null, render: "surface", depends: [], point: ["0", "0", "2"], normal: ["0", "0", "1"] },
          { id: "sec_ir", type: "circle3", label: "Thiết diện tròn", origin: "derived", producer: null, render: "circle", surface_role: "SECTION_REGION", depends: ["S_ball", "Q_mp"], center: ["0", "0", "2"], normal: ["0", "0", "1"], radius_sq: "21" },
        ],
        events: [
          { step_index: 0, action: "INIT" },
          { step_index: 1, action: "CREATE", object: "S_ball" },
          { step_index: 2, action: "CREATE", object: "Q_mp" },
          { step_index: 3, action: "CREATE", object: "sec_ir" },
        ],
        free_objects: ["I"],
      } as unknown as Scene3D;
      const irPlan = buildPedagogicalConstructionPlan(withSubEntities(irratSphereCut));
      expect(verifySceneMathematicalConsistency(irPlan.scene).valid).toBe(true);
      expect(irPlan.scene.objects.find((o) => o.id === "sec_ir__center")?.xyz).toEqual(["0", "0", "2"]);
      expect(irPlan.scene.objects.find((o) => o.id === "sec_ir__dist")).toBeDefined();
      expect(irPlan.scene.objects.find((o) => o.id === "sec_ir__sec_rad")).toBeUndefined();
      const irVis = objectsAt(irPlan.scene, irPlan.steps[irPlan.steps.length - 1].anchor);
      const refGroup = buildContractReferenceGroup(irPlan.scene, irVis, irPlan.steps[irPlan.steps.length - 1].anchor);
      const refNames = refGroup ? refGroup.children.map((c) => c.name) : [];
      expect(refNames.some((n) => n.startsWith("sphere_pythagoras_r:"))).toBe(false);
      expect(refNames.some((n) => n.startsWith("sphere_pythagoras_R:"))).toBe(false);
    });

    it("enforces Hybrid presentation boundary on expandPrimaryCurvedFoundation: zero GIVEN spoofing, authoritative=false, non-empty depends, and valid source", () => {
      for (const sampleId of ["tru-truc-xien", "tru-thiet-dien-tron", "non-duong-sinh", "non-thiet-dien-truc"]) {
        const sample = (samplesData.samples as any[]).find((s) => s.id === sampleId)!;
        const plan = buildPedagogicalConstructionPlan(
          withSubEntities(veKhongGian(sample.envelope.scene3d)),
        );
        const synth = plan.scene.objects.filter((o) =>
          o.id.includes("__axis") || o.id.includes("__radius") || o.id.includes("__base_"),
        );
        expect(synth.length).toBeGreaterThan(0);
        for (const obj of synth) {
          expect(obj.origin).toBe("derived");
          expect(obj.authoritative).toBe(false);
          expect(obj.display_group ?? []).not.toContain("given");
          expect(obj.depends.length).toBeGreaterThan(0);
          expect(obj.source).toBeDefined();
        }
      }
    });

    it("highlights exact carrier edge SC (and never unrelated edges) at midpoint P construction step, and groups/deduplicates Study Dock chips without future leakage or math mutation", () => {
      const pyrSample = (samplesData.samples as any[]).find((s) => s.id === "thiet-dien-chop")!;
      const rawPyr = withSubEntities(veKhongGian(pyrSample.envelope.scene3d));
      const plan = buildPedagogicalConstructionPlan(rawPyr);
      const sc = plan.scene;

      // 1. Midpoint P of SC step: highlights P as new and SC carrier edge as dep, never SA/SB/SD
      const stepP = plan.steps.find((s) => s.targetIds.includes("P"))!;
      expect(stepP).toBeDefined();
      const hlP = computeStepHighlightTargets(sc, stepP.anchor, stepP.startAnchor);
      expect(hlP.newIds.has("P")).toBe(true);
      const scEdge = sc.objects.find(
        (o) => o.id.includes("::edge:") && (o.depends ?? []).includes("S") && (o.depends ?? []).includes("C"),
      );
      expect(scEdge).toBeDefined();
      expect(hlP.depIds.has(scEdge!.id)).toBe(true);
      for (const otherOtherVertex of ["A", "B", "D"]) {
        const unrelatedEdge = sc.objects.find(
          (o) =>
            o.id.includes("::edge:")
            && (o.depends ?? []).includes("S")
            && (o.depends ?? []).includes(otherOtherVertex),
        );
        if (unrelatedEdge) expect(hlP.depIds.has(unrelatedEdge.id)).toBe(false);
      }

      // 2. Zero future-step leakage & zero duplicate/verbose/quantity chips across every step
      for (let i = 0; i < plan.steps.length; i += 1) {
        const st = plan.steps[i];
        const presentIds = new Set(objectsAt(sc, st.anchor).map((o) => o.id));
        const groups = buildStepEntityGroups(sc, st.anchor);
        expect(groups.primary.length).toBeGreaterThan(0);
        const seenIds = new Set<string>();
        const seenLabels = new Set<string>();
        for (const item of groups.all) {
          expect(presentIds.has(item.id)).toBe(true);
          expect(seenIds.has(item.id)).toBe(false);
          seenIds.add(item.id);
          expect(seenLabels.has(item.shortLabel)).toBe(false);
          seenLabels.add(item.shortLabel);
          expect(item.shortLabel).not.toMatch(/«|»/);
          expect(item.shortLabel.length).toBeLessThanOrEqual(22);
          const srcObj = sc.objects.find((o) => o.id === item.id)!;
          expect(srcObj.type).not.toBe("quantity");
          expect(srcObj.render).not.toBe("readout");
        }
      }

      // 3. Final step SSR renders 3-tier Study Dock structure & collapsible Group 3 button without mutating scene math
      const snapshotBefore = JSON.stringify(sc.objects);
      const finalAnchor = plan.steps[plan.steps.length - 1].anchor;
      const html = renderToString(
        <AxoWorkspaceV62
          scene={sc}
          de={pyrSample.envelope.description}
          tieuDe={pyrSample.title}
          initialStep={finalAnchor}
          initialSelectedId="Q"
        />,
      );
      expect(html).toContain('data-entity-tier="primary"');
      expect(html).toContain("dock-entity-more-btn");
      expect(JSON.stringify(sc.objects)).toBe(snapshotBefore);

      // 4. Tilted-axis right circular cylinder (`tru-truc-xien`): chip uses axis OO′ (not AO) and narration distinguishes tilted right circular cylinder from oblique cylinder
      const tiltedSample = (samplesData.samples as any[]).find((s) => s.id === "tru-truc-xien")!;
      const tiltedPlan = buildPedagogicalConstructionPlan(withSubEntities(veKhongGian(tiltedSample.envelope.scene3d)));
      const tiltedSc = tiltedPlan.scene;
      const tiltedSurfaceStep = tiltedPlan.steps.find((st) => /^Hoàn thiện mặt xung quanh/u.test(st.title))!;
      expect(tiltedSurfaceStep).toBeDefined();
      expect(tiltedSurfaceStep.subtitle).toMatch(/hình trụ tròn xoay đặt nghiêng trong không gian, không phải hình trụ xiên/iu);
      const tiltedGroups = buildStepEntityGroups(tiltedSc, tiltedPlan.steps[tiltedPlan.steps.length - 1].anchor);
      expect(tiltedGroups.primary.some((c) => /^Hình trụ OO[′']$/u.test(c.shortLabel))).toBe(true);
      expect(tiltedGroups.all.some((c) => c.shortLabel === "Hình trụ AO")).toBe(false);
    });
  });

  describe("Multi-Plane Visual Clarity & Goal-Complete Construction Reliability (§17 + BỔ SUNG §B)", () => {
    it("§17.2 & §17.3: generalizes 4-gon plane patches & core intersection segment to novel plane pairs (SAM) ∩ (SBD), and fails closed on parallel or coincident planes", () => {
      // Novel plane pair (SAM) and (SBD) where M=(1, 1/2, 0) is midpoint of BC
      const novelPlanesScene = {
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["3", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["3", "4", "0"] },
          { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["0", "4", "0"] },
          { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["0", "0", "5"] },
          { id: "day_ABCD", type: "polygon3", label: "Đáy ABCD", origin: "derived", producer: null, render: "polygon", depends: ["A", "B", "C", "D"], vertices: [["0", "0", "0"], ["3", "0", "0"], ["3", "4", "0"], ["0", "4", "0"]], vertex_ids: ["A", "B", "C", "D"], formation_roles: ["CONSTRUCT_BASE"] },
          { id: "khoi_S_ABCD", type: "solid", label: "Hình chóp S.ABCD", notation: "S.ABCD", origin: "derived", producer: null, render: "mesh", depends: ["A", "B", "C", "D", "S"], vertices: [["0", "0", "5"], ["0", "0", "0"], ["3", "0", "0"], ["3", "4", "0"], ["0", "4", "0"]], vertex_ids: ["S", "A", "B", "C", "D"], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]], formation_roles: ["CLOSE_SOLID"] },
          { id: "M", type: "point3", label: "M", notation: "M", origin: "derived", producer: null, render: "point_marker", depends: ["B", "C"], xyz: ["3", "2", "0"] },
          { id: "mp_sam", type: "plane3", label: "(SAM)", notation: "(SAM)", origin: "derived", producer: null, render: "surface", depends: ["S", "A", "M"], point: ["0", "0", "5"], normal: ["2", "-3", "0"] },
          { id: "mp_sbd", type: "plane3", label: "(SBD)", notation: "(SBD)", origin: "derived", producer: null, render: "surface", depends: ["S", "B", "D"], point: ["0", "0", "5"], normal: ["20", "15", "12"] },
          { id: "gt_si", type: "line3", label: "Giao tuyến của (SAM) và (SBD)", origin: "derived", producer: null, render: "line", depends: ["mp_sam", "mp_sbd"], source: { instruction: "intersect_plane_plane" }, point: ["0", "0", "5"], direction: ["2", "4/3", "-5"] },
        ],
        events: [
          { step_index: 0, action: "INIT" },
          { step_index: 1, action: "CREATE", object: "day_ABCD" },
          { step_index: 2, action: "CREATE", object: "khoi_S_ABCD" },
          { step_index: 3, action: "CREATE", object: "M" },
          { step_index: 4, action: "CREATE", object: "mp_sam" },
          { step_index: 5, action: "CREATE", object: "mp_sbd" },
          { step_index: 6, action: "CREATE", object: "gt_si" },
        ],
        free_objects: ["A", "B", "C", "D", "S"],
      } as unknown as Scene3D;

      const novelPlan = buildPedagogicalConstructionPlan(withSubEntities(novelPlanesScene));
      const novelSc = novelPlan.scene;
      const novelVis = objectsAt(novelSc, novelPlan.steps[novelPlan.steps.length - 1].anchor);
      const samPoly = computeBoundedStudiedPlanePolygon(novelSc, novelSc.objects.find((o) => o.id === "mp_sam")!, novelVis);
      const sbdPoly = computeBoundedStudiedPlanePolygon(novelSc, novelSc.objects.find((o) => o.id === "mp_sbd")!, novelVis);
      expect(samPoly.length).toBe(4);
      expect(sbdPoly.length).toBe(4);
      const gtSpan = resolveLineDisplaySpan(novelSc, novelSc.objects.find((o) => o.id === "gt_si")!, novelVis);
      expect(gtSpan.coreSegment).not.toBeNull();
      expect(novelPlan.goalCompletion.status).toBe("reached");
      expect(novelPlan.goalCompletion.items.some((g) => g.kind === "intersection_line")).toBe(true);

      // Parallel planes with forged unique intersection line -> must fail closed and refuse rendering
      const parallelPlanesScene = {
        objects: [
          { id: "mp_p1", type: "plane3", label: "(P)", notation: "(P)", origin: "derived", producer: null, render: "surface", depends: [], point: ["0", "0", "0"], normal: ["0", "0", "1"] },
          { id: "mp_p2", type: "plane3", label: "(Q)", notation: "(Q)", origin: "derived", producer: null, render: "surface", depends: [], point: ["0", "0", "2"], normal: ["0", "0", "3"] },
          { id: "forged_gt", type: "line3", label: "Giao tuyến giả", origin: "derived", producer: null, render: "line", depends: ["mp_p1", "mp_p2"], source: { instruction: "intersect_plane_plane" }, point: ["0", "0", "1"], direction: ["1", "0", "0"] },
        ],
        events: [
          { step_index: 0, action: "INIT" },
          { step_index: 1, action: "CREATE", object: "mp_p1" },
          { step_index: 2, action: "CREATE", object: "mp_p2" },
          { step_index: 3, action: "CREATE", object: "forged_gt" },
        ],
        free_objects: [],
      } as unknown as Scene3D;
      expect(verifySceneMathematicalConsistency(parallelPlanesScene).valid).toBe(false);
      const parSpan = resolveLineDisplaySpan(parallelPlanesScene, parallelPlanesScene.objects[2], parallelPlanesScene.objects);
      expect(parSpan.mode).toBe("no_intersection");
      expect(parSpan.endpoints).toBeNull();
      expect(buildObject3D(parallelPlanesScene.objects[2], false, undefined, [[0, 0, 0], [1, 0, 2]], undefined, undefined, undefined, false, "primary", false, true, false, parallelPlanesScene)).toBeNull();

      // Coincident planes with forged unique intersection line -> must fail closed and refuse rendering
      const coincidentPlanesScene = {
        objects: [
          { id: "mp_c1", type: "plane3", label: "(P)", notation: "(P)", origin: "derived", producer: null, render: "surface", depends: [], point: ["0", "0", "0"], normal: ["1", "-1", "0"] },
          { id: "mp_c2", type: "plane3", label: "(Q)", notation: "(Q)", origin: "derived", producer: null, render: "surface", depends: [], point: ["2", "2", "1"], normal: ["2", "-2", "0"] },
          { id: "forged_coin_gt", type: "line3", label: "Giao tuyến trùng", origin: "derived", producer: null, render: "line", depends: ["mp_c1", "mp_c2"], source: { instruction: "intersect_plane_plane" }, point: ["0", "0", "0"], direction: ["0", "0", "1"] },
        ],
        events: [
          { step_index: 0, action: "INIT" },
          { step_index: 1, action: "CREATE", object: "mp_c1" },
          { step_index: 2, action: "CREATE", object: "mp_c2" },
          { step_index: 3, action: "CREATE", object: "forged_coin_gt" },
        ],
        free_objects: [],
      } as unknown as Scene3D;
      expect(verifySceneMathematicalConsistency(coincidentPlanesScene).valid).toBe(false);
      expect(resolveLineDisplaySpan(coincidentPlanesScene, coincidentPlanesScene.objects[2], coincidentPlanesScene.objects).mode).toBe("no_intersection");
    });

    it("§17.4 & §17.5: completes skew-line distance goals (AB & SC -> √2, AD & SC -> 12/5 with chart_metric) with certified dual right-angle markers and refuses unverified witnesses", () => {
      // Case A: d(AB, SC) = √2 in square-base pyramid S.ABCD (a = 2, SA = 2)
      const skewAbSc = {
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["1", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["1", "1", "0"] },
          { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["0", "1", "0"] },
          { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["0", "0", "1"] },
          { id: "day_ABCD", type: "polygon3", label: "Đáy ABCD", origin: "derived", producer: null, render: "polygon", depends: ["A", "B", "C", "D"], display_group: ["construction", "face"], vertices: [["0", "0", "0"], ["1", "0", "0"], ["1", "1", "0"], ["0", "1", "0"]], vertex_ids: ["A", "B", "C", "D"], formation_roles: ["CONSTRUCT_BASE"] },
          { id: "khoi_S_ABCD", type: "solid", label: "Hình chóp S.ABCD", notation: "S.ABCD", origin: "derived", producer: null, render: "mesh", depends: ["A", "B", "C", "D", "S"], display_group: ["construction", "solid"], vertices: [["0", "0", "1"], ["0", "0", "0"], ["1", "0", "0"], ["1", "1", "0"], ["0", "1", "0"]], vertex_ids: ["S", "A", "B", "C", "D"], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]], formation_roles: ["CLOSE_SOLID"] },
          { id: "dt1_sk5", type: "line3", label: "Đường thẳng qua A và B", origin: "derived", producer: null, render: "line", depends: ["A", "B"], display_group: ["construction", "target"], point: ["0", "0", "0"], direction: ["1", "0", "0"] },
          { id: "dt2_sk5", type: "line3", label: "Đường thẳng qua S và C", origin: "derived", producer: null, render: "line", depends: ["S", "C"], display_group: ["construction", "target"], point: ["0", "0", "1"], direction: ["1", "1", "-1"] },
          {
            id: "kq_sk5",
            type: "quantity",
            label: "Khoảng cách giữa AB và SC",
            notation: "d(AB, SC)",
            origin: "derived",
            producer: "measure.distance",
            render: "readout",
            depends: ["dt1_sk5", "dt2_sk5"],
            display_group: ["construction", "measurement", "target"],
            value: "√2",
            exact: { kind: "radical", coefficient: "1", radicand: 2 },
            annotation: {
              kind: "distance",
              subject_ids: ["dt1_sk5", "dt2_sk5"],
              anchor: "witness",
              unit: null,
              category: "result",
              role: "result",
              witness: {
                from: "dt2_sk5",
                from_point: ["1/2", "1/2", "1/2"],
                foot: ["1/2", "0", "0"],
                on: "dt1_sk5",
                relation: "common_perpendicular",
                marker: { u: ["-1/2", "0", "0"], v: ["0", "1/2", "1/2"], u_to: "A" },
                second: {
                  foot: ["1/2", "1/2", "1/2"],
                  on: "dt2_sk5",
                  marker: { u: ["1/2", "1/2", "-1/2"], v: ["0", "-1/2", "-1/2"], u_to: "C" },
                },
              },
            },
          },
        ],
        chart_metric: [["4", "0", "0"], ["0", "4", "0"], ["0", "0", "4"]],
        events: [
          { step_index: 0, action: "INIT" },
          { step_index: 1, action: "CREATE", object: "day_ABCD" },
          { step_index: 2, action: "CREATE", object: "khoi_S_ABCD" },
          { step_index: 3, action: "CREATE", object: "dt1_sk5" },
          { step_index: 4, action: "CREATE", object: "dt2_sk5" },
          { step_index: 5, action: "MEASURE", object: "kq_sk5", depends: ["dt1_sk5", "dt2_sk5"], learner_text: "Tính khoảng cách giữa AB và SC: d(AB, SC) = √2." },
        ],
        free_objects: ["A", "B", "C", "D", "S"],
      } as unknown as Scene3D;

      const skewPlan = buildPedagogicalConstructionPlan(withSubEntities(skewAbSc));
      expect(verifySceneMathematicalConsistency(skewPlan.scene).valid).toBe(true);
      const perpSeg = skewPlan.scene.objects.find((o) => o.id === "kq_sk5__perp_seg");
      const foot1 = skewPlan.scene.objects.find((o) => o.id === "kq_sk5__foot1");
      const foot2 = skewPlan.scene.objects.find((o) => o.id === "kq_sk5__foot2");
      expect(perpSeg).toBeDefined();
      expect(foot1).toBeDefined();
      expect(foot2).toBeDefined();
      for (const synth of [perpSeg!, foot1!, foot2!]) {
        expect(synth.origin).toBe("derived");
        expect(synth.authoritative).toBe(false);
        expect(synth.display_group ?? []).not.toContain("given");
      }
      const skewFinalAnchor = skewPlan.steps[skewPlan.steps.length - 1].anchor;
      expect(skewPlan.steps[skewPlan.steps.length - 1].targetIds).toContain("kq_sk5__perp_seg");
      expect(skewPlan.steps[skewPlan.steps.length - 1].title).toMatch(/vuông góc chung|khoảng cách/iu);
      // Auxiliary toggle OFF must NOT hide goal witness!
      const skewHiddenAux = auxiliaryHiddenAt(skewPlan.scene, skewFinalAnchor, false, null);
      expect(skewHiddenAux.has("kq_sk5__perp_seg")).toBe(false);
      expect(skewHiddenAux.has("kq_sk5__foot1")).toBe(false);
      expect(skewHiddenAux.has("kq_sk5__foot2")).toBe(false);

      // Dual right-angle markers rendered in 3D after Cholesky world transform
      const worldSkew = registerExactSceneOrigin(veKhongGian(skewPlan.scene), skewPlan.scene);
      const worldSeg = worldSkew.objects.find((o) => o.id === "kq_sk5__perp_seg")!;
      const builtSeg = buildObject3D(worldSeg, "dich", undefined, [[0, 0, 0], [2, 2, 2]], undefined, undefined, undefined, false, "primary", false, true, false, worldSkew)!;
      const markerNames: string[] = [];
      builtSeg.traverse((n) => {
        if (n.name.startsWith("perp_marker")) markerNames.push(n.name);
      });
      expect(markerNames).toContain("perp_marker:kq_sk5__perp_seg");
      expect(markerNames).toContain("perp_marker_2:kq_sk5__perp_seg");
      expect(skewPlan.goalCompletion.status).toBe("reached");
      expect(skewPlan.goalCompletion.items[0]?.valueText).toContain("√2");

      // Case B: Uncertified / missing witness on skew-line quantity -> NEVER fabricates fake perpendicular segment
      const unverifiedSkew = {
        ...skewAbSc,
        objects: skewAbSc.objects.map((o) =>
          o.id === "kq_sk5"
            ? {
                ...o,
                annotation: {
                  ...o.annotation!,
                  witness: undefined,
                },
              }
            : o,
        ),
      } as unknown as Scene3D;
      const unverifiedPlan = buildPedagogicalConstructionPlan(withSubEntities(unverifiedSkew));
      expect(unverifiedPlan.scene.objects.find((o) => o.id === "kq_sk5__perp_seg")).toBeUndefined();
    });

    it("§17.6–§17.9: completes point-plane distance, missing length segments (MG/SK), target angle conclusion steps, #dock-goal-summary SSR, and enforces reverse-dependency guard", () => {
      // 1. Point-to-plane distance d(A, (SBC)) = 12/5 where (SBC) was collapsed as duplicate face plane
      const ptPlaneDist = {
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given", "target"], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["1", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["1", "1", "0"] },
          { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["0", "1", "0"] },
          { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["0", "0", "1"] },
          { id: "day_ABCD", type: "polygon3", label: "Đáy ABCD là hình vuông", origin: "derived", producer: null, render: "polygon", depends: ["A", "B", "C", "D"], vertices: [["0", "0", "0"], ["1", "0", "0"], ["1", "1", "0"], ["0", "1", "0"]], vertex_ids: ["A", "B", "C", "D"], formation_roles: ["CONSTRUCT_BASE"] },
          { id: "khoi_S_ABCD", type: "solid", label: "Hình chóp S.ABCD", notation: "S.ABCD", origin: "derived", producer: null, render: "mesh", depends: ["A", "B", "C", "D", "S"], vertices: [["0", "0", "1"], ["0", "0", "0"], ["1", "0", "0"], ["1", "1", "0"], ["0", "1", "0"]], vertex_ids: ["S", "A", "B", "C", "D"], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]], formation_roles: ["CLOSE_SOLID"] },
          { id: "mp_dp5", type: "plane3", label: "Mặt phẳng qua S, B, C", origin: "derived", producer: null, render: "surface", depends: ["S", "B", "C"], display_group: ["construction", "target"], point: ["0", "0", "1"], normal: ["1", "0", "1"] },
          {
            id: "kq_dp5",
            type: "quantity",
            label: "Khoảng cách giữa A và (SBC)",
            notation: "d(A, (SBC))",
            origin: "derived",
            producer: "measure.distance",
            render: "readout",
            depends: ["A", "mp_dp5"],
            display_group: ["construction", "measurement", "target"],
            value: "12/5",
            exact: { kind: "rational", value: "12/5" },
            annotation: {
              kind: "distance",
              subject_ids: ["A", "mp_dp5"],
              anchor: "witness",
              unit: null,
              category: "result",
              role: "result",
              witness: {
                from: "A",
                foot: ["16/25", "0", "9/25"],
                on: "mp_dp5",
                relation: "line_perp_plane",
                marker: { u: ["9/25", "0", "-9/25"], v: ["-16/25", "0", "-9/25"], u_to: "B" },
              },
            },
          },
        ],
        chart_metric: [["9", "0", "0"], ["0", "9", "0"], ["0", "0", "16"]],
        events: [
          { step_index: 0, action: "INIT", depends: [] },
          { step_index: 1, action: "CREATE", object: "day_ABCD", depends: ["A", "B", "C", "D"] },
          { step_index: 2, action: "CREATE", object: "khoi_S_ABCD", depends: ["A", "B", "C", "D", "S"] },
          { step_index: 3, action: "CREATE", object: "mp_dp5", depends: ["S", "B", "C"] },
          { step_index: 4, action: "MEASURE", object: "kq_dp5", depends: ["A", "mp_dp5"], learner_text: "Tính khoảng cách giữa A và (SBC): d(A, (SBC)) = 12/5." },
        ],
        free_objects: ["A", "B", "C", "D", "S"],
      } as unknown as Scene3D;

      const dpPlan = buildPedagogicalConstructionPlan(withSubEntities(ptPlaneDist));
      expect(dpPlan.scene.objects.find((o) => o.id === "kq_dp5__perp_seg")).toBeDefined();
      expect(dpPlan.steps[dpPlan.steps.length - 1].targetIds).toContain("kq_dp5__perp_seg");

      // 2. Missing target length segment MG = √7
      const mgScene = {
        objects: [
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["6", "0", "0"] },
          { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["0", "6", "0"] },
          { id: "D", type: "point3", label: "D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["0", "0", "4"] },
          { id: "G", type: "point3", label: "G", notation: "G", origin: "derived", producer: null, render: "point_marker", depends: ["A", "B", "C"], xyz: ["2", "2", "0"] },
          { id: "M", type: "point3", label: "M", notation: "M", origin: "derived", producer: null, render: "point_marker", depends: ["C", "D"], xyz: ["0", "3", "2"] },
          {
            id: "kq_mg",
            type: "quantity",
            label: "Độ dài đoạn MG",
            notation: "MG",
            origin: "derived",
            producer: "measure.length",
            render: "readout",
            depends: ["M", "G"],
            display_group: ["construction", "measurement", "target"],
            value: "3",
            exact: { kind: "rational", value: "3" },
            annotation: { kind: "length", subject_ids: ["M", "G"], anchor: "segment", unit: null, category: "result", role: "result" },
          },
        ],
        events: [
          { step_index: 0, action: "INIT" },
          { step_index: 1, action: "CREATE", object: "G" },
          { step_index: 2, action: "CREATE", object: "M" },
          { step_index: 3, action: "MEASURE", object: "kq_mg", depends: ["M", "G"], learner_text: "Tính độ dài đoạn MG: MG = 3." },
        ],
        free_objects: ["A", "B", "C", "D"],
      } as unknown as Scene3D;
      const mgPlan = buildPedagogicalConstructionPlan(mgScene);
      expect(mgPlan.scene.objects.find((o) => o.id === "kq_mg__target_seg")).toBeDefined();
      expect(mgPlan.steps[mgPlan.steps.length - 1].targetIds).toContain("kq_mg__target_seg");

      // 3. Target angle goal preserves a dedicated conclusion step without fabricating fake 3D objects
      const angleScene = {
        objects: [
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["4", "0", "0"] },
          { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["4", "4", "0"] },
          { id: "D", type: "point3", label: "D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["0", "4", "0"] },
          { id: "S", type: "point3", label: "S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], display_group: ["given"], xyz: ["0", "0", "4"] },
          { id: "day_ABCD", type: "polygon3", label: "Đáy ABCD", origin: "derived", producer: null, render: "polygon", depends: ["A", "B", "C", "D"], vertices: [["0", "0", "0"], ["4", "0", "0"], ["4", "4", "0"], ["0", "4", "0"]], vertex_ids: ["A", "B", "C", "D"], formation_roles: ["CONSTRUCT_BASE"] },
          { id: "khoi_S_ABCD", type: "solid", label: "Hình chóp S.ABCD", notation: "S.ABCD", origin: "derived", producer: null, render: "mesh", depends: ["A", "B", "C", "D", "S"], vertices: [["0", "0", "4"], ["0", "0", "0"], ["4", "0", "0"], ["4", "4", "0"], ["0", "4", "0"]], vertex_ids: ["S", "A", "B", "C", "D"], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]], formation_roles: ["CLOSE_SOLID"] },
          { id: "mp1_dh5", type: "plane3", label: "Mặt phẳng qua S, B, C", origin: "derived", producer: null, render: "surface", depends: ["S", "B", "C"], display_group: ["construction", "target"], point: ["0", "0", "4"], normal: ["1", "0", "1"] },
          { id: "mp2_dh5", type: "plane3", label: "(ABCD)", notation: "(ABCD)", origin: "derived", producer: null, render: "surface", depends: ["A", "B", "C"], display_group: ["construction", "target"], point: ["0", "0", "0"], normal: ["0", "0", "1"] },
          {
            id: "kq_dh5",
            type: "quantity",
            label: "Côsin bình phương của góc giữa (SBC) và (ABCD)",
            origin: "derived",
            producer: "measure.angle",
            render: "readout",
            depends: ["mp1_dh5", "mp2_dh5"],
            display_group: ["construction", "measurement", "target"],
            value: "1/2",
            exact: { kind: "rational", value: "1/2" },
          },
        ],
        events: [
          { step_index: 0, action: "INIT" },
          { step_index: 1, action: "CREATE", object: "day_ABCD" },
          { step_index: 2, action: "CREATE", object: "khoi_S_ABCD" },
          { step_index: 3, action: "CREATE", object: "mp1_dh5" },
          { step_index: 4, action: "CREATE", object: "mp2_dh5" },
          { step_index: 5, action: "MEASURE", object: "kq_dh5", depends: ["mp1_dh5", "mp2_dh5"], learner_text: "Tính côsin bình phương của góc giữa (SBC) và (ABCD): cos²((SBC), (ABCD)) = 1/2." },
        ],
        free_objects: ["A", "B", "C", "D", "S"],
      } as unknown as Scene3D;
      const anglePlan = buildPedagogicalConstructionPlan(withSubEntities(angleScene));
      expect(anglePlan.steps.some((st) => st.epistemicCategory === "conclusion")).toBe(false);
      expect(anglePlan.goalCompletion.status).toBe("reached");
      expect(anglePlan.goalCompletion.items[0]?.valueText).toContain("45°");

      // SSR of AxoWorkspaceV62 eliminates duplicate #dock-goal-summary when goalCompletion.status === "reached",
      // never leaks the numeric answer ("12/5") into construction steps (#dock-steps-ul) or Step 1,
      // presents verified "12/5" only in #dock-math-results once construction completes, and renders #dock-goal-summary only when incomplete/unverified
      const ssrHtml = renderToString(
        <AxoWorkspaceV62
          scene={dpPlan.scene}
          de="Cho hình chóp S.ABCD có đáy là hình vuông cạnh 3, SA = 4 vuông góc đáy. Tính khoảng cách từ A đến (SBC)."
          tieuDe="Khoảng cách từ A đến (SBC)"
        />,
      );
      expect(ssrHtml).not.toContain('id="dock-goal-summary"');
      expect(ssrHtml).toContain('data-goal-status="reached"');
      const stepsUlMatch = ssrHtml.match(/<ul[^>]*id="dock-steps-ul"[\s\S]*?<\/ul>/u);
      expect(stepsUlMatch?.[0] ?? "").not.toContain("12/5");
      expect(ssrHtml).not.toContain('id="dock-math-results"');
      expect(ssrHtml).not.toContain('id="dock-goal-reveal"');
      expect(ssrHtml).not.toContain('id="dock-goal-conclusion"');
      expect(ssrHtml).not.toContain("12/5");
      expect(dpPlan.goalCompletion.items.map((it) => it.valueText)).toContain("12/5");
      expect(ssrHtml).not.toContain("Đang ẩn đáp án");
      expect(ssrHtml).not.toMatch(/Thực hành có hướng dẫn|Kiểm tra nhanh|Chấm điểm/iu);

      const ssrStep1Html = renderToString(
        <AxoWorkspaceV62
          scene={dpPlan.scene}
          initialStep={dpPlan.steps[0].anchor}
          de="Cho hình chóp S.ABCD có đáy là hình vuông cạnh 3, SA = 4 vuông góc đáy. Tính khoảng cách từ A đến (SBC)."
          tieuDe="Khoảng cách từ A đến (SBC)"
        />,
      );
      expect(ssrStep1Html).not.toContain('id="dock-goal-summary"');
      expect(ssrStep1Html).toContain("Dựng đáy ABCD là hình vuông");
      // Active Step 1 banner must not leak the final numeric distance 12/5
      const step1BannerMatch = ssrStep1Html.match(/class="dock-active-banner"[\s\S]*?<\/div>\s*<div class="dock-steps-header"/u);
      expect(step1BannerMatch?.[0] ?? "").not.toContain("12/5");

      // Split conclusion step navigation (`vuong-goc-chop`) must not snap Step N-1 forward to Step N
      const sampleList = (samplesData as unknown as { samples: { id: string; envelope: { scene3d: Scene3D } }[] }).samples;
      const vuongGocSample = sampleList.find((s) => s.id === "vuong-goc-chop")!;
      const vgPlan = buildPedagogicalConstructionPlan(withSubEntities(veKhongGian(vuongGocSample.envelope.scene3d)));
      expect(vgPlan.steps.length).toBeGreaterThanOrEqual(5);
      const vgPenultimate = vgPlan.steps[vgPlan.steps.length - 2];
      const vgPenultimateHtml = renderToString(
        <AxoWorkspaceV62
          scene={vuongGocSample.envelope.scene3d}
          initialStep={vgPenultimate.anchor}
          tieuDe="Góc vuông chóp"
        />,
      );
      expect(vgPenultimateHtml).toContain(`Bước ${vgPlan.steps.length - 1}/${vgPlan.steps.length}`);

      // Section goal completion (`thiet-dien-chop`) resolves to the final closed section step (Step 10/10), not Step 9/10
      const thietDienSample = sampleList.find((s) => s.id === "thiet-dien-chop")!;
      const tdPlan = buildPedagogicalConstructionPlan(withSubEntities(veKhongGian(thietDienSample.envelope.scene3d)));
      expect(tdPlan.goalCompletion.reachedAtStepIndex).toBe(tdPlan.steps.length - 1);
      expect(tdPlan.goalCompletion.headline).toContain("hoàn thiện thiết diện");

      // 4. Reverse-dependency guard (§17.9): authoritative object depending on authoritative=false helper is rejected
      const reverseDepScene = {
        objects: [
          { id: "aux_h", type: "point3", label: "H", notation: "H", origin: "derived", authoritative: false, producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "auth_p", type: "point3", label: "P", notation: "P", origin: "derived", producer: null, render: "point_marker", depends: ["aux_h"], xyz: ["1", "0", "0"] },
        ],
        events: [
          { step_index: 0, action: "INIT" },
          { step_index: 1, action: "CREATE", object: "aux_h" },
          { step_index: 2, action: "CREATE", object: "auth_p" },
        ],
        free_objects: [],
      } as unknown as Scene3D;
      const revCheck = verifySceneMathematicalConsistency(reverseDepScene);
      expect(revCheck.valid).toBe(false);
    });
  });

  describe("Step Provenance, Mathematical Witness Audit & Cross-Family Generalization (PHẦN II–VI)", () => {
    it("PHẦN II §3: certifies exact AB–SC skew-line common perpendicular (H=[1/2,0,0], K=[1/2,1/2,1/2] in G=diag(4,4,4), d=√2), rejects forged witness coordinates or mismatched distance norm fail-closed, and extends diemChoDuong to w.second.foot", () => {
      // Square pyramid S.ABCD, side a = 2, SA = 2, SA ⊥ (ABCD), chart_metric G = diag(4, 4, 4)
      // In chart coordinates: A=[0,0,0], B=[1,0,0], C=[1,1,0], D=[0,1,0], S=[0,0,1].
      // Common perpendicular between AB (y=0, z=0) and SC (P(t) = [t, t, 1-t]):
      //   H(s) = [s, 0, 0], K(t) = [t, t, 1-t], HK = [t-s, t, 1-t].
      //   HK ⊥ AB=[1,0,0]_G => t - s = 0 => s = t.
      //   HK ⊥ SC=[1,1,-1]_G => 0 + 4t - 4(1-t) = 0 => 8t = 4 => t = 1/2, s = 1/2.
      //   Unique feet: H = [1/2, 0, 0] (Euclidean [1, 0, 0] midpoint of AB), K = [1/2, 1/2, 1/2] (Euclidean [1, 1, 1] midpoint of SC).
      //   ||HK||_G^2 = 4*(0^2 + (1/2)^2 + (1/2)^2) = 2 => d(AB, SC) = √2.
      const makeAbScSkewScene = (): Scene3D => ({
        version: 1,
        chart_metric: [
          ["4", "0", "0"],
          ["0", "4", "0"],
          ["0", "0", "4"],
        ],
        free_objects: ["A", "B", "C", "D", "S"],
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", render: "point", depends: [], xyz: ["1", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", render: "point", depends: [], xyz: ["1", "1", "0"] },
          { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", render: "point", depends: [], xyz: ["0", "1", "0"] },
          { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", render: "point", depends: [], xyz: ["0", "0", "1"] },
          {
            id: "day_ABCD",
            type: "polygon3",
            label: "Đáy ABCD",
            notation: "ABCD",
            origin: "derived",
            render: "polygon",
            surface_role: "BASE_REGION",
            formation_roles: ["CONSTRUCT_BASE"],
            depends: ["A", "B", "C", "D"],
            vertices: [["0", "0", "0"], ["1", "0", "0"], ["1", "1", "0"], ["0", "1", "0"]],
            polygon: [["0", "0", "0"], ["1", "0", "0"], ["1", "1", "0"], ["0", "1", "0"]],
            vertex_ids: ["A", "B", "C", "D"],
          },
          {
            id: "chieu_cao_SA",
            type: "segment3",
            label: "Đường cao SA",
            notation: "SA",
            origin: "derived",
            render: "segment",
            formation_roles: ["CONSTRUCT_HEIGHT"],
            depends: ["S", "A"],
            point_a: ["0", "0", "1"],
            point_b: ["0", "0", "0"],
            endpoints: [["0", "0", "1"], ["0", "0", "0"]],
            perpendicular_witness: {
              relation: "line_perp_plane",
              from: "S",
              foot_id: "A",
              foot: ["0", "0", "0"],
              on: "day_ABCD",
              plane_directions: [["1", "0", "0"], ["0", "1", "0"]],
              marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] },
            },
          },
          { id: "cb_SB", type: "segment3", label: "Cạnh bên SB", notation: "SB", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["S", "B"], endpoints: [["0", "0", "1"], ["1", "0", "0"]] },
          { id: "cb_SC", type: "segment3", label: "Cạnh bên SC", notation: "SC", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["S", "C"], endpoints: [["0", "0", "1"], ["1", "1", "0"]] },
          { id: "cb_SD", type: "segment3", label: "Cạnh bên SD", notation: "SD", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["S", "D"], endpoints: [["0", "0", "1"], ["0", "1", "0"]] },
          {
            id: "chop_SABCD",
            type: "solid",
            label: "Hình chóp S.ABCD",
            notation: "S.ABCD",
            origin: "derived",
            render: "mesh",
            formation_roles: ["CLOSE_SOLID"],
            depends: ["S", "A", "B", "C", "D"],
            vertex_ids: ["S", "A", "B", "C", "D"],
            vertices: [["0", "0", "1"], ["0", "0", "0"], ["1", "0", "0"], ["1", "1", "0"], ["0", "1", "0"]],
            faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]],
          },
          {
            id: "duong_AB",
            type: "line3",
            label: "Đường thẳng AB",
            notation: "AB",
            origin: "derived",
            render: "line",
            depends: ["A", "B"],
            point: ["0", "0", "0"],
            direction: ["1", "0", "0"],
          },
          {
            id: "duong_SC",
            type: "line3",
            label: "Đường thẳng SC",
            notation: "SC",
            origin: "derived",
            render: "line",
            depends: ["S", "C"],
            point: ["0", "0", "1"],
            direction: ["1", "1", "-1"],
          },
          {
            id: "kq_d_AB_SC",
            type: "quantity",
            label: "Khoảng cách giữa AB và SC",
            origin: "derived",
            render: "readout",
            depends: ["duong_AB", "duong_SC"],
            value: "√2",
            exact: { kind: "radical", coefficient: "1", radicand: 2 },
            annotation: {
              kind: "distance",
              witness: {
                relation: "common_perpendicular",
                on: "duong_AB",
                foot: ["1/2", "0", "0"],
                from_point: ["1/2", "1/2", "1/2"],
                marker: { u: ["1", "0", "0"], v: ["0", "1/2", "1/2"] },
                second: {
                  on: "duong_SC",
                  foot: ["1/2", "1/2", "1/2"],
                  marker: { u: ["1", "1", "-1"], v: ["0", "-1/2", "-1/2"] },
                },
              },
            },
          },
        ],
        events: [
          { step_index: 0, action: "INIT", objects: ["A", "B", "C", "D", "S"] },
          { step_index: 1, action: "CREATE", object: "day_ABCD", depends: ["A", "B", "C", "D"] },
          { step_index: 2, action: "CREATE", object: "chieu_cao_SA", depends: ["S", "A"] },
          { step_index: 3, action: "CREATE", object: "cb_SB", objects: ["cb_SB", "cb_SC", "cb_SD"], depends: ["S", "B", "C", "D"] },
          { step_index: 4, action: "CREATE", object: "chop_SABCD", depends: ["S", "A", "B", "C", "D"] },
          { step_index: 5, action: "CREATE", object: "duong_AB", depends: ["A", "B"] },
          { step_index: 6, action: "CREATE", object: "duong_SC", depends: ["S", "C"] },
          { step_index: 7, action: "MEASURE", object: "kq_d_AB_SC", depends: ["duong_AB", "duong_SC"] },
        ],
      } as unknown as Scene3D);

      const exactScene = makeAbScSkewScene();
      const exactCheck = verifySceneMathematicalConsistency(exactScene);
      expect(exactCheck.valid, JSON.stringify(exactCheck.contradictions)).toBe(true);

      // Forged prose coordinates ([0,0,0] and [2/3, 0, 4/3] -> chart [0,0,0] and [1/3, 0, 2/3], NOT on SC!) MUST fail closed
      const forgedProseScene = makeAbScSkewScene();
      const forgedQ = forgedProseScene.objects.find((o) => o.id === "kq_d_AB_SC")!;
      forgedQ.annotation!.witness = {
        ...forgedQ.annotation!.witness!,
        foot: ["0", "0", "0"],
        from_point: ["1/3", "0", "2/3"],
        marker: { u: ["1", "0", "0"], v: ["1/3", "0", "2/3"] },
        second: {
          on: "duong_SC",
          foot: ["1/3", "0", "2/3"],
          marker: { u: ["1", "1", "-1"], v: ["-1/3", "0", "-2/3"] },
        },
      };
      const forgedCheck = verifySceneMathematicalConsistency(forgedProseScene);
      expect(forgedCheck.valid).toBe(false);
      expect(forgedCheck.contradictions.some((c) => c.objectId === "kq_d_AB_SC")).toBe(true);

      // Valid common perpendicular feet but tampered distance norm (value = "3", exact = 3 != √2) MUST also fail closed
      const wrongNormScene = makeAbScSkewScene();
      const wrongNormQ = wrongNormScene.objects.find((o) => o.id === "kq_d_AB_SC")!;
      wrongNormQ.value = "3";
      wrongNormQ.exact = { kind: "rational", value: "3" };
      const wrongNormCheck = verifySceneMathematicalConsistency(wrongNormScene);
      expect(wrongNormCheck.valid).toBe(false);
      expect(wrongNormCheck.contradictions.some((c) => c.title.includes("khoảng cách"))).toBe(true);

      // Exterior second.foot (`d(DN, SB) = 2√6/3` where foot on SB lies outside [S, B]) is collected by diemChoDuong so carrier SB extends to the foot
      const exteriorFootScene = makeAbScSkewScene();
      const extLine = exteriorFootScene.objects.find((o) => o.id === "duong_SC")!;
      const extQ = exteriorFootScene.objects.find((o) => o.id === "kq_d_AB_SC")!;
      extQ.annotation!.witness!.second!.foot = ["3/2", "3/2", "-1/2"];
      const lineAnchorPts = diemChoDuong(exteriorFootScene.objects, extLine.id);
      expect(lineAnchorPts.some((pt) => Math.abs(pt[2] - -0.5) < 1e-6)).toBe(true);
    });

    it("PHẦN IV §11: renders #dock-goal-summary ONLY when goalCompletion.status !== 'reached' (e.g. missing_goal_output)", () => {
      const emptyStepScene = {
        version: 1,
        free_objects: ["A"],
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        ],
        events: [],
      } as unknown as Scene3D;
      const plan = buildPedagogicalConstructionPlan(emptyStepScene);
      expect(plan.goalCompletion.status).toBe("missing_goal_output");
      const htmlMissingGoal = renderToString(
        <AxoWorkspaceV62 scene={emptyStepScene} de="Cho điểm A." tieuDe="Cảnh thiếu mục tiêu" />,
      );
      expect(htmlMissingGoal).toContain('id="dock-goal-summary"');
      expect(htmlMissingGoal).toContain("Chưa đủ kết quả mục tiêu");
    });

    it("PHẦN III & PHẦN VI §16: generalizes step sequencing across 6 unseen novel scenes (scaled/translated pyramid, pentagonal oblique pyramid, rectangular oblique prism with foot H, 3-goal cone, exterior line-plane intersection, and novel sphere cut)", () => {
      // 1. Scaled & translated right pyramid K.EFGH (base square side 5, height KE = 12, shifted origin [10, -4, 3])
      const scaledPyr = {
        version: 1,
        free_objects: ["E", "F", "G", "H", "K"],
        objects: [
          { id: "E", type: "point3", label: "Điểm E", notation: "E", origin: "free", render: "point", depends: [], xyz: ["10", "-4", "3"] },
          { id: "F", type: "point3", label: "Điểm F", notation: "F", origin: "free", render: "point", depends: [], xyz: ["15", "-4", "3"] },
          { id: "G", type: "point3", label: "Điểm G", notation: "G", origin: "free", render: "point", depends: [], xyz: ["15", "1", "3"] },
          { id: "H", type: "point3", label: "Điểm H", notation: "H", origin: "free", render: "point", depends: [], xyz: ["10", "1", "3"] },
          { id: "K", type: "point3", label: "Điểm K", notation: "K", origin: "free", render: "point", depends: [], xyz: ["10", "-4", "15"] },
          {
            id: "base_EFGH",
            type: "polygon3",
            label: "Đáy EFGH là hình vuông",
            notation: "EFGH",
            origin: "derived",
            render: "polygon",
            surface_role: "BASE_REGION",
            formation_roles: ["CONSTRUCT_BASE"],
            depends: ["E", "F", "G", "H"],
            polygon: [["10", "-4", "3"], ["15", "-4", "3"], ["15", "1", "3"], ["10", "1", "3"]],
            vertex_ids: ["E", "F", "G", "H"],
          },
          {
            id: "lat_KE",
            type: "segment3",
            label: "Cạnh bên KE",
            notation: "KE",
            origin: "derived",
            render: "segment",
            formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"],
            depends: ["K", "E"],
            endpoints: [["10", "-4", "15"], ["10", "-4", "3"]],
            perpendicular_witness: {
              relation: "line_perp_plane",
              from: "K",
              foot_id: "E",
              foot: ["10", "-4", "3"],
              on: "base_EFGH",
              plane_directions: [["5", "0", "0"], ["0", "5", "0"]],
              marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] },
            },
          },
          { id: "lat_KF", type: "segment3", label: "Cạnh bên KF", notation: "KF", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["K", "F"], endpoints: [["10", "-4", "15"], ["15", "-4", "3"]] },
          { id: "lat_KG", type: "segment3", label: "Cạnh bên KG", notation: "KG", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["K", "G"], endpoints: [["10", "-4", "15"], ["15", "1", "3"]] },
          { id: "lat_KH", type: "segment3", label: "Cạnh bên KH", notation: "KH", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["K", "H"], endpoints: [["10", "-4", "15"], ["10", "1", "3"]] },
          {
            id: "sol_KEFGH",
            type: "solid",
            label: "Hình chóp K.EFGH",
            notation: "K.EFGH",
            origin: "derived",
            render: "mesh",
            formation_roles: ["CLOSE_SOLID"],
            depends: ["K", "E", "F", "G", "H"],
            vertex_ids: ["K", "E", "F", "G", "H"],
            vertices: [["10", "-4", "15"], ["10", "-4", "3"], ["15", "-4", "3"], ["15", "1", "3"], ["10", "1", "3"]],
            faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]],
          },
          { id: "vol_KEFGH", type: "quantity", label: "Thể tích khối chóp K.EFGH", origin: "derived", render: "readout", depends: ["sol_KEFGH"], value: "100", exact: "100", annotation: { kind: "volume" } },
        ],
        events: [
          { step_index: 0, action: "INIT", objects: ["E", "F", "G", "H", "K"] },
          { step_index: 1, action: "CREATE", object: "base_EFGH", depends: ["E", "F", "G", "H"] },
          { step_index: 2, action: "CREATE", object: "lat_KE", objects: ["lat_KE", "lat_KF", "lat_KG", "lat_KH"], depends: ["K", "E", "F", "G", "H"] },
          { step_index: 3, action: "CREATE", object: "sol_KEFGH", depends: ["K", "E", "F", "G", "H"] },
          { step_index: 4, action: "MEASURE", object: "vol_KEFGH", depends: ["sol_KEFGH"] },
        ],
      } as unknown as Scene3D;
      const scaledPlan = buildPedagogicalConstructionPlan(withSubEntities(scaledPyr));
      expect(scaledPlan.steps.map((s) => s.title)).toEqual([
        "Dựng đáy EFGH là hình vuông",
        "Dựng đường cao KE ⊥ (EFGH) tại E",
        "Dựng các cạnh bên KF, KG, KH",
        "Hoàn thiện hình chóp K.EFGH",
      ]);

      // 2. Pentagonal oblique pyramid P.ABCDE (5-sided base, NO certified altitude -> never fabricates altitude step)
      const pentPyr = {
        version: 1,
        free_objects: ["A", "B", "C", "D", "E", "P"],
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", render: "point", depends: [], xyz: ["2", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", render: "point", depends: [], xyz: ["3", "2", "0"] },
          { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", render: "point", depends: [], xyz: ["1", "3", "0"] },
          { id: "E", type: "point3", label: "Điểm E", notation: "E", origin: "free", render: "point", depends: [], xyz: ["-1", "2", "0"] },
          { id: "P", type: "point3", label: "Điểm P", notation: "P", origin: "free", render: "point", depends: [], xyz: ["1", "1", "4"] },
          {
            id: "base_pent",
            type: "polygon3",
            label: "Đáy ABCDE",
            notation: "ABCDE",
            origin: "derived",
            render: "polygon",
            surface_role: "BASE_REGION",
            formation_roles: ["CONSTRUCT_BASE"],
            depends: ["A", "B", "C", "D", "E"],
            polygon: [["0", "0", "0"], ["2", "0", "0"], ["3", "2", "0"], ["1", "3", "0"], ["-1", "2", "0"]],
            vertex_ids: ["A", "B", "C", "D", "E"],
          },
          { id: "cb_PA", type: "segment3", label: "PA", notation: "PA", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["P", "A"], endpoints: [["1", "1", "4"], ["0", "0", "0"]] },
          { id: "cb_PB", type: "segment3", label: "PB", notation: "PB", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["P", "B"], endpoints: [["1", "1", "4"], ["2", "0", "0"]] },
          { id: "cb_PC", type: "segment3", label: "PC", notation: "PC", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["P", "C"], endpoints: [["1", "1", "4"], ["3", "2", "0"]] },
          { id: "cb_PD", type: "segment3", label: "PD", notation: "PD", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["P", "D"], endpoints: [["1", "1", "4"], ["1", "3", "0"]] },
          { id: "cb_PE", type: "segment3", label: "PE", notation: "PE", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["P", "E"], endpoints: [["1", "1", "4"], ["-1", "2", "0"]] },
          {
            id: "sol_PABCDE",
            type: "solid",
            label: "Hình chóp ngũ giác P.ABCDE",
            notation: "P.ABCDE",
            origin: "derived",
            render: "mesh",
            formation_roles: ["CLOSE_SOLID"],
            depends: ["P", "A", "B", "C", "D", "E"],
            vertex_ids: ["P", "A", "B", "C", "D", "E"],
            vertices: [["1", "1", "4"], ["0", "0", "0"], ["2", "0", "0"], ["3", "2", "0"], ["1", "3", "0"], ["-1", "2", "0"]],
            faces: [[1, 2, 3, 4, 5], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 5], [0, 5, 1]],
          },
        ],
        events: [
          { step_index: 0, action: "INIT", objects: ["A", "B", "C", "D", "E", "P"] },
          { step_index: 1, action: "CREATE", object: "base_pent", depends: ["A", "B", "C", "D", "E"] },
          { step_index: 2, action: "CREATE", object: "cb_PA", depends: ["P", "A"] },
          { step_index: 3, action: "CREATE", object: "cb_PB", depends: ["P", "B"] },
          { step_index: 4, action: "CREATE", object: "cb_PC", depends: ["P", "C"] },
          { step_index: 5, action: "CREATE", object: "cb_PD", depends: ["P", "D"] },
          { step_index: 6, action: "CREATE", object: "cb_PE", depends: ["P", "E"] },
          { step_index: 7, action: "CREATE", object: "sol_PABCDE", depends: ["P", "A", "B", "C", "D", "E"] },
        ],
      } as unknown as Scene3D;
      const pentPlan = buildPedagogicalConstructionPlan(withSubEntities(pentPyr));
      expect(pentPlan.steps.map((s) => s.title)).toEqual([
        "Dựng mặt đáy ABCDE",
        "Dựng các cạnh bên PA, PB, PC, PD, PE",
        "Hoàn thiện hình chóp ngũ giác P.ABCDE",
      ]);
      expect(pentPlan.steps.some((s) => /đường cao/iu.test(s.title))).toBe(false);

      // 3. Rectangular oblique prism MNPQ.M′N′P′Q′ where foot H (midpoint of MN) is emitted BEFORE base in raw events -> reordered after base MNPQ and before M′N′P′Q′
      const oblPrism = {
        version: 1,
        free_objects: ["M", "N", "P", "Q", "Mp", "Np", "Pp", "Qp"],
        objects: [
          { id: "M", type: "point3", label: "M", notation: "M", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
          { id: "N", type: "point3", label: "N", notation: "N", origin: "free", render: "point", depends: [], xyz: ["4", "0", "0"] },
          { id: "P", type: "point3", label: "P", notation: "P", origin: "free", render: "point", depends: [], xyz: ["4", "2", "0"] },
          { id: "Q", type: "point3", label: "Q", notation: "Q", origin: "free", render: "point", depends: [], xyz: ["0", "2", "0"] },
          { id: "H", type: "point3", label: "Trung điểm H", notation: "H", origin: "derived", render: "point", depends: ["M", "N"], xyz: ["2", "0", "0"] },
          { id: "Mp", type: "point3", label: "M′", notation: "M′", origin: "free", render: "point", depends: [], xyz: ["2", "0", "3"] },
          { id: "Np", type: "point3", label: "N′", notation: "N′", origin: "free", render: "point", depends: [], xyz: ["6", "0", "3"] },
          { id: "Pp", type: "point3", label: "P′", notation: "P′", origin: "free", render: "point", depends: [], xyz: ["6", "2", "3"] },
          { id: "Qp", type: "point3", label: "Q′", notation: "Q′", origin: "free", render: "point", depends: [], xyz: ["2", "2", "3"] },
          {
            id: "base_MNPQ",
            type: "polygon3",
            label: "Đáy MNPQ là hình chữ nhật",
            notation: "MNPQ",
            origin: "derived",
            render: "polygon",
            surface_role: "BASE_REGION",
            formation_roles: ["CONSTRUCT_BASE"],
            depends: ["M", "N", "P", "Q"],
            polygon: [["0", "0", "0"], ["4", "0", "0"], ["4", "2", "0"], ["0", "2", "0"]],
            vertex_ids: ["M", "N", "P", "Q"],
          },
          {
            id: "top_MpNpPpQp",
            type: "polygon3",
            label: "Đáy M′N′P′Q′",
            notation: "M′N′P′Q′",
            origin: "derived",
            render: "polygon",
            surface_role: "BASE_REGION",
            formation_roles: ["CONSTRUCT_TRANSLATED_FACE"],
            depends: ["Mp", "Np", "Pp", "Qp"],
            polygon: [["2", "0", "3"], ["6", "0", "3"], ["6", "2", "3"], ["2", "2", "3"]],
            vertex_ids: ["Mp", "Np", "Pp", "Qp"],
          },
          { id: "le_MM", type: "segment3", label: "MM′", notation: "MM′", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["M", "Mp"], endpoints: [["0", "0", "0"], ["2", "0", "3"]] },
          { id: "le_NN", type: "segment3", label: "NN′", notation: "NN′", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["N", "Np"], endpoints: [["4", "0", "0"], ["6", "0", "3"]] },
          { id: "le_PP", type: "segment3", label: "PP′", notation: "PP′", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["P", "Pp"], endpoints: [["4", "2", "0"], ["6", "2", "3"]] },
          { id: "le_QQ", type: "segment3", label: "QQ′", notation: "QQ′", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["Q", "Qp"], endpoints: [["0", "2", "0"], ["2", "2", "3"]] },
          {
            id: "prism_sol",
            type: "solid",
            label: "Lăng trụ xiên MNPQ.M′N′P′Q′",
            notation: "MNPQ.M′N′P′Q′",
            origin: "derived",
            render: "mesh",
            formation_roles: ["CLOSE_SOLID"],
            depends: ["M", "N", "P", "Q", "Mp", "Np", "Pp", "Qp"],
            vertex_ids: ["M", "N", "P", "Q", "Mp", "Np", "Pp", "Qp"],
            vertices: [["0", "0", "0"], ["4", "0", "0"], ["4", "2", "0"], ["0", "2", "0"], ["2", "0", "3"], ["6", "0", "3"], ["6", "2", "3"], ["2", "2", "3"]],
            faces: [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]],
          },
          { id: "vol_prism", type: "quantity", label: "Thể tích lăng trụ", origin: "derived", render: "readout", depends: ["prism_sol"], value: "24", exact: "24", annotation: { kind: "volume" } },
        ],
        events: [
          { step_index: 0, action: "INIT", objects: ["M", "N", "P", "Q", "Mp", "Np", "Pp", "Qp"] },
          { step_index: 1, action: "CREATE", object: "H", depends: ["M", "N"] },
          { step_index: 2, action: "CREATE", object: "base_MNPQ", depends: ["M", "N", "P", "Q"] },
          { step_index: 3, action: "CREATE", object: "top_MpNpPpQp", depends: ["Mp", "Np", "Pp", "Qp"] },
          { step_index: 4, action: "CREATE", object: "le_MM", objects: ["le_MM", "le_NN", "le_PP", "le_QQ"], depends: ["M", "N", "P", "Q", "Mp", "Np", "Pp", "Qp"] },
          { step_index: 5, action: "CREATE", object: "prism_sol", depends: ["M", "N", "P", "Q", "Mp", "Np", "Pp", "Qp"] },
          { step_index: 6, action: "MEASURE", object: "vol_prism", depends: ["prism_sol"] },
        ],
      } as unknown as Scene3D;
      const oblPrismPlan = buildPedagogicalConstructionPlan(withSubEntities(oblPrism));
      expect(oblPrismPlan.reordered).toBe(true);
      expect(oblPrismPlan.steps.map((s) => s.title)).toEqual([
        "Dựng đáy MNPQ là hình chữ nhật",
        "Xác định trung điểm H của MN",
        "Dựng mặt đáy đối diện M′N′P′Q′ của lăng trụ",
        "Dựng các cạnh bên MM′, NN′, PP′, QQ′",
        "Hoàn thiện lăng trụ xiên MNPQ.M′N′P′Q′",
      ]);

      // 4. Novel cone with custom symbols (apex T, center C, rim E, R=5, h=12, l=13) and 3 target metrics (l, Sxq, V), with generator TE emitted BEFORE base in raw events
      const novelCone = {
        version: 1,
        free_objects: ["C", "E", "T"],
        objects: [
          { id: "C", type: "point3", label: "Tâm C", notation: "C", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
          { id: "E", type: "point3", label: "Điểm E", notation: "E", origin: "free", render: "point", depends: [], xyz: ["5", "0", "0"] },
          { id: "T", type: "point3", label: "Đỉnh T", notation: "T", origin: "free", render: "point", depends: [], xyz: ["0", "0", "12"] },
          { id: "gen_TE", type: "segment3", label: "Đường sinh TE", notation: "TE", origin: "derived", render: "segment", depends: ["T", "E"], endpoints: [["0", "0", "12"], ["5", "0", "0"]] },
          {
            id: "cone_TCE",
            type: "curved_solid",
            curved_kind: "cone",
            label: "Hình nón đỉnh T",
            notation: "TC",
            origin: "derived",
            render: "mesh",
            depends: ["T", "C", "E"],
            anchor: ["0", "0", "0"],
            apex_or_top: ["0", "0", "12"],
            axis: ["0", "0", "12"],
            radius_sq: "25",
            height_sq: "144",
          },
          { id: "q_l", type: "quantity", label: "Độ dài đường sinh TE", origin: "derived", render: "readout", depends: ["T", "E"], value: "13", exact: "13" },
          { id: "q_sxq", type: "quantity", label: "Diện tích xung quanh hình nón", origin: "derived", render: "readout", depends: ["cone_TCE"], value: "65π", exact: "65*pi", annotation: { kind: "area" } },
          { id: "q_vol", type: "quantity", label: "Thể tích khối nón", origin: "derived", render: "readout", depends: ["cone_TCE"], value: "100π", exact: "100*pi", annotation: { kind: "volume" } },
        ],
        events: [
          { step_index: 0, action: "INIT", objects: ["C", "E", "T"] },
          { step_index: 1, action: "CREATE", object: "gen_TE", depends: ["T", "E"] },
          { step_index: 2, action: "CREATE", object: "cone_TCE", depends: ["T", "C", "E"] },
          { step_index: 3, action: "MEASURE", object: "q_l", depends: ["T", "E"] },
          { step_index: 4, action: "MEASURE", object: "q_sxq", depends: ["cone_TCE"] },
          { step_index: 5, action: "MEASURE", object: "q_vol", depends: ["cone_TCE"] },
        ],
      } as unknown as Scene3D;
      const conePlan = buildPedagogicalConstructionPlan(withSubEntities(novelCone));
      expect(conePlan.steps.length).toBe(4);
      expect(conePlan.steps[0].title).toBe("Dựng đường tròn đáy tâm C, bán kính CE của hình nón");
      expect(conePlan.steps[1].title).toMatch(/dựng đường cao.*TC của hình nón/iu);
      expect(conePlan.steps[2].title).toBe("Dựng đường sinh TE của hình nón");
      expect(conePlan.steps[3].title).toMatch(/^Hoàn thiện mặt xung quanh hình nón/u);
      expect(conePlan.steps.some((s) => /^Tính /u.test(s.title))).toBe(false);
      expect(conePlan.goalCompletion.items.map((it) => it.valueText)).toEqual(["13", "65π", "100π"]);

      // 5. Construction-only exterior line–plane intersection (I = EF ∩ (α) outside [E, F], steep plane, zero numeric metric step)
      const extLinePlane = {
        version: 1,
        free_objects: ["A", "B", "C", "E", "F"],
        objects: [
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point", depends: [], xyz: ["2", "0", "1"] },
          { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point", depends: [], xyz: ["0", "2", "1"] },
          { id: "E", type: "point3", label: "E", notation: "E", origin: "free", render: "point", depends: [], xyz: ["0", "0", "4"] },
          { id: "F", type: "point3", label: "F", notation: "F", origin: "free", render: "point", depends: [], xyz: ["0", "0", "2"] },
          { id: "mp_alpha", type: "plane3", label: "Mặt phẳng (α)", notation: "(α)", origin: "derived", render: "surface", depends: ["A", "B", "C"], point: ["0", "0", "0"], normal: ["-1", "-1", "2"] },
          { id: "line_ef", type: "line3", label: "Đường thẳng EF", notation: "EF", origin: "derived", render: "line", depends: ["E", "F"], point: ["0", "0", "4"], direction: ["0", "0", "-2"] },
          { id: "I", type: "point3", label: "Giao điểm I", notation: "I", origin: "derived", render: "point", depends: ["line_ef", "mp_alpha"], source: { instruction: "intersect_line_plane" }, xyz: ["0", "0", "0"] },
        ],
        events: [
          { step_index: 0, action: "INIT", objects: ["A", "B", "C", "E", "F"] },
          { step_index: 1, action: "CREATE", object: "mp_alpha", depends: ["A", "B", "C"] },
          { step_index: 2, action: "CREATE", object: "line_ef", depends: ["E", "F"] },
          { step_index: 3, action: "CREATE", object: "I", depends: ["line_ef", "mp_alpha"] },
        ],
      } as unknown as Scene3D;
      expect(verifySceneMathematicalConsistency(extLinePlane).valid).toBe(true);
      const extLpPlan = buildPedagogicalConstructionPlan(withSubEntities(extLinePlane));
      expect(extLpPlan.goalCompletion.primaryKind).toBe("intersection_point");
      expect(extLpPlan.steps[extLpPlan.steps.length - 1].title).toMatch(/(?:Xác định giao điểm|Kéo dài).*I/u);
      expect(extLpPlan.steps.some((s) => /^Tính /u.test(s.title))).toBe(false);

      // 6. Novel sphere cut (center J, R = 10, plane distance d = 6 => r = 8) with 2 target metrics (r, S)
      const novelSphereCut = {
        version: 1,
        free_objects: ["J", "U"],
        objects: [
          { id: "J", type: "point3", label: "Tâm J", notation: "J", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
          { id: "U", type: "point3", label: "Điểm U", notation: "U", origin: "free", render: "point", depends: [], xyz: ["10", "0", "0"] },
          {
            id: "ball_J",
            type: "curved_solid",
            curved_kind: "ball",
            label: "Mặt cầu (S)",
            notation: "(S)",
            origin: "derived",
            render: "mesh",
            depends: ["J", "U"],
            anchor: ["0", "0", "0"],
            radius_sq: "100",
          },
          { id: "mp_beta", type: "plane3", label: "Mặt phẳng (β)", notation: "(β)", origin: "free", render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["0", "0", "6"], normal: ["0", "0", "1"] },
          { id: "sec_circ", type: "circle3", label: "Đường tròn thiết diện", origin: "derived", render: "curve", surface_role: "SECTION_REGION", depends: ["ball_J", "mp_beta"], center: ["0", "0", "6"], normal: ["0", "0", "1"], radius_sq: "64" },
          { id: "q_r_sec", type: "quantity", label: "Bán kính đường tròn giao tuyến", origin: "derived", render: "readout", depends: ["sec_circ"], value: "8", exact: "8" },
          { id: "q_s_sec", type: "quantity", label: "Diện tích hình tròn thiết diện", origin: "derived", render: "readout", depends: ["sec_circ"], value: "64π", exact: "64*pi", annotation: { kind: "area" } },
        ],
        events: [
          { step_index: 0, action: "INIT", objects: ["J", "U"] },
          { step_index: 1, action: "CREATE", object: "ball_J", depends: ["J", "U"] },
          { step_index: 2, action: "CREATE", object: "mp_beta", depends: ["J"] },
          { step_index: 3, action: "CREATE", object: "sec_circ", depends: ["ball_J", "mp_beta"] },
          { step_index: 4, action: "MEASURE", object: "q_r_sec", depends: ["sec_circ"] },
          { step_index: 5, action: "MEASURE", object: "q_s_sec", depends: ["sec_circ"] },
        ],
      } as unknown as Scene3D;
      expect(verifySceneMathematicalConsistency(novelSphereCut).valid).toBe(true);
      const sphereCutPlan = buildPedagogicalConstructionPlan(withSubEntities(novelSphereCut));
      expect(sphereCutPlan.steps[sphereCutPlan.steps.length - 1].title).toBe("Dựng đường tròn thiết diện giao của (S) và (β)");
      expect(sphereCutPlan.steps[sphereCutPlan.steps.length - 1].subtitle).toMatch(/hình\s+chiếu\s+vuông\s+góc/iu);
      expect(sphereCutPlan.steps[sphereCutPlan.steps.length - 1].subtitle).not.toContain("R² = d² + r²");
      expect(sphereCutPlan.steps[sphereCutPlan.steps.length - 1].subtitle).not.toContain("64π");
      expect(sphereCutPlan.goalCompletion.items.map((it) => it.valueText)).toEqual(["8", "64π"]);

      // 7. Coplanar plane with lower base vs parallel upper base: never falsely claim coplanar base is "song song với mặt đáy"
      const coplanarBaseCheckScene = {
        objects: [
          {
            id: "base_bot",
            type: "polygon3",
            label: "Đáy ABC",
            notation: "ABC",
            origin: "derived",
            render: "polygon",
            surface_role: "BASE_REGION",
            depends: ["A", "B", "C"],
            polygon: [["0", "0", "0"], ["4", "0", "0"], ["0", "4", "0"]],
          },
          {
            id: "base_top",
            type: "polygon3",
            label: "Đáy A'B'C'",
            notation: "A'B'C'",
            origin: "derived",
            render: "polygon",
            surface_role: "BASE_REGION",
            depends: ["A'", "B'", "C'"],
            polygon: [["0", "0", "5"], ["4", "0", "5"], ["0", "4", "5"]],
          },
          {
            id: "pl_abc",
            type: "plane3",
            label: "Mặt phẳng (ABC)",
            notation: "(ABC)",
            origin: "derived",
            render: "surface",
            depends: ["A", "B", "C"],
            point: ["0", "0", "0"],
            normal: ["0", "0", "1"],
          },
          {
            id: "pl_mid",
            type: "plane3",
            label: "Mặt phẳng (MNP)",
            notation: "(MNP)",
            origin: "derived",
            render: "surface",
            depends: ["M", "N", "P"],
            point: ["0", "0", "2"],
            normal: ["0", "0", "1"],
          },
        ],
      } as unknown as Scene3D;
      expect(findParallelBaseForPlane(coplanarBaseCheckScene, coplanarBaseCheckScene.objects[2])).toBeNull();
      expect(findParallelBaseForPlane(coplanarBaseCheckScene, coplanarBaseCheckScene.objects[3])).toBe("(ABC)");

      // 8. Section-area conclusion step inside a polyhedral solid names the section, never the parent solid
      const secAreaInPrism = {
        version: 1,
        free_objects: ["A", "B", "C", "A'", "B'", "C'"],
        objects: [
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point", depends: [], xyz: ["3", "0", "0"] },
          { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point", depends: [], xyz: ["0", "4", "0"] },
          { id: "A'", type: "point3", label: "A'", notation: "A'", origin: "free", render: "point", depends: [], xyz: ["0", "0", "4"] },
          { id: "B'", type: "point3", label: "B'", notation: "B'", origin: "free", render: "point", depends: [], xyz: ["3", "0", "4"] },
          { id: "C'", type: "point3", label: "C'", notation: "C'", origin: "free", render: "point", depends: [], xyz: ["0", "4", "4"] },
          {
            id: "sol_prism",
            type: "solid",
            label: "Lăng trụ đứng ABC.A'B'C'",
            notation: "ABC.A'B'C'",
            shape_class: "PRISM_LIKE",
            origin: "derived",
            render: "mesh",
            depends: ["A", "B", "C", "A'", "B'", "C'"],
            vertex_ids: ["A", "B", "C", "A'", "B'", "C'"],
            vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "4", "0"], ["0", "0", "4"], ["3", "0", "4"], ["0", "4", "4"]],
            faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]],
          },
          { id: "M", type: "point3", label: "Trung điểm M của AA'", notation: "M", origin: "derived", producer: "construct_point.midpoint", render: "point", depends: ["A", "A'"], xyz: ["0", "0", "2"] },
          { id: "pl_cut", type: "plane3", label: "Mặt phẳng (MBC')", notation: "(MBC')", origin: "derived", render: "surface", surface_role: "CUTTING_PLANE", depends: ["M", "B", "C'"], point: ["0", "0", "2"], normal: ["-8", "6", "-12"] },
          {
            id: "td",
            type: "section",
            label: "Thiết diện MBC'",
            notation: "MBC'",
            origin: "derived",
            render: "polygon",
            surface_role: "SECTION_REGION",
            depends: ["sol_prism", "pl_cut"],
            polygon: [["0", "0", "2"], ["3", "0", "0"], ["0", "4", "4"]],
            closed: true,
          },
          { id: "pl_do", type: "plane3", label: "Mặt phẳng đo", origin: "derived", render: "surface", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], depends: ["M", "B", "C'"], point: ["0", "0", "2"], normal: ["-8", "6", "-12"] },
          { id: "q_s_td", type: "quantity", label: "Diện tích thiết diện MBC'", origin: "derived", render: "readout", depends: ["td", "pl_do"], value: "3√41/2", exact: "3*sqrt(41)/2", annotation: { kind: "area", subject_ids: ["td"] } },
        ],
        events: [
          { step_index: 0, action: "INIT", objects: ["A", "B", "C", "A'", "B'", "C'"] },
          { step_index: 1, action: "CREATE", object: "sol_prism", depends: ["A", "B", "C", "A'", "B'", "C'"] },
          { step_index: 2, action: "CREATE", object: "M", depends: ["A", "A'"] },
          { step_index: 3, action: "CREATE", object: "pl_cut", depends: ["M", "B", "C'"] },
          { step_index: 4, action: "CREATE", object: "td", depends: ["sol_prism", "pl_cut"] },
          { step_index: 5, action: "CREATE", object: "pl_do", depends: ["M", "B", "C'"] },
          { step_index: 6, action: "MEASURE", object: "q_s_td", depends: ["td", "pl_do"] },
        ],
      } as unknown as Scene3D;
      const secAreaPlan = buildPedagogicalConstructionPlan(withSubEntities(secAreaInPrism));
      expect(secAreaPlan.steps.some((s) => /^Tính /iu.test(s.title) || s.title.includes("(đo)"))).toBe(false);
      expect(secAreaPlan.steps[secAreaPlan.steps.length - 1].title).toMatch(/thiết diện \(?MBC[′']\)?/iu);
      expect(secAreaPlan.goalCompletion.items[0]?.label).toMatch(/^Diện tích thiết diện \(?MBC[′']\)?$/u);
      expect(secAreaPlan.goalCompletion.items[0]?.label).not.toContain("lăng trụ");

      // Verify universal DAG prerequisite invariant & zero future leakage across all unseen scenes
      for (const plan of [scaledPlan, pentPlan, oblPrismPlan, conePlan, extLpPlan, sphereCutPlan]) {
        const seen = new Set<string>(plan.scene.free_objects);
        for (const st of plan.steps) {
          expect(st.title.trim().length).toBeGreaterThan(0);
          expect(st.targetIds.length).toBeGreaterThan(0);
          for (const pre of st.prerequisiteIds) {
            expect(seen.has(pre)).toBe(true);
          }
          for (const v of st.visibleIds) seen.add(v);
          for (const t of st.targetIds) seen.add(t);
        }
      }
    });
  });
});
