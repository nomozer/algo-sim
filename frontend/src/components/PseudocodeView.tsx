import type { AlgorithmId } from "../core/types";
import { PSEUDOCODE } from "../core/pseudocode";

/**
 * Panel mã giả: hiện thuật toán dạng liệt kê bước (kiểu SGK),
 * highlight dòng đang thực hiện theo Step.line — cho học sinh thấy
 * "thuật toán đang đứng ở câu lệnh nào".
 */
export function PseudocodeView({
  algorithmId,
  lines: linesProp,
  currentLine,
}: {
  /** Tra bảng PSEUDOCODE tĩnh theo thuật toán (8 bài chuyên biệt). */
  algorithmId?: AlgorithmId;
  /** M12: mã giả DẪN XUẤT (vd từ ScanSpec) — truyền thẳng, ưu tiên hơn tra bảng. */
  lines?: string[];
  currentLine?: number;
}) {
  const lines = linesProp ?? (algorithmId ? PSEUDOCODE[algorithmId] : []);
  return (
    <div className="pseudo-panel">
      <div className="pseudo-title">THUẬT TOÁN</div>
      {lines.map((text, idx) => (
        <div
          key={idx}
          className={`pseudo-line${currentLine === idx + 1 ? " is-current" : ""}`}
        >
          <span className="pseudo-no">{idx + 1}</span>
          <span className="pseudo-text">{text}</span>
        </div>
      ))}
    </div>
  );
}
