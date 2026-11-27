import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { LeftSidebar } from "../LeftSidebar";

describe("AXO Sidebar Brand Wordmark Refinement", () => {
  it("renders text-only Axo wordmark in LeftSidebar expanded header without icon SVG while keeping semantics and collapsed trigger", () => {
    const html = renderToStaticMarkup(<LeftSidebar />);

    const brandMatch = html.match(
      /<button[^>]*id="sb-brand-home"[^>]*>([\s\S]*?)<\/button>/,
    );
    expect(brandMatch).not.toBeNull();
    const brandAttrAndBody = brandMatch![0];
    const brandInner = brandMatch![1];

    expect(brandAttrAndBody).toContain('type="button"');
    expect(brandAttrAndBody).toContain('aria-label="Axo — Về màn hình nhập đề toán"');
    expect(brandAttrAndBody).toContain('title="Axo — Về màn hình nhập đề toán"');
    expect(brandInner).toContain('<span class="sb-brand-name">Axo</span>');
    expect(brandInner).not.toContain("<svg");
    expect(brandInner).not.toContain("sb-brand-logo");

    // Collapsed sidebar trigger and search button remain intact
    expect(html).toContain('id="btn-sidebar-open-trigger"');
    expect(html).toContain('id="btn-sidebar-search"');
    expect(html).toContain('id="btn-sidebar-collapse"');
    expect(html).toContain("sb-toggle-layout-icon");
  });

  it("sets Inter SemiBold 24px -0.04em wordmark CSS in global.css and removes dead .sb-brand-logo", () => {
    const globalCss = readFileSync(resolve(__dirname, "../../styles/global.css"), "utf8");
    expect(globalCss).toMatch(
      /\.sb-brand-name\s*\{[^}]*font-size:\s*24px;[^}]*font-weight:\s*600;[^}]*letter-spacing:\s*-0\.04em;[^}]*line-height:\s*1;/s,
    );
    expect(globalCss).not.toContain(".sb-brand-logo");
  });

  it("preserves IconAxoLogo / IconAxoSidebarLogo in Landing Header, Footer, TopNav, Auth, Admin, and icons.tsx", () => {
    for (const rel of [
      "../landing/LandingHeader.tsx",
      "../landing/LandingFooter.tsx",
      "../TopNav.tsx",
      "../AuthPageView.tsx",
      "../AdminWorkspaceView.tsx",
    ]) {
      const src = readFileSync(resolve(__dirname, rel), "utf8");
      expect(src, `${rel} must keep IconAxoLogo`).toContain("IconAxoLogo");
    }
    const adminSrc = readFileSync(resolve(__dirname, "../AdminWorkspaceView.tsx"), "utf8");
    expect(adminSrc).toContain("IconAxoSidebarLogo");
    const iconsSrc = readFileSync(resolve(__dirname, "../icons.tsx"), "utf8");
    expect(iconsSrc).toContain("export const IconAxoLogo");
    expect(iconsSrc).toContain("export const IconAxoSidebarLogo");
  });
});
