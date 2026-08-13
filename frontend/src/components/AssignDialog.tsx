import { useEffect, useState } from "react";
import { useAuthStore } from "../state/auth";
import { useClassroomStore } from "../state/classroom";
import { useAppStore } from "../state/store";

/**
 * M18 — "GIAO CHO LỚP": từ một mô phỏng ĐANG MỞ tới một bài thực hành.
 *
 * ─── VÌ SAO GIAO TỪ TRONG MÔ PHỎNG ────────────────────────────────────────
 *
 * Giáo viên phải XEM được thứ mình giao trước khi giao. Một trang "tạo bài
 * thực hành" riêng, nơi phải chọn mô phỏng từ một danh sách tên, sẽ tách quyết
 * định khỏi thứ nó nói về — và đó là cách người ta giao nhầm.
 *
 * ─── THỨ ĐƯỢC GỬI ĐI ──────────────────────────────────────────────────────
 *
 * ENVELOPE của phiên đang mở, tức bản ĐÃ QUA validate. Máy chủ vẫn kiểm lại
 * lần nữa qua `SimSpec.validate` (bất biến #28) — không phải vì không tin
 * client, mà vì client KHÔNG PHẢI nơi luật sống.
 *
 * Lời dặn là CHỮ. Nó hiện cạnh mô phỏng cho học sinh đọc và không bao giờ được
 * đọc như tham số.
 */
export function AssignDialog() {
  const user = useAuthStore((s) => s.user);
  const active = useAppStore((s) => s.active);
  const classes = useClassroomStore((s) => s.classes);
  const loadClasses = useClassroomStore((s) => s.loadClasses);
  const assign = useClassroomStore((s) => s.assign);
  const busy = useClassroomStore((s) => s.busy);
  const error = useClassroomStore((s) => s.error);

  const [open, setOpen] = useState(false);
  const [classId, setClassId] = useState<number | null>(null);
  const [title, setTitle] = useState("");
  const [instruction, setInstruction] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => { if (user?.role === "teacher") void loadClasses(); }, [user, loadClasses]);
  useEffect(() => {
    if (classId == null && classes.length) setClassId(classes[0].id);
  }, [classes, classId]);
  useEffect(() => {
    /* Tiêu đề gợi ý = tiêu đề đề bài. Giáo viên sửa được, nhưng không phải gõ
       lại từ đầu thứ đang hiện ngay trên đầu màn hình. */
    if (open && !title && active) setTitle(String(active.envelope?.title ?? ""));
  }, [open, title, active]);

  if (!user || user.role !== "teacher" || !active) return null;

  return (
    <>
      <button type="button" className="btn-utility" onClick={() => { setOpen(true); setDone(false); }}>
        Giao cho lớp
      </button>

      {open && (
        <div className="auth-overlay" role="dialog" aria-modal="true" aria-label="Giao bài cho lớp"
          onClick={(e) => { if (e.target === e.currentTarget) setOpen(false); }}>
          <div className="auth-card">
            <div className="auth-head">
              <h2 className="auth-title">Giao cho lớp</h2>
              <button type="button" className="auth-close" onClick={() => setOpen(false)}
                aria-label="Đóng">×</button>
            </div>

            {classes.length === 0 ? (
              <p className="empty-note" style={{ marginTop: "var(--sp-md)" }}>
                Thầy/cô chưa có lớp nào. Tạo lớp ở mục “Lớp học” trước đã.
              </p>
            ) : done ? (
              <p className="form-notice" style={{ marginTop: "var(--sp-md)" }} role="status">
                Đã giao. Học sinh trong lớp sẽ thấy bài này ở mục “Bài thực hành”.
              </p>
            ) : (
              <form className="auth-form" onSubmit={async (e) => {
                e.preventDefault();
                if (classId == null || !active.envelope) return;
                const ok = await assign({
                  classroomId: classId, title: title.trim(),
                  instruction: instruction.trim(), envelope: active.envelope,
                });
                if (ok) setDone(true);
              }}>
                <label className="auth-field">
                  <span>Lớp</span>
                  <select value={classId ?? ""} onChange={(e) => setClassId(Number(e.target.value))}>
                    {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </label>
                <label className="auth-field">
                  <span>Tên bài thực hành</span>
                  <input value={title} onChange={(e) => setTitle(e.target.value)}
                    required maxLength={200} />
                </label>
                <label className="auth-field">
                  <span>Lời dặn cho học sinh</span>
                  <textarea value={instruction} onChange={(e) => setInstruction(e.target.value)}
                    rows={3} maxLength={4000}
                    placeholder="Ví dụ: Bật/tắt hai đầu vào rồi ghi lại khi nào đầu ra bằng 1." />
                </label>
                {error && <p className="auth-error" role="alert">{error}</p>}
                <button type="submit" className="btn-primary auth-submit"
                  disabled={busy || !title.trim()}>
                  {busy ? "Đang giao…" : "Giao bài"}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
}
