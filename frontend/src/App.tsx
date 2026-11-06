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
  const unsupported = useAppStore((s) => s.unsupported);
  const activeSampleId = useAppStore((s) => s.activeSampleId);
  const activeHistoryId = useAppStore((s) => s.activeHistoryId);
  const routeFailure = useAppStore((s) => s.routeFailure);
  const hasInAppNavigation = useAppStore((s) => s.hasInAppNavigation);
  const syncLocationRoute = useAppStore((s) => s.syncLocationRoute);
  const escapeFromError = useAppStore((s) => s.escapeFromError);
  const openLibrary = useAppStore((s) => s.openLibrary);
  const rightOpen = useAppStore((s) => s.rightOpen);
  const toggleRight = useAppStore((s) => s.toggleRight);
  const goHome = useAppStore((s) => s.goHome);
  const assignment = useAppStore((s) => s.activeAssignment);

  const user = useAuthStore((s) => s.user);
  const refresh = useAuthStore((s) => s.refresh);
  const isPopStateSyncRef = useRef(false);
  const hasHydratedLocationRef = useRef(false);
  const [crashedResetKey, setCrashedResetKey] = useState<string | null>(null);

  /* Hỏi máy chủ MỘT LẦN lúc mở app: phiên nằm ở cookie httpOnly nên JS không
     tự đọc được, và đây là cách duy nhất biết mình đang là ai. Đồng thời đồng bộ
     pathname/hash ban đầu và lắng nghe Browser Back/Forward (popstate). */
  useEffect(() => {
    void refresh();
    if (typeof window === "undefined") return;
    const applyBrowserLocation = () => {
      isPopStateSyncRef.current = true;
      try {
        syncLocationRoute(window.location.pathname, window.location.hash, window.location.search);
        const st = useAppStore.getState();
        if (st.view === "workspace" && st.routeFailure === null && typeof window.history?.replaceState === "function") {
          const canonicalTarget = canonicalPathForView(st.view, st.activeSampleId ?? st.activeHistoryId);
          const curPath =
            window.location.pathname.length > 1 && window.location.pathname.endsWith("/")
              ? window.location.pathname.replace(/\/+$/, "")
              : window.location.pathname || "/";
          if (curPath !== canonicalTarget) {
            try {
              window.history.replaceState(
                { axoView: st.view, sampleId: st.activeSampleId, historyId: st.activeHistoryId },
                "",
                canonicalTarget,
              );
            } catch {
              /* bỏ qua nếu môi trường kiểm thử chặn replaceState */
            }
          }
        }




      } finally {
        window.setTimeout(() => {
          isPopStateSyncRef.current = false;
        }, 0);
      }
    };
    if (!hasHydratedLocationRef.current) {
      hasHydratedLocationRef.current = true;
      if (
        window.location.pathname !== "/" ||
        window.location.hash === "#admin" ||
        window.location.hash === "#reset" ||
        new URLSearchParams(window.location.search).has("reset_token")
      ) {
        applyBrowserLocation();
      }
    }
    window.addEventListener("hashchange", applyBrowserLocation);
    window.addEventListener("popstate", applyBrowserLocation);
    return () => {
      window.removeEventListener("hashchange", applyBrowserLocation);
      window.removeEventListener("popstate", applyBrowserLocation);
    };
  }, [refresh, syncLocationRoute]);

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
    const targetPath = canonicalPathForView(view, activeSampleId ?? activeHistoryId);
    const currentPath =
      window.location.pathname.length > 1 && window.location.pathname.endsWith("/")
        ? window.location.pathname.replace(/\/+$/, "")
        : window.location.pathname || "/";
    if (currentPath === targetPath) return;
    try {
      window.history.pushState({ axoView: view, sampleId: activeSampleId, historyId: activeHistoryId }, "", targetPath);
    } catch {
      /* bỏ qua nếu môi trường kiểm thử chặn pushState */
    }
  }, [view, activeSampleId, activeHistoryId, routeFailure]);

  const inWorkspace = view === "workspace" && (active !== null || unsupported !== null) && routeFailure === null;
  const isAuthPage =
    view === "login" || view === "register" || view === "forgot" || view === "reset";
  const isAdminPage = view === "admin";
  const isStandaloneShell = isAuthPage || isAdminPage;
  const mainResetKey = `${view}|${activeHistoryId ?? activeSampleId ?? ""}|${active?.envelope?.simulation_id ?? ""}|${active?.envelope?.title ?? ""}`;
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
    inWorkspace && active?.envelope?.domain === "geometry",
  );
  const canvasFirst =
    inWorkspace && hopLeScene3D(safeScene3d)
      ? !mainBoundaryCrashed
      : isGeometryDomainWorkspace && !mainBoundaryCrashed;
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
    : view === "history" ? <HistoryView />
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
      className={`app-root${user ? " is-authed" : ""}${canvasFirst ? " la-tap-trung" : ""}${isAuthPage ? " is-auth-page" : ""}${isAdminPage ? " is-page-admin" : ""}`}
    >
      <div className="app-main">
        {/* W05 · CHẾ ĐỘ TẬP TRUNG: cảnh 3D lấp trang — thanh trên toàn cục (đăng nhập/đăng ký, điều hướng, «Giải
            thích» vốn không tác dụng với cảnh 3D) KHÔNG dựng. Khi ErrorBoundary bắt lỗi render, `canvasFirst`
            tắt ngay để khôi phục thanh điều hướng trên cùng bên ngoài vùng hỏng. */}
        {!canvasFirst && (
        <header className="nav-bar">
          <TopNav />

          <nav className="nav-links axo-header-right" aria-label="Tác vụ người dùng">
            {!user ? (
              <div className="header-auth-group" id="header-guest-actions">
                <button
                  type="button"
                  id="btn-open-login"
                  className="nav-link btn-auth-ghost"
                  onClick={() => setView("login")}
                >
                  Đăng nhập
                </button>
                <button
                  type="button"
                  id="btn-open-signup"
                  className="btn-primary nav-cta btn-auth-primary"
                  onClick={() => setView("register")}
                >
                  Đăng ký
                </button>
              </div>
            ) : inWorkspace && active !== null && active.envelope.domain !== "geometry" && !mainBoundaryCrashed && (
              <>
                {assignment && (
                  <span className="nav-assignment" title={assignment.instruction}>
                    Bài: <strong>{assignment.title}</strong>
                  </span>
                )}
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
