import type { WorkspaceProps } from "../../types";
import { colorPropOf, cssTextOf, htmlTextOf, isModified } from "./apply";
import {
  CHANNELS, CHANNEL_LABEL, CHANNEL_MAX, COLOR_CHOICES, NUMERIC_RANGE, NUMERIC_PROPS,
  TEXT_COLOR_CHOICES, hexOf, rgbOf, rgbTextOf, type Channel,
} from "./props";
import { NODE_LABEL, SELECTOR_OF, type WebBlock, type WebConfig, type WebNode, type WebState } from "./model";

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

/**
 * Nhóm control DẪN TỪ ĐĂNG KÍ, không liệt kê lại bằng tay.
 *
 * Bản trước ghi cứng cả ba nhóm ở đây, nên `NUMERIC_PROPS` và bề mặt công cụ là
 * hai danh sách rời: thêm thuộc tính vào đăng kí mà quên sửa chỗ này thì học
 * sinh không chạm được vào nó, và không test nào đỏ. Nay chỉ SWATCH là dữ kiện
 * riêng của UI (nó là màu, không phải thuộc tính số); phần còn lại đọc `node`
 * từ `NUMERIC_RANGE`.
 */
const SWATCH_OF = {
  page: { swatch: "backgroundColor", swatchLabel: "Màu nền" },
  heading: { swatch: "headingColor", swatchLabel: "Màu chữ tiêu đề" },
  paragraph: { swatch: "color", swatchLabel: "Màu chữ đoạn văn" },
} as const;

const GROUPS = (["page", "heading", "paragraph"] as const).map((node) => ({
  node,
  props: NUMERIC_PROPS.filter((p) => NUMERIC_RANGE[p].node === node),
  ...SWATCH_OF[node],
}));

