/**
 * PHASE 7 — FRONTEND REPRESENTATION CONSISTENCY VERIFICATION
 *
 * Verifies geometric consistency of the rendered / presentation representation
 * WITHOUT mutating Backend coordinates and WITHOUT replacing Backend's exact
 * Kernel validator.
 *
 * All tolerances scale with the scene bounding diameter and numerical conditioning
 * rather than using an arbitrary fixed absolute epsilon.
 * Insufficient geometric data resolves cleanly to `UNDETERMINED`.
 */
import { chiaTamGiac, dienTichCoDau } from "./polygon-triangulate";
import { veKhongGian } from "./scene3d-chart";
import {
  clampStep,
  diemHuuHan,
  duongKinhCanh,
  objectsAt,
  toNumber,
  toVec3,
  type ExactVec3,
  type Scene3D,
  type SceneObject,
  type Vec3,
} from "./scene3d-model";
import {
  compactPlaneAnchorPoints,
  computeBoundedStudiedPlanePolygon,
} from "./scene3d-semantic-policy";

export type ConsistencyCheckKind =
  | "point_on_plane"
  | "point_on_line"
  | "intersection_consistency"
  | "section_connectivity"
  | "mesh_consistency";

export type ConsistencyStatus = "VALID" | "INVALID" | "UNDETERMINED";

export interface ConsistencyFinding {
  check: ConsistencyCheckKind;
  status: ConsistencyStatus;
  objectIds: string[];
  message: string;
  measuredError?: number;
  tolerance?: number;
}

export interface ConsistencyCheckSummary {
  check: ConsistencyCheckKind;
  status: ConsistencyStatus;
  checkedCount: number;
  validCount: number;
  invalidCount: number;
  undeterminedCount: number;
  maxNormalizedError: number;
  findings: ConsistencyFinding[];
}

export interface SceneConsistencyReport {
  overallStatus: ConsistencyStatus;
  stepIndex: number | null;
  sceneScale: number;
  tolerances: {
    distance: number;
    direction: number;
    area: number;
  };
  checks: Record<ConsistencyCheckKind, ConsistencyCheckSummary>;
  findings: ConsistencyFinding[];
  isConsistent: boolean;
}

export interface AuditRepresentationOptions {
  step?: number;
  bypassCache?: boolean;
}

const CHECK_KINDS: readonly ConsistencyCheckKind[] = [
  "point_on_plane",
  "point_on_line",
  "intersection_consistency",
  "section_connectivity",
  "mesh_consistency",
];

const REPORT_CACHE = new WeakMap<object, Map<string, SceneConsistencyReport>>();

function safeToVec3(v?: ExactVec3 | null): Vec3 | null {
  if (!v || v.length !== 3) return null;
  try {
    const out = toVec3(v);
    return Number.isFinite(out[0]) && Number.isFinite(out[1]) && Number.isFinite(out[2]) ? out : null;
  } catch {
    return null;
  }
}

function sub3(a: Vec3, b: Vec3): Vec3 {
  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
}

function dot3(a: Vec3, b: Vec3): number {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

function cross3(a: Vec3, b: Vec3): Vec3 {
  return [
    a[1] * b[2] - a[2] * b[1],
    a[2] * b[0] - a[0] * b[2],
    a[0] * b[1] - a[1] * b[0],
  ];
}

function len3(v: Vec3): number {
  return Math.hypot(v[0], v[1], v[2]);
}

function unit3(v: Vec3, minNorm = 1e-12): Vec3 | null {
  const l = len3(v);
  if (!Number.isFinite(l) || l <= minNorm) return null;
  return [v[0] / l, v[1] / l, v[2] / l];
}

function dist3(a: Vec3, b: Vec3): number {
  return len3(sub3(a, b));
}

function distPointPlane(p: Vec3, planePoint: Vec3, unitNormal: Vec3): number {
  return Math.abs(dot3(sub3(p, planePoint), unitNormal));
}

function pointLineProjection(
  p: Vec3,
  lineOrigin: Vec3,
  unitDir: Vec3,
): { dist: number; along: number } {
  const d = sub3(p, lineOrigin);
  const along = dot3(d, unitDir);
  const perp = cross3(d, unitDir);
  return { dist: len3(perp), along };
}

function planeBasisFromNormal(unitN: Vec3): [Vec3, Vec3] {
  const seed: Vec3 = Math.abs(unitN[0]) < 0.85 ? [1, 0, 0] : [0, 1, 0];
  const u = unit3(cross3(unitN, seed)) ?? [0, 1, 0];
  const v = cross3(unitN, u);
  return [u, v];
}

function bestFitPlaneFromPoints(
  pts: readonly Vec3[],
): { origin: Vec3; unitNormal: Vec3; maxCross: number } | null {
  if (pts.length < 3) return null;
  let bestCross: Vec3 | null = null;
  let bestOrigin = pts[0];
  let bestNorm = 0;
  for (let i = 0; i < pts.length; i += 1) {
    for (let j = i + 1; j < pts.length; j += 1) {
      const ab = sub3(pts[j], pts[i]);
      if (len3(ab) <= 1e-12) continue;
      for (let k = j + 1; k < pts.length; k += 1) {
        const ac = sub3(pts[k], pts[i]);
        const cr = cross3(ab, ac);
        const n = len3(cr);
        if (n > bestNorm) {
          bestNorm = n;
          bestCross = cr;
          bestOrigin = pts[i];
        }
      }
    }
  }
  if (!bestCross || bestNorm <= 1e-12) return null;
  const u = unit3(bestCross);
  if (!u) return null;
  return { origin: bestOrigin, unitNormal: u, maxCross: bestNorm };
}

function collectAllFinitePoints(objs: readonly SceneObject[]): Vec3[] {
  const pts: Vec3[] = [...diemHuuHan([...objs])];
  for (const o of objs) {
    for (const candidate of [o.xyz, o.point, o.point_a, o.point_b, o.center, o.anchor, o.apex_or_top, o.rim_point]) {
      const v = safeToVec3(candidate);
      if (v) pts.push(v);
    }
    for (const list of [o.endpoints, o.vertices, o.polygon]) {
      for (const item of list ?? []) {
        const v = safeToVec3(item);
        if (v) pts.push(v);
      }
    }
    for (const s of o.steps ?? []) {
      const va = safeToVec3(s.a);
      const vb = safeToVec3(s.b);
      if (va) pts.push(va);
      if (vb) pts.push(vb);
    }
  }
  return pts;
}

function segmentsProperlyIntersect2D(
  a1: readonly [number, number],
  a2: readonly [number, number],
  b1: readonly [number, number],
  b2: readonly [number, number],
  eps: number,
): boolean {
  const orient = (p: readonly [number, number], q: readonly [number, number], r: readonly [number, number]) =>
    (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]);
  const d1 = orient(b1, b2, a1);
  const d2 = orient(b1, b2, a2);
  const d3 = orient(a1, a2, b1);
  const d4 = orient(a1, a2, b2);
  const scaleA = Math.hypot(a2[0] - a1[0], a2[1] - a1[1]);
  const scaleB = Math.hypot(b2[0] - b1[0], b2[1] - b1[1]);
  const areaEps = eps * Math.max(scaleA, scaleB, eps);
  return ((d1 > areaEps && d2 < -areaEps) || (d1 < -areaEps && d2 > areaEps))
    && ((d3 > areaEps && d4 < -areaEps) || (d3 < -areaEps && d4 > areaEps));
}

function emptySummaries(): Record<ConsistencyCheckKind, ConsistencyCheckSummary> {
  const out = {} as Record<ConsistencyCheckKind, ConsistencyCheckSummary>;
  for (const kind of CHECK_KINDS) {
    out[kind] = {
      check: kind,
      status: "VALID",
      checkedCount: 0,
      validCount: 0,
      invalidCount: 0,
      undeterminedCount: 0,
      maxNormalizedError: 0,
      findings: [],
    };
  }
  return out;
}

function computeCacheKey(step: number | undefined): string {
  return step === undefined ? "FINAL" : `STEP:${Math.trunc(step)}`;
}

/**
 * Runs Phase 7 scale-aware geometric representation checks on a `Scene3D`.
 * Does NOT modify `rawScene` coordinates. Intended for verification & offline/inspection audits,
 * never inside per-frame animation loops or hover handlers.
 */
