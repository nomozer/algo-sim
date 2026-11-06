import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { attachHybridViewToScene, type Scene3D, type SceneObject } from "./scene3d-model";
import { veKhongGian } from "./scene3d-chart";
import { deriveSectionSubEntities, sectionCycleLabel, sectionDetails, withSubEntities } from "./scene3d-subentities";
import {
  buildPedagogicalConstructionPlan,
  buildStepEntityGroups,
  buildVerifiedObjectTooltip,
  classifyPolygonShapeWithProvenance,
  deriveExactPolygonMathBasis,
  pedagogicalStepList,
} from "./scene3d-semantic-policy";
import { annotationsAt, DEFAULT_ANNOTATION_VIEW, givenQuantitiesSummary } from "./scene3d-annotations";
import {
  docPhanHoiHybrid,
  HYBRID_SIMULATION_ADAPTER,
  HYBRID_SIMULATION_SCHEMA,
  hybridViewCua,
  KHOA_HYBRID_VIEW,
  kiemHybridView,
} from "./hybrid-preview-adapter";

const HYBRID_FIXTURE_FILES = [
  path.resolve(__dirname, "../../../../../docs/evaluation/geometry/runs/hybrid-primary-b1-b2-offline/results/offline/fixtures.json"),
  path.resolve(__dirname, "../../../../../docs/evaluation/geometry/runs/visual-hybrid-integration/integrated/offline/fixtures.json"),
];

