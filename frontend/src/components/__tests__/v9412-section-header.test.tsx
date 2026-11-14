import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { publicCatalog } from "../../data/offline-catalog";
import { registerAllSimulations } from "../../simulations";
import { useAuthStore } from "../../state/auth";
import { __resetHistoryForTest } from "../../state/history";
import { useAppStore } from "../../state/store";
import { LeftSidebar } from "../LeftSidebar";

registerAllSimulations();

const globalCss = readFileSync(
  resolve(__dirname, "../../styles/global.css"),
  "utf8",
);

function syncSSR() {
  useAuthStore.setState({ user: null, resolved: true });
  Object.assign(useAuthStore.getInitialState(), { user: null, resolved: true });
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
}

function renderSidebar(): string {
  syncSSR();
  return renderToString(<LeftSidebar />);
}

function extractCssBlock(selectorPattern: RegExp): string {
  const m = globalCss.match(selectorPattern);
  expect(m).not.toBeNull();
  return m![0];
}

describe("AXO V9.4.12 — Sidebar Section Header & Filter Alignment", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
    useAppStore.getState().setGuestEnteredApp(true);
    syncSSR();
  });

  afterEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
    syncSSR();
  });

  it("renders DOM order Bài toán -> dynamic badge -> chevron inside a single toggle button, followed by Filter icon -> Tất cả", () => {
    // 0 problems
    const htmlZero = renderSidebar();
    const hdrStart = htmlZero.indexOf('class="sb-group-hdr"');
    expect(hdrStart).toBeGreaterThan(-1);
    const hdrHtmlZero = htmlZero.slice(hdrStart, hdrStart + 2200);

    const titleIdx = hdrHtmlZero.indexOf('<span class="sb-group-title">Bài toán</span>');
    const countIdx = hdrHtmlZero.indexOf('<span class="sb-group-count" id="sb-problem-count">0</span>');
    const chevronIdx = hdrHtmlZero.indexOf('<span class="sb-group-chevron" aria-hidden="true">');
    expect(titleIdx).toBeGreaterThan(-1);
    expect(countIdx).toBeGreaterThan(titleIdx);
    expect(chevronIdx).toBeGreaterThan(countIdx);
    expect(hdrHtmlZero).toContain('stroke-width="1.75"');

    // Filter trigger: SVG comes BEFORE #sb-problem-filter-label ("Tất cả"), no chevron on filter
    const filterStart = hdrHtmlZero.indexOf('id="btn-sidebar-problem-filter"');
    expect(filterStart).toBeGreaterThan(-1);
    const filterChunk = hdrHtmlZero.slice(filterStart, hdrHtmlZero.indexOf("</div>", filterStart));
    const filterSvgIdx = filterChunk.indexOf("<svg");
    const filterLabelIdx = filterChunk.indexOf('<span id="sb-problem-filter-label">Tất cả</span>');
    expect(filterSvgIdx).toBeGreaterThan(-1);
    expect(filterLabelIdx).toBeGreaterThan(filterSvgIdx);
    expect(filterChunk).toContain("M3 5.2h14M6 10h8M8.5 14.8h3");
    expect(filterChunk).not.toContain("sb-group-chevron");
    expect(filterChunk).not.toContain("M4.8 7.5L10 12.7 15.2 7.5");

    // 2 problems -> dynamic badge updates to 2
    const catalog = publicCatalog();
    useAppStore.getState().loadEnvelope(catalog[0].envelope, catalog[0].id);
    useAppStore.getState().loadEnvelope(catalog[1].envelope, catalog[1].id);
    const htmlTwo = renderSidebar();
    expect(htmlTwo).toContain('<span class="sb-group-count" id="sb-problem-count">2</span>');
  });

  it("updates aria-expanded, chevron path, and #sb-problem-list collapsed state cleanly on toggle", () => {
    const htmlExpanded = renderSidebar();
    expect(htmlExpanded).toContain('aria-expanded="true"');
    expect(htmlExpanded).toContain('data-group-collapsed="false"');
    expect(htmlExpanded).toContain("M4.8 7.5L10 12.7 15.2 7.5");

    useAppStore.getState().toggleLeftRailProblemGroup();
    const htmlCollapsed = renderSidebar();
    expect(htmlCollapsed).toContain('aria-expanded="false"');
    expect(htmlCollapsed).toContain('data-group-collapsed="true"');
    expect(htmlCollapsed).toContain("M7.5 4.8L12.7 10 7.5 15.2");
    expect(htmlCollapsed).toMatch(/class="sb-problem-list is-collapsed"[^>]*hidden=""/);

    useAppStore.getState().setLeftRailProblemFilter("ready");
    const htmlFiltered = renderSidebar();
    expect(htmlFiltered).toContain('data-problem-filter="ready"');
    expect(htmlFiltered).toContain('<span id="sb-problem-filter-label">Sẵn sàng</span>');
  });

  it("enforces sentence-case typography, instant hover/focus chevron reveal in fixed slot, touch capability visibility, and zero decorative hover CSS", () => {
    const titleBlock = extractCssBlock(/\.sb-group-title\s*\{[^}]*\}/);
    expect(titleBlock).toContain("font-size: 12px;");
    expect(titleBlock).toContain("font-weight: 600;");
    expect(titleBlock).not.toContain("text-transform: uppercase");
    expect(titleBlock).not.toContain("letter-spacing: 0.04em");

    const toggleBlock = extractCssBlock(/\.sb-group-toggle\s*\{[^}]*\}/);
    expect(toggleBlock).toContain("flex: 0 1 auto;");
    expect(toggleBlock).toContain("padding: 0;");
    expect(toggleBlock).not.toContain("transition:");
    expect(toggleBlock).not.toContain("margin-");

    expect(globalCss).not.toMatch(/\.sb-group-toggle:hover\s*\{/);

    const chevronBlock = extractCssBlock(/\.sb-group-chevron\s*\{[^}]*\}/);
    expect(chevronBlock).toContain("width: 14px;");
    expect(chevronBlock).toContain("height: 14px;");
    expect(chevronBlock).toContain("visibility: hidden;");
    expect(chevronBlock).toContain("opacity: 0;");
    expect(chevronBlock).not.toContain("display: none");
    expect(chevronBlock).not.toContain("transition:");

    const chevronSvgBlock = extractCssBlock(/\.sb-group-chevron\s+svg\s*\{[^}]*\}/);
    expect(chevronSvgBlock).toContain("width: 11px;");
    expect(chevronSvgBlock).toContain("height: 11px;");

    expect(globalCss).toMatch(
      /\.sb-group-toggle:hover\s+\.sb-group-chevron,\s*\.sb-group-toggle:focus-visible\s+\.sb-group-chevron\s*\{\s*visibility:\s*visible;\s*opacity:\s*1;\s*\}/s,
    );
    expect(globalCss).toMatch(
      /@media\s*\(hover:\s*none\),\s*\(pointer:\s*coarse\)\s*\{[^}]*\.sb-group-chevron\s*\{\s*visibility:\s*visible;\s*opacity:\s*1;\s*\}/s,
    );

    const filterBlock = extractCssBlock(/\.sb-filter-trigger-btn\s*\{[^}]*\}/);
    expect(filterBlock).not.toContain("transition:");
    expect(globalCss).not.toMatch(/\.sb-filter-trigger-btn:hover/);
  });
});
