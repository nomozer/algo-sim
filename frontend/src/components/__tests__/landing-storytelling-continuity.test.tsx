import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import {
  interpolateStoryPose,
  LandingStorytellingV14,
  projectPrismPoint3D,
  STORY_STAGES_V14,
} from "../landing/LandingStorytellingV14";

describe("AXO Landing V1.4 — Continuous Spatial Storytelling", () => {
  it("projects 3D prism points cleanly and defines all 4 sequential chapters", () => {
    expect(STORY_STAGES_V14).toHaveLength(4);
    expect(STORY_STAGES_V14.map((s) => s.desktopTag)).toEqual([
      "Từ đề bài",
      "Dựng không gian",
      "Xác lập quan hệ",
      "Kết quả",
    ]);

    const p = projectPrismPoint3D([2, 0, -1], -0.28, 0.27, 300, 220, 68);
    expect(Number.isFinite(p.x)).toBe(true);
    expect(Number.isFinite(p.y)).toBe(true);
    expect(Number.isFinite(p.z)).toBe(true);

    const mid = interpolateStoryPose(0.58, false);
    expect(mid.activeStageIndex).toBe(2);
    expect(mid.planeSweep).toBeGreaterThan(0.5);
  });

  it("enforces strict epistemic gating before Stage 4 without 4-button primary UI", () => {
    const initialHtml = renderToStaticMarkup(<LandingStorytellingV14 />);
    expect(initialHtml).toContain('id="cach-hoat-dong"');
    expect(initialHtml).toContain("axo-v14-anno-underline");
    expect(initialHtml).toContain("từng lớp không gian");
    expect(initialHtml).not.toContain('id="btn-landing-story-step-0"');
    expect(initialHtml).not.toContain('id="btn-landing-story-step-3"');
    expect(initialHtml).toContain('id="landing-storytelling-scene"');
    expect(initialHtml).toContain('data-story-chapter="0"');
    expect(initialHtml).toContain('data-story-chapter="3"');

    // Final area and edge metric ratios must NOT appear in Stage 0 initial view
    expect(initialHtml).not.toContain("3√7");
    expect(initialHtml).not.toContain("MQ = NP = 2√2");

    // Stage 4 spec alone holds the verified result
    for (const s of STORY_STAGES_V14.slice(0, 3)) {
      expect(s.verifiedResult).toBeUndefined();
      expect(s.relationNote).not.toContain("2√2");
    }
    expect(STORY_STAGES_V14[3].verifiedResult).toBe("S(MNPQ) = 3√7");
    expect(STORY_STAGES_V14[3].relationNote).toContain("MQ = NP = 2√2");
  });

  it("uses 0 WebGL contexts and preserves token hygiene", () => {
    const source = readFileSync(
      resolve(__dirname, "../landing/LandingStorytellingV14.tsx"),
      "utf8",
    );
    expect(source).not.toContain("var(--");
    expect(source).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(source).not.toContain("WebGLRenderer");
    expect(source).toContain("cancelAnimationFrame");
    expect(source).toContain("prefers-reduced-motion: reduce");
  });
});
