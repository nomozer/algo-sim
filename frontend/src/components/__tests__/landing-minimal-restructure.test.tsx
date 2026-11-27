import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { PUBLIC_GEOMETRY_SAMPLES } from "../../data/geometry-samples";
import { publicCatalog } from "../../data/offline-catalog";
import { registerAllSimulations } from "../../simulations";
import { useAppStore } from "../../state/store";
import { LandingView } from "../LandingView";
import { openSampleInWorkspace } from "../landing/landing-geometry-data";

const FORBIDDEN_ANSWERS = [
  "6√6",
  "= 32",
  "12√3",
  "2√2",
  "3√7",
  "MN = 2",
  "PQ = 4",
  "V(S.ABCD)",
  "S(MENPF)",
  "S(MNEPFQ)",
  "S(MNPQ)",
] as const;

describe("AXO Landing Redesign — 5-Band Architecture, Real Samples, Studio 3D Assets & Motion Contract", () => {
  it("renders Header, Hero, 3 distinct post-Hero sections (Về Axo, Cách hoạt động, Bài mẫu), and Two-Tier Footer Closing Scene", () => {
    const html = renderToStaticMarkup(<LandingView />);

    expect(html).toContain('id="view-landing"');
    expect(html).toContain('id="landing-header"');
    expect(html).toContain('id="landing-hero"');
    expect(html).toContain('id="about-axo"');
    expect(html).toContain('id="cach-hoat-dong"');
    expect(html).toContain('id="bai-mau"');
    expect(html).toContain('id="landing-final-cta"');
    expect(html).toContain('id="landing-footer"');

    // Frameless Automatic Hero SVG Scenes + Real Axo Workspace 3D renders + Axonometric Closing SVG
    expect(html).toContain('id="hero-scene-dodecahedron"');
    expect(html).toContain('id="hero-scene-cylinder-section"');
    expect(html).toContain('id="hero-scene-dihedral-planes"');
    expect(html).not.toContain("hero-pyramid-section.png");
    expect(html).not.toContain("axo-v14-hero-facts");
    expect(html).toContain("/assets/landing/product-renders/about-cube-section.png");
    expect(html).toContain("/assets/landing/product-renders/sample-pyramid-section.png");
    expect(html).toContain("/assets/landing/product-renders/how-step-construct.png");
    expect(html).toContain("/assets/landing/product-renders/how-step-inspect.png");
    expect(html).toContain("/assets/landing/product-renders/sample-sphere-pyramid.png");
    expect(html).toContain("/assets/landing/product-renders/sample-oxyz-intersection.png");
    expect(html).toContain("/assets/landing/product-renders/sample-distance-plane.png");
    expect(html).toContain('class="axo-v14-closing-svg"');
    expect(html).not.toContain("/assets/landing/hero-studio/hero-studio-diorama.png");
    expect(html).not.toContain("/assets/landing/studio-scenes/closing-scene.png");
    expect(html).not.toContain("/assets/landing/studio-scenes/about-scene.png");
    expect(html).not.toContain("/assets/landing/studio-scenes/how-it-works-scene.png");
    expect(html).not.toContain("/assets/landing/studio-scenes/samples-scene.png");

    // Zero legacy scrollytelling / interactive demo / WebGL / review stamps / Tin học / answer dumps
    expect(html).not.toContain('id="trai-nghiem"');
    expect(html).not.toContain('id="landing-storytelling-scene"');
    expect(html).not.toContain('id="landing-product-showcase"');
    expect(html).not.toContain("<canvas");
    expect(html).not.toContain('type="range"');
    expect(html).not.toContain("Tin học");
    expect(html).not.toContain("PENDING_OWNER_REVIEW");
    expect(html).not.toContain("APPROVED_BY_USER");

    for (const pat of FORBIDDEN_ANSWERS) {
      expect(html).not.toContain(pat);
    }

    // All curated sample buttons reference real verified IDs from PUBLIC_GEOMETRY_SAMPLES
    const publicIds = new Set(PUBLIC_GEOMETRY_SAMPLES.map((s) => s.id));
    for (const sampleId of [
      "chop-thiet-dien-ba-diem",
      "oxyz-giao-diem-duong-mat",
      "khoang-cach-diem-mat-phang-nghieng",
      "chop-mat-cau-ngoai-tiep",
    ]) {
      expect(publicIds.has(sampleId), `Sample ID ${sampleId} missing from PUBLIC_GEOMETRY_SAMPLES`).toBe(true);
      expect(html).toContain(`id="btn-landing-sample-${sampleId}"`);
    }
  });

  it("enforces unified motion tokens, Hero 3-layer pointer parallax + one-shot arrival (no infinite float), reduced-motion styles, Google Inter link, and strict TSX hygiene", () => {
    const indexHtml = readFileSync(resolve(__dirname, "../../../index.html"), "utf8");
    expect(indexHtml).toContain("fonts.googleapis.com/css2?family=Inter");

    const landingCss = readFileSync(resolve(__dirname, "../landing/landing.css"), "utf8");
    expect(landingCss).toContain("@media (prefers-reduced-motion: reduce)");
    expect(landingCss).toContain("--axo-sp-t-press");
    expect(landingCss).toContain("--axo-sp-t-hover");
    expect(landingCss).toContain("--axo-sp-t-nav");
    expect(landingCss).toContain("--axo-sp-t-return");
    expect(landingCss).toContain("--axo-sp-t-enter");
    expect(landingCss).toContain("@keyframes axoHeroLayerEnter");
    expect(landingCss).not.toContain("infinite");
    expect(landingCss).toMatch(/\.axo-sp-header-inner\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\)\s+auto\s+minmax\(0,\s*1fr\)/);
    expect(landingCss).toMatch(/@media \(prefers-reduced-motion:\s*reduce\)[\s\S]*\.axo-hero-showcase-media/);
    expect(landingCss).toMatch(/@media \(prefers-reduced-motion:\s*reduce\)[\s\S]*\.axo-v14-closing-media/);
    expect(landingCss).not.toMatch(/:\s*[^;]*#[0-9a-fA-F]{3,8}\b/);

    for (const rel of [
      "../LandingView.tsx",
      "../landing/LandingHeader.tsx",
      "../landing/LandingHeroV14.tsx",
      "../landing/LandingAboutAxo.tsx",
      "../landing/LandingHowItWorks.tsx",
      "../landing/LandingSamples.tsx",
      "../landing/LandingFooter.tsx",
      "../landing/useLandingReveal.ts",
    ]) {
      const src = readFileSync(resolve(__dirname, rel), "utf8");
      expect(src, `${rel} must not contain inline var(-- tokens`).not.toContain("var(--");
      expect(src, `${rel} must not contain raw hex`).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
      expect(src, `${rel} must not import CSS directly`).not.toMatch(/import\s+["'][^"']*\.css["']/);
      expect(src).not.toContain("APPROVED_BY_USER");
      expect(src).not.toContain("PENDING_OWNER_REVIEW");
    }

    // Coverage guard for capsule pill buttons, primary/secondary hover, keyboard focus, responsive layout & cleanup
    expect(landingCss).toMatch(/\.axo-v14-btn\s*\{[^}]*border-radius:\s*var\(--rounded-full\)/);
    expect(landingCss).toContain(".axo-v14-btn:focus-visible");
    expect(landingCss).toContain(".axo-v14-btn-primary:not(:disabled):hover");
    expect(landingCss).toContain(".axo-v14-btn-secondary:not(:disabled):hover");
    expect(landingCss).toContain("overflow-x: clip");
    expect(landingCss).toContain("@media (max-width: 920px)");
    expect(landingCss).toContain("@media (max-width: 680px)");
    expect(landingCss).toContain("@media (max-width: 420px)");
    expect(landingCss).toContain("@media (hover: none)");
    expect(landingCss).not.toContain(".axo-v13-");
    expect(landingCss).not.toContain(".axo-v14-closing-motif");
    expect(landingCss).not.toContain(".axo-v14-footer-mark");

    const headerSrc = readFileSync(resolve(__dirname, "../landing/LandingHeader.tsx"), "utf8");
    expect(headerSrc).toContain("displayIdRef");
    expect(headerSrc).toContain("useState<string | null>(null)");
    expect(headerSrc).toContain("scrollHeight - window.innerHeight");

    const revealSrc = readFileSync(resolve(__dirname, "../landing/useLandingReveal.ts"), "utf8");
    expect(revealSrc).toContain("IntersectionObserver");
    expect(revealSrc).toContain("prefers-reduced-motion: reduce");

    const heroSrc = readFileSync(resolve(__dirname, "../landing/LandingHeroV14.tsx"), "utf8");
    expect(heroSrc).toContain("prefers-reduced-motion: reduce");
    expect(heroSrc).toContain("onPointerMove");
    expect(heroSrc).toContain("onPointerLeave");
    expect(heroSrc).toContain("onPointerCancel");
    expect(heroSrc).toContain('e.pointerType === "touch"');
    expect(heroSrc).toContain("cancelAnimationFrame");
    expect(heroSrc).toContain("data-pointer-active");
  });

  it("verifies all 4 curated Landing samples back real Scene3D geometry and open cleanly into Workspace", () => {
    registerAllSimulations();
    const catalogById = new Map(publicCatalog().map((s) => [s.id, s]));
    const curatedIds = [
      "chop-mat-cau-ngoai-tiep",
      "oxyz-giao-diem-duong-mat",
      "khoang-cach-diem-mat-phang-nghieng",
      "chop-thiet-dien-ba-diem",
    ] as const;

    try {
      for (const sampleId of curatedIds) {
        const entry = catalogById.get(sampleId);
        expect(entry, `Curated sample ${sampleId} must exist in publicCatalog()`).toBeDefined();
        const scene3d = (entry?.envelope as { scene3d?: { objects?: unknown[] } } | undefined)?.scene3d;
        expect(Array.isArray(scene3d?.objects) && scene3d.objects.length > 0).toBe(true);

        useAppStore.getState().setView("landing");
        openSampleInWorkspace(sampleId);
        expect(useAppStore.getState().view).toBe("workspace");
        expect(useAppStore.getState().activeSampleId).toBe(sampleId);
      }
    } finally {
      useAppStore.getState().reset();
    }
  });
});
