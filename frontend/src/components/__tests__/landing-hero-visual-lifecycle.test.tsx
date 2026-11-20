import fs from "node:fs";
import path from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it } from "vitest";
import { useAuthStore, type AuthUser } from "../../state/auth";
import { LandingView, readLandingPrototypeMode } from "../LandingView";
import { canonicalPathForView, resolveLocationRoute } from "../AxoErrorExperience";
import {
  LANDING_CUBE_SAMPLE,
  LANDING_PRISM_STORY_SPEC,
  LANDING_PYRAMID_SAMPLE,
} from "../landing/landing-geometry-data";
import { LandingHeroV14 } from "../landing/LandingHeroV14";
import { LandingPreviewV14 } from "../landing/LandingPreviewV14";
import { GOLDEN_PORTAL_HEIGHT } from "../landing/portals/PortalEngine";
import {
  AXO_V14_CAMERA_FOV,
  computeV14PortalCameraZ,
  V14_HERO_PORTAL_SPECS,
} from "../landing/portals/HeroPortalStageV14";

function syncAuthStoreForSSR() {
  Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());
}

const TEST_STUDENT_USER: AuthUser = {
  id: 101,
  email: "student@axo.edu.vn",
  displayName: "Nguyễn Minh Anh",
  role: "student",
  mustChangePassword: false,
  status: "active",
};

