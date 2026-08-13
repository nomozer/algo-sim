import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import {
  BaseConvWorkspace,
  CONV_BASES,
  makeBaseConvModule,
  positionalBreakdown,
  strategyOf,
} from "./convert-module";
import type { BaseConvConfig, ConvBase } from "./convert-module";

/**
 * WAVE 5 — ĐỔI CƠ SỐ LÀ CÔNG CỤ, KHÔNG PHẢI HOẠT HÌNH.
 *
 * ─── KHIẾM KHUYẾT ĐÃ ĐO TRƯỚC KHI SỬA ─────────────────────────────────────
 *
 * `measure-tool-first-w5.mjs` ở 1920 (HEAD d945706): **0 ô dữ liệu lúc mở bài,
 * 12 ô sau khi tua hết**. Học sinh đổi cơ số đích rồi vẫn phải bấm Tiến mới biết
 * kết quả. Đó là định nghĩa của "hoạt hình": câu trả lời bị khoá sau nút bấm.
 *
 * ─── ORACLE ĐỘC LẬP (§13) ─────────────────────────────────────────────────
 *
 * Kết quả được đối chiếu với `parseInt`/`Number.prototype.toString` của chính
 * JavaScript — một hiện thực KHÁC, không phải `parseInBase`/`toBase` của repo.
 * Dùng hàm của repo làm oracle cho chính nó thì test chỉ chứng minh nó nhất
 * quán với bản thân, kể cả khi cùng sai.
 *
 * Renderer KHÔNG được làm oracle: nó phải KHỚP oracle, không định nghĩa oracle.
 */

/** Oracle: phép đổi cơ số của JS, không đụng tới mã của repo. */
const oracleToBase = (n: number, base: number) => n.toString(base).toUpperCase();
const oracleParse = (s: string, base: number) => parseInt(s, base);

function conf(over: Partial<BaseConvConfig> = {}): BaseConvConfig {
  /* KHÔNG đặt `strategy`: nó DẪN XUẤT tất định từ cặp cơ số và validator từ
     chối giá trị tự đặt. Cũng không dựng cặp cơ số trùng nhau — hợp đồng đòi
     nguồn khác đích. */
  return { inputValue: "13", sourceBase: 10, targetBase: 2, ...over } as BaseConvConfig;
}

const mod = makeBaseConvModule();

function stateFor(over: Partial<BaseConvConfig> = {}) {
  const parsed = mod.validateConfig(conf(over));
  if (!parsed.ok) throw new Error(`config không hợp lệ: ${parsed.error}`);
  return { config: parsed.config, state: mod.init(parsed.config) };
}

function html(over: Partial<BaseConvConfig> = {}) {
  const { config, state } = stateFor(over);
  return renderToString(
    <BaseConvWorkspace state={state} config={config} busy={false} dispatch={() => {}} />,
  );
}

// ── 1. ORACLE ĐỘC LẬP ────────────────────────────────────────────────────────

describe("W5 §13 — kết quả khớp oracle độc lập", () => {
  it("mọi cặp cơ số, mọi giá trị mẫu đều khớp phép đổi của JS", () => {
    const samples = [0, 1, 2, 7, 8, 13, 15, 16, 26, 255, 256, 1000, 65535];
    let checked = 0;
    for (const src of CONV_BASES) {
      for (const dst of CONV_BASES) {
        if (src === dst) continue; // hợp đồng đòi nguồn ≠ đích
        for (const n of samples) {
          const digits = oracleToBase(n, src);
          const { state } = stateFor({
            inputValue: digits, sourceBase: src as ConvBase, targetBase: dst as ConvBase,
          });
          expect(state.decimalValue, `${digits} cơ số ${src}`).toBe(oracleParse(digits, src));
          expect(state.result, `${digits}: ${src}→${dst}`).toBe(oracleToBase(n, dst));
          checked += 1;
        }
      }
    }
    expect(checked, "vòng lặp không chạy case nào ⇒ test rỗng").toBeGreaterThan(100);
  });

  it("phân tích vị trí cộng lại đúng bằng giá trị (§14 biên)", () => {
    for (const src of CONV_BASES) {
      for (const n of [0, 1, src - 1, src, src * src, 65535]) {
        const digits = oracleToBase(n, src);
        const { total, cells } = positionalBreakdown(digits, src as ConvBase);
        expect(total, `${digits} cơ số ${src}`).toBe(oracleParse(digits, src));
        expect(cells.reduce((s, c) => s + c.product, 0)).toBe(total);
        // Trọng số phải là LUỸ THỪA CỦA CƠ SỐ ĐANG DÙNG, không phải của 10.
        for (const c of cells) expect(c.weight).toBe(src ** c.position);
      }
    }
  });
});

