import { veKhongGian } from "../simulations/domains/geometry/scene3d-chart";
import {
  hopLeScene3D,
  inspectScene3DPayloadIntegrity,
  markVerifiedStepEditedScene,
  type Scene3D,
} from "../simulations/domains/geometry/scene3d-model";
import { verifySceneMathematicalConsistency } from "../simulations/domains/geometry/scene3d-semantic-policy";

export const AXO_CLIENT_SESSION_HEADER = "X-Axo-Client-Session";

const CLIENT_TOKEN_STORAGE_KEY = "axo:client-session-id:v1";
const STEP_STATE_STORAGE_PREFIX = "axo:step-edits:v1:";

export interface StepEditDependencySummary {
  edited_target_ids: string[];
  created_ids: string[];
  reused_ids: string[];
  retired_ids: string[];
  recomputed_ids: string[];
  skipped_unaffected_ids: string[];
  cycle_detected: boolean;
}

export interface StepEditRevisionItem {
  revision_id: string;
  version_number: number;
  step_id: string;
  step_index: number;
  previous_instruction: string;
  edited_instruction: string;
  validation_status: string;
  execution_status: string;
  error_code?: string | null;
  learner_error?: string | null;
}

export interface StepEditFeedbackItem {
  feedback_id: string;
  revision_id: string;
  problem_group_key: string;
  original_step: string;
  corrected_step: string;
  user_acceptance_status: string;
  dataset_eligibility: string;
}

export interface PersistedStepEditSnapshot {
  sessionId: string;
  problemKey: string;
  versionNumber?: number;
  committedScene: Scene3D | null;
  stepOverrides: Record<string, string>;
  dependencySummary?: StepEditDependencySummary | null;
  revisions: StepEditRevisionItem[];
  feedbackItems: StepEditFeedbackItem[];
  updatedAt: number;
}

export interface StepEditValidationResult {
  valid?: boolean;
  passed?: boolean;
  exact_arithmetic?: boolean;
  checks_passed?: string[];
  change_classification?: string;
  continuity?: { passed?: boolean; issues?: unknown[] } | null;
}

export interface StepEditSubmitSuccess {
  status: "committed";
  mode: string;
  equivalence_info?: {
    geometrically_equivalent?: boolean;
    change_classification?: string;
    [k: string]: unknown;
  } | null;
  session_id: string;
  revision_id: string;
  feedback_id: string;
  feedback_status: string;
  dataset_eligibility: string;
  version_number: number;
  committed_version?: number;
  primary_target_id: string;
  scene3d: Scene3D;
  step_overrides: Record<string, string>;
  dependency_summary: StepEditDependencySummary;
  validation_result?: StepEditValidationResult | null;
  stage_timings_ms: Record<string, number>;
  llm_calls: number;
  quota_charged: boolean;
}

export function isVerifiedRebuildScene(scene: unknown): scene is Scene3D {
  try {
    if (!hopLeScene3D(scene)) return false;
    if (!inspectScene3DPayloadIntegrity(scene).valid) return false;
    const world = veKhongGian(scene);
    return verifySceneMathematicalConsistency(world).valid;
  } catch {
    return false;
  }
}

export function isVerifiedStepEditCommitResponse(data: unknown): data is StepEditSubmitSuccess {
  if (!data || typeof data !== "object") return false;
  const d = data as Partial<StepEditSubmitSuccess>;
  if (d.status !== "committed" || d.feedback_status !== "GEOMETRY_VERIFIED") return false;
  if (typeof d.version_number !== "number" || !Number.isInteger(d.version_number) || d.version_number < 1) {
    return false;
  }
  if (typeof d.primary_target_id !== "string" || !d.primary_target_id.trim()) return false;
  const val = d.validation_result;
  if (
    !val
    || val.passed !== true
    || val.valid !== true
    || val.exact_arithmetic !== true
    || !val.continuity
    || val.continuity.passed !== true
    || !Array.isArray(val.checks_passed)
    || val.checks_passed.length === 0
  ) {
    return false;
  }
  const dep = d.dependency_summary;
  if (
    !dep
    || dep.cycle_detected !== false
    || !Array.isArray(dep.edited_target_ids)
    || dep.edited_target_ids.length === 0
  ) {
    return false;
  }
  if (!isVerifiedRebuildScene(d.scene3d)) return false;
  return d.scene3d.objects.some((o) => o.id === d.primary_target_id);
}

