import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import {
  docPhanHoiHybrid,
  HYBRID_SIMULATION_ADAPTER,
  HYBRID_SIMULATION_SCHEMA,
  hybridViewCua,
} from "./hybrid-preview-adapter";
import {
  annotationsAt,
  classifyQuantityProvenance,
  DEFAULT_ANNOTATION_VIEW,
  givenQuantitiesSummary,
  quantitySources,
} from "./scene3d-annotations";
import * as THREE from "three";
import { veKhongGian } from "./scene3d-chart";
import { classifySolidEdgeVisibility } from "./scene3d-edge-visibility";
import { tangNhanManh } from "./interaction-state";
import {
  attachHybridViewToScene,
  phanTichToanHocCuaCanh,
  quantityChoices,
  registerExactSceneOrigin,
  solutionAt,
  type Scene3D,
  type SceneObject,
} from "./scene3d-model";
import {
  buildPedagogicalConstructionPlan,
  classifyPolygonShapeWithProvenance,
  classifySceneObjectSemantics,
  findPointMidpointRelation,
  resolvePlaneSectionVisibility,
} from "./scene3d-semantic-policy";
import { withSubEntities } from "./scene3d-subentities";

import circumsphereRaw from "./scene3d-circumsphere-fixture.json";
import inscribedRaw from "./scene3d-inscribed-circumscribed-fixtures.json";
import regressionArchetypesRaw from "./scene3d-regression-archetypes-fixtures.json";
import sectionRaw from "./scene3d-section-fixture.json";

