import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import {
  buildClosingCompositionData,
  LandingClosingScene3D,
} from "../landing/LandingClosingScene3D";
import { separateLabelPositions, type LabelCandidate } from "../landing/LandingHeroScene3D";
import { LandingHeroSculpture3D } from "../landing/LandingHeroSculpture3D";
import { LANDING_CUBE_SAMPLE, extractPointsFromSample } from "../landing/landing-geometry-data";

describe("AXO Landing — WebGL Budget, Persistent Lifecycle, Deduplication & Label Collision", () => {
  it("deduplicates repeated point IDs in extractPointsFromSample", () => {
    const fakeSample = {
      envelope: {
        scene3d: {
          objects: [
            { id: "A", notation: "A", type: "point3", xyz: [0, 0, 0] },
            { id: " A ", notation: "A_dup", type: "point3", xyz: [9, 9, 9] },
            { id: "B", notation: "B", type: "point3", xyz: [4, 0, 0] },
            { id: "M", notation: "M", type: "point3", xyz: [2, 0, 0] },
          ],
        },
      },
    } as unknown as Parameters<typeof extractPointsFromSample>[0];
    const deduped = extractPointsFromSample(fakeSample, [
      { id: "A", label: "A", xyz: [0, 0, 0] },
    ]);
    const ids = deduped.map((pt) => pt.id);
    expect(ids).toEqual(["A", "B", "M"]);
    expect(new Set(ids).size).toBe(ids.length);
    expect(LANDING_CUBE_SAMPLE.points).toHaveLength(new Set(LANDING_CUBE_SAMPLE.points.map((p) => p.id)).size);
  });

  it("separates clustered 2D vertex labels via 2-pass repulsion and clamps inside safe viewport bounds", () => {
    const items: LabelCandidate[] = [
      { id: "M", x: 140, y: 120 },
      { id: "N", x: 142, y: 121 },
      { id: "E", x: 139, y: 123 },
      { id: "OOB_TL", x: -10, y: -15 },
      { id: "OOB_BR", x: 700, y: 500 },
    ];
    separateLabelPositions(items, 560, 420, 26, 24, 26, 46);

    for (const item of items) {
      expect(item.x).toBeGreaterThanOrEqual(24);
      expect(item.x).toBeLessThanOrEqual(536);
      expect(item.y).toBeGreaterThanOrEqual(26);
      expect(item.y).toBeLessThanOrEqual(374);
    }

    for (let i = 0; i < 3; i++) {
      for (let j = i + 1; j < 3; j++) {
        const dist = Math.hypot(items[i].x - items[j].x, items[i].y - items[j].y);
        expect(dist).toBeGreaterThanOrEqual(25);
      }
    }
  });

  it("keeps a single persistent WebGLRenderer across sample swaps, avoids MeshPhysicalMaterial, and isolates hero sculpture", () => {
    const sceneSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingHeroScene3D.tsx"),
      "utf8",
    );
    const sculptureSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingHeroSculpture3D.tsx"),
      "utf8",
    );

    expect(sceneSrc).not.toContain("MeshPhysicalMaterial");
    expect(sculptureSrc).not.toContain("MeshPhysicalMaterial");
    expect(sceneSrc).toContain("swapSample");
    expect(sceneSrc).toContain("syncSampleRigRef");
    expect(sceneSrc).toContain("${sample.id}:${pt.id}");
    expect(sculptureSrc).not.toContain("sphereCompanionGroup");
    expect(sculptureSrc).not.toContain("octMesh");
  });

  it("verifies §15 Workspace Renderer Error keeps SimulationWorkspace stage-scoped via AxoViewerRecoverySurface", () => {
    const workspaceSrc = fs.readFileSync(
      path.resolve(__dirname, "../SimulationWorkspace.tsx"),
      "utf8",
    );
    const errExpSrc = fs.readFileSync(
      path.resolve(__dirname, "../AxoErrorExperience.tsx"),
      "utf8",
    );

    expect(workspaceSrc).toContain('mien="scene3d-viewer"');
    expect(workspaceSrc).toContain("export function AxoViewerRecoverySurface");
    expect(workspaceSrc).toContain("webglRecoveringNode={");
    expect(workspaceSrc).toContain("webglFallbackNode={");
    expect(workspaceSrc).toContain("<AxoErrorExperience");
    expect(workspaceSrc).toContain('variant="stage"');
    expect(errExpSrc).toContain('readonly variant?: "page" | "stage" | "refusal"');
    expect(errExpSrc).toContain('variant === "page"');
  });

  it("keeps Hero production Concept A illustration intact without vertex tags", () => {
    const html = renderToString(<LandingHeroSculpture3D />);
    expect(html).toContain('id="landing-hero-sculpture"');
    expect(html).toContain('data-hero-variant="transformation"');
    expect(html).toContain("<svg");
    expect(html).not.toContain("axo-sp-point-tag");

    const altHtml = renderToString(<LandingHeroSculpture3D variant="sculpture" />);
    expect(altHtml).toContain('data-hero-variant="sculpture"');
  });

  it("keeps LandingClosingScene3D reusing shared SpatialSceneCanvas (0 duplicate renderer) with offscreen pause and full GPU cleanup", () => {
    const closingSceneSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingClosingScene3D.tsx"),
      "utf8",
    );

    expect(closingSceneSrc).toContain('from "./LandingHeroScene3D"');
    expect(closingSceneSrc).not.toContain("new THREE.WebGLRenderer(");
    expect(closingSceneSrc).toContain("IntersectionObserver");
    expect(closingSceneSrc).toContain('document.addEventListener("visibilitychange"');
    expect(closingSceneSrc).toContain("cancelAnimationFrame");

    const ssrHtml = renderToString(<LandingClosingScene3D />);
    expect(ssrHtml).toContain('id="landing-closing-scene3d"');
    const comp = buildClosingCompositionData();
    expect(comp.sectionVertices).toHaveLength(6);
  });
});
