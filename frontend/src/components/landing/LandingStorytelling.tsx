import { useEffect, useRef, useState } from "react";
import { LANDING_PRISM_STORY_SPEC } from "./landing-geometry-data";
import { EXPLAINER_SCENES, LandingExplainerAnimation } from "./LandingExplainerAnimation";
import { StoryBridgeAccent } from "./LandingIllustrationAccents";

const AUTOPLAY_INTERVAL_MS = 3800;

export function LandingStorytelling() {
  const sample = LANDING_PRISM_STORY_SPEC;
  const milestones = sample.milestones;

  const runwayRef = useRef<HTMLDivElement | null>(null);
  const manualLockUntilRef = useRef<number>(0);
  const [selectedStage, setSelectedStage] = useState(0);
  const [autoPlaying, setAutoPlaying] = useState(true);
  const [inView, setInView] = useState(false);
  const [isMobileOrReduced, setIsMobileOrReduced] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const checkMode = () => {
      const reduced =
        typeof window.matchMedia === "function" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const mobile = window.innerWidth <= 920;
      setIsMobileOrReduced(reduced || mobile);
      if (reduced) {
        setAutoPlaying(false);
      }
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
      if (passed > 18) {
        setSelectedStage((prev) => (prev === mapped ? prev : mapped));
      }
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

    const io =
      typeof IntersectionObserver !== "undefined" && runwayRef.current
        ? new IntersectionObserver(
            (entries) => {
              setInView(entries.some((entry) => entry.isIntersecting));
            },
            { threshold: 0.12 },
          )
        : null;
    if (runwayRef.current) {
      io?.observe(runwayRef.current);
    }

    syncDiscreteStage();
    window.addEventListener("scroll", scheduleSync, { passive: true });
    window.addEventListener("resize", onResize, { passive: true });
    return () => {
      if (rafPending !== 0) window.cancelAnimationFrame(rafPending);
      io?.disconnect();
      window.removeEventListener("scroll", scheduleSync);
      window.removeEventListener("resize", onResize);
    };
  }, [milestones.length]);

  useEffect(() => {
    if (!autoPlaying || !inView || typeof window === "undefined") return;
    if (
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      return;
    }

    const timer = window.setInterval(() => {
      if (typeof document !== "undefined" && document.hidden) return;
      const now = typeof performance !== "undefined" ? performance.now() : Date.now();
      if (now < manualLockUntilRef.current) return;
      setSelectedStage((prev) => (prev + 1) % EXPLAINER_SCENES.length);
    }, AUTOPLAY_INTERVAL_MS);

    return () => {
      window.clearInterval(timer);
    };
  }, [autoPlaying, inView]);

  const handleStageSelect = (idx: number) => {
    manualLockUntilRef.current =
      (typeof performance !== "undefined" ? performance.now() : Date.now()) + 4200;
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
      handleStageSelect(Math.min(milestones.length - 1, currentIdx + 1));
    } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
      e.preventDefault();
      handleStageSelect(Math.max(0, currentIdx - 1));
    } else if (e.key === "Home") {
      e.preventDefault();
      handleStageSelect(0);
    } else if (e.key === "End") {
      e.preventDefault();
      handleStageSelect(milestones.length - 1);
    }
  };

  const activeStage = milestones[selectedStage] ?? milestones[0];
  const activeScene = EXPLAINER_SCENES[selectedStage] ?? EXPLAINER_SCENES[0];
  const stagePointSummary = activeStage.visiblePoints.map((id) => {
    const pt = sample.pointMap[id];
    return pt ? `${pt.label}(${pt.domainXyz.map((n) => Number(n.toFixed(2))).join(", ")})` : id;
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
            {/* Left narrative rail — "Một thời điểm, một ý chính" */}
            <div className="axo-sp-story-rail">
              <div className="axo-sp-section-head axo-sp-story-head">
                <div className="axo-sp-story-eyebrow-row">
                  <p className="axo-sp-eyebrow">Cách Axo hoạt động</p>
                  <StoryBridgeAccent />
                </div>
                <h2 id="landing-story-heading" className="axo-sp-section-title">
                  Một bài toán, mở ra từng lớp không gian.
                </h2>
                <p className="axo-sp-section-lead">
                  Theo dõi khối lăng trụ <span className="axo-sp-mono">ABC.A′B′C′</span> chuyển
                  hóa từ đề bài tiếng Việt thành thiết diện <span className="axo-sp-mono">MNPQ</span>.
                </p>
              </div>

              {/* Mobile / reduced-motion horizontal scene switcher (non-wrapping single strip) */}
              <div className="axo-sp-story-pills" role="tablist" aria-label="Các chặng minh họa">
                {EXPLAINER_SCENES.map((sc, idx) => (
                  <button
                    key={sc.id}
                    id={`btn-landing-story-pill-${idx}`}
                    type="button"
                    role="tab"
                    aria-selected={selectedStage === idx}
                    className={`axo-sp-story-pill${selectedStage === idx ? " is-active" : ""}`}
                    onClick={() => handleStageSelect(idx)}
                    onKeyDown={(e) => handleStageKeyDown(e, idx)}
                  >
                    <span>{sc.stepNumber}</span>
                    <span>{sc.shortLabel}</span>
                  </button>
                ))}
              </div>

              {/* Compact Desktop step rail (clean titles only — zero wall of multi-paragraph cards) */}
              <div className="axo-sp-story-chapters">
                {EXPLAINER_SCENES.map((sc, idx) => {
                  const isActive = idx === selectedStage;
                  const isPassed = idx < selectedStage;
                  return (
                    <button
                      key={sc.id}
                      id={`btn-landing-story-step-${idx}`}
                      type="button"
                      className={`axo-sp-story-chapter${isActive ? " is-active" : ""}${isPassed ? " is-passed" : ""}`}
                      aria-current={isActive ? "step" : undefined}
                      onClick={() => handleStageSelect(idx)}
                      onKeyDown={(e) => handleStageKeyDown(e, idx)}
                    >
                      <span className="axo-sp-story-chapter-index">{sc.stepNumber}</span>
                      <span className="axo-sp-story-chapter-title">{sc.shortLabel}</span>
                    </button>
                  );
                })}
              </div>

              {/* Single focused active-scene insight box (fixed height -> 0 CLS) */}
              <div className="axo-sp-story-active-card" aria-live="polite">
                <h3 className="axo-sp-story-active-title">{activeScene.headline}</h3>
                <p className="axo-sp-story-active-desc">{activeScene.summary}</p>
              </div>

              <details className="axo-sp-story-math-disclosure">
                <summary>Chi tiết tọa độ &amp; kiểm chứng hình học</summary>
                <div className="axo-sp-story-math-body">
                  <p>
                    <strong>{activeStage.tag}:</strong> {activeStage.mathFact}
                  </p>
                  <p>Mặt phẳng cắt (MNP): {sample.equationText}</p>
                  <p className="axo-sp-mono axo-sp-story-coord-line">
                    Điểm hiển thị: {stagePointSummary.join(" · ")}
                  </p>
                  <p className="axo-sp-story-coord-line">
                    Tiến trình: {milestones.map((m) => m.tag).join(" → ")}
                  </p>
                </div>
              </details>
            </div>

            {/* Right Bespoke 4-Scene Animated Product Explainer */}
            <div className="axo-sp-story-visual-col">
              <div className="axo-sp-story-stage-frame">
                <LandingExplainerAnimation
                  selectedStage={selectedStage}
                  autoPlaying={autoPlaying}
                  onToggleAutoPlay={() => setAutoPlaying((v) => !v)}
                  onUserInteract={() => {
                    manualLockUntilRef.current =
                      (typeof performance !== "undefined" ? performance.now() : Date.now()) + 2800;
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
