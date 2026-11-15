import { useCallback, useEffect, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import { IconAxoLogo } from "../icons";
import { useAuthStore } from "../../state/auth";
import { FinalCtaCornerAccent } from "./LandingIllustrationAccents";
import { LandingHeader } from "./LandingHeader";
import { LandingInteractiveDemo } from "./LandingInteractiveDemo";
import {
  LANDING_PRISM_STORY_SPEC,
  enterAxoWorkspace,
  openLibraryFromLanding,
  type Vec3Tuple,
} from "./landing-geometry-data";

export interface V13ReviewBannerProps {
  readonly activeMode: "prod" | "a" | "b";
  readonly onSwitchMode: (mode: "prod" | "a" | "b") => void;
}

export function V13ReviewBanner({ activeMode, onSwitchMode }: V13ReviewBannerProps) {
  return (
    <aside
      id="landing-v13-review-banner"
      className="axo-v13-review-bar"
      data-ui="v13-review-bar"
      aria-label="Thanh chuyển xem thử nghiệm V1.3"
    >
      <div className="axo-sp-container axo-v13-review-inner">
        <div className="axo-v13-review-status">
          <span className="axo-v13-review-badge">PENDING_OWNER_REVIEW</span>
          <span className="axo-v13-review-note">
            Bản thử nghiệm V1.3 tách biệt hoàn toàn khỏi trang chính thức V1.2.2
          </span>
        </div>
        <div className="axo-v13-review-actions" role="group" aria-label="Chọn phiên bản Landing">
          <button
            type="button"
            id="btn-proto-switch-prod"
            className={
              activeMode === "prod"
                ? "axo-v13-switch-btn is-active"
                : "axo-v13-switch-btn"
            }
            onClick={() => onSwitchMode("prod")}
          >
            Bản V1.2.2 hiện hành
          </button>
          <button
            type="button"
            id="btn-proto-switch-a"
            className={
              activeMode === "a"
                ? "axo-v13-switch-btn is-active"
                : "axo-v13-switch-btn"
            }
            aria-pressed={activeMode === "a"}
            onClick={() => onSwitchMode("a")}
          >
            Prototype A: Vector Motion
          </button>
          <button
            type="button"
            id="btn-proto-switch-b"
            className={
              activeMode === "b"
                ? "axo-v13-switch-btn is-active"
                : "axo-v13-switch-btn"
            }
            aria-pressed={activeMode === "b"}
            onClick={() => onSwitchMode("b")}
          >
            Prototype B: 3D Spatial
          </button>
        </div>
      </div>
    </aside>
  );
}

export interface V13StorySceneCopy {
  readonly id: string;
  readonly stepLabel: string;
  readonly title: string;
  readonly narrative: string;
  readonly stageChips: readonly { readonly label: string; readonly emphasis?: "primary" | "result" }[];
  readonly yaw: number;
  readonly pitch: number;
  readonly zoom: number;
  readonly extrude: number;
  readonly planeSweep: number;
  readonly sectionFill: number;
}

export const V13_STORY_SCENES: readonly V13StorySceneCopy[] = [
  {
    id: "scene-1",
    stepLabel: "Bước 1",
    title: "Đề bài xuất hiện",
    narrative:
      "Cho lăng trụ đều ABC.A′B′C′ có cạnh bằng a = 4. Ba điểm M ∈ AB, N ∈ AC và P ∈ CC′ xác định mặt phẳng cắt (MNP).",
    stageChips: [
      { label: "Giả thiết: Lăng trụ đều ABC.A′B′C′ (a = 4)" },
      { label: "Dữ kiện: M ∈ AB · N ∈ AC · P ∈ CC′" },
    ],
    yaw: -0.62,
    pitch: 0.42,
    zoom: 0.96,
    extrude: 0.28,
    planeSweep: 0,
    sectionFill: 0,
  },
  {
    id: "scene-2",
    stepLabel: "Bước 2",
    title: "Hình thành không gian",
    narrative:
      "Từ hai đáy tam giác đều song song ABC, A′B′C′ và các cạnh bên AA′, BB′, CC′ vuông góc với đáy, khối lăng trụ dựng lên rõ nét thấy và nét khuất.",
    stageChips: [
      { label: "Quan hệ dựng: AA′, BB′, CC′ ⊥ (ABC)" },
      { label: "Mặt bên & trung điểm M, N, P trên cạnh" },
    ],
    yaw: -0.5,
    pitch: 0.45,
    zoom: 1.0,
    extrude: 1,
    planeSweep: 0,
    sectionFill: 0,
  },
  {
    id: "scene-3",
    stepLabel: "Bước 3",
    title: "Khám phá quan hệ",
    narrative:
      "Vì MN ∥ BC, mặt phẳng (MNP) mở rộng theo giao tuyến qua P song song BC, cắt cạnh bên BB′ tại trung điểm Q để khép vòng giao tuyến.",
    stageChips: [
      { label: "Quan hệ song song: MN ∥ BC" },
      { label: "Giao tuyến (MNP) ∩ (BCC′B′) = PQ tại Q ∈ BB′" },
    ],
    yaw: -0.36,
    pitch: 0.49,
    zoom: 1.04,
    extrude: 1,
    planeSweep: 1,
    sectionFill: 0.34,
  },
  {
    id: "scene-4",
    stepLabel: "Bước 4",
    title: "Kết quả trực quan",
    narrative:
      "Thiết diện khép kín MNPQ hiện rõ là hình thang cân với hai đáy song song MN, PQ và đầy đủ độ dài xác minh từ hệ tọa độ gốc.",
    stageChips: [
      { label: "Thiết diện hình thang cân: MN = 2 · PQ = 4", emphasis: "primary" },
      { label: "MQ = NP = 2√2 · S(MNPQ) = 3√7", emphasis: "result" },
    ],
    yaw: -0.26,
    pitch: 0.52,
    zoom: 1.09,
    extrude: 1,
    planeSweep: 1,
    sectionFill: 1,
  },
];

export function scrollToLandingSection(id: string): void {
  if (typeof document === "undefined") return;
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

export function V13FinalCtaBand({ idSuffix }: { readonly idSuffix: string }) {
  const user = useAuthStore((s) => s.user);
  const primaryLabel = user ? "Vào ứng dụng" : "Bắt đầu dựng hình";

  return (
    <section
      id="landing-final-cta"
      className="axo-sp-final-cta"
      aria-labelledby="landing-final-title"
    >
      <div className="axo-sp-container">
        <div className="axo-sp-final-cta-band axo-v13-final-card" data-variant={idSuffix}>
          <FinalCtaCornerAccent />
          <div className="axo-sp-final-cta-copy">
            <div className="axo-v13-lead-tag">SẴN SÀNG BẮT ĐẦU</div>
            <h2 id="landing-final-title" className="axo-sp-final-title">
              Từ đề toán đến mô hình hình học không gian.
            </h2>
            <p className="axo-sp-final-desc">
              Nhập đề bài tiếng Việt hoặc mở một bài toán mẫu để quan sát khối đa diện,
              mặt phẳng cắt và từng bước lập luận trong không gian 3D.
            </p>
            <div className="axo-sp-final-actions">
              <button
                type="button"
                id="btn-landing-final-start"
                className="axo-sp-btn-primary axo-sp-btn-lg"
                onClick={enterAxoWorkspace}
              >
                {primaryLabel}
              </button>
              <button
                type="button"
                id="btn-landing-hero-library"
                className="axo-sp-btn-secondary axo-sp-btn-lg"
                onClick={openLibraryFromLanding}
              >
                Khám phá thư viện bài mẫu
              </button>
            </div>
          </div>

          <div className="axo-v13-final-motif" aria-hidden="true">
            <svg viewBox="0 0 280 220" role="presentation">
              <polygon
                points="68,176 202,164 150,118"
                fill="rgba(49, 48, 46, 0.05)"
                stroke="rgba(49, 48, 46, 0.28)"
                strokeWidth="1.2"
                strokeDasharray="4 4"
              />
              <polygon
                points="68,176 202,164 202,64 68,76"
                fill="rgba(247, 246, 244, 0.72)"
                stroke="#31302e"
                strokeOpacity="0.65"
                strokeWidth="1.5"
              />
              <line x1="68" y1="76" x2="150" y2="30" stroke="#31302e" strokeOpacity="0.65" strokeWidth="1.5" />
              <line x1="202" y1="64" x2="150" y2="30" stroke="#31302e" strokeOpacity="0.65" strokeWidth="1.5" />
              <line x1="150" y1="30" x2="150" y2="118" stroke="#615d59" strokeDasharray="4 4" strokeWidth="1.2" />
              <polygon
                points="52,138 192,102 224,132 84,170"
                fill="rgba(220, 235, 250, 0.42)"
                stroke="#0075de"
                strokeWidth="1.5"
              />
              <polygon
                points="108,144 134,126 176,120 156,148"
                fill="rgba(221, 91, 0, 0.88)"
                stroke="#9a3412"
                strokeWidth="1.6"
              />
            </svg>
          </div>
        </div>
      </div>
    </section>
  );
}

export function V13FooterBand() {
  return (
    <footer id="landing-footer" className="axo-sp-footer">
      <div className="axo-sp-container axo-sp-footer-inner">
        <div className="axo-sp-footer-brand">
          <span className="axo-sp-logo-mark" aria-hidden="true">
            <IconAxoLogo />
          </span>
          <div>
            <strong>Axo</strong>
            <p>Trực quan hóa và khám phá hình học không gian.</p>
          </div>
        </div>

        <nav className="axo-sp-footer-links" aria-label="Liên kết chân trang">
          <button type="button" onClick={() => scrollToLandingSection("landing-hero")}>
            Giới thiệu
          </button>
          <button type="button" onClick={() => scrollToLandingSection("cach-hoat-dong")}>
            Cách hoạt động
          </button>
          <button type="button" onClick={() => scrollToLandingSection("trai-nghiem")}>
            Trải nghiệm
          </button>
          <button type="button" onClick={openLibraryFromLanding}>
            Thư viện bài mẫu
          </button>
        </nav>
      </div>
    </footer>
  );
}

interface Projected2D {
  readonly x: number;
  readonly y: number;
  readonly depth: number;
}

function projectPoint3D(
  p: Vec3Tuple,
  yaw: number,
  pitch: number,
  cx: number,
  cy: number,
  scale: number,
): Projected2D {
  const cosY = Math.cos(yaw);
  const sinY = Math.sin(yaw);
  const x1 = p[0] * cosY + p[2] * sinY;
  const z1 = -p[0] * sinY + p[2] * cosY;

  const cosP = Math.cos(pitch);
  const sinP = Math.sin(pitch);
  const y2 = p[1] * cosP - z1 * sinP;
  const z2 = p[1] * sinP + z1 * cosP;

  const persp = 10.5 / (10.5 - z2 * 0.48);
  return {
    x: cx + x1 * scale * persp,
    y: cy - y2 * scale * persp,
    depth: z2,
  };
}

function lerpNum(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function lerpVec3(a: Vec3Tuple, b: Vec3Tuple, t: number): Vec3Tuple {
  return [lerpNum(a[0], b[0], t), lerpNum(a[1], b[1], t), lerpNum(a[2], b[2], t)];
}

function HeroConceptASvg() {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const [motionT, setMotionT] = useState(0.25);
  const [tilt, setTilt] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const targetTiltRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const curTiltRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const rafRef = useRef<number>(0);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const reduced =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      setMotionT(1);
      return;
    }

    const startMs = performance.now();
    const durationMs = 900;
    let alive = true;

    const step = (nowMs: number) => {
      if (!alive) return;
      const linear = Math.min(1, Math.max(0, (nowMs - startMs) / durationMs));
      const eased = 1 - Math.pow(1 - linear, 3);
      setMotionT(0.25 + 0.75 * eased);

      const cur = curTiltRef.current;
      const tgt = targetTiltRef.current;
      const nextX = cur.x + (tgt.x - cur.x) * 0.16;
      const nextY = cur.y + (tgt.y - cur.y) * 0.16;
      curTiltRef.current = { x: nextX, y: nextY };
      setTilt({ x: nextX, y: nextY });

      const tiltSettled = Math.abs(tgt.x - nextX) < 0.001 && Math.abs(tgt.y - nextY) < 0.001;
      if (linear < 1 || !tiltSettled) {
        rafRef.current = window.requestAnimationFrame(step);
      } else {
        rafRef.current = 0;
      }
    };

    rafRef.current = window.requestAnimationFrame(step);
    return () => {
      alive = false;
      if (rafRef.current) {
        window.cancelAnimationFrame(rafRef.current);
        rafRef.current = 0;
      }
    };
  }, []);

  const wakeTiltRaf = useCallback(() => {
    if (typeof window === "undefined") return;
    const reduced =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) return;
    if (rafRef.current !== 0) return;

    const tick = () => {
      const cur = curTiltRef.current;
      const tgt = targetTiltRef.current;
      const nextX = cur.x + (tgt.x - cur.x) * 0.16;
      const nextY = cur.y + (tgt.y - cur.y) * 0.16;
      curTiltRef.current = { x: nextX, y: nextY };
      setTilt({ x: nextX, y: nextY });
      if (Math.abs(tgt.x - nextX) >= 0.001 || Math.abs(tgt.y - nextY) >= 0.001) {
        rafRef.current = window.requestAnimationFrame(tick);
      } else {
        rafRef.current = 0;
      }
    };
    rafRef.current = window.requestAnimationFrame(tick);
  }, []);

  const handlePointerMove = useCallback(
    (e: ReactPointerEvent<HTMLDivElement>) => {
      const rect = hostRef.current?.getBoundingClientRect();
      if (!rect || rect.width <= 0 || rect.height <= 0) return;
      const nx = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
      const ny = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
      targetTiltRef.current = { x: nx * 0.14, y: -ny * 0.08 };
      wakeTiltRaf();
    },
    [wakeTiltRaf],
  );

  const handlePointerLeave = useCallback(() => {
    targetTiltRef.current = { x: 0, y: 0 };
    wakeTiltRaf();
  }, [wakeTiltRaf]);

  const geom = useMemo(() => {
    const yaw = -0.54 + tilt.x - (1 - motionT) * 0.14;
    const pitch = 0.44 + tilt.y;
    const cx = 290;
    const cy = 225;
    const scale = 68;

    const baseA: Vec3Tuple = [-1.55, -1.1, 1.05];
    const baseB: Vec3Tuple = [1.55, -1.1, 1.05];
    const baseC: Vec3Tuple = [1.4, -1.1, -1.25];
    const baseD: Vec3Tuple = [-1.45, -1.1, -1.2];
    const apexS: Vec3Tuple = [-0.25, 1.85, 0.15];

    const cutRatio = 0.46;
    const kM: Vec3Tuple = lerpVec3(baseA, apexS, cutRatio + 0.08);
    const kN: Vec3Tuple = lerpVec3(baseB, apexS, cutRatio);
    const kP: Vec3Tuple = lerpVec3(baseC, apexS, cutRatio - 0.04);
    const kQ: Vec3Tuple = lerpVec3(baseD, apexS, cutRatio + 0.04);

    const shiftPlane: Vec3Tuple = [0, (1 - motionT) * 0.85, 0];
    const planeQuad: readonly Vec3Tuple[] = [
      [-2.15, 0.2 + shiftPlane[1], 1.45],
      [2.15, 0.05 + shiftPlane[1], 1.45],
      [2.0, -0.25 + shiftPlane[1], -1.65],
      [-2.05, -0.05 + shiftPlane[1], -1.65],
    ];

    const p = (v: Vec3Tuple) => projectPoint3D(v, yaw, pitch, cx, cy, scale);
    const pA = p(baseA);
    const pB = p(baseB);
    const pC = p(baseC);
    const pD = p(baseD);
    const pS = p(lerpVec3(baseA, apexS, 0.35 + 0.65 * motionT));
    const pM = p(kM);
    const pN = p(kN);
    const pP = p(kP);
    const pQ = p(kQ);
    const planePts = planeQuad.map(p);
    const footO = p([-0.25, -1.1, 0.15]);

    const fmt = (pts: readonly Projected2D[]) =>
      pts.map((pt) => `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`).join(" ");

    return {
      pA,
      pB,
      pC,
      pD,
      pS,
      pM,
      pN,
      pP,
      pQ,
      footO,
      lowerFrontLeft: fmt([pA, pB, pN, pM]),
      lowerFrontRight: fmt([pB, pC, pP, pN]),
      upperCapPts: fmt([pM, pN, pP, pS]),
      sectionPts: fmt([pM, pN, pP, pQ]),
      planePts: fmt(planePts),
      planeOpacity: 0.18 + 0.24 * motionT,
      sectionOpacity: Math.max(0.15, (motionT - 0.25) / 0.75),
    };
  }, [motionT, tilt]);

  return (
    <div
      id="landing-hero-sculpture"
      ref={hostRef}
      className="axo-v13-hero-stage"
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
      aria-label="Minh họa biến đổi hình học không gian Axo"
    >
      <svg
        className="axo-v13-hero-svg"
        viewBox="0 0 580 440"
        role="img"
        aria-label="Khối chóp không gian và mặt phẳng cắt tạo thiết diện"
      >
        <ellipse cx="290" cy="368" rx="164" ry="20" fill="rgba(25, 25, 24, 0.06)" />

        {/* Back hidden base edges */}
        <line
          x1={geom.pA.x}
          y1={geom.pA.y}
          x2={geom.pD.x}
          y2={geom.pD.y}
          stroke="#615d59"
          strokeOpacity="0.45"
          strokeWidth="1.4"
          strokeDasharray="5 5"
        />
        <line
          x1={geom.pD.x}
          y1={geom.pD.y}
          x2={geom.pC.x}
          y2={geom.pC.y}
          stroke="#615d59"
          strokeOpacity="0.45"
          strokeWidth="1.4"
          strokeDasharray="5 5"
        />
        <line
          x1={geom.pD.x}
          y1={geom.pD.y}
          x2={geom.pS.x}
          y2={geom.pS.y}
          stroke="#615d59"
          strokeOpacity="0.42"
          strokeWidth="1.4"
          strokeDasharray="5 5"
        />
        <line
          x1={geom.pS.x}
          y1={geom.pS.y}
          x2={geom.footO.x}
          y2={geom.footO.y}
          stroke="#0075de"
          strokeOpacity="0.34"
          strokeWidth="1.3"
          strokeDasharray="4 4"
        />

        {/* Lower solid frustum faces */}
        <polygon
          points={geom.lowerFrontLeft}
          fill="#f7f6f4"
          stroke="#191918"
          strokeOpacity="0.72"
          strokeWidth="1.7"
          strokeLinejoin="round"
        />
        <polygon
          points={geom.lowerFrontRight}
          fill="#ebe9e4"
          stroke="#191918"
          strokeOpacity="0.72"
          strokeWidth="1.7"
          strokeLinejoin="round"
        />

        {/* Sweeping Axo-Blue cutting plane */}
        <polygon
          points={geom.planePts}
          fill="#dcebfa"
          fillOpacity={geom.planeOpacity}
          stroke="#0075de"
          strokeOpacity="0.82"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />

        {/* Semantic-orange cross-section */}
        <polygon
          points={geom.sectionPts}
          fill="#dd5b00"
          fillOpacity={0.9 * geom.sectionOpacity}
          stroke="#9a3412"
          strokeWidth="2.1"
          strokeLinejoin="round"
        />

        {/* Upper translucent pyramid cap */}
        <polygon
          points={geom.upperCapPts}
          fill="rgba(220, 235, 250, 0.22)"
          stroke="#31302e"
          strokeOpacity="0.58"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
        <line
          x1={geom.pS.x}
          y1={geom.pS.y}
          x2={geom.pN.x}
          y2={geom.pN.y}
          stroke="#191918"
          strokeOpacity="0.65"
          strokeWidth="1.5"
        />

        {/* Intersection key nodes */}
        {[geom.pM, geom.pN, geom.pP, geom.pQ].map((pt, idx) => (
          <circle
            key={idx}
            cx={pt.x}
            cy={pt.y}
            r="4.2"
            fill="#dd5b00"
            stroke="#ffffff"
            strokeWidth="1.5"
            opacity={geom.sectionOpacity}
          />
        ))}
      </svg>
    </div>
  );
}

