import * as THREE from "three";
import { describe, expect, it } from "vitest";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import circumsphereFixture from "./scene3d-circumsphere-fixture.json";
import inscribedFixtures from "./scene3d-inscribed-circumscribed-fixtures.json";
import archetypeFixtures from "./scene3d-regression-archetypes-fixtures.json";
import sectionFixture from "./scene3d-section-fixture.json";
import { veKhongGian } from "./scene3d-chart";
import {
  clampStep,
  objectsAt,
  stepCount,
  toNumber,
  toVec3,
  type ExactVec3,
  type Scene3D,
  type SceneObject,
  type Vec3,
} from "./scene3d-model";
import { auditSceneRepresentationConsistency } from "./scene3d-representation-consistency";
import {
  buildContractReferenceGroup,
  buildPedagogicalConstructionPlan,
  resolveAdaptivePlaneVisualization,
  resolveCertifiedRightAngleMarkers,
  resolveStepGoalKind,
  resolveStepVisualRoles,
  resolveVerifiedAngleArcs,
  verifyVisualContinuity,
} from "./scene3d-semantic-policy";
import {
  STEP_GOAL_LABELS,
  STEP_GOAL_PRESENTATION_POLICY,
  type StepGoalKind,
} from "./scene3d-student-presentation-policy";

interface InventoryEntry {
  id: string;
  source: "catalog" | "fixture";
  scene: Scene3D;
}

const VALID_STEP_GOALS = new Set<StepGoalKind>([
  "Define",
  "Construct",
  "Intersect",
  "Verify",
  "Measure",
  "Complete",
]);

function extractCatalogScene(id: string): Scene3D {
  const found = GEOMETRY_SAMPLES.find((s) => s.id === id);
  if (!found) throw new Error(`Missing catalog sample: ${id}`);
  return (found.envelope as unknown as { scene3d: Scene3D }).scene3d;
}

function collectFullInventory(): InventoryEntry[] {
  const entries: InventoryEntry[] = GEOMETRY_SAMPLES.map((s) => ({
    id: s.id,
    source: "catalog",
    scene: (s.envelope as unknown as { scene3d: Scene3D }).scene3d,
  }));

  entries.push(
    {
      id: "fixture:circumsphere",
      source: "fixture",
      scene: circumsphereFixture as unknown as Scene3D,
    },
    {
      id: "fixture:section",
      source: "fixture",
      scene: sectionFixture as unknown as Scene3D,
    },
    {
      id: "fixture:base_circles_square_pyramid",
      source: "fixture",
      scene: (inscribedFixtures as unknown as Record<string, { scene3d: Scene3D }>).base_circles_square_pyramid.scene3d,
    },
    {
      id: "fixture:insphere_square_pyramid",
      source: "fixture",
      scene: (inscribedFixtures as unknown as Record<string, { scene3d: Scene3D }>).insphere_square_pyramid.scene3d,
    },
    {
      id: "fixture:multi_layer_aux_pyramid",
      source: "fixture",
      scene: (archetypeFixtures as unknown as Record<string, { scene3d: Scene3D }>).multi_layer_aux_pyramid.scene3d,
    },
    {
      id: "fixture:coincident_elements_pyramid",
      source: "fixture",
      scene: (archetypeFixtures as unknown as Record<string, { scene3d: Scene3D }>).coincident_elements_pyramid.scene3d,
    },
  );
  return entries;
}

function deepFreeze<T>(value: T): T {
  if (!value || typeof value !== "object") return value;
  Object.freeze(value);
  for (const val of Object.values(value as Record<string, unknown>)) {
    if (val && typeof val === "object" && !Object.isFrozen(val)) {
      deepFreeze(val);
    }
  }
  return value;
}

