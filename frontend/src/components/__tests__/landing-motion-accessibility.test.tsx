import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { LandingView, readLandingPrototypeMode } from "../LandingView";
import { LandingPreviewV14 } from "../landing/LandingPreviewV14";

describe("AXO Landing — Prototype Isolation, Motion Accessibility & Token Hygiene", () => {
  it("parses query-gated preview mode deterministically and preserves V1.2.2 by default", () => {
    expect(readLandingPrototypeMode("")).toBe("prod");
    expect(readLandingPrototypeMode("?foo=1")).toBe("prod");
    expect(readLandingPrototypeMode("?prototype=unknown")).toBe("prod");
    expect(readLandingPrototypeMode("?prototype=a")).toBe("prod");
    expect(readLandingPrototypeMode("?prototype=b")).toBe("prod");
    expect(readLandingPrototypeMode("?preview=v1.4")).toBe("v14");
    expect(readLandingPrototypeMode("?preview=V14")).toBe("v14");
    expect(readLandingPrototypeMode("?prototype=v1.4")).toBe("v14");
    expect(readLandingPrototypeMode("?prototype=v14")).toBe("v14");

    const defaultHtml = renderToString(<LandingView />);
    expect(defaultHtml).toContain('id="landing-hero"');
    expect(defaultHtml).toContain('id="landing-storytelling-scene"');
    expect(defaultHtml).toContain('id="landing-final-cta"');
    expect(defaultHtml).not.toContain('id="landing-v13-review-banner"');
    expect(defaultHtml).not.toContain("axo-v14-root");
    expect(defaultHtml).not.toContain("PENDING_OWNER_REVIEW");
  });

  it("renders preview V1.4 cleanly without WebGL storytelling overhead and with accessible fallbacks", () => {
    const html = renderToString(<LandingPreviewV14 />);

    expect(html).toContain('id="landing-hero-sculpture"');
    expect(html).toContain('id="landing-storytelling-scene"');
    expect(html).toContain('id="landing-demo-scene"');
    expect(html).toContain('id="landing-closing-scene3d"');
    expect(html).not.toContain("axo-v13-");

    // Storytelling section remains 100% WebGL-free
    const storyStart = html.indexOf('id="cach-hoat-dong"');
    const demoStart = html.indexOf('id="trai-nghiem"');
    const storySlice = html.slice(storyStart, demoStart);
    expect(storySlice).not.toContain("<canvas");
    expect(storySlice).toContain("<svg");
  });

  it("enforces prefers-reduced-motion styles, zero inline CSS tokens, and never auto-approves deliverables", () => {
    const landingCss = fs.readFileSync(
      path.resolve(__dirname, "../landing/landing.css"),
      "utf8",
    );

    expect(landingCss).toContain("@media (prefers-reduced-motion: reduce)");
    expect(landingCss).not.toContain(".axo-v13-");

    for (const rel of [
      "../landing/LandingHeroV14.tsx",
      "../landing/LandingStorytellingV14.tsx",
      "../landing/LandingClosingScene3D.tsx",
      "../landing/LandingClosingV14.tsx",
    ]) {
      const src = fs.readFileSync(path.resolve(__dirname, rel), "utf8");
      expect(src).not.toContain("var(--");
      expect(src).not.toMatch(/import\s+["'][^"']*\.css["']/);
      expect(src).not.toContain("APPROVED_BY_USER");
    }

    for (const motionRel of [
      "../landing/LandingHeroV14.tsx",
      "../landing/LandingStorytellingV14.tsx",
      "../landing/LandingClosingScene3D.tsx",
    ]) {
      const motionSrc = fs.readFileSync(path.resolve(__dirname, motionRel), "utf8");
      expect(motionSrc).toContain("prefers-reduced-motion: reduce");
    }
  });
});
