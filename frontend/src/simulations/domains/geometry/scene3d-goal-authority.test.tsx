import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { docPhanHoiHybrid, hybridViewCua, kiemHybridView } from "./hybrid-preview-adapter";
import { attachHybridViewToScene, registerExactSceneOrigin, type Scene3D } from "./scene3d-model";
import { veKhongGian } from "./scene3d-chart";
import { withSubEntities } from "./scene3d-subentities";
import { buildPedagogicalConstructionPlan } from "./scene3d-semantic-policy";
import { evaluateStudentPresentationPolicy } from "./scene3d-student-presentation-policy";
import { createHistoryStore, fromServerHistoryDto, memoryStorage } from "../../../state/history";
import type { SimulationEnvelope } from "../../types";

const fixture = JSON.parse(readFileSync(new URL(
  "../../../../../docs/evaluation/geometry/runs/axo-final-mathematical-reliability/inputs/prism-baseline.json",
  import.meta.url,
), "utf8"));
const corpus = JSON.parse(readFileSync(new URL(
  "../../../../../docs/evaluation/geometry/runs/axo-final-mathematical-reliability/inputs/corpus.json",
  import.meta.url,
), "utf8")) as { id: string; input: { problem_text: string }; oracle: string | null;
  response: typeof fixture.response }[];

// Regenerated on the current backend (run axo-end-to-end-authority-scene3d-usability): every case is SERVED with a
// certified exact answer; the frontend previously rejected (primed section labels) or downgraded (metric heuristic) 18.
const regressions = JSON.parse(readFileSync(new URL(
  "../../../../../docs/evaluation/geometry/runs/axo-end-to-end-authority-scene3d-usability/inputs/authority-regressions.json",
  import.meta.url,
), "utf8")) as { cases: { key: string; audit: string; answers: Record<string, { coef: string }>;
  response: typeof fixture.response }[] };

/** Workspace order (`SimulationWorkspace` preparedSceneResult): attach view → verify → plan. */
function workspacePlan(response: unknown) {
  const decoded = docPhanHoiHybrid(structuredClone(response));
  if (!decoded.ok) return { decodeError: decoded.reason } as const;
  const scene = decoded.envelope.scene3d as Scene3D;
  const view = hybridViewCua(decoded.envelope)!;
  attachHybridViewToScene(scene, view);
  const plan = buildPedagogicalConstructionPlan(withSubEntities(scene));
  return { scene, view, plan, policy: evaluateStudentPresentationPolicy(scene, plan.goalCompletion) } as const;
}

