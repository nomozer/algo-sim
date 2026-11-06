import { create } from "zustand";

/**
 * M18 — DANH TÍNH VÀ QUYỀN, ĐỌC TỪ MÁY CHỦ.
 *
 * ─── VÌ SAO LÀ MỘT STORE RIÊNG ────────────────────────────────────────────
 *
 * `state/store.ts` sở hữu PHIÊN MÔ PHỎNG và cố ý **mù domain**. Nhét tài khoản
 * vào đó sẽ làm nó biết hai chuyện chẳng liên quan gì nhau, và mọi test mô
 * phỏng sẽ phải dựng một người dùng giả để chạy. Hai store, hai trách nhiệm.
 *
 * ─── VÌ SAO KHÔNG LƯU VAI TRÒ VÀO localStorage ────────────────────────────
 *
 * Vai trò ở đây là BẢN CHIẾU để vẽ giao diện, KHÔNG phải quyền. Sửa nó trong
 * devtools thì thấy được thanh điều hướng của giáo viên và **không gọi nổi một
 * endpoint nào** — máy chủ tra vai trò từ phiên, không đọc từ request
 * (`§7`, khoá bằng `test_auth_api.py`). Nên nó không được lưu bền: một bản sao
 * cũ trong localStorage chỉ tạo ra khoảng thời gian màn hình nói sai.
 */

export type Role = "student" | "teacher" | "admin";

export interface AuthUser {
  id: number;
  email: string;
  displayName: string;
  role: Role;
  mustChangePassword: boolean;
  school?: string;
  grade?: string;
  className?: string;
  workplace?: string;
  subject?: string;
  status?: string;
  usedToday?: number;
  dailyLimit?: number;
  bonusQuotaToday?: number;
}

export interface Entitlement {
  canRunSimulation: boolean;
  canPersistHistory: boolean;
  canJoinClass: boolean;
  canOwnClass: boolean;
  canReceiveAssignment: boolean;
  /** `null` = đã đăng nhập, không còn giới hạn lượt thử. */
  trialsLeft: number | null;
}

/** Quyền của khách khi CHƯA hỏi được máy chủ — bảo thủ, không hứa trước. */
const UNKNOWN: Entitlement = {
  canRunSimulation: true,
  canPersistHistory: false,
  canJoinClass: false,
  canOwnClass: false,
  canReceiveAssignment: false,
  trialsLeft: null,
};

interface AuthState {
  user: AuthUser | null;
  entitlement: Entitlement;
  /** Đã hỏi máy chủ xong chưa — trước đó KHÔNG được vẽ "chưa đăng nhập". */
  resolved: boolean;
  busy: boolean;
  error: string | null;
  /** Cửa đăng nhập/đăng ký đang mở ở chế độ nào. `null` = đóng. */
  authGate: "login" | "register" | null;

  refresh: () => Promise<void>;
  login: (email: string, password: string) => Promise<boolean>;
  register: (input: {
    email: string;
    displayName: string;
    password: string;
    role?: Role;
    teacherCode?: string;
  }) => Promise<boolean>;
  logout: () => Promise<void>;
  updateProfile: (
    input:
      | string
      | {
          displayName: string;
          school?: string;
          grade?: string;
          className?: string;
          workplace?: string;
          subject?: string;
        },
  ) => Promise<{ ok: boolean; error?: string }>;
  changePassword: (
    currentPassword: string,
    newPassword: string,
  ) => Promise<{ ok: boolean; error?: string }>;
  requestPasswordReset: (
    email: string,
  ) => Promise<{
    ok: boolean;
    smtpConfigured?: boolean;
    deliveryStatus?: string;
    message?: string;
    error?: string;
  }>;
  fetchRecoveryStatus: () => Promise<{ emailRecoveryAvailable: boolean }>;
  resetPassword: (
    token: string,
    newPassword: string,
    email?: string,
  ) => Promise<{ ok: boolean; updated?: boolean; error?: string }>;
  openAuthGate: (mode: "login" | "register") => void;
  closeAuthGate: () => void;
  clearError: () => void;
}

/** Đọc câu lỗi tiếng Việt của backend; không có thì trả câu chung. */
async function errorOf(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (typeof body?.error === "string") return body.error;
  } catch {
    /* body không phải JSON */
  }
  return "Không kết nối được máy chủ. Em thử lại sau ít phút nhé.";
}

