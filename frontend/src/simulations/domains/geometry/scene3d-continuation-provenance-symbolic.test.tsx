import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import * as THREE from "three";
import {
  hopLeScene3D,
  hienSo,
  ghiChuGiaTriDung,
  objectsAt,
  stepCount,
  attachHybridViewToScene,
  registerExactSceneOrigin,
  type Scene3D,
  type SceneObject,
} from "./scene3d-model";
import { veKhongGian } from "./scene3d-chart";
import { withSubEntities } from "./scene3d-subentities";
import {
  annotationsAt,
  annotationAnchor,
  classifyQuantityProvenance,
  DEFAULT_ANNOTATION_VIEW,
  givenQuantitiesSummary,
  placeAnnotationLabels,
} from "./scene3d-annotations";
import { auxiliaryHiddenAt, auxiliaryObjects } from "./scene3d-auxiliary";
import {
  buildPedagogicalConstructionPlan,
  classifyPolygonShapeWithProvenance,
  classifyScenePolygonShape,
  classifySphereSemanticRole,
  formatCompactEntityChipLabel,
  resolvePlaneSectionVisibility,
  shouldShowSphereReferenceEquator,
} from "./scene3d-semantic-policy";
import { buildObject3D } from "./scene3d-view";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";

function buildUnderdeterminedSabcScene(opts?: {
  cXyz?: [string, string, string];
  symbolic?: boolean;
  includeUnverifiedBc?: boolean;
  renameVertices?: boolean;
}): Scene3D {
  const cXyz = opts?.cXyz ?? ["0", "2", "0"];
  const symbolic = opts?.symbolic ?? true;
  const [nA, nB, nC, nS] = opts?.renameVertices ? ["M", "N", "P", "K"] : ["A", "B", "C", "S"];
  const baseId = `day_${nA}${nB}${nC}`;
  const heightId = `cao_${nS.toLowerCase()}${nA.toLowerCase()}`;
  const solidId = `khoi_${nS.toLowerCase()}${nA.toLowerCase()}${nB.toLowerCase()}${nC.toLowerCase()}`;
  const qAbId = symbolic ? "q_ab_2a" : "q_ab_2";
  const qSaId = symbolic ? "q_sa_4a" : "q_sa_4";

  const objects: SceneObject[] = [
    { id: nA, type: "point3", label: `Điểm ${nA}`, notation: nA, origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"], source: {} },
    { id: nB, type: "point3", label: `Điểm ${nB}`, notation: nB, origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"], source: {} },
    { id: nC, type: "point3", label: `Điểm ${nC}`, notation: nC, origin: "free", producer: null, render: "point_marker", depends: [], xyz: cXyz, source: {} },
    { id: nS, type: "point3", label: `Điểm ${nS}`, notation: nS, origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"], source: {} },
    {
      id: baseId,
      type: "polygon3",
      label: `Đáy ${nA}${nB}${nC}`,
      notation: `${nA}${nB}${nC}`,
      role: `Đa giác ${nA}, ${nB}, ${nC}`,
      origin: "derived",
      producer: "construct_polygon",
      render: "polygon",
      surface_role: "BASE_REGION",
      depends: [nA, nB, nC],
      vertex_ids: [nA, nB, nC],
      vertices: [["0", "0", "0"], ["2", "0", "0"], cXyz],
    },
    {
      id: heightId,
      type: "segment3",
      label: `Đường cao ${nS}${nA}`,
      notation: `${nS}${nA}`,
      origin: "derived",
      producer: "construct_segment",
      render: "segment",
      depends: [nS, nA],
      formation_roles: ["CONSTRUCT_HEIGHT"],
      endpoint_ids: [nS, nA],
      endpoints: [["0", "0", "4"], ["0", "0", "0"]],
      perpendicular_witness: {
        from: nS,
        foot: ["0", "0", "0"],
        foot_id: nA,
        on: baseId,
        relation: "line_perp_plane",
        plane_directions: [["2", "0", "0"], cXyz],
        marker: { u: ["2", "0", "0"], v: ["0", "0", "4"] },
      },
    },
    {
      id: solidId,
      type: "solid",
      label: `Hình chóp ${nS}.${nA}${nB}${nC}`,
      notation: `${nS}.${nA}${nB}${nC}`,
      shape_class: "PYRAMID_LIKE",
      origin: "derived",
      producer: "construct_solid",
      render: "mesh",
      depends: [nS, nA, nB, nC],
      formation_roles: ["CLOSE_SOLID"],
      vertex_ids: [nS, nA, nB, nC],
      vertices: [["0", "0", "4"], ["0", "0", "0"], ["2", "0", "0"], cXyz],
      faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]],
    },
    {
      id: qAbId,
      type: "quantity",
      label: `Độ dài ${nA}${nB}`,
      notation: `${nA}${nB}`,
      origin: "free",
      producer: null,
      render: "readout",
      depends: [nA, nB],
      value: symbolic ? "2a" : "2",
      ...(symbolic ? {} : { exact: { kind: "rational", value: "2" } }),
      source: { fact_id: "f_ab" },
      annotation: { kind: "length", category: "measurement", role: "given", subject_ids: [nA, nB], anchor: "segment" },
    },
    {
      id: qSaId,
      type: "quantity",
      label: `Độ dài ${nS}${nA}`,
      notation: `${nS}${nA}`,
      origin: "free",
      producer: null,
      render: "readout",
      depends: [nS, nA],
      value: symbolic ? "4a" : "4",
      ...(symbolic ? {} : { exact: { kind: "rational", value: "4" } }),
      source: { fact_id: "f_sa" },
      annotation: { kind: "length", category: "measurement", role: "given", subject_ids: [nS, nA], anchor: "segment" },
    },
  ];

  if (opts?.includeUnverifiedBc) {
    objects.push({
      id: "q_bc_unverified",
      type: "quantity",
      label: `Độ dài ${nB}${nC}`,
      notation: `${nB}${nC}`,
      origin: "free",
      producer: null,
      render: "readout",
      depends: [nB, nC],
      value: "2√2",
      source: {},
      annotation: { kind: "length", category: "measurement", subject_ids: [nB, nC], anchor: "segment" },
    });
  }

  return {
    free_objects: [nA, nB, nC, nS, qAbId, qSaId],
    chart_metric: [
      ["1", "0", "0"],
      ["0", "1", "0"],
      ["0", "0", "1"],
    ],
    ...(symbolic ? { length_unit: { symbol: "a", display_scale: "a = 1 đơn vị dựng", is_given: false } } : {}),
    objects,
    events: [
      { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Đặt các điểm." },
      { step_index: 1, action: "CREATE", object: baseId, depends: [nA, nB, nC], explanation: "Dựng đáy." },
      { step_index: 2, action: "CREATE", object: heightId, depends: [nS, nA], explanation: "Dựng đường cao." },
      { step_index: 3, action: "CREATE", object: solidId, depends: [nS, nA, nB, nC], explanation: "Hoàn thiện khối chóp." },
    ],
  };
}

describe("AXO Master Continuation — Priority A: Semantic Provenance & Counterfactuals", () => {
  it("A1. Mandatory S.ABC (SA ⊥ (ABC), AB = 2a, SA = 4a) never claims ABC is vuông cân despite identity chart_metric & (0,0,0)-(2,0,0)-(0,2,0)", () => {
    const scene = buildUnderdeterminedSabcScene({ symbolic: true });
    const base = scene.objects.find((o) => o.id === "day_ABC")!;
    const prov = classifyPolygonShapeWithProvenance(scene, base);
    expect(prov.certifiedShape).toBeNull();
    expect(prov.provenance).not.toBe("GIVEN");
    expect(prov.provenance).not.toBe("DERIVED_VERIFIED");
    expect(classifyScenePolygonShape(scene, base)).toBe("tam giác");

    const plan = buildPedagogicalConstructionPlan(withSubEntities(scene));
    const stepTexts = plan.steps.map((s) => `${s.title} ${s.subtitle}`).join(" | ");
    expect(stepTexts).not.toMatch(/tam\s+giác\s+vuông\s+cân|tam\s+giác\s+vuông|tam\s+giác\s+cân|tam\s+giác\s+đều/iu);
  });

  it("A2. Distinguishes ABC right-given, ABC right-certified by witness, ABC equilateral-given, square-certified, and rectangle-not-square", () => {
    // 1. ABC right given on equal-leg coords -> tam giác vuông (NOT vuông cân)
    const rightGiven = buildUnderdeterminedSabcScene({ symbolic: false });
    const baseRightGiven = rightGiven.objects.find((o) => o.id === "day_ABC")!;
    baseRightGiven.label = "Tam giác ABC vuông tại A";
    const pRightGiven = classifyPolygonShapeWithProvenance(rightGiven, baseRightGiven);
    expect(pRightGiven.provenance).toBe("GIVEN");
    expect(pRightGiven.certifiedShape).toBe("tam giác vuông");

    // 2. ABC right certified via Backend in-plane perpendicular_witness (generic label, equal-leg coords)
    const rightCert = buildUnderdeterminedSabcScene({ symbolic: false });
    rightCert.objects.push({
      id: "seg_ab_perp_ac",
      type: "segment3",
      label: "Cạnh AB",
      notation: "AB",
      origin: "derived",
      producer: "construct_segment",
      render: "segment",
      depends: ["A", "B"],
      endpoint_ids: ["A", "B"],
      endpoints: [["0", "0", "0"], ["2", "0", "0"]],
      perpendicular_witness: {
        from: "B",
        foot: ["0", "0", "0"],
        foot_id: "A",
        on: "C",
        relation: "perpendicular_lines",
        can_present_as_proven: true,
        certificate: "in_plane_orthogonality",
        marker: { u: ["0", "2", "0"], v: ["2", "0", "0"], u_to: "C" },
      },
    });
    const pRightCert = classifyPolygonShapeWithProvenance(
      rightCert,
      rightCert.objects.find((o) => o.id === "day_ABC")!,
    );
    expect(pRightCert.provenance).toBe("DERIVED_VERIFIED");
    expect(pRightCert.certifiedShape).toBe("tam giác vuông");

    // 3. ABC equilateral given on affine chart_metric
    const eqScene: Scene3D = {
      free_objects: ["A", "B", "C"],
      chart_metric: [
        ["4", "2", "0"],
        ["2", "4", "0"],
        ["0", "0", "1"],
      ],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "0", "0"] },
        { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "1", "0"] },
        { id: "day_eq", type: "polygon3", label: "Tam giác đều ABC", notation: "ABC", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"]] },
      ],
      events: [
        { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
        { step_index: 1, action: "CREATE", object: "day_eq", depends: ["A", "B", "C"], explanation: "Base" },
      ],
    };
    const pEq = classifyPolygonShapeWithProvenance(eqScene, eqScene.objects[3]);
    expect(pEq.provenance).toBe("GIVEN");
    expect(pEq.certifiedShape).toBe("tam giác đều");

    // 4. Certified square vs Non-square rectangle on equal-side coordinates
    const quadBase = (label: string): Scene3D => ({
      free_objects: ["A", "B", "C", "D"],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
        { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "2", "0"] },
        { id: "D", type: "point3", label: "D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
        { id: "day_quad", type: "polygon3", label, notation: "ABCD", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", depends: ["A", "B", "C", "D"], vertex_ids: ["A", "B", "C", "D"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]] },
      ],
      events: [
        { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
        { step_index: 1, action: "CREATE", object: "day_quad", depends: ["A", "B", "C", "D"], explanation: "Base" },
      ],
    });
    const sqRes = classifyPolygonShapeWithProvenance(quadBase("Hình vuông đáy ABCD"), quadBase("Hình vuông đáy ABCD").objects[4]);
    expect(sqRes.provenance).toBe("GIVEN");
    expect(sqRes.certifiedShape).toBe("hình vuông");

    const rectRes = classifyPolygonShapeWithProvenance(quadBase("Đáy ABCD là hình chữ nhật"), quadBase("Đáy ABCD là hình chữ nhật").objects[4]);
    expect(rectRes.provenance).toBe("GIVEN");
    expect(rectRes.certifiedShape).toBe("hình chữ nhật");

    const genericQuad = quadBase("Đáy ABCD");
    const genQuadRes = classifyPolygonShapeWithProvenance(genericQuad, genericQuad.objects[4]);
    expect(genQuadRes.certifiedShape).toBeNull();
    expect(classifyScenePolygonShape(genericQuad, genericQuad.objects[4])).toBe("tứ giác");
  });

  it("A3. Never self-measures coordinates into DERIVED_VERIFIED without Backend certificate, and catches contradictory provenance", () => {
    const sssNoCert: Scene3D = {
      free_objects: ["A", "B", "C", "q_ab", "q_ac", "q_bc"],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
        { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
        { id: "day_sss", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "4", "0"]] },
        { id: "q_ab", type: "quantity", label: "AB", notation: "AB", origin: "free", producer: null, render: "readout", depends: ["A", "B"], value: "3", annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "B"], anchor: "segment" } },
        { id: "q_ac", type: "quantity", label: "AC", notation: "AC", origin: "free", producer: null, render: "readout", depends: ["A", "C"], value: "4", annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "C"], anchor: "segment" } },
        { id: "q_bc", type: "quantity", label: "BC", notation: "BC", origin: "free", producer: null, render: "readout", depends: ["B", "C"], value: "5", annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["B", "C"], anchor: "segment" } },
      ],
      events: [
        { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
        { step_index: 1, action: "CREATE", object: "day_sss", depends: ["A", "B", "C"], explanation: "Base" },
      ],
    };
    const sssRes = classifyPolygonShapeWithProvenance(sssNoCert, sssNoCert.objects[3]);
    expect(sssRes.provenance).not.toBe("DERIVED_VERIFIED");
    expect(sssRes.provenance).not.toBe("GIVEN");
    expect(sssRes.certifiedShape).toBeNull();

    // Contradictory metadata: claims provenance GIVEN and ILLUSTRATIVE_CONFIGURATION simultaneously
    const contradictoryScene = buildUnderdeterminedSabcScene({ symbolic: false });
    const cBase = contradictoryScene.objects.find((o) => o.id === "day_ABC")!;
    (cBase as unknown as { source: Record<string, unknown> }).source = {
      is_given: true,
      provenance: "GIVEN",
      assumption: "ILLUSTRATIVE_CONFIGURATION",
    };
    const cRes = classifyPolygonShapeWithProvenance(contradictoryScene, cBase);
    expect(cRes.provenance).toBe("CONTRADICTORY_OR_UNSUPPORTED");
    expect(cRes.certifiedShape).toBeNull();
  });

  it("A4. Metamorphic, point-renaming, camera-invariance & uncertified tetrahedron checks", () => {
    const cLayouts: [string, string, string][] = [
      ["0", "2", "0"],   // accidental right-isosceles
      ["2", "3", "0"],   // scalene acute
      ["-1", "5/2", "0"], // obtuse
    ];
    const signatures = cLayouts.map((cXyz) => {
      const sc = buildUnderdeterminedSabcScene({ cXyz, symbolic: true });
      const disp = registerExactSceneOrigin(veKhongGian(sc), sc);
      const base = disp.objects.find((o) => o.id === "day_ABC")!;
      const prov = classifyPolygonShapeWithProvenance(disp, base);
      const plan = buildPedagogicalConstructionPlan(withSubEntities(sc));
      const givens = givenQuantitiesSummary(disp, stepCount(disp) - 1).map((g) => g.text);
      return {
        certifiedShape: prov.certifiedShape,
        polyNoun: classifyScenePolygonShape(disp, base),
        stepTitles: plan.steps.map((s) => s.title),
        givens,
      };
    });
    expect(signatures[0]).toEqual(signatures[1]);
    expect(signatures[1]).toEqual(signatures[2]);
    expect(signatures[0].givens).toEqual(["AB = 2a", "SA = 4a"]);

    // Point renaming M, N, P, K
    const renamed = buildUnderdeterminedSabcScene({ renameVertices: true, symbolic: true });
    const baseMnp = renamed.objects.find((o) => o.id === "day_MNP")!;
    expect(classifyPolygonShapeWithProvenance(renamed, baseMnp).certifiedShape).toBeNull();
    expect(classifyScenePolygonShape(renamed, baseMnp)).toBe("tam giác");

    // Camera rotation does not alter any semantic classification or mesh validity
    const camA = buildObject3D(baseMnp, false, 0.08, [], new THREE.Vector3(6, -6, 5));
    const camB = buildObject3D(baseMnp, false, 0.08, [], new THREE.Vector3(-5, 7, 2));
    expect(camA).toBeTruthy();
    expect(camB).toBeTruthy();
    expect(classifyScenePolygonShape(renamed, baseMnp)).toBe("tam giác");

    // Uncertified 4-vertex solid without BASE_REGION on regular-tetrahedron chart_metric is NOT auto-upgraded to "tứ diện đều"
    const uncertTet: Scene3D = {
      free_objects: ["A", "B", "C", "D"],
      chart_metric: [
        ["2", "1", "1"],
        ["1", "2", "1"],
        ["1", "1", "2"],
      ],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"], source: { assumption: "LAYOUT_DERIVED" } },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "0", "0"], source: { assumption: "LAYOUT_DERIVED" } },
        { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "1", "0"], source: { assumption: "LAYOUT_DERIVED" } },
        { id: "D", type: "point3", label: "D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "1"], source: { assumption: "LAYOUT_DERIVED" } },
        { id: "tet", type: "solid", label: "Tứ diện ABCD", notation: "ABCD", origin: "derived", producer: "construct_solid", render: "mesh", depends: ["A", "B", "C", "D"], vertex_ids: ["A", "B", "C", "D"], vertices: [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]], faces: [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]] },
      ],
      events: [
        { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
        { step_index: 1, action: "CREATE", object: "tet", depends: ["A", "B", "C", "D"], explanation: "Dựng tứ diện." },
      ],
    };
    const tetPlan = buildPedagogicalConstructionPlan(withSubEntities(uncertTet));
    expect(tetPlan.steps.map((s) => `${s.title} ${s.subtitle}`).join(" ")).not.toMatch(/tứ\s+diện\s+đều/iu);
  });

  it("A5. Semantic-defect oracle (§11): valid Scene3D JSON + valid Three.js rendering with false special-shape claim is caught as a semantic defect", () => {
    const validScene = (GEOMETRY_SAMPLES.find((s) => s.id === "thiet-dien-chop")!.envelope as { scene3d?: Scene3D }).scene3d as Scene3D;
    expect(hopLeScene3D(validScene)).toBe(true);
    const baseObj = validScene.objects.find((o) => o.id === "day_ABCD")!;
    expect(buildObject3D(baseObj, false)).toBeTruthy();

    // `thiet-dien-chop` `day_ABCD` has `assumption: "hệ trục do đề chọn"` and generic `Đáy ABCD`:
    // claiming `hình vuông` despite valid JSON + valid render would be a semantic defect.
    const prov = classifyPolygonShapeWithProvenance(validScene, baseObj);
    expect(prov.certifiedShape).toBeNull();
    expect(classifyScenePolygonShape(validScene, baseObj)).toBe("tứ giác");
  });
});