export interface StepEditSubmitRefusal {
  status: "rolled_back" | "network_error" | "duplicate_ignored";
  error_code: string;
  failed_stage: string;
  learner_error: string;
  draft_preserved: boolean;
}

export type StepEditSubmitResult = StepEditSubmitSuccess | StepEditSubmitRefusal;

type InFlightAbortReason = "cancelled" | "superseded" | "timeout";

interface InFlightEditEntry {
  seq: number;
  clientRequestId: string;
  stepId: string;
  stepIndex: number;
  controller: AbortController;
  abortReason: InFlightAbortReason | null;
}

const DEFAULT_STEP_EDIT_TIMEOUT_MS = 15_000;
let nextSubmitSeq = 0;
const inFlightSessions = new Map<string, InFlightEditEntry>();

function notifyServerCancelStepEdit(sessionId: string, clientRequestId: string): void {
  if (typeof fetch !== "function" || !sessionId || !clientRequestId) return;
  try {
    void fetch("/api/simulation/steps/cancel", {
      method: "POST",
      credentials: "include",
      keepalive: true,
      headers: {
        "Content-Type": "application/json",
        [AXO_CLIENT_SESSION_HEADER]: getOrCreateAxoClientSessionToken(),
      },
      body: JSON.stringify({
        session_id: sessionId,
        client_request_id: clientRequestId,
      }),
    }).catch(() => undefined);
  } catch {
    // Best-effort cancellation notification; abort signal also fires synchronously
  }
}

export function cancelInFlightStepEdit(sessionId: string): boolean {
  const entry = inFlightSessions.get(sessionId);
  if (!entry) return false;
  entry.abortReason = "cancelled";
  notifyServerCancelStepEdit(sessionId, entry.clientRequestId);
  entry.controller.abort();
  inFlightSessions.delete(sessionId);
  return true;
}

function fnv1aHex(input: string): string {
  let h = 0x811c9dc5;
  for (let i = 0; i < input.length; i += 1) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0).toString(16).padStart(8, "0");
}

