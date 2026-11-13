import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { publicCatalog } from "../data/offline-catalog";
import {
  GeometryFamilyIcon,
  resolveGeometrySolidFamily,
  type GeometrySolidFamily,
} from "./family-icons";
import { IconAxoLogo, IconSidebarPanel } from "./icons";
import { clearSavedDraftAttachments } from "./ProblemInput";
import { stepCountOfEnvelope } from "./SessionCard";
import { useAuthStore } from "../state/auth";
import { historyStore } from "../state/history";
import { loadLearnerRecoverySnapshot } from "../state/learner-recovery-snapshot";
import {
  buildUnifiedProblemList,
  resolveEffectiveWorkspaceTabs,
  useAppStore,
  type LeftRailProblemFilter,
  type UnifiedSidebarProblemItem,
  type WorkspaceTabItem,
} from "../state/store";

function formatStepSubtitle(
  tab: WorkspaceTabItem,
  liveProgress: { current: number; total: number } | undefined,
): string {
  if (tab.kind === "draft") {
    return "Đang nhập đề toán";
  }
  if (liveProgress && liveProgress.total > 0) {
    const safeCurrent = Math.max(1, Math.min(liveProgress.current, liveProgress.total));
    return `Bước ${safeCurrent}/${liveProgress.total}`;
  }
  const env = tab.active?.envelope;
  const totalSteps = env ? stepCountOfEnvelope(env) : 0;
  const problemKey = tab.sampleId || tab.historyId || env?.simulation_id || tab.id;
  const recovered = problemKey ? loadLearnerRecoverySnapshot(problemKey) : null;
  if (totalSteps > 0) {
    const stepNum =
      typeof recovered?.stepIndex === "number"
        ? Math.max(1, Math.min(recovered.stepIndex + 1, totalSteps))
        : 1;
    return `Bước ${stepNum}/${totalSteps}`;
  }
  return "Mô phỏng 3D";
}

function formatUnifiedProblemSubtitle(
  item: UnifiedSidebarProblemItem,
  tabStepProgress: Record<string, { current: number; total: number }>,
): string {
  if (item.processingStatus === "in_progress") {
    return "Đang tiến hành";
  }
  if (item.processingStatus === "needs_attention") {
    return (
      item.processingRecord?.reasonMessage ||
      item.processingRecord?.analysisError ||
      "Cần chú ý"
    );
  }
  if (item.openTab) {
    const sub = formatStepSubtitle(item.openTab, tabStepProgress[item.openTab.id]);
    return item.kind === "draft" ? sub : `Đang mở · ${sub}`;
  }
  if (item.historyItem) {
    const totalSteps = stepCountOfEnvelope(item.historyItem.envelope);
    const stepNum =
      typeof item.historyItem.lastCursor === "number" && totalSteps > 0
        ? Math.max(1, Math.min(item.historyItem.lastCursor + 1, totalSteps))
        : null;
    if (stepNum !== null && totalSteps > 0) {
      return `Bước ${stepNum}/${totalSteps}`;
    }
    if (totalSteps > 0) {
      return `${totalSteps} bước`;
    }
  }
  return "Mô phỏng 3D";
}

function getInitials(displayName: string): string {
  const parts = displayName.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "AX";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  const first = parts[0]?.[0] ?? "";
  const last = parts[parts.length - 1]?.[0] ?? "";
  return `${first}${last}`.toUpperCase();
}

function detectSearchShortcutLabel(): string {
  if (typeof navigator === "undefined") return "Ctrl+K";
  const platform =
    (navigator as Navigator & { userAgentData?: { platform?: string } })
      .userAgentData?.platform ||
    navigator.platform ||
    navigator.userAgent ||
    "";
  return /Mac|iPhone|iPad|iPod/i.test(platform) ? "⌘K" : "Ctrl+K";
}

export function foldVietnamese(raw: string): string {
  return raw
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[đĐ]/g, "d")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

export function matchesSearchQuery(
  queryRaw: string,
  ...fields: Array<string | null | undefined>
): boolean {
  const qTrim = queryRaw.trim();
  if (!qTrim) return true;
  const qLower = qTrim.toLowerCase();
  const qFolded = foldVietnamese(qTrim);
  const qTokens = qFolded.split(" ").filter(Boolean);

  const combinedRaw = fields.filter(Boolean).join(" ").toLowerCase();
  if (combinedRaw.includes(qLower)) return true;

  const combinedFolded = foldVietnamese(combinedRaw);
  if (combinedFolded.includes(qFolded)) return true;

  if (qTokens.length > 1) {
    return qTokens.every((tok) => combinedFolded.includes(tok));
  }
  return false;
}

function formatHistoryDateBadge(timestampMs: number): string {
  if (!Number.isFinite(timestampMs) || timestampMs <= 0) return "Gần đây";
  const diffMs = Date.now() - timestampMs;
  if (diffMs < 60_000) return "Vừa xong";
  if (diffMs < 3_600_000) return `${Math.max(1, Math.floor(diffMs / 60_000))} phút trước`;
  if (diffMs < 86_400_000) return `${Math.max(1, Math.floor(diffMs / 3_600_000))} giờ trước`;
  try {
    const d = new Date(timestampMs);
    const day = String(d.getDate()).padStart(2, "0");
    const month = String(d.getMonth() + 1).padStart(2, "0");
    return `${day}/${month}`;
  } catch {
    return "Gần đây";
  }
}

const FILTER_LABELS: Record<LeftRailProblemFilter, string> = {
  all: "Tất cả",
  ready: "Sẵn sàng",
  needs_attention: "Cần chú ý",
  in_progress: "Đang tiến hành",
};

const FILTER_OPTIONS_ORDER: readonly LeftRailProblemFilter[] = [
  "all",
  "ready",
  "needs_attention",
  "in_progress",
];

export function IconSidebarToggle() {
  return <IconSidebarPanel />;
}

export function IconSidebarCollapsedTrigger() {
  return <IconSidebarToggle />;
}

function IconFilterOption({ filter }: { filter: LeftRailProblemFilter }) {
  if (filter === "ready") {
    return (
      <span className="sb-filter-opt-icon is-ready" aria-hidden="true">
        <svg viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="4.2" fill="#2383E2" />
        </svg>
      </span>
    );
  }
  if (filter === "needs_attention") {
    return (
      <span className="sb-filter-opt-icon is-needs-attention" aria-hidden="true">
        <svg
          viewBox="0 0 16 16"
          fill="none"
          stroke="#D9730D"
          strokeWidth="1.55"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M3.5 2.5v11" />
          <path
            d="M3.5 3.2h8l-1.9 2.8 1.9 2.8h-8"
            fill="rgba(217, 115, 13, 0.16)"
          />
        </svg>
      </span>
    );
  }
  if (filter === "in_progress") {
    return (
      <span className="sb-filter-opt-icon is-in-progress" aria-hidden="true">
        <svg
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.65"
          strokeLinecap="round"
        >
          <circle cx="8" cy="8" r="5.2" strokeOpacity="0.25" />
          <path d="M8 2.8a5.2 5.2 0 0 1 5.2 5.2" />
        </svg>
      </span>
    );
  }
  return (
    <span className="sb-filter-opt-icon is-all" aria-hidden="true">
      <svg
        viewBox="0 0 16 16"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.55"
        strokeLinecap="round"
      >
        <path d="M2.5 4h11M4.5 8h7M6.5 12h3" />
      </svg>
    </span>
  );
}

interface FilterPopoverCoords {
  top: number;
  left: number;
  placement: "bottom-start" | "top-start";
}

interface SearchPopupEntry {
  key: string;
  source: "active" | "recent" | "library";
  title: string;
  subtitle: string;
  badgeText: string;
  geometryFamily: GeometrySolidFamily;
  onSelect: () => void;
}

interface ActionMenuState {
  canonicalId: string;
  top: number;
  left: number;
  placement: "bottom-right" | "top-right";
}

interface RenameModalState {
  canonicalId: string;
  currentTitle: string;
  draftTitle: string;
  error: string | null;
}

interface DeleteModalState {
  item: UnifiedSidebarProblemItem;
  deleting: boolean;
  error: string | null;
}

