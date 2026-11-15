import { useState } from "react";
import {
  LANDING_SHOWCASE_SAMPLES,
  landingSampleById,
  openSampleInWorkspace,
} from "./landing-geometry-data";
import { SpatialSceneCanvas } from "./LandingHeroScene3D";

export function LandingInteractiveDemo() {
  const [selectedSampleId, setSelectedSampleId] = useState<string>(
    LANDING_SHOWCASE_SAMPLES[0].id,
  );
  const [stepIdx, setStepIdx] = useState<number>(3);
  const [orbitResetNonce, setOrbitResetNonce] = useState<number>(0);
  const [hasOrbited, setHasOrbited] = useState<boolean>(false);

  const sample = landingSampleById(selectedSampleId);
  const milestones = sample.milestones;
  const activeStep = milestones[Math.min(stepIdx, milestones.length - 1)] ?? milestones[0];

  const handleSelectSample = (nextId: string) => {
    setSelectedSampleId(nextId);
    const nextSample = landingSampleById(nextId);
    setStepIdx(nextSample.milestones.length - 1);
    setOrbitResetNonce((n) => n + 1);
    setHasOrbited(false);
  };

  return (
    <section
      id="trai-nghiem"
      className="axo-sp-demo"
      aria-labelledby="landing-demo-heading"
    >
      <div className="axo-sp-container">
        <div className="axo-sp-section-head">
          <span className="axo-sp-section-kicker">Trải nghiệm trực tiếp</span>
          <h2 id="landing-demo-heading" className="axo-sp-section-title">
            Xoay mô hình, bước qua từng nét dựng và mở ngay bài mẫu thật
          </h2>
          <p className="axo-sp-section-lead">
            Thử tương tác trực tiếp với hai bài toán thiết diện chuẩn từ thư viện Axo trước khi
            vào xưởng dựng hình đầy đủ.
          </p>
        </div>

        <div id="landing-product-showcase" className="axo-sp-showcase-card">
          <div className="axo-sp-showcase-bar">
            <div className="axo-sp-sample-tabs" role="tablist" aria-label="Chọn bài mẫu tương tác">
              {LANDING_SHOWCASE_SAMPLES.map((item) => {
                const isActive = item.id === sample.id;
                return (
                  <button
                    key={item.id}
                    id={`btn-demo-sample-${item.id}`}
                    type="button"
                    role="tab"
                    aria-selected={isActive}
                    className={`axo-sp-sample-tab${isActive ? " is-active" : ""}`}
                    onClick={() => handleSelectSample(item.id)}
                  >
                    <span>{item.shortName}</span>
                  </button>
                );
              })}
            </div>

            <button
              type="button"
              id="btn-landing-showcase-reset"
              className="axo-sp-reset-btn"
              onClick={() => {
                setOrbitResetNonce((n) => n + 1);
                setHasOrbited(false);
              }}
            >
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path
                  d="M2.5 8a5.5 5.5 0 1 1 1.4 3.67M2.5 4.25V8h3.75"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <span>Đặt lại góc nhìn</span>
            </button>
          </div>

          <div className="axo-sp-showcase-body">
            <div className="axo-sp-showcase-stage">
              <SpatialSceneCanvas
                sceneId="landing-demo-scene"
                sample={sample}
                visiblePoints={activeStep.visiblePoints}
                activePoints={activeStep.activePoints}
                showGuideEdges={activeStep.showGuideEdges}
                planeOpacity={activeStep.planeOpacity}
                sectionProgress={activeStep.sectionProgress}
                sectionFillOpacity={activeStep.sectionFillOpacity}
                cameraPos={activeStep.cameraPos}
                lookAt={activeStep.lookAt}
                interactiveOrbit
                orbitResetNonce={orbitResetNonce}
                compact
                onUserOrbit={() => setHasOrbited(true)}
                topBadgeLeft={sample.categoryLabel}
                topBadgeRight={sample.answerBadge}
                bottomCaption={`Bước ${stepIdx + 1}/${milestones.length}: ${activeStep.tag}`}
                bottomHint={hasOrbited ? "Đang xoay tự do" : "Kéo hoặc dùng phím mũi tên để xoay"}
                ariaLabel={`Khung 3D tương tác: ${sample.title}`}
              />
            </div>

            <div className="axo-sp-showcase-side">
              <div>
                <div className="axo-sp-problem-box">
                  <div className="axo-sp-side-label">Đề bài xác thực</div>
                  <p className="axo-sp-problem-text">{sample.problemText}</p>
                </div>

                <div className="axo-sp-stepper" style={{ marginTop: 14 }}>
                  <div className="axo-sp-side-label">Mốc dựng hình</div>
                  <div className="axo-sp-milestone-pills">
                    {milestones.map((m, i) => (
                      <button
                        key={m.id}
                        id={`btn-demo-step-${i}`}
                        type="button"
                        aria-pressed={i === stepIdx}
                        className={`axo-sp-milestone-pill${i === stepIdx ? " is-active" : ""}`}
                        onClick={() => setStepIdx(i)}
                      >
                        {m.stepNumber} · {m.tag}
                      </button>
                    ))}
                  </div>

                  <div className="axo-sp-step-readout" aria-live="polite">
                    <h3 className="axo-sp-step-readout-title">{activeStep.title}</h3>
                    <p className="axo-sp-step-readout-desc">{activeStep.summary}</p>
                    <div className="axo-sp-step-readout-math">{activeStep.mathFact}</div>
                  </div>

                  <div className="axo-sp-step-nav">
                    <button
                      type="button"
                      id="btn-demo-prev-step"
                      className="axo-sp-step-btn"
                      disabled={stepIdx <= 0}
                      onClick={() => setStepIdx((i) => Math.max(0, i - 1))}
                    >
                      ← Bước trước
                    </button>
                    <button
                      type="button"
                      id="btn-demo-next-step"
                      className="axo-sp-step-btn"
                      disabled={stepIdx >= milestones.length - 1}
                      onClick={() => setStepIdx((i) => Math.min(milestones.length - 1, i + 1))}
                    >
                      Bước tiếp →
                    </button>
                  </div>
                </div>
              </div>

              <div className="axo-sp-side-foot">
                <button
                  type="button"
                  id="btn-landing-open-showcase-3d"
                  className="axo-sp-btn-primary"
                  style={{ width: "100%" }}
                  onClick={() => openSampleInWorkspace(sample.id)}
                >
                  <span>Mở bài này trong Xưởng 3D</span>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                    <path
                      d="M3.5 8h9m0 0L9 4.5M12.5 8 9 11.5"
                      stroke="currentColor"
                      strokeWidth="1.6"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
