import { readFileSync } from "node:fs";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import App from "../../App";
import { LeftSidebar } from "../LeftSidebar";
import { useAuthStore, type AuthUser } from "../../state/auth";
import { useAppStore } from "../../state/store";
import { registerAllSimulations } from "../../simulations";
import { __resetHistoryForTest } from "../../state/history";

registerAllSimulations();

function syncAuthForSSR(user: AuthUser | null, resolved: boolean) {
  useAuthStore.setState({ user, resolved });
  Object.assign(useAuthStore.getInitialState(), { user, resolved });
}

function syncAppForSSR() {
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
}

describe("AXO V9.2 — LeftSidebar Guest Account Footer Recovery & Cross-Role Audit", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
    useAppStore.getState().setGuestEnteredApp(true);
    syncAuthForSSR(null, true);
    syncAppForSSR();
  });

  afterEach(() => {
    syncAuthForSSR(null, true);
    useAppStore.getState().reset();
    syncAppForSSR();
  });

  it("Phase 1.1: Auth Loading (!user && !authResolved) renders #sb-auth-loading-row without flashing Guest 'Đăng nhập' UI", () => {
    syncAuthForSSR(null, false);
    const html = renderToString(<LeftSidebar />);

    expect(html).toContain('id="sb-auth-loading-row"');
    expect(html).toContain('aria-busy="true"');
    expect(html).not.toContain('id="sb-guest-account-btn"');
    expect(html).not.toContain("sb-guest-login-label");
    expect(html).not.toContain("Đăng nhập · Đăng ký");
  });

  it("Phase 1.2 & 1.3: Guest state (!user && authResolved) renders ONLY single-row #sb-guest-account-btn ('Đăng nhập') with no popover or redundant labels", () => {
    syncAuthForSSR(null, true);
    const html = renderToString(<LeftSidebar />);

    expect(html).toContain('class="sb-account-anchor"');
    expect(html).toContain('id="sb-guest-account-btn"');
    expect(html).toContain('class="sb-guest-login-btn"');
    expect(html).toContain('class="sb-guest-login-icon"');
    expect(html).toContain('<span class="sb-guest-login-label">Đăng nhập</span>');

    // Completely removed redundant Guest Footer clutter
    expect(html).not.toContain('id="sb-guest-account-popover"');
    expect(html).not.toContain('id="btn-sb-guest-login"');
    expect(html).not.toContain('id="btn-sb-guest-signup"');
    expect(html).not.toContain("Đăng nhập · Đăng ký");
    expect(html).not.toContain('<span class="sb-user-name">Tài khoản</span>');

    const leftSidebarSrc = readFileSync(
      new URL("../LeftSidebar.tsx", import.meta.url),
      "utf8",
    );
    expect(leftSidebarSrc).not.toContain("guestSidebarMenuOpen");
    expect(leftSidebarSrc).not.toContain("sb-guest-account-popover");
    expect(leftSidebarSrc).not.toContain("Đăng nhập · Đăng ký");
    expect(leftSidebarSrc).toMatch(
      /id="sb-guest-account-btn"[\s\S]*?onClick=\{\(\)\s*=>\s*\{\s*setView\("login"\);\s*closeMobileIfOpen\(\);\s*\}\}/,
    );
  });

  it("Phase 1.1 & Phase 2: Authenticated Student, Teacher, and Admin roles render accurate role footers and navigation items without fallback", () => {
    // 1. Student
    syncAuthForSSR(
      {
        id: 301,
        email: "student.v92@axo.vn",
        displayName: "Nguyễn Minh Anh",
        role: "student",
        mustChangePassword: false,
      },
      true,
    );
    const studentHtml = renderToString(<LeftSidebar />);
    expect(studentHtml).toContain('id="sb-user-account-btn"');
    expect(studentHtml).toContain("Nguyễn Minh Anh");
    expect(studentHtml).toContain("Học sinh");
    expect(studentHtml).not.toContain('id="sb-guest-account-btn"');
    expect(studentHtml).not.toContain('id="sb-auth-loading-row"');
    expect(studentHtml).not.toContain('id="sidebar-group-teacher"');
    expect(studentHtml).not.toContain('id="nav-item-admin"');

    // 2. Teacher (V9.3: Unified Sidebar identical to Student, while keeping "Giáo viên" role label in Account Footer)
    syncAuthForSSR(
      {
        id: 302,
        email: "teacher.v92@axo.vn",
        displayName: "Thầy Trần Quốc Tuấn",
        role: "teacher",
        mustChangePassword: false,
      },
      true,
    );
    const teacherHtml = renderToString(<LeftSidebar />);
    expect(teacherHtml).toContain('id="sb-user-account-btn"');
    expect(teacherHtml).toContain("Thầy Trần Quốc Tuấn");
    expect(teacherHtml).toContain("Giáo viên");
    expect(teacherHtml).not.toContain("Học sinh");
    expect(teacherHtml).toContain('id="nav-item-new-problem"');
    expect(teacherHtml).toContain('id="nav-item-library"');
    expect(teacherHtml).toContain('id="sidebar-group-problems"');
    expect(teacherHtml).not.toContain('id="sidebar-group-teacher"');
    expect(teacherHtml).not.toContain('id="nav-item-classes"');
    expect(teacherHtml).not.toContain('id="nav-item-assignments"');
    expect(teacherHtml).not.toContain('id="nav-item-monitor"');
    expect(teacherHtml).not.toContain("Lớp học");
    expect(teacherHtml).not.toContain("Bài thực hành");
    expect(teacherHtml).not.toContain("Theo dõi lớp");
    expect(teacherHtml).not.toContain('id="nav-item-admin"');

    // 3. Admin
    syncAuthForSSR(
      {
        id: 303,
        email: "admin.v92@axo.vn",
        displayName: "Quản Trị Hệ Thống",
        role: "admin",
        mustChangePassword: false,
      },
      true,
    );
    const adminHtml = renderToString(<LeftSidebar />);
    expect(adminHtml).toContain('id="sb-user-account-btn"');
    expect(adminHtml).toContain("Quản Trị Hệ Thống");
    expect(adminHtml).toContain("Quản trị viên");
    expect(adminHtml).not.toContain("Học sinh");
    expect(adminHtml).toContain('id="nav-item-admin"');
    expect(adminHtml).not.toContain('id="sidebar-group-teacher"');

    // 4. Expired session -> transitions back to Guest #sb-guest-account-btn
    syncAuthForSSR(null, true);
    const expiredHtml = renderToString(<LeftSidebar />);
    expect(expiredHtml).toContain('id="sb-guest-account-btn"');
    expect(expiredHtml).not.toContain('id="sb-user-account-btn"');
  });

  it("Phase 2 & Phase 7: Sidebar filter labels and App header guest actions stay consistent", () => {
    syncAuthForSSR(null, true);
    useAppStore.getState().goHome();
    useAppStore.getState().setGuestEnteredApp(true);
    syncAppForSSR();

    const appHtml = renderToString(<App />);
    expect(appHtml).toContain('id="btn-sidebar-problem-filter"');
    expect(appHtml).toContain('id="sb-problem-filter-label">Tất cả<');
    expect(appHtml).toContain('id="btn-header-guest-account"');
    expect(appHtml).toContain('id="sb-guest-account-btn"');

    const leftSidebarSrc = readFileSync(
      new URL("../LeftSidebar.tsx", import.meta.url),
      "utf8",
    );
    expect(leftSidebarSrc).toContain('all: "Tất cả"');
    expect(leftSidebarSrc).toContain('ready: "Sẵn sàng"');
    expect(leftSidebarSrc).toContain('needs_attention: "Cần chú ý"');
    expect(leftSidebarSrc).toContain('in_progress: "Đang tiến hành"');
  });

  it("V9.3 Phase 2.2: Removed classroom routes (/classes, /assignments, /monitor, /observe) safely fall back to 404 not_found experience", () => {
    for (const removedPath of ["/classes", "/assignments", "/monitor", "/observe"]) {
      useAppStore.getState().reset();
      useAppStore.getState().syncLocationRoute(removedPath, "", "");
      syncAppForSSR();

      expect(useAppStore.getState().view).toBe("not_found");
      expect(useAppStore.getState().routeFailure).toEqual({
        kind: "not_found",
        requestedPath: removedPath,
      });

      const html = renderToString(<App />);
      expect(html).toContain('data-error-kind="not_found"');
      expect(html).toContain("404");
    }
  });
});
