import { useEffect } from "react";
import { AppSidebar } from "./components/AppSidebar";
import { AssignDialog } from "./components/AssignDialog";
import { AssignmentsView } from "./components/AssignmentsView";
import { AuthGate } from "./components/AuthGate";
import { ClassesView } from "./components/ClassesView";
import { HistoryView } from "./components/HistoryView";
import { HomeView } from "./components/HomeView";
import { IconPanel } from "./components/icons";
import { LibraryView } from "./components/LibraryView";
import { MonitorRoute } from "./components/MonitorRoute";
import { ObserveView } from "./components/ObserveView";
import { PracticeReporter } from "./components/PracticeReporter";
import { SimulationControls } from "./components/SimulationControls";
import { SimulationWorkspace } from "./components/SimulationWorkspace";
import { hopLeScene3D } from "./simulations/domains/geometry/scene3d-model";
import { useAppStore } from "./state/store";
import { useAuthStore } from "./state/auth";

/**
 * M18 — HAI VỎ, MỘT ỨNG DỤNG.
 *
 * TRƯỚC ĐĂNG NHẬP: không thanh điều hướng bên trái. Chỉ header mỏng + một ô
 * nhập đề ở giữa. Người lạ vào trang chưa cần biết AlgoSim có lớp học; họ cần
 * biết nó làm được gì, và cách nhanh nhất là để họ chạy thử một cái thật.
 *
 * SAU ĐĂNG NHẬP: thêm thanh điều hướng ứng dụng theo VAI TRÒ. Nó THU GỌN được
 * (56px) và thành ngăn kéo ở màn hẹp, nên sân khấu mô phỏng vẫn là thứ lớn nhất
 * trên màn hình — đo ở 1366: sân khấu 1074px kể cả khi thanh đang mở.
 *
 * M18-UI — NHIỀU PHIÊN ĐÃ GỠ. Mỗi lúc đúng một mô phỏng: mở bài khác là THAY
 * bài đang xem, và bài cũ nằm lại trong Lịch sử (mở lại 0 gọi AI). Dải tab
 * phiên cùng bộ máy `sessions`/`switchSession` đã xoá theo.
 */

