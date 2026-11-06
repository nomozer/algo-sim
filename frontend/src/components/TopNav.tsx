import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { create } from "zustand";
import { useAppStore, type AppView } from "../state/store";
import { useAuthStore } from "../state/auth";
import { useClassroomStore } from "../state/classroom";
import {
  IconAlert,
  IconAxoLogo,
  IconBell,
  IconCheck,
  IconChevronDown,
  IconClose,
  IconHistory,
  IconHome,
  IconInfo,
  IconLibrary,
  IconLogout,
} from "./icons";

/**
 * ĐIỀU HƯỚNG MỨC ỨNG DỤNG, MENU TÀI KHOẢN, CHUÔNG THÔNG BÁO & TOAST (Axo V2.7 Slice 1).
 *
 * Bảo toàn 100% logic phân quyền theo vai trò (`student` / `teacher`) từ máy chủ
 * và tích hợp ngôn ngữ thị giác V2.7:
 *  - Thương hiệu Axo kèm logo hình khối 3D chuẩn.
 *  - Capsule điều hướng `.nav-n1-capsule` tự động co thành icon-only trên màn hình
 *    di động hẹp (390×844, 360×800) để không bao giờ bị tràn hay xén chữ.
 *  - Cụm phải gồm Chuông thông báo (`NotificationDropdown`) và Menu tài khoản
 *    (`.user-profile-btn` + `.account-popover`).
 *  - Hệ thống thông báo góc phải (`ToastContainer` + `useToastStore`) dùng chung.
 */

/* ── Toast Store & ToastContainer (Axo V2.7) ─────────────────────────────── */

export type ToastTone = "info" | "error" | "success";

export interface ToastItem {
  id: string;
  tone: ToastTone;
  title: string;
  description?: string;
  durationMs?: number;
}

interface ToastState {
  toasts: ToastItem[];
  showToast: (toast: Omit<ToastItem, "id"> & { id?: string }) => string;
  pauseToast: (id: string) => void;
  resumeToast: (id: string) => void;
  dismissToast: (id: string) => void;
  clearToasts: () => void;
}

const toastTimers = new Map<string, ReturnType<typeof setTimeout>>();
const toastTimingMeta = new Map<string, { remainingMs: number; startedAt: number }>();
let toastCounter = 0;

export const useToastStore = create<ToastState>((set, get) => ({
  toasts: [],
  showToast: (input) => {
    const current = get().toasts;
    const duplicate = !input.id
      ? current.find(
          (t) =>
            t.tone === input.tone &&
            t.title === input.title &&
            (t.description ?? "") === (input.description ?? ""),
        )
      : undefined;
    const id = input.id ?? duplicate?.id ?? `toast-${++toastCounter}`;
    const durationMs = input.durationMs ?? 5200;
    const item: ToastItem = {
      id,
      tone: input.tone,
      title: input.title,
      description: input.description,
      durationMs,
    };

    const existingTimer = toastTimers.get(id);
    if (existingTimer) {
      clearTimeout(existingTimer);
      toastTimers.delete(id);
    }
    toastTimingMeta.delete(id);

    set((state) => {
      const idx = state.toasts.findIndex((t) => t.id === id);
      if (idx >= 0) {
        const next = [...state.toasts];
        next[idx] = item;
        return { toasts: next };
      }
      return { toasts: [...state.toasts, item].slice(-3) };
    });

    if (durationMs > 0) {
      toastTimingMeta.set(id, { remainingMs: durationMs, startedAt: Date.now() });
      const timer = setTimeout(() => {
        toastTimers.delete(id);
        toastTimingMeta.delete(id);
        get().dismissToast(id);
      }, durationMs);
      toastTimers.set(id, timer);
    }

    return id;
  },
  pauseToast: (id) => {
    const timer = toastTimers.get(id);
    if (!timer) return;
    clearTimeout(timer);
    toastTimers.delete(id);
    const meta = toastTimingMeta.get(id);
    if (meta) {
      const elapsed = Math.max(0, Date.now() - meta.startedAt);
      toastTimingMeta.set(id, {
        remainingMs: Math.max(1800, meta.remainingMs - elapsed),
        startedAt: Date.now(),
      });
    }
  },
  resumeToast: (id) => {
    if (toastTimers.has(id)) return;
    const exists = get().toasts.some((t) => t.id === id);
    const meta = toastTimingMeta.get(id);
    if (!exists || !meta || meta.remainingMs <= 0) return;
    toastTimingMeta.set(id, { remainingMs: meta.remainingMs, startedAt: Date.now() });
    const timer = setTimeout(() => {
      toastTimers.delete(id);
      toastTimingMeta.delete(id);
      get().dismissToast(id);
    }, meta.remainingMs);
    toastTimers.set(id, timer);
  },
  dismissToast: (id) => {
    const timer = toastTimers.get(id);
    if (timer) {
      clearTimeout(timer);
      toastTimers.delete(id);
    }
    toastTimingMeta.delete(id);
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }));
  },
  clearToasts: () => {
    for (const timer of toastTimers.values()) {
      clearTimeout(timer);
    }
    toastTimers.clear();
    toastTimingMeta.clear();
    set({ toasts: [] });
  },
}));