function extractGuidePairs(group: THREE.Group | null, prefix: string): Array<{
  name: string;
  a: Vec3;
  b: Vec3;
}> {
  if (!group) return [];
  const out: Array<{ name: string; a: Vec3; b: Vec3 }> = [];
  for (const child of group.children) {
    if (!child.name.startsWith(prefix)) continue;
    let endpoints: Vec3[] | null = null;
    child.traverse((node) => {
      if (!endpoints && node instanceof THREE.Line) {
        const pos = node.geometry.getAttribute("position");
        if (pos && pos.count >= 2) {
          endpoints = [
            [pos.getX(0), pos.getY(0), pos.getZ(0)],
            [pos.getX(pos.count - 1), pos.getY(pos.count - 1), pos.getZ(pos.count - 1)],
          ];
        }
      }
    });
    if (endpoints) {
      out.push({ name: child.name, a: endpoints[0], b: endpoints[1] });
    }
  }
  return out;
}

function matchesSegmentEndpoints(pair: { a: Vec3; b: Vec3 }, p: Vec3, q: Vec3, tol = 1e-4): boolean {
  const d = (u: Vec3, v: Vec3) => Math.hypot(u[0] - v[0], u[1] - v[1], u[2] - v[2]);
  return (d(pair.a, p) <= tol && d(pair.b, q) <= tol) || (d(pair.a, q) <= tol && d(pair.b, p) <= tol);
}

function transformScene(
  rawScene: Scene3D,
  mapVec3: (v: Vec3) => Vec3,
  mapNormal: (n: Vec3) => Vec3,
): Scene3D {
  const fmt = (v: Vec3): ExactVec3 => [
    `${Math.round(v[0] * 1_000_000)}/1000000`,
    `${Math.round(v[1] * 1_000_000)}/1000000`,
    `${Math.round(v[2] * 1_000_000)}/1000000`,
  ];
  const shiftPoint = (ev: ExactVec3 | undefined | null): ExactVec3 | undefined =>
    ev ? fmt(mapVec3(toVec3(ev))) : undefined;
  const shiftVec = (ev: ExactVec3 | undefined | null): ExactVec3 | undefined =>
    ev ? fmt([mapVec3(toVec3(ev))[0] - mapVec3([0, 0, 0])[0], mapVec3(toVec3(ev))[1] - mapVec3([0, 0, 0])[1], mapVec3(toVec3(ev))[2] - mapVec3([0, 0, 0])[2]]) : undefined;

  const scaleFactor = Math.hypot(
    mapVec3([1, 0, 0])[0] - mapVec3([0, 0, 0])[0],
    mapVec3([1, 0, 0])[1] - mapVec3([0, 0, 0])[1],
    mapVec3([1, 0, 0])[2] - mapVec3([0, 0, 0])[2],
  );

  return {
    ...rawScene,
    chart_metric: undefined,
    objects: rawScene.objects.map((o): SceneObject => ({
      ...o,
      xyz: shiftPoint(o.xyz),
      point: shiftPoint(o.point),
      direction: shiftVec(o.direction),
      point_a: shiftPoint(o.point_a),
      point_b: shiftPoint(o.point_b),
      endpoints: o.endpoints?.map((ep) => fmt(mapVec3(toVec3(ep)))),
      normal: o.normal ? fmt(mapNormal(toVec3(o.normal))) : undefined,
      vertices: o.vertices?.map((vx) => fmt(mapVec3(toVec3(vx)))),
      polygon: o.polygon?.map((vx) => fmt(mapVec3(toVec3(vx)))),
      center: shiftPoint(o.center),
      anchor: shiftPoint(o.anchor),
      apex_or_top: o.apex_or_top ? shiftPoint(o.apex_or_top) : o.apex_or_top,
      rim_point: shiftPoint(o.rim_point),
      radius_sq:
        o.radius_sq !== undefined
          ? `${Math.round(toNumber(o.radius_sq) * scaleFactor * scaleFactor * 1_000_000)}/1000000`
          : undefined,
      steps: o.steps?.map((st) => ({
        ...st,
        a: fmt(mapVec3(toVec3(st.a))),
        b: fmt(mapVec3(toVec3(st.b))),
      })),
      perpendicular_witness: o.perpendicular_witness
        ? {
            ...o.perpendicular_witness,
            foot: fmt(mapVec3(toVec3(o.perpendicular_witness.foot))),
            marker: {
              ...o.perpendicular_witness.marker,
              u: shiftVec(o.perpendicular_witness.marker.u)!,
              v: shiftVec(o.perpendicular_witness.marker.v)!,
            },
          }
        : undefined,
      annotation: o.annotation?.witness
        ? {
            ...o.annotation,
            witness: {
              ...o.annotation.witness,
              foot: fmt(mapVec3(toVec3(o.annotation.witness.foot))),
              marker: {
                ...o.annotation.witness.marker,
                u: shiftVec(o.annotation.witness.marker.u)!,
                v: shiftVec(o.annotation.witness.marker.v)!,
              },
              second: o.annotation.witness.second
                ? {
                    ...o.annotation.witness.second,
                    foot: fmt(mapVec3(toVec3(o.annotation.witness.second.foot))),
                    marker: {
                      ...o.annotation.witness.second.marker,
                      u: shiftVec(o.annotation.witness.second.marker.u)!,
                      v: shiftVec(o.annotation.witness.second.marker.v)!,
                    },
                  }
                : undefined,
            },
          }
        : o.annotation,
    })),
  };
}

