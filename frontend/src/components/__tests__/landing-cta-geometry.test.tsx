import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import {
  buildClosingCompositionData,
  LandingClosingScene3D,
} from "../landing/LandingClosingScene3D";

describe("Landing CTA geometry — unified cube ABCD.A'B'C'D' with regular hexagon MNEPFQ", () => {
  it("constructs an exact planar regular hexagon section MNEPFQ by slicing unit cube with (MNP)", () => {
    const data = buildClosingCompositionData();

    expect(data.cubeVertices).toHaveLength(8);
    expect(data.sectionVertices).toHaveLength(6);
    expect(data.planarResiduals).toHaveLength(6);
    expect(data.sectionEdgeLengths).toHaveLength(6);
    expect(data.midpointResiduals).toHaveLength(6);

    // Every hexagon vertex lies on cutting plane -x + y + z = 2 within 1e-6
    for (const residual of data.planarResiduals) {
      expect(residual).toBeLessThan(1e-6);
    }

    // All 6 hexagon edges are equal (regular hexagon) and midpoint anchors lie on cube edges
    const firstLen = data.sectionEdgeLengths[0];
    for (const len of data.sectionEdgeLengths) {
      expect(len).toBeCloseTo(firstLen, 5);
    }
    for (const residual of data.midpointResiduals) {
      expect(residual).toBeLessThan(1e-6);
    }
  });

  it("reuses shared SpatialSceneCanvas without duplicating bespoke WebGLRenderer or leaking math answers", () => {
    const html = renderToString(<LandingClosingScene3D />);
    expect(html).toContain('id="landing-closing-scene3d"');
    expect(html).toContain('data-cta-visual="spatial-cube-hexagon-3d"');
    expect(html).toContain('data-section-edges="6"');
    expect(html).toContain("axo-sp-scene-shell");
    expect(html).toContain("is-frameless");
    expect(html).not.toContain("<button");
    expect(html).not.toContain("<table");

    const src = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingClosingScene3D.tsx"),
      "utf8",
    );
    expect(src).toContain('from "./LandingHeroScene3D"');
    expect(src).not.toContain("new THREE.WebGLRenderer(");
    expect(src).toContain("LANDING_CUBE_SAMPLE");
    expect(src).not.toContain("var(--");
    expect(src).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
  });
});
