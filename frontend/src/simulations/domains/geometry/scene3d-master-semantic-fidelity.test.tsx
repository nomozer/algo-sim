import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import * as THREE from "three";
import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { solutionAt, tapKetQuaCuoi, type Scene3D, type SceneObject } from "./scene3d-model";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { veKhongGian } from "./scene3d-chart";
import { withSubEntities } from "./scene3d-subentities";
import { auxiliaryHiddenAt } from "./scene3d-auxiliary";
import {
  buildPedagogicalConstructionPlan,
  buildVerifiedObjectTooltip,
  classifyPolygonShapeWithProvenance,
  classifyScenePolygonShape,
  deriveExactPolygonMathBasis,
  formatCompactEntityChipLabel,
  pedagogicalStepList,
  resolvePlaneSectionVisibility,
  shortSym,
  verifySceneMathematicalConsistency,
  type SceneClaimProvenance,
} from "./scene3d-semantic-policy";
import {
  annotationsAt,
  DEFAULT_ANNOTATION_VIEW,
  givenQuantitiesSummary,
  placeAnnotationLabels,
} from "./scene3d-annotations";
import { buildObject3D } from "./scene3d-view";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";

function makePoint(
  id: string,
  xyz: [string, string, string],
  opts?: { provenance?: string; assumption?: string; isGiven?: boolean; notation?: string },
): SceneObject {
  const source: Record<string, unknown> = {};
  if (opts?.provenance) source.provenance = opts.provenance;
  if (opts?.assumption) source.assumption = opts.assumption;
  if (opts?.isGiven !== undefined) source.is_given = opts.isGiven;
  return {
    id,
    label: `Điểm ${opts?.notation ?? id}`,
    notation: opts?.notation ?? id,
    reference: opts?.notation ?? id,
    type: "point3",
    render: "point_marker",
    origin: "free",
    producer: null,
    depends: [],
    xyz,
    ...(Object.keys(source).length > 0 ? { source } : {}),
  } as unknown as SceneObject;
}

/**
 * Tái hiện trung thực bài toán bắt buộc §4.2:
 * "Cho hình chóp S.ABC có SA vuông góc với mặt phẳng (ABC), AB = 2a, SA = 4a."
 * Trong đường `SemanticProgramSpec -> build_scene3d`, các đỉnh `A(0,0,0), B(2,0,0), C(0,2,0), S(0,0,4)`
 * mang `source: { provenance: "LAYOUT_DERIVED" }` và không có `chart_metric`.
 */
function buildMandatorySabcScene(opts?: {
  withContractRolesAndWitness?: boolean;
  vertexNames?: [string, string, string, string];
  scaleFactor?: number;
  withExplicitAnnotations?: boolean;
}): Scene3D {
  const [A, B, C, S] = opts?.vertexNames ?? ["A", "B", "C", "S"];
  const k = opts?.scaleFactor ?? 1;
  const abVal = String(2 * k);
  const saVal = String(4 * k);
  const withRoles = opts?.withContractRolesAndWitness ?? false;
  const baseId = `day_${A}${B}${C}`;
  const saSegId = `${S}${A}_seg`;
  const solidId = "khoi_chop";

  return {
    free_objects: [A, `${A}${B}_length`, B, C, S, `${S}${A}_length`],
    objects: [
      makePoint(A, ["0", "0", "0"], { provenance: "LAYOUT_DERIVED" }),
      makePoint(B, [abVal, "0", "0"], { provenance: "LAYOUT_DERIVED" }),
      makePoint(C, ["0", abVal, "0"], { provenance: "LAYOUT_DERIVED" }),
      makePoint(S, ["0", "0", saVal], { provenance: "LAYOUT_DERIVED" }),
      {
        id: `${A}${B}_length`,
        label: `${A}${B}`,
        notation: `${A}${B}`,
        reference: `${A}${B}`,
        type: "quantity",
        render: "readout",
        origin: "free",
        producer: null,
        depends: opts?.withExplicitAnnotations ? [A, B] : [],
        source: { fact_id: "f_ab", provenance: "GIVEN" },
        value: abVal,
        exact: { kind: "rational", value: abVal },
        ...(opts?.withExplicitAnnotations
          ? {
              annotation: {
                kind: "length",
                category: "measurement",
                role: "given",
                subject_ids: [A, B],
                anchor: "segment",
              },
            }
          : {}),
      } as unknown as SceneObject,
      {
        id: `${S}${A}_length`,
        label: `${S}${A}`,
        notation: `${S}${A}`,
        reference: `${S}${A}`,
        type: "quantity",
        render: "readout",
        origin: "free",
        producer: null,
        depends: opts?.withExplicitAnnotations ? [S, A] : [],
        source: { fact_id: "f_sa", provenance: "GIVEN" },
        value: saVal,
        exact: { kind: "rational", value: saVal },
        ...(opts?.withExplicitAnnotations
          ? {
              annotation: {
                kind: "length",
                category: "measurement",
                role: "given",
                subject_ids: [S, A],
                anchor: "segment",
              },
            }
          : {}),
      } as unknown as SceneObject,
      {
        id: baseId,
        label: `Đáy ${A}${B}${C}`,
        notation: `${A}${B}${C}`,
        reference: `${A}${B}${C}`,
        role: `Đa giác ${A}, ${B}, ${C}`,
        type: "polygon3",
        render: "polygon",
        origin: "derived",
        producer: "construct_polygon",
        depends: [A, B, C],
        parent: solidId,
        display_group: ["construction", "face"],
        source: { instruction: "construct_polygon" },
        formation_roles: withRoles ? ["CONSTRUCT_BASE"] : ["CONSTRUCT_AUXILIARY_GEOMETRY"],
        vertices: [["0", "0", "0"], [abVal, "0", "0"], ["0", abVal, "0"]],
        vertex_ids: [A, B, C],
        surface_role: "BASE_REGION",
      } as unknown as SceneObject,
      {
        id: saSegId,
        label: `Đường cao ${S}${A}`,
        notation: `${S}${A}`,
        reference: `${S}${A}`,
        role: `Đoạn thẳng nối ${S} và ${A}`,
        type: "segment3",
        render: "segment",
        origin: "derived",
        producer: "construct_segment",
        depends: [A, S],
        endpoint_ids: [S, A],
        display_group: ["construction"],
        source: { instruction: "construct_segment" },
        formation_roles: withRoles ? ["CONSTRUCT_HEIGHT", "CONSTRUCT_LATERAL_BOUNDARY"] : ["CONSTRUCT_AUXILIARY_GEOMETRY"],
        point_a: ["0", "0", saVal],
        point_b: ["0", "0", "0"],
        endpoints: [["0", "0", saVal], ["0", "0", "0"]],
        ...(withRoles
          ? {
              perpendicular_witness: {
                certificate: "exact-gram-line-plane-orthogonality/1",
                relation: "line_perpendicular_plane",
                status: "ENGINE_VERIFIED",
                rule: "formation_construct_height",
                from: S,
                foot_id: A,
                foot: ["0", "0", "0"],
                on: baseId,
                plane_vertex_ids: [A, B, C],
                line_direction: ["0", "0", saVal],
                plane_directions: [[abVal, "0", "0"], ["0", abVal, "0"]],
                can_present_as_proven: true,
                marker: { u: [abVal, "0", "0"], v: ["0", "0", saVal] },
              },
            }
          : {}),
      } as unknown as SceneObject,
      {
        id: solidId,
        label: `Hình chóp ${S}.${A}${B}${C}`,
        notation: `${S}.${A}${B}${C}`,
        reference: `${S}.${A}${B}${C}`,
        type: "solid",
        render: "mesh",
        origin: "derived",
        producer: "construct_solid",
        depends: [A, B, C, S],
        display_group: ["construction", "solid"],
        source: { instruction: "construct_solid" },
        formation_roles: ["CLOSE_SOLID"],
        vertex_ids: [S, A, B, C],
        vertices: [["0", "0", saVal], ["0", "0", "0"], [abVal, "0", "0"], ["0", abVal, "0"]],
        faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]],
      } as unknown as SceneObject,
    ],
    events: [
      { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Khởi tạo.", semantic_kind: "EXPLANATION" },
      { step_index: 1, action: "CREATE", object: baseId, depends: [A, B, C], explanation: `Dựng Đáy ${A}${B}${C}.`, semantic_kind: "GEOMETRY_CONSTRUCTION" },
      { step_index: 2, action: "CREATE", object: saSegId, depends: [S, A], explanation: `Dựng ${S}${A}.`, semantic_kind: "GEOMETRY_CONSTRUCTION" },
      { step_index: 3, action: "CREATE", object: solidId, depends: [S, A, B, C], explanation: `Dựng Hình chóp ${S}.${A}${B}${C}.`, semantic_kind: "GEOMETRY_CONSTRUCTION" },
    ],
  } as unknown as Scene3D;
}