interface VectorSceneVisualState {
  readonly yaw: number;
  readonly pitch: number;
  readonly zoom: number;
  readonly extrude: number;
  readonly planeSweep: number;
  readonly sectionFill: number;
}

function ContinuousVectorStoryCanvas({
  activeStage,
}: {
  readonly activeStage: number;
}) {
  const [vis, setVis] = useState<VectorSceneVisualState>(() => {
    const target = V13_STORY_SCENES[activeStage] ?? V13_STORY_SCENES[0];
    return {
      yaw: target.yaw,
      pitch: target.pitch,
      zoom: target.zoom,
      extrude: target.extrude,
      planeSweep: target.planeSweep,
      sectionFill: target.sectionFill,
    };
  });
  const curRef = useRef<VectorSceneVisualState>(vis);
  const targetRef = useRef<VectorSceneVisualState>(vis);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const targetScene = V13_STORY_SCENES[activeStage] ?? V13_STORY_SCENES[0];
    const nextTarget: VectorSceneVisualState = {
      yaw: targetScene.yaw,
      pitch: targetScene.pitch,
      zoom: targetScene.zoom,
      extrude: targetScene.extrude,
      planeSweep: targetScene.planeSweep,
      sectionFill: targetScene.sectionFill,
    };
    targetRef.current = nextTarget;

    if (typeof window === "undefined") {
      curRef.current = nextTarget;
      setVis(nextTarget);
      return;
    }

    const reduced =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      curRef.current = nextTarget;
      setVis(nextTarget);
      return;
    }

    const startState = { ...curRef.current };
    const startMs = performance.now();
    const durationMs = 520;
    let alive = true;

    const animate = (nowMs: number) => {
      if (!alive) return;
      const linear = Math.min(1, Math.max(0, (nowMs - startMs) / durationMs));
      const e = 1 - Math.pow(1 - linear, 3);
      const interpolated: VectorSceneVisualState = {
        yaw: lerpNum(startState.yaw, nextTarget.yaw, e),
        pitch: lerpNum(startState.pitch, nextTarget.pitch, e),
        zoom: lerpNum(startState.zoom, nextTarget.zoom, e),
        extrude: lerpNum(startState.extrude, nextTarget.extrude, e),
        planeSweep: lerpNum(startState.planeSweep, nextTarget.planeSweep, e),
        sectionFill: lerpNum(startState.sectionFill, nextTarget.sectionFill, e),
      };
      curRef.current = interpolated;
      setVis(interpolated);

      if (linear < 1) {
        rafRef.current = window.requestAnimationFrame(animate);
      } else {
        rafRef.current = 0;
      }
    };

    if (rafRef.current) {
      window.cancelAnimationFrame(rafRef.current);
      rafRef.current = 0;
    }
    rafRef.current = window.requestAnimationFrame(animate);

    return () => {
      alive = false;
      if (rafRef.current) {
        window.cancelAnimationFrame(rafRef.current);
        rafRef.current = 0;
      }
    };
  }, [activeStage]);

  const sceneData = useMemo(() => {
    const map = LANDING_PRISM_STORY_SPEC.pointMap;
    const baseY = map["A"].pos[1];
    const extrudePos = (id: string): Vec3Tuple => {
      const pt = map[id].pos;
      if (id === "A" || id === "B" || id === "C" || id === "M" || id === "N") {
        return pt;
      }
      return [pt[0], baseY + (pt[1] - baseY) * vis.extrude, pt[2]];
    };

    const pts3D: Record<string, Vec3Tuple> = {
      A: extrudePos("A"),
      B: extrudePos("B"),
      C: extrudePos("C"),
      A_prime: extrudePos("A_prime"),
      B_prime: extrudePos("B_prime"),
      C_prime: extrudePos("C_prime"),
      M: extrudePos("M"),
      N: extrudePos("N"),
      P: extrudePos("P"),
      Q: extrudePos("Q"),
    };

    const scale = 55 * vis.zoom;
    const cx = 300;
    const cy = 216;
    const proj: Record<string, Projected2D> = {};
    for (const [k, v] of Object.entries(pts3D)) {
      proj[k] = projectPoint3D(v, vis.yaw, vis.pitch, cx, cy, scale);
    }

    const prismCentroid = {
      x: (proj["A"].x + proj["B"].x + proj["C"].x + proj["A_prime"].x + proj["B_prime"].x + proj["C_prime"].x) / 6,
      y: (proj["A"].y + proj["B"].y + proj["C"].y + proj["A_prime"].y + proj["B_prime"].y + proj["C_prime"].y) / 6,
    };

    const solidEdges = LANDING_PRISM_STORY_SPEC.solidEdges.map((edge) => {
      const a = proj[edge.from];
      const b = proj[edge.to];
      const isBack = edge.from === "C" || edge.to === "C";
      return { ...edge, a, b, isBack };
    });

    const sweepLift = (1 - vis.planeSweep) * 0.72;
    const planeProj = LANDING_PRISM_STORY_SPEC.planeQuad.map((qPt) =>
      projectPoint3D(
        [qPt[0], qPt[1] + sweepLift, qPt[2]],
        vis.yaw,
        vis.pitch,
        cx,
        cy,
        scale,
      ),
    );

    const fmt = (pts: readonly Projected2D[]) =>
      pts.map((pt) => `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`).join(" ");

    const labelList = ["A", "B", "C", "A_prime", "B_prime", "C_prime", "M", "N", "P", "Q"].filter(
      (id) => {
        if (id === "Q") return vis.planeSweep > 0.25;
        if (id === "A_prime" || id === "B_prime" || id === "C_prime") return vis.extrude > 0.65;
        return true;
      },
    );

    const positionedLabels = labelList.map((id) => {
      const pt = proj[id];
      const dx = pt.x - prismCentroid.x;
      const dy = pt.y - prismCentroid.y;
      const len = Math.max(1, Math.hypot(dx, dy));
      const offset = 16;
      return {
        id,
        label: map[id].label,
        role: map[id].role,
        px: pt.x,
        py: pt.y,
        lx: Math.min(576, Math.max(24, pt.x + (dx / len) * offset)),
        ly: Math.min(406, Math.max(24, pt.y + (dy / len) * offset + 4)),
      };
    });

    return {
      proj,
      solidEdges,
      baseFill: fmt([proj["A"], proj["B"], proj["C"]]),
      planePts: fmt(planeProj),
      sectionPts: fmt([proj["M"], proj["N"], proj["P"], proj["Q"]]),
      positionedLabels,
    };
  }, [vis]);

  return (
    <div id="landing-storytelling-scene" className="axo-v13-story-canvas-wrap">
      <svg
        className="axo-v13-story-svg"
        viewBox="0 0 600 430"
        role="img"
        aria-label="Minh họa vector liên tục lăng trụ đứng ABC.A′B′C′ và thiết diện MNPQ"
      >
        {/* Base contact ellipse */}
        <ellipse cx="300" cy="348" rx="176" ry="22" fill="rgba(25, 25, 24, 0.05)" />

        {/* Base triangle ABC */}
        <polygon
          points={sceneData.baseFill}
          fill="#f7f6f4"
          stroke="#191918"
          strokeOpacity="0.65"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />

        {/* Prism edges (back dashed vs front solid) */}
        {sceneData.solidEdges.map((edge) => {
          const isVertical =
            (edge.from === "A" && edge.to === "A_prime") ||
            (edge.from === "B" && edge.to === "B_prime") ||
            (edge.from === "C" && edge.to === "C_prime");
          const isTop = edge.from.includes("prime") && edge.to.includes("prime");
          let edgeOpacity = 0.8;
          if (isVertical || isTop) {
            edgeOpacity = Math.max(0.18, vis.extrude * 0.85);
          }
          const shouldDash = edge.isBack || (vis.extrude < 0.65 && (isVertical || isTop));

          return (
            <line
              key={`${edge.from}-${edge.to}`}
              x1={edge.a.x}
              y1={edge.a.y}
              x2={edge.b.x}
              y2={edge.b.y}
              stroke={shouldDash ? "#615d59" : "#191918"}
              strokeOpacity={shouldDash ? edgeOpacity * 0.58 : edgeOpacity}
              strokeWidth={shouldDash ? "1.35" : "1.8"}
              strokeDasharray={shouldDash ? "5 5" : undefined}
              strokeLinecap="round"
            />
          );
        })}

        {/* Parallel relation highlight MN // PQ in stages 3 & 4 */}
        {vis.planeSweep > 0.15 && (
          <line
            x1={sceneData.proj["M"].x}
            y1={sceneData.proj["M"].y}
            x2={sceneData.proj["N"].x}
            y2={sceneData.proj["N"].y}
            stroke="#0075de"
            strokeOpacity={vis.planeSweep * 0.92}
            strokeWidth="2.4"
            strokeLinecap="round"
          />
        )}

        {/* Cutting plane (MNP) */}
        {vis.planeSweep > 0.05 && (
          <polygon
            points={sceneData.planePts}
            fill="#dcebfa"
            fillOpacity={0.34 * vis.planeSweep}
            stroke="#0075de"
            strokeOpacity={0.82 * vis.planeSweep}
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
        )}

        {/* Cross section MNPQ */}
        {vis.sectionFill > 0.02 && (
          <polygon
            points={sceneData.sectionPts}
            fill="#dd5b00"
            fillOpacity={0.84 * vis.sectionFill}
            stroke="#9a3412"
            strokeOpacity={Math.min(1, vis.sectionFill * 1.25)}
            strokeWidth="2.2"
            strokeLinejoin="round"
          />
        )}

        {/* Construction segment PQ when plane sweeps */}
        {vis.planeSweep > 0.2 && (
          <line
            x1={sceneData.proj["P"].x}
            y1={sceneData.proj["P"].y}
            x2={sceneData.proj["Q"].x}
            y2={sceneData.proj["Q"].y}
            stroke="#0075de"
            strokeOpacity={vis.planeSweep * 0.92}
            strokeWidth="2.2"
            strokeDasharray={vis.sectionFill < 0.7 ? "5 4" : undefined}
            strokeLinecap="round"
          />
        )}

        {/* Vertices and labels */}
        {sceneData.positionedLabels.map((pt) => {
          const isAccent = pt.role === "seed" || pt.role === "intersection";
          return (
            <g key={pt.id}>
              <circle
                cx={pt.px}
                cy={pt.py}
                r={isAccent ? "4.6" : "3.4"}
                fill={
                  pt.role === "intersection"
                    ? "#dd5b00"
                    : pt.role === "seed"
                      ? "#0075de"
                      : "#191918"
                }
                stroke="#ffffff"
                strokeWidth="1.5"
              />
              <text
                x={pt.lx}
                y={pt.ly}
                textAnchor="middle"
                fontSize="13"
                fontWeight="700"
                fill={isAccent ? "#191918" : "#31302e"}
              >
                {pt.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export function LandingPrototypeA({
  onSwitchMode,
}: {
  readonly onSwitchMode: (mode: "prod" | "a" | "b") => void;
}) {
  const user = useAuthStore((s) => s.user);
  const primaryHeroLabel = user ? "Vào ứng dụng" : "Bắt đầu dựng hình";

  const [activeStage, setActiveStage] = useState(0);
  const [autoPlay, setAutoPlay] = useState(true);
  const stepRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const storySectionRef = useRef<HTMLElement | null>(null);

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
    <div id="view-landing" className="axo-sp-root axo-v13-root axo-v13-proto-a">
      <LandingHeader />

      <main className="axo-sp-main">
        <V13ReviewBanner activeMode="a" onSwitchMode={onSwitchMode} />

        {/* Hero Concept A: Geometric Transformation (Vector-first frameless canvas) */}
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
              <HeroConceptASvg />
            </div>
          </div>
        </section>

        {/* Continuous Vector Storytelling Section */}
        <section
          id="cach-hoat-dong"
          ref={storySectionRef}
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

                <ContinuousVectorStoryCanvas activeStage={activeStage} />

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
                Theo dõi khối lăng trụ đều ABC.A′B′C′ (a = 4) chuyển hóa liên tục từ dữ
                kiện đến thiết diện MNPQ.
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
                  <p>
                    Hệ trục chuẩn: {LANDING_PRISM_STORY_SPEC.problemText}
                  </p>
                  <p>
                    Trung điểm M ∈ AB, N ∈ AC suy ra MN ∥ BC, MN = 2. Giao tuyến PQ ∥ BC với P ∈ CC′,
                    Q ∈ BB′ và PQ = 4 tạo hình thang cân MNPQ có diện tích {LANDING_PRISM_STORY_SPEC.equationText}.
                  </p>
                </div>
              </details>
            </div>
          </div>
        </section>

        <LandingInteractiveDemo />

        <V13FinalCtaBand idSuffix="proto-a" />
      </main>

      <V13FooterBand />
    </div>
  );
}