export function auditSceneRepresentationConsistency(
  rawScene: Scene3D,
  options: AuditRepresentationOptions = {},
): SceneConsistencyReport {
  const cacheKey = computeCacheKey(options.step);
  if (!options.bypassCache && rawScene && typeof rawScene === "object") {
    const existing = REPORT_CACHE.get(rawScene)?.get(cacheKey);
    if (existing) return existing;
  }

  const summaries = emptySummaries();
  const findings: ConsistencyFinding[] = [];
  const record = (
    check: ConsistencyCheckKind,
    status: ConsistencyStatus,
    objectIds: string[],
    message: string,
    measuredError?: number,
    tolerance?: number,
  ) => {
    const s = summaries[check];
    s.checkedCount += 1;
    if (status === "VALID") s.validCount += 1;
    else if (status === "INVALID") s.invalidCount += 1;
    else s.undeterminedCount += 1;

    if (
      measuredError !== undefined
      && tolerance !== undefined
      && Number.isFinite(measuredError)
      && tolerance > 0
    ) {
      s.maxNormalizedError = Math.max(s.maxNormalizedError, measuredError / tolerance);
    }
    if (status !== "VALID") {
      const f: ConsistencyFinding = { check, status, objectIds, message, measuredError, tolerance };
      s.findings.push(f);
      findings.push(f);
    }
  };

  let scene: Scene3D;
  try {
    scene = veKhongGian(rawScene);
  } catch (err) {
    record(
      "mesh_consistency",
      "INVALID",
      [],
      `Invalid chart_metric: ${err instanceof Error ? err.message : String(err)}`,
    );
    summaries.mesh_consistency.status = "INVALID";
    return {
      overallStatus: "INVALID",
      stepIndex: options.step ?? null,
      sceneScale: 0,
      tolerances: { distance: 0, direction: 1e-4, area: 0 },
      checks: summaries,
      findings,
      isConsistent: false,
    };
  }

  const resolvedStep = options.step !== undefined ? clampStep(scene, options.step) : null;
  const visibleObjects = resolvedStep !== null ? objectsAt(scene, resolvedStep) : [...scene.objects];
  const allObjects = scene.objects;
  const byId = new Map<string, SceneObject>();
  for (const o of visibleObjects) byId.set(o.id, o);
  const allById = new Map<string, SceneObject>();
  for (const o of allObjects) allById.set(o.id, o);

  const finitePts = collectAllFinitePoints(visibleObjects.length > 0 ? visibleObjects : allObjects);
  const rawScale = duongKinhCanh(finitePts);
  const sceneScale = Number.isFinite(rawScale) && rawScale > 1e-9 ? rawScale : 0;

  if (visibleObjects.length === 0 || sceneScale === 0) {
    record(
      "mesh_consistency",
      "UNDETERMINED",
      visibleObjects.map((o) => o.id),
      "Insufficient finite geometric coordinates to verify representation.",
    );
    summaries.mesh_consistency.status = "UNDETERMINED";
    return {
      overallStatus: "UNDETERMINED",
      stepIndex: resolvedStep,
      sceneScale,
      tolerances: { distance: 0, direction: 1e-4, area: 0 },
      checks: summaries,
      findings,
      isConsistent: false,
    };
  }

  const distTol = Math.max(1e-4 * sceneScale, 1e-7);
  const dirTol = 1e-4;
  const areaTol = 1e-7 * sceneScale * sceneScale;
  const minEdgeLen = 1e-5 * sceneScale;

  const getPlaneData = (
    o: SceneObject,
  ): { point: Vec3; normal: Vec3 } | null => {
    const pt = safeToVec3(o.point);
    const nRaw = safeToVec3(o.normal);
    const n = nRaw ? unit3(nRaw, 1e-12) : null;
    if (!pt || !n) return null;
    return { point: pt, normal: n };
  };

  const getLineData = (
    o: SceneObject,
  ): { origin: Vec3; dir: Vec3; end?: Vec3; bounded: boolean } | null => {
    if (o.render === "line") {
      const p = safeToVec3(o.point);
      const dRaw = safeToVec3(o.direction);
      const d = dRaw ? unit3(dRaw, 1e-12) : null;
      if (!p || !d) return null;
      return { origin: p, dir: d, bounded: false };
    }
    const pa = safeToVec3(o.endpoints?.[0] ?? o.point_a);
    const pb = safeToVec3(o.endpoints?.[1] ?? o.point_b);
    if (!pa || !pb) return null;
    const d = unit3(sub3(pb, pa), 1e-12);
    if (!d) return null;
    return { origin: pa, dir: d, end: pb, bounded: true };
  };

  // Precompute solids available in visible step (fallback to scene solids if referenced)
  const visibleSolids = visibleObjects.filter(
    (o) => o.type === "solid" && Array.isArray(o.vertices) && Array.isArray(o.faces),
  );

  // 1. POINT ON PLANE & BOUNDED PLANE POLYGON CONSISTENCY
  for (const o of visibleObjects) {
    // Witness foot -> plane
    for (const w of [o.perpendicular_witness, o.annotation?.witness, o.annotation?.witness?.second]) {
      if (!w?.on || !w.foot) continue;
      const target = byId.get(w.on) ?? allById.get(w.on);
      if (!target) continue;
      const foot = safeToVec3(w.foot);
      if (!foot) {
        record("point_on_plane", "UNDETERMINED", [o.id, target.id], `Witness foot coordinate invalid or missing.`);
        continue;
      }
      if (target.render === "surface") {
        const pl = getPlaneData(target);
        if (!pl) {
          record("point_on_plane", "UNDETERMINED", [o.id, target.id], `Plane "${target.id}" missing anchor or normal.`);
        } else {
          const err = distPointPlane(foot, pl.point, pl.normal);
          record(
            "point_on_plane",
            err <= distTol ? "VALID" : "INVALID",
            [o.id, target.id],
            err <= distTol
              ? `Witness foot lies on plane "${target.id}".`
              : `Witness foot is off plane "${target.id}" by ${err.toExponential(3)} (tol ${distTol.toExponential(3)}).`,
            err,
            distTol,
          );
        }
      } else {
        const targetVerts = target.polygon ?? target.vertices;
        if (target.render === "polygon" && Array.isArray(targetVerts) && targetVerts.length >= 3) {
          const polyPts = targetVerts.map(safeToVec3);
          const fit = polyPts.every((v): v is Vec3 => v !== null)
            ? bestFitPlaneFromPoints(polyPts as Vec3[])
            : null;
          if (!fit) {
            record("point_on_plane", "UNDETERMINED", [o.id, target.id], `Target polygon "${target.id}" lacks coplanar span.`);
          } else {
            const err = distPointPlane(foot, fit.origin, fit.unitNormal);
            record(
              "point_on_plane",
              err <= distTol ? "VALID" : "INVALID",
              [o.id, target.id],
              err <= distTol
                ? `Witness foot lies on polygon plane "${target.id}".`
                : `Witness foot is off polygon plane "${target.id}" by ${err.toExponential(3)} (tol ${distTol.toExponential(3)}).`,
              err,
              distTol,
            );
          }
        }
      }
    }

    // Polygon / Section coplanarity + plane surface patch containment
    if (o.render === "surface") {
      const pl = getPlaneData(o);
      if (!pl) {
        record("point_on_plane", "UNDETERMINED", [o.id], `Surface "${o.id}" lacks valid point or normal.`);
        continue;
      }
      const bounded = computeBoundedStudiedPlanePolygon(scene, o, visibleObjects);

      if (bounded.length > 0 && bounded.length < 3) {
        record(
          "mesh_consistency",
          "INVALID",
          [o.id],
          `Bounded plane polygon for "${o.id}" has fewer than 3 vertices (${bounded.length}).`,
        );
      } else if (bounded.length === 0) {
        const compact = compactPlaneAnchorPoints(scene, o, visibleObjects);
        if (compact.length >= 3) {
          let maxOffCompact = 0;
          for (const v of compact) {
            maxOffCompact = Math.max(maxOffCompact, distPointPlane(v, pl.point, pl.normal));
          }
          record(
            "point_on_plane",
            maxOffCompact <= distTol ? "VALID" : "INVALID",
            [o.id],
            maxOffCompact <= distTol
              ? `Compact plane patch vertices lie on "${o.id}".`
              : `Compact plane patch vertex deviates from "${o.id}" by ${maxOffCompact.toExponential(3)}.`,
            maxOffCompact,
            distTol,
          );
        }
      } else if (bounded.length >= 3) {
        let maxOffPlane = 0;
        for (const v of bounded) {
          maxOffPlane = Math.max(maxOffPlane, distPointPlane(v, pl.point, pl.normal));
        }
        record(
          "point_on_plane",
          maxOffPlane <= distTol ? "VALID" : "INVALID",
          [o.id],
          maxOffPlane <= distTol
            ? `Bounded plane polygon vertices lie on "${o.id}".`
            : `Bounded plane polygon vertex deviates from "${o.id}" by ${maxOffPlane.toExponential(3)}.`,
          maxOffPlane,
          distTol,
        );

        try {
          const tris = chiaTamGiac(bounded);
          record(
            "mesh_consistency",
            tris.length >= bounded.length - 2 ? "VALID" : "INVALID",
            [o.id],
            tris.length >= bounded.length - 2
              ? `Bounded plane triangulation valid (${tris.length} tris).`
              : `Bounded plane triangulation collapsed (${tris.length} tris for ${bounded.length} verts).`,
          );
        } catch (err) {
          record(
            "mesh_consistency",
            "INVALID",
            [o.id],
            `Bounded plane triangulation threw: ${err instanceof Error ? err.message : String(err)}`,
          );
        }
      }
    }
  }

  // Derived point3 (intersect / project / foot) incidence on dependent planes and lines
  for (const o of visibleObjects) {
    if (o.type !== "point3" || o.origin !== "derived" || !o.xyz) continue;
    const pVec = safeToVec3(o.xyz);
    if (!pVec) continue;
    const prod = (o.producer ?? "").toLowerCase();
    const isIntersect = prod.includes("intersect") || prod.includes("giao");
    const isProjectOrFoot =
      prod.includes("project")
      || prod.includes("foot")
      || prod.includes("hinh_chieu")
      || prod.includes("chan_");
    if (!isIntersect && !isProjectOrFoot) continue;

    const depObjs = (o.depends ?? [])
      .map((id) => byId.get(id) ?? allById.get(id))
      .filter((d): d is SceneObject => Boolean(d));
    const hasPlaneDep = depObjs.some((d) => d.type === "plane3");
    const isParallelProd = prod.includes("parallel") || prod.includes("distance");

    for (const dep of depObjs) {
      if (dep.type === "plane3") {
        const pl = getPlaneData(dep);
        if (!pl) {
          record("point_on_plane", "UNDETERMINED", [o.id, dep.id], `Dependent plane "${dep.id}" incomplete.`);
        } else {
          const err = distPointPlane(pVec, pl.point, pl.normal);
          record(
            "point_on_plane",
            err <= distTol ? "VALID" : "INVALID",
            [o.id, dep.id],
            err <= distTol
              ? `Derived point "${o.id}" lies on dependent plane "${dep.id}".`
              : `Derived point "${o.id}" (${o.producer ?? ""}) deviates from plane "${dep.id}" by ${err.toExponential(3)} (tol ${distTol.toExponential(3)}).`,
            err,
            distTol,
          );
        }
      } else if (
        (dep.type === "line3" || dep.type === "segment3" || dep.type === "edge")
        && !isParallelProd
        && (isIntersect || !hasPlaneDep)
      ) {
        const ld = getLineData(dep);
        if (!ld) {
          record("point_on_line", "UNDETERMINED", [o.id, dep.id], `Dependent line "${dep.id}" incomplete.`);
        } else {
          const { dist: err } = pointLineProjection(pVec, ld.origin, ld.dir);
          record(
            "point_on_line",
            err <= distTol ? "VALID" : "INVALID",
            [o.id, dep.id],
            err <= distTol
              ? `Derived point "${o.id}" lies on dependent line "${dep.id}".`
              : `Derived point "${o.id}" (${o.producer ?? ""}) misses line "${dep.id}" by ${err.toExponential(3)} (tol ${distTol.toExponential(3)}).`,
            err,
            distTol,
          );
        }
      }
    }
  }

  // 2. POINT ON LINE / SEGMENT & EDGE SPAN
  for (const o of visibleObjects) {
    // Witness foot -> line or segment
    for (const w of [o.perpendicular_witness, o.annotation?.witness, o.annotation?.witness?.second]) {
      if (!w?.on || !w.foot) continue;
      const target = byId.get(w.on) ?? allById.get(w.on);
      if (!target || (target.render !== "line" && target.render !== "segment")) continue;
      const foot = safeToVec3(w.foot);
      const ln = getLineData(target);
      if (!foot || !ln) {
        record("point_on_line", "UNDETERMINED", [o.id, target.id], `Line witness target lacks valid endpoints/direction.`);
        continue;
      }
      const { dist } = pointLineProjection(foot, ln.origin, ln.dir);
      record(
        "point_on_line",
        dist <= distTol ? "VALID" : "INVALID",
        [o.id, target.id],
        dist <= distTol
          ? `Witness foot lies on supporting line of "${target.id}".`
          : `Witness foot misses line "${target.id}" by ${dist.toExponential(3)}.`,
        dist,
        distTol,
      );
    }

    // Segment endpoints matching endpoint_ids
    if (o.render === "segment") {
      const pa = safeToVec3(o.endpoints?.[0] ?? o.point_a);
      const pb = safeToVec3(o.endpoints?.[1] ?? o.point_b);
      if (!pa || !pb) {
        record("point_on_line", "UNDETERMINED", [o.id], `Segment "${o.id}" lacks finite endpoints.`);
      } else {
        const segLen = dist3(pa, pb);
        if (segLen <= minEdgeLen && o.endpoint_ids?.[0] !== o.endpoint_ids?.[1]) {
          record(
            "point_on_line",
            "INVALID",
            [o.id],
            `Segment "${o.id}" has degenerate zero length (${segLen.toExponential(3)}).`,
            minEdgeLen,
            minEdgeLen,
          );
        } else {
          let maxEndErr = 0;
          if (o.endpoint_ids && o.endpoint_ids.length >= 2) {
            const p0Obj = allById.get(o.endpoint_ids[0]);
            const p1Obj = allById.get(o.endpoint_ids[1]);
            const p0Vec = safeToVec3(p0Obj?.xyz);
            const p1Vec = safeToVec3(p1Obj?.xyz);
            if (p0Vec && p1Vec) {
              const directErr = Math.max(dist3(pa, p0Vec), dist3(pb, p1Vec));
              const swappedErr = Math.max(dist3(pa, p1Vec), dist3(pb, p0Vec));
              maxEndErr = Math.min(directErr, swappedErr);
            }
          }
          record(
            "point_on_line",
            maxEndErr <= distTol ? "VALID" : "INVALID",
            [o.id],
            maxEndErr <= distTol
              ? `Segment "${o.id}" endpoints match referenced vertices.`
              : `Segment "${o.id}" deviates from endpoint_ids by ${maxEndErr.toExponential(3)}.`,
            maxEndErr,
            distTol,
          );
        }
      }
    }

    if (o.edge_span) {
      const { t0, t1 } = o.edge_span;
      const inDomain =
        Number.isFinite(t0)
        && Number.isFinite(t1)
        && t0 >= -1e-4
        && t1 <= 1 + 1e-4
        && t0 <= t1 + 1e-4;
      record(
        "point_on_line",
        inDomain ? "VALID" : "INVALID",
        [o.id],
        inDomain
          ? `Edge span [${t0}, ${t1}] on "${o.id}" within [0, 1].`
          : `Edge span [${t0}, ${t1}] on "${o.id}" out of [0, 1] domain.`,
      );
    }
  }

  // 3. INTERSECTION CONSISTENCY & 4. SECTION CONNECTIVITY & 5. MESH CONSISTENCY
  for (const o of visibleObjects) {
    // Line built from 2 planes -> must satisfy both planes and be orthogonal to both normals
    if (o.render === "line") {
      const ln = getLineData(o);
      const planeDeps = o.depends
        .map((id) => allById.get(id))
        .filter((d): d is SceneObject => Boolean(d && d.render === "surface"));
      if (ln && planeDeps.length >= 2) {
        const plA = getPlaneData(planeDeps[0]);
        const plB = getPlaneData(planeDeps[1]);
        if (!plA || !plB) {
          record("intersection_consistency", "UNDETERMINED", [o.id], `Intersection line "${o.id}" parent plane incomplete.`);
        } else if (len3(cross3(plA.normal, plB.normal)) > dirTol) {
          const distErr = Math.max(
            distPointPlane(ln.origin, plA.point, plA.normal),
            distPointPlane(ln.origin, plB.point, plB.normal),
          );
          const orthoErr = Math.max(
            Math.abs(dot3(ln.dir, plA.normal)),
            Math.abs(dot3(ln.dir, plB.normal)),
          );
          const ok = distErr <= distTol && orthoErr <= dirTol;
          record(
            "intersection_consistency",
            ok ? "VALID" : "INVALID",
            [o.id, planeDeps[0].id, planeDeps[1].id],
            ok
              ? `Line "${o.id}" matches intersection of planes "${planeDeps[0].id}" and "${planeDeps[1].id}".`
              : `Line "${o.id}" inconsistent with plane intersection (dist=${distErr.toExponential(3)}, dot=${orthoErr.toExponential(3)}).`,
            Math.max(distErr, orthoErr * sceneScale),
            distTol,
          );
        }
      }
    }

    // Circle lying on a plane or slicing a sphere
    if (o.render === "circle") {
      const center = safeToVec3(o.center);
      const normalRaw = safeToVec3(o.normal);
      const normal = normalRaw ? unit3(normalRaw, 1e-12) : null;
      let rSq = NaN;
      try {
        if (o.radius_sq !== undefined) rSq = toNumber(o.radius_sq);
      } catch {
        rSq = NaN;
      }
      if (!center || !normal || !Number.isFinite(rSq) || rSq <= 0) {
        record("mesh_consistency", "INVALID", [o.id], `Circle "${o.id}" has invalid center, normal, or non-positive radius_sq.`);
      } else {
        record("mesh_consistency", "VALID", [o.id], `Circle "${o.id}" parameters valid.`);
        const planeDep = o.depends
          .map((id) => allById.get(id))
          .find((d): d is SceneObject => Boolean(d && d.render === "surface"));
        if (planeDep) {
          const pl = getPlaneData(planeDep);
          if (!pl) {
            record("intersection_consistency", "UNDETERMINED", [o.id, planeDep.id], `Plane "${planeDep.id}" incomplete.`);
          } else {
            const cDist = distPointPlane(center, pl.point, pl.normal);
            const sinAngle = len3(cross3(normal, pl.normal));
            const ok = cDist <= distTol && sinAngle <= dirTol;
            record(
              "intersection_consistency",
              ok ? "VALID" : "INVALID",
              [o.id, planeDep.id],
              ok
                ? `Circle "${o.id}" center & normal match plane "${planeDep.id}".`
                : `Circle "${o.id}" does not lie in plane "${planeDep.id}" (dist=${cDist.toExponential(3)}, angle=${sinAngle.toExponential(3)}).`,
              cDist,
              distTol,
            );
          }
          const ballDep = o.depends
            .map((id) => allById.get(id))
            .find((d): d is SceneObject => Boolean(d && d.type === "curved_solid" && d.curved_kind === "ball"));
          if (ballDep?.anchor && ballDep.radius_sq !== undefined && pl) {
            const sphC = safeToVec3(ballDep.anchor);
            let bigRSq = NaN;
            try {
              bigRSq = toNumber(ballDep.radius_sq);
            } catch {
              bigRSq = NaN;
            }
            if (sphC && Number.isFinite(bigRSq) && bigRSq > 0) {
              const d = distPointPlane(sphC, pl.point, pl.normal);
              const rCircle = Math.sqrt(rSq);
              const bigR = Math.sqrt(bigRSq);
              const radialErr = Math.abs(Math.hypot(d, rCircle) - bigR);
              record(
                "intersection_consistency",
                radialErr <= distTol ? "VALID" : "INVALID",
                [o.id, ballDep.id, planeDep.id],
                radialErr <= distTol
                  ? `Sphere-plane circle "${o.id}" satisfies R^2 = d^2 + r^2.`
                  : `Sphere-plane circle "${o.id}" violates R^2 = d^2 + r^2 (err=${radialErr.toExponential(3)}).`,
                radialErr,
                distTol,
              );
            }
          }
        }

        // 24-point 3D curved-surface perimeter sampling for circle sections / rims on ball, cylinder, cone
        if (o.semantic_role !== "INSCRIBED_CIRCLE") {
          const rCircle = Math.sqrt(rSq);
          const [uAx, vAx] = planeBasisFromNormal(normal);
          const samplePts: Vec3[] = [];
          for (let i = 0; i < 24; i += 1) {
            const theta = (2 * Math.PI * i) / 24;
            const cs = Math.cos(theta);
            const sn = Math.sin(theta);
            samplePts.push([
              center[0] + rCircle * (cs * uAx[0] + sn * vAx[0]),
              center[1] + rCircle * (cs * uAx[1] + sn * vAx[1]),
              center[2] + rCircle * (cs * uAx[2] + sn * vAx[2]),
            ]);
          }
          const resolveCurvedRadius = (csObj: SceneObject, anchorVec: Vec3): number => {
            if (csObj.radius_sq !== undefined) {
              try {
                const r2 = toNumber(csObj.radius_sq);
                if (Number.isFinite(r2) && r2 > 0) return Math.sqrt(r2);
              } catch {
                // fallback below
              }
            }
            const rim = safeToVec3(csObj.rim_point);
            return rim ? dist3(anchorVec, rim) : NaN;
          };

          for (const depId of o.depends ?? []) {
            const curvedDep = allById.get(depId);
            if (!curvedDep || curvedDep.type !== "curved_solid" || !curvedDep.anchor) continue;
            const anchorVec = safeToVec3(curvedDep.anchor);
            if (!anchorVec) continue;
            const curvedR = resolveCurvedRadius(curvedDep, anchorVec);
            if (!Number.isFinite(curvedR) || curvedR <= 0) continue;
            const curveTol = Math.max(distTol, 5e-4 * curvedR);

            if (curvedDep.curved_kind === "ball") {
              let maxErr = 0;
              for (const pt of samplePts) {
                maxErr = Math.max(maxErr, Math.abs(dist3(pt, anchorVec) - curvedR));
              }
              record(
                "intersection_consistency",
                maxErr <= curveTol ? "VALID" : "INVALID",
                [o.id, curvedDep.id],
                maxErr <= curveTol
                  ? `Circle "${o.id}" 24-point perimeter lies on sphere "${curvedDep.id}".`
                  : `Circle "${o.id}" 24-point perimeter deviates from sphere "${curvedDep.id}" by ${maxErr.toExponential(3)}.`,
                maxErr,
                curveTol,
              );
            } else if (curvedDep.curved_kind === "cylinder" || curvedDep.curved_kind === "cone") {
              const topVec = safeToVec3(curvedDep.apex_or_top);
              if (!topVec) continue;
              const axisVec = sub3(topVec, anchorVec);
              const axisLen = len3(axisVec);
              const axisUnit = unit3(axisVec, 1e-12);
              if (!axisUnit || axisLen <= minEdgeLen) continue;
              let maxErr = 0;
              for (const pt of samplePts) {
                const { dist: radialDist, along } = pointLineProjection(pt, anchorVec, axisUnit);
                const axialOverhang = Math.max(0, -along, along - axisLen);
                const expectedR =
                  curvedDep.curved_kind === "cone"
                    ? curvedR * Math.max(0, Math.min(1, 1 - along / axisLen))
                    : curvedR;
                maxErr = Math.max(maxErr, Math.abs(radialDist - expectedR), axialOverhang);
              }
              record(
                "intersection_consistency",
                maxErr <= curveTol ? "VALID" : "INVALID",
                [o.id, curvedDep.id],
                maxErr <= curveTol
                  ? `Circle "${o.id}" 24-point perimeter lies on ${curvedDep.curved_kind} "${curvedDep.id}".`
                  : `Circle "${o.id}" 24-point perimeter deviates from ${curvedDep.curved_kind} "${curvedDep.id}" by ${maxErr.toExponential(3)}.`,
                maxErr,
                curveTol,
              );
            }
          }
        }
      }
    }

    // Standalone sphere tangent-plane distance check
    if (o.render === "surface") {
      const pl = getPlaneData(o);
      if (pl && !/cut|secant|intersect|cat/i.test(o.producer ?? "")) {
        for (const ball of visibleObjects) {
          if (ball.type !== "curved_solid" || ball.curved_kind !== "ball" || !ball.anchor) continue;
          const hasSecantCircle = visibleObjects.some(
            (c) =>
              c.render === "circle"
              && (c.depends ?? []).includes(ball.id)
              && (c.depends ?? []).includes(o.id),
          );
          if (hasSecantCircle) continue;
          const sphC = safeToVec3(ball.anchor);
          let bigR = NaN;
          if (ball.radius_sq !== undefined) {
            try {
              const r2 = toNumber(ball.radius_sq);
              if (Number.isFinite(r2) && r2 > 0) bigR = Math.sqrt(r2);
            } catch {
              bigR = NaN;
            }
          } else if (sphC && ball.rim_point) {
            const rim = safeToVec3(ball.rim_point);
            if (rim) bigR = dist3(sphC, rim);
          }
          if (!sphC || !Number.isFinite(bigR) || bigR <= 0) continue;

          const tangentTol = Math.max(distTol, 5e-4 * bigR);
          const hasTangentLink =
            ((o.depends ?? []).includes(ball.id))
            || (/tangent|tiep_xuc|tiep_diem/i.test(o.producer ?? "")
              && ((o.depends ?? []).includes(ball.id)
                || visibleObjects.filter((b) => b.type === "curved_solid" && b.curved_kind === "ball").length === 1))
            || visibleObjects.some((pt) => {
              if (pt.type !== "point3" || !pt.xyz) return false;
              const pProd = pt.producer ?? "";
              if (!/tangent|tiep_xuc|tiep_diem/i.test(pProd)) return false;
              const pv = safeToVec3(pt.xyz);
              if (!pv) return false;
              return (
                ((pt.depends ?? []).includes(ball.id) || (pt.depends ?? []).includes(o.id))
                && distPointPlane(pv, pl.point, pl.normal) <= tangentTol
                && Math.abs(dist3(pv, sphC) - bigR) <= tangentTol
              );
            });
          const hasWitnessTangent = visibleObjects.some((wObj) => {
            for (const w of [wObj.perpendicular_witness, wObj.annotation?.witness, wObj.annotation?.witness?.second]) {
              if (!w || w.on !== o.id || !w.foot) continue;
              const ft = safeToVec3(w.foot);
              if (!ft) continue;
              const fromId = "from" in w && typeof w.from === "string" ? w.from : wObj.annotation?.witness?.from;
              const fromObj = fromId ? allById.get(fromId) : undefined;
              const fromPt = fromObj?.xyz ? safeToVec3(fromObj.xyz) : null;
              if (fromPt && dist3(fromPt, sphC) <= tangentTol && Math.abs(dist3(ft, sphC) - bigR) <= tangentTol) {
                return true;
              }
            }
            return false;
          });
          if (!hasTangentLink && !hasWitnessTangent) continue;

          const dPlane = distPointPlane(sphC, pl.point, pl.normal);
          const err = Math.abs(dPlane - bigR);
          record(
            "intersection_consistency",
            err <= tangentTol ? "VALID" : "INVALID",
            [o.id, ball.id],
            err <= tangentTol
              ? `Tangent plane "${o.id}" sits at sphere radius from "${ball.id}".`
              : `Tangent plane "${o.id}" violates d(I, P) = R for sphere "${ball.id}" (|d-R|=${err.toExponential(3)}).`,
            err,
            tangentTol,
          );
        }
      }
    }

    // Solid mesh integrity (vertex bounds, face indices, face coplanarity)
    if (o.type === "solid" && Array.isArray(o.vertices) && Array.isArray(o.faces)) {
      const verts = o.vertices.map(safeToVec3);
      if (verts.some((v) => v === null) || verts.length < 4 || o.faces.length < 4) {
        record("mesh_consistency", "INVALID", [o.id], `Solid "${o.id}" has missing vertices or too few faces.`);
      } else {
        const cleanVerts = verts as Vec3[];
        let badFaceMsg: string | null = null;
        let maxFacePlaneErr = 0;
        for (let fi = 0; fi < o.faces.length; fi += 1) {
          const face = o.faces[fi];
          if (!Array.isArray(face) || face.length < 3) {
            badFaceMsg = `Face ${fi} of "${o.id}" has < 3 vertices.`;
            break;
          }
          const outOfBounds = face.some((idx) => !Number.isInteger(idx) || idx < 0 || idx >= cleanVerts.length);
          if (outOfBounds) {
            badFaceMsg = `Face ${fi} of "${o.id}" references out-of-range vertex index.`;
            break;
          }
          const facePts = face.map((idx) => cleanVerts[idx]);
          const fit = bestFitPlaneFromPoints(facePts);
          if (!fit) {
            badFaceMsg = `Face ${fi} of "${o.id}" is collinear/degenerate.`;
            break;
          }
          for (const p of facePts) {
            maxFacePlaneErr = Math.max(maxFacePlaneErr, distPointPlane(p, fit.origin, fit.unitNormal));
          }
        }
        record(
          "mesh_consistency",
          !badFaceMsg && maxFacePlaneErr <= distTol ? "VALID" : "INVALID",
          [o.id],
          badFaceMsg
            ?? (maxFacePlaneErr <= distTol
              ? `Solid "${o.id}" faces (${o.faces.length}) are valid and coplanar.`
              : `Solid "${o.id}" face has non-coplanar vertex deviation ${maxFacePlaneErr.toExponential(3)}.`),
          maxFacePlaneErr,
          distTol,
        );
      }
    }

    // Polygon & Section checks
    const rawPolySource = o.polygon ?? o.vertices;
    if ((o.type === "section" || o.type === "polygon3") && Array.isArray(rawPolySource)) {
      const rawPoly = rawPolySource.map(safeToVec3);
      if (rawPoly.some((v) => v === null)) {
        record("mesh_consistency", "INVALID", [o.id], `Polygon "${o.id}" contains non-finite vertex coordinates.`);
        continue;
      }
      const poly = rawPoly as Vec3[];
      if (poly.length < 3) {
        if (o.closed !== false) {
          record("section_connectivity", "INVALID", [o.id], `Closed polygon "${o.id}" has < 3 vertices.`);
        }
        continue;
      }

      const fit = bestFitPlaneFromPoints(poly);
      if (!fit) {
        record("point_on_plane", "INVALID", [o.id], `Polygon "${o.id}" vertices are collinear or coincident.`);
        record("section_connectivity", "INVALID", [o.id], `Polygon "${o.id}" encloses zero area.`);
        continue;
      }

      // Coplanarity of polygon vertices
      let maxPolyOffPlane = 0;
      for (const p of poly) {
        maxPolyOffPlane = Math.max(maxPolyOffPlane, distPointPlane(p, fit.origin, fit.unitNormal));
      }
      record(
        "point_on_plane",
        maxPolyOffPlane <= distTol ? "VALID" : "INVALID",
        [o.id],
        maxPolyOffPlane <= distTol
          ? `All ${poly.length} vertices of "${o.id}" are coplanar.`
          : `Vertex of "${o.id}" deviates from polygon plane by ${maxPolyOffPlane.toExponential(3)}.`,
        maxPolyOffPlane,
        distTol,
      );

      // Adjacent edge lengths & non-self-intersection & area
      const [u, v] = planeBasisFromNormal(fit.unitNormal);
      const poly2D = poly.map((p): [number, number] => {
        const d = sub3(p, fit.origin);
        return [dot3(d, u), dot3(d, v)];
      });
      const signedArea = Math.abs(dienTichCoDau(poly2D));
      let minAdjEdge = Infinity;
      const edgeCount = o.closed === false ? poly.length - 1 : poly.length;
      for (let i = 0; i < edgeCount; i += 1) {
        const j = (i + 1) % poly.length;
        minAdjEdge = Math.min(minAdjEdge, dist3(poly[i], poly[j]));
      }
      let selfIntersects = false;
      for (let i = 0; i < edgeCount && !selfIntersects; i += 1) {
        const iNext = (i + 1) % poly.length;
        for (let k = i + 1; k < edgeCount; k += 1) {
          const kNext = (k + 1) % poly.length;
          if (i === k || iNext === k || kNext === i) continue;
          if (segmentsProperlyIntersect2D(poly2D[i], poly2D[iNext], poly2D[k], poly2D[kNext], distTol)) {
            selfIntersects = true;
            break;
          }
        }
      }

      const connValid =
        signedArea > areaTol
        && minAdjEdge > minEdgeLen
        && !selfIntersects;
      record(
        "section_connectivity",
        connValid ? "VALID" : "INVALID",
        [o.id],
        connValid
          ? `Polygon "${o.id}" edges are ordered, non-degenerate, and non-self-intersecting.`
          : `Polygon "${o.id}" connectivity defect (area=${signedArea.toExponential(2)}, minEdge=${minAdjEdge.toExponential(2)}, selfCross=${selfIntersects}).`,
      );

      // Section steps edge-to-boundary verification (order-independent edge coverage)
      if (Array.isArray(o.steps) && o.steps.length > 0 && o.closed !== false) {
        let stepsOk = true;
        let stepReason = "";
        let maxStepMismatch = 0;
        const n = poly.length;
        for (let si = 0; si < o.steps.length; si += 1) {
          const st = o.steps[si];
          const sa = safeToVec3(st.a);
          const sb = safeToVec3(st.b);
          if (!sa || !sb) {
            stepsOk = false;
            stepReason = `Step ${si} has invalid endpoints.`;
            break;
          }
          const idxA = poly.findIndex((p) => dist3(p, sa) <= distTol);
          const idxB = poly.findIndex((p) => dist3(p, sb) <= distTol);
          if (idxA === -1 || idxB === -1 || idxA === idxB) {
            stepsOk = false;
            stepReason = `Step ${si} endpoints do not map to distinct section vertices.`;
            break;
          }
          const diff = (idxB - idxA + n) % n;
          if (diff !== 1 && diff !== n - 1) {
            stepsOk = false;
            stepReason = `Step ${si} jumps non-adjacent polygon vertices ${idxA} -> ${idxB}.`;
            break;
          }
          maxStepMismatch = Math.max(maxStepMismatch, dist3(poly[idxA], sa), dist3(poly[idxB], sb));
        }
        record(
          "section_connectivity",
          stepsOk && maxStepMismatch <= distTol ? "VALID" : "INVALID",
          [o.id],
          stepsOk && maxStepMismatch <= distTol
            ? `Section "${o.id}" steps match polygon boundary edges.`
            : stepReason || `Section "${o.id}" step endpoint mismatch ${maxStepMismatch.toExponential(3)}.`,
          maxStepMismatch,
          distTol,
        );
      }

      // Section intersection against parent plane & solid vertex sources
      const cuttingPlane = o.depends
        .map((id) => allById.get(id))
        .find((d): d is SceneObject => Boolean(d && d.render === "surface"));
      if (cuttingPlane) {
        const pl = getPlaneData(cuttingPlane);
        if (!pl) {
          record("intersection_consistency", "UNDETERMINED", [o.id, cuttingPlane.id], `Cutting plane "${cuttingPlane.id}" incomplete.`);
        } else {
          let maxCutErr = 0;
          for (const p of poly) {
            maxCutErr = Math.max(maxCutErr, distPointPlane(p, pl.point, pl.normal));
          }
          record(
            "intersection_consistency",
            maxCutErr <= distTol ? "VALID" : "INVALID",
            [o.id, cuttingPlane.id],
            maxCutErr <= distTol
              ? `Section "${o.id}" lies on cutting plane "${cuttingPlane.id}".`
              : `Section "${o.id}" deviates from cutting plane "${cuttingPlane.id}" by ${maxCutErr.toExponential(3)}.`,
            maxCutErr,
            distTol,
          );
        }
      }

      if (Array.isArray(o.vertex_sources) && o.vertex_sources.length === poly.length) {
        const targetSolid =
          o.depends.map((id) => allById.get(id)).find((d) => d?.type === "solid" && Array.isArray(d.vertices))
          ?? visibleSolids[0];
        if (targetSolid?.vertices) {
          const solidVerts = targetSolid.vertices.map(safeToVec3);
          let maxSrcErr = 0;
          let srcFailMsg: string | null = null;
          for (let vi = 0; vi < poly.length; vi += 1) {
            const vs = o.vertex_sources[vi];
            if (vs.kind === "SOLID_VERTEX" && vs.solid_vertex_index != null) {
              const sv = solidVerts[vs.solid_vertex_index];
              if (!sv) {
                srcFailMsg = `Invalid solid_vertex_index ${vs.solid_vertex_index} on "${o.id}".`;
                break;
              }
              maxSrcErr = Math.max(maxSrcErr, dist3(poly[vi], sv));
            } else if (
              vs.kind === "SOLID_EDGE_INTERSECTION"
              && Array.isArray(vs.solid_edge_vertex_indices)
              && vs.solid_edge_vertex_indices.length === 2
            ) {
              const va = solidVerts[vs.solid_edge_vertex_indices[0]];
              const vb = solidVerts[vs.solid_edge_vertex_indices[1]];
              if (!va || !vb) {
                srcFailMsg = `Invalid solid_edge_vertex_indices on "${o.id}".`;
                break;
              }
              const edgeDir = unit3(sub3(vb, va));
              const edgeLen = dist3(va, vb);
              if (!edgeDir || edgeLen <= minEdgeLen) {
                srcFailMsg = `Degenerate source edge for vertex ${vi} on "${o.id}".`;
                break;
              }
              const proj = pointLineProjection(poly[vi], va, edgeDir);
              const t = proj.along / edgeLen;
              const domainErr = t < 0 ? -t * edgeLen : t > 1 ? (t - 1) * edgeLen : 0;
              maxSrcErr = Math.max(maxSrcErr, proj.dist, domainErr);
            }
          }
          record(
            "intersection_consistency",
            !srcFailMsg && maxSrcErr <= distTol ? "VALID" : "INVALID",
            [o.id, targetSolid.id],
            srcFailMsg
              ?? (maxSrcErr <= distTol
                ? `All section vertices of "${o.id}" satisfy Backend solid vertex/edge sources.`
                : `Section vertex source mismatch on "${o.id}": ${maxSrcErr.toExponential(3)}.`),
            maxSrcErr,
            distTol,
          );
        }
      }

      // Section mesh triangulation
      try {
        const tris = chiaTamGiac(poly);
        record(
          "mesh_consistency",
          tris.length >= poly.length - 2 ? "VALID" : "INVALID",
          [o.id],
          tris.length >= poly.length - 2
            ? `Polygon "${o.id}" triangulated (${tris.length} tris).`
            : `Polygon "${o.id}" triangulation missing triangles (${tris.length}/${poly.length - 2}).`,
        );
      } catch (err) {
        record(
          "mesh_consistency",
          "INVALID",
          [o.id],
          `Polygon "${o.id}" triangulation threw: ${err instanceof Error ? err.message : String(err)}`,
        );
      }
    }

    // Perpendicular witness marker orthogonality
    for (const w of [o.perpendicular_witness, o.annotation?.witness, o.annotation?.witness?.second]) {
      if (!w?.marker?.u || !w.marker.v) continue;
      const uVec = safeToVec3(w.marker.u);
      const vVec = safeToVec3(w.marker.v);
      if (!uVec || !vVec) {
        record("mesh_consistency", "UNDETERMINED", [o.id], `Witness marker vectors on "${o.id}" are invalid.`);
        continue;
      }
      const uLen = len3(uVec);
      const vLen = len3(vVec);
      const orthoTol = Math.max(dirTol, 1e-3);
      if (uLen <= 1e-9 || vLen <= 1e-9) {
        record("mesh_consistency", "INVALID", [o.id], `Witness marker on "${o.id}" has zero-length axis vector.`);
        continue;
      }
      const cosErr = Math.abs(dot3(uVec, vVec) / (uLen * vLen));
      record(
        "mesh_consistency",
        cosErr <= orthoTol ? "VALID" : "INVALID",
        [o.id],
        cosErr <= orthoTol
          ? `Perpendicular witness marker on "${o.id}" is orthogonal.`
          : `Perpendicular witness marker on "${o.id}" is non-orthogonal (|cos|=${cosErr.toExponential(3)}).`,
        cosErr,
        orthoTol,
      );
    }
  }

  let totalChecked = 0;
  let anyInvalid = false;
  let anyUndetermined = false;
  for (const kind of CHECK_KINDS) {
    const s = summaries[kind];
    totalChecked += s.checkedCount;
    if (s.invalidCount > 0) {
      s.status = "INVALID";
      anyInvalid = true;
    } else if (s.undeterminedCount > 0) {
      s.status = "UNDETERMINED";
      anyUndetermined = true;
    } else {
      s.status = "VALID";
    }
  }

  const overallStatus: ConsistencyStatus = anyInvalid
    ? "INVALID"
    : anyUndetermined
      ? "UNDETERMINED"
      : totalChecked > 0 || (visibleObjects.every((o) => o.type !== "point3" || safeToVec3(o.xyz) !== null) && finitePts.length > 0)
        ? "VALID"
        : "UNDETERMINED";

  const report: SceneConsistencyReport = {
    overallStatus,
    stepIndex: resolvedStep,
    sceneScale,
    tolerances: {
      distance: distTol,
      direction: dirTol,
      area: areaTol,
    },
    checks: summaries,
    findings,
    isConsistent: overallStatus === "VALID",
  };

  if (!options.bypassCache && rawScene && typeof rawScene === "object") {
    let map = REPORT_CACHE.get(rawScene);
    if (!map) {
      map = new Map();
      REPORT_CACHE.set(rawScene, map);
    }
    map.set(cacheKey, report);
  }
  return report;
}