describe("backend certificate is the authority for a source-bound Hybrid /4 answer", () => {
  it.each(regressions.cases)("$key ($audit) reaches its certified answer", (row) => {
    const r = workspacePlan(row.response);
    expect("decodeError" in r ? r.decodeError : null).toBeNull();
    if ("decodeError" in r) return;
    expect(r.plan.goalCompletion.status).toBe("reached");
    for (const [goal, answer] of Object.entries(row.answers)) {
      expect(r.plan.goalCompletion.items.find((i) => i.id === `kq_${goal}`)).toMatchObject({
        provenance: "DERIVED_VERIFIED", valueText: answer.coef,
      });
      expect(r.policy.canDisplayEntityValue(r.scene.objects.find((o) => o.id === `kq_${goal}`)!)).toBe(false);
    }
    expect(r.policy.showDiagnosticNotice).toBe(false);
  });

  const prismLayers = JSON.parse(readFileSync(new URL(
    "../../../../../docs/evaluation/geometry/runs/axo-end-to-end-authority-scene3d-usability/inputs/prism-layers.json",
    import.meta.url,
  ), "utf8")) as { oracle: string; rows: Record<string, { "7_adapter4": { status: string; failure_category: string | null };
    response: typeof fixture.response }> };
  it.each(Object.entries(prismLayers.rows))("right prism, extraction %s: layers 7–8 keep the backend verdict", (_, row) => {
    const decoded = docPhanHoiHybrid(structuredClone(row.response));
    expect(decoded.ok).toBe(true);
    if (!decoded.ok) return;
    if (row["7_adapter4"].status === "REFUSED") {
      expect(decoded.envelope).toMatchObject({ status: "unsupported", failure_category: row["7_adapter4"].failure_category });
      return;
    }
    const storage = memoryStorage();
    createHistoryStore(storage).record(decoded.envelope as unknown as SimulationEnvelope, row.response.envelope.title ?? "x", "attempt");
    const restored = createHistoryStore(storage).list()[0].envelope;
    for (const env of [decoded.envelope, restored]) {
      const scene = structuredClone((env as unknown as { scene3d: Scene3D }).scene3d);
      attachHybridViewToScene(scene, hybridViewCua(env));
      const g = buildPedagogicalConstructionPlan(withSubEntities(scene)).goalCompletion;
      expect(g.status).toBe("reached");
      expect(g.items.find((i) => i.id === "kq_q")).toMatchObject({ provenance: "DERIVED_VERIFIED", valueText: prismLayers.oracle });
    }
  });

  it("a record read back from server history keeps its answer evidence and attempt identity", () => {
    const row = regressions.cases.find((c) => c.audit === "decode_rejected")!;   // primed labels, section certificate
    const decoded = docPhanHoiHybrid(structuredClone(row.response));
    if (!decoded.ok) throw Error(decoded.reason);
    // `backend/app/accounts/router.py` stores and returns `envelope` verbatim (test_learning_history_api.py locks it).
    const wire = JSON.parse(JSON.stringify({ id: "a-server-attempt", sampleId: null, title: "t", simulationId: "s",
      domain: "geometry", envelope: decoded.envelope, originalInput: "Đề gốc của lần gửi" }));
    const item = fromServerHistoryDto(wire)!;
    expect([item.id, item.originalInput]).toEqual(["a-server-attempt", "Đề gốc của lần gửi"]);
    expect(hybridViewCua(item.envelope)).toEqual(hybridViewCua(decoded.envelope));
    const scene = (item.envelope as unknown as { scene3d: Scene3D }).scene3d;
    attachHybridViewToScene(scene, hybridViewCua(item.envelope));
    const g = buildPedagogicalConstructionPlan(withSubEntities(scene)).goalCompletion;
    expect(g.status).toBe("reached");
  });

  it("a binding whose coefficient disagrees with the scene is inconsistent, never insufficient data", () => {
    const row = regressions.cases.find((c) => c.audit.startsWith("not_reached"))!;
    const decoded = docPhanHoiHybrid(structuredClone(row.response));
    if (!decoded.ok) throw Error(decoded.reason);
    const scene = decoded.envelope.scene3d as Scene3D;
    const view = structuredClone(hybridViewCua(decoded.envelope)!);
    view.answers[0].coefficient = "999";
    attachHybridViewToScene(scene, view);
    const g = buildPedagogicalConstructionPlan(withSubEntities(scene)).goalCompletion;
    expect(g.items.find((i) => i.id === view.answers[0].quantity_id)?.provenance).toBe("INVALID");
    expect(g.status).toBe("unverified_or_contradictory");
    expect(`${g.headline} ${g.detail}`).not.toMatch(/chưa đủ dữ kiện|thiếu dữ kiện/iu);
  });
});

