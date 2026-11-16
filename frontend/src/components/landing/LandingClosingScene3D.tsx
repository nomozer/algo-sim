import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from "react";
import * as THREE from "three";
import { computeBoundedPlaneQuad, type Vec3Tuple } from "./landing-geometry-data";

export const CLOSING_STORYBOARD_MS = 3400;
export const CLOSING_SECTION_FILL_OPACITY = 0.28;

export type ClosingStoryboardBeat =
  | "solids-emergence"
  | "plane-emergence"
  | "section-trace"
  | "composition-settled";

export interface ClosingMotionState {
  readonly progress: number;
  readonly beat: ClosingStoryboardBeat;
  readonly solidReveal: number;
  readonly planeSweep: number;
  readonly traceProgress: number;
  readonly sectionFillOpacity: number;
  readonly orbitOffsetRad: number;
  readonly settled: boolean;
  readonly reducedMotion: boolean;
}

export interface ClosingCompositionData {
  readonly prismBottom: readonly Vec3Tuple[];
  readonly prismTop: readonly Vec3Tuple[];
  readonly prismSection: readonly Vec3Tuple[];
  readonly prismPlaneNormal: Vec3Tuple;
  readonly prismPlaneQuad: readonly Vec3Tuple[];
  readonly prismPlanarResiduals: readonly number[];
  readonly coneBaseCenter: Vec3Tuple;
  readonly coneApex: Vec3Tuple;
  readonly coneRadius: number;
  readonly coneHeight: number;
  readonly coneSectionHeightY: number;
  readonly coneSectionRadius: number;
  readonly solidCenterGap: number;
}

