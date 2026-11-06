import { useEffect, useState } from "react";
import { useAuthStore } from "../state/auth";
import { deleteServerHistoryItem, historyStore, type HistoryItem } from "../state/history";
import { useAppStore } from "../state/store";
import { SessionCard } from "./SessionCard";

/**
 * Lịch sử học Axo V2.7 (Phase B & Phase C P2 — Full UI Replacement).
 *
 * Chuyển nguyên vẹn cấu trúc `#view-history`, `#history-clear-modal` và
 * hộp thoại xác nhận xóa từng mục `#history-delete-item-modal` (P2.4–P2.5):
 * - `.page-container#view-history`
 * - `.page-head-block`: tiêu đề `Lịch sử học`, nút `#btn-history-clear-init` (`Xóa tất cả`), mô tả phụ
 * - `.history-list#history-geometry-list`: danh sách `.history-card` hoặc `.lib-empty-state`
 * - Hộp thoại xác nhận xóa tất cả `#history-clear-modal`
 * - Hộp thoại xác nhận xóa 1 mục `#history-delete-item-modal` hiển thị tên bài toán sắp xóa,
 *   nút `Hủy` và `Xóa khỏi lịch sử`, khóa nút khi đang xử lý và hiển thị thông báo lỗi nếu xóa thất bại.
 */
