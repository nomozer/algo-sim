import { useEffect, useId, useMemo, useRef, useState } from "react";
import * as THREE from "three";

interface PolyFace {
  readonly pts: THREE.Vector3[];
}

interface ClippedSolid {
  readonly lowerFaces: PolyFace[];
  readonly upperFaces: PolyFace[];
  readonly sectionLoop: THREE.Vector3[];
}

const SLICE_NORMAL = new THREE.Vector3(-0.38, 0.84, 0.38).normalize();
const SLICE_OFFSET = 0.04;

/**
 * Exact Sutherland-Hodgman polygon clip against half-space `n · p <= d`.
 * Keeps cap polygons and seam vertices watertight with zero mesh boolean gaps.
 */
function clipPolygonHalfSpace(
  poly: readonly THREE.Vector3[],
  normal: THREE.Vector3,
  offset: number,
  keepPositive: boolean,
): THREE.Vector3[] {
  if (poly.length < 3) return [];
  const sign = keepPositive ? -1 : 1;
  const distOf = (p: THREE.Vector3) => (p.dot(normal) - offset) * sign;
  const eps = 1e-5;
  const out: THREE.Vector3[] = [];

  for (let i = 0; i < poly.length; i++) {
    const a = poly[i];
    const b = poly[(i + 1) % poly.length];
    const da = distOf(a);
    const db = distOf(b);
    const aInside = da <= eps;
    const bInside = db <= eps;

    if (aInside && bInside) {
      out.push(b.clone());
    } else if (aInside && !bInside) {
      const denom = da - db;
      const t = Math.abs(denom) > 1e-8 ? da / denom : 0;
      out.push(a.clone().lerp(b, Math.max(0, Math.min(1, t))));
    } else if (!aInside && bInside) {
      const denom = da - db;
      const t = Math.abs(denom) > 1e-8 ? da / denom : 0;
      out.push(a.clone().lerp(b, Math.max(0, Math.min(1, t))));
      out.push(b.clone());
    }
  }

  // Deduplicate sequential coincident vertices
  const compact: THREE.Vector3[] = [];
  for (const v of out) {
    if (compact.length === 0 || compact[compact.length - 1].distanceToSquared(v) > 1e-8) {
      compact.push(v);
    }
  }
  if (compact.length > 1 && compact[0].distanceToSquared(compact[compact.length - 1]) <= 1e-8) {
    compact.pop();
  }
  return compact.length >= 3 ? compact : [];
}