describe("AXO Master §13: Repeatable Hybrid Backend <-> Frontend Scene3D Contract Matrix", () => {
  it("1. Preserves invariants across all served Hybrid Adapter /4 fixtures and offline catalog samples (objects, events, formation, quantities, certificates, chart_metric)", () => {
    const servedScenes: { label: string; scene: Scene3D }[] = [];

    for (const fixturePath of HYBRID_FIXTURE_FILES) {
      const parsed = JSON.parse(fs.readFileSync(fixturePath, "utf8")) as { fixtures?: Record<string, unknown>[] };
      const rows = parsed.fixtures ?? [];
      expect(rows.length).toBeGreaterThan(0);

      for (const row of rows) {
        const res = docPhanHoiHybrid(row);
        expect(res.ok, `${path.basename(fixturePath)}:${String(row.id ?? "")}`).toBe(true);
        if (!res.ok) continue;
        if (res.envelope.status === "ok" && res.envelope.scene3d) {
          const scene = res.envelope.scene3d as Scene3D;
          expect(kiemHybridView(res.envelope.hybrid_preview, scene)).toBeNull();
          servedScenes.push({ label: `hybrid:${String(row.id ?? "")}`, scene });
        }
      }
    }

    for (const sample of GEOMETRY_SAMPLES) {
      const scene = (sample.envelope as unknown as { scene3d?: Scene3D }).scene3d;
      if (scene) {
        servedScenes.push({ label: `catalog:${sample.id}`, scene });
      }
    }

    expect(servedScenes.length).toBeGreaterThanOrEqual(20);

    for (const { label, scene } of servedScenes) {
      if (!Array.isArray(scene.objects) || !Array.isArray(scene.events)) continue;

      const expanded = withSubEntities(scene);
      const plan = buildPedagogicalConstructionPlan(expanded);
      const stepList = pedagogicalStepList(plan.scene);

      expect(plan.steps.length, `${label} must produce >= 1 construction step`).toBeGreaterThanOrEqual(1);
      expect(stepList.length, `${label} pedagogicalStepList parity`).toBe(plan.steps.length);

      for (const st of plan.steps) {
        expect(st.epistemicCategory, `${label} no calculation step`).not.toBe("conclusion");
        expect(st.anchor).toBeGreaterThanOrEqual(0);
        expect(st.anchor).toBeLessThan(plan.scene.events.length);
        // [W2-F02] Never concatenate descriptive intersection phrases into compact vertex/edge symbols
        expect(st.title, `${label} broken vertex concatenation`).not.toMatch(/[A-Z′']giao\s+điểm/iu);
        expect(st.subtitle, `${label} broken subtitle concatenation`).not.toMatch(/[A-Z′']giao\s+điểm/iu);
        expect(st.title, `${label} repeated descriptive lateral edge phrase`).not.toMatch(/cạnh bên của .*,.*cạnh bên của /iu);
        // [W2-F01 / W3-F01] Never leak internal translate helper points H/H1 into section cycle names or chips
        expect(st.title, `${label} leaked H/H1 cycle`).not.toMatch(/\(HH1|\(HMH1|\(H1H/u);
        const stGroups = buildStepEntityGroups(plan.scene, st.anchor, { steps: plan.steps });
        for (const chip of stGroups.all) {
          // [W3-F02] Chip labels must never chop Vietnamese words leaving trailing space or single dangling consonant
          expect(chip.shortLabel, `${label} chip trailing space`).not.toMatch(/\s$/u);
          expect(chip.shortLabel, `${label} mid-word chop`).not.toMatch(/của khối [a-zà-ỹ]$/iu);
        }
      }

      // [W2-F03] Multi-solid causality: if scene has a host solid (e.g., S.ABC / S.ABCD) and a derived point M on one of its edges,
      // the host solid MUST close BEFORE M and BEFORE any cut sub-solid (e.g., S.MNP / S.MII1)
      const solidsInPlan = plan.scene.objects.filter((o) => o.type === "solid");
      if (solidsInPlan.length >= 2) {
        const freeSet = new Set(plan.scene.free_objects ?? []);
        const hostSolid = solidsInPlan.find((s) => (s.vertex_ids ?? s.depends ?? []).every((v) => freeSet.has(v)));
        if (hostSolid) {
          const hostCloseIdx = plan.steps.findIndex((st) => st.targetIds.includes(hostSolid.id));
          expect(hostCloseIdx, `${label} host solid ${hostSolid.id} must have a closing step`).toBeGreaterThanOrEqual(0);
          const hostVerts = new Set(hostSolid.vertex_ids ?? hostSolid.depends ?? []);
          for (const pt of plan.scene.objects) {
            if (pt.type !== "point3" || pt.origin !== "derived" || hostVerts.has(pt.id)) continue;
            if ((pt.depends ?? []).length >= 2 && (pt.depends ?? []).every((d) => hostVerts.has(d))) {
              const ptStepIdx = plan.steps.findIndex((st) => st.targetIds.includes(pt.id));
              if (ptStepIdx >= 0) {
                expect(
                  hostCloseIdx,
                  `${label}: host solid ${hostSolid.id} (step ${hostCloseIdx + 1}) must close before edge point ${pt.id} (step ${ptStepIdx + 1})`,
                ).toBeLessThan(ptStepIdx);
              }
            }
          }
        }
      }

      // Transforming with chart_metric (veKhongGian) never crashes or leaks derived result quantities by default
      const transformed = veKhongGian(plan.scene);
      const finalAnns = annotationsAt(transformed, plan.steps[plan.steps.length - 1].anchor, DEFAULT_ANNOTATION_VIEW, null);
      for (const a of finalAnns) {
        expect(a.role, `${label} default annotation must be GIVEN`).toBe("given");
      }
      const summary = givenQuantitiesSummary(transformed, plan.steps[plan.steps.length - 1].anchor);
      expect(Array.isArray(summary)).toBe(true);
    }
  }, 20_000);

  it("2. Handles both `line_perp_plane` and `line_perpendicular_plane` certificate variants plus optional/unknown fields through docPhanHoiHybrid without crashing", () => {
    for (const rel of ["line_perp_plane", "line_perpendicular_plane"] as const) {
      const scene3d: Scene3D = {
        chart_metric: [
          ["1", "0", "0"],
          ["0", "1", "0"],
          ["0", "0", "1"],
        ],
        free_objects: ["A", "B", "C", "S"],
        objects: [
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"], unknown_future_attr: true },
          { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
          { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
          { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "5"] },
          {
            id: "sa_h",
            type: "segment3",
            label: "SA",
            notation: "SA",
            origin: "derived",
            render: "segment",
            depends: ["S", "A"],
            endpoint_ids: ["S", "A"],
            point_a: ["0", "0", "5"],
            point_b: ["0", "0", "0"],
            perpendicular_witness: {
              certificate: "exact-gram-line-plane-orthogonality/1",
              relation: rel,
              status: "ENGINE_VERIFIED",
              from: "S",
              foot_id: "A",
              foot: ["0", "0", "0"],
              on: "chop",
              plane_directions: [["3", "0", "0"], ["0", "4", "0"]],
              can_present_as_proven: true,
              marker: { u: ["3", "0", "0"], v: ["0", "0", "5"] },
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
            vertices: [["0", "0", "5"], ["0", "0", "0"], ["3", "0", "0"], ["0", "4", "0"]],
            faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]],
          },
        ] as unknown as SceneObject[],
        events: [
          { step_index: 0, action: "CREATE", object: "sa_h", depends: ["S", "A"] },
          { step_index: 1, action: "CREATE", object: "chop", depends: ["A", "B", "C", "S"] },
        ],
      } as unknown as Scene3D;

      const payload = {
        schema_version: HYBRID_SIMULATION_SCHEMA,
        future_unknown_top_level_field: { version: "hybrid-next" },
        envelope: {
          status: "ok",
          domain: "geometry",
          simulation_id: "generic.semantic_program",
          title: "Hình chóp S.ABC",
          config: {},
          scene3d,
        },
        route_d: {
          schema_version: HYBRID_SIMULATION_SCHEMA,
          adapter_version: HYBRID_SIMULATION_ADAPTER,
          contract_version: "typed-fact-next/2",
          status: "SERVED",
          refusal: null,
          source_verification: { authority: "registry.kiem_nguon" },
          length_unit: null,
          answers: {},
          answer_exact: {},
          sections: [],
          source_provenance: [
            { id: "r1", fn: "right_angle", args: { vertex: "A", rays: ["B", "C"] }, quotes: ["tam giác ABC vuông tại A"] },
          ],
          planner: { trace: [], goal_checks: {}, negated_checks: {} },
          future_unknown_route_field: ["tolerant"],
        },
      };

      const adapted = docPhanHoiHybrid(payload);
      expect(adapted.ok).toBe(true);
      if (!adapted.ok) continue;

      const adaptedScene = adapted.envelope.scene3d as Scene3D;
      // Without Hybrid source_provenance attached, chart_metric/coordinates alone do NOT promote base ABC (§3.2)
      const unattachedPlan = buildPedagogicalConstructionPlan(withSubEntities(structuredClone(adaptedScene)));
      expect(unattachedPlan.steps[0].title).toBe("Dựng mặt đáy ABC");

      attachHybridViewToScene(adaptedScene, hybridViewCua(adapted.envelope));
      const plan = buildPedagogicalConstructionPlan(withSubEntities(adaptedScene));
      const baseObj = plan.scene.objects.find((o) => o.surface_role === "BASE_REGION")!;
      expect(classifyPolygonShapeWithProvenance(plan.scene, baseObj).certifiedShape).toBe("tam giác vuông");
      expect(plan.steps.map((s) => s.title)).toEqual([
        "Dựng đáy ABC là tam giác vuông",
        "Dựng đường cao SA ⊥ (ABC) tại A",
        "Dựng các cạnh bên SB, SC",
        "Hoàn thiện hình chóp S.ABC",
      ]);

      // Conversely, if source_provenance is absent AND an underdetermined vertex/base is marked ILLUSTRATIVE_CHOICE / ILLUSTRATIVE_CONFIGURATION / MODEL_ASSUMPTION / is_given: false, even WITH chart_metric, base shape is NOT claimed
      for (const uncertSrc of [
        { provenance: "ILLUSTRATIVE_CHOICE", is_given: false },
        { provenance: "ILLUSTRATIVE_CONFIGURATION" },
        { provenance: "MODEL_ASSUMPTION" },
        { is_given: false },
      ]) {
        const uncertScene: Scene3D = {
          ...adaptedScene,
          objects: adaptedScene.objects.map((o) =>
            o.id === "C" ? ({ ...o, source: uncertSrc } as unknown as SceneObject) : o,
          ),
        };
        const uncertPlan = buildPedagogicalConstructionPlan(withSubEntities(uncertScene));
        const uncertBase = uncertPlan.scene.objects.find((o) => o.surface_role === "BASE_REGION")!;
        expect(classifyPolygonShapeWithProvenance(uncertPlan.scene, uncertBase).certifiedShape).toBeNull();
        expect(uncertPlan.steps[0].title).toBe("Dựng mặt đáy ABC");
      }
    }
  });

  it("3. Category B `plane-section-certificate/1` (`ENGINE_DERIVED_SECTION` from Adapter /4) passes `docPhanHoiHybrid` + `kiemHybridView`, while tampered certificates fail-closed", () => {
    const buildCatBPayload = () => ({
      schema_version: HYBRID_SIMULATION_SCHEMA,
      envelope: {
        status: "ok",
        domain: "geometry",
        simulation_id: "generic.semantic_program",
        title: "Thiết diện mặt phẳng song song qua M",
        config: {},
        scene3d: {
          chart_metric: [
            ["1", "0", "0"],
            ["0", "1", "0"],
            ["0", "0", "1"],
          ],
          free_objects: ["A", "B", "C", "S"],
          objects: [
            { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "2"] },
            { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
            { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
            { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
            { id: "M", type: "point3", label: "M", notation: "M", origin: "derived", render: "point_marker", depends: ["S", "A"], xyz: ["0", "0", "1"] },
            { id: "H_aux1", type: "point3", label: "H", origin: "derived", role: "Điểm dựng phụ", render: "point_marker", depends: ["M"], xyz: ["1", "0", "1"] },
            { id: "H_aux2", type: "point3", label: "H1", origin: "derived", role: "Điểm dựng phụ", render: "point_marker", depends: ["M"], xyz: ["0", "1", "1"] },
            {
              id: "khoi_S_ABC",
              type: "solid",
              label: "Hình chóp S.ABC",
              notation: "S.ABC",
              shape_class: "PYRAMID_LIKE",
              origin: "derived",
              render: "mesh",
              depends: ["S", "A", "B", "C"],
              vertex_ids: ["S", "A", "B", "C"],
              vertices: [["0", "0", "2"], ["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]],
              faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]],
            },
            {
              id: "mp_td_sec1",
              type: "plane3",
              label: "(α)",
              notation: "(α)",
              origin: "derived",
              render: "surface",
              formation_roles: ["CONSTRUCT_CUTTING_OBJECT"],
              depends: ["M", "H_aux1", "H_aux2"],
              point: ["0", "0", "1"],
              normal: ["0", "0", "1"],
            },
            {
              id: "td_sec1",
              type: "section",
              label: "Thiết diện bởi (α)",
              origin: "derived",
              render: "section",
              closed: true,
              depends: ["khoi_S_ABC", "mp_td_sec1"],
              polygon: [["0", "0", "1"], ["1", "0", "1"], ["0", "1", "1"]],
              vertex_sources: [
                { kind: "SOLID_EDGE_INTERSECTION", solid_edge_vertex_indices: [0, 1] },
                { kind: "SOLID_EDGE_INTERSECTION", solid_edge_vertex_indices: [0, 2] },
                { kind: "SOLID_EDGE_INTERSECTION", solid_edge_vertex_indices: [0, 3] },
              ],
              endpoint_entities: [
                {
                  entity_id: "section:td_sec1:point:on:khoi_S_ABC::edge:S-A",
                  section_vertex_ordinal: 0,
                  provenance_kind: "SOLID_EDGE_INTERSECTION",
                  anonymous_coordinate_fallback: false,
                },
                {
                  entity_id: "section:td_sec1:point:on:khoi_S_ABC::edge:S-B",
                  section_vertex_ordinal: 1,
                  provenance_kind: "SOLID_EDGE_INTERSECTION",
                  anonymous_coordinate_fallback: false,
                },
                {
                  entity_id: "section:td_sec1:point:on:khoi_S_ABC::edge:S-C",
                  section_vertex_ordinal: 2,
                  provenance_kind: "SOLID_EDGE_INTERSECTION",
                  anonymous_coordinate_fallback: false,
                },
              ],
            },
          ],
          events: [
            { step_index: 0, action: "CREATE", object: "khoi_S_ABC", depends: ["S", "A", "B", "C"], explanation: "" },
            { step_index: 1, action: "CREATE", object: "M", depends: ["S", "A"], explanation: "" },
            { step_index: 2, action: "CREATE", object: "H_aux1", depends: ["M"], explanation: "" },
            { step_index: 3, action: "CREATE", object: "H_aux2", depends: ["M"], explanation: "" },
            { step_index: 4, action: "CREATE", object: "mp_td_sec1", depends: ["M", "H_aux1", "H_aux2"], explanation: "" },
            { step_index: 5, action: "STEP", object: "td_sec1", depends: ["khoi_S_ABC", "mp_td_sec1"], explanation: "" },
          ],
        },
      },
      route_d: {
        schema_version: HYBRID_SIMULATION_SCHEMA,
        adapter_version: HYBRID_SIMULATION_ADAPTER,
        contract_version: "typed-fact-next/2",
        status: "SERVED",
        refusal: null,
        source_verification: { authority: "registry.kiem_nguon" },
        length_unit: null,
        answers: {},
        answer_exact: {},
        sections: [
          {
            certificate_version: "plane-section-certificate/1",
            certificate_category: "ENGINE_DERIVED_SECTION",
            section_id: "sec1",
            section_object_id: "td_sec1",
            solid: "S.ABC",
            solid_object_id: "khoi_S_ABC",
            plane_object_id: "mp_td_sec1",
            plane_points: ["M", "H_aux1", "H_aux2"],
            plane_equation: { normal: ["0", "0", "1"], offset: "1" },
            // Giá trị thật của backend: registry.py `MAT_SONG_SONG` (fixture Axo cũ dùng một chuỗi backend không phát).
            plane_rule: "section(plane through point ∥ plane)",
            through_point: "M",
            plane_relation: { kind: "parallel_plane", through_point: "M", parallel_to: ["A", "B", "C"] },
            declared_boundary: null,
            boundary: [
              "section:td_sec1:point:on:khoi_S_ABC::edge:S-A",
              "section:td_sec1:point:on:khoi_S_ABC::edge:S-B",
              "section:td_sec1:point:on:khoi_S_ABC::edge:S-C",
            ],
            vertices: [
              {
                ordinal: 0,
                entity_id: "section:td_sec1:point:on:khoi_S_ABC::edge:S-A",
                label: "M",
                xyz: ["0", "0", "1"],
                edge: ["S", "A"],
                solid_edge_vertex_indices: [0, 1],
                solid_vertex_index: null,
                t: "1/2",
                source_kind: "SOLID_EDGE_INTERSECTION",
                choice: "reuse_through_point",
                provenance: "THROUGH_POINT_REUSE",
                stated: false,
              },
              {
                ordinal: 1,
                entity_id: "section:td_sec1:point:on:khoi_S_ABC::edge:S-B",
                label: null,
                xyz: ["1", "0", "1"],
                edge: ["S", "B"],
                solid_edge_vertex_indices: [0, 2],
                solid_vertex_index: null,
                t: "1/2",
                source_kind: "SOLID_EDGE_INTERSECTION",
                choice: "engine_derived_edge_cut",
                provenance: "ENGINE_DERIVED_EDGE_CUT",
                stated: false,
              },
              {
                ordinal: 2,
                entity_id: "section:td_sec1:point:on:khoi_S_ABC::edge:S-C",
                label: null,
                xyz: ["0", "1", "1"],
                edge: ["S", "C"],
                solid_edge_vertex_indices: [0, 3],
                solid_vertex_index: null,
                t: "1/2",
                source_kind: "SOLID_EDGE_INTERSECTION",
                choice: "engine_derived_edge_cut",
                provenance: "ENGINE_DERIVED_EDGE_CUT",
                stated: false,
              },
            ],
            closure_certificate: {
              verified: true,
              version: "plane-section-certificate/1",
              // Hằng thật của backend: engine.py `PLANE_SECTION_CERTIFICATE_RULE` / `_PRODUCER`.
              rule: "engine_derived_plane_section",
              producer: "engine.kiem_chung_chi_thiet_dien",
              boundary: [
                "section:td_sec1:point:on:khoi_S_ABC::edge:S-A",
                "section:td_sec1:point:on:khoi_S_ABC::edge:S-B",
                "section:td_sec1:point:on:khoi_S_ABC::edge:S-C",
              ],
              polygon: [["0", "0", "1"], ["1", "0", "1"], ["0", "1", "1"]],
              area_squared: "1/4",
            },
          },
        ],
        planner: { trace: [], goal_checks: {}, negated_checks: {} },
      },
    });

    const valid = docPhanHoiHybrid(buildCatBPayload());
    expect(valid.ok).toBe(true);
    if (valid.ok) {
      const scene = valid.envelope.scene3d as Scene3D;
      expect(kiemHybridView(valid.envelope[KHOA_HYBRID_VIEW], scene)).toBeNull();
    }

    // Tamper 1: falsely claiming `stated: true` on an engine-derived edge cut MUST fail-closed
    const tamperedStated = buildCatBPayload();
    tamperedStated.route_d.sections[0].vertices[1].stated = true;
    expect(docPhanHoiHybrid(tamperedStated).ok).toBe(false);

    // Tamper 2: mismatched boundary entity_id MUST fail-closed
    const tamperedBoundary = buildCatBPayload();
    tamperedBoundary.route_d.sections[0].boundary[1] = "forged_vertex_N";
    expect(docPhanHoiHybrid(tamperedBoundary).ok).toBe(false);
  });

  it("4. [W2-F01] Category B `prism-parallel-base-plane-only` never leaks coincident internal translate points `H`, `H1` into section titles, subtitles, or Study Dock chips", () => {
    const prismCatBScene: Scene3D = {
      chart_metric: [
        ["1", "1/2", "0"],
        ["1/2", "1", "0"],
        ["0", "0", "4"],
      ],
      free_objects: ["A", "B", "C", "A_prime", "B_prime", "C_prime"],
      objects: [
        { id: "A", type: "point3", label: "Điểm A", notation: "A", role: "Điểm", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"], source: { provenance: "LAYOUT_DERIVED" } },
        { id: "B", type: "point3", label: "Điểm B", notation: "B", role: "Điểm", origin: "free", render: "point_marker", depends: [], xyz: ["1", "0", "0"], source: { provenance: "LAYOUT_DERIVED" } },
        { id: "C", type: "point3", label: "Điểm C", notation: "C", role: "Điểm", origin: "free", render: "point_marker", depends: [], xyz: ["0", "1", "0"], source: { provenance: "LAYOUT_DERIVED" } },
        { id: "A_prime", type: "point3", label: "Điểm A′", notation: "A′", role: "Điểm", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "1"], source: { provenance: "LAYOUT_DERIVED" } },
        { id: "B_prime", type: "point3", label: "Điểm B′", notation: "B′", role: "Điểm", origin: "free", render: "point_marker", depends: [], xyz: ["1", "0", "1"], source: { provenance: "LAYOUT_DERIVED" } },
        { id: "C_prime", type: "point3", label: "Điểm C′", notation: "C′", role: "Điểm", origin: "free", render: "point_marker", depends: [], xyz: ["0", "1", "1"], source: { provenance: "LAYOUT_DERIVED" } },
        {
          id: "khoi_ABC_A_primeB_primeC_prime",
          type: "solid",
          label: "Lăng trụ đứng ABC.A′B′C′",
          notation: "ABC.A′B′C′",
          shape_class: "PRISM_LIKE",
          origin: "derived",
          render: "mesh",
          formation_roles: ["CLOSE_SOLID"],
          depends: ["A", "A_prime", "B", "B_prime", "C", "C_prime"],
          vertex_ids: ["A", "B", "C", "A_prime", "B_prime", "C_prime"],
          vertices: [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"], ["1", "0", "1"], ["0", "1", "1"]],
          faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]],
        },
        { id: "M", type: "point3", label: "M", notation: "M", role: "Trung điểm của A và A′", origin: "derived", render: "point_marker", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], depends: ["A", "A_prime"], xyz: ["0", "0", "1/2"], source: { instruction: "construct_point.midpoint" } },
        { id: "derived_H_vec", type: "vector3", label: "Vectơ từ A đến B", notation: "AB", origin: "derived", render: "non_visual", depends: ["A", "B"], source: { instruction: "vector_from_points" } },
        { id: "H", type: "point3", label: "H", notation: "H", role: "Ảnh của M qua phép tịnh tiến theo AB", origin: "derived", render: "point_marker", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], depends: ["M", "derived_H_vec"], xyz: ["1", "0", "1/2"], source: { instruction: "construct_point.translate" } },
        { id: "derived_H1_vec", type: "vector3", label: "Vectơ từ A đến C", notation: "AC", origin: "derived", render: "non_visual", depends: ["A", "C"], source: { instruction: "vector_from_points" } },
        { id: "H1", type: "point3", label: "H1", notation: "H1", role: "Ảnh của M qua phép tịnh tiến theo AC", origin: "derived", render: "point_marker", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], depends: ["M", "derived_H1_vec"], xyz: ["0", "1", "1/2"], source: { instruction: "construct_point.translate" } },
        { id: "mp_td_sec", type: "plane3", label: "(α)", notation: "(α)", role: "Mặt phẳng qua M và song song với (ABC)", origin: "derived", render: "surface", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: ["H", "H1", "M"], point: ["0", "0", "1/2"], normal: ["0", "0", "1"] },
        {
          id: "td_sec",
          type: "section",
          label: "Thiết diện bởi (α)",
          origin: "derived",
          render: "polygon",
          closed: true,
          depends: ["khoi_ABC_A_primeB_primeC_prime", "mp_td_sec"],
          polygon: [["1", "0", "1/2"], ["0", "0", "1/2"], ["0", "1", "1/2"]],
          steps: [
            { a: ["1", "0", "1/2"], b: ["0", "0", "1/2"], face_index: 2 },
            { a: ["0", "0", "1/2"], b: ["0", "1", "1/2"], face_index: 4 },
            { a: ["0", "1", "1/2"], b: ["1", "0", "1/2"], face_index: 3 },
          ],
          vertex_sources: [
            { kind: "SOLID_EDGE_INTERSECTION", solid_edge_vertex_indices: [1, 4] },
            { kind: "SOLID_EDGE_INTERSECTION", solid_edge_vertex_indices: [0, 3] },
            { kind: "SOLID_EDGE_INTERSECTION", solid_edge_vertex_indices: [2, 5] },
          ],
        },
        { id: "day_ABC", type: "polygon3", label: "Đáy dưới ABC", notation: "ABC", origin: "derived", render: "polygon", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C"], polygon: [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"]] },
        { id: "day_A_primeB_primeC_prime", type: "polygon3", label: "Đáy trên A′B′C′", notation: "A′B′C′", origin: "derived", render: "polygon", formation_roles: ["CONSTRUCT_TRANSLATED_FACE"], depends: ["A_prime", "B_prime", "C_prime"], polygon: [["0", "0", "1"], ["1", "0", "1"], ["0", "1", "1"]] },
        { id: "canh_ben_A_A_prime", type: "segment3", label: "Cạnh bên AA′", notation: "AA′", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["A", "A_prime"], endpoints: [["0", "0", "0"], ["0", "0", "1"]] },
        { id: "canh_ben_B_B_prime", type: "segment3", label: "Cạnh bên BB′", notation: "BB′", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["B", "B_prime"], endpoints: [["1", "0", "0"], ["1", "0", "1"]] },
        { id: "canh_ben_C_C_prime", type: "segment3", label: "Cạnh bên CC′", notation: "CC′", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["C", "C_prime"], endpoints: [["0", "1", "0"], ["0", "1", "1"]] },
      ] as unknown as SceneObject[],
      events: [
        { step_index: 0, action: "INIT" },
        { step_index: 1, action: "CREATE", object: "day_ABC", depends: ["A", "B", "C"] },
        { step_index: 2, action: "CREATE", object: "day_A_primeB_primeC_prime", depends: ["A_prime", "B_prime", "C_prime"] },
        { step_index: 3, action: "CREATE", objects: ["canh_ben_A_A_prime", "canh_ben_B_B_prime", "canh_ben_C_C_prime"] },
        { step_index: 4, action: "CREATE", object: "khoi_ABC_A_primeB_primeC_prime", depends: ["A", "B", "C", "A_prime", "B_prime", "C_prime"] },
        { step_index: 5, action: "CREATE", object: "M", depends: ["A", "A_prime"] },
        { step_index: 6, action: "MEASURE", object: "derived_H_vec", depends: ["A", "B"] },
        { step_index: 7, action: "CREATE", object: "H", depends: ["M", "derived_H_vec"] },
        { step_index: 8, action: "MEASURE", object: "derived_H1_vec", depends: ["A", "C"] },
        { step_index: 9, action: "CREATE", object: "H1", depends: ["M", "derived_H1_vec"] },
        { step_index: 10, action: "CREATE", object: "mp_td_sec", depends: ["M", "H", "H1"] },
        { step_index: 11, action: "EXTEND", object: "td_sec", depends: ["khoi_ABC_A_primeB_primeC_prime", "mp_td_sec"] },
        { step_index: 12, action: "EXTEND", object: "td_sec", depends: ["khoi_ABC_A_primeB_primeC_prime", "mp_td_sec"] },
        { step_index: 13, action: "EXTEND", object: "td_sec", depends: ["khoi_ABC_A_primeB_primeC_prime", "mp_td_sec"] },
        { step_index: 14, action: "STEP", object: "td_sec", depends: ["khoi_ABC_A_primeB_primeC_prime", "mp_td_sec"] },
      ] as unknown as Scene3D["events"],
    };

    const plan = buildPedagogicalConstructionPlan(withSubEntities(prismCatBScene));
    const joinedSteps = plan.steps.map((s) => `${s.title} :: ${s.subtitle}`).join("\n");
    expect(joinedSteps).not.toMatch(/HH1|HM|MH1|\bH1\b/u);
    const finalStep = plan.steps[plan.steps.length - 1];
    expect(finalStep.title).toBe("Dựng các giao tuyến và hoàn thiện thiết diện tạo bởi (α)");

    for (const st of plan.steps) {
      const stGroups = buildStepEntityGroups(plan.scene, st.anchor, { steps: plan.steps });
      expect(stGroups.all.map((c) => c.shortLabel), `step ${st.index + 1} (${st.title}) leaked H`).not.toContain("H");
      expect(stGroups.all.map((c) => c.shortLabel), `step ${st.index + 1} (${st.title}) leaked H1`).not.toContain("H1");
      expect(stGroups.all.map((c) => c.shortLabel)).not.toContain("Thiết diện (HH1M)");
    }

    const groups = buildStepEntityGroups(plan.scene, finalStep.anchor, { steps: plan.steps });
    expect(groups.primary.map((c) => c.shortLabel)).toEqual(["Thiết diện (α)"]);

    const secObj = plan.scene.objects.find((o) => o.id === "td_sec")!;
    expect(sectionCycleLabel(plan.scene, "td_sec")).toBeNull();
    expect(sectionDetails(plan.scene, "td_sec")?.cycleLabel).toBeNull();
    const secEdges = deriveSectionSubEntities(prismCatBScene).filter((s) => s.parent === "td_sec" && s.type === "edge");
    expect(secEdges.map((e) => e.label)).toEqual(["Cạnh 1", "Cạnh 2", "Cạnh 3"]);
    for (const e of secEdges) {
      expect(e.depends).not.toContain("H");
      expect(e.depends).not.toContain("H1");
    }
    const basis = deriveExactPolygonMathBasis(plan.scene, secObj);
    expect(basis?.summary ?? "").not.toMatch(/HH1|HM|MH1|\bH1\b/u);
    const planeTip = buildVerifiedObjectTooltip(plan.scene, "mp_td_sec", finalStep.anchor);
    expect(`${planeTip?.header ?? ""} ${planeTip?.body ?? ""}`).not.toMatch(/HH1|\bH1\b|\bH,/u);
    const secTip = buildVerifiedObjectTooltip(plan.scene, "td_sec", finalStep.anchor);
    expect(`${secTip?.header ?? ""} ${secTip?.body ?? ""}`).not.toMatch(/HH1|HM|MH1|\bH1\b/u);
  });

  it("5. [W2-F02 + W2-F03 + W2-m01] Multi-solid cut pyramid with unnamed intersections preserves causal order (host solid before M and sub-solid), clean Vietnamese narration, and multi-dep centroid recognition", () => {
    const twoSolidScene: Scene3D = {
      chart_metric: [
        ["1", "0", "0"],
        ["0", "1", "0"],
        ["0", "0", "1"],
      ],
      free_objects: ["S", "A", "B", "C"],
      objects: [
        { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "2"] },
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
        { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
        { id: "day_ABC", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "derived", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C"], polygon: [["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]] },
        {
          id: "canh_SA",
          type: "segment3",
          label: "Cạnh bên SA",
          notation: "SA",
          origin: "derived",
          render: "segment",
          formation_roles: ["CONSTRUCT_HEIGHT", "CONSTRUCT_LATERAL_BOUNDARY"],
          depends: ["S", "A"],
          endpoints: [["0", "0", "2"], ["0", "0", "0"]],
          perpendicular_witness: {
            certificate: "exact-gram-line-plane-orthogonality/1",
            relation: "line_perpendicular_plane",
            status: "ENGINE_VERIFIED",
            from: "S",
            foot_id: "A",
            foot: ["0", "0", "0"],
            on: "day_ABC",
            can_present_as_proven: true,
          },
        },
        { id: "canh_SB", type: "segment3", label: "Cạnh bên SB", notation: "SB", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["S", "B"], endpoints: [["0", "0", "2"], ["2", "0", "0"]] },
        { id: "canh_SC", type: "segment3", label: "Cạnh bên SC", notation: "SC", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["S", "C"], endpoints: [["0", "0", "2"], ["0", "2", "0"]] },
        {
          id: "khoi_S_ABC",
          type: "solid",
          label: "Hình chóp S.ABC",
          notation: "S.ABC",
          shape_class: "PYRAMID_LIKE",
          origin: "derived",
          render: "mesh",
          formation_roles: ["CLOSE_SOLID"],
          depends: ["S", "A", "B", "C"],
          vertex_ids: ["S", "A", "B", "C"],
          vertices: [["0", "0", "2"], ["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]],
          faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]],
        },
        { id: "M", type: "point3", label: "M", notation: "M", origin: "derived", render: "point_marker", depends: ["S", "A"], xyz: ["0", "0", "1"] },
        { id: "mp_alpha", type: "plane3", label: "(α)", notation: "(α)", role: "Mặt phẳng qua M và song song với (ABC)", origin: "derived", render: "surface", formation_roles: ["CONSTRUCT_CUTTING_OBJECT"], depends: ["M"], point: ["0", "0", "1"], normal: ["0", "0", "1"] },
        { id: "line_sb", type: "line3", label: "SB", notation: "SB", origin: "derived", render: "non_visual", depends: ["S", "B"], point: ["0", "0", "2"], direction: ["2", "0", "-2"] },
        { id: "line_sc", type: "line3", label: "SC", notation: "SC", origin: "derived", render: "non_visual", depends: ["S", "C"], point: ["0", "0", "2"], direction: ["0", "2", "-2"] },
        { id: "cut_sb", type: "point3", label: "Giao điểm của SB và (α)", origin: "derived", render: "point_marker", depends: ["line_sb", "mp_alpha"], xyz: ["1", "0", "1"] },
        { id: "cut_sc", type: "point3", label: "Giao điểm của SC và (α)", origin: "derived", render: "point_marker", depends: ["line_sc", "mp_alpha"], xyz: ["0", "1", "1"] },
        {
          id: "khoi_cat",
          type: "solid",
          label: "Khối chóp đỉnh S cắt bởi (α)",
          shape_class: "PYRAMID_LIKE",
          origin: "derived",
          render: "mesh",
          formation_roles: ["CLOSE_SOLID"],
          depends: ["S", "M", "cut_sb", "cut_sc"],
          vertex_ids: ["S", "M", "cut_sb", "cut_sc"],
          vertices: [["0", "0", "2"], ["0", "0", "1"], ["1", "0", "1"], ["0", "1", "1"]],
          faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]],
        },
        { id: "mid_bc", type: "point3", label: "Trung điểm BC", origin: "derived", render: "point_marker", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], depends: ["B", "C"], xyz: ["1", "1", "0"] },
        { id: "med_a", type: "segment3", label: "Trung tuyến", origin: "derived", render: "segment", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], depends: ["A", "mid_bc"], endpoints: [["0", "0", "0"], ["1", "1", "0"]] },
        { id: "G", type: "point3", label: "G", notation: "G", origin: "derived", render: "point_marker", depends: ["A", "B", "C", "mid_bc", "med_a"], xyz: ["2/3", "2/3", "0"] },
      ] as unknown as SceneObject[],
      events: [
        { step_index: 0, action: "CREATE", object: "day_ABC", depends: ["A", "B", "C"] },
        { step_index: 1, action: "CREATE", object: "canh_SA", depends: ["S", "A"] },
        { step_index: 2, action: "CREATE", objects: ["canh_SB", "canh_SC"] },
        { step_index: 3, action: "CREATE", object: "khoi_S_ABC", depends: ["S", "A", "B", "C"] },
        { step_index: 4, action: "CREATE", object: "M", depends: ["S", "A"] },
        { step_index: 5, action: "CREATE", object: "mp_alpha", depends: ["M"] },
        { step_index: 6, action: "CREATE", object: "cut_sb", depends: ["line_sb", "mp_alpha"] },
        { step_index: 7, action: "CREATE", object: "cut_sc", depends: ["line_sc", "mp_alpha"] },
        { step_index: 8, action: "CREATE", object: "khoi_cat", depends: ["S", "M", "cut_sb", "cut_sc"] },
        { step_index: 9, action: "CREATE", object: "mid_bc", depends: ["B", "C"] },
        { step_index: 10, action: "CREATE", object: "med_a", depends: ["A", "mid_bc"] },
        { step_index: 11, action: "CREATE", object: "G", depends: ["A", "B", "C", "mid_bc", "med_a"] },
      ] as unknown as Scene3D["events"],
    };

    const plan = buildPedagogicalConstructionPlan(withSubEntities(twoSolidScene));
    const idxHost = plan.steps.findIndex((s) => s.targetIds.includes("khoi_S_ABC"));
    const idxM = plan.steps.findIndex((s) => s.targetIds.includes("M"));
    const idxSub = plan.steps.findIndex((s) => s.targetIds.includes("khoi_cat"));
    expect(idxHost).toBeGreaterThanOrEqual(0);
    expect(idxHost).toBeLessThan(idxM);
    expect(idxM).toBeLessThan(idxSub);

    const gStep = plan.steps.find((s) => s.targetIds.includes("G"));
    expect(gStep?.title).toBe("Xác định trọng tâm G của tam giác ABC");

    for (const s of plan.steps) {
      expect(s.title).not.toMatch(/[A-Z′']giao\s+điểm/iu);
      expect(s.subtitle).not.toMatch(/[A-Z′']giao\s+điểm/iu);
      expect(s.title).not.toMatch(/cạnh bên của .*,.*cạnh bên của /iu);
      expect(s.subtitle).not.toMatch(/khối\s+Khối/u);
      const chips = buildStepEntityGroups(plan.scene, s.anchor, { steps: plan.steps }).all.map((c) => c.shortLabel);
      for (const ch of chips) {
        expect(ch).not.toMatch(/\s$/u);
        expect(ch).not.toMatch(/của khối [a-zà-ỹ]$/iu);
      }
    }

    // [W3-F02] A 4-vertex base with 3 named vertices (M, N, Q) and 1 unnamed intersection (cut_sc) must NEVER be mislabeled as triangle "MNQ"
    const quadPartialScene: Scene3D = {
      ...twoSolidScene,
      free_objects: ["S", "A", "B", "C", "D"],
      objects: [
        { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "2"] },
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
        { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point_marker", depends: [], xyz: ["2", "2", "0"] },
        { id: "D", type: "point3", label: "D", notation: "D", origin: "free", render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
        { id: "M", type: "point3", label: "M", notation: "M", origin: "derived", render: "point_marker", depends: ["S", "A"], xyz: ["0", "0", "1"] },
        { id: "N", type: "point3", label: "N", notation: "N", origin: "derived", render: "point_marker", depends: ["S", "B"], xyz: ["1", "0", "1"] },
        { id: "cut_sc", type: "point3", label: "Giao điểm của SC và (α)", origin: "derived", render: "point_marker", depends: ["S", "C"], xyz: ["1", "1", "1"] },
        { id: "Q", type: "point3", label: "Q", notation: "Q", origin: "derived", render: "point_marker", depends: ["S", "D"], xyz: ["0", "1", "1"] },
        {
          id: "khoi_cat_4",
          type: "solid",
          label: "Khối chóp đỉnh S cắt bởi (α)",
          shape_class: "PYRAMID_LIKE",
          origin: "derived",
          render: "mesh",
          formation_roles: ["CLOSE_SOLID"],
          depends: ["S", "M", "N", "cut_sc", "Q"],
          vertex_ids: ["S", "M", "N", "cut_sc", "Q"],
          vertices: [["0", "0", "2"], ["0", "0", "1"], ["1", "0", "1"], ["1", "1", "1"], ["0", "1", "1"]],
          faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]],
        },
      ] as unknown as SceneObject[],
      events: [
        { step_index: 0, action: "CREATE", object: "M", depends: ["S", "A"] },
        { step_index: 1, action: "CREATE", object: "N", depends: ["S", "B"] },
        { step_index: 2, action: "CREATE", object: "cut_sc", depends: ["S", "C"] },
        { step_index: 3, action: "CREATE", object: "Q", depends: ["S", "D"] },
        { step_index: 4, action: "CREATE", object: "khoi_cat_4", depends: ["S", "M", "N", "cut_sc", "Q"] },
      ] as unknown as Scene3D["events"],
    };
    const quadPlan = buildPedagogicalConstructionPlan(withSubEntities(quadPartialScene));
    for (const st of quadPlan.steps) {
      const allChipLabels = buildStepEntityGroups(quadPlan.scene, st.anchor, { steps: quadPlan.steps }).all.map((c) => c.shortLabel);
      expect(allChipLabels).not.toContain("MNQ");
    }
  });
});
