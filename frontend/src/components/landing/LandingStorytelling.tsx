import { useEffect, useRef, useState } from "react";
import { LANDING_PYRAMID_SAMPLE, type Vec3Tuple } from "./landing-geometry-data";
import { SpatialSceneCanvas } from "./LandingHeroScene3D";

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function lerpVec3(a: Vec3Tuple, b: Vec3Tuple, t: number): Vec3Tuple {
  return [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
}

export function LandingStorytelling() {
  const sample = LANDING_PYRAMID_SAMPLE;
  const milestones = sample.milestones;

  const runwayRef = useRef<HTMLDivElement | null>(null);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [selectedStage, setSelectedStage] = useState(0);
  const [isMobileOrReduced, setIsMobileOrReduced] = useState(false);

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
    const measureScroll = () => {
      rafPending = 0;
      const runway = runwayRef.current;
      if (!runway) return;
      const rect = runway.getBoundingClientRect();
      const viewportH = window.innerHeight || 900;
      const maxTravel = Math.max(1, rect.height - viewportH * 0.72);
      const passed = Math.max(0, viewportH * 0.22 - rect.top);
      const ratio = Math.max(0, Math.min(1, passed / maxTravel));
      setScrollProgress(ratio);
      const mapped = Math.min(milestones.length - 1, Math.floor(ratio * milestones.length * 0.999));
      setSelectedStage(mapped);
    };

    const onScrollOrResize = () => {
      checkMode();
      if (rafPending === 0) {
        rafPending = window.requestAnimationFrame(measureScroll);
      }
    };

    measureScroll();
    window.addEventListener("scroll", onScrollOrResize, { passive: true });
    window.addEventListener("resize", onScrollOrResize, { passive: true });
    return () => {
      if (rafPending !== 0) window.cancelAnimationFrame(rafPending);
      window.removeEventListener("scroll", onScrollOrResize);
      window.removeEventListener("resize", onScrollOrResize);
    };
  }, [milestones.length]);

  const handleStageSelect = (idx: number) => {
    setSelectedStage(idx);
    const runway = runwayRef.current;
    if (!isMobileOrReduced && runway && typeof window !== "undefined") {
      const rect = runway.getBoundingClientRect();
      const viewportH = window.innerHeight || 900;
      const maxTravel = Math.max(1, rect.height - viewportH * 0.72);
      const targetProgress = milestones.length > 1 ? idx / (milestones.length - 1) : 0;
      const runwayTopPageY = window.scrollY + rect.top;
      const destY = Math.max(0, runwayTopPageY - viewportH * 0.16 + targetProgress * maxTravel);
      window.scrollTo({ top: destY, behavior: "smooth" });
    }
  };

  // Continuous interpolation on desktop scroll; direct stage snapshot on mobile / reduced motion
  const continuousU = isMobileOrReduced
    ? selectedStage
    : Math.max(0, Math.min(milestones.length - 1, scrollProgress * (milestones.length - 1)));
  const lowerIdx = Math.min(milestones.length - 1, Math.floor(continuousU));
  const upperIdx = Math.min(milestones.length - 1, lowerIdx + 1);
  const frac = continuousU - lowerIdx;

  const lowerStage = milestones[lowerIdx];
  const upperStage = milestones[upperIdx];
  const activeStage = milestones[selectedStage] ?? milestones[0];

  const interpPlaneOp = lerp(lowerStage.planeOpacity, upperStage.planeOpacity, frac);
  const interpSecProg = lerp(lowerStage.sectionProgress, upperStage.sectionProgress, frac);
  const interpSecFill = lerp(lowerStage.sectionFillOpacity, upperStage.sectionFillOpacity, frac);
  const interpCamera = lerpVec3(lowerStage.cameraPos, upperStage.cameraPos, frac);

  const stagePointSummary = activeStage.visiblePoints.map((id: string) => {
    const pt = sample.pointMap[id];
    return pt ? `${pt.label}(${pt.pos.map((n) => Number(n.toFixed(2))).join(", ")})` : id;
  });

  return (
    <section
      id="cach-hoat-dong"
      className="axo-sp-story-section"
      aria-labelledby="landing-story-heading"
    >
      <div className="axo-sp-container">
        <div ref={runwayRef} className="axo-sp-story-runway">
          <div className="axo-sp-story-sticky">
            {/* Left continuous narrative column */}
            <div className="axo-sp-story-rail">
              <div className="axo-sp-section-head axo-sp-story-head">
                <p className="axo-sp-eyebrow">Cách Axo hoạt động</p>
                <h2 id="landing-story-heading" className="axo-sp-section-title">
                  Một bài toán, mở ra từng lớp không gian.
                </h2>
                <p className="axo-sp-section-lead">
                  Cuộn để theo dõi khối chóp <span className="axo-sp-mono">S.ABCD</span> đi từ giả
                  thiết tiếng Việt đến thiết diện khép kín và tỉ lệ{" "}
                  <span className="axo-sp-mono">{sample.answerBadge}</span>.
                </p>
              </div>

              {/* Mobile / reduced-motion horizontal pills */}
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
                  >
                    <span>{st.stepNumber}</span>
                    <span>{st.tag}</span>
                  </button>
                ))}
              </div>

              {/* Clean editorial chapter list (only active chapter expands body) */}
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
                    >
                      <span className="axo-sp-story-chapter-index">{st.stepNumber}</span>
                      <span className="axo-sp-story-chapter-body">
                        <span className="axo-sp-story-chapter-title-row">
                          <strong className="axo-sp-story-chapter-title">{st.tag}</strong>
                          <span className="axo-sp-story-chapter-meta">{st.title}</span>
                        </span>
                        {isActive && (
                          <span className="axo-sp-story-chapter-copy">{st.summary}</span>
                        )}
                      </span>
                    </button>
                  );
                })}
              </div>

              <details className="axo-sp-story-math-disclosure">
                <summary>Chi tiết tọa độ &amp; kiểm chứng hình học</summary>
                <div className="axo-sp-story-math-body">
                  <p>{activeStage.mathFact}</p>
                  <p>{sample.equationText}</p>
                  <p className="axo-sp-mono axo-sp-story-coord-line">
                    Điểm hiển thị: {stagePointSummary.join(" · ")}
                  </p>
                </div>
              </details>
            </div>

            {/* Right continuous spatial demonstration stage */}
            <div className="axo-sp-story-visual-col">
              <div className="axo-sp-story-stage-frame">
                <SpatialSceneCanvas
                  sceneId="landing-storytelling-scene"
                  sample={sample}
                  visiblePoints={activeStage.visiblePoints}
                  activePoints={activeStage.activePoints}
                  showGuideEdges={activeStage.showGuideEdges}
                  planeOpacity={interpPlaneOp}
                  sectionProgress={interpSecProg}
                  sectionFillOpacity={interpSecFill}
                  cameraPos={interpCamera}
                  topBadgeLeft={`Chặng ${activeStage.stepNumber} · ${activeStage.tag}`}
                  topBadgeRight={selectedStage >= 2 ? sample.answerBadge : "S.ABCD"}
                  bottomCaption={activeStage.mathFact}
                  ariaLabel={`Minh họa chặng ${activeStage.stepNumber}: ${activeStage.title}`}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
