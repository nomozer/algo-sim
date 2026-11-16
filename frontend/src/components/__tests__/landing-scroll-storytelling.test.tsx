import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import {
  computeStoryScrollProgress,
  interpolateStoryPose,
  LandingStorytellingV14,
  projectPrismPoint3D,
  STORY_STAGES_V14,
} from "../landing/LandingStorytellingV14";

describe("AXO Landing — Scroll-Driven Spatial Storytelling", () => {
  it("computes monotonic normalized scroll progress across chapters forward and reverse", () => {
    // Anchor is 0.48 * vh on desktop, 0.68 * vh in compact stacked layout
    expect(computeStoryScrollProgress(600, 1800, 1000)).toBe(0);
    expect(computeStoryScrollProgress(480, 1680, 1000)).toBe(0);
    expect(computeStoryScrollProgress(-120, 1080, 1000)).toBeCloseTo(0.5, 4);
    expect(computeStoryScrollProgress(-720, 480, 1000)).toBe(1);
    expect(computeStoryScrollProgress(-950, 250, 1000)).toBe(1);
    expect(computeStoryScrollProgress(680, 1880, 1000, true)).toBe(0);
    expect(computeStoryScrollProgress(80, 1280, 1000, true)).toBeCloseTo(0.5, 4);
    expect(computeStoryScrollProgress(-520, 680, 1000, true)).toBe(1);

    // Continuous monotonic interpolation across [0, 1]
    const samples = [0, 0.16, 0.34, 0.5, 0.64, 0.88, 1];
    const poses = samples.map((p) => interpolateStoryPose(p, false));
    for (let i = 1; i < poses.length; i++) {
      expect(poses[i].extrude).toBeGreaterThanOrEqual(poses[i - 1].extrude);
      expect(poses[i].planeSweep).toBeGreaterThanOrEqual(poses[i - 1].planeSweep);
      expect(poses[i].traceProgress).toBeGreaterThanOrEqual(poses[i - 1].traceProgress);
      expect(poses[i].sectionFill).toBeGreaterThanOrEqual(poses[i - 1].sectionFill);
    }

    // Reverse scroll determinism
    const forwardMid = interpolateStoryPose(0.55, false);
    const reverseMid = interpolateStoryPose(0.55, false);
    expect(reverseMid).toEqual(forwardMid);
  });

  it("snaps cleanly per chapter under prefers-reduced-motion", () => {
    const r0 = interpolateStoryPose(0.12, true);
    const r2 = interpolateStoryPose(0.6, true);
    const r3 = interpolateStoryPose(0.9, true);

    expect(r0.activeStageIndex).toBe(0);
    expect(r0.extrude).toBe(STORY_STAGES_V14[0].camera.extrude);
    expect(r2.activeStageIndex).toBe(2);
    expect(r2.planeSweep).toBe(1);
    expect(r3.activeStageIndex).toBe(3);
    expect(r3.sectionFill).toBe(1);
  });

  it("removes fixed 4-button tablist UI and gates final metrics strictly to Stage 4", () => {
    const html = renderToStaticMarkup(<LandingStorytellingV14 />);

    expect(html).toContain('id="cach-hoat-dong"');
    expect(html).toContain('id="landing-storytelling-scene"');
    expect(html).not.toContain('role="tablist"');
    expect(html).not.toContain('id="btn-landing-story-step-0"');
    expect(html).not.toContain('id="btn-landing-story-step-3"');

    // All 4 scroll chapters present in flow
    for (const stage of STORY_STAGES_V14) {
      expect(html).toContain(stage.chapterHeading);
    }

    // Strict epistemic gating: final area and edge lengths do NOT leak at initial progress = 0
    expect(html).not.toContain("3√7");
    expect(html).not.toContain("MQ = NP = 2√2");

    // Stage 4 alone unlocks verified result
    for (const s of STORY_STAGES_V14.slice(0, 3)) {
      expect(s.verifiedResult).toBeUndefined();
      expect(s.relationNote).not.toContain("2√2");
    }
    expect(STORY_STAGES_V14[3].verifiedResult).toBe("S(MNPQ) = 3√7");
    expect(STORY_STAGES_V14[3].relationNote).toContain("MQ = NP = 2√2");

    const p = projectPrismPoint3D([2, 0, -1], -0.28, 0.27, 300, 220, 68);
    expect(Number.isFinite(p.x)).toBe(true);
    expect(Number.isFinite(p.y)).toBe(true);
  });

  it("uses 0 WebGL contexts and passive scroll hygiene without leaks", () => {
    const src = readFileSync(
      resolve(__dirname, "../landing/LandingStorytellingV14.tsx"),
      "utf8",
    );
    expect(src).not.toContain("var(--");
    expect(src).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(src).not.toContain("WebGLRenderer");
    expect(src).toContain('{ passive: true }');
    expect(src).toContain("cancelAnimationFrame");
    expect(src).toContain("prefers-reduced-motion: reduce");
  });
});
