import { useAppStore } from "../state/store";
import { SessionCard } from "./SessionCard";

/**
 * LỊCH SỬ (M9-UX1) — toàn bộ mô phỏng đã học, sống trong localStorage.
 * Mở lại = envelope đã validate + engine tất định → 0 gọi AI.
 * Đơn giản có chủ đích: KHÔNG thư mục/tag/tìm kiếm/sync/chia sẻ (ngoài phạm vi).
 *
 * M9-UX4: dùng CHUNG `SessionCard` với "Tiếp tục học" ở Home — trước đây là một
 * hàng rộng gần hết màn hình, và nó IN THẲNG `item.simulationId`
 * (`algorithm.bubble_sort`) ra cho học sinh. Chuỗi kĩ thuật không bao giờ được
 * lên UI; nhãn tiếng Việt + tiến độ mới là thứ học sinh cần.
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
            <SessionCard
              key={item.id}
              item={item}
              onOpen={() => reopenFromHistory(item.id)}
              onRemove={() => removeHistoryItem(item.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
