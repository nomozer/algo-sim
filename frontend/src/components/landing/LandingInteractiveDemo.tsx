import { useState } from "react";
import { AnnotatedPhrase } from "./AnnotatedHeading";
import {
  LANDING_SHOWCASE_SAMPLES,
  landingSampleById,
  openSampleInWorkspace,
} from "./landing-geometry-data";
import { SpatialSceneCanvas } from "./LandingHeroScene3D";

export interface LandingInteractiveDemoProps {
  readonly presentation?: "default" | "v14";
}

export function LandingInteractiveDemo({
  presentation = "default",
}: LandingInteractiveDemoProps = {}) {
  const isV14 = presentation === "v14";
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
      className={isV14 ? "axo-sp-demo-section is-v14" : "axo-sp-demo-section"}
      aria-labelledby="landing-demo-heading"
    >
      <div className="axo-sp-container">
        <div className="axo-sp-demo-header">
          <div className="axo-sp-section-head">
            {!isV14 && <p className="axo-sp-eyebrow">Trải nghiệm trực tiếp</p>}
            <h2 id="landing-demo-heading" className="axo-sp-section-title">
              {isV14 ? (
                <>
                  Xoay khối 3D và kiểm chứng{" "}
                  <AnnotatedPhrase variant="highlight">
                    thiết diện thật
                  </AnnotatedPhrase>
                  .
                </>
              ) : (
                "Xoay, cắt và kiểm chứng ngay trên mô hình 3D."
              )}
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

        <div
          id="landing-product-showcase"
          data-ui={isV14 ? "product-workbench" : undefined}
          className={isV14 ? "axo-sp-demo-workbench is-v14" : "axo-sp-demo-workbench"}
        >
          {/* Dominant Interactive 3D Viewport */}
          <div className="axo-sp-demo-canvas-wrap">
            <div className={isV14 ? "axo-sp-demo-toolbar is-v14" : "axo-sp-demo-toolbar"}>
              {!isV14 && <span className="axo-sp-demo-toolbar-title">{sample.title}</span>}
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
              cameraPos={
                isV14 && activeStage.v14CameraPos
                  ? activeStage.v14CameraPos
                  : activeStage.cameraPos
              }
              lookAt={
                isV14 && activeStage.v14LookAt
                  ? activeStage.v14LookAt
                  : activeStage.lookAt
              }
              interactiveOrbit={true}
              orbitResetNonce={orbitResetNonce}
              onUserOrbit={() => setHasCameraMoved(true)}
              presentation={presentation}
              bottomHint={
                isV14 || hasCameraMoved
                  ? undefined
                  : "Kéo để xoay 3D · Phím mũi tên để đổi góc"
              }
              ariaLabel={`Mô hình 3D tương tác: ${sample.title}`}
            />
          </div>

          {/* Focused Step Control Column */}
          <aside className="axo-sp-demo-panel" aria-label="Điều khiển bước dựng">
            <div className="axo-sp-demo-step-head">
              <span
                className={
                  isV14 ? "axo-v14-demo-step-tag" : "axo-sp-demo-step-eyebrow"
                }
              >
                {isV14
                  ? activeStage.v14StepLabel ?? `Bước ${stepIndex + 1}`
                  : `Bước ${activeStage.stepNumber} · ${activeStage.tag}`}
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
                  {isV14 ? String(idx + 1) : st.stepNumber}
                </button>
              ))}
            </div>

            <div className="axo-sp-demo-step-detail">
              <h3 className="axo-sp-demo-step-title">
                {isV14 ? activeStage.v14Title ?? activeStage.title : activeStage.title}
              </h3>
              <p className="axo-sp-demo-step-desc">
                {isV14 ? activeStage.v14Guide ?? activeStage.summary : activeStage.summary}
              </p>
            </div>

            {isV14 ? (
              activeStage.v14Focus ? (
                <div className="axo-v14-demo-focus-note">
                  <p className="axo-v14-demo-focus-text">{activeStage.v14Focus}</p>
                </div>
              ) : null
            ) : isFinalVerifiedStage ? (
              <div
                className="axo-sp-demo-metrics"
                aria-label="Kết quả kiểm chứng chính xác"
              >
                {sample.verifiedMetrics.map((metric) => (
                  <div key={`${sample.id}-${metric.label}`} className="axo-sp-demo-metric-chip">
                    <span className="axo-sp-demo-metric-label">{metric.label}</span>
                    <span className="axo-sp-demo-metric-val">{metric.value}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div
                className="axo-sp-demo-metrics"
                aria-label={`Dữ kiện bước ${activeStage.stepNumber}`}
              >
                <div className="axo-sp-demo-metric-chip is-stage-note">
                  <span className="axo-sp-demo-metric-label">{activeStage.tag}</span>
                  <span className="axo-sp-demo-metric-val">{activeStage.mathFact}</span>
                </div>
              </div>
            )}

            {!isV14 && (
              <details className="axo-sp-demo-problem-disclosure">
                <summary>Xem đề bài gốc</summary>
                <p>{sample.problemText}</p>
              </details>
            )}

            <div className="axo-sp-demo-footer-action">
              <button
                id="btn-landing-open-showcase-3d"
                type="button"
                className={
                  isV14
                    ? "axo-v14-btn axo-v14-btn-primary axo-sp-btn-full"
                    : "axo-sp-btn-primary axo-sp-btn-full"
                }
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
