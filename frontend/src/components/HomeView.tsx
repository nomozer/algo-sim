import { useState } from "react";
import {
  DOMAIN_COLOR,
  DOMAIN_LABEL,
  publicCatalog,
  starterEntries,
  type CatalogEntry,
} from "../data/offline-catalog";
import type { Domain } from "../simulations/types";
import { useAppStore } from "../state/store";
import { ProblemInput } from "./ProblemInput";
import { previewKindOf, SamplePreview } from "./SamplePreview";

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

/** Thứ tự nhóm khi mở "xem tất cả" — bám chương trình, không bám bảng chữ cái. */
const GROUP_ORDER: Domain[] = [
  "algorithm",
  "binary",
  "network",
  "logic",
  "web",
  "database",
  "geometry",
  "generic",
];

function groupByDomain(entries: CatalogEntry[]): [Domain, CatalogEntry[]][] {
  const byDomain = new Map<Domain, CatalogEntry[]>();
  for (const e of entries) {
    const bucket = byDomain.get(e.domain);
    if (bucket) bucket.push(e);
    else byDomain.set(e.domain, [e]);
  }
  return GROUP_ORDER.filter((d) => byDomain.has(d)).map((d) => [d, byDomain.get(d)!]);
}

/**
 * Card gợi ý (M9-UX3) — HÀNG NGANG: tranh nhỏ bên trái, chữ bên phải.
 * Trước đây tranh nằm trên, chữ dưới → tiêu đề dài ngắn khác nhau làm card cao
 * thấp so le, lưới bị gãy. Hàng ngang thì chiều cao do tranh quyết định, không
 * do độ dài tiêu đề — mọi card bằng nhau.
 */
function StarterCard({
  entry,
  onPick,
  showDomain = true,
}: {
  entry: CatalogEntry;
  onPick: (envelope: CatalogEntry["envelope"], sampleId: string) => void;
  /** Trong chế độ GOM NHÓM, tiêu đề nhóm đã nói domain rồi — lặp lại ở từng
      card là nhiễu thuần tuý (nguyên tắc coherence, COVERAGE §2). */
  showDomain?: boolean;
}) {
  return (
    <button className="starter-card" onClick={() => onPick(entry.envelope, entry.id)}>
      <SamplePreview kind={previewKindOf(entry.simId, entry.preview)} />
      <span className="starter-card-body">
        <strong className="starter-card-title">{entry.title}</strong>
        {showDomain && (
          <span className="starter-card-domain">
            <span className="starter-dot" style={{ background: DOMAIN_COLOR[entry.domain] }} />
            {DOMAIN_LABEL[entry.domain]}
          </span>
        )}
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
  const [showAll, setShowAll] = useState(false);

  // M9-UX2: học sinh chỉ thấy danh mục CÔNG KHAI (Tin học THPT) —
  // fixture nội bộ vẫn sống cho test/dev qua offlineCatalog().
  const starters = starterEntries();
  const all = publicCatalog();
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
        <ProblemInput variant="hero" />
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

        {showAll ? (
          // Mở rộng: GOM NHÓM theo chủ đề — 12 card phẳng đổ một lượt là bức tường,
          // học sinh không có mỏ neo nào để định vị mình đang xem phần nào.
          groupByDomain(all).map(([domain, entries]) => (
            <div key={domain} className="starter-group">
              <h3 className="starter-group-title">
                <span className="starter-dot" style={{ background: DOMAIN_COLOR[domain] }} />
                {DOMAIN_LABEL[domain]}
              </h3>
              <div className="starter-grid">
                {entries.map((e) => (
                  <StarterCard key={e.id} entry={e} onPick={loadEnvelope} showDomain={false} />
                ))}
              </div>
            </div>
          ))
        ) : (
          <div className="starter-grid">
            {starters.map((e) => (
              <StarterCard key={e.id} entry={e} onPick={loadEnvelope} />
            ))}
          </div>
        )}

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
                <span className="recent-foot">
                  <span className="hint">{formatRelativeTime(item.lastViewedAt)}</span>
                  <span className="recent-continue">Tiếp tục ▸</span>
                </span>
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
