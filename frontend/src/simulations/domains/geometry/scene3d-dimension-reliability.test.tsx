import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import type { Scene3D, SceneObject } from "./scene3d-model";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { veKhongGian } from "./scene3d-chart";
import { withSubEntities } from "./scene3d-subentities";
import { buildPedagogicalConstructionPlan } from "./scene3d-semantic-policy";
import {
  annotationsAt,
  annotationAnchor,
  classifyQuantityProvenance,
  DEFAULT_ANNOTATION_VIEW,
  givenQuantitiesSummary,
  placeAnnotationLabels,
} from "./scene3d-annotations";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";

function pt(id: string, xyz: [string, string, string], label = `Điểm ${id}`): SceneObject {
  return {
    id,
    label,
    notation: id.replace(/_prime$/, "′"),
    type: "point3",
    render: "point_marker",
    origin: "free",
    producer: null,
    depends: [],
    xyz,
  } as SceneObject;
}

function buildSphereGivenIAScene(opts?: {
  centerId?: string;
  rimId?: string;
  reversedSubjectOrder?: boolean;
  omitFromFreeObjects?: boolean;
  givenAsNumericalRadiusEdgeOnly?: boolean;
  value?: string;
  radiusSq?: string;
  rimX?: string;
}): Scene3D {
  const cId = opts?.centerId ?? "I";
  const rId = opts?.rimId ?? "A";
  const val = opts?.value ?? "3";
  const rSq = opts?.radiusSq ?? "9";
  const rimX = opts?.rimX ?? "3";
  const segLabel = opts?.reversedSubjectOrder ? `${rId}${cId}` : `${cId}${rId}`;
  const subj = opts?.reversedSubjectOrder ? [rId, cId] : [cId, rId];

  const qObj: SceneObject = opts?.givenAsNumericalRadiusEdgeOnly
    ? ({
        id: "R_given",
        label: "Bán kính R",
        notation: "R",
        type: "quantity",
        render: "readout",
        origin: "free",
        producer: null,
        depends: [],
        value: val,
        exact: { kind: "rational", value: val },
        source: { fact_id: "f_ia", provenance: "GIVEN", is_given: true },
      } as unknown as SceneObject)
    : ({
        id: `given_len_${cId}_${rId}`,
        label: `Độ dài ${segLabel}`,
        notation: segLabel,
        type: "quantity",
        render: "readout",
        origin: "free",
        producer: null,
        depends: [cId, rId],
        value: val,
        exact: { kind: "rational", value: val },
        source: { fact_id: "f_ia", provenance: "GIVEN", is_given: true },
        annotation: {
          kind: "length",
          category: "measurement",
          role: "given",
          subject_ids: subj,
          anchor: "segment",
        },
      } as unknown as SceneObject);

  const sphereObj: SceneObject = {
    id: "cau",
    label: `Mặt cầu tâm ${cId} đi qua ${rId}`,
    notation: "(S)",
    type: "curved_solid",
    curved_kind: "ball",
    render: "curved_solid",
    origin: "derived",
    producer: "construct_sphere",
    depends: opts?.givenAsNumericalRadiusEdgeOnly ? [cId, rId, qObj.id] : [cId, rId],
    ...(opts?.givenAsNumericalRadiusEdgeOnly
      ? { dependency_edges: [{ source_id: qObj.id, relation: "numerical" as const }] }
      : {}),
    anchor: ["0", "0", "0"],
    rim_point: [rimX, "0", "0"],
    radius_sq: rSq,
  } as unknown as SceneObject;

  const rResult: SceneObject = {
    id: "R_ans",
    label: "Bán kính mặt cầu",
    notation: "R",
    type: "quantity",
    render: "readout",
    origin: "derived",
    producer: "measure.radius",
    depends: ["cau"],
    value: val,
    exact: { kind: "rational", value: val },
    annotation: {
      kind: "length",
      category: "result",
      role: "result",
      subject_ids: ["cau"],
      anchor: "solid",
    },
  } as unknown as SceneObject;

  const vResult: SceneObject = {
    id: "V_ans",
    label: "Thể tích khối cầu",
    notation: "V",
    type: "quantity",
    render: "readout",
    origin: "derived",
    producer: "measure.volume",
    depends: ["cau"],
    value: "36π",
    exact: { kind: "pi_multiple", coefficient: "36" },
    annotation: {
      kind: "volume",
      category: "result",
      role: "result",
      subject_ids: ["cau"],
      anchor: "solid",
    },
  } as unknown as SceneObject;

  return {
    free_objects: opts?.omitFromFreeObjects ? [cId, rId] : [cId, rId, qObj.id],
    objects: [pt(cId, ["0", "0", "0"]), pt(rId, [rimX, "0", "0"]), qObj, sphereObj, rResult, vResult],
    events: [
      { step_index: 0, action: "CREATE", object: "cau", depends: [cId, rId], explanation: "Dựng mặt cầu.", semantic_kind: "GEOMETRY_CONSTRUCTION" },
      { step_index: 1, action: "MEASURE", object: "R_ans", depends: ["cau"], explanation: "Bán kính.", semantic_kind: "FINAL_RESULT" },
      { step_index: 2, action: "MEASURE", object: "V_ans", depends: ["cau"], explanation: "Thể tích.", semantic_kind: "FINAL_RESULT" },
    ],
    formation: {
      steps: [
        { step_index: 0, semantic_kind: "GEOMETRY_CONSTRUCTION", visible_ids: [cId, rId, "cau"], readout_ids: opts?.omitFromFreeObjects ? [] : [qObj.id] },
        { step_index: 1, semantic_kind: "FINAL_RESULT", visible_ids: [cId, rId, "cau"], readout_ids: ["R_ans"] },
        { step_index: 2, semantic_kind: "FINAL_RESULT", visible_ids: [cId, rId, "cau"], readout_ids: ["R_ans", "V_ans"] },
      ],
    },
  } as unknown as Scene3D;
}

