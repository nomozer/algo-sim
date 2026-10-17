/** Camera-relative edge visibility. Presentation-only; never feeds geometry state. */
import * as THREE from "three";
import { chiaTamGiac } from "./polygon-triangulate";
import { toVec3, type SceneObject } from "./scene3d-model";

export interface CanonicalEdge {
  id: string;
  a: THREE.Vector3;
  b: THREE.Vector3;
  adjacentFaces: number[];
  adjacentSurfaceIds: string[];
}

export interface EdgeVisibilitySpan {
  edge_id: string;
  t0: number;
  t1: number;
  visibility: "VISIBLE" | "HIDDEN";
}

export interface EdgeVisibilityAudit {
  visible_edge_ids: string[];
  hidden_edge_ids: string[];
  mixed_edge_ids: string[];
  duplicate_visual_owner_ids: string[];
  edge_spans: EdgeVisibilitySpan[];
  triangle_count: number;
  sample_count: number;
}

export interface VisibilityOptions {
  /** Physical projected length; refinement targets cells no wider than 0.5px. */
  projected_edge_pixels?: number | ((edge: CanonicalEdge) => number);
  /** Additional objects may occlude this owner when classifying a whole scene. */
  occluders?: SceneObject[];
}

export function canonicalEdgesOf(o: SceneObject): CanonicalEdge[] {
  if (o.type !== "solid" || !o.vertices || !o.vertex_ids || !o.faces) return [];
  if (o.vertices.length !== o.vertex_ids.length) return [];
  const indexById = new Map(o.vertex_ids.map((id, index) => [id, index]));
  if (o.edge_ownership?.length) {
    return o.edge_ownership.flatMap((owner): CanonicalEdge[] => {
      const ia = indexById.get(owner.endpoint_ids[0]);
      const ib = indexById.get(owner.endpoint_ids[1]);
      if (ia === undefined || ib === undefined) return [];
      const adjacentSurfaceIds = [...owner.adjacent_surface_ids];
      return [{
        id: owner.edge_id,
        a: new THREE.Vector3(...toVec3(o.vertices![ia])),
        b: new THREE.Vector3(...toVec3(o.vertices![ib])),
        adjacentFaces: adjacentSurfaceIds.map((id) => Number(id.split(":face:")[1]))
          .filter(Number.isInteger),
        adjacentSurfaceIds,
      }];
    }).sort((a, b) => a.id.localeCompare(b.id));
  }
  const byId = new Map<string, CanonicalEdge>();
  o.faces.forEach((face, faceIndex) => {
    for (let i = 0; i < face.length; i += 1) {
      const ia = face[i];
      const ib = face[(i + 1) % face.length];
      if (!o.vertices?.[ia] || !o.vertices?.[ib] || !o.vertex_ids?.[ia] || !o.vertex_ids?.[ib]) {
        continue;
      }
      const [first, second] = ia <= ib ? [ia, ib] : [ib, ia];
      const id = `${o.id}::edge:${o.vertex_ids[first]}-${o.vertex_ids[second]}`;
      const surfaceId = `${o.id}::face:${faceIndex}`;
      const existing = byId.get(id);
      if (existing) {
        if (!existing.adjacentFaces.includes(faceIndex)) existing.adjacentFaces.push(faceIndex);
        if (!existing.adjacentSurfaceIds.includes(surfaceId)) {
          existing.adjacentSurfaceIds.push(surfaceId);
        }
      } else {
        byId.set(id, {
          id,
          a: new THREE.Vector3(...toVec3(o.vertices[first])),
          b: new THREE.Vector3(...toVec3(o.vertices[second])),
          adjacentFaces: [faceIndex],
          adjacentSurfaceIds: [surfaceId],
        });
      }
    }
  });
  return [...byId.values()].sort((a, b) => a.id.localeCompare(b.id));
}

interface OccludingTriangle {
  surfaceId: string;
  a: THREE.Vector3;
  b: THREE.Vector3;
  c: THREE.Vector3;
  normal: THREE.Vector3;
  tri: THREE.Triangle;
  box: THREE.Box3;
}

export interface WorldSolidOccluder {
  solid: SceneObject;
  matrixWorld?: THREE.Matrix4;
}

export interface WorldSegmentVisibilityResult {
  spans: EdgeVisibilitySpan[];
  colinear_canonical_edge_ids: string[];
}

