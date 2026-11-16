import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from "react";
import type { Vec3Tuple } from "./landing-geometry-data";

export const CLOSING_CYCLE_DURATION_MS = 9600;

export type ClosingMotionPhase =
  | "sphere-axis"
  | "plane-emergence"
  | "circle-intersection"
  | "complete-settled";

export interface ClosingMotionState {
  readonly cycleProgress: number;
  readonly phase: ClosingMotionPhase;
  readonly sphereOpacity: number;
  readonly axisProgress: number;
  readonly planeProgress: number;
  readonly traceProgress: number;
  readonly sectionFillOpacity: number;
  readonly triangleReveal: number;
  readonly orbitAngleRad: number;
  readonly reducedMotion: boolean;
}

export interface ClosingPointSpec {
  readonly id: string;
  readonly label: string;
  readonly role: "center" | "foot" | "circle_vertex";
  readonly domainXyz: Vec3Tuple;
  readonly pos: Vec3Tuple;
}

export interface ClosingSpatialRigData {
  readonly radiusR: number;
  readonly distanceD: number;
  readonly sectionRadiusR: number;
  readonly points: readonly ClosingPointSpec[];
  readonly pointMap: Readonly<Record<string, ClosingPointSpec>>;
  readonly circleSamples: readonly Vec3Tuple[];
  readonly planeQuadWorld: readonly Vec3Tuple[];
  readonly sphereMathResiduals: readonly number[];
  readonly orthoDotResidual: number;
  readonly pythagoreanResidual: number;
}

export interface ProjectedArcSegment {
  readonly key: string;
  readonly x1: number;
  readonly y1: number;
  readonly x2: number;
  readonly y2: number;
  readonly front: boolean;
}

export interface ProjectedClosingStage {
  readonly width: number;
  readonly height: number;
  readonly sphereCenter: { readonly x: number; readonly y: number; readonly rPx: number };
  readonly contactBase: { readonly x: number; readonly y: number; readonly rx: number; readonly ry: number };
  readonly meridianArcs: readonly ProjectedArcSegment[];
  readonly equatorArcs: readonly ProjectedArcSegment[];
  readonly equatorBackPath: string;
  readonly equatorFrontPath: string;
  readonly meridianBackPath: string;
  readonly meridianFrontPath: string;
  readonly planePolygonPoints: string;
  readonly planeLabelPos: { readonly x: number; readonly y: number };
  readonly sectionPolygonPoints: string;
  readonly circleArcs: readonly (ProjectedArcSegment & { readonly u: number })[];
  readonly circleBackPath: string;
  readonly circleFrontPath: string;
  readonly axisIH: { readonly x1: number; readonly y1: number; readonly x2: number; readonly y2: number };
  readonly radiusHA: { readonly x1: number; readonly y1: number; readonly x2: number; readonly y2: number };
  readonly slantIA: { readonly x1: number; readonly y1: number; readonly x2: number; readonly y2: number };
  readonly rightAnglePath: string;
  readonly points: Readonly<Record<string, { readonly x: number; readonly y: number; readonly label: string }>>;
}

function clamp01(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(1, value));
}

function smoothstep(edge0: number, edge1: number, x: number): number {
  const t = clamp01((x - edge0) / Math.max(1e-6, edge1 - edge0));
  return t * t * (3 - 2 * t);
}

/**
 * Sphere (S): center I(0, 0, 0), radius R = 5 in mathematical (x, y, z) domain.
 * Plane (P): z = 3 (distance d = |IH| = 3).
 * Intersection circle center H(0, 0, 3), exact radius r = sqrt(5^2 - 3^2) = 4.
 * Cardinal section points A(4, 0, 3), B(0, 4, 3), C(-4, 0, 3), D(0, -4, 3).
 * Mapping to view coordinates (X, Y, Z): (x, z, -y) so z domain is vertical +Y.
 */
function domainToView(domain: Vec3Tuple, scaleNorm = 0.42): Vec3Tuple {
  return [
    Number((domain[0] * scaleNorm).toFixed(5)),
    Number((domain[2] * scaleNorm).toFixed(5)),
    Number((-domain[1] * scaleNorm).toFixed(5)),
  ];
}

