import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it } from "vitest";
import { useAuthStore, type AuthUser } from "../../state/auth";
import {
  buildHeroSpatialGallerySpecs,
  computeTrueShapeSection2D,
  evaluateHeroStoryboard,
  HERO_SATELLITE_COUNT,
  HERO_SECTION_FILL_OPACITY,
  HERO_STORYBOARD_MS,
  LandingHeroV14,
} from "../landing/LandingHeroV14";

function syncAuthStoreForSSR() {
  Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());
}

const TEST_STUDENT_USER: AuthUser = {
  id: 101,
  email: "student@axo.edu.vn",
  displayName: "Nguyễn Minh Anh",
  role: "student",
  mustChangePassword: false,
  status: "active",
};

describe("AXO Landing V1.4 — Hero Visual System & Lifecycle", () => {
  afterEach(() => {
    useAuthStore.setState({ user: null });
    syncAuthStoreForSSR();
  });

  it("computes an exact isometric 2D true-shape projection and 4-beat finite storyboard", () => {
    const result = computeTrueShapeSection2D();
    expect(result.vertices.map((v) => v.label)).toEqual(["M", "E", "N", "P", "F"]);
    expect(result.edgeLengths3D.length).toBe(5);
    expect(result.edgeLengths2D.length).toBe(5);
    expect(result.maxDeviation).toBeLessThan(1e-4);
    for (const v of result.vertices) {
      expect(v.nx).toBeGreaterThanOrEqual(0);
      expect(v.nx).toBeLessThanOrEqual(1);
      expect(v.ny).toBeGreaterThanOrEqual(0);
      expect(v.ny).toBeLessThanOrEqual(1);
    }

    const b1 = evaluateHeroStoryboard(HERO_STORYBOARD_MS * 0.12, false);
    const b2 = evaluateHeroStoryboard(HERO_STORYBOARD_MS * 0.34, false);
    const b3 = evaluateHeroStoryboard(HERO_STORYBOARD_MS * 0.62, false);
    const b4 = evaluateHeroStoryboard(HERO_STORYBOARD_MS + 10, false);

    expect(b1.beat).toBe("solid-emergence");
    expect(b1.settled).toBe(false);
    expect(b1.capLift).toBe(0);
    expect(b2.beat).toBe("seed-anchors");
    expect(b2.seedReveal).toBeGreaterThan(0.4);
    expect(b3.beat).toBe("plane-intersection");
    expect(b3.planeSweep).toBeGreaterThan(0.5);
    expect(b4.beat).toBe("section-settled");
    expect(b4.settled).toBe(true);
    expect(b4.capLift).toBe(0);
    expect(HERO_SECTION_FILL_OPACITY).toBe(0.5);
    expect(b1.satelliteReveal).toBe(0);
    expect(b3.satelliteReveal).toBeGreaterThan(0.5);
    expect(b4.satelliteReveal).toBe(1);

    const reduced = evaluateHeroStoryboard(100, true);
    expect(reduced.settled).toBe(true);
    expect(reduced.capLift).toBe(0);
    expect(reduced.satelliteReveal).toBe(1);
    expect(reduced.beat).toBe("section-settled");
  });

  it("constructs a mathematically grounded 3-satellite Spatial Geometry Gallery in distinct depth planes", () => {
    const gallery = buildHeroSpatialGallerySpecs();
    expect(gallery.satellites).toHaveLength(HERO_SATELLITE_COUNT);
    expect(HERO_SATELLITE_COUNT).toBe(3);

    // Non-collinear screen triangle (shoelace area > 1.5) and 3 distinct camera-depth planes
    const [s0, s1, s2] = gallery.satellites;
    const triArea =
      0.5 *
      Math.abs(
        (s1.screenDx - s0.screenDx) * (s2.screenDy - s0.screenDy) -
          (s2.screenDx - s0.screenDx) * (s1.screenDy - s0.screenDy),
      );
    expect(triArea).toBeGreaterThan(1.5);
    expect(new Set([s0.screenDz, s1.screenDz, s2.screenDz]).size).toBe(3);

    // Satellite 0: exact regular octahedron edges (all 12 edges = r * sqrt(2))
    const expectedOctEdge = gallery.octahedronRadius * Math.SQRT2;
    for (const [i, j] of gallery.octahedronEdges) {
      const a = gallery.octahedronVertices[i];
      const b = gallery.octahedronVertices[j];
      const d = Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
      expect(Math.abs(d - expectedOctEdge)).toBeLessThan(1e-6);
    }

    // Satellite 1: extracted isometric pentagon matches computeTrueShapeSection2D() edge ratios
    const trueShape = computeTrueShapeSection2D();
    expect(gallery.extractedPentagonPts).toHaveLength(5);
    const scaleRatio =
      Math.hypot(
        gallery.extractedPentagonPts[1][0] - gallery.extractedPentagonPts[0][0],
        gallery.extractedPentagonPts[1][1] - gallery.extractedPentagonPts[0][1],
      ) / trueShape.edgeLengths2D[0];
    for (let i = 0; i < 5; i++) {
      const j = (i + 1) % 5;
      const d = Math.hypot(
        gallery.extractedPentagonPts[j][0] - gallery.extractedPentagonPts[i][0],
        gallery.extractedPentagonPts[j][1] - gallery.extractedPentagonPts[i][1],
      );
      expect(Math.abs(d / trueShape.edgeLengths2D[i] - scaleRatio)).toBeLessThan(1e-6);
    }

    // Satellite 2: unit cube sliced by x + y + z = 0 regular hexagon (planar + equal edges)
    expect(gallery.cubeHexSection).toHaveLength(6);
    const expectedHexEdge = gallery.cubeHalfSize * Math.SQRT2;
    for (let i = 0; i < 6; i++) {
      const pt = gallery.cubeHexSection[i];
      expect(Math.abs(pt[0] + pt[1] + pt[2])).toBeLessThan(1e-6);
      const next = gallery.cubeHexSection[(i + 1) % 6];
      const d = Math.hypot(next[0] - pt[0], next[1] - pt[1], next[2] - pt[2]);
      expect(Math.abs(d - expectedHexEdge)).toBeLessThan(1e-6);
    }
  });

  it("renders guest and authenticated Hero CTAs cleanly without floating math result cards", () => {
    useAuthStore.setState({ user: null });
    syncAuthStoreForSSR();
    const guestHtml = renderToStaticMarkup(<LandingHeroV14 />);
    expect(guestHtml).toContain("axo-v14-anno-circle");
    expect(guestHtml).toContain('id="btn-landing-hero-start"');
    expect(guestHtml).toContain("Bắt đầu dựng hình");
    expect(guestHtml).toContain('id="btn-landing-hero-story"');
    expect(guestHtml).toContain("Xem cách hoạt động");
    expect(guestHtml).toContain('id="landing-hero-sculpture"');
    expect(guestHtml).not.toContain("axo-v14-hero-trueshape");
    expect(guestHtml).not.toContain("S(MENPF) = 6√6");
    expect(guestHtml).not.toContain("Pending Owner Review");

    useAuthStore.setState({ user: TEST_STUDENT_USER });
    syncAuthStoreForSSR();
    const authHtml = renderToStaticMarkup(<LandingHeroV14 />);
    expect(authHtml).toContain("Vào ứng dụng");
    expect(authHtml).not.toContain("Đăng nhập ngay");
  });

  it("enforces GPU cleanup, single renderer context, finite choreography, and token hygiene", () => {
    const source = readFileSync(
      resolve(__dirname, "../landing/LandingHeroV14.tsx"),
      "utf8",
    );
    expect(source).not.toContain("var(--");
    expect(source).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect((source.match(/new THREE\.WebGLRenderer\(/g) ?? [])).toHaveLength(1);
    expect(source).not.toContain('canvas.getContext("webgl2"');
    expect(source).toContain("webglcontextlost");
    expect(source).toContain("webglcontextrestored");
    expect(source).toContain("renderer.dispose()");
    expect(source).toContain("cancelAnimationFrame");
    expect(source).toContain("prefers-reduced-motion: reduce");
    expect(source).toContain("HERO_STORYBOARD_MS = 3800");
  });
});