describe("AXO V9.4.15 — System-Wide Step Integrity, Coplanar Guides & Mathematical Invariants", () => {
  const inventory = collectFullInventory();

  it("Step-Aware Presentation Policy exports complete 6-stage metadata with Construct fallback for minimal scenes", () => {
    for (const kind of VALID_STEP_GOALS) {
      expect(STEP_GOAL_LABELS[kind].length).toBeGreaterThan(0);
      expect(STEP_GOAL_PRESENTATION_POLICY[kind].goal).toBe(kind);
    }

    const minimalScene: Scene3D = {
      free_objects: [],
      objects: [
        { id: "A", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"], label: "A" },
        { id: "B", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["2", "0", "0"], label: "B" },
        { id: "AB", type: "segment3", render: "segment", origin: "derived", producer: "segment", depends: ["A", "B"], point_a: ["0", "0", "0"], point_b: ["2", "0", "0"], label: "AB" },
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "AB", depends: ["A", "B"], explanation: "Nối A và B." },
      ],
    };
    expect(resolveStepGoalKind(minimalScene, 0)).toBe("Construct");
  });

  it(`Full Repository Inventory (${inventory.length} scenes): representation consistency, continuity, step goals, scrub determinism & immutability across ALL steps`, () => {
    expect(inventory.length).toBe(28);

    for (const entry of inventory) {
      const frozenInput = deepFreeze(structuredClone(entry.scene));
      const continuity = verifyVisualContinuity(frozenInput);
      expect(continuity.valid, `${entry.id} continuity violations: ${JSON.stringify(continuity.violations)}`).toBe(true);
      expect(continuity.dimensions.geometric, `${entry.id} geometric`).toBe(true);
      expect(continuity.dimensions.semantic, `${entry.id} semantic`).toBe(true);
      expect(continuity.dimensions.visual, `${entry.id} visual`).toBe(true);
      expect(continuity.dimensions.pedagogical, `${entry.id} pedagogical`).toBe(true);

      const totalSteps = Math.max(1, stepCount(frozenInput));
      const worldScene = veKhongGian(frozenInput);
      const plan = buildPedagogicalConstructionPlan(frozenInput);
      for (const ps of plan.steps) {
        expect(ps.stepGoal).toBeDefined();
        expect(VALID_STEP_GOALS.has(ps.stepGoal!)).toBe(true);
      }

      const forwardRoles: string[] = [];
      for (let s = 0; s < totalSteps; s += 1) {
        const rep = auditSceneRepresentationConsistency(frozenInput, { step: s, bypassCache: true });
        expect(
          rep.overallStatus,
          `${entry.id} step ${s} failed consistency: ${JSON.stringify(rep.findings)}`,
        ).toBe(rep.sceneScale > 0 ? "VALID" : "UNDETERMINED");

        const goal = resolveStepGoalKind(worldScene, s);
        expect(VALID_STEP_GOALS.has(goal), `${entry.id} step ${s} invalid goal ${goal}`).toBe(true);

        const roles = resolveStepVisualRoles(worldScene, clampStep(worldScene, s), {
          auxiliaryShown: false,
          selectedId: null,
        });
        forwardRoles.push(
          JSON.stringify([...roles.entries()].map(([id, r]) => [id, r.role, r.presentationTier, r.stepGoal, r.visible]).sort()),
        );
      }

      // Backward scrubbing must produce bitwise identical role signatures at every step
      for (let s = totalSteps - 1; s >= 0; s -= 1) {
        const rolesBack = resolveStepVisualRoles(worldScene, clampStep(worldScene, s), {
          auxiliaryShown: false,
          selectedId: null,
        });
        const sig = JSON.stringify(
          [...rolesBack.entries()].map(([id, r]) => [id, r.role, r.presentationTier, r.stepGoal, r.visible]).sort(),
        );
        expect(sig, `${entry.id} backward scrub mismatch at step ${s}`).toBe(forwardRoles[s]);
      }
    }
  });

  it("Case 1 (chop-thiet-dien-ba-diem): F ∈ SD & (MNP), coplanar guides bridge exterior E/F during Intersect steps and retire upon thiet_dien Complete", () => {
    const raw = extractCatalogScene("chop-thiet-dien-ba-diem");
    const scene = veKhongGian(raw);
    const pt = (id: string) => toVec3(scene.objects.find((o) => o.id === id)!.xyz!);
    const M = pt("M");
    const N = pt("N");
    const P = pt("P");
    const E = pt("E");
    const F = pt("F");
    const S = pt("S");
    const D = pt("D");

    // Exact mathematical incidence: F lies on segment SD and on cutting plane (MNP)
    const sd = [D[0] - S[0], D[1] - S[1], D[2] - S[2]];
    const tF = ((F[0] - S[0]) * sd[0] + (F[1] - S[1]) * sd[1] + (F[2] - S[2]) * sd[2])
      / (sd[0] * sd[0] + sd[1] * sd[1] + sd[2] * sd[2]);
    expect(tF).toBeGreaterThan(0);
    expect(tF).toBeLessThan(1);
    const mpMnp = scene.objects.find((o) => o.id === "mp_MNP")!;
    const p0 = toVec3(mpMnp.point!);
    const nVec = toVec3(mpMnp.normal!);
    const distF = Math.abs((F[0] - p0[0]) * nVec[0] + (F[1] - p0[1]) * nVec[1] + (F[2] - p0[2]) * nVec[2])
      / Math.hypot(nVec[0], nVec[1], nVec[2]);
    expect(distF).toBeLessThan(1e-7);

    // EV[13] (intersect E): E connected along faces SAB (M-E) & SBC (N-E), while △MNP stays minimal
    expect(resolveStepGoalKind(scene, 13)).toBe("Intersect");
    const vis13 = objectsAt(scene, 13);
    expect(resolveAdaptivePlaneVisualization(scene, mpMnp, vis13).mode).toBe("MINIMAL_GEOMETRY");
    const guides13 = extractGuidePairs(buildContractReferenceGroup(scene, vis13, 13), "coplanar_guide:");
    expect(guides13.some((g) => matchesSegmentEndpoints(g, M, E))).toBe(true);
    expect(guides13.some((g) => matchesSegmentEndpoints(g, N, E))).toBe(true);

    // EV[14] (intersect F): F ALSO connected along faces SAD (M-F) & SCD (P-F), zero oversized triangle
    expect(resolveStepGoalKind(scene, 14)).toBe("Intersect");
    const vis14 = objectsAt(scene, 14);
    expect(resolveAdaptivePlaneVisualization(scene, mpMnp, vis14).patchVertices).toHaveLength(3);
    const guides14 = extractGuidePairs(buildContractReferenceGroup(scene, vis14, 14), "coplanar_guide:");
    expect(guides14.some((g) => matchesSegmentEndpoints(g, M, F))).toBe(true);
    expect(guides14.some((g) => matchesSegmentEndpoints(g, P, F))).toBe(true);

    // EV[20] (thiet_dien closed): all temporary coplanar guides retire cleanly
    expect(resolveStepGoalKind(scene, 20)).toBe("Complete");
    const vis20 = objectsAt(scene, 20);
    const guides20 = extractGuidePairs(buildContractReferenceGroup(scene, vis20, 20), "coplanar_guide:");
    expect(guides20).toHaveLength(0);
  });

  it("Case 2 (Oxyz): interior intersection emits 0 redundant guides; synthetic exterior Oxyz intersection receives coplanar guide", () => {
    const rawOxyz = extractCatalogScene("oxyz-giao-diem-duong-mat");
    const oxyz = veKhongGian(rawOxyz);
    const finalStep = stepCount(oxyz) - 1;
    const visFinal = objectsAt(oxyz, finalStep);
    const oxyzGuides = extractGuidePairs(buildContractReferenceGroup(oxyz, visFinal, finalStep), "coplanar_guide:");
    expect(oxyzGuides).toHaveLength(0);

    // Exterior Oxyz intersection I_ext = (3, 1, -2) on plane x + y + z = 2 outside △ABC((2,0,0),(0,2,0),(0,0,2))
    const synthExt: Scene3D = {
      free_objects: ["A", "B", "C", "mp_P", "d_ext"],
      events: [
        { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Hệ Oxyz" },
        { step_index: 1, action: "CREATE", object: "mp_P", depends: ["A", "B", "C"], explanation: "Mặt phẳng (P)" },
        { step_index: 2, action: "CREATE", object: "d_ext", depends: [], explanation: "Đường thẳng d" },
        { step_index: 3, action: "CREATE", object: "I_ext", depends: ["d_ext", "mp_P"], explanation: "Giao điểm I = d ∩ (P)" },
      ],
      objects: [
        { id: "A", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["2", "0", "0"], label: "A" },
        { id: "B", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "2", "0"], label: "B" },
        { id: "C", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "0", "2"], label: "C" },
        {
          id: "mp_P",
          type: "plane3",
          render: "surface",
          origin: "free",
          producer: "construct_plane",
          depends: ["A", "B", "C"],
          point: ["2", "0", "0"],
          normal: ["1", "1", "1"],
          surface_role: "CUTTING_PLANE",
          label: "(P)",
        },
        {
          id: "d_ext",
          type: "line3",
          render: "line",
          origin: "free",
          producer: "construct_line",
          depends: [],
          point: ["3", "1", "0"],
          direction: ["0", "0", "1"],
          label: "d",
        },
        {
          id: "I_ext",
          type: "point3",
          render: "point_marker",
          origin: "derived",
          producer: "construct_point.intersect_line_plane",
          depends: ["d_ext", "mp_P"],
          xyz: ["3", "1", "-2"],
          label: "I",
        },
      ],
    };
    const guidesExt = extractGuidePairs(buildContractReferenceGroup(synthExt, synthExt.objects, 3), "coplanar_guide:");
    expect(guidesExt.length).toBeGreaterThanOrEqual(1);
    expect(resolveStepGoalKind(synthExt, 3)).toBe("Intersect");
  });

  it("Cases 3 & 4 (Cube & Triangular Prism Sections): intermediate coplanar guides appear cleanly and retire on section close", () => {
    const cases = [
      { id: "lap-phuong-thiet-dien-bat-ky", interStep: 14, closedStep: 21 },
      { id: "lang-tru-tam-giac-thiet-dien", interStep: 12, closedStep: 18 },
    ];
    for (const tc of cases) {
      const scene = veKhongGian(extractCatalogScene(tc.id));
      expect(resolveStepGoalKind(scene, tc.interStep)).toBe("Intersect");
      const visInter = objectsAt(scene, tc.interStep);
      const guidesInter = extractGuidePairs(buildContractReferenceGroup(scene, visInter, tc.interStep), "coplanar_guide:");
      expect(guidesInter.length, `${tc.id} should emit coplanar guides at intersection step`).toBeGreaterThanOrEqual(2);

      expect(resolveStepGoalKind(scene, tc.closedStep)).toBe("Complete");
      const visClosed = objectsAt(scene, tc.closedStep);
      const guidesClosed = extractGuidePairs(buildContractReferenceGroup(scene, visClosed, tc.closedStep), "coplanar_guide:");
      expect(guidesClosed, `${tc.id} should retire temporary coplanar guides once section closes`).toHaveLength(0);
    }
  });

  it("Case 5 (Angles, Distances & Perpendiculars): zero spurious guides on foot/project points; verified markers & angle arcs satisfy orthogonality", () => {
    const angleDistIds = [
      "khoang-cach-diem-mat-phang-nghieng",
      "goc-nhi-dien-hai-mat-phang",
      "khoang-cach-hai-duong-cheo-nhau",
      "vuong-goc-chop",
      "mp-vuong-goc-duong",
    ];
    for (const id of angleDistIds) {
      const scene = veKhongGian(extractCatalogScene(id));
      const finalStep = stepCount(scene) - 1;
      const visFinal = objectsAt(scene, finalStep);
      const guides = extractGuidePairs(buildContractReferenceGroup(scene, visFinal, finalStep), "coplanar_guide:");
      expect(guides, `${id} should not emit spurious coplanar guides on foot/project points`).toHaveLength(0);

      const markers = resolveCertifiedRightAngleMarkers(scene, visFinal);
      for (const m of markers) {
        const uLen = Math.hypot(m.rayU[0], m.rayU[1], m.rayU[2]);
        const vLen = Math.hypot(m.rayV[0], m.rayV[1], m.rayV[2]);
        expect(uLen).toBeGreaterThan(1e-6);
        expect(vLen).toBeGreaterThan(1e-6);
        const cos = Math.abs(m.rayU[0] * m.rayV[0] + m.rayU[1] * m.rayV[1] + m.rayU[2] * m.rayV[2]) / (uLen * vLen);
        expect(cos).toBeLessThan(1e-3);
      }

      const arcs = resolveVerifiedAngleArcs(scene, visFinal);
      for (const arc of arcs) {
        expect(arc.radius).toBeGreaterThan(0);
        expect(arc.arcPoints.length).toBeGreaterThanOrEqual(2);
        const aLen = Math.hypot(arc.rayADir[0], arc.rayADir[1], arc.rayADir[2]);
        const bLen = Math.hypot(arc.rayBDir[0], arc.rayBDir[1], arc.rayBDir[2]);
        expect(aLen).toBeCloseTo(1, 3);
        expect(bLen).toBeCloseTo(1, 3);
      }
    }
  });

  it("Case 6 (Curved Solids): 24-point curved surface checks & standalone sphere tangent plane equality pass", () => {
    const curvedIds = [
      "mat-cau-cat-mat-phang",
      "mat-phang-tiep-xuc-mat-cau",
      "hinh-non-cat-song-song-day",
      "non-thiet-dien-truc",
      "tru-thiet-dien-tron",
      "tru-truc-xien",
      "chop-mat-cau-ngoai-tiep",
    ];
    for (const id of curvedIds) {
      const raw = extractCatalogScene(id);
      const rep = auditSceneRepresentationConsistency(raw, { step: stepCount(raw) - 1, bypassCache: true });
      expect(rep.overallStatus, `${id} findings: ${JSON.stringify(rep.findings)}`).toBe("VALID");
      expect(rep.checks.intersection_consistency.status).toBe("VALID");
    }
  });

  it("Adversarial & Metamorphic Invariants: defects caught deterministically; carrier extension & rigid/scale symmetries hold", () => {
    // 1. Off-plane derived intersect point caught
    const badPlanePoint: Scene3D = {
      free_objects: ["A", "B", "C", "mp_P", "d_ln"],
      events: [{ step_index: 0, action: "CREATE", object: "I_bad", depends: ["d_ln", "mp_P"], explanation: "bad" }],
      objects: [
        { id: "A", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"], label: "A" },
        { id: "B", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["2", "0", "0"], label: "B" },
        { id: "C", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "2", "0"], label: "C" },
        { id: "mp_P", type: "plane3", render: "surface", origin: "free", producer: "construct_plane", depends: ["A", "B", "C"], point: ["0", "0", "0"], normal: ["0", "0", "1"], label: "(P)" },
        { id: "d_ln", type: "line3", render: "line", origin: "free", producer: "construct_line", depends: [], point: ["1", "1", "0"], direction: ["0", "0", "1"], label: "d" },
        { id: "I_bad", type: "point3", render: "point_marker", origin: "derived", producer: "construct_point.intersect_line_plane", depends: ["d_ln", "mp_P"], xyz: ["1", "1", "1"], label: "I" },
      ],
    };
    const repBadPlane = auditSceneRepresentationConsistency(badPlanePoint, { bypassCache: true });
    expect(repBadPlane.overallStatus).toBe("INVALID");
    expect(repBadPlane.checks.point_on_plane.status).toBe("INVALID");

    // 2. Off-line derived intersect point caught
    const badLinePoint: Scene3D = {
      ...badPlanePoint,
      objects: badPlanePoint.objects.map((o) =>
        o.id === "I_bad" ? { ...o, xyz: ["2", "2", "0"] as ExactVec3 } : o,
      ),
    };
    const repBadLine = auditSceneRepresentationConsistency(badLinePoint, { bypassCache: true });
    expect(repBadLine.overallStatus).toBe("INVALID");
    expect(repBadLine.checks.point_on_line.status).toBe("INVALID");

    // 3. Self-intersecting bowtie section polygon caught
    const bowtieScene: Scene3D = {
      free_objects: [],
      events: [{ step_index: 0, action: "CREATE", object: "bow", depends: [], explanation: "bowtie" }],
      objects: [
        {
          id: "bow",
          type: "section",
          render: "polygon",
          origin: "derived",
          producer: "construct_section",
          depends: [],
          polygon: [
            ["0", "0", "0"],
            ["2", "2", "0"],
            ["0", "2", "0"],
            ["2", "0", "0"],
          ],
          closed: true,
          label: "Bowtie",
        },
      ],
    };
    const repBowtie = auditSceneRepresentationConsistency(bowtieScene, { bypassCache: true });
    expect(repBowtie.overallStatus).toBe("INVALID");
    expect(repBowtie.checks.section_connectivity.status).toBe("INVALID");

    // 4. Off-surface circle on sphere caught by 24-point sampler
    const badSphereCircle: Scene3D = {
      free_objects: [],
      events: [{ step_index: 0, action: "CREATE", object: "c_bad", depends: ["ball_1"], explanation: "bad circle" }],
      objects: [
        { id: "ball_1", type: "curved_solid", render: "curved_solid", origin: "free", curved_kind: "ball", producer: null, depends: [], anchor: ["0", "0", "0"], radius_sq: "9", label: "S" },
        { id: "mp_P", type: "plane3", render: "surface", origin: "free", producer: null, depends: [], point: ["0", "0", "0"], normal: ["0", "0", "1"], label: "P" },
        { id: "c_bad", type: "circle3", render: "circle", origin: "derived", producer: "intersect", depends: ["ball_1", "mp_P"], center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "16", label: "C" },
      ],
    };
    const repBadCircle = auditSceneRepresentationConsistency(badSphereCircle, { bypassCache: true });
    expect(repBadCircle.overallStatus).toBe("INVALID");
    expect(repBadCircle.checks.intersection_consistency.status).toBe("INVALID");

    // 5. Non-orthogonal perpendicular_witness.marker caught
    const badWitnessMarker: Scene3D = {
      free_objects: ["A", "B", "H"],
      events: [{ step_index: 0, action: "CREATE", object: "H", depends: [], explanation: "bad marker" }],
      objects: [
        { id: "A", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "0", "3"], label: "A" },
        { id: "B", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["3", "0", "0"], label: "B" },
        { id: "mp_P", type: "plane3", render: "surface", origin: "free", producer: null, depends: [], point: ["0", "0", "0"], normal: ["0", "0", "1"], label: "(P)" },
        {
          id: "H",
          type: "point3",
          render: "point_marker",
          origin: "derived",
          producer: "foot",
          depends: ["A", "mp_P"],
          xyz: ["0", "0", "0"],
          perpendicular_witness: {
            from: "A",
            on: "mp_P",
            foot: ["0", "0", "0"],
            marker: { u: ["1", "0", "1"], v: ["0", "0", "1"] },
          },
          label: "H",
        },
      ],
    };
    const repBadMarker = auditSceneRepresentationConsistency(badWitnessMarker, { bypassCache: true });
    expect(repBadMarker.overallStatus).toBe("INVALID");
    expect(repBadMarker.checks.mesh_consistency.status).toBe("INVALID");

    // 6. Collinear point on segment extension (t = 3/2) emits CARRIER_EXTENSION_GUIDE
    const extSegScene: Scene3D = {
      free_objects: ["A", "B", "seg_AB"],
      events: [
        { step_index: 0, action: "CREATE", object: "seg_AB", depends: ["A", "B"], explanation: "AB" },
        { step_index: 1, action: "EXTEND", object: "K", depends: ["seg_AB"], explanation: "K trên tia đối BA" },
      ],
      objects: [
        { id: "A", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"], label: "A" },
        { id: "B", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["2", "0", "0"], label: "B" },
        { id: "seg_AB", type: "segment3", render: "segment", origin: "free", producer: "segment", depends: ["A", "B"], point_a: ["0", "0", "0"], point_b: ["2", "0", "0"], endpoint_ids: ["A", "B"], label: "AB" },
        { id: "K", type: "point3", render: "point_marker", origin: "derived", producer: "construct_point.intersect_line_plane", depends: ["seg_AB"], xyz: ["3", "0", "0"], label: "K" },
      ],
    };
    const extGuides = extractGuidePairs(buildContractReferenceGroup(extSegScene, extSegScene.objects, 1), "carrier_extension:");
    expect(extGuides).toHaveLength(1);
    expect(matchesSegmentEndpoints(extGuides[0], [2, 0, 0], [3, 0, 0])).toBe(true);

    // 7. Metamorphic symmetries: scale (0.05x, 25x, 200x), translation [+120,-85,+40], axis permutation (x,y,z)->(y,z,x)
    const sampleIds = ["chop-thiet-dien-ba-diem", "mat-cau-cat-mat-phang"];
    for (const id of sampleIds) {
      const world = veKhongGian(extractCatalogScene(id));
      for (const factor of [0.05, 25, 200]) {
        const scaled = transformScene(
          world,
          ([x, y, z]) => [x * factor, y * factor, z * factor],
          (n) => n,
        );
        const rep = auditSceneRepresentationConsistency(scaled, { step: stepCount(scaled) - 1, bypassCache: true });
        expect(rep.overallStatus, `${id} scale ${factor}x failed: ${JSON.stringify(rep.findings)}`).toBe("VALID");
      }
      const shiftedPermuted = transformScene(
        world,
        ([x, y, z]) => [y + 120, z - 85, x + 40],
        ([nx, ny, nz]) => [ny, nz, nx],
      );
      const repShift = auditSceneRepresentationConsistency(shiftedPermuted, {
        step: stepCount(shiftedPermuted) - 1,
        bypassCache: true,
      });
      expect(repShift.overallStatus, `${id} translate+permute failed: ${JSON.stringify(repShift.findings)}`).toBe("VALID");
    }
  });
});
