import {
  geometryShapeLabel,
  publicCatalog,
  starterEntries,
  type CatalogEntry,
} from "../data/offline-catalog";
import { useAppStore } from "../state/store";
import { ProblemInput } from "./ProblemInput";
import { SamplePreview } from "./SamplePreview";
import { SessionCard } from "./SessionCard";

/**
 * Trang chủ Axo V2.7 (Phase B — Full UI Replacement).
 *
 * Chuyển nguyên vẹn cấu trúc từ `#view-home` của `axo-unified-ui-v2-7-composer-validation-divider-review.html`:
 * - `.home-page-container` (max-width: 1120px, padding: 28px 24px 48px, gap: 28px)
 * - `.hero-composer-zone`: `.hero-title` + `.hero-sub` + `.composer-card`
 * - `.home-section` (Gợi ý khám phá): `.home-sec-bar` + `.starter-grid` (4 `.starter-card`)
 * - `.home-section#home-resume-section` (Tiếp tục học): `.home-sec-bar` + `.resume-home-card`
 */

const DAY_MS = 86_400_000;

/** Hàm thuần — test được với mốc `now` cố định, không lệ thuộc đồng hồ thật. */
export function formatRelativeTime(ts: number, now: number = Date.now()): string {
  const diff = Math.max(0, now - ts);
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "vừa xong";
  if (mins < 60) return `${mins} phút trước`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.floor(diff / DAY_MS);
  if (days === 1) return "hôm qua";
  if (days < 7) return `${days} ngày trước`;
  const d = new Date(ts);
  return `${d.getDate()}/${d.getMonth() + 1}`;
}

export function HomeView() {
  const history = useAppStore((s) => s.history);
  const reopenFromHistory = useAppStore((s) => s.reopenFromHistory);
  const openHistory = useAppStore((s) => s.openHistory);
  const openLibrary = useAppStore((s) => s.openLibrary);
  const loadEnvelope = useAppStore((s) => s.loadEnvelope);

  const starters = starterEntries();
  const totalPublic = publicCatalog().length;
  const latest = history[0] ?? null;

  const openSample = (entry: CatalogEntry) => {
    loadEnvelope(entry.envelope, entry.id);
  };

  return (
    <div className="page-container home-container" id="view-home">
      <section className="home-hero" aria-label="Nhập đề bài hình học">
        <h1 className="home-hero-title">Em muốn dựng hình nào?</h1>
        <div className="home-composer">
          <ProblemInput />
        </div>
      </section>

      <section className="home-section" aria-label="Gợi ý khám phá">
        <div className="home-sec-bar">
          <h2 className="home-sec-title">Gợi ý khám phá</h2>
          <button
            type="button"
            className="btn-sec-link"
            id="btn-home-to-library"
            onClick={openLibrary}
          >
            {`Xem tất cả thư viện (${totalPublic}) →`}
          </button>
        </div>

        <div className="starter-grid" id="home-starter-grid">
          {starters.map((s) => {
            const shapeLabel = geometryShapeLabel(s.id);
            return (
              <button
                key={s.id}
                type="button"
                className="starter-card"
                data-starter-prob={s.id}
                onClick={() => openSample(s)}
                aria-label={`Mở mẫu: ${s.title} (${shapeLabel})`}
              >
                <div className="starter-thumb" aria-hidden="true">
                  <SamplePreview sampleId={s.id} category={shapeLabel} />
                </div>
                <span className="starter-cat">{shapeLabel}</span>
                <span className="starter-title">{s.title}</span>
              </button>
            );
          })}
        </div>
      </section>

      {latest && (
        <section className="home-section" id="home-resume-section" aria-label="Tiếp tục học">
          <div className="home-sec-bar">
            <h2 className="home-sec-title">Tiếp tục học</h2>
            <button
              type="button"
              className="btn-sec-link"
              id="btn-home-to-history"
              onClick={openHistory}
            >
              Xem lịch sử →
            </button>
          </div>
          <SessionCard item={latest} onOpen={() => reopenFromHistory(latest.id)} />
        </section>
      )}
    </div>
  );
}
