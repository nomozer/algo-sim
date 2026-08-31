import { useState } from "react";
import {
  DOMAIN_COLOR,
  DOMAIN_LABEL,
  publicCatalog,
  type CatalogEntry,
} from "../data/offline-catalog";
import type { Domain } from "../simulations/types";
import { useAppStore } from "../state/store";
import { IconSearch } from "./icons";
import { previewKindOf, SamplePreview } from "./SamplePreview";

/**
 * THƯ VIỆN (M9-UX5) — nhà riêng của danh mục mô phỏng ĐẦY ĐỦ.
 *
 * Vì sao tách khỏi Home: Home từng bung cả 12 mẫu tại chỗ ("Xem tất cả mô phỏng
 * mẫu") và liệt kê mọi bài đang học dở. Học sinh học dở nhiều bài thì gợi ý bị
 * đẩy xuống, và Home phình theo lịch sử. Tách ra thì Home KHÔNG BAO GIỜ phình —
 * nó luôn là composer + 6 gợi ý nổi bật + 1 thẻ tiếp tục, bất kể học bao nhiêu.
 *
 * `publicCatalog()` — người dùng chỉ thấy mẫu thuộc `PRODUCT_DOMAINS` (hình
 * học); mẫu của đề cũ và fixture nội bộ vẫn sống trong `offlineCatalog()` cho
 * test/dev/regression (luật phạm vi M9-UX2/UX3).
 */

/** Thứ tự nhóm — bám chương trình, không bám bảng chữ cái. */
/**
 * Thứ tự nhóm trong Thư viện — CỐ Ý theo mạch sư phạm, không theo bảng chữ cái.
 *
 * W4B-3D — DANH SÁCH NÀY LÀ BỘ LỌC, NÊN THIẾU MỘT MIỀN LÀ MẤT BÀI KHÔNG BÁO.
 * `groupByDomain` chỉ giữ những miền có mặt ở đây, nên khi `tree` bị bỏ quên,
 * mẫu công khai của `tree.traversal` render vào KHÔNG nhóm nào và biến mất khỏi
 * Thư viện — im lặng, không lỗi. Chỉ lộ ra khi miền đó có mẫu công khai đầu
 * tiên. `library-domain-coverage` khoá: mọi `Domain` phải có mặt ở đây.
 */
export const GROUP_ORDER: Domain[] = [
  // Hình học đứng đầu vì nó LÀ sản phẩm (`PRODUCT_DOMAINS`). Chín miền dưới
  // hiện không có mẫu công khai nào nên không nhóm nào dựng ra — nhưng vẫn
  // phải liệt kê: danh sách này là BỘ LỌC, thiếu một miền là mất bài không
  // báo, và bài từ Lịch sử hay từ giáo viên giao vẫn thuộc các miền ấy.
  "geometry",
  "algorithm",
  "binary",
  "network",
  "tree",
  "logic",
  "web",
  "color",
  "database",
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

export function LibraryView() {
  const loadEnvelope = useAppStore((s) => s.loadEnvelope);
  const [filter, setFilter] = useState("");

  const q = filter.trim().toLowerCase();
  const all = publicCatalog().filter(
    (e) =>
      q === "" ||
      e.title.toLowerCase().includes(q) ||
      DOMAIN_LABEL[e.domain].toLowerCase().includes(q),
  );
  const groups = groupByDomain(all);

  return (
    <div className="library-view">
      <div className="library-head">
        <div>
          <h1 className="page-title">Thư viện mô phỏng</h1>
          <p className="hint">
            {publicCatalog().length} bài hình học không gian — mở ra chạy ngay, không cần AI.
          </p>
        </div>
        <label className="library-search">
          <IconSearch size={15} />
          <input
            type="search"
            placeholder="Tìm mô phỏng…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </label>
      </div>

      {groups.length === 0 ? (
        <div className="empty-state">
          <p>Không có mô phỏng nào khớp “{filter}”.</p>
        </div>
      ) : (
        groups.map(([domain, entries]) => (
          <section key={domain} className="starter-group">
            <h2 className="starter-group-title">
              <span className="starter-dot" style={{ background: DOMAIN_COLOR[domain] }} />
              {DOMAIN_LABEL[domain]}
            </h2>
            <div className="starter-grid">
              {entries.map((e) => (
                <button
                  key={e.id}
                  className="starter-card"
                  onClick={() => loadEnvelope(e.envelope, e.id)}
                >
                  <SamplePreview kind={previewKindOf(e.simId, e.preview)} />
                  <span className="starter-card-body">
                    <strong className="starter-card-title">{e.title}</strong>
                  </span>
                </button>
              ))}
            </div>
          </section>
        ))
      )}
    </div>
  );
}
