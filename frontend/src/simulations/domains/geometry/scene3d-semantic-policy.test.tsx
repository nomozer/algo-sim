import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import * as THREE from "three";
import samplesData from "../../../data/geometry-samples.json";
import circumFixture from "./scene3d-circumsphere-fixture.json";
import inCircumFixtures from "./scene3d-inscribed-circumscribed-fixtures.json";
import supplementalArchetypes from "./scene3d-regression-archetypes-fixtures.json";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import {
  anchorOfGeometryStep,
  geometryStepCount,
  geometryTimeline,
  moRongDaGiacMatPhang,
  daGiacMatPhang,
  objectsAt,
  toNumber,
  toVec3,
  type Scene3D,
  type SceneObject,
} from "./scene3d-model";
import { kyHieuDiem } from "./scene3d-presentation";
import { DICH_CANH_PX, DICH_DIEM_PX } from "./pick-target";
import { PHONG_CACH_SCENE3D } from "./scene3d-roles";
import { chonHuongNhin } from "./scene3d-camera";
import { auxiliaryHiddenAt } from "./scene3d-auxiliary";
import { diemTaiDinhThietDien, entitiesPresentAt, withSubEntities } from "./scene3d-subentities";
import { dongBoNetDayManHinh } from "./scene3d-edge-visibility";
import {
  buildObject3D,
  chonCuThe,
  datCoDauDinh,
  datKhungNhin,
  dungTrucOxyzSuPham,
  updateCanonicalEdgeVisibility,
} from "./scene3d-view";
import { veKhongGian } from "./scene3d-chart";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import {
  SEMANTIC_ROLE_SPECS,
  buildContractReferenceGroup,
  buildPedagogicalConstructionPlan,
  buildVerifiedObjectTooltip,
  cauTrucSuPham,
  classifyCircleSemanticRole,
  classifySceneObjectSemantics,
  classifySphereSemanticRole,
  compactPlaneAnchorPoints,
  computeStepHighlightTargets,
  formatCycleNotation,
  modulateSemanticColor,
  pedagogicalStepList,
  planeSolidEdgeIntersections,
  resolvePlaneSectionVisibility,
  shouldShowSphereReferenceEquator,
  ungroundedFreePointIdsAt,
} from "./scene3d-semantic-policy";

type SampleItem = {
  id: string;
  title: string;
  envelope: {
    description: string;
    scene3d: Scene3D;
  };
};

const SAMPLES = ((samplesData as unknown as { samples?: SampleItem[]; items?: SampleItem[] }).samples
  ?? (samplesData as unknown as { items?: SampleItem[] }).items
  ?? []) as SampleItem[];

function sampleById(id: string): SampleItem {
  const found = SAMPLES.find((s) => s.id === id);
  if (!found) throw new Error(`Missing geometry sample: ${id}`);
  return found;
}

function sceneOf(id: string): Scene3D {
  return structuredClone(sampleById(id).envelope.scene3d);
}

function hslDeg(hex: number): { h: number; s: number; l: number } {
  const out = { h: 0, s: 0, l: 0 };
  new THREE.Color(hex).getHSL(out, THREE.SRGBColorSpace);
  return { h: out.h * 360, s: out.s, l: out.l };
}

function hueDistanceDeg(aHex: number, bHex: number): number {
  const a = hslDeg(aHex);
  const b = hslDeg(bHex);
  if (a.s < 0.05 && b.s < 0.05) return 0;
  const diff = Math.abs(a.h - b.h) % 360;
  return diff > 180 ? 360 - diff : diff;
}

describe("Scene3D Semantic Visualization Policy — Standardized Roles & HTML Reference Palette", () => {
  it("defines all canonical mathematical semantic roles matching HTML PALETTE with distinct hues", () => {
    expect(SEMANTIC_ROLE_SPECS.BOUNDARY_AND_INTERSECTION.colorHex.toLowerCase()).toBe("#1e293b");
    expect(SEMANTIC_ROLE_SPECS.HIDDEN_EDGE.colorHex.toLowerCase()).toBe("#64748b");
    expect(SEMANTIC_ROLE_SPECS.SOLID_SHELL.colorHex.toLowerCase()).toBe("#7c8b9e");
    expect(SEMANTIC_ROLE_SPECS.RESULT_SECTION.colorHex.toLowerCase()).toBe("#c85a32");
    expect(SEMANTIC_ROLE_SPECS.GEOMETRIC_PLANE.colorHex.toLowerCase()).toBe("#6d28d9");
    expect(SEMANTIC_ROLE_SPECS.INSCRIBED_CIRCLE.colorHex.toLowerCase()).toBe("#d97706");
    expect(SEMANTIC_ROLE_SPECS.CIRCUMSCRIBED_CIRCLE.colorHex.toLowerCase()).toBe("#2563eb");
    expect(SEMANTIC_ROLE_SPECS.INSCRIBED_SPHERE.colorHex.toLowerCase()).toBe("#d97706");
    expect(SEMANTIC_ROLE_SPECS.CIRCUMSCRIBED_SPHERE.colorHex.toLowerCase()).toBe("#0f766e");
    expect(SEMANTIC_ROLE_SPECS.CERTIFIED_RELATION_MARKER.colorHex.toLowerCase()).toBe("#0f766e");
    expect(SEMANTIC_ROLE_SPECS.AUXILIARY_CONSTRUCTION.colorHex.toLowerCase()).toBe("#0f766e");
    expect(SEMANTIC_ROLE_SPECS.REFERENCE_EQUATOR.colorHex.toLowerCase()).toBe("#64748b");

    // Circumscribed circle cobalt (#2563EB) must remain distinct from perpendicular/circumsphere teal (#0F766E)
    expect(SEMANTIC_ROLE_SPECS.CIRCUMSCRIBED_CIRCLE.colorHex).not.toBe(
      SEMANTIC_ROLE_SPECS.CERTIFIED_RELATION_MARKER.colorHex,
    );
    // Inscribed amber (#D97706) must remain distinct from terracotta section (#C85A32)
    expect(SEMANTIC_ROLE_SPECS.INSCRIBED_CIRCLE.colorHex).not.toBe(
      SEMANTIC_ROLE_SPECS.RESULT_SECTION.colorHex,
    );
    expect(SEMANTIC_ROLE_SPECS.RESULT_SECTION.prominenceTier).toBeLessThan(
      SEMANTIC_ROLE_SPECS.SOLID_SHELL.prominenceTier,
    );
    expect(SEMANTIC_ROLE_SPECS.SOLID_SHELL.prominenceTier).toBeLessThan(
      SEMANTIC_ROLE_SPECS.AUXILIARY_CONSTRUCTION.prominenceTier,
    );
  });

  it("classifies unseen synthetic scenes purely from verified geometric contract without ID or label hardcoding, and preserves semantic hue on hover & selection", () => {
    const syntheticScene: Scene3D = {
      free_objects: ["v_alpha", "v_beta", "v_gamma", "v_apex"],
      objects: [
        { id: "v_alpha", label: "P1", notation: "X1", type: "point3", render: "point_marker", origin: "free", depends: [], xyz: ["0", "0", "0"] },
        { id: "v_beta", label: "P2", notation: "X2", type: "point3", render: "point_marker", origin: "free", depends: [], xyz: ["4", "0", "0"] },
        { id: "v_gamma", label: "P3", notation: "X3", type: "point3", render: "point_marker", origin: "free", depends: [], xyz: ["0", "4", "0"] },
        { id: "v_apex", label: "P4", notation: "X4", type: "point3", render: "point_marker", origin: "free", depends: [], xyz: ["0", "0", "5"] },
        {
          id: "mystery_body_99",
          label: "Khối bất kỳ",
          type: "solid",
          render: "mesh",
          origin: "derived",
          depends: ["v_alpha", "v_beta", "v_gamma", "v_apex"],
          vertex_ids: ["v_alpha", "v_beta", "v_gamma", "v_apex"],
          vertices: [["0", "0", "0"], ["4", "0", "0"], ["0", "4", "0"], ["0", "0", "5"]],
          faces: [[0, 1, 2], [0, 1, 3], [1, 2, 3], [2, 0, 3]],
        },
        {
          id: "ref_tri_helper",
          label: "Tam giác phụ giải thích",
          type: "polygon3",
          render: "polygon",
          origin: "derived",
          surface_role: "AUXILIARY_SURFACE",
          formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
          display_group: ["construction"],
          depends: ["v_alpha", "v_beta", "v_apex"],
          polygon: [["0", "0", "0"], ["4", "0", "0"], ["0", "0", "5"]],
        },
        {
          id: "cut_plane_z2",
          label: "Mặt cắt ngang",
          type: "plane3",
          render: "surface",
          origin: "derived",
          surface_role: "CUTTING_PLANE",
          formation_roles: ["CONSTRUCT_CUTTING_OBJECT"],
          depends: [],
          point: ["0", "0", "2"],
          normal: ["0", "0", "1"],
        },
        {
          id: "true_cut_poly",
          label: "Thiết diện kết quả",
          type: "section",
          render: "polygon",
          origin: "derived",
          surface_role: "SECTION_REGION",
          formation_roles: ["PRODUCE_SECTION_RESULT"],
          display_group: ["construction", "target"],
          depends: ["mystery_body_99", "cut_plane_z2"],
          polygon: [["0", "0", "2"], ["12/5", "0", "2"], ["0", "12/5", "2"]],
          closed: true,
          fill_visible: true,
        },
      ] as unknown as SceneObject[],
      events: [
        { step_index: 0, action: "CREATE", object: "mystery_body_99", depends: [], explanation: "" },
        { step_index: 1, action: "CREATE", object: "ref_tri_helper", depends: [], explanation: "" },
        { step_index: 2, action: "CREATE", object: "cut_plane_z2", depends: [], explanation: "" },
        { step_index: 3, action: "CREATE", object: "true_cut_poly", depends: [], explanation: "" },
      ],
    };

    const helperSem = classifySceneObjectSemantics(syntheticScene, syntheticScene.objects[5], 3, null);
    const resultSem = classifySceneObjectSemantics(syntheticScene, syntheticScene.objects[7], 3, null);
    expect(resultSem.role).toBe("RESULT_SECTION");
    expect(resultSem.fillColor).toBe(0xc85a32);
    expect(helperSem.epistemicStatus).toBe("auxiliary");
    expect(helperSem.fillColor).toBe(0x0f766e);

    const coneScene = sceneOf("non-thiet-dien-truc");
    const td = coneScene.objects.find((o) => o.id === "td")!;
    const tdSem = classifySceneObjectSemantics(coneScene, td, coneScene.events.length - 1, null);
    expect(tdSem.role).toBe("RESULT_SECTION");
    expect(tdSem.epistemicStatus).toBe("constructed_result");
    expect(tdSem.fillColor).toBe(0xc85a32);
    expect(tdSem.strokeColor).toBe(0xc85a32);

    // Hovering or selecting SAB MUST preserve its RESULT_SECTION terracotta hue (never turning teal 0x0f766e or cobalt 0x2563eb)
    const tdHover = classifySceneObjectSemantics(coneScene, td, coneScene.events.length - 1, null, "td");
    expect(tdHover.role).toBe("RESULT_SECTION");
    expect(tdHover.fillColor).toBe(0xc85a32);
    expect(tdHover.strokeColor).not.toBe(0x0f766e);
    expect(tdHover.strokeColor).not.toBe(0x2563eb);
    expect(hueDistanceDeg(tdHover.strokeColor, 0xc85a32)).toBeLessThan(2);

    const tdSelected = classifySceneObjectSemantics(coneScene, td, coneScene.events.length - 1, "td", null);
    expect(tdSelected.role).toBe("RESULT_SECTION");
    expect(tdSelected.fillColor).toBe(0xc85a32);
    expect(tdSelected.strokeColor).not.toBe(0x0f766e);
    expect(tdSelected.strokeColor).not.toBe(0x2563eb);
    expect(hueDistanceDeg(tdSelected.strokeColor, 0xc85a32)).toBeLessThan(2);
  });

  it("preserves semantic mathematical hue on hover, click/selection, and background context across all colored geometric roles", () => {
    const paletteRoles = [0xc85a32, 0xd97706, 0x2563eb, 0x6d28d9, 0x0f766e, 0x1e293b];
    for (const baseHex of paletteRoles) {
      for (const state of ["neutral", "hover", "selected", "context"] as const) {
        const modulated = modulateSemanticColor(baseHex, state);
        expect(hueDistanceDeg(modulated, baseHex)).toBeLessThan(2);
      }
    }
  });
});

