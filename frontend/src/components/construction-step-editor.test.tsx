import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import { GEOMETRY_SAMPLES } from "../data/geometry-samples";
import { registerAllSimulations } from "../simulations";
import type { Scene3D } from "../simulations/domains/geometry/scene3d-model";
import { buildPedagogicalConstructionPlan } from "../simulations/domains/geometry/scene3d-semantic-policy";
import type { SimulationEnvelope } from "../simulations/types";
import {
  buildStepEditSessionId,
  loadCachedStepEditState,
  saveCachedStepEditState,
  submitConstructionStepEdit,
} from "../state/construction-step-edits";
import { __resetHistoryForTest } from "../state/history";
import { useAppStore } from "../state/store";
import {
  InlineConstructionStepEditor,
  StepEditPencilButton,
} from "./ConstructionStepEditor";
import { SimulationWorkspace } from "./SimulationWorkspace";

registerAllSimulations();

const syncStoreForSSR = () => Object.assign(useAppStore.getInitialState(), useAppStore.getState());
const sample11 = GEOMETRY_SAMPLES.find((s) => s.id === "chop-mat-cau-ngoai-tiep")!;

function installMemoryStorage() {
  const map = new Map<string, string>();
  const storage: Storage = {
    get length() {
      return map.size;
    },
    clear() {
      map.clear();
    },
    getItem(k: string) {
      return map.has(k) ? map.get(k)! : null;
    },
    key(i: number) {
      return [...map.keys()][i] ?? null;
    },
    removeItem(k: string) {
      map.delete(k);
    },
    setItem(k: string, v: string) {
      map.set(k, v);
    },
  };
  vi.stubGlobal("window", { localStorage: storage });
  return map;
}

