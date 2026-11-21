import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from "react";
import { IconAxoLogo } from "../icons";
import { useAuthStore } from "../../state/auth";
import {
  enterAxoWorkspace,
  openLibraryFromLanding,
} from "./landing-geometry-data";
import { useLandingReveal } from "./useLandingReveal";

export function scrollToLandingSection(id: string) {
  if (typeof document === "undefined") return;
  const reduced =
    typeof window !== "undefined" &&
    Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches);
  const behavior: ScrollBehavior = reduced ? "auto" : "smooth";
  if (
    id === "landing-hero" &&
    typeof window !== "undefined" &&
    (window.scrollY || window.pageYOffset || 0) > 0 &&
    typeof window.scrollTo === "function"
  ) {
    window.scrollTo({ top: 0, behavior });
    return;
  }
  document
    .getElementById(id)
    ?.scrollIntoView({ behavior, block: "start" });
}

export function LandingFooter() {
  const user = useAuthStore((s) => s.user);
  const primaryLabel = user ? "Vào ứng dụng" : "Bắt đầu dựng hình";
  const { ref: revealRef, revealState } = useLandingReveal<HTMLDivElement>();
  const sceneStageRef = useRef<HTMLDivElement | null>(null);
  const sceneMediaRef = useRef<HTMLDivElement | null>(null);
  const rafRef = useRef<number | null>(null);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const mql = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    const sync = () => setReducedMotion(Boolean(mql?.matches));
    sync();
    mql?.addEventListener?.("change", sync);
    return () => mql?.removeEventListener?.("change", sync);
  }, []);

  const resetParallax = useCallback(() => {
    if (rafRef.current !== null && typeof cancelAnimationFrame === "function") {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    sceneStageRef.current?.removeAttribute("data-pointer-active");
    if (sceneMediaRef.current) sceneMediaRef.current.style.transform = "";
  }, []);

  useEffect(() => {
    if (reducedMotion) resetParallax();
  }, [reducedMotion, resetParallax]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.addEventListener("blur", resetParallax);
    return () => {
      window.removeEventListener("blur", resetParallax);
      if (rafRef.current !== null && typeof cancelAnimationFrame === "function") {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
    };
  }, [resetParallax]);

  const handlePointerMove = useCallback(
    (e: ReactPointerEvent<HTMLDivElement>) => {
      if (reducedMotion || e.pointerType === "touch") return;
      const rect = e.currentTarget.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) return;
      sceneStageRef.current?.setAttribute("data-pointer-active", "true");
      const nx = Math.max(-1, Math.min(1, ((e.clientX - rect.left) / rect.width) * 2 - 1));
      const ny = Math.max(-1, Math.min(1, ((e.clientY - rect.top) / rect.height) * 2 - 1));
      if (rafRef.current !== null && typeof cancelAnimationFrame === "function") {
        cancelAnimationFrame(rafRef.current);
      }
      rafRef.current = requestAnimationFrame(() => {
        rafRef.current = null;
        if (sceneMediaRef.current) {
          sceneMediaRef.current.style.transform = `translate3d(${(nx * 4.5).toFixed(2)}px, ${(ny * 3.5).toFixed(2)}px, 0)`;
        }
      });
    },
    [reducedMotion],
  );

  const scrollTo = useCallback((id: string) => {
    scrollToLandingSection(id);
  }, []);

  return (
    <footer id="landing-footer" className="axo-v14-footer">
      <div className="axo-v14-footer-shell">
        <div
          ref={revealRef}
          id="landing-final-cta"
          className="axo-v14-closing-scene"
          data-reveal={revealState}
          role="region"
          aria-labelledby="landing-final-title"
          onPointerMove={handlePointerMove}
          onPointerLeave={resetParallax}
          onPointerCancel={resetParallax}
        >
          <div className="axo-v14-closing-copy">
            <h2 id="landing-final-title" className="axo-v14-closing-title">
              Sẵn sàng nhìn hình học theo cách khác?
            </h2>
            <p className="axo-v14-closing-lead">
              Nhập đề tiếng Việt hoặc mở nhanh bài mẫu ngay trong Workspace.
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
            </div>
          </div>

          <div ref={sceneStageRef} className="axo-v14-closing-visual" aria-hidden="true">
            <div ref={sceneMediaRef} className="axo-v14-closing-media">
              <img
                src="/assets/landing/studio-scenes/closing-scene.png"
                width={1008}
                height={680}
                alt=""
                loading="lazy"
                decoding="async"
                draggable={false}
                className="axo-v14-closing-img"
              />
            </div>
          </div>
        </div>

        <div className="axo-v14-footer-bar">
          <nav className="axo-v14-footer-links" aria-label="Liên kết chân trang">
            <a
              href="#about-axo"
              onClick={(e) => {
                e.preventDefault();
                scrollTo("about-axo");
              }}
            >
              Về Axo
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
              href="#bai-mau"
              onClick={(e) => {
                e.preventDefault();
                scrollTo("bai-mau");
              }}
            >
              Bài mẫu
            </a>
            <a
              id="btn-landing-footer-library"
              href="/library"
              className="axo-v14-footer-link-btn"
              onClick={(e) => {
                e.preventDefault();
                openLibraryFromLanding();
              }}
            >
              Thư viện
            </a>
          </nav>

          <div className="axo-v14-footer-center">
            <a
              id="btn-landing-footer-logo"
              href="#landing-hero"
              className="axo-sp-logo axo-v14-footer-logo"
              onClick={(e) => {
                e.preventDefault();
                scrollTo("landing-hero");
              }}
              aria-label="Axo, trở về đầu trang"
            >
              <span className="axo-sp-logo-mark" aria-hidden="true">
                <IconAxoLogo />
              </span>
            </a>
            <p className="axo-v14-footer-copy">
              © Axo · Hình học không gian 3D
            </p>
          </div>

          <div className="axo-v14-footer-top-wrap">
            <a
              id="btn-landing-footer-top"
              href="#landing-hero"
              className="axo-v14-footer-top-link"
              onClick={(e) => {
                e.preventDefault();
                scrollTo("landing-hero");
              }}
            >
              <span>Trở về đầu trang</span>
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
      </div>
    </footer>
  );
}
