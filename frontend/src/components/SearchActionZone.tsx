import type {
  SearchAction,
  SearchInteractionModel,
} from "../simulations/domains/algorithm/decision";
import { IconCheck, IconInfo, IconPredict, IconSearch } from "./icons";

/**
 * SearchActionZone — VÙNG HÀNH ĐỘNG CỦA CỤM TÌM KIẾM (INTERACTION-FAMILY W2).
 *
 * Một primitive cho `linear_search` và `binary_search`. Hai bài cùng khuôn "xét
 * một phần tử → so sánh → chọn bước đi tiếp", nhưng cơ chế ẩn khác nhau nên
 * model cấp cho chúng hai bộ dữ liệu khác nhau:
 *
 * - tuần tự: 2 hành động + KHỐI CHI PHÍ (đã so sánh / còn lại / xấu nhất);
 * - nhị phân: 2–3 hành động không gian + VÙNG XÉT + TIỀN ĐỀ dãy đã sắp.
 *
 * Component KHÔNG chứa phép so sánh số học, KHÔNG tính lại `candidate === target`,
 * KHÔNG tự quyết định trái/phải. Nó nhận model, render, và phát `id` hành động —
 * việc chấm do `predict.check` của engine tất định làm, y như PredictionBar và
 * ScanActionZone. Không có đường chấm điểm thứ hai.
 *
 * Chi phí hiển thị như THÔNG TIN TIẾN TRÌNH, không phải câu hỏi: mục tiêu là học
 * sinh thấy con số đổi theo từng bước mình đi, chứ không phải trả lời thêm một
 * câu trắc nghiệm nữa.
 */

interface SearchActionZoneProps {
  model: SearchInteractionModel;
  answered: boolean;
  busy: boolean;
  onAct: (actionId: string) => void;
  feedback?: { verdict: string; message: string } | null;
}

export function SearchActionZone({
  model, answered, busy, onAct, feedback = null,
}: SearchActionZoneProps) {
  return (
    <section className="action-zone search-action" aria-label="Thao tác với bước tìm kiếm">
      {model.precondition && (
        <p className="search-precondition">
          <IconInfo size={13} />
          {model.precondition}
        </p>
      )}

      <div className="search-state">
        <span className="scan-chip is-candidate">
          <IconSearch size={13} />
          {model.activeRange ? "Phần tử giữa" : `Phần tử vị trí ${model.currentIndex + 1}`}
          <strong>{model.currentValue}</strong>
        </span>
        <span className="scan-chip">
          cần tìm
          <strong>{model.targetValue}</strong>
        </span>
        {model.activeRange && (
          <span className="scan-chip">
            vùng xét
            <strong>
              {model.activeRange.left + 1}–{model.activeRange.right + 1}
            </strong>
          </span>
        )}
      </div>

      {/* CHI PHÍ — dẫn xuất từ `vars.i` và độ dài dãy, không phải chạy lại thuật
          toán. Đây là thứ đáng học ở tìm kiếm tuần tự (CSTA 3B-AP-11: đánh giá
          thuật toán theo efficiency). */}
      {model.cost && (
        <div className="search-cost">
          <span>
            Đã so sánh <strong>{model.cost.comparisonsDone}</strong>
          </span>
          <span>
            Chưa xét <strong>{model.cost.remainingCandidates}</strong>
          </span>
          <span className="search-cost-worst">
            Xấu nhất <strong>{model.cost.worstCaseComparisons}</strong>
          </span>
        </div>
      )}

      <p className="scan-instruction">Em hãy quyết định bước tiếp theo.</p>

      <div className="search-actions">
        {model.actions.map((a: SearchAction) => (
          <button
            key={a.id}
            type="button"
            className={`btn-choice search-act is-${a.visualRole}`}
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
          {/* Chọn sai = cơ hội học (CORRECTNESS.md §4), không phải lỗi hệ thống. */}
          {feedback.verdict !== "correct" && <IconPredict size={15} />}
          <span>{feedback.message}</span>
        </p>
      )}
    </section>
  );
}
