import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { afterEach, describe, expect, it } from "vitest";
import { useAuthStore, type AuthUser } from "../../state/auth";
import { LandingHeader } from "../landing/LandingHeader";

const SAMPLE_STUDENT: AuthUser = {
  id: 303,
  email: "minh@axo.edu.vn",
  displayName: "Nguyễn Nhật Minh",
  role: "student",
  mustChangePassword: false,
  status: "active",
};

function syncAuthSSR() {
  Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());
}

describe("AXO Landing — Mobile Drawer Cleanliness, Accessibility & Motion", () => {
  afterEach(() => {
    useAuthStore.setState({ user: null, resolved: false, error: null });
    syncAuthSSR();
  });

  it("mounts closed drawer state safely on SSR and renders 3 nav items + primary CTA without Guest login", () => {
    useAuthStore.setState({ user: null, resolved: true, error: null });
    syncAuthSSR();

    const html = renderToString(<LandingHeader />);
    expect(html).toContain('id="btn-landing-mobile-menu"');
    expect(html).toContain('aria-expanded="false"');
    expect(html).toContain('aria-controls="landing-mobile-drawer"');
    expect(html).not.toContain('id="landing-mobile-drawer"');

    const headerSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingHeader.tsx"),
      "utf8",
    );
    expect(headerSrc).toContain("id={`drawer-nav-${item.id}`}");
    expect(headerSrc).toContain('id="btn-landing-drawer-library"');
    expect(headerSrc).toContain('id="btn-landing-drawer-primary"');
    expect(headerSrc).toContain('{user ? "Vào ứng dụng" : "Bắt đầu dựng hình"}');
    expect(headerSrc).not.toContain("btn-landing-drawer-login");
    expect(headerSrc).not.toContain("Đăng nhập tài khoản");
  });

  it("enforces body scroll lock, Tab/Shift+Tab focus trap, Escape return focus, and zero duplicate CTA when open", () => {
    const headerSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingHeader.tsx"),
      "utf8",
    );
    const cssSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/landing.css"),
      "utf8",
    );

    expect(headerSrc).toContain('document.body.style.overflow = "hidden"');
    expect(headerSrc).toContain('e.key === "Escape"');
    expect(headerSrc).toContain("restoreFocusOnCloseRef.current = true");
    expect(headerSrc).toContain("mobileBtnRef.current?.focus()");
    expect(headerSrc).toContain('e.key === "Tab" && drawerRef.current');
    expect(headerSrc).toContain("{!mobileOpen && (");
    expect(headerSrc).toContain("setMobileOpen(false);");

    expect(headerSrc).not.toContain('id="landing-mobile-account"');
    expect(headerSrc).not.toContain('id="btn-landing-drawer-logout"');
    expect(cssSrc).toContain("@keyframes axoDrawerSlideIn");
    expect(cssSrc).not.toContain(".axo-sp-mobile-account-logout");
    expect(cssSrc).not.toMatch(/\.axo-sp-mobile-link-utility\s*\{[^}]*border-top:/);
    expect(cssSrc).toContain("--axo-v14-shadow-cta-secondary-hover");
    expect(cssSrc).not.toMatch(/\.axo-v14-btn-secondary:not\(:disabled\):hover\s*\{[^}]*var\(--axo-sp-shadow-soft\)/);
  });

  it("keeps Landing Header focused on 'Vào ứng dụng' + 'Thư viện' without showing Avatar when authenticated", () => {
    useAuthStore.setState({ user: SAMPLE_STUDENT, resolved: true, error: null });
    syncAuthSSR();
    const html = renderToString(<LandingHeader />);
    expect(html).not.toContain(SAMPLE_STUDENT.displayName);
    expect(html).not.toContain('id="header-user-actions"');
    expect(html).toContain("Thư viện");
    expect(html).toContain("Vào ứng dụng");
  });
});
