import {
  buildBlocker,
  describeUncertainToken,
  needsConfirmation,
  photoStatusText,
  type PhotoState,
} from "./photo-problem-flow";

/**
 * Khối ẢNH ĐỀ BÀI: xem trước · xoay · thay · xoá · đọc · XEM LẠI · dựng.
 *
 * PHOTO_PROBLEM_TO_SCENE_END_TO_END §3/§6. Thuần trình bày — mọi luật nằm ở
 * `photo-problem-flow.ts`, mọi lượt gọi mạng nằm ở `ProblemInput.tsx`.
 *
 * Ba điều cố ý:
 * - Bản chép và công thức hiện ra dạng CHỮ (React tự thoát ký tự) — chuỗi đọc
 *   từ ảnh là dữ liệu không tin cậy, không bao giờ đi qua HTML thô.
 * - Quan sát từ hình vẽ được gắn nhãn "chỉ để tham khảo": chúng không được
 *   chép vào ô nội dung, vì hệ không suy dữ kiện hình học từ điểm ảnh.
 * - Mã từ chối/cờ của máy chủ KHÔNG hiện ra; chỉ thông điệp tiếng Việt đi kèm.
 */
export interface PhotoProblemPanelProps {
  state: PhotoState;
  previewUrl: string | null;
  onRotate(): void;
  onReplace(): void;
  onRemove(): void;
  onRead(): void;
  onEdit(text: string): void;
  onConfirm(value: boolean): void;
  onBuild(): void;
}

function Khoi({ tieuDe, muc }: { tieuDe: string; muc: string[] }) {
  if (muc.length === 0) return null;
  return (
    <div className="photo-block">
      <h3 className="photo-block-title">{tieuDe}</h3>
      <ul className="photo-list">
        {muc.map((m, i) => (
          <li key={i}>{m}</li>
        ))}
      </ul>
    </div>
  );
}

export function PhotoProblemPanel(props: PhotoProblemPanelProps) {
  const { state, previewUrl } = props;
  if (!state.file) return null;

  const dangDung = state.phase === "building";
  const dangDoc = state.phase === "reading";
  const res = state.response;
  const danhGia = res?.assessment;
  const trich = res?.extraction;
  const chan = buildBlocker(state);
  const trangThai = photoStatusText(state);

  return (
    <section className="photo-panel" aria-label="Ảnh đề bài">
      <div className="photo-head">
        <figure className="photo-figure">
          {previewUrl && (
            <img
              className="photo-preview"
              src={previewUrl}
              alt={`Ảnh đề bài ${state.file.name}`}
              style={{ transform: `rotate(${state.rotation}deg)` }}
            />
          )}
        </figure>
        <div className="photo-actions">
          <button
            type="button"
            className="btn-utility"
            onClick={props.onRotate}
            disabled={dangDung}
            aria-label="Xoay ảnh 90 độ theo chiều kim đồng hồ"
          >
            Xoay ảnh
          </button>
          <button type="button" className="btn-utility" onClick={props.onReplace} disabled={dangDung}>
            Thay ảnh
          </button>
          <button type="button" className="btn-utility" onClick={props.onRemove} disabled={dangDung}>
            Xoá ảnh
          </button>
          {(state.phase === "selected" || state.phase === "error" || dangDoc) && (
            <button
              type="button"
              className="btn-primary"
              onClick={props.onRead}
              disabled={dangDoc}
              aria-busy={dangDoc}
            >
              {dangDoc ? "Đang đọc…" : "Đọc đề trong ảnh"}
            </button>
          )}
        </div>
      </div>

      <p className="photo-status" role="status" aria-live="polite">
        {trangThai}
      </p>

      {state.error && (
        <div className="error-banner" role="alert">
          {state.error}
        </div>
      )}

      {danhGia && trich && (
        <div className="photo-review">
          {danhGia.status === "rejected" && danhGia.learner_message && (
            <div className="photo-alert" role="alert">
              {danhGia.learner_message}
            </div>
          )}
          {danhGia.flag_messages.length > 0 && (
            <ul className="photo-warnings">
              {danhGia.flag_messages.map((m) => (
                <li key={m}>{m}</li>
              ))}
            </ul>
          )}

          <Khoi tieuDe="Chỗ đọc chưa chắc chắn" muc={trich.uncertain_tokens.map(describeUncertainToken)} />
          <Khoi tieuDe="Phần ảnh không đọc được" muc={trich.missing_regions} />
          <Khoi tieuDe="Chữ và hình vẽ mâu thuẫn" muc={trich.text_diagram_conflicts} />
          <Khoi
            tieuDe="Công thức đã chuẩn hoá"
            muc={trich.math_expressions.map((e) =>
              e.normalized === e.verbatim ? e.normalized : `${e.normalized}  (ảnh ghi: ${e.verbatim})`,
            )}
          />
          <Khoi
            tieuDe="Quan sát từ hình vẽ — chỉ để tham khảo, không dùng làm dữ kiện"
            muc={trich.diagram_observations}
          />

          <details className="photo-details">
            <summary>Bản chép nguyên văn từ ảnh</summary>
            <pre className="photo-verbatim">
              {trich.problem_text_verbatim || "(không đọc được chữ nào)"}
            </pre>
          </details>

          <label className="photo-label" htmlFor="photo-problem-text">
            Nội dung đề sẽ dùng để dựng — em sửa được
          </label>
          <textarea
            id="photo-problem-text"
            className="photo-text"
            rows={6}
            value={state.text}
            onChange={(e) => props.onEdit(e.target.value)}
            disabled={dangDung}
          />

          {needsConfirmation(state) && (
            <label className="photo-confirm">
              <input
                type="checkbox"
                checked={state.confirmed}
                onChange={(e) => props.onConfirm(e.target.checked)}
                disabled={dangDung}
              />
              <span>Em đã đọc lại và sửa nội dung cho khớp với ảnh</span>
            </label>
          )}

          <div className="photo-build">
            <button
              type="button"
              className="btn-primary"
              onClick={props.onBuild}
              disabled={chan !== null}
              aria-describedby={chan && !dangDung ? "photo-build-hint" : undefined}
            >
              {dangDung ? "Đang dựng…" : "Dựng mô phỏng"}
            </button>
            {chan && !dangDung && (
              <span id="photo-build-hint" className="hint">
                {chan}
              </span>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