describe("Inscribed & Circumscribed Circles and Spheres — 5 Distinct Sphere Roles & Contextual Circle Occlusion", () => {
  it("classifies and renders base inscribed (#D97706) and circumscribed (#2563EB) circles with exact camera occlusion and zero fake spheres", () => {
    const circleScene = structuredClone(inCircumFixtures.base_circles_square_pyramid.scene3d) as unknown as Scene3D;
    const chop = circleScene.objects.find((o) => o.id === "chop")!;
    const cIn = circleScene.objects.find((o) => o.id === "c_in")!;
    const cOut = circleScene.objects.find((o) => o.id === "c_out")!;
    const pts = circleScene.objects.filter((o) => o.xyz).map((o) => toVec3(o.xyz!));

    expect(classifyCircleSemanticRole(circleScene, cIn)).toBe("INSCRIBED_CIRCLE");
    expect(classifyCircleSemanticRole(circleScene, cOut)).toBe("CIRCUMSCRIBED_CIRCLE");

    const root = new THREE.Group();
    const builtSolid = buildObject3D(chop, false, undefined, pts, undefined, undefined, undefined, false, "primary", true, true, false, circleScene)!;
    const builtIn = buildObject3D(cIn, false, undefined, pts, undefined, undefined, undefined, false, "primary", true, true, false, circleScene)!;
    const builtOut = buildObject3D(cOut, false, undefined, pts, undefined, undefined, undefined, false, "primary", true, true, false, circleScene)!;
    root.add(builtSolid, builtIn, builtOut);

    // Neither circle spawns any sphere geometry or silhouette
    let hasSphereGeo = false;
    for (const node of [builtIn, builtOut]) {
      node.traverse((ch) => {
        if (ch.name.startsWith("sphere_silhouette:") || ch.name.startsWith("sphere_reference:")) hasSphereGeo = true;
      });
    }
    expect(hasSphereGeo).toBe(false);

    // Inscribed circle has amber #D97706 stroke & subtle 0.08 fill; Circumscribed circle has cobalt #2563EB stroke & NO fill
    const inRim = builtIn.userData.curvedRimLoop;
    const outRim = builtOut.userData.curvedRimLoop;
    expect((inRim.thayMesh.material as THREE.MeshBasicMaterial).color.getHex()).toBe(0xd97706);
    const inFill = builtIn.children.find((c) => c.name.endsWith(":c_in")) as THREE.Mesh | undefined;
    expect(inFill).toBeDefined();
    expect((inFill!.material as THREE.MeshBasicMaterial).color.getHex()).toBe(0xd97706);
    expect((inFill!.material as THREE.MeshBasicMaterial).opacity).toBeCloseTo(0.08, 3);

    expect((outRim.thayMesh.material as THREE.MeshBasicMaterial).color.getHex()).toBe(0x2563eb);
    const outFill = builtOut.children.find((c) => c.name.endsWith(":c_out"));
    expect(outFill).toBeUndefined();

    // Camera ABOVE pyramid (z = 6): inscribed circle on bottom base is occluded (dashed), while circumscribed circle has BOTH visible outer arcs and hidden inner arcs!
    const camAbove = new THREE.PerspectiveCamera(45, 16 / 10, 0.1, 200);
    camAbove.up.set(0, 0, 1);
    camAbove.position.set(7, -6, 5);
    camAbove.lookAt(0, 0, 1);
    camAbove.updateMatrixWorld();
    updateCanonicalEdgeVisibility(root, camAbove);

    expect(inRim.thayNet.geometry.drawRange.count).toBe(0);
    expect(inRim.khuatNet.geometry.drawRange.count).toBeGreaterThan(0);
    expect(outRim.thayNet.geometry.drawRange.count).toBeGreaterThan(0);
    expect(outRim.khuatNet.geometry.drawRange.count).toBeGreaterThan(0);

    // Camera BELOW pyramid base (z = -6): base faces camera directly -> inscribed circle becomes visible solid!
    const camBelow = new THREE.PerspectiveCamera(45, 16 / 10, 0.1, 200);
    camBelow.up.set(0, 0, 1);
    camBelow.position.set(5, -5, -6);
    camBelow.lookAt(0, 0, 0);
    camBelow.updateMatrixWorld();
    updateCanonicalEdgeVisibility(root, camBelow);

    expect(inRim.thayNet.geometry.drawRange.count).toBeGreaterThan(0);
    expect(inRim.khuatNet.geometry.drawRange.count).toBe(0);

    // Hover & selection preserve amber (#D97706) and cobalt (#2563EB) hues
    const builtInHover = buildObject3D(cIn, "hover", undefined, pts, undefined, undefined, undefined, false, "primary", true, true, false, circleScene)!;
    const builtOutSel = buildObject3D(cOut, "dich", undefined, pts, undefined, undefined, undefined, false, "primary", true, true, false, circleScene)!;
    expect(hueDistanceDeg((builtInHover.userData.curvedRimLoop.thayMesh.material as THREE.MeshBasicMaterial).color.getHex(), 0xd97706)).toBeLessThan(2);
    expect(hueDistanceDeg((builtOutSel.userData.curvedRimLoop.thayMesh.material as THREE.MeshBasicMaterial).color.getHex(), 0x2563eb)).toBeLessThan(2);
  });

  it("distinguishes all 5 sphere-related roles: standalone sphere, inscribed sphere, circumscribed sphere, non-authoritative equator, and plane-sphere section circle", () => {
    // 1 & 4. Standalone sphere (cau-the-tich): neutral shell #7C8B9E (opacity 0.12 per matphang.html), NO artificial black silhouette stroke, + non-authoritative equator
    const standaloneScene = sceneOf("cau-the-tich");
    const standaloneBall = standaloneScene.objects.find((o) => o.id === "cau")!;
    expect(classifySphereSemanticRole(standaloneScene, standaloneBall)).toBe("STANDALONE_SPHERE");
    const builtStandalone = buildObject3D(standaloneBall, false, undefined, [], undefined, undefined, undefined, false, "primary", true, true, false, standaloneScene)!;
    expect(builtStandalone.getObjectByName("sphere_silhouette:cau")).toBeUndefined();
    const shellStandalone = builtStandalone.children.find((c) => (c as THREE.Mesh).isMesh && c.userData?.voKhoi) as THREE.Mesh;
    expect((shellStandalone.material as THREE.MeshBasicMaterial).color.getHex()).toBe(0x7c8b9e);
    expect((shellStandalone.material as THREE.MeshBasicMaterial).opacity).toBeCloseTo(0.12, 3);
    const eqStandalone = builtStandalone.getObjectByName("sphere_reference:cau")!;
    expect(eqStandalone).toBeDefined();
    expect(eqStandalone.userData.presentationReference?.authoritative).toBe(false);
    expect(standaloneScene.free_objects).not.toContain("sphere_reference:cau");

    // 2. Inscribed sphere (insphere_square_pyramid): amber shell #D97706, NO black silhouette, ALL-DASHED amber equator
    const inSphereScene = structuredClone(inCircumFixtures.insphere_square_pyramid.scene3d) as unknown as Scene3D;
    const chopIn = inSphereScene.objects.find((o) => o.id === "chop")!;
    const cauNoi = inSphereScene.objects.find((o) => o.id === "cau_noi")!;
    expect(classifySphereSemanticRole(inSphereScene, cauNoi)).toBe("INSCRIBED_SPHERE");

    const rootIn = new THREE.Group();
    const builtChopIn = buildObject3D(chopIn, false, undefined, [], undefined, undefined, undefined, false, "primary", true, true, false, inSphereScene)!;
    const builtCauNoi = buildObject3D(cauNoi, false, undefined, [], undefined, undefined, undefined, false, "primary", true, true, false, inSphereScene)!;
    rootIn.add(builtChopIn, builtCauNoi);

    expect(builtCauNoi.getObjectByName("sphere_silhouette:cau_noi")).toBeUndefined();
    const shellIn = builtCauNoi.children.find((c) => (c as THREE.Mesh).isMesh && c.userData?.voKhoi) as THREE.Mesh;
    expect((shellIn.material as THREE.MeshBasicMaterial).color.getHex()).toBe(0xd97706);
    expect((shellIn.material as THREE.MeshBasicMaterial).opacity).toBeCloseTo(0.16, 2);

    const cam = new THREE.PerspectiveCamera(45, 16 / 10, 0.1, 200);
    cam.up.set(0, 0, 1);
    cam.position.set(8, -7, 5);
    cam.lookAt(0, 0, 1.5);
    cam.updateMatrixWorld();
    updateCanonicalEdgeVisibility(rootIn, cam);

    const eqIn = builtCauNoi.getObjectByName("sphere_reference:cau_noi")!;
    expect(eqIn).toBeDefined();
    const eqInRim = eqIn.userData.curvedRimLoop;
    expect((eqInRim.khuatMesh.material as THREE.MeshBasicMaterial).color.getHex()).toBe(0xd97706);
    expect(eqInRim.thayNet.geometry.drawRange.count).toBe(0);
    expect(eqInRim.khuatNet.geometry.drawRange.count).toBeGreaterThan(0);

    // 3. Circumscribed sphere (scene3d-circumsphere-fixture.json): teal shell #0F766E, NO black silhouette, front-solid/back-dashed teal equator, non-occluding so OABC has visible edges
    const circumScene = structuredClone(circumFixture) as unknown as Scene3D;
    const oabc = circumScene.objects.find((o) => o.id === "OABC")!;
    const circumBall = circumScene.objects.find((o) => o.id === "circumsphere")!;
    expect(classifySphereSemanticRole(circumScene, circumBall)).toBe("CIRCUMSCRIBED_SPHERE");

    const rootOut = new THREE.Group();
    const builtCircum = buildObject3D(circumBall, false, undefined, [], undefined, undefined, undefined, false, "primary", true, true, false, circumScene)!;
    const builtOabc = buildObject3D(oabc, false, undefined, [], undefined, undefined, undefined, false, "primary", true, true, false, circumScene)!;
    // Add circumsphere FIRST to prove non-occlusion does not depend on object array order!
    rootOut.add(builtCircum, builtOabc);

    expect(builtCircum.getObjectByName("sphere_silhouette:circumsphere")).toBeUndefined();
    const shellOut = builtCircum.children.find((c) => (c as THREE.Mesh).isMesh && c.userData?.voKhoi) as THREE.Mesh;
    expect((shellOut.material as THREE.MeshBasicMaterial).color.getHex()).toBe(0x0f766e);
    expect((shellOut.material as THREE.MeshBasicMaterial).opacity).toBeCloseTo(0.085, 2);

    const auditOut = updateCanonicalEdgeVisibility(rootOut, cam);
    expect(auditOut.visible_edge_ids.length).toBeGreaterThan(0);
    const eqOut = builtCircum.getObjectByName("sphere_reference:circumsphere")!;
    const eqOutRim = eqOut.userData.curvedRimLoop;
    expect((eqOutRim.thayMesh.material as THREE.MeshBasicMaterial).color.getHex()).toBe(0x0f766e);
    expect(eqOutRim.thayNet.geometry.drawRange.count).toBeGreaterThan(0);
    expect(eqOutRim.khuatNet.geometry.drawRange.count).toBeGreaterThan(0);

    // 5. Plane-sphere intersection circle (cau-cat-mat-phang): RESULT_SECTION terracotta #C85A32
    const sphereCutScene = sceneOf("cau-cat-mat-phang");
    const cutCircle = sphereCutScene.objects.find((o) => o.id === "C")!;
    expect(classifyCircleSemanticRole(sphereCutScene, cutCircle)).toBe("RESULT_SECTION");
    const builtCut = buildObject3D(cutCircle, false, undefined, [], undefined, undefined, undefined, false, "primary", true, true, false, sphereCutScene)!;
    const cutFill = builtCut.getObjectByName("section_fill:C") as THREE.Mesh;
    expect((cutFill.material as THREE.MeshBasicMaterial).color.getHex()).toBe(0xc85a32);
    expect((builtCut.userData.curvedRimLoop.thayMesh.material as THREE.MeshBasicMaterial).color.getHex()).toBe(0xc85a32);
  });

  it("renders a two-pass 3D volumetric sphere shell with deterministic renderOrder and camera-space grazing shader while leaving cones/cylinders untouched", () => {
    const standaloneScene = sceneOf("cau-the-tich");
    const standaloneBall = standaloneScene.objects.find((o) => o.id === "cau")!;
    const builtStandalone = buildObject3D(standaloneBall, false, undefined, [], undefined, undefined, undefined, false, "primary", true, true, false, standaloneScene)!;

    const shellsStandalone = builtStandalone.children.filter((c) => (c as THREE.Mesh).isMesh && c.userData?.voKhoi) as THREE.Mesh[];
    expect(shellsStandalone).toHaveLength(2);
    const [frontSt, backSt] = shellsStandalone;
    const frontMat = frontSt.material as THREE.MeshBasicMaterial;
    const backMat = backSt.material as THREE.MeshBasicMaterial;
    expect(frontMat.side).toBe(THREE.FrontSide);
    expect(backMat.side).toBe(THREE.BackSide);
    expect(backSt.userData.voKhoiMatSau).toBe(true);
    expect(frontMat.color.getHex()).toBe(0x7c8b9e);
    expect(backMat.color.getHex()).toBe(0x7c8b9e);
    expect(frontMat.opacity).toBeCloseTo(0.12, 3);
    expect(backSt.userData.baseShellOpacity).toBeCloseTo(0.12 * PHONG_CACH_SCENE3D.opacity.shellBackRatio, 3);
    expect(frontMat.depthWrite).toBe(false);
    expect(frontMat.depthTest).toBe(false);
    expect(backMat.depthWrite).toBe(false);
    expect(backMat.depthTest).toBe(false);
    expect(backSt.renderOrder).toBe(-1);
    expect(frontSt.renderOrder).toBe(0);
    expect(frontMat.customProgramCacheKey()).toBe("axo-sphere-airy-front-v2");
    expect(backMat.customProgramCacheKey()).toBe("axo-sphere-airy-back-v2");

    const mockShader = {
      uniforms: {},
      vertexShader: "#include <common>\nvoid main() {\n#include <beginnormal_vertex>\n#include <defaultnormal_vertex>\n#include <begin_vertex>\n#include <project_vertex>\n}",
      fragmentShader: "#include <common>\nvoid main() {\nvec4 diffuseColor = vec4(diffuse, opacity);\nvec3 outgoingLight = diffuseColor.rgb;\n#include <opaque_fragment>\n}",
    };
    frontMat.onBeforeCompile(mockShader as any, {} as any);
    expect(mockShader.vertexShader).toContain("vSphereViewNormal");
    expect(mockShader.fragmentShader).toContain("vSphereViewDir");
    // Must NEVER apply directional key-light / wrap shadow darkening that turns the sphere dark grey/heavy
    expect(mockShader.fragmentShader).not.toContain("spKey");
    expect(mockShader.fragmentShader).not.toContain("spShade");
    expect(mockShader.fragmentShader).not.toContain("spCrescent");
    expect(mockShader.fragmentShader).not.toContain("outgoingLight *=");
    expect(mockShader.fragmentShader).toContain("0.28");

    const mockBackShader = {
      uniforms: {},
      vertexShader: "#include <common>\nvoid main() {\n#include <beginnormal_vertex>\n#include <defaultnormal_vertex>\n#include <begin_vertex>\n#include <project_vertex>\n}",
      fragmentShader: "#include <common>\nvoid main() {\nvec4 diffuseColor = vec4(diffuse, opacity);\nvec3 outgoingLight = diffuseColor.rgb;\n#include <opaque_fragment>\n}",
    };
    backMat.onBeforeCompile(mockBackShader as any, {} as any);
    expect(mockBackShader.fragmentShader).not.toContain("outgoingLight *=");
    expect(mockBackShader.fragmentShader).toContain("0.20");

    // Selection gently increases shell opacity (0.12 -> 0.20) while preserving exact #7C8B9E semantic color, and deselect restores 0.12
    const builtSelected = buildObject3D(standaloneBall, "dich", undefined, [], undefined, undefined, undefined, false, "primary", true, true, false, standaloneScene)!;
    const selFront = builtSelected.children.find((c) => (c as THREE.Mesh).isMesh && c.userData?.voKhoi && !c.userData?.voKhoiMatSau) as THREE.Mesh;
    expect((selFront.material as THREE.MeshBasicMaterial).color.getHex()).toBe(0x7c8b9e);
    expect((selFront.material as THREE.MeshBasicMaterial).opacity).toBeCloseTo(0.20, 3);
    const builtRestored = buildObject3D(standaloneBall, false, undefined, [], undefined, undefined, undefined, false, "primary", true, true, false, standaloneScene)!;
    const resFront = builtRestored.children.find((c) => (c as THREE.Mesh).isMesh && c.userData?.voKhoi && !c.userData?.voKhoiMatSau) as THREE.Mesh;
    expect((resFront.material as THREE.MeshBasicMaterial).opacity).toBeCloseTo(0.12, 3);

    // 3D reference equator screen width stays crisp (> 2.0px @720p) yet strictly thinner than auxiliary and solid edge
    const eqFatGroup = new THREE.Group();
    dongBoNetDayManHinh([builtStandalone], eqFatGroup, 1280, 720, true);
    const eqVisibleLine = eqFatGroup.children.find((c) => c.visible && c.name.includes("sphere_reference:") && c.name.endsWith(":thay")) as unknown as {
      material: { linewidth: number };
    };
    expect(eqVisibleLine.material.linewidth).toBeGreaterThan(2.0);
    expect(eqVisibleLine.material.linewidth).toBeLessThan(PHONG_CACH_SCENE3D.fatPx.auxiliary);

    // Inscribed & circumscribed spheres use deterministic non-conflicting renderOrders behind sections (7) and lines (8)
    const inSphereScene = structuredClone(inCircumFixtures.insphere_square_pyramid.scene3d) as unknown as Scene3D;
    const cauNoi = inSphereScene.objects.find((o) => o.id === "cau_noi")!;
    const shellsIn = buildObject3D(cauNoi, false, undefined, [], undefined, undefined, undefined, false, "primary", true, true, false, inSphereScene)!
      .children.filter((c) => (c as THREE.Mesh).isMesh && c.userData?.voKhoi) as THREE.Mesh[];
    expect(shellsIn).toHaveLength(2);
    expect(shellsIn[1].renderOrder).toBeCloseTo(-0.6, 5);
    expect(shellsIn[0].renderOrder).toBeCloseTo(-0.4, 5);

    const circumScene = structuredClone(circumFixture) as unknown as Scene3D;
    const circumBall = circumScene.objects.find((o) => o.id === "circumsphere")!;
    const shellsOut = buildObject3D(circumBall, false, undefined, [], undefined, undefined, undefined, false, "primary", true, true, false, circumScene)!
      .children.filter((c) => (c as THREE.Mesh).isMesh && c.userData?.voKhoi) as THREE.Mesh[];
    expect(shellsOut).toHaveLength(2);
    expect(shellsOut[1].renderOrder).toBeCloseTo(-1.5, 5);
    expect(shellsOut[0].renderOrder).toBeCloseTo(0.5, 5);

    // Non-sphere curved solids (cone) stay untouched: 1 DoubleSide shell + dynamic curved_silhouette
    const coneScene = sceneOf("non-thiet-dien-truc");
    const coneObj = coneScene.objects.find((o) => o.id === "non")!;
    const builtCone = buildObject3D(coneObj, false, undefined, [], undefined, undefined, undefined, false, "primary", true, true, false, coneScene)!;
    const coneShells = builtCone.children.filter((c) => (c as THREE.Mesh).isMesh && c.userData?.voKhoi) as THREE.Mesh[];
    expect(coneShells).toHaveLength(1);
    expect((coneShells[0].material as THREE.MeshBasicMaterial).side).toBe(THREE.DoubleSide);
    expect(builtCone.getObjectByName("curved_silhouette:non")).toBeDefined();
  });

  it("handles degenerate or incomplete circle/sphere inputs safely without fabricating geometry", () => {
    const emptyScene: Scene3D = { free_objects: [], objects: [], events: [] };
    const zeroRadiusCircle: SceneObject = {
      id: "bad_c",
      label: "Degenerate circle",
      type: "circle3",
      render: "circle",
      origin: "derived",
      producer: null,
      depends: [],
      center: ["0", "0", "0"],
      normal: ["0", "0", "1"],
      radius_sq: "0",
    };
    const missingCenterCircle: SceneObject = {
      id: "no_center",
      label: "Missing center",
      type: "circle3",
      render: "circle",
      origin: "derived",
      producer: null,
      depends: [],
      normal: ["0", "0", "1"],
      radius_sq: "4",
    };
    expect(buildObject3D(zeroRadiusCircle, false, undefined, [], undefined, undefined, undefined, false, "primary", true, true, false, emptyScene)).toBeNull();
    expect(buildObject3D(missingCenterCircle, false, undefined, [], undefined, undefined, undefined, false, "primary", true, true, false, emptyScene)).toBeNull();
  });
});

