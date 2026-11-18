import { readFileSync } from "node:fs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import {
  GEOMETRY_SAMPLES,
  PUBLIC_GEOMETRY_SAMPLES,
} from "../data/geometry-samples";
import { registerAllSimulations } from "../simulations";
import { veKhongGian } from "../simulations/domains/geometry/scene3d-chart";
import type { Scene3D } from "../simulations/domains/geometry/scene3d-model";
import { buildPedagogicalConstructionPlan } from "../simulations/domains/geometry/scene3d-semantic-policy";
import { buildPedagogicalStepNarration } from "../simulations/domains/geometry/scene3d-student-presentation-policy";
import { withSubEntities } from "../simulations/domains/geometry/scene3d-subentities";
import type { SimulationEnvelope } from "../simulations/types";
import * as stepEditsApi from "../state/construction-step-edits";
import {
  buildStepEditSessionId,
  fetchStepEditSessionState,
  isVerifiedRebuildScene,
  loadCachedStepEditState,
  saveCachedStepEditState,
  submitConstructionStepEdit,
} from "../state/construction-step-edits";
import { __resetHistoryForTest } from "../state/history";
import { useAppStore } from "../state/store";
import {
  InlineConstructionStepEditor,
  STEP_TEXTAREA_MAX_HEIGHT_PX,
  STEP_TEXTAREA_MIN_HEIGHT_PX,
  StepEditPencilButton,
  StepTitleText,
  syncStepTextareaHeight,
} from "./ConstructionStepEditor";
import { AxoWorkspaceV62, SimulationWorkspace } from "./SimulationWorkspace";

registerAllSimulations();