describe("AXO Master Frontend §3–§4: Universal Given-Dimension Reliability & Epistemic Invariants", () => {
  it("1. Sphere IA = 3 displays at Step 1 (foundation radius IA) AND Step 2, never leaks V = 36π, and survives omitFromFreeObjects after curved foundation expansion", () => {
    const raw = buildSphereGivenIAScene({ omitFromFreeObjects: true });
    const plan = buildPedagogicalConstructionPlan(withSubEntities(raw));
    const scene = veKhongGian(plan.scene);
    expect(plan.steps.length).toBe(1);

    // Cohesive Step 1 (`I -> IA -> mặt cầu`): segment IA (`cau__radius`) + sphere are present -> `IA = 3` MUST be visible and `V = 36π` / `R_ans` NEVER leak!
    const step1Anns = annotationsAt(scene, plan.steps[0].anchor, DEFAULT_ANNOTATION_VIEW, null);
    expect(step1Anns.map((a) => a.text)).toEqual(["IA = 3"]);
    const anchor1 = annotationAnchor(scene, step1Anns[0]);
    expect(anchor1).not.toBeNull();

    // Stepping backward Step 2 -> Step 1 preserves exact determinism without duplicating badges
    const backStep1Anns = annotationsAt(scene, plan.steps[0].anchor, DEFAULT_ANNOTATION_VIEW, null);
    expect(backStep1Anns).toEqual(step1Anns);
  });

  it("2. Sphere IA = 3 adversarial variants: renamed vertices (OP = 5), reversed endpoints ([A, I] -> AI = 3), and numerical radius edge binding (R = 3 on cau with rim A)", () => {
    // Renamed vertices O, P
    const opPlan = buildPedagogicalConstructionPlan(
      withSubEntities(buildSphereGivenIAScene({ centerId: "O", rimId: "P", value: "5", radiusSq: "25", rimX: "5" })),
    );
    const opStep1 = annotationsAt(veKhongGian(opPlan.scene), opPlan.steps[0].anchor, DEFAULT_ANNOTATION_VIEW, null);
    expect(opStep1.map((a) => a.text)).toEqual(["OP = 5"]);

    // Reversed endpoint order [A, I]
    const revPlan = buildPedagogicalConstructionPlan(
      withSubEntities(buildSphereGivenIAScene({ reversedSubjectOrder: true })),
    );
    const revStep1 = annotationsAt(veKhongGian(revPlan.scene), revPlan.steps[0].anchor, DEFAULT_ANNOTATION_VIEW, null);
    expect(revStep1.map((a) => a.text)).toEqual(["AI = 3"]);

    // Numerical dependency_edge `R_given = 3` on `cau` (exact R² === radius_sq = 9) resolves to foundation radius segment `[I, A]` at Step 1!
    const numPlan = buildPedagogicalConstructionPlan(
      withSubEntities(buildSphereGivenIAScene({ givenAsNumericalRadiusEdgeOnly: true, omitFromFreeObjects: true })),
    );
    const numStep1 = annotationsAt(veKhongGian(numPlan.scene), numPlan.steps[0].anchor, DEFAULT_ANNOTATION_VIEW, null);
    expect(numStep1.map((a) => a.text)).toEqual(["R = 3"]);
    expect(numStep1[0].anchor).toBe("segment");
    expect(new Set(numStep1[0].subject_ids)).toEqual(new Set(["I", "A"]));
  });

  it("3. Catalog curved solids (`cau-cat-mat-phang` R = 5 and `tru-thiet-dien-tron` R = 2) bind structurally verified GIVEN radius from Step 1 without variable-name guessing", () => {
    const cauCutSample = GEOMETRY_SAMPLES.find((s) => s.id === "cau-cat-mat-phang")!;
    const cauCutPlan = buildPedagogicalConstructionPlan(
      withSubEntities((cauCutSample.envelope as unknown as { scene3d: Scene3D }).scene3d),
    );
    const cauCutScene = veKhongGian(cauCutPlan.scene);
    const cauStep1 = annotationsAt(cauCutScene, cauCutPlan.steps[0].anchor, DEFAULT_ANNOTATION_VIEW, null);
    expect(givenQuantitiesSummary(cauCutScene, cauCutPlan.steps[0].anchor).some((g) => g.text.includes("R = 5"))).toBe(true);
    expect(cauStep1.some((a) => a.anchor === "solid")).toBe(false);
    const cauStep4 = annotationsAt(cauCutScene, cauCutPlan.steps[3].anchor, DEFAULT_ANNOTATION_VIEW, null);
    expect(cauStep4.map((a) => a.text)).toContain("R = 5");
    expect(annotationAnchor(cauCutScene, cauStep4.find((a) => a.text === "R = 5")!)).not.toBeNull();

    const truCutSample = GEOMETRY_SAMPLES.find((s) => s.id === "tru-thiet-dien-tron")!;
    const truCutPlan = buildPedagogicalConstructionPlan(
      withSubEntities((truCutSample.envelope as unknown as { scene3d: Scene3D }).scene3d),
    );
    const truCutScene = veKhongGian(truCutPlan.scene);
    // At Step 1 (`tru__base_bot`), `tru` is not yet created until Step 3, yet `R = 2` MUST already anchor to `tru__base_bot`!
    const truStep1 = annotationsAt(truCutScene, truCutPlan.steps[0].anchor, DEFAULT_ANNOTATION_VIEW, null);
    expect(truStep1.map((a) => a.text)).toContain("R = 2");
    expect(annotationAnchor(truCutScene, truStep1[0])).not.toBeNull();
  });

  it("4. Strict epistemic guard: `cau-the-tich` derived R and V = 36π are NEVER promoted to GIVEN; unattached free scalar without structural link never guesses subject", () => {
    const cauVolSample = GEOMETRY_SAMPLES.find((s) => s.id === "cau-the-tich")!;
    const cauVolPlan = buildPedagogicalConstructionPlan(
      withSubEntities((cauVolSample.envelope as unknown as { scene3d: Scene3D }).scene3d),
    );
    const cauVolScene = veKhongGian(cauVolPlan.scene);
    for (const q of cauVolScene.objects.filter((o) => o.type === "quantity")) {
      expect(classifyQuantityProvenance(q)).toBe("CERTIFIED_DERIVED");
    }
    for (const st of cauVolPlan.steps) {
      expect(annotationsAt(cauVolScene, st.anchor, DEFAULT_ANNOTATION_VIEW, null)).toEqual([]);
    }
  });

  it("5. Deduplicates multiple quantities sharing the same geometric subject (no duplicate badges on IA/AI)", () => {
    const raw = buildSphereGivenIAScene();
    raw.objects.push({
      id: "dup_len_A_I",
      label: "Độ dài AI",
      notation: "AI",
      type: "quantity",
      render: "readout",
      origin: "free",
      producer: null,
      depends: ["A", "I"],
      value: "3",
      exact: { kind: "rational", value: "3" },
      source: { provenance: "GIVEN", is_given: true },
      annotation: {
        kind: "length",
        category: "measurement",
        role: "given",
        subject_ids: ["A", "I"],
        anchor: "segment",
      },
    } as unknown as SceneObject);
    raw.free_objects.push("dup_len_A_I");
    const plan = buildPedagogicalConstructionPlan(withSubEntities(raw));
    const anns = annotationsAt(veKhongGian(plan.scene), plan.steps[0].anchor, DEFAULT_ANNOTATION_VIEW, null);
    expect(anns).toHaveLength(1);
  });

  it("6. Cross-family GIVEN dimensions (pyramid AB=2 SA=4, cone SO=4 OA=3, right cylinder IJ=3 IK=√5, oblique cylinder OO′=3 OA=√5, prism AB=6 AA′=5) + narrow viewport Study Dock guarantee + `#chk-dimensions` toggle", () => {
    // Cone SO = 4, OA = 3
    const coneScene: Scene3D = {
      free_objects: ["O", "A", "S", "q_oa", "q_so"],
      objects: [
        pt("O", ["0", "0", "0"]),
        pt("A", ["3", "0", "0"]),
        pt("S", ["0", "0", "4"]),
        {
          id: "non",
          label: "Hình nón",
          notation: "(N)",
          type: "curved_solid",
          curved_kind: "cone",
          render: "curved_solid",
          origin: "derived",
          producer: "construct_cone",
          depends: ["O", "A", "S"],
          anchor: ["0", "0", "0"],
          axis: ["0", "0", "1"],
          apex: ["0", "0", "4"],
          rim_point: ["3", "0", "0"],
          radius_sq: "9",
          height_sq: "16",
        } as unknown as SceneObject,
        {
          id: "q_oa",
          label: "OA",
          notation: "OA",
          type: "quantity",
          render: "readout",
          origin: "free",
          producer: null,
          depends: ["O", "A"],
          value: "3",
          exact: { kind: "rational", value: "3" },
          source: { provenance: "GIVEN", is_given: true },
          annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["O", "A"], anchor: "segment" },
        } as unknown as SceneObject,
        {
          id: "q_so",
          label: "SO",
          notation: "SO",
          type: "quantity",
          render: "readout",
          origin: "free",
          producer: null,
          depends: ["S", "O"],
          value: "4",
          exact: { kind: "rational", value: "4" },
          source: { provenance: "GIVEN", is_given: true },
          annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["S", "O"], anchor: "segment" },
        } as unknown as SceneObject,
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "non", depends: ["O", "A", "S"], explanation: "Dựng hình nón.", semantic_kind: "GEOMETRY_CONSTRUCTION" },
      ],
    } as unknown as Scene3D;

    const conePlan = buildPedagogicalConstructionPlan(withSubEntities(coneScene));
    const coneTransformed = veKhongGian(conePlan.scene);
    // Step 1: base circle + OA -> `OA = 3` visible, `SO = 4` waits until Step 2!
    expect(annotationsAt(coneTransformed, conePlan.steps[0].anchor, DEFAULT_ANNOTATION_VIEW, null).map((a) => a.text)).toEqual(["OA = 3"]);
    // Step 2: axis SO constructed -> both `OA = 3` and `SO = 4` visible!
    expect(
      annotationsAt(coneTransformed, conePlan.steps[1].anchor, DEFAULT_ANNOTATION_VIEW, null)
        .map((a) => a.text)
        .sort(),
    ).toEqual(["OA = 3", "SO = 4"]);

    // Narrow viewport collision -> suppressed in `placeAnnotationLabels`, yet `givenQuantitiesSummary` + Study Dock `#dock-given-params` keeps every GIVEN quantity readable!
    const placedOnTinyViewport = placeAnnotationLabels(
      [
        { id: "q_oa", ax: 50, ay: 50, w: 64, h: 20, priority: 1 },
        { id: "q_so", ax: 52, ay: 51, w: 64, h: 20, priority: 1 },
      ],
      [{ x: 0, y: 0, w: 120, h: 120 }],
      { w: 120, h: 120 },
    );
    expect(placedOnTinyViewport.size).toBe(0);
    const summary = givenQuantitiesSummary(coneTransformed, conePlan.steps[1].anchor);
    expect(summary.map((s) => s.text).sort()).toEqual(["OA = 3", "SO = 4"]);

    // Workspace SSR exposes explicit `#chk-dimensions` toggle and `#dock-given-params` readout strip
    const wsHtml = renderToString(
      <AxoWorkspaceV62
        scene={coneScene}
        de="Cho hình nón đỉnh S, tâm đáy O với OA = 3, SO = 4."
        tieuDe="Hình nón"
      />,
    );
    expect(wsHtml).toContain('id="chk-dimensions"');
    expect(wsHtml).toContain('id="dock-given-params"');
    expect(wsHtml).toContain("OA = 3");
    expect(wsHtml).toContain("SO = 4");

    // Pyramid AB = 2, SA = 4 AND renamed Pyramid EF = 3, KE = 4
    const buildPyramidWithDims = (
      vNames: [string, string, string, string],
      baseLen: string,
      hLen: string,
    ): Scene3D => {
      const [A, B, C, S] = vNames;
      return {
        free_objects: [A, B, C, S, "q_base", "q_h"],
        objects: [
          pt(A, ["0", "0", "0"]),
          pt(B, [baseLen, "0", "0"]),
          pt(C, ["0", baseLen, "0"]),
          pt(S, ["0", "0", hLen]),
          {
            id: "chop",
            label: `Hình chóp ${S}.${A}${B}${C}`,
            type: "solid",
            render: "mesh",
            origin: "derived",
            producer: "construct_pyramid",
            depends: [A, B, C, S],
            vertex_ids: [A, B, C, S],
            vertices: [
              ["0", "0", "0"],
              [baseLen, "0", "0"],
              ["0", baseLen, "0"],
              ["0", "0", hLen],
            ],
            faces: [
              [0, 1, 2],
              [0, 1, 3],
              [1, 2, 3],
              [2, 0, 3],
            ],
          } as unknown as SceneObject,
          {
            id: "q_base",
            label: `${A}${B}`,
            notation: `${A}${B}`,
            type: "quantity",
            render: "readout",
            origin: "free",
            producer: null,
            depends: [A, B],
            value: baseLen,
            exact: { kind: "rational", value: baseLen },
            annotation: { kind: "length", category: "measurement", role: "given", subject_ids: [A, B], anchor: "segment" },
          } as unknown as SceneObject,
          {
            id: "q_h",
            label: `${S}${A}`,
            notation: `${S}${A}`,
            type: "quantity",
            render: "readout",
            origin: "free",
            producer: null,
            depends: [S, A],
            value: hLen,
            exact: { kind: "rational", value: hLen },
            annotation: { kind: "length", category: "measurement", role: "given", subject_ids: [S, A], anchor: "segment" },
          } as unknown as SceneObject,
        ],
        events: [
          { step_index: 0, action: "CREATE", object: "chop", depends: [A, B, C, S], explanation: "Dựng hình chóp.", semantic_kind: "GEOMETRY_CONSTRUCTION" },
        ],
      } as unknown as Scene3D;
    };

    const pyrAB = buildPedagogicalConstructionPlan(withSubEntities(buildPyramidWithDims(["A", "B", "C", "S"], "2", "4")));
    const pyrABFinal = annotationsAt(veKhongGian(pyrAB.scene), pyrAB.steps[pyrAB.steps.length - 1].anchor, DEFAULT_ANNOTATION_VIEW, null);
    expect(pyrABFinal.map((a) => a.text).sort()).toEqual(["AB = 2", "SA = 4"]);

    const pyrEF = buildPedagogicalConstructionPlan(withSubEntities(buildPyramidWithDims(["E", "F", "G", "K"], "3", "4")));
    const pyrEFFinal = annotationsAt(veKhongGian(pyrEF.scene), pyrEF.steps[pyrEF.steps.length - 1].anchor, DEFAULT_ANNOTATION_VIEW, null);
    expect(pyrEFFinal.map((a) => a.text).sort()).toEqual(["EF = 3", "KE = 4"]);

    // Right Cylinder IJ = 3, IK = √5 AND Oblique Cylinder OO′ = 3, OA = √5
    const buildCylWithDims = (cBot: string, cTop: string, rim: string, topX: string): Scene3D => ({
      free_objects: [cBot, cTop, rim, "q_axis", "q_rad"],
      objects: [
        pt(cBot, ["0", "0", "0"]),
        pt(cTop, [topX, "0", "3"]),
        pt(rim, ["2", "1", "0"]),
        {
          id: "tru",
          label: "Hình trụ",
          type: "curved_solid",
          curved_kind: "cylinder",
          render: "curved_solid",
          origin: "derived",
          producer: "construct_cylinder",
          depends: [cBot, cTop, rim],
          anchor: ["0", "0", "0"],
          apex_or_top: [topX, "0", "3"],
          rim_point: ["2", "1", "0"],
          radius_sq: "5",
          height_sq: "9",
        } as unknown as SceneObject,
        {
          id: "q_axis",
          label: `${cBot}${cTop.replace("_prime", "′")}`,
          notation: `${cBot}${cTop.replace("_prime", "′")}`,
          type: "quantity",
          render: "readout",
          origin: "free",
          producer: null,
          depends: [cBot, cTop],
          value: "3",
          exact: { kind: "rational", value: "3" },
          annotation: { kind: "length", category: "measurement", role: "given", subject_ids: [cBot, cTop], anchor: "segment" },
        } as unknown as SceneObject,
        {
          id: "q_rad",
          label: `${cBot}${rim}`,
          notation: `${cBot}${rim}`,
          type: "quantity",
          render: "readout",
          origin: "free",
          producer: null,
          depends: [cBot, rim],
          value: "√5",
          exact: { kind: "radical", coefficient: "1", radicand: 5 },
          annotation: { kind: "length", category: "measurement", role: "given", subject_ids: [cBot, rim], anchor: "segment" },
        } as unknown as SceneObject,
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "tru", depends: [cBot, cTop, rim], explanation: "Dựng hình trụ.", semantic_kind: "GEOMETRY_CONSTRUCTION" },
      ],
    } as unknown as Scene3D);

    const rightCyl = buildPedagogicalConstructionPlan(withSubEntities(buildCylWithDims("I", "J", "K", "0")));
    expect(
      annotationsAt(veKhongGian(rightCyl.scene), rightCyl.steps[rightCyl.steps.length - 1].anchor, DEFAULT_ANNOTATION_VIEW, null)
        .map((a) => a.text)
        .sort(),
    ).toEqual(["IJ = 3", "IK = √5"]);

    const obliqueCyl = buildPedagogicalConstructionPlan(withSubEntities(buildCylWithDims("O", "O_prime", "A", "1")));
    expect(
      annotationsAt(veKhongGian(obliqueCyl.scene), obliqueCyl.steps[obliqueCyl.steps.length - 1].anchor, DEFAULT_ANNOTATION_VIEW, null)
        .map((a) => a.text)
        .sort(),
    ).toEqual(["OA = √5", "OO′ = 3"]);

    // Prism AB = 6, AA′ = 5
    const prismScene: Scene3D = {
      free_objects: ["A", "B", "C", "A_prime", "B_prime", "C_prime", "q_ab", "q_aa"],
      objects: [
        pt("A", ["0", "0", "0"]),
        pt("B", ["6", "0", "0"]),
        pt("C", ["0", "6", "0"]),
        pt("A_prime", ["0", "0", "5"]),
        pt("B_prime", ["6", "0", "5"]),
        pt("C_prime", ["0", "6", "5"]),
        {
          id: "lt",
          label: "Lăng trụ ABC.A′B′C′",
          type: "solid",
          shape_class: "PRISM_LIKE",
          render: "mesh",
          origin: "derived",
          producer: "construct_prism",
          depends: ["A", "B", "C", "A_prime", "B_prime", "C_prime"],
          vertex_ids: ["A", "B", "C", "A_prime", "B_prime", "C_prime"],
          vertices: [
            ["0", "0", "0"],
            ["6", "0", "0"],
            ["0", "6", "0"],
            ["0", "0", "5"],
            ["6", "0", "5"],
            ["0", "6", "5"],
          ],
          faces: [
            [0, 1, 2],
            [3, 4, 5],
            [0, 1, 4, 3],
            [1, 2, 5, 4],
            [2, 0, 3, 5],
          ],
        } as unknown as SceneObject,
        {
          id: "q_ab",
          label: "AB",
          notation: "AB",
          type: "quantity",
          render: "readout",
          origin: "free",
          producer: null,
          depends: ["A", "B"],
          value: "6",
          exact: { kind: "rational", value: "6" },
          annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "B"], anchor: "segment" },
        } as unknown as SceneObject,
        {
          id: "q_aa",
          label: "AA′",
          notation: "AA′",
          type: "quantity",
          render: "readout",
          origin: "free",
          producer: null,
          depends: ["A", "A_prime"],
          value: "5",
          exact: { kind: "rational", value: "5" },
          annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "A_prime"], anchor: "segment" },
        } as unknown as SceneObject,
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "lt", depends: ["A", "B", "C", "A_prime", "B_prime", "C_prime"], explanation: "Dựng lăng trụ.", semantic_kind: "GEOMETRY_CONSTRUCTION" },
      ],
    } as unknown as Scene3D;
    const prismPlan = buildPedagogicalConstructionPlan(withSubEntities(prismScene));
    expect(
      annotationsAt(veKhongGian(prismPlan.scene), prismPlan.steps[prismPlan.steps.length - 1].anchor, DEFAULT_ANNOTATION_VIEW, null)
        .map((a) => a.text)
        .sort(),
    ).toEqual(["AA′ = 5", "AB = 6"]);

    // Pure geometry problem with ZERO given dimensions -> no #dock-given-params clutter, empty annotations
    const pureGeoSample = GEOMETRY_SAMPLES.find((s) => s.id === "thiet-dien-chop")!;
    const pureGeoScene = (pureGeoSample.envelope as unknown as { scene3d: Scene3D }).scene3d;
    const pureHtml = renderToString(
      <AxoWorkspaceV62 scene={pureGeoScene} de={pureGeoSample.problemText} tieuDe="Thiết diện hình chóp" />,
    );
    expect(pureHtml).not.toContain('id="dock-given-params"');
  });

  it("5. Hybrid Backend contract hardening: blocks MODEL_ASSUMPTION / free-text assumption scalars from GIVEN and fails closed on equilateral cylinder/cone (R = h)", () => {
    expect(
      classifyQuantityProvenance({
        id: "a_unit",
        label: "a",
        notation: "a",
        type: "quantity",
        render: "readout",
        origin: "free",
        producer: null,
        depends: [],
        value: "1",
        source: { provenance: "MODEL_ASSUMPTION", assumption: "Đặt cạnh đơn vị a = 1" },
      } as unknown as SceneObject),
    ).toBe("UNVERIFIED");

    expect(
      classifyQuantityProvenance({
        id: "ratio_k",
        label: "k",
        notation: "k",
        type: "quantity",
        render: "readout",
        origin: "free",
        producer: null,
        depends: [],
        value: "2",
        source: { assumption: "Giả thiết tỉ lệ dựng hình" },
      } as unknown as SceneObject),
    ).toBe("UNVERIFIED");

    expect(
      classifyQuantityProvenance({
        id: "ans_q",
        label: "V",
        notation: "V",
        type: "quantity",
        render: "readout",
        origin: "free",
        producer: null,
        depends: [],
        value: "12",
        annotation: { kind: "volume", category: "result", role: "answer" as unknown as "result", subject_ids: ["khoi"], anchor: "solid" },
      } as unknown as SceneObject),
    ).toBe("CERTIFIED_DERIVED");

    // Equilateral cylinder where R = h = 2 (radius_sq = "4", height_sq = "4"):
    // Unbound GIVEN scalars must NOT misbind h onto base radius OA or deduplicate h out of #dock-given-params!
    const eqCylScene: Scene3D = {
      free_objects: ["O", "O_prime", "R", "h"],
      objects: [
        pt("O", ["0", "0", "0"]),
        pt("O_prime", ["0", "0", "2"]),
        {
          id: "tru_deu",
          label: "Hình trụ R = h = 2",
          type: "curved_solid",
          render: "curved_solid",
          curved_kind: "cylinder",
          origin: "derived",
          producer: "construct_cylinder",
          depends: ["O", "O_prime", "R", "h"],
          center: ["0", "0", "0"],
          top_center: ["0", "0", "2"],
          axis: ["0", "0", "1"],
          rim_point: ["2", "0", "0"],
          radius_sq: "4",
          height_sq: "4",
        } as unknown as SceneObject,
        {
          id: "R",
          label: "Bán kính đáy",
          notation: "R",
          type: "quantity",
          render: "readout",
          origin: "free",
          producer: null,
          depends: [],
          value: "2",
          exact: { kind: "rational", value: "2" },
          source: { provenance: "GIVEN", fact_id: "f_r" },
        } as unknown as SceneObject,
        {
          id: "h",
          label: "Chiều cao",
          notation: "h",
          type: "quantity",
          render: "readout",
          origin: "free",
          producer: null,
          depends: [],
          value: "2",
          exact: { kind: "rational", value: "2" },
          source: { provenance: "GIVEN", fact_id: "f_h" },
        } as unknown as SceneObject,
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "tru_deu", depends: ["O", "O_prime", "R", "h"], explanation: "Dựng hình trụ.", semantic_kind: "GEOMETRY_CONSTRUCTION" },
      ],
    } as unknown as Scene3D;

    const eqPlan = buildPedagogicalConstructionPlan(withSubEntities(eqCylScene));
    const eqTransformed = veKhongGian(eqPlan.scene);
    // Neither unbound scalar may falsely pin onto base radius at Step 1 when radius_sq === height_sq
    expect(annotationsAt(eqTransformed, eqPlan.steps[0].anchor, DEFAULT_ANNOTATION_VIEW, null)).toEqual([]);
    // Yet BOTH GIVEN scalars remain distinct and readable in Study Dock #dock-given-params!
    const eqSummary = givenQuantitiesSummary(eqTransformed, eqPlan.steps[eqPlan.steps.length - 1].anchor);
    expect(eqSummary.map((s) => s.text).sort()).toEqual(["R = 2", "h = 2"]);
    expect(eqSummary.every((s) => s.status === "unattached_scalar")).toBe(true);
  });
});
