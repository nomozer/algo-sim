import { useState } from "react";
import { DOMAIN_COLOR, DOMAIN_LABEL, offlineCatalog, starterEntries } from "../data/offline-catalog";
import { useAppStore } from "../state/store";
import { ProblemInput } from "./ProblemInput";

/**
 * HOME (M9-UX1) — trạng thái vào app: MỘT hành động chính rõ ràng.
 *
 * Nguyên tắc: học sinh không cần hiểu kiến trúc AlgoSim trước khi dùng.
 * Không inspector rỗng, không timeline rỗng, không panel thừa — chỉ:
 *   composer (phân tích đề) → gợi ý khám phá (bộ nhỏ) → tiếp tục học (gần đây).
 * Toàn bộ mục "gần đây" mở lại bằng envelope đã validate — KHÔNG gọi AI.
 */

export function formatRelativeTime(ts: number, nowMs = Date.now()): string {
  const s = Math.max(0, Math.floor((nowMs - ts) / 1000));
  if (s < 60) return "vừa xong";
  const m = Math.floor(s / 60);
  if (m < 60) return `${m} phút trước`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h} giờ trước`;
  const d = Math.floor(h / 24);
  if (d < 7) return `${d} ngày trước`;
  return new Date(ts).toLocaleDateString("vi-VN");
}

const RECENT_ON_HOME = 5;

export function HomeView() {
  const loadEnvelope = useAppStore((s) => s.loadEnvelope);
  const unsupported = useAppStore((s) => s.unsupported);
  const history = useAppStore((s) => s.history);
  const reopenFromHistory = useAppStore((s) => s.reopenFromHistory);
  const openHistory = useAppStore((s) => s.openHistory);
  const [showAll, setShowAll] = useState(false);

  const starters = starterEntries();
  const all = offlineCatalog();
  const recents = history.slice(0, RECENT_ON_HOME);

  return (
    <div className="home-view">
      <div className="home-hero">
        <h1 className="home-title">Em muốn khám phá bài toán nào?</h1>
        <p className="home-subtitle">
          Nhập một bài toán Tin học để AlgoSim phân tích và tạo mô phỏng phù hợp — hoặc chọn
          một mô phỏng mẫu bên dưới để chạy ngay.
        </p>
      </div>

      <div className="home-composer">
        <ProblemInput />
        {unsupported && (
          <section className="card" role="status">
            <span className="eyebrow">NGOÀI DANH MỤC MÔ PHỎNG</span>
            <p style={{ marginTop: "var(--sp-sm)" }}>{unsupported.reason}</p>
            <p className="notes">
              Danh mục mô phỏng sẽ được mở rộng dần — em có thể thử một bài mẫu bên dưới.
            </p>
          </section>
        )}
      </div>

      <section className="home-section">
        <h2 className="home-section-title">Gợi ý khám phá</h2>
        <div className="starter-grid">
          {(showAll ? all : starters).map((e) => (
            <button
              key={e.id}
              className="starter-card"
              onClick={() => loadEnvelope(e.envelope, e.id)}
            >
              <span className="sample-dot" style={{ background: DOMAIN_COLOR[e.domain] }} />
              <span className="starter-card-body">
                <strong>{e.title}</strong>
                <span className="hint">{DOMAIN_LABEL[e.domain]}</span>
              </span>
            </button>
          ))}
        </div>
        <button className="btn-utility home-see-all" onClick={() => setShowAll(!showAll)}>
          {showAll ? "Thu gọn gợi ý" : `Xem tất cả mô phỏng mẫu (${all.length})`}
        </button>
      </section>

      {recents.length > 0 && (
        <section className="home-section">
          <h2 className="home-section-title">Tiếp tục học</h2>
          <div className="recent-grid">
            {recents.map((item) => (
              <button
                key={item.id}
                className="recent-card"
                onClick={() => reopenFromHistory(item.id)}
                title="Mở lại — không gọi AI"
              >
                <strong className="recent-title">{item.title}</strong>
                <span className="hint">
                  {DOMAIN_LABEL[item.domain as keyof typeof DOMAIN_LABEL] ?? item.domain}
                  {item.lastCursor !== null && item.lastCursor > 0 && (
                    <> · đang ở bước {item.lastCursor + 1}</>
                  )}
                </span>
                <span className="hint">{formatRelativeTime(item.lastViewedAt)}</span>
              </button>
            ))}
          </div>
          {history.length > recents.length && (
            <button className="btn-utility home-see-all" onClick={openHistory}>
              Xem tất cả lịch sử ({history.length})
            </button>
          )}
        </section>
      )}
    </div>
  );
}
