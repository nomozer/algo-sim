import { IconAxoLogo } from "./icons";
import { useAuthStore } from "../state/auth";
import { useAppStore } from "../state/store";
import { LandingHeader } from "./landing/LandingHeader";
import { SpatialSceneCanvas } from "./landing/LandingHeroScene3D";
import { LandingInteractiveDemo } from "./landing/LandingInteractiveDemo";
import { LandingStorytelling } from "./landing/LandingStorytelling";
import {
  enterAxoWorkspace,
  LANDING_PYRAMID_SAMPLE,
  openLibraryFromLanding,
} from "./landing/landing-geometry-data";

function scrollToStorytelling() {
  if (typeof document === "undefined" || typeof window === "undefined") return;
  const el = document.getElementById("cach-hoat-dong");
  if (!el) return;
  const reduced =
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const top = Math.max(0, el.getBoundingClientRect().top + window.scrollY - 68);
  window.scrollTo({ top, behavior: reduced ? "auto" : "smooth" });
}

export function LandingView() {
  const user = useAuthStore((s) => s.user);
  const setView = useAppStore((s) => s.setView);
  const heroFinalStage = LANDING_PYRAMID_SAMPLE.milestones[3];

  return (
    <div id="view-landing" className="axo-sp-root">
      <LandingHeader />

      {/* 1. HERO SECTION */}
      <section
        id="gioi-thieu"
        className="axo-sp-hero"
        aria-labelledby="landing-hero-title"
      >
        <div className="axo-sp-container">
          <div id="landing-hero" className="axo-sp-hero-grid">
            <div className="axo-sp-hero-copy">
              <span className="axo-sp-eyebrow">
                <span className="axo-sp-eyebrow-dot" aria-hidden="true" />
                <span>Không gian 3D &amp; từng bước dựng hình</span>
              </span>

              <h1 id="landing-hero-title" className="axo-sp-hero-title">
                Hình học không gian, dễ hình dung hơn.
              </h1>

              <p className="axo-sp-hero-sub">
                Từ đề bài đến mô hình 3D tương tác. Quan sát từng bước dựng hình và khám phá các
                quan hệ trong không gian.
              </p>

              <div className="axo-sp-hero-ctas">
                <button
                  type="button"
                  id="btn-landing-hero-start"
                  className="axo-sp-btn-primary"
                  onClick={enterAxoWorkspace}
                >
                  <span>Bắt đầu dựng hình</span>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                    <path
                      d="M3.5 8h9m0 0L9 4.5M12.5 8 9 11.5"
                      stroke="currentColor"
                      strokeWidth="1.65"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </button>

                <button
                  type="button"
                  id="btn-landing-hero-how"
                  className="axo-sp-btn-secondary"
                  onClick={scrollToStorytelling}
                >
                  <span>Khám phá cách hoạt động</span>
                </button>
              </div>

              <div style={{ marginTop: 14 }}>
                <button
                  type="button"
                  id="btn-landing-hero-library"
                  className="axo-sp-btn-ghost-link"
                  onClick={openLibraryFromLanding}
                >
                  <span>Khám phá thư viện bài mẫu</span>
                  <span aria-hidden="true">→</span>
                </button>
              </div>

              <div className="axo-sp-hero-meta" aria-label="Đặc trưng trực quan">
                <span className="axo-sp-hero-metric">
                  <span className="axo-sp-hero-metric-pip is-blue" aria-hidden="true" />
                  <span>Nét liền / nét đứt đúng khuất 3D</span>
                </span>
                <span className="axo-sp-hero-metric">
                  <span className="axo-sp-hero-metric-pip is-amber" aria-hidden="true" />
                  <span>Thiết diện &amp; giao tuyến chính xác</span>
                </span>
              </div>
            </div>

            <div className="axo-sp-hero-stage-col">
              <SpatialSceneCanvas
                sceneId="landing-hero-scene"
                sample={LANDING_PYRAMID_SAMPLE}
                visiblePoints={heroFinalStage.visiblePoints}
                activePoints={["M", "N", "P", "E", "F"]}
                showGuideEdges={false}
                planeOpacity={0.62}
                sectionProgress={1}
                sectionFillOpacity={0.86}
                cameraPos={LANDING_PYRAMID_SAMPLE.defaultCamera}
                lookAt={LANDING_PYRAMID_SAMPLE.defaultLookAt}
                subtlePointerParallax
                interactiveOrbit
                topBadgeLeft="S.ABCD · SA ⊥ (ABCD)"
                topBadgeRight="(MNP): x + y + 2z = 6"
                bottomCaption="Thiết diện ngũ giác MENPF"
                bottomHint="Di chuột hoặc kéo nhẹ để đổi góc nhìn"
                ariaLabel="Mô hình 3D hình chóp S.ABCD bị cắt bởi mặt phẳng (MNP) tạo thiết diện ngũ giác MENPF"
              />
            </div>
          </div>
        </div>
      </section>

      {/* 2. SCROLL STORYTELLING SECTION */}
      <LandingStorytelling />

      {/* 3. INTERACTIVE DEMO SECTION */}
      <LandingInteractiveDemo />

      {/* 4. CLOSING CTA BLOCK */}
      <section
        id="landing-final-cta"
        className="axo-sp-cta-section"
        aria-labelledby="landing-cta-heading"
      >
        <div className="axo-sp-container">
          <div className="axo-sp-cta-card">
            <div>
              <h2 id="landing-cta-heading" className="axo-sp-cta-title">
                Sẵn sàng khám phá hình học theo một cách khác?
              </h2>
              <p className="axo-sp-cta-sub">
                Vào thẳng màn hình dựng hình để thử đề bài của bạn, hoặc xem các mô hình thiết diện
                và quan hệ không gian có sẵn trong thư viện.
              </p>
              <div className="axo-sp-cta-actions">
                <button
                  type="button"
                  id="btn-landing-final-start"
                  className="axo-sp-btn-primary"
                  onClick={enterAxoWorkspace}
                >
                  <span>Bắt đầu dựng hình</span>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                    <path
                      d="M3.5 8h9m0 0L9 4.5M12.5 8 9 11.5"
                      stroke="currentColor"
                      strokeWidth="1.65"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </button>
                <button
                  type="button"
                  id="btn-landing-final-library"
                  className="axo-sp-btn-secondary"
                  onClick={openLibraryFromLanding}
                >
                  <span>Mở thư viện bài mẫu</span>
                </button>
              </div>
            </div>

            <div className="axo-sp-cta-visual" aria-hidden="true">
              <svg width="240" height="168" viewBox="0 0 240 168" fill="none">
                <polygon
                  points="44,126 116,144 198,112 126,96"
                  fill="#0075de"
                  fillOpacity="0.08"
                  stroke="#1b1b19"
                  strokeOpacity="0.32"
                  strokeWidth="1.4"
                  strokeDasharray="4 4"
                />
                <polygon
                  points="76,72 162,62 178,108 94,118"
                  fill="#0075de"
                  fillOpacity="0.14"
                  stroke="#0075de"
                  strokeOpacity="0.55"
                  strokeWidth="1.4"
                />
                <line x1="94" y1="24" x2="44" y2="126" stroke="#1b1b19" strokeWidth="1.7" />
                <line x1="94" y1="24" x2="116" y2="144" stroke="#1b1b19" strokeWidth="1.7" />
                <line x1="94" y1="24" x2="198" y2="112" stroke="#1b1b19" strokeWidth="1.7" />
                <line
                  x1="94"
                  y1="24"
                  x2="126"
                  y2="96"
                  stroke="#6b7280"
                  strokeWidth="1.4"
                  strokeDasharray="4 4"
                />
                <polygon
                  points="69,75 105,84 157,128 162,102 110,60"
                  fill="#d96b18"
                  fillOpacity="0.26"
                  stroke="#c2550a"
                  strokeWidth="2.2"
                />
                <circle cx="94" cy="24" r="3.5" fill="#1b1b19" />
                <circle cx="69" cy="75" r="4" fill="#0075de" />
                <circle cx="157" cy="128" r="4" fill="#0075de" />
                <circle cx="105" cy="84" r="4.2" fill="#c2550a" />
                <circle cx="162" cy="102" r="4.2" fill="#c2550a" />
              </svg>
            </div>
          </div>
        </div>
      </section>

      {/* 5. MINIMAL REAL FOOTER */}
      <footer id="landing-footer" className="axo-sp-footer">
        <div className="axo-sp-container axo-sp-footer-inner">
          <div className="axo-sp-footer-brand">
            <IconAxoLogo size={20} />
            <span>Axo · Trực quan hóa hình học không gian</span>
          </div>

          <div className="axo-sp-footer-links">
            <button
              type="button"
              id="btn-landing-footer-start"
              className="axo-sp-footer-link"
              onClick={enterAxoWorkspace}
            >
              Bắt đầu dựng hình
            </button>
            <button
              type="button"
              id="btn-landing-footer-library"
              className="axo-sp-footer-link"
              onClick={openLibraryFromLanding}
            >
              Thư viện bài mẫu
            </button>
            <button
              type="button"
              id="btn-landing-footer-login"
              className="axo-sp-footer-link"
              onClick={() => {
                if (user) {
                  enterAxoWorkspace();
                } else {
                  setView("login");
                }
              }}
            >
              {user ? "Vào ứng dụng" : "Đăng nhập"}
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}