export function getOrCreateAxoClientSessionToken(): string {
  try {
    const existing = window.localStorage.getItem(CLIENT_TOKEN_STORAGE_KEY);
    if (existing && existing.trim().length >= 8) {
      return existing.trim();
    }
    const created =
      typeof window.crypto?.randomUUID === "function"
        ? `axo-cli-${window.crypto.randomUUID()}`
        : `axo-cli-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
    window.localStorage.setItem(CLIENT_TOKEN_STORAGE_KEY, created);
    return created;
  } catch {
    return "axo-cli-ephemeral";
  }
}

export function buildStepEditSessionId(problemKey: string, userScopeHint?: string | null): string {
  const cleanProblem = problemKey.trim() || "active-problem";
  const slug = cleanProblem
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 42) || "geom";
  const scopePart = userScopeHint?.trim() ? fnv1aHex(userScopeHint.trim()) : "anon";
  return `se-${scopePart}-${slug}-${fnv1aHex(cleanProblem)}`;
}

export function loadCachedStepEditState(sessionId: string): PersistedStepEditSnapshot | null {
  if (!sessionId) return null;
  try {
    const raw = window.localStorage.getItem(`${STEP_STATE_STORAGE_PREFIX}${sessionId}`);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PersistedStepEditSnapshot;
    if (!parsed || typeof parsed !== "object" || parsed.sessionId !== sessionId) {
      return null;
    }
    const cachedScene = isVerifiedRebuildScene(parsed.committedScene)
      ? markVerifiedStepEditedScene(parsed.committedScene)
      : null;
    return {
      sessionId,
      problemKey: typeof parsed.problemKey === "string" ? parsed.problemKey : "",
      versionNumber: typeof parsed.versionNumber === "number" ? parsed.versionNumber : undefined,
      committedScene: cachedScene,
      stepOverrides: cachedScene && parsed.stepOverrides && typeof parsed.stepOverrides === "object"
        ? parsed.stepOverrides
        : {},
      dependencySummary: parsed.dependencySummary ?? null,
      revisions: Array.isArray(parsed.revisions) ? parsed.revisions : [],
      feedbackItems: Array.isArray(parsed.feedbackItems) ? parsed.feedbackItems : [],
      updatedAt: typeof parsed.updatedAt === "number" ? parsed.updatedAt : Date.now(),
    };
  } catch {
    return null;
  }
}

export function saveCachedStepEditState(sessionId: string, snapshot: PersistedStepEditSnapshot): boolean {
  if (!sessionId) return false;
  try {
    const existing = loadCachedStepEditState(sessionId);
    const sameProblem =
      !existing
      || !existing.problemKey
      || !snapshot.problemKey
      || existing.problemKey === snapshot.problemKey;
    if (
      sameProblem
      && existing?.committedScene
      && existing.versionNumber !== undefined
      && snapshot.versionNumber !== undefined
      && snapshot.versionNumber < existing.versionNumber
    ) {
      return false;
    }
    window.localStorage.setItem(`${STEP_STATE_STORAGE_PREFIX}${sessionId}`, JSON.stringify(snapshot));
    return true;
  } catch {
    // Best-effort client persistence; server SQLite remains authoritative
    return false;
  }
}

export async function fetchStepEditSessionState(sessionId: string): Promise<PersistedStepEditSnapshot | null> {
  if (!sessionId) return null;
  try {
    const res = await fetch(`/api/simulation/sessions/${encodeURIComponent(sessionId)}/state`, {
      method: "GET",
      credentials: "include",
      headers: {
        [AXO_CLIENT_SESSION_HEADER]: getOrCreateAxoClientSessionToken(),
      },
    });
    if (!res.ok) return null;
    const data = await res.json();
    if (!data?.found) return null;
    if (data.dependency_summary && data.dependency_summary.cycle_detected !== false && Number(data.revision_count || 0) > 0) {
      return null;
    }
    const committedVer =
      typeof data.committed_version === "number"
        ? data.committed_version
        : (typeof data.revision_count === "number" ? data.revision_count : undefined);
    const remoteScene =
      (committedVer === undefined || committedVer > 0) && isVerifiedRebuildScene(data.committed_scene)
        ? markVerifiedStepEditedScene(data.committed_scene as Scene3D)
        : null;
    const snapshot: PersistedStepEditSnapshot = {
      sessionId,
      problemKey: typeof data.problem_key === "string" ? data.problem_key : "",
      versionNumber: committedVer,
      committedScene: remoteScene,
      stepOverrides: remoteScene ? ((data.step_overrides as Record<string, string>) ?? {}) : {},
      dependencySummary: (data.dependency_summary as StepEditDependencySummary) ?? null,
      revisions: Array.isArray(data.revisions) ? data.revisions : [],
      feedbackItems: Array.isArray(data.feedback_items) ? data.feedback_items : [],
      updatedAt: Date.now(),
    };
    const saved = saveCachedStepEditState(sessionId, snapshot);
    if (!saved) {
      return loadCachedStepEditState(sessionId) ?? snapshot;
    }
    return snapshot;
  } catch {
    return null;
  }
}

export async function submitConstructionStepEdit(params: {
  sessionId: string;
  problemKey: string;
  stepId: string;
  stepIndex: number;
  previousInstruction: string;
  editedInstruction: string;
  targetIds: string[];
  absorbedIds: string[];
  priorStepIds?: string[];
  scene3d: Scene3D;
  timeoutMs?: number;
  supersedeInFlight?: boolean;
}): Promise<StepEditSubmitResult> {
  const { sessionId } = params;
  const existingEntry = inFlightSessions.get(sessionId);
  if (existingEntry) {
    const sameTarget = existingEntry.stepId === params.stepId && existingEntry.stepIndex === params.stepIndex;
    if (sameTarget && !params.supersedeInFlight) {
      return {
        status: "duplicate_ignored",
        error_code: "EDIT_IN_PROGRESS",
        failed_stage: "ui_lock",
        learner_error: "Hệ thống đang kiểm tra và dựng lại bước vừa gửi, vui lòng chờ hoàn tất.",
        draft_preserved: true,
      };
    }
    existingEntry.abortReason = "superseded";
    notifyServerCancelStepEdit(sessionId, existingEntry.clientRequestId);
    existingEntry.controller.abort();
  }

  const controller = new AbortController();
  const seq = ++nextSubmitSeq;
  const clientRequestId =
    typeof window !== "undefined" && typeof window.crypto?.randomUUID === "function"
      ? `se-req-${window.crypto.randomUUID()}`
      : `se-req-${Date.now().toString(36)}-${seq}`;
  const entry: InFlightEditEntry = {
    seq,
    clientRequestId,
    stepId: params.stepId,
    stepIndex: params.stepIndex,
    controller,
    abortReason: null,
  };
  inFlightSessions.set(sessionId, entry);

  const timeoutMs =
    typeof params.timeoutMs === "number" && Number.isFinite(params.timeoutMs) && params.timeoutMs > 0
      ? params.timeoutMs
      : DEFAULT_STEP_EDIT_TIMEOUT_MS;
  const timeoutTimer = setTimeout(() => {
    if (entry.abortReason === null) {
      entry.abortReason = "timeout";
      controller.abort();
    }
  }, timeoutMs);

  try {
    const res = await fetch("/api/simulation/steps/edit", {
      method: "POST",
      credentials: "include",
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        [AXO_CLIENT_SESSION_HEADER]: getOrCreateAxoClientSessionToken(),
      },
      body: JSON.stringify({
        session_id: params.sessionId,
        problem_key: params.problemKey,
        step_id: params.stepId,
        step_index: params.stepIndex,
        previous_instruction: params.previousInstruction,
        edited_instruction: params.editedInstruction,
        target_ids: params.targetIds,
        absorbed_ids: params.absorbedIds,
        prior_step_ids: params.priorStepIds ?? [],
        scene3d: params.scene3d,
        client_request_id: clientRequestId,
        client_seq: seq,
      }),
    });

    if (entry.abortReason === "cancelled") {
      return {
        status: "rolled_back",
        error_code: "EDIT_CANCELLED",
        failed_stage: "cancelled",
        learner_error: "Đã hủy lượt chỉnh sửa đang chạy.",
        draft_preserved: true,
      };
    }
    const isCurrentSeq = inFlightSessions.get(sessionId)?.seq === seq && entry.abortReason !== "superseded";
    if (!isCurrentSeq) {
      return {
        status: "rolled_back",
        error_code: "EDIT_SUPERSEDED",
        failed_stage: "superseded",
        learner_error: "Yêu cầu cũ đã được thay thế bởi lượt chỉnh sửa mới hơn.",
        draft_preserved: true,
      };
    }

    const data = await res.json().catch(() => null);
    if (res.ok && data?.status === "committed" && data?.scene3d) {
      if (!isVerifiedStepEditCommitResponse(data)) {
        return {
          status: "rolled_back",
          error_code: "UNVERIFIED_REBUILD_REJECTED",
          failed_stage: "client_verification",
          learner_error:
            "Mô hình dựng lại chưa vượt qua kiểm chứng hình học nên trạng thái hợp lệ trước đó được giữ nguyên.",
          draft_preserved: true,
        };
      }
      const success = data as StepEditSubmitSuccess;
      markVerifiedStepEditedScene(success.scene3d);
      const effectiveVer =
        typeof success.committed_version === "number" ? success.committed_version : success.version_number;
      const existingCache = loadCachedStepEditState(sessionId);
      saveCachedStepEditState(sessionId, {
        sessionId,
        problemKey: params.problemKey,
        versionNumber: effectiveVer,
        committedScene: success.scene3d,
        stepOverrides: success.step_overrides ?? {},
        dependencySummary: success.dependency_summary ?? null,
        revisions: existingCache?.revisions ?? [],
        feedbackItems: existingCache?.feedbackItems ?? [],
        updatedAt: Date.now(),
      });
      return success;
    }

    return {
      status: "rolled_back",
      error_code: String(data?.error_code || `HTTP_${res.status}`),
      failed_stage: String(data?.failed_stage || "server"),
      learner_error: String(
        data?.learner_error ||
          data?.detail ||
          "Không thể dựng hình với nội dung bước vừa chỉnh. Bước dựng cũ vẫn được giữ nguyên.",
      ),
      draft_preserved: true,
    };
  } catch {
    if (entry.abortReason === "cancelled") {
      return {
        status: "rolled_back",
        error_code: "EDIT_CANCELLED",
        failed_stage: "cancelled",
        learner_error: "Đã hủy lượt chỉnh sửa đang chạy.",
        draft_preserved: true,
      };
    }
    if (entry.abortReason === "superseded" || inFlightSessions.get(sessionId)?.seq !== seq) {
      return {
        status: "rolled_back",
        error_code: "EDIT_SUPERSEDED",
        failed_stage: "superseded",
        learner_error: "Yêu cầu cũ đã được thay thế bởi lượt chỉnh sửa mới hơn.",
        draft_preserved: true,
      };
    }
    if (entry.abortReason === "timeout") {
      return {
        status: "network_error",
        error_code: "REQUEST_TIMEOUT",
        failed_stage: "network_timeout",
        learner_error: "Máy chủ dựng hình phản hồi quá thời gian chờ. Trạng thái hợp lệ trước đó vẫn được giữ nguyên.",
        draft_preserved: true,
      };
    }
    // Reconcile once with /state (bounded timeout) in case the server committed before a transport socket drop
    const recoverCtrl = new AbortController();
    const recoverTimer = setTimeout(() => recoverCtrl.abort(), 1500);
    try {
      const stateRes = await fetch(`/api/simulation/sessions/${encodeURIComponent(sessionId)}/state`, {
        method: "GET",
        credentials: "include",
        signal: recoverCtrl.signal,
        headers: {
          [AXO_CLIENT_SESSION_HEADER]: getOrCreateAxoClientSessionToken(),
        },
      });
      if (stateRes.ok) {
        const sData = await stateRes.json().catch(() => null);
        if (
          sData?.found
          && sData.last_committed_request_id === clientRequestId
          && isVerifiedRebuildScene(sData.committed_scene)
        ) {
          const recScene = markVerifiedStepEditedScene(sData.committed_scene as Scene3D);
          const recVer =
            typeof sData.committed_version === "number" && sData.committed_version > 0
              ? sData.committed_version
              : Number(sData.revision_count || 1);
          const recResult: StepEditSubmitSuccess = {
            status: "committed",
            mode: "POST_COMMIT_RECOVERED",
            equivalence_info: null,
            session_id: sessionId,
            revision_id: "recovered-from-state",
            feedback_id: "recovered-from-state",
            feedback_status: "GEOMETRY_VERIFIED",
            dataset_eligibility: "ELIGIBLE",
            version_number: recVer,
            committed_version: recVer,
            primary_target_id: params.stepId,
            scene3d: recScene,
            step_overrides: (sData.step_overrides as Record<string, string>) ?? {},
            dependency_summary: (sData.dependency_summary as StepEditDependencySummary) ?? {
              edited_target_ids: [params.stepId],
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
              checks_passed: ["post_commit_state_reconciliation"],
              continuity: { passed: true, issues: [] },
            },
            stage_timings_ms: { total_ms: 0 },
            llm_calls: 0,
            quota_charged: false,
          };
          saveCachedStepEditState(sessionId, {
            sessionId,
            problemKey: params.problemKey,
            versionNumber: recVer,
            committedScene: recScene,
            stepOverrides: recResult.step_overrides,
            dependencySummary: recResult.dependency_summary,
            revisions: Array.isArray(sData.revisions) ? sData.revisions : [],
            feedbackItems: Array.isArray(sData.feedback_items) ? sData.feedback_items : [],
            updatedAt: Date.now(),
          });
          return recResult;
        }
      }
    } catch {
      // Fall back to explicit network_error keeping draft intact
    } finally {
      clearTimeout(recoverTimer);
    }
    return {
      status: "network_error",
      error_code: "NETWORK_UNAVAILABLE",
      failed_stage: "network",
      learner_error: "Không thể kết nối tới máy chủ dựng hình cục bộ. Nội dung bạn vừa gõ vẫn được giữ lại.",
      draft_preserved: true,
    };
  } finally {
    clearTimeout(timeoutTimer);
    if (inFlightSessions.get(sessionId)?.seq === seq) {
      inFlightSessions.delete(sessionId);
    }
  }
}

export async function approveVerifiedStepFeedback(
  feedbackId: string,
  approved: boolean,
  reviewerNote?: string,
): Promise<boolean> {
  if (!feedbackId) return false;
  try {
    const res = await fetch(`/api/simulation/feedback/${encodeURIComponent(feedbackId)}/approve`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        [AXO_CLIENT_SESSION_HEADER]: getOrCreateAxoClientSessionToken(),
      },
      body: JSON.stringify({
        approved,
        promote_to_training: approved,
        reviewer_note: reviewerNote ?? null,
      }),
    });
    return res.ok;
  } catch {
    return false;
  }
}
