import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import {
  buildClosingCompositionData,
  LandingClosingScene3D,
} from "../landing/LandingClosingScene3D";

describe("Landing CTA geometry — multi-solid hexagonal prism + companion cone spatial composition", () => {
  it("constructs an exact planar oblique 6-gon section and spatially separated companion cone", () => {
    const data = buildClosingCompositionData();

    expect(data.prismBottom).toHaveLength(6);
    expect(data.prismTop).toHaveLength(6);
    expect(data.prismSection).toHaveLength(6);
    expect(data.prismPlaneQuad).toHaveLength(4);

    // Every oblique section vertex satisfies planar equation within 1e-6
    for (const residual of data.prismPlanarResiduals) {
      expect(residual).toBeLessThan(1e-6);
    }

    // All 6 section intersection vertices lie strictly interior along vertical lateral edges
    for (let k = 0; k < 6; k++) {
      expect(data.prismSection[k][1]).toBeGreaterThan(data.prismBottom[k][1]);
      expect(data.prismSection[k][1]).toBeLessThan(data.prismTop[k][1]);
    }

    // Companion cone horizontal section radius satisfies similar-triangle proportion R*(1 - t)
    const t = (data.coneSectionHeightY - data.coneBaseCenter[1]) / data.coneHeight;
    expect(data.coneSectionRadius).toBeCloseTo(data.coneRadius * (1 - t), 6);

    // Hexagonal prism and companion cone remain spatially separated without solid overlap
    expect(data.solidCenterGap).toBeGreaterThan(1.42 + data.coneRadius);
  });

  it("renders a single WebGL canvas host + SVG fallback without Sphere SVG or leaked math answers", () => {
    const html = renderToString(<LandingClosingScene3D />);
    expect(html).toContain('id="landing-closing-scene3d"');
    expect(html).toContain('data-cta-visual="spatial-multi-solid-3d"');
    expect(html).toContain("axo-v14-closing-canvas-host");
    expect(html).toContain("axo-v14-closing-fallback-svg");
    expect(html).not.toContain("axo-v14-svg-sphere");
    expect(html).not.toContain("<button");
    expect(html).not.toContain("<table");

    const src = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingClosingScene3D.tsx"),
      "utf8",
    );
    expect((src.match(/new THREE\.WebGLRenderer\(/g) ?? [])).toHaveLength(1);
    expect(src).not.toContain("LANDING_PYRAMID_SAMPLE");
    expect(src).not.toContain("var(--");
    expect(src).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
  });
});
