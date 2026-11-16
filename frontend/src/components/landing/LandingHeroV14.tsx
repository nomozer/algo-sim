import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type MouseEvent as ReactMouseEvent,
  type PointerEvent as ReactPointerEvent,
} from "react";
import * as THREE from "three";
import { useAuthStore } from "../../state/auth";
import { AnnotatedPhrase } from "./AnnotatedHeading";
import { separateLabelPositions } from "./LandingHeroScene3D";
import {
  computeBoundedPlaneQuad,
  enterAxoWorkspace,
  LANDING_PYRAMID_SAMPLE,
  type LandingPointSpec,
  type Vec3Tuple,
} from "./landing-geometry-data";

export interface TrueShapeVertex2D {
  readonly id: string;
  readonly label: string;
  readonly x: number;
  readonly y: number;
  readonly nx: number;
  readonly ny: number;
}

export interface TrueShapeProjectionResult {
  readonly vertices: readonly TrueShapeVertex2D[];
  readonly edgeLengths3D: readonly number[];
  readonly edgeLengths2D: readonly number[];
  readonly maxDeviation: number;
}

export type HeroStoryboardBeat =
  | "solid-emergence"
  | "seed-anchors"
  | "plane-intersection"
  | "section-settled";

export interface HeroStoryboardState {
  readonly beat: HeroStoryboardBeat;
  readonly progress: number;
  readonly solidReveal: number;
  readonly seedReveal: number;
  readonly planeSweep: number;
  readonly traceProgress: number;
  readonly sectionFill: number;
  readonly satelliteReveal: number;
  readonly capLift: number;
  readonly orbitOffsetRad: number;
  readonly settled: boolean;
}

export const HERO_STORYBOARD_MS = 3800;
export const HERO_SECTION_FILL_OPACITY = 0.5;
export const HERO_SATELLITE_COUNT = 3;

export interface HeroGallerySatelliteSpec {
  readonly id: "octahedron" | "extractedPentagon" | "slicedCube";
  readonly offset: Vec3Tuple;
  readonly screenDx: number;
  readonly screenDy: number;
  readonly screenDz: number;
  readonly rotation: Vec3Tuple;
  readonly parallaxFactor: number;
}

export interface HeroSpatialGallerySpecs {
  readonly cameraOffset: Vec3Tuple;
  readonly lookTarget: Vec3Tuple;
  readonly basisRight: Vec3Tuple;
  readonly basisUp: Vec3Tuple;
  readonly basisForward: Vec3Tuple;
  readonly octahedronRadius: number;
  readonly octahedronVertices: readonly Vec3Tuple[];
  readonly octahedronEdges: readonly (readonly [number, number])[];
  readonly octahedronFaces: readonly (readonly [number, number, number])[];
  readonly octahedronMidRing: readonly Vec3Tuple[];
  readonly extractedPentagonPts: readonly Vec3Tuple[];
  readonly cubeHalfSize: number;
  readonly cubeVertices: readonly Vec3Tuple[];
  readonly cubeEdges: readonly (readonly [number, number])[];
  readonly cubeHexSection: readonly Vec3Tuple[];
  readonly satellites: readonly HeroGallerySatelliteSpec[];
}

interface ClippedPolygonFace {
  readonly pts: THREE.Vector3[];
}

interface TrackedDisposable {
  dispose(): void;
}

interface ProjectedCallout {
  readonly id: string;
  readonly label: string;
  readonly role: "vertex" | "seed" | "intersection" | "plane" | "aux";
  readonly x: number;
  readonly y: number;
  readonly visible: boolean;
}

function clamp01(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(1, value));
}

function clampPhase(value: number, start: number, end: number): number {
  if (value <= start) return 0;
  if (value >= end) return 1;
  const u = (value - start) / Math.max(1e-6, end - start);
  return 1 - Math.pow(1 - u, 3);
}

export function evaluateHeroStoryboard(
  elapsedMs: number,
  reducedMotion = false,
): HeroStoryboardState {
  if (reducedMotion || elapsedMs >= HERO_STORYBOARD_MS) {
    return {
      beat: "section-settled",
      progress: 1,
      solidReveal: 1,
      seedReveal: 1,
      planeSweep: 1,
      traceProgress: 1,
      sectionFill: 1,
      satelliteReveal: 1,
      capLift: 0,
      orbitOffsetRad: 0,
      settled: true,
    };
  }

  const p = clamp01(elapsedMs / HERO_STORYBOARD_MS);
  let beat: HeroStoryboardBeat = "solid-emergence";
  if (p >= 0.76) beat = "section-settled";
  else if (p >= 0.48) beat = "plane-intersection";
  else if (p >= 0.24) beat = "seed-anchors";

  const solidReveal = 0.45 + 0.55 * clampPhase(p, 0.0, 0.22);
  const seedReveal = clampPhase(p, 0.12, 0.3);
  const planeSweep = clampPhase(p, 0.18, 0.36);
  const traceProgress = clampPhase(p, 0.22, 0.42);
  const sectionFill = clampPhase(p, 0.26, 0.48);
  const satelliteReveal = clampPhase(p, 0.14, 0.46);
  const capLift = 0;
  const orbitOffsetRad = (1 - clampPhase(p, 0.0, 0.96)) * 0.14;

  return {
    beat,
    progress: p,
    solidReveal,
    seedReveal,
    planeSweep,
    traceProgress,
    sectionFill,
    satelliteReveal,
    capLift,
    orbitOffsetRad,
    settled: p >= 0.999,
  };
}

function sub3(a: Vec3Tuple, b: Vec3Tuple): Vec3Tuple {
  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
}

function cross3(a: Vec3Tuple, b: Vec3Tuple): Vec3Tuple {
  return [
    a[1] * b[2] - a[2] * b[1],
    a[2] * b[0] - a[0] * b[2],
    a[0] * b[1] - a[1] * b[0],
  ];
}