describe("AXO Master Scene3D §4–§7 & §10: Source Grounding, Pedagogical Sequencing & Plane/Section Clarity", () => {
  it("§4.1–§4.2 Mandatory Reproduction: S.ABC (SA ⊥ (ABC), AB = 2a, SA = 4a) NEVER claims base ABC is 'tam giác vuông cân' or 'Đề cho', and orders SA BEFORE solid closure", () => {
    for (const withContract of [false, true]) {
      const raw = buildMandatorySabcScene({ withContractRolesAndWitness: withContract, withExplicitAnnotations: true });
      const expanded = withSubEntities(raw);
      const basePoly = expanded.objects.find((o) => o.id === "day_ABC")!;

      const prov = classifyPolygonShapeWithProvenance(expanded, basePoly);
      expect(prov.provenance).toBe("ILLUSTRATIVE_CHOICE" satisfies SceneClaimProvenance);
      expect(prov.certifiedShape).toBeNull();
      expect(prov.coordinateShape).toBe("tam giác vuông cân");
      expect(classifyScenePolygonShape(expanded, basePoly)).toBe("tam giác");

      const plan = buildPedagogicalConstructionPlan(expanded);
      const titles = plan.steps.map((s) => s.title);
      expect(titles[0]).toBe("Dựng mặt đáy ABC");
      for (const st of plan.steps) {
        expect(st.title).not.toMatch(/vuông\s+cân|tam\s+giác\s+đều|tam\s+giác\s+vuông|tam\s+giác\s+cân/iu);
        expect(st.subtitle).not.toMatch(/vuông\s+cân/iu);
        expect(st.premise).not.toMatch(/vuông\s+cân/iu);
      }
      // Step 1 base shape is illustrative, so it must NOT stamp epistemicCategory = "given" ("Đề cho")
      expect(plan.steps[0].epistemicCategory).toBe("constructed");
      expect(plan.steps[0].premise).toMatch(/cấu\s+hình\s+minh\s+họa/iu);

      // SA must NEVER be ordered after "Hoàn thiện hình chóp S.ABC"
      const saStepIdx = plan.steps.findIndex((s) => s.targetIds.includes("SA_seg"));
      const closeStepIdx = plan.steps.findIndex((s) => s.targetIds.includes("khoi_chop"));
      expect(saStepIdx).toBeGreaterThan(0);
      expect(saStepIdx).toBeLessThan(closeStepIdx);
      if (withContract) {
        expect(plan.steps[saStepIdx].title).toBe("Dựng đường cao SA ⊥ (ABC) tại A");
      }

      // Tooltip on base ABC must not assert "tam giác vuông cân"
      const tip = buildVerifiedObjectTooltip(plan.scene, "day_ABC", plan.steps[0].anchor);
      expect(tip?.body ?? "").not.toMatch(/vuông\s+cân/iu);

      // Certified GIVEN lengths AB = 2 and SA = 4 appear at their carrier birth steps
      const transformed = veKhongGian(plan.scene);
      expect(annotationsAt(transformed, plan.steps[0].anchor, DEFAULT_ANNOTATION_VIEW, null).map((a) => a.text)).toEqual(["AB = 2"]);
      expect(
        annotationsAt(transformed, plan.steps[closeStepIdx].anchor, DEFAULT_ANNOTATION_VIEW, null)
          .map((a) => a.text)
          .sort(),
      ).toEqual(["AB = 2", "SA = 4"]);
    }
  });

  it("§4.1 & §10 Counterfactuals: renamed vertices (K.EFG), rescaled coordinates, 6-state provenance taxonomy, SSS-certified triangle, uncertified tetrahedron & regular-pyramid guard", () => {
    // 1. Renamed & rescaled counterfactual (K.EFG, EF = 6, KE = 12)
    const renamed = buildMandatorySabcScene({
      withContractRolesAndWitness: true,
      vertexNames: ["E", "F", "G", "K"],
      scaleFactor: 3,
      withExplicitAnnotations: true,
    });
    const renamedPlan = buildPedagogicalConstructionPlan(withSubEntities(renamed));
    expect(renamedPlan.steps[0].title).toBe("Dựng mặt đáy EFG");
    expect(renamedPlan.steps.some((s) => /vuông\s+cân/iu.test(s.title))).toBe(false);
    expect(renamedPlan.steps[1].title).toBe("Dựng đường cao KE ⊥ (EFG) tại E");

    // 2. LAYOUT_DERIVED vertices WITH all 3 triangle side lengths GIVEN (3-4-5 SSS) -> certified right triangle!
    const sssTriScene: Scene3D = {
      free_objects: ["A", "B", "C", "S", "q_ab", "q_ac", "q_bc"],
      objects: [
        makePoint("A", ["0", "0", "0"], { provenance: "LAYOUT_DERIVED" }),
        makePoint("B", ["3", "0", "0"], { provenance: "LAYOUT_DERIVED" }),
        makePoint("C", ["0", "4", "0"], { provenance: "LAYOUT_DERIVED" }),
        makePoint("S", ["0", "0", "5"], { provenance: "LAYOUT_DERIVED" }),
        {
          id: "q_ab",
          label: "AB",
          notation: "AB",
          type: "quantity",
          render: "readout",
          origin: "free",
          producer: null,
          depends: ["A", "B"],
          source: { provenance: "GIVEN", fact_id: "f1" },
          value: "3",
          exact: { kind: "rational", value: "3" },
          annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "B"], anchor: "segment" },
        } as unknown as SceneObject,
        {
          id: "q_ac",
          label: "AC",
          notation: "AC",
          type: "quantity",
          render: "readout",
          origin: "free",
          producer: null,
          depends: ["A", "C"],
          source: { provenance: "GIVEN", fact_id: "f2" },
          value: "4",
          exact: { kind: "rational", value: "4" },
          annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "C"], anchor: "segment" },
        } as unknown as SceneObject,
        {
          id: "q_bc",
          label: "BC",
          notation: "BC",
          type: "quantity",
          render: "readout",
          origin: "free",
          producer: null,
          depends: ["B", "C"],
          source: { provenance: "GIVEN", fact_id: "f3" },
          value: "5",
          exact: { kind: "rational", value: "5" },
          annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["B", "C"], anchor: "segment" },
        } as unknown as SceneObject,
        {
          id: "day_sss",
          label: "Đáy ABC",
          notation: "ABC",
          type: "polygon3",
          render: "polygon",
          surface_role: "BASE_REGION",
          formation_roles: ["CONSTRUCT_BASE"],
          origin: "derived",
          depends: ["A", "B", "C"],
          vertex_ids: ["A", "B", "C"],
          vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "4", "0"]],
        } as unknown as SceneObject,
      ],
      events: [{ step_index: 0, action: "CREATE", object: "day_sss", depends: ["A", "B", "C"] }],
    } as unknown as Scene3D;
    // Without a Backend right-angle witness or shape provenance, Frontend must NOT re-measure 3 lengths to self-certify DERIVED_VERIFIED (§3.2)
    const sssProv = classifyPolygonShapeWithProvenance(sssTriScene, sssTriScene.objects.find((o) => o.id === "day_sss")!);
    expect(sssProv.certifiedShape).toBeNull();
    // Once Backend certifies the in-plane right angle via `perpendicular_witness`, it becomes DERIVED_VERIFIED "tam giác vuông"
    const sssWithBackendCert: Scene3D = {
      ...sssTriScene,
      objects: [
        ...sssTriScene.objects,
        {
          id: "ab_perp_ac",
          type: "segment3",
          label: "AB",
          notation: "AB",
          origin: "derived",
          render: "segment",
          depends: ["A", "B"],
          point_a: ["3", "0", "0"],
          point_b: ["0", "0", "0"],
          perpendicular_witness: {
            relation: "line_perp_line",
            status: "ENGINE_VERIFIED",
            can_present_as_proven: true,
            from: "B",
            foot_id: "A",
            foot: ["0", "0", "0"],
            on: "C",
            marker: { u: ["3", "0", "0"], v: ["0", "4", "0"] },
          },
        } as unknown as SceneObject,
      ],
    };
    const sssCertProv = classifyPolygonShapeWithProvenance(
      sssWithBackendCert,
      sssWithBackendCert.objects.find((o) => o.id === "day_sss")!,
    );
    expect(["GIVEN", "DERIVED_VERIFIED"]).toContain(sssCertProv.provenance);
    expect(sssCertProv.certifiedShape).toBe("tam giác vuông");

    // 3. Contradictory label vs coordinates -> CONTRADICTORY_OR_UNSUPPORTED, never claims "hình vuông"
    const contraScene: Scene3D = {
      free_objects: ["A", "B", "C", "D"],
      objects: [
        makePoint("A", ["0", "0", "0"]),
        makePoint("B", ["3", "0", "0"]),
        makePoint("C", ["2", "2", "0"]),
        makePoint("D", ["0", "2", "0"]),
        {
          id: "day_bad",
          label: "Đáy ABCD là hình vuông",
          notation: "ABCD",
          type: "polygon3",
          render: "polygon",
          surface_role: "BASE_REGION",
          formation_roles: ["CONSTRUCT_BASE"],
          origin: "derived",
          depends: ["A", "B", "C", "D"],
          vertex_ids: ["A", "B", "C", "D"],
          vertices: [["0", "0", "0"], ["3", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]],
        } as unknown as SceneObject,
      ],
      events: [{ step_index: 0, action: "CREATE", object: "day_bad", depends: ["A", "B", "C", "D"] }],
    } as unknown as Scene3D;
    const contraProv = classifyPolygonShapeWithProvenance(contraScene, contraScene.objects.find((o) => o.id === "day_bad")!);
    expect(contraProv.provenance).toBe("CONTRADICTORY_OR_UNSUPPORTED");
    expect(contraProv.certifiedShape).toBeNull();
    const contraPlan = buildPedagogicalConstructionPlan(contraScene);
    expect(contraPlan.steps[0].title).not.toMatch(/hình\s+vuông/iu);

    // 4. Missing provenance with partial given edge (AB = 2 only, no source on vertices) -> UNVERIFIED / ILLUSTRATIVE_CHOICE, NOT "tam giác vuông cân"
    const missingProvScene: Scene3D = {
      free_objects: ["A", "B", "C", "q_ab"],
      objects: [
        makePoint("A", ["0", "0", "0"]),
        makePoint("B", ["2", "0", "0"]),
        makePoint("C", ["0", "2", "0"]),
        {
          id: "q_ab",
          label: "AB",
          notation: "AB",
          type: "quantity",
          render: "readout",
          origin: "free",
          producer: null,
          depends: ["A", "B"],
          value: "2",
          annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "B"], anchor: "segment" },
        } as unknown as SceneObject,
        {
          id: "day_partial",
          label: "Đáy ABC",
          notation: "ABC",
          type: "polygon3",
          render: "polygon",
          surface_role: "BASE_REGION",
          formation_roles: ["CONSTRUCT_BASE"],
          origin: "derived",
          depends: ["A", "B", "C"],
          vertex_ids: ["A", "B", "C"],
          vertices: [["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]],
        } as unknown as SceneObject,
      ],
      events: [{ step_index: 0, action: "CREATE", object: "day_partial", depends: ["A", "B", "C"] }],
    } as unknown as Scene3D;
    const partialProv = classifyPolygonShapeWithProvenance(
      missingProvScene,
      missingProvScene.objects.find((o) => o.id === "day_partial")!,
    );
    expect(["UNVERIFIED", "ILLUSTRATIVE_CHOICE"]).toContain(partialProv.provenance);
    expect(partialProv.certifiedShape).toBeNull();

    // 5. Uncertified LAYOUT_DERIVED square-like pyramid with apex above center MUST NOT synthesize false regular-pyramid center O or claim "chóp đều"
    const uncertPyr: Scene3D = {
      free_objects: ["A", "B", "C", "D", "S"],
      objects: [
        makePoint("A", ["0", "0", "0"], { provenance: "LAYOUT_DERIVED" }),
        makePoint("B", ["2", "0", "0"], { provenance: "LAYOUT_DERIVED" }),
        makePoint("C", ["2", "2", "0"], { provenance: "LAYOUT_DERIVED" }),
        makePoint("D", ["0", "2", "0"], { provenance: "LAYOUT_DERIVED" }),
        makePoint("S", ["1", "1", "3"], { provenance: "LAYOUT_DERIVED" }),
        {
          id: "chop_uncert",
          label: "Hình chóp S.ABCD",
          notation: "S.ABCD",
          shape_class: "PYRAMID_LIKE",
          type: "solid",
          render: "mesh",
          origin: "derived",
          depends: ["A", "B", "C", "D", "S"],
          vertex_ids: ["S", "A", "B", "C", "D"],
          vertices: [["1", "1", "3"], ["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]],
          faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]],
        } as unknown as SceneObject,
      ],
      events: [{ step_index: 0, action: "CREATE", object: "chop_uncert", depends: ["A", "B", "C", "D", "S"] }],
    } as unknown as Scene3D;
    const uncertPyrPlan = buildPedagogicalConstructionPlan(withSubEntities(uncertPyr));
    expect(uncertPyrPlan.steps.some((s) => /hình\s+vuông|chóp\s+đều|tâm\s+đáy/iu.test(s.title))).toBe(false);
  });

  it("§4.3 Cross-family geometric fidelity: parallel section on uncertified base, genuine oblique cylinder, tangent & non-intersecting sphere-plane cases", () => {
    // 1. Parallel cross-section (MNP) on uncertified S.ABC preserves MN ∥ AB without claiming "tam giác vuông cân"
    const sabcSec = buildMandatorySabcScene({ withContractRolesAndWitness: true });
    sabcSec.objects.push(
      { id: "M", label: "M", notation: "M", type: "point3", render: "point_marker", origin: "derived", producer: "construct_point.midpoint", depends: ["S", "A"], xyz: ["0", "0", "2"] } as unknown as SceneObject,
      { id: "N", label: "N", notation: "N", type: "point3", render: "point_marker", origin: "derived", producer: "construct_point.midpoint", depends: ["S", "B"], xyz: ["1", "0", "2"] } as unknown as SceneObject,
      { id: "P", label: "P", notation: "P", type: "point3", render: "point_marker", origin: "derived", producer: "construct_point.midpoint", depends: ["S", "C"], xyz: ["0", "1", "2"] } as unknown as SceneObject,
      { id: "mp_mnp", label: "(MNP)", notation: "(MNP)", type: "plane3", render: "surface", surface_role: "CUTTING_PLANE", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], origin: "derived", depends: ["M", "N", "P"], point: ["0", "0", "2"], normal: ["0", "0", "1"] } as unknown as SceneObject,
      { id: "td_mnp", label: "Thiết diện (MNP)", notation: "(MNP)", type: "section", render: "polygon", origin: "derived", depends: ["khoi_chop", "mp_mnp", "M", "N", "P"], polygon: [["0", "0", "2"], ["1", "0", "2"], ["0", "1", "2"]] } as unknown as SceneObject,
    );
    sabcSec.events.push(
      { step_index: 4, action: "CREATE", object: "M", depends: ["S", "A"], explanation: "M" },
      { step_index: 5, action: "CREATE", object: "N", depends: ["S", "B"], explanation: "N" },
      { step_index: 6, action: "CREATE", object: "P", depends: ["S", "C"], explanation: "P" },
      { step_index: 7, action: "CREATE", object: "mp_mnp", depends: ["M", "N", "P"], explanation: "(MNP)" },
      { step_index: 8, action: "CREATE", object: "td_mnp", depends: ["khoi_chop", "mp_mnp", "M", "N", "P"], explanation: "Thiết diện" },
    );
    const basis = deriveExactPolygonMathBasis(sabcSec, sabcSec.objects.find((o) => o.id === "td_mnp")!);
    expect(basis).not.toBeNull();
    expect(basis!.shape).toBe("tam giác");
    expect(basis!.summary).not.toMatch(/vuông\s+cân/iu);
    expect(basis!.parallelPairs.length).toBeGreaterThanOrEqual(2);

    // 2. Genuine oblique cylinder (axis OO′ = (1, 0, 3) NOT orthogonal to horizontal base z = 0)
    const oblCyl: Scene3D = {
      free_objects: ["O", "O_prime", "A"],
      objects: [
        makePoint("O", ["0", "0", "0"]),
        makePoint("O_prime", ["1", "0", "3"], { notation: "O′" }),
        makePoint("A", ["2", "0", "0"]),
        {
          id: "tru_xien",
          label: "Hình trụ xiên",
          type: "curved_solid",
          curved_kind: "cylinder",
          render: "curved_solid",
          origin: "derived",
          depends: ["O", "O_prime", "A"],
          anchor: ["0", "0", "0"],
          apex_or_top: ["1", "0", "3"],
          rim_point: ["2", "0", "0"],
          radius_sq: "4",
          height_sq: "9",
        } as unknown as SceneObject,
      ],
      events: [{ step_index: 0, action: "CREATE", object: "tru_xien", depends: ["O", "O_prime", "A"], explanation: "Dựng hình trụ xiên." }],
    } as unknown as Scene3D;
    const oblCylPlan = buildPedagogicalConstructionPlan(withSubEntities(oblCyl));
    expect(oblCylPlan.steps.some((s) => /hình\s+trụ\s+xiên/iu.test(s.title))).toBe(true);
    expect(oblCylPlan.steps.some((s) => /trục\s+đối\s+xứng\s+vuông\s+góc/iu.test(s.subtitle))).toBe(false);

    // 3. Sphere + tangent plane (d = R = 5 -> 1 tangent point T, NO false circle3 section) & non-intersecting plane (d = 7 > R = 5)
    const sphereTangent: Scene3D = {
      free_objects: ["I"],
      objects: [
        makePoint("I", ["0", "0", "0"]),
        { id: "cau", label: "Mặt cầu (S)", notation: "(S)", type: "curved_solid", curved_kind: "ball", render: "curved_solid", origin: "derived", depends: ["I"], anchor: ["0", "0", "0"], radius_sq: "25" } as unknown as SceneObject,
        { id: "mp_tiep", label: "(P)", notation: "(P)", type: "plane3", render: "surface", origin: "derived", depends: [], point: ["0", "0", "5"], normal: ["0", "0", "1"] } as unknown as SceneObject,
        { id: "T", label: "Tiếp điểm T", notation: "T", role: "Tiếp điểm của mặt cầu (S) và mặt phẳng (P)", type: "point3", render: "point_marker", origin: "derived", depends: ["cau", "mp_tiep"], xyz: ["0", "0", "5"], perpendicular_witness: { from: "I", foot: ["0", "0", "5"], foot_id: "T", on: "mp_tiep", relation: "line_perp_plane", marker: { u: ["1", "0", "0"], v: ["0", "0", "-5"] } } } as unknown as SceneObject,
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "cau", depends: ["I"] },
        { step_index: 1, action: "CREATE", object: "mp_tiep", depends: [] },
        { step_index: 2, action: "CREATE", object: "T", depends: ["cau", "mp_tiep"] },
      ],
    } as unknown as Scene3D;
    expect(verifySceneMathematicalConsistency(sphereTangent).valid).toBe(true);
    const tanPlan = buildPedagogicalConstructionPlan(sphereTangent);
    expect(tanPlan.scene.objects.some((o) => o.type === "circle3" && o.surface_role !== "BASE_REGION")).toBe(false);

    // Contradictory circle section claimed on non-intersecting plane (d = 7 > R = 5) MUST fail consistency check!
    const badSphereCut: Scene3D = {
      free_objects: ["I"],
      objects: [
        makePoint("I", ["0", "0", "0"]),
        { id: "cau", label: "Mặt cầu (S)", notation: "(S)", type: "curved_solid", curved_kind: "ball", render: "curved_solid", origin: "derived", depends: ["I"], anchor: ["0", "0", "0"], radius_sq: "25" } as unknown as SceneObject,
        { id: "mp_ngoai", label: "(Q)", notation: "(Q)", type: "plane3", render: "surface", origin: "derived", depends: [], point: ["0", "0", "7"], normal: ["0", "0", "1"] } as unknown as SceneObject,
        { id: "c_fake", label: "Giao tuyến", type: "circle3", render: "circle", origin: "derived", depends: ["cau", "mp_ngoai"], center: ["0", "0", "7"], normal: ["0", "0", "1"], radius_sq: "4" } as unknown as SceneObject,
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "cau", depends: ["I"] },
        { step_index: 1, action: "CREATE", object: "mp_ngoai", depends: [] },
        { step_index: 2, action: "CREATE", object: "c_fake", depends: ["cau", "mp_ngoai"] },
      ],
    } as unknown as Scene3D;
    expect(verifySceneMathematicalConsistency(badSphereCut).valid).toBe(false);
  });

  it("§5 Zero calculation/measurement steps in buildPedagogicalConstructionPlan AND pedagogicalStepList (including intermediate MEASURE events & clean geometric operations)", () => {
    for (const sample of GEOMETRY_SAMPLES) {
      const raw = (sample.envelope as unknown as { scene3d: Scene3D }).scene3d;
      const expanded = withSubEntities(raw);
      const plan = buildPedagogicalConstructionPlan(expanded);
      const directList = pedagogicalStepList(plan.scene);
      const rawList = pedagogicalStepList(expanded);

      expect(directList.map((s) => s.title)).toEqual(plan.steps.map((s) => s.title));
      expect(rawList.length).toBeGreaterThan(0);

      for (const st of [...plan.steps, ...rawList]) {
        expect(st.epistemicCategory).not.toBe("conclusion");
        expect(st.title).not.toMatch(/^(Tính|Kết luận|Đo)\b/iu);
        expect(st.operation).not.toMatch(/độ dài cần tìm|khoảng cách giữa hai đường thẳng chéo nhau$/iu);
      }
    }

    // Scene with an isolated intermediate MEASURE step (role: "intermediate") between constructions -> MUST be folded, never a standalone step!
    const interMeasScene: Scene3D = {
      free_objects: ["O", "O_prime", "A"],
      objects: [
        makePoint("O", ["0", "0", "0"]),
        makePoint("O_prime", ["0", "0", "3"], { notation: "O′" }),
        makePoint("A", ["2", "0", "0"]),
        {
          id: "tru",
          label: "Hình trụ",
          type: "curved_solid",
          curved_kind: "cylinder",
          render: "curved_solid",
          origin: "derived",
          depends: ["O", "O_prime", "A"],
          anchor: ["0", "0", "0"],
          apex_or_top: ["0", "0", "3"],
          rim_point: ["2", "0", "0"],
          radius_sq: "4",
          height_sq: "9",
        } as unknown as SceneObject,
        {
          id: "h_inter",
          label: "Chiều cao OO′",
          notation: "d(O, O′)",
          type: "quantity",
          render: "readout",
          origin: "derived",
          producer: "measure.distance",
          depends: ["O", "O_prime"],
          value: "3",
          annotation: { kind: "length", category: "measurement", role: "intermediate", subject_ids: ["O", "O_prime"], anchor: "segment" },
        } as unknown as SceneObject,
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "tru", depends: ["O", "O_prime", "A"], semantic_kind: "GEOMETRY_CONSTRUCTION" },
        { step_index: 1, action: "MEASURE", object: "h_inter", depends: ["O", "O_prime"], semantic_kind: "MEASUREMENT", explanation: "Tính chiều cao OO′ = 3." },
      ],
    } as unknown as Scene3D;
    const interPlan = buildPedagogicalConstructionPlan(withSubEntities(interMeasScene));
    expect(interPlan.steps.every((s) => s.targetIds.length > 0)).toBe(true);
    expect(pedagogicalStepList(withSubEntities(interMeasScene)).every((s) => s.targetIds.length > 0)).toBe(true);

    // Leading MEASURE event before first visual CREATE + common_perpendicular witness -> 0 standalone MEASURE steps and pure geometric operation string
    const leadingMeasAndSkewScene: Scene3D = {
      free_objects: ["A", "B", "C", "D"],
      objects: [
        makePoint("A", ["0", "0", "0"]),
        makePoint("B", ["2", "0", "0"]),
        makePoint("C", ["0", "2", "0"]),
        makePoint("D", ["0", "2", "3"]),
        {
          id: "q_init",
          label: "Tham số tỷ lệ",
          type: "quantity",
          render: "readout",
          origin: "derived",
          depends: ["A", "B"],
          value: "2",
          annotation: { kind: "length", category: "measurement", role: "intermediate", subject_ids: ["A", "B"], anchor: "segment" },
        } as unknown as SceneObject,
        {
          id: "seg_common_perp",
          label: "AC",
          notation: "AC",
          type: "segment3",
          render: "segment",
          origin: "derived",
          depends: ["A", "C"],
          endpoints: [["0", "0", "0"], ["0", "2", "0"]],
          perpendicular_witness: {
            from: "A",
            foot: ["0", "2", "0"],
            foot_id: "C",
            on: "C",
            relation: "common_perpendicular",
            marker: { u: ["1", "0", "0"], v: ["0", "1", "0"] },
          },
        } as unknown as SceneObject,
      ],
      events: [
        { step_index: 0, action: "MEASURE", object: "q_init", depends: ["A", "B"], semantic_kind: "MEASUREMENT", explanation: "Tính tham số trung gian." },
        { step_index: 1, action: "CREATE", object: "seg_common_perp", depends: ["A", "C"], semantic_kind: "GEOMETRY_CONSTRUCTION", explanation: "Dựng đoạn vuông góc chung AC." },
      ],
    } as unknown as Scene3D;
    const skewPlan = buildPedagogicalConstructionPlan(leadingMeasAndSkewScene);
    expect(skewPlan.steps).toHaveLength(1);
    expect(skewPlan.steps[0].targetIds).toContain("seg_common_perp");
    expect(skewPlan.steps[0].operation).not.toMatch(/khoảng cách giữa hai đường thẳng chéo nhau|độ dài cần tìm/iu);
    expect(pedagogicalStepList(leadingMeasAndSkewScene)).toHaveLength(1);
  });

  it("§6 & §7 Display controls, single non-duplicated step counter, and cross-section interior avoidance for numeric annotations", () => {
    const tdSample = GEOMETRY_SAMPLES.find((s) => s.id === "thiet-dien-chop")!;
    const tdScene = (tdSample.envelope as unknown as { scene3d: Scene3D }).scene3d;
    const plan = buildPedagogicalConstructionPlan(withSubEntities(tdScene));
    const mpObj = plan.scene.objects.find((o) => o.type === "plane3")!;
    const finalAnchor = plan.steps[plan.steps.length - 1].anchor;

    // Cutting plane demoted/attenuated once section completes
    const visAtFinal = resolvePlaneSectionVisibility(plan.scene, mpObj, finalAnchor, false, null);
    expect(visAtFinal.opacityScale).toBeLessThanOrEqual(0.3);

    // Study Dock header does NOT duplicate `(X/Y)` next to `#dock-steps-counter` `Bước X/Y`
    const ssr = renderToString(<AxoWorkspaceV62 scene={tdScene} de={tdSample.problemText} tieuDe="Thiết diện" />);
    expect(ssr).toContain('id="dock-steps-counter"');
    expect(ssr).not.toMatch(/Các bước dựng hình\s*\(\d+\/\d+\)/iu);

    // Numeric annotation placement avoids active cross-section interior (`tranhUuTien`) when exterior space exists
    const sectionBox = { x: 180, y: 180, w: 90, h: 90 };
    const candidate = [{ id: "q_sa", ax: 182, ay: 210, w: 52, h: 20, priority: 2 }];
    const placed = placeAnnotationLabels(candidate, [], { w: 600, h: 480 }, [sectionBox]);
    const box = placed.get("q_sa");
    expect(box).toBeDefined();
    const overlapsSection =
      box!.x < sectionBox.x + sectionBox.w
      && box!.x + box!.w > sectionBox.x
      && box!.y < sectionBox.y + sectionBox.h
      && box!.y + box!.h > sectionBox.y;
    expect(overlapsSection).toBe(false);
  });

  it("§5–§7 Visual QA Root-Cause Gate: segment3 with render='line' builds 3D intersection geometry, givenQuantitiesSummary deduplicates unbound+attached pairs, oblique prism orders base BEFORE centroid G, and unnamed intersection points avoid 'giao điểm giao điểm'", () => {
    // 1. segment3 carrying render='line' + endpoints (without infinite line point+direction) builds non-null 3D geometry
    const interSegObj = {
      id: "gt_so",
      type: "segment3",
      label: "Giao tuyến SO",
      notation: "SO",
      origin: "derived",
      producer: "intersect_planes",
      render: "line",
      display_group: ["construction", "target"],
      depends: ["S", "O"],
      endpoints: [["0", "0", "5"], ["2", "2", "0"]],
    } as unknown as SceneObject;
    const builtSeg = buildObject3D(interSegObj, true);
    expect(builtSeg).not.toBeNull();

    // 2. givenQuantitiesSummary deduplicates unbound scalar `AB_length` + attached `q_ab_given` having identical `AB = 2` text
    const dupGivenScene = buildMandatorySabcScene({ withContractRolesAndWitness: true, withExplicitAnnotations: true });
    dupGivenScene.objects.push({
      id: "AB_length_unbound",
      type: "quantity",
      label: "AB",
      notation: "AB",
      origin: "free",
      render: "readout",
      depends: [],
      value: "2",
    } as unknown as SceneObject);
    dupGivenScene.free_objects.push("AB_length_unbound");
    const summaryPills = givenQuantitiesSummary(dupGivenScene, 4);
    const abPills = summaryPills.filter((p) => p.text === "AB = 2");
    expect(abPills).toHaveLength(1);
    expect(abPills[0].status).toBe("on_canvas");

    // 3. Oblique prism with centroid G on base ABC: base ABC MUST be constructed BEFORE centroid G, and illustrative base never claims 'tam giác vuông cân'
    const obliquePrismScene: Scene3D = {
      free_objects: ["A", "B", "C", "A_prime", "B_prime", "C_prime"],
      objects: [
        makePoint("A", ["0", "0", "0"], { provenance: "LAYOUT_DERIVED" }),
        makePoint("B", ["3", "0", "0"], { provenance: "LAYOUT_DERIVED" }),
        makePoint("C", ["0", "3", "0"], { provenance: "LAYOUT_DERIVED" }),
        makePoint("A_prime", ["1", "1", "4"], { provenance: "LAYOUT_DERIVED" }),
        makePoint("B_prime", ["4", "1", "4"], { provenance: "LAYOUT_DERIVED" }),
        makePoint("C_prime", ["1", "4", "4"], { provenance: "LAYOUT_DERIVED" }),
        {
          id: "G",
          type: "point3",
          label: "Trọng tâm G",
          notation: "G",
          origin: "derived",
          producer: "centroid",
          render: "point_marker",
          depends: ["A", "B", "C"],
          xyz: ["1", "1", "0"],
        } as unknown as SceneObject,
        {
          id: "h_a_prime_g",
          type: "segment3",
          label: "Đường cao A′G",
          notation: "A′G",
          origin: "derived",
          render: "segment",
          formation_roles: ["CONSTRUCT_HEIGHT"],
          depends: ["A_prime", "G"],
          point_a: ["1", "1", "4"],
          point_b: ["1", "1", "0"],
          perpendicular_witness: {
            from: "A_prime",
            foot: ["1", "1", "0"],
            foot_id: "G",
            on: "lang_tru_xien",
            relation: "line_perp_plane",
            plane_directions: [["3", "0", "0"], ["0", "3", "0"]],
            marker: { u: ["3", "0", "0"], v: ["0", "0", "4"] },
          },
        } as unknown as SceneObject,
        {
          id: "lang_tru_xien",
          type: "solid",
          label: "Hình lăng trụ xiên ABC.A′B′C′",
          notation: "ABC.A′B′C′",
          shape_class: "PRISM_LIKE",
          origin: "derived",
          render: "mesh",
          depends: ["A", "B", "C", "A_prime", "B_prime", "C_prime"],
          vertex_ids: ["A", "B", "C", "A_prime", "B_prime", "C_prime"],
          vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "3", "0"], ["1", "1", "4"], ["4", "1", "4"], ["1", "4", "4"]],
          faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]],
        } as unknown as SceneObject,
      ],
      events: [
        { step_index: 0, action: "INIT" },
        { step_index: 1, action: "CREATE", object: "G", depends: ["A", "B", "C"] },
        { step_index: 2, action: "CREATE", object: "h_a_prime_g", depends: ["A_prime", "G"] },
        { step_index: 3, action: "CREATE", object: "lang_tru_xien", depends: ["A", "B", "C", "A_prime", "B_prime", "C_prime"] },
      ],
    } as unknown as Scene3D;
    const obliquePlan = buildPedagogicalConstructionPlan(withSubEntities(obliquePrismScene));
    const baseStepIdx = obliquePlan.steps.findIndex((s) => s.targetIds.includes("lang_tru_xien__base"));
    const centroidStepIdx = obliquePlan.steps.findIndex((s) => s.targetIds.includes("G"));
    expect(baseStepIdx).toBe(0);
    expect(centroidStepIdx).toBeGreaterThan(baseStepIdx);
    expect(obliquePlan.steps[baseStepIdx].title).toBe("Dựng mặt đáy ABC");
    expect(obliquePlan.steps.some((s) => /vuông\s+cân/iu.test(s.title))).toBe(false);

    // 4. Unnamed Hybrid intersection point (`label: "Giao điểm của BB′ và (α)"`) never produces duplicate 'giao điểm giao điểm'
    const unnamedInterScene: Scene3D = {
      free_objects: ["B", "B_prime", "M"],
      objects: [
        makePoint("B", ["0", "0", "0"]),
        makePoint("B_prime", ["0", "0", "4"], { notation: "B′" }),
        makePoint("M", ["2", "0", "2"]),
        {
          id: "line_bb",
          type: "line3",
          label: "Đường thẳng BB′",
          notation: "BB′",
          origin: "derived",
          render: "line",
          depends: ["B", "B_prime"],
          point: ["0", "0", "0"],
          direction: ["0", "0", "1"],
        } as unknown as SceneObject,
        {
          id: "mp_alpha",
          type: "plane3",
          label: "Mặt phẳng (α)",
          notation: "(α)",
          origin: "derived",
          render: "surface",
          depends: ["M"],
          point: ["0", "0", "1"],
          normal: ["0", "0", "1"],
        } as unknown as SceneObject,
        {
          id: "pt_inter_unnamed",
          type: "point3",
          label: "Giao điểm của BB′ và (α)",
          origin: "derived",
          producer: "intersect_line_plane",
          render: "point_marker",
          depends: ["line_bb", "mp_alpha"],
          xyz: ["0", "0", "1"],
        } as unknown as SceneObject,
      ],
      events: [
        { step_index: 0, action: "INIT" },
        { step_index: 1, action: "CREATE", object: "line_bb", depends: ["B", "B_prime"] },
        { step_index: 2, action: "CREATE", object: "mp_alpha", depends: ["M"] },
        { step_index: 3, action: "CREATE", object: "pt_inter_unnamed", depends: ["line_bb", "mp_alpha"] },
      ],
    } as unknown as Scene3D;
    const interPlan = buildPedagogicalConstructionPlan(unnamedInterScene);
    for (const st of interPlan.steps) {
      expect(st.title).not.toMatch(/giao\s+điểm\s+giao\s+điểm/iu);
    }
  });

  it("§7.1 Certified GIVEN quantities emitted via untyped MEASURE events or referenced via same_as from a result are never hidden as final answers", () => {
    const baseScene = buildMandatorySabcScene({
      withContractRolesAndWitness: true,
      withExplicitAnnotations: true,
    });
    // Simulate upstream emitting untyped MEASURE events for GIVEN quantities + a FINAL_RESULT referencing a GIVEN via same_as
    const sceneWithUntypedGivenMeasure: Scene3D = {
      ...baseScene,
      free_objects: baseScene.free_objects.filter((id) => id !== "AB_length" && id !== "SA_length"),
      objects: [
        ...baseScene.objects,
        {
          id: "kq_res_alias",
          label: "Kết quả tham chiếu",
          notation: "d",
          type: "quantity",
          render: "readout",
          origin: "derived",
          depends: ["S", "A"],
          value: "4",
          annotation: {
            kind: "distance",
            category: "result",
            role: "result",
            subject_ids: ["S", "A"],
            anchor: "segment",
            same_as: "SA_length",
          },
        } as unknown as SceneObject,
      ],
      events: [
        ...baseScene.events,
        { step_index: baseScene.events.length, action: "MEASURE", object: "AB_length", depends: ["A", "B"], explanation: "" },
        { step_index: baseScene.events.length + 1, action: "MEASURE", object: "SA_length", depends: ["S", "A"], explanation: "" },
        {
          step_index: baseScene.events.length + 2,
          action: "MEASURE",
          semantic_kind: "FINAL_RESULT",
          object: "kq_res_alias",
          depends: ["S", "A"],
          explanation: "",
        },
      ],
    };

    const hiddenResults = tapKetQuaCuoi(sceneWithUntypedGivenMeasure);
    expect(hiddenResults.has("kq_res_alias")).toBe(true);
    expect(hiddenResults.has("AB_length")).toBe(false);
    expect(hiddenResults.has("SA_length")).toBe(false);

    const lastIdx = sceneWithUntypedGivenMeasure.events.length - 1;
    const sol = solutionAt(sceneWithUntypedGivenMeasure, lastIdx);
    expect(sol.results.map((r) => r.id)).toEqual(["kq_res_alias"]);

    const html = renderToString(
      <AxoWorkspaceV62
        scene={sceneWithUntypedGivenMeasure}
        de="Cho hình chóp S.ABC có SA vuông góc với mặt phẳng (ABC), AB = 2, SA = 4."
        tieuDe="Hình chóp S.ABC"
      />,
    );
    expect(html).toContain('data-ann-id="AB_length"');
    expect(html).toContain('data-ann-id="SA_length"');
    expect(html).not.toContain('data-ann-id="kq_res_alias"');
  });

  it("§12 Adversarial Review [F-02..F-05]: section chip identity (`CORPUS-DEV10`), oblique prism causality, `mp-vuong-goc-duong` target plane retention, `reproSabc` height step & epistemic badge, sphere radius anchor, studied-plane corner arcs, and oblique centroid perp leg", () => {
    // 1. [F-03.1..3] CORPUS-DEV10-prism-area: no `Thiết diện (HH1M)` chip, no `shortSym` from `o.id`, no standalone `Xác định điểm H` step
    const hybridRows = JSON.parse(
      readFileSync(
        resolve(
          __dirname,
          "../../../../../docs/evaluation/geometry/runs/hybrid-primary-b1-b2-offline/results/offline/fixtures.json",
        ),
        "utf8",
      ),
    ).fixtures as Array<Record<string, any>>;
    const dev10 = hybridRows.find((r) => String(r.id ?? r.case_id ?? "").includes("DEV10"))!;
    const dev10Plan = buildPedagogicalConstructionPlan(withSubEntities(veKhongGian(dev10.envelope.scene3d as Scene3D)));
    const dev10Section = dev10Plan.scene.objects.find((o) => o.type === "section")!;
    const sectionChip = formatCompactEntityChipLabel(dev10Plan.scene, dev10Section);
    expect(sectionChip).not.toContain("HH1M");
    expect(sectionChip).toBe("Thiết diện (α)");
    expect(dev10Plan.steps.some((s) => /\bđiểm\s+H\b/iu.test(s.title))).toBe(false);

    const unnamedDescriptivePoint = {
      id: "H1",
      type: "point3",
      label: "Giao điểm của BB′ và (α)",
      origin: "derived",
      render: "point_marker",
      depends: [],
      xyz: ["1", "0", "1/2"],
    } as unknown as SceneObject;
    expect(shortSym(unnamedDescriptivePoint)).toBe("Giao điểm của BB′ và (α)");

    // 2. [F-04.3 & F-04.5] reproSabc: explicit backend `"Dựng đường cao SA."` stays its own step before `SB, SC`, and solid closure on uncertified `LAYOUT_DERIVED` vertices is `constructed` (never `given` / "Đề cho")
    const sabcRaw = buildMandatorySabcScene({ withContractRolesAndWitness: false });
    const sabcPlan = buildPedagogicalConstructionPlan(withSubEntities(sabcRaw));
    expect(sabcPlan.steps.map((s) => s.title)).toEqual([
      "Dựng mặt đáy ABC",
      "Dựng đường cao SA",
      "Dựng các cạnh bên SB, SC",
      "Hoàn thiện hình chóp S.ABC",
    ]);
    const sabcSolidStep = sabcPlan.steps[sabcPlan.steps.length - 1]!;
    expect(sabcSolidStep.epistemicCategory).toBe("constructed");

    // 3. [F-04.1 & F-05.3] Oblique prism (`A′G ⊥ (ABC)` at centroid `G`): `ABC` -> `G` -> `A′G` -> `A′B′C′`, and perp marker at `G` aligns along drawn median instead of pointing into empty space
    const obliquePrismScene: Scene3D = {
      free_objects: ["A", "B", "C", "A_prime", "B_prime", "C_prime"],
      objects: [
        makePoint("A", ["0", "0", "0"], { provenance: "LAYOUT_DERIVED" }),
        makePoint("B", ["3", "0", "0"], { provenance: "LAYOUT_DERIVED" }),
        makePoint("C", ["0", "3", "0"], { provenance: "LAYOUT_DERIVED" }),
        makePoint("A_prime", ["1", "1", "4"], { notation: "A′", provenance: "LAYOUT_DERIVED" }),
        makePoint("B_prime", ["4", "1", "4"], { notation: "B′", provenance: "LAYOUT_DERIVED" }),
        makePoint("C_prime", ["1", "4", "4"], { notation: "C′", provenance: "LAYOUT_DERIVED" }),
        {
          id: "M_ab",
          label: "Trung điểm AB",
          type: "point3",
          origin: "derived",
          render: "point_marker",
          depends: ["A", "B"],
          xyz: ["3/2", "0", "0"],
        } as unknown as SceneObject,
        {
          id: "med_cm",
          label: "Trung tuyến",
          type: "segment3",
          origin: "derived",
          render: "segment",
          depends: ["C", "M_ab"],
          endpoint_ids: ["C", "M_ab"],
          point_a: ["0", "3", "0"],
          point_b: ["3/2", "0", "0"],
        } as unknown as SceneObject,
        {
          id: "G",
          label: "Trọng tâm G",
          notation: "G",
          type: "point3",
          origin: "derived",
          render: "point_marker",
          depends: ["A", "B", "C"],
          xyz: ["1", "1", "0"],
        } as unknown as SceneObject,
        {
          id: "h_a_prime_g",
          label: "A′G",
          notation: "A′G",
          type: "segment3",
          origin: "derived",
          render: "segment",
          depends: ["A_prime", "G"],
          endpoint_ids: ["A_prime", "G"],
          point_a: ["1", "1", "4"],
          point_b: ["1", "1", "0"],
          perpendicular_witness: {
            relation: "line_perp_plane",
            from: "A_prime",
            foot_id: "G",
            foot: ["1", "1", "0"],
            on: "lang_tru",
            can_present_as_proven: true,
            marker: { u: ["1", "0", "0"], v: ["0", "0", "4"] },
          },
        } as unknown as SceneObject,
        {
          id: "lang_tru",
          label: "Hình lăng trụ xiên ABC.A′B′C′",
          notation: "ABC.A′B′C′",
          shape_class: "PRISM_LIKE",
          type: "solid",
          origin: "derived",
          render: "mesh",
          depends: ["A", "B", "C", "A_prime", "B_prime", "C_prime"],
          vertex_ids: ["A", "B", "C", "A_prime", "B_prime", "C_prime"],
          vertices: [
            ["0", "0", "0"],
            ["3", "0", "0"],
            ["0", "3", "0"],
            ["1", "1", "4"],
            ["4", "1", "4"],
            ["1", "4", "4"],
          ],
          faces: [
            [0, 1, 2],
            [3, 4, 5],
            [0, 1, 4, 3],
            [1, 2, 5, 4],
            [2, 0, 3, 5],
          ],
        } as unknown as SceneObject,
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "M_ab", depends: ["A", "B"], explanation: "" },
        { step_index: 1, action: "CREATE", object: "med_cm", depends: ["C", "M_ab"], explanation: "" },
        { step_index: 2, action: "CREATE", object: "G", depends: ["A", "B", "C"], explanation: "" },
        { step_index: 3, action: "CREATE", object: "h_a_prime_g", depends: ["A_prime", "G"], explanation: "" },
        { step_index: 4, action: "CREATE", object: "lang_tru", depends: ["A", "B", "C", "A_prime", "B_prime", "C_prime"], explanation: "" },
      ],
    } as unknown as Scene3D;
    const obPlan = buildPedagogicalConstructionPlan(withSubEntities(obliquePrismScene));
    const idxBase = obPlan.steps.findIndex((s) => /mặt đáy ABC/iu.test(s.title));
    const idxG = obPlan.steps.findIndex((s) => /trọng tâm G/iu.test(s.title));
    const idxAG = obPlan.steps.findIndex((s) => /A′G/u.test(s.title));
    const idxTop = obPlan.steps.findIndex((s) => /A′B′C′/u.test(s.title));
    expect(idxBase).toBeGreaterThanOrEqual(0);
    expect(idxG).toBeGreaterThan(idxBase);
    expect(idxAG).toBeGreaterThan(idxG);
    expect(idxTop).toBeGreaterThan(idxAG);
    expect(obPlan.steps[obPlan.steps.length - 1]!.epistemicCategory).toBe("constructed");

    const hBuilt = buildObject3D(
      obPlan.scene.objects.find((o) => o.id === "h_a_prime_g")!,
      false,
      undefined,
      [
        [0, 0, 0],
        [3, 0, 0],
        [0, 3, 0],
        [1, 1, 4],
      ],
      undefined,
      undefined,
      undefined,
      false,
      "primary",
      true,
      true,
      false,
      obPlan.scene,
    )!;
    const perpMarker = hBuilt.getObjectByName("perp_marker:h_a_prime_g") as THREE.Line;
    expect(perpMarker).toBeDefined();
    const uUnit = (perpMarker.userData.gocVuongDonVi as { u: [number, number, number] }).u;
    // Median direction through G=(1,1,0) toward C=(0,3,0) is proportional to (-1, 2, 0), NOT raw (1, 0, 0)!
    const cosMedian = Math.abs(-1 * uUnit[0] + 2 * uUnit[1]) / Math.hypot(-1, 2);
    expect(cosMedian).toBeGreaterThan(0.999);

    // 4. [F-04.2 & F-04.4] `mp-vuong-goc-duong`: target plane `mpb` (`(α)`) remains visible at final step (`aux=0`), and line `sc` chip is `"Đường thẳng SC"` (never `"đt SC"`)
    const mpSample = GEOMETRY_SAMPLES.find((s) => s.id === "mp-vuong-goc-duong")!;
    const mpPlan = buildPedagogicalConstructionPlan(
      withSubEntities((mpSample.envelope as unknown as { scene3d: Scene3D }).scene3d),
    );
    const mpLastAnchor = mpPlan.steps[mpPlan.steps.length - 1]!.anchor;
    expect(mpLastAnchor).toBeGreaterThan(0);
    expect(auxiliaryHiddenAt(mpPlan.scene, mpLastAnchor, false, null).has("mpb")).toBe(false);
    const scLine = mpPlan.scene.objects.find((o) => o.id === "sc")!;
    expect(formatCompactEntityChipLabel(mpPlan.scene, scLine)).toBe("Đường thẳng SC");

    // 5. [F-05.1] `cau-cat-mat-phang`: `R = 5` anchors onto segment `IM` at final step (never floating `anchor: "solid"`)
    const cauSample = GEOMETRY_SAMPLES.find((s) => s.id === "cau-cat-mat-phang")!;
    const cauPlan = buildPedagogicalConstructionPlan(
      withSubEntities((cauSample.envelope as unknown as { scene3d: Scene3D }).scene3d),
    );
    const cauFinalAnchor = cauPlan.steps[cauPlan.steps.length - 1]!.anchor;
    expect(cauFinalAnchor).toBeGreaterThan(0);
    const cauAnns = annotationsAt(cauPlan.scene, cauFinalAnchor, DEFAULT_ANNOTATION_VIEW, null);
    const rAnn = cauAnns.find((a) => a.text.includes("R = 5") || a.id === "R")!;
    expect(rAnn).toBeDefined();
    expect(rAnn.anchor).toBe("segment");

    // 6. [F-05.2] Studied plane through solid vertices (`(SAC)` / `(SBD)`) never attaches `plane_corner_arc:` with `depthTest: false`
    const studiedPlaneScene: Scene3D = {
      free_objects: ["S", "A", "B", "C", "D"],
      objects: [
        makePoint("A", ["0", "0", "0"]),
        makePoint("B", ["4", "0", "0"]),
        makePoint("C", ["4", "4", "0"]),
        makePoint("D", ["0", "4", "0"]),
        makePoint("S", ["0", "0", "5"]),
        {
          id: "chop",
          type: "solid",
          label: "S.ABCD",
          notation: "S.ABCD",
          origin: "derived",
          render: "mesh",
          depends: ["S", "A", "B", "C", "D"],
          vertex_ids: ["S", "A", "B", "C", "D"],
          vertices: [["0", "0", "5"], ["0", "0", "0"], ["4", "0", "0"], ["4", "4", "0"], ["0", "4", "0"]],
          faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]],
        } as unknown as SceneObject,
        {
          id: "mp_sac",
          type: "plane3",
          label: "(SAC)",
          notation: "(SAC)",
          origin: "derived",
          render: "surface",
          depends: ["S", "A", "C"],
          point: ["0", "0", "0"],
          normal: ["1", "-1", "0"],
        } as unknown as SceneObject,
        {
          id: "mp_sbd",
          type: "plane3",
          label: "(SBD)",
          notation: "(SBD)",
          origin: "derived",
          render: "surface",
          depends: ["S", "B", "D"],
          point: ["4", "0", "0"],
          normal: ["1", "1", "0"],
        } as unknown as SceneObject,
      ],
      events: [],
    } as unknown as Scene3D;
    const builtSac = buildObject3D(
      studiedPlaneScene.objects.find((o) => o.id === "mp_sac")!,
      false,
      undefined,
      [[0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 4, 0], [0, 0, 5]],
      undefined,
      undefined,
      undefined,
      false,
      "primary",
      false,
      true,
      false,
      studiedPlaneScene,
    )!;
    let foundCornerArc = false;
    builtSac.traverse((child) => {
      if (child.name.startsWith("plane_corner_arc:")) foundCornerArc = true;
    });
    expect(foundCornerArc).toBe(false);
  });
});
