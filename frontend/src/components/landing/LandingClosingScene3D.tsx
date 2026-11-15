import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { LANDING_PYRAMID_SAMPLE, type Vec3Tuple } from "./landing-geometry-data";

export const CLOSING_CYCLE_DURATION_MS = 9600;

export type ClosingMotionPhase =
  | "base-pyramid"
  | "plane-emergence"
  | "section-intersection"
  | "complete-settled";

export interface ClosingMotionState {
  phase: ClosingMotionPhase;
  cycleProgress: number;
  pyramidOpacity: number;
  guideProgress: number;
  planeProgress: number;
  traceProgress: number;
  sectionFillOpacity: number;
  seedPointScale: number;
  intersectionPointScale: number;
  capLift: number;
  orbitAngleRad: number;
  reducedMotion: boolean;
}

interface ProjectedPoint2D {
  x: number;
  y: number;
  depth: number;
}

export interface ClosingFallbackProjection {
  width: number;
  height: number;
  points: Record<string, ProjectedPoint2D>;
  planePolygonPoints: string;
  sectionPolygonPoints: string;
  tracedEdges: readonly { x1: number; y1: number; x2: number; y2: number; progress: number }[];
  lowerPolygons: readonly string[];
  upperPolygons: readonly string[];
  hiddenEdges: readonly { id: string; x1: number; y1: number; x2: number; y2: number; isAltitude: boolean }[];
  solidEdges: readonly { x1: number; y1: number; x2: number; y2: number }[];
  contactBase: { x: number; y: number; rx: number; ry: number };
}

export interface ClosingPyramidRigData {
  pointWorldMap: Record<string, Vec3Tuple>;
  pointMathMap: Record<string, Vec3Tuple>;
  sectionIds: readonly string[];
  sectionMathResiduals: readonly number[];
  planeQuadWorld: readonly Vec3Tuple[];
  lowerFrustumFaces: readonly (readonly Vec3Tuple[])[];
  upperCapFaces: readonly (readonly Vec3Tuple[])[];
  solidEdges: readonly { from: string; to: string; hidden: boolean }[];
  guideEdges: readonly { from: string; to: string }[];
}

interface ClippedPolygonFace {
  pts: THREE.Vector3[];
}

type TrackedDisposable = THREE.BufferGeometry | THREE.Material;

const MATH_CENTER: Vec3Tuple = [2, 2, 2.65];

function smoothstep01(t: number): number {
  const c = Math.max(0, Math.min(1, t));
  return c * c * (3 - 2 * c);
}

function windowEase(t: number, start: number, end: number): number {
  if (end <= start) return t >= end ? 1 : 0;
  return smoothstep01((t - start) / (end - start));
}

export function evaluateClosingMotionState(
  elapsedMs: number,
  reducedMotion: boolean,
  previewOverride?: "mid" | "settled" | null,
): ClosingMotionState {
  if (reducedMotion || previewOverride === "settled") {
    return {
      phase: "complete-settled",
      cycleProgress: 1,
      pyramidOpacity: 1,
      guideProgress: 1,
      planeProgress: 1,
      traceProgress: 1,
      sectionFillOpacity: 1,
      seedPointScale: 1,
      intersectionPointScale: 1,
      capLift: 0,
      orbitAngleRad: 0,
      reducedMotion,
    };
  }

  if (previewOverride === "mid") {
    return {
      phase: "section-intersection",
      cycleProgress: 0.58,
      pyramidOpacity: 1,
      guideProgress: 1,
      planeProgress: 1,
      traceProgress: 0.72,
      sectionFillOpacity: 0.52,
      seedPointScale: 1,
      intersectionPointScale: 0.92,
      capLift: 0.05,
      orbitAngleRad: -0.05,
      reducedMotion: false,
    };
  }

  const wrappedMs =
    ((elapsedMs % CLOSING_CYCLE_DURATION_MS) + CLOSING_CYCLE_DURATION_MS) %
    CLOSING_CYCLE_DURATION_MS;
  const u = wrappedMs / CLOSING_CYCLE_DURATION_MS;

  // Periodic fade-out near end of cycle guarantees C^0/C^1 seamless wrap at u = 0 / 1
  const dissolveOut = u >= 0.88 ? 1 - windowEase(u, 0.88, 0.98) : 1;

  const pyramidOpacity = 0.88 + 0.12 * Math.sin(u * Math.PI * 2) * 0.5 + 0.06;
  const guideProgress = Math.min(1, 0.78 + 0.22 * (u < 0.5 ? windowEase(u, 0.02, 0.2) : dissolveOut));
  const seedPointScale =
    u < 0.88 ? 0.35 + 0.65 * windowEase(u, 0.06, 0.24) : 0.35 + 0.65 * dissolveOut;
  const planeProgress = u < 0.88 ? windowEase(u, 0.16, 0.44) : dissolveOut;
  const traceProgress = u < 0.88 ? windowEase(u, 0.38, 0.68) : dissolveOut;
  const sectionFillOpacity = u < 0.88 ? windowEase(u, 0.54, 0.75) : dissolveOut;
  const intersectionPointScale = u < 0.88 ? windowEase(u, 0.44, 0.7) : dissolveOut;
  const capLift =
    u < 0.88 ? 0.055 * windowEase(u, 0.58, 0.78) : 0.055 * dissolveOut;

  let phase: ClosingMotionPhase = "base-pyramid";
  if (u >= 0.74 && u < 0.92) {
    phase = "complete-settled";
  } else if (u >= 0.42) {
    phase = "section-intersection";
  } else if (u >= 0.2) {
    phase = "plane-emergence";
  }

  const orbitAngleRad = Math.sin(u * Math.PI * 2) * 0.13;

  return {
    phase,
    cycleProgress: u,
    pyramidOpacity: Math.min(1, Math.max(0.84, pyramidOpacity)),
    guideProgress,
    planeProgress,
    traceProgress,
    sectionFillOpacity,
    seedPointScale,
    intersectionPointScale,
    capLift,
    orbitAngleRad,
    reducedMotion: false,
  };
}

