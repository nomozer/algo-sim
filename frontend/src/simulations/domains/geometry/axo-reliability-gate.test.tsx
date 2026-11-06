import { createRequire } from "node:module";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
import { describe, expect, it, vi, afterEach } from "vitest";
import { renderToString } from "react-dom/server";
import * as THREE from "three";
import {
  classifySceneEntityProvenance,
  ghiChuGiaTriDung,
  objectsAt,
  phanTichToanHocCuaCanh,
  registerExactSceneOrigin,
  type Scene3D,
  type SceneObject,
} from "./scene3d-model";
import { veKhongGian } from "./scene3d-chart";
import { withSubEntities } from "./scene3d-subentities";
import { givenQuantitiesSummary } from "./scene3d-annotations";
import { auxiliaryHiddenAt } from "./scene3d-auxiliary";
import {
  buildPedagogicalConstructionPlan,
  classifyPolygonShapeWithProvenance,
  classifyScenePolygonShape,
  resolvePlaneSectionVisibility,
  resolveStepVisualRoles,
  verifySceneMathematicalConsistency,
  type PedagogicalStepRole,
} from "./scene3d-semantic-policy";
import { setWebGLRendererFactoryForTest, tryCreateWebGLRenderer } from "./scene3d-view";
import { classifySolidEdgeVisibility } from "./scene3d-edge-visibility";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import App from "../../../App";
import { registerAllSimulations } from "../../index";
import { useAppStore } from "../../../state/store";

registerAllSimulations();

const __dirname = dirname(fileURLToPath(import.meta.url));
const requireFromFrontend = createRequire(import.meta.url);

function syncStoreForSSR() {
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
}

function loadCatalogScene(sampleId: string): { raw: Scene3D; world: Scene3D; desc: string; title: string } {
  const sample = GEOMETRY_SAMPLES.find((s) => s.id === sampleId);
  if (!sample) throw new Error(`Missing sample: ${sampleId}`);
  const raw = structuredClone((sample.envelope as unknown as { scene3d: Scene3D }).scene3d);
  const world = veKhongGian(raw);
  registerExactSceneOrigin(world, raw);
  return {
    raw,
    world: withSubEntities(world),
    desc: sample.envelope.description ?? sample.problemText,
    title: sample.envelope.title ?? sampleId,
  };
}

function buildCounterexampleSabcScene(opts: {
  cXyz: [string, string, string];
  symbolic?: boolean;
  declareDisplayScale?: boolean;
  numericOnlySymbolic?: boolean;
  goalQuantity?: "none" | "V_SABC" | "S_ABC" | "AC" | "BC" | "SB" | "d_S_ABC";
  postSolidEdgeSegment?: boolean;
}): Scene3D {
  const symbolic = opts.symbolic ?? true;
  const declareScale = opts.declareDisplayScale ?? true;
  const cXyz = opts.cXyz;

  const objects: SceneObject[] = [
    { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"], source: {} },
    { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"], source: {} },
    { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: cXyz, source: {} },
    { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"], source: {} },
    {
      id: "day_ABC",
      type: "polygon3",
      label: "Đáy ABC",
      notation: "ABC",
      role: "Đa giác A, B, C",
      origin: "derived",
      producer: "construct_polygon",
      render: "polygon",
      surface_role: "BASE_REGION",
      depends: ["A", "B", "C"],
      vertex_ids: ["A", "B", "C"],
      vertices: [["0", "0", "0"], ["2", "0", "0"], cXyz],
    },
    {
      id: "cao_SA",
      type: "segment3",
      label: "Đường cao SA",
      notation: "SA",
      origin: "derived",
      producer: "construct_segment",
      render: "segment",
      depends: ["S", "A"],
      formation_roles: ["CONSTRUCT_HEIGHT"],
      endpoint_ids: ["S", "A"],
      endpoints: [["0", "0", "4"], ["0", "0", "0"]],
      perpendicular_witness: {
        from: "S",
        foot: ["0", "0", "0"],
        foot_id: "A",
        on: "day_ABC",
        relation: "line_perp_plane",
        status: "GIVEN",
        plane_directions: [["2", "0", "0"], cXyz],
        marker: { u: ["2", "0", "0"], v: ["0", "0", "4"] },
      },
    },
    {
      id: "khoi_SABC",
      type: "solid",
      label: "Hình chóp S.ABC",
      notation: "S.ABC",
      shape_class: "PYRAMID_LIKE",
      origin: "derived",
      producer: "construct_solid",
      render: "mesh",
      depends: ["S", "A", "B", "C"],
      formation_roles: ["CLOSE_SOLID"],
      vertex_ids: ["S", "A", "B", "C"],
      vertices: [["0", "0", "4"], ["0", "0", "0"], ["2", "0", "0"], cXyz],
      faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]],
    },
    {
      id: "q_AB",
      type: "quantity",
      label: "Độ dài AB",
      notation: "AB",
      origin: "free",
      producer: null,
      render: "readout",
      depends: ["A", "B"],
      value: symbolic && !opts.numericOnlySymbolic ? "2a" : "2",
      ...(symbolic && !opts.numericOnlySymbolic ? { symbolic: "2a" } : { exact: { kind: "rational", value: "2" } }),
      source: { fact_id: "f_ab", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"],
      annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "B"], anchor: "segment" },
    },
    {
      id: "q_SA",
      type: "quantity",
      label: "Độ dài SA",
      notation: "SA",
      origin: "free",
      producer: null,
      render: "readout",
      depends: ["S", "A"],
      value: symbolic && !opts.numericOnlySymbolic ? "4a" : "4",
      ...(symbolic && !opts.numericOnlySymbolic ? { symbolic: "4a" } : { exact: { kind: "rational", value: "4" } }),
      source: { fact_id: "f_sa", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"],
      annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["S", "A"], anchor: "segment" },
    },
  ];

  const events: Scene3D["events"] = [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Khởi tạo các điểm." },
    { step_index: 1, action: "CREATE", object: "day_ABC", depends: ["A", "B", "C"], explanation: "Dựng đáy ABC." },
    { step_index: 2, action: "CREATE", object: "cao_SA", depends: ["S", "A"], explanation: "Dựng SA vuông góc (ABC)." },
    { step_index: 3, action: "CREATE", object: "khoi_SABC", depends: ["S", "A", "B", "C"], explanation: "Hoàn thiện S.ABC." },
  ];

  if (opts.postSolidEdgeSegment) {
    objects.push({
      id: "seg_SA_again",
      type: "segment3",
      label: "SA",
      notation: "SA",
      origin: "derived",
      producer: "construct_segment",
      render: "segment",
      depends: ["S", "A"],
      endpoint_ids: ["S", "A"],
      endpoints: [["0", "0", "4"], ["0", "0", "0"]],
    });
    events.push({
      step_index: events.length,
      action: "CREATE",
      object: "seg_SA_again",
      depends: ["S", "A"],
      explanation: "Dựng đoạn thẳng SA.",
    });
  }

  const goal = opts.goalQuantity ?? "none";
  if (goal === "V_SABC") {
    objects.push({
      id: "kq_V",
      type: "quantity",
      label: "Thể tích S.ABC",
      notation: "V(S.ABC)",
      origin: "derived",
      producer: "measure_volume",
      render: "readout",
      depends: ["khoi_SABC"],
      value: "8/3",
      annotation: { kind: "volume", category: "result", role: "result", subject_ids: ["khoi_SABC"], anchor: "solid" },
    });
    events.push({ step_index: events.length, action: "MEASURE", object: "kq_V", depends: ["khoi_SABC"], explanation: "" });
  } else if (goal === "S_ABC") {
    objects.push({
      id: "kq_S",
      type: "quantity",
      label: "Diện tích ABC",
      notation: "S(ABC)",
      origin: "derived",
      producer: "measure_area",
      render: "readout",
      depends: ["day_ABC"],
      value: "2",
      annotation: { kind: "area", category: "result", role: "result", subject_ids: ["day_ABC"], anchor: "region" },
    });
    events.push({ step_index: events.length, action: "MEASURE", object: "kq_S", depends: ["day_ABC"], explanation: "" });
  } else if (goal === "AC") {
    objects.push({
      id: "kq_AC",
      type: "quantity",
      label: "Khoảng cách giữa A và C",
      notation: "AC",
      origin: "derived",
      producer: "measure_distance",
      render: "readout",
      depends: ["A", "C"],
      value: "2",
      annotation: { kind: "length", category: "result", role: "result", subject_ids: ["A", "C"], anchor: "segment" },
    });
    events.push({ step_index: events.length, action: "MEASURE", object: "kq_AC", depends: ["A", "C"], explanation: "" });
  } else if (goal === "BC") {
    objects.push({
      id: "kq_BC",
      type: "quantity",
      label: "Khoảng cách giữa B và C",
      notation: "BC",
      origin: "derived",
      producer: "measure_distance",
      render: "readout",
      depends: ["B", "C"],
      value: "2√2",
      annotation: { kind: "length", category: "result", role: "result", subject_ids: ["B", "C"], anchor: "segment" },
    });
    events.push({ step_index: events.length, action: "MEASURE", object: "kq_BC", depends: ["B", "C"], explanation: "" });
  } else if (goal === "SB") {
    objects.push({
      id: "kq_SB",
      type: "quantity",
      label: "Độ dài SB",
      notation: "SB",
      origin: "derived",
      producer: "measure_distance",
      render: "readout",
      depends: ["S", "B"],
      value: "2a√5",
      symbolic: "2a√5",
      annotation: { kind: "length", category: "result", role: "result", subject_ids: ["S", "B"], anchor: "segment" },
    });
    events.push({ step_index: events.length, action: "MEASURE", object: "kq_SB", depends: ["S", "B"], explanation: "" });
  } else if (goal === "d_S_ABC") {
    objects.push({
      id: "kq_d",
      type: "quantity",
      label: "Khoảng cách từ S đến (ABC)",
      notation: "d(S, (ABC))",
      origin: "derived",
      producer: "measure_distance",
      render: "readout",
      depends: ["S", "day_ABC"],
      value: "4a",
      symbolic: "4a",
      annotation: {
        kind: "distance",
        category: "result",
        role: "result",
        subject_ids: ["S", "day_ABC"],
        anchor: "pair",
        witness: {
          from: "S",
          on: "day_ABC",
          foot: ["0", "0", "0"],
          relation: "point_to_plane",
          marker: { u: ["2", "0", "0"], v: ["0", "0", "4"] },
        },
      },
    });
    events.push({ step_index: events.length, action: "MEASURE", object: "kq_d", depends: ["S", "day_ABC"], explanation: "" });
  }

  return {
    free_objects: ["A", "B", "C", "S", "q_AB", "q_SA"],
    chart_metric: [
      ["1", "0", "0"],
      ["0", "1", "0"],
      ["0", "0", "1"],
    ],
    ...(symbolic
      ? {
          length_unit: (declareScale
            ? { symbol: "a", display_scale: "a = 1 đơn vị dựng", is_given: false }
            : { symbol: "a", display_scale: "", is_given: false }) as Scene3D["length_unit"],
        }
      : {}),
    objects,
    events,
  };
}