export function buildClosingSpatialRigData(): ClosingSpatialRigData {
  const radiusR = 5;
  const distanceD = 3;
  const sectionRadiusR = Math.sqrt(radiusR * radiusR - distanceD * distanceD); // exact 4

  const specs: readonly { id: string; label: string; role: ClosingPointSpec["role"]; xyz: Vec3Tuple }[] = [
    { id: "I", label: "I", role: "center", xyz: [0, 0, 0] },
    { id: "H", label: "H", role: "foot", xyz: [0, 0, 3] },
    { id: "A", label: "A", role: "circle_vertex", xyz: [4, 0, 3] },
    { id: "B", label: "B", role: "circle_vertex", xyz: [0, 4, 3] },
    { id: "C", label: "C", role: "circle_vertex", xyz: [-4, 0, 3] },
    { id: "D", label: "D", role: "circle_vertex", xyz: [0, -4, 3] },
  ];

  const points: ClosingPointSpec[] = specs.map((sp) => ({
    id: sp.id,
    label: sp.label,
    role: sp.role,
    domainXyz: sp.xyz,
    pos: domainToView(sp.xyz),
  }));
  const pointMap = Object.fromEntries(points.map((pt) => [pt.id, pt]));

  const sampleCount = 72;
  const circleSamples: Vec3Tuple[] = [];
  for (let i = 0; i < sampleCount; i++) {
    const theta = (i / sampleCount) * Math.PI * 2;
    const x = sectionRadiusR * Math.cos(theta);
    const y = sectionRadiusR * Math.sin(theta);
    circleSamples.push(domainToView([x, y, distanceD]));
  }

  const planeHalf = 5.45;
  const planeQuadWorld: Vec3Tuple[] = [
    domainToView([-planeHalf, -planeHalf, distanceD]),
    domainToView([planeHalf, -planeHalf, distanceD]),
    domainToView([planeHalf, planeHalf, distanceD]),
    domainToView([-planeHalf, planeHalf, distanceD]),
  ];

  // Verify mathematical invariants in domain coordinates
  const circleVertices = points.filter((p) => p.role === "circle_vertex");
  const sphereMathResiduals = circleVertices.map((p) => {
    const [x, y, z] = p.domainXyz;
    return Math.abs(x * x + y * y + z * z - radiusR * radiusR);
  });

  const vecIH: Vec3Tuple = [
    pointMap["H"].domainXyz[0] - pointMap["I"].domainXyz[0],
    pointMap["H"].domainXyz[1] - pointMap["I"].domainXyz[1],
    pointMap["H"].domainXyz[2] - pointMap["I"].domainXyz[2],
  ];
  const vecHA: Vec3Tuple = [
    pointMap["A"].domainXyz[0] - pointMap["H"].domainXyz[0],
    pointMap["A"].domainXyz[1] - pointMap["H"].domainXyz[1],
    pointMap["A"].domainXyz[2] - pointMap["H"].domainXyz[2],
  ];
  const vecIA: Vec3Tuple = [
    pointMap["A"].domainXyz[0] - pointMap["I"].domainXyz[0],
    pointMap["A"].domainXyz[1] - pointMap["I"].domainXyz[1],
    pointMap["A"].domainXyz[2] - pointMap["I"].domainXyz[2],
  ];
  const orthoDotResidual = Math.abs(
    vecIH[0] * vecHA[0] + vecIH[1] * vecHA[1] + vecIH[2] * vecHA[2],
  );
  const lenIH2 = vecIH[0] ** 2 + vecIH[1] ** 2 + vecIH[2] ** 2;
  const lenHA2 = vecHA[0] ** 2 + vecHA[1] ** 2 + vecHA[2] ** 2;
  const lenIA2 = vecIA[0] ** 2 + vecIA[1] ** 2 + vecIA[2] ** 2;
  const pythagoreanResidual = Math.abs(lenIH2 + lenHA2 - lenIA2);

  return {
    radiusR,
    distanceD,
    sectionRadiusR,
    points,
    pointMap,
    circleSamples,
    planeQuadWorld,
    sphereMathResiduals,
    orthoDotResidual,
    pythagoreanResidual,
  };
}

