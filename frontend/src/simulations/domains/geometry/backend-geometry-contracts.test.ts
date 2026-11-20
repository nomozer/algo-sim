import { describe, expect, it } from "vitest";
import rawSamplesFile from "../../../data/advanced-geometry-samples.json";
import rawCircumsphereFixture from "./scene3d-circumsphere-fixture.json";
import rawArchetypesFixture from "./scene3d-regression-archetypes-fixtures.json";
import rawCoplanarSectionsFixture from "./__fixtures__/coplanar-euclidean-sections.fixture.json";
import {
  hienBieuThucDaiLuong,
  isVectorLeakString,
  resolveCertifiedMeasuredRelation,
  resolveVisualPrerequisitesOf,
  type Scene3D,
  type SceneObject,
} from "./scene3d-model";
import { sectionDetails, withSubEntities } from "./scene3d-subentities";
import {
  buildPedagogicalConstructionPlan,
  classifySceneAuxiliaryUsage,
  describeConstructionLineageForLearner,
  getSemanticConstructionContract,
  inspectMeasuredQuantityContract,
  resolveCanonicalSectionDesignation,
  resolveStudentObjectPresentation,
  verifyVisualContinuity,
} from "./scene3d-semantic-policy";
import { dependencyClosure, directDependencies } from "./interaction-state";

interface SampleEntry {
  id: string;
  group: string;
  envelope: {
    scene3d?: Scene3D;
    simulation?: { scene3d?: Scene3D };
  };
}

function sceneFromEntry(entry: SampleEntry): Scene3D {
  const sc = entry.envelope.simulation?.scene3d ?? entry.envelope.scene3d;
  if (!sc) throw new Error(`Missing scene3d in sample ${entry.id}`);
  return sc;
}

const SAMPLES = (rawSamplesFile as unknown as { khai: string; samples: SampleEntry[]; zero_measure_audit?: unknown[] }).samples;
const ZERO_MEASURE_AUDIT = (
  rawSamplesFile as unknown as {
    zero_measure_audit?: Array<{
      sample_id: string;
      object: string;
      measured_quantity: {
        quantity_kind: string;
        value: string;
        certified_relation: string | null;
      };
    }>;
  }
).zero_measure_audit ?? [];
const COPLANAR_SAMPLES = (rawCoplanarSectionsFixture as unknown as { samples: SampleEntry[] }).samples;

