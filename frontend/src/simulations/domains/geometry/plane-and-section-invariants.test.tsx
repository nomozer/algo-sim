import * as THREE from "three";
import { describe, expect, it } from "vitest";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { chiaTamGiac } from "./polygon-triangulate";
import { veKhongGian } from "./scene3d-chart";
import {
  objectsAt,
  stepCount,
  toVec3,
  type ExactVec3,
  type Scene3D,
  type SceneObject,
  type Vec3,
} from "./scene3d-model";
import {
  auditSceneRepresentationConsistency,
  verifySceneMathematicalInvariants,
} from "./scene3d-representation-consistency";
import {
  buildPedagogicalConstructionPlan,
  describePlaneConceptualSeparation,
  registerExactSceneOrigin,
} from "./scene3d-semantic-policy";
import circumsphereFixture from "./scene3d-circumsphere-fixture.json";
import inscribedFixtures from "./scene3d-inscribed-circumscribed-fixtures.json";
import archetypeFixtures from "./scene3d-regression-archetypes-fixtures.json";
import sectionFixture from "./scene3d-section-fixture.json";
import { withSubEntities } from "./scene3d-subentities";

interface InventoryEntry {
  id: string;
  source: "catalog" | "fixture";
  scene: Scene3D;
}

function collectInventory(): InventoryEntry[] {
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

function sampleRaw(id: string): { title: string; description: string; scene: Scene3D } {
  const s = GEOMETRY_SAMPLES.find((x) => x.id === id);
  if (!s) throw new Error(`Missing catalog sample: ${id}`);
  return {
    title: s.envelope.title ?? s.id,
    description: s.envelope.description ?? s.problemText ?? s.id,
    scene: (s.envelope as unknown as { scene3d: Scene3D }).scene3d,
  };
}

function prepareDisplayScene(raw: Scene3D): Scene3D {
  const sub = withSubEntities(raw);
  registerExactSceneOrigin(sub, raw);
  const plan = buildPedagogicalConstructionPlan(sub);
  return registerExactSceneOrigin(veKhongGian(plan.scene), plan.scene);
}

function makeSceneObj(partial: Omit<SceneObject, "origin" | "producer"> & Partial<Pick<SceneObject, "origin" | "producer">>): SceneObject {
  return {
    origin: "derived",
    producer: "test",
    ...partial,
  };
}

function rotatePoint(p: Vec3, q: THREE.Quaternion): Vec3 {
  const v = new THREE.Vector3(p[0], p[1], p[2]).applyQuaternion(q);
  return [v.x, v.y, v.z];
}

function rotateSceneSO3(scene: Scene3D, q: THREE.Quaternion): Scene3D {
  const SCALE = 100_000_000;
  const toExactRat = (x: number): string => `${Math.round(x * SCALE)}/${SCALE}`;
  const rotExact = (p: ExactVec3): ExactVec3 => {
    const out = rotatePoint(toVec3(p), q);
    return [toExactRat(out[0]), toExactRat(out[1]), toExactRat(out[2])];
  };
  const rotatedObjects: SceneObject[] = scene.objects.map((o) => {
    const clone: SceneObject = { ...o };
    if (o.xyz) clone.xyz = rotExact(o.xyz);
    if (o.endpoints) clone.endpoints = [rotExact(o.endpoints[0]), rotExact(o.endpoints[1])];
    if (o.point_a) clone.point_a = rotExact(o.point_a);
    if (o.point_b) clone.point_b = rotExact(o.point_b);
    if (o.point) clone.point = rotExact(o.point);
    if (o.direction) clone.direction = rotExact(o.direction);
    if (o.normal) clone.normal = rotExact(o.normal);
    if (o.vertices) clone.vertices = o.vertices.map(rotExact);
    if (o.polygon) clone.polygon = o.polygon.map(rotExact);
    if (o.steps) {
      clone.steps = o.steps.map((st) => ({
        ...st,
        a: rotExact(st.a),
        b: rotExact(st.b),
      }));
    }
    if (o.anchor) clone.anchor = rotExact(o.anchor);
    if (o.apex_or_top) clone.apex_or_top = rotExact(o.apex_or_top);
    if (o.rim_point) clone.rim_point = rotExact(o.rim_point);
    if (o.center) clone.center = rotExact(o.center);
    if (o.major_dir) clone.major_dir = rotExact(o.major_dir);
    if (o.minor_dir) clone.minor_dir = rotExact(o.minor_dir);
    if (o.perpendicular_witness) {
      clone.perpendicular_witness = {
        ...o.perpendicular_witness,
        foot: rotExact(o.perpendicular_witness.foot),
        plane_directions: o.perpendicular_witness.plane_directions
          ? o.perpendicular_witness.plane_directions.map(rotExact)
          : undefined,
        marker: {
          ...o.perpendicular_witness.marker,
          u: rotExact(o.perpendicular_witness.marker.u),
          v: rotExact(o.perpendicular_witness.marker.v),
        },
      };
    }
    if (o.annotation?.witness) {
      const aw = o.annotation.witness;
      clone.annotation = {
        ...o.annotation,
        witness: {
          ...aw,
          foot: rotExact(aw.foot),
          from_point: aw.from_point ? rotExact(aw.from_point) : undefined,
          plane_directions: aw.plane_directions ? aw.plane_directions.map(rotExact) : undefined,
          marker: {
            ...aw.marker,
            u: rotExact(aw.marker.u),
            v: rotExact(aw.marker.v),
          },
          second: aw.second
            ? {
                ...aw.second,
                foot: rotExact(aw.second.foot),
                marker: {
                  ...aw.second.marker,
                  u: rotExact(aw.second.marker.u),
                  v: rotExact(aw.second.marker.v),
                },
              }
            : undefined,
        },
      };
    }
    return clone;
  });
  return {
    ...scene,
    objects: rotatedObjects,
  };
}

function triArea(a: Vec3, b: Vec3, c: Vec3): number {
  const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2];
  const vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
  return 0.5 * Math.hypot(uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx);
}


