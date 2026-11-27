import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { chromium } from "playwright";
import { renderToString } from "react-dom/server";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { offlineCatalog } from "../data/offline-catalog";
import { registerAllSimulations } from "../simulations";
import { useAuthStore } from "../state/auth";
import { __resetHistoryForTest, type HistoryItem } from "../state/history";
import { useAppStore } from "../state/store";
import { LeftSidebar } from "./LeftSidebar";

registerAllSimulations();

const requireFromFrontend = createRequire(import.meta.url);

function stripCssComments(css: string): string {
  return css.replace(/\/\*[\s\S]*?\*\//g, "");
}

function extractBalancedBlock(source: string, headerStartIndex: number): { full: string; inner: string; endIndex: number } {
  const openBrace = source.indexOf("{", headerStartIndex);
  if (openBrace === -1) {
    throw new Error(`Expected '{' after index ${headerStartIndex}`);
  }
  let depth = 0;
  for (let i = openBrace; i < source.length; i += 1) {
    const ch = source[i];
    if (ch === "{") depth += 1;
    else if (ch === "}") {
      depth -= 1;
      if (depth === 0) {
        return {
          full: source.slice(headerStartIndex, i + 1),
          inner: source.slice(openBrace + 1, i),
          endIndex: i + 1,
        };
      }
    }
  }
  throw new Error(`Unclosed '{' starting at index ${openBrace}`);
}

function parseTopLevelCssRules(css: string): Array<{ selector: string; body: string }> {
  const out: Array<{ selector: string; body: string }> = [];
  let i = 0;
  while (i < css.length) {
    while (i < css.length && /\s/.test(css[i]!)) i += 1;
    if (i >= css.length) break;
    const open = css.indexOf("{", i);
    if (open === -1) break;
    const header = css.slice(i, open).trim();
    const block = extractBalancedBlock(css, i);
    if (!header.startsWith("@")) {
      out.push({ selector: header, body: block.inner });
    }
    i = block.endIndex;
  }
  return out;
}

describe("Sidebar Scrollbar Refinement — scoped sleek CSS & LeftSidebar interaction", () => {
  const rawGlobalCss = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");
  const rawTokensCss = readFileSync(new URL("../styles/tokens.css", import.meta.url), "utf8");
  const cssCode = stripCssComments(rawGlobalCss);

  beforeEach(() => {
    __resetHistoryForTest();
    useAuthStore.setState({ user: null, resolved: true });
    Object.assign(useAuthStore.getInitialState(), { user: null, resolved: true });
    useAppStore.getState().reset();
    useAppStore.getState().setGuestEnteredApp(true);
    Object.assign(useAppStore.getInitialState(), useAppStore.getState());
  });

  afterEach(() => {
    __resetHistoryForTest();
    useAuthStore.setState({ user: null, resolved: true });
    Object.assign(useAuthStore.getInitialState(), { user: null, resolved: true });
    useAppStore.getState().reset();
    Object.assign(useAppStore.getInitialState(), useAppStore.getState());
  });

  it("global.css has a single authoritative #sb-scroll-region.sb-scroll-region layout rule and no duplicate override", () => {
    const topRules = parseTopLevelCssRules(cssCode);
    const sbLayoutRules = topRules.filter(
      (r) =>
        r.selector === ".sb-scroll-region" ||
        r.selector === "#sb-scroll-region" ||
        r.selector === "#sb-scroll-region.sb-scroll-region",
    );

    expect(sbLayoutRules).toHaveLength(1);
    const layoutRule = sbLayoutRules[0]!;
    expect(layoutRule.selector).toBe("#sb-scroll-region.sb-scroll-region");

    expect(layoutRule.body).toMatch(/flex:\s*1\s+1\s+auto;/);
    expect(layoutRule.body).toMatch(/min-height:\s*0;/);
    expect(layoutRule.body).toMatch(/overflow-y:\s*auto;/);
    expect(layoutRule.body).toMatch(/overflow-x:\s*hidden;/);
    expect(layoutRule.body).toMatch(/scrollbar-gutter:\s*auto;/);
    expect(layoutRule.body).toMatch(/overscroll-behavior:\s*contain;/);
    expect(layoutRule.body).toMatch(/padding:\s*2px\s+10px\s+8px;/);
    expect(layoutRule.body).toMatch(/display:\s*flex;/);
    expect(layoutRule.body).toMatch(/flex-direction:\s*column;/);
    expect(layoutRule.body).toMatch(/gap:\s*14px;/);
  });

  it("global.css scopes Chromium WebKit scrollbar rules to .sb-scroll-region (8px gutter, 4px content-box thumb, transparent track, hidden arrows, coarse fallback)", () => {
    const topRules = parseTopLevelCssRules(cssCode);
    const findRule = (exactSelector: string) =>
      topRules.find((r) => r.selector.replace(/\s+/g, " ") === exactSelector);

    const scrollbarRule = findRule(".sb-scroll-region::-webkit-scrollbar");
    expect(scrollbarRule).toBeDefined();
    expect(scrollbarRule!.body).toMatch(/width:\s*8px;/);
    expect(scrollbarRule!.body).toMatch(/height:\s*8px;/);
    expect(scrollbarRule!.body).toMatch(/background:\s*transparent;/);

    const trackRule = findRule(
      ".sb-scroll-region::-webkit-scrollbar-track, .sb-scroll-region::-webkit-scrollbar-track-piece, .sb-scroll-region::-webkit-scrollbar-corner",
    );
    expect(trackRule).toBeDefined();
    expect(trackRule!.body).toMatch(/background:\s*transparent;/);
    expect(trackRule!.body).toMatch(/border:\s*none;/);
    expect(trackRule!.body).toMatch(/box-shadow:\s*none;/);

    const buttonRule = findRule(".sb-scroll-region::-webkit-scrollbar-button");
    expect(buttonRule).toBeDefined();
    expect(buttonRule!.body).toMatch(/display:\s*none;/);
    expect(buttonRule!.body).toMatch(/width:\s*0;/);
    expect(buttonRule!.body).toMatch(/height:\s*0;/);

    const thumbRule = findRule(".sb-scroll-region::-webkit-scrollbar-thumb");
    expect(thumbRule).toBeDefined();
    expect(thumbRule!.body).toMatch(/background-color:\s*transparent;/);
    expect(thumbRule!.body).toMatch(/border-radius:\s*999px;/);
    expect(thumbRule!.body).toMatch(/border:\s*2px\s+solid\s+transparent;/);
    expect(thumbRule!.body).toMatch(/background-clip:\s*content-box;/);
    expect(thumbRule!.body).toMatch(/min-height:\s*32px;/);
    expect(thumbRule!.body).toMatch(/transition:\s*background-color\s+0\.16s\s+ease;/);

    const activeThumbVisibilityRule = findRule(
      ".sb-scroll-region:hover::-webkit-scrollbar-thumb, .sb-scroll-region:focus-visible::-webkit-scrollbar-thumb, .sb-scroll-region:focus-within::-webkit-scrollbar-thumb, .sb-scroll-region.is-scrolling::-webkit-scrollbar-thumb",
    );
    expect(activeThumbVisibilityRule).toBeDefined();
    expect(activeThumbVisibilityRule!.body).toMatch(/background-color:\s*rgba\(31,\s*30,\s*29,\s*0\.24\);/);

    const thumbHoverRule = findRule(".sb-scroll-region::-webkit-scrollbar-thumb:hover");
    expect(thumbHoverRule).toBeDefined();
    expect(thumbHoverRule!.body).toMatch(/background-color:\s*rgba\(31,\s*30,\s*29,\s*0\.38\);/);

    const thumbActiveRule = findRule(".sb-scroll-region::-webkit-scrollbar-thumb:active");
    expect(thumbActiveRule).toBeDefined();
    expect(thumbActiveRule!.body).toMatch(/background-color:\s*rgba\(31,\s*30,\s*29,\s*0\.50\);/);

    const focusVisibleRule = findRule(".sb-scroll-region:focus-visible");
    expect(focusVisibleRule).toBeDefined();
    expect(focusVisibleRule!.body).toMatch(/outline:\s*none;/);
    expect(focusVisibleRule!.body).toMatch(/box-shadow:\s*inset\s+0\s+0\s+0\s+1\.5px\s+rgba\(31,\s*30,\s*29,\s*0\.16\);/);
    expect(focusVisibleRule!.body).toMatch(/border-radius:\s*8px;/);

    expect(cssCode).toMatch(
      /@media\s*\(hover:\s*none\),\s*\(pointer:\s*coarse\)\s*\{\s*\.sb-scroll-region::-webkit-scrollbar-thumb\s*\{[^}]*background-color:\s*rgba\(31,\s*30,\s*29,\s*0\.22\);/s,
    );
  });

  it("global.css guards Firefox scrollbar-width/scrollbar-color strictly inside @supports not selector(::-webkit-scrollbar)", () => {
    const supportsHeader = "@supports not selector(::-webkit-scrollbar)";
    const supportsIdx = cssCode.indexOf(supportsHeader);
    expect(supportsIdx).toBeGreaterThan(-1);

    const supportsBlock = extractBalancedBlock(cssCode, supportsIdx);
    const outsideSupports =
      cssCode.slice(0, supportsIdx) + cssCode.slice(supportsBlock.endIndex);

    // Critical Chromium 121+ guard: outside @supports, no rule touching .sb-scroll-region may set scrollbar-width or scrollbar-color
    const outsideRules = parseTopLevelCssRules(outsideSupports).filter((r) =>
      r.selector.includes("sb-scroll-region"),
    );
    expect(outsideRules.length).toBeGreaterThan(0);
    for (const r of outsideRules) {
      expect(r.body).not.toMatch(/\bscrollbar-width\s*:/);
      expect(r.body).not.toMatch(/\bscrollbar-color\s*:/);
    }

    // Inside @supports not selector(::-webkit-scrollbar): verify Firefox thin/transparent + hover/focus/scrolling + coarse fallback
    expect(supportsBlock.inner).toMatch(
      /\.sb-scroll-region\s*\{[^}]*scrollbar-width:\s*thin;[^}]*scrollbar-color:\s*transparent\s+transparent;/s,
    );
    expect(supportsBlock.inner).toMatch(
      /\.sb-scroll-region:hover,\s*\.sb-scroll-region:focus-visible,\s*\.sb-scroll-region:focus-within,\s*\.sb-scroll-region\.is-scrolling\s*\{[^}]*scrollbar-color:\s*rgba\(31,\s*30,\s*29,\s*0\.24\)\s+transparent;/s,
    );
    expect(supportsBlock.inner).toMatch(
      /@media\s*\(hover:\s*none\),\s*\(pointer:\s*coarse\)\s*\{[^}]*\.sb-scroll-region\s*\{[^}]*scrollbar-color:\s*rgba\(31,\s*30,\s*29,\s*0\.22\)\s+transparent;/s,
    );
  });

  it("LeftSidebar SSR renders #sb-scroll-region with tabIndex=0, aria-label='Danh sách bài toán', and intact header/footer", () => {
    const html = renderToString(<LeftSidebar />);
    expect(html).toContain('id="sb-scroll-region"');
    expect(html).toContain('class="sb-scroll-region"');
    expect(html).toContain('tabindex="0"');
    expect(html).toContain('aria-label="Danh sách bài toán"');
    expect(html).toContain('id="sb-footer"');
    expect(html).toContain('id="sb-guest-account-btn"');
    expect(html).toContain("Đăng nhập");
    expect(html).toContain('id="sb-brand-home"');
    expect(html).toContain('<span class="sb-brand-name">Axo</span>');
  });

  it(
    "LeftSidebar live Chromium DOM: scrolling toggles .is-scrolling, closes open popovers, clears after 650ms without layout shift or unmount timer leak",
    async () => {
      const esbuild = requireFromFrontend("esbuild") as {
        build: (opts: Record<string, unknown>) => Promise<{ outputFiles: { text: string }[] }>;
      };

      // Seed 20 deterministic history items from offlineCatalog() so #sb-scroll-region overflows cleanly
      const baseCatalog = offlineCatalog();
      const seededHistory: HistoryItem[] = Array.from({ length: 20 }, (_, i) => {
        const sample = baseCatalog[i % baseCatalog.length]!;
        return {
          id: `hist-scroll-${i + 1}`,
          schemaVersion: 2,
          title: `${sample.title} (${i + 1})`,
          simulationId: sample.envelope.simulation_id,
          domain: sample.envelope.domain,
          envelope: sample.envelope,
          originalInput: sample.envelope.problem_statement ?? sample.title,
          createdAt: 1_700_000_000_000 + i * 1000,
          updatedAt: 1_700_000_000_000 + i * 1000,
          lastViewedAt: 1_700_000_000_000 + i * 1000,
          lastCursor: 0,
          visualMode: null,
        };
      });

      const bundled = await esbuild.build({
        stdin: {
          contents: `
            import React from "react";
            import { flushSync } from "react-dom";
            import { createRoot } from "react-dom/client";
            import { LeftSidebar } from "./LeftSidebar";
            import { registerAllSimulations } from "../simulations";
            import { useAuthStore } from "../state/auth";
            import { useAppStore } from "../state/store";

            registerAllSimulations();
            const SEEDED_HISTORY = ${JSON.stringify(seededHistory)};
            let root = null;

            window.__mountSidebar = () => {
              useAuthStore.setState({ user: null, resolved: true });
              useAppStore.getState().reset();
              useAppStore.getState().setGuestEnteredApp(true);
              useAppStore.setState({ history: SEEDED_HISTORY });

              let host = document.getElementById("root");
              if (!host) {
                host = document.createElement("div");
                host.id = "root";
                host.className = "app-root has-left-sidebar";
                document.body.appendChild(host);
              }
              root = createRoot(host);
              flushSync(() => {
                root.render(React.createElement(LeftSidebar));
              });
            };

            window.__unmountSidebar = () => {
              if (!root) return;
              flushSync(() => {
                root.render(null);
              });
            };
          `,
          resolveDir: __dirname,
          sourcefile: "left-sidebar-scroll-harness.tsx",
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
          "import.meta.url": '"http://localhost/"',
        },
      });

      const strippedImportCss = rawGlobalCss.replace('@import "./tokens.css";', "");
      const browser = await chromium.launch({ headless: true });
      const pageErrors: string[] = [];
      const consoleErrors: string[] = [];

      try {
        const page = await browser.newPage({ viewport: { width: 1280, height: 560 } });
        page.on("pageerror", (err) => pageErrors.push(err.message));
        page.on("console", (msg) => {
          if (msg.type() === "error") consoleErrors.push(msg.text());
        });

        await page.setContent(
          `<!doctype html><html><head><style>${rawTokensCss}\n${strippedImportCss}</style></head><body></body></html>`,
        );
        await page.addScriptTag({ content: bundled.outputFiles[0]!.text });

        await page.evaluate(() => {
          (window as unknown as { __mountSidebar: () => void }).__mountSidebar();
        });
        await page.waitForSelector("#sb-scroll-region", { timeout: 3000 });

        const baseline = await page.evaluate(() => {
          const region = document.getElementById("sb-scroll-region")!;
          const footer = document.getElementById("sb-footer")!;
          const firstItem = document.querySelector(".sb-problem-item")!;
          const cs = getComputedStyle(region);
          const sbCs = getComputedStyle(region, "::-webkit-scrollbar");
          const btnCs = getComputedStyle(region, "::-webkit-scrollbar-button");
          const trackCs = getComputedStyle(region, "::-webkit-scrollbar-track");
          const thumbCs = getComputedStyle(region, "::-webkit-scrollbar-thumb");
          return {
            tabIndex: region.tabIndex,
            ariaLabel: region.getAttribute("aria-label"),
            hasIsScrolling: region.classList.contains("is-scrolling"),
            scrollHeight: region.scrollHeight,
            clientHeight: region.clientHeight,
            clientWidth: region.clientWidth,
            firstItemWidth: firstItem.getBoundingClientRect().width,
            footerTop: footer.getBoundingClientRect().top,
            footerBottom: footer.getBoundingClientRect().bottom,
            overflowY: cs.overflowY,
            overflowX: cs.overflowX,
            overscrollBehavior: cs.overscrollBehavior,
            scrollbarWidthPx: sbCs.width,
            scrollbarButtonDisplay: btnCs.display,
            scrollbarTrackBg: trackCs.backgroundColor,
            scrollbarThumbIdleBg: thumbCs.backgroundColor,
            itemCount: document.querySelectorAll(".sb-problem-item").length,
          };
        });

        expect(baseline.tabIndex).toBe(0);
        expect(baseline.ariaLabel).toBe("Danh sách bài toán");
        expect(baseline.hasIsScrolling).toBe(false);
        expect(baseline.itemCount).toBe(20);
        expect(baseline.scrollHeight).toBeGreaterThan(baseline.clientHeight);
        expect(baseline.overflowY).toBe("auto");
        expect(baseline.overflowX).toBe("hidden");
        expect(baseline.overscrollBehavior).toBe("contain");
        expect(baseline.scrollbarWidthPx).toBe("8px");
        expect(baseline.scrollbarButtonDisplay).toBe("none");
        expect(baseline.scrollbarTrackBg).toBe("rgba(0, 0, 0, 0)");
        expect(baseline.scrollbarThumbIdleBg).toBe("rgba(0, 0, 0, 0)");

        // Open filter menu first, then scroll -> existing filterMenuOpen close logic AND .is-scrolling toggle both happen
        await page.click("#btn-sidebar-problem-filter");
        await page.waitForSelector("#sb-problem-filter-popover", { timeout: 2000 });

        // Hover over scroll region and scroll via mouse wheel -> zero horizontal layout shift
        const box = await page.locator("#sb-scroll-region").boundingBox();
        expect(box).not.toBeNull();
        await page.mouse.move(box!.x + box!.width / 2, box!.y + box!.height / 2);
        await page.mouse.wheel(0, 140);

        await page.waitForFunction(
          () => {
            const region = document.getElementById("sb-scroll-region");
            if (!region || region.scrollTop <= 0 || !region.classList.contains("is-scrolling")) {
              return false;
            }
            return getComputedStyle(region, "::-webkit-scrollbar-thumb").backgroundColor !== "rgba(0, 0, 0, 0)";
          },
          undefined,
          { timeout: 2000 },
        );

        const duringScrollAndHover = await page.evaluate(() => {
          const region = document.getElementById("sb-scroll-region")!;
          const firstItem = document.querySelector(".sb-problem-item")!;
          const footer = document.getElementById("sb-footer")!;
          const thumbCs = getComputedStyle(region, "::-webkit-scrollbar-thumb");
          return {
            scrollTop: region.scrollTop,
            hasIsScrolling: region.classList.contains("is-scrolling"),
            filterPopoverPresent: Boolean(document.getElementById("sb-problem-filter-popover")),
            clientWidth: region.clientWidth,
            firstItemWidth: firstItem.getBoundingClientRect().width,
            footerTop: footer.getBoundingClientRect().top,
            footerBottom: footer.getBoundingClientRect().bottom,
            thumbActiveBg: thumbCs.backgroundColor,
          };
        });

        expect(duringScrollAndHover.scrollTop).toBeGreaterThan(0);
        expect(duringScrollAndHover.hasIsScrolling).toBe(true);
        expect(duringScrollAndHover.filterPopoverPresent).toBe(false);
        expect(duringScrollAndHover.clientWidth).toBe(baseline.clientWidth);
        expect(duringScrollAndHover.firstItemWidth).toBe(baseline.firstItemWidth);
        expect(duringScrollAndHover.footerTop).toBe(baseline.footerTop);
        expect(duringScrollAndHover.footerBottom).toBe(baseline.footerBottom);
        expect(duringScrollAndHover.thumbActiveBg).not.toBe("rgba(0, 0, 0, 0)");

        // Wait past 650ms idle timeout -> .is-scrolling must clear automatically
        await page.waitForFunction(
          () => !document.getElementById("sb-scroll-region")?.classList.contains("is-scrolling"),
          undefined,
          { timeout: 2000 },
        );

        // Keyboard focus + PageDown scrolling works and keeps footer pinned
        await page.evaluate(() => {
          document.getElementById("sb-scroll-region")!.focus();
        });
        const scrollBeforePageDown = await page.evaluate(
          () => document.getElementById("sb-scroll-region")!.scrollTop,
        );
        await page.keyboard.press("PageDown");
        await page.waitForFunction(
          (prev) => (document.getElementById("sb-scroll-region")?.scrollTop ?? 0) > prev,
          scrollBeforePageDown,
          { timeout: 2000 },
        );

        // Unmount cleanup check: trigger scroll so 650ms timer is armed, spy clearTimeout, unmount immediately, verify timer cleared with 0 errors
        await page.evaluate(() => {
          const w = window as unknown as {
            __clearedTimers: number[];
            __armedScrollTimerCount: number;
            __unmountSidebar: () => void;
          };
          w.__clearedTimers = [];
          w.__armedScrollTimerCount = 0;
          const origSetTimeout = window.setTimeout.bind(window);
          const origClearTimeout = window.clearTimeout.bind(window);
          window.setTimeout = ((fn: TimerHandler, delay?: number, ...args: unknown[]) => {
            const id = origSetTimeout(fn, delay, ...(args as []));
            if (delay === 650) w.__armedScrollTimerCount += 1;
            return id;
          }) as typeof window.setTimeout;
          window.clearTimeout = ((id?: number) => {
            if (typeof id === "number") w.__clearedTimers.push(id);
            return origClearTimeout(id);
          }) as typeof window.clearTimeout;

          const region = document.getElementById("sb-scroll-region")!;
          region.scrollTop = region.scrollTop + 25;
          region.dispatchEvent(new Event("scroll"));
        });

        await page.waitForFunction(
          () => (window as unknown as { __armedScrollTimerCount: number }).__armedScrollTimerCount > 0,
          undefined,
          { timeout: 2000 },
        );

        const cleanupCount = await page.evaluate(() => {
          const w = window as unknown as {
            __clearedTimers: number[];
            __unmountSidebar: () => void;
          };
          const before = w.__clearedTimers.length;
          w.__unmountSidebar();
          return w.__clearedTimers.length - before;
        });

        // Wait past 650ms after unmount to confirm no post-unmount state errors occur
        await page.waitForTimeout(750);

        expect(cleanupCount).toBeGreaterThanOrEqual(1);
        expect(pageErrors).toEqual([]);
        expect(consoleErrors).toEqual([]);
      } finally {
        await browser.close();
      }
    },
    15000,
  );
});
