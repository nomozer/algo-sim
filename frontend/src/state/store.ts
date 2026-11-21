import { create } from "zustand";
import {
  canonicalPathForView,
  resolveLocationRoute,
  type AxoErrorKind,
} from "../components/AxoErrorExperience";
import {
  resolveGeometrySolidFamily,
  type GeometrySolidFamily,
} from "../components/family-icons";
import type { AnalysisUnsupported } from "../core/types";
import {
  offlineCatalog,
  publicCatalog,
  recoverCatalogScene3D,
  resolveGeometrySampleId,
} from "../data/offline-catalog";
import { GEOMETRY_SAMPLES } from "../data/geometry-samples";
import type { AxoClientError, ClientFailureContract } from "../llm/client";
import { getSimulation } from "../simulations/registry";
import { useAuthStore } from "./auth";
import {
  clearServerHistory,
  deleteServerHistoryItem,
  fetchServerHistory,
  historyIdOf,
  historyStore,
  INTERRUPTED_BY_RELOAD_REASON,
  normalizeStatement,
  PROBLEM_DRAFT_STORAGE_KEY,
  PROBLEM_PROCESSING_RECORDS_KEY,
  sceneDigestOf,
  stripStatusPrefixesFromTitle,
  submissionIdOf,
  touchServerHistory,
  upsertServerHistory,
  type HistoryItem,
  type PersistedProblemProcessingRecord,
  type ProblemProcessingFailureKind,
} from "./history";
import {
  DRAFT_RESOURCE_KEY,
  DRAFT_TAB_ID,
  findMatchingOpenSimulationTab,
  getSimulationResourceKey,
  getWorkspaceTabResourceKey,
  LIBRARY_RESOURCE_KEY,
  LIBRARY_TAB_ID,
} from "./workspace-tab-identity";
import type {
  SimAction,
  ConfigResult,
  SimulationEnvelope,
  TimelineCapability,
  VisualMode,
} from "../simulations/types";

export {
  INTERRUPTED_BY_RELOAD_REASON,
  PROBLEM_DRAFT_STORAGE_KEY,
  PROBLEM_PROCESSING_RECORDS_KEY,
  resolveGeometrySolidFamily,
  stripStatusPrefixesFromTitle,
  type GeometrySolidFamily,
  type ProblemProcessingFailureKind,
};

/**
 * Store lõi — MÙ DOMAIN (ràng buộc M2 #7): chỉ giữ moduleId + envelope +
 * config + state dạng opaque. Mọi biến đổi state đi qua module.apply /
 * module.timeline lấy từ registry. Store không import Trace, không biết
 * mảng/nhánh/mã giả là gì.
 */

export interface ActiveSimulation {
  moduleId: string;
  envelope: SimulationEnvelope;
  /** Config đã qua module.validateConfig — bất biến. */
  config: unknown;
  /** Engine state — module sở hữu, store chỉ cầm hộ. */
  state: unknown;
  /**
   * Đề gốc đi kèm CHÍNH lần mở này (đề học sinh gửi khi phân tích, hoặc đề đã lưu khi mở lại từ Lịch sử).
   * Gắn vào `active` chứ không đọc từ bản ghi lịch sử: một bản ghi (khoá `simulation_id + config`) có thể
   * dùng chung với bài mẫu, nên mở bài mẫu từ Thư viện không được hiện đề của một lần gửi khác.
   */
  problemStatement?: string | null;
}


/**
 * M18 — MẶT TRÌNH BÀY. Bốn mặt cũ giữ nguyên; năm mặt mới là tầng lớp học.
 *
 * Vì sao MỞ RỘNG trường `view` chứ không thêm router: repo chưa từng có router,
 * và điều hướng đã có đúng một chủ sở hữu là trường này. Thêm `react-router`
 * để có năm màn nữa là dựng hệ điều hướng THỨ HAI cạnh hệ đang chạy — đúng
 * loại "hai nơi làm một việc" mà M9-UX7 đã gỡ một lần.
 */
export type AppView =
  | "home" | "landing" | "workspace" | "library" | "history" | "not_found"
  | "account"
  | "login" | "register" | "forgot" | "reset" | "admin";

export interface RouteFailureState {
  readonly kind: AxoErrorKind;
  readonly requestedPath?: string | null;
}

export interface WorkspaceTabItem {
  readonly id: string;
  readonly problemId: string | null;
  readonly sessionId: string | null;
  readonly kind: "simulation" | "draft";
  readonly title: string;
  readonly active: ActiveSimulation | null;
  readonly sampleId: string | null;
  readonly historyId: string | null;
  readonly draftText?: string;
}

export interface WorkspaceNavEntry {
  readonly view: AppView;
  readonly tabId: string | null;
}

const SAFE_ESCAPE_VIEWS = new Set<AppView>([
  "home",
  "landing",
  "library",
  "history",
  "account",
]);

function pushSafeRoute(stack: readonly AppView[], next: AppView): AppView[] {
  if (!SAFE_ESCAPE_VIEWS.has(next)) return [...stack];
  if (stack[stack.length - 1] === next) return [...stack];
  const updated = [...stack, next];
  return updated.length > 24 ? updated.slice(updated.length - 24) : updated;
}

function ensureSafeNavRoot(
  stack: readonly WorkspaceNavEntry[],
  fallbackView: AppView = "home",
): WorkspaceNavEntry[] {
  const safeRoot: AppView = SAFE_ESCAPE_VIEWS.has(fallbackView) ? fallbackView : "home";
  if (stack.length === 0) {
    return [{ view: safeRoot, tabId: null }];
  }
  if (!SAFE_ESCAPE_VIEWS.has(stack[0].view)) {
    return [{ view: safeRoot, tabId: null }, ...stack];
  }
  return [...stack];
}

function pushWorkspaceNav(
  stack: readonly WorkspaceNavEntry[],
  index: number,
  entry: WorkspaceNavEntry,
  fallbackRoot: AppView = "home",
): { stack: WorkspaceNavEntry[]; index: number } {
  const safeIdx = stack.length > 0 ? Math.max(0, Math.min(index, stack.length - 1)) : 0;
  const baseRaw = stack.length > 0 ? stack.slice(0, safeIdx + 1) : [];
  const base = ensureSafeNavRoot(baseRaw, fallbackRoot);
  const top = base[base.length - 1];
  if (top && top.view === entry.view && top.tabId === entry.tabId) {
    return { stack: base, index: base.length - 1 };
  }
  const updated = [...base, entry];
  const capped =
    updated.length > 32
      ? ensureSafeNavRoot(updated.slice(updated.length - 31), fallbackRoot)
      : updated;
  return { stack: capped, index: capped.length - 1 };
}

function pruneTabFromNavStack(
  stack: readonly WorkspaceNavEntry[],
  index: number,
  closedTabId: string,
  fallbackRoot: AppView = "home",
): { stack: WorkspaceNavEntry[]; index: number } {
  const safeIdx = stack.length > 0 ? Math.max(0, Math.min(index, stack.length - 1)) : 0;
  const filtered: WorkspaceNavEntry[] = [];
  let newIndex = 0;
  for (let i = 0; i < stack.length; i += 1) {
    const item = stack[i];
    if (item.tabId === closedTabId) {
      if (i <= safeIdx && filtered.length > 0) {
        newIndex = filtered.length - 1;
      }
      continue;
    }
    const prev = filtered[filtered.length - 1];
    if (prev && prev.view === item.view && prev.tabId === item.tabId) {
      if (i <= safeIdx) {
        newIndex = filtered.length - 1;
      }
      continue;
    }
    filtered.push(item);
    if (i <= safeIdx) {
      newIndex = filtered.length - 1;
    }
  }
  if (filtered.length === 0 || !SAFE_ESCAPE_VIEWS.has(filtered[0].view)) {
    const safeRoot: AppView = SAFE_ESCAPE_VIEWS.has(fallbackRoot) ? fallbackRoot : "home";
    filtered.unshift({ view: safeRoot, tabId: null });
    newIndex = Math.min(filtered.length - 1, newIndex + 1);
  }
  return {
    stack: filtered,
    index: Math.max(0, Math.min(newIndex, filtered.length - 1)),
  };
}

function syncCurrentTabInList(
  tabs: readonly WorkspaceTabItem[],
  activeTabId: string | null,
  active: ActiveSimulation | null,
  activeSampleId: string | null,
  activeHistoryId: string | null,
  problemText = "",
): WorkspaceTabItem[] {
  if (tabs.length === 0) {
    if (!active) return [];
    const fallbackId = activeSampleId
      ? `tab-sample-${activeSampleId}`
      : activeHistoryId
        ? `tab-hist-${activeHistoryId}`
        : "tab-sim-0";
    return [
      {
        id: fallbackId,
        problemId: activeSampleId ?? activeHistoryId ?? active.envelope.simulation_id,
        sessionId: activeHistoryId ?? activeSampleId ?? "session-0",
        kind: "simulation",
        title: active.envelope.title?.trim() || "Mô phỏng 3D",
        active,
        sampleId: activeSampleId,
        historyId: activeHistoryId,
      },
    ];
  }
  return tabs.map((t) => {
    if (t.id === activeTabId && t.kind === "simulation" && active) {
      return {
        ...t,
        active,
        sampleId: activeSampleId ?? t.sampleId,
        historyId: activeHistoryId ?? t.historyId,
      };
    }
    if (t.id === activeTabId && t.kind === "draft") {
      return {
        ...t,
        draftText: problemText,
      };
    }
    return t;
  });
}

export type LeftRailProblemFilter = "all" | "ready" | "needs_attention" | "in_progress";

export type ProblemProcessingStatus =
  | "ready"
  | "needs_attention"
  | "in_progress"
  | "draft"
  | "unknown";

export interface ProblemProcessingRecord {
  readonly canonicalId: string;
  readonly title: string;
  readonly problemStatement: string;
  readonly status: "in_progress" | "needs_attention";
  readonly reasonCode?: string | null;
  readonly reasonMessage?: string | null;
  readonly interruptedByReload?: boolean;
  readonly failureKind?: ProblemProcessingFailureKind | null;
  readonly unsupported?: AnalysisUnsupported | null;
  readonly clientFailure?: ClientFailureContract | null;
  readonly analysisError?: string | null;
  readonly createdAt: number;
  readonly updatedAt: number;
}

export interface UnifiedSidebarProblemItem {
  /** Định danh duy nhất ổn định (canonicalId: historyId / "tab-draft-new" / attemptId / tab.id). */
  readonly canonicalId: string;
  readonly kind: "simulation" | "draft";
  readonly title: string;
  readonly problemStatement: string;
  readonly geometryFamily: GeometrySolidFamily;
  readonly isOpenInTab: boolean;
  readonly isCurrentActiveTab: boolean;
  readonly isInHistory: boolean;
  readonly openTab: WorkspaceTabItem | null;
  readonly historyItem: HistoryItem | null;
  readonly processingRecord?: ProblemProcessingRecord | null;
  readonly processingStatus: ProblemProcessingStatus;
  readonly processingReason?: string | null;
  readonly pinned: boolean;
  readonly pinnedAt: number | null;
  readonly lastAccessMs: number;
}

export function resolveWorkspaceTabGeometryFamily(
  tab: WorkspaceTabItem | null | undefined,
): GeometrySolidFamily {
  if (!tab || tab.kind === "draft") {
    return resolveGeometrySolidFamily({
      problemStatement: tab?.draftText ?? null,
      title: tab?.title ?? null,
    });
  }
  const env = tab.active?.envelope ?? null;
  const sampleId =
    tab.sampleId ??
    resolveGeometrySampleId({
      id: tab.historyId ?? tab.problemId ?? tab.id,
      envelope: env,
    });
  return resolveGeometrySolidFamily({
    envelope: env,
    sampleId,
    problemStatement: tab.active?.problemStatement ?? env?.problem_statement ?? null,
    title: env?.title ?? tab.title ?? null,
  });
}

export function recoverPersistedProblemProcessingRecords(): Record<
  string,
  ProblemProcessingRecord
> {
  const raw = historyStore.readProcessingRecords({ recoverReloadInterrupted: true });
  const out: Record<string, ProblemProcessingRecord> = {};
  for (const [k, rec] of Object.entries(raw)) {
    const isReloadInterrupted =
      rec.status === "needs_attention" &&
      (rec.interruptedByReload === true ||
        rec.reasonCode === "INTERRUPTED_BY_RELOAD" ||
        rec.failureKind === "CONNECTION_INTERRUPTED");
    const failureKind: ProblemProcessingFailureKind | null =
      rec.status === "in_progress"
        ? null
        : rec.failureKind === "CONNECTION_INTERRUPTED" || isReloadInterrupted
          ? "CONNECTION_INTERRUPTED"
          : "PROBLEM_ERROR";
    out[k] = {
      canonicalId: rec.canonicalId,
      title: stripStatusPrefixesFromTitle(rec.title) || "Bài toán cần chú ý",
      problemStatement: rec.problemStatement,
      status: rec.status,
      reasonCode: rec.reasonCode ?? null,
      reasonMessage: rec.reasonMessage ?? null,
      interruptedByReload: isReloadInterrupted,
      failureKind,
      unsupported: (rec.unsupported as AnalysisUnsupported | null | undefined) ?? null,
      clientFailure: (rec.clientFailure as ClientFailureContract | null | undefined) ?? null,
      analysisError: rec.analysisError ?? null,
      createdAt: rec.createdAt,
      updatedAt: rec.updatedAt,
    };
  }
  return out;
}

function persistProblemProcessingRecords(
  records: Readonly<Record<string, ProblemProcessingRecord>>,
): void {
  historyStore.writeProcessingRecords(
    records as Readonly<Record<string, PersistedProblemProcessingRecord>>,
  );
}

export interface LibraryUiState {
  readonly search: string;
  readonly category: string;
  readonly scrollTop: number;
}

const DEFAULT_LIBRARY_UI_STATE: LibraryUiState = {
  search: "",
  category: "all",
  scrollTop: 0,
};

export const WORKSPACE_SESSION_STORAGE_KEY = "algosim.workspace_tabs_session.v1";

interface PersistedWorkspaceTabEntry {
  readonly id: string;
  readonly kind: "simulation" | "draft";
  readonly sampleId: string | null;
  readonly historyId: string | null;
  readonly title: string;
  readonly draftText?: string;
}

interface PersistedWorkspaceSessionSnapshot {
  readonly version: 1;
  readonly libraryTabOpen: boolean;
  readonly libraryUiState: LibraryUiState;
  readonly activeTabId: string | null;
  readonly activeWorkspaceTabId?: string | null;
  readonly view: AppView;
  readonly tabs: readonly PersistedWorkspaceTabEntry[];
}

function getWorkspaceSessionStorageSafe(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.sessionStorage ?? null;
  } catch {
    return null;
  }
}

function sanitizeLibraryUiState(raw: unknown): LibraryUiState {
  if (!raw || typeof raw !== "object") {
    return { ...DEFAULT_LIBRARY_UI_STATE };
  }
  const rec = raw as Record<string, unknown>;
  const scrollRaw = typeof rec.scrollTop === "number" ? rec.scrollTop : Number(rec.scrollTop);
  return {
    search: typeof rec.search === "string" ? rec.search.slice(0, 240) : "",
    category: typeof rec.category === "string" && rec.category.trim() ? rec.category.trim() : "all",
    scrollTop: Number.isFinite(scrollRaw) && scrollRaw > 0 ? scrollRaw : 0,
  };
}

function clearWorkspaceSessionSnapshot(): void {
  const ss = getWorkspaceSessionStorageSafe();
  if (!ss) return;
  try {
    ss.removeItem(WORKSPACE_SESSION_STORAGE_KEY);
  } catch {
    /* bỏ qua trong môi trường bị chặn storage */
  }
}

function persistWorkspaceSessionSnapshot(state: {
  readonly libraryTabOpen: boolean;
  readonly libraryUiState: LibraryUiState;
  readonly view: AppView;
  readonly workspaceTabs: readonly WorkspaceTabItem[];
  readonly activeTabId: string | null;
  readonly active: ActiveSimulation | null;
  readonly activeSampleId: string | null;
  readonly activeHistoryId: string | null;
}): void {
  const ss = getWorkspaceSessionStorageSafe();
  if (!ss) return;
  const { tabs: effectiveTabs, activeTabId } = resolveEffectiveWorkspaceTabs({
    workspaceTabs: state.workspaceTabs,
    activeTabId: state.activeTabId,
    active: state.active,
    activeSampleId: state.activeSampleId,
    activeHistoryId: state.activeHistoryId,
  });
  if (
    !state.libraryTabOpen &&
    effectiveTabs.length === 0 &&
    (state.view === "home" || state.view === "landing")
  ) {
    clearWorkspaceSessionSnapshot();
    return;
  }
  const seenKeys = new Set<string>();
  const tabs: PersistedWorkspaceTabEntry[] = [];
  for (const tab of effectiveTabs) {
    const resourceKey = getWorkspaceTabResourceKey(tab);
    if (seenKeys.has(resourceKey)) continue;
    seenKeys.add(resourceKey);
    tabs.push({
      id: tab.id,
      kind: tab.kind,
      sampleId: tab.sampleId,
      historyId: tab.historyId,
      title: tab.title,
      ...(tab.kind === "draft" ? { draftText: tab.draftText ?? "" } : {}),
    });
  }
  const payload: PersistedWorkspaceSessionSnapshot = {
    version: 1,
    libraryTabOpen: state.libraryTabOpen,
    libraryUiState: sanitizeLibraryUiState(state.libraryUiState),
    activeTabId,
    activeWorkspaceTabId: activeTabId,
    view: state.view,
    tabs,
  };
  try {
    ss.setItem(WORKSPACE_SESSION_STORAGE_KEY, JSON.stringify(payload));
  } catch {
    /* bỏ qua trong môi trường đầy hoặc bị chặn storage */
  }
}

