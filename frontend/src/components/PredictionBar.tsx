import { useState } from "react";
import type { SimulationModule } from "../simulations/types";
import { useAppStore } from "../state/store";

/**
 * PredictionBar (M8-PRE-LIP) — UI DỰ ĐOÁN DÙNG CHUNG cho MỌI domain.
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
        <span className="eyebrow">🔮 DỰ ĐOÁN BƯỚC TIẾP THEO</span>
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
          {prediction.verdict === "correct" && "✓ "}
          {prediction.verdict === "incorrect" && "✗ "}
          {prediction.verdict === "unsupported_to_verify" && "• "}
          {prediction.message}
        </p>
      )}
    </section>
  );
}
