import {
  useCallback,
  useEffect,
  useRef,
  type MouseEvent as ReactMouseEvent,
  type PointerEvent as ReactPointerEvent,
} from "react";
import { useAuthStore } from "../../state/auth";
import { AnnotatedPhrase } from "./AnnotatedHeading";
import { enterAxoWorkspace } from "./landing-geometry-data";

export interface HeroSculptureAssetSpec {
  readonly id: "sat-left" | "centerpiece" | "sat-right";
  readonly src: string;
  readonly alt: string;
}

export const AXO_V14_HERO_CONCEPT_ASSETS: readonly HeroSculptureAssetSpec[] = [
  {
    id: "sat-left",
    src: "/assets/landing/hero-concept/axo-hero-sat-left.png",
    alt: "",
  },
  {
    id: "centerpiece",
    src: "/assets/landing/hero-concept/axo-hero-centerpiece.png",
    alt: "Khối đa diện kiến trúc bằng sứ trắng và chàm sâu cắt qua mặt phẳng kính xanh sapphire tạo thiết diện hổ phách",
  },
  {
    id: "sat-right",
    src: "/assets/landing/hero-concept/axo-hero-sat-right.png",
    alt: "",
  },
];

export function LandingHeroV14() {
  const user = useAuthStore((s) => s.user);
  const stageRef = useRef<HTMLDivElement | null>(null);
  const pointerStateRef = useRef({
    targetX: 0,
    targetY: 0,
    currentX: 0,
    currentY: 0,
    rafId: 0,
    reducedMotion: false,
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    const mql = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    const syncMotion = () => {
      const reduced = Boolean(mql?.matches);
      pointerStateRef.current.reducedMotion = reduced;
      if (reduced && stageRef.current) {
        stageRef.current.style.setProperty("--axo-hx", "0");
        stageRef.current.style.setProperty("--axo-hy", "0");
      }
    };
    syncMotion();
    mql?.addEventListener?.("change", syncMotion);
    return () => {
      mql?.removeEventListener?.("change", syncMotion);
      if (pointerStateRef.current.rafId) {
        window.cancelAnimationFrame(pointerStateRef.current.rafId);
        pointerStateRef.current.rafId = 0;
      }
    };
  }, []);

  const scheduleParallaxFrame = useCallback(() => {
    const state = pointerStateRef.current;
    if (state.rafId || typeof window === "undefined") return;

    const tick = () => {
      const stageEl = stageRef.current;
      if (!stageEl || state.reducedMotion) {
        state.rafId = 0;
        return;
      }

      state.currentX += (state.targetX - state.currentX) * 0.14;
      state.currentY += (state.targetY - state.currentY) * 0.14;

      stageEl.style.setProperty("--axo-hx", state.currentX.toFixed(4));
      stageEl.style.setProperty("--axo-hy", state.currentY.toFixed(4));

      const settled =
        Math.abs(state.targetX - state.currentX) < 0.002 &&
        Math.abs(state.targetY - state.currentY) < 0.002;
      if (settled) {
        state.currentX = state.targetX;
        state.currentY = state.targetY;
        stageEl.style.setProperty("--axo-hx", state.targetX.toFixed(4));
        stageEl.style.setProperty("--axo-hy", state.targetY.toFixed(4));
        state.rafId = 0;
        return;
      }

      state.rafId = window.requestAnimationFrame(tick);
    };

    state.rafId = window.requestAnimationFrame(tick);
  }, []);

  const handleStagePointerMove = useCallback(
    (e: ReactPointerEvent<HTMLDivElement>) => {
      if (e.pointerType !== "mouse" || pointerStateRef.current.reducedMotion) return;
      const el = stageRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) return;
      const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const ny = ((e.clientY - rect.top) / rect.height) * 2 - 1;
      pointerStateRef.current.targetX = Math.max(-1, Math.min(1, nx));
      pointerStateRef.current.targetY = Math.max(-1, Math.min(1, ny));
      scheduleParallaxFrame();
    },
    [scheduleParallaxFrame],
  );

  const handleStagePointerLeave = useCallback(() => {
    if (pointerStateRef.current.reducedMotion) return;
    pointerStateRef.current.targetX = 0;
    pointerStateRef.current.targetY = 0;
    scheduleParallaxFrame();
  }, [scheduleParallaxFrame]);

  const handleStoryScroll = useCallback((e: ReactMouseEvent<HTMLAnchorElement>) => {
    const target = document.getElementById("cach-hoat-dong");
    if (!target) return;
    e.preventDefault();
    const reduced =
      typeof window !== "undefined" &&
      Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches);
    target.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
  }, []);

  const leftAsset = AXO_V14_HERO_CONCEPT_ASSETS[0];
  const centerAsset = AXO_V14_HERO_CONCEPT_ASSETS[1];
  const rightAsset = AXO_V14_HERO_CONCEPT_ASSETS[2];

  return (
    <section
      id="landing-hero"
      className="axo-v14-hero axo-v14-hero-horizon"
      aria-labelledby="axo-v14-hero-heading"
    >
      <div className="axo-v14-hero-horizon-shell">
        <h1 id="axo-v14-hero-heading" className="axo-v14-hero-title axo-v14-hero-horizon-title">
          <span className="axo-v14-hero-title-line">Hình học không gian,{" "}</span>
          <span className="axo-v14-hero-title-line">
            dễ{" "}
            <span className="axo-v14-hero-phrase-keep">
              <AnnotatedPhrase variant="circle">hình dung</AnnotatedPhrase> hơn.
            </span>
          </span>
        </h1>

        <div className="axo-v14-hero-horizon-body">
          <p className="axo-v14-hero-lead axo-v14-hero-horizon-lead">
            Nhập đề bài tiếng Việt để quan sát khối đa diện 3D chính xác, mặt
            phẳng cắt và từng đường giao tuyến ngay trong không gian trực quan.
          </p>
          <div className="axo-v14-hero-actions axo-v14-hero-horizon-actions">
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
          ref={stageRef}
          className="axo-v14-hero-horizon-stage"
          data-design-stage="first-principles-concept"
          aria-label="Quần thể điêu khắc không gian và mặt phẳng cắt của Axo"
          onPointerMove={handleStagePointerMove}
          onPointerLeave={handleStagePointerLeave}
        >
          <svg
            className="axo-v14-horizon-drafting"
            viewBox="0 0 1120 420"
            preserveAspectRatio="xMidYMid meet"
            aria-hidden="true"
          >
            <ellipse
              className="axo-v14-horizon-orbit-ring"
              cx="560"
              cy="228"
              rx="430"
              ry="148"
              transform="rotate(-9 560 228)"
            />
            <ellipse
              className="axo-v14-horizon-orbit-inner"
              cx="560"
              cy="226"
              rx="312"
              ry="96"
              transform="rotate(-9 560 226)"
            />
            <line className="axo-v14-horizon-datum" x1="160" y1="364" x2="960" y2="364" />
            <path
              className="axo-v14-horizon-tick"
              d="M150 96 L150 110 M143 103 L157 103 M970 302 L970 316 M963 309 L977 309"
            />
          </svg>

          <div className="axo-v14-horizon-shadow axo-v14-horizon-shadow-left" aria-hidden="true" />
          <div className="axo-v14-horizon-shadow axo-v14-horizon-shadow-main" aria-hidden="true" />
          <div className="axo-v14-horizon-shadow axo-v14-horizon-shadow-right" aria-hidden="true" />

          <figure className="axo-v14-sculpt-layer axo-v14-sculpt-sat-left" aria-hidden="true">
            <img
              src={leftAsset.src}
              alt={leftAsset.alt}
              className="axo-v14-sculpt-img"
              draggable={false}
              decoding="async"
            />
          </figure>

          <figure className="axo-v14-sculpt-layer axo-v14-sculpt-center">
            <img
              src={centerAsset.src}
              alt={centerAsset.alt}
              className="axo-v14-sculpt-img"
              draggable={false}
              decoding="async"
            />
          </figure>

          <figure className="axo-v14-sculpt-layer axo-v14-sculpt-sat-right" aria-hidden="true">
            <img
              src={rightAsset.src}
              alt={rightAsset.alt}
              className="axo-v14-sculpt-img"
              draggable={false}
              decoding="async"
            />
          </figure>
        </div>

        <div className="axo-v14-horizon-footer-cue">
          <span className="axo-v14-horizon-cross" aria-hidden="true">+</span>
          <span className="axo-v14-horizon-cross axo-v14-horizon-cross-mid" aria-hidden="true">+</span>
          <a
            href="#cach-hoat-dong"
            className="axo-v14-horizon-scroll-link"
            onClick={handleStoryScroll}
          >
            Kéo xuống để xem cách dựng
          </a>
          <span className="axo-v14-horizon-cross axo-v14-horizon-cross-mid" aria-hidden="true">+</span>
          <span className="axo-v14-horizon-cross" aria-hidden="true">+</span>
        </div>
      </div>
    </section>
  );
}
