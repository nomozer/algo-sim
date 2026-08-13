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

export type Role = "student" | "teacher";

export interface AuthUser {
  id: number;
  email: string;
  displayName: string;
  role: Role;
  mustChangePassword: boolean;
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
    email: string; displayName: string; password: string;
    role?: Role; teacherCode?: string;
  }) => Promise<boolean>;
  logout: () => Promise<void>;
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
  } catch { /* body không phải JSON */ }
  return "Không kết nối được máy chủ. Em thử lại sau ít phút nhé.";
}

/** `credentials: "include"` là BẮT BUỘC: phiên nằm ở cookie httpOnly. */
const OPTS: RequestInit = { credentials: "include", headers: { "Content-Type": "application/json" } };

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
      set({ user: body.user ?? null, entitlement: body.entitlement ?? UNKNOWN, resolved: true });
    } catch {
      /* Máy chủ không trả lời: giữ nguyên thứ đang biết và đánh dấu đã hỏi.
         KHÔNG tự đăng xuất người dùng vì một lần mất mạng (`§33`). */
      set({ resolved: true });
    }
  },

  login: async (email, password) => {
    set({ busy: true, error: null });
    const res = await fetch("/api/auth/login", {
      ...OPTS, method: "POST", body: JSON.stringify({ email, password }),
    }).catch(() => null);
    if (!res || !res.ok) {
      set({ busy: false, error: res ? await errorOf(res) : "Không kết nối được máy chủ." });
      return false;
    }
    const body = await res.json();
    set({ user: body.user, entitlement: body.entitlement, busy: false, authGate: null, resolved: true });
    return true;
  },

  register: async (input) => {
    set({ busy: true, error: null });
    const res = await fetch("/api/auth/register", {
      ...OPTS, method: "POST", body: JSON.stringify(input),
    }).catch(() => null);
    if (!res || !res.ok) {
      set({ busy: false, error: res ? await errorOf(res) : "Không kết nối được máy chủ." });
      return false;
    }
    const body = await res.json();
    set({ user: body.user, entitlement: body.entitlement, busy: false, authGate: null, resolved: true });
    return true;
  },

  logout: async () => {
    await fetch("/api/auth/logout", { ...OPTS, method: "POST" }).catch(() => null);
    set({ user: null, entitlement: UNKNOWN, authGate: null });
    await get().refresh();
  },

  openAuthGate: (mode) => set({ authGate: mode, error: null }),
  closeAuthGate: () => set({ authGate: null, error: null }),
  clearError: () => set({ error: null }),
}));

/** Đang đăng nhập hay không — dùng ở chỗ chỉ cần một boolean. */
export const isAuthenticated = (s: AuthState): boolean => s.user !== null;
