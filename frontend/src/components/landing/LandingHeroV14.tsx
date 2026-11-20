import { useCallback, useEffect, useMemo, useState, type MouseEvent as ReactMouseEvent } from "react";
import { useAuthStore } from "../../state/auth";
import {
  LANDING_CUBE_SAMPLE,
  enterAxoWorkspace,
  type Vec3Tuple,
} from "./landing-geometry-data";

export interface MinimalHeroStepSpec {
  readonly id: "premise" | "plane" | "section";
  readonly shortLabel: string;
  readonly statusBadge: string;
}

export const AXO_MINIMAL_HERO_STEPS: readonly MinimalHeroStepSpec[] = [
  {
    id: "premise",
    shortLabel: "1. Giả thiết",
    statusBadge: "M, N, P",
  },
  {
    id: "plane",
    shortLabel: "2. Mặt (MNP)",
    statusBadge: "Cắt 6 cạnh",
  },
  {
    id: "section",
    shortLabel: "3. Thiết diện",
    statusBadge: "Lục giác đều",
  },
];

interface ProjectedPoint {
  readonly x: number;
  readonly y: number;
  readonly depth: number;
}

interface ProjectedFace {
  readonly key: string;
  readonly pointsAttr: string;
  readonly depth: number;
  readonly shade: "top" | "left" | "right" | "back";
}

interface ProjectedEdge {
  readonly key: string;
  readonly x1: number;
  readonly y1: number;
  readonly x2: number;
  readonly y2: number;
  readonly kind: "hidden" | "outer" | "crease";
}

const HERO_VIEWBOX_W = 540;
const HERO_VIEWBOX_H = 415;
const HERO_CAM_POS: Vec3Tuple = [8.6, 5.4, 7.8];
const HERO_LOOK_AT: Vec3Tuple = [0, -0.1, 0];
const HERO_PROJ_SCALE = 735;

const CUBE_HIDDEN_EDGE_VERTEX = "D";
const CUBE_FRONT_CREASE_EDGE = new Set(["B-B_prime", "B_prime-B", "A_prime-B_prime", "B_prime-A_prime", "B_prime-C_prime", "C_prime-B_prime"]);

function sub3(a: Vec3Tuple, b: Vec3Tuple): Vec3Tuple {
  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
}

