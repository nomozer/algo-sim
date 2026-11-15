import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type TouchEvent as ReactTouchEvent,
} from "react";
import { AnnotatedPhrase } from "./AnnotatedHeading";
import {
  LANDING_PRISM_STORY_SPEC,
  type Vec3Tuple,
} from "./landing-geometry-data";

export interface StoryStageV14Spec {
  readonly index: number;
  readonly shortNum: string;
  readonly desktopTag: string;
  readonly mobileShortTag: string;
  readonly title: string;
  readonly summary: string;
  readonly relationNote: string;
  readonly verifiedResult?: string;
  readonly camera: {
    readonly yaw: number;
    readonly pitch: number;
    readonly zoom: number;
    readonly extrude: number;
    readonly planeSweep: number;
    readonly parallelCue: number;
    readonly sectionFill: number;
  };
}

export const STORY_STAGES_V14: readonly StoryStageV14Spec[] = [
  {
    index: 0,
    shortNum: "1",
    desktopTag: "Từ đề bài",
    mobileShortTag: "Đề bài",
    title: "Ghim ba điểm gốc M, N, P trên đáy và cạnh bên",
    summary:
      "Axo phân tích giả thiết lăng trụ tam giác đều ABC.A′B′C′ cạnh 4 và ghim chuẩn xác ba trung điểm M ∈ AB, N ∈ AC, P ∈ CC′ ngay từ dữ kiện đầu vào.",
    relationNote: "M ∈ AB · N ∈ AC · P ∈ CC′",
    camera: {
      yaw: -0.44,
      pitch: 0.34,
      zoom: 0.94,
      extrude: 0.16,
      planeSweep: 0,
      parallelCue: 0,
      sectionFill: 0,
    },
  },
  {
    index: 1,
    shortNum: "2",
    desktopTag: "Dựng không gian",
    mobileShortTag: "Dựng hình",
    title: "Mở rộng khối đứng và định vị mặt phẳng (MNP)",
    summary:
      "Khối lăng trụ vươn lên nắp A′B′C′ cùng lúc mặt phẳng cắt (MNP) đi qua bộ ba điểm gốc hạ vào khối để xác định miền giao cắt.",
    relationNote: "Mặt phẳng (MNP): √3x + y − √3z = 2√3",
    camera: {
      yaw: -0.28,
      pitch: 0.27,
      zoom: 1.0,
      extrude: 1,
      planeSweep: 0.68,
      parallelCue: 0.35,
      sectionFill: 0,
    },
  },
  {
    index: 2,
    shortNum: "3",
    desktopTag: "Xác lập quan hệ",
    mobileShortTag: "Quan hệ",
    title: "Kéo giao tuyến song song MN // BC để chốt điểm Q",
    summary:
      "Đường trung bình MN song song BC trên mặt đáy. Do BC thuộc mặt bên (BCC′B′), giao tuyến qua P bắt buộc song song BC và cắt BB′ tại trung điểm Q.",
    relationNote: "MN // BC ⇒ PQ // BC · Q là trung điểm BB′",
    camera: {
      yaw: -0.14,
      pitch: 0.23,
      zoom: 1.03,
      extrude: 1,
      planeSweep: 1,
      parallelCue: 1,
      sectionFill: 0.32,
    },
  },
  {
    index: 3,
    shortNum: "4",
    desktopTag: "Kết quả",
    mobileShortTag: "Kết quả",
    title: "Khép kín thiết diện hình thang cân MNPQ",
    summary:
      "Bốn đoạn MN, NP, PQ, QM nối kín tạo thành hình thang cân đối xứng hoàn chỉnh và xác nhận kết quả hình học trực tiếp trên mô hình.",
    relationNote: "MN = 2 · PQ = 4 · MQ = NP = 2√2",
    verifiedResult: "S(MNPQ) = 3√7",
    camera: {
      yaw: 0.04,
      pitch: 0.21,
      zoom: 1.05,
      extrude: 1,
      planeSweep: 1,
      parallelCue: 1,
      sectionFill: 1,
    },
  },
];

interface ProjectedPoint2D {
  readonly x: number;
  readonly y: number;
  readonly z: number;
}

