import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { computeTrueShapeSection2D } from "./LandingHeroV14";
import { LANDING_PYRAMID_SAMPLE, type Vec3Tuple } from "./landing-geometry-data";

export const CLOSING_STORYBOARD_MS = 3600;
export const CLOSING_SECTION_FILL_OPACITY = 0.56;

export type ClosingStoryboardBeat =
  | "pyramid-solid"
  | "cutting-plane"
  | "intersection-trace"
  | "pentagon-settled";

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
  readonly pyramidVertices: readonly Vec3Tuple[];
  readonly sectionVertices: readonly Vec3Tuple[];
  readonly planeNormal: Vec3Tuple;
  readonly planarResiduals: readonly number[];
  readonly midpointResiduals: readonly number[];
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

const MATH_ORIGIN: Vec3Tuple = [2, 2, 2.65];
const UP_AXIS = new THREE.Vector3(0, 1, 0);

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
      beat: "pentagon-settled",
      progress: 1,
      solidReveal: 1,
      seedScale: 1,
      planeOpacity: 1,
      traceProgress: 1,
      sectionFillOpacity: 1,
      intersectionScale: 1,
      capLift: 0,
      orbitOffsetRad: 0,
      settled: true,
      reducedMotion,
    };
  }

  const p = clamp01(elapsedMs / CLOSING_STORYBOARD_MS);
  const solidReveal = easeOutCubic(p, 0, 0.24);
  const seedScale = easeOutCubic(p, 0.08, 0.34);
  const planeOpacity = easeOutCubic(p, 0.24, 0.56);
  const traceProgress = easeOutCubic(p, 0.44, 0.84);
  const sectionFillOpacity = easeOutCubic(p, 0.68, 0.96);
  const intersectionScale = easeOutCubic(p, 0.48, 0.78);
  const orbitOffsetRad = (1 - Math.pow(1 - p, 2)) * 0.085 - 0.085;

  let beat: ClosingStoryboardBeat = "pyramid-solid";
  if (p >= 0.84) {
    beat = "pentagon-settled";
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
    capLift: 0,
    orbitOffsetRad,
    settled: false,
    reducedMotion: false,
  };
}

