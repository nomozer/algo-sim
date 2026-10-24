import { describe, expect, it } from "vitest";
import * as THREE from "three";
import {
  THU_TU_TO_THIET_DIEN,
  buildObject3D,
  doanNhuongCanh,
  dongBoNetDayManHinh,
  tinhViTriNhanDiem,
} from "./scene3d-view";
import { diemHuuHan, type Scene3D, type SceneObject } from "./scene3d-model";
import { hangCuThe } from "./pick-target";
import { semanticTree } from "./interaction-state";
import { PHONG_CACH_SCENE3D } from "./scene3d-roles";

describe("Session 1 (P2–P5) — Unified Geometry Visual System & Curved Solid Presentation", () => {
  it("unifies curved_solid surface material with polyhedral mesh palette (DESIGN sky, common normal / selected opacity)", () => {
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
      expect(matDefault.color.getHex()).toBe(PHONG_CACH_SCENE3D.colors.mesh);
      expect(matDefault.opacity).toBeCloseTo(polyMat.opacity, 5);
      expect(matDefault.opacity).toBeCloseTo(PHONG_CACH_SCENE3D.opacity.solid, 5);

      const groupHighlighted = buildObject3D(curvedObj, true)!;
      const meshHighlighted = groupHighlighted.children.find(
        (c): c is THREE.Mesh =>
          c instanceof THREE.Mesh && (c.material as THREE.Material).colorWrite !== false,
      )!;
      const matHighlighted = meshHighlighted.material as THREE.MeshStandardMaterial;
      expect(matHighlighted.opacity).toBeCloseTo(PHONG_CACH_SCENE3D.opacity.selectedSolid, 5);
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
    const baseFillMat = baseFill.material as THREE.MeshBasicMaterial;
    expect(baseFillMat.color.getHex()).toBe(PHONG_CACH_SCENE3D.colors.mesh);
    expect(baseFillMat.opacity).toBeCloseTo(0.09, 5);
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
    const secFillMat = secFill.material as THREE.MeshBasicMaterial;
    expect(secFillMat.color.getHex()).toBe(PHONG_CACH_SCENE3D.colors.polygon);
    expect(secFillMat.opacity).toBeCloseTo(PHONG_CACH_SCENE3D.opacity.section, 5);
    expect(secFillMat.depthTest).toBe(true);
    expect(secFillMat.depthFunc).toBe(THREE.LessEqualDepth);
    const secRim = builtCut.children.find(
      (c): c is THREE.Mesh => c instanceof THREE.Mesh && c !== secFill,
    )!;
    expect((secRim.material as THREE.MeshBasicMaterial).color.getHex()).toBe(PHONG_CACH_SCENE3D.colors.sectionOutline);

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
    const elFillMat = elFill.material as THREE.MeshBasicMaterial;
    expect(elFillMat.color.getHex()).toBe(PHONG_CACH_SCENE3D.colors.polygon);
    expect(elFillMat.opacity).toBeCloseTo(PHONG_CACH_SCENE3D.opacity.section, 5);
    expect(elFillMat.depthTest).toBe(true);
    expect(elFillMat.depthFunc).toBe(THREE.LessEqualDepth);
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
  it("aligns Scene3D V6.2 S1 selection semantics (preserving semantic section color #F59E0B/#D97706 and 0.72 context attenuation)", () => {
    const cutCircle: SceneObject = {
      id: "td_sec_sphere",
      label: "Thiết diện tròn",
      type: "circle3",
      render: "circle",
      origin: "derived",
      producer: "intersect_plane_curved",
      depends: ["mp_alpha", "khoi_cau"],
      surface_role: "SECTION_REGION",
      center: ["0", "0", "1"],
      normal: ["0", "0", "1"],
      radius_sq: "4",
    };
    const builtSelected = buildObject3D(cutCircle, true)!;
    const secFill = builtSelected.getObjectByName("section_fill:td_sec_sphere") as THREE.Mesh;
    const secFillMat = secFill.material as THREE.MeshBasicMaterial;
    // SGK reference: section fill and outline are both terracotta; base circles stay shell grey (above).
    expect(secFillMat.color.getHex()).toBe(PHONG_CACH_SCENE3D.colors.polygon);
    expect(secFillMat.color.getHex()).not.toBe(PHONG_CACH_SCENE3D.colors.mesh);
    expect(secFillMat.opacity).toBeCloseTo(PHONG_CACH_SCENE3D.opacity.selectedSection, 5);
    const secRim = builtSelected.children.find(
      (c): c is THREE.Mesh => c instanceof THREE.Mesh && c !== secFill,
    )!;
    expect((secRim.material as THREE.MeshBasicMaterial).color.getHex()).toBe(PHONG_CACH_SCENE3D.colors.sectionOutline);
  });

  it("pilots illustration-quality multi-pixel Line2 hierarchy, single-pass outward polyhedral shells, section-coincident base yielding, standalone plane visibility, and outward radial vertex labels", () => {
    const pyramid: SceneObject = {
      id: "khoi_S_ABCD",
      label: "Hình chóp S.ABCD",
      type: "solid",
      render: "mesh",
      origin: "derived",
      producer: "construct_solid",
      depends: ["S", "A", "B", "C", "D"],
      vertices: [
        ["0", "0", "0"],
        ["2", "0", "0"],
        ["2", "2", "0"],
        ["0", "2", "0"],
        ["0", "0", "3"],
      ],
      vertex_ids: ["A", "B", "C", "D", "S"],
      faces: [
        [0, 1, 2, 3],
        [4, 0, 1],
        [4, 1, 2],
        [4, 2, 3],
        [4, 3, 0],
      ],
    };
    const section: SceneObject = {
      id: "td_ask9",
      label: "Thiết diện M.I1.I2.I3",
      type: "section",
      render: "polygon",
      origin: "derived",
      producer: "construct_section",
      depends: ["khoi_S_ABCD", "mp_ask9"],
      surface_role: "SECTION_REGION",
      polygon: [
        ["0", "0", "3/2"],
        ["1", "0", "3/2"],
        ["1", "1", "3/2"],
        ["0", "1", "3/2"],
      ],
      closed: true,
      fill_visible: true,
    };
    const baseSub: SceneObject = {
      id: "day_MI1I2I3",
      label: "Đáy phụ M.I1.I2.I3",
      type: "polygon3",
      render: "polygon",
      origin: "derived",
      producer: "construct_polygon",
      depends: ["M", "I1", "I2", "I3"],
      surface_role: "AUXILIARY_SURFACE",
      formation_roles: ["CONSTRUCT_BASE"],
      polygon: [
        ["0", "0", "3/2"],
        ["1", "0", "3/2"],
        ["1", "1", "3/2"],
        ["0", "1", "3/2"],
      ],
      closed: true,
      fill_visible: true,
    };

    // 1. Coincident auxiliary base polygon yields to active closed section when unexploded
    const yielded = doanNhuongCanh([pyramid, section, baseSub], () => "0,0,0");
    expect(yielded.has("day_MI1I2I3")).toBe(true);
    expect(yielded.has("td_ask9")).toBe(false);

    // 2. SGK shell (reference addPolyhedronShell): unlit FrontSide pass at full shell opacity plus ONE BackSide pass at
    //    shellBackRatio × opacity — bounded compound alpha, never a DoubleSide mesh at full opacity.
    const pyrGroup = buildObject3D(pyramid, false, undefined, diemHuuHan([pyramid]), undefined, undefined, undefined, false)!;
    const shellPasses = pyrGroup.children.filter(
      (c): c is THREE.Mesh => c instanceof THREE.Mesh && (c.material as THREE.Material).colorWrite !== false,
    );
    expect(shellPasses.map((m) => (m.material as THREE.Material).side)).toEqual([THREE.FrontSide, THREE.BackSide]);
    const [front, back] = shellPasses.map((m) => m.material as THREE.MeshBasicMaterial);
    expect(front).toBeInstanceOf(THREE.MeshBasicMaterial);
    expect(back.opacity).toBeCloseTo(front.opacity * PHONG_CACH_SCENE3D.opacity.shellBackRatio, 6);

    // 3. Multi-pixel Line2 fat-line synchronization enforces stroke hierarchy
    const secGroup = buildObject3D(section, false, undefined, diemHuuHan([pyramid]))!;
    const root = new THREE.Group();
    root.add(pyrGroup, secGroup);
    const fatGroup = new THREE.Group();
    const summary = dongBoNetDayManHinh([root], fatGroup, 1280, 720);
    expect(summary.totalLines).toBeGreaterThan(0);
    expect(summary.maxSectionBorderWidth).toBeGreaterThan(summary.maxVisibleEdgeWidth);
    expect(summary.maxVisibleEdgeWidth).toBeGreaterThan(summary.minHiddenEdgeWidth);

    // 4. SGK reference (addCuttingPlanePatch): the finite plane patch ALWAYS carries a dashed violet border — with or
    //    without a closed section — so the patch edge is never read as a real (solid) edge.
    const planeObj: SceneObject = {
      id: "mp_P",
      label: "Mặt phẳng (P)",
      type: "plane3",
      render: "surface",
      origin: "derived",
      producer: "construct_plane",
      depends: ["B", "SC"],
      point: ["2", "0", "0"],
      normal: ["2", "2", "-3"],
    };
    const diemNen = diemHuuHan([pyramid]);
    const carrierPlane = buildObject3D(planeObj, false, undefined, diemNen)!;
    const carrierBorder = carrierPlane.getObjectByName("plane_border:mp_P") as THREE.Line;
    expect(carrierBorder.material).toBeInstanceOf(THREE.LineDashedMaterial);
    expect((carrierBorder.material as THREE.LineDashedMaterial).colorWrite).toBe(true);
    expect((carrierBorder.material as THREE.LineDashedMaterial).color.getHex()).toBe(PHONG_CACH_SCENE3D.colors.planeOutline);

    const standalonePlane = buildObject3D(
      planeObj, false, undefined, diemNen, undefined, undefined, undefined, false, "primary", false,
    )!;
    const standaloneBorder = standalonePlane.getObjectByName("plane_border:mp_P") as THREE.Line;
    expect(standaloneBorder.material).toBeInstanceOf(THREE.LineDashedMaterial);
    expect((standaloneBorder.material as THREE.LineDashedMaterial).opacity).toBeGreaterThanOrEqual(0.28);

    // 5. Outward radial & right-angle-avoiding vertex label placement
    const placed = tinhViTriNhanDiem(
      [
        { id: "S", x: 300, y: 60, w: 18, h: 18 },
        { id: "A", x: 210, y: 260, w: 18, h: 18 },
        { id: "B", x: 120, y: 360, w: 18, h: 18 },
        { id: "C", x: 350, y: 395, w: 18, h: 18 },
        { id: "D", x: 470, y: 295, w: 18, h: 18 },
      ],
      [
        { ax: 300, ay: 60, bx: 210, by: 260 },
        { ax: 210, ay: 260, bx: 120, by: 360 },
        { ax: 210, ay: 260, bx: 470, by: 295 },
      ],
      [{ fx: 210, fy: 260, cx: 224, cy: 248 }],
    );
    const boxA = placed.get("A")!;
    expect(boxA).toBeDefined();
    // Center of label A should be pushed outward-left (away from right-angle corner at (224, 248) and away from vertex dot (210, 260))
    const centerAx = boxA.x + 9;
    const centerAy = boxA.y + 9;
    expect(Math.hypot(centerAx - 210, centerAy - 260)).toBeGreaterThanOrEqual(12);
    expect(Math.hypot(centerAx - 224, centerAy - 248)).toBeGreaterThan(Math.hypot(210 - 224, 260 - 248));
  });
});
