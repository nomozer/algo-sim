import { useCallback, useEffect, useRef, useState } from "react";
import { IconAxoLogo } from "../icons";
import { TopNavAccount } from "../TopNav";
import { useAuthStore } from "../../state/auth";
import { enterAxoWorkspace, openLandingLogin, openLibraryFromLanding } from "./landing-geometry-data";

export interface LandingSectionNavItem {
  readonly id: string;
  readonly label: string;
}

const LANDING_NAV_ITEMS: readonly LandingSectionNavItem[] = [
  { id: "landing-hero", label: "Giới thiệu" },
  { id: "cach-hoat-dong", label: "Cách hoạt động" },
  { id: "trai-nghiem", label: "Trải nghiệm" },
];

const ROLE_LABELS: Record<"student" | "teacher" | "admin", string> = {
  student: "Học sinh",
  teacher: "Giáo viên",
  admin: "Quản trị viên",
};

export function LandingHeader() {
  const user = useAuthStore((s) => s.user);
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
  const drawerRef = useRef<HTMLDivElement | null>(null);
  const firstDrawerActionRef = useRef<HTMLAnchorElement | null>(null);
  const prevMobileOpenRef = useRef(false);
  const openedViaKeyboardRef = useRef(false);
  const clickLockUntilRef = useRef<number>(0);

  const displayId = hoveredId ?? activeId;

  const updatePillGeometry = useCallback((targetId: string) => {
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
      if (alive) updatePillGeometry(displayId);
    });
    return () => {
      alive = false;
    };
  }, [displayId, updatePillGeometry]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    let rafId = 0;
    const syncScrollSpy = () => {
      rafId = 0;
      const y = window.scrollY || window.pageYOffset || 0;
      const nextScrolled = y > 16;
      setScrolled((prev) => (prev === nextScrolled ? prev : nextScrolled));

      if (Date.now() < clickLockUntilRef.current) return;

      const probeY = y + 180;
      let nextActive: string = LANDING_NAV_ITEMS[0].id;
      for (const item of LANDING_NAV_ITEMS) {
        const el = document.getElementById(item.id);
        if (el) {
          const top = el.getBoundingClientRect().top + y;
          if (probeY >= top) {
            nextActive = item.id;
          }
        }
      }
      setActiveId((prev) => (prev === nextActive ? prev : nextActive));
    };

    const onScroll = () => {
      if (rafId !== 0) return;
      rafId = window.requestAnimationFrame(syncScrollSpy);
    };

    const onResize = () => {
      updatePillGeometry(displayId);
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
  }, [displayId, updatePillGeometry]);

  // Body scroll lock, Escape handling, and focus management for mobile drawer
  useEffect(() => {
    if (typeof document === "undefined") return;

    const prevOverflow = document.body.style.overflow;
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
      const focusFromKeyboard = openedViaKeyboardRef.current;
      openedViaKeyboardRef.current = false;
      window.requestAnimationFrame(() => {
        if (focusFromKeyboard) {
          firstDrawerActionRef.current?.focus();
        } else {
          drawerRef.current?.focus();
        }
      });
    } else if (prevMobileOpenRef.current) {
      if (openedViaKeyboardRef.current) {
        mobileBtnRef.current?.focus();
      }
      openedViaKeyboardRef.current = false;
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
          {!mobileOpen && (
            <>
              <button
                id="btn-landing-header-library"
                type="button"
                className="axo-sp-btn-ghost"
                onClick={openLibraryFromLanding}
              >
                Thư viện
              </button>
              {!user && (
                <button
                  id="btn-landing-header-login"
                  type="button"
                  className="axo-sp-btn-ghost"
                  onClick={openLandingLogin}
                >
                  Đăng nhập
                </button>
              )}
              <button
                id="btn-landing-header-start"
                type="button"
                className="axo-sp-btn-primary"
                onClick={enterAxoWorkspace}
              >
                {user ? "Vào ứng dụng" : "Bắt đầu"}
              </button>
              {user && (
                <div className="axo-sp-header-account">
                  <TopNavAccount />
                </div>
              )}
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
            {user && (
              <div className="axo-sp-mobile-account" id="landing-mobile-account">
                <div className="axo-sp-mobile-account-name">{user.displayName}</div>
                <span className="axo-sp-mobile-account-role">{ROLE_LABELS[user.role]}</span>
              </div>
            )}
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
              <button
                id="btn-landing-drawer-library"
                type="button"
                className="axo-sp-mobile-link axo-sp-mobile-link-btn"
                onClick={() => {
                  setMobileOpen(false);
                  openLibraryFromLanding();
                }}
              >
                <span>Thư viện mẫu</span>
                <span className="axo-sp-mobile-link-meta" aria-hidden="true">↗</span>
              </button>
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
              {!user && (
                <button
                  id="btn-landing-drawer-login"
                  type="button"
                  className="axo-sp-btn-ghost axo-sp-btn-full"
                  onClick={() => {
                    setMobileOpen(false);
                    openLandingLogin();
                  }}
                >
                  Đăng nhập tài khoản
                </button>
              )}
            </div>
          </div>
        </>
      )}
    </header>
  );
}
