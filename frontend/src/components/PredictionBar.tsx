import { useState } from "react";
import type { SimulationModule } from "../simulations/types";
import { useAppStore } from "../state/store";
import { IconCheck, IconCross, IconInfo, IconPredict } from "./icons";

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
 */

interface PredictionBarProps {
  module: SimulationModule<unknown, unknown>;
  state: unknown;
  busy: boolean;
}

export function PredictionBar({ module, state, busy }: PredictionBarProps) {
  const prediction = useAppStore((s) => s.prediction);
  const submitPrediction = useAppStore((s) => s.submitPrediction);
  const [picked, setPicked] = useState<string | null>(null);

  // Mặc định an toàn — giống `timeline?` / `edit?`: không khai thì không có UI.
  if (!module.predict) return null;

  const challenge = module.predict.challenge(state);
  if (!challenge) return null;

  const answered = prediction !== null;

  return (
    <section className="predict-bar" aria-label="Dự đoán bước tiếp theo">
      <div className="predict-head">
        {/* badge-pill (DESIGN.md): nền trắng, chữ primary, 12px/600, pill 4px 8px */}
        <span className="eyebrow">
          <IconPredict size={13} />
          DỰ ĐOÁN BƯỚC TIẾP THEO
        </span>
        <p className="predict-question">{challenge.question}</p>
      </div>

      <div className="predict-options">
        {challenge.options.map((o) => (
          <button
            key={o.id}
            type="button"
            className={`btn-choice${picked === o.id ? " is-picked" : ""}`}
            disabled={busy || answered}
            onClick={() => setPicked(o.id)}
          >
            {o.label}
          </button>
        ))}
        <button
          type="button"
          className="btn-primary"
          disabled={busy || answered || picked === null}
          onClick={() => picked && submitPrediction(picked)}
        >
          Kiểm tra
        </button>
      </div>

      {prediction && (
        <p className={`predict-result is-${prediction.verdict}`} role="status">
          {prediction.verdict === "correct" && <IconCheck size={15} />}
          {prediction.verdict === "incorrect" && <IconCross size={15} />}
          {prediction.verdict === "unsupported_to_verify" && <IconInfo size={15} />}
          <span>{prediction.message}</span>
        </p>
      )}
    </section>
  );
}