describe("Plane Conceptual Separation, Triangulation & Mathematical Invariants", () => {
  it("1. Plane Conceptual Separation: separates infinite mathematicalPlane, finite visualPatch, and realized sections", () => {
    const { scene: raw } = sampleRaw("chop-thiet-dien-ba-diem");
    const disp = prepareDisplayScene(raw);
    const lastStep = Math.max(0, stepCount(disp) - 1);
    const vis = objectsAt(disp, lastStep);
    const planeMnp = vis.find((o) => o.type === "plane3" && (o.id === "mp_MNP" || (o.label ?? "").includes("MNP")));
    expect(planeMnp).toBeDefined();

    const sep = describePlaneConceptualSeparation(disp, planeMnp!, vis, {
      completedPolySectionActive: true,
      auxiliaryShown: true,
      directlySelected: true,
    });
    expect(sep.planeId).toBe(planeMnp!.id);
    expect(sep.mathematicalPlane).not.toBeNull();
    expect(sep.mathematicalPlane!.isInfiniteAuthority).toBe(true);
    expect(Math.hypot(...sep.mathematicalPlane!.unitNormal)).toBeCloseTo(1, 5);
    expect(["MINIMAL_GEOMETRY", "COMPACT_PLANE_PATCH", "CONTROLLED_EXTENDED_PATCH"]).toContain(
      sep.visualPatch.mode,
    );
    expect(sep.sections.length).toBeGreaterThanOrEqual(1);
    for (const sec of sep.sections) {
      expect(sec.vertexCount).toBeGreaterThanOrEqual(3);
      expect(sec.onInfinitePlane).toBe(true);
    }
  });

  it("2. polygon-triangulate handles anisotropic extreme aspect ratios, micro/macro scales, concave notch, and collinear/duplicate degeneracy", () => {
    // Extreme 1000 x 0.01 rectangle
    const rectWide: Vec3[] = [
      [0, 0, 0],
      [1000, 0, 0],
      [1000, 0.01, 0],
      [0, 0.01, 0],
    ];
    const trisWide = chiaTamGiac(rectWide);
    expect(trisWide).toHaveLength(2);
    const areaWide = trisWide.reduce((s, [a, b, c]) => s + triArea(rectWide[a], rectWide[b], rectWide[c]), 0);
    expect(areaWide).toBeCloseTo(10, 4);

    // Micro scale 1e-5
    const sMicro = 1e-5;
    const microQuad: Vec3[] = [
      [0, 0, 0],
      [sMicro, 0, 0],
      [sMicro, sMicro, 0],
      [0, sMicro, 0],
    ];
    expect(chiaTamGiac(microQuad)).toHaveLength(2);

    // Macro scale 1e5
    const sMacro = 1e5;
    const macroQuad: Vec3[] = [
      [0, 0, 0],
      [sMacro, 0, sMacro * 0.25],
      [sMacro, sMacro, sMacro * 0.25],
      [0, sMacro, 0],
    ];
    expect(chiaTamGiac(macroQuad)).toHaveLength(2);

    // Concave notch chevron — exact notch area = 8
    const concave: Vec3[] = [
      [0, 0, 0],
      [4, 0, 0],
      [4, 3, 0],
      [2, 1, 0],
      [0, 3, 0],
    ];
    const trisConcave = chiaTamGiac(concave);
    expect(trisConcave).toHaveLength(3);
    const areaConcave = trisConcave.reduce((s, [a, b, c]) => s + triArea(concave[a], concave[b], concave[c]), 0);
    expect(areaConcave).toBeCloseTo(8, 5);

    // Strict 3-point collinearity must return [] (no thin sliver triangles)
    expect(chiaTamGiac([[0, 0, 0], [5, 0, 0], [10, 0, 0]])).toEqual([]);
    // Degenerate duplicate points
    expect(chiaTamGiac([[1, 1, 1], [1, 1, 1], [2, 1, 1]])).toEqual([]);
  });

  it("3. verifySceneMathematicalInvariants passes across all 22 catalog samples and 6 fixture scenes (28 total)", () => {
    const inventory = collectInventory();
    expect(inventory).toHaveLength(28);
    const failures: string[] = [];

    for (const entry of inventory) {
      const disp = prepareDisplayScene(entry.scene);
      const lastStep = Math.max(0, stepCount(disp) - 1);
      const rep = verifySceneMathematicalInvariants(disp, { step: lastStep });
      if (!rep.isValid || rep.overallStatus !== "VALID") {
        const msgs = rep.findings.map((f) => `${f.check}:${f.message}`).join("; ");
        failures.push(`${entry.id} -> ${rep.overallStatus} (${msgs})`);
      }
    }
    expect(failures).toEqual([]);
  });

  it("4. verifySceneMathematicalInvariants rejects synthetic violations in all mathematical invariant categories", () => {
    // 4a. point_on_line violation
    const badPointOnLine: Scene3D = {
      events: [],
      free_objects: [],
      objects: [
        makeSceneObj({ id: "A", type: "point3", render: "point_marker", label: "A", xyz: ["0", "0", "0"], origin: "free", depends: [] }),
        makeSceneObj({ id: "B", type: "point3", render: "point_marker", label: "B", xyz: ["4", "0", "0"], origin: "free", depends: [] }),
        makeSceneObj({
          id: "AB",
          type: "segment3",
          render: "segment",
          label: "AB",
          endpoints: [["0", "0", "0"], ["4", "0", "0"]],
          endpoint_ids: ["A", "B"],
          depends: ["A", "B"],
        }),
        makeSceneObj({
          id: "M",
          type: "point3",
          render: "point_marker",
          label: "M",
          producer: "construct_point.intersect",
          xyz: ["2", "2", "0"],
          depends: ["AB"],
          source: { assumption: "M ∈ AB" },
        }),
      ],
    };
    const repLine = verifySceneMathematicalInvariants(badPointOnLine);
    expect(repLine.isValid).toBe(false);
    expect(repLine.categories.point_on_line.invalidCount).toBeGreaterThan(0);

    // 4b. point_on_plane violation
    const badPointOnPlane: Scene3D = {
      events: [],
      free_objects: [],
      objects: [
        makeSceneObj({ id: "A", type: "point3", render: "point_marker", label: "A", xyz: ["0", "0", "0"], origin: "free", depends: [] }),
        makeSceneObj({ id: "B", type: "point3", render: "point_marker", label: "B", xyz: ["4", "0", "0"], origin: "free", depends: [] }),
        makeSceneObj({ id: "C", type: "point3", render: "point_marker", label: "C", xyz: ["0", "4", "0"], origin: "free", depends: [] }),
        makeSceneObj({
          id: "P",
          type: "plane3",
          render: "surface",
          label: "(ABC)",
          point: ["0", "0", "0"],
          normal: ["0", "0", "1"],
          depends: ["A", "B", "C"],
        }),
        makeSceneObj({
          id: "Q",
          type: "point3",
          render: "point_marker",
          label: "Q",
          producer: "construct_point.project",
          xyz: ["1", "1", "3"],
          depends: ["P"],
        }),
      ],
    };
    const repPlane = verifySceneMathematicalInvariants(badPointOnPlane);
    expect(repPlane.isValid).toBe(false);
    expect(repPlane.categories.point_on_plane.invalidCount).toBeGreaterThan(0);

    // 4c. line_plane_intersection violation
    const badLinePlaneInt: Scene3D = {
      events: [],
      free_objects: [],
      objects: [
        makeSceneObj({
          id: "P",
          type: "plane3",
          render: "surface",
          label: "(P)",
          point: ["0", "0", "0"],
          normal: ["0", "0", "1"],
          depends: [],
        }),
        makeSceneObj({
          id: "d",
          type: "line3",
          render: "line",
          label: "d",
          point: ["1", "1", "0"],
          direction: ["0", "0", "1"],
          depends: [],
        }),
        makeSceneObj({
          id: "I",
          type: "point3",
          render: "point_marker",
          label: "I",
          xyz: ["1", "1", "2"],
          depends: ["d", "P"],
        }),
      ],
    };
    const repLpi = verifySceneMathematicalInvariants(badLinePlaneInt);
    expect(repLpi.isValid).toBe(false);
    expect(repLpi.categories.line_plane_intersection.invalidCount).toBeGreaterThan(0);

    // 4c2. plane_plane_intersection violation
    const badPlanePlaneInt: Scene3D = {
      events: [],
      free_objects: [],
      objects: [
        makeSceneObj({
          id: "P1",
          type: "plane3",
          render: "surface",
          label: "(P1)",
          point: ["0", "0", "0"],
          normal: ["0", "0", "1"],
          depends: [],
        }),
        makeSceneObj({
          id: "P2",
          type: "plane3",
          render: "surface",
          label: "(P2)",
          point: ["0", "0", "0"],
          normal: ["0", "1", "0"],
          depends: [],
        }),
        makeSceneObj({
          id: "gt",
          type: "line3",
          render: "line",
          label: "giao tuyến",
          point: ["0", "1", "1"],
          direction: ["1", "0", "0"],
          depends: ["P1", "P2"],
        }),
      ],
    };
    const repPpi = verifySceneMathematicalInvariants(badPlanePlaneInt);
    expect(repPpi.isValid).toBe(false);
    expect(repPpi.categories.plane_plane_intersection.invalidCount).toBeGreaterThan(0);

    // 4d. section_polygon self-intersecting bowtie / off-plane violation
    const badSection: Scene3D = {
      events: [],
      free_objects: [],
      objects: [
        makeSceneObj({
          id: "P",
          type: "plane3",
          render: "surface",
          label: "(P)",
          point: ["0", "0", "0"],
          normal: ["0", "0", "1"],
          depends: [],
        }),
        makeSceneObj({
          id: "sec",
          type: "section",
          render: "polygon",
          label: "Thiết diện MNPQ",
          polygon: [
            ["0", "0", "0"],
            ["3", "3", "0"],
            ["3", "0", "0"],
            ["0", "3", "0"],
          ],
          depends: ["P"],
        }),
      ],
    };
    const repSec = verifySceneMathematicalInvariants(badSection);
    expect(repSec.isValid).toBe(false);
    expect(repSec.categories.section_polygon.invalidCount).toBeGreaterThan(0);

    // 4e. tangency violation (sphere distance != R)
    const badTangency: Scene3D = {
      events: [],
      free_objects: [],
      objects: [
        makeSceneObj({
          id: "O",
          type: "point3",
          render: "point_marker",
          label: "O",
          xyz: ["0", "0", "0"],
          origin: "free",
          depends: [],
        }),
        makeSceneObj({
          id: "S",
          type: "curved_solid",
          curved_kind: "ball",
          render: "curved_solid",
          label: "Mặt cầu (O; 3)",
          anchor: ["0", "0", "0"],
          radius_sq: "9",
          depends: ["O"],
        }),
        makeSceneObj({
          id: "P",
          type: "plane3",
          render: "surface",
          label: "(P)",
          point: ["0", "0", "5"],
          normal: ["0", "0", "1"],
          depends: ["S"],
        }),
      ],
    };
    const repTan = verifySceneMathematicalInvariants(badTangency);
    expect(repTan.isValid).toBe(false);
    expect(repTan.categories.tangency.invalidCount).toBeGreaterThan(0);

    // 4f. curved_intersections violation (secant circle r^2 + d^2 != R^2)
    const badSecant: Scene3D = {
      events: [],
      free_objects: [],
      objects: [
        makeSceneObj({
          id: "S",
          type: "curved_solid",
          curved_kind: "ball",
          render: "curved_solid",
          label: "Mặt cầu",
          anchor: ["0", "0", "0"],
          radius_sq: "25",
          depends: [],
        }),
        makeSceneObj({
          id: "P",
          type: "plane3",
          render: "surface",
          label: "(P)",
          point: ["0", "0", "3"],
          normal: ["0", "0", "1"],
          depends: [],
        }),
        makeSceneObj({
          id: "C",
          type: "circle3",
          render: "circle",
          label: "Đường tròn giao tuyến",
          center: ["0", "0", "3"],
          normal: ["0", "0", "1"],
          radius_sq: "4", // should be 25 - 9 = 16
          depends: ["S", "P"],
        }),
      ],
    };
    const repCurved = verifySceneMathematicalInvariants(badSecant);
    expect(repCurved.isValid).toBe(false);
    expect(repCurved.categories.curved_intersections.invalidCount).toBeGreaterThan(0);
  });

  it("5. View-invariance under SO(3) 3D rotations preserves verifySceneMathematicalInvariants & auditSceneRepresentationConsistency", () => {
    const eulerQuats = [
      new THREE.Quaternion().setFromEuler(new THREE.Euler(0.45, -0.72, 1.15)),
      new THREE.Quaternion().setFromEuler(new THREE.Euler(-1.1, 0.85, -0.35)),
    ];
    for (const id of ["chop-thiet-dien-ba-diem", "mat-cau-cat-mat-phang", "oxyz-giao-diem-duong-mat"]) {
      const { scene: raw } = sampleRaw(id);
      const disp = prepareDisplayScene(raw);
      const lastStep = Math.max(0, stepCount(disp) - 1);
      for (const q of eulerQuats) {
        const rotated = rotateSceneSO3(disp, q);
        const inv = verifySceneMathematicalInvariants(rotated, { step: lastStep });
        const cons = auditSceneRepresentationConsistency(rotated, { step: lastStep });
        expect(inv.findings, `${id}: ${JSON.stringify(inv.findings)}`).toEqual([]);
        expect(inv.isValid).toBe(true);
        expect(cons.overallStatus).toBe("VALID");
      }
    }
  });
});
