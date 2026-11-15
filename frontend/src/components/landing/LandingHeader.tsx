import { useCallback, useEffect, useRef, useState } from "react";
import { IconAxoLogo } from "../icons";
import { useAuthStore } from "../../state/auth";
import { useAppStore } from "../../state/store";
import { enterAxoWorkspace } from "./landing-geometry-data";

export type LandingSectionId = "gioi-thieu" | "cach-hoat-dong" | "trai-nghiem";

interface NavItem {
  readonly id: LandingSectionId;
  readonly label: string;
}

const NAV_ITEMS: readonly NavItem[] = [
  { id: "gioi-thieu", label: "Giới thiệu" },
  { id: "cach-hoat-dong", label: "Cách hoạt động" },
  { id: "trai-nghiem", label: "Trải nghiệm" },
];

function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function LandingHeader() {
  const user = useAuthStore((s) => s.user);
  const setView = useAppStore((s) => s.setView);

  const [activeSection, setActiveSection] = useState<LandingSectionId>("gioi-thieu");
  const [hoveredSection, setHoveredSection] = useState<LandingSectionId | null>(null);
  const [focusedSection, setFocusedSection] = useState<LandingSectionId | null>(null);
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [pillStyle, setPillStyle] = useState<{ left: number; width: number; ready: boolean }>({
    left: 0,
    width: 0,
    ready: false,
  });

  const navRef = useRef<HTMLElement | null>(null);
  const linkRefs = useRef<Partial<Record<LandingSectionId, HTMLButtonElement | null>>>({});
  const clickLockUntilRef = useRef<number>(0);

  const targetPillId = hoveredSection ?? focusedSection ?? activeSection;

  const measurePill = useCallback((id: LandingSectionId) => {
    const btn = linkRefs.current[id];
    const navEl = navRef.current;
    if (!btn || !navEl) return;
    const width = btn.offsetWidth;
    if (width <= 0) return;
    setPillStyle({
      left: btn.offsetLeft,
      width,
      ready: true,
    });
  }, []);

  useEffect(() => {
    measurePill(targetPillId);
  }, [measurePill, targetPillId]);

  useEffect(() => {
    const navEl = navRef.current;
    if (!navEl || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(() => {
      measurePill(targetPillId);
    });
    ro.observe(navEl);
    for (const item of NAV_ITEMS) {
      const btn = linkRefs.current[item.id];
      if (btn) ro.observe(btn);
    }
    return () => ro.disconnect();
  }, [measurePill, targetPillId]);

  useEffect(() => {
    if (typeof window === "undefined" || typeof document === "undefined") return;

    let rafId = 0;
    const syncScrollAndActive = () => {
      rafId = 0;
      const y = window.scrollY || window.pageYOffset || 0;
      setIsScrolled(y > 16);

      if (Date.now() < clickLockUntilRef.current) return;

      const anchorLine = Math.min(280, window.innerHeight * 0.34);
      let current: LandingSectionId = "gioi-thieu";
      for (const item of NAV_ITEMS) {
        const el = document.getElementById(item.id);
        if (!el) continue;
        const rect = el.getBoundingClientRect();
        if (rect.top <= anchorLine) {
          current = item.id;
        }
      }
      setActiveSection(current);
    };

    const scheduleSync = () => {
      if (rafId !== 0) return;
      rafId = window.requestAnimationFrame(syncScrollAndActive);
    };

    syncScrollAndActive();
    window.addEventListener("scroll", scheduleSync, { passive: true });
    window.addEventListener("resize", scheduleSync, { passive: true });
    return () => {
      if (rafId !== 0) window.cancelAnimationFrame(rafId);
      window.removeEventListener("scroll", scheduleSync);
      window.removeEventListener("resize", scheduleSync);
    };
  }, []);

  useEffect(() => {
    if (!mobileMenuOpen || typeof window === "undefined") return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileMenuOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [mobileMenuOpen]);

  const scrollToSection = useCallback((id: LandingSectionId) => {
    setActiveSection(id);
    setHoveredSection(null);
    setMobileMenuOpen(false);
    clickLockUntilRef.current = Date.now() + 750;

    if (typeof document === "undefined" || typeof window === "undefined") return;
    const target = document.getElementById(id);
    if (target) {
      const headerOffset = 68;
      const top = Math.max(0, target.getBoundingClientRect().top + window.scrollY - headerOffset);
      window.scrollTo({
        top: id === "gioi-thieu" ? 0 : top,
        behavior: prefersReducedMotion() ? "auto" : "smooth",
      });
    }
  }, []);

  return (
    <>
      <header
        id="landing-header"
        className={`axo-sp-header${isScrolled ? " is-scrolled" : ""}`}
        data-scrolled={isScrolled ? "true" : "false"}
      >
        <div className="axo-sp-container axo-sp-header-inner">
          <button
            type="button"
            className="axo-sp-brand"
            onClick={() => scrollToSection("gioi-thieu")}
            aria-label="Axo — Về đầu trang"
          >
            <IconAxoLogo size={26} />
            <span className="axo-sp-brand-name">Axo</span>
          </button>

          <div className="axo-sp-nav-wrap">
            <nav
              id="landing-nav"
              ref={navRef}
              className="axo-sp-nav"
              aria-label="Điều hướng giới thiệu"
              onMouseLeave={() => setHoveredSection(null)}
              onBlur={(e) => {
                if (!e.currentTarget.contains(e.relatedTarget as Node | null)) {
                  setFocusedSection(null);
                }
              }}
            >
              <span
                className="axo-sp-nav-pill"
                aria-hidden="true"
                style={{
                  transform: `translate3d(${pillStyle.left}px, 0, 0)`,
                  width: `${pillStyle.width}px`,
                  opacity: pillStyle.ready ? 1 : 0,
                }}
              />
              {NAV_ITEMS.map((item) => {
                const isActive = activeSection === item.id;
                return (
                  <button
                    key={item.id}
                    ref={(el) => {
                      linkRefs.current[item.id] = el;
                    }}
                    type="button"
                    id={`landing-nav-${item.id}`}
                    className={`axo-sp-nav-link${isActive ? " is-active" : ""}`}
                    aria-current={isActive ? "page" : undefined}
                    onMouseEnter={() => setHoveredSection(item.id)}
                    onFocus={() => setFocusedSection(item.id)}
                    onClick={() => scrollToSection(item.id)}
                  >
                    {item.label}
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="axo-sp-header-actions">
            <button
              type="button"
              id="btn-landing-login"
              className="axo-sp-btn-login"
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

            <button
              type="button"
              id="btn-landing-mobile-menu"
              className="axo-sp-mobile-toggle"
              aria-label={mobileMenuOpen ? "Đóng menu" : "Mở menu điều hướng"}
              aria-expanded={mobileMenuOpen}
              aria-controls="landing-mobile-drawer"
              onClick={() => setMobileMenuOpen((prev) => !prev)}
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                {mobileMenuOpen ? (
                  <path
                    d="M4.5 4.5L13.5 13.5M13.5 4.5L4.5 13.5"
                    stroke="currentColor"
                    strokeWidth="1.75"
                    strokeLinecap="round"
                  />
                ) : (
                  <path
                    d="M3 5.25H15M3 9H15M3 12.75H15"
                    stroke="currentColor"
                    strokeWidth="1.75"
                    strokeLinecap="round"
                  />
                )}
              </svg>
            </button>
          </div>
        </div>
      </header>

      {mobileMenuOpen && (
        <div
          id="landing-mobile-drawer"
          className="axo-sp-mobile-drawer"
          role="dialog"
          aria-label="Menu điều hướng Axo"
        >
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`axo-sp-mobile-link${activeSection === item.id ? " is-active" : ""}`}
              onClick={() => scrollToSection(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </>
  );
}