type PrismTweenState = StoryStageV14Spec["camera"];

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

export function projectPrismPoint3D(
  pt: Vec3Tuple,
  yaw: number,
  pitch: number,
  cx: number,
  cy: number,
  scale: number,
): ProjectedPoint2D {
  const cosY = Math.cos(yaw);
  const sinY = Math.sin(yaw);
  const x1 = pt[0] * cosY - pt[2] * sinY;
  const z1 = pt[0] * sinY + pt[2] * cosY;

  const cosP = Math.cos(pitch);
  const sinP = Math.sin(pitch);
  const y2 = pt[1] * cosP - z1 * sinP;
  const z2 = pt[1] * sinP + z1 * cosP;

  const camDist = 11.5;
  const persp = camDist / Math.max(3, camDist - z2);
  return {
    x: cx + x1 * scale * persp,
    y: cy - y2 * scale * persp,
    z: z2,
  };
}

function PrismEditorialStage({
  activeStage,
  onSwipePrev,
  onSwipeNext,
}: {
  readonly activeStage: number;
  readonly onSwipePrev: () => void;
  readonly onSwipeNext: () => void;
}) {
  const [vis, setVis] = useState<PrismTweenState>(
    () => (STORY_STAGES_V14[activeStage] ?? STORY_STAGES_V14[0]).camera,
  );
  const curRef = useRef<PrismTweenState>(vis);
  const rafRef = useRef<number>(0);
  const touchStartXRef = useRef<number | null>(null);

  useEffect(() => {
    const nextTarget = (STORY_STAGES_V14[activeStage] ?? STORY_STAGES_V14[0]).camera;
    const reduced =
      typeof window !== "undefined" &&
      Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches);

    if (typeof window === "undefined" || reduced) {
      curRef.current = nextTarget;
      setVis(nextTarget);
      return;
    }

    const startState = { ...curRef.current };
    const startMs = performance.now();
    const durationMs = 520;
    let alive = true;

    const tick = (nowMs: number) => {
      if (!alive) return;
      const linear = Math.min(1, Math.max(0, (nowMs - startMs) / durationMs));
      const eased = 1 - Math.pow(1 - linear, 3);
      const next: PrismTweenState = {
        yaw: lerp(startState.yaw, nextTarget.yaw, eased),
        pitch: lerp(startState.pitch, nextTarget.pitch, eased),
        zoom: lerp(startState.zoom, nextTarget.zoom, eased),
        extrude: lerp(startState.extrude, nextTarget.extrude, eased),
        planeSweep: lerp(startState.planeSweep, nextTarget.planeSweep, eased),
        parallelCue: lerp(startState.parallelCue, nextTarget.parallelCue, eased),
        sectionFill: lerp(startState.sectionFill, nextTarget.sectionFill, eased),
      };
      curRef.current = next;
      setVis(next);

      if (linear < 1) {
        rafRef.current = window.requestAnimationFrame(tick);
      } else {
        rafRef.current = 0;
      }
    };

    if (rafRef.current) {
      window.cancelAnimationFrame(rafRef.current);
      rafRef.current = 0;
    }
    rafRef.current = window.requestAnimationFrame(tick);

    return () => {
      alive = false;
      if (rafRef.current) {
        window.cancelAnimationFrame(rafRef.current);
        rafRef.current = 0;
      }
    };
  }, [activeStage]);

  const scene = useMemo(() => {
    const pMap = LANDING_PRISM_STORY_SPEC.pointMap;
    const baseY = pMap["A"].pos[1];
    const extrudeVec = (id: string): Vec3Tuple => {
      const p = pMap[id].pos;
      if (id === "A" || id === "B" || id === "C" || id === "M" || id === "N") {
        return p;
      }
      return [p[0], baseY + (p[1] - baseY) * vis.extrude, p[2]];
    };

    const coords: Record<string, Vec3Tuple> = {};
    for (const key of [
      "A",
      "B",
      "C",
      "A_prime",
      "B_prime",
      "C_prime",
      "M",
      "N",
      "P",
      "Q",
    ]) {
      coords[key] = extrudeVec(key);
    }

    const scale = 55 * vis.zoom;
    const cx = 300;
    const cy = 220;
    const proj: Record<string, ProjectedPoint2D> = {};
    for (const [k, v] of Object.entries(coords)) {
      proj[k] = projectPrismPoint3D(v, vis.yaw, vis.pitch, cx, cy, scale);
    }

    const centroidX =
      (proj["A"].x +
        proj["B"].x +
        proj["C"].x +
        proj["A_prime"].x +
        proj["B_prime"].x +
        proj["C_prime"].x) /
      6;
    const centroidY =
      (proj["A"].y +
        proj["B"].y +
        proj["C"].y +
        proj["A_prime"].y +
        proj["B_prime"].y +
        proj["C_prime"].y) /
      6;

    const edges = LANDING_PRISM_STORY_SPEC.solidEdges.map((edge) => {
      const a = proj[edge.from];
      const b = proj[edge.to];
      const isVertical =
        (edge.from === "A" && edge.to === "A_prime") ||
        (edge.from === "B" && edge.to === "B_prime") ||
        (edge.from === "C" && edge.to === "C_prime");
      const isTop = edge.from.includes("prime") && edge.to.includes("prime");
      const isBack = edge.from === "C" || edge.to === "C";
      let opacity = 0.84;
      if (isVertical || isTop) {
        opacity = Math.max(0.18, vis.extrude * 0.86);
      }
      const dashed = isBack || (vis.extrude < 0.65 && (isVertical || isTop));
      return {
        key: `${edge.from}-${edge.to}`,
        a,
        b,
        dashed,
        opacity,
      };
    });

    const liftY = (1 - vis.planeSweep) * 0.72;
    const planePolyPts = LANDING_PRISM_STORY_SPEC.planeQuad.map((q) =>
      projectPrismPoint3D(
        [q[0], q[1] + liftY, q[2]],
        vis.yaw,
        vis.pitch,
        cx,
        cy,
        scale,
      ),
    );

    const fmt = (pts: readonly ProjectedPoint2D[]) =>
      pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");

    const visibleIds = [
      "A",
      "B",
      "C",
      "A_prime",
      "B_prime",
      "C_prime",
      "M",
      "N",
      "P",
      "Q",
    ].filter((id) => {
      if (id === "Q") return vis.planeSweep > 0.25;
      if (id === "A_prime" || id === "B_prime" || id === "C_prime") {
        return vis.extrude > 0.65;
      }
      return true;
    });

    const labels = visibleIds.map((id) => {
      const pt = proj[id];
      const dx = pt.x - centroidX;
      const dy = pt.y - centroidY;
      const len = Math.max(1, Math.hypot(dx, dy));
      const pad = 16;
      return {
        id,
        label: pMap[id].label,
        role: pMap[id].role,
        px: pt.x,
        py: pt.y,
        lx: Math.min(574, Math.max(26, pt.x + (dx / len) * pad)),
        ly: Math.min(404, Math.max(24, pt.y + (dy / len) * pad + 4)),
      };
    });

    return {
      proj,
      edges,
      basePts: fmt([proj["A"], proj["B"], proj["C"]]),
      topPts: fmt([proj["A_prime"], proj["B_prime"], proj["C_prime"]]),
      planePts: fmt(planePolyPts),
      sectionPts: fmt([proj["M"], proj["N"], proj["P"], proj["Q"]]),
      labels,
    };
  }, [vis]);

  const handleTouchStart = useCallback((e: ReactTouchEvent<HTMLDivElement>) => {
    touchStartXRef.current = e.touches[0]?.clientX ?? null;
  }, []);

  const handleTouchEnd = useCallback(
    (e: ReactTouchEvent<HTMLDivElement>) => {
      const startX = touchStartXRef.current;
      touchStartXRef.current = null;
      const endX = e.changedTouches[0]?.clientX;
      if (startX === null || endX === undefined) return;
      const delta = endX - startX;
      if (delta <= -42) {
        onSwipeNext();
      } else if (delta >= 42) {
        onSwipePrev();
      }
    },
    [onSwipeNext, onSwipePrev],
  );

  const stage = STORY_STAGES_V14[activeStage] ?? STORY_STAGES_V14[0];

  return (
    <div
      id="landing-storytelling-scene"
      className="axo-v14-story-visual"
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      <svg
        className="axo-v14-story-svg"
        viewBox="0 0 600 430"
        role="img"
        aria-label={`Lăng trụ tam giác đều ABC.A′B′C′: ${stage.desktopTag}`}
      >
        <ellipse
          className="axo-v14-svg-contact-halo"
          cx="300"
          cy="346"
          rx="172"
          ry="22"
        />

        <polygon
          className="axo-v14-svg-prism-base"
          points={scene.basePts}
        />

        {vis.extrude > 0.35 && (
          <polygon
            className="axo-v14-svg-prism-top"
            points={scene.topPts}
            fillOpacity={(0.12 * vis.extrude).toFixed(3)}
          />
        )}

        {scene.edges.map((edge) => (
          <line
            key={edge.key}
            className={
              edge.dashed
                ? "axo-v14-svg-prism-edge-back"
                : "axo-v14-svg-prism-edge-front"
            }
            x1={edge.a.x}
            y1={edge.a.y}
            x2={edge.b.x}
            y2={edge.b.y}
            strokeOpacity={
              edge.dashed
                ? (edge.opacity * 0.56).toFixed(3)
                : edge.opacity.toFixed(3)
            }
          />
        ))}

        {vis.parallelCue > 0.04 && (
          <g opacity={vis.parallelCue.toFixed(3)}>
            <line
              className="axo-v14-svg-parallel-guide"
              x1={scene.proj["B"].x}
              y1={scene.proj["B"].y}
              x2={scene.proj["C"].x}
              y2={scene.proj["C"].y}
            />
            <line
              className="axo-v14-svg-parallel-guide"
              x1={scene.proj["M"].x}
              y1={scene.proj["M"].y}
              x2={scene.proj["N"].x}
              y2={scene.proj["N"].y}
            />
            {vis.planeSweep > 0.45 && (
              <line
                className="axo-v14-svg-parallel-guide"
                x1={scene.proj["P"].x}
                y1={scene.proj["P"].y}
                x2={scene.proj["Q"].x}
                y2={scene.proj["Q"].y}
              />
            )}
          </g>
        )}

        {vis.planeSweep > 0.02 && (
          <polygon
            className="axo-v14-svg-cutting-plane"
            points={scene.planePts}
            fillOpacity={(0.36 * vis.planeSweep).toFixed(3)}
            strokeOpacity={(0.78 * vis.planeSweep).toFixed(3)}
          />
        )}

        {vis.sectionFill > 0.02 && (
          <polygon
            className="axo-v14-svg-section-poly"
            points={scene.sectionPts}
            fillOpacity={(0.84 * vis.sectionFill).toFixed(3)}
            strokeOpacity={vis.sectionFill.toFixed(3)}
          />
        )}

        {scene.labels.map((item) => {
          const isSeed = item.role === "seed";
          const isInter = item.role === "intersection";
          const dotClass = isInter
            ? "axo-v14-svg-section-dot"
            : isSeed
              ? "axo-v14-svg-seed-dot"
              : "axo-v14-svg-vertex-dot";
          const textClass = isInter
            ? "axo-v14-svg-label-inter"
            : isSeed
              ? "axo-v14-svg-label-seed"
              : "axo-v14-svg-vertex-text";
          return (
            <g key={item.id}>
              <circle
                className={dotClass}
                cx={item.px}
                cy={item.py}
                r={isInter ? 4.4 : isSeed ? 3.8 : 2.9}
              />
              <text className={textClass} x={item.lx} y={item.ly}>
                {item.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export function LandingStorytellingV14() {
  const [activeStage, setActiveStage] = useState<number>(0);
  const current = STORY_STAGES_V14[activeStage] ?? STORY_STAGES_V14[0];
  const isFinalStage = activeStage === STORY_STAGES_V14.length - 1;

  const handleStageKeyDown = useCallback(
    (e: ReactKeyboardEvent<HTMLButtonElement>, idx: number) => {
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        setActiveStage(Math.min(STORY_STAGES_V14.length - 1, idx + 1));
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        setActiveStage(Math.max(0, idx - 1));
      } else if (e.key === "Home") {
        e.preventDefault();
        setActiveStage(0);
      } else if (e.key === "End") {
        e.preventDefault();
        setActiveStage(STORY_STAGES_V14.length - 1);
      }
    },
    [],
  );

  return (
    <section
      id="cach-hoat-dong"
      className="axo-v14-story"
      aria-labelledby="landing-story-heading"
    >
      <div className="axo-v14-story-shell">
        <div className="axo-v14-story-header">
          <h2 id="landing-story-heading" className="axo-v14-story-title">
            Theo dõi bài toán qua{" "}
            <AnnotatedPhrase variant="underline">
              từng lớp không gian
            </AnnotatedPhrase>
            .
          </h2>
          <p className="axo-v14-story-lead">
            Một mạch dựng liên tục trên lăng trụ tam giác đều ABC.A′B′C′ (cạnh a
            = 4): từ ba trung điểm gốc đến thiết diện hoàn chỉnh.
          </p>
        </div>

        <div className="axo-v14-story-grid">
          <div
            className="axo-v14-story-rail"
            role="tablist"
            aria-label="Các chặng dựng hình lăng trụ"
          >
            {STORY_STAGES_V14.map((stage, idx) => {
              const selected = idx === activeStage;
              return (
                <button
                  key={stage.shortNum}
                  id={`btn-landing-story-step-${idx}`}
                  type="button"
                  role="tab"
                  aria-selected={selected}
                  className={
                    selected
                      ? "axo-v14-story-step is-active"
                      : "axo-v14-story-step"
                  }
                  onClick={() => setActiveStage(idx)}
                  onKeyDown={(e) => handleStageKeyDown(e, idx)}
                >
                  <span className="axo-v14-story-step-dot" aria-hidden="true" />
                  <span className="axo-v14-story-step-meta">
                    <span className="axo-v14-story-step-num">
                      Chặng {stage.shortNum}
                    </span>
                    <span className="axo-v14-story-step-desktop-name">
                      {stage.desktopTag}
                    </span>
                    <span className="axo-v14-story-step-mobile-name">
                      {stage.mobileShortTag}
                    </span>
                  </span>
                </button>
              );
            })}
          </div>

          <PrismEditorialStage
            activeStage={activeStage}
            onSwipePrev={() => setActiveStage((s) => Math.max(0, s - 1))}
            onSwipeNext={() =>
              setActiveStage((s) =>
                Math.min(STORY_STAGES_V14.length - 1, s + 1),
              )
            }
          />

          <div
            className="axo-v14-story-readout"
            role="tabpanel"
            aria-labelledby={`btn-landing-story-step-${activeStage}`}
          >
            <div className="axo-v14-story-readout-tag">
              Chặng {current.shortNum} · {current.desktopTag}
            </div>
            <h3 className="axo-v14-story-readout-title">{current.title}</h3>
            <p className="axo-v14-story-readout-summary">{current.summary}</p>
            <div className="axo-v14-story-relation">
              <span className="axo-v14-story-relation-text">
                {current.relationNote}
              </span>
              {isFinalStage && current.verifiedResult ? (
                <AnnotatedPhrase
                  variant="highlight"
                  active={isFinalStage}
                  className="axo-v14-story-verified"
                >
                  {current.verifiedResult}
                </AnnotatedPhrase>
              ) : null}
            </div>

            <details className="axo-v14-story-proof">
              <summary>Xem kiểm chứng tọa độ chuẩn xác</summary>
              <p>
                Hệ trục chuẩn tại A(0; 0; 0), B(4; 0; 0), C(2; 2√3; 0),
                A′(0; 0; 4) cho phép xác định duy nhất mặt phẳng (MNP) với
                {isFinalStage
                  ? " thiết diện hình thang cân MNPQ, đáy MN = 2, PQ = 4 và diện tích S(MNPQ) = 3√7."
                  : " bộ điểm gốc M(2; 0; 0), N(1; √3; 0), P(2; 2√3; 2)."}
              </p>
            </details>
          </div>
        </div>
      </div>
    </section>
  );
}
