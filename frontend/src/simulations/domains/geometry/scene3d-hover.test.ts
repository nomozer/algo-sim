import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { applyHoverFeedback } from "./scene3d-view";
import { modulateSemanticColor } from "./scene3d-semantic-policy";

describe("transient hover on existing render objects", () => {
  it("restores colors/state without replacing geometry, materials, children or semantic colors", () => {
    const root = new THREE.Group();
    const owner = new THREE.Group(); owner.name = "solid:renamed-solid";
    const line = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0xad4236 }));
    line.name = "edge:renamed-edge"; line.userData.interactionState = "neutral";
    const proxy = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({ colorWrite: false, opacity: 0 }));
    owner.add(line, proxy); root.add(owner);
    const ids = [line.uuid, line.geometry.uuid, line.material.uuid, proxy.material.uuid];
    const original = line.material.color.getHex();
    const undo = applyHoverFeedback(root, "renamed-solid", new Set());
    expect(line.material.color.getHex()).toBe(modulateSemanticColor(original, "hover"));
    expect(line.userData.interactionState).toBe("hover");
    expect(proxy.material.opacity).toBe(0);
    expect([line.uuid, line.geometry.uuid, line.material.uuid, proxy.material.uuid]).toEqual(ids);
    undo();
    expect(line.material.color.getHex()).toBe(original);
    expect(line.userData.interactionState).toBe("neutral");
    expect(owner.children).toEqual([line, proxy]);
  });

  it("addresses a canonical edge owned by another object and preserves selected emphasis", () => {
    const root = new THREE.Group();
    const owner = new THREE.Group(); owner.name = "solid:outer";
    const edge = new THREE.Group(); edge.name = "edge:outer::edge:2";
    edge.userData.interactionState = "neutral";
    const material = new THREE.LineBasicMaterial({ color: 0x567891 });
    const line = new THREE.Line(new THREE.BufferGeometry(), material);
    edge.add(line); owner.add(edge); root.add(owner);
    const base = material.color.getHex();
    const undo = applyHoverFeedback(root, "auxiliary", new Set(["outer::edge:2"]));
    expect(material.color.getHex()).toBe(modulateSemanticColor(base, "hover")); undo();
    edge.userData.interactionState = "selected";
    const undoSelected = applyHoverFeedback(root, "outer", new Set());
    expect(material.color.getHex()).toBe(base); undoSelected();
    expect(edge.userData.interactionState).toBe("selected");
  });
});
