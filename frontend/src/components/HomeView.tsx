import { DOMAIN_COLOR, DOMAIN_LABEL, starterEntries, type CatalogEntry } from "../data/offline-catalog";
import { useAppStore } from "../state/store";
import { ProblemInput } from "./ProblemInput";
import { previewKindOf, SamplePreview } from "./SamplePreview";
import { SessionCard } from "./SessionCard";

/**
 * HOME (M9-UX1 · dọn lại M9-UX5) — trạng thái vào app: MỘT hành động chính.
 *
 * M9-UX5 — HOME KHÔNG BAO GIỜ PHÌNH. Ba thứ bị gỡ vì chúng làm Home to dần theo
 * lượng dữ liệu, đúng thứ khiến nó "rối":
 *   1. Nút "Xem tất cả mô phỏng mẫu (12)" — bung cả danh mục ngay tại chỗ.
 *      Danh mục đầy đủ nay có nhà riêng: `LibraryView` (mục Thư viện trên header).
 *   2. Danh sách "Tiếp tục học" nhiều thẻ — học sinh học dở 30 bài thì gợi ý bị
 *      đẩy khuất. Nay CHỈ MỘT thẻ gần nhất; phần còn lại ở trang Lịch sử.
 *   3. Phụ đề hai dòng + hàng chip "thử đề mẫu AI" — phụ đề trùng ý tiêu đề, còn
 *      3 đề chip thì TRÙNG NỘI DUNG với 3 bài mẫu ngay bên dưới (chỉ khác là tốn
 *      một lượt gọi API). Trang chủ nên có ĐÚNG MỘT đường dùng AI: gõ đề của em.
 *
 * Thứ tự: composer → gợi ý (6 nổi bật) → tiếp tục học (1 thẻ).
 * "Tiếp tục học" nằm DƯỚI gợi ý: Home dẫn bằng khám phá, không dẫn bằng đống bài
 * đang học dở của người dùng cũ.
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

function StarterCard({
  entry,
  onPick,
}: {
  entry: CatalogEntry;
  onPick: (envelope: CatalogEntry["envelope"], sampleId: string) => void;
}) {
  return (
    <button className="starter-card" onClick={() => onPick(entry.envelope, entry.id)}>
      <SamplePreview kind={previewKindOf(entry.simId, entry.preview)} />
      <span className="starter-card-body">
        <strong className="starter-card-title">{entry.title}</strong>
        <span className="starter-card-domain">
          <span className="starter-dot" style={{ background: DOMAIN_COLOR[entry.domain] }} />
          {DOMAIN_LABEL[entry.domain]}
        </span>
      </span>
    </button>
  );
}

export function HomeView() {
  const loadEnvelope = useAppStore((s) => s.loadEnvelope);
  const unsupported = useAppStore((s) => s.unsupported);
  const history = useAppStore((s) => s.history);
  const reopenFromHistory = useAppStore((s) => s.reopenFromHistory);
  const openHistory = useAppStore((s) => s.openHistory);
  const openLibrary = useAppStore((s) => s.openLibrary);

  const starters = starterEntries();
  const latest = history[0] ?? null;

  return (
    <div className="home-view">
      <h1 className="home-title">Em muốn khám phá bài toán nào?</h1>

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
        <div className="home-section-head">
          <h2 className="home-section-title">Gợi ý khám phá</h2>
          <button className="link-btn" onClick={openLibrary}>
            Xem thư viện
          </button>
        </div>
        <div className="starter-grid">
          {starters.map((e) => (
            <StarterCard key={e.id} entry={e} onPick={loadEnvelope} />
          ))}
        </div>
      </section>

      {latest && (
        <section className="home-section">
          <div className="home-section-head">
            <h2 className="home-section-title">Tiếp tục học</h2>
            {history.length > 1 && (
              <button className="link-btn" onClick={openHistory}>
                Xem tất cả ({history.length})
              </button>
            )}
          </div>
          <div className="session-list">
            <SessionCard item={latest} onOpen={() => reopenFromHistory(latest.id)} />
          </div>
        </section>
      )}
    </div>
  );
}
