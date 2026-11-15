import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import {
  buildClosingPyramidRigData,
  evaluateClosingMotionState,
  LandingClosingScene3D,
  projectClosingFallbackSvg,
} from "../landing/LandingClosingScene3D";
import { LANDING_PYRAMID_SAMPLE } from "../landing/landing-geometry-data";

describe("Landing CTA 3D geometry & mathematical accuracy", () => {
  it("grounds vertices, edges, and MENPF section strictly in LANDING_PYRAMID_SAMPLE", () => {
    const rig = buildClosingPyramidRigData();

    expect(rig.sectionIds).toEqual(["M", "E", "N", "P", "F"]);
    for (const pt of LANDING_PYRAMID_SAMPLE.points) {
      expect(rig.pointWorldMap[pt.id]).toEqual(pt.pos);
    }

    // All five pentagon vertices must lie strictly on cutting plane x + y + 2z = 6
    expect(rig.sectionMathResiduals).toHaveLength(5);
    for (const residual of rig.sectionMathResiduals) {
      expect(residual).toBeLessThan(1e-6);
    }

    // Exact midpoint definitions from problem statement: M(SA), N(BC), P(CD)
    const [ax, ay, az] = rig.pointMathMap.A;
    const [bx, by, bz] = rig.pointMathMap.B;
    const [cx, cy, cz] = rig.pointMathMap.C;
    const [dx, dy, dz] = rig.pointMathMap.D;
    const [sx, sy, sz] = rig.pointMathMap.S;
    expect(rig.pointMathMap.M).toEqual([(ax + sx) / 2, (ay + sy) / 2, (az + sz) / 2]);
    expect(rig.pointMathMap.N).toEqual([(bx + cx) / 2, (by + cy) / 2, (bz + cz) / 2]);
    expect(rig.pointMathMap.P).toEqual([(cx + dx) / 2, (cy + dy) / 2, (cz + dz) / 2]);

    // Clipped frustum + upper cap both exist cleanly without degenerate polygon splits
    expect(rig.lowerFrustumFaces.length).toBeGreaterThanOrEqual(4);
    expect(rig.upperCapFaces.length).toBeGreaterThanOrEqual(3);
  });

  it("produces non-degenerate projected 2D MENPF pentagon and valid SVG fallback without fake badges", () => {
    const state = evaluateClosingMotionState(0, true);
    const proj = projectClosingFallbackSvg(480, 380, state);

    const coords = ["M", "E", "N", "P", "F"].map((id) => proj.points[id]);
    expect(coords.every((c) => Number.isFinite(c.x) && Number.isFinite(c.y))).toBe(true);

    // Shoelace polygon area in 2D must be clearly non-zero (no collapsed projection)
    let area2 = 0;
    for (let i = 0; i < coords.length; i++) {
      const a = coords[i];
      const b = coords[(i + 1) % coords.length];
      area2 += a.x * b.y - b.x * a.y;
    }
    expect(Math.abs(area2) * 0.5).toBeGreaterThan(800);

    // All projected vertices stay strictly inside fallback viewBox margins
    for (const p of Object.values(proj.points)) {
      expect(p.x).toBeGreaterThan(20);
      expect(p.x).toBeLessThan(proj.width - 20);
      expect(p.y).toBeGreaterThan(20);
      expect(p.y).toBeLessThan(proj.height - 20);
    }

    const html = renderToString(<LandingClosingScene3D />);
    expect(html).toContain('id="landing-closing-scene3d"');
    expect(html).toContain('role="img"');
    // No duplicate camera controls, no playback buttons, no fake metric tables inside CTA 3D stage
    expect(html).not.toContain("<button");
    expect(html).not.toContain("<table");

    const src = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingClosingScene3D.tsx"),
      "utf8",
    );
    expect(src).toContain("MeshStandardMaterial");
    expect(src).toContain("AmbientLight");
    expect(src).toContain("DirectionalLight");
    expect(src).toContain("clipPolygonHalfSpace");
    expect(src).toContain("LANDING_PYRAMID_SAMPLE");
  });
});
