import type { SearchInteractionModel } from "../simulations/domains/algorithm/decision";
import { IconInfo, IconSearch } from "./icons";

/**
 * SearchStateView — DẢI DỮ KIỆN CỦA CỤM TÌM KIẾM (`linear_search`, `binary_search`).
 *
 * W13 — FILE NÀY TÁCH RA TỪ `SearchActionZone.tsx`, file đó đã bị XOÁ.
 *
 * Lý do xoá đáng ghi lại: `SearchActionZone` chở *quyền hành động được chấm*, và
 * W4B-2V đã dời toàn bộ dữ kiện quan sát của họ tìm kiếm sang đây. Nên khi W13
 * gỡ hình thức hỏi-đáp, phần còn lại của nó RỖNG — không phải rút gọn được, mà
 * là không còn lý do tồn tại. Hai component nằm chung một file chỉ vì lịch sử;
 * tách ra là trả chúng về đúng vòng đời.
 *
 * ── TIỀN ĐỀ THUỘC QUAN SÁT, KHÔNG THUỘC CỔNG (W4B-2D §29) ──────────────────
 *
 * "Tìm kiếm nhị phân chỉ đúng khi dãy đã sắp thứ tự" là điều kiện áp dụng của
 * thuật toán: nó đúng ở mọi bước, kể cả khi học sinh chưa làm gì.
 *
 * ── VÌ SAO TRẠNG THÁI PHẢI TÁCH KHỎI HÀNH ĐỘNG (root cause #1, audit `fe6b0d5`) ──
 *
 * Bản cũ gộp HAI trách nhiệm khác loại trong một `<section>` — trạng thái để
 * QUAN SÁT và điều khiển để CAM KẾT — rồi shell gác cả cây con bằng
 * `commitmentVisible`. Hệ quả đo được ở W4B-2D: gác *nút cam kết* thì mất luôn
 * chip vị trí/đích/vùng xét và khối chi phí. Với tìm tuần tự thì chi phí CHÍNH
 * LÀ cơ chế đáng học, nên cổng đã lấy đi đúng thứ nó viện dẫn để tự biện minh.
 *
 * Luật rút ra: **cổng chỉ gác QUYỀN HÀNH ĐỘNG, không gác THÔNG TIN.** W13 gỡ nốt
 * cổng, nên nay dữ kiện là thường trực — nhưng luật vẫn đáng nhớ, vì lần sau ai
 * đó thêm một chế độ mới sẽ bị cám dỗ gác nhầm lần nữa.
 *
 * QUAN HỆ (`7 = 9 ?`) cũng thuộc về đây: trước nó sống ở dải nhân quả, mà dải đó
 * tắt đúng khi vùng cam kết bật — nên MỞ Thí nghiệm lại làm mất quan hệ. Nay
 * khối này là chủ sở hữu DUY NHẤT của quan hệ ở họ tìm kiếm, và dải nhân quả
 * không dựng cho họ này ⇒ không bao giờ hai kênh nói cùng một điều.
 */

export function SearchPrecondition({ text }: { text: string }) {
  return (
    <p className="search-precondition">
      <IconInfo size={13} />
      {text}
    </p>
  );
}

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