describe("AXO Master Continuation — Priority B: Symbolic Annotations & Quantity Provenance", () => {
  it("B1. Preserves integer, decimal, fraction, radical (OA = √5), single-param (AB = 2a, SA = 4a), multi-param (2a + b), and angle (α = 30°) expressions cleanly", () => {
    const scene: Scene3D = {
      free_objects: ["O", "S", "A", "B", "q_int", "q_dec", "q_frac", "q_rad", "q_param1", "q_param_norm", "q_multiparam", "q_angle"],
      length_unit: { symbol: "a", display_scale: "a = 1 đơn vị dựng", is_given: false },
      objects: [
        { id: "O", type: "point3", label: "O", notation: "O", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        { id: "S", type: "point3", label: "S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "1", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "3", "0"] },
        { id: "seg_oa", type: "segment3", label: "OA", notation: "OA", origin: "derived", producer: "construct_segment", render: "segment", depends: ["O", "A"], endpoint_ids: ["O", "A"], endpoints: [["0", "0", "0"], ["2", "1", "0"]] },
        { id: "seg_so", type: "segment3", label: "SO", notation: "SO", origin: "derived", producer: "construct_segment", render: "segment", depends: ["S", "O"], endpoint_ids: ["S", "O"], endpoints: [["0", "0", "4"], ["0", "0", "0"]] },
        { id: "seg_ab", type: "segment3", label: "AB", notation: "AB", origin: "derived", producer: "construct_segment", render: "segment", depends: ["A", "B"], endpoint_ids: ["A", "B"], endpoints: [["2", "1", "0"], ["0", "3", "0"]] },
        { id: "seg_ob", type: "segment3", label: "OB", notation: "OB", origin: "derived", producer: "construct_segment", render: "segment", depends: ["O", "B"], endpoint_ids: ["O", "B"], endpoints: [["0", "0", "0"], ["0", "3", "0"]] },
        { id: "seg_sa", type: "segment3", label: "SA", notation: "SA", origin: "derived", producer: "construct_segment", render: "segment", depends: ["S", "A"], endpoint_ids: ["S", "A"], endpoints: [["0", "0", "4"], ["2", "1", "0"]] },
        { id: "seg_sb", type: "segment3", label: "SB", notation: "SB", origin: "derived", producer: "construct_segment", render: "segment", depends: ["S", "B"], endpoint_ids: ["S", "B"], endpoints: [["0", "0", "4"], ["0", "3", "0"]] },
        // Radical with decimal value + exact radical
        { id: "q_rad", type: "quantity", label: "OA", notation: "OA", origin: "free", producer: null, render: "readout", depends: ["O", "A"], value: "2.2360679", exact: { kind: "radical", coefficient: "1", radicand: 5 }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["O", "A"], anchor: "segment" } },
        // Normalized numeric at a = 1 (no symbolic field) -> MUST carry scale note
        { id: "q_int", type: "quantity", label: "SO", notation: "SO", origin: "free", producer: null, render: "readout", depends: ["S", "O"], value: "4", exact: { kind: "rational", value: "4" }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["S", "O"], anchor: "segment" } },
        // Single-parameter symbolic in value -> NO scale note
        { id: "q_param1", type: "quantity", label: "AB", notation: "AB", origin: "free", producer: null, render: "readout", depends: ["A", "B"], value: "2a", annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "B"], anchor: "segment" } },
        // Symbolic field alongside normalized exact rational -> preserves symbolic "4a" without scale note
        { id: "q_param_norm", type: "quantity", label: "SA", notation: "SA", origin: "free", producer: null, render: "readout", depends: ["S", "A"], value: "4", symbolic: "4a", exact: { kind: "rational", value: "4" }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["S", "A"], anchor: "segment" } },
        // Multi-parameter symbolic
        { id: "q_multiparam", type: "quantity", label: "SB", notation: "SB", origin: "free", producer: null, render: "readout", depends: ["S", "B"], value: "2a + b", annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["S", "B"], anchor: "segment" } },
        // Fraction & Decimal scalars without length_unit test below, plus 3-point angle
        { id: "q_frac", type: "quantity", label: "OB", notation: "OB", origin: "free", producer: null, render: "readout", depends: ["O", "B"], value: "3/4", exact: { kind: "rational", value: "3/4" }, annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["O", "B"], anchor: "segment" } },
        { id: "q_dec", type: "quantity", label: "h", notation: "h", origin: "free", producer: null, render: "readout", depends: [], value: "2.5" },
        { id: "q_angle", type: "quantity", label: "Góc α", notation: "α", origin: "free", producer: null, render: "readout", depends: ["S", "A", "O"], value: "30°", annotation: { kind: "angle", category: "measurement", role: "given", subject_ids: ["S", "A", "O"], anchor: "pair" } },
      ],
      events: [
        { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
        { step_index: 1, action: "CREATE", object: "seg_oa", objects: ["seg_oa", "seg_so", "seg_ab", "seg_ob", "seg_sa", "seg_sb"], depends: ["O", "S", "A", "B"], explanation: "Segments" },
      ],
    };

    const anns = annotationsAt(scene, 1, DEFAULT_ANNOTATION_VIEW, null);
    const annTexts = new Map(anns.map((a) => [a.id, a.text]));
    expect(annTexts.get("q_rad")).toBe("OA = √5 (trên hình dựng, a = 1 đơn vị dựng)");
    expect(annTexts.get("q_int")).toBe("SO = 4 (trên hình dựng, a = 1 đơn vị dựng)");
    expect(annTexts.get("q_frac")).toBe("OB = 3/4 (trên hình dựng, a = 1 đơn vị dựng)");
    expect(annTexts.get("q_param1")).toBe("AB = 2a");
    expect(annTexts.get("q_param_norm")).toBe("SA = 4a");
    expect(annTexts.get("q_multiparam")).toBe("SB = 2a + b");
    expect(annTexts.get("q_angle")).toBe("α = 30°");

    // Angle subject_ids [S, A, O] anchors at vertex A ([2, 1, 0]), NOT at S ([0, 0, 4])
    const angleEntry = anns.find((a) => a.id === "q_angle")!;
    expect(annotationAnchor(scene, angleEntry)).toEqual([2, 1, 0]);

    // Without length_unit, OA = √5 has no scale note
    const sceneNoUnit: Scene3D = { ...scene, length_unit: undefined };
    const annsNoUnit = annotationsAt(sceneNoUnit, 1, DEFAULT_ANNOTATION_VIEW, null);
    expect(annsNoUnit.find((a) => a.id === "q_rad")?.text).toBe("OA = √5");
    expect(givenQuantitiesSummary(sceneNoUnit, 1).find((g) => g.id === "q_rad")?.text).toBe("OA = √5");
    expect(givenQuantitiesSummary(sceneNoUnit, 1).find((g) => g.id === "q_dec")?.text).toBe("h = 2.5");
    expect(hienSo(undefined, "2a")).toBe("2a");
    expect(ghiChuGiaTriDung(scene, "2a")).toBe("");
    expect(ghiChuGiaTriDung(scene, "30°", "angle")).toBe("");
    expect(ghiChuGiaTriDung(scene, "2")).toBe(" (trên hình dựng, a = 1 đơn vị dựng)");
  });

  it("B2. Blocks unverified/contradictory provenance quantities, unknown placeholders, and misbound annotations; handles collision & Desktop/Mobile DOM", () => {
    const sabcUnverified = buildUnderdeterminedSabcScene({ symbolic: false, includeUnverifiedBc: true });
    const qBc = sabcUnverified.objects.find((o) => o.id === "q_bc_unverified")!;
    expect(classifyQuantityProvenance(qBc, sabcUnverified)).toBe("UNVERIFIED");
    expect(annotationsAt(sabcUnverified, 3, DEFAULT_ANNOTATION_VIEW, null).map((a) => a.id)).not.toContain("q_bc_unverified");
    expect(givenQuantitiesSummary(sabcUnverified, 3).map((g) => g.id)).not.toContain("q_bc_unverified");

    // Contradictory quantity: origin === "derived" claiming source.provenance === "GIVEN"
    const qContradictory: SceneObject = {
      id: "q_contra",
      type: "quantity",
      label: "BC",
      notation: "BC",
      origin: "derived",
      producer: "measure.length",
      render: "readout",
      depends: ["B", "C"],
      value: "5",
      source: { fact_id: "f_fake", instruction: "measure.length" },
      annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["B", "C"], anchor: "segment" },
    };
    expect(classifyQuantityProvenance(qContradictory, sabcUnverified)).toBe("UNVERIFIED");

    // Unknown placeholders & misbound subject_ids
    const edgeCaseScene = buildUnderdeterminedSabcScene({ symbolic: true });
    edgeCaseScene.free_objects.push("q_unknown", "q_dup_pts", "q_missing_subj", "q_solid_as_seg");
    edgeCaseScene.objects.push(
      { id: "q_unknown", type: "quantity", label: "Chưa biết", notation: "BC", origin: "free", producer: null, render: "readout", depends: ["B", "C"], value: "?", annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["B", "C"], anchor: "segment" } },
      { id: "q_dup_pts", type: "quantity", label: " Trùng đỉnh", notation: "AA", origin: "free", producer: null, render: "readout", depends: ["A"], value: "3a", annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "A"], anchor: "segment" } },
      { id: "q_missing_subj", type: "quantity", label: "Sai ID", notation: "AX", origin: "free", producer: null, render: "readout", depends: ["A"], value: "5a", annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "NO_SUCH_POINT"], anchor: "segment" } },
      { id: "q_solid_as_seg", type: "quantity", label: "Sai kiểu neo", notation: "AS", origin: "free", producer: null, render: "readout", depends: ["A"], value: "6a", annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "khoi_sabc"], anchor: "segment" } },
    );
    const filteredAnns = annotationsAt(edgeCaseScene, 3, DEFAULT_ANNOTATION_VIEW, null);
    expect(filteredAnns.map((a) => a.text)).toEqual(["AB = 2a", "SA = 4a"]);
    const filteredSummary = givenQuantitiesSummary(edgeCaseScene, 3);
    expect(filteredSummary.map((g) => g.text)).toEqual(["AB = 2a", "SA = 4a"]);

    // Label collision deterministic placement
    const placed = placeAnnotationLabels(
      [
        { id: "l1", ax: 200, ay: 200, w: 64, h: 22, priority: 2 },
        { id: "l2", ax: 200, ay: 200, w: 64, h: 22, priority: 1 },
      ],
      [{ x: 190, y: 168, w: 24, h: 18 }],
      { w: 390, h: 844 },
    );
    expect(placed.size).toBe(2);
    const r1 = placed.get("l1")!;
    const r2 = placed.get("l2")!;
    const overlap =
      r1.x < r2.x + r2.w && r2.x < r1.x + r1.w && r1.y < r2.y + r2.h && r2.y < r1.y + r1.h;
    expect(overlap).toBe(false);

    // Desktop & Mobile AxoWorkspaceV62 SSR/DOM renders given banner without "(trên hình dựng, a = 1 đơn vị dựng)"
    const html = renderToString(
      <AxoWorkspaceV62
        scene={buildUnderdeterminedSabcScene({ symbolic: true })}
        tieuDe="Hình chóp S.ABC"
        de="Cho hình chóp S.ABC có SA ⊥ (ABC), AB = 2a, SA = 4a."
      />,
    );
    expect(html).toContain("id=\"dock-given-params\"");
    expect(html).toContain("AB = 2a");
    expect(html).toContain("SA = 4a");
    expect(html).not.toContain("a = 1 đơn vị dựng");
  });
});