describe("Hybrid exact answer authority survives presentation and reload", () => {
  it.each(corpus)("$id retains mathematical classification through history", (row) => {
    const decoded = docPhanHoiHybrid(structuredClone(row.response));
    expect(decoded.ok).toBe(true);
    if (!decoded.ok) return;
    if (row.response.route_d.status === "REFUSED") {
      expect(decoded.envelope.status).toBe("unsupported");
      expect(decoded.envelope).not.toHaveProperty("scene3d");
      expect(decoded.envelope).toMatchObject({
        reason_code: row.response.envelope.reason_code,
        failure_category: row.response.envelope.failure_category,
      });
      return;
    }
    const storage = memoryStorage();
    createHistoryStore(storage).record(decoded.envelope as unknown as SimulationEnvelope, row.input.problem_text, row.id);
    const restored = createHistoryStore(storage).list()[0];
    expect(restored.id).toBe(row.id);
    expect(restored.originalInput).toBe(row.input.problem_text);
    const raw = (restored.envelope as unknown as { scene3d: Scene3D }).scene3d;
    const before = JSON.stringify(raw);
    const view = hybridViewCua(restored.envelope);
    expect(kiemHybridView(view, raw)).toBeNull();
    attachHybridViewToScene(raw, view);
    const plan = buildPedagogicalConstructionPlan(withSubEntities(raw));
    expect(plan.goalCompletion.status).toBe("reached");
    expect(plan.goalCompletion.items.some(i => i.valueText === row.oracle && i.provenance === "DERIVED_VERIFIED")).toBe(true);
    expect(JSON.stringify(raw)).toBe(before);
    const policy = evaluateStudentPresentationPolicy(raw, plan.goalCompletion);
    expect(policy.showDiagnosticNotice).toBe(false);
    for (const answer of view!.answers) {
      expect(policy.canDisplayEntityValue(raw.objects.find(o => o.id === answer.quantity_id)!)).toBe(false);
    }
  });

  it("keeps separate attempts and original wording for shared compiled geometry", () => {
    const decoded = docPhanHoiHybrid(structuredClone(fixture.response));
    if (!decoded.ok) throw Error(decoded.reason);
    const storage = memoryStorage();
    const history = createHistoryStore(storage);
    const env = decoded.envelope as unknown as SimulationEnvelope;
    history.record(env, "Original statement one", "attempt-one");
    history.record(env, "Original statement two", "attempt-two");
    const restored = createHistoryStore(storage).list();
    expect(restored.map(r => [r.id, r.originalInput]).sort()).toEqual([
      ["attempt-one", "Original statement one"], ["attempt-two", "Original statement two"],
    ]);
    expect(restored[0].envelope.config).toEqual(restored[1].envelope.config);
  });
  it("rejects saved answer evidence paired with another scene value", () => {
    const decoded = docPhanHoiHybrid(structuredClone(fixture.response));
    expect(decoded.ok).toBe(true);
    if (!decoded.ok) return;
    const changed = structuredClone(decoded.envelope.scene3d) as Scene3D;
    changed.objects.find((o) => o.id === "kq_q")!.value = "31";
    changed.objects.find((o) => o.id === "kq_q")!.exact = { kind: "rational", value: "31" };
    expect(kiemHybridView(hybridViewCua(decoded.envelope), changed)).not.toBeNull();
  });
  it("does not diagnose mathematical insufficiency from an unverified quantity", () => {
    const raw = structuredClone(fixture.response.envelope.scene3d) as Scene3D;
    Object.assign(raw.objects.find((o) => o.id === "kq_q")!.source!, { provenance: "UNVERIFIED" });
    const plan = buildPedagogicalConstructionPlan(withSubEntities(raw));
    expect(plan.goalCompletion.status).not.toBe("reached");
    expect(`${plan.goalCompletion.headline} ${plan.goalCompletion.detail}`).not.toMatch(/thiếu dữ kiện|chưa đủ dữ kiện/iu);
  });
  it("preserves backend evidence in the saved attempt, including after a storage reload", () => {
    const decoded = docPhanHoiHybrid(structuredClone(fixture.response));
    expect(decoded.ok).toBe(true);
    if (!decoded.ok) return;
    const storage = memoryStorage();
    const history = createHistoryStore(storage);
    history.record(decoded.envelope as unknown as SimulationEnvelope, fixture.input.problem_text, "attempt-prism");
    const restored = createHistoryStore(storage).list()[0];
    expect(restored.id).toBe("attempt-prism");
    expect(restored.originalInput).toBe(fixture.input.problem_text);
    expect(hybridViewCua(restored.envelope)).toEqual(hybridViewCua(decoded.envelope));
    const raw = (restored.envelope as unknown as { scene3d: Scene3D }).scene3d;
    attachHybridViewToScene(raw, hybridViewCua(restored.envelope));
    const plan = buildPedagogicalConstructionPlan(withSubEntities(raw));
    expect(plan.goalCompletion.status).toBe("reached");
  });
  it.each([false, true])("accepts the source-verified kernel volume, reload=%s", (reload) => {
    const response = reload ? JSON.parse(JSON.stringify(fixture.response)) : structuredClone(fixture.response);
    const decoded = docPhanHoiHybrid(response);
    expect(decoded.ok).toBe(true);
    if (!decoded.ok) return;
    const raw = decoded.envelope.scene3d as Scene3D;
    attachHybridViewToScene(raw, hybridViewCua(decoded.envelope));
    const display = withSubEntities(registerExactSceneOrigin(veKhongGian(raw), raw));
    const plan = buildPedagogicalConstructionPlan(display);
    expect(plan.goalCompletion.status).toBe("reached");
    expect(plan.goalCompletion.items.find((item) => item.id === "kq_q")).toMatchObject({
      kind: "volume", valueText: "30", provenance: "DERIVED_VERIFIED",
    });
    const policy = evaluateStudentPresentationPolicy(display, plan.goalCompletion);
    expect(policy.showDiagnosticNotice).toBe(false);
    expect(policy.showMathResultsPanel).toBe(false);
    expect(policy.canDisplayEntityValue(raw.objects.find((o) => o.id === "kq_q")!)).toBe(false);
  });
});