function buildChamferedCubeFaces(hx: number, hy: number, hz: number, chamfer: number): PolyFace[] {
  // Start with a clean rectangular prism and clip all 8 octahedral corners symmetrically
  let faces: PolyFace[] = [
    { pts: [new THREE.Vector3(hx, -hy, -hz), new THREE.Vector3(hx, hy, -hz), new THREE.Vector3(hx, hy, hz), new THREE.Vector3(hx, -hy, hz)] },
    { pts: [new THREE.Vector3(-hx, -hy, hz), new THREE.Vector3(-hx, hy, hz), new THREE.Vector3(-hx, hy, -hz), new THREE.Vector3(-hx, -hy, -hz)] },
    { pts: [new THREE.Vector3(-hx, hy, -hz), new THREE.Vector3(-hx, hy, hz), new THREE.Vector3(hx, hy, hz), new THREE.Vector3(hx, hy, -hz)] },
    { pts: [new THREE.Vector3(-hx, -hy, hz), new THREE.Vector3(-hx, -hy, -hz), new THREE.Vector3(hx, -hy, -hz), new THREE.Vector3(hx, -hy, hz)] },
    { pts: [new THREE.Vector3(-hx, -hy, hz), new THREE.Vector3(hx, -hy, hz), new THREE.Vector3(hx, hy, hz), new THREE.Vector3(-hx, hy, hz)] },
    { pts: [new THREE.Vector3(hx, -hy, -hz), new THREE.Vector3(-hx, -hy, -hz), new THREE.Vector3(-hx, hy, -hz), new THREE.Vector3(hx, hy, -hz)] },
  ];

  const corners: [number, number, number][] = [
    [1, 1, 1],
    [1, 1, -1],
    [1, -1, 1],
    [1, -1, -1],
    [-1, 1, 1],
    [-1, 1, -1],
    [-1, -1, 1],
    [-1, -1, -1],
  ];

  for (const [sx, sy, sz] of corners) {
    const cNormal = new THREE.Vector3(sx, sy, sz).normalize();
    const cOffset = chamfer;
    const capPts: THREE.Vector3[] = [];
    const nextFaces: PolyFace[] = [];

    for (const face of faces) {
      const clipped = clipPolygonHalfSpace(face.pts, cNormal, cOffset, false);
      if (clipped.length >= 3) {
        nextFaces.push({ pts: clipped });
        for (const p of clipped) {
          if (Math.abs(p.dot(cNormal) - cOffset) < 1e-3) {
            if (!capPts.some((q) => q.distanceToSquared(p) < 1e-6)) {
              capPts.push(p.clone());
            }
          }
        }
      }
    }

    if (capPts.length >= 3) {
      const center = capPts.reduce((acc, v) => acc.add(v), new THREE.Vector3()).divideScalar(capPts.length);
      const ref = Math.abs(cNormal.y) < 0.9 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0);
      const u = new THREE.Vector3().crossVectors(ref, cNormal).normalize();
      const v = new THREE.Vector3().crossVectors(cNormal, u).normalize();
      capPts.sort((a, b) => {
        const da = a.clone().sub(center);
        const db = b.clone().sub(center);
        return Math.atan2(da.dot(v), da.dot(u)) - Math.atan2(db.dot(v), db.dot(u));
      });
      nextFaces.push({ pts: capPts });
    }
    faces = nextFaces;
  }

  return faces;
}

function buildSlicedSculpture(): ClippedSolid {
  const baseFaces = buildChamferedCubeFaces(1.06, 1.16, 1.06, 1.54);
  const lowerFaces: PolyFace[] = [];
  const upperFaces: PolyFace[] = [];
  const seamPts: THREE.Vector3[] = [];

  for (const face of baseFaces) {
    const lo = clipPolygonHalfSpace(face.pts, SLICE_NORMAL, SLICE_OFFSET, false);
    if (lo.length >= 3) lowerFaces.push({ pts: lo });

    const hi = clipPolygonHalfSpace(face.pts, SLICE_NORMAL, SLICE_OFFSET, true);
    if (hi.length >= 3) upperFaces.push({ pts: hi });

    for (const pt of [...lo, ...hi]) {
      if (Math.abs(pt.dot(SLICE_NORMAL) - SLICE_OFFSET) < 1.5e-3) {
        if (!seamPts.some((existing) => existing.distanceToSquared(pt) < 1e-6)) {
          seamPts.push(pt.clone());
        }
      }
    }
  }

  const center = seamPts.reduce((acc, v) => acc.add(v), new THREE.Vector3()).divideScalar(Math.max(1, seamPts.length));
  const ref = Math.abs(SLICE_NORMAL.y) < 0.9 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0);
  const u = new THREE.Vector3().crossVectors(ref, SLICE_NORMAL).normalize();
  const v = new THREE.Vector3().crossVectors(SLICE_NORMAL, u).normalize();

  seamPts.sort((a, b) => {
    const da = a.clone().sub(center);
    const db = b.clone().sub(center);
    return Math.atan2(da.dot(v), da.dot(u)) - Math.atan2(db.dot(v), db.dot(u));
  });

  return { lowerFaces, upperFaces, sectionLoop: seamPts };
}

