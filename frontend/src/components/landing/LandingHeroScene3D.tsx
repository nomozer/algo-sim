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
  readonly topBadgeLeft?: string;
  readonly topBadgeRight?: string;
  readonly bottomCaption?: string;
  readonly bottomHint?: string;
  readonly sceneId?: string;
  readonly ariaLabel?: string;
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

function projectToSvgViewport(
  point: Vec3Tuple,
  cameraPos: Vec3Tuple,
  lookAt: Vec3Tuple,
  width: number,
  height: number,
  fovDeg = 36,
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
  const baseCount = Math.max(1, sample.solidFaces.length);
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

  void baseCount;
  return sample.solidFaces.map((face) => {
    const coords = face.map((id) => sample.pointMap[id]?.pos ?? [0, 0, 0]);
    const p0 = new THREE.Vector3(...coords[0]);
    const p1 = new THREE.Vector3(...coords[1]);
    const p2 = new THREE.Vector3(...coords[2]);
    const center = new THREE.Vector3();
    for (const c of coords) center.add(new THREE.Vector3(...c));
    center.divideScalar(Math.max(1, coords.length));

    const normal = new THREE.Vector3().subVectors(p1, p0).cross(new THREE.Vector3().subVectors(p2, p0)).normalize();
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
  topBadgeLeft,
  topBadgeRight,
  bottomCaption,
  bottomHint,
  sceneId,
  ariaLabel = "Mô hình hình học không gian 3D Axo",
  onUserOrbit,
}: SpatialSceneCanvasProps) {
  const shellRef = useRef<HTMLDivElement | null>(null);
  const hostRef = useRef<HTMLDivElement | null>(null);
  const labelRefs = useRef<Record<string, HTMLSpanElement | null>>({});

  const targetCamera = cameraPos ?? sample.defaultCamera;
  const targetLookAt = lookAt ?? sample.defaultLookAt;

  const [webglReady, setWebglReady] = useState(false);
  const onUserOrbitRef = useRef(onUserOrbit);
  onUserOrbitRef.current = onUserOrbit;

  const propsRef = useRef({
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
  }, [orbitResetNonce, sample.id]);

  // Precompute fallback SVG geometry using the exact same 3D points & projection math
  const svgFallback = useMemo(() => {
    const w = 560;
    const h = 420;
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
    const cx =
      visibleList.reduce((acc, p) => acc + p.x, 0) / Math.max(1, visibleList.length);
    const cy =
      visibleList.reduce((acc, p) => acc + p.y, 0) / Math.max(1, visibleList.length);

    return { w, h, projPoints, solidSegments, planePts, sectionPts, visibleList, cx, cy };
  }, [sample, targetCamera, targetLookAt, visiblePoints]);

  useEffect(() => {
    const shell = shellRef.current;
    const host = hostRef.current;
    if (!shell || !host || typeof window === "undefined") return;

    const reducedMotion =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let renderer: THREE.WebGLRenderer | null = null;
    let rafId = 0;
    let isDisposed = false;
    let isInView = true;

    const disposables: { dispose: () => void }[] = [];
    const track = <T extends { dispose: () => void }>(item: T): T => {
      disposables.push(item);
      return item;
    };

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
    activeRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    activeRenderer.setClearColor(0x000000, 0);
    activeRenderer.outputColorSpace = THREE.SRGBColorSpace;
    host.appendChild(activeRenderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(35, 1.33, 0.1, 100);

    // Subtle studio lighting on clean porcelain/alabaster surfaces
    scene.add(new THREE.AmbientLight(0xffffff, 1.25));
    const keyLight = new THREE.DirectionalLight(0xfffbf4, 1.45);
    keyLight.position.set(7, 11, -5);
    scene.add(keyLight);
    const rimLight = new THREE.DirectionalLight(0xd9ecff, 0.72);
    rimLight.position.set(-7, 4, 6);
    scene.add(rimLight);

    // Subtle base grid circle datum underneath solid
    const minY = Math.min(...sample.points.map((p) => p.pos[1]));
    const datumGroup = new THREE.Group();
    const ringGeo = track(new THREE.RingGeometry(2.65, 2.68, 72));
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
    datumGroup.add(ringMesh);
    scene.add(datumGroup);

    // Translucent solid faces
    const solidFacesMeta = computeOutwardFaceNormals(sample);
    const baseFaceMat = track(
      new THREE.MeshPhysicalMaterial({
        color: 0xeef3f8,
        transparent: true,
        opacity: 0.24,
        roughness: 0.45,
        metalness: 0.0,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const sideFaceMat = track(
      new THREE.MeshPhysicalMaterial({
        color: 0xf7f8fa,
        transparent: true,
        opacity: 0.14,
        roughness: 0.35,
        metalness: 0.0,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );

    for (let fIdx = 0; fIdx < sample.solidFaces.length; fIdx++) {
      const face = sample.solidFaces[fIdx];
      if (face.length < 3) continue;
      const verts: number[] = [];
      const p0 = sample.pointMap[face[0]].pos;
      for (let i = 1; i < face.length - 1; i++) {
        const p1 = sample.pointMap[face[i]].pos;
        const p2 = sample.pointMap[face[i + 1]].pos;
        verts.push(...p0, ...p1, ...p2);
      }
      const faceGeo = track(new THREE.BufferGeometry());
      faceGeo.setAttribute("position", new THREE.Float32BufferAttribute(verts, 3));
      faceGeo.computeVertexNormals();
      const mesh = new THREE.Mesh(faceGeo, fIdx === 0 ? baseFaceMat : sideFaceMat);
      mesh.renderOrder = 1;
      scene.add(mesh);
    }

    // Dual front-solid / back-dashed materials for every solid edge
    const edgeObjects = sample.solidEdges.map((edge) => {
      const a = sample.pointMap[edge.from].pos;
      const b = sample.pointMap[edge.to].pos;

      const solidGeo = track(new THREE.BufferGeometry());
      solidGeo.setAttribute("position", new THREE.Float32BufferAttribute([...a, ...b], 3));
      const solidMat = track(
        new THREE.LineBasicMaterial({
          color: edge.kind === "altitude" ? 0x005bab : 0x1b1b19,
          transparent: true,
          opacity: 0.88,
        }),
      );
      const solidLine = new THREE.Line(solidGeo, solidMat);
      solidLine.renderOrder = 3;

      const dashedGeo = track(new THREE.BufferGeometry());
      dashedGeo.setAttribute("position", new THREE.Float32BufferAttribute([...a, ...b], 3));
      const dashedMat = track(
        new THREE.LineDashedMaterial({
          color: 0x6b7280,
          dashSize: 0.18,
          gapSize: 0.13,
          transparent: true,
          opacity: 0.7,
        }),
      );
      const dashedLine = new THREE.Line(dashedGeo, dashedMat);
      dashedLine.computeLineDistances();
      dashedLine.renderOrder = 2;

      scene.add(solidLine);
      scene.add(dashedLine);
      return { edge, solidLine, dashedLine };
    });

    // Optional base diagonals / construction guides
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
      scene.add(line);
      return { line, mat };
    });

    // Orthogonal right-angle tick for altitude SA ⊥ (ABCD)
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
        const geo = track(
          new THREE.BufferGeometry().setFromPoints([pA, pCorner, pB]),
        );
        const mat = track(
          new THREE.LineBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.72 }),
        );
        scene.add(new THREE.Line(geo, mat));
      };
      createTick(bId);
      createTick(dId);
    }

    // Bounded Cutting Plane (MNP)
    const pq = sample.planeQuad;
    const planeGeo = track(new THREE.BufferGeometry());
    planeGeo.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(
        [...pq[0], ...pq[1], ...pq[2], ...pq[0], ...pq[2], ...pq[3]],
        3,
      ),
    );
    planeGeo.computeVertexNormals();
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
    scene.add(planeMesh);

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
    scene.add(planeBorderLine);

    // Cross-Section Polygon Fill (MENPF / MNEPFQ)
    const secPositions: number[] = [];
    const secLoopPts = sample.sectionLoop.map((id) => sample.pointMap[id].pos);
    for (let i = 1; i < secLoopPts.length - 1; i++) {
      secPositions.push(...secLoopPts[0], ...secLoopPts[i], ...secLoopPts[i + 1]);
    }
    const secFillGeo = track(new THREE.BufferGeometry());
    secFillGeo.setAttribute("position", new THREE.Float32BufferAttribute(secPositions, 3));
    const secFillMat = track(
      new THREE.MeshBasicMaterial({
        color: 0xd96b18,
        transparent: true,
        opacity: 0.24,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const secFillMesh = new THREE.Mesh(secFillGeo, secFillMat);
    secFillMesh.renderOrder = 6;
    scene.add(secFillMesh);

    // Progressive Section Perimeter Edges
    const sectionSegments = sample.sectionLoop.map((id, idx) => {
      const nextId = sample.sectionLoop[(idx + 1) % sample.sectionLoop.length];
      const p1 = new THREE.Vector3(...sample.pointMap[id].pos);
      const p2 = new THREE.Vector3(...sample.pointMap[nextId].pos);
      const geo = track(new THREE.BufferGeometry().setFromPoints([p1, p1.clone()]));
      const mat = track(
        new THREE.LineBasicMaterial({
          color: 0xc2550a,
          transparent: true,
          opacity: 0.96,
        }),
      );
      const line = new THREE.Line(geo, mat);
      line.renderOrder = 7;
      scene.add(line);
      return { p1, p2, geo, line, mat };
    });

    // Vertex Spheres
    const pointMeshes = sample.points.map((pt) => {
      const radius =
        pt.role === "intersection" ? 0.11 : pt.role === "seed" ? 0.095 : 0.07;
      const color =
        pt.role === "intersection"
          ? 0xc2550a
          : pt.role === "seed"
            ? 0x0075de
            : 0x1b1b19;
      const geo = track(new THREE.SphereGeometry(radius, 20, 20));
      const mat = track(
        new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity: 1,
        }),
      );
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(pt.pos[0], pt.pos[1], pt.pos[2]);
      mesh.renderOrder = 8;
      scene.add(mesh);
      return { pt, mesh, mat };
    });

    // Smoothed camera & visual state
    const curCam = new THREE.Vector3(...propsRef.current.targetCamera);
    const curLook = new THREE.Vector3(...propsRef.current.targetLookAt);
    let curPlaneOp = propsRef.current.planeOpacity;
    let curSecProg = propsRef.current.sectionProgress;
    let curSecFill = propsRef.current.sectionFillOpacity;
    let curParallaxX = 0;
    let curParallaxY = 0;
    let targetParallaxX = 0;
    let targetParallaxY = 0;

    // Interactive orbit pointer handling (never steals wheel vertical scroll)
    let isDragging = false;
    let lastPtrX = 0;
    let lastPtrY = 0;

    const onPointerDown = (e: PointerEvent) => {
      if (!propsRef.current.interactiveOrbit) return;
      isDragging = true;
      lastPtrX = e.clientX;
      lastPtrY = e.clientY;
      shell.setPointerCapture?.(e.pointerId);
      onUserOrbitRef.current?.();
    };

    const onPointerMove = (e: PointerEvent) => {
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
      } else if (propsRef.current.subtlePointerParallax && !reducedMotion) {
        const rect = shell.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          targetParallaxX = ((e.clientX - rect.left) / rect.width - 0.5) * 0.55;
          targetParallaxY = ((e.clientY - rect.top) / rect.height - 0.5) * 0.35;
        }
      }
    };

    const onPointerUp = (e: PointerEvent) => {
      if (isDragging) {
        isDragging = false;
        shell.releasePointerCapture?.(e.pointerId);
      }
    };

    const onPointerLeave = () => {
      targetParallaxX = 0;
      targetParallaxY = 0;
    };

    shell.addEventListener("pointerdown", onPointerDown);
    shell.addEventListener("pointermove", onPointerMove);
    shell.addEventListener("pointerup", onPointerUp);
    shell.addEventListener("pointercancel", onPointerUp);
    shell.addEventListener("pointerleave", onPointerLeave);

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
    const ro =
      typeof ResizeObserver !== "undefined"
        ? new ResizeObserver(() => {
            viewportSize = syncSize();
          })
        : null;
    ro?.observe(shell);

    const io =
      typeof IntersectionObserver !== "undefined"
        ? new IntersectionObserver(
            (entries) => {
              isInView = entries.some((entry) => entry.isIntersecting);
            },
            { threshold: 0.05 },
          )
        : null;
    io?.observe(shell);

    const onContextLost = (ev: Event) => {
      ev.preventDefault();
      setWebglReady(false);
    };
    activeRenderer.domElement.addEventListener("webglcontextlost", onContextLost);

    const tempVec = new THREE.Vector3();
    const baseVec = new THREE.Vector3();
    const sph = new THREE.Spherical();

    const renderFrame = (timeMs: number) => {
      if (isDisposed) return;
      rafId = window.requestAnimationFrame(renderFrame);
      if (!isInView && !isDragging) return;

      const p = propsRef.current;
      const damp = reducedMotion ? 1 : 0.1;

      baseVec.set(...p.targetCamera).sub(new THREE.Vector3(...p.targetLookAt));
      sph.setFromVector3(baseVec);
      sph.theta += sphericalOffsetRef.current.theta;
      sph.phi = Math.max(0.28, Math.min(Math.PI * 0.48, sph.phi + sphericalOffsetRef.current.phi));
      sph.radius *= sphericalOffsetRef.current.radiusScale;

      if (p.subtlePointerParallax && !reducedMotion) {
        const idleBreath = Math.sin(timeMs * 0.00055) * 0.055;
        sph.theta += idleBreath;
      }

      const desiredPos = new THREE.Vector3().setFromSpherical(sph).add(new THREE.Vector3(...p.targetLookAt));
      curParallaxX += (targetParallaxX - curParallaxX) * damp;
      curParallaxY += (targetParallaxY - curParallaxY) * damp;
      desiredPos.x += curParallaxX;
      desiredPos.y -= curParallaxY;

      curCam.lerp(desiredPos, damp);
      curLook.lerp(new THREE.Vector3(...p.targetLookAt), damp);
      camera.position.copy(curCam);
      camera.lookAt(curLook);
      camera.updateMatrixWorld();

      curPlaneOp += (p.planeOpacity - curPlaneOp) * damp;
      curSecProg += (p.sectionProgress - curSecProg) * damp;
      curSecFill += (p.sectionFillOpacity - curSecFill) * damp;

      planeMesh.visible = curPlaneOp > 0.02;
      planeBorderLine.visible = curPlaneOp > 0.02;
      planeFillMat.opacity = curPlaneOp * 0.16;
      planeBorderMat.opacity = curPlaneOp * 0.56;

      secFillMesh.visible = curSecFill > 0.02;
      secFillMat.opacity = curSecFill * 0.25;

      // Progressive cross-section segment reveal
      const totalSegs = sectionSegments.length;
      const scaled = Math.max(0, Math.min(1, curSecProg)) * totalSegs;
      for (let i = 0; i < totalSegs; i++) {
        const seg = sectionSegments[i];
        const segT = Math.max(0, Math.min(1, scaled - i));
        seg.line.visible = segT > 0.01;
        if (seg.line.visible) {
          const endPt = new THREE.Vector3().lerpVectors(seg.p1, seg.p2, segT);
          const posAttr = seg.geo.getAttribute("position") as THREE.BufferAttribute;
          posAttr.setXYZ(1, endPt.x, endPt.y, endPt.z);
          posAttr.needsUpdate = true;
        }
      }

      // Guide diagonals visibility
      for (const g of guideLines) {
        g.mat.opacity = p.showGuideEdges ? 0.52 : 0;
        g.line.visible = p.showGuideEdges;
      }

      // Depth-correct solid/dashed visibility for every solid edge
      for (const item of edgeObjects) {
        const adjacent = solidFacesMeta.filter((f) =>
          edgeBelongsToFace(item.edge.from, item.edge.to, f.vertices),
        );
        const front =
          adjacent.length === 0 ||
          adjacent.some((f) => {
            const viewVec = new THREE.Vector3().subVectors(camera.position, f.center).normalize();
            return f.normal.dot(viewVec) > 0.015;
          });
        item.solidLine.visible = front;
        item.dashedLine.visible = !front;
      }

      const visSet = new Set(p.visiblePoints ?? sample.points.map((pt) => pt.id));
      const actSet = new Set(p.activePoints);

      // Update vertex spheres + projected 2D labels outside silhouette center
      let projCx = 0;
      let projCy = 0;
      let projCount = 0;
      const projectedMap: Record<string, { x: number; y: number; visible: boolean }> = {};

      for (const pm of pointMeshes) {
        const isVis = visSet.has(pm.pt.id);
        pm.mesh.visible = isVis;
        const isAct = actSet.has(pm.pt.id);
        const scale = isAct ? 1.32 : 1;
        pm.mesh.scale.setScalar(scale);

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

      for (const pm of pointMeshes) {
        const tag = labelRefs.current[pm.pt.id];
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
        const lx = Math.max(22, Math.min(viewportSize.width - 22, pr.x + (vx / vLen) * pushDist));
        const ly = Math.max(44, Math.min(viewportSize.height - 44, pr.y + (vy / vLen) * pushDist));
        tag.style.opacity = "1";
        tag.style.transform = `translate3d(${lx.toFixed(1)}px, ${ly.toFixed(1)}px, 0) translate(-50%, -50%)`;
      }

      activeRenderer.render(scene, camera);
    };

    setWebglReady(true);
    rafId = window.requestAnimationFrame(renderFrame);

    return () => {
      isDisposed = true;
      if (rafId !== 0) window.cancelAnimationFrame(rafId);
      ro?.disconnect();
      io?.disconnect();
      shell.removeEventListener("pointerdown", onPointerDown);
      shell.removeEventListener("pointermove", onPointerMove);
      shell.removeEventListener("pointerup", onPointerUp);
      shell.removeEventListener("pointercancel", onPointerUp);
      shell.removeEventListener("pointerleave", onPointerLeave);
      activeRenderer.domElement.removeEventListener("webglcontextlost", onContextLost);
      for (const d of disposables) d.dispose();
      activeRenderer.dispose();
      if (activeRenderer.domElement.parentNode === host) {
        host.removeChild(activeRenderer.domElement);
      }
      setWebglReady(false);
    };
  }, [sample]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!interactiveOrbit) return;
    const step = 0.14;
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      sphericalOffsetRef.current.theta -= step;
      onUserOrbit?.();
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      sphericalOffsetRef.current.theta += step;
      onUserOrbit?.();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      sphericalOffsetRef.current.phi = Math.max(-0.65, sphericalOffsetRef.current.phi - step * 0.7);
      onUserOrbit?.();
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      sphericalOffsetRef.current.phi = Math.min(0.65, sphericalOffsetRef.current.phi + step * 0.7);
      onUserOrbit?.();
    }
  };

  const activeSet = useMemo(() => new Set(activePoints), [activePoints]);
  const visibleSet = useMemo(
    () => new Set(visiblePoints ?? sample.points.map((p) => p.id)),
    [sample.points, visiblePoints],
  );

  return (
    <div
      id={sceneId}
      ref={shellRef}
      className={`axo-sp-scene-shell${interactiveOrbit ? " is-interactive" : ""}${compact ? " is-compact" : ""}`}
      role={interactiveOrbit ? "application" : "img"}
      aria-label={ariaLabel}
      tabIndex={interactiveOrbit ? 0 : undefined}
      onKeyDown={handleKeyDown}
    >
      <div className="axo-sp-scene-grid" aria-hidden="true" />
      <div ref={hostRef} className="axo-sp-scene-canvas-host" />

      {/* Geometrically faithful SVG fallback (rendered only before WebGL or when WebGL is unavailable) */}
      {!webglReady && (
        <svg
          className="axo-sp-scene-svg"
          viewBox={`0 0 ${svgFallback.w} ${svgFallback.h}`}
          preserveAspectRatio="xMidYMid meet"
          aria-hidden="true"
        >
          {/* Cutting plane (MNP) */}
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

          {/* Solid & dashed edges */}
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

          {/* Section fill */}
          {sectionFillOpacity > 0.02 && (
            <polygon
              points={svgFallback.sectionPts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")}
              fill="#d96b18"
              fillOpacity={(sectionFillOpacity * 0.24).toFixed(3)}
            />
          )}

          {/* Progressive section edges */}
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

          {/* Point markers */}
          {svgFallback.visibleList.map((pt) => (
            <circle
              key={`svg-dot-${pt.id}`}
              cx={pt.x}
              cy={pt.y}
              r={pt.role === "intersection" ? 5.2 : pt.role === "seed" ? 4.4 : 3.4}
              fill={
                pt.role === "intersection"
                  ? "#c2550a"
                  : pt.role === "seed"
                    ? "#0075de"
                    : "#1b1b19"
              }
            />
          ))}
        </svg>
      )}

      {/* Projected 2D point badges (synced cleanly by WebGL loop or computed SVG fallback) */}
      <div className="axo-sp-scene-labels" aria-hidden="true">
        {sample.points.map((pt) => {
          const fb = svgFallback.projPoints[pt.id];
          const vx = fb.x - svgFallback.cx;
          const vy = fb.y - svgFallback.cy;
          const len = Math.hypot(vx, vy) || 1;
          const push = pt.role === "base_center" ? 13 : 16;
          const pctX = ((fb.x + (vx / len) * push) / svgFallback.w) * 100;
          const pctY = ((fb.y + (vy / len) * push) / svgFallback.h) * 100;
          const isVisible = visibleSet.has(pt.id);
          const isActive = activeSet.has(pt.id);
          const roleClass =
            pt.role === "seed"
              ? " is-seed"
              : pt.role === "intersection"
                ? " is-intersection"
                : "";
          return (
            <span
              key={pt.id}
              ref={(el) => {
                labelRefs.current[pt.id] = el;
              }}
              className={`axo-sp-point-tag${roleClass}${isActive ? " is-active" : ""}`}
              style={
                webglReady
                  ? undefined
                  : {
                      left: `${pctX.toFixed(2)}%`,
                      top: `${pctY.toFixed(2)}%`,
                      opacity: isVisible ? 1 : 0,
                    }
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
