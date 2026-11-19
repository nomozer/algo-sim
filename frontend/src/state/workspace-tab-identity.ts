import { GEOMETRY_SAMPLES } from "../data/geometry-samples";
import {
  resolveGeometrySampleId,
  resolveSampleByRouteToken,
} from "../data/offline-catalog";
import type { SimulationEnvelope } from "../simulations/types";
import { historyIdOf, normalizeStatement } from "./history";

export const LIBRARY_TAB_ID = "tab-library";
export const LIBRARY_RESOURCE_KEY = "library";
export const LIBRARY_TAB_TITLE = "Thư viện mô phỏng";

export const DRAFT_TAB_ID = "tab-draft-new";
export const DRAFT_RESOURCE_KEY = "draft:new";

export interface WorkspaceTabIdentityShape {
  readonly id: string;
  readonly kind: "simulation" | "draft";
  readonly title: string;
  readonly sampleId: string | null;
  readonly historyId: string | null;
  readonly active: {
    readonly envelope: SimulationEnvelope;
    readonly problemStatement?: string | null;
  } | null;
  readonly draftText?: string;
}

export interface SimulationResourceCandidate {
  readonly tabId?: string | null;
  readonly sampleId?: string | null;
  readonly historyId?: string | null;
  readonly title?: string | null;
  readonly problemStatement?: string | null;
  readonly originalInput?: string | null;
  readonly envelope?: SimulationEnvelope | null;
}

export type ProjectedTabKind = "library" | "simulation" | "draft";

export interface ProjectedWorkspaceTab<TTab extends WorkspaceTabIdentityShape = WorkspaceTabIdentityShape> {
  readonly id: string;
  readonly kind: ProjectedTabKind;
  readonly resourceKey: string;
  readonly title: string;
  readonly tab?: TTab;
}

const sampleNormalizedStatementMap = new Map<string, string>();
for (const sample of GEOMETRY_SAMPLES) {
  const norm = normalizeStatement(sample.problemText);
  if (norm && !sampleNormalizedStatementMap.has(norm)) {
    sampleNormalizedStatementMap.set(norm, sample.id);
  }
}

function extractSampleIdFromTabId(tabId: string | null | undefined): string | null {
  if (!tabId) return null;
  if (tabId.startsWith("tab-sample-")) {
    const raw = tabId.slice("tab-sample-".length).trim();
    return raw || null;
  }
  return null;
}

function extractHistoryIdFromTabId(tabId: string | null | undefined): string | null {
  if (!tabId) return null;
  if (tabId.startsWith("tab-hist-")) {
    const raw = tabId.slice("tab-hist-".length).trim();
    return raw || null;
  }
  return null;
}

function resolveExplicitCatalogSampleId(
  sampleOrToken: string | null | undefined,
  envelope?: SimulationEnvelope | null,
  title?: string | null,
): string | null {
  if (!sampleOrToken) return null;
  const trimmed = sampleOrToken.trim();
  if (!trimmed) return null;
  const resolved = resolveGeometrySampleId({ id: trimmed, title, envelope });
  return resolved ?? trimmed;
}

/**
 * Suy ra khoá tài nguyên chính tắc cho một bài toán / tab mô phỏng:
 * - `"library"` cho tab Thư viện (`tab-library`).
 * - `"draft:new"` cho tab Bài toán mới (`tab-draft-new`).
 * - `"problem:<canonicalSampleId>"` khi khớp bài mẫu thư viện (trừ lần gửi đề riêng của người học có đề khác mẫu).
 * - `historyId` (hoặc fallback đề chuẩn hoá / envelope hash) cho bài nộp của người học.
 */
