import { IconClose } from "./icons";
import {
  assistBlocker,
  canConfirmAssistText,
  describeUncertainToken,
  type UnifiedAssistState,
} from "./photo-problem-flow";

/**
 * Khung hỗ trợ trực tiếp bên dưới ô nhập đề (`#composer-assist-panel`):
 * 1. `needs_selection`: khi ảnh/PDF/DOCX có nhiều bài độc lập mà học sinh chưa gõ chỉ dẫn chọn bài,
 *    hiển thị các nút ứng viên để chạm chọn 1 bước (không bắt kéo khung crop).
 * 2. `needs_confirmation`: khi trích xuất ảnh có ký hiệu chưa chắc chắn hoặc vùng bị che khuất,
 *    hiển thị đúng danh sách điểm cần kiểm tra kèm ô sửa nhanh văn bản trước khi dựng hình 3D.
 */
export interface PhotoProblemPanelProps {
  state: UnifiedAssistState;
  busy?: boolean;
  onSelectCandidate(candidateId: string): void;
  onEditDraft(text: string): void;
  onToggleConfirm(value: boolean): void;
  onSubmitConfirmed(): void;
  onDismiss(): void;
}

export function PhotoProblemPanel({
  state,
  busy = false,
  onSelectCandidate,
  onEditDraft,
  onToggleConfirm,
  onSubmitConfirmed,
  onDismiss,
}: PhotoProblemPanelProps) {
  if (state.phase === "idle") return null;

  if (state.phase === "needs_selection") {
    return (
      <section
        className="composer-assist-card"
        id="composer-candidate-picker"
        aria-label="Chọn bài toán cần dựng hình"
      >
        <div className="composer-assist-head">
          <p className="composer-assist-title" role="status" aria-live="polite">
            {state.learnerMessage ?? "Chọn bài toán muốn dựng hình"}
          </p>
          <button
            type="button"
            className="context-close-icon-btn"
            onClick={onDismiss}
            disabled={busy}
            aria-label="Đóng bảng chọn bài"
          >
            <IconClose size={15} />
          </button>
        </div>

        <div className="composer-candidate-list" role="list">
          {state.candidates.map((cand) => (
            <button
              key={cand.candidate_id}
              type="button"
              className="composer-candidate-btn"
              data-candidate-id={cand.candidate_id}
              disabled={busy}
              onClick={() => onSelectCandidate(cand.candidate_id)}
            >
              {cand.preview_data_url && (
                <img
                  className="composer-candidate-thumb"
                  src={cand.preview_data_url}
                  alt={cand.label}
                />
              )}
              <span className="composer-candidate-meta">
                <span className="composer-candidate-label">{cand.label}</span>
                {cand.preview_snippet && (
                  <span className="composer-candidate-snippet">{cand.preview_snippet}</span>
                )}
              </span>
            </button>
          ))}
        </div>
      </section>
    );
  }

  const blocker = assistBlocker(state);
  const canConfirm = canConfirmAssistText(state) && !busy;

  return (
    <section
      className="composer-assist-card photo-review"
      id="composer-extraction-confirm"
      aria-label="Xác nhận nội dung trích xuất"
    >
      <div className="composer-assist-head">
        <p className="composer-assist-title" role="status" aria-live="polite">
          {state.learnerMessage ?? "Kiểm tra nhanh nội dung trước khi dựng hình"}
        </p>
        <button
          type="button"
          className="context-close-icon-btn"
          onClick={onDismiss}
          disabled={busy}
          aria-label="Đóng bảng xác nhận"
        >
          <IconClose size={15} />
        </button>
      </div>

      {state.flagMessages.length > 0 && (
        <ul className="photo-warnings">
          {state.flagMessages.map((m) => (
            <li key={m}>{m}</li>
          ))}
        </ul>
      )}

      {state.uncertainTokens.length > 0 && (
        <div className="photo-block">
          <h3 className="photo-block-title">Chỗ đọc chưa chắc chắn</h3>
          <ul className="photo-list">
            {state.uncertainTokens.map((t, idx) => (
              <li key={`${t.token}-${idx}`}>{describeUncertainToken(t)}</li>
            ))}
          </ul>
        </div>
      )}

      {state.missingRegions.length > 0 && (
        <div className="photo-block">
          <h3 className="photo-block-title">Phần nội dung nghi bị che hoặc mất</h3>
          <ul className="photo-list">
            {state.missingRegions.map((m, idx) => (
              <li key={idx}>{m}</li>
            ))}
          </ul>
        </div>
      )}

      <label className="photo-label" htmlFor="photo-problem-text">
        Nội dung đề sẽ dùng để dựng hình — em sửa lại ký hiệu nếu cần
      </label>
      <textarea
        id="photo-problem-text"
        className="photo-text"
        rows={4}
        value={state.draftText}
        onChange={(e) => onEditDraft(e.target.value)}
        disabled={busy}
        spellCheck={false}
      />

      <label className="photo-confirm">
        <input
          type="checkbox"
          id="chk-confirm-extracted-text"
          checked={state.confirmed}
          disabled={busy}
          onChange={(e) => onToggleConfirm(e.target.checked)}
        />
        <span>Em đã kiểm tra và xác nhận nội dung đề khớp với tài liệu</span>
      </label>

      {blocker && (
        <p id="photo-accept-hint" className="composer-assist-hint">
          {blocker}
        </p>
      )}

      <div className="photo-dialog-actions">
        <button type="button" className="btn-utility" onClick={onDismiss} disabled={busy}>
          Huỷ
        </button>
        <button
          type="button"
          id="btn-confirm-extracted-build"
          className="btn-primary"
          disabled={!canConfirm}
          onClick={onSubmitConfirmed}
        >
          Xác nhận & Dựng hình
        </button>
      </div>
    </section>
  );
}
