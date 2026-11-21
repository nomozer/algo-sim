import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

function srgbToLinear(c: number): number {
  const s = c / 255;
  return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
}

function relLuminance(hex: string): number {
  const clean = hex.replace("#", "");
  const r = parseInt(clean.slice(0, 2), 16);
  const g = parseInt(clean.slice(2, 4), 16);
  const b = parseInt(clean.slice(4, 6), 16);
  return 0.2126 * srgbToLinear(r) + 0.7152 * srgbToLinear(g) + 0.0722 * srgbToLinear(b);
}

function contrastRatio(fgHex: string, bgHex: string): number {
  const l1 = relLuminance(fgHex);
  const l2 = relLuminance(bgHex);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

describe("AXO Landing Page — Design System & WCAG AA Token Audit", () => {
  const landingCssPath = path.resolve(__dirname, "../landing/landing.css");
  const tokensCssPath = path.resolve(__dirname, "../../styles/tokens.css");
  const landingCss = fs.readFileSync(landingCssPath, "utf8");
  const tokensCss = fs.readFileSync(tokensCssPath, "utf8");

  it("uses zero raw color hex literals inside landing.css and delegates all theme colors to tokens.css", () => {
    const colorHexMatches = landingCss.match(/#[0-9a-fA-F]{3,8}\b/g) ?? [];
    const propertyHexMatches = landingCss
      .split(/\r?\n/)
      .filter((line) => line.includes(":") && !line.trim().startsWith("/*"))
      .filter((line) => /#[0-9a-fA-F]{3,8}\b/.test(line));
    expect(propertyHexMatches).toEqual([]);
    expect(colorHexMatches.filter((m) => /^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/.test(m))).toEqual([]);

    expect(landingCss).toContain("var(--primary)");
    expect(landingCss).toContain("var(--primary-active)");
    expect(landingCss).toContain("var(--on-primary)");
    expect(landingCss).toContain("var(--accent-orange)");
    expect(landingCss).toContain("var(--accent-orange-deep)");
    expect(landingCss).toContain("var(--canvas)");
    expect(landingCss).toContain("var(--canvas-soft)");
    expect(landingCss).toContain("var(--ink)");
    expect(landingCss).toContain("var(--ink-secondary)");
    expect(landingCss).toContain("var(--ink-muted)");
    expect(landingCss).toContain("var(--hairline)");
  });

  it("assigns Primary Blue CTA and WCAG AA (>= 4.5:1) accessible ink/accent combinations", () => {
    const extractToken = (name: string): string => {
      const m = tokensCss.match(new RegExp(`${name}:\\s*(#[0-9a-fA-F]{6});`));
      if (!m) throw new Error(`Missing token ${name}`);
      return m[1];
    };

    const primary = extractToken("--primary");
    const primaryActive = extractToken("--primary-active");
    const onPrimary = extractToken("--on-primary");
    const canvas = extractToken("--canvas");
    const canvasSoft = extractToken("--canvas-soft");
    const ink = extractToken("--ink");
    const inkSecondary = extractToken("--ink-secondary");
    const inkMuted = extractToken("--ink-muted");
    const skyTint = extractToken("--accent-sky-tint");

    expect(contrastRatio(onPrimary, primary)).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio(primaryActive, canvas)).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio(primaryActive, canvasSoft)).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio(primaryActive, skyTint)).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio(ink, skyTint)).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio(inkSecondary, skyTint)).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio(inkSecondary, canvasSoft)).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio(inkMuted, canvasSoft)).toBeGreaterThanOrEqual(4.5);

    expect(landingCss).toMatch(/\.axo-about-link\s*\{[^}]*var\(--axo-sp-accent-active\)/);
    expect(landingCss).toMatch(/\.axo-sample-row-arrow\s*\{[^}]*var\(--axo-sp-accent-active\)/);
  });
});
