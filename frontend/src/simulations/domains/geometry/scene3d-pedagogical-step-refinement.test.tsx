import { describe, expect, it } from "vitest";
import type { Scene3D, SceneObject } from "./scene3d-model";
import { objectsAt } from "./scene3d-model";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { veKhongGian } from "./scene3d-chart";
import { withSubEntities } from "./scene3d-subentities";
import {
  buildPedagogicalConstructionPlan,
  buildVerifiedObjectTooltip,
  resolvePlaneSectionVisibility,
  resolveStepVisualRoles,
  shortSym,
} from "./scene3d-semantic-policy";

function sampleScene(id: string): Scene3D {
  const found = GEOMETRY_SAMPLES.find((s) => s.id === id);
  if (!found) throw new Error(`Missing sample: ${id}`);
  return structuredClone((found.envelope as unknown as { scene3d: Scene3D }).scene3d);
}

describe("AXO Master Frontend §5–§6: Pedagogical Step Consolidation & Goal-Aware Visual Salience", () => {
  it("1. Consolidates redundant fill-only STEP after closed EXTEND traces (`thiet-dien-chop` 11 -> 10, `mat-cheo-sac` 7 -> 6) while keeping Q = SD ∩ (MNP), face traces, parallel basis, and zero shape spoilers", () => {
    const tdPlan = buildPedagogicalConstructionPlan(withSubEntities(sampleScene("thiet-dien-chop")));
    expect(tdPlan.steps).toHaveLength(10);

    // Essential intermediate steps remain distinct and dependency-ordered
    expect(tdPlan.steps[7].title).toBe("Dựng mặt phẳng cắt (MNP)");
    expect(tdPlan.steps[8].title).toBe("Xác định giao điểm Q = SD ∩ (MNP)");

    // Final consolidated step builds the face intersection traces AND highlights the closed section MNPQ in one coherent step
    const finalStep = tdPlan.steps[9];
    expect(finalStep.title).toBe("Dựng các giao tuyến và hoàn thiện thiết diện (MNPQ)");
    expect(finalStep.title).not.toContain("hình vuông");
    expect(finalStep.subtitle).toContain("(SAB)");
    expect(finalStep.subtitle).toContain("MN");
    expect(finalStep.subtitle).toContain("(SBC)");
    expect(finalStep.subtitle).toContain("NP");
    expect(finalStep.subtitle).toContain("(SCD)");
    expect(finalStep.subtitle).toContain("PQ");
    expect(finalStep.subtitle).toMatch(/\(SAD\)|\(SDA\)/u);
    expect(finalStep.subtitle).toContain("QM");
    expect(finalStep.subtitle).toContain("MN ∥ AB");
    expect(finalStep.subtitle).not.toContain("hình vuông");

    // Polygon fill is active at finalStep.anchor, auxiliary cutting plane retires by default and restores on `#chk-aux`
    const prog = tdPlan.scene.formation?.steps[finalStep.anchor]?.geometry_progress?.find(
      (gp) => gp.object_id === "thiet_dien",
    );
    expect(prog?.closed).toBe(true);
    expect(prog?.fill_visible).toBe(true);

    const rolesDefault = resolveStepVisualRoles(tdPlan.scene, finalStep.anchor, {
      auxiliaryShown: false,
      selectedId: null,
    });
    expect(rolesDefault.get("thiet_dien")?.role).toBe("PRIMARY");
    expect(rolesDefault.get("chop")?.role).toBe("CONTEXT");
    // On the consolidated trace+section step, cutting plane `(MNP)` stays gently visible in softened SUPPORT (`0.28`)
    // so the learner sees how `(MNP)` cuts each lateral face to form `MN, NP, PQ, QM`!
    expect(rolesDefault.get("mp")?.role).toBe("SUPPORT");
    expect(rolesDefault.get("mp")?.visible).toBe(true);
    expect(rolesDefault.get("mp")!.opacityScale).toBeCloseTo(0.28, 5);

    const rolesAux = resolveStepVisualRoles(tdPlan.scene, finalStep.anchor, {
      auxiliaryShown: true,
      selectedId: null,
    });
    expect(rolesAux.get("mp")?.visible).toBe(true);
    expect(rolesAux.get("mp")!.opacityScale).toBeCloseTo(0.42, 5);

    // On-demand tooltip provides verified shape proof when base ABCD carries explicit square premise, and avoids uncertified square upgrade on raw legacy scene (§3.2)
    const rawTip = buildVerifiedObjectTooltip(veKhongGian(tdPlan.scene), "thiet_dien", finalStep.anchor);
    expect(rawTip?.body).toContain("MN ∥ AB");
    expect(rawTip?.body).not.toContain("hình vuông");
    const certTdRaw = sampleScene("thiet-dien-chop");
    certTdRaw.objects.find((o) => o.id === "day_ABCD")!.label = "Đáy ABCD là hình vuông";
    const certTdPlan = buildPedagogicalConstructionPlan(withSubEntities(certTdRaw));
    const certTip = buildVerifiedObjectTooltip(
      veKhongGian(certTdPlan.scene),
      "thiet_dien",
      certTdPlan.steps[certTdPlan.steps.length - 1].anchor,
    );
    expect(certTip?.body).toContain("hình vuông");

    // Diagonal section `mat-cheo-sac` consolidates 7 -> 6
    const sacPlan = buildPedagogicalConstructionPlan(withSubEntities(sampleScene("mat-cheo-sac")));
    expect(sacPlan.steps).toHaveLength(6);
    expect(sacPlan.steps[5].title).toContain("thiết diện");
  });

  it("2. Preserves separate steps when an intermediate pierce-point construction separates partial open EXTEND traces from final section closure", () => {
    // Multi-stage section: partial open EXTEND (2 edges, closed: false) -> pierce point Q -> remaining EXTEND + STEP closure
    const base = sampleScene("thiet-dien-chop");
    const origF = base.formation!.steps;
    const perm = [0, 1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 9, 10, 13, 14, 15];
    const visAcc = new Set<string>(base.free_objects);
    const nonAdjacent: Scene3D = {
      ...base,
      events: perm.map((oldIdx, idx) => ({ ...base.events[oldIdx], step_index: idx })),
      formation: {
        steps: perm.map((oldIdx, idx) => {
          const ev = base.events[oldIdx];
          if (ev.object) visAcc.add(ev.object);
          for (const oid of ev.objects ?? []) visAcc.add(oid);
          const origProg = origF[oldIdx]?.geometry_progress ?? [];
          return {
            ...origF[oldIdx],
            step_index: idx,
            visible_ids: [...visAcc],
            geometry_progress: origProg,
          };
        }),
      },
    };
    const plan = buildPedagogicalConstructionPlan(withSubEntities(nonAdjacent));
    // Open partial trace before Q must NOT swallow Q or collapse across Q; Q remains its own step before final closure!
    const qIdx = plan.steps.findIndex((s) => s.targetIds.includes("Q"));
    const finalSecIdx = plan.steps.findIndex((s) => s.title.includes("thiết diện (MNPQ)"));
    expect(qIdx).toBeGreaterThan(0);
    expect(finalSecIdx).toBeGreaterThan(qIdx);
  });

  it("3. Undeclared polyhedron with pre-existing `formation` (`expandPrimaryPolyhedralFoundation`) rebuilds `formation.steps` in lockstep with `events`, and `shortSym` avoids verbose duplicate midpoint prose", () => {
    const undeclaredTetWithFormation: Scene3D = {
      free_objects: ["A", "B", "C", "D"],
      objects: [
        { id: "A", label: "Điểm A", notation: "A", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"] } as SceneObject,
        { id: "B", label: "Điểm B", notation: "B", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["4", "0", "0"] } as SceneObject,
        { id: "C", label: "Điểm C", notation: "C", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "4", "0"] } as SceneObject,
        { id: "D", label: "Điểm D", notation: "D", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "0", "4"] } as SceneObject,
        {
          id: "khoi_D_ABC",
          label: "Tứ diện ABCD",
          notation: "ABCD",
          type: "solid",
          render: "mesh",
          origin: "derived",
          producer: "construct_pyramid",
          depends: ["A", "B", "C", "D"],
          vertex_ids: ["A", "B", "C", "D"],
          vertices: [["0", "0", "0"], ["4", "0", "0"], ["0", "4", "0"], ["0", "0", "4"]],
          faces: [[0, 1, 2], [0, 1, 3], [1, 2, 3], [2, 0, 3]],
        } as unknown as SceneObject,
        {
          id: "M",
          label: "Trung điểm của B và C",
          notation: null,
          type: "point3",
          render: "point_marker",
          origin: "derived",
          producer: "construct_midpoint",
          depends: ["B", "C"],
          xyz: ["2", "2", "0"],
        } as unknown as SceneObject,
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "khoi_D_ABC", depends: ["A", "B", "C", "D"], explanation: "Dựng tứ diện ABCD.", semantic_kind: "GEOMETRY_CONSTRUCTION" },
        { step_index: 1, action: "CREATE", object: "M", depends: ["B", "C"], explanation: "Xác định M.", semantic_kind: "GEOMETRY_CONSTRUCTION" },
      ],
      formation: {
        steps: [
          {
            step_index: 0,
            visible_ids: ["A", "B", "C", "D", "khoi_D_ABC"],
            focus_ids: ["khoi_D_ABC"],
            readout_ids: [],
            learner_text: "Dựng tứ diện ABCD.",
            semantic_kind: "GEOMETRY_CONSTRUCTION",
          },
          {
            step_index: 1,
            visible_ids: ["A", "B", "C", "D", "khoi_D_ABC", "M"],
            focus_ids: ["M"],
            readout_ids: [],
            learner_text: "Xác định M.",
            semantic_kind: "GEOMETRY_CONSTRUCTION",
          },
        ],
      },
    };

    expect(shortSym(undeclaredTetWithFormation.objects.find((o) => o.id === "M"))).toBe("M");

    const plan = buildPedagogicalConstructionPlan(withSubEntities(undeclaredTetWithFormation));
    expect(plan.scene.formation?.steps).toHaveLength(plan.scene.events.length);

    // Step 1 must ONLY show base ABC (`khoi_D_ABC__base`), NOT the full solid `khoi_D_ABC` prematurely!
    const step0Ids = new Set(objectsAt(plan.scene, plan.steps[0].anchor).map((o) => o.id));
    expect(step0Ids.has("khoi_D_ABC__base")).toBe(true);
    expect(step0Ids.has("khoi_D_ABC")).toBe(false);

    // Midpoint step narration must say "Xác định trung điểm M của BC", never "Trung điểm của B và C của BC"
    const mStep = plan.steps.find((s) => s.targetIds.includes("M"));
    expect(mStep).toBeDefined();
    expect(mStep!.title).toBe("Xác định trung điểm M của BC");
    expect(mStep!.title).not.toContain("Trung điểm của B và C");
  });

  it("4. Goal-aware visual roles preserve BOTH planes (`CONTEXT`) on plane-plane intersection and highlight perpendicular witness (`PRIMARY`) on point-plane & skew-line distance", () => {
    // Plane-plane intersection scene
    const planeInterScene: Scene3D = {
      free_objects: ["A", "B", "C", "D"],
      objects: [
        { id: "A", label: "A", notation: "A", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"] } as SceneObject,
        { id: "B", label: "B", notation: "B", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["4", "0", "0"] } as SceneObject,
        { id: "C", label: "C", notation: "C", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "4", "0"] } as SceneObject,
        { id: "D", label: "D", notation: "D", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "0", "4"] } as SceneObject,
        { id: "P", label: "Mặt phẳng (P)", notation: "(P)", type: "plane3", render: "plane", surface_role: "GIVEN_PLANE", origin: "derived", producer: "construct_plane", depends: ["A", "B", "C"], point: ["0", "0", "0"], normal: ["0", "0", "1"] } as unknown as SceneObject,
        { id: "Q_pl", label: "Mặt phẳng (Q)", notation: "(Q)", type: "plane3", render: "plane", surface_role: "CUTTING_PLANE", origin: "derived", producer: "construct_plane", depends: ["A", "B", "D"], point: ["0", "0", "0"], normal: ["0", "1", "0"] } as unknown as SceneObject,
        { id: "gt", label: "Giao tuyến d", notation: "d", type: "line3", render: "line", origin: "derived", producer: "intersect_plane_plane", depends: ["P", "Q_pl"], point: ["0", "0", "0"], direction: ["1", "0", "0"] } as unknown as SceneObject,
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "P", depends: ["A", "B", "C"], explanation: "Dựng (P).", semantic_kind: "GEOMETRY_CONSTRUCTION" },
        { step_index: 1, action: "CREATE", object: "Q_pl", depends: ["A", "B", "D"], explanation: "Dựng (Q).", semantic_kind: "GEOMETRY_CONSTRUCTION" },
        { step_index: 2, action: "CREATE", object: "gt", depends: ["P", "Q_pl"], explanation: "Giao tuyến d.", semantic_kind: "GEOMETRY_CONSTRUCTION" },
      ],
    };
    const interPlan = buildPedagogicalConstructionPlan(planeInterScene);
    const interFinalAnchor = interPlan.steps[interPlan.steps.length - 1].anchor;
    const interRoles = resolveStepVisualRoles(interPlan.scene, interFinalAnchor);
    expect(interRoles.get("gt")?.role).toBe("PRIMARY");
    expect(interRoles.get("P")?.visible).toBe(true);
    expect(interRoles.get("Q_pl")?.visible).toBe(true);
    expect(interRoles.get("P")?.role).toBe("CONTEXT");
    expect(interRoles.get("Q_pl")?.role).toBe("CONTEXT");
    expect(resolvePlaneSectionVisibility(interPlan.scene, interPlan.scene.objects.find((o) => o.id === "P")!, interFinalAnchor, false, null).subRole).toBe("MANDATORY_STUDIED_PLANE");
    expect(resolvePlaneSectionVisibility(interPlan.scene, interPlan.scene.objects.find((o) => o.id === "Q_pl")!, interFinalAnchor, false, null).subRole).toBe("MANDATORY_STUDIED_PLANE");

    // Point-plane / line-plane distance & perpendicularity (`mp-vuong-goc-duong`) + Skew-line common perpendicular fixture
    const perpPlan = buildPedagogicalConstructionPlan(withSubEntities(sampleScene("mp-vuong-goc-duong")));
    const perpFinal = perpPlan.steps[perpPlan.steps.length - 1].anchor;
    const perpRoles = resolveStepVisualRoles(perpPlan.scene, perpFinal);
    expect(perpRoles.get("mpb")?.visible).toBe(true);
    expect(["PRIMARY", "CONTEXT"]).toContain(perpRoles.get("mpb")?.role);

    const skewScene: Scene3D = {
      free_objects: ["A", "B", "C", "S"],
      objects: [
        { id: "A", label: "A", notation: "A", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"] } as SceneObject,
        { id: "B", label: "B", notation: "B", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["4", "0", "0"] } as SceneObject,
        { id: "C", label: "C", notation: "C", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "4", "0"] } as SceneObject,
        { id: "S", label: "S", notation: "S", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "0", "4"] } as SceneObject,
        { id: "d1", label: "SA", notation: "SA", type: "line3", render: "line", origin: "derived", producer: "construct_line", depends: ["S", "A"], point: ["0", "0", "0"], direction: ["0", "0", "1"] } as unknown as SceneObject,
        { id: "d2", label: "BC", notation: "BC", type: "line3", render: "line", origin: "derived", producer: "construct_line", depends: ["B", "C"], point: ["4", "0", "0"], direction: ["-1", "1", "0"] } as unknown as SceneObject,
        {
          id: "H",
          label: "H",
          notation: "H",
          type: "point3",
          render: "point_marker",
          origin: "derived",
          producer: "project_point_line",
          depends: ["A", "d2"],
          xyz: ["2", "2", "0"],
        } as unknown as SceneObject,
        {
          id: "AH",
          label: "Đoạn vuông góc chung AH",
          notation: "AH",
          type: "segment3",
          render: "segment",
          display_group: ["construction", "target"],
          origin: "derived",
          producer: "construct_segment",
          depends: ["A", "H"],
          endpoint_ids: ["A", "H"],
          point_a: ["0", "0", "0"],
          point_b: ["2", "2", "0"],
          endpoints: [["0", "0", "0"], ["2", "2", "0"]],
          perpendicular_witness: {
            relation: "common_perpendicular",
            from: "d1",
            foot: ["2", "2", "0"],
            on: "d2",
            foot_id: "H",
            marker: { u: ["-1", "1", "0"], v: ["-2", "-2", "0"] },
          },
        } as unknown as SceneObject,
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "d1", depends: ["S", "A"], explanation: "Dựng SA.", semantic_kind: "GEOMETRY_CONSTRUCTION" },
        { step_index: 1, action: "CREATE", object: "d2", depends: ["B", "C"], explanation: "Dựng BC.", semantic_kind: "GEOMETRY_CONSTRUCTION" },
        { step_index: 2, action: "CREATE", object: "H", depends: ["A", "d2"], explanation: "Hạ H.", semantic_kind: "GEOMETRY_CONSTRUCTION" },
        { step_index: 3, action: "CREATE", object: "AH", depends: ["A", "H"], explanation: "Đoạn vuông góc chung AH.", semantic_kind: "GEOMETRY_CONSTRUCTION" },
      ],
    };
    const skewPlan = buildPedagogicalConstructionPlan(skewScene);
    const skewFinal = skewPlan.steps[skewPlan.steps.length - 1].anchor;
    const skewRoles = resolveStepVisualRoles(skewPlan.scene, skewFinal);
    expect(skewRoles.get("AH")?.role).toBe("PRIMARY");
    expect(skewRoles.get("d1")?.role).toBe("CONTEXT");
    expect(skewRoles.get("d2")?.role).toBe("CONTEXT");
  });
});