describe("AXO Master Continuation §7–§10: Deep Pedagogical Construction, Symbolic Fidelity & Cross-Family Matrix", () => {
  it("1. §7.1–§7.2 & §9: S.ABC (SA ⊥ (ABC), AB = 2a, SA = 4a) preserves symbolic '2a'/'4a' across canvas, Study Dock, compact readouts, goal summary & phanTichToanHocCuaCanh without promoting ABC to right-isosceles or 'a = 1' to GIVEN", () => {
    const sabcScene: Scene3D = {
      chart_metric: [
        ["1", "0", "0"],
        ["0", "1", "0"],
        ["0", "0", "1"],
      ],
      length_unit: { symbol: "a", display_scale: "a = 1 đơn vị dựng", is_given: false },
      free_objects: ["A", "B", "C", "S"],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
        // Coordinate chosen at (0, 2, 0) for layout illustration ONLY — NOT given as perpendicular or equal in problem!
        {
          id: "C",
          type: "point3",
          label: "C",
          notation: "C",
          origin: "free",
          render: "point_marker",
          depends: [],
          xyz: ["0", "2", "0"],
          source: { provenance: "ILLUSTRATIVE_CHOICE", assumption: "ILLUSTRATIVE_CONFIGURATION", is_given: false },
        },
        { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
        {
          id: "day",
          type: "polygon3",
          label: "Đáy ABC",
          notation: "(ABC)",
          surface_role: "BASE_REGION",
          origin: "derived",
          render: "polygon",
          depends: ["A", "B", "C"],
          vertex_ids: ["A", "B", "C"],
          vertices: [["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]],
        },
        {
          id: "sa",
          type: "segment3",
          label: "Cạnh bên SA",
          notation: "SA",
          formation_roles: ["CONSTRUCT_HEIGHT"],
          origin: "derived",
          render: "segment",
          depends: ["S", "A"],
          endpoint_ids: ["S", "A"],
          point_a: ["0", "0", "4"],
          point_b: ["0", "0", "0"],
          perpendicular_witness: {
            certificate: "exact-gram-line-plane-orthogonality/1",
            relation: "line_perp_plane",
            status: "ENGINE_VERIFIED",
            from: "S",
            foot_id: "A",
            foot: ["0", "0", "0"],
            on: "day",
            plane_directions: [["2", "0", "0"], ["0", "2", "0"]],
            can_present_as_proven: true,
            marker: { u: ["2", "0", "0"], v: ["0", "0", "4"] },
          },
        },
        {
          id: "chop",
          type: "solid",
          label: "Hình chóp S.ABC",
          notation: "S.ABC",
          shape_class: "PYRAMID_LIKE",
          origin: "derived",
          render: "mesh",
          depends: ["A", "B", "C", "S"],
          vertex_ids: ["S", "A", "B", "C"],
          vertices: [["0", "0", "4"], ["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]],
          faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]],
        },
        // Symbolic given quantities where `.value` holds normalized scalar at a = 1 ("2", "4") and `.symbolic` holds source expression ("2a", "4a")
        {
          id: "q_ab",
          type: "quantity",
          label: "Độ dài AB",
          notation: "AB",
          origin: "free",
          render: "readout",
          depends: ["A", "B"],
          value: "2",
          symbolic: "2a",
          source: { fact_id: "f_ab", provenance: "GIVEN", is_given: true },
          annotation: { kind: "length", role: "given", anchor: "segment", subject_ids: ["A", "B"] },
        },
        {
          id: "q_sa",
          type: "quantity",
          label: "Chiều cao SA",
          notation: "SA",
          origin: "free",
          render: "readout",
          depends: ["S", "A"],
          value: "4",
          symbolic: "4a",
          source: { fact_id: "f_sa", provenance: "GIVEN", is_given: true },
          annotation: { kind: "length", role: "given", anchor: "segment", subject_ids: ["S", "A"] },
        },
        // Unverified / illustrative AC length at a = 1 -> MUST NOT leak as GIVEN anywhere!
        {
          id: "q_ac_illus",
          type: "quantity",
          label: "Độ dài AC minh họa",
          notation: "AC",
          origin: "free",
          render: "readout",
          depends: ["A", "C"],
          value: "2",
          symbolic: "2a",
          source: { provenance: "ILLUSTRATIVE_CHOICE", assumption: "ILLUSTRATIVE_CONFIGURATION", is_given: false },
          annotation: { kind: "length", role: "given", anchor: "segment", subject_ids: ["A", "C"] },
        },
        // Unlisted free quantity omitted from scene.free_objects (point-only free_objects) and lacking authoritative source -> MUST NOT leak as GIVEN even if annotation.role claims "given"!
        {
          id: "q_bc_unlisted",
          type: "quantity",
          label: "Độ dài BC chưa chứng thực",
          notation: "BC",
          origin: "free",
          render: "readout",
          depends: ["B", "C"],
          value: "2√2",
          annotation: { kind: "length", role: "given", anchor: "segment", subject_ids: ["B", "C"] },
        },
        // Derived goal quantity with symbolic expression
        {
          id: "q_h",
          type: "quantity",
          label: "Khoảng cách từ S đến (ABC)",
          notation: "d(S, (ABC))",
          origin: "derived",
          render: "readout",
          depends: ["S", "day"],
          value: "4",
          symbolic: "4a",
          source: { instruction: "measure.distance" },
          annotation: {
            kind: "distance",
            role: "result",
            anchor: "witness",
            subject_ids: ["S", "day"],
            witness: {
              from: "S",
              on: "day",
              foot: ["0", "0", "0"],
              marker: { u: ["2", "0", "0"], v: ["0", "0", "4"] },
            },
          },
        },
      ] as unknown as SceneObject[],
      events: [
        { step_index: 0, action: "CREATE", object: "day", depends: ["A", "B", "C"], explanation: "" },
        { step_index: 1, action: "CREATE", object: "sa", depends: ["S", "A", "day"], explanation: "" },
        { step_index: 2, action: "CREATE", object: "chop", depends: ["A", "B", "C", "S"], explanation: "" },
        { step_index: 3, action: "MEASURE", object: "q_h", depends: ["S", "day"], explanation: "" },
      ],
    };

    const plan = buildPedagogicalConstructionPlan(withSubEntities(sabcScene));
    const disp = registerExactSceneOrigin(veKhongGian(plan.scene), plan.scene);

    // 1A. ABC is NEVER promoted to "vuông cân" / "vuông" / "cân" despite coordinates (0,0,0)-(2,0,0)-(0,2,0)
    const baseObj = disp.objects.find((o) => o.id === "day")!;
    const baseShape = classifyPolygonShapeWithProvenance(disp, baseObj);
    expect(baseShape.certifiedShape).toBeNull();
    for (const st of plan.steps) {
      expect(st.title).not.toMatch(/vuông\s*cân|tam\s+giác\s+vuông|tam\s+giác\s+cân|AC\s*=\s*AB/iu);
      expect(st.subtitle).not.toMatch(/vuông\s*cân|tam\s+giác\s+vuông|tam\s+giác\s+cân|AC\s*=\s*AB/iu);
    }

    // 1B. Symbolic expressions "2a" and "4a" preserved in GoalCompletionSummary (never silently degraded to "4")
    expect(plan.goalCompletion.items.find((it) => it.id === "q_h")?.valueText).toBe("4a");

    // 1C. `phanTichToanHocCuaCanh` rejects illustrative `q_ac_illus` AND unlisted `q_bc_unlisted` AND never promotes `a = 1` to GIVEN_DIMENSION
    const analysis = phanTichToanHocCuaCanh(disp);
    expect(analysis.givenDimensions.map((g) => `${g.notation}=${g.valueDisplay}`)).toEqual([
      "AB=2a",
      "SA=4a",
    ]);

    const structuralOnlySymbolicScene: Scene3D = {
      ...sabcScene,
      free_objects: ["A", "B", "C", "S"],
      objects: sabcScene.objects.filter((o) => o.type !== "quantity"),
      events: sabcScene.events.filter((e) => e.action !== "MEASURE"),
    };
    const structuralAnalysis = phanTichToanHocCuaCanh(structuralOnlySymbolicScene);
    // `length_unit.is_given === false` MUST NOT be pushed into `givenDimensions` as a GIVEN_DIMENSION!
    expect(structuralAnalysis.givenDimensions).toEqual([]);

    // 1D. Full AxoWorkspaceV62 render: shows AB = 2a and SA = 4a, NEVER shows AC = 2a or BC = 2√2 on canvas or Study Dock
    const qBcUnlisted = sabcScene.objects.find((o) => o.id === "q_bc_unlisted")!;
    expect(classifyQuantityProvenance(qBcUnlisted, sabcScene)).toBe("UNVERIFIED");
    expect(classifyQuantityProvenance(qBcUnlisted, { ...sabcScene, free_objects: [] })).toBe("UNVERIFIED");
    expect(classifyQuantityProvenance(disp.objects.find((o) => o.id === "q_bc_unlisted")!, disp)).toBe("UNVERIFIED");
    const wsHtml = renderToString(
      <AxoWorkspaceV62
        scene={sabcScene}
        de="Cho hình chóp S.ABC có SA vuông góc với (ABC), AB = 2a, SA = 4a."
        tieuDe="Hình chóp S.ABC"
      />,
    );
    expect(wsHtml).toContain("AB = 2a");
    expect(wsHtml).toContain("SA = 4a");
    expect(wsHtml).not.toContain("AC = 2a");
    expect(wsHtml).not.toContain("BC = 2√2");
  });

  it("2. §2 & §9: Hybrid Adapter /4 `source_provenance` (`segment_length`, `regular_polygon.side`) surfaces certified GIVEN dimensions on canvas & Study Dock without mutating `envelope.scene3d`, and respects `Thông số hình học` toggle", () => {
    const rawHybridPayload = {
      schema_version: HYBRID_SIMULATION_SCHEMA,
      envelope: {
        status: "ok",
        domain: "geometry",
        simulation_id: "generic.semantic_program",
        title: "Hình chóp S.ABCD",
        description: "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA vuông góc với đáy và SA = 4a.",
        config: {},
        scene3d: {
          chart_metric: [
            ["1", "0", "0"],
            ["0", "1", "0"],
            ["0", "0", "1"],
          ],
          length_unit: { symbol: "a", display_scale: "a = 1 đơn vị dựng", is_given: false },
          free_objects: ["A", "B", "C", "D", "S"],
          objects: [
            { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
            { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["1", "0", "0"] },
            { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point_marker", depends: [], xyz: ["1", "1", "0"] },
            { id: "D", type: "point3", label: "D", notation: "D", origin: "free", render: "point_marker", depends: [], xyz: ["0", "1", "0"] },
            { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "2"] },
            {
              id: "chop",
              type: "solid",
              label: "Hình chóp S.ABCD",
              notation: "S.ABCD",
              shape_class: "PYRAMID_LIKE",
              origin: "derived",
              render: "mesh",
              depends: ["A", "B", "C", "D", "S"],
              vertex_ids: ["S", "A", "B", "C", "D"],
              vertices: [["0", "0", "2"], ["0", "0", "0"], ["1", "0", "0"], ["1", "1", "0"], ["0", "1", "0"]],
              faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]],
            },
          ],
          events: [{ step_index: 0, action: "CREATE", object: "chop", depends: ["A", "B", "C", "D", "S"] }],
        },
      },
      route_d: {
        schema_version: HYBRID_SIMULATION_SCHEMA,
        adapter_version: HYBRID_SIMULATION_ADAPTER,
        contract_version: "typed-fact-next/2",
        status: "SERVED",
        refusal: null,
        source_verification: { authority: "registry.kiem_nguon", verified: true },
        length_unit: "a",
        sections: [],
        answers: {},
        answer_exact: {},
        observations: {},
        planner: { trace: [], goal_checks: {}, negated_checks: {} },
        source_provenance: [
          {
            id: "p1",
            fn: "regular_polygon",
            args: { vertices: ["A", "B", "C", "D"], side: "2a" },
            quotes: ["Đáy ABCD là hình vuông cạnh 2a"],
          },
          {
            id: "p2",
            fn: "segment_length",
            args: { segment: ["S", "A"], value: "4a" },
            quotes: ["SA = 4a"],
          },
        ],
      },
    };

    const parsed = docPhanHoiHybrid(rawHybridPayload);
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;

    const sceneSnapshotBefore = structuredClone(parsed.envelope.scene3d);
    const hv = hybridViewCua(parsed.envelope)!;
    const rawScene = parsed.envelope.scene3d as Scene3D;
    attachHybridViewToScene(rawScene, hv);

    const plan = buildPedagogicalConstructionPlan(withSubEntities(rawScene));
    const disp = registerExactSceneOrigin(veKhongGian(plan.scene), plan.scene);
    const finalAnchor = plan.steps[plan.steps.length - 1]!.anchor;

    // `envelope.scene3d` was NEVER mutated!
    expect(parsed.envelope.scene3d).toEqual(sceneSnapshotBefore);

    const summary = givenQuantitiesSummary(disp, finalAnchor);
    expect(summary.map((s) => s.text)).toEqual(expect.arrayContaining(["AB = 2a", "SA = 4a"]));

    const canvasAnns = annotationsAt(disp, finalAnchor, DEFAULT_ANNOTATION_VIEW, null);
    expect(canvasAnns.map((a) => a.text)).toEqual(expect.arrayContaining(["AB = 2a", "SA = 4a"]));

    // Turning OFF `Thông số hình học` (`hideGiven: true`) hides canvas given labels cleanly
    const hiddenAnns = annotationsAt(disp, finalAnchor, { ...DEFAULT_ANNOTATION_VIEW, hideGiven: true }, null);
    expect(hiddenAnns.filter((a) => a.role === "given")).toEqual([]);
  });

  it("3. §7.3–§7.5 & §8: Cross-family semantic delta, cutting-plane attenuation, dynamic hidden-edge occlusion & zero duplicate visual edges across Pyramids, Prisms, Cylinders, Cones, Spheres & General Archetypes", () => {
    const familyCorpus: { family: string; id: string; scene: Scene3D }[] = [];

    for (const s of GEOMETRY_SAMPLES) {
      familyCorpus.push({
        family: s.group,
        id: `sample:${s.id}`,
        scene: (s.envelope as unknown as { scene3d: Scene3D }).scene3d,
      });
    }

    familyCorpus.push({ family: "section_fixture", id: "fixture:section", scene: sectionRaw as unknown as Scene3D });
    familyCorpus.push({ family: "sphere_circumscribed", id: "fixture:circumsphere", scene: circumsphereRaw as unknown as Scene3D });
    for (const [k, v] of Object.entries(inscribedRaw as Record<string, unknown>)) {
      if (v && typeof v === "object" && "objects" in v) {
        familyCorpus.push({ family: "inscribed_circumscribed", id: `fixture:${k}`, scene: v as Scene3D });
      }
    }
    for (const [k, v] of Object.entries(regressionArchetypesRaw as Record<string, unknown>)) {
      if (v && typeof v === "object" && "objects" in v) {
        familyCorpus.push({ family: "regression_archetype", id: `fixture:${k}`, scene: v as Scene3D });
      }
    }

    // Add Hybrid Adapter /4 served fixtures (covering pyramids + prisms + sections + ratios)
    const hybridPath = path.resolve(
      __dirname,
      "../../../../../docs/evaluation/geometry/runs/hybrid-primary-b1-b2-offline/results/offline/fixtures.json",
    );
    const hybridRows = (JSON.parse(fs.readFileSync(hybridPath, "utf8")) as { fixtures?: Record<string, unknown>[] }).fixtures ?? [];
    for (const row of hybridRows) {
      const res = docPhanHoiHybrid(row);
      if (res.ok && res.envelope.status === "ok" && res.envelope.scene3d) {
        const sc = res.envelope.scene3d as Scene3D;
        attachHybridViewToScene(sc, hybridViewCua(res.envelope));
        familyCorpus.push({ family: "hybrid_v4", id: `hybrid:${String(row.id ?? "")}`, scene: sc });
      }
    }

    expect(familyCorpus.length).toBeGreaterThanOrEqual(25);

    for (const entry of familyCorpus) {
      const plan = buildPedagogicalConstructionPlan(withSubEntities(entry.scene));
      const disp = registerExactSceneOrigin(veKhongGian(plan.scene), plan.scene);
      expect(plan.steps.length, `${entry.id} has >= 1 step`).toBeGreaterThanOrEqual(1);

      // §7.3 Semantic Delta Audit: consecutive steps must NEVER be empty/duplicate render-only clones
      let prevVisible = new Set<string>();
      const seenTargetSignatures = new Set<string>();
      for (let i = 0; i < plan.steps.length; i += 1) {
        const st = plan.steps[i]!;
        expect(st.epistemicCategory, `${entry.id}@step${i + 1} never calculation-only`).not.toBe("conclusion");
        expect(st.targetIds.length, `${entry.id}@step${i + 1} non-empty targetIds`).toBeGreaterThan(0);

        const curVisible = new Set(st.visibleIds);
        const newlyVisible = [...curVisible].filter((id) => !prevVisible.has(id));
        const sig = `${st.epistemicCategory}|${[...st.targetIds].sort().join(",")}`;
        // Every step after step 0 must introduce either new visible entities or a distinct semantic target signature
        if (i > 0) {
          expect(
            newlyVisible.length > 0 || !seenTargetSignatures.has(sig),
            `${entry.id}@step${i + 1} (${st.title}) must have non-empty semantic delta`,
          ).toBe(true);
        }
        seenTargetSignatures.add(sig);
        prevVisible = curVisible;
      }

      // §7.5 Dynamic Edge Occlusion & Zero Duplicate Visual Ownership on polyhedral scenes
      const primarySolid = disp.objects.find((o) => o.type === "solid" && (o.faces?.length ?? 0) >= 4);
      if (primarySolid) {
        const visFront = classifySolidEdgeVisibility(primarySolid, new THREE.Vector3(8, -7, 5));
        const visBack = classifySolidEdgeVisibility(primarySolid, new THREE.Vector3(-8, 7, 5));
        expect(visFront.duplicate_visual_owner_ids, `${entry.id} zero duplicate edges (front)`).toEqual([]);
        expect(visBack.duplicate_visual_owner_ids, `${entry.id} zero duplicate edges (back)`).toEqual([]);
        const frontHidden = [...visFront.hidden_edge_ids, ...visFront.mixed_edge_ids].sort().join(",");
        const backHidden = [...visBack.hidden_edge_ids, ...visBack.mixed_edge_ids].sort().join(",");
        expect(frontHidden === backHidden && frontHidden.length > 0 ? false : true).toBe(true);
      }

      // §7.4 Cutting-plane attenuation after section closure while keeping plane in scene data for `#chk-plane`
      const secObj = disp.objects.find((o) => o.type === "section" || ((o.type === "polygon3" || o.type === "circle3" || o.type === "ellipse3") && o.role?.toLowerCase().includes("thiết diện")));
      const cutPlanes = disp.objects.filter((o) => o.type === "plane3");
      if (secObj && cutPlanes.length > 0 && plan.steps.length >= 2) {
        const finalStep = plan.steps[plan.steps.length - 1]!;
        for (const pl of cutPlanes) {
          // Plane object NEVER deleted from scene.objects
          expect(disp.objects.some((o) => o.id === pl.id)).toBe(true);
          const dec = resolvePlaneSectionVisibility(disp, pl, finalStep.anchor, false, null, finalStep.startAnchor);
          expect(dec.opacityScale).toBeLessThanOrEqual(1);
        }
      }
    }
  });

  it("4. §10 General Pedagogical Sequencer Invariants: invariant to vertex renaming, independent object permutation, uniform coordinate scaling, and multi-goal shared-premise non-duplication", () => {
    const baseSample = GEOMETRY_SAMPLES.find((s) => s.id === "thiet-dien-chop")!;
    const origScene = structuredClone((baseSample.envelope as unknown as { scene3d: Scene3D }).scene3d);
    const origPlan = buildPedagogicalConstructionPlan(withSubEntities(origScene));

    // 4A. Vertex renaming invariance (S -> K, A -> E, B -> F, C -> G, D -> H)
    const renameMap: Record<string, string> = { S: "K", A: "E", B: "F", C: "G", D: "H" };
    const renameTokenString = (s: string): string =>
      s
        .replace(/(?<![A-Za-z0-9])(S|A|B|C|D)(?![A-Za-z0-9])/g, (m) => renameMap[m] ?? m)
        .replace(/ABCD/g, "EFGH")
        .replace(/SAB/g, "KEF")
        .replace(/SBC/g, "KFG")
        .replace(/SCD/g, "KGH")
        .replace(/SDA/g, "KHE")
        .replace(/SAD/g, "KEH")
        .replace(/\bsa\b/g, "ke");
    const deepRenameValue = (val: unknown): unknown => {
      if (typeof val === "string") return renameTokenString(val);
      if (Array.isArray(val)) return val.map(deepRenameValue);
      if (val && typeof val === "object") {
        const out: Record<string, unknown> = {};
        for (const [k, v] of Object.entries(val as Record<string, unknown>)) {
          out[renameTokenString(k)] = deepRenameValue(v);
        }
        return out;
      }
      return val;
    };
    const renamedScene = deepRenameValue(origScene) as Scene3D;
    const renamedPlan = buildPedagogicalConstructionPlan(withSubEntities(renamedScene));
    expect(renamedPlan.steps.length).toBe(origPlan.steps.length);
    expect(renamedPlan.steps.map((s) => s.epistemicCategory)).toEqual(
      origPlan.steps.map((s) => s.epistemicCategory),
    );

    // 4B. Independent free-point object order permutation invariance
    const freePts = origScene.objects.filter((o) => o.type === "point3" && o.origin === "free").reverse();
    const restObjs = origScene.objects.filter((o) => !(o.type === "point3" && o.origin === "free"));
    const permutedScene: Scene3D = {
      ...origScene,
      objects: [...freePts, ...restObjs],
    };
    const permutedPlan = buildPedagogicalConstructionPlan(withSubEntities(permutedScene));
    expect(permutedPlan.steps.length).toBe(origPlan.steps.length);
    expect(permutedPlan.steps.map((s) => s.epistemicCategory)).toEqual(
      origPlan.steps.map((s) => s.epistemicCategory),
    );

    // 4C. Uniform coordinate scale invariance (multiply all coordinates by 3)
    const scaleExact = (v: string) => (v.includes("/") ? `${BigInt(v.split("/")[0]!) * 3n}/${v.split("/")[1]!}` : String(BigInt(v) * 3n));
    const scaleVec = (vec: [string, string, string]): [string, string, string] => [
      scaleExact(vec[0]),
      scaleExact(vec[1]),
      scaleExact(vec[2]),
    ];
    const scaledScene: Scene3D = {
      ...origScene,
      objects: origScene.objects.map((o) => ({
        ...o,
        ...(o.xyz ? { xyz: scaleVec(o.xyz) } : {}),
        ...(o.point ? { point: scaleVec(o.point) } : {}),
        ...(o.point_a ? { point_a: scaleVec(o.point_a) } : {}),
        ...(o.point_b ? { point_b: scaleVec(o.point_b) } : {}),
        ...(o.vertices ? { vertices: o.vertices.map(scaleVec) } : {}),
        ...(o.polygon ? { polygon: o.polygon.map(scaleVec) } : {}),
      })),
    };
    const scaledPlan = buildPedagogicalConstructionPlan(withSubEntities(scaledScene));
    expect(scaledPlan.steps.length).toBe(origPlan.steps.length);
    expect(scaledPlan.steps.map((s) => s.title)).toEqual(origPlan.steps.map((s) => s.title));

    // 4D. Multi-goal configuration sharing premises (`ORDER-goals` in Hybrid corpus) never duplicates construction steps
    const hybridPath = path.resolve(
      __dirname,
      "../../../../../docs/evaluation/geometry/runs/hybrid-primary-b1-b2-offline/results/offline/fixtures.json",
    );
    const hybridRows = (JSON.parse(fs.readFileSync(hybridPath, "utf8")) as { fixtures?: Record<string, unknown>[] }).fixtures ?? [];
    const multiGoalRow = hybridRows.find((r) => r.id === "ORDER-goals");
    expect(multiGoalRow).toBeDefined();
    const multiParsed = docPhanHoiHybrid(multiGoalRow);
    expect(multiParsed.ok).toBe(true);
    if (multiParsed.ok && multiParsed.envelope.scene3d) {
      const mgPlan = buildPedagogicalConstructionPlan(withSubEntities(multiParsed.envelope.scene3d as Scene3D));
      const stepFocusKeys = mgPlan.steps.map((s) => `${s.epistemicCategory}:${[...s.targetIds].sort().join(",")}`);
      expect(new Set(stepFocusKeys).size).toBe(stepFocusKeys.length);
      expect(mgPlan.goalCompletion.items.length).toBeGreaterThanOrEqual(2);
    }

    // 4E. Adversarial Relabeling Invariance WITHOUT `BASE_REGION` and WITH asymmetric ratio `1/3` (`S.ABC` vs `T.DEF`)
    const makeAsymmetricRatioPyramid = (syms: { S: string; A: string; B: string; C: string; M: string }): Scene3D => ({
      free_objects: [syms.A, syms.B, syms.C, syms.S],
      objects: [
        { id: syms.A, type: "point3", label: syms.A, notation: syms.A, origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        { id: syms.B, type: "point3", label: syms.B, notation: syms.B, origin: "free", render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
        { id: syms.C, type: "point3", label: syms.C, notation: syms.C, origin: "free", render: "point_marker", depends: [], xyz: ["0", "3", "0"] },
        { id: syms.S, type: "point3", label: syms.S, notation: syms.S, origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "6"] },
        {
          id: "alt_seg",
          type: "segment3",
          label: `Đường cao ${syms.S}${syms.A}`,
          notation: `${syms.S}${syms.A}`,
          formation_roles: ["CONSTRUCT_HEIGHT"],
          origin: "derived",
          render: "segment",
          depends: [syms.S, syms.A],
          endpoint_ids: [syms.S, syms.A],
          point_a: ["0", "0", "6"],
          point_b: ["0", "0", "0"],
          perpendicular_witness: {
            relation: "line_perp_plane",
            from: syms.S,
            foot_id: syms.A,
            foot: ["0", "0", "0"],
            on: "chop_solid",
            can_present_as_proven: true,
            marker: { u: ["3", "0", "0"], v: ["0", "0", "6"] },
          },
        },
        {
          id: "chop_solid",
          type: "solid",
          label: `Hình chóp ${syms.S}.${syms.A}${syms.B}${syms.C}`,
          notation: `${syms.S}.${syms.A}${syms.B}${syms.C}`,
          shape_class: "PYRAMID_LIKE",
          origin: "derived",
          render: "mesh",
          depends: [syms.A, syms.B, syms.C, syms.S],
          vertex_ids: [syms.A, syms.B, syms.C, syms.S],
          vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "3", "0"], ["0", "0", "6"]],
          faces: [[0, 1, 2], [0, 1, 3], [1, 2, 3], [2, 0, 3]],
        },
        // Deliberately list base vertex FIRST in `depends` (`[A, S]` / `[D, T]`) at 1/3 from apex `(0, 0, 4)`
        {
          id: syms.M,
          type: "point3",
          label: syms.M,
          notation: syms.M,
          origin: "derived",
          render: "point_marker",
          depends: [syms.A, syms.S],
          xyz: ["0", "0", "4"],
        },
      ] as unknown as SceneObject[],
      events: [
        { step_index: 0, action: "INIT", object: null, explanation: "", objects: [syms.A, syms.B, syms.C, syms.S], depends: [] },
        { step_index: 1, action: "CREATE", object: "alt_seg", explanation: "", depends: [syms.S, syms.A] },
        { step_index: 2, action: "CREATE", object: "chop_solid", explanation: "", depends: [syms.A, syms.B, syms.C, syms.S] },
        { step_index: 3, action: "CREATE", object: syms.M, explanation: "", depends: [syms.A, syms.S] },
      ],
    });

    const sabcRatioScene = makeAsymmetricRatioPyramid({ S: "S", A: "A", B: "B", C: "C", M: "M" });
    const tdefRatioScene = makeAsymmetricRatioPyramid({ S: "T", A: "D", B: "E", C: "F", M: "M" });

    const relS = findPointMidpointRelation(sabcRatioScene, sabcRatioScene.objects.find((o) => o.id === "M")!);
    const relT = findPointMidpointRelation(tdefRatioScene, tdefRatioScene.objects.find((o) => o.id === "M")!);
    expect(relS).toEqual({ kind: "ratio", aSym: "S", bSym: "A", ratioFrac: [1n, 3n] });
    expect(relT).toEqual({ kind: "ratio", aSym: "T", bSym: "D", ratioFrac: [1n, 3n] });

    const planS = buildPedagogicalConstructionPlan(withSubEntities(sabcRatioScene));
    const planT = buildPedagogicalConstructionPlan(withSubEntities(tdefRatioScene));
    expect(planT.steps.length).toBe(planS.steps.length);
    const mStepS = planS.steps.find((st) => st.targetIds.includes("M"))!;
    const mStepT = planT.steps.find((st) => st.targetIds.includes("M"))!;
    expect(mStepS.subtitle).toContain("1/3");
    expect(mStepT.subtitle).toContain("1/3");
    expect(mStepT.subtitle).not.toContain("2/3");
  });

  it("5. §7.1–§7.2 Deep Provenance Enforcement Across Readouts, Selection Chains, Object Semantics & Construction Badges", () => {
    const provScene: Scene3D = {
      free_objects: ["A", "q_true_given"],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        {
          id: "P_unlisted_free",
          type: "point3",
          label: "P",
          notation: "P",
          origin: "free",
          render: "point_marker",
          depends: [],
          xyz: ["1", "0", "0"],
        },
        {
          id: "P_illustrative_free",
          type: "point3",
          label: "Q",
          notation: "Q",
          origin: "free",
          render: "point_marker",
          depends: [],
          xyz: ["0", "1", "0"],
          source: { provenance: "ILLUSTRATIVE_CHOICE", is_given: false },
        },
        {
          id: "q_true_given",
          type: "quantity",
          label: "Cạnh a",
          notation: "a",
          origin: "free",
          render: "readout",
          value: "2",
          depends: [],
          source: { provenance: "GIVEN", is_given: true, fact_id: "f_a" },
        },
        {
          id: "q_layout_assumed",
          type: "quantity",
          label: "Đơn vị dựng a = 1",
          notation: "a_unit",
          origin: "free",
          render: "readout",
          value: "1",
          depends: [],
          source: { provenance: "MODEL_ASSUMPTION", is_given: false, assumption: "LAYOUT_DERIVED" },
        },
        {
          id: "q_unlisted_free",
          type: "quantity",
          label: "Hệ số không khai báo",
          notation: "k_unlisted",
          origin: "free",
          render: "readout",
          value: "3",
          depends: [],
        },
        {
          id: "q_result",
          type: "quantity",
          label: "Thể tích V",
          notation: "V",
          origin: "derived",
          render: "readout",
          value: "8",
          annotation: { kind: "volume", category: "result", role: "result", subject_ids: ["A"], anchor: "solid" },
          depends: ["q_true_given", "q_layout_assumed", "q_unlisted_free"],
          dependency_edges: [
            { source_id: "q_true_given", relation: "numerical" },
            { source_id: "q_layout_assumed", relation: "numerical" },
            { source_id: "q_unlisted_free", relation: "numerical" },
          ],
        },
      ] as unknown as SceneObject[],
      events: [
        {
          step_index: 0,
          action: "INIT",
          object: null,
          explanation: "",
          objects: ["A", "P_unlisted_free", "P_illustrative_free", "q_true_given", "q_layout_assumed", "q_unlisted_free"],
          depends: [],
        },
        {
          step_index: 1,
          action: "MEASURE",
          semantic_kind: "FINAL_RESULT",
          explanation: "",
          object: "q_result",
          depends: ["q_true_given", "q_layout_assumed", "q_unlisted_free"],
        },
      ],
    };

    // 5A. solutionAt & quantityChoices NEVER leak uncertified `origin: "free"` quantities into `givens`
    const sol = solutionAt(provScene, 1);
    expect(sol.givens.map((g) => g.id)).toEqual(["q_true_given"]);
    const choices = quantityChoices(provScene, 1);
    expect(choices.givens).toEqual(["q_true_given"]);

    // 5B. tangNhanManh & quantitySources NEVER label uncertified `origin: "free"` quantities as `"du_kien_so"` / `givens`
    const chain = tangNhanManh(provScene, "q_result");
    expect(chain.get("q_true_given")).toBe("du_kien_so");
    expect(chain.get("q_layout_assumed")).toBe("trung_gian");
    expect(chain.get("q_unlisted_free")).toBe("trung_gian");
    expect(quantitySources(provScene, "q_result").givens).toEqual(["q_true_given"]);

    // 5C. classifySceneObjectSemantics enforces strict provenance on `origin: "free"` objects, empty `free_objects`, and `CONSTRUCT_LATERAL_BOUNDARY` segments with illustrative endpoints
    expect(classifySceneObjectSemantics(provScene, provScene.objects[0]!, 0, null, null).epistemicStatus).toBe("given");
    expect(classifySceneObjectSemantics(provScene, provScene.objects[1]!, 0, null, null).epistemicStatus).not.toBe("given");
    expect(classifySceneObjectSemantics(provScene, provScene.objects[2]!, 0, null, null).epistemicStatus).not.toBe("given");
    expect(
      classifySceneObjectSemantics({ ...provScene, free_objects: [] }, provScene.objects[1]!, 0, null, null).epistemicStatus,
    ).not.toBe("given");

    const scLateralWithIllustrativeEndpoint = {
      id: "seg_sc_illus",
      type: "segment3",
      label: "Cạnh bên SC",
      notation: "SC",
      origin: "derived",
      producer: "segment_through",
      render: "segment",
      formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"],
      depends: ["S", "C"],
      endpoint_ids: ["S", "C"],
      point_a: ["0", "0", "4"],
      point_b: ["0", "2", "0"],
    } as unknown as SceneObject;
    const sabcWithSc: Scene3D = {
      free_objects: ["A", "B", "C", "S"],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
        {
          id: "C",
          type: "point3",
          label: "C",
          notation: "C",
          origin: "free",
          render: "point_marker",
          depends: [],
          xyz: ["0", "2", "0"],
          source: { provenance: "ILLUSTRATIVE_CHOICE", assumption: "ILLUSTRATIVE_CONFIGURATION", is_given: false },
        },
        { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
        scLateralWithIllustrativeEndpoint,
      ] as unknown as SceneObject[],
      events: [{ step_index: 0, action: "CREATE", object: "seg_sc_illus", depends: ["S", "C"], explanation: "" }],
    };
    expect(
      classifySceneObjectSemantics(sabcWithSc, scLateralWithIllustrativeEndpoint, 2, null, null).epistemicStatus,
    ).toBe("constructed_result");

    // 5D. Unmodified `tru-truc-xien` sample builds cleanly, while a genuine oblique cylinder (`OO'` not orthogonal to `authoritative: false` horizontal cap circle, WITHOUT doctoring `cyl.source`) marks base circle & curved solid steps as `"constructed"` (never `"given"` / `"Đề cho"`)
    const tiltedRightCylSample = (GEOMETRY_SAMPLES.find((s) => s.id === "tru-truc-xien")!.envelope as unknown as {
      scene3d: Scene3D;
    }).scene3d;
    const tiltedPlan = buildPedagogicalConstructionPlan(withSubEntities(tiltedRightCylSample));
    expect(tiltedPlan.steps.length).toBeGreaterThanOrEqual(2);

    const genuineObliqueCylScene: Scene3D = {
      free_objects: ["O", "O1", "A"],
      objects: [
        { id: "O", type: "point3", label: "O", notation: "O", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        { id: "O1", type: "point3", label: "O'", notation: "O'", origin: "free", render: "point_marker", depends: [], xyz: ["1", "0", "3"] },
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
        {
          id: "cap_bot",
          type: "circle3",
          label: "Đáy dưới (O)",
          notation: "(O)",
          surface_role: "BASE_REGION",
          origin: "derived",
          authoritative: false,
          display_group: ["given"],
          render: "curve",
          depends: ["O", "A"],
          center: ["0", "0", "0"],
          normal: ["0", "0", "1"],
          radius_sq: "4",
        },
        {
          id: "cyl_oblique",
          type: "curved_solid",
          label: "Hình trụ xiên",
          notation: "Hình trụ",
          curved_kind: "cylinder",
          shape_class: "CYLINDER_LIKE",
          origin: "derived",
          render: "mesh",
          depends: ["O", "O1", "A", "cap_bot"],
          center: ["0", "0", "0"],
          axis: ["1", "0", "3"],
          anchor: ["0", "0", "0"],
          apex_or_top: ["1", "0", "3"],
          rim_point: ["2", "0", "0"],
          radius_sq: "4",
          height_sq: "10",
        },
      ] as unknown as SceneObject[],
      events: [
        { step_index: 0, action: "CREATE", object: "cap_bot", depends: ["O", "A"], explanation: "" },
        { step_index: 1, action: "CREATE", object: "cyl_oblique", depends: ["O", "O1", "A", "cap_bot"], explanation: "" },
      ],
    };
    const obliquePlan = buildPedagogicalConstructionPlan(withSubEntities(genuineObliqueCylScene));
    const baseAndSolidSteps = obliquePlan.steps.filter((st) =>
      st.targetIds.some(
        (tid) => tid === "cap_bot" || tid === "cyl_oblique" || tid.endsWith("__base_bot") || tid.endsWith("__base_top"),
      ),
    );
    expect(baseAndSolidSteps.length).toBeGreaterThanOrEqual(2);
    for (const st of baseAndSolidSteps) {
      expect(st.epistemicCategory).toBe("constructed");
      expect(st.categoryLabel).not.toBe("Đề cho");
    }

    // 5D-2. Spoofed `display_group: ["given"]` on derived midpoint, centroid, ratio point, and `authoritative: false` segment NEVER leaks `"given"` / `"Đề cho"` in `buildPedagogicalConstructionPlan`
    const spoofedGroupScene: Scene3D = {
      free_objects: ["A", "B", "C", "S"],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
        { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point_marker", depends: [], xyz: ["0", "3", "0"] },
        { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "3"] },
        {
          id: "day",
          type: "polygon3",
          label: "Đáy ABC",
          notation: "(ABC)",
          surface_role: "BASE_REGION",
          origin: "derived",
          render: "polygon",
          depends: ["A", "B", "C"],
          vertex_ids: ["A", "B", "C"],
          vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "3", "0"]],
        },
        {
          id: "chop",
          type: "solid",
          label: "Hình chóp S.ABC",
          notation: "S.ABC",
          shape_class: "PYRAMID_LIKE",
          origin: "derived",
          render: "mesh",
          depends: ["A", "B", "C", "S"],
          vertex_ids: ["S", "A", "B", "C"],
          vertices: [["0", "0", "3"], ["0", "0", "0"], ["3", "0", "0"], ["0", "3", "0"]],
          faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]],
        },
        {
          id: "M_mid",
          type: "point3",
          label: "Trung điểm M",
          notation: "M",
          origin: "derived",
          display_group: ["given"],
          render: "point_marker",
          depends: ["A", "B"],
          xyz: ["3/2", "0", "0"],
        },
        {
          id: "G_cent",
          type: "point3",
          label: "Trọng tâm G",
          notation: "G",
          origin: "derived",
          display_group: ["given"],
          render: "point_marker",
          depends: ["A", "B", "C"],
          xyz: ["1", "1", "0"],
        },
        {
          id: "N_ratio",
          type: "point3",
          label: "Điểm N trên SA",
          notation: "N",
          origin: "derived",
          display_group: ["given"],
          render: "point_marker",
          depends: ["S", "A"],
          xyz: ["0", "0", "1"],
        },
        {
          id: "seg_nonauth",
          type: "segment3",
          label: "Đoạn nối MN",
          notation: "MN",
          origin: "derived",
          authoritative: false,
          display_group: ["given"],
          render: "segment",
          depends: ["M_mid", "N_ratio"],
          endpoint_ids: ["M_mid", "N_ratio"],
          point_a: ["3/2", "0", "0"],
          point_b: ["0", "0", "1"],
        },
      ] as unknown as SceneObject[],
      events: [
        { step_index: 0, action: "CREATE", object: "day", depends: ["A", "B", "C"], explanation: "" },
        { step_index: 1, action: "CREATE", object: "chop", depends: ["A", "B", "C", "S"], explanation: "" },
        { step_index: 2, action: "CREATE", object: "M_mid", depends: ["A", "B"], explanation: "" },
        { step_index: 3, action: "CREATE", object: "G_cent", depends: ["A", "B", "C"], explanation: "" },
        { step_index: 4, action: "CREATE", object: "N_ratio", depends: ["S", "A"], explanation: "" },
        { step_index: 5, action: "CREATE", object: "seg_nonauth", depends: ["M_mid", "N_ratio"], explanation: "" },
      ],
    };
    const spoofedPlan = buildPedagogicalConstructionPlan(withSubEntities(spoofedGroupScene));
    for (const id of ["M_mid", "G_cent", "N_ratio", "seg_nonauth"]) {
      const stepsForId = spoofedPlan.steps.filter((st) => st.targetIds.includes(id));
      expect(stepsForId.length).toBeGreaterThanOrEqual(1);
      for (const st of stepsForId) {
        expect(st.epistemicCategory).toBe("constructed");
        expect(st.categoryLabel).not.toBe("Đề cho");
      }
    }

    // 5E. Regular pyramid center altitude (`regular_pyramid_center_altitude`) is classified as `"derived"` (theorem-derived), never `"given"`
    const regPyrRow = (
      JSON.parse(
        fs.readFileSync(
          path.resolve(
            __dirname,
            "../../../../../docs/evaluation/geometry/runs/hybrid-primary-b1-b2-offline/results/offline/fixtures.json",
          ),
          "utf8",
        ),
      ) as { fixtures?: Record<string, unknown>[] }
    ).fixtures?.find((r) => String(r.problem_text ?? "").toLowerCase().includes("chóp tứ giác đều"));
    if (regPyrRow) {
      const parsed = docPhanHoiHybrid(regPyrRow);
      if (parsed.ok && parsed.envelope.scene3d) {
        const regPlan = buildPedagogicalConstructionPlan(withSubEntities(parsed.envelope.scene3d as Scene3D));
        const theoremAltSteps = regPlan.steps.filter((st) =>
          st.targetIds.some((tid) => {
            const obj = regPlan.scene.objects.find((o) => o.id === tid);
            return obj?.perpendicular_witness?.rule === "regular_pyramid_center_altitude";
          }),
        );
        for (const st of theoremAltSteps) {
          expect(st.epistemicCategory).toBe("derived");
          expect(st.categoryLabel).not.toBe("Đề cho");
        }
      }
    }
  });
});
