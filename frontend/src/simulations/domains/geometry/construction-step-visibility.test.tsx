import * as THREE from "three";
import { describe, expect, it } from "vitest";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { veKhongGian } from "./scene3d-chart";
import { objectsAt, stepCount, type Scene3D } from "./scene3d-model";
import {
  buildContractReferenceGroup,
  buildPedagogicalConstructionPlan,
  pedagogicalStepList,
  registerExactSceneOrigin,
  resolveStepGoalKind,
  shortSym,
} from "./scene3d-semantic-policy";
import {
  STEP_GOAL_LABELS,
  STEP_GOAL_PRESENTATION_POLICY,
  type StepGoalKind,
} from "./scene3d-student-presentation-policy";
import { withSubEntities } from "./scene3d-subentities";

function extractCatalogSample(id: string) {
  const found = GEOMETRY_SAMPLES.find((s) => s.id === id);
  if (!found) throw new Error(`Missing catalog sample: ${id}`);
  return found;
}

function sampleRawScene(sample: ReturnType<typeof extractCatalogSample>): Scene3D {
  return (sample.envelope as unknown as { scene3d: Scene3D }).scene3d;
}

function prepareScene(raw: Scene3D) {
  const sub = withSubEntities(raw);
  registerExactSceneOrigin(sub, raw);
  const plan = buildPedagogicalConstructionPlan(sub);
  const disp = registerExactSceneOrigin(veKhongGian(plan.scene), plan.scene);
  return { raw, plan, disp };
}

function collectCoplanarGuideOpacities(group: THREE.Group | null): Map<string, number[]> {
  const result = new Map<string, number[]>();
  if (!group) return result;
  group.traverse((child) => {
    const ref = child.userData?.presentationReference as
      | { role?: string; source_object_id?: string }
      | undefined;
    if (ref?.role !== "COPLANAR_INTERSECTION_GUIDE" || !ref.source_object_id) return;
    let opacity: number | null = null;
    child.traverse((sub) => {
      if (sub instanceof THREE.Line) {
        const mat = sub.material as THREE.Material & { opacity?: number };
        if (typeof mat.opacity === "number") opacity = mat.opacity;
      }
    });
    if (opacity !== null) {
      const list = result.get(ref.source_object_id) ?? [];
      list.push(opacity);
      result.set(ref.source_object_id, list);
    }
  });
  return result;
}

