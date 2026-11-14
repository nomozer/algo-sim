import { renderToString } from "react-dom/server";
import * as THREE from "three";
import { describe, expect, it } from "vitest";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { veKhongGian } from "./scene3d-chart";
import {
  clampStep,
  diemHuuHan,
  objectsAt,
  stepCount,
  toVec3,
  type Scene3D,
  type Vec3,
} from "./scene3d-model";
import { auditSceneRepresentationConsistency } from "./scene3d-representation-consistency";
import {
  compactPlaneAnchorPoints,
  computeBoundedStudiedPlanePolygon,
  isCoordinatePlaneInterceptPolygon,
  resolveAdaptivePlaneVisualization,
  resolvePlaneSectionVisibility,
} from "./scene3d-semantic-policy";
import { buildObject3D } from "./scene3d-view";
import { Scene3DExplorer } from "./Scene3DExplorer";

function extractScene(id: string): Scene3D {
  const s = GEOMETRY_SAMPLES.find((x) => x.id === id);
  if (!s) throw new Error(`Missing catalog sample: ${id}`);
  return (s.envelope as unknown as { scene3d: Scene3D }).scene3d;
}

function maxDiagonal(pts: readonly Vec3[]): number {
  let d = 0;
  for (let i = 0; i < pts.length; i += 1) {
    for (let j = i + 1; j < pts.length; j += 1) {
      d = Math.max(
        d,
        Math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1], pts[i][2] - pts[j][2]),
      );
    }
  }
  return d;
}

function distToPlane(p: Vec3, origin: Vec3, normalRaw: Vec3): number {
  const nLen = Math.hypot(normalRaw[0], normalRaw[1], normalRaw[2]) || 1;
  return Math.abs(
    ((p[0] - origin[0]) * normalRaw[0]
      + (p[1] - origin[1]) * normalRaw[1]
      + (p[2] - origin[2]) * normalRaw[2]) / nLen,
  );
}

function createSyntheticStandaloneOxyzBase(): Scene3D {
  return {
    free_objects: ["A", "B", "C", "E", "mp_P"],
    events: [
      { action: "CREATE", object: "A", step_index: 0, depends: [], explanation: "Điểm A" },
      { action: "CREATE", object: "B", step_index: 1, depends: [], explanation: "Điểm B" },
      { action: "CREATE", object: "C", step_index: 2, depends: [], explanation: "Điểm C" },
      { action: "CREATE", object: "mp_P", step_index: 3, depends: ["A", "B", "C"], explanation: "Mặt phẳng (P)" },
      { action: "CREATE", object: "E", step_index: 4, depends: [], explanation: "Điểm E" },
    ],
    objects: [
      { id: "A", type: "point3", render: "point_marker", origin: "free", producer: "test", xyz: ["2", "0", "0"], depends: [], label: "A" },
      { id: "B", type: "point3", render: "point_marker", origin: "free", producer: "test", xyz: ["0", "2", "0"], depends: [], label: "B" },
      { id: "C", type: "point3", render: "point_marker", origin: "free", producer: "test", xyz: ["0", "0", "2"], depends: [], label: "C" },
      {
        id: "mp_P",
        type: "plane3",
        render: "surface",
        origin: "free",
        producer: "test",
        point: ["2", "0", "0"],
        normal: ["1", "1", "1"],
        depends: ["A", "B", "C"],
        label: "(P)",
      },
      { id: "E", type: "point3", render: "point_marker", origin: "free", producer: "test", xyz: ["3", "3", "3"], depends: [], label: "E" },
    ],
  };
}

