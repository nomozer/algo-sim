import type { Scene3D } from "../simulations/domains/geometry/scene3d-model";

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
  committedScene: Scene3D | null;
  stepOverrides: Record<string, string>;
  dependencySummary?: StepEditDependencySummary | null;
  revisions: StepEditRevisionItem[];
  feedbackItems: StepEditFeedbackItem[];
  updatedAt: number;
}

export interface StepEditSubmitSuccess {
  status: "committed";
  mode: string;
  session_id: string;
  revision_id: string;
  feedback_id: string;
  feedback_status: string;
  dataset_eligibility: string;
  version_number: number;
  primary_target_id: string;
  scene3d: Scene3D;
  step_overrides: Record<string, string>;
  dependency_summary: StepEditDependencySummary;
  stage_timings_ms: Record<string, number>;
  llm_calls: number;
  quota_charged: boolean;
}

export interface StepEditSubmitRefusal {
  status: "rolled_back" | "network_error" | "duplicate_ignored";
  error_code: string;
  failed_stage: string;
  learner_error: string;
  draft_preserved: boolean;
}

export type StepEditSubmitResult = StepEditSubmitSuccess | StepEditSubmitRefusal;

const inFlightSessions = new Set<string>();

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
    return {
      sessionId,
      problemKey: typeof parsed.problemKey === "string" ? parsed.problemKey : "",
      committedScene: parsed.committedScene ?? null,
      stepOverrides: parsed.stepOverrides && typeof parsed.stepOverrides === "object" ? parsed.stepOverrides : {},
      dependencySummary: parsed.dependencySummary ?? null,
      revisions: Array.isArray(parsed.revisions) ? parsed.revisions : [],
      feedbackItems: Array.isArray(parsed.feedbackItems) ? parsed.feedbackItems : [],
      updatedAt: typeof parsed.updatedAt === "number" ? parsed.updatedAt : Date.now(),
    };
  } catch {
    return null;
  }
}

export function saveCachedStepEditState(sessionId: string, snapshot: PersistedStepEditSnapshot): void {
  if (!sessionId) return;
  try {
    window.localStorage.setItem(`${STEP_STATE_STORAGE_PREFIX}${sessionId}`, JSON.stringify(snapshot));
  } catch {
    // Best-effort client persistence; server SQLite remains authoritative
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
    const snapshot: PersistedStepEditSnapshot = {
      sessionId,
      problemKey: typeof data.problem_key === "string" ? data.problem_key : "",
      committedScene: (data.committed_scene as Scene3D) ?? null,
      stepOverrides: (data.step_overrides as Record<string, string>) ?? {},
      dependencySummary: (data.dependency_summary as StepEditDependencySummary) ?? null,
      revisions: Array.isArray(data.revisions) ? data.revisions : [],
      feedbackItems: Array.isArray(data.feedback_items) ? data.feedback_items : [],
      updatedAt: Date.now(),
    };
    saveCachedStepEditState(sessionId, snapshot);
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
  scene3d: Scene3D;
}): Promise<StepEditSubmitResult> {
  const { sessionId } = params;
  if (inFlightSessions.has(sessionId)) {
    return {
      status: "duplicate_ignored",
      error_code: "EDIT_IN_PROGRESS",
      failed_stage: "ui_lock",
      learner_error: "Hệ thống đang kiểm tra và dựng lại bước vừa gửi, vui lòng chờ hoàn tất.",
      draft_preserved: true,
    };
  }

  inFlightSessions.add(sessionId);
  try {
    const res = await fetch("/api/simulation/steps/edit", {
      method: "POST",
      credentials: "include",
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
        scene3d: params.scene3d,
      }),
    });

    const data = await res.json().catch(() => null);
    if (res.ok && data?.status === "committed" && data?.scene3d) {
      const success = data as StepEditSubmitSuccess;
      const existingCache = loadCachedStepEditState(sessionId);
      saveCachedStepEditState(sessionId, {
        sessionId,
        problemKey: params.problemKey,
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
    return {
      status: "network_error",
      error_code: "NETWORK_UNAVAILABLE",
      failed_stage: "network",
      learner_error: "Không thể kết nối tới máy chủ dựng hình cục bộ. Nội dung bạn vừa gõ vẫn được giữ lại.",
      draft_preserved: true,
    };
  } finally {
    inFlightSessions.delete(sessionId);
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
