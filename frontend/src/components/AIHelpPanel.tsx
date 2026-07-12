import { useState } from "react";
import { explainViaServer, type ExplainTurn } from "../llm/client";
import { getSimulation } from "../simulations/registry";
import { useAppStore } from "../state/store";

/**
 * Trợ giúp AI — panel PHỤ, không phải workflow bắt buộc (M2 #6, M3 §1).
 * Gửi /api/explain với snapshot JSON sạch từ module.getExplainContext
 * (trạng thái THẬT của engine). AI chỉ giải thích — không điều khiển
 * mô phỏng, không quyết định chuyển bước.
 */
export function AIHelpPanel() {
  const active = useAppStore((s) => s.active);
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<ExplainTurn[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showContext, setShowContext] = useState(false);

  if (!active) {
    return <p className="hint">Nạp một mô phỏng trước, rồi hỏi AI về trạng thái đang xem.</p>;
  }

  const mod = getSimulation(active.moduleId);
  const context = mod ? mod.getExplainContext(active.state, active.config) : null;
  const canSend = question.trim().length > 0 && !sending && context !== null;

  async function onSend() {
    if (!canSend || !context) return;
    const q = question.trim();
    setError(null);
    setSending(true);
    setQuestion("");
    setHistory((h) => [...h, { role: "user", text: q }]);
    try {
      const reply = await explainViaServer({
        simulationId: active!.moduleId,
        explainContext: context,
        question: q,
        recentHistory: history,
      });
      setHistory((h) => [...h, { role: "assistant", text: reply }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <p className="hint">
        AI giải thích <strong>trạng thái hiện tại</strong> của mô phỏng (đúng bước đang xem),
        gợi mở thay vì đưa đáp án. AI không điều khiển được mô phỏng.
      </p>

      {history.length > 0 && (
        <div className="stack" style={{ gap: "var(--sp-xs)" }}>
          {history.map((turn, idx) => (
            <div
              key={idx}
              className={`explain-msg${turn.role === "user" ? " is-user" : ""}`}
            >
              {turn.text}
            </div>
          ))}
          {sending && <div className="explain-msg">Đang suy nghĩ…</div>}
        </div>
      )}

      <textarea
        className="text-input"
        rows={3}
        placeholder='Ví dụ: "Vì sao bước này không đổi chỗ hai phần tử?"'
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            void onSend();
          }
        }}
      />
      <button className="btn-primary" disabled={!canSend} onClick={() => void onSend()}>
        {sending ? "Đang gửi…" : "Hỏi về trạng thái hiện tại"}
      </button>
      {error && <div className="error-banner">{error}</div>}

      <button className="btn-utility" onClick={() => setShowContext(!showContext)}>
        {showContext ? "Ẩn" : "Xem"} dữ liệu trạng thái sẽ gửi kèm
      </button>
      {showContext && context && (
        <pre className="context-preview">{JSON.stringify(context, null, 2)}</pre>
      )}
    </div>
  );
}
