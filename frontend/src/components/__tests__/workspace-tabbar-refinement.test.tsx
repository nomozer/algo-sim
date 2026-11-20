import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import esbuild from "esbuild";
import { chromium, type Browser, type Page } from "playwright";
import { renderToString } from "react-dom/server";
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { publicCatalog } from "../../data/offline-catalog";
import { registerAllSimulations } from "../../simulations";
import { useAuthStore } from "../../state/auth";
import { __resetHistoryForTest } from "../../state/history";
import {
  resolveWorkspaceTabGeometryFamily,
  useAppStore,
} from "../../state/store";
import { LIBRARY_TAB_ID } from "../../state/workspace-tab-identity";
import { WorkspaceTabBar } from "../WorkspaceTabBar";
import {
  GEOMETRY_SOLID_FAMILIES,
  GeometryFamilyIcon,
  resolveGeometrySolidFamily,
} from "../family-icons";

const tokensCss = readFileSync(resolve(__dirname, "../../styles/tokens.css"), "utf8");
const globalCss = readFileSync(resolve(__dirname, "../../styles/global.css"), "utf8");

function syncStoreForSSR() {
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
  Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());
}

describe("AXO Pha B — Workspace Tab Bar Readability, Overflow, Icons & Accessibility", () => {
  beforeEach(() => {
    registerAllSimulations();
    __resetHistoryForTest();
    useAppStore.getState().reset();
    useAuthStore.setState({ user: null, resolved: true });
    useAppStore.getState().setGuestEnteredApp(true);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    useAppStore.getState().reset();
  });

  it("maps every geometry family (especially cube vs pyramid) accurately without SSR layout warnings", () => {
    const cubeSample = publicCatalog().find((s) => s.id === "lap-phuong-thiet-dien-bat-ky")!;
    const pyramidSample = publicCatalog().find((s) => s.id === "chop-thiet-dien-ba-diem")!;
    const prismSample = publicCatalog().find((s) => s.id === "lang-tru-tam-giac-thiet-dien")!;
    const oxyzSample = publicCatalog().find((s) => s.id === "oxyz-giao-diem-duong-mat")!;
    expect(cubeSample).toBeDefined();

    useAppStore.getState().loadEnvelope(cubeSample.envelope, cubeSample.id, cubeSample.title);
    useAppStore.getState().openDraftWorkspaceTab();
    useAppStore.getState().loadEnvelope(pyramidSample.envelope, pyramidSample.id, pyramidSample.title);
    useAppStore.getState().openDraftWorkspaceTab();
    useAppStore.getState().loadEnvelope(prismSample.envelope, prismSample.id, prismSample.title);
    useAppStore.getState().openDraftWorkspaceTab();
    useAppStore.getState().loadEnvelope(oxyzSample.envelope, oxyzSample.id, oxyzSample.title);
    syncStoreForSSR();

    const tabs = useAppStore.getState().workspaceTabs;
    expect(resolveWorkspaceTabGeometryFamily(tabs[0])).toBe("cube");
    expect(resolveWorkspaceTabGeometryFamily(tabs[1])).toBe("pyramid");
    expect(resolveWorkspaceTabGeometryFamily(tabs[2])).toBe("prism");
    expect(resolveWorkspaceTabGeometryFamily(tabs[3])).toBe("neutral");

    expect(
      resolveGeometrySolidFamily({
        title: "Thiết diện lục giác đều của hình lập phương ABCD.A'B'C'D'",
      }),
    ).toBe("cube");

    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    const html = renderToString(<WorkspaceTabBar />);
    expect(errorSpy).not.toHaveBeenCalled();

    expect(html).toContain('role="tablist"');
    expect(html).toContain(`data-tab-id="tab-sample-${cubeSample.id}"`);
    expect(html).toContain('data-geometry-icon="cube"');
    expect(html).toContain('data-geometry-icon="pyramid"');
    expect(html).toContain('data-geometry-icon="prism"');
    expect(html).toContain('data-geometry-icon="neutral"');
    expect(html).not.toContain('window.confirm');

    for (const fam of GEOMETRY_SOLID_FAMILIES) {
      const iconHtml = renderToString(<GeometryFamilyIcon family={fam} size={14} />);
      expect(iconHtml).toContain(`data-geometry-icon="${fam}"`);
    }
  });

  describe("Live Chromium Tab Bar Browser Matrix", () => {
    let browser: Browser;
    let htmlDoc: string;
    let bundleJs: string;

    beforeAll(async () => {
      const bundled = await esbuild.build({
        stdin: {
          contents: `
            import React from "react";
            import { createRoot } from "react-dom/client";
            import { WorkspaceTabBar } from "./WorkspaceTabBar";
            import { registerAllSimulations } from "../simulations";
            import { publicCatalog } from "../data/offline-catalog";
            import { useAuthStore } from "../state/auth";
            import { useAppStore } from "../state/store";

            registerAllSimulations();
            useAuthStore.setState({ user: null, resolved: true });
            useAppStore.getState().setGuestEnteredApp(true);
            useAppStore.getState().setView("workspace");
            (window as unknown as { __axoStore: typeof useAppStore; __axoCatalog: typeof publicCatalog }).__axoStore = useAppStore;
            (window as unknown as { __axoCatalog: typeof publicCatalog }).__axoCatalog = publicCatalog;

            const host = document.getElementById("root")!;
            createRoot(host).render(React.createElement("div", { className: "axo-workspace-v62 axo-frame is-page-workspace" }, React.createElement(WorkspaceTabBar)));
          `,
          resolveDir: resolve(__dirname, ".."),
          sourcefile: "tabbar-refinement-harness.tsx",
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
      bundleJs = bundled.outputFiles[0]!.text;
      htmlDoc = `<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8" /><style>${tokensCss}\n${globalCss}\nhtml, body { margin: 0; }</style></head><body><div id="root"></div><script src="/bundle.js"></script></body></html>`;
      browser = await chromium.launch({ headless: true });
    });

    afterAll(async () => {
      await browser?.close();
    });

    async function openPreparedTabBarPage(tabCount: number): Promise<{ page: Page; pageErrors: string[]; getConfirmCount: () => number }> {
      const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
      const pageErrors: string[] = [];
      let confirmCalled = 0;
      page.on("pageerror", (e) => pageErrors.push(e.message));
      page.on("dialog", async (dlg) => {
        confirmCalled += 1;
        await dlg.dismiss();
      });
      await page.route("http://axo.test/**", async (route) => {
        const url = route.request().url();
        if (url === "http://axo.test/bundle.js") {
          await route.fulfill({ status: 200, contentType: "application/javascript; charset=utf-8", body: bundleJs });
        } else {
          await route.fulfill({ status: 200, contentType: "text/html; charset=utf-8", body: htmlDoc });
        }
      });
      await page.goto("http://axo.test/app", { waitUntil: "domcontentloaded" });
      await page.waitForSelector(".axo-header.ws-axo-header", { timeout: 6000 });
      await page.evaluate((count) => {
        const st = (window as any).__axoStore.getState();
        st.openLibrary();
        const cat = (window as any).__axoCatalog();
        for (let i = 0; i < Math.min(count, cat.length); i += 1) {
          const item = cat[i]!;
          if (i > 0) st.openDraftWorkspaceTab();
          const longTitle =
            i === 1
              ? "Thiết diện lục giác đều của hình lập phương ABCD.A'B'C'D' qua ba trung điểm cạnh đối xứng rất dài để kiểm tra ellipsis"
              : item.title;
          st.loadEnvelope(
            { ...item.envelope, title: longTitle },
            item.id,
            item.problemText || item.envelope.description,
          );
        }
      }, tabCount);
      await page.waitForSelector(".ws-tabbar-strip .ws-tab-item", { timeout: 6000 });
      return { page, pageErrors, getConfirmCount: () => confirmCalled };
    }

    it("supports hover/focus unclipped tooltips, keyboard navigation, zero width/height shift, cube icon & close without confirm", async () => {
      const { page, pageErrors, getConfirmCount } = await openPreparedTabBarPage(10);
      try {
        const tabs = page.locator(".ws-tabbar-strip .ws-tab-item");
        expect(await tabs.count()).toBeGreaterThanOrEqual(10);

        const cubeTabIcon = await page
          .locator('.ws-tab-item[data-tab-id="tab-sample-lap-phuong-thiet-dien-bat-ky"] .ws-tab-icon svg')
          .getAttribute("data-geometry-icon");
        expect(cubeTabIcon).toBe("cube");

        const targetTab = page.locator('.ws-tab-item[data-tab-id="tab-sample-lap-phuong-thiet-dien-bat-ky"]');
        const inactiveTab = page.locator('.ws-tab-item[data-tab-id="tab-sample-chop-thiet-dien-ba-diem"]');
        await inactiveTab.click();
        expect(await inactiveTab.getAttribute("aria-selected")).toBe("true");
        await targetTab.scrollIntoViewIfNeeded();
        const beforeBox = await targetTab.boundingBox();
        await targetTab.hover();
        const hoverTip = page.locator('[role="tooltip"].ws-tab-floating-tooltip');
        await hoverTip.waitFor({ state: "visible", timeout: 3000 });
        expect(await hoverTip.textContent()).toContain("rất dài để kiểm tra ellipsis");
        const tipBox = await hoverTip.boundingBox();
        expect(tipBox!.x).toBeGreaterThanOrEqual(0);
        expect(tipBox!.x + tipBox!.width).toBeLessThanOrEqual(1440);

        const hoverBox = await targetTab.boundingBox();
        expect(Math.abs(hoverBox!.width - beforeBox!.width)).toBeLessThanOrEqual(0.5);
        expect(Math.abs(hoverBox!.height - beforeBox!.height)).toBeLessThanOrEqual(0.5);

        await targetTab.click();
        const activeBox = await targetTab.boundingBox();
        expect(Math.abs(activeBox!.width - beforeBox!.width)).toBeLessThanOrEqual(0.5);
        expect(Math.abs(activeBox!.height - beforeBox!.height)).toBeLessThanOrEqual(0.5);
        expect(await targetTab.getAttribute("aria-selected")).toBe("true");

        await inactiveTab.focus();
        await page.keyboard.press("ArrowRight");
        const focusTip = page.locator('[role="tooltip"].ws-tab-floating-tooltip');
        await focusTip.waitFor({ state: "visible", timeout: 2500 });
        expect(await focusTip.textContent()).toContain("rất dài để kiểm tra ellipsis");
        await page.keyboard.press("Escape");
        expect(await focusTip.count()).toBe(0);
        await page.keyboard.press("Home");
        await page.keyboard.press("Enter");
        expect(await page.evaluate(() => (window as any).__axoStore.getState().view)).toBe("library");
        expect(await page.locator(`.ws-tab-item[data-tab-id="${LIBRARY_TAB_ID}"]`).getAttribute("aria-selected")).toBe("true");

        await page.locator('.ws-tab-item[data-tab-id="tab-sample-lap-phuong-thiet-dien-bat-ky"] .ws-tab-close-btn').click();
        expect(getConfirmCount()).toBe(0);
        expect(await page.locator('.ws-tab-item[data-tab-id="tab-sample-lap-phuong-thiet-dien-bat-ky"]').count()).toBe(0);
        expect(pageErrors).toEqual([]);
      } finally {
        await page.close();
      }
    });

    it("preserves readable tab widths, horizontal strip scroll, zero close-btn overlap, and zero page overflow across all 8 viewports", async () => {
      const { page, pageErrors } = await openPreparedTabBarPage(10);
      try {
        const viewports: Array<[number, number]> = [
          [1920, 1080],
          [1440, 900],
          [1366, 768],
          [1024, 768],
          [768, 1024],
          [390, 844],
          [360, 800],
          [320, 568],
        ];
        for (const [vw, vh] of viewports) {
          await page.setViewportSize({ width: vw, height: vh });
          const check = await page.evaluate(() => {
            const docOverflow = document.documentElement.scrollWidth - window.innerWidth;
            const strip = document.querySelector(".ws-tabbar-strip") as HTMLElement | null;
            const probTabs = [...document.querySelectorAll(".ws-tab-item:not(.is-library)")];
            let minWidth = Infinity;
            let overlappingClose = false;
            for (const tab of probTabs) {
              const tr = tab.getBoundingClientRect();
              minWidth = Math.min(minWidth, tr.width);
              const iconR = tab.querySelector(".ws-tab-icon")?.getBoundingClientRect();
              const closeR = tab.querySelector(".ws-tab-close-btn")?.getBoundingClientRect();
              if (iconR && closeR && iconR.right > closeR.left + 0.5) {
                overlappingClose = true;
              }
            }
            return {
              docOverflow,
              stripScrollW: strip?.scrollWidth ?? 0,
              stripClientW: strip?.clientWidth ?? 0,
              minWidth,
              overlappingClose,
            };
          });
          expect(check.docOverflow, `${vw}x${vh} page horizontal overflow`).toBeLessThanOrEqual(0);
          expect(check.minWidth, `${vw}x${vh} min tab width`).toBeGreaterThanOrEqual(100);
          expect(check.overlappingClose, `${vw}x${vh} icon/close overlap`).toBe(false);
          expect(check.stripScrollW, `${vw}x${vh} strip horizontal scroll`).toBeGreaterThan(check.stripClientW);
        }
        expect(pageErrors).toEqual([]);
      } finally {
        await page.close();
      }
    });
  });
});