describe("Backend Geometry Contracts Integration", () => {
  it("preserves all 11 baseline sample IDs and top-level khai metadata", () => {
    expect((rawSamplesFile as { khai?: string }).khai).toBeTruthy();
    expect(SAMPLES).toHaveLength(11);
    const byId = new Set(SAMPLES.map((s) => s.id));
    expect(byId.has("chop-thiet-dien-ba-diem")).toBe(true);
    expect(byId.has("lap-phuong-thiet-dien-bat-ky")).toBe(true);
    expect(byId.has("chop-mat-cau-ngoai-tiep")).toBe(true);
  });

  it("handles all four construction_lineage modes cleanly and preserves algebraic limitations", () => {
    const chopSample = SAMPLES.find((s) => s.id === "chop-thiet-dien-ba-diem")!;
    const chopScene = sceneFromEntry(chopSample);
    const oObj = chopScene.objects.find((o) => o.id === "O")!;
    const eObj = chopScene.objects.find((o) => o.id === "E")!;

    const directSummary = describeConstructionLineageForLearner(chopScene, oObj);
    expect(directSummary.mode).toBe("direct_euclidean_primitive");
    expect(directSummary.isEuclidean).toBe(true);
    expect(directSummary.isAlgebraic).toBe(false);

    const algebraicSummary = describeConstructionLineageForLearner(chopScene, eObj);
    expect(algebraicSummary.mode).toBe("algebraic_line_plane_intersection");
    expect(algebraicSummary.isAlgebraic).toBe(true);
    expect(algebraicSummary.isEuclidean).toBe(false);
    expect(algebraicSummary.hasPedagogicalLimitation).toBe(true);
    expect(algebraicSummary.rawLimitation).toContain("đồng phẳng");
    expect(algebraicSummary.learnerNote).toBeTruthy();

    const coplanarChop = COPLANAR_SAMPLES.find((s) => s.id === "chop-thiet-dien-ba-diem")!;
    const coplanarScene = sceneFromEntry(coplanarChop);
    const i1Obj = coplanarScene.objects.find((o) => o.id === "I1")!;
    const euclidSummary = describeConstructionLineageForLearner(coplanarScene, i1Obj);
    expect(euclidSummary.mode).toBe("euclidean_coplanar_intersection");
    expect(euclidSummary.isEuclidean).toBe(true);
    expect(euclidSummary.isAlgebraic).toBe(false);
    expect(euclidSummary.learnerNote).toContain("NP");

    const circum = rawCircumsphereFixture as unknown as Scene3D;
    const aPrime = circum.objects.find((o) => o.id === "A_prime")!;
    const vecSummary = describeConstructionLineageForLearner(circum, aPrime);
    expect(vecSummary.mode).toBe("vector_translation");
    expect(vecSummary.isVectorTranslation).toBe(true);
    expect(vecSummary.learnerNote).not.toContain("vec_");
  });

  it("separates visible_prerequisites from computational_depends without breaking causal selection or weakening CAUSAL_BIRTH_ORDER", () => {
    const circum = rawCircumsphereFixture as unknown as Scene3D;
    const aPrime = circum.objects.find((o) => o.id === "A_prime")!;
    const dObj = circum.objects.find((o) => o.id === "D")!;

    expect(resolveVisualPrerequisitesOf(circum, aPrime)).toEqual(["A", "B", "O"]);
    expect(resolveVisualPrerequisitesOf(circum, dObj)).toEqual(["A_prime", "C", "O"]);
    expect(directDependencies(circum, "A_prime")).toEqual(["A", "vec_OB"]);
    expect(dependencyClosure(circum, "D")).toContain("vec_OB");

    const contract = getSemanticConstructionContract(circum);
    expect(contract.objectsById.get("A_prime")?.prerequisiteIds).toEqual(["A", "B", "O"]);
    expect(contract.objectsById.get("D")?.prerequisiteIds).toEqual(["A_prime", "C", "O"]);

    const continuity = verifyVisualContinuity(withSubEntities(circum));
    expect(continuity.valid, JSON.stringify(continuity.violations)).toBe(true);

    const broken = structuredClone(circum);
    const brokenAPrime = broken.objects.find((o) => o.id === "A_prime")!;
    delete brokenAPrime.visible_prerequisites;
    delete brokenAPrime.construction_lineage;
    delete brokenAPrime.dependency_edges;
    const brokenContinuity = verifyVisualContinuity(broken);
    expect(brokenContinuity.valid).toBe(false);
    expect(brokenContinuity.violations.some((v) => v.detail.includes("CAUSAL_BIRTH_ORDER") && v.objectId === "A_prime")).toBe(true);

    // Even when visible_prerequisites IS provided, a visible prerequisite born AFTER A_prime still triggers CAUSAL_BIRTH_ORDER.
    const latePrereqScene = structuredClone(circum);
    const evA = latePrereqScene.events.find((e) => e.object === "A_prime")!;
    const evB = latePrereqScene.events.find((e) => e.object === "B");
    if (evB) {
      evB.step_index = evA.step_index + 1;
    } else {
      const aObj = latePrereqScene.objects.find((o) => o.id === "A_prime")!;
      aObj.visible_prerequisites = [...(aObj.visible_prerequisites ?? []), "D"];
    }
    const lateContinuity = verifyVisualContinuity(latePrereqScene);
    expect(lateContinuity.valid).toBe(false);
    expect(lateContinuity.violations.some((v) => v.detail.includes("CAUSAL_BIRTH_ORDER") && v.objectId === "A_prime")).toBe(true);

    const chopMatCau = sceneFromEntry(SAMPLES.find((s) => s.id === "chop-mat-cau-ngoai-tiep")!);
    const chopMatCauContinuity = verifyVisualContinuity(withSubEntities(chopMatCau));
    expect(chopMatCauContinuity.valid, JSON.stringify(chopMatCauContinuity.violations)).toBe(true);
  });

  it("consumes measured_quantity metadata, certifies zero-measure perpendicularity only when explicitly certified, and blocks Vec3 leaks", () => {
    const seenKinds = new Set<string>();
    const inspectedZeroObjects: string[] = [];

    for (const s of SAMPLES) {
      const sc = sceneFromEntry(s);
      for (const obj of sc.objects) {
        if (!obj.measured_quantity) continue;
        seenKinds.add(obj.measured_quantity.quantity_kind);
        const inspected = inspectMeasuredQuantityContract(sc, obj)!;
        expect(inspected.hasVectorLeak).toBe(false);
        if (inspected.isZeroMeasure && inspected.isCertifiedPerpendicular) {
          inspectedZeroObjects.push(`${s.id}:${obj.id}`);
        }
      }
    }

    for (const kind of ["distance", "angle_cos_sq", "volume", "area", "radius"]) {
      expect(seenKinds.has(kind)).toBe(true);
    }
    expect(ZERO_MEASURE_AUDIT.length).toBeGreaterThanOrEqual(11);
    for (const entry of ZERO_MEASURE_AUDIT) {
      const sc = sceneFromEntry(SAMPLES.find((s) => s.id === entry.sample_id)!);
      const qObj = sc.objects.find((o) => o.id === entry.object)!;
      const inspected = inspectMeasuredQuantityContract(sc, qObj)!;
      expect(inspected.quantityKind).toBe(entry.measured_quantity.quantity_kind);
      expect(inspected.isZeroMeasure).toBe(true);
      expect(inspected.isCertifiedPerpendicular).toBe(true);
    }
    expect(inspectedZeroObjects.length).toBeGreaterThanOrEqual(11);

    const uncertifiedZero: SceneObject = {
      id: "qty_unverified_zero",
      type: "quantity",
      label: "cos²(AB, CD)",
      render: "readout",
      origin: "derived",
      producer: null,
      depends: ["ab", "cd"],
      value: "0",
      measured_quantity: {
        quantity_kind: "angle_cos_sq",
        subject_ids: ["ab", "cd"],
        value: "0",
        certified_relation: null,
      },
    };
    const mockScene: Scene3D = {
      objects: [uncertifiedZero],
      events: [],
      free_objects: [],
    };
    expect(resolveCertifiedMeasuredRelation(uncertifiedZero)).toBeNull();
    expect(inspectMeasuredQuantityContract(mockScene, uncertifiedZero)?.isCertifiedPerpendicular).toBe(false);

    const leakedVecObj: SceneObject = {
      id: "qty_vec_leak",
      type: "quantity",
      label: "Giá trị nội bộ",
      render: "readout",
      origin: "derived",
      producer: null,
      depends: [],
      value: "Vec3(1, 2, 3)",
      measured_quantity: {
        quantity_kind: "distance",
        subject_ids: [],
        value: "Vec3(1, 2, 3)",
        certified_relation: null,
      },
    };
    expect(isVectorLeakString("Vec3(1, 2, 3)")).toBe(true);
    expect(hienBieuThucDaiLuong(leakedVecObj)).toBeNull();
    expect(inspectMeasuredQuantityContract({ objects: [leakedVecObj], events: [], free_objects: [] }, leakedVecObj)).toMatchObject({
      hasVectorLeak: true,
      displayValue: null,
    });
  });

  it("uses ordered_vertex_ids, ordered_vertex_symbols, and ordered_boundary_edges without truncation or reversing cycles", () => {
    const expectedSections: Array<{ id: string; cycle: string; edges: string[] }> = [
      { id: "chop-thiet-dien-ba-diem", cycle: "MENPF", edges: ["ME", "EN", "NP", "PF", "FM"] },
      { id: "lap-phuong-thiet-dien-bat-ky", cycle: "MNEPFQ", edges: ["MN", "NE", "EP", "PF", "FQ", "QM"] },
      { id: "lang-tru-tam-giac-thiet-dien", cycle: "MNPQE", edges: ["MN", "NP", "PQ", "QE", "EM"] },
    ];

    for (const exp of expectedSections) {
      const sample = SAMPLES.find((s) => s.id === exp.id)!;
      const sc = withSubEntities(sceneFromEntry(sample));
      const sec = sc.objects.find((o) => o.type === "section")!;
      const canon = resolveCanonicalSectionDesignation(sc, sec)!;
      expect(canon.source).toBe("ordered_vertex_symbols");
      expect(canon.compactLabel).toBe(exp.cycle);
      expect(canon.notation).toBe(`(${exp.cycle})`);
      expect(canon.boundaryEdges).toEqual(exp.edges);
      expect(canon.vertexIds).toEqual(sec.ordered_vertex_ids);
      expect(sectionDetails(sc, sec.id)?.vertexNames).toEqual([...exp.cycle]);

      const pres = resolveStudentObjectPresentation(sc, sec.id, sc.events.length - 1)!;
      expect(pres.title).toBe(`Thiết diện (${exp.cycle})`);
    }
  });

  it("verifies GEO-BE-V9415-004 fix on coincident_elements_pyramid", () => {
    const coinc = (
      rawArchetypesFixture as unknown as {
        coincident_elements_pyramid: { scene3d: Scene3D };
      }
    ).coincident_elements_pyramid.scene3d;

    const sbIdx = coinc.events.findIndex((e) => e.action === "CREATE" && e.object === "SB_line");
    const mIdx = coinc.events.findIndex((e) => e.action === "CREATE" && e.object === "M");
    const kIdx = coinc.events.findIndex((e) => e.action === "CREATE" && e.object === "K");
    expect(sbIdx).toBeGreaterThanOrEqual(0);
    expect(mIdx).toBeGreaterThan(sbIdx);
    expect(kIdx).toBeGreaterThan(mIdx);
    expect(coinc.formation?.steps?.every((st) => Array.isArray(st.readout_ids))).toBe(true);

    const continuity = verifyVisualContinuity(withSubEntities(coinc));
    expect(continuity.valid, JSON.stringify(continuity.violations)).toBe(true);
  });

  it("preserves unused_auxiliary_ids (such as center O) as audit metadata without deleting them from Scene Graph", () => {
    const chopSample = SAMPLES.find((s) => s.id === "chop-thiet-dien-ba-diem")!;
    const chopScene = sceneFromEntry(chopSample);
    expect(chopScene.unused_auxiliary_ids).toEqual(["O"]);

    const audit = classifySceneAuxiliaryUsage(chopScene);
    expect(audit.unusedAuxiliaryAuditIds).toEqual(["O"]);
    expect(audit.allUnusedRetainedInScene).toBe(true);
    expect(audit.retainedSceneGivenIds).toContain("O");

    const plan = buildPedagogicalConstructionPlan(withSubEntities(chopScene));
    const oObj = plan.scene.objects.find((o) => o.id === "O");
    expect(oObj).toBeDefined();
    expect(oObj?.render).not.toBe("non_visual");
  });

  it("evaluates the three coplanar Euclidean section variants cleanly without replacing the 11-sample baseline", () => {
    expect(COPLANAR_SAMPLES).toHaveLength(3);
    const reportRows: Array<{
      id: string;
      computationalEvents: number;
      formationSteps: number;
      studentVisibleSteps: number;
      baselineEvents: number;
      baselineStudentSteps: number;
      valid: boolean;
    }> = [];

    for (const entry of COPLANAR_SAMPLES) {
      const euclidScene = withSubEntities(sceneFromEntry(entry));
      const baseEntry = SAMPLES.find((s) => s.id === entry.id)!;
      const baseScene = withSubEntities(sceneFromEntry(baseEntry));

      const continuity = verifyVisualContinuity(euclidScene);
      expect(continuity.valid, `${entry.id} continuity: ${JSON.stringify(continuity.violations)}`).toBe(true);

      const euclidPlan = buildPedagogicalConstructionPlan(euclidScene);
      const basePlan = buildPedagogicalConstructionPlan(baseScene);

      expect(euclidPlan.steps.length).toBeGreaterThan(0);
      expect(euclidPlan.steps.length).toBeLessThanOrEqual(euclidScene.events.length);
      expect(euclidScene.events.some((ev) => ev.action === "CREATE" && euclidScene.objects.some((o) => o.id === ev.object && o.construction_lineage?.mode === "euclidean_coplanar_intersection"))).toBe(true);

      reportRows.push({
        id: entry.id,
        computationalEvents: euclidScene.events.length,
        formationSteps: euclidScene.formation?.steps?.length ?? 0,
        studentVisibleSteps: euclidPlan.steps.length,
        baselineEvents: baseScene.events.length,
        baselineStudentSteps: basePlan.steps.length,
        valid: continuity.valid,
      });
    }

    expect(reportRows.map((r) => [r.id, r.computationalEvents])).toEqual([
      ["chop-thiet-dien-ba-diem", 29],
      ["lap-phuong-thiet-dien-bat-ky", 30],
      ["lang-tru-tam-giac-thiet-dien", 29],
    ]);
  });
});
