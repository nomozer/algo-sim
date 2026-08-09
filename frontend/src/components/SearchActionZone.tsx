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

/**
 * TIỀN ĐỀ — thuộc QUAN SÁT, không thuộc cổng Thí nghiệm (W4B-2D §29).
 *
 * "Tìm kiếm nhị phân chỉ đúng khi dãy đã sắp thứ tự" là điều kiện áp dụng của
 * thuật toán: nó đúng ở mọi bước, kể cả khi học sinh chưa làm gì. Trước wave
 * này nó sống BÊN TRONG vùng cam kết, nên khoảnh khắc cổng ẩn vùng đó đi thì
 * tiền đề biến mất theo — cổng vô tình lấy mất một dữ kiện thuần quan sát, đúng
 * thứ §29 cấm.
 *
 * Tách ra thành component riêng thay vì chép JSX sang `ui.tsx`: hai nơi dựng
 * cùng một dòng chữ là hai nơi để nó trôi khác nhau. Người gọi bảo đảm nó chỉ
 * xuất hiện MỘT lần (vùng cam kết hiện XOR dòng độc lập hiện) — bất biến "tiền
 * đề chỉ nói một lần" của W2 có test riêng.
 */
export function SearchPrecondition({ text }: { text: string }) {
  return (
    <p className="search-precondition">
      <IconInfo size={13} />
      {text}
    </p>
  );
}

/**
 * TRẠNG THÁI QUAN SÁT CỦA BƯỚC TÌM KIẾM — W4B-2V, tách khỏi vùng cam kết.
 *
 * VÌ SAO TÁCH (root cause #1 của bản audit đóng băng `fe6b0d5`):
 * component này trước đây sở hữu HAI trách nhiệm khác loại trong cùng một
 * `<section>` — trạng thái để QUAN SÁT và điều khiển để CAM KẾT — rồi
 * `AlgorithmWorkspace` gác cả cây con bằng `commitmentVisible`. Hệ quả đo được
 * ở W4B-2D: gác *nút cam kết* thì mất luôn chip vị trí/đích/vùng xét và khối
 * chi phí. Với tìm tuần tự thì chi phí CHÍNH LÀ cơ chế đáng học — chính lời
 * biện minh trong `interaction-policy.ts` nói thế — nên cổng đã lấy đi đúng thứ
 * nó viện dẫn để tự biện minh.
 *
 * Luật nay là: **cổng chỉ gác QUYỀN HÀNH ĐỘNG, không gác THÔNG TIN.**
 *
 * QUAN HỆ CŨNG VỀ ĐÂY. `expression` ("7 = 9 ?") trước sống ở dải nhân quả, mà
 * dải đó bị tắt đúng khi vùng cam kết bật — nên MỞ Thí nghiệm lại làm mất quan
 * hệ. Hai chiều của cùng một lỗi: một dữ kiện quan sát bị buộc vào công tắc của
 * cổng. Nay khối này là chủ sở hữu DUY NHẤT của quan hệ ở họ tìm kiếm, và dải
 * nhân quả không dựng cho họ này nữa ⇒ không còn hai kênh nói cùng một điều.
 */
export function SearchStateView({
  model,
  relation = null,
}: {
  model: SearchInteractionModel;
  /** Phép so sánh đang xét, từ `decisionPointOf(state).expression`. */
  relation?: string | null;
}) {
  return (
    <section className="search-observe" aria-label="Trạng thái bước tìm kiếm">
      {model.precondition && <SearchPrecondition text={model.precondition} />}

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
        {relation && <span className="scan-expression">{relation}</span>}
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
    </section>
  );
}

interface SearchActionZoneProps {
  model: SearchInteractionModel;
  answered: boolean;
  busy: boolean;
  onAct: (actionId: string) => void;
  feedback?: { verdict: string; message: string } | null;
  /** Bài chưa gác cổng thì zone tự hỏi; bài gác cổng để công cụ hỏi. */
  showPrompt?: boolean;
  /**
   * W4B-2V/C2 — HÌNH HỌC, không phải nội dung.
   * `"panel"` = thẻ cũ (nền + viền + padding, xếp dọc) cho bài CHƯA gác cổng,
   * nơi vùng cam kết là một phần thường trực của Quan sát.
   * `"tool"`  = một hàng inline không nền không viền, để nó nằm GỌN TRONG
   * `.experiment-tool` thay vì thành tấm nội dung thứ hai.
   */
  chrome?: "panel" | "tool";
}

/**
 * VÙNG CAM KẾT của bước tìm kiếm — CHỈ quyền hành động của học sinh.
 *
 * Sau W4B-2V khối này không còn mang một dữ kiện quan sát nào: trạng thái đã
 * sang `SearchStateView`. Nhờ vậy `commitmentSurfaceVisible` gác đúng thứ nó
 * được đặt tên để gác, và mở/đóng Thí nghiệm chỉ THÊM/BỚT quyền hành động chứ
 * không đổi lượng thông tin về cơ chế.
 */
export function SearchActionZone({
  model, answered, busy, onAct, feedback = null, showPrompt = true, chrome = "panel",
}: SearchActionZoneProps) {
  return (
    <section className={`action-zone search-action is-${chrome}`} aria-label="Thao tác với bước tìm kiếm">
      {/* W4B-2V/C: ở bài GÁC CỔNG, khay Thí nghiệm đã hỏi đúng câu này rồi —
          in lại ở đây là hai kênh nói một điều. Bài CHƯA gác không có khay
          nên mặc định `true` giữ nguyên hành vi cũ cho chúng. */}
      {showPrompt && <p className="scan-instruction">Em hãy quyết định bước tiếp theo.</p>}

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
