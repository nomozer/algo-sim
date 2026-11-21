import { useState } from "react";
import {
  openLibraryFromLanding,
  openSampleInWorkspace,
} from "./landing-geometry-data";
import { useLandingReveal } from "./useLandingReveal";

interface CuratedSampleTopic {
  readonly sampleId: string;
  readonly title: string;
  readonly summary: string;
  readonly previewSrc: string;
  readonly previewLabel: string;
  readonly previewAlt: string;
}

const CURATED_TOPICS: readonly CuratedSampleTopic[] = [
  {
    sampleId: "chop-mat-cau-ngoai-tiep",
    title: "Khối đa diện & mặt cầu",
    summary: "Hình chóp ngoại tiếp mặt cầu, mặt cầu và hình nón cắt phẳng.",
    previewSrc: "/assets/landing/product-renders/sample-sphere-pyramid.png",
    previewLabel: "Mặt cầu ngoại tiếp hình chóp S.ABCD",
    previewAlt:
      "Mô hình 3D thật trong Axo: mặt cầu ngoại tiếp tâm I đi qua toàn bộ các đỉnh của hình chóp tứ giác S.ABCD",
  },
  {
    sampleId: "oxyz-giao-diem-duong-mat",
    title: "Quan hệ song song & vuông góc",
    summary:
      "Giao điểm đường thẳng, mặt phẳng và quan hệ vị trí trong không gian.",
    previewSrc: "/assets/landing/product-renders/sample-oxyz-intersection.png",
    previewLabel: "Giao điểm đường thẳng d và mặt phẳng (P) trong Oxyz",
    previewAlt:
      "Mô hình 3D thật trong Axo: giao điểm M của đường thẳng d với mặt phẳng (P) và hình chiếu H trong hệ tọa độ Oxyz",
  },
  {
    sampleId: "khoang-cach-diem-mat-phang-nghieng",
    title: "Khoảng cách & góc nhị diện",
    summary:
      "Khoảng cách từ điểm đến mặt phẳng, hai đường chéo nhau và góc giữa hai mặt.",
    previewSrc: "/assets/landing/product-renders/sample-distance-plane.png",
    previewLabel: "Khoảng cách từ điểm A đến mặt phẳng (SBC)",
    previewAlt:
      "Mô hình 3D thật trong Axo: hình chóp S.ABC với đường cao SA và hình chiếu vuông góc AH hạ xuống mặt phẳng (SBC)",
  },
  {
    sampleId: "chop-thiet-dien-ba-diem",
    title: "Thiết diện khối đa diện",
    summary: "Hình chóp, lập phương và lăng trụ cắt bởi mặt phẳng.",
    previewSrc: "/assets/landing/product-renders/sample-pyramid-section.png",
    previewLabel: "Thiết diện ngũ giác của hình chóp S.ABCD",
    previewAlt:
      "Mô hình 3D thật trong Axo: hình chóp S.ABCD bị mặt phẳng (MNP) cắt theo thiết diện ngũ giác M-E-N-P-F",
  },
];

export function LandingSamples() {
  const { ref, revealState } = useLandingReveal<HTMLDivElement>();
  const [activeSampleId, setActiveSampleId] = useState<string>(
    CURATED_TOPICS[0].sampleId,
  );
  const activeTopic =
    CURATED_TOPICS.find((t) => t.sampleId === activeSampleId) ??
    CURATED_TOPICS[0];

  return (
    <section
      id="bai-mau"
      className="axo-samples"
      aria-labelledby="axo-samples-heading"
    >
      <div ref={ref} className="axo-samples-grid" data-reveal={revealState}>
        <div className="axo-samples-copy">
          <h2 id="axo-samples-heading" className="axo-samples-title">
            Khám phá từ bộ bài mẫu sẵn có.
          </h2>
          <p className="axo-samples-lead">
            Mở ngay một chủ đề hình học đã kiểm chứng trong Workspace, hoặc duyệt
            toàn bộ danh sách trong thư viện.
          </p>

          <div className="axo-samples-list" role="list">
            {CURATED_TOPICS.map((topic) => {
              const isActive = topic.sampleId === activeTopic.sampleId;
              return (
                <button
                  key={topic.sampleId}
                  id={`btn-landing-sample-${topic.sampleId}`}
                  type="button"
                  role="listitem"
                  className={`axo-sample-row${isActive ? " is-active" : ""}`}
                  data-active={isActive ? "true" : "false"}
                  onMouseEnter={() => setActiveSampleId(topic.sampleId)}
                  onFocus={() => setActiveSampleId(topic.sampleId)}
                  onClick={() => openSampleInWorkspace(topic.sampleId)}
                >
                  <span className="axo-sample-row-content">
                    <span className="axo-sample-row-title">{topic.title}</span>
                    <span className="axo-sample-row-summary">
                      {topic.summary}
                    </span>
                  </span>
                  <svg
                    className="axo-sample-row-arrow"
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="none"
                    aria-hidden="true"
                    focusable="false"
                  >
                    <path
                      d="M3.5 8h9M8.75 4.25L12.5 8l-3.75 3.75"
                      stroke="currentColor"
                      strokeWidth="1.6"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </button>
              );
            })}
          </div>

          <div className="axo-samples-cta">
            <a
              id="btn-landing-samples-library"
              href="/library"
              className="axo-v14-btn axo-v14-btn-secondary"
              onClick={(e) => {
                e.preventDefault();
                openLibraryFromLanding();
              }}
            >
              <span>Xem thư viện bài mẫu</span>
              <svg
                className="axo-samples-cta-icon"
                width="15"
                height="15"
                viewBox="0 0 16 16"
                fill="none"
                aria-hidden="true"
                focusable="false"
              >
                <path
                  d="M3.5 8h9M8.75 4.25L12.5 8l-3.75 3.75"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </a>
          </div>
        </div>

        <div className="axo-samples-stage">
          <button
            id="btn-landing-sample-preview"
            type="button"
            className="axo-samples-preview-frame"
            data-active-sample={activeTopic.sampleId}
            aria-label={`Mở bài mẫu ${activeTopic.previewLabel} trong Workspace`}
            onClick={() => openSampleInWorkspace(activeTopic.sampleId)}
          >
            <span className="axo-samples-preview-canvas">
              {CURATED_TOPICS.map((topic) => {
                const isActive = topic.sampleId === activeTopic.sampleId;
                return (
                  <img
                    key={topic.sampleId}
                    src={topic.previewSrc}
                    width={920}
                    height={642}
                    alt={topic.previewAlt}
                    loading="lazy"
                    decoding="async"
                    draggable={false}
                    aria-hidden={!isActive}
                    className={`axo-samples-preview-img${isActive ? " is-active" : ""}`}
                  />
                );
              })}
            </span>
            <span className="axo-samples-preview-caption" data-ui="true">
              <span className="axo-samples-preview-label">
                {activeTopic.previewLabel}
              </span>
              <span className="axo-samples-preview-open" aria-hidden="true">
                Mở mô hình →
              </span>
            </span>
          </button>
        </div>
      </div>
    </section>
  );
}