export function evaluateClosingMotionState(
  elapsedMs: number,
  reducedMotion: boolean,
  previewOverride: "mid" | "settled" | null = null,
): ClosingMotionState {
  if (reducedMotion || previewOverride === "settled") {
    return {
      cycleProgress: 0.78,
      phase: "complete-settled",
      sphereOpacity: 1,
      axisProgress: 1,
      planeProgress: 1,
      traceProgress: 1,
      sectionFillOpacity: 1,
      triangleReveal: 1,
      orbitAngleRad: 0,
      reducedMotion: Boolean(reducedMotion),
    };
  }

  if (previewOverride === "mid") {
    return {
      cycleProgress: 0.56,
      phase: "circle-intersection",
      sphereOpacity: 1,
      axisProgress: 1,
      planeProgress: 1,
      traceProgress: 0.68,
      sectionFillOpacity: 0.42,
      triangleReveal: 0.86,
      orbitAngleRad: -0.06,
      reducedMotion: false,
    };
  }

  const safeMs = ((elapsedMs % CLOSING_CYCLE_DURATION_MS) + CLOSING_CYCLE_DURATION_MS) % CLOSING_CYCLE_DURATION_MS;
  const t = safeMs / CLOSING_CYCLE_DURATION_MS;

  let phase: ClosingMotionPhase = "sphere-axis";
  if (t >= 0.68) phase = "complete-settled";
  else if (t >= 0.44) phase = "circle-intersection";
  else if (t >= 0.2) phase = "plane-emergence";

  const resetOut = t >= 0.9 ? 1 - smoothstep(0.9, 1.0, t) : 1;

  const sphereOpacity = (0.35 + 0.65 * smoothstep(0.0, 0.14, t)) * (t >= 0.9 ? 0.35 + 0.65 * resetOut : 1);
  const axisProgress = smoothstep(0.04, 0.2, t) * resetOut;
  const planeProgress = smoothstep(0.2, 0.42, t) * resetOut;
  const traceProgress = smoothstep(0.44, 0.68, t) * resetOut;
  const triangleReveal = smoothstep(0.46, 0.72, t) * resetOut;
  const sectionFillOpacity = smoothstep(0.58, 0.76, t) * resetOut;
  const orbitAngleRad = Math.sin(t * Math.PI * 2) * 0.14;

  return {
    cycleProgress: t,
    phase,
    sphereOpacity,
    axisProgress,
    planeProgress,
    traceProgress,
    sectionFillOpacity,
    triangleReveal,
    orbitAngleRad,
    reducedMotion: false,
  };
}

function projectPoint3D(
  pt: Vec3Tuple,
  yaw: number,
  pitch: number,
  cx: number,
  cy: number,
  scale: number,
): { x: number; y: number; z: number } {
  const cosY = Math.cos(yaw);
  const sinY = Math.sin(yaw);
  const x1 = pt[0] * cosY - pt[2] * sinY;
  const z1 = pt[0] * sinY + pt[2] * cosY;

  const cosP = Math.cos(pitch);
  const sinP = Math.sin(pitch);
  const y2 = pt[1] * cosP - z1 * sinP;
  const z2 = pt[1] * sinP + z1 * cosP;

  const camDist = 11.2;
  const persp = camDist / Math.max(3, camDist - z2);
  return {
    x: cx + x1 * scale * persp,
    y: cy - y2 * scale * persp,
    z: z2,
  };
}

function buildRingSegments(
  pts: readonly Vec3Tuple[],
  prefix: string,
  yaw: number,
  pitch: number,
  cx: number,
  cy: number,
  scale: number,
): ProjectedArcSegment[] {
  const projected = pts.map((pt) => projectPoint3D(pt, yaw, pitch, cx, cy, scale));
  const out: ProjectedArcSegment[] = [];
  for (let i = 0; i < projected.length; i++) {
    const a = projected[i];
    const b = projected[(i + 1) % projected.length];
    const midZ = (a.z + b.z) * 0.5;
    out.push({
      key: `${prefix}-${i}`,
      x1: a.x,
      y1: a.y,
      x2: b.x,
      y2: b.y,
      front: midZ >= -0.02,
    });
  }
  return out;
}

const CLOSING_RIG_SINGLETON = buildClosingSpatialRigData();

