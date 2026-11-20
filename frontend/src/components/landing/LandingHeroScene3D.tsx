import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import {
  LANDING_PYRAMID_SAMPLE,
  type LandingPointSpec,
  type LandingSampleSpec,
  type Vec3Tuple,
} from "./landing-geometry-data";

export interface SpatialSceneCanvasProps {
  readonly sample?: LandingSampleSpec;
  readonly visiblePoints?: readonly string[];
  readonly activePoints?: readonly string[];
  readonly showGuideEdges?: boolean;
  readonly planeOpacity?: number;
  readonly sectionProgress?: number;
  readonly sectionFillOpacity?: number;
  readonly cameraPos?: Vec3Tuple;
  readonly lookAt?: Vec3Tuple;
  readonly interactiveOrbit?: boolean;
  readonly orbitResetNonce?: number;
  readonly subtlePointerParallax?: boolean;
  readonly compact?: boolean;
  readonly frameless?: boolean;
  readonly pointTagFilter?: readonly string[];
  readonly topBadgeLeft?: string;
  readonly topBadgeRight?: string;
  readonly bottomCaption?: string;
  readonly bottomHint?: string;
  readonly sceneId?: string;
  readonly ariaLabel?: string;
  readonly presentation?: "default" | "v14";
  readonly onUserOrbit?: () => void;
}

interface ProjectedPoint2D {
  readonly id: string;
  readonly label: string;
  readonly role: LandingPointSpec["role"];
  readonly x: number;
  readonly y: number;
  readonly depth: number;
}

export interface LabelCandidate {
  id: string;
  x: number;
  y: number;
}

export function separateLabelPositions(
  items: LabelCandidate[],
  width: number,
  height: number,
  minDist = 26,
  padX = 24,
  padTop = 26,
  padBottom = 46,
): void {
  const maxX = Math.max(padX + 1, width - padX);
  const maxY = Math.max(padTop + 1, height - padBottom);
  const clampAll = () => {
    for (const item of items) {
      item.x = Math.max(padX, Math.min(maxX, item.x));
      item.y = Math.max(padTop, Math.min(maxY, item.y));
    }
  };

  clampAll();
  for (let pass = 0; pass < 2; pass++) {
    for (let i = 0; i < items.length; i++) {
      for (let j = i + 1; j < items.length; j++) {
        const a = items[i];
        const b = items[j];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.hypot(dx, dy);
        if (dist < minDist) {
          const nx = dist > 1e-3 ? dx / dist : 0;
          const ny = dist > 1e-3 ? dy / dist : -1;
          const push = (minDist - dist) * 0.52;
          a.x -= nx * push;
          a.y -= ny * push;
          b.x += nx * push;
          b.y += ny * push;
        }
      }
    }
    clampAll();
  }
}

function projectToSvgViewport(
  point: Vec3Tuple,
  cameraPos: Vec3Tuple,
  lookAt: Vec3Tuple,
  width: number,
  height: number,
  fovDeg = 35,
): { x: number; y: number; depth: number } {
  const fx = lookAt[0] - cameraPos[0];
  const fy = lookAt[1] - cameraPos[1];
  const fz = lookAt[2] - cameraPos[2];
  const fLen = Math.hypot(fx, fy, fz) || 1;
  const f = [fx / fLen, fy / fLen, fz / fLen];

  const worldUp = [0, 1, 0];
  let rx = f[1] * worldUp[2] - f[2] * worldUp[1];
  let ry = f[2] * worldUp[0] - f[0] * worldUp[2];
  let rz = f[0] * worldUp[1] - f[1] * worldUp[0];
  const rLen = Math.hypot(rx, ry, rz) || 1;
  rx /= rLen;
  ry /= rLen;
  rz /= rLen;

  const ux = ry * f[2] - rz * f[1];
  const uy = rz * f[0] - rx * f[2];
  const uz = rx * f[1] - ry * f[0];

  const dx = point[0] - cameraPos[0];
  const dy = point[1] - cameraPos[1];
  const dz = point[2] - cameraPos[2];

  const camX = dx * rx + dy * ry + dz * rz;
  const camY = dx * ux + dy * uy + dz * uz;
  const camZ = dx * f[0] + dy * f[1] + dz * f[2];

  const safeZ = Math.max(0.25, camZ);
  const tanHalf = Math.tan(((fovDeg / 2) * Math.PI) / 180);
  const scale = height / (2 * tanHalf);

  return {
    x: width / 2 + (camX / safeZ) * scale,
    y: height / 2 - (camY / safeZ) * scale,
    depth: safeZ,
  };
}

function computeOutwardFaceNormals(
  sample: LandingSampleSpec,
): readonly { vertices: readonly string[]; center: THREE.Vector3; normal: THREE.Vector3 }[] {
  const solidCentroid = new THREE.Vector3();
  let vertexTally = 0;
  for (const face of sample.solidFaces) {
    for (const id of face) {
      const p = sample.pointMap[id]?.pos;
      if (p) {
        solidCentroid.add(new THREE.Vector3(p[0], p[1], p[2]));
        vertexTally++;
      }
    }
  }
  if (vertexTally > 0) solidCentroid.divideScalar(vertexTally);

  return sample.solidFaces.map((face) => {
    const coords = face.map((id) => sample.pointMap[id]?.pos ?? [0, 0, 0]);
    const p0 = new THREE.Vector3(...coords[0]);
    const p1 = new THREE.Vector3(...coords[1]);
    const p2 = new THREE.Vector3(...coords[2]);
    const center = new THREE.Vector3();
    for (const c of coords) center.add(new THREE.Vector3(...c));
    center.divideScalar(Math.max(1, coords.length));

    const normal = new THREE.Vector3()
      .subVectors(p1, p0)
      .cross(new THREE.Vector3().subVectors(p2, p0))
      .normalize();
    if (normal.dot(new THREE.Vector3().subVectors(center, solidCentroid)) < 0) {
      normal.negate();
    }
    return { vertices: face, center, normal };
  });
}

function edgeBelongsToFace(a: string, b: string, face: readonly string[]): boolean {
  const n = face.length;
  for (let i = 0; i < n; i++) {
    const u = face[i];
    const v = face[(i + 1) % n];
    if ((u === a && v === b) || (u === b && v === a)) return true;
  }
  return false;
}

interface ActiveSampleRig {
  sampleId: string;
  sample: LandingSampleSpec;
  group: THREE.Group;
  disposables: { dispose: () => void }[];
  solidFacesMeta: readonly { vertices: readonly string[]; center: THREE.Vector3; normal: THREE.Vector3 }[];
  secNormal: THREE.Vector3;
  secOffset: number;
  edgeObjects: {
    edge: LandingSampleSpec["solidEdges"][number];
    solidLine: THREE.Line | null;
    posSolidLine: THREE.Line | null;
    negSolidLine: THREE.Line | null;
    dashedLine: THREE.Line;
  }[];
  guideLines: { line: THREE.Line; mat: THREE.LineDashedMaterial }[];
  planeMesh: THREE.Mesh;
  planeFillMat: THREE.MeshBasicMaterial;
  planeBorderLine: THREE.Line;
  planeBorderMat: THREE.LineBasicMaterial;
  secFillMesh: THREE.Mesh;
  secFillMat: THREE.MeshBasicMaterial;
  sectionSegments: {
    p1: THREE.Vector3;
    p2: THREE.Vector3;
    geo: THREE.BufferGeometry;
    line: THREE.Line;
    mat: THREE.LineBasicMaterial;
    hostFaceIndex: number;
  }[];
  pointMeshes: { pt: LandingPointSpec; mesh: THREE.Mesh }[];
}