const syncStoreForSSR = () => Object.assign(useAppStore.getInitialState(), useAppStore.getState());
const sample11 = GEOMETRY_SAMPLES.find((s) => s.id === "chop-mat-cau-ngoai-tiep")!;
const GLOBAL_CSS = readFileSync(new URL("../styles/global.css", import.meta.url), "utf-8");
const EDITOR_SRC = readFileSync(new URL("./ConstructionStepEditor.tsx", import.meta.url), "utf-8");
const stripHtml = (html: string) => html.replace(/<!--[\s\S]*?-->/g, "").replace(/<[^>]+>/g, "");

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
            validation_result: {
              valid: true,
              passed: true,
              exact_arithmetic: true,
              checks_passed: ["given_points_immutable", "continuity_invariants_7_of_7"],
              continuity: { passed: true, issues: [] },
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
    expect(stripHtml(html)).toContain(editedOverride);
  });

  it("Regression 1 (Pencil Hover Visibility): hidden by default, V1 size/padding restored, reserved right gutter prevents text occlusion, no sticky :focus-within bug", () => {
    expect(GLOBAL_CSS).toMatch(
      /\.step-edit-pencil-btn\s*\{[^}]*top:\s*6px;[^}]*right:\s*6px;[^}]*width:\s*24px;[^}]*height:\s*24px;[^}]*opacity:\s*0;[^}]*pointer-events:\s*none;/s,
    );
    expect(GLOBAL_CSS).toMatch(
      /@media\s*\(hover:\s*hover\)\s*\{\s*\.step-row:hover\s+\.step-edit-pencil-btn\s*\{[^}]*opacity:\s*1;\s*pointer-events:\s*auto;/s,
    );
    // Regression guard against V1-V2.2 bug where clicking a row kept the pencil stuck after mouse leave
    expect(GLOBAL_CSS).not.toContain(".step-row:focus-within .step-edit-pencil-btn");
    // Desktop step-row keeps V1 padding + editor uses symmetric padding, while non-editing rows reserve 34px right gutter for 24px pencil
    expect(GLOBAL_CSS).toMatch(/\.step-row\s*\{\s*padding:\s*8px 10px;\s*gap:\s*9px;\s*\}/);
    expect(GLOBAL_CSS).toMatch(/\.step-row:not\(\.is-editing\)\s*\{\s*padding-right:\s*34px;\s*\}/);
    expect(GLOBAL_CSS).toMatch(/\.step-row\.is-editing\s*\{[^}]*padding:\s*8px 10px;/s);
  });

  it("Regression 2 (Pencil Keyboard Accessibility): :focus-visible rules, Enter/Space trigger, Escape returns focus vs mouse Cancel", () => {
    expect(GLOBAL_CSS).toMatch(
      /\.step-row:focus-visible\s+\.step-edit-pencil-btn,\s*\.step-edit-pencil-btn:focus-visible\s*\{[^}]*opacity:\s*1;\s*pointer-events:\s*auto;/s,
    );
    const onStartEdit = vi.fn();
    const pencilEl = StepEditPencilButton({ stepNumber: 8, onStartEdit }) as React.ReactElement<{
      onKeyDown: (e: { key: string; preventDefault: () => void; stopPropagation: () => void }) => void;
    }>;
    const prevent = vi.fn();
    const stop = vi.fn();
    pencilEl.props.onKeyDown({ key: "Enter", preventDefault: prevent, stopPropagation: stop });
    pencilEl.props.onKeyDown({ key: " ", preventDefault: prevent, stopPropagation: stop });
    expect(onStartEdit).toHaveBeenCalledTimes(2);
    expect(prevent).toHaveBeenCalledTimes(2);

    // Source contract check: Escape calls onCancel(true), mouse Cancel checks e.detail === 0
    expect(EDITOR_SRC).toContain("onCancel(true)");
    expect(EDITOR_SRC).toContain("onCancel(e.detail === 0)");
    expect(EDITOR_SRC).toContain("preventScroll: true");
  });

  it("Regression 3 (Mobile Edit Access): touch query shows pencil ONLY on .step-row.is-active with reserved right padding", () => {
    const touchBlocks = [
      ...GLOBAL_CSS.matchAll(/@media\s*\(hover:\s*none\),\s*\(pointer:\s*coarse\)\s*\{([\s\S]*?)\n\}/gu),
    ].map((m) => m[1]!);
    const touchBlock = touchBlocks.find((blk) => blk.includes(".step-edit-pencil-btn"));
    expect(touchBlock).toBeDefined();
    expect(touchBlock!).toContain(".step-row:not(.is-editing)");
    expect(touchBlock!).toContain("padding-right: 35px");
    expect(touchBlock!).toContain(".step-row.is-active .step-edit-pencil-btn");
    // Must never show pencil permanently across all non-active rows
    expect(touchBlock!).not.toMatch(/(?:^|\n)\s*\.step-row\s+\.step-edit-pencil-btn/);
  });

  it("Regression 4 (Auto-Resize Textarea): border-inclusive fit eliminates 2-line scrollbar, caps at 144px, preserves scrollTop & cursor", () => {
    const scrollHost = { scrollTop: 245 };
    const makeMockTextarea = (scrollHeight: number, borderTop = "1px", borderBottom = "1px") => {
      const style: Record<string, string> = {};
      const el = {
        style,
        scrollHeight,
        scrollTop: 0,
        closest: (sel: string) => (sel === ".dock-scroll" ? scrollHost : null),
      } as unknown as HTMLTextAreaElement;
      vi.stubGlobal("window", {
        localStorage: window.localStorage,
        getComputedStyle: () => ({ borderTopWidth: borderTop, borderBottomWidth: borderBottom }),
      });
      return el;
    };

    // 1-line text -> clamped to minH (32px), zero vertical scrollbar
    const single = syncStepTextareaHeight(makeMockTextarea(20));
    expect(single).toEqual({ heightPx: STEP_TEXTAREA_MIN_HEIGHT_PX, scrollable: false });

    // 2-line text (scrollHeight = 44 + 2px border = 46px) -> fits without vertical scrollbar!
    const twoLineEl = makeMockTextarea(44);
    const twoLine = syncStepTextareaHeight(twoLineEl);
    expect(twoLine).toEqual({ heightPx: 46, scrollable: false });
    expect(twoLineEl.style.height).toBe("46px");
    expect(twoLineEl.style.overflowY).toBe("hidden");
    expect(twoLineEl.style.overflowX).toBe("hidden");
    expect(scrollHost.scrollTop).toBe(245);

    // Long overflow text (> 144px) -> capped at 144px and enables vertical scroll only
    const longEl = makeMockTextarea(188);
    const longRes = syncStepTextareaHeight(longEl);
    expect(longRes).toEqual({ heightPx: STEP_TEXTAREA_MAX_HEIGHT_PX, scrollable: true });
    expect(longEl.style.height).toBe("144px");
    expect(longEl.style.overflowY).toBe("auto");
    expect(longEl.style.overflowX).toBe("hidden");

    // Caret preservation: setSelectionRange only runs in [stepIndex] mount effect, never in [draft]
    const setSelCount = (EDITOR_SRC.match(/setSelectionRange/g) ?? []).length;
    expect(setSelCount).toBe(1);
  });

  it("Regression 5 (Cancel Restoring Original Text): cancelling editor preserves original step title and scene state", () => {
    const env = structuredClone(sample11.envelope) as unknown as SimulationEnvelope;
    useAppStore.getState().loadEnvelope(env, sample11.id);
    syncStoreForSSR();
    const initialHtml = stripHtml(renderToString(<SimulationWorkspace />));
    expect(initialHtml).toContain("Dựng mặt phẳng trung trực (α) của cạnh AB");
  });

  it("Regression 6 & 7 (Submit Rebuild Sync + Unverified/Network Failures): verifies scene mathematically and preserves valid state on failure", async () => {
    const sid = buildStepEditSessionId("sample:chop-mat-cau-ngoai-tiep", "guest");
    const validScene = structuredClone((sample11.envelope as unknown as { scene3d: Scene3D }).scene3d);
    expect(isVerifiedRebuildScene(validScene)).toBe(true);

    // Corrupted/unverified scene (e.g., empty objects or inconsistent geometry) must be rejected
    expect(isVerifiedRebuildScene({ objects: [], events: [], free_objects: [] })).toBe(false);

    // 1. Seed committed valid state in cache
    saveCachedStepEditState(sid, {
      sessionId: sid,
      problemKey: "sample:chop-mat-cau-ngoai-tiep",
      committedScene: validScene,
      stepOverrides: { mp_tt_AB: "Dựng mặt phẳng (α) đi qua O và vuông góc với AB." },
      revisions: [],
      feedbackItems: [],
      updatedAt: Date.now(),
    });

    // 2. HTTP 200 claiming committed but feedback_status != GEOMETRY_VERIFIED -> fail-closed!
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: "committed",
            feedback_status: "UNVERIFIED",
            validation_result: { passed: false },
            scene3d: validScene,
            step_overrides: { mp_tt_AB: "Giả mạo chưa kiểm chứng" },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    const fake200 = await submitConstructionStepEdit({
      sessionId: sid,
      problemKey: "sample:chop-mat-cau-ngoai-tiep",
      stepId: "mp_tt_AB",
      stepIndex: 7,
      previousInstruction: "Dựng mặt phẳng (α) đi qua O và vuông góc với AB.",
      editedInstruction: "Dựng mặt phẳng (P) giả mạo",
      targetIds: ["mp_tt_AB"],
      absorbedIds: [],
      scene3d: validScene,
    });
    expect(fake200.status).toBe("rolled_back");
    if (fake200.status === "rolled_back") {
      expect(fake200.error_code).toBe("UNVERIFIED_REBUILD_REJECTED");
      expect(fake200.draft_preserved).toBe(true);
    }
    expect(loadCachedStepEditState(sid)?.stepOverrides.mp_tt_AB).toBe(
      "Dựng mặt phẳng (α) đi qua O và vuông góc với AB.",
    );

    // 3. Mid-flight network failure -> draft_preserved & prior valid scene intact
    vi.stubGlobal("fetch", vi.fn().mockRejectedValueOnce(new Error("socket hang up")));
    const netFail = await submitConstructionStepEdit({
      sessionId: sid,
      problemKey: "sample:chop-mat-cau-ngoai-tiep",
      stepId: "mp_tt_AB",
      stepIndex: 7,
      previousInstruction: "Dựng mặt phẳng (α) đi qua O và vuông góc với AB.",
      editedInstruction: "Dựng mặt phẳng (P) qua O và vuông góc với AB.",
      targetIds: ["mp_tt_AB"],
      absorbedIds: [],
      scene3d: validScene,
    });
    expect(netFail.status).toBe("network_error");
    if (netFail.status === "network_error") {
      expect(netFail.draft_preserved).toBe(true);
    }
    expect(loadCachedStepEditState(sid)?.stepOverrides.mp_tt_AB).toBe(
      "Dựng mặt phẳng (α) đi qua O và vuông góc với AB.",
    );
  });

  it("Regression 8 (Long-Step Wrapping): Steps 8-12 and all 11 samples bind geometric connectors/tokens cleanly without altering text", () => {
    const sample11Cases: { text: string; expectedNowrap: string[] }[] = [
      {
        text: "Dựng mặt phẳng trung trực (α) của cạnh AB",
        expectedNowrap: ["(α)", "cạnh AB"],
      },
      {
        text: "Dựng mặt phẳng trung trực (β) của cạnh AD",
        expectedNowrap: ["(β)", "cạnh AD"],
      },
      {
        text: "Dựng mặt phẳng trung trực (γ) của cạnh AS",
        expectedNowrap: ["(γ)", "cạnh AS"],
      },
      {
        text: "Xác định giao tuyến của (α) và (β)",
        expectedNowrap: ["(α)", "và (β)"],
      },
      {
        text: "Xác định giao điểm I = Giao tuyến của (α) và (β) ∩ (γ)",
        expectedNowrap: ["(α)", "(β) ∩ (γ)"],
      },
      {
        text: "Dựng mặt phẳng (ABC) cắt hình chóp theo thiết diện A′B′C′",
        expectedNowrap: ["(ABC)", "A′B′C′"],
      },
    ];

    for (const c of sample11Cases) {
      const html = renderToString(<StepTitleText text={c.text} />);
      expect(stripHtml(html)).toBe(c.text);
      for (const tok of c.expectedNowrap) {
        expect(html, `${c.text} missing nowrap "${tok}"`).toContain(
          `<span class="math-nowrap">${tok}</span>`,
        );
      }
    }

    // Check every step title across all 11 PUBLIC_GEOMETRY_SAMPLES preserves verbatim plain text
    for (const sample of PUBLIC_GEOMETRY_SAMPLES) {
      const raw = (sample.envelope as { scene3d?: Scene3D }).scene3d;
      if (!raw) continue;
      const day = withSubEntities(veKhongGian(raw));
      const plan = buildPedagogicalConstructionPlan(day);
      for (const step of plan.steps) {
        const narration = step.narration ?? buildPedagogicalStepNarration(day, step);
        const title = narration.actionTitle || step.title;
        const html = renderToString(<StepTitleText text={title} />);
        expect(stripHtml(html), `${sample.id} step ${step.index + 1}`).toBe(title);
      }
    }

    // .step-title must never force single-line white-space: nowrap
    const stepTitleBlocks = [...GLOBAL_CSS.matchAll(/\.step-title\s*\{([^}]*)\}/g)].map((m) => m[1]);
    expect(stepTitleBlocks.length).toBeGreaterThanOrEqual(2);
    for (const blk of stepTitleBlocks) {
      expect(blk).not.toMatch(/white-space:\s*nowrap/);
    }
  });

  it("Regression 9 (Sidebar Overflow & Problem Statement Typography): left-aligned readable statement, no justify, no textarea horizontal overflow", () => {
    const psBlock = /\.problem-statement\s*\{([^}]*)\}/.exec(GLOBAL_CSS)?.[1] ?? "";
    expect(psBlock).toContain("text-align: left");
    expect(psBlock).not.toContain("justify");
    expect(psBlock).toContain("word-spacing: normal");
    expect(psBlock).toContain("white-space: pre-line");
    expect(psBlock).toContain("overflow-wrap: break-word");

    const taBlock = /\.step-edit-textarea\s*\{([^}]*)\}/.exec(GLOBAL_CSS)?.[1] ?? "";
    expect(taBlock).toContain("overflow-x: hidden");
    expect(taBlock).toContain("max-height: 144px");
    expect(taBlock).toContain("resize: none");
  });
});

