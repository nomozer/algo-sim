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
 * (M17 W0) Thông báo "ngoài danh mục" cho HỌC SINH — component THUẦN theo
 * props (export để test SSR như VisualModeToggle). Ưu tiên `learner_reason`
 * (server gắn ở biên API, không token kỹ thuật); `reason` kỹ thuật chỉ là
 * fallback tương thích ngược cho envelope cũ. Không bao giờ render
 * error_code / failure_category / JSON path.
 */
export function UnsupportedNotice({
  unsupported,
}: {
  unsupported: { reason: string; learner_reason?: string; failure_category?: string };
}) {
  // (M17-VR1) Đề THIẾU DỮ KIỆN khác hẳn đề NGOÀI DANH MỤC: chủ đề vẫn được hỗ
  // trợ, chỉ là em chưa cho đủ dữ liệu. Nói "ngoài danh mục" ở đây làm học sinh
  // tưởng hệ không mô phỏng được dạng bài đó — sai và làm nản.
  const insufficient = unsupported.failure_category === "insufficient_specification";
  // (M17 W2B-VR) Đề hỏi NHIỀU việc/nhiều truy vấn cùng lúc khác hẳn "thiếu dữ
  // kiện" và "ngoài danh mục": chủ đề được hỗ trợ, dữ liệu đủ, chỉ là mỗi lần
  // mô phỏng trình bày được một yêu cầu. Nói "ngoài danh mục" ở đây làm học
  // sinh tưởng hệ không làm được — sai.
  const incomplete = unsupported.failure_category === "semantic_incomplete";
  const eyebrow = insufficient ? "CHƯA ĐỦ DỮ KIỆN"
    : incomplete ? "TÁCH THÀNH TỪNG YÊU CẦU"
    : "NGOÀI DANH MỤC MÔ PHỎNG";
  const hint = insufficient
    ? "Bổ sung dữ liệu còn thiếu vào đề rồi gửi lại — dạng bài này hệ có mô phỏng."
    : incomplete
    ? "Mỗi lần hỏi một yêu cầu (giữ nguyên dữ liệu) để xem đầy đủ từng bước của yêu cầu đó."
    : "Danh mục mô phỏng sẽ được mở rộng dần (nhị phân, cổng logic, mạng máy tính...).";
  return (
    <section className="card">
      <span className="eyebrow">{eyebrow}</span>
      <p style={{ marginTop: "var(--sp-sm)" }}>
        {unsupported.learner_reason ?? unsupported.reason}
      </p>
      <p className="notes">{hint}</p>
    </section>
  );
}

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
    return <UnsupportedNotice unsupported={unsupported} />;
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
  // M17-RC1 §E — nhãn miền hiển thị cho HỌC SINH, không phải id kỹ thuật.
  // "GENERIC" vô nghĩa với người học (audit trình duyệt bắt được); các miền
  // khác đổi sang tiếng Việt cho nhất quán. Không đổi `mod.domain`.
  function domainBadge(domain: string): string {
    const VI: Record<string, string> = {
      generic: "MÔ PHỎNG THEO MÔ TẢ",
      algorithm: "THUẬT TOÁN",
      network: "MẠNG",
      tree: "CÂY",
      binary: "HỆ CƠ SỐ",
      logic: "LOGIC",
      database: "TRUY VẤN BẢNG",
    };
    return VI[domain] ?? domain.toUpperCase();
  }

  return (
    <section className="card card-elevated workspace-card">
      <div className="workspace-header">
        <span className="eyebrow">{domainBadge(mod.domain)}</span>
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
