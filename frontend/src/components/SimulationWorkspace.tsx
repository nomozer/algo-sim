import { Suspense, type ComponentType } from "react";
import { getSimulation } from "../simulations/registry";
import { availableVisualModes, effectiveVisualMode, rendererFor } from "../simulations/renderer";
import type { VisualMode, WorkspaceProps } from "../simulations/types";
import { useAppStore } from "../state/store";
import { PredictionBar } from "./PredictionBar";

/**
 * M8: toggle 2D/3D — component THUẦN theo props (export để test SSR được:
 * store zustand trả initial state khi renderToString nên không test qua store).
 * Dưới 2 mode khả dụng → null: không affordance rỗng (triết lý M7.14D.1).
 */
export function VisualModeToggle({
  modes,
  mode,
  onSelect,
}: {
  modes: VisualMode[];
  mode: VisualMode;
  onSelect: (m: VisualMode) => void;
}) {
  if (modes.length < 2) return null;
  return (
    <span className="visual-mode-toggle" role="group" aria-label="Chế độ hiển thị">
      {modes.map((m) => (
        <button
          key={m}
          type="button"
          className={`btn-utility${mode === m ? " is-active" : ""}`}
          onClick={() => onSelect(m)}
        >
          {m.toUpperCase()}
        </button>
      ))}
    </span>
  );
}

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
  const visualMode = useAppStore((s) => s.visualMode);
  const setVisualMode = useAppStore((s) => s.setVisualMode);

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

  // M8: renderer DẪN XUẤT TỪ CAPABILITY của module (không switch-case theo id).
  // Mode người dùng chọn nhưng module không đáp ứng → rơi an toàn về 2D.
  const modes = availableVisualModes(mod);
  const mode = effectiveVisualMode(mod, visualMode);
  const Stage = rendererFor(mod, mode) as ComponentType<WorkspaceProps>;

  return (
    <section className="card card-elevated workspace-card">
      <div className="workspace-header">
        <span className="eyebrow">{mod.domain.toUpperCase()}</span>
        <h2 className="workspace-title">{active.envelope.title}</h2>
        <span className="hint">
          {mod.title} · {MODE_LABEL[mod.interactionMode]} ·{" "}
          {mod.supportedVisualModes.join(" / ").toUpperCase()}
        </span>
        {/* M8: toggle 2D/3D CHỈ khi module thật sự có ≥2 renderer — module 2D-only
            không thấy nút nào. Đổi mode = đổi component vẽ, engine state/timeline/
            prediction giữ nguyên. */}
        <VisualModeToggle modes={modes} mode={mode} onSelect={setVisualMode} />
      </div>
      {/* Suspense: renderer 3D được code-split (React.lazy) — chờ tải chunk
          Three.js thì hiện placeholder; renderer 2D đồng bộ, không suspend. */}
      <Suspense fallback={<div className="empty-state">Đang tải chế độ hiển thị…</div>}>
        <Stage config={active.config} state={active.state} busy={playing} dispatch={dispatch} />
      </Suspense>
      {/* M8-PRE-LIP: một UI dự đoán DÙNG CHUNG — module không khai `predict` thì
          không render gì. M8: nằm NGOÀI renderer nên tự nhiên renderer-independent —
          2D hay 3D đều cùng PredictionBar này, không có bản 3D riêng. */}
      <PredictionBar module={mod} state={active.state} busy={playing} />
    </section>
  );
}
