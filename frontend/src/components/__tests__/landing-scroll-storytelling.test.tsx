import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import {
  computeChapterEnvelope,
  computeStoryScrollProgress,
  interpolateStoryPose,
  LandingStorytellingV14,
  projectPrismPoint3D,
  STORY_STAGES_V14,
} from "../landing/LandingStorytellingV14";

describe("AXO Landing — Scroll-Driven Spatial Storytelling", () => {
  it("computes monotonic normalized scroll progress across runway and guarantees non-overlapping chapter dissolve", () => {
    // travel = runwayHeight - stickyHeight = 2000 - 800 = 1200
    expect(computeStoryScrollProgress(120, 2000, 800)).toBe(0);
    expect(computeStoryScrollProgress(0, 2000, 800)).toBe(0);
    expect(computeStoryScrollProgress(-600, 2000, 800)).toBeCloseTo(0.5, 4);
    expect(computeStoryScrollProgress(-1200, 2000, 800)).toBe(1);
    expect(computeStoryScrollProgress(-1500, 2000, 800)).toBe(1);

    // At every normalized progress step in [0, 1], EXACTLY ONE chapter has opacity > 0 (zero blink, zero overlap)
    for (let step = 0; step <= 100; step++) {
      const p = step / 100;
      const visibleCount = [0, 1, 2, 3].filter(
        (idx) => computeChapterEnvelope(p, idx, false).opacity > 0,
      ).length;
      expect(visibleCount).toBe(1);
    }

    // All 4 chapters keep complete prism structure, consistent height & scale (no half-broken stage 1 or zoom pumping)
    for (const s of STORY_STAGES_V14) {
      expect(s.camera.extrude).toBe(1);
      expect(s.camera.zoom).toBe(1);
      expect(s.camera.prismBuild).toBe(1);
    }

    // Reduced motion exposes all chapters statically without dissolve fade
    for (const idx of [0, 1, 2, 3]) {
      expect(computeChapterEnvelope(0.3, idx, true)).toEqual({
        opacity: 1,
        offsetY: 0,
        isVisible: true,
      });
    }

    // Continuous monotonic interpolation across [0, 1]
    const samples = [0, 0.16, 0.34, 0.5, 0.64, 0.88, 1];
    const poses = samples.map((p) => interpolateStoryPose(p, false));
    for (let i = 1; i < poses.length; i++) {
      expect(poses[i].extrude).toBeGreaterThanOrEqual(poses[i - 1].extrude);
      expect(poses[i].prismBuild).toBeGreaterThanOrEqual(poses[i - 1].prismBuild);
      expect(poses[i].planeSweep).toBeGreaterThanOrEqual(poses[i - 1].planeSweep);
      expect(poses[i].traceProgress).toBeGreaterThanOrEqual(poses[i - 1].traceProgress);
      expect(poses[i].sectionFill).toBeGreaterThanOrEqual(poses[i - 1].sectionFill);
    }

    // Point Q stays absent during Stage 1–2 and appears only in Stage 3–4 once parallel construction begins
    const pStage1 = interpolateStoryPose(0.1, false);
    const pStage2Mid = interpolateStoryPose(0.38, false);
    const pStage2Late = interpolateStoryPose(0.45, false);
    const pStage3 = interpolateStoryPose(0.65, false);
    const pStage4 = interpolateStoryPose(0.95, false);
    expect(pStage1.activeStageIndex >= 2 && (pStage1.parallelCue > 0.25 || pStage1.traceProgress > 0.56)).toBe(false);
    expect(pStage2Mid.activeStageIndex >= 2 && (pStage2Mid.parallelCue > 0.25 || pStage2Mid.traceProgress > 0.56)).toBe(false);
    expect(pStage2Late.activeStageIndex >= 2 && (pStage2Late.parallelCue > 0.25 || pStage2Late.traceProgress > 0.56)).toBe(false);
    expect(pStage3.activeStageIndex >= 2 && (pStage3.parallelCue > 0.25 || pStage3.traceProgress > 0.56)).toBe(true);
    expect(pStage4.activeStageIndex >= 2 && (pStage4.parallelCue > 0.25 || pStage4.traceProgress > 0.56)).toBe(true);

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

  it("removes fixed 4-button tablist UI and keeps ALL 4 chapters free of numerical answers", () => {
    const html = renderToStaticMarkup(<LandingStorytellingV14 />);

    expect(html).toContain('id="cach-hoat-dong"');
    expect(html).toContain('id="landing-storytelling-scene"');
    expect(html).not.toContain('role="tablist"');
    expect(html).not.toContain('id="btn-landing-story-step-0"');
    expect(html).not.toContain('id="btn-landing-story-step-3"');

    // All 4 scroll chapters present in DOM
    for (const stage of STORY_STAGES_V14) {
      expect(html).toContain(stage.chapterHeading);
    }
    expect(html).toContain("axo-v14-story-context-line");

    // Zero pre-displayed computed answers AND zero assumed lateral edge length inferred from "lăng trụ tam giác đều"
    expect(html).not.toContain("a = 4");
    expect(html).not.toContain("tất cả các cạnh bằng 4");
    expect(html).toContain("Giả thiết");
    expect(html).toContain("Đối tượng đã dựng");
    expect(html).toContain("Quan hệ quan sát được");
    expect(html).toContain("Kết quả xác lập");
    expect(html).not.toContain("3√7");
    expect(html).not.toContain("2√2");
    expect(html).not.toContain("MN = 2");
    expect(html).not.toContain("PQ = 4");
    expect(html).not.toContain("axo-v14-story-verified");

    for (const s of STORY_STAGES_V14) {
      expect(s.summary).not.toContain("3√7");
      expect(s.summary).not.toContain("2√2");
      expect(s.relationNote).not.toContain("3√7");
      expect(s.relationNote).not.toContain("2√2");
      expect(s.relationNote).not.toContain("MN = 2");
      expect(s.relationNote).not.toContain("PQ = 4");
    }

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
    expect(src).not.toContain("buildParallelChevronD");
    expect(src).toContain("Hình thật thiết diện");
    expect(src).toContain('{ passive: true }');
    expect(src).toContain("cancelAnimationFrame");
    expect(src).toContain("prefers-reduced-motion: reduce");
  });
});
