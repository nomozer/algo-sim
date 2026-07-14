import type { ComponentType } from "react";
import { getSimulation } from "../simulations/registry";
import type { WorkspaceProps } from "../simulations/types";
import { useAppStore } from "../state/store";
import { AIHelpPanel } from "./AIHelpPanel";
import { IconAsk, IconChevronDown, IconChevronRight } from "./icons";

/**
 * Panel phải — nội dung QUAN SÁT theo domain qua module.Inspector (M2 #5):
 * algorithm → biến + mã giả; binary → bit; network → tuyến... Core không
 * hard-code bất kỳ nội dung domain nào.
 *
 * M9-UX5 — AI THÔI NGANG HÀNG VỚI MÔ PHỎNG.
 * Trước đây đây là hai tab [Quan sát][Hỏi AI]: một nửa cột phải, lúc nào cũng
 * vậy, dành cho AI. Đó là mâu thuẫn với chính luật gốc của hệ (R0: LLM KHÔNG
 * phải xương sống — nó không sinh bước, không sinh kết quả, không điều khiển
 * mô phỏng). UI mà cho AI một nửa sân khấu thì đang nói ngược lại điều đó.
 *
 * Nay: cột phải LUÔN là Quan sát. AI là một mục THU GỌN ở đáy — vẫn ở đó khi
 * học sinh cần hỏi, nhưng không đòi chỗ ngang với thứ đang dạy học.
 */
export function SimulationInspector() {
  const active = useAppStore((s) => s.active);
  const playing = useAppStore((s) => s.playing);
  const dispatch = useAppStore((s) => s.dispatch);
  const aiOpen = useAppStore((s) => s.aiOpen);
  const setAiOpen = useAppStore((s) => s.setAiOpen);

  const mod = active ? getSimulation(active.moduleId) : undefined;
  const Inspector = mod?.Inspector as ComponentType<WorkspaceProps> | undefined;

  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <span className="eyebrow">QUAN SÁT</span>

      {active && Inspector ? (
        <Inspector config={active.config} state={active.state} busy={playing} dispatch={dispatch} />
      ) : (
        <p className="hint">
          {active
            ? "Mô phỏng này không có panel quan sát riêng."
            : "Chưa có mô phỏng nào đang chạy."}
        </p>
      )}

      <section className="ai-section">
        <button
          className="ai-toggle"
          onClick={() => setAiOpen(!aiOpen)}
          aria-expanded={aiOpen}
        >
          <IconAsk size={15} />
          <span>Hỏi AI về bước này</span>
          <span className="ai-toggle-caret">
            {aiOpen ? <IconChevronDown size={15} /> : <IconChevronRight size={15} />}
          </span>
        </button>

        {aiOpen && <AIHelpPanel />}
      </section>
    </div>
  );
}
