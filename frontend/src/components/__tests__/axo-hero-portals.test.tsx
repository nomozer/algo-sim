import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { canonicalPathForView, resolveLocationRoute } from "../AxoErrorExperience";
import { LandingView, readLandingPrototypeMode } from "../LandingView";
import {
  LANDING_CUBE_SAMPLE,
  LANDING_PRISM_STORY_SPEC,
  LANDING_PYRAMID_SAMPLE,
} from "../landing/landing-geometry-data";
import { GOLDEN_PORTAL_HEIGHT } from "../landing/portals/PortalEngine";
import {
  AXO_HERO_CAMERA_FOV,
  AXO_PORTAL_CARDS,
  AxoHeroPortalFallback,
  AxoHeroPortals,
  computeAxoPortalCameraZ,
} from "../landing/portals/AxoHeroPortals";

describe("AXO Landing Hero Portal Integration — Routing, Responsive Framing & Fallback", () => {
  it("resolves /about as canonical landing path while keeping /gioi-thieu alias & 404 safety", () => {
    expect(canonicalPathForView("landing")).toBe("/about");
    expect(resolveLocationRoute("/about")).toEqual({ kind: "view", view: "landing" });
    expect(resolveLocationRoute("/gioi-thieu")).toEqual({ kind: "view", view: "landing" });
    expect(resolveLocationRoute("/app")).toEqual({ kind: "view", view: "home" });
    expect(resolveLocationRoute("/unknown-route-404")).toEqual({
      kind: "not_found",
      requestedPath: "/unknown-route-404",
    });
  });

  it("parses English kebab-case ?preview modes and falls back safely on unknown queries", () => {
    expect(readLandingPrototypeMode("")).toBe("prod");
    expect(readLandingPrototypeMode("?preview=portal-reference")).toBe("portal-reference");
    expect(readLandingPrototypeMode("?preview=axo-hero")).toBe("axo-hero");
    expect(readLandingPrototypeMode("?preview=v1.4")).toBe("v14");
    expect(readLandingPrototypeMode("?preview=unknown-value")).toBe("prod");
    expect(readLandingPrototypeMode("?preview=invalid")).toBe("prod");
  });

  it("binds all 3 Axo Hero portals to verified mathematical solids without invented geometry", () => {
    expect(GOLDEN_PORTAL_HEIGHT).toBeCloseTo((1 + Math.sqrt(5)) / 2, 9);
    expect(AXO_PORTAL_CARDS.map((c) => c.id)).toEqual([
      "construction",
      "exploration",
      "relationships",
    ]);
    expect(AXO_PORTAL_CARDS.map((c) => c.sampleId)).toEqual([
      LANDING_PRISM_STORY_SPEC.id,
      LANDING_CUBE_SAMPLE.id,
      LANDING_PYRAMID_SAMPLE.id,
    ]);
  });

  it("computes unclipped responsive camera Z framing across desktop, tablet, and 320px mobile aspects", () => {
    const tanHalfFov = Math.tan((AXO_HERO_CAMERA_FOV * Math.PI) / 360);
    const halfClusterW = 1.6;
    const frontZOffset = 0.24;

    const aspects = [
      1.6, // 768x1024 single-column wide box
      1.3, // 1920x1080 / 1366x768 desktop right column
      1.25, // 1440x900 desktop right column
      1.15, // 1024x768 narrow desktop column
      1.09, // 390x844 mobile stage
      0.95, // 320x568 smallest mobile stage
    ];

    for (const aspect of aspects) {
      const z = computeAxoPortalCameraZ(aspect);
      expect(Number.isFinite(z)).toBe(true);
      expect(z).toBeGreaterThan(2.5);
      const distFromFrontPlane = z - frontZOffset;
      const visibleHalfH = distFromFrontPlane * tanHalfFov;
      const visibleHalfW = visibleHalfH * aspect;
      expect(visibleHalfH).toBeGreaterThan(GOLDEN_PORTAL_HEIGHT * 0.5);
      expect(visibleHalfW).toBeGreaterThan(halfClusterW);
    }

    // Narrower mobile viewports pull camera farther back monotonically
    expect(computeAxoPortalCameraZ(0.95)).toBeGreaterThan(computeAxoPortalCameraZ(1.3));
  });

  it("renders accessible SVG fallback and 3 portal keyboard controls in non-WebGL / SSR environments", () => {
    const html = renderToString(<AxoHeroPortals />);
    expect(html).toContain('id="axo-hero-portals-stage"');
    expect(html).toContain('id="axo-portal-fallback"');
    expect(html).toContain('id="axo-portal-pill-bar"');
    expect(html).toContain('id="btn-axo-portal-construction"');
    expect(html).toContain('id="btn-axo-portal-exploration"');
    expect(html).toContain('id="btn-axo-portal-relationships"');

    const activeFallback = renderToString(<AxoHeroPortalFallback activePortal="relationships" />);
    expect(activeFallback).toContain("MENPF");
    expect(activeFallback).toContain("Mở trong Xưởng 3D");
  });

  it("keeps stable LandingView SSR output unchanged without prototype activation", () => {
    const prodHtml = renderToString(<LandingView />);
    expect(prodHtml).toContain("axo-sp-hero-sculpture");
    expect(prodHtml).toContain('id="cach-hoat-dong"');
    expect(prodHtml).toContain('id="trai-nghiem"');
    expect(prodHtml).toContain('id="landing-final-cta"');
    expect(prodHtml).toContain('id="landing-footer"');
    expect(prodHtml).not.toContain('id="axo-hero-portals-stage"');
    expect(prodHtml).not.toContain("axo-ref-portal-stage");
  });

  it("shares PortalEngine cleanly without importing rejected A/B/C hero modules", () => {
    const enginePath = path.resolve(__dirname, "../landing/portals/PortalEngine.tsx");
    const axoPath = path.resolve(__dirname, "../landing/portals/AxoHeroPortals.tsx");
    expect(fs.existsSync(enginePath)).toBe(true);
    const axoSrc = fs.readFileSync(axoPath, "utf8");
    expect(axoSrc).toContain("./PortalEngine");
    expect(axoSrc).not.toContain("wouter");
    expect(axoSrc).not.toContain("@pmndrs/branding");
    expect(axoSrc).not.toContain("HeroStaticVariant");
    expect(axoSrc).not.toContain("HeroInteractiveVariant");
    expect(axoSrc).not.toContain("HeroHybridVariant");
  });
});
