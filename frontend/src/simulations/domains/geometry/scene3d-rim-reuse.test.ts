import { describe, expect, it, vi } from "vitest";
import * as THREE from "three";
import { dongBoNetDayManHinh } from "./scene3d-edge-visibility";
import { buildObject3D, disposeScene3DObject, updateCanonicalEdgeVisibility } from "./scene3d-view";
import type { SceneObject } from "./scene3d-model";

const circle: SceneObject = {
  id: "test-section", type: "circle3", render: "circle", label: "Section",
  origin: "derived", producer: null, depends: [], center: ["0", "0", "0"], normal: ["0", "0", "1"],
  radius_sq: "4", surface_role: "SECTION_REGION", fill_visible: false,
};

describe("semantic rim buffer reuse", () => {
  it("reuses thick-line nodes and buffers across 30 rebuilt step owners and releases them once", () => {
    const fat = new THREE.Group();
    const camera = new THREE.PerspectiveCamera(40, 1.6, .1, 100);
    camera.position.set(8, 3, 6); camera.lookAt(0, 0, 0); camera.updateMatrixWorld();
    let first: THREE.Object3D[] = [];
    let buffers: unknown[] = [];
    for (let i = 0; i < 30; i++) {
      const root = buildObject3D({ ...circle, radius_sq: i % 2 ? "9" : "4" }, false)!;
      updateCanonicalEdgeVisibility(root, camera, "1440x900@1");
      dongBoNetDayManHinh([root], fat, 1440, 900);
      const nodes = fat.children.filter(n => n.userData.fatRimCompanion);
      if (!i) { first = [...nodes]; buffers = nodes.map(n => (n as THREE.Mesh).geometry); }
      expect(nodes.length).toBe(first.length);
      expect(nodes.every((n, j) => n === first[j] && (n as THREE.Mesh).geometry === buffers[j])).toBe(true);
      disposeScene3DObject(root);
    }
    const disposals = buffers.map(g => vi.spyOn(g as THREE.BufferGeometry, "dispose"));
    disposeScene3DObject(fat);
    expect(disposals.every(spy => spy.mock.calls.length === 1)).toBe(true);
  });
});
