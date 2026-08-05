import type { MechanismAction, ScanInteractionModel } from "../simulations/domains/algorithm/decision";
import { IconCheck, IconPredict, IconSearch } from "./icons";

/**
 * ScanActionZone — VÙNG HÀNH ĐỘNG CỦA CỤM "QUÉT DÃY + BIẾN TÍCH LUỸ".
 *
 * Một primitive dùng chung cho `find_max` · `find_min` · `count_if` · `sum_if`:
 * bốn bài khác nhau, cùng một cơ chế, cùng một vùng tương tác. Đây chính là điều
 * wave này cần chứng minh — một thiết kế tương tác phục vụ nhiều bài toán cùng
 * cơ chế, thay vì viết riêng component cho từng đề.
 *
 * VÌ SAO LÀ HÀNH ĐỘNG CHỨ KHÔNG PHẢI CÂU HỎI CÓ/KHÔNG.
 * Không phải vì câu hỏi kém hiệu quả — cam kết trước khi thấy kết quả mới là thứ
 * tạo ra học tập, và bỏ nó đi thì mô phỏng thành đồ chơi. Ở đây cam kết vẫn còn
 * NGUYÊN, chỉ đổi hình thức: thay vì trả lời "Có/Không" về cơ chế, học sinh THỰC
 * HIỆN đúng việc mà thuật toán làm ở bước đó. Hành động đẳng cấu với cơ chế, nên
 * cái sai hiện ra ngay trên đối tượng chứ không nằm trong một câu chữ.
 *
 * RANH GIỚI:
 * - component KHÔNG biết đáp án. `ScanInteractionModel` cố ý không mang
 *   `correctActionId` lẫn `evidence` — có chúng thì đáp án nằm sẵn trong DOM và
 *   renderer bị mời tự phán xử.
 * - chấm điểm đi qua `predict.check` của module (engine tất định), giống hệt
 *   đường của PredictionBar. Không có đường chấm thứ hai.
 * - hành động sai KHÔNG đổi state canonical; nó chỉ sinh dữ liệu phản hồi.
 *
 * Màu: `--primary` là màu DUY NHẤT sơn hành động (DESIGN.md §Don't). Hai hành
 * động phân biệt bằng CHỮ và vị trí, không bằng hai màu trang trí.
 */

interface ScanActionZoneProps {
  model: ScanInteractionModel;
  /** Đã chốt một hành động chưa — khoá nút để không nộp hai lần cho cùng một bước. */
  answered: boolean;
  busy: boolean;
  onAct: (actionId: string) => void;
  /** Phản hồi sau khi chốt: do ENGINE sinh, component chỉ hiển thị. */
  feedback?: { verdict: string; message: string } | null;
}

export function ScanActionZone({
  model, answered, busy, onAct, feedback = null,
}: ScanActionZoneProps) {
  return (
    <section className="scan-action" aria-label="Thao tác với biến tích luỹ">
      <div className="scan-state">
        <span className="scan-chip is-candidate">
          <IconSearch size={13} />
          {model.candidateLabel}
          <strong>{model.candidateValue}</strong>
        </span>
        <span className="scan-expression">{model.expression}</span>
        <span className="scan-chip is-accumulator">
          {model.accumulatorLabel}
          <strong>{model.accumulatorValue}</strong>
        </span>
      </div>

      <p className="scan-instruction">Em hãy làm bước này: chọn một trong hai.</p>

      <div className="scan-actions">
        {model.actions.map((a: MechanismAction) => (
          <button
            key={a.id}
            type="button"
            className={`btn-choice scan-act is-${a.tone}`}
            disabled={busy || answered}
            onClick={() => onAct(a.id)}
          >
            {a.label}
          </button>
        ))}
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