export default function App() {
  const view = useAppStore((s) => s.view);
  const active = useAppStore((s) => s.active);
  const rightOpen = useAppStore((s) => s.rightOpen);
  const toggleRight = useAppStore((s) => s.toggleRight);
  const goHome = useAppStore((s) => s.goHome);
  const setView = useAppStore((s) => s.setView);
  const collapsed = useAppStore((s) => s.sidebarCollapsed);
  const openDrawer = useAppStore((s) => s.openSidebarDrawer);
  const assignment = useAppStore((s) => s.activeAssignment);

  const user = useAuthStore((s) => s.user);
  const refresh = useAuthStore((s) => s.refresh);
  const openAuthGate = useAuthStore((s) => s.openAuthGate);

  /* Hỏi máy chủ MỘT LẦN lúc mở app: phiên nằm ở cookie httpOnly nên JS không
     tự đọc được, và đây là cách duy nhất biết mình đang là ai. */
  useEffect(() => { void refresh(); }, [refresh]);

  const inWorkspace = view === "workspace" && active !== null;
  /* ── CANVAS-FIRST: KHÔNG cột điều hướng thường trực ────────────────────
   *
   * Cột 216px (hay 56px lúc thu) là đúng cho một trang danh sách. Với xưởng
   * hình 3D thì nó lấy mất bề rộng của **thứ cả bài nói về**, và học sinh
   * không điều hướng đi đâu trong lúc đang xoay hình.
   *
   * Component vẫn được MOUNT — chỉ cột thường trực biến mất, còn ngăn kéo giữ
   * nguyên (chip «Menu» trong thanh xưởng mở nó). Gỡ hẳn component thì mất
   * luôn ngăn kéo, và học sinh vào xưởng là không ra được.
   *
   * Điều kiện dùng CÙNG thẩm quyền với `SimulationWorkspace`: cảnh ĐÃ DỰNG,
   * không phải `visual_mode` được khai. Hai chỗ hỏi hai câu khác nhau thì vỏ
   * và ruột sẽ lệch nhau đúng ở bài đầu tiên có envelope lạ. */
  const canvasFirst =
    inWorkspace && hopLeScene3D((active.envelope as { scene3d?: unknown }).scene3d);
  /* W-UI · XƯỞNG 3D LẤY BỀ RỘNG MÀN HÌNH.
     Lưới shell được đặt cho các cơ chế 2D: cột nội dung `auto` với sàn bằng
     chính sách khay, nên một xưởng 3D — vốn không có bề rộng nội tại — co về
     đúng cái sàn ấy và nằm giữa hai khoảng trắng lớn. Đo được ở 1600×900:
     khung 3D 606px trên 1600px khả dụng.
     Cùng vị ngữ `canvasFirst` (dẫn từ `scene3d` có thật, không từ chế độ khai),
     nên vỏ và ruột không thể lệch nhau. */
  const layoutClass = `app-layout${rightOpen ? "" : " right-closed"}`
    + (canvasFirst ? " la-canh-3d" : "");

  const page =
    view === "history" ? <HistoryView />
    : view === "library" ? <LibraryView />
    : view === "classes" ? <ClassesView />
    : view === "assignments" ? <AssignmentsView />
    : view === "observe" ? <ObserveView />
    : view === "monitor" ? <MonitorRoute />
    : <HomeView />;

  return (
    <div className={`app-root${user ? " is-authed" : ""}`
      + (user && inWorkspace && collapsed ? " nav-collapsed" : "")
      + (user && canvasFirst ? " is-canvas-first" : "")}>
      {user && <AppSidebar />}
      {/* Không vẽ gì — chỉ chuyển state engine thành bằng chứng thực hành. */}
      {user && <PracticeReporter />}

      <div className="app-main">
        <header className="nav-bar">
          {/* Nút mở ngăn kéo CHỈ có nghĩa ở màn hẹp; CSS ẩn nó ở desktop. */}
          {user && (
            <button className="nav-drawer-btn" onClick={openDrawer}
              aria-label="Mở thanh điều hướng">
              <IconPanel side="left" size={18} />
            </button>
          )}
          {/* W6C — ĐĂNG NHẬP RỒI thì tên sản phẩm sống ở ĐẦU CỘT TRÁI
              (`AppSidebar`), nên giữ thêm một bản ở thanh trên là nói cùng một
              điều hai lần trên cùng một màn hình — và bản ở đây còn nằm lệch
              khỏi cột, đọc ra như hai hệ điều hướng. Chưa đăng nhập thì KHÔNG có
              cột trái, nên thanh trên vẫn là chỗ duy nhất mang tên. */}
          {!user && (
            <button className="nav-wordmark" onClick={goHome} title="Về trang chủ">
              AlgoSim
            </button>
          )}

          <nav className="nav-links">
            {/* CHƯA đăng nhập: header mỏng, hai hành động, không mục ứng dụng nào. */}
            {!user ? (
              <>
                <button className="nav-link" onClick={() => openAuthGate("login")}>
                  Đăng nhập
                </button>
                <button className="btn-primary nav-cta" onClick={() => openAuthGate("register")}>
                  Đăng ký
                </button>
              </>
            ) : inWorkspace && (
              <>
                {/* Đang làm bài được giao: nói ra, để em ấy biết mình đang ở đâu. */}
                {assignment && (
                  <span className="nav-assignment" title={assignment.instruction}>
                    Bài: <strong>{assignment.title}</strong>
                  </span>
                )}
                {/* Giáo viên giao ĐÚNG thứ đang xem — quyết định không tách
                    khỏi mô phỏng nó nói về. */}
                <AssignDialog />
                {/* M18-UI — MỘT mô phỏng tại một thời điểm: nút này THAY bài
                    đang xem chứ không mở thêm. Bài cũ không mất — nó đã nằm
                    trong Lịch sử, mở lại vẫn 0 gọi AI. */}
                <button className="btn-utility" onClick={goHome}
                  title="Phân tích một đề khác (bài đang xem được lưu vào Lịch sử)">
                  + Mô phỏng mới
                </button>
                <button className={`btn-utility${rightOpen ? " is-active" : ""}`}
                  onClick={toggleRight} title="Ẩn/hiện bảng giải thích">
                  Giải thích
                  <IconPanel side="right" size={14} />
                </button>
              </>
            )}
            {/* Đã đăng nhập nhưng KHÔNG ở trong mô phỏng: điều hướng nằm ở
                thanh bên, header không lặp lại nó. */}
            {user && !inWorkspace && view !== "home" && (
              <button className="btn-utility" onClick={() => setView("home")}>
                + Mô phỏng mới
              </button>
            )}
          </nav>
        </header>

        {inWorkspace ? (
          <main className={layoutClass}>
            <section className="panel-center">
              <SimulationWorkspace />
            </section>
            {/* W5AC — KHÔNG còn `aside.panel-right`: nội dung Giải thích nay là
                CỘT HAI bên trong thẻ (`SimulationWorkspace`), cạnh chính cơ chế
                nó giải thích. Xem lý do đo được ở chú thích trong workspace. */}
            {/* W-UI · MỘT KHAY ĐIỀU KHIỂN TRÊN MỘT MÀN HÌNH.
                `SimulationControls` là khay của đường 2D: nó lái bước trong
                store. Xưởng 3D có bộ tua riêng, lái `InteractionState` — hai
                trạng thái THẬT SỰ khác nhau, nên hiện cả hai là bày ra hai
                thanh cùng ghi chữ "Bước" mà kéo thanh dưới thì hình không đổi.
                Ảnh chụp thật bắt đúng cảnh ấy: trên ghi "Bước 7/7", dưới ghi
                "Bước 1/7".
                Ẩn khay 2D khi cảnh là 3D. Không xoá hành vi nào: đường 2D giữ
                nguyên khay của nó. */}
            {!canvasFirst && (
              <footer className="panel-controls">
                <SimulationControls />
              </footer>
            )}
          </main>
        ) : (
          <main className="app-single">{page}</main>
        )}
      </div>

      <AuthGate />
    </div>
  );
}
