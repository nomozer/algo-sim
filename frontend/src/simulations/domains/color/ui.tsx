import { Fragment } from "react";
import type { WorkspaceProps } from "../../types";
import {
  CHANNELS,
  CHANNEL_LABEL,
  CHANNEL_MAX,
  channelRamp,
  clampChannel,
  readableInkOn,
  type Channel,
} from "../../color-channels";
import {
  CHANNEL_FIELD,
  cornerNameOf,
  cssColorOfState,
  hexColorOfState,
  rgbOfState,
  type ColorConfig,
  type ColorState,
} from "./model";

/**
 * Renderer 2D của `color.rgb_model`.
 *
 * ─── BỐ CỤC ĐỌC THEO MỘT CHIỀU ─────────────────────────────────────────────
 *
 *     BA NGUYÊN NHÂN  →  MỘT KẾT QUẢ
 *
 *     Đỏ  ──────●───  200        ┌───────────────┐
 *     Lục ───●──────   90        │               │
 *     Lam ─●────────   60        │   ô màu lớn   │
 *                                └───────────────┘
 *                                rgb(200, 90, 60) · #c85a3c
 *
 * Ô màu KHÔNG phải một chỉ báo nhỏ nằm cạnh bộ điều khiển — nó là thứ bài học
 * nói về, nên nó chiếm chỗ tương xứng. Đây là chỗ `generic.rule_scene` không
 * bao giờ chở nổi bài này: ở đó "màu" chỉ có thể là thuộc tính của một đối tượng
 * trong cảnh, không thể là CHÍNH kết quả đang được tính.
 *
 * Renderer chỉ ĐỌC state và PHÁT action (`set_param`). Không có phép toán màu
 * nào ở đây — chúng thuộc `color-channels.ts` / `model.ts`.
 */

type Props = WorkspaceProps<ColorConfig, ColorState>;

export function ColorWorkspace({ state, busy, dispatch }: Props) {
  const rgb = rgbOfState(state);
  const css = cssColorOfState(state);
  const hex = hexColorOfState(state);
  const ink = readableInkOn(rgb);
  const corner = cornerNameOf(state);

  const set = (ch: Channel, raw: number) =>
    dispatch({ type: "set_param", name: CHANNEL_FIELD[ch], value: clampChannel(raw) });

  return (
    <div className="stack rgb-stage" style={{ gap: "var(--sp-md)" }}>
      <div className="rgb-channels" role="group" aria-label="Ba kênh màu">
        {CHANNELS.map((ch) => {
          const value = state[CHANNEL_FIELD[ch]];
          return (
            <div className="rgb-channel" key={ch}>
              <span className="rgb-channel-name">{CHANNEL_LABEL[ch]}</span>
              {/* Vệt màu của thanh = "kênh này chạy 0→255, hai kênh kia giữ
                  nguyên", nên thanh trượt đã trả lời "kéo thì màu đi về đâu"
                  TRƯỚC khi học sinh kéo. */}
              <input
                type="range"
                className="rgb-channel-range"
                min={0}
                max={CHANNEL_MAX}
                step={1}
                value={value}
                disabled={busy}
                style={{ background: channelRamp(rgb, ch) }}
                aria-label={`Kênh ${CHANNEL_LABEL[ch]}`}
                aria-valuetext={`${value} trên ${CHANNEL_MAX}`}
                onChange={(e) => set(ch, Number(e.target.value))}
              />
              {/* Ô SỐ nhập được, không chỉ là nhãn: đặt đúng 128 bằng cách kéo
                  là một trò chơi khéo tay, và bài học không nằm ở đó. */}
              <input
                type="number"
                className="rgb-channel-number"
                min={0}
                max={CHANNEL_MAX}
                step={1}
                value={value}
                disabled={busy}
                aria-label={`Trị số kênh ${CHANNEL_LABEL[ch]}`}
                onChange={(e) => set(ch, Number(e.target.value))}
              />
            </div>
          );
        })}
      </div>

      <div className="rgb-result">
        <div
          className="rgb-swatch"
          style={{ background: css, color: ink }}
          role="img"
          aria-label={`Màu kết quả: ${css}${corner ? `, màu ${corner}` : ""}`}
        >
          {corner && <span className="rgb-swatch-name">{corner}</span>}
        </div>
        {/* HAI CÁCH VIẾT của cùng một màu, đặt cạnh ô màu chứ không ở panel
            khác: `rgb(…)` là ba số học sinh vừa kéo, `#rrggbb` là chính ba số
            ấy viết theo vị trí — quan hệ đó chỉ đọc được khi chúng đứng cạnh
            nhau và cùng đổi trong một lần kéo. */}
        <div className="rgb-codes">
          <code className="rgb-code-css">{css}</code>
          <code className="rgb-code-hex">{hex}</code>
        </div>
      </div>
    </div>
  );
}

/**
 * Panel Giải thích — dùng lại `analysis-grid` của shell (cùng khuôn với
 * `BinaryInspector`/`LogicInspector`), không đẻ một lớp bảng riêng cho một miền.
 *
 * Việc DUY NHẤT nó làm mà sân khấu không làm: tách `#rrggbb` thành BA CẶP, mỗi
 * cặp đứng cạnh trị số của chính kênh nó. Đó là chỗ mã hex thôi là một chuỗi bí
 * ẩn và trở thành ba con số viết theo cơ số 16.
 */
export function ColorInspector({ state }: Props) {
  const hex = hexColorOfState(state);
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <section className="card" style={{ padding: "var(--sp-md)" }}>
        <span className="eyebrow">BA KÊNH</span>
        <div className="analysis-grid" style={{ marginTop: "var(--sp-sm)" }}>
          {CHANNELS.map((ch, i) => (
            <Fragment key={ch}>
              <span className="analysis-label">{CHANNEL_LABEL[ch]}</span>
              <span>
                {state[CHANNEL_FIELD[ch]]} / {CHANNEL_MAX}
                {" · hex "}
                <code>{hex.slice(1 + i * 2, 3 + i * 2)}</code>
              </span>
            </Fragment>
          ))}
        </div>
      </section>
    </div>
  );
}
