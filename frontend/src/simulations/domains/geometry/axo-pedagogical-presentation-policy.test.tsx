import { describe, expect, it, vi, afterEach } from "vitest";
import { renderToString } from "react-dom/server";
import {
  classifySceneEntityProvenance,
  objectsAt,
  phanTichToanHocCuaCanh,
  registerExactSceneOrigin,
  type Scene3D,
  type SceneObject,
} from "./scene3d-model";
import { veKhongGian } from "./scene3d-chart";
import { withSubEntities } from "./scene3d-subentities";
import { annotationsAt, DEFAULT_ANNOTATION_VIEW, givenQuantitiesSummary } from "./scene3d-annotations";
import { auxiliaryHiddenAt } from "./scene3d-auxiliary";
import {
  buildPedagogicalConstructionPlan,
  buildVerifiedObjectTooltip,
  classifyPolygonShapeWithProvenance,
  classifyScenePolygonShape,
  formatCompactEntityChipLabel,
  isAuxiliaryExplanatoryPolygon,
  resolvePlaneSectionVisibility,
  resolveStepVisualRoles,
  verifySceneMathematicalConsistency,
} from "./scene3d-semantic-policy";
import {
  classifySimulationEntityCategory,
  evaluateStudentPresentationPolicy,
  sanitizeStudentDescriptorText,
  type SimulationInformationCategory,
} from "./scene3d-student-presentation-policy";
import { buildObject3D, setWebGLRendererFactoryForTest } from "./scene3d-view";
import * as THREE from "three";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import App from "../../../App";
import { registerAllSimulations } from "../../index";
import { useAppStore } from "../../../state/store";

registerAllSimulations();

function syncStoreForSSR() {
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
}

function loadCatalogScene(sampleId: string): { raw: Scene3D; world: Scene3D; desc: string; title: string } {
  const sample = GEOMETRY_SAMPLES.find((s) => s.id === sampleId);
  if (!sample) throw new Error(`Missing sample: ${sampleId}`);
  const raw = structuredClone((sample.envelope as unknown as { scene3d: Scene3D }).scene3d);
  const world = veKhongGian(raw);
  registerExactSceneOrigin(world, raw);
  return {
    raw,
    world: withSubEntities(world),
    desc: sample.envelope.description ?? sample.problemText,
    title: sample.envelope.title ?? sampleId,
  };
}

