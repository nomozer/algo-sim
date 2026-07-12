import type { WorkspaceProps } from "../../types";
import {
  binaryString,
  decimalOf,
  placeValues,
  type BinaryConfig,
  type BinaryState,
} from "./model";

/**
 * UI domain binary — bit toggle + trọng số + giá trị thập phân cập nhật tức thì.
 * Không array/pseudocode (M5 §7): inspector riêng cho bit/weight/decimal.
 */

type Props = WorkspaceProps<BinaryConfig, BinaryState>;

const CELL = 60;
const GAP = 12;

export function BinaryWorkspace({ state, dispatch }: Props) {
  const pv = placeValues(state.bitWidth);
  const n = state.bits.length;
  const width = n * CELL + (n - 1) * GAP;
  const decimal = decimalOf(state);

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div className="sim-stage" style={{ padding: "var(--sp-md) 0" }}>
        <svg viewBox={`0 0 ${width} 150`} width="100%" style={{ maxWidth: width, display: "block", margin: "0 auto" }}>
          {state.bits.map((bit, i) => {
            const x = i * (CELL + GAP);
            return (
              <g key={i} style={{ cursor: "pointer" }} onClick={() => dispatch({ type: "toggle", target: String(i) })}>
                <text x={x + CELL / 2} y={20} textAnchor="middle" fontSize={13} fontWeight={600} fill="var(--ink-muted)">
                  {pv[i]}
                </text>
                <rect
                  x={x}
                  y={32}
                  width={CELL}
                  height={CELL}
                  rx={8}
                  fill={bit === 1 ? "var(--primary)" : "var(--canvas-soft)"}
                  stroke={bit === 1 ? "var(--primary)" : "var(--hairline)"}
                  strokeWidth={2}
                  style={{ transition: "fill 0.15s ease" }}
                />
                <text
                  x={x + CELL / 2}
                  y={72}
                  textAnchor="middle"
                  fontSize={24}
                  fontWeight={700}
                  fill={bit === 1 ? "#fff" : "var(--ink-faint)"}
                >
                  {bit}
                </text>
                <text x={x + CELL / 2} y={110} textAnchor="middle" fontSize={11} fill="var(--ink-faint)">
                  {bit === 1 ? `+${pv[i]}` : "0"}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
      <div className="narration-bar">
        Bấm vào từng bit để bật/tắt. Nhị phân <strong>{binaryString(state)}</strong> = {decimal} (hệ thập phân).
      </div>
    </div>
  );
}

export function BinaryInspector({ state }: Props) {
  const pv = placeValues(state.bitWidth);
  const active = pv.filter((_, i) => state.bits[i] === 1);
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <section className="card" style={{ padding: "var(--sp-md)" }}>
        <span className="eyebrow">GIÁ TRỊ</span>
        <div className="analysis-grid" style={{ marginTop: "var(--sp-sm)" }}>
          <span className="analysis-label">Thập phân</span>
          <span>
            <strong>{decimalOf(state)}</strong>
          </span>
          <span className="analysis-label">Nhị phân</span>
          <span style={{ fontFamily: "ui-monospace, monospace" }}>{binaryString(state)}</span>
          <span className="analysis-label">Số bit</span>
          <span>{state.bitWidth}</span>
          <span className="analysis-label">Trọng số</span>
          <span>{pv.join(" · ")}</span>
          <span className="analysis-label">Bit đang bật</span>
          <span>{active.length ? active.join(" + ") + " = " + decimalOf(state) : "(không có)"}</span>
        </div>
      </section>
    </div>
  );
}
