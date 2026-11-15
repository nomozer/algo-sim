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

interface ClippedPolygonFace {
  readonly pts: THREE.Vector3[];
}

interface TrackedDisposable {
  dispose(): void;
}

const ANIMATION_DURATION_MS = 1420;
const KEY_LIGHT_DIR = new THREE.Vector3(6.5, 10.5, 4.5).normalize();
const RIM_LIGHT_DIR = new THREE.Vector3(-7.0, 3.8, 5.0).normalize();

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

function computeStudioShade(normal: THREE.Vector3): number {
  const key = Math.max(0, normal.dot(KEY_LIGHT_DIR)) * 0.2;
  const rim = Math.max(0, normal.dot(RIM_LIGHT_DIR)) * 0.08;
  return Math.min(1.04, 0.78 + key + rim);
}

function buildShadedFacesGeometry(
  faces: readonly ClippedPolygonFace[],
  baseColorHex: number,
  shadeFaces: boolean,
): THREE.BufferGeometry {
  const positions: number[] = [];
  const colors: number[] = [];
  const baseColor = new THREE.Color(baseColorHex);
  const e1 = new THREE.Vector3();
  const e2 = new THREE.Vector3();
  const triNormal = new THREE.Vector3();

  for (const face of faces) {
    if (face.pts.length < 3) continue;
    const p0 = face.pts[0];
    for (let i = 1; i < face.pts.length - 1; i++) {
      const p1 = face.pts[i];
      const p2 = face.pts[i + 1];
      e1.subVectors(p1, p0);
      e2.subVectors(p2, p0);
      triNormal.crossVectors(e1, e2).normalize();
      const shade = shadeFaces ? computeStudioShade(triNormal) : 1;
      const r = Math.min(1, baseColor.r * shade);
      const g = Math.min(1, baseColor.g * shade);
      const b = Math.min(1, baseColor.b * shade);
      positions.push(p0.x, p0.y, p0.z, p1.x, p1.y, p1.z, p2.x, p2.y, p2.z);
      colors.push(r, g, b, r, g, b, r, g, b);
    }
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
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

function clampPhase(value: number, start: number, end: number): number {
  if (value <= start) return 0;
  if (value >= end) return 1;
  const u = (value - start) / (end - start);
  return 1 - Math.pow(1 - u, 3);
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
        cx="265"
        cy="364"
        rx="148"
        ry="26"
      />
      <ellipse
        className="axo-v14-svg-contact-core"
        cx="265"
        cy="364"
        rx="106"
        ry="18"
      />

      <polygon
        className="axo-v14-svg-solid-base"
        points="148,342 352,366 424,296 216,282"
      />
      <polygon
        className="axo-v14-svg-solid-lower"
        points="148,342 352,366 424,296 336,204 272,190 188,236"
      />
      <polygon
        className="axo-v14-svg-solid-upper"
        points="216,90 188,236 272,190 336,204"
      />

      <line
        className="axo-v14-svg-edge-hidden"
        x1="216"
        y1="282"
        x2="148"
        y2="342"
      />
      <line
        className="axo-v14-svg-edge-hidden"
        x1="216"
        y1="282"
        x2="424"
        y2="296"
      />
      <line
        className="axo-v14-svg-edge-altitude"
        x1="216"
        y1="90"
        x2="216"
        y2="282"
      />

      <line
        className="axo-v14-svg-edge-solid"
        x1="216"
        y1="90"
        x2="148"
        y2="342"
      />
      <line
        className="axo-v14-svg-edge-solid"
        x1="216"
        y1="90"
        x2="352"
        y2="366"
      />
      <line
        className="axo-v14-svg-edge-solid"
        x1="216"
        y1="90"
        x2="424"
        y2="296"
      />
      <line
        className="axo-v14-svg-edge-solid"
        x1="148"
        y1="342"
        x2="352"
        y2="366"
      />
      <line
        className="axo-v14-svg-edge-solid"
        x1="352"
        y1="366"
        x2="424"
        y2="296"
      />

      <polygon
        className="axo-v14-svg-cutting-plane"
        points="106,256 372,294 436,192 174,168"
      />
      <polygon
        className="axo-v14-svg-section-poly"
        points="186,238 246,282 314,274 338,208 268,194"
      />

      <line
        className="axo-v14-svg-projection-ray"
        x1="268"
        y1="194"
        x2="412"
        y2="118"
      />
      <line
        className="axo-v14-svg-projection-ray"
        x1="338"
        y1="208"
        x2="430"
        y2="162"
      />
    </svg>
  );
}

function HeroSpatialStage({
  trueShape,
}: {
  readonly trueShape: TrueShapeProjectionResult;
}) {
  const shellRef = useRef<HTMLDivElement | null>(null);
  const hostRef = useRef<HTMLDivElement | null>(null);
  const wakeRef = useRef<(() => void) | null>(null);
  const targetTiltRef = useRef({ x: 0, y: 0 });
  const [webglReady, setWebglReady] = useState(false);
  const [contextLost, setContextLost] = useState(false);
  const [isSettled, setIsSettled] = useState(false);

  const webglAllowed = useMemo(() => {
    if (typeof window === "undefined") return false;
    return !window.location.search.includes("no_webgl=1");
  }, []);

  useEffect(() => {
    const reducedMotion =
      typeof window !== "undefined" &&
      Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches);

    if (reducedMotion) {
      setIsSettled(true);
    }

    const host = hostRef.current;
    if (!host || !webglAllowed) return;

    const canvas = document.createElement("canvas");
    const gl =
      canvas.getContext("webgl2", {
        alpha: true,
        antialias: true,
        powerPreference: "high-performance",
      }) ||
      canvas.getContext("webgl", {
        alpha: true,
        antialias: true,
        powerPreference: "high-performance",
      });

    if (!gl) {
      setWebglReady(false);
      return;
    }

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
    camera.lookAt(lookX, lookY, lookZ);

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

    // Group 1: Ground contact shadow, altitude witness SA perp (ABCD), base vertices
    const baseGuideGroup = new THREE.Group();
    const shadowOuterGeo = track(new THREE.CircleGeometry(2.45, 48));
    shadowOuterGeo.rotateX(-Math.PI / 2);
    const shadowOuterMat = track(
      new THREE.MeshBasicMaterial({
        color: 0x191918,
        transparent: true,
        opacity: 0.032,
        depthWrite: false,
      }),
    );
    const shadowOuterMesh = new THREE.Mesh(shadowOuterGeo, shadowOuterMat);
    shadowOuterMesh.position.set(baseCenter.x, A.y - 0.035, baseCenter.z);
    shadowOuterMesh.renderOrder = 0;
    baseGuideGroup.add(shadowOuterMesh);

    const shadowInnerGeo = track(new THREE.CircleGeometry(1.72, 40));
    shadowInnerGeo.rotateX(-Math.PI / 2);
    const shadowInnerMat = track(
      new THREE.MeshBasicMaterial({
        color: 0x191918,
        transparent: true,
        opacity: 0.055,
        depthWrite: false,
      }),
    );
    const shadowInnerMesh = new THREE.Mesh(shadowInnerGeo, shadowInnerMat);
    shadowInnerMesh.position.set(baseCenter.x, A.y - 0.03, baseCenter.z);
    shadowInnerMesh.renderOrder = 1;
    baseGuideGroup.add(shadowInnerMesh);

    const saGuideLine = createLineSegment(S, A, 0x0075de, 0.54, true, track);
    baseGuideGroup.add(saGuideLine);

    // Right-angle marker at foot A along SA and AB/AD
    const uAB = new THREE.Vector3().subVectors(B, A).normalize().multiplyScalar(0.24);
    const uAS = new THREE.Vector3().subVectors(S, A).normalize().multiplyScalar(0.24);
    const footCorner = A.clone().add(uAB).add(uAS);
    const rightAngle1 = createLineSegment(
      A.clone().add(uAS),
      footCorner,
      0x0075de,
      0.56,
      false,
      track,
    );
    const rightAngle2 = createLineSegment(
      A.clone().add(uAB),
      footCorner,
      0x0075de,
      0.56,
      false,
      track,
    );
    baseGuideGroup.add(rightAngle1, rightAngle2);

    const nodeGeo = track(new THREE.SphereGeometry(0.056, 16, 16));
    const darkNodeMat = track(
      new THREE.MeshBasicMaterial({
        color: 0x191918,
        transparent: true,
        opacity: 0.9,
      }),
    );
    for (const pt of [S, A, B, C, D]) {
      const dot = new THREE.Mesh(nodeGeo, darkNodeMat);
      dot.position.copy(pt);
      baseGuideGroup.add(dot);
    }
    root.add(baseGuideGroup);

    // Group 2: Split pyramid volume (lower solid + upper translucent frustum)
    const solidGroup = new THREE.Group();
    const lowerGeo = track(buildShadedFacesGeometry(lowerFaces, 0xf4f3f0, true));
    const lowerMat = track(
      new THREE.MeshBasicMaterial({
        vertexColors: true,
        transparent: true,
        opacity: 0.94,
        side: THREE.DoubleSide,
      }),
    );
    const lowerMesh = new THREE.Mesh(lowerGeo, lowerMat);
    lowerMesh.renderOrder = 2;
    solidGroup.add(lowerMesh);

    const upperGeo = track(buildShadedFacesGeometry(upperFaces, 0xfbfaf8, true));
    const upperMat = track(
      new THREE.MeshBasicMaterial({
        vertexColors: true,
        transparent: true,
        opacity: 0.3,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const upperMesh = new THREE.Mesh(upperGeo, upperMat);
    upperMesh.renderOrder = 2;
    solidGroup.add(upperMesh);

    const visibleEdges: readonly [THREE.Vector3, THREE.Vector3][] = [
      [S, B],
      [S, C],
      [S, D],
      [B, C],
      [C, D],
    ];
    const hiddenEdges: readonly [THREE.Vector3, THREE.Vector3][] = [
      [A, B],
      [A, D],
    ];
    const solidLines: THREE.Line[] = [];
    for (const [u, v] of visibleEdges) {
      const edge = createLineSegment(u, v, 0x191918, 0.78, false, track);
      solidLines.push(edge);
      solidGroup.add(edge);
    }
    for (const [u, v] of hiddenEdges) {
      const edge = createLineSegment(u, v, 0x615d59, 0.44, true, track);
      solidLines.push(edge);
      solidGroup.add(edge);
    }
    root.add(solidGroup);

    // Group 3: Cutting plane (MNP)
    const planeGroup = new THREE.Group();
    const planeQuadVecs = LANDING_PYRAMID_SAMPLE.planeQuad.map(
      (pt) => new THREE.Vector3(pt[0], pt[1], pt[2]),
    );
    const planeCenter = planeQuadVecs
      .reduce((acc, v) => acc.add(v), new THREE.Vector3())
      .divideScalar(Math.max(1, planeQuadVecs.length));
    const localPlane = planeQuadVecs.map((v) => v.clone().sub(planeCenter));
    planeGroup.position.copy(planeCenter);

    const planeGeo = track(
      buildShadedFacesGeometry([{ pts: localPlane }], 0xdcebfa, false),
    );
    const planeMat = track(
      new THREE.MeshBasicMaterial({
        vertexColors: true,
        transparent: true,
        opacity: 0.32,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const planeMesh = new THREE.Mesh(planeGeo, planeMat);
    planeMesh.renderOrder = 3;
    planeGroup.add(planeMesh);

    const planeRimLines: THREE.Line[] = [];
    for (let i = 0; i < localPlane.length; i++) {
      const rim = createLineSegment(
        localPlane[i],
        localPlane[(i + 1) % localPlane.length],
        0x0075de,
        0.84,
        false,
        track,
      );
      planeRimLines.push(rim);
      planeGroup.add(rim);
    }
    root.add(planeGroup);

    // Group 4: Pentagon cross-section MENPF
    const sectionGroup = new THREE.Group();
    const sectionOffsetLoop = loopPts.map((pt) =>
      pt.clone().addScaledVector(cutPlaneNormal, 0.006),
    );
    const secGeo = track(
      buildShadedFacesGeometry([{ pts: sectionOffsetLoop }], 0xdd5b00, false),
    );
    const secMat = track(
      new THREE.MeshBasicMaterial({
        vertexColors: true,
        transparent: true,
        opacity: 0.9,
        side: THREE.DoubleSide,
      }),
    );
    const secMesh = new THREE.Mesh(secGeo, secMat);
    secMesh.renderOrder = 4;
    sectionGroup.add(secMesh);

    const orangeNodeMat = track(
      new THREE.MeshBasicMaterial({
        color: 0xdd5b00,
        transparent: true,
        opacity: 1,
      }),
    );
    const secBorderLines: THREE.Line[] = [];
    for (let i = 0; i < sectionOffsetLoop.length; i++) {
      const a = sectionOffsetLoop[i];
      const b = sectionOffsetLoop[(i + 1) % sectionOffsetLoop.length];
      const border = createLineSegment(a, b, 0x793400, 0.96, false, track);
      border.renderOrder = 5;
      secBorderLines.push(border);
      sectionGroup.add(border);

      const dot = new THREE.Mesh(nodeGeo, orangeNodeMat);
      dot.position.copy(a);
      dot.scale.setScalar(0.84);
      dot.renderOrder = 5;
      sectionGroup.add(dot);
    }
    root.add(sectionGroup);

    let disposed = false;
    let isInView = true;
    let rafId = 0;
    let settledTriggered = reducedMotion;
    const startMs = performance.now();
    let curTiltX = 0;
    let curTiltY = 0;

    const applyState = (nowMs: number): boolean => {
      const rawProgress = reducedMotion
        ? 1
        : Math.min(1, Math.max(0, (nowMs - startMs) / ANIMATION_DURATION_MS));

      const pBase = reducedMotion ? 1 : clampPhase(rawProgress, 0.0, 0.24);
      const pSolid = reducedMotion ? 1 : clampPhase(rawProgress, 0.14, 0.48);
      const pPlane = reducedMotion ? 1 : clampPhase(rawProgress, 0.36, 0.68);
      const pSection = reducedMotion ? 1 : clampPhase(rawProgress, 0.56, 0.84);
      const pSettled = reducedMotion ? 1 : clampPhase(rawProgress, 0.74, 1.0);

      if (!settledTriggered && pSettled > 0.35) {
        settledTriggered = true;
        setIsSettled(true);
      }

      const damp = reducedMotion ? 1 : 0.14;
      curTiltX += (targetTiltRef.current.x - curTiltX) * damp;
      curTiltY += (targetTiltRef.current.y - curTiltY) * damp;

      shadowOuterMat.opacity = 0.032 * pBase;
      shadowInnerMat.opacity = 0.055 * pBase;
      darkNodeMat.opacity = 0.9 * pBase;
      (saGuideLine.material as THREE.LineDashedMaterial).opacity = 0.54 * pBase;
      (rightAngle1.material as THREE.LineBasicMaterial).opacity = 0.56 * pBase;
      (rightAngle2.material as THREE.LineBasicMaterial).opacity = 0.56 * pBase;

      solidGroup.scale.setScalar(0.94 + 0.06 * pSolid);
      lowerMat.opacity = 0.94 * pSolid;
      upperMat.opacity = 0.3 * pSolid;
      for (const line of solidLines) {
        (line.material as THREE.Material & { opacity: number }).opacity =
          (line.material instanceof THREE.LineDashedMaterial ? 0.44 : 0.78) * pSolid;
      }

      planeMat.opacity = 0.32 * pPlane;
      planeGroup.position
        .copy(planeCenter)
        .addScaledVector(cutPlaneNormal, (1 - pPlane) * 0.58);
      for (const rim of planeRimLines) {
        (rim.material as THREE.LineBasicMaterial).opacity = 0.84 * pPlane;
      }

      secMat.opacity = 0.9 * pSection;
      orangeNodeMat.opacity = pSection;
      for (const border of secBorderLines) {
        (border.material as THREE.LineBasicMaterial).opacity = 0.96 * pSection;
      }

      const orbitOffset = (1 - pSolid) * 0.18;
      root.rotation.y = 0.12 + curTiltX - orbitOffset;
      root.rotation.x = 0.02 + curTiltY;

      renderer.render(scene, camera);

      const timelineDone = rawProgress >= 0.999;
      const tiltDone =
        Math.abs(targetTiltRef.current.x - curTiltX) < 0.0008 &&
        Math.abs(targetTiltRef.current.y - curTiltY) < 0.0008;
      return timelineDone && tiltDone;
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
              if (isInView) wake();
            },
            { threshold: 0.06 },
          )
        : null;
    if (shellRef.current) io?.observe(shellRef.current);

    const onVisibility = () => {
      if (!document.hidden && isInView) wake();
    };
    document.addEventListener("visibilitychange", onVisibility);

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

    wake();

    return () => {
      disposed = true;
      wakeRef.current = null;
      if (rafId) {
        window.cancelAnimationFrame(rafId);
      }
      ro?.disconnect();
      io?.disconnect();
      document.removeEventListener("visibilitychange", onVisibility);
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

  const insetW = 160;
  const insetH = 126;
  const polyPoints = trueShape.vertices
    .map((v) => `${(v.nx * insetW).toFixed(1)},${(v.ny * insetH).toFixed(1)}`)
    .join(" ");

  return (
    <div
      id="landing-hero-sculpture"
      ref={shellRef}
      className="axo-v14-hero-visual"
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
      aria-label="Minh họa khối chóp S.ABCD và thiết diện thật MENPF"
    >
      <div
        ref={hostRef}
        className={
          webglAllowed && webglReady && !contextLost
            ? "axo-v14-hero-canvas-host"
            : "axo-v14-hero-canvas-host is-hidden"
        }
      />

      {(!webglAllowed || !webglReady || contextLost) && <HeroFallbackSvg />}

      <aside
        className={
          isSettled
            ? "axo-v14-hero-trueshape is-settled"
            : "axo-v14-hero-trueshape"
        }
        aria-label="Hình chiếu trực giao thiết diện MENPF"
      >
        <div className="axo-v14-trueshape-head">
          <span className="axo-v14-trueshape-caption">Thiết diện thật (MNP)</span>
          <span className="axo-v14-trueshape-formula">S(MENPF) = 6√6</span>
        </div>
        <svg
          className="axo-v14-trueshape-svg"
          viewBox={`0 0 ${insetW} ${insetH}`}
          aria-hidden="true"
          focusable="false"
        >
          <line
            className="axo-v14-svg-projection-ray"
            x1="10"
            y1="108"
            x2={(trueShape.vertices[0]?.nx ?? 0.3) * insetW}
            y2={(trueShape.vertices[0]?.ny ?? 0.5) * insetH}
          />
          <polygon
            className="axo-v14-svg-trueshape-poly"
            points={polyPoints}
          />
          {trueShape.vertices.map((v) => {
            const cx = v.nx * insetW;
            const cy = v.ny * insetH;
            const dx = v.nx < 0.5 ? -10 : 8;
            const dy = v.ny < 0.48 ? -7 : 12;
            return (
              <g key={v.id}>
                <circle
                  className="axo-v14-svg-section-dot"
                  cx={cx}
                  cy={cy}
                  r="3.2"
                />
                <text
                  className="axo-v14-svg-vertex-text"
                  x={cx + dx}
                  y={cy + dy}
                >
                  {v.label}
                </text>
              </g>
            );
          })}
        </svg>
      </aside>
    </div>
  );
}

export function LandingHeroV14() {
  const user = useAuthStore((s) => s.user);
  const trueShape = useMemo(() => computeTrueShapeSection2D(), []);

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
            Nhập đề bài tiếng Việt để quan sát mô hình 3D chính xác, thiết diện
            cắt và chuỗi lập luận dựng hình trên cùng một không gian trực quan.
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

        <HeroSpatialStage trueShape={trueShape} />
      </div>
    </section>
  );
}
