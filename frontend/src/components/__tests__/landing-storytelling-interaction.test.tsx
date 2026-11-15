import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { LandingExplainerAnimation } from "../landing/LandingExplainerAnimation";
import { LandingStorytelling } from "../landing/LandingStorytelling";
import { LANDING_PRISM_STORY_SPEC } from "../landing/landing-geometry-data";

describe("AXO Landing Page V1.2.2 — Vector Storytelling & Stage-Strict Math Epistemics", () => {
  it("renders zero WebGL canvas elements, keeps Stage 0 free of premature final results, and reveals all 4 verified metrics on Stage 3", () => {
    const html = renderToString(<LandingStorytelling />);

    expect(html).toContain('id="landing-storytelling-scene"');
    expect(html).toContain('data-stage="0"');
    // Option A uses deterministic vector SVG + CSS transitions, zero <canvas> / WebGL contexts
    expect(html).not.toContain("<canvas");
    expect(html).toContain("<svg");
    expect(html).toContain("axo-sp-story-runway");

    for (let i = 0; i < 4; i++) {
      expect(html).toContain(`id="btn-landing-story-step-${i}"`);
      expect(html).toContain(`id="btn-landing-story-pill-${i}"`);
    }

    // Stage 0 bottom bar shows only problem givens and never leaks premature final results at low opacity
    const bottomBarStart = html.indexOf('class="axo-sp-story-bottom-bar"');
    const bottomBarHtml = bottomBarStart >= 0 ? html.slice(bottomBarStart) : "";
    expect(bottomBarHtml).toContain("Giả thiết: Lăng trụ đều ABC.A′B′C′");
    expect(bottomBarHtml).not.toContain("S(MNPQ) = 3√7");
    expect(bottomBarHtml).not.toContain("MN = 2");
    expect(html).not.toContain("axo-sp-explainer-result-badge is-shown");
    expect(html).toContain('id="btn-landing-story-autoplay"');
    expect(html).toContain("axo-sp-story-active-card");

    const stage3Html = renderToString(
      <LandingExplainerAnimation
        selectedStage={3}
        autoPlaying={false}
        onToggleAutoPlay={() => undefined}
      />,
    );
    const pillCount = (stage3Html.match(/class="axo-sp-story-metric-pill/g) ?? []).length;
    expect(pillCount).toBe(4);
    expect(stage3Html).toContain("MN = 2");
    expect(stage3Html).toContain("PQ = 4");
    expect(stage3Html).toContain("MQ = NP = 2√2");
    expect(stage3Html).toContain("S(MNPQ) = 3√7");
  });

  it("V1.2.1: renders 4-scene animated explainer scenes without Workspace screen recording", () => {
    const explainerSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingExplainerAnimation.tsx"),
      "utf8",
    );
    expect(explainerSrc).toContain("Đề bài xuất hiện");
    expect(explainerSrc).toContain("Hình thành không gian");
    expect(explainerSrc).toContain("Khám phá quan hệ");
    expect(explainerSrc).toContain("Kết quả trực quan");
    expect(explainerSrc).not.toContain("<video");
    expect(explainerSrc).not.toContain("<canvas");
  });

  it("proves exact Regular Triangular Prism ABC.A'B'C' isosceles trapezoid MNPQ metrics from domain coordinates", () => {
    const p = LANDING_PRISM_STORY_SPEC.pointMap;
    const dist = (a: string, b: string) => {
      const u = p[a].domainXyz;
      const v = p[b].domainXyz;
      return Math.hypot(u[0] - v[0], u[1] - v[1], u[2] - v[2]);
    };

    const mn = dist("M", "N");
    const pq = dist("P", "Q");
    const mq = dist("M", "Q");
    const np = dist("N", "P");

    expect(mn).toBeCloseTo(2, 6);
    expect(pq).toBeCloseTo(4, 6);
    expect(mq).toBeCloseTo(2 * Math.SQRT2, 6);
    expect(np).toBeCloseTo(2 * Math.SQRT2, 6);

    // Parallelism MN // BC // PQ via normalized direction cosine
    const vMN = p["N"].domainXyz.map((c, i) => c - p["M"].domainXyz[i]);
    const vPQ = p["P"].domainXyz.map((c, i) => c - p["Q"].domainXyz[i]);
    const crossNorm = Math.hypot(
      vMN[1] * vPQ[2] - vMN[2] * vPQ[1],
      vMN[2] * vPQ[0] - vMN[0] * vPQ[2],
      vMN[0] * vPQ[1] - vMN[1] * vPQ[0],
    );
    expect(crossNorm).toBeCloseTo(0, 6);

    // Height & Area of isosceles trapezoid MNPQ: h = sqrt(mq^2 - ((pq - mn)/2)^2) = sqrt(7), S = 3*sqrt(7)
    const halfDiff = (pq - mn) / 2;
    const height = Math.sqrt(mq * mq - halfDiff * halfDiff);
    const area = ((mn + pq) / 2) * height;
    expect(height).toBeCloseTo(Math.sqrt(7), 6);
    expect(area).toBeCloseTo(3 * Math.sqrt(7), 6);

    // Confirm no pathLength JSX prop regression in source and compact 152vh runway CSS
    const storySrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingStorytelling.tsx"),
      "utf8",
    );
    expect(storySrc).not.toContain("pathLength=");
    const cssSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/landing.css"),
      "utf8",
    );
    expect(cssSrc).toContain("min-height: 152vh;");
  });
});