describe("AXO Master Continuation — Priority C, D, E: Planes, Sections, Sphere Equator & Cross-Family Sequencing", () => {
  it("C1. Sphere reference equator is visually subordinated (muted slate 0.46/0.28, front-solid/back-dashed, 0.75x rim width) below terracotta RESULT_SECTION circle while preserving 3D curvature depth", () => {
    const standalone = (GEOMETRY_SAMPLES.find((s) => s.id === "cau-the-tich")!.envelope as { scene3d?: Scene3D }).scene3d as Scene3D;
    const standaloneBall = standalone.objects.find((o) => o.curved_kind === "ball")!;
    expect(shouldShowSphereReferenceEquator(standalone, standaloneBall, false, standalone.objects)).toBe(true);
    const standaloneMesh = buildObject3D(standaloneBall, false, 0.08, [], new THREE.Vector3(8, -8, 6))!;
    const eqNode = standaloneMesh.getObjectByName(`sphere_reference:${standaloneBall.id}`)!;
    expect(eqNode).toBeTruthy();
    const eqRim = eqNode.userData.curvedRimLoop;
    expect(eqRim.thayMesh.material.color.getHex()).toBe(0x475569);
    expect(eqRim.thayMesh.material.opacity).toBeLessThan(0.6);
    expect(eqRim.khuatMesh.material.opacity).toBeLessThan(0.35);
    expect(eqRim.selfOccludingSphere).toBeDefined();

    const sphereCut = (GEOMETRY_SAMPLES.find((s) => s.id === "cau-cat-mat-phang")!.envelope as { scene3d?: Scene3D }).scene3d as Scene3D;
    const cutBall = sphereCut.objects.find((o) => o.curved_kind === "ball")!;
    const cutCircle = sphereCut.objects.find((o) => o.type === "circle3")!;
    const finalVis = objectsAt(sphereCut, stepCount(sphereCut) - 1);
    expect(shouldShowSphereReferenceEquator(sphereCut, cutBall, false, finalVis)).toBe(true);
    expect(shouldShowSphereReferenceEquator(sphereCut, cutBall, true, finalVis)).toBe(true);
    const cutMesh = buildObject3D(
      cutCircle,
      false,
      0.08,
      [],
      new THREE.Vector3(8, -8, 6),
      new Set(),
      new Map(),
      false,
      "primary",
      true,
      true,
      false,
      sphereCut,
    )!;
    const cutRim = cutMesh.userData.curvedRimLoop;
    expect(cutRim.thayMesh.material.color.getHex()).toBe(0xc85a32);
    expect(cutRim.thayMesh.material.opacity).toBeGreaterThan(eqRim.thayMesh.material.opacity);
  });

  it("C2. Retires circumscribed-sphere perpendicular-bisector scaffold planes/lines at final sphere step and keeps Step 15 narration clean", () => {
    const circumSphereScene: Scene3D = {
      free_objects: ["A", "B", "C", "D", "S"],
      length_unit: { symbol: "a", display_scale: "a = 1 đơn vị dựng", is_given: false },
      chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
      objects: [
        { id: "A", type: "point3", label: "Điểm A", notation: "A", role: "Điểm", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"], source: { assumption: "LAYOUT_DERIVED" } },
        { id: "B", type: "point3", label: "Điểm B", notation: "B", role: "Điểm", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"], source: { assumption: "LAYOUT_DERIVED" } },
        { id: "C", type: "point3", label: "Điểm C", notation: "C", role: "Điểm", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "2", "0"], source: { assumption: "LAYOUT_DERIVED" } },
        { id: "D", type: "point3", label: "Điểm D", notation: "D", role: "Điểm", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"], source: { assumption: "LAYOUT_DERIVED" } },
        { id: "S", type: "point3", label: "Điểm S", notation: "S", role: "Điểm", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"], source: { assumption: "LAYOUT_DERIVED" } },
        { id: "day_ABCD", type: "polygon3", label: "Hình vuông đáy ABCD", notation: "ABCD", role: "Hình vuông A, B, C, D", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", depends: ["A", "B", "C", "D"], vertex_ids: ["A", "B", "C", "D"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]] },
        { id: "khoi_S_ABCD", type: "solid", label: "Hình chóp S.ABCD", notation: "S.ABCD", role: "Đỉnh S, đáy ABCD", origin: "derived", producer: "construct_solid", render: "mesh", depends: ["S", "A", "B", "C", "D"], vertex_ids: ["S", "A", "B", "C", "D"], vertices: [["0", "0", "4"], ["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]] },
        { id: "td_1", type: "point3", label: "Trung điểm của A và B", notation: null, role: "Điểm dựng phụ", origin: "derived", producer: "construct_point.midpoint", render: "point_marker", depends: ["A", "B"], xyz: ["1", "0", "0"] },
        { id: "dt_1", type: "line3", label: "Đường thẳng qua A và B", notation: "AB", role: "Đường thẳng", origin: "derived", producer: "construct_line", render: "line", depends: ["A", "B"], point: ["0", "0", "0"], direction: ["2", "0", "0"] },
        { id: "mp_1", type: "plane3", label: "Mặt phẳng qua «Trung điểm của A và B» và vuông góc với AB", notation: "(α)", role: "Mặt phẳng", origin: "derived", producer: "plane_perpendicular_to_line", render: "surface", depends: ["td_1", "dt_1"], point: ["1", "0", "0"], normal: ["2", "0", "0"] },
        { id: "td_2", type: "point3", label: "Trung điểm của A và C", notation: null, role: "Điểm dựng phụ", origin: "derived", producer: "construct_point.midpoint", render: "point_marker", depends: ["A", "C"], xyz: ["1", "1", "0"] },
        { id: "dt_2", type: "line3", label: "Đường thẳng qua A và C", notation: "AC", role: "Đường thẳng", origin: "derived", producer: "construct_line", render: "line", depends: ["A", "C"], point: ["0", "0", "0"], direction: ["2", "2", "0"] },
        { id: "mp_2", type: "plane3", label: "Mặt phẳng qua «Trung điểm của A và C» và vuông góc với AC", notation: "(β)", role: "Mặt phẳng", origin: "derived", producer: "plane_perpendicular_to_line", render: "surface", depends: ["td_2", "dt_2"], point: ["1", "1", "0"], normal: ["2", "2", "0"] },
        { id: "td_3", type: "point3", label: "Trung điểm của A và S", notation: null, role: "Điểm dựng phụ", origin: "derived", producer: "construct_point.midpoint", render: "point_marker", depends: ["A", "S"], xyz: ["0", "0", "2"] },
        { id: "dt_3", type: "line3", label: "Đường thẳng qua A và S", notation: "AS", role: "Đường thẳng", origin: "derived", producer: "construct_line", render: "line", depends: ["A", "S"], point: ["0", "0", "0"], direction: ["0", "0", "4"] },
        { id: "mp_3", type: "plane3", label: "Mặt phẳng qua «Trung điểm của A và S» và vuông góc với AS", notation: "(γ)", role: "Mặt phẳng", origin: "derived", producer: "plane_perpendicular_to_line", render: "surface", depends: ["td_3", "dt_3"], point: ["0", "0", "2"], normal: ["0", "0", "4"] },
        { id: "truc_cau", type: "line3", label: "Giao tuyến của (α) và (β)", notation: null, role: "Đường thẳng", origin: "derived", producer: "intersect_plane_plane", render: "line", depends: ["mp_1", "mp_2"], point: ["1", "1", "0"], direction: ["0", "0", "1"] },
        { id: "tam_cau", type: "point3", label: "Giao điểm của «Giao tuyến của (α) và (β)» và (γ)", notation: null, role: "Điểm dựng phụ", origin: "derived", producer: "construct_point.intersect_line_plane", render: "point_marker", depends: ["truc_cau", "mp_3"], xyz: ["1", "1", "2"] },
        { id: "mat_cau", type: "curved_solid", label: "Mặt cầu ngoại tiếp S.ABCD", notation: null, role: "Khối cầu tâm I, đi qua A", origin: "derived", producer: "construct_curved_solid.ball", render: "curved_solid", depends: ["tam_cau", "A"], curved_kind: "ball", anchor: ["1", "1", "2"], radius_sq: "6" },
        { id: "kq_v", type: "quantity", label: "Thể tích khối cầu ngoại tiếp S.ABCD", notation: null, role: "Kết quả cuối", origin: "derived", producer: "measure.volume", render: "readout", depends: ["mat_cau"], value: "8π√6", exact: { kind: "radical", coefficient: "8", radicand: 6, pi: 1 } },
      ],
      events: [
        { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
        { step_index: 1, action: "CREATE", object: "day_ABCD", depends: ["A", "B", "C", "D"], explanation: "Base" },
        { step_index: 2, action: "CREATE", object: "khoi_S_ABCD", depends: ["S", "A", "B", "C", "D"], explanation: "Solid" },
        { step_index: 3, action: "CREATE", object: "td_1", depends: ["A", "B"], explanation: "M1" },
        { step_index: 4, action: "CREATE", object: "dt_1", depends: ["A", "B"], explanation: "L1" },
        { step_index: 5, action: "CREATE", object: "mp_1", depends: ["td_1", "dt_1"], explanation: "P1" },
        { step_index: 6, action: "CREATE", object: "td_2", depends: ["A", "C"], explanation: "M2" },
        { step_index: 7, action: "CREATE", object: "dt_2", depends: ["A", "C"], explanation: "L2" },
        { step_index: 8, action: "CREATE", object: "mp_2", depends: ["td_2", "dt_2"], explanation: "P2" },
        { step_index: 9, action: "CREATE", object: "td_3", depends: ["A", "S"], explanation: "M3" },
        { step_index: 10, action: "CREATE", object: "dt_3", depends: ["A", "S"], explanation: "L3" },
        { step_index: 11, action: "CREATE", object: "mp_3", depends: ["td_3", "dt_3"], explanation: "P3" },
        { step_index: 12, action: "CREATE", object: "truc_cau", depends: ["mp_1", "mp_2"], explanation: "Axis" },
        { step_index: 13, action: "CREATE", object: "tam_cau", depends: ["truc_cau", "mp_3"], explanation: "Center" },
        { step_index: 14, action: "CREATE", object: "mat_cau", depends: ["tam_cau", "A"], explanation: "Sphere" },
        { step_index: 15, action: "MEASURE", object: "kq_v", depends: ["mat_cau"], semantic_kind: "FINAL_RESULT", explanation: "Volume" },
      ],
    };

    const plan = buildPedagogicalConstructionPlan(withSubEntities(circumSphereScene));
    const finalAnchor = plan.steps[plan.steps.length - 1]!.anchor;
    const auxMap = auxiliaryObjects(plan.scene);
    expect(auxMap.has("mp_1")).toBe(true);
    expect(auxMap.has("mp_2")).toBe(true);
    expect(auxMap.has("mp_3")).toBe(true);
    expect(auxMap.has("truc_cau")).toBe(true);

    const hiddenAtFinal = auxiliaryHiddenAt(plan.scene, finalAnchor, false, null);
    expect(hiddenAtFinal.has("mp_1")).toBe(true);
    expect(hiddenAtFinal.has("mp_2")).toBe(true);
    expect(hiddenAtFinal.has("mp_3")).toBe(true);
    expect(hiddenAtFinal.has("truc_cau")).toBe(true);
    expect(auxiliaryHiddenAt(plan.scene, finalAnchor, true, null).size).toBe(0);

    const mp1Obj = plan.scene.objects.find((o) => o.id === "mp_1")!;
    expect(resolvePlaneSectionVisibility(plan.scene, mp1Obj, finalAnchor, false, null).visible).toBe(false);
    expect(resolvePlaneSectionVisibility(plan.scene, mp1Obj, finalAnchor, true, null).visible).toBe(true);

    const lastStep = plan.steps[plan.steps.length - 1]!;
    expect(`${lastStep.title} ${lastStep.subtitle}`).not.toMatch(/[«»]/u);
    expect(`${lastStep.title} ${lastStep.subtitle}`).not.toContain("R = Giao điểm");

    // BLOCKER-3 regressions:
    // 1. Primary chip must NEVER say `Mặt cầu (A)` (which falsely means centered at rim vertex A!)
    const sphereObj = plan.scene.objects.find((o) => o.id === "mat_cau")!;
    expect(formatCompactEntityChipLabel(plan.scene, sphereObj)).toBe("Mặt cầu ngoại tiếp");
    // 2. Absorbed scaffold planes (α), (β), (γ) must NEVER be referenced in learner steps when folded,
    //    and unlabelled `tam_cau` (`notation: null`) must NEVER invent `"tâm I"` in Step 8 when no `I` exists on canvas!
    const allStepsText = plan.steps.map((s) => `${s.title} ${s.subtitle}`).join(" | ");
    expect(allStepsText).not.toMatch(/\([αβγ]\)/u);
    expect(allStepsText).not.toMatch(/\btâm\s+I\b/u);
  });

  it("AR-1 (BLOCKER-1): Triangle altitude projection `AH ⊥ BC` NEVER falsely promotes base `ABC` to `tam giác vuông` AND NEVER triggers false `CONTRADICTORY_OR_UNSUPPORTED` on acute/scalene triangles", () => {
    // Case 1: Illustrative right coordinates (0,0,0)-(2,0,0)-(0,2,0) with uncertified base + altitude H = proj(A, BC)
    const rightCoordsWithAltitude = buildUnderdeterminedSabcScene({ symbolic: false });
    rightCoordsWithAltitude.objects.push(
      {
        id: "line_BC",
        type: "line3",
        label: "Đường thẳng BC",
        notation: "BC",
        origin: "derived",
        producer: "construct_line",
        render: "line",
        depends: ["B", "C"],
        point: ["2", "0", "0"],
        direction: ["-2", "2", "0"],
      },
      {
        id: "H",
        type: "point3",
        label: "Điểm H",
        notation: "H",
        origin: "derived",
        producer: "construct_foot",
        render: "point_marker",
        depends: ["A", "line_BC"],
        xyz: ["1", "1", "0"],
        perpendicular_witness: {
          from: "A",
          foot: ["1", "1", "0"],
          on: "line_BC",
          marker: { u: ["-1", "-1", "0"], v: ["1", "-1", "0"] },
        },
      },
    );
    const baseRight = rightCoordsWithAltitude.objects.find((o) => o.id === "day_ABC")!;
    // Even if `day_ABC` has no `LAYOUT_DERIVED` tag (e.g. legacy generic source), altitude `AH ⊥ BC` is NOT a right angle of △ABC!
    baseRight.source = { instruction: "construct_polygon" };
    const prov1 = classifyPolygonShapeWithProvenance(rightCoordsWithAltitude, baseRight);
    expect(prov1.certifiedShape).toBeNull();
    expect(prov1.provenance).not.toBe("DERIVED_VERIFIED");
    expect(classifyScenePolygonShape(rightCoordsWithAltitude, baseRight)).toBe("tam giác");

    // Case 2: Valid scalene/acute triangle A=(0,0,0), B=(4,0,0), C=(1,3,0) with altitude H = proj(A, BC)
    const acuteScene: Scene3D = {
      free_objects: ["A", "B", "C"],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["4", "0", "0"] },
        { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "3", "0"] },
        { id: "day_ABC", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "free", producer: null, render: "surface", surface_role: "BASE_REGION", depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["4", "0", "0"], ["1", "3", "0"]] },
        { id: "line_BC", type: "line3", label: "BC", notation: "BC", origin: "derived", producer: "construct_line", render: "line", depends: ["B", "C"], point: ["4", "0", "0"], direction: ["-3", "3", "0"] },
        {
          id: "H",
          type: "point3",
          label: "H",
          notation: "H",
          origin: "derived",
          producer: "construct_foot",
          render: "point_marker",
          depends: ["A", "line_BC"],
          xyz: ["2", "2", "0"],
          perpendicular_witness: { from: "A", foot: ["2", "2", "0"], on: "line_BC", marker: { u: ["-2", "-2", "0"], v: ["2", "-2", "0"] } },
        },
      ],
      events: [{ step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" }],
    };
    const acuteBase = acuteScene.objects.find((o) => o.id === "day_ABC")!;
    const prov2 = classifyPolygonShapeWithProvenance(acuteScene, acuteBase);
    expect(prov2.provenance).not.toBe("CONTRADICTORY_OR_UNSUPPORTED");
    expect(prov2.certifiedShape).toBeNull();
  });

  it("AR-2 (BLOCKER-2): Partial single-vertex or lateral-line `source_provenance` NEVER certifies or contradicts base `ABC`", () => {
    const s = buildUnderdeterminedSabcScene({ symbolic: false });
    const baseObj = s.objects.find((o) => o.id === "day_ABC")!;
    attachHybridViewToScene(s, {
      source_provenance: [
        { kind: "right_angle", vertex: "A", line: "SA", verified: true },
        { id: "p_lat", fn: "perpendicular_lines", args: { line1: ["A", "B"], line2_ref: "d_lat" }, quotes: ["d ⊥ AB"] },
      ],
    });
    const prov = classifyPolygonShapeWithProvenance(s, baseObj);
    expect(prov.certifiedShape).toBeNull();
    expect(prov.provenance).not.toBe("GIVEN");
    expect(prov.provenance).not.toBe("CONTRADICTORY_OR_UNSUPPORTED");
  });

  it("AR-3 (MAJOR-1, MAJOR-2, BLOCKER-3, MINOR-1): Preserves `symbolic` in Object Inspector without `a = 1 đơn vị dựng`, avoids `Đường tròn (P)` collision & `Mặt phẳng cho bằng phương trình` leak, and prevents uncertified free sphere promotion", () => {
    // 1. Object Inspector preserves `symbolic: "2a"` without `(trên hình dựng, a = 1 đơn vị dựng)`
    const symScene = buildUnderdeterminedSabcScene({ symbolic: true });
    // Simulate Hybrid normalized numeric value `"2"` with `symbolic: "2a"`
    const qAb = symScene.objects.find((o) => o.id === "q_ab_2a")!;
    qAb.value = "2";
    qAb.exact = { kind: "rational", value: "2" };
    qAb.symbolic = "2a";
    const inspectorHtml = renderToString(
      <AxoWorkspaceV62 scene={symScene} de="Cho hình chóp S.ABC có AB = 2a, SA = 4a." initialSelectedId="q_ab_2a" />,
    );
    expect(inspectorHtml).toContain("AB = 2a");
    expect(inspectorHtml).not.toContain("đơn vị dựng");

    // 2. Sphere-cut (`cau-cat-mat-phang`): no `Đường tròn (P)` collision, no `Mặt phẳng cho bằng phương trình`, no uncertified `(S)` when `notation: null`
    const sphereCut = (GEOMETRY_SAMPLES.find((x) => x.id === "cau-cat-mat-phang")!.envelope as { scene3d?: Scene3D }).scene3d as Scene3D;
    const cutPlan = buildPedagogicalConstructionPlan(withSubEntities(sphereCut));
    const cutCircle = cutPlan.scene.objects.find((o) => o.type === "circle3")!;
    const circleChip = formatCompactEntityChipLabel(cutPlan.scene, cutCircle);
    expect(circleChip).not.toBe("Đường tròn (P)");
    expect(cutPlan.steps[0]!.title).not.toContain("(S)");
    expect(cutPlan.steps.map((st) => `${st.title} ${st.subtitle} ${st.premise}`).join(" ")).not.toMatch(/phương\s+trình/iu);

    // 3. Free standalone sphere that happens to pass through 4 points is NOT promoted to `CIRCUMSCRIBED_SPHERE` without derived lineage
    const coincidentalFreeSphere: Scene3D = {
      free_objects: ["A", "B", "C", "D", "sp_free"],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["-1", "0", "0"] },
        { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "1", "0"] },
        { id: "D", type: "point3", label: "D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "1"] },
        { id: "tet", type: "solid", label: "Tứ diện", notation: "ABCD", origin: "derived", producer: "construct_solid", render: "mesh", depends: ["A", "B", "C", "D"], vertices: [["1", "0", "0"], ["-1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]], faces: [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]] },
        { id: "sp_free", type: "curved_solid", label: "Mặt cầu", notation: null, origin: "free", producer: null, render: "curved_solid", depends: [], curved_kind: "ball", anchor: ["0", "0", "0"], radius_sq: "1" },
      ],
      events: [{ step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" }],
    };
    expect(classifySphereSemanticRole(coincidentalFreeSphere, coincidentalFreeSphere.objects[5]!)).toBe("STANDALONE_SPHERE");
  });

  it("D1/E1. Audits all GEOMETRY_SAMPLES across pyramid, prism, cylinder, cone, sphere & relations for zero calculation-only steps and zero answer leaks", () => {
    expect(GEOMETRY_SAMPLES.length).toBeGreaterThanOrEqual(8);
    for (const sample of GEOMETRY_SAMPLES) {
      const sampleScene = (sample.envelope as { scene3d?: Scene3D }).scene3d as Scene3D;
      const plan = buildPedagogicalConstructionPlan(withSubEntities(sampleScene));
      expect(plan.steps.length).toBeGreaterThan(0);
      for (const st of plan.steps) {
        expect(`${st.title} ${st.subtitle}`).not.toMatch(/[«»]/u);
        // No step exists solely to present a numeric answer
        const stepEvents = plan.scene.events.slice(st.startAnchor, st.anchor + 1);
        const hasGeometricAction = stepEvents.some((ev) => ev.action !== "MEASURE");
        expect(hasGeometricAction).toBe(true);
      }
      // Default annotations at final step never expose `result` role quantities
      const defaultAnns = annotationsAt(plan.scene, plan.steps[plan.steps.length - 1]!.anchor, DEFAULT_ANNOTATION_VIEW, null);
      expect(defaultAnns.every((a) => a.role === "given")).toBe(true);
    }
  });
});
