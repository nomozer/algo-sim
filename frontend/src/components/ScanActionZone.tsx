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
  /**
   * Phản hồi sau khi chốt: do ENGINE sinh, component chỉ hiển thị.
   *
   * `answerId` là LỰA CHỌN CỦA CHÍNH HỌC SINH, không phải đáp án — nó vào đây
   * để vùng hành động nói lại được "em vừa chọn cái nào". `expectedId` của
   * `PredictionResult` cố ý KHÔNG có mặt trong kiểu này: đọc được nó ở renderer
   * là mời renderer tự phán xử, và nó sẽ lọt vào DOM.
   */
  feedback?: { verdict: string; message: string; answerId?: string } | null;
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

      {/* SAU KHI CHỐT, HỌC SINH PHẢI CÒN THẤY MÌNH ĐÃ CHỌN GÌ.
          Đo trong Chrome (W3B-1 baseline, 4/4 target): chốt xong thì cả hai nút
          chỉ khác trạng thái trước ở chỗ `disabled` — không viền, không chữ,
          không thuộc tính nào phân biệt. Phản hồi thì nói "Chưa đúng…" mà không
          nói chưa đúng CÁI GÌ, nên nửa vòng lặp học tập bị mất.
          Dấu hiệu chính là CHỮ ("em đã chọn"); viền và độ đậm chỉ là lớp thứ
          hai — màu không bao giờ là tín hiệu duy nhất (global.css). */}
      <div className="scan-actions">
        {model.actions.map((a: MechanismAction) => {
          const chosen = answered && feedback?.answerId === a.id;
          const state = answered ? (chosen ? " is-chosen" : " is-notchosen") : "";
          return (
            <button
              key={a.id}
              type="button"
              className={`btn-choice scan-act is-${a.tone}${state}`}
              disabled={busy || answered}
              // Chỉ khẳng định khi đã có cam kết: trước đó hai nút chưa mang
              // trạng thái nào, nói "không được nhấn" là kể sai.
              aria-pressed={answered ? chosen : undefined}
              data-chosen={answered ? String(chosen) : undefined}
              onClick={() => onAct(a.id)}
            >
              {a.label}
              {/* Khoảng trắng THẬT, không phải `margin` — đo trong Chrome thấy
                  `innerText` ra "Giữ max = 9em đã chọn": mắt thấy cách nhau vì
                  margin, còn trình đọc màn hình đọc dính liền. */}
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
