import { renderToString } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  LandingClosingV14,
  LandingFooterV14,
  scrollToLandingSection,
} from "../landing/LandingClosingV14";
import { IconAxoLogo } from "../icons";
import { useAuthStore } from "../../state/auth";
import { useAppStore } from "../../state/store";

describe("Landing Footer structure, branding, links, and navigation", () => {
  const origDocument = globalThis.document;

  afterEach(() => {
    vi.restoreAllMocks();
    Object.defineProperty(globalThis, "document", {
      value: origDocument,
      configurable: true,
    });
    useAppStore.setState({ view: "landing" });
    useAuthStore.setState({ user: null });
  });

  it("uses the official dark-ink IconAxoLogo mark and preserves essential links without bloat or second 3D model", () => {
    const html = renderToString(<LandingFooterV14 />);
    const logoSvg = renderToString(<IconAxoLogo />);

    expect(html).toContain('id="landing-footer"');
    expect(html).toContain("axo-sp-logo-mark");
    expect(html).toContain(logoSvg);
    expect(html).not.toContain("axo-v14-footer-mark");
    expect(html).not.toContain("<canvas");
    expect(html).toContain("axo-v14-footer-trace-svg");

    // Essential links + concise copyright + back-to-top anchor
    expect(html).toContain('href="#landing-hero"');
    expect(html).toContain("Giới thiệu");
    expect(html).toContain('href="#cach-hoat-dong"');
    expect(html).toContain("Cách hoạt động");
    expect(html).toContain('href="#trai-nghiem"');
    expect(html).toContain("Trải nghiệm");
    expect(html).toContain('id="btn-landing-footer-library"');
    expect(html).toContain("Thư viện bài mẫu");
    expect(html).toContain("© Axo · Mô phỏng hình học không gian 3D");
    expect(html).toContain('id="btn-landing-footer-top"');
    expect(html).toContain("Về đầu trang");

    // Zero invented social/contact metadata or duplicated primary CTA inside footer
    expect(html).not.toContain('id="btn-landing-final-start"');
    expect(html).not.toContain("mailto:");
    expect(html).not.toContain("facebook.com");
  });

  it("scrolls smoothly to hero and section targets and renders complete closing CTA actions", () => {
    const scrollIntoView = vi.fn();
    Object.defineProperty(globalThis, "document", {
      value: {
        getElementById: (id: string) =>
          id === "landing-hero" || id === "trai-nghiem" ? { scrollIntoView } : null,
      },
      configurable: true,
    });

    scrollToLandingSection("landing-hero");
    scrollToLandingSection("trai-nghiem");
    expect(scrollIntoView).toHaveBeenCalledTimes(2);
    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth", block: "start" });

    const closingHtml = renderToString(<LandingClosingV14 />);
    expect(closingHtml).toContain('id="btn-landing-final-start"');
    expect(closingHtml).toContain('id="btn-landing-hero-library"');
    expect(closingHtml).toContain('id="landing-closing-scene3d"');
    expect(useAppStore.getState().view).toBe("landing");
  });
});