describe("AXO V9.4.14 — Geometry Visualization Simplification & Pedagogical Consistency", () => {
  it("Scenario 1 (Oxyz): plane (P) renders minimal triangle ABC (no outer 4-gon) and intercept polygon is flagged for dedup", () => {
    const raw = extractScene("oxyz-giao-diem-duong-mat");
    const scene = veKhongGian(raw);
    const mpP = scene.objects.find((o) => o.id === "mp_P")!;
    const tamGiac = scene.objects.find((o) => o.id === "tam_giac_ABC")!;
    expect(mpP).toBeDefined();
    expect(tamGiac).toBeDefined();

    const dec = resolveAdaptivePlaneVisualization(scene, mpP, scene.objects);
    expect(dec.mode).toBe("MINIMAL_GEOMETRY");
    expect(dec.patchVertices).toHaveLength(3);

    const bounded = computeBoundedStudiedPlanePolygon(scene, mpP, scene.objects);
    expect(bounded).toHaveLength(3);
    for (const id of ["A", "B", "C"]) {
      const p = toVec3(scene.objects.find((o) => o.id === id)!.xyz!);
      expect(Math.min(...bounded.map((v) => Math.hypot(v[0] - p[0], v[1] - p[1], v[2] - p[2])))).toBeLessThan(1e-6);
    }

    // tam_giac_ABC is identified as a coplanar coordinate-intercept duplicate of visible mp_P
    expect(isCoordinatePlaneInterceptPolygon(scene, tamGiac)).toBe(true);
    const p0 = toVec3(mpP.point!);
    const n = toVec3(mpP.normal!);
    for (const v of tamGiac.polygon ?? tamGiac.vertices ?? []) {
      expect(distToPlane(toVec3(v), p0, n)).toBeLessThan(1e-5);
    }

    // Three.js mesh built for mp_P has exactly 3 coplanar vertices
    const built = buildObject3D(
      mpP,
      false,
      undefined,
      diemHuuHan(scene.objects),
      new THREE.Vector3(8, 6, 7),
      undefined,
      undefined,
      false,
      "primary",
      true,
      true,
      false,
      scene,
      undefined,
      undefined,
      bounded,
      scene.objects,
    )!;
    expect(built).toBeTruthy();
    const meshes: THREE.Mesh[] = [];
    built.traverse((c) => { if (c instanceof THREE.Mesh) meshes.push(c); });
    expect(meshes.length).toBeGreaterThanOrEqual(1);
    expect(meshes[0].geometry.getAttribute("position").count).toBe(3);
  });

  it("Scenarios 2, 3, 4 (Polyhedron Oblique Sections): minimal △MNP/△NPQ at intermediate step and retired plane on completed section", () => {
    const obliqueSamples = [
      { id: "chop-thiet-dien-ba-diem", planeId: "mp_MNP", sectionVerts: 5 },
      { id: "lap-phuong-thiet-dien-bat-ky", planeId: "mp_MNP", sectionVerts: 6 },
      { id: "lang-tru-tam-giac-thiet-dien", planeId: "mp_NPQ", sectionVerts: 5 },
    ];

    for (const tc of obliqueSamples) {
      const raw = extractScene(tc.id);
      const scene = veKhongGian(raw);
      const midVis = objectsAt(scene, 10);
      const midPlane = midVis.find((o) => o.id === tc.planeId)!;
      expect(midPlane).toBeDefined();

      // Intermediate step shows minimal 3-vertex defining triangle
      const midDec = resolveAdaptivePlaneVisualization(scene, midPlane, midVis);
      expect(midDec.mode).toBe("MINIMAL_GEOMETRY");
      expect(midDec.patchVertices).toHaveLength(3);
      expect(resolvePlaneSectionVisibility(scene, midPlane, 10, false).visible).toBe(true);

      // Completed step retires redundant purple plane while terracotta section shows exact edges/vertices
      const finalStep = Math.max(0, stepCount(scene) - 1);
      const finalPlane = scene.objects.find((o) => o.id === tc.planeId)!;
      const finalVis = resolvePlaneSectionVisibility(scene, finalPlane, finalStep, false);
      expect(finalVis.visible).toBe(false);
      expect(finalVis.lifecycleStage).toBe("retired_scaffold");

      // Auxiliary toggle and direct selection restore the plane cleanly
      expect(resolvePlaneSectionVisibility(scene, finalPlane, finalStep, true).visible).toBe(true);
      expect(resolvePlaneSectionVisibility(scene, finalPlane, finalStep, false, tc.planeId).visible).toBe(true);

      const sec = scene.objects.find((o) => o.type === "section" && (o.depends ?? []).includes(tc.planeId))!;
      expect((sec.polygon ?? sec.vertices ?? []).length).toBe(tc.sectionVerts);
    }
  });

  it("Scenario 5 & 6 (Single vs Multi Studied Planes): single non-cutting planes stay minimal triangle; coexisting intersection planes use compact 4-gon", () => {
    // Single non-cutting studied plane (SAC) on khoang-cach-hai-duong-cheo-nhau
    const skewScene = veKhongGian(extractScene("khoang-cach-hai-duong-cheo-nhau"));
    const sac = skewScene.objects.find((o) => o.id === "sac")!;
    const skewDec = resolveAdaptivePlaneVisualization(skewScene, sac, skewScene.objects);
    expect(skewDec.mode).toBe("MINIMAL_GEOMETRY");
    expect(skewDec.patchVertices).toHaveLength(3);
    expect(resolvePlaneSectionVisibility(skewScene, sac, stepCount(skewScene) - 1, false).visible).toBe(true);

    // Multi-plane coexisting intersection (SAH) & (SBC) on goc-nhi-dien-hai-mat-phang -> compact 4-gon
    const dihedralScene = veKhongGian(extractScene("goc-nhi-dien-hai-mat-phang"));
    for (const plId of ["mp_SAH", "sbc"]) {
      const pl = dihedralScene.objects.find((o) => o.id === plId)!;
      const dec = resolveAdaptivePlaneVisualization(dihedralScene, pl, dihedralScene.objects);
      expect(dec.mode).toBe("COMPACT_PLANE_PATCH");
      expect(dec.patchVertices).toHaveLength(4);
      expect(maxDiagonal(dec.patchVertices)).toBeLessThan(10.0);
    }
  });

  it("Curved Solids & Sphere Tangent/Secant: MODE B COMPACT_PLANE_PATCH with tight cut/tangent footprint", () => {
    // Cone parallel cut: rCut = 3, tight patch diag around ~9.9 (not blown up to base R=6 -> ~21)
    const coneScene = veKhongGian(extractScene("hinh-non-cat-song-song-day"));
    const conePlane = coneScene.objects.find((o) => o.type === "plane3")!;
    const coneDec = resolveAdaptivePlaneVisualization(coneScene, conePlane, coneScene.objects);
    expect(coneDec.mode).toBe("COMPACT_PLANE_PATCH");
    expect(maxDiagonal(coneDec.patchVertices)).toBeLessThan(10.5);

    // Cylinder circular cut: R = 2, rCut = 2, tight collar
    const cylScene = veKhongGian(extractScene("tru-thiet-dien-tron"));
    const cylPlane = cylScene.objects.find((o) => o.type === "plane3")!;
    const cylDec = resolveAdaptivePlaneVisualization(cylScene, cylPlane, cylScene.objects);
    expect(cylDec.mode).toBe("COMPACT_PLANE_PATCH");
    expect(maxDiagonal(cylDec.patchVertices)).toBeLessThan(7.0);

    // Sphere tangent plane: tight patch around tangent point & line segment (diag < 8.5, well under 11.2)
    const tanScene = veKhongGian(extractScene("mat-phang-tiep-xuc-mat-cau"));
    const tanPlane = tanScene.objects.find((o) => o.type === "plane3")!;
    const tanDec = resolveAdaptivePlaneVisualization(tanScene, tanPlane, tanScene.objects);
    expect(tanDec.mode).toBe("COMPACT_PLANE_PATCH");
    expect(maxDiagonal(tanDec.patchVertices)).toBeLessThan(8.5);

    // Sphere secant cut: encircles cut circle cleanly
    const secSphereScene = veKhongGian(extractScene("mat-cau-cat-mat-phang"));
    const secSpherePlane = secSphereScene.objects.find((o) => o.type === "plane3")!;
    const secSphereDec = resolveAdaptivePlaneVisualization(secSphereScene, secSpherePlane, secSphereScene.objects);
    expect(secSphereDec.mode).toBe("COMPACT_PLANE_PATCH");
    expect(secSphereDec.patchVertices).toHaveLength(4);
  });

  it("Scenario 7 (Exterior Intersection Outside △ABC): keeps MINIMAL_GEOMETRY without expanding a huge rectangle and passes consistency audit", () => {
    const raw = createSyntheticStandaloneOxyzBase();
    // Line intersects x+y+z = 2 at I(4, 4, -6), which lies strictly outside △ABC (x,y,z >= 0)
    raw.objects.push(
      { id: "I", type: "point3", render: "point_marker", origin: "derived", producer: "test", xyz: ["4", "4", "-6"], depends: ["E", "mp_P"], label: "I" },
      {
        id: "duong_EI",
        type: "segment3",
        render: "segment",
        origin: "derived",
        producer: "test",
        point_a: ["3", "3", "3"],
        point_b: ["4", "4", "-6"],
        depends: ["E", "I"],
        label: "EI",
      },
    );
    raw.events.push(
      { action: "CREATE", object: "I", step_index: 5, depends: ["E", "mp_P"], explanation: "Giao điểm I" },
      { action: "CREATE", object: "duong_EI", step_index: 6, depends: ["E", "I"], explanation: "Đoạn EI" },
    );

    const scene = veKhongGian(raw);
    const mpP = scene.objects.find((o) => o.id === "mp_P")!;
    const dec = resolveAdaptivePlaneVisualization(scene, mpP, scene.objects);
    expect(dec.mode).toBe("MINIMAL_GEOMETRY");
    expect(dec.patchVertices).toHaveLength(3);

    // V9.4.14 validator must accept valid finite △ABC even when coplanar intersection point I lies outside △ABC
    const audit = auditSceneRepresentationConsistency(raw);
    expect(audit.overallStatus, JSON.stringify(audit.findings)).toBe("VALID");
    expect(audit.isConsistent).toBe(true);
  });

  it("Scenario 8 (MODE C — CONTROLLED_EXTENDED_PATCH): expands minimally and locally only around ungrounded exterior witness foot", () => {
    const raw = createSyntheticStandaloneOxyzBase();
    // E=(5,5,-5) projects orthogonally onto H=(4,4,-6) on x+y+z=2, strictly outside △ABC
    const eObj = raw.objects.find((o) => o.id === "E")!;
    eObj.xyz = ["5", "5", "-5"];
    raw.objects.push(
      { id: "H", type: "point3", render: "point_marker", origin: "derived", producer: "test", xyz: ["4", "4", "-6"], depends: ["E", "mp_P"], label: "H" },
      {
        id: "duan_EH",
        type: "segment3",
        render: "segment",
        origin: "derived",
        producer: "test",
        point_a: ["5", "5", "-5"],
        point_b: ["4", "4", "-6"],
        depends: ["E", "H"],
        perpendicular_witness: {
          from: "E",
          on: "mp_P",
          foot: ["4", "4", "-6"],
          marker: { u: ["-2", "-4", "6"], v: ["1", "1", "1"] },
        },
        label: "EH",
      },
    );
    raw.events.push(
      { action: "CREATE", object: "H", step_index: 5, depends: ["E", "mp_P"], explanation: "Hình chiếu H" },
      { action: "CREATE", object: "duan_EH", step_index: 6, depends: ["E", "H"], explanation: "Đoạn EH" },
    );

    const scene = veKhongGian(raw);
    const mpP = scene.objects.find((o) => o.id === "mp_P")!;
    const dec = resolveAdaptivePlaneVisualization(scene, mpP, scene.objects);
    expect(dec.mode).toBe("CONTROLLED_EXTENDED_PATCH");
    expect(dec.patchVertices.length).toBeGreaterThanOrEqual(4);

    // All controlled extension vertices stay strictly coplanar on x + y + z = 2
    const p0 = toVec3(mpP.point!);
    const n = toVec3(mpP.normal!);
    for (const v of dec.patchVertices) {
      expect(distToPlane(v, p0, n)).toBeLessThan(1e-6);
    }

    // Controlled convex patch stays bounded tightly to hull(A,B,C,H) + ~6.5% padding rather than blowing up to a 16+ billboard
    const hullPts = [
      toVec3(["2", "0", "0"]),
      toVec3(["0", "2", "0"]),
      toVec3(["0", "0", "2"]),
      toVec3(["4", "4", "-6"]),
    ];
    const baseHullDiag = maxDiagonal(hullPts);
    const patchDiag = maxDiagonal(dec.patchVertices);
    expect(patchDiag).toBeGreaterThan(baseHullDiag);
    expect(patchDiag).toBeLessThan(baseHullDiag * 1.25);

    const audit = auditSceneRepresentationConsistency(raw);
    expect(audit.overallStatus, JSON.stringify(audit.findings)).toBe("VALID");
  });

  it("All 22 Catalog Samples: valid consistency across every step, no future leakage, no input mutation, and no extra visualization UI toggles", () => {
    expect(GEOMETRY_SAMPLES.length).toBe(22);

    for (const sample of GEOMETRY_SAMPLES) {
      const raw = (sample.envelope as unknown as { scene3d: Scene3D }).scene3d;
      const beforeJson = JSON.stringify(raw);
      const scene = veKhongGian(raw);
      const total = stepCount(scene);
      expect(total).toBeGreaterThanOrEqual(1);

      const seenPerStep: Set<string>[] = [];
      for (let k = 0; k < total; k += 1) {
        const vis = objectsAt(scene, k);
        seenPerStep.push(new Set(vis.map((o) => o.id)));
        const report = auditSceneRepresentationConsistency(raw, { step: k });
        expect(
          report.overallStatus,
          `${sample.id} step ${k} failed consistency: ${JSON.stringify(report.findings)}`,
        ).toBe(report.sceneScale > 0 ? "VALID" : "UNDETERMINED");

        // Every visible surface builds valid coplanar Three.js mesh geometry in the shared scene frame
        const diemNen = diemHuuHan(vis);
        for (const obj of vis) {
          if (obj.render !== "surface") continue;
          const b = computeBoundedStudiedPlanePolygon(scene, obj, vis);
          const c = b.length < 3 ? compactPlaneAnchorPoints(scene, obj, vis) : [];
          const patch = b.length >= 3 ? b : c;
          if (patch.length >= 3 && obj.point && obj.normal) {
            const p0 = toVec3(obj.point);
            const n = toVec3(obj.normal);
            for (const pt of patch) {
              expect(distToPlane(pt, p0, n)).toBeLessThan(1e-3);
            }
          }
          if (obj.type === "plane3") {
            const built = buildObject3D(
              obj,
              false,
              undefined,
              diemNen,
              new THREE.Vector3(8, 6, 7),
              undefined,
              undefined,
              false,
              "primary",
              true,
              true,
              false,
              scene,
              undefined,
              undefined,
              patch,
              vis,
            );
            expect(built).toBeTruthy();
          }
        }
      }

      // Monotonic construction without future-step object leakage
      for (let k = 1; k < seenPerStep.length; k += 1) {
        for (const prevId of seenPerStep[k - 1]) {
          expect(seenPerStep[k].has(prevId), `${sample.id} lost ${prevId} between steps ${k - 1}->${k}`).toBe(true);
        }
      }

      // Backward step clamping / reset to step 0 preserves exact initial set
      const backTo0 = objectsAt(scene, clampStep(scene, 0)).map((o) => o.id);
      expect(backTo0).toEqual([...seenPerStep[0]]);

      // Zero mutation of caller Scene3D
      expect(JSON.stringify(raw)).toBe(beforeJson);
    }

    // Confirm no user-facing plane mode switcher or dropdown was added to Scene3DExplorer
    const explorerHtml = renderToString(<Scene3DExplorer scene={extractScene("chop-thiet-dien-ba-diem")} />);
    expect(explorerHtml).not.toMatch(/MINIMAL_GEOMETRY|COMPACT_PLANE_PATCH|CONTROLLED_EXTENDED_PATCH/);
    expect(explorerHtml).not.toMatch(/Chế độ mặt phẳng|Plane Mode/i);
  });
});