function ToastIcon({ tone }: { tone: ToastTone }) {
  if (tone === "error") return <IconAlert size={16} />;
  if (tone === "success") return <IconCheck size={16} />;
  return <IconInfo size={16} />;
}

export function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);
  const pauseToast = useToastStore((s) => s.pauseToast);
  const resumeToast = useToastStore((s) => s.resumeToast);
  const dismissToast = useToastStore((s) => s.dismissToast);

  if (toasts.length === 0) return null;

  return (
    <div className="axo-toast-stack" aria-live="polite" aria-atomic="false">
      {toasts.map((t) => (
        <div
          key={t.id}
          className="axo-composer-toast visible"
          data-toast-id={t.id}
          data-toast-tone={t.tone}
          role={t.tone === "error" ? "alert" : "status"}
          onMouseEnter={() => pauseToast(t.id)}
          onMouseLeave={() => resumeToast(t.id)}
          onFocus={() => pauseToast(t.id)}
          onBlur={() => resumeToast(t.id)}
        >
          <div className="axo-composer-toast-main">
            <span className="axo-composer-toast-icon-wrap" aria-hidden="true">
              <ToastIcon tone={t.tone} />
            </span>
            <div className="axo-composer-toast-copy">
              <div className="axo-composer-toast-title">{t.title}</div>
              {t.description && (
                <div className="axo-composer-toast-desc">{t.description}</div>
              )}
            </div>
          </div>
          <button
            type="button"
            className="axo-composer-toast-close"
            onClick={() => dismissToast(t.id)}
            aria-label="Đóng thông báo"
            title="Đóng thông báo"
          >
            <IconClose size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}

/* ── Chuông thông báo (NotificationDropdown) ─────────────────────────────── */

interface NotificationEntry {
  id: string;
  title: string;
  subtitle: string;
  targetView: AppView;
}

export function NotificationDropdown({ initialOpen = false }: { initialOpen?: boolean }) {
  const [open, setOpen] = useState(initialOpen);
  const [readIds, setReadIds] = useState<string[]>([]);
  const wrapRef = useRef<HTMLDivElement | null>(null);

  const classes = useClassroomStore((s) => s.classes);
  const assignments = useClassroomStore((s) => s.assignments);
  const session = useClassroomStore((s) => s.session);
  const sessionClassId = useClassroomStore((s) => s.sessionClassId);
  const setView = useAppStore((s) => s.setView);

  const items = useMemo<NotificationEntry[]>(() => {
    const out: NotificationEntry[] = [];
    const classMap = new Map(classes.map((c) => [c.id, c.name]));

    if (session) {
      const clsName =
        sessionClassId !== null
          ? (classMap.get(sessionClassId) ?? `Lớp #${sessionClassId}`)
          : "Lớp học";
      out.push({
        id: `live-${session.sessionId}-${session.roundId}`,
        title: `Phiên học trực tiếp đang diễn ra (${clsName})`,
        subtitle: "Nhấn để vào lớp học",
        targetView: "classes",
      });
    }

    for (const a of assignments) {
      if (a.closed) continue;
      const done = Boolean(a.myPractice?.completed);
      if (done) continue;
      const clsName = classMap.get(a.classroomId);
      out.push({
        id: `asg-${a.id}`,
        title: a.title,
        subtitle: clsName ? `Bài thực hành · ${clsName}` : (a.instruction || "Bài thực hành mới"),
        targetView: "assignments",
      });
    }

    return out;
  }, [assignments, classes, session, sessionClassId]);

  const unreadCount = useMemo(
    () => items.filter((item) => !readIds.includes(item.id)).length,
    [items, readIds],
  );

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    window.addEventListener("mousedown", onPointerDown);
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("mousedown", onPointerDown);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const markAllRead = () => {
    setReadIds(items.map((i) => i.id));
  };

  const handleSelectItem = (entry: NotificationEntry) => {
    if (!readIds.includes(entry.id)) {
      setReadIds((prev) => [...prev, entry.id]);
    }
    setOpen(false);
    setView(entry.targetView);
  };

  return (
    <div className="notif-wrap" ref={wrapRef}>
      <button
        type="button"
        className={`notif-trigger-btn${open ? " is-open" : ""}`}
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label="Thông báo"
        title="Thông báo"
      >
        <IconBell size={16} />
        {unreadCount > 0 && (
          <span className="notif-dot" aria-label={`${unreadCount} thông báo chưa đọc`} />
        )}
      </button>

      {open && (
        <div className="notif-popover open" role="dialog" aria-label="Thông báo">
          <div className="notif-pop-head">
            <span className="notif-pop-title">Thông báo</span>
            {unreadCount > 0 && (
              <button
                type="button"
                className="notif-mark-read-btn"
                onClick={markAllRead}
              >
                <IconCheck size={12} />
                <span>Đánh dấu đã đọc</span>
              </button>
            )}
          </div>

          {items.length === 0 ? (
            <div className="notif-empty">Chưa có thông báo mới.</div>
          ) : (
            <div className="notif-list" role="menu">
              {items.map((item) => {
                const isUnread = !readIds.includes(item.id);
                return (
                  <button
                    type="button"
                    key={item.id}
                    role="menuitem"
                    className={`notif-item${isUnread ? " is-unread" : ""}`}
                    onClick={() => handleSelectItem(item)}
                  >
                    <span className="notif-item-title">{item.title}</span>
                    <span className="notif-item-sub">{item.subtitle}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── TopNav & TopNavAccount ──────────────────────────────────────────────── */

interface Item {
  view: AppView;
  label: string;
  icon: React.ReactNode;
}

/**
 * Axo V2.7 Phase A (P3) — Capsule điều hướng chính chỉ gồm đúng 3 mục:
 *  1. Trang chủ (`home`)
 *  2. Thư viện (`library`)
 *  3. Lịch sử (`history`)
 * Nhất quán choทั้ง khách (Guest), học sinh (Student) và giáo viên (Teacher).
 */
const AXO_V27_NAV_ITEMS: Item[] = [
  { view: "home", label: "Trang chủ", icon: <IconHome size={14} /> },
  { view: "library", label: "Thư viện", icon: <IconLibrary size={14} /> },
  { view: "history", label: "Lịch sử", icon: <IconHistory size={14} /> },
];

/** W05 — tên trang đích của nút quay lại trong xưởng 3D. Khoá `AppView` vào, tiếng Việt ra. */
export const TEN_TRANG: Partial<Record<AppView, string>> = {
  home: "Trang chủ",
  library: "Thư viện",
  history: "Lịch sử",
  classes: "Lớp học",
  assignments: "Bài thực hành",
  observe: "Quan sát lớp",
  account: "Tài khoản",
  monitor: "Theo dõi lớp",
  admin: "Trung tâm quản trị",
};

export function itemsForRole(_role?: "student" | "teacher" | "admin"): Item[] {
  return AXO_V27_NAV_ITEMS;
}

function getInitials(displayName: string): string {
  const parts = displayName.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "A";
  const last = parts[parts.length - 1] || displayName.trim();
  return last.charAt(0).toUpperCase();
}

export function TopNav() {
  const user = useAuthStore((s) => s.user);
  const view = useAppStore((s) => s.view);
  const setView = useAppStore((s) => s.setView);
  const goHome = useAppStore((s) => s.goHome);

  const items = itemsForRole(user?.role);

  return (
    <div className="topnav axo-brand-and-nav">
      <div className="axo-brand">
        <button
          type="button"
          id="btn-brand-home"
          className="nav-wordmark axo-logo-btn"
          onClick={goHome}
          title="Về trang chủ Axo"
          aria-label="Về trang chủ Axo"
        >
          <IconAxoLogo size={22} />
          <span className="nav-wordmark-text">Axo</span>
        </button>
      </div>

      <nav className="topnav-links nav-n1-capsule" aria-label="Điều hướng sản phẩm">
        {items.map((it) => (
          <button
            type="button"
            key={it.view}
            id={`nav-btn-${it.view}`}
            className={`nav-link topnav-link nav-n1-item${view === it.view ? " is-active" : ""}`}
            aria-current={view === it.view ? "page" : undefined}
            aria-label={it.label}
            title={it.label}
            onClick={() => setView(it.view)}
          >
            <span className="topnav-icon" aria-hidden="true">{it.icon}</span>
            <span className="topnav-label">{it.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}

export const HEADER_COMPACT_BREAKPOINT_PX = 720;

export function shouldUseCompactHeaderAccount(params: {
  viewportWidth: number;
  navRight?: number;
  navWidth?: number;
  rightClusterLeft?: number;
  rightClusterWidth?: number;
  nameScrollWidth?: number;
  nameClientWidth?: number;
}): boolean {
  if (params.viewportWidth <= HEADER_COMPACT_BREAKPOINT_PX) {
    return true;
  }
  const hasRects =
    typeof params.navWidth === "number" &&
    params.navWidth > 0 &&
    typeof params.rightClusterWidth === "number" &&
    params.rightClusterWidth > 0 &&
    typeof params.navRight === "number" &&
    typeof params.rightClusterLeft === "number";
  const collision = hasRects && params.navRight! + 14 > params.rightClusterLeft!;
  const nameClipped =
    typeof params.nameClientWidth === "number" &&
    params.nameClientWidth > 0 &&
    typeof params.nameScrollWidth === "number" &&
    params.nameScrollWidth > params.nameClientWidth + 1;
  return Boolean(collision || nameClipped);
}

const useIsomorphicLayoutEffect =
  typeof window !== "undefined" ? useLayoutEffect : useEffect;

export function TopNavAccount({ initialOpen = false }: { initialOpen?: boolean }) {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const view = useAppStore((s) => s.view);
  const setView = useAppStore((s) => s.setView);
  const openAccountModal = useAppStore((s) => s.openAccountModal);
  const accountModalOpen = useAppStore((s) => s.accountModalOpen);

  const [open, setOpen] = useState(initialOpen);
  const groupRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (e: MouseEvent) => {
      if (groupRef.current && !groupRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    window.addEventListener("mousedown", onPointerDown);
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("mousedown", onPointerDown);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  useIsomorphicLayoutEffect(() => {
    if (!user || typeof window === "undefined") return;
    const groupEl = groupRef.current;
    if (!groupEl) return;
    const headerEl = groupEl.closest("header.nav-bar, header.axo-header");
    const profileBtn = groupEl.querySelector<HTMLButtonElement>("#btn-header-user-profile");
    let syncing = false;

    const syncCompactAccountState = () => {
      if (syncing) return;
      syncing = true;
      try {
        const applyCompact = (compact: boolean) => {
          headerEl?.classList.toggle("is-compact-account", compact);
          profileBtn?.classList.toggle("is-compact-account", compact);
        };

        if (shouldUseCompactHeaderAccount({ viewportWidth: window.innerWidth })) {
          applyCompact(true);
          return;
        }

        applyCompact(false);
        if (!headerEl || !profileBtn) return;

        const navCapsule = headerEl.querySelector<HTMLElement>(".nav-n1-capsule");
        const rightCluster = headerEl.querySelector<HTMLElement>(".axo-header-right");
        const nameSpan = profileBtn.querySelector<HTMLElement>(".user-name-txt");
        if (navCapsule && rightCluster) {
          const navRect = navCapsule.getBoundingClientRect();
          const rightRect = rightCluster.getBoundingClientRect();
          if (
            shouldUseCompactHeaderAccount({
              viewportWidth: window.innerWidth,
              navRight: navRect.right,
              navWidth: navRect.width,
              rightClusterLeft: rightRect.left,
              rightClusterWidth: rightRect.width,
              nameScrollWidth: nameSpan?.scrollWidth,
              nameClientWidth: nameSpan?.clientWidth,
            })
          ) {
            applyCompact(true);
          }
        }
      } finally {
        syncing = false;
      }
    };

    syncCompactAccountState();
    window.addEventListener("resize", syncCompactAccountState);
    let ro: ResizeObserver | null = null;
    if (typeof ResizeObserver !== "undefined" && headerEl) {
      ro = new ResizeObserver(() => syncCompactAccountState());
      ro.observe(headerEl);
    }
    return () => {
      window.removeEventListener("resize", syncCompactAccountState);
      ro?.disconnect();
      headerEl?.classList.remove("is-compact-account");
      profileBtn?.classList.remove("is-compact-account");
    };
  }, [user, view]);

  if (!user) return null;

  const displayName = user.displayName || "Người dùng";
  const initials = getInitials(displayName);
  const roleLabel =
    user.role === "admin"
      ? "Quản trị viên"
      : user.role === "teacher"
        ? "Giáo viên"
        : "Học sinh";

  const quotaMax =
    typeof user.dailyLimit === "number" && user.dailyLimit > 0
      ? user.dailyLimit
      : user.role === "admin"
        ? 500
        : user.role === "teacher"
          ? 80
          : 15;
  const quotaUsed = Math.min(
    quotaMax,
    typeof user.usedToday === "number" ? user.usedToday : 0,
  );
  const quotaPct = Math.min(100, Math.round((quotaUsed / quotaMax) * 100));
  const avatarToneClass = user.role === "student" ? "" : user.role;

  return (
    <div className="topnav-account header-user-group visible" id="header-user-actions" ref={groupRef}>
      <div className="account-menu-anchor">
        <button
          type="button"
          id="btn-header-user-profile"
          className={`user-profile-btn topnav-user${view === "account" || accountModalOpen ? " is-active" : ""}${open ? " is-open" : ""}`}
          onClick={() => setOpen((v) => !v)}
          aria-haspopup="menu"
          aria-expanded={open}
          aria-label={`Menu tài khoản ${displayName} (${roleLabel})`}
          title={`${displayName} · ${roleLabel}`}
        >
          <span className={`user-avatar-dot topnav-avatar ${avatarToneClass}`.trim()} id="header-user-avatar" aria-hidden="true">
            {initials}
          </span>
          <span className="user-name-txt topnav-user-name" id="header-user-name">
            {displayName}
          </span>
          <IconChevronDown size={13} className="user-caret-svg" />
        </button>

        {open && (
          <div className="account-popover open" id="account-popover" role="dialog" aria-label="Menu tài khoản">
            <div className="acc-pop-header account-pop-head">
              <span className={`account-pop-avatar ${avatarToneClass}`.trim()} aria-hidden="true">
                {initials}
              </span>
              <div className="account-pop-id-meta">
                <div className="acc-pop-name account-pop-name" id="acc-pop-name">{displayName}</div>
                <div className="acc-pop-email account-pop-email" id="acc-pop-email">{user.email}</div>
                <div className="account-pop-role-row">
                  <span className={`role-chip ${user.role}`}>{roleLabel}</span>
                </div>
              </div>
            </div>

            <div className="acc-pop-quota">
              <div className="acc-pop-quota-top">
                <span>Hạn mức AI hôm nay</span>
                <strong id="acc-pop-quota-txt">{`Đã dùng ${quotaUsed} / ${quotaMax} lượt`}</strong>
              </div>
              <div className="acc-pop-quota-bar">
                <div
                  className="acc-pop-quota-fill"
                  id="acc-pop-quota-fill"
                  style={{ width: `${quotaPct}%` }}
                />
              </div>
            </div>

            <div className="account-pop-actions" role="menu">
              {user.role === "admin" && (
                <button
                  type="button"
                  id="btn-acc-open-admin"
                  className="acc-pop-item account-pop-btn admin-only-item"
                  role="menuitem"
                  onClick={() => {
                    setOpen(false);
                    setView("admin");
                  }}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  </svg>
                  <span>Bảng điều khiển Quản trị</span>
                </button>
              )}

              <button
                type="button"
                id="btn-acc-open-settings"
                className="acc-pop-item account-pop-btn"
                role="menuitem"
                onClick={() => {
                  setOpen(false);
                  openAccountModal("profile");
                }}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
                <span>Cài đặt tài khoản</span>
              </button>

              <button
                type="button"
                id="btn-acc-open-history"
                className="acc-pop-item account-pop-btn"
                role="menuitem"
                onClick={() => {
                  setOpen(false);
                  setView("history");
                }}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <circle cx="12" cy="12" r="9" />
                  <polyline points="12 7 12 12 15 15" />
                </svg>
                <span>Lịch sử học tập</span>
              </button>

              <div className="acc-pop-sep account-pop-sep" role="separator" />

              <button
                type="button"
                id="btn-acc-logout"
                className="acc-pop-item account-pop-btn danger topnav-logout"
                role="menuitem"
                onClick={() => {
                  setOpen(false);
                  void logout();
                }}
                aria-label="Đăng xuất"
              >
                <IconLogout size={15} />
                <span>Đăng xuất</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Adaptive Scroll Header State Machine (hysteresis-guarded, constant size, CLS = 0) ── */

export interface AdaptiveHeaderState {
  isScrolled: boolean;
  lastY: number;
}

const INITIAL_ADAPTIVE_HEADER_STATE: AdaptiveHeaderState = {
  isScrolled: false,
  lastY: 0,
};

const SCROLLED_ENTER_Y = 20;
const SCROLLED_EXIT_Y = 8;

export function computeAdaptiveHeaderState(
  prev: AdaptiveHeaderState | undefined,
  rawScrollY: number,
): AdaptiveHeaderState {
  const base = prev ?? INITIAL_ADAPTIVE_HEADER_STATE;
  const y = Math.max(0, Number.isFinite(rawScrollY) ? rawScrollY : 0);
  // ponytail: dual-threshold hysteresis (8px exit / 20px enter) prevents border/surface flicker near top; size stays 100% constant
  const isScrolled =
    y <= SCROLLED_EXIT_Y ? false : y >= SCROLLED_ENTER_Y ? true : base.isScrolled;
  if (base.isScrolled === isScrolled && base.lastY === y) return base;
  return { isScrolled, lastY: y };
}

