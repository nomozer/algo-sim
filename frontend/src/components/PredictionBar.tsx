import { useRef, useState } from "react";
import type { SimulationModule } from "../simulations/types";
import { useAppStore } from "../state/store";
import { IconCheck, IconInfo, IconPredict } from "./icons";

/**
 * PredictionBar (M8-PRE-LIP · trình bày lại theo DESIGN.md ở M9-UX6)
 * — UI DỰ ĐOÁN DÙNG CHUNG cho MỌI domain.
 *
 * Bằng chứng cho tuyên bố kiến trúc: CÙNG một capability (`predict?`) + CÙNG một
 * component phục vụ nhiều domain khác nhau (network: chọn nút — N lựa chọn;
 * algorithm: có/không — 2 lựa chọn). Nội dung 100% do `module.predict` cung cấp;
 * KHÔNG có component dự đoán riêng cho từng domain.
 *
 * Theo đúng khuôn renderer của repo: nhận `module` + `state` qua PROPS (không tự
 * thò vào store lấy state), chỉ đọc/ghi store cho phần KẾT QUẢ chấm.
 *
 * - Module KHÔNG khai `predict` → trả null → KHÔNG có affordance nào.
 * - Chấm bằng ENGINE TẤT ĐỊNH (`module.predict.check`) — KHÔNG LLM, không fetch.
 * - Kết quả là DỮ LIỆU (store.prediction), không phải hội thoại; mô phỏng
 *   canonical (`active.state`) KHÔNG hề bị đụng tới.
 *
 * TRÌNH BÀY — theo `DESIGN.md`, KHÔNG tự chế:
 * - Thẻ nổi lên bằng **nền canvas ấm** trên nền trắng, hairline, `rounded-md` —
 *   đúng khuôn `pricing-plan-card-featured`: *"Distinguished by SURFACE TINT
 *   rather than a coloured border."* KHÔNG viền màu, KHÔNG nền tím.
 * - Bảng màu sticker (tím/hồng/cam/teal) là **TRANG TRÍ**: cấm sơn nút, cấm sơn
 *   nền cấu trúc (`DESIGN.md` §Don't). Màu DUY NHẤT sơn hành động là `--primary`.
 * - Lựa chọn = `button-utility` (trắng, hairline, 8px); lựa chọn đang chọn dùng
 *   `--primary` — đây là *active signal*, đúng vai của primary.
 * - Phán quyết đúng/sai được phép dùng sticker palette vì `DESIGN.md` §Semantic
 *   nói rõ *"status is carried by the sticker palette"* — status thì được, nút thì không.
 *
 * THU GỌN MẶC ĐỊNH (UI-CLARITY W1) — vì sao:
 * - Đo được ở `main@1c9f9d5`: thanh dự đoán chiếm **19 % diện tích thẻ (161 px)**
 *   ở mọi bước có điểm quyết định, và **25 % (222 px)** sau khi trả lời. Nó là
 *   LỚP HỖ TRỢ, không phải sân khấu — nên mặc định chỉ còn một nút nhỏ.
 * - Bước không có điểm quyết định thì component trả `null`, nên khi TỰ CHẠY thẻ
 *   phình/xẹp theo từng bước (đo được 776 px → 585 px). Giữ thu gọn lúc `busy`
 *   để chiều cao không nhảy giữa lúc học sinh đang nhìn sân khấu.
 * - Không có state "đã chọn nhưng chưa nộp": mỗi đáp án LÀ hành động kiểm tra,
 *   nên bỏ hẳn nút "Kiểm tra" — bớt một bước, bớt một affordance.
 *
 * MỞ/GẬP là trạng thái TRÌNH BÀY THUẦN, sống trong component (giống `labOpen`
 * của algorithm workspace) — KHÔNG vào store, KHÔNG vào engine state.
 */

interface PredictionBarProps {
  module: SimulationModule<unknown, unknown>;
  state: unknown;
  busy: boolean;
}

