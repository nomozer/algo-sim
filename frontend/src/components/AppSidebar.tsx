import { useAppStore, type AppView } from "../state/store";
import { useAuthStore } from "../state/auth";
import {
  IconBack, IconCheck, IconExperiment, IconPanel, IconPredict, IconSearch,
} from "./icons";

/**
 * M18 — THANH ĐIỀU HƯỚNG ỨNG DỤNG, CHỈ CÓ SAU KHI ĐĂNG NHẬP.
 *
 * ─── KHÔNG PHẢI CÁI CỘT PHIÊN ĐÃ BỊ GỠ ────────────────────────────────────
 *
 * W4B-3B từng gỡ một cột trái 208px vì nó trải qua CẢ hàng sân khấu lẫn hàng
 * điều khiển, bóp cả hai và làm hàng transport xuống dòng. Cái đó liệt kê các
 * PHIÊN MÔ PHỎNG đang mở; điều hướng phiên nay là `SessionTabs` — một hàng
 * ngang trên sân khấu, và nó KHÔNG đổi.
 *
 * Cái này là chuyện khác: điều hướng MỨC ỨNG DỤNG (lớp, bài, thư viện). Để hai
 * thứ đó không lặp lại lỗi cũ, có ba ràng buộc, cả ba đều có test:
 *   1. nó nằm NGOÀI lưới của workspace — không ô lưới nào của nó đi qua hàng
 *      điều khiển (đó chính là cơ chế gây lỗi cũ);
 *   2. vào trong mô phỏng thì mặc định THU GỌN thành dải biểu tượng;
 *   3. màn hẹp thì nó thành ngăn kéo TẠM, không chiếm chỗ thường trực.
 */

interface Item {
  view: AppView;
  label: string;
  icon: React.ReactNode;
}

/** Điều hướng của HỌC SINH — bám vào việc học, không phải vào quản trị. */
const STUDENT_ITEMS: Item[] = [
  { view: "home", label: "Mô phỏng mới", icon: <IconExperiment size={16} /> },
  { view: "assignments", label: "Bài thực hành", icon: <IconCheck size={16} /> },
  { view: "classes", label: "Lớp của em", icon: <IconPredict size={16} /> },
  { view: "library", label: "Thư viện", icon: <IconSearch size={16} /> },
  { view: "history", label: "Lịch sử", icon: <IconBack size={16} /> },
];

/** Điều hướng của GIÁO VIÊN. Không sổ điểm, không thời khoá biểu (`§12`). */
const TEACHER_ITEMS: Item[] = [
  { view: "home", label: "Mô phỏng mới", icon: <IconExperiment size={16} /> },
  { view: "classes", label: "Lớp học", icon: <IconPredict size={16} /> },
  { view: "assignments", label: "Bài đã giao", icon: <IconCheck size={16} /> },
  { view: "observe", label: "Quan sát lớp", icon: <IconSearch size={16} /> },
  { view: "library", label: "Thư viện", icon: <IconPanel side="left" size={16} /> },
  { view: "history", label: "Lịch sử", icon: <IconBack size={16} /> },
];

export function itemsForRole(role: "student" | "teacher"): Item[] {
  return role === "teacher" ? TEACHER_ITEMS : STUDENT_ITEMS;
}

export function AppSidebar() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const view = useAppStore((s) => s.view);
  const setView = useAppStore((s) => s.setView);
  const collapsed = useAppStore((s) => s.sidebarCollapsed);
  const toggle = useAppStore((s) => s.toggleSidebar);
  const drawerOpen = useAppStore((s) => s.sidebarDrawerOpen);
  const closeDrawer = useAppStore((s) => s.closeSidebarDrawer);

  if (!user) return null;
  const items = itemsForRole(user.role);

  return (
    <>
      {/* Nền mờ CHỈ ở màn hẹp: ngăn kéo phải đóng được bằng cách bấm ra ngoài. */}
      {drawerOpen && <div className="app-nav-scrim" onClick={closeDrawer} aria-hidden="true" />}

      <nav className={`app-nav${collapsed ? " is-collapsed" : ""}${drawerOpen ? " is-drawer-open" : ""}`}
        aria-label="Điều hướng chính">
        <button type="button" className="app-nav-toggle" onClick={toggle}
          aria-expanded={!collapsed}
          aria-label={collapsed ? "Mở rộng thanh điều hướng" : "Thu gọn thanh điều hướng"}
          title={collapsed ? "Mở rộng" : "Thu gọn"}>
          <IconPanel side="left" size={16} />
        </button>

        <ul className="app-nav-list">
          {items.map((it) => (
            <li key={it.view}>
              <button type="button"
                className={`app-nav-item${view === it.view ? " is-active" : ""}`}
                aria-current={view === it.view ? "page" : undefined}
                /* Thu gọn thì nhãn biến mất khỏi hình, nên tên khả truy cập
                   phải do `aria-label` chở — nếu không, dải biểu tượng là một
                   hàng nút không tên với trình đọc màn hình. */
                aria-label={collapsed ? it.label : undefined}
                title={collapsed ? it.label : undefined}
                onClick={() => { setView(it.view); closeDrawer(); }}>
                <span className="app-nav-icon" aria-hidden="true">{it.icon}</span>
                <span className="app-nav-label">{it.label}</span>
              </button>
            </li>
          ))}
        </ul>

        <div className="app-nav-foot">
          <button type="button" className="app-nav-item app-nav-account"
            aria-label={collapsed ? user.displayName : undefined}
            title={collapsed ? user.displayName : undefined}
            onClick={() => setView("account")}>
            <span className="app-nav-avatar" aria-hidden="true">
              {user.displayName.trim().charAt(0).toUpperCase() || "?"}
            </span>
            <span className="app-nav-label">
              <strong>{user.displayName}</strong>
              <small>{user.role === "teacher" ? "Giáo viên" : "Học sinh"}</small>
            </span>
          </button>
          <button type="button" className="app-nav-item app-nav-logout"
            aria-label={collapsed ? "Đăng xuất" : undefined}
            title={collapsed ? "Đăng xuất" : undefined}
            onClick={() => void logout()}>
            <span className="app-nav-icon" aria-hidden="true"><IconBack size={16} /></span>
            <span className="app-nav-label">Đăng xuất</span>
          </button>
        </div>
      </nav>
    </>
  );
}
