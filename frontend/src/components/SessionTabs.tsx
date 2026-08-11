import { useState } from "react";
import { useAppStore } from "../state/store";

/**
 * W4B-3B — ĐIỀU HƯỚNG PHIÊN LÀ HÀNG NGANG GỌN, KHÔNG PHẢI MỘT CỘT THƯỜNG TRỰC.
 *
 * ─── VÌ SAO ĐỔI (đo được, không phải khẩu vị) ─────────────────────────────
 *
 * Bản trước (`SessionRail`) là một CỘT 208px với `grid-area: rail` trải qua CẢ
 * hai hàng `center` và `controls`:
 *
 *     "rail center right"
 *     "rail controls right"
 *
 * Nên nó không chỉ bóp sân khấu — nó bóp luôn DẢI ĐIỀU KHIỂN đúng bằng ngần
 * ấy, và đó là nguyên nhân thật của việc hàng transport bị xuống dòng. Hai
 * triệu chứng, một nguyên nhân.
 *
 * Thứ bậc đúng của AlgoSim: **sân khấu > điều khiển > quản lí phiên**. Một cột
 * thường trực cho hạng mục thứ ba là đặt ngược thứ bậc, và mỗi pixel bề ngang
 * lấy của sân khấu phải có việc để làm.
 *
 * ─── LỖI CHỨC NĂNG BẢN CŨ CÒN MẮC ────────────────────────────────────────
 *
 * `+ Mô phỏng mới` CHỈ tồn tại trong đầu cột này, mà cột lại ẩn khi có <2 phiên
 * ⇒ đang mở đúng MỘT bài thì **không có đường nào mở bài thứ hai**. Tính năng
 * nhiều phiên không với tới được từ chính trạng thái khởi đầu của nó. Nay lối
 * vào đó về `App` header — chỗ đã sở hữu các hành động mức-không-gian-làm-việc
 * (cạnh "Giải thích") — nên nó có mặt ở MỌI số phiên.
 *
 * ─── PHẠM VI CỐ Ý HẸP ────────────────────────────────────────────────────
 *
 * mở · liệt kê · chuyển · đóng. KHÔNG lớp học, KHÔNG bài tập, KHÔNG điểm số —
 * AlgoSim là hệ mô phỏng, không phải LMS. Kiến trúc phiên KHÔNG đổi: đây thuần
 * là dời TRÌNH BÀY, `switchSession` vẫn là khôi phục thuần (0 fetch/init).
 */

/** Bao nhiêu tab hiện thẳng trước khi gộp phần dư vào `+N`. */
const VISIBLE_TABS = 4;

/**
 * Hậu tố phân biệt khi HAI phiên trùng tiêu đề — chuyện thường gặp vì mở cùng
 * một bài hai lần là cách so sánh hai nhánh what-if.
 *
 * TRÌNH BÀY THUẦN: không đụng `config`/`envelope`, không suy nghĩa từ chuỗi
 * tiêu đề. Chỉ đánh số theo THỨ TỰ MỞ, và chỉ khi thật sự trùng — bài duy nhất
 * mang tên đó thì không có hậu tố nào.
 */
export function sessionLabels(titles: string[]): string[] {
  const total = new Map<string, number>();
  for (const t of titles) total.set(t, (total.get(t) ?? 0) + 1);
  const seen = new Map<string, number>();
  return titles.map((t) => {
    if ((total.get(t) ?? 0) < 2) return t;
    const n = (seen.get(t) ?? 0) + 1;
    seen.set(t, n);
    return `${t} · ${n}`;
  });
}

export function SessionTabs() {
  const sessions = useAppStore((s) => s.sessions);
  const activeSessionId = useAppStore((s) => s.activeSessionId);
  const switchSession = useAppStore((s) => s.switchSession);
  const closeSession = useAppStore((s) => s.closeSession);
  const [listOpen, setListOpen] = useState(false);

  /* Một phiên thì không có gì để chuyển: một hàng điều hướng chỉ để lặp lại
     đúng cái tiêu đề đã in to trên sân khấu là một dải thừa. `Mô phỏng mới`
     KHÔNG mất theo — nó sống ở header. */
  if (sessions.length < 2) return null;

  const labels = sessionLabels(sessions.map((s) => s.title));
  const activeIndex = sessions.findIndex((s) => s.id === activeSessionId);

  /* Phiên đang xem LUÔN nằm trong nhóm hiện thẳng — nếu không, chuyển sang một
     bài ở phần dư sẽ làm nó biến mất khỏi hàng ngay khi vừa chọn. */
  const shown = sessions.slice(0, VISIBLE_TABS);
  if (activeIndex >= VISIBLE_TABS) shown[VISIBLE_TABS - 1] = sessions[activeIndex];
  const shownIds = new Set(shown.map((s) => s.id));
  const overflow = sessions.filter((s) => !shownIds.has(s.id));

  return (
    <nav className="session-tabs" aria-label="Mô phỏng đang mở">
      <ul className="session-tab-list">
        {shown.map((sn) => {
          const isActive = sn.id === activeSessionId;
          const label = labels[sessions.indexOf(sn)];
          return (
            <li key={sn.id} className={`session-tab${isActive ? " is-active" : ""}`}>
              <button
                type="button"
                className="session-tab-open"
                onClick={() => switchSession(sn.id)}
                aria-current={isActive ? "true" : undefined}
                title={label}
              >
                {label}
              </button>
              <button
                type="button"
                className="session-tab-close"
                onClick={() => closeSession(sn.id)}
                aria-label={`Đóng ${label}`}
                title="Đóng mô phỏng này"
              >
                ×
              </button>
            </li>
          );
        })}
      </ul>

      {/* MỘT nút giữ hai vai, đổi vai bằng CSS chứ không bằng `window.innerWidth`:
          màn rộng ⇒ `+N` cho phần dư; màn hẹp ⇒ bộ chọn "Mô phỏng: <tên> ▾".
          Đọc bề rộng bằng JS sẽ làm SSR và trình duyệt khởi tạo khác nhau —
          đúng thứ store đã cố ý bỏ (xem chú thích `rightOpen`). Danh sách bung
          ra luôn liệt kê ĐỦ phiên, nên không bài nào không với tới được. */}
      <div className={`session-more${overflow.length === 0 ? " is-empty" : ""}`}>
        <button
          type="button"
          className="session-more-trigger"
          onClick={() => setListOpen(!listOpen)}
          aria-expanded={listOpen}
          aria-label="Chọn mô phỏng đang mở"
        >
          <span className="session-more-count">+{overflow.length}</span>
          <span className="session-more-current">
            Mô phỏng: {activeIndex >= 0 ? labels[activeIndex] : ""}
          </span>
        </button>
        {listOpen && (
          <ul className="session-more-list">
            {sessions.map((sn, i) => (
              <li key={sn.id} className={sn.id === activeSessionId ? "is-active" : undefined}>
                <button
                  type="button"
                  className="session-more-open"
                  onClick={() => { switchSession(sn.id); setListOpen(false); }}
                >
                  {labels[i]}
                </button>
                <button
                  type="button"
                  className="session-more-close"
                  onClick={() => closeSession(sn.id)}
                  aria-label={`Đóng ${labels[i]}`}
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </nav>
  );
}