export type MathematicalInvariantCategory =
  | "point_on_line"
  | "point_on_plane"
  | "line_plane_intersection"
  | "plane_plane_intersection"
  | "section_polygon"
  | "tangency"
  | "curved_intersections";

export interface MathematicalInvariantCheckResult {
  category: MathematicalInvariantCategory;
  status: ConsistencyStatus;
  checkedCount: number;
  validCount: number;
  invalidCount: number;
  undeterminedCount: number;
  maxNormalizedError: number;
  findings: ConsistencyFinding[];
}

export interface SceneMathematicalInvariantsReport {
  overallStatus: ConsistencyStatus;
  isValid: boolean;
  stepIndex: number | null;
  sceneScale: number;
  tolerances: {
    distance: number;
    direction: number;
    area: number;
  };
  categories: Record<MathematicalInvariantCategory, MathematicalInvariantCheckResult>;
  findings: ConsistencyFinding[];
  baseReport: SceneConsistencyReport;
}

function emptyInvariantCategories(): Record<MathematicalInvariantCategory, MathematicalInvariantCheckResult> {
  const mk = (category: MathematicalInvariantCategory): MathematicalInvariantCheckResult => ({
    category,
    status: "VALID",
    checkedCount: 0,
    validCount: 0,
    invalidCount: 0,
    undeterminedCount: 0,
    maxNormalizedError: 0,
    findings: [],
  });
  return {
    point_on_line: mk("point_on_line"),
    point_on_plane: mk("point_on_plane"),
    line_plane_intersection: mk("line_plane_intersection"),
    plane_plane_intersection: mk("plane_plane_intersection"),
    section_polygon: mk("section_polygon"),
    tangency: mk("tangency"),
    curved_intersections: mk("curved_intersections"),
  };
}

