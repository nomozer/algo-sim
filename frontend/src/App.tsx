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

/**
 * Icon panel (M9-UX4) — SVG, KHÔNG dùng ký tự Unicode.
 * Trước đây nút này ghi `◧` / `◨` (U+25E7/25E8): font hệ thống Windows không có
 * glyph nên hiện ra Ô VUÔNG RỖNG (tofu) ngay trên header. Ký tự hình khối hiếm
 * là bẫy — vẽ SVG thì không phụ thuộc font nào.
 */
function PanelIcon({ side }: { side: "left" | "right" }) {
  return (
    <svg
      className="panel-icon"
      viewBox="0 0 16 16"
      width="13"
      height="13"
      aria-hidden="true"
      focusable="false"
    >
      <rect x="1.5" y="2.5" width="13" height="11" rx="2" fill="none" stroke="currentColor" />
      <rect
        x={side === "left" ? 1.5 : 9.5}
        y="2.5"
        width="5"
        height="11"
        rx={0}
        fill="currentColor"
        opacity={0.75}
      />
    </svg>
  );
}

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
              title="Ẩn/hiện danh mục mô phỏng"
            >
              <PanelIcon side="left" />
              Danh mục
            </button>
            <button
              className={`btn-utility${rightOpen ? " is-active" : ""}`}
              onClick={toggleRight}
              title="Ẩn/hiện bảng quan sát và hỏi AI"
            >
              Quan sát
              <PanelIcon side="right" />
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