function arcsToSvgPath(segs: readonly ProjectedArcSegment[]): string {
  if (segs.length === 0) return "";
  const parts: string[] = [];
  let prevX = Number.NaN;
  let prevY = Number.NaN;
  for (const s of segs) {
    const x1s = s.x1.toFixed(1);
    const y1s = s.y1.toFixed(1);
    const x2s = s.x2.toFixed(1);
    const y2s = s.y2.toFixed(1);
    const continuous =
      Number.isFinite(prevX) &&
      Math.abs(s.x1 - prevX) < 0.05 &&
      Math.abs(s.y1 - prevY) < 0.05;
    parts.push(continuous ? `L ${x2s} ${y2s}` : `M ${x1s} ${y1s} L ${x2s} ${y2s}`);
    prevX = s.x2;
    prevY = s.y2;
  }
  return parts.join(" ");
}

export function projectClosingSpatialStage(
  width = 480,
  height = 360,
  state: ClosingMotionState = evaluateClosingMotionState(0, true),
  tiltX = 0,
  tiltY = 0,
): ProjectedClosingStage {
  const rig = CLOSING_RIG_SINGLETON;
  const scaleNorm = 0.42;
  const radiusView = rig.radiusR * scaleNorm; // 2.1
  const cx = width * 0.5;
  const cy = height * 0.48;
  const scale = Math.min(width, height) * 0.175;
  const yaw = -0.34 + state.orbitAngleRad + tiltX * 0.28;
  const pitch = 0.31 + tiltY * 0.18;

  const proj = (pt: Vec3Tuple) => projectPoint3D(pt, yaw, pitch, cx, cy, scale);

  const centerP = proj(rig.pointMap["I"].pos);
  const contactP = proj(domainToView([0, 0, -rig.radiusR]));
  const rPx = radiusView * scale * (11.2 / (11.2 - centerP.z));

  // Great circle curves on sphere S(I, R)
  const ringSteps = 64;
  const equatorRaw: Vec3Tuple[] = [];
  const meridianRaw: Vec3Tuple[] = [];
  for (let i = 0; i < ringSteps; i++) {
    const theta = (i / ringSteps) * Math.PI * 2;
    equatorRaw.push(
      domainToView([
        rig.radiusR * Math.cos(theta),
        rig.radiusR * Math.sin(theta),
        0,
      ]),
    );
    meridianRaw.push(
      domainToView([
        rig.radiusR * Math.sin(theta) * Math.cos(0.32),
        rig.radiusR * Math.sin(theta) * Math.sin(0.32),
        rig.radiusR * Math.cos(theta),
      ]),
    );
  }

  const equatorArcs = buildRingSegments(equatorRaw, "eq", yaw, pitch, cx, cy, scale);
  const meridianArcs = buildRingSegments(meridianRaw, "mer", yaw, pitch, cx, cy, scale);

  const liftView = (1 - state.planeProgress) * 0.72;
  const planeProj = rig.planeQuadWorld.map((pt) =>
    proj([pt[0], pt[1] + liftView, pt[2]]),
  );
  const planePolygonPoints = planeProj
    .map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`)
    .join(" ");

  const circleProj = rig.circleSamples.map((pt) => proj(pt));
  const sectionPolygonPoints = circleProj
    .map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`)
    .join(" ");

  const nCirc = rig.circleSamples.length;
  const circleArcs = rig.circleSamples.map((pt, i) => {
    const nextPt = rig.circleSamples[(i + 1) % nCirc];
    const p0 = projectPoint3D(pt, yaw, pitch, cx, cy, scale);
    const p1 = projectPoint3D(nextPt, yaw, pitch, cx, cy, scale);
    const u = clamp01(state.traceProgress * nCirc - i);
    const midZ = (p0.z + p1.z) * 0.5;
    return {
      key: `circ-${i}`,
      x1: p0.x,
      y1: p0.y,
      x2: p0.x + (p1.x - p0.x) * u,
      y2: p0.y + (p1.y - p0.y) * u,
      front: midZ >= -0.02,
      u,
    };
  });

  const pI = proj(rig.pointMap["I"].pos);
  const pH = proj(rig.pointMap["H"].pos);
  const pA = proj(rig.pointMap["A"].pos);

  // Right angle marker at H between H->I (down) and H->A (+x)
  const bSize = 0.58;
  const pHb1 = proj(domainToView([bSize, 0, 3]));
  const pHb2 = proj(domainToView([0, 0, 3 - bSize]));
  const pHbc = proj(domainToView([bSize, 0, 3 - bSize]));

  const mappedPoints: Record<string, { x: number; y: number; label: string }> = {};
  for (const pt of rig.points) {
    const p2 = proj(pt.pos);
    mappedPoints[pt.id] = { x: p2.x, y: p2.y, label: pt.label };
  }

  return {
    width,
    height,
    sphereCenter: { x: centerP.x, y: centerP.y, rPx },
    contactBase: {
      x: contactP.x,
      y: Math.min(height - 20, contactP.y + 12),
      rx: rPx * 0.72,
      ry: rPx * 0.14,
    },
    meridianArcs,
    equatorArcs,
    equatorBackPath: arcsToSvgPath(equatorArcs.filter((s) => !s.front)),
    equatorFrontPath: arcsToSvgPath(equatorArcs.filter((s) => s.front)),
    meridianBackPath: arcsToSvgPath(meridianArcs.filter((s) => !s.front)),
    meridianFrontPath: arcsToSvgPath(meridianArcs.filter((s) => s.front)),
    planePolygonPoints,
    planeLabelPos: {
      x: planeProj[2].x - 16,
      y: planeProj[2].y - 10,
    },
    sectionPolygonPoints,
    circleArcs,
    circleBackPath: arcsToSvgPath(circleArcs.filter((s) => !s.front && s.u > 0.01)),
    circleFrontPath: arcsToSvgPath(circleArcs.filter((s) => s.front && s.u > 0.01)),
    axisIH: {
      x1: pI.x,
      y1: pI.y,
      x2: pI.x + (pH.x - pI.x) * state.axisProgress,
      y2: pI.y + (pH.y - pI.y) * state.axisProgress,
    },
    radiusHA: {
      x1: pH.x,
      y1: pH.y,
      x2: pH.x + (pA.x - pH.x) * state.triangleReveal,
      y2: pH.y + (pA.y - pH.y) * state.triangleReveal,
    },
    slantIA: {
      x1: pI.x,
      y1: pI.y,
      x2: pI.x + (pA.x - pI.x) * state.triangleReveal,
      y2: pI.y + (pA.y - pI.y) * state.triangleReveal,
    },
    rightAnglePath: `M ${pHb1.x.toFixed(1)} ${pHb1.y.toFixed(1)} L ${pHbc.x.toFixed(1)} ${pHbc.y.toFixed(1)} L ${pHb2.x.toFixed(1)} ${pHb2.y.toFixed(1)}`,
    points: mappedPoints,
  };
}

