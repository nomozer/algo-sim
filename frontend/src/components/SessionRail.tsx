import { useAppStore } from "../state/store";
import { getSimulation } from "../simulations/registry";

/**
 * W4B-2Z §29 — THANH PHIÊN ĐANG MỞ.
 *
 * Lý do tồn tại là SỰ LIÊN TỤC CỦA MÔ PHỎNG, không phải "sản phẩm nào cũng có
 * thanh bên". Học sinh đang dở bài A, muốn xem thử bài B, rồi quay lại A đúng
 * chỗ cũ — không có chỗ nào để quay lại thì phiên mở ra cũng vô nghĩa.
 *
 * Phạm vi CỐ Ý HẸP: mở phiên mới · liệt kê phiên · chuyển · đóng. KHÔNG lớp
 * học, KHÔNG bài tập, KHÔNG điểm số, KHÔNG cây môn học — AlgoSim là hệ mô
 * phỏng, không phải LMS.
 *
 * Thanh này KHÔNG dựng khi chỉ có một phiên: một danh sách một dòng không giúp
 * ai chuyển đi đâu, nó chỉ ăn bề ngang của sân khấu — mà sân khấu là thứ phải
 * chiếm ưu thế thị giác.
 */
export function SessionRail() {
  const sessions = useAppStore((s) => s.sessions);
  const activeSessionId = useAppStore((s) => s.activeSessionId);
  const switchSession = useAppStore((s) => s.switchSession);
  const closeSession = useAppStore((s) => s.closeSession);
  const newSession = useAppStore((s) => s.newSession);

  if (sessions.length < 2) return null;

  return (
    <nav className="session-rail" aria-label="Mô phỏng đang mở">
      <div className="session-rail-head">
        <span className="session-rail-title">Đang mở</span>
        <button type="button" className="session-new" onClick={newSession}>
          + Mô phỏng mới
        </button>
      </div>
      <ul className="session-list">
        {sessions.map((sn) => {
          const isActive = sn.id === activeSessionId;
          /* Nhãn miền lấy từ module đã đăng ký, KHÔNG từ chuỗi trong tiêu đề —
             định danh kĩ thuật (`algorithm.bubble_sort`) không được lọt lên UI. */
          const mod = getSimulation(sn.active.moduleId);
          return (
            <li key={sn.id} className={`session-item${isActive ? " is-active" : ""}`}>
              <button
                type="button"
                className="session-open"
                onClick={() => switchSession(sn.id)}
                aria-current={isActive ? "true" : undefined}
              >
                <span className="session-name">{sn.title}</span>
                <span className="session-kind">{mod?.title ?? ""}</span>
              </button>
              <button
                type="button"
                className="session-close"
                onClick={() => closeSession(sn.id)}
                aria-label={`Đóng ${sn.title}`}
                title="Đóng mô phỏng này"
              >
                ×
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
