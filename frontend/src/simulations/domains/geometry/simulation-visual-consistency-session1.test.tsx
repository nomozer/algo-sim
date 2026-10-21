import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { THU_TU_TO_THIET_DIEN, buildObject3D } from "./scene3d-view";
import { diemHuuHan, type Scene3D, type SceneObject } from "./scene3d-model";
import { hangCuThe } from "./pick-target";
import { semanticTree } from "./interaction-state";

describe("Session 1 (P2–P5) — Unified Geometry Visual System & Curved Solid Presentation", () => {
  it("unifies curved_solid surface material with polyhedral mesh palette (slate-blue 0x647a96, opacity 0.22 / 0.36)", () => {
    const polyObj: SceneObject = {
      id: "chop",
      label: "Hình chóp S.ABC",
      type: "solid",
      render: "mesh",
      origin: "derived",
      producer: "construct_solid",
      depends: ["S", "A", "B", "C"],
      vertices: [
        ["0", "0", "3"],
        ["0", "0", "0"],
        ["2", "0", "0"],
        ["0", "2", "0"],
      ],
      faces: [
        [1, 2, 3],
        [0, 1, 2],
        [0, 2, 3],
        [0, 3, 1],
      ],
    };
    const polyGroup = buildObject3D(polyObj, false)!;
    const polyMesh = polyGroup.children.find(
      (c): c is THREE.Mesh =>
        c instanceof THREE.Mesh && (c.material as THREE.Material).colorWrite !== false,
    )!;
    const polyMat = polyMesh.material as THREE.MeshStandardMaterial;

    for (const kind of ["cylinder", "cone", "ball"] as const) {
      const curvedObj: SceneObject = {
        id: `khoi_${kind}`,
        label: `Khối ${kind}`,
        type: "curved_solid",
        render: "curved_solid",
        origin: "derived",
        producer: "construct_curved_solid",
        depends: ["O", "R"],
        curved_kind: kind,
        anchor: ["0", "0", "0"],
        radius_sq: "9",
        height_sq: kind === "ball" ? "0" : "16",
      };
      const groupDefault = buildObject3D(curvedObj, false)!;
      const meshDefault = groupDefault.children.find(
        (c): c is THREE.Mesh =>
          c instanceof THREE.Mesh && (c.material as THREE.Material).colorWrite !== false,
      )!;
      const matDefault = meshDefault.material as THREE.MeshStandardMaterial;
      expect(matDefault.color.getHex()).toBe(polyMat.color.getHex());
      expect(matDefault.color.getHex()).toBe(0x647a96);
      expect(matDefault.opacity).toBeCloseTo(polyMat.opacity, 5);
      expect(matDefault.opacity).toBeCloseTo(0.22, 5);

      const groupHighlighted = buildObject3D(curvedObj, true)!;
      const meshHighlighted = groupHighlighted.children.find(
        (c): c is THREE.Mesh =>
          c instanceof THREE.Mesh && (c.material as THREE.Material).colorWrite !== false,
      )!;
      const matHighlighted = meshHighlighted.material as THREE.MeshStandardMaterial;
      expect(matHighlighted.opacity).toBeCloseTo(0.36, 5);
    }
  });

  it("distinguishes structural base circles (BASE_REGION) from cutting circular/elliptical sections (SECTION_REGION)", () => {
    const baseCircle: SceneObject = {
      id: "duong_tron_day_cyl",
      label: "Đường tròn đáy",
      type: "circle3",
      render: "circle",
      origin: "derived",
      producer: "intersect_plane_curved",
      depends: ["mp_day", "khoi_cyl"],
      surface_role: "BASE_REGION",
      center: ["0", "0", "0"],
      normal: ["0", "0", "1"],
      radius_sq: "4",
    };
    const builtBase = buildObject3D(baseCircle, false)!;
    const baseFill = builtBase.getObjectByName("polygon_fill:duong_tron_day_cyl") as THREE.Mesh;
    expect(baseFill).toBeDefined();
    const baseFillMat = baseFill.material as THREE.MeshStandardMaterial;
    expect(baseFillMat.color.getHex()).toBe(0x647a96);
    expect(baseFillMat.opacity).toBeCloseTo(0.12, 5);
    const baseRim = builtBase.children.find(
      (c): c is THREE.Mesh => c instanceof THREE.Mesh && c !== baseFill,
    )!;
    expect((baseRim.material as THREE.MeshBasicMaterial).color.getHex()).toBe(0x1e293b);

    const cutCircle: SceneObject = {
      id: "td_sec_parallel",
      label: "Thiết diện tròn",
      type: "circle3",
      render: "circle",
      origin: "derived",
      producer: "intersect_plane_curved",
      depends: ["mp_alpha", "khoi_cyl"],
      surface_role: "SECTION_REGION",
      center: ["0", "0", "1"],
      normal: ["0", "0", "1"],
      radius_sq: "4",
    };
    const builtCut = buildObject3D(cutCircle, false)!;
    const secFill = builtCut.getObjectByName("section_fill:td_sec_parallel") as THREE.Mesh;
    expect(secFill).toBeDefined();
    expect(secFill.renderOrder).toBe(THU_TU_TO_THIET_DIEN);
    const secFillMat = secFill.material as THREE.MeshStandardMaterial;
    expect(secFillMat.color.getHex()).toBe(0xf59e0b);
    expect(secFillMat.opacity).toBeCloseTo(0.28, 5);
    expect(secFillMat.depthTest).toBe(true);
    expect(secFillMat.depthFunc).toBe(THREE.AlwaysDepth);
    const secRim = builtCut.children.find(
      (c): c is THREE.Mesh => c instanceof THREE.Mesh && c !== secFill,
    )!;
    expect((secRim.material as THREE.MeshBasicMaterial).color.getHex()).toBe(0xf59e0b);

    const cutEllipse: SceneObject = {
      id: "td_sec_el",
      label: "Thiết diện elip",
      type: "ellipse3",
      render: "ellipse",
      origin: "derived",
      producer: "intersect_plane_curved_ellipse",
      depends: ["mp_P", "khoi_cyl"],
      surface_role: "SECTION_REGION",
      center: ["0", "0", "3"],
      normal: ["1", "0", "-1"],
      major_dir: ["1", "0", "1"],
      minor_dir: ["0", "1", "0"],
      semi_major_sq: "8",
      semi_minor_sq: "4",
    };
    const builtEllipse = buildObject3D(cutEllipse, false)!;
    const elFill = builtEllipse.getObjectByName("section_fill:td_sec_el") as THREE.Mesh;
    expect(elFill).toBeDefined();
    expect(elFill.renderOrder).toBe(THU_TU_TO_THIET_DIEN);
    const elFillMat = elFill.material as THREE.MeshStandardMaterial;
    expect(elFillMat.color.getHex()).toBe(0xf59e0b);
    expect(elFillMat.opacity).toBeCloseTo(0.28, 5);
    expect(elFillMat.depthTest).toBe(true);
    expect(elFillMat.depthFunc).toBe(THREE.AlwaysDepth);
  });

  it("computes tight cone and circle bounds in diemHuuHan without inflating cone apex horizontally", () => {
    const coneObj: SceneObject = {
      id: "non",
      label: "Hình nón S.O",
      type: "curved_solid",
      render: "curved_solid",
      origin: "derived",
      producer: "construct_curved_solid",
      depends: ["O", "S", "R"],
      curved_kind: "cone",
      anchor: ["0", "0", "0"],
      apex_or_top: ["0", "0", "4"],
      radius_sq: "9",
      height_sq: "16",
    };
    const pts = diemHuuHan([coneObj]);
    const topPts = pts.filter((p) => Math.abs(p[2] - 4) < 1e-6);
    expect(topPts.length).toBeGreaterThan(0);
    for (const p of topPts) {
      expect(p[0]).toBeCloseTo(0, 5);
      expect(p[1]).toBeCloseTo(0, 5);
    }

    const cirObj: SceneObject = {
      id: "vong",
      label: "Đường tròn",
      type: "circle3",
      render: "circle",
      origin: "derived",
      producer: "intersect_plane_curved",
      depends: [],
      center: ["0", "0", "2"],
      normal: ["0", "0", "1"],
      radius_sq: "16",
    };
    const cirPts = diemHuuHan([cirObj]);
    const maxR = Math.max(...cirPts.map((p) => Math.hypot(p[0], p[1])));
    expect(maxR).toBeCloseTo(4, 5);
  });

  it("ranks interior segments and circular/elliptical sections ahead of outer curved_solid shells in pick-target and categorizes base circles under Đa giác", () => {
    expect(hangCuThe("point3")).toBeLessThan(hangCuThe("segment3"));
    expect(hangCuThe("segment3")).toBe(hangCuThe("edge"));
    expect(hangCuThe("circle3")).toBe(hangCuThe("section"));
    expect(hangCuThe("ellipse3")).toBe(hangCuThe("section"));
    expect(hangCuThe("circle3")).toBeLessThan(hangCuThe("curved_solid"));
    expect(hangCuThe("segment3")).toBeLessThan(hangCuThe("curved_solid"));

    const scene: Scene3D = {
      objects: [
        {
          id: "duong_tron_day_1",
          label: "Đường tròn đáy",
          type: "circle3",
          render: "circle",
          origin: "derived",
          producer: "intersect_plane_curved",
          depends: [],
          surface_role: "BASE_REGION",
        },
        {
          id: "td_cat",
          label: "Thiết diện tròn",
          type: "circle3",
          render: "circle",
          origin: "derived",
          producer: "intersect_plane_curved",
          depends: [],
          surface_role: "SECTION_REGION",
        },
      ],
      free_objects: [],
      events: [],
    };
    const tree = semanticTree(scene);
    const polyCat = tree.find((n) => n.label === "Đa giác");
    const secCat = tree.find((n) => n.label === "Thiết diện");
    expect(polyCat?.children.some((c) => c.id === "duong_tron_day_1")).toBe(true);
    expect(secCat?.children.some((c) => c.id === "td_cat")).toBe(true);
  });
});
