import type { ScanInteractionModel } from "../simulations/domains/algorithm/decision";
import { IconSearch } from "./icons";

/**
 * ScanActionZone — DẢI DỮ KIỆN CỦA CỤM "QUÉT DÃY + BIẾN TÍCH LUỸ".
 *
 * Một primitive dùng chung cho `find_max` · `find_min` · `count_if` · `sum_if`:
 * bốn bài khác nhau, cùng một cơ chế, cùng một dải. Đây vẫn là điều đáng chứng
 * minh — một thiết kế phục vụ nhiều bài cùng cơ chế, thay vì viết riêng
 * component cho từng đề.
 *
 * W13 — TỪ VÙNG CAM KẾT THÀNH DẢI DỮ KIỆN.
 *
 * Bản trước có hai nút ("Đặt 6 làm max mới" / "Giữ max = 9"), một dòng mời ("Em
 * hãy làm bước này: chọn một trong hai") và một dòng phán quyết từ
 * `predict.check`. Lập luận cũ ghi ngay tại đây là *"cam kết trước khi thấy kết
 * quả mới tạo ra học tập"* — và chủ đề tài đã bác: đây là hệ **mô phỏng tương
 * tác**, cam kết-rồi-được-chấm là mô hình của hệ hỏi-đáp. Học sinh tác động lên
 * chính mô hình (`explore` → `apply`) rồi đọc hệ quả tất định; hệ quả LÀ câu trả
 * lời, không cần ai phán đúng/sai.
 *
 * Thứ Ở LẠI là trạng thái cơ chế: ứng viên đang xét, phép so sánh, giá trị biến
 * tích luỹ. Nó ở lại vì `SIMULATION_SURFACE_COMPOSITION_CONTRACT §EXPLAIN` đòi
 * đóng panel Giải thích lại thì học sinh vẫn phải nhận ra *cái gì đang hoạt
 * động · vừa đổi gì*. Với cụm này, biến tích luỹ CHÍNH LÀ điểm nghẽn nhận thức
 * (README §2b #1: học sinh không giữ nổi "max đến giờ" trong đầu) — giấu nó đi
 * là bỏ mất lý do bài này được mô phỏng.
 *
 * RANH GIỚI GIỮ NGUYÊN: component KHÔNG biết đáp án. `ScanInteractionModel` cố ý
 * không mang `correctActionId` lẫn `evidence` — trước là để đáp án khỏi lọt vào
 * DOM, nay là vì không còn đáp án nào tồn tại.
 */

interface ScanActionZoneProps {
  model: ScanInteractionModel;
  /**
   * W4B-2V/C2 — HÌNH HỌC, không phải nội dung.
   * `"panel"` = thẻ (nền + viền + padding, xếp dọc).
   * `"tool"`  = một hàng inline không nền không viền.
   */
  chrome?: "panel" | "tool";
}

export function ScanActionZone({ model, chrome = "panel" }: ScanActionZoneProps) {
  return (
    <section
      className={`action-zone scan-action is-${chrome}`}
      aria-label="Trạng thái biến tích luỹ"
    >
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
    </section>
  );
}
