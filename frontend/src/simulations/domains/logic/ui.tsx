import type { WorkspaceProps } from "../../types";
import { AND_RULE, andOutput, type Bit, type LogicConfig, type LogicState } from "./model";

/**
 * UI domain logic — cổng AND. Chỉ đọc state + phát toggle qua dispatch.
 * Không pseudocode/array/variables (M5 §7) — inspector riêng: truth table.
 */

type Props = WorkspaceProps<LogicConfig, LogicState>;

const ON = "var(--accent-green)";
const OFF = "var(--hairline)";
const WIRE_ON = "var(--accent-green)";
const WIRE_OFF = "var(--ink-faint)";

function Switch({ label, value, y, onToggle }: { label: string; value: Bit; y: number; onToggle: () => void }) {
  return (
    <g style={{ cursor: "pointer" }} onClick={onToggle}>
      <rect x={16} y={y - 18} width={64} height={36} rx={18} fill={value === 1 ? ON : OFF} />
      <circle cx={value === 1 ? 62 : 34} cy={y} r={14} fill="#fff" />
      <text x={48} y={y - 28} textAnchor="middle" fontSize={13} fontWeight={600} fill="var(--ink)">
        {label} = {value}
      </text>
    </g>
  );
}

export function LogicWorkspace({ state, dispatch }: Props) {
  const out = andOutput(state);
  const wireA = state.inputA === 1 ? WIRE_ON : WIRE_OFF;
  const wireB = state.inputB === 1 ? WIRE_ON : WIRE_OFF;
  const wireOut = out === 1 ? WIRE_ON : WIRE_OFF;

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div className="sim-stage">
        <svg viewBox="0 0 460 240" width="100%" style={{ maxWidth: 460, display: "block", margin: "0 auto" }}>
          {/* Dây từ hai công tắc vào cổng */}
          <path d="M80 70 H180 V96 H210" fill="none" stroke={wireA} strokeWidth={3} />
          <path d="M80 170 H180 V144 H210" fill="none" stroke={wireB} strokeWidth={3} />
          {/* Cổng AND (hình chữ D) */}
          <path
            d="M210 80 H250 A40 40 0 0 1 250 160 H210 Z"
            fill="var(--surface)"
            stroke="var(--primary)"
            strokeWidth={2.5}
          />
          <text x={244} y={126} textAnchor="middle" fontSize={15} fontWeight={700} fill="var(--primary)">
            AND
          </text>
          {/* Dây ra bóng đèn */}
          <path d="M290 120 H360" fill="none" stroke={wireOut} strokeWidth={3} />
          {/* Bóng đèn output */}
          <circle
            cx={392}
            cy={120}
            r={26}
            fill={out === 1 ? "var(--accent-green)" : "var(--canvas-soft)"}
            stroke={out === 1 ? "var(--accent-green)" : "var(--hairline)"}
            strokeWidth={2}
            style={{ transition: "fill 0.2s ease" }}
          />
          <text x={392} y={126} textAnchor="middle" fontSize={18} fontWeight={700} fill={out === 1 ? "#fff" : "var(--ink-muted)"}>
            {out}
          </text>
          <text x={392} y={168} textAnchor="middle" fontSize={12} fill="var(--ink-muted)">
            Đầu ra
          </text>

          <Switch label="A" value={state.inputA} y={70} onToggle={() => dispatch({ type: "toggle", target: "A" })} />
          <Switch label="B" value={state.inputB} y={170} onToggle={() => dispatch({ type: "toggle", target: "B" })} />
        </svg>
      </div>
      <div className="narration-bar">
        Bấm vào công tắc A hoặc B để bật/tắt. {AND_RULE} Hiện tại: {state.inputA} AND {state.inputB} = {out}.
      </div>
    </div>
  );
}

export function LogicInspector({ state }: Props) {
  const rows: [Bit, Bit][] = [
    [0, 0],
    [0, 1],
    [1, 0],
    [1, 1],
  ];
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <section className="card" style={{ padding: "var(--sp-md)" }}>
        <span className="eyebrow">TRẠNG THÁI</span>
        <div className="analysis-grid" style={{ marginTop: "var(--sp-sm)" }}>
          <span className="analysis-label">A</span>
          <span>{state.inputA}</span>
          <span className="analysis-label">B</span>
          <span>{state.inputB}</span>
          <span className="analysis-label">Đầu ra</span>
          <span>
            <strong>{andOutput(state)}</strong>
          </span>
        </div>
      </section>
      <section className="card" style={{ padding: "var(--sp-md)" }}>
        <span className="eyebrow">BẢNG CHÂN TRỊ</span>
        <table className="truth-table">
          <thead>
            <tr>
              <th>A</th>
              <th>B</th>
              <th>A AND B</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([a, b]) => {
              const current = a === state.inputA && b === state.inputB;
              return (
                <tr key={`${a}${b}`} className={current ? "is-current" : ""}>
                  <td>{a}</td>
                  <td>{b}</td>
                  <td>
                    <strong>{a === 1 && b === 1 ? 1 : 0}</strong>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </div>
  );
}
