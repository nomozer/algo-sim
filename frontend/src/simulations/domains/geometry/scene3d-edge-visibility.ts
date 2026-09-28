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
  box: THREE.Box3;
}

function occludingTriangles(objects: SceneObject[]): OccludingTriangle[] {
  const triangles: OccludingTriangle[] = [];
  for (const object of objects) {
    if (object.type !== "solid" || !object.vertices || !object.faces) continue;
    const vertices = object.vertices.map((point) => new THREE.Vector3(...toVec3(point)));
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
        triangles.push({
          surfaceId: policy?.surface_id ?? `${object.id}::face:${faceIndex}`,
          a, b, c,
          box: new THREE.Box3().setFromPoints([a, b, c]),
        });
      }
    });
  }
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