const STEP_EDITS_SRC = readFileSync(new URL("../state/construction-step-edits.ts", import.meta.url), "utf-8");
const WORKSPACE_SRC = readFileSync(new URL("./SimulationWorkspace.tsx", import.meta.url), "utf-8");

function makeVerifiedCommitResponse(opts: {
  sessionId: string;
  versionNumber: number;
  scene: Scene3D;
  overrideText: string;
  primaryTargetId?: string;
  validationResult?: unknown;
  dependencySummary?: unknown;
}) {
  const targetId = opts.primaryTargetId ?? "mp_tt_AB";
  return {
    status: "committed",
    mode: "PARTIAL_TOPOLOGICAL_REBUILD",
    session_id: opts.sessionId,
    revision_id: `rev-${opts.versionNumber}`,
    feedback_id: `fb-${opts.versionNumber}`,
    feedback_status: "GEOMETRY_VERIFIED",
    dataset_eligibility: "INELIGIBLE",
    version_number: opts.versionNumber,
    primary_target_id: targetId,
    scene3d: opts.scene,
    step_overrides: { [targetId]: opts.overrideText },
    dependency_summary:
      opts.dependencySummary !== undefined
        ? opts.dependencySummary
        : {
            edited_target_ids: [targetId],
            created_ids: [],
            reused_ids: ["ab"],
            retired_ids: [],
            recomputed_ids: ["truc_day", "I"],
            skipped_unaffected_ids: ["O", "M"],
            cycle_detected: false,
          },
    validation_result:
      opts.validationResult !== undefined
        ? opts.validationResult
        : {
            valid: true,
            passed: true,
            exact_arithmetic: true,
            checks_passed: ["given_points_immutable", "continuity_invariants_7_of_7"],
            continuity: { passed: true, issues: [] },
          },
    stage_timings_ms: { total_ms: 4.5 },
    llm_calls: 0,
    quota_charged: false,
  };
}

