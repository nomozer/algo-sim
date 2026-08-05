/**
 * StageLegend — CHÚ GIẢI SÂN KHẤU DÙNG CHUNG (UI-CLARITY W1).
 *
 * Vì sao có file này: đo tại `main@1c9f9d5` thấy chú giải chỉ thường trực ở
 * **4/22 target**, và markup `<p class="stage-legend">` bị chép tay ở 5 module.
 * Cùng lúc, cùng một màu mang nghĩa khác nhau giữa các bài (xanh lá = "đã đếm
 * vào" ở `count_if` nhưng = "tín hiệu 1" ở `boolean_dag`), nên quy ước màu chỉ
 * tồn tại trong đầu người viết code.
 *
 * Component này KHÔNG áp nghĩa — nghĩa thuộc về từng family. Nó chỉ đảm bảo
 * mọi sân khấu nói ra quy ước **theo cùng một hình thức**, và mỗi ô mẫu luôn đi
 * kèm NHÃN CHỮ (`global.css`: "màu KHÔNG BAO GIỜ là tín hiệu duy nhất").
 *
 * Danh sách rỗng → không render gì: target không dùng trạng thái nào thì không
 * bịa ra chú giải rỗng (chống affordance rỗng, `ARCHITECTURE_MAP §7`).
 */

/** Ô mẫu — tên tone khớp lớp CSS `.stage-legend .dot.is-<tone>`. */
export type LegendTone =
  | "scan"
  | "done"
  | "eliminated"
  | "considering"
  | "bound"
  | "idle"
  | "gap"
  | "unknown"
  | "frontier"
  | "current";

export interface LegendItem {
  tone: LegendTone;
  label: string;
}

export function StageLegend({ items }: { items: LegendItem[] }) {
  if (items.length === 0) return null;
  return (
    <p className="stage-legend">
      {items.map((it) => (
        <span key={`${it.tone}-${it.label}`}>
          <i className={`dot is-${it.tone}`} /> {it.label}
        </span>
      ))}
    </p>
  );
}
