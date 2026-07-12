import { SAMPLES } from "../data/samples";
import { OFFLINE_SAMPLES, SAMPLE_PROMPTS } from "../data/sim-samples";
import { fromLegacyAnalysis, toSimulationId } from "../simulations/legacy";
import type { Domain } from "../simulations/types";
import { useAppStore } from "../state/store";
import { ProblemInput } from "./ProblemInput";

/** Chấm màu theo domain — trang trí (sticker palette). */
const DOMAIN_COLOR: Record<Domain, string> = {
  algorithm: "var(--accent-green)",
  logic: "var(--accent-purple-deep)",
  binary: "var(--primary)",
  network: "var(--accent-pink)",
  database: "var(--accent-teal)",
  web: "var(--accent-orange)",
  geometry: "var(--secondary)",
  generic: "var(--accent-orange-deep)",
};

interface OfflineRow {
  id: string;
  title: string;
  simId: string;
  domain: Domain;
  load: () => void;
}

/**
 * Panel trái: nhập đề + hai nhóm mẫu tách bạch —
 * "Chạy ngay" (envelope offline, không cần AI) vs "Thử phân tích bằng AI"
 * (đề đưa qua pipeline thật analyze→classify→simulate→validate, M5 §8).
 */
export function InputPanel() {
  const activeSampleId = useAppStore((s) => s.activeSampleId);
  const loadEnvelope = useAppStore((s) => s.loadEnvelope);
  const setProblemText = useAppStore((s) => s.setProblemText);

  const offlineRows: OfflineRow[] = [
    ...SAMPLES.map((s) => ({
      id: s.id,
      title: s.analysis.problem.summary,
      simId: toSimulationId(s.algorithmId),
      domain: "algorithm" as Domain,
      load: () => loadEnvelope(fromLegacyAnalysis(s.analysis), s.id),
    })),
    ...OFFLINE_SAMPLES.map((s) => ({
      id: s.id,
      title: s.envelope.title,
      simId: s.envelope.simulation_id,
      domain: s.envelope.domain,
      load: () => loadEnvelope(s.envelope, s.id),
    })),
  ];

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
                <span className="hint">{row.simId}</span>
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
