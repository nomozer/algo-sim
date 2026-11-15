import { useEffect, useId, useMemo, useRef, useState } from "react";
import * as THREE from "three";

export type HeroIllustrationVariant = "transformation" | "sculpture";

interface PolyFace {
  readonly pts: THREE.Vector3[];
}

interface ClippedSolid {
  readonly lowerFaces: PolyFace[];
  readonly upperFaces: PolyFace[];
  readonly sectionLoop: THREE.Vector3[];
  readonly axisSegments: readonly [THREE.Vector3, THREE.Vector3][];
}

// Geometric Transformation oblique plane slicing a 5-vertex pentagonal cross-section
const TRANSFORMATION_NORMAL = new THREE.Vector3(-0.30, 0.86, 0.41).normalize();
const TRANSFORMATION_OFFSET = -0.22;

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
  const out: THREE.Vector3[] = [];
  const eps = 1e-6;
  const side = (v: THREE.Vector3) => {
    const signed = v.dot(normal) - offset;
    return keepPositive ? signed : -signed;
  };

  for (let i = 0; i < poly.length; i++) {
    const curr = poly[i];
    const next = poly[(i + 1) % poly.length];
    const dc = side(curr);
    const dn = side(next);
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

function buildArchitecturalPyramidFaces(): PolyFace[] {
  // Architectural tilted square pyramid — crisp proportions, recognizable silhouette without letter labels
  const s = new THREE.Vector3(0.06, 1.72, -0.08);
  const a = new THREE.Vector3(-1.42, -1.16, 1.38);
  const b = new THREE.Vector3(1.42, -1.16, 1.38);
  const c = new THREE.Vector3(1.42, -1.16, -1.38);
  const d = new THREE.Vector3(-1.42, -1.16, -1.38);

  return [
    { pts: [d.clone(), c.clone(), b.clone(), a.clone()] }, // base (outward normal -Y)
    { pts: [a.clone(), b.clone(), s.clone()] },
    { pts: [b.clone(), c.clone(), s.clone()] },
    { pts: [c.clone(), d.clone(), s.clone()] },
    { pts: [d.clone(), a.clone(), s.clone()] },
  ];
}

function buildTransformationSolid(): ClippedSolid {
  const baseFaces = buildArchitecturalPyramidFaces();
  const lowerFaces: PolyFace[] = [];
  const upperFaces: PolyFace[] = [];
  const seamPts: THREE.Vector3[] = [];

  for (const face of baseFaces) {
    const lo = clipPolygonHalfSpace(face.pts, TRANSFORMATION_NORMAL, TRANSFORMATION_OFFSET, false);
    if (lo.length >= 3) lowerFaces.push({ pts: lo });

    const hi = clipPolygonHalfSpace(face.pts, TRANSFORMATION_NORMAL, TRANSFORMATION_OFFSET, true);
    if (hi.length >= 3) upperFaces.push({ pts: hi });

    for (const pt of [...lo, ...hi]) {
      if (Math.abs(pt.dot(TRANSFORMATION_NORMAL) - TRANSFORMATION_OFFSET) < 1.5e-3) {
        if (!seamPts.some((existing) => existing.distanceToSquared(pt) < 1e-6)) {
          seamPts.push(pt.clone());
        }
      }
    }
  }

  const center = seamPts
    .reduce((acc, v) => acc.add(v), new THREE.Vector3())
    .divideScalar(Math.max(1, seamPts.length));
  const ref =
    Math.abs(TRANSFORMATION_NORMAL.y) < 0.9
      ? new THREE.Vector3(0, 1, 0)
      : new THREE.Vector3(1, 0, 0);
  const u = new THREE.Vector3().crossVectors(ref, TRANSFORMATION_NORMAL).normalize();
  const v = new THREE.Vector3().crossVectors(TRANSFORMATION_NORMAL, u).normalize();

  seamPts.sort((a, b) => {
    const da = a.clone().sub(center);
    const db = b.clone().sub(center);
    return Math.atan2(da.dot(v), da.dot(u)) - Math.atan2(db.dot(v), db.dot(u));
  });

  const axisSegments: [THREE.Vector3, THREE.Vector3][] = [
    [new THREE.Vector3(0.06, 1.72, -0.08), new THREE.Vector3(0, -1.16, 0)],
    [new THREE.Vector3(-1.42, -1.16, 1.38), new THREE.Vector3(1.42, -1.16, -1.38)],
    [new THREE.Vector3(1.42, -1.16, 1.38), new THREE.Vector3(-1.42, -1.16, -1.38)],
  ];

  return { lowerFaces, upperFaces, sectionLoop: seamPts, axisSegments };
}

const ANALYTICAL_KEY_DIR = new THREE.Vector3(6.5, 10.5, 4.5).normalize();
const ANALYTICAL_RIM_DIR = new THREE.Vector3(-7, 3.8, 5).normalize();

function computeAnalyticalShade(normal: THREE.Vector3): number {
  const key = Math.max(0, normal.dot(ANALYTICAL_KEY_DIR)) * 0.20;
  const rim = Math.max(0, normal.dot(ANALYTICAL_RIM_DIR)) * 0.08;
  return Math.min(1.06, 0.80 + key + rim);
}

function buildPolyhedronGeometry(
  faces: readonly PolyFace[],
  baseColorHex = 0xf7f5f0,
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
  normal: THREE.Vector3,
  normalOffset = 0,
  reverseWinding = false,
  baseColorHex = 0xdd5b00,
): THREE.BufferGeometry {
  const positions: number[] = [];
  const colors: number[] = [];
  if (loop.length >= 3) {
    const baseColor = new THREE.Color(baseColorHex);
    const shade = computeAnalyticalShade(normal);
    const r = Math.min(1, baseColor.r * shade);
    const g = Math.min(1, baseColor.g * shade);
    const b = Math.min(1, baseColor.b * shade);
    const offsetVec = normal.clone().multiplyScalar(normalOffset);
    const p0 = loop[0].clone().add(offsetVec);
    for (let i = 1; i < loop.length - 1; i++) {
      const p1 = loop[reverseWinding ? i + 1 : i].clone().add(offsetVec);
      const p2 = loop[reverseWinding ? i : i + 1].clone().add(offsetVec);
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
  const shape = new THREE.Shape();
  const x = -width / 2;
  const y = -height / 2;
  const r = Math.min(radius, width / 2, height / 2);
  shape.moveTo(x + r, y);
  shape.lineTo(x + width - r, y);
  shape.quadraticCurveTo(x + width, y, x + width, y + r);
  shape.lineTo(x + width, y + height - r);
  shape.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
  shape.lineTo(x + r, y + height);
  shape.quadraticCurveTo(x, y + height, x, y + height - r);
  shape.lineTo(x, y + r);
  shape.quadraticCurveTo(x, y, x + r, y);
  return shape;
}

function createRadialShadowTexture(): THREE.CanvasTexture | null {
  if (typeof document === "undefined") return null;
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  const grad = ctx.createRadialGradient(64, 64, 6, 64, 64, 62);
  grad.addColorStop(0, "rgba(17, 17, 16, 0.16)");
  grad.addColorStop(0.55, "rgba(17, 17, 16, 0.06)");
  grad.addColorStop(1, "rgba(17, 17, 16, 0)");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 128, 128);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.needsUpdate = true;
  return tex;
}

function resolveHeroProtoFromUrl(): HeroIllustrationVariant | null {
  if (typeof window === "undefined") return null;
  try {
    const param = new URLSearchParams(window.location.search).get("hero_proto");
    if (param === "b" || param === "sculpture") return "sculpture";
    if (param === "a" || param === "transformation") return "transformation";
  } catch {
    /* ignore search parse issues */
  }
  return null;
}

export interface LandingHeroSculpture3DProps {
  readonly variant?: HeroIllustrationVariant;
}

/**
 * Frameless brand spatial illustration for the Hero section.
 * Benchmarks Concept A ("transformation" — sweeping cutting plane revealing pentagonal cross-section)
 * and Concept B ("sculpture" — architectural intersecting spatial planes & warm core prism).
 * Uses lightweight MeshBasicMaterial/LineBasicMaterial, zero vertex proof tags (S, A, B, M, N, P),
 * zero floating companion balls, and sleeps WebGL RAF whenever settled, off-screen, or tab-hidden.
 */
export function LandingHeroSculpture3D({
  variant = "transformation",
}: LandingHeroSculpture3DProps = {}) {
  const shellRef = useRef<HTMLDivElement | null>(null);
  const hostRef = useRef<HTMLDivElement | null>(null);
  const [webglReady, setWebglReady] = useState(false);
  const [activeVariant, setActiveVariant] = useState<HeroIllustrationVariant>(
    () => resolveHeroProtoFromUrl() ?? variant,
  );
  const svgGradBase = useId().replace(/:/g, "");

  useEffect(() => {
    const fromUrl = resolveHeroProtoFromUrl();
    const target = fromUrl ?? variant;
    setActiveVariant((prev) => (prev === target ? prev : target));
  }, [variant]);

  const transformationSolid = useMemo(() => buildTransformationSolid(), []);

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
      activeRenderer.setPixelRatio(
        Math.min(window.devicePixelRatio || 1, isMobileViewport ? 1.25 : 1.5),
      );
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
      camera.position.set(4.85, 3.25, 5.55);
      camera.lookAt(0, 0.08, 0);

      const sculptureRoot = new THREE.Group();
      scene.add(sculptureRoot);

      // Soft contact shadow shared across both concepts
      const shadowTex = createRadialShadowTexture();
      if (shadowTex) track(shadowTex);
      const shadowGeo = track(new THREE.PlaneGeometry(4.5, 3.6));
      shadowGeo.rotateX(-Math.PI / 2);
      const shadowMat = track(
        new THREE.MeshBasicMaterial({
          map: shadowTex ?? undefined,
          color: shadowTex ? 0xffffff : 0x111110,
          transparent: true,
          opacity: shadowTex ? 0.9 : 0.08,
          depthWrite: false,
        }),
      );
      const shadowMesh = new THREE.Mesh(shadowGeo, shadowMat);
      shadowMesh.position.set(0, -1.72, 0.08);
      scene.add(shadowMesh);

      let updateMotion: (entranceT: number, depthPhase: number, hoverBoost: number) => void;
      const baseRotX = activeVariant === "transformation" ? 0.08 : 0.12;
      const baseRotY = activeVariant === "transformation" ? -0.46 : 0.56;

      if (activeVariant === "transformation") {
        // Concept A: Geometric Transformation — solid pyramid sliced by sweeping sky plane revealing luminous cross-section
        const lowerGeo = track(
          buildPolyhedronGeometry(transformationSolid.lowerFaces, 0xf6f4ee),
        );
        const lowerMat = track(new THREE.MeshBasicMaterial({ vertexColors: true }));
        const lowerMesh = new THREE.Mesh(lowerGeo, lowerMat);
        sculptureRoot.add(lowerMesh);

        const lowerEdgesGeo = track(new THREE.EdgesGeometry(lowerGeo, 20));
        const lowerEdgesMat = track(
          new THREE.LineBasicMaterial({ color: 0x1f1e1c, transparent: true, opacity: 0.62 }),
        );
        lowerMesh.add(new THREE.LineSegments(lowerEdgesGeo, lowerEdgesMat));

        // Exposed semantic-orange pentagonal cross-section (grows gently in scale & vibrance during cut)
        const sectionGroup = new THREE.Group();
        const sectionCenter = transformationSolid.sectionLoop
          .reduce((acc, v) => acc.add(v), new THREE.Vector3())
          .divideScalar(Math.max(1, transformationSolid.sectionLoop.length));
        sectionGroup.position.copy(sectionCenter);

        const centeredLoop = transformationSolid.sectionLoop.map((p) => p.clone().sub(sectionCenter));
        const lowerCapGeo = track(
          buildLoopPolygonGeometry(centeredLoop, TRANSFORMATION_NORMAL, 0.004, false, 0xdd5b00),
        );
        const lowerCapMat = track(
          new THREE.MeshBasicMaterial({
            vertexColors: true,
            transparent: true,
            opacity: 0.94,
            side: THREE.DoubleSide,
          }),
        );
        sectionGroup.add(new THREE.Mesh(lowerCapGeo, lowerCapMat));

        const contourPts = [...centeredLoop, centeredLoop[0]].map((p) =>
          p.clone().addScaledVector(TRANSFORMATION_NORMAL, 0.008),
        );
        const contourGeo = track(new THREE.BufferGeometry().setFromPoints(contourPts));
        const contourMat = track(
          new THREE.LineBasicMaterial({ color: 0x9a3412, transparent: true, opacity: 0.98 }),
        );
        sectionGroup.add(new THREE.Line(contourGeo, contourMat));
        sculptureRoot.add(sectionGroup);

        // Sweeping frosted Axo-Blue glass cutting plane
        const planeHolder = new THREE.Group();
        planeHolder.position.copy(sectionCenter);
        planeHolder.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), TRANSFORMATION_NORMAL);

        const roundedPlaneShape = createRoundedPlaneShape(3.65, 3.05, 0.24);
        const glassGeo = track(new THREE.ShapeGeometry(roundedPlaneShape, 12));
        const glassMat = track(
          new THREE.MeshBasicMaterial({
            color: 0xdcebfa,
            transparent: true,
            opacity: 0.28,
            side: THREE.DoubleSide,
            depthWrite: false,
          }),
        );
        const glassMesh = new THREE.Mesh(glassGeo, glassMat);
        glassMesh.renderOrder = 4;
        planeHolder.add(glassMesh);

        const glassEdgeGeo = track(new THREE.EdgesGeometry(glassGeo));
        const glassEdgeMat = track(
          new THREE.LineBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.88 }),
        );
        planeHolder.add(new THREE.LineSegments(glassEdgeGeo, glassEdgeMat));
        sculptureRoot.add(planeHolder);

        // Translucent upper pyramid apex cap lifting gently along slice normal
        const upperHolder = new THREE.Group();
        const upperGeo = track(
          buildPolyhedronGeometry(transformationSolid.upperFaces, 0xeef5ff),
        );
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

        const upperEdgesGeo = track(new THREE.EdgesGeometry(upperGeo, 20));
        const upperEdgesMat = track(
          new THREE.LineBasicMaterial({ color: 0x31302e, transparent: true, opacity: 0.56 }),
        );
        upperMesh.add(new THREE.LineSegments(upperEdgesGeo, upperEdgesMat));

        // Architectural spatial construction axes (subtle inner depth lines — no labels)
        const axisPoints: THREE.Vector3[] = [];
        for (const [p1, p2] of transformationSolid.axisSegments) {
          axisPoints.push(p1, p2);
        }
        const axisGeo = track(new THREE.BufferGeometry().setFromPoints(axisPoints));
        const axisMat = track(
          new THREE.LineBasicMaterial({ color: 0x62aef0, transparent: true, opacity: 0.36 }),
        );
        sculptureRoot.add(new THREE.LineSegments(axisGeo, axisMat));

        const upperCapGeo = track(
          buildLoopPolygonGeometry(
            transformationSolid.sectionLoop,
            TRANSFORMATION_NORMAL,
            -0.003,
            true,
            0xdd5b00,
          ),
        );
        const upperCapMat = track(
          new THREE.MeshBasicMaterial({
            color: 0xdd5b00,
            transparent: true,
            opacity: 0.14,
            side: THREE.DoubleSide,
            depthWrite: false,
          }),
        );
        const upperCapMesh = new THREE.Mesh(upperCapGeo, upperCapMat);
        upperCapMesh.renderOrder = 3;
        upperHolder.add(upperCapMesh);
        sculptureRoot.add(upperHolder);

        updateMotion = (entranceT, depthPhase, hoverBoost) => {
          const sweepLift = 0.08 + 0.36 * entranceT + hoverBoost * 0.14;
          const planeGlide = (1 - entranceT) * 0.92 + sweepLift * 0.45;
          upperHolder.position.copy(TRANSFORMATION_NORMAL).multiplyScalar(sweepLift);
          planeHolder.position
            .copy(sectionCenter)
            .addScaledVector(TRANSFORMATION_NORMAL, planeGlide);

          const secScale = 0.84 + 0.16 * entranceT;
          sectionGroup.scale.set(secScale, secScale, secScale);
          lowerCapMat.opacity = 0.42 + 0.52 * entranceT;
          sculptureRoot.position.y = -0.04 * (1 - entranceT) + hoverBoost * 0.03;
          sculptureRoot.rotation.z = -0.02 + depthPhase * 0.015;
        };
      } else {
        // Concept B: Abstract Spatial Sculpture — interlocking dihedral sapphire planes + suspended amber prism core
        const frameOuter = track(new THREE.OctahedronGeometry(1.48, 0));
        const frameEdgeGeo = track(new THREE.EdgesGeometry(frameOuter, 8));
        const frameEdgeMat = track(
          new THREE.LineBasicMaterial({ color: 0x31302e, transparent: true, opacity: 0.48 }),
        );
        const frameLines = new THREE.LineSegments(frameEdgeGeo, frameEdgeMat);
        frameLines.scale.set(1.06, 1.16, 1.06);
        sculptureRoot.add(frameLines);

        const planeShapeA = createRoundedPlaneShape(2.9, 2.35, 0.22);
        const planeGeoA = track(new THREE.ShapeGeometry(planeShapeA, 12));
        const planeMatA = track(
          new THREE.MeshBasicMaterial({
            color: 0xdcebfa,
            transparent: true,
            opacity: 0.32,
            side: THREE.DoubleSide,
            depthWrite: false,
          }),
        );
        const ribbonA = new THREE.Group();
        const ribbonMeshA = new THREE.Mesh(planeGeoA, planeMatA);
        ribbonMeshA.renderOrder = 3;
        ribbonA.add(ribbonMeshA);
        ribbonA.add(
          new THREE.LineSegments(
            track(new THREE.EdgesGeometry(planeGeoA)),
            track(new THREE.LineBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.86 })),
          ),
        );
        ribbonA.rotation.set(0.42, 0.28, -0.22);
        sculptureRoot.add(ribbonA);

        const ribbonB = new THREE.Group();
        const planeMatB = track(
          new THREE.MeshBasicMaterial({
            color: 0xeaf4ff,
            transparent: true,
            opacity: 0.26,
            side: THREE.DoubleSide,
            depthWrite: false,
          }),
        );
        const ribbonMeshB = new THREE.Mesh(planeGeoA, planeMatB);
        ribbonMeshB.renderOrder = 2;
        ribbonB.add(ribbonMeshB);
        ribbonB.add(
          new THREE.LineSegments(
            track(new THREE.EdgesGeometry(planeGeoA)),
            track(new THREE.LineBasicMaterial({ color: 0x62aef0, transparent: true, opacity: 0.72 })),
          ),
        );
        ribbonB.rotation.set(-0.48, -0.45, 0.32);
        sculptureRoot.add(ribbonB);

        // Suspended inner amber hexagonal core facet along spatial diagonal
        const hexShape = new THREE.Shape();
        for (let i = 0; i < 6; i++) {
          const ang = (i / 6) * Math.PI * 2;
          const r = i % 2 === 0 ? 0.94 : 0.78;
          const hx = Math.cos(ang) * r;
          const hy = Math.sin(ang) * r;
          if (i === 0) hexShape.moveTo(hx, hy);
          else hexShape.lineTo(hx, hy);
        }
        hexShape.closePath();
        const coreGeo = track(new THREE.ShapeGeometry(hexShape, 6));
        const coreMat = track(
          new THREE.MeshBasicMaterial({
            color: 0xdd5b00,
            transparent: true,
            opacity: 0.86,
            side: THREE.DoubleSide,
          }),
        );
        const coreGroup = new THREE.Group();
        const coreMesh = new THREE.Mesh(coreGeo, coreMat);
        coreMesh.renderOrder = 4;
        coreGroup.add(coreMesh);
        coreGroup.add(
          new THREE.LineSegments(
            track(new THREE.EdgesGeometry(coreGeo)),
            track(new THREE.LineBasicMaterial({ color: 0x9a3412, transparent: true, opacity: 0.96 })),
          ),
        );
        coreGroup.rotation.set(-0.62, 0.36, 0.2);
        sculptureRoot.add(coreGroup);

        const axisGeo = track(
          new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(-1.35, -1.25, -0.95),
            new THREE.Vector3(1.35, 1.25, 0.95),
          ]),
        );
        sculptureRoot.add(
          new THREE.Line(
            axisGeo,
            track(new THREE.LineBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0.56 })),
          ),
        );

        updateMotion = (entranceT, depthPhase, hoverBoost) => {
          ribbonA.rotation.y = 0.28 + hoverBoost * 0.14 + depthPhase * 0.08;
          ribbonB.rotation.y = -0.45 - hoverBoost * 0.12 - depthPhase * 0.06;
          coreGroup.scale.setScalar(0.82 + 0.18 * entranceT);
          coreGroup.position.y = (entranceT - 1) * -0.14 + hoverBoost * 0.06;
          sculptureRoot.position.y = -0.04 * (1 - entranceT) + hoverBoost * 0.03;
          sculptureRoot.rotation.z = 0.02 + depthPhase * 0.02;
        };
      }

      // Render / animation state with demand-based sleeping (0 idle RAF once settled)
      let isDisposed = false;
      let isInView = true;
      let rafId = 0;
      let scrollPausedUntil = 0;
      let scrollResumeTimer = 0;

      let entranceT = reducedMotion ? 1 : 0;
      const entranceStartMs = typeof performance !== "undefined" ? performance.now() : Date.now();
      const entranceDurationMs = 950;

      let targetTiltX = 0;
      let targetTiltY = 0;
      let targetHoverBoost = 0;
      let curTiltX = 0;
      let curTiltY = 0;
      let curHoverBoost = 0;

      const applyVisualState = (nowMs: number) => {
        if (!reducedMotion && entranceT < 1) {
          const linear = Math.max(0, Math.min(1, (nowMs - entranceStartMs) / entranceDurationMs));
          entranceT = 1 - Math.pow(1 - linear, 3);
        }
        const damp = reducedMotion ? 1 : 0.12;
        curTiltX += (targetTiltX - curTiltX) * damp;
        curTiltY += (targetTiltY - curTiltY) * damp;
        curHoverBoost += (targetHoverBoost - curHoverBoost) * damp;

        const depthPhase = reducedMotion ? 0 : Math.sin(entranceT * Math.PI) * 0.4;
        updateMotion(entranceT, depthPhase, curHoverBoost);

        sculptureRoot.rotation.x = baseRotX + curTiltX;
        sculptureRoot.rotation.y = baseRotY + curTiltY - (1 - entranceT) * 0.26;

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
        scrollPausedUntil =
          (typeof performance !== "undefined" ? performance.now() : Date.now()) + 120;
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
      if (!reducedMotion) {
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
  }, [activeVariant, transformationSolid]);

  return (
    <div
      id="landing-hero-sculpture"
      data-hero-variant={activeVariant}
      ref={shellRef}
      className="axo-sp-hero-sculpture"
      role="img"
      aria-label={
        activeVariant === "transformation"
          ? "Minh họa chuyển hóa hình học không gian Axo — mặt phẳng cắt làm lộ thiết diện đa giác"
          : "Điêu khắc không gian Axo — hai mặt phẳng giao nhau quanh lõi đa giác cam"
      }
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
              <stop offset="0%" stopColor="#faf8f3" />
              <stop offset="100%" stopColor="#ece7dc" />
            </linearGradient>
          </defs>

          <ellipse cx="280" cy="400" rx="164" ry="26" fill={`url(#${svgGradBase}-shadow)`} />

          {activeVariant === "transformation" ? (
            <>
              {/* Concept A SVG fallback: Pyramid cut by oblique Axo-Blue plane revealing pentagonal cross-section */}
              <polygon
                points="154,328 242,374 406,336 356,226 196,244"
                fill={`url(#${svgGradBase}-stone)`}
                stroke="rgba(31, 30, 28, 0.56)"
                strokeWidth="1.6"
              />
              <line
                x1="278"
                y1="74"
                x2="278"
                y2="348"
                stroke="#62aef0"
                strokeOpacity="0.45"
                strokeWidth="1.3"
                strokeDasharray="5 5"
              />
              <polygon
                points="196,244 256,204 356,226 332,276 232,286"
                fill={`url(#${svgGradBase}-amber)`}
                stroke="#9a3412"
                strokeWidth="1.7"
              />
              <polygon
                points="118,224 278,154 442,202 282,286"
                fill="rgba(220, 235, 250, 0.34)"
                stroke="#0075de"
                strokeOpacity="0.84"
                strokeWidth="1.5"
              />
              <polygon
                points="204,218 278,74 352,202 276,248"
                fill="rgba(234, 244, 255, 0.3)"
                stroke="rgba(49, 48, 46, 0.54)"
                strokeWidth="1.5"
              />
            </>
          ) : (
            <>
              {/* Concept B SVG fallback: Dihedral sapphire planes around hexagonal amber core */}
              <polygon
                points="154,230 280,104 406,230 280,356"
                fill="none"
                stroke="rgba(49, 48, 46, 0.42)"
                strokeWidth="1.5"
              />
              <polygon
                points="132,262 284,154 426,206 274,314"
                fill="rgba(220, 235, 250, 0.36)"
                stroke="#0075de"
                strokeOpacity="0.84"
                strokeWidth="1.5"
              />
              <polygon
                points="174,174 344,142 386,282 216,314"
                fill="rgba(234, 244, 255, 0.28)"
                stroke="#62aef0"
                strokeOpacity="0.72"
                strokeWidth="1.4"
              />
              <polygon
                points="226,230 258,186 312,190 334,234 300,276 248,272"
                fill={`url(#${svgGradBase}-amber)`}
                fillOpacity="0.88"
                stroke="#9a3412"
                strokeWidth="1.7"
              />
            </>
          )}
        </svg>
      )}
    </div>
  );
}
