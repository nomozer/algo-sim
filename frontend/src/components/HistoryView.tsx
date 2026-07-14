import { DOMAIN_LABEL } from "../data/offline-catalog";
import { useAppStore } from "../state/store";
import { formatRelativeTime } from "./HomeView";

/**
 * LỊCH SỬ (M9-UX1) — toàn bộ mô phỏng đã học, sống trong localStorage.
 * Mở lại = envelope đã validate + engine tất định → 0 gọi AI.
 * Đơn giản có chủ đích: KHÔNG thư mục/tag/tìm kiếm/sync/chia sẻ (ngoài phạm vi).
 */
export function HistoryView() {
  const history = useAppStore((s) => s.history);
  const reopenFromHistory = useAppStore((s) => s.reopenFromHistory);
  const removeHistoryItem = useAppStore((s) => s.removeHistoryItem);
  const clearHistory = useAppStore((s) => s.clearHistory);
  const goHome = useAppStore((s) => s.goHome);

  return (
    <div className="history-view">
      <div className="history-head">
        <h1 className="home-section-title" style={{ fontSize: 26 }}>
          Lịch sử học
        </h1>
        <span style={{ marginLeft: "auto", display: "flex", gap: "var(--sp-xs)" }}>
          {history.length > 0 && (
            <button
              className="btn-utility"
              onClick={() => {
                if (window.confirm("Xóa toàn bộ lịch sử học? Hành động này không hoàn tác được.")) {
                  clearHistory();
                }
              }}
            >
              Xóa tất cả
            </button>
          )}
          <button className="btn-utility" onClick={goHome}>
            ← Trang chủ
          </button>
        </span>
      </div>

      {history.length === 0 ? (
        <div className="empty-state">
          <p>
            Chưa có mô phỏng nào trong lịch sử.
            <br />
            Phân tích một đề bài hoặc chạy một bài mẫu — AlgoSim sẽ lưu lại để em mở lại
            bất cứ lúc nào mà không cần gọi AI.
          </p>
        </div>
      ) : (
        <div className="history-list">
          {history.map((item) => (
            <div key={item.id} className="history-row">
              <div className="history-row-info">
                <strong>{item.title}</strong>
                <span className="hint">
                  {DOMAIN_LABEL[item.domain as keyof typeof DOMAIN_LABEL] ?? item.domain} ·{" "}
                  {item.simulationId}
                  {item.lastCursor !== null && item.lastCursor > 0 && (
                    <> · đang ở bước {item.lastCursor + 1}</>
                  )}
                </span>
                <span className="hint">Xem lần cuối: {formatRelativeTime(item.lastViewedAt)}</span>
              </div>
              <span className="history-row-actions">
                <button
                  className="btn-primary"
                  onClick={() => reopenFromHistory(item.id)}
                  title="Mở lại — không gọi AI"
                >
                  Mở lại
                </button>
                <button
                  className="btn-utility"
                  onClick={() => removeHistoryItem(item.id)}
                  title="Xóa khỏi lịch sử"
                >
                  Xóa
                </button>
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
