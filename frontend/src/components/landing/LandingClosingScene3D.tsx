import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { computeBoundedPlaneQuad, type Vec3Tuple } from "./landing-geometry-data";

export const CLOSING_STORYBOARD_MS = 3600;
export const CLOSING_SECTION_FILL_OPACITY = 0.56;
export const CLOSING_PRISM_RADIUS = 1.62;
export const CLOSING_PRISM_HEIGHT = 2.88;

export type ClosingStoryboardBeat =
  | "prism-emergence"
  | "cutting-plane"
  | "intersection-trace"
  | "exploration-settled";

export interface ClosingStoryboardState {
  readonly beat: ClosingStoryboardBeat;
  readonly progress: number;
  readonly solidReveal: number;
  readonly seedScale: number;
  readonly planeOpacity: number;
  readonly traceProgress: number;
  readonly sectionFillOpacity: number;
  readonly intersectionScale: number;
  readonly capLift: number;
  readonly orbitOffsetRad: number;
  readonly settled: boolean;
  readonly reducedMotion: boolean;
}

export interface ClosingCompositionData {
  readonly prismBottomVertices: readonly Vec3Tuple[];
  readonly prismTopVertices: readonly Vec3Tuple[];
  readonly sectionVertices: readonly Vec3Tuple[];
  readonly planeNormal: Vec3Tuple;
  readonly planeOffset: number;
  readonly planarResiduals: readonly number[];
  readonly baseRadiusResiduals: readonly number[];
  readonly lowerFrustumFaceCount: number;
  readonly upperCapFaceCount: number;
  readonly companionCount: number;
}

interface ClippedPolygonFace {
  readonly pts: THREE.Vector3[];
}

interface TrackedDisposable {
  dispose(): void;
}

const UP_AXIS = new THREE.Vector3(0, 1, 0);
const PLANE_RAW_NORMAL: Vec3Tuple = [0.32, 0.91, -0.26];
const PLANE_RAW_OFFSET = 0.12;
const KEY_DIR = new THREE.Vector3(6.8, 11.4, -4.6).normalize();
const RIM_DIR = new THREE.Vector3(-8.2, 4.2, 6.8).normalize();

function clamp01(v: number): number {
  if (!Number.isFinite(v)) return 0;
  return Math.max(0, Math.min(1, v));
}

function easeOutCubic(value: number, start: number, end: number): number {
  if (value <= start) return 0;
  if (value >= end) return 1;
  const u = (value - start) / Math.max(1e-6, end - start);
  return 1 - Math.pow(1 - u, 3);
}

export function evaluateClosingStoryboard(
  elapsedMs: number,
  reducedMotion = false,
): ClosingStoryboardState {
  if (reducedMotion || elapsedMs >= CLOSING_STORYBOARD_MS) {
    return {
      beat: "exploration-settled",
      progress: 1,
      solidReveal: 1,
      seedScale: 1,
      planeOpacity: 1,
      traceProgress: 1,
      sectionFillOpacity: 1,
      intersectionScale: 1,
      capLift: 0.22,
      orbitOffsetRad: 0,
      settled: true,
      reducedMotion,
    };
  }

  const p = clamp01(elapsedMs / CLOSING_STORYBOARD_MS);
  const solidReveal = easeOutCubic(p, 0, 0.24);
  const seedScale = easeOutCubic(p, 0.1, 0.36);
  const planeOpacity = easeOutCubic(p, 0.24, 0.54);
  const traceProgress = easeOutCubic(p, 0.44, 0.84);
  const sectionFillOpacity = easeOutCubic(p, 0.68, 0.96);
  const intersectionScale = easeOutCubic(p, 0.48, 0.78);
  const capLift = 0.22 * easeOutCubic(p, 0.58, 0.94);
  const orbitOffsetRad = (1 - Math.pow(1 - p, 2)) * 0.095 - 0.095;

  let beat: ClosingStoryboardBeat = "prism-emergence";
  if (p >= 0.84) {
    beat = "exploration-settled";
  } else if (p >= 0.44) {
    beat = "intersection-trace";
  } else if (p >= 0.24) {
    beat = "cutting-plane";
  }

  return {
    beat,
    progress: p,
    solidReveal,
    seedScale,
    planeOpacity,
    traceProgress,
    sectionFillOpacity,
    intersectionScale,
    capLift,
    orbitOffsetRad,
    settled: false,
    reducedMotion: false,
  };
}

function buildHexPrismModel() {
  const halfH = CLOSING_PRISM_HEIGHT * 0.5;
  const angleOffset = 0.26;
  const bottomPts: THREE.Vector3[] = [];
  const topPts: THREE.Vector3[] = [];

  for (let i = 0; i < 6; i++) {
    const theta = angleOffset + (i * Math.PI) / 3;
    const x = Math.cos(theta) * CLOSING_PRISM_RADIUS;
    const z = Math.sin(theta) * CLOSING_PRISM_RADIUS;
    bottomPts.push(new THREE.Vector3(x, -halfH, z));
    topPts.push(new THREE.Vector3(x, halfH, z));
  }

  const cutNormal = new THREE.Vector3(...PLANE_RAW_NORMAL).normalize();
  const normLen = Math.hypot(...PLANE_RAW_NORMAL) || 1;
  const cutOffset = PLANE_RAW_OFFSET / normLen;

  const sectionPts: THREE.Vector3[] = [];
  for (let i = 0; i < 6; i++) {
    const b = bottomPts[i];
    const t = topPts[i];
    const db = b.dot(cutNormal) - cutOffset;
    const dt = t.dot(cutNormal) - cutOffset;
    const u = db / (db - dt || 1);
    sectionPts.push(new THREE.Vector3().lerpVectors(b, t, clamp01(u)));
  }

  return { bottomPts, topPts, sectionPts, cutNormal, cutOffset };
}

