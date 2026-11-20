import { Suspense, lazy, useCallback, type MouseEvent as ReactMouseEvent } from "react";
import { useAuthStore } from "../../state/auth";
import { AnnotatedPhrase } from "./AnnotatedHeading";
import { enterAxoWorkspace } from "./landing-geometry-data";
import { HeroPortalFallbackSvg } from "./portals/HeroPortalFallbackSvg";

const LazyHeroPortalStageV14 = lazy(() =>
  import("./portals/HeroPortalStageV14").then((m) => ({
    default: m.HeroPortalStageV14,
  })),
);

export function LandingHeroV14() {
  const user = useAuthStore((s) => s.user);

  const handleStoryScroll = useCallback((e: ReactMouseEvent<HTMLAnchorElement>) => {
    const target = document.getElementById("cach-hoat-dong");
    if (!target) return;
    e.preventDefault();
    const reduced =
      typeof window !== "undefined" &&
      Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches);
    target.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
  }, []);

  return (
    <section
      id="landing-hero"
      className="axo-v14-hero"
      aria-labelledby="axo-v14-hero-heading"
    >
      <div className="axo-v14-hero-shell">
        <div className="axo-v14-hero-copy">
          <h1 id="axo-v14-hero-heading" className="axo-v14-hero-title">
            <span className="axo-v14-hero-title-line">Hình học không gian,{" "}</span>
            <span className="axo-v14-hero-title-line">
              dễ{" "}
              <span className="axo-v14-hero-phrase-keep">
                <AnnotatedPhrase variant="circle">hình dung</AnnotatedPhrase> hơn.
              </span>
            </span>
          </h1>
          <p className="axo-v14-hero-lead">
            Nhập đề bài tiếng Việt để quan sát khối đa diện 3D chính xác, mặt
            phẳng cắt và từng đường giao tuyến ngay trong không gian trực quan.
          </p>
          <div className="axo-v14-hero-actions">
            <button
              id="btn-landing-hero-start"
              type="button"
              className="axo-v14-btn axo-v14-btn-primary"
              onClick={enterAxoWorkspace}
            >
              {user ? "Vào ứng dụng" : "Bắt đầu dựng hình"}
            </button>
            <a
              id="btn-landing-hero-story"
              href="#cach-hoat-dong"
              className="axo-v14-btn axo-v14-btn-secondary"
              onClick={handleStoryScroll}
            >
              Xem cách hoạt động
            </a>
          </div>
        </div>

        <div
          id="landing-hero-sculpture"
          className="axo-v14-hero-visual axo-v14-portal-stage"
          aria-label="Cụm Portal 3D khám phá hình học không gian Axo"
        >
          <Suspense fallback={<HeroPortalFallbackSvg />}>
            <LazyHeroPortalStageV14 />
          </Suspense>
        </div>
      </div>
    </section>
  );
}