export function WebWorkspace({ state, dispatch }: Props) {
  const s = state.style;
  const set = (name: string, value: number | string) =>
    dispatch({ type: "set_param", name, value });
  const select = (node: WebNode) => set("selected", node);
  /* Dời khối: phát ô ĐÍCH tuyệt đối. Renderer không tự tính hoán vị — nó chỉ
     nói "đặt khối này vào ô kia" rồi đọc lại `state.order`. */
  const moveTo = (block: WebBlock, slot: number) =>
    dispatch({ type: "move", target: block, x: 0, y: slot });

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

  /**
   * W5 §2/§2A — BÀN ĐIỀU KHIỂN BA KÊNH.
   *
   * Bảy ô màu gợi ý vẫn còn (chọn nhanh), nhưng chúng KHÔNG dạy được bài học
   * của T12.CD4: học sinh bấm "Xanh dương nhạt" rồi không biết vì sao nó xanh,
   * và không có cách nào giữ hai kênh cố định để xem kênh thứ ba làm gì.
   *
   * Ba dòng dưới đây đọc theo chiều dọc thành một câu:
   *     R ─────●──  220
   *     G ──●─────   80
   *     B ─●──────   60      →  ▉  rgb(220, 80, 60)  #dc503c
   * Vệt màu của từng thanh chạy từ "kênh này bằng 0" tới "kênh này bằng 255",
   * hai kênh kia giữ nguyên — nên chính THANH TRƯỢT đã là câu trả lời cho
   * "kéo nó thì màu đi về đâu", trước cả khi học sinh kéo.
   */
  const channelBar = (label: string) => {
    const prop = colorPropOf(state.selected);
    const hex = s[prop] as string;
    const c = rgbOf(hex);
    if (!c) return null;
    const ramp = (ch: Channel) => {
      const lo = hexOf(...(ch === "r" ? [0, c.g, c.b] : ch === "g" ? [c.r, 0, c.b] : [c.r, c.g, 0]) as [number, number, number]);
      const hi = hexOf(...(ch === "r" ? [255, c.g, c.b] : ch === "g" ? [c.r, 255, c.b] : [c.r, c.g, 255]) as [number, number, number]);
      return `linear-gradient(to right, ${lo}, ${hi})`;
    };
    return (
      <div className="web-control web-channels" role="group"
        aria-label={`Ba kênh màu của ${label}`}>
        <span className="web-control-label">{label} — ba kênh</span>
        {CHANNELS.map((ch) => (
          <div className="web-channel" key={ch}>
            <span className="web-channel-name">{CHANNEL_LABEL[ch]}</span>
            <input type="range" min={0} max={CHANNEL_MAX} step={1} value={c[ch]}
              className="web-channel-range" style={{ background: ramp(ch) }}
              aria-label={`${CHANNEL_LABEL[ch]} của ${label}`}
              aria-valuetext={`${c[ch]} trên ${CHANNEL_MAX}`}
              onChange={(e) => set(ch, Number(e.target.value))} />
            <output className="web-channel-value">{c[ch]}</output>
          </div>
        ))}
        {/* KẾT QUẢ của ba kênh — đặt ngay dưới chúng để quan hệ "ba kênh → một
            màu" đọc được bằng mắt. Cả hai dạng viết đều DẪN XUẤT từ cùng một
            hex trong state, không phải hai giá trị lưu song song. */}
        <div className="web-channel-result">
          <span className="web-channel-chip" style={{ background: hex }} aria-hidden="true" />
          <code>{rgbTextOf(hex)}</code>
          <code className="web-channel-hex">{hex}</code>
        </div>
      </div>
    );
  };

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

  /* MỘT KHỐI TRÊN SÂN KHẤU — bấm thẳng vào nó để chọn.
     Vùng bấm là `role="button"` chứ không phải `<button>` thật vì bên trong là
     `<h1>`/`<p>` (nội dung khối), mà `<button>` chỉ chứa được nội dung câu.
     Hai mũi tên nằm NGOÀI vùng bấm, không lồng nút trong nút. */
  const blockNode = (b: WebBlock, i: number) => {
    const on = state.selected === b;
    const last = state.order.length - 1;
    return (
      <div key={b} className={`web-node${on ? " is-selected" : ""}`}>
        <div className="web-node-hit" role="button" tabIndex={0}
          aria-pressed={on}
          aria-label={`Chọn ${NODE_LABEL[b]} (${SELECTOR_OF[b]})`}
          onClick={() => select(b)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(b); }
          }}>
          {b === "heading" ? (
            <h1 className="web-page-heading" style={{
              color: s.headingColor, fontSize: `${s.headingSize}px`,
            }}>{state.heading}</h1>
          ) : (
            <p className="web-page-paragraph" style={{
              color: s.color, fontSize: `${s.fontSize}px`,
            }}>{state.paragraph}</p>
          )}
        </div>

        {on && <span className="web-node-tag">{SELECTOR_OF[b]}</span>}

        {/* Dời khối: chỉ hiện khi thân trang có từ hai khối trở lên — một khối
            thì "đổi thứ tự" là câu hỏi không có nghĩa. */}
        {on && state.order.length > 1 && (
          <div className="web-node-tools">
            <button type="button" className="web-node-move"
              aria-label={`Đưa ${NODE_LABEL[b]} lên trên`}
              disabled={i === 0} onClick={() => moveTo(b, i - 1)}>↑</button>
            <button type="button" className="web-node-move"
              aria-label={`Đưa ${NODE_LABEL[b]} xuống dưới`}
              disabled={i === last} onClick={() => moveTo(b, i + 1)}>↓</button>
          </div>
        )}
      </div>
    );
  };

  /* Cột điều khiển bám theo NÚT ĐANG CHỌN. Đầu nhóm là nút thật, nên mỗi nút
     đều có đường bàn phím kể cả khung trang (khung không tự làm vùng bấm được
     vì các khối nằm bên trong nó). */
  const group = (g: (typeof GROUPS)[number]) => {
    const on = state.selected === g.node;
    return (
      <div key={g.node} className={`web-group${on ? " is-selected" : ""}`}>
        <button type="button" className="web-group-head" aria-pressed={on}
          onClick={() => select(g.node)}>
          <code>{SELECTOR_OF[g.node]}</code> {NODE_LABEL[g.node]}
        </button>
        {swatches(
          g.node === "page" ? COLOR_CHOICES : TEXT_COLOR_CHOICES,
          g.swatch, g.swatchLabel,
        )}
        {/* Ba kênh chỉ hiện cho nút ĐANG CHỌN: hiện cả ba nhóm cùng lúc thì có
            chín thanh trượt trên màn hình và không còn rõ thanh nào đổi cái gì. */}
        {on && channelBar(g.swatchLabel)}
        {g.props.map((k) => slider(k))}
      </div>
    );
  };

  return (
    <div className="web-workspace">
      <div className="web-controls">
        {GROUPS.filter((g) => g.node !== "paragraph" || state.paragraph).map(group)}

        {isModified(state) && (
          <button type="button" className="sim-secondary-action"
            onClick={() => dispatch({ type: "toggle", target: "reset" })}>
            Về ban đầu
          </button>
        )}
      </div>

      <div className="web-preview-area">
        {/* XEM TRƯỚC — đọc THẲNG từ state. Không iframe, không script, không
            chuỗi style thô: từng thuộc tính là một giá trị đã kiểm miền.
            Đây cũng là chỗ THAO TÁC: bấm vào phần nào là chọn phần ấy. */}
        <div className="web-preview">
          {/* Thanh trình duyệt giả: nó nói "đây là một TRANG", và nó là TRANG
              TRÍ thuần — không nút nào bấm được, không trạng thái nào. */}
          <div className="web-browser-bar" aria-hidden="true">
            <span className="web-dot" /><span className="web-dot" /><span className="web-dot" />
            <span className="web-url">trang-cua-em.html</span>
          </div>
          {/* Bấm vào NỀN khung (không phải vào khối) thì chọn khung. Đường bàn
              phím của khung là nút đầu nhóm `.trang` bên cột trái. */}
          <div className={`web-page${state.selected === "page" ? " is-selected" : ""}`}
            onClick={(e) => { if (e.target === e.currentTarget) select("page"); }}
            style={{
              backgroundColor: s.backgroundColor,
              padding: `${s.padding}px`,
              borderRadius: `${s.borderRadius}px`,
            }}>
            {state.order.map(blockNode)}
          </div>
        </div>

        {/* HAI BẢN CHIẾU CỦA CÙNG MỘT STATE: cấu trúc thẻ và bảng kiểu. Cả hai
            SINH RA từ state — không bản nào là nguồn sự thật thứ hai. Dời khối
            đổi bản TRÁI mà không đổi bản PHẢI, và đó chính là bài học: thứ tự
            thuộc về HTML, hình thức thuộc về CSS. */}
        <div className="web-code-pair">
          <pre className="web-css" aria-label="Cấu trúc HTML tương ứng">{htmlTextOf(state)}</pre>
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
        <span className="eyebrow">ĐANG CHỌN</span>
        {/* Nói ra bộ chọn đang cầm, cùng một chuỗi mà nhãn trên sân khấu in ra —
            Inspector và sân khấu đọc chung một `state.selected`. */}
        <p className="muted" style={{ margin: "var(--sp-xs) 0 0" }}>
          {NODE_LABEL[state.selected]} — <code>{SELECTOR_OF[state.selected]}</code>
        </p>
      </section>
      <section className="card" style={{ padding: "var(--sp-md)" }}>
        <span className="eyebrow">THUỘC TÍNH ĐANG ĐẶT</span>
        <pre className="web-css" style={{ marginTop: "var(--sp-sm)" }}>{cssTextOf(state.style)}</pre>
      </section>
    </div>
  );
}
