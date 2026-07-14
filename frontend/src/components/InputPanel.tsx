import { useState } from "react";
import { DOMAIN_COLOR, DOMAIN_LABEL, publicCatalog } from "../data/offline-catalog";
import { useAppStore } from "../state/store";
import { IconBack } from "./icons";
import { previewKindOf, SamplePreview } from "./SamplePreview";

/**
 * Panel trái TRONG WORKSPACE (M9-UX4) — MỘT việc duy nhất: **đổi sang bài khác**.
 *
 * Trước M9-UX4 panel này nhồi ba khối vào một cột ~270px: composer đầy đủ (ô nhập
 * + nút tải tệp xuống 2 dòng + nút xanh to) + 12 mẫu + 3 đề "thử phân tích bằng AI".
 * Trang chủ ĐÃ LÀ nơi phân tích đề — giữ thêm một composer ở đây là hai nơi làm
 * cùng một việc, và chính nó là thứ làm cột này chật. Nay: về Trang chủ để nhập đề
 * mới; panel chỉ còn danh mục (có tranh) + bộ lọc.
 *
 * `publicCatalog()` (M9-UX3): học sinh chỉ thấy mẫu Tin học THPT; fixture nội bộ
 * vẫn sống trong `offlineCatalog()` cho test/dev.
 */
export function InputPanel() {
  const activeSampleId = useAppStore((s) => s.activeSampleId);
  const loadEnvelope = useAppStore((s) => s.loadEnvelope);
  const goHome = useAppStore((s) => s.goHome);
  const [filter, setFilter] = useState("");

  const q = filter.trim().toLowerCase();
  const rows = publicCatalog().filter(
    (e) =>
      q === "" ||
      e.title.toLowerCase().includes(q) ||
      DOMAIN_LABEL[e.domain].toLowerCase().includes(q),
  );

  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <button className="panel-home-link" onClick={goHome}>
        <IconBack size={14} />
        Trang chủ · nhập đề bài mới
      </button>

      <section className="card stack" style={{ gap: "var(--sp-sm)" }}>
        <span className="eyebrow">ĐỔI SANG BÀI KHÁC</span>

        <input
          className="panel-filter"
          type="search"
          placeholder="Lọc mô phỏng…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />

        <div className="stack" style={{ gap: 2 }}>
          {rows.map((row) => (
            <button
              key={row.id}
              className={`sample-row${activeSampleId === row.id ? " is-active" : ""}`}
              onClick={() => loadEnvelope(row.envelope, row.id)}
            >
              <SamplePreview kind={previewKindOf(row.simId, row.preview)} />
              <span className="sample-row-body">
                <strong className="sample-row-title">{row.title}</strong>
                {/* nhãn tiếng Việt — KHÔNG lộ simulation_id kĩ thuật */}
                <span className="starter-card-domain">
                  <span className="starter-dot" style={{ background: DOMAIN_COLOR[row.domain] }} />
                  {DOMAIN_LABEL[row.domain]}
                </span>
              </span>
            </button>
          ))}

          {rows.length === 0 && (
            <span className="hint" style={{ padding: "var(--sp-sm) 0" }}>
              Không có mô phỏng nào khớp “{filter}”.
            </span>
          )}
        </div>
      </section>
    </div>
  );
}
