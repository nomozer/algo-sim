import { useAppStore, type AppView } from "../state/store";
import { useAuthStore } from "../state/auth";
import {
  IconBack, IconCheck, IconExperiment, IconPanel, IconPredict, IconSearch,
} from "./icons";

/**
 * ĐIỀU HƯỚNG MỨC ỨNG DỤNG — MỘT HÀNG NGANG TRONG THANH TRÊN.
 *
 * ─── VÌ SAO THAY `AppSidebar` (cột trái 216px) ─────────────────────────────
 *
 * Cột trái tự nó không tệ; thứ hỏng là nó bị VÔ HIỆU đúng ở nơi sản phẩm sống.
 * `is-canvas-first` đã phải thu cột về `width: 0` mỗi khi mở một bài hình học —
 * tức là ở mọi bài, vì miền hình học nay là toàn bộ danh mục. Còn lại một cột
 * chỉ tồn tại trên các trang danh sách, cộng một ngăn kéo để mở lại nó.
 *
 * Ngăn kéo ấy là chỗ hỏng ĐO ĐƯỢC: mọi luật làm nó cư xử như ngăn kéo (phủ đè,
 * nền mờ, bấm ra ngoài để đóng) đều nằm trong `@media (max-width: 900px)`, nên
 * trên desktop bấm «Menu» biến nó thành CỘT THƯỜNG TRỰC bóp sân khấu, không nền
 * mờ, không bấm-ra-ngoài. Ảnh chụp của một bài thiết diện bắt đúng cảnh đó.
 *
 * Hàng ngang không có trạng thái nào để lệch: nó luôn hiện, ở mọi trang, kể cả
 * trong xưởng 3D. Nên «đường ra của xưởng» — bất biến mà chip «Menu» từng gánh —
 * nay là chính thanh này, và không còn gì để quên bật.
 *
 * `docs/DESIGN_BRIEF.md §2` vốn viết *"bốn màn hình (thanh điều hướng trên
 * cùng)"*; cột trái là bản trôi khỏi brief ở M18, đây là quay lại.
 *
 * ─── HAI MẢNH, VÌ THANH TRÊN CÓ HAI ĐẦU ────────────────────────────────────
 *
 * `TopNav` (trái: tên sản phẩm + mục theo vai) và `TopNavAccount` (phải: tài
 * khoản + đăng xuất) là hai export chứ không một, vì giữa chúng còn `.nav-links`
 * — hàng hành động của trang đang mở, do `App` sở hữu. Gộp làm một thì phải
 * chuyền hàng hành động ấy xuống làm prop chỉ để nó được in ra ở giữa.
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

/**
 * ĐẦU TRÁI — tên sản phẩm + mục điều hướng theo vai.
 *
 * Mục dùng lại `.nav-link` chứ không đẻ lớp mới: luật trình bày của điều hướng
 * trang (link chữ, trang đang xem gạch chân dưới) đã có từ M9-UX5 và đúng
 * nguyên vẹn ở đây. Thêm `.topnav-link` chỉ để chở phần biểu tượng.
 */
export function TopNav() {
  const user = useAuthStore((s) => s.user);
  const view = useAppStore((s) => s.view);
  const setView = useAppStore((s) => s.setView);
  const goHome = useAppStore((s) => s.goHome);

  if (!user) return null;
  const items = itemsForRole(user.role);

  return (
    <div className="topnav">
      <button type="button" className="nav-wordmark" onClick={goHome}
        title="Về trang chủ">
        AlgoSim
      </button>

      <nav className="topnav-links" aria-label="Điều hướng chính">
        {items.map((it) => (
          <button type="button" key={it.view}
            className={`nav-link topnav-link${view === it.view ? " is-active" : ""}`}
            aria-current={view === it.view ? "page" : undefined}
            onClick={() => setView(it.view)}>
            <span className="topnav-icon" aria-hidden="true">{it.icon}</span>
            {it.label}
          </button>
        ))}
      </nav>
    </div>
  );
}

/**
 * ĐẦU PHẢI — ai đang dùng máy, và lối ra.
 *
 * Vai trò in ra từ `user.role`, tức từ máy chủ (`CLASSROOM_AUTH_CONTRACT §2.1`).
 * KHÔNG dựng công tắc «chế độ giáo viên»: vai là thứ được cấp, không phải thứ
 * chọn — một ô tick ở đây sẽ đọc như lời hứa rằng bấm vào là đổi được quyền.
 */
export function TopNavAccount() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const view = useAppStore((s) => s.view);
  const setView = useAppStore((s) => s.setView);

  if (!user) return null;

  return (
    <div className="topnav-account">
      <button type="button"
        className={`topnav-user${view === "account" ? " is-active" : ""}`}
        onClick={() => setView("account")}
        title={`${user.displayName} — ${user.role === "teacher" ? "Giáo viên" : "Học sinh"}`}>
        <span className="topnav-avatar" aria-hidden="true">
          {user.displayName.trim().charAt(0).toUpperCase() || "?"}
        </span>
        <span className="topnav-user-name">{user.displayName}</span>
      </button>
      <button type="button" className="topnav-logout" onClick={() => void logout()}
        title="Đăng xuất" aria-label="Đăng xuất">
        <IconBack size={16} />
      </button>
    </div>
  );
}
