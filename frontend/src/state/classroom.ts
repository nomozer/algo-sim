import { create } from "zustand";

/**
 * M18 — LỚP HỌC VÀ BÀI THỰC HÀNH (bản chiếu của máy chủ).
 *
 * Store này KHÔNG giữ sự thật: máy chủ giữ. Nó giữ thứ vừa tải về để vẽ, cộng
 * cờ đang-tải và câu lỗi. Mọi phán quyết quyền đã xảy ra ở backend trước khi
 * dữ liệu tới đây (`§23`) — không hàm nào dưới đây được "kiểm tra quyền" lần
 * nữa, vì một phép kiểm ở client là thứ tự nó không chặn được ai.
 */

export interface Classroom {
  id: number;
  name: string;
  archived: boolean;
  createdAt: string;
  /** CHỈ có với giáo viên sở hữu lớp — học sinh không nhận trường này. */
  joinCode?: string | null;
  codeActive?: boolean;
}

export interface PracticeSnapshot {
  cursor: number;
  stepCount: number;
  completed: boolean;
  updatedAt: string;
}

export interface Assignment {
  id: number;
  classroomId: number;
  title: string;
  instruction: string;
  simulationId: string;
  closed: boolean;
  createdAt: string;
  /** Tiến độ của CHÍNH người đang đăng nhập; `null` = chưa bắt đầu. */
  myPractice?: PracticeSnapshot | null;
  /** Chỉ có khi mở một bài cụ thể. */
  envelope?: unknown;
}

export interface ObserveRow {
  studentId: number;
  studentName: string;
  assignmentId: number;
  assignmentTitle: string;
  simulationId: string;
  status: "not_started" | "practicing" | "completed";
  cursor: number | null;
  stepCount: number | null;
  exploreOpen: boolean | null;
  challengeOpen: boolean | null;
  actionCount: number | null;
  commitmentCount: number | null;
  updatedAt: string | null;
}

export interface ClassMember {
  id: number;
  displayName: string;
  email: string;
}

interface ClassroomState {
  classes: Classroom[];
  assignments: Assignment[];
  members: Record<number, ClassMember[]>;
  observe: { classroomId: number; rows: ObserveRow[]; observedAt: string } | null;
  busy: boolean;
  error: string | null;
  notice: string | null;

  loadClasses: () => Promise<void>;
  loadAssignments: () => Promise<void>;
  createClass: (name: string) => Promise<Classroom | null>;
  regenerateCode: (classId: number) => Promise<void>;
  joinClass: (code: string) => Promise<boolean>;
  loadMembers: (classId: number) => Promise<void>;
  assign: (input: {
    classroomId: number; title: string; instruction: string; envelope: unknown;
  }) => Promise<boolean>;
  openAssignment: (id: number) => Promise<Assignment | null>;
  reportProgress: (assignmentId: number, body: ProgressBody) => Promise<void>;
  loadObserve: (classId: number) => Promise<void>;
  clearNotice: () => void;
  clearError: () => void;
}

export interface ProgressBody {
  cursor: number;
  stepCount: number;
  exploreOpen: boolean;
  challengeOpen: boolean;
  actionCount: number;
  commitmentCount: number;
  completed: boolean;
}

const OPTS: RequestInit = {
  credentials: "include",
  headers: { "Content-Type": "application/json" },
};

async function errorOf(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (typeof body?.error === "string") return body.error;
  } catch { /* không phải JSON */ }
  return "Không kết nối được máy chủ. Em thử lại sau ít phút nhé.";
}

