import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { buildObject3D } from "./scene3d-view";
import { diemHuuHan, objectsAt, stepCount, type Scene3D, type SceneObject } from "./scene3d-model";
import { veKhongGian } from "./scene3d-chart";
import { TRANG_THAI_DAU, explode, isolate, select, semanticTree, visualTransformOf } from "./interaction-state";
import { withSubEntities } from "./scene3d-subentities";
import demo1 from "../../../../../docs/evaluation/geometry/runs/simulation-coverage-visual-validation/demos/demo1-pyramid-derived-section.json";
import demo2 from "../../../../../docs/evaluation/geometry/runs/simulation-coverage-visual-validation/demos/demo2-unnamed-section-intersections.json";
import demo3 from "../../../../../docs/evaluation/geometry/runs/simulation-coverage-visual-validation/demos/demo3-multi-solid-shared-geometry.json";
import demo4 from "../../../../../docs/evaluation/geometry/runs/simulation-coverage-visual-validation/demos/demo4-step-by-step-construction.json";
import demo5 from "../../../../../docs/evaluation/geometry/runs/simulation-coverage-visual-validation/demos/demo5-selection-and-highlighting.json";
import demo6a from "../../../../../docs/evaluation/geometry/runs/simulation-coverage-visual-validation/demos/demo6a-curved-cylinder-sections.json";
import demo6b from "../../../../../docs/evaluation/geometry/runs/simulation-coverage-visual-validation/demos/demo6b-curved-cone-frustum-cut.json";
import demo6c from "../../../../../docs/evaluation/geometry/runs/simulation-coverage-visual-validation/demos/demo6c-curved-sphere-plane-cut.json";
import demo7 from "../../../../../docs/evaluation/geometry/runs/simulation-coverage-visual-validation/demos/demo7-invalid-geometry-safe-refusal.json";
import visualReceipt from "../../../../../docs/evaluation/geometry/runs/simulation-coverage-visual-validation/visual-acceptance-receipt.json";
import evalSummary from "../../../../../docs/evaluation/geometry/runs/simulation-coverage-visual-validation/eval-summary.json";

function makeBaseScene(objects: SceneObject[]): Scene3D {
  return {
    objects,
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
      producer: "construct_curved_solid",
      depends: ["I", "R"],
      curved_kind: "ball",
      anchor: ["0", "0", "0"],
      radius_sq: "25",
      height_sq: "0",
      display_group: ["solid"],
    };
    const ballGroup = buildObject3D(ballObj, false);
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
      producer: "construct_curved_solid",
      depends: ["O", "R", "h"],
      curved_kind: "cylinder",
      anchor: ["0", "0", "0"],
      radius_sq: "4",
      height_sq: "9",
      display_group: ["solid"],
    };
    const cylGroup = buildObject3D(cylObj, false);
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
      producer: "construct_curved_solid",
      depends: ["O", "R", "h"],
      curved_kind: "cone",
      anchor: ["0", "0", "0"],
      radius_sq: "9",
      height_sq: "16",
      display_group: ["solid"],
    };
    const coneGroup = buildObject3D(coneObj, false);
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
      producer: "construct_curved_solid",
      depends: ["O", "R", "h"],
      curved_kind: "cone",
      anchor: ["0", "0", "0"],
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
        producer: "construct_curved_solid",
        depends: ["I", "R"],
        curved_kind: "ball",
        anchor: ["0", "0", "0"],
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
        producer: "intersect_plane_curved",
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

  it("verifies P6 interactive demo suite (Demos 1..7) and P7/P8 visual acceptance & evaluation receipts", () => {
    const positiveDemos = [
      { id: "demo1", env: demo1 },
      { id: "demo2", env: demo2 },
      { id: "demo3", env: demo3 },
      { id: "demo4", env: demo4 },
      { id: "demo5", env: demo5 },
      { id: "demo6a", env: demo6a },
      { id: "demo6b", env: demo6b },
      { id: "demo6c", env: demo6c },
    ];

    for (const { id, env } of positiveDemos) {
      expect(env.route_d.status, id).toBe("SERVED");
      const rawScene = env.route_d.scene3d as unknown as Scene3D;
      expect(rawScene, id).toBeTruthy();
      const charted = veKhongGian(rawScene);
      const enriched = withSubEntities(charted);
      const totalSteps = stepCount(enriched);
      expect(totalSteps, id).toBeGreaterThan(1);

      const finalObjects = objectsAt(enriched, totalSteps - 1);
      expect(finalObjects.length, id).toBeGreaterThan(0);
      expect(diemHuuHan(finalObjects).length, id).toBeGreaterThan(0);

      // Every primary object builds a non-null Three.js Object3D
      const primary = finalObjects.filter((o) =>
        ["solid", "curved_solid", "section", "polygon3", "circle3", "ellipse3"].includes(o.type)
      );
      expect(primary.length, id).toBeGreaterThan(0);
      for (const obj of primary) {
        const built = buildObject3D(obj, false);
        expect(built, `${id}:${obj.id}`).not.toBeNull();
      }

      // Semantic tree has no unclassified "Khác" group
      const tree = semanticTree(enriched);
      expect(tree.some((n) => n.label === "Khác"), id).toBe(false);

      // Select / isolate / explode state transitions work cleanly
      const targetId = primary[0]!.id;
      const selState = select(TRANG_THAI_DAU, targetId);
      expect(selState.selected_id).toBe(targetId);
      const isoState = isolate(selState, [targetId]);
      expect(isoState.isolated_ids).toContain(targetId);
    }

    // Demo 7 negative case refuses fail-closed with no fake Scene3D
    expect(demo7.route_d.status).toBe("REFUSED");
    expect(demo7.route_d.refusal?.code).toBe("CURVED_PLANE_DOES_NOT_CUT");
    expect(demo7.route_d.scene3d).toBeNull();

    // P7 real-browser visual acceptance receipt invariants
    expect(visualReceipt.totalScenes).toBe(9);
    expect(visualReceipt.totalConsoleErrors).toBe(0);
    expect(visualReceipt.totalPageErrors).toBe(0);
    for (const r of visualReceipt.results) {
      if (r.served) {
        expect(r.inkPixels, r.id).toBeGreaterThan(0);
        expect(r.cameraChecks!.orbitDiffPixels, r.id).toBeGreaterThan(0);
        expect(r.cameraChecks!.zoomDiffPixels, r.id).toBeGreaterThan(0);
        expect(r.cameraChecks!.panDiffPixels, r.id).toBeGreaterThan(0);
        expect(r.interactionChecks!.selectionDiffPixels, r.id).toBeGreaterThan(0);
        expect(r.interactionChecks!.step0DiffPixels, r.id).toBeGreaterThan(0);
        expect(r.labelChecks!.labelsNotCollapsed, r.id).toBe(true);
        expect(r.depViolations, r.id).toEqual([]);
        const ownMap = (r.ownPixelMap ?? {}) as Record<string, { ownPixels: number }>;
        for (const [oid, pm] of Object.entries(ownMap)) {
          expect(pm.ownPixels, `${r.id}:${oid}`).toBeGreaterThan(0);
        }
      }
    }

    // P8 development evaluation summary invariants
    expect(evalSummary.evaluation_scope).toBe("DEVELOPMENT_EVALUATION_NOT_BLIND");
    expect(evalSummary.all_passed).toBe(true);
    expect(evalSummary.metrics.wrong_serves).toBe(0);
    expect(evalSummary.metrics.positive_served).toBe(10);
    expect(evalSummary.metrics.negative_refused).toBe(5);
  });
});
