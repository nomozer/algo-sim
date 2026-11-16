import { useEffect, useMemo, useRef, useState } from "react";
import {
  LANDING_CUBE_SAMPLE,
  type Vec3Tuple,
} from "./landing-geometry-data";
import { SpatialSceneCanvas } from "./LandingHeroScene3D";

export const CLOSING_STORYBOARD_MS = 3400;
export const CLOSING_SECTION_FILL_OPACITY = 0.28;

export type ClosingStoryboardBeat =
  | "cube-solid"
  | "cutting-plane"
  | "intersection-trace"
  | "hexagon-settled";

export interface ClosingMotionState {
  readonly progress: number;
  readonly beat: ClosingStoryboardBeat;
  readonly milestoneIndex: number;
  readonly planeOpacity: number;
  readonly sectionProgress: number;
  readonly sectionFillOpacity: number;
  readonly cameraPos: Vec3Tuple;
  readonly settled: boolean;
  readonly reducedMotion: boolean;
}

export interface ClosingCompositionData {
  readonly cubeVertices: readonly Vec3Tuple[];
  readonly sectionVertices: readonly Vec3Tuple[];
  readonly planeNormal: Vec3Tuple;
  readonly planarResiduals: readonly number[];
  readonly sectionEdgeLengths: readonly number[];
  readonly midpointResiduals: readonly number[];
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

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

/**
 * Verifies geometric invariants of AXO's canonical closing cube-section model
 * (ABCD.A'B'C'D' sliced by plane (MNP) to form regular hexagon MNEPFQ).
 */
export function buildClosingCompositionData(): ClosingCompositionData {
  const pm = LANDING_CUBE_SAMPLE.pointMap;
  const cubeIds = [
    "A",
    "B",
    "C",
    "D",
    "A_prime",
    "B_prime",
    "C_prime",
    "D_prime",
  ] as const;
  const cubeVertices = cubeIds.map((id) => pm[id].domainXyz);
  const sectionVertices = LANDING_CUBE_SAMPLE.sectionLoop.map(
    (id) => pm[id].domainXyz,
  );

  // Domain plane -x + y + z = 2
  const nLen = Math.hypot(-1, 1, 1);
  const planeNormal: Vec3Tuple = [-1 / nLen, 1 / nLen, 1 / nLen];
  const planarResiduals = sectionVertices.map(
    ([x, y, z]) => Math.abs(-x + y + z - 2) / nLen,
  );

  const sectionEdgeLengths = sectionVertices.map((pt, i) => {
    const next = sectionVertices[(i + 1) % sectionVertices.length];
    return Math.hypot(next[0] - pt[0], next[1] - pt[1], next[2] - pt[2]);
  });

  const midpointPairs: readonly (readonly [string, string, string])[] = [
    ["M", "A", "D"],
    ["N", "C", "D"],
    ["E", "C", "C_prime"],
    ["P", "B_prime", "C_prime"],
    ["F", "A_prime", "B_prime"],
    ["Q", "A", "A_prime"],
  ];
  const midpointResiduals = midpointPairs.map(([midId, aId, bId]) => {
    const m = pm[midId].domainXyz;
    const a = pm[aId].domainXyz;
    const b = pm[bId].domainXyz;
    return Math.hypot(
      m[0] - (a[0] + b[0]) * 0.5,
      m[1] - (a[1] + b[1]) * 0.5,
      m[2] - (a[2] + b[2]) * 0.5,
    );
  });

  return {
    cubeVertices,
    sectionVertices,
    planeNormal,
    planarResiduals,
    sectionEdgeLengths,
    midpointResiduals,
  };
}

export function evaluateClosingStoryboard(
  elapsedMs: number,
  reducedMotion = false,
): ClosingMotionState {
  if (reducedMotion || elapsedMs >= CLOSING_STORYBOARD_MS) {
    return {
      progress: 1,
      beat: "hexagon-settled",
      milestoneIndex: 3,
      planeOpacity: 0.56,
      sectionProgress: 1,
      sectionFillOpacity: 0.92,
      cameraPos: [9.8, 6.2, -7.0],
      settled: true,
      reducedMotion,
    };
  }

  const p = clamp01(elapsedMs / CLOSING_STORYBOARD_MS);
  let beat: ClosingStoryboardBeat = "cube-solid";
  let milestoneIndex = 0;
  if (p >= 0.76) {
    beat = "hexagon-settled";
    milestoneIndex = 3;
  } else if (p >= 0.5) {
    beat = "intersection-trace";
    milestoneIndex = 2;
  } else if (p >= 0.24) {
    beat = "cutting-plane";
    milestoneIndex = 1;
  }

  const planeSweep = clampPhase(p, 0.22, 0.48);
  const trace = clampPhase(p, 0.46, 0.8);
  const fillT = clampPhase(p, 0.72, 0.98);
  const camT = clampPhase(p, 0.0, 0.92);

  const planeOpacity =
    planeSweep <= 0.01
      ? 0
      : fillT > 0.01
        ? lerp(0.74, 0.56, fillT)
        : 0.74 * planeSweep;

  return {
    progress: p,
    beat,
    milestoneIndex,
    planeOpacity,
    sectionProgress: trace,
    sectionFillOpacity: fillT * 0.92,
    cameraPos: [
      lerp(10.6, 9.8, camT),
      lerp(6.8, 6.2, camT),
      lerp(-7.8, -7.0, camT),
    ],
    settled: p >= 0.999,
    reducedMotion: false,
  };
}

const CLOSING_SECTION_LABELS = ["M", "N", "P", "E", "F", "Q"] as const;

export function LandingClosingScene3D() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [state, setState] = useState<ClosingMotionState>(() =>
    evaluateClosingStoryboard(0, false),
  );

