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
  readonly capLift: number;
  readonly orbitOffsetRad: number;
  readonly settled: boolean;
}

export const HERO_STORYBOARD_MS = 3600;
export const HERO_SECTION_FILL_OPACITY = 0.5;

interface ClippedPolygonFace {
  readonly pts: THREE.Vector3[];
}

interface TrackedDisposable {
  dispose(): void;
}

interface ProjectedCallout {
  readonly id: string;
  readonly label: string;
  readonly role: "vertex" | "seed" | "intersection" | "plane";
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
      capLift: 0.085,
      orbitOffsetRad: 0,
      settled: true,
    };
  }

  const p = clamp01(elapsedMs / HERO_STORYBOARD_MS);
  let beat: HeroStoryboardBeat = "solid-emergence";
  if (p >= 0.76) beat = "section-settled";
  else if (p >= 0.48) beat = "plane-intersection";
  else if (p >= 0.24) beat = "seed-anchors";

  const solidReveal = 0.35 + 0.65 * clampPhase(p, 0.0, 0.24);
  const seedReveal = clampPhase(p, 0.2, 0.46);
  const planeSweep = clampPhase(p, 0.44, 0.68);
  const traceProgress = clampPhase(p, 0.52, 0.8);
  const sectionFill = clampPhase(p, 0.74, 0.98);
  const capLift = 0.085 * clampPhase(p, 0.76, 1.0);
  const orbitOffsetRad = (1 - clampPhase(p, 0.0, 0.92)) * 0.14;

  return {
    beat,
    progress: p,
    solidReveal,
    seedReveal,
    planeSweep,
    traceProgress,
    sectionFill,
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
        cx="268"
        cy="366"
        rx="148"
        ry="24"
      />
      <ellipse
        className="axo-v14-svg-contact-core"
        cx="268"
        cy="366"
        rx="106"
        ry="17"
      />

      <polygon
        className="axo-v14-svg-solid-base"
        points="152,340 350,368 424,296 220,282"
      />
      <polygon
        className="axo-v14-svg-solid-lower"
        points="152,340 350,368 424,296 338,208 268,194 188,236"
      />
      <polygon
        className="axo-v14-svg-solid-upper"
        points="220,86 188,236 268,194 338,208"
      />

      <line className="axo-v14-svg-edge-hidden" x1="220" y1="282" x2="152" y2="340" />
      <line className="axo-v14-svg-edge-hidden" x1="220" y1="282" x2="424" y2="296" />
      <line className="axo-v14-svg-edge-altitude" x1="220" y1="86" x2="220" y2="282" />

      <line className="axo-v14-svg-edge-solid" x1="152" y1="340" x2="350" y2="368" />
      <line className="axo-v14-svg-edge-solid" x1="350" y1="368" x2="424" y2="296" />
      <line className="axo-v14-svg-edge-solid" x1="152" y1="340" x2="188" y2="236" />
      <line className="axo-v14-svg-edge-solid" x1="350" y1="368" x2="268" y2="194" />
      <line className="axo-v14-svg-edge-solid" x1="424" y1="296" x2="338" y2="208" />

      <polygon
        className="axo-v14-svg-cutting-plane"
        points="106,256 372,294 438,192 174,168"
      />
      <polygon
        className="axo-v14-svg-section-poly"
        points="188,236 248,284 316,274 338,208 268,194"
      />

      <circle className="axo-v14-svg-vertex-dot" cx="220" cy="86" r="3.4" />
      <circle className="axo-v14-svg-seed-dot" cx="188" cy="236" r="4.0" />
      <circle className="axo-v14-svg-seed-dot" cx="316" cy="274" r="4.0" />
      <circle className="axo-v14-svg-seed-dot" cx="338" cy="208" r="4.0" />
      <circle className="axo-v14-svg-section-dot" cx="248" cy="284" r="4.2" />
      <circle className="axo-v14-svg-section-dot" cx="268" cy="194" r="4.2" />

      <text className="axo-v14-svg-vertex-text" x="220" y="74">S</text>
      <text className="axo-v14-svg-label-seed" x="174" y="232">M</text>
      <text className="axo-v14-svg-label-seed" x="320" y="294">N</text>
      <text className="axo-v14-svg-label-seed" x="354" y="206">P</text>
      <text className="axo-v14-svg-label-inter" x="242" y="302">E</text>
      <text className="axo-v14-svg-label-inter" x="268" y="180">F</text>
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
    const camera = new THREE.PerspectiveCamera(34, width / height, 0.1, 100);
    const [camX, camY, camZ] = LANDING_PYRAMID_SAMPLE.defaultCamera;
    const [lookX, lookY, lookZ] = LANDING_PYRAMID_SAMPLE.defaultLookAt;
    camera.position.set(camX * 0.94, camY * 0.94, camZ * 0.94);
    camera.lookAt(lookX, lookY + 0.16, lookZ);

    const ambientLight = new THREE.AmbientLight(0xfffdf9, 2.1);
    const keyLight = new THREE.DirectionalLight(0xfffaf0, 2.15);
    keyLight.position.set(14, 15, -9);
    const fillLight = new THREE.DirectionalLight(0xeef4fc, 1.05);
    fillLight.position.set(-6, 10, -12);
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

    // 1. Contact shadow & altitude SA perp (ABCD)
    const shadowOuterGeo = track(new THREE.CircleGeometry(2.52, 48));
    shadowOuterGeo.rotateX(-Math.PI / 2);
    const shadowOuterMat = track(
      new THREE.MeshBasicMaterial({
        color: 0x191918,
        transparent: true,
        opacity: 0.036,
        depthWrite: false,
      }),
    );
    const shadowOuterMesh = new THREE.Mesh(shadowOuterGeo, shadowOuterMat);
    shadowOuterMesh.position.set(baseCenter.x, A.y - 0.04, baseCenter.z);
    shadowOuterMesh.renderOrder = 0;
    root.add(shadowOuterMesh);

    const shadowInnerGeo = track(new THREE.CircleGeometry(1.76, 40));
    shadowInnerGeo.rotateX(-Math.PI / 2);
    const shadowInnerMat = track(
      new THREE.MeshBasicMaterial({
        color: 0x191918,
        transparent: true,
        opacity: 0.058,
        depthWrite: false,
      }),
    );
    const shadowInnerMesh = new THREE.Mesh(shadowInnerGeo, shadowInnerMat);
    shadowInnerMesh.position.set(baseCenter.x, A.y - 0.032, baseCenter.z);
    shadowInnerMesh.renderOrder = 1;
    root.add(shadowInnerMesh);

    const saLowerLine = createLineSegment(A, M, 0x0075de, 0.56, true, track);
    saLowerLine.renderOrder = 2;
    root.add(saLowerLine);

    const uAB = new THREE.Vector3().subVectors(B, A).normalize().multiplyScalar(0.26);
    const uAS = new THREE.Vector3().subVectors(S, A).normalize().multiplyScalar(0.26);
    const footCorner = A.clone().add(uAB).add(uAS);
    const rightAngle1 = createLineSegment(A.clone().add(uAS), footCorner, 0x0075de, 0.58, false, track);
    const rightAngle2 = createLineSegment(A.clone().add(uAB), footCorner, 0x0075de, 0.58, false, track);
    root.add(rightAngle1, rightAngle2);

    // 2. Lower Frustum Volume + Split Lower Edges (below plane x + y + 2z = 6)
    const lowerGroup = new THREE.Group();
    const lowerGeo = track(buildFacesBufferGeometry(lowerFaces));
    const lowerMat = track(
      new THREE.MeshStandardMaterial({
        color: 0xfaf7f2,
        emissive: 0x38342e,
        emissiveIntensity: 0.28,
        roughness: 0.86,
        metalness: 0.02,
        flatShading: true,
        transparent: true,
        opacity: 0.86,
        side: THREE.DoubleSide,
      }),
    );
    const lowerMesh = new THREE.Mesh(lowerGeo, lowerMat);
    lowerMesh.renderOrder = 2;
    lowerGroup.add(lowerMesh);

    const lowerVisibleSegs: readonly [THREE.Vector3, THREE.Vector3][] = [
      [B, E],
      [D, F],
      [B, N],
      [D, P],
    ];
    const lowerSolidEdgeCyls: THREE.Mesh[] = [];
    for (const [u, v] of lowerVisibleSegs) {
      const cyl = createCylinderEdge(u, v, 0.02, 0x191918, 0.88, track);
      cyl.renderOrder = 6;
      lowerSolidEdgeCyls.push(cyl);
      lowerGroup.add(cyl);
    }
    const hiddenBaseLines: THREE.Line[] = [
      createLineSegment(A, B, 0x615d59, 0.46, true, track),
      createLineSegment(A, D, 0x615d59, 0.46, true, track),
    ];
    for (const hl of hiddenBaseLines) {
      hl.renderOrder = 2;
      lowerGroup.add(hl);
    }

    const nodeGeo = track(new THREE.SphereGeometry(0.058, 16, 16));
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

    // 3. Upper Cap Volume + Split Upper Edges (moves together cleanly along cutPlaneNormal)
    const upperGroup = new THREE.Group();
    const upperGeo = track(buildFacesBufferGeometry(upperFaces));
    const upperMat = track(
      new THREE.MeshStandardMaterial({
        color: 0xffffff,
        roughness: 0.78,
        metalness: 0.02,
        flatShading: true,
        transparent: true,
        opacity: 0.24,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const upperMesh = new THREE.Mesh(upperGeo, upperMat);
    upperMesh.renderOrder = 3;
    upperGroup.add(upperMesh);

    const upperEdgeLines: THREE.Line[] = [];
    for (const [u, v] of [
      [S, E],
      [S, F],
      [S, C],
      [N, C],
      [P, C],
    ] as const) {
      const ln = createLineSegment(u, v, 0x31302e, 0.66, false, track);
      ln.renderOrder = 6;
      upperEdgeLines.push(ln);
      upperGroup.add(ln);
    }
    const saUpperLine = createLineSegment(M, S, 0x0075de, 0.48, true, track);
    saUpperLine.renderOrder = 2;
    upperGroup.add(saUpperLine);

    const dotS = new THREE.Mesh(nodeGeo, baseNodeMat);
    dotS.position.copy(S);
    dotS.renderOrder = 8;
    const dotC = new THREE.Mesh(nodeGeo, baseNodeMat);
    dotC.position.copy(C);
    dotC.renderOrder = 8;
    upperGroup.add(dotS, dotC);
    root.add(upperGroup);

    // 4. Cutting Plane (MNP)
    const planeGroup = new THREE.Group();
    const planeQuadVecs = LANDING_PYRAMID_SAMPLE.planeQuad.map(
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
        opacity: 0.18,
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

    // 5. Cross-section Pentagon MENPF (balanced translucent amber 0.52 + progressive perimeter)
    const sectionGroup = new THREE.Group();
    const sectionOffsetLoop = loopPts.map((pt) =>
      pt.clone().addScaledVector(cutPlaneNormal, 0.008),
    );
    const secGeo = track(buildFacesBufferGeometry([{ pts: sectionOffsetLoop }]));
    const secMat = track(
      new THREE.MeshStandardMaterial({
        color: 0xe6620a,
        emissive: 0x993d00,
        emissiveIntensity: 0.18,
        roughness: 0.62,
        metalness: 0.04,
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
      const candidates = specs.map((sp) => {
        tmp.copy(sp.pos).addScaledVector(cutPlaneNormal, sp.lift);
        root.localToWorld(tmp);
        tmp.project(camera);
        return {
          id: sp.id,
          x: (tmp.x * 0.5 + 0.5) * cw + 14,
          y: (-tmp.y * 0.5 + 0.5) * ch - 10,
        };
      });
      separateLabelPositions(candidates, cw, ch, 26, 18, 18, 22);
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

      shadowOuterMat.opacity = 0.036 * state.solidReveal;
      shadowInnerMat.opacity = 0.058 * state.solidReveal;
      baseNodeMat.opacity = 0.9 * state.solidReveal;
      hiddenNodeMat.opacity = 0.45 * state.solidReveal;
      (saLowerLine.material as THREE.LineDashedMaterial).opacity = 0.56 * state.solidReveal;
      (saUpperLine.material as THREE.LineDashedMaterial).opacity = 0.48 * state.solidReveal;
      (rightAngle1.material as THREE.LineBasicMaterial).opacity = 0.58 * state.solidReveal;
      (rightAngle2.material as THREE.LineBasicMaterial).opacity = 0.58 * state.solidReveal;

      root.scale.setScalar(0.95 + 0.05 * state.solidReveal);
      lowerMat.opacity = 0.9 * state.solidReveal;
      upperMat.opacity = 0.24 * state.solidReveal;
      upperGroup.position.copy(cutPlaneNormal).multiplyScalar(state.capLift);

      for (const cyl of lowerSolidEdgeCyls) {
        (cyl.material as THREE.MeshBasicMaterial).opacity = 0.88 * state.solidReveal;
      }
      for (const hl of hiddenBaseLines) {
        (hl.material as THREE.LineDashedMaterial).opacity = 0.46 * state.solidReveal;
      }
      for (const ul of upperEdgeLines) {
        (ul.material as THREE.LineBasicMaterial).opacity = 0.66 * state.solidReveal;
      }

      seedMat.opacity = state.seedReveal;
      for (const d of seedDots) {
        d.visible = state.seedReveal > 0.05;
        d.scale.setScalar(Math.max(0.05, 1.06 * state.seedReveal));
      }

      planeMat.opacity = 0.18 * state.planeSweep;
      planeGroup.position
        .copy(planeCenter)
        .addScaledVector(cutPlaneNormal, (1 - state.planeSweep) * 0.65);
      for (const rim of planeRimCyls) {
        (rim.material as THREE.MeshBasicMaterial).opacity = 0.82 * state.planeSweep;
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

      root.rotation.y = 0.1 - state.orbitOffsetRad + curTiltX;
      root.rotation.x = 0.02 + curTiltY;

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
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
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
    target.scrollIntoView({ behavior: "smooth", block: "start" });
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
            Hình học không gian,
            <br />
            dễ <AnnotatedPhrase variant="circle">hình dung</AnnotatedPhrase> hơn.
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
