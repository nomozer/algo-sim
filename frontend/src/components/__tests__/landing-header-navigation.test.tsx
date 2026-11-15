import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { afterEach, describe, expect, it } from "vitest";
import { useAuthStore, type AuthUser } from "../../state/auth";
import { useAppStore } from "../../state/store";
import { LandingHeader } from "../landing/LandingHeader";
import { enterAxoWorkspace, openLandingLogin } from "../landing/landing-geometry-data";

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

describe("AXO Landing Page V1.2 — Header Auth Awareness, Guest Freedom & Accessibility", () => {
  afterEach(() => {
    useAuthStore.setState({ user: null, resolved: false, error: null });
    useAppStore.getState().reset();
    syncAuthForSSR();
  });

  it("shows Guest CTAs without login gate and enters workspace directly when clicked", () => {
    useAuthStore.setState({ user: null, resolved: true, error: null });
    syncAuthForSSR();
    const html = renderToString(<LandingHeader />);

    expect(html).toContain('id="btn-landing-header-start"');
    expect(html).toContain("Bắt đầu");
    expect(html).toContain('id="btn-landing-header-login"');
    expect(html).toContain("Đăng nhập");
    expect(html).toContain('id="btn-landing-header-library"');
    expect(html).toContain("Thư viện");
    expect(html).not.toContain('id="header-user-actions"');

    useAppStore.getState().setView("landing");
    enterAxoWorkspace();
    expect(useAppStore.getState().view).toBe("home");
    expect(useAppStore.getState().guestEnteredApp).toBe(true);

    useAppStore.getState().setView("landing");
    openLandingLogin();
    expect(useAppStore.getState().view).toBe("login");
    expect(useAppStore.getState().guestEnteredApp).toBe(true);
  });

  it("renders TopNavAccount and 'Vào ứng dụng' across Student, Teacher, and Admin authenticated sessions", () => {
    for (const user of [SAMPLE_STUDENT, SAMPLE_TEACHER, SAMPLE_ADMIN]) {
      useAuthStore.setState({ user, resolved: true, error: null });
      syncAuthForSSR();
      const html = renderToString(<LandingHeader />);
      expect(html).toContain('id="header-user-actions"');
      expect(html).toContain('id="btn-header-user-profile"');
      expect(html).toContain(user.displayName);
      expect(html).toContain('id="btn-landing-header-start"');
      expect(html).toContain("Vào ứng dụng");
    }
  });

  it("implements keyboard focus trap inside mobile drawer and RAF-throttled scroll spy", () => {
    const headerSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingHeader.tsx"),
      "utf8",
    );
    expect(headerSrc).toContain("window.requestAnimationFrame");
    expect(headerSrc).toContain("window.cancelAnimationFrame");
    expect(headerSrc).toContain('e.key === "Tab"');
    expect(headerSrc).toContain("e.shiftKey");
    expect(headerSrc).toContain('id="landing-mobile-account"');
  });

  it("V1.2.1: eliminates duplicate CTAs in mobile header/drawer and styles pointer vs keyboard focus cleanly", () => {
    const headerSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingHeader.tsx"),
      "utf8",
    );
    const cssSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/landing.css"),
      "utf8",
    );

    // Open mobile header omits top-bar CTA/account so drawer and header never duplicate "Vào ứng dụng"
    expect(headerSrc).toContain("{!mobileOpen && (");
    expect(headerSrc).toContain('id="btn-landing-drawer-primary"');
    expect(headerSrc).toContain("openedViaKeyboardRef");
    expect(headerSrc).toContain("drawerRef.current?.focus()");

    // Distinct default / hover / active / pressed / focus-visible states in tokens, no default black focus ring
    expect(cssSrc).toContain(".axo-sp-mobile-link.is-active");
    expect(cssSrc).toContain(".axo-sp-mobile-link:active");
    expect(cssSrc).toContain(".axo-sp-mobile-link:focus:not(:focus-visible)");
    expect(cssSrc).toContain(".axo-sp-mobile-link:focus-visible");
    expect(cssSrc).toContain(".axo-sp-header-account");
  });
});
