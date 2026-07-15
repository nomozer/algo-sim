import type { WorkspaceProps } from "../../types";
import {
  currentStep, LAYERS, LAYER_LABEL,
  type EncapConfig, type EncapState, type PduComponent, type Side,
} from "./encap-model";

/**
 * Renderer 2D của network.protocol_encapsulation — baseline dễ đọc.
 *
 * M7.FREEZE: BỐ CỤC thuộc renderer, không thuộc state. Đọc CÙNG EncapState mà
 * renderer 3D đọc: PDU là danh sách phân đoạn, ở đây trải NGANG cho dễ đọc
 * (ưu tiên rõ ràng hơn hình khối lồng nhau).
 */

type Props = WorkspaceProps<EncapConfig, EncapState>;

const ROLE_COLOR: Record<string, string> = {
  payload: "var(--accent-green)",
  header: "var(--accent-sky)",
  trailer: "var(--accent-orange)",
};

function PduRow({ pdu, changed }: { pdu: PduComponent[]; changed: Set<string> }) {
  return (
    <div className="encap-pdu">
      {pdu.map((c) => (
        <span
          key={c.id}
          className={`encap-seg encap-seg-${c.role}${changed.has(c.id) ? " is-changed" : ""}`}
          style={{ borderColor: ROLE_COLOR[c.role] }}
        >
          {c.label}
        </span>
      ))}
    </div>
  );
}

export function EncapWorkspace({ state }: Props) {
  const step = currentStep(state);
  const changed = new Set(step.delta.componentIds);
  const sides: Side[] = ["sender", "receiver"];
  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div className="sim-stage">
        <div className="encap-2d">
          {sides.map((side) => (
            <div key={side} className={`encap-col${step.side === side ? " is-active-side" : ""}`}>
              <div className="encap-col-label">{side === "sender" ? "MÁY GỬI" : "MÁY NHẬN"}</div>
              {LAYERS.map((layer) => {
                const here = step.side === side && step.activeLayer === layer;
                return (
                  <div key={layer} className={`encap-layer${here ? " is-active-layer" : ""}`}>
                    <span className="encap-layer-name">{LAYER_LABEL[layer]}</span>
                    {here && <PduRow pdu={step.pdu} changed={changed} />}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
        {step.side === "medium" && (
          <div className="encap-medium">
            <span className="encap-medium-label">Đường truyền</span>
            <PduRow pdu={step.pdu} changed={new Set()} />
          </div>
        )}
      </div>
      <div className="narration-bar">{step.narration}</div>
    </div>
  );
}

export function EncapInspector({ state }: Props) {
  const step = currentStep(state);
  const sideLabel =
    step.side === "sender" ? "Máy gửi" : step.side === "receiver" ? "Máy nhận" : "Đường truyền";
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <section className="card" style={{ padding: "var(--sp-md)" }}>
        <span className="eyebrow">ĐÓNG GÓI DỮ LIỆU</span>
        <div className="analysis-grid" style={{ marginTop: "var(--sp-sm)" }}>
          <span className="analysis-label">Vị trí</span>
          <span>{sideLabel}</span>
          <span className="analysis-label">Tầng</span>
          <span>{step.activeLayer ? LAYER_LABEL[step.activeLayer] : "—"}</span>
          <span className="analysis-label">Đơn vị dữ liệu</span>
          <span>{step.pdu.map((c) => c.label).join(" | ")}</span>
          <span className="analysis-label">Bước</span>
          <span>
            {state.cursor + 1} / {state.steps.length}
          </span>
        </div>
      </section>
    </div>
  );
}