/**
 * Verifies all V9.4.17 scale-adaptive mathematical invariants across points, lines,
 * infinite planes, plane-plane / line-plane intersections, section polygons, tangency
 * witnesses, and curved-surface plane intersections without mutating `rawScene`.
 */
export function verifySceneMathematicalInvariants(
  rawScene: Scene3D,
  options: AuditRepresentationOptions = {},
): SceneMathematicalInvariantsReport {
  const baseReport = auditSceneRepresentationConsistency(rawScene, options);
  const categories = emptyInvariantCategories();
  const extraFindings: ConsistencyFinding[] = [];

  const pushCategoryRecord = (
    category: MathematicalInvariantCategory,
    check: ConsistencyCheckKind,
    status: ConsistencyStatus,
    objectIds: string[],
    message: string,
    measuredError?: number,
    tolerance?: number,
  ) => {
    const slot = categories[category];
    slot.checkedCount += 1;
    if (status === "VALID") slot.validCount += 1;
    else if (status === "INVALID") slot.invalidCount += 1;
    else slot.undeterminedCount += 1;
    if (
      measuredError !== undefined
      && tolerance !== undefined
      && Number.isFinite(measuredError)
      && tolerance > 0
    ) {
      slot.maxNormalizedError = Math.max(slot.maxNormalizedError, measuredError / tolerance);
    }
    if (status !== "VALID") {
      const f: ConsistencyFinding = { check, status, objectIds, message, measuredError, tolerance };
      slot.findings.push(f);
      extraFindings.push(f);
    }
  };

  // Seed direct checks already audited in baseReport
  const mirrorSummary = (src: ConsistencyCheckKind, dst: MathematicalInvariantCategory) => {
    const s = baseReport.checks[src];
    const d = categories[dst];
    d.checkedCount += s.checkedCount;
    d.validCount += s.validCount;
    d.invalidCount += s.invalidCount;
    d.undeterminedCount += s.undeterminedCount;
    d.maxNormalizedError = Math.max(d.maxNormalizedError, s.maxNormalizedError);
    d.findings.push(...s.findings);
  };
  mirrorSummary("point_on_line", "point_on_line");
  mirrorSummary("point_on_plane", "point_on_plane");
  mirrorSummary("section_connectivity", "section_polygon");

  let scene: Scene3D;
  try {
    scene = veKhongGian(rawScene);
  } catch {
    categories.point_on_plane.status = baseReport.overallStatus === "INVALID" ? "INVALID" : "UNDETERMINED";
    return {
      overallStatus: baseReport.overallStatus,
      isValid: baseReport.isConsistent,
      stepIndex: baseReport.stepIndex,
      sceneScale: baseReport.sceneScale,
      tolerances: baseReport.tolerances,
      categories,
      findings: [...baseReport.findings],
      baseReport,
    };
  }

  const resolvedStep = options.step !== undefined ? clampStep(scene, options.step) : null;
  const visibleObjects = resolvedStep !== null ? objectsAt(scene, resolvedStep) : [...scene.objects];
  const byId = new Map<string, SceneObject>(visibleObjects.map((o) => [o.id, o]));
  const allById = new Map<string, SceneObject>(scene.objects.map((o) => [o.id, o]));
  const distTol = baseReport.tolerances.distance > 0 ? baseReport.tolerances.distance : 1e-6;
  const dirTol = baseReport.tolerances.direction > 0 ? baseReport.tolerances.direction : 1e-4;
  const areaTol = baseReport.tolerances.area > 0 ? baseReport.tolerances.area : 1e-12;
  const scale = Math.max(baseReport.sceneScale, 1e-9);

  const getPlane = (o?: SceneObject): { point: Vec3; normal: Vec3 } | null => {
    if (!o) return null;
    const pt = safeToVec3(o.point);
    const nRaw = safeToVec3(o.normal);
    const n = nRaw ? unit3(nRaw, 1e-15) : null;
    return pt && n ? { point: pt, normal: n } : null;
  };
  const getLine = (o?: SceneObject): { origin: Vec3; dir: Vec3; end?: Vec3 } | null => {
    if (!o) return null;
    if (o.render === "line") {
      const p = safeToVec3(o.point);
      const dRaw = safeToVec3(o.direction);
      const d = dRaw ? unit3(dRaw, 1e-15) : null;
      return p && d ? { origin: p, dir: d } : null;
    }
    const pa = safeToVec3(o.endpoints?.[0] ?? o.point_a);
    const pb = safeToVec3(o.endpoints?.[1] ?? o.point_b);
    if (!pa || !pb) return null;
    const d = unit3(sub3(pb, pa), 1e-15);
    return d ? { origin: pa, dir: d, end: pb } : null;
  };

  // A. Line-Plane Intersection (P ∈ line AND P ∈ plane; flag parallel line-plane vs in-plane)
  for (const o of visibleObjects) {
    if (o.type !== "point3" || !o.xyz) continue;
    const pv = safeToVec3(o.xyz);
    if (!pv) continue;
    const deps = (o.depends ?? []).map((id) => byId.get(id) ?? allById.get(id)).filter((x): x is SceneObject => Boolean(x));
    const lineDep = deps.find((d) => d.render === "line" || d.render === "segment");
    const planeDep = deps.find((d) => d.render === "surface" || d.type === "plane3");
    if (!lineDep || !planeDep) continue;
    const ln = getLine(lineDep);
    const pl = getPlane(planeDep);
    if (!ln || !pl) {
      pushCategoryRecord("line_plane_intersection", "intersection_consistency", "UNDETERMINED", [o.id, lineDep.id, planeDep.id], `Line-plane intersection "${o.id}" lacks finite carrier data.`);
      continue;
    }
    const cosAng = Math.abs(dot3(ln.dir, pl.normal));
    const lineErr = pointLineProjection(pv, ln.origin, ln.dir).dist;
    const planeErr = distPointPlane(pv, pl.point, pl.normal);
    if (cosAng <= dirTol) {
      const lineDistToPlane = distPointPlane(ln.origin, pl.point, pl.normal);
      const ok = lineDistToPlane <= distTol && lineErr <= distTol && planeErr <= distTol;
      pushCategoryRecord(
        "line_plane_intersection",
        "intersection_consistency",
        ok ? "VALID" : "INVALID",
        [o.id, lineDep.id, planeDep.id],
        ok
          ? `Line "${lineDep.id}" lies in "${planeDep.id}" at "${o.id}".`
          : `Parallel line "${lineDep.id}" and plane "${planeDep.id}" cannot yield isolated intersection "${o.id}" (line-plane dist=${lineDistToPlane.toExponential(2)}).`,
        Math.max(lineDistToPlane, lineErr, planeErr),
        distTol,
      );
    } else {
      const err = Math.max(lineErr, planeErr);
      pushCategoryRecord(
        "line_plane_intersection",
        "intersection_consistency",
        err <= distTol ? "VALID" : "INVALID",
        [o.id, lineDep.id, planeDep.id],
        err <= distTol
          ? `Intersection point "${o.id}" lies on both "${lineDep.id}" and "${planeDep.id}".`
          : `Intersection point "${o.id}" misses line/plane (err=${err.toExponential(3)}).`,
        err,
        distTol,
      );
    }
  }

  // B. Plane-Plane Intersection (unique line vs parallel vs coincident)
  for (const o of visibleObjects) {
    if (o.render !== "line" && o.render !== "segment") continue;
    const planeDeps = (o.depends ?? [])
      .map((id) => byId.get(id) ?? allById.get(id))
      .filter((d): d is SceneObject => Boolean(d && (d.render === "surface" || d.type === "plane3")));
    if (planeDeps.length < 2) continue;
    const ln = getLine(o);
    const plA = getPlane(planeDeps[0]);
    const plB = getPlane(planeDeps[1]);
    if (!ln || !plA || !plB) {
      pushCategoryRecord("plane_plane_intersection", "intersection_consistency", "UNDETERMINED", [o.id, planeDeps[0].id, planeDeps[1].id], `Plane-plane intersection "${o.id}" lacks plane or line carrier.`);
      continue;
    }
    const sinTheta = len3(cross3(plA.normal, plB.normal));
    if (sinTheta <= dirTol) {
      const offset = distPointPlane(plB.point, plA.point, plA.normal);
      pushCategoryRecord(
        "plane_plane_intersection",
        "intersection_consistency",
        "INVALID",
        [o.id, planeDeps[0].id, planeDeps[1].id],
        offset <= distTol
          ? `Planes "${planeDeps[0].id}" and "${planeDeps[1].id}" are coincident, not an isolated line "${o.id}".`
          : `Planes "${planeDeps[0].id}" and "${planeDeps[1].id}" are strictly parallel (gap=${offset.toExponential(2)}), no intersection line "${o.id}".`,
        offset,
        distTol,
      );
    } else {
      const distErr = Math.max(
        distPointPlane(ln.origin, plA.point, plA.normal),
        distPointPlane(ln.origin, plB.point, plB.normal),
        ln.end ? distPointPlane(ln.end, plA.point, plA.normal) : 0,
        ln.end ? distPointPlane(ln.end, plB.point, plB.normal) : 0,
      );
      const orthoErr = Math.max(Math.abs(dot3(ln.dir, plA.normal)), Math.abs(dot3(ln.dir, plB.normal)));
      const ok = distErr <= distTol && orthoErr <= dirTol;
      pushCategoryRecord(
        "plane_plane_intersection",
        "intersection_consistency",
        ok ? "VALID" : "INVALID",
        [o.id, planeDeps[0].id, planeDeps[1].id],
        ok
          ? `Line "${o.id}" is the exact intersection of "${planeDeps[0].id}" and "${planeDeps[1].id}".`
          : `Line "${o.id}" deviates from intersection of "${planeDeps[0].id}" and "${planeDeps[1].id}" (dist=${distErr.toExponential(2)}, ortho=${orthoErr.toExponential(2)}).`,
        Math.max(distErr, orthoErr * scale),
        distTol,
      );
    }
  }

  // C. Section Polygon face-coplanar edges & triangulation area sanity
  const solids = visibleObjects.filter((s) => s.type === "solid" && Array.isArray(s.vertices) && Array.isArray(s.faces));
  for (const o of visibleObjects) {
    if (o.type !== "section" && !(o.type === "polygon3" && o.semantic_role === "RESULT_SECTION")) continue;
    const rawPoly = (o.polygon ?? o.vertices ?? []).map(safeToVec3);
    if (rawPoly.length < 3 || rawPoly.some((v) => v === null)) {
      pushCategoryRecord("section_polygon", "section_connectivity", "INVALID", [o.id], `Section "${o.id}" has missing or fewer than 3 vertices.`);
      continue;
    }
    const poly = rawPoly as Vec3[];
    const tris = chiaTamGiac(poly);
    const trisOk = tris.length >= poly.length - 2 && tris.every(([i, j, k]) => {
      const a = poly[i], b = poly[j], c = poly[k];
      const cr = cross3(sub3(b, a), sub3(c, a));
      return 0.5 * len3(cr) > areaTol * 0.1;
    });
    pushCategoryRecord(
      "section_polygon",
      "mesh_consistency",
      trisOk ? "VALID" : "INVALID",
      [o.id],
      trisOk
        ? `Section "${o.id}" triangulation produces ${tris.length} non-degenerate triangles.`
        : `Section "${o.id}" triangulation has missing or degenerate triangles.`,
    );

    const hostSolid =
      (o.depends ?? []).map((id) => allById.get(id)).find((d) => d?.type === "solid" && d.vertices && d.faces)
      ?? solids[0];
    if (hostSolid?.vertices && hostSolid.faces) {
      const sVerts = hostSolid.vertices.map(safeToVec3);
      if (sVerts.every((v): v is Vec3 => v !== null)) {
        const facePlanes = hostSolid.faces
          .map((f) => bestFitPlaneFromPoints(f.map((vi) => sVerts[vi]).filter(Boolean)))
          .filter((fp): fp is NonNullable<typeof fp> => fp !== null);
        if (facePlanes.length > 0 && o.closed !== false) {
          let maxEdgeFaceErr = 0;
          for (let i = 0; i < poly.length; i += 1) {
            const pA = poly[i];
            const pB = poly[(i + 1) % poly.length];
            let bestFaceErr = Infinity;
            for (const fp of facePlanes) {
              const e = Math.max(distPointPlane(pA, fp.origin, fp.unitNormal), distPointPlane(pB, fp.origin, fp.unitNormal));
              if (e < bestFaceErr) bestFaceErr = e;
            }
            maxEdgeFaceErr = Math.max(maxEdgeFaceErr, bestFaceErr);
          }
          pushCategoryRecord(
            "section_polygon",
            "section_connectivity",
            maxEdgeFaceErr <= distTol * 2 ? "VALID" : "INVALID",
            [o.id, hostSolid.id],
            maxEdgeFaceErr <= distTol * 2
              ? `Every edge of section "${o.id}" lies on a face of solid "${hostSolid.id}".`
              : `Section "${o.id}" edge does not lie on any face of "${hostSolid.id}" (err=${maxEdgeFaceErr.toExponential(2)}).`,
            maxEdgeFaceErr,
            distTol * 2,
          );
        }
      }
    }
  }

  // D. Tangency: d(I, P) = R, A ∈ sphere, A ∈ P, IA ⊥ P
  const balls = visibleObjects.filter((b) => b.type === "curved_solid" && b.curved_kind === "ball" && b.anchor);
  const planes = visibleObjects.filter((p) => p.render === "surface" || p.type === "plane3");
  for (const ball of balls) {
    const sphC = safeToVec3(ball.anchor);
    let bigR = NaN;
    if (ball.radius_sq !== undefined) {
      try {
        const r2 = toNumber(ball.radius_sq);
        if (Number.isFinite(r2) && r2 > 0) bigR = Math.sqrt(r2);
      } catch { bigR = NaN; }
    } else if (sphC && ball.rim_point) {
      const rim = safeToVec3(ball.rim_point);
      if (rim) bigR = dist3(sphC, rim);
    }
    if (!sphC || !Number.isFinite(bigR) || bigR <= 0) continue;
    const tangentTol = Math.max(distTol, 5e-4 * bigR);

    for (const plane of planes) {
      const pl = getPlane(plane);
      if (!pl) continue;
      const hasSecant = visibleObjects.some((c) => c.render === "circle" && (c.depends ?? []).includes(ball.id) && (c.depends ?? []).includes(plane.id));
      if (hasSecant) continue;
      const linked = (plane.depends ?? []).includes(ball.id) || visibleObjects.some((pt) =>
        pt.type === "point3" && pt.xyz && (pt.depends ?? []).includes(ball.id) && (pt.depends ?? []).includes(plane.id),
      ) || visibleObjects.some((wObj) =>
        [wObj.perpendicular_witness, wObj.annotation?.witness].some((w) => w?.on === plane.id),
      );
      const dIP = distPointPlane(sphC, pl.point, pl.normal);
      if (!linked && Math.abs(dIP - bigR) > tangentTol) continue;

      if (linked) {
        const err = Math.abs(dIP - bigR);
        pushCategoryRecord(
          "tangency",
          "intersection_consistency",
          err <= tangentTol ? "VALID" : "INVALID",
          [ball.id, plane.id],
          err <= tangentTol
            ? `Sphere "${ball.id}" tangent to "${plane.id}" (d(I,P)=R).`
            : `Tangent plane "${plane.id}" deviates from sphere "${ball.id}" radius by ${err.toExponential(3)}.`,
          err,
          tangentTol,
        );
      }

      // Check tangent point candidates A and radius IA ⊥ P
      for (const pt of visibleObjects) {
        if (pt.type !== "point3" || !pt.xyz) continue;
        const pv = safeToVec3(pt.xyz);
        if (!pv) continue;
        const isLinkedPt = (pt.depends ?? []).includes(ball.id) || (pt.depends ?? []).includes(plane.id) || (plane.depends ?? []).includes(pt.id);
        if (!isLinkedPt) continue;
        const onSphereErr = Math.abs(dist3(pv, sphC) - bigR);
        const onPlaneErr = distPointPlane(pv, pl.point, pl.normal);
        const radiusVec = sub3(pv, sphC);
        const radiusUnit = unit3(radiusVec, 1e-12);
        const perpSinErr = radiusUnit ? len3(cross3(radiusUnit, pl.normal)) : 1;
        if (onSphereErr <= tangentTol * 10 || onPlaneErr <= tangentTol * 10 || linked) {
          const ok = onSphereErr <= tangentTol && onPlaneErr <= tangentTol && perpSinErr <= Math.max(dirTol, 1e-3);
          pushCategoryRecord(
            "tangency",
            "intersection_consistency",
            ok ? "VALID" : "INVALID",
            [pt.id, ball.id, plane.id],
            ok
              ? `Tangent point "${pt.id}" satisfies A ∈ S, A ∈ P, and IA ⊥ P.`
              : `Tangency witness "${pt.id}" fails incidence/normal orthogonality (dS=${onSphereErr.toExponential(2)}, dP=${onPlaneErr.toExponential(2)}, sin=${perpSinErr.toExponential(2)}).`,
            Math.max(onSphereErr, onPlaneErr, perpSinErr * bigR),
            tangentTol,
          );
        }
      }
    }
  }

  // E. Curved Intersections (circle & ellipse sampled points on plane AND cone/cylinder/sphere)
  for (const f of baseReport.checks.intersection_consistency.findings) {
    if (f.status !== "VALID") {
      categories.curved_intersections.invalidCount += f.status === "INVALID" ? 1 : 0;
      categories.curved_intersections.undeterminedCount += f.status === "UNDETERMINED" ? 1 : 0;
      categories.curved_intersections.checkedCount += 1;
      categories.curved_intersections.findings.push(f);
    }
  }
  for (const o of visibleObjects) {
    if (o.render === "circle" && o.semantic_role !== "INSCRIBED_CIRCLE") {
      const center = safeToVec3(o.center);
      const nRaw = safeToVec3(o.normal);
      const normal = nRaw ? unit3(nRaw, 1e-12) : null;
      let rSq = NaN;
      try { if (o.radius_sq !== undefined) rSq = toNumber(o.radius_sq); } catch { rSq = NaN; }
      const planeDep = (o.depends ?? []).map((id) => allById.get(id)).find((d) => d && (d.render === "surface" || d.type === "plane3"));
      const pl = getPlane(planeDep);
      if (center && normal && Number.isFinite(rSq) && rSq > 0 && pl) {
        const rC = Math.sqrt(rSq);
        const [uAx, vAx] = planeBasisFromNormal(normal);
        let maxPlErr = 0;
        for (let i = 0; i < 24; i += 1) {
          const theta = (2 * Math.PI * i) / 24;
          const pt: Vec3 = [
            center[0] + rC * (Math.cos(theta) * uAx[0] + Math.sin(theta) * vAx[0]),
            center[1] + rC * (Math.cos(theta) * uAx[1] + Math.sin(theta) * vAx[1]),
            center[2] + rC * (Math.cos(theta) * uAx[2] + Math.sin(theta) * vAx[2]),
          ];
          maxPlErr = Math.max(maxPlErr, distPointPlane(pt, pl.point, pl.normal));
        }
        const tol = Math.max(distTol, 5e-4 * rC);
        pushCategoryRecord(
          "curved_intersections",
          "intersection_consistency",
          maxPlErr <= tol ? "VALID" : "INVALID",
          [o.id, planeDep!.id],
          maxPlErr <= tol
            ? `24-point circle sample of "${o.id}" lies on plane "${planeDep!.id}".`
            : `Circle "${o.id}" samples leave plane "${planeDep!.id}" by ${maxPlErr.toExponential(2)}.`,
          maxPlErr,
          tol,
        );
      }
    } else if (o.render === "ellipse") {
      const center = safeToVec3(o.center);
      const uMajRaw = safeToVec3(o.major_dir);
      const uMinRaw = safeToVec3(o.minor_dir);
      const uMaj = uMajRaw ? unit3(uMajRaw, 1e-12) : null;
      const uMin = uMinRaw ? unit3(uMinRaw, 1e-12) : null;
      let aSq = NaN;
      let bSq = NaN;
      try { if (o.semi_major_sq !== undefined) aSq = toNumber(o.semi_major_sq); } catch { aSq = NaN; }
      try { if (o.semi_minor_sq !== undefined) bSq = toNumber(o.semi_minor_sq); } catch { bSq = NaN; }
      const planeDep = (o.depends ?? []).map((id) => allById.get(id)).find((d) => d && (d.render === "surface" || d.type === "plane3"));
      const pl = getPlane(planeDep);
      if (center && uMaj && uMin && Number.isFinite(aSq) && aSq > 0 && Number.isFinite(bSq) && bSq > 0) {
        const aLen = Math.sqrt(aSq);
        const bLen = Math.sqrt(bSq);
        const tol = Math.max(distTol, 5e-4 * Math.max(aLen, bLen, 1e-6));
        const samplePts: Vec3[] = [];
        for (let i = 0; i < 24; i += 1) {
          const t = (2 * Math.PI * i) / 24;
          const cs = Math.cos(t);
          const sn = Math.sin(t);
          samplePts.push([
            center[0] + cs * aLen * uMaj[0] + sn * bLen * uMin[0],
            center[1] + cs * aLen * uMaj[1] + sn * bLen * uMin[1],
            center[2] + cs * aLen * uMaj[2] + sn * bLen * uMin[2],
          ]);
        }
        if (pl) {
          let maxPlErr = 0;
          for (const pt of samplePts) {
            maxPlErr = Math.max(maxPlErr, distPointPlane(pt, pl.point, pl.normal));
          }
          pushCategoryRecord(
            "curved_intersections",
            "intersection_consistency",
            maxPlErr <= tol ? "VALID" : "INVALID",
            [o.id, planeDep!.id],
            maxPlErr <= tol
              ? `24-point ellipse sample of "${o.id}" lies on plane "${planeDep!.id}".`
              : `Ellipse "${o.id}" samples leave plane "${planeDep!.id}" by ${maxPlErr.toExponential(2)}.`,
            maxPlErr,
            tol,
          );
        }
        for (const depId of o.depends ?? []) {
          const csObj = allById.get(depId);
          if (!csObj || csObj.type !== "curved_solid" || (csObj.curved_kind !== "cylinder" && csObj.curved_kind !== "cone")) continue;
          const anchorVec = safeToVec3(csObj.anchor);
          const topVec = safeToVec3(csObj.apex_or_top);
          if (!anchorVec || !topVec) continue;
          const axisVec = sub3(topVec, anchorVec);
          const axisLen = len3(axisVec);
          const axisUnit = unit3(axisVec, 1e-12);
          let csR = NaN;
          try { if (csObj.radius_sq !== undefined) csR = Math.sqrt(toNumber(csObj.radius_sq)); } catch { csR = NaN; }
          if (!Number.isFinite(csR) && csObj.rim_point) {
            const rim = safeToVec3(csObj.rim_point);
            if (rim) csR = dist3(anchorVec, rim);
          }
          if (!axisUnit || axisLen <= 1e-12 || !Number.isFinite(csR) || csR <= 0) continue;
          const csTol = Math.max(tol, 5e-4 * csR);
          let maxSurfErr = 0;
          for (const pt of samplePts) {
            const { dist: radialDist, along } = pointLineProjection(pt, anchorVec, axisUnit);
            const axialOverhang = Math.max(0, -along, along - axisLen);
            const expectedR = csObj.curved_kind === "cone"
              ? csR * Math.max(0, Math.min(1, 1 - along / axisLen))
              : csR;
            maxSurfErr = Math.max(maxSurfErr, Math.abs(radialDist - expectedR), axialOverhang);
          }
          pushCategoryRecord(
            "curved_intersections",
            "intersection_consistency",
            maxSurfErr <= csTol ? "VALID" : "INVALID",
            [o.id, csObj.id],
            maxSurfErr <= csTol
              ? `24-point ellipse sample of "${o.id}" lies on ${csObj.curved_kind} "${csObj.id}".`
              : `Ellipse "${o.id}" deviates from ${csObj.curved_kind} "${csObj.id}" by ${maxSurfErr.toExponential(2)}.`,
            maxSurfErr,
            csTol,
          );
        }
      }
    }
  }

  let anyInvalid = baseReport.overallStatus === "INVALID";
  let anyUndetermined = baseReport.overallStatus === "UNDETERMINED";
  for (const cat of Object.values(categories)) {
    if (cat.invalidCount > 0) {
      cat.status = "INVALID";
      anyInvalid = true;
    } else if (cat.undeterminedCount > 0) {
      cat.status = "UNDETERMINED";
      anyUndetermined = true;
    } else {
      cat.status = "VALID";
    }
  }
  const overallStatus: ConsistencyStatus = anyInvalid ? "INVALID" : anyUndetermined ? "UNDETERMINED" : "VALID";
  return {
    overallStatus,
    isValid: overallStatus === "VALID",
    stepIndex: baseReport.stepIndex,
    sceneScale: baseReport.sceneScale,
    tolerances: baseReport.tolerances,
    categories,
    findings: [...baseReport.findings, ...extraFindings],
    baseReport,
  };
}
