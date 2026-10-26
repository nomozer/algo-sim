/** Camera-relative edge visibility. Presentation-only; never feeds geometry state. */
import * as THREE from "three";
import { Line2 } from "three/addons/lines/Line2.js";
import { LineGeometry } from "three/addons/lines/LineGeometry.js";
import { LineMaterial } from "three/addons/lines/LineMaterial.js";
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
  /** Inverse presentation transform; intersections stay in the primitive's original local frame. */
  worldToLocal?: THREE.Matrix4;
}

/** Compile occluders once when sampling a true 3D curve, rather than rebuilding triangles per point. */
export function createWorldPointOcclusionTest(
  camera: THREE.Vector3,
  occluders: readonly WorldSolidOccluder[],
  curved: readonly CurvedSolidVolumeMeta[],
): (point: THREE.Vector3) => boolean {
  const triangles = occludingTriangles(occluders.map(o => o.solid), occluders.map(o => o.matrixWorld));
  const excluded = new Set<string>();
  return point => pointIsHidden(point, camera, triangles, excluded) || diemVanhCongBiChe(point, camera, curved);
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
    for (const point of points) {
      const relative = point.clone().sub(volume.anchor), direction = eye.clone().sub(point);
      const normal = relative.clone();
      let residual: number;
      if (volume.kind === "ball") {
        residual = relative.lengthSq() - volume.radius ** 2;
      } else {
        if (!axis || volume.height <= 0) break;
        const z = relative.dot(axis);
        if (z < -1e-8 || z > volume.height + 1e-8) break;
        normal.addScaledVector(axis, -z);
        const fraction = volume.kind === "cone" ? 1 - z / volume.height : 1;
        residual = normal.lengthSq() - (volume.radius * fraction) ** 2;
        if (volume.kind === "cone") normal.addScaledVector(axis, volume.radius ** 2 * fraction / volume.height);
      }
      if (Math.abs(residual) > 1e-8 * Math.max(1, volume.radius ** 2)) break;
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
      if (rel.addScaledVector(dir, t).lengthSq() < r * r * (1 - 1e-10)) return true;
      continue;
    }
    const h = vol.height;
    if (!vol.top || h <= 1e-6) continue;
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
    if (minimum < -r * r * 1e-10) return true;
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
    const outline = candidate.getObjectByName(`sphere_silhouette:${meta.id}`);
    if (!outline) return;
    const towardEye = eye.clone().sub(anchor), distance = towardEye.length();
    outline.visible = distance > r;
    if (outline.visible) {
      towardEye.divideScalar(distance);
      outline.position.copy(anchor).addScaledVector(towardEye, r * r / distance);
      outline.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), towardEye);
      outline.scale.setScalar(r * Math.sqrt(1 - r * r / (distance * distance)));
    }
  } else if (top && h > 0) {
    const outline = candidate.getObjectByName(`curved_silhouette:${meta.id}`);
    if (!outline) return;
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
  return [solidHold, dashedHold];
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

export function dongBoNetDayManHinh(
  roots: readonly THREE.Object3D[],
  fatGroup: THREE.Group,
  wCss: number,
  hCss: number,
): FatLineSyncSummary {
  const activeLines: THREE.Line[] = [];
  for (const r of roots) {
    r.updateMatrixWorld(true);
    r.traverse((node) => {
      if (!(node as THREE.Line).isLine || (node as THREE.LineSegments).isLineSegments) return;
      for (let p: THREE.Object3D | null = node; p; p = p.parent) {
        if (!p.visible) return;
        if (p === r) break;
      }
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
  let maxSectionBorderWidth = 0;
  let maxVisibleEdgeWidth = 0;
  let minHiddenEdgeWidth = Infinity;

  activeLines.forEach((line) => {
    const mat = line.material as THREE.LineBasicMaterial | THREE.LineDashedMaterial;
    const pos = line.geometry.getAttribute("position") as THREE.BufferAttribute;
    const isDashed =
      line.userData?.hidden === true
      || (mat as THREE.LineDashedMaterial).isLineDashedMaterial === true
      || line.name.endsWith(":khuat");
    const isPlaneBorder =
      Boolean(line.parent?.userData?.nonCanonicalLoop?.isPlaneBorder)
      || line.name.startsWith("plane_border:");
    const isSectionOrPolyBorder =
      !isPlaneBorder
      && (line.name.startsWith("section_border:") || line.name.startsWith("polygon_border:"));
    const isPerpOrWitness =
      line.name.startsWith("perp_marker:") || Boolean(line.parent?.userData?.nhanChung);
    const isHighlighted = Boolean(
      line.userData?.sang
      || line.parent?.userData?.highlighted
      || (mat.linewidth && mat.linewidth >= 2.6),
    );

    const w = PHONG_CACH_SCENE3D.fatPx;
    const raw = isPlaneBorder
      ? (isHighlighted ? w.selectedPlane : w.plane)
      : isSectionOrPolyBorder
        ? (isHighlighted ? w.selectedSection : isDashed ? w.hiddenSection : w.section)
        : isPerpOrWitness
          ? (isDashed ? w.hiddenPerpendicular : w.perpendicular)
          : line.name.startsWith("sphere_silhouette:")
            ? w.edge * 0.65 // A sphere's continuous outline stays subordinate to its true section curve.
            : (isHighlighted ? w.selectedEdge : isDashed ? w.hiddenEdge : w.edge);
    const widthPx = Number((raw * heSoNet).toFixed(2));

    if (isSectionOrPolyBorder && !isDashed) {
      maxSectionBorderWidth = Math.max(maxSectionBorderWidth, widthPx);
    } else if (!isPlaneBorder && !isPerpOrWitness && !isDashed) {
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
      lm.dashSize = dm.dashSize || 0.14;
      lm.gapSize = dm.gapSize || 0.10;
      lm.dashScale = 1;
    }
    line2.renderOrder = line.renderOrder;
    line2.name = `fat:${line.name}`;
    line2.visible = true;
  });

  for (const [n, nhom] of pools) {
    for (let k = daDung.get(n) ?? 0; k < nhom.length; k += 1) nhom[k].visible = false;
  }

  return {
    totalLines: activeLines.length,
    maxSectionBorderWidth,
    maxVisibleEdgeWidth,
    minHiddenEdgeWidth: Number.isFinite(minHiddenEdgeWidth) ? minHiddenEdgeWidth : 0,
    sourceLines: activeLines,
  };
}