export function LeftSidebar() {
  const view = useAppStore((s) => s.view);
  const workspaceTabs = useAppStore((s) => s.workspaceTabs);
  const activeTabId = useAppStore((s) => s.activeTabId);
  const active = useAppStore((s) => s.active);
  const activeSampleId = useAppStore((s) => s.activeSampleId);
  const activeHistoryId = useAppStore((s) => s.activeHistoryId);
  const history = useAppStore((s) => s.history);
  const tabStepProgress = useAppStore((s) => s.tabStepProgress);
  const problemMetaVersion = useAppStore((s) => s.problemMetaVersion);
  const problemProcessingRecords = useAppStore((s) => s.problemProcessingRecords);
  const analyzing = useAppStore((s) => s.analyzing);
  const problemText = useAppStore((s) => s.problemText);
  const openProblemAttempt = useAppStore((s) => s.openProblemAttempt);

  const leftRailManualCollapsed = useAppStore((s) => s.leftRailManualCollapsed);
  const leftRailHoverPreview = useAppStore((s) => s.leftRailHoverPreview);
  const leftRailMobileOpen = useAppStore((s) => s.leftRailMobileOpen);
  const leftRailSearchOpen = useAppStore((s) => s.leftRailSearchOpen);
  const leftRailSearchQuery = useAppStore((s) => s.leftRailSearchQuery);
  const leftRailProblemGroupCollapsed = useAppStore((s) => s.leftRailProblemGroupCollapsed);
  const leftRailProblemFilter = useAppStore((s) => s.leftRailProblemFilter);

  const toggleLeftRailCollapsed = useAppStore((s) => s.toggleLeftRailCollapsed);
  const setLeftRailCollapsed = useAppStore((s) => s.setLeftRailCollapsed);
  const setLeftRailHoverPreview = useAppStore((s) => s.setLeftRailHoverPreview);
  const setLeftRailMobileOpen = useAppStore((s) => s.setLeftRailMobileOpen);
  const setLeftRailSearchOpen = useAppStore((s) => s.setLeftRailSearchOpen);
  const setLeftRailSearchQuery = useAppStore((s) => s.setLeftRailSearchQuery);
  const toggleLeftRailProblemGroup = useAppStore((s) => s.toggleLeftRailProblemGroup);
  const setLeftRailProblemFilter = useAppStore((s) => s.setLeftRailProblemFilter);
  const togglePinProblem = useAppStore((s) => s.togglePinProblem);
  const renameProblem = useAppStore((s) => s.renameProblem);
  const deleteProblem = useAppStore((s) => s.deleteProblem);
  const setGuestEnteredApp = useAppStore((s) => s.setGuestEnteredApp);

  const goHome = useAppStore((s) => s.goHome);
  const openLibrary = useAppStore((s) => s.openLibrary);
  const setView = useAppStore((s) => s.setView);
  const closeWorkspaceTab = useAppStore((s) => s.closeWorkspaceTab);
  const setProblemText = useAppStore((s) => s.setProblemText);
  const activateWorkspaceTab = useAppStore((s) => s.activateWorkspaceTab);
  const reopenFromHistory = useAppStore((s) => s.reopenFromHistory);
  const loadEnvelope = useAppStore((s) => s.loadEnvelope);
  const openAccountModal = useAppStore((s) => s.openAccountModal);

  const user = useAuthStore((s) => s.user);
  const authResolved = useAuthStore(
    (s) => (s as { authResolved?: boolean }).authResolved ?? s.resolved,
  );
  const logout = useAuthStore((s) => s.logout);

  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [filterMenuOpen, setFilterMenuOpen] = useState(false);
  const [filterPopoverCoords, setFilterPopoverCoords] = useState<FilterPopoverCoords>({
    top: 224,
    left: 182,
    placement: "bottom-start",
  });
  const [actionMenuState, setActionMenuState] = useState<ActionMenuState | null>(null);
  const [renameModalState, setRenameModalState] = useState<RenameModalState | null>(null);
  const [deleteModalState, setDeleteModalState] = useState<DeleteModalState | null>(null);
  const [selectedSearchIndex, setSelectedSearchIndex] = useState(0);

  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const searchModalRef = useRef<HTMLDivElement | null>(null);
  const searchTriggerBtnRef = useRef<HTMLButtonElement | null>(null);
  const lastSearchTriggerRef = useRef<HTMLElement | null>(null);
  const sidebarRef = useRef<HTMLElement | null>(null);
  const triggerZoneRef = useRef<HTMLDivElement | null>(null);
  const accountBtnRef = useRef<HTMLButtonElement | null>(null);
  const accountPopoverRef = useRef<HTMLDivElement | null>(null);
  const guestSidebarRowRef = useRef<HTMLDivElement | null>(null);
  const filterBtnRef = useRef<HTMLButtonElement | null>(null);
  const filterPopoverRef = useRef<HTMLDivElement | null>(null);
  const actionMenuPopoverRef = useRef<HTMLDivElement | null>(null);
  const renameInputRef = useRef<HTMLInputElement | null>(null);

  const hoverOpenTimerRef = useRef<number | null>(null);
  const hoverCloseTimerRef = useRef<number | null>(null);
  const isPointerInsidePreviewRef = useRef(false);
  const shortcutLabel = useMemo(() => detectSearchShortcutLabel(), []);

  const [viewportWidth, setViewportWidth] = useState<number>(() =>
    typeof window !== "undefined" ? window.innerWidth : 1440,
  );

  const clearHoverCloseTimer = () => {
    if (hoverOpenTimerRef.current !== null && typeof window !== "undefined") {
      window.clearTimeout(hoverOpenTimerRef.current);
      hoverOpenTimerRef.current = null;
    }
    if (hoverCloseTimerRef.current !== null && typeof window !== "undefined") {
      window.clearTimeout(hoverCloseTimerRef.current);
      hoverCloseTimerRef.current = null;
    }
  };

  useEffect(() => {
    return () => {
      if (hoverOpenTimerRef.current !== null && typeof window !== "undefined") {
        window.clearTimeout(hoverOpenTimerRef.current);
      }
      if (hoverCloseTimerRef.current !== null && typeof window !== "undefined") {
        window.clearTimeout(hoverCloseTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    let prevW = window.innerWidth;
    const onResize = () => {
      const w = window.innerWidth;
      setViewportWidth(w);
      if (w > 767) {
        setLeftRailMobileOpen(false);
      } else {
        setLeftRailHoverPreview(false);
      }
      const wasDesktop = prevW > 1024;
      const isNowDesktop = w > 1024;
      if (wasDesktop !== isNowDesktop) {
        setLeftRailCollapsed(null);
      }
      prevW = w;
    };
    window.addEventListener("resize", onResize, { passive: true });
    return () => window.removeEventListener("resize", onResize);
  }, [setLeftRailCollapsed, setLeftRailHoverPreview, setLeftRailMobileOpen]);

  const closeSearchModal = useCallback(
    (restoreFocus = true) => {
      setLeftRailSearchOpen(false);
      if (restoreFocus && typeof window !== "undefined") {
        const target = lastSearchTriggerRef.current ?? searchTriggerBtnRef.current;
        window.setTimeout(() => {
          if (target && document.body.contains(target)) {
            target.focus();
          } else {
            searchTriggerBtnRef.current?.focus();
          }
        }, 15);
      }
    },
    [setLeftRailSearchOpen],
  );

  const openSearchModal = useCallback(() => {
    if (typeof document !== "undefined" && document.activeElement instanceof HTMLElement) {
      lastSearchTriggerRef.current = document.activeElement;
    }
    setSelectedSearchIndex(0);
    setLeftRailSearchOpen(true);
    if (typeof window !== "undefined") {
      window.setTimeout(() => searchInputRef.current?.focus(), 20);
    }
  }, [setLeftRailSearchOpen]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        const state = useAppStore.getState();
        if (state.leftRailSearchOpen) {
          closeSearchModal(true);
        } else {
          openSearchModal();
        }
      } else if (e.key === "Escape") {
        if (renameModalState) {
          e.preventDefault();
          setRenameModalState(null);
          return;
        }
        if (deleteModalState && !deleteModalState.deleting) {
          e.preventDefault();
          setDeleteModalState(null);
          return;
        }
        if (actionMenuState) {
          e.preventDefault();
          setActionMenuState(null);
          return;
        }
        if (filterMenuOpen) {
          e.preventDefault();
          setFilterMenuOpen(false);
          filterBtnRef.current?.focus();
          return;
        }
        const state = useAppStore.getState();
        if (state.leftRailSearchOpen) {
          e.preventDefault();
          closeSearchModal(true);
          return;
        }
        if (accountMenuOpen) {
          setAccountMenuOpen(false);
          accountBtnRef.current?.focus();
          return;
        }
        if (state.leftRailMobileOpen) {
          setLeftRailMobileOpen(false);
        } else if (state.leftRailHoverPreview) {
          setLeftRailHoverPreview(false);
        }
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [
    accountMenuOpen,
    actionMenuState,
    closeSearchModal,
    deleteModalState,
    filterMenuOpen,
    openSearchModal,
    renameModalState,
    setLeftRailHoverPreview,
    setLeftRailMobileOpen,
  ]);

  useEffect(() => {
    if (!user && accountMenuOpen) {
      setAccountMenuOpen(false);
    }
  }, [accountMenuOpen, user]);

  useEffect(() => {
    if (!accountMenuOpen || typeof document === "undefined") return;
    const onPointerDownOutside = (e: MouseEvent) => {
      const target = e.target as Node | null;
      if (!target) return;
      if (
        accountPopoverRef.current?.contains(target) ||
        accountBtnRef.current?.contains(target)
      ) {
        return;
      }
      setAccountMenuOpen(false);
    };
    document.addEventListener("mousedown", onPointerDownOutside);
    return () => document.removeEventListener("mousedown", onPointerDownOutside);
  }, [accountMenuOpen]);

  useEffect(() => {
    if (!filterMenuOpen || typeof document === "undefined") return;
    const onPointerDownOutside = (e: MouseEvent) => {
      const target = e.target as Node | null;
      if (!target) return;
      if (
        filterPopoverRef.current?.contains(target) ||
        filterBtnRef.current?.contains(target)
      ) {
        return;
      }
      setFilterMenuOpen(false);
    };
    document.addEventListener("mousedown", onPointerDownOutside);
    return () => document.removeEventListener("mousedown", onPointerDownOutside);
  }, [filterMenuOpen]);

  useEffect(() => {
    if (!actionMenuState || typeof document === "undefined") return;
    const onPointerDownOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement | null;
      if (!target) return;
      if (actionMenuPopoverRef.current?.contains(target)) {
        return;
      }
      if (target.closest?.(`[data-problem-more-btn="${actionMenuState.canonicalId}"]`)) {
        return;
      }
      setActionMenuState(null);
    };
    document.addEventListener("mousedown", onPointerDownOutside);
    return () => document.removeEventListener("mousedown", onPointerDownOutside);
  }, [actionMenuState]);

  useEffect(() => {
    if (!renameModalState || typeof window === "undefined") return;
    const id = window.setTimeout(() => {
      renameInputRef.current?.focus();
      renameInputRef.current?.select();
    }, 15);
    return () => window.clearTimeout(id);
  }, [renameModalState?.canonicalId]);

  useEffect(() => {
    if (!leftRailHoverPreview || typeof document === "undefined") return;
    const onPointerDownOutside = (e: MouseEvent) => {
      const target = e.target as Node | null;
      if (!target) return;
      if (
        sidebarRef.current?.contains(target) ||
        triggerZoneRef.current?.contains(target) ||
        actionMenuPopoverRef.current?.contains(target) ||
        filterPopoverRef.current?.contains(target)
      ) {
        return;
      }
      setLeftRailHoverPreview(false);
    };
    document.addEventListener("mousedown", onPointerDownOutside);
    return () => document.removeEventListener("mousedown", onPointerDownOutside);
  }, [leftRailHoverPreview, setLeftRailHoverPreview]);

  useEffect(() => {
    if (leftRailSearchOpen) {
      setSelectedSearchIndex(0);
      const id = window.setTimeout(() => searchInputRef.current?.focus(), 20);
      return () => window.clearTimeout(id);
    }
  }, [leftRailSearchOpen]);

  useEffect(() => {
    setSelectedSearchIndex(0);
  }, [leftRailSearchQuery]);

  const isMobileViewport = viewportWidth <= 767;
  const isTabletViewport = viewportWidth >= 768 && viewportWidth <= 1024;

  const isCollapsed = useMemo(() => {
    if (isMobileViewport) return false;
    if (leftRailManualCollapsed !== null) return leftRailManualCollapsed;
    if (isTabletViewport) return true;
    return false;
  }, [isMobileViewport, isTabletViewport, leftRailManualCollapsed]);

  const isHoverPreviewActive = isCollapsed && !isMobileViewport && leftRailHoverPreview;
  const sidebarState: "expanded" | "collapsed" | "hover-preview" = isCollapsed
    ? isHoverPreviewActive
      ? "hover-preview"
      : "collapsed"
    : "expanded";

  const handleTriggerMouseEnter = () => {
    isPointerInsidePreviewRef.current = true;
    if (isMobileViewport || !isCollapsed) return;
    clearHoverCloseTimer();
    if (leftRailHoverPreview) return;
    if (typeof window !== "undefined") {
      hoverOpenTimerRef.current = window.setTimeout(() => {
        setLeftRailHoverPreview(true);
        hoverOpenTimerRef.current = null;
      }, 80);
    } else {
      setLeftRailHoverPreview(true);
    }
  };

  const handlePanelMouseEnter = () => {
    isPointerInsidePreviewRef.current = true;
    if (isMobileViewport || !isCollapsed) return;
    clearHoverCloseTimer();
    setLeftRailHoverPreview(true);
  };

  const handlePreviewZoneMouseLeave = () => {
    isPointerInsidePreviewRef.current = false;
    if (isMobileViewport || !isCollapsed) return;
    if (actionMenuState || filterMenuOpen || accountMenuOpen) return;
    clearHoverCloseTimer();
    if (typeof window !== "undefined") {
      hoverCloseTimerRef.current = window.setTimeout(() => {
        setLeftRailHoverPreview(false);
        hoverCloseTimerRef.current = null;
      }, 160);
    } else {
      setLeftRailHoverPreview(false);
    }
  };

  useEffect(() => {
    if (sidebarState !== "hover-preview") return;
    if (actionMenuState || filterMenuOpen || accountMenuOpen) return;
    if (isPointerInsidePreviewRef.current) return;
    clearHoverCloseTimer();
    if (typeof window !== "undefined") {
      hoverCloseTimerRef.current = window.setTimeout(() => {
        if (!isPointerInsidePreviewRef.current) {
          setLeftRailHoverPreview(false);
        }
        hoverCloseTimerRef.current = null;
      }, 140);
    } else {
      setLeftRailHoverPreview(false);
    }
  }, [
    accountMenuOpen,
    actionMenuState,
    filterMenuOpen,
    setLeftRailHoverPreview,
    sidebarState,
  ]);

  const handlePinExpandFromCollapsed = () => {
    clearHoverCloseTimer();
    setLeftRailHoverPreview(false);
    setLeftRailCollapsed(false);
  };

  const { tabs: effectiveTabs, activeTabId: effectiveActiveTabId } = useMemo(
    () =>
      resolveEffectiveWorkspaceTabs({
        workspaceTabs,
        activeTabId,
        active,
        activeSampleId,
        activeHistoryId,
      }),
    [workspaceTabs, activeTabId, active, activeSampleId, activeHistoryId],
  );

  const allUnifiedItems = useMemo(
    () =>
      buildUnifiedProblemList({
        effectiveTabs,
        effectiveActiveTabId,
        view,
        history,
        filter: "all",
        processingRecords: problemProcessingRecords,
        analyzing,
        activeProblemText: problemText,
      }),
    [
      effectiveTabs,
      effectiveActiveTabId,
      view,
      history,
      problemMetaVersion,
      problemProcessingRecords,
      analyzing,
      problemText,
    ],
  );

  const unifiedSidebarItems = useMemo(
    () =>
      buildUnifiedProblemList({
        effectiveTabs,
        effectiveActiveTabId,
        view,
        history,
        filter: leftRailProblemFilter,
        processingRecords: problemProcessingRecords,
        analyzing,
        activeProblemText: problemText,
      }),
    [
      effectiveTabs,
      effectiveActiveTabId,
      view,
      history,
      leftRailProblemFilter,
      problemMetaVersion,
      problemProcessingRecords,
      analyzing,
      problemText,
    ],
  );

  const computeFilterPopoverPosition = useCallback((): FilterPopoverCoords => {
    if (typeof window === "undefined" || !filterBtnRef.current) {
      return { top: 224, left: 182, placement: "bottom-start" };
    }
    const triggerRect = filterBtnRef.current.getBoundingClientRect();
    const popoverWidth = 192;
    const popoverHeight = 162;
    const vw = window.innerWidth || 1440;
    const vh = window.innerHeight || 900;

    const left = Math.round(
      Math.max(8, Math.min(vw - popoverWidth - 8, triggerRect.left)),
    );

    const shouldFlipUp =
      triggerRect.bottom + 4 + popoverHeight > vh - 8 &&
      triggerRect.top >= popoverHeight + 8;
    const top = Math.round(
      shouldFlipUp
        ? Math.max(8, triggerRect.top - popoverHeight - 4)
        : triggerRect.bottom + 4,
    );
    return {
      top,
      left,
      placement: shouldFlipUp ? "top-start" : "bottom-start",
    };
  }, []);

  useEffect(() => {
    if (!filterMenuOpen || typeof window === "undefined") return;
    setFilterPopoverCoords(computeFilterPopoverPosition());
    const onReposition = () => {
      setFilterPopoverCoords(computeFilterPopoverPosition());
    };
    window.addEventListener("resize", onReposition, { passive: true });
    return () => window.removeEventListener("resize", onReposition);
  }, [computeFilterPopoverPosition, filterMenuOpen, sidebarState]);

  const handleFilterPopoverKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const items = Array.from(
      filterPopoverRef.current?.querySelectorAll<HTMLButtonElement>(
        '[role="menuitemradio"]',
      ) ?? [],
    );
    if (items.length === 0) return;
    const currentIndex = items.indexOf(document.activeElement as HTMLButtonElement);
    if (e.key === "ArrowDown") {
      e.preventDefault();
      const next = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
      items[next]?.focus();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      const prev = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
      items[prev]?.focus();
    } else if (e.key === "Home") {
      e.preventDefault();
      items[0]?.focus();
    } else if (e.key === "End") {
      e.preventDefault();
      items[items.length - 1]?.focus();
    }
  };

  const activeActionMenuItem = useMemo(
    () =>
      actionMenuState
        ? unifiedSidebarItems.find((x) => x.canonicalId === actionMenuState.canonicalId) ??
          allUnifiedItems.find((x) => x.canonicalId === actionMenuState.canonicalId) ??
          null
        : null,
    [actionMenuState, allUnifiedItems, unifiedSidebarItems],
  );

  const closeMobileIfOpen = useCallback(() => {
    if (leftRailMobileOpen) {
      setLeftRailMobileOpen(false);
    }
  }, [leftRailMobileOpen, setLeftRailMobileOpen]);

  const handleSelectProblemItem = useCallback(
    (item: UnifiedSidebarProblemItem) => {
      if (item.openTab) {
        activateWorkspaceTab(item.openTab.id);
      } else if (item.historyItem) {
        reopenFromHistory(item.historyItem.id);
      } else if (item.processingRecord) {
        openProblemAttempt(item.canonicalId);
        if (typeof document !== "undefined") {
          window.setTimeout(() => {
            const input =
              (document.getElementById("home-problem-input") as HTMLTextAreaElement | null) ??
              (document.getElementById("composer-input") as HTMLTextAreaElement | null);
            input?.focus();
          }, 30);
        }
      }
      closeMobileIfOpen();
    },
    [activateWorkspaceTab, closeMobileIfOpen, openProblemAttempt, reopenFromHistory],
  );

  const hasQuery = leftRailSearchQuery.trim().length > 0;

  const searchPopupEntries = useMemo<SearchPopupEntry[]>(() => {
    const entries: SearchPopupEntry[] = [];
    const seenSampleIds = new Set<string>();
    const seenTitles = new Set<string>();

    // 1. Unified user problems (open tabs + history, deduplicated, reflecting custom titles & pin priority)
    for (const item of allUnifiedItems) {
      if (
        hasQuery &&
        !matchesSearchQuery(leftRailSearchQuery, item.title, item.problemStatement)
      ) {
        continue;
      }
      if (item.openTab?.sampleId) {
        seenSampleIds.add(item.openTab.sampleId);
      }
      seenTitles.add(foldVietnamese(item.title));
      const sub = formatUnifiedProblemSubtitle(item, tabStepProgress);
      const badgeText = item.isCurrentActiveTab
        ? "Đang xem"
        : item.isOpenInTab
          ? "Đang mở"
          : formatHistoryDateBadge(item.lastAccessMs);

      const itemFamily =
        (item as UnifiedSidebarProblemItem & { geometryFamily?: GeometrySolidFamily })
          .geometryFamily ??
        resolveGeometrySolidFamily({
          envelope: item.openTab?.active?.envelope ?? item.historyItem?.envelope,
          sampleId: item.openTab?.sampleId,
          problemStatement: item.problemStatement,
          title: item.title,
        });

      entries.push({
        key: `problem-${item.canonicalId}`,
        source: item.isOpenInTab ? "active" : "recent",
        title: item.title,
        subtitle: item.isOpenInTab ? sub : `Gần đây · ${sub}`,
        badgeText,
        geometryFamily: itemFamily,
        onSelect: () => {
          handleSelectProblemItem(item);
          closeSearchModal(false);
        },
      });

      if (!hasQuery && entries.length >= 10) {
        break;
      }
    }

    // 2. Public Simulation Library (when searching, or when no active/recent items exist yet)
    if (hasQuery || entries.length === 0) {
      const catalog = publicCatalog();
      for (const entry of catalog) {
        if (seenSampleIds.has(entry.id) || seenTitles.has(foldVietnamese(entry.title))) {
          continue;
        }
        const prompt = entry.envelope.problem_statement ?? "";
        if (
          hasQuery &&
          !matchesSearchQuery(leftRailSearchQuery, entry.title, prompt, entry.slug)
        ) {
          continue;
        }
        const totalSteps = stepCountOfEnvelope(entry.envelope);
        const catalogFamily = resolveGeometrySolidFamily({
          envelope: entry.envelope,
          sampleId: entry.id,
          problemStatement: prompt,
          title: entry.title,
        });
        entries.push({
          key: `catalog-${entry.id}`,
          source: "library",
          title: entry.title,
          subtitle:
            totalSteps > 0
              ? `Thư viện mô phỏng · ${totalSteps} bước`
              : "Thư viện mô phỏng · 3D",
          badgeText: "Thư viện",
          geometryFamily: catalogFamily,
          onSelect: () => {
            loadEnvelope(entry.envelope, entry.id);
            closeSearchModal(false);
            closeMobileIfOpen();
          },
        });
        if (!hasQuery && entries.length >= 6) {
          break;
        }
      }
    }

    return entries;
  }, [
    allUnifiedItems,
    closeMobileIfOpen,
    closeSearchModal,
    handleSelectProblemItem,
    hasQuery,
    leftRailSearchQuery,
    loadEnvelope,
    tabStepProgress,
  ]);

  const handleGoHome = () => {
    goHome();
    closeMobileIfOpen();
  };

  const handleNewProblem = () => {
    const curState = useAppStore.getState();
    if (curState.workspaceTabs.some((t) => t.id === "tab-draft-new")) {
      closeWorkspaceTab("tab-draft-new");
    }
    if (!curState.analyzing) {
      setProblemText("");
      historyStore.clearDraftText();
      clearSavedDraftAttachments();
    }
    goHome();
    closeMobileIfOpen();
    if (typeof window !== "undefined") {
      window.setTimeout(() => {
        const el = document.querySelector<HTMLTextAreaElement>(
          "#home-problem-input, #composer-input, .composer-textarea",
        );
        el?.focus();
      }, 30);
    }
  };

  const handleSearchTriggerClick = () => {
    if (leftRailSearchOpen) {
      closeSearchModal(true);
    } else {
      openSearchModal();
    }
  };

  const handleOpenActionMenu = (
    e: React.MouseEvent<HTMLButtonElement>,
    item: UnifiedSidebarProblemItem,
  ) => {
    e.stopPropagation();
    setFilterMenuOpen(false);
    if (actionMenuState?.canonicalId === item.canonicalId) {
      setActionMenuState(null);
      return;
    }
    const btnRect = e.currentTarget.getBoundingClientRect();
    const menuWidth = 176;
    const menuHeight = 128;
    const vw = typeof window !== "undefined" ? window.innerWidth : 1440;
    const vh = typeof window !== "undefined" ? window.innerHeight : 900;
    const rawLeft = Math.round(btnRect.left - 4);
    const left =
      rawLeft + menuWidth > vw - 8
        ? Math.max(8, Math.round(vw - menuWidth - 8))
        : Math.max(8, rawLeft);
    const spaceBelow = vh - btnRect.bottom - 10;
    const shouldFlipUp = spaceBelow < menuHeight && btnRect.top >= menuHeight + 10;
    const top = shouldFlipUp
      ? Math.max(8, Math.round(btnRect.top - menuHeight - 4))
      : Math.round(btnRect.bottom + 4);
    setActionMenuState({
      canonicalId: item.canonicalId,
      top,
      left,
      placement: shouldFlipUp ? "top-right" : "bottom-right",
    });
  };

  const handleSubmitRename = (e: React.FormEvent) => {
    e.preventDefault();
    if (!renameModalState) return;
    const trimmed = renameModalState.draftTitle.trim();
    if (!trimmed) {
      setRenameModalState({
        ...renameModalState,
        error: "Tên bài toán không được để trống.",
      });
      return;
    }
    const ok = renameProblem(renameModalState.canonicalId, trimmed);
    if (ok) {
      setRenameModalState(null);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteModalState || deleteModalState.deleting) return;
    setDeleteModalState({ ...deleteModalState, deleting: true, error: null });
    const res = await deleteProblem(deleteModalState.item.canonicalId);
    if (!res.ok) {
      setDeleteModalState({
        ...deleteModalState,
        deleting: false,
        error: res.error ?? "Không thể xóa bài toán lúc này.",
      });
      return;
    }
    setDeleteModalState(null);
  };

  const handleSearchModalKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "ArrowDown") {
      if (searchPopupEntries.length === 0) return;
      e.preventDefault();
      const next = (selectedSearchIndex + 1) % searchPopupEntries.length;
      setSelectedSearchIndex(next);
      const itemEl = searchModalRef.current?.querySelector<HTMLElement>(
        `[data-search-result-idx="${next}"]`,
      );
      itemEl?.scrollIntoView({ block: "nearest" });
    } else if (e.key === "ArrowUp") {
      if (searchPopupEntries.length === 0) return;
      e.preventDefault();
      const prev =
        (selectedSearchIndex - 1 + searchPopupEntries.length) % searchPopupEntries.length;
      setSelectedSearchIndex(prev);
      const itemEl = searchModalRef.current?.querySelector<HTMLElement>(
        `[data-search-result-idx="${prev}"]`,
      );
      itemEl?.scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter") {
      const chosen = searchPopupEntries[selectedSearchIndex] ?? searchPopupEntries[0];
      if (chosen) {
        e.preventDefault();
        chosen.onSelect();
      }
    } else if (e.key === "Tab") {
      const focusable = Array.from(
        searchModalRef.current?.querySelectorAll<HTMLElement>(
          'input:not([disabled]), button:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      );
      if (focusable.length === 0) return;
      const first = focusable[0]!;
      const last = focusable[focusable.length - 1]!;
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  };

  const handleAccountPopoverKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const items = Array.from(
      accountPopoverRef.current?.querySelectorAll<HTMLButtonElement>('[role="menuitem"]') ?? [],
    );
    if (items.length === 0) return;
    const currentIndex = items.indexOf(document.activeElement as HTMLButtonElement);
    if (e.key === "ArrowDown") {
      e.preventDefault();
      const next = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
      items[next]?.focus();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      const prev = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
      items[prev]?.focus();
    } else if (e.key === "Home") {
      e.preventDefault();
      items[0]?.focus();
    } else if (e.key === "End") {
      e.preventDefault();
      items[items.length - 1]?.focus();
    }
  };

  const catalogCount = publicCatalog().length;

  return (
    <div
      className={`axo-left-sidebar-slot${isCollapsed ? " is-collapsed" : ""}`}
      data-sidebar-slot-state={sidebarState}
    >
      <div
        id="sb-drawer-backdrop"
        className={`sb-drawer-backdrop${leftRailMobileOpen ? " is-open" : ""}`}
        onClick={() => setLeftRailMobileOpen(false)}
        aria-hidden="true"
      />

      {/* Notion-style top-left trigger when sidebar is collapsed (hidden completely) */}
      <div
        ref={triggerZoneRef}
        id="sb-collapsed-trigger-zone"
        className={`sb-collapsed-trigger-zone${
          isCollapsed && !isMobileViewport ? " is-visible" : ""
        }${isHoverPreviewActive ? " is-preview-open" : ""}`}
        onMouseEnter={handleTriggerMouseEnter}
        onMouseLeave={handlePreviewZoneMouseLeave}
      >
        <button
          type="button"
          id="btn-sidebar-open-trigger"
          className="sb-open-trigger-btn"
          onClick={handlePinExpandFromCollapsed}
          title="Hiện thanh bên"
          aria-label="Hiện thanh bên"
          aria-expanded={!isCollapsed}
          aria-controls="left-sidebar"
          aria-hidden={isHoverPreviewActive || !isCollapsed || isMobileViewport ? "true" : undefined}
          tabIndex={isCollapsed && !isHoverPreviewActive && !isMobileViewport ? 0 : -1}
        >
          <IconSidebarCollapsedTrigger />
        </button>
      </div>

      <aside
        ref={sidebarRef}
        id="left-sidebar"
        data-sidebar-state={sidebarState}
        className={`axo-left-sidebar${isCollapsed ? " is-collapsed" : ""}${
          isHoverPreviewActive ? " is-hover-preview" : ""
        }${leftRailMobileOpen ? " is-mobile-open" : ""}`}
        aria-label="Điều hướng chính Axo"
        onMouseEnter={handlePanelMouseEnter}
        onMouseLeave={handlePreviewZoneMouseLeave}
      >
        {/* 1. HEADER: Brand + Search Icon + Collapse / Pin / Mobile close */}
        <div className="sb-top" id="sb-header">
          <button
            type="button"
            id="sb-brand-home"
            className="sb-brand"
            onClick={handleGoHome}
            title="Axo — Về màn hình nhập đề toán"
            aria-label="Axo — Về màn hình nhập đề toán"
          >
            <span className="sb-brand-logo" aria-hidden="true">
              <IconAxoLogo size={22} />
            </span>
            <span className="sb-brand-name">Axo</span>
          </button>

          <div className="sb-top-actions">
            <button
              ref={searchTriggerBtnRef}
              type="button"
              id="btn-sidebar-search"
              className={`sb-icon-btn sb-search-trigger-btn${leftRailSearchOpen ? " is-active" : ""}`}
              onClick={handleSearchTriggerClick}
              title={`Tìm bài toán (${shortcutLabel})`}
              aria-label="Tìm bài toán"
              aria-haspopup="dialog"
              aria-expanded={leftRailSearchOpen}
              aria-controls="axo-search-modal"
            >
              <svg
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <circle cx="9.1" cy="9.1" r="5.6" />
                <path d="M13.2 13.2L16.5 16.5" />
              </svg>
            </button>

            <button
              type="button"
              id="btn-sidebar-collapse"
              className="sb-icon-btn sb-sidebar-toggle-btn"
              onClick={() => {
                clearHoverCloseTimer();
                if (isHoverPreviewActive) {
                  handlePinExpandFromCollapsed();
                } else {
                  toggleLeftRailCollapsed(isCollapsed);
                }
              }}
              title={
                isHoverPreviewActive
                  ? "Ghim mở thanh bên"
                  : isCollapsed
                    ? "Hiện thanh bên"
                    : "Ẩn thanh bên"
              }
              aria-label={
                isHoverPreviewActive
                  ? "Ghim mở thanh bên"
                  : isCollapsed
                    ? "Hiện thanh bên"
                    : "Ẩn thanh bên"
              }
              aria-expanded={!isCollapsed || isHoverPreviewActive}
            >
              <IconSidebarToggle />
            </button>

            <button
              type="button"
              id="btn-sidebar-mobile-close"
              className="sb-icon-btn sb-mobile-close-btn"
              onClick={() => setLeftRailMobileOpen(false)}
              title="Đóng menu"
              aria-label="Đóng menu"
            >
              <svg
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
                strokeLinecap="round"
                aria-hidden="true"
              >
                <path d="M4.2 4.2l11.6 11.6M15.8 4.2l-11.6 11.6" />
              </svg>
            </button>
          </div>
        </div>

        {/* 2. PRIMARY NAVIGATION: Bài toán mới · Thư viện mô phỏng (+ Role Nav) */}
        <nav className="sb-primary-nav" aria-label="Điều hướng chính">
          <button
            type="button"
            id="nav-item-new-problem"
            className={`sb-nav-item${view === "home" ? " is-active" : ""}`}
            onClick={handleNewProblem}
            title="Bài toán mới"
          >
            <svg
              className="sb-nav-icon is-new-problem-icon"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M10 3.75H4.5a2 2 0 0 0-2 2v9.5a2 2 0 0 0 2 2h9.5a2 2 0 0 0 2-2V9.75" />
              <path d="M15.1 2.9a1.55 1.55 0 0 1 2.2 2.2L9.8 12.6l-2.8.7.7-2.8z" />
            </svg>
            <span className="sb-nav-label">Bài toán mới</span>
          </button>

          <button
            type="button"
            id="nav-item-library"
            className={`sb-nav-item${view === "library" ? " is-active" : ""}`}
            onClick={() => {
              openLibrary();
              closeMobileIfOpen();
            }}
            title="Thư viện mô phỏng"
          >
            <svg
              className="sb-nav-icon"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <rect x="2.8" y="2.8" width="5.8" height="5.8" rx="1.4" />
              <rect x="11.4" y="2.8" width="5.8" height="5.8" rx="1.4" />
              <rect x="2.8" y="11.4" width="5.8" height="5.8" rx="1.4" />
              <rect x="11.4" y="11.4" width="5.8" height="5.8" rx="1.4" />
            </svg>
            <span className="sb-nav-label">Thư viện mô phỏng</span>
            <span className="sb-nav-badge" id="sb-library-count">{catalogCount}</span>
          </button>

          {user?.role === "admin" && (
            <button
              type="button"
              id="nav-item-admin"
              className={`sb-nav-item${view === "admin" ? " is-active" : ""}`}
              onClick={() => {
                setView("admin");
                closeMobileIfOpen();
              }}
              title="Bảng điều khiển Quản trị"
            >
              <svg
                className="sb-nav-icon"
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M10 17.5s6.5-3 6.5-7.7V4.8L10 2.5 3.5 4.8v5c0 4.7 6.5 7.7 6.5 7.7z" />
              </svg>
              <span className="sb-nav-label">Bảng điều khiển Quản trị</span>
            </button>
          )}
        </nav>

        {/* 3. UNIFIED PROBLEM LIST: Bài toán (Scrollable region with native visible scrollbar) */}
        <div
          className="sb-scroll-region"
          id="sb-scroll-region"
          onScroll={() => {
            if (actionMenuState) setActionMenuState(null);
            if (filterMenuOpen) setFilterMenuOpen(false);
          }}
        >
          <div
            className={`sb-group${leftRailProblemGroupCollapsed ? " is-group-collapsed" : ""}`}
            id="sidebar-group-problems"
            data-group-collapsed={leftRailProblemGroupCollapsed ? "true" : "false"}
            data-problem-filter={leftRailProblemFilter}
          >
            <div className="sb-group-hdr">
              <button
                type="button"
                id="btn-toggle-group-problems"
                className="sb-group-toggle"
                onClick={toggleLeftRailProblemGroup}
                aria-expanded={!leftRailProblemGroupCollapsed}
                aria-controls="sb-problem-list"
                title={
                  leftRailProblemGroupCollapsed
                    ? "Mở rộng nhóm Bài toán"
                    : "Thu gọn nhóm Bài toán"
                }
              >
                <span className="sb-group-title">Bài toán</span>
                <span className="sb-group-count" id="sb-problem-count">
                  {unifiedSidebarItems.length}
                </span>
                <span className="sb-group-chevron" aria-hidden="true">
                  {leftRailProblemGroupCollapsed ? (
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.95" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M7.5 4.8L12.7 10 7.5 15.2" />
                    </svg>
                  ) : (
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.95" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M4.8 7.5L10 12.7 15.2 7.5" />
                    </svg>
                  )}
                </span>
              </button>

              <div className="sb-filter-anchor">
                <button
                  ref={filterBtnRef}
                  type="button"
                  id="btn-sidebar-problem-filter"
                  className={`sb-filter-trigger-btn${filterMenuOpen ? " is-open" : ""}${
                    leftRailProblemFilter !== "all" ? " is-filtered" : ""
                  }`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setActionMenuState(null);
                    setFilterMenuOpen((prev) => {
                      const next = !prev;
                      if (next) {
                        setFilterPopoverCoords(computeFilterPopoverPosition());
                        if (typeof window !== "undefined") {
                          window.setTimeout(() => {
                            filterPopoverRef.current
                              ?.querySelector<HTMLButtonElement>(
                                `[data-filter-value="${leftRailProblemFilter}"], [role="menuitemradio"]`,
                              )
                              ?.focus();
                          }, 20);
                        }
                      }
                      return next;
                    });
                  }}
                  title={`Lọc danh sách bài toán (${FILTER_LABELS[leftRailProblemFilter]})`}
                  aria-label={`Lọc bài toán: ${FILTER_LABELS[leftRailProblemFilter]}`}
                  aria-haspopup="menu"
                  aria-expanded={filterMenuOpen}
                  aria-controls="sb-problem-filter-popover"
                >
                  <svg
                    viewBox="0 0 20 20"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.85"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <path d="M3 5.2h14M6 10h8M8.5 14.8h3" />
                  </svg>
                  <span id="sb-problem-filter-label">{FILTER_LABELS[leftRailProblemFilter]}</span>
                </button>
              </div>
            </div>

            <div
              className={`sb-problem-list${leftRailProblemGroupCollapsed ? " is-collapsed" : ""}`}
              id="sb-problem-list"
              role="list"
              hidden={leftRailProblemGroupCollapsed}
            >
              {unifiedSidebarItems.length === 0 ? (
                <div className="sb-empty-state" id="sb-problem-empty">
                  {leftRailProblemFilter === "ready"
                    ? "Chưa có bài toán nào ở trạng thái Sẵn sàng."
                    : leftRailProblemFilter === "needs_attention"
                      ? "Không có bài toán nào Cần chú ý."
                      : leftRailProblemFilter === "in_progress"
                        ? "Không có bài toán nào Đang tiến hành."
                        : "Chưa có bài toán nào."}
                  <div>
                    <button
                      type="button"
                      className="sb-empty-cta"
                      onClick={handleNewProblem}
                    >
                      + Mở bài toán mới
                    </button>
                  </div>
                </div>
              ) : (
                unifiedSidebarItems.map((item) => {
                  const isMenuOpen = actionMenuState?.canonicalId === item.canonicalId;
                  const itemFamily =
                    (
                      item as UnifiedSidebarProblemItem & {
                        geometryFamily?: GeometrySolidFamily;
                      }
                    ).geometryFamily ??
                    resolveGeometrySolidFamily({
                      envelope:
                        item.openTab?.active?.envelope ?? item.historyItem?.envelope,
                      sampleId: item.openTab?.sampleId,
                      problemStatement: item.problemStatement,
                      title: item.title,
                    });
                  return (
                    <div
                      key={item.canonicalId}
                      role="listitem"
                      data-sidebar-problem-id={item.canonicalId}
                      data-sidebar-active-tab={item.openTab?.id ?? undefined}
                      data-sidebar-recent-id={item.isInHistory ? item.canonicalId : undefined}
                      data-pinned={item.pinned ? "true" : "false"}
                      data-processing-status={item.processingStatus}
                      data-geometry-family={itemFamily}
                      className={`sb-problem-item${item.isCurrentActiveTab ? " is-current" : ""}${
                        item.pinned ? " is-pinned" : ""
                      }${isMenuOpen ? " is-menu-open" : ""} is-status-${item.processingStatus}`}
                      title={item.title}
                      onClick={() => handleSelectProblemItem(item)}
                    >
                      <span
                        className={`sb-item-geo-icon is-status-${item.processingStatus}`}
                        data-geometry-family={itemFamily}
                        aria-hidden="true"
                      >
                        {item.processingStatus === "in_progress" ? (
                          <svg
                            className="sb-item-status-spinner"
                            viewBox="0 0 16 16"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.65"
                            strokeLinecap="round"
                          >
                            <circle cx="8" cy="8" r="5.2" strokeOpacity="0.25" />
                            <path d="M8 2.8a5.2 5.2 0 0 1 5.2 5.2" />
                          </svg>
                        ) : item.processingStatus === "needs_attention" ? (
                          <svg
                            viewBox="0 0 16 16"
                            fill="none"
                            stroke="#D9730D"
                            strokeWidth="1.55"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          >
                            <path d="M3.5 2.5v11" />
                            <path
                              d="M3.5 3.2h8l-1.9 2.8 1.9 2.8h-8"
                              fill="rgba(217, 115, 13, 0.16)"
                            />
                          </svg>
                        ) : item.kind === "draft" && itemFamily === "neutral" ? (
                          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <path d="M8 3.5v9M3.5 8h9" strokeLinecap="round" />
                          </svg>
                        ) : (
                          <GeometryFamilyIcon family={itemFamily} />
                        )}
                      </span>

                      <div className="sb-item-body">
                        {item.pinned && (
                          <span
                            className="sb-item-pin-badge"
                            title="Đã ghim lên đầu"
                            aria-label="Đã ghim"
                          >
                            <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                              <path d="M9.8 2.1a1 1 0 0 1 1.4 0l2.7 2.7a1 1 0 0 1-.4 1.6l-2.1.7-2.2 2.2.4 2.5a.8.8 0 0 1-1.3.6L5.8 9.9 2.9 12.8a.75.75 0 1 1-1.1-1.1L4.7 8.8 2.2 6.3a.8.8 0 0 1 .6-1.3l2.5.4 2.2-2.2.7-2.1a1 1 0 0 1 1.6-.4z" />
                            </svg>
                          </span>
                        )}
                        <span className="sb-item-title" title={item.title}>
                          {item.title}
                        </span>
                      </div>

                      <div className="sb-item-trailing">
                        <button
                          type="button"
                          className={`sb-item-more-btn${isMenuOpen ? " is-menu-open" : ""}`}
                          data-problem-more-btn={item.canonicalId}
                          title={`Tùy chọn cho ${item.title}`}
                          aria-label={`Tùy chọn cho ${item.title}`}
                          aria-haspopup="menu"
                          aria-expanded={isMenuOpen}
                          onClick={(e) => handleOpenActionMenu(e, item)}
                        >
                          <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                            <circle cx="8" cy="3.4" r="1.35" />
                            <circle cx="8" cy="8" r="1.35" />
                            <circle cx="8" cy="12.6" r="1.35" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* 4. FOOTER (Fixed at bottom): Real User Account + Account Menu Popover */}
        <div className="sb-footer" id="sb-footer">
          {user !== null ? (
            <div className="sb-account-container">
              {accountMenuOpen && (
                <div
                  ref={accountPopoverRef}
                  id="sb-account-popover"
                  className="sb-account-popover"
                  role="menu"
                  aria-label="Tài khoản người dùng"
                  onKeyDown={handleAccountPopoverKeyDown}
                >
                  <div className="sb-account-popover-head">
                    <div className="sb-account-popover-name" title={user.displayName || user.email}>
                      {user.displayName || user.email}
                    </div>
                    <div className="sb-account-popover-email" title={user.email}>
                      {user.email}
                    </div>
                  </div>
                  <div className="sb-account-popover-sep" role="separator" />
                  {user.role === "admin" && (
                    <button
                      type="button"
                      role="menuitem"
                      id="btn-sb-acc-admin"
                      className="sb-account-popover-item"
                      onClick={() => {
                        setAccountMenuOpen(false);
                        setView("admin");
                        closeMobileIfOpen();
                      }}
                    >
                      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <path d="M10 17.5s6.5-3 6.5-7.7V4.8L10 2.5 3.5 4.8v5c0 4.7 6.5 7.7 6.5 7.7z" />
                      </svg>
                      <span>Bảng điều khiển Quản trị</span>
                    </button>
                  )}
                  <button
                    type="button"
                    role="menuitem"
                    id="btn-sb-acc-profile"
                    className="sb-account-popover-item"
                    onClick={() => {
                      setAccountMenuOpen(false);
                      openAccountModal("profile");
                      closeMobileIfOpen();
                    }}
                  >
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <circle cx="10" cy="6.8" r="3.1" />
                      <path d="M4.3 16.5c1.1-2.8 3.1-4.1 5.7-4.1s4.6 1.3 5.7 4.1" />
                    </svg>
                    <span>Hồ sơ</span>
                  </button>
                  <button
                    type="button"
                    role="menuitem"
                    id="btn-sb-acc-settings"
                    className="sb-account-popover-item"
                    onClick={() => {
                      setAccountMenuOpen(false);
                      openAccountModal("security");
                      closeMobileIfOpen();
                    }}
                  >
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <circle cx="10" cy="10" r="2.75" />
                      <path d="M10 2.8v1.7M10 15.5v1.7M2.8 10h1.7M15.5 10h1.7M4.9 4.9l1.2 1.2M13.9 13.9l1.2 1.2M15.1 4.9l-1.2 1.2M6.1 13.9l-1.2 1.2" />
                    </svg>
                    <span>Cài đặt</span>
                  </button>
                  <div className="sb-account-popover-sep" role="separator" />
                  <button
                    type="button"
                    role="menuitem"
                    id="btn-sb-acc-logout"
                    className="sb-account-popover-item is-danger"
                    onClick={() => {
                      setAccountMenuOpen(false);
                      closeMobileIfOpen();
                      setGuestEnteredApp(false);
                      void logout().then(() => {
                        goHome();
                      });
                    }}
                  >
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M8 3.25H4.75a1.5 1.5 0 0 0-1.5 1.5v10.5a1.5 1.5 0 0 0 1.5 1.5H8" />
                      <path d="M8 10h8.75M13.5 6.75L16.75 10l-3.25 3.25" />
                    </svg>
                    <span>Đăng xuất</span>
                  </button>
                </div>
              )}

              <button
                ref={accountBtnRef}
                type="button"
                id="sb-user-account-btn"
                className={`sb-user-row${accountMenuOpen ? " is-menu-open" : ""}`}
                aria-haspopup="menu"
                aria-expanded={accountMenuOpen}
                aria-controls="sb-account-popover"
                onClick={() => {
                  const next = !accountMenuOpen;
                  setAccountMenuOpen(next);
                  if (next && typeof window !== "undefined") {
                    window.setTimeout(() => {
                      accountPopoverRef.current
                        ?.querySelector<HTMLButtonElement>('[role="menuitem"]')
                        ?.focus();
                    }, 20);
                  }
                }}
                title={user.displayName || user.email}
              >
                <span className="sb-avatar" aria-hidden="true">
                  {getInitials(user.displayName || user.email)}
                </span>
                <span className="sb-user-meta">
                  <span className="sb-user-name">{user.displayName || user.email}</span>
                  <span className="sb-user-role">
                    {user.role === "teacher"
                      ? "Giáo viên"
                      : user.role === "admin"
                        ? "Quản trị viên"
                        : "Học sinh"}
                  </span>
                </span>
                <span className="sb-user-menu-icon" aria-hidden="true">
                  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M6.5 8L10 4.5 13.5 8M6.5 12L10 15.5 13.5 12" />
                  </svg>
                </span>
              </button>
            </div>
          ) : !authResolved ? (
            <div
              id="sb-auth-loading-row"
              className="sb-account-anchor sb-auth-loading-row"
              aria-busy="true"
              aria-live="polite"
            >
              <span className="sb-auth-loading-skeleton" aria-hidden="true" />
            </div>
          ) : (
            <div className="sb-account-anchor" ref={guestSidebarRowRef}>
              <button
                id="sb-guest-account-btn"
                type="button"
                className="sb-guest-login-btn"
                onClick={() => {
                  setView("login");
                  closeMobileIfOpen();
                }}
                aria-label="Đăng nhập"
              >
                <span className="sb-guest-login-icon" aria-hidden="true">
                  <svg width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="10" cy="6.8" r="3.1" />
                    <path d="M4.3 16.5c1.1-2.8 3.1-4.1 5.7-4.1s4.6 1.3 5.7 4.1" />
                  </svg>
                </span>
                <span className="sb-guest-login-label">Đăng nhập</span>
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* V6 PHASE 1 & 2 — PROCESSING STATUS FILTER POPOVER (Right-opening, non-overlapping) */}
      {filterMenuOpen && (
        <div
          ref={filterPopoverRef}
          id="sb-problem-filter-popover"
          className="sb-filter-popover"
          role="menu"
          aria-label="Bộ lọc trạng thái bài toán"
          data-placement={filterPopoverCoords.placement}
          style={{
            top: `${filterPopoverCoords.top}px`,
            left: `${filterPopoverCoords.left}px`,
          }}
          onMouseEnter={handlePanelMouseEnter}
          onMouseLeave={handlePreviewZoneMouseLeave}
          onKeyDown={handleFilterPopoverKeyDown}
        >
          {FILTER_OPTIONS_ORDER.map((filterVal) => {
            const isSelected = leftRailProblemFilter === filterVal;
            return (
              <button
                key={filterVal}
                type="button"
                id={`filter-opt-${filterVal}`}
                role="menuitemradio"
                aria-checked={isSelected}
                data-filter-value={filterVal}
                className={`sb-filter-option${isSelected ? " is-selected" : ""}`}
                onClick={(e) => {
                  e.stopPropagation();
                  setLeftRailProblemFilter(filterVal);
                  setFilterMenuOpen(false);
                }}
              >
                <span className="sb-filter-opt-main">
                  <IconFilterOption filter={filterVal} />
                  <span className="sb-filter-opt-label">{FILTER_LABELS[filterVal]}</span>
                </span>
                {isSelected && (
                  <span className="sb-filter-check" aria-hidden="true">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M3.5 8.5l3 3 6-6.5" />
                    </svg>
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* V7 PHASE 2 — PROBLEM MANAGEMENT 3-DOT MENU POPOVER (Opens below ⋮, extends right) */}
      {actionMenuState && activeActionMenuItem && (
        <div
          ref={actionMenuPopoverRef}
          id="sb-problem-action-menu"
          className="sb-action-menu-popover"
          role="menu"
          aria-label={`Quản lý ${activeActionMenuItem.title}`}
          data-placement={actionMenuState.placement}
          style={{
            top: `${actionMenuState.top}px`,
            left: `${actionMenuState.left}px`,
          }}
          onMouseEnter={handlePanelMouseEnter}
          onMouseLeave={handlePreviewZoneMouseLeave}
        >
          <button
            type="button"
            id="menu-action-pin"
            role="menuitem"
            className="sb-action-menu-item"
            onClick={(e) => {
              e.stopPropagation();
              togglePinProblem(activeActionMenuItem.canonicalId);
              setActionMenuState(null);
            }}
          >
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M9.5 2.5l4 4-1.5 1.5-2.5-.5-2.5 2.5.5 2.5-1.5 1.5-3-3-3 3M6.5 9.5l-3-3 1.5-1.5 2.5.5 2.5-2.5-.5-2.5z" />
            </svg>
            <span>{activeActionMenuItem.pinned ? "Bỏ ghim" : "Ghim"}</span>
          </button>

          <button
            type="button"
            id="menu-action-rename"
            role="menuitem"
            className="sb-action-menu-item"
            onClick={(e) => {
              e.stopPropagation();
              setRenameModalState({
                canonicalId: activeActionMenuItem.canonicalId,
                currentTitle: activeActionMenuItem.title,
                draftTitle: activeActionMenuItem.title,
                error: null,
              });
              setActionMenuState(null);
            }}
          >
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M11.2 2.5l2.3 2.3-8.3 8.3-3 .7.7-3 8.3-8.3z" />
            </svg>
            <span>Đổi tên</span>
          </button>

          <div className="sb-action-menu-sep" role="separator" />

          <button
            type="button"
            id="menu-action-delete"
            role="menuitem"
            className="sb-action-menu-item is-danger"
            onClick={(e) => {
              e.stopPropagation();
              setDeleteModalState({
                item: activeActionMenuItem,
                deleting: false,
                error: null,
              });
              setActionMenuState(null);
            }}
          >
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M3 4.2h10M6.2 4.2V2.8h3.6v1.4M4.3 4.2l.6 9a1.2 1.2 0 0 0 1.2 1.1h3.8a1.2 1.2 0 0 0 1.2-1.1l.6-9" />
            </svg>
            <span>Xóa</span>
          </button>
        </div>
      )}

      {/* V5 PHASE 7.2 — RENAME PROBLEM MODAL */}
      {renameModalState && (
        <div
          id="sb-problem-rename-backdrop"
          className="sb-manage-modal-backdrop"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) {
              setRenameModalState(null);
            }
          }}
        >
          <form
            id="sb-problem-rename-modal"
            className="sb-manage-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="sb-rename-modal-title"
            onSubmit={handleSubmitRename}
          >
            <h3 id="sb-rename-modal-title" className="sb-manage-modal-title">
              Đổi tên bài toán
            </h3>
            <p className="sb-manage-modal-desc">
              Tên hiển thị mới sẽ được cập nhật trên thanh bên, tìm kiếm, lịch sử và tab đang mở (không làm thay đổi đề gốc hay hình học 3D).
            </p>
            <input
              ref={renameInputRef}
              id="sb-rename-input"
              className="sb-manage-modal-input"
              type="text"
              value={renameModalState.draftTitle}
              onChange={(e) =>
                setRenameModalState({
                  ...renameModalState,
                  draftTitle: e.target.value,
                  error: null,
                })
              }
              placeholder="Nhập tên bài toán..."
              aria-label="Tên bài toán mới"
              autoComplete="off"
            />
            {renameModalState.error && (
              <p id="sb-rename-error" className="sb-manage-modal-error" role="alert">
                {renameModalState.error}
              </p>
            )}
            <div className="sb-manage-modal-actions">
              <button
                type="button"
                id="btn-cancel-rename-problem"
                className="sb-manage-btn-cancel"
                onClick={() => setRenameModalState(null)}
              >
                Hủy
              </button>
              <button
                type="submit"
                id="btn-confirm-rename-problem"
                className="sb-manage-btn-primary"
                disabled={renameModalState.draftTitle.trim().length === 0}
              >
                Lưu tên mới
              </button>
            </div>
          </form>
        </div>
      )}

      {/* V5 PHASE 7.3 — DELETE PROBLEM CONFIRMATION MODAL */}
      {deleteModalState && (
        <div
          id="sb-problem-delete-backdrop"
          className="sb-manage-modal-backdrop"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget && !deleteModalState.deleting) {
              setDeleteModalState(null);
            }
          }}
        >
          <div
            id="sb-problem-delete-modal"
            className="sb-manage-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="sb-delete-modal-title"
          >
            <h3 id="sb-delete-modal-title" className="sb-manage-modal-title">
              Xóa bài toán này?
            </h3>
            <p className="sb-manage-modal-desc">
              Bạn sắp xóa <strong>“{deleteModalState.item.title}”</strong> khỏi danh sách bài toán cá nhân và lịch sử học tập.
              {deleteModalState.item.isOpenInTab
                ? " Tab đang mở của bài toán này trong Workspace cũng sẽ được đóng."
                : ""}
            </p>
            {deleteModalState.error && (
              <p id="sb-delete-error" className="sb-manage-modal-error" role="alert">
                {deleteModalState.error}
              </p>
            )}
            <div className="sb-manage-modal-actions">
              <button
                type="button"
                id="btn-cancel-delete-problem"
                className="sb-manage-btn-cancel"
                disabled={deleteModalState.deleting}
                onClick={() => setDeleteModalState(null)}
              >
                Hủy
              </button>
              <button
                type="button"
                id="btn-confirm-delete-problem"
                className="sb-manage-btn-danger"
                disabled={deleteModalState.deleting}
                onClick={() => void handleConfirmDelete()}
              >
                {deleteModalState.deleting ? "Đang xóa..." : "Xóa bài toán"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* GEMINI-STYLE SEARCH POPUP MODAL (Light Mode) */}
      {leftRailSearchOpen && (
        <div
          id="axo-search-backdrop"
          className="axo-search-backdrop"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) {
              closeSearchModal(true);
            }
          }}
        >
          <div
            ref={searchModalRef}
            id="axo-search-modal"
            className="axo-search-modal"
            role="dialog"
            aria-modal="true"
            aria-label="Tìm bài toán"
            onKeyDown={handleSearchModalKeyDown}
          >
            <div className="axo-search-modal-header">
              <span className="axo-search-modal-icon" aria-hidden="true">
                <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round">
                  <circle cx="8" cy="8" r="5.2" />
                  <path d="M12 12l3.6 3.6" />
                </svg>
              </span>
              <input
                ref={searchInputRef}
                id="axo-search-modal-input"
                className="axo-search-modal-input"
                type="text"
                value={leftRailSearchQuery}
                onChange={(e) => setLeftRailSearchQuery(e.target.value)}
                placeholder="Tìm bài toán đang học, gần đây hoặc thư viện..."
                aria-label="Nhập từ khóa tìm bài toán"
                autoComplete="off"
              />
              {leftRailSearchQuery && (
                <button
                  type="button"
                  id="btn-clear-search-query"
                  className="axo-search-clear-btn"
                  onClick={() => {
                    setLeftRailSearchQuery("");
                    searchInputRef.current?.focus();
                  }}
                  title="Xóa từ khóa"
                  aria-label="Xóa từ khóa"
                >
                  Đặt lại
                </button>
              )}
              <button
                type="button"
                id="btn-close-search-modal"
                className="axo-search-close-btn"
                onClick={() => closeSearchModal(true)}
                title="Đóng tìm kiếm (Esc)"
                aria-label="Đóng tìm kiếm"
              >
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" aria-hidden="true">
                  <path d="M4 4l8 8M12 4l-8 8" />
                </svg>
              </button>
            </div>

            <div className="axo-search-modal-body" id="axo-search-results-scroll">
              <div className="axo-search-section-label" id="axo-search-section-label">
                {hasQuery
                  ? `Kết quả phù hợp (${searchPopupEntries.length})`
                  : effectiveTabs.length > 0 || history.length > 0
                    ? "Gần đây"
                    : "Gợi ý từ Thư viện mô phỏng"}
              </div>

              {searchPopupEntries.length === 0 ? (
                <div className="axo-search-empty-state" id="axo-search-empty-state">
                  <p className="axo-search-empty-title">
                    {`Không tìm thấy bài toán nào khớp với “${leftRailSearchQuery.trim()}”.`}
                  </p>
                  <p className="axo-search-empty-sub">
                    Thử tìm theo tên khối hình (chóp, lăng trụ, lập phương, mặt cầu) hoặc dạng bài (thiết diện, khoảng cách, góc).
                  </p>
                </div>
              ) : (
                <div className="axo-search-results-list" role="listbox" aria-label="Danh sách bài toán">
                  {searchPopupEntries.map((entry, idx) => {
                    const isSelected = idx === selectedSearchIndex;
                    return (
                      <button
                        key={entry.key}
                        type="button"
                        role="option"
                        aria-selected={isSelected}
                        data-search-result-idx={idx}
                        data-search-source={entry.source}
                        data-geometry-family={entry.geometryFamily}
                        className={`axo-search-result-item${isSelected ? " is-selected" : ""}`}
                        onMouseEnter={() => setSelectedSearchIndex(idx)}
                        onClick={entry.onSelect}
                        title={entry.title}
                      >
                        <span
                          className={`axo-search-item-icon is-${entry.source}`}
                          data-geometry-family={entry.geometryFamily}
                          aria-hidden="true"
                        >
                          <GeometryFamilyIcon family={entry.geometryFamily} />
                        </span>
                        <span className="axo-search-item-main">
                          <span className="axo-search-item-title">{entry.title}</span>
                          <span className="axo-search-item-sub">{entry.subtitle}</span>
                        </span>
                        <span className="axo-search-item-badge">{entry.badgeText}</span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
