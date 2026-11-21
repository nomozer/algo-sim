import { useEffect, useRef, useState } from "react";
import {
  AccountSettingsModal,
  AdminWorkspaceView,
  AuthGate,
  AuthPageView,
} from "./components/AuthGate";
import {
  AxoErrorExperience,
  canonicalPathForView,
} from "./components/AxoErrorExperience";
import { ErrorBoundary, ErrorFallback } from "./components/ErrorBoundary";
import { HistoryView } from "./components/HistoryView";
import { HomeView } from "./components/HomeView";
import { IconPanel } from "./components/icons";
import { LandingView } from "./components/LandingView";
import {
  applyIntendedDestination,
  clearIntendedDestination,
  consumeIntendedDestination,
  peekIntendedDestination,
  restoreSavedDraftIfEmpty,
  saveIntendedDestination,
} from "./components/landing/landing-geometry-data";
import { LeftSidebar } from "./components/LeftSidebar";
import { LibraryView } from "./components/LibraryView";
import { SimulationControls } from "./components/SimulationControls";
import { SimulationWorkspace } from "./components/SimulationWorkspace";
import {
  computeAdaptiveHeaderState,
  TEN_TRANG,
  ToastContainer,
  TopNav,
  TopNavAccount,
  type AdaptiveHeaderState,
} from "./components/TopNav";
import { pageTitle } from "./branding";
import { AxoScrollbar } from "./components/AxoScrollbar";
import { recoverCatalogScene3D } from "./data/offline-catalog";
import { hopLeScene3D } from "./simulations/domains/geometry/scene3d-model";
import { useAppStore } from "./state/store";
import { useAuthStore } from "./state/auth";
import { LIBRARY_TAB_ID } from "./state/workspace-tab-identity";

export const AXO_AUTH_SYNC_STORAGE_KEY = "axo_auth_sync_v1";
export const AXO_AUTH_SYNC_CHANNEL = "axo_auth_sync_v1";

let activeAuthReconcile: Promise<void> | null = null;
let lastAuthReconcileAt = 0;
const AUTH_RECONCILE_THROTTLE_MS = 1200;

export function resetAuthReconcileForTests(): void {
  activeAuthReconcile = null;
  lastAuthReconcileAt = 0;
}

export async function reconcileAuthSession(force = false): Promise<void> {
  if (typeof fetch !== "function") {
    await useAuthStore.getState().refresh();
    return;
  }
  if (activeAuthReconcile) {
    return activeAuthReconcile;
  }
  if (!force && lastAuthReconcileAt > 0 && Date.now() - lastAuthReconcileAt < AUTH_RECONCILE_THROTTLE_MS) {
    return;
  }

  activeAuthReconcile = (async () => {
    try {
      const res = await fetch("/api/auth/me", {
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        method: "GET",
      });
      if (res.status === 401 || res.status === 403) {
        useAuthStore.setState({
          user: null,
          resolved: true,
          authGate: null,
          error: null,
        });
        if (typeof window !== "undefined") {
          try {
            window.sessionStorage.removeItem("axo_auth_session_hint");
          } catch {
            /* bỏ qua nếu trình duyệt chặn sessionStorage */
          }
        }
        return;
      }
      if (!res.ok) {
        if (!useAuthStore.getState().resolved) {
          useAuthStore.setState({ resolved: true });
        }
        return;
      }
      const body = (await res.json()) as {
        user?: ReturnType<typeof useAuthStore.getState>["user"];
        entitlement?: ReturnType<typeof useAuthStore.getState>["entitlement"];
      };
      useAuthStore.setState((prev) => ({
        user: body?.user ?? null,
        entitlement: body?.entitlement ?? prev.entitlement,
        resolved: true,
      }));
    } catch {
      if (!useAuthStore.getState().resolved) {
        useAuthStore.setState({ resolved: true });
      }
    } finally {
      lastAuthReconcileAt = Date.now();
      activeAuthReconcile = null;
    }
  })();

  return activeAuthReconcile;
}

export function reconcileCrashedResetKey(
  crashedResetKey: string | null,
  currentResetKey: string,
): string | null {
  return crashedResetKey === currentResetKey ? crashedResetKey : null;
}

