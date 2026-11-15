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
  const [hasCameraMoved, setHasCameraMoved] = useState<boolean>(false);

  const sample = landingSampleById(selectedId);
  const activeStage = sample.milestones[stepIndex] ?? sample.milestones[sample.milestones.length - 1];
  const isFinalVerifiedStage = stepIndex === sample.milestones.length - 1;

  const handleSelectSample = (nextId: string) => {
    setSelectedId(nextId);
    setStepIndex(3);
    setOrbitResetNonce((n) => n + 1);
    setHasCameraMoved(false);
  };

  const handleResetCamera = () => {
    setOrbitResetNonce((n) => n + 1);
    setHasCameraMoved(false);
  };

  const handleStepKeyDown = (e: React.KeyboardEvent, idx: number) => {
    if (e.key === "ArrowRight") {
      e.preventDefault();
      setStepIndex(Math.min(sample.milestones.length - 1, idx + 1));
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      setStepIndex(Math.max(0, idx - 1));
    } else if (e.key === "Home") {
      e.preventDefault();
      setStepIndex(0);
    } else if (e.key === "End") {
      e.preventDefault();
      setStepIndex(sample.milestones.length - 1);
    }
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
                data-visible={hasCameraMoved ? "true" : "false"}
                aria-hidden={!hasCameraMoved}
                tabIndex={hasCameraMoved ? 0 : -1}
                onClick={handleResetCamera}
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
              lookAt={activeStage.lookAt}
              interactiveOrbit={true}
              orbitResetNonce={orbitResetNonce}
              onUserOrbit={() => setHasCameraMoved(true)}
              bottomHint={
                hasCameraMoved ? undefined : "Kéo để xoay 3D · Phím mũi tên để đổi góc"
              }
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
                  onKeyDown={(e) => handleStepKeyDown(e, idx)}
                >
                  {st.stepNumber}
                </button>
              ))}
            </div>

            <div className="axo-sp-demo-step-detail">
              <h3 className="axo-sp-demo-step-title">{activeStage.title}</h3>
              <p className="axo-sp-demo-step-desc">{activeStage.summary}</p>
            </div>

            {/* Separated Verification / Stage Facts (final results appear strictly on the concluding stage) */}
            <div
              className="axo-sp-demo-metrics"
              aria-label={isFinalVerifiedStage ? "Kết quả kiểm chứng chính xác" : `Dữ kiện bước ${activeStage.stepNumber}`}
            >
              {isFinalVerifiedStage ? (
                sample.verifiedMetrics.map((metric) => (
                  <div key={`${sample.id}-${metric.label}`} className="axo-sp-demo-metric-chip">
                    <span className="axo-sp-demo-metric-label">{metric.label}</span>
                    <span className="axo-sp-demo-metric-val">{metric.value}</span>
                  </div>
                ))
              ) : (
                <div className="axo-sp-demo-metric-chip is-stage-note">
                  <span className="axo-sp-demo-metric-label">{activeStage.tag}</span>
                  <span className="axo-sp-demo-metric-val">{activeStage.mathFact}</span>
                </div>
              )}
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
