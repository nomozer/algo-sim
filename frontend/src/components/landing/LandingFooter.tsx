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
          sceneMediaRef.current.style.transform = `translate3d(${(nx * 4).toFixed(2)}px, ${(ny * 3).toFixed(2)}px, 0)`;
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
          <div ref={sceneStageRef} className="axo-v14-closing-visual" aria-hidden="true">
            <div ref={sceneMediaRef} className="axo-v14-closing-media">
              {/* Orthographic axonometric cube (azimuth 32 deg, elevation 24 deg)
                  with midpoint regular hexagon plane x + y + z = 0 */}
              <svg
                className="axo-v14-closing-svg"
                viewBox="56 6 248 248"
                fill="none"
                focusable="false"
              >
                <path
                  className="axo-closing-hex-fill"
                  d="M113 40.8 L221.9 30.6 L288.9 119.8 L247 219.2 L138.1 229.4 L71.1 140.2 Z"
                />
                <path
                  className="axo-closing-cube-hidden"
                  d="M154.9 157.9 L71.1 212.4 M154.9 157.9 L288.9 191.9 M154.9 157.9 L154.9 13.6"
                  strokeLinecap="round"
                />
                <path
                  className="axo-closing-cube-edge"
                  d="M71.1 212.4 L205.1 246.4 L288.9 191.9 M71.1 68.1 L205.1 102.1 L288.9 47.6 L154.9 13.6 Z M71.1 212.4 L71.1 68.1 M205.1 246.4 L205.1 102.1 M288.9 191.9 L288.9 47.6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  className="axo-closing-hex-hidden"
                  d="M221.9 30.6 L288.9 119.8 M247 219.2 L138.1 229.4 M71.1 140.2 L113 40.8"
                  strokeLinecap="round"
                />
                <path
                  className="axo-closing-hex-visible"
                  d="M113 40.8 L221.9 30.6 M288.9 119.8 L247 219.2 M138.1 229.4 L71.1 140.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  className="axo-closing-vertex-mark"
                  d="M113 37.3 L116.5 40.8 L113 44.3 L109.5 40.8 Z M221.9 27.1 L225.4 30.6 L221.9 34.1 L218.4 30.6 Z M288.9 116.3 L292.4 119.8 L288.9 123.3 L285.4 119.8 Z M247 215.7 L250.5 219.2 L247 222.7 L243.5 219.2 Z M138.1 225.9 L141.6 229.4 L138.1 232.9 L134.6 229.4 Z M71.1 136.7 L74.6 140.2 L71.1 143.7 L67.6 140.2 Z"
                />
              </svg>
            </div>
          </div>

          <div className="axo-v14-closing-copy">
            <h2 id="landing-final-title" className="axo-v14-closing-title">
              Sẵn sàng nhìn hình học theo cách khác?
            </h2>
            <p className="axo-v14-closing-lead">
              Nhập đề tiếng Việt hoặc mở nhanh bài mẫu trong Workspace.
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
        </div>

        <div className="axo-v14-footer-bar">
          <div className="axo-v14-footer-brand">
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
              <span className="axo-sp-logo-name">Axo</span>
            </a>
            <p className="axo-v14-footer-copy">
              © Axo · Hình học không gian 3D
            </p>
          </div>

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
