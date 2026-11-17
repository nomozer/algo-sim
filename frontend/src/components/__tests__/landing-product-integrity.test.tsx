import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { LandingPreviewV14 } from "../landing/LandingPreviewV14";
import { LandingInteractiveDemo } from "../landing/LandingInteractiveDemo";
import { LandingClosingV14 } from "../landing/LandingClosingV14";
import { STORY_STAGES_V14 } from "../landing/LandingStorytellingV14";
import {
  computeShowcaseCameraPreset,
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
    expect(demoV14Html).toContain("axo-v14-demo-model-name");
    expect(demoV14Html).toContain("axo-v14-demo-focus-note");
    expect(demoV14Html).toContain("axo-v14-btn-primary");
    expect(demoV14Html).not.toContain("axo-sp-demo-toolbar-title");
    expect(demoV14Html).not.toContain("axo-sp-demo-metrics");

    // Bounding-box + normal-aware showcase presets show both sections clearly without edge-on grazing
    const cubePreset = computeShowcaseCameraPreset(LANDING_CUBE_SAMPLE.points, [-1, 1, -1], {
      azimuthBias: 0.22,
      elevationRad: 0.46,
      distanceScale: 3.52,
    });
    expect(cubePreset.normalCosine).toBeGreaterThanOrEqual(0.65);
    expect(cubePreset.lookAt).toEqual([0, 0, 0]);
    for (const ms of LANDING_CUBE_SAMPLE.milestones) {
      expect(ms.v14CameraPos).toEqual(cubePreset.cameraPos);
      expect(ms.v14LookAt).toEqual(cubePreset.lookAt);
    }

    const pyrPreset = computeShowcaseCameraPreset(LANDING_PYRAMID_SAMPLE.points, [1, 2, -1], {
      azimuthBias: 0.14,
      elevationRad: 0.45,
      distanceScale: 3.55,
    });
    expect(pyrPreset.normalCosine).toBeGreaterThanOrEqual(0.65);
    expect(pyrPreset.lookAt[1]).toBeCloseTo(0.35, 3);
    for (const ms of LANDING_PYRAMID_SAMPLE.milestones) {
      expect(ms.v14CameraPos).toEqual(pyrPreset.cameraPos);
      expect(ms.v14LookAt).toEqual(pyrPreset.lookAt);
    }

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
