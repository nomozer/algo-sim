import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { buildObject3D } from "./scene3d-view";
import { diemHuuHan, type Scene3D, type SceneObject } from "./scene3d-model";
import { TRANG_THAI_DAU, explode, semanticTree, visualTransformOf } from "./interaction-state";

function makeBaseScene(objects: SceneObject[]): Scene3D {
  return {
    version: "1.0",
    coordinate_frame: { origin: ["0", "0", "0"], axes: ["x", "y", "z"] },
    objects,
    dependencies: {},
    free_objects: [],
    events: [],
  };
}

describe("Session 1 P3 — Simulation Coverage & Visual Validation Fixes", () => {
  it("renders scalar-radius ball, cylinder, and cone (rim_point: null, radius_sq > 0)", () => {
    const ballObj: SceneObject = {
      id: "cau",
      label: "Mặt cầu tâm I",
      type: "curved_solid",
      render: "curved_solid",
      origin: "derived",
      depends: ["I", "R"],
      curved_kind: "ball",
      anchor: ["0", "0", "0"],
      apex_or_top: null,
      rim_point: null,
      radius_sq: "25",
      height_sq: "0",
      display_group: ["solid"],
    };
    const ballGroup = buildObject3D(ballObj, false, false);
    expect(ballGroup).not.toBeNull();
    const ballMesh = ballGroup!.children.find((c): c is THREE.Mesh => c instanceof THREE.Mesh);
    expect(ballMesh).toBeDefined();
    expect(ballMesh!.geometry).toBeInstanceOf(THREE.SphereGeometry);

    const cylObj: SceneObject = {
      id: "tru",
      label: "Hình trụ tròn xoay",
      type: "curved_solid",
      render: "curved_solid",
      origin: "derived",
      depends: ["O", "R", "h"],
      curved_kind: "cylinder",
      anchor: ["0", "0", "0"],
      apex_or_top: null,
      rim_point: null,
      radius_sq: "4",
      height_sq: "9",
      display_group: ["solid"],
    };
    const cylGroup = buildObject3D(cylObj, false, false);
    expect(cylGroup).not.toBeNull();
    const cylMesh = cylGroup!.children.find((c): c is THREE.Mesh => c instanceof THREE.Mesh);
    expect(cylMesh).toBeDefined();
    expect(cylMesh!.geometry).toBeInstanceOf(THREE.CylinderGeometry);
    // Midpoint along canonical axis (0, 0, 1) for anchor (0,0,0) and h=3 must be (0, 0, 1.5)
    expect(cylMesh!.position.x).toBeCloseTo(0, 5);
    expect(cylMesh!.position.y).toBeCloseTo(0, 5);
    expect(cylMesh!.position.z).toBeCloseTo(1.5, 5);
    // Local Y-axis (0, 1, 0) rotated by quaternion must align with canonical Z-axis (0, 0, 1)
    const rotatedAxis = new THREE.Vector3(0, 1, 0).applyQuaternion(cylMesh!.quaternion);
    expect(rotatedAxis.x).toBeCloseTo(0, 5);
    expect(rotatedAxis.y).toBeCloseTo(0, 5);
    expect(rotatedAxis.z).toBeCloseTo(1, 5);

    const coneObj: SceneObject = {
      id: "non",
      label: "Hình nón tròn xoay",
      type: "curved_solid",
      render: "curved_solid",
      origin: "derived",
      depends: ["O", "R", "h"],
      curved_kind: "cone",
      anchor: ["0", "0", "0"],
      apex_or_top: null,
      rim_point: null,
      radius_sq: "9",
      height_sq: "16",
      display_group: ["solid"],
    };
    const coneGroup = buildObject3D(coneObj, false, false);
    expect(coneGroup).not.toBeNull();
    const coneMesh = coneGroup!.children.find((c): c is THREE.Mesh => c instanceof THREE.Mesh);
    expect(coneMesh).toBeDefined();
    expect(coneMesh!.geometry).toBeInstanceOf(THREE.ConeGeometry);
    expect(coneMesh!.position.z).toBeCloseTo(2, 5);
  });

  it("includes canonical Z height extent in diemHuuHan for scalar-height cylinder and cone", () => {
    const coneObj: SceneObject = {
      id: "non",
      label: "Hình nón tròn xoay",
      type: "curved_solid",
      render: "curved_solid",
      origin: "derived",
      depends: ["O", "R", "h"],
      curved_kind: "cone",
      anchor: ["0", "0", "0"],
      apex_or_top: null,
      rim_point: null,
      radius_sq: "9",
      height_sq: "16",
      display_group: ["solid"],
    };
    const pts = diemHuuHan([coneObj]);
    const maxZ = Math.max(...pts.map((p) => p[2]));
    const minX = Math.min(...pts.map((p) => p[0]));
    const maxX = Math.max(...pts.map((p) => p[0]));
    expect(maxZ).toBeCloseTo(4, 5);
    expect(minX).toBeCloseTo(-3, 5);
    expect(maxX).toBeCloseTo(3, 5);
  });

  it("classifies curved_solid, circle3, and ellipse3 properly in semanticTree and visualTransformOf", () => {
    const scene = makeBaseScene([
      {
        id: "cau",
        label: "Mặt cầu tâm I",
        type: "curved_solid",
        render: "curved_solid",
        origin: "derived",
        depends: ["I", "R"],
        curved_kind: "ball",
        anchor: ["0", "0", "0"],
        apex_or_top: null,
        rim_point: null,
        radius_sq: "25",
        height_sq: "0",
        display_group: ["solid"],
      },
      {
        id: "vong_giao",
        label: "Đường tròn giao tuyến (C)",
        type: "circle3",
        render: "circle",
        origin: "derived",
        depends: ["mp", "cau"],
        center: ["0", "0", "3"],
        normal: ["0", "0", "1"],
        radius_sq: "16",
        display_group: ["section"],
      },
    ]);

    const tree = semanticTree(scene);
    // curved_solid is a root solid node, and circle3 is categorized under "Thiết diện" (not "Khác")
    expect(tree.some((n) => n.id === "cau")).toBe(true);
    const secCat = tree.find((n) => n.label === "Thiết diện");
    expect(secCat).toBeDefined();
    expect(secCat!.children.some((c) => c.id === "vong_giao")).toBe(true);
    expect(tree.some((n) => n.label === "Khác")).toBe(false);

    // Exploding "section" group translates circle3 with non-zero center (0, 0, 3) away from origin
    const st = explode(TRANG_THAI_DAU, "section");
    const tr = visualTransformOf(st, scene, "vong_giao");
    expect(tr.translate[2]).toBeGreaterThan(0);
  });
});
