import type { Step } from "../core/types";
import { fmt } from "../core/trace-builder";

const VAR_LABELS: Record<string, string> = {
  max: "max",
  min: "min",
  vt: "vị trí",
  tong: "tổng",
  dem: "đếm",
  can_tim: "cần tìm",
  i: "i",
  trai: "trái",
  phai: "phải",
  giua: "giữa",
  luot: "lượt",
  gia_tri_chen: "giá trị chèn",
};

/**
 * W2C-VR4 — biến luận lý hiển thị bằng TIẾNG VIỆT ("đúng"/"sai"), khớp với mã
 * giả và thuyết minh. Trước đó chip hiện `true`/`false` trong khi cùng màn hình
 * mã giả viết "đúng"/"sai" — hai chữ khác nhau cho cùng một giá trị.
 * Chỉ luồng điều khiển hữu hạn đưa boolean vào `vars`, nên đổi ở đây không làm
 * trôi cách hiển thị của các domain khác (chúng chỉ dùng số/chuỗi).
 */
export function formatVarValue(value: number | string | boolean | null): string {
  if (typeof value === "boolean") return value ? "đúng" : "sai";
  if (typeof value === "number") return fmt(value);
  return String(value ?? "—");
}

/** Hộp giá trị các biến của thuật toán — nháy sáng biến vừa được gán. */
export function VarsView({ step }: { step: Step }) {
  const entries = Object.entries(step.snapshot.vars);
  if (entries.length === 0) return null;

  const justAssigned = new Set(
    step.events.filter((e) => e.type === "assign_var").map((e) => e.name),
  );

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--sp-xs)" }}>
      {entries.map(([name, value]) => {
        const hot = justAssigned.has(name);
        return (
          <div
            key={name}
            style={{
              display: "inline-flex",
              alignItems: "baseline",
              gap: 6,
              border: `1px solid ${hot ? "var(--primary)" : "var(--hairline)"}`,
              background: hot ? "#e8f2fd" : "var(--surface)",
              borderRadius: "var(--rounded-md)",
              padding: "4px 12px",
              fontSize: 14,
              transition: "background 0.2s ease, border-color 0.2s ease",
            }}
          >
            <span style={{ color: "var(--ink-muted)", fontSize: 12, fontWeight: 600 }}>
              {VAR_LABELS[name] ?? name}
            </span>
            <span style={{ fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>
              {formatVarValue(value)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