export function PredictionBar({ module, state, busy }: PredictionBarProps) {
  const prediction = useAppStore((s) => s.prediction);
  const submitPrediction = useAppStore((s) => s.submitPrediction);
  /**
   * Đã mở checkpoint của BƯỚC NÀY chưa.
   *
   * Cờ này an toàn vì `SimulationWorkspace` gắn `key` theo bước hiện tại: đổi
   * bước / Đặt lại / đổi fixture đều tạo mount mới nên cờ tự về `false`. Không
   * cần effect, và component vẫn không phải biết gì về `cursor` — `state` ở đây
   * là `unknown`, đọc `.cursor` sẽ là kiến thức domain lọt vào shell dùng chung.
   */
  const [opened, setOpened] = useState(false);
  /**
   * W6 §16 — TRẢ FOCUS VỀ CHỖ CŨ KHI ĐÓNG THỬ THÁCH.
   *
   * Trước wave này Thử thách là CỬA MỘT CHIỀU: chỉ có `setOpened(true)`, không
   * có đường đóng. Người dùng bàn phím mở nhầm thì mắc kẹt trong khối cho tới
   * khi đổi bước, và không có nơi nào để trả tiêu điểm về.
   *
   * Ref trỏ vào chính nút mở, nên đóng xong tiêu điểm quay lại đúng chỗ đã bấm
   * — không nhảy về đầu trang, không biến mất.
   */
  const openBtn = useRef<HTMLButtonElement>(null);
  const closeChallenge = () => {
    setOpened(false);
    /* Đợi React vẽ lại nút mở rồi mới focus; focus vào phần tử sắp bị gỡ là
       cách chắc chắn nhất để tiêu điểm rơi về `<body>`. */
    requestAnimationFrame(() => openBtn.current?.focus());
  };

  // Mặc định an toàn — giống `timeline?` / `edit?`: không khai thì không có UI.
  if (!module.predict) return null;

  /* ĐANG TỰ CHẠY → không render gì.
     Không phải bước nào cũng có điểm quyết định, nên nếu vẫn vẽ nút thu gọn thì
     lúc tự chạy nó nhấp nháy 0 ↔ 30px theo từng bước — đúng thứ làm sân khấu
     giật mà W1 cần bỏ. Học sinh cũng không thao tác được lúc này (nút đằng nào
     cũng disabled). Dừng lại thì checkpoint hiện lại ngay. */
  if (busy) return null;

  const challenge = module.predict.challenge(state);
  if (!challenge) return null;

  const answered = prediction !== null;
  // Tự chạy: luôn thu gọn. Học sinh không kịp đọc, mà thẻ thì không được nhảy.
  const open = !busy && opened;

  if (!open) {
    return (
      <div className="predict-inline">
        <button
          type="button"
          ref={openBtn}
          className="btn-utility predict-open"
          disabled={busy}
          onClick={() => setOpened(true)}
        >
          <IconPredict size={14} />
          Dự đoán bước này
        </button>
      </div>
    );
  }

  return (
    <section className="predict-bar" aria-label="Dự đoán bước tiếp theo"
      onKeyDown={(e) => { if (e.key === "Escape") closeChallenge(); }}>
      {/* W12-A — câu hỏi · lựa chọn · nút đóng là ANH EM trong một dải ngang
          biết xuống dòng. Bọc câu hỏi + nút đóng trong một hàng riêng (bản
          trước) ép khối thử thách thành hai hàng cứng, và đo được nó cao bằng
          0,62 lần cơ chế ở `network.packet_routing`. */}
      <p className="predict-question">{challenge.question}</p>

      <div className="predict-options">
        {/* Mỗi đáp án ĐỒNG THỜI là hành động kiểm tra — không có nút nộp riêng. */}
        {challenge.options.map((o) => (
          <button
            key={o.id}
            type="button"
            className="btn-choice"
            disabled={busy || answered}
            onClick={() => submitPrediction(o.id)}
          >
            {o.label}
          </button>
        ))}
      </div>

      {/* Đóng được bằng chuột LẪN bàn phím (nút thật + phím Esc). Không dùng
          biểu tượng trần: "Đóng" đọc lên được, và nhãn nói rõ đóng cái gì. */}
      <button type="button" className="btn-utility predict-close"
        onClick={closeChallenge} aria-label="Đóng thử thách">
        Đóng
      </button>

      {prediction && (
        <p className={`predict-result is-${prediction.verdict}`} role="status">
          {prediction.verdict === "correct" && <IconCheck size={15} />}
          {/* Đoán sai = cơ hội học, KHÔNG phải lỗi hệ thống (CORRECTNESS.md):
              bóng đèn "đây là điều xảy ra" thay cho dấu × mang tông báo lỗi. */}
          {prediction.verdict === "incorrect" && <IconPredict size={15} />}
          {prediction.verdict === "unsupported_to_verify" && <IconInfo size={15} />}
          <span>{prediction.message}</span>
        </p>
      )}
    </section>
  );
}
