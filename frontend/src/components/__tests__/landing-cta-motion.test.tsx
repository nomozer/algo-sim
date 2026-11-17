import { describe, expect, it } from "vitest";
import {
  CLOSING_SECTION_FILL_OPACITY,
  CLOSING_STORYBOARD_MS,
  evaluateClosingStoryboard,
} from "../landing/LandingClosingScene3D";

describe("Landing CTA hexagonal-prism 4-beat finite exploration storyboard & reduced-motion states", () => {
  it("progresses monotonically through prism-emergence -> cutting-plane -> intersection-trace -> exploration-settled and halts cleanly", () => {
    const b1 = evaluateClosingStoryboard(CLOSING_STORYBOARD_MS * 0.12, false);
    const b2 = evaluateClosingStoryboard(CLOSING_STORYBOARD_MS * 0.34, false);
    const b3 = evaluateClosingStoryboard(CLOSING_STORYBOARD_MS * 0.62, false);
    const b4 = evaluateClosingStoryboard(CLOSING_STORYBOARD_MS + 10, false);

    expect(b1.beat).toBe("prism-emergence");
    expect(b1.settled).toBe(false);
    expect(b1.planeOpacity).toBe(0);
    expect(b1.capLift).toBe(0);

    expect(b2.beat).toBe("cutting-plane");
    expect(b2.planeOpacity).toBeGreaterThan(0.2);
    expect(b2.sectionFillOpacity).toBe(0);
    expect(b2.capLift).toBe(0);

    expect(b3.beat).toBe("intersection-trace");
    expect(b3.traceProgress).toBeGreaterThan(0.35);

    expect(b4.beat).toBe("exploration-settled");
    expect(b4.settled).toBe(true);
    expect(b4.planeOpacity).toBe(1);
    expect(b4.traceProgress).toBe(1);
    expect(b4.sectionFillOpacity).toBe(1);
    expect(b4.capLift).toBeGreaterThan(0.15);
    expect(CLOSING_SECTION_FILL_OPACITY).toBe(0.56);
  });

  it("locks immediately to final settled exploration composition when prefers-reduced-motion is active", () => {
    for (const ms of [0, 600, 1800, 3600]) {
      const reduced = evaluateClosingStoryboard(ms, true);
      expect(reduced.reducedMotion).toBe(true);
      expect(reduced.settled).toBe(true);
      expect(reduced.beat).toBe("exploration-settled");
      expect(reduced.planeOpacity).toBe(1);
      expect(reduced.traceProgress).toBe(1);
      expect(reduced.sectionFillOpacity).toBe(1);
      expect(reduced.capLift).toBeGreaterThan(0.15);
    }
  });
});
