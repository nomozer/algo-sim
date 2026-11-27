import { useCallback, useEffect, useRef, useState } from "react";
import { IconAxoLogo } from "../icons";
import { useAuthStore } from "../../state/auth";
import {
  enterAxoWorkspace,
  openLibraryFromLanding,
  prefetchLibraryShell,
  prefetchWorkspaceShell,
} from "./landing-geometry-data";

export interface LandingSectionNavItem {
  readonly id: string;
  readonly label: string;
}

export const LANDING_NAV_ITEMS: readonly LandingSectionNavItem[] = [
  { id: "about-axo", label: "Về Axo" },
  { id: "cach-hoat-dong", label: "Cách hoạt động" },
  { id: "bai-mau", label: "Bài mẫu" },
];

export function LandingHeader() {
  const user = useAuthStore((s) => s.user);
  const [scrolled, setScrolled] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
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
  const drawerRef = useRef<HTMLDivElement | null>(null);
  const firstDrawerActionRef = useRef<HTMLAnchorElement | null>(null);
  const prevMobileOpenRef = useRef(false);
  const openedViaKeyboardRef = useRef(false);
  const restoreFocusOnCloseRef = useRef(false);
  const clickLockUntilRef = useRef<number>(0);

  const displayId = hoveredId ?? activeId;
  const displayIdRef = useRef<string | null>(displayId);
  displayIdRef.current = displayId;

  const updatePillGeometry = useCallback((targetId: string | null) => {
    if (!targetId) {
      setPillRect((prev) => (prev.opacity === 0 ? prev : { ...prev, opacity: 0 }));
      return;
    }
    const navEl = navRef.current;
    const linkEl = linkRefs.current[targetId];
    if (!navEl || !linkEl) return;
    if (linkEl.offsetWidth > 0) {
      setPillRect({
        left: linkEl.offsetLeft,
        width: linkEl.offsetWidth,
        opacity: 1,
      });
      return;
    }
    const navBox = navEl.getBoundingClientRect();
    const linkBox = linkEl.getBoundingClientRect();
    setPillRect({
      left: Math.max(0, linkBox.left - navBox.left - navEl.clientLeft),
      width: linkBox.width,
      opacity: linkBox.width > 0 ? 1 : 0,
    });
  }, []);

  useEffect(() => {
    updatePillGeometry(displayId);
  }, [displayId, updatePillGeometry]);

  useEffect(() => {
    if (typeof document === "undefined" || !document.fonts?.ready) return;
    let alive = true;
    void document.fonts.ready.then(() => {
      if (alive) updatePillGeometry(displayIdRef.current);
    });
    return () => {
      alive = false;
    };
  }, [updatePillGeometry]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    let rafId = 0;
    const syncScrollSpy = () => {
      rafId = 0;
      const y = window.scrollY || window.pageYOffset || 0;
      const nextScrolled = y > 16;
      setScrolled((prev) => (prev === nextScrolled ? prev : nextScrolled));

      if (Date.now() < clickLockUntilRef.current) return;

      // Hero is an independent opening: keep nav unselected while viewing Hero.
      const probeY = y + Math.min(260, Math.round(window.innerHeight * 0.34));
      let nextActive: string | null = null;
      for (const item of LANDING_NAV_ITEMS) {
        const el = document.getElementById(item.id);
        if (el) {
          const top = el.getBoundingClientRect().top + y;
          if (probeY >= top) {
            nextActive = item.id;
          }
        }
      }

      const maxScroll = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
      if (nextActive !== null && maxScroll > 0 && y >= maxScroll - 24) {
        nextActive = LANDING_NAV_ITEMS[LANDING_NAV_ITEMS.length - 1].id;
      }

      setActiveId((prev) => (prev === nextActive ? prev : nextActive));
    };

    const onScroll = () => {
      if (rafId !== 0) return;
      rafId = window.requestAnimationFrame(syncScrollSpy);
    };

    const onResize = () => {
      updatePillGeometry(displayIdRef.current);
      if (window.innerWidth > 920) {
        setMobileOpen(false);
      }
    };

    syncScrollSpy();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onResize, { passive: true });
    return () => {
      if (rafId !== 0) window.cancelAnimationFrame(rafId);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onResize);
    };
  }, [updatePillGeometry]);

  // Body scroll lock, Escape handling, and focus management for mobile drawer
  useEffect(() => {
    if (typeof document === "undefined") return;

    const prevOverflow = document.body.style.overflow;
    let focusRaf = 0;
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
      const focusFromKeyboard = openedViaKeyboardRef.current;
      restoreFocusOnCloseRef.current = focusFromKeyboard;
      openedViaKeyboardRef.current = false;
      focusRaf = window.requestAnimationFrame(() => {
        focusRaf = 0;
        if (focusFromKeyboard) {
          firstDrawerActionRef.current?.focus();
        } else {
          drawerRef.current?.focus();
        }
      });
    } else if (prevMobileOpenRef.current) {
      if (restoreFocusOnCloseRef.current) {
        mobileBtnRef.current?.focus();
      }
      restoreFocusOnCloseRef.current = false;
      openedViaKeyboardRef.current = false;
    }
    prevMobileOpenRef.current = mobileOpen;

    if (!mobileOpen) {
      return () => {
        if (focusRaf !== 0) window.cancelAnimationFrame(focusRaf);
        document.body.style.overflow = prevOverflow;
      };
    }

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        restoreFocusOnCloseRef.current = true;
        setMobileOpen(false);
        return;
      }
      if (e.key === "Tab" && drawerRef.current) {
        const focusables = Array.from(
          drawerRef.current.querySelectorAll<HTMLElement>(
            'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
          ),
        );
        if (focusables.length === 0) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (e.shiftKey) {
          if (document.activeElement === first || !drawerRef.current.contains(document.activeElement)) {
            e.preventDefault();
            last.focus();
          }
        } else if (document.activeElement === last || !drawerRef.current.contains(document.activeElement)) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      if (focusRaf !== 0) window.cancelAnimationFrame(focusRaf);
      window.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = prevOverflow;
    };
  }, [mobileOpen]);

  const scrollToTop = () => {
    setActiveId(null);
    setHoveredId(null);
    clickLockUntilRef.current = Date.now() + 900;
    setMobileOpen(false);
    if (typeof window === "undefined") return;
    const reduced = Boolean(
      window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches,
    );
    window.scrollTo({ top: 0, behavior: reduced ? "auto" : "smooth" });
  };

  const scrollToSection = (sectionId: string) => {
    setActiveId(sectionId);
    setHoveredId(null);
    clickLockUntilRef.current = Date.now() + 900;
    setMobileOpen(false);
    if (typeof document === "undefined") return;
    const reduced =
      typeof window !== "undefined" &&
      Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches);
    const target = document.getElementById(sectionId);
    target?.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
  };

  const navHoverState =
    hoveredId === null
      ? activeId === null
        ? "idle"
        : "rest"
      : hoveredId === activeId
        ? "active"
        : "other";

  return (
    <header
      id="landing-header"
      className={`axo-sp-header is-v14${scrolled ? " is-scrolled" : ""}${mobileOpen ? " is-menu-open" : ""}`}
    >
      <div className="axo-sp-header-inner">
        <a
          id="btn-landing-logo"
          href="#landing-hero"
          className="axo-sp-logo"
          aria-label="Axo — Về đầu trang giới thiệu"
          onClick={(e) => {
            e.preventDefault();
            scrollToTop();
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
          className="axo-sp-nav is-v14"
          data-nav-hover-state={navHoverState}
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
            const isSectionActive = activeId === item.id;
            const isHovered = hoveredId === item.id;
            return (
              <a
                key={item.id}
                ref={(el) => {
                  linkRefs.current[item.id] = el;
                }}
                id={`nav-landing-${item.id}`}
                href={`#${item.id}`}
                className={`axo-sp-nav-link${isSectionActive ? " is-active is-current-section" : ""}${isHovered ? " is-hovered" : ""}`}
                aria-current={isSectionActive ? "location" : undefined}
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
          {!mobileOpen && (
            <>
              <a
                id="btn-landing-header-library"
                href="/library"
                className="axo-sp-btn-ghost"
                onMouseEnter={prefetchLibraryShell}
                onFocus={prefetchLibraryShell}
                onClick={(e) => {
                  e.preventDefault();
                  openLibraryFromLanding();
                }}
              >
                Thư viện
              </a>
              <button
                id="btn-landing-header-start"
                type="button"
                className="axo-sp-btn-primary"
                onMouseEnter={prefetchWorkspaceShell}
                onFocus={prefetchWorkspaceShell}
                onClick={enterAxoWorkspace}
              >
                {user ? "Vào ứng dụng" : "Bắt đầu"}
              </button>
            </>
          )}

          <button
            ref={mobileBtnRef}
            id="btn-landing-mobile-menu"
            type="button"
            className="axo-sp-mobile-toggle"
            aria-expanded={mobileOpen}
            aria-controls="landing-mobile-drawer"
            aria-label={mobileOpen ? "Đóng điều hướng" : "Mở điều hướng"}
            onPointerDown={() => {
              openedViaKeyboardRef.current = false;
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                openedViaKeyboardRef.current = true;
              }
            }}
            onClick={() => setMobileOpen((v) => !v)}
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
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
            ref={drawerRef}
            id="landing-mobile-drawer"
            className="axo-sp-mobile-drawer"
            role="dialog"
            aria-modal="true"
            aria-label="Điều hướng di động Axo"
            tabIndex={-1}
          >
            <nav className="axo-sp-mobile-links" aria-label="Mục trang giới thiệu">
              {LANDING_NAV_ITEMS.map((item, idx) => (
                <a
                  key={item.id}
                  ref={idx === 0 ? firstDrawerActionRef : undefined}
                  id={`drawer-nav-${item.id}`}
                  href={`#${item.id}`}
                  className={`axo-sp-mobile-link${activeId === item.id ? " is-active" : ""}`}
                  aria-current={activeId === item.id ? "location" : undefined}
                  onClick={(e) => {
                    e.preventDefault();
                    scrollToSection(item.id);
                  }}
                >
                  {item.label}
                </a>
              ))}
              <a
                id="btn-landing-drawer-library"
                href="/library"
                className="axo-sp-mobile-link axo-sp-mobile-link-utility"
                onClick={(e) => {
                  e.preventDefault();
                  setMobileOpen(false);
                  openLibraryFromLanding();
                }}
              >
                <span>Thư viện</span>
                <svg
                  className="axo-sp-mobile-link-arrow"
                  width="15"
                  height="15"
                  viewBox="0 0 16 16"
                  fill="none"
                  aria-hidden="true"
                  focusable="false"
                >
                  <path
                    d="M3.5 8h9M8.75 4.25L12.5 8l-3.75 3.75"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </a>
            </nav>
            <div className="axo-sp-mobile-cta-row">
              <button
                id="btn-landing-drawer-primary"
                type="button"
                className="axo-sp-btn-primary axo-sp-btn-full"
                onClick={() => {
                  setMobileOpen(false);
                  enterAxoWorkspace();
                }}
              >
                {user ? "Vào ứng dụng" : "Bắt đầu dựng hình"}
              </button>
            </div>
          </div>
        </>
      )}
    </header>
  );
}
