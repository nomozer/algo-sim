import { describe, expect, it } from "vitest";
import {
  CLOSING_SECTION_FILL_OPACITY,
  CLOSING_STORYBOARD_MS,
  evaluateClosingStoryboard,
} from "../landing/LandingClosingScene3D";

describe("Landing CTA cube-to-hexagon 4-beat finite storyboard & reduced-motion states", () => {
  it("progresses monotonically through cube-solid -> cutting-plane -> intersection-trace -> hexagon-settled and halts cleanly", () => {
    const b1 = evaluateClosingStoryboard(CLOSING_STORYBOARD_MS * 0.12, false);
    const b2 = evaluateClosingStoryboard(CLOSING_STORYBOARD_MS * 0.34, false);
    const b3 = evaluateClosingStoryboard(CLOSING_STORYBOARD_MS * 0.62, false);
    const b4 = evaluateClosingStoryboard(CLOSING_STORYBOARD_MS + 10, false);

    expect(b1.beat).toBe("cube-solid");
    expect(b1.settled).toBe(false);
    expect(b1.planeOpacity).toBe(0);

    expect(b2.beat).toBe("cutting-plane");
    expect(b2.planeOpacity).toBeGreaterThan(0.2);
    expect(b2.sectionFillOpacity).toBe(0);

    expect(b3.beat).toBe("intersection-trace");
    expect(b3.sectionProgress).toBeGreaterThan(0.35);

    expect(b4.beat).toBe("hexagon-settled");
    expect(b4.settled).toBe(true);
    expect(b4.planeOpacity).toBeGreaterThan(0.4);
    expect(b4.sectionProgress).toBe(1);
    expect(b4.sectionFillOpacity).toBeGreaterThan(0.8);
    expect(CLOSING_SECTION_FILL_OPACITY).toBe(0.28);
  });

  it("locks immediately to final settled hexagon composition when prefers-reduced-motion is active", () => {
    for (const ms of [0, 600, 1800, 3400]) {
      const reduced = evaluateClosingStoryboard(ms, true);
      expect(reduced.reducedMotion).toBe(true);
      expect(reduced.settled).toBe(true);
      expect(reduced.beat).toBe("hexagon-settled");
      expect(reduced.planeOpacity).toBeGreaterThan(0.4);
      expect(reduced.sectionProgress).toBe(1);
      expect(reduced.sectionFillOpacity).toBeGreaterThan(0.8);
    }
  });
});
