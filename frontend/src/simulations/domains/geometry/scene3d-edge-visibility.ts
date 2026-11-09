/** Camera-relative edge visibility. Presentation-only; never feeds geometry state. */
import * as THREE from "three";
import { Line2 } from "three/addons/lines/Line2.js";
import { LineGeometry } from "three/addons/lines/LineGeometry.js";
import { LineMaterial } from "three/addons/lines/LineMaterial.js";
import { LineSegments2 } from "three/addons/lines/LineSegments2.js";
import { LineSegmentsGeometry } from "three/addons/lines/LineSegmentsGeometry.js";
import { chiaTamGiac } from "./polygon-triangulate";
import { toVec3, type SceneObject } from "./scene3d-model";
import { PHONG_CACH_SCENE3D } from "./scene3d-roles";

/** Hệ số độ dày nét theo chiều cao khung (CSS px): hình luôn lấp ~78% khung, nên nét tỉ lệ với khung giữ đúng tỉ lệ
 *  nét/hình như nét world-space của HTML tham chiếu; kẹp để nét không mất trên khung nhỏ, không thô trên khung lớn. */
export function heSoNetTheoKhung(hCss: number): number {
  const w = PHONG_CACH_SCENE3D.fatPx;
  return Math.min(w.maxScale, Math.max(w.minScale, hCss / w.referenceCanvasHeight));
}

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
    if ((options.occluders?.length ?? 1) > 1) {
      for (const tri of triangles) {
        if (excluded.has(tri.surfaceId)) continue;
        const da = Math.abs(tri.normal.dot(new THREE.Vector3().subVectors(edge.a, tri.a)));
        const db = Math.abs(tri.normal.dot(new THREE.Vector3().subVectors(edge.b, tri.a)));
        if (da <= 1e-4 && db <= 1e-4) {
          excluded.add(tri.surfaceId);
        }
      }
    }
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
    curved_occluders?: readonly CurvedSolidVolumeMeta[];
  } = {},
): WorldSegmentVisibilityResult {
  const edgeId = options.edge_id ?? "segment";
  const ab = b.clone().sub(a);
  const len = ab.length();
  const curved = options.curved_occluders ?? [];
  if (occluders.length === 0 && curved.length === 0 && !options.priority_segments?.length) {
    return {
      spans: [{ edge_id: edgeId, t0: 0, t1: 1, visibility: "VISIBLE" }],
      colinear_canonical_edge_ids: [],
    };
  }
  if (len <= 1e-9) {
    const triangles = occludingTriangles(occluders.map(o => o.solid), occluders.map(o => o.matrixWorld));
    const hidden = pointIsHidden(a, camera, triangles, new Set()) || diemVanhCongBiChe(a, camera, curved);
    return { spans: [{ edge_id: edgeId, t0: 0, t1: 1, visibility: hidden ? "HIDDEN" : "VISIBLE" }], colinear_canonical_edge_ids: [] };
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
  if (occluders.length === 0 && curved.length === 0) {
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
    if (diemVanhCongBiChe(point, camera, curved)) return true;
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

export interface CurvedSolidVolumeMeta {
  id: string;
  kind: "cylinder" | "cone" | "ball";
  anchor: THREE.Vector3;
  top: THREE.Vector3 | null;
  radius: number;
  height: number;
  /** Orthonormal basis `(u1, u2)` in the base plane when an oblique cylinder's base normal is non-parallel to `top - anchor`. */
  capBasis?: [THREE.Vector3, THREE.Vector3];
  /** Inverse presentation transform; intersections stay in the primitive's original local frame. */
  worldToLocal?: THREE.Matrix4;
}

export function resolveObliqueCylinderCapBasis(
  anchor: THREE.Vector3,
  top: THREE.Vector3,
  rawCapNormal: THREE.Vector3 | null,
): { u1: THREE.Vector3; u2: THREE.Vector3; normal: THREE.Vector3 } | null {
  if (!rawCapNormal) return null;
  const d = top.clone().sub(anchor);
  const dLen = d.length();
  const nLen = rawCapNormal.length();
  if (!(dLen > 1e-6) || !(nLen > 1e-6)) return null;
  const dHat = d.clone().divideScalar(dLen);
  const nHat = rawCapNormal.clone().divideScalar(nLen);
  if (nHat.dot(dHat) < 0) nHat.negate();
  const crossMag = new THREE.Vector3().crossVectors(dHat, nHat).length();
  // Right cylinder: cap normal is parallel to center-line => keep standard CylinderGeometry path.
  if (crossMag <= 1e-4 || Math.abs(nHat.dot(dHat)) <= 1e-4) return null;
  let u1 = dHat.clone().addScaledVector(nHat, -dHat.dot(nHat));
  if (u1.lengthSq() <= 1e-10) {
    const fallback = Math.abs(nHat.x) < 0.9 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 1, 0);
    u1 = new THREE.Vector3().crossVectors(nHat, fallback);
  }
  u1.normalize();
  const u2 = new THREE.Vector3().crossVectors(nHat, u1).normalize();
  return { u1, u2, normal: nHat };
}

export function buildObliqueCylinderGeometry(
  anchor: THREE.Vector3,
  top: THREE.Vector3,
  u1: THREE.Vector3,
  u2: THREE.Vector3,
  radius: number,
  radialSegments: number,
): THREE.BufferGeometry {
  const segs = Math.max(16, radialSegments);
  const positions: number[] = [];
  const normals: number[] = [];
  const indices: number[] = [];
  const d = top.clone().sub(anchor);
  const capN = new THREE.Vector3().crossVectors(u1, u2).normalize();
  if (capN.dot(d) < 0) capN.negate();

  // 1. Lateral sheared surface (2 * (segs + 1) vertices)
  for (let i = 0; i <= segs; i += 1) {
    const theta = (i / segs) * Math.PI * 2;
    const c = Math.cos(theta);
    const s = Math.sin(theta);
    const offset = u1.clone().multiplyScalar(radius * c).addScaledVector(u2, radius * s);
    const tangent = u1.clone().multiplyScalar(-s).addScaledVector(u2, c);
    const outN = new THREE.Vector3().crossVectors(tangent, d).normalize();
    const pBot = anchor.clone().add(offset);
    const pTop = top.clone().add(offset);
    positions.push(pBot.x, pBot.y, pBot.z, pTop.x, pTop.y, pTop.z);
    normals.push(outN.x, outN.y, outN.z, outN.x, outN.y, outN.z);
  }
  for (let i = 0; i < segs; i += 1) {
    const b0 = i * 2;
    const t0 = b0 + 1;
    const b1 = b0 + 2;
    const t1 = b0 + 3;
    indices.push(b0, b1, t1, b0, t1, t0);
  }

  // 2. Bottom cap (outward normal -capN)
  const botCenterIdx = positions.length / 3;
  positions.push(anchor.x, anchor.y, anchor.z);
  normals.push(-capN.x, -capN.y, -capN.z);
  for (let i = 0; i <= segs; i += 1) {
    const theta = (i / segs) * Math.PI * 2;
    const p = anchor.clone()
      .addScaledVector(u1, radius * Math.cos(theta))
      .addScaledVector(u2, radius * Math.sin(theta));
    positions.push(p.x, p.y, p.z);
    normals.push(-capN.x, -capN.y, -capN.z);
  }
  for (let i = 0; i < segs; i += 1) {
    indices.push(botCenterIdx, botCenterIdx + 1 + i + 1, botCenterIdx + 1 + i);
  }

  // 3. Top cap (outward normal +capN)
  const topCenterIdx = positions.length / 3;
  positions.push(top.x, top.y, top.z);
  normals.push(capN.x, capN.y, capN.z);
  for (let i = 0; i <= segs; i += 1) {
    const theta = (i / segs) * Math.PI * 2;
    const p = top.clone()
      .addScaledVector(u1, radius * Math.cos(theta))
      .addScaledVector(u2, radius * Math.sin(theta));
    positions.push(p.x, p.y, p.z);
    normals.push(capN.x, capN.y, capN.z);
  }
  for (let i = 0; i < segs; i += 1) {
    indices.push(topCenterIdx, topCenterIdx + 1 + i, topCenterIdx + 1 + i + 1);
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
  geo.setIndex(indices);
  geo.computeBoundingBox();
  geo.computeBoundingSphere();
  return geo;
}

/** Compile occluders once when sampling a true 3D curve, rather than rebuilding triangles per point. */
export function createWorldPointOcclusionTest(
  camera: THREE.Vector3,
  occluders: readonly WorldSolidOccluder[],
  curved: readonly CurvedSolidVolumeMeta[],
): (point: THREE.Vector3, curveNormal?: THREE.Vector3, checkHostBackface?: boolean) => boolean {
  const triangles = occludingTriangles(occluders.map(o => o.solid), occluders.map(o => o.matrixWorld));
  const emptyExcluded = new Set<string>();
  const closestTmp = new THREE.Vector3();
  const diffTmp = new THREE.Vector3();
  const toCamTmp = new THREE.Vector3();
  return (point: THREE.Vector3, curveNormal?: THREE.Vector3, checkHostBackface = true) => {
    if (curveNormal) {
      const excluded = new Set<string>();
      const containingNormals: THREE.Vector3[] = [];
      for (const triangle of triangles) {
        if (Math.abs(triangle.normal.dot(curveNormal)) < 0.999) continue;
        if (triangle.box.distanceToPoint(point) > 1e-4) continue;
        if (Math.abs(triangle.normal.dot(diffTmp.subVectors(point, triangle.a))) > 1e-4) continue;
        if (triangle.tri.closestPointToPoint(point, closestTmp).distanceTo(point) <= 1e-4) {
          excluded.add(triangle.surfaceId);
          containingNormals.push(triangle.normal);
        }
      }
      if (pointIsHidden(point, camera, triangles, excluded)) return true;
      if (diemVanhCongBiChe(point, camera, curved)) return true;
      if (checkHostBackface && containingNormals.length > 0) {
        toCamTmp.subVectors(camera, point);
        if (!containingNormals.some((n) => n.dot(toCamTmp) > 1e-6)) return true;
      }
      return false;
    }
    return pointIsHidden(point, camera, triangles, emptyExcluded) || diemVanhCongBiChe(point, camera, curved);
  };
}

/** Host-quadric tangencies seed even arbitrarily short front arcs between uniform probes. */
export function curvedSurfaceTangentTurns(
  sampleWorld: (turn: number) => THREE.Vector3,
  camera: THREE.Vector3,
  volumes: readonly CurvedSolidVolumeMeta[],
): number[] {
  const turns: number[] = [];
  for (const volume of volumes) {
    const points = Array.from({ length: 8 }, (_, i) => {
      const point = sampleWorld(i / 8);
      return volume.worldToLocal ? point.applyMatrix4(volume.worldToLocal) : point;
    });
    const eye = volume.worldToLocal ? camera.clone().applyMatrix4(volume.worldToLocal) : camera;
    const axis = volume.top?.clone().sub(volume.anchor).normalize();
    const values: number[] = [];
    const obBasis = volume.kind === "cylinder" && volume.top && volume.capBasis ? volume.capBasis : null;
    const obD = obBasis && volume.top ? volume.top.clone().sub(volume.anchor) : null;
    const obN = obBasis ? new THREE.Vector3().crossVectors(obBasis[0], obBasis[1]) : null;
    const obDenom = obD && obN ? obN.dot(obD) : 0;
    for (const point of points) {
      const relative = point.clone().sub(volume.anchor), direction = eye.clone().sub(point);
      const normal = relative.clone();
      let residual: number;
      if (volume.kind === "ball") {
        residual = relative.lengthSq() - volume.radius ** 2;
      } else if (obBasis && obD && obN && Math.abs(obDenom) > 1e-8) {
        const s = relative.dot(obN) / obDenom;
        if (s < -1e-6 || s > 1 + 1e-6) break;
        const inCap = relative.clone().addScaledVector(obD, -s);
        const cx = inCap.dot(obBasis[0]);
        const cy = inCap.dot(obBasis[1]);
        residual = cx * cx + cy * cy - volume.radius ** 2;
        const tangent = obBasis[0].clone().multiplyScalar(-cy).addScaledVector(obBasis[1], cx);
        normal.crossVectors(tangent, obD);
        if (obDenom < 0) normal.negate();
      } else {
        if (!axis || volume.height <= 0) break;
        const z = relative.dot(axis);
        if (z < -1e-8 || z > volume.height + 1e-8) break;
        normal.addScaledVector(axis, -z);
        const fraction = volume.kind === "cone" ? 1 - z / volume.height : 1;
        residual = normal.lengthSq() - (volume.radius * fraction) ** 2;
        if (volume.kind === "cone") normal.addScaledVector(axis, volume.radius ** 2 * fraction / volume.height);
      }
      if (Math.abs(residual) > 1e-6 * Math.max(1, volume.radius ** 2)) break;
      values.push(normal.dot(direction));
    }
    if (values.length !== 8) continue; // not a curve on this solid's side surface
    const a = (values[0] - values[4]) / 2, b = (values[2] - values[6]) / 2;
    const c = (values[0] + values[4]) / 2, radius = Math.hypot(a, b);
    if (radius <= 1e-14 || Math.abs(c) > radius) continue;
    const phi = Math.atan2(b, a), alpha = Math.acos(Math.max(-1, Math.min(1, -c / radius)));
    for (const angle of [phi - alpha, phi + alpha]) turns.push(((angle / (2 * Math.PI)) % 1 + 1) % 1);
  }
  return turns;
}

export function diemVanhCongBiChe(
  pt: THREE.Vector3,
  worldCam: THREE.Vector3,
  volumes: readonly CurvedSolidVolumeMeta[],
): boolean {
  // Parameterise from the boundary toward the eye; no fixed fraction of the ray may be discarded.
  for (const vol of volumes) {
    const point = vol.worldToLocal ? pt.clone().applyMatrix4(vol.worldToLocal) : pt;
    const eye = vol.worldToLocal ? worldCam.clone().applyMatrix4(vol.worldToLocal) : worldCam;
    const dir = eye.clone().sub(point);
    if (dir.lengthSq() < 1e-12) continue;
    const r = vol.radius;
    if (r <= 1e-6) continue;
    if (vol.kind === "ball") {
      const rel = point.clone().sub(vol.anchor);
      const t = Math.max(0, Math.min(1, -rel.dot(dir) / dir.lengthSq()));
      const c0 = rel.lengthSq() - r * r;
      const onBallBias = c0 < 0 && c0 > -r * r * 2e-6 ? c0 : 0;
      if (rel.addScaledVector(dir, t).lengthSq() - r * r - onBallBias < -r * r * 1e-10) return true;
      continue;
    }
    const h = vol.height;
    if (!vol.top || h <= 1e-6) continue;
    if (vol.kind === "cylinder" && vol.capBasis) {
      const [u1, u2] = vol.capBasis;
      const dVec = new THREE.Vector3().subVectors(vol.top, vol.anchor);
      const capN = new THREE.Vector3().crossVectors(u1, u2);
      const denom = capN.dot(dVec);
      if (Math.abs(denom) > 1e-8) {
        const ptRel = new THREE.Vector3().subVectors(point, vol.anchor);
        const s0 = ptRel.dot(capN) / denom;
        const ds = dir.dot(capN) / denom;
        let tLo = 0;
        let tHi = 1;
        if (Math.abs(ds) < 1e-12) {
          if (s0 <= 0 || s0 >= 1) continue;
        } else {
          const t0 = -s0 / ds;
          const t1 = (1 - s0) / ds;
          tLo = Math.max(tLo, Math.min(t0, t1));
          tHi = Math.min(tHi, Math.max(t0, t1));
        }
        if (tLo >= tHi) continue;
        const pCap = ptRel.clone().addScaledVector(dVec, -s0);
        const dCap = dir.clone().addScaledVector(dVec, -ds);
        const px = pCap.dot(u1), py = pCap.dot(u2);
        const dx = dCap.dot(u1), dy = dCap.dot(u2);
        const qa = dx * dx + dy * dy;
        const qb = 2 * (px * dx + py * dy);
        const at = (t: number) => (px + dx * t) ** 2 + (py + dy * t) ** 2 - r * r;
        let minimum = Math.min(at(tLo), at(tHi));
        if (qa > 0) minimum = Math.min(minimum, at(Math.max(tLo, Math.min(tHi, -qb / (2 * qa)))));
        const onCylBias = tLo === 0 && at(0) < 0 && at(0) > -r * r * 2e-6 ? at(0) : 0;
        if (minimum - onCylBias < -r * r * 1e-9) return true;
        continue;
      }
    }
    const axis = new THREE.Vector3().subVectors(vol.top, vol.anchor).normalize();
    const ptRel = new THREE.Vector3().subVectors(point, vol.anchor);
    const zPt = ptRel.dot(axis);
    const dz = dir.dot(axis);
    let tLo = 0;
    let tHi = 1;
    if (Math.abs(dz) < h * 1e-12) {
      if (zPt <= 0 || zPt >= h) continue;
    } else {
      const t0 = -zPt / dz;
      const t1 = (h - zPt) / dz;
      tLo = Math.max(tLo, Math.min(t0, t1));
      tHi = Math.min(tHi, Math.max(t0, t1));
    }
    if (tLo >= tHi) continue;
    const ptPerp = ptRel.clone().addScaledVector(axis, -zPt);
    const dPerp = dir.clone().addScaledVector(axis, -dz);
    const r0 = vol.kind === "cone" ? r * (1 - zPt / h) : r;
    const dr = vol.kind === "cone" ? -r * dz / h : 0;
    // Minimise the radial quadratic on the axial interval; a cone's radius changes along the ray.
    const qa = dPerp.lengthSq() - dr * dr;
    const qb = 2 * (ptPerp.dot(dPerp) - r0 * dr);
    const at = (t: number) => ptPerp.clone().addScaledVector(dPerp, t).lengthSq() - (r0 + dr * t) ** 2;
    let minimum = Math.min(at(tLo), at(tHi));
    if (qa > 0) minimum = Math.min(minimum, at(Math.max(tLo, Math.min(tHi, -qb / (2 * qa)))));
    const onConeBias = tLo === 0 && at(0) < 0 && at(0) > -r * r * 2e-6 ? at(0) : 0;
    if (minimum - onConeBias < -r * r * 1e-10) return true;
  }
  return false;
}

/** Camera tangent contours of certified primitives. Presentation only; never creates backend facts or entities. */
export function updateCurvedSolidSilhouette(candidate: THREE.Object3D, camera: THREE.Camera): void {
  // `curvedSilhouetteVolume`: a curved solid shown but not used as an occluder (see `datKhoiCongKhongChe`).
  const meta = (candidate.userData.curvedSolidVolume ?? candidate.userData.curvedSilhouetteVolume) as CurvedSolidVolumeMeta | undefined;
  if (!meta) return;
  const eye = candidate.worldToLocal(camera.position.clone());
  const { anchor, top, radius: r, height: h, kind } = meta;
  if (kind === "ball") {
    return;
  } else if (top && h > 0) {
    const outline = candidate.getObjectByName(`curved_silhouette:${meta.id}`);
    if (!outline) return;
    if (kind === "cylinder" && meta.capBasis) {
      const [u1, u2] = meta.capBasis;
      const dVec = top.clone().sub(anchor);
      const rel = eye.clone().sub(anchor);
      const capCross = new THREE.Vector3().crossVectors(u1, u2);
      const sign = capCross.dot(dVec) < 0 ? -1 : 1;
      const A = sign * new THREE.Vector3().crossVectors(u2, dVec).dot(rel);
      const B = -sign * new THREE.Vector3().crossVectors(u1, dVec).dot(rel);
      const C = sign * r * capCross.dot(dVec);
      const rho = Math.hypot(A, B);
      outline.visible = rho > Math.abs(C) + 1e-8;
      if (outline.visible) {
        const phi = Math.atan2(B, A);
        const alpha = Math.acos(Math.max(-1, Math.min(1, C / rho)));
        outline.children.forEach((child, i) => {
          const theta = phi + (i ? -alpha : alpha);
          const offset = u1.clone().multiplyScalar(r * Math.cos(theta)).addScaledVector(u2, r * Math.sin(theta));
          const a = anchor.clone().add(offset);
          const b = top.clone().add(offset);
          const pos = (child as THREE.Line).geometry.getAttribute("position") as THREE.BufferAttribute;
          pos.setXYZ(0, a.x, a.y, a.z); pos.setXYZ(1, b.x, b.y, b.z); pos.needsUpdate = true;
          (child as THREE.Line).geometry.computeBoundingSphere();
        });
      }
      return;
    }
    const axis = top.clone().sub(anchor).normalize(), relative = eye.clone().sub(anchor);
    const axial = relative.dot(axis), radial = relative.addScaledVector(axis, -axial);
    const distance = radial.length(), cosine = distance > 0 ? r * (kind === "cone" ? 1 - axial / h : 1) / distance : Infinity;
    outline.visible = Math.abs(cosine) < 1;
    if (outline.visible) {
      radial.divideScalar(distance);
      const across = new THREE.Vector3().crossVectors(axis, radial);
      outline.children.forEach((child, i) => {
        const u = radial.clone().multiplyScalar(cosine).addScaledVector(across, (i ? -1 : 1) * Math.sqrt(1 - cosine * cosine));
        const a = anchor.clone().addScaledVector(u, r);
        const b = kind === "cone" ? top : top.clone().addScaledVector(u, r);
        const pos = (child as THREE.Line).geometry.getAttribute("position") as THREE.BufferAttribute;
        pos.setXYZ(0, a.x, a.y, a.z); pos.setXYZ(1, b.x, b.y, b.z); pos.needsUpdate = true;
        (child as THREE.Line).geometry.computeBoundingSphere();
      });
    }
  }
}

export interface FatLineSyncSummary {
  totalLines: number;
  maxSectionBorderWidth: number;
  maxVisibleEdgeWidth: number;
  minHiddenEdgeWidth: number;
  sourceLines: THREE.Line[];
  sourceRimObjects: THREE.Object3D[];
}

export function taoGiuAmNetDay(): THREE.Object3D[] {
  const geo = new LineGeometry();
  geo.setPositions([0, 0, 0, 1, 0, 0]);
  const solidMat = new LineMaterial({
    color: 0x1e293b,
    linewidth: 1.8,
    dashed: false,
    transparent: true,
    opacity: 0,
    depthTest: false,
    depthWrite: false,
  });
  solidMat.colorWrite = false;
  const dashedMat = new LineMaterial({
    color: 0x475569,
    linewidth: 1.25,
    dashed: true,
    dashSize: 0.1,
    gapSize: 0.1,
    transparent: true,
    opacity: 0,
    depthTest: false,
    depthWrite: false,
  });
  dashedMat.colorWrite = false;
  const solidHold = new Line2(geo, solidMat);
  const dashedHold = new Line2(geo, dashedMat);
  solidHold.computeLineDistances();
  dashedHold.computeLineDistances();
  solidHold.frustumCulled = false;
  dashedHold.frustumCulled = false;
  solidHold.raycast = () => {};
  dashedHold.raycast = () => {};
  const segGeo = new LineSegmentsGeometry();
  segGeo.setPositions([0, 0, 0, 1, 0, 0]);
  const segMat = new LineMaterial({
    color: 0x1e293b,
    linewidth: 1.8,
    dashed: false,
    transparent: true,
    opacity: 0,
    depthTest: false,
    depthWrite: false,
  });
  segMat.colorWrite = false;
  const segHold = new LineSegments2(segGeo, segMat);
  segHold.frustumCulled = false;
  segHold.raycast = () => {};
  return [solidHold, dashedHold, segHold];
}

/**
 * Ghi toạ độ polyline mới VÀO CHÍNH các buffer instanced sẵn có của một `Line2` cùng số điểm (đoạn + khoảng cách nét
 * đứt), thay vì `setPositions`/`computeLineDistances` — hai hàm ấy tạo `InstancedInterleavedBuffer` mới mỗi lần, tức
 * một buffer GPU mới mỗi khi một span đổi lúc xoay (cổng `scene3d-orbit-gate`, `capPhat = 0`). `false` ⇒ chưa có
 * buffer hợp cỡ, người gọi dựng lại như cũ.
 */
function capNhatLine2TaiCho(line2: Line2, coords: Float32Array): boolean {
  const g = line2.geometry as LineGeometry;
  const start = g.attributes.instanceStart as THREE.InterleavedBufferAttribute | undefined;
  const dist = g.attributes.instanceDistanceStart as THREE.InterleavedBufferAttribute | undefined;
  const doan = coords.length / 3 - 1;
  if (!start || !dist || doan < 1 || start.data.array.length !== doan * 6 || dist.data.array.length !== doan * 2) {
    return false;
  }
  const seg = start.data.array as Float32Array;
  const d = dist.data.array as Float32Array;
  let tong = 0;
  for (let i = 0; i < doan; i += 1) {
    for (let k = 0; k < 6; k += 1) seg[i * 6 + k] = coords[i * 3 + k];
    const dai = Math.hypot(coords[i * 3 + 3] - coords[i * 3], coords[i * 3 + 4] - coords[i * 3 + 1],
      coords[i * 3 + 5] - coords[i * 3 + 2]);
    d[i * 2] = tong;
    tong += dai;
    d[i * 2 + 1] = tong;
  }
  start.data.needsUpdate = true;
  dist.data.needsUpdate = true;
  g.computeBoundingBox();
  g.computeBoundingSphere();
  return true;
}

function capNhatLineSegments2TaiCho(
  seg2: LineSegments2,
  coords: Float32Array,
  segCount: number,
): boolean {
  const g = seg2.geometry as LineSegmentsGeometry;
  const start = g.attributes.instanceStart as THREE.InterleavedBufferAttribute | undefined;
  const needed = segCount * 6;
  if (!start || segCount < 1 || start.data.array.length < needed) {
    return false;
  }
  const dst = start.data.array as Float32Array;
  dst.set(coords.subarray(0, needed), 0);
  g.instanceCount = segCount;
  start.data.needsUpdate = true;
  return true;
}

interface CurvedRimLike {
  objectId: string;
  rimRole?: "section" | "base" | "reference" | "inscribed" | "circumscribed";
  highlighted?: boolean;
  interactionState?: "neutral" | "hover" | "selected";
  thayMesh: THREE.Mesh;
  khuatMesh: THREE.Mesh;
  thayNet: THREE.LineSegments;
  khuatNet: THREE.LineSegments;
}

export function dongBoNetDayManHinh(
  roots: readonly THREE.Object3D[],
  fatGroup: THREE.Group,
  wCss: number,
  hCss: number,
  dashedHiddenShown = true,
  stepPulse = 0,
  zoomDashScale = 1,
): FatLineSyncSummary {
  const clampedPulse = Number.isFinite(stepPulse) ? Math.max(0, Math.min(1, stepPulse)) : 0;
  const resolveStepRole = (n: THREE.Object3D | null | undefined): "new" | "dep" | undefined => {
    for (let cur = n; cur; cur = cur.parent) {
      const r = cur.userData?.stepHighlightRole as "new" | "dep" | undefined;
      if (r === "new" || r === "dep") return r;
    }
    return undefined;
  };
  const activeLines: THREE.Line[] = [];
  const activeRims: { node: THREE.Object3D; rim: CurvedRimLike }[] = [];
  const sourceRimObjects: THREE.Object3D[] = [];
  for (const r of roots) {
    r.updateMatrixWorld(true);
    r.traverse((node) => {
      for (let p: THREE.Object3D | null = node; p; p = p.parent) {
        if (!p.visible) return;
        if (p === r) break;
      }
      const rim = node.userData?.curvedRimLoop as CurvedRimLike | undefined;
      if (rim?.thayNet && rim?.khuatNet && rim?.thayMesh && rim?.khuatMesh) {
        activeRims.push({ node, rim });
        return;
      }
      if (!(node as THREE.Line).isLine || (node as THREE.LineSegments).isLineSegments) return;
      const line = node as THREE.Line;
      const mat = line.material as (THREE.LineBasicMaterial | THREE.LineDashedMaterial) | undefined;
      if (!mat || mat.colorWrite === false || (mat.transparent && mat.opacity <= 0.01) || line.name.endsWith(":proxy")) {
        return;
      }
      const pos = line.geometry?.getAttribute?.("position") as THREE.BufferAttribute | undefined;
      if (!pos || pos.count < 2) return;
      activeLines.push(line);
    });
  }

  // Pool THEO SỐ ĐIỂM: khi tập span đổi lúc xoay, một bản sao chỉ nhận nét cùng số điểm, nên buffer của nó được ghi
  // tại chỗ (`capNhatLine2TaiCho`) thay vì dựng lại; chỉ khi một nhóm phải lớn thêm mới cấp phát.
  const pools: Map<number, Line2[]> = (fatGroup.userData.pools as Map<number, Line2[]> | undefined) ?? new Map();
  fatGroup.userData.pools = pools;
  const daDung = new Map<number, number>();
  const tmp = new THREE.Vector3();
  const resW = Math.max(1, wCss);
  const resH = Math.max(1, hCss);
  const heSoNet = heSoNetTheoKhung(hCss);
  const w = PHONG_CACH_SCENE3D.fatPx;
  let maxSectionBorderWidth = 0;
  let maxVisibleEdgeWidth = 0;
  let minHiddenEdgeWidth = Infinity;

  activeLines.forEach((line) => {
    const mat = line.material as THREE.LineBasicMaterial | THREE.LineDashedMaterial;
    const pos = line.geometry.getAttribute("position") as THREE.BufferAttribute;
    const continuousPlaneBorder = Boolean(
      line.userData?.continuousPlaneBorder
      || line.parent?.userData?.nonCanonicalLoop?.continuousPlaneBorder,
    );
    const isDashed =
      !continuousPlaneBorder
      && (
        line.userData?.hidden === true
        || (mat as THREE.LineDashedMaterial).isLineDashedMaterial === true
        || line.name.endsWith(":khuat")
      );
    const isUnoccludedForcedDash = Boolean(line.userData?.forceDashed === true && line.userData?.hidden !== true);
    if (!dashedHiddenShown && isDashed && !isUnoccludedForcedDash) {
      return;
    }
    const isPlaneBorder =
      Boolean(line.parent?.userData?.nonCanonicalLoop?.isPlaneBorder)
      || line.name.startsWith("plane_border:");
    const isPlaneCornerArc = line.name.startsWith("plane_corner_arc:");
    const isLineExtension = Boolean(
      line.userData?.semanticLineRole === "line_extension"
      || line.parent?.userData?.semanticLineRole === "line_extension",
    );
    const isAuxiliaryLine = Boolean(
      line.userData?.semanticLineRole === "auxiliary_line"
      || line.parent?.userData?.semanticLineRole === "auxiliary_line",
    );
    const isSolidEdgeRole = Boolean(
      line.userData?.semanticLineRole === "solid_edge"
      || line.parent?.userData?.semanticLineRole === "solid_edge",
    );
    const isIntersectionLine = Boolean(
      line.userData?.semanticLineRole === "intersection_line"
      || line.parent?.userData?.semanticLineRole === "intersection_line",
    );
    const isSectionOrPolyBorder =
      !isPlaneBorder
      && !isPlaneCornerArc
      && !isLineExtension
      && !isAuxiliaryLine
      && !isSolidEdgeRole
      && (isIntersectionLine || line.name.startsWith("section_border:") || line.name.startsWith("polygon_border:"));
    const isPerpOrWitness =
      line.name.startsWith("perp_marker")
      || Boolean(line.parent?.userData?.nhanChung)
      || Boolean(
        line.userData?.semanticLineRole === "perpendicular_witness"
        || line.parent?.userData?.semanticLineRole === "perpendicular_witness",
      );
    const interactionState = (
      line.userData?.interactionState
      ?? line.parent?.userData?.interactionState
      ?? (
        line.userData?.sang
        || line.parent?.userData?.highlighted
        || (mat.linewidth && mat.linewidth >= 2.6)
          ? "selected"
          : "neutral"
      )
    ) as "neutral" | "hover" | "selected";

    const raw = isPlaneCornerArc
      ? (interactionState === "selected" ? 2.0 : 1.55)
      : isPlaneBorder
        ? (interactionState === "selected"
          ? w.selectedPlane
          : interactionState === "hover"
            ? w.hoverPlane
            : w.plane * ((line.parent?.userData?.planeBorderWidthScale as number | undefined) ?? 1))
        : isLineExtension
          ? (interactionState === "selected" ? 2.8 : interactionState === "hover" ? 2.4 : 2.0)
          : isSectionOrPolyBorder
            ? (interactionState === "selected"
              ? w.selectedSection
              : interactionState === "hover"
                ? w.hoverSection
                : isDashed
                  ? w.hiddenSection
                  : w.section)
            : isPerpOrWitness
              ? (interactionState === "selected"
                ? w.selectedEdge * 0.85
                : isDashed
                  ? w.hiddenPerpendicular
                  : w.perpendicular)
              : isAuxiliaryLine
                  ? (interactionState === "selected"
                    ? w.selectedEdge
                    : interactionState === "hover"
                      ? w.hoverEdge
                      : isDashed
                        ? w.hiddenAuxiliary
                        : w.auxiliary)
                  : (interactionState === "selected"
                    ? w.selectedEdge
                    : interactionState === "hover"
                      ? w.hoverEdge
                      : isDashed
                        ? w.hiddenEdge
                        : w.edge);
    const lineStepRole = clampedPulse > 0.005 && interactionState === "neutral" ? resolveStepRole(line) : undefined;
    const lineStepBoost = lineStepRole === "new"
      ? 1 + 0.24 * clampedPulse
      : lineStepRole === "dep"
        ? 1 + 0.11 * clampedPulse
        : 1;
    const widthPx = Number((raw * lineStepBoost * heSoNet).toFixed(2));

    if (isSectionOrPolyBorder && !isDashed) {
      maxSectionBorderWidth = Math.max(maxSectionBorderWidth, widthPx);
    } else if (!isPlaneBorder && !isPerpOrWitness && !isAuxiliaryLine && !isDashed) {
      maxVisibleEdgeWidth = Math.max(maxVisibleEdgeWidth, widthPx);
    }
    if (isDashed) {
      minHiddenEdgeWidth = Math.min(minHiddenEdgeWidth, widthPx);
    }

    const nhom = pools.get(pos.count) ?? [];
    pools.set(pos.count, nhom);
    const thu = daDung.get(pos.count) ?? 0;
    daDung.set(pos.count, thu + 1);
    let line2 = nhom[thu];
    if (!line2) {
      const g = new LineGeometry();
      g.setPositions([0, 0, 0, 1, 0, 0]);
      const m = new LineMaterial({
        color: 0x1e293b,
        linewidth: widthPx,
        dashed: false,
        transparent: true,
        opacity: 1,
        depthTest: false,
        depthWrite: false,
      });
      line2 = new Line2(g, m);
      line2.frustumCulled = false;
      line2.raycast = () => {};
      line2.userData.voHan = true;
      line2.userData.fatLineCompanion = true;
      nhom.push(line2);
      fatGroup.add(line2);
    }

    const nCoords = pos.count * 3;
    let coords = line2.userData.coordsCache as Float32Array | undefined;
    let changed = !coords || coords.length !== nCoords;
    if (!coords || coords.length !== nCoords) {
      coords = new Float32Array(nCoords);
      line2.userData.coordsCache = coords;
    }
    for (let i = 0; i < pos.count; i += 1) {
      tmp.fromBufferAttribute(pos, i).applyMatrix4(line.matrixWorld);
      const base = i * 3;
      if (
        !changed
        && (Math.abs(coords[base] - tmp.x) > 1e-6
          || Math.abs(coords[base + 1] - tmp.y) > 1e-6
          || Math.abs(coords[base + 2] - tmp.z) > 1e-6)
      ) {
        changed = true;
      }
      coords[base] = tmp.x;
      coords[base + 1] = tmp.y;
      coords[base + 2] = tmp.z;
    }

    if (changed) {
      if (line2.userData.pointCount !== pos.count || !capNhatLine2TaiCho(line2, coords)) {
        line2.geometry?.dispose?.();
        line2.geometry = new LineGeometry();
        line2.userData.pointCount = pos.count;
        line2.geometry.setPositions(coords);
        line2.computeLineDistances();
      }
    }

    const lm = line2.material as LineMaterial;
    lm.color.copy(mat.color);
    lm.linewidth = widthPx;
    lm.resolution.set(resW, resH);
    lm.transparent = true;
    lm.opacity = mat.opacity ?? 1;
    lm.depthTest = mat.depthTest;
    lm.depthWrite = false;
    lm.depthFunc = mat.depthFunc;
    lm.polygonOffset = mat.polygonOffset;
    lm.polygonOffsetFactor = mat.polygonOffsetFactor;
    lm.polygonOffsetUnits = mat.polygonOffsetUnits;
    if (lm.dashed !== isDashed) {
      lm.dashed = isDashed;
      lm.needsUpdate = true;
    }
    if (isDashed) {
      const dm = mat as THREE.LineDashedMaterial;
      const clampedZoomScale = Number.isFinite(zoomDashScale)
        ? Math.max(0.55, Math.min(2.2, zoomDashScale))
        : 1;
      const roleDashFactor = isAuxiliaryLine || isLineExtension ? 1.14 : isPerpOrWitness ? 1.08 : 1;
      const effDashScale = clampedZoomScale * roleDashFactor;
      lm.dashSize = dm.dashSize || PHONG_CACH_SCENE3D.dash.fallback;
      lm.gapSize = dm.gapSize || lm.dashSize * PHONG_CACH_SCENE3D.dash.gapRatio;
      lm.dashScale = effDashScale;
      const rawDistOffset = Number(line.userData?.dashDistanceOffset) || 0;
      lm.dashOffset = rawDistOffset * effDashScale;
    } else {
      lm.dashOffset = 0;
    }
    line2.renderOrder = line.renderOrder;
    line2.name = `fat:${line.name}`;
    line2.visible = true;
  });

  for (const [n, nhom] of pools) {
    for (let k = daDung.get(n) ?? 0; k < nhom.length; k += 1) nhom[k].visible = false;
  }

  // Đồng bộ vành cong (đường tròn, elip, nắp trụ/nón, vòng tham chiếu cầu) qua `LineSegments2` theo điểm ảnh màn hình
  // để độ dày nét đều 360° không bị co 1px ở cung trước/sau khi chiếu phối cảnh, đồng thời tái sử dụng buffer GPU tại chỗ.
  const rimSegMap: Map<string, LineSegments2> =
    (fatGroup.userData.rimSegMap as Map<string, LineSegments2> | undefined) ?? new Map();
  fatGroup.userData.rimSegMap = rimSegMap;
  const usedRimKeys = new Set<string>();
  const rimNameCounts = new Map<string, number>();
  let totalRimPasses = 0;

  for (const { node, rim } of activeRims) {
    const baseRimLabel = node.name || rim.objectId;
    const dupIdx = rimNameCounts.get(baseRimLabel) ?? 0;
    rimNameCounts.set(baseRimLabel, dupIdx + 1);
    const uniqueRimLabel = dupIdx === 0 ? baseRimLabel : `${baseRimLabel}#${dupIdx}`;
    for (const part of [rim.thayMesh, rim.khuatMesh, rim.thayNet, rim.khuatNet]) {
      if (part.visible) sourceRimObjects.push(part);
    }
    const role: "section" | "base" | "reference" | "inscribed" | "circumscribed" =
      rim.rimRole
      ?? (node.userData?.presentationReference || node.name.startsWith("sphere_reference:")
        ? "reference"
        : node.name.startsWith("ellipse:") || Boolean(node.getObjectByName?.(`section_fill:${rim.objectId}`))
          ? "section"
          : "base");
    const rimState = (
      rim.interactionState
      ?? node.userData?.interactionState
      ?? (rim.highlighted || node.userData?.highlighted ? "selected" : "neutral")
    ) as "neutral" | "hover" | "selected";
    const passes: { suffix: "thay" | "khuat"; netSrc: THREE.LineSegments; meshSrc: THREE.Mesh; isHidden: boolean }[] = [
      { suffix: "thay", netSrc: rim.thayNet, meshSrc: rim.thayMesh, isHidden: false },
      { suffix: "khuat", netSrc: rim.khuatNet, meshSrc: rim.khuatMesh, isHidden: true },
    ];
    for (const pass of passes) {
      if (pass.isHidden && !dashedHiddenShown) continue;
      if (!pass.netSrc.visible) continue;
      const matSrc = pass.meshSrc.material as THREE.MeshBasicMaterial | undefined;
      if (!matSrc || matSrc.colorWrite === false || (matSrc.transparent && matSrc.opacity <= 0.01)) continue;
      const posAttr = pass.netSrc.geometry?.getAttribute?.("position") as THREE.BufferAttribute | undefined;
      if (!posAttr || posAttr.count < 2) continue;
      const drawVerts = Math.min(pass.netSrc.geometry.drawRange.count, posAttr.count);
      const segCount = Math.floor(drawVerts / 2);
      if (segCount < 1) continue;

      const rawRim = role === "reference"
        ? (rimState === "selected"
          ? (pass.isHidden ? w.edge * 0.63 : w.edge * 0.74)
          : rimState === "hover"
            ? (pass.isHidden ? w.edge * 0.56 : w.edge * 0.65)
            : (pass.isHidden ? w.edge * 0.50 : w.edge * 0.58))
        : role === "section"
          ? (rimState === "selected"
            ? w.selectedSection
            : rimState === "hover"
              ? w.hoverSection
              : pass.isHidden
                ? w.hiddenSection
                : w.section)
          : role === "inscribed" || role === "circumscribed"
            ? (rimState === "selected"
              ? 4.4
              : rimState === "hover"
                ? 3.9
                : pass.isHidden
                  ? 2.35
                  : 3.4)
            : (rimState === "selected"
              ? w.selectedEdge
              : rimState === "hover"
                ? w.hoverEdge
                : pass.isHidden
                  ? w.hiddenEdge
                  : w.edge);
      const rimStepRole = clampedPulse > 0.005 && rimState === "neutral" ? resolveStepRole(node) : undefined;
      const rimStepBoost = rimStepRole === "new"
        ? 1 + 0.24 * clampedPulse
        : rimStepRole === "dep"
          ? 1 + 0.11 * clampedPulse
          : 1;
      const widthPx = Number((rawRim * rimStepBoost * heSoNet).toFixed(2));

      if (role === "section" && !pass.isHidden) {
        maxSectionBorderWidth = Math.max(maxSectionBorderWidth, widthPx);
      } else if ((role === "base" || role === "inscribed" || role === "circumscribed") && !pass.isHidden) {
        maxVisibleEdgeWidth = Math.max(maxVisibleEdgeWidth, widthPx);
      }
      if (pass.isHidden) {
        minHiddenEdgeWidth = Math.min(minHiddenEdgeWidth, widthPx);
      }

      // Step owners get new UUIDs; their semantic rims keep the same reusable GPU buffers.
      const key = `${uniqueRimLabel}:${rim.objectId}:${pass.suffix}`;
      usedRimKeys.add(key);
      totalRimPasses += 1;
      let seg2 = rimSegMap.get(key);
      const capSegs = Math.max(2048, Math.ceil(posAttr.count / 2));
      if (!seg2) {
        const g = new LineSegmentsGeometry();
        const initBuf = new Float32Array(capSegs * 6);
        g.setPositions(initBuf);
        const startAttr = g.attributes.instanceStart as THREE.InterleavedBufferAttribute | undefined;
        startAttr?.data.setUsage(THREE.DynamicDrawUsage);
        const m = new LineMaterial({
          color: 0x1e293b,
          linewidth: widthPx,
          dashed: false,
          transparent: true,
          opacity: 1,
          depthTest: false,
          depthWrite: false,
        });
        seg2 = new LineSegments2(g, m);
        seg2.frustumCulled = false;
        seg2.raycast = () => {};
        seg2.userData.voHan = true;
        seg2.userData.fatRimCompanion = true;
        rimSegMap.set(key, seg2);
        fatGroup.add(seg2);
      }

      const neededCoords = segCount * 6;
      let coords = seg2.userData.coordsCache as Float32Array | undefined;
      let changed = seg2.userData.segCount !== segCount || !coords || coords.length < neededCoords;
      if (!coords || coords.length < neededCoords) {
        coords = new Float32Array(Math.max(neededCoords, capSegs * 6));
        seg2.userData.coordsCache = coords;
      }
      for (let i = 0; i < segCount * 2; i += 1) {
        tmp.fromBufferAttribute(posAttr, i).applyMatrix4(pass.netSrc.matrixWorld);
        const base = i * 3;
        if (
          !changed
          && (Math.abs(coords[base] - tmp.x) > 1e-6
            || Math.abs(coords[base + 1] - tmp.y) > 1e-6
            || Math.abs(coords[base + 2] - tmp.z) > 1e-6)
        ) {
          changed = true;
        }
        coords[base] = tmp.x;
        coords[base + 1] = tmp.y;
        coords[base + 2] = tmp.z;
      }

      if (changed) {
        seg2.userData.segCount = segCount;
        if (!capNhatLineSegments2TaiCho(seg2, coords, segCount)) {
          seg2.geometry?.dispose?.();
          const g = new LineSegmentsGeometry();
          const newBuf = new Float32Array(Math.max(neededCoords, capSegs * 6));
          newBuf.set(coords.subarray(0, neededCoords), 0);
          g.setPositions(newBuf);
          g.instanceCount = segCount;
          const startAttr = g.attributes.instanceStart as THREE.InterleavedBufferAttribute | undefined;
          startAttr?.data.setUsage(THREE.DynamicDrawUsage);
          seg2.geometry = g;
        }
      }

      const lm = seg2.material as LineMaterial;
      lm.color.copy(matSrc.color);
      lm.linewidth = widthPx;
      lm.resolution.set(resW, resH);
      lm.transparent = true;
      lm.opacity = matSrc.opacity ?? 1;
      lm.depthTest = matSrc.depthTest;
      lm.depthWrite = false;
      lm.depthFunc = matSrc.depthFunc;
      lm.polygonOffset = matSrc.polygonOffset;
      lm.polygonOffsetFactor = matSrc.polygonOffsetFactor;
      lm.polygonOffsetUnits = matSrc.polygonOffsetUnits;
      seg2.renderOrder = pass.meshSrc.renderOrder;
      seg2.name = `fat_rim:${uniqueRimLabel}:${pass.suffix}`;
      seg2.visible = true;
    }
  }

  for (const [key, seg2] of rimSegMap) {
    if (!usedRimKeys.has(key)) seg2.visible = false;
  }

  return {
    totalLines: activeLines.length + totalRimPasses,
    maxSectionBorderWidth,
    maxVisibleEdgeWidth,
    minHiddenEdgeWidth: Number.isFinite(minHiddenEdgeWidth) ? minHiddenEdgeWidth : 0,
    sourceLines: activeLines,
    sourceRimObjects,
  };
}
