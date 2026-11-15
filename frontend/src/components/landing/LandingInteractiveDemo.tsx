import { useState } from "react";
import {
  LANDING_SHOWCASE_SAMPLES,
  landingSampleById,
  openSampleInWorkspace,
} from "./landing-geometry-data";
import { SpatialSceneCanvas } from "./LandingHeroScene3D";

export function LandingInteractiveDemo() {
  const [selectedId, setSelectedId] = useState<string>(LANDING_SHOWCASE_SAMPLES[0].id);
  const [stepIndex, setStepIndex] = useState<number>(3);
  const [orbitResetNonce, setOrbitResetNonce] = useState<number>(0);

  const sample = landingSampleById(selectedId);
  const activeStage = sample.milestones[stepIndex] ?? sample.milestones[sample.milestones.length - 1];

  const handleSelectSample = (nextId: string) => {
    setSelectedId(nextId);
    setStepIndex(3);
    setOrbitResetNonce((n) => n + 1);
  };

  return (
    <section
      id="trai-nghiem"
      className="axo-sp-demo-section"
      aria-labelledby="landing-demo-heading"
    >
      <div className="axo-sp-container">
        <div className="axo-sp-demo-header">
          <div className="axo-sp-section-head">
            <p className="axo-sp-eyebrow">Trải nghiệm trực tiếp</p>
            <h2 id="landing-demo-heading" className="axo-sp-section-title">
              Xoay, cắt và kiểm chứng ngay trên mô hình 3D.
            </h2>
          </div>

          <div
            id="landing-demo-sample-tabs"
            className="axo-sp-demo-samples"
            role="tablist"
            aria-label="Chọn bài toán mẫu"
          >
            {LANDING_SHOWCASE_SAMPLES.map((item) => {
              const active = item.id === selectedId;
              return (
                <button
                  key={item.id}
                  id={`btn-landing-sample-${item.id}`}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  className={`axo-sp-sample-pill${active ? " is-active" : ""}`}
                  onClick={() => handleSelectSample(item.id)}
                >
                  {item.shortName}
                </button>
              );
            })}
          </div>
        </div>

        <div id="landing-product-showcase" className="axo-sp-demo-workbench">
          {/* Dominant Interactive 3D Viewport */}
          <div className="axo-sp-demo-canvas-wrap">
            <div className="axo-sp-demo-toolbar">
              <span className="axo-sp-demo-toolbar-title">{sample.title}</span>
              <button
                id="btn-landing-demo-reset"
                type="button"
                className="axo-sp-ghost-chip"
                onClick={() => setOrbitResetNonce((n) => n + 1)}
              >
                Đặt lại góc nhìn
              </button>
            </div>

            <SpatialSceneCanvas
              sceneId="landing-demo-scene"
              sample={sample}
              visiblePoints={activeStage.visiblePoints}
              activePoints={activeStage.activePoints}
              showGuideEdges={activeStage.showGuideEdges}
              planeOpacity={activeStage.planeOpacity}
              sectionProgress={activeStage.sectionProgress}
              sectionFillOpacity={activeStage.sectionFillOpacity}
              cameraPos={activeStage.cameraPos}
              interactiveOrbit={true}
              orbitResetNonce={orbitResetNonce}
              topBadgeLeft={`Bước ${stepIndex + 1}/${sample.milestones.length}`}
              topBadgeRight={sample.answerBadge}
              bottomCaption={activeStage.mathFact}
              bottomHint="Kéo để xoay 3D · Phím mũi tên để đổi góc"
              ariaLabel={`Mô hình 3D tương tác: ${sample.title}`}
            />
          </div>

          {/* Focused Step Control Column */}
          <aside className="axo-sp-demo-panel" aria-label="Điều khiển bước dựng">
            <div className="axo-sp-demo-step-head">
              <span className="axo-sp-demo-step-eyebrow">
                Bước {activeStage.stepNumber} · {activeStage.tag}
              </span>
            </div>

            <div className="axo-sp-demo-step-tabs" role="tablist" aria-label="Các bước dựng hình">
              {sample.milestones.map((st, idx) => (
                <button
                  key={st.id}
                  id={`btn-landing-demo-step-${idx}`}
                  type="button"
                  role="tab"
                  aria-selected={idx === stepIndex}
                  className={`axo-sp-step-tab${idx === stepIndex ? " is-active" : ""}`}
                  onClick={() => setStepIndex(idx)}
                >
                  {st.stepNumber}
                </button>
              ))}
            </div>

            <div className="axo-sp-demo-step-detail">
              <h3 className="axo-sp-demo-step-title">{activeStage.title}</h3>
              <p className="axo-sp-demo-step-desc">{activeStage.summary}</p>
            </div>

            <div className="axo-sp-demo-stepper-nav">
              <button
                id="btn-landing-demo-prev"
                type="button"
                className="axo-sp-ghost-chip"
                disabled={stepIndex <= 0}
                onClick={() => setStepIndex((i) => Math.max(0, i - 1))}
              >
                ← Bước trước
              </button>
              <button
                id="btn-landing-demo-next"
                type="button"
                className="axo-sp-ghost-chip"
                disabled={stepIndex >= sample.milestones.length - 1}
                onClick={() => setStepIndex((i) => Math.min(sample.milestones.length - 1, i + 1))}
              >
                Bước tiếp →
              </button>
            </div>

            <details className="axo-sp-demo-problem-disclosure">
              <summary>Xem đề bài gốc</summary>
              <p>{sample.problemText}</p>
            </details>

            <div className="axo-sp-demo-footer-action">
              <button
                id="btn-landing-open-showcase-3d"
                type="button"
                className="axo-sp-btn-primary axo-sp-btn-full"
                onClick={() => openSampleInWorkspace(sample.id)}
              >
                Mở trong Xưởng 3D
              </button>
            </div>
          </aside>
        </div>
      </div>
    </section>
  );
}
