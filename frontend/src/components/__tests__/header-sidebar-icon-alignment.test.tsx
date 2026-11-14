import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import esbuild from "esbuild";
import { chromium } from "playwright";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import App from "../../App";
import { publicCatalog } from "../../data/offline-catalog";
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

  it(
    "renders IconSidebarPanel with outer rounded rect and short interior left vertical bar not touching top or bottom borders, and toggles sidebar via click/keyboard across desktop and mobile without disturbing open tabs",
    async () => {
      const panelHtml = renderToString(<IconSidebarPanel />);
      const rectMatch = panelHtml.match(
        /<rect[^>]*x="([\d.]+)"[^>]*y="([\d.]+)"[^>]*width="([\d.]+)"[^>]*height="([\d.]+)"[^>]*rx="([\d.]+)"/,
      );
      expect(rectMatch).not.toBeNull();
      const [, rxStr, ryStr, rwStr, rhStr, radiusStr] = rectMatch!;
      const rectX = Number(rxStr);
      const rectY = Number(ryStr);
      const rectH = Number(rhStr);
      const radius = Number(radiusStr);
      const strokeWidth = 1.75;
      expect(Number(rwStr)).toBeCloseTo(15.5, 2);
      expect(rectH).toBeCloseTo(13.5, 2);
      expect(radius).toBeGreaterThanOrEqual(2.5);

      const pathMatch = panelHtml.match(
        /<path[^>]*d="M([\d.]+)\s+([\d.]+)v([\d.]+)"/,
      );
      expect(pathMatch).not.toBeNull();
      const [, pxStr, py1Str, pLenStr] = pathMatch!;
      const barX = Number(pxStr);
      const barY1 = Number(py1Str);
      const barY2 = barY1 + Number(pLenStr);

      expect(barX).toBeGreaterThan(rectX + strokeWidth);
      expect(barX).toBeLessThan(10);
      expect(barY1 - strokeWidth / 2).toBeGreaterThan(rectY + strokeWidth / 2);
      expect(barY2 + strokeWidth / 2).toBeLessThan(rectY + rectH - strokeWidth / 2);
      expect(panelHtml).not.toContain('d="M7.5 3.5v13"');

      const sample = publicCatalog()[0]!;
      const bundled = await esbuild.build({
        stdin: {
          contents: `
            import React from "react";
            import { createRoot } from "react-dom/client";
            import App from "../App";
            import { registerAllSimulations } from "../simulations";
            import { useAuthStore } from "../state/auth";
            import { useAppStore } from "../state/store";

            registerAllSimulations();
            useAuthStore.setState({ user: null, resolved: true });
            useAppStore.getState().setGuestEnteredApp(true);
            (window as unknown as { __axoStore?: typeof useAppStore }).__axoStore = useAppStore;

            const host = document.getElementById("root")!;
            createRoot(host).render(React.createElement(App));
          `,
          resolveDir: resolve(__dirname, ".."),
          sourcefile: "sidebar-icon-browser-harness.tsx",
          loader: "tsx",
        },
        bundle: true,
        write: false,
        jsx: "automatic",
        format: "iife",
        platform: "browser",
        target: "es2022",
        define: {
          "process.env.NODE_ENV": '"development"',
          "import.meta.hot": "undefined",
        },
      });

      const browser = await chromium.launch({
        headless: true,
        args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
      });
      const bundleJs = bundled.outputFiles[0]!.text;
      const htmlDoc = `<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8" /><style>${tokensCss}\n${globalCss}\nhtml, body { margin: 0; }</style></head><body><div id="root"></div><script src="/bundle.js"></script></body></html>`;
      try {
        const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
        const pageErrors: string[] = [];
        page.on("pageerror", (e) => pageErrors.push(e.message));
        await page.route("http://axo.test/**", async (route) => {
          const url = route.request().url();
          if (url === "http://axo.test/bundle.js") {
            await route.fulfill({ status: 200, contentType: "application/javascript; charset=utf-8", body: bundleJs });
          } else if (url.includes("/api/auth/")) {
            await route.fulfill({ status: 200, contentType: "application/json", body: '{"user":null}' });
          } else if (url.includes("/api/health")) {
            await route.fulfill({ status: 200, contentType: "application/json", body: '{"ok":true,"hasKey":false}' });
          } else {
            await route.fulfill({ status: 200, contentType: "text/html; charset=utf-8", body: htmlDoc });
          }
        });
        await page.goto("http://axo.test/app", { waitUntil: "domcontentloaded" });
        await page.waitForSelector("#nav-item-library", { timeout: 10000 });
        await page.locator("#nav-item-library").click();
        await page.waitForSelector(`.lib-card[data-lib-prob="${sample.id}"]`, { timeout: 10000 });
        await page.locator(`.lib-card[data-lib-prob="${sample.id}"]`).click();
        await page.waitForSelector('[data-close-tab^="tab-sample-"]', { timeout: 10000 });

        await page.waitForSelector("#btn-sidebar-collapse", { timeout: 10000 });
        type AxoStoreWindow = {
          __axoStore: { getState: () => { workspaceTabs?: Array<{ id: string }> } };
        };
        const readTabIds = () =>
          page.evaluate(() =>
            ((window as unknown as AxoStoreWindow).__axoStore.getState().workspaceTabs ?? []).map(
              (t) => t.id,
            ),
          );
        const initialTabs = await readTabIds();
        expect(initialTabs).toEqual([`tab-sample-${sample.id}`]);

        // Verify SVG path inside desktop header toggle & click to collapse
        expect(
          await page.locator("#btn-sidebar-collapse svg.sb-toggle-layout-icon path").getAttribute("d"),
        ).toBe("M6.25 6.75v6.5");
        await page.locator("#btn-sidebar-collapse").click();
        await page.waitForSelector('#left-sidebar[data-sidebar-state="collapsed"]', {
          state: "attached",
          timeout: 5000,
        });
        await page.waitForSelector("#btn-sidebar-open-trigger", { state: "visible", timeout: 5000 });
        expect(await readTabIds()).toEqual(initialTabs);

        // Keyboard Enter on collapsed trigger re-expands sidebar
        expect(
          await page.locator("#btn-sidebar-open-trigger svg.sb-toggle-layout-icon path").getAttribute("d"),
        ).toBe("M6.25 6.75v6.5");
        await page.locator("#btn-sidebar-open-trigger").focus();
        await page.keyboard.press("Enter");
        await page.waitForSelector('#left-sidebar[data-sidebar-state="expanded"]', { timeout: 5000 });
        expect(await readTabIds()).toEqual(initialTabs);

        // Mobile viewport uses same short-bar IconSidebarPanel on #btn-mobile-open-ws without losing open tabs
        await page.setViewportSize({ width: 390, height: 844 });
        await page.waitForSelector("#btn-mobile-open-ws", { state: "visible", timeout: 5000 });
        expect(
          await page.locator("#btn-mobile-open-ws svg.sb-toggle-layout-icon path").getAttribute("d"),
        ).toBe("M6.25 6.75v6.5");
        await page.locator("#btn-mobile-open-ws").click();
        await page.waitForSelector("#left-sidebar.is-mobile-open", { timeout: 5000 });
        expect(await readTabIds()).toEqual(initialTabs);

        expect(pageErrors).toEqual([]);
      } finally {
        await browser.close();
      }
    },
    30_000,
  );
});
