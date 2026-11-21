import { renderToString } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LandingFooter, scrollToLandingSection } from "../landing/LandingFooter";
import { IconAxoLogo } from "../icons";
import { useAuthStore } from "../../state/auth";
import { useAppStore } from "../../state/store";

describe("Landing Footer — Two-Tier Closing Scene (3D Visual + Pastel CTA) & 3-Zone Info Bar", () => {
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

  it("renders Tier 1 Closing Scene with 3D asset & primary CTA and Tier 2 3-zone info bar", () => {
    const html = renderToString(<LandingFooter />);
    const logoSvg = renderToString(<IconAxoLogo />);

    expect(html).toContain('id="landing-footer"');
    expect(html).toContain('id="landing-final-cta"');
    expect(html).toContain('class="axo-v14-closing-scene"');
    expect(html).toContain('id="btn-landing-final-start"');
    expect(html).toContain("Sẵn sàng nhìn hình học theo cách khác?");
    expect(html).toContain("Bắt đầu dựng hình");
    expect(html).toContain("/assets/landing/studio-scenes/closing-scene.png");

    expect(html).toContain('class="axo-v14-footer-bar"');
    expect(html).toContain("axo-sp-logo-mark");
    expect(html).toContain(logoSvg);
    expect(html).not.toContain("<canvas");
    expect(html).toContain('id="btn-landing-footer-top"');
    expect(html).toContain("Trở về đầu trang");
    expect(html).toContain('href="#landing-hero"');

    // Real product anchors & library trigger only
    expect(html).toContain('href="#about-axo"');
    expect(html).toContain("Về Axo");
    expect(html).toContain('href="#cach-hoat-dong"');
    expect(html).toContain("Cách hoạt động");
    expect(html).toContain('href="#bai-mau"');
    expect(html).toContain("Bài mẫu");
    expect(html).toContain('id="btn-landing-footer-library"');
    expect(html).toContain("Thư viện");
    expect(html).toContain("© Axo · Hình học không gian 3D");

    // Zero invented social/contact metadata
    expect(html).not.toContain("mailto:");
    expect(html).not.toContain("facebook.com");
  });

  it("scrolls cleanly to hero and all three section targets", () => {
    const scrollIntoView = vi.fn();
    Object.defineProperty(globalThis, "document", {
      value: {
        getElementById: (id: string) =>
          ["landing-hero", "about-axo", "cach-hoat-dong", "bai-mau"].includes(id)
            ? { scrollIntoView }
            : null,
      },
      configurable: true,
    });

    scrollToLandingSection("landing-hero");
    scrollToLandingSection("about-axo");
    scrollToLandingSection("cach-hoat-dong");
    scrollToLandingSection("bai-mau");
    expect(scrollIntoView).toHaveBeenCalledTimes(4);
    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth", block: "start" });
    expect(useAppStore.getState().view).toBe("landing");
  });
});