describe("AXO Editable Construction Steps & Reload Persistence", () => {
  beforeEach(() => {
    installMemoryStorage();
    __resetHistoryForTest();
    useAppStore.getState().reset();
    syncStoreForSSR();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("Test 1 (UI Default & Editor Buttons): default dock renders pencil triggers, zero open textareas, zero 'Lưu'/'Huấn luyện' buttons", () => {
    const env = structuredClone(sample11.envelope) as unknown as SimulationEnvelope;
    useAppStore.getState().loadEnvelope(env, sample11.id);
    syncStoreForSSR();

    const html = renderToString(<SimulationWorkspace />);
    expect(html).toContain('id="dock-steps-ul"');
    expect(html).toContain("step-edit-pencil-btn");
    expect(html).not.toContain("step-edit-textarea");
    expect(html).not.toContain("step-edit-updated-pill");
    expect(html).not.toContain("is-just-updated");
    expect(html).not.toContain("Đã cập nhật");
    expect(html).not.toContain(">Lưu<");
    expect(html).not.toContain(">Huấn luyện<");

    const pencilHtml = renderToString(
      <StepEditPencilButton stepNumber={8} onStartEdit={() => {}} />,
    );
    expect(pencilHtml).toContain('aria-label="Chỉnh sửa bước 8"');

    const editorHtml = renderToString(
      <InlineConstructionStepEditor
        stepIndex={7}
        initialValue="Xác định trung điểm H của AB, dựng mặt phẳng (α) đi qua H và vuông góc với AB."
        running={false}
        errorText={null}
        onCancel={() => {}}
        onSubmit={() => {}}
      />,
    );
    expect(editorHtml).toContain("<textarea");
    expect(editorHtml).toContain('rows="1"');
    expect(editorHtml).toContain("Hủy");
    expect(editorHtml).toContain("Chạy");
    expect(editorHtml).not.toContain(">Lưu<");
    expect(editorHtml).not.toContain(">Huấn luyện<");

    const runningHtml = renderToString(
      <InlineConstructionStepEditor
        stepIndex={7}
        initialValue="Dựng (α)"
        running={true}
        errorText={null}
        onCancel={() => {}}
        onSubmit={() => {}}
      />,
    );
    expect(runningHtml).toContain("Đang chạy...");
    expect(runningHtml).toContain("step-edit-spinner");
    expect(runningHtml).toContain('aria-live="polite"');
    expect(runningHtml).toContain("disabled");

    const errorHtml = renderToString(
      <InlineConstructionStepEditor
        stepIndex={7}
        initialValue="Dựng mặt phẳng (α) qua Q và vuông góc với AB."
        running={false}
        errorText="Chưa xác định được điểm Q."
        onCancel={() => {}}
        onSubmit={() => {}}
      />,
    );
    expect(errorHtml).toContain('role="alert"');
    expect(errorHtml).toContain("Chưa xác định được điểm Q.");
    expect(errorHtml).toContain("Dựng mặt phẳng (α) qua Q và vuông góc với AB.");
  });

  it("Test 2 (Mutex, Commit Cache & Rollback Preservation): blocks duplicate clicks, persists on 200, keeps prior scene on 422", async () => {
    const sid = buildStepEditSessionId("sample:chop-mat-cau-ngoai-tiep", "guest");
    const baseScene = structuredClone((sample11.envelope as unknown as { scene3d: Scene3D }).scene3d);

    let releaseFirst!: () => void;
    const firstGate = new Promise<void>((res) => {
      releaseFirst = res;
    });

    const fetchMock = vi
      .fn()
      .mockImplementationOnce(async () => {
        await firstGate;
        return new Response(
          JSON.stringify({
            status: "committed",
            mode: "PARTIAL_TOPOLOGICAL_REBUILD",
            session_id: sid,
            revision_id: "rev-1",
            feedback_id: "fb-1",
            feedback_status: "GEOMETRY_VERIFIED",
            dataset_eligibility: "INELIGIBLE",
            version_number: 1,
            primary_target_id: "mp_tt_AB",
            scene3d: baseScene,
            step_overrides: {
              mp_tt_AB: "Xác định trung điểm H của AB, dựng mặt phẳng (α) đi qua H và vuông góc với AB.",
            },
            dependency_summary: {
              edited_target_ids: ["mp_tt_AB"],
              created_ids: ["H"],
              reused_ids: ["ab"],
              retired_ids: ["M_AB"],
              recomputed_ids: ["truc_day", "I"],
              skipped_unaffected_ids: ["O", "M"],
              cycle_detected: false,
            },
            stage_timings_ms: { total_ms: 4.2 },
            llm_calls: 0,
            quota_charged: false,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      })
      .mockImplementationOnce(
        async () =>
          new Response(
            JSON.stringify({
              status: "rolled_back",
              error_code: "MISSING_DEPENDENCY",
              failed_stage: "planner",
              learner_error: "Không thể dựng mặt phẳng (α) vì chưa xác định được điểm Q.",
              draft_preserved: true,
            }),
            { status: 422, headers: { "Content-Type": "application/json" } },
          ),
      );
    vi.stubGlobal("fetch", fetchMock);

    const p1 = submitConstructionStepEdit({
      sessionId: sid,
      problemKey: "sample:chop-mat-cau-ngoai-tiep",
      stepId: "mp_tt_AB",
      stepIndex: 7,
      previousInstruction: "Dựng mặt phẳng trung trực (α) của cạnh AB",
      editedInstruction: "Xác định trung điểm H của AB, dựng mặt phẳng (α) đi qua H và vuông góc với AB.",
      targetIds: ["mp_tt_AB"],
      absorbedIds: ["M_AB"],
      priorStepIds: ["A", "B", "C", "D", "S", "O", "M"],
      scene3d: baseScene,
    });
    // Concurrent duplicate submission must be ignored cleanly without issuing a 2nd fetch!
    const dup = await submitConstructionStepEdit({
      sessionId: sid,
      problemKey: "sample:chop-mat-cau-ngoai-tiep",
      stepId: "mp_tt_AB",
      stepIndex: 7,
      previousInstruction: "Dựng mặt phẳng trung trực (α) của cạnh AB",
      editedInstruction: "Duplicate",
      targetIds: ["mp_tt_AB"],
      absorbedIds: ["M_AB"],
      scene3d: baseScene,
    });
    expect(dup.status).toBe("duplicate_ignored");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const firstReqBody = JSON.parse(String(fetchMock.mock.calls[0][1]?.body ?? "{}"));
    expect(firstReqBody.prior_step_ids).toEqual(["A", "B", "C", "D", "S", "O", "M"]);

    releaseFirst();
    const okRes = await p1;
    expect(okRes.status).toBe("committed");
    const cachedAfterOk = loadCachedStepEditState(sid);
    expect(cachedAfterOk?.stepOverrides.mp_tt_AB).toContain("trung điểm H của AB");

    // Failed 422 rollback must keep cached scene intact
    const badRes = await submitConstructionStepEdit({
      sessionId: sid,
      problemKey: "sample:chop-mat-cau-ngoai-tiep",
      stepId: "mp_tt_AB",
      stepIndex: 7,
      previousInstruction: "Xác định trung điểm H của AB, dựng mặt phẳng (α) đi qua H và vuông góc với AB.",
      editedInstruction: "Dựng mặt phẳng (α) đi qua Q và vuông góc với AB.",
      targetIds: ["mp_tt_AB"],
      absorbedIds: [],
      scene3d: baseScene,
    });
    expect(badRes.status).toBe("rolled_back");
    if (badRes.status === "rolled_back") {
      expect(badRes.draft_preserved).toBe(true);
      expect(badRes.learner_error).toContain("chưa xác định được điểm Q");
    }
    expect(loadCachedStepEditState(sid)?.stepOverrides.mp_tt_AB).toContain("trung điểm H của AB");
  });

  it("Test 3 (Inline Child Coalescing & Reload UI Recovery): coalesces inline_step_parent H into (α) step and renders cached step override", () => {
    const origScene = (sample11.envelope as unknown as { scene3d: Scene3D }).scene3d;
    const modScene = structuredClone(origScene);
    // Inject inline midpoint H with source.inline_step_parent = "mp_tt_AB" right before mp_tt_AB
    const mpIdx = modScene.objects.findIndex((o) => o.id === "mp_tt_AB");
    expect(mpIdx).toBeGreaterThan(-1);
    const hObj = {
      id: "H",
      type: "point3",
      label: "Trung điểm H của AB",
      notation: "H",
      reference: "H",
      role: "Điểm H",
      origin: "derived",
      producer: "construct_point.midpoint",
      depends: ["A", "B"],
      render: "point_marker",
      display_role: "visual_owner",
      display_group: ["construction"],
      xyz: ["2", "0", "0"],
      source: {
        instruction: "construct_point.midpoint",
        binding: "TEXT_RELATION",
        inline_step_parent: "mp_tt_AB",
      },
    };
    modScene.objects = modScene.objects.filter((o) => o.id !== "M_AB");
    const insertObjIdx = modScene.objects.findIndex((o) => o.id === "mp_tt_AB");
    modScene.objects.splice(insertObjIdx, 0, hObj as unknown as Scene3D["objects"][number]);
    const mpObj = modScene.objects.find((o) => o.id === "mp_tt_AB")!;
    mpObj.depends = (mpObj.depends ?? []).map((d) => (d === "M_AB" ? "H" : d));

    const newEvents = [] as Scene3D["events"];
    for (const ev of modScene.events) {
      if (ev.object === "M_AB") continue;
      if (ev.object === "mp_tt_AB") {
        newEvents.push({
          step_index: newEvents.length,
          action: "CREATE",
          object: "H",
          depends: ["A", "B"],
          explanation: "Trung điểm H của AB",
          display_label: "H",
          learner_text: "Trung điểm H của AB",
        });
      }
      newEvents.push({
        ...ev,
        step_index: newEvents.length,
        depends: ev.object === "mp_tt_AB" ? mpObj.depends : ev.depends,
      });
    }
    modScene.events = newEvents;
    modScene.formation = undefined;

    const basePlan = buildPedagogicalConstructionPlan(structuredClone(origScene));
    const modPlan = buildPedagogicalConstructionPlan(modScene);
    expect(modPlan.steps.length).toBe(basePlan.steps.length);
    const alphaStep = modPlan.steps.find((s) => s.targetIds.includes("mp_tt_AB"));
    expect(alphaStep).toBeDefined();
    expect(alphaStep!.visibleIds).toContain("H");

    // Verify SimulationWorkspace displays the persisted override on initial render (SSR/reload recovery)
    const sid = buildStepEditSessionId("sample:chop-mat-cau-ngoai-tiep", "guest");
    const editedOverride = "Xác định trung điểm H của AB, dựng mặt phẳng (α) đi qua H và vuông góc với AB.";
    saveCachedStepEditState(sid, {
      sessionId: sid,
      problemKey: "sample:chop-mat-cau-ngoai-tiep",
      committedScene: modScene,
      stepOverrides: { mp_tt_AB: editedOverride },
      revisions: [],
      feedbackItems: [],
      updatedAt: Date.now(),
    });

    const env = structuredClone(sample11.envelope) as unknown as SimulationEnvelope;
    useAppStore.getState().loadEnvelope(env, sample11.id);
    syncStoreForSSR();
    const html = renderToString(<SimulationWorkspace />);
    expect(html).toContain(editedOverride);
  });
});