describe("Unified Semantic Plane & Section Default Policy (3-Mode UI Removed)", () => {
  it("distinguishes construction-tool planes, spatial-relation sphere planes, mandatory studied planes, and duplicate base planes under one unified default policy", () => {
    // 1. Pyramid cut by (MNP): cutting plane visible during construction (0.92) and subtly retained at completed final frame (0.68, matching HTML V2.7) while spotlighting section
    const chop = sceneOf("thiet-dien-chop");
    const mpChop = chop.objects.find((o) => o.id === "mp")!;
    const mpCreateStep = chop.formation!.steps.findIndex((s) => s.visible_ids.includes("mp"));
    const chopFinalStep = chop.formation!.steps.length - 1;

    const createDecision = resolvePlaneSectionVisibility(chop, mpChop, mpCreateStep, false, null);
    const finalDecision = resolvePlaneSectionVisibility(chop, mpChop, chopFinalStep, false, null);
    expect(createDecision.visible).toBe(true);
    expect(createDecision.opacityScale).toBe(1);
    expect(finalDecision.visible).toBe(false);
    expect(finalDecision.opacityScale).toBe(0);
    expect(resolvePlaneSectionVisibility(chop, mpChop, chopFinalStep, true, null).visible).toBe(true);
    expect(resolvePlaneSectionVisibility(chop, mpChop, chopFinalStep, false, "mp").opacityScale).toBe(1);

    // 2. Sphere cut by plane (cau-cat-mat-phang): softens plane (P) to SUPPORT when circle C is completed
    const sphereCut = sceneOf("cau-cat-mat-phang");
    const mpSphere = sphereCut.objects.find((o) => o.id === "P")!;
    const sphereFinal = sphereCut.formation!.steps.length - 1;
    const spherePlaneDecision = resolvePlaneSectionVisibility(sphereCut, mpSphere, sphereFinal, false, null);
    expect(spherePlaneDecision.visible).toBe(true);
    expect(spherePlaneDecision.opacityScale).toBeLessThan(0.5);

    // 3. Mandatory studied plane (mp-vuong-goc-duong): mpb = (α) stays visible while duplicate solid base `day = (ABCD)` hides!
    const mpPerp = sceneOf("mp-vuong-goc-duong");
    const mpb = mpPerp.objects.find((o) => o.id === "mpb")!;
    const day = mpPerp.objects.find((o) => o.id === "day")!;
    const perpFinal = mpPerp.formation!.steps.length - 1;
    expect(resolvePlaneSectionVisibility(mpPerp, mpb, perpFinal, false, null).visible).toBe(true);
    expect(resolvePlaneSectionVisibility(mpPerp, day, perpFinal, false, null).visible).toBe(false);

    const compactPts = compactPlaneAnchorPoints(mpPerp, mpb, mpPerp.objects);
    expect(compactPts.length).toBeGreaterThanOrEqual(3);
    const spanCompact = Math.max(
      ...compactPts.flatMap((a) => compactPts.map((b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]))),
    );
    expect(spanCompact).toBeLessThan(4.3);
  });

  it("removes the 3-mode plane/section selector from AxoWorkspaceV62 while preserving all V2.7 display toggles", () => {
    const sample = sampleById("thiet-dien-chop");
    const scene = withSubEntities(veKhongGian(sample.envelope.scene3d));
    const finalAnchor = anchorOfGeometryStep(scene, Math.max(0, geometryStepCount(scene) - 1));
    const html = renderToString(
      <AxoWorkspaceV62
        scene={scene}
        de={sample.envelope.description}
        tieuDe={sample.title}
        initialStep={finalAnchor}
      />,
    );
    expect(html).not.toContain('id="tb-plane-section-mode"');
    expect(html).not.toContain('id="btn-ps-mode-auto"');
    expect(html).not.toContain('id="btn-ps-mode-plane"');
    expect(html).not.toContain('id="btn-ps-mode-section"');
    for (const id of ["chk-shell", "chk-labels", "chk-plane", "chk-section", "chk-aux", "chk-axes", "chk-grid", "btn-reset-display-opts"]) {
      expect(html).toContain(`id="${id}"`);
    }
    expect(html).toMatch(/id="chk-aux"(?![^>]*checked)/);
  });
});