describe("Construction Step Goals, Narration & Coplanar Guide Visibility", () => {
  it("supports all 6 StepGoalKind values across catalog scenes without problem-name hardcoding", () => {
    const allKinds: StepGoalKind[] = ["Define", "Construct", "Intersect", "Verify", "Measure", "Complete"];
    for (const k of allKinds) {
      expect(STEP_GOAL_LABELS[k].length).toBeGreaterThan(0);
      expect(STEP_GOAL_PRESENTATION_POLICY[k].goal).toBe(k);
    }

    const observedGoals = new Set<StepGoalKind>();
    for (const sample of GEOMETRY_SAMPLES) {
      const raw = sampleRawScene(sample);
      const { disp } = prepareScene(raw);
      const total = Math.max(1, stepCount(disp));
      for (let i = 0; i < total; i += 1) {
        observedGoals.add(resolveStepGoalKind(disp, i));
      }
    }
    for (const kind of allKinds) {
      expect(observedGoals.has(kind), `Expected StepGoalKind ${kind} across catalog`).toBe(true);
    }

    // Pyramid 3-point section key steps
    const chopRaw = sampleRawScene(extractCatalogSample("chop-thiet-dien-ba-diem"));
    const { disp: chopDisp } = prepareScene(chopRaw);
    const chopSteps = pedagogicalStepList(chopDisp);

    expect(resolveStepGoalKind(chopDisp, 0)).toBe("Define");

    const mnpStep = chopSteps.find((s) => s.title.includes("(MNP)"));
    expect(mnpStep).toBeDefined();
    expect(resolveStepGoalKind(chopDisp, mnpStep!.anchor)).toBe("Construct");

    const intersectSteps = chopSteps.filter((s) => /\b(E|F)\b/.test(s.title) && s.title.includes("giao điểm"));
    expect(intersectSteps.length).toBeGreaterThanOrEqual(2);
    for (const st of intersectSteps) {
      expect(resolveStepGoalKind(chopDisp, st.anchor)).toBe("Intersect");
    }

    const finalStep = chopSteps[chopSteps.length - 1]!;
    expect(resolveStepGoalKind(chopDisp, finalStep.anchor)).toBe("Complete");
  });

  it("Step 12 (MENPF) narration emits all 5 canonical section edges including EN and keeps raw learner_text untouched", () => {
    const sample = extractCatalogSample("chop-thiet-dien-ba-diem");
    const raw = sampleRawScene(sample);
    const originalLearnerText = JSON.stringify(raw.events?.map((e) => e.explanation ?? null) ?? []);
    const { disp } = prepareScene(raw);
    const steps = pedagogicalStepList(disp);
    const finalStep = steps[steps.length - 1]!;
    const fullText = [
      finalStep.title,
      finalStep.subtitle,
      finalStep.narration?.actionTitle ?? "",
      finalStep.narration?.conciseRationale ?? "",
      ...(finalStep.narration?.detailedEvidence ?? []),
    ].join(" ");

    expect(finalStep.title).toContain("MENPF");
    for (const edge of ["ME", "EN", "NP", "PF", "FM"]) {
      expect(fullText).toContain(edge);
    }
    // Canonical cycle ordering check within the edge trace rationale
    const rationale = finalStep.narration?.conciseRationale ?? "";
    const idxME = rationale.indexOf("ME");
    const idxEN = rationale.indexOf("EN");
    const idxNP = rationale.indexOf("NP");
    const idxPF = rationale.indexOf("PF");
    const idxFM = rationale.indexOf("FM");
    expect(idxME).toBeGreaterThanOrEqual(0);
    expect(idxME).toBeLessThan(idxEN);
    expect(idxEN).toBeLessThan(idxNP);
    expect(idxNP).toBeLessThan(idxPF);
    expect(idxPF).toBeLessThan(idxFM);

    // Input scene learner explanations are never mutated by frontend presentation
    expect(JSON.stringify(raw.events?.map((e) => e.explanation ?? null) ?? [])).toBe(originalLearnerText);
  });

  it("fades prior coplanar intersection guides when stepping from E to F and retires guides after closed section MENPF", () => {
    const raw = sampleRawScene(extractCatalogSample("chop-thiet-dien-ba-diem"));
    const { disp } = prepareScene(raw);
    const steps = pedagogicalStepList(disp);
    const stepE = steps.find((s) => s.title.includes("E") && s.title.includes("giao điểm"))!;
    const stepF = steps.find((s) => s.title.includes("F") && s.title.includes("giao điểm"))!;
    const stepFinal = steps[steps.length - 1]!;
    expect(stepE).toBeDefined();
    expect(stepF).toBeDefined();

    const pointE = disp.objects.find((o) => o.type === "point3" && (shortSym(o) === "E" || o.id === "E"))!;
    const pointF = disp.objects.find((o) => o.type === "point3" && (shortSym(o) === "F" || o.id === "F"))!;
    expect(pointE).toBeDefined();
    expect(pointF).toBeDefined();

    const opAtE = collectCoplanarGuideOpacities(
      buildContractReferenceGroup(disp, objectsAt(disp, stepE.anchor), stepE.anchor),
    );
    const opAtF = collectCoplanarGuideOpacities(
      buildContractReferenceGroup(disp, objectsAt(disp, stepF.anchor), stepF.anchor),
    );
    const opAtFinal = collectCoplanarGuideOpacities(
      buildContractReferenceGroup(disp, objectsAt(disp, stepFinal.anchor), stepFinal.anchor),
    );

    const eActiveOps = opAtE.get(pointE.id) ?? [];
    const ePriorOps = opAtF.get(pointE.id) ?? [];
    const fActiveOps = opAtF.get(pointF.id) ?? [];
    expect(eActiveOps.length).toBeGreaterThan(0);
    expect(ePriorOps.length).toBeGreaterThan(0);
    expect(fActiveOps.length).toBeGreaterThan(0);
    expect(Math.max(...eActiveOps)).toBeGreaterThan(Math.max(...ePriorOps));
    expect(Math.max(...fActiveOps)).toBeGreaterThan(Math.max(...ePriorOps));

    expect(opAtFinal.get(pointE.id) ?? []).toHaveLength(0);
    expect(opAtFinal.get(pointF.id) ?? []).toHaveLength(0);
  });
});
