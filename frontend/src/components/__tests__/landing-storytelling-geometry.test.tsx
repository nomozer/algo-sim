import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { LandingPrototypeA, V13_STORY_SCENES } from "../landing/LandingPrototypeA";
import { LandingPrototypeB } from "../landing/LandingPrototypeB";
import { LANDING_PRISM_STORY_SPEC } from "../landing/landing-geometry-data";

describe("AXO Landing Page V1.3 — Storytelling Scene Continuity & Geometric Epistemics", () => {
  it("defines 4 continuous Vietnamese storytelling stages with strict Stage 4 result gating", () => {
    expect(V13_STORY_SCENES).toHaveLength(4);
    expect(V13_STORY_SCENES.map((s) => s.stepLabel)).toEqual([
      "Bước 1",
      "Bước 2",
      "Bước 3",
      "Bước 4",
    ]);
    expect(V13_STORY_SCENES.map((s) => s.title)).toEqual([
      "Đề bài xuất hiện",
      "Hình thành không gian",
      "Khám phá quan hệ",
      "Kết quả trực quan",
    ]);

    for (let idx = 0; idx < 3; idx++) {
      const chipText = V13_STORY_SCENES[idx].stageChips.map((c) => c.label).join(" | ");
      expect(chipText).not.toContain("3√7");
      expect(chipText).not.toContain("S(MNPQ)");
      expect(V13_STORY_SCENES[idx].stageChips.every((c) => c.emphasis !== "result")).toBe(true);
    }

    const stage4Text = V13_STORY_SCENES[3].stageChips.map((c) => c.label).join(" | ");
    expect(stage4Text).toContain("MN = 2");
    expect(stage4Text).toContain("PQ = 4");
    expect(stage4Text).toContain("MQ = NP = 2√2");
    expect(stage4Text).toContain("S(MNPQ) = 3√7");
    expect(V13_STORY_SCENES[3].stageChips.some((c) => c.emphasis === "result")).toBe(true);
  });

  it("mounts a single storytelling stage in both Prototypes A and B without leaking Stage 4 area in Stage 0 HUD", () => {
    for (const html of [
      renderToString(<LandingPrototypeA onSwitchMode={() => undefined} />),
      renderToString(<LandingPrototypeB onSwitchMode={() => undefined} />),
    ]) {
      const sceneMatches = html.match(/id="landing-storytelling-scene"/g) ?? [];
      expect(sceneMatches).toHaveLength(1);

      const bottomStart = html.indexOf('class="axo-sp-story-bottom-bar"');
      const copyStart = html.indexOf('class="axo-v13-story-copy-col"');
      expect(bottomStart).toBeGreaterThan(-1);
      expect(copyStart).toBeGreaterThan(bottomStart);

      const stage0BottomBar = html.slice(bottomStart, copyStart);
      expect(stage0BottomBar).toContain("Giả thiết: Lăng trụ đều ABC.A′B′C′ (a = 4)");
      expect(stage0BottomBar).not.toContain("S(MNPQ) = 3√7");
      expect(stage0BottomBar).not.toContain("MQ = NP = 2√2");
      expect(stage0BottomBar).not.toContain("MN = 2");
    }
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
