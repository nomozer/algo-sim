import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import {
  objectsAt,
  phanTichToanHocCuaCanh,
  type Scene3D,
} from "./scene3d-model";
import { veKhongGian } from "./scene3d-chart";
import { withSubEntities, isSubEntity } from "./scene3d-subentities";
import { auxiliaryHiddenAt, auxiliaryObjects } from "./scene3d-auxiliary";
import {
  buildPedagogicalConstructionPlan,
  buildVerifiedObjectTooltip,
  inspectAxialCurvedOrthogonality,
  ungroundedFreePointIdsAt,
  verifySceneMathematicalConsistency,
} from "./scene3d-semantic-policy";

function catalogScene(id: string): Scene3D {
  const found = GEOMETRY_SAMPLES.find((s) => s.id === id);
  const env = found?.envelope as { scene3d?: Scene3D } | undefined;
  if (!env?.scene3d) {
    throw new Error(`Missing catalog scene: ${id}`);
  }
  return veKhongGian(env.scene3d);
}

function buildTestScene(raw: Record<string, unknown>): Scene3D {
  return veKhongGian(raw as unknown as Scene3D);
}

/**
 * Real Hybrid engine output for Case A (`AB = 3, BC = 4, SA ⊥ (ABCD), SA = 5, V = 20`),
 * preserving exact `chart_metric` and `can_present_as_proven: false` (`GIVEN` perpendicularity).
 */
function makeRectPyramid345Scene(withPerpWitness: boolean): Scene3D {
  return buildTestScene({
    chart_metric: [
      ["9", "0", "0"],
      ["0", "16", "0"],
      ["0", "0", "25"],
    ],
    free_objects: ["A", "B", "C", "D", "S"],
    objects: [
      { id: "A", type: "point3", label: "Điểm A", notation: "A", role: "Điểm", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"], source: { provenance: "LAYOUT_DERIVED" } },
      { id: "B", type: "point3", label: "Điểm B", notation: "B", role: "Điểm", origin: "free", render: "point_marker", depends: [], xyz: ["1", "0", "0"], source: { provenance: "LAYOUT_DERIVED" } },
      { id: "C", type: "point3", label: "Điểm C", notation: "C", role: "Điểm", origin: "free", render: "point_marker", depends: [], xyz: ["1", "1", "0"], source: { provenance: "LAYOUT_DERIVED" } },
      { id: "D", type: "point3", label: "Điểm D", notation: "D", role: "Điểm", origin: "free", render: "point_marker", depends: [], xyz: ["0", "1", "0"], source: { provenance: "LAYOUT_DERIVED" } },
      { id: "S", type: "point3", label: "Điểm S", notation: "S", role: "Điểm", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "1"], source: { provenance: "LAYOUT_DERIVED" } },
      {
        id: "day_ABCD",
        type: "polygon3",
        label: "Đáy ABCD là hình chữ nhật",
        notation: "ABCD",
        origin: "derived",
        producer: "construct_polygon",
        render: "polygon",
        depends: ["A", "B", "C", "D"],
        formation_roles: ["CONSTRUCT_BASE"],
        surface_role: "BASE_REGION",
        polygon: [["0", "0", "0"], ["1", "0", "0"], ["1", "1", "0"], ["0", "1", "0"]],
        vertex_ids: ["A", "B", "C", "D"],
      },
      {
        id: "canh_ben_S_A",
        type: "segment3",
        label: "Cạnh bên SA",
        notation: "SA",
        origin: "derived",
        producer: "construct_segment",
        render: "segment",
        depends: ["A", "S"],
        formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"],
        point_a: ["0", "0", "0"],
        point_b: ["0", "0", "1"],
        endpoints: [["0", "0", "0"], ["0", "0", "1"]],
        ...(withPerpWitness
          ? {
              perpendicular_witness: {
                from: "S",
                on: "day_ABCD",
                foot: ["0", "0", "0"],
                foot_id: "A",
                relation: "line_perp_plane",
                status: "GIVEN",
                certificate: "exact-gram-line-plane-orthogonality/1",
                rule: "perpendicular_foot_at_A",
                can_present_as_proven: false,
                plane_directions: [["1", "0", "0"], ["0", "1", "0"]],
                marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] },
              },
            }
          : {}),
      },
      { id: "canh_ben_S_B", type: "segment3", label: "Cạnh bên SB", notation: "SB", origin: "derived", producer: "construct_segment", render: "segment", depends: ["B", "S"], formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], point_a: ["1", "0", "0"], point_b: ["0", "0", "1"], endpoints: [["1", "0", "0"], ["0", "0", "1"]] },
      { id: "canh_ben_S_C", type: "segment3", label: "Cạnh bên SC", notation: "SC", origin: "derived", producer: "construct_segment", render: "segment", depends: ["C", "S"], formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], point_a: ["1", "1", "0"], point_b: ["0", "0", "1"], endpoints: [["1", "1", "0"], ["0", "0", "1"]] },
      { id: "canh_ben_S_D", type: "segment3", label: "Cạnh bên SD", notation: "SD", origin: "derived", producer: "construct_segment", render: "segment", depends: ["D", "S"], formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], point_a: ["0", "1", "0"], point_b: ["0", "0", "1"], endpoints: [["0", "1", "0"], ["0", "0", "1"]] },
      {
        id: "khoi_S_ABCD",
        type: "solid",
        label: "Hình chóp S.ABCD",
        notation: "S.ABCD",
        shape_class: "PYRAMID_LIKE",
        origin: "derived",
        producer: "construct_solid",
        render: "mesh",
        depends: ["A", "B", "C", "D", "S"],
        formation_roles: ["CLOSE_SOLID"],
        vertex_ids: ["S", "A", "B", "C", "D"],
        vertices: [["0", "0", "1"], ["0", "0", "0"], ["1", "0", "0"], ["1", "1", "0"], ["0", "1", "0"]],
        faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]],
      },
      ...(withPerpWitness
        ? [
            {
              id: "kq_u1_7",
              type: "quantity",
              label: "Thể tích S.ABCD",
              notation: "V(S.ABCD)",
              origin: "derived",
              producer: "measure.volume",
              render: "readout",
              depends: ["khoi_S_ABCD"],
              value: "20",
              exact: { kind: "rational", value: "20" },
              annotation: { kind: "volume", category: "result", role: "result", subject_ids: ["khoi_S_ABCD"], anchor: "solid" },
            },
          ]
        : []),
    ],
    events: [
      { step_index: 0, action: "INIT", semantic_kind: "EXPLANATION" },
      { step_index: 1, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "day_ABCD", depends: ["A", "B", "C", "D"] },
      { step_index: 2, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "canh_ben", objects: ["canh_ben_S_A", "canh_ben_S_B", "canh_ben_S_C", "canh_ben_S_D"], depends: ["canh_ben_S_A", "canh_ben_S_B", "canh_ben_S_C", "canh_ben_S_D"] },
      { step_index: 3, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "khoi_S_ABCD", depends: ["S", "A", "B", "C", "D"] },
      ...(withPerpWitness
        ? [{ step_index: 4, action: "MEASURE", semantic_kind: "FINAL_RESULT", object: "kq_u1_7", depends: ["khoi_S_ABCD"] }]
        : []),
    ],
  });
}

/**
 * Real Hybrid engine output for Case B (`hybrid_hexagonal_pyramid`: regular hexagonal pyramid
 * `S.ABCDEF`, base edge `2`, lateral edge `4`, center `O = (0,0,0)` in `free_objects`, `V = 12`).
 */