describe("AXO Pedagogical Simulation Presentation Policy & Cross-Family Verification", () => {
  afterEach(() => {
    setWebGLRendererFactoryForTest(null);
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe("11.A — Contract Tests: 5-Part Simulation Information Policy", () => {
    it("separates GIVEN_FACT, CONSTRUCTION_OBJECT, GEOMETRIC_CONSTRUCTION_RELATION, and INTERNAL_MATH_RESULT while retaining full Engine verification", () => {
      const { raw, world } = loadCatalogScene("cau-cat-mat-phang");
      const plan = buildPedagogicalConstructionPlan(world);

      // Engine & internal GoalCompletion retain verified r = 4 and S = 16π
      expect(plan.goalCompletion.status).toBe("reached");
      expect(plan.goalCompletion.items.map((it) => it.valueText)).toEqual(["4", "16π"]);
      const analysis = phanTichToanHocCuaCanh(raw, null);
      expect(analysis.requestedResults.length).toBeGreaterThanOrEqual(2);

      const byId = new Map(plan.scene.objects.map((o) => [o.id, o]));
      const qR = byId.get("R")!;
      const circ = byId.get("C")!;
      const hPt = byId.get("C__center")!;
      const ihSeg = byId.get("C__dist")!;
      const resR = byId.get("r")!;
      const resS = byId.get("S")!;

      const validCategories = new Set<SimulationInformationCategory>([
        "GIVEN_FACT",
        "CONSTRUCTION_OBJECT",
        "GEOMETRIC_CONSTRUCTION_RELATION",
        "INTERNAL_MATH_RESULT",
      ]);
      for (const o of [qR, circ, hPt, ihSeg, resR, resS]) {
        expect(validCategories.has(classifySimulationEntityCategory(plan.scene, o))).toBe(true);
      }

      expect(classifySimulationEntityCategory(plan.scene, qR)).toBe("GIVEN_FACT");
      expect(classifySimulationEntityCategory(plan.scene, circ)).toBe("CONSTRUCTION_OBJECT");
      expect(classifySimulationEntityCategory(plan.scene, ihSeg)).toBe("GEOMETRIC_CONSTRUCTION_RELATION");
      expect(classifySimulationEntityCategory(plan.scene, resR)).toBe("INTERNAL_MATH_RESULT");
      expect(classifySimulationEntityCategory(plan.scene, resS)).toBe("INTERNAL_MATH_RESULT");

      // Presentation policy blocks INTERNAL_MATH_RESULT on student simulation surfaces
      const policy = evaluateStudentPresentationPolicy(plan.scene, plan.goalCompletion);
      expect(policy.showMathResultsPanel).toBe(false);
      expect(policy.canDisplayEntityValue(qR)).toBe(true);
      expect(policy.canDisplayEntityValue(resR)).toBe(false);
      expect(policy.canDisplayEntityValue(resS)).toBe(false);
      expect(policy.canRenderGeometricObject(circ)).toBe(true);
      expect(policy.canRenderGeometricObject(ihSeg)).toBe(true);
    });
  });

  describe("11.B — Anti-Answer-Leak Tests Across All Student Surfaces", () => {
    it("never leaks #dock-math-results, 'KẾT QUẢ TOÁN HỌC', 'Đã xác minh', numeric answers, intermediate readouts, or algebraic formulas across all 11 catalog samples", () => {
      const leakedTokensBySample: Record<string, string[]> = {
        "cau-cat-mat-phang": ["16π", "√(R² − d²)", "R² = d² + r²"],
        "cau-the-tich": ["36π", "4πR²", "4/3"],
        "non-duong-sinh": ["15π", "12π"],
        "tru-dung-the-tich": ["18π", "27π", "45π"],
        "chop-deu": ["16√2/3", "32/3"],
        "chop-canh-ben-vuong-goc": ["8/3", "4√3"],
        "lang-tru-tam-giac": ["9√3"],
        "khoang-cach-cheo-nhau": ["a√2/2", "√2/2"],
        "vuong-goc-chop": ["12/5", "6/5"],
      };

      for (const sample of GEOMETRY_SAMPLES) {
        const { world, desc, title } = loadCatalogScene(sample.id);
        const plan = buildPedagogicalConstructionPlan(world);

        // 1. Step list & subtitles never contain pure calculation steps or answer readouts
        for (const st of plan.steps) {
          expect(st.epistemicCategory, `${sample.id} step ${st.index}`).not.toBe("conclusion");
          expect(st.stepRole, `${sample.id} step ${st.index}`).not.toBe("conclude_and_calculate");
          const stepText = `${st.title} || ${st.subtitle} || ${st.premise}`;
          expect(stepText, `${sample.id} step ${st.index}`).not.toContain("R² = d² + r²");
          for (const tok of leakedTokensBySample[sample.id] ?? []) {
            if (!desc.includes(tok)) {
              expect(stepText, `${sample.id} step ${st.index} leaked ${tok}`).not.toContain(tok);
            }
          }
        }

        // 2. 3D annotations under student view only expose GIVEN quantities after policy hiddenIds filtering
        const finalAnchor = plan.steps[plan.steps.length - 1]!.anchor;
        const policy = evaluateStudentPresentationPolicy(plan.scene, plan.goalCompletion);
        const hiddenIds = new Set(
          plan.scene.objects
            .filter((o) => (o.type === "quantity" || o.render === "readout") && !policy.canDisplayEntityValue(o))
            .map((o) => o.id),
        );
        const anns = annotationsAt(
          plan.scene,
          finalAnchor,
          {
            ...DEFAULT_ANNOTATION_VIEW,
            hiddenIds,
          },
          null,
        ).filter((a) => !hiddenIds.has(a.id));
        for (const a of anns) {
          expect(a.role, `${sample.id} annotation ${a.id}`).toBe("given");
          expect(a.provenance, `${sample.id} annotation ${a.id}`).toBe("GIVEN");
        }

        // 3. Verified tooltips never leak algebraic formulas or final answers
        for (const o of plan.scene.objects) {
          if (o.id.includes("::")) continue;
          const tip = buildVerifiedObjectTooltip(plan.scene, o.id, finalAnchor);
          if (tip) {
            expect(`${tip.header} ${tip.body}`, `${sample.id} tooltip ${o.id}`).not.toContain("R² = d² + r²");
            for (const tok of leakedTokensBySample[sample.id] ?? []) {
              if (!desc.includes(tok)) {
                expect(`${tip.header} ${tip.body}`, `${sample.id} tooltip ${o.id} leaked ${tok}`).not.toContain(tok);
              }
            }
          }
        }

        // 4. Full AxoWorkspaceV62 SSR never renders #dock-math-results or 'KẾT QUẢ TOÁN HỌC' or 'Đã xác minh'
        const html = renderToString(
          <AxoWorkspaceV62 scene={plan.scene} de={desc} tieuDe={title} />,
        );
        expect(html, sample.id).not.toContain('id="dock-math-results"');
        expect(html, sample.id).not.toContain("KẾT QUẢ TOÁN HỌC");
        expect(html, sample.id).not.toContain("Đã xác minh");
        // Kể cả kết luận đã xác minh cũng không nằm trong DOM: luồng dựng hình không trình bày đáp án.
        for (const tok of leakedTokensBySample[sample.id] ?? []) {
          if (!desc.includes(tok)) {
            expect(html, `${sample.id} SSR leaked ${tok}`).not.toContain(tok);
          }
        }
      }
    });

    it("blocks intermediate/derived quantity values, coherentFormula derivations, and standalone MEASURE steps even when no title or construction step is provided", () => {
      const leakProbeScene: Scene3D = {
        free_objects: ["A", "B", "C", "q_ab"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
          {
            id: "q_ab",
            type: "quantity",
            label: "Độ dài AB",
            notation: "AB",
            origin: "free",
            producer: null,
            render: "readout",
            depends: ["A", "B"],
            value: "3",
            exact: { kind: "rational", value: "3" },
            source: { fact_id: "f_ab", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"],
            annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "B"], anchor: "segment" },
          },
          {
            id: "q_mid_area",
            type: "quantity",
            label: "Diện tích trung gian",
            notation: "S_mid",
            origin: "derived",
            producer: "measure_area",
            render: "readout",
            depends: ["A", "B", "C"],
            value: "6",
            exact: { kind: "rational", value: "6" },
            formula: {
              text: "S_mid = 1/2 · AB · AC = 6",
              references: [{ entity_id: "q_ab", display_label: "AB", relation: "numerical" }],
            },
            annotation: { kind: "area", category: "measurement", role: "intermediate", subject_ids: ["A", "B", "C"], anchor: "region" },
          },
          {
            id: "q_final_bc",
            type: "quantity",
            label: "Độ dài BC",
            notation: "BC",
            origin: "derived",
            producer: "measure_length",
            render: "readout",
            depends: ["B", "C"],
            value: "5",
            exact: { kind: "rational", value: "5" },
            annotation: { kind: "length", category: "result", role: "result", subject_ids: ["B", "C"], anchor: "segment" },
          },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "MEASURE", object: "q_mid_area", depends: ["A", "B", "C"], explanation: "" },
          { step_index: 2, action: "MEASURE", object: "q_final_bc", depends: ["B", "C"], explanation: "" },
        ],
      };

      const plan = buildPedagogicalConstructionPlan(withSubEntities(leakProbeScene));
      for (const st of plan.steps) {
        expect(st.epistemicCategory).not.toBe("conclusion");
        expect(`${st.title} ${st.subtitle}`).not.toContain("S_mid = 6");
        expect(`${st.title} ${st.subtitle}`).not.toContain("BC = 5");
      }

      const policy = evaluateStudentPresentationPolicy(plan.scene, plan.goalCompletion);
      const qMid = plan.scene.objects.find((o) => o.id === "q_mid_area")!;
      expect(classifySimulationEntityCategory(plan.scene, qMid)).toBe("INTERNAL_MATH_RESULT");
      expect(policy.canDisplayEntityValue(qMid)).toBe(false);
      expect(policy.canDisplayEntityFormula(qMid)).toBe(false);

      // Omit tieuDe so safeGoalTitle fallback is exercised — must NOT leak "5" from goalCompletion.headline
      const html = renderToString(<AxoWorkspaceV62 scene={plan.scene} de="Cho ba điểm A, B, C với AB = 3." />);
      expect(html).not.toContain("Độ dài BC: 5");
      expect(html).not.toContain("S_mid = 1/2");
      expect(html).not.toContain('id="dock-math-results"');
    });
  });

  describe("11.C — Sphere & Plane Mandatory Regression (Section 7)", () => {
    it("cau-cat-mat-phang: progresses step-by-step (S) -> (P) -> (H, IH) -> (M, IM, HM) -> (C) with ZERO answer/formula leak", () => {
      const { world, desc, title } = loadCatalogScene("cau-cat-mat-phang");
      const plan = buildPedagogicalConstructionPlan(world);
      expect(plan.steps.length).toBe(5);

      // Step 1: Sphere center I, R = 5 as GIVEN, no H/IH/C yet, no target results
      const s1Anchor = plan.steps[0]!.anchor;
      const s1Objs = new Set(objectsAt(plan.scene, s1Anchor).map((o) => o.id));
      expect(s1Objs.has("I")).toBe(true);
      expect(s1Objs.has("cau")).toBe(true);
      expect(s1Objs.has("P")).toBe(false);
      expect(s1Objs.has("C__center")).toBe(false);
      expect(s1Objs.has("C__dist")).toBe(false);
      expect(s1Objs.has("C")).toBe(false);
      const s1Givens = givenQuantitiesSummary(plan.scene, s1Anchor).map((g) => g.text);
      expect(s1Givens).toContain("R = 5");

      // Step 2: Cutting plane (P) introduced first before projection H/IH
      const s2Anchor = plan.steps[1]!.anchor;
      const s2Objs = new Set(objectsAt(plan.scene, s2Anchor).map((o) => o.id));
      expect(s2Objs.has("P")).toBe(true);
      expect(s2Objs.has("C__center")).toBe(false);
      expect(s2Objs.has("C__dist")).toBe(false);
      expect(s2Objs.has("C")).toBe(false);

      // Step 3: Exact projection foot H on (P), perpendicular segment IH ⊥ (P), and d(I, (P)) = 3 anchored on IH
      const s3Anchor = plan.steps[2]!.anchor;
      const s3Objs = new Set(objectsAt(plan.scene, s3Anchor).map((o) => o.id));
      const s3Hidden = auxiliaryHiddenAt(plan.scene, s3Anchor, false, null);
      expect(s3Objs.has("P")).toBe(true);
      expect(s3Objs.has("C__center")).toBe(true);
      expect(s3Objs.has("C__dist")).toBe(true);
      expect(s3Hidden.has("C__center")).toBe(false);
      expect(s3Hidden.has("C__dist")).toBe(false);
      expect(s3Objs.has("C")).toBe(false);
      expect(s3Objs.has("C__rim_pt")).toBe(false);

      const ihObj = plan.scene.objects.find((o) => o.id === "C__dist")!;
      expect(ihObj.perpendicular_witness?.can_present_as_proven).toBe(true);
      expect(ihObj.perpendicular_witness?.on).toBe("P");

      const s3Anns = annotationsAt(plan.scene, s3Anchor, DEFAULT_ANNOTATION_VIEW, null);
      const distAnnStep3 = s3Anns.find((a) => /d\(I,\s*\(P\)\)\s*=\s*3/u.test(a.text));
      expect(distAnnStep3).toBeDefined();
      expect(distAnnStep3?.anchor).toBe("segment");

      // Step 4: Certified rim point M and right-triangle legs IM, HM before closing (C)
      const s4Anchor = plan.steps[3]!.anchor;
      const s4Objs = new Set(objectsAt(plan.scene, s4Anchor).map((o) => o.id));
      expect(s4Objs.has("C__rim_pt")).toBe(true);
      expect(s4Objs.has("C__sec_rad")).toBe(true);
      expect(s4Objs.has("C__sph_rad")).toBe(true);
      expect(s4Objs.has("C")).toBe(false);

      // Step 5: Intersection circle C + observable I, H, M and segments IH, HM, IM; plane (P) attenuated; NO r=4, NO 16π, NO R²=d²+r², NO #dock-math-results
      const s5Anchor = plan.steps[4]!.anchor;
      const s5Objs = new Set(objectsAt(plan.scene, s5Anchor).map((o) => o.id));
      const s5Hidden = auxiliaryHiddenAt(plan.scene, s5Anchor, false, null);
      for (const id of ["I", "C", "C__center", "C__dist", "C__rim_pt", "C__sec_rad", "C__sph_rad"]) {
        expect(s5Objs.has(id), `${id} present at Step 5`).toBe(true);
        expect(s5Hidden.has(id), `${id} visible at Step 5`).toBe(false);
      }
      const s5Roles = resolveStepVisualRoles(plan.scene, s5Anchor);
      expect(s5Roles.get("C")?.role).toBe("PRIMARY");
      expect(s5Roles.get("P")?.role).toBe("SUPPORT");

      for (const stepIdx of [0, 1, 2, 3, 4]) {
        const stepHtml = renderToString(
          <AxoWorkspaceV62
            scene={plan.scene}
            initialStep={plan.steps[stepIdx]!.anchor}
            de={desc}
            tieuDe={title}
          />,
        );
        expect(stepHtml).not.toContain('id="dock-math-results"');
        // Không bước nào có nút xem kết quả hay đáp án trong DOM.
        expect(stepHtml).not.toContain('id="dock-goal-reveal"');
        expect(stepHtml).not.toContain('id="dock-goal-conclusion"');
        expect(stepHtml).not.toContain("16π");
        expect(stepHtml).not.toContain("√(R² − d²)");
        expect(stepHtml).not.toContain("R² = d² + r²");
      }
    });

    it("handles all 5 additional sphere–plane situations cleanly without hardcoding: tangent (d=R), non-intersecting (d>R), great circle (d=0), underdetermined, and contradictory", () => {
      // (a) Tangent plane (d = R = 5): slanted plane 3x + 4z - 25 = 0 touches sphere I=(0,0,0), R=5 at H=(3,0,4) with IH ⊥ (P)
      const tangentScene: Scene3D = {
        free_objects: ["O_sph", "q_rad"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "O_sph", type: "point3", label: "Tâm K", notation: "K", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "q_rad", type: "quantity", label: "Bán kính mặt cầu", notation: "R", origin: "free", producer: null, render: "readout", depends: ["ball_k"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f_r", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"] },
          { id: "ball_k", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: null, render: "curved_solid", depends: ["O_sph", "q_rad"], anchor: ["0", "0", "0"], radius_sq: "25" },
          { id: "mp_tan", type: "plane3", label: "Mặt phẳng tiếp diện (α)", notation: "(α)", origin: "derived", producer: null, render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["0", "0", "25/4"], normal: ["3", "0", "4"] },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "ball_k", depends: ["O_sph", "q_rad"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "mp_tan", depends: [], explanation: "" },
        ],
      };
      expect(verifySceneMathematicalConsistency(tangentScene).valid).toBe(true);
      const tanPlan = buildPedagogicalConstructionPlan(withSubEntities(tangentScene));
      const tanFoot = tanPlan.scene.objects.find((o) => o.type === "point3" && o.xyz?.join("|") === "3|0|4");
      const tanSeg = tanPlan.scene.objects.find((o) => o.type === "segment3" && o.perpendicular_witness?.on === "mp_tan");
      expect(tanFoot).toBeDefined();
      expect(tanSeg).toBeDefined();
      expect(tanSeg?.perpendicular_witness?.can_present_as_proven).toBe(true);

      // (b) Non-intersecting plane (d = 7 > R = 5): cutting plane fails mathematical consistency fail-closed
      const nonIntersectingScene: Scene3D = {
        free_objects: ["I"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "ball_i", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: null, render: "curved_solid", depends: ["I"], anchor: ["0", "0", "0"], radius_sq: "25" },
          { id: "mp_far", type: "plane3", label: "Mặt phẳng cắt (P)", notation: "(P)", origin: "derived", producer: null, render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["0", "0", "7"], normal: ["0", "0", "1"] },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "ball_i", depends: ["I"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "mp_far", depends: [], explanation: "" },
        ],
      };
      const nonInterVerif = verifySceneMathematicalConsistency(nonIntersectingScene);
      expect(nonInterVerif.valid).toBe(false);
      const nonInterHtml = renderToString(
        <AxoWorkspaceV62 scene={nonIntersectingScene} de="Mặt cầu tâm I bán kính 5 và mặt phẳng cắt cách tâm 7." />,
      );
      expect(nonInterHtml).toMatch(/không\s+cắt\s+mặt\s+cầu|mâu\s+thuẫn/iu);

      // (c) Plane through sphere center (d = 0, great circle): no zero-length IH segment, clean geometric description, rim radius shown
      const greatCircleScene: Scene3D = {
        free_objects: ["I", "q_r0"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "q_r0", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["ball_0"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f0", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"] },
          { id: "ball_0", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: null, render: "curved_solid", depends: ["I", "q_r0"], anchor: ["0", "0", "0"], radius_sq: "25" },
          { id: "mp_0", type: "plane3", label: "Mặt phẳng (P)", notation: "(P)", origin: "derived", producer: null, render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["0", "0", "0"], normal: ["0", "0", "1"] },
          { id: "c_great", type: "circle3", label: "Đường tròn lớn", origin: "derived", producer: null, render: "circle", surface_role: "SECTION_REGION", depends: ["ball_0", "mp_0"], center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "25" },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "ball_0", depends: ["I", "q_r0"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "mp_0", depends: [], explanation: "" },
          { step_index: 3, action: "CREATE", object: "c_great", depends: ["ball_0", "mp_0"], explanation: "" },
        ],
      };
      expect(verifySceneMathematicalConsistency(greatCircleScene).valid).toBe(true);
      const greatPlan = buildPedagogicalConstructionPlan(withSubEntities(greatCircleScene));
      expect(greatPlan.scene.objects.find((o) => o.id === "c_great__dist")).toBeUndefined();
      expect(greatPlan.scene.objects.find((o) => o.id === "c_great__sph_rad")).toBeDefined();
      expect(greatPlan.steps[greatPlan.steps.length - 1]!.subtitle).toMatch(/đường\s+tròn\s+lớn/iu);
      expect(greatPlan.steps[greatPlan.steps.length - 1]!.subtitle).not.toContain("(r = R)");

      // (d) Underdetermined sphere–plane (plane position illustrative, d not given): goal r is UNDERDETERMINED, no leaked answer
      const underSphereScene: Scene3D = {
        free_objects: ["I", "q_r_u"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "q_r_u", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["ball_u"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f_ru", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"] },
          { id: "ball_u", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: null, render: "curved_solid", depends: ["I", "q_r_u"], anchor: ["0", "0", "0"], radius_sq: "25" },
          { id: "mp_u", type: "plane3", label: "Mặt phẳng cắt (P)", notation: "(P)", origin: "derived", producer: null, render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["0", "0", "3"], normal: ["0", "0", "1"], source: { provenance: "ILLUSTRATIVE_CONFIGURATION", is_given: false } as unknown as SceneObject["source"] },
          { id: "c_u", type: "circle3", label: "Đường tròn giao tuyến", origin: "derived", producer: null, render: "circle", surface_role: "SECTION_REGION", depends: ["ball_u", "mp_u"], center: ["0", "0", "3"], normal: ["0", "0", "1"], radius_sq: "16" },
          { id: "kq_ru", type: "quantity", label: "Bán kính giao tuyến", notation: "r", origin: "derived", producer: "measure_radius", render: "readout", depends: ["c_u"], value: "4", exact: { kind: "rational", value: "4" }, annotation: { kind: "length", category: "result", role: "result", subject_ids: ["c_u"], anchor: "region" } },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "ball_u", depends: ["I", "q_r_u"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "mp_u", depends: [], explanation: "" },
          { step_index: 3, action: "CREATE", object: "c_u", depends: ["ball_u", "mp_u"], explanation: "" },
          { step_index: 4, action: "MEASURE", object: "kq_ru", depends: ["c_u"], explanation: "" },
        ],
      };
      const underSpherePlan = buildPedagogicalConstructionPlan(withSubEntities(underSphereScene));
      expect(underSpherePlan.goalCompletion.items[0]?.provenance).toBe("UNDERDETERMINED");
      expect(underSpherePlan.goalCompletion.items[0]?.valueText).toBeNull();
      const underSphereHtml = renderToString(
        <AxoWorkspaceV62 scene={underSpherePlan.scene} de="Mặt cầu bán kính 5 bị cắt bởi mặt phẳng (P)." />,
      );
      expect(underSphereHtml).not.toContain('id="dock-math-results"');
      expect(underSphereHtml).toContain("Bản ghi chưa có chứng nhận kết quả mục tiêu.");
      expect(underSphereHtml).not.toMatch(/Chưa\s+đủ\s+dữ\s+kiện/iu);

      // (e) Contradictory sphere–plane data (r² = 20 violates d² + r² = R² where d² = 9, R² = 25)
      const contradictorySphereScene: Scene3D = {
        free_objects: ["I"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "ball_bad", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: null, render: "curved_solid", depends: ["I"], anchor: ["0", "0", "0"], radius_sq: "25" },
          { id: "mp_bad", type: "plane3", label: "Mặt phẳng (P)", notation: "(P)", origin: "derived", producer: null, render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["0", "0", "3"], normal: ["0", "0", "1"] },
          { id: "c_bad", type: "circle3", label: "Đường tròn mâu thuẫn", origin: "derived", producer: null, render: "circle", surface_role: "SECTION_REGION", depends: ["ball_bad", "mp_bad"], center: ["0", "0", "3"], normal: ["0", "0", "1"], radius_sq: "20" },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "ball_bad", depends: ["I"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "mp_bad", depends: [], explanation: "" },
          { step_index: 3, action: "CREATE", object: "c_bad", depends: ["ball_bad", "mp_bad"], explanation: "" },
        ],
      };
      expect(verifySceneMathematicalConsistency(contradictorySphereScene).valid).toBe(false);
    });
  });

  describe("11.D & 11.E — Underdetermined Geometry & All 12 Cross-Family Groups (Sections 6 & 8)", () => {
    it("verifies underdetermined S.ABC (SA ⊥ (ABC), AB = 2a, SA = 4a) and underdetermined quadrilateral pyramid S.ABCD without inventing base properties or leaking answers", () => {
      const sabc: Scene3D = {
        free_objects: ["A", "B", "C", "S", "q_ab", "q_sa"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        length_unit: { symbol: "a", display_scale: "a = 1 đơn vị dựng", is_given: false },
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"], source: {} },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"], source: {} },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"], source: {} },
          { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"], source: {} },
          { id: "day_ABC", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]] },
          {
            id: "cao_SA",
            type: "segment3",
            label: "Đường cao SA",
            notation: "SA",
            origin: "derived",
            producer: "construct_segment",
            render: "segment",
            depends: ["S", "A"],
            formation_roles: ["CONSTRUCT_HEIGHT"],
            endpoint_ids: ["S", "A"],
            endpoints: [["0", "0", "4"], ["0", "0", "0"]],
            perpendicular_witness: {
              from: "S",
              foot: ["0", "0", "0"],
              foot_id: "A",
              on: "day_ABC",
              relation: "line_perp_plane",
              status: "GIVEN",
              plane_directions: [["2", "0", "0"], ["0", "2", "0"]],
              marker: { u: ["2", "0", "0"], v: ["0", "0", "4"] },
            },
          },
          { id: "khoi_SABC", type: "solid", label: "Hình chóp S.ABC", notation: "S.ABC", shape_class: "PYRAMID_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", depends: ["S", "A", "B", "C"], formation_roles: ["CLOSE_SOLID"], vertex_ids: ["S", "A", "B", "C"], vertices: [["0", "0", "4"], ["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]], faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]] },
          { id: "q_ab", type: "quantity", label: "Độ dài AB", notation: "AB", origin: "free", producer: null, render: "readout", depends: ["A", "B"], value: "2a", symbolic: "2a", source: { fact_id: "f1", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"], annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "B"], anchor: "segment" } },
          { id: "q_sa", type: "quantity", label: "Độ dài SA", notation: "SA", origin: "free", producer: null, render: "readout", depends: ["S", "A"], value: "4a", symbolic: "4a", source: { fact_id: "f2", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"], annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["S", "A"], anchor: "segment" } },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_ABC", depends: ["A", "B", "C"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "cao_SA", depends: ["S", "A"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "khoi_SABC", depends: ["S", "A", "B", "C"], explanation: "" },
        ],
      };

      const base = sabc.objects.find((o) => o.id === "day_ABC")!;
      expect(classifyPolygonShapeWithProvenance(sabc, base).certifiedShape).toBeNull();
      expect(classifyScenePolygonShape(sabc, base)).toBe("tam giác");
      expect(classifySceneEntityProvenance(sabc, base)).toBe("ILLUSTRATIVE");
      const plan = buildPedagogicalConstructionPlan(withSubEntities(sabc));
      const html = renderToString(
        <AxoWorkspaceV62 scene={plan.scene} de="Cho hình chóp S.ABC có SA ⊥ (ABC), AB = 2a, SA = 4a." tieuDe="Hình chóp S.ABC" />,
      );
      expect(html).not.toMatch(/tam\s+giác\s+(?:vuông\s+cân|vuông|cân|đều)/iu);
      expect(html).toContain("AB = 2a");
      expect(html).toContain("SA = 4a");
      expect(html).not.toContain('id="dock-math-results"');
    });

    it("audits all 12 mandatory geometry families (pyramids, right & oblique prisms, cones, right & oblique cylinders, spheres, sections, plane-plane intersections, point-plane distance, skew-lines distance, midpoints/centroids, and multi-object scenes)", () => {
      // All 11 generated catalog scenes + dedicated right prism, oblique prism + section, oblique cylinder, plane-plane intersection + centroid, and skew-lines common perpendicular
      const catalogChecks = [
        "the-tich-chop",        // Group 1: orthogonal pyramid
        "mp-vuong-goc-duong",   // Group 1 & 9: line perpendicular to plane
        "tru-truc-xien",        // Group 5: cylinder axial cut
        "tru-thiet-dien-tron",  // Group 5a & 7: right cylinder circular section
        "non-duong-sinh",       // Group 4: cone + generator
        "non-thiet-dien-truc",  // Group 4 & 7: cone axial section
        "cau-the-tich",         // Group 6: sphere
        "thiet-dien-chop",      // Group 7a & 11: pyramid cross-section + midpoints
        "mat-cheo-sac",         // Group 8: diagonal plane & intersection
        "vuong-goc-chop",       // Group 9: point-to-plane distance / perpendicularity
        "cau-cat-mat-phang",    // Group 6, 7c & 12: sphere + plane + circle + distance
      ];
      for (const id of catalogChecks) {
        const { world, desc, title } = loadCatalogScene(id);
        expect(verifySceneMathematicalConsistency(world).valid, id).toBe(true);
        const plan = buildPedagogicalConstructionPlan(world);
        expect(plan.steps.length, id).toBeGreaterThan(0);
        const ssr = renderToString(<AxoWorkspaceV62 scene={plan.scene} de={desc} tieuDe={title} />);
        expect(ssr, id).not.toContain('id="dock-math-results"');
      }

      // Group 2 & 10: Right prism ABC.A′B′C′ (AA′ ⊥ (ABC)) + skew-lines common perpendicular between AA′ and BC
      const rightPrismSkewScene: Scene3D = {
        free_objects: ["A", "B", "C", "A1", "B1", "C1"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["4", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
          { id: "A1", type: "point3", label: "Điểm A′", notation: "A′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "5"] },
          { id: "B1", type: "point3", label: "Điểm B′", notation: "B′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["4", "0", "5"] },
          { id: "C1", type: "point3", label: "Điểm C′", notation: "C′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "5"] },
          { id: "day_ABC", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["4", "0", "0"], ["0", "4", "0"]] },
          { id: "cao_AA1", type: "segment3", label: "Cạnh bên AA′", notation: "AA′", origin: "derived", producer: "construct_segment", render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["A1", "A"], endpoint_ids: ["A1", "A"], endpoints: [["0", "0", "5"], ["0", "0", "0"]], perpendicular_witness: { from: "A1", foot: ["0", "0", "0"], foot_id: "A", on: "day_ABC", relation: "line_perp_plane", status: "GIVEN", plane_directions: [["4", "0", "0"], ["0", "4", "0"]], marker: { u: ["4", "0", "0"], v: ["0", "0", "5"] } } },
          { id: "lt_dung", type: "solid", label: "Lăng trụ đứng ABC.A′B′C′", notation: "ABC.A′B′C′", shape_class: "PRISM_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", depends: ["A", "B", "C", "A1", "B1", "C1"], vertex_ids: ["A", "B", "C", "A1", "B1", "C1"], vertices: [["0", "0", "0"], ["4", "0", "0"], ["0", "4", "0"], ["0", "0", "5"], ["4", "0", "5"], ["0", "4", "5"]], faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]] },
          { id: "ln_aa1", type: "line3", label: "Đường thẳng AA′", notation: "AA′", origin: "derived", producer: "construct_line", render: "line", depends: ["A", "A1"], point: ["0", "0", "0"], direction: ["0", "0", "5"] },
          { id: "ln_bc", type: "line3", label: "Đường thẳng BC", notation: "BC", origin: "derived", producer: "construct_line", render: "line", depends: ["B", "C"], point: ["4", "0", "0"], direction: ["-4", "4", "0"] },
          {
            id: "q_skew",
            type: "quantity",
            label: "Khoảng cách giữa AA′ và BC",
            notation: "d(AA′, BC)",
            origin: "derived",
            producer: "measure_distance",
            render: "readout",
            depends: ["ln_aa1", "ln_bc"],
            value: "2√2",
            exact: { kind: "radical", coefficient: "2", radicand: 2 },
            annotation: {
              kind: "distance",
              category: "result",
              role: "result",
              subject_ids: ["ln_aa1", "ln_bc"],
              anchor: "witness",
              witness: {
                from: "ln_bc",
                from_point: ["2", "2", "0"],
                on: "ln_aa1",
                foot: ["0", "0", "0"],
                relation: "common_perpendicular",
                marker: { u: ["0", "0", "5"], v: ["2", "2", "0"] },
                second: {
                  on: "ln_bc",
                  foot: ["2", "2", "0"],
                  marker: { u: ["-4", "4", "0"], v: ["-2", "-2", "0"] },
                },
              },
            },
          },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_ABC", depends: ["A", "B", "C"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "cao_AA1", depends: ["A1", "A"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "lt_dung", depends: ["A", "B", "C", "A1", "B1", "C1"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "ln_aa1", depends: ["A", "A1"], explanation: "" },
          { step_index: 5, action: "CREATE", object: "ln_bc", depends: ["B", "C"], explanation: "" },
          { step_index: 6, action: "MEASURE", object: "q_skew", depends: ["ln_aa1", "ln_bc"], explanation: "" },
        ],
      };
      expect(verifySceneMathematicalConsistency(rightPrismSkewScene).valid).toBe(true);
      const rpPlan = buildPedagogicalConstructionPlan(withSubEntities(rightPrismSkewScene));
      expect(rpPlan.scene.objects.some((o) => o.id === "q_skew__perp_seg")).toBe(true);
      const rpSsr = renderToString(<AxoWorkspaceV62 scene={rpPlan.scene} de="Cho lăng trụ đứng ABC.A′B′C′." />);
      expect(rpSsr).not.toContain('id="dock-math-results"');
      expect(rpSsr).not.toContain('id="dock-goal-reveal"');
      expect(rpSsr).not.toContain('id="dock-goal-conclusion"');
      expect(rpSsr).not.toContain("2√2");

      // Group 3 & 7b: Oblique prism ABC.A′B′C′ cut by cross-section plane (A′BC) + projection foot H of A′ on (ABC)
      const obliquePrismWithSection: Scene3D = {
        free_objects: ["A", "B", "C", "A1", "B1", "C1"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["4", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
          { id: "H", type: "point3", label: "Hình chiếu H", notation: "H", origin: "derived", producer: "project_point", render: "point_marker", depends: ["A1", "day_ABC"], xyz: ["1", "2", "0"], perpendicular_witness: { from: "A1", foot: ["1", "2", "0"], foot_id: "H", on: "day_ABC", relation: "line_perp_plane", plane_directions: [["4", "0", "0"], ["0", "4", "0"]], marker: { u: ["4", "0", "0"], v: ["0", "0", "3"] } } },
          { id: "A1", type: "point3", label: "Điểm A′", notation: "A′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "2", "3"] },
          { id: "B1", type: "point3", label: "Điểm B′", notation: "B′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["5", "2", "3"] },
          { id: "C1", type: "point3", label: "Điểm C′", notation: "C′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "6", "3"] },
          { id: "day_ABC", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["4", "0", "0"], ["0", "4", "0"]] },
          { id: "cao_A1H", type: "segment3", label: "Đường cao A′H", notation: "A′H", origin: "derived", producer: "construct_segment", render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["A1", "H"], endpoint_ids: ["A1", "H"], endpoints: [["1", "2", "3"], ["1", "2", "0"]], perpendicular_witness: { from: "A1", foot: ["1", "2", "0"], foot_id: "H", on: "day_ABC", relation: "line_perp_plane", plane_directions: [["4", "0", "0"], ["0", "4", "0"]], marker: { u: ["4", "0", "0"], v: ["0", "0", "3"] } } },
          { id: "day_A1B1C1", type: "polygon3", label: "Đáy A′B′C′", notation: "A′B′C′", origin: "derived", producer: "construct_polygon", render: "polygon", formation_roles: ["CONSTRUCT_TRANSLATED_FACE"], depends: ["A1", "B1", "C1"], vertex_ids: ["A1", "B1", "C1"], vertices: [["1", "2", "3"], ["5", "2", "3"], ["1", "6", "3"]] },
          { id: "lt_xien", type: "solid", label: "Lăng trụ xiên ABC.A′B′C′", notation: "ABC.A′B′C′", shape_class: "PRISM_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", depends: ["A", "B", "C", "A1", "B1", "C1"], vertex_ids: ["A", "B", "C", "A1", "B1", "C1"], vertices: [["0", "0", "0"], ["4", "0", "0"], ["0", "4", "0"], ["1", "2", "3"], ["5", "2", "3"], ["1", "6", "3"]], faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]] },
          { id: "M_ab", type: "point3", label: "Trung điểm M", notation: "M", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["A", "B"], xyz: ["2", "0", "0"] },
          { id: "N_ac", type: "point3", label: "Trung điểm N", notation: "N", origin: "derived", producer: "midpoint", render: "point_marker", depends: ["A", "C"], xyz: ["0", "2", "0"] },
          { id: "mp_cut", type: "plane3", label: "Mặt phẳng cắt (A′MN)", notation: "(A′MN)", origin: "derived", producer: "construct_plane", render: "surface", surface_role: "CUTTING_PLANE", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: ["A1", "M_ab", "N_ac"], point: ["2", "0", "0"], normal: ["3", "3", "-1"] },
          { id: "td_lt", type: "section", label: "Thiết diện A′MN", notation: "A′MN", origin: "derived", producer: "intersect_plane_solid", render: "polygon", depends: ["lt_xien", "mp_cut"], polygon: [["1", "2", "3"], ["2", "0", "0"], ["0", "2", "0"]], closed: true },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_ABC", depends: ["A", "B", "C"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "H", depends: ["A1", "day_ABC"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "cao_A1H", depends: ["A1", "H"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "day_A1B1C1", depends: ["A1", "B1", "C1"], explanation: "" },
          { step_index: 5, action: "CREATE", object: "lt_xien", depends: ["A", "B", "C", "A1", "B1", "C1"], explanation: "" },
          { step_index: 6, action: "CREATE", object: "M_ab", depends: ["A", "B"], explanation: "" },
          { step_index: 7, action: "CREATE", object: "N_ac", depends: ["A", "C"], explanation: "" },
          { step_index: 8, action: "CREATE", object: "mp_cut", depends: ["A1", "M_ab", "N_ac"], explanation: "" },
          { step_index: 9, action: "CREATE", object: "td_lt", depends: ["lt_xien", "mp_cut"], explanation: "" },
        ],
      };
      expect(verifySceneMathematicalConsistency(obliquePrismWithSection).valid).toBe(true);
      const obPrismPlan = buildPedagogicalConstructionPlan(withSubEntities(obliquePrismWithSection));
      const obPrismFinal = obPrismPlan.steps[obPrismPlan.steps.length - 1]!.anchor;
      expect(resolvePlaneSectionVisibility(obPrismPlan.scene, obPrismPlan.scene.objects.find((o) => o.id === "td_lt")!, obPrismFinal, false, null).visible).toBe(true);
      // Never calls lateral edge AA′ an altitude of oblique prism
      expect(obPrismPlan.steps.map((s) => s.title).join("\n")).not.toMatch(/Đường\s+cao\s+AA′/iu);

      // Group 5b: Oblique cylinder (OO′ not perpendicular to base plane z = 0) never calls OO′ a right axis
      const obliqueCylScene: Scene3D = {
        free_objects: ["O", "O1"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "O", type: "point3", label: "Tâm O", notation: "O", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "O1", type: "point3", label: "Tâm O′", notation: "O′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "4"] },
          { id: "day_duoi", type: "circle3", label: "Đáy tâm O", origin: "derived", producer: null, render: "circle", surface_role: "BASE_REGION", depends: ["O"], center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "9" },
          { id: "day_tren", type: "circle3", label: "Đáy tâm O′", origin: "derived", producer: null, render: "circle", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_TRANSLATED_FACE"], depends: ["O1"], center: ["2", "0", "4"], normal: ["0", "0", "1"], radius_sq: "9" },
          { id: "tru_xien", type: "curved_solid", curved_kind: "cylinder", label: "Hình trụ xiên", origin: "derived", producer: null, render: "curved_solid", depends: ["O", "O1", "day_duoi", "day_tren"], anchor: ["0", "0", "0"], apex_or_top: ["2", "0", "4"], base_normal: ["0", "0", "1"], radius_sq: "9" } as unknown as SceneObject,
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_duoi", depends: ["O"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "day_tren", depends: ["O1"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "tru_xien", depends: ["O", "O1", "day_duoi", "day_tren"], explanation: "" },
        ],
      };
      const obCylPlan = buildPedagogicalConstructionPlan(withSubEntities(obliqueCylScene));
      expect(obCylPlan.steps.map((s) => `${s.title} ${s.subtitle}`).join("\n")).not.toMatch(/trục\s+OO′\s+vuông\s+góc/iu);

      // Group 8 & 11: Plane–plane intersection line (SAC) ∩ (SBD) = SO + centroid G of triangle SBC
      const interAndCentroidScene: Scene3D = {
        free_objects: ["S", "A", "B", "C", "D"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["6", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["6", "6", "0"] },
          { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "6", "0"] },
          { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "6"] },
          { id: "day_abcd", type: "polygon3", label: "Đáy ABCD", notation: "ABCD", origin: "derived", producer: null, render: "polygon", depends: ["A", "B", "C", "D"], vertices: [["0", "0", "0"], ["6", "0", "0"], ["6", "6", "0"], ["0", "6", "0"]], vertex_ids: ["A", "B", "C", "D"], formation_roles: ["CONSTRUCT_BASE"] },
          { id: "khoi_chop", type: "solid", label: "Hình chóp S.ABCD", notation: "S.ABCD", shape_class: "PYRAMID_LIKE", origin: "derived", producer: null, render: "mesh", depends: ["S", "A", "B", "C", "D"], vertex_ids: ["S", "A", "B", "C", "D"], vertices: [["0", "0", "6"], ["0", "0", "0"], ["6", "0", "0"], ["6", "6", "0"], ["0", "6", "0"]], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]], formation_roles: ["CLOSE_SOLID"] },
          { id: "mp_sac", type: "plane3", label: "(SAC)", notation: "(SAC)", origin: "derived", producer: null, render: "surface", depends: ["S", "A", "C"], point: ["0", "0", "6"], normal: ["1", "-1", "0"], formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"] },
          { id: "mp_sbd", type: "plane3", label: "(SBD)", notation: "(SBD)", origin: "derived", producer: null, render: "surface", depends: ["S", "B", "D"], point: ["0", "0", "6"], normal: ["1", "1", "1"], formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"] },
          { id: "gt_so", type: "line3", label: "Giao tuyến của (SAC) và (SBD)", notation: "SO", origin: "derived", producer: null, render: "line", depends: ["mp_sac", "mp_sbd"], source: { instruction: "intersect_plane_plane" }, point: ["0", "0", "6"], direction: ["-1", "-1", "2"], formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"] },
          { id: "G_sbc", type: "point3", label: "Trọng tâm G", notation: "G", origin: "derived", producer: null, render: "point_marker", depends: ["S", "B", "C"], source: { instruction: "centroid" }, xyz: ["4", "2", "2"] },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_abcd", depends: ["A", "B", "C", "D"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "khoi_chop", depends: ["S", "A", "B", "C", "D"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "mp_sac", depends: ["S", "A", "C"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "mp_sbd", depends: ["S", "B", "D"], explanation: "" },
          { step_index: 5, action: "CREATE", object: "gt_so", depends: ["mp_sac", "mp_sbd"], explanation: "" },
          { step_index: 6, action: "CREATE", object: "G_sbc", depends: ["S", "B", "C"], explanation: "" },
        ],
      };
      expect(verifySceneMathematicalConsistency(interAndCentroidScene).valid).toBe(true);
      const icPlan = buildPedagogicalConstructionPlan(withSubEntities(interAndCentroidScene));
      expect(icPlan.scene.objects.some((o) => o.type === "point3" && o.xyz?.join("|") === "3|3|0")).toBe(true);
      expect(icPlan.steps.some((s) => /trọng\s+tâm/iu.test(`${s.title} ${s.operation}`))).toBe(true);
    });
  });

  describe("11.F — Route 404 & WebGL / Error Recovery Preservation", () => {
    it("renders minimalist 404 without reload loop and preserves problem statement + step dock when WebGL is unavailable", () => {
      try {
        useAppStore.getState().syncLocationRoute("/duong-dan-khong-ton-tai", "", "");
        syncStoreForSSR();
        const notFoundHtml = renderToString(<App />);
        expect(notFoundHtml).toContain('data-error-kind="not_found"');
        expect(notFoundHtml).not.toMatch(/meta[^>]*http-equiv="refresh"/iu);

        useAppStore.getState().syncLocationRoute("/simulation/cau-cat-mat-phang", "", "");
        syncStoreForSSR();
        const simHtml = renderToString(<App />);
        expect(simHtml).not.toContain('data-error-kind="not_found"');
        expect(simHtml).toContain('id="ws-dock"');
        expect(simHtml).not.toContain('id="dock-math-results"');
        expect(simHtml).not.toContain('id="dock-goal-reveal"');
        expect(simHtml).not.toContain('id="dock-goal-conclusion"');
        expect(simHtml).not.toContain("16π");
      } finally {
        useAppStore.getState().reset();
        syncStoreForSSR();
      }
    });
  });

  describe("11.G — Adversarial Edge-Case Regressions (Disjoint Sphere-Plane, Lateral Face Distance, Inscribed Sphere, Closed Perp Marker, Role Sanitization)", () => {
    it("allows valid disjoint sphere + external reference plane (d > R without cutting intent) while still refusing cutting planes with d > R", () => {
      const disjointDistanceSphereScene: Scene3D = {
        free_objects: ["I", "q_r"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "q_r", type: "quantity", label: "Bán kính R", notation: "R", origin: "free", producer: null, render: "readout", depends: ["ball_s"], value: "3", exact: { kind: "rational", value: "3" }, source: { fact_id: "f_r", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"] },
          { id: "ball_s", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: null, render: "curved_solid", depends: ["I", "q_r"], anchor: ["0", "0", "0"], radius_sq: "9" },
          // Backend stamps surface_role = CUTTING_PLANE by default on every plane3 even when it is only a distance reference plane
          { id: "mp_ext", type: "plane3", label: "Mặt phẳng (P)", notation: "(P)", role: "Mặt phẳng trong không gian", origin: "derived", producer: "construct_plane", render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["0", "0", "5"], normal: ["0", "0", "1"] },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "ball_s", depends: ["I", "q_r"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "mp_ext", depends: [], explanation: "" },
        ],
      };
      expect(verifySceneMathematicalConsistency(disjointDistanceSphereScene).valid).toBe(true);
    });

    it("narrates lateral face (SBC) as a polyhedron lateral face (never Thiết diện) and narrates authoritative AH ⊥ (SBC) distance steps cleanly", () => {
      const lateralDistanceScene: Scene3D = {
        free_objects: ["A", "B", "C", "D", "S"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "2", "0"] },
          { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
          { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "2"] },
          { id: "day_ABCD", type: "polygon3", label: "Đáy hình vuông ABCD", notation: "ABCD", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C", "D"], vertex_ids: ["A", "B", "C", "D"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]] },
          { id: "cao_SA", type: "segment3", label: "Đường cao SA", notation: "SA", origin: "derived", producer: "construct_segment", render: "segment", formation_roles: ["CONSTRUCT_HEIGHT"], depends: ["S", "A"], endpoint_ids: ["S", "A"], endpoints: [["0", "0", "2"], ["0", "0", "0"]], perpendicular_witness: { from: "S", foot: ["0", "0", "0"], foot_id: "A", on: "day_ABCD", relation: "line_perp_plane", marker: { u: ["2", "0", "0"], v: ["0", "0", "2"] } } },
          { id: "khoi_SABCD", type: "solid", label: "Hình chóp S.ABCD", notation: "S.ABCD", shape_class: "PYRAMID_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["S", "A", "B", "C", "D"], vertex_ids: ["S", "A", "B", "C", "D"], vertices: [["0", "0", "2"], ["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"]], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]] },
          { id: "mp_SBC", type: "polygon3", label: "Mặt bên (SBC)", notation: "(SBC)", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", depends: ["S", "B", "C"], vertex_ids: ["S", "B", "C"], vertices: [["0", "0", "2"], ["2", "0", "0"], ["2", "2", "0"]] },
          { id: "H", type: "point3", label: "Hình chiếu H", notation: "H", origin: "derived", producer: "foot_of_perpendicular", render: "point_marker", depends: ["A", "S", "B"], xyz: ["1", "0", "1"] },
          { id: "doan_AH", type: "segment3", label: "Đoạn AH", notation: "AH", origin: "derived", producer: "construct_perpendicular", render: "segment", depends: ["A", "H", "mp_SBC"], endpoint_ids: ["A", "H"], endpoints: [["0", "0", "0"], ["1", "0", "1"]], perpendicular_witness: { from: "A", foot: ["1", "0", "1"], foot_id: "H", on: "mp_SBC", relation: "line_perp_plane", marker: { u: ["-1", "0", "1"], v: ["-1", "0", "-1"] } } },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_ABCD", depends: ["A", "B", "C", "D"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "cao_SA", depends: ["S", "A"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "khoi_SABCD", depends: ["S", "A", "B", "C", "D"], explanation: "" },
          { step_index: 4, action: "CREATE", object: "mp_SBC", depends: ["S", "B", "C"], explanation: "" },
          { step_index: 5, action: "CREATE", object: "H", depends: ["A", "S", "B"], explanation: "" },
          { step_index: 6, action: "CREATE", object: "doan_AH", depends: ["A", "H", "mp_SBC"], explanation: "" },
        ],
      };

      const plan = buildPedagogicalConstructionPlan(withSubEntities(lateralDistanceScene));
      const allStepTitles = plan.steps.map((s) => s.title).join(" | ");
      expect(allStepTitles).not.toMatch(/thiết\s+diện/iu);
      expect(allStepTitles).toMatch(/Xác định mặt bên \(SBC\)/u);
      expect(allStepTitles).toMatch(/Hạ hình chiếu vuông góc H của A lên \(SBC\)/u);
      expect(allStepTitles).toMatch(/Hạ đoạn vuông góc AH ⊥ \(SBC\) tại H/u);

      const mpObj = plan.scene.objects.find((o) => o.id === "mp_SBC")!;
      expect(isAuxiliaryExplanatoryPolygon(plan.scene, mpObj)).toBe(true);
      expect(formatCompactEntityChipLabel(plan.scene, mpObj)).not.toMatch(/Thiết diện/iu);
      expect(buildVerifiedObjectTooltip(plan.scene, "mp_SBC", 99)?.header).toBe("Mặt bên (SBC)");
    });

    it("does not synthesize tangent-plane segments on polyhedron + inscribed-sphere scenes", () => {
      const cubeInscribedSphereScene: Scene3D = {
        free_objects: ["A", "B", "C", "D", "A1", "B1", "C1", "D1", "I"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
          { id: "C", type: "point3", label: "C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "2", "0"] },
          { id: "D", type: "point3", label: "D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
          { id: "A1", type: "point3", label: "A1", notation: "A′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "2"] },
          { id: "B1", type: "point3", label: "B1", notation: "B′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "2"] },
          { id: "C1", type: "point3", label: "C1", notation: "C′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "2", "2"] },
          { id: "D1", type: "point3", label: "D1", notation: "D′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "2"] },
          { id: "cube", type: "solid", label: "Hình lập phương", notation: "ABCD.A′B′C′D′", origin: "derived", producer: null, render: "mesh", depends: ["A", "B", "C", "D", "A1", "B1", "C1", "D1"], vertex_ids: ["A", "B", "C", "D", "A1", "B1", "C1", "D1"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["2", "2", "0"], ["0", "2", "0"], ["0", "0", "2"], ["2", "0", "2"], ["2", "2", "2"], ["0", "2", "2"]], faces: [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]] },
          { id: "I", type: "point3", label: "Tâm I", notation: "I", origin: "derived", producer: null, render: "point_marker", depends: [], xyz: ["1", "1", "1"] },
          { id: "sph_in", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu nội tiếp", origin: "derived", producer: null, render: "curved_solid", depends: ["I"], anchor: ["1", "1", "1"], radius_sq: "1" },
          { id: "mp_base_meas", type: "plane3", label: "(ABCD)", notation: "(ABCD)", origin: "derived", producer: null, render: "surface", depends: ["A", "B", "C"], point: ["0", "0", "0"], normal: ["0", "0", "1"] },
          { id: "q_h", type: "quantity", label: "Chiều cao", origin: "derived", producer: "measure_distance", render: "readout", depends: ["mp_base_meas"], value: "2" },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "cube", depends: ["A", "B", "C", "D", "A1", "B1", "C1", "D1"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "sph_in", depends: ["I"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "mp_base_meas", depends: ["A", "B", "C"], explanation: "" },
          { step_index: 4, action: "MEASURE", object: "q_h", depends: ["mp_base_meas"], explanation: "" },
        ],
      };

      const plan = buildPedagogicalConstructionPlan(withSubEntities(cubeInscribedSphereScene));
      expect(plan.scene.objects.find((o) => o.id === "sph_in__mp_base_meas__dist")).toBeUndefined();
      expect(plan.steps.some((s) => /tiếp\s+diện/iu.test(s.title))).toBe(false);
    });

    it("closes the right-angle marker base leg at Step 2 (before HM exists) and opens onto HM at Step 3, and sanitizes polluted role/label descriptors", () => {
      const sphereSample = GEOMETRY_SAMPLES.find((s) => s.id === "cau-cat-mat-phang")!;
      const rawScene = structuredClone((sphereSample.envelope as { scene3d?: Scene3D }).scene3d!) as Scene3D;
      const expanded = veKhongGian(withSubEntities(rawScene));
      registerExactSceneOrigin(expanded, rawScene);
      const plan = buildPedagogicalConstructionPlan(expanded);

      const distSeg = plan.scene.objects.find((o) => o.id === "C__dist")!;
      const step2Visible = objectsAt(plan.scene, plan.steps[2]!.anchor);
      const step3Visible = objectsAt(plan.scene, plan.steps[4]!.anchor);

      const builtStep2 = buildObject3D(
        distSeg,
        false,
        0.1,
        [],
        new THREE.Vector3(8, 3, 6),
        undefined,
        undefined,
        false,
        "primary",
        false,
        true,
        false,
        plan.scene,
        undefined,
        undefined,
        undefined,
        step2Visible,
      )!;
      expect(builtStep2.getObjectByName("perp_marker:C__dist")).toBeUndefined();
      expect(builtStep2.getObjectByName("perp_plane_ray:C__dist")).toBeUndefined();

      const builtStep3 = buildObject3D(
        distSeg,
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
        plan.scene,
        undefined,
        undefined,
        undefined,
        step3Visible,
      )!;
      const markerStep3 = builtStep3.getObjectByName("perp_marker:C__dist") as THREE.Line;
      expect(markerStep3.geometry.getAttribute("position").count).toBe(3);
      expect(builtStep3.getObjectByName("perp_plane_ray:C__dist")).toBeUndefined();

      expect(sanitizeStudentDescriptorText("Bán kính thiết diện r = 4")).toBe("Bán kính thiết diện r");
      expect(sanitizeStudentDescriptorText("Diện tích hình tròn ⇒ 16π")).toBe("Diện tích hình tròn");
      const policy = evaluateStudentPresentationPolicy(plan.scene, {
        status: "reached",
        headline: "OK",
        detail: "",
        items: [{ id: "q1", label: "Bán kính giao tuyến = 4", valueText: "4", provenance: "DERIVED_VERIFIED" }],
      });
      expect(policy.safeWorkspaceTitle).toBe("Bán kính giao tuyến");
      expect(
        policy.formatStudentObjectRole({
          ...distSeg,
          role: "Đoạn khoảng cách d = 3",
        }),
      ).toBe("Đoạn khoảng cách d");
    });
  });
});