function buildPolyhedronGeometry(faces: readonly PolyFace[]): THREE.BufferGeometry {
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

function buildLoopPolygonGeometry(loop: readonly THREE.Vector3[], normalOffset = 0, reverseWinding = false): THREE.BufferGeometry {
  const positions: number[] = [];
  if (loop.length >= 3) {
    const offsetVec = SLICE_NORMAL.clone().multiplyScalar(normalOffset);
    const pts = loop.map((p) => p.clone().add(offsetVec));
    const ordered = reverseWinding ? [...pts].reverse() : pts;
    const p0 = ordered[0];
    for (let i = 1; i < ordered.length - 1; i++) {
      const p1 = ordered[i];
      const p2 = ordered[i + 1];
      positions.push(p0.x, p0.y, p0.z, p1.x, p1.y, p1.z, p2.x, p2.y, p2.z);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.computeVertexNormals();
  return geo;
}

function createRoundedPlaneShape(width: number, height: number, radius: number): THREE.Shape {
  const s = new THREE.Shape();
  const hw = width / 2;
  const hh = height / 2;
  const r = Math.min(radius, hw, hh);
  s.moveTo(-hw + r, -hh);
  s.lineTo(hw - r, -hh);
  s.quadraticCurveTo(hw, -hh, hw, -hh + r);
  s.lineTo(hw, hh - r);
  s.quadraticCurveTo(hw, hh, hw - r, hh);
  s.lineTo(-hw + r, hh);
  s.quadraticCurveTo(-hw, hh, -hw, hh - r);
  s.lineTo(-hw, -hh + r);
  s.quadraticCurveTo(-hw, -hh, -hw + r, -hh);
  return s;
}

function createRadialShadowTexture(): THREE.CanvasTexture | null {
  if (typeof document === "undefined") return null;
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  const grad = ctx.createRadialGradient(128, 128, 12, 128, 128, 124);
  grad.addColorStop(0, "rgba(24, 24, 21, 0.20)");
  grad.addColorStop(0.45, "rgba(24, 24, 21, 0.08)");
  grad.addColorStop(1, "rgba(24, 24, 21, 0)");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 256, 256);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

/**
 * Frameless studio-lit brand sculpture for the Hero section.
 * Distinct from the technical coordinate canvases used in Storytelling & Demo:
 * carries zero card frame, zero vertex proof tags (A, B, C, S, M), and
 * sleeps WebGL RAF whenever settled, off-screen, or tab-hidden.
 */
export function LandingHeroSculpture3D() {
  const shellRef = useRef<HTMLDivElement | null>(null);
  const hostRef = useRef<HTMLDivElement | null>(null);
  const [webglReady, setWebglReady] = useState(false);
  const svgGradBase = useId().replace(/:/g, "");

  const solidSpec = useMemo(() => buildSlicedSculpture(), []);

  useEffect(() => {
    const shell = shellRef.current;
    const host = hostRef.current;
    if (!shell || !host || typeof window === "undefined") return;

    const reducedMotion =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

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
    const isMobileViewport = window.innerWidth <= 820;
    activeRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, isMobileViewport ? 1.5 : 2));
    activeRenderer.setClearColor(0x000000, 0);
    activeRenderer.outputColorSpace = THREE.SRGBColorSpace;
    activeRenderer.toneMapping = THREE.ACESFilmicToneMapping;
    activeRenderer.toneMappingExposure = 1.06;
    host.appendChild(activeRenderer.domElement);

    const disposables: { dispose: () => void }[] = [];
    const track = <T extends { dispose: () => void }>(item: T): T => {
      disposables.push(item);
      return item;
    };

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(34, 1.18, 0.1, 100);
    camera.position.set(4.85, 3.3, 5.35);
    camera.lookAt(0, 0.12, 0);

    // Warm studio light rig
    scene.add(new THREE.AmbientLight(0xfdfaf4, 1.2));
    const hemi = new THREE.HemisphereLight(0xffffff, 0xdad4c8, 0.68);
    scene.add(hemi);
    const keyLight = new THREE.DirectionalLight(0xfff9f0, 1.92);
    keyLight.position.set(7, 10, 4);
    scene.add(keyLight);
    const rimLight = new THREE.DirectionalLight(0xdbeafe, 0.96);
    rimLight.position.set(-7, 3.5, 5);
    scene.add(rimLight);
    const warmBounce = new THREE.DirectionalLight(0xfef3c7, 0.48);
    warmBounce.position.set(2, -4, 4);
    scene.add(warmBounce);

    const sculptureRoot = new THREE.Group();
    sculptureRoot.rotation.set(0.06, 0.54, -0.03);
    scene.add(sculptureRoot);

    // Lower solid mass — warm matte alabaster
    const lowerGeo = track(buildPolyhedronGeometry(solidSpec.lowerFaces));
    const lowerMat = track(
      new THREE.MeshPhysicalMaterial({
        color: 0xf5f0e6,
        roughness: 0.44,
        metalness: 0.02,
        clearcoat: 0.18,
        clearcoatRoughness: 0.48,
        flatShading: true,
      }),
    );
    const lowerMesh = new THREE.Mesh(lowerGeo, lowerMat);
    sculptureRoot.add(lowerMesh);

    const lowerEdgesGeo = track(new THREE.EdgesGeometry(lowerGeo, 24));
    const lowerEdgesMat = track(
      new THREE.LineBasicMaterial({ color: 0x262933, transparent: true, opacity: 0.36 }),
    );
    lowerMesh.add(new THREE.LineSegments(lowerEdgesGeo, lowerEdgesMat));

    // Exposed satin Axo amber cross-section on lower body
    const lowerCapGeo = track(buildLoopPolygonGeometry(solidSpec.sectionLoop, 0.0025, false));
    const lowerCapMat = track(
      new THREE.MeshPhysicalMaterial({
        color: 0xe07a16,
        roughness: 0.28,
        metalness: 0.04,
        clearcoat: 0.35,
        side: THREE.DoubleSide,
      }),
    );
    const lowerCapMesh = new THREE.Mesh(lowerCapGeo, lowerCapMat);
    sculptureRoot.add(lowerCapMesh);

    // Crisp intersection contour around section
    const contourPts = [...solidSpec.sectionLoop, solidSpec.sectionLoop[0]].map((p) =>
      p.clone().addScaledVector(SLICE_NORMAL, 0.005),
    );
    const contourGeo = track(new THREE.BufferGeometry().setFromPoints(contourPts));
    const contourMat = track(
      new THREE.LineBasicMaterial({ color: 0xb45309, transparent: true, opacity: 0.92 }),
    );
    sculptureRoot.add(new THREE.Line(contourGeo, contourMat));

    // Translucent frosted slicing plane hovering inside the cut gap
    const planeHolder = new THREE.Group();
    const planeCenter = solidSpec.sectionLoop
      .reduce((acc, v) => acc.add(v), new THREE.Vector3())
      .divideScalar(Math.max(1, solidSpec.sectionLoop.length));
    planeHolder.position.copy(planeCenter);
    planeHolder.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), SLICE_NORMAL);

    const roundedPlaneShape = createRoundedPlaneShape(3.45, 2.85, 0.24);
    const glassGeo = track(new THREE.ShapeGeometry(roundedPlaneShape, 12));
    const glassMat = track(
      new THREE.MeshPhysicalMaterial({
        color: 0xdceafb,
        transparent: true,
        opacity: 0.35,
        roughness: 0.18,
        metalness: 0.0,
        clearcoat: 0.72,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const glassMesh = new THREE.Mesh(glassGeo, glassMat);
    glassMesh.renderOrder = 4;
    planeHolder.add(glassMesh);

    const glassEdgeGeo = track(new THREE.EdgesGeometry(glassGeo));
    const glassEdgeMat = track(
      new THREE.LineBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.62 }),
    );
    planeHolder.add(new THREE.LineSegments(glassEdgeGeo, glassEdgeMat));
    sculptureRoot.add(planeHolder);

    // Upper lifted frosted crystal cap
    const upperHolder = new THREE.Group();
    const upperGeo = track(buildPolyhedronGeometry(solidSpec.upperFaces));
    const upperMat = track(
      new THREE.MeshPhysicalMaterial({
        color: 0xeef5fc,
        transparent: true,
        opacity: 0.82,
        roughness: 0.22,
        metalness: 0.0,
        clearcoat: 0.65,
        clearcoatRoughness: 0.16,
        flatShading: true,
      }),
    );
    const upperMesh = new THREE.Mesh(upperGeo, upperMat);
    upperMesh.renderOrder = 3;
    upperHolder.add(upperMesh);

    const upperEdgesGeo = track(new THREE.EdgesGeometry(upperGeo, 24));
    const upperEdgesMat = track(
      new THREE.LineBasicMaterial({ color: 0x1e293b, transparent: true, opacity: 0.36 }),
    );
    upperMesh.add(new THREE.LineSegments(upperEdgesGeo, upperEdgesMat));

    const upperCapGeo = track(buildLoopPolygonGeometry(solidSpec.sectionLoop, -0.0025, true));
    const upperCapMat = track(
      new THREE.MeshPhysicalMaterial({
        color: 0xf59e0b,
        transparent: true,
        opacity: 0.78,
        roughness: 0.24,
        side: THREE.DoubleSide,
      }),
    );
    const upperCapMesh = new THREE.Mesh(upperCapGeo, upperCapMat);
    upperCapMesh.renderOrder = 3;
    upperHolder.add(upperCapMesh);
    sculptureRoot.add(upperHolder);

    // Companion 1: Porcelain sphere + crisp brushed-blue orbital ring in left negative space
    const sphereCompanionGroup = new THREE.Group();
    sphereCompanionGroup.position.set(-1.92, 0.74, 0.52);
    const sphereGeo = track(new THREE.SphereGeometry(0.28, 32, 24));
    const sphereMat = track(
      new THREE.MeshPhysicalMaterial({
        color: 0xfcfbf7,
        roughness: 0.28,
        clearcoat: 0.45,
      }),
    );
    sphereCompanionGroup.add(new THREE.Mesh(sphereGeo, sphereMat));

    const torusGeo = track(new THREE.TorusGeometry(0.42, 0.022, 16, 56));
    const torusMat = track(
      new THREE.MeshPhysicalMaterial({
        color: 0x0075de,
        roughness: 0.32,
        metalness: 0.12,
      }),
    );
    const torusMesh = new THREE.Mesh(torusGeo, torusMat);
    torusMesh.rotation.set(1.12, 0.42, 0.18);
    sphereCompanionGroup.add(torusMesh);
    sculptureRoot.add(sphereCompanionGroup);

    // Companion 2: Small warm crystal octahedron in upper-right negative space
    const octGeo = track(new THREE.OctahedronGeometry(0.25, 0));
    const octMat = track(
      new THREE.MeshPhysicalMaterial({
        color: 0xfef3c7,
        roughness: 0.26,
        clearcoat: 0.4,
      }),
    );
    const octMesh = new THREE.Mesh(octGeo, octMat);
    octMesh.position.set(1.84, 0.86, -0.24);
    octMesh.rotation.set(0.32, 0.65, 0.22);
    const octEdgesGeo = track(new THREE.EdgesGeometry(octGeo));
    const octEdgesMat = track(
      new THREE.LineBasicMaterial({ color: 0xb45309, transparent: true, opacity: 0.38 }),
    );
    octMesh.add(new THREE.LineSegments(octEdgesGeo, octEdgesMat));
    sculptureRoot.add(octMesh);

    // Ground soft contact shadow beneath floating sculpture
    const shadowTex = createRadialShadowTexture();
    if (shadowTex) track(shadowTex);
    const shadowGeo = track(new THREE.PlaneGeometry(4.4, 3.6));
    shadowGeo.rotateX(-Math.PI / 2);
    const shadowMat = track(
      new THREE.MeshBasicMaterial({
        map: shadowTex ?? undefined,
        color: shadowTex ? 0xffffff : 0x111110,
        transparent: true,
        opacity: shadowTex ? 0.92 : 0.08,
        depthWrite: false,
      }),
    );
    const shadowMesh = new THREE.Mesh(shadowGeo, shadowMat);
    shadowMesh.position.set(0, -1.78, 0.1);
    scene.add(shadowMesh);

    // Render / animation state with demand-based sleeping
    let isDisposed = false;
    let isInView = true;
    let rafId = 0;

    let entranceT = reducedMotion ? 1 : 0;
    const entranceStartMs = typeof performance !== "undefined" ? performance.now() : Date.now();
    const entranceDurationMs = 1350;

    let targetTiltX = 0;
    let targetTiltY = 0;
    let targetHoverBoost = 0;
    let curTiltX = 0;
    let curTiltY = 0;
    let curHoverBoost = 0;

    const baseRotX = 0.06;
    const baseRotY = 0.54;
    const baseSep = 0.50;

    const applyVisualState = (nowMs: number) => {
      if (!reducedMotion && entranceT < 1) {
        const linear = Math.max(0, Math.min(1, (nowMs - entranceStartMs) / entranceDurationMs));
        entranceT = 1 - Math.pow(1 - linear, 3);
      }
      const damp = reducedMotion ? 1 : 0.12;
      curTiltX += (targetTiltX - curTiltX) * damp;
      curTiltY += (targetTiltY - curTiltY) * damp;
      curHoverBoost += (targetHoverBoost - curHoverBoost) * damp;

      const sep = (0.18 + 0.32 * entranceT) + curHoverBoost * 0.14;
      upperHolder.position.copy(SLICE_NORMAL).multiplyScalar(sep);
      planeHolder.position.copy(planeCenter).addScaledVector(SLICE_NORMAL, sep * 0.48);

      sculptureRoot.rotation.set(
        baseRotX + curTiltX,
        baseRotY + curTiltY - (1 - entranceT) * 0.22,
        -0.03,
      );
      sculptureRoot.position.y = -0.06 * (1 - entranceT) + curHoverBoost * 0.03;

      sphereCompanionGroup.position.set(
        -1.92 - curHoverBoost * 0.08,
        0.74 + curHoverBoost * 0.1 + entranceT * 0.04,
        0.52,
      );
      octMesh.position.set(
        1.84 + curHoverBoost * 0.08,
        0.86 - curHoverBoost * 0.04,
        -0.24,
      );
      octMesh.rotation.y = 0.65 + curTiltY * 0.8 + entranceT * 0.25;

      activeRenderer.render(scene, camera);

      const settled =
        entranceT >= 0.999 &&
        Math.abs(targetTiltX - curTiltX) < 0.0005 &&
        Math.abs(targetTiltY - curTiltY) < 0.0005 &&
        Math.abs(targetHoverBoost - curHoverBoost) < 0.0005;

      return settled;
    };

    const renderFrame = (nowMs: number) => {
      if (isDisposed) return;
      if (!isInView || document.hidden) {
        rafId = 0;
        return;
      }
      const settled = applyVisualState(nowMs);
      if (!settled && !reducedMotion) {
        rafId = window.requestAnimationFrame(renderFrame);
      } else {
        rafId = 0;
      }
    };

    const wakeRender = () => {
      if (isDisposed || !isInView || document.hidden) return;
      if (reducedMotion) {
        applyVisualState(0);
        return;
      }
      if (rafId === 0) {
        rafId = window.requestAnimationFrame(renderFrame);
      }
    };

    const syncSize = () => {
      const rect = shell.getBoundingClientRect();
      const width = Math.max(180, Math.floor(rect.width));
      const height = Math.max(180, Math.floor(rect.height));
      activeRenderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      wakeRender();
    };

    syncSize();

    const onPointerMove = (e: PointerEvent) => {
      if (reducedMotion) return;
      const rect = shell.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) return;
      const nx = (e.clientX - rect.left) / rect.width - 0.5;
      const ny = (e.clientY - rect.top) / rect.height - 0.5;
      targetTiltY = nx * 0.28;
      targetTiltX = -ny * 0.16;
      targetHoverBoost = 1;
      wakeRender();
    };

    const onPointerLeave = () => {
      targetTiltX = 0;
      targetTiltY = 0;
      targetHoverBoost = 0;
      wakeRender();
    };

    shell.addEventListener("pointermove", onPointerMove);
    shell.addEventListener("pointerleave", onPointerLeave);

    const ro =
      typeof ResizeObserver !== "undefined"
        ? new ResizeObserver(() => {
            syncSize();
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

    setWebglReady(true);
    // Guarantee an immediate crisp initial paint including static fallback elimination
    applyVisualState(entranceStartMs);
    if (!reducedMotion && baseSep > 0) {
      wakeRender();
    }

    return () => {
      isDisposed = true;
      if (rafId !== 0) window.cancelAnimationFrame(rafId);
      ro?.disconnect();
      io?.disconnect();
      shell.removeEventListener("pointermove", onPointerMove);
      shell.removeEventListener("pointerleave", onPointerLeave);
      document.removeEventListener("visibilitychange", onVisibilityChange);
      activeRenderer.domElement.removeEventListener("webglcontextlost", onContextLost);
      for (const d of disposables) d.dispose();
      activeRenderer.dispose();
      if (activeRenderer.domElement.parentNode === host) {
        host.removeChild(activeRenderer.domElement);
      }
      setWebglReady(false);
    };
  }, [solidSpec]);

  return (
    <div
      id="landing-hero-sculpture"
      ref={shellRef}
      className="axo-sp-hero-sculpture"
      role="img"
      aria-label="Điêu khắc hình học không gian Axo — khối đa diện tách lớp theo mặt phẳng cắt"
    >
      <div className="axo-sp-hero-sculpture-glow" aria-hidden="true" />
      <div ref={hostRef} className="axo-sp-hero-sculpture-canvas" />

      {!webglReady && (
        <svg
          className="axo-sp-hero-sculpture-fallback"
          viewBox="0 0 560 460"
          role="presentation"
          aria-hidden="true"
        >
          <defs>
            <radialGradient id={`${svgGradBase}-shadow`} cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="rgba(24, 24, 21, 0.16)" />
              <stop offset="55%" stopColor="rgba(24, 24, 21, 0.06)" />
              <stop offset="100%" stopColor="rgba(24, 24, 21, 0)" />
            </radialGradient>
            <linearGradient id={`${svgGradBase}-amber`} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f59e0b" />
              <stop offset="100%" stopColor="#d97706" />
            </linearGradient>
            <linearGradient id={`${svgGradBase}-stone`} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#faf7f0" />
              <stop offset="100%" stopColor="#e8e2d5" />
            </linearGradient>
          </defs>

          <ellipse cx="282" cy="396" rx="168" ry="30" fill={`url(#${svgGradBase}-shadow)`} />

          {/* Lower chamfered mass */}
          <polygon
            points="166,248 258,204 388,244 374,342 272,374 174,332"
            fill={`url(#${svgGradBase}-stone)`}
            stroke="rgba(38, 41, 51, 0.34)"
            strokeWidth="1.6"
          />
          <polygon
            points="182,248 262,212 372,244 294,284"
            fill={`url(#${svgGradBase}-amber)`}
            stroke="#b45309"
            strokeWidth="1.6"
          />

          {/* Frosted cutting plane */}
          <polygon
            points="126,222 272,158 434,208 286,282"
            fill="rgba(220, 234, 251, 0.42)"
            stroke="rgba(37, 99, 235, 0.55)"
            strokeWidth="1.5"
          />

          {/* Separated translucent cap */}
          <polygon
            points="194,166 266,94 362,140 356,192 276,222 198,194"
            fill="rgba(244, 248, 254, 0.86)"
            stroke="rgba(30, 41, 59, 0.38)"
            strokeWidth="1.5"
          />
          <polygon
            points="198,194 276,222 356,192 282,164"
            fill="rgba(245, 158, 11, 0.55)"
          />

          {/* Porcelain sphere + orbital ring */}
          <circle cx="118" cy="144" r="24" fill="#fcfbf7" stroke="rgba(17, 17, 16, 0.16)" strokeWidth="1.2" />
          <ellipse
            cx="118"
            cy="144"
            rx="42"
            ry="13"
            transform="rotate(-24 118 144)"
            fill="none"
            stroke="#0075de"
            strokeWidth="2.4"
          />

          {/* Warm octahedron */}
          <polygon
            points="436,276 462,306 436,336 410,306"
            fill="#fef3c7"
            stroke="rgba(180, 83, 9, 0.45)"
            strokeWidth="1.4"
          />
        </svg>
      )}
    </div>
  );
}
