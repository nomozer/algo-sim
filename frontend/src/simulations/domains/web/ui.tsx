import type { WorkspaceProps } from "../../types";
import { cssTextOf, isModified } from "./apply";
import { COLOR_CHOICES, NUMERIC_PROPS, NUMERIC_RANGE, TEXT_COLOR_CHOICES } from "./props";
import type { WebConfig, WebState } from "./model";

/**
 * Sân khấu của mô hình CSS có ràng buộc — KHÔNG PHẢI trình soạn thảo.
 *
 * Bố cục CHIA ĐÔI: điều khiển trái, XEM TRƯỚC phải và chiếm phần lớn bề ngang.
 * Cơ chế của bài là QUAN HỆ "giá trị em đặt ↔ kết quả nhìn thấy", nên hai vế
 * phải nằm trong cùng một tầm mắt — khác các target có sân khấu ở giữa.
 *
 * Mọi control phát `set_param` → `module.apply` → state mới → xem trước đọc lại
 * state. Renderer KHÔNG giữ state riêng và KHÔNG tự tính CSS.
 */
type Props = WorkspaceProps<WebConfig, WebState>;

export function WebWorkspace({ state, dispatch }: Props) {
  const s = state.style;
  const set = (name: string, value: number | string) =>
    dispatch({ type: "set_param", name, value });

  return (
    <div className="web-workspace">
      <div className="web-controls">
        <div className="web-control">
          <span className="web-control-label">Màu nền</span>
          <div className="web-swatches">
            {COLOR_CHOICES.map((c) => (
              <button key={c.value} type="button"
                className={`web-swatch${s.backgroundColor === c.value ? " is-active" : ""}`}
                style={{ background: c.value }}
                aria-label={`Màu nền ${c.label}`}
                aria-pressed={s.backgroundColor === c.value}
                onClick={() => set("backgroundColor", c.value)} />
            ))}
          </div>
        </div>

        <div className="web-control">
          <span className="web-control-label">Màu chữ</span>
          <div className="web-swatches">
            {TEXT_COLOR_CHOICES.map((c) => (
              <button key={c.value} type="button"
                className={`web-swatch${s.color === c.value ? " is-active" : ""}`}
                style={{ background: c.value }}
                aria-label={`Màu chữ ${c.label}`}
                aria-pressed={s.color === c.value}
                onClick={() => set("color", c.value)} />
            ))}
          </div>
        </div>

        {NUMERIC_PROPS.map((k) => {
          const r = NUMERIC_RANGE[k];
          return (
            <div className="web-control" key={k}>
              <span className="web-control-label">
                {r.label} <strong>{s[k]}{r.unit}</strong>
              </span>
              <input type="range" min={r.min} max={r.max} step={r.step} value={s[k]}
                aria-label={r.label}
                onChange={(e) => set(k, Number(e.target.value))} />
            </div>
          );
        })}

        {isModified(state) && (
          <button type="button" className="sim-secondary-action"
            onClick={() => dispatch({ type: "toggle", target: "reset" })}>
            Về ban đầu
          </button>
        )}
      </div>

      <div className="web-preview-area">
        {/* XEM TRƯỚC — đọc THẲNG từ state. Không iframe, không script, không
            chuỗi style thô: từng thuộc tính là một giá trị đã kiểm miền. */}
        <div className="web-preview">
          <div className="web-artifact" style={{
            backgroundColor: s.backgroundColor, color: s.color,
            fontSize: `${s.fontSize}px`, padding: `${s.padding}px`,
            borderRadius: `${s.borderRadius}px`,
          }}>{state.content}</div>
        </div>
        <pre className="web-css" aria-label="CSS tương ứng">{cssTextOf(s)}</pre>
      </div>
    </div>
  );
}

export function WebInspector({ state }: Props) {
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <section className="card" style={{ padding: "var(--sp-md)" }}>
        <span className="eyebrow">THUỘC TÍNH ĐANG ĐẶT</span>
        <pre className="web-css" style={{ marginTop: "var(--sp-sm)" }}>{cssTextOf(state.style)}</pre>
      </section>
    </div>
  );
}