interface TrackedDisposable {
  dispose(): void;
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

/**
 * Computes exact mathematical coordinates for the Closing CTA multi-solid composition:
 * - Upright regular hexagonal prism sliced obliquely (0.34*dx - 0.18*dz + 1.82)
 * - Right circular cone with horizontal circular section ring and vertical altitude
 */
export function buildClosingCompositionData(): ClosingCompositionData {
  const cx = -1.48;
  const cy = -1.68;
  const cz = 0.22;
  const hexRadius = 1.42;
  const hexHeight = 3.5;

  // Plane in prism-local frame: dy = 1.82 + 0.34*dx - 0.18*dz
  const slopeX = 0.34;
  const slopeZ = -0.18;
  const intercept = 1.82;
  const nLen = Math.hypot(-slopeX, 1, -slopeZ);
  const prismPlaneNormal: Vec3Tuple = [-slopeX / nLen, 1 / nLen, -slopeZ / nLen];

  const prismBottom: Vec3Tuple[] = [];
  const prismTop: Vec3Tuple[] = [];
  const prismSection: Vec3Tuple[] = [];

  for (let k = 0; k < 6; k++) {
    const theta = Math.PI / 6 + (k * Math.PI) / 3 + 0.14;
    const dx = hexRadius * Math.cos(theta);
    const dz = hexRadius * Math.sin(theta);
    const dySection = intercept + slopeX * dx + slopeZ * dz;
    prismBottom.push([cx + dx, cy, cz + dz]);
    prismTop.push([cx + dx, cy + hexHeight, cz + dz]);
    prismSection.push([cx + dx, cy + dySection, cz + dz]);
  }

  const p0 = prismSection[0];
  const prismPlanarResiduals = prismSection.map((pt) => {
    const dx = pt[0] - p0[0];
    const dy = pt[1] - p0[1];
    const dz = pt[2] - p0[2];
    return Math.abs(
      dx * prismPlaneNormal[0] + dy * prismPlaneNormal[1] + dz * prismPlaneNormal[2],
    );
  });

  const prismPlaneQuad = computeBoundedPlaneQuad(prismSection, prismPlaneNormal, 0.34);

  const coneBaseCenter: Vec3Tuple = [2.16, cy, -0.22];
  const coneRadius = 1.2;
  const coneHeight = 3.2;
  const coneApex: Vec3Tuple = [coneBaseCenter[0], cy + coneHeight, coneBaseCenter[2]];
  const coneSectionHeightY = cy + 1.38;
  const t = (coneSectionHeightY - cy) / coneHeight;
  const coneSectionRadius = coneRadius * (1 - t);

  const solidCenterGap = Math.hypot(
    coneBaseCenter[0] - cx,
    coneBaseCenter[2] - cz,
  );

  return {
    prismBottom,
    prismTop,
    prismSection,
    prismPlaneNormal,
    prismPlaneQuad,
    prismPlanarResiduals,
    coneBaseCenter,
    coneApex,
    coneRadius,
    coneHeight,
    coneSectionHeightY,
    coneSectionRadius,
    solidCenterGap,
  };
}

export function evaluateClosingStoryboard(
  elapsedMs: number,
  reducedMotion = false,
): ClosingMotionState {
  if (reducedMotion || elapsedMs >= CLOSING_STORYBOARD_MS) {
    return {
      progress: 1,
      beat: "composition-settled",
      solidReveal: 1,
      planeSweep: 1,
      traceProgress: 1,
      sectionFillOpacity: 1,
      orbitOffsetRad: 0,
      settled: true,
      reducedMotion,
    };
  }

  const p = clamp01(elapsedMs / CLOSING_STORYBOARD_MS);
  let beat: ClosingStoryboardBeat = "solids-emergence";
  if (p >= 0.74) beat = "composition-settled";
  else if (p >= 0.48) beat = "section-trace";
  else if (p >= 0.24) beat = "plane-emergence";

  const solidReveal = 0.35 + 0.65 * clampPhase(p, 0.0, 0.28);
  const planeSweep = clampPhase(p, 0.22, 0.54);
  const traceProgress = clampPhase(p, 0.46, 0.8);
  const sectionFillOpacity = clampPhase(p, 0.72, 0.98);
  const orbitOffsetRad = (1 - clampPhase(p, 0.0, 0.9)) * 0.1;

  return {
    progress: p,
    beat,
    solidReveal,
    planeSweep,
    traceProgress,
    sectionFillOpacity,
    orbitOffsetRad,
    settled: p >= 0.999,
    reducedMotion: false,
  };
}

function orientFaceOutward(
  pts: readonly THREE.Vector3[],
  centroid: THREE.Vector3,
): THREE.Vector3[] {
  if (pts.length < 3) return [...pts];
  const e1 = new THREE.Vector3().subVectors(pts[1], pts[0]);
  const e2 = new THREE.Vector3().subVectors(pts[2], pts[0]);
  const n = new THREE.Vector3().crossVectors(e1, e2);
  const inward = new THREE.Vector3().subVectors(centroid, pts[0]);
  return n.dot(inward) > 0 ? [...pts].reverse() : [...pts];
}

function buildFacesBufferGeometry(faces: readonly (readonly THREE.Vector3[])[]): THREE.BufferGeometry {
  const positions: number[] = [];
  for (const pts of faces) {
    if (pts.length < 3) continue;
    const p0 = pts[0];
    for (let i = 1; i < pts.length - 1; i++) {
      const p1 = pts[i];
      const p2 = pts[i + 1];
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
          dashSize: 0.13,
          gapSize: 0.09,
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

function ClosingFallbackSvg() {
  return (
    <svg
      className="axo-v14-closing-fallback-svg"
      viewBox="0 0 600 440"
      role="img"
      aria-label="Minh họa lăng trụ lục giác đều có thiết diện chéo và hình nón tròn xoay"
    >
      <ellipse className="axo-v14-svg-contact-halo" cx="204" cy="346" rx="116" ry="20" />
      <ellipse className="axo-v14-svg-contact-core" cx="204" cy="346" rx="80" ry="13" />
      <ellipse className="axo-v14-svg-contact-halo" cx="446" cy="346" rx="88" ry="18" />
      <ellipse className="axo-v14-svg-contact-core" cx="446" cy="346" rx="62" ry="12" />

      {/* Hexagonal prism */}
      <polygon
        className="axo-v14-svg-solid-lower"
        points="118,308 168,342 252,336 288,296 288,136 244,104 156,110 118,148"
      />
      <polygon
        className="axo-v14-svg-solid-upper"
        points="118,148 168,180 252,174 288,136 244,104 156,110"
      />

      <line className="axo-v14-svg-edge-hidden" x1="156" y1="270" x2="156" y2="110" />
      <line className="axo-v14-svg-edge-hidden" x1="244" y1="264" x2="244" y2="104" />
      <line className="axo-v14-svg-edge-hidden" x1="118" y1="308" x2="156" y2="270" />
      <line className="axo-v14-svg-edge-hidden" x1="156" y1="270" x2="244" y2="264" />
      <line className="axo-v14-svg-edge-hidden" x1="244" y1="264" x2="288" y2="296" />

      <line className="axo-v14-svg-edge-solid" x1="118" y1="148" x2="118" y2="308" />
      <line className="axo-v14-svg-edge-solid" x1="168" y1="180" x2="168" y2="342" />
      <line className="axo-v14-svg-edge-solid" x1="252" y1="174" x2="252" y2="336" />
      <line className="axo-v14-svg-edge-solid" x1="288" y1="136" x2="288" y2="296" />
      <line className="axo-v14-svg-edge-solid" x1="118" y1="308" x2="168" y2="342" />
      <line className="axo-v14-svg-edge-solid" x1="168" y1="342" x2="252" y2="336" />
      <line className="axo-v14-svg-edge-solid" x1="252" y1="336" x2="288" y2="296" />
      <polygon
        className="axo-v14-svg-edge-solid"
        fill="none"
        points="118,148 168,180 252,174 288,136 244,104 156,110"
      />

      {/* Oblique cutting plane & amber 6-gon section */}
      <polygon
        className="axo-v14-svg-cutting-plane"
        points="84,264 294,254 328,176 118,188"
      />
      <polygon
        className="axo-v14-svg-section-poly"
        points="118,242 168,262 252,240 288,200 244,186 156,204"
      />

      {/* Companion right circular cone */}
      <polygon
        className="axo-v14-svg-solid-upper"
        points="446,112 374,316 518,316"
      />
      <ellipse className="axo-v14-svg-solid-lower" cx="446" cy="316" rx="72" ry="22" />
      <line className="axo-v14-svg-edge-altitude" x1="446" y1="112" x2="446" y2="316" />
      <line className="axo-v14-svg-edge-hidden" x1="446" y1="316" x2="518" y2="316" />
      <line className="axo-v14-svg-edge-solid" x1="446" y1="112" x2="374" y2="316" />
      <line className="axo-v14-svg-edge-solid" x1="446" y1="112" x2="518" y2="316" />
      <path className="axo-v14-svg-edge-hidden" fill="none" d="M 374 316 A 72 22 0 0 1 518 316" />
      <path className="axo-v14-svg-edge-solid" fill="none" d="M 374 316 A 72 22 0 0 0 518 316" />
      <ellipse className="axo-v14-svg-section-poly" cx="446" cy="222" rx="39" ry="11" />
    </svg>
  );
}

export function LandingClosingScene3D() {
  const shellRef = useRef<HTMLDivElement | null>(null);
  const hostRef = useRef<HTMLDivElement | null>(null);
  const wakeRef = useRef<(() => void) | null>(null);
  const targetTiltRef = useRef({ x: 0, y: 0 });
  const [webglReady, setWebglReady] = useState(false);
  const [contextLost, setContextLost] = useState(false);
  const [beat, setBeat] = useState<ClosingStoryboardBeat>("solids-emergence");

  const composition = useMemo(() => buildClosingCompositionData(), []);

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
      return;
    }

    const tracked: TrackedDisposable[] = [];
    const track = <T extends TrackedDisposable>(item: T): T => {
      tracked.push(item);
      return item;
    };

    const width = Math.max(320, host.clientWidth || 560);
    const height = Math.max(260, host.clientHeight || 420);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height, false);
    renderer.setClearColor(0x000000, 0);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(31, width / height, 0.1, 100);
    camera.position.set(0.6, 4.35, 12.2);
    camera.lookAt(0.18, -0.05, 0);

    const ambientLight = new THREE.AmbientLight(0xfffdf9, 2.05);
    const keyLight = new THREE.DirectionalLight(0xfffaf0, 2.0);
    keyLight.position.set(8, 12, 9);
    const fillLight = new THREE.DirectionalLight(0xeef4fc, 1.0);
    fillLight.position.set(-7, 7, -6);
    scene.add(ambientLight, keyLight, fillLight);

    const root = new THREE.Group();
    scene.add(root);

    const botPts = composition.prismBottom.map((p) => new THREE.Vector3(...p));
    const topPts = composition.prismTop.map((p) => new THREE.Vector3(...p));
    const secPts = composition.prismSection.map((p) => new THREE.Vector3(...p));
    const planeNormal = new THREE.Vector3(...composition.prismPlaneNormal);
    const prismCentroid = [...botPts, ...topPts]
      .reduce((acc, p) => acc.add(p), new THREE.Vector3())
      .divideScalar(12);
    const prismBaseCenter = botPts
      .reduce((acc, p) => acc.add(p), new THREE.Vector3())
      .divideScalar(6);

    const coneBase = new THREE.Vector3(...composition.coneBaseCenter);
    const coneApex = new THREE.Vector3(...composition.coneApex);

    // 1. Subtle ground contact halos under each solid
    const prismHaloGeo = track(new THREE.CircleGeometry(1.92, 48));
    prismHaloGeo.rotateX(-Math.PI / 2);
    const prismHaloMat = track(
      new THREE.MeshBasicMaterial({
        color: 0x191918,
        transparent: true,
        opacity: 0.032,
        depthWrite: false,
      }),
    );
    const prismHalo = new THREE.Mesh(prismHaloGeo, prismHaloMat);
    prismHalo.position.set(prismBaseCenter.x, prismBaseCenter.y - 0.035, prismBaseCenter.z);
    prismHalo.renderOrder = 0;

    const coneHaloGeo = track(new THREE.CircleGeometry(1.56, 48));
    coneHaloGeo.rotateX(-Math.PI / 2);
    const coneHaloMat = track(
      new THREE.MeshBasicMaterial({
        color: 0x191918,
        transparent: true,
        opacity: 0.03,
        depthWrite: false,
      }),
    );
    const coneHalo = new THREE.Mesh(coneHaloGeo, coneHaloMat);
    coneHalo.position.set(coneBase.x, coneBase.y - 0.035, coneBase.z);
    coneHalo.renderOrder = 0;
    root.add(prismHalo, coneHalo);

    // 2. Primary Solid: Upright Regular Hexagonal Prism (translucent faces + dynamic front-solid / back-dashed edges)
    const prismFacesRaw: THREE.Vector3[][] = [
      orientFaceOutward([...botPts].reverse(), prismCentroid),
      orientFaceOutward([...topPts], prismCentroid),
    ];
    for (let k = 0; k < 6; k++) {
      const next = (k + 1) % 6;
      prismFacesRaw.push(
        orientFaceOutward([botPts[k], botPts[next], topPts[next], topPts[k]], prismCentroid),
      );
    }

    const prismFaceSpecs = prismFacesRaw.map((face) => {
      const e1 = new THREE.Vector3().subVectors(face[1], face[0]);
      const e2 = new THREE.Vector3().subVectors(face[2], face[0]);
      const normal = new THREE.Vector3().crossVectors(e1, e2).normalize();
      const center = face.reduce((a, b) => a.add(b), new THREE.Vector3()).divideScalar(face.length);
      return { normal, center };
    });

    const prismSolidMat = track(
      new THREE.MeshStandardMaterial({
        color: 0xf7f5f0,
        emissive: 0x38342e,
        emissiveIntensity: 0.2,
        roughness: 0.86,
        metalness: 0.02,
        flatShading: true,
        transparent: true,
        opacity: 0.24,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const prismGeo = track(buildFacesBufferGeometry(prismFacesRaw));
    const prismMesh = new THREE.Mesh(prismGeo, prismSolidMat);
    prismMesh.renderOrder = 2;
    root.add(prismMesh);

    const prismEdgeDefs: { a: THREE.Vector3; b: THREE.Vector3; faces: readonly [number, number] }[] = [];
    for (let k = 0; k < 6; k++) {
      const next = (k + 1) % 6;
      const sideFace = 2 + k;
      const prevSideFace = 2 + ((k + 5) % 6);
      prismEdgeDefs.push({ a: botPts[k], b: botPts[next], faces: [0, sideFace] });
      prismEdgeDefs.push({ a: topPts[k], b: topPts[next], faces: [1, sideFace] });
      prismEdgeDefs.push({ a: botPts[k], b: topPts[k], faces: [prevSideFace, sideFace] });
    }

    const prismEdgeBindings = prismEdgeDefs.map((ed) => {
      const solid = createCylinderEdge(ed.a, ed.b, 0.0155, 0x191918, 0.88, track);
      solid.renderOrder = 6;
      const dashed = createLineSegment(ed.a, ed.b, 0x615d59, 0.44, true, track);
      dashed.renderOrder = 2;
      root.add(solid, dashed);
      return { ...ed, solid, dashed };
    });

    // 3. Oblique Cutting Plane & 6-gon Amber Section on Hexagonal Prism
    const planeGroup = new THREE.Group();
    const planeQuadVecs = composition.prismPlaneQuad.map((p) => new THREE.Vector3(...p));
    const planeCenter = planeQuadVecs
      .reduce((acc, v) => acc.add(v), new THREE.Vector3())
      .divideScalar(planeQuadVecs.length);
    const localPlane = planeQuadVecs.map((v) => v.clone().sub(planeCenter));
    planeGroup.position.copy(planeCenter);

    const planeMat = track(
      new THREE.MeshBasicMaterial({
        color: 0x62aef0,
        transparent: true,
        opacity: 0.13,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const planeGeo = track(buildFacesBufferGeometry([localPlane]));
    const planeMesh = new THREE.Mesh(planeGeo, planeMat);
    planeMesh.renderOrder = 4;
    planeGroup.add(planeMesh);

    const planeRims: THREE.Mesh[] = [];
    for (let i = 0; i < localPlane.length; i++) {
      const rim = createCylinderEdge(
        localPlane[i],
        localPlane[(i + 1) % localPlane.length],
        0.013,
        0x0075de,
        0.78,
        track,
      );
      rim.renderOrder = 6;
      planeRims.push(rim);
      planeGroup.add(rim);
    }
    root.add(planeGroup);

    const secLoop = secPts.map((pt) => pt.clone().addScaledVector(planeNormal, 0.008));
    const secFillMat = track(
      new THREE.MeshStandardMaterial({
        color: 0xe6620a,
        emissive: 0x993d00,
        emissiveIntensity: 0.16,
        roughness: 0.65,
        metalness: 0.04,
        flatShading: true,
        transparent: true,
        opacity: CLOSING_SECTION_FILL_OPACITY,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const secGeo = track(buildFacesBufferGeometry([secLoop]));
    const secMesh = new THREE.Mesh(secGeo, secFillMat);
    secMesh.renderOrder = 5;
    root.add(secMesh);

    const secBorders: THREE.Mesh[] = [];
    for (let i = 0; i < secLoop.length; i++) {
      const seg = createCylinderEdge(
        secLoop[i],
        secLoop[(i + 1) % secLoop.length],
        0.022,
        0x793400,
        0.94,
        track,
        true,
      );
      seg.renderOrder = 7;
      secBorders.push(seg);
      root.add(seg);
    }

    const secNodeGeo = track(new THREE.SphereGeometry(0.042, 14, 14));
    const secNodeMat = track(
      new THREE.MeshBasicMaterial({ color: 0xdd5b00, transparent: true, opacity: 1 }),
    );
    const secNodes = secLoop.map((pt) => {
      const dot = new THREE.Mesh(secNodeGeo, secNodeMat);
      dot.position.copy(pt);
      dot.renderOrder = 8;
      root.add(dot);
      return dot;
    });

    // 4. Companion Right Circular Cone (spatially separated)
    const coneShellMat = track(
      new THREE.MeshStandardMaterial({
        color: 0xf7f5f0,
        emissive: 0x38342e,
        emissiveIntensity: 0.16,
        roughness: 0.84,
        metalness: 0.02,
        transparent: true,
        opacity: 0.18,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const coneGeo = track(
      new THREE.ConeGeometry(composition.coneRadius, composition.coneHeight, 48, 1, true),
    );
    const coneMesh = new THREE.Mesh(coneGeo, coneShellMat);
    coneMesh.position.set(
      coneBase.x,
      coneBase.y + composition.coneHeight * 0.5,
      coneBase.z,
    );
    coneMesh.renderOrder = 3;

    const coneBaseDiscGeo = track(new THREE.CircleGeometry(composition.coneRadius, 48));
    coneBaseDiscGeo.rotateX(-Math.PI / 2);
    const coneBaseDiscMat = track(
      new THREE.MeshBasicMaterial({
        color: 0xeeece6,
        transparent: true,
        opacity: 0.24,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const coneBaseDisc = new THREE.Mesh(coneBaseDiscGeo, coneBaseDiscMat);
    coneBaseDisc.position.copy(coneBase);
    coneBaseDisc.renderOrder = 2;

    const coneAltLine = createLineSegment(coneBase, coneApex, 0x0075de, 0.62, true, track);
    coneAltLine.renderOrder = 4;

    const coneRadiusEnd = new THREE.Vector3(
      coneBase.x + composition.coneRadius,
      coneBase.y,
      coneBase.z,
    );
    const coneRadiusLine = createLineSegment(coneBase, coneRadiusEnd, 0x615d59, 0.52, true, track);
    coneRadiusLine.renderOrder = 4;

    const coneRightAnglePts = [
      new THREE.Vector3(coneBase.x, coneBase.y + 0.22, coneBase.z),
      new THREE.Vector3(coneBase.x + 0.22, coneBase.y + 0.22, coneBase.z),
      new THREE.Vector3(coneBase.x + 0.22, coneBase.y, coneBase.z),
    ];
    const coneRightAngleGeo = track(new THREE.BufferGeometry().setFromPoints(coneRightAnglePts));
    const coneRightAngleMat = track(
      new THREE.LineBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.62 }),
    );
    const coneRightAngle = new THREE.Line(coneRightAngleGeo, coneRightAngleMat);
    coneRightAngle.renderOrder = 5;

    // Base front/back circle arcs
    const baseArcSegCount = 48;
    const coneBaseSegs: { a: THREE.Vector3; b: THREE.Vector3; mid: THREE.Vector3; solid: THREE.Mesh; dashed: THREE.Line }[] = [];
    for (let i = 0; i < baseArcSegCount; i++) {
      const a0 = (i / baseArcSegCount) * Math.PI * 2;
      const a1 = ((i + 1) / baseArcSegCount) * Math.PI * 2;
      const pA = new THREE.Vector3(
        coneBase.x + composition.coneRadius * Math.cos(a0),
        coneBase.y,
        coneBase.z + composition.coneRadius * Math.sin(a0),
      );
      const pB = new THREE.Vector3(
        coneBase.x + composition.coneRadius * Math.cos(a1),
        coneBase.y,
        coneBase.z + composition.coneRadius * Math.sin(a1),
      );
      const solid = createCylinderEdge(pA, pB, 0.015, 0x191918, 0.86, track);
      solid.renderOrder = 6;
      const dashed = createLineSegment(pA, pB, 0x615d59, 0.42, true, track);
      dashed.renderOrder = 3;
      root.add(solid, dashed);
      coneBaseSegs.push({
        a: pA,
        b: pB,
        mid: new THREE.Vector3().addVectors(pA, pB).multiplyScalar(0.5),
        solid,
        dashed,
      });
    }

    // Dynamic outer silhouette slant generators for cone (2 solid lines rotated cleanly around O-S axis)
    const slantMat = track(
      new THREE.MeshBasicMaterial({ color: 0x191918, transparent: true, opacity: 0.88 }),
    );
    const slantLeft = createCylinderEdge(coneApex, new THREE.Vector3(coneBase.x - composition.coneRadius, coneBase.y, coneBase.z), 0.0155, 0x191918, 0.88, track);
    slantLeft.material = slantMat;
    slantLeft.renderOrder = 6;
    const slantRight = createCylinderEdge(coneApex, new THREE.Vector3(coneBase.x + composition.coneRadius, coneBase.y, coneBase.z), 0.0155, 0x191918, 0.88, track);
    slantRight.material = slantMat;
    slantRight.renderOrder = 6;

    // Horizontal parallel section circle ring on cone
    const coneSecDiscGeo = track(new THREE.CircleGeometry(composition.coneSectionRadius, 48));
    coneSecDiscGeo.rotateX(-Math.PI / 2);
    const coneSecDiscMat = track(
      new THREE.MeshBasicMaterial({
        color: 0xe6620a,
        transparent: true,
        opacity: 0.2,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const coneSecDisc = new THREE.Mesh(coneSecDiscGeo, coneSecDiscMat);
    coneSecDisc.position.set(coneBase.x, composition.coneSectionHeightY, coneBase.z);
    coneSecDisc.renderOrder = 5;

    const coneSecRingPts: THREE.Vector3[] = [];
    for (let i = 0; i <= 64; i++) {
      const ang = (i / 64) * Math.PI * 2;
      coneSecRingPts.push(
        new THREE.Vector3(
          coneBase.x + composition.coneSectionRadius * Math.cos(ang),
          composition.coneSectionHeightY + 0.004,
          coneBase.z + composition.coneSectionRadius * Math.sin(ang),
        ),
      );
    }
    const coneSecRingGeo = track(new THREE.BufferGeometry().setFromPoints(coneSecRingPts));
    const coneSecRingMat = track(
      new THREE.LineBasicMaterial({ color: 0x793400, transparent: true, opacity: 0.92 }),
    );
    const coneSecRing = new THREE.Line(coneSecRingGeo, coneSecRingMat);
    coneSecRing.renderOrder = 7;

    const dotO = new THREE.Mesh(secNodeGeo, track(new THREE.MeshBasicMaterial({ color: 0x191918, transparent: true, opacity: 0.88 })));
    dotO.position.copy(coneBase);
    dotO.scale.setScalar(0.88);
    dotO.renderOrder = 8;

    const dotApex = new THREE.Mesh(secNodeGeo, track(new THREE.MeshBasicMaterial({ color: 0x191918, transparent: true, opacity: 0.92 })));
    dotApex.position.copy(coneApex);
    dotApex.renderOrder = 8;

    root.add(
      coneMesh,
      coneBaseDisc,
      coneAltLine,
      coneRadiusLine,
      coneRightAngle,
      slantLeft,
      slantRight,
      coneSecDisc,
      coneSecRing,
      dotO,
      dotApex,
    );

    const updateConeSilhouette = () => {
      const localCam = root.worldToLocal(camera.position.clone());
      const toCamXZ = new THREE.Vector2(localCam.x - coneBase.x, localCam.z - coneBase.z);
      const radialLen = Math.max(1e-4, toCamXZ.length());
      toCamXZ.divideScalar(radialLen);
      const tangentXZ = new THREE.Vector2(-toCamXZ.y, toCamXZ.x);

      const pL = new THREE.Vector3(
        coneBase.x + tangentXZ.x * composition.coneRadius,
        coneBase.y,
        coneBase.z + tangentXZ.y * composition.coneRadius,
      );
      const pR = new THREE.Vector3(
        coneBase.x - tangentXZ.x * composition.coneRadius,
        coneBase.y,
        coneBase.z - tangentXZ.y * composition.coneRadius,
      );

      for (const [mesh, targetPt] of [
        [slantLeft, pL],
        [slantRight, pR],
      ] as const) {
        const dir = new THREE.Vector3().subVectors(targetPt, coneApex);
        mesh.position.copy(coneApex).add(targetPt).multiplyScalar(0.5);
        mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize());
      }

      for (const seg of coneBaseSegs) {
        const outward = new THREE.Vector2(seg.mid.x - coneBase.x, seg.mid.z - coneBase.z);
        const isFront = outward.dot(toCamXZ) >= -0.04;
        seg.solid.visible = isFront;
        seg.dashed.visible = !isFront;
      }
    };

    let disposed = false;
    let isInView = true;
    let rafId = 0;
    const startMs = performance.now();
    let curTiltX = 0;
    let curTiltY = 0;
    let lastBeat: ClosingStoryboardBeat | null = null;

    const applyState = (nowMs: number): boolean => {
      const elapsed = nowMs - startMs;
      const state = evaluateClosingStoryboard(elapsed, reducedMotion);

      if (state.beat !== lastBeat) {
        lastBeat = state.beat;
        setBeat(state.beat);
      }

      const damp = reducedMotion ? 1 : 0.14;
      curTiltX += (targetTiltRef.current.x - curTiltX) * damp;
      curTiltY += (targetTiltRef.current.y - curTiltY) * damp;

      prismHaloMat.opacity = 0.032 * state.solidReveal;
      coneHaloMat.opacity = 0.03 * state.solidReveal;
      prismSolidMat.opacity = 0.24 * state.solidReveal;
      coneShellMat.opacity = 0.18 * state.solidReveal;
      coneBaseDiscMat.opacity = 0.24 * state.solidReveal;
      slantMat.opacity = 0.88 * state.solidReveal;
      (coneAltLine.material as THREE.LineDashedMaterial).opacity = 0.62 * state.solidReveal;
      (coneRadiusLine.material as THREE.LineDashedMaterial).opacity = 0.52 * state.solidReveal;
      coneRightAngleMat.opacity = 0.62 * state.solidReveal;
      (dotO.material as THREE.MeshBasicMaterial).opacity = 0.88 * state.solidReveal;
      (dotApex.material as THREE.MeshBasicMaterial).opacity = 0.92 * state.solidReveal;

      root.scale.setScalar(0.95 + 0.05 * state.solidReveal);
      root.rotation.y = -state.orbitOffsetRad + curTiltX;
      root.rotation.x = 0.015 + curTiltY;
      root.updateMatrixWorld(true);

      const tmpNormal = new THREE.Vector3();
      const tmpCenter = new THREE.Vector3();
      const tmpToCam = new THREE.Vector3();
      const frontFacing = prismFaceSpecs.map((fs) => {
        tmpNormal.copy(fs.normal).transformDirection(root.matrixWorld);
        tmpCenter.copy(fs.center).applyMatrix4(root.matrixWorld);
        tmpToCam.copy(camera.position).sub(tmpCenter);
        return tmpNormal.dot(tmpToCam) > 0;
      });
      for (const edge of prismEdgeBindings) {
        const isFrontEdge = frontFacing[edge.faces[0]] || frontFacing[edge.faces[1]];
        edge.solid.visible = isFrontEdge;
        edge.dashed.visible = !isFrontEdge;
        if (isFrontEdge) {
          (edge.solid.material as THREE.MeshBasicMaterial).opacity = 0.88 * state.solidReveal;
        } else {
          (edge.dashed.material as THREE.LineDashedMaterial).opacity = 0.44 * state.solidReveal;
        }
      }

      updateConeSilhouette();

      planeMat.opacity = 0.13 * state.planeSweep;
      planeGroup.position
        .copy(planeCenter)
        .addScaledVector(planeNormal, (1 - state.planeSweep) * 0.48);
      for (const rim of planeRims) {
        (rim.material as THREE.MeshBasicMaterial).opacity = 0.78 * state.planeSweep;
      }

      secNodeMat.opacity = state.planeSweep;
      for (const dot of secNodes) {
        dot.visible = state.planeSweep > 0.25;
        dot.scale.setScalar(Math.max(0.05, state.planeSweep));
      }

      for (let i = 0; i < secBorders.length; i++) {
        const seg = secBorders[i];
        const edgeStart = i / secBorders.length;
        const edgeEnd = (i + 1) / secBorders.length;
        const localP = clamp01((state.traceProgress - edgeStart) / (edgeEnd - edgeStart));
        seg.visible = localP > 0.01;
        seg.scale.set(1, Math.max(0.01, localP), 1);
        (seg.material as THREE.MeshBasicMaterial).opacity = 0.94 * Math.min(1, localP * 2);
      }

      secFillMat.opacity = CLOSING_SECTION_FILL_OPACITY * state.sectionFillOpacity;
      secMesh.visible = state.sectionFillOpacity > 0.01;
      coneSecDiscMat.opacity = 0.2 * state.sectionFillOpacity;
      coneSecDisc.visible = state.sectionFillOpacity > 0.01;
      coneSecRingMat.opacity = 0.92 * state.traceProgress;
      coneSecRing.visible = state.traceProgress > 0.05;

      renderer.render(scene, camera);

      const tiltDone =
        Math.abs(targetTiltRef.current.x - curTiltX) < 0.0008 &&
        Math.abs(targetTiltRef.current.y - curTiltY) < 0.0008;
      return state.settled && tiltDone;
    };

    const scheduleFrame = () => {
      if (disposed || rafId !== 0 || !isInView || document.hidden) return;
      rafId = window.requestAnimationFrame((now) => {
        rafId = 0;
        if (disposed || !isInView || document.hidden) return;
        const idle = applyState(now);
        if (!idle) scheduleFrame();
      });
    };

    wakeRef.current = () => {
      if (disposed) return;
      if (reducedMotion) {
        applyState(performance.now());
        return;
      }
      scheduleFrame();
    };

    const handleResize = () => {
      if (disposed || !host) return;
      const nextW = Math.max(320, host.clientWidth || 560);
      const nextH = Math.max(260, host.clientHeight || 420);
      camera.aspect = nextW / nextH;
      camera.updateProjectionMatrix();
      renderer.setSize(nextW, nextH, false);
      applyState(performance.now());
    };

    const onMotionChange = (e: MediaQueryListEvent) => {
      reducedMotion = e.matches;
      applyState(performance.now());
      if (!e.matches) scheduleFrame();
    };

    const onVisibilityChange = () => {
      if (document.hidden) {
        if (rafId !== 0) {
          window.cancelAnimationFrame(rafId);
          rafId = 0;
        }
      } else {
        applyState(performance.now());
        scheduleFrame();
      }
    };

    const handleContextLost = (e: Event) => {
      e.preventDefault();
      setContextLost(true);
      if (rafId !== 0) {
        window.cancelAnimationFrame(rafId);
        rafId = 0;
      }
    };
    const handleContextRestored = () => {
      setContextLost(false);
      applyState(performance.now());
      scheduleFrame();
    };

    let io: IntersectionObserver | null = null;
    if (typeof IntersectionObserver !== "undefined") {
      io = new IntersectionObserver(
        (entries) => {
          const entry = entries[0];
          isInView = Boolean(entry?.isIntersecting);
          if (isInView && !document.hidden) {
            const idle = applyState(performance.now());
            if (!idle) scheduleFrame();
          } else if (rafId !== 0) {
            window.cancelAnimationFrame(rafId);
            rafId = 0;
          }
        },
        { threshold: 0.08 },
      );
      io.observe(host);
    }

    host.appendChild(canvas);
    setWebglReady(true);
    const initialIdle = applyState(performance.now());
    if (!initialIdle && isInView && !document.hidden) {
      scheduleFrame();
    }

    let ro: ResizeObserver | null = null;
    if (typeof ResizeObserver !== "undefined") {
      ro = new ResizeObserver(handleResize);
      ro.observe(host);
    }
    window.addEventListener("resize", handleResize);
    reducedQuery?.addEventListener?.("change", onMotionChange);
    document.addEventListener("visibilitychange", onVisibilityChange);
    canvas.addEventListener("webglcontextlost", handleContextLost);
    canvas.addEventListener("webglcontextrestored", handleContextRestored);

    return () => {
      disposed = true;
      wakeRef.current = null;
      if (rafId !== 0) window.cancelAnimationFrame(rafId);
      io?.disconnect();
      ro?.disconnect();
      window.removeEventListener("resize", handleResize);
      reducedQuery?.removeEventListener?.("change", onMotionChange);
      document.removeEventListener("visibilitychange", onVisibilityChange);
      canvas.removeEventListener("webglcontextlost", handleContextLost);
      canvas.removeEventListener("webglcontextrestored", handleContextRestored);
      for (const item of tracked) {
        item.dispose();
      }
      renderer.dispose();
      canvas.remove();
    };
  }, [composition, webglAllowed]);

  const handlePointerMove = (e: ReactPointerEvent<HTMLDivElement>) => {
    const shell = shellRef.current;
    if (!shell) return;
    const rect = shell.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return;
    const nx = (e.clientX - rect.left) / rect.width - 0.5;
    const ny = (e.clientY - rect.top) / rect.height - 0.5;
    targetTiltRef.current = { x: nx * 0.14, y: -ny * 0.08 };
    wakeRef.current?.();
  };

  const handlePointerLeave = () => {
    targetTiltRef.current = { x: 0, y: 0 };
    wakeRef.current?.();
  };

  return (
    <div
      id="landing-closing-scene3d"
      ref={shellRef}
      className="axo-v14-closing-visual"
      data-cta-visual="spatial-multi-solid-3d"
      data-closing-beat={beat}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
    >
      <div
        ref={hostRef}
        className={
          webglAllowed && webglReady && !contextLost
            ? "axo-v14-closing-canvas-host"
            : "axo-v14-closing-canvas-host is-hidden"
        }
      />

      {(!webglAllowed || !webglReady || contextLost) && <ClosingFallbackSvg />}
    </div>
  );
}