/**
 * MỘT VỎ, MỘT THANH TRÊN.
 *
 * TRƯỚC ĐĂNG NHẬP: header mỏng — tên sản phẩm + hai hành động. Người lạ vào
 * trang chưa cần biết AlgoSim có lớp học; họ cần biết nó làm được gì, và cách
 * nhanh nhất là để họ chạy thử một cái thật.
 *
 * SAU ĐĂNG NHẬP: cùng cái header ấy mọc thêm mục điều hướng theo VAI TRÒ
 * (`TopNav`) và cụm tài khoản (`TopNavAccount`). Không có cột trái.
 *
 * ─── VÌ SAO CỘT TRÁI BIẾN MẤT ────────────────────────────────────────────
 *
 * Nó đã tự vô hiệu ở nơi sản phẩm sống: mọi bài hình học đều bật `canvas-first`,
 * và luật ấy thu cột về `width: 0`. Còn lại một cột chỉ sống trên trang danh
 * sách, cộng một ngăn kéo để gọi nó về — mà ngăn kéo ấy chỉ được cấp luật phủ
 * đè ở `max-width: 900px`, nên trên desktop nó mở ra thành cột thường trực bóp
 * sân khấu, không nền mờ, không bấm-ra-ngoài-để-đóng.
 *
 * Hàng ngang bỏ cả hai trạng thái đó: luôn hiện, ở mọi trang, kể cả trong xưởng
 * 3D. Nên «đường ra của xưởng» hết cần chip «Menu» riêng, và sân khấu lấy trọn
 * bề rộng mà không phải nhớ tắt cái gì. Về lại đúng `DESIGN_BRIEF §2`.
 *
 * M18-UI — NHIỀU PHIÊN ĐÃ GỠ. Mỗi lúc đúng một mô phỏng: mở bài khác là THAY
 * bài đang xem, và bài cũ nằm lại trong Lịch sử (mở lại 0 gọi AI). Dải tab
 * phiên cùng bộ máy `sessions`/`switchSession` đã xoá theo.
 */

