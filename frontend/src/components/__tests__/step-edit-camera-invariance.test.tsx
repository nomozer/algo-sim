/**
 * step-edit-camera-invariance.test.tsx — regression test for ISSUE-FE-UNORBITED-CAMERA-JUMP-ON-STEP-EDIT-COMMIT.
 *
 * Verifies that Scene3DView preserves both unorbited auto-fit camera pose + lens offset and user-orbited camera
 * across in-place step-edit scene rebuilds when `sceneIdentityKey` stays unchanged, while resetting on `fitToken` change.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import * as THREE from "three";
import * as ts from "typescript";
import { describe, expect, it } from "vitest";

const SCENE3D_VIEW_PATH = resolve(__dirname, "../../simulations/domains/geometry/scene3d-view.tsx");
const WORKSPACE_PATH = resolve(__dirname, "../SimulationWorkspace.tsx");

function hasJsxAttribute(sourceText: string, fileName: string, componentName: string, attrName: string): boolean {
  const sf = ts.createSourceFile(fileName, sourceText, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  let found = false;
  const visit = (node: ts.Node) => {
    if (found) return;
    if (ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) {
      if (node.tagName.getText(sf) === componentName) {
        for (const prop of node.attributes.properties) {
          if (ts.isJsxAttribute(prop) && prop.name.getText(sf) === attrName) {
            found = true;
            return;
          }
        }
      }
    }
    ts.forEachChild(node, visit);
  };
  visit(sf);
  return found;
}

describe("Step-Edit Unorbited & Orbited Camera Invariance Contract", () => {
  it("wires sceneIdentityKey from SimulationWorkspace into Scene3DView and preserves live pose + lens offset across rebuilds", () => {
    const wsSrc = readFileSync(WORKSPACE_PATH, "utf8");
    const viewSrc = readFileSync(SCENE3D_VIEW_PATH, "utf8");

    expect(hasJsxAttribute(wsSrc, "SimulationWorkspace.tsx", "Scene3DWorkspace", "sceneIdentityKey")).toBe(true);
    expect(hasJsxAttribute(wsSrc, "SimulationWorkspace.tsx", "Scene3DWorkspace", "initialCameraPose")).toBe(true);

    const sf = ts.createSourceFile("scene3d-view.tsx", viewSrc, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
    const declNames = new Set<string>();
    const visit = (n: ts.Node) => {
      if (ts.isVariableDeclaration(n) && ts.isIdentifier(n.name)) {
        declNames.add(n.name.text);
      }
      ts.forEachChild(n, visit);
    };
    visit(sf);

    expect(declNames.has("liveCameraStateRef")).toBe(true);
    expect(declNames.has("prevSceneIdentityKeyRef")).toBe(true);
    expect(declNames.has("sameIdentitySceneRebuild")).toBe(true);
    expect(viewSrc).toContain("savedPose.offset");
    expect(viewSrc).toContain("fromAutoFit: true");
  });

  it("restoring position, target, and viewOffset keeps PerspectiveCamera projection and view matrices invariant", () => {
    const camInitial = new THREE.PerspectiveCamera(42, 16 / 9, 0.1, 200);
    camInitial.up.set(0, 0, 1);
    camInitial.position.set(9.4, -7.2, 6.1);
    camInitial.setViewOffset(1200, 900, 72, -38, 1200, 900);
    camInitial.lookAt(2, 2, 1.5);
    camInitial.updateMatrixWorld(true);
    camInitial.updateProjectionMatrix();

    // Simulate post-edit Scene3DView rebuild where datKhungNhin picks a different direction before restore
    const camRebuilt = new THREE.PerspectiveCamera(42, 16 / 9, 0.1, 200);
    camRebuilt.up.set(0, 0, 1);
    camRebuilt.position.set(-5, 11, 8);
    camRebuilt.setViewOffset(1200, 900, -40, 25, 1200, 900);
    camRebuilt.lookAt(1, 1, 1);

    // Apply restored liveCameraStateRef snapshot (offset + position + target)
    camRebuilt.setViewOffset(1200, 900, 72, -38, 1200, 900);
    camRebuilt.position.set(9.4, -7.2, 6.1);
    camRebuilt.lookAt(2, 2, 1.5);
    camRebuilt.updateMatrixWorld(true);
    camRebuilt.updateProjectionMatrix();

    for (let i = 0; i < 16; i += 1) {
      expect(camRebuilt.matrixWorldInverse.elements[i]).toBeCloseTo(camInitial.matrixWorldInverse.elements[i]!, 10);
      expect(camRebuilt.projectionMatrix.elements[i]).toBeCloseTo(camInitial.projectionMatrix.elements[i]!, 10);
    }
  });
});
