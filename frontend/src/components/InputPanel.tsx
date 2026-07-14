import { SAMPLE_PROMPTS } from "../data/sim-samples";
import { DOMAIN_COLOR, DOMAIN_LABEL, publicCatalog } from "../data/offline-catalog";
import { useAppStore } from "../state/store";
import { ProblemInput } from "./ProblemInput";

/**
 * Panel trái TRONG WORKSPACE: nhập đề + hai nhóm mẫu tách bạch —
 * "Chạy ngay" (envelope offline, không cần AI) vs "Thử phân tích bằng AI"
 * (đề đưa qua pipeline thật analyze→classify→simulate→validate, M5 §8).
 * M9-UX1: danh mục lấy từ offline-catalog dùng chung với HomeView.
 *
 * M9-UX3 — `publicCatalog()`, KHÔNG phải `offlineCatalog()`. Luật phạm vi M9-UX2
 * ("danh mục công khai khoanh trong Tin học THPT") phải áp ở MỌI bề mặt học sinh
 * thấy, không riêng Home: panel này từng đổ cả fixture nội bộ (tam giác, 3 bản
 * "(tổng quát)") ra cho học sinh, kèm chuỗi kĩ thuật `algorithm.find_max` làm phụ
 * đề. Fixture KHÔNG mất — `offlineCatalog()` vẫn còn nguyên cho test/dev, và lịch
 * sử mở lại bằng envelope nên không phụ thuộc danh mục (bất biến #17).
 */
export function InputPanel() {
  const activeSampleId = useAppStore((s) => s.activeSampleId);
  const loadEnvelope = useAppStore((s) => s.loadEnvelope);
  const setProblemText = useAppStore((s) => s.setProblemText);

  const offlineRows = publicCatalog().map((e) => ({
    ...e,
    load: () => loadEnvelope(e.envelope, e.id),
  }));

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <ProblemInput />

      <section className="card stack" style={{ gap: "var(--sp-sm)" }}>
        <span className="eyebrow">CHẠY NGAY — KHÔNG CẦN AI</span>
        <div className="stack" style={{ gap: 2 }}>
          {offlineRows.map((row) => (
            <button
              key={row.id}
              className={`sample-row${activeSampleId === row.id ? " is-active" : ""}`}
              onClick={() => {
                setProblemText("");
                row.load();
              }}
            >
              <span className="sample-dot" style={{ background: DOMAIN_COLOR[row.domain] }} />
              <span>
                <strong style={{ fontWeight: 600 }}>{row.title}</strong>
                <br />
                {/* nhãn domain tiếng Việt — KHÔNG lộ simulation_id kĩ thuật */}
                <span className="hint">{DOMAIN_LABEL[row.domain]}</span>
              </span>
            </button>
          ))}
        </div>
      </section>

      <section className="card stack" style={{ gap: "var(--sp-sm)" }}>
        <span className="eyebrow">THỬ PHÂN TÍCH BẰNG AI</span>
        <span className="hint">
          Điền đề vào ô trên rồi bấm <strong>Phân tích đề bằng AI</strong> — đề đi qua pipeline
          thật (phân tích → phân loại → sinh cấu hình → kiểm tra).
        </span>
        <div className="stack" style={{ gap: 2 }}>
          {SAMPLE_PROMPTS.map((p) => (
            <button key={p.id} className="sample-row" onClick={() => setProblemText(p.text)}>
              <span className="sample-dot" style={{ background: "var(--ink-faint)" }} />
              <span>
                <strong style={{ fontWeight: 600 }}>{p.label}</strong>
                <br />
                <span className="hint">{p.text}</span>
              </span>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
