import { create } from "zustand";
import type { ClassroomSession } from "./classroom-sync";

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
  /* W13 — cạnh đây từng có `challengeOpen` + `commitmentCount` (số lần học sinh
     chốt một câu trả lời được chấm). Bỏ quiz thì bỏ luôn: bảng quan sát nay chở
     ĐÚNG MỘT loại bằng chứng tham gia — em này có động tay vào mô hình hay chỉ
     bấm chạy. Bất biến #27 (bảng đọc bằng chứng, không phán đúng/sai) vì thế
     chặt hơn trước, không lỏng đi. */
  actionCount: number | null;
  updatedAt: string | null;
}

/** Một dòng của bảng THEO DÕI — tiêu điểm ngữ nghĩa NGAY LÚC NÀY. */
export interface MonitorRow {
  studentId: number;
  studentName: string;
  assignmentId: number | null;
  assignmentTitle: string | null;
  currentStep: number | null;
  stepCount: number | null;
  /** ID NGỮ NGHĨA của Scene3D (`M`, `chop::face:1`) — không phải UUID Three.js. */
  selectedId: string | null;
  lastAction: string | null;
  helpRequested: boolean;
  helpWaitingSeconds: number | null;
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

  // ── PHIÊN DẠY TRỰC TIẾP ────────────────────────────────────────────────
  //
  // Store này chỉ sở hữu dữ liệu ĐIỀU PHỐI. Nó KHÔNG giữ `GeometryState`
  // (kernel sở hữu) và KHÔNG giữ `InteractionState` (sống ở xưởng 3D của
  // chính trình duyệt này). Giữ hộ một trong hai là dựng bản sao thứ hai của
  // một sự thật đã có chủ.
  session: ClassroomSession | null;
  /** Lớp đang theo dõi phiên. `null` = không poll. */
  sessionClassId: number | null;
  /** Lần cuối máy chủ trả lời. Dùng để nói "đang kết nối lại", không để sắp thứ tự. */
  sessionFetchedAt: number | null;
  monitor: { classroomId: number; rows: MonitorRow[]; serverNow: string } | null;
  /** Chính người đang đăng nhập có đang giơ tay không. */
  helpRequested: boolean;

  loadSession: (classId: number) => Promise<void>;
  startSession: (classId: number, assignmentId: number | null,
                 mode?: "follow" | "free") => Promise<boolean>;
  endSession: (classId: number) => Promise<void>;
  sendCommand: (classId: number, cmd: SessionCommand) => Promise<boolean>;
  loadMonitor: (classId: number) => Promise<void>;
  requestHelp: (assignmentId: number, requested: boolean) => Promise<void>;
  clearHelp: (classId: number, studentId: number) => Promise<void>;

  clearNotice: () => void;
  clearError: () => void;
}

/** Lệnh giáo viên phát. Hình dạng khớp `session_router.CommandBody`. */
export interface SessionCommand {
  kind: "STATE_UPDATE" | "SET_MODE" | "SYNC_CLASS";
  mode?: "follow" | "free";
  assignmentId?: number;
  currentStep?: number;
  selectedId?: string | null;
  isolatedIds?: string[];
  explodedGroups?: string[];
}

export interface ProgressBody {
  cursor: number;
  stepCount: number;
  exploreOpen: boolean;
  actionCount: number;
  completed: boolean;
  /** ID NGỮ NGHĨA của vật đang chọn. `null` = chưa chọn gì. */
  selectedId?: string | null;
  /** Enum ở máy chủ (`ACTIONS`); chuỗi lạ bị bỏ ở đó, không hiện lên bảng GV. */
  lastAction?: string | null;
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

  // ── PHIÊN DẠY TRỰC TIẾP ────────────────────────────────────────────────
  session: null,
  sessionClassId: null,
  sessionFetchedAt: null,
  monitor: null,
  helpRequested: false,

  loadSession: async (classId) => {
    const res = await fetch(`/api/classes/${classId}/session`, { ...OPTS, method: "GET" })
      .catch(() => null);
    // Một nhịp hỏi hỏng KHÔNG được làm sập xưởng hình (`§17`). Giữ nguyên
    // phiên đã biết và để `sessionFetchedAt` cũ đi — chính độ cũ ấy là thứ
    // giao diện dùng để nói "đang kết nối lại", trung thực hơn là xoá sạch.
    if (!res || !res.ok) return;
    const body = await res.json();
    set({ session: body.session ?? null, sessionClassId: classId,
          sessionFetchedAt: Date.now() });
  },

  startSession: async (classId, assignmentId, mode = "follow") => {
    const res = await fetch(`/api/classes/${classId}/session`, {
      ...OPTS, method: "POST", body: JSON.stringify({ assignmentId, mode }),
    }).catch(() => null);
    if (!res || !res.ok) { set({ error: res ? await errorOf(res) : null }); return false; }
    const body = await res.json();
    set({ session: body.session ?? null, sessionClassId: classId,
          sessionFetchedAt: Date.now(), notice: "Đã bắt đầu tiết học." });
    return true;
  },

  endSession: async (classId) => {
    const res = await fetch(`/api/classes/${classId}/session`, { ...OPTS, method: "DELETE" })
      .catch(() => null);
    if (!res || !res.ok) { set({ error: res ? await errorOf(res) : null }); return; }
    set({ session: null, sessionFetchedAt: Date.now(), notice: "Đã kết thúc tiết học." });
  },

  sendCommand: async (classId, cmd) => {
    const s = get().session;
    // `roundId` LUÔN đi kèm: máy chủ từ chối 409 nếu tab này thuộc tiết cũ, và
    // đó là chỗ duy nhất chặn được một tab quên đóng kéo cả lớp về bài hôm qua.
    if (!s) return false;
    const res = await fetch(`/api/classes/${classId}/session/command`, {
      ...OPTS, method: "POST", body: JSON.stringify({ ...cmd, roundId: s.roundId }),
    }).catch(() => null);
    if (!res || !res.ok) { set({ error: res ? await errorOf(res) : null }); return false; }
    const body = await res.json();
    set({ session: body.session ?? null, sessionFetchedAt: Date.now() });
    return true;
  },

  loadMonitor: async (classId) => {
    const res = await fetch(`/api/classes/${classId}/monitor`, { ...OPTS, method: "GET" })
      .catch(() => null);
    if (!res || !res.ok) { set({ error: res ? await errorOf(res) : null }); return; }
    const body = await res.json();
    set({ monitor: { classroomId: classId, rows: body.rows ?? [],
                     serverNow: body.serverNow },
          session: body.session ?? null, sessionFetchedAt: Date.now() });
  },

  requestHelp: async (assignmentId, requested) => {
    const res = await fetch(`/api/assignments/${assignmentId}/help`, {
      ...OPTS, method: "POST", body: JSON.stringify({ requested }),
    }).catch(() => null);
    if (!res || !res.ok) return;
    set({ helpRequested: Boolean((await res.json()).helpRequested) });
  },

  clearHelp: async (classId, studentId) => {
    const res = await fetch(`/api/classes/${classId}/help/${studentId}/clear`, {
      ...OPTS, method: "POST",
    }).catch(() => null);
    if (!res || !res.ok) return;
    await get().loadMonitor(classId);
  },

  clearNotice: () => set({ notice: null }),
  clearError: () => set({ error: null }),
}));
