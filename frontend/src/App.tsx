import { HistoryView } from "./components/HistoryView";
import { HomeView } from "./components/HomeView";
import { IconPanel } from "./components/icons";
import { LibraryView } from "./components/LibraryView";
import { SimulationControls } from "./components/SimulationControls";
import { SimulationInspector } from "./components/SimulationInspector";
import { SimulationWorkspace } from "./components/SimulationWorkspace";
import { useAppStore } from "./state/store";
import { SessionTabs } from "./components/SessionTabs";

/**
 * M9-UX1 (mở rộng M9-UX5/UX7) — BỐN mặt trình bày trên MỘT store:
 *   home      = vào cửa: MỘT hành động chính (phân tích đề) + 6 gợi ý + 1 thẻ tiếp tục;
 *   library   = danh mục mô phỏng ĐẦY ĐỦ (gom nhóm, có lọc);
 *   workspace = phiên học: SÂN KHẤU + Giải thích + điều khiển theo capability;
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
  const newSession = useAppStore((s) => s.newSession);
  const sessionCount = useAppStore((s) => s.sessions.length);

  const inWorkspace = view === "workspace" && active !== null;
  /* W4B-3B — điều hướng phiên là một HÀNG NGANG GỌN ngay trên sân khấu, chỉ
     dựng khi có ≥2 bài đang mở. Bản trước là một CỘT 208px trải qua cả hàng
     `center` lẫn hàng `controls`, nên nó bóp cả sân khấu lẫn dải điều khiển —
     đó mới là nguyên nhân thật của việc hàng transport xuống dòng. */
  const hasTabs = sessionCount >= 2;
  const layoutClass =
    `app-layout${rightOpen ? "" : " right-closed"}${hasTabs ? " has-tabs" : ""}`;

  return (
    <>
      <header className="nav-bar">
        <button className="nav-wordmark" onClick={goHome} title="Về trang chủ">
          AlgoSim
        </button>
        {/* M9-UX5: điều hướng là LINK CHỮ đẩy sang phải, trang đang xem gạch chân.
            M9-UX7: chỉ còn MỘT nút bật/tắt panel (Giải thích) — panel trái đã gỡ hẳn.
            W4B-2B §8: panel nay ĐÓNG mặc định ở mọi màn, nên nút này là đường VÀO
            chứ không còn là đường ra — giữ nó luôn hiện khi ở workspace. */}
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
              {/* W4B-3B — LỐI VÀO "MÔ PHỎNG MỚI" VỀ ĐÂY.
                  Trước đây nó chỉ nằm trong đầu cột phiên, mà cột đó ẩn khi có
                  <2 phiên ⇒ đang mở đúng MỘT bài thì không có đường nào mở bài
                  thứ hai: tính năng nhiều phiên không với tới được từ chính
                  trạng thái khởi đầu của nó. Header đã là chủ sở hữu của hành
                  động mức-không-gian-làm-việc (cạnh "Giải thích"), nên gộp vào
                  đây chứ KHÔNG dựng hệ điều hướng thứ hai. */}
              <button
                className="btn-utility"
                onClick={newSession}
                title="Mở thêm một mô phỏng, giữ nguyên bài đang dở"
              >
                + Mô phỏng mới
              </button>
              <button
                className={`btn-utility${rightOpen ? " is-active" : ""}`}
                onClick={toggleRight}
                title="Ẩn/hiện bảng giải thích"
              >
                Giải thích
                <IconPanel side="right" size={14} />
              </button>
            </>
          )}
        </nav>
      </header>

      {inWorkspace ? (
        <main className={layoutClass}>
          <SessionTabs />

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
