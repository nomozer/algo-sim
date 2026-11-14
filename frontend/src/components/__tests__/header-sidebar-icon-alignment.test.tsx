import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import App from "../../App";
import {
  GEOMETRY_SOLID_FAMILIES,
  GeometryFamilyIcon,
} from "../family-icons";
import { IconAxoLogo, IconSidebarPanel } from "../icons";
import { LeftSidebar } from "../LeftSidebar";
import { useAuthStore, type AuthUser } from "../../state/auth";
import { __resetHistoryForTest } from "../../state/history";
import { useAppStore } from "../../state/store";

const tokensCss = readFileSync(
  resolve(__dirname, "../../styles/tokens.css"),
  "utf8",
);
const globalCss = readFileSync(
  resolve(__dirname, "../../styles/global.css"),
  "utf8",
);

function syncAuthAndStore(user: AuthUser | null = null, resolved = true) {
  useAuthStore.setState({ user, resolved });
  Object.assign(useAuthStore.getInitialState(), { user, resolved });
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
}

function extractElementChunk(html: string, id: string, maxLen = 1200): string {
  const idx = html.indexOf(`id="${id}"`);
  expect(idx).toBeGreaterThan(-1);
  return html.slice(idx, idx + maxLen);
}

describe("AXO V9.4.11 — Icon System Consistency & Optical Alignment", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
    useAppStore.getState().setGuestEnteredApp(true);
    useAppStore.getState().setView("home");
    syncAuthAndStore(null, true);
  });

  afterEach(() => {
    useAppStore.getState().reset();
    syncAuthAndStore(null, true);
  });

  it("defines shared V9.4.11 icon system tokens and alignment rules in CSS while keeping 271px sidebar", () => {
    expect(tokensCss).toContain("--axo-icon-header-hit: 32px;");
    expect(tokensCss).toContain("--axo-icon-mobile-hit: 34px;");
    expect(tokensCss).toContain("--axo-icon-header-glyph: 18px;");
    expect(tokensCss).toContain("--axo-icon-nav-glyph: 18px;");
    expect(tokensCss).toContain("--axo-icon-geo-slot: 18px;");
    expect(tokensCss).toContain("--axo-icon-geo-glyph: 17px;");
    expect(tokensCss).toContain("--axo-icon-sm-glyph: 14px;");
    expect(tokensCss).toContain("--axo-icon-menu-glyph: 16px;");
    expect(tokensCss).toContain("--axo-icon-brand-sb: 22px;");
    expect(tokensCss).toContain("--axo-sb-icon-gap: 9px;");

    expect(globalCss).toMatch(/--axo-sb-width:\s*271px/);
    expect(globalCss).toMatch(
      /#btn-header-guest-account,\s*\.header-guest-account-btn\s*\{[^}]*width:\s*var\(--axo-icon-mobile-hit\);\s*min-width:\s*var\(--axo-icon-mobile-hit\);\s*height:\s*var\(--axo-icon-mobile-hit\);\s*padding:\s*0;/s,
    );
    expect(globalCss).toMatch(
      /#sb-footer,\s*\.sb-footer\s*\{[^}]*padding:\s*8px 10px 8px 11px;/s,
    );
    expect(globalCss).toMatch(
      /#left-sidebar\s+#sb-guest-account-btn\.sb-guest-login-btn\s*\{\s*gap:\s*8px;/s,
    );
  });

  it("unifies header control icons (viewBox 0 0 20 20, stroke-width 1.75) and balances sidebar brand mark at 22px", () => {
    const appHtml = renderToString(<App />);
    const panelHtml = renderToString(<IconSidebarPanel />);
    const logoHtml = renderToString(<IconAxoLogo />);

    expect(logoHtml).toContain('width="22"');
    expect(logoHtml).toContain('height="22"');
    expect(panelHtml).toContain('viewBox="0 0 20 20"');
    expect(panelHtml).toContain('stroke-width="1.75"');

    const brandChunk = extractElementChunk(appHtml, "sb-brand-home", 1600);
    expect(brandChunk).toContain('width="22"');
    expect(brandChunk).toContain('height="22"');

    for (const id of [
      "btn-sidebar-search",
      "btn-sidebar-collapse",
      "btn-sidebar-mobile-close",
      "btn-header-guest-account",
    ]) {
      const chunk = extractElementChunk(appHtml, id, 800);
      expect(chunk, `${id} should use viewBox 0 0 20 20`).toContain(
        'viewBox="0 0 20 20"',
      );
      expect(chunk, `${id} should use stroke-width 1.75`).toContain(
        'stroke-width="1.75"',
      );
    }
  });

  it("unifies sidebar navigation and guest footer icons on viewBox 0 0 20 20 and stroke-width 1.75", () => {
    const adminUser: AuthUser = {
      id: 1,
      email: "admin@example.com",
      displayName: "Admin Axo",
      role: "admin",
      mustChangePassword: false,
    };
    syncAuthAndStore(adminUser, true);
    const adminSidebarHtml = renderToString(<LeftSidebar />);

    for (const id of [
      "nav-item-new-problem",
      "nav-item-library",
      "nav-item-admin",
    ]) {
      const chunk = extractElementChunk(adminSidebarHtml, id, 800);
      expect(chunk, `${id} nav icon viewBox`).toContain('viewBox="0 0 20 20"');
      expect(chunk, `${id} nav icon stroke-width`).toContain(
        'stroke-width="1.75"',
      );
    }

    syncAuthAndStore(null, true);
    const guestSidebarHtml = renderToString(<LeftSidebar />);
    const guestFooterChunk = extractElementChunk(
      guestSidebarHtml,
      "sb-guest-account-btn",
      800,
    );
    expect(guestFooterChunk).toContain('viewBox="0 0 20 20"');
    expect(guestFooterChunk).toContain('stroke-width="1.75"');
  });

  it("renders all 7 GeometryFamilyIcon variants with uniform 16x16 coordinate grid and stroke-width 1.5", () => {
    expect(GEOMETRY_SOLID_FAMILIES).toEqual([
      "pyramid",
      "cube",
      "prism",
      "sphere",
      "cylinder",
      "cone",
      "neutral",
    ]);

    for (const family of GEOMETRY_SOLID_FAMILIES) {
      const html = renderToString(
        <GeometryFamilyIcon family={family} size={17} />,
      );
      expect(html).toContain(`data-geometry-icon="${family}"`);
      expect(html).toContain('viewBox="0 0 16 16"');
      expect(html).toContain('stroke-width="1.5"');
      expect(html).toContain('width="17"');
      expect(html).toContain('height="17"');
    }
  });
});
