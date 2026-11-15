import { useMemo } from "react";
import { LANDING_PRISM_STORY_SPEC, type Vec3Tuple } from "./landing-geometry-data";

interface Point2D {
  readonly id: string;
  readonly label: string;
  readonly role: "vertex" | "base_center" | "seed" | "intersection";
  readonly x: number;
  readonly y: number;
}

const SVG_W = 600;
const SVG_H = 400;

function projectPoint(point: Vec3Tuple, camera: Vec3Tuple, lookAt: Vec3Tuple): { x: number; y: number } {
  const fx = lookAt[0] - camera[0];
  const fy = lookAt[1] - camera[1];
  const fz = lookAt[2] - camera[2];
  const fLen = Math.hypot(fx, fy, fz) || 1;
  const f: Vec3Tuple = [fx / fLen, fy / fLen, fz / fLen];

  let rx = f[1] * 0 - f[2] * 1;
  let ry = f[2] * 0 - f[0] * 0;
  let rz = f[0] * 1 - f[1] * 0;
  const rLen = Math.hypot(rx, ry, rz) || 1;
  rx /= rLen;
  ry /= rLen;
  rz /= rLen;

  const ux = ry * f[2] - rz * f[1];
  const uy = rz * f[0] - rx * f[2];
  const uz = rx * f[1] - ry * f[0];

  const dx = point[0] - camera[0];
  const dy = point[1] - camera[1];
  const dz = point[2] - camera[2];

  const camX = dx * rx + dy * ry + dz * rz;
  const camY = dx * ux + dy * uy + dz * uz;
  const camZ = Math.max(0.25, dx * f[0] + dy * f[1] + dz * f[2]);
  const tanHalf = Math.tan(((37 / 2) * Math.PI) / 180);
  const scale = SVG_H / (2 * tanHalf);

  return {
    x: SVG_W / 2 + 24 + (camX / camZ) * scale,
    y: SVG_H / 2 - 4 - (camY / camZ) * scale,
  };
}

function edgeInFace(a: string, b: string, face: readonly string[]): boolean {
  for (let i = 0; i < face.length; i++) {
    const u = face[i];
    const v = face[(i + 1) % face.length];
    if ((u === a && v === b) || (u === b && v === a)) return true;
  }
  return false;
}

export interface LandingExplainerSceneMeta {
  readonly id: string;
  readonly stepNumber: string;
  readonly shortLabel: string;
  readonly headline: string;
  readonly summary: string;
}

export const EXPLAINER_SCENES: readonly LandingExplainerSceneMeta[] = [
  {
    id: "scene-parse",
    stepNumber: "01",
    shortLabel: "Đề bài xuất hiện",
    headline: "Đề bài tiếng Việt tách thành đối tượng không gian",
    summary:
      "Từng giả thiết trong đề — khối lăng trụ ABC.A′B′C′, ba điểm M, N, P và mặt phẳng (MNP) — được nhận diện thành cấu trúc hình học rõ ràng.",
  },
  {
    id: "scene-construct",
    stepNumber: "02",
    shortLabel: "Hình thành không gian",
    headline: "Khối lăng trụ và nét khuất dựng lên theo đúng tỷ lệ",
    summary:
      "Mặt đáy mở rộng theo chiều cao không gian, cạnh khuất chuyển nét đứt tự nhiên, ba điểm gốc M, N, P đặt chính xác trên cạnh.",
  },
  {
    id: "scene-relations",
    stepNumber: "03",
    shortLabel: "Khám phá quan hệ",
    headline: "Mặt phẳng cắt mở đường giao tuyến song song MN // BC",
    summary:
      "Từ quan hệ song song của mặt phẳng (MNP), tia cắt kéo dài tìm đúng giao điểm Q trên cạnh BB′ ở góc nhìn sâu hơn.",
  },
  {
    id: "scene-result",
    stepNumber: "04",
    shortLabel: "Kết quả trực quan",
    headline: "Thiết diện MNPQ khép kín cùng kết quả kiểm chứng",
    summary:
      "Hình thang cân MNPQ hiện nổi bật với các số đo cạnh và diện tích S(MNPQ) = 3√7 khớp chặt mô hình không gian.",
  },
];

