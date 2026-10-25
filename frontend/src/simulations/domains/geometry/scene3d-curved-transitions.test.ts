import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { buildObject3D, updateCanonicalEdgeVisibility } from "./scene3d-view";
import type { SceneObject } from "./scene3d-model";

const cylinder: SceneObject = {
  id: "body", label: "Cylinder", type: "curved_solid", render: "curved_solid",
  origin: "derived", producer: "construct_curved_solid", depends: [],
  curved_kind: "cylinder", anchor: ["0", "0", "0"], apex_or_top: ["0", "0", "8"],
  radius_sq: "4", height_sq: "64",
};
const ellipse: SceneObject = {
  id: "cut", label: "Cut", type: "ellipse3", render: "ellipse", origin: "derived",
  producer: "intersect_plane_curved_ellipse", depends: ["body", "plane"], surface_role: "SECTION_REGION",
  center: ["0", "0", "4"], normal: ["-1", "0", "1"],
  major_dir: ["1", "0", "1"], minor_dir: ["0", "1", "0"], semi_major_sq: "8", semi_minor_sq: "4",
};
const cameraAt = (p: THREE.Vector3) => {
  const camera = new THREE.PerspectiveCamera(45, 1.6, 0.1, 100);
  camera.position.copy(p); camera.lookAt(0, 0, 4); camera.updateMatrixWorld(true);
  return camera;
};

describe("curved-rim visibility at the true curve transition", () => {
  it("splits an ellipse at cylinder tangency instead of colouring the entire midpoint chord", () => {
    const root = new THREE.Group();
    root.add(buildObject3D(cylinder, false)!, buildObject3D(ellipse, false)!);
    const camera = cameraAt(new THREE.Vector3(10, 3, 9));
    updateCanonicalEdgeVisibility(root, camera, "1440x900@1");
    const rimNode = root.getObjectByName("ellipse:cut")!;
    const rim = rimNode.userData.curvedRimLoop;
    const positions = rim.thayNet.geometry.getAttribute("position") as THREE.BufferAttribute;
    // Independent cylinder surface-normal oracle: n(theta)·(eye - p(theta)) = 0.
    const phi = Math.atan2(3, 10), alpha = Math.acos(2 / Math.hypot(10, 3));
    for (const theta of [phi - alpha, phi + alpha]) {
      const tangent = new THREE.Vector3(2 * Math.cos(theta), 2 * Math.sin(theta), 2 * Math.cos(theta));
      let distance = Infinity;
      for (let i = 0; i < rim.thayNet.geometry.drawRange.count; i++) {
        distance = Math.min(distance, tangent.distanceTo(new THREE.Vector3().fromBufferAttribute(positions, i)));
      }
      expect(distance).toBeLessThan(2e-4);
    }
  });

  it("keeps geometry and GPU buffers stable across opposite, axial and grazing cameras", () => {
    const root = new THREE.Group();
    root.rotation.set(0.3, -0.2, 0.1);
    root.position.set(2, -1, 3);
    root.add(buildObject3D(cylinder, false)!, buildObject3D(ellipse, "dich")!);
    root.updateMatrixWorld(true);
    const original = JSON.stringify([cylinder, ellipse]);
    const rim = root.getObjectByName("ellipse:cut")!.userData.curvedRimLoop;
    let geometry: THREE.BufferGeometry | undefined;
    let buffer: ArrayLike<number> | undefined;
    for (const position of [[10, 3, 9], [-10, -3, 9], [0, 0, 20], [10, 0.0001, 4], [10, 3, -5]]) {
      const eye = new THREE.Vector3(...position).applyMatrix4(root.matrixWorld);
      updateCanonicalEdgeVisibility(root, cameraAt(eye), "390x844@2");
      const g = rim.thayNet.geometry as THREE.BufferGeometry;
      geometry ??= g; buffer ??= g.getAttribute("position").array;
      expect(g).toBe(geometry);
      expect(g.getAttribute("position").array).toBe(buffer);
      expect(g.drawRange.count).toBeLessThanOrEqual(g.getAttribute("position").count);
    }
    expect(JSON.stringify([cylinder, ellipse])).toBe(original);
  });
});

describe("standalone sphere presentation reference", () => {
  it("shows one 3D reference circle without changing scene data and updates front/back under orbit", () => {
    const sphere: SceneObject = { ...cylinder, id: "sphere", curved_kind: "ball", height_sq: "0", apex_or_top: undefined };
    const source = JSON.stringify(sphere);
    const root = buildObject3D(sphere, false)!;
    const reference = root.getObjectByName("sphere_reference:sphere");
    expect(reference).toBeDefined();
    expect(reference!.userData.presentationReference).toEqual({ role: "REFERENCE_CURVE", source_object_id: "sphere", authoritative: false });
    const signatures: string[] = [];
    for (const eye of [new THREE.Vector3(8, 3, 6), new THREE.Vector3(-8, -3, 6)]) {
      updateCanonicalEdgeVisibility(root, cameraAt(eye), "1440x900@1");
      const rim = reference!.userData.curvedRimLoop;
      expect(rim.thayNet.geometry.drawRange.count).toBeGreaterThan(0);
      expect(rim.khuatNet.geometry.drawRange.count).toBeGreaterThan(0);
      signatures.push(reference!.userData.curvedRimFlagSig);
    }
    expect(signatures[0]).not.toBe(signatures[1]);
    expect(JSON.stringify(sphere)).toBe(source);
    expect(reference!.getObjectByName("section_fill:sphere")).toBeUndefined();
  });

  it("can suppress the reference for a real sphere-plane scene without suppressing its silhouette", () => {
    const sphere: SceneObject = { ...cylinder, id: "sphere", curved_kind: "ball", height_sq: "0", apex_or_top: undefined };
    const root = buildObject3D(sphere, false, undefined, [], undefined, undefined, undefined, false, "primary", true, false)!;
    expect(root.getObjectByName("sphere_reference:sphere")).toBeUndefined();
    updateCanonicalEdgeVisibility(root, cameraAt(new THREE.Vector3(8, 3, 6)));
    expect(root.getObjectByName("sphere_silhouette:sphere")!.visible).toBe(true);
  });
});