export function getSimulationResourceKey(candidate: SimulationResourceCandidate): string {
  const tabId = candidate.tabId?.trim() || null;
  if (tabId === LIBRARY_TAB_ID) return LIBRARY_RESOURCE_KEY;
  if (tabId === DRAFT_TAB_ID) return DRAFT_RESOURCE_KEY;

  const explicitSampleId =
    candidate.sampleId?.trim() || extractSampleIdFromTabId(tabId);
  if (explicitSampleId) {
    return `problem:${resolveExplicitCatalogSampleId(explicitSampleId, candidate.envelope, candidate.title)}`;
  }

  const historyId =
    candidate.historyId?.trim() || extractHistoryIdFromTabId(tabId);

  if (historyId) {
    const directSampleByToken =
      resolveSampleByRouteToken(historyId)?.id ??
      GEOMETRY_SAMPLES.find((s) => s.id === historyId)?.id ??
      null;
    if (directSampleByToken) {
      return `problem:${directSampleByToken}`;
    }
  }

  const explicitOriginalNorm = normalizeStatement(candidate.originalInput);
  const statementNorm =
    explicitOriginalNorm ??
    normalizeStatement(
      candidate.problemStatement ?? candidate.envelope?.problem_statement ?? null,
    );

  // Lần gửi của người học (đề tự nhập khác nguyên văn bài mẫu) phải giữ định danh riêng theo lần gửi,
  // không gộp nhầm sang bài mẫu thư viện dù cùng `simulation_id + config`.
  const catalogIdByEnvOrId = resolveGeometrySampleId({
    id: historyId,
    title: candidate.title,
    envelope: candidate.envelope,
  });

  if (catalogIdByEnvOrId) {
    const matchedSample = GEOMETRY_SAMPLES.find((s) => s.id === catalogIdByEnvOrId);
    const sampleStatementNorm = matchedSample
      ? normalizeStatement(matchedSample.problemText)
      : null;
    const hasCustomLearnerStatement =
      Boolean(explicitOriginalNorm && sampleStatementNorm && explicitOriginalNorm !== sampleStatementNorm) ||
      Boolean(statementNorm && sampleStatementNorm && statementNorm !== sampleStatementNorm);
    const isSubmissionKey = Boolean(historyId?.startsWith("s") || historyId?.startsWith("a"));
    if (!hasCustomLearnerStatement && !isSubmissionKey) {
      return `problem:${catalogIdByEnvOrId}`;
    }
  }

  if (!explicitOriginalNorm && statementNorm && (!historyId || !historyId.startsWith("s"))) {
    const matchedByStatement = sampleNormalizedStatementMap.get(statementNorm);
    if (matchedByStatement) {
      return `problem:${matchedByStatement}`;
    }
  }

  if (historyId) {
    return historyId;
  }

  if (candidate.envelope) {
    return historyIdOf(candidate.envelope);
  }

  if (statementNorm) {
    return `stmt:${statementNorm}`;
  }

  return tabId ?? "unknown";
}

export function getWorkspaceTabResourceKey(tab: WorkspaceTabIdentityShape): string {
  if (tab.kind === "draft" || tab.id === DRAFT_TAB_ID) {
    return DRAFT_RESOURCE_KEY;
  }
  return getSimulationResourceKey({
    tabId: tab.id,
    sampleId: tab.sampleId,
    historyId: tab.historyId,
    title: tab.title,
    problemStatement: tab.active?.problemStatement ?? null,
    envelope: tab.active?.envelope ?? null,
  });
}

function hasStatementOrKindConflict(
  tab: WorkspaceTabIdentityShape,
  tabKey: string,
  candidate: SimulationResourceCandidate,
  targetKey: string,
): boolean {
  if (tabKey.startsWith("problem:") && targetKey.startsWith("problem:")) {
    return tabKey !== targetKey;
  }
  if (!tabKey.startsWith("problem:") && targetKey.startsWith("problem:")) {
    return true;
  }
  const candidateStatement = normalizeStatement(
    candidate.originalInput ??
      candidate.problemStatement ??
      candidate.envelope?.problem_statement ??
      null,
  );
  if (tabKey.startsWith("problem:") && candidateStatement) {
    const sampleId = tabKey.slice("problem:".length);
    const sample = GEOMETRY_SAMPLES.find((s) => s.id === sampleId);
    const sampleNorm = sample ? normalizeStatement(sample.problemText) : null;
    if (sampleNorm && candidateStatement !== sampleNorm) {
      return true;
    }
  }
  const tabStatement = normalizeStatement(
    tab.active?.problemStatement ?? tab.active?.envelope?.problem_statement ?? null,
  );
  if (candidateStatement && tabStatement && candidateStatement !== tabStatement) {
    return true;
  }
  return false;
}

