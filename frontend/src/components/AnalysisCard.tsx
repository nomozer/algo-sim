import type { AnalysisOk } from "../core/types";
import { fmt } from "../core/trace-builder";
import { IconInfo } from "./icons";

const OP_SYMBOL: Record<string, string> = {
  ">": ">",
  ">=": "≥",
  "<": "<",
  "<=": "≤",
  "==": "=",
  "!=": "≠",
};

/**
 * Khối "xác định bài toán" — Input / Output / dữ liệu, đúng SGK.
 *
 * W4B-2B §9 — GỠ HAI THỨ ĐÃ CÓ Ở HEADER WORKSPACE. Panel nay là tuỳ chọn, nên
 * nội dung của nó phải ĐÀO SÂU chứ không chép lại trang chính:
 *
 * - tiêu đề `problem.summary` từng dựng thành `<h2 class="card-title">` ở đây,
 *   trong khi `SimulationWorkspace` đã dựng CHÍNH chuỗi đó thành
 *   `<h2 class="workspace-title">` — `offline-catalog.ts` đặt
 *   `envelope.title = analysis.problem.summary`, nên đó là hai `<h2>` chữ y hệt
 *   nhau trên cùng một màn hình khi mở panel;
 * - hàng "Thuật toán" in `ALGORITHM_NAMES[algorithm_id]`, mà header đã in chính
 *   `mod.title` (= cùng bảng tên đó) VÀ `PseudocodeView` ngay bên dưới còn có
 *   đầu mục "THUẬT TOÁN" — một ý, ba lần, trong một cột hẹp.
 *
 * Giữ lại đúng phần header KHÔNG nói: Input, Output, dữ liệu cụ thể.
 */
export function AnalysisCard({ analysis }: { analysis: AnalysisOk }) {
  const { problem, data } = analysis;
  return (
    <section className="card">
      <span className="eyebrow">XÁC ĐỊNH BÀI TOÁN</span>
      <div className="analysis-grid" style={{ marginTop: "var(--sp-sm)" }}>
        <span className="analysis-label">Input</span>
        <span>{problem.input}</span>
        <span className="analysis-label">Output</span>
        <span>{problem.output}</span>
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
          <IconInfo size={14} /> Đề không cho số liệu cụ thể — dữ liệu mẫu do hệ thống sinh ra để mô phỏng.
        </p>
      )}
      {analysis.notes && <p className="notes">{analysis.notes}</p>}
    </section>
  );
}
