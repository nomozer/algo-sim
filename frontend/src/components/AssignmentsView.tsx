import { useEffect } from "react";
import { useAuthStore } from "../state/auth";
import { useClassroomStore } from "../state/classroom";
import { useAppStore } from "../state/store";

/**
 * M18 — BÀI THỰC HÀNH.
 *
 * Học sinh: danh sách bài được giao + chỗ đang dở. Giáo viên: bài mình đã giao.
 *
 * MỞ BÀI = NẠP ENVELOPE ĐÃ VALIDATE, KHÔNG GỌI LLM. Đây là điểm khác quan trọng
 * so với "Mô phỏng mới": bài giao phải giống hệt nhau ở mọi máy, còn một lượt
 * phân tích lại sẽ cho ba mươi học sinh ba mươi mô phỏng.
 */
export function AssignmentsView() {
  const user = useAuthStore((s) => s.user);
  const assignments = useClassroomStore((s) => s.assignments);
  const load = useClassroomStore((s) => s.loadAssignments);
  const open = useClassroomStore((s) => s.openAssignment);
  const error = useClassroomStore((s) => s.error);
  const loadEnvelope = useAppStore((s) => s.loadEnvelope);
  const setActiveAssignment = useAppStore((s) => s.setActiveAssignment);

  useEffect(() => { void load(); }, [load]);

  if (!user) return null;
  const isTeacher = user.role === "teacher";

  const openOne = async (id: number) => {
    const a = await open(id);
    if (!a?.envelope) return;
    /* Gắn danh tính bài TRƯỚC khi nạp: `loadEnvelope` dựng phiên mới, và phiên
       đó phải biết nó thuộc bài nào để báo tiến độ về đúng chỗ. */
    setActiveAssignment({ id: a.id, title: a.title, instruction: a.instruction });
    loadEnvelope(a.envelope as Parameters<typeof loadEnvelope>[0]);
  };

  return (
    <div className="page-stack">
      <header className="page-head">
        <h1 className="page-title">{isTeacher ? "Bài đã giao" : "Bài thực hành"}</h1>
        <p className="page-sub">
          {isTeacher
            ? "Những bài em đã giao cho các lớp của mình."
            : "Bài cô/thầy giao. Mở ra làm, lần sau vào lại vẫn ở đúng chỗ em dừng."}
        </p>
      </header>

      {error && <p className="form-error" role="alert">{error}</p>}

      {assignments.length === 0 ? (
        <p className="empty-note">
          {isTeacher
            ? "Chưa giao bài nào. Mở một mô phỏng rồi bấm “Giao cho lớp”."
            : "Chưa có bài thực hành nào. Em vào lớp bằng mã để nhận bài."}
        </p>
      ) : (
        <ul className="assignment-list">
          {assignments.map((a) => {
            const p = a.myPractice;
            return (
              <li key={a.id} className="assignment-card">
                <div className="assignment-main">
                  <strong className="assignment-title">{a.title}</strong>
                  {a.instruction && <p className="assignment-instruction">{a.instruction}</p>}
                  {/* KHÔNG in `simulationId` ra màn hình: định danh kỹ thuật
                      không phải ngôn ngữ của học sinh (anti-pattern #10). */}
                  {!isTeacher && (
                    <span className="assignment-progress">
                      {/* Bài KHÔNG có timeline (vd cổng logic) thì `stepCount`
                          bằng 0 — in "bước 1/1" ở đó là bịa một trục thời gian
                          mà cơ chế không có. Nói đúng thứ biết được. */}
                      {p == null
                        ? "Chưa bắt đầu"
                        : p.completed
                          ? "Đã hoàn thành"
                          : p.stepCount > 1
                            ? `Đang làm dở — bước ${p.cursor + 1}/${p.stepCount}`
                            : "Em đã mở bài này"}
                    </span>
                  )}
                </div>
                {!isTeacher && (
                  <button type="button" className="btn-primary"
                    onClick={() => void openOne(a.id)}>
                    {p == null ? "Bắt đầu" : p.completed ? "Xem lại" : "Làm tiếp"}
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
