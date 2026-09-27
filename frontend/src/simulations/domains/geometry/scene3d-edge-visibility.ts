/** Camera-relative edge visibility. Presentation-only; never feeds geometry state. */
import * as THREE from "three";
import { toVec3, type SceneObject } from "./scene3d-model";
import { edgeId } from "./scene3d-subentities";

export interface CanonicalEdge {
  id: string;
  a: THREE.Vector3;
  b: THREE.Vector3;
  adjacentFaces: number[];
}

export interface EdgeVisibilityAudit {
  visible_edge_ids: string[];
  hidden_edge_ids: string[];
  mixed_edge_ids: string[];
  duplicate_visual_owner_ids: string[];
}

export function canonicalEdgesOf(o: SceneObject): CanonicalEdge[] {
  if (o.type !== "solid" || !o.vertices || !o.vertex_ids || !o.faces) return [];
  if (o.vertices.length !== o.vertex_ids.length) return [];
  const byId = new Map<string, CanonicalEdge>();
  o.faces.forEach((face, faceIndex) => {
    for (let i = 0; i < face.length; i += 1) {
      const ia = face[i];
      const ib = face[(i + 1) % face.length];
      if (!o.vertices?.[ia] || !o.vertices?.[ib] || !o.vertex_ids?.[ia] || !o.vertex_ids?.[ib]) {
        continue;
      }
      const id = edgeId(o.id, o.vertex_ids[ia], o.vertex_ids[ib]);
      const existing = byId.get(id);
      if (existing) {
        if (!existing.adjacentFaces.includes(faceIndex)) existing.adjacentFaces.push(faceIndex);
      } else {
        byId.set(id, {
          id,
          a: new THREE.Vector3(...toVec3(o.vertices[ia])),
          b: new THREE.Vector3(...toVec3(o.vertices[ib])),
          adjacentFaces: [faceIndex],
        });
      }
    }
  });
  return [...byId.values()].sort((a, b) => a.id.localeCompare(b.id));
}

function faceIsFrontFacing(
  o: SceneObject,
  faceIndex: number,
  camera: THREE.Vector3,
  solidCenter: THREE.Vector3,
): boolean {
  const face = o.faces?.[faceIndex] ?? [];
  const points = face
    .map((index) => o.vertices?.[index])
    .filter((value): value is NonNullable<typeof value> => !!value)
    .map((value) => new THREE.Vector3(...toVec3(value)));
  if (points.length < 3) return true;
  const center = points.reduce((sum, point) => sum.add(point), new THREE.Vector3())
    .multiplyScalar(1 / points.length);
  let normal = new THREE.Vector3();
  let index = 1;
  while (index < points.length - 1 && normal.lengthSq() === 0) {
    normal = new THREE.Vector3()
      .subVectors(points[index], points[0])
      .cross(new THREE.Vector3().subVectors(points[index + 1], points[0]));
    index += 1;
  }
  if (normal.lengthSq() === 0) return true;
  normal.normalize();
  if (normal.dot(center.clone().sub(solidCenter)) < 0) normal.negate();
  return normal.dot(camera.clone().sub(center)) >= 0;
}

/** Recomputed for every camera frame, so orbit cannot retain a stale set. */
export function classifySolidEdgeVisibility(
  o: SceneObject,
  camera: THREE.Vector3,
): EdgeVisibilityAudit {
  const edges = canonicalEdgesOf(o);
  const vertices = (o.vertices ?? []).map((value) => new THREE.Vector3(...toVec3(value)));
  const center = vertices.length > 0
    ? vertices.reduce((sum, point) => sum.add(point), new THREE.Vector3())
      .multiplyScalar(1 / vertices.length)
    : new THREE.Vector3();
  const visible: string[] = [];
  const hidden: string[] = [];
  for (const edge of edges) {
    const isVisible = edge.adjacentFaces.some((faceIndex) =>
      faceIsFrontFacing(o, faceIndex, camera, center));
    (isVisible ? visible : hidden).push(edge.id);
  }
  return {
    visible_edge_ids: visible.sort(),
    hidden_edge_ids: hidden.sort(),
    mixed_edge_ids: [],
    duplicate_visual_owner_ids: [],
  };
}