describe("AXO Landing V1.4 — Redesigned Enter Portals Hero, Route Normalization & Lifecycle", () => {
  afterEach(() => {
    useAuthStore.setState({ user: null });
    syncAuthStoreForSSR();
  });

  it("activates ?preview=landing-v14 (with ?preview=v1.4 alias) and rejects deprecated axo-hero/portal-reference previews", () => {
    expect(canonicalPathForView("landing")).toBe("/about");
    expect(resolveLocationRoute("/about")).toEqual({ kind: "view", view: "landing" });
    expect(resolveLocationRoute("/gioi-thieu")).toEqual({ kind: "view", view: "landing" });
    expect(resolveLocationRoute("/app")).toEqual({ kind: "view", view: "home" });

    expect(readLandingPrototypeMode("?preview=landing-v14")).toBe("v14");
    expect(readLandingPrototypeMode("?preview=v1.4")).toBe("v14");
    expect(readLandingPrototypeMode("?preview=v14")).toBe("v14");

    // Deprecated wrong previews fall back to canonical prod instead of activating separate pages
    expect(readLandingPrototypeMode("?preview=axo-hero")).toBe("prod");
    expect(readLandingPrototypeMode("?preview=portal-reference")).toBe("prod");
    expect(readLandingPrototypeMode("")).toBe("prod");

    const prodHtml = renderToStaticMarkup(<LandingView />);
    expect(prodHtml).not.toContain("axo-v14-root");
  });

  it("binds the 3 Hero portals to verified mathematical solids and keeps desktop/mobile framing unclipped", () => {
    expect(GOLDEN_PORTAL_HEIGHT).toBeCloseTo((1 + Math.sqrt(5)) / 2, 9);
    expect(V14_HERO_PORTAL_SPECS.map((p) => p.id)).toEqual([
      "construction",
      "exploration",
      "relationships",
    ]);
    expect(V14_HERO_PORTAL_SPECS.map((p) => p.sampleId)).toEqual([
      LANDING_PRISM_STORY_SPEC.id,
      LANDING_CUBE_SAMPLE.id,
      LANDING_PYRAMID_SAMPLE.id,
    ]);
    expect(V14_HERO_PORTAL_SPECS[0].rotation[1]).toBeGreaterThan(0);
    expect(V14_HERO_PORTAL_SPECS[1].position[2]).toBeGreaterThan(
      V14_HERO_PORTAL_SPECS[0].position[2],
    );
    expect(V14_HERO_PORTAL_SPECS[2].rotation[1]).toBeLessThan(0);

    const tanHalfFov = Math.tan((AXO_V14_CAMERA_FOV * Math.PI) / 360);
    const halfW = 1.59;
    const frontOffset = 0.22;

    for (const aspect of [1.5, 1.25, 1.15, 1.0, 0.875]) {
      const z = computeV14PortalCameraZ(aspect);
      const dist = z - frontOffset;
      const visibleHalfH = dist * tanHalfFov;
      const visibleHalfW = visibleHalfH * aspect;
      expect(visibleHalfH).toBeGreaterThan(GOLDEN_PORTAL_HEIGHT * 0.5);
      expect(visibleHalfW).toBeGreaterThan(halfW);
    }
  });

  it("preserves exact Landing V1.4 left copy, annotation, CTAs, and non-Hero sections with SVG fallback", () => {
    useAuthStore.setState({ user: null });
    syncAuthStoreForSSR();
    const v14Html = renderToStaticMarkup(<LandingPreviewV14 />);
    expect(v14Html).toContain("axo-v14-root");
    expect(v14Html).toContain("axo-v14-anno-circle");
    expect(v14Html).toContain('id="btn-landing-hero-start"');
    expect(v14Html).toContain("Bắt đầu dựng hình");
    expect(v14Html).toContain('id="btn-landing-hero-story"');
    expect(v14Html).toContain("Xem cách hoạt động");
    expect(v14Html).toContain('id="landing-hero-sculpture"');
    expect(v14Html).toContain('id="v14-hero-portal-fallback"');
    expect(v14Html).toContain('id="cach-hoat-dong"');
    expect(v14Html).toContain('id="trai-nghiem"');
    expect(v14Html).toContain('id="landing-final-cta"');
    expect(v14Html).toContain('id="landing-footer"');
    expect(v14Html).not.toContain("PENDING_OWNER_REVIEW");

    useAuthStore.setState({ user: TEST_STUDENT_USER });
    syncAuthStoreForSSR();
    const authHtml = renderToStaticMarkup(<LandingHeroV14 />);
    expect(authHtml).toContain("Vào ứng dụng");
    expect(authHtml).not.toContain("Đăng nhập ngay");
  });

  it("enforces cleanup of wrong previews/GLBs/Draco and enforces single Canvas + GPU disposal", () => {
    const feRoot = path.resolve(__dirname, "../../..");
    expect(fs.existsSync(path.join(feRoot, "src/prototypes/enter-portals-ref"))).toBe(false);
    expect(fs.existsSync(path.join(feRoot, "public/draco"))).toBe(false);
    expect(
      fs.existsSync(path.join(feRoot, "src/components/landing/portals/AxoHeroPortals.tsx")),
    ).toBe(false);
    expect(
      fs.existsSync(path.join(feRoot, "src/components/landing/portals/axo-portal-worlds.tsx")),
    ).toBe(false);

    const stageSrc = fs.readFileSync(
      path.join(feRoot, "src/components/landing/portals/HeroPortalStageV14.tsx"),
      "utf8",
    );
    expect((stageSrc.match(/<Canvas\b/g) ?? [])).toHaveLength(1);
    expect(stageSrc).toContain("prefers-reduced-motion: reduce");
    expect(stageSrc).toContain("IntersectionObserver");
    expect(stageSrc).toContain("HeroPortalFallbackSvg");

    const worldsSrc = fs.readFileSync(
      path.join(feRoot, "src/components/landing/portals/HeroPortalWorldsV14.tsx"),
      "utf8",
    );
    expect(worldsSrc).toContain("dispose()");
    expect(worldsSrc).not.toContain("APPROVED_BY_USER");

    const engineSrc = fs.readFileSync(
      path.join(feRoot, "src/components/landing/portals/PortalEngine.tsx"),
      "utf8",
    );
    expect(engineSrc).not.toContain("suspend-react");
    expect(engineSrc).not.toContain("@pmndrs/");
  });
});
