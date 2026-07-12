import { InputPanel } from "./components/InputPanel";
import { SimulationControls } from "./components/SimulationControls";
import { SimulationInspector } from "./components/SimulationInspector";
import { SimulationWorkspace } from "./components/SimulationWorkspace";
import { useAppStore } from "./state/store";

/**
 * Bố cục simulation-centered (M2 #1, #8):
 *   trái  = nhập đề + danh mục (collapse được);
 *   GIỮA  = sân khấu mô phỏng — luôn chiếm diện tích lớn nhất;
 *   phải  = Inspector + Hỏi AI (collapse được, AI không mở mặc định);
 *   đáy   = điều khiển theo capability.
 * Màn hình hẹp: panel thành drawer nổi, workspace KHÔNG bị bóp nhỏ.
 */
export default function App() {
  const leftOpen = useAppStore((s) => s.leftOpen);
  const rightOpen = useAppStore((s) => s.rightOpen);
  const toggleLeft = useAppStore((s) => s.toggleLeft);
  const toggleRight = useAppStore((s) => s.toggleRight);

  const layoutClass = `app-layout${leftOpen ? "" : " left-closed"}${rightOpen ? "" : " right-closed"}`;

  return (
    <>
      <header className="nav-bar">
        <span className="nav-wordmark">AlgoSim</span>
        <span className="nav-tagline">
          Hệ thống mô phỏng tương tác 2D/3D kết hợp LLM phân tích bài toán bằng ngôn ngữ tự
          nhiên · Tin học THPT
        </span>
        <span style={{ marginLeft: "auto", display: "flex", gap: "var(--sp-xs)" }}>
          <button
            className={`btn-utility${leftOpen ? " is-active" : ""}`}
            onClick={toggleLeft}
            title="Ẩn/hiện bảng nhập đề và danh mục"
          >
            ◧ Đề bài
          </button>
          <button
            className={`btn-utility${rightOpen ? " is-active" : ""}`}
            onClick={toggleRight}
            title="Ẩn/hiện bảng quan sát và hỏi AI"
          >
            Quan sát ◨
          </button>
        </span>
      </header>

      <main className={layoutClass}>
        {leftOpen && (
          <aside className="panel-left">
            <InputPanel />
          </aside>
        )}

        <section className="panel-center">
          <SimulationWorkspace />
        </section>

        {rightOpen && (
          <aside className="panel-right">
            <SimulationInspector />
          </aside>
        )}

        <footer className="panel-controls">
          <SimulationControls />
        </footer>
      </main>
    </>
  );
}