export function findMatchingOpenSimulationTab<T extends WorkspaceTabIdentityShape>(
  tabs: readonly T[],
  candidate: SimulationResourceCandidate,
): T | undefined {
  const targetKey = getSimulationResourceKey(candidate);
  const candidateTabId = candidate.tabId?.trim() || null;
  if (candidateTabId) {
    const byTabId = tabs.find((t) => {
      if (t.kind !== "simulation" || t.id !== candidateTabId) return false;
      const tabKey = getWorkspaceTabResourceKey(t);
      return !hasStatementOrKindConflict(t, tabKey, candidate, targetKey);
    });
    if (byTabId) return byTabId;
  }

  const candidateSampleId =
    candidate.sampleId?.trim() || extractSampleIdFromTabId(candidateTabId);
  if (candidateSampleId) {
    const canonicalSample = resolveExplicitCatalogSampleId(
      candidateSampleId,
      candidate.envelope,
      candidate.title,
    );
    const expectedSampleKey = `problem:${canonicalSample ?? candidateSampleId}`;
    const bySample = tabs.find((t) => {
      if (t.kind !== "simulation") return false;
      if (getWorkspaceTabResourceKey(t) === expectedSampleKey) return true;
      if (t.sampleId && t.sampleId === candidateSampleId) return true;
      const tabSample = t.sampleId
        ? resolveExplicitCatalogSampleId(t.sampleId, t.active?.envelope, t.title)
        : null;
      return Boolean(canonicalSample && tabSample === canonicalSample);
    });
    if (bySample) return bySample;
  }

  const candidateHistoryId =
    candidate.historyId?.trim() || extractHistoryIdFromTabId(candidateTabId);
  if (candidateHistoryId) {
    const byHistory = tabs.find((t) => {
      if (t.kind !== "simulation" || t.historyId !== candidateHistoryId) return false;
      const tabKey = getWorkspaceTabResourceKey(t);
      return !hasStatementOrKindConflict(t, tabKey, candidate, targetKey);
    });
    if (byHistory) return byHistory;
  }

  if (!targetKey || targetKey === "unknown") return undefined;

  return tabs.find(
    (t) => t.kind === "simulation" && getWorkspaceTabResourceKey(t) === targetKey,
  );
}

export function buildProjectedWorkspaceTabs<T extends WorkspaceTabIdentityShape>(
  workspaceTabs: readonly T[],
  libraryTabOpen: boolean,
  fallbackTitle = "Mô phỏng 3D",
): ProjectedWorkspaceTab<T>[] {
  const projected: ProjectedWorkspaceTab<T>[] = [];
  const seenKeys = new Set<string>();

  if (libraryTabOpen) {
    seenKeys.add(LIBRARY_RESOURCE_KEY);
    projected.push({
      id: LIBRARY_TAB_ID,
      kind: "library",
      resourceKey: LIBRARY_RESOURCE_KEY,
      title: LIBRARY_TAB_TITLE,
    });
  }

  for (const tab of workspaceTabs) {
    const resourceKey = getWorkspaceTabResourceKey(tab);
    if (seenKeys.has(resourceKey)) continue;
    seenKeys.add(resourceKey);
    const title =
      tab.kind === "draft"
        ? tab.title.trim() || "Bài toán mới"
        : tab.title.trim() || fallbackTitle.trim() || "Mô phỏng 3D";
    projected.push({
      id: tab.id,
      kind: tab.kind,
      resourceKey,
      title,
      tab,
    });
  }

  return projected;
}
