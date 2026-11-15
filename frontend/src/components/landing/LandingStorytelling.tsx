import { useEffect, useRef, useState } from "react";
import { LANDING_PYRAMID_SAMPLE } from "./landing-geometry-data";
import { SpatialSceneCanvas } from "./LandingHeroScene3D";

export function LandingStorytelling() {
  const milestones = LANDING_PYRAMID_SAMPLE.milestones;
  const [activeIndex, setActiveIndex] = useState<number>(0);
  const cardRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const manualSelectLockRef = useRef<number>(0);

  useEffect(() => {
    if (typeof window === "undefined" || typeof document === "undefined") return;

    let rafId = 0;
    const syncActiveCardOnScroll = () => {
      rafId = 0;
      if (Date.now() < manualSelectLockRef.current) return;
      // Do not fight manual reading on narrow viewports where visual stage stacks above cards
      if (window.innerWidth <= 920) return;

      const targetLine = window.innerHeight * 0.44;
      let bestIdx = 0;
      let bestDist = Infinity;

      for (let i = 0; i < cardRefs.current.length; i++) {
        const el = cardRefs.current[i];
        if (!el) continue;
        const rect = el.getBoundingClientRect();
        const center = rect.top + rect.height * 0.5;
        const dist = Math.abs(center - targetLine);
        if (dist < bestDist) {
          bestDist = dist;
          bestIdx = i;
        }
      }

      // Only track while the storytelling section is within the viewport band
      const firstRect = cardRefs.current[0]?.getBoundingClientRect();
      const lastRect = cardRefs.current[cardRefs.current.length - 1]?.getBoundingClientRect();
      if (firstRect && lastRect && firstRect.top < window.innerHeight * 0.85 && lastRect.bottom > 100) {
        setActiveIndex(bestIdx);
      }
    };

    const schedule = () => {
      if (rafId !== 0) return;
      rafId = window.requestAnimationFrame(syncActiveCardOnScroll);
    };

    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule, { passive: true });
    return () => {
      if (rafId !== 0) window.cancelAnimationFrame(rafId);
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
    };
  }, []);

  const current = milestones[activeIndex] ?? milestones[0];

  return (
    <section
      id="cach-hoat-dong"
      className="axo-sp-story"
      aria-labelledby="landing-story-heading"
    >
      <div className="axo-sp-container">
        <div className="axo-sp-section-head">
          <span className="axo-sp-section-kicker">Cách Axo hoạt động</span>
          <h2 id="landing-story-heading" className="axo-sp-section-title">
            Từ giả thiết tiếng Việt đến hình khối không gian nhất quán
          </h2>
          <p className="axo-sp-section-lead">
            Mỗi bước dựng hình gắn liền với một quan hệ toán học xác thực trên cùng một mô hình
            duy nhất, giúp học sinh theo kịp mạch suy luận thay vì đoán hình trong tưởng tượng.
          </p>
        </div>

        <div className="axo-sp-story-grid">
          <div className="axo-sp-story-steps" role="list" aria-label="Bốn chặng dựng hình Axo">
            {milestones.map((stage, idx) => {
              const isActive = idx === activeIndex;
              return (
                <button
                  key={stage.id}
                  id={`btn-story-stage-${idx}`}
                  ref={(el) => {
                    cardRefs.current[idx] = el;
                  }}
                  type="button"
                  aria-pressed={isActive}
                  className={`axo-sp-story-card${isActive ? " is-active" : ""}`}
                  onClick={() => {
                    manualSelectLockRef.current = Date.now() + 900;
                    setActiveIndex(idx);
                  }}
                >
                  <div className="axo-sp-story-card-top">
                    <span className="axo-sp-step-index">{stage.stepNumber}</span>
                    <span className="axo-sp-step-tag">{stage.tag}</span>
                  </div>
                  <h3 className="axo-sp-story-card-title">{stage.title}</h3>
                  <p className="axo-sp-story-card-copy">{stage.summary}</p>
                  <div className="axo-sp-story-math">{stage.mathFact}</div>
                </button>
              );
            })}
          </div>

          <div className="axo-sp-story-sticky">
            <div className="axo-sp-story-panel">
              <div className="axo-sp-story-caption">
                <span className="axo-sp-story-caption-title">
                  {current.stepNumber} · {current.tag}
                </span>
                <span className="axo-sp-story-caption-eq">
                  {LANDING_PYRAMID_SAMPLE.equationText}
                </span>
              </div>

              <SpatialSceneCanvas
                sceneId="landing-story-scene"
                sample={LANDING_PYRAMID_SAMPLE}
                visiblePoints={current.visiblePoints}
                activePoints={current.activePoints}
                showGuideEdges={current.showGuideEdges}
                planeOpacity={current.planeOpacity}
                sectionProgress={current.sectionProgress}
                sectionFillOpacity={current.sectionFillOpacity}
                cameraPos={current.cameraPos}
                lookAt={current.lookAt}
                topBadgeLeft={LANDING_PYRAMID_SAMPLE.shortName}
                topBadgeRight={
                  activeIndex >= 3
                    ? LANDING_PYRAMID_SAMPLE.answerBadge
                    : `Chặng ${current.stepNumber}/04`
                }
                bottomCaption={current.title}
                ariaLabel={`Minh họa bước ${current.stepNumber}: ${current.title}`}
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
