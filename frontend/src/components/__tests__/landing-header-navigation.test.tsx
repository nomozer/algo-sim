import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { afterEach, describe, expect, it } from "vitest";
import { useAuthStore, type AuthUser } from "../../state/auth";
import { useAppStore } from "../../state/store";
import { LandingHeader } from "../landing/LandingHeader";
import { enterAxoWorkspace } from "../landing/landing-geometry-data";

const SAMPLE_STUDENT: AuthUser = {
  id: 11,
  email: "minh@axo.edu.vn",
  displayName: "Nguyễn Nhật Minh",
  role: "student",
  mustChangePassword: false,
  status: "active",
};

const SAMPLE_TEACHER: AuthUser = {
  id: 22,
  email: "lan@axo.edu.vn",
  displayName: "Trần Phương Lan",
  role: "teacher",
  mustChangePassword: false,
  status: "active",
};

const SAMPLE_ADMIN: AuthUser = {
  id: 1,
  email: "admin@axo.edu.vn",
  displayName: "Quản trị Axo",
  role: "admin",
  mustChangePassword: false,
  status: "active",
};

function syncAuthForSSR() {
  Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
}

describe("AXO Landing Header — 3-Zone Navigation, Auth Awareness, Guest Freedom & Accessibility", () => {
  afterEach(() => {
    useAuthStore.setState({ user: null, resolved: false, error: null });
    useAppStore.getState().reset();
    syncAuthForSSR();
  });

  it("shows 3-zone Guest Header with 'Thư viện' immediately beside 'Bắt đầu' and no standalone login button", () => {
    useAuthStore.setState({ user: null, resolved: true, error: null });
    syncAuthForSSR();
    const html = renderToString(<LandingHeader />);

    expect(html).toContain('id="btn-landing-header-library"');
    expect(html).toContain('href="/library"');
    expect(html).toContain("Thư viện");
    expect(html).toContain('id="btn-landing-header-start"');
    expect(html).toContain("Bắt đầu");
    expect(html.indexOf('id="btn-landing-header-library"')).toBeLessThan(
      html.indexOf('id="btn-landing-header-start"'),
    );
    expect(html).not.toContain('id="btn-landing-header-login"');
    expect(html).not.toContain("Đăng nhập");
    expect(html).not.toContain('id="header-user-actions"');

    useAppStore.getState().setView("landing");
    enterAxoWorkspace();
    expect(useAppStore.getState().view).toBe("login");
    expect(useAppStore.getState().guestEnteredApp).toBe(false);
  });

  it("switches primary CTA to 'Vào ứng dụng' without rendering Avatar/TopNavAccount on Landing Header across Student, Teacher, and Admin sessions", () => {
    for (const user of [SAMPLE_STUDENT, SAMPLE_TEACHER, SAMPLE_ADMIN]) {
      useAuthStore.setState({ user, resolved: true, error: null });
      syncAuthForSSR();
      const html = renderToString(<LandingHeader />);
      expect(html).not.toContain('id="header-user-actions"');
      expect(html).not.toContain('id="btn-header-user-profile"');
      expect(html).not.toContain(user.displayName);
      expect(html).toContain('id="btn-landing-header-library"');
      expect(html).toContain("Thư viện");
      expect(html).toContain('id="btn-landing-header-start"');
      expect(html).toContain("Vào ứng dụng");
    }
  });

  it("implements keyboard focus trap inside mobile drawer and RAF-throttled scroll spy without Workspace account controls on Landing", () => {
    const headerSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingHeader.tsx"),
      "utf8",
    );
    expect(headerSrc).toContain("window.requestAnimationFrame");
    expect(headerSrc).toContain("window.cancelAnimationFrame");
    expect(headerSrc).toContain('e.key === "Tab"');
    expect(headerSrc).toContain("e.shiftKey");
    expect(headerSrc).not.toContain('id="landing-mobile-account"');
    expect(headerSrc).not.toContain("TopNavAccount");
  });

  it("eliminates duplicate CTAs in mobile header/drawer and styles pointer vs keyboard focus cleanly", () => {
    const headerSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingHeader.tsx"),
      "utf8",
    );
    const cssSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/landing.css"),
      "utf8",
    );

    expect(headerSrc).toContain("{!mobileOpen && (");
    expect(headerSrc).toContain('id="btn-landing-drawer-primary"');
    expect(headerSrc).toContain("openedViaKeyboardRef");
    expect(headerSrc).toContain("drawerRef.current?.focus()");

    expect(cssSrc).toContain(".axo-sp-mobile-link.is-active");
    expect(cssSrc).toContain(".axo-sp-mobile-link:active");
    expect(cssSrc).toContain(".axo-sp-mobile-link:focus:not(:focus-visible)");
    expect(cssSrc).toContain(".axo-sp-mobile-link:focus-visible");
    expect(cssSrc).not.toContain(".axo-sp-header-account");
  });

  it("renders exactly 3 post-Hero nav links (Về Axo | Cách hoạt động | Bài mẫu) with NO default active highlight at Hero", () => {
    useAuthStore.setState({ user: null, resolved: true, error: null });
    syncAuthForSSR();
    const headerHtml = renderToString(<LandingHeader />);
    const cssSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/landing.css"),
      "utf8",
    );

    expect(headerHtml).toContain("Về Axo");
    expect(headerHtml).toContain("Cách hoạt động");
    expect(headerHtml).toContain("Bài mẫu");
    expect(headerHtml).not.toContain("Tổng quan");
    expect(headerHtml).toContain('href="#about-axo"');
    expect(headerHtml).toContain('href="#cach-hoat-dong"');
    expect(headerHtml).toContain('href="#bai-mau"');
    expect(headerHtml).toContain("axo-sp-nav is-v14");
    expect(headerHtml).toContain('data-nav-hover-state="idle"');
    expect(headerHtml).not.toContain("is-current-section");
    expect(headerHtml).not.toContain('aria-current="location"');
    expect(cssSrc).toContain('.axo-sp-nav.is-v14[data-nav-hover-state="other"] .axo-sp-nav-pill');
    expect(cssSrc).toContain(".axo-sp-nav.is-v14 .axo-sp-nav-link.is-current-section::after");
  });
});
