import { describe, expect, it } from "vitest";
import {
  GOLDEN_PORTAL_HEIGHT,
  REFERENCE_PORTAL_SPECS,
} from "../EnterPortalsRefApp";

describe("Gate 1 Enter Portals reference reconstruction specification", () => {
  it("matches the 3 reference portals, golden aspect ratio, and symmetric curved layout", () => {
    expect(GOLDEN_PORTAL_HEIGHT).toBeCloseTo((1 + Math.sqrt(5)) / 2, 9);
    expect(REFERENCE_PORTAL_SPECS).toHaveLength(3);

    expect(REFERENCE_PORTAL_SPECS.map((p) => p.id)).toEqual(["01", "02", "03"]);
    expect(REFERENCE_PORTAL_SPECS[0].position).toEqual([-1.15, 0, 0]);
    expect(REFERENCE_PORTAL_SPECS[0].rotation).toEqual([0, 0.5, 0]);
    expect(REFERENCE_PORTAL_SPECS[0].bg).toBe("#e4cdac");

    expect(REFERENCE_PORTAL_SPECS[1].position).toEqual([0, 0, 0]);
    expect(REFERENCE_PORTAL_SPECS[1].rotation).toEqual([0, 0, 0]);

    expect(REFERENCE_PORTAL_SPECS[2].position).toEqual([1.15, 0, 0]);
    expect(REFERENCE_PORTAL_SPECS[2].rotation).toEqual([0, -0.5, 0]);
    expect(REFERENCE_PORTAL_SPECS[2].bg).toBe("#d1d1ca");
  });
});