function occludingTriangles(objects: SceneObject[], transforms?: (THREE.Matrix4 | undefined)[]): OccludingTriangle[] {
  const triangles: OccludingTriangle[] = [];
  objects.forEach((object, objIdx) => {
    if (object.type !== "solid" || !object.vertices || !object.faces) return;
    const mat = transforms?.[objIdx];
    const vertices = object.vertices.map((point) => {
      const v = new THREE.Vector3(...toVec3(point));
      return mat ? v.applyMatrix4(mat) : v;
    });
    const center = new THREE.Vector3();
    for (const v of vertices) center.add(v);
    if (vertices.length > 0) center.divideScalar(vertices.length);
    object.faces.forEach((face, faceIndex) => {
      const policy = object.surfaces?.find((surface) =>
        surface.surface_id === `${object.id}::face:${faceIndex}`);
      if (policy && (policy.surface_role !== "SOLID_FACE" || !policy.occludes_edges)) return;
      const points = face.map((index) => vertices[index]).filter(Boolean);
      if (points.length < 3) return;
      for (const [ia, ib, ic] of chiaTamGiac(points.map((point) => point.toArray()))) {
        const a = points[ia];
        const b = points[ib];
        const c = points[ic];
        const normal = new THREE.Vector3().subVectors(b, a).cross(new THREE.Vector3().subVectors(c, a));
        if (normal.lengthSq() > 1e-12) {
          normal.normalize();
          if (normal.dot(new THREE.Vector3().subVectors(a, center)) < 0) normal.negate();
        }
        triangles.push({
          surfaceId: policy?.surface_id ?? `${object.id}::face:${faceIndex}`,
          a, b, c,
          normal,
          tri: new THREE.Triangle(a, b, c),
          box: new THREE.Box3().setFromPoints([a, b, c]),
        });
      }
    });
  });
  return triangles;
}

function pointIsHidden(
  point: THREE.Vector3,
  camera: THREE.Vector3,
  triangles: OccludingTriangle[],
  excludedSurfaces: Set<string>,
): boolean {
  const direction = point.clone().sub(camera);
  const edgeDistance = direction.length();
  if (edgeDistance <= 1e-10) return false;
  direction.multiplyScalar(1 / edgeDistance);
  const ray = new THREE.Ray(camera, direction);
  const hit = new THREE.Vector3();
  for (const triangle of triangles) {
    if (excludedSurfaces.has(triangle.surfaceId)) continue;
    // Cheap broad phase before the exact ray/triangle intersection.
    if (!ray.intersectsBox(triangle.box)) continue;
    if (!ray.intersectTriangle(triangle.a, triangle.b, triangle.c, false, hit)) continue;
    const hitDistance = hit.distanceTo(camera);
    const tolerance = Math.max(1e-7, edgeDistance * 1e-7);
    if (hitDistance > tolerance && hitDistance < edgeDistance - tolerance) return true;
  }
  return false;
}

function sampleSegments(projectedPixels: number): number {
  // Sixteen cells are the coarse grid. Uniform refinement closes its blind
  // spots and guarantees a final cell width below half a physical pixel.
  const target = Math.max(16, Math.ceil(Math.max(projectedPixels, 256) / 0.5));
  let cells = 16;
  while (cells < target) cells *= 2;
  return Math.min(cells, 4096);
}

/** World-space ray/triangle classifier. Exactly one class owns each edge. */
export function classifySolidEdgeVisibility(
  o: SceneObject,
  camera: THREE.Vector3,
  options: VisibilityOptions = {},
): EdgeVisibilityAudit {
  const edges = canonicalEdgesOf(o);
  const triangles = occludingTriangles(options.occluders ?? [o]);
  const visible: string[] = [];
  const hidden: string[] = [];
  const mixed: string[] = [];
  const spans: EdgeVisibilitySpan[] = [];
  let sampleCount = 0;
  for (const edge of edges) {
    const pixels = typeof options.projected_edge_pixels === "function"
      ? options.projected_edge_pixels(edge)
      : options.projected_edge_pixels ?? 256;
    const cells = sampleSegments(pixels);
    const excluded = new Set(edge.adjacentSurfaceIds);
    const states: boolean[] = [];
    for (let index = 0; index < cells; index += 1) {
      const t = (index + 0.5) / cells;
      states.push(pointIsHidden(edge.a.clone().lerp(edge.b, t), camera, triangles, excluded));
      sampleCount += 1;
    }
    const hiddenCount = states.filter(Boolean).length;
    if (hiddenCount === 0) visible.push(edge.id);
    else if (hiddenCount === states.length) hidden.push(edge.id);
    else mixed.push(edge.id);
    let start = 0;
    for (let index = 1; index <= states.length; index += 1) {
      if (index < states.length && states[index] === states[start]) continue;
      spans.push({
        edge_id: edge.id,
        t0: start / cells,
        t1: index / cells,
        visibility: states[start] ? "HIDDEN" : "VISIBLE",
      });
      start = index;
    }
  }
  return {
    visible_edge_ids: visible.sort(),
    hidden_edge_ids: hidden.sort(),
    mixed_edge_ids: mixed.sort(),
    duplicate_visual_owner_ids: [],
    edge_spans: spans,
    triangle_count: triangles.length,
    sample_count: sampleCount,
  };
}

/**
 * Classify visibility of an arbitrary world-space segment `[a, b]` (derived `line3`, `segment3`,
 * cross-section boundary edge, or perpendicular witness) against `SOLID_FACE` occluders.
 * Also detects and optionally yields sub-intervals that coincide with canonical solid edges.
 */
