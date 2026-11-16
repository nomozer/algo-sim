import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
  type WheelEvent,
} from "react";
import { createPortal } from "react-dom";
import {
  resolveEffectiveWorkspaceTabs,
  resolveWorkspaceTabGeometryFamily,
  useAppStore,
} from "../state/store";
import {
  buildProjectedWorkspaceTabs,
  LIBRARY_RESOURCE_KEY,
  LIBRARY_TAB_ID,
} from "../state/workspace-tab-identity";
import { GeometryFamilyIcon } from "./family-icons";
import { IconSidebarCollapsedTrigger } from "./LeftSidebar";
import {
  IconChevronRight,
  IconClose,
  IconFileDoc,
  IconLibrary,
  IconPlus,
} from "./icons";

export interface WorkspaceTabBarProps {
  readonly fallbackTitle?: string;
}

interface TabTooltipState {
  readonly resourceKey: string;
  readonly text: string;
  readonly anchorRect: {
    readonly left: number;
    readonly right: number;
    readonly top: number;
    readonly bottom: number;
    readonly width: number;
  };
}

export function WorkspaceTabBar({ fallbackTitle }: WorkspaceTabBarProps) {
  const view = useAppStore((s) => s.view);
  const workspaceTabs = useAppStore((s) => s.workspaceTabs);
  const activeTabId = useAppStore((s) => s.activeTabId);
  const active = useAppStore((s) => s.active);
  const activeSampleId = useAppStore((s) => s.activeSampleId);
  const activeHistoryId = useAppStore((s) => s.activeHistoryId);
  const leftRailMobileOpen = useAppStore((s) => s.leftRailMobileOpen);
  const libraryTabOpen = useAppStore((s) => s.libraryTabOpen);
  const workspaceNavStack = useAppStore((s) => s.workspaceNavStack);
  const workspaceNavIndex = useAppStore((s) => s.workspaceNavIndex);
  const activateWorkspaceTab = useAppStore((s) => s.activateWorkspaceTab);
  const closeWorkspaceTab = useAppStore((s) => s.closeWorkspaceTab);
  const openDraftWorkspaceTab = useAppStore((s) => s.openDraftWorkspaceTab);
  const openLibrary = useAppStore((s) => s.openLibrary);
  const workspaceGoBack = useAppStore((s) => s.workspaceGoBack);
  const workspaceGoForward = useAppStore((s) => s.workspaceGoForward);

  const stripRef = useRef<HTMLDivElement>(null);
  const tabElsRef = useRef<Map<string, HTMLDivElement>>(new Map());
  const tooltipElRef = useRef<HTMLDivElement>(null);
  const tooltipId = useId();
  const [tooltip, setTooltip] = useState<TabTooltipState | null>(null);
  const [tooltipCoords, setTooltipCoords] = useState<{ left: number; top: number } | null>(null);

  const { tabs: effectiveTabs, activeTabId: resolvedActiveTabId } =
    resolveEffectiveWorkspaceTabs({
      workspaceTabs,
      activeTabId,
      active,
      activeSampleId,
      activeHistoryId,
    });

  const projectedTabs = buildProjectedWorkspaceTabs(
    effectiveTabs,
    libraryTabOpen,
    fallbackTitle,
  );

  const activeResourceKey =
    view === "library"
      ? projectedTabs.find((t) => t.kind === "library")?.resourceKey ?? LIBRARY_RESOURCE_KEY
      : projectedTabs.find((t) => t.kind !== "library" && t.id === resolvedActiveTabId)?.resourceKey ?? null;

  const canGoBack = true;
  const canGoForward = workspaceNavIndex < workspaceNavStack.length - 1;

  const setTabRef = useCallback((resourceKey: string, el: HTMLDivElement | null) => {
    if (el) {
      tabElsRef.current.set(resourceKey, el);
    } else {
      tabElsRef.current.delete(resourceKey);
    }
  }, []);

  const ensureTabVisibleInStrip = useCallback((el: HTMLElement | null | undefined) => {
    const strip = stripRef.current;
    if (!strip || !el) return;
    if (!(strip.clientWidth > 0) || !(strip.scrollWidth > strip.clientWidth)) return;
    const stripRect = strip.getBoundingClientRect();
    const elRect = el.getBoundingClientRect();
    let nextLeft: number | null = null;
    if (stripRect.width > 0 && elRect.width > 0) {
      if (elRect.left < stripRect.left + 4) {
        nextLeft = Math.max(0, strip.scrollLeft + (elRect.left - stripRect.left) - 8);
      } else if (elRect.right > stripRect.right - 4) {
        nextLeft = Math.max(0, strip.scrollLeft + (elRect.right - stripRect.right) + 8);
      }
    } else {
      const elLeft = el.offsetLeft;
      const elRight = elLeft + el.offsetWidth;
      const viewLeft = strip.scrollLeft;
      const viewRight = viewLeft + strip.clientWidth;
      if (elLeft < viewLeft + 4) {
        nextLeft = Math.max(0, elLeft - 8);
      } else if (elRight > viewRight - 4) {
        nextLeft = Math.max(0, elRight - strip.clientWidth + 8);
      }
    }
    if (nextLeft !== null) {
      if (typeof strip.scrollTo === "function") {
        strip.scrollTo({ left: nextLeft, behavior: "auto" });
      } else {
        strip.scrollLeft = nextLeft;
      }
    }
  }, []);

  useEffect(() => {
    if (!activeResourceKey) return;
    const el = tabElsRef.current.get(activeResourceKey);
    ensureTabVisibleInStrip(el);
  }, [activeResourceKey, projectedTabs.length, ensureTabVisibleInStrip]);

  useEffect(() => {
    const strip = stripRef.current;
    if (!strip || !activeResourceKey) return;
    let rafId: number | null = null;
    const syncActiveVisibility = () => {
      if (rafId !== null && typeof cancelAnimationFrame === "function") {
        cancelAnimationFrame(rafId);
      }
      if (typeof requestAnimationFrame === "function") {
        rafId = requestAnimationFrame(() => {
          rafId = null;
          const el = tabElsRef.current.get(activeResourceKey);
          ensureTabVisibleInStrip(el);
        });
      } else {
        const el = tabElsRef.current.get(activeResourceKey);
        ensureTabVisibleInStrip(el);
      }
    };
    const observer =
      typeof ResizeObserver !== "undefined" ? new ResizeObserver(syncActiveVisibility) : null;
    observer?.observe(strip);
    if (typeof window !== "undefined") {
      window.addEventListener("resize", syncActiveVisibility);
    }
    return () => {
      observer?.disconnect();
      if (typeof window !== "undefined") {
        window.removeEventListener("resize", syncActiveVisibility);
      }
      if (rafId !== null && typeof cancelAnimationFrame === "function") {
        cancelAnimationFrame(rafId);
      }
    };
  }, [activeResourceKey, ensureTabVisibleInStrip]);

  useEffect(() => {
    if (!tooltip) {
      setTooltipCoords(null);
      return;
    }
    const stillExists = projectedTabs.some((t) => t.resourceKey === tooltip.resourceKey);
    if (!stillExists) {
      setTooltip(null);
    }
  }, [projectedTabs, tooltip]);

  useEffect(() => {
    if (!tooltip || typeof window === "undefined") {
      setTooltipCoords(null);
      return;
    }
    const vw = window.innerWidth || 1280;
    const vh = window.innerHeight || 720;
    const measuredW = tooltipElRef.current?.offsetWidth ?? 0;
    const tipWidth = measuredW > 0 ? measuredW : Math.min(360, vw - 20);
    const tipHeight = tooltipElRef.current?.offsetHeight || 32;
    const center = tooltip.anchorRect.left + tooltip.anchorRect.width / 2;
    const clampedLeft = Math.max(10, Math.min(vw - tipWidth - 10, center - tipWidth / 2));
    const preferredTop = tooltip.anchorRect.bottom + 6;
    const clampedTop =
      preferredTop + tipHeight <= vh - 8
        ? preferredTop
        : Math.max(8, tooltip.anchorRect.top - tipHeight - 6);
    setTooltipCoords({
      left: Math.round(clampedLeft),
      top: Math.round(clampedTop),
    });
  }, [tooltip]);

  const showTooltipForTab = useCallback(
    (resourceKey: string, text: string, el: HTMLDivElement | null) => {
      if (!el || !text.trim()) return;
      const r = el.getBoundingClientRect();
      const vw = typeof window !== "undefined" ? window.innerWidth || 1280 : 1280;
      const fallbackW = Math.min(360, vw - 20);
      setTooltipCoords({
        left: Math.round(Math.max(10, Math.min(vw - fallbackW - 10, r.left))),
        top: Math.round(r.bottom + 6),
      });
      setTooltip({
        resourceKey,
        text,
        anchorRect: {
          left: r.left,
          right: r.right,
          top: r.top,
          bottom: r.bottom,
          width: r.width,
        },
      });
    },
    [],
  );

  const hideTooltipForTab = useCallback((resourceKey?: string) => {
    setTooltip((prev) => {
      if (!prev) return null;
      if (resourceKey && prev.resourceKey !== resourceKey) return prev;
      return null;
    });
  }, []);

  const activateProjectedTab = (id: string, kind: "library" | "simulation" | "draft") => {
    setTooltip(null);
    if (kind === "library" || id === LIBRARY_TAB_ID) {
      openLibrary();
      return;
    }
    activateWorkspaceTab(id);
  };

  const handleOpenNewTab = () => {
    setTooltip(null);
    openDraftWorkspaceTab();
    if (typeof document !== "undefined") {
      setTimeout(() => {
        const input =
          (document.getElementById("composer-input") as HTMLTextAreaElement | null) ??
          (document.getElementById("home-problem-input") as HTMLTextAreaElement | null);
        input?.focus();
      }, 40);
    }
  };

  const handleCloseTab = (id: string) => {
    setTooltip(null);
    closeWorkspaceTab(id);
  };

  const handleStripWheel = (e: WheelEvent<HTMLDivElement>) => {
    const strip = stripRef.current;
    if (!strip || strip.scrollWidth <= strip.clientWidth) return;
    if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
      strip.scrollLeft += e.deltaY;
      setTooltip(null);
    }
  };

  const handleTabKeyDown = (
    e: KeyboardEvent<HTMLDivElement>,
    idx: number,
    id: string,
    kind: "library" | "simulation" | "draft",
  ) => {
    if (e.target !== e.currentTarget) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      activateProjectedTab(id, kind);
      return;
    }
    if (e.key === "Escape") {
      setTooltip(null);
      return;
    }
    let nextIdx: number | null = null;
    if (e.key === "ArrowRight") {
      nextIdx = (idx + 1) % projectedTabs.length;
    } else if (e.key === "ArrowLeft") {
      nextIdx = (idx - 1 + projectedTabs.length) % projectedTabs.length;
    } else if (e.key === "Home") {
      nextIdx = 0;
    } else if (e.key === "End") {
      nextIdx = projectedTabs.length - 1;
    }
    if (nextIdx !== null && projectedTabs[nextIdx]) {
      e.preventDefault();
      const targetTab = projectedTabs[nextIdx];
      const nextEl = tabElsRef.current.get(targetTab.resourceKey);
      if (nextEl) {
        ensureTabVisibleInStrip(nextEl);
        nextEl.focus();
      }
    }
  };

  return (
    <header
      className="axo-header ws-axo-header"
      data-ws-tab-bar="true"
      role="banner"
      aria-label="Thanh tab bài toán"
    >
      <button
        type="button"
        id="btn-mobile-open-ws"
        className={`btn-mobile-drawer-trigger ws-mobile-drawer-btn${
          leftRailMobileOpen ? " is-hidden-when-drawer-open" : ""
        }`}
        onClick={() => useAppStore.getState().setLeftRailMobileOpen(true)}
        aria-label="Mở điều hướng"
        title="Mở điều hướng"
        aria-hidden={leftRailMobileOpen ? "true" : undefined}
        tabIndex={leftRailMobileOpen ? -1 : undefined}
      >
        <IconSidebarCollapsedTrigger />
      </button>

      <div className="ws-tabbar-nav" role="group" aria-label="Điều hướng lịch sử">
        <button
          type="button"
          className="ws-nav-arrow-btn btn-ws-back"
          id="btn-ws-back"
          disabled={!canGoBack}
          title="Quay lại"
          aria-label="Quay lại"
          onClick={workspaceGoBack}
        >
          <svg
            viewBox="0 0 16 16"
            width="13"
            height="13"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M10.2 3.2L5.4 8l4.8 4.8" />
          </svg>
        </button>
        <button
          type="button"
          className="ws-nav-arrow-btn btn-ws-forward"
          id="btn-ws-forward"
          disabled={!canGoForward}
          title="Tiếp theo"
          aria-label="Tiếp theo"
          onClick={workspaceGoForward}
        >
          <IconChevronRight size={13} />
        </button>
      </div>

      <div className="header-div ws-tabbar-div" id="header-prob-div" aria-hidden="true" />

      <div
        ref={stripRef}
        className="ws-tabbar-strip"
        role="tablist"
        aria-label="Các bài toán đang mở"
        onWheel={handleStripWheel}
      >
        {projectedTabs.map((ptab, idx) => {
          const isActive =
            ptab.kind === "library"
              ? view === "library"
              : view === "workspace" && ptab.id === resolvedActiveTabId;
          const isProblemActiveTab =
            view === "workspace" && ptab.kind !== "library" && ptab.id === resolvedActiveTabId;
          const tabFamily =
            ptab.kind === "simulation" && ptab.tab
              ? resolveWorkspaceTabGeometryFamily(ptab.tab)
              : undefined;
          const isTooltipTarget = tooltip?.resourceKey === ptab.resourceKey;

          return (
            <div
              key={ptab.resourceKey}
              ref={(el) => setTabRef(ptab.resourceKey, el)}
              role="tab"
              tabIndex={0}
              aria-selected={isActive}
              aria-label={ptab.title}
              aria-describedby={isTooltipTarget ? tooltipId : undefined}
              className={`ws-tab-item${isActive ? " is-active" : ""}${ptab.kind === "draft" ? " is-draft" : ""}${ptab.kind === "library" ? " is-library" : ""}`}
              id={isProblemActiveTab ? "ws-active-problem-tab" : undefined}
              data-tab-id={ptab.id}
              data-tab-kind={ptab.kind}
              data-resource-key={ptab.resourceKey}
              data-geometry-family={tabFamily}
              data-full-title={ptab.title}
              onClick={() => activateProjectedTab(ptab.id, ptab.kind)}
              onKeyDown={(e) => handleTabKeyDown(e, idx, ptab.id, ptab.kind)}
              onMouseEnter={(e) => showTooltipForTab(ptab.resourceKey, ptab.title, e.currentTarget)}
              onMouseLeave={() => hideTooltipForTab(ptab.resourceKey)}
              onFocus={(e) => {
                if (e.target === e.currentTarget) {
                  ensureTabVisibleInStrip(e.currentTarget);
                  showTooltipForTab(ptab.resourceKey, ptab.title, e.currentTarget);
                }
              }}
              onBlur={(e) => {
                if (!e.currentTarget.contains(e.relatedTarget as Node | null)) {
                  hideTooltipForTab(ptab.resourceKey);
                } else if (e.target === e.currentTarget) {
                  hideTooltipForTab(ptab.resourceKey);
                }
              }}
            >
              <span
                className="ws-tab-icon"
                data-geometry-family={tabFamily}
                aria-hidden="true"
              >
                {ptab.kind === "library" ? (
                  <IconLibrary size={14} />
                ) : ptab.kind === "draft" ? (
                  <IconFileDoc size={14} />
                ) : (
                  <GeometryFamilyIcon family={tabFamily ?? "neutral"} size={14} />
                )}
              </span>
              <span
                className="prob-title-top ws-tab-title"
                id={isProblemActiveTab ? "top-prob-title" : undefined}
              >
                {ptab.title}
              </span>
              <button
                type="button"
                className="ws-tab-close-btn"
                data-close-tab={ptab.id}
                title={`Đóng tab ${ptab.title}`}
                aria-label={`Đóng tab ${ptab.title}`}
                onMouseEnter={(e) => {
                  e.stopPropagation();
                  hideTooltipForTab(ptab.resourceKey);
                }}
                onFocus={(e) => {
                  e.stopPropagation();
                  hideTooltipForTab(ptab.resourceKey);
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  handleCloseTab(ptab.id);
                }}
              >
                <IconClose size={11} />
              </button>
            </div>
          );
        })}
      </div>

      <button
        type="button"
        className="ws-tab-add-btn btn-change-prob"
        id="btn-header-change-prob"
        title="Mở tab bài toán mới"
        aria-label="Mở tab bài toán mới"
        onClick={handleOpenNewTab}
      >
        <IconPlus size={14} />
      </button>

      {tooltip &&
        (typeof document !== "undefined" && document.body
          ? createPortal(
              <div
                ref={tooltipElRef}
                id={tooltipId}
                role="tooltip"
                className="ws-tab-floating-tooltip"
                style={{
                  left: `${tooltipCoords?.left ?? Math.max(10, tooltip.anchorRect.left)}px`,
                  top: `${tooltipCoords?.top ?? tooltip.anchorRect.bottom + 6}px`,
                  visibility: tooltipCoords ? "visible" : "hidden",
                }}
              >
                {tooltip.text}
              </div>,
              document.body,
            )
          : null)}
    </header>
  );
}
