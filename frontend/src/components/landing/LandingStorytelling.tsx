import { useEffect, useMemo, useRef, useState } from "react";
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
    x: SVG_W / 2 + (camX / camZ) * scale,
    y: SVG_H / 2 - 6 - (camY / camZ) * scale,
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

const PROMPT_TOKENS = [
  { id: "tok-solid", text: "Lăng trụ đều ABC.A′B′C′", minStage: 0, tone: "blue" },
  { id: "tok-seeds", text: "M ∈ AB, N ∈ AC, P ∈ CC′", minStage: 0, tone: "blue" },
  { id: "tok-parallel", text: "MN // BC", minStage: 1, tone: "blue" },
  { id: "tok-cut", text: "Q = (MNP) ∩ BB′", minStage: 2, tone: "amber" },
  { id: "tok-result", text: "Hình thang cân MNPQ", minStage: 3, tone: "amber" },
] as const;

export function LandingStorytelling() {
  const sample = LANDING_PRISM_STORY_SPEC;
  const milestones = sample.milestones;

  const runwayRef = useRef<HTMLDivElement | null>(null);
  const manualLockUntilRef = useRef<number>(0);
  const [selectedStage, setSelectedStage] = useState(0);
  const [isMobileOrReduced, setIsMobileOrReduced] = useState(false);

  const projected = useMemo(() => {
    const cam = sample.defaultCamera;
    const look = sample.defaultLookAt;
    const pts: Record<string, Point2D> = {};
    for (const pt of sample.points) {
      const pr = projectPoint(pt.pos, cam, look);
      pts[pt.id] = { id: pt.id, label: pt.label, role: pt.role, x: pr.x, y: pr.y };
    }

    // Determine back/front solid edges from outward triangle/quad normals
    const centroid: Vec3Tuple = [0, 0, 0];
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
    void centroid;

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
      pc[0] + (q[0] - pc[0]) * 0.8,
      pc[1] + (q[1] - pc[1]) * 0.8,
      pc[2] + (q[2] - pc[2]) * 0.8,
    ]);
    const planePts = shrunkenPlane.map((q) => projectPoint(q, cam, look));
    const sectionPts = sample.sectionLoop.map((id) => pts[id]);

    // Compute clean outward label offsets for vertices
    const visPts = Object.values(pts);
    const meanX = visPts.reduce((acc, p) => acc + p.x, 0) / Math.max(1, visPts.length);
    const meanY = visPts.reduce((acc, p) => acc + p.y, 0) / Math.max(1, visPts.length);

    const labels = sample.points.map((pt) => {
      const p2 = pts[pt.id];
      const vx = p2.x - meanX;
      const vy = p2.y - meanY;
      const len = Math.hypot(vx, vy) || 1;
      const dist = pt.role === "vertex" ? 18 : 20;
      const customBias: Record<string, readonly [number, number]> = {
        C: [0, 17],
        C_prime: [0, -17],
        N: [-16, 10],
        P: [16, -6],
        Q: [18, 0],
        M: [0, 18],
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

  useEffect(() => {
    if (typeof window === "undefined") return;

    const checkMode = () => {
      const reduced =
        typeof window.matchMedia === "function" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const mobile = window.innerWidth <= 920;
      setIsMobileOrReduced(reduced || mobile);
    };
    checkMode();

    let rafPending = 0;
    const syncDiscreteStage = () => {
      rafPending = 0;
      const now = typeof performance !== "undefined" ? performance.now() : Date.now();
      if (now < manualLockUntilRef.current) return;
      const runway = runwayRef.current;
      if (!runway) return;
      const rect = runway.getBoundingClientRect();
      const viewportH = window.innerHeight || 900;
      if (rect.bottom < 0 || rect.top > viewportH) return;
      const maxTravel = Math.max(1, rect.height - viewportH * 0.66);
      const passed = Math.max(0, viewportH * 0.24 - rect.top);
      const ratio = Math.max(0, Math.min(1, passed / maxTravel));
      const mapped = Math.min(milestones.length - 1, Math.floor(ratio * milestones.length * 0.999));
      setSelectedStage((prev) => (prev === mapped ? prev : mapped));
    };

    const scheduleSync = () => {
      if (rafPending === 0) {
        rafPending = window.requestAnimationFrame(syncDiscreteStage);
      }
    };

    const onResize = () => {
      checkMode();
      scheduleSync();
    };

    syncDiscreteStage();
    window.addEventListener("scroll", scheduleSync, { passive: true });
    window.addEventListener("resize", onResize, { passive: true });
    return () => {
      if (rafPending !== 0) window.cancelAnimationFrame(rafPending);
      window.removeEventListener("scroll", scheduleSync);
      window.removeEventListener("resize", onResize);
    };
  }, [milestones.length]);

  const handleStageSelect = (idx: number) => {
    manualLockUntilRef.current = (typeof performance !== "undefined" ? performance.now() : Date.now()) + 750;
    setSelectedStage(idx);
    const runway = runwayRef.current;
    if (!isMobileOrReduced && runway && typeof window !== "undefined") {
      const rect = runway.getBoundingClientRect();
      const viewportH = window.innerHeight || 900;
      const maxTravel = Math.max(1, rect.height - viewportH * 0.66);
      const targetProgress = milestones.length > 1 ? idx / (milestones.length - 1) : 0;
      const runwayTopPageY = window.scrollY + rect.top;
      const destY = Math.max(0, runwayTopPageY - viewportH * 0.16 + targetProgress * maxTravel);
      window.scrollTo({ top: destY, behavior: "smooth" });
    }
  };

  const handleStageKeyDown = (e: React.KeyboardEvent, currentIdx: number) => {
    if (e.key === "ArrowRight" || e.key === "ArrowDown") {
      e.preventDefault();
      const next = Math.min(milestones.length - 1, currentIdx + 1);
      handleStageSelect(next);
    } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
      e.preventDefault();
      const prev = Math.max(0, currentIdx - 1);
      handleStageSelect(prev);
    } else if (e.key === "Home") {
      e.preventDefault();
      handleStageSelect(0);
    } else if (e.key === "End") {
      e.preventDefault();
      handleStageSelect(milestones.length - 1);
    }
  };

  const activeStage = milestones[selectedStage] ?? milestones[0];
  const stagePointSummary = activeStage.visiblePoints.map((id) => {
    const pt = sample.pointMap[id];
    return pt ? `${pt.label}(${pt.domainXyz.map((n) => Number(n.toFixed(2))).join(", ")})` : id;
  });

  const { pts, edges, planePts, sectionPts, labels } = projected;

  return (
    <section
      id="cach-hoat-dong"
      className="axo-sp-story-section"
      aria-labelledby="landing-story-heading"
    >
      <div className="axo-sp-container">
        <div ref={runwayRef} className="axo-sp-story-runway">
          <div className="axo-sp-story-sticky">
            {/* Left structured learner narrative */}
            <div className="axo-sp-story-rail">
              <div className="axo-sp-section-head axo-sp-story-head">
                <p className="axo-sp-eyebrow">Cách Axo hoạt động</p>
                <h2 id="landing-story-heading" className="axo-sp-section-title">
                  Một bài toán, mở ra từng lớp không gian.
                </h2>
                <p className="axo-sp-section-lead">
                  Theo dõi khối lăng trụ <span className="axo-sp-mono">ABC.A′B′C′</span> đi từ giả
                  thiết tiếng Việt đến thiết diện hình thang cân{" "}
                  <span className="axo-sp-mono">MNPQ</span>.
                </p>
              </div>

              {/* Mobile / reduced-motion horizontal tabs */}
              <div className="axo-sp-story-pills" role="tablist" aria-label="Các chặng dựng hình">
                {milestones.map((st, idx) => (
                  <button
                    key={st.id}
                    id={`btn-landing-story-pill-${idx}`}
                    type="button"
                    role="tab"
                    aria-selected={selectedStage === idx}
                    className={`axo-sp-story-pill${selectedStage === idx ? " is-active" : ""}`}
                    onClick={() => handleStageSelect(idx)}
                    onKeyDown={(e) => handleStageKeyDown(e, idx)}
                  >
                    <span>{st.stepNumber}</span>
                    <span>{st.tag}</span>
                  </button>
                ))}
              </div>

              {/* Stable zero-CLS chapter stack (always mounted copy so scroll never shifts layout) */}
              <div className="axo-sp-story-chapters">
                {milestones.map((st, idx) => {
                  const isActive = idx === selectedStage;
                  const isPassed = idx < selectedStage;
                  return (
                    <button
                      key={st.id}
                      id={`btn-landing-story-step-${idx}`}
                      type="button"
                      className={`axo-sp-story-chapter${isActive ? " is-active" : ""}${isPassed ? " is-passed" : ""}`}
                      aria-current={isActive ? "step" : undefined}
                      onClick={() => handleStageSelect(idx)}
                      onKeyDown={(e) => handleStageKeyDown(e, idx)}
                    >
                      <span className="axo-sp-story-chapter-index">{st.stepNumber}</span>
                      <span className="axo-sp-story-chapter-body">
                        <span className="axo-sp-story-chapter-title-row">
                          <strong className="axo-sp-story-chapter-title">{st.tag}</strong>
                          <span className="axo-sp-story-chapter-meta">{st.title}</span>
                        </span>
                        <span className="axo-sp-story-chapter-copy">{st.summary}</span>
                      </span>
                    </button>
                  );
                })}
              </div>

              <details className="axo-sp-story-math-disclosure">
                <summary>Chi tiết tọa độ &amp; kiểm chứng hình học</summary>
                <div className="axo-sp-story-math-body">
                  <p>{activeStage.mathFact}</p>
                  <p>Mặt phẳng cắt (MNP): {sample.equationText}</p>
                  <p className="axo-sp-mono axo-sp-story-coord-line">
                    Điểm hiển thị: {stagePointSummary.join(" · ")}
                  </p>
                </div>
              </details>
            </div>

            {/* Right GPU-composited Option A Vector Motion Graphics Stage (0 WebGL contexts) */}
            <div className="axo-sp-story-visual-col">
              <div className="axo-sp-story-stage-frame">
                <div
                  id="landing-storytelling-scene"
                  className="axo-sp-story-canvas"
                  data-stage={selectedStage}
                  role="img"
                  aria-label={`Minh họa chặng ${activeStage.stepNumber} — ${activeStage.tag}: ${activeStage.title}`}
                >
                  <div className="axo-sp-story-top-bar">
                    <span className="axo-sp-scene-chip">
                      Chặng {activeStage.stepNumber} · {activeStage.tag}
                    </span>
                    <span className={`axo-sp-story-state-chip${selectedStage >= 2 ? " is-amber" : ""}`}>
                      {selectedStage >= 2 ? "Hình thang cân MNPQ" : sample.shortName}
                    </span>
                  </div>

                  {/* Interactive Vietnamese Prompt Highlight Strip */}
                  <div className="axo-sp-story-tokens" aria-hidden="true">
                    {PROMPT_TOKENS.map((tok) => {
                      const lit = selectedStage >= tok.minStage;
                      return (
                        <span
                          key={tok.id}
                          className={`axo-sp-story-token${lit ? ` is-lit is-${tok.tone}` : ""}`}
                        >
                          {tok.text}
                        </span>
                      );
                    })}
                  </div>

                  <svg
                    className="axo-sp-story-svg"
                    viewBox={`0 0 ${SVG_W} ${SVG_H}`}
                    preserveAspectRatio="xMidYMid meet"
                    aria-hidden="true"
                  >
                    {/* Subtle base fill (ABC) */}
                    <polygon
                      points={`${pts.A.x.toFixed(1)},${pts.A.y.toFixed(1)} ${pts.B.x.toFixed(1)},${pts.B.y.toFixed(1)} ${pts.C.x.toFixed(1)},${pts.C.y.toFixed(1)}`}
                      className="axo-sp-story-base-poly"
                    />

                    {/* Stage >= 1: Frosted cutting plane (MNP) */}
                    <polygon
                      points={planePts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")}
                      className={`axo-sp-story-plane${selectedStage >= 1 ? " is-shown" : ""}`}
                    />

                    {/* Solid wireframe with true front-solid / back-dashed visibility */}
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

                    {/* Stage >= 1: Parallel relationship highlight (MN // BC) */}
                    <line
                      x1={pts.B.x}
                      y1={pts.B.y}
                      x2={pts.C.x}
                      y2={pts.C.y}
                      className={`axo-sp-story-parallel-line${selectedStage >= 1 ? " is-shown" : ""}`}
                    />
                    <line
                      x1={pts.M.x}
                      y1={pts.M.y}
                      x2={pts.N.x}
                      y2={pts.N.y}
                      className={`axo-sp-story-parallel-line${selectedStage >= 1 ? " is-shown" : ""}`}
                    />

                    {/* Stage === 3: Translucent amber isosceles trapezoid fill */}
                    <polygon
                      points={sectionPts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")}
                      className={`axo-sp-story-section-fill${selectedStage >= 3 ? " is-shown" : ""}`}
                    />

                    {/* Stage >= 2: Progressive perimeter drawing of M-N-P-Q */}
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

                    {/* Point vertices, seeds (M,N,P), and intersection (Q) */}
                    {labels.map((pt) => {
                      const showPoint = pt.id !== "Q" || selectedStage >= 2;
                      const isSeed = pt.role === "seed";
                      const isInter = pt.role === "intersection";
                      const isSectionLit =
                        selectedStage >= 3 && (isSeed || isInter);
                      const dotClass = isInter
                        ? "axo-sp-story-dot is-inter"
                        : isSeed
                          ? "axo-sp-story-dot is-seed"
                          : "axo-sp-story-dot is-vertex";
                      return (
                        <g
                          key={pt.id}
                          className={`axo-sp-story-node${showPoint ? " is-visible" : ""}`}
                        >
                          {(isSeed || isInter || isSectionLit) && (
                            <circle
                              cx={pt.x}
                              cy={pt.y}
                              r={isInter ? 10 : 8}
                              className={`axo-sp-story-halo${isInter ? " is-amber" : " is-blue"}`}
                            />
                          )}
                          <circle
                            cx={pt.x}
                            cy={pt.y}
                            r={isInter ? 5.2 : isSeed ? 4.6 : 3.2}
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

                  {/* Bottom separated verification metrics (always mounted -> CLS 0) */}
                  <div className="axo-sp-story-bottom-bar">
                    <div className="axo-sp-story-metric-group">
                      <span className={`axo-sp-story-metric-pill${selectedStage < 1 ? " is-muted" : ""}`}>
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
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