export function classifyWorldSegmentVisibility(
  a: THREE.Vector3,
  b: THREE.Vector3,
  camera: THREE.Vector3,
  occluders: readonly WorldSolidOccluder[],
  options: {
    edge_id?: string;
    yield_colinear_canonical_edges?: boolean;
    priority_segments?: readonly { id: string; a: THREE.Vector3; b: THREE.Vector3 }[];
    projected_edge_pixels?: number;
  } = {},
): WorldSegmentVisibilityResult {
  const edgeId = options.edge_id ?? "segment";
  const ab = b.clone().sub(a);
  const len = ab.length();
  if (len <= 1e-9 || (occluders.length === 0 && !options.priority_segments?.length)) {
    return {
      spans: [{ edge_id: edgeId, t0: 0, t1: 1, visibility: "VISIBLE" }],
      colinear_canonical_edge_ids: [],
    };
  }
  const dir = ab.clone().divideScalar(len);
  const colinearTol = 1e-4 * Math.max(1, len);
  const colinearIds: string[] = [];
  let intervals: [number, number][] = [[0, 1]];

  const checkColinear = (segId: string, eA: THREE.Vector3, eB: THREE.Vector3) => {
    const vA = eA.clone().sub(a);
    const vB = eB.clone().sub(a);
    const projA = vA.dot(dir);
    const projB = vB.dot(dir);
    const distA = vA.clone().addScaledVector(dir, -projA).length();
    const distB = vB.clone().addScaledVector(dir, -projB).length();
    if (distA <= colinearTol && distB <= colinearTol) {
      const u0 = Math.max(0, Math.min(projA, projB) / len);
      const u1 = Math.min(1, Math.max(projA, projB) / len);
      if (u1 - u0 > 1e-4) {
        if (!colinearIds.includes(segId)) colinearIds.push(segId);
        if (options.yield_colinear_canonical_edges) {
          intervals = intervals.flatMap(([s0, s1]): [number, number][] => {
            if (u1 <= s0 + 1e-5 || u0 >= s1 - 1e-5) return [[s0, s1]];
            const next: [number, number][] = [];
            if (u0 - s0 > 1e-4) next.push([s0, u0]);
            if (s1 - u1 > 1e-4) next.push([u1, s1]);
            return next;
          });
        }
      }
    }
  };

  for (const occ of occluders) {
    for (const ce of canonicalEdgesOf(occ.solid)) {
      const eA = occ.matrixWorld ? ce.a.clone().applyMatrix4(occ.matrixWorld) : ce.a;
      const eB = occ.matrixWorld ? ce.b.clone().applyMatrix4(occ.matrixWorld) : ce.b;
      checkColinear(ce.id, eA, eB);
    }
  }
  if (options.yield_colinear_canonical_edges && options.priority_segments) {
    for (const ps of options.priority_segments) {
      checkColinear(ps.id, ps.a, ps.b);
    }
  }

  if (intervals.length === 0) {
    return { spans: [], colinear_canonical_edge_ids: colinearIds };
  }
  if (occluders.length === 0) {
    return {
      spans: intervals.map(([t0, t1]) => ({ edge_id: edgeId, t0, t1, visibility: "VISIBLE" as const })),
      colinear_canonical_edge_ids: colinearIds,
    };
  }

  const triangles = occludingTriangles(
    occluders.map((occ) => occ.solid),
    occluders.map((occ) => occ.matrixWorld),
  );
  const onFaceTol = 1e-4 * Math.max(1, len);
  const closestTmp = new THREE.Vector3();

  const sampleHidden = (t: number): boolean => {
    const point = a.clone().lerp(b, t);
    const containingSurfaces = new Set<string>();
    const containingNormals: THREE.Vector3[] = [];
    for (const triangle of triangles) {
      if (triangle.box.distanceToPoint(point) > onFaceTol) continue;
      if (Math.abs(triangle.normal.dot(point.clone().sub(triangle.a))) > onFaceTol) continue;
      if (triangle.tri.closestPointToPoint(point, closestTmp).distanceTo(point) <= onFaceTol) {
        containingSurfaces.add(triangle.surfaceId);
        containingNormals.push(triangle.normal);
      }
    }
    if (pointIsHidden(point, camera, triangles, containingSurfaces)) return true;
    if (containingNormals.length > 0) {
      const toCam = camera.clone().sub(point);
      const anyFrontFacing = containingNormals.some((n) => n.dot(toCam) > 1e-6);
      if (!anyFrontFacing) return true;
    }
    return false;
  };

  const spans: EdgeVisibilitySpan[] = [];
  const basePixels = options.projected_edge_pixels ?? 192;
  for (const [int0, int1] of intervals) {
    const spanLen = int1 - int0;
    const cells = Math.max(16, Math.min(128, sampleSegments(basePixels * spanLen)));
    const states: boolean[] = [];
    for (let i = 0; i < cells; i += 1) {
      const t = int0 + ((i + 0.5) / cells) * spanLen;
      states.push(sampleHidden(t));
    }
    let start = 0;
    for (let i = 1; i <= states.length; i += 1) {
      if (i < states.length && states[i] === states[start]) continue;
      spans.push({
        edge_id: edgeId,
        t0: int0 + (start / cells) * spanLen,
        t1: int0 + (i / cells) * spanLen,
        visibility: states[start] ? "HIDDEN" : "VISIBLE",
      });
      start = i;
    }
  }
  return { spans, colinear_canonical_edge_ids: colinearIds };
}