export interface LandingExplainerAnimationProps {
  readonly selectedStage: number;
  readonly autoPlaying: boolean;
  readonly onToggleAutoPlay: () => void;
  readonly onUserInteract?: () => void;
}

/**
 * 4-scene continuous animated product explainer (100% vector SVG + CSS motion graphics, 0 WebGL canvas).
 * Scene 1: Problem card & semantic extraction ->
 * Scene 2: Spatial extrusion & seed points ->
 * Scene 3: Cutting plane sweep, MN // BC & orbit cue ->
 * Scene 4: Closed luminous MNPQ trapezoid & exact verified answer.
 */
export function LandingExplainerAnimation({
  selectedStage,
  autoPlaying,
  onToggleAutoPlay,
  onUserInteract,
}: LandingExplainerAnimationProps) {
  const sample = LANDING_PRISM_STORY_SPEC;
  const activeMeta = EXPLAINER_SCENES[selectedStage] ?? EXPLAINER_SCENES[0];

  const projected = useMemo(() => {
    const cam = sample.defaultCamera;
    const look = sample.defaultLookAt;
    const pts: Record<string, Point2D> = {};
    for (const pt of sample.points) {
      const pr = projectPoint(pt.pos, cam, look);
      pts[pt.id] = { id: pt.id, label: pt.label, role: pt.role, x: pr.x, y: pr.y };
    }

    let cCount = 0;
    let cxAcc = 0;
    let cyAcc = 0;
    let czAcc = 0;
    for (const face of sample.solidFaces) {
      for (const vid of face) {
        const p = sample.pointMap[vid].pos;
        cxAcc += p[0];
        cyAcc += p[1];
        czAcc += p[2];
        cCount++;
      }
    }
    const solidCenter: Vec3Tuple = [
      cxAcc / Math.max(1, cCount),
      cyAcc / Math.max(1, cCount),
      czAcc / Math.max(1, cCount),
    ];

    const faceFront = sample.solidFaces.map((face) => {
      const p0 = sample.pointMap[face[0]].pos;
      const p1 = sample.pointMap[face[1]].pos;
      const p2 = sample.pointMap[face[2]].pos;
      const fc: Vec3Tuple = [
        face.reduce((acc, id) => acc + sample.pointMap[id].pos[0], 0) / face.length,
        face.reduce((acc, id) => acc + sample.pointMap[id].pos[1], 0) / face.length,
        face.reduce((acc, id) => acc + sample.pointMap[id].pos[2], 0) / face.length,
      ];
      const u: Vec3Tuple = [p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]];
      const v: Vec3Tuple = [p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]];
      let nx = u[1] * v[2] - u[2] * v[1];
      let ny = u[2] * v[0] - u[0] * v[2];
      let nz = u[0] * v[1] - u[1] * v[0];
      if (nx * (fc[0] - solidCenter[0]) + ny * (fc[1] - solidCenter[1]) + nz * (fc[2] - solidCenter[2]) < 0) {
        nx = -nx;
        ny = -ny;
        nz = -nz;
      }
      const vx = cam[0] - fc[0];
      const vy = cam[1] - fc[1];
      const vz = cam[2] - fc[2];
      return { face, front: nx * vx + ny * vy + nz * vz > 0.02 };
    });

    const edges = sample.solidEdges.map((edge) => {
      const adj = faceFront.filter((f) => edgeInFace(edge.from, edge.to, f.face));
      const front = adj.length === 0 || adj.some((f) => f.front);
      return {
        id: `${edge.from}-${edge.to}`,
        from: edge.from,
        to: edge.to,
        p1: pts[edge.from],
        p2: pts[edge.to],
        front,
      };
    });

    const pSum = sample.planeQuad.reduce<Vec3Tuple>(
      (acc, q) => [acc[0] + q[0], acc[1] + q[1], acc[2] + q[2]],
      [0, 0, 0],
    );
    const pDenom = Math.max(1, sample.planeQuad.length);
    const pc: Vec3Tuple = [pSum[0] / pDenom, pSum[1] / pDenom, pSum[2] / pDenom];
    const shrunkenPlane = sample.planeQuad.map<Vec3Tuple>((q) => [
      pc[0] + (q[0] - pc[0]) * 0.78,
      pc[1] + (q[1] - pc[1]) * 0.78,
      pc[2] + (q[2] - pc[2]) * 0.78,
    ]);
    const planePts = shrunkenPlane.map((q) => projectPoint(q, cam, look));
    const sectionPts = sample.sectionLoop.map((id) => pts[id]);

    const visPts = Object.values(pts);
    const meanX = visPts.reduce((acc, p) => acc + p.x, 0) / Math.max(1, visPts.length);
    const meanY = visPts.reduce((acc, p) => acc + p.y, 0) / Math.max(1, visPts.length);

    const labels = sample.points.map((pt) => {
      const p2 = pts[pt.id];
      const vx = p2.x - meanX;
      const vy = p2.y - meanY;
      const len = Math.hypot(vx, vy) || 1;
      const dist = pt.role === "vertex" ? 17 : 19;
      const customBias: Record<string, readonly [number, number]> = {
        C: [0, 17],
        C_prime: [0, -17],
        N: [-16, 10],
        P: [16, -6],
        Q: [18, -2],
        M: [0, 17],
      };
      const offset = customBias[pt.id] ?? [(vx / len) * dist, (vy / len) * dist];
      return {
        id: pt.id,
        label: pt.label,
        role: pt.role,
        x: p2.x,
        y: p2.y,
        lx: p2.x + offset[0],
        ly: p2.y + offset[1],
      };
    });

    return { pts, edges, planePts, sectionPts, labels };
  }, [sample]);

  const { pts, edges, planePts, sectionPts, labels } = projected;

  return (
    <div
      id="landing-storytelling-scene"
      className="axo-sp-story-canvas axo-sp-explainer-stage"
      data-stage={selectedStage}
      role="img"
      aria-label={`Minh họa động chặng ${activeMeta.stepNumber} — ${activeMeta.shortLabel}: ${activeMeta.headline}`}
      onMouseEnter={onUserInteract}
    >
      <div className="axo-sp-story-top-bar">
        <span className="axo-sp-scene-chip">
          {activeMeta.stepNumber} · {activeMeta.shortLabel}
        </span>

        <div className="axo-sp-explainer-controls">
          <div className="axo-sp-explainer-progress-track" aria-hidden="true">
            {EXPLAINER_SCENES.map((sc, idx) => (
              <span
                key={sc.id}
                className={`axo-sp-explainer-progress-seg${
                  idx === selectedStage ? " is-current" : idx < selectedStage ? " is-done" : ""
                }`}
              />
            ))}
          </div>

          <button
            id="btn-landing-story-autoplay"
            type="button"
            className="axo-sp-explainer-play-btn"
            aria-label={autoPlaying ? "Tạm dừng chuyển động minh họa" : "Phát tiếp chuyển động minh họa"}
            aria-pressed={autoPlaying}
            onClick={onToggleAutoPlay}
          >
            {autoPlaying ? "Tạm dừng" : "Tự chạy"}
          </button>
        </div>
      </div>

      {/* Bespoke 4-scene SVG vector motion theater */}
      <svg
        className="axo-sp-story-svg axo-sp-explainer-svg"
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        preserveAspectRatio="xMidYMid meet"
        aria-hidden="true"
      >
        {/* Subtle depth floor ellipse */}
        <ellipse
          cx={pts.A.x * 0.35 + pts.B.x * 0.35 + pts.C.x * 0.3}
          cy={pts.C.y + 18}
          rx="145"
          ry="24"
          className="axo-sp-explainer-shadow"
        />

        {/* ACT 1 (Stage 0 prominent, recedes smoothly in Stages 1–3): Floating Problem Sheet & Extraction Flows */}
        <g className={`axo-sp-explainer-prompt-card${selectedStage === 0 ? " is-featured" : " is-receded"}`}>
          <rect x="26" y="42" width="196" height="162" rx="14" className="axo-sp-explainer-card-bg" />
          <line x1="42" y1="68" x2="112" y2="68" className="axo-sp-explainer-card-kicker" />
          <text x="42" y="92" className="axo-sp-explainer-card-line">
            Lăng trụ đều ABC.A′B′C′
          </text>
          <rect x="40" y="104" width="164" height="24" rx="8" className="axo-sp-explainer-chip-blue" />
          <text x="48" y="120" className="axo-sp-explainer-chip-text-blue">
            M ∈ AB · N ∈ AC · P ∈ CC′
          </text>
          <rect x="40" y="138" width="144" height="24" rx="8" className="axo-sp-explainer-chip-amber" />
          <text x="48" y="154" className="axo-sp-explainer-chip-text-amber">
            Dựng thiết diện (MNP)
          </text>
          <text x="42" y="186" className="axo-sp-explainer-card-sub">
            Phân rã dữ kiện chuẩn xác →
          </text>
        </g>

        {/* Data extraction curves linking problem phrases to spatial anchors */}
        <g className={`axo-sp-explainer-flow-group${selectedStage === 0 ? " is-active" : ""}`}>
          <path
            d={`M 218 116 C 276 116, 260 ${pts.M.y}, ${pts.M.x} ${pts.M.y}`}
            className="axo-sp-explainer-flow-arc is-blue"
          />
          <path
            d={`M 218 150 C 282 150, 290 ${pts.P.y}, ${pts.P.x} ${pts.P.y}`}
            className="axo-sp-explainer-flow-arc is-amber"
          />
        </g>

        {/* Base triangle ABC */}
        <polygon
          points={`${pts.A.x.toFixed(1)},${pts.A.y.toFixed(1)} ${pts.B.x.toFixed(1)},${pts.B.y.toFixed(1)} ${pts.C.x.toFixed(1)},${pts.C.y.toFixed(1)}`}
          className={`axo-sp-story-base-poly${selectedStage === 0 ? " is-soft" : ""}`}
        />

        {/* ACT 2 & 3: Solid prism wireframe with self-drawing extrusion on Stage >= 1 */}
        <g className={`axo-sp-explainer-solid${selectedStage >= 1 ? " is-formed" : " is-ghost"}`}>
          {edges.map((e) => (
            <line
              key={e.id}
              x1={e.p1.x}
              y1={e.p1.y}
              x2={e.p2.x}
              y2={e.p2.y}
              className={e.front ? "axo-sp-story-edge-front" : "axo-sp-story-edge-back"}
            />
          ))}
        </g>

        {/* ACT 3 (Stage >= 2): Frosted cutting plane (MNP) sweep & MN // BC spatial guides */}
        <polygon
          points={planePts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")}
          className={`axo-sp-story-plane${selectedStage >= 2 ? " is-shown" : ""}`}
        />

        <line
          x1={pts.B.x}
          y1={pts.B.y}
          x2={pts.C.x}
          y2={pts.C.y}
          className={`axo-sp-story-parallel-line${selectedStage >= 2 ? " is-shown" : ""}`}
        />
        <line
          x1={pts.M.x}
          y1={pts.M.y}
          x2={pts.N.x}
          y2={pts.N.y}
          className={`axo-sp-story-parallel-line${selectedStage >= 2 ? " is-shown" : ""}`}
        />

        {/* ACT 3 Orbit inspection cue arc around the upper prism */}
        <path
          d={`M ${pts.A_prime.x - 16} ${pts.A_prime.y - 26} A 90 22 0 0 1 ${pts.P.x + 22} ${pts.A_prime.y - 14}`}
          className={`axo-sp-explainer-orbit-cue${selectedStage === 2 ? " is-visible" : ""}`}
        />

        {/* ACT 4 (Stage === 3): Closed glowing orange trapezoid fill & drawn perimeter MNPQ */}
        <polygon
          points={sectionPts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")}
          className={`axo-sp-story-section-fill${selectedStage >= 3 ? " is-shown" : ""}`}
        />

        {sectionPts.map((pt, idx) => {
          const nextPt = sectionPts[(idx + 1) % sectionPts.length];
          return (
            <line
              key={`sec-${pt.id}-${nextPt.id}`}
              x1={pt.x}
              y1={pt.y}
              x2={nextPt.x}
              y2={nextPt.y}
              className={`axo-sp-story-section-edge${selectedStage >= 2 ? " is-drawn" : ""}`}
            />
          );
        })}

        {/* ACT 4 visual result badge rendered inside the theater when Stage 3 resolves */}
        <g className={`axo-sp-explainer-result-badge${selectedStage === 3 ? " is-shown" : ""}`}>
          <rect x="382" y="16" width="202" height="58" rx="14" className="axo-sp-explainer-result-bg" />
          <text x="398" y="40" className="axo-sp-explainer-result-kicker">
            Thiết diện hình thang cân MNPQ
          </text>
          <text x="398" y="62" className="axo-sp-explainer-result-val">
            S(MNPQ) = 3√7
          </text>
        </g>

        {/* Vertices, Seed points (M, N, P), and Discovered Intersection Q */}
        {labels.map((pt) => {
          const isSeed = pt.role === "seed";
          const isInter = pt.role === "intersection";
          const isVertexVisible =
            selectedStage === 0
              ? isSeed || pt.id === "A" || pt.id === "B" || pt.id === "C"
              : pt.id !== "Q" || selectedStage >= 2;
          const isSectionLit = selectedStage >= 3 && (isSeed || isInter);
          const dotClass = isInter
            ? "axo-sp-story-dot is-inter"
            : isSeed
              ? "axo-sp-story-dot is-seed"
              : "axo-sp-story-dot is-vertex";
          return (
            <g
              key={pt.id}
              className={`axo-sp-story-node${isVertexVisible ? " is-visible" : ""}`}
            >
              {(isSeed || isInter || isSectionLit) && (
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={isInter ? 11 : 8.5}
                  className={`axo-sp-story-halo${isInter ? " is-amber" : " is-blue"}`}
                />
              )}
              <circle
                cx={pt.x}
                cy={pt.y}
                r={isInter ? 5.2 : isSeed ? 4.5 : 3.2}
                className={dotClass}
              />
              <text
                x={pt.lx}
                y={pt.ly}
                textAnchor="middle"
                dominantBaseline="central"
                className={`axo-sp-story-svg-label${isInter ? " is-amber" : isSeed ? " is-blue" : ""}`}
              >
                {pt.label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Single-line fixed-height bottom verification strip (0.000 CLS across mobile & desktop) */}
      <div className="axo-sp-story-bottom-bar">
        <div className="axo-sp-story-metric-group">
          <span className={`axo-sp-story-metric-pill${selectedStage < 2 ? " is-muted" : ""}`}>
            MN = 2
          </span>
          <span className={`axo-sp-story-metric-pill${selectedStage < 2 ? " is-muted" : ""}`}>
            PQ = 4
          </span>
          <span className={`axo-sp-story-metric-pill${selectedStage < 2 ? " is-muted" : ""}`}>
            MQ = NP = 2√2
          </span>
          <span
            className={`axo-sp-story-metric-pill${
              selectedStage >= 3 ? " is-highlight" : " is-muted"
            }`}
          >
            S(MNPQ) = 3√7
          </span>
        </div>
      </div>
    </div>
  );
}