function worldToMath(pos: Vec3Tuple): Vec3Tuple {
  return [
    pos[0] + MATH_ORIGIN[0],
    -pos[2] + MATH_ORIGIN[1],
    pos[1] + MATH_ORIGIN[2],
  ];
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

export function buildClosingCompositionData(): ClosingCompositionData {
  const pMap = LANDING_PYRAMID_SAMPLE.pointMap;
  const v3 = (id: string) => {
    const p = pMap[id]?.pos ?? [0, 0, 0];
    return new THREE.Vector3(p[0], p[1], p[2]);
  };

  const pyramidVertices: Vec3Tuple[] = ["S", "A", "B", "C", "D"].map((id) => [
    ...(pMap[id]?.pos ?? [0, 0, 0]),
  ]) as Vec3Tuple[];
  const sectionIds = LANDING_PYRAMID_SAMPLE.sectionLoop;
  const sectionVertices: Vec3Tuple[] = sectionIds.map((id) => [
    ...(pMap[id]?.pos ?? [0, 0, 0]),
  ]) as Vec3Tuple[];

  const planarResiduals = sectionVertices.map((pos) => {
    const [mx, my, mz] = worldToMath(pos);
    return Math.abs(mx + my + 2 * mz - 6);
  });

  const midpointResidual = (mId: string, aId: string, bId: string): number => {
    const m = pMap[mId].domainXyz;
    const a = pMap[aId].domainXyz;
    const b = pMap[bId].domainXyz;
    return Math.hypot(
      m[0] - (a[0] + b[0]) * 0.5,
      m[1] - (a[1] + b[1]) * 0.5,
      m[2] - (a[2] + b[2]) * 0.5,
    );
  };
  const midpointResiduals = [
    midpointResidual("M", "S", "A"),
    midpointResidual("N", "B", "C"),
    midpointResidual("P", "C", "D"),
  ];

  const S = v3("S");
  const A = v3("A");
  const B = v3("B");
  const C = v3("C");
  const D = v3("D");
  const loopPts = sectionIds.map(v3);
  const centroid = new THREE.Vector3()
    .add(S)
    .add(A)
    .add(B)
    .add(C)
    .add(D)
    .divideScalar(5);

  const rawNormal = new THREE.Vector3()
    .subVectors(loopPts[1], loopPts[0])
    .cross(new THREE.Vector3().subVectors(loopPts[2], loopPts[0]))
    .normalize();
  const cutPlaneNormal =
    rawNormal.dot(new THREE.Vector3().subVectors(S, loopPts[0])) >= 0
      ? rawNormal
      : rawNormal.negate();
  const cutPlaneOffset = cutPlaneNormal.dot(loopPts[0]);

  const rawFaces = [
    orientFaceOutward([D, C, B, A], centroid),
    orientFaceOutward([A, B, S], centroid),
    orientFaceOutward([B, C, S], centroid),
    orientFaceOutward([C, D, S], centroid),
    orientFaceOutward([D, A, S], centroid),
  ];

  let lowerFrustumFaceCount = 0;
  let upperCapFaceCount = 0;
  for (const face of rawFaces) {
    if (clipPolygonHalfSpace(face, cutPlaneNormal, cutPlaneOffset, false).length >= 3) {
      lowerFrustumFaceCount++;
    }
    if (clipPolygonHalfSpace(face, cutPlaneNormal, cutPlaneOffset, true).length >= 3) {
      upperCapFaceCount++;
    }
  }

  return {
    pyramidVertices,
    sectionVertices,
    planeNormal: [cutPlaneNormal.x, cutPlaneNormal.y, cutPlaneNormal.z],
    planarResiduals,
    midpointResiduals,
    lowerFrustumFaceCount,
    upperCapFaceCount,
    companionCount: 3,
  };
}

function buildFacesBufferGeometry(
  faces: readonly ClippedPolygonFace[],
): THREE.BufferGeometry {
  const positions: number[] = [];
  for (const face of faces) {
    if (face.pts.length < 3) continue;
    const p0 = face.pts[0];
    for (let i = 1; i < face.pts.length - 1; i++) {
      const p1 = face.pts[i];
      const p2 = face.pts[i + 1];
      positions.push(p0.x, p0.y, p0.z, p1.x, p1.y, p1.z, p2.x, p2.y, p2.z);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
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
  return (
    <svg
      className="axo-v14-closing-fallback-svg"
      viewBox="0 0 540 420"
      role="img"
      aria-label="Mô hình khối chóp S.ABCD và thiết diện ngũ giác phẳng MENPF"
    >
      <ellipse
        className="axo-v14-svg-contact-halo"
        cx="256"
        cy="346"
        rx="154"
        ry="26"
      />
      <ellipse
        className="axo-v14-svg-contact-core"
        cx="256"
        cy="346"
        rx="104"
        ry="17"
      />
      <path
        className="axo-v14-svg-edge-altitude"
        d="M 116 356 A 176 42 0 0 0 416 332"
        fill="none"
        strokeOpacity="0.34"
      />
      <polygon
        className="axo-v14-svg-edge-hidden"
        points="82,118 98,94 114,118 98,142"
        fill="none"
        strokeOpacity="0.48"
      />

      <polygon
        className="axo-v14-svg-solid-base"
        points="142,318 332,350 408,278 212,258"
      />
      <polygon
        className="axo-v14-svg-solid-lower"
        points="142,318 332,350 408,278 326,188 256,174 176,216"
      />
      <polygon
        className="axo-v14-svg-solid-upper"
        points="212,72 176,216 256,174 326,188"
      />

      <line className="axo-v14-svg-edge-hidden" x1="212" y1="258" x2="142" y2="318" />
      <line className="axo-v14-svg-edge-hidden" x1="212" y1="258" x2="408" y2="278" />
      <line className="axo-v14-svg-edge-altitude" x1="212" y1="72" x2="212" y2="258" />

      <line className="axo-v14-svg-edge-solid" x1="142" y1="318" x2="332" y2="350" />
      <line className="axo-v14-svg-edge-solid" x1="332" y1="350" x2="408" y2="278" />
      <line className="axo-v14-svg-edge-solid" x1="212" y1="72" x2="142" y2="318" />
      <line className="axo-v14-svg-edge-solid" x1="212" y1="72" x2="332" y2="350" />
      <line className="axo-v14-svg-edge-solid" x1="212" y1="72" x2="408" y2="278" />

      <polygon
        className="axo-v14-svg-cutting-plane"
        points="98,236 364,274 428,176 168,150"
        opacity={state.planeOpacity}
      />
      <polygon
        className="axo-v14-svg-section-poly"
        points="176,216 238,266 306,256 326,188 256,174"
        fillOpacity={CLOSING_SECTION_FILL_OPACITY * state.sectionFillOpacity}
      />
      <polygon
        className="axo-v14-svg-section-poly"
        points="456,96 488,88 506,118 480,140 450,126"
        fillOpacity={0.2 * state.sectionFillOpacity}
        strokeOpacity={0.68 * state.sectionFillOpacity}
      />

      <circle className="axo-v14-svg-vertex-dot" cx="212" cy="72" r="3.4" />
      <circle className="axo-v14-svg-seed-dot" cx="176" cy="216" r="4.0" />
      <circle className="axo-v14-svg-seed-dot" cx="306" cy="256" r="4.0" />
      <circle className="axo-v14-svg-seed-dot" cx="326" cy="188" r="4.0" />
      <circle className="axo-v14-svg-section-dot" cx="238" cy="266" r="4.2" />
      <circle className="axo-v14-svg-section-dot" cx="256" cy="174" r="4.2" />
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
    useState<ClosingStoryboardBeat>("pyramid-solid");

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
      setBeatLabel("pentagon-settled");
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
      setBeatLabel("pentagon-settled");
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
    const [baseCamX, baseCamY, baseCamZ] = LANDING_PYRAMID_SAMPLE.defaultCamera;
    const [lookX, lookY, lookZ] = LANDING_PYRAMID_SAMPLE.defaultLookAt;
    const camVec = new THREE.Vector3(
      baseCamX * 0.96,
      baseCamY * 0.86,
      baseCamZ * 0.78,
    );
    const lookVec = new THREE.Vector3(lookX, lookY + 0.34, lookZ);
    const camOffset = new THREE.Vector3().subVectors(camVec, lookVec);
    const rotatedOffset = new THREE.Vector3();

    const updateCameraFraming = (
      w: number,
      h: number,
      orbitRad: number,
      tiltX: number,
      tiltY: number,
    ) => {
      const aspect = Math.max(0.68, w / Math.max(1, h));
      const aspectScale = aspect < 1.16 ? 1 + (1.16 - aspect) * 0.55 : 1;
      const shortScale = h <= 290 ? 1.07 : 1;
      const distScale = Math.max(aspectScale, shortScale);
      rotatedOffset
        .copy(camOffset)
        .multiplyScalar(distScale)
        .applyAxisAngle(UP_AXIS, orbitRad + tiltX * 0.24);
      rotatedOffset.y += tiltY * 0.72;
      camera.position.copy(lookVec).add(rotatedOffset);
      camera.lookAt(lookVec);
    };

    updateCameraFraming(width, height, 0, 0, 0);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.46);
    const keyLight = new THREE.DirectionalLight(0xfffaf2, 1.2);
    keyLight.position.set(11, 15, -5);
    const fillLight = new THREE.DirectionalLight(0xdcebfa, 0.58);
    fillLight.position.set(-10, 4, 10);
    scene.add(ambientLight, keyLight, fillLight);

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

    const rawNormal = new THREE.Vector3()
      .subVectors(loopPts[1], loopPts[0])
      .cross(new THREE.Vector3().subVectors(loopPts[2], loopPts[0]))
      .normalize();
    const cutPlaneNormal =
      rawNormal.dot(new THREE.Vector3().subVectors(S, loopPts[0])) >= 0
        ? rawNormal
        : rawNormal.negate();
    const cutPlaneOffset = cutPlaneNormal.dot(loopPts[0]);

    const rawFaces = [
      orientFaceOutward([D, C, B, A], pyramidCentroid),
      orientFaceOutward([A, B, S], pyramidCentroid),
      orientFaceOutward([B, C, S], pyramidCentroid),
      orientFaceOutward([C, D, S], pyramidCentroid),
      orientFaceOutward([D, A, S], pyramidCentroid),
    ];

    const lowerFaces: ClippedPolygonFace[] = [];
    const upperFaces: ClippedPolygonFace[] = [];
    for (const face of rawFaces) {
      const lo = clipPolygonHalfSpace(face, cutPlaneNormal, cutPlaneOffset, false);
      if (lo.length >= 3) lowerFaces.push({ pts: lo });
      const hi = clipPolygonHalfSpace(face, cutPlaneNormal, cutPlaneOffset, true);
      if (hi.length >= 3) upperFaces.push({ pts: hi });
    }

    const root = new THREE.Group();
    scene.add(root);

    // 1. Ground contact AO discs under ABCD
    const shadowOuterGeo = track(new THREE.CircleGeometry(2.72, 48));
    shadowOuterGeo.rotateX(-Math.PI / 2);
    const shadowOuterMat = track(
      new THREE.MeshBasicMaterial({
        color: 0x1f201e,
        transparent: true,
        opacity: 0.04,
        depthWrite: false,
      }),
    );
    const shadowOuter = new THREE.Mesh(shadowOuterGeo, shadowOuterMat);
    shadowOuter.position.set(baseCenter.x, A.y - 0.055, baseCenter.z);
    shadowOuter.renderOrder = 0;

    const shadowInnerGeo = track(new THREE.CircleGeometry(1.86, 40));
    shadowInnerGeo.rotateX(-Math.PI / 2);
    const shadowInnerMat = track(
      new THREE.MeshBasicMaterial({
        color: 0x1f201e,
        transparent: true,
        opacity: 0.068,
        depthWrite: false,
      }),
    );
    const shadowInner = new THREE.Mesh(shadowInnerGeo, shadowInnerMat);
    shadowInner.position.set(baseCenter.x, A.y - 0.045, baseCenter.z);
    shadowInner.renderOrder = 1;
    root.add(shadowOuter, shadowInner);

    // 2. Sculpted Pyramid Volumes
    const lowerGeo = track(buildFacesBufferGeometry(lowerFaces));
    const lowerMat = track(
      new THREE.MeshStandardMaterial({
        color: 0xf3f1ec,
        roughness: 0.86,
        metalness: 0.02,
        flatShading: true,
        transparent: true,
        opacity: 0.86,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const lowerMesh = new THREE.Mesh(lowerGeo, lowerMat);
    lowerMesh.renderOrder = 2;
    root.add(lowerMesh);

    const upperGeo = track(buildFacesBufferGeometry(upperFaces));
    const upperMat = track(
      new THREE.MeshStandardMaterial({
        color: 0xffffff,
        roughness: 0.78,
        metalness: 0.02,
        flatShading: true,
        transparent: true,
        opacity: 0.2,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const upperMesh = new THREE.Mesh(upperGeo, upperMat);
    upperMesh.renderOrder = 3;
    root.add(upperMesh);

    // 3. Dynamic front/back solid & dashed edges
    const faceSpecs = rawFaces.map((face) => {
      const e1 = new THREE.Vector3().subVectors(face[1], face[0]);
      const e2 = new THREE.Vector3().subVectors(face[2], face[0]);
      const normal = new THREE.Vector3().crossVectors(e1, e2).normalize();
      const center = face
        .reduce((acc, pt) => acc.add(pt), new THREE.Vector3())
        .divideScalar(face.length);
      return { normal, center };
    });

    const edgeBindings = [
      { a: A, b: B, faces: [0, 1] as const, altitude: false },
      { a: B, b: C, faces: [0, 2] as const, altitude: false },
      { a: C, b: D, faces: [0, 3] as const, altitude: false },
      { a: D, b: A, faces: [0, 4] as const, altitude: false },
      { a: S, b: A, faces: [1, 4] as const, altitude: true },
      { a: S, b: B, faces: [1, 2] as const, altitude: false },
      { a: S, b: C, faces: [2, 3] as const, altitude: false },
      { a: S, b: D, faces: [3, 4] as const, altitude: false },
    ].map((edge) => {
      const solid = createCylinderEdge(edge.a, edge.b, 0.02, 0x1f201e, 0.9, track);
      solid.renderOrder = 6;
      const dashed = createDashedEdge(
        edge.a,
        edge.b,
        edge.altitude ? 0x0075de : 0x615d59,
        edge.altitude ? 0.56 : 0.44,
        0.16,
        0.12,
        track,
      );
      dashed.renderOrder = 2;
      root.add(solid, dashed);
      return { ...edge, solid, dashed };
    });

    const guideLines = LANDING_PYRAMID_SAMPLE.guideEdges.map((guide) => {
      const line = createDashedEdge(
        vec3(guide.from),
        vec3(guide.to),
        0x615d59,
        0.32,
        0.14,
        0.12,
        track,
      );
      line.renderOrder = 2;
      root.add(line);
      return line;
    });

    const unitB = new THREE.Vector3().subVectors(B, A).normalize().multiplyScalar(0.28);
    const unitS = new THREE.Vector3().subVectors(S, A).normalize().multiplyScalar(0.28);
    const raCorner = new THREE.Vector3().copy(A).add(unitB).add(unitS);
    const raGeo1 = track(new THREE.BufferGeometry().setFromPoints([A.clone().add(unitB), raCorner]));
    const raGeo2 = track(new THREE.BufferGeometry().setFromPoints([raCorner, A.clone().add(unitS)]));
    const raMat = track(
      new THREE.LineBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.56 }),
    );
    const ra1 = new THREE.Line(raGeo1, raMat);
    const ra2 = new THREE.Line(raGeo2, raMat);
    ra1.renderOrder = 2;
    ra2.renderOrder = 2;
    root.add(ra1, ra2);

    // 4. Cutting Plane (MNP)
    const planeGroup = new THREE.Group();
    const qPts = LANDING_PYRAMID_SAMPLE.planeQuad.map(
      (v) => new THREE.Vector3(v[0], v[1], v[2]),
    );
    const planeCenter = qPts
      .reduce((acc, v) => acc.add(v), new THREE.Vector3())
      .divideScalar(Math.max(1, qPts.length));
    const localQuad = qPts.map((pt) => pt.clone().sub(planeCenter));
    const planeGeo = track(buildFacesBufferGeometry([{ pts: localQuad }]));
    const planeMat = track(
      new THREE.MeshBasicMaterial({
        color: 0x62aef0,
        transparent: true,
        opacity: 0.22,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const planeMesh = new THREE.Mesh(planeGeo, planeMat);
    planeMesh.renderOrder = 4;
    planeGroup.add(planeMesh);

    const planeRimCyls: THREE.Mesh[] = [];
    for (let i = 0; i < localQuad.length; i++) {
      const rim = createCylinderEdge(
        localQuad[i],
        localQuad[(i + 1) % localQuad.length],
        0.015,
        0x0075de,
        0.84,
        track,
      );
      rim.renderOrder = 6;
      planeRimCyls.push(rim);
      planeGroup.add(rim);
    }
    planeGroup.position.copy(planeCenter);
    root.add(planeGroup);

    // 5. Cross-section Pentagon MENPF
    const sectionGroup = new THREE.Group();
    const offsetLoop = loopPts.map((pt) =>
      pt.clone().addScaledVector(cutPlaneNormal, 0.012),
    );
    const sectionGeo = track(buildFacesBufferGeometry([{ pts: offsetLoop }]));
    const sectionMat = track(
      new THREE.MeshStandardMaterial({
        color: 0xe6620a,
        emissive: 0x993d00,
        emissiveIntensity: 0.2,
        roughness: 0.6,
        metalness: 0.04,
        flatShading: true,
        transparent: true,
        opacity: CLOSING_SECTION_FILL_OPACITY,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const sectionMesh = new THREE.Mesh(sectionGeo, sectionMat);
    sectionMesh.renderOrder = 5;
    sectionGroup.add(sectionMesh);

    const sectionBorderCyls: THREE.Mesh[] = [];
    for (let i = 0; i < offsetLoop.length; i++) {
      const seg = createCylinderEdge(
        offsetLoop[i],
        offsetLoop[(i + 1) % offsetLoop.length],
        0.026,
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

    // 6. Anchor Spheres (0 textbook letters)
    const nodeGeo = track(new THREE.SphereGeometry(0.064, 16, 16));
    const baseNodeMat = track(
      new THREE.MeshBasicMaterial({ color: 0x1f201e, transparent: true, opacity: 0.92 }),
    );
    const hiddenNodeMat = track(
      new THREE.MeshBasicMaterial({ color: 0x5c5b57, transparent: true, opacity: 0.38 }),
    );
    const seedNodeMat = track(
      new THREE.MeshBasicMaterial({ color: 0x0075de, transparent: true, opacity: 1 }),
    );
    const interNodeMat = track(
      new THREE.MeshBasicMaterial({ color: 0xdd5b00, transparent: true, opacity: 1 }),
    );

    for (const pt of [S, B, C, D]) {
      const dot = new THREE.Mesh(nodeGeo, baseNodeMat);
      dot.position.copy(pt);
      dot.renderOrder = 8;
      root.add(dot);
    }
    const backDotA = new THREE.Mesh(nodeGeo, hiddenNodeMat);
    backDotA.position.copy(A);
    backDotA.scale.setScalar(0.84);
    backDotA.renderOrder = 3;
    root.add(backDotA);

    const seedDots = [M, N, P].map((pt) => {
      const dot = new THREE.Mesh(nodeGeo, seedNodeMat);
      dot.position.copy(pt).addScaledVector(cutPlaneNormal, 0.014);
      dot.scale.setScalar(1.06);
      dot.renderOrder = 8;
      root.add(dot);
      return dot;
    });
    const interDots = [E, F].map((pt) => {
      const dot = new THREE.Mesh(nodeGeo, interNodeMat);
      dot.position.copy(pt).addScaledVector(cutPlaneNormal, 0.015);
      dot.scale.setScalar(1.12);
      dot.renderOrder = 8;
      root.add(dot);
      return dot;
    });

    // 7. Three Restrained Peripheral Geometric Companions
    // 7a. Base spatial azimuth datum arc + radial end-ticks + extended NP trace
    const dirNP = new THREE.Vector3().subVectors(P, N).normalize();
    const extNP = createDashedEdge(
      N.clone().addScaledVector(dirNP, -0.78),
      P.clone().addScaledVector(dirNP, 0.78),
      0x0075de,
      0.42,
      0.14,
      0.1,
      track,
    );
    extNP.renderOrder = 2;
    root.add(extNP);

    const orbitArcPts: THREE.Vector3[] = [];
    const orbitRadius = 2.66;
    for (let i = 0; i <= 32; i++) {
      const theta = -0.44 + (1.46 * i) / 32;
      orbitArcPts.push(
        new THREE.Vector3(
          baseCenter.x + Math.cos(theta) * orbitRadius,
          A.y - 0.028,
          baseCenter.z + Math.sin(theta) * orbitRadius,
        ),
      );
    }
    const orbitArcGeo = track(new THREE.BufferGeometry().setFromPoints(orbitArcPts));
    const orbitArcMat = track(
      new THREE.LineBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.26 }),
    );
    const orbitArc = new THREE.Line(orbitArcGeo, orbitArcMat);
    orbitArc.renderOrder = 1;
    const orbitNodeMat = track(
      new THREE.MeshBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.62 }),
    );
    const orbitNode = new THREE.Mesh(nodeGeo, orbitNodeMat);
    orbitNode.position.copy(orbitArcPts[orbitArcPts.length - 1]);
    orbitNode.scale.setScalar(0.66);
    orbitNode.renderOrder = 3;
    root.add(orbitArc, orbitNode);

    // 7b. Upper-right rear orthographic true-shape MENPF satellite + subtle rays
    const trueShape = computeTrueShapeSection2D();
    const satGroup = new THREE.Group();
    satGroup.position.set(baseCenter.x + 2.42, S.y - 0.72, baseCenter.z + 1.04);
    satGroup.lookAt(camera.position);
    const satScale = 1.12;
    const satPts = trueShape.vertices.map(
      (v) => new THREE.Vector3((v.nx - 0.5) * satScale, (0.52 - v.ny) * satScale, 0),
    );
    const satGeo = track(buildFacesBufferGeometry([{ pts: satPts }]));
    const satFillMat = track(
      new THREE.MeshBasicMaterial({
        color: 0xe6620a,
        transparent: true,
        opacity: 0.16,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const satFill = new THREE.Mesh(satGeo, satFillMat);
    satFill.renderOrder = 2;
    satGroup.add(satFill);

    const satRimGeo = track(
      new THREE.BufferGeometry().setFromPoints([...satPts, satPts[0]]),
    );
    const satRimMat = track(
      new THREE.LineBasicMaterial({ color: 0xdd5b00, transparent: true, opacity: 0.7 }),
    );
    const satRim = new THREE.Line(satRimGeo, satRimMat);
    satRim.renderOrder = 3;
    satGroup.add(satRim);
    root.add(satGroup);

    const satAnchorM = satPts[0]
      .clone()
      .applyQuaternion(satGroup.quaternion)
      .add(satGroup.position);
    const satAnchorF = satPts[4]
      .clone()
      .applyQuaternion(satGroup.quaternion)
      .add(satGroup.position);
    const projRayM = createDashedEdge(M, satAnchorM, 0x716d69, 0.22, 0.12, 0.12, track);
    const projRayF = createDashedEdge(F, satAnchorF, 0x716d69, 0.22, 0.12, 0.12, track);
    projRayM.renderOrder = 1;
    projRayF.renderOrder = 1;
    root.add(projRayM, projRayF);

    // 7c. Upper-left mid-rear miniature wireframe octahedron companion
    const octSolidGeo = track(new THREE.OctahedronGeometry(0.42, 0));
    const octWireGeo = track(new THREE.EdgesGeometry(octSolidGeo));
    const octFillMat = track(
      new THREE.MeshBasicMaterial({
        color: 0xdcebfa,
        transparent: true,
        opacity: 0.24,
        depthWrite: false,
      }),
    );
    const octWireMat = track(
      new THREE.LineBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.48 }),
    );
    const octMesh = new THREE.Mesh(octSolidGeo, octFillMat);
    const octWire = new THREE.LineSegments(octWireGeo, octWireMat);
    const octGroup = new THREE.Group();
    octGroup.position.set(baseCenter.x - 2.38, S.y - 1.15, baseCenter.z + 0.96);
    octGroup.rotation.set(0.35, 0.62, 0.12);
    octGroup.add(octMesh, octWire);
    root.add(octGroup);

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
      if (!startedPlayback && !reducedMotion) {
        const previewState = evaluateClosingStoryboard(0, false);
        renderer.render(scene, camera);
        return !previewState.settled;
      }

      const elapsed = startedPlayback ? nowMs - startMs : 0;
      const state = evaluateClosingStoryboard(elapsed, reducedMotion);

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

      root.scale.setScalar(0.95 + 0.05 * state.solidReveal);
      shadowOuterMat.opacity = 0.04 * state.solidReveal;
      shadowInnerMat.opacity = 0.068 * state.solidReveal;
      lowerMat.opacity = 0.86 * state.solidReveal;
      upperMat.opacity = 0.2 * state.solidReveal;
      baseNodeMat.opacity = 0.92 * state.solidReveal;
      hiddenNodeMat.opacity = 0.38 * state.solidReveal;
      raMat.opacity = 0.56 * state.solidReveal;
      for (const gl of guideLines) {
        (gl.material as THREE.LineDashedMaterial).opacity = 0.32 * state.solidReveal;
      }

      orbitArcMat.opacity = 0.26 * state.solidReveal;
      orbitNodeMat.opacity = 0.62 * state.solidReveal;
      octFillMat.opacity = 0.24 * state.solidReveal;
      octWireMat.opacity = 0.48 * state.solidReveal;

      seedNodeMat.opacity = state.seedScale;
      for (const dot of seedDots) {
        dot.visible = state.seedScale > 0.05;
        dot.scale.setScalar(Math.max(0.05, 1.06 * state.seedScale));
      }

      planeMat.opacity = 0.22 * state.planeOpacity;
      planeGroup.position
        .copy(planeCenter)
        .addScaledVector(cutPlaneNormal, (1 - state.planeOpacity) * 0.5);
      for (const rim of planeRimCyls) {
        (rim.material as THREE.MeshBasicMaterial).opacity = 0.84 * state.planeOpacity;
      }
      (extNP.material as THREE.LineDashedMaterial).opacity = 0.42 * state.planeOpacity;
      extNP.visible = state.planeOpacity > 0.06;

      interNodeMat.opacity = state.intersectionScale;
      for (const dot of interDots) {
        dot.visible = state.intersectionScale > 0.05;
        dot.scale.setScalar(Math.max(0.05, 1.12 * state.intersectionScale));
      }

      for (let i = 0; i < sectionBorderCyls.length; i++) {
        const seg = sectionBorderCyls[i];
        const edgeStart = i / sectionBorderCyls.length;
        const edgeEnd = (i + 1) / sectionBorderCyls.length;
        const localP = clamp01(
          (state.traceProgress - edgeStart) / (edgeEnd - edgeStart),
        );
        seg.visible = localP > 0.01;
        seg.scale.set(1, Math.max(0.01, localP), 1);
        (seg.material as THREE.MeshBasicMaterial).opacity =
          0.96 * Math.min(1, localP * 2);
      }

      sectionMat.opacity = CLOSING_SECTION_FILL_OPACITY * state.sectionFillOpacity;
      sectionMesh.visible = state.sectionFillOpacity > 0.01;

      satFillMat.opacity = 0.16 * state.sectionFillOpacity;
      satRimMat.opacity = 0.7 * state.sectionFillOpacity;
      satGroup.visible = state.sectionFillOpacity > 0.04;
      (projRayM.material as THREE.LineDashedMaterial).opacity =
        0.22 * state.sectionFillOpacity;
      (projRayF.material as THREE.LineDashedMaterial).opacity =
        0.22 * state.sectionFillOpacity;
      projRayM.visible = state.sectionFillOpacity > 0.06;
      projRayF.visible = state.sectionFillOpacity > 0.06;

      root.updateMatrixWorld(true);
      const frontFacing = faceSpecs.map((fs) => {
        tmpNormal.copy(fs.normal).transformDirection(root.matrixWorld);
        tmpCenter.copy(fs.center).applyMatrix4(root.matrixWorld);
        tmpToCam.copy(camera.position).sub(tmpCenter);
        return tmpNormal.dot(tmpToCam) > 0;
      });

      for (const edge of edgeBindings) {
        const isFrontEdge =
          frontFacing[edge.faces[0]] || frontFacing[edge.faces[1]];
        edge.solid.visible = isFrontEdge;
        edge.dashed.visible = !isFrontEdge;
        if (isFrontEdge) {
          (edge.solid.material as THREE.MeshBasicMaterial).opacity =
            0.9 * state.solidReveal;
        } else {
          (edge.dashed.material as THREE.LineDashedMaterial).opacity =
            (edge.altitude ? 0.56 : 0.44) * state.solidReveal;
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
      aria-label="Mô hình 3D hình chóp S.ABCD và thiết diện ngũ giác phẳng MENPF"
      data-cta-visual={
        showFallback ? "svg-fallback" : "spatial-pyramid-editorial-3d"
      }
      data-closing-beat={beatLabel}
      data-section-edges="5"
      onPointerMove={(e) => {
        if (window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches) {
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