export default function App() {
  const view = useAppStore((s) => s.view);
  const setView = useAppStore((s) => s.setView);
  const active = useAppStore((s) => s.active);
  const workspaceTabs = useAppStore((s) => s.workspaceTabs);
  const activeTabId = useAppStore((s) => s.activeTabId);
  const navHistoryMode = useAppStore((s) => s.navHistoryMode);
  const unsupported = useAppStore((s) => s.unsupported);
  const activeSampleId = useAppStore((s) => s.activeSampleId);
  const activeHistoryId = useAppStore((s) => s.activeHistoryId);
  const routeFailure = useAppStore((s) => s.routeFailure);
  const hasInAppNavigation = useAppStore((s) => s.hasInAppNavigation);
  const syncLocationRoute = useAppStore((s) => s.syncLocationRoute);
  const hydrateWorkspaceSession = useAppStore((s) => s.hydrateWorkspaceSession);
  const escapeFromError = useAppStore((s) => s.escapeFromError);
  const openLibrary = useAppStore((s) => s.openLibrary);
  const rightOpen = useAppStore((s) => s.rightOpen);
  const toggleRight = useAppStore((s) => s.toggleRight);
  const goHome = useAppStore((s) => s.goHome);
  const guestEnteredApp = useAppStore((s) => s.guestEnteredApp);
  const leftRailMobileOpen = useAppStore((s) => s.leftRailMobileOpen);

  const user = useAuthStore((s) => s.user);
  const authResolved = useAuthStore((s) => s.resolved);
  const isPopStateSyncRef = useRef(false);
  const hasHydratedLocationRef = useRef(false);
  const prevBroadcastUserIdRef = useRef<number | null | undefined>(undefined);
  const prevSessionUserIdRef = useRef<number | null | undefined>(undefined);
  const prevViewForAuthRef = useRef(view);
  const lastNonAuthDestRef = useRef<{
    kind: "home" | "workspace" | "library" | "sample";
    sampleId?: string;
    preferActive?: boolean;
  } | null>(null);
  const [crashedResetKey, setCrashedResetKey] = useState<string | null>(null);
  const [guestHeaderMenuOpen, setGuestHeaderMenuOpen] = useState(false);
  const guestHeaderRef = useRef<HTMLDivElement | null>(null);
  void HistoryView;

  useEffect(() => {
    setGuestHeaderMenuOpen(false);
  }, [user, view]);

  useEffect(() => {
    if (!guestHeaderMenuOpen || typeof window === "undefined") return;
    const onPointerDown = (e: MouseEvent) => {
      if (guestHeaderRef.current && !guestHeaderRef.current.contains(e.target as Node)) {
        setGuestHeaderMenuOpen(false);
      }
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setGuestHeaderMenuOpen(false);
      }
    };
    window.addEventListener("mousedown", onPointerDown);
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("mousedown", onPointerDown);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [guestHeaderMenuOpen]);

  useEffect(() => {
    if (typeof window === "undefined" || !authResolved) return;
    const nextUserId = user?.id ?? null;
    try {
      if (user) {
        window.sessionStorage.setItem("axo_auth_session_hint", "1");
      } else {
        window.sessionStorage.removeItem("axo_auth_session_hint");
      }
    } catch {
      /* bỏ qua nếu trình duyệt chặn sessionStorage */
    }

    if (prevBroadcastUserIdRef.current === undefined) {
      prevBroadcastUserIdRef.current = nextUserId;
      return;
    }
    if (prevBroadcastUserIdRef.current === nextUserId) {
      return;
    }
    prevBroadcastUserIdRef.current = nextUserId;
    const payload = JSON.stringify({ userId: nextUserId, ts: Date.now() });
    try {
      window.localStorage.setItem(AXO_AUTH_SYNC_STORAGE_KEY, payload);
    } catch {
      /* bỏ qua nếu trình duyệt chặn localStorage */
    }
    try {
      if (typeof BroadcastChannel !== "undefined") {
        const ch = new BroadcastChannel(AXO_AUTH_SYNC_CHANNEL);
        ch.postMessage({ userId: nextUserId, ts: Date.now() });
        ch.close();
      }
    } catch {
      /* bỏ qua nếu môi trường không hỗ trợ BroadcastChannel */
    }
  }, [authResolved, user]);

  /* Hỏi máy chủ và giữ phiên đồng bộ xuyên tab + xuyên view giữa Landing và Workspace:
     cookie httpOnly nên JS không tự đọc trực tiếp được. */
  useEffect(() => {
    void reconcileAuthSession(true);
    if (typeof window === "undefined") return;

    const handleFocusOrVisibility = () => {
      if (typeof document !== "undefined" && document.visibilityState === "hidden") return;
      void reconcileAuthSession();
    };
    const handleStorageSync = (e: StorageEvent) => {
      if (e.key !== AXO_AUTH_SYNC_STORAGE_KEY || !e.newValue) return;
      try {
        const parsed = JSON.parse(e.newValue) as { userId?: number | null };
        const curUserId = useAuthStore.getState().user?.id ?? null;
        if ((parsed.userId ?? null) !== curUserId) {
          void reconcileAuthSession(true);
        }
      } catch {
        void reconcileAuthSession(true);
      }
    };

    let bc: BroadcastChannel | null = null;
    try {
      if (typeof BroadcastChannel !== "undefined") {
        bc = new BroadcastChannel(AXO_AUTH_SYNC_CHANNEL);
        bc.onmessage = (ev: MessageEvent<{ userId?: number | null }>) => {
          const curUserId = useAuthStore.getState().user?.id ?? null;
          if ((ev.data?.userId ?? null) !== curUserId) {
            void reconcileAuthSession(true);
          }
        };
      }
    } catch {
      bc = null;
    }

    let popStateResetTimer: number | null = null;
    const applyBrowserLocation = (ev?: Event) => {
      isPopStateSyncRef.current = true;
      if (popStateResetTimer !== null) {
        window.clearTimeout(popStateResetTimer);
      }
      try {
        syncLocationRoute(window.location.pathname, window.location.hash, window.location.search);
        const popState = (
          (ev as PopStateEvent | undefined)?.state ?? window.history?.state
        ) as
          | { axoView?: string; axoTabId?: string | null; tabId?: string | null }
          | null
          | undefined;
        const requestedTabId = popState?.axoTabId ?? popState?.tabId ?? null;
        if (popState?.axoView === "workspace" && requestedTabId) {
          const cur = useAppStore.getState();
          const matchingTab = cur.workspaceTabs.find((t) => t.id === requestedTabId);
          if (matchingTab && (cur.view !== "workspace" || cur.activeTabId !== matchingTab.id)) {
            if (matchingTab.kind === "draft") {
              useAppStore.setState({
                view: "workspace",
                activeTabId: matchingTab.id,
                problemText: matchingTab.draftText ?? cur.problemText,
                routeFailure: null,
                navHistoryMode: "replace",
              });
            } else {
              useAppStore.setState({
                view: "workspace",
                activeTabId: matchingTab.id,
                active: matchingTab.active ?? cur.active,
                activeSampleId: matchingTab.sampleId,
                activeHistoryId: matchingTab.historyId,
                routeFailure: null,
                navHistoryMode: "replace",
              });
            }
          }
        }
        const st = useAppStore.getState();
        if (st.routeFailure === null && typeof window.history?.replaceState === "function") {
          const curPath =
            window.location.pathname.length > 1 && window.location.pathname.endsWith("/")
              ? window.location.pathname.replace(/\/+$/, "")
              : window.location.pathname || "/";
          if (st.view === "workspace") {
            const isDraftActive =
              st.activeTabId === "tab-draft-new" &&
              st.workspaceTabs.some((t) => t.id === "tab-draft-new");
            const canonicalTarget = isDraftActive
              ? "/workspace"
              : canonicalPathForView(st.view, st.activeSampleId ?? st.activeHistoryId);
            if (
              curPath !== canonicalTarget ||
              (window.history.state as { axoTabId?: string | null } | null)?.axoTabId !== st.activeTabId
            ) {
              try {
                window.history.replaceState(
                  {
                    axoView: st.view,
                    axoTabId: st.activeTabId,
                    tabId: st.activeTabId,
                    sampleId: isDraftActive ? null : st.activeSampleId,
                    historyId: isDraftActive ? null : st.activeHistoryId,
                  },
                  "",
                  canonicalTarget,
                );
              } catch {
                /* bỏ qua nếu môi trường kiểm thử chặn replaceState */
              }
            }
          } else if (
            st.view === "library" &&
            curPath === "/library" &&
            (window.history.state as { axoTabId?: string | null } | null)?.axoTabId !== LIBRARY_TAB_ID
          ) {
            try {
              window.history.replaceState(
                {
                  axoView: "library",
                  axoTabId: LIBRARY_TAB_ID,
                  tabId: LIBRARY_TAB_ID,
                  sampleId: null,
                  historyId: null,
                },
                "",
                "/library",
              );
            } catch {
              /* bỏ qua nếu môi trường kiểm thử chặn replaceState */
            }
          }
        }
      } finally {
        popStateResetTimer = window.setTimeout(() => {
          isPopStateSyncRef.current = false;
          popStateResetTimer = null;
        }, 0);
      }
    };
    if (!hasHydratedLocationRef.current) {
      hasHydratedLocationRef.current = true;
      hydrateWorkspaceSession();
      if (
        window.location.pathname !== "/" ||
        window.location.hash === "#admin" ||
        window.location.hash === "#reset" ||
        new URLSearchParams(window.location.search).has("reset_token")
      ) {
        applyBrowserLocation();
      }
      restoreSavedDraftIfEmpty();
    }
    window.addEventListener("hashchange", applyBrowserLocation);
    window.addEventListener("popstate", applyBrowserLocation);
    window.addEventListener("focus", handleFocusOrVisibility);
    window.addEventListener("storage", handleStorageSync);
    if (typeof document !== "undefined") {
      document.addEventListener("visibilitychange", handleFocusOrVisibility);
    }
    return () => {
      if (popStateResetTimer !== null) {
        window.clearTimeout(popStateResetTimer);
      }
      isPopStateSyncRef.current = false;
      window.removeEventListener("hashchange", applyBrowserLocation);
      window.removeEventListener("popstate", applyBrowserLocation);
      window.removeEventListener("focus", handleFocusOrVisibility);
      window.removeEventListener("storage", handleStorageSync);
      if (typeof document !== "undefined") {
        document.removeEventListener("visibilitychange", handleFocusOrVisibility);
      }
      if (bc) {
        bc.close();
      }
    };
  }, [syncLocationRoute, hydrateWorkspaceSession]);

  useEffect(() => {
    if (view === "library") {
      lastNonAuthDestRef.current = { kind: "library" };
    } else if (view === "workspace") {
      if (activeSampleId) {
        lastNonAuthDestRef.current = { kind: "sample", sampleId: activeSampleId };
      } else if (active !== null) {
        lastNonAuthDestRef.current = { kind: "workspace", preferActive: true };
      }
    } else if (view === "home" && (guestEnteredApp || Boolean(user))) {
      lastNonAuthDestRef.current = { kind: "home" };
    }
  }, [view, activeSampleId, active, guestEnteredApp, user]);

  useEffect(() => {
    const prevView = prevViewForAuthRef.current;
    prevViewForAuthRef.current = view;
    if ((view === "login" || view === "register") && prevView !== view) {
      if (!peekIntendedDestination() && lastNonAuthDestRef.current) {
        saveIntendedDestination(lastNonAuthDestRef.current);
      }
    }
    if (view === "landing" && (prevView === "login" || prevView === "register") && !user) {
      clearIntendedDestination();
    }
    if (!authResolved || prevView === view) return;
    if (prevView === "landing" || view === "landing") {
      void reconcileAuthSession();
    }
  }, [view, authResolved]);

  useEffect(() => {
    const curUserId = user?.id ?? null;
    if (prevSessionUserIdRef.current === undefined) {
      prevSessionUserIdRef.current = curUserId;
      return;
    }
    const prevUserId = prevSessionUserIdRef.current;
    prevSessionUserIdRef.current = curUserId;

    if (prevUserId === null && user !== null) {
      const pending = consumeIntendedDestination();
      if (pending) {
        applyIntendedDestination(pending, user);
      } else {
        restoreSavedDraftIfEmpty();
      }
    } else if (prevUserId !== null && user === null) {
      clearIntendedDestination();
      const liveView = useAppStore.getState().view;
      if (liveView === "admin" || liveView === "account") {
        useAppStore.getState().enterGuestWorkspaceAfterLogout();
      } else if (liveView === "home" || liveView === "workspace") {
        useAppStore.getState().enterGuestWorkspaceAfterLogout();
      } else if (liveView === "library") {
        // Keep user on public Library while wiping any authenticated private state/history.
        useAppStore.getState().enterGuestWorkspaceAfterLogout();
        useAppStore.getState().openLibrary();
      }
    }
  }, [user, view, setView]);

  // §D2 — Người dùng đã đăng nhập truy cập /login hoặc /register được điều hướng hợp lý về Workspace (/app hoặc /admin).
  useEffect(() => {
    if (!authResolved || !user) return;
    const liveView = useAppStore.getState().view;
    if (liveView !== "login" && liveView !== "register") return;
    const pending = consumeIntendedDestination();
    if (pending) {
      applyIntendedDestination(pending, user);
    } else if (user.role === "admin") {
      setView("admin");
    } else {
      useAppStore.getState().setGuestEnteredApp(true);
      useAppStore.getState().goHome();
      restoreSavedDraftIfEmpty();
    }
  }, [authResolved, user, view, setView]);

  // Browser tab: "Axo" on the home page, "<page> | Axo" elsewhere (the 3D workspace is named by its role).
  useEffect(() => {
    if (typeof document === "undefined") return;
    document.title = pageTitle(view === "home" ? null
      : view === "workspace" ? "Mô phỏng hình học 3D" : TEN_TRANG[view] ?? null);
  }, [view]);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.history?.pushState !== "function") return;
    if (isPopStateSyncRef.current) return;
    if (view === "not_found" || routeFailure !== null) return;
    if (view === "reset" && new URLSearchParams(window.location.search).has("reset_token")) return;
    if (view === "admin" && window.location.hash === "#admin") return;
    const isDraftActive =
      view === "workspace" &&
      activeTabId === "tab-draft-new" &&
      workspaceTabs.some((t) => t.id === "tab-draft-new");
    const currentPath =
      window.location.pathname.length > 1 && window.location.pathname.endsWith("/")
        ? window.location.pathname.replace(/\/+$/, "")
        : window.location.pathname || "/";
    const targetPath = isDraftActive
      ? "/workspace"
      : view === "home" && (Boolean(user) || guestEnteredApp || currentPath === "/app")
        ? "/app"
        : canonicalPathForView(view, activeSampleId ?? activeHistoryId);
    const resolvedAxoTabId =
      view === "library"
        ? LIBRARY_TAB_ID
        : view === "workspace"
          ? activeTabId
          : null;
    const prevHistoryState = window.history.state as
      | { axoView?: string; axoTabId?: string | null }
      | null
      | undefined;
    const sameWorkspaceTabRoute =
      view === "workspace" &&
      targetPath === "/workspace" &&
      prevHistoryState?.axoView === "workspace" &&
      Boolean(prevHistoryState?.axoTabId) &&
      prevHistoryState?.axoTabId !== resolvedAxoTabId;
    const effectiveView = useAppStore.getState().view;
    if (effectiveView !== view) return;
    if (
      effectiveView === "landing" &&
      (currentPath === "/gioi-thieu" ||
        currentPath === "/" ||
        currentPath === "/about" ||
        currentPath === "/landing" ||
        currentPath === "/welcome" ||
        currentPath === "/intro")
    ) {
      const searchParams = new URLSearchParams(window.location.search ?? "");
      const hasLegacyPreviewParam = searchParams.has("preview");
      const isLegacyLandingAlias =
        currentPath === "/gioi-thieu" ||
        currentPath === "/landing" ||
        currentPath === "/welcome" ||
        currentPath === "/intro";
      if (isLegacyLandingAlias || hasLegacyPreviewParam) {
        try {
          if (hasLegacyPreviewParam) {
            searchParams.delete("preview");
          }
          const cleanSearch = searchParams.toString();
          const suffix = `${cleanSearch ? `?${cleanSearch}` : ""}${window.location.hash ?? ""}`;
          const targetLandingPath = currentPath === "/" ? `/${suffix}` : `/about${suffix}`;
          if (typeof window.history?.replaceState === "function") {
            window.history.replaceState(
              {
                axoView: "landing",
                axoTabId: null,
                tabId: null,
                sampleId: null,
                historyId: null,
              },
              "",
              targetLandingPath,
            );
          }
        } catch {
          /* bỏ qua nếu môi trường kiểm thử chặn replaceState */
        }
      }
      return;
    }
    if (currentPath === targetPath && !sameWorkspaceTabRoute) return;
    const historyState = {
      axoView: view,
      axoTabId: resolvedAxoTabId,
      tabId: activeTabId,
      sampleId: isDraftActive ? null : activeSampleId,
      historyId: isDraftActive ? null : activeHistoryId,
    };
    try {
      if (navHistoryMode === "replace" && typeof window.history?.replaceState === "function") {
        window.history.replaceState(historyState, "", targetPath);
      } else {
        window.history.pushState(historyState, "", targetPath);
      }
    } catch {
      /* bỏ qua nếu môi trường kiểm thử chặn pushState */
    }
  }, [view, activeTabId, workspaceTabs, activeSampleId, activeHistoryId, routeFailure, navHistoryMode, guestEnteredApp, user]);

  const inWorkspace =
    view === "workspace" &&
    (active !== null || unsupported !== null || workspaceTabs.length > 0) &&
    routeFailure === null;
  const isDraftWorkspaceTab =
    inWorkspace && activeTabId === "tab-draft-new" && workspaceTabs.some((t) => t.id === "tab-draft-new");
  const isAuthPage =
    view === "login" || view === "register" || view === "forgot" || view === "reset";
  const isAdminPage = view === "admin";
  const browserPathname =
    typeof window !== "undefined" ? window.location.pathname || "/" : "";
  const normalizedBrowserPath =
    browserPathname.length > 1 && browserPathname.endsWith("/")
      ? browserPathname.replace(/\/+$/, "")
      : browserPathname;
  const isExplicitAppPath =
    normalizedBrowserPath === "/app" || normalizedBrowserPath === "/home";
  const isLandingPathname =
    normalizedBrowserPath === "/about" ||
    normalizedBrowserPath === "/gioi-thieu" ||
    normalizedBrowserPath === "/welcome" ||
    normalizedBrowserPath === "/intro" ||
    normalizedBrowserPath === "/landing";
  const isInitialLandingPathname =
    !hasHydratedLocationRef.current &&
    !hasInAppNavigation &&
    view === "home" &&
    isLandingPathname;
  const hasSessionHint =
    typeof window !== "undefined" &&
    (() => {
      try {
        return window.sessionStorage.getItem("axo_auth_session_hint") === "1";
      } catch {
        return false;
      }
    })();
  const isGuestLandingOnHome =
    view === "home" &&
    !user &&
    !guestEnteredApp &&
    !isExplicitAppPath &&
    (authResolved || (typeof window !== "undefined" && browserPathname === "/" && !hasSessionHint));
  const isLandingPage = view === "landing" || isGuestLandingOnHome || isInitialLandingPathname;
  const isStandaloneShell = isAuthPage || isAdminPage || isLandingPage;
  const mainResetKey = `${view}|${activeTabId ?? ""}|${activeHistoryId ?? activeSampleId ?? ""}|${active?.envelope?.simulation_id ?? ""}|${active?.envelope?.title ?? ""}`;
  const activeCrashedResetKey = reconcileCrashedResetKey(crashedResetKey, mainResetKey);
  useEffect(() => {
    if (crashedResetKey !== null && crashedResetKey !== mainResetKey) {
      setCrashedResetKey(null);
    }
  }, [crashedResetKey, mainResetKey]);
  const mainBoundaryCrashed = activeCrashedResetKey !== null;

  const safeScene3d = inWorkspace && active
    ? (() => {
        try {
          return (recoverCatalogScene3D(active.envelope) as { scene3d?: unknown })?.scene3d;
        } catch {
          return null;
        }
      })()
    : null;
  const isGeometryDomainWorkspace = Boolean(
    inWorkspace && (active?.envelope?.domain === "geometry" || isDraftWorkspaceTab),
  );
  const canvasFirst =
    inWorkspace && hopLeScene3D(safeScene3d)
      ? !mainBoundaryCrashed
      : (isGeometryDomainWorkspace || (inWorkspace && isDraftWorkspaceTab)) && !mainBoundaryCrashed;
  const adaptiveStateRef = useRef<AdaptiveHeaderState | undefined>(undefined);

  useEffect(() => {
    adaptiveStateRef.current = undefined;
    if (typeof window === "undefined" || typeof document === "undefined") return;
    if (canvasFirst || inWorkspace || isStandaloneShell) {
      const el = document.querySelector<HTMLElement>("header.nav-bar");
      if (el) {
        el.classList.remove("is-scrolled");
        delete el.dataset.headerState;
      }
      return;
    }

    let rafId = 0;
    const syncHeader = () => {
      rafId = 0;
      const el = document.querySelector<HTMLElement>("header.nav-bar");
      if (!el) return;
      const next = computeAdaptiveHeaderState(adaptiveStateRef.current, window.scrollY);
      adaptiveStateRef.current = next;
      el.classList.toggle("is-scrolled", next.isScrolled);
      el.dataset.headerState = next.isScrolled ? "scrolled" : "top";
    };

    const scheduleSync = () => {
      if (rafId !== 0) return;
      rafId = window.requestAnimationFrame(syncHeader);
    };

    syncHeader();
    window.addEventListener("scroll", scheduleSync, { passive: true });
    window.addEventListener("resize", scheduleSync, { passive: true });
    return () => {
      if (rafId !== 0) window.cancelAnimationFrame(rafId);
      window.removeEventListener("scroll", scheduleSync);
      window.removeEventListener("resize", scheduleSync);
    };
  }, [canvasFirst, inWorkspace, isStandaloneShell, view]);
  /* W-UI · XƯỞNG 3D LẤY BỀ RỘNG MÀN HÌNH.
     Lưới shell được đặt cho các cơ chế 2D: cột nội dung `auto` với sàn bằng
     chính sách khay, nên một xưởng 3D — vốn không có bề rộng nội tại — co về
     đúng cái sàn ấy và nằm giữa hai khoảng trắng lớn. Đo được ở 1600×900:
     khung 3D 606px trên 1600px khả dụng.
     Cùng vị ngữ `canvasFirst` (dẫn từ `scene3d` có thật, không từ chế độ khai),
     nên vỏ và ruột không thể lệch nhau. */
  const layoutClass = `app-layout${rightOpen ? "" : " right-closed"}`
    + (canvasFirst ? " la-canh-3d" : "");

  const page =
    routeFailure?.kind === "network_failure" || routeFailure?.kind === "unsupported_simulation" ? (
      <AxoErrorExperience
        kind={routeFailure.kind}
        hasBackHistory={hasInAppNavigation}
        onBack={() => escapeFromError()}
        onGoHome={() => goHome()}
        onOpenLibrary={() => openLibrary()}
      />
    )
    : view === "not_found" ? (
      <AxoErrorExperience
        kind="not_found"
        requestedPath={routeFailure?.requestedPath ?? null}
        hasBackHistory={hasInAppNavigation}
        onBack={() => escapeFromError()}
        onGoHome={() => goHome()}
        onOpenLibrary={() => openLibrary()}
      />
    )
    : isAuthPage ? <AuthPageView mode={view} />
    : isAdminPage ? <AdminWorkspaceView />
    : isLandingPage ? <LandingView />
    : view === "history" ? <HomeView />
    : view === "library" ? <LibraryView />
    : view === "account" && user ? (
      <section className="page-stack" aria-label="Cài đặt tài khoản">
        <div className="page-card account-overview-card">
          <div className="account-overview-head">
            <h1 className="home-section-title">Tài khoản cá nhân</h1>
            <span className={`role-chip ${user.role}`}>
              {user.role === "admin"
                ? "Quản trị viên"
                : user.role === "teacher"
                  ? "Giáo viên"
                  : "Học sinh"}
            </span>
          </div>
          <dl className="account-overview-meta">
            <div>
              <dt>Họ và tên</dt>
              <dd>{user.displayName}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{user.email}</dd>
            </div>
          </dl>
        </div>
      </section>
    )
    : <HomeView />;

  return (
    <div
      className={`app-root${user ? " is-authed" : ""}${!isStandaloneShell ? " has-left-sidebar" : ""}${leftRailMobileOpen ? " is-mobile-sidebar-open" : ""}${canvasFirst ? " la-tap-trung" : ""}${isAuthPage ? " is-auth-page" : ""}${isAdminPage ? " is-page-admin" : ""}${isLandingPage ? " is-page-landing" : ""}`}
    >
      {!isStandaloneShell && <LeftSidebar />}
      <div className="app-main">
        {/* W05 · CHẾ ĐỘ TẬP TRUNG: cảnh 3D lấp trang — thanh trên toàn cục (đăng nhập/đăng ký, điều hướng, «Giải
            thích» vốn không tác dụng với cảnh 3D) KHÔNG dựng. Khi ErrorBoundary bắt lỗi render, `canvasFirst`
            tắt ngay để khôi phục thanh điều hướng trên cùng bên ngoài vùng hỏng. */}
        {!canvasFirst && !isLandingPage && (
        <header className="nav-bar">
          <TopNav />

          <nav className="nav-links axo-header-right" aria-label="Tác vụ người dùng">
            {!user && (!hasSessionHint || authResolved) ? (
              <div
                ref={guestHeaderRef}
                className="header-auth-group header-guest-account-wrap"
                id="header-guest-actions"
              >
                <button
                  type="button"
                  id="btn-header-guest-account"
                  className={`header-guest-account-btn${guestHeaderMenuOpen ? " is-open" : ""}`}
                  onClick={() => setGuestHeaderMenuOpen((v) => !v)}
                  aria-label="Tài khoản — Đăng nhập hoặc Đăng ký"
                  title="Tài khoản — Đăng nhập hoặc Đăng ký"
                  aria-haspopup="menu"
                  aria-expanded={guestHeaderMenuOpen}
                  aria-controls="header-guest-popover"
                >
                  <svg
                    viewBox="0 0 20 20"
                    width="18"
                    height="18"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.75"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <circle cx="10" cy="6.8" r="3.1" />
                    <path d="M4.3 16.5c1.1-2.8 3.1-4.1 5.7-4.1s4.6 1.3 5.7 4.1" />
                  </svg>
                </button>
                <div
                  id="header-guest-popover"
                  className={`header-guest-popover${guestHeaderMenuOpen ? " open" : ""}`}
                  role="menu"
                  aria-label="Tài khoản khách"
                >
                  <button
                    type="button"
                    id="btn-open-login"
                    role="menuitem"
                    className="header-guest-menu-item nav-link btn-auth-ghost"
                    onClick={() => {
                      setGuestHeaderMenuOpen(false);
                      setView("login");
                    }}
                  >
                    Đăng nhập
                  </button>
                  <button
                    type="button"
                    id="btn-open-signup"
                    role="menuitem"
                    className="header-guest-menu-item btn-primary nav-cta btn-auth-primary"
                    onClick={() => {
                      setGuestHeaderMenuOpen(false);
                      setView("register");
                    }}
                  >
                    Đăng ký
                  </button>
                </div>
              </div>
            ) : inWorkspace && active !== null && active.envelope.domain !== "geometry" && !mainBoundaryCrashed && (
              <>
                <button className="btn-utility" onClick={goHome}
                  title="Phân tích một đề khác (bài đang xem được lưu vào Lịch sử)">
                  + Mô phỏng mới
                </button>
                <button className={`btn-utility${rightOpen ? " is-active" : ""}`}
                  onClick={toggleRight} title="Ẩn/hiện bảng giải thích">
                  Giải thích
                  <IconPanel side="right" size={14} />
                </button>
              </>
            )}
            {user && <TopNavAccount />}
          </nav>
        </header>
        )}

        {/* ─── LƯỚI CHẶN TRONG: giữ ĐIỀU HƯỚNG khi nội dung vỡ ──────────────
            Năm miền hỏng — HOME, WORKSPACE, SCENE3D, INSPECTOR, PLAYBACK —
            đều dựng bên trong `<main>`, nên MỘT lưới ở đây phủ cả năm. Đặt
            hẹp hơn không giữ thêm được gì: với bài hình học, `Scene3DExplorer`
            CHÍNH LÀ cả bề mặt workspace (đề bài truyền vào trong nó), nên bọc
            riêng khung 3D vẫn mất đề bài.

            Thứ nó cứu được là **thanh điều hướng** — nằm ngoài vùng hỏng, cùng
            giao diện lỗi Axo ưu tiên nút "Quay lại" về trang hợp lệ trước đó.

            `resetKey` theo bài đang mở: mở bài khác ⇒ quên lỗi cũ. */}
        <ErrorBoundary
          mien="main"
          resetKey={`${view}|${activeHistoryId ?? activeSampleId ?? ""}|${active?.envelope?.simulation_id ?? ""}|${active?.envelope?.title ?? ""}`}
          onCatch={() => setCrashedResetKey(mainResetKey)}
          onRecover={() => setCrashedResetKey(null)}
          fallback={(thuLai, { canRetry }) => (
            <main className="app-single">
              <AxoErrorExperience
                kind="render_failure"
                hasBackHistory={hasInAppNavigation}
                onBack={() => {
                  setCrashedResetKey(null);
                  escapeFromError();
                  thuLai();
                }}
                onGoHome={() => {
                  setCrashedResetKey(null);
                  goHome();
                  thuLai();
                }}
                onOpenLibrary={() => {
                  setCrashedResetKey(null);
                  openLibrary();
                  thuLai();
                }}
                onSecondaryRetry={
                  canRetry
                    ? () => {
                        setCrashedResetKey(null);
                        thuLai();
                      }
                    : undefined
                }
              />
            </main>
          )}
        >
        {inWorkspace ? (
          <main className={layoutClass}>
            <section className="panel-center">
              <SimulationWorkspace />
            </section>
            {/* W5AC — KHÔNG còn `aside.panel-right`: nội dung Giải thích nay là
                CỘT HAI bên trong thẻ (`SimulationWorkspace`), cạnh chính cơ chế
                nó giải thích. Xem lý do đo được ở chú thích trong workspace. */}
            {/* W-UI · MỘT KHAY ĐIỀU KHIỂN TRÊN MỘT MÀN HÌNH.
                `SimulationControls` là khay của đường 2D: nó lái bước trong
                store. Xưởng 3D có bộ tua riêng, lái `InteractionState` — hai
                trạng thái THẬT SỰ khác nhau, nên hiện cả hai là bày ra hai
                thanh cùng ghi chữ "Bước" mà kéo thanh dưới thì hình không đổi.
                Ảnh chụp thật bắt đúng cảnh ấy: trên ghi "Bước 7/7", dưới ghi
                "Bước 1/7".
                Ẩn khay 2D khi cảnh là 3D. Không xoá hành vi nào: đường 2D giữ
                nguyên khay của nó. */}
            {!canvasFirst && (
              <footer className="panel-controls">
                <SimulationControls />
              </footer>
            )}
          </main>
        ) : (
          <main className={`app-single${isStandaloneShell ? " is-standalone-main" : ""}`}>{page}</main>
        )}
        </ErrorBoundary>
      </div>

      <AccountSettingsModal />
      <AuthGate />
      <ToastContainer />
      <AxoScrollbar />
    </div>
  );
}