function dot3(a: Vec3Tuple, b: Vec3Tuple): number {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

function normalize3(v: Vec3Tuple): Vec3Tuple {
  const len = Math.hypot(v[0], v[1], v[2]) || 1;
  return [v[0] / len, v[1] / len, v[2] / len];
}

/**
 * Computes an exact 2D isometric orthographic projection of a planar 3D polygon loop.
 * Preserves all pairwise Euclidean lengths between vertices in plane space.
 */
export function computeTrueShapeSection2D(
  pointMap: Readonly<Record<string, LandingPointSpec>> = LANDING_PYRAMID_SAMPLE.pointMap,
  sectionLoop: readonly string[] = LANDING_PYRAMID_SAMPLE.sectionLoop,
): TrueShapeProjectionResult {
  const coords = sectionLoop.map((id) => ({
    id,
    label: pointMap[id]?.label ?? id,
    p: pointMap[id]?.domainXyz ?? ([0, 0, 0] as Vec3Tuple),
  }));

  if (coords.length < 3) {
    return {
      vertices: coords.map((c) => ({
        id: c.id,
        label: c.label,
        x: 0,
        y: 0,
        nx: 0.5,
        ny: 0.5,
      })),
      edgeLengths3D: [],
      edgeLengths2D: [],
      maxDeviation: 0,
    };
  }

  const p0 = coords[0].p;
  const e1 = normalize3(sub3(coords[1].p, p0));
  let p2Idx = 2;
  for (let i = 2; i < coords.length; i++) {
    const candidate = cross3(e1, sub3(coords[i].p, p0));
    if (Math.hypot(candidate[0], candidate[1], candidate[2]) > 1e-6) {
      p2Idx = i;
      break;
    }
  }
  const n = normalize3(cross3(e1, sub3(coords[p2Idx].p, p0)));
  const e2 = normalize3(cross3(n, e1));

  const centroid: Vec3Tuple = [
    coords.reduce((s, c) => s + c.p[0], 0) / coords.length,
    coords.reduce((s, c) => s + c.p[1], 0) / coords.length,
    coords.reduce((s, c) => s + c.p[2], 0) / coords.length,
  ];

  const projected = coords.map((c) => {
    const rel = sub3(c.p, centroid);
    return {
      id: c.id,
      label: c.label,
      x: dot3(rel, e1),
      y: -dot3(rel, e2),
    };
  });

  const minX = Math.min(...projected.map((v) => v.x));
  const maxX = Math.max(...projected.map((v) => v.x));
  const minY = Math.min(...projected.map((v) => v.y));
  const maxY = Math.max(...projected.map((v) => v.y));
  const spanX = Math.max(1e-6, maxX - minX);
  const spanY = Math.max(1e-6, maxY - minY);
  const scale = Math.min(0.68 / spanX, 0.64 / spanY);
  const midX = (minX + maxX) * 0.5;
  const midY = (minY + maxY) * 0.5;

  const vertices: TrueShapeVertex2D[] = projected.map((v) => ({
    id: v.id,
    label: v.label,
    x: v.x,
    y: v.y,
    nx: 0.5 + (v.x - midX) * scale,
    ny: 0.52 + (v.y - midY) * scale,
  }));

  const edgeLengths3D: number[] = [];
  const edgeLengths2D: number[] = [];
  let maxDeviation = 0;

  for (let i = 0; i < coords.length; i++) {
    const j = (i + 1) % coords.length;
    const d3 = Math.hypot(
      coords[j].p[0] - coords[i].p[0],
      coords[j].p[1] - coords[i].p[1],
      coords[j].p[2] - coords[i].p[2],
    );
    const d2 = Math.hypot(
      vertices[j].x - vertices[i].x,
      vertices[j].y - vertices[i].y,
    );
    edgeLengths3D.push(d3);
    edgeLengths2D.push(d2);
    maxDeviation = Math.max(maxDeviation, Math.abs(d3 - d2));
  }

  return { vertices, edgeLengths3D, edgeLengths2D, maxDeviation };
}

/**
 * Pure Spatial Geometry Gallery specification: places 3 asymmetric, mathematically
 * grounded Axo satellites in 3D camera-basis depth around S.ABCD without overlap or collinearity.
 */
export function buildHeroSpatialGallerySpecs(): HeroSpatialGallerySpecs {
  const [lookX, lookY, lookZ] = LANDING_PYRAMID_SAMPLE.defaultLookAt;
  const cameraOffset: Vec3Tuple = [10.8, 5.9, -7.2];
  const lookTarget: Vec3Tuple = [lookX, lookY + 0.22, lookZ];

  const basisForward = normalize3([-cameraOffset[0], -cameraOffset[1], -cameraOffset[2]]);
  const basisRight = normalize3(cross3(basisForward, [0, 1, 0]));
  const basisUp = normalize3(cross3(basisRight, basisForward));

  const placeInCameraFrame = (dx: number, dy: number, dz: number): Vec3Tuple => [
    lookTarget[0] + basisRight[0] * dx + basisUp[0] * dy + basisForward[0] * dz,
    lookTarget[1] + basisRight[1] * dx + basisUp[1] * dy + basisForward[1] * dz,
    lookTarget[2] + basisRight[2] * dx + basisUp[2] * dy + basisForward[2] * dz,
  ];

  // Satellite 1 (rear upper-right): Regular Octahedron + horizontal equatorial square trace
  const r = 0.44;
  const octahedronVertices: readonly Vec3Tuple[] = [
    [r, 0, 0],
    [-r, 0, 0],
    [0, r, 0],
    [0, -r, 0],
    [0, 0, r],
    [0, 0, -r],
  ];
  const octahedronEdges: readonly (readonly [number, number])[] = [
    [2, 0], [2, 1], [2, 4], [2, 5],
    [3, 0], [3, 1], [3, 4], [3, 5],
    [0, 4], [4, 1], [1, 5], [5, 0],
  ];
  const octahedronFaces: readonly (readonly [number, number, number])[] = [
    [2, 0, 4], [2, 4, 1], [2, 1, 5], [2, 5, 0],
    [3, 4, 0], [3, 1, 4], [3, 5, 1], [3, 0, 5],
  ];
  const hr = r * 0.5;
  const octahedronMidRing: readonly Vec3Tuple[] = [
    [hr, 0, hr],
    [-hr, 0, hr],
    [-hr, 0, -hr],
    [hr, 0, -hr],
  ];

  // Satellite 2 (foreground lower-left): Extracted isometric true-shape pentagon MENPF plate
  const trueShape = computeTrueShapeSection2D();
  const pentScale = 0.185;
  const extractedPentagonPts: readonly Vec3Tuple[] = trueShape.vertices.map((v) => [
    v.x * pentScale,
    -v.y * pentScale,
    0,
  ]);

  // Satellite 3 (midground lower-right): Unit cube sliced by x + y + z = 0 regular hexagon
  const h = 0.34;
  const cubeVertices: readonly Vec3Tuple[] = [
    [-h, -h, -h],
    [h, -h, -h],
    [h, h, -h],
    [-h, h, -h],
    [-h, -h, h],
    [h, -h, h],
    [h, h, h],
    [-h, h, h],
  ];
  const cubeEdges: readonly (readonly [number, number])[] = [
    [0, 1], [1, 2], [2, 3], [3, 0],
    [4, 5], [5, 6], [6, 7], [7, 4],
    [0, 4], [1, 5], [2, 6], [3, 7],
  ];
  const cubeHexSection: readonly Vec3Tuple[] = [
    [h, -h, 0],
    [h, 0, -h],
    [0, h, -h],
    [-h, h, 0],
    [-h, 0, h],
    [0, -h, h],
  ];

  const satellites: readonly HeroGallerySatelliteSpec[] = [
    {
      id: "octahedron",
      offset: placeInCameraFrame(2.36, 1.88, 1.35),
      screenDx: 2.36,
      screenDy: 1.88,
      screenDz: 1.35,
      rotation: [0.26, 0.44, -0.14],
      parallaxFactor: 0.72,
    },
    {
      id: "extractedPentagon",
      offset: placeInCameraFrame(-2.92, 0.58, -0.65),
      screenDx: -2.92,
      screenDy: 0.58,
      screenDz: -0.65,
      rotation: [-0.22, 0.32, 0.08],
      parallaxFactor: 1.28,
    },
    {
      id: "slicedCube",
      offset: placeInCameraFrame(3.24, -0.36, -0.28),
      screenDx: 3.24,
      screenDy: -0.36,
      screenDz: -0.28,
      rotation: [0.24, -0.36, 0.12],
      parallaxFactor: 1.12,
    },
  ];

  return {
    cameraOffset,
    lookTarget,
    basisRight,
    basisUp,
    basisForward,
    octahedronRadius: r,
    octahedronVertices,
    octahedronEdges,
    octahedronFaces,
    octahedronMidRing,
    extractedPentagonPts,
    cubeHalfSize: h,
    cubeVertices,
    cubeEdges,
    cubeHexSection,
    satellites,
  };
}

function clipPolygonHalfSpace(
  poly: readonly THREE.Vector3[],
  normal: THREE.Vector3,
  offset: number,
  keepPositive: boolean,
): THREE.Vector3[] {
  const out: THREE.Vector3[] = [];
  const eps = 1e-6;
  const signedDist = (v: THREE.Vector3) => {
    const d = v.dot(normal) - offset;
    return keepPositive ? d : -d;
  };

  for (let i = 0; i < poly.length; i++) {
    const curr = poly[i];
    const next = poly[(i + 1) % poly.length];
    const dc = signedDist(curr);
    const dn = signedDist(next);
    const currIn = dc >= -eps;
    const nextIn = dn >= -eps;

    if (currIn && nextIn) {
      out.push(next.clone());
    } else if (currIn && !nextIn) {
      const t = dc / (dc - dn || 1);
      out.push(new THREE.Vector3().lerpVectors(curr, next, Math.max(0, Math.min(1, t))));
    } else if (!currIn && nextIn) {
      const t = dc / (dc - dn || 1);
      out.push(new THREE.Vector3().lerpVectors(curr, next, Math.max(0, Math.min(1, t))));
      out.push(next.clone());
    }
  }

  const deduped: THREE.Vector3[] = [];
  for (const pt of out) {
    if (deduped.length === 0 || deduped[deduped.length - 1].distanceToSquared(pt) > 1e-8) {
      deduped.push(pt);
    }
  }
  if (deduped.length >= 2 && deduped[0].distanceToSquared(deduped[deduped.length - 1]) < 1e-8) {
    deduped.pop();
  }
  return deduped;
}

function orientFaceOutward(
  face: readonly THREE.Vector3[],
  centroid: THREE.Vector3,
): THREE.Vector3[] {
  if (face.length < 3) return [...face];
  const e1 = new THREE.Vector3().subVectors(face[1], face[0]);
  const e2 = new THREE.Vector3().subVectors(face[2], face[0]);
  const n = new THREE.Vector3().crossVectors(e1, e2);
  const inward = new THREE.Vector3().subVectors(centroid, face[0]);
  return n.dot(inward) > 0 ? [...face].reverse() : [...face];
}

function buildFacesBufferGeometry(
  faces: readonly ClippedPolygonFace[],
  baseColorHex?: number,
): THREE.BufferGeometry {
  const positions: number[] = [];
  const colors: number[] = [];
  const baseColor = baseColorHex !== undefined ? new THREE.Color(baseColorHex) : null;
  const keyDir = new THREE.Vector3(6.5, 11.2, -5.0).normalize();
  const rimDir = new THREE.Vector3(-8.0, 4.0, 7.0).normalize();
  const e1 = new THREE.Vector3();
  const e2 = new THREE.Vector3();
  const triNormal = new THREE.Vector3();

  for (const face of faces) {
    if (face.pts.length < 3) continue;
    const p0 = face.pts[0];
    for (let i = 1; i < face.pts.length - 1; i++) {
      const p1 = face.pts[i];
      const p2 = face.pts[i + 1];
      positions.push(p0.x, p0.y, p0.z, p1.x, p1.y, p1.z, p2.x, p2.y, p2.z);
      if (baseColor) {
        e1.subVectors(p1, p0);
        e2.subVectors(p2, p0);
        triNormal.crossVectors(e1, e2).normalize();
        const key = Math.max(0, triNormal.dot(keyDir)) * 0.22;
        const rim = Math.max(0, triNormal.dot(rimDir)) * 0.08;
        const shade = Math.min(1.04, 0.8 + key + rim);
        const r = Math.min(1, baseColor.r * shade);
        const g = Math.min(1, baseColor.g * shade);
        const b = Math.min(1, baseColor.b * shade);
        colors.push(r, g, b, r, g, b, r, g, b);
      }
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  if (baseColor) {
    geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  }
  geo.computeVertexNormals();
  return geo;
}

function createLineSegment(
  a: THREE.Vector3,
  b: THREE.Vector3,
  colorHex: number,
  opacity: number,
  dashed: boolean,
  track: <T extends TrackedDisposable>(item: T) => T,
): THREE.Line {
  const geo = track(new THREE.BufferGeometry().setFromPoints([a, b]));
  const mat = dashed
    ? track(
        new THREE.LineDashedMaterial({
          color: colorHex,
          dashSize: 0.14,
          gapSize: 0.1,
          transparent: true,
          opacity,
        }),
      )
    : track(
        new THREE.LineBasicMaterial({
          color: colorHex,
          transparent: true,
          opacity,
        }),
      );
  const line = new THREE.Line(geo, mat);
  if (dashed) {
    line.computeLineDistances();
  }
  return line;
}

function createCylinderEdge(
  a: THREE.Vector3,
  b: THREE.Vector3,
  radius: number,
  colorHex: number,
  opacity: number,
  track: <T extends TrackedDisposable>(item: T) => T,
  anchorFromStart = false,
): THREE.Mesh {
  const dir = new THREE.Vector3().subVectors(b, a);
  const len = Math.max(0.001, dir.length());
  const geo = track(new THREE.CylinderGeometry(radius, radius, len, 10, 1));
  if (anchorFromStart) {
    geo.translate(0, len * 0.5, 0);
  }
  const mat = track(
    new THREE.MeshBasicMaterial({
      color: colorHex,
      transparent: true,
      opacity,
    }),
  );
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.copy(
    anchorFromStart ? a : new THREE.Vector3().addVectors(a, b).multiplyScalar(0.5),
  );
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize());
  return mesh;
}

function createHeroShadowTexture(): THREE.CanvasTexture | null {
  if (typeof document === "undefined") return null;
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  const grad = ctx.createRadialGradient(64, 64, 8, 64, 64, 62);
  grad.addColorStop(0, "rgba(25, 25, 24, 0.14)");
  grad.addColorStop(0.54, "rgba(25, 25, 24, 0.05)");
  grad.addColorStop(1, "rgba(25, 25, 24, 0)");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 128, 128);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.needsUpdate = true;
  return tex;
}

function HeroFallbackSvg() {
  return (
    <svg
      className="axo-v14-hero-fallback-svg"
      viewBox="0 0 600 460"
      role="img"
      aria-label="Khối chóp S.ABCD và thiết diện ngũ giác MENPF"
    >
      <ellipse
        className="axo-v14-svg-contact-halo"
        cx="296"
        cy="346"
        rx="164"
        ry="28"
      />
      <ellipse
        className="axo-v14-svg-contact-core"
        cx="296"
        cy="346"
        rx="112"
        ry="18"
      />

      {/* Satellite 1 (rear upper-right): Wireframe Octahedron + horizontal mid trace */}
      <g opacity="0.86">
        <polygon className="axo-v14-svg-solid-upper" points="502,74 538,108 502,144 466,108" fillOpacity="0.42" />
        <line className="axo-v14-svg-edge-hidden" x1="466" y1="108" x2="538" y2="108" strokeOpacity="0.38" />
        <line className="axo-v14-svg-edge-altitude" x1="484" y1="98" x2="520" y2="98" strokeOpacity="0.7" />
        <line className="axo-v14-svg-edge-altitude" x1="520" y1="98" x2="520" y2="118" strokeOpacity="0.7" />
        <line className="axo-v14-svg-edge-solid" x1="502" y1="74" x2="466" y2="108" strokeWidth="1.25" />
        <line className="axo-v14-svg-edge-solid" x1="502" y1="74" x2="538" y2="108" strokeWidth="1.25" />
        <line className="axo-v14-svg-edge-solid" x1="466" y1="108" x2="502" y2="144" strokeWidth="1.25" />
        <line className="axo-v14-svg-edge-solid" x1="538" y1="108" x2="502" y2="144" strokeWidth="1.25" />
        <line className="axo-v14-svg-edge-solid" x1="502" y1="74" x2="502" y2="144" strokeWidth="1.15" />
      </g>

      {/* Satellite 2 (foreground lower-left): Extracted true-shape pentagon MENPF plate */}
      <g opacity="0.9">
        <ellipse className="axo-v14-svg-contact-halo" cx="86" cy="296" rx="44" ry="11" />
        <polygon
          className="axo-v14-svg-section-poly"
          points="86,216 54,244 68,280 106,276 116,240"
          fillOpacity="0.28"
          strokeWidth="1.65"
        />
        <circle className="axo-v14-svg-seed-dot" cx="86" cy="216" r="2.7" />
        <circle className="axo-v14-svg-section-dot" cx="54" cy="244" r="2.7" />
        <circle className="axo-v14-svg-seed-dot" cx="68" cy="280" r="2.7" />
        <circle className="axo-v14-svg-seed-dot" cx="106" cy="276" r="2.7" />
        <circle className="axo-v14-svg-section-dot" cx="116" cy="240" r="2.7" />
      </g>

      {/* Satellite 3 (midground lower-right): Mini unit cube + oblique regular hexagon slice */}
      <g opacity="0.9">
        <ellipse className="axo-v14-svg-contact-halo" cx="508" cy="368" rx="46" ry="12" />
        <polygon
          className="axo-v14-svg-solid-base"
          points="476,304 508,288 540,304 540,342 508,358 476,342"
          fillOpacity="0.72"
        />
        <polygon
          className="axo-v14-svg-cutting-plane"
          points="492,296 524,296 540,323 524,350 492,350 476,323"
          fillOpacity="0.28"
          strokeWidth="1.25"
        />
        <line className="axo-v14-svg-edge-solid" x1="476" y1="304" x2="508" y2="288" strokeWidth="1.25" />
        <line className="axo-v14-svg-edge-solid" x1="508" y1="288" x2="540" y2="304" strokeWidth="1.25" />
        <line className="axo-v14-svg-edge-solid" x1="540" y1="304" x2="540" y2="342" strokeWidth="1.25" />
        <line className="axo-v14-svg-edge-solid" x1="540" y1="342" x2="508" y2="358" strokeWidth="1.25" />
        <line className="axo-v14-svg-edge-solid" x1="508" y1="358" x2="476" y2="342" strokeWidth="1.25" />
        <line className="axo-v14-svg-edge-solid" x1="476" y1="342" x2="476" y2="304" strokeWidth="1.25" />
      </g>

      {/* Centerpiece Primary Solid: S.ABCD */}
      <polygon
        className="axo-v14-svg-solid-base"
        points="168,334 358,370 436,294 234,274"
      />
      <polygon
        className="axo-v14-svg-solid-lower"
        points="168,334 358,370 436,294 385.5,241 234,178 184.5,271"
      />
      <polygon
        className="axo-v14-svg-solid-upper"
        points="234,82 184.5,271 234,178 385.5,241"
      />

      {/* Hidden back edges & base diagonals + SA altitude */}
      <line className="axo-v14-svg-edge-hidden" x1="234" y1="274" x2="168" y2="334" />
      <line className="axo-v14-svg-edge-hidden" x1="234" y1="274" x2="436" y2="294" />
      <line className="axo-v14-svg-edge-hidden" x1="234" y1="274" x2="358" y2="370" strokeOpacity="0.3" />
      <line className="axo-v14-svg-edge-hidden" x1="168" y1="334" x2="436" y2="294" strokeOpacity="0.3" />
      <line className="axo-v14-svg-edge-altitude" x1="234" y1="82" x2="234" y2="274" />

      {/* Front solid edges */}
      <line className="axo-v14-svg-edge-solid" x1="168" y1="334" x2="358" y2="370" />
      <line className="axo-v14-svg-edge-solid" x1="358" y1="370" x2="436" y2="294" />
      <line className="axo-v14-svg-edge-solid" x1="234" y1="82" x2="168" y2="334" />
      <line className="axo-v14-svg-edge-solid" x1="234" y1="82" x2="358" y2="370" />
      <line className="axo-v14-svg-edge-solid" x1="234" y1="82" x2="436" y2="294" />

      {/* Cutting plane (MNP) */}
      <polygon
        className="axo-v14-svg-cutting-plane"
        points="136,252 400,382 456,246 198,136"
      />

      {/* True planar section pentagon MENPF */}
      <polygon
        className="axo-v14-svg-section-poly"
        points="234,178 184.5,271 263,352 397,332 385.5,241"
      />

      <circle className="axo-v14-svg-vertex-dot" cx="234" cy="82" r="3.4" />
      <circle className="axo-v14-svg-seed-dot" cx="234" cy="178" r="4.0" />
      <circle className="axo-v14-svg-seed-dot" cx="263" cy="352" r="4.0" />
      <circle className="axo-v14-svg-seed-dot" cx="397" cy="332" r="4.0" />
      <circle className="axo-v14-svg-section-dot" cx="184.5" cy="271" r="4.2" />
      <circle className="axo-v14-svg-section-dot" cx="385.5" cy="241" r="4.2" />

      <text className="axo-v14-svg-vertex-text" x="234" y="68">S</text>
      <text className="axo-v14-svg-label-seed" x="218" y="176">M</text>
      <text className="axo-v14-svg-label-seed" x="262" y="372">N</text>
      <text className="axo-v14-svg-label-seed" x="414" y="344">P</text>
      <text className="axo-v14-svg-label-inter" x="168" y="271">E</text>
      <text className="axo-v14-svg-label-inter" x="402" y="238">F</text>
    </svg>
  );
}

function HeroSpatialStage() {
  const shellRef = useRef<HTMLDivElement | null>(null);
  const hostRef = useRef<HTMLDivElement | null>(null);
  const wakeRef = useRef<(() => void) | null>(null);
  const targetTiltRef = useRef({ x: 0, y: 0 });
  const [webglReady, setWebglReady] = useState(false);
  const [contextLost, setContextLost] = useState(false);
  const [beat, setBeat] = useState<HeroStoryboardBeat>("solid-emergence");
  const [callouts, setCallouts] = useState<readonly ProjectedCallout[]>([]);

  const webglAllowed = useMemo(() => {
    if (typeof window === "undefined") return false;
    return !window.location.search.includes("no_webgl=1");
  }, []);

  useEffect(() => {
    const reducedQuery = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    let reducedMotion = Boolean(reducedQuery?.matches);

    const host = hostRef.current;
    if (!host || !webglAllowed) return;

    const canvas = document.createElement("canvas");
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        canvas,
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
      });
    } catch {
      setWebglReady(false);
      return;
    }

    const disposables: TrackedDisposable[] = [];
    const track = <T extends TrackedDisposable>(item: T): T => {
      disposables.push(item);
      return item;
    };

    host.appendChild(canvas);
    setWebglReady(true);

    const width = Math.max(280, host.clientWidth || 560);
    const height = Math.max(260, host.clientHeight || 460);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height, false);
    renderer.setClearColor(0x000000, 0);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(33, width / height, 0.1, 100);
    const gallerySpecs = buildHeroSpatialGallerySpecs();
    const baseCamOffset = new THREE.Vector3(...gallerySpecs.cameraOffset);
    const heroLookTarget = new THREE.Vector3(...gallerySpecs.lookTarget);
    let curAspectSpread = 1;
    const applyHeroCameraFraming = (w: number, h: number) => {
      const aspect = Math.max(0.72, w / Math.max(1, h));
      const scaleDist = aspect < 1.2 ? 1.12 + (1.2 - aspect) * 0.62 : 1.1;
      curAspectSpread = aspect < 1.08 ? Math.max(0.84, 0.84 + (aspect - 0.72) * 0.44) : 1;
      camera.aspect = w / Math.max(1, h);
      camera.position.copy(heroLookTarget).addScaledVector(baseCamOffset, scaleDist);
      camera.lookAt(heroLookTarget);
      camera.updateProjectionMatrix();
    };
    applyHeroCameraFraming(width, height);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.52);
    const keyLight = new THREE.DirectionalLight(0xfffaf2, 1.24);
    keyLight.position.set(12, 15, -6);
    const fillLight = new THREE.DirectionalLight(0xdcebfa, 0.62);
    fillLight.position.set(-10, 5, 10);
    scene.add(ambientLight, keyLight, fillLight);

    const root = new THREE.Group();
    scene.add(root);

    const pMap = LANDING_PYRAMID_SAMPLE.pointMap;
    const vec3 = (id: string) => {
      const p = pMap[id]?.pos ?? [0, 0, 0];
      return new THREE.Vector3(p[0], p[1], p[2]);
    };

    const S = vec3("S");
    const A = vec3("A");
    const B = vec3("B");
    const C = vec3("C");
    const D = vec3("D");
    const M = vec3("M");
    const N = vec3("N");
    const P = vec3("P");
    const E = vec3("E");
    const F = vec3("F");
    const loopPts = LANDING_PYRAMID_SAMPLE.sectionLoop.map(vec3);

    const pyramidCentroid = new THREE.Vector3()
      .add(S)
      .add(A)
      .add(B)
      .add(C)
      .add(D)
      .divideScalar(5);

    const baseCenter = new THREE.Vector3()
      .add(A)
      .add(B)
      .add(C)
      .add(D)
      .divideScalar(4);

    // Orient cutting plane normal from loopPts toward apex S
    const rawPlaneNormal = new THREE.Vector3()
      .subVectors(loopPts[1], loopPts[0])
      .cross(new THREE.Vector3().subVectors(loopPts[2], loopPts[0]))
      .normalize();
    const cutPlaneNormal =
      rawPlaneNormal.dot(new THREE.Vector3().subVectors(S, loopPts[0])) >= 0
        ? rawPlaneNormal
        : rawPlaneNormal.negate();
    const cutPlaneOffset = cutPlaneNormal.dot(loopPts[0]);

    const pyramidFaces = [
      orientFaceOutward([D, C, B, A], pyramidCentroid),
      orientFaceOutward([A, B, S], pyramidCentroid),
      orientFaceOutward([B, C, S], pyramidCentroid),
      orientFaceOutward([C, D, S], pyramidCentroid),
      orientFaceOutward([D, A, S], pyramidCentroid),
    ];

    const lowerFaces: ClippedPolygonFace[] = [];
    const upperFaces: ClippedPolygonFace[] = [];
    for (const face of pyramidFaces) {
      const lo = clipPolygonHalfSpace(face, cutPlaneNormal, cutPlaneOffset, false);
      if (lo.length >= 3) lowerFaces.push({ pts: lo });
      const hi = clipPolygonHalfSpace(face, cutPlaneNormal, cutPlaneOffset, true);
      if (hi.length >= 3) upperFaces.push({ pts: hi });
    }

    // 1. Soft Studio Contact Shadow & Altitude SA perp (ABCD) Right-Angle Witness
    const shadowTex = createHeroShadowTexture();
    if (shadowTex) track(shadowTex);
    const groundShadowGeo = track(new THREE.PlaneGeometry(4.8, 4.2));
    groundShadowGeo.rotateX(-Math.PI / 2);
    const groundShadowMat = track(
      new THREE.MeshBasicMaterial({
        map: shadowTex ?? undefined,
        color: shadowTex ? 0xffffff : 0x191918,
        transparent: true,
        opacity: shadowTex ? 0.94 : 0.06,
        depthWrite: false,
      }),
    );
    const groundShadowMesh = new THREE.Mesh(groundShadowGeo, groundShadowMat);
    groundShadowMesh.position.set(baseCenter.x, A.y - 0.036, baseCenter.z);
    groundShadowMesh.renderOrder = 0;
    root.add(groundShadowMesh);

    const uAB = new THREE.Vector3().subVectors(B, A).normalize().multiplyScalar(0.26);
    const uAS = new THREE.Vector3().subVectors(S, A).normalize().multiplyScalar(0.26);
    const footCorner = A.clone().add(uAB).add(uAS);
    const rightAngle1 = createLineSegment(A.clone().add(uAS), footCorner, 0x0075de, 0.56, false, track);
    const rightAngle2 = createLineSegment(A.clone().add(uAB), footCorner, 0x0075de, 0.56, false, track);
    root.add(rightAngle1, rightAngle2);

    // 2. Unified Pyramid Solid (clean matte architectural facets, crisp front-solid / back-dashed edges)
    const lowerGroup = new THREE.Group();
    const lowerGeo = track(buildFacesBufferGeometry(lowerFaces, 0xf3f0ea));
    const lowerMat = track(
      new THREE.MeshBasicMaterial({
        color: 0xffffff,
        vertexColors: true,
        transparent: true,
        opacity: 0.86,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const lowerMesh = new THREE.Mesh(lowerGeo, lowerMat);
    lowerMesh.renderOrder = 2;
    lowerGroup.add(lowerMesh);

    const baseDiagAC = createLineSegment(A, C, 0x716d69, 0.2, true, track);
    const baseDiagBD = createLineSegment(B, D, 0x716d69, 0.2, true, track);
    baseDiagAC.renderOrder = 2;
    baseDiagBD.renderOrder = 2;
    lowerGroup.add(baseDiagAC, baseDiagBD);

    const faceSpecs = pyramidFaces.map((face) => {
      const e1 = new THREE.Vector3().subVectors(face[1], face[0]);
      const e2 = new THREE.Vector3().subVectors(face[2], face[0]);
      const normal = new THREE.Vector3().crossVectors(e1, e2).normalize();
      const center = face
        .reduce((acc, pt) => acc.add(pt), new THREE.Vector3())
        .divideScalar(face.length);
      return { normal, center };
    });

    const edgeBindings = [
      { id: "AB", a: A, b: B, faces: [0, 1] as const, altitude: false },
      { id: "BC", a: B, b: C, faces: [0, 2] as const, altitude: false },
      { id: "CD", a: C, b: D, faces: [0, 3] as const, altitude: false },
      { id: "DA", a: D, b: A, faces: [0, 4] as const, altitude: false },
      { id: "SA", a: S, b: A, faces: [1, 4] as const, altitude: true },
      { id: "SB", a: S, b: B, faces: [1, 2] as const, altitude: false },
      { id: "SC", a: S, b: C, faces: [2, 3] as const, altitude: false },
      { id: "SD", a: S, b: D, faces: [3, 4] as const, altitude: false },
    ].map((edge) => {
      const solid = createCylinderEdge(edge.a, edge.b, 0.0175, 0x191918, 0.88, track);
      solid.renderOrder = 6;
      const dashed = createLineSegment(
        edge.a,
        edge.b,
        edge.altitude ? 0x0075de : 0x615d59,
        edge.altitude ? 0.56 : 0.44,
        true,
        track,
      );
      dashed.renderOrder = 2;
      lowerGroup.add(solid, dashed);
      return { ...edge, solid, dashed };
    });

    const nodeGeo = track(new THREE.SphereGeometry(0.056, 16, 16));
    const baseNodeMat = track(
      new THREE.MeshBasicMaterial({ color: 0x191918, transparent: true, opacity: 0.9 }),
    );
    const hiddenNodeMat = track(
      new THREE.MeshBasicMaterial({ color: 0x615d59, transparent: true, opacity: 0.45 }),
    );
    for (const pt of [B, D]) {
      const dot = new THREE.Mesh(nodeGeo, baseNodeMat);
      dot.position.copy(pt);
      dot.renderOrder = 8;
      lowerGroup.add(dot);
    }
    const dotA = new THREE.Mesh(nodeGeo, hiddenNodeMat);
    dotA.position.copy(A);
    dotA.scale.setScalar(0.84);
    dotA.renderOrder = 3;
    lowerGroup.add(dotA);
    root.add(lowerGroup);

    // 3. Upper Pyramid Shell (unified seamlessly with lower frustum, no split detachment)
    const upperGroup = new THREE.Group();
    const upperGeo = track(buildFacesBufferGeometry(upperFaces, 0xfaf9f7));
    const upperMat = track(
      new THREE.MeshBasicMaterial({
        color: 0xffffff,
        vertexColors: true,
        transparent: true,
        opacity: 0.14,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const upperMesh = new THREE.Mesh(upperGeo, upperMat);
    upperMesh.renderOrder = 3;
    upperGroup.add(upperMesh);

    const dotS = new THREE.Mesh(nodeGeo, baseNodeMat);
    dotS.position.copy(S);
    dotS.renderOrder = 8;
    const dotC = new THREE.Mesh(nodeGeo, baseNodeMat);
    dotC.position.copy(C);
    dotC.renderOrder = 8;
    upperGroup.add(dotS, dotC);
    root.add(upperGroup);

    // 4. Cutting Plane (MNP) with tightened margin 0.26
    const planeGroup = new THREE.Group();
    const sectionWorldPts: Vec3Tuple[] = loopPts.map((pt) => [pt.x, pt.y, pt.z]);
    const planeQuadVecs = computeBoundedPlaneQuad(sectionWorldPts, [1, 2, -1], 0.26).map(
      (pt) => new THREE.Vector3(pt[0], pt[1], pt[2]),
    );
    const planeCenter = planeQuadVecs
      .reduce((acc, v) => acc.add(v), new THREE.Vector3())
      .divideScalar(Math.max(1, planeQuadVecs.length));
    const localPlane = planeQuadVecs.map((v) => v.clone().sub(planeCenter));
    planeGroup.position.copy(planeCenter);

    const planeGeo = track(buildFacesBufferGeometry([{ pts: localPlane }]));
    const planeMat = track(
      new THREE.MeshBasicMaterial({
        color: 0x62aef0,
        transparent: true,
        opacity: 0.14,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const planeMesh = new THREE.Mesh(planeGeo, planeMat);
    planeMesh.renderOrder = 4;
    planeGroup.add(planeMesh);

    const planeRimCyls: THREE.Mesh[] = [];
    for (let i = 0; i < localPlane.length; i++) {
      const rim = createCylinderEdge(
        localPlane[i],
        localPlane[(i + 1) % localPlane.length],
        0.015,
        0x0075de,
        0.82,
        track,
      );
      rim.renderOrder = 6;
      planeRimCyls.push(rim);
      planeGroup.add(rim);
    }
    root.add(planeGroup);

    // 5. Cross-section Pentagon MENPF (crisp luminous orange over translucent faces)
    const sectionGroup = new THREE.Group();
    const sectionOffsetLoop = loopPts.map((pt) =>
      pt.clone().addScaledVector(cutPlaneNormal, 0.008),
    );
    const secGeo = track(buildFacesBufferGeometry([{ pts: sectionOffsetLoop }]));
    const secMat = track(
      new THREE.MeshStandardMaterial({
        color: 0xed6d14,
        emissive: 0xb24700,
        emissiveIntensity: 0.24,
        roughness: 0.54,
        metalness: 0.02,
        flatShading: true,
        transparent: true,
        opacity: HERO_SECTION_FILL_OPACITY,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const secMesh = new THREE.Mesh(secGeo, secMat);
    secMesh.renderOrder = 5;
    sectionGroup.add(secMesh);

    const secBorderCyls: THREE.Mesh[] = [];
    for (let i = 0; i < sectionOffsetLoop.length; i++) {
      const seg = createCylinderEdge(
        sectionOffsetLoop[i],
        sectionOffsetLoop[(i + 1) % sectionOffsetLoop.length],
        0.025,
        0x793400,
        0.96,
        track,
        true,
      );
      seg.renderOrder = 7;
      secBorderCyls.push(seg);
      sectionGroup.add(seg);
    }

    const seedMat = track(
      new THREE.MeshBasicMaterial({ color: 0x0075de, transparent: true, opacity: 1 }),
    );
    const interMat = track(
      new THREE.MeshBasicMaterial({ color: 0xdd5b00, transparent: true, opacity: 1 }),
    );
    const seedDots = [M, N, P].map((pt) => {
      const dot = new THREE.Mesh(nodeGeo, seedMat);
      dot.position.copy(pt).addScaledVector(cutPlaneNormal, 0.014);
      dot.scale.setScalar(1.06);
      dot.renderOrder = 8;
      root.add(dot);
      return dot;
    });
    const interDots = [E, F].map((pt) => {
      const dot = new THREE.Mesh(nodeGeo, interMat);
      dot.position.copy(pt).addScaledVector(cutPlaneNormal, 0.015);
      dot.scale.setScalar(1.12);
      dot.renderOrder = 8;
      root.add(dot);
      return dot;
    });
    root.add(sectionGroup);

    // 6. Structurally Coupled Ground Companions (extended NP base trace, azimuth datum arc)
    const dirNP = new THREE.Vector3().subVectors(P, N).normalize();
    const extNPStart = N.clone().addScaledVector(dirNP, -0.78);
    const extNPEnd = P.clone().addScaledVector(dirNP, 0.78);
    const extendedTraceLine = createLineSegment(
      extNPStart,
      extNPEnd,
      0x0075de,
      0.42,
      true,
      track,
    );
    extendedTraceLine.renderOrder = 2;
    root.add(extendedTraceLine);

    const orbitArcPts: THREE.Vector3[] = [];
    const orbitRadius = 2.66;
    const orbitStart = -0.44;
    const orbitEnd = 1.02;
    for (let i = 0; i <= 32; i++) {
      const theta = orbitStart + ((orbitEnd - orbitStart) * i) / 32;
      orbitArcPts.push(
        new THREE.Vector3(
          baseCenter.x + Math.cos(theta) * orbitRadius,
          A.y - 0.026,
          baseCenter.z + Math.sin(theta) * orbitRadius,
        ),
      );
    }
    const orbitGeo = track(new THREE.BufferGeometry().setFromPoints(orbitArcPts));
    const orbitMat = track(
      new THREE.LineBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.24 }),
    );
    const orbitArcLine = new THREE.Line(orbitGeo, orbitMat);
    orbitArcLine.renderOrder = 1;
    const orbitNodeMat = track(
      new THREE.MeshBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.56 }),
    );
    const orbitNode = new THREE.Mesh(nodeGeo, orbitNodeMat);
    orbitNode.position.copy(orbitArcPts[orbitArcPts.length - 1]);
    orbitNode.scale.setScalar(0.64);
    orbitNode.renderOrder = 3;
    root.add(orbitArcLine, orbitNode);

    // 6. Concept A: Spatial Geometry Gallery (grounded NP trace + 3 camera-framed Axo satellites)
    const basisRightVec = new THREE.Vector3(...gallerySpecs.basisRight);
    const basisUpVec = new THREE.Vector3(...gallerySpecs.basisUp);
    const basisForwardVec = new THREE.Vector3(...gallerySpecs.basisForward);
    const satellitesRoot = new THREE.Group();
    scene.add(satellitesRoot);

    const satOpacityBindings: {
      readonly mat: THREE.Material & { opacity: number };
      readonly baseOpacity: number;
    }[] = [];
    const registerSatMaterial = <T extends THREE.Material & { opacity: number }>(
      mat: T,
      baseOpacity: number,
    ): T => {
      satOpacityBindings.push({ mat, baseOpacity });
      return mat;
    };
    const createSatLine = (
      a: THREE.Vector3,
      b: THREE.Vector3,
      colorHex: number,
      baseOpacity: number,
      renderOrder: number,
    ) => {
      const line = createLineSegment(a, b, colorHex, baseOpacity, false, track);
      line.renderOrder = renderOrder;
      registerSatMaterial(line.material as THREE.LineBasicMaterial, baseOpacity);
      return line;
    };
    const satBeadGeo = track(new THREE.SphereGeometry(0.028, 12, 12));
    const satAmberDotMat = registerSatMaterial(
      track(new THREE.MeshBasicMaterial({ color: 0xdd5b00, transparent: true, opacity: 0.85 })),
      0.85,
    );
    const satBlueDotMat = registerSatMaterial(
      track(new THREE.MeshBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.88 })),
      0.88,
    );

    // Satellite 0 (rear upper-right): Regular Octahedron + Mid-Section Square
    const octGroup = new THREE.Group();
    const octVecs = gallerySpecs.octahedronVertices.map(([x, y, z]) => new THREE.Vector3(x, y, z));
    const octFaceData: ClippedPolygonFace[] = gallerySpecs.octahedronFaces.map(([i0, i1, i2]) => ({
      pts: [octVecs[i0], octVecs[i1], octVecs[i2]],
    }));
    const octFaceGeo = track(buildFacesBufferGeometry(octFaceData, 0xdcebfa));
    const octFaceMat = registerSatMaterial(
      track(
        new THREE.MeshBasicMaterial({
          color: 0xffffff,
          vertexColors: true,
          transparent: true,
          opacity: 0.22,
          side: THREE.DoubleSide,
          depthWrite: false,
        }),
      ),
      0.22,
    );
    const octFaceMesh = new THREE.Mesh(octFaceGeo, octFaceMat);
    octFaceMesh.renderOrder = 2;
    octGroup.add(octFaceMesh);
    for (const [aIdx, bIdx] of gallerySpecs.octahedronEdges) {
      octGroup.add(createSatLine(octVecs[aIdx], octVecs[bIdx], 0x0075de, 0.56, 4));
    }
    const midRingVecs = gallerySpecs.octahedronMidRing.map(([x, y, z]) => new THREE.Vector3(x, y, z));
    const midRingFillGeo = track(buildFacesBufferGeometry([{ pts: midRingVecs }]));
    const midRingFillMat = registerSatMaterial(
      track(
        new THREE.MeshBasicMaterial({
          color: 0xed6d14,
          transparent: true,
          opacity: 0.28,
          side: THREE.DoubleSide,
          depthWrite: false,
        }),
      ),
      0.28,
    );
    const midRingFillMesh = new THREE.Mesh(midRingFillGeo, midRingFillMat);
    midRingFillMesh.renderOrder = 3;
    octGroup.add(midRingFillMesh);
    for (let i = 0; i < midRingVecs.length; i++) {
      octGroup.add(
        createSatLine(midRingVecs[i], midRingVecs[(i + 1) % midRingVecs.length], 0xdd5b00, 0.72, 5),
      );
      const dot = new THREE.Mesh(satBeadGeo, satAmberDotMat);
      dot.position.copy(midRingVecs[i]);
      dot.renderOrder = 6;
      octGroup.add(dot);
    }
    satellitesRoot.add(octGroup);

    // Satellite 1 (foreground lower-left): Extracted Isometric True-Shape MENPF Plate
    const pentGroup = new THREE.Group();
    const pentVecs = gallerySpecs.extractedPentagonPts.map(
      ([x, y, z]) => new THREE.Vector3(x, y, z),
    );
    const pentFillGeo = track(buildFacesBufferGeometry([{ pts: pentVecs }]));
    const pentFillMat = registerSatMaterial(
      track(
        new THREE.MeshBasicMaterial({
          color: 0xed6d14,
          transparent: true,
          opacity: 0.36,
          side: THREE.DoubleSide,
          depthWrite: false,
        }),
      ),
      0.36,
    );
    const pentFillMesh = new THREE.Mesh(pentFillGeo, pentFillMat);
    pentFillMesh.renderOrder = 3;
    pentGroup.add(pentFillMesh);
    for (let i = 0; i < pentVecs.length; i++) {
      pentGroup.add(
        createSatLine(pentVecs[i], pentVecs[(i + 1) % pentVecs.length], 0x793400, 0.88, 5),
      );
      const isSeedVertex = i === 0 || i === 2 || i === 3;
      const dot = new THREE.Mesh(satBeadGeo, isSeedVertex ? satBlueDotMat : satAmberDotMat);
      dot.position.copy(pentVecs[i]);
      dot.renderOrder = 6;
      pentGroup.add(dot);
    }
    const pentShadowGeo = track(new THREE.PlaneGeometry(0.96, 0.72));
    pentShadowGeo.rotateX(-Math.PI / 2);
    const pentShadowMat = registerSatMaterial(
      track(
        new THREE.MeshBasicMaterial({
          map: shadowTex ?? undefined,
          color: shadowTex ? 0xffffff : 0x191918,
          transparent: true,
          opacity: shadowTex ? 0.56 : 0.04,
          depthWrite: false,
        }),
      ),
      shadowTex ? 0.56 : 0.04,
    );
    const pentShadowMesh = new THREE.Mesh(pentShadowGeo, pentShadowMat);
    pentShadowMesh.position.set(0, -0.44, 0);
    pentShadowMesh.renderOrder = 0;
    pentGroup.add(pentShadowMesh);
    satellitesRoot.add(pentGroup);

    // Satellite 2 (midground lower-right): Mini Cube Sliced by Regular Hexagon (x+y+z=0)
    const cubeGroup = new THREE.Group();
    const cubeVecs = gallerySpecs.cubeVertices.map(([x, y, z]) => new THREE.Vector3(x, y, z));
    for (const [aIdx, bIdx] of gallerySpecs.cubeEdges) {
      cubeGroup.add(createSatLine(cubeVecs[aIdx], cubeVecs[bIdx], 0x615d59, 0.48, 4));
    }
    const hexVecs = gallerySpecs.cubeHexSection.map(([x, y, z]) => new THREE.Vector3(x, y, z));
    const hexFillGeo = track(buildFacesBufferGeometry([{ pts: hexVecs }]));
    const hexFillMat = registerSatMaterial(
      track(
        new THREE.MeshBasicMaterial({
          color: 0xed6d14,
          transparent: true,
          opacity: 0.38,
          side: THREE.DoubleSide,
          depthWrite: false,
        }),
      ),
      0.38,
    );
    const hexFillMesh = new THREE.Mesh(hexFillGeo, hexFillMat);
    hexFillMesh.renderOrder = 3;
    cubeGroup.add(hexFillMesh);
    for (let i = 0; i < hexVecs.length; i++) {
      cubeGroup.add(
        createSatLine(hexVecs[i], hexVecs[(i + 1) % hexVecs.length], 0x793400, 0.86, 5),
      );
      const dot = new THREE.Mesh(satBeadGeo, satAmberDotMat);
      dot.position.copy(hexVecs[i]);
      dot.renderOrder = 6;
      cubeGroup.add(dot);
    }
    const cubeShadowGeo = track(new THREE.PlaneGeometry(1.06, 0.84));
    cubeShadowGeo.rotateX(-Math.PI / 2);
    const cubeShadowMat = registerSatMaterial(
      track(
        new THREE.MeshBasicMaterial({
          map: shadowTex ?? undefined,
          color: shadowTex ? 0xffffff : 0x191918,
          transparent: true,
          opacity: shadowTex ? 0.52 : 0.04,
          depthWrite: false,
        }),
      ),
      shadowTex ? 0.52 : 0.04,
    );
    const cubeShadowMesh = new THREE.Mesh(cubeShadowGeo, cubeShadowMat);
    cubeShadowMesh.position.set(0, -0.48, 0);
    cubeShadowMesh.renderOrder = 0;
    cubeGroup.add(cubeShadowMesh);
    satellitesRoot.add(cubeGroup);

    const satelliteEntries = [
      { group: octGroup, spec: gallerySpecs.satellites[0] },
      { group: pentGroup, spec: gallerySpecs.satellites[1] },
      { group: cubeGroup, spec: gallerySpecs.satellites[2] },
    ] as const;

    const projectAnchors = (
      currentBeat: HeroStoryboardState,
    ): readonly ProjectedCallout[] => {
      const cw = host.clientWidth || width;
      const ch = host.clientHeight || height;
      const tmp = new THREE.Vector3();
      root.updateMatrixWorld(true);
      const specs: {
        id: string;
        label: string;
        role: ProjectedCallout["role"];
        pos: THREE.Vector3;
        lift: number;
        visible: boolean;
      }[] = [
        { id: "S", label: "S", role: "vertex", pos: S, lift: currentBeat.capLift, visible: true },
        { id: "M", label: "M", role: "seed", pos: M, lift: 0, visible: currentBeat.seedReveal > 0.25 },
        { id: "N", label: "N", role: "seed", pos: N, lift: 0, visible: currentBeat.seedReveal > 0.25 },
        { id: "P", label: "P", role: "seed", pos: P, lift: 0, visible: currentBeat.seedReveal > 0.25 },
        { id: "E", label: "E", role: "intersection", pos: E, lift: 0, visible: currentBeat.planeSweep > 0.55 },
        { id: "F", label: "F", role: "intersection", pos: F, lift: 0, visible: currentBeat.planeSweep > 0.55 },
      ];
      tmp.copy(pyramidCentroid);
      root.localToWorld(tmp);
      tmp.project(camera);
      const centerPx = (tmp.x * 0.5 + 0.5) * cw;
      const centerPy = (-tmp.y * 0.5 + 0.5) * ch;

      const candidates = specs.map((sp) => {
        tmp.copy(sp.pos).addScaledVector(cutPlaneNormal, sp.lift);
        root.localToWorld(tmp);
        tmp.project(camera);
        const px = (tmp.x * 0.5 + 0.5) * cw;
        const py = (-tmp.y * 0.5 + 0.5) * ch;
        if (sp.id === "S") {
          return { id: sp.id, x: px, y: py - 20 };
        }
        const dx = px - centerPx;
        const dy = py - centerPy;
        const len = Math.hypot(dx, dy) || 1;
        return {
          id: sp.id,
          x: px + (dx / len) * 18,
          y: py + (dy / len) * 18,
        };
      });
      separateLabelPositions(candidates, cw, ch, 26, 18, 14, 22);
      return specs.map((sp, i) => ({
        id: sp.id,
        label: sp.label,
        role: sp.role,
        x: candidates[i].x,
        y: candidates[i].y,
        visible: sp.visible,
      }));
    };

    let disposed = false;
    let isInView = true;
    let rafId = 0;
    const startMs = performance.now();
    let curTiltX = 0;
    let curTiltY = 0;
    let lastBeat: HeroStoryboardBeat | null = null;
    let calloutTick = 0;

    const applyState = (nowMs: number): boolean => {
      const elapsed = nowMs - startMs;
      const state = evaluateHeroStoryboard(elapsed, reducedMotion);

      if (state.beat !== lastBeat) {
        lastBeat = state.beat;
        setBeat(state.beat);
      }

      const damp = reducedMotion ? 1 : 0.14;
      curTiltX += (targetTiltRef.current.x - curTiltX) * damp;
      curTiltY += (targetTiltRef.current.y - curTiltY) * damp;

      const tmpNormal = new THREE.Vector3();
      const tmpCenter = new THREE.Vector3();
      const tmpToCam = new THREE.Vector3();

      groundShadowMat.opacity = (shadowTex ? 0.94 : 0.06) * state.solidReveal;
      baseNodeMat.opacity = 0.9 * state.solidReveal;
      hiddenNodeMat.opacity = 0.45 * state.solidReveal;
      (rightAngle1.material as THREE.LineBasicMaterial).opacity = 0.56 * state.solidReveal;
      (rightAngle2.material as THREE.LineBasicMaterial).opacity = 0.56 * state.solidReveal;

      root.scale.setScalar(0.95 + 0.05 * state.solidReveal);
      lowerMat.opacity = 0.86 * state.solidReveal;
      upperMat.opacity = 0.18 * state.solidReveal;
      upperGroup.position.set(0, 0, 0);
      (baseDiagAC.material as THREE.LineDashedMaterial).opacity = 0.2 * state.solidReveal;
      (baseDiagBD.material as THREE.LineDashedMaterial).opacity = 0.2 * state.solidReveal;

      (extendedTraceLine.material as THREE.LineDashedMaterial).opacity =
        0.42 * state.planeSweep;
      extendedTraceLine.visible = state.planeSweep > 0.06;
      orbitMat.opacity = 0.24 * state.solidReveal;
      orbitNodeMat.opacity = 0.56 * state.solidReveal;

      for (const binding of satOpacityBindings) {
        binding.mat.opacity = binding.baseOpacity * state.satelliteReveal;
      }
      const satScale = 0.84 + 0.16 * state.satelliteReveal;
      const satDrop = (1 - state.satelliteReveal) * 0.18;
      for (const entry of satelliteEntries) {
        const sp = entry.spec;
        entry.group.visible = state.satelliteReveal > 0.01;
        entry.group.scale.setScalar(satScale);
        entry.group.position
          .copy(heroLookTarget)
          .addScaledVector(basisRightVec, sp.screenDx * curAspectSpread)
          .addScaledVector(basisUpVec, sp.screenDy - satDrop)
          .addScaledVector(basisForwardVec, sp.screenDz);
        entry.group.rotation.set(
          sp.rotation[0] + curTiltY * sp.parallaxFactor,
          sp.rotation[1] - state.orbitOffsetRad * 0.45 + curTiltX * sp.parallaxFactor,
          sp.rotation[2],
        );
      }

      seedMat.opacity = state.seedReveal;
      for (const d of seedDots) {
        d.visible = state.seedReveal > 0.05;
        d.scale.setScalar(Math.max(0.05, 1.06 * state.seedReveal));
      }

      planeMat.opacity = 0.2 * state.planeSweep;
      planeGroup.position
        .copy(planeCenter)
        .addScaledVector(cutPlaneNormal, (1 - state.planeSweep) * 0.55);
      for (const rim of planeRimCyls) {
        (rim.material as THREE.MeshBasicMaterial).opacity = 0.78 * state.planeSweep;
      }

      interMat.opacity = state.planeSweep;
      for (const d of interDots) {
        d.visible = state.planeSweep > 0.35;
        d.scale.setScalar(Math.max(0.05, 1.12 * state.planeSweep));
      }

      for (let i = 0; i < secBorderCyls.length; i++) {
        const seg = secBorderCyls[i];
        const edgeStart = i / secBorderCyls.length;
        const edgeEnd = (i + 1) / secBorderCyls.length;
        const localP = clamp01((state.traceProgress - edgeStart) / (edgeEnd - edgeStart));
        seg.visible = localP > 0.01;
        seg.scale.set(1, Math.max(0.01, localP), 1);
        (seg.material as THREE.MeshBasicMaterial).opacity = 0.96 * Math.min(1, localP * 2);
      }

      secMat.opacity = HERO_SECTION_FILL_OPACITY * state.sectionFill;
      secMesh.visible = state.sectionFill > 0.01;

      root.rotation.y = 0.06 - state.orbitOffsetRad + curTiltX;
      root.rotation.x = 0.02 + curTiltY;
      root.updateMatrixWorld(true);

      const frontFacing = faceSpecs.map((fs) => {
        tmpNormal.copy(fs.normal).transformDirection(root.matrixWorld);
        tmpCenter.copy(fs.center).applyMatrix4(root.matrixWorld);
        tmpToCam.copy(camera.position).sub(tmpCenter);
        return tmpNormal.dot(tmpToCam) > 0;
      });

      for (const edge of edgeBindings) {
        const isFrontEdge = frontFacing[edge.faces[0]] || frontFacing[edge.faces[1]];
        edge.solid.visible = isFrontEdge;
        edge.dashed.visible = !isFrontEdge;
        if (isFrontEdge) {
          (edge.solid.material as THREE.MeshBasicMaterial).opacity = 0.88 * state.solidReveal;
        } else {
          (edge.dashed.material as THREE.LineDashedMaterial).opacity =
            (edge.altitude ? 0.56 : 0.44) * state.solidReveal;
        }
      }

      renderer.render(scene, camera);

      const tiltDone =
        Math.abs(targetTiltRef.current.x - curTiltX) < 0.0008 &&
        Math.abs(targetTiltRef.current.y - curTiltY) < 0.0008;
      const done = state.settled && tiltDone;

      if (calloutTick % 3 === 0 || done || reducedMotion) {
        setCallouts(projectAnchors(state));
      }
      calloutTick++;

      return done;
    };

    const tick = (nowMs: number) => {
      if (disposed || !isInView || document.hidden) {
        rafId = 0;
        return;
      }
      const done = applyState(nowMs);
      if (!done && !reducedMotion) {
        rafId = window.requestAnimationFrame(tick);
      } else {
        rafId = 0;
      }
    };

    const wake = () => {
      if (disposed || !isInView || document.hidden) return;
      if (reducedMotion) {
        applyState(performance.now());
        return;
      }
      if (rafId === 0) {
        rafId = window.requestAnimationFrame(tick);
      }
    };

    wakeRef.current = wake;

    const ro =
      typeof ResizeObserver !== "undefined"
        ? new ResizeObserver(() => {
            if (disposed || !host) return;
            const w = Math.max(260, host.clientWidth);
            const h = Math.max(240, host.clientHeight);
            applyHeroCameraFraming(w, h);
            renderer.setSize(w, h, false);
            wake();
          })
        : null;
    ro?.observe(host);

    const io =
      typeof IntersectionObserver !== "undefined"
        ? new IntersectionObserver(
            (entries) => {
              const entry = entries[0];
              isInView = Boolean(entry?.isIntersecting);
              if (isInView) {
                wake();
              } else if (rafId) {
                window.cancelAnimationFrame(rafId);
                rafId = 0;
              }
            },
            { threshold: 0.06 },
          )
        : null;
    if (shellRef.current) io?.observe(shellRef.current);

    const onVisibility = () => {
      if (!document.hidden && isInView) wake();
      else if (document.hidden && rafId) {
        window.cancelAnimationFrame(rafId);
        rafId = 0;
      }
    };
    document.addEventListener("visibilitychange", onVisibility);

    const onMotionChange = (ev: MediaQueryListEvent) => {
      reducedMotion = ev.matches;
      if (reducedMotion && rafId) {
        window.cancelAnimationFrame(rafId);
        rafId = 0;
      }
      wake();
    };
    reducedQuery?.addEventListener?.("change", onMotionChange);

    const onContextLost = (e: Event) => {
      e.preventDefault();
      setContextLost(true);
      if (rafId) {
        window.cancelAnimationFrame(rafId);
        rafId = 0;
      }
    };
    const onContextRestored = () => {
      setContextLost(false);
      wake();
    };
    canvas.addEventListener("webglcontextlost", onContextLost);
    canvas.addEventListener("webglcontextrestored", onContextRestored);

    applyState(performance.now());
    if (!reducedMotion) {
      wake();
    }

    return () => {
      disposed = true;
      wakeRef.current = null;
      if (rafId) {
        window.cancelAnimationFrame(rafId);
      }
      ro?.disconnect();
      io?.disconnect();
      document.removeEventListener("visibilitychange", onVisibility);
      reducedQuery?.removeEventListener?.("change", onMotionChange);
      canvas.removeEventListener("webglcontextlost", onContextLost);
      canvas.removeEventListener("webglcontextrestored", onContextRestored);
      for (const item of disposables) {
        item.dispose();
      }
      renderer.dispose();
      if (canvas.parentElement === host) {
        host.removeChild(canvas);
      }
    };
  }, [webglAllowed]);

  const handlePointerMove = useCallback((e: ReactPointerEvent<HTMLDivElement>) => {
    if (e.pointerType === "touch") return;
    const rect = shellRef.current?.getBoundingClientRect();
    if (!rect || rect.width <= 0 || rect.height <= 0) return;
    targetTiltRef.current = {
      x: ((e.clientX - rect.left) / rect.width - 0.5) * 0.14,
      y: -((e.clientY - rect.top) / rect.height - 0.5) * 0.09,
    };
    wakeRef.current?.();
  }, []);

  const handlePointerLeave = useCallback(() => {
    targetTiltRef.current = { x: 0, y: 0 };
    wakeRef.current?.();
  }, []);

  return (
    <div
      id="landing-hero-sculpture"
      ref={shellRef}
      className="axo-v14-hero-visual"
      data-hero-beat={beat}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
      aria-label="Minh họa khối chóp S.ABCD và thiết diện ngũ giác MENPF"
    >
      <div
        ref={hostRef}
        className={
          webglAllowed && webglReady && !contextLost
            ? "axo-v14-hero-canvas-host"
            : "axo-v14-hero-canvas-host is-hidden"
        }
      />

      {webglAllowed && webglReady && !contextLost && callouts.length > 0 && (
        <svg className="axo-v14-hero-callouts" aria-hidden="true" focusable="false">
          {callouts.map((c) =>
            c.visible ? (
              <text
                key={c.id}
                x={c.x.toFixed(1)}
                y={c.y.toFixed(1)}
                className={
                  c.role === "intersection"
                    ? "axo-v14-svg-label-inter"
                    : c.role === "seed"
                      ? "axo-v14-svg-label-seed"
                      : c.role === "aux"
                        ? "axo-v14-svg-label-aux"
                        : "axo-v14-svg-vertex-text"
                }
              >
                {c.label}
              </text>
            ) : null,
          )}
        </svg>
      )}

      {(!webglAllowed || !webglReady || contextLost) && <HeroFallbackSvg />}
    </div>
  );
}

export function LandingHeroV14() {
  const user = useAuthStore((s) => s.user);

  const handleStoryScroll = useCallback((e: ReactMouseEvent<HTMLAnchorElement>) => {
    const target = document.getElementById("cach-hoat-dong");
    if (!target) return;
    e.preventDefault();
    const reduced =
      typeof window !== "undefined" &&
      Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches);
    target.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
  }, []);

  return (
    <section
      id="landing-hero"
      className="axo-v14-hero"
      aria-labelledby="axo-v14-hero-heading"
    >
      <div className="axo-v14-hero-shell">
        <div className="axo-v14-hero-copy">
          <h1 id="axo-v14-hero-heading" className="axo-v14-hero-title">
            <span className="axo-v14-hero-title-line">Hình học không gian,{" "}</span>
            <span className="axo-v14-hero-title-line">
              dễ{" "}
              <span className="axo-v14-hero-phrase-keep">
                <AnnotatedPhrase variant="circle">hình dung</AnnotatedPhrase> hơn.
              </span>
            </span>
          </h1>
          <p className="axo-v14-hero-lead">
            Nhập đề bài tiếng Việt để quan sát khối đa diện 3D chính xác, mặt
            phẳng cắt và từng đường giao tuyến ngay trong không gian trực quan.
          </p>
          <div className="axo-v14-hero-actions">
            <button
              id="btn-landing-hero-start"
              type="button"
              className="axo-v14-btn axo-v14-btn-primary"
              onClick={enterAxoWorkspace}
            >
              {user ? "Vào ứng dụng" : "Bắt đầu dựng hình"}
            </button>
            <a
              id="btn-landing-hero-story"
              href="#cach-hoat-dong"
              className="axo-v14-btn axo-v14-btn-secondary"
              onClick={handleStoryScroll}
            >
              Xem cách hoạt động
            </a>
          </div>
        </div>

        <HeroSpatialStage />
      </div>
    </section>
  );
}
