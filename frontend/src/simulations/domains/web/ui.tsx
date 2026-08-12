import type { WorkspaceProps } from "../../types";
import { cssTextOf, isModified } from "./apply";
import { COLOR_CHOICES, NUMERIC_RANGE, NUMERIC_PROPS, TEXT_COLOR_CHOICES } from "./props";
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
 *
 * ─── W4B-3F — TRANG, KHÔNG PHẢI MỘT Ô ─────────────────────────────────────
 *
 * Bản trước vẽ đúng MỘT `<div>` chữ. Nó chạy đúng, nhưng nó không dạy được thứ
 * `html_css` (T12 CĐ4) thật sự dạy: quan hệ THẺ ↔ HIỂN THỊ. Một div không có
 * tổ tiên, không có anh em, và bảng CSS chỉ ra một luật — nên "trang web" đọc
 * thành một ô trôi giữa khoảng trống.
 *
 * Nay xem trước là một TRANG: thanh trình duyệt giả (chỉ trang trí, không phải
 * control), khung `.trang` chứa `<h1>` và `<p>`. Nhờ có phân cấp thật:
 *   - bảng CSS có ba bộ chọn, trong đó hai cái là bộ chọn HẬU DUỆ;
 *   - đổi "cỡ chữ tiêu đề" và "cỡ chữ đoạn văn" cho hai kết quả khác nhau —
 *     đó chính là bài học, và trước đây nó không tồn tại.
 *
 * Vẫn KHÔNG có: chuỗi CSS thô, `eval`, `new Function`, iframe, `<style>`, JS.
 * Từng thuộc tính là một giá trị đã qua cổng kiểm miền, đặt qua `style` prop.
 */
type Props = WorkspaceProps<WebConfig, WebState>;

/** Nhóm control theo ĐÚNG bộ chọn nó ảnh hưởng — nhãn nói ra quan hệ đó. */
const GROUPS = [
  { selector: ".trang", label: "Khung trang", props: ["padding", "borderRadius"] },
  { selector: ".trang h1", label: "Tiêu đề", props: ["headingSize"] },
  { selector: ".trang p", label: "Đoạn văn", props: ["fontSize"] },
] as const;

export function WebWorkspace({ state, dispatch }: Props) {
  const s = state.style;
  const set = (name: string, value: number | string) =>
    dispatch({ type: "set_param", name, value });

  const swatches = (
    choices: readonly { value: string; label: string }[],
    prop: "backgroundColor" | "color" | "headingColor",
    label: string,
  ) => (
    <div className="web-control">
      <span className="web-control-label">{label}</span>
      <div className="web-swatches">
        {choices.map((c) => (
          <button key={c.value} type="button"
            className={`web-swatch${s[prop] === c.value ? " is-active" : ""}`}
            style={{ background: c.value }}
            aria-label={`${label} ${c.label}`}
            aria-pressed={s[prop] === c.value}
            onClick={() => set(prop, c.value)} />
        ))}
      </div>
    </div>
  );

  const slider = (k: (typeof NUMERIC_PROPS)[number]) => {
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
  };

  return (
    <div className="web-workspace">
      <div className="web-controls">
        <div className="web-group">
          <span className="web-group-head"><code>.trang</code> Khung trang</span>
          {swatches(COLOR_CHOICES, "backgroundColor", "Màu nền")}
          {GROUPS[0].props.map((k) => slider(k))}
        </div>

        <div className="web-group">
          <span className="web-group-head"><code>.trang h1</code> Tiêu đề</span>
          {swatches(TEXT_COLOR_CHOICES, "headingColor", "Màu chữ tiêu đề")}
          {GROUPS[1].props.map((k) => slider(k))}
        </div>

        <div className="web-group">
          <span className="web-group-head"><code>.trang p</code> Đoạn văn</span>
          {swatches(TEXT_COLOR_CHOICES, "color", "Màu chữ đoạn văn")}
          {GROUPS[2].props.map((k) => slider(k))}
        </div>

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
          {/* Thanh trình duyệt giả: nó nói "đây là một TRANG", và nó là TRANG
              TRÍ thuần — không nút nào bấm được, không trạng thái nào. */}
          <div className="web-browser-bar" aria-hidden="true">
            <span className="web-dot" /><span className="web-dot" /><span className="web-dot" />
            <span className="web-url">trang-cua-em.html</span>
          </div>
          <div className="web-page" style={{
            backgroundColor: s.backgroundColor,
            padding: `${s.padding}px`,
            borderRadius: `${s.borderRadius}px`,
          }}>
            <h1 className="web-page-heading" style={{
              color: s.headingColor, fontSize: `${s.headingSize}px`,
            }}>{state.heading}</h1>
            {state.paragraph && (
              <p className="web-page-paragraph" style={{
                color: s.color, fontSize: `${s.fontSize}px`,
              }}>{state.paragraph}</p>
            )}
          </div>
        </div>

        {/* HAI BẢN CHIẾU CỦA CÙNG MỘT STATE: cấu trúc thẻ và bảng kiểu. Cả hai
            SINH RA từ state — không bản nào là nguồn sự thật thứ hai. */}
        <div className="web-code-pair">
          <pre className="web-css" aria-label="Cấu trúc HTML tương ứng">{
`<div class="trang">
  <h1>${state.heading}</h1>${state.paragraph ? `
  <p>${state.paragraph}</p>` : ""}
</div>`
          }</pre>
          <pre className="web-css" aria-label="CSS tương ứng">{cssTextOf(s)}</pre>
        </div>
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
