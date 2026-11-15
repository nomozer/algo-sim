import { useCallback } from "react";
import { IconAxoLogo } from "../icons";
import { useAuthStore } from "../../state/auth";
import {
  enterAxoWorkspace,
  openLibraryFromLanding,
} from "./landing-geometry-data";

function ClosingConstructionMotif() {
  return (
    <div className="axo-v14-closing-motif" aria-hidden="true">
      <svg className="axo-v14-closing-svg" viewBox="0 0 420 280" focusable="false">
        <ellipse
          className="axo-v14-svg-contact-halo"
          cx="235"
          cy="226"
          rx="126"
          ry="18"
        />

        {/* Wireframe-to-solid transition construction lines */}
        <line
          className="axo-v14-svg-projection-ray"
          x1="44"
          y1="196"
          x2="132"
          y2="196"
        />
        <line
          className="axo-v14-svg-projection-ray"
          x1="74"
          y1="82"
          x2="192"
          y2="52"
        />
        <polygon
          className="axo-v14-svg-wireframe-hint"
          points="56,196 112,172 86,84"
        />

        {/* Cohesive S.ABCD pyramid echoed from Hero */}
        <polygon
          className="axo-v14-svg-solid-base"
          points="132,208 292,226 350,174 190,162"
        />
        <polygon
          className="axo-v14-svg-solid-lower"
          points="132,208 292,226 350,174 286,118 232,108 168,142"
        />
        <polygon
          className="axo-v14-svg-solid-upper"
          points="192,46 168,142 232,108 286,118"
        />

        <line
          className="axo-v14-svg-edge-hidden"
          x1="190"
          y1="162"
          x2="132"
          y2="208"
        />
        <line
          className="axo-v14-svg-edge-hidden"
          x1="190"
          y1="162"
          x2="350"
          y2="174"
        />
        <line
          className="axo-v14-svg-edge-altitude"
          x1="192"
          y1="46"
          x2="190"
          y2="162"
        />

        <line
          className="axo-v14-svg-edge-solid"
          x1="192"
          y1="46"
          x2="132"
          y2="208"
        />
        <line
          className="axo-v14-svg-edge-solid"
          x1="192"
          y1="46"
          x2="292"
          y2="226"
        />
        <line
          className="axo-v14-svg-edge-solid"
          x1="192"
          y1="46"
          x2="350"
          y2="174"
        />
        <line
          className="axo-v14-svg-edge-solid"
          x1="132"
          y1="208"
          x2="292"
          y2="226"
        />
        <line
          className="axo-v14-svg-edge-solid"
          x1="292"
          y1="226"
          x2="350"
          y2="174"
        />

        <polygon
          className="axo-v14-svg-cutting-plane"
          points="108,154 316,184 366,112 162,92"
        />
        <polygon
          className="axo-v14-svg-section-poly"
          points="168,142 214,174 268,168 286,118 232,108"
        />

        {/* Vertex emphasis dots */}
        <circle className="axo-v14-svg-vertex-dot" cx="192" cy="46" r="3" />
        <circle className="axo-v14-svg-section-dot" cx="168" cy="142" r="3.4" />
        <circle className="axo-v14-svg-section-dot" cx="214" cy="174" r="3.4" />
        <circle className="axo-v14-svg-section-dot" cx="268" cy="168" r="3.4" />
        <circle className="axo-v14-svg-section-dot" cx="286" cy="118" r="3.4" />
        <circle className="axo-v14-svg-section-dot" cx="232" cy="108" r="3.4" />
      </svg>
    </div>
  );
}

export function LandingClosingV14() {
  const user = useAuthStore((s) => s.user);
  const primaryLabel = user ? "Vào ứng dụng" : "Bắt đầu dựng hình";

  return (
    <section
      id="landing-final-cta"
      className="axo-v14-closing"
      aria-labelledby="landing-final-title"
    >
      <div className="axo-v14-closing-shell">
        <div className="axo-v14-closing-copy">
          <h2 id="landing-final-title" className="axo-v14-closing-title">
            Đưa đề bài của bạn vào không gian 3D.
          </h2>
          <p className="axo-v14-closing-lead">
            Nhập trực tiếp đề bài tiếng Việt hoặc mở thư viện bài mẫu để quan
            sát khối đa diện, giao tuyến và thiết diện thật.
          </p>
          <div className="axo-v14-closing-actions">
            <button
              id="btn-landing-final-start"
              type="button"
              className="axo-v14-btn axo-v14-btn-primary"
              onClick={enterAxoWorkspace}
            >
              {primaryLabel}
            </button>
            <button
              id="btn-landing-hero-library"
              type="button"
              className="axo-v14-btn axo-v14-btn-secondary"
              onClick={openLibraryFromLanding}
            >
              Khám phá thư viện bài mẫu
            </button>
          </div>
        </div>

        <ClosingConstructionMotif />
      </div>
    </section>
  );
}

export function LandingFooterV14() {
  const scrollTo = useCallback((id: string) => {
    if (typeof document === "undefined") return;
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  return (
    <footer id="landing-footer" className="axo-v14-footer">
      <div className="axo-v14-footer-shell">
        <div className="axo-v14-footer-brand">
          <span className="axo-v14-footer-mark" aria-hidden="true">
            <IconAxoLogo />
          </span>
          <div>
            <strong>Axo</strong>
            <p>Trực quan hóa và khám phá hình học không gian.</p>
          </div>
        </div>

        <nav className="axo-v14-footer-links" aria-label="Liên kết chân trang">
          <a
            href="#landing-hero"
            onClick={(e) => {
              e.preventDefault();
              scrollTo("landing-hero");
            }}
          >
            Giới thiệu
          </a>
          <a
            href="#cach-hoat-dong"
            onClick={(e) => {
              e.preventDefault();
              scrollTo("cach-hoat-dong");
            }}
          >
            Cách hoạt động
          </a>
          <a
            href="#trai-nghiem"
            onClick={(e) => {
              e.preventDefault();
              scrollTo("trai-nghiem");
            }}
          >
            Trải nghiệm
          </a>
          <button
            id="btn-landing-footer-library"
            type="button"
            className="axo-v14-footer-link-btn"
            onClick={openLibraryFromLanding}
          >
            Thư viện bài mẫu
          </button>
        </nav>
      </div>
    </footer>
  );
}
