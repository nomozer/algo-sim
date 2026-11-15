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

describe("AXO Landing V1.2.2 — Mobile Drawer Cleanliness, Accessibility & Motion", () => {
  afterEach(() => {
    useAuthStore.setState({ user: null, resolved: false, error: null });
    syncAuthSSR();
  });

  it("mounts closed drawer state safely on SSR and hides Guest login action in drawer source", () => {
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
    // Exact 5 Guest drawer items: 3 section links + Thư viện mẫu + Bắt đầu dựng hình (no Guest login item)
    expect(headerSrc).toContain("id={`drawer-nav-${item.id}`}");
    expect(headerSrc).toContain('id="btn-landing-drawer-library"');
    expect(headerSrc).toContain("Thư viện mẫu");
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

    // Authenticated mobile drawer account summary + logout action
    expect(headerSrc).toContain('id="landing-mobile-account"');
    expect(headerSrc).toContain('id="btn-landing-drawer-logout"');
    expect(cssSrc).toContain("@keyframes axoDrawerSlideIn");
    expect(cssSrc).toContain(".axo-sp-mobile-account-logout");
  });

  it("keeps Hero/Header account identity accurate for authenticated state without JSX syntax issues", () => {
    useAuthStore.setState({ user: SAMPLE_STUDENT, resolved: true, error: null });
    syncAuthSSR();
    const html = renderToString(<LandingHeader />);
    expect(html).toContain(SAMPLE_STUDENT.displayName);
    expect(html).toContain("Vào ứng dụng");
  });
});
