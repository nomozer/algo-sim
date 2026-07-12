import type { ComponentType } from "react";
import { getSimulation } from "../simulations/registry";
import type { WorkspaceProps } from "../simulations/types";
import { useAppStore } from "../state/store";

const MODE_LABEL: Record<string, string> = {
  progressive: "từng bước",
  exploratory: "khám phá",
  hybrid: "kết hợp",
};

/**
 * Vùng trung tâm — host sân khấu mô phỏng (M2 #1). KHÔNG giả định simulation
 * là thuật toán (M2 #2): mọi thứ domain-specific render qua module.Workspace
 * lấy từ registry.
 */
export function SimulationWorkspace() {
  const active = useAppStore((s) => s.active);
  const unsupported = useAppStore((s) => s.unsupported);
  const playing = useAppStore((s) => s.playing);
  const dispatch = useAppStore((s) => s.dispatch);

  if (unsupported) {
    return (
      <section className="card">
        <span className="eyebrow">NGOÀI DANH MỤC MÔ PHỎNG</span>
        <p style={{ marginTop: "var(--sp-sm)" }}>{unsupported.reason}</p>
        <p className="notes">
          Danh mục mô phỏng sẽ được mở rộng dần (nhị phân, cổng logic, mạng máy tính...).
        </p>
      </section>
    );
  }

  if (!active) {
    return (
      <div className="empty-state" style={{ margin: "auto 0" }}>
        <p style={{ fontSize: 40, marginBottom: "var(--sp-sm)" }}>⧉</p>
        <p>
          Nhập một bài toán rồi bấm <strong>Phân tích đề bằng AI</strong>,
          <br />
          hoặc chọn một bài trong <strong>danh mục mô phỏng</strong> bên trái.
        </p>
      </div>
    );
  }

  const mod = getSimulation(active.moduleId);
  if (!mod) {
    return <div className="error-banner">Không tìm thấy module "{active.moduleId}".</div>;
  }
  const Workspace = mod.Workspace as ComponentType<WorkspaceProps>;

  return (
    <section className="card card-elevated workspace-card">
      <div className="workspace-header">
        <span className="eyebrow">{mod.domain.toUpperCase()}</span>
        <h2 className="workspace-title">{active.envelope.title}</h2>
        <span className="hint">
          {mod.title} · {MODE_LABEL[mod.interactionMode]} ·{" "}
          {mod.supportedVisualModes.join(" / ").toUpperCase()}
        </span>
      </div>
      <Workspace config={active.config} state={active.state} busy={playing} dispatch={dispatch} />
    </section>
  );
}