function worldToMathCoords(pos: Vec3Tuple): Vec3Tuple {
  return [
    pos[0] + MATH_CENTER[0],
    -pos[2] + MATH_CENTER[1],
    pos[1] + MATH_CENTER[2],
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

export function buildClosingPyramidRigData(): ClosingPyramidRigData {
  const pMap = LANDING_PYRAMID_SAMPLE.pointMap;
  const pointWorldMap: Record<string, Vec3Tuple> = {};
  const pointMathMap: Record<string, Vec3Tuple> = {};

  for (const [id, spec] of Object.entries(pMap)) {
    pointWorldMap[id] = [...spec.pos];
    pointMathMap[id] = worldToMathCoords(spec.pos);
  }

  const vec3 = (id: string) => {
    const p = pointWorldMap[id] ?? [0, 0, 0];
    return new THREE.Vector3(p[0], p[1], p[2]);
  };

  const S = vec3("S");
  const A = vec3("A");
  const B = vec3("B");
  const C = vec3("C");
  const D = vec3("D");

  const sectionIds = [...LANDING_PYRAMID_SAMPLE.sectionLoop];
  const sectionMathResiduals = sectionIds.map((id) => {
    const [mx, my, mz] = pointMathMap[id] ?? [0, 0, 0];
    return Math.abs(mx + my + 2 * mz - 6);
  });

  const loopPts = sectionIds.map(vec3);
  const pyramidCentroid = new THREE.Vector3()
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
    orientFaceOutward([D, C, B, A], pyramidCentroid),
    orientFaceOutward([A, B, S], pyramidCentroid),
    orientFaceOutward([B, C, S], pyramidCentroid),
    orientFaceOutward([C, D, S], pyramidCentroid),
    orientFaceOutward([D, A, S], pyramidCentroid),
  ];

  const lowerFrustumFaces: Vec3Tuple[][] = [];
  const upperCapFaces: Vec3Tuple[][] = [];

  for (const face of rawFaces) {
    const lo = clipPolygonHalfSpace(face, cutPlaneNormal, cutPlaneOffset, false);
    if (lo.length >= 3) {
      lowerFrustumFaces.push(lo.map((v) => [v.x, v.y, v.z]));
    }
    const hi = clipPolygonHalfSpace(face, cutPlaneNormal, cutPlaneOffset, true);
    if (hi.length >= 3) {
      upperCapFaces.push(hi.map((v) => [v.x, v.y, v.z]));
    }
  }

  // From viewing octant (+X, +Y, -Z), corner A and SA lie behind faces SBC/SCD
  const hiddenBackPairs = new Set(["S-A", "A-S", "A-B", "B-A", "D-A", "A-D"]);
  const solidEdges = LANDING_PYRAMID_SAMPLE.solidEdges.map((edge) => ({
    from: edge.from,
    to: edge.to,
    hidden: hiddenBackPairs.has(`${edge.from}-${edge.to}`),
  }));

  const guideEdges = LANDING_PYRAMID_SAMPLE.guideEdges.map((edge) => ({
    from: edge.from,
    to: edge.to,
  }));

  return {
    pointWorldMap,
    pointMathMap,
    sectionIds,
    sectionMathResiduals,
    planeQuadWorld: LANDING_PYRAMID_SAMPLE.planeQuad.map((p) => [...p]),
    lowerFrustumFaces,
    upperCapFaces,
    solidEdges,
    guideEdges,
  };
}

function buildFacesBufferGeometry(faces: readonly ClippedPolygonFace[]): THREE.BufferGeometry {
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

const UP_AXIS = new THREE.Vector3(0, 1, 0);

function createCylinderEdge(
  a: THREE.Vector3,
  b: THREE.Vector3,
  radius: number,
  colorHex: number,
  opacity: number,
  track: <T extends TrackedDisposable>(item: T) => T,
  anchorAtStart = false,
): THREE.Mesh {
  const len = a.distanceTo(b);
  const geo = track(new THREE.CylinderGeometry(radius, radius, len, 8, 1));
  if (anchorAtStart) {
    geo.translate(0, len / 2, 0);
  }
  const mat = track(
    new THREE.MeshBasicMaterial({
      color: colorHex,
      transparent: true,
      opacity,
    }),
  );
  const mesh = new THREE.Mesh(geo, mat);
  const dir = new THREE.Vector3().subVectors(b, a).normalize();
  mesh.quaternion.setFromUnitVectors(UP_AXIS, dir);
  if (anchorAtStart) {
    mesh.position.copy(a);
  } else {
    mesh.position.addVectors(a, b).multiplyScalar(0.5);
  }
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

export function projectClosingFallbackSvg(
  width = 480,
  height = 380,
  motionState: ClosingMotionState = evaluateClosingMotionState(0, true),
): ClosingFallbackProjection {
  const rig = buildClosingPyramidRigData();
  const [camX, camY, camZ] = LANDING_PYRAMID_SAMPLE.defaultCamera;
  const [lookX, lookY, lookZ] = LANDING_PYRAMID_SAMPLE.defaultLookAt;
  const camPos = new THREE.Vector3(camX * 0.86, camY * 0.86, camZ * 0.86);
  const lookAt = new THREE.Vector3(lookX, lookY + 0.40, lookZ);

  const forward = new THREE.Vector3().subVectors(lookAt, camPos).normalize();
  const right = new THREE.Vector3().crossVectors(forward, new THREE.Vector3(0, 1, 0)).normalize();
  const up = new THREE.Vector3().crossVectors(right, forward).normalize();

  const scale = Math.min(width, height) * 0.098;
  const cx = width * 0.51;
  const cy = height * 0.52;

  const projectVec = (v: readonly [number, number, number]): ProjectedPoint2D => {
    const relX = v[0] - lookAt.x;
    const relY = v[1] - lookAt.y;
    const relZ = v[2] - lookAt.z;
    const px = relX * right.x + relY * right.y + relZ * right.z;
    const py = relX * up.x + relY * up.y + relZ * up.z;
    const depth = relX * forward.x + relY * forward.y + relZ * forward.z;
    const persp = 1 / (1 + depth * 0.032);
    return {
      x: Number((cx + px * scale * persp).toFixed(2)),
      y: Number((cy - py * scale * persp).toFixed(2)),
      depth,
    };
  };

  const points: Record<string, ProjectedPoint2D> = {};
  for (const [id, vec] of Object.entries(rig.pointWorldMap)) {
    points[id] = projectVec(vec);
  }

  const toPolyStr = (vecs: readonly Vec3Tuple[]) =>
    vecs
      .map((v) => {
        const p = projectVec(v);
        return `${p.x},${p.y}`;
      })
      .join(" ");

  const lowerPolygons = rig.lowerFrustumFaces.map(toPolyStr);
  const upperPolygons = rig.upperCapFaces.map(toPolyStr);
  const planePolygonPoints = toPolyStr(rig.planeQuadWorld);
  const sectionPts2D = rig.sectionIds.map((id) => points[id]);
  const sectionPolygonPoints = sectionPts2D.map((p) => `${p.x},${p.y}`).join(" ");

  const edgeCount = sectionPts2D.length;
  const tracedEdges = sectionPts2D.map((startPt, idx) => {
    const endPt = sectionPts2D[(idx + 1) % edgeCount];
    const edgeStart = idx / edgeCount;
    const edgeEnd = (idx + 1) / edgeCount;
    const localProgress = Math.max(
      0,
      Math.min(1, (motionState.traceProgress - edgeStart) / (edgeEnd - edgeStart)),
    );
    return {
      x1: startPt.x,
      y1: startPt.y,
      x2: Number((startPt.x + (endPt.x - startPt.x) * localProgress).toFixed(2)),
      y2: Number((startPt.y + (endPt.y - startPt.y) * localProgress).toFixed(2)),
      progress: localProgress,
    };
  });

  const hiddenEdges: {
    id: string;
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    isAltitude: boolean;
  }[] = [];
  const solidEdges: { x1: number; y1: number; x2: number; y2: number }[] = [];

  for (const e of rig.solidEdges) {
    const p1 = points[e.from];
    const p2 = points[e.to];
    if (!p1 || !p2) continue;
    if (e.hidden) {
      hiddenEdges.push({
        id: `${e.from}-${e.to}`,
        x1: p1.x,
        y1: p1.y,
        x2: p2.x,
        y2: p2.y,
        isAltitude: e.from === "S" && e.to === "A",
      });
    } else {
      solidEdges.push({ x1: p1.x, y1: p1.y, x2: p2.x, y2: p2.y });
    }
  }

  for (const g of rig.guideEdges) {
    const p1 = points[g.from];
    const p2 = points[g.to];
    if (p1 && p2) {
      hiddenEdges.push({
        id: `${g.from}-${g.to}`,
        x1: p1.x,
        y1: p1.y,
        x2: p2.x,
        y2: p2.y,
        isAltitude: false,
      });
    }
  }

  const baseCenter2D = projectVec([0, -2.65, 0]);
  return {
    width,
    height,
    points,
    planePolygonPoints,
    sectionPolygonPoints,
    tracedEdges,
    lowerPolygons,
    upperPolygons,
    hiddenEdges,
    solidEdges,
    contactBase: {
      x: baseCenter2D.x,
      y: baseCenter2D.y + 8,
      rx: scale * 2.45,
      ry: scale * 0.72,
    },
  };
}

function shouldAttemptWebGL(): boolean {
  if (typeof window === "undefined" || typeof document === "undefined") return false;
  if (window.location.search.includes("no_webgl=1")) return false;
  return typeof window.WebGLRenderingContext !== "undefined";
}

function readPreviewPhaseOverride(): "mid" | "settled" | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  const raw = params.get("cta_phase");
  if (raw === "mid" || raw === "settled") return raw;
  return null;
}

export function LandingClosingScene3D() {
  const stageRef = useRef<HTMLDivElement | null>(null);
  const hostRef = useRef<HTMLDivElement | null>(null);
  const targetTiltRef = useRef({ x: 0, y: 0 });
  const wakeRef = useRef<(() => void) | null>(null);

  const [webglReady, setWebglReady] = useState(true);
  const [contextLost, setContextLost] = useState(false);
  const [phaseLabel, setPhaseLabel] = useState<ClosingMotionPhase>("base-pyramid");
  const [fallbackState, setFallbackState] = useState<ClosingMotionState>(() =>
    evaluateClosingMotionState(0, true, readPreviewPhaseOverride() ?? "settled"),
  );

  const fallbackProjection = useMemo(
    () => projectClosingFallbackSvg(480, 380, fallbackState),
    [fallbackState],
  );

  useEffect(() => {
    const stage = stageRef.current;
    const host = hostRef.current;
    if (!stage || !host || typeof window === "undefined") return;

    const previewOverride = readPreviewPhaseOverride();
    const reducedQuery = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    let reducedMotion = Boolean(reducedQuery?.matches);

    if (!shouldAttemptWebGL()) {
      setWebglReady(false);
      const nextState = evaluateClosingMotionState(0, true, previewOverride ?? "settled");
      setFallbackState(nextState);
      setPhaseLabel(nextState.phase);
      return;
    }

    let disposed = false;
    let rendererInitialized = false;
    let cleanupWebGL: (() => void) | null = null;

    const initWebGL = () => {
      if (disposed || rendererInitialized) return;
      rendererInitialized = true;

      const canvas = document.createElement("canvas");
      canvas.className = "axo-v14-closing-canvas";
      canvas.setAttribute("aria-hidden", "true");

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
        const nextState = evaluateClosingMotionState(0, true, previewOverride ?? "settled");
        setFallbackState(nextState);
        setPhaseLabel(nextState.phase);
        return;
      }

      const disposables: TrackedDisposable[] = [];
      const track = <T extends TrackedDisposable>(item: T): T => {
        disposables.push(item);
        return item;
      };

      host.appendChild(canvas);
      setWebglReady(true);

      const width = Math.max(240, host.clientWidth || 480);
      const height = Math.max(220, host.clientHeight || 380);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.setSize(width, height, false);
      renderer.setClearColor(0x000000, 0);

      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(34, width / height, 0.1, 100);
      const [baseCamX, baseCamY, baseCamZ] = LANDING_PYRAMID_SAMPLE.defaultCamera;
      const [lookX, lookY, lookZ] = LANDING_PYRAMID_SAMPLE.defaultLookAt;
      const camVec = new THREE.Vector3(baseCamX * 0.86, baseCamY * 0.86, baseCamZ * 0.86);
      const lookVec = new THREE.Vector3(lookX, lookY + 0.40, lookZ);
      const camOffset = new THREE.Vector3().subVectors(camVec, lookVec);
      const rotatedOffset = new THREE.Vector3();
      const yAxis = new THREE.Vector3(0, 1, 0);

      const updateCameraFraming = (w: number, h: number, orbitAngleRad: number, tiltX: number, tiltY: number) => {
        const aspect = Math.max(0.68, w / Math.max(1, h));
        const aspectScale = aspect < 1.16 ? 1 + (1.16 - aspect) * 0.55 : 1;
        const shortScale = h <= 290 ? 1.07 : 1;
        const distanceScale = Math.max(aspectScale, shortScale);
        rotatedOffset
          .copy(camOffset)
          .multiplyScalar(distanceScale)
          .applyAxisAngle(yAxis, orbitAngleRad + tiltX * 0.28);
        rotatedOffset.y += tiltY * 0.85;
        camera.position.copy(lookVec).add(rotatedOffset);
        camera.lookAt(lookVec);
      };

      updateCameraFraming(width, height, 0, 0, 0);

      // Lighting: sculpted architectural key + cool rim fill for clear face separation
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.42);
      const keyLight = new THREE.DirectionalLight(0xfffaf2, 1.18);
      keyLight.position.set(11, 15, -5);
      const fillLight = new THREE.DirectionalLight(0xdcebfa, 0.56);
      fillLight.position.set(-10, 4, 10);
      scene.add(ambientLight, keyLight, fillLight);

      const rigData = buildClosingPyramidRigData();
      const vec3 = (id: string) => {
        const p = rigData.pointWorldMap[id] ?? [0, 0, 0];
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
      const loopPts = rigData.sectionIds.map(vec3);

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

      const rawPlaneNormal = new THREE.Vector3()
        .subVectors(loopPts[1], loopPts[0])
        .cross(new THREE.Vector3().subVectors(loopPts[2], loopPts[0]))
        .normalize();
      const cutPlaneNormal =
        rawPlaneNormal.dot(new THREE.Vector3().subVectors(S, loopPts[0])) >= 0
          ? rawPlaneNormal
          : rawPlaneNormal.negate();
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
      for (const f of rawFaces) {
        const lo = clipPolygonHalfSpace(f, cutPlaneNormal, cutPlaneOffset, false);
        if (lo.length >= 3) lowerFaces.push({ pts: lo });
        const hi = clipPolygonHalfSpace(f, cutPlaneNormal, cutPlaneOffset, true);
        if (hi.length >= 3) upperFaces.push({ pts: hi });
      }

      const root = new THREE.Group();
      scene.add(root);

      // 1. Ground contact AO discs under ABCD (depthWrite disabled)
      const shadowGroup = new THREE.Group();
      const shadowOuterGeo = track(new THREE.CircleGeometry(2.85, 48));
      shadowOuterGeo.rotateX(-Math.PI / 2);
      const shadowOuterMat = track(
        new THREE.MeshBasicMaterial({
          color: 0x1f201e,
          transparent: true,
          opacity: 0.045,
          depthWrite: false,
        }),
      );
      const shadowOuter = new THREE.Mesh(shadowOuterGeo, shadowOuterMat);
      shadowOuter.position.set(baseCenter.x, A.y - 0.055, baseCenter.z);
      shadowOuter.renderOrder = 0;
      shadowGroup.add(shadowOuter);

      const shadowInnerGeo = track(new THREE.CircleGeometry(1.92, 40));
      shadowInnerGeo.rotateX(-Math.PI / 2);
      const shadowInnerMat = track(
        new THREE.MeshBasicMaterial({
          color: 0x1f201e,
          transparent: true,
          opacity: 0.075,
          depthWrite: false,
        }),
      );
      const shadowInner = new THREE.Mesh(shadowInnerGeo, shadowInnerMat);
      shadowInner.position.set(baseCenter.x, A.y - 0.045, baseCenter.z);
      shadowInner.renderOrder = 1;
      shadowGroup.add(shadowInner);
      root.add(shadowGroup);

      // 2. Sculpted Pyramid Volumes (MeshStandardMaterial for authentic directional shading)
      const lowerGeo = track(buildFacesBufferGeometry(lowerFaces));
      const lowerMat = track(
        new THREE.MeshStandardMaterial({
          color: 0xf3f1ec,
          roughness: 0.88,
          metalness: 0.02,
          flatShading: true,
          transparent: true,
          opacity: 0.9,
          side: THREE.DoubleSide,
          depthWrite: false,
        }),
      );
      const lowerMesh = new THREE.Mesh(lowerGeo, lowerMat);
      lowerMesh.renderOrder = 2;
      root.add(lowerMesh);

      const upperGroup = new THREE.Group();
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
      upperGroup.add(upperMesh);
      root.add(upperGroup);

      // 3. Edges & Construction Guides (front crisp cylinders, back dashed lines)
      const visibleSolidMeshes: THREE.Mesh[] = [];
      const hiddenEdgeLines: { line: THREE.Line; baseOpacity: number }[] = [];

      for (const edge of rigData.solidEdges) {
        const pFrom = vec3(edge.from);
        const pTo = vec3(edge.to);
        if (edge.hidden) {
          const isAlt = edge.from === "S" && edge.to === "A";
          const line = createDashedEdge(
            pFrom,
            pTo,
            isAlt ? 0x0075de : 0x615d59,
            isAlt ? 0.56 : 0.44,
            0.16,
            0.12,
            track,
          );
          line.renderOrder = 2;
          hiddenEdgeLines.push({ line, baseOpacity: isAlt ? 0.56 : 0.44 });
          root.add(line);
        } else {
          const cyl = createCylinderEdge(pFrom, pTo, 0.021, 0x1f201e, 0.9, track);
          cyl.renderOrder = 6;
          visibleSolidMeshes.push(cyl);
          root.add(cyl);
        }
      }

      for (const guide of rigData.guideEdges) {
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
        hiddenEdgeLines.push({ line, baseOpacity: 0.32 });
        root.add(line);
      }

      // Perpendicular symbol at A for SA perp (ABCD)
      const unitB = new THREE.Vector3().subVectors(B, A).normalize().multiplyScalar(0.3);
      const unitS = new THREE.Vector3().subVectors(S, A).normalize().multiplyScalar(0.3);
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
      const qPts = rigData.planeQuadWorld.map((v) => new THREE.Vector3(v[0], v[1], v[2]));
      const planeCenter = new THREE.Vector3()
        .add(qPts[0])
        .add(qPts[1])
        .add(qPts[2])
        .add(qPts[3])
        .divideScalar(4);
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
          0.016,
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

      // 5. Cross-section Pentagon MENPF (progressive border trace + shaded orange face)
      const sectionGroup = new THREE.Group();
      const offsetLoop = loopPts.map((pt) =>
        pt.clone().addScaledVector(cutPlaneNormal, 0.012),
      );
      const sectionGeo = track(buildFacesBufferGeometry([{ pts: offsetLoop }]));
      const sectionMat = track(
        new THREE.MeshStandardMaterial({
          color: 0xe6620a,
          emissive: 0x993d00,
          emissiveIntensity: 0.24,
          roughness: 0.58,
          metalness: 0.04,
          flatShading: true,
          transparent: true,
          opacity: 0.92,
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
          0.028,
          0x793400,
          0.98,
          track,
          true,
        );
        seg.renderOrder = 7;
        sectionBorderCyls.push(seg);
        sectionGroup.add(seg);
      }
      root.add(sectionGroup);

      // 6. Vertex Nodes (Structural ink, seed midpoints blue, intersection orange)
      const nodeGeo = track(new THREE.SphereGeometry(0.068, 16, 16));
      const baseNodeMat = track(
        new THREE.MeshBasicMaterial({ color: 0x1f201e, transparent: true, opacity: 0.92 }),
      );
      const hiddenNodeMat = track(
        new THREE.MeshBasicMaterial({ color: 0x5c5b57, transparent: true, opacity: 0.34 }),
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
        dot.scale.setScalar(1.08);
        dot.renderOrder = 8;
        root.add(dot);
        return dot;
      });

      const interDots = [E, F].map((pt) => {
        const dot = new THREE.Mesh(nodeGeo, interNodeMat);
        dot.position.copy(pt).addScaledVector(cutPlaneNormal, 0.015);
        dot.scale.setScalar(1.14);
        dot.renderOrder = 8;
        root.add(dot);
        return dot;
      });

      // Lifecycle state
      let isInView = true;
      let isLost = false;
      let rafId = 0;
      const startMs = performance.now();
      let curTiltX = 0;
      let curTiltY = 0;
      let lastReportedPhase: ClosingMotionPhase = "base-pyramid";

      const renderAtTime = (nowMs: number) => {
        if (disposed || isLost) return;
        const elapsed = nowMs - startMs;
        const motion = evaluateClosingMotionState(elapsed, reducedMotion, previewOverride);

        if (motion.phase !== lastReportedPhase) {
          lastReportedPhase = motion.phase;
          setPhaseLabel(motion.phase);
        }

        const damp = reducedMotion ? 1 : 0.14;
        curTiltX += (targetTiltRef.current.x - curTiltX) * damp;
        curTiltY += (targetTiltRef.current.y - curTiltY) * damp;

        shadowOuterMat.opacity = 0.042 * motion.pyramidOpacity;
        shadowInnerMat.opacity = 0.072 * motion.pyramidOpacity;
        baseNodeMat.opacity = 0.92 * motion.pyramidOpacity;
        hiddenNodeMat.opacity = 0.34 * motion.pyramidOpacity;

        // Emphasize cross-section during Phase D by easing upper cap subtly
        const phaseEmphasis = 1 - motion.sectionFillOpacity * 0.18;
        lowerMat.opacity = 0.9 * motion.pyramidOpacity * phaseEmphasis;
        upperMat.opacity = 0.2 * motion.pyramidOpacity * phaseEmphasis;
        upperGroup.position.copy(cutPlaneNormal).multiplyScalar(motion.capLift);

        for (const cyl of visibleSolidMeshes) {
          (cyl.material as THREE.MeshBasicMaterial).opacity =
            0.9 * motion.pyramidOpacity * (1 - motion.sectionFillOpacity * 0.14);
        }
        for (const entry of hiddenEdgeLines) {
          (entry.line.material as THREE.LineDashedMaterial).opacity =
            entry.baseOpacity * motion.guideProgress;
        }
        raMat.opacity = 0.56 * motion.guideProgress;

        planeMat.opacity = 0.22 * motion.planeProgress;
        planeGroup.position
          .copy(planeCenter)
          .addScaledVector(cutPlaneNormal, (1 - motion.planeProgress) * 0.65);
        for (const rim of planeRimCyls) {
          (rim.material as THREE.MeshBasicMaterial).opacity = 0.84 * motion.planeProgress;
        }

        const edgeCount = sectionBorderCyls.length;
        for (let i = 0; i < edgeCount; i++) {
          const seg = sectionBorderCyls[i];
          const edgeStart = i / edgeCount;
          const edgeEnd = (i + 1) / edgeCount;
          const localP = Math.max(
            0,
            Math.min(1, (motion.traceProgress - edgeStart) / (edgeEnd - edgeStart)),
          );
          seg.visible = localP > 0.01;
          seg.scale.set(1, Math.max(0.01, localP), 1);
          (seg.material as THREE.MeshBasicMaterial).opacity = 0.98 * Math.min(1, localP * 2);
        }

        sectionMat.opacity = 0.92 * motion.sectionFillOpacity;
        sectionMesh.visible = motion.sectionFillOpacity > 0.01;

        seedNodeMat.opacity = 0.35 + 0.65 * motion.seedPointScale;
        for (const d of seedDots) {
          d.scale.setScalar(0.8 + 0.3 * motion.seedPointScale);
        }

        interNodeMat.opacity = motion.intersectionPointScale;
        for (const d of interDots) {
          d.visible = motion.intersectionPointScale > 0.03;
          d.scale.setScalar(Math.max(0.01, 1.14 * motion.intersectionPointScale));
        }

        const currentWidth = host.clientWidth || width;
        const currentHeight = host.clientHeight || height;
        updateCameraFraming(
          currentWidth,
          currentHeight,
          motion.orbitAngleRad,
          curTiltX,
          curTiltY,
        );

        renderer.render(scene, camera);
      };

      const needsContinuousLoop = () =>
        !disposed &&
        !isLost &&
        isInView &&
        !document.hidden &&
        !reducedMotion &&
        previewOverride === null;

      const tick = (nowMs: number) => {
        rafId = 0;
        if (disposed || isLost) return;
        renderAtTime(nowMs);
        if (needsContinuousLoop()) {
          rafId = window.requestAnimationFrame(tick);
        }
      };

      const wake = () => {
        if (disposed || isLost || !isInView || document.hidden) return;
        if (rafId === 0) {
          rafId = window.requestAnimationFrame(tick);
        }
      };

      wakeRef.current = wake;

      const ro =
        typeof ResizeObserver !== "undefined"
          ? new ResizeObserver(() => {
              if (disposed || !host) return;
              const w = Math.max(240, host.clientWidth);
              const h = Math.max(220, host.clientHeight);
              camera.aspect = w / h;
              camera.updateProjectionMatrix();
              renderer.setSize(w, h, false);
              if (reducedMotion || previewOverride !== null) {
                renderAtTime(performance.now());
              } else {
                wake();
              }
            })
          : null;
      ro?.observe(host);

      const viewIo =
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
              { threshold: 0.05 },
            )
          : null;
      viewIo?.observe(stage);

      const onVisibility = () => {
        if (document.hidden) {
          if (rafId) {
            window.cancelAnimationFrame(rafId);
            rafId = 0;
          }
        } else if (isInView) {
          wake();
        }
      };
      document.addEventListener("visibilitychange", onVisibility);

      const onMotionChange = (ev: MediaQueryListEvent) => {
        reducedMotion = ev.matches;
        if (reducedMotion && rafId) {
          window.cancelAnimationFrame(rafId);
          rafId = 0;
        }
        renderAtTime(performance.now());
        if (!reducedMotion && isInView) {
          wake();
        }
      };
      reducedQuery?.addEventListener?.("change", onMotionChange);

      const onContextLost = (ev: Event) => {
        ev.preventDefault();
        isLost = true;
        setContextLost(true);
        if (rafId) {
          window.cancelAnimationFrame(rafId);
          rafId = 0;
        }
      };
      const onContextRestored = () => {
        isLost = false;
        setContextLost(false);
        renderAtTime(performance.now());
        wake();
      };
      canvas.addEventListener("webglcontextlost", onContextLost);
      canvas.addEventListener("webglcontextrestored", onContextRestored);

      renderAtTime(performance.now());
      wake();

      cleanupWebGL = () => {
        disposed = true;
        wakeRef.current = null;
        if (rafId) {
          window.cancelAnimationFrame(rafId);
          rafId = 0;
        }
        ro?.disconnect();
        viewIo?.disconnect();
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
    };

    const lazyObserver =
      typeof IntersectionObserver !== "undefined"
        ? new IntersectionObserver(
            (entries) => {
              if (entries.some((e) => e.isIntersecting)) {
                lazyObserver?.disconnect();
                initWebGL();
              }
            },
            { rootMargin: "260px 0px", threshold: 0.01 },
          )
        : null;

    if (lazyObserver) {
      lazyObserver.observe(stage);
    } else {
      initWebGL();
    }

    return () => {
      disposed = true;
      lazyObserver?.disconnect();
      cleanupWebGL?.();
    };
  }, []);

  const showFallback = !webglReady || contextLost;

  return (
    <div
      ref={stageRef}
      id="landing-closing-scene3d"
      className="axo-v14-closing-stage"
      role="img"
      aria-label="Mô hình 3D hình chóp S.ABCD và thiết diện ngũ giác MENPF tạo bởi mặt phẳng (MNP)"
      data-cta-visual={showFallback ? "svg-fallback" : "webgl"}
      data-cta-phase={phaseLabel}
      onPointerMove={(event) => {
        if (window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches) return;
        const rect = event.currentTarget.getBoundingClientRect();
        if (!rect.width || !rect.height) return;
        const nx = (event.clientX - rect.left) / rect.width - 0.5;
        const ny = (event.clientY - rect.top) / rect.height - 0.5;
        targetTiltRef.current = { x: nx * 0.48, y: -ny * 0.28 };
        wakeRef.current?.();
      }}
      onPointerLeave={() => {
        targetTiltRef.current = { x: 0, y: 0 };
        wakeRef.current?.();
      }}
    >
      <div
        ref={hostRef}
        className="axo-v14-closing-canvas-host"
        hidden={showFallback}
      />

      {showFallback && (
        <div className="axo-v14-closing-fallback">
          <svg
            className="axo-v14-closing-fallback-svg"
            viewBox={`0 0 ${fallbackProjection.width} ${fallbackProjection.height}`}
            aria-hidden="true"
          >
            <ellipse
              className="axo-v14-svg-contact-halo"
              cx={fallbackProjection.contactBase.x}
              cy={fallbackProjection.contactBase.y}
              rx={fallbackProjection.contactBase.rx}
              ry={fallbackProjection.contactBase.ry}
            />
            <ellipse
              className="axo-v14-svg-contact-core"
              cx={fallbackProjection.contactBase.x}
              cy={fallbackProjection.contactBase.y}
              rx={fallbackProjection.contactBase.rx * 0.68}
              ry={fallbackProjection.contactBase.ry * 0.68}
            />

            {fallbackProjection.lowerPolygons.map((pts, idx) => (
              <polygon key={`lo-${idx}`} className="axo-v14-svg-solid-lower" points={pts} />
            ))}

            {fallbackProjection.hiddenEdges.map((edge) => (
              <line
                key={edge.id}
                className={edge.isAltitude ? "axo-v14-svg-edge-altitude" : "axo-v14-svg-edge-hidden"}
                x1={edge.x1}
                y1={edge.y1}
                x2={edge.x2}
                y2={edge.y2}
              />
            ))}

            <polygon
              className="axo-v14-svg-cutting-plane"
              points={fallbackProjection.planePolygonPoints}
              opacity={fallbackState.planeProgress}
            />

            <polygon
              className="axo-v14-svg-section-poly"
              points={fallbackProjection.sectionPolygonPoints}
              opacity={fallbackState.sectionFillOpacity}
            />

            {fallbackProjection.upperPolygons.map((pts, idx) => (
              <polygon key={`hi-${idx}`} className="axo-v14-svg-solid-upper" points={pts} />
            ))}

            {fallbackProjection.solidEdges.map((edge, idx) => (
              <line
                key={`solid-${idx}`}
                className="axo-v14-svg-edge-solid"
                x1={edge.x1}
                y1={edge.y1}
                x2={edge.x2}
                y2={edge.y2}
              />
            ))}

            {fallbackProjection.tracedEdges.map((edge, idx) =>
              edge.progress > 0.01 ? (
                <line
                  key={`trace-${idx}`}
                  className="axo-v14-svg-section-poly"
                  x1={edge.x1}
                  y1={edge.y1}
                  x2={edge.x2}
                  y2={edge.y2}
                  fill="none"
                />
              ) : null,
            )}

            {["S", "A", "B", "C", "D"].map((id) => {
              const p = fallbackProjection.points[id];
              return p ? (
                <circle key={id} className="axo-v14-svg-vertex-dot" cx={p.x} cy={p.y} r="3.4" />
              ) : null;
            })}

            {["M", "N", "P"].map((id) => {
              const p = fallbackProjection.points[id];
              return p ? (
                <circle key={id} className="axo-v14-svg-seed-dot" cx={p.x} cy={p.y} r="4.2" />
              ) : null;
            })}

            {["E", "F"].map((id) => {
              const p = fallbackProjection.points[id];
              return p ? (
                <circle
                  key={id}
                  className="axo-v14-svg-section-dot"
                  cx={p.x}
                  cy={p.y}
                  r="4.4"
                  opacity={fallbackState.intersectionPointScale}
                />
              ) : null;
            })}
          </svg>
        </div>
      )}
    </div>
  );
}