function readWorkspaceSessionSnapshot(): PersistedWorkspaceSessionSnapshot | null {
  const ss = getWorkspaceSessionStorageSafe();
  if (!ss) return null;
  try {
    const raw = ss.getItem(WORKSPACE_SESSION_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    if (!parsed || typeof parsed !== "object" || parsed.version !== 1) return null;
    const rawTabs = Array.isArray(parsed.tabs) ? parsed.tabs : [];
    const tabs: PersistedWorkspaceTabEntry[] = [];
    for (const entry of rawTabs) {
      if (!entry || typeof entry !== "object") continue;
      const rec = entry as Record<string, unknown>;
      if (rec.kind !== "simulation" && rec.kind !== "draft") continue;
      if (typeof rec.id !== "string" || !rec.id.trim()) continue;
      tabs.push({
        id: rec.id.trim(),
        kind: rec.kind,
        sampleId: typeof rec.sampleId === "string" && rec.sampleId.trim() ? rec.sampleId.trim() : null,
        historyId: typeof rec.historyId === "string" && rec.historyId.trim() ? rec.historyId.trim() : null,
        title: typeof rec.title === "string" && rec.title.trim() ? rec.title.trim() : "Mô phỏng 3D",
        ...(rec.kind === "draft" && typeof rec.draftText === "string" ? { draftText: rec.draftText } : {}),
      });
    }
    const activeTabId =
      typeof parsed.activeWorkspaceTabId === "string" && parsed.activeWorkspaceTabId.trim()
        ? parsed.activeWorkspaceTabId.trim()
        : typeof parsed.activeTabId === "string" && parsed.activeTabId.trim()
          ? parsed.activeTabId.trim()
          : null;
    const view: AppView =
      parsed.view === "library" || parsed.view === "workspace" || parsed.view === "home"
        ? parsed.view
        : "home";
    return {
      version: 1,
      libraryTabOpen: Boolean(parsed.libraryTabOpen),
      libraryUiState: sanitizeLibraryUiState(parsed.libraryUiState),
      activeTabId,
      activeWorkspaceTabId: activeTabId,
      view,
      tabs,
    };
  } catch {
    return null;
  }
}

const envelopeValidationCache = new WeakMap<
  object,
  { readonly ok: boolean; readonly error?: string }
>();

function checkEnvelopeReadyStatus(envelope: SimulationEnvelope | null | undefined): {
  readonly ok: boolean;
  readonly error?: string;
} {
  if (!envelope || typeof envelope !== "object") {
    return { ok: false, error: "MISSING_ENVELOPE" };
  }
  const cached = envelopeValidationCache.get(envelope);
  if (cached) return cached;

  const mod = getSimulation(envelope.simulation_id);
  if (!mod) {
    const res = { ok: false, error: `UNSUPPORTED_MODULE:${envelope.simulation_id}` };
    envelopeValidationCache.set(envelope, res);
    return res;
  }
  let validated: ConfigResult<unknown>;
  try {
    validated = mod.validateEnvelope
      ? mod.validateEnvelope(envelope)
      : mod.validateConfig(envelope.config);
  } catch {
    validated = { ok: false, error: "ENVELOPE_VALIDATION_EXCEPTION" };
  }
  const res = validated.ok
    ? { ok: true }
    : { ok: false, error: validated.error || "INVALID_SIMULATION_CONFIG" };
  envelopeValidationCache.set(envelope, res);
  return res;
}

function deriveProblemAttemptTitle(statement: string, fallback = "Đề toán đang xử lý"): string {
  const clean = stripStatusPrefixesFromTitle(statement).replace(/\s+/g, " ").trim();
  if (!clean) return fallback;
  if (clean.length <= 56) return clean;
  return `${clean.slice(0, 54).trimEnd()}…`;
}

export function resolveEffectiveWorkspaceTabs(state: {
  readonly workspaceTabs: readonly WorkspaceTabItem[];
  readonly activeTabId: string | null;
  readonly active: ActiveSimulation | null;
  readonly activeSampleId: string | null;
  readonly activeHistoryId: string | null;
}): {
  readonly tabs: WorkspaceTabItem[];
  readonly activeTabId: string | null;
} {
  if (state.workspaceTabs.length > 0) {
    const resolvedActiveId =
      state.activeTabId ?? state.workspaceTabs[state.workspaceTabs.length - 1]?.id ?? null;
    return {
      tabs: [...state.workspaceTabs],
      activeTabId: resolvedActiveId,
    };
  }
  if (!state.active) {
    return { tabs: [], activeTabId: null };
  }
  const fallbackId = state.activeSampleId
    ? `tab-sample-${state.activeSampleId}`
    : state.activeHistoryId
      ? `tab-hist-${state.activeHistoryId}`
      : "tab-sim-0";
  return {
    tabs: [
      {
        id: fallbackId,
        problemId:
          state.activeSampleId ?? state.activeHistoryId ?? state.active.envelope.simulation_id,
        sessionId: state.activeHistoryId ?? state.activeSampleId ?? "session-0",
        kind: "simulation",
        title: state.active.envelope.title?.trim() || "Mô phỏng 3D",
        active: state.active,
        sampleId: state.activeSampleId,
        historyId: state.activeHistoryId,
      },
    ],
    activeTabId: fallbackId,
  };
}

/**
 * V5/V6 — Hợp nhất danh sách `Đang mở` (workspaceTabs), `Gần đây` (history) và các lượt phân tích đang chạy / cần chú ý (`processingRecords`)
 * thành MỘT danh sách `BÀI TOÁN` duy nhất:
 * - Khử trùng lặp theo `canonicalId` ổn định (`historyId`, `"tab-draft-new"`, hoặc `attemptId`), KHÔNG BAO GIỜ khử trùng lặp theo tiêu đề.
 * - Phân loại `processingStatus` hoàn toàn theo bằng chứng dữ liệu thực tế:
 *   - `"ready"` (`Sẵn sàng`): bài toán đã xử lý hoàn tất với `SimulationEnvelope` hợp lệ (không phụ thuộc tab đóng/mở hay `Bước X/Y`).
 *   - `"needs_attention"` (`Cần chú ý`): bài toán có lỗi xác thực/phân tích/từ chối (`AnalysisUnsupported`, `analysisError`, `clientFailure`, hoặc scene 3D không hợp lệ).
 *   - `"in_progress"` (`Đang tiến hành`): chỉ khi bài toán có tác vụ phân tích/dựng hình đang thực sự chạy (`status === "in_progress"` hoặc `analyzing === true` trên bản nháp đang gửi).
 *   - `"draft"` (`Bản nháp chưa gửi`): chỉ hiển thị ở `"all"`, tuyệt đối không vào `"ready"`, `"needs_attention"`, hay `"in_progress"`.
 */
export function buildUnifiedProblemList(params: {
  readonly effectiveTabs: readonly WorkspaceTabItem[];
  readonly effectiveActiveTabId: string | null;
  readonly view: AppView;
  readonly history: readonly HistoryItem[];
  readonly filter?: LeftRailProblemFilter;
  readonly processingRecords?: Readonly<Record<string, ProblemProcessingRecord>>;
  readonly analyzing?: boolean;
  readonly activeProblemText?: string;
}): UnifiedSidebarProblemItem[] {
  const {
    effectiveTabs,
    effectiveActiveTabId,
    view,
    history,
    filter = "all",
    processingRecords = {},
    analyzing = false,
    activeProblemText = "",
  } = params;

  const historyById = new Map<string, HistoryItem>();
  for (const h of history) {
    if (!historyById.has(h.id)) {
      historyById.set(h.id, h);
    }
  }

  const seenCanonicalIds = new Set<string>();
  const combined: UnifiedSidebarProblemItem[] = [];

  // 1. Các bài toán đã có dữ liệu mô phỏng đang mở trên thanh tab Workspace (không bao giờ đưa tab nháp `draft` vào BÀI TOÁN)
  for (let i = 0; i < effectiveTabs.length; i += 1) {
    const tab = effectiveTabs[i]!;
    if (tab.kind === "draft") continue;

    const canonicalId =
      tab.historyId ?? (tab.active ? historyIdOf(tab.active.envelope) : tab.id);
    const matchedProcessingRecord: ProblemProcessingRecord | null =
      processingRecords[canonicalId] ?? null;

    if (seenCanonicalIds.has(canonicalId)) continue;
    seenCanonicalIds.add(canonicalId);

    const historyItem = historyById.get(canonicalId) ?? null;
    const meta = historyStore.getMeta(canonicalId);
    const customTitle = (meta?.customTitle ?? historyItem?.customTitle ?? "").trim() || null;

    const resolvedTitle =
      customTitle ||
      historyItem?.title?.trim() ||
      tab.title?.trim() ||
      tab.active?.envelope.title?.trim() ||
      "Mô phỏng 3D";

    const problemStatement =
      tab.active?.problemStatement ??
      tab.active?.envelope.problem_statement ??
      historyItem?.originalInput ??
      historyItem?.envelope.problem_statement ??
      "";

    const pinned = Boolean(meta?.pinned ?? historyItem?.pinned);
    const pinnedAt = pinned
      ? (meta?.pinnedAt ?? historyItem?.pinnedAt ?? historyItem?.updatedAt ?? 1)
      : null;

    const fallbackAccessMs = 9_000_000_000_000 - i;
    const lastAccessMs =
      matchedProcessingRecord?.updatedAt ||
      historyItem?.lastViewedAt ||
      historyItem?.updatedAt ||
      historyItem?.createdAt ||
      fallbackAccessMs;

    let processingStatus: ProblemProcessingStatus = "unknown";
    let processingReason: string | null = null;

    if (matchedProcessingRecord?.status === "in_progress") {
      processingStatus = "in_progress";
      processingReason = matchedProcessingRecord.reasonMessage ?? null;
    } else if (matchedProcessingRecord?.status === "needs_attention") {
      processingStatus = "needs_attention";
      processingReason =
        matchedProcessingRecord.reasonMessage ??
        matchedProcessingRecord.reasonCode ??
        null;
    } else {
      const envelope = tab.active?.envelope ?? historyItem?.envelope ?? null;
      const check = checkEnvelopeReadyStatus(envelope);
      if (check.ok) {
        processingStatus = "ready";
      } else {
        processingStatus = "needs_attention";
        processingReason = check.error ?? "INVALID_SIMULATION";
      }
    }

    const envelopeForTab = tab.active?.envelope ?? historyItem?.envelope ?? null;
    const sampleIdForTab =
      tab.sampleId ??
      resolveGeometrySampleId({
        id: canonicalId,
        envelope: envelopeForTab,
      });
    const geometryFamily = resolveGeometrySolidFamily({
      envelope: envelopeForTab,
      sampleId: sampleIdForTab,
      problemStatement,
      title:
        tab.active?.envelope.title ??
        historyItem?.envelope.title ??
        matchedProcessingRecord?.title ??
        resolvedTitle,
    });

    combined.push({
      canonicalId,
      kind: tab.kind,
      title: resolvedTitle,
      problemStatement,
      geometryFamily,
      isOpenInTab: true,
      isCurrentActiveTab: view === "workspace" && tab.id === effectiveActiveTabId,
      isInHistory: historyItem !== null,
      openTab: tab,
      historyItem,
      processingRecord: matchedProcessingRecord,
      processingStatus,
      processingReason,
      pinned,
      pinnedAt,
      lastAccessMs,
    });
  }

  // 2. Các bài toán trong Lịch sử chưa nằm trong các tab đang mở
  for (const item of history) {
    if (seenCanonicalIds.has(item.id)) continue;
    seenCanonicalIds.add(item.id);

    const meta = historyStore.getMeta(item.id);
    const customTitle = (meta?.customTitle ?? item.customTitle ?? "").trim() || null;
    const resolvedTitle =
      customTitle || item.title?.trim() || item.envelope.title?.trim() || "Mô phỏng 3D";
    const problemStatement = item.originalInput ?? item.envelope.problem_statement ?? "";
    const pinned = Boolean(meta?.pinned ?? item.pinned);
    const pinnedAt = pinned ? (meta?.pinnedAt ?? item.pinnedAt ?? item.updatedAt ?? 1) : null;
    const lastAccessMs = item.lastViewedAt || item.updatedAt || item.createdAt || 0;

    const rec = processingRecords[item.id] ?? null;
    let processingStatus: ProblemProcessingStatus = "ready";
    let processingReason: string | null = null;

    if (rec?.status === "in_progress") {
      processingStatus = "in_progress";
      processingReason = rec.reasonMessage ?? null;
    } else if (rec?.status === "needs_attention") {
      processingStatus = "needs_attention";
      processingReason = rec.reasonMessage ?? rec.reasonCode ?? null;
    } else {
      const check = checkEnvelopeReadyStatus(item.envelope);
      if (check.ok) {
        processingStatus = "ready";
      } else {
        processingStatus = "needs_attention";
        processingReason = check.error ?? "INVALID_SIMULATION";
      }
    }

    const sampleIdForItem = resolveGeometrySampleId({
      id: item.id,
      envelope: item.envelope,
    });
    const geometryFamily = resolveGeometrySolidFamily({
      envelope: item.envelope,
      sampleId: sampleIdForItem,
      problemStatement,
      title: item.envelope.title ?? resolvedTitle,
    });

    combined.push({
      canonicalId: item.id,
      kind: "simulation",
      title: resolvedTitle,
      problemStatement,
      geometryFamily,
      isOpenInTab: false,
      isCurrentActiveTab: false,
      isInHistory: true,
      openTab: null,
      historyItem: item,
      processingRecord: rec,
      processingStatus,
      processingReason,
      pinned,
      pinnedAt,
      lastAccessMs,
    });
  }

  // 3. Các lượt phân tích đang chạy (`in_progress`) hoặc cần chú ý (`needs_attention`) chưa có trong tab hay history
  const sortedRecords = Object.values(processingRecords).sort(
    (a, b) => b.updatedAt - a.updatedAt,
  );
  for (const rec of sortedRecords) {
    if (seenCanonicalIds.has(rec.canonicalId)) continue;
    seenCanonicalIds.add(rec.canonicalId);

    const meta = historyStore.getMeta(rec.canonicalId);
    const customTitle = (meta?.customTitle ?? "").trim() || null;
    const resolvedTitle =
      customTitle ||
      rec.title?.trim() ||
      deriveProblemAttemptTitle(
        rec.problemStatement,
        rec.status === "needs_attention" ? "Đề toán cần chú ý" : "Đề toán đang xử lý",
      );
    const pinned = Boolean(meta?.pinned);
    const pinnedAt = pinned ? (meta?.pinnedAt ?? rec.updatedAt ?? 1) : null;
    const geometryFamily = resolveGeometrySolidFamily({
      sampleId: rec.canonicalId,
      problemStatement: rec.problemStatement,
      title: rec.title ?? resolvedTitle,
    });

    combined.push({
      canonicalId: rec.canonicalId,
      kind: "simulation",
      title: resolvedTitle,
      problemStatement: rec.problemStatement,
      geometryFamily,
      isOpenInTab: false,
      isCurrentActiveTab: false,
      isInHistory: false,
      openTab: null,
      historyItem: null,
      processingRecord: rec,
      processingStatus: rec.status,
      processingReason: rec.reasonMessage ?? rec.reasonCode ?? null,
      pinned,
      pinnedAt,
      lastAccessMs: rec.updatedAt || rec.createdAt || Date.now(),
    });
  }

  // Fallback khi `analyzing === true` được bật trực tiếp mà chưa đăng ký bản ghi `in_progress`
  if (
    analyzing &&
    !combined.some((x) => x.processingStatus === "in_progress")
  ) {
    const fallbackId = "attempt-in-progress-active";
    if (!seenCanonicalIds.has(fallbackId)) {
      seenCanonicalIds.add(fallbackId);
      const meta = historyStore.getMeta(fallbackId);
      const customTitle = (meta?.customTitle ?? "").trim() || null;
      const stmt = activeProblemText.trim();
      const geometryFamily = resolveGeometrySolidFamily({
        problemStatement: stmt,
        title: customTitle ?? undefined,
      });
      combined.push({
        canonicalId: fallbackId,
        kind: "simulation",
        title: customTitle || deriveProblemAttemptTitle(stmt, "Bài toán đang xử lý"),
        problemStatement: stmt,
        geometryFamily,
        isOpenInTab: false,
        isCurrentActiveTab: false,
        isInHistory: false,
        openTab: null,
        historyItem: null,
        processingRecord: null,
        processingStatus: "in_progress",
        processingReason: null,
        pinned: Boolean(meta?.pinned),
        pinnedAt: meta?.pinned ? (meta?.pinnedAt ?? 1) : null,
        lastAccessMs: 9_100_000_000_000,
      });
    }
  }

  const sortUnified = (list: UnifiedSidebarProblemItem[]): UnifiedSidebarProblemItem[] =>
    [...list].sort((a, b) => {
      if (a.pinned !== b.pinned) return a.pinned ? -1 : 1;
      if (a.pinned && b.pinned) {
        const diffPin = (b.pinnedAt ?? 0) - (a.pinnedAt ?? 0);
        if (diffPin !== 0) return diffPin;
      }
      const aInProg = a.processingStatus === "in_progress";
      const bInProg = b.processingStatus === "in_progress";
      if (aInProg !== bInProg) return aInProg ? -1 : 1;
      return b.lastAccessMs - a.lastAccessMs;
    });

  if (filter === "needs_attention") {
    return sortUnified(combined.filter((x) => x.processingStatus === "needs_attention"));
  }

  if (filter === "in_progress") {
    return sortUnified(combined.filter((x) => x.processingStatus === "in_progress"));
  }

  // filter === "all" | "ready": Danh sách BÀI TOÁN chính chỉ hiển thị các bài toán đã xử lý hợp lệ (READY),
  // không hiển thị bản nháp chưa gửi hoặc lượt đang xử lý / lỗi như một bài toán đã hoàn thành.
  return sortUnified(combined.filter((x) => x.processingStatus === "ready"));
}

interface AppState {
  problemText: string;
  analyzing: boolean;
  analysisError: string | null;
  clientFailure: ClientFailureContract | null;
  routeFailure: RouteFailureState | null;
  validRouteStack: AppView[];
  hasInAppNavigation: boolean;
  unsupported: AnalysisUnsupported | null;
  activeSampleId: string | null;

  /**
   * M9-UX1 (mở rộng M9-UX5): BỐN MẶT TRÌNH BÀY trên cùng store — "home" (mặc
   * định: composer + vài gợi ý nổi bật), "workspace" (khi có mô phỏng),
   * "library" (danh mục ĐẦY ĐỦ, gom nhóm), "history" (toàn bộ lịch sử).
   * Là presentation state như visualMode: không đụng engine.
   *
   * Vì sao tách "library" khỏi Home (M9-UX5): Home từng bung cả 12 mẫu tại chỗ
   * và liệt kê mọi bài đang học dở — học sinh học dở nhiều thì gợi ý bị đẩy
   * xuống, Home phình theo lịch sử. Danh mục đầy đủ có NHÀ RIÊNG thì Home
   * KHÔNG BAO GIỜ phình: luôn là composer + 6 gợi ý + 1 thẻ tiếp tục.
   */
  view: AppView;
  /**
   * M9-UX1: BẢN CHIẾU lịch sử bền (localStorage qua historyStore) để render.
   * Nguồn chân lý là storage; store chỉ mirror sau mỗi thao tác. reset()/goHome
   * KHÔNG xoá lịch sử — runtime state và learning history là hai đời sống riêng.
   */
  history: HistoryItem[];
  /** id item lịch sử của mô phỏng đang mở — để ghi tiến độ (cursor/mode). */
  activeHistoryId: string | null;

  /**
   * W4B-2Z §26 — các mô phỏng ĐANG MỞ. `active` bên dưới là BẢN LÀM VIỆC của
   * phiên đang chọn; chuyển phiên = chụp bản làm việc vào phiên cũ rồi khôi
   * phục bản của phiên mới. Không gọi AI, không validate lại, không `init` lại.
   */

  active: ActiveSimulation | null;
  workspaceTabs: WorkspaceTabItem[];
  activeTabId: string | null;
  libraryTabOpen: boolean;
  libraryUiState: LibraryUiState;
  workspaceNavStack: WorkspaceNavEntry[];
  workspaceNavIndex: number;
  navHistoryMode: "push" | "replace";
  /** Chỉ có nghĩa khi module có timeline capability. */
  playing: boolean;
  speedMs: number;

  /**
   * Trạng thái panel (tổng quát, không dính domain — M2 #3, #8).
   * M9-UX7: panel TRÁI đã GỠ HẲN — sau khi có trang Thư viện, danh mục tồn tại ở
   * ba nơi (Home / Thư viện / panel trái). Panel trái là bản sao thứ ba; đổi bài
   * nay đi qua Thư viện trên header. Workspace còn 2 cột: sân khấu + Giải thích.
   * W4B-2B §8: mặc định ĐÓNG ở mọi bề rộng — xem lý do ở chỗ khởi tạo bên dưới.
   */
  rightOpen: boolean;
  /* ⛔ `sidebarCollapsed` / `sidebarDrawerOpen` ĐÃ GỠ cùng cột điều hướng trái.
     Điều hướng nay là hàng ngang luôn hiện (`components/TopNav.tsx`) — nó không
     có trạng thái mở/thu/ngăn kéo nào để store phải nhớ. */
  /**
   * M9-UX5 — AI KHÔNG còn ngang hàng với Quan sát.
   * Trước đây panel phải là hai tab [Quan sát][Hỏi AI]: một nửa cột phải, lúc
   * nào cũng vậy, dành cho AI — trong khi luật gốc R0 nói LLM KHÔNG phải xương
   * sống của hệ. Nay cột phải LUÔN là Giải thích; AI là một mục THU GỌN ở đáy.
   * (Thay `inspectorTab: "inspect" | "ai"`.)
   */
  aiOpen: boolean;
  /**
   * W4B-3A — CHẾ ĐỘ KHÁM PHÁ có mở không. TRÌNH BÀY THUẦN, sống cạnh
   * `rightOpen`/`aiOpen`, KHÔNG bao giờ vào engine state hay spec; và cũng MÙ
   * DOMAIN: store không biết "khám phá" ở bài này nghĩa là kéo cột hay bấm liên
   * kết mạng.
   *
   * W13 — trước đây có cờ chị em `challengeOpen` cho chế độ Thử thách (cam kết
   * đi qua `predict.check` để engine phán đúng/sai). Năng lực đó đã bị gỡ hẳn:
   * sản phẩm là hệ mô phỏng tương tác, không phải hệ hỏi-đáp. Nay chỉ còn MỘT
   * chế độ thao tác, và nó không phán gì cả — hệ quả tất định là câu trả lời.
   *
   * Trước wave này cờ này sống ở `useState` cục bộ trong HAI renderer miền
   * (`domains/algorithm/ui.tsx`, `domains/network/ui.tsx`) với tên `labOpen`,
   * nên: (1) mỗi miền tự dựng lấy một nút mở, thành một DẢI nội dung dưới mô
   * hình; (2) chuyển phiên là mất chế độ đang mở mà không ai đo được; (3) không
   * test nào chạm được vào nó ngoài trình duyệt (SSR luôn thấy `false` —
   * `ARCHITECTURE_MAP §8` #13).
   */
  exploreOpen: boolean;
  /**
   * M8: visual mode là TRÌNH BÀY THUẦN TÚY — chọn component vẽ, không hơn.
   * KHÔNG nằm trong engine state/SimulationSpec, KHÔNG do LLM chọn, KHÔNG ảnh
   * hưởng tính toán tất định. Đổi mode giữ nguyên active/state/cursor.
   * Mặc định "2d"; nạp mô
   * phỏng mới thì quay về "2d" (chính sách M8: 2D là mặc định).
   */
  visualMode: VisualMode;

  setProblemText: (text: string) => void;
  setAnalyzing: (v: boolean) => void;
  setAnalysisError: (msg: string | null) => void;
  setClientFailure: (failure: ClientFailureContract | null) => void;
  reportNetworkFailure: (err: AxoClientError | ClientFailureContract) => void;
  syncLocationRoute: (pathname: string, hash?: string, search?: string) => void;
  escapeFromError: () => AppView;
  /** `originalInput`: đề gốc (text đã chuẩn hoá) — lưu vào lịch sử nếu có. */
  /** `recordId`: ID lần học (lần gửi mới từ `newAttemptId`, hoặc bản ghi đang mở lại) — xem `historyStore.record`. */
  loadEnvelope: (env: SimulationEnvelope, sampleId?: string, originalInput?: string, recordId?: string) => void;
  loadUnsupported: (u: AnalysisUnsupported, attemptId?: string, statement?: string) => void;
  clearUnsupported: () => void;

  /** M9-UX1 — điều hướng trình bày + lịch sử bền. */
  goHome: () => void;
  /** W05 — trang đứng TRƯỚC khi vào xưởng (ghi lúc `loadEnvelope` từ ngoài xưởng); đích của nút quay lại. */
  returnView: AppView;
  /** W05 — rời xưởng như `goHome` (dọn bài, bài giao) nhưng về đúng `returnView`. */
  roiXuong: () => void;
  openHistory: () => void;
  /** Mở lại từ lịch sử: envelope đã validate + engine tất định — 0 gọi AI. */
  reopenFromHistory: (id: string) => void;
  removeHistoryItem: (id: string) => void;
  clearHistory: () => void;

  /** Tương tác người học → module.apply (what-if, toggle, tham số...). */
  dispatch: (action: SimAction) => void;
  /** Điều khiển timeline — NO-OP nếu module không có capability (M2 #4). */
  goToStep: (step: number) => void;
  nextStep: () => void;
  prevStep: () => void;
  toStart: () => void;
  toEnd: () => void;
  /** Dựng lại state từ config — dùng cho cả progressive lẫn exploratory. */
  resetSim: () => void;

  /**
   * M7.14: thay config + state sau một EDIT đã validate (patch flow). Store
   * vẫn MÙ DOMAIN — cặp config/state mới do module tự dựng (vd applyEditedSpec)
   * rồi đưa vào đây nguyên khối; config tiếp tục bất biến sau khi thay.
   */
  replaceSimulation: (config: unknown, state: unknown) => void;

  setPlaying: (v: boolean) => void;
  setSpeedMs: (ms: number) => void;
  toggleRight: () => void;
  setAiOpen: (v: boolean) => void;
  setExploreOpen: (v: boolean) => void;
  openLibrary: () => void;
  openLanding: () => void;
  setLibraryUiState: (patch: Partial<LibraryUiState>) => void;
  hydrateWorkspaceSession: (opts?: { readonly force?: boolean }) => void;
  /**
   * TÓM TẮT tiêu điểm ngữ nghĩa của xưởng 3D — id vật đang chọn + việc vừa
   * làm. KHÔNG phải bản sao `InteractionState`: đó là `StudentObservation`,
   * thứ giáo viên đọc. `InteractionState` đầy đủ vẫn chỉ sống trong xưởng.
   */
  semanticFocus: { selectedId: string | null; action: string } | null;
  setSemanticFocus: (f: { selectedId: string | null; action: string } | null) => void;
  setView: (view: AppView) => void;

  /** Axo V2.7 Phase D: Modal Cài đặt tài khoản (#user-account-settings-modal) & email khôi phục mật khẩu */
  accountModalOpen: boolean;
  accountModalTab: "profile" | "security";
  openAccountModal: (tab?: "profile" | "security") => void;
  closeAccountModal: () => void;
  authResetEmail: string;
  setAuthResetEmail: (email: string) => void;

  /** M8: đổi renderer — CHỈ đổi trường trình bày, không đụng active. */
  setVisualMode: (mode: VisualMode) => void;
  leftRailManualCollapsed: boolean | null;
  leftRailHoverPreview: boolean;
  leftRailMobileOpen: boolean;
  leftRailSearchOpen: boolean;
  leftRailSearchQuery: string;
  leftRailActiveGroupCollapsed: boolean;
  leftRailRecentGroupCollapsed: boolean;
  leftRailProblemGroupCollapsed: boolean;
  leftRailProblemFilter: LeftRailProblemFilter;
  problemMetaVersion: number;
  problemProcessingRecords: Record<string, ProblemProcessingRecord>;
  lastAnalyzedStatement: string;
  guestEnteredApp: boolean;
  tabStepProgress: Record<string, { current: number; total: number }>;
  startProblemProcessing: (canonicalId: string, problemStatement: string, title?: string) => void;
  updateProblemProcessingStatement: (canonicalId: string, problemStatement: string, title?: string) => void;
  failProblemProcessing: (
    canonicalId: string,
    details: {
      readonly problemStatement?: string;
      readonly title?: string;
      readonly reasonCode?: string | null;
      readonly reasonMessage?: string | null;
      readonly interruptedByReload?: boolean;
      readonly failureKind?: ProblemProcessingFailureKind | null;
      readonly unsupported?: AnalysisUnsupported | null;
      readonly clientFailure?: ClientFailureContract | null;
      readonly analysisError?: string | null;
    },
  ) => void;
  clearProblemProcessing: (canonicalId: string) => void;
  hydrateProblemProcessingAfterReload: () => void;
  recoverProblemProcessingFromStorage: () => void;
  openProblemAttempt: (canonicalId: string) => void;
  selectSidebarProblem: (canonicalId: string) => void;
  toggleLeftRailCollapsed: (currentEffectiveCollapsed: boolean) => void;
  setLeftRailCollapsed: (collapsed: boolean | null) => void;
  setLeftRailHoverPreview: (hover: boolean) => void;
  setLeftRailMobileOpen: (open: boolean) => void;
  setLeftRailSearchOpen: (open: boolean) => void;
  setLeftRailSearchQuery: (query: string) => void;
  toggleLeftRailActiveGroup: () => void;
  toggleLeftRailRecentGroup: () => void;
  setLeftRailActiveGroupCollapsed: (collapsed: boolean) => void;
  setLeftRailRecentGroupCollapsed: (collapsed: boolean) => void;
  toggleLeftRailProblemGroup: () => void;
  setLeftRailProblemGroupCollapsed: (collapsed: boolean) => void;
  setLeftRailProblemFilter: (filter: LeftRailProblemFilter) => void;
  togglePinProblem: (canonicalId: string) => boolean;
  renameProblem: (canonicalId: string, newTitle: string) => boolean;
  deleteProblem: (canonicalId: string) => Promise<{ ok: boolean; error?: string }>;
  setGuestEnteredApp: (entered: boolean) => void;
  /** §D3/§D5 — Đăng xuất khỏi Workspace: xóa sạch dữ liệu riêng tư và giữ phiên Khách tại /app. */
  enterGuestWorkspaceAfterLogout: () => void;
  setTabStepProgress: (tabId: string, current: number, total: number) => void;
  openDraftWorkspaceTab: () => void;
  activateWorkspaceTab: (tabId: string) => void;
  closeWorkspaceTab: (tabId: string) => void;
  workspaceGoBack: () => void;
  workspaceGoForward: () => void;
  reset: () => void;
}


export const useAppStore = create<AppState>((set, get) => {
  let hasHydratedLocation = false;
  let hasHydratedWorkspaceSession = false;
  /** Chạy một phép biến đổi qua timeline capability; không có thì bỏ qua. */
  function withTimeline(
    fn: (tl: TimelineCapability<unknown>, state: unknown) => unknown,
  ): void {
    const { active, activeHistoryId } = get();
    if (!active) return;
    const mod = getSimulation(active.moduleId);
    if (!mod?.timeline) return;
    const next = fn(mod.timeline, active.state);
    if (next !== active.state) {
      set({ active: { ...active, state: next } });
      // M9-UX1: ghi tiến độ TRÌNH BÀY vào lịch sử bền (cursor là tất định nên
      // goToStep khôi phục đúng). Chỉ storage — không set() để khỏi re-render.
      if (activeHistoryId) {
        const lastCursor = mod.timeline.currentStep(next);
        historyStore.touch(activeHistoryId, { lastCursor });
        if (useAuthStore.getState().user !== null) {
          void touchServerHistory(activeHistoryId, { lastCursor });
        }
      }
    }
  }



  return {
    problemText: "",
    analyzing: false,
    analysisError: null,
    clientFailure: null,
    routeFailure: null,
    validRouteStack: ["home"],
    hasInAppNavigation: false,
    unsupported: null,
    activeSampleId: null,
    view: "home",
    returnView: "home",
    history: historyStore.list(),
    activeHistoryId: null,
    active: null,
    workspaceTabs: [],
    activeTabId: null,
    libraryTabOpen: false,
    libraryUiState: { ...DEFAULT_LIBRARY_UI_STATE },
    workspaceNavStack: [{ view: "home", tabId: null }],
    workspaceNavIndex: 0,
    navHistoryMode: "push",
    playing: false,
    speedMs: 1200,
    // W4B-2B §8 — panel PHẢI (Giải thích) ĐÓNG mặc định ở MỌI bề rộng.
    //
    // Trước đây nó mở sẵn trên màn ≥1100px với lý do "biến/mã giả là biểu diễn
    // liên kết cốt lõi". Lý do đó vẫn đúng, nhưng nó biện minh cho việc panel
    // LUÔN SẴN CÓ, không phải cho việc panel LUÔN MỞ: mở sẵn thì sân khấu — thứ
    // duy nhất mang cơ chế của bài — bị cắt ~316px ngay ở cái nhìn đầu tiên, và
    // học sinh đọc lời giải thích trước khi kịp tự nhìn ra điều gì.
    //
    // An toàn được vì thông tin KHÔNG nằm riêng ở đây: mọi bước đều mang giá trị
    // trong `Step.narration` do engine dựng (vd `core/program.ts` ghép tên+giá
    // trị biến vào chính bước xét điều kiện), và narration nằm ở cột giữa nên
    // không phụ thuộc trạng thái panel. Panel là đường ĐÀO SÂU, mở bằng nút
    // "Giải thích" trên header — không phải nguồn duy nhất của sự thật.
    //
    // Hằng `WIDE_SCREEN` đã gỡ: không còn mặc định nào phụ thuộc `window` nữa,
    // nên SSR và trình duyệt khởi tạo giống hệt nhau.
    rightOpen: false,
    semanticFocus: null,
    aiOpen: false,
    exploreOpen: false,
    visualMode: "2d",
    leftRailManualCollapsed: null,
    leftRailHoverPreview: false,
    leftRailMobileOpen: false,
    leftRailSearchOpen: false,
    leftRailSearchQuery: "",
    leftRailActiveGroupCollapsed: false,
    leftRailRecentGroupCollapsed: false,
    leftRailProblemGroupCollapsed: false,
    leftRailProblemFilter: "all",
    problemMetaVersion: 0,
    problemProcessingRecords: recoverPersistedProblemProcessingRecords(),
    lastAnalyzedStatement: "",
    guestEnteredApp: false,
    tabStepProgress: {},
    startProblemProcessing: (canonicalId, problemStatement, title) =>
      set((s) => {
        if (!canonicalId) return {};
        const now = Date.now();
        const prev = s.problemProcessingRecords[canonicalId];
        const meta = historyStore.getMeta(canonicalId);
        const stmt = problemStatement.trim();
        const resolvedTitle = stripStatusPrefixesFromTitle(
          meta?.customTitle?.trim() ||
            title?.trim() ||
            prev?.title?.trim() ||
            deriveProblemAttemptTitle(stmt, "Bài toán đang xử lý"),
        );
        if (stmt) {
          historyStore.writeDraftText(stmt);
        }
        const nextRecords: Record<string, ProblemProcessingRecord> = {
          ...s.problemProcessingRecords,
          [canonicalId]: {
            canonicalId,
            title: resolvedTitle,
            problemStatement: stmt,
            status: "in_progress",
            reasonCode: null,
            reasonMessage: null,
            interruptedByReload: false,
            failureKind: null,
            unsupported: null,
            clientFailure: null,
            analysisError: null,
            createdAt: prev?.createdAt ?? now,
            updatedAt: now,
          },
        };
        persistProblemProcessingRecords(nextRecords);
        return {
          problemProcessingRecords: nextRecords,
          ...(stmt ? { lastAnalyzedStatement: stmt } : {}),
        };
      }),
    updateProblemProcessingStatement: (canonicalId, problemStatement, title) =>
      set((s) => {
        const prev = s.problemProcessingRecords[canonicalId];
        if (!prev) return {};
        const meta = historyStore.getMeta(canonicalId);
        const stmt = problemStatement.trim();
        const resolvedTitle = stripStatusPrefixesFromTitle(
          meta?.customTitle?.trim() ||
            title?.trim() ||
            deriveProblemAttemptTitle(stmt, prev.title),
        );
        if (stmt) {
          historyStore.writeDraftText(stmt);
        }
        const nextRecords: Record<string, ProblemProcessingRecord> = {
          ...s.problemProcessingRecords,
          [canonicalId]: {
            ...prev,
            title: resolvedTitle,
            problemStatement: stmt,
            updatedAt: Date.now(),
          },
        };
        persistProblemProcessingRecords(nextRecords);
        return {
          problemProcessingRecords: nextRecords,
          ...(stmt ? { lastAnalyzedStatement: stmt } : {}),
        };
      }),
    failProblemProcessing: (canonicalId, details) =>
      set((s) => {
        if (!canonicalId) return {};
        const now = Date.now();
        const prev = s.problemProcessingRecords[canonicalId];
        const meta = historyStore.getMeta(canonicalId);
        const stmt = (details.problemStatement ?? prev?.problemStatement ?? s.problemText ?? "").trim();
        const resolvedTitle = stripStatusPrefixesFromTitle(
          meta?.customTitle?.trim() ||
            details.title?.trim() ||
            prev?.title?.trim() ||
            deriveProblemAttemptTitle(stmt, "Bài toán cần chú ý"),
        );
        const effectiveReasonCode = details.reasonCode ?? prev?.reasonCode ?? null;
        const isReloadInterrupted =
          details.interruptedByReload === true ||
          effectiveReasonCode === "INTERRUPTED_BY_RELOAD" ||
          details.failureKind === "CONNECTION_INTERRUPTED";
        const effectiveFailureKind: ProblemProcessingFailureKind =
          details.failureKind ??
          (isReloadInterrupted ? "CONNECTION_INTERRUPTED" : "PROBLEM_ERROR");
        if (stmt && !historyStore.readDraftText().trim()) {
          historyStore.writeDraftText(stmt);
        }
        const nextRecords: Record<string, ProblemProcessingRecord> = {
          ...s.problemProcessingRecords,
          [canonicalId]: {
            canonicalId,
            title: resolvedTitle,
            problemStatement: stmt,
            status: "needs_attention",
            reasonCode: effectiveReasonCode,
            reasonMessage: details.reasonMessage ?? prev?.reasonMessage ?? null,
            interruptedByReload: isReloadInterrupted,
            failureKind: effectiveFailureKind,
            unsupported: details.unsupported !== undefined ? details.unsupported : (prev?.unsupported ?? null),
            clientFailure: details.clientFailure !== undefined ? details.clientFailure : (prev?.clientFailure ?? null),
            analysisError: details.analysisError !== undefined ? details.analysisError : (prev?.analysisError ?? null),
            createdAt: prev?.createdAt ?? now,
            updatedAt: now,
          },
        };
        persistProblemProcessingRecords(nextRecords);
        return {
          problemProcessingRecords: nextRecords,
          ...(stmt ? { lastAnalyzedStatement: stmt } : {}),
        };
      }),
    clearProblemProcessing: (canonicalId) =>
      set((s) => {
        if (!canonicalId || !(canonicalId in s.problemProcessingRecords)) return {};
        const next = { ...s.problemProcessingRecords };
        delete next[canonicalId];
        persistProblemProcessingRecords(next);
        return { problemProcessingRecords: next };
      }),
    hydrateProblemProcessingAfterReload: () =>
      set((s) => {
        const persisted = recoverPersistedProblemProcessingRecords();
        const now = Date.now();
        const merged: Record<string, ProblemProcessingRecord> = { ...persisted };
        for (const [id, rec] of Object.entries(s.problemProcessingRecords)) {
          if (rec.status === "in_progress") {
            merged[id] = {
              ...rec,
              title: stripStatusPrefixesFromTitle(rec.title),
              status: "needs_attention",
              reasonCode: rec.reasonCode ?? "INTERRUPTED_BY_RELOAD",
              reasonMessage: rec.reasonMessage ?? INTERRUPTED_BY_RELOAD_REASON,
              interruptedByReload: true,
              failureKind: "CONNECTION_INTERRUPTED",
              analysisError: rec.analysisError ?? INTERRUPTED_BY_RELOAD_REASON,
              updatedAt: now,
            };
          } else if (!(id in merged)) {
            const isReloadInterrupted =
              rec.interruptedByReload === true ||
              rec.reasonCode === "INTERRUPTED_BY_RELOAD" ||
              rec.failureKind === "CONNECTION_INTERRUPTED";
            merged[id] = {
              ...rec,
              title: stripStatusPrefixesFromTitle(rec.title),
              interruptedByReload: isReloadInterrupted,
              failureKind:
                rec.failureKind ??
                (isReloadInterrupted ? "CONNECTION_INTERRUPTED" : "PROBLEM_ERROR"),
            };
          }
        }
        persistProblemProcessingRecords(merged);

        // Nếu có lượt xử lý bị ngắt bởi reload và ô nháp hiện tại đang trống, khôi phục đề bài vào algosim.draft.v1 & problemText
        const reloadInterruptedList = Object.values(merged)
          .filter(
            (r) =>
              (r.interruptedByReload === true ||
                r.reasonCode === "INTERRUPTED_BY_RELOAD") &&
              r.problemStatement.trim().length > 0,
          )
          .sort((a, b) => b.updatedAt - a.updatedAt);
        const latestInterruptedStmt =
          reloadInterruptedList[0]?.problemStatement.trim() || "";
        if (latestInterruptedStmt && !historyStore.readDraftText().trim()) {
          historyStore.writeDraftText(latestInterruptedStmt);
        }
        const restoredDraft =
          s.problemText.trim() ||
          latestInterruptedStmt ||
          historyStore.readDraftText().trim();

        return {
          problemProcessingRecords: merged,
          analyzing: false,
          ...(restoredDraft && !s.problemText.trim()
            ? {
                problemText: restoredDraft,
                lastAnalyzedStatement: restoredDraft,
                workspaceTabs: s.workspaceTabs.map((t) =>
                  t.id === "tab-draft-new" && !(t.draftText ?? "").trim()
                    ? { ...t, draftText: restoredDraft }
                    : t,
                ),
              }
            : latestInterruptedStmt
              ? { lastAnalyzedStatement: latestInterruptedStmt }
              : {}),
        };
      }),
    recoverProblemProcessingFromStorage: () => {
      get().hydrateProblemProcessingAfterReload();
    },
    openProblemAttempt: (canonicalId) =>
      set((s) => {
        const rec = s.problemProcessingRecords[canonicalId];
        if (!rec) return {};
        const restoredStmt = (rec.problemStatement || s.problemText || "").trim();
        if (restoredStmt) {
          historyStore.writeDraftText(restoredStmt);
        }
        const syncedTabs = syncCurrentTabInList(
          s.workspaceTabs,
          s.activeTabId,
          s.active,
          s.activeSampleId,
          s.activeHistoryId,
          restoredStmt || s.problemText,
        ).map((t) =>
          t.id === "tab-draft-new"
            ? { ...t, draftText: restoredStmt || s.problemText }
            : t,
        );
        const nav = pushWorkspaceNav(
          s.workspaceNavStack,
          s.workspaceNavIndex,
          { view: "home", tabId: null },
          "home",
        );
        if (typeof window !== "undefined" && typeof window.dispatchEvent === "function") {
          try {
            window.dispatchEvent(
              new CustomEvent("axo:restore-problem-draft", {
                detail: {
                  canonicalId,
                  problemStatement: restoredStmt,
                  record: rec,
                },
              }),
            );
          } catch {
            /* bỏ qua trong môi trường SSR */
          }
        }
        return {
          view: "home",
          active: null,
          workspaceTabs: syncedTabs,
          workspaceNavStack: nav.stack,
          workspaceNavIndex: nav.index,
          navHistoryMode: "push",
          activeHistoryId: null,
          activeSampleId: null,
          playing: false,
          problemText: restoredStmt || s.problemText,
          lastAnalyzedStatement: restoredStmt || s.lastAnalyzedStatement,
          unsupported: rec.unsupported ?? null,
          clientFailure: rec.clientFailure ?? null,
          analysisError: rec.analysisError ?? null,
          hasInAppNavigation: true,
          validRouteStack: pushSafeRoute(s.validRouteStack, "home"),
        };
      }),
    selectSidebarProblem: (canonicalId) => {
      if (!canonicalId) return;
      if (canonicalId === LIBRARY_TAB_ID || canonicalId === LIBRARY_RESOURCE_KEY) {
        get().openLibrary();
        return;
      }
      const curState = get();
      const { tabs: effectiveTabs } = resolveEffectiveWorkspaceTabs({
        workspaceTabs: curState.workspaceTabs,
        activeTabId: curState.activeTabId,
        active: curState.active,
        activeSampleId: curState.activeSampleId,
        activeHistoryId: curState.activeHistoryId,
      });
      const histItem = historyStore.list().find((x) => x.id === canonicalId);
      const sampleIdMatch = resolveGeometrySampleId({ id: canonicalId });
      const openTab = findMatchingOpenSimulationTab(effectiveTabs, {
        tabId: canonicalId,
        sampleId: sampleIdMatch,
        historyId: canonicalId,
        title: histItem?.title ?? null,
        originalInput: histItem?.originalInput ?? null,
        problemStatement: histItem?.envelope?.problem_statement ?? null,
        envelope: histItem?.envelope ?? null,
      });
      if (openTab) {
        get().activateWorkspaceTab(openTab.id);
        return;
      }
      if (histItem) {
        get().reopenFromHistory(histItem.id);
        return;
      }
      if (sampleIdMatch) {
        const entry =
          publicCatalog().find((s) => s.id === sampleIdMatch) ??
          offlineCatalog().find((s) => s.id === sampleIdMatch);
        if (entry) {
          get().loadEnvelope(entry.envelope, entry.id);
          return;
        }
      }
      if (canonicalId in curState.problemProcessingRecords) {
        get().openProblemAttempt(canonicalId);
        return;
      }
      if (canonicalId === "tab-draft-new") {
        get().openDraftWorkspaceTab();
      }
    },
    toggleLeftRailCollapsed: (currentEffectiveCollapsed) =>
      set({
        leftRailManualCollapsed: !currentEffectiveCollapsed,
        leftRailHoverPreview: false,
      }),
    setLeftRailCollapsed: (collapsed) =>
      set({
        leftRailManualCollapsed: collapsed,
        leftRailHoverPreview: false,
      }),
    setLeftRailHoverPreview: (hover) => set({ leftRailHoverPreview: hover }),
    setLeftRailMobileOpen: (open) => set({ leftRailMobileOpen: open }),
    setLeftRailSearchOpen: (open) =>
      set(() => ({
        leftRailSearchOpen: open,
        ...(open
          ? { leftRailManualCollapsed: false, leftRailHoverPreview: false }
          : { leftRailSearchQuery: "" }),
      })),
    setLeftRailSearchQuery: (query) => set({ leftRailSearchQuery: query }),
    toggleLeftRailActiveGroup: () =>
      set((s) => ({ leftRailActiveGroupCollapsed: !s.leftRailActiveGroupCollapsed })),
    toggleLeftRailRecentGroup: () =>
      set((s) => ({ leftRailRecentGroupCollapsed: !s.leftRailRecentGroupCollapsed })),
    setLeftRailActiveGroupCollapsed: (collapsed) =>
      set({ leftRailActiveGroupCollapsed: collapsed }),
    setLeftRailRecentGroupCollapsed: (collapsed) =>
      set({ leftRailRecentGroupCollapsed: collapsed }),
    toggleLeftRailProblemGroup: () =>
      set((s) => ({ leftRailProblemGroupCollapsed: !s.leftRailProblemGroupCollapsed })),
    setLeftRailProblemGroupCollapsed: (collapsed) =>
      set({ leftRailProblemGroupCollapsed: collapsed }),
    setLeftRailProblemFilter: (filter) => set({ leftRailProblemFilter: filter }),
    togglePinProblem: (canonicalId) => {
      const currentMeta = historyStore.getMeta(canonicalId);
      const nextPinned = !Boolean(currentMeta?.pinned);
      historyStore.setPinned(canonicalId, nextPinned);
      set((s) => ({
        history: historyStore.list(),
        problemMetaVersion: s.problemMetaVersion + 1,
      }));
      return nextPinned;
    },
    renameProblem: (canonicalId, newTitle) => {
      const trimmed = stripStatusPrefixesFromTitle(newTitle);
      if (!canonicalId || !trimmed) return false;
      const updatedItem = historyStore.rename(canonicalId, trimmed);
      if (updatedItem && useAuthStore.getState().user !== null) {
        void upsertServerHistory(updatedItem);
      }
      set((s) => {
        const baseTabs = syncCurrentTabInList(
          s.workspaceTabs,
          s.activeTabId,
          s.active,
          s.activeSampleId,
          s.activeHistoryId,
          s.problemText,
        );
        const matchesCanonical = (t: WorkspaceTabItem): boolean => {
          if (t.id === canonicalId || t.historyId === canonicalId) return true;
          if (t.kind === "simulation" && t.active) {
            return historyIdOf(t.active.envelope) === canonicalId;
          }
          return false;
        };
        const updatedTabs = baseTabs.map((t) => {
          if (!matchesCanonical(t)) return t;
          if (t.kind === "draft") {
            return { ...t, title: trimmed };
          }
          return {
            ...t,
            title: trimmed,
            active: t.active
              ? {
                  ...t.active,
                  envelope: { ...t.active.envelope, title: trimmed },
                }
              : null,
          };
        });
        const activeMatches =
          s.active !== null &&
          (s.activeHistoryId === canonicalId ||
            s.activeTabId === canonicalId ||
            historyIdOf(s.active.envelope) === canonicalId);
        const nextActive =
          activeMatches && s.active
            ? {
                ...s.active,
                envelope: { ...s.active.envelope, title: trimmed },
              }
            : s.active;
        const nextRecords =
          canonicalId in s.problemProcessingRecords
            ? {
                ...s.problemProcessingRecords,
                [canonicalId]: {
                  ...s.problemProcessingRecords[canonicalId]!,
                  title: trimmed,
                },
              }
            : s.problemProcessingRecords;
        if (canonicalId in s.problemProcessingRecords) {
          persistProblemProcessingRecords(nextRecords);
        }
        return {
          workspaceTabs: updatedTabs,
          active: nextActive,
          history: historyStore.list(),
          problemProcessingRecords: nextRecords,
          problemMetaVersion: s.problemMetaVersion + 1,
        };
      });
      return true;
    },
    deleteProblem: async (canonicalId) => {
      if (!canonicalId) {
        return { ok: false, error: "Không xác định được bài toán cần xóa." };
      }
      const isLoggedIn = useAuthStore.getState().user !== null;
      const existsInHistory = historyStore.list().some((x) => x.id === canonicalId);
      if (isLoggedIn && existsInHistory && canonicalId !== "tab-draft-new") {
        const deletedRemote = await deleteServerHistoryItem(canonicalId);
        if (!deletedRemote) {
          return {
            ok: false,
            error: "Không thể xóa bài toán trên máy chủ lúc này. Vui lòng thử lại.",
          };
        }
      }
      historyStore.remove(canonicalId);

      // Nếu bài toán đang mở ở bất kỳ tab nào trong Workspace, đóng tab đó để không trỏ tới dữ liệu đã xóa
      const curState = get();
      const { tabs: effectiveTabs } = resolveEffectiveWorkspaceTabs({
        workspaceTabs: curState.workspaceTabs,
        activeTabId: curState.activeTabId,
        active: curState.active,
        activeSampleId: curState.activeSampleId,
        activeHistoryId: curState.activeHistoryId,
      });
      const matchingTabs = effectiveTabs.filter((t) => {
        if (t.id === canonicalId || t.historyId === canonicalId) return true;
        if (t.kind === "simulation" && t.active) {
          return historyIdOf(t.active.envelope) === canonicalId;
        }
        return false;
      });
      for (const tab of matchingTabs) {
        get().closeWorkspaceTab(tab.id);
      }

      set((s) => {
        const nextRecords = { ...s.problemProcessingRecords };
        delete nextRecords[canonicalId];
        persistProblemProcessingRecords(nextRecords);
        return {
          history: historyStore.list(),
          problemProcessingRecords: nextRecords,
          problemMetaVersion: s.problemMetaVersion + 1,
        };
      });
      return { ok: true };
    },
    setGuestEnteredApp: (entered) => set({ guestEnteredApp: entered }),

    enterGuestWorkspaceAfterLogout: () => {
      clearWorkspaceSessionSnapshot();
      historyStore.clear();
      if (typeof window !== "undefined") {
        try {
          window.sessionStorage.removeItem("axo_auth_session_hint");
        } catch {
          /* bỏ qua nếu trình duyệt chặn sessionStorage */
        }
      }
      set({
        view: "home",
        guestEnteredApp: true,
        active: null,
        workspaceTabs: [],
        activeTabId: null,
        activeHistoryId: null,
        activeSampleId: null,
        history: [],
        problemProcessingRecords: {},
        problemText: "",
        lastAnalyzedStatement: "",
        unsupported: null,
        analysisError: null,
        clientFailure: null,
        routeFailure: null,
        playing: false,
        analyzing: false,
        accountModalOpen: false,
        leftRailSearchOpen: false,
        leftRailSearchQuery: "",
        tabStepProgress: {},
        navHistoryMode: "replace",
        hasInAppNavigation: true,
        returnView: "home",
        workspaceNavStack: [{ view: "home", tabId: null }],
        workspaceNavIndex: 0,
        validRouteStack: ["home"],
      });
    },
    setTabStepProgress: (tabId, current, total) =>
      set((s) => {
        const prev = s.tabStepProgress[tabId];
        if (prev && prev.current === current && prev.total === total) return s;
        return {
          tabStepProgress: {
            ...s.tabStepProgress,
            [tabId]: { current, total },
          },
        };
      }),

    setProblemText: (text) =>
      set((s) => {
        if (s.view === "home" || s.activeTabId === "tab-draft-new") {
          historyStore.writeDraftText(text);
        }
        return {
          problemText: text,
          workspaceTabs:
            s.activeTabId === "tab-draft-new" || s.view === "home"
              ? s.workspaceTabs.map((t) =>
                  t.id === "tab-draft-new" ? { ...t, draftText: text } : t,
                )
              : s.workspaceTabs,
        };
      }),
    // Hybrid /4 (main 6fc6b309): một lần phân tích MỚI thất bại không được để lại mô phỏng/bài giao/lựa chọn của bài
    // trước cạnh thông báo lỗi của bài khác. Giữ `clientFailure` và ngăn điều hướng của trải nghiệm lỗi Axo.
    setAnalyzing: (v) => set(v ? { analyzing: true, unsupported: null } : { analyzing: false }),
    setAnalysisError: (msg) =>
      set((s) => {
        if (msg === null) {
          return { analysisError: null, clientFailure: null };
        }
        if (/lượt mô phỏng thử/.test(msg)) {
          return { analysisError: msg, unsupported: null, clientFailure: s.clientFailure };
        }
        const activeInProgress = Object.values(s.problemProcessingRecords).find(
          (r) => r.status === "in_progress",
        );
        let nextRecords = s.problemProcessingRecords;
        if (activeInProgress) {
          const now = Date.now();
          nextRecords = {
            ...s.problemProcessingRecords,
            [activeInProgress.canonicalId]: {
              ...activeInProgress,
              status: "needs_attention",
              reasonCode: s.clientFailure?.code ?? "ANALYSIS_ERROR",
              reasonMessage: msg,
              interruptedByReload: false,
              failureKind: "PROBLEM_ERROR",
              analysisError: msg,
              clientFailure: s.clientFailure,
              updatedAt: now,
            },
          };
          persistProblemProcessingRecords(nextRecords);
        } else if (s.problemText.trim().length > 0) {
          const fallbackId = "attempt-error-latest";
          const now = Date.now();
          const prev = s.problemProcessingRecords[fallbackId];
          const meta = historyStore.getMeta(fallbackId);
          const stmt = s.problemText.trim();
          nextRecords = {
            ...s.problemProcessingRecords,
            [fallbackId]: {
              canonicalId: fallbackId,
              title: stripStatusPrefixesFromTitle(
                meta?.customTitle?.trim() ||
                  prev?.title?.trim() ||
                  deriveProblemAttemptTitle(stmt, "Bài toán cần chú ý"),
              ),
              problemStatement: stmt,
              status: "needs_attention",
              reasonCode: s.clientFailure?.code ?? "ANALYSIS_ERROR",
              reasonMessage: msg,
              interruptedByReload: false,
              failureKind: "PROBLEM_ERROR",
              analysisError: msg,
              clientFailure: s.clientFailure,
              createdAt: prev?.createdAt ?? now,
              updatedAt: now,
            },
          };
          persistProblemProcessingRecords(nextRecords);
        }
        return {
          analysisError: msg,
          clientFailure: s.clientFailure,
          problemProcessingRecords: nextRecords,
          unsupported: null,
          active: null,
          semanticFocus: null,
          activeHistoryId: null,
          activeSampleId: null,
          playing: false,
          view: "home",
          hasInAppNavigation: true,
          validRouteStack: pushSafeRoute(s.validRouteStack, "home"),
        };
      }),
    setClientFailure: (failure) => set({ clientFailure: failure }),
    reportNetworkFailure: (err) => {
      const contract: ClientFailureContract = {
        kind: err.kind,
        code: err.code,
        status: err.status,
        message: err.message,
      };
      set((s) => {
        const activeInProgress = Object.values(s.problemProcessingRecords).find(
          (r) => r.status === "in_progress",
        );
        let nextRecords = s.problemProcessingRecords;
        if (activeInProgress) {
          const now = Date.now();
          nextRecords = {
            ...s.problemProcessingRecords,
            [activeInProgress.canonicalId]: {
              ...activeInProgress,
              status: "needs_attention",
              reasonCode: contract.code,
              reasonMessage: contract.message,
              interruptedByReload: false,
              failureKind: "CONNECTION_INTERRUPTED",
              clientFailure: contract,
              analysisError: contract.message,
              updatedAt: now,
            },
          };
          persistProblemProcessingRecords(nextRecords);
        }
        return {
          clientFailure: contract,
          routeFailure: { kind: "network_failure" },
          problemProcessingRecords: nextRecords,
          analyzing: false,
          playing: false,
        };
      });
    },
    syncLocationRoute: (pathname, hash = "", search = "") => {
      const wasHydrated = hasHydratedLocation;
      hasHydratedLocation = true;
      if (!wasHydrated) {
        const curRecords = get().problemProcessingRecords;
        const hasInMemoryOrReloadRecords = Object.values(curRecords).some(
          (r) => r.status === "in_progress" || r.interruptedByReload === true,
        );
        if (hasInMemoryOrReloadRecords || Object.keys(curRecords).length === 0) {
          const persisted = recoverPersistedProblemProcessingRecords();
          if (hasInMemoryOrReloadRecords || Object.keys(persisted).length > 0) {
            get().hydrateProblemProcessingAfterReload();
          }
        }
      }
      const hadNav = get().hasInAppNavigation || wasHydrated;
      const normalizedPathname =
        pathname.length > 1 && pathname.endsWith("/")
          ? pathname.replace(/\/+$/, "")
          : pathname || "/";
      const decision = resolveLocationRoute(pathname, hash, search);
      if (
        normalizedPathname === "/history" ||
        normalizedPathname.startsWith("/history/") ||
        (decision.kind === "view" && decision.view === "history")
      ) {
        const canonicalTargetPath = useAuthStore.getState().user !== null ? "/" : "/app";
        set((s) => {
          const syncedTabs = syncCurrentTabInList(
            s.workspaceTabs,
            s.activeTabId,
            s.active,
            s.activeSampleId,
            s.activeHistoryId,
            s.problemText,
          );
          const nav = !hadNav
            ? { stack: [{ view: "home" as const, tabId: null }], index: 0 }
            : pushWorkspaceNav(
                s.workspaceNavStack,
                s.workspaceNavIndex,
                { view: "home", tabId: null },
                "home",
              );
          return {
            view: "home",
            guestEnteredApp: true,
            workspaceTabs: syncedTabs,
            routeFailure: null,
            unsupported: null,
            analysisError: null,
            clientFailure: null,
            hasInAppNavigation: hadNav,
            navHistoryMode: "replace",
            history: historyStore.list(),
            validRouteStack: pushSafeRoute(s.validRouteStack, "home"),
            workspaceNavStack: nav.stack,
            workspaceNavIndex: nav.index,
          };
        });
        if (typeof window !== "undefined" && typeof window.history?.replaceState === "function") {
          try {
            window.history.replaceState({ axoView: "home", sampleId: null }, "", canonicalTargetPath);
          } catch {
            /* bỏ qua nếu môi trường kiểm thử chặn replaceState */
          }
        }
        return;
      }
      if (decision.kind === "not_found") {
        set({
          view: "not_found",
          routeFailure: { kind: "not_found", requestedPath: decision.requestedPath },
          playing: false,
          hasInAppNavigation: hadNav,
        });
        return;
      }
      if (decision.kind === "sample") {
        const curState = get();
        const syncedExisting = syncCurrentTabInList(
          curState.workspaceTabs,
          curState.activeTabId,
          curState.active,
          curState.activeSampleId,
          curState.activeHistoryId,
          curState.problemText,
        );
        const existingTab = findMatchingOpenSimulationTab(syncedExisting, {
          tabId: `tab-sample-${decision.sampleId}`,
          sampleId: decision.sampleId,
        });
        if (existingTab && existingTab.active) {
          set((s) => {
            const prevIdx = s.workspaceNavIndex - 1;
            const nextIdx = s.workspaceNavIndex + 1;
            let matchedIndex = -1;
            if (prevIdx >= 0 && s.workspaceNavStack[prevIdx]?.view === "workspace" && s.workspaceNavStack[prevIdx]?.tabId === existingTab.id) {
              matchedIndex = prevIdx;
            } else if (nextIdx < s.workspaceNavStack.length && s.workspaceNavStack[nextIdx]?.view === "workspace" && s.workspaceNavStack[nextIdx]?.tabId === existingTab.id) {
              matchedIndex = nextIdx;
            }
            const nav =
              matchedIndex >= 0
                ? { stack: ensureSafeNavRoot(s.workspaceNavStack, s.returnView), index: matchedIndex }
                : pushWorkspaceNav(s.workspaceNavStack, s.workspaceNavIndex, {
                    view: "workspace",
                    tabId: existingTab.id,
                  }, s.returnView);
            return {
              view: "workspace",
              routeFailure: null,
              unsupported: null,
              analysisError: null,
              clientFailure: null,
              playing: false,
              workspaceTabs: syncedExisting,
              activeTabId: existingTab.id,
              active: existingTab.active,
              activeSampleId: existingTab.sampleId,
              activeHistoryId: existingTab.historyId,
              workspaceNavStack: nav.stack,
              workspaceNavIndex: nav.index,
              navHistoryMode: "replace",
              hasInAppNavigation: hadNav,
            };
          });
          persistWorkspaceSessionSnapshot(get());
          return;
        }
        const entry = publicCatalog().find((s) => s.id === decision.sampleId) ?? offlineCatalog().find((s) => s.id === decision.sampleId);
        if (entry) {
          set({ routeFailure: null });
          get().loadEnvelope(entry.envelope, entry.id);
          if (get().active === null && get().unsupported === null) {
            set({
              view: "workspace",
              routeFailure: { kind: "unsupported_simulation", requestedPath: pathname },
              hasInAppNavigation: hadNav,
            });
            return;
          }
          if (!hadNav) {
            const st = get();
            set({
              hasInAppNavigation: false,
              workspaceNavStack: [
                { view: "home", tabId: null },
                { view: st.view, tabId: st.activeTabId },
              ],
              workspaceNavIndex: 1,
              navHistoryMode: "replace",
            });
          }
          persistWorkspaceSessionSnapshot(get());
        }
        return;
      }
      if (decision.kind === "history_item") {
        const curState = get();
        const syncedExisting = syncCurrentTabInList(
          curState.workspaceTabs,
          curState.activeTabId,
          curState.active,
          curState.activeSampleId,
          curState.activeHistoryId,
          curState.problemText,
        );
        const histMatch = historyStore.list().find((x) => x.id === decision.historyId);
        const existingTab = findMatchingOpenSimulationTab(syncedExisting, {
          historyId: decision.historyId,
          title: histMatch?.title ?? null,
          originalInput: histMatch?.originalInput ?? null,
          problemStatement: histMatch?.envelope?.problem_statement ?? null,
          envelope: histMatch?.envelope ?? null,
        });
        if (existingTab && existingTab.active) {
          set((s) => {
            const prevIdx = s.workspaceNavIndex - 1;
            const nextIdx = s.workspaceNavIndex + 1;
            let matchedIndex = -1;
            if (prevIdx >= 0 && s.workspaceNavStack[prevIdx]?.view === "workspace" && s.workspaceNavStack[prevIdx]?.tabId === existingTab.id) {
              matchedIndex = prevIdx;
            } else if (nextIdx < s.workspaceNavStack.length && s.workspaceNavStack[nextIdx]?.view === "workspace" && s.workspaceNavStack[nextIdx]?.tabId === existingTab.id) {
              matchedIndex = nextIdx;
            }
            const nav =
              matchedIndex >= 0
                ? { stack: ensureSafeNavRoot(s.workspaceNavStack, s.returnView), index: matchedIndex }
                : pushWorkspaceNav(s.workspaceNavStack, s.workspaceNavIndex, {
                    view: "workspace",
                    tabId: existingTab.id,
                  }, s.returnView);
            return {
              view: "workspace",
              routeFailure: null,
              unsupported: null,
              analysisError: null,
              clientFailure: null,
              playing: false,
              workspaceTabs: syncedExisting,
              activeTabId: existingTab.id,
              active: existingTab.active,
              activeSampleId: existingTab.sampleId,
              activeHistoryId: existingTab.historyId,
              workspaceNavStack: nav.stack,
              workspaceNavIndex: nav.index,
              navHistoryMode: "replace",
              hasInAppNavigation: hadNav,
            };
          });
          persistWorkspaceSessionSnapshot(get());
          return;
        }
        set({ routeFailure: null });
        get().reopenFromHistory(decision.historyId);
        if (get().active === null) {
          set({
            view: "workspace",
            routeFailure: { kind: "unsupported_simulation", requestedPath: pathname },
            hasInAppNavigation: hadNav,
          });
          return;
        }
        if (!hadNav) {
          const st = get();
          set({
            hasInAppNavigation: false,
            workspaceNavStack: [
              { view: "home", tabId: null },
              { view: st.view, tabId: st.activeTabId },
            ],
            workspaceNavIndex: 1,
            navHistoryMode: "replace",
          });
        }
        persistWorkspaceSessionSnapshot(get());
        return;
      }
      if (decision.kind === "workspace_root") {
        const curState = get();
        if (curState.active !== null || curState.unsupported !== null || curState.workspaceTabs.length > 0) {
          const stateTabId =
            typeof window !== "undefined"
              ? ((window.history.state as { axoTabId?: string | null; tabId?: string | null } | null)?.axoTabId ??
                 (window.history.state as { axoTabId?: string | null; tabId?: string | null } | null)?.tabId ??
                 null)
              : null;
          const targetTab = stateTabId
            ? curState.workspaceTabs.find((t) => t.id === stateTabId)
            : null;
          if (targetTab) {
            if (targetTab.kind === "draft") {
              set({
                view: "workspace",
                activeTabId: targetTab.id,
                problemText: targetTab.draftText ?? curState.problemText,
                routeFailure: null,
                navHistoryMode: "replace",
                hasInAppNavigation: hadNav,
              });
            } else {
              set({
                view: "workspace",
                activeTabId: targetTab.id,
                active: targetTab.active ?? curState.active,
                activeSampleId: targetTab.sampleId,
                activeHistoryId: targetTab.historyId,
                routeFailure: null,
                navHistoryMode: "replace",
                hasInAppNavigation: hadNav,
              });
            }
          } else {
            set({ view: "workspace", routeFailure: null, navHistoryMode: "replace", hasInAppNavigation: hadNav });
          }
          persistWorkspaceSessionSnapshot(get());
        } else {
          set((s) => ({
            view: "home",
            routeFailure: null,
            hasInAppNavigation: hadNav,
            validRouteStack: pushSafeRoute(s.validRouteStack, "home"),
          }));
          if (typeof window !== "undefined" && typeof window.history?.replaceState === "function") {
            try {
              window.history.replaceState({ axoView: "home", sampleId: null }, "", "/");
            } catch {
              /* bỏ qua nếu môi trường kiểm thử chặn replaceState */
            }
          }
        }
        return;
      }
      const nextView = decision.view;
      set((s) => {
        const syncedTabs = syncCurrentTabInList(
          s.workspaceTabs,
          s.activeTabId,
          s.active,
          s.activeSampleId,
          s.activeHistoryId,
          s.problemText,
        );
        const navTabId = nextView === "library" ? LIBRARY_TAB_ID : null;
        let nav: { stack: WorkspaceNavEntry[]; index: number };
        if (!hadNav) {
          nav = { stack: [{ view: nextView, tabId: navTabId }], index: 0 };
        } else {
          const prevIdx = s.workspaceNavIndex - 1;
          const nextIdx = s.workspaceNavIndex + 1;
          if (prevIdx >= 0 && s.workspaceNavStack[prevIdx]?.view === nextView) {
            nav = { stack: ensureSafeNavRoot(s.workspaceNavStack, s.returnView), index: prevIdx };
          } else if (nextIdx < s.workspaceNavStack.length && s.workspaceNavStack[nextIdx]?.view === nextView) {
            nav = { stack: ensureSafeNavRoot(s.workspaceNavStack, s.returnView), index: nextIdx };
          } else {
            nav = pushWorkspaceNav(s.workspaceNavStack, s.workspaceNavIndex, { view: nextView, tabId: navTabId }, s.returnView);
          }
        }
        return {
          view: nextView,
          libraryTabOpen: nextView === "library" ? true : s.libraryTabOpen,
          guestEnteredApp: pathname === "/app" || pathname === "/home",
          workspaceTabs: syncedTabs,
          routeFailure: null,
          hasInAppNavigation: hadNav,
          navHistoryMode: "replace",
          history: nextView === "history" || nextView === "home" ? historyStore.list() : s.history,
          validRouteStack: pushSafeRoute(s.validRouteStack, nextView),
          workspaceNavStack: nav.stack,
          workspaceNavIndex: nav.index,
        };
      });
      persistWorkspaceSessionSnapshot(get());
    },
    escapeFromError: () => {
      const {
        view,
        returnView,
        validRouteStack,
        hasInAppNavigation,
        routeFailure,
        clientFailure,
        analysisError,
      } = get();
      let target: AppView = "home";
      let nextStack: AppView[] = ["home"];
      if (hasInAppNavigation) {
        const safeCandidates = validRouteStack.filter((v) => SAFE_ESCAPE_VIEWS.has(v));
        const hasOverlayOnSafeView =
          SAFE_ESCAPE_VIEWS.has(view)
          && (routeFailure !== null || clientFailure !== null || analysisError !== null);
        if (hasOverlayOnSafeView) {
          target = view;
          nextStack = safeCandidates.length > 0 ? safeCandidates : pushSafeRoute(["home"], target);
        } else if (view === "workspace" || view === "not_found") {
          target =
            safeCandidates[safeCandidates.length - 1] ??
            (SAFE_ESCAPE_VIEWS.has(returnView) ? returnView : "home");
          nextStack = safeCandidates.length > 0 ? safeCandidates : pushSafeRoute(["home"], target);
        } else if (safeCandidates.length > 1) {
          nextStack = safeCandidates.slice(0, -1);
          target = nextStack[nextStack.length - 1] ?? "home";
        } else {
          target = safeCandidates[0] ?? "home";
          nextStack = pushSafeRoute(["home"], target);
        }
      }
      set({
        view: target,
        active: null,
        activeHistoryId: null,
        unsupported: null,
        analysisError: null,
        clientFailure: null,
        routeFailure: null,
        activeSampleId: null,
        playing: false,
        validRouteStack: nextStack,
        history: historyStore.list(),
      });
      if (typeof window !== "undefined" && typeof window.history?.replaceState === "function") {
        try {
          window.history.replaceState(
            { axoView: target },
            "",
            canonicalPathForView(target, null),
          );
        } catch {
          /* môi trường sandbox không cho phép replaceState thì giữ state bộ nhớ */
        }
      }
      return target;
    },


    loadEnvelope: (envIn, sampleId, originalInput, recordId) => {
      // «Đề bài» = đề người học đã gửi, đóng dấu vào envelope để mọi lối mở lại (Lịch sử, Thư viện, bài giao) mang theo
      // (main 928fb880). Mở bài mẫu TƯỜNG MINH không bao giờ đóng dấu; envelope đã mang đề đóng dấu (vd bài giao) là
      // một lần gửi với đề ấy, không phải bài mẫu.
      const deGui = sampleId ? undefined : (originalInput?.trim() || envIn.problem_statement?.trim() || undefined);
      const env = deGui ? { ...envIn, problem_statement: deGui } : envIn;
      const mod = getSimulation(env.simulation_id);
      if (!mod) {
        set({
          active: null, semanticFocus: null, activeHistoryId: null, unsupported: null, playing: false, view: "home",
          analysisError: `Hệ thống chưa có mô phỏng "${env.simulation_id}".`,
          activeSampleId: null,
        });
        return;
      }
      let result: ConfigResult<unknown>;
      try {
        result = mod.validateEnvelope ? mod.validateEnvelope(env) : mod.validateConfig(env.config);
      } catch {
        result = { ok: false, error: "Dữ liệu không vượt qua kiểm tra an toàn. Hãy phân tích lại đề." };
      }
      if (!result.ok) {
        set({
          active: null, semanticFocus: null, activeHistoryId: null, unsupported: null, playing: false, view: "home",
          analysisError: `Cấu hình mô phỏng không hợp lệ: ${result.error}`,
          activeSampleId: null,
        });
        return;
      }
      // M13: lưới sau cùng — config qua được validateConfig (hai tầng, Task
      // 3/5) nhưng runtime vẫn có thể phát hiện không evaluate được (defense
      // in depth). Store MÙ DOMAIN: bắt Error BẤT KỲ từ mod.init, không
      // import kiểu lỗi domain generic. Ghi lịch sử PHẢI nằm SAU init thành
      // công — cảnh hỏng không được lên sân khấu, cũng không bị ghi lại.
      const statementInput = normalizeStatement(deGui);
      const resolvedSampleId = sampleId ?? null;
      const sampleStatement = sampleId ? GEOMETRY_SAMPLES.find((s) => s.id === sampleId)?.problemText : null;
      const savedEnvelope = sampleStatement ? { ...env, problem_statement: sampleStatement } : env;
      const legacyMatch =
        statementInput && !(sampleId ? false : Boolean(recordId))
          ? historyStore.list().find(
              (x) =>
                x.id === historyIdOf(savedEnvelope) &&
                normalizeStatement(x.originalInput) === statementInput &&
                sceneDigestOf(x.envelope) === sceneDigestOf(savedEnvelope),
            )
          : undefined;
      const expectedHistoryId = resolvedSampleId
        ? historyIdOf(savedEnvelope)
        : (recordId ??
            legacyMatch?.id ??
            (statementInput ? submissionIdOf(savedEnvelope, statementInput) : historyIdOf(savedEnvelope)));
      const curState = get();
      const { tabs: effectiveTabs } = resolveEffectiveWorkspaceTabs({
        workspaceTabs: curState.workspaceTabs,
        activeTabId: curState.activeTabId,
        active: curState.active,
        activeSampleId: curState.activeSampleId,
        activeHistoryId: curState.activeHistoryId,
      });
      const existingOpenTab = findMatchingOpenSimulationTab(effectiveTabs, {
        tabId: resolvedSampleId ? `tab-sample-${resolvedSampleId}` : undefined,
        sampleId: resolvedSampleId,
        historyId: expectedHistoryId,
        title: savedEnvelope.title ?? null,
        originalInput: statementInput,
        problemStatement: deGui ?? sampleStatement ?? savedEnvelope.problem_statement ?? null,
        envelope: savedEnvelope,
      });
      if (existingOpenTab && existingOpenTab.active) {
        hasHydratedWorkspaceSession = true;
        if (recordId) {
          set((s) => {
            if (!(recordId in s.problemProcessingRecords)) return {};
            const nextRecords = { ...s.problemProcessingRecords };
            delete nextRecords[recordId];
            persistProblemProcessingRecords(nextRecords);
            return { problemProcessingRecords: nextRecords };
          });
        }
        get().activateWorkspaceTab(existingOpenTab.id);
        return;
      }

      let initialState: unknown;
      try {
        initialState = mod.init(result.config);
      } catch {
        set({
          active: null, semanticFocus: null, activeHistoryId: null, unsupported: null, playing: false, view: "home",
          analysisError:
            "Mô phỏng này không còn mở được: cấu hình không vượt qua kiểm tra an toàn hiện hành. " +
            "Hãy phân tích lại đề để tạo mô phỏng mới.",
          activeSampleId: null,
        });
        return;
      }
      // M9-UX1: mô phỏng validate + khởi tạo thành công → ghi lịch sử bền.
      // Ngữ cảnh trình bày:
      //  - mở bài mẫu TƯỜNG MINH (`sampleId`) là mở bài mẫu: đề lấy từ danh mục, mọi đề kèm theo bị bỏ qua;
      //  - lần mở không kèm đề giữ trạng thái thiếu đề; chương trình trùng không chứng minh nguồn đề;
      //  - một lần gửi (có đề) trùng chương trình với bài mẫu vẫn là lần gửi: khoá bản ghi, URL, snapshot UI và đề
      //    là của chính nó (`historyStore.record` khoá theo `submissionIdOf`).
      // Mở bài mẫu tường minh không bao giờ ghi vào bản ghi lần học được truyền kèm.
      const item = historyStore.record(savedEnvelope, statementInput, sampleId ? undefined : recordId);
      if (useAuthStore.getState().user !== null) {
        const hasScene3d = Boolean((env as { scene3d?: unknown }).scene3d);
        const stepCount = hasScene3d ? 0 : (mod.timeline ? mod.timeline.stepCount(initialState) : 0);
        void upsertServerHistory(item, { sampleId: resolvedSampleId, stepCount });
      }
      const resolvedTitle = item.title?.trim() || env.title?.trim() || "Mô phỏng 3D";
      const activeEnv =
        resolvedTitle !== env.title ? { ...env, title: resolvedTitle } : env;
      const nextActive: ActiveSimulation = {
        moduleId: mod.id,
        envelope: activeEnv,
        config: result.config,
        state: initialState,
        problemStatement: deGui ?? null,
      };
      const prevView = get().view;
      const nextReturnView =
        prevView === "workspace" || prevView === "not_found" ? get().returnView : prevView;
      const safeReturnView: AppView = SAFE_ESCAPE_VIEWS.has(nextReturnView) ? nextReturnView : "home";
      const simTabId = resolvedSampleId
        ? `tab-sample-${resolvedSampleId}`
        : `tab-hist-${item.id}`;
      const tabTitle = resolvedTitle;
      const newSimTab: WorkspaceTabItem = {
        id: simTabId,
        problemId: resolvedSampleId ?? item.id,
        sessionId: item.id,
        kind: "simulation",
        title: tabTitle,
        active: nextActive,
        sampleId: resolvedSampleId,
        historyId: item.id,
      };
      hasHydratedWorkspaceSession = true;
      set((s) => {
        const baseTabs = syncCurrentTabInList(
          s.workspaceTabs,
          s.activeTabId,
          s.active,
          s.activeSampleId,
          s.activeHistoryId,
          s.problemText,
        );
        const isReplacingActiveDraft =
          s.view === "workspace" && s.activeTabId === "tab-draft-new";
        let nextTabs: WorkspaceTabItem[];
        if (baseTabs.some((t) => t.id === simTabId)) {
          nextTabs = (
            isReplacingActiveDraft
              ? baseTabs.filter((t) => t.id !== "tab-draft-new")
              : baseTabs
          ).map((t) => (t.id === simTabId ? newSimTab : t));
        } else if (isReplacingActiveDraft && baseTabs.some((t) => t.id === "tab-draft-new")) {
          nextTabs = baseTabs.map((t) => (t.id === "tab-draft-new" ? newSimTab : t));
        } else {
          nextTabs = [...baseTabs, newSimTab];
        }
        const cleanedStack = isReplacingActiveDraft
          ? s.workspaceNavStack.map((entry) =>
              entry.tabId === "tab-draft-new" ? { ...entry, tabId: simTabId } : entry,
            )
          : s.workspaceNavStack;
        const navBefore =
          s.view !== "workspace" && SAFE_ESCAPE_VIEWS.has(s.view)
            ? pushWorkspaceNav(
                cleanedStack,
                s.workspaceNavIndex,
                { view: s.view, tabId: s.view === "library" ? LIBRARY_TAB_ID : null },
                safeReturnView,
              )
            : { stack: ensureSafeNavRoot(cleanedStack, safeReturnView), index: s.workspaceNavIndex };
        const navNext = pushWorkspaceNav(navBefore.stack, navBefore.index, {
          view: "workspace",
          tabId: simTabId,
        }, safeReturnView);
        const nextRecords = { ...s.problemProcessingRecords };
        if (recordId) delete nextRecords[recordId];
        delete nextRecords[item.id];
        if (statementInput) {
          for (const [recKey, recVal] of Object.entries(nextRecords)) {
            if (
              recVal.status === "needs_attention" &&
              normalizeStatement(recVal.problemStatement) === statementInput
            ) {
              delete nextRecords[recKey];
            }
          }
        }
        persistProblemProcessingRecords(nextRecords);
        return {
          active: nextActive,
          workspaceTabs: nextTabs,
          activeTabId: simTabId,
          workspaceNavStack: navNext.stack,
          workspaceNavIndex: navNext.index,
          navHistoryMode: "push",
          problemProcessingRecords: nextRecords,
          unsupported: null,
          analysisError: null,
          clientFailure: null,
          routeFailure: null,
          activeSampleId: resolvedSampleId,
          playing: false,
          /* W4B-2Z: mô phỏng MỚI luôn mở ở chế độ Quan sát — cờ chế độ không được
             rò từ bài trước sang bài sau (với một phiên thì khó thấy, với nhiều
             phiên thì thành sai lệch đo được).
             W4B-3A — cùng lý do, cùng một dòng, nay chỉ còn một chế độ. */
          exploreOpen: false,
          // Chính sách M8: mô phỏng MỚI luôn mở ở 2D (mặc định); 3D là lựa chọn
          // của người dùng SAU đó, và chỉ khi module khai hỗ trợ.
          visualMode: "2d",
          view: "workspace",
          // Đổi bài ngay trong xưởng không phải "trang trước" — giữ đích quay lại cũ.
          returnView: safeReturnView,
          hasInAppNavigation: true,
          validRouteStack: pushSafeRoute(s.validRouteStack, safeReturnView),
          history: historyStore.list(),
          activeHistoryId: item.id,
        };
      });
      persistWorkspaceSessionSnapshot(get());
    },

    roiXuong: () => {
      const ve = SAFE_ESCAPE_VIEWS.has(get().returnView) ? get().returnView : "home";
      get().goHome();
      get().setView(ve);
    },

    /* W4B-2Z §26 — về Home KHÔNG đóng phiên nào: chụp bản làm việc lại trước
       khi rời đi, nếu không quay lại phiên sẽ mất chỗ đang dở. */
    goHome: () => {
      set((s) => {
        const syncedTabs = syncCurrentTabInList(
          s.workspaceTabs,
          s.activeTabId,
          s.active,
          s.activeSampleId,
          s.activeHistoryId,
          s.problemText,
        );
        const nav = pushWorkspaceNav(s.workspaceNavStack, s.workspaceNavIndex, {
          view: "home",
          tabId: null,
        }, "home");
        return {
          view: "home",
          active: null,
          workspaceTabs: syncedTabs,
          workspaceNavStack: nav.stack,
          workspaceNavIndex: nav.index,
          navHistoryMode: "push",
          activeHistoryId: null,
          unsupported: null,
          analysisError: null,
          clientFailure: null,
          routeFailure: null,
          activeSampleId: null,
          playing: false,
          hasInAppNavigation: true,
          validRouteStack: pushSafeRoute(s.validRouteStack, "home"),
          history: historyStore.list(),
        };
      });
      persistWorkspaceSessionSnapshot(get());
    },

    openHistory: () => {
      const canonicalTargetPath = useAuthStore.getState().user !== null ? "/" : "/app";
      set((s) => {
        const syncedTabs = syncCurrentTabInList(
          s.workspaceTabs,
          s.activeTabId,
          s.active,
          s.activeSampleId,
          s.activeHistoryId,
          s.problemText,
        );
        const nav = pushWorkspaceNav(
          s.workspaceNavStack,
          s.workspaceNavIndex,
          {
            view: "home",
            tabId: null,
          },
          "home",
        );
        return {
          view: "home",
          guestEnteredApp: true,
          workspaceTabs: syncedTabs,
          workspaceNavStack: nav.stack,
          workspaceNavIndex: nav.index,
          navHistoryMode: "replace",
          routeFailure: null,
          unsupported: null,
          analysisError: null,
          clientFailure: null,
          hasInAppNavigation: true,
          validRouteStack: pushSafeRoute(s.validRouteStack, "home"),
          history: historyStore.list(),
        };
      });
      persistWorkspaceSessionSnapshot(get());
      if (typeof window !== "undefined" && typeof window.history?.replaceState === "function") {
        try {
          window.history.replaceState({ axoView: "home", sampleId: null }, "", canonicalTargetPath);
        } catch {
          /* bỏ qua nếu môi trường kiểm thử chặn replaceState */
        }
      }
    },

    openLibrary: () => {
      hasHydratedWorkspaceSession = true;
      set((s) => {
        const syncedTabs = syncCurrentTabInList(
          s.workspaceTabs,
          s.activeTabId,
          s.active,
          s.activeSampleId,
          s.activeHistoryId,
          s.problemText,
        );
        const nav = pushWorkspaceNav(s.workspaceNavStack, s.workspaceNavIndex, {
          view: "library",
          tabId: LIBRARY_TAB_ID,
        }, "library");
        return {
          view: "library",
          libraryTabOpen: true,
          workspaceTabs: syncedTabs,
          workspaceNavStack: nav.stack,
          workspaceNavIndex: nav.index,
          navHistoryMode: "push",
          routeFailure: null,
          unsupported: null,
          analysisError: null,
          clientFailure: null,
          playing: false,
          hasInAppNavigation: true,
          validRouteStack: pushSafeRoute(s.validRouteStack, "library"),
        };
      });
      persistWorkspaceSessionSnapshot(get());
    },

    setLibraryUiState: (patch) => {
      set((s) => {
        const next: LibraryUiState = {
          search: patch.search !== undefined ? patch.search : s.libraryUiState.search,
          category: patch.category !== undefined ? patch.category : s.libraryUiState.category,
          scrollTop:
            patch.scrollTop !== undefined
              ? Math.max(0, Number(patch.scrollTop) || 0)
              : s.libraryUiState.scrollTop,
        };
        if (
          next.search === s.libraryUiState.search &&
          next.category === s.libraryUiState.category &&
          next.scrollTop === s.libraryUiState.scrollTop
        ) {
          return s;
        }
        return { libraryUiState: next };
      });
      persistWorkspaceSessionSnapshot(get());
    },

    openLanding: () =>
      set((s) => {
        const syncedTabs = syncCurrentTabInList(
          s.workspaceTabs,
          s.activeTabId,
          s.active,
          s.activeSampleId,
          s.activeHistoryId,
          s.problemText,
        );
        const nav = pushWorkspaceNav(
          s.workspaceNavStack,
          s.workspaceNavIndex,
          {
            view: "landing",
            tabId: null,
          },
          "landing",
        );
        return {
          view: "landing",
          workspaceTabs: syncedTabs,
          workspaceNavStack: nav.stack,
          workspaceNavIndex: nav.index,
          navHistoryMode: "push",
          routeFailure: null,
          playing: false,
          hasInAppNavigation: true,
          validRouteStack: pushSafeRoute(s.validRouteStack, "landing"),
        };
      }),

    /* M18 — điều hướng mức ứng dụng. Đổi mặt trình bày KHÔNG đụng `active`:
       rời sang "Lớp của em" rồi quay lại phải thấy đúng mô phỏng đang dở. */
    setView: (view) => {
      if (view === "library") {
        get().openLibrary();
        return;
      }
      set((s) => {
        const syncedTabs = syncCurrentTabInList(
          s.workspaceTabs,
          s.activeTabId,
          s.active,
          s.activeSampleId,
          s.activeHistoryId,
          s.problemText,
        );
        const nav =
          view === "not_found"
            ? { stack: s.workspaceNavStack, index: s.workspaceNavIndex }
            : pushWorkspaceNav(s.workspaceNavStack, s.workspaceNavIndex, {
                view,
                tabId: view === "workspace" ? s.activeTabId : null,
              }, SAFE_ESCAPE_VIEWS.has(view) ? view : s.returnView);
        return {
          view,
          workspaceTabs: syncedTabs,
          workspaceNavStack: nav.stack,
          workspaceNavIndex: nav.index,
          navHistoryMode: "push",
          routeFailure: view === "not_found" ? s.routeFailure : null,
          hasInAppNavigation: view === "not_found" ? s.hasInAppNavigation : true,
          validRouteStack: pushSafeRoute(s.validRouteStack, view),
          ...(view === "history" || view === "home" ? { history: historyStore.list() } : {}),
        };
      });
      persistWorkspaceSessionSnapshot(get());
    },
    setSemanticFocus: (f) => set({ semanticFocus: f }),

    reopenFromHistory: (id) => {
      const item = historyStore.list().find((x) => x.id === id);
      if (!item) return;
      const savedCursor = item.lastCursor;
      // History opens its own saved statement; matching catalog geometry cannot recover missing original wording.
      // Bản ghi là bài mẫu chỉ khi CHÍNH nó mang bằng chứng: không có đề người học, khoá biên dịch của bài mẫu và dấu
      // `problem_statement` mà lần mở bài mẫu tường minh đã ghi (`loadEnvelope`). Bản ghi cũ không dấu vẫn là "thiếu đề".
      const sampleId = item.originalInput
        ? undefined
        : GEOMETRY_SAMPLES.find((s) => historyIdOf(s.envelope) === item.id
          && s.problemText === item.envelope.problem_statement)?.id;
      const curState = get();
      const { tabs: effectiveTabs } = resolveEffectiveWorkspaceTabs({
        workspaceTabs: curState.workspaceTabs,
        activeTabId: curState.activeTabId,
        active: curState.active,
        activeSampleId: curState.activeSampleId,
        activeHistoryId: curState.activeHistoryId,
      });
      const existingTab = findMatchingOpenSimulationTab(effectiveTabs, {
        tabId: sampleId ? `tab-sample-${sampleId}` : `tab-hist-${item.id}`,
        sampleId: sampleId ?? null,
        historyId: item.id,
        title: item.title,
        originalInput: item.originalInput,
        problemStatement: item.envelope.problem_statement ?? null,
        envelope: item.envelope,
      });
      if (existingTab && existingTab.active) {
        const mod = getSimulation(item.envelope.simulation_id);
        let validatedOk = Boolean(mod);
        if (mod) {
          try {
            const check = mod.validateEnvelope
              ? mod.validateEnvelope(item.envelope)
              : mod.validateConfig(item.envelope.config);
            validatedOk = check.ok;
          } catch {
            validatedOk = false;
          }
        }
        if (validatedOk) {
          hasHydratedWorkspaceSession = true;
          get().activateWorkspaceTab(existingTab.id);
          if (item.visualMode && get().visualMode !== item.visualMode) {
            get().setVisualMode(item.visualMode);
          }
          return;
        }
      }
      // Envelope đã validate + engine tất định → 0 gọi AI, không đi pipeline.
      // Mở lại = cùng lần học: truyền chính ID bản ghi để không bị khoá lại theo nội dung (giữ ID qua reload/Back/Forward).
      // Bài mẫu được khoá bằng `historyIdOf`, chính là `item.id` theo điều kiện trên.
      get().loadEnvelope(item.envelope, sampleId, item.originalInput ?? undefined, item.id);
      if (get().active) {
        if (savedCursor !== null) {
          get().goToStep(savedCursor);
          // Cảnh 3D có số bước dựng nhiều hơn `view_steps` 2D: giữ nguyên `savedCursor` trong `historyStore`
          // để `AxoWorkspaceV62` khôi phục đúng bước dựng 3D mà không bị timeline 2D kẹp cụt.
          const hasScene3d = Boolean(
            (item.envelope as { scene3d?: unknown }).scene3d ||
            (recoverCatalogScene3D(item.envelope) as { scene3d?: unknown })?.scene3d,
          );
          if (hasScene3d) {
            historyStore.touch(item.id, { lastCursor: savedCursor });
            set({ history: historyStore.list() });
          }
        }
        if (item.visualMode) get().setVisualMode(item.visualMode);
      }
    },

    removeHistoryItem: (id) => {
      historyStore.remove(id);
      set((s) => {
        const nextRecords = { ...s.problemProcessingRecords };
        delete nextRecords[id];
        persistProblemProcessingRecords(nextRecords);
        return {
          history: historyStore.list(),
          problemProcessingRecords: nextRecords,
        };
      });
      if (useAuthStore.getState().user !== null) {
        void deleteServerHistoryItem(id);
      }
    },

    clearHistory: () => {
      historyStore.clear();
      set({ history: [], problemProcessingRecords: {} });
      if (useAuthStore.getState().user !== null) {
        void clearServerHistory();
      }
    },

    loadUnsupported: (u, attemptId, statement) =>
      set((s) => {
        const activeInProgress = Object.values(s.problemProcessingRecords).find(
          (r) => r.status === "in_progress",
        );
        const targetId =
          attemptId ?? activeInProgress?.canonicalId ?? "attempt-unsupported-latest";
        const prev = s.problemProcessingRecords[targetId];
        const meta = historyStore.getMeta(targetId);
        const stmt = (
          statement ??
          prev?.problemStatement ??
          s.problemText ??
          ""
        ).trim();
        const now = Date.now();
        const resolvedTitle = stripStatusPrefixesFromTitle(
          meta?.customTitle?.trim() ||
            prev?.title?.trim() ||
            deriveProblemAttemptTitle(stmt, "Bài toán cần chú ý"),
        );
        const nextRecords: Record<string, ProblemProcessingRecord> = {
          ...s.problemProcessingRecords,
          [targetId]: {
            canonicalId: targetId,
            title: resolvedTitle,
            problemStatement: stmt,
            status: "needs_attention",
            reasonCode: u.error_code ?? u.failure_category ?? "UNSUPPORTED",
            reasonMessage: u.reason ?? null,
            interruptedByReload: false,
            failureKind: "PROBLEM_ERROR",
            unsupported: u,
            clientFailure: null,
            analysisError: null,
            createdAt: prev?.createdAt ?? now,
            updatedAt: now,
          },
        };
        persistProblemProcessingRecords(nextRecords);
        return {
          view: "home",
          active: null,
          semanticFocus: null,
          activeHistoryId: null,
          unsupported: u,
          analysisError: null,
          activeSampleId: null,
          playing: false,
          problemProcessingRecords: nextRecords,
          hasInAppNavigation: true,
          validRouteStack: pushSafeRoute(s.validRouteStack, "home"),
        };
      }),

    clearUnsupported: () => set({ unsupported: null }),

    dispatch: (action) => {
      const { active } = get();
      if (!active) return;
      const mod = getSimulation(active.moduleId);
      if (!mod) return;
      const next = mod.apply(active.state, action);
      if (next !== active.state) set({ active: { ...active, state: next } });
    },

    goToStep: (step) => withTimeline((tl, s) => tl.goToStep(s, step)),

    nextStep: () =>
      withTimeline((tl, s) => {
        const cur = tl.currentStep(s);
        if (cur >= tl.stepCount(s) - 1) {
          set({ playing: false });
          return s;
        }
        return tl.goToStep(s, cur + 1);
      }),

    prevStep: () => {
      set({ playing: false });
      withTimeline((tl, s) => tl.goToStep(s, tl.currentStep(s) - 1));
    },

    toStart: () => {
      set({ playing: false });
      withTimeline((tl, s) => tl.goToStep(s, 0));
    },

    toEnd: () => {
      set({ playing: false });
      withTimeline((tl, s) => tl.goToStep(s, tl.stepCount(s) - 1));
    },

    resetSim: () => {
      const { active } = get();
      if (!active) return;
      const mod = getSimulation(active.moduleId);
      if (!mod) return;
      // Đặt lại = về Quan sát: Khám phá là chế độ học sinh chủ động vào, nên
      // dựng lại mô hình thì nó đóng theo.
      set({
        active: { ...active, state: mod.init(active.config) },
        playing: false, exploreOpen: false,
      });
    },

    replaceSimulation: (config, state) => {
      const { active } = get();
      if (!active) return;
      set({
        active: {
          ...active,
          config,
          state,
          envelope: { ...active.envelope, config },
        },
        playing: false,
      });
    },

    setPlaying: (v) => set({ playing: v }),
    setSpeedMs: (ms) => set({ speedMs: ms }),
    toggleRight: () => set({ rightOpen: !get().rightOpen }),
    setAiOpen: (v) => set({ aiOpen: v }),
    setExploreOpen: (v) => set({ exploreOpen: v }),

    accountModalOpen: false,
    accountModalTab: "profile",
    openAccountModal: (tab = "profile") =>
      set({ accountModalOpen: true, accountModalTab: tab }),
    closeAccountModal: () => set({ accountModalOpen: false }),
    authResetEmail: "",
    setAuthResetEmail: (email) => set({ authResetEmail: email }),

    // M8: CHỈ đổi trường trình bày. Không đụng active (engine state/cursor giữ
    // nguyên khối), không rebuild, không gọi mạng.
    setVisualMode: (mode) => {
      set({ visualMode: mode });
      // M9-UX1: visual mode là tiến độ trình bày an toàn → ghi vào lịch sử.
      const id = get().activeHistoryId;
      if (id) {
        historyStore.touch(id, { visualMode: mode });
        if (useAuthStore.getState().user !== null) {
          void touchServerHistory(id, { visualMode: mode });
        }
      }
    },

    openDraftWorkspaceTab: () => {
      hasHydratedWorkspaceSession = true;
      set((s) => {
        const baseTabs = syncCurrentTabInList(
          s.workspaceTabs,
          s.activeTabId,
          s.active,
          s.activeSampleId,
          s.activeHistoryId,
          s.problemText,
        );
        const draftId = "tab-draft-new";
        const existingDraft = baseTabs.find((t) => t.id === draftId);
        const savedDraft = historyStore.readDraftText();
        const candidateText =
          s.active?.problemStatement &&
          s.problemText.trim() === s.active.problemStatement.trim()
            ? ""
            : s.problemText;
        const initialDraftText =
          candidateText.trim().length > 0 ? candidateText : savedDraft;
        const nextTabs: WorkspaceTabItem[] = existingDraft
          ? baseTabs
          : [
              ...baseTabs,
              {
                id: draftId,
                problemId: null,
                sessionId: draftId,
                kind: "draft",
                title: "Bài toán mới",
                active: null,
                sampleId: null,
                historyId: null,
                draftText: initialDraftText,
              },
            ];
        const nav = pushWorkspaceNav(s.workspaceNavStack, s.workspaceNavIndex, {
          view: "workspace",
          tabId: draftId,
        }, s.returnView);
        return {
          view: "workspace",
          workspaceTabs: nextTabs,
          activeTabId: draftId,
          workspaceNavStack: nav.stack,
          workspaceNavIndex: nav.index,
          navHistoryMode: "push",
          problemText: existingDraft ? (existingDraft.draftText ?? "") : initialDraftText,
          analysisError: null,
          clientFailure: null,
          unsupported: null,
          playing: false,
          hasInAppNavigation: true,
          history: historyStore.list(),
        };
      });
      persistWorkspaceSessionSnapshot(get());
    },

    activateWorkspaceTab: (tabId) => {
      if (tabId === LIBRARY_TAB_ID) {
        get().openLibrary();
        return;
      }
      hasHydratedWorkspaceSession = true;
      set((s) => {
        const baseTabs = syncCurrentTabInList(
          s.workspaceTabs,
          s.activeTabId,
          s.active,
          s.activeSampleId,
          s.activeHistoryId,
          s.problemText,
        );
        const target = baseTabs.find((t) => t.id === tabId);
        if (!target) return {};
        const nav = pushWorkspaceNav(s.workspaceNavStack, s.workspaceNavIndex, {
          view: "workspace",
          tabId: target.id,
        }, s.returnView);
        if (target.kind === "draft") {
          return {
            view: "workspace",
            workspaceTabs: baseTabs,
            activeTabId: target.id,
            workspaceNavStack: nav.stack,
            workspaceNavIndex: nav.index,
            navHistoryMode: "push",
            problemText: target.draftText ?? "",
            unsupported: null,
            analysisError: null,
            clientFailure: null,
            playing: false,
            hasInAppNavigation: true,
          };
        }
        return {
          view: "workspace",
          workspaceTabs: baseTabs,
          activeTabId: target.id,
          workspaceNavStack: nav.stack,
          workspaceNavIndex: nav.index,
          navHistoryMode: "push",
          active: target.active ?? s.active,
          activeSampleId: target.sampleId,
          activeHistoryId: target.historyId,
          unsupported: null,
          analysisError: null,
          clientFailure: null,
          playing: false,
          hasInAppNavigation: true,
        };
      });
      persistWorkspaceSessionSnapshot(get());
    },

    closeWorkspaceTab: (tabId) => {
      if (tabId === LIBRARY_TAB_ID) {
        let didClose = false;
        set((s) => {
          if (!s.libraryTabOpen && s.view !== "library") return {};
          didClose = true;
          const baseTabs = syncCurrentTabInList(
            s.workspaceTabs,
            s.activeTabId,
            s.active,
            s.activeSampleId,
            s.activeHistoryId,
            s.problemText,
          );
          const cleanedStack = s.workspaceNavStack.filter((entry) => entry.view !== "library");
          const safeReturnView: AppView = s.returnView === "library" ? "home" : s.returnView;

          if (s.view === "workspace" && baseTabs.length > 0) {
            const preservedStack = ensureSafeNavRoot(cleanedStack, safeReturnView);
            return {
              libraryTabOpen: false,
              libraryUiState: { ...DEFAULT_LIBRARY_UI_STATE },
              returnView: safeReturnView,
              workspaceTabs: baseTabs,
              workspaceNavStack: preservedStack,
              workspaceNavIndex: Math.min(s.workspaceNavIndex, preservedStack.length - 1),
            };
          }

          if (baseTabs.length === 0) {
            const savedDraft = historyStore.readDraftText();
            const preservedProblemText =
              s.active?.problemStatement &&
              s.problemText.trim() === s.active.problemStatement.trim()
                ? savedDraft
                : s.problemText.trim().length > 0
                  ? s.problemText
                  : savedDraft;
            return {
              view: "home",
              libraryTabOpen: false,
              libraryUiState: { ...DEFAULT_LIBRARY_UI_STATE },
              returnView: "home",
              workspaceTabs: [],
              activeTabId: null,
              active: null,
              activeSampleId: null,
              activeHistoryId: null,
              unsupported: null,
              analysisError: null,
              clientFailure: null,
              routeFailure: null,
              playing: false,
              problemText: preservedProblemText,
              hasInAppNavigation: true,
              navHistoryMode: "replace",
              validRouteStack: pushSafeRoute(s.validRouteStack, "home"),
              workspaceNavStack: [{ view: "home", tabId: null }],
              workspaceNavIndex: 0,
              history: historyStore.list(),
            };
          }

          const nextTab =
            (s.activeTabId ? baseTabs.find((t) => t.id === s.activeTabId) : undefined) ??
            baseTabs[baseTabs.length - 1];
          const ensured = ensureSafeNavRoot(cleanedStack, safeReturnView);
          const navAfter = pushWorkspaceNav(
            ensured,
            ensured.length - 1,
            { view: "workspace", tabId: nextTab.id },
            safeReturnView,
          );

          if (nextTab.kind === "draft") {
            return {
              view: "workspace",
              libraryTabOpen: false,
              libraryUiState: { ...DEFAULT_LIBRARY_UI_STATE },
              returnView: safeReturnView,
              workspaceTabs: baseTabs,
              activeTabId: nextTab.id,
              problemText: nextTab.draftText ?? "",
              workspaceNavStack: navAfter.stack,
              workspaceNavIndex: navAfter.index,
              navHistoryMode: "replace",
              unsupported: null,
              analysisError: null,
              clientFailure: null,
              routeFailure: null,
              playing: false,
              hasInAppNavigation: true,
            };
          }

          return {
            view: "workspace",
            libraryTabOpen: false,
            libraryUiState: { ...DEFAULT_LIBRARY_UI_STATE },
            returnView: safeReturnView,
            workspaceTabs: baseTabs,
            activeTabId: nextTab.id,
            active: nextTab.active ?? s.active,
            activeSampleId: nextTab.sampleId,
            activeHistoryId: nextTab.historyId,
            workspaceNavStack: navAfter.stack,
            workspaceNavIndex: navAfter.index,
            navHistoryMode: "replace",
            unsupported: null,
            analysisError: null,
            clientFailure: null,
            routeFailure: null,
            playing: false,
            hasInAppNavigation: true,
          };
        });
        if (didClose) {
          persistWorkspaceSessionSnapshot(get());
        }
        return;
      }

      set((s) => {
        const baseTabs = syncCurrentTabInList(
          s.workspaceTabs,
          s.activeTabId,
          s.active,
          s.activeSampleId,
          s.activeHistoryId,
          s.problemText,
        );
        const closedIdx = baseTabs.findIndex((t) => t.id === tabId);
        if (closedIdx === -1) return {};
        const closedTab = baseTabs[closedIdx]!;
        const remainingTabs = baseTabs.filter((t) => t.id !== tabId);
        const prunedNav = pruneTabFromNavStack(
          s.workspaceNavStack,
          s.workspaceNavIndex,
          tabId,
          s.returnView,
        );
        const currentEffectiveActiveTabId = s.activeTabId ?? baseTabs[0]?.id ?? null;
        let preservedDraft = "";
        if (tabId === "tab-draft-new") {
          const rawDraft =
            tabId === currentEffectiveActiveTabId
              ? s.problemText
              : (closedTab.draftText ?? s.problemText);
          preservedDraft = rawDraft.trim().length > 0 ? rawDraft : "";
          historyStore.writeDraftText(preservedDraft);
        }

        if (remainingTabs.length === 0) {
          const fallbackView: AppView = s.libraryTabOpen ? "library" : "home";
          const savedDraft = historyStore.readDraftText();
          const remainingProblemText =
            tabId === "tab-draft-new"
              ? preservedDraft
              : closedTab.active?.problemStatement &&
                  s.problemText.trim() === closedTab.active.problemStatement.trim()
                ? savedDraft
                : s.problemText.trim().length > 0
                  ? s.problemText
                  : savedDraft;
          return {
            view: fallbackView,
            workspaceTabs: [],
            activeTabId: null,
            active: null,
            activeSampleId: null,
            activeHistoryId: null,
            unsupported: null,
            analysisError: null,
            clientFailure: null,
            routeFailure: null,
            playing: false,
            problemText: remainingProblemText,
            hasInAppNavigation: true,
            navHistoryMode: "replace",
            validRouteStack: pushSafeRoute(s.validRouteStack, fallbackView),
            workspaceNavStack: [{ view: fallbackView, tabId: fallbackView === "library" ? LIBRARY_TAB_ID : null }],
            workspaceNavIndex: 0,
            history: historyStore.list(),
          };
        }

        if (s.view === "library") {
          const nextIdx = Math.min(closedIdx, remainingTabs.length - 1);
          const nextTab = remainingTabs[nextIdx];
          return {
            workspaceTabs: remainingTabs,
            ...(tabId === currentEffectiveActiveTabId
              ? {
                  activeTabId: nextTab.id,
                  ...(nextTab.kind === "simulation"
                    ? {
                        active: nextTab.active ?? s.active,
                        activeSampleId: nextTab.sampleId,
                        activeHistoryId: nextTab.historyId,
                      }
                    : {}),
                }
              : {}),
            workspaceNavStack: prunedNav.stack,
            workspaceNavIndex: prunedNav.index,
            ...(tabId === "tab-draft-new" ? { problemText: preservedDraft } : {}),
          };
        }

        if (tabId !== currentEffectiveActiveTabId) {
          return {
            workspaceTabs: remainingTabs,
            workspaceNavStack: prunedNav.stack,
            workspaceNavIndex: prunedNav.index,
            ...(tabId === "tab-draft-new" ? { problemText: preservedDraft } : {}),
          };
        }

        const nextTabIdx = Math.min(closedIdx, remainingTabs.length - 1);
        const nextTab = remainingTabs[nextTabIdx];
        const topEntry = prunedNav.stack[prunedNav.index];
        const navAfter =
          topEntry && topEntry.view === "workspace" && topEntry.tabId === nextTab.id
            ? prunedNav
            : pushWorkspaceNav(
                prunedNav.stack,
                prunedNav.index,
                { view: "workspace", tabId: nextTab.id },
                s.returnView,
              );

        if (nextTab.kind === "draft") {
          return {
            view: "workspace",
            workspaceTabs: remainingTabs,
            activeTabId: nextTab.id,
            problemText: nextTab.draftText ?? "",
            workspaceNavStack: navAfter.stack,
            workspaceNavIndex: navAfter.index,
            navHistoryMode: "replace",
            unsupported: null,
            analysisError: null,
            clientFailure: null,
            playing: false,
            hasInAppNavigation: true,
          };
        }

        return {
          view: "workspace",
          workspaceTabs: remainingTabs,
          activeTabId: nextTab.id,
          active: nextTab.active ?? s.active,
          activeSampleId: nextTab.sampleId,
          activeHistoryId: nextTab.historyId,
          ...(tabId === "tab-draft-new" ? { problemText: preservedDraft } : {}),
          workspaceNavStack: navAfter.stack,
          workspaceNavIndex: navAfter.index,
          navHistoryMode: "replace",
          unsupported: null,
          analysisError: null,
          clientFailure: null,
          playing: false,
          hasInAppNavigation: true,
        };
      });
      persistWorkspaceSessionSnapshot(get());
    },

    workspaceGoBack: () => {
      set((s) => {
        const baseTabs = syncCurrentTabInList(
          s.workspaceTabs,
          s.activeTabId,
          s.active,
          s.activeSampleId,
          s.activeHistoryId,
          s.problemText,
        );
        if (s.workspaceNavIndex <= 0) {
          if (s.view === "workspace") {
            const safeRoot: AppView = SAFE_ESCAPE_VIEWS.has(s.returnView) ? s.returnView : "home";
            const ensuredStack = ensureSafeNavRoot(s.workspaceNavStack, safeRoot);
            return {
              view: safeRoot,
              libraryTabOpen: safeRoot === "library" ? true : s.libraryTabOpen,
              workspaceTabs: baseTabs,
              workspaceNavStack: ensuredStack,
              workspaceNavIndex: 0,
              navHistoryMode: "replace",
              routeFailure: null,
              playing: false,
              hasInAppNavigation: true,
              validRouteStack: pushSafeRoute(s.validRouteStack, safeRoot),
              ...(safeRoot === "history" || safeRoot === "home"
                ? { history: historyStore.list() }
                : {}),
            };
          }
          return {};
        }
        const nextIdx = s.workspaceNavIndex - 1;
        const entry = s.workspaceNavStack[nextIdx];
        if (!entry) return {};
        if (entry.view === "workspace") {
          const target =
            (entry.tabId ? baseTabs.find((t) => t.id === entry.tabId) : undefined) ??
            baseTabs[0];
          if (!target) {
            return {
              view: "home",
              workspaceTabs: baseTabs,
              workspaceNavIndex: 0,
              navHistoryMode: "replace",
              playing: false,
              hasInAppNavigation: true,
              history: historyStore.list(),
            };
          }
          if (target.kind === "draft") {
            return {
              view: "workspace",
              workspaceTabs: baseTabs,
              activeTabId: target.id,
              problemText: target.draftText ?? "",
              workspaceNavIndex: nextIdx,
              navHistoryMode: "replace",
              unsupported: null,
              playing: false,
              hasInAppNavigation: true,
            };
          }
          return {
            view: "workspace",
            workspaceTabs: baseTabs,
            activeTabId: target.id,
            workspaceNavIndex: nextIdx,
            navHistoryMode: "replace",
            active: target.active ?? s.active,
            activeSampleId: target.sampleId,
            activeHistoryId: target.historyId,
            unsupported: null,
            playing: false,
            hasInAppNavigation: true,
          };
        }
        return {
          view: entry.view,
          libraryTabOpen: entry.view === "library" ? true : s.libraryTabOpen,
          workspaceTabs: baseTabs,
          workspaceNavIndex: nextIdx,
          navHistoryMode: "replace",
          routeFailure: null,
          playing: false,
          hasInAppNavigation: true,
          validRouteStack: pushSafeRoute(s.validRouteStack, entry.view),
          ...(entry.view === "history" || entry.view === "home"
            ? { history: historyStore.list() }
            : {}),
        };
      });
      persistWorkspaceSessionSnapshot(get());
    },

    workspaceGoForward: () => {
      set((s) => {
        if (s.workspaceNavIndex >= s.workspaceNavStack.length - 1) return {};
        const nextIdx = s.workspaceNavIndex + 1;
        const entry = s.workspaceNavStack[nextIdx];
        if (!entry) return {};
        const baseTabs = syncCurrentTabInList(
          s.workspaceTabs,
          s.activeTabId,
          s.active,
          s.activeSampleId,
          s.activeHistoryId,
          s.problemText,
        );
        if (entry.view === "workspace") {
          const target =
            (entry.tabId ? baseTabs.find((t) => t.id === entry.tabId) : undefined) ??
            baseTabs[baseTabs.length - 1];
          if (!target) return { workspaceNavIndex: nextIdx };
          if (target.kind === "draft") {
            return {
              view: "workspace",
              workspaceTabs: baseTabs,
              activeTabId: target.id,
              problemText: target.draftText ?? "",
              workspaceNavIndex: nextIdx,
              navHistoryMode: "replace",
              unsupported: null,
              playing: false,
              hasInAppNavigation: true,
            };
          }
          return {
            view: "workspace",
            workspaceTabs: baseTabs,
            activeTabId: target.id,
            workspaceNavIndex: nextIdx,
            navHistoryMode: "replace",
            active: target.active ?? s.active,
            activeSampleId: target.sampleId,
            activeHistoryId: target.historyId,
            unsupported: null,
            playing: false,
            hasInAppNavigation: true,
          };
        }
        return {
          view: entry.view,
          libraryTabOpen: entry.view === "library" ? true : s.libraryTabOpen,
          workspaceTabs: baseTabs,
          workspaceNavIndex: nextIdx,
          navHistoryMode: "replace",
          routeFailure: null,
          playing: false,
          hasInAppNavigation: true,
          validRouteStack: pushSafeRoute(s.validRouteStack, entry.view),
          ...(entry.view === "history" || entry.view === "home"
            ? { history: historyStore.list() }
            : {}),
        };
      });
      persistWorkspaceSessionSnapshot(get());
    },

    hydrateWorkspaceSession: (opts) => {
      if (hasHydratedWorkspaceSession && !opts?.force) return;
      hasHydratedWorkspaceSession = true;
      const snapshot = readWorkspaceSessionSnapshot();
      if (!snapshot) return;

      const cur = get();
      const baseTabs = syncCurrentTabInList(
        cur.workspaceTabs,
        cur.activeTabId,
        cur.active,
        cur.activeSampleId,
        cur.activeHistoryId,
        cur.problemText,
      );
      const nextTabs: WorkspaceTabItem[] = [...baseTabs];
      const seenKeys = new Set<string>(nextTabs.map((t) => getWorkspaceTabResourceKey(t)));
      const historyItems = historyStore.list();

      for (const entry of snapshot.tabs) {
        if (entry.kind === "draft") {
          if (seenKeys.has(DRAFT_RESOURCE_KEY)) continue;
          seenKeys.add(DRAFT_RESOURCE_KEY);
          nextTabs.push({
            id: DRAFT_TAB_ID,
            problemId: null,
            sessionId: DRAFT_TAB_ID,
            kind: "draft",
            title: entry.title || "Bài toán mới",
            active: null,
            sampleId: null,
            historyId: null,
            draftText: entry.draftText ?? "",
          });
          continue;
        }

        const histItem = entry.historyId
          ? historyItems.find((x) => x.id === entry.historyId)
          : undefined;
        const catalogEntry = entry.sampleId
          ? (publicCatalog().find((s) => s.id === entry.sampleId) ??
             offlineCatalog().find((s) => s.id === entry.sampleId))
          : undefined;
        const rawEnv = histItem?.envelope ?? catalogEntry?.envelope ?? null;
        if (!rawEnv) continue;

        const inferredSampleId =
          entry.sampleId ??
          (histItem && !histItem.originalInput
            ? GEOMETRY_SAMPLES.find(
                (s) =>
                  historyIdOf(s.envelope) === histItem.id &&
                  s.problemText === histItem.envelope.problem_statement,
              )?.id ?? null
            : null);

        const existingMatch = findMatchingOpenSimulationTab(nextTabs, {
          tabId: entry.id,
          sampleId: inferredSampleId,
          historyId: histItem?.id ?? entry.historyId,
          title: histItem?.title ?? entry.title,
          originalInput: histItem?.originalInput ?? null,
          problemStatement: rawEnv.problem_statement ?? null,
          envelope: rawEnv,
        });
        if (existingMatch) continue;

        const deGui = inferredSampleId
          ? undefined
          : (histItem?.originalInput?.trim() || rawEnv.problem_statement?.trim() || undefined);
        const envWithStatement = deGui ? { ...rawEnv, problem_statement: deGui } : rawEnv;
        const env = inferredSampleId || !histItem?.originalInput
          ? recoverCatalogScene3D(envWithStatement)
          : envWithStatement;
        const mod = getSimulation(env.simulation_id);
        if (!mod) continue;

        let validResult: ConfigResult<unknown>;
        try {
          validResult = mod.validateEnvelope
            ? mod.validateEnvelope(env)
            : mod.validateConfig(env.config);
        } catch {
          continue;
        }
        if (!validResult.ok) continue;

        let restoredState: unknown;
        try {
          restoredState = mod.init(validResult.config);
        } catch {
          continue;
        }

        if (histItem?.lastCursor != null && mod.timeline) {
          const total = mod.timeline.stepCount(restoredState);
          if (histItem.lastCursor >= 0 && histItem.lastCursor <= total) {
            restoredState = mod.timeline.goToStep(restoredState, histItem.lastCursor);
          }
        }

        const resolvedTitle =
          histItem?.title?.trim() || entry.title.trim() || env.title?.trim() || "Mô phỏng 3D";
        const resourceKey = getSimulationResourceKey({
          tabId: entry.id,
          sampleId: inferredSampleId,
          historyId: histItem?.id ?? entry.historyId,
          title: resolvedTitle,
          originalInput: histItem?.originalInput ?? null,
          problemStatement: deGui ?? env.problem_statement ?? null,
          envelope: env,
        });
        if (seenKeys.has(resourceKey)) continue;
        seenKeys.add(resourceKey);

        const tabId = inferredSampleId
          ? `tab-sample-${inferredSampleId}`
          : entry.id || (histItem ? `tab-hist-${histItem.id}` : `tab-sim-${nextTabs.length}`);
        nextTabs.push({
          id: tabId,
          problemId: inferredSampleId ?? histItem?.id ?? entry.historyId ?? env.simulation_id,
          sessionId: histItem?.id ?? entry.historyId ?? inferredSampleId ?? tabId,
          kind: "simulation",
          title: resolvedTitle,
          active: {
            moduleId: mod.id,
            envelope: resolvedTitle !== env.title ? { ...env, title: resolvedTitle } : env,
            config: validResult.config,
            state: restoredState,
            problemStatement: deGui ?? null,
          },
          sampleId: inferredSampleId,
          historyId: histItem?.id ?? entry.historyId,
        });
      }

      const desiredActiveId = snapshot.activeWorkspaceTabId ?? snapshot.activeTabId;
      const matchedActive =
        (desiredActiveId ? nextTabs.find((t) => t.id === desiredActiveId) : undefined) ??
        (cur.activeTabId ? nextTabs.find((t) => t.id === cur.activeTabId) : undefined) ??
        nextTabs[nextTabs.length - 1] ??
        null;

      const nextLibraryOpen = snapshot.libraryTabOpen;
      let nextView: AppView = cur.view;
      if (snapshot.view === "library" && nextLibraryOpen) {
        nextView = "library";
      } else if (matchedActive && (snapshot.view === "workspace" || nextTabs.length > 0)) {
        nextView = snapshot.view === "home" ? "home" : "workspace";
      }

      set((s) => ({
        libraryTabOpen: nextLibraryOpen || s.libraryTabOpen,
        libraryUiState: sanitizeLibraryUiState(snapshot.libraryUiState),
        workspaceTabs: nextTabs,
        activeTabId: matchedActive?.id ?? s.activeTabId,
        active:
          matchedActive?.kind === "simulation"
            ? (matchedActive.active ?? s.active)
            : nextTabs.length === 0
              ? null
              : s.active,
        activeSampleId:
          matchedActive?.kind === "simulation"
            ? matchedActive.sampleId
            : s.activeSampleId,
        activeHistoryId:
          matchedActive?.kind === "simulation"
            ? matchedActive.historyId
            : s.activeHistoryId,
        problemText:
          matchedActive?.kind === "draft"
            ? (matchedActive.draftText ?? "")
            : s.problemText,
        view: s.routeFailure ? s.view : nextView,
        navHistoryMode: "replace",
        hasInAppNavigation: s.hasInAppNavigation || nextTabs.length > 0 || nextLibraryOpen,
      }));
      persistWorkspaceSessionSnapshot(get());
    },

    // Dọn RUNTIME — lịch sử bền KHÔNG bị đụng (hai đời sống tách biệt, M9-UX1).
    /* `reset` là "về trạng thái sạch" (dùng ở test và thoát hẳn). Khác
       `goHome`: goHome giữ lịch sử hiển thị, reset dọn cả bàn làm việc. */
    reset: () => {
      hasHydratedLocation = false;
      hasHydratedWorkspaceSession = false;
      clearWorkspaceSessionSnapshot();
      historyStore.clearProcessingRecords();
      historyStore.clearDraftText();
      set({
        active: null,
        workspaceTabs: [],
        activeTabId: null,
        libraryTabOpen: false,
        libraryUiState: { ...DEFAULT_LIBRARY_UI_STATE },
        workspaceNavStack: [{ view: "home", tabId: null }],
        workspaceNavIndex: 0,
        navHistoryMode: "push",
        unsupported: null,
        analysisError: null,
        clientFailure: null,
        routeFailure: null,
        validRouteStack: ["home"],
        hasInAppNavigation: false,
        returnView: "home",
        activeSampleId: null,
        playing: false,
        exploreOpen: false,
        visualMode: "2d",
        leftRailManualCollapsed: null,
        leftRailHoverPreview: false,
        leftRailMobileOpen: false,
        leftRailSearchOpen: false,
        leftRailSearchQuery: "",
        leftRailActiveGroupCollapsed: false,
        leftRailRecentGroupCollapsed: false,
        leftRailProblemGroupCollapsed: false,
        leftRailProblemFilter: "all",
        problemMetaVersion: 0,
        problemProcessingRecords: {},
        lastAnalyzedStatement: "",
        analyzing: false,
        guestEnteredApp: false,
        tabStepProgress: {},
        view: "home",
        activeHistoryId: null,
        history: historyStore.list(),
      });
    },
  };
});

/* Đồng bộ lịch sử theo tài khoản khi trạng thái đăng nhập thay đổi. */
useAuthStore.subscribe((state, prevState) => {
  const prevId = prevState.user?.id ?? null;
  const nextId = state.user?.id ?? null;
  if (prevId === nextId) return;
  if (nextId === null) {
    clearWorkspaceSessionSnapshot();
    historyStore.clear();
    if (typeof window !== "undefined") {
      try {
        window.sessionStorage.removeItem("axo_auth_session_hint");
      } catch {
        /* bỏ qua nếu trình duyệt chặn sessionStorage */
      }
    }
    useAppStore.setState({
      active: null,
      workspaceTabs: [],
      activeTabId: null,
      activeHistoryId: null,
      activeSampleId: null,
      history: [],
      problemProcessingRecords: {},
      problemText: "",
      lastAnalyzedStatement: "",
      unsupported: null,
      analysisError: null,
      clientFailure: null,
      routeFailure: null,
      playing: false,
      analyzing: false,
      accountModalOpen: false,
      leftRailSearchOpen: false,
      leftRailSearchQuery: "",
      tabStepProgress: {},
      workspaceNavStack: [{ view: "home", tabId: null }],
      workspaceNavIndex: 0,
      validRouteStack: ["home"],
    });
    return;
  }
  void fetchServerHistory().then((items) => {
    if (items === null) return;
    if (useAuthStore.getState().user?.id !== nextId) return;
    historyStore.replaceAll?.(items);
    useAppStore.setState({ history: historyStore.list() });
  });
});

export function syncStoreFromStorageKey(changedKey: string | null): void {
  if (
    changedKey !== null &&
    !changedKey.startsWith("algosim.history.v1") &&
    changedKey !== "algosim.problem_meta.v1" &&
    changedKey !== PROBLEM_PROCESSING_RECORDS_KEY
  ) {
    return;
  }
  useAppStore.setState((s) => ({
    history: historyStore.list(),
    problemProcessingRecords:
      changedKey === PROBLEM_PROCESSING_RECORDS_KEY || changedKey === null
        ? recoverPersistedProblemProcessingRecords()
        : s.problemProcessingRecords,
    problemMetaVersion: s.problemMetaVersion + 1,
  }));
}

if (typeof window !== "undefined" && typeof window.addEventListener === "function") {
  window.addEventListener("storage", (e: StorageEvent) => {
    syncStoreFromStorageKey(e.key);
  });
}
