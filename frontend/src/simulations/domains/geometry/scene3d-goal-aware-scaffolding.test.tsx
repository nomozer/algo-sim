import { describe, expect, it } from "vitest";
import * as THREE from "three";
import samplesData from "../../../data/geometry-samples.json";
import { objectsAt, toVec3, type Scene3D } from "./scene3d-model";
import { veKhongGian } from "./scene3d-chart";
import { withSubEntities } from "./scene3d-subentities";
import { buildObject3D, updateCanonicalEdgeVisibility } from "./scene3d-view";
import {
  buildPedagogicalConstructionPlan,
  computeBoundedStudiedPlanePolygon,
  deriveExactPolygonMathBasis,
  pedagogicalStepList,
  resolvePlaneSectionVisibility,
  resolveStepVisualRoles,
} from "./scene3d-semantic-policy";

function sampleScene(id: string): Scene3D {
  const found = (samplesData.samples as unknown as Array<{ id: string; envelope: { scene3d: Scene3D } }>).find(
    (s) => s.id === id,
  );
  if (!found) throw new Error(`Sample not found: ${id}`);
  return withSubEntities(veKhongGian(found.envelope.scene3d));
}

describe("AXO Goal-Aware Visual Scaffolding & Construction Step Refinement (§4–§10)", () => {
  describe("1. Unified 4-tier step visual role policy (PRIMARY | CONTEXT | SUPPORT | INACTIVE)", () => {
    it("transitions cutting plane (MNP) from INACTIVE -> PRIMARY -> CONTEXT -> SUPPORT -> retired SUPPORT at completed polyhedron section while preserving #chk-aux and selection overrides", () => {
      const plan = buildPedagogicalConstructionPlan(sampleScene("thiet-dien-chop"));
      const scene = plan.scene;
      const steps = plan.steps;

      // Step 1-4 (building pyramid S.ABCD): cutting plane `mp` and section `thiet_dien` are INACTIVE
      const rolesStep4 = resolveStepVisualRoles(scene, steps[3].anchor);
      expect(rolesStep4.get("mp")?.role).toBe("INACTIVE");
      expect(rolesStep4.get("mp")?.visible).toBe(false);
      expect(rolesStep4.get("thiet_dien")?.role).toBe("INACTIVE");
      expect(rolesStep4.get("thiet_dien")?.visible).toBe(false);

      // Step 8 (constructing cutting plane (MNP)): `mp` is PRIMARY at full opacity
      const planeStepIdx = steps.findIndex((s) => s.targetIds.includes("mp"));
      expect(planeStepIdx).toBeGreaterThanOrEqual(0);
      const rolesPlaneStep = resolveStepVisualRoles(scene, steps[planeStepIdx].anchor);
      expect(rolesPlaneStep.get("mp")?.role).toBe("PRIMARY");
      expect(rolesPlaneStep.get("mp")?.visible).toBe(true);
      expect(rolesPlaneStep.get("mp")?.opacityScale).toBe(1);

      // Step 9 (finding Q = SD ∩ (MNP)): Q is PRIMARY, `mp` softens to CONTEXT
      const qStepIdx = steps.findIndex((s) => s.targetIds.includes("Q"));
      expect(qStepIdx).toBeGreaterThan(planeStepIdx);
      const rolesQStep = resolveStepVisualRoles(scene, steps[qStepIdx].anchor);
      expect(rolesQStep.get("Q")?.role).toBe("PRIMARY");
      expect(rolesQStep.get("mp")?.role).toBe("CONTEXT");
      expect(rolesQStep.get("mp")?.visible).toBe(true);
      expect(rolesQStep.get("mp")!.opacityScale).toBeLessThan(0.8);
      expect(rolesQStep.get("mp")!.opacityScale).toBeGreaterThanOrEqual(0.5);

      // Step 10 (learner-reachable consolidated face traces + completed section MNPQ):
      // `thiet_dien` is PRIMARY, `chop` is CONTEXT, and `mp` stays gently visible in softened SUPPORT (`0.28`)
      // so the learner sees how `(MNP)` cuts each face to form `MN, NP, PQ, QM`!
      const finalStep = steps[steps.length - 1];
      const finalAnchor = finalStep.anchor;
      const rolesFinalDefault = resolveStepVisualRoles(scene, finalAnchor, {
        auxiliaryShown: false,
        selectedId: null,
      });
      expect(rolesFinalDefault.get("thiet_dien")?.role).toBe("PRIMARY");
      expect(rolesFinalDefault.get("thiet_dien")?.visible).toBe(true);
      expect(rolesFinalDefault.get("thiet_dien")?.opacityScale).toBe(1);
      expect(rolesFinalDefault.get("chop")?.role).toBe("CONTEXT");
      expect(rolesFinalDefault.get("chop")?.visible).toBe(true);
      expect(rolesFinalDefault.get("mp")?.role).toBe("SUPPORT");
      expect(rolesFinalDefault.get("mp")?.visible).toBe(true);
      expect(rolesFinalDefault.get("mp")!.opacityScale).toBeCloseTo(0.28, 5);

      const mpObj = scene.objects.find((o) => o.id === "mp")!;
      expect(
        resolvePlaneSectionVisibility(scene, mpObj, finalAnchor, false, null, finalStep.startAnchor).visible,
      ).toBe(true);
      // On a standalone post-trace frame (`startAnchor === finalAnchor`), `mp` retires by default (`visible: false`)
      expect(resolvePlaneSectionVisibility(scene, mpObj, finalAnchor, false, null).visible).toBe(false);

      // Toggling `#chk-aux` (`auxiliaryShown = true`) restores `mp` gently without displacing PRIMARY `thiet_dien`
      const rolesFinalAuxOn = resolveStepVisualRoles(scene, finalAnchor, {
        auxiliaryShown: true,
        selectedId: null,
      });
      expect(rolesFinalAuxOn.get("thiet_dien")?.role).toBe("PRIMARY");
      expect(rolesFinalAuxOn.get("mp")?.visible).toBe(true);
      expect(rolesFinalAuxOn.get("mp")!.opacityScale).toBeLessThan(0.6);

      // Directly selecting `mp` restores full inspection opacity
      expect(resolvePlaneSectionVisibility(scene, mpObj, finalAnchor, false, "mp").visible).toBe(true);
      expect(resolvePlaneSectionVisibility(scene, mpObj, finalAnchor, false, "mp").opacityScale).toBe(1);
    });

    it("generalizes section salience policy to renamed/rescaled novel polyhedron section (K.EFGH cut by (UVW) -> UVWX) without case-ID or label hardcoding", () => {
      const novelPyrSection = veKhongGian({
        free_objects: ["E", "F", "G", "H", "K"],
        objects: [
          { id: "E", type: "point3", label: "E", notation: "E", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "F", type: "point3", label: "F", notation: "F", origin: "free", render: "point_marker", depends: [], xyz: ["6", "0", "0"] },
          { id: "G", type: "point3", label: "G", notation: "G", origin: "free", render: "point_marker", depends: [], xyz: ["6", "4", "0"] },
          { id: "H", type: "point3", label: "H", notation: "H", origin: "free", render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
          { id: "K", type: "point3", label: "K", notation: "K", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "8"] },
          {
            id: "solid_kefgh",
            type: "solid",
            label: "Hình chóp K.EFGH",
            notation: "K.EFGH",
            shape_class: "PYRAMID_LIKE",
            origin: "derived",
            render: "mesh",
            depends: ["E", "F", "G", "H", "K"],
            vertex_ids: ["K", "E", "F", "G", "H"],
            vertices: [["0", "0", "8"], ["0", "0", "0"], ["6", "0", "0"], ["6", "4", "0"], ["0", "4", "0"]],
            faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]],
          },
          { id: "U", type: "point3", label: "U", notation: "U", origin: "derived", render: "point_marker", depends: ["K", "E"], xyz: ["0", "0", "4"] },
          { id: "V", type: "point3", label: "V", notation: "V", origin: "derived", render: "point_marker", depends: ["K", "F"], xyz: ["3", "0", "4"] },
          { id: "W", type: "point3", label: "W", notation: "W", origin: "derived", render: "point_marker", depends: ["K", "G"], xyz: ["3", "2", "4"] },
          { id: "mp_uvw", type: "plane3", label: "(UVW)", notation: "(UVW)", origin: "derived", render: "surface", surface_role: "CUTTING_PLANE", depends: ["U", "V", "W"], point: ["0", "0", "4"], normal: ["0", "0", "1"] },
          { id: "X", type: "point3", label: "X", notation: "X", origin: "derived", render: "point_marker", depends: ["K", "H", "mp_uvw"], xyz: ["0", "2", "4"] },
          {
            id: "sec_uvwx",
            type: "section",
            label: "Thiết diện UVWX",
            notation: "UVWX",
            origin: "derived",
            render: "polygon",
            surface_role: "SECTION_REGION",
            depends: ["solid_kefgh", "mp_uvw", "U", "V", "W", "X"],
            vertex_ids: ["U", "V", "W", "X"],
            polygon: [["0", "0", "4"], ["3", "0", "4"], ["3", "2", "4"], ["0", "2", "4"]],
            closed: true,
            fill_visible: true,
          },
        ],
        events: [
          { step_index: 0, action: "INIT" },
          { step_index: 1, action: "CREATE", object: "solid_kefgh" },
          { step_index: 2, action: "CREATE", object: "U" },
          { step_index: 3, action: "CREATE", object: "V" },
          { step_index: 4, action: "CREATE", object: "W" },
          { step_index: 5, action: "CREATE", object: "mp_uvw" },
          { step_index: 6, action: "CREATE", object: "X" },
          { step_index: 7, action: "CREATE", object: "sec_uvwx" },
        ],
      } as unknown as Scene3D);

      const plan = buildPedagogicalConstructionPlan(withSubEntities(novelPyrSection));
      const finalStep = plan.steps[plan.steps.length - 1];
      const finalRoles = resolveStepVisualRoles(plan.scene, finalStep.anchor);
      expect(finalRoles.get("sec_uvwx")?.role).toBe("PRIMARY");
      expect(finalRoles.get("solid_kefgh")?.role).toBe("CONTEXT");
      expect(finalRoles.get("mp_uvw")?.role).toBe("SUPPORT");
      expect(finalRoles.get("mp_uvw")?.visible).toBe(false);
      expect(finalStep.title).toBe("Hoàn thiện và làm nổi bật thiết diện (UVWX)");
      expect(finalStep.title).not.toContain("hình chữ nhật");
    });

    it("preserves BOTH planes as visible CONTEXT during plane-plane intersection (§6.B) and keeps target plane visible in point-to-plane distance (§6.D)", () => {
      // Plane-plane intersection: (P_alpha) ∩ (P_beta) = gt_d
      const interScene = withSubEntities(
        veKhongGian({
          free_objects: ["A", "B", "C", "D", "S"],
          objects: [
            { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
            { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["4", "0", "0"] },
            { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point_marker", depends: [], xyz: ["4", "4", "0"] },
            { id: "D", type: "point3", label: "D", notation: "D", origin: "free", render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
            { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
            {
              id: "chop_sabcd",
              type: "solid",
              label: "Hình chóp S.ABCD",
              notation: "S.ABCD",
              shape_class: "PYRAMID_LIKE",
              origin: "derived",
              render: "mesh",
              depends: ["A", "B", "C", "D", "S"],
              vertex_ids: ["S", "A", "B", "C", "D"],
              vertices: [["0", "0", "4"], ["0", "0", "0"], ["4", "0", "0"], ["4", "4", "0"], ["0", "4", "0"]],
              faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]],
            },
            { id: "mp_sac", type: "plane3", label: "(SAC)", notation: "(SAC)", origin: "derived", render: "surface", depends: ["S", "A", "C"], point: ["0", "0", "0"], normal: ["1", "-1", "0"] },
            { id: "mp_sbd", type: "plane3", label: "(SBD)", notation: "(SBD)", origin: "derived", render: "surface", depends: ["S", "B", "D"], point: ["4", "0", "0"], normal: ["1", "1", "1"] },
            { id: "gt_so", type: "line3", label: "Giao tuyến SO", notation: "SO", origin: "derived", producer: "intersect_planes", render: "line", display_group: ["construction", "target"], depends: ["mp_sac", "mp_sbd"], point: ["0", "0", "4"], direction: ["2", "2", "-4"] },
          ],
          events: [
            { step_index: 0, action: "INIT" },
            { step_index: 1, action: "CREATE", object: "chop_sabcd" },
            { step_index: 2, action: "CREATE", object: "mp_sac" },
            { step_index: 3, action: "CREATE", object: "mp_sbd" },
            { step_index: 4, action: "CREATE", object: "gt_so" },
          ],
        } as unknown as Scene3D),
      );
      const interPlan = buildPedagogicalConstructionPlan(interScene);
      const interFinal = interPlan.steps[interPlan.steps.length - 1].anchor;
      const interRoles = resolveStepVisualRoles(interPlan.scene, interFinal);
      expect(interRoles.get("gt_so")?.role).toBe("PRIMARY");
      expect(interRoles.get("mp_sac")?.role).toBe("CONTEXT");
      expect(interRoles.get("mp_sac")?.visible).toBe(true);
      expect(interRoles.get("mp_sbd")?.role).toBe("CONTEXT");
      expect(interRoles.get("mp_sbd")?.visible).toBe(true);

      // Point-to-plane / perpendicular studied plane (`mp-vuong-goc-duong`)
      const perpPlan = buildPedagogicalConstructionPlan(sampleScene("mp-vuong-goc-duong"));
      const perpFinal = perpPlan.steps[perpPlan.steps.length - 1].anchor;
      const perpRoles = resolveStepVisualRoles(perpPlan.scene, perpFinal);
      expect(perpRoles.get("mpb")?.visible).toBe(true);
      expect(["PRIMARY", "CONTEXT"]).toContain(perpRoles.get("mpb")?.role);
    });

    it("handles sphere cut by plane (§6.F): circle is PRIMARY, plane & IH/r/R recede to SUPPORT, and pure 1D BOUNDARY_CURVE / fill_visible:false circles never fabricate a solid disk", () => {
      const sphPlan = buildPedagogicalConstructionPlan(sampleScene("cau-cat-mat-phang"));
      const sc = sphPlan.scene;
      expect(sphPlan.steps.length).toBe(5);

      // Step 2: cutting plane P is PRIMARY
      const rolesStep2 = resolveStepVisualRoles(sc, sphPlan.steps[1].anchor);
      expect(rolesStep2.get("P")?.role).toBe("PRIMARY");
      expect(rolesStep2.get("P")?.opacityScale).toBe(1);

      // Step 5: circle C is PRIMARY, sphere `cau` is CONTEXT, cutting plane `P` and `C__dist`/`C__sec_rad`/`C__sph_rad` are SUPPORT
      const rolesStep3 = resolveStepVisualRoles(sc, sphPlan.steps[4].anchor);
      expect(rolesStep3.get("C")?.role).toBe("PRIMARY");
      expect(rolesStep3.get("C")?.opacityScale).toBe(1);
      expect(rolesStep3.get("cau")?.role).toBe("CONTEXT");
      expect(rolesStep3.get("P")?.role).toBe("SUPPORT");
      expect(rolesStep3.get("P")?.visible).toBe(true);
      expect(rolesStep3.get("P")!.opacityScale).toBeLessThan(0.5);
      expect(rolesStep3.get("C__dist")?.role).toBe("SUPPORT");
      expect(rolesStep3.get("C__sec_rad")?.role).toBe("SUPPORT");
      expect(rolesStep3.get("C__sph_rad")?.role).toBe("SUPPORT");

      // Pure 1D intersection circle (`fill_visible: false` or `surface_role: "BOUNDARY_CURVE"`) must NOT fabricate `section_fill:`
      const pureCurveCircle = {
        ...sc.objects.find((o) => o.id === "C")!,
        id: "C_curve_only",
        surface_role: "BOUNDARY_CURVE",
      } as unknown as Scene3D["objects"][number];
      const builtCurveOnly = buildObject3D(
        pureCurveCircle,
        false,
        undefined,
        [],
        undefined,
        undefined,
        undefined,
        false,
        "primary",
        true,
        true,
        false,
        { objects: [sc.objects.find((o) => o.id === "cau")!, pureCurveCircle] },
      )!;
      expect(builtCurveOnly.getObjectByName("section_fill:C_curve_only")).toBeUndefined();
    });

    it("renders standalone solids (pyramid, cone, cylinder, sphere) at full normal clarity at their final step without cross-section dimming (§6.G)", () => {
      for (const sampleId of ["the-tich-chop", "non-duong-sinh", "cau-the-tich", "tru-truc-xien"]) {
        const plan = buildPedagogicalConstructionPlan(sampleScene(sampleId));
        const finalAnchor = plan.steps[plan.steps.length - 1].anchor;
        const roles = resolveStepVisualRoles(plan.scene, finalAnchor);
        const solidObj = plan.scene.objects.find((o) => o.type === "solid" || o.type === "curved_solid")!;
        expect(solidObj).toBeDefined();
        expect(roles.get(solidObj.id)?.visible).toBe(true);
        expect(roles.get(solidObj.id)?.opacityScale).toBe(1);
      }
    });
  });

  describe("2. Bounded cutting-plane patch & WebGL span border attenuation (§5.3 & §9)", () => {
    it("bounds cutting plane (MNP) tightly around coplanar pierce points instead of inflating to the full base footprint, and propagates opacityScale to nonCanonicalLoop border spans", () => {
      const plan = buildPedagogicalConstructionPlan(sampleScene("thiet-dien-chop"));
      const sc = plan.scene;
      const mp = sc.objects.find((o) => o.id === "mp")!;
      const finalStep = plan.steps[plan.steps.length - 1];
      const visAtFinal = objectsAt(sc, finalStep.anchor);

      const bounded = computeBoundedStudiedPlanePolygon(sc, mp, visAtFinal);
      expect(bounded.length).toBeGreaterThanOrEqual(4);
      const pt0 = toVec3(mp.point!);
      const nrm = toVec3(mp.normal!);
      for (const v of bounded) {
        const dot = (v[0] - pt0[0]) * nrm[0] + (v[1] - pt0[1]) * nrm[1] + (v[2] - pt0[2]) * nrm[2];
        expect(Math.abs(dot)).toBeLessThan(1e-5);
      }
      const maxDiag = Math.max(
        ...bounded.flatMap((a) => bounded.map((b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]))),
      );
      // Section MNPQ is 1x1 (diag ~1.414) on a 2x2 base; compact patch diagonal must stay < 2.35 (was ~2.7+ / full base width)
      expect(maxDiag).toBeLessThan(2.35);
      expect(maxDiag).toBeGreaterThan(1.5);

      // Verify WebGL span rebuild preserves attenuated border opacity when cutting plane recedes to SUPPORT at learner-reachable finalStep
      const root = new THREE.Group();
      const chop = sc.objects.find((o) => o.id === "chop")!;
      const builtSolid = buildObject3D(chop, false, undefined, bounded, undefined, undefined, undefined, false, "primary", true, true, false, sc)!;
      const builtMp = buildObject3D(mp, false, undefined, bounded, undefined, undefined, undefined, false, "primary", true, true, false, sc, undefined, undefined, bounded)!;

      const qMp = resolvePlaneSectionVisibility(sc, mp, finalStep.anchor, false, null, finalStep.startAnchor);
      expect(qMp.visible).toBe(true);
      expect(qMp.opacityScale).toBeLessThanOrEqual(0.45);
      builtMp.traverse((child) => {
        if (child.userData?.nonCanonicalLoop?.isPlaneBorder) {
          child.userData.lamDiu = qMp.opacityScale;
        }
        const line = child as THREE.Line;
        if (line.isLine && line.name.startsWith("plane_border:")) {
          (line.material as THREE.LineBasicMaterial).opacity *= qMp.opacityScale;
        }
      });

      root.add(builtSolid, builtMp);
      const cam = new THREE.PerspectiveCamera(50, 1.5, 0.1, 100);
      cam.up.set(0, 0, 1);
      cam.position.set(6, 5, 5);
      cam.lookAt(1, 1, 2);
      cam.updateMatrixWorld();
      cam.updateProjectionMatrix();

      updateCanonicalEdgeVisibility(root, cam, "1440x900@1");
      const borderOpacities: number[] = [];
      builtMp.traverse((child) => {
        const line = child as THREE.Line;
        if (line.isLine && line.name.startsWith("plane_border:")) {
          borderOpacities.push((line.material as THREE.LineBasicMaterial).opacity);
        }
      });
      expect(borderOpacities.length).toBeGreaterThan(0);
      for (const op of borderOpacities) {
        expect(op).toBeLessThan(0.45);
      }
    });
  });

  describe("3. Observable non-spoiler section narration & deterministic step scrubbing (§7, §8, §10)", () => {
    it("uses observable action title 'Dựng các giao tuyến và hoàn thiện thiết diện (MNPQ)' without unprompted shape conclusion while retaining exact math basis helpers", () => {
      const scene = sampleScene("thiet-dien-chop");
      const steps = pedagogicalStepList(scene);
      const last = steps[steps.length - 1];
      expect(last.title).toBe("Dựng các giao tuyến và hoàn thiện thiết diện (MNPQ)");
      expect(last.title).not.toContain("hình vuông");
      expect(last.subtitle).not.toMatch(/⇒.*hình vuông/u);

      // Raw uncertified legacy scene refuses to infer "hình vuông" from coordinates alone (§3.2), while certified square base preserves exact "hình vuông" deduction
      const secObj = scene.objects.find((o) => o.id === "thiet_dien")!;
      expect(deriveExactPolygonMathBasis(scene, secObj)?.shape).toBe("tứ giác");
      const certScene = structuredClone(scene);
      certScene.objects.find((o) => o.id === "day_ABCD")!.label = "Đáy ABCD là hình vuông";
      expect(deriveExactPolygonMathBasis(certScene, certScene.objects.find((o) => o.id === "thiet_dien")!)?.shape).toBe("hình vuông");
    });

    it("restores identical deterministic step visual roles across forward 1..N, backward N..1, and direct jump(k)", () => {
      const plan = buildPedagogicalConstructionPlan(sampleScene("thiet-dien-chop"));
      const snap = (idx: number) =>
        [...resolveStepVisualRoles(plan.scene, plan.steps[idx].anchor).entries()]
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([id, r]) => `${id}:${r.role}:${r.visible}:${r.opacityScale.toFixed(2)}`);

      const forward = plan.steps.map((_, idx) => snap(idx));
      for (let idx = plan.steps.length - 1; idx >= 0; idx -= 1) {
        expect(snap(idx)).toEqual(forward[idx]);
      }
      expect(snap(plan.steps.length - 1)).toEqual(forward[plan.steps.length - 1]);
    });
  });
});
