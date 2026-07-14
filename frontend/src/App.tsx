import { HistoryView } from "./components/HistoryView";
import { HomeView } from "./components/HomeView";
import { IconPanel } from "./components/icons";
import { LibraryView } from "./components/LibraryView";
import { SimulationControls } from "./components/SimulationControls";
import { SimulationInspector } from "./components/SimulationInspector";
import { SimulationWorkspace } from "./components/SimulationWorkspace";
import { useAppStore } from "./state/store";

/**
 * M9-UX1 (mở rộng M9-UX5/UX7) — BỐN mặt trình bày trên MỘT store:
 *   home      = vào cửa: MỘT hành động chính (phân tích đề) + 6 gợi ý + 1 thẻ tiếp tục;
 *   library   = danh mục mô phỏng ĐẦY ĐỦ (gom nhóm, có lọc);
 *   workspace = phiên học: SÂN KHẤU + Quan sát + điều khiển theo capability;
 *   history   = toàn bộ lịch sử học (mở lại zero-AI).
 * Về Home KHÔNG phá liên tục học: active dọn đi nhưng lịch sử bền giữ nguyên.
 *
 * M9-UX7 — PANEL TRÁI ĐÃ GỠ HẲN. Sau khi có trang Thư viện, danh mục tồn tại ở BA
 * nơi (Home / Thư viện / panel trái) — panel trái là bản sao thứ ba, đúng thứ lỗi
 * "hai nơi làm một việc" mà M9-UX4 đã dùng để gỡ composer khỏi chính panel đó.
 * Đổi bài nay đi qua **Thư viện** trên header. Workspace còn 2 cột → sân khấu rộng
 * hẳn, header bớt một nút, bớt một component phải giữ đồng bộ.
 */

export default function App() {
  const view = useAppStore((s) => s.view);
  const active = useAppStore((s) => s.active);
  const rightOpen = useAppStore((s) => s.rightOpen);
  const toggleRight = useAppStore((s) => s.toggleRight);
  const goHome = useAppStore((s) => s.goHome);
  const openHistory = useAppStore((s) => s.openHistory);
  const openLibrary = useAppStore((s) => s.openLibrary);

  const inWorkspace = view === "workspace" && active !== null;
  const layoutClass = `app-layout${rightOpen ? "" : " right-closed"}`;

  return (
    <>
      <header className="nav-bar">
        <button className="nav-wordmark" onClick={goHome} title="Về trang chủ">
          AlgoSim
        </button>
        {/* M9-UX5: điều hướng là LINK CHỮ đẩy sang phải, trang đang xem gạch chân.
            M9-UX7: chỉ còn MỘT nút bật/tắt panel (Quan sát) — panel trái đã gỡ hẳn. */}
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