function createDemoContactTexture(): THREE.CanvasTexture | null {
  if (typeof document === "undefined") return null;
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  const grad = ctx.createRadialGradient(64, 64, 8, 64, 64, 62);
  grad.addColorStop(0, "rgba(25, 25, 24, 0.14)");
  grad.addColorStop(0.55, "rgba(25, 25, 24, 0.05)");
  grad.addColorStop(1, "rgba(25, 25, 24, 0)");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 128, 128);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.needsUpdate = true;
  return tex;
}

function buildSampleRig(
  sample: LandingSampleSpec,
  presentation: "default" | "v14" = "default",
): ActiveSampleRig {
  const group = new THREE.Group();
  const disposables: { dispose: () => void }[] = [];
  const track = <T extends { dispose: () => void }>(item: T): T => {
    disposables.push(item);
    return item;
  };
  const isV14 = presentation === "v14";

  // Datum reference ring or soft radial contact disc under solid
  const minY = Math.min(...sample.points.map((p) => p.pos[1]));
  if (isV14) {
    const contactTex = createDemoContactTexture();
    if (contactTex) track(contactTex);
    const contactGeo = track(new THREE.PlaneGeometry(5.6, 5.2));
    contactGeo.rotateX(-Math.PI / 2);
    const contactMat = track(
      new THREE.MeshBasicMaterial({
        map: contactTex ?? undefined,
        color: contactTex ? 0xffffff : 0x191918,
        transparent: true,
        opacity: contactTex ? 0.92 : 0.05,
        depthWrite: false,
      }),
    );
    const contactDisc = new THREE.Mesh(contactGeo, contactMat);
    contactDisc.position.y = minY - 0.04;
    group.add(contactDisc);
  } else {
    const ringGeo = track(new THREE.RingGeometry(2.65, 2.68, 64));
    ringGeo.rotateX(-Math.PI / 2);
    const ringMat = track(
      new THREE.MeshBasicMaterial({
        color: 0x111110,
        transparent: true,
        opacity: 0.08,
        side: THREE.DoubleSide,
      }),
    );
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.position.y = minY - 0.04;
    group.add(ringMesh);
  }

  // Lightweight translucent solid faces (studio face-normal shading in V1.4 presentation)
  const solidFacesMeta = computeOutwardFaceNormals(sample);
  const keyDir = new THREE.Vector3(6.5, 10.5, 4.5).normalize();
  const baseAlbedo = new THREE.Color(0xf5f4f1);
  const baseFaceMat = track(
    new THREE.MeshBasicMaterial({
      color: isV14 ? 0xffffff : 0xeef3f8,
      vertexColors: isV14,
      transparent: true,
      opacity: isV14 ? 0.38 : 0.24,
      side: THREE.DoubleSide,
      depthWrite: false,
    }),
  );
  const sideFaceMat = track(
    new THREE.MeshBasicMaterial({
      color: isV14 ? 0xffffff : 0xf4f6f9,
      vertexColors: isV14,
      transparent: true,
      opacity: isV14 ? 0.24 : 0.14,
      side: THREE.DoubleSide,
      depthWrite: false,
    }),
  );

  for (let fIdx = 0; fIdx < sample.solidFaces.length; fIdx++) {
    const face = sample.solidFaces[fIdx];
    if (face.length < 3) continue;
    const verts: number[] = [];
    const vertColors: number[] = [];
    const faceMeta = solidFacesMeta[fIdx];
    const shade =
      isV14 && faceMeta
        ? Math.min(1.02, 0.8 + Math.max(0, faceMeta.normal.dot(keyDir)) * 0.22)
        : 1;
    const r = Math.min(1, baseAlbedo.r * shade);
    const g = Math.min(1, baseAlbedo.g * shade);
    const b = Math.min(1, baseAlbedo.b * shade);
    const p0 = sample.pointMap[face[0]].pos;
    for (let i = 1; i < face.length - 1; i++) {
      const p1 = sample.pointMap[face[i]].pos;
      const p2 = sample.pointMap[face[i + 1]].pos;
      verts.push(...p0, ...p1, ...p2);
      if (isV14) {
        vertColors.push(r, g, b, r, g, b, r, g, b);
      }
    }
    const faceGeo = track(new THREE.BufferGeometry());
    faceGeo.setAttribute("position", new THREE.Float32BufferAttribute(verts, 3));
    if (isV14) {
      faceGeo.setAttribute("color", new THREE.Float32BufferAttribute(vertColors, 3));
    }
    const mesh = new THREE.Mesh(faceGeo, fIdx === 0 ? baseFaceMat : sideFaceMat);
    mesh.renderOrder = 1;
    group.add(mesh);
  }

  // Compute oriented section plane (secNormal, secOffset) for half-space V14 occlusion
  const secLoopPts = sample.sectionLoop.map((id) => sample.pointMap[id].pos);
  const secNormal = new THREE.Vector3(0, 1, 0);
  let secOffset = 0;
  if (secLoopPts.length >= 3) {
    const sp0 = new THREE.Vector3(...secLoopPts[0]);
    const sp1 = new THREE.Vector3(...secLoopPts[1]);
    const sp2 = new THREE.Vector3(...secLoopPts[2]);
    const candidate = new THREE.Vector3()
      .subVectors(sp1, sp0)
      .cross(new THREE.Vector3().subVectors(sp2, sp0));
    if (candidate.lengthSq() > 1e-8) {
      secNormal.copy(candidate.normalize());
      secOffset = secNormal.dot(sp0);
    }
  }

  const splitSegmentAtPlane = (
    pA: THREE.Vector3,
    pB: THREE.Vector3,
  ): {
    pos: readonly [THREE.Vector3, THREE.Vector3] | null;
    neg: readonly [THREE.Vector3, THREE.Vector3] | null;
  } => {
    const da = pA.dot(secNormal) - secOffset;
    const db = pB.dot(secNormal) - secOffset;
    const eps = 1e-4;
    if (da >= -eps && db >= -eps) return { pos: [pA, pB], neg: null };
    if (da <= eps && db <= eps) return { pos: null, neg: [pA, pB] };
    const t = Math.max(0, Math.min(1, da / (da - db)));
    const mid = new THREE.Vector3().lerpVectors(pA, pB, t);
    return da > 0
      ? { pos: [pA, mid], neg: [mid, pB] }
      : { neg: [pA, mid], pos: [mid, pB] };
  };

  // Dual front-solid / back-dashed materials (split at section plane in V14 for true 3D occlusion)
  const edgeObjects = sample.solidEdges.map((edge) => {
    const a = sample.pointMap[edge.from].pos;
    const b = sample.pointMap[edge.to].pos;

    let solidLine: THREE.Line | null = null;
    let posSolidLine: THREE.Line | null = null;
    let negSolidLine: THREE.Line | null = null;

    if (isV14) {
      const aVec = new THREE.Vector3(...a);
      const bVec = new THREE.Vector3(...b);
      const { pos, neg } = splitSegmentAtPlane(aVec, bVec);
      if (pos) {
        const geo = track(new THREE.BufferGeometry().setFromPoints([pos[0], pos[1]]));
        const mat = track(
          new THREE.LineBasicMaterial({
            color: edge.kind === "altitude" ? 0x005bab : 0x1b1b19,
            transparent: true,
            opacity: 0.9,
          }),
        );
        posSolidLine = new THREE.Line(geo, mat);
        posSolidLine.renderOrder = 8;
        group.add(posSolidLine);
      }
      if (neg) {
        const geo = track(new THREE.BufferGeometry().setFromPoints([neg[0], neg[1]]));
        const mat = track(
          new THREE.LineBasicMaterial({
            color: edge.kind === "altitude" ? 0x005bab : 0x1b1b19,
            transparent: true,
            opacity: 0.9,
          }),
        );
        negSolidLine = new THREE.Line(geo, mat);
        negSolidLine.renderOrder = 3;
        group.add(negSolidLine);
      }
    } else {
      const solidGeo = track(new THREE.BufferGeometry());
      solidGeo.setAttribute("position", new THREE.Float32BufferAttribute([...a, ...b], 3));
      const solidMat = track(
        new THREE.LineBasicMaterial({
          color: edge.kind === "altitude" ? 0x005bab : 0x1b1b19,
          transparent: true,
          opacity: 0.9,
        }),
      );
      solidLine = new THREE.Line(solidGeo, solidMat);
      solidLine.renderOrder = 3;
      group.add(solidLine);
    }

    const dashedGeo = track(new THREE.BufferGeometry());
    dashedGeo.setAttribute("position", new THREE.Float32BufferAttribute([...a, ...b], 3));
    const dashedMat = track(
      new THREE.LineDashedMaterial({
        color: 0x6b7280,
        dashSize: 0.18,
        gapSize: 0.13,
        transparent: true,
        opacity: 0.72,
      }),
    );
    const dashedLine = new THREE.Line(dashedGeo, dashedMat);
    dashedLine.computeLineDistances();
    dashedLine.renderOrder = 2;

    group.add(dashedLine);
    return { edge, solidLine, posSolidLine, negSolidLine, dashedLine };
  });

  // Base diagonals / construction guides
  const guideLines = sample.guideEdges.map((edge) => {
    const a = sample.pointMap[edge.from].pos;
    const b = sample.pointMap[edge.to].pos;
    const geo = track(new THREE.BufferGeometry());
    geo.setAttribute("position", new THREE.Float32BufferAttribute([...a, ...b], 3));
    const mat = track(
      new THREE.LineDashedMaterial({
        color: 0x8a857e,
        dashSize: 0.16,
        gapSize: 0.16,
        transparent: true,
        opacity: 0,
      }),
    );
    const line = new THREE.Line(geo, mat);
    line.computeLineDistances();
    line.renderOrder = 2;
    group.add(line);
    return { line, mat };
  });

  // Right-angle altitude symbol (e.g. SA ⊥ (ABCD))
  if (sample.altitudePair && sample.basePolygon.length >= 2) {
    const footId = sample.altitudePair[1];
    const topId = sample.altitudePair[0];
    const foot = new THREE.Vector3(...sample.pointMap[footId].pos);
    const upDir = new THREE.Vector3(...sample.pointMap[topId].pos).sub(foot).normalize();
    const bId = sample.basePolygon.find((id) => id !== footId) ?? "B";
    const dId = [...sample.basePolygon].reverse().find((id) => id !== footId) ?? "D";
    const createTick = (dirPointId: string) => {
      const dir = new THREE.Vector3(...sample.pointMap[dirPointId].pos).sub(foot).normalize();
      const s = 0.34;
      const pA = foot.clone().addScaledVector(dir, s);
      const pCorner = foot.clone().addScaledVector(dir, s).addScaledVector(upDir, s);
      const pB = foot.clone().addScaledVector(upDir, s);
      const geo = track(new THREE.BufferGeometry().setFromPoints([pA, pCorner, pB]));
      const mat = track(
        new THREE.LineBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.72 }),
      );
      group.add(new THREE.Line(geo, mat));
    };
    createTick(bId);
    createTick(dId);
  }

  // Bounded cutting plane (MNP)
  const pq = sample.planeQuad;
  const planeGeo = track(new THREE.BufferGeometry());
  planeGeo.setAttribute(
    "position",
    new THREE.Float32BufferAttribute(
      [...pq[0], ...pq[1], ...pq[2], ...pq[0], ...pq[2], ...pq[3]],
      3,
    ),
  );
  const planeFillMat = track(
    new THREE.MeshBasicMaterial({
      color: 0x0075de,
      transparent: true,
      opacity: 0.14,
      side: THREE.DoubleSide,
      depthWrite: false,
    }),
  );
  const planeMesh = new THREE.Mesh(planeGeo, planeFillMat);
  planeMesh.renderOrder = 4;
  group.add(planeMesh);

  const planeBorderGeo = track(new THREE.BufferGeometry());
  planeBorderGeo.setAttribute(
    "position",
    new THREE.Float32BufferAttribute([...pq[0], ...pq[1], ...pq[2], ...pq[3], ...pq[0]], 3),
  );
  const planeBorderMat = track(
    new THREE.LineBasicMaterial({
      color: 0x0075de,
      transparent: true,
      opacity: 0.45,
    }),
  );
  const planeBorderLine = new THREE.Line(planeBorderGeo, planeBorderMat);
  planeBorderLine.renderOrder = 5;
  group.add(planeBorderLine);

  // Cross-section polygon fill
  const secPositions: number[] = [];
  for (let i = 1; i < secLoopPts.length - 1; i++) {
    secPositions.push(...secLoopPts[0], ...secLoopPts[i], ...secLoopPts[i + 1]);
  }
  const secFillGeo = track(new THREE.BufferGeometry());
  secFillGeo.setAttribute("position", new THREE.Float32BufferAttribute(secPositions, 3));
  const secFillMat = track(
    new THREE.MeshBasicMaterial({
      color: 0xdd5b00,
      transparent: true,
      opacity: 0.24,
      side: THREE.DoubleSide,
      depthWrite: false,
    }),
  );
  const secFillMesh = new THREE.Mesh(secFillGeo, secFillMat);
  secFillMesh.renderOrder = 6;
  group.add(secFillMesh);

  // Coplanar check per section segment so back-face section traces soften behind front faces in V14
  const findHostFaceIndex = (pA: THREE.Vector3, pB: THREE.Vector3): number => {
    for (let fIdx = 0; fIdx < solidFacesMeta.length; fIdx++) {
      const fm = solidFacesMeta[fIdx];
      const da = Math.abs(fm.normal.dot(new THREE.Vector3().subVectors(pA, fm.center)));
      const db = Math.abs(fm.normal.dot(new THREE.Vector3().subVectors(pB, fm.center)));
      if (da < 1e-3 && db < 1e-3) return fIdx;
    }
    return 0;
  };

  // Progressive section perimeter edges
  const sectionSegments = sample.sectionLoop.map((id, idx) => {
    const nextId = sample.sectionLoop[(idx + 1) % sample.sectionLoop.length];
    const p1 = new THREE.Vector3(...sample.pointMap[id].pos);
    const p2 = new THREE.Vector3(...sample.pointMap[nextId].pos);
    const hostFaceIndex = findHostFaceIndex(p1, p2);
    const geo = track(new THREE.BufferGeometry().setFromPoints([p1, p1.clone()]));
    const mat = track(
      new THREE.LineBasicMaterial({
        color: isV14 ? 0x9a4006 : 0xc2550a,
        transparent: true,
        opacity: 0.96,
      }),
    );
    const line = new THREE.Line(geo, mat);
    line.renderOrder = 7;
    group.add(line);
    return { p1, p2, geo, line, mat, hostFaceIndex };
  });

  // Shared sphere geometries per role radius (deduplicated resources)
  const geoVertex = track(new THREE.SphereGeometry(0.068, 16, 16));
  const geoSeed = track(new THREE.SphereGeometry(0.095, 16, 16));
  const geoInter = track(new THREE.SphereGeometry(0.11, 16, 16));
  const matVertex = track(new THREE.MeshBasicMaterial({ color: 0x1b1b19 }));
  const matSeed = track(new THREE.MeshBasicMaterial({ color: 0x0075de }));
  const matInter = track(new THREE.MeshBasicMaterial({ color: 0xdd5b00 }));

  const pointMeshes = sample.points.map((pt) => {
    const geo = pt.role === "intersection" ? geoInter : pt.role === "seed" ? geoSeed : geoVertex;
    const mat = pt.role === "intersection" ? matInter : pt.role === "seed" ? matSeed : matVertex;
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(pt.pos[0], pt.pos[1], pt.pos[2]);
    mesh.renderOrder = isV14 ? 9 : 8;
    group.add(mesh);
    return { pt, mesh };
  });

  return {
    sampleId: sample.id,
    sample,
    group,
    disposables,
    solidFacesMeta,
    secNormal,
    secOffset,
    edgeObjects,
    guideLines,
    planeMesh,
    planeFillMat,
    planeBorderLine,
    planeBorderMat,
    secFillMesh,
    secFillMat,
    sectionSegments,
    pointMeshes,
  };
}