export function HistoryView({
  initialClearModalOpen = false,
  initialDeleteItemId = null,
  initialDeleteError = null,
}: {
  initialClearModalOpen?: boolean;
  initialDeleteItemId?: string | null;
  initialDeleteError?: string | null;
} = {}) {
  const history = useAppStore((s) => s.history);
  const reopenFromHistory = useAppStore((s) => s.reopenFromHistory);
  const clearHistory = useAppStore((s) => s.clearHistory);
  const setView = useAppStore((s) => s.setView);

  const [confirmOpen, setConfirmOpen] = useState(initialClearModalOpen);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(initialDeleteItemId);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(initialDeleteError);

  const pendingDeleteItem: HistoryItem | null =
    pendingDeleteId !== null
      ? history.find((item) => item.id === pendingDeleteId) ?? null
      : null;

  useEffect(() => {
    if (!confirmOpen && !pendingDeleteItem) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && deletingId === null) {
        setConfirmOpen(false);
        setPendingDeleteId(null);
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [confirmOpen, pendingDeleteItem, deletingId]);

  const isModalVisible = confirmOpen && history.length > 0;
  const isSingleDeleteModalVisible = pendingDeleteItem !== null;

  const handleConfirmSingleDelete = async () => {
    if (!pendingDeleteItem || deletingId !== null) return;
    const targetId = pendingDeleteItem.id;
    setDeletingId(targetId);
    setDeleteError(null);

    try {
      const simulatedFailure =
        typeof window !== "undefined" &&
        Boolean((window as unknown as { __axoSimulateHistoryDeleteError?: boolean }).__axoSimulateHistoryDeleteError);
      if (simulatedFailure) {
        setDeletingId(null);
        setPendingDeleteId(null);
        setDeleteError("Không thể xóa mục lịch sử lúc này. Vui lòng thử lại.");
        return;
      }

      if (useAuthStore.getState().user !== null) {
        const ok = await deleteServerHistoryItem(targetId);
        if (!ok) {
          setDeletingId(null);
          setPendingDeleteId(null);
          setDeleteError("Không thể xóa mục lịch sử lúc này. Vui lòng thử lại.");
          return;
        }
      }

      historyStore.remove(targetId);
      useAppStore.setState({ history: historyStore.list() });
      setDeletingId(null);
      setPendingDeleteId(null);
    } catch {
      setDeletingId(null);
      setPendingDeleteId(null);
      setDeleteError("Không thể xóa mục lịch sử lúc này. Vui lòng thử lại.");
    }
  };

  return (
    <div className="page-container" id="view-history">
      <div className="page-head-block">
        <div className="page-head-row">
          <h1 className="page-main-title">Lịch sử học</h1>
          <button
            type="button"
            className="btn-clear-history-quiet"
            id="btn-history-clear-init"
            disabled={history.length === 0}
            onClick={() => {
              if (history.length > 0) setConfirmOpen(true);
            }}
          >
            Xóa tất cả
          </button>
        </div>
        <p className="page-sub-desc">
          Các bài hình học không gian đang học dở. Nhấn <strong>Tiếp tục</strong> để mở lại đúng bước dựng đã lưu.
        </p>
      </div>

      {deleteError && (
        <div
          className="history-delete-error-banner"
          id="history-delete-error-banner"
          role="alert"
        >
          <span>{deleteError}</span>
          <button
            type="button"
            className="history-error-dismiss"
            onClick={() => setDeleteError(null)}
            aria-label="Đóng thông báo lỗi"
          >
            ×
          </button>
        </div>
      )}

      <div className="history-list" id="history-geometry-list">
        {history.length === 0 ? (
          <div className="lib-empty-state" id="history-empty-state">
            <p className="lib-empty-text">Chưa có bài hình học nào trong lịch sử học tập.</p>
            <div className="lib-empty-actions">
              <button
                type="button"
                className="btn-resume-session"
                onClick={() => setView("library")}
              >
                Khám phá Thư viện mô phỏng →
              </button>
              <button
                type="button"
                className="btn-clear-history-quiet"
                onClick={() => setView("home")}
              >
                Nhập đề trên Trang chủ
              </button>
            </div>
          </div>
        ) : (
          history.map((item) => (
            <SessionCard
              key={item.id}
              item={item}
              variant="history"
              deleting={deletingId === item.id}
              onOpen={() => reopenFromHistory(item.id)}
              onRemove={() => {
                setDeleteError(null);
                setPendingDeleteId(item.id);
              }}
            />
          ))
        )}
      </div>

      <div
        className={`axo-modal-backdrop${isSingleDeleteModalVisible ? " open" : ""}`}
        id="history-delete-item-modal"
        role="dialog"
        aria-modal="true"
        aria-hidden={!isSingleDeleteModalVisible}
        aria-labelledby="history-delete-item-modal-title"
        aria-describedby="history-delete-item-modal-desc"
        onClick={(e) => {
          if (e.target === e.currentTarget && deletingId === null) {
            setPendingDeleteId(null);
          }
        }}
      >
        <div className="axo-modal-dialog">
          <div className="axo-modal-header">
            <h3 className="axo-modal-title" id="history-delete-item-modal-title">
              Xóa khỏi lịch sử học tập?
            </h3>
            <button
              type="button"
              className="axo-modal-close"
              id="btn-close-history-delete-item-modal"
              aria-label="Đóng hộp thoại"
              disabled={deletingId !== null}
              onClick={() => setPendingDeleteId(null)}
            >
              ×
            </button>
          </div>
          <div className="axo-modal-body" id="history-delete-item-modal-desc">
            Bạn có chắc chắn muốn xóa bài toán{" "}
            <strong className="history-delete-target-title">
              {pendingDeleteItem?.title ?? ""}
            </strong>{" "}
            khỏi lịch sử học tập?
          </div>
          <div className="axo-modal-footer">
            <button
              type="button"
              className="axo-modal-btn-cancel"
              id="btn-cancel-delete-item"
              disabled={deletingId !== null}
              onClick={() => setPendingDeleteId(null)}
            >
              Hủy
            </button>
            <button
              type="button"
              className="axo-modal-btn-danger"
              id="btn-confirm-delete-item"
              disabled={deletingId !== null}
              onClick={() => void handleConfirmSingleDelete()}
            >
              {deletingId !== null ? "Đang xóa..." : "Xóa khỏi lịch sử"}
            </button>
          </div>
        </div>
      </div>

      <div
        className={`axo-modal-backdrop${isModalVisible ? " open" : ""}`}
        id="history-clear-modal"
        role="dialog"
        aria-modal="true"
        aria-hidden={!isModalVisible}
        aria-labelledby="history-clear-modal-title"
        aria-describedby="history-clear-modal-desc"
        onClick={(e) => {
          if (e.target === e.currentTarget) setConfirmOpen(false);
        }}
      >
        <div className="axo-modal-dialog">
          <div className="axo-modal-header">
            <h3 className="axo-modal-title" id="history-clear-modal-title">
              Xóa toàn bộ lịch sử học?
            </h3>
            <button
              type="button"
              className="axo-modal-close"
              id="btn-close-history-clear-modal"
              aria-label="Đóng hộp thoại"
              onClick={() => setConfirmOpen(false)}
            >
              ×
            </button>
          </div>
          <div className="axo-modal-body" id="history-clear-modal-desc">
            Bạn có chắc chắn muốn xóa toàn bộ lịch sử học tập?
          </div>
          <div className="axo-modal-footer">
            <button
              type="button"
              className="axo-modal-btn-cancel"
              id="btn-history-modal-cancel"
              onClick={() => setConfirmOpen(false)}
            >
              Hủy
            </button>
            <button
              type="button"
              className="axo-modal-btn-danger"
              id="btn-history-modal-confirm"
              onClick={() => {
                clearHistory();
                setConfirmOpen(false);
              }}
            >
              Xóa lịch sử
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