function clipPolygonHalfSpace(
  poly: readonly THREE.Vector3[],
  normal: THREE.Vector3,
  offset: number,
  keepPositive: boolean,
): THREE.Vector3[] {
  const out: THREE.Vector3[] = [];
  const eps = 1e-6;
  const dist = (v: THREE.Vector3) => {
    const d = v.dot(normal) - offset;
    return keepPositive ? d : -d;
  };

  for (let i = 0; i < poly.length; i++) {
    const curr = poly[i];
    const next = poly[(i + 1) % poly.length];
    const dc = dist(curr);
    const dn = dist(next);
    const currIn = dc >= -eps;
    const nextIn = dn >= -eps;

    if (currIn && nextIn) {
      out.push(next.clone());
    } else if (currIn && !nextIn) {
      const t = dc / (dc - dn || 1);
      out.push(new THREE.Vector3().lerpVectors(curr, next, clamp01(t)));
    } else if (!currIn && nextIn) {
      const t = dc / (dc - dn || 1);
      out.push(new THREE.Vector3().lerpVectors(curr, next, clamp01(t)));
      out.push(next.clone());
    }
  }

  const deduped: THREE.Vector3[] = [];
  for (const pt of out) {
    if (
      deduped.length === 0 ||
      deduped[deduped.length - 1].distanceToSquared(pt) > 1e-8
    ) {
      deduped.push(pt);
    }
  }
  if (
    deduped.length >= 2 &&
    deduped[0].distanceToSquared(deduped[deduped.length - 1]) < 1e-8
  ) {
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

function buildHexPrismFaces(
  bottomPts: readonly THREE.Vector3[],
  topPts: readonly THREE.Vector3[],
): THREE.Vector3[][] {
  const centroid = new THREE.Vector3(0, 0, 0);
  const rawFaces: THREE.Vector3[][] = [
    orientFaceOutward([...bottomPts].reverse(), centroid),
    orientFaceOutward([...topPts], centroid),
  ];
  for (let i = 0; i < 6; i++) {
    const next = (i + 1) % 6;
    rawFaces.push(
      orientFaceOutward(
        [bottomPts[i], bottomPts[next], topPts[next], topPts[i]],
        centroid,
      ),
    );
  }
  return rawFaces;
}

export function buildClosingCompositionData(): ClosingCompositionData {
  const { bottomPts, topPts, sectionPts, cutNormal, cutOffset } =
    buildHexPrismModel();
  const prismBottomVertices: Vec3Tuple[] = bottomPts.map((v) => [v.x, v.y, v.z]);
  const prismTopVertices: Vec3Tuple[] = topPts.map((v) => [v.x, v.y, v.z]);
  const sectionVertices: Vec3Tuple[] = sectionPts.map((v) => [v.x, v.y, v.z]);

  const planarResiduals = sectionPts.map((pt) =>
    Math.abs(pt.dot(cutNormal) - cutOffset),
  );
  const baseRadiusResiduals = bottomPts.map((pt) =>
    Math.abs(Math.hypot(pt.x, pt.z) - CLOSING_PRISM_RADIUS),
  );

  const rawFaces = buildHexPrismFaces(bottomPts, topPts);
  let lowerFrustumFaceCount = 0;
  let upperCapFaceCount = 0;
  for (const face of rawFaces) {
    if (clipPolygonHalfSpace(face, cutNormal, cutOffset, false).length >= 3) {
      lowerFrustumFaceCount++;
    }
    if (clipPolygonHalfSpace(face, cutNormal, cutOffset, true).length >= 3) {
      upperCapFaceCount++;
    }
  }

  return {
    prismBottomVertices,
    prismTopVertices,
    sectionVertices,
    planeNormal: [cutNormal.x, cutNormal.y, cutNormal.z],
    planeOffset: cutOffset,
    planarResiduals,
    baseRadiusResiduals,
    lowerFrustumFaceCount,
    upperCapFaceCount,
    companionCount: 3,
  };
}

export interface ClosingExtractedVertex2D {
  readonly index: number;
  readonly x: number;
  readonly y: number;
}

export interface ClosingExtractedHexagon2D {
  readonly vertices: readonly ClosingExtractedVertex2D[];
  readonly edgeLengths3D: readonly number[];
  readonly edgeLengths2D: readonly number[];
  readonly maxDeviation: number;
}

/**
 * Isometric 2D projection of the oblique hexagonal section onto plane Pi.
 * Preserves all 6 3D edge lengths without perspective foreshortening.
 */
export function computeClosingExtractedHexagon2D(): ClosingExtractedHexagon2D {
  const { sectionPts, cutNormal } = buildHexPrismModel();
  if (sectionPts.length < 3) {
    return { vertices: [], edgeLengths3D: [], edgeLengths2D: [], maxDeviation: 0 };
  }

  const centroid = sectionPts
    .reduce((acc, p) => acc.add(p), new THREE.Vector3())
    .divideScalar(sectionPts.length);

  const e1 = new THREE.Vector3().subVectors(sectionPts[0], centroid).normalize();
  const e2 = new THREE.Vector3().crossVectors(cutNormal, e1).normalize();

  const vertices: ClosingExtractedVertex2D[] = sectionPts.map((pt, index) => {
    const rel = new THREE.Vector3().subVectors(pt, centroid);
    return {
      index,
      x: rel.dot(e1),
      y: rel.dot(e2),
    };
  });

  const edgeLengths3D: number[] = [];
  const edgeLengths2D: number[] = [];
  let maxDeviation = 0;

  for (let i = 0; i < sectionPts.length; i++) {
    const j = (i + 1) % sectionPts.length;
    const d3 = sectionPts[i].distanceTo(sectionPts[j]);
    const d2 = Math.hypot(vertices[j].x - vertices[i].x, vertices[j].y - vertices[i].y);
    edgeLengths3D.push(d3);
    edgeLengths2D.push(d2);
    maxDeviation = Math.max(maxDeviation, Math.abs(d3 - d2));
  }

  return { vertices, edgeLengths3D, edgeLengths2D, maxDeviation };
}

function createClosingContactTexture(): THREE.CanvasTexture | null {
  if (typeof document === "undefined") return null;
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  const grad = ctx.createRadialGradient(128, 128, 14, 128, 128, 124);
  grad.addColorStop(0, "rgba(31, 32, 30, 0.15)");
  grad.addColorStop(0.45, "rgba(31, 32, 30, 0.05)");
  grad.addColorStop(1, "rgba(31, 32, 30, 0)");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 256, 256);
  const tex = new THREE.CanvasTexture(canvas);
  tex.needsUpdate = true;
  return tex;
}

function buildFacesBufferGeometry(
  faces: readonly ClippedPolygonFace[],
  baseColorHex?: number,
): THREE.BufferGeometry {
  const positions: number[] = [];
  const colors: number[] = [];
  const baseColor = baseColorHex !== undefined ? new THREE.Color(baseColorHex) : null;
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
        const key = Math.max(0, triNormal.dot(KEY_DIR)) * 0.28;
        const rim = Math.max(0, triNormal.dot(RIM_DIR)) * 0.12;
        const t = clamp01(0.18 + key * 1.6 + rim * 1.2);
        // Cool sky-slate shade -> warm porcelain lit so facets detach cleanly on stone-paper ground
        const r = Math.min(1, baseColor.r * (0.84 + 0.16 * t));
        const g = Math.min(1, baseColor.g * (0.88 + 0.116 * t));
        const b = Math.min(1, baseColor.b * (0.94 + 0.048 * t));
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

function createCylinderEdge(
  a: THREE.Vector3,
  b: THREE.Vector3,
  radius: number,
  colorHex: number,
  opacity: number,
  track: <T extends TrackedDisposable>(item: T) => T,
  anchorStart = false,
): THREE.Mesh {
  const dir = new THREE.Vector3().subVectors(b, a);
  const len = Math.max(0.001, dir.length());
  const geo = track(new THREE.CylinderGeometry(radius, radius, len, 10, 1));
  if (anchorStart) {
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
    anchorStart ? a : new THREE.Vector3().addVectors(a, b).multiplyScalar(0.5),
  );
  mesh.quaternion.setFromUnitVectors(UP_AXIS, dir.normalize());
  return mesh;
}

function createDashedEdge(
  a: THREE.Vector3,
  b: THREE.Vector3,
  colorHex: number,
  opacity: number,
  dashSize: number,
  gapSize: number,
  track: <T extends TrackedDisposable>(item: T) => T,
): THREE.Line {
  const geo = track(new THREE.BufferGeometry().setFromPoints([a, b]));
  const mat = track(
    new THREE.LineDashedMaterial({
      color: colorHex,
      transparent: true,
      opacity,
      dashSize,
      gapSize,
    }),
  );
  const line = new THREE.Line(geo, mat);
  line.computeLineDistances();
  return line;
}

function ClosingFallbackSvg({ state }: { readonly state: ClosingStoryboardState }) {
  const dy = -12 * (state.capLift / 0.22);
  return (
    <svg
      className="axo-v14-closing-fallback-svg"
      viewBox="0 0 540 420"
      role="img"
      aria-label="Mô hình không gian lăng trụ lục giác đều cắt bởi mặt phẳng nghiên cứu"
    >
      <ellipse
        className="axo-v14-svg-contact-halo"
        cx="270"
        cy="340"
        rx="168"
        ry="34"
      />
      <ellipse
        className="axo-v14-svg-contact-core"
        cx="270"
        cy="340"
        rx="118"
        ry="24"
      />
      {/* Companion 1: Circumscribed radius-R base ring & azimuth arc */}
      <ellipse
        className="axo-v14-svg-edge-altitude"
        cx="270"
        cy="326"
        rx="126"
        ry="32"
        fill="none"
        strokeOpacity="0.34"
      />
      {/* Companion 3: Coaxial base-plane orthographic projection of section hexagon */}
      <polygon
        className="axo-v14-svg-section-poly"
        points="160,322 214,352 326,352 380,322 326,294 214,294"
        fillOpacity={0.14 * state.sectionFillOpacity}
        strokeWidth="1.25"
        strokeOpacity={0.42 * state.sectionFillOpacity}
      />

      {/* Companion 3: Extracted isometric 2D oblique hexagon in upper-right depth */}
      <g opacity={0.78 * state.sectionFillOpacity}>
        <polygon
          className="axo-v14-svg-section-poly"
          points="446,74 478,66 498,90 484,118 450,124 432,100"
          fillOpacity="0.28"
          strokeWidth="1.35"
        />
        <circle className="axo-v14-svg-seed-dot" cx="446" cy="74" r="2.3" />
        <circle className="axo-v14-svg-section-dot" cx="478" cy="66" r="2.3" />
        <circle className="axo-v14-svg-section-dot" cx="498" cy="90" r="2.3" />
        <circle className="axo-v14-svg-seed-dot" cx="484" cy="118" r="2.3" />
        <circle className="axo-v14-svg-section-dot" cx="450" cy="124" r="2.3" />
        <circle className="axo-v14-svg-seed-dot" cx="432" cy="100" r="2.3" />
      </g>

      {/* Base hexagon */}
      <polygon
        className="axo-v14-svg-solid-base"
        points="160,322 214,352 326,352 380,322 326,294 214,294"
      />
      {/* Lower shaded prism frustum */}
      <polygon
        className="axo-v14-svg-solid-lower"
        points="160,322 214,352 326,352 380,322 380,192 326,174 214,200 160,236"
      />

      {/* Hidden back lower prism edges & central symmetry axis OO' */}
      <line className="axo-v14-svg-edge-hidden" x1="160" y1="322" x2="214" y2="294" />
      <line className="axo-v14-svg-edge-hidden" x1="214" y1="294" x2="326" y2="294" />
      <line className="axo-v14-svg-edge-hidden" x1="326" y1="294" x2="380" y2="322" />
      <line className="axo-v14-svg-edge-altitude" x1="270" y1="322" x2="270" y2="104" />

      {/* Lower front prism edges */}
      <line className="axo-v14-svg-edge-solid" x1="160" y1="322" x2="214" y2="352" />
      <line className="axo-v14-svg-edge-solid" x1="214" y1="352" x2="326" y2="352" />
      <line className="axo-v14-svg-edge-solid" x1="326" y1="352" x2="380" y2="322" />
      <line className="axo-v14-svg-edge-solid" x1="160" y1="236" x2="160" y2="322" />
      <line className="axo-v14-svg-edge-solid" x1="214" y1="254" x2="214" y2="352" />
      <line className="axo-v14-svg-edge-solid" x1="326" y1="226" x2="326" y2="352" />
      <line className="axo-v14-svg-edge-solid" x1="380" y1="192" x2="380" y2="322" />

      {/* Exploration plane */}
      <polygon
        className="axo-v14-svg-cutting-plane"
        points="116,256 410,192 436,144 142,208"
        opacity={state.planeOpacity}
      />

      {/* Companion 2: Plane normal vector & perpendicular foot on Pi */}
      <line
        className="axo-v14-svg-edge-altitude"
        x1="270"
        y1="214"
        x2="246"
        y2="152"
        strokeOpacity="0.72"
      />
      <path
        className="axo-v14-svg-edge-altitude"
        d="M 284 210 L 279 198 L 265 202"
        fill="none"
        strokeOpacity="0.65"
      />

      {/* Oblique 6-vertex hexagonal section */}
      <polygon
        className="axo-v14-svg-section-poly"
        points="160,236 214,254 326,226 380,192 326,174 214,200"
        fillOpacity={CLOSING_SECTION_FILL_OPACITY * state.sectionFillOpacity}
      />

      {/* Axial lifted upper cap */}
      <g transform={`translate(0 ${dy.toFixed(1)})`}>
        <polygon
          className="axo-v14-svg-solid-upper"
          points="160,236 214,254 326,226 380,192 380,104 326,76 214,76 160,104"
        />
        <line className="axo-v14-svg-edge-hidden" x1="214" y1="200" x2="214" y2="76" />
        <line className="axo-v14-svg-edge-hidden" x1="326" y1="174" x2="326" y2="76" />
        <line className="axo-v14-svg-edge-solid" x1="160" y1="104" x2="214" y2="132" />
        <line className="axo-v14-svg-edge-solid" x1="214" y1="132" x2="326" y2="132" />
        <line className="axo-v14-svg-edge-solid" x1="326" y1="132" x2="380" y2="104" />
        <line className="axo-v14-svg-edge-solid" x1="160" y1="104" x2="214" y2="76" />
        <line className="axo-v14-svg-edge-solid" x1="214" y1="76" x2="326" y2="76" />
        <line className="axo-v14-svg-edge-solid" x1="326" y1="76" x2="380" y2="104" />
        <line className="axo-v14-svg-edge-solid" x1="160" y1="104" x2="160" y2="236" />
        <line className="axo-v14-svg-edge-solid" x1="214" y1="132" x2="214" y2="254" />
        <line className="axo-v14-svg-edge-solid" x1="326" y1="132" x2="326" y2="226" />
        <line className="axo-v14-svg-edge-solid" x1="380" y1="104" x2="380" y2="192" />
      </g>

      <circle className="axo-v14-svg-seed-dot" cx="160" cy="236" r="4.0" />
      <circle className="axo-v14-svg-section-dot" cx="214" cy="254" r="4.1" />
      <circle className="axo-v14-svg-section-dot" cx="326" cy="226" r="4.1" />
      <circle className="axo-v14-svg-seed-dot" cx="380" cy="192" r="4.0" />
      <circle className="axo-v14-svg-section-dot" cx="326" cy="174" r="4.1" />
      <circle className="axo-v14-svg-seed-dot" cx="214" cy="200" r="4.0" />
    </svg>
  );
}

function shouldAttemptWebGL(): boolean {
  if (typeof window === "undefined" || typeof document === "undefined") return false;
  if (window.location.search.includes("no_webgl=1")) return false;
  return typeof window.WebGLRenderingContext !== "undefined";
}

export function LandingClosingScene3D() {
  const stageRef = useRef<HTMLDivElement | null>(null);
  const hostRef = useRef<HTMLDivElement | null>(null);
  const targetTiltRef = useRef({ x: 0, y: 0 });
  const wakeRef = useRef<(() => void) | null>(null);

  const [webglAllowed, setWebglAllowed] = useState(true);
  const [webglReady, setWebglReady] = useState(false);
  const [contextLost, setContextLost] = useState(false);
  const [beatLabel, setBeatLabel] =
    useState<ClosingStoryboardBeat>("prism-emergence");

  const fallbackState = useMemo(
    () => evaluateClosingStoryboard(CLOSING_STORYBOARD_MS, true),
    [],
  );

  useEffect(() => {
    const stage = stageRef.current;
    const host = hostRef.current;
    if (!stage || !host || typeof window === "undefined") return;

    const mq = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    let reducedMotion = Boolean(mq?.matches);

    if (!shouldAttemptWebGL()) {
      setWebglAllowed(false);
      setBeatLabel("exploration-settled");
      return;
    }

    let canvas: HTMLCanvasElement;
    let renderer: THREE.WebGLRenderer;
    try {
      canvas = document.createElement("canvas");
      canvas.className = "axo-v14-closing-canvas";
      canvas.setAttribute("aria-hidden", "true");
      renderer = new THREE.WebGLRenderer({
        canvas,
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
      });
    } catch {
      setWebglAllowed(false);
      setBeatLabel("exploration-settled");
      return;
    }

    const disposables: TrackedDisposable[] = [];
    const track = <T extends TrackedDisposable>(item: T): T => {
      disposables.push(item);
      return item;
    };

    host.appendChild(canvas);
    setWebglReady(true);

    const width = Math.max(260, host.clientWidth || 520);
    const height = Math.max(240, host.clientHeight || 400);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height, false);
    renderer.setClearColor(0x000000, 0);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(34, width / height, 0.1, 100);
    const camVec = new THREE.Vector3(6.9, 3.85, 7.6);
    const lookVec = new THREE.Vector3(0.24, 0.04, 0);
    const camOffset = new THREE.Vector3().subVectors(camVec, lookVec);
    const rotatedOffset = new THREE.Vector3();

    const updateCameraFraming = (
      w: number,
      h: number,
      orbitRad: number,
      tiltX: number,
      tiltY: number,
    ) => {
      const nextAspect = w / Math.max(1, h);
      const aspect = Math.max(0.68, nextAspect);
      const baseScale = 0.9;
      const aspectScale = aspect < 1.18 ? baseScale + (1.18 - aspect) * 0.46 : baseScale;
      const shortScale = h <= 290 ? 1.0 : baseScale;
      const distScale = Math.max(aspectScale, shortScale);
      if (Math.abs(camera.aspect - nextAspect) > 1e-4) {
        camera.aspect = nextAspect;
        camera.updateProjectionMatrix();
      }
      rotatedOffset
        .copy(camOffset)
        .multiplyScalar(distScale)
        .applyAxisAngle(UP_AXIS, orbitRad + tiltX * 0.24);
      rotatedOffset.y += tiltY * 0.72;
      camera.position.copy(lookVec).add(rotatedOffset);
      camera.lookAt(lookVec);
    };

    updateCameraFraming(width, height, 0, 0, 0);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.56);
    const keyLight = new THREE.DirectionalLight(0xfffaf2, 1.16);
    keyLight.position.set(10, 14, 7);
    const fillLight = new THREE.DirectionalLight(0xdcebfa, 0.58);
    fillLight.position.set(-9, 5, -8);
    scene.add(ambientLight, keyLight, fillLight);

    const { bottomPts, topPts, sectionPts, cutNormal, cutOffset } =
      buildHexPrismModel();
    const rawFaces = buildHexPrismFaces(bottomPts, topPts);

    const lowerFaces: ClippedPolygonFace[] = [];
    const upperFaces: ClippedPolygonFace[] = [];
    for (const face of rawFaces) {
      const lo = clipPolygonHalfSpace(face, cutNormal, cutOffset, false);
      if (lo.length >= 3) lowerFaces.push({ pts: lo });
      const hi = clipPolygonHalfSpace(face, cutNormal, cutOffset, true);
      if (hi.length >= 3) upperFaces.push({ pts: hi });
    }

    const root = new THREE.Group();
    scene.add(root);

    const baseY = bottomPts[0].y;
    const topY = topPts[0].y;

    // 1. Soft Studio Contact Disc + Companion 2: Circumscribed radius-R base ring
    const contactTex = createClosingContactTexture();
    if (contactTex) track(contactTex);
    const closingContactGeo = track(new THREE.PlaneGeometry(5.2, 4.8));
    closingContactGeo.rotateX(-Math.PI / 2);
    const closingContactMat = track(
      new THREE.MeshBasicMaterial({
        map: contactTex ?? undefined,
        color: contactTex ? 0xffffff : 0x1f201e,
        transparent: true,
        opacity: contactTex ? 0.92 : 0.05,
        depthWrite: false,
      }),
    );
    const closingContactMesh = new THREE.Mesh(closingContactGeo, closingContactMat);
    closingContactMesh.position.set(0, baseY - 0.048, 0);
    closingContactMesh.renderOrder = 0;
    root.add(closingContactMesh);

    const ringPts: THREE.Vector3[] = [];
    for (let i = 0; i <= 64; i++) {
      const theta = (i * Math.PI * 2) / 64;
      ringPts.push(
        new THREE.Vector3(
          Math.cos(theta) * CLOSING_PRISM_RADIUS,
          baseY - 0.014,
          Math.sin(theta) * CLOSING_PRISM_RADIUS,
        ),
      );
    }
    const baseRingGeo = track(new THREE.BufferGeometry().setFromPoints(ringPts));
    const baseRingMat = track(
      new THREE.LineBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.28 }),
    );
    const baseRingLine = new THREE.Line(baseRingGeo, baseRingMat);
    baseRingLine.renderOrder = 1;
    root.add(baseRingLine);

    // 2. Sculpted Lower Frustum & Lifted Upper Cap Group
    const lowerGeo = track(buildFacesBufferGeometry(lowerFaces, 0xffffff));
    const lowerMat = track(
      new THREE.MeshBasicMaterial({
        color: 0xffffff,
        vertexColors: true,
        transparent: true,
        opacity: 0.94,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const lowerMesh = new THREE.Mesh(lowerGeo, lowerMat);
    lowerMesh.renderOrder = 2;
    root.add(lowerMesh);

    const upperCapGroup = new THREE.Group();
    const upperGeo = track(buildFacesBufferGeometry(upperFaces, 0xfaf9f7));
    const upperMat = track(
      new THREE.MeshBasicMaterial({
        color: 0xffffff,
        vertexColors: true,
        transparent: true,
        opacity: 0.26,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const upperMesh = new THREE.Mesh(upperGeo, upperMat);
    upperMesh.renderOrder = 3;
    upperCapGroup.add(upperMesh);

    // Subtle underside cap rim on upperCapGroup emphasizing coaxial separation
    const capRimCyls: THREE.Mesh[] = [];
    for (let i = 0; i < sectionPts.length; i++) {
      const seg = createCylinderEdge(
        sectionPts[i],
        sectionPts[(i + 1) % sectionPts.length],
        0.013,
        0x9a4006,
        0.48,
        track,
      );
      seg.renderOrder = 5;
      capRimCyls.push(seg);
      upperCapGroup.add(seg);
    }
    root.add(upperCapGroup);

    // 3. Split Front-Solid / Back-Dashed Hexagonal Prism Edges (lower in root, upper in upperCapGroup)
    const faceSpecs = rawFaces.map((face) => {
      const e1 = new THREE.Vector3().subVectors(face[1], face[0]);
      const e2 = new THREE.Vector3().subVectors(face[2], face[0]);
      const normal = new THREE.Vector3().crossVectors(e1, e2).normalize();
      const center = face
        .reduce((acc, pt) => acc.add(pt), new THREE.Vector3())
        .divideScalar(face.length);
      return { normal, center };
    });

    interface EdgeBinding {
      a: THREE.Vector3;
      b: THREE.Vector3;
      faces: readonly [number, number];
      solid: THREE.Mesh;
      dashed: THREE.Line;
    }
    const edgeBindings: EdgeBinding[] = [];
    const registerEdge = (
      targetGroup: THREE.Group,
      a: THREE.Vector3,
      b: THREE.Vector3,
      faces: readonly [number, number],
      solidRenderOrder: number,
      dashedRenderOrder: number,
    ) => {
      const solid = createCylinderEdge(a, b, 0.017, 0x1f201e, 0.88, track);
      solid.renderOrder = solidRenderOrder;
      const dashed = createDashedEdge(a, b, 0x615d59, 0.42, 0.14, 0.11, track);
      dashed.renderOrder = dashedRenderOrder;
      targetGroup.add(solid, dashed);
      edgeBindings.push({ a, b, faces, solid, dashed });
    };

    for (let i = 0; i < 6; i++) {
      const next = (i + 1) % 6;
      const prevLat = 2 + ((i + 5) % 6);
      const currLat = 2 + i;
      registerEdge(root, bottomPts[i], bottomPts[next], [0, currLat], 4, 2);
      registerEdge(root, bottomPts[i], sectionPts[i], [prevLat, currLat], 4, 2);
      registerEdge(upperCapGroup, topPts[i], topPts[next], [1, currLat], 8, 3);
      registerEdge(upperCapGroup, sectionPts[i], topPts[i], [prevLat, currLat], 8, 3);
    }

    // Companion 1: Central Symmetry Axis OO' + Base Perpendicular Witness + Plane Normal Vector
    const axisBottom = new THREE.Vector3(0, baseY, 0);
    const axisTop = new THREE.Vector3(0, topY, 0);
    const axisLine = createDashedEdge(
      axisBottom,
      axisTop,
      0x0075de,
      0.56,
      0.14,
      0.1,
      track,
    );
    axisLine.renderOrder = 2;
    root.add(axisLine);

    const raMat = track(
      new THREE.LineBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.6 }),
    );
    const dirO0 = new THREE.Vector3().subVectors(bottomPts[0], axisBottom).normalize().multiplyScalar(0.24);
    const upSeg = new THREE.Vector3(0, 0.24, 0);
    const raCorner = axisBottom.clone().add(dirO0).add(upSeg);
    const raGeo = track(
      new THREE.BufferGeometry().setFromPoints([
        axisBottom.clone().add(dirO0),
        raCorner,
        axisBottom.clone().add(upSeg),
      ]),
    );
    const raLine = new THREE.Line(raGeo, raMat);
    raLine.renderOrder = 3;
    root.add(raLine);

    const sectionCentroid = sectionPts
      .reduce((acc, pt) => acc.add(pt), new THREE.Vector3())
      .divideScalar(sectionPts.length);
    const normalStem = createCylinderEdge(
      sectionCentroid,
      sectionCentroid.clone().addScaledVector(cutNormal, 0.92),
      0.015,
      0x0075de,
      0.72,
      track,
      true,
    );
    normalStem.renderOrder = 7;

    // Perpendicularity L-bracket proving normalStem perp Π at sectionCentroid
    const uPlane = new THREE.Vector3()
      .subVectors(sectionPts[0], sectionCentroid)
      .normalize()
      .multiplyScalar(0.24);
    const nBracket = cutNormal.clone().multiplyScalar(0.24);
    const centroidRaGeo = track(
      new THREE.BufferGeometry().setFromPoints([
        sectionCentroid.clone().add(uPlane),
        sectionCentroid.clone().add(uPlane).add(nBracket),
        sectionCentroid.clone().add(nBracket),
      ]),
    );
    const centroidRaMat = track(
      new THREE.LineBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.68 }),
    );
    const centroidRaLine = new THREE.Line(centroidRaGeo, centroidRaMat);
    centroidRaLine.renderOrder = 7;
    root.add(normalStem, centroidRaLine);

    // 4. Inclined Exploration Plane (Π)
    const planeGroup = new THREE.Group();
    const secTuples: Vec3Tuple[] = sectionPts.map((pt) => [pt.x, pt.y, pt.z]);
    const planeQuad = computeBoundedPlaneQuad(
      secTuples,
      [cutNormal.x, cutNormal.y, cutNormal.z],
      0.34,
    ).map((pt) => new THREE.Vector3(pt[0], pt[1], pt[2]));
    const planeCenter = planeQuad
      .reduce((acc, v) => acc.add(v), new THREE.Vector3())
      .divideScalar(planeQuad.length);
    const localQuad = planeQuad.map((pt) => pt.clone().sub(planeCenter));

    const planeGeo = track(buildFacesBufferGeometry([{ pts: localQuad }]));
    const planeMat = track(
      new THREE.MeshBasicMaterial({
        color: 0x62aef0,
        transparent: true,
        opacity: 0.13,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const planeMesh = new THREE.Mesh(planeGeo, planeMat);
    planeMesh.renderOrder = 5;
    planeGroup.add(planeMesh);

    const planeRimCyls: THREE.Mesh[] = [];
    for (let i = 0; i < localQuad.length; i++) {
      const rim = createCylinderEdge(
        localQuad[i],
        localQuad[(i + 1) % localQuad.length],
        0.011,
        0x0075de,
        0.48,
        track,
      );
      rim.renderOrder = 5;
      planeRimCyls.push(rim);
      planeGroup.add(rim);
    }
    planeGroup.position.copy(planeCenter);
    root.add(planeGroup);

    // 5. Oblique 6-Edge Section Hexagon
    const sectionGroup = new THREE.Group();
    const offsetLoop = sectionPts.map((pt) =>
      pt.clone().addScaledVector(cutNormal, 0.01),
    );
    const sectionGeo = track(buildFacesBufferGeometry([{ pts: offsetLoop }]));
    const sectionMat = track(
      new THREE.MeshStandardMaterial({
        color: 0xed6d14,
        emissive: 0xb24700,
        emissiveIntensity: 0.24,
        roughness: 0.56,
        metalness: 0.02,
        flatShading: true,
        transparent: true,
        opacity: CLOSING_SECTION_FILL_OPACITY,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const sectionMesh = new THREE.Mesh(sectionGeo, sectionMat);
    sectionMesh.renderOrder = 6;
    sectionGroup.add(sectionMesh);

    const sectionBorderCyls: THREE.Mesh[] = [];
    for (let i = 0; i < offsetLoop.length; i++) {
      const seg = createCylinderEdge(
        offsetLoop[i],
        offsetLoop[(i + 1) % offsetLoop.length],
        0.024,
        0x793400,
        0.96,
        track,
        true,
      );
      seg.renderOrder = 7;
      sectionBorderCyls.push(seg);
      sectionGroup.add(seg);
    }
    root.add(sectionGroup);

    // 6. Clean Anchor Spheres (0 textbook letter tags)
    const nodeGeo = track(new THREE.SphereGeometry(0.056, 16, 16));
    const seedNodeMat = track(
      new THREE.MeshBasicMaterial({ color: 0x0075de, transparent: true, opacity: 1 }),
    );
    const interNodeMat = track(
      new THREE.MeshBasicMaterial({ color: 0xdd5b00, transparent: true, opacity: 1 }),
    );
    const baseVertexMat = track(
      new THREE.MeshBasicMaterial({ color: 0x1f201e, transparent: true, opacity: 0.84 }),
    );

    const bottomVertexDots = bottomPts.map((pt) => {
      const dot = new THREE.Mesh(nodeGeo, baseVertexMat);
      dot.position.copy(pt);
      dot.scale.setScalar(0.76);
      dot.renderOrder = 9;
      root.add(dot);
      return dot;
    });
    const topVertexDots = topPts.map((pt) => {
      const dot = new THREE.Mesh(nodeGeo, baseVertexMat);
      dot.position.copy(pt);
      dot.scale.setScalar(0.76);
      dot.renderOrder = 9;
      upperCapGroup.add(dot);
      return dot;
    });
    const solidVertexDots = [...bottomVertexDots, ...topVertexDots];

    const seedDots = [0, 3, 5].map((idx) => {
      const dot = new THREE.Mesh(nodeGeo, seedNodeMat);
      dot.position.copy(sectionPts[idx]).addScaledVector(cutNormal, 0.012);
      dot.scale.setScalar(1.04);
      dot.renderOrder = 9;
      root.add(dot);
      return dot;
    });

    const interDots = [1, 2, 4].map((idx) => {
      const dot = new THREE.Mesh(nodeGeo, interNodeMat);
      dot.position.copy(sectionPts[idx]).addScaledVector(cutNormal, 0.012);
      dot.scale.setScalar(1.08);
      dot.renderOrder = 9;
      root.add(dot);
      return dot;
    });

    // Companion 3: Isometric Extracted True-Shape Oblique Hexagon + Outer Azimuth Arc + Coaxial Base Projection
    const extractedHex = computeClosingExtractedHexagon2D();
    const extractedHexGroup = new THREE.Group();
    const hexScale = 0.21;
    const hexLocalPts = extractedHex.vertices.map(
      (v) => new THREE.Vector3(v.x * hexScale, v.y * hexScale, 0),
    );
    const hexFillGeo = track(buildFacesBufferGeometry([{ pts: hexLocalPts }]));
    const hexFillMat = track(
      new THREE.MeshBasicMaterial({
        color: 0xed6d14,
        transparent: true,
        opacity: 0.28,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const hexFillMesh = new THREE.Mesh(hexFillGeo, hexFillMat);
    hexFillMesh.renderOrder = 3;
    extractedHexGroup.add(hexFillMesh);
    const hexRimMats: THREE.LineBasicMaterial[] = [];
    for (let i = 0; i < hexLocalPts.length; i++) {
      const rimGeo = track(
        new THREE.BufferGeometry().setFromPoints([
          hexLocalPts[i],
          hexLocalPts[(i + 1) % hexLocalPts.length],
        ]),
      );
      const rimMat = track(
        new THREE.LineBasicMaterial({
          color: 0x793400,
          transparent: true,
          opacity: 0.72,
        }),
      );
      hexRimMats.push(rimMat);
      const rimLine = new THREE.Line(rimGeo, rimMat);
      rimLine.renderOrder = 5;
      extractedHexGroup.add(rimLine);
    }
    const hexBeadGeo = track(new THREE.SphereGeometry(0.025, 10, 10));
    const hexSeedBeadMat = track(
      new THREE.MeshBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.85 }),
    );
    const hexInterBeadMat = track(
      new THREE.MeshBasicMaterial({ color: 0xdd5b00, transparent: true, opacity: 0.85 }),
    );
    for (let i = 0; i < hexLocalPts.length; i++) {
      const isSeed = i === 0 || i === 3 || i === 5;
      const bead = new THREE.Mesh(hexBeadGeo, isSeed ? hexSeedBeadMat : hexInterBeadMat);
      bead.position.copy(hexLocalPts[i]);
      bead.renderOrder = 6;
      extractedHexGroup.add(bead);
    }
    const basisFwd = camOffset.clone().negate().normalize();
    const basisRight = new THREE.Vector3().crossVectors(basisFwd, UP_AXIS).normalize();
    const basisUp = new THREE.Vector3().crossVectors(basisRight, basisFwd).normalize();
    const hexFaceCamQuat = new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 0, 1),
      basisFwd.clone().negate(),
    );
    const hexTiltQuat = new THREE.Quaternion().setFromEuler(
      new THREE.Euler(0.14, -0.22, -0.06),
    );
    extractedHexGroup.quaternion.copy(hexFaceCamQuat).multiply(hexTiltQuat);
    extractedHexGroup.position
      .copy(lookVec)
      .addScaledVector(basisRight, 2.52)
      .addScaledVector(basisUp, 1.54)
      .addScaledVector(basisFwd, 0.55);
    scene.add(extractedHexGroup);

    const orbitArcPts: THREE.Vector3[] = [];
    const orbitR = 2.48;
    for (let i = 0; i <= 40; i++) {
      const theta = -0.35 + (2.35 * i) / 40;
      orbitArcPts.push(
        new THREE.Vector3(Math.cos(theta) * orbitR, baseY - 0.02, Math.sin(theta) * orbitR),
      );
    }
    const orbitArcGeo = track(new THREE.BufferGeometry().setFromPoints(orbitArcPts));
    const orbitArcMat = track(
      new THREE.LineBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.24 }),
    );
    const orbitArcLine = new THREE.Line(orbitArcGeo, orbitArcMat);
    orbitArcLine.renderOrder = 1;
    root.add(orbitArcLine);

    const floorProjPts = sectionPts.map(
      (pt) => new THREE.Vector3(pt.x, baseY + 0.014, pt.z),
    );
    const floorProjFillGeo = track(buildFacesBufferGeometry([{ pts: floorProjPts }]));
    const floorProjFillMat = track(
      new THREE.MeshBasicMaterial({
        color: 0xed6d14,
        transparent: true,
        opacity: 0.15,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const floorProjFillMesh = new THREE.Mesh(floorProjFillGeo, floorProjFillMat);
    floorProjFillMesh.renderOrder = 2;
    root.add(floorProjFillMesh);

    const floorProjRimGeo = track(
      new THREE.BufferGeometry().setFromPoints([...floorProjPts, floorProjPts[0]]),
    );
    const floorProjRimMat = track(
      new THREE.LineBasicMaterial({
        color: 0x9a4006,
        transparent: true,
        opacity: 0.44,
      }),
    );
    const floorProjRimLine = new THREE.Line(floorProjRimGeo, floorProjRimMat);
    floorProjRimLine.renderOrder = 3;
    root.add(floorProjRimLine);

    let disposed = false;
    let isInView = false;
    let startedPlayback = false;
    let startMs = 0;
    let rafId = 0;
    let curTiltX = 0;
    let curTiltY = 0;
    let lastBeat: ClosingStoryboardBeat | null = null;
    const tmpNormal = new THREE.Vector3();
    const tmpCenter = new THREE.Vector3();
    const tmpToCam = new THREE.Vector3();

    const applyFrame = (nowMs: number): boolean => {
      const elapsed = startedPlayback ? nowMs - startMs : 0;
      const state = evaluateClosingStoryboard(elapsed, reducedMotion);

      if (!startedPlayback && !reducedMotion) {
        floorProjFillMesh.visible = false;
        floorProjRimLine.visible = false;
        renderer.render(scene, camera);
        return !state.settled;
      }

      if (state.beat !== lastBeat) {
        lastBeat = state.beat;
        setBeatLabel(state.beat);
      }

      const damp = reducedMotion ? 1 : 0.14;
      curTiltX += (targetTiltRef.current.x - curTiltX) * damp;
      curTiltY += (targetTiltRef.current.y - curTiltY) * damp;

      updateCameraFraming(
        Math.max(260, host.clientWidth || width),
        Math.max(240, host.clientHeight || height),
        state.orbitOffsetRad,
        curTiltX,
        curTiltY,
      );

      root.scale.setScalar(0.94 + 0.06 * state.solidReveal);
      closingContactMat.opacity = (contactTex ? 0.92 : 0.05) * state.solidReveal;
      baseRingMat.opacity = 0.28 * state.solidReveal;
      orbitArcMat.opacity = 0.24 * state.solidReveal;
      lowerMat.opacity = 0.9 * state.solidReveal;
      upperMat.opacity = 0.26 * state.solidReveal;
      upperCapGroup.position.copy(cutNormal).multiplyScalar(state.capLift);
      for (const rim of capRimCyls) {
        (rim.material as THREE.MeshBasicMaterial).opacity =
          0.48 * state.sectionFillOpacity;
      }
      baseVertexMat.opacity = 0.84 * state.solidReveal;
      for (const d of solidVertexDots) {
        d.visible = state.solidReveal > 0.05;
      }

      raMat.opacity = 0.6 * state.solidReveal;
      (axisLine.material as THREE.LineDashedMaterial).opacity =
        0.56 * state.solidReveal;
      void topY;

      seedNodeMat.opacity = state.seedScale;
      for (const dot of seedDots) {
        dot.visible = state.seedScale > 0.05;
        dot.scale.setScalar(Math.max(0.05, 1.04 * state.seedScale));
      }

      planeMat.opacity = 0.13 * state.planeOpacity;
      planeGroup.position
        .copy(planeCenter)
        .addScaledVector(cutNormal, (1 - state.planeOpacity) * 0.45);
      for (const rim of planeRimCyls) {
        (rim.material as THREE.MeshBasicMaterial).opacity =
          0.48 * state.planeOpacity;
      }
      normalStem.visible = state.planeOpacity > 0.15;
      (normalStem.material as THREE.MeshBasicMaterial).opacity =
        0.72 * state.planeOpacity;
      centroidRaLine.visible = state.planeOpacity > 0.25;
      centroidRaMat.opacity = 0.68 * state.planeOpacity;

      floorProjFillMesh.visible = state.sectionFillOpacity > 0.02;
      floorProjRimLine.visible = state.sectionFillOpacity > 0.02;
      floorProjFillMat.opacity = 0.15 * state.sectionFillOpacity;
      floorProjRimMat.opacity = 0.44 * state.sectionFillOpacity;

      const curW = Math.max(260, host.clientWidth || width);
      const curH = Math.max(240, host.clientHeight || height);
      const curAspect = curW / curH;
      const spreadX = curAspect < 1.15 ? 0.88 : 1;
      extractedHexGroup.visible = state.sectionFillOpacity > 0.04;
      extractedHexGroup.scale.setScalar(0.84 + 0.16 * state.sectionFillOpacity);
      extractedHexGroup.position
        .copy(lookVec)
        .addScaledVector(basisRight, 2.52 * spreadX)
        .addScaledVector(basisUp, 1.54 - (1 - state.sectionFillOpacity) * 0.14)
        .addScaledVector(basisFwd, 0.55);
      hexFillMat.opacity = 0.28 * state.sectionFillOpacity;
      for (const hm of hexRimMats) {
        hm.opacity = 0.72 * state.sectionFillOpacity;
      }
      hexSeedBeadMat.opacity = 0.85 * state.sectionFillOpacity;
      hexInterBeadMat.opacity = 0.85 * state.sectionFillOpacity;

      interNodeMat.opacity = state.intersectionScale;
      for (const dot of interDots) {
        dot.visible = state.intersectionScale > 0.05;
        dot.scale.setScalar(Math.max(0.05, 1.08 * state.intersectionScale));
      }

      root.updateMatrixWorld(true);
      const frontFacing = faceSpecs.map((fs) => {
        tmpNormal.copy(fs.normal).transformDirection(root.matrixWorld);
        tmpCenter.copy(fs.center).applyMatrix4(root.matrixWorld);
        tmpToCam.copy(camera.position).sub(tmpCenter);
        return tmpNormal.dot(tmpToCam) > 0;
      });

      for (let i = 0; i < sectionBorderCyls.length; i++) {
        const seg = sectionBorderCyls[i];
        const edgeStart = i / sectionBorderCyls.length;
        const edgeEnd = (i + 1) / sectionBorderCyls.length;
        const localP = clamp01(
          (state.traceProgress - edgeStart) / (edgeEnd - edgeStart),
        );
        const hostFront = frontFacing[2 + i] ?? true;
        seg.visible = localP > 0.01;
        seg.renderOrder = hostFront ? 7 : 6;
        seg.scale.set(1, Math.max(0.01, localP), 1);
        (seg.material as THREE.MeshBasicMaterial).opacity =
          (hostFront ? 0.96 : 0.44) * Math.min(1, localP * 2);
      }

      sectionMat.opacity =
        CLOSING_SECTION_FILL_OPACITY * state.sectionFillOpacity;
      sectionMesh.visible = state.sectionFillOpacity > 0.01;

      for (const edge of edgeBindings) {
        const isFrontEdge =
          frontFacing[edge.faces[0]] || frontFacing[edge.faces[1]];
        edge.solid.visible = isFrontEdge;
        edge.dashed.visible = !isFrontEdge;
        if (isFrontEdge) {
          (edge.solid.material as THREE.MeshBasicMaterial).opacity =
            0.88 * state.solidReveal;
        } else {
          (edge.dashed.material as THREE.LineDashedMaterial).opacity =
            0.42 * state.solidReveal;
        }
      }

      renderer.render(scene, camera);

      const tiltDone =
        Math.abs(targetTiltRef.current.x - curTiltX) < 0.0008 &&
        Math.abs(targetTiltRef.current.y - curTiltY) < 0.0008;
      return state.settled && tiltDone;
    };

    const scheduleFrame = () => {
      if (disposed || !isInView || document.hidden || rafId !== 0) return;
      rafId = window.requestAnimationFrame(loop);
    };

    const stopLoop = () => {
      if (rafId !== 0) {
        window.cancelAnimationFrame(rafId);
        rafId = 0;
      }
    };

    const loop = (now: number) => {
      rafId = 0;
      if (disposed || !isInView || document.hidden) return;
      const done = applyFrame(now);
      if (!done && !reducedMotion) {
        scheduleFrame();
      }
    };

    wakeRef.current = () => {
      if (!startedPlayback) {
        startedPlayback = true;
        startMs = performance.now();
      }
      if (!isInView || document.hidden || disposed) return;
      if (reducedMotion) {
        applyFrame(performance.now());
        return;
      }
      scheduleFrame();
    };

    const io =
      typeof IntersectionObserver !== "undefined"
        ? new IntersectionObserver(
            (entries) => {
              const entry = entries[0];
              const nextInView = Boolean(
                entry && (entry.isIntersecting || entry.intersectionRatio > 0.05),
              );
              isInView = nextInView;
              if (nextInView) {
                if (!startedPlayback) {
                  startedPlayback = true;
                  startMs = performance.now();
                }
                if (reducedMotion) {
                  applyFrame(performance.now());
                } else {
                  scheduleFrame();
                }
              } else {
                stopLoop();
              }
            },
            { threshold: [0, 0.08, 0.25] },
          )
        : null;

    if (io) {
      io.observe(stage);
    } else {
      isInView = true;
      startedPlayback = true;
      startMs = performance.now();
    }

    applyFrame(performance.now());
    if (isInView && !reducedMotion) {
      scheduleFrame();
    }

    const onVisibilityChange = () => {
      if (document.hidden) {
        stopLoop();
      } else if (isInView) {
        applyFrame(performance.now());
        if (!reducedMotion) scheduleFrame();
      }
    };
    document.addEventListener("visibilitychange", onVisibilityChange);

    const onMotionChange = (ev: MediaQueryListEvent) => {
      reducedMotion = ev.matches;
      stopLoop();
      applyFrame(performance.now());
    };
    mq?.addEventListener?.("change", onMotionChange);

    const onContextLost = (ev: Event) => {
      ev.preventDefault();
      stopLoop();
      setContextLost(true);
    };
    const onContextRestored = () => {
      setContextLost(false);
      applyFrame(performance.now());
      if (isInView && !reducedMotion) scheduleFrame();
    };
    canvas.addEventListener("webglcontextlost", onContextLost);
    canvas.addEventListener("webglcontextrestored", onContextRestored);

    const ro =
      typeof ResizeObserver !== "undefined"
        ? new ResizeObserver(() => {
            if (disposed) return;
            const w = Math.max(260, host.clientWidth || 520);
            const h = Math.max(240, host.clientHeight || 400);
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h, false);
            applyFrame(performance.now());
          })
        : null;
    ro?.observe(host);

    return () => {
      disposed = true;
      wakeRef.current = null;
      stopLoop();
      io?.disconnect();
      ro?.disconnect();
      document.removeEventListener("visibilitychange", onVisibilityChange);
      mq?.removeEventListener?.("change", onMotionChange);
      canvas.removeEventListener("webglcontextlost", onContextLost);
      canvas.removeEventListener("webglcontextrestored", onContextRestored);
      for (const d of disposables) {
        d.dispose();
      }
      renderer.dispose();
      canvas.remove();
    };
  }, []);

  const showFallback = !webglAllowed || !webglReady || contextLost;

  return (
    <div
      ref={stageRef}
      id="landing-closing-scene3d"
      className="axo-v14-closing-visual"
      role="img"
      aria-label="Mô hình không gian lăng trụ lục giác đều cắt bởi mặt phẳng nghiên cứu"
      data-cta-visual={
        showFallback ? "svg-fallback" : "spatial-polyhedra-exploration-3d"
      }
      data-closing-beat={beatLabel}
      data-section-edges="6"
      onPointerMove={(e) => {
        if (
          e.pointerType === "touch" ||
          window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches
        ) {
          return;
        }
        const rect = e.currentTarget.getBoundingClientRect();
        if (!rect.width || !rect.height) return;
        const nx = (e.clientX - rect.left) / rect.width - 0.5;
        const ny = (e.clientY - rect.top) / rect.height - 0.5;
        targetTiltRef.current = { x: nx * 0.42, y: -ny * 0.24 };
        wakeRef.current?.();
      }}
      onPointerLeave={() => {
        targetTiltRef.current = { x: 0, y: 0 };
        wakeRef.current?.();
      }}
    >
      <div
        ref={hostRef}
        className={`axo-v14-closing-canvas-host${webglReady && !contextLost && webglAllowed ? "" : " is-hidden"}`}
        aria-hidden="true"
      />
      {showFallback && <ClosingFallbackSvg state={fallbackState} />}
    </div>
  );
}
