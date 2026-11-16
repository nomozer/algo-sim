import { useCallback } from "react";
import { IconAxoLogo } from "../icons";
import { useAuthStore } from "../../state/auth";
import { LandingClosingScene3D } from "./LandingClosingScene3D";
import {
  enterAxoWorkspace,
  openLibraryFromLanding,
} from "./landing-geometry-data";

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
            Đưa bài toán của bạn vào không gian 3D.
          </h2>
          <p className="axo-v14-closing-lead">
            Nhập đề bài tiếng Việt hoặc khám phá các mô hình có sẵn trong thư viện.
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

        <LandingClosingScene3D />
      </div>
    </section>
  );
}

export function scrollToLandingSection(id: string) {
  if (typeof document === "undefined") return;
  const reduced =
    typeof window !== "undefined" &&
    Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches);
  document
    .getElementById(id)
    ?.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
}

export function LandingFooterV14() {
  const scrollTo = useCallback((id: string) => {
    scrollToLandingSection(id);
  }, []);

  return (
    <footer id="landing-footer" className="axo-v14-footer">
      <div className="axo-v14-footer-shell">
        <div className="axo-v14-footer-top">
          <div className="axo-v14-footer-brand">
            <a
              id="btn-landing-footer-logo"
              href="#landing-hero"
              className="axo-sp-logo axo-v14-footer-logo"
              onClick={(e) => {
                e.preventDefault();
                scrollTo("landing-hero");
              }}
              aria-label="Axo — Về đầu trang"
            >
              <span className="axo-sp-logo-mark" aria-hidden="true">
                <IconAxoLogo />
              </span>
              <span className="axo-sp-logo-name">Axo</span>
            </a>
            <p className="axo-v14-footer-tagline">
              Không gian trực quan hóa và kiểm chứng hình học không gian 3D từ đề
              bài tiếng Việt.
            </p>
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

        <div className="axo-v14-footer-bottom">
          <p className="axo-v14-footer-copy">
            © Axo · Mô phỏng hình học không gian 3D
          </p>
          <a
            id="btn-landing-footer-top"
            href="#landing-hero"
            className="axo-v14-footer-top-link"
            onClick={(e) => {
              e.preventDefault();
              scrollTo("landing-hero");
            }}
          >
            <span>Về đầu trang</span>
            <svg
              className="axo-v14-footer-top-icon"
              viewBox="0 0 16 16"
              fill="none"
              aria-hidden="true"
              focusable="false"
            >
              <path
                d="M8 12.5V3.5M8 3.5L4.25 7.25M8 3.5L11.75 7.25"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </a>
        </div>
      </div>
    </footer>
  );
}