/** `credentials: "include"` là BẮT BUỘC: phiên nằm ở cookie httpOnly. */
const OPTS: RequestInit = {
  credentials: "include",
  headers: { "Content-Type": "application/json" },
};

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  entitlement: UNKNOWN,
  resolved: false,
  busy: false,
  error: null,
  authGate: null,

  refresh: async () => {
    try {
      const res = await fetch("/api/auth/me", { ...OPTS, method: "GET" });
      if (!res.ok) throw new Error("me failed");
      const body = await res.json();
      set({
        user: body.user ?? null,
        entitlement: body.entitlement ?? UNKNOWN,
        resolved: true,
      });
    } catch {
      /* Máy chủ không trả lời: giữ nguyên thứ đang biết và đánh dấu đã hỏi.
         KHÔNG tự đăng xuất người dùng vì một lần mất mạng (`§33`). */
      set({ resolved: true });
    }
  },

  login: async (email, password) => {
    set({ busy: true, error: null });
    const res = await fetch("/api/auth/login", {
      ...OPTS,
      method: "POST",
      body: JSON.stringify({ email, password }),
    }).catch(() => null);
    if (!res || !res.ok) {
      set({
        busy: false,
        error: res ? await errorOf(res) : "Không kết nối được máy chủ.",
      });
      return false;
    }
    const body = await res.json();
    set({
      user: body.user,
      entitlement: body.entitlement,
      busy: false,
      authGate: null,
      resolved: true,
    });
    return true;
  },

  register: async (input) => {
    set({ busy: true, error: null });
    const res = await fetch("/api/auth/register", {
      ...OPTS,
      method: "POST",
      body: JSON.stringify(input),
    }).catch(() => null);
    if (!res || !res.ok) {
      set({
        busy: false,
        error: res ? await errorOf(res) : "Không kết nối được máy chủ.",
      });
      return false;
    }
    const body = await res.json();
    set({
      user: body.user,
      entitlement: body.entitlement,
      busy: false,
      authGate: null,
      resolved: true,
    });
    return true;
  },

  logout: async () => {
    await fetch("/api/auth/logout", { ...OPTS, method: "POST" }).catch(() => null);
    set({ user: null, entitlement: UNKNOWN, authGate: null });
    await get().refresh();
  },

  updateProfile: async (input) => {
    set({ busy: true, error: null });
    const payload = typeof input === "string" ? { displayName: input } : input;
    const res = await fetch("/api/auth/profile", {
      ...OPTS,
      method: "PATCH",
      body: JSON.stringify(payload),
    }).catch(() => null);
    if (!res || !res.ok) {
      const err = res ? await errorOf(res) : "Không kết nối được máy chủ.";
      set({ busy: false, error: err });
      return { ok: false, error: err };
    }
    const body = await res.json();
    set({
      user: body.user ?? get().user,
      entitlement: body.entitlement ?? get().entitlement,
      busy: false,
      error: null,
    });
    return { ok: true };
  },

  changePassword: async (currentPassword, newPassword) => {
    set({ busy: true, error: null });
    const res = await fetch("/api/auth/password", {
      ...OPTS,
      method: "POST",
      body: JSON.stringify({ currentPassword, newPassword }),
    }).catch(() => null);
    if (!res || !res.ok) {
      const err = res ? await errorOf(res) : "Không kết nối được máy chủ.";
      set({ busy: false, error: err });
      return { ok: false, error: err };
    }
    const curUser = get().user;
    set({
      user: curUser ? { ...curUser, mustChangePassword: false } : null,
      busy: false,
      error: null,
    });
    return { ok: true };
  },

  requestPasswordReset: async (email) => {
    set({ busy: true, error: null });
    const res = await fetch("/api/auth/forgot-password", {
      ...OPTS,
      method: "POST",
      body: JSON.stringify({ email }),
    }).catch(() => null);
    if (!res || !res.ok) {
      const err = res ? await errorOf(res) : "Không kết nối được máy chủ.";
      set({ busy: false, error: err });
      return { ok: false, error: err };
    }
    const body = await res.json();
    set({ busy: false, error: null });
    return {
      ok: true,
      smtpConfigured: Boolean(body.smtpConfigured),
      deliveryStatus: typeof body.deliveryStatus === "string" ? body.deliveryStatus : undefined,
      message: typeof body.message === "string" ? body.message : undefined,
    };
  },

  fetchRecoveryStatus: async () => {
    const res = await fetch("/api/auth/recovery-status", OPTS).catch(() => null);
    if (!res || !res.ok) {
      return { emailRecoveryAvailable: false };
    }
    const body = await res.json().catch(() => ({}));
    return { emailRecoveryAvailable: Boolean(body?.emailRecoveryAvailable) };
  },

  resetPassword: async (token, newPassword, email) => {
    set({ busy: true, error: null });
    const res = await fetch("/api/auth/reset-password", {
      ...OPTS,
      method: "POST",
      body: JSON.stringify({ token, newPassword, ...(email ? { email } : {}) }),
    }).catch(() => null);
    if (!res || !res.ok) {
      const err = res ? await errorOf(res) : "Không kết nối được máy chủ.";
      set({ busy: false, error: err });
      return { ok: false, error: err };
    }
    const body = await res.json();
    set({ busy: false, error: null });
    return { ok: true, updated: Boolean(body.updated) };
  },

  openAuthGate: (mode) => set({ authGate: mode, error: null }),
  closeAuthGate: () => set({ authGate: null, error: null }),
  clearError: () => set({ error: null }),
}));

/** Đang đăng nhập hay không — dùng ở chỗ chỉ cần một boolean. */
export const isAuthenticated = (s: AuthState): boolean => s.user !== null;