describe("Pedagogical Camera Selection & Focus Surface Openness", () => {
  it("opens axial cone section SAB broadside (|n·d| >= 0.72) instead of near-edge-on baseline (0.33)", () => {
    const cone = sceneOf("non-thiet-dien-truc");
    const ct = cauTrucSuPham(cone.objects);
    const dir = new THREE.Vector3(...chonHuongNhin(ct.diem, ct.canh, ct.mat, ct.tuyChon)).normalize();
    const openness = Math.abs(dir.y);
    expect(openness).toBeGreaterThanOrEqual(0.72);
  });

  it("opens diagonal pyramid section (SAC) in mat-cheo-sac (|n·d| >= 0.55) instead of foreshortened sliver", () => {
    const diag = sceneOf("mat-cheo-sac");
    const ct = cauTrucSuPham(diag.objects);
    const dir = new THREE.Vector3(...chonHuongNhin(ct.diem, ct.canh, ct.mat, ct.tuyChon)).normalize();
    const nSAC = new THREE.Vector3(1, -1, 0).normalize();
    expect(Math.abs(dir.dot(nSAC))).toBeGreaterThanOrEqual(0.55);
  });

  it("orients cone generator scene non-duong-sinh so S-O-A profile triangle is wide open (|n·d| >= 0.65)", () => {
    const gen = sceneOf("non-duong-sinh");
    const ct = cauTrucSuPham(gen.objects);
    const dir = new THREE.Vector3(...chonHuongNhin(ct.diem, ct.canh, ct.mat, ct.tuyChon)).normalize();
    expect(Math.abs(dir.y)).toBeGreaterThanOrEqual(0.65);
  });

  it("prevents perspective grazing on prism/cuboid top caps and oblique cylinder caps", () => {
    const fixDir = path.resolve(
      __dirname,
      "../../../../../docs/evaluation/geometry/runs/visual-closure-hybrid-readiness/visual/final-inputs/fixtures",
    );
    const prismScene = JSON.parse(fs.readFileSync(path.join(fixDir, "triangular_prism_positive.json"), "utf8")).envelope
      .scene3d as Scene3D;
    const cuboidScene = JSON.parse(fs.readFileSync(path.join(fixDir, "cuboid_positive.json"), "utf8")).envelope
      .scene3d as Scene3D;
    for (const sc of [prismScene, cuboidScene]) {
      const ct = cauTrucSuPham(sc.objects);
      const dir = new THREE.Vector3(...chonHuongNhin(ct.diem, ct.canh, ct.mat, ct.tuyChon)).normalize();
      expect(dir.z).toBeGreaterThanOrEqual(0.40);
    }
    const obliqueCyl = sceneOf("tru-truc-xien");
    const ctCyl = cauTrucSuPham(obliqueCyl.objects);
    const dirCyl = new THREE.Vector3(...chonHuongNhin(ctCyl.diem, ctCyl.canh, ctCyl.mat, ctCyl.tuyChon)).normalize();
    expect(ctCyl.tuyChon.capDayTru?.length).toBe(1);
    const [c0, c1] = ctCyl.tuyChon.capDayTru![0];
    const axis = new THREE.Vector3(c1[0] - c0[0], c1[1] - c0[1], c1[2] - c0[2]).normalize();
    expect(Math.abs(dirCyl.dot(axis))).toBeGreaterThanOrEqual(0.25);
  });
});