  const composition = useMemo(() => buildClosingCompositionData(), []);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const mq = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    let isReduced = Boolean(mq?.matches);
    setReducedMotion(isReduced);

    if (isReduced) {
      setState(evaluateClosingStoryboard(CLOSING_STORYBOARD_MS, true));
    }

    let rafId = 0;
    let startedAt = 0;
    let settled = isReduced;
    let isInView = false;

    const stopLoop = () => {
      if (rafId !== 0) {
        window.cancelAnimationFrame(rafId);
        rafId = 0;
      }
    };

    const tick = (now: number) => {
      rafId = 0;
      if (document.hidden || isReduced || settled) return;
      if (startedAt === 0) startedAt = now;
      const next = evaluateClosingStoryboard(now - startedAt, false);
      setState(next);
      if (next.settled) {
        settled = true;
        return;
      }
      if (isInView) {
        rafId = window.requestAnimationFrame(tick);
      }
    };

    const startOrResume = () => {
      if (document.hidden || settled || isReduced) return;
      if (rafId === 0) {
        rafId = window.requestAnimationFrame(tick);
      }
    };

    const onMotionChange = (ev: MediaQueryListEvent) => {
      isReduced = ev.matches;
      setReducedMotion(isReduced);
      if (isReduced) {
        stopLoop();
        settled = true;
        setState(evaluateClosingStoryboard(CLOSING_STORYBOARD_MS, true));
      } else {
        settled = false;
        startedAt = performance.now();
        if (isInView) startOrResume();
      }
    };

    const onVisibility = () => {
      if (document.hidden) stopLoop();
      else if (isInView && !settled) startOrResume();
    };

    let io: IntersectionObserver | null = null;
    if (typeof IntersectionObserver !== "undefined" && containerRef.current) {
      io = new IntersectionObserver(
        (entries) => {
          const entry = entries[0];
          isInView = Boolean(entry?.isIntersecting);
          if (isInView) startOrResume();
          else stopLoop();
        },
        { threshold: 0.12 },
      );
      io.observe(containerRef.current);
    } else {
      isInView = true;
      startOrResume();
    }

    mq?.addEventListener?.("change", onMotionChange);
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      stopLoop();
      io?.disconnect();
      mq?.removeEventListener?.("change", onMotionChange);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, []);

  const milestone =
    LANDING_CUBE_SAMPLE.milestones[state.milestoneIndex] ??
    LANDING_CUBE_SAMPLE.milestones[3];

  const effectiveState = reducedMotion
    ? evaluateClosingStoryboard(CLOSING_STORYBOARD_MS, true)
    : state;

  return (
    <div
      id="landing-closing-scene3d"
      ref={containerRef}
      className="axo-v14-closing-visual"
      data-cta-visual="spatial-cube-hexagon-3d"
      data-closing-beat={effectiveState.beat}
      data-section-edges={composition.sectionVertices.length}
    >
      <SpatialSceneCanvas
        sample={LANDING_CUBE_SAMPLE}
        visiblePoints={milestone.visiblePoints}
        activePoints={milestone.activePoints}
        showGuideEdges={false}
        planeOpacity={effectiveState.planeOpacity}
        sectionProgress={effectiveState.sectionProgress}
        sectionFillOpacity={effectiveState.sectionFillOpacity}
        cameraPos={effectiveState.cameraPos}
        lookAt={[0, 0.04, 0]}
        subtlePointerParallax={true}
        frameless={true}
        pointTagFilter={CLOSING_SECTION_LABELS}
        presentation="v14"
        ariaLabel="Mô hình 3D hình lập phương ABCD.A′B′C′D′ với thiết diện lục giác MNEPFQ"
      />
    </div>
  );
}
