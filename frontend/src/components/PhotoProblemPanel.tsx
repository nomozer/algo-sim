import {
  acceptBlocker,
  describeUncertainToken,
  needsConfirmation,
  type PhotoState,
} from "./photo-problem-flow";

/**
 * XEM LẠI văn bản đọc từ ảnh — phần thân của màn "Xem lại" trong `PhotoProblemDialog`.
 *
 * PHOTO_PROBLEM_TO_SCENE_END_TO_END §3/§6. Thuần trình bày — mọi luật nằm ở `photo-problem-flow.ts`.
 *
 * Ba điều cố ý:
 * - Bản chép và công thức hiện ra dạng CHỮ (React tự thoát ký tự) — chuỗi đọc từ ảnh là dữ liệu không tin cậy,
 *   không bao giờ đi qua HTML thô.
 * - Quan sát từ hình vẽ được gắn nhãn "chỉ để tham khảo": chúng không được chép vào ô nội dung, vì hệ không suy dữ
 *   kiện hình học từ điểm ảnh. TypedFactNext + Source Gate của Hybrid vẫn là tầng kiểm dữ kiện.
 * - Mã từ chối/cờ của máy chủ KHÔNG hiện ra; chỉ thông điệp tiếng Việt đi kèm. Văn bản không bị tự sửa: người học là
 *   người duy nhất đổi nó (vd `SA ⊥ SB` không bao giờ thành `SA ⊥ (ABC)`).
 */
export interface PhotoProblemPanelProps {
  state: PhotoState;
  onEdit(text: string): void;
  onConfirm(value: boolean): void;
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

export function PhotoProblemPanel({ state, onEdit, onConfirm }: PhotoProblemPanelProps) {
  const danhGia = state.response?.assessment;
  const trich = state.response?.extraction;
  if (!danhGia || !trich) return null;
  const chan = acceptBlocker(state);

  return (
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

      <label className="photo-label" htmlFor="photo-problem-text">
        Nội dung đề đọc từ ảnh — em sửa ký hiệu, tên đỉnh, số liệu nếu đọc sai
      </label>
      <textarea
        id="photo-problem-text"
        className="photo-text"
        rows={7}
        value={state.text}
        onChange={(e) => onEdit(e.target.value)}
        spellCheck={false}
      />

      {needsConfirmation(state) && (
        <label className="photo-confirm">
          <input type="checkbox" checked={state.confirmed} onChange={(e) => onConfirm(e.target.checked)} />
          <span>Em đã đọc lại và sửa nội dung cho khớp với ảnh</span>
        </label>
      )}
      {chan && (
        <p id="photo-accept-hint" className="hint">
          {chan}
        </p>
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
      <Khoi tieuDe="Quan sát từ hình vẽ — chỉ để tham khảo, không dùng làm dữ kiện" muc={trich.diagram_observations} />

      <details className="photo-details">
        <summary>Bản chép nguyên văn từ ảnh</summary>
        <pre className="photo-verbatim">{trich.problem_text_verbatim || "(không đọc được chữ nào)"}</pre>
      </details>
    </div>
  );
}
