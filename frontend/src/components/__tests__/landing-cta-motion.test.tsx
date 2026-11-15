import { describe, expect, it } from "vitest";
import {
  CLOSING_CYCLE_DURATION_MS,
  evaluateClosingMotionState,
} from "../landing/LandingClosingScene3D";

describe("Landing CTA 3D continuous construction & reduced-motion states", () => {
  it("progresses cleanly through Phases A -> B -> C -> D without abrupt jumps", () => {
    const phaseA = evaluateClosingMotionState(CLOSING_CYCLE_DURATION_MS * 0.08, false);
    const phaseB = evaluateClosingMotionState(CLOSING_CYCLE_DURATION_MS * 0.30, false);
    const phaseC = evaluateClosingMotionState(CLOSING_CYCLE_DURATION_MS * 0.58, false);
    const phaseD = evaluateClosingMotionState(CLOSING_CYCLE_DURATION_MS * 0.80, false);

    expect(phaseA.phase).toBe("base-pyramid");
    expect(phaseA.planeProgress).toBe(0);
    expect(phaseA.traceProgress).toBe(0);
    expect(phaseA.sectionFillOpacity).toBe(0);

    expect(phaseB.phase).toBe("plane-emergence");
    expect(phaseB.planeProgress).toBeGreaterThan(0.35);
    expect(phaseB.traceProgress).toBe(0);

    expect(phaseC.phase).toBe("section-intersection");
    expect(phaseC.planeProgress).toBe(1);
    expect(phaseC.traceProgress).toBeGreaterThan(0.5);
    expect(phaseC.sectionFillOpacity).toBeGreaterThan(0);

    expect(phaseD.phase).toBe("complete-settled");
    expect(phaseD.planeProgress).toBe(1);
    expect(phaseD.traceProgress).toBe(1);
    expect(phaseD.sectionFillOpacity).toBe(1);
  });

  it("maintains seamless C0 periodic loop wrap at cycle boundaries", () => {
    const start = evaluateClosingMotionState(0, false);
    const end = evaluateClosingMotionState(CLOSING_CYCLE_DURATION_MS, false);
    const nearEnd = evaluateClosingMotionState(CLOSING_CYCLE_DURATION_MS - 4, false);

    expect(Math.abs(start.planeProgress - end.planeProgress)).toBeLessThan(1e-6);
    expect(Math.abs(start.traceProgress - end.traceProgress)).toBeLessThan(1e-6);
    expect(Math.abs(start.sectionFillOpacity - end.sectionFillOpacity)).toBeLessThan(1e-6);
    expect(Math.abs(start.orbitAngleRad - end.orbitAngleRad)).toBeLessThan(1e-6);

    expect(nearEnd.planeProgress).toBeLessThan(0.05);
    expect(nearEnd.traceProgress).toBeLessThan(0.05);
    expect(nearEnd.sectionFillOpacity).toBeLessThan(0.05);
    expect(Math.abs(nearEnd.orbitAngleRad)).toBeLessThan(0.01);
  });

  it("locks to static complete composition when prefers-reduced-motion is active", () => {
    const sampleTimes = [0, 1200, 4800, 7900, 9400];
    for (const ms of sampleTimes) {
      const reduced = evaluateClosingMotionState(ms, true);
      expect(reduced.reducedMotion).toBe(true);
      expect(reduced.phase).toBe("complete-settled");
      expect(reduced.planeProgress).toBe(1);
      expect(reduced.traceProgress).toBe(1);
      expect(reduced.sectionFillOpacity).toBe(1);
      expect(reduced.orbitAngleRad).toBe(0);
      expect(reduced.capLift).toBe(0);
    }
  });

  it("supports deterministic mid and settled QA preview overrides", () => {
    const mid = evaluateClosingMotionState(0, false, "mid");
    const settled = evaluateClosingMotionState(0, false, "settled");

    expect(mid.phase).toBe("section-intersection");
    expect(mid.traceProgress).toBeGreaterThan(0.4);
    expect(mid.traceProgress).toBeLessThan(1);

    expect(settled.phase).toBe("complete-settled");
    expect(settled.traceProgress).toBe(1);
    expect(settled.sectionFillOpacity).toBe(1);
  });
});
