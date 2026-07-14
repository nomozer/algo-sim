import type { ComponentType } from "react";
import { getSimulation } from "../simulations/registry";
import type { WorkspaceProps } from "../simulations/types";
import { useAppStore } from "../state/store";
import { AIHelpPanel } from "./AIHelpPanel";

/**
 * Panel phải — nội dung quan sát THEO DOMAIN qua module.Inspector (M2 #5):
 * algorithm → biến + mã giả; logic (sau này) → truth table; binary → bit...
 * Core không hard-code bất kỳ nội dung domain nào.
 * AI Help chỉ là tab phụ (M2 #6).
 */
export function SimulationInspector() {
  const active = useAppStore((s) => s.active);
  const playing = useAppStore((s) => s.playing);
  const dispatch = useAppStore((s) => s.dispatch);
  // Tab nằm trong store (không mất khi panel đóng/mở); AI không mở mặc định
  const tab = useAppStore((s) => s.inspectorTab);
  const setTab = useAppStore((s) => s.setInspectorTab);

  const mod = active ? getSimulation(active.moduleId) : undefined;
  const Inspector = mod?.Inspector as ComponentType<WorkspaceProps> | undefined;

  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <div className="tab-bar">
        <button
          className={`btn-utility${tab === "inspect" ? " is-active" : ""}`}
          onClick={() => setTab("inspect")}
        >
          Quan sát
        </button>
        <button
          className={`btn-utility${tab === "ai" ? " is-active" : ""}`}
          onClick={() => setTab("ai")}
        >
          Hỏi AI
        </button>
      </div>

      {/* M9-UX2: thẻ "Ứng dụng của cơ chế này" (M9-UX1 §17) đã GỠ — nội dung
          tay quá nông so với mô hình học mô phỏng và gây nhiễu thị giác.
          Trải nghiệm transfer-of-learning thật là việc tương lai (cần duyệt). */}
      {tab === "inspect" &&
        (active && Inspector ? (
          <Inspector
            config={active.config}
            state={active.state}
            busy={playing}
            dispatch={dispatch}
          />
        ) : (
          <p className="hint">
            {active
              ? "Mô phỏng này không có panel quan sát riêng."
              : "Chưa có mô phỏng nào đang chạy."}
          </p>
        ))}

      {tab === "ai" && <AIHelpPanel />}
    </div>
  );
}
