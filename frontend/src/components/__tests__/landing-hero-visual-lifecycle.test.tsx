import fs from "node:fs";
import path from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it } from "vitest";
import { useAuthStore, type AuthUser } from "../../state/auth";
import { LandingView } from "../LandingView";
import { canonicalPathForView, resolveLocationRoute } from "../AxoErrorExperience";
import { LandingHeroV14 } from "../landing/LandingHeroV14";

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

describe("AXO Landing — Hero Baseline, Unified Studio 3D Assets & Routing Lifecycle", () => {
  afterEach(() => {
    useAuthStore.setState({ user: null });
    syncAuthStoreForSSR();
  });

  it("maps canonical /about route, handles legacy /gioi-thieu alias, and removes preview query branches", () => {
    expect(canonicalPathForView("landing")).toBe("/about");
    expect(resolveLocationRoute("/about")).toEqual({ kind: "view", view: "landing" });
    expect(resolveLocationRoute("/about", "", "?preview=landing-v14")).toEqual({
      kind: "view",
      view: "landing",
    });
    expect(resolveLocationRoute("/gioi-thieu")).toEqual({ kind: "view", view: "landing" });
    expect(resolveLocationRoute("/app")).toEqual({ kind: "view", view: "home" });

    const landingViewSrc = fs.readFileSync(path.resolve(__dirname, "../LandingView.tsx"), "utf8");
    const appSrc = fs.readFileSync(path.resolve(__dirname, "../../App.tsx"), "utf8");
    expect(landingViewSrc).not.toContain("preview");
    expect(landingViewSrc).not.toContain("LandingPreview");
    expect(appSrc).toContain('searchParams.delete("preview")');
  });

  it("renders preserved left Hero copy with keyword ring + Atelier studio diorama visual on right", () => {
    useAuthStore.setState({ user: null });
    syncAuthStoreForSSR();
    const html = renderToStaticMarkup(<LandingView />);
    const heroStart = html.indexOf('id="landing-hero"');
    const aboutStart = html.indexOf('id="about-axo"');
    expect(heroStart).toBeGreaterThan(-1);
    expect(aboutStart).toBeGreaterThan(heroStart);

    const heroSlice = html.slice(heroStart, aboutStart);
    const heroPlainText = heroSlice.replace(/<[^>]+>/g, "").replace(/\s+/g, " ");
    expect(heroSlice).toContain('id="axo-v14-hero-heading"');
    expect(heroSlice).toContain("axo-v14-hero-atelier");
    expect(heroPlainText).toContain("Hình học không gian,");
    expect(heroPlainText).toContain("dễ hình dung hơn.");
    expect(heroSlice).toContain("axo-v14-hero-keyword");
    expect(heroSlice).toContain("axo-v14-hero-keyword-ring");
    expect(heroSlice).toContain('aria-hidden="true"');
    expect(heroSlice).toContain('focusable="false"');
    expect(heroSlice).toContain('preserveAspectRatio="none"');
    expect(heroSlice).toContain('pathLength="1"');
    const h1Match = heroSlice.match(/<h1[^>]*>([\s\S]*?)<\/h1>/);
    const h1Text = (h1Match?.[1] ?? "").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
    expect(h1Text).toBe("Hình học không gian, dễ hình dung hơn.");
    expect(heroSlice).toContain('id="btn-landing-hero-start"');
    expect(heroSlice).toContain("Bắt đầu dựng hình");
    expect(heroSlice).toContain('id="btn-landing-hero-about"');
    expect(heroSlice).toContain("Tìm hiểu về Axo");
    expect(heroSlice).toContain('id="landing-hero-sculpture"');
    expect(heroSlice).toContain('data-hero-mode="atelier-studio-diorama"');
    expect(heroSlice).toContain("/assets/landing/hero-studio/hero-studio-diorama.png");
    expect(heroSlice).toContain("/assets/landing/hero-studio/hero-float-plane.png");
    expect(heroSlice).toContain("/assets/landing/hero-studio/hero-float-orbit.png");
    expect(heroSlice).not.toContain("<canvas");
    expect(heroSlice).not.toContain("12√3");

    useAuthStore.setState({ user: TEST_STUDENT_USER });
    syncAuthStoreForSSR();
    const authHtml = renderToStaticMarkup(<LandingHeroV14 />);
    expect(authHtml).toContain("Vào ứng dụng");
    expect(authHtml).not.toContain("Đăng nhập ngay");
  });

  it("verifies redesigned Landing component files, 4 Brand 3D PNGs + 6 Real Axo product renders exist, obsolete stylized PNGs are deleted, and zero WebGL deps", () => {
    const feRoot = path.resolve(__dirname, "../../..");
    const landingDir = path.resolve(__dirname, "../landing");
    const landingFiles = fs.readdirSync(landingDir).sort();
    expect(landingFiles).toEqual([
      "LandingAboutAxo.tsx",
      "LandingFooter.tsx",
      "LandingHeader.tsx",
      "LandingHeroV14.tsx",
      "LandingHowItWorks.tsx",
      "LandingSamples.tsx",
      "landing-geometry-data.ts",
      "landing.css",
      "useLandingReveal.ts",
    ]);

    for (const relAsset of [
      "public/assets/landing/hero-studio/hero-studio-diorama.png",
      "public/assets/landing/hero-studio/hero-float-plane.png",
      "public/assets/landing/hero-studio/hero-float-orbit.png",
      "public/assets/landing/studio-scenes/closing-scene.png",
      "public/assets/landing/product-renders/about-cube-section.png",
      "public/assets/landing/product-renders/sample-pyramid-section.png",
      "public/assets/landing/product-renders/how-step-construct.png",
      "public/assets/landing/product-renders/how-step-inspect.png",
      "public/assets/landing/product-renders/sample-oxyz-intersection.png",
      "public/assets/landing/product-renders/sample-distance-plane.png",
      "public/assets/landing/product-renders/sample-sphere-pyramid.png",
    ]) {
      expect(fs.existsSync(path.join(feRoot, relAsset)), `Missing asset ${relAsset}`).toBe(true);
    }

    for (const removedAsset of [
      "public/assets/landing/studio-scenes/about-scene.png",
      "public/assets/landing/studio-scenes/how-it-works-scene.png",
      "public/assets/landing/studio-scenes/samples-scene.png",
    ]) {
      expect(fs.existsSync(path.join(feRoot, removedAsset)), `Obsolete asset still present: ${removedAsset}`).toBe(false);
    }

    const pkg = JSON.parse(fs.readFileSync(path.join(feRoot, "package.json"), "utf8")) as {
      dependencies?: Record<string, string>;
    };
    expect(pkg.dependencies?.["@react-three/fiber"]).toBeUndefined();
    expect(pkg.dependencies?.["@react-three/drei"]).toBeUndefined();
    expect(pkg.dependencies?.["maath"]).toBeUndefined();
  });
});
