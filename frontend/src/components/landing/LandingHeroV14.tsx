import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type MouseEvent as ReactMouseEvent,
  type PointerEvent as ReactPointerEvent,
} from "react";
import { useAuthStore } from "../../state/auth";
import { enterAxoWorkspace } from "./landing-geometry-data";

export function LandingHeroV14() {
  const user = useAuthStore((s) => s.user);
  const [reducedMotion, setReducedMotion] = useState(false);

  const stageRef = useRef<HTMLDivElement | null>(null);
  const dioramaLayerRef = useRef<HTMLDivElement | null>(null);
  const planeLayerRef = useRef<HTMLDivElement | null>(null);
  const orbitLayerRef = useRef<HTMLDivElement | null>(null);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const mql = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    const sync = () => setReducedMotion(Boolean(mql?.matches));
    sync();
    mql?.addEventListener?.("change", sync);
    return () => {
      mql?.removeEventListener?.("change", sync);
    };
  }, []);

  const applyParallax = useCallback((nx: number, ny: number) => {
    if (dioramaLayerRef.current) {
      dioramaLayerRef.current.style.transform = `translate3d(${(nx * 3.5).toFixed(2)}px, ${(ny * 2.5).toFixed(2)}px, 0)`;
    }
    if (planeLayerRef.current) {
      planeLayerRef.current.style.transform = `translate3d(${(nx * 6.5).toFixed(2)}px, ${(ny * 5).toFixed(2)}px, 0)`;
    }
    if (orbitLayerRef.current) {
      orbitLayerRef.current.style.transform = `translate3d(${(nx * -5.5).toFixed(2)}px, ${(ny * 4).toFixed(2)}px, 0)`;
    }
  }, []);

  const resetParallax = useCallback(() => {
    if (rafRef.current !== null && typeof cancelAnimationFrame === "function") {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    stageRef.current?.removeAttribute("data-pointer-active");
    for (const layer of [dioramaLayerRef.current, planeLayerRef.current, orbitLayerRef.current]) {
      if (layer) layer.style.transform = "";
    }
  }, []);

  useEffect(() => {
    if (reducedMotion) {
      resetParallax();
    }
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
      const stage = stageRef.current;
      if (!stage) return;
      const rect = stage.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) return;
      stage.setAttribute("data-pointer-active", "true");
      const nx = Math.max(-1, Math.min(1, ((e.clientX - rect.left) / rect.width) * 2 - 1));
      const ny = Math.max(-1, Math.min(1, ((e.clientY - rect.top) / rect.height) * 2 - 1));
      if (rafRef.current !== null && typeof cancelAnimationFrame === "function") {
        cancelAnimationFrame(rafRef.current);
      }
      rafRef.current = requestAnimationFrame(() => {
        rafRef.current = null;
        applyParallax(nx, ny);
      });
    },
    [applyParallax, reducedMotion],
  );

  const handlePointerLeave = useCallback(() => {
    resetParallax();
  }, [resetParallax]);

  const handleAboutScroll = useCallback(
    (e: ReactMouseEvent<HTMLAnchorElement>) => {
      const target = document.getElementById("about-axo");
      if (!target) return;
      e.preventDefault();
      const isReduced =
        reducedMotion ||
        (typeof window !== "undefined" &&
          Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches));
      target.scrollIntoView({ behavior: isReduced ? "auto" : "smooth", block: "start" });
    },
    [reducedMotion],
  );

  return (
    <section
      id="landing-hero"
      className="axo-v14-hero axo-v14-hero-atelier"
      aria-labelledby="axo-v14-hero-heading"
    >
      <div className="axo-v14-hero-atelier-grid">
        <h1 id="axo-v14-hero-heading" className="axo-v14-hero-atelier-title">
          <span className="axo-v14-hero-title-line">Hình học không gian,</span>
          <span className="axo-v14-hero-title-line">
            dễ{" "}
            <span className="axo-v14-hero-keyword">
              <span className="axo-v14-hero-keyword-text">hình dung</span>
              <svg
                className="axo-v14-hero-keyword-ring"
                viewBox="0 0 320 125"
                preserveAspectRatio="none"
                aria-hidden="true"
                focusable="false"
              >
                <path
                  className="axo-v14-hero-keyword-path"
                  d="M 214 15 C 154 6, 42 4, 9 29 C -7 44, -1 98, 88 111 C 164 121, 250 121, 297 108 C 320 96, 324 38, 286 19 C 254 4, 212 6, 174 11"
                  pathLength={1}
                />
              </svg>
            </span>{" "}
            hơn.
          </span>
        </h1>

        <div className="axo-v14-hero-atelier-body">
          <p className="axo-v14-hero-atelier-lead">
            Mô hình hóa bài toán tiếng Việt thành không gian 3D trực quan, giúp
            bạn dựng hình, xoay góc nhìn và quan sát từng mặt cắt rõ ràng.
          </p>
          <div className="axo-v14-hero-actions axo-v14-hero-atelier-actions">
            <button
              id="btn-landing-hero-start"
              type="button"
              className="axo-v14-btn axo-v14-btn-primary"
              onClick={enterAxoWorkspace}
            >
              {user ? "Vào ứng dụng" : "Bắt đầu dựng hình"}
            </button>
            <a
              id="btn-landing-hero-about"
              href="#about-axo"
              className="axo-v14-btn axo-v14-btn-secondary"
              onClick={handleAboutScroll}
            >
              Tìm hiểu về Axo
            </a>
          </div>
        </div>

        <div
          id="landing-hero-sculpture"
          ref={stageRef}
          className="axo-v14-hero-atelier-stage"
          data-hero-mode="atelier-studio-diorama"
          onPointerMove={handlePointerMove}
          onPointerLeave={handlePointerLeave}
          onPointerCancel={handlePointerLeave}
        >
          <div
            ref={orbitLayerRef}
            className="axo-v14-hero-atelier-layer axo-v14-hero-atelier-orbit"
            aria-hidden="true"
          >
            <img
              src="/assets/landing/hero-studio/hero-float-orbit.png"
              width={512}
              height={485}
              alt=""
              decoding="async"
              draggable={false}
              className="axo-v14-hero-atelier-img axo-v14-hero-atelier-img-float-b"
            />
          </div>

          <div
            ref={dioramaLayerRef}
            className="axo-v14-hero-atelier-layer axo-v14-hero-atelier-diorama"
            aria-hidden="true"
          >
            <img
              src="/assets/landing/hero-studio/hero-studio-diorama.png"
              width={963}
              height={824}
              alt=""
              decoding="async"
              draggable={false}
              className="axo-v14-hero-atelier-img axo-v14-hero-atelier-img-main"
            />
          </div>

          <div
            ref={planeLayerRef}
            className="axo-v14-hero-atelier-layer axo-v14-hero-atelier-plane"
            aria-hidden="true"
          >
            <img
              src="/assets/landing/hero-studio/hero-float-plane.png"
              width={446}
              height={512}
              alt=""
              decoding="async"
              draggable={false}
              className="axo-v14-hero-atelier-img axo-v14-hero-atelier-img-float-a"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
