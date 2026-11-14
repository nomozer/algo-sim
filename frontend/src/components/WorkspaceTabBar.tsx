import type { KeyboardEvent } from "react";
import {
  resolveEffectiveWorkspaceTabs,
  resolveWorkspaceTabGeometryFamily,
  useAppStore,
} from "../state/store";
import {
  buildProjectedWorkspaceTabs,
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

export function WorkspaceTabBar({ fallbackTitle }: WorkspaceTabBarProps) {
  const view = useAppStore((s) => s.view);
  const workspaceTabs = useAppStore((s) => s.workspaceTabs);
  const activeTabId = useAppStore((s) => s.activeTabId);
  const active = useAppStore((s) => s.active);
  const activeSampleId = useAppStore((s) => s.activeSampleId);
  const activeHistoryId = useAppStore((s) => s.activeHistoryId);
  const problemText = useAppStore((s) => s.problemText);
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

  const canGoBack = true;
  const canGoForward = workspaceNavIndex < workspaceNavStack.length - 1;

  const activateProjectedTab = (id: string, kind: "library" | "simulation" | "draft") => {
    if (kind === "library" || id === LIBRARY_TAB_ID) {
      openLibrary();
      return;
    }
    activateWorkspaceTab(id);
  };

  const handleOpenNewTab = () => {
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

  const handleCloseTab = (
    id: string,
    kind: "library" | "simulation" | "draft",
    draftText?: string,
  ) => {
    if (kind === "draft") {
      const isDraftActive = id === resolvedActiveTabId;
      const unsavedText = (isDraftActive ? problemText : (draftText ?? "")).trim();
      if (
        unsavedText.length > 0 &&
        typeof window !== "undefined" &&
        typeof window.confirm === "function"
      ) {
        const ok = window.confirm(
          "Em đang nhập dở đề bài trong tab «Bài toán mới». Em có chắc muốn đóng tab này?",
        );
        if (!ok) return;
      }
    }
    closeWorkspaceTab(id);
  };

  const handleTabKeyDown = (
    e: KeyboardEvent<HTMLDivElement>,
    id: string,
    kind: "library" | "simulation" | "draft",
  ) => {
    if (e.target !== e.currentTarget) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      activateProjectedTab(id, kind);
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

      <div className="ws-tabbar-strip" role="tablist" aria-label="Các bài toán đang mở">
        {projectedTabs.map((ptab) => {
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

          return (
            <div
              key={ptab.resourceKey}
              role="tab"
              tabIndex={0}
              aria-selected={isActive}
              className={`ws-tab-item${isActive ? " is-active" : ""}${ptab.kind === "draft" ? " is-draft" : ""}${ptab.kind === "library" ? " is-library" : ""}`}
              id={isProblemActiveTab ? "ws-active-problem-tab" : undefined}
              data-tab-id={ptab.id}
              data-tab-kind={ptab.kind}
              data-resource-key={ptab.resourceKey}
              data-geometry-family={tabFamily}
              title={ptab.title}
              onClick={() => activateProjectedTab(ptab.id, ptab.kind)}
              onKeyDown={(e) => handleTabKeyDown(e, ptab.id, ptab.kind)}
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
                  <GeometryFamilyIcon family={tabFamily ?? "neutral"} />
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
                onClick={(e) => {
                  e.stopPropagation();
                  handleCloseTab(ptab.id, ptab.kind, ptab.tab?.draftText);
                }}
              >
                <IconClose size={11} />
              </button>
            </div>
          );
        })}

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
      </div>
    </header>
  );
}
