/**
 * DẢI LỚP trong thanh xưởng — chỗ DUY NHẤT nối tầng lớp học vào xưởng 3D.
 *
 * ─── VÌ SAO CẦN MỘT COMPONENT RIÊNG ─────────────────────────────────────
 *
 * `Scene3DExplorer` nhận phiên qua PROPS và không được biết tới `useClassroom
 * Store` — miền hình học không phụ thuộc tầng lớp học. Nhưng cái gì đó phải
 * hỏi máy chủ và phân vai. Đó là file này: nó đứng ở BIÊN, đọc store, rồi trả
 * xuống một mẩu JSX.
 *
 * ─── HAI VAI, MỘT DẢI ───────────────────────────────────────────────────
 *
 * Giáo viên thấy DOCK (đổi chế độ, gọi cả lớp về, theo dõi). Học sinh thấy
 * CHỈ BÁO + nút giơ tay. Không ai thấy phần của người kia — và đó là một luật
 * uỷ quyền được máy chủ cưỡng chế, không phải chuyện ẩn hiện: học sinh có gọi
 * thẳng endpoint cũng nhận 403.
 */
import { useEffect, useRef, useState } from "react";
import { HelpRequestButton, LiveClassDock, StudentLiveIndicator } from "./LiveClassDock";
import { NHIP_PHIEN_MS } from "../state/classroom-sync";
import { useClassroomStore } from "../state/classroom";
import { useAppStore } from "../state/store";
import { useAuthStore } from "../state/auth";

/** Quá hạn này chưa nghe máy chủ ⇒ nói thật là đang kết nối lại. */
const CU_MS = NHIP_PHIEN_MS * 4;

export function LiveClassStrip() {
  const user = useAuthStore((s) => s.user);
  const assignment = useAppStore((s) => s.activeAssignment);
  const setView = useAppStore((s) => s.setView);

  const session = useClassroomStore((s) => s.session);
  const fetchedAt = useClassroomStore((s) => s.sessionFetchedAt);
  const helpRequested = useClassroomStore((s) => s.helpRequested);
  const classes = useClassroomStore((s) => s.classes);
  const monitor = useClassroomStore((s) => s.monitor);
  const loadSession = useClassroomStore((s) => s.loadSession);
  const startSession = useClassroomStore((s) => s.startSession);
  const endSession = useClassroomStore((s) => s.endSession);
  const sendCommand = useClassroomStore((s) => s.sendCommand);
  const requestHelp = useClassroomStore((s) => s.requestHelp);

  const [busy, setBusy] = useState(false);
  const [nhip, setNhip] = useState(0);
  const classId = assignment?.classroomId ?? null;

  /* Nhịp hỏi phiên. Chỉ chạy khi ĐANG ở một bài thuộc một lớp — không có lớp
     thì không có gì để hỏi, và hỏi vẫn là đốt một request mỗi 1,5 giây. */
  useEffect(() => {
    if (classId === null) return;
    void loadSession(classId);
    const t = setInterval(() => void loadSession(classId), NHIP_PHIEN_MS);
    return () => clearInterval(t);
  }, [classId, loadSession]);

  /* Đồng hồ RIÊNG để tính "đã cũ chưa". Không dùng `fetchedAt` làm dependency
     của một effect ghi state — đó là một vòng lặp render. */
  useEffect(() => {
    const t = setInterval(() => setNhip((n) => n + 1), 1000);
    return () => clearInterval(t);
  }, []);
  const cu = fetchedAt !== null && Date.now() - fetchedAt > CU_MS;
  void nhip;

  const lam = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    try { await fn(); } finally { setBusy(false); }
  };

  if (!user || classId === null) return null;

  // ── GIÁO VIÊN ────────────────────────────────────────────────────────────
  if (user.role === "teacher") {
    const lop = classes.find((c) => c.id === classId);
    const rows = monitor?.classroomId === classId ? monitor.rows : [];
    return (
      <LiveClassDock
        session={session}
        className={lop?.name ?? "Lớp"}
        studentCount={rows.length}
        helpCount={rows.filter((r) => r.helpRequested).length}
        assignmentId={assignment?.id ?? null}
        busy={busy}
        onStart={() => void lam(() =>
          startSession(classId, assignment?.id ?? null, "follow"))}
        onEnd={() => void lam(() => endSession(classId))}
        onSetMode={(mode) => void lam(() =>
          sendCommand(classId, { kind: "SET_MODE", mode }))}
        onSync={() => void lam(() =>
          sendCommand(classId, { kind: "SYNC_CLASS" }))}
        onMonitor={() => setView("monitor")}
      />
    );
  }

  // ── HỌC SINH ─────────────────────────────────────────────────────────────
  return (
    <span className="live-hs">
      <StudentLiveIndicator session={session} stale={cu} />
      {assignment && (
        <HelpRequestButton
          requested={helpRequested}
          busy={busy}
          onRequest={() => void lam(() => requestHelp(assignment.id, true))}
          onCancel={() => void lam(() => requestHelp(assignment.id, false))}
        />
      )}
    </span>
  );
}

/**
 * Báo TIÊU ĐIỂM NGỮ NGHĨA của giáo viên lên phiên.
 *
 * Dùng `useRef` giữ chữ ký lần gửi trước + chặn nhịp: xoay hình sinh hàng chục
 * thay đổi mỗi giây, và một `STATE_UPDATE` mỗi khung hình là bão HTTP chứ
 * không phải đồng bộ. Chỉ gửi khi TIÊU ĐIỂM thật sự đổi.
 */
export function useTeacherStateReport(
  classId: number | null,
  focus: { step: number; selectedId: string | null;
           isolatedIds: string[]; explodedGroups: string[] } | null,
) {
  const session = useClassroomStore((s) => s.session);
  const sendCommand = useClassroomStore((s) => s.sendCommand);
  const truoc = useRef<string>("");
  const lucGui = useRef<number>(0);

  useEffect(() => {
    if (classId === null || session === null || focus === null) return;
    const chuKy = [focus.step, focus.selectedId,
                   focus.isolatedIds.join(","), focus.explodedGroups.join(",")].join("|");
    if (chuKy === truoc.current) return;
    const now = Date.now();
    if (now - lucGui.current < 700) return;
    truoc.current = chuKy;
    lucGui.current = now;
    void sendCommand(classId, {
      kind: "STATE_UPDATE",
      currentStep: focus.step,
      selectedId: focus.selectedId,
      isolatedIds: focus.isolatedIds,
      explodedGroups: focus.explodedGroups,
    });
  }, [classId, session, focus, sendCommand]);
}
