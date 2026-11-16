import { describe, expect, it } from "vitest";
import {
  CLOSING_SECTION_FILL_OPACITY,
  CLOSING_STORYBOARD_MS,
  evaluateClosingStoryboard,
} from "../landing/LandingClosingScene3D";

describe("Landing CTA multi-solid 4-beat finite storyboard & reduced-motion states", () => {
  it("progresses monotonically through solids -> plane -> trace -> composition-settled and halts cleanly", () => {
    const b1 = evaluateClosingStoryboard(CLOSING_STORYBOARD_MS * 0.12, false);
    const b2 = evaluateClosingStoryboard(CLOSING_STORYBOARD_MS * 0.34, false);
    const b3 = evaluateClosingStoryboard(CLOSING_STORYBOARD_MS * 0.62, false);
    const b4 = evaluateClosingStoryboard(CLOSING_STORYBOARD_MS + 10, false);

    expect(b1.beat).toBe("solids-emergence");
    expect(b1.settled).toBe(false);
    expect(b1.planeSweep).toBe(0);

    expect(b2.beat).toBe("plane-emergence");
    expect(b2.planeSweep).toBeGreaterThan(0.2);
    expect(b2.sectionFillOpacity).toBe(0);

    expect(b3.beat).toBe("section-trace");
    expect(b3.traceProgress).toBeGreaterThan(0.35);

    expect(b4.beat).toBe("composition-settled");
    expect(b4.settled).toBe(true);
    expect(b4.planeSweep).toBe(1);
    expect(b4.traceProgress).toBe(1);
    expect(b4.sectionFillOpacity).toBe(1);
    expect(b4.orbitOffsetRad).toBe(0);
    expect(CLOSING_SECTION_FILL_OPACITY).toBe(0.28);
  });

  it("locks immediately to final settled composition when prefers-reduced-motion is active", () => {
    for (const ms of [0, 600, 1800, 3400]) {
      const reduced = evaluateClosingStoryboard(ms, true);
      expect(reduced.reducedMotion).toBe(true);
      expect(reduced.settled).toBe(true);
      expect(reduced.beat).toBe("composition-settled");
      expect(reduced.planeSweep).toBe(1);
      expect(reduced.traceProgress).toBe(1);
      expect(reduced.sectionFillOpacity).toBe(1);
      expect(reduced.orbitOffsetRad).toBe(0);
    }
  });
});