describe("Curved Reference Geometry, Section Vertex Badges, Hover/Selection Stroke Hierarchy & GIVEN Preservation", () => {
  it("marks vertices of section-role polygon3 (non-thiet-dien-truc SAB) without marking parent solid faces or mutating GIVEN origins", () => {
    const cone = sceneOf("non-thiet-dien-truc");
    const freeBefore = cone.objects.filter((o) => o.origin === "free").map((o) => o.id);
    const coneSectionVerts = diemTaiDinhThietDien(cone);
    expect([...coneSectionVerts].sort()).toEqual(["A", "B", "S"]);
    expect(cone.objects.filter((o) => o.origin === "free").map((o) => o.id)).toEqual(freeBefore);

    const circum = circumFixture as unknown as Scene3D;
    expect([...diemTaiDinhThietDien(circum)]).toEqual([]);
  });

  it("builds contract-grounded non-authoritative cone/sphere/circle references without mutating scene data or inventing right angles", () => {
    const coneGen = sceneOf("non-duong-sinh");
    const snapshotBefore = JSON.stringify(coneGen);
    const refGroup = buildContractReferenceGroup(coneGen, coneGen.objects, coneGen.events.length - 1);
    expect(refGroup).not.toBeNull();

    const names: string[] = [];
    let hasFakePerp = false;
    refGroup!.traverse((node) => {
      if (node.name) names.push(node.name);
      if (node.userData?.gocVuongDonVi || node.userData?.perpMarker) hasFakePerp = true;
    });
    expect(names.some((n) => n.startsWith("curved_axis:"))).toBe(true);
    expect(names.some((n) => n.startsWith("curved_radius:"))).toBe(true);
    // `doan_SA` is already an authoritative segment in `non-duong-sinh`, so `buildContractReferenceGroup` avoids duplicating it;
    // when no segment covers S-A, `quantity_span:l` provides the fallback reference segment.
    expect(names.some((n) => n.startsWith("quantity_span:"))).toBe(false);
    const withoutDoanSa = coneGen.objects.filter((o) => o.id !== "doan_SA");
    const fallbackGroup = buildContractReferenceGroup({ objects: withoutDoanSa }, withoutDoanSa, coneGen.events.length - 1)!;
    const fallbackNames: string[] = [];
    fallbackGroup.traverse((node) => {
      if (node.name) fallbackNames.push(node.name);
    });
    expect(fallbackNames.some((n) => n.startsWith("quantity_span:"))).toBe(true);
    expect(hasFakePerp).toBe(false);
    expect(JSON.stringify(coneGen)).toBe(snapshotBefore);
  });

  it("enforces stroke width hierarchy (selected section > hovered section > neutral section > solid edge > auxiliary line) without semantic recoloring", () => {
    const chop = sceneOf("thiet-dien-chop");
    const solid = chop.objects.find((o) => o.type === "solid")!;
    const sec = chop.objects.find((o) => o.type === "section")!;
    const auxLine: SceneObject = {
      id: "helper_l",
      label: "d",
      type: "line3",
      render: "line",
      origin: "derived",
      producer: "construct_line",
      formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
      display_group: ["construction"],
      depends: ["A", "C"],
      point: ["0", "0", "0"],
      direction: ["1", "1", "0"],
    };
    const pts = chop.objects.filter((o) => o.xyz).map((o) => toVec3(o.xyz!));

    const measureSectionWidthAndColor = (emphasis: false | "hover" | "dich") => {
      const root = new THREE.Group();
      root.add(
        buildObject3D(solid, false, undefined, pts)!,
        buildObject3D(sec, emphasis, undefined, pts)!,
        buildObject3D(auxLine, false, undefined, pts)!,
      );
      const fatGroup = new THREE.Group();
      dongBoNetDayManHinh([root], fatGroup, 1440, 900, true);
      const fatSec = fatGroup.children.find((c) => c.visible && c.name.includes(`polygon_border:${sec.id}:thay`)) as unknown as {
        material: { linewidth: number; color: THREE.Color };
      };
      const fatSolid = fatGroup.children.find(
        (c) =>
          c.visible
          && !c.name.includes(sec.id)
          && !c.name.includes("helper_l")
          && (c as unknown as { material?: { dashed?: boolean } }).material?.dashed !== true,
      ) as unknown as {
        material: { linewidth: number };
      };
      const fatAux = fatGroup.children.find((c) => c.visible && c.name.includes("line:helper_l:thay")) as unknown as {
        material: { linewidth: number };
      };
      return {
        secWidth: fatSec.material.linewidth,
        secHex: fatSec.material.color.getHex(),
        solidWidth: fatSolid.material.linewidth,
        auxWidth: fatAux.material.linewidth,
      };
    };

    const neutral = measureSectionWidthAndColor(false);
    const hovered = measureSectionWidthAndColor("hover");
    const selected = measureSectionWidthAndColor("dich");

    expect(selected.secWidth).toBeGreaterThan(hovered.secWidth);
    expect(hovered.secWidth).toBeGreaterThan(neutral.secWidth);
    expect(neutral.secWidth).toBeGreaterThan(neutral.solidWidth);
    expect(neutral.solidWidth).toBeGreaterThan(neutral.auxWidth);

    // Zero semantic color swap across neutral, hover, and selected!
    expect(hueDistanceDeg(neutral.secHex, 0xc85a32)).toBeLessThan(2);
    expect(hueDistanceDeg(hovered.secHex, 0xc85a32)).toBeLessThan(2);
    expect(hueDistanceDeg(selected.secHex, 0xc85a32)).toBeLessThan(2);
  });

  it("preserves projection carrier line3 (construct_point.project_onto) when auxiliary toggle is OFF while hiding pure helper lines", () => {
    const projScene: Scene3D = {
      free_objects: ["A", "B", "D", "S"],
      objects: [
        { id: "A", label: "A", type: "point3", render: "point_marker", origin: "free", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", label: "B", type: "point3", render: "point_marker", origin: "free", depends: [], xyz: ["6", "0", "0"] },
        { id: "D", label: "D", type: "point3", render: "point_marker", origin: "free", depends: [], xyz: ["0", "6", "0"] },
        { id: "S", label: "S", type: "point3", render: "point_marker", origin: "free", depends: [], xyz: ["0", "0", "6"] },
        {
          id: "BD",
          label: "Đường thẳng BD",
          type: "line3",
          render: "line",
          origin: "derived",
          producer: "construct_line",
          formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
          display_group: ["construction"],
          depends: ["B", "D"],
          point: ["6", "0", "0"],
          direction: ["-6", "6", "0"],
        },
        {
          id: "H",
          label: "Hình chiếu H",
          type: "point3",
          render: "point_marker",
          origin: "derived",
          producer: "construct_point.project_onto",
          formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
          display_group: ["construction", "target"],
          depends: ["BD", "S"],
          xyz: ["3", "3", "0"],
        },
        {
          id: "helper_line",
          label: "Đường dựng phụ",
          type: "line3",
          render: "line",
          origin: "derived",
          producer: "construct_line",
          formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
          display_group: ["construction"],
          depends: ["A", "B"],
          point: ["0", "0", "0"],
          direction: ["6", "0", "0"],
        },
        {
          id: "M",
          label: "Điểm dựng từ đường phụ",
          type: "point3",
          render: "point_marker",
          origin: "derived",
          producer: "construct_point.intersect",
          display_group: ["construction"],
          depends: ["helper_line"],
          xyz: ["3", "0", "0"],
        },
      ] as unknown as SceneObject[],
      events: [
        { step_index: 0, action: "INIT", object: null, objects: ["A", "B", "D", "S"], depends: [], explanation: "" },
        { step_index: 1, action: "CREATE", object: "BD", depends: ["B", "D"], explanation: "" },
        { step_index: 2, action: "CREATE", object: "H", depends: ["BD", "S"], explanation: "" },
        { step_index: 3, action: "CREATE", object: "helper_line", depends: ["A", "B"], explanation: "" },
        { step_index: 4, action: "CREATE", object: "M", depends: ["helper_line"], explanation: "" },
        { step_index: 5, action: "CREATE", object: "H", depends: ["H", "S"], explanation: "" },
      ],
    };
    const hiddenFinal = auxiliaryHiddenAt(projScene, 5, false, null);
    expect(hiddenFinal.has("BD")).toBe(false);
    expect(hiddenFinal.has("helper_line")).toBe(true);
  });
});

describe("Regression: Cutting Plane Full-Penetration Across Solid Bounds (§5 & §12)", () => {
  it("pierces all 4 lateral edges of thiet-dien-chop at intermediate step BEFORE Q exists so illustrative plane never stops short", () => {
    const chop = sceneOf("thiet-dien-chop");
    const mpChop = chop.objects.find((o) => o.id === "mp")!;
    const mpCreateStep = chop.formation!.steps.findIndex((s) => s.visible_ids.includes("mp"));
    const visibleIds = new Set(chop.formation!.steps[mpCreateStep].visible_ids);
    expect(visibleIds.has("Q")).toBe(false);

    const visibleAtCreate = chop.objects.filter((o) => visibleIds.has(o.id));
    const pierces = planeSolidEdgeIntersections(mpChop, visibleAtCreate);
    expect(pierces.length).toBeGreaterThanOrEqual(4);

    const anchorPool = [
      ...visibleAtCreate.flatMap((o) => (o.xyz ? [toVec3(o.xyz)] : o.vertices ? o.vertices.map(toVec3) : [])),
      ...pierces,
    ];
    const p0 = toVec3(mpChop.point!);
    const n = toVec3(mpChop.normal!);
    const corePoly = daGiacMatPhang(p0, n, anchorPool);
    const extPoly = moRongDaGiacMatPhang(p0, n, anchorPool, corePoly);
    expect(extPoly).not.toBeNull();
    expect(extPoly!.length).toBeGreaterThanOrEqual(4);

    // Every pierced solid edge point (including Q on SD) must lie strictly inside the extended illustrative plane patch,
    // and the horizontal cutting plane patch on S.ABCD (base 2x2) must extend outside the pyramid's footprint like matphang.html!
    const cx = extPoly!.reduce((s, p) => s + p[0], 0) / extPoly!.length;
    const cy = extPoly!.reduce((s, p) => s + p[1], 0) / extPoly!.length;
    const cz = extPoly!.reduce((s, p) => s + p[2], 0) / extPoly!.length;
    const patchRadius = Math.max(...extPoly!.map((p) => Math.hypot(p[0] - cx, p[1] - cy, p[2] - cz)));
    for (const pt of pierces) {
      expect(Math.hypot(pt[0] - cx, pt[1] - cy, pt[2] - cz)).toBeLessThan(patchRadius);
    }
    const extXs = extPoly!.map((p) => p[0]);
    const extYs = extPoly!.map((p) => p[1]);
    expect(Math.max(...extXs) - Math.min(...extXs)).toBeGreaterThan(2.05);
    expect(Math.max(...extYs) - Math.min(...extYs)).toBeGreaterThan(2.05);
  });

  it("sizes cutting plane across full curved-solid diameter for oblique cylinder, horizontal cylinder, and sphere cuts at intermediate & final steps", () => {
    // 1. Oblique cylinder cut (p6_thiet_dien_elip_cua_hinh_tru: R = 5)
    const p6Path = path.resolve(
      __dirname,
      "../../../../../docs/evaluation/geometry/product-ui-result-rendering/fixtures/p6_thiet_dien_elip_cua_hinh_tru.json",
    );
    const p6Scene = JSON.parse(fs.readFileSync(p6Path, "utf8")).envelope.scene3d as Scene3D;
    const p6Plane = p6Scene.objects.find((o) => o.type === "plane3")!;
    const p6Cyl = p6Scene.objects.find((o) => o.type === "curved_solid")!;
    const p6R = Math.sqrt(toNumber(p6Cyl.radius_sq!));
    const p6MidObjs = objectsAt(p6Scene, 2); // intermediate step before ellipse is constructed
    for (const pool of [p6MidObjs, p6Scene.objects]) {
      const anchors = compactPlaneAnchorPoints(p6Scene, p6Plane, pool);
      expect(anchors.length).toBeGreaterThanOrEqual(4);
      const xs = anchors.map((p) => p[0]);
      const ys = anchors.map((p) => p[1]);
      expect(Math.min(...xs)).toBeLessThan(-p6R);
      expect(Math.max(...xs)).toBeGreaterThan(p6R);
      expect(Math.min(...ys)).toBeLessThan(-p6R);
      expect(Math.max(...ys)).toBeGreaterThan(p6R);
    }

    // 2. Perpendicular cylinder cut (tru-thiet-dien-tron) & sphere cut (cau-cat-mat-phang)
    for (const sampleId of ["tru-thiet-dien-tron", "cau-cat-mat-phang"] as const) {
      const sc = sceneOf(sampleId);
      const pl = sc.objects.find((o) => o.type === "plane3")!;
      const cs = sc.objects.find((o) => o.type === "curved_solid")!;
      const r = Math.sqrt(toNumber(cs.radius_sq!));
      const anchors = compactPlaneAnchorPoints(sc, pl, sc.objects);
      expect(anchors.length).toBeGreaterThanOrEqual(4);
      const xs = anchors.map((p) => p[0]);
      const ys = anchors.map((p) => p[1]);
      expect(Math.max(...xs) - Math.min(...xs)).toBeGreaterThan(2 * r * 1.10);
      expect(Math.max(...ys) - Math.min(...ys)).toBeGreaterThan(2 * r * 1.10);
    }
  });
});

describe("matphang.html Sphere Visual Parity: No Artificial Outer Stroke & 3D Reference Equator (§3)", () => {
  it("renders standalone and off-center plane-cut spheres with translucent shell + 3D reference equator and NO extra sphere_silhouette stroke, suppressing equator only when an explicit horizontal great circle coincides with it", () => {
    const standalone = sceneOf("cau-the-tich");
    const ballStandalone = standalone.objects.find((o) => o.type === "curved_solid" && o.curved_kind === "ball")!;
    expect(shouldShowSphereReferenceEquator(standalone, ballStandalone, false, standalone.objects)).toBe(true);
    expect(shouldShowSphereReferenceEquator(standalone, ballStandalone, true, standalone.objects)).toBe(true);

    const builtStandalone = buildObject3D(
      ballStandalone,
      false,
      undefined,
      [],
      undefined,
      undefined,
      undefined,
      false,
      "primary",
      false,
      shouldShowSphereReferenceEquator(standalone, ballStandalone, false, standalone.objects),
      false,
      standalone,
    )!;
    const childNames: string[] = [];
    let hasVoKhoi = false;
    builtStandalone.traverse((n) => {
      if (n.name) childNames.push(n.name);
      if ((n as THREE.Mesh).isMesh && n.userData?.voKhoi) hasVoKhoi = true;
    });
    expect(hasVoKhoi).toBe(true);
    expect(childNames.some((n) => n.startsWith("sphere_silhouette:"))).toBe(false);
    expect(childNames.some((n) => n.startsWith("sphere_reference:"))).toBe(true);

    // Off-center plane-cut sphere (cau-cat-mat-phang: center I=(0,0,0), R=5; section C at z=3, r=4):
    // matches matphang.html `mat_cau` Step 4 -> keeps horizontal slate equator at z=0 alongside terracotta section at z=3!
    const sphereCut = sceneOf("cau-cat-mat-phang");
    const ballCut = sphereCut.objects.find((o) => o.type === "curved_solid" && o.curved_kind === "ball")!;
    expect(shouldShowSphereReferenceEquator(sphereCut, ballCut, false, sphereCut.objects)).toBe(true);
    expect(shouldShowSphereReferenceEquator(sphereCut, ballCut, true, sphereCut.objects)).toBe(true);

    // Coincident horizontal great-circle cut (explicit circle3 at exact sphere center & horizontal normal):
    // switches reference great circle to an orthogonal plane so two circles never overlap on the exact same 3D curve!
    const greatCircleCut: Scene3D = {
      ...sphereCut,
      objects: sphereCut.objects.map((o) =>
        o.type === "circle3"
          ? { ...o, center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "25" }
          : o,
      ),
    };
    const ballGreatCut = greatCircleCut.objects.find((o) => o.type === "curved_solid" && o.curved_kind === "ball")!;
    expect(shouldShowSphereReferenceEquator(greatCircleCut, ballGreatCut, false, greatCircleCut.objects)).toBe(false);

    const insphereScene = (inCircumFixtures as unknown as { insphere_square_pyramid: { scene3d: Scene3D } })
      .insphere_square_pyramid.scene3d;
    const inBall = insphereScene.objects.find((o) => o.type === "curved_solid" && o.curved_kind === "ball")!;
    expect(shouldShowSphereReferenceEquator(insphereScene, inBall, false, insphereScene.objects)).toBe(true);

    const circumScene = circumFixture as unknown as Scene3D;
    const circumBall = circumScene.objects.find((o) => o.type === "curved_solid" && o.curved_kind === "ball")!;
    expect(shouldShowSphereReferenceEquator(circumScene, circumBall, false, circumScene.objects)).toBe(true);
  });
});

describe("Independent Step Highlight vs Selection Highlight & Semantic Hue Preservation (§8 & §12)", () => {
  it("separates Step Highlight transient entrance pulse from neutral steady state and respects reduced-motion (pulse = 0)", () => {
    const chop = sceneOf("thiet-dien-chop");
    const tl = geometryTimeline(chop);
    expect(tl.length).toBeGreaterThanOrEqual(4);

    // Step 1 (gIdx === 0) has no transient entrance targets
    const s0 = computeStepHighlightTargets(chop, tl[0].anchor);
    expect(s0.newIds.size).toBe(0);
    expect(s0.depIds.size).toBe(0);

    // Mid step where mp is created highlights mp as new and M, N, P as direct dependencies
    const mpGIdx = tl.findIndex((g) => objectsAt(chop, g.anchor).some((o) => o.id === "mp"));
    expect(mpGIdx).toBeGreaterThan(0);
    const sMid = computeStepHighlightTargets(chop, tl[mpGIdx].anchor);
    expect(sMid.newIds.has("mp")).toBe(true);
    for (const id of sMid.newIds) {
      expect(sMid.depIds.has(id)).toBe(false);
    }

    // Verify transient screen-space pulse boosts width on new > dep > neutral and settles to exact 1.00x at pulse = 0
    const sec = chop.objects.find((o) => o.type === "section")!;
    const pts = chop.objects.filter((o) => o.xyz).map((o) => toVec3(o.xyz!));
    const measureAtPulse = (role: "new" | "dep" | undefined, pulse: number) => {
      const root = new THREE.Group();
      const built = buildObject3D(sec, false, undefined, pts)!;
      if (role) built.userData.stepHighlightRole = role;
      root.add(built);
      const fatGroup = new THREE.Group();
      dongBoNetDayManHinh([root], fatGroup, 1440, 900, true, pulse);
      const line = fatGroup.children.find((c) => c.visible && c.name.includes(`polygon_border:${sec.id}:thay`)) as unknown as {
        material: { linewidth: number; color: THREE.Color };
      };
      return { width: line.material.linewidth, hex: line.material.color.getHex() };
    };

    const steady = measureAtPulse(undefined, 0);
    const pulseNew = measureAtPulse("new", 1);
    const pulseDep = measureAtPulse("dep", 1);
    const settledAfter650ms = measureAtPulse("new", 0);
    const sectionHex = Number.parseInt(SEMANTIC_ROLE_SPECS.RESULT_SECTION.colorHex.slice(1), 16);

    expect(pulseNew.width / steady.width).toBeCloseTo(1.24, 2);
    expect(pulseDep.width / steady.width).toBeCloseTo(1.11, 2);
    expect(settledAfter650ms.width).toBeCloseTo(steady.width, 6);
    expect(hueDistanceDeg(pulseNew.hex, sectionHex)).toBeLessThan(1.5);
  });

  it("preserves semantic hue (|Δhue| < 1.5°), keeps selection width ratio in [1.2, 1.4], and keeps hidden lines dashed", () => {
    const roleHexes = [
      SEMANTIC_ROLE_SPECS.RESULT_SECTION.colorHex,
      SEMANTIC_ROLE_SPECS.GEOMETRIC_PLANE.colorHex,
      SEMANTIC_ROLE_SPECS.CERTIFIED_RELATION_MARKER.colorHex,
      SEMANTIC_ROLE_SPECS.INSCRIBED_CIRCLE.colorHex,
      SEMANTIC_ROLE_SPECS.CIRCUMSCRIBED_CIRCLE.colorHex,
    ].map((h) => Number.parseInt(h.slice(1), 16));
    for (const baseHex of roleHexes) {
      expect(hueDistanceDeg(modulateSemanticColor(baseHex, "hover"), baseHex)).toBeLessThan(1.5);
      expect(hueDistanceDeg(modulateSemanticColor(baseHex, "selected"), baseHex)).toBeLessThan(1.5);
    }

    const chop = sceneOf("thiet-dien-chop");
    const solid = chop.objects.find((o) => o.type === "solid")!;
    const sec = chop.objects.find((o) => o.type === "section")!;
    const pts = chop.objects.filter((o) => o.xyz).map((o) => toVec3(o.xyz!));

    const run = (emp: false | "dich") => {
      const root = new THREE.Group();
      root.add(buildObject3D(solid, false, undefined, pts)!, buildObject3D(sec, emp, undefined, pts)!);
      const cam = new THREE.PerspectiveCamera(50, 1440 / 900, 0.1, 200);
      cam.up.set(0, 0, 1);
      cam.position.set(10, -11, 8);
      cam.lookAt(2, 2, 2);
      cam.updateMatrixWorld();
      updateCanonicalEdgeVisibility(root, cam, "1440x900@1");
      const fatGroup = new THREE.Group();
      dongBoNetDayManHinh([root], fatGroup, 1440, 900, true, 0);
      const secSpans = fatGroup.children.filter((c) => c.visible && c.name.includes(sec.id)) as unknown as {
        material: { linewidth: number; dashed: boolean };
      }[];
      const thay = secSpans.find((c) => !c.material.dashed)!;
      const khuat = secSpans.find((c) => c.material.dashed)!;
      return { thayW: thay.material.linewidth, khuatDashed: Boolean(khuat?.material.dashed) };
    };

    const n = run(false);
    const s = run("dich");
    const ratio = s.thayW / n.thayW;
    expect(ratio).toBeGreaterThanOrEqual(1.2);
    expect(ratio).toBeLessThanOrEqual(1.4);
    expect(s.khuatDashed).toBe(true);
  });
});

describe("Curve Hit-Testing Proxies, Overlap Priority & Camera Zoom Clamping (§8 & §9)", () => {
  it("attaches raycastable curve pick-rings on circle3 & ellipse3 without breaking datCoDauDinh and prioritizes specific hits", () => {
    expect(DICH_CANH_PX).toBe(10);
    expect(DICH_CANH_PX).toBeLessThan(DICH_DIEM_PX);
    expect(
      chonCuThe(
        ["solid_S", "mp_alpha", "face_ABCD", "circle_C", "seg_MN", "pt_M"],
        (id) =>
          ({
            solid_S: "solid",
            mp_alpha: "plane3",
            face_ABCD: "face",
            circle_C: "circle3",
            seg_MN: "segment3",
            pt_M: "point3",
          })[id],
      ),
    ).toBe("pt_M");
    expect(
      chonCuThe(["solid_S", "mp_alpha", "circle_C"], (id) => ({ solid_S: "curved_solid", mp_alpha: "plane3", circle_C: "circle3" })[id]),
    ).toBe("circle_C");

    const sphereCut = sceneOf("cau-cat-mat-phang");
    const circleC = sphereCut.objects.find((o) => o.id === "C")!;
    const builtCircle = buildObject3D(circleC, false, undefined, [], undefined, undefined, undefined, false, "primary", false, true, false, sphereCut)!;
    const names: string[] = [];
    builtCircle.traverse((n) => {
      if (n.name) names.push(n.name);
    });
    expect(names).toContain("circle:C:proxy");

    // datCoDauDinh must run cleanly over root containing circle:C:proxy without throwing on non-SphereGeometry
    const root = new THREE.Group();
    root.add(builtCircle);
    const cam = new THREE.PerspectiveCamera(50, 1.6, 0.1, 200);
    cam.position.set(8, 8, 6);
    cam.lookAt(0, 0, 0);
    cam.updateMatrixWorld();
    expect(() => datCoDauDinh(root, cam, 1280, 800, 0.5)).not.toThrow();
  });

  it("clamps OrbitControls minDistance and maxDistance proportionally to fitted camera distance in datKhungNhin", () => {
    const cam = new THREE.PerspectiveCamera(50, 1.5, 0.1, 200);
    cam.up.set(0, 0, 1);
    const docStub = { addEventListener() {}, removeEventListener() {} };
    const domStub = {
      style: {},
      ownerDocument: docStub,
      addEventListener() {},
      removeEventListener() {},
      getRootNode() {
        return docStub;
      },
    } as unknown as HTMLElement;
    const controls = new OrbitControls(cam, domStub);
    datKhungNhin(cam, controls, { viTri: [10, 0, 0], nhinVao: [0, 0, 0] });
    expect(controls.minDistance).toBeCloseTo(4.2, 5);
    expect(controls.maxDistance).toBeCloseTo(28, 5);
    controls.dispose();
  });
});

describe("Supplemental Regression Archetypes #9 (Multi-Layer Aux) & #10 (Coincident Elements) (§12)", () => {
  it("validates dependency-respecting steps, GIVEN purity, aux retirement, and coincident point label deduplication", () => {
    const archMap = supplementalArchetypes as unknown as Record<string, { scene3d: Scene3D }>;
    const multiAux = withSubEntities(veKhongGian(structuredClone(archMap.multi_layer_aux_pyramid.scene3d)));
    const coinc = withSubEntities(veKhongGian(structuredClone(archMap.coincident_elements_pyramid.scene3d)));

    for (const sc of [multiAux, coinc]) {
      // GIVEN purity: no auxiliary helper in free_objects or origin="free"
      for (const o of sc.objects) {
        if ((o.formation_roles ?? []).includes("CONSTRUCT_AUXILIARY_GEOMETRY")) {
          expect(o.origin).not.toBe("free");
          expect(sc.free_objects).not.toContain(o.id);
        }
      }
      // Every timeline step respects dependencies: all object depends exist at or before object appearance
      const tl = geometryTimeline(sc);
      expect(tl.length).toBeGreaterThanOrEqual(4);
      for (const g of tl) {
        const present = entitiesPresentAt(sc, g.anchor, objectsAt);
        for (const o of objectsAt(sc, g.anchor)) {
          for (const d of o.depends ?? []) {
            expect(present.has(d)).toBe(true);
          }
        }
      }
    }

    // Archetype #9: auxiliary diagonals AC & BD and cutting plane P_cut auto-retire at final closed section step (restorable via Hình phụ)
    const finalMulti = multiAux.events.length - 1;
    const hiddenAux = auxiliaryHiddenAt(multiAux, finalMulti, false, null);
    expect(hiddenAux.has("AC")).toBe(true);
    expect(hiddenAux.has("BD")).toBe(true);
    const pCut = multiAux.objects.find((o) => o.id === "P_cut")!;
    const cutVis = resolvePlaneSectionVisibility(multiAux, pCut, finalMulti, false, null);
    expect(cutVis.visible).toBe(false);
    expect(resolvePlaneSectionVisibility(multiAux, pCut, finalMulti, true, null).visible).toBe(true);

    // Archetype #10: coincident points H and O at (0,0,0) merge cleanly into one label without duplicate clutter
    const finalCoincPts = objectsAt(coinc, coinc.events.length - 1).filter((o) => o.type === "point3" && !o.id.includes("::"));
    const labelMap = kyHieuDiem(finalCoincPts);
    const mergedLabels = [...labelMap.values()];
    expect(mergedLabels.some((txt) => txt.includes("≡"))).toBe(true);
    expect(labelMap.has("H") && labelMap.has("O")).toBe(false);
  });
});

describe("Semantic Line, Segment, Intersection, Altitude & Vector Distinction (§3.3 & §3.4)", () => {
  it("distinguishes finite segment3, infinite primary/given line3, plane-plane intersection line3, altitude witness segment3, auxiliary line3, non_visual vector3, and directed Oxyz axes", () => {
    const anchorPts: [number, number, number][] = [
      [0, 0, 0],
      [4, 0, 0],
      [0, 4, 0],
      [0, 0, 4],
    ];

    // 1. Plane-plane intersection line (`CONSTRUCT_INTERSECTION`): terracotta #C85A32, extended, full prominence, yields colinear canonical segment cleanly
    const interLine: SceneObject = {
      id: "gt_d",
      label: "Δ",
      type: "line3",
      render: "line",
      origin: "derived",
      producer: "intersect_plane_plane",
      formation_roles: ["CONSTRUCT_INTERSECTION"],
      display_group: ["construction", "target"],
      depends: ["alpha", "beta"],
      point: ["0", "0", "0"],
      direction: ["4", "0", "0"],
    };
    const interSem = classifySceneObjectSemantics({ objects: [interLine] } as unknown as Scene3D, interLine, 0);
    expect(interSem.role).toBe("RESULT_SECTION");
    expect(interSem.strokeColor).toBe(0xc85a32);

    const builtInter = buildObject3D(interLine, false, undefined, anchorPts)!;
    expect(builtInter.userData.voHan).toBe(true);
    expect(builtInter.userData.nonCanonicalSegment.yieldColinear).toBe(true);
    const interThay = builtInter.getObjectByName("line:gt_d:thay") as THREE.Line;
    const interMat = interThay.material as THREE.LineBasicMaterial;
    expect(hueDistanceDeg(interMat.color.getHex(), 0xc85a32)).toBeLessThan(2);
    expect(interMat.opacity).toBeGreaterThanOrEqual(0.9);
    const interPos = interThay.geometry.getAttribute("position") as THREE.BufferAttribute;
    const interLen = new THREE.Vector3().fromBufferAttribute(interPos, 0).distanceTo(
      new THREE.Vector3().fromBufferAttribute(interPos, 1),
    );
    expect(interLen).toBeGreaterThan(4.2); // Infinite line extends past [0,0,0]..[4,0,0]

    // 2. Given / target spatial line3 (e.g. `bc` in `vuong-goc-chop`): cobalt #2563EB, extended, NOT crushed to 0.42 opacity
    const vgScene = sceneOf("vuong-goc-chop");
    const bcLine = vgScene.objects.find((o) => o.id === "bc")!;
    const bcSem = classifySceneObjectSemantics(vgScene, bcLine, vgScene.events.length - 1);
    expect(bcSem.role).toBe("BOUNDARY_AND_INTERSECTION");
    expect(bcSem.strokeColor).toBe(0x2563eb);
    const vgPts = vgScene.objects.filter((o) => o.xyz).map((o) => toVec3(o.xyz!));
    const builtBc = buildObject3D(bcLine, false, undefined, vgPts, undefined, undefined, undefined, false, "primary", true, true, false, vgScene)!;
    expect(builtBc.userData.voHan).toBe(true);
    const bcThay = builtBc.getObjectByName("line:bc:thay") as THREE.Line;
    const bcMat = bcThay.material as THREE.LineBasicMaterial;
    expect(hueDistanceDeg(bcMat.color.getHex(), 0x2563eb)).toBeLessThan(2);
    expect(bcMat.opacity).toBeGreaterThanOrEqual(0.85);
    const builtBcSel = buildObject3D(bcLine, "dich", undefined, vgPts, undefined, undefined, undefined, false, "primary", true, true, false, vgScene)!;
    const bcSelMat = (builtBcSel.getObjectByName("line:bc:thay") as THREE.Line).material as THREE.LineBasicMaterial;
    expect(hueDistanceDeg(bcSelMat.color.getHex(), 0x2563eb)).toBeLessThan(2);

    // 3. Finite altitude / perpendicular witness segment3 (`SO` in `insphere_square_pyramid`): teal #0F766E, exact endpoints, certified right-angle marker, zero arrowheads
    const inSphereScene = (inCircumFixtures as unknown as { insphere_square_pyramid: { scene3d: Scene3D } }).insphere_square_pyramid.scene3d;
    const shSeg = inSphereScene.objects.find((o) => o.id === "SO")!;
    const shSem = classifySceneObjectSemantics(inSphereScene, shSeg, inSphereScene.events.length - 1);
    expect(shSem.role).toBe("CERTIFIED_RELATION_MARKER");
    expect(shSem.strokeColor).toBe(0x0f766e);
    const inPts = inSphereScene.objects.filter((o) => o.xyz).map((o) => toVec3(o.xyz!));
    const builtSh = buildObject3D(shSeg, false, undefined, inPts, undefined, undefined, undefined, false, "primary", true, true, false, inSphereScene)!;
    expect(builtSh.userData.voHan).toBe(false);
    const shThay = builtSh.getObjectByName("segment:SO:thay") as THREE.Line;
    const shPos = shThay.geometry.getAttribute("position") as THREE.BufferAttribute;
    const shLen = new THREE.Vector3().fromBufferAttribute(shPos, 0).distanceTo(
      new THREE.Vector3().fromBufferAttribute(shPos, 1),
    );
    const expectedShLen = new THREE.Vector3(...toVec3(shSeg.point_a!)).distanceTo(new THREE.Vector3(...toVec3(shSeg.point_b!)));
    expect(shLen).toBeCloseTo(expectedShLen, 6); // Finite segment stops strictly at endpoints
    let hasPerpMarker = false;
    let hasConeArrow = false;
    builtSh.traverse((n) => {
      if (n.name.startsWith("perp_marker:")) hasPerpMarker = true;
      if ((n as THREE.Mesh).isMesh && (n as THREE.Mesh).geometry instanceof THREE.ConeGeometry) hasConeArrow = true;
    });
    expect(hasPerpMarker).toBe(true);
    expect(hasConeArrow).toBe(false);

    // 4. Auxiliary construction line3 keeps teal #0F766E & `auxiliary_line` width < solid edge, subtly attenuated in neutral state (`<= 0.5`) and full opacity when selected
    const auxLine: SceneObject = {
      id: "aux_bd",
      label: "BD",
      type: "line3",
      render: "line",
      origin: "derived",
      producer: "construct_line",
      formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
      display_group: ["construction"],
      depends: ["B", "D"],
      point: ["4", "0", "0"],
      direction: ["-4", "4", "0"],
    };
    const builtAux = buildObject3D(auxLine, false, undefined, anchorPts)!;
    expect(builtAux.userData.semanticLineRole).toBe("auxiliary_line");
    const auxMat = (builtAux.getObjectByName("line:aux_bd:thay") as THREE.Line).material as THREE.LineBasicMaterial;
    expect(hueDistanceDeg(auxMat.color.getHex(), 0x0f766e)).toBeLessThan(2);
    expect(auxMat.opacity).toBeCloseTo(PHONG_CACH_SCENE3D.opacity.auxiliary, 3);
    expect(auxMat.opacity).toBeLessThan(bcMat.opacity);

    // Fat-line screen width hierarchy: intersection line (section tier) > primary line (edge tier) > auxiliary line
    const lineRoot = new THREE.Group();
    lineRoot.add(builtInter, builtBc, builtAux);
    const fatLines = new THREE.Group();
    dongBoNetDayManHinh([lineRoot], fatLines, 1440, 900, true);
    const wInter = (fatLines.children.find((c) => c.name.includes("line:gt_d:thay")) as unknown as { material: { linewidth: number } }).material.linewidth;
    const wBc = (fatLines.children.find((c) => c.name.includes("line:bc:thay")) as unknown as { material: { linewidth: number } }).material.linewidth;
    const wAux = (fatLines.children.find((c) => c.name.includes("line:aux_bd:thay")) as unknown as { material: { linewidth: number } }).material.linewidth;
    expect(wInter).toBeGreaterThan(wBc);
    expect(wBc).toBeGreaterThan(wAux);

    // 5. Free vector3 (`render: "non_visual"`) never fabricates a 3D mesh, while directed Oxyz axes carry explicit ConeGeometry arrowheads
    const freeVec: SceneObject = {
      id: "v_ab",
      label: "u",
      type: "vector3",
      render: "non_visual",
      origin: "derived",
      producer: "construct_vector",
      depends: [],
    };
    expect(buildObject3D(freeVec, false, undefined, anchorPts)).toBeNull();

    const oxyz = dungTrucOxyzSuPham(anchorPts);
    const arrowTips: string[] = [];
    oxyz.traverse((n) => {
      if ((n as THREE.Mesh).isMesh && n.name.endsWith(":mui")) arrowTips.push(n.name);
    });
    expect(arrowTips).toEqual(["truc:Ox:mui", "truc:Oy:mui", "truc:Oz:mui"]);
  });
});

describe("Unified Visual, Pedagogical & Interaction Repair (§2–§5, §7)", () => {
  it("renders default semantic colors at default open without requiring hover or click (purple cutting plane 0.085/0.85, terracotta section #C85A32, teal certified height SA #0F766E)", () => {
    const sample = sampleById("thiet-dien-chop");
    const scene = withSubEntities(veKhongGian(sample.envelope.scene3d));
    const defaultHtml = renderToString(
      <AxoWorkspaceV62 scene={scene} de={sample.envelope.description} tieuDe={sample.title} />,
    );
    // Opens on the completed final pedagogical step by default so the full figure & semantic colors are immediately legible
    expect(defaultHtml).toContain("Bước 10/10");
    expect(defaultHtml).toContain("Dựng các giao tuyến và hoàn thiện thiết diện (MNPQ)");
    expect(defaultHtml).toContain("Thiết diện (MNPQ)");
    expect(defaultHtml).not.toContain("Thiết diện (NMQP)");

    // Cutting plane `mp` has matphang.html reference fill 0.085 (#6D28D9) and visible border 0.85 (2.7px) at default state
    const mp = scene.objects.find((o) => o.id === "mp")!;
    const anchorPts = scene.objects.filter((o) => o.xyz).map((o) => toVec3(o.xyz!));
    const builtMp = buildObject3D(
      mp,
      false,
      undefined,
      anchorPts,
      undefined,
      undefined,
      undefined,
      false,
      "primary",
      true,
      true,
      false,
      scene,
    )!;
    const mpSheet = (builtMp.getObjectByName("plane_sheet:mp") ?? builtMp) as THREE.Mesh;
    const mpFillMat = mpSheet.material as THREE.MeshBasicMaterial;
    const mpBorder = builtMp.getObjectByName("plane_border:mp") as THREE.Line;
    const mpBorderMat = mpBorder.material as THREE.LineBasicMaterial;
    expect(mpFillMat.color.getHex()).toBe(0x6d28d9);
    expect(mpFillMat.opacity).toBeCloseTo(0.085, 3);
    expect(mpBorderMat.color.getHex()).toBe(0x6d28d9);
    expect(mpBorderMat.opacity).toBeCloseTo(0.85, 2);

    // Hover on cutting plane subtly boosts stroke/fill without shifting hue to blue or cyan
    const hoveredMp = buildObject3D(
      mp,
      "hover",
      undefined,
      anchorPts,
      undefined,
      undefined,
      undefined,
      false,
      "primary",
      true,
      true,
      false,
      scene,
    )!;
    const hovBorderMat = (hoveredMp.getObjectByName("plane_border:mp") as THREE.Line).material as THREE.LineBasicMaterial;
    expect(hueDistanceDeg(hovBorderMat.color.getHex(), 0x6d28d9)).toBeLessThan(2);
    expect(hovBorderMat.opacity).toBeGreaterThan(mpBorderMat.opacity);

    // Certified height SA (`chieu_cao_SA` -> `chop::edge:A-S`) renders in #0F766E teal on canonical solid edges at default open
    const solid = scene.objects.find((o) => o.id === "chop")!;
    const defaultEdgeColors = new Map<string, number>([["chop::edge:A-S", 0x0f766e]]);
    const builtSolid = buildObject3D(
      solid,
      false,
      undefined,
      anchorPts,
      undefined,
      undefined,
      undefined,
      false,
      "primary",
      true,
      true,
      false,
      scene,
      defaultEdgeColors,
    )!;
    let saEdgeMatColor: number | null = null;
    let bcEdgeMatColor: number | null = null;
    builtSolid.traverse((node) => {
      const ce = node.userData?.canonicalEdge as { id: string } | undefined;
      if (ce?.id === "chop::edge:A-S") {
        const line = node.children.find((c) => (c as THREE.Line).isLine) as THREE.Line;
        saEdgeMatColor = (line.material as THREE.LineBasicMaterial).color.getHex();
      } else if (ce?.id === "chop::edge:B-C") {
        const line = node.children.find((c) => (c as THREE.Line).isLine) as THREE.Line;
        bcEdgeMatColor = (line.material as THREE.LineBasicMaterial).color.getHex();
      }
    });
    expect(saEdgeMatColor).toBe(0x0f766e);
    expect(bcEdgeMatColor).toBe(PHONG_CACH_SCENE3D.colors.canh);
  });

  it("constructs dependency-grounded pedagogical steps without floating future points and provides verified mathematical tooltips", () => {
    const sample = sampleById("thiet-dien-chop");
    const scene = withSubEntities(veKhongGian(sample.envelope.scene3d));
    const steps = pedagogicalStepList(scene);

    expect(steps).toHaveLength(10);
    // Raw legacy `thiet-dien-chop` in `geometry-samples.json` lacks base shape provenance (`day_ABCD.label = "Đáy ABCD"`), so Step 1 honestly avoids fabricating "hình vuông" (§3.2)
    expect(steps[0].title).toBe("Dựng mặt đáy ABCD");
    expect(steps[1].title).toBe("Dựng đường cao SA ⊥ (ABCD) tại A");
    expect(steps[2].title).toBe("Dựng các cạnh bên SB, SC, SD");
    expect(steps[3].title).toBe("Hoàn thiện hình chóp S.ABCD");
    expect(steps[7].title).toBe("Dựng mặt phẳng cắt (MNP)");
    expect(steps[7].subtitle).toContain("song song với mặt đáy (ABCD)");
    expect(steps[8].title).toBe("Xác định giao điểm Q = SD ∩ (MNP)");
    expect(steps[8].subtitle).toContain("SQ = QD");
    expect(steps[9].title).toBe("Dựng các giao tuyến và hoàn thiện thiết diện (MNPQ)");

    // Step 1 (`anchor = 1`): apex S is ungrounded and must NOT float prematurely before Step 2 (`SA ⊥ (ABCD)`)
    const ungroundedStep1 = ungroundedFreePointIdsAt(scene, steps[0].anchor);
    expect(ungroundedStep1.has("S")).toBe(true);
    expect(ungroundedFreePointIdsAt(scene, steps[1].anchor).has("S")).toBe(false);

    // Canonical cycle notation orders out-of-order polygon traversal `(N, M, Q, P)` into `(MNPQ)`
    expect(formatCycleNotation(["N", "M", "Q", "P"], ["M", "N", "P", "Q"])).toBe("(MNPQ)");

    // Verified mathematical tooltips provide meaningful mathematical facts and return null for bare unannotated edges
    const finalAnchor = steps[steps.length - 1].anchor;
    const tipM = buildVerifiedObjectTooltip(scene, "M", finalAnchor);
    expect(tipM).not.toBeNull();
    expect(tipM!.body).toContain("Trung điểm của SA");
    expect(tipM!.body).toContain("SM = MA");

    const tipQ = buildVerifiedObjectTooltip(scene, "Q", finalAnchor);
    expect(tipQ).not.toBeNull();
    expect(tipQ!.body).toContain("SD");
    expect(tipQ!.body).toContain("(MNP)");
    expect(tipQ!.body).toContain("SQ = QD");

    const tipMp = buildVerifiedObjectTooltip(scene, "mp", finalAnchor);
    expect(tipMp).not.toBeNull();
    expect(tipMp!.body).toContain("M, N, P");
    expect(tipMp!.body).toContain("(ABCD)");

    const tipSa = buildVerifiedObjectTooltip(scene, "chieu_cao_SA", finalAnchor);
    expect(tipSa).not.toBeNull();
    expect(tipSa!.body).toContain("Vuông góc");
    expect(tipSa!.body).toContain("ABCD");

    const tipSec = buildVerifiedObjectTooltip(scene, "thiet_dien", finalAnchor);
    expect(tipSec).not.toBeNull();
    expect(tipSec!.header).toBe("Thiết diện (MNPQ)");
    expect(tipSec!.body).toContain("MN ∥ AB");
    expect(tipSec!.body).not.toContain("hình vuông");

    const certRaw = structuredClone(sample.envelope.scene3d);
    certRaw.objects.find((o) => o.id === "day_ABCD")!.label = "Đáy ABCD là hình vuông";
    const certScene = withSubEntities(veKhongGian(certRaw));
    expect(buildVerifiedObjectTooltip(certScene, "thiet_dien", finalAnchor)?.body).toContain("hình vuông");

    // Bare solid edge without special height/witness relation returns null instead of merely repeating "Cạnh BC"
    expect(buildVerifiedObjectTooltip(scene, "chop::edge:B-C", finalAnchor)).toBeNull();

    // Non-cutting studied planes & hidden duplicate base planes across families
    const mpPerpSteps = pedagogicalStepList(withSubEntities(veKhongGian(sampleById("mp-vuong-goc-duong").envelope.scene3d)));
    expect(mpPerpSteps[mpPerpSteps.length - 1].title).toBe("Dựng mặt phẳng (α)");
    expect(mpPerpSteps.some((s) => s.title.includes("(ABCD)") && s.title.includes("mặt phẳng cắt"))).toBe(false);

    const volSteps = pedagogicalStepList(withSubEntities(veKhongGian(sampleById("the-tich-chop").envelope.scene3d)));
    expect(volSteps.map((s) => s.title)).toEqual([
      "Dựng mặt đáy ABCD",
      "Dựng đường cao SA ⊥ (ABCD) tại A",
      "Dựng các cạnh bên SB, SC, SD",
      "Hoàn thiện hình chóp S.ABCD",
    ]);
    expect(volSteps).toHaveLength(4);
    expect(volSteps.some((s) => /^Tính /u.test(s.title))).toBe(false);
    expect(volSteps.some((s) => s.title.includes("mặt phẳng cắt"))).toBe(false);

    const obliqueCylSteps = pedagogicalStepList(withSubEntities(veKhongGian(sampleById("tru-truc-xien").envelope.scene3d)));
    expect(obliqueCylSteps.map((s) => s.title)).toEqual([
      "Dựng hình trụ trục OO′",
    ]);
    const obliqueCylFullSteps = buildPedagogicalConstructionPlan(
      withSubEntities(veKhongGian(sampleById("tru-truc-xien").envelope.scene3d)),
    ).steps;
    expect(obliqueCylFullSteps.map((s) => s.title)).toEqual([
      "Dựng đường tròn đáy tâm O, bán kính OA của hình trụ",
      "Xác định tâm O′, dựng trục OO′ và đường tròn đáy tâm O′ của hình trụ",
      "Hoàn thiện mặt xung quanh hình trụ trục OO′",
    ]);

    const cylSecSteps = pedagogicalStepList(withSubEntities(veKhongGian(sampleById("tru-thiet-dien-tron").envelope.scene3d)));
    expect(cylSecSteps[cylSecSteps.length - 1].title).toBe("Dựng đường tròn thiết diện giao của hình trụ và (α)");
  });
});
