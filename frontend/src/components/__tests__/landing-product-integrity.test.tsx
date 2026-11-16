import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { LandingPreviewV14 } from "../landing/LandingPreviewV14";
import { LandingInteractiveDemo } from "../landing/LandingInteractiveDemo";
import { LandingClosingV14 } from "../landing/LandingClosingV14";
import { STORY_STAGES_V14 } from "../landing/LandingStorytellingV14";
import {
  LANDING_CUBE_SAMPLE,
  LANDING_PYRAMID_SAMPLE,
} from "../landing/landing-geometry-data";

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

describe("AXO Landing V1.4 — Zero Pre-Displayed Answers & Product Honesty Guard", () => {
  it("contains zero numerical answers or dimension formulas in LandingPreviewV14 SSR output", () => {
    const html = renderToStaticMarkup(<LandingPreviewV14 />);
    for (const pat of FORBIDDEN_ANSWERS) {
      expect(html).not.toContain(pat);
    }
    expect(html).not.toContain("axo-sp-demo-metrics");
    expect(html).not.toContain("axo-v14-story-verified");
    expect(html).not.toContain("axo-sp-scene-hint");
  });

  it("keeps ALL 4 steps of BOTH Pyramid and Cube answer-free in V1.4 presentation without mutating Workspace sample metrics", () => {
    for (const sample of [LANDING_PYRAMID_SAMPLE, LANDING_CUBE_SAMPLE]) {
      expect(sample.verifiedMetrics.length).toBeGreaterThanOrEqual(2);
      for (const stage of sample.milestones) {
        const joined = [
          stage.v14StepLabel ?? "",
          stage.v14Title ?? "",
          stage.v14Guide ?? "",
          stage.v14Focus ?? "",
        ].join(" ");
        for (const pat of FORBIDDEN_ANSWERS) {
          expect(joined).not.toContain(pat);
        }
      }
    }

    const demoV14Html = renderToStaticMarkup(<LandingInteractiveDemo presentation="v14" />);
    expect(demoV14Html).toContain("axo-v14-demo-focus-note");
    expect(demoV14Html).toContain("axo-v14-btn-primary");
    expect(demoV14Html).not.toContain("axo-sp-demo-toolbar-title");
    expect(demoV14Html).not.toContain("axo-sp-demo-metrics");

    for (const stage of STORY_STAGES_V14) {
      const text = `${stage.chapterHeading} ${stage.title} ${stage.summary} ${stage.relationNote}`;
      for (const pat of FORBIDDEN_ANSWERS) {
        expect(text).not.toContain(pat);
      }
    }

    const closingHtml = renderToStaticMarkup(<LandingClosingV14 />);
    expect(closingHtml).toContain('id="landing-closing-scene3d"');
    expect(closingHtml).toContain('data-section-edges="6"');
    for (const pat of FORBIDDEN_ANSWERS) {
      expect(closingHtml).not.toContain(pat);
    }
  });
});