function dot3(a: Vec3Tuple, b: Vec3Tuple): number {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

function cross3(a: Vec3Tuple, b: Vec3Tuple): Vec3Tuple {
  return [
    a[1] * b[2] - a[2] * b[1],
    a[2] * b[0] - a[0] * b[2],
    a[0] * b[1] - a[1] * b[0],
  ];
}

function normalize3(v: Vec3Tuple): Vec3Tuple {
  const len = Math.hypot(v[0], v[1], v[2]) || 1;
  return [v[0] / len, v[1] / len, v[2] / len];
}

function buildCubeHeroGeometry() {
  const forward = normalize3(sub3(HERO_LOOK_AT, HERO_CAM_POS));
  const right = normalize3(cross3(forward, [0, 1, 0]));
  const up = cross3(right, forward);

  const projectPoint = (p: Vec3Tuple): ProjectedPoint => {
    const d = sub3(p, HERO_CAM_POS);
    const cz = Math.max(0.5, dot3(d, forward));
    const cx = dot3(d, right);
    const cy = dot3(d, up);
    return {
      x: HERO_VIEWBOX_W / 2 + (cx / cz) * HERO_PROJ_SCALE,
      y: HERO_VIEWBOX_H / 2 - (cy / cz) * HERO_PROJ_SCALE - 10,
      depth: cz,
    };
  };

  const { pointMap, solidFaces, solidEdges, planeQuad, sectionLoop } = LANDING_CUBE_SAMPLE;

  const projectedPoints = Object.fromEntries(
    Object.entries(pointMap).map(([id, spec]) => [id, projectPoint(spec.pos)]),
  ) as Record<string, ProjectedPoint>;

  const faceDefinitions: readonly {
    readonly key: string;
    readonly ids: readonly string[];
    readonly shade: ProjectedFace["shade"];
  }[] = [
    { key: "back-cd", ids: solidFaces[4], shade: "back" },
    { key: "back-da", ids: solidFaces[5], shade: "back" },
    { key: "base", ids: solidFaces[0], shade: "back" },
    { key: "left", ids: solidFaces[2], shade: "left" },
    { key: "right", ids: solidFaces[3], shade: "right" },
    { key: "top", ids: solidFaces[1], shade: "top" },
  ];

  const faces: ProjectedFace[] = faceDefinitions
    .map((fd) => {
      const worldPts = fd.ids.map((id) => pointMap[id].pos);
      const center: Vec3Tuple = [
        worldPts.reduce((acc, p) => acc + p[0], 0) / worldPts.length,
        worldPts.reduce((acc, p) => acc + p[1], 0) / worldPts.length,
        worldPts.reduce((acc, p) => acc + p[2], 0) / worldPts.length,
      ];
      const depth = dot3(sub3(center, HERO_CAM_POS), forward);
      const pts2d = fd.ids.map((id) => projectedPoints[id]);
      return {
        key: fd.key,
        pointsAttr: pts2d.map((pt) => `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`).join(" "),
        depth,
        shade: fd.shade,
      };
    })
    .sort((a, b) => b.depth - a.depth);

  const edges: ProjectedEdge[] = solidEdges
    .map((e) => {
      const p1 = projectedPoints[e.from];
      const p2 = projectedPoints[e.to];
      const edgeKey = `${e.from}-${e.to}`;
      const isHidden = e.from === CUBE_HIDDEN_EDGE_VERTEX || e.to === CUBE_HIDDEN_EDGE_VERTEX;
      const kind: ProjectedEdge["kind"] = isHidden
        ? "hidden"
        : CUBE_FRONT_CREASE_EDGE.has(edgeKey)
          ? "crease"
          : "outer";
      return {
        key: edgeKey,
        x1: p1.x,
        y1: p1.y,
        x2: p2.x,
        y2: p2.y,
        kind,
      };
    });

  const planePts = planeQuad.map(projectPoint);
  const planeAttr = planePts.map((pt) => `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`).join(" ");

  const sectionPts = sectionLoop.map((id) => ({
    id,
    label: pointMap[id].label,
    role: pointMap[id].role,
    ...projectedPoints[id],
  }));
  const sectionAttr = sectionPts.map((pt) => `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`).join(" ");

  const secCx = sectionPts.reduce((s, p) => s + p.x, 0) / sectionPts.length;
  const secCy = sectionPts.reduce((s, p) => s + p.y, 0) / sectionPts.length;

  const sectionPointsWithLabels = sectionPts.map((pt) => {
    const dx = pt.x - secCx;
    const dy = pt.y - secCy;
    const len = Math.hypot(dx, dy) || 1;
    const pad = pt.id === "P" || pt.id === "F" ? 19 : 21;
    return {
      ...pt,
      lx: pt.x + (dx / len) * pad,
      ly: pt.y + (dy / len) * pad + 4,
    };
  });

  const bottomShadowY = projectedPoints.B.y + 12;
  const bottomShadowX = projectedPoints.B.x;

  return {
    faces,
    edges,
    planeAttr,
    sectionAttr,
    sectionPoints: sectionPointsWithLabels,
    bottomShadowX,
    bottomShadowY,
  };
}

export function LandingHeroV14() {
  const user = useAuthStore((s) => s.user);
  const [activeStepIndex, setActiveStepIndex] = useState(2);
  const [reducedMotion, setReducedMotion] = useState(false);

  const cubeGeometry = useMemo(() => buildCubeHeroGeometry(), []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const mql = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    const sync = () => setReducedMotion(Boolean(mql?.matches));
    sync();
    mql?.addEventListener?.("change", sync);
    return () => {
      mql?.removeEventListener?.("change", sync);
    };
  }, []);

  const handleStoryScroll = useCallback(
    (e: ReactMouseEvent<HTMLAnchorElement>) => {
      const target = document.getElementById("cach-hoat-dong");
      if (!target) return;
      e.preventDefault();
      const isReduced =
        reducedMotion ||
        (typeof window !== "undefined" &&
          Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches));
      target.scrollIntoView({ behavior: isReduced ? "auto" : "smooth", block: "start" });
    },
    [reducedMotion],
  );

  const activeStep = AXO_MINIMAL_HERO_STEPS[activeStepIndex] ?? AXO_MINIMAL_HERO_STEPS[2];
  const showPlane = activeStepIndex >= 1;
  const showSection = activeStepIndex >= 2;

  return (
    <section
      id="landing-hero"
      className="axo-v14-hero axo-v14-hero-minimal"
      aria-labelledby="axo-v14-hero-heading"
    >
      <div className="axo-v14-hero-minimal-grid">
        <h1 id="axo-v14-hero-heading" className="axo-v14-hero-minimal-title">
          <span className="axo-v14-hero-title-line">Hình học không gian,</span>
          <span className="axo-v14-hero-title-line">dễ hình dung hơn.</span>
        </h1>

        <div className="axo-v14-hero-minimal-body">
          <p className="axo-v14-hero-minimal-lead">
            Nhập đề bài tiếng Việt để quan sát khối đa diện 3D chính xác, mặt
            phẳng cắt và từng đường giao tuyến ngay trong không gian trực quan.
          </p>
          <div className="axo-v14-hero-actions axo-v14-hero-minimal-actions">
            <button
              id="btn-landing-hero-start"
              type="button"
              className="axo-v14-btn axo-v14-btn-primary"
              onClick={enterAxoWorkspace}
            >
              {user ? "Vào ứng dụng" : "Bắt đầu dựng hình"}
            </button>
            <a
              id="btn-landing-hero-story"
              href="#cach-hoat-dong"
              className="axo-v14-btn axo-v14-btn-secondary"
              onClick={handleStoryScroll}
            >
              Xem cách hoạt động
            </a>
          </div>
        </div>

        <div
          id="landing-hero-sculpture"
          className="axo-v14-hero-minimal-visual"
          data-hero-mode="minimal-product-first"
          data-hero-step={activeStep.id}
          aria-label="Minh họa trực quan khối lập phương ABCD.A′B′C′D′ và thiết diện lục giác đều MNEPFQ của Axo"
        >
          <div className="axo-v14-min-prompt-pill" aria-hidden="true">
            <span className="axo-v14-min-prompt-dot" />
            <span className="axo-v14-min-prompt-tag">Đề bài</span>
            <span className="axo-v14-min-prompt-text">
              Lập phương ABCD.A′B′C′D′ · cắt (MNP)
            </span>
          </div>

          <svg
            className="axo-v14-min-stage-svg"
            viewBox={`0 0 ${HERO_VIEWBOX_W} ${HERO_VIEWBOX_H}`}
            role="img"
            aria-label="Khối lập phương ABCD.A′B′C′D′ cùng mặt phẳng (MNP) và thiết diện lục giác đều MNEPFQ"
          >
            <defs>
              <radialGradient id="axo-min-contact-shadow" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="rgb(0, 0, 0)" stopOpacity="0.12" />
                <stop offset="55%" stopColor="rgb(0, 0, 0)" stopOpacity="0.045" />
                <stop offset="100%" stopColor="rgb(0, 0, 0)" stopOpacity="0" />
              </radialGradient>
              <linearGradient id="axo-min-face-top-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="rgb(255, 255, 255)" stopOpacity="0.96" />
                <stop offset="100%" stopColor="rgb(246, 245, 244)" stopOpacity="0.92" />
              </linearGradient>
              <linearGradient id="axo-min-face-left-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="rgb(248, 247, 246)" stopOpacity="0.95" />
                <stop offset="100%" stopColor="rgb(240, 238, 235)" stopOpacity="0.92" />
              </linearGradient>
              <linearGradient id="axo-min-face-right-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="rgb(236, 234, 231)" stopOpacity="0.82" />
                <stop offset="100%" stopColor="rgb(225, 222, 217)" stopOpacity="0.72" />
              </linearGradient>
              <linearGradient id="axo-min-section-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="rgb(0, 117, 222)" stopOpacity="0.24" />
                <stop offset="100%" stopColor="rgb(33, 49, 131)" stopOpacity="0.15" />
              </linearGradient>
            </defs>

            <ellipse
              cx={cubeGeometry.bottomShadowX.toFixed(1)}
              cy={cubeGeometry.bottomShadowY.toFixed(1)}
              rx="158"
              ry="19"
              fill="url(#axo-min-contact-shadow)"
            />

            {cubeGeometry.faces.map((face) => (
              <polygon
                key={face.key}
                points={face.pointsAttr}
                className={`axo-v14-min-face axo-v14-min-face-${face.shade}`}
              />
            ))}

            {cubeGeometry.edges
              .filter((edge) => edge.kind === "hidden")
              .map((edge) => (
                <line
                  key={edge.key}
                  x1={edge.x1.toFixed(1)}
                  y1={edge.y1.toFixed(1)}
                  x2={edge.x2.toFixed(1)}
                  y2={edge.y2.toFixed(1)}
                  className="axo-v14-min-edge-hidden"
                />
              ))}

            <polygon
              points={cubeGeometry.planeAttr}
              className={`axo-v14-min-plane ${showPlane ? "is-visible" : ""}`}
            />

            <polygon
              points={cubeGeometry.sectionAttr}
              className={`axo-v14-min-section ${showSection ? "is-visible" : ""}`}
            />

            {cubeGeometry.edges
              .filter((edge) => edge.kind !== "hidden")
              .map((edge) => (
                <line
                  key={edge.key}
                  x1={edge.x1.toFixed(1)}
                  y1={edge.y1.toFixed(1)}
                  x2={edge.x2.toFixed(1)}
                  y2={edge.y2.toFixed(1)}
                  className={
                    edge.kind === "crease"
                      ? "axo-v14-min-edge-crease"
                      : "axo-v14-min-edge-solid"
                  }
                />
              ))}

            <polygon
              points={cubeGeometry.sectionAttr}
              className={`axo-v14-min-section-stroke ${showSection ? "is-visible" : ""}`}
            />

            {cubeGeometry.sectionPoints.map((pt) => {
              const isSeed = pt.role === "seed";
              const visible = isSeed || showPlane;
              return (
                <g
                  key={pt.id}
                  className={`axo-v14-min-pt ${isSeed ? "is-seed" : "is-inter"} ${visible ? "is-visible" : ""}`}
                >
                  <circle cx={pt.x.toFixed(1)} cy={pt.y.toFixed(1)} r={isSeed ? 4.4 : 4.1} />
                  <text x={pt.lx.toFixed(1)} y={pt.ly.toFixed(1)}>
                    {pt.label}
                  </text>
                </g>
              );
            })}
          </svg>

          <div
            className="axo-v14-min-step-rail"
            role="group"
            aria-label="Các bước dựng thiết diện trên mô hình"
          >
            <div className="axo-v14-min-step-tabs">
              {AXO_MINIMAL_HERO_STEPS.map((step, idx) => (
                <button
                  key={step.id}
                  id={`btn-landing-hero-step-${step.id}`}
                  type="button"
                  aria-pressed={idx === activeStepIndex}
                  className={`axo-v14-min-step-tab ${idx === activeStepIndex ? "is-active" : ""}`}
                  onClick={() => setActiveStepIndex(idx)}
                >
                  {step.shortLabel}
                </button>
              ))}
            </div>
            <span className="axo-v14-min-step-result">{activeStep.statusBadge}</span>
          </div>
        </div>
      </div>
    </section>
  );
}
