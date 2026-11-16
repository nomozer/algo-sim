import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { LandingStorytellingV14, STORY_STAGES_V14 } from "../landing/LandingStorytellingV14";
import { LANDING_PRISM_STORY_SPEC } from "../landing/landing-geometry-data";

describe("AXO Landing — Storytelling Scene Continuity & Geometric Epistemics", () => {
  it("defines 4 continuous Vietnamese storytelling chapters without pre-displayed numerical answers", () => {
    expect(STORY_STAGES_V14).toHaveLength(4);
    expect(STORY_STAGES_V14.map((s) => s.chapterHeading)).toEqual([
      "Chặng 1: Từ đề bài",
      "Chặng 2: Dựng không gian",
      "Chặng 3: Xác lập quan hệ",
      "Chặng 4: Hoàn thiện thiết diện",
    ]);

    for (const stage of STORY_STAGES_V14) {
      expect(stage.relationNote).not.toContain("3√7");
      expect(stage.relationNote).not.toContain("2√2");
      expect(stage.relationNote).not.toContain("MN = 2");
      expect(stage.relationNote).not.toContain("PQ = 4");
      expect(stage.summary).not.toContain("a = 4");
    }
  });

  it("mounts a single sticky storytelling runway without leaking answers or extra WebGL", () => {
    const html = renderToString(<LandingStorytellingV14 />);
    const sceneMatches = html.match(/id="landing-storytelling-scene"/g) ?? [];
    expect(sceneMatches).toHaveLength(1);
    expect(html).toContain("ABC.A′B′C′");
    expect(html).toContain("axo-v14-story-runway");
    expect(html).not.toContain("S(MNPQ) = 3√7");
    expect(html).not.toContain("MQ = NP = 2√2");
    expect(html).not.toContain("a = 4");
  });

  it("verifies underlying LANDING_PRISM_STORY_SPEC coordinates satisfy MN=2, PQ=4, MQ=NP=2√2, MN∥PQ, and S(MNPQ)=3√7", () => {
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

    const vMN = p["N"].domainXyz.map((c, i) => c - p["M"].domainXyz[i]);
    const vPQ = p["P"].domainXyz.map((c, i) => c - p["Q"].domainXyz[i]);
    const crossNorm = Math.hypot(
      vMN[1] * vPQ[2] - vMN[2] * vPQ[1],
      vMN[2] * vPQ[0] - vMN[0] * vPQ[2],
      vMN[0] * vPQ[1] - vMN[1] * vPQ[0],
    );
    expect(crossNorm).toBeCloseTo(0, 6);

    const height = Math.sqrt(mq * mq - Math.pow((pq - mn) / 2, 2));
    const area = ((mn + pq) / 2) * height;
    expect(height).toBeCloseTo(Math.sqrt(7), 6);
    expect(area).toBeCloseTo(3 * Math.sqrt(7), 6);
  });
});