function makeRegularHexagonalPyramidScene(opts?: {
  apex?: string;
  center?: string;
  baseNames?: [string, string, string, string, string, string];
  baseSq?: string;
  halfNegBaseSq?: string;
  heightSq?: string;
  volumeVal?: string;
}): Scene3D {
  const apex = opts?.apex ?? "S";
  const center = opts?.center ?? "O";
  const [n0, n1, n2, n3, n4, n5] = opts?.baseNames ?? ["A", "B", "C", "D", "E", "F"];
  const baseSq = opts?.baseSq ?? "4";
  const halfNeg = opts?.halfNegBaseSq ?? "-2";
  const heightSq = opts?.heightSq ?? "12";
  const volumeVal = opts?.volumeVal ?? "12";
  const coords: [string, [string, string, string]][] = [
    [n0, ["1", "0", "0"]],
    [n1, ["1", "1", "0"]],
    [n2, ["0", "1", "0"]],
    [n3, ["-1", "0", "0"]],
    [n4, ["-1", "-1", "0"]],
    [n5, ["0", "-1", "0"]],
  ];
  const baseCycle = coords.map(([n]) => n).join("");
  const solidId = `khoi_${apex}_${baseCycle}`;
  const baseId = `day_${baseCycle}`;
  const latIds = coords.map(([n]) => `canh_ben_${apex}_${n}`);

  return buildTestScene({
    chart_metric: [
      [baseSq, halfNeg, "0"],
      [halfNeg, baseSq, "0"],
      ["0", "0", heightSq],
    ],
    free_objects: [...coords.map(([n]) => n), center, apex],
    objects: [
      ...coords.map(([n, xyz]) => ({
        id: n,
        type: "point3",
        label: `Điểm ${n}`,
        notation: n,
        origin: "free",
        render: "point_marker",
        depends: [],
        xyz,
      })),
      { id: apex, type: "point3", label: `Điểm ${apex}`, notation: apex, origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "1"] },
      { id: center, type: "point3", label: `Điểm ${center}`, notation: center, origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
      {
        id: baseId,
        type: "polygon3",
        label: `Đáy ${baseCycle} là lục giác đều`,
        notation: baseCycle,
        origin: "derived",
        producer: "construct_polygon",
        render: "polygon",
        depends: coords.map(([n]) => n),
        formation_roles: ["CONSTRUCT_BASE"],
        surface_role: "BASE_REGION",
        polygon: coords.map(([, xyz]) => xyz),
        vertex_ids: coords.map(([n]) => n),
      },
      ...coords.map(([n, xyz]) => ({
        id: `canh_ben_${apex}_${n}`,
        type: "segment3",
        label: `Cạnh bên ${apex}${n}`,
        notation: `${apex}${n}`,
        origin: "derived",
        producer: "construct_segment",
        render: "segment",
        depends: [n, apex],
        formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"],
        point_a: xyz,
        point_b: ["0", "0", "1"],
        endpoints: [xyz, ["0", "0", "1"]],
      })),
      {
        id: solidId,
        type: "solid",
        label: `Hình chóp ${apex}.${baseCycle}`,
        notation: `${apex}.${baseCycle}`,
        shape_class: "PYRAMID_LIKE",
        origin: "derived",
        producer: "construct_solid",
        render: "mesh",
        depends: [...coords.map(([n]) => n), apex],
        formation_roles: ["CLOSE_SOLID"],
        vertex_ids: [apex, ...coords.map(([n]) => n)],
        vertices: [["0", "0", "1"], ...coords.map(([, xyz]) => xyz)],
        faces: [[1, 2, 3, 4, 5, 6], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 5], [0, 5, 6], [0, 6, 1]],
      },
      {
        id: "kq_hex_vol",
        type: "quantity",
        label: `Thể tích ${apex}.${baseCycle}`,
        notation: `V(${apex}.${baseCycle})`,
        origin: "derived",
        producer: "measure.volume",
        render: "readout",
        depends: [solidId],
        value: volumeVal,
        exact: { kind: "rational", value: volumeVal },
        annotation: { kind: "volume", category: "result", role: "result", subject_ids: [solidId], anchor: "solid" },
      },
    ],
    events: [
      { step_index: 0, action: "INIT", semantic_kind: "EXPLANATION" },
      { step_index: 1, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: baseId, depends: coords.map(([n]) => n) },
      { step_index: 2, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "canh_ben", objects: latIds, depends: latIds },
      { step_index: 3, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: solidId, depends: [apex, ...coords.map(([n]) => n)] },
      { step_index: 4, action: "MEASURE", semantic_kind: "FINAL_RESULT", object: "kq_hex_vol", depends: [solidId] },
    ],
  });
}

/**
 * Real Hybrid engine output for Case C (`hybrid_oblique_prism`: equilateral base `ABC` side `6`,
 * centroid `G` constructed via `G_mid_BC = midpoint(B, C)` and `divide_segment(A, G_mid_BC)`, `V = 18√3`).
 */
function makeObliquePrismCentroidScene(scaleOpts?: {
  g11: string;
  g12: string;
  g33: string;
  volDisplay: string;
}): Scene3D {
  const g11 = scaleOpts?.g11 ?? "36";
  const g12 = scaleOpts?.g12 ?? "18";
  const g33 = scaleOpts?.g33 ?? "4";
  const volDisplay = scaleOpts?.volDisplay ?? "18√3";
  return buildTestScene({
    chart_metric: [
      [g11, g12, "0"],
      [g12, g11, "0"],
      ["0", "0", g33],
    ],
    free_objects: ["A", "A_prime", "B", "B_prime", "C", "C_prime"],
    objects: [
      { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
      { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["1", "0", "0"] },
      { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", render: "point_marker", depends: [], xyz: ["0", "1", "0"] },
      { id: "A_prime", type: "point3", label: "Điểm A′", notation: "A′", origin: "free", render: "point_marker", depends: [], xyz: ["1/3", "1/3", "1"] },
      { id: "B_prime", type: "point3", label: "Điểm B′", notation: "B′", origin: "free", render: "point_marker", depends: [], xyz: ["4/3", "1/3", "1"] },
      { id: "C_prime", type: "point3", label: "Điểm C′", notation: "C′", origin: "free", render: "point_marker", depends: [], xyz: ["1/3", "4/3", "1"] },
      {
        id: "day_ABC",
        type: "polygon3",
        label: "Đáy dưới ABC",
        notation: "ABC",
        origin: "derived",
        producer: "construct_polygon",
        render: "polygon",
        depends: ["A", "B", "C"],
        formation_roles: ["CONSTRUCT_BASE"],
        surface_role: "BASE_REGION",
        polygon: [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"]],
        vertex_ids: ["A", "B", "C"],
      },
      {
        id: "day_A_primeB_primeC_prime",
        type: "polygon3",
        label: "Đáy trên A′B′C′",
        notation: "A′B′C′",
        origin: "derived",
        producer: "construct_polygon",
        render: "polygon",
        depends: ["A_prime", "B_prime", "C_prime"],
        formation_roles: ["CONSTRUCT_TRANSLATED_FACE"],
        surface_role: "BASE_REGION",
        polygon: [["1/3", "1/3", "1"], ["4/3", "1/3", "1"], ["1/3", "4/3", "1"]],
        vertex_ids: ["A_prime", "B_prime", "C_prime"],
      },
      { id: "canh_ben_A_A_prime", type: "segment3", label: "Cạnh bên AA′", notation: "AA′", origin: "derived", producer: "construct_segment", render: "segment", depends: ["A", "A_prime"], formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], point_a: ["0", "0", "0"], point_b: ["1/3", "1/3", "1"], endpoints: [["0", "0", "0"], ["1/3", "1/3", "1"]] },
      { id: "canh_ben_B_B_prime", type: "segment3", label: "Cạnh bên BB′", notation: "BB′", origin: "derived", producer: "construct_segment", render: "segment", depends: ["B", "B_prime"], formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], point_a: ["1", "0", "0"], point_b: ["4/3", "1/3", "1"], endpoints: [["1", "0", "0"], ["4/3", "1/3", "1"]] },
      { id: "canh_ben_C_C_prime", type: "segment3", label: "Cạnh bên CC′", notation: "CC′", origin: "derived", producer: "construct_segment", render: "segment", depends: ["C", "C_prime"], formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], point_a: ["0", "1", "0"], point_b: ["1/3", "4/3", "1"], endpoints: [["0", "1", "0"], ["1/3", "4/3", "1"]] },
      {
        id: "khoi_ABC_A_primeB_primeC_prime",
        type: "solid",
        label: "Lăng trụ ABC.A′B′C′",
        notation: "ABC.A′B′C′",
        shape_class: "PRISM_LIKE",
        origin: "derived",
        producer: "construct_solid",
        render: "mesh",
        depends: ["A", "A_prime", "B", "B_prime", "C", "C_prime"],
        formation_roles: ["CLOSE_SOLID"],
        vertex_ids: ["A", "B", "C", "A_prime", "B_prime", "C_prime"],
        vertices: [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"], ["1/3", "1/3", "1"], ["4/3", "1/3", "1"], ["1/3", "4/3", "1"]],
        faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]],
      },
      {
        id: "G_mid_BC",
        type: "point3",
        label: "Trung điểm của B và C",
        role: "Điểm",
        origin: "derived",
        producer: "construct_point.midpoint",
        render: "point_marker",
        depends: ["B", "C"],
        formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
        xyz: ["1/2", "1/2", "0"],
        source: { instruction: "construct_point.midpoint" },
      },
      {
        id: "G",
        type: "point3",
        label: "G",
        notation: "G",
        role: "Điểm chia đoạn nối A và «Trung điểm của B và C»",
        origin: "derived",
        producer: "construct_point.divide_segment",
        render: "point_marker",
        depends: ["A", "G_mid_BC"],
        formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
        xyz: ["1/3", "1/3", "0"],
        source: { instruction: "construct_point.divide_segment" },
      },
      {
        id: "kq_op6",
        type: "quantity",
        label: "Thể tích ABC.A′B′C′",
        notation: "V(ABC.A′B′C′)",
        origin: "derived",
        producer: "measure.volume",
        render: "readout",
        depends: ["khoi_ABC_A_primeB_primeC_prime"],
        value: volDisplay,
        annotation: { kind: "volume", category: "result", role: "result", subject_ids: ["khoi_ABC_A_primeB_primeC_prime"], anchor: "solid" },
      },
    ],
    events: [
      { step_index: 0, action: "INIT", semantic_kind: "EXPLANATION" },
      { step_index: 1, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "day_ABC", depends: ["A", "B", "C"] },
      { step_index: 2, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "day_A_primeB_primeC_prime", depends: ["A_prime", "B_prime", "C_prime"] },
      { step_index: 3, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "canh_ben", objects: ["canh_ben_A_A_prime", "canh_ben_B_B_prime", "canh_ben_C_C_prime"], depends: ["canh_ben_A_A_prime", "canh_ben_B_B_prime", "canh_ben_C_C_prime"] },
      { step_index: 4, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "khoi_ABC_A_primeB_primeC_prime", depends: ["A", "B", "C", "A_prime", "B_prime", "C_prime"] },
      { step_index: 5, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "G_mid_BC", depends: ["B", "C"] },
      { step_index: 6, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "G", depends: ["A", "G_mid_BC"] },
      { step_index: 7, action: "MEASURE", semantic_kind: "FINAL_RESULT", object: "kq_op6", depends: ["khoi_ABC_A_primeB_primeC_prime"] },
    ],
  });
}

