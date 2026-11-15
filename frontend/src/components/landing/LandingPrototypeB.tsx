import { useCallback, useEffect, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import * as THREE from "three";
import { useAuthStore } from "../../state/auth";
import { LandingHeader } from "./LandingHeader";
import { LandingInteractiveDemo } from "./LandingInteractiveDemo";
import {
  V13FinalCtaBand,
  V13FooterBand,
  V13ReviewBanner,
  V13_STORY_SCENES,
  scrollToLandingSection,
} from "./LandingPrototypeA";
import {
  LANDING_PRISM_STORY_SPEC,
  LANDING_PYRAMID_SAMPLE,
  enterAxoWorkspace,
  type Vec3Tuple,
} from "./landing-geometry-data";

interface ScreenLabel2D {
  readonly id: string;
  readonly label: string;
  readonly role: string;
  readonly px: number;
  readonly py: number;
  readonly lx: number;
  readonly ly: number;
}

function buildConvexPolygonGeometry(
  pts: readonly THREE.Vector3[],
  hexColor: number,
  shadeFactor = 1,
): THREE.BufferGeometry {
  const geo = new THREE.BufferGeometry();
  const base = new THREE.Color(hexColor).multiplyScalar(shadeFactor);
  const positions: number[] = [];
  const colors: number[] = [];

  for (let i = 1; i + 1 < pts.length; i++) {
    const tri = [pts[0], pts[i], pts[i + 1]];
    for (const v of tri) {
      positions.push(v.x, v.y, v.z);
      colors.push(base.r, base.g, base.b);
    }
  }

  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  geo.computeVertexNormals();
  return geo;
}

function computeLightShade(normal: THREE.Vector3): number {
  const lightDir = new THREE.Vector3(0.45, 0.82, 0.36).normalize();
  const ndotl = Math.max(-1, Math.min(1, normal.clone().normalize().dot(lightDir)));
  return Math.max(0.76, Math.min(1.04, 0.88 + 0.14 * ndotl));
}

function addDashableSegment(
  a: THREE.Vector3,
  b: THREE.Vector3,
  color: number,
  opacity: number,
  dashed: boolean,
  track: <T extends { dispose: () => void }>(item: T) => T,
): THREE.Line {
  const geo = track(new THREE.BufferGeometry().setFromPoints([a, b]));
  if (dashed) {
    const mat = track(
      new THREE.LineDashedMaterial({
        color,
        transparent: true,
        opacity,
        dashSize: 0.12,
        gapSize: 0.08,
      }),
    );
    const line = new THREE.Line(geo, mat);
    line.computeLineDistances();
    return line;
  }
  const mat = track(
    new THREE.LineBasicMaterial({
      color,
      transparent: true,
      opacity,
    }),
  );
  return new THREE.Line(geo, mat);
}

function HeroConceptBFallbackSvg() {
  return (
    <svg
      className="axo-v13-hero-svg"
      viewBox="0 0 580 440"
      role="img"
      aria-label="Không gian dựng hình 3D với các mặt phẳng cắt và thiết diện"
    >
      <ellipse cx="290" cy="368" rx="160" ry="20" fill="rgba(25, 25, 24, 0.06)" />
      <line x1="290" y1="68" x2="290" y2="352" stroke="#0075de" strokeOpacity="0.42" strokeWidth="1.4" strokeDasharray="4 4" />
      <polygon
        points="146,246 286,144 434,196 294,298"
        fill="rgba(220, 235, 250, 0.38)"
        stroke="#0075de"
        strokeWidth="1.6"
      />
      <polygon
        points="174,174 342,138 398,274 230,310"
        fill="rgba(247, 246, 244, 0.72)"
        stroke="#191918"
        strokeOpacity="0.72"
        strokeWidth="1.6"
      />
      <polygon
        points="224,234 256,184 316,188 344,232 308,278 248,274"
        fill="#dd5b00"
        fillOpacity="0.9"
        stroke="#9a3412"
        strokeWidth="2"
      />
    </svg>
  );
}

function HeroConceptB3D({
  webglAllowed,
}: {
  readonly webglAllowed: boolean;
}) {
  const shellRef = useRef<HTMLDivElement | null>(null);
  const hostRef = useRef<HTMLDivElement | null>(null);
  const [webglReady, setWebglReady] = useState(false);
  const [contextLost, setContextLost] = useState(false);
  const targetTiltRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const wakeRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    const shell = shellRef.current;
    const host = hostRef.current;
    if (!shell || !host || !webglAllowed || typeof window === "undefined") {
      setWebglReady(false);
      return;
    }

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

    setWebglReady(true);

    const activeRenderer = renderer;
    const isMobile = window.innerWidth <= 820;
    activeRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, isMobile ? 1.25 : 1.5));
    activeRenderer.setClearColor(0x000000, 0);
    activeRenderer.outputColorSpace = THREE.SRGBColorSpace;
    host.appendChild(activeRenderer.domElement);

    const disposables: { dispose: () => void }[] = [];
    const track = <T extends { dispose: () => void }>(item: T): T => {
      disposables.push(item);
      return item;
    };

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(36, 580 / 440, 0.1, 100);
    const [camX, camY, camZ] = LANDING_PYRAMID_SAMPLE.defaultCamera;
    const [lookX, lookY, lookZ] = LANDING_PYRAMID_SAMPLE.defaultLookAt;
    camera.position.set(camX * 0.92, camY * 0.92, camZ * 0.92);
    camera.lookAt(lookX, lookY, lookZ);

    const root = new THREE.Group();
    scene.add(root);

    // Spatial construction based on LANDING_PYRAMID_SAMPLE coordinates
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

    // Phase 1: Base + altitude guide + vertices
    const guideGroup = new THREE.Group();
    guideGroup.add(addDashableSegment(S, A, 0x0075de, 0.48, true, track));
    guideGroup.add(addDashableSegment(A, B, 0x31302e, 0.5, true, track));
    guideGroup.add(addDashableSegment(A, D, 0x31302e, 0.5, true, track));
    root.add(guideGroup);

    const nodeGeo = track(new THREE.SphereGeometry(0.055, 16, 16));
    const nodeDarkMat = track(new THREE.MeshBasicMaterial({ color: 0x191918 }));
    const nodeOrangeMat = track(new THREE.MeshBasicMaterial({ color: 0xdd5b00 }));
    for (const pt of [S, A, B, C, D]) {
      const m = new THREE.Mesh(nodeGeo, nodeDarkMat);
      m.position.copy(pt);
      guideGroup.add(m);
    }

    // Phase 2: Solid front faces + edges
    const solidGroup = new THREE.Group();
    const faceList = [
      [S, B, C],
      [S, C, D],
      [B, C, D, A],
    ];
    for (const face of faceList) {
      const n = new THREE.Vector3()
        .subVectors(face[1], face[0])
        .cross(new THREE.Vector3().subVectors(face[2], face[0]))
        .normalize();
      const geo = track(buildConvexPolygonGeometry(face, 0xf7f6f4, computeLightShade(n)));
      const mat = track(
        new THREE.MeshBasicMaterial({
          vertexColors: true,
          transparent: true,
          opacity: 0.78,
          side: THREE.DoubleSide,
        }),
      );
      solidGroup.add(new THREE.Mesh(geo, mat));
    }
    for (const [u, v] of [
      [S, B],
      [S, C],
      [S, D],
      [B, C],
      [C, D],
    ] as const) {
      solidGroup.add(addDashableSegment(u, v, 0x191918, 0.72, false, track));
    }
    root.add(solidGroup);

    // Phase 3: Cutting plane (MNP) + cross section loop MENPF using exact sample planeQuad
    const planeGroup = new THREE.Group();
    const heroPlaneVecs = LANDING_PYRAMID_SAMPLE.planeQuad.map(
      (pt) => new THREE.Vector3(pt[0], pt[1], pt[2]),
    );
    const secCenter = heroPlaneVecs
      .reduce((acc, v) => acc.add(v), new THREE.Vector3())
      .divideScalar(Math.max(1, heroPlaneVecs.length));
    const nVec = new THREE.Vector3()
      .subVectors(loopPts[1], loopPts[0])
      .cross(new THREE.Vector3().subVectors(loopPts[2], loopPts[0]))
      .normalize();
    const localHeroPlane = heroPlaneVecs.map((v) => v.clone().sub(secCenter));
    planeGroup.position.copy(secCenter);

    const planeGeo = track(buildConvexPolygonGeometry(localHeroPlane, 0xdcebfa, 1));
    const planeMat = track(
      new THREE.MeshBasicMaterial({
        vertexColors: true,
        transparent: true,
        opacity: 0.36,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const planeMesh = new THREE.Mesh(planeGeo, planeMat);
    planeMesh.renderOrder = 3;
    planeGroup.add(planeMesh);
    for (let i = 0; i < localHeroPlane.length; i++) {
      planeGroup.add(
        addDashableSegment(
          localHeroPlane[i],
          localHeroPlane[(i + 1) % localHeroPlane.length],
          0x0075de,
          0.88,
          false,
          track,
        ),
      );
    }
    root.add(planeGroup);

    const sectionGroup = new THREE.Group();
    const secGeo = track(buildConvexPolygonGeometry(loopPts, 0xdd5b00, 1));
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
    for (let i = 0; i < loopPts.length; i++) {
      const a = loopPts[i];
      const b = loopPts[(i + 1) % loopPts.length];
      sectionGroup.add(addDashableSegment(a, b, 0x9a3412, 0.96, false, track));
      const dot = new THREE.Mesh(nodeGeo, nodeOrangeMat);
      dot.position.copy(a);
      dot.scale.setScalar(0.82);
      sectionGroup.add(dot);
    }
    root.add(sectionGroup);

    let disposed = false;
    let isInView = true;
    let rafId = 0;
    let t = reducedMotion ? 1 : 0;
    const startMs = performance.now();
    let curTiltX = 0;
    let curTiltY = 0;

    const applyState = (nowMs: number): boolean => {
      if (!reducedMotion && t < 1) {
        const linear = Math.min(1, Math.max(0, (nowMs - startMs) / 1050));
        t = 1 - Math.pow(1 - linear, 3);
      }
      const damp = reducedMotion ? 1 : 0.14;
      curTiltX += (targetTiltRef.current.x - curTiltX) * damp;
      curTiltY += (targetTiltRef.current.y - curTiltY) * damp;

      const solidAppear = Math.min(1, Math.max(0.18, (t - 0.1) / 0.55));
      const planeAppear = Math.min(1, Math.max(0, (t - 0.35) / 0.45));
      const secAppear = Math.min(1, Math.max(0, (t - 0.55) / 0.45));

      solidGroup.scale.setScalar(0.92 + 0.08 * solidAppear);
      planeMat.opacity = 0.36 * planeAppear;
      planeGroup.position
        .copy(secCenter)
        .addScaledVector(nVec, (1 - planeAppear) * 0.65);
      secMat.opacity = 0.92 * secAppear;

      const orbitOffset = (1 - t) * 0.24;
      root.rotation.y = 0.18 + curTiltX - orbitOffset;
      root.rotation.x = 0.04 + curTiltY;

      activeRenderer.render(scene, camera);

      return (
        t >= 0.999 &&
        Math.abs(targetTiltRef.current.x - curTiltX) < 0.0008 &&
        Math.abs(targetTiltRef.current.y - curTiltY) < 0.0008
      );
    };

    const tick = (nowMs: number) => {
      if (disposed || !isInView || document.hidden) {
        rafId = 0;
        return;
      }
      const settled = applyState(nowMs);
      if (!settled && !reducedMotion) {
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

    const syncSize = () => {
      const rect = shell.getBoundingClientRect();
      const w = Math.max(220, Math.floor(rect.width));
      const h = Math.max(220, Math.floor(rect.height));
      activeRenderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      wake();
    };
    syncSize();

    const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(syncSize) : null;
    ro?.observe(shell);

    const io =
      typeof IntersectionObserver !== "undefined"
        ? new IntersectionObserver(
            (entries) => {
              isInView = Boolean(entries[0]?.isIntersecting);
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
    io?.observe(shell);

    const onVisibility = () => {
      if (document.hidden && rafId) {
        window.cancelAnimationFrame(rafId);
        rafId = 0;
      } else if (!document.hidden && isInView) {
        wake();
      }
    };
    document.addEventListener("visibilitychange", onVisibility);

    const canvas = activeRenderer.domElement;
    const onLost = (e: Event) => {
      e.preventDefault();
      setContextLost(true);
      if (rafId) {
        window.cancelAnimationFrame(rafId);
        rafId = 0;
      }
    };
    const onRestored = () => {
      setContextLost(false);
      wake();
    };
    canvas.addEventListener("webglcontextlost", onLost);
    canvas.addEventListener("webglcontextrestored", onRestored);

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
      canvas.removeEventListener("webglcontextlost", onLost);
      canvas.removeEventListener("webglcontextrestored", onRestored);
      for (const item of disposables) {
        item.dispose();
      }
      activeRenderer.dispose();
      if (canvas.parentElement === host) {
        host.removeChild(canvas);
      }
    };
  }, [webglAllowed]);

  const handlePointerMove = useCallback((e: ReactPointerEvent<HTMLDivElement>) => {
    const rect = shellRef.current?.getBoundingClientRect();
    if (!rect || rect.width <= 0 || rect.height <= 0) return;
    targetTiltRef.current = {
      x: ((e.clientX - rect.left) / rect.width - 0.5) * 0.24,
      y: -((e.clientY - rect.top) / rect.height - 0.5) * 0.14,
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
      className="axo-v13-hero-stage"
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
      aria-label="Minh họa dựng hình không gian 3D Axo"
    >
      <div
        ref={hostRef}
        className={
          webglAllowed && webglReady && !contextLost
            ? "axo-v13-canvas-host"
            : "axo-v13-canvas-host is-hidden"
        }
      />
      {(!webglAllowed || !webglReady || contextLost) && <HeroConceptBFallbackSvg />}
    </div>
  );
}

function Story3DFallbackSvg({ activeStage }: { readonly activeStage: number }) {
  const s = V13_STORY_SCENES[activeStage] ?? V13_STORY_SCENES[0];
  return (
    <svg
      className="axo-v13-story-svg"
      viewBox="0 0 600 430"
      role="img"
      aria-label={`Khối lăng trụ ABC.A′B′C′ chặng ${s.stepLabel}`}
    >
      <ellipse cx="300" cy="348" rx="172" ry="20" fill="rgba(25, 25, 24, 0.05)" />
      <polygon
        points="180,318 424,334 316,246"
        fill="#f7f6f4"
        stroke="#191918"
        strokeWidth="1.6"
      />
      <polygon
        points="180,148 424,164 316,84"
        fill="rgba(247, 246, 244, 0.52)"
        stroke="#191918"
        strokeOpacity={0.25 + 0.65 * s.extrude}
        strokeWidth="1.6"
      />
      <line x1="180" y1="318" x2="180" y2="148" stroke="#191918" strokeOpacity={0.25 + 0.65 * s.extrude} strokeWidth="1.7" />
      <line x1="424" y1="334" x2="424" y2="164" stroke="#191918" strokeOpacity={0.25 + 0.65 * s.extrude} strokeWidth="1.7" />
      <line x1="316" y1="246" x2="316" y2="84" stroke="#615d59" strokeOpacity={0.45} strokeDasharray="5 5" strokeWidth="1.4" />
      {s.planeSweep > 0 && (
        <polygon
          points="156,280 438,248 456,162 200,214"
          fill="#dcebfa"
          fillOpacity={0.38 * s.planeSweep}
          stroke="#0075de"
          strokeWidth="1.6"
        />
      )}
      {s.sectionFill > 0 && (
        <polygon
          points="302,326 248,282 316,165 424,249"
          fill="#dd5b00"
          fillOpacity={0.86 * s.sectionFill}
          stroke="#9a3412"
          strokeWidth="2.1"
        />
      )}
    </svg>
  );
}

function Continuous3DStoryStage({
  activeStage,
}: {
  readonly activeStage: number;
}) {
  const shellRef = useRef<HTMLDivElement | null>(null);
  const hostRef = useRef<HTMLDivElement | null>(null);
  const [webglReady, setWebglReady] = useState(false);
  const [contextLost, setContextLost] = useState(false);
  const [overlayLabels, setOverlayLabels] = useState<readonly ScreenLabel2D[]>([]);
  const targetStageRef = useRef(activeStage);
  const wakeRef = useRef<(() => void) | null>(null);

  targetStageRef.current = activeStage;

  useEffect(() => {
    wakeRef.current?.();
  }, [activeStage]);

  useEffect(() => {
    const shell = shellRef.current;
    const host = hostRef.current;
    if (!shell || !host || typeof window === "undefined") {
      setWebglReady(false);
      return;
    }

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

    setWebglReady(true);

    const activeRenderer = renderer;
    const isMobile = window.innerWidth <= 820;
    activeRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, isMobile ? 1.25 : 1.5));
    activeRenderer.setClearColor(0x000000, 0);
    activeRenderer.outputColorSpace = THREE.SRGBColorSpace;
    host.appendChild(activeRenderer.domElement);

    const disposables: { dispose: () => void }[] = [];
    const track = <T extends { dispose: () => void }>(item: T): T => {
      disposables.push(item);
      return item;
    };

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(34, 600 / 430, 0.1, 100);
    const root = new THREE.Group();
    scene.add(root);

    const pMap = LANDING_PRISM_STORY_SPEC.pointMap;
    const baseVec = (id: string) => {
      const pos: Vec3Tuple = pMap[id]?.pos ?? [0, 0, 0];
      return new THREE.Vector3(pos[0], pos[1], pos[2]);
    };

    const pA = baseVec("A");
    const pB = baseVec("B");
    const pC = baseVec("C");
    const pA1 = baseVec("A_prime");
    const pB1 = baseVec("B_prime");
    const pC1 = baseVec("C_prime");
    const pM = baseVec("M");
    const pN = baseVec("N");
    const pP = baseVec("P");
    const pQ = baseVec("Q");

    // Prism group scaled smoothly from base Y = pA.y
    const baseY = pA.y;
    const prismPivot = new THREE.Group();
    prismPivot.position.set(0, baseY, 0);
    root.add(prismPivot);

    const toLocal = (v: THREE.Vector3) => new THREE.Vector3(v.x, v.y - baseY, v.z);

    // Side & top faces anchored to prismPivot
    const wallFaces = [
      [toLocal(pA), toLocal(pB), toLocal(pB1), toLocal(pA1)],
      [toLocal(pA), toLocal(pC), toLocal(pC1), toLocal(pA1)],
      [toLocal(pB), toLocal(pC), toLocal(pC1), toLocal(pB1)],
      [toLocal(pA1), toLocal(pB1), toLocal(pC1)],
    ];
    const wallMats: THREE.MeshBasicMaterial[] = [];
    for (const face of wallFaces) {
      const n = new THREE.Vector3()
        .subVectors(face[1], face[0])
        .cross(new THREE.Vector3().subVectors(face[2], face[0]))
        .normalize();
      const geo = track(buildConvexPolygonGeometry(face, 0xf7f6f4, computeLightShade(n)));
      const mat = track(
        new THREE.MeshBasicMaterial({
          vertexColors: true,
          transparent: true,
          opacity: 0.48,
          side: THREE.DoubleSide,
          depthWrite: false,
        }),
      );
      wallMats.push(mat);
      prismPivot.add(new THREE.Mesh(geo, mat));
    }

    const baseGeo = track(
      buildConvexPolygonGeometry([pA, pB, pC], 0xebe9e4, 0.96),
    );
    const baseMat = track(
      new THREE.MeshBasicMaterial({
        vertexColors: true,
        transparent: true,
        opacity: 0.85,
        side: THREE.DoubleSide,
      }),
    );
    root.add(new THREE.Mesh(baseGeo, baseMat));

    const solidLineMats: THREE.LineBasicMaterial[] = [];
    for (const edge of LANDING_PRISM_STORY_SPEC.solidEdges) {
      const a = toLocal(baseVec(edge.from));
      const b = toLocal(baseVec(edge.to));
      const isBack = edge.from === "C" || edge.to === "C";
      const seg = addDashableSegment(
        a,
        b,
        isBack ? 0x615d59 : 0x191918,
        isBack ? 0.56 : 0.82,
        isBack,
        track,
      );
      if (seg.material instanceof THREE.LineBasicMaterial) {
        solidLineMats.push(seg.material);
      }
      prismPivot.add(seg);
    }

    // Cutting plane (MNP) from exact specimen planeQuad
    const storyPlaneVecs = LANDING_PRISM_STORY_SPEC.planeQuad.map(
      (pt) => new THREE.Vector3(pt[0], pt[1], pt[2]),
    );
    const planeCenter = storyPlaneVecs
      .reduce((acc, v) => acc.add(v), new THREE.Vector3())
      .divideScalar(Math.max(1, storyPlaneVecs.length));
    const planeN = new THREE.Vector3()
      .subVectors(pN, pM)
      .cross(new THREE.Vector3().subVectors(pP, pM))
      .normalize();
    const localStoryPlane = storyPlaneVecs.map((v) => v.clone().sub(planeCenter));
    const planeGroup = new THREE.Group();
    planeGroup.position.copy(planeCenter);
    const planeGeo = track(buildConvexPolygonGeometry(localStoryPlane, 0xdcebfa, 1));
    const planeMat = track(
      new THREE.MeshBasicMaterial({
        vertexColors: true,
        transparent: true,
        opacity: 0,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    const planeMesh = new THREE.Mesh(planeGeo, planeMat);
    planeMesh.renderOrder = 3;
    planeGroup.add(planeMesh);
    const planeEdgeMat = track(
      new THREE.LineBasicMaterial({ color: 0x0075de, transparent: true, opacity: 0 }),
    );
    for (let i = 0; i < localStoryPlane.length; i++) {
      const edgeGeo = track(
        new THREE.BufferGeometry().setFromPoints([
          localStoryPlane[i],
          localStoryPlane[(i + 1) % localStoryPlane.length],
        ]),
      );
      planeGroup.add(new THREE.Line(edgeGeo, planeEdgeMat));
    }
    root.add(planeGroup);

    // Cross section MNPQ
    const secGeo = track(buildConvexPolygonGeometry([pM, pN, pP, pQ], 0xdd5b00, 1));
    const secMat = track(
      new THREE.MeshBasicMaterial({
        vertexColors: true,
        transparent: true,
        opacity: 0,
        side: THREE.DoubleSide,
      }),
    );
    const secMesh = new THREE.Mesh(secGeo, secMat);
    secMesh.renderOrder = 4;
    root.add(secMesh);

    const secEdgeMats: THREE.LineBasicMaterial[] = [];
    for (const [u, v] of [
      [pM, pN],
      [pN, pP],
      [pP, pQ],
      [pQ, pM],
    ] as const) {
      const seg = addDashableSegment(u, v, 0x9a3412, 0, false, track);
      if (seg.material instanceof THREE.LineBasicMaterial) {
        secEdgeMats.push(seg.material);
      }
      root.add(seg);
    }

    // Highlighted intersection & seed dots (P and Q live inside prismPivot so P tracks extrude)
    const dotGeo = track(new THREE.SphereGeometry(0.068, 14, 14));
    const qDotMat = track(
      new THREE.MeshBasicMaterial({ color: 0xdd5b00, transparent: true, opacity: 0 }),
    );
    const seedDotMat = track(new THREE.MeshBasicMaterial({ color: 0x0075de }));
    for (const seed of [pM, pN]) {
      const m = new THREE.Mesh(dotGeo, seedDotMat);
      m.position.copy(seed);
      root.add(m);
    }
    const pDot = new THREE.Mesh(dotGeo, seedDotMat);
    pDot.position.copy(toLocal(pP));
    prismPivot.add(pDot);

    const qDot = new THREE.Mesh(dotGeo, qDotMat);
    qDot.position.copy(toLocal(pQ));
    prismPivot.add(qDot);

    let disposed = false;
    let isInView = true;
    let rafId = 0;

    const initialTarget = V13_STORY_SCENES[targetStageRef.current] ?? V13_STORY_SCENES[0];
    let curYaw = initialTarget.yaw;
    let curPitch = initialTarget.pitch;
    let curZoom = initialTarget.zoom;
    let curExtrude = initialTarget.extrude;
    let curPlane = initialTarget.planeSweep;
    let curSection = initialTarget.sectionFill;

    const applyState = (): boolean => {
      const target = V13_STORY_SCENES[targetStageRef.current] ?? V13_STORY_SCENES[0];
      const damp = reducedMotion ? 1 : 0.14;
      curYaw += (target.yaw - curYaw) * damp;
      curPitch += (target.pitch - curPitch) * damp;
      curZoom += (target.zoom - curZoom) * damp;
      curExtrude += (target.extrude - curExtrude) * damp;
      curPlane += (target.planeSweep - curPlane) * damp;
      curSection += (target.sectionFill - curSection) * damp;

      const radius = 12.6 / curZoom;
      const targetX = 0;
      const targetY = -0.08;
      const targetZ = -0.38;
      camera.position.set(
        targetX + radius * Math.sin(curYaw) * Math.cos(curPitch),
        targetY + radius * Math.sin(curPitch),
        targetZ + radius * Math.cos(curYaw) * Math.cos(curPitch),
      );
      camera.lookAt(targetX, targetY, targetZ);
      camera.updateMatrixWorld();

      prismPivot.scale.set(1, Math.max(0.05, curExtrude), 1);
      for (const mat of wallMats) {
        mat.opacity = 0.08 + 0.44 * curExtrude;
      }
      for (const mat of solidLineMats) {
        mat.opacity = 0.25 + 0.6 * curExtrude;
      }

      planeGroup.position
        .copy(planeCenter)
        .addScaledVector(planeN, (1 - curPlane) * 0.85);
      planeMat.opacity = 0.36 * curPlane;
      planeEdgeMat.opacity = 0.86 * curPlane;

      secMat.opacity = 0.88 * curSection;
      for (const m of secEdgeMats) {
        m.opacity = Math.max(curPlane * 0.55, curSection * 0.96);
      }
      qDotMat.opacity = curPlane;

      activeRenderer.render(scene, camera);

      const rect = shell.getBoundingClientRect();
      const vw = 600;
      const vh = 430;
      const centroidWorld = new THREE.Vector3();
      const visibleIds = ["A", "B", "C", "A_prime", "B_prime", "C_prime", "M", "N", "P", "Q"].filter(
        (id) => {
          if (id === "Q") return curPlane > 0.25;
          if (id.includes("prime")) return curExtrude > 0.68;
          return true;
        },
      );
      const projectedPts: { id: string; sx: number; sy: number }[] = visibleIds.map((id) => {
        const w = baseVec(id);
        if (id.includes("prime") || id === "P" || id === "Q") {
          w.y = baseY + (w.y - baseY) * curExtrude;
        }
        const ndc = w.clone().project(camera);
        const sx = (ndc.x * 0.5 + 0.5) * vw;
        const sy = (-ndc.y * 0.5 + 0.5) * vh;
        centroidWorld.add(new THREE.Vector3(sx, sy, 0));
        return { id, sx, sy };
      });
      if (projectedPts.length > 0 && rect.width > 0) {
        centroidWorld.divideScalar(projectedPts.length);
        setOverlayLabels(
          projectedPts.map((pt) => {
            const dx = pt.sx - centroidWorld.x;
            const dy = pt.sy - centroidWorld.y;
            const len = Math.max(1, Math.hypot(dx, dy));
            return {
              id: pt.id,
              label: pMap[pt.id].label,
              role: pMap[pt.id].role,
              px: pt.sx,
              py: pt.sy,
              lx: Math.min(576, Math.max(24, pt.sx + (dx / len) * 16)),
              ly: Math.min(406, Math.max(24, pt.sy + (dy / len) * 16 + 4)),
            };
          }),
        );
      }

      return (
        Math.abs(target.yaw - curYaw) < 0.0008 &&
        Math.abs(target.pitch - curPitch) < 0.0008 &&
        Math.abs(target.zoom - curZoom) < 0.0008 &&
        Math.abs(target.extrude - curExtrude) < 0.0008 &&
        Math.abs(target.planeSweep - curPlane) < 0.0008 &&
        Math.abs(target.sectionFill - curSection) < 0.0008
      );
    };

    const tick = () => {
      if (disposed || !isInView || document.hidden) {
        rafId = 0;
        return;
      }
      const converged = applyState();
      if (!converged && !reducedMotion) {
        rafId = window.requestAnimationFrame(tick);
      } else {
        rafId = 0;
      }
    };

    const wake = () => {
      if (disposed || !isInView || document.hidden) return;
      if (reducedMotion) {
        applyState();
        return;
      }
      if (rafId === 0) {
        rafId = window.requestAnimationFrame(tick);
      }
    };
    wakeRef.current = wake;

    const syncSize = () => {
      const rect = shell.getBoundingClientRect();
      const w = Math.max(240, Math.floor(rect.width));
      const h = Math.max(220, Math.floor(rect.height));
      activeRenderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      wake();
    };
    syncSize();

    const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(syncSize) : null;
    ro?.observe(shell);

    const io =
      typeof IntersectionObserver !== "undefined"
        ? new IntersectionObserver(
            (entries) => {
              isInView = Boolean(entries[0]?.isIntersecting);
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
    io?.observe(shell);

    const onVisibility = () => {
      if (document.hidden && rafId) {
        window.cancelAnimationFrame(rafId);
        rafId = 0;
      } else if (!document.hidden && isInView) {
        wake();
      }
    };
    document.addEventListener("visibilitychange", onVisibility);

    const canvas = activeRenderer.domElement;
    const onLost = (e: Event) => {
      e.preventDefault();
      setContextLost(true);
      if (rafId) {
        window.cancelAnimationFrame(rafId);
        rafId = 0;
      }
    };
    const onRestored = () => {
      setContextLost(false);
      wake();
    };
    canvas.addEventListener("webglcontextlost", onLost);
    canvas.addEventListener("webglcontextrestored", onRestored);

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
      canvas.removeEventListener("webglcontextlost", onLost);
      canvas.removeEventListener("webglcontextrestored", onRestored);
      for (const item of disposables) {
        item.dispose();
      }
      activeRenderer.dispose();
      if (canvas.parentElement === host) {
        host.removeChild(canvas);
      }
    };
  }, []);

  return (
    <div id="landing-storytelling-scene" ref={shellRef} className="axo-v13-story-canvas-wrap">
      <div
        ref={hostRef}
        className={webglReady && !contextLost ? "axo-v13-canvas-host" : "axo-v13-canvas-host is-hidden"}
      />
      {webglReady && !contextLost && overlayLabels.length > 0 && (
        <svg className="axo-v13-3d-labels-overlay" viewBox="0 0 600 430" aria-hidden="true">
          {overlayLabels.map((pt) => (
            <text
              key={pt.id}
              x={pt.lx}
              y={pt.ly}
              textAnchor="middle"
              fontSize="13"
              fontWeight="700"
              fill={pt.role === "intersection" ? "#9a3412" : "#191918"}
            >
              {pt.label}
            </text>
          ))}
        </svg>
      )}
      {(!webglReady || contextLost) && <Story3DFallbackSvg activeStage={activeStage} />}
    </div>
  );
}

export function LandingPrototypeB({
  onSwitchMode,
}: {
  readonly onSwitchMode: (mode: "prod" | "a" | "b") => void;
}) {
  const user = useAuthStore((s) => s.user);
  const primaryHeroLabel = user ? "Vào ứng dụng" : "Bắt đầu dựng hình";

  const [activeStage, setActiveStage] = useState(0);
  const [autoPlay, setAutoPlay] = useState(true);
  const [demoNearViewport, setDemoNearViewport] = useState(false);
  const demoSlotRef = useRef<HTMLDivElement | null>(null);
  const stepRefs = useRef<(HTMLButtonElement | null)[]>([]);

  useEffect(() => {
    if (!autoPlay || typeof window === "undefined") return;
    const reduced =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      setAutoPlay(false);
      return;
    }
    if (activeStage >= V13_STORY_SCENES.length - 1) {
      setAutoPlay(false);
      return;
    }
    const timer = window.setTimeout(() => {
      setActiveStage((prev) => Math.min(V13_STORY_SCENES.length - 1, prev + 1));
    }, 3400);
    return () => window.clearTimeout(timer);
  }, [activeStage, autoPlay]);

  useEffect(() => {
    if (typeof window === "undefined" || typeof IntersectionObserver === "undefined") return;
    const nodes = stepRefs.current.filter((n): n is HTMLButtonElement => n !== null);
    if (nodes.length === 0) return;

    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          const idxStr = entry.target.getAttribute("data-story-index");
          const idx = idxStr ? Number(idxStr) : -1;
          if (idx >= 0 && idx < V13_STORY_SCENES.length && !autoPlay) {
            setActiveStage(idx);
          }
        }
      },
      { threshold: 0.6, rootMargin: "-15% 0px -30% 0px" },
    );

    for (const el of nodes) io.observe(el);
    return () => io.disconnect();
  }, [autoPlay]);

  // Keep total active WebGL contexts <= 2 by leasing WebGL slot #2 between Hero (top) and Demo (bottom)
  useEffect(() => {
    const slot = demoSlotRef.current;
    if (!slot || typeof IntersectionObserver === "undefined") return;
    const io = new IntersectionObserver(
      (entries) => {
        setDemoNearViewport(Boolean(entries[0]?.isIntersecting));
      },
      { rootMargin: "260px 0px" },
    );
    io.observe(slot);
    return () => io.disconnect();
  }, []);

  const scene = V13_STORY_SCENES[activeStage] ?? V13_STORY_SCENES[0];

  const handleToggleAutoPlay = () => {
    if (autoPlay) {
      setAutoPlay(false);
    } else {
      if (activeStage >= V13_STORY_SCENES.length - 1) {
        setActiveStage(0);
      }
      setAutoPlay(true);
    }
  };

  return (
    <div id="view-landing" className="axo-sp-root axo-v13-root axo-v13-proto-b">
      <LandingHeader />

      <main className="axo-sp-main">
        <V13ReviewBanner activeMode="b" onSwitchMode={onSwitchMode} />

        {/* Hero Concept B: Spatial Construction (3D demand-rendered scene) */}
        <section
          id="landing-hero"
          className="axo-sp-hero axo-v13-hero"
          aria-labelledby="landing-hero-title"
        >
          <div className="axo-sp-container axo-sp-hero-grid">
            <div className="axo-sp-hero-copy">
              <h1 id="landing-hero-title" className="axo-sp-hero-title axo-v13-hero-title">
                Hình học không gian, dễ hình dung hơn.
              </h1>
              <p className="axo-sp-hero-lead">
                Axo biến đề bài tiếng Việt thành mô hình 3D trực quan, giúp bạn quan sát từng
                mặt phẳng, giao tuyến và thiết diện theo từng bước dựng.
              </p>
              <div className="axo-sp-hero-actions">
                <button
                  type="button"
                  id="btn-landing-hero-start"
                  className="axo-sp-btn-primary axo-sp-btn-lg"
                  onClick={enterAxoWorkspace}
                >
                  {primaryHeroLabel}
                </button>
                <button
                  type="button"
                  id="btn-landing-hero-story"
                  className="axo-sp-btn-secondary axo-sp-btn-lg"
                  onClick={() => scrollToLandingSection("cach-hoat-dong")}
                >
                  Khám phá cách hoạt động
                </button>
              </div>
            </div>

            <div className="axo-sp-hero-visual">
              <HeroConceptB3D webglAllowed={!demoNearViewport} />
            </div>
          </div>
        </section>

        {/* Continuous 3D Spatial Storytelling */}
        <section
          id="cach-hoat-dong"
          className="axo-v13-story-section"
          aria-labelledby="landing-story-heading"
        >
          <div className="axo-sp-container axo-v13-story-grid">
            <div className="axo-v13-story-visual-col">
              <div className="axo-v13-story-sticky">
                <div className="axo-v13-stage-toolbar">
                  <span className="axo-v13-stage-caption">
                    {scene.stepLabel}: {scene.title}
                  </span>
                  <button
                    type="button"
                    id="btn-landing-story-play-toggle"
                    className="axo-v13-play-btn"
                    onClick={handleToggleAutoPlay}
                  >
                    {autoPlay
                      ? "Tạm dừng"
                      : activeStage >= V13_STORY_SCENES.length - 1
                        ? "Phát lại"
                        : "Tiếp tục"}
                  </button>
                </div>

                <Continuous3DStoryStage activeStage={activeStage} />

                <div className="axo-sp-story-bottom-bar">
                  <div className="axo-sp-story-metric-group">
                    {scene.stageChips.map((chip) => (
                      <span
                        key={chip.label}
                        className={
                          chip.emphasis === "result"
                            ? "axo-sp-story-metric-pill is-verified"
                            : "axo-sp-story-metric-pill"
                        }
                      >
                        {chip.label}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="axo-v13-story-copy-col">
              <div className="axo-v13-lead-tag">CÁCH AXO HOẠT ĐỘNG</div>
              <h2 id="landing-story-heading" className="axo-sp-section-title">
                Một bài toán, mở ra từng lớp không gian.
              </h2>
              <p className="axo-sp-section-lead">
                Camera dịch chuyển qua 4 chặng dựng trực tiếp khối lăng trụ đều ABC.A′B′C′ (a = 4)
                tới thiết diện MNPQ.
              </p>

              <div className="axo-v13-step-list" role="tablist" aria-label="Bốn chặng dựng hình">
                {V13_STORY_SCENES.map((item, idx) => {
                  const isActive = idx === activeStage;
                  return (
                    <button
                      key={item.id}
                      ref={(el) => {
                        stepRefs.current[idx] = el;
                      }}
                      type="button"
                      role="tab"
                      aria-selected={isActive}
                      data-story-index={idx}
                      id={`btn-landing-story-step-${idx}`}
                      className={
                        isActive ? "axo-v13-step-item is-active" : "axo-v13-step-item"
                      }
                      onClick={() => {
                        setAutoPlay(false);
                        setActiveStage(idx);
                      }}
                    >
                      <span className="axo-v13-step-label">{item.stepLabel}</span>
                      <span className="axo-v13-step-title">{item.title}</span>
                      <span className="axo-v13-step-desc">{item.narrative}</span>
                    </button>
                  );
                })}
              </div>

              <details className="axo-sp-story-math-disclosure">
                <summary>Chi tiết tọa độ &amp; kiểm chứng hình học</summary>
                <div className="axo-sp-story-math-body">
                  <p>{LANDING_PRISM_STORY_SPEC.problemText}</p>
                  <p>
                    Trung điểm M ∈ AB, N ∈ AC suy ra MN ∥ BC, MN = 2. Giao tuyến PQ ∥ BC với P ∈ CC′,
                    Q ∈ BB′ và PQ = 4 tạo hình thang cân MNPQ có diện tích {LANDING_PRISM_STORY_SPEC.equationText}.
                  </p>
                </div>
              </details>
            </div>
          </div>
        </section>

        {/* Viewport-windowed Interactive Demo keeps total active WebGL <= 2 */}
        <div id="v13-demo-slot" ref={demoSlotRef} className="axo-v13-demo-slot">
          {demoNearViewport ? (
            <LandingInteractiveDemo />
          ) : (
            <section
              id="trai-nghiem"
              className="axo-sp-demo-section"
              aria-labelledby="landing-demo-heading"
            >
              <div className="axo-sp-container axo-v13-demo-standby">
                <h2 id="landing-demo-heading" className="axo-sp-section-title">
                  Chạm &amp; xoay thử một bài toán mẫu
                </h2>
                <p className="axo-sp-section-lead">
                  Cuộn xuống khu vực này để nạp khung dựng hình 3D tương tác theo bài mẫu.
                </p>
              </div>
            </section>
          )}
        </div>

        <V13FinalCtaBand idSuffix="proto-b" />
      </main>

      <V13FooterBand />
    </div>
  );
}