// ── 2. CÔNG CỤ TRẢ LỜI NGAY, KHÔNG ĐỢI THANH ĐIỀU KHIỂN ──────────────────────

describe("W5 §7 — dùng được khi ẩn thanh điều khiển", () => {
  it("kết quả hiện ngay ở cursor 0, không cần tua", () => {
    /* Đây chính là khiếm khuyết đã đo: 0 ô lúc mở. Nếu ai đó đưa bề mặt công
       cụ vào sau cursor lần nữa, test này đỏ. */
    const out = html({ inputValue: "13", sourceBase: 10, targetBase: 2 });
    expect(out).toContain("1101");
  });

  it("nhãn trọng số DẪN XUẤT từ cơ số, không cứng ở luỹ thừa 10", () => {
    const b2 = html({ inputValue: "1101", sourceBase: 2, targetBase: 10 });
    expect(b2).toContain("<sup>3</sup>");
    expect(b2).toMatch(/2<sup>3<\/sup>/);
    expect(b2).not.toMatch(/10<sup>3<\/sup>/);

    const b16 = html({ inputValue: "1A", sourceBase: 16, targetBase: 10 });
    expect(b16).toMatch(/16<sup>1<\/sup>/);
    expect(b16).not.toMatch(/10<sup>1<\/sup>/);
  });

  it("đổi cơ số đích tính lại NGAY, không đợi bước nào", () => {
    const { config, state } = stateFor({ inputValue: "26", sourceBase: 10, targetBase: 2 });
    expect(state.result).toBe("11010");
    const next = mod.apply(state, { type: "set_param", name: "targetBase", value: 16 });
    expect(next.result).toBe(oracleToBase(26, 16)); // "1A"
    expect(next.cursor).toBe(0); // tính lại, KHÔNG giữ vị trí cũ
    void config;
  });

  it("đổi cơ số thì CHIẾN LƯỢC diễn giải cũng đổi theo", () => {
    /* LỖ NÀY DO TIÊM LỖI TÌM RA.
       Phép tiêm §15 #6 — bỏ `strategy: strategyOf(...)` khi đổi `targetBase` —
       đi qua sạch cả 133 test. Kết quả vẫn đúng, nên không guard nào kêu; thứ
       hỏng là DIỄN GIẢI: 13 (cơ số 10) → cơ số 2 phải kể phép chia lấy dư, còn
       1101 (cơ số 2) → cơ số 10 phải kể trọng số vị trí. Giữ chiến lược cũ thì
       học sinh nghe một lời giải thích không khớp thao tác mình vừa làm — đúng
       thứ §3C gọi là "trace phải khớp tham số hiện tại". */
    const { state } = stateFor({ inputValue: "1101", sourceBase: 2, targetBase: 10 });
    expect(state.config.strategy).toBe("positional_weights");

    const toHex = mod.apply(state, { type: "set_param", name: "targetBase", value: 16 });
    expect(toHex.config.strategy, "2 → 16 phải đi qua hai giai đoạn")
      .toBe(strategyOf(2, 16));
    expect(toHex.config.strategy).not.toBe(state.config.strategy);

    const { state: dec } = stateFor({ inputValue: "13", sourceBase: 10, targetBase: 2 });
    expect(dec.config.strategy).toBe("quotient_remainder");
    const toBase8 = mod.apply(dec, { type: "set_param", name: "targetBase", value: 8 });
    expect(toBase8.config.strategy).toBe(strategyOf(10, 8));
  });

  it("đổi giá trị KHÔNG để lại nhãn vị trí cũ", () => {
    /* §3C: "no stale positional labels survive parameter changes". Bản trước
       vẽ bảng từ `steps` đã cắt theo cursor nên nhãn cũ sống sót qua một lượt
       đổi tham số cho tới khi người dùng tua lại. */
    const { state } = stateFor({ inputValue: "1101", sourceBase: 2, targetBase: 10 });
    const next = mod.apply(state, { type: "set_param", name: "inputValue", value: "11" });
    const { cells } = positionalBreakdown(next.config.inputValue, next.config.sourceBase);
    expect(cells.map((c) => c.position)).toEqual([1, 0]);
  });
});
