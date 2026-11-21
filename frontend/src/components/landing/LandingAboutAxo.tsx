import { enterAxoWorkspace } from "./landing-geometry-data";
import { useLandingReveal } from "./useLandingReveal";

export function LandingAboutAxo() {
  const { ref: sectionRef, revealState } = useLandingReveal<HTMLDivElement>();

  return (
    <section
      id="about-axo"
      className="axo-about"
      aria-labelledby="axo-about-heading"
    >
      <div
        ref={sectionRef}
        className="axo-about-grid"
        data-reveal={revealState}
      >
        <div className="axo-about-stage">
          <figure className="axo-about-product-frame">
            <div className="axo-about-prompt-strip" data-ui="true">
              <span className="axo-about-prompt-badge">Đề bài</span>
              <span className="axo-about-prompt-text">
                Cho hình lập phương ABCD.A&apos;B&apos;C&apos;D&apos;. Dựng thiết diện lục giác (MNP).
              </span>
            </div>
            <div className="axo-about-render-wrap">
              <img
                src="/assets/landing/product-renders/about-cube-section.png"
                width={920}
                height={642}
                alt="Mô hình 3D thật dựng trong Axo Workspace của hình lập phương ABCD.A'B'C'D' và thiết diện lục giác đều M-N-E-P-F-Q"
                loading="lazy"
                decoding="async"
                draggable={false}
                className="axo-about-render-img"
              />
            </div>
          </figure>
        </div>

        <div className="axo-about-copy">
          <h2 id="axo-about-heading" className="axo-about-title">
            Nhìn thấy bài toán trong không gian thật.
          </h2>
          <p className="axo-about-body">
            Axo là ứng dụng hội thoại giúp chuyển đề bài hình học không gian
            tiếng Việt thành mô hình 3D rõ ràng. Bạn dễ dàng quan sát cấu trúc
            khối, mặt phẳng cắt và các quan hệ không gian thay vì tự tưởng tượng
            trên hình vẽ phẳng.
          </p>
          <button
            id="btn-landing-about-workspace"
            type="button"
            className="axo-about-link"
            onClick={enterAxoWorkspace}
          >
            <span>Mở Workspace</span>
            <svg
              className="axo-about-link-icon"
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
        </div>
      </div>
    </section>
  );
}
