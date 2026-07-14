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

      {tab === "inspect" && (
        <>
          {active && Inspector ? (
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
          )}
          {/* M9-UX1 §17: ứng dụng đời thực — module tự khai, tĩnh, không LLM. */}
          {mod?.applications && mod.applications.length > 0 && (
            <section className="card" style={{ padding: "var(--sp-md)" }}>
              <span className="eyebrow">ỨNG DỤNG CỦA CƠ CHẾ NÀY</span>
              <ul style={{ margin: "var(--sp-sm) 0 0", paddingLeft: 18 }}>
                {mod.applications.map((a) => (
                  <li key={a} className="hint" style={{ marginBottom: 2 }}>
                    {a}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}

      {tab === "ai" && <AIHelpPanel />}
    </div>
  );
}
