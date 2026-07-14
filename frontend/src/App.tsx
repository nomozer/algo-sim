import { HistoryView } from "./components/HistoryView";
import { HomeView } from "./components/HomeView";
import { IconPanel } from "./components/icons";
import { InputPanel } from "./components/InputPanel";
import { LibraryView } from "./components/LibraryView";
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
  const openLibrary = useAppStore((s) => s.openLibrary);

  const inWorkspace = view === "workspace" && active !== null;
  const layoutClass = `app-layout${leftOpen ? "" : " left-closed"}${rightOpen ? "" : " right-closed"}`;

  return (
    <>
      <header className="nav-bar">
        <button className="nav-wordmark" onClick={goHome} title="Về trang chủ">
          AlgoSim
        </button>
        {/* M9-UX5: điều hướng là LINK CHỮ đẩy sang phải, trang đang xem gạch chân.
            Trước đây là hai nút pill dính sát wordmark — trông như thanh công cụ,
            không phải điều hướng. Nút bật/tắt panel nằm cùng bên phải, sau vạch ngăn. */}
        <nav className="nav-links">
          <button
            className={`nav-link${view === "home" ? " is-active" : ""}`}
            onClick={goHome}
          >
            Trang chủ
          </button>
          <button
            className={`nav-link${view === "library" ? " is-active" : ""}`}
            onClick={openLibrary}
          >
            Thư viện
          </button>
          <button
            className={`nav-link${view === "history" ? " is-active" : ""}`}
            onClick={openHistory}
          >
            Lịch sử
          </button>

          {inWorkspace && (
            <>
              <span className="nav-divider" />
              <button
                className={`btn-utility${leftOpen ? " is-active" : ""}`}
                onClick={toggleLeft}
                title="Ẩn/hiện danh mục mô phỏng"
              >
                <IconPanel side="left" size={14} />
                Danh mục
              </button>
              <button
                className={`btn-utility${rightOpen ? " is-active" : ""}`}
                onClick={toggleRight}
                title="Ẩn/hiện bảng quan sát"
              >
                Quan sát
                <IconPanel side="right" size={14} />
              </button>
            </>
          )}
        </nav>
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
        <main className="app-single">
          {view === "history" ? (
            <HistoryView />
          ) : view === "library" ? (
            <LibraryView />
          ) : (
            <HomeView />
          )}
        </main>
      )}
    </>
  );
}
