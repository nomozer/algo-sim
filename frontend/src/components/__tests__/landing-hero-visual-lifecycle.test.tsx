import fs from "node:fs";
import path from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it } from "vitest";
import { useAuthStore, type AuthUser } from "../../state/auth";
import { LandingView } from "../LandingView";
import { canonicalPathForView, resolveLocationRoute } from "../AxoErrorExperience";
import { LandingHeroV14, HERO_SCENES, HERO_SCENE_DWELL_MS, nextHeroSceneIndex } from "../landing/LandingHeroV14";

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

  it("renders simplified editorial Hero copy (zero supporting facts) + frameless automatic 3-scene SVG showcase with minimal pause controls", () => {
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
    expect(heroSlice).toContain("axo-v14-hero-copy");
    expect(heroPlainText).toContain("Hình học không gian,");
    expect(heroPlainText).toContain("dễ hình dung hơn.");
    expect(heroSlice).not.toContain("axo-v14-hero-keyword");
    expect(heroSlice).not.toContain("axo-v14-hero-keyword-ring");
    // Removed supporting facts & old sample-card chrome
    expect(heroSlice).not.toContain("axo-v14-hero-facts");
    expect(heroPlainText).not.toContain("Đọc đề tiếng Việt");
    expect(heroPlainText).not.toContain("Dựng hình từng bước");
    expect(heroPlainText).not.toContain("Xoay góc nhìn 3D");
    expect(heroSlice).not.toContain("hero-specimen-tab-");
    expect(heroSlice).not.toContain("btn-landing-hero-open-specimen");
    expect(heroSlice).not.toContain("hero-pyramid-section.png");

    const h1Match = heroSlice.match(/<h1[^>]*>([\s\S]*?)<\/h1>/);
    const h1Text = (h1Match?.[1] ?? "").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
    expect(h1Text).toBe("Hình học không gian, dễ hình dung hơn.");
    expect(heroSlice).toContain('id="btn-landing-hero-start"');
    expect(heroSlice).toContain("Bắt đầu dựng hình");
    expect(heroSlice).toContain('id="btn-landing-hero-about"');
    expect(heroSlice).toContain("Tìm hiểu về Axo");

    // Automatic geometric SVG showcase
    expect(heroSlice).toContain('id="landing-hero-sculpture"');
    expect(heroSlice).toContain('data-hero-mode="automatic-geometric-showcase"');
    expect(heroSlice).toContain('id="hero-scene-dodecahedron"');
    expect(heroSlice).toContain('id="hero-scene-cylinder-section"');
    expect(heroSlice).toContain('id="hero-scene-dihedral-planes"');
    expect(heroSlice).toContain('id="hero-scene-dot-0"');
    expect(heroSlice).toContain('id="hero-scene-dot-1"');
    expect(heroSlice).toContain('id="hero-scene-dot-2"');
    expect(heroSlice).toContain('id="hero-scene-toggle"');
    expect(heroSlice).not.toContain("aria-live");
    expect(heroSlice).not.toContain("/assets/landing/hero-studio/");
    expect(heroSlice).not.toContain("<canvas");
    expect(heroSlice).not.toContain("12√3");

    const viewBoxMatches = heroSlice.match(/viewBox="54 42 372 336"/g) ?? [];
    expect(viewBoxMatches.length).toBe(3);

    expect(HERO_SCENE_DWELL_MS).toBe(6000);
    const sequence: string[] = [HERO_SCENES[0].id];
    let idx = 0;
    for (let step = 0; step < 6; step += 1) {
      idx = nextHeroSceneIndex(idx);
      sequence.push(HERO_SCENES[idx].id);
    }
    expect(sequence).toEqual([
      "dodecahedron",
      "cylinder-section",
      "dihedral-planes",
      "dodecahedron",
      "cylinder-section",
      "dihedral-planes",
      "dodecahedron",
    ]);

    useAuthStore.setState({ user: TEST_STUDENT_USER });
    syncAuthStoreForSSR();
    const authHtml = renderToStaticMarkup(<LandingHeroV14 />);
    expect(authHtml).toContain("Vào ứng dụng");
    expect(authHtml).not.toContain("Đăng nhập ngay");
  });

  it("verifies Hero lifecycle guards (visibilitychange, IntersectionObserver, reduced-motion, timer cleanup), 7 remaining product renders, and removed Hero/AI PNGs", () => {
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

    const heroSrc = fs.readFileSync(path.join(landingDir, "LandingHeroV14.tsx"), "utf8");
    expect(heroSrc).toContain("visibilitychange");
    expect(heroSrc).toContain("IntersectionObserver");
    expect(heroSrc).toContain("clearTimeout");
    expect(heroSrc).toContain("prefers-reduced-motion: reduce");
    expect(heroSrc).not.toContain("aria-live");

    const landingCss = fs.readFileSync(path.join(landingDir, "landing.css"), "utf8");
    expect(landingCss).not.toContain(".axo-v14-hero-facts");
    expect(landingCss).not.toContain(".axo-v14-hero-plate");

    for (const relAsset of [
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
      "public/assets/landing/product-renders/hero-pyramid-section.png",
      "public/assets/landing/product-renders/hero-sphere-pyramid.png",
      "public/assets/landing/product-renders/hero-distance-plane.png",
      "public/assets/landing/hero-studio/hero-studio-diorama.png",
      "public/assets/landing/hero-studio/hero-float-plane.png",
      "public/assets/landing/hero-studio/hero-float-orbit.png",
      "public/assets/landing/studio-scenes/closing-scene.png",
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
