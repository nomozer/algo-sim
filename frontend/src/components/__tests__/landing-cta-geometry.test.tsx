import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import {
  buildClosingCompositionData,
  LandingClosingScene3D,
} from "../landing/LandingClosingScene3D";

describe("Landing CTA geometry — studio pyramid S.ABCD with planar pentagon MENPF", () => {
  it("constructs an exact planar pentagon section MENPF by slicing pyramid S.ABCD with (MNP)", () => {
    const data = buildClosingCompositionData();

    expect(data.pyramidVertices).toHaveLength(5);
    expect(data.sectionVertices).toHaveLength(5);
    expect(data.planarResiduals).toHaveLength(5);
    expect(data.midpointResiduals).toHaveLength(3);
    expect(data.lowerFrustumFaceCount).toBe(5);
    expect(data.upperCapFaceCount).toBe(5);
    expect(data.companionCount).toBe(3);

    // Every section vertex lies on cutting plane x + y + 2z = 6 within 1e-6
    for (const residual of data.planarResiduals) {
      expect(residual).toBeLessThan(1e-6);
    }

    // Seed points M, N, P lie at exact edge midpoints
    for (const residual of data.midpointResiduals) {
      expect(residual).toBeLessThan(1e-6);
    }
  });

  it("renders pure answer-free pyramid composition with zero textbook letter clutter", () => {
    const html = renderToString(<LandingClosingScene3D />);
    expect(html).toContain('id="landing-closing-scene3d"');
    expect(html).toContain('data-section-edges="5"');
    expect(html).toContain("axo-v14-closing-visual");
    expect(html).not.toContain("axo-sp-point-tag");
    expect(html).not.toContain("<button");
    expect(html).not.toContain("<table");

    const src = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingClosingScene3D.tsx"),
      "utf8",
    );
    expect(src).toContain("LANDING_PYRAMID_SAMPLE");
    expect(src).toContain("computeTrueShapeSection2D");
    expect(src).toContain("spatial-pyramid-editorial-3d");
    expect(src).not.toContain("MeshPhysicalMaterial");
    expect(src).not.toContain("var(--");
    expect(src).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
  });
});