export function SpatialSceneCanvas({
  sample = LANDING_PYRAMID_SAMPLE,
  visiblePoints,
  activePoints = [],
  showGuideEdges = false,
  planeOpacity = 0.62,
  sectionProgress = 1,
  sectionFillOpacity = 0.85,
  cameraPos,
  lookAt,
  interactiveOrbit = false,
  orbitResetNonce = 0,
  subtlePointerParallax = false,
  compact = false,
  frameless = false,
  pointTagFilter,
  topBadgeLeft,
  topBadgeRight,
  bottomCaption,
  bottomHint,
  sceneId,
  ariaLabel = "Mô hình hình học không gian 3D Axo",
  presentation = "default",
  onUserOrbit,
}: SpatialSceneCanvasProps) {
  const shellRef = useRef<HTMLDivElement | null>(null);
  const hostRef = useRef<HTMLDivElement | null>(null);
  const labelRefs = useRef<Record<string, HTMLSpanElement | null>>({});

  const targetCamera = cameraPos ?? sample.defaultCamera;
  const targetLookAt = lookAt ?? sample.defaultLookAt;

  const [webglReady, setWebglReady] = useState(false);
  const [shouldMountWebgl, setShouldMountWebgl] = useState(false);
  const webglAllowed = useMemo(() => {
    if (typeof window === "undefined") return false;
    return !window.location.search.includes("no_webgl=1");
  }, []);

  const wakeRenderRef = useRef<() => void>(() => {});
  const syncSampleRigRef = useRef<(nextSample: LandingSampleSpec) => void>(() => {});
  const onUserOrbitRef = useRef(onUserOrbit);
  onUserOrbitRef.current = onUserOrbit;

  const propsRef = useRef({
    sample,
    presentation,
    visiblePoints,
    activePoints,
    showGuideEdges,
    planeOpacity,
    sectionProgress,
    sectionFillOpacity,
    targetCamera,
    targetLookAt,
    interactiveOrbit,
    subtlePointerParallax,
  });
  propsRef.current = {
    sample,
    presentation,
    visiblePoints,
    activePoints,
    showGuideEdges,
    planeOpacity,
    sectionProgress,
    sectionFillOpacity,
    targetCamera,
    targetLookAt,
    interactiveOrbit,
    subtlePointerParallax,
  };

  const sphericalOffsetRef = useRef<{ theta: number; phi: number; radiusScale: number }>({
    theta: 0,
    phi: 0,
    radiusScale: 1,
  });

  useEffect(() => {
    sphericalOffsetRef.current = { theta: 0, phi: 0, radiusScale: 1 };
    wakeRenderRef.current();
  }, [orbitResetNonce, sample.id]);

  // Pre-warm Demo WebGL lazily when approaching Demo viewport (preserves Hero initial load = 1 WebGL context)
  useEffect(() => {
    const shell = shellRef.current;
    if (!shell || typeof window === "undefined" || !webglAllowed) return;
    if (shouldMountWebgl) return;

    let fallbackTimer = 0;
    const triggerMount = () => setShouldMountWebgl(true);

    const mountObserver =
      typeof IntersectionObserver !== "undefined"
        ? new IntersectionObserver(
            (entries) => {
              if (entries.some((entry) => entry.isIntersecting)) {
                triggerMount();
                mountObserver?.disconnect();
              }
            },
            { rootMargin: "320px 0px", threshold: 0.01 },
          )
        : null;
    mountObserver?.observe(shell);

    if (!mountObserver) {
      fallbackTimer = window.setTimeout(triggerMount, 1800);
    }

    return () => {
      mountObserver?.disconnect();
      if (fallbackTimer) window.clearTimeout(fallbackTimer);
    };
  }, [shouldMountWebgl]);

  // Persistent single WebGLRenderer per component mount (0 extra contexts created on sample switches)
  useEffect(() => {
    if (!shouldMountWebgl || !webglAllowed) return;
    const shell = shellRef.current;
    const host = hostRef.current;
    if (!shell || !host || typeof window === "undefined") return;

    const reducedMotion =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let cancelled = false;
    let cleanupInner: (() => void) | null = null;
    let mountTimer = 0;

    const initPersistentRenderer = () => {
      if (cancelled) return;

      let renderer: THREE.WebGLRenderer | null = null;
      try {
        renderer = new THREE.WebGLRenderer({
          antialias: true,
          alpha: true,
          powerPreference: "high-performance",
        });
      } catch {
        setWebglReady(false);
        return;
      }

      const activeRenderer = renderer;
      const maxDpr = window.innerWidth <= 820 ? 1.25 : 1.5;
      activeRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, maxDpr));
      activeRenderer.setClearColor(0x000000, 0);
      activeRenderer.outputColorSpace = THREE.SRGBColorSpace;
      host.appendChild(activeRenderer.domElement);

      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(35, 1.33, 0.1, 100);
      let activeRig: ActiveSampleRig | null = null;

      let rafId = 0;
      let isDisposed = false;
      let isInView = true;
      let scrollPausedUntil = 0;
      let scrollResumeTimer = 0;
      let hasPaintedOnce = false;

      const curCam = new THREE.Vector3(...propsRef.current.targetCamera);
      const curLook = new THREE.Vector3(...propsRef.current.targetLookAt);
      let curPlaneOp = propsRef.current.planeOpacity;
      let curSecProg = propsRef.current.sectionProgress;
      let curSecFill = propsRef.current.sectionFillOpacity;
      let curParallaxX = 0;
      let curParallaxY = 0;
      let targetParallaxX = 0;
      let targetParallaxY = 0;
      let isDragging = false;
      let gestureMode: "idle" | "pending" | "orbit" | "scroll" = "idle";
      let ptrDownId = -1;
      let downPtrX = 0;
      let downPtrY = 0;
      let lastPtrX = 0;
      let lastPtrY = 0;

      const tempVec = new THREE.Vector3();
      const baseVec = new THREE.Vector3();
      const desiredLookVec = new THREE.Vector3();
      const sph = new THREE.Spherical();

      const syncSize = () => {
        const rect = shell.getBoundingClientRect();
        const width = Math.max(120, Math.floor(rect.width));
        const height = Math.max(120, Math.floor(rect.height));
        activeRenderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        return { width, height };
      };
      let viewportSize = syncSize();

      const disposeActiveRig = () => {
        if (!activeRig) return;
        scene.remove(activeRig.group);
        for (const d of activeRig.disposables) d.dispose();
        activeRig = null;
      };

      const swapSample = (nextSample: LandingSampleSpec) => {
        if (activeRig && activeRig.sampleId === nextSample.id) return;
        disposeActiveRig();
        activeRig = buildSampleRig(nextSample, propsRef.current.presentation);
        scene.add(activeRig.group);
        curCam.set(...(propsRef.current.targetCamera));
        curLook.set(...(propsRef.current.targetLookAt));
        curPlaneOp = propsRef.current.planeOpacity;
        curSecProg = propsRef.current.sectionProgress;
        curSecFill = propsRef.current.sectionFillOpacity;
      };

      const renderFrame = () => {
        if (isDisposed || !activeRig) return;
        if (!isInView || document.hidden) {
          rafId = 0;
          return;
        }
        const now = typeof performance !== "undefined" ? performance.now() : Date.now();
        if (hasPaintedOnce && !isDragging && now < scrollPausedUntil) {
          rafId = 0;
          if (!scrollResumeTimer) {
            scrollResumeTimer = window.setTimeout(() => {
              scrollResumeTimer = 0;
              wakeRender();
            }, 130);
          }
          return;
        }

        const p = propsRef.current;
        if (activeRig.sampleId !== p.sample.id) {
          swapSample(p.sample);
        }
        const rig = activeRig;
        const damp = reducedMotion ? 1 : 0.14;

        const isV14Presentation = p.presentation === "v14";
        const stageAspect = viewportSize.width / Math.max(1, viewportSize.height);
        const v14AspectScale =
          isV14Presentation && stageAspect < 1.18
            ? 1 + (1.18 - stageAspect) * 0.78
            : 1;

        desiredLookVec.set(...p.targetLookAt);
        if (isV14Presentation && stageAspect < 1.08) {
          desiredLookVec.y += (1.08 - stageAspect) * 3.4;
        }
        baseVec.set(...p.targetCamera).sub(desiredLookVec);
        sph.setFromVector3(baseVec);
        sph.theta += sphericalOffsetRef.current.theta;
        sph.phi = Math.max(
          0.28,
          Math.min(Math.PI * 0.48, sph.phi + sphericalOffsetRef.current.phi),
        );
        sph.radius *= sphericalOffsetRef.current.radiusScale * v14AspectScale;

        const desiredPos = new THREE.Vector3().setFromSpherical(sph).add(desiredLookVec);
        curParallaxX += (targetParallaxX - curParallaxX) * damp;
        curParallaxY += (targetParallaxY - curParallaxY) * damp;
        desiredPos.x += curParallaxX;
        desiredPos.y -= curParallaxY;

        curCam.lerp(desiredPos, damp);
        curLook.lerp(desiredLookVec, damp);
        camera.position.copy(curCam);
        camera.lookAt(curLook);
        camera.updateMatrixWorld();

        curPlaneOp += (p.planeOpacity - curPlaneOp) * damp;
        curSecProg += (p.sectionProgress - curSecProg) * damp;
        curSecFill += (p.sectionFillOpacity - curSecFill) * damp;
        rig.planeMesh.visible = curPlaneOp > 0.02;
        rig.planeBorderLine.visible = curPlaneOp > 0.02;
        rig.planeFillMat.opacity = curPlaneOp * (isV14Presentation ? 0.13 : 0.16);
        rig.planeBorderMat.opacity = curPlaneOp * (isV14Presentation ? 0.48 : 0.56);

        rig.secFillMesh.visible = curSecFill > 0.02;
        rig.secFillMat.opacity = curSecFill * (isV14Presentation ? 0.44 : 0.25);

        const faceFrontFlags = rig.solidFacesMeta.map((f) => {
          const viewVec = new THREE.Vector3().subVectors(camera.position, f.center).normalize();
          return f.normal.dot(viewVec) > 0.015;
        });

        const totalSegs = rig.sectionSegments.length;
        const scaled = Math.max(0, Math.min(1, curSecProg)) * totalSegs;
        for (let i = 0; i < totalSegs; i++) {
          const seg = rig.sectionSegments[i];
          const segT = Math.max(0, Math.min(1, scaled - i));
          seg.line.visible = segT > 0.01;
          if (seg.line.visible) {
            const endPt = new THREE.Vector3().lerpVectors(seg.p1, seg.p2, segT);
            const posAttr = seg.geo.getAttribute("position") as THREE.BufferAttribute;
            posAttr.setXYZ(1, endPt.x, endPt.y, endPt.z);
            posAttr.needsUpdate = true;
            if (isV14Presentation) {
              const hostFront = faceFrontFlags[seg.hostFaceIndex] ?? true;
              seg.mat.opacity = hostFront ? 0.96 : 0.48;
              seg.line.renderOrder = hostFront ? 7 : 6;
            }
          }
        }

        for (const g of rig.guideLines) {
          g.mat.opacity = p.showGuideEdges ? 0.52 : 0;
          g.line.visible = p.showGuideEdges;
        }

        const camOnPosSide = rig.secNormal.dot(camera.position) >= rig.secOffset;
        for (const item of rig.edgeObjects) {
          const adjacentIndices = rig.solidFacesMeta
            .map((f, idx) => (edgeBelongsToFace(item.edge.from, item.edge.to, f.vertices) ? idx : -1))
            .filter((idx) => idx >= 0);
          const front =
            adjacentIndices.length === 0 || adjacentIndices.some((idx) => faceFrontFlags[idx]);
          if (item.solidLine) {
            item.solidLine.visible = front;
          }
          if (item.posSolidLine) {
            item.posSolidLine.visible = front;
            item.posSolidLine.renderOrder = camOnPosSide ? 8 : 3;
          }
          if (item.negSolidLine) {
            item.negSolidLine.visible = front;
            item.negSolidLine.renderOrder = camOnPosSide ? 3 : 8;
          }
          item.dashedLine.visible = !front;
        }

        const visSet = new Set(p.visiblePoints ?? rig.sample.points.map((pt) => pt.id));
        const actSet = new Set(p.activePoints);

        let projCx = 0;
        let projCy = 0;
        let projCount = 0;
        const projectedMap: Record<string, { x: number; y: number; visible: boolean }> = {};

        for (const pm of rig.pointMeshes) {
          const isVis = visSet.has(pm.pt.id);
          pm.mesh.visible = isVis;
          pm.mesh.scale.setScalar(actSet.has(pm.pt.id) ? 1.32 : 1);

          tempVec.copy(pm.mesh.position).project(camera);
          const sx = (tempVec.x * 0.5 + 0.5) * viewportSize.width;
          const sy = (-tempVec.y * 0.5 + 0.5) * viewportSize.height;
          projectedMap[pm.pt.id] = { x: sx, y: sy, visible: isVis };
          if (isVis) {
            projCx += sx;
            projCy += sy;
            projCount++;
          }
        }

        const avgCx = projCx / Math.max(1, projCount);
        const avgCy = projCy / Math.max(1, projCount);
        const visibleCandidates: LabelCandidate[] = [];

        for (const pm of rig.pointMeshes) {
          const refKey = `${rig.sampleId}:${pm.pt.id}`;
          const tag = labelRefs.current[refKey];
          const pr = projectedMap[pm.pt.id];
          if (!tag || !pr) continue;
          if (!pr.visible) {
            tag.style.opacity = "0";
            continue;
          }
          const vx = pr.x - avgCx;
          const vy = pr.y - avgCy;
          const vLen = Math.hypot(vx, vy) || 1;
          const pushDist = pm.pt.role === "base_center" ? 13 : 16;
          visibleCandidates.push({
            id: pm.pt.id,
            x: pr.x + (vx / vLen) * pushDist,
            y: pr.y + (vy / vLen) * pushDist,
          });
        }

        // 2-pass 2D label collision repulsion prevents overlapping labels (e.g. Cube M/N/E/A)
        separateLabelPositions(visibleCandidates, viewportSize.width, viewportSize.height);
        for (const cand of visibleCandidates) {
          const tag = labelRefs.current[`${rig.sampleId}:${cand.id}`];
          if (!tag) continue;
          tag.style.opacity = "1";
          tag.style.transform = `translate3d(${cand.x.toFixed(1)}px, ${cand.y.toFixed(1)}px, 0) translate(-50%, -50%)`;
        }

        activeRenderer.render(scene, camera);
        hasPaintedOnce = true;

        const settled =
          !isDragging &&
          curCam.distanceTo(desiredPos) < 0.0008 &&
          curLook.distanceTo(desiredLookVec) < 0.0008 &&
          Math.abs(p.planeOpacity - curPlaneOp) < 0.0008 &&
          Math.abs(p.sectionProgress - curSecProg) < 0.0008 &&
          Math.abs(p.sectionFillOpacity - curSecFill) < 0.0008 &&
          Math.abs(targetParallaxX - curParallaxX) < 0.0008 &&
          Math.abs(targetParallaxY - curParallaxY) < 0.0008;

        if (!settled && !reducedMotion) {
          rafId = window.requestAnimationFrame(renderFrame);
        } else {
          rafId = 0;
        }
      };

      const wakeRender = () => {
        if (isDisposed || !isInView || document.hidden) return;
        if (reducedMotion) {
          renderFrame();
          return;
        }
        const now = typeof performance !== "undefined" ? performance.now() : Date.now();
        if (hasPaintedOnce && !isDragging && now < scrollPausedUntil) {
          if (!scrollResumeTimer) {
            scrollResumeTimer = window.setTimeout(() => {
              scrollResumeTimer = 0;
              wakeRender();
            }, 130);
          }
          return;
        }
        if (rafId === 0) {
          rafId = window.requestAnimationFrame(renderFrame);
        }
      };

      wakeRenderRef.current = wakeRender;
      syncSampleRigRef.current = (nextSample: LandingSampleSpec) => {
        swapSample(nextSample);
        renderFrame();
      };

      const onPointerDown = (e: PointerEvent) => {
        if (!propsRef.current.interactiveOrbit) return;
        if (propsRef.current.presentation === "v14") {
          gestureMode = "pending";
          ptrDownId = e.pointerId;
          downPtrX = e.clientX;
          downPtrY = e.clientY;
          lastPtrX = e.clientX;
          lastPtrY = e.clientY;
          if (e.pointerType !== "touch") {
            isDragging = true;
            gestureMode = "orbit";
            shell.setPointerCapture?.(e.pointerId);
            wakeRender();
          }
          return;
        }
        isDragging = true;
        lastPtrX = e.clientX;
        lastPtrY = e.clientY;
        shell.setPointerCapture?.(e.pointerId);
        onUserOrbitRef.current?.();
        wakeRender();
      };

      const onPointerMove = (e: PointerEvent) => {
        if (propsRef.current.presentation === "v14") {
          if (gestureMode === "pending" && e.pointerId === ptrDownId) {
            const totalDx = Math.abs(e.clientX - downPtrX);
            const totalDy = Math.abs(e.clientY - downPtrY);
            if (totalDx < 5 && totalDy < 5) return;
            if (e.pointerType === "touch" && totalDy > totalDx * 1.15) {
              gestureMode = "scroll";
              isDragging = false;
              return;
            }
            gestureMode = "orbit";
            isDragging = true;
            lastPtrX = e.clientX;
            lastPtrY = e.clientY;
            shell.setPointerCapture?.(e.pointerId);
            onUserOrbitRef.current?.();
            wakeRender();
            return;
          }
          if (isDragging && gestureMode === "orbit" && propsRef.current.interactiveOrbit) {
            const dx = e.clientX - lastPtrX;
            const dy = e.clientY - lastPtrY;
            if (Math.hypot(e.clientX - downPtrX, e.clientY - downPtrY) >= 2) {
              onUserOrbitRef.current?.();
            }
            lastPtrX = e.clientX;
            lastPtrY = e.clientY;
            sphericalOffsetRef.current.theta -= dx * 0.009;
            sphericalOffsetRef.current.phi = Math.max(
              -0.65,
              Math.min(0.65, sphericalOffsetRef.current.phi - dy * 0.007),
            );
            wakeRender();
            return;
          }
          if (e.pointerType !== "touch" && propsRef.current.subtlePointerParallax && !reducedMotion) {
            const rect = shell.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
              targetParallaxX = ((e.clientX - rect.left) / rect.width - 0.5) * 0.55;
              targetParallaxY = ((e.clientY - rect.top) / rect.height - 0.5) * 0.35;
              wakeRender();
            }
          }
          return;
        }
        if (isDragging && propsRef.current.interactiveOrbit) {
          const dx = e.clientX - lastPtrX;
          const dy = e.clientY - lastPtrY;
          lastPtrX = e.clientX;
          lastPtrY = e.clientY;
          sphericalOffsetRef.current.theta -= dx * 0.009;
          sphericalOffsetRef.current.phi = Math.max(
            -0.65,
            Math.min(0.65, sphericalOffsetRef.current.phi - dy * 0.007),
          );
          wakeRender();
        } else if (propsRef.current.subtlePointerParallax && !reducedMotion) {
          const rect = shell.getBoundingClientRect();
          if (rect.width > 0 && rect.height > 0) {
            targetParallaxX = ((e.clientX - rect.left) / rect.width - 0.5) * 0.55;
            targetParallaxY = ((e.clientY - rect.top) / rect.height - 0.5) * 0.35;
            wakeRender();
          }
        }
      };

      const onPointerUp = (e: PointerEvent) => {
        if (e.pointerId === ptrDownId) {
          gestureMode = "idle";
          ptrDownId = -1;
        }
        if (isDragging) {
          isDragging = false;
          shell.releasePointerCapture?.(e.pointerId);
          wakeRender();
        }
      };

      const onPointerLeave = () => {
        targetParallaxX = 0;
        targetParallaxY = 0;
        wakeRender();
      };

      shell.addEventListener("pointerdown", onPointerDown);
      shell.addEventListener("pointermove", onPointerMove);
      shell.addEventListener("pointerup", onPointerUp);
      shell.addEventListener("pointercancel", onPointerUp);
      shell.addEventListener("pointerleave", onPointerLeave);

      const ro =
        typeof ResizeObserver !== "undefined"
          ? new ResizeObserver(() => {
              viewportSize = syncSize();
              wakeRender();
            })
          : null;
      ro?.observe(shell);

      const io =
        typeof IntersectionObserver !== "undefined"
          ? new IntersectionObserver(
              (entries) => {
                const visible = entries.some((entry) => entry.isIntersecting);
                isInView = visible;
                if (visible) {
                  wakeRender();
                } else if (rafId !== 0) {
                  window.cancelAnimationFrame(rafId);
                  rafId = 0;
                }
              },
              { threshold: 0.02 },
            )
          : null;
      io?.observe(shell);

      const onVisibilityChange = () => {
        if (document.hidden) {
          if (rafId !== 0) {
            window.cancelAnimationFrame(rafId);
            rafId = 0;
          }
        } else {
          wakeRender();
        }
      };
      const onWindowScroll = () => {
        scrollPausedUntil = (typeof performance !== "undefined" ? performance.now() : Date.now()) + 120;
      };
      window.addEventListener("scroll", onWindowScroll, { passive: true });
      document.addEventListener("visibilitychange", onVisibilityChange);

      const onContextLost = (ev: Event) => {
        ev.preventDefault();
        if (rafId !== 0) {
          window.cancelAnimationFrame(rafId);
          rafId = 0;
        }
        setWebglReady(false);
      };
      activeRenderer.domElement.addEventListener("webglcontextlost", onContextLost);

      swapSample(propsRef.current.sample);
      setWebglReady(true);
      renderFrame();

      cleanupInner = () => {
        isDisposed = true;
        wakeRenderRef.current = () => {};
        syncSampleRigRef.current = () => {};
        if (rafId !== 0) window.cancelAnimationFrame(rafId);
        if (scrollResumeTimer) window.clearTimeout(scrollResumeTimer);
        ro?.disconnect();
        io?.disconnect();
        shell.removeEventListener("pointerdown", onPointerDown);
        shell.removeEventListener("pointermove", onPointerMove);
        shell.removeEventListener("pointerup", onPointerUp);
        shell.removeEventListener("pointercancel", onPointerUp);
        shell.removeEventListener("pointerleave", onPointerLeave);
        window.removeEventListener("scroll", onWindowScroll);
        document.removeEventListener("visibilitychange", onVisibilityChange);
        activeRenderer.domElement.removeEventListener("webglcontextlost", onContextLost);
        disposeActiveRig();
        activeRenderer.dispose();
        if (activeRenderer.domElement.parentNode === host) {
          host.removeChild(activeRenderer.domElement);
        }
        setWebglReady(false);
      };
    };

    const mountRaf =
      typeof window.requestAnimationFrame === "function"
        ? window.requestAnimationFrame(initPersistentRenderer)
        : 0;
    if (mountRaf === 0) {
      mountTimer = window.setTimeout(initPersistentRenderer, 0);
    }

    return () => {
      cancelled = true;
      if (mountRaf !== 0 && typeof window.cancelAnimationFrame === "function") {
        window.cancelAnimationFrame(mountRaf);
      }
      if (mountTimer !== 0) window.clearTimeout(mountTimer);
      cleanupInner?.();
    };
  }, [shouldMountWebgl]);

  // Swap Three.js sample group inside persistent WebGLRenderer (0 new WebGL contexts)
  useEffect(() => {
    if (webglReady) {
      syncSampleRigRef.current(sample);
    }
  }, [sample, webglReady]);

  // Wake sleeping demand-based RAF whenever stage props or camera targets change
  useEffect(() => {
    wakeRenderRef.current();
  }, [
    visiblePoints,
    activePoints,
    showGuideEdges,
    planeOpacity,
    sectionProgress,
    sectionFillOpacity,
    targetCamera,
    targetLookAt,
    interactiveOrbit,
    subtlePointerParallax,
  ]);

  // Skip expensive fallback 3D math completely once WebGL is live
  const svgFallback = useMemo(() => {
    const w = 560;
    const h = 420;
    if (webglReady) {
      return {
        w,
        h,
        labelCoords: {} as Record<string, { x: number; y: number }>,
        solidSegments: [] as {
          from: string;
          to: string;
          kind: LandingSampleSpec["solidEdges"][number]["kind"];
          p1: ProjectedPoint2D;
          p2: ProjectedPoint2D;
          front: boolean;
        }[],
        planePts: [] as { x: number; y: number; depth: number }[],
        sectionPts: [] as ProjectedPoint2D[],
        visibleList: [] as ProjectedPoint2D[],
      };
    }

    const visSet = new Set(visiblePoints ?? sample.points.map((p) => p.id));
    const faces = computeOutwardFaceNormals(sample);
    const camVec = new THREE.Vector3(...targetCamera);

    const isEdgeFront = (a: string, b: string) => {
      const adjacent = faces.filter((f) => edgeBelongsToFace(a, b, f.vertices));
      if (adjacent.length === 0) return true;
      return adjacent.some((f) => {
        const viewVec = new THREE.Vector3().subVectors(camVec, f.center).normalize();
        return f.normal.dot(viewVec) > 0.02;
      });
    };

    const projPoints: Record<string, ProjectedPoint2D> = {};
    for (const p of sample.points) {
      const pr = projectToSvgViewport(p.pos, targetCamera, targetLookAt, w, h, 35);
      projPoints[p.id] = {
        id: p.id,
        label: p.label,
        role: p.role,
        x: pr.x,
        y: pr.y,
        depth: pr.depth,
      };
    }

    const solidSegments = sample.solidEdges.map((e) => ({
      ...e,
      p1: projPoints[e.from],
      p2: projPoints[e.to],
      front: isEdgeFront(e.from, e.to),
    }));

    const planePts = sample.planeQuad.map((v) =>
      projectToSvgViewport(v, targetCamera, targetLookAt, w, h, 35),
    );
    const sectionPts = sample.sectionLoop.map((id) => projPoints[id]).filter(Boolean);
    const visibleList = sample.points.filter((p) => visSet.has(p.id)).map((p) => projPoints[p.id]);
    const cx = visibleList.reduce((acc, p) => acc + p.x, 0) / Math.max(1, visibleList.length);
    const cy = visibleList.reduce((acc, p) => acc + p.y, 0) / Math.max(1, visibleList.length);

    const candidates: LabelCandidate[] = visibleList.map((pt) => {
      const vx = pt.x - cx;
      const vy = pt.y - cy;
      const len = Math.hypot(vx, vy) || 1;
      const push = pt.role === "base_center" ? 13 : 16;
      return { id: pt.id, x: pt.x + (vx / len) * push, y: pt.y + (vy / len) * push };
    });
    separateLabelPositions(candidates, w, h);
    const labelCoords = Object.fromEntries(candidates.map((c) => [c.id, { x: c.x, y: c.y }]));

    return { w, h, labelCoords, solidSegments, planePts, sectionPts, visibleList };
  }, [webglReady, sample, targetCamera, targetLookAt, visiblePoints]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!interactiveOrbit) return;
    const step = 0.14;
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      sphericalOffsetRef.current.theta -= step;
      wakeRenderRef.current();
      onUserOrbit?.();
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      sphericalOffsetRef.current.theta += step;
      wakeRenderRef.current();
      onUserOrbit?.();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      sphericalOffsetRef.current.phi = Math.max(-0.65, sphericalOffsetRef.current.phi - step * 0.7);
      wakeRenderRef.current();
      onUserOrbit?.();
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      sphericalOffsetRef.current.phi = Math.min(0.65, sphericalOffsetRef.current.phi + step * 0.7);
      wakeRenderRef.current();
      onUserOrbit?.();
    }
  };

  const activeSet = useMemo(() => new Set(activePoints), [activePoints]);
  const tagFilterSet = useMemo(
    () => (pointTagFilter ? new Set(pointTagFilter) : null),
    [pointTagFilter],
  );

  return (
    <div
      id={sceneId}
      ref={shellRef}
      className={`axo-sp-scene-shell${interactiveOrbit ? " is-interactive" : ""}${compact ? " is-compact" : ""}${frameless ? " is-frameless" : ""}${presentation === "v14" ? " is-v14" : ""}`}
      role={interactiveOrbit ? "application" : "img"}
      aria-label={ariaLabel}
      tabIndex={interactiveOrbit ? 0 : undefined}
      onKeyDown={handleKeyDown}
    >
      {!frameless && <div className="axo-sp-scene-grid" aria-hidden="true" />}
      <div
        ref={hostRef}
        className="axo-sp-scene-canvas-host"
        style={{ visibility: webglReady && webglAllowed ? "visible" : "hidden" }}
      />

      {(!webglReady || !webglAllowed) && (
        <svg
          className="axo-sp-scene-svg"
          viewBox={`0 0 ${svgFallback.w} ${svgFallback.h}`}
          preserveAspectRatio="xMidYMid meet"
          aria-hidden="true"
        >
          {planeOpacity > 0.02 && (
            <polygon
              points={svgFallback.planePts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")}
              fill="#0075de"
              fillOpacity={(planeOpacity * 0.14).toFixed(3)}
              stroke="#0075de"
              strokeOpacity={(planeOpacity * 0.55).toFixed(3)}
              strokeWidth="1.25"
            />
          )}

          {svgFallback.solidSegments.map((seg) => (
            <line
              key={`${seg.from}-${seg.to}`}
              x1={seg.p1.x}
              y1={seg.p1.y}
              x2={seg.p2.x}
              y2={seg.p2.y}
              stroke={seg.kind === "altitude" && seg.front ? "#005bab" : seg.front ? "#1b1b19" : "#6b7280"}
              strokeWidth={seg.front ? 1.85 : 1.35}
              strokeDasharray={seg.front ? undefined : "5 4"}
              strokeOpacity={seg.front ? 0.88 : 0.65}
            />
          ))}

          {sectionFillOpacity > 0.02 && (
            <polygon
              points={svgFallback.sectionPts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")}
              fill="#dd5b00"
              fillOpacity={(sectionFillOpacity * 0.24).toFixed(3)}
            />
          )}

          {sectionProgress > 0.02 &&
            svgFallback.sectionPts.map((pt, idx) => {
              const nextPt = svgFallback.sectionPts[(idx + 1) % svgFallback.sectionPts.length];
              const ratio = Math.max(
                0,
                Math.min(1, sectionProgress * svgFallback.sectionPts.length - idx),
              );
              if (ratio <= 0.01 || !nextPt) return null;
              return (
                <line
                  key={`sec-${pt.id}-${nextPt.id}`}
                  x1={pt.x}
                  y1={pt.y}
                  x2={pt.x + (nextPt.x - pt.x) * ratio}
                  y2={pt.y + (nextPt.y - pt.y) * ratio}
                  stroke="#c2550a"
                  strokeWidth="2.35"
                  strokeLinecap="round"
                />
              );
            })}

          {svgFallback.visibleList.map((pt) => {
            const labelText =
              "label" in pt && typeof pt.label === "string"
                ? pt.label
                : pt.id.replace("_prime", "′");
            const showLabel = !tagFilterSet || tagFilterSet.has(pt.id);
            const fillColor =
              pt.role === "intersection"
                ? "#dd5b00"
                : pt.role === "seed"
                  ? "#0075de"
                  : "#1b1b19";
            return (
              <g key={`svg-dot-${pt.id}`}>
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={pt.role === "intersection" ? 5.2 : pt.role === "seed" ? 4.4 : 3.4}
                  fill={fillColor}
                />
                {showLabel && (
                  <text
                    x={pt.x + 8}
                    y={pt.y - 7}
                    fontSize="11"
                    fontWeight="700"
                    fontFamily={
                      presentation === "v14"
                        ? "Inter, system-ui, sans-serif"
                        : "JetBrains Mono, ui-monospace, monospace"
                    }
                    fill={fillColor}
                  >
                    {labelText}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      )}

      {/* Projected 2D point badges keyed per sample+point to eliminate carryover on sample switch */}
      <div className="axo-sp-scene-labels" aria-hidden="true">
        {sample.points
          .filter((pt) => !tagFilterSet || tagFilterSet.has(pt.id))
          .map((pt) => {
          const isActive = activeSet.has(pt.id);
          const roleClass =
            pt.role === "seed"
              ? " is-seed"
              : pt.role === "intersection"
                ? " is-intersection"
                : "";
          const refKey = `${sample.id}:${pt.id}`;
          return (
            <span
              key={refKey}
              data-point-id={pt.id}
              data-sample-id={sample.id}
              ref={(el) => {
                if (el) {
                  labelRefs.current[refKey] = el;
                } else {
                  delete labelRefs.current[refKey];
                }
              }}
              className={`axo-sp-point-tag${roleClass}${isActive ? " is-active" : ""}`}
              style={
                webglReady && webglAllowed
                  ? undefined
                  : { opacity: 0 }
              }
            >
              {pt.label}
            </span>
          );
        })}
      </div>

      {(topBadgeLeft || topBadgeRight) && (
        <div className="axo-sp-scene-hud-top">
          {topBadgeLeft ? <span className="axo-sp-scene-chip">{topBadgeLeft}</span> : <span />}
          {topBadgeRight && (
            <span className="axo-sp-scene-chip is-mono">{topBadgeRight}</span>
          )}
        </div>
      )}

      {(bottomCaption || bottomHint) && (
        <div className="axo-sp-scene-hud-bottom">
          {bottomCaption ? <span className="axo-sp-scene-pill">{bottomCaption}</span> : <span />}
          {bottomHint && <span className="axo-sp-scene-hint">{bottomHint}</span>}
        </div>
      )}
    </div>
  );
}
