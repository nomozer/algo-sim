import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import type { SceneObject } from "./scene3d-model";
import { classifySolidEdgeVisibility } from "./scene3d-edge-visibility";
import {
  buildObject3D,
  canonicalEdgeMaterial,
  updateCanonicalEdgeVisibility,
} from "./scene3d-view";

const PARTIAL: SceneObject = {
  id: "partial", label: "Partial", type: "solid", render: "mesh",
  origin: "derived", producer: "construct_solid", depends: [],
  vertices: [
    ["-2", "0", "0"], ["2", "0", "0"], ["0", "-2", "0"],
    ["0", "-1", "1"], ["1/20", "-1", "1"], ["1/40", "1", "1"],
  ],
  vertex_ids: ["A", "B", "C", "P", "Q", "R"],
  faces: [[0, 1, 2], [3, 4, 5]],
};

describe("Scene3D occlusion fault gates", () => {
  it("count-preserving ID swap is rejected by exact set comparison", () => {
    const expected = ["solid::edge:A-B", "solid::edge:B-C"];
    const swapped = ["solid::edge:A-B", "solid::edge:A-C"];
    expect(swapped).toHaveLength(expected.length);
    expect(swapped.sort()).not.toEqual(expected.sort());
  });

  it("small occluder is not missed by the coarse grid", () => {
    const result = classifySolidEdgeVisibility(PARTIAL, new THREE.Vector3(0, 0, 5), {
      projected_edge_pixels: 1200,
    });
    expect(result.mixed_edge_ids).toContain("partial::edge:A-B");
    const spans = result.edge_spans.filter((span) => span.edge_id === "partial::edge:A-B");
    expect(new Set(spans.map((span) => span.visibility))).toEqual(new Set(["VISIBLE", "HIDDEN"]));
    expect(Math.max(...spans.map((span) => span.t1 - span.t0)) * 1200).toBeGreaterThan(0);
    const edgeCount = new Set(result.edge_spans.map((span) => span.edge_id)).size;
    expect(1200 / (result.sample_count / edgeCount), "UNREFINED_TRANSITION").toBeLessThan(0.5);
  });

  it("mixed hidden spans render dashed under one logical owner", () => {
    const root = buildObject3D(PARTIAL, false)!;
    const owners: THREE.Object3D[] = [];
    root.traverse((node) => {
      if (node.userData.visualOwnerId === "partial::edge:A-B") owners.push(node);
    });
    expect(owners).toHaveLength(1);
    const materials = owners[0].children.map((child) => (child as THREE.Line).material);
    expect(materials.some((material) => material instanceof THREE.LineDashedMaterial)).toBe(true);
    expect(materials.some((material) => material instanceof THREE.LineBasicMaterial
      && !(material instanceof THREE.LineDashedMaterial))).toBe(true);
  });

  it("highlight cannot overwrite hidden dash policy", () => {
    expect(canonicalEdgeMaterial(true, true)).toBeInstanceOf(THREE.LineDashedMaterial);
    expect(canonicalEdgeMaterial(false, true)).toBeInstanceOf(THREE.LineBasicMaterial);
  });

  it("surface policy prevents base/section/auxiliary occlusion", () => {
    const scene: SceneObject = {
      ...PARTIAL,
      surfaces: [
        { surface_id: "partial::face:0", vertex_indices: [0, 1, 2],
          boundary_edge_ids: [], surface_role: "SOLID_FACE", occludes_edges: true },
        { surface_id: "partial::face:1", vertex_indices: [3, 4, 5],
          boundary_edge_ids: [], surface_role: "BASE_REGION", occludes_edges: false },
      ],
    };
    const result = classifySolidEdgeVisibility(scene, new THREE.Vector3(0, 0, 5));
    expect(result.visible_edge_ids).toContain("partial::edge:A-B");
    expect(result.mixed_edge_ids).not.toContain("partial::edge:A-B");
  });

  it("camera signature invalidates once, then 120 immutable frames recompute zero", () => {
    const root = new THREE.Group();
    root.add(buildObject3D(PARTIAL, false)!);
    const camera = new THREE.PerspectiveCamera(45, 4 / 3, 0.1, 100);
    camera.position.set(0, 0, 5);
    camera.lookAt(0, 0, 0);
    camera.updateMatrixWorld(true);
    camera.updateProjectionMatrix();
    expect(updateCanonicalEdgeVisibility(root, camera, "800x600@1").recomputed_solid_count).toBe(1);
    for (let frame = 0; frame < 120; frame += 1) {
      expect(updateCanonicalEdgeVisibility(root, camera, "800x600@1").recomputed_solid_count).toBe(0);
    }
    camera.position.x = 1;
    camera.lookAt(0, 0, 0);
    camera.updateMatrixWorld(true);
    expect(updateCanonicalEdgeVisibility(root, camera, "800x600@1").recomputed_solid_count).toBe(1);
  });

  it("OrbitControls damping float drift does not recompute; a real pose change still does", () => {
    // Mobile evidence 2026-09-28: `dieuKhien.update()` round-trips the camera
    // through spherical coordinates every frame and the position walks in the
    // last ULPs forever, so an exact-float signature recomputed 841/841 frames.
    const root = new THREE.Group();
    root.add(buildObject3D(PARTIAL, false)!);
    const camera = new THREE.PerspectiveCamera(50, 340 / 418, 0.1, 1000);
    camera.up.set(0, 0, 1);
    camera.position.set(13.219735978431286, 6.394900991911706, 11.289801983823384);
    // Node test env has no DOM; OrbitControls only needs listeners + style here.
    const element = Object.assign(new EventTarget(), {
      style: {}, ownerDocument: new EventTarget(), getRootNode() { return element; },
    }) as unknown as HTMLElement;
    const controls = new OrbitControls(camera, element);
    controls.enableDamping = true;
    controls.target.set(0.5, 0.25, 0.5);
    controls.update();
    camera.updateMatrixWorld(true);
    camera.updateProjectionMatrix();
    updateCanonicalEdgeVisibility(root, camera, "340x418@1");
    const start = camera.position.clone();
    let recomputed = 0;
    for (let frame = 0; frame < 240; frame += 1) {
      controls.update();
      camera.updateMatrixWorld(true);
      recomputed += updateCanonicalEdgeVisibility(root, camera, "340x418@1").recomputed_solid_count;
    }
    expect(camera.position.distanceTo(start), "damping must keep drifting (product behavior)")
      .toBeLessThan(1e-9);
    expect(recomputed).toBe(0);
    // Every pose change that moves a projected vertex by more than the 0.5 px
    // product↔oracle tolerance must invalidate, whichever axis it moves on.
    const px = (p: THREE.Vector3) => {
      const n = p.clone().project(camera);
      return new THREE.Vector2(n.x * 340 / 2, n.y * 418 / 2);
    };
    const vertex = new THREE.Vector3(2, 0, 0);
    for (const axis of [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, -1, 0], [0, 1, -1]]) {
      const before = px(vertex);
      const step = new THREE.Vector3(...axis).normalize().multiplyScalar(1e-4);
      let moved = 0;
      while (moved < 0.6) {
        camera.position.add(step);
        camera.updateMatrixWorld(true);
        moved = px(vertex).distanceTo(before);
      }
      expect(moved).toBeLessThan(1);
      expect(updateCanonicalEdgeVisibility(root, camera, "340x418@1").recomputed_solid_count,
        `axis ${axis}`).toBe(1);
    }
  });

  it("duplicate logical owner is named by the renderer audit", () => {
    const root = new THREE.Group();
    root.add(buildObject3D(PARTIAL, false)!, buildObject3D(PARTIAL, false)!);
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    camera.position.set(0, 0, 5);
    camera.lookAt(0, 0, 0);
    camera.updateMatrixWorld(true);
    const audit = updateCanonicalEdgeVisibility(root, camera, "800x800@1");
    expect(audit.duplicate_visual_owner_ids).toContain("partial::edge:A-B");
  });
});
