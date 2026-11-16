import { useEffect, useState } from "react";
import { IconAxoLogo } from "./icons";
import { LandingClosingSculpture } from "./landing/LandingClosingSculpture";
import { LandingHeader } from "./landing/LandingHeader";
import { LandingHeroSculpture3D } from "./landing/LandingHeroSculpture3D";
import { FinalCtaCornerAccent } from "./landing/LandingIllustrationAccents";
import { LandingInteractiveDemo } from "./landing/LandingInteractiveDemo";
import { LandingPreviewV14 } from "./landing/LandingPreviewV14";
import { LandingStorytelling } from "./landing/LandingStorytelling";
import { enterAxoWorkspace, openLibraryFromLanding } from "./landing/landing-geometry-data";
import { useAuthStore } from "../state/auth";

export type LandingPrototypeMode = "prod" | "v14";

const PROTO_CHANGE_EVENT = "axolanding:protochange";

export function readLandingPrototypeMode(search?: string): LandingPrototypeMode {
  const raw =
    search !== undefined
      ? search
      : typeof window !== "undefined"
        ? window.location.search
        : "";
  const params = new URLSearchParams(raw);
  const previewParam = params.get("preview")?.trim().toLowerCase();
  const protoParam = params.get("prototype")?.trim().toLowerCase();
  if (
    previewParam === "v1.4" ||
    previewParam === "v14" ||
    protoParam === "v1.4" ||
    protoParam === "v14"
  ) {
    return "v14";
  }
  return "prod";
}

export function switchLandingPrototype(mode: LandingPrototypeMode): void {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  url.searchParams.delete("prototype");
  if (mode === "prod") {
    url.searchParams.delete("preview");
  } else {
    url.searchParams.set("preview", "v1.4");
  }
  const nextUrl = `${url.pathname}${url.search}${url.hash}`;
  window.history.pushState(null, "", nextUrl);
  window.dispatchEvent(new CustomEvent(PROTO_CHANGE_EVENT));
  if (typeof window.scrollTo === "function") {
    window.scrollTo({ top: 0, behavior: "auto" });
  }
}

export function LandingView() {
  const user = useAuthStore((s) => s.user);
  const primaryStartLabel = user ? "Vào ứng dụng" : "Bắt đầu dựng hình";
  const [protoMode, setProtoMode] = useState<LandingPrototypeMode>(() =>
    readLandingPrototypeMode(),
  );

  useEffect(() => {
    if (typeof window === "undefined") return;
    const sync = () => setProtoMode(readLandingPrototypeMode(window.location.search));
    window.addEventListener("popstate", sync);
    window.addEventListener(PROTO_CHANGE_EVENT, sync);
    return () => {
      window.removeEventListener("popstate", sync);
      window.removeEventListener(PROTO_CHANGE_EVENT, sync);
    };
  }, []);

  if (protoMode === "v14") {
    return <LandingPreviewV14 />;
  }

  const scrollToSection = (id: string) => {
    if (typeof document === "undefined") return;
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div id="view-landing" className="axo-sp-root">
      <LandingHeader />

      <main id="landing-main" className="axo-sp-main">
        {/* Hero — Frameless Spatial Brand Sculpture + Focused 2-CTA Hierarchy */}
        <section id="landing-hero" className="axo-sp-hero" aria-labelledby="landing-hero-title">
          <div className="axo-sp-container axo-sp-hero-grid">
            <div className="axo-sp-hero-copy">
              <h1 id="landing-hero-title" className="axo-sp-hero-title">
                Hình học không gian, dễ hình dung hơn.
              </h1>

              <p className="axo-sp-hero-lead">
                Axo biến đề bài tiếng Việt thành mô hình 3D trực quan, giúp bạn quan sát từng mặt
                phẳng, giao tuyến và thiết diện theo từng bước dựng.
              </p>

              <div className="axo-sp-hero-actions">
                <button
                  id="btn-landing-hero-start"
                  type="button"
                  className="axo-sp-btn-primary axo-sp-btn-lg"
                  onClick={enterAxoWorkspace}
                >
                  {primaryStartLabel}
                </button>
                <button
                  id="btn-landing-hero-story"
                  type="button"
                  className="axo-sp-btn-secondary axo-sp-btn-lg"
                  onClick={() => scrollToSection("cach-hoat-dong")}
                >
                  Khám phá cách hoạt động
                </button>
              </div>
            </div>

            <div className="axo-sp-hero-visual">
              <LandingHeroSculpture3D />
            </div>
          </div>
        </section>

        {/* Scroll Storytelling — Continuous Mathematical Construction */}
        <LandingStorytelling />

        {/* Live Interactive 3D Demonstration */}
        <LandingInteractiveDemo />

        {/* Final CTA — Warm Tinted Closing Architecture + Multi-Solid Brand Sculpture */}
        <section id="landing-final-cta" className="axo-sp-final-cta" aria-labelledby="landing-final-title">
          <div className="axo-sp-container">
            <div className="axo-sp-final-cta-band">
              <FinalCtaCornerAccent />
              <div className="axo-sp-final-cta-copy">
                <p className="axo-sp-eyebrow">Sẵn sàng bắt đầu</p>
                <h2 id="landing-final-title" className="axo-sp-final-title">
                  Từ đề toán đến mô hình hình học không gian.
                </h2>
                <p className="axo-sp-final-desc">
                  Nhập đề bài tiếng Việt hoặc mở một bài toán mẫu để quan sát khối đa diện, mặt
                  phẳng cắt và từng bước lập luận trong không gian 3D.
                </p>
                <div className="axo-sp-final-actions">
                  <button
                    id="btn-landing-final-start"
                    type="button"
                    className="axo-sp-btn-primary axo-sp-btn-lg"
                    onClick={enterAxoWorkspace}
                  >
                    {primaryStartLabel}
                  </button>
                  <button
                    id="btn-landing-hero-library"
                    type="button"
                    className="axo-sp-btn-secondary axo-sp-btn-lg"
                    onClick={openLibraryFromLanding}
                  >
                    Khám phá thư viện bài mẫu
                  </button>
                </div>
              </div>

              <LandingClosingSculpture />
            </div>
          </div>
        </section>
      </main>

      <footer id="landing-footer" className="axo-sp-footer">
        <div className="axo-sp-container axo-sp-footer-inner">
          <div className="axo-sp-footer-brand">
            <span className="axo-sp-logo-mark" aria-hidden="true">
              <IconAxoLogo />
            </span>
            <div>
              <strong>Axo</strong>
              <p>Trực quan hóa và khám phá hình học không gian.</p>
            </div>
          </div>

          <nav className="axo-sp-footer-links" aria-label="Liên kết chân trang">
            <a href="#landing-hero" onClick={(e) => { e.preventDefault(); scrollToSection("landing-hero"); }}>
              Giới thiệu
            </a>
            <a href="#cach-hoat-dong" onClick={(e) => { e.preventDefault(); scrollToSection("cach-hoat-dong"); }}>
              Cách hoạt động
            </a>
            <a href="#trai-nghiem" onClick={(e) => { e.preventDefault(); scrollToSection("trai-nghiem"); }}>
              Trải nghiệm
            </a>
            <button id="btn-landing-footer-library" type="button" onClick={openLibraryFromLanding}>
              Thư viện bài mẫu
            </button>
          </nav>
        </div>
      </footer>
    </div>
  );
}
