import { useCallback, useEffect, useRef, useState } from "react";
import { IconAxoLogo } from "../icons";
import { enterAxoWorkspace, openLibraryFromLanding } from "./landing-geometry-data";

export interface LandingSectionNavItem {
  readonly id: string;
  readonly label: string;
}

const LANDING_NAV_ITEMS: readonly LandingSectionNavItem[] = [
  { id: "landing-hero", label: "Giới thiệu" },
  { id: "cach-hoat-dong", label: "Cách hoạt động" },
  { id: "trai-nghiem", label: "Trải nghiệm" },
];

export function LandingHeader() {
  const [scrolled, setScrolled] = useState(false);
  const [activeId, setActiveId] = useState<string>("landing-hero");
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [pillRect, setPillRect] = useState<{ left: number; width: number; opacity: number }>({
    left: 0,
    width: 0,
    opacity: 0,
  });

  const navRef = useRef<HTMLElement | null>(null);
  const linkRefs = useRef<Record<string, HTMLAnchorElement | null>>({});
  const mobileBtnRef = useRef<HTMLButtonElement | null>(null);
  const firstDrawerActionRef = useRef<HTMLAnchorElement | null>(null);
  const prevMobileOpenRef = useRef(false);
  const clickLockUntilRef = useRef<number>(0);

  const displayId = hoveredId ?? activeId;

  const updatePillGeometry = useCallback((targetId: string) => {
    const navEl = navRef.current;
    const linkEl = linkRefs.current[targetId];
    if (!navEl || !linkEl) return;
    const navBox = navEl.getBoundingClientRect();
    const linkBox = linkEl.getBoundingClientRect();
    setPillRect({
      left: linkBox.left - navBox.left,
      width: linkBox.width,
      opacity: linkBox.width > 0 ? 1 : 0,
    });
  }, []);

  useEffect(() => {
    updatePillGeometry(displayId);
  }, [displayId, updatePillGeometry]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const onScroll = () => {
      const y = window.scrollY || window.pageYOffset || 0;
      setScrolled(y > 16);

      if (Date.now() < clickLockUntilRef.current) return;

      const probeY = y + 180;
      let nextActive = LANDING_NAV_ITEMS[0].id;
      for (const item of LANDING_NAV_ITEMS) {
        const el = document.getElementById(item.id);
        if (el) {
          const top = el.getBoundingClientRect().top + y;
          if (probeY >= top) {
            nextActive = item.id;
          }
        }
      }
      setActiveId(nextActive);
    };

    const onResize = () => {
      updatePillGeometry(displayId);
      if (window.innerWidth > 920) {
        setMobileOpen(false);
      }
    };

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onResize, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onResize);
    };
  }, [displayId, updatePillGeometry]);

  // Body scroll lock, Escape handling, and focus management for mobile drawer
  useEffect(() => {
    if (typeof document === "undefined") return;

    const prevOverflow = document.body.style.overflow;
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
      window.requestAnimationFrame(() => {
        firstDrawerActionRef.current?.focus();
      });
    } else if (prevMobileOpenRef.current) {
      mobileBtnRef.current?.focus();
    }
    prevMobileOpenRef.current = mobileOpen;

    if (!mobileOpen) {
      return () => {
        document.body.style.overflow = prevOverflow;
      };
    }

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setMobileOpen(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = prevOverflow;
    };
  }, [mobileOpen]);

  const scrollToSection = (sectionId: string) => {
    setActiveId(sectionId);
    setHoveredId(null);
    clickLockUntilRef.current = Date.now() + 900;
    setMobileOpen(false);
    if (typeof document === "undefined") return;
    const target = document.getElementById(sectionId);
    target?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <header
      id="landing-header"
      className={`axo-sp-header${scrolled ? " is-scrolled" : ""}${mobileOpen ? " is-menu-open" : ""}`}
    >
      <div className="axo-sp-header-inner">
        <a
          id="btn-landing-logo"
          href="#landing-hero"
          className="axo-sp-logo"
          aria-label="Axo — Về đầu trang giới thiệu"
          onClick={(e) => {
            e.preventDefault();
            scrollToSection("landing-hero");
          }}
        >
          <span className="axo-sp-logo-mark" aria-hidden="true">
            <IconAxoLogo />
          </span>
          <span className="axo-sp-logo-name">Axo</span>
        </a>

        <nav
          id="landing-nav"
          ref={navRef}
          className="axo-sp-nav"
          aria-label="Điều hướng trang giới thiệu"
          onMouseLeave={() => setHoveredId(null)}
        >
          <span
            className="axo-sp-nav-pill"
            aria-hidden="true"
            style={{
              width: `${pillRect.width}px`,
              transform: `translate3d(${pillRect.left}px, 0, 0)`,
              opacity: pillRect.opacity,
            }}
          />
          {LANDING_NAV_ITEMS.map((item) => {
            const isCurrent = displayId === item.id;
            return (
              <a
                key={item.id}
                ref={(el) => {
                  linkRefs.current[item.id] = el;
                }}
                id={`nav-landing-${item.id}`}
                href={`#${item.id}`}
                className={`axo-sp-nav-link${isCurrent ? " is-active" : ""}`}
                aria-current={activeId === item.id ? "location" : undefined}
                onMouseEnter={() => setHoveredId(item.id)}
                onFocus={() => setHoveredId(item.id)}
                onBlur={() => setHoveredId(null)}
                onClick={(e) => {
                  e.preventDefault();
                  scrollToSection(item.id);
                }}
              >
                {item.label}
              </a>
            );
          })}
        </nav>

        <div className="axo-sp-header-actions">
          <button
            id="btn-landing-header-library"
            type="button"
            className="axo-sp-btn-ghost"
            onClick={openLibraryFromLanding}
          >
            Thư viện
          </button>
          <button
            id="btn-landing-header-start"
            type="button"
            className="axo-sp-btn-primary"
            onClick={enterAxoWorkspace}
          >
            Bắt đầu
          </button>

          <button
            ref={mobileBtnRef}
            id="btn-landing-mobile-menu"
            type="button"
            className="axo-sp-mobile-toggle"
            aria-expanded={mobileOpen}
            aria-controls="landing-mobile-drawer"
            aria-label={mobileOpen ? "Đóng điều hướng" : "Mở điều hướng"}
            onClick={() => setMobileOpen((v) => !v)}
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round">
              {mobileOpen ? (
                <>
                  <path d="M5 5l10 10" />
                  <path d="M15 5L5 15" />
                </>
              ) : (
                <>
                  <path d="M3.5 6h13" />
                  <path d="M3.5 10h13" />
                  <path d="M3.5 14h13" />
                </>
              )}
            </svg>
          </button>
        </div>
      </div>

      {mobileOpen && (
        <>
          <div
            className="axo-sp-mobile-backdrop"
            aria-hidden="true"
            onClick={() => setMobileOpen(false)}
          />
          <div
            id="landing-mobile-drawer"
            className="axo-sp-mobile-drawer"
            role="dialog"
            aria-modal="true"
            aria-label="Điều hướng di động Axo"
          >
            <nav className="axo-sp-mobile-links" aria-label="Mục trang giới thiệu">
              {LANDING_NAV_ITEMS.map((item, idx) => (
                <a
                  key={item.id}
                  ref={idx === 0 ? firstDrawerActionRef : undefined}
                  href={`#${item.id}`}
                  className={`axo-sp-mobile-link${activeId === item.id ? " is-active" : ""}`}
                  onClick={(e) => {
                    e.preventDefault();
                    scrollToSection(item.id);
                  }}
                >
                  {item.label}
                </a>
              ))}
            </nav>
            <div className="axo-sp-mobile-cta-row">
              <button
                type="button"
                className="axo-sp-btn-secondary"
                onClick={() => {
                  setMobileOpen(false);
                  openLibraryFromLanding();
                }}
              >
                Khám phá thư viện
              </button>
              <button
                type="button"
                className="axo-sp-btn-primary"
                onClick={() => {
                  setMobileOpen(false);
                  enterAxoWorkspace();
                }}
              >
                Bắt đầu dựng hình
              </button>
            </div>
          </div>
        </>
      )}
    </header>
  );
}
