import type {
  MechanismAction,
  SortFact,
  SortInteractionModel,
} from "../simulations/domains/algorithm/decision";
import { IconCheck, IconPredict, IconSearch } from "./icons";

/**
 * SortActionZone — VÙNG HÀNH ĐỘNG CỦA CỤM SẮP XẾP (W3B §9).
 *
 * Cụm thứ ba, và là cụm CUỐI trong phạm vi đề tài. Ba bài — nổi bọt, chọn,
 * chèn — cùng một khuôn trình bày nhưng ba cơ chế khác nhau (`kind`), nên nhãn
 * hành động nói bằng ngôn ngữ của từng cơ chế chứ không phải "Có/Không".
 *
 * VÌ SAO CAM KẾT LÀ NÚT CHỨ KHÔNG PHẢI KÉO:
 * kéo cột đã có nghĩa từ trước — THÍ NGHIỆM what-if, fork sang nhánh. Nếu cam
 * kết cũng là kéo thì cùng một cử chỉ, trên cùng hai cột, ở cùng một bước lại
 * mang hai nghĩa và cho hai kết cục khác nhau (một cái được chấm, một cái đẻ
 * nhánh). Tách bằng hình thức: nút = làm đúng bước thuật toán; kéo = thử xem
 * "nếu khác đi thì sao". Trong lúc chưa cam kết, kéo bị khoá (`ui.tsx`) để hai
 * nghĩa không tranh nhau.
 *
 * RANH GIỚI — giống hệt `ScanActionZone`/`SearchActionZone`:
 * - `SortInteractionModel` cố ý KHÔNG mang `correctActionId`/`evidence`/kết quả
 *   cuối; có chúng thì đáp án nằm sẵn trong DOM trước khi học sinh hành động;
 * - chấm đi qua `predict.check` của module — không có đường chấm thứ hai;
 * - hành động sai KHÔNG đổi state canonical, chỉ sinh dữ liệu phản hồi.
 */

interface SortActionZoneProps {
  model: SortInteractionModel;
  /** Đã chốt một hành động chưa — khoá nút để không nộp hai lần cho một bước. */
  answered: boolean;
  busy: boolean;
  onAct: (actionId: string) => void;
  /**
   * Phản hồi sau khi chốt: do ENGINE sinh, component chỉ hiển thị. `answerId`
   * là lựa chọn CỦA HỌC SINH, không phải đáp án — `expectedId` cố ý vắng mặt
   * khỏi kiểu này (xem `ScanActionZone`).
   */
  feedback?: { verdict: string; message: string; answerId?: string } | null;
}

export function SortActionZone({
  model, answered, busy, onAct, feedback = null,
}: SortActionZoneProps) {
  return (
    <section className="action-zone sort-action" aria-label="Thao tác sắp xếp">
      <p className="sort-title">
        <IconSearch size={13} />
        {model.title}
      </p>

      <div className="sort-state">
        {model.facts.map((f: SortFact) => (
          <span key={`${f.label}-${f.value}`} className="sort-chip">
            {f.label}
            <strong>{f.value}</strong>
          </span>
        ))}
        <span className="sort-expression">{model.expression}</span>
      </div>

      <p className="sort-instruction">Em hãy làm bước này: chọn một trong hai.</p>

      <div className="sort-actions">
        {model.actions.map((a: MechanismAction) => {
          const chosen = answered && feedback?.answerId === a.id;
          const state = answered ? (chosen ? " is-chosen" : " is-notchosen") : "";
          return (
            <button
              key={a.id}
              type="button"
              className={`btn-choice sort-act is-${a.tone}${state}`}
              disabled={busy || answered}
              aria-pressed={answered ? chosen : undefined}
              data-chosen={answered ? String(chosen) : undefined}
              onClick={() => onAct(a.id)}
            >
              {a.label}
              {chosen && <> <span className="scan-act-mark">em đã chọn</span></>}
            </button>
          );
        })}
      </div>

      {feedback && (
        <p className={`predict-result is-${feedback.verdict}`} role="status">
          {feedback.verdict === "correct" && <IconCheck size={15} />}
          {/* Làm sai = cơ hội học, không phải lỗi hệ thống (CORRECTNESS.md §4). */}
          {feedback.verdict !== "correct" && <IconPredict size={15} />}
          <span>{feedback.message}</span>
        </p>
      )}
    </section>
  );
}
