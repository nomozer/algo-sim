import type { AnalysisOk } from "../core/types";
import { ALGORITHM_NAMES } from "../core/types";
import { fmt } from "../core/trace-builder";

const OP_SYMBOL: Record<string, string> = {
  ">": ">",
  ">=": "≥",
  "<": "<",
  "<=": "≤",
  "==": "=",
  "!=": "≠",
};

/** Khối "xác định bài toán" — Input / Output / thuật toán, đúng SGK. */
export function AnalysisCard({ analysis }: { analysis: AnalysisOk }) {
  const { problem, data } = analysis;
  return (
    <section className="card">
      <span className="eyebrow">XÁC ĐỊNH BÀI TOÁN</span>
      <h2 className="card-title" style={{ marginTop: "var(--sp-sm)" }}>
        {problem.summary}
      </h2>
      <div className="analysis-grid">
        <span className="analysis-label">Input</span>
        <span>{problem.input}</span>
        <span className="analysis-label">Output</span>
        <span>{problem.output}</span>
        <span className="analysis-label">Thuật toán</span>
        <span>
          <strong>{ALGORITHM_NAMES[analysis.algorithm_id]}</strong>{" "}
          <code
            style={{
              fontSize: 13,
              color: "var(--ink-muted)",
              background: "var(--canvas-soft)",
              borderRadius: "var(--rounded-xs)",
              padding: "1px 6px",
            }}
          >
            {analysis.algorithm_id}
          </code>
        </span>
        <span className="analysis-label">Dữ liệu</span>
        <span style={{ fontVariantNumeric: "tabular-nums" }}>
          [{data.array.map(fmt).join("; ")}]
          {data.target !== null && (
            <>
              {" — "}cần tìm: <strong>{fmt(data.target)}</strong>
            </>
          )}
          {data.condition && (
            <>
              {" — "}điều kiện: <strong>{OP_SYMBOL[data.condition.op]} {fmt(data.condition.value)}</strong>
            </>
          )}
          {data.order && (
            <>
              {" — "}thứ tự: <strong>{data.order === "asc" ? "tăng dần" : "giảm dần"}</strong>
            </>
          )}
        </span>
      </div>
      {analysis.data_generated && (
        <p className="notes">
          ⚠ Đề không cho số liệu cụ thể — dữ liệu mẫu do hệ thống sinh ra để mô phỏng.
        </p>
      )}
      {analysis.notes && <p className="notes">{analysis.notes}</p>}
    </section>
  );
}