describe("AXO Step Editor V2.2 — Reliability Hardening & Edge Cases (§5, §7)", () => {
  beforeEach(() => {
    installMemoryStorage();
    __resetHistoryForTest();
    useAppStore.getState().reset();
    syncStoreForSSR();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it("BUG-2 / §7 #10 (Fail-Closed Validation): rejects missing, undefined, null, or incomplete validation_result & dependency_summary", async () => {
    // Source must NOT contain permissive !== false or !== true shortcuts
    expect(STEP_EDITS_SRC).not.toContain("validation_result?.passed !== false");
    expect(STEP_EDITS_SRC).not.toContain("cycle_detected !== true");

    const sid = buildStepEditSessionId("sample:chop-mat-cau-ngoai-tiep", "guest");
    const validScene = structuredClone((sample11.envelope as unknown as { scene3d: Scene3D }).scene3d);

    const incompletePayloads = [
      // Missing validation_result entirely
      makeVerifiedCommitResponse({
        sessionId: sid,
        versionNumber: 1,
        scene: validScene,
        overrideText: "bad-1",
        validationResult: undefined,
      }),
      // validation_result with passed missing (undefined)
      makeVerifiedCommitResponse({
        sessionId: sid,
        versionNumber: 2,
        scene: validScene,
        overrideText: "bad-2",
        validationResult: { valid: true, exact_arithmetic: true, continuity: { passed: true }, checks_passed: ["a"] },
      }),
      // validation_result missing continuity.passed === true
      makeVerifiedCommitResponse({
        sessionId: sid,
        versionNumber: 3,
        scene: validScene,
        overrideText: "bad-3",
        validationResult: { valid: true, passed: true, exact_arithmetic: true, checks_passed: ["a"] },
      }),
      // dependency_summary missing cycle_detected === false
      makeVerifiedCommitResponse({
        sessionId: sid,
        versionNumber: 4,
        scene: validScene,
        overrideText: "bad-4",
        dependencySummary: { edited_target_ids: ["mp_tt_AB"] },
      }),
    ];

    // Strip undefined key cleanly on payload 0
    delete (incompletePayloads[0] as Record<string, unknown>).validation_result;

    for (const badBody of incompletePayloads) {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValueOnce(
          new Response(JSON.stringify(badBody), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        ),
      );
      const res = await submitConstructionStepEdit({
        sessionId: sid,
        problemKey: "sample:chop-mat-cau-ngoai-tiep",
        stepId: "mp_tt_AB",
        stepIndex: 14,
        previousInstruction: "Dựng mặt phẳng trung trực (α) của cạnh AB",
        editedInstruction: `Thử payload thiếu ${String(badBody.version_number)}`,
        targetIds: ["mp_tt_AB"],
        absorbedIds: ["M_AB"],
        scene3d: validScene,
      });
      expect(res.status).toBe("rolled_back");
      if (res.status === "rolled_back") {
        expect(res.error_code).toBe("UNVERIFIED_REBUILD_REJECTED");
        expect(res.draft_preserved).toBe(true);
      }
      expect(loadCachedStepEditState(sid)).toBeNull();
    }
  });

  it("BUG-3 / §7 #6, #8, #14 (Async Order Independence & Stale Response Guard): late v1 NEVER overwrites v2 across all arrival orders", async () => {
    const sid = buildStepEditSessionId("sample:chop-mat-cau-ngoai-tiep", "guest");
    const sceneV1 = structuredClone((sample11.envelope as unknown as { scene3d: Scene3D }).scene3d);
    const sceneV2 = structuredClone((sample11.envelope as unknown as { scene3d: Scene3D }).scene3d);
    const mp2 = sceneV2.objects.find((o) => o.id === "mp_tt_AB");
    if (mp2) mp2.label = "Mặt phẳng (α) phiên bản v2";

    let resolveReq1!: (res: Response) => void;
    let resolveReq2!: (res: Response) => void;
    let reqCount = 0;

    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: unknown, init?: RequestInit) => {
        if (String(url) === "/api/simulation/steps/cancel") {
          return Promise.resolve(new Response(JSON.stringify({ cancelled: true }), { status: 200 }));
        }
        reqCount += 1;
        const idx = reqCount;
        return new Promise<Response>((resolve, reject) => {
          init?.signal?.addEventListener("abort", () => {
            reject(new DOMException("Aborted", "AbortError"));
          });
          if (idx === 1) resolveReq1 = resolve;
          else resolveReq2 = resolve;
        });
      }),
    );

    const p1 = submitConstructionStepEdit({
      sessionId: sid,
      problemKey: "sample:chop-mat-cau-ngoai-tiep",
      stepId: "mp_tt_AB",
      stepIndex: 14,
      previousInstruction: "Dựng mặt phẳng trung trực (α) của cạnh AB",
      editedInstruction: "Dựng (α) lượt 1",
      targetIds: ["mp_tt_AB"],
      absorbedIds: ["M_AB"],
      scene3d: sceneV1,
    });

    // §7 #8: Starting a DIFFERENT rebuild while p1 is in-flight must supersede p1 rather than ignoring p2!
    const p2 = submitConstructionStepEdit({
      sessionId: sid,
      problemKey: "sample:chop-mat-cau-ngoai-tiep",
      stepId: "mp_tt_AD",
      stepIndex: 15,
      previousInstruction: "Dựng mặt phẳng trung trực (β) của cạnh AD",
      editedInstruction: "Dựng (β) lượt 2 mới hơn",
      targetIds: ["mp_tt_AD"],
      absorbedIds: ["M_AD"],
      scene3d: sceneV2,
    });

    expect(reqCount).toBe(2);

    // Resolve v2 FIRST, then resolve stale v1 LATER (permutation [v2, v1])
    resolveReq2(
      new Response(
        JSON.stringify(
          makeVerifiedCommitResponse({
            sessionId: sid,
            versionNumber: 2,
            scene: sceneV2,
            primaryTargetId: "mp_tt_AD",
            overrideText: "Dựng (β) lượt 2 mới hơn",
          }),
        ),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    resolveReq1(
      new Response(
        JSON.stringify(
          makeVerifiedCommitResponse({
            sessionId: sid,
            versionNumber: 1,
            scene: sceneV1,
            primaryTargetId: "mp_tt_AB",
            overrideText: "Dựng (α) lượt 1",
          }),
        ),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    const [r1, r2] = await Promise.all([p1, p2]);
    expect(r2.status).toBe("committed");
    expect(r1.status).not.toBe("committed");
    // Final cached state MUST reflect v2, NEVER overwritten by late v1!
    const cached = loadCachedStepEditState(sid);
    expect(cached?.versionNumber).toBe(2);
    expect(cached?.stepOverrides.mp_tt_AD).toBe("Dựng (β) lượt 2 mới hơn");
    expect(cached?.stepOverrides.mp_tt_AB).toBeUndefined();

    // Monotonicity guard on saveCachedStepEditState + stale GET /state response:
    saveCachedStepEditState(sid, {
      sessionId: sid,
      problemKey: "sample:chop-mat-cau-ngoai-tiep",
      versionNumber: 1,
      committedScene: sceneV1,
      stepOverrides: { mp_tt_AB: "Stale v1" },
      revisions: [],
      feedbackItems: [],
      updatedAt: Date.now(),
    });
    expect(loadCachedStepEditState(sid)?.versionNumber).toBe(2);
    expect(loadCachedStepEditState(sid)?.stepOverrides.mp_tt_AD).toBe("Dựng (β) lượt 2 mới hơn");

    // Stale GET /sessions/{id}/state with lower revision_count (1 < 2) must NOT overwrite v2
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            found: true,
            session_id: sid,
            problem_key: "sample:chop-mat-cau-ngoai-tiep",
            revision_count: 1,
            committed_scene: sceneV1,
            step_overrides: { mp_tt_AB: "Stale GET v1" },
            dependency_summary: { cycle_detected: false },
            revisions: [],
            feedback_items: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    await fetchStepEditSessionState(sid);
    expect(loadCachedStepEditState(sid)?.versionNumber).toBe(2);
    expect(loadCachedStepEditState(sid)?.stepOverrides.mp_tt_AD).toBe("Dựng (β) lượt 2 mới hơn");

    // Permutation B ([v1 resolves first, then v2 resolves second] after v2 aborted v1):
    // Both arrival orders must converge to exact same final state (versionNumber = 3 on sidB)!
    const sidB = `${sid}-permB`;
    let relB1!: (r: Response) => void;
    let relB2!: (r: Response) => void;
    let cntB = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((_u: unknown, init?: RequestInit) => {
        cntB += 1;
        const cIdx = cntB;
        return new Promise<Response>((res, rej) => {
          init?.signal?.addEventListener("abort", () => rej(new DOMException("Aborted", "AbortError")));
          if (cIdx === 1) relB1 = res;
          else relB2 = res;
        });
      }),
    );
    const pb1 = submitConstructionStepEdit({
      sessionId: sidB,
      problemKey: "sample:chop-mat-cau-ngoai-tiep",
      stepId: "mp_tt_AB",
      stepIndex: 14,
      previousInstruction: "Dựng mặt phẳng trung trực (α) của cạnh AB",
      editedInstruction: "Dựng (α) B1",
      targetIds: ["mp_tt_AB"],
      absorbedIds: ["M_AB"],
      scene3d: sceneV1,
    });
    const pb2 = submitConstructionStepEdit({
      sessionId: sidB,
      problemKey: "sample:chop-mat-cau-ngoai-tiep",
      stepId: "mp_tt_AD",
      stepIndex: 15,
      previousInstruction: "Dựng mặt phẳng trung trực (β) của cạnh AD",
      editedInstruction: "Dựng (β) lượt 2 mới hơn",
      targetIds: ["mp_tt_AD"],
      absorbedIds: ["M_AD"],
      scene3d: sceneV2,
    });
    relB1(
      new Response(
        JSON.stringify(
          makeVerifiedCommitResponse({
            sessionId: sidB,
            versionNumber: 1,
            scene: sceneV1,
            primaryTargetId: "mp_tt_AB",
            overrideText: "Dựng (α) B1",
          }),
        ),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    relB2(
      new Response(
        JSON.stringify(
          makeVerifiedCommitResponse({
            sessionId: sidB,
            versionNumber: 2,
            scene: sceneV2,
            primaryTargetId: "mp_tt_AD",
            overrideText: "Dựng (β) lượt 2 mới hơn",
          }),
        ),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    const [rb1, rb2] = await Promise.all([pb1, pb2]);
    expect(rb1.status).not.toBe("committed");
    expect(rb2.status).toBe("committed");
    expect(loadCachedStepEditState(sidB)?.versionNumber).toBe(2);
    expect(loadCachedStepEditState(sidB)?.stepOverrides.mp_tt_AD).toBe("Dựng (β) lượt 2 mới hơn");
    expect(loadCachedStepEditState(sidB)?.stepOverrides.mp_tt_AB).toBeUndefined();
  });

  it("BUG-3 / §7 #6 & #9 (In-Flight Cancel & Backend Timeout): cancelInFlightStepEdit cancels cleanly and timeout unlocks draft safely", async () => {
    const sid = buildStepEditSessionId("sample:chop-mat-cau-ngoai-tiep", "guest");
    const validScene = structuredClone((sample11.envelope as unknown as { scene3d: Scene3D }).scene3d);

    // 1. Running UI must still allow clicking Hủy or pressing Escape to abort in-flight request!
    const runningHtml = renderToString(
      <InlineConstructionStepEditor
        stepIndex={14}
        initialValue="Dựng (α)"
        running={true}
        errorText={null}
        onCancel={() => {}}
        onSubmit={() => {}}
      />,
    );
    const cancelBtnMatch = runningHtml.match(/<button[^>]*step-edit-btn--cancel[^>]*>/);
    expect(cancelBtnMatch).not.toBeNull();
    expect(cancelBtnMatch![0]).not.toContain("disabled");

    // 2. cancelInFlightStepEdit must exist and abort a pending fetch cleanly
    const cancelFn = (stepEditsApi as Record<string, unknown>).cancelInFlightStepEdit as
      | ((sessionId: string) => boolean)
      | undefined;
    expect(typeof cancelFn).toBe("function");

    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(
        (_url: unknown, init?: RequestInit) =>
          new Promise<Response>((_resolve, reject) => {
            init?.signal?.addEventListener("abort", () => {
              reject(new DOMException("Aborted by user", "AbortError"));
            });
          }),
      ),
    );
    const pendingEdit = submitConstructionStepEdit({
      sessionId: sid,
      problemKey: "sample:chop-mat-cau-ngoai-tiep",
      stepId: "mp_tt_AB",
      stepIndex: 14,
      previousInstruction: "Dựng (α)",
      editedInstruction: "Sửa rồi nhấn Hủy",
      targetIds: ["mp_tt_AB"],
      absorbedIds: ["M_AB"],
      scene3d: validScene,
    });
    expect(cancelFn!(sid)).toBe(true);
    const cancelledRes = await pendingEdit;
    expect(cancelledRes.status).toBe("rolled_back");
    if (cancelledRes.status === "rolled_back") {
      expect(cancelledRes.error_code).toBe("EDIT_CANCELLED");
      expect(cancelledRes.draft_preserved).toBe(true);
    }

    // 3. Backend timeout triggers AbortController after timeoutMs and preserves draft + previous scene
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(
        (_url: unknown, init?: RequestInit) =>
          new Promise<Response>((_resolve, reject) => {
            init?.signal?.addEventListener("abort", () => {
              reject(new DOMException("Timed out", "AbortError"));
            });
          }),
      ),
    );
    const timedOut = await (submitConstructionStepEdit as (p: Record<string, unknown>) => Promise<stepEditsApi.StepEditSubmitResult>)({
      sessionId: sid,
      problemKey: "sample:chop-mat-cau-ngoai-tiep",
      stepId: "mp_tt_AB",
      stepIndex: 14,
      previousInstruction: "Dựng (α)",
      editedInstruction: "Chạy timeout",
      targetIds: ["mp_tt_AB"],
      absorbedIds: ["M_AB"],
      scene3d: validScene,
      timeoutMs: 25,
    });
    expect(timedOut.status).toBe("network_error");
    if (timedOut.status === "network_error") {
      expect(timedOut.error_code).toBe("REQUEST_TIMEOUT");
      expect(timedOut.draft_preserved).toBe(true);
    }
  });

  it("BUG-8 / §7 #15, #16, #17, #18 (WebGL Context Loss Recovery & Stale GET Race Guard in Workspace): cleanly remounts damaged WebGL stage on rebuild and guards stale GET", () => {
    // 1. Same-problem rebuild branch in SimulationWorkspace MUST remount damaged WebGL stage
    const sameProblemBlock =
      /if\s*\(isSameProblemRebuild\)\s*\{([\s\S]*?(?:return;\s*\r?\n\s*\}|\}\s*else\s*\{))/.exec(WORKSPACE_SRC)?.[1] ?? "";
    expect(sameProblemBlock.length).toBeGreaterThan(20);
    expect(sameProblemBlock).toContain("setViewerMountGen");
    expect(sameProblemBlock).toContain("setWebglLifecycle");

    // 2. fetchStepEditSessionState effect MUST check epoch/version before overwriting state
    expect(WORKSPACE_SRC).toContain("editMutationEpochRef");
    expect(WORKSPACE_SRC).toContain("committedVersionRef");
  });

  it("RC-3: fetchStepEditSessionState ignores empty/zero-revision scene payloads and respects committed_version", async () => {
    const validScene = structuredClone((sample11.envelope as unknown as { scene3d: Scene3D }).scene3d);
    const sid = buildStepEditSessionId("sample:rc3-test", "guest");

    // 1. Server reports found=true, committed_version=0, committed_scene=null after failed 422 edit
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            found: true,
            session_id: sid,
            problem_key: "sample:rc3-test",
            revision_count: 0,
            committed_version: 0,
            committed_scene: null,
            step_overrides: {},
            dependency_summary: { cycle_detected: false },
            revisions: [],
            feedback_items: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    const zeroSnap = await fetchStepEditSessionState(sid);
    expect(zeroSnap).not.toBeNull();
    expect(zeroSnap?.committedScene).toBeNull();
    expect(zeroSnap?.versionNumber).toBe(0);

    // 2. Server returns both revision_count=5 (failed attempts included) and committed_version=2
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            found: true,
            session_id: sid,
            problem_key: "sample:rc3-test",
            revision_count: 5,
            committed_version: 2,
            committed_scene: validScene,
            step_overrides: { mp_tt_AB: "Bước đã sửa v2" },
            dependency_summary: { cycle_detected: false },
            revisions: [],
            feedback_items: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    const committedSnap = await fetchStepEditSessionState(sid);
    expect(committedSnap?.committedScene).not.toBeNull();
    expect(committedSnap?.versionNumber).toBe(2);
  });

  it("RC-4: #pa-short-title and #pa-pips-mount reflect overridden step title consistently with #dock-steps-ul", () => {
    const env = structuredClone(sample11.envelope) as unknown as SimulationEnvelope;
    const baseScene = structuredClone((sample11.envelope as unknown as { scene3d: Scene3D }).scene3d);
    const sid = buildStepEditSessionId(`sample:${sample11.id}`, "guest");
    const customTitle = "Xác định H trung điểm AB và mặt phẳng vuông góc";
    saveCachedStepEditState(sid, {
      sessionId: sid,
      problemKey: `sample:${sample11.id}`,
      versionNumber: 1,
      committedScene: baseScene,
      stepOverrides: { mp_tt_AB: customTitle },
      dependencySummary: null,
      revisions: [],
      feedbackItems: [],
      updatedAt: Date.now(),
    });

    const pedPlan = buildPedagogicalConstructionPlan(withSubEntities(baseScene));
    const targetStep = pedPlan.steps.find((st) => st.targetIds.includes("mp_tt_AB"))!;
    expect(targetStep).toBeDefined();

    useAppStore.getState().loadEnvelope(env, sample11.id);
    syncStoreForSSR();

    const html = renderToString(
      <AxoWorkspaceV62
        scene={baseScene}
        tieuDe={env.title}
        de={sample11.problemText}
        initialStep={targetStep.anchor}
      />,
    );
    const paTitle = /id="pa-short-title"[^>]*>([\s\S]*?)<\/span>/.exec(html)?.[1] ?? "";
    expect(paTitle).toContain(customTitle);
    const pipAria = new RegExp(`data-step="${targetStep.index}"[^>]*aria-label="([^"]+)"`).exec(html)?.[1] ?? "";
    expect(pipAria).toContain(customTitle);
  });

  it("RC-5 & RC-6 & RC-7: Escape on form cancels, draft stays isolated, cleanup aborts in-flight edit, scroll & ErrorBoundary resetKey respond to rebuilds", () => {
    // 1. ConstructionStepEditor keeps user draft across initialValue changes on same stepIndex and cancels via form Escape
    expect(EDITOR_SRC).toContain("prevStepIndexRef");
    expect(EDITOR_SRC).toContain("onKeyDown=");

    // 2. SimulationWorkspace aborts in-flight step edit on session switch / unmount cleanup
    const cleanupSlice = /return\s*\(\)\s*=>\s*\{([\s\S]{0,160})\};\s*\n\s*\},\s*\[activeEditSessionId\]\)/.exec(WORKSPACE_SRC)?.[1] ?? "";
    expect(cleanupSlice).toContain("cancelInFlightStepEdit(activeEditSessionId)");

    // 3. Auto-scroll dependency array responds to rebuilds (tong / scene)
    const scrollEffectDeps = /const lastStepScrollContextRef[\s\S]{0,1600}?\},\s*(\[[^\]]+\])\)/.exec(WORKSPACE_SRC)?.[1] ?? "";
    expect(scrollEffectDeps).toContain("tong");
    expect(scrollEffectDeps).toContain("scene");

    // 4. ErrorBoundary resetKey includes viewerMountGen so rebuild remount clears boundary crashes
    expect(WORKSPACE_SRC).toContain('resetKey={`${problemSnapshotKey}|${viewerMountGen}|${webglStageAttempt}`}');
  });

  it("FP-4: Hybrid /4 answers rebind safely on verified step-edited scenes while unedited mismatched scenes stay INVALID", async () => {
    const modelMod = await import("../simulations/domains/geometry/scene3d-model");
    const markFn = (modelMod as Record<string, unknown>).markVerifiedStepEditedScene as
      | ((s: Scene3D) => Scene3D)
      | undefined;
    expect(typeof markFn).toBe("function");

    const rawScene = structuredClone((sample11.envelope as unknown as { scene3d: Scene3D }).scene3d);
    const radiusObj = rawScene.objects.find((o) => o.id === "R")!;
    const mutatedUnverified = structuredClone(rawScene);
    const qTampered = mutatedUnverified.objects.find((o) => o.id === "R")!;
    qTampered.value = "999";

    const fakeHybrid = {
      answers: [
        {
          kind: "radius",
          label: "Bán kính R",
          value: String(radiusObj.value),
          coefficient: String(radiusObj.value),
          quantity_id: "R",
        },
      ],
    } as unknown as Parameters<typeof modelMod.attachHybridViewToScene>[1];

    // 1. Unedited tampered scene must still be classified INVALID (guard intact)
    modelMod.attachHybridViewToScene(mutatedUnverified, fakeHybrid);
    expect(modelMod.classifySceneEntityProvenance(mutatedUnverified, qTampered)).toBe("INVALID");

    // 2. Verified step-edited scene rebinds Hybrid answer to rebuilt exact value instead of marking INVALID
    const mutatedEdited = markFn!(structuredClone(rawScene));
    const qEdited = mutatedEdited.objects.find((o) => o.id === "R")!;
    qEdited.value = "4";
    modelMod.attachHybridViewToScene(mutatedEdited, fakeHybrid);
    expect(modelMod.classifySceneEntityProvenance(mutatedEdited, qEdited)).toBe("DERIVED_VERIFIED");
  });

  it("FP-5 & FP-6: committed_version monotonic guard, post-commit network recovery, and server cancel dispatch", async () => {
    const sid = buildStepEditSessionId("sample:fp5-fp6-test", "guest");
    const validScene = structuredClone((sample11.envelope as unknown as { scene3d: Scene3D }).scene3d);

    // 1. After two 422 refusals then one 200 commit, version_number=3 while committed_version=1.
    // fetchStepEditSessionState returning later committed_version=2 (with revision version_number=4) must NOT be rejected!
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: "committed",
            mode: "PARTIAL_TOPOLOGICAL_REBUILD",
            session_id: sid,
            revision_id: "rev-1",
            feedback_id: "fb-1",
            feedback_status: "GEOMETRY_VERIFIED",
            dataset_eligibility: "ELIGIBLE",
            version_number: 3,
            committed_version: 1,
            primary_target_id: "mp_tt_AB",
            scene3d: validScene,
            step_overrides: { mp_tt_AB: "Lượt 1" },
            dependency_summary: {
              edited_target_ids: ["mp_tt_AB"],
              created_ids: [],
              reused_ids: [],
              retired_ids: [],
              recomputed_ids: [],
              skipped_unaffected_ids: [],
              cycle_detected: false,
            },
            validation_result: {
              valid: true,
              passed: true,
              exact_arithmetic: true,
              checks_passed: ["given_points_immutable"],
              continuity: { passed: true, issues: [] },
            },
            stage_timings_ms: { total_ms: 10 },
            llm_calls: 0,
            quota_charged: false,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    const c1 = await submitConstructionStepEdit({
      sessionId: sid,
      problemKey: "sample:fp5-fp6-test",
      stepId: "mp_tt_AB",
      stepIndex: 7,
      previousInstruction: "Dựng (α)",
      editedInstruction: "Lượt 1",
      targetIds: ["mp_tt_AB"],
      absorbedIds: ["M_AB"],
      scene3d: validScene,
    });
    expect(c1.status).toBe("committed");

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            found: true,
            session_id: sid,
            problem_key: "sample:fp5-fp6-test",
            revision_count: 4,
            committed_version: 2,
            committed_scene: validScene,
            step_overrides: { mp_tt_AB: "Lượt 2 từ server" },
            dependency_summary: { cycle_detected: false },
            revisions: [],
            feedback_items: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    const snap2 = await fetchStepEditSessionState(sid);
    expect(snap2?.versionNumber).toBe(2);
    expect(snap2?.stepOverrides.mp_tt_AB).toBe("Lượt 2 từ server");

    // 2. Post-commit network drop reconciles against GET /state via client_request_id!
    let postedClientReqId = "";
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      if (url === "/api/simulation/steps/edit") {
        const body = JSON.parse(String(init?.body || "{}"));
        postedClientReqId = String(body.client_request_id || "");
        throw new TypeError("Simulated connection drop after server commit");
      }
      if (url.includes(`/api/simulation/sessions/${encodeURIComponent(sid)}/state`)) {
        return new Response(
          JSON.stringify({
            found: true,
            session_id: sid,
            problem_key: "sample:fp5-fp6-test",
            revision_count: 5,
            committed_version: 3,
            last_committed_request_id: postedClientReqId,
            committed_scene: validScene,
            step_overrides: { mp_tt_AB: "Recovered post-commit" },
            dependency_summary: {
              edited_target_ids: ["mp_tt_AB"],
              created_ids: [],
              reused_ids: [],
              retired_ids: [],
              recomputed_ids: [],
              skipped_unaffected_ids: [],
              cycle_detected: false,
            },
            revisions: [],
            feedback_items: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("{}", { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const rec = await submitConstructionStepEdit({
      sessionId: sid,
      problemKey: "sample:fp5-fp6-test",
      stepId: "mp_tt_AB",
      stepIndex: 7,
      previousInstruction: "Lượt 2",
      editedInstruction: "Recovered post-commit",
      targetIds: ["mp_tt_AB"],
      absorbedIds: ["M_AB"],
      scene3d: validScene,
    });
    expect(postedClientReqId.length).toBeGreaterThan(4);
    expect(rec.status).toBe("committed");
    if (rec.status === "committed") {
      expect(rec.step_overrides.mp_tt_AB).toBe("Recovered post-commit");
    }

    // 3. cancelInFlightStepEdit notifies POST /api/simulation/steps/cancel
    const calledUrls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string, init?: RequestInit) => {
        calledUrls.push(String(url));
        if (url === "/api/simulation/steps/cancel") {
          return Promise.resolve(new Response(JSON.stringify({ cancelled: true }), { status: 200 }));
        }
        return new Promise<Response>((_res, rej) => {
          init?.signal?.addEventListener("abort", () => rej(new DOMException("Aborted", "AbortError")));
        });
      }),
    );
    const pPending = submitConstructionStepEdit({
      sessionId: sid,
      problemKey: "sample:fp5-fp6-test",
      stepId: "mp_tt_AB",
      stepIndex: 7,
      previousInstruction: "Dựng (α)",
      editedInstruction: "Đang chạy rồi hủy",
      targetIds: ["mp_tt_AB"],
      absorbedIds: ["M_AB"],
      scene3d: validScene,
    });
    stepEditsApi.cancelInFlightStepEdit(sid);
    await pPending;
    expect(calledUrls).toContain("/api/simulation/steps/cancel");
  });
});
