import { HistoryView } from "./components/HistoryView";
import { HomeView } from "./components/HomeView";
import { InputPanel } from "./components/InputPanel";
import { SimulationControls } from "./components/SimulationControls";
import { SimulationInspector } from "./components/SimulationInspector";
import { SimulationWorkspace } from "./components/SimulationWorkspace";
import { useAppStore } from "./state/store";

/**
 * M9-UX1 — ba mặt trình bày trên MỘT store:
 *   home      = vào cửa: MỘT hành động chính (phân tích đề) + gợi ý + gần đây;
 *               KHÔNG inspector rỗng, KHÔNG timeline rỗng, KHÔNG panel thừa.
 *   workspace = phiên học đầy đủ (bố cục simulation-centered M2 giữ nguyên:
 *               trái đề/danh mục · GIỮA sân khấu lớn nhất · phải quan sát/AI ·
 *               đáy điều khiển theo capability).
 *   history   = toàn bộ lịch sử học (mở lại zero-AI).
 * Về Home KHÔNG phá liên tục học: active dọn đi nhưng lịch sử bền giữ nguyên.
 */
export default function App() {
  const view = useAppStore((s) => s.view);
  const active = useAppStore((s) => s.active);
  const leftOpen = useAppStore((s) => s.leftOpen);
  const rightOpen = useAppStore((s) => s.rightOpen);
  const toggleLeft = useAppStore((s) => s.toggleLeft);
  const toggleRight = useAppStore((s) => s.toggleRight);
  const goHome = useAppStore((s) => s.goHome);
  const openHistory = useAppStore((s) => s.openHistory);

  const inWorkspace = view === "workspace" && active !== null;
  const layoutClass = `app-layout${leftOpen ? "" : " left-closed"}${rightOpen ? "" : " right-closed"}`;

  return (
    <>
      <header className="nav-bar">
        <button className="nav-wordmark" onClick={goHome} title="Về trang chủ">
          AlgoSim
        </button>
        <nav style={{ display: "flex", gap: "var(--sp-xs)" }}>
          <button
            className={`btn-utility${view === "home" ? " is-active" : ""}`}
            onClick={goHome}
          >
            Trang chủ
          </button>
          <button
            className={`btn-utility${view === "history" ? " is-active" : ""}`}
            onClick={openHistory}
          >
            Lịch sử
          </button>
        </nav>
        {inWorkspace && (
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
        )}
      </header>

      {inWorkspace ? (
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
      ) : (
        <main className="app-single">{view === "history" ? <HistoryView /> : <HomeView />}</main>
      )}
    </>
  );
}