/**
 * LƯỚI CHẶN NGOÀI — lưới cuối, và nó cố ý nghèo nàn.
 *
 * Lưới trong (quanh `<main>`) phủ năm miền nội dung. Cái này phủ phần còn lại:
 * thanh trên (`TopNav`), `AuthGate`, `PracticeReporter` — những thứ mà nếu vỡ
 * thì lưới trong không với tới, và người dùng lại nhìn trang trắng.
 *
 * Vì sao KHÔNG gộp làm một: hai lưới trả lời hai câu khác nhau. Lưới trong nói
 * *"phần nội dung hỏng, giữ lấy điều hướng"*; lưới ngoài nói *"vỏ hỏng, tải
 * lại thôi"* — nó không thể giữ điều hướng, vì điều hướng chính là thứ vừa vỡ.
 *
 * Không dựng một trang lỗi lớn: một câu, một nút tải lại. Fallback càng nhiều
 * thứ thì càng nhiều thứ ném được trong chính lưới cuối.
 */
export function AppRoot() {
  const [rootLocationKey, setRootLocationKey] = useState(() =>
    typeof window !== "undefined"
      ? `${window.location.pathname}${window.location.search}${window.location.hash}`
      : "/",
  );

  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const syncRootKey = () => {
      setRootLocationKey(
        `${window.location.pathname}${window.location.search}${window.location.hash}`,
      );
    };
    window.addEventListener("popstate", syncRootKey);
    return () => window.removeEventListener("popstate", syncRootKey);
  }, []);

  return (
    <ErrorBoundary
      mien="root"
      resetKey={rootLocationKey}
      fallback={(thuLai, { canRetry }) => (
        <div className="loi-chan-goc" role="alert">
          <ErrorFallback
            loiNhan="Ứng dụng gặp lỗi hiển thị. Hãy tải lại trang."
            hanhDong={canRetry ? "Khôi phục giao diện" : "Tải lại trang"}
            onHanhDong={() => {
              if (canRetry) {
                thuLai();
                return;
              }
              window.location.reload();
            }}
          />
        </div>
      )}
    >
      <App />
    </ErrorBoundary>
  );
}
