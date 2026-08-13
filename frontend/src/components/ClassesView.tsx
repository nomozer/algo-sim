import { useEffect, useState } from "react";
import { useAuthStore } from "../state/auth";
import { useClassroomStore } from "../state/classroom";
import { useAppStore } from "../state/store";

/**
 * M18 — LỚP HỌC. Một component, hai vai, vì đây là CÙNG một khái niệm nhìn từ
 * hai phía: giáo viên sở hữu lớp và phát mã, học sinh vào lớp bằng mã. Tách hai
 * file sẽ nhân đôi phần hiển thị danh sách mà không thêm gì.
 *
 * Không có sổ điểm, không có điểm danh, không có thời khoá biểu (`§0`).
 */
export function ClassesView() {
  const user = useAuthStore((s) => s.user);
  const classes = useClassroomStore((s) => s.classes);
  const busy = useClassroomStore((s) => s.busy);
  const error = useClassroomStore((s) => s.error);
  const notice = useClassroomStore((s) => s.notice);
  const loadClasses = useClassroomStore((s) => s.loadClasses);
  const createClass = useClassroomStore((s) => s.createClass);
  const joinClass = useClassroomStore((s) => s.joinClass);
  const regenerate = useClassroomStore((s) => s.regenerateCode);
  const clearNotice = useClassroomStore((s) => s.clearNotice);
  const clearError = useClassroomStore((s) => s.clearError);
  const setView = useAppStore((s) => s.setView);

  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [copied, setCopied] = useState<number | null>(null);

  useEffect(() => { void loadClasses(); }, [loadClasses]);

  if (!user) return null;
  const isTeacher = user.role === "teacher";

  return (
    <div className="page-stack">
      <header className="page-head">
        <h1 className="page-title">{isTeacher ? "Lớp học" : "Lớp của em"}</h1>
        <p className="page-sub">
          {isTeacher
            ? "Tạo lớp rồi đưa mã cho học sinh. Mã đổi được bất cứ lúc nào."
            : "Nhập mã lớp cô/thầy đưa để nhận bài thực hành."}
        </p>
      </header>

      {(notice || error) && (
        <p className={error ? "form-error" : "form-notice"} role="status"
          onAnimationEnd={() => { clearNotice(); clearError(); }}>
          {error ?? notice}
        </p>
      )}

      <section className="card page-card">
        {isTeacher ? (
          <form className="inline-form" onSubmit={async (e) => {
            e.preventDefault();
            if (!name.trim()) return;
            const created = await createClass(name.trim());
            if (created) setName("");
          }}>
            <label className="inline-field">
              <span>Tên lớp</span>
              <input value={name} onChange={(e) => setName(e.target.value)}
                placeholder="Ví dụ: 10A1 — Tin học" maxLength={160} />
            </label>
            <button className="btn-primary" disabled={busy || !name.trim()}>Tạo lớp</button>
          </form>
        ) : (
          <form className="inline-form" onSubmit={async (e) => {
            e.preventDefault();
            if (!code.trim()) return;
            if (await joinClass(code)) setCode("");
          }}>
            <label className="inline-field">
              <span>Mã lớp</span>
              <input value={code} onChange={(e) => setCode(e.target.value.toUpperCase())}
                placeholder="VD: K7M2QP" maxLength={12} className="code-input" />
            </label>
            <button className="btn-primary" disabled={busy || !code.trim()}>Tham gia lớp</button>
          </form>
        )}
      </section>

      {classes.length === 0 ? (
        <p className="empty-note">
          {isTeacher ? "Chưa có lớp nào. Tạo lớp đầu tiên ở trên." : "Em chưa vào lớp nào."}
        </p>
      ) : (
        <ul className="class-list">
          {classes.map((c) => (
            <li key={c.id} className="class-card">
              <div className="class-card-main">
                <strong className="class-card-name">{c.name}</strong>
                {isTeacher && c.joinCode && (
                  <span className="class-code" aria-label={`Mã lớp ${c.joinCode}`}>
                    <code>{c.joinCode}</code>
                    <button type="button" className="btn-utility"
                      onClick={() => {
                        void navigator.clipboard?.writeText(c.joinCode!);
                        setCopied(c.id);
                        window.setTimeout(() => setCopied(null), 1600);
                      }}>
                      {copied === c.id ? "Đã chép" : "Chép mã"}
                    </button>
                  </span>
                )}
                {isTeacher && !c.joinCode && (
                  <span className="class-code-off">Mã đã ngừng — sinh mã mới để nhận thêm học sinh.</span>
                )}
              </div>
              {isTeacher && (
                <div className="class-card-actions">
                  <button type="button" className="btn-utility"
                    onClick={() => void regenerate(c.id)}>Đổi mã</button>
                  <button type="button" className="btn-utility"
                    onClick={() => setView("observe")}>Quan sát</button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