describe("AXO Structured Construction Step Scaffolding & Provenance Audit (§3–§8)", () => {
  it("Case A: Rectangular pyramid 3×4, SA = 5 verifies GIVEN SA ⊥ (ABCD), cites V = 1/3·S(ABCD)·SA = 20, and never invents altitude when SA ⊥ (ABCD) is absent", () => {
    const certScene = makeRectPyramid345Scene(true);
    expect(verifySceneMathematicalConsistency(certScene).valid).toBe(true);

    // `phanTichToanHocCuaCanh` must surface `SA ⊥ (ABCD)` (`status: "GIVEN"`, `can_present_as_proven: false`) in `givenRelations`
    const analysis = phanTichToanHocCuaCanh(certScene, null);
    expect(analysis.givenRelations.some((r) => /SA\s*⊥/u.test(r.valueDisplay ?? "") || /SA/u.test(r.label))).toBe(true);

    const plan = buildPedagogicalConstructionPlan(withSubEntities(certScene));
    expect(plan.steps.map((s) => s.title)).toEqual([
      "Dựng đáy ABCD là hình chữ nhật",
      "Dựng đường cao SA ⊥ (ABCD) tại A",
      "Dựng các cạnh bên SB, SC, SD",
      "Hoàn thiện hình chóp S.ABCD",
    ]);
    // Pure answer/calculation step must NOT appear in the construction timeline (§4.3); metadata stays in goalCompletion
    expect(plan.steps.some((s) => s.epistemicCategory === "conclusion")).toBe(false);
    expect(plan.goalCompletion.items[0]?.valueText).toBe("20");

    // Adversarial counterpart: WITHOUT `SA ⊥ (ABCD)` witness, never promotes `SA` to altitude or claims `SA ⊥ (ABCD)`
    const uncertScene = makeRectPyramid345Scene(false);
    const uncertPlan = buildPedagogicalConstructionPlan(withSubEntities(uncertScene));
    expect(uncertPlan.steps.some((s) => /đường cao|⊥/iu.test(s.title))).toBe(false);
    expect(uncertPlan.steps.map((s) => s.title)).toEqual([
      "Dựng đáy ABCD là hình chữ nhật",
      "Dựng các cạnh bên SA, SB, SC, SD",
      "Hoàn thiện hình chóp S.ABCD",
    ]);
  });

  it("Case B: Regular hexagonal pyramid S.ABCDEF (and renamed variant P.MNQRST) withholds center O at Step 1, constructs certified altitude SO ⊥ (ABCDEF), and keeps volume out of timeline", () => {
    const hexScene = makeRegularHexagonalPyramidScene();
    expect(verifySceneMathematicalConsistency(hexScene).valid).toBe(true);
    const hexPlan = buildPedagogicalConstructionPlan(withSubEntities(hexScene));

    // O must NOT float unanchored at Step 1 (`Dựng đáy ABCDEF là lục giác đều`)
    expect(hexPlan.steps[0].title).toBe("Dựng đáy ABCDEF là lục giác đều");
    expect(hexPlan.steps[0].visibleIds).not.toContain("O");
    expect(hexPlan.steps[0].visibleIds).not.toContain("S");

    // Step 2 must construct center O and certified altitude SO ⊥ (ABCDEF) before lateral edges SA..SF
    expect(hexPlan.steps.length).toBe(4);
    expect(hexPlan.steps[1].title).toMatch(/tâm đáy O.*SO\s*⊥\s*\(ABCDEF\)|đường cao SO\s*⊥\s*\(ABCDEF\)\s*tại\s*O/iu);
    expect(hexPlan.steps[1].subtitle).toMatch(/chóp đều.*tâm.*O/iu);
    expect(hexPlan.steps[1].visibleIds).toContain("O");
    expect(hexPlan.steps[1].visibleIds).toContain("S");
    const altObj = hexPlan.scene.objects.find((o) => o.id === "khoi_S_ABCDEF__altitude");
    expect(altObj).toBeDefined();
    expect(altObj?.authoritative).toBe(false);
    expect(altObj?.perpendicular_witness?.foot_id).toBe("O");

    expect(hexPlan.steps[2].title).toBe("Dựng các cạnh bên SA, SB, SC, SD, SE, SF");
    expect(hexPlan.steps[3].title).toMatch(/^Hoàn thiện hình chóp.*S\.ABCDEF$/u);
    expect(hexPlan.steps.some((s) => s.epistemicCategory === "conclusion")).toBe(false);
    expect(hexPlan.goalCompletion.items[0]?.valueText).toBe("12");

    // Unseen scaled + renamed regular hexagonal pyramid `P.MNQRST` with center `J` (base edge 3, height 4√3 => V = 54)
    const renamedHex = makeRegularHexagonalPyramidScene({
      apex: "P",
      center: "J",
      baseNames: ["M", "N", "Q", "R", "S", "T"],
      baseSq: "9",
      halfNegBaseSq: "-9/2",
      heightSq: "48",
      volumeVal: "54",
    });
    const renamedPlan = buildPedagogicalConstructionPlan(withSubEntities(renamedHex));
    expect(renamedPlan.steps[0].visibleIds).not.toContain("J");
    expect(renamedPlan.steps[1].title).toMatch(/J.*PJ\s*⊥\s*\(MNQRST\)|PJ\s*⊥\s*\(MNQRST\).*J/u);
    expect(renamedPlan.steps[2].title).toBe("Dựng các cạnh bên PM, PN, PQ, PR, PS, PT");
    expect(renamedPlan.goalCompletion.items[0]?.valueText).toBe("54");
  });

  it("Case C: Oblique prism centroid G shows temporary midpoint + median helper at G's step, retires both afterward, and matches narration to divide_segment (2/3)", () => {
    for (const [scene, expectedVol] of [
      [makeObliquePrismCentroidScene(), "18√3"],
      [makeObliquePrismCentroidScene({ g11: "64", g12: "32", g33: "44/3", volDisplay: "32√11" }), "32√11"],
    ] as const) {
      expect(verifySceneMathematicalConsistency(scene).valid).toBe(true);
      const plan = buildPedagogicalConstructionPlan(withSubEntities(scene));
      const gStep = plan.steps.find((st) => st.targetIds.includes("G"))!;
      expect(gStep).toBeDefined();

      // Narration & tooltip must match the actual `divide_segment(A, G_mid_BC)` construction (2/3 of median from A to midpoint of BC), NOT claim intersection of multiple medians
      expect(gStep.subtitle).not.toMatch(/giao điểm các đường trung tuyến/iu);
      expect(gStep.subtitle).toMatch(/trung tuyến.*A.*trung điểm.*BC.*2\/3/iu);
      const gTip = buildVerifiedObjectTooltip(plan.scene, "G", gStep.anchor)!;
      expect(gTip.body).toMatch(/trung tuyến.*2\/3|Trọng tâm.*ABC/iu);

      // Temporary scaffolding: helper midpoint `G_mid_BC` AND temporary median segment `G__median` are visible at `gStep.anchor` (aux=false) and hidden at subsequent steps!
      const medianSeg = plan.scene.objects.find((o) => o.id === "G__median");
      expect(medianSeg).toBeDefined();
      expect(medianSeg?.authoritative).toBe(false);

      const auxMap = auxiliaryObjects(plan.scene);
      expect(auxMap.get("G_mid_BC")?.loai).toBe("dung");
      expect(auxMap.get("G__median")?.loai).toBe("dung");

      const hiddenAtG = auxiliaryHiddenAt(plan.scene, gStep.anchor, false, null);
      expect(hiddenAtG.has("G_mid_BC")).toBe(false);
      expect(hiddenAtG.has("G__median")).toBe(false);

      const finalAnchor = plan.steps[plan.steps.length - 1].anchor;
      const hiddenAtFinal = auxiliaryHiddenAt(plan.scene, finalAnchor, false, null);
      expect(hiddenAtFinal.has("G_mid_BC")).toBe(true);
      expect(hiddenAtFinal.has("G__median")).toBe(true);
      // Toggling `showAux = true` reveals them on demand
      expect(auxiliaryHiddenAt(plan.scene, finalAnchor, true, null).size).toBe(0);

      const lastStep = plan.steps[plan.steps.length - 1];
      expect(lastStep.subtitle).not.toContain(expectedVol);
      expect(plan.goalCompletion.items.some((it) => it.valueText === expectedVol)).toBe(true);
    }
  });

  it("Case D: Cylinder distinguishes tilted right cylinder vs oblique cylinder even when OA · OO' = 0 on a single radius (§5.2.2)", () => {
    const truScene = catalogScene("tru-truc-xien");
    const plan = buildPedagogicalConstructionPlan(withSubEntities(truScene));
    expect(plan.steps.length).toBe(3);
    expect(plan.steps[0].visibleIds).toEqual(["O", "A", "tru__radius", "tru__base_bot"]);
    expect(plan.steps[0].visibleIds).not.toContain("O_prime");
    expect(plan.steps.some((s) => s.subtitle.includes("15π"))).toBe(false);

    // §5.2.2: Even when OA · OO′ = 0 on ONE single radius OA (`(0,2,0)·(3,0,4) = 0`), an explicit oblique cylinder (`Hình trụ xiên OO′`) is NOT certified perpendicular to the entire base plane!
    const singleRadiusPerpObliqueCyl = buildTestScene({
      free_objects: ["O", "O_prime", "A"],
      objects: [
        { id: "O", type: "point3", label: "O", notation: "O", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "O_prime", type: "point3", label: "O′", notation: "O′", origin: "free", render: "point", depends: [], xyz: ["3", "0", "4"] },
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["0", "2", "0"] },
        {
          id: "cyl_adv",
          type: "curved_solid",
          curved_kind: "cylinder",
          label: "Hình trụ xiên OO′",
          role: "Hình trụ xiên tâm O, O′",
          origin: "derived",
          render: "curved_solid",
          depends: ["O", "O_prime", "A"],
          anchor: ["0", "0", "0"],
          apex_or_top: ["3", "0", "4"],
          rim_point: ["0", "2", "0"],
          radius_sq: "4",
          height_sq: "25",
        },
      ],
      events: [
        { step_index: 0, action: "INIT" },
        { step_index: 1, action: "CREATE", object: "cyl_adv", depends: ["O", "O_prime", "A"] },
      ],
    });
    const orthoSingleRad = inspectAxialCurvedOrthogonality(singleRadiusPerpObliqueCyl, singleRadiusPerpObliqueCyl.objects[3]);
    expect(orthoSingleRad.isRightCertified).toBe(false);
    expect(orthoSingleRad.isOblique).toBe(true);
    expect(orthoSingleRad.isIllustrativeBasePlane).toBe(true);

    // True geometric oblique cylinder: `O=(0,0,0), O′=(1,0,3), A=(2,0,0)` in z=0 base (`OA · OO′ = 2 ≠ 0` with explicit base normal `(0,0,1)`)
    const trueObliqueCyl = buildTestScene({
      free_objects: ["O", "O_prime", "A"],
      objects: [
        { id: "O", type: "point3", label: "O", notation: "O", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "O_prime", type: "point3", label: "O′", notation: "O′", origin: "free", render: "point", depends: [], xyz: ["1", "0", "3"] },
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["2", "0", "0"] },
        { id: "c_bot", type: "circle3", label: "(O)", origin: "derived", render: "circle", surface_role: "BASE_REGION", depends: ["O", "A"], center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "4" },
        {
          id: "cyl_obl",
          type: "curved_solid",
          curved_kind: "cylinder",
          label: "Hình trụ tròn xoay",
          origin: "derived",
          render: "curved_solid",
          depends: ["O", "O_prime", "A"],
          anchor: ["0", "0", "0"],
          apex_or_top: ["1", "0", "3"],
          rim_point: ["2", "0", "0"],
          radius_sq: "4",
          height_sq: "9",
        },
      ],
      events: [
        { step_index: 0, action: "INIT" },
        { step_index: 1, action: "CREATE", object: "c_bot", depends: ["O", "A"] },
        { step_index: 2, action: "CREATE", object: "cyl_obl", depends: ["O", "O_prime", "A"] },
      ],
    });
    const orthoObl = inspectAxialCurvedOrthogonality(trueObliqueCyl, trueObliqueCyl.objects[4]);
    expect(orthoObl.isOblique).toBe(true);
    expect(orthoObl.isRightCertified).toBe(false);
  });

  it("Case E & F + Point-Line Distance: verifies MNPQ section closure/square proof, sphere & cone construction steps without answer leaks, and coincident-foot projection", () => {
    // Case E: `thiet-dien-chop`
    const tdScene = catalogScene("thiet-dien-chop");
    const tdPlan = buildPedagogicalConstructionPlan(withSubEntities(tdScene));
    expect(tdPlan.steps.length).toBe(10);
    expect(tdPlan.steps[8].title).toBe("Xác định giao điểm Q = SD ∩ (MNP)");
    expect(tdPlan.steps[9].title).toBe("Dựng các giao tuyến và hoàn thiện thiết diện (MNPQ)");
    // Consolidated Step 10 closes `fill_visible: true` while intermediate EXTEND sub-event (`anchor = 14`) had `fill_visible: false`
    const extSubAnchor = tdPlan.scene.events
      .map((e, idx) => (e.action === "EXTEND" && e.object === "thiet_dien" ? idx : -1))
      .filter((idx) => idx >= 0)
      .pop()!;
    const progExt = tdPlan.scene.formation?.steps[extSubAnchor]?.geometry_progress?.[0];
    const progFinal = tdPlan.scene.formation?.steps[tdPlan.steps[9].anchor]?.geometry_progress?.[0];
    expect(progExt?.fill_visible).toBe(false);
    expect(progFinal?.fill_visible).toBe(true);
    // Study Dock SSR normalizes raw `"Thiết diện NMQP"` to `(MNPQ)` and mobile problem badge SVG carries explicit 14x14 bounds (preventing mobile canvas occlusion)
    const tdHtml = renderToString(<AxoWorkspaceV62 scene={tdScene} tieuDe="Thiết diện hình chóp" />);
    expect(tdHtml).not.toContain("NMQP");
    expect(tdHtml).toMatch(/id="canvas-mobile-prob-badge"[\s\S]*?<svg[^>]*width="14"[\s\S]*?height="14"/u);

    // Case F: `cau-the-tich`, `cau-cat-mat-phang`, `non-duong-sinh`
    const cauVolPlan = buildPedagogicalConstructionPlan(withSubEntities(catalogScene("cau-the-tich")));
    expect(cauVolPlan.steps.length).toBe(1);
    expect(cauVolPlan.steps.some((s) => s.subtitle.includes("36π"))).toBe(false);
    expect(cauVolPlan.goalCompletion.items.map((it) => it.valueText)).toContain("36π");

    const cauCutPlan = buildPedagogicalConstructionPlan(withSubEntities(catalogScene("cau-cat-mat-phang")));
    expect(cauCutPlan.steps[0].visibleIds).toEqual(expect.arrayContaining(["I", "cau__ref_pt", "cau__radius", "cau"]));
    expect(cauCutPlan.steps[1].visibleIds).toEqual(expect.arrayContaining(["I", "cau__ref_pt", "cau__radius", "cau", "P"]));
    expect(cauCutPlan.steps[2].visibleIds).toEqual(expect.arrayContaining(["P", "C__center", "C__dist"]));
    expect(cauCutPlan.steps[3].visibleIds).toEqual(expect.arrayContaining(["C__rim_pt", "C__sec_rad", "C__sph_rad"]));
    expect(cauCutPlan.steps[4].subtitle).toMatch(/hình\s+chiếu\s+vuông\s+góc/iu);
    expect(cauCutPlan.steps[4].subtitle).not.toContain("R² = d² + r²");
    expect(cauCutPlan.steps[4].subtitle).not.toContain("16π");

    const nonPlan = buildPedagogicalConstructionPlan(withSubEntities(catalogScene("non-duong-sinh")));
    expect(nonPlan.steps[0].visibleIds).not.toContain("S");
    expect(nonPlan.steps.length).toBe(4);
    expect(nonPlan.steps.some((s) => /^Tính /iu.test(s.title))).toBe(false);

    // Point-to-line distance where projection foot H coincides with B (`d(S, BC) = SB = 5` with `annotation.kind = "length"`)
    const ptLineScene = buildTestScene({
      free_objects: ["A", "B", "C", "D", "S"],
      objects: [
        { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["3", "0", "0"] },
        { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", render: "point_marker", depends: [], xyz: ["3", "3", "0"] },
        { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", render: "point_marker", depends: [], xyz: ["0", "3", "0"] },
        { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
        { id: "day_ABCD", type: "polygon3", label: "Đáy ABCD", notation: "ABCD", origin: "derived", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C", "D"], polygon: [["0", "0", "0"], ["3", "0", "0"], ["3", "3", "0"], ["0", "3", "0"]] },
        { id: "khoi_S_ABCD", type: "solid", label: "Hình chóp S.ABCD", notation: "S.ABCD", shape_class: "PYRAMID_LIKE", origin: "derived", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["A", "B", "C", "D", "S"], vertex_ids: ["S", "A", "B", "C", "D"], vertices: [["0", "0", "4"], ["0", "0", "0"], ["3", "0", "0"], ["3", "3", "0"], ["0", "3", "0"]], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]] },
        { id: "derived_H_line", type: "line3", label: "Đường thẳng qua B và C", origin: "derived", render: "line", formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"], depends: ["B", "C"], point: ["3", "0", "0"], direction: ["0", "3", "0"] },
        {
          id: "H",
          type: "point3",
          label: "H",
          notation: "H",
          origin: "derived",
          render: "point_marker",
          formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
          depends: ["S", "derived_H_line"],
          xyz: ["3", "0", "0"],
          perpendicular_witness: {
            from: "S",
            on: "derived_H_line",
            foot: ["3", "0", "0"],
            relation: "point_line_projection",
            marker: { u: ["0", "1", "0"], v: ["-3", "0", "4"] },
          },
        },
        {
          id: "kq_pl5",
          type: "quantity",
          label: "Khoảng cách giữa S và BC",
          notation: "d(S, BC)",
          origin: "derived",
          render: "readout",
          depends: ["H", "S"],
          value: "5",
          annotation: { kind: "length", category: "result", role: "result", subject_ids: ["S", "H"], anchor: "segment" },
        },
      ],
      events: [
        { step_index: 0, action: "INIT", semantic_kind: "EXPLANATION" },
        { step_index: 1, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "day_ABCD", depends: ["A", "B", "C", "D"] },
        { step_index: 2, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "khoi_S_ABCD", depends: ["A", "B", "C", "D", "S"] },
        { step_index: 3, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "derived_H_line", depends: ["B", "C"] },
        { step_index: 4, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "H", depends: ["S", "derived_H_line"] },
        { step_index: 5, action: "MEASURE", semantic_kind: "FINAL_RESULT", object: "kq_pl5", depends: ["H", "S"] },
      ],
    });
    const ptLinePlan = buildPedagogicalConstructionPlan(withSubEntities(ptLineScene));
    const lastPtLine = ptLinePlan.steps[ptLinePlan.steps.length - 1];
    expect(lastPtLine.title).toContain("H");
    expect(lastPtLine.title).not.toContain("(d = 5)");
    expect(lastPtLine.subtitle).toMatch(/H\s*(?:≡|trùng)\s*B/u);
    expect(lastPtLine.subtitle).not.toContain("SB = 5");
  });

  it("§7 & §8: Step-transition determinism (1..N, 1->N, N->1->N), vertex-renaming invariance (S.ABCD -> K.EFGH), and 7 adversarial safety checks", () => {
    // 1. Step transition invariants across all 11 public catalog samples
    for (const sample of GEOMETRY_SAMPLES) {
      const base = catalogScene(sample.id);
      const plan = buildPedagogicalConstructionPlan(withSubEntities(base));
      expect(plan.steps.length).toBeGreaterThanOrEqual(sample.id === "cau-the-tich" ? 1 : 2);

      const snapshotAt = (stepIdx: number) => {
        const anchor = plan.steps[stepIdx].anchor;
        const ungrounded = ungroundedFreePointIdsAt(plan.scene, anchor);
        const hiddenAux = auxiliaryHiddenAt(plan.scene, anchor, false, null);
        return objectsAt(plan.scene, anchor)
          .filter((o) => !isSubEntity(o.id) && o.render !== "readout" && o.render !== "non_visual" && !ungrounded.has(o.id) && !hiddenAux.has(o.id))
          .map((o) => o.id)
          .sort();
      };

      const forwardSnaps = plan.steps.map((_, i) => snapshotAt(i));
      // Jump 1 -> N matches sequential arrival at N
      expect(snapshotAt(plan.steps.length - 1)).toEqual(forwardSnaps[forwardSnaps.length - 1]);
      // Backward N -> 1 -> N reproduces identical state at every step
      for (let i = plan.steps.length - 1; i >= 0; i -= 1) {
        expect(snapshotAt(i)).toEqual(forwardSnaps[i]);
      }
      // Zero consecutive steps differing only in title without visual/conclusion delta
      for (let i = 1; i < plan.steps.length; i += 1) {
        const prev = plan.steps[i - 1];
        const curr = plan.steps[i];
        if (curr.epistemicCategory !== "conclusion") {
          const sameVis = JSON.stringify(prev.visibleIds) === JSON.stringify(curr.visibleIds);
          const prevProg = JSON.stringify(plan.scene.formation?.steps[prev.anchor]?.geometry_progress ?? []);
          const currProg = JSON.stringify(plan.scene.formation?.steps[curr.anchor]?.geometry_progress ?? []);
          expect(sameVis && prevProg === currProg, `${sample.id} step ${i + 1}: ${curr.title}`).toBe(false);
        }
      }
    }

    // 2. Vertex-renaming invariance: `S.ABCD` + `(SBC)` vs `K.EFGH` + `(KFG)` (structural apex `K` placed first in `(KFG)`, not hardcoded `"S"`!)
    const buildPlaneOnPyramid = (apex: string, b0: string, b1: string, b2: string, b3: string): Scene3D =>
      buildTestScene({
        free_objects: [b0, b1, b2, b3, apex],
        objects: [
          { id: b0, type: "point3", label: b0, notation: b0, origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
          { id: b1, type: "point3", label: b1, notation: b1, origin: "free", render: "point", depends: [], xyz: ["4", "0", "0"] },
          { id: b2, type: "point3", label: b2, notation: b2, origin: "free", render: "point", depends: [], xyz: ["4", "4", "0"] },
          { id: b3, type: "point3", label: b3, notation: b3, origin: "free", render: "point", depends: [], xyz: ["0", "4", "0"] },
          { id: apex, type: "point3", label: apex, notation: apex, origin: "free", render: "point", depends: [], xyz: ["0", "0", "4"] },
          { id: "base", type: "polygon3", label: `Đáy ${b0}${b1}${b2}${b3}`, notation: `${b0}${b1}${b2}${b3}`, origin: "derived", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: [b0, b1, b2, b3], polygon: [["0", "0", "0"], ["4", "0", "0"], ["4", "4", "0"], ["0", "4", "0"]], vertex_ids: [b0, b1, b2, b3] },
          { id: "pyr", type: "solid", label: `Hình chóp ${apex}.${b0}${b1}${b2}${b3}`, notation: `${apex}.${b0}${b1}${b2}${b3}`, shape_class: "PYRAMID_LIKE", origin: "derived", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: [b0, b1, b2, b3, apex], vertex_ids: [apex, b0, b1, b2, b3], vertices: [["0", "0", "4"], ["0", "0", "0"], ["4", "0", "0"], ["4", "4", "0"], ["0", "4", "0"]], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]] },
          // Deliberately pass `depends: [b0, b2, apex]` (`A, C, S` vs `E, G, K`) on diagonal plane `(SAC)` / `(KEG)` so structural apex-first canonicalization is tested!
          { id: "mp_diag", type: "plane3", label: `Mặt phẳng qua ${b0}, ${b2}, ${apex}`, origin: "derived", render: "surface", depends: [b0, b2, apex], point: ["0", "0", "0"], normal: ["1", "-1", "0"] },
        ],
        events: [
          { step_index: 0, action: "INIT" },
          { step_index: 1, action: "CREATE", object: "base", depends: [b0, b1, b2, b3] },
          { step_index: 2, action: "CREATE", object: "pyr", depends: [b0, b1, b2, b3, apex] },
          { step_index: 3, action: "CREATE", object: "mp_diag", depends: [b0, b2, apex] },
        ],
      });

    const planS = buildPedagogicalConstructionPlan(withSubEntities(buildPlaneOnPyramid("S", "A", "B", "C", "D")));
    const planK = buildPedagogicalConstructionPlan(withSubEntities(buildPlaneOnPyramid("K", "E", "F", "G", "H")));
    expect(planS.steps.length).toBe(planK.steps.length);
    expect(planS.steps[planS.steps.length - 1].title).toBe("Dựng mặt phẳng (SAC)");
    expect(planK.steps[planK.steps.length - 1].title).toBe("Dựng mặt phẳng (KEG)");

    // 3. Adversarial checks across §8 categories:
    // (a) Contradictory hypothesis (`midpoint` coordinate disagrees with `(A+B)/2`)
    const forgedMidpoint = buildTestScene({
      free_objects: ["A", "B"],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point", depends: [], xyz: ["4", "0", "0"] },
        { id: "M", type: "point3", label: "Trung điểm M", notation: "M", origin: "derived", producer: "construct_point.midpoint", render: "point", depends: ["A", "B"], xyz: ["3", "0", "0"] },
      ],
      events: [{ step_index: 0, action: "INIT" }, { step_index: 1, action: "CREATE", object: "M", depends: ["A", "B"] }],
    });
    expect(verifySceneMathematicalConsistency(forgedMidpoint).valid).toBe(false);

    // (b) Intersection outside segment forged as lying on segment (`t = 3/2 > 1` on `AB` with `source.instruction = "intersect_segment_plane"`)
    const exteriorSegmentIntersection = buildTestScene({
      free_objects: ["A", "B"],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point", depends: [], xyz: ["2", "0", "0"] },
        { id: "seg_AB", type: "segment3", label: "Đoạn AB", notation: "AB", origin: "derived", render: "segment", depends: ["A", "B"], point_a: ["0", "0", "0"], point_b: ["2", "0", "0"], endpoints: [["0", "0", "0"], ["2", "0", "0"]] },
        { id: "mp_cut", type: "plane3", label: "(α)", origin: "free", render: "surface", depends: [], point: ["3", "0", "0"], normal: ["1", "0", "0"] },
        { id: "Q_ext", type: "point3", label: "Q", notation: "Q", origin: "derived", render: "point", depends: ["seg_AB", "mp_cut"], source: { instruction: "intersect_segment_plane" }, xyz: ["3", "0", "0"] },
      ],
      events: [
        { step_index: 0, action: "INIT" },
        { step_index: 1, action: "CREATE", object: "seg_AB", depends: ["A", "B"] },
        { step_index: 2, action: "CREATE", object: "Q_ext", depends: ["seg_AB", "mp_cut"] },
      ],
    });
    expect(verifySceneMathematicalConsistency(exteriorSegmentIntersection).valid).toBe(false);

    // (c) Parallel / coincident planes claiming a unique intersection line
    const parallelPlanesIntersection = buildTestScene({
      free_objects: [],
      objects: [
        { id: "p1", type: "plane3", label: "(α)", origin: "free", render: "surface", depends: [], point: ["0", "0", "0"], normal: ["0", "0", "1"] },
        { id: "p2", type: "plane3", label: "(β)", origin: "free", render: "surface", depends: [], point: ["0", "0", "2"], normal: ["0", "0", "2"] },
        { id: "gt", type: "line3", label: "Giao tuyến", origin: "derived", render: "line", depends: ["p1", "p2"], source: { instruction: "intersect_plane_plane" }, point: ["0", "0", "0"], direction: ["1", "0", "0"] },
      ],
      events: [{ step_index: 0, action: "INIT" }, { step_index: 1, action: "CREATE", object: "gt", depends: ["p1", "p2"] }],
    });
    expect(verifySceneMathematicalConsistency(parallelPlanesIntersection).valid).toBe(false);

    // (d) Degenerate / non-unique plane through 3 collinear points + coincident planes + degenerate zero-length segment
    const collinearPlane = buildTestScene({
      free_objects: ["A", "B", "C"],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point", depends: [], xyz: ["1", "0", "0"] },
        { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point", depends: [], xyz: ["2", "0", "0"] },
        { id: "mp", type: "plane3", label: "(ABC)", origin: "derived", render: "surface", depends: ["A", "B", "C"], point: ["0", "0", "0"], normal: ["0", "0", "1"] },
      ],
      events: [{ step_index: 0, action: "INIT" }, { step_index: 1, action: "CREATE", object: "mp", depends: ["A", "B", "C"] }],
    });
    expect(verifySceneMathematicalConsistency(collinearPlane).valid).toBe(false);

    const coincidentPlanes = buildTestScene({
      free_objects: [],
      objects: [
        { id: "p1", type: "plane3", label: "(α)", origin: "free", render: "surface", depends: [], point: ["0", "0", "0"], normal: ["0", "0", "1"] },
        { id: "p2", type: "plane3", label: "(β)", origin: "free", render: "surface", depends: [], point: ["1", "2", "0"], normal: ["0", "0", "-3"] },
        { id: "gt", type: "line3", label: "Giao tuyến", origin: "derived", render: "line", depends: ["p1", "p2"], source: { instruction: "intersect_plane_plane" }, point: ["0", "0", "0"], direction: ["1", "0", "0"] },
      ],
      events: [{ step_index: 0, action: "INIT" }, { step_index: 1, action: "CREATE", object: "gt", depends: ["p1", "p2"] }],
    });
    expect(verifySceneMathematicalConsistency(coincidentPlanes).valid).toBe(false);

    const degenerateSegment = buildTestScene({
      free_objects: ["A"],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["1", "2", "3"] },
        { id: "seg_AA", type: "segment3", label: "AA", notation: "AA", origin: "derived", render: "segment", depends: ["A"], point_a: ["1", "2", "3"], point_b: ["1", "2", "3"] },
      ],
      events: [{ step_index: 0, action: "INIT" }, { step_index: 1, action: "CREATE", object: "seg_AA", depends: ["A"] }],
    });
    expect(verifySceneMathematicalConsistency(degenerateSegment).valid).toBe(false);
  });

  it("§8 Full Cross-Family Matrix: verifies unseen non-hardcoded variants across all 8 geometry groups + monolithic solid sub-entity decomposition & DAG closure", () => {
    // Unseen 1: Monolithic triangular pyramid `T.UVX` (backend emits ONLY `solid` + `quantity`, testing §7 sub-entity decomposition + altitude TU ⊥ (UVX), V = 72)
    const unseenTriPyramidMonolithic = buildTestScene({
      free_objects: ["U", "V", "X", "T"],
      objects: [
        { id: "U", type: "point3", label: "Điểm U", notation: "U", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "V", type: "point3", label: "Điểm V", notation: "V", origin: "free", render: "point", depends: [], xyz: ["6", "0", "0"] },
        { id: "X", type: "point3", label: "Điểm X", notation: "X", origin: "free", render: "point", depends: [], xyz: ["0", "8", "0"] },
        { id: "T", type: "point3", label: "Điểm T", notation: "T", origin: "free", render: "point", depends: [], xyz: ["0", "0", "9"] },
        {
          id: "seg_TU",
          type: "segment3",
          label: "Cạnh bên TU",
          notation: "TU",
          origin: "derived",
          render: "segment",
          depends: ["U", "T"],
          point_a: ["0", "0", "0"],
          point_b: ["0", "0", "9"],
          perpendicular_witness: {
            from: "T",
            on: "khoi_TUVX",
            foot: ["0", "0", "0"],
            foot_id: "U",
            relation: "line_perp_plane",
            status: "GIVEN",
            certificate: "exact-gram-line-plane-orthogonality/1",
            can_present_as_proven: false,
            plane_directions: [["1", "0", "0"], ["0", "1", "0"]],
            marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] },
          },
        },
        {
          id: "khoi_TUVX",
          type: "solid",
          label: "Hình chóp T.UVX",
          role: "Tam giác UVX vuông tại U",
          notation: "T.UVX",
          shape_class: "PYRAMID_LIKE",
          origin: "derived",
          render: "mesh",
          depends: ["U", "V", "X", "T"],
          vertex_ids: ["T", "U", "V", "X"],
          vertices: [["0", "0", "9"], ["0", "0", "0"], ["6", "0", "0"], ["0", "8", "0"]],
          faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]],
        },
        {
          id: "vol_TUVX",
          type: "quantity",
          label: "Thể tích T.UVX",
          notation: "V(T.UVX)",
          origin: "derived",
          render: "readout",
          depends: ["khoi_TUVX"],
          value: "72",
          annotation: { kind: "volume", category: "result", role: "result", subject_ids: ["khoi_TUVX"], anchor: "solid" },
        },
      ],
      events: [
        { step_index: 0, action: "INIT" },
        { step_index: 1, action: "CREATE", object: "seg_TU", depends: ["U", "T"] },
        { step_index: 2, action: "CREATE", object: "khoi_TUVX", depends: ["U", "V", "X", "T"] },
        { step_index: 3, action: "MEASURE", semantic_kind: "FINAL_RESULT", object: "vol_TUVX", depends: ["khoi_TUVX"] },
      ],
    });

    // Unseen 2: Right quadrangular prism `EFGH.E′F′G′H′` + cross-section `(MF′G′H)` where `M` is midpoint of `EE′`
    const unseenRightPrismSection = buildTestScene({
      free_objects: ["E", "F", "G", "H", "Ep", "Fp", "Gp", "Hp"],
      objects: [
        { id: "E", type: "point3", label: "E", notation: "E", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "F", type: "point3", label: "F", notation: "F", origin: "free", render: "point", depends: [], xyz: ["3", "0", "0"] },
        { id: "G", type: "point3", label: "G", notation: "G", origin: "free", render: "point", depends: [], xyz: ["3", "4", "0"] },
        { id: "H", type: "point3", label: "H", notation: "H", origin: "free", render: "point", depends: [], xyz: ["0", "4", "0"] },
        { id: "Ep", type: "point3", label: "E′", notation: "E′", origin: "free", render: "point", depends: [], xyz: ["0", "0", "6"] },
        { id: "Fp", type: "point3", label: "F′", notation: "F′", origin: "free", render: "point", depends: [], xyz: ["3", "0", "6"] },
        { id: "Gp", type: "point3", label: "G′", notation: "G′", origin: "free", render: "point", depends: [], xyz: ["3", "4", "6"] },
        { id: "Hp", type: "point3", label: "H′", notation: "H′", origin: "free", render: "point", depends: [], xyz: ["0", "4", "6"] },
        { id: "day_EFGH", type: "polygon3", label: "Đáy EFGH", notation: "EFGH", origin: "derived", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["E", "F", "G", "H"], polygon: [["0", "0", "0"], ["3", "0", "0"], ["3", "4", "0"], ["0", "4", "0"]], vertex_ids: ["E", "F", "G", "H"] },
        { id: "day_EpFpGpHp", type: "polygon3", label: "Đáy E′F′G′H′", notation: "E′F′G′H′", origin: "derived", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_TRANSLATED_FACE"], depends: ["Ep", "Fp", "Gp", "Hp"], polygon: [["0", "0", "6"], ["3", "0", "6"], ["3", "4", "6"], ["0", "4", "6"]], vertex_ids: ["Ep", "Fp", "Gp", "Hp"] },
        { id: "prism_EFGH", type: "solid", label: "Lăng trụ đứng EFGH.E′F′G′H′", notation: "EFGH.E′F′G′H′", shape_class: "PRISM_LIKE", origin: "derived", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["E", "F", "G", "H", "Ep", "Fp", "Gp", "Hp"], vertex_ids: ["E", "F", "G", "H", "Ep", "Fp", "Gp", "Hp"], vertices: [["0", "0", "0"], ["3", "0", "0"], ["3", "4", "0"], ["0", "4", "0"], ["0", "0", "6"], ["3", "0", "6"], ["3", "4", "6"], ["0", "4", "6"]], faces: [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]] },
        { id: "M", type: "point3", label: "Trung điểm M", notation: "M", origin: "derived", producer: "construct_point.midpoint", render: "point", depends: ["E", "Ep"], xyz: ["0", "0", "3"] },
        { id: "N", type: "point3", label: "Trung điểm N", notation: "N", origin: "derived", producer: "construct_point.midpoint", render: "point", depends: ["H", "Hp"], xyz: ["0", "4", "3"] },
        { id: "mp_cut_pr", type: "plane3", label: "Mặt phẳng (MF′G′)", origin: "derived", render: "surface", depends: ["M", "Fp", "Gp"], point: ["0", "0", "3"], normal: ["-1", "0", "1"] },
        { id: "sec_pr", type: "section", label: "Thiết diện MF′G′N", notation: "MF′G′N", origin: "derived", render: "polygon", depends: ["prism_EFGH", "mp_cut_pr", "M", "Fp", "Gp", "N"], polygon: [["0", "0", "3"], ["3", "0", "6"], ["3", "4", "6"], ["0", "4", "3"]] },
      ],
      events: [
        { step_index: 0, action: "INIT" },
        { step_index: 1, action: "CREATE", object: "day_EFGH", depends: ["E", "F", "G", "H"] },
        { step_index: 2, action: "CREATE", object: "day_EpFpGpHp", depends: ["Ep", "Fp", "Gp", "Hp"] },
        { step_index: 3, action: "CREATE", object: "prism_EFGH", depends: ["E", "F", "G", "H", "Ep", "Fp", "Gp", "Hp"] },
        { step_index: 4, action: "CREATE", object: "M", depends: ["E", "Ep"] },
        { step_index: 5, action: "CREATE", object: "N", depends: ["H", "Hp"] },
        { step_index: 6, action: "CREATE", object: "mp_cut_pr", depends: ["M", "Fp", "Gp"] },
        { step_index: 7, action: "CREATE", object: "sec_pr", depends: ["prism_EFGH", "mp_cut_pr", "M", "Fp", "Gp", "N"] },
      ],
    });

    // Unseen 3: Two-plane intersection `(MAC) ∩ (SBD) = MO` where `M` is midpoint of `SB` and `O = AC ∩ BD` (non-altitude pyramid)
    const unseenTwoPlaneIntersection = buildTestScene({
      free_objects: ["A", "B", "C", "D", "S"],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point", depends: [], xyz: ["4", "0", "0"] },
        { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point", depends: [], xyz: ["4", "4", "0"] },
        { id: "D", type: "point3", label: "D", notation: "D", origin: "free", render: "point", depends: [], xyz: ["0", "4", "0"] },
        { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point", depends: [], xyz: ["1", "2", "5"] },
        { id: "day_ABCD", type: "polygon3", label: "Đáy ABCD", notation: "ABCD", origin: "derived", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C", "D"], polygon: [["0", "0", "0"], ["4", "0", "0"], ["4", "4", "0"], ["0", "4", "0"]], vertex_ids: ["A", "B", "C", "D"] },
        { id: "pyr", type: "solid", label: "Hình chóp S.ABCD", notation: "S.ABCD", shape_class: "PYRAMID_LIKE", origin: "derived", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["A", "B", "C", "D", "S"], vertex_ids: ["S", "A", "B", "C", "D"], vertices: [["1", "2", "5"], ["0", "0", "0"], ["4", "0", "0"], ["4", "4", "0"], ["0", "4", "0"]], faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]] },
        { id: "diag_AC", type: "segment3", label: "AC", notation: "AC", origin: "derived", render: "segment", depends: ["A", "C"], point_a: ["0", "0", "0"], point_b: ["4", "4", "0"] },
        { id: "diag_BD", type: "segment3", label: "BD", notation: "BD", origin: "derived", render: "segment", depends: ["B", "D"], point_a: ["4", "0", "0"], point_b: ["0", "4", "0"] },
        { id: "O", type: "point3", label: "O", notation: "O", origin: "derived", render: "point", depends: ["diag_AC", "diag_BD"], source: { instruction: "intersect_line_line" }, xyz: ["2", "2", "0"] },
        { id: "M", type: "point3", label: "M", notation: "M", origin: "derived", producer: "construct_point.midpoint", render: "point", depends: ["S", "B"], xyz: ["5/2", "1", "5/2"] },
        { id: "mp_MAC", type: "plane3", label: "(MAC)", origin: "derived", render: "surface", depends: ["M", "A", "C"], point: ["0", "0", "0"], normal: ["5", "-5", "-3"] },
        { id: "mp_SBD", type: "plane3", label: "(SBD)", origin: "derived", render: "surface", depends: ["S", "B", "D"], point: ["4", "0", "0"], normal: ["5", "5", "1"] },
        { id: "gt_MO", type: "line3", label: "Giao tuyến MO", notation: "MO", origin: "derived", render: "line", depends: ["mp_MAC", "mp_SBD"], source: { instruction: "intersect_plane_plane" }, point: ["2", "2", "0"], direction: ["1", "-2", "5"] },
      ],
      events: [
        { step_index: 0, action: "INIT" },
        { step_index: 1, action: "CREATE", object: "day_ABCD", depends: ["A", "B", "C", "D"] },
        { step_index: 2, action: "CREATE", object: "pyr", depends: ["A", "B", "C", "D", "S"] },
        { step_index: 3, action: "CREATE", object: "diag_AC", depends: ["A", "C"] },
        { step_index: 4, action: "CREATE", object: "diag_BD", depends: ["B", "D"] },
        { step_index: 5, action: "CREATE", object: "O", depends: ["diag_AC", "diag_BD"] },
        { step_index: 6, action: "CREATE", object: "M", depends: ["S", "B"] },
        { step_index: 7, action: "CREATE", object: "mp_MAC", depends: ["M", "A", "C"] },
        { step_index: 8, action: "CREATE", object: "mp_SBD", depends: ["S", "B", "D"] },
        { step_index: 9, action: "CREATE", object: "gt_MO", depends: ["mp_MAC", "mp_SBD"] },
      ],
    });

    // Unseen 4: Skew-line common perpendicular (`d(SA, BC) = AB = 3`), Point-Plane Distance (`d(E, (KFG)) = 12/5`), and Dihedral Angle (`((KFG), (EFG)) = 45°`)
    const unseenSkewDistAndDihedral = buildTestScene({
      free_objects: ["E", "F", "G", "K"],
      objects: [
        { id: "E", type: "point3", label: "E", notation: "E", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "F", type: "point3", label: "F", notation: "F", origin: "free", render: "point", depends: [], xyz: ["4", "0", "0"] },
        { id: "G", type: "point3", label: "G", notation: "G", origin: "free", render: "point", depends: [], xyz: ["4", "3", "0"] },
        { id: "K", type: "point3", label: "K", notation: "K", origin: "free", render: "point", depends: [], xyz: ["0", "0", "4"] },
        { id: "day_EFG", type: "polygon3", label: "Đáy EFG", notation: "EFG", origin: "derived", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["E", "F", "G"], polygon: [["0", "0", "0"], ["4", "0", "0"], ["4", "3", "0"]], vertex_ids: ["E", "F", "G"] },
        { id: "pyr_KEFG", type: "solid", label: "Hình chóp K.EFG", notation: "K.EFG", shape_class: "PYRAMID_LIKE", origin: "derived", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["E", "F", "G", "K"], vertex_ids: ["K", "E", "F", "G"], vertices: [["0", "0", "4"], ["0", "0", "0"], ["4", "0", "0"], ["4", "3", "0"]], faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]] },
        { id: "line_KE", type: "segment3", label: "KE", notation: "KE", origin: "derived", render: "segment", depends: ["K", "E"], point_a: ["0", "0", "4"], point_b: ["0", "0", "0"] },
        { id: "line_FG", type: "segment3", label: "FG", notation: "FG", origin: "derived", render: "segment", depends: ["F", "G"], point_a: ["4", "0", "0"], point_b: ["4", "3", "0"] },
        {
          id: "seg_EF_common",
          type: "segment3",
          label: "Đoạn vuông góc chung EF",
          notation: "EF",
          origin: "derived",
          render: "segment",
          depends: ["line_KE", "line_FG", "E", "F"],
          point_a: ["0", "0", "0"],
          point_b: ["4", "0", "0"],
          perpendicular_witness: {
            from: "F",
            on: "line_KE",
            foot: ["0", "0", "0"],
            foot_id: "E",
            relation: "common_perpendicular",
            marker: { u: ["0", "0", "1"], v: ["1", "0", "0"] },
            second: {
              from: "E",
              on: "line_FG",
              foot: ["4", "0", "0"],
              foot_id: "F",
              marker: { u: ["0", "1", "0"], v: ["-1", "0", "0"] },
            },
          },
        },
        { id: "H_proj", type: "point3", label: "H", notation: "H", origin: "derived", render: "point", depends: ["E", "K", "F"], xyz: ["2", "0", "2"] },
        { id: "mp_KFG", type: "plane3", label: "(KFG)", origin: "derived", render: "surface", depends: ["K", "F", "G"], point: ["4", "0", "0"], normal: ["1", "0", "1"] },
        {
          id: "seg_EH",
          type: "segment3",
          label: "EH",
          notation: "EH",
          origin: "derived",
          render: "segment",
          depends: ["E", "H_proj", "mp_KFG"],
          point_a: ["0", "0", "0"],
          point_b: ["2", "0", "2"],
          perpendicular_witness: {
            from: "E",
            on: "mp_KFG",
            foot: ["2", "0", "2"],
            foot_id: "H_proj",
            relation: "line_perp_plane",
            marker: { u: ["-1", "0", "1"], v: ["-1", "0", "-1"] },
          },
        },
        {
          id: "kq_skew",
          type: "quantity",
          label: "Khoảng cách giữa KE và FG",
          notation: "d(KE, FG)",
          origin: "derived",
          render: "readout",
          depends: ["seg_EF_common"],
          value: "4",
          annotation: { kind: "distance", category: "result", role: "result", subject_ids: ["line_KE", "line_FG"] },
        },
        {
          id: "kq_dih",
          type: "quantity",
          label: "Góc nhị diện ((KFG), (EFG))",
          notation: "((KFG),(EFG))",
          origin: "derived",
          render: "readout",
          depends: ["mp_KFG", "day_EFG"],
          value: "45°",
          annotation: { kind: "angle", category: "result", role: "result", subject_ids: ["mp_KFG", "day_EFG"] },
        },
      ],
      events: [
        { step_index: 0, action: "INIT" },
        { step_index: 1, action: "CREATE", object: "day_EFG", depends: ["E", "F", "G"] },
        { step_index: 2, action: "CREATE", object: "pyr_KEFG", depends: ["E", "F", "G", "K"] },
        { step_index: 3, action: "CREATE", object: "line_KE", depends: ["K", "E"] },
        { step_index: 4, action: "CREATE", object: "line_FG", depends: ["F", "G"] },
        { step_index: 5, action: "CREATE", object: "seg_EF_common", depends: ["line_KE", "line_FG", "E", "F"] },
        { step_index: 6, action: "CREATE", object: "mp_KFG", depends: ["K", "F", "G"] },
        { step_index: 7, action: "CREATE", object: "H_proj", depends: ["E", "K", "F"] },
        { step_index: 8, action: "CREATE", object: "seg_EH", depends: ["E", "H_proj", "mp_KFG"] },
        { step_index: 9, action: "MEASURE", semantic_kind: "FINAL_RESULT", object: "kq_skew", depends: ["seg_EF_common"] },
        { step_index: 10, action: "MEASURE", semantic_kind: "FINAL_RESULT", object: "kq_dih", depends: ["mp_KFG", "day_EFG"] },
      ],
    });

    // Unseen 5: Cone (`V_cone`, `I`, `B`, `R=5, h=12, l=13`) & Sphere cut by inclined plane (`J`, `R=13, d=5, r=12`)
    const unseenCone51213 = buildTestScene({
      free_objects: ["I", "V_ap", "B_rim"],
      objects: [
        { id: "I", type: "point3", label: "I", notation: "I", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "V_ap", type: "point3", label: "V", notation: "V", origin: "free", render: "point", depends: [], xyz: ["0", "0", "12"] },
        { id: "B_rim", type: "point3", label: "B", notation: "B", origin: "free", render: "point", depends: [], xyz: ["5", "0", "0"] },
        { id: "cone_u", type: "curved_solid", curved_kind: "cone", label: "Hình nón đỉnh V", origin: "derived", render: "curved_solid", depends: ["I", "V_ap", "B_rim"], anchor: ["0", "0", "0"], apex_or_top: ["0", "0", "12"], rim_point: ["5", "0", "0"], radius_sq: "25", height_sq: "144" },
        { id: "kq_cone_v", type: "quantity", label: "Thể tích hình nón", notation: "V", origin: "derived", render: "readout", depends: ["cone_u"], value: "100π", annotation: { kind: "volume", category: "result", role: "result", subject_ids: ["cone_u"] } },
        { id: "kq_cone_s", type: "quantity", label: "Diện tích xung quanh", notation: "Sxq", origin: "derived", render: "readout", depends: ["cone_u"], value: "65π", annotation: { kind: "area", category: "result", role: "result", subject_ids: ["cone_u"] } },
      ],
      events: [
        { step_index: 0, action: "INIT" },
        { step_index: 1, action: "CREATE", object: "cone_u", depends: ["I", "V_ap", "B_rim"] },
        { step_index: 2, action: "MEASURE", semantic_kind: "FINAL_RESULT", object: "kq_cone_v", depends: ["cone_u"] },
        { step_index: 3, action: "MEASURE", semantic_kind: "FINAL_RESULT", object: "kq_cone_s", depends: ["cone_u"] },
      ],
    });

    const unseenSphereCut135 = buildTestScene({
      free_objects: ["J", "H_c"],
      objects: [
        { id: "J", type: "point3", label: "J", notation: "J", origin: "free", render: "point", depends: [], xyz: ["0", "0", "0"] },
        { id: "H_c", type: "point3", label: "H", notation: "H", origin: "free", render: "point", depends: [], xyz: ["3", "0", "4"] },
        { id: "sph_J", type: "curved_solid", curved_kind: "sphere", label: "Mặt cầu (J)", origin: "derived", render: "curved_solid", depends: ["J"], anchor: ["0", "0", "0"], radius_sq: "169" },
        { id: "mp_P", type: "plane3", label: "(P)", origin: "derived", render: "surface", depends: [], point: ["3", "0", "4"], normal: ["3", "0", "4"] },
        { id: "cir_cut", type: "circle3", label: "Đường tròn giao tuyến", origin: "derived", render: "circle", surface_role: "INTERSECTION_OR_SECTION", depends: ["sph_J", "mp_P", "H_c"], center: ["3", "0", "4"], normal: ["3", "0", "4"], radius_sq: "144" },
      ],
      events: [
        { step_index: 0, action: "INIT" },
        { step_index: 1, action: "CREATE", object: "sph_J", depends: ["J"] },
        { step_index: 2, action: "CREATE", object: "mp_P", depends: [] },
        { step_index: 3, action: "CREATE", object: "cir_cut", depends: ["sph_J", "mp_P", "H_c"] },
      ],
    });

    const matrixCases: [string, Scene3D][] = [
      ["unseen_tri_pyramid_monolithic", unseenTriPyramidMonolithic],
      ["unseen_right_prism_section", unseenRightPrismSection],
      ["unseen_two_plane_intersection", unseenTwoPlaneIntersection],
      ["unseen_skew_dist_and_dihedral", unseenSkewDistAndDihedral],
      ["unseen_cone_5_12_13", unseenCone51213],
      ["unseen_sphere_cut_13_5", unseenSphereCut135],
    ];

    for (const [name, scene] of matrixCases) {
      const consistency = verifySceneMathematicalConsistency(scene);
      expect(consistency.valid, `${name}: ${JSON.stringify(consistency.contradictions)}`).toBe(true);

      const expanded = withSubEntities(scene);
      const plan = buildPedagogicalConstructionPlan(expanded);
      expect(plan.steps.length, name).toBeGreaterThanOrEqual(3);

      // Unique object IDs & DAG dependency closure across every step `k`
      const allIds = plan.scene.objects.map((o) => o.id);
      expect(new Set(allIds).size, `${name} duplicate IDs`).toBe(allIds.length);
      const byId = new Map(plan.scene.objects.map((o) => [o.id, o]));

      for (let k = 0; k < plan.steps.length; k += 1) {
        const anchor = plan.steps[k].anchor;
        const presentIds = new Set(objectsAt(plan.scene, anchor).map((o) => o.id));
        for (const id of presentIds) {
          const obj = byId.get(id);
          if (!obj || isSubEntity(obj.id)) continue;
          for (const depId of obj.depends ?? []) {
            if (byId.has(depId)) {
              expect(presentIds.has(depId), `${name} step ${k + 1}: ${id} missing dep ${depId}`).toBe(true);
            }
          }
        }
        const ungroundedAtK = ungroundedFreePointIdsAt(plan.scene, anchor);
        const visiblePresentIds = new Set(
          objectsAt(plan.scene, anchor)
            .filter((o) => !ungroundedAtK.has(o.id))
            .map((o) => o.id),
        );
        // Future-step newly constructed objects and future conclusion readouts must NEVER appear at step `k`
        for (let f = k + 1; f < plan.steps.length; f += 1) {
          const futStep = plan.steps[f];
          if (futStep.epistemicCategory !== "conclusion") {
            for (const futureId of futStep.targetIds) {
              expect(visiblePresentIds.has(futureId), `${name} step ${k + 1} leaks future ${futureId}`).toBe(false);
            }
          }
          const futEv = plan.scene.events[futStep.anchor];
          if (futEv?.action === "MEASURE" && futEv.object) {
            expect(presentIds.has(futEv.object), `${name} step ${k + 1} leaks future readout ${futEv.object}`).toBe(false);
          }
        }
      }
    }

    // Specific mathematical & pedagogical assertions on the unseen matrix cases:
    const triExpanded = withSubEntities(unseenTriPyramidMonolithic);
    // Monolithic solid is decomposed into sub-entity faces & edges (`khoi_TUVX::face:...`, `khoi_TUVX::edge:...`) AND decomposed into Base -> Altitude -> Lateral edges -> Solid -> Volume!
    expect(triExpanded.objects.some((o) => isSubEntity(o.id))).toBe(true);
    const triPlan = buildPedagogicalConstructionPlan(triExpanded);
    expect(triPlan.steps.map((s) => s.title)).toEqual([
      "Dựng đáy UVX là tam giác vuông",
      "Dựng đường cao TU ⊥ (UVX) tại U",
      "Dựng các cạnh bên TV, TX",
      "Hoàn thiện hình chóp T.UVX",
    ]);
    expect(triPlan.goalCompletion.items[0]?.valueText).toBe("72");

    const conePlan = buildPedagogicalConstructionPlan(withSubEntities(unseenCone51213));
    expect(conePlan.steps[0].visibleIds).toEqual(["I", "B_rim", "cone_u__radius", "cone_u__base_bot"]);
    expect(conePlan.steps[0].visibleIds).not.toContain("V_ap");
    expect(conePlan.steps.some((s) => s.subtitle.includes("100π") || s.subtitle.includes("65π"))).toBe(false);
    expect(conePlan.goalCompletion.items.map((it) => it.valueText)).toContain("100π");
    expect(conePlan.goalCompletion.items.map((it) => it.valueText)).toContain("65π");
  });
});