describe("AXO Mathematical & Pedagogical Reliability Gate", () => {
  afterEach(() => {
    setWebGLRendererFactoryForTest(null);
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe("Gate 1 & 2 — End-to-End Provenance & Mandatory Counterexample S.ABC", () => {
    const baseConfigs: { name: string; cXyz: [string, string, string] }[] = [
      { name: "illustrative right-isosceles coords C=(0,2,0)", cXyz: ["0", "2", "0"] },
      { name: "scalene acute coords C=(1,3,0)", cXyz: ["1", "3", "0"] },
      { name: "obtuse coords C=(-1,5/2,0)", cXyz: ["-1", "5/2", "0"] },
    ];

    it.each(baseConfigs)(
      "S.ABC ($name): never claims ABC is vuông cân, preserves symbolic 2a/4a, and classifies provenance cleanly",
      ({ cXyz }) => {
        const scene = buildCounterexampleSabcScene({ cXyz, symbolic: true });
        const base = scene.objects.find((o) => o.id === "day_ABC")!;
        const prov = classifyPolygonShapeWithProvenance(scene, base);
        expect(prov.certifiedShape).toBeNull();
        expect(classifyScenePolygonShape(scene, base)).toBe("tam giác");

        const plan = buildPedagogicalConstructionPlan(withSubEntities(scene));
        const allText = plan.steps.map((s) => `${s.title} || ${s.subtitle}`).join("\n");
        expect(allText).not.toMatch(/tam\s+giác\s+vuông\s+cân|tam\s+giác\s+vuông|tam\s+giác\s+cân|tam\s+giác\s+đều/iu);
        expect(allText).not.toMatch(/AC\s*=\s*AB|AB\s*[⊥⟂]\s*AC/u);

        // Symbolic 2a, 4a preserved without turning into bare 2, 4
        const finalAnchor = plan.steps[plan.steps.length - 1].anchor;
        const givens = givenQuantitiesSummary(plan.scene, finalAnchor);
        expect(givens.map((g) => g.text)).toContain("AB = 2a");
        expect(givens.map((g) => g.text)).toContain("SA = 4a");
        for (const g of givens) {
          expect(g.provenance).toBe("GIVEN");
        }

        // Canonical entity provenance distinguishes GIVEN vs ILLUSTRATIVE
        expect(classifySceneEntityProvenance(plan.scene, plan.scene.objects.find((o) => o.id === "q_AB")!)).toBe("GIVEN");
        expect(classifySceneEntityProvenance(plan.scene, plan.scene.objects.find((o) => o.id === "day_ABC")!)).toBe("ILLUSTRATIVE");
      },
    );

    it("never turns symbolic 2a, 4a into bare numeric 2, 4 even when length_unit.display_scale is omitted", () => {
      const scene = buildCounterexampleSabcScene({
        cXyz: ["0", "2", "0"],
        symbolic: true,
        declareDisplayScale: false,
        numericOnlySymbolic: true,
      });
      const note = ghiChuGiaTriDung(scene, "2", "length");
      expect(note).toMatch(/chuẩn\s+hóa\s+a\s*=\s*1/iu);
      const plan = buildPedagogicalConstructionPlan(withSubEntities(scene));
      const givens = givenQuantitiesSummary(plan.scene, plan.steps[plan.steps.length - 1].anchor);
      for (const g of givens) {
        expect(g.text).not.toBe("AB = 2");
        expect(g.text).not.toBe("SA = 4");
        expect(g.text).toMatch(/chuẩn\s+hóa\s+a\s*=\s*1/iu);
      }
    });

    it.each(["V_SABC", "S_ABC", "AC", "BC"] as const)(
      "fails closed (UNDERDETERMINED, no fabricated single answer) when S.ABC asks for underdetermined %s while keeping valid illustrative 3D view",
      (goalQuantity) => {
        const scene = buildCounterexampleSabcScene({
          cXyz: ["0", "2", "0"],
          symbolic: true,
          goalQuantity,
        });
        // Illustrative 3D configuration itself has no mathematical contradiction
        expect(verifySceneMathematicalConsistency(scene).valid).toBe(true);

        const plan = buildPedagogicalConstructionPlan(withSubEntities(scene));
        expect(plan.goalCompletion.status).not.toBe("reached");
        expect(plan.goalCompletion.items.length).toBeGreaterThan(0);
        for (const item of plan.goalCompletion.items) {
          expect(item.provenance).toBe("UNDERDETERMINED");
          expect(item.valueText).toBeNull();
        }

        const html = renderToString(
          <AxoWorkspaceV62
            scene={plan.scene}
            de="Cho hình chóp S.ABC có SA vuông góc với (ABC), AB = 2a, SA = 4a."
            tieuDe="Hình chóp S.ABC chưa xác định duy nhất đáy"
          />,
        );
        expect(html).not.toContain('id="dock-math-results"');
        expect(html).toContain('id="dock-goal-summary"');
        expect(html).toContain("Bản ghi chưa có chứng nhận kết quả mục tiêu.");
        expect(html).not.toMatch(/Chưa\s+đủ\s+dữ\s+kiện/iu);
        expect(html).not.toContain("8/3");
      },
    );

    it.each(["SB", "d_S_ABC"] as const)(
      "certifies genuinely invariant quantity %s on S.ABC as DERIVED_VERIFIED (does NOT over-block)",
      (goalQuantity) => {
        const scene = buildCounterexampleSabcScene({
          cXyz: ["1", "3", "0"],
          symbolic: true,
          goalQuantity,
        });
        const plan = buildPedagogicalConstructionPlan(withSubEntities(scene));
        expect(plan.goalCompletion.status).toBe("reached");
        expect(plan.goalCompletion.items[0]?.provenance).toBe("DERIVED_VERIFIED");
        expect(plan.goalCompletion.items[0]?.valueText).toBeTruthy();
      },
    );

    it("classifies coordinate-frame placement assumptions as ILLUSTRATIVE (not GIVEN) in phanTichToanHocCuaCanh", () => {
      const { raw } = loadCatalogScene("thiet-dien-chop");
      const analysis = phanTichToanHocCuaCanh(raw, null);
      const assumpItem = analysis.givenRelations.find((r) => /hệ trục do đề chọn/iu.test(r.valueDisplay ?? ""));
      expect(assumpItem).toBeDefined();
      expect(assumpItem?.provenance).toBe("ILLUSTRATIVE");
    });
  });

  describe("Gate 3 — Dependency-Driven Pedagogical Construction Plan & Step Roles", () => {
    it("enforces non-empty valid prerequisites, topological order, and fine-grained stepRole across all 11 catalog samples", () => {
      const validRoles = new Set<PedagogicalStepRole>([
        "identify_given",
        "construct_geometry",
        "identify_auxiliary",
        "deduce_relation",
        "construct_intersection_or_section",
        "emphasize_result",
        "conclude_and_calculate",
      ]);

      for (const sample of GEOMETRY_SAMPLES) {
        const { world } = loadCatalogScene(sample.id);
        const plan = buildPedagogicalConstructionPlan(world);
        expect(plan.steps.length, sample.id).toBeGreaterThan(0);

        const available = new Set<string>(plan.scene.free_objects);
        const seenTitles = new Set<string>();
        plan.steps.forEach((st, idx) => {
          expect(validRoles.has(st.stepRole), `${sample.id} step ${idx} role=${st.stepRole}`).toBe(true);
          expect(st.stepRoleLabel.trim().length, `${sample.id} step ${idx}`).toBeGreaterThan(0);
          if (idx > 0) {
            expect(st.prerequisiteIds.length, `${sample.id} step ${idx} (${st.title}) must have prerequisites`).toBeGreaterThan(0);
          }
          for (const pre of st.prerequisiteIds) {
            expect(available.has(pre), `${sample.id} step ${idx} prerequisite ${pre} must exist before step`).toBe(true);
          }
          expect(seenTitles.has(st.title), `${sample.id} duplicate step title: ${st.title}`).toBe(false);
          seenTitles.add(st.title);
          for (const v of st.visibleIds) available.add(v);
          for (const t of st.targetIds) available.add(t);
        });
      }
    });

    it("never narrates an already-constructed solid edge as a brand-new 'Dựng đoạn thẳng SA' after the pyramid is closed", () => {
      const scene = buildCounterexampleSabcScene({
        cXyz: ["1", "2", "0"],
        symbolic: true,
        postSolidEdgeSegment: true,
      });
      const plan = buildPedagogicalConstructionPlan(withSubEntities(scene));
      const postSteps = plan.steps.slice(3);
      for (const st of postSteps) {
        expect(st.title).not.toMatch(/^Dựng\s+(?:đoạn\s+thẳng|đường\s+thẳng|đường\s+cao)\s+SA\b/iu);
      }
    });
  });

  describe("Gate 4 — Planes, Intersection Lines, Cross-Sections & S.ABCD Acceptance (Section IV)", () => {
    function parseRat(s: string): [bigint, bigint] {
      const t = s.trim();
      const slash = t.indexOf("/");
      if (slash < 0) return [BigInt(t), 1n];
      return [BigInt(t.slice(0, slash)), BigInt(t.slice(slash + 1))];
    }
    function gcdBig(a: bigint, b: bigint): bigint {
      let x = a < 0n ? -a : a;
      let y = b < 0n ? -b : b;
      while (y !== 0n) {
        const r = x % y;
        x = y;
        y = r;
      }
      return x === 0n ? 1n : x;
    }
    function normRat([n, d]: [bigint, bigint]): [bigint, bigint] {
      const sign = d < 0n ? -1n : 1n;
      const g = gcdBig(n, d);
      return [(sign * n) / g, (sign * d) / g];
    }
    function subRat(a: [bigint, bigint], b: [bigint, bigint]): [bigint, bigint] {
      return normRat([a[0] * b[1] - b[0] * a[1], a[1] * b[1]]);
    }
    function mulRat(a: [bigint, bigint], b: [bigint, bigint]): [bigint, bigint] {
      return normRat([a[0] * b[0], a[1] * b[1]]);
    }
    function addRat(a: [bigint, bigint], b: [bigint, bigint]): [bigint, bigint] {
      return normRat([a[0] * b[1] + b[0] * a[1], a[1] * b[1]]);
    }
    function vecSub(u: [string, string, string], v: [string, string, string]) {
      return [
        subRat(parseRat(u[0]), parseRat(v[0])),
        subRat(parseRat(u[1]), parseRat(v[1])),
        subRat(parseRat(u[2]), parseRat(v[2])),
      ] as const;
    }
    function vecDot(
      u: readonly [[bigint, bigint], [bigint, bigint], [bigint, bigint]],
      v: readonly [[bigint, bigint], [bigint, bigint], [bigint, bigint]],
    ): [bigint, bigint] {
      return addRat(addRat(mulRat(u[0], v[0]), mulRat(u[1], v[1])), mulRat(u[2], v[2]));
    }
    function vecCross(
      u: readonly [[bigint, bigint], [bigint, bigint], [bigint, bigint]],
      v: readonly [[bigint, bigint], [bigint, bigint], [bigint, bigint]],
    ) {
      return [
        subRat(mulRat(u[1], v[2]), mulRat(u[2], v[1])),
        subRat(mulRat(u[2], v[0]), mulRat(u[0], v[2])),
        subRat(mulRat(u[0], v[1]), mulRat(u[1], v[0])),
      ] as const;
    }

    it("verifies S.ABCD midpoint section (thiet-dien-chop) AND vertex-renamed T.EFGH by exact rational geometry, step salience, and camera-orbit occlusion invariance", () => {
      const { raw, world } = loadCatalogScene("thiet-dien-chop");
      const getPt = (sc: Scene3D, id: string) => sc.objects.find((o) => o.id === id)!.xyz!;

      const S = getPt(raw, "S");
      const A = getPt(raw, "A");
      const B = getPt(raw, "B");
      const C = getPt(raw, "C");
      const D = getPt(raw, "D");
      const M = getPt(raw, "M");
      const N = getPt(raw, "N");
      const P = getPt(raw, "P");
      const Q = getPt(raw, "Q");

      // 1. M, N, P lie at exact midpoint ratio t = 1/2 on SA, SB, SC: 2*(M - S) === (A - S)
      for (const [mid, baseV] of [
        [M, A],
        [N, B],
        [P, C],
      ] as const) {
        const sm = vecSub(mid, S);
        const sb = vecSub(baseV, S);
        for (let k = 0; k < 3; k += 1) {
          expect(mulRat([2n, 1n], sm[k])).toEqual(sb[k]);
        }
      }

      // 2. Plane (MNP) normal is perpendicular to MN and MP, and Q lies on BOTH SD and (MNP)
      const planeObj = raw.objects.find((o) => o.type === "plane3")!;
      const normal = [
        parseRat(planeObj.normal![0]),
        parseRat(planeObj.normal![1]),
        parseRat(planeObj.normal![2]),
      ] as const;
      expect(vecDot(normal, vecSub(N, M))).toEqual([0n, 1n]);
      expect(vecDot(normal, vecSub(P, M))).toEqual([0n, 1n]);
      expect(vecDot(normal, vecSub(Q, M))).toEqual([0n, 1n]); // Q ∈ (MNP)
      // Q ∈ SD (collinear: (Q - S) × (D - S) = (0,0,0)) and verified geometrically at ratio t = 1/2
      const sq = vecSub(Q, S);
      const sd = vecSub(D, S);
      expect(vecCross(sq, sd)).toEqual([[0n, 1n], [0n, 1n], [0n, 1n]]);
      for (let k = 0; k < 3; k += 1) {
        expect(mulRat([2n, 1n], sq[k])).toEqual(sd[k]);
      }

      // 3. Parallelism MN ∥ AB and PQ ∥ CD verified by exact cross product = 0
      expect(vecCross(vecSub(N, M), vecSub(B, A))).toEqual([[0n, 1n], [0n, 1n], [0n, 1n]]);
      expect(vecCross(vecSub(Q, P), vecSub(D, C))).toEqual([[0n, 1n], [0n, 1n], [0n, 1n]]);

      // 4. Section MNPQ is distinct from cutting plane (MNP), closed, coplanar, and step-salience transitions cleanly
      const plan = buildPedagogicalConstructionPlan(world);
      const planeWorld = plan.scene.objects.find((o) => o.type === "plane3")!;
      const secWorld = plan.scene.objects.find((o) => o.type === "section")!;
      expect(planeWorld.id).not.toBe(secWorld.id);
      expect(secWorld.polygon?.length).toBe(4);

      const planeIntroStep = plan.steps.find((st) => st.targetIds.includes(planeWorld.id))!;
      const qFindStep = plan.steps.find((st) => st.targetIds.includes("Q"))!;
      const finalStep = plan.steps[plan.steps.length - 1]!;

      // At plane introduction step: cutting plane is visible
      expect(resolvePlaneSectionVisibility(plan.scene, planeWorld, planeIntroStep.anchor, false, null).visible).toBe(true);
      // While finding intersection Q: Q is highlighted as active primary target
      const qRoles = resolveStepVisualRoles(plan.scene, qFindStep.anchor);
      expect(qRoles.get("Q")?.role).toBe("PRIMARY");
      expect(qRoles.get("Q")?.reason).toBe("step_primary_target");
      // When section MNPQ completes: section is visible & primary; user can still re-enable/select plane
      const finalRoles = resolveStepVisualRoles(plan.scene, finalStep.anchor);
      expect(finalRoles.get(secWorld.id)?.role).toBe("PRIMARY");
      expect(resolvePlaneSectionVisibility(plan.scene, secWorld, finalStep.anchor, false, null).visible).toBe(true);
      expect(resolvePlaneSectionVisibility(plan.scene, planeWorld, finalStep.anchor, false, planeWorld.id).visible).toBe(true);

      // 5. Vertex-renamed T.EFGH with fourth point L (proving zero reliance on vertex name "Q")
      const renameMap: Record<string, string> = {
        S: "T",
        A: "E",
        B: "F",
        C: "G",
        D: "H",
        M: "I",
        N: "J",
        P: "K",
        Q: "L",
      };
      const mapId = (id: string) => renameMap[id] ?? id;
      const mapEmbeddedIds = (s: string) =>
        s
          .replace(/::edge:([A-Z])-([A-Z])/g, (_m, u, v) => `::edge:${mapId(u)}-${mapId(v)}`)
          .replace(/\b(S|A|B|C|D|M|N|P|Q)\b/g, (m) => mapId(m));
      const renamedRaw = JSON.parse(JSON.stringify(raw), (_key, val) =>
        typeof val === "string" ? mapEmbeddedIds(val) : val,
      ) as Scene3D;
      const renamedPlan = buildPedagogicalConstructionPlan(
        withSubEntities(veKhongGian(registerExactSceneOrigin(renamedRaw, renamedRaw))),
      );
      expect(verifySceneMathematicalConsistency(renamedPlan.scene).valid).toBe(true);
      expect(renamedPlan.goalCompletion.status).toBe("reached");
      expect(renamedPlan.steps.some((st) => st.targetIds.includes("L"))).toBe(true);
      const lStep = renamedPlan.steps.find((st) => st.targetIds.includes("L"))!;
      expect(`${lStep.title} ${lStep.subtitle}`).toMatch(/trung\s+điểm\s+L/iu);

      // 6. Camera-orbit hidden/visible dashing invariance: rotating camera changes presentation visibility
      // accurately per viewing ray without mutating Scene3D coordinates
      const solidObj = plan.scene.objects.find((o) => o.type === "solid")!;
      const beforeVerts = JSON.stringify(solidObj.vertices);
      const frontRightCam = new THREE.Vector3(8, -8, 5);
      const backLeftCam = new THREE.Vector3(-8, 8, 5);
      const visFront = classifySolidEdgeVisibility(solidObj, frontRightCam);
      const visBack = classifySolidEdgeVisibility(solidObj, backLeftCam);
      expect(visFront.visible_edge_ids.length).toBeGreaterThan(0);
      expect(visBack.visible_edge_ids.length).toBeGreaterThan(0);
      // Opposite azimuths occlude different lateral/base edges while keeping total canonical edges invariant
      const totalFront =
        visFront.visible_edge_ids.length + visFront.hidden_edge_ids.length + visFront.mixed_edge_ids.length;
      const totalBack =
        visBack.visible_edge_ids.length + visBack.hidden_edge_ids.length + visBack.mixed_edge_ids.length;
      expect(totalFront).toBe(totalBack);
      expect(visFront.hidden_edge_ids).not.toEqual(visBack.hidden_edge_ids);
      expect(JSON.stringify(solidObj.vertices)).toBe(beforeVerts);
    });
  });

  describe("Gate 5 — Mathematical Result Completeness & Mandatory Sphere Case (cau-cat-mat-phang)", () => {
    it("verifies cau-cat-mat-phang end-to-end: R=5, d(I,(P))=3, visible right-triangle witnesses (IH, HM, IM) at Step 3, and verified results 4 & 16π without fake 3D answer objects", () => {
      const { world, desc, title } = loadCatalogScene("cau-cat-mat-phang");
      const plan = buildPedagogicalConstructionPlan(world);
      expect(plan.steps.length).toBe(5);

      // 1. Both R = 5 and d(I, (P)) = 3 appear in givenQuantitiesSummary at final step
      const finalAnchor = plan.steps[4].anchor;
      const givens = givenQuantitiesSummary(plan.scene, finalAnchor);
      const givenTexts = givens.map((g) => g.text);
      expect(givenTexts).toContain("R = 5");
      expect(givenTexts.some((t) => /d\(I,\s*\(P\)\)\s*=\s*3/u.test(t))).toBe(true);

      // 2. Right-triangle witnesses distinguishing sphere radius R = IM, distance d = IH, and section radius r = HM
      // MUST BE VISIBLE at Step 3 (not hidden by auxiliaryHiddenAt due to folded MEASURE events!)
      const hiddenAuxAtStep3 = auxiliaryHiddenAt(plan.scene, finalAnchor, false, null);
      const presentAtStep3 = new Set(objectsAt(plan.scene, finalAnchor).map((o) => o.id));
      for (const witnessId of ["C__center", "C__dist", "C__rim_pt", "C__sec_rad", "C__sph_rad"]) {
        expect(presentAtStep3.has(witnessId), `${witnessId} present at Step 3`).toBe(true);
        expect(hiddenAuxAtStep3.has(witnessId), `${witnessId} must NOT be hidden at Step 3`).toBe(false);
      }

      // 3. No fake 3D objects created to store answers 4 or 16π
      const answerHolders = plan.scene.objects.filter(
        (o) => o.type !== "quantity" && (/\b16π\b/u.test(`${o.label} ${o.notation ?? ""}`) || /^4$/u.test(`${o.notation ?? ""}`)),
      );
      expect(answerHolders).toEqual([]);

      // 4. Verified GoalCompletion items for r = 4 and S = 16π with clean Vietnamese labels & formulas
      expect(plan.goalCompletion.status).toBe("reached");
      expect(plan.goalCompletion.items.length).toBe(2);
      const rItem = plan.goalCompletion.items.find((it) => it.id === "r")!;
      const sItem = plan.goalCompletion.items.find((it) => it.id === "S")!;
      expect(rItem.label).toBe("Bán kính đường tròn thiết diện");
      expect(rItem.valueText).toBe("4");
      expect(rItem.provenance).toBe("DERIVED_VERIFIED");
      expect(rItem.witnessSummary).toMatch(/R\s*=\s*5.*d\(I,\s*\(P\)\)\s*=\s*3/u);
      expect(sItem.label).toBe("Diện tích hình tròn thiết diện");
      expect(sItem.valueText).toBe("16π");
      expect(sItem.provenance).toBe("DERIVED_VERIFIED");

      // Early steps keep answers hidden; the final conclusion publishes the verified goals.
      const ssrStep1 = renderToString(
        <AxoWorkspaceV62 scene={plan.scene} initialStep={plan.steps[0].anchor} de={desc} tieuDe={title} />,
      );
      expect(ssrStep1).not.toContain('id="dock-math-results"');
      expect(ssrStep1).not.toContain("16π");

      const ssrFinal = renderToString(
        <AxoWorkspaceV62 scene={plan.scene} de={desc} tieuDe={title} />,
      );
      expect(ssrFinal).not.toContain('id="dock-math-results"');
      expect(ssrFinal).not.toContain("KẾT QUẢ TOÁN HỌC");
      expect(ssrFinal).not.toContain('id="dock-goal-reveal"');
      expect(ssrFinal).not.toContain('id="dock-goal-conclusion"');
      expect(ssrFinal).not.toContain("16π");
    });

    it("omits #dock-math-results across all student simulation workspaces and avoids ungrounded (S) on cau-the-tich", () => {
      for (const pureId of ["thiet-dien-chop", "mat-cheo-sac"]) {
        const { world, desc, title } = loadCatalogScene(pureId);
        const html = renderToString(<AxoWorkspaceV62 scene={world} de={desc} tieuDe={title} />);
        expect(html, pureId).not.toContain('id="dock-math-results"');
      }

      const { world: cauWorld, desc: cauDesc, title: cauTitle } = loadCatalogScene("cau-the-tich");
      const cauPlan = buildPedagogicalConstructionPlan(cauWorld);
      for (const item of cauPlan.goalCompletion.items) {
        expect(item.label).not.toContain("(S)");
      }
      expect(cauPlan.goalCompletion.items.map((it) => it.valueText)).toContain("36π");
      const cauHtml = renderToString(<AxoWorkspaceV62 scene={cauPlan.scene} de={cauDesc} tieuDe={cauTitle} />);
      expect(cauHtml).not.toContain('id="dock-math-results"');
      expect(cauHtml).not.toContain('id="dock-goal-reveal"');
      expect(cauHtml).not.toContain('id="dock-goal-conclusion"');
      expect(cauHtml).not.toContain("36π");
      expect(cauHtml).not.toContain("Bán kính (S)");
      expect(cauHtml).not.toContain("Thể tích (S)");
    });
  });

  describe("Gate 6 — Cross-Family Over-Inference Counterexamples (Prisms, Curved Solids, Relations)", () => {
    it("Prism counterexample: right prism ABC.A′B′C′ with only AB = 2a, AA′ = 3a never claims ABC is equilateral/right and fails closed on V", () => {
      const prismScene: Scene3D = {
        free_objects: ["A", "B", "C", "A1", "B1", "C1", "q_ab", "q_aa1"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        length_unit: { symbol: "a", display_scale: "a = 1 đơn vị dựng", is_given: false },
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"], source: {} },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"], source: {} },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"], source: {} },
          { id: "A1", type: "point3", label: "Điểm A′", notation: "A′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "3"], source: {} },
          { id: "B1", type: "point3", label: "Điểm B′", notation: "B′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "3"], source: {} },
          { id: "C1", type: "point3", label: "Điểm C′", notation: "C′", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "3"], source: {} },
          {
            id: "day_ABC",
            type: "polygon3",
            label: "Đáy ABC",
            notation: "ABC",
            origin: "derived",
            producer: "construct_polygon",
            render: "polygon",
            surface_role: "BASE_REGION",
            depends: ["A", "B", "C"],
            vertex_ids: ["A", "B", "C"],
            vertices: [["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]],
          },
          {
            id: "day_A1B1C1",
            type: "polygon3",
            label: "Đáy A′B′C′",
            notation: "A′B′C′",
            origin: "derived",
            producer: "construct_polygon",
            render: "polygon",
            formation_roles: ["CONSTRUCT_TRANSLATED_FACE"],
            depends: ["A1", "B1", "C1"],
            vertex_ids: ["A1", "B1", "C1"],
            vertices: [["0", "0", "3"], ["2", "0", "3"], ["0", "2", "3"]],
          },
          {
            id: "lt",
            type: "solid",
            label: "Lăng trụ ABC.A′B′C′",
            notation: "ABC.A′B′C′",
            shape_class: "PRISM_LIKE",
            origin: "derived",
            producer: "construct_solid",
            render: "mesh",
            depends: ["A", "B", "C", "A1", "B1", "C1"],
            vertex_ids: ["A", "B", "C", "A1", "B1", "C1"],
            vertices: [["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"], ["0", "0", "3"], ["2", "0", "3"], ["0", "2", "3"]],
            faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]],
          },
          {
            id: "q_ab",
            type: "quantity",
            label: "Độ dài AB",
            notation: "AB",
            origin: "free",
            producer: null,
            render: "readout",
            depends: ["A", "B"],
            value: "2a",
            symbolic: "2a",
            source: { fact_id: "f1" },
            annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "B"], anchor: "segment" },
          },
          {
            id: "q_aa1",
            type: "quantity",
            label: "Độ dài AA′",
            notation: "AA′",
            origin: "free",
            producer: null,
            render: "readout",
            depends: ["A", "A1"],
            value: "3a",
            symbolic: "3a",
            source: { fact_id: "f2" },
            annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "A1"], anchor: "segment" },
          },
          {
            id: "kq_v_lt",
            type: "quantity",
            label: "Thể tích ABC.A′B′C′",
            notation: "V",
            origin: "derived",
            producer: "measure_volume",
            render: "readout",
            depends: ["lt"],
            value: "6",
            annotation: { kind: "volume", category: "result", role: "result", subject_ids: ["lt"], anchor: "solid" },
          },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_ABC", depends: ["A", "B", "C"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "day_A1B1C1", depends: ["A1", "B1", "C1"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "lt", depends: ["A", "B", "C", "A1", "B1", "C1"], explanation: "" },
          { step_index: 4, action: "MEASURE", object: "kq_v_lt", depends: ["lt"], explanation: "" },
        ],
      };

      const plan = buildPedagogicalConstructionPlan(withSubEntities(prismScene));
      const stepTexts = plan.steps.map((s) => `${s.title} ${s.subtitle}`).join(" | ");
      expect(stepTexts).not.toMatch(/tam\s+giác\s+vuông|tam\s+giác\s+đều|tam\s+giác\s+cân/iu);
      expect(plan.goalCompletion.status).not.toBe("reached");
      expect(plan.goalCompletion.items[0]?.provenance).toBe("UNDERDETERMINED");
      expect(plan.goalCompletion.items[0]?.valueText).toBeNull();
    });

    it("Curved solid counterexample: unmodified tru-thiet-dien-tron (given R = 2, ungiven height OO′) certifies perpendicular section r = 2 while failing closed on volume V", () => {
      const { raw, world } = loadCatalogScene("tru-thiet-dien-tron");
      // 1) Unmodified catalog sample certifies perpendicular circular section radius r = R = 2 (height-invariant)
      const basePlan = buildPedagogicalConstructionPlan(world);
      expect(basePlan.goalCompletion.status).toBe("reached");
      expect(basePlan.goalCompletion.items[0]?.provenance).toBe("DERIVED_VERIFIED");
      expect(basePlan.goalCompletion.items[0]?.valueText).toContain("2");

      // 2) Asking for cylinder volume V on the SAME unmodified cylinder (without mutating O′.source!) MUST fail closed
      const cylScene = structuredClone(raw);
      cylScene.objects.push({
        id: "kq_V_cyl",
        type: "quantity",
        label: "Thể tích hình trụ",
        notation: "V",
        origin: "derived",
        producer: "measure_volume",
        render: "readout",
        depends: ["tru"],
        value: "16π",
        annotation: { kind: "volume", category: "result", role: "result", subject_ids: ["tru"], anchor: "solid" },
      });
      cylScene.events.push({ step_index: cylScene.events.length, action: "MEASURE", object: "kq_V_cyl", depends: ["tru"], explanation: "" });

      const disp = withSubEntities(veKhongGian(registerExactSceneOrigin(cylScene, cylScene)));
      const plan = buildPedagogicalConstructionPlan(disp);
      expect(plan.goalCompletion.status).not.toBe("reached");
      const vItem = plan.goalCompletion.items.find((it) => it.id === "kq_V_cyl")!;
      expect(vItem.provenance).toBe("UNDERDETERMINED");
      expect(vItem.valueText).toBeNull();
      const analysis = phanTichToanHocCuaCanh(disp);
      expect(JSON.stringify(analysis.requestedResults)).not.toContain("16π");
    });

    it("Adversarial DoF & Provenance Suite: rigid base + ungiven apex height, spatial angle non-inflation, 4-gon 1-right-angle DoF, phanTichToanHocCuaCanh fail-closed, and unverified producer=null fail-closed", () => {
      // Case 1: Rigid equilateral base ABC (AB = 2a) + SA ⊥ (ABC), NO given height SA -> S(ABC) is DERIVED_VERIFIED, V(S.ABC) is UNDERDETERMINED
      const ungivenHeightPyr: Scene3D = {
        free_objects: ["A", "B", "C", "S", "q_ab"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        length_unit: { symbol: "a", display_scale: "a = 1", is_given: false },
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["1", "2", "0"] },
          { id: "S", type: "point3", label: "Đỉnh S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
          { id: "day", type: "polygon3", label: "Tam giác đều ABC", notation: "ABC", role: "Tam giác đều đáy", surface_role: "BASE_REGION", origin: "derived", producer: "polygon", render: "polygon", depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], vertices: [["0", "0", "0"], ["2", "0", "0"], ["1", "2", "0"]] },
          { id: "khoi", type: "solid", label: "Hình chóp S.ABC", notation: "S.ABC", origin: "derived", producer: "pyramid", render: "mesh", depends: ["S", "A", "B", "C"], vertex_ids: ["S", "A", "B", "C"], vertices: [["0", "0", "4"], ["0", "0", "0"], ["2", "0", "0"], ["1", "2", "0"]], faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]] },
          {
            id: "seg_SA",
            type: "segment3",
            label: "Đoạn SA",
            notation: "SA",
            origin: "derived",
            producer: "segment",
            render: "segment",
            depends: ["S", "A"],
            endpoint_ids: ["S", "A"],
            endpoints: [["0", "0", "4"], ["0", "0", "0"]],
            perpendicular_witness: {
              relation: "line_perp_plane",
              from: "S",
              on: "day",
              foot_id: "A",
              foot: ["0", "0", "0"],
              status: "GIVEN",
              can_present_as_proven: true,
              marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] },
            },
          },
          {
            id: "q_ab",
            type: "quantity",
            label: "Độ dài AB",
            notation: "AB",
            origin: "free",
            producer: null,
            render: "readout",
            depends: ["A", "B"],
            value: "2a",
            symbolic: "2a",
            source: { fact_id: "f_ab", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"],
            annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "B"], anchor: "segment" },
          },
          {
            id: "kq_s_abc",
            type: "quantity",
            label: "Diện tích đáy ABC",
            notation: "S(ABC)",
            origin: "derived",
            producer: "measure_area",
            render: "readout",
            depends: ["day", "q_ab"],
            value: "a^2√3",
            symbolic: "a^2√3",
            annotation: { kind: "area", category: "measurement", role: "intermediate", subject_ids: ["day"], anchor: "region" },
          },
          {
            id: "kq_v_sabc",
            type: "quantity",
            label: "Thể tích S.ABC",
            notation: "V(S.ABC)",
            origin: "derived",
            producer: "measure_volume",
            render: "readout",
            depends: ["khoi", "kq_s_abc"],
            value: "4a^3√3/3",
            symbolic: "4a^3√3/3",
            annotation: { kind: "volume", category: "result", role: "result", subject_ids: ["khoi"], anchor: "solid" },
          },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day", depends: ["A", "B", "C"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "khoi", depends: ["S", "A", "B", "C"], explanation: "" },
          { step_index: 3, action: "MEASURE", object: "kq_v_sabc", depends: ["khoi"], explanation: "" },
        ],
      };
      const dispPyr = withSubEntities(ungivenHeightPyr);
      expect(classifySceneEntityProvenance(dispPyr, dispPyr.objects.find((o) => o.id === "kq_s_abc")!)).toBe("DERIVED_VERIFIED");
      expect(classifySceneEntityProvenance(dispPyr, dispPyr.objects.find((o) => o.id === "kq_v_sabc")!)).toBe("UNDERDETERMINED");

      // Case 2: S.ABC (AB = 2a, SA = 4a) + spatial angle(SB, (ABC)) = 60° MUST NOT inflate in-plane base DoF
      const sabcWithSpatialAngle = buildCounterexampleSabcScene({ cXyz: ["0", "2", "0"], goalQuantity: "V_SABC" });
      sabcWithSpatialAngle.free_objects = [...(sabcWithSpatialAngle.free_objects ?? []), "q_ang_sb"];
      sabcWithSpatialAngle.objects.push({
        id: "seg_SB",
        type: "segment3",
        label: "Cạnh SB",
        notation: "SB",
        origin: "derived",
        producer: "segment",
        render: "segment",
        depends: ["S", "B"],
        endpoint_ids: ["S", "B"],
        endpoints: [["0", "0", "4"], ["2", "0", "0"]],
      });
      sabcWithSpatialAngle.objects.push({
        id: "q_ang_sb",
        type: "quantity",
        label: "Góc giữa SB và (ABC)",
        notation: "∠(SB, (ABC))",
        origin: "free",
        producer: null,
        render: "readout",
        depends: ["seg_SB", "day_ABC"],
        value: "60°",
        source: { fact_id: "f_ang", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"],
        annotation: { kind: "angle", category: "measurement", role: "given", subject_ids: ["seg_SB", "day_ABC"], anchor: "pair" },
      });
      const dispSpatial = withSubEntities(sabcWithSpatialAngle);
      const spatialPlan = buildPedagogicalConstructionPlan(dispSpatial);
      expect(spatialPlan.goalCompletion.items[0]?.provenance).toBe("UNDERDETERMINED");
      expect(spatialPlan.goalCompletion.items[0]?.valueText).toBeNull();
      const spatialAnalysis = phanTichToanHocCuaCanh(dispSpatial);
      expect(JSON.stringify(spatialAnalysis.requestedResults)).not.toContain("8/3");

      // Case 3: 4-gon ABCD with 1 right angle (AB ⊥ AD) + 2 sides (AB = 3, AD = 4) + SA = 5 has 4-gon DoF = 5 - 1 = 4 > 2 -> UNDERDETERMINED
      const quadScene: Scene3D = {
        free_objects: ["A", "B", "C", "D", "S", "q_ab_q", "q_ad_q", "q_sa_q"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["3", "4", "0"] },
          { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "4", "0"] },
          { id: "S", type: "point3", label: "Đỉnh S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "5"] },
          { id: "day_q", type: "polygon3", label: "Tứ giác ABCD", notation: "ABCD", surface_role: "BASE_REGION", origin: "derived", producer: "polygon", render: "polygon", depends: ["A", "B", "C", "D"], vertex_ids: ["A", "B", "C", "D"], vertices: [["0", "0", "0"], ["3", "0", "0"], ["3", "4", "0"], ["0", "4", "0"]] },
          { id: "khoi_q", type: "solid", label: "Hình chóp S.ABCD", notation: "S.ABCD", origin: "derived", producer: "pyramid", render: "mesh", depends: ["S", "A", "B", "C", "D"], vertex_ids: ["S", "A", "B", "C", "D"], vertices: [["0", "0", "5"], ["0", "0", "0"], ["3", "0", "0"], ["3", "4", "0"], ["0", "4", "0"]], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]] },
          { id: "seg_AB", type: "segment3", label: "Cạnh AB", notation: "AB", origin: "derived", producer: "segment", render: "segment", depends: ["A", "B"], endpoint_ids: ["A", "B"], endpoints: [["0", "0", "0"], ["3", "0", "0"]] },
          {
            id: "seg_AD",
            type: "segment3",
            label: "Cạnh AD",
            notation: "AD",
            origin: "derived",
            producer: "segment",
            render: "segment",
            depends: ["A", "D"],
            endpoint_ids: ["A", "D"],
            endpoints: [["0", "0", "0"], ["0", "4", "0"]],
            perpendicular_witness: {
              relation: "line_perp_line",
              from: "seg_AD",
              on: "seg_AB",
              foot_id: "A",
              foot: ["0", "0", "0"],
              status: "GIVEN",
              can_present_as_proven: true,
              marker: { u: ["1", "0", "0"], v: ["0", "1", "0"] },
            },
          },
          {
            id: "seg_SA_q",
            type: "segment3",
            label: "Cạnh SA",
            notation: "SA",
            origin: "derived",
            producer: "segment",
            render: "segment",
            depends: ["S", "A"],
            endpoint_ids: ["S", "A"],
            endpoints: [["0", "0", "5"], ["0", "0", "0"]],
            perpendicular_witness: {
              relation: "line_perp_plane",
              from: "S",
              on: "day_q",
              foot_id: "A",
              foot: ["0", "0", "0"],
              status: "GIVEN",
              can_present_as_proven: true,
              marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] },
            },
          },
          { id: "q_ab_q", type: "quantity", label: "AB", notation: "AB", origin: "free", producer: null, render: "readout", depends: ["A", "B"], value: "3", source: { fact_id: "f1", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"], annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "B"], anchor: "segment" } },
          { id: "q_ad_q", type: "quantity", label: "AD", notation: "AD", origin: "free", producer: null, render: "readout", depends: ["A", "D"], value: "4", source: { fact_id: "f2", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"], annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "D"], anchor: "segment" } },
          { id: "q_sa_q", type: "quantity", label: "SA", notation: "SA", origin: "free", producer: null, render: "readout", depends: ["S", "A"], value: "5", source: { fact_id: "f3", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"], annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["S", "A"], anchor: "segment" } },
          { id: "kq_v_q", type: "quantity", label: "Thể tích S.ABCD", notation: "V(S.ABCD)", origin: "derived", producer: "measure_volume", render: "readout", depends: ["khoi_q"], value: "20", annotation: { kind: "volume", category: "result", role: "result", subject_ids: ["khoi_q"], anchor: "solid" } },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "day_q", depends: ["A", "B", "C", "D"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "khoi_q", depends: ["S", "A", "B", "C", "D"], explanation: "" },
          { step_index: 3, action: "MEASURE", object: "kq_v_q", depends: ["khoi_q"], explanation: "" },
        ],
      };
      const quadPlan = buildPedagogicalConstructionPlan(withSubEntities(quadScene));
      expect(quadPlan.goalCompletion.items[0]?.provenance).toBe("UNDERDETERMINED");
      expect(quadPlan.goalCompletion.items[0]?.valueText).toBeNull();

      // Case 4: Named "Tam giác vuông ABC" + right-angle witness at A + only 1 given leg (AB = 2a, AC ungiven) MUST NOT double-subtract DoF to 1
      const rightTriOneLeg = buildCounterexampleSabcScene({ cXyz: ["0", "3", "0"], goalQuantity: "V_SABC" });
      const rtBase = rightTriOneLeg.objects.find((o) => o.id === "day_ABC")!;
      rtBase.label = "Tam giác vuông ABC";
      rtBase.role = "Tam giác vuông tại A";
      rightTriOneLeg.objects.push({
        id: "seg_AB_rt",
        type: "segment3",
        label: "Cạnh AB",
        notation: "AB",
        origin: "derived",
        producer: "segment",
        render: "segment",
        depends: ["A", "B"],
        endpoint_ids: ["A", "B"],
        endpoints: [["0", "0", "0"], ["2", "0", "0"]],
      });
      rightTriOneLeg.objects.push({
        id: "seg_AC_rt",
        type: "segment3",
        label: "Cạnh AC",
        notation: "AC",
        origin: "derived",
        producer: "segment",
        render: "segment",
        depends: ["A", "C"],
        endpoint_ids: ["A", "C"],
        endpoints: [["0", "0", "0"], ["0", "3", "0"]],
        perpendicular_witness: {
          relation: "line_perp_line",
          from: "seg_AC_rt",
          on: "seg_AB_rt",
          foot_id: "A",
          foot: ["0", "0", "0"],
          status: "GIVEN",
          can_present_as_proven: true,
          marker: { u: ["1", "0", "0"], v: ["0", "1", "0"] },
        },
      });
      const rtPlan = buildPedagogicalConstructionPlan(withSubEntities(rightTriOneLeg));
      expect(rtPlan.goalCompletion.items[0]?.provenance).toBe("UNDERDETERMINED");
      expect(rtPlan.goalCompletion.items[0]?.valueText).toBeNull();

      // Case 5: Named "Hình chữ nhật ABCD" + right-angle witness at A + only 1 given side (AB = 3, AD ungiven) MUST NOT double-subtract DoF to 1
      const rectOneSide = structuredClone(quadScene);
      rectOneSide.free_objects = ["A", "B", "C", "D", "S", "q_ab_q", "q_sa_q"];
      rectOneSide.objects = rectOneSide.objects.filter((o) => o.id !== "q_ad_q");
      const rectBase = rectOneSide.objects.find((o) => o.id === "day_q")!;
      rectBase.label = "Hình chữ nhật ABCD";
      rectBase.role = "Hình chữ nhật đáy";
      const rectPlan = buildPedagogicalConstructionPlan(withSubEntities(rectOneSide));
      expect(rectPlan.goalCompletion.items[0]?.provenance).toBe("UNDERDETERMINED");
      expect(rectPlan.goalCompletion.items[0]?.valueText).toBeNull();

      // Case 6: Unverified derived quantity (origin: "derived", producer: null, no kernel exact/formula/witness) fails closed in GoalCompletionSummary & stepProvenance
      const { raw: sphereRaw } = loadCatalogScene("cau-cat-mat-phang");
      const unverifiedSphere = structuredClone(sphereRaw);
      unverifiedSphere.objects.push({
        id: "kq_unverified",
        type: "quantity",
        label: "Thể tích chưa kiểm chứng",
        notation: "V_fake",
        origin: "derived",
        producer: null,
        render: "readout",
        depends: ["C"],
        value: "99π",
        annotation: { kind: "volume", category: "result", role: "result", subject_ids: ["C"], anchor: "solid" },
      });
      unverifiedSphere.events.push({ step_index: unverifiedSphere.events.length, action: "MEASURE", object: "kq_unverified", depends: ["C"], explanation: "" });
      const unverifiedWorld = veKhongGian(unverifiedSphere);
      registerExactSceneOrigin(unverifiedWorld, unverifiedSphere);
      const unverifiedDisp = withSubEntities(unverifiedWorld);
      const unverifiedPlan = buildPedagogicalConstructionPlan(unverifiedDisp);
      expect(unverifiedPlan.goalCompletion.status).toBe("unverified_or_contradictory");
      const fakeItem = unverifiedPlan.goalCompletion.items.find((it) => it.id === "kq_unverified")!;
      expect(fakeItem.provenance).toBe("INVALID");
      expect(fakeItem.valueText).toBeNull();
      const unverifiedAnalysis = phanTichToanHocCuaCanh(unverifiedDisp);
      expect(JSON.stringify(unverifiedAnalysis.requestedResults)).not.toContain("99π");
      const calcSteps = unverifiedPlan.steps.filter((s) => s.stepRole === "conclude_and_calculate");
      if (calcSteps.length > 0) {
        expect(calcSteps.some((s) => s.provenance === "INVALID")).toBe(true);
      }
    });

    it("Geometric relation counterexample: plane–plane intersection keeps BOTH planes visible at final step (never globally hides all planes)", () => {
      const twoPlanesScene: Scene3D = {
        free_objects: ["A", "B", "C", "D", "S"],
        chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        objects: [
          { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
          { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["2", "2", "0"] },
          { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
          { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
          { id: "mp_SAC", type: "plane3", label: "Mặt phẳng (SAC)", notation: "(SAC)", origin: "derived", producer: "construct_plane", render: "surface", depends: ["S", "A", "C"], point: ["0", "0", "0"], normal: ["1", "-1", "0"] },
          { id: "mp_SBD", type: "plane3", label: "Mặt phẳng (SBD)", notation: "(SBD)", origin: "derived", producer: "construct_plane", render: "surface", depends: ["S", "B", "D"], point: ["2", "0", "0"], normal: ["1", "1", "1/2"] },
          { id: "gt_SO", type: "line3", label: "Giao tuyến d", notation: "d", origin: "derived", producer: "intersect_planes", render: "line", depends: ["mp_SAC", "mp_SBD"], point: ["0", "0", "4"], direction: ["1", "1", "-4"] },
        ],
        events: [
          { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
          { step_index: 1, action: "CREATE", object: "mp_SAC", depends: ["S", "A", "C"], explanation: "" },
          { step_index: 2, action: "CREATE", object: "mp_SBD", depends: ["S", "B", "D"], explanation: "" },
          { step_index: 3, action: "CREATE", object: "gt_SO", depends: ["mp_SAC", "mp_SBD"], explanation: "" },
        ],
      };
      const plan = buildPedagogicalConstructionPlan(withSubEntities(twoPlanesScene));
      const finalStep = plan.steps[plan.steps.length - 1].anchor;
      const p1 = plan.scene.objects.find((o) => o.id === "mp_SAC")!;
      const p2 = plan.scene.objects.find((o) => o.id === "mp_SBD")!;
      expect(resolvePlaneSectionVisibility(plan.scene, p1, finalStep, false, null).visible).toBe(true);
      expect(resolvePlaneSectionVisibility(plan.scene, p2, finalStep, false, null).visible).toBe(true);
    });
  });

  describe("Gate 7 — Runtime Recovery & Route Hygiene Fault-Injection (Section VII)", () => {
    it("catches WebGLRenderer constructor exceptions safely in tryCreateWebGLRenderer()", () => {
      setWebGLRendererFactoryForTest(() => {
        throw new Error("Simulated GPU driver crash");
      });
      expect(tryCreateWebGLRenderer()).toBeNull();
    });

    it(
      "executes real Chromium fault-injection for WebGL recovery: scene switch during retry, background tab visibilitychange, bounded retry cap, unmount during retry, renderer null fallback, and Browser Back/Forward",
      async () => {
        const esbuild = requireFromFrontend("esbuild") as {
          build: (opts: Record<string, unknown>) => Promise<{ outputFiles: { text: string }[] }>;
        };
        const { world: sceneA, desc: descA, title: titleA } = loadCatalogScene("cau-cat-mat-phang");
        const { world: sceneB } = loadCatalogScene("thiet-dien-chop");

        const bundled = await esbuild.build({
          stdin: {
            contents: `
              import React from "react";
              import { flushSync } from "react-dom";
              import { createRoot } from "react-dom/client";
              import { Scene3DWorkspace, setWebGLRendererFactoryForTest } from "./scene3d-view";
              import { DEFAULT_ANNOTATION_VIEW } from "./scene3d-annotations";
              import { taoTrangThai } from "./interaction-state";
              import { stepCount } from "./scene3d-model";
              import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";

              const SCENE_A = ${JSON.stringify(sceneA)};
              const SCENE_B = ${JSON.stringify(sceneB)};
              const DESC_A = ${JSON.stringify(descA)};
              const TITLE_A = ${JSON.stringify(titleA)};

              function createMockRenderer() {
                const domElement = document.createElement("canvas");
                domElement.className = "mock-webgl-canvas";
                return {
                  domElement,
                  getPixelRatio() { return 1; },
                  setPixelRatio() {},
                  setSize() {},
                  setClearColor() {},
                  render() {},
                  dispose() {},
                  getContext() { return {}; },
                };
              }

              const host = document.createElement("div");
              host.id = "harness-host";
              host.style.width = "800px";
              host.style.height = "600px";
              document.body.appendChild(host);
              let root = createRoot(host);

              window.__state = { phases: [], failed: false, postUnmountFailureCalls: 0 };

              window.__setRendererMode = (mode) => {
                if (mode === "mock") {
                  setWebGLRendererFactoryForTest(() => createMockRenderer());
                } else if (mode === "throw") {
                  setWebGLRendererFactoryForTest(() => { throw new Error("Simulated WebGL constructor exception"); });
                } else {
                  setWebGLRendererFactoryForTest(null);
                }
              };

              window.__mountScene = (which) => {
                const sc = which === "B" ? SCENE_B : SCENE_A;
                flushSync(() => {
                  root.render(
                    React.createElement(Scene3DWorkspace, {
                      scene: sc,
                      step: stepCount(sc) - 1,
                      interaction: taoTrangThai(),
                      onSelect: () => {},
                      fitToken: 0,
                      annotationView: DEFAULT_ANNOTATION_VIEW,
                      auxiliaryShown: false,
                      gridShown: false,
                      xray: false,
                      webglFallbackNode: React.createElement("div", { "data-testid": "localized-webgl-failed" }, "Khung 3D tạm dừng"),
                      onWebglFailure: (f) => {
                        window.__state.failed = f;
                        if (window.__trackingPostUnmount) {
                          window.__state.postUnmountFailureCalls += 1;
                        }
                      },
                      onWebglLifecycleChange: (st) => {
                        window.__state.phases.push(st.phase);
                      },
                    })
                  );
                });
              };

              window.__mountFullWorkspace = () => {
                flushSync(() => {
                  root.render(
                    React.createElement(AxoWorkspaceV62, {
                      scene: SCENE_A,
                      de: DESC_A,
                      tieuDe: TITLE_A,
                    })
                  );
                });
              };

              window.__resetRoot = () => {
                flushSync(() => {
                  root.unmount();
                });
                host.innerHTML = "";
                root = createRoot(host);
                window.__state = { phases: [], failed: false, postUnmountFailureCalls: 0 };
                window.__trackingPostUnmount = false;
              };

              window.__dispatchLost = () => {
                flushSync(() => {
                  document.querySelector("canvas")!.dispatchEvent(new Event("webglcontextlost", { cancelable: true }));
                });
              };

              window.__dispatchRestored = () => {
                flushSync(() => {
                  document.querySelector("canvas")!.dispatchEvent(new Event("webglcontextrestored"));
                });
              };

              window.__setVisibility = (state) => {
                Object.defineProperty(document, "visibilityState", {
                  configurable: true,
                  get: () => state,
                });
                flushSync(() => {
                  document.dispatchEvent(new Event("visibilitychange"));
                });
              };

              window.__unmountDuringRecovery = () => {
                window.__trackingPostUnmount = true;
                flushSync(() => {
                  root.unmount();
                });
              };
            `,
            resolveDir: __dirname,
            sourcefile: "gate7-recovery-harness.tsx",
            loader: "tsx",
          },
          bundle: true,
          write: false,
          jsx: "automatic",
          format: "iife",
          platform: "browser",
          target: "es2022",
          define: {
            "process.env.NODE_ENV": '"development"',
            "import.meta.hot": "undefined",
          },
        });

        const browser = await chromium.launch({
          headless: true,
          args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
        });
        try {
          const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
          await page.clock.install();
          await page.setContent("<!doctype html><html><body></body></html>");
          await page.addScriptTag({ content: bundled.outputFiles[0]!.text });

          // 1) Problem switch while WebGL recovery timer is in flight -> cancels stale timer, Scene B stays healthy
          await page.evaluate(() => {
            const w = window as any;
            w.__setRendererMode("mock");
            w.__mountScene("A");
            w.__dispatchLost();
          });
          expect(await page.evaluate(() => (window as any).__state.phases.at(-1))).toBe("recovering");

          await page.evaluate(() => {
            (window as any).__mountScene("B");
          });
          await page.clock.fastForward(5500);
          const afterSwitch = await page.evaluate(() => ({
            lastPhase: (window as any).__state.phases.at(-1),
            failed: (window as any).__state.failed,
            canvasCount: document.querySelectorAll("canvas").length,
          }));
          expect(afterSwitch).toEqual({
            lastPhase: "healthy",
            failed: false,
            canvasCount: 1,
          });

          // 2) Tab hidden (visibilitychange) while recovering -> pauses timeout, then recovers cleanly on tab return
          await page.evaluate(() => {
            const w = window as any;
            w.__resetRoot();
            w.__setRendererMode("mock");
            w.__mountScene("A");
            w.__setVisibility("hidden");
            w.__dispatchLost();
          });
          await page.clock.fastForward(6000);
          expect(await page.evaluate(() => (window as any).__state.phases.at(-1))).toBe("recovering");

          await page.evaluate(() => {
            const w = window as any;
            w.__setVisibility("visible");
            w.__dispatchRestored();
          });
          const afterTabReturn = await page.evaluate(() => ({
            lastPhase: (window as any).__state.phases.at(-1),
            canvasCount: document.querySelectorAll("canvas").length,
          }));
          expect(afterTabReturn).toEqual({ lastPhase: "healthy", canvasCount: 1 });

          // 3) Bounded retry cap: 2 context restores succeed, 3rd context loss immediately latches "failed"
          await page.evaluate(() => {
            const w = window as any;
            w.__resetRoot();
            w.__setRendererMode("mock");
            w.__mountScene("A");
            for (let i = 0; i < 2; i += 1) {
              w.__dispatchLost();
              w.__dispatchRestored();
            }
            w.__dispatchLost();
          });
          const afterCap = await page.evaluate(() => ({
            lastPhase: (window as any).__state.phases.at(-1),
            hasLocalizedFallback: Boolean(document.querySelector('[data-testid="localized-webgl-failed"]')),
          }));
          expect(afterCap).toEqual({ lastPhase: "failed", hasLocalizedFallback: true });

          // 4) Unmount while recovery timer is in flight -> cancels timer cleanly, zero post-unmount callbacks
          await page.evaluate(() => {
            const w = window as any;
            w.__resetRoot();
            w.__setRendererMode("mock");
            w.__mountScene("A");
            w.__dispatchLost();
            w.__unmountDuringRecovery();
          });
          await page.clock.fastForward(6000);
          expect(await page.evaluate(() => (window as any).__state.postUnmountFailureCalls)).toBe(0);

          // 5) Renderer constructor exception -> localized fallback in #stage-3d-box, #ws-dock stays intact, NOT 404
          await page.evaluate(() => {
            const w = window as any;
            w.__resetRoot();
            w.__setRendererMode("throw");
            w.__mountFullWorkspace();
          });
          const afterThrow = await page.evaluate(() => ({
            hasDock: Boolean(document.getElementById("ws-dock")),
            hasSteps: Boolean(document.getElementById("dock-steps-ul")),
            hasMathResults: Boolean(document.getElementById("dock-math-results")),
            hasLocalizedFailed: Boolean(document.querySelector('[data-viewer-recovery-phase="failed"]')),
            hasNotFound: Boolean(document.querySelector('[data-error-kind="not_found"]')),
          }));
          expect(afterThrow).toEqual({
            hasDock: true,
            hasSteps: true,
            hasMathResults: false,
            hasLocalizedFailed: true,
            hasNotFound: false,
          });
        } finally {
          await browser.close();
        }
      },
      25_000,
    );

    it("handles deep-links to valid & non-existing routes, renders minimalist 404 without auto-reload, and transitions cleanly across routes", () => {
      try {
        useAppStore.getState().syncLocationRoute("/khong-ton-tai-xyz", "", "");
        syncStoreForSSR();
        const notFoundHtml = renderToString(<App />);
        expect(notFoundHtml).toContain('data-error-kind="not_found"');
        expect(notFoundHtml).not.toMatch(/meta[^>]*http-equiv="refresh"/iu);

        // Navigate to valid simulation deep-link /simulation/cau-cat-mat-phang
        useAppStore.getState().syncLocationRoute("/simulation/cau-cat-mat-phang", "", "");
        syncStoreForSSR();
        const validDeepLinkHtml = renderToString(<App />);
        expect(validDeepLinkHtml).not.toContain('data-error-kind="not_found"');
        expect(validDeepLinkHtml).toContain('id="ws-dock"');
        expect(validDeepLinkHtml).not.toContain('id="dock-math-results"');
        expect(validDeepLinkHtml).not.toContain('id="dock-goal-reveal"');
        expect(validDeepLinkHtml).not.toContain('id="dock-goal-conclusion"');
        expect(validDeepLinkHtml).not.toContain("16π");

        // Navigate to /library (e.g. Browser Back/Forward target)
        useAppStore.getState().syncLocationRoute("/library", "", "");
        syncStoreForSSR();
        const libHtml = renderToString(<App />);
        expect(libHtml).not.toContain('data-error-kind="not_found"');
      } finally {
        useAppStore.getState().reset();
        syncStoreForSSR();
      }
    });
  });
});
