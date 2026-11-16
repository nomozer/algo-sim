import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import {
  buildClosingCompositionData,
  LandingClosingScene3D,
} from "../landing/LandingClosingScene3D";

describe("Landing CTA geometry — regular hexagonal prism exploration rig with oblique hexagon section", () => {
  it("constructs an exact planar 6-vertex oblique hexagon section by slicing a regular hexagonal prism", () => {
    const data = buildClosingCompositionData();

    expect(data.prismBottomVertices).toHaveLength(6);
    expect(data.prismTopVertices).toHaveLength(6);
    expect(data.sectionVertices).toHaveLength(6);
    expect(data.planarResiduals).toHaveLength(6);
    expect(data.baseRadiusResiduals).toHaveLength(6);
    expect(data.lowerFrustumFaceCount).toBe(7);
    expect(data.upperCapFaceCount).toBe(7);
    expect(data.companionCount).toBe(3);

    // Every section vertex lies on exploration cutting plane within 1e-6
    for (const residual of data.planarResiduals) {
      expect(residual).toBeLessThan(1e-6);
    }

    // All 6 base vertices lie strictly on circumcircle radius R within 1e-6
    for (const rResidual of data.baseRadiusResiduals) {
      expect(rResidual).toBeLessThan(1e-6);
    }
  });

  it("renders a distinct answer-free exploration composition without duplicating the Hero pyramid", () => {
    const html = renderToString(<LandingClosingScene3D />);
    expect(html).toContain('id="landing-closing-scene3d"');
    expect(html).toContain('data-section-edges="6"');
    expect(html).toContain("axo-v14-closing-visual");
    expect(html).not.toContain("axo-sp-point-tag");
    expect(html).not.toContain("<button");
    expect(html).not.toContain("<table");

    const src = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingClosingScene3D.tsx"),
      "utf8",
    );
    expect(src).not.toContain("LANDING_PYRAMID_SAMPLE");
    expect(src).toContain("spatial-polyhedra-exploration-3d");
    expect(src).not.toContain("MeshPhysicalMaterial");
    expect(src).not.toContain("var(--");
    expect(src).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
  });
});