function readPreviewPhaseOverride(): "mid" | "settled" | null {
  if (typeof window === "undefined") return null;
  const val = new URLSearchParams(window.location.search)
    .get("closing_phase")
    ?.trim()
    .toLowerCase();
  if (val === "mid" || val === "settled") return val;
  return null;
}

export function LandingClosingScene3D() {
  const stageRef = useRef<HTMLDivElement | null>(null);
  const wakeRef = useRef<(() => void) | null>(null);
  const targetTiltRef = useRef({ x: 0, y: 0 });
  const curTiltRef = useRef({ x: 0, y: 0 });

  const [frameState, setFrameState] = useState<{
    readonly motionState: ClosingMotionState;
    readonly tilt: { readonly x: number; readonly y: number };
  }>(() => ({
    motionState: evaluateClosingMotionState(
      0,
      true,
      readPreviewPhaseOverride() ?? "settled",
    ),
    tilt: { x: 0, y: 0 },
  }));
  const { motionState, tilt } = frameState;

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stage = stageRef.current;
    if (!stage) return;

    const previewOverride = readPreviewPhaseOverride();
    const reducedQuery = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    let reducedMotion = Boolean(reducedQuery?.matches);

    let disposed = false;
    let isInView = false;
    let rafId = 0;
    const startMs = performance.now();

    const stepFrame = (nowMs: number) => {
      if (disposed) return;
      const nextMotion = evaluateClosingMotionState(
        nowMs - startMs,
        reducedMotion,
        previewOverride,
      );

      const damp = reducedMotion ? 1 : 0.14;
      const nx =
        curTiltRef.current.x + (targetTiltRef.current.x - curTiltRef.current.x) * damp;
      const ny =
        curTiltRef.current.y + (targetTiltRef.current.y - curTiltRef.current.y) * damp;
      curTiltRef.current = { x: nx, y: ny };
      setFrameState({
        motionState: nextMotion,
        tilt: { x: nx, y: ny },
      });
    };

    const tick = (nowMs: number) => {
      rafId = 0;
      if (disposed || !isInView || document.hidden) return;
      stepFrame(nowMs);
      const tiltMoving =
        Math.abs(targetTiltRef.current.x - curTiltRef.current.x) > 0.001 ||
        Math.abs(targetTiltRef.current.y - curTiltRef.current.y) > 0.001;
      if ((!reducedMotion && previewOverride === null) || tiltMoving) {
        rafId = window.requestAnimationFrame(tick);
      }
    };

    const wake = () => {
      if (disposed || !isInView || document.hidden) return;
      if (reducedMotion || previewOverride !== null) {
        stepFrame(performance.now());
        return;
      }
      if (rafId === 0) {
        rafId = window.requestAnimationFrame(tick);
      }
    };

    wakeRef.current = wake;

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

    if (io) {
      io.observe(stage);
    } else {
      isInView = true;
      stepFrame(performance.now());
    }

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
      stepFrame(performance.now());
      if (!reducedMotion && isInView) wake();
    };
    reducedQuery?.addEventListener?.("change", onMotionChange);

    return () => {
      disposed = true;
      wakeRef.current = null;
      if (rafId) window.cancelAnimationFrame(rafId);
      io?.disconnect();
      document.removeEventListener("visibilitychange", onVisibility);
      reducedQuery?.removeEventListener?.("change", onMotionChange);
    };
  }, []);

  const projection = useMemo(
    () => projectClosingSpatialStage(480, 360, motionState, tilt.x, tilt.y),
    [motionState, tilt.x, tilt.y],
  );

  const ptI = projection.points["I"];
  const ptH = projection.points["H"];
  const ptA = projection.points["A"];

  const handlePointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches) return;
    const rect = event.currentTarget.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const nx = (event.clientX - rect.left) / rect.width - 0.5;
    const ny = (event.clientY - rect.top) / rect.height - 0.5;
    targetTiltRef.current = { x: nx * 0.48, y: -ny * 0.28 };
    wakeRef.current?.();
  };

  const handlePointerLeave = () => {
    targetTiltRef.current = { x: 0, y: 0 };
    wakeRef.current?.();
  };

  return (
    <div
      ref={stageRef}
      id="landing-closing-scene3d"
      className="axo-v14-closing-stage"
      role="img"
      aria-label="Mặt cầu S tâm I bán kính R = 5 cắt bởi mặt phẳng (P) tạo đường tròn giao tuyến tâm H bán kính r = 4"
      data-cta-visual="analytical-3d-svg"
      data-cta-phase={motionState.phase}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
    >
      <svg
        className="axo-v14-closing-svg"
        viewBox={`0 0 ${projection.width} ${projection.height}`}
        aria-hidden="true"
        focusable="false"
      >
        <ellipse
          className="axo-v14-svg-contact-halo"
          cx={projection.contactBase.x}
          cy={projection.contactBase.y}
          rx={projection.contactBase.rx}
          ry={projection.contactBase.ry}
          opacity={motionState.sphereOpacity}
        />

        <circle
          className="axo-v14-svg-sphere-shell"
          cx={projection.sphereCenter.x}
          cy={projection.sphereCenter.y}
          r={projection.sphereCenter.rPx}
          opacity={motionState.sphereOpacity}
        />

        {/* Back hemisphere great-circle guides (dashed) */}
        <g opacity={motionState.sphereOpacity}>
          {projection.equatorBackPath ? (
            <path
              className="axo-v14-svg-sphere-arc-back"
              d={projection.equatorBackPath}
              fill="none"
            />
          ) : null}
          {projection.meridianBackPath ? (
            <path
              className="axo-v14-svg-sphere-arc-back"
              d={projection.meridianBackPath}
              fill="none"
            />
          ) : null}
        </g>

        {/* Cutting plane (P): z = 3 */}
        {motionState.planeProgress > 0.02 && (
          <polygon
            className="axo-v14-svg-cutting-plane"
            points={projection.planePolygonPoints}
            fillOpacity={(0.24 * motionState.planeProgress).toFixed(3)}
            strokeOpacity={(0.76 * motionState.planeProgress).toFixed(3)}
          />
        )}

        {/* Shaded intersection disk (C) = (S) intersect (P) */}
        {motionState.sectionFillOpacity > 0.02 && (
          <polygon
            className="axo-v14-svg-sphere-section-fill"
            points={projection.sectionPolygonPoints}
            fillOpacity={(0.36 * motionState.sectionFillOpacity).toFixed(3)}
          />
        )}

        {/* Back arc of intersection circle (dashed amber) */}
        {projection.circleBackPath ? (
          <path
            className="axo-v14-svg-sphere-circle-back"
            d={projection.circleBackPath}
            fill="none"
          />
        ) : null}

        {/* Orthogonal distance axis IH, radius HA, and sphere radius IA (3-4-5 right triangle) */}
        {motionState.axisProgress > 0.02 && (
          <line
            className="axo-v14-svg-edge-altitude"
            x1={projection.axisIH.x1}
            y1={projection.axisIH.y1}
            x2={projection.axisIH.x2}
            y2={projection.axisIH.y2}
          />
        )}

        {motionState.planeProgress > 0.7 && (
          <path
            className="axo-v14-svg-edge-altitude"
            d={projection.rightAnglePath}
            fill="none"
            opacity={((motionState.planeProgress - 0.7) / 0.3).toFixed(3)}
          />
        )}

        {motionState.triangleReveal > 0.02 && (
          <g opacity={motionState.triangleReveal.toFixed(3)}>
            <line
              className="axo-v14-svg-sphere-radius"
              x1={projection.radiusHA.x1}
              y1={projection.radiusHA.y1}
              x2={projection.radiusHA.x2}
              y2={projection.radiusHA.y2}
            />
            <line
              className="axo-v14-svg-sphere-slant"
              x1={projection.slantIA.x1}
              y1={projection.slantIA.y1}
              x2={projection.slantIA.x2}
              y2={projection.slantIA.y2}
            />
          </g>
        )}

        {/* Front hemisphere great-circle arcs */}
        <g opacity={motionState.sphereOpacity}>
          {projection.equatorFrontPath ? (
            <path
              className="axo-v14-svg-sphere-arc-front"
              d={projection.equatorFrontPath}
              fill="none"
            />
          ) : null}
          {projection.meridianFrontPath ? (
            <path
              className="axo-v14-svg-sphere-arc-front"
              d={projection.meridianFrontPath}
              fill="none"
            />
          ) : null}
        </g>

        {/* Front arc of intersection circle (crisp amber) */}
        {projection.circleFrontPath ? (
          <path
            className="axo-v14-svg-sphere-circle-front"
            d={projection.circleFrontPath}
            fill="none"
          />
        ) : null}

        {/* Anchors & sparse labels: I, H, A */}
        {ptI && (
          <g opacity={motionState.sphereOpacity}>
            <circle className="axo-v14-svg-vertex-dot" cx={ptI.x} cy={ptI.y} r="3.4" />
            <text className="axo-v14-svg-vertex-text" x={ptI.x - 13} y={ptI.y + 4}>
              I
            </text>
          </g>
        )}

        {ptH && motionState.axisProgress > 0.65 && (
          <g opacity={((motionState.axisProgress - 0.65) / 0.35).toFixed(3)}>
            <circle className="axo-v14-svg-seed-dot" cx={ptH.x} cy={ptH.y} r="4.0" />
            <text className="axo-v14-svg-label-seed" x={ptH.x - 13} y={ptH.y - 8}>
              H
            </text>
          </g>
        )}

        {ptA && motionState.triangleReveal > 0.7 && (
          <g opacity={((motionState.triangleReveal - 0.7) / 0.3).toFixed(3)}>
            <circle className="axo-v14-svg-section-dot" cx={ptA.x} cy={ptA.y} r="4.2" />
            <text className="axo-v14-svg-label-inter" x={ptA.x + 13} y={ptA.y + 4}>
              A
            </text>
          </g>
        )}

        {motionState.planeProgress > 0.55 && (
          <text
            className="axo-v14-svg-label-seed"
            x={projection.planeLabelPos.x}
            y={projection.planeLabelPos.y}
            opacity={motionState.planeProgress.toFixed(3)}
          >
            (P)
          </text>
        )}
      </svg>
    </div>
  );
}
