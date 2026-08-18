import type {
  SortFact,
  SortInteractionModel,
} from "../simulations/domains/algorithm/decision";
import { IconSearch } from "./icons";

/**
 * SortActionZone — DẢI DỮ KIỆN CƠ CHẾ CỦA CỤM SẮP XẾP (W3B §9, rút gọn ở W13).
 *
 * Ba bài — nổi bọt, chọn, chèn — cùng một khuôn trình bày nhưng ba cơ chế khác
 * nhau (`kind`), nên chữ nói bằng ngôn ngữ của từng cơ chế.
 *
 * W13 — TỪ VÙNG CAM KẾT THÀNH DẢI DỮ KIỆN.
 *
 * Trước đây khối này còn chở hai nút ("Đổi chỗ hai phần tử này" / "Giữ nguyên
 * thứ tự"), một dòng mời ("Em hãy làm bước này: chọn một trong hai") và một dòng
 * phán quyết đúng/sai từ `predict.check`. Toàn bộ phần ấy đã gỡ: đây là hệ mô
 * phỏng tương tác, học sinh tác động lên mô hình rồi đọc hệ quả tất định, chứ
 * không trả lời câu hỏi để lấy điểm.
 *
 * Thứ Ở LẠI là trạng thái cơ chế — engine đang xét cặp nào, giá trị bao nhiêu,
 * cần sắp theo chiều nào. Nó ở lại vì `SIMULATION_SURFACE_COMPOSITION_CONTRACT
 * §EXPLAIN` đòi: đóng panel Giải thích lại, học sinh vẫn phải nhận ra *cái gì
 * đang hoạt động · vừa đổi gì*. Giấu nó vào panel là bắt học sinh xem một hoạt
 * hình mà không giải thích nổi thứ tự các bước.
 *
 * RANH GIỚI GIỮ NGUYÊN: `SortInteractionModel` cố ý KHÔNG mang đáp án hay kết
 * quả cuối — trước là để đáp án khỏi nằm sẵn trong DOM, nay là vì không còn đáp
 * án nào tồn tại. Component này chỉ ĐỌC model do `decision.ts` dựng từ trace.
 */

interface SortActionZoneProps {
  model: SortInteractionModel;
  /**
   * W4B-2V/C2 — HÌNH HỌC, không phải nội dung.
   * `"panel"` = thẻ (nền + viền + padding, xếp dọc).
   * `"tool"`  = một hàng inline không nền không viền.
   *
   * W13 giữ tham số này dù mọi chỗ gọi đang truyền `"panel"`: nó là trục HÌNH
   * HỌC dùng chung của ba dải, và bố cục hẹp sẽ cần `"tool"` trở lại.
   */
  chrome?: "panel" | "tool";
}

export function SortActionZone({ model, chrome = "panel" }: SortActionZoneProps) {
  return (
    <section className={`action-zone sort-action is-${chrome}`} aria-label="Trạng thái sắp xếp">
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
    </section>
  );
}
