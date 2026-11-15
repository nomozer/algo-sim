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

const SLICE_NORMAL = new THREE.Vector3(-0.36, 0.84, 0.40).normalize();
const SLICE_OFFSET = 0.05;

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
  const baseFaces = buildChamferedCubeFaces(1.02, 1.28, 1.02, 1.58);
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

const ANALYTICAL_KEY_DIR = new THREE.Vector3(6.5, 10.5, 4.5).normalize();
const ANALYTICAL_RIM_DIR = new THREE.Vector3(-7, 3.8, 5).normalize();

function computeAnalyticalShade(normal: THREE.Vector3): number {
  const key = Math.max(0, normal.dot(ANALYTICAL_KEY_DIR)) * 0.22;
  const rim = Math.max(0, normal.dot(ANALYTICAL_RIM_DIR)) * 0.08;
  return Math.min(1.06, 0.78 + key + rim);
}

function buildPolyhedronGeometry(faces: readonly PolyFace[], baseColorHex = 0xf7f4ec): THREE.BufferGeometry {
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
      const shade = computeAnalyticalShade(triNormal);
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

function buildLoopPolygonGeometry(
  loop: readonly THREE.Vector3[],
  normalOffset = 0,
  reverseWinding = false,
  baseColorHex = 0xdd5b00,
): THREE.BufferGeometry {
  const positions: number[] = [];
  const colors: number[] = [];
  if (loop.length >= 3) {
    const baseColor = new THREE.Color(baseColorHex);
    const shade = computeAnalyticalShade(SLICE_NORMAL);
    const r = Math.min(1, baseColor.r * shade);
    const g = Math.min(1, baseColor.g * shade);
    const b = Math.min(1, baseColor.b * shade);
    const offsetVec = SLICE_NORMAL.clone().multiplyScalar(normalOffset);
    const pts = loop.map((p) => p.clone().add(offsetVec));
    const ordered = reverseWinding ? [...pts].reverse() : pts;
    const p0 = ordered[0];
    for (let i = 1; i < ordered.length - 1; i++) {
      const p1 = ordered[i];
      const p2 = ordered[i + 1];
      positions.push(p0.x, p0.y, p0.z, p1.x, p1.y, p1.z, p2.x, p2.y, p2.z);
      colors.push(r, g, b, r, g, b, r, g, b);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
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

    let cancelled = false;
    let cleanupInner: (() => void) | null = null;
    let mountTimer = 0;

    const mountWebGL = () => {
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
      const isMobileViewport = window.innerWidth <= 820;
      activeRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, isMobileViewport ? 1.25 : 1.5));
      activeRenderer.setClearColor(0x000000, 0);
      activeRenderer.outputColorSpace = THREE.SRGBColorSpace;
      host.appendChild(activeRenderer.domElement);

      const disposables: { dispose: () => void }[] = [];
      const track = <T extends { dispose: () => void }>(item: T): T => {
        disposables.push(item);
        return item;
      };

      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(34, 1.18, 0.1, 100);
      camera.position.set(4.95, 3.35, 5.45);
      camera.lookAt(0, 0.1, 0);

      const sculptureRoot = new THREE.Group();
      sculptureRoot.rotation.set(0.06, 0.54, -0.03);
      scene.add(sculptureRoot);

      // Tier 1: Lower solid mass — analytical studio-shaded alabaster (lightweight MeshBasicMaterial)
      const lowerGeo = track(buildPolyhedronGeometry(solidSpec.lowerFaces, 0xf7f4ec));
      const lowerMat = track(
        new THREE.MeshBasicMaterial({
          vertexColors: true,
        }),
      );
      const lowerMesh = new THREE.Mesh(lowerGeo, lowerMat);
      sculptureRoot.add(lowerMesh);

      const lowerEdgesGeo = track(new THREE.EdgesGeometry(lowerGeo, 24));
      const lowerEdgesMat = track(
        new THREE.LineBasicMaterial({ color: 0x1f1e1c, transparent: true, opacity: 0.58 }),
      );
      lowerMesh.add(new THREE.LineSegments(lowerEdgesGeo, lowerEdgesMat));

      // Tier 2: Exposed satin Axo amber cross-section on lower body
      const lowerCapGeo = track(buildLoopPolygonGeometry(solidSpec.sectionLoop, 0.003, false, 0xdd5b00));
      const lowerCapMat = track(
        new THREE.MeshBasicMaterial({
          vertexColors: true,
          side: THREE.DoubleSide,
        }),
      );
      const lowerCapMesh = new THREE.Mesh(lowerCapGeo, lowerCapMat);
      sculptureRoot.add(lowerCapMesh);

      // Crisp deep-amber perimeter contour
      const contourPts = [...solidSpec.sectionLoop, solidSpec.sectionLoop[0]].map((p) =>
        p.clone().addScaledVector(SLICE_NORMAL, 0.0055),
      );
      const contourGeo = track(new THREE.BufferGeometry().setFromPoints(contourPts));
      const contourMat = track(
        new THREE.LineBasicMaterial({ color: 0x9a3412, transparent: true, opacity: 0.96 }),
      );
      sculptureRoot.add(new THREE.Line(contourGeo, contourMat));

      // Tier 3: Frosted blue cutting plane
      const planeHolder = new THREE.Group();
      const planeCenter = solidSpec.sectionLoop
        .reduce((acc, v) => acc.add(v), new THREE.Vector3())
        .divideScalar(Math.max(1, solidSpec.sectionLoop.length));
      planeHolder.position.copy(planeCenter);
      planeHolder.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), SLICE_NORMAL);

      const roundedPlaneShape = createRoundedPlaneShape(3.55, 2.95, 0.24);
      const glassGeo = track(new THREE.ShapeGeometry(roundedPlaneShape, 12));
      const glassMat = track(
        new THREE.MeshBasicMaterial({
          color: 0xdcebfa,
          transparent: true,
          opacity: 0.26,
          side: THREE.DoubleSide,
          depthWrite: false,
        }),
      );
      const glassMesh = new THREE.Mesh(glassGeo, glassMat);
      glassMesh.renderOrder = 4;
      planeHolder.add(glassMesh);

      const glassEdgeGeo = track(new THREE.EdgesGeometry(glassGeo));
      const glassEdgeMat = track(
        new THREE.LineBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.86 }),
      );
      planeHolder.add(new THREE.LineSegments(glassEdgeGeo, glassEdgeMat));
      sculptureRoot.add(planeHolder);

      // Tier 4: Upper lifted clear-glass crystal cap (never obscures amber cut surface)
      const upperHolder = new THREE.Group();
      const upperGeo = track(buildPolyhedronGeometry(solidSpec.upperFaces, 0xeaf4ff));
      const upperMat = track(
        new THREE.MeshBasicMaterial({
          vertexColors: true,
          transparent: true,
          opacity: 0.24,
          side: THREE.FrontSide,
          depthWrite: false,
        }),
      );
      const upperMesh = new THREE.Mesh(upperGeo, upperMat);
      upperMesh.renderOrder = 3;
      upperHolder.add(upperMesh);

      const upperEdgesGeo = track(new THREE.EdgesGeometry(upperGeo, 24));
      const upperEdgesMat = track(
        new THREE.LineBasicMaterial({ color: 0x1e293b, transparent: true, opacity: 0.52 }),
      );
      upperMesh.add(new THREE.LineSegments(upperEdgesGeo, upperEdgesMat));

      const upperCapGeo = track(buildLoopPolygonGeometry(solidSpec.sectionLoop, -0.0025, true));
      const upperCapMat = track(
        new THREE.MeshBasicMaterial({
          color: 0xf59e0b,
          transparent: true,
          opacity: 0.16,
          side: THREE.DoubleSide,
          depthWrite: false,
        }),
      );
      const upperCapMesh = new THREE.Mesh(upperCapGeo, upperCapMat);
      upperCapMesh.renderOrder = 3;
      upperHolder.add(upperCapMesh);
      sculptureRoot.add(upperHolder);

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
      shadowMesh.position.set(0, -1.86, 0.1);
      scene.add(shadowMesh);

      // Render / animation state with demand-based sleeping
      let isDisposed = false;
      let isInView = true;
      let rafId = 0;
      let scrollPausedUntil = 0;
      let scrollResumeTimer = 0;

      let entranceT = reducedMotion ? 1 : 0;
      const entranceStartMs = typeof performance !== "undefined" ? performance.now() : Date.now();
      const entranceDurationMs = 650;

      let targetTiltX = 0;
      let targetTiltY = 0;
      let targetHoverBoost = 0;
      let curTiltX = 0;
      let curTiltY = 0;
      let curHoverBoost = 0;

      const baseRotX = 0.06;
      const baseRotY = 0.54;
      const baseSep = 0.52;

      const applyVisualState = (nowMs: number) => {
        if (!reducedMotion && entranceT < 1) {
          const linear = Math.max(0, Math.min(1, (nowMs - entranceStartMs) / entranceDurationMs));
          entranceT = 1 - Math.pow(1 - linear, 3);
        }
        const damp = reducedMotion ? 1 : 0.12;
        curTiltX += (targetTiltX - curTiltX) * damp;
        curTiltY += (targetTiltY - curTiltY) * damp;
        curHoverBoost += (targetHoverBoost - curHoverBoost) * damp;

        const sep = 0.20 + 0.34 * entranceT + curHoverBoost * 0.14;
        upperHolder.position.copy(SLICE_NORMAL).multiplyScalar(sep);
        planeHolder.position.copy(planeCenter).addScaledVector(SLICE_NORMAL, sep * 0.48);

        sculptureRoot.rotation.set(
          baseRotX + curTiltX,
          baseRotY + curTiltY - (1 - entranceT) * 0.22,
          -0.03,
        );
        sculptureRoot.position.y = -0.06 * (1 - entranceT) + curHoverBoost * 0.03;

        activeRenderer.render(scene, camera);

        return (
          entranceT >= 0.999 &&
          Math.abs(targetTiltX - curTiltX) < 0.0005 &&
          Math.abs(targetTiltY - curTiltY) < 0.0005 &&
          Math.abs(targetHoverBoost - curHoverBoost) < 0.0005
        );
      };

      let wakeRender: () => void = () => {};

      const renderFrame = (nowMs: number) => {
        if (isDisposed) return;
        if (!isInView || document.hidden) {
          rafId = 0;
          return;
        }
        if (nowMs < scrollPausedUntil) {
          rafId = 0;
          if (!scrollResumeTimer) {
            scrollResumeTimer = window.setTimeout(() => {
              scrollResumeTimer = 0;
              wakeRender();
            }, 130);
          }
          return;
        }
        const settled = applyVisualState(nowMs);
        if (!settled && !reducedMotion) {
          rafId = window.requestAnimationFrame(renderFrame);
        } else {
          rafId = 0;
        }
      };

      wakeRender = () => {
        if (isDisposed || !isInView || document.hidden) return;
        if (reducedMotion) {
          applyVisualState(0);
          return;
        }
        const now = typeof performance !== "undefined" ? performance.now() : Date.now();
        if (now < scrollPausedUntil) {
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

      setWebglReady(true);
      applyVisualState(entranceStartMs);
      if (!reducedMotion && baseSep > 0) {
        wakeRender();
      }

      cleanupInner = () => {
        isDisposed = true;
        if (rafId !== 0) window.cancelAnimationFrame(rafId);
        if (scrollResumeTimer) window.clearTimeout(scrollResumeTimer);
        ro?.disconnect();
        io?.disconnect();
        shell.removeEventListener("pointermove", onPointerMove);
        shell.removeEventListener("pointerleave", onPointerLeave);
        window.removeEventListener("scroll", onWindowScroll);
        document.removeEventListener("visibilitychange", onVisibilityChange);
        activeRenderer.domElement.removeEventListener("webglcontextlost", onContextLost);
        for (const d of disposables) d.dispose();
        activeRenderer.dispose();
        if (activeRenderer.domElement.parentNode === host) {
          host.removeChild(activeRenderer.domElement);
        }
        setWebglReady(false);
      };
    };

    const mountRaf =
      typeof window.requestAnimationFrame === "function"
        ? window.requestAnimationFrame(mountWebGL)
        : 0;
    if (mountRaf === 0) {
      mountTimer = window.setTimeout(mountWebGL, 0);
    }

    return () => {
      cancelled = true;
      if (mountRaf !== 0 && typeof window.cancelAnimationFrame === "function") {
        window.cancelAnimationFrame(mountRaf);
      }
      if (mountTimer !== 0) {
        window.clearTimeout(mountTimer);
      }
      cleanupInner?.();
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
      <div
        ref={hostRef}
        className="axo-sp-hero-sculpture-canvas"
        style={{ visibility: webglReady ? "visible" : "hidden" }}
      />

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
              <stop offset="0%" stopColor="#fb923c" />
              <stop offset="100%" stopColor="#dd5b00" />
            </linearGradient>
            <linearGradient id={`${svgGradBase}-stone`} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#faf7f0" />
              <stop offset="100%" stopColor="#ebe5d8" />
            </linearGradient>
          </defs>

          <ellipse cx="280" cy="402" rx="164" ry="28" fill={`url(#${svgGradBase}-shadow)`} />

          {/* Lower beveled monolith */}
          <polygon
            points="168,246 258,200 390,240 374,354 270,384 176,342"
            fill={`url(#${svgGradBase}-stone)`}
            stroke="rgba(31, 30, 28, 0.45)"
            strokeWidth="1.6"
          />
          <polygon
            points="182,246 262,210 374,242 292,284"
            fill={`url(#${svgGradBase}-amber)`}
            stroke="#9a3412"
            strokeWidth="1.6"
          />

          {/* Frosted Primary Blue cutting plane */}
          <polygon
            points="126,220 274,154 434,204 284,280"
            fill="rgba(220, 235, 250, 0.34)"
            stroke="#0075de"
            strokeOpacity="0.8"
            strokeWidth="1.5"
          />

          {/* Clear-glass upper cap revealing amber section below */}
          <polygon
            points="190,152 268,78 368,128 360,192 276,222 194,190"
            fill="rgba(234, 244, 255, 0.34)"
            stroke="rgba(30, 41, 59, 0.54)"
            strokeWidth="1.5"
          />
          <polygon
            points="194,190 276,222 360,192 280,162"
            fill="rgba(245, 158, 11, 0.16)"
          />
        </svg>
      )}
    </div>
  );
}
