import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import {
  buildClosingSpatialRigData,
  evaluateClosingMotionState,
  LandingClosingScene3D,
  projectClosingSpatialStage,
} from "../landing/LandingClosingScene3D";

describe("Landing CTA geometry — distinct sphere-plane-circle spatial rig & mathematical accuracy", () => {
  it("satisfies x^2 + y^2 + z^2 = R^2 (R=5), z = 3, IH perp HA, and 3-4-5 right triangle", () => {
    const rig = buildClosingSpatialRigData();

    expect(rig.radiusR).toBe(5);
    expect(rig.distanceD).toBe(3);
    expect(rig.sectionRadiusR).toBe(4);
    expect(rig.circleSamples).toHaveLength(72);

    expect(rig.sphereMathResiduals.length).toBe(4);
    for (const r of rig.sphereMathResiduals) {
      expect(r).toBeLessThan(1e-6);
    }
    expect(rig.orthoDotResidual).toBeLessThan(1e-6);
    expect(rig.pythagoreanResidual).toBeLessThan(1e-6);

    for (const pt of rig.points) {
      if (pt.role === "circle_vertex") {
        expect(pt.domainXyz[2]).toBe(3);
      }
    }
  });

  it("projects a distinct sphere intersection stage without WebGL or Pyramid duplication", () => {
    const state = evaluateClosingMotionState(0, true);
    const proj = projectClosingSpatialStage(480, 360, state);

    expect(proj.sphereCenter.rPx).toBeGreaterThan(60);
    expect(proj.circleArcs).toHaveLength(72);
    expect(proj.circleFrontPath.length).toBeGreaterThan(10);
    expect(proj.equatorFrontPath.length).toBeGreaterThan(10);
    expect(proj.planePolygonPoints.split(" ")).toHaveLength(4);
    expect(proj.points["I"]).toBeDefined();
    expect(proj.points["H"]).toBeDefined();
    expect(proj.points["A"]).toBeDefined();

    const html = renderToString(<LandingClosingScene3D />);
    expect(html).toContain('id="landing-closing-scene3d"');
    expect(html).toContain('role="img"');
    expect(html).toContain('data-cta-visual="analytical-3d-svg"');
    expect(html).toContain("<path");
    expect(html).not.toContain("<canvas");
    expect(html).not.toContain("<button");
    expect(html).not.toContain("<table");

    const src = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingClosingScene3D.tsx"),
      "utf8",
    );
    expect(src).not.toContain("WebGLRenderer");
    expect(src).not.toContain("LANDING_PYRAMID_SAMPLE");
  });
});
