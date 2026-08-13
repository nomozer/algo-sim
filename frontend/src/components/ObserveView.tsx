import { useEffect, useState } from "react";
import { useAuthStore } from "../state/auth";
import { useClassroomStore, type ObserveRow } from "../state/classroom";

/**
 * M18 — QUAN SÁT LỚP.
 *
 * ─── VÌ SAO KHÔNG PHẢI LUỒNG MÀN HÌNH (`§21`) ─────────────────────────────
 *
 * Chiếu màn hình học sinh vừa nặng, vừa lộ nhiều thứ không liên quan đến giờ
 * học, vừa buộc phải dựng một hạ tầng truyền hình ảnh mà kiến trúc này không
 * có. Thứ giáo viên thật sự cần trả lời được là "em nào đang ở đâu, em nào
 * chưa bắt đầu" — và đó là TRẠNG THÁI CÓ CẤU TRÚC, vài chục byte một dòng.
 *
 * ─── VÌ SAO HỎI LẠI THEO CHU KỲ, KHÔNG PHẢI WEBSOCKET (`§22`) ─────────────
 *
 * Repo chưa có websocket/SSE. Dựng một hạ tầng truyền tin thời gian thực cho
 * một bảng đổi vài giây một lần là thêm bộ phận không đổi lấy gì. Hỏi lại mỗi
 * 5 giây là đủ tươi cho việc đứng lớp và không cần gì mới.
 *
 * KHÔNG cột nào ở đây nói học sinh ĐÚNG hay SAI (bất biến #27).
 */

const POLL_MS = 5000;

function statusLabel(r: ObserveRow): string {
  if (r.status === "not_started") return "Chưa bắt đầu";
  if (r.status === "completed") return "Đã xong";
  return "Đang thực hành";
}

/** Câu mô tả vị trí — dẫn xuất từ CHÍNH khái niệm sản phẩm đang dùng. */
function whereLabel(r: ObserveRow): string {
  if (r.status === "not_started") return "—";
  const bits: string[] = [];
  if (r.stepCount && r.stepCount > 1 && r.cursor != null) {
    bits.push(`bước ${r.cursor + 1}/${r.stepCount}`);
  }
  if (r.exploreOpen) bits.push("Khám phá");
  if (r.challengeOpen) bits.push("Thử thách");
  if (r.commitmentCount) bits.push(`${r.commitmentCount} lần cam kết`);
  if (!bits.length && r.actionCount) bits.push(`${r.actionCount} thao tác`);
  return bits.length ? bits.join(" · ") : "vừa mở bài";
}

export function ObserveView() {
  const user = useAuthStore((s) => s.user);
  const classes = useClassroomStore((s) => s.classes);
  const loadClasses = useClassroomStore((s) => s.loadClasses);
  const observe = useClassroomStore((s) => s.observe);
  const loadObserve = useClassroomStore((s) => s.loadObserve);
  const [classId, setClassId] = useState<number | null>(null);
  const [live, setLive] = useState(true);

  useEffect(() => { void loadClasses(); }, [loadClasses]);
  useEffect(() => {
    if (classId == null && classes.length) setClassId(classes[0].id);
  }, [classes, classId]);

  useEffect(() => {
    if (classId == null) return;
    void loadObserve(classId);
    if (!live) return;
    const t = window.setInterval(() => void loadObserve(classId), POLL_MS);
    /* Dọn interval khi đổi lớp/rời trang: không dọn thì mỗi lần đổi lớp lại
       thêm một vòng hỏi, và sau vài phút giáo viên có năm vòng chạy song song. */
    return () => window.clearInterval(t);
  }, [classId, live, loadObserve]);

  if (!user || user.role !== "teacher") return null;

  const rows = observe?.rows ?? [];
  return (
    <div className="page-stack">
      <header className="page-head">
        <h1 className="page-title">Quan sát lớp</h1>
        <p className="page-sub">
          Trạng thái thực hành của học sinh, tự cập nhật. Bảng này KHÔNG chấm đúng/sai —
          phần đó do chính mô phỏng quyết định khi em ấy làm.
        </p>
      </header>

      <div className="observe-bar">
        <label className="inline-field">
          <span>Lớp</span>
          <select value={classId ?? ""} onChange={(e) => setClassId(Number(e.target.value))}>
            {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </label>
        <button type="button" className={`btn-utility${live ? " is-active" : ""}`}
          onClick={() => setLive((v) => !v)}
          aria-pressed={live}>
          {live ? "Đang theo dõi" : "Đã tạm dừng"}
        </button>
        {observe && (
          <span className="observe-stamp">
            Cập nhật lúc {new Date(observe.observedAt).toLocaleTimeString("vi-VN")}
          </span>
        )}
      </div>

      {classes.length === 0 ? (
        <p className="empty-note">Chưa có lớp nào để quan sát.</p>
      ) : rows.length === 0 ? (
        <p className="empty-note">
          Lớp này chưa có học sinh hoặc chưa có bài thực hành nào được giao.
        </p>
      ) : (
        <div className="table-scroll">
          <table className="data-table observe-table">
            <thead>
              <tr>
                <th>Học sinh</th>
                <th>Bài thực hành</th>
                <th>Trạng thái</th>
                <th>Đang ở đâu</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={`${r.studentId}-${r.assignmentId}`}
                  className={r.status === "not_started" ? "is-idle-row" : undefined}>
                  <td>{r.studentName}</td>
                  <td>{r.assignmentTitle}</td>
                  <td>
                    <span className={`observe-status is-${r.status}`}>{statusLabel(r)}</span>
                  </td>
                  <td>{whereLabel(r)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