export const useClassroomStore = create<ClassroomState>((set, get) => ({
  classes: [],
  assignments: [],
  members: {},
  observe: null,
  busy: false,
  error: null,
  notice: null,

  loadClasses: async () => {
    const res = await fetch("/api/classes", { ...OPTS, method: "GET" }).catch(() => null);
    if (!res || !res.ok) return;           // chưa đăng nhập / mất mạng ⇒ im lặng
    set({ classes: (await res.json()).classes ?? [] });
  },

  loadAssignments: async () => {
    const res = await fetch("/api/assignments", { ...OPTS, method: "GET" }).catch(() => null);
    if (!res || !res.ok) return;
    set({ assignments: (await res.json()).assignments ?? [] });
  },

  createClass: async (name) => {
    set({ busy: true, error: null });
    const res = await fetch("/api/classes", {
      ...OPTS, method: "POST", body: JSON.stringify({ name }),
    }).catch(() => null);
    if (!res || !res.ok) {
      set({ busy: false, error: res ? await errorOf(res) : "Không kết nối được máy chủ." });
      return null;
    }
    const c: Classroom = await res.json();
    set((s) => ({ classes: [c, ...s.classes], busy: false, notice: `Đã tạo lớp ${c.name}.` }));
    return c;
  },

  regenerateCode: async (classId) => {
    const res = await fetch(`/api/classes/${classId}/code`, { ...OPTS, method: "POST" })
      .catch(() => null);
    if (!res || !res.ok) return;
    const c: Classroom = await res.json();
    set((s) => ({
      classes: s.classes.map((x) => (x.id === c.id ? c : x)),
      notice: "Đã đổi mã lớp. Mã cũ không dùng được nữa.",
    }));
  },

  joinClass: async (code) => {
    set({ busy: true, error: null });
    const res = await fetch("/api/classes/join", {
      ...OPTS, method: "POST", body: JSON.stringify({ code }),
    }).catch(() => null);
    if (!res || !res.ok) {
      set({ busy: false, error: res ? await errorOf(res) : "Không kết nối được máy chủ." });
      return false;
    }
    const body = await res.json();
    set({ busy: false, notice: body.alreadyMember
      ? `Em đã ở trong lớp ${body.classroom.name} rồi.`
      : `Đã vào lớp ${body.classroom.name}.` });
    await get().loadClasses();
    await get().loadAssignments();
    return true;
  },

  loadMembers: async (classId) => {
    const res = await fetch(`/api/classes/${classId}/members`, { ...OPTS, method: "GET" })
      .catch(() => null);
    if (!res || !res.ok) return;
    const body = await res.json();
    set((s) => ({ members: { ...s.members, [classId]: body.members ?? [] } }));
  },

  assign: async ({ classroomId, title, instruction, envelope }) => {
    set({ busy: true, error: null });
    const res = await fetch("/api/assignments", {
      ...OPTS, method: "POST",
      body: JSON.stringify({ classroomId, title, instruction, envelope }),
    }).catch(() => null);
    if (!res || !res.ok) {
      set({ busy: false, error: res ? await errorOf(res) : "Không kết nối được máy chủ." });
      return false;
    }
    set({ busy: false, notice: "Đã giao bài cho lớp." });
    await get().loadAssignments();
    return true;
  },

  openAssignment: async (id) => {
    const res = await fetch(`/api/assignments/${id}`, { ...OPTS, method: "GET" })
      .catch(() => null);
    if (!res || !res.ok) {
      set({ error: res ? await errorOf(res) : "Không kết nối được máy chủ." });
      return null;
    }
    return await res.json();
  },

  reportProgress: async (assignmentId, body) => {
    /* Gửi-và-quên có chủ đích: mất mạng KHÔNG được làm hỏng buổi thực hành
       đang diễn ra (`§33`). Bằng chứng tới muộn vẫn là bằng chứng. */
    await fetch(`/api/assignments/${assignmentId}/progress`, {
      ...OPTS, method: "POST", body: JSON.stringify(body),
    }).catch(() => null);
  },

  loadObserve: async (classId) => {
    const res = await fetch(`/api/classes/${classId}/observe`, { ...OPTS, method: "GET" })
      .catch(() => null);
    if (!res || !res.ok) {
      set({ error: res ? await errorOf(res) : null });
      return;
    }
    const body = await res.json();
    set({ observe: { classroomId: classId, rows: body.rows ?? [], observedAt: body.observedAt } });
  },

  clearNotice: () => set({ notice: null }),
  clearError: () => set({ error: null }),
}));
