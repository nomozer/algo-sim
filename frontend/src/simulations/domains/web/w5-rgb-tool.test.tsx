import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { WebWorkspace } from "./ui";
import { applyChannelChange, colorPropOf, cssTextOf } from "./apply";
import { CHANNEL_MAX, hexOf, rgbOf, rgbTextOf } from "./props";
import { registerWebDomain } from "./index";
import { getSimulation, clearRegistryForTest } from "../../registry";
import type { WebConfig, WebState } from "./model";

/**
 * WAVE 5 §2 — CÔNG CỤ MÀU RGB THẬT.
 *
 * ─── ĐO TRƯỚC KHI SỬA ─────────────────────────────────────────────────────
 *
 * `web.style_model` vốn KHÔNG có timeline nên nó đã là công cụ — khiếm khuyết
 * của nó khác hai target binary. Đo ở 1920 (HEAD d945706): 4 ô điều khiển, toàn
 * bộ là bảng màu ĐÓNG bảy ô. Học sinh bấm "Xanh dương nhạt" rồi không biết vì
 * sao nó xanh, và không có cách nào giữ hai kênh cố định để xem kênh thứ ba làm
 * gì — tức đúng bài học của T12.CD4 là thứ duy nhất bề mặt ấy không dạy được.
 *
 * ─── ORACLE ĐỘC LẬP (§13) ─────────────────────────────────────────────────
 *
 * Đối chiếu với phép đổi hex ↔ RGB viết ĐỘC LẬP ngay trong file này bằng số học
 * chuỗi, không gọi `rgbOf`/`hexOf` của sản phẩm. Lấy hàm sản phẩm làm oracle cho
 * chính nó thì test chỉ chứng minh nó nhất quán với bản thân, kể cả khi cùng sai.
 */

/** Oracle: cắt chuỗi + parse từng cặp, không đụng dịch bit của sản phẩm. */
const oracleRgb = (hex: string) => ({
  r: parseInt(hex.slice(1, 3), 16),
  g: parseInt(hex.slice(3, 5), 16),
  b: parseInt(hex.slice(5, 7), 16),
});
const oracleHex = (r: number, g: number, b: number) =>
  "#" + [r, g, b].map((v) => (v < 16 ? "0" : "") + v.toString(16)).join("");

function webState(): { config: WebConfig; state: WebState } {
  clearRegistryForTest();
  registerWebDomain();
  const mod = getSimulation("web.style_model")!;
  const parsed = mod.validateConfig({
    heading: "Câu lạc bộ Tin học",
    paragraph: "Chào mừng các bạn.",
  });
  if (!parsed.ok) throw new Error(parsed.error);
  return { config: parsed.config as WebConfig, state: mod.init(parsed.config) as WebState };
}

const mod = () => {
  clearRegistryForTest();
  registerWebDomain();
  return getSimulation("web.style_model")!;
};

// ── 1. ORACLE ĐỘC LẬP + PHỦ THAM SỐ (§13/§14) ───────────────────────────────

describe("W5 §13 — hex ↔ RGB khớp oracle độc lập", () => {
  it("mọi màu mẫu, gồm biên 0/255, giữa, một-kênh, xám bằng nhau", () => {
    /* §14 đòi đúng năm nhóm này. Xám bằng-ba-kênh là ca dễ lộ lỗi dịch bit
       nhất vì ba kênh giống nhau nên hoán vị sai vẫn ra cùng kết quả — nên nó
       đi kèm các ca một-kênh, nơi hoán vị sai lộ ra ngay. */
    const cases: [number, number, number][] = [
      [0, 0, 0], [255, 255, 255], [128, 128, 128],
      [255, 0, 0], [0, 255, 0], [0, 0, 255],
      [220, 80, 60], [1, 2, 3], [254, 0, 1], [0, 128, 255],
    ];
    for (const [r, g, b] of cases) {
      const hex = hexOf(r, g, b)!;
      expect(hex, `${r},${g},${b}`).toBe(oracleHex(r, g, b));
      expect(rgbOf(hex), hex).toEqual(oracleRgb(hex));
      expect(rgbTextOf(hex)).toBe(`rgb(${r}, ${g}, ${b})`);
    }
  });

  it("khứ hồi hex → rgb → hex giữ nguyên với MỌI giá trị kênh", () => {
    for (let v = 0; v <= CHANNEL_MAX; v++) {
      const hex = hexOf(v, CHANNEL_MAX - v, (v * 7) % 256)!;
      const c = rgbOf(hex)!;
      expect(hexOf(c.r, c.g, c.b), hex).toBe(hex);
    }
  });

  it("giá trị kênh ngoài miền bị TỪ CHỐI, không kẹp về biên", () => {
    /* Kẹp im lặng nói dối hai lần: người gọi tưởng đã đặt được, và học sinh
       thấy một con số mình không hề chọn. Cùng luật với thuộc tính số. */
    for (const bad of [-1, 256, 1.5, NaN]) {
      expect(hexOf(bad, 0, 0), String(bad)).toBeNull();
    }
  });
});

// ── 2. QUAN HỆ NHÂN QUẢ (§2A) ────────────────────────────────────────────────

describe("W5 §2A — đổi một kênh, hai kênh kia đứng yên", () => {
  it("đổi R giữ nguyên G và B", () => {
    const { state } = webState();
    const before = rgbOf(state.style.backgroundColor)!;
    const next = applyChannelChange(state.style, "page", "r", 200)!;
    const after = rgbOf(next.backgroundColor)!;
    expect(after.r).toBe(200);
    expect(after.g).toBe(before.g);
    expect(after.b).toBe(before.b);
  });

  it("năm quan hệ mẫu mà học sinh phải kiểm được (§2)", () => {
    const { state } = webState();
    const set = (r: number, g: number, b: number) => {
      let s = state.style;
      s = applyChannelChange(s, "page", "r", r)!;
      s = applyChannelChange(s, "page", "g", g)!;
      s = applyChannelChange(s, "page", "b", b)!;
      return s.backgroundColor;
    };
    expect(set(255, 0, 0)).toBe("#ff0000");
    expect(set(0, 255, 0)).toBe("#00ff00");
    expect(set(0, 0, 255)).toBe("#0000ff");
    expect(set(255, 255, 255)).toBe("#ffffff");
    expect(set(0, 0, 0)).toBe("#000000");
    expect(set(128, 128, 128)).toBe("#808080");
  });

  it("chọn CHỮ thì chỉ chữ đổi; chọn NỀN thì chỉ nền đổi", () => {
    /* §2C bước 1–8, và là lỗi #2 trong danh sách tiêm lỗi. Không thể xảy ra vì
       chỉ có MỘT `selected` trong state — test này khoá điều đó lại. */
    const m = mod();
    const { config } = webState();
    const s0 = m.init(config) as WebState;

    const onHeading = m.apply({ ...s0, selected: "heading" },
      { type: "set_param", name: "r", value: 255 }) as WebState;
    expect(onHeading.style.backgroundColor).toBe(s0.style.backgroundColor);
    expect(onHeading.style.headingColor).not.toBe(s0.style.headingColor);

    const onPage = m.apply({ ...s0, selected: "page" },
      { type: "set_param", name: "b", value: 255 }) as WebState;
    expect(onPage.style.headingColor).toBe(s0.style.headingColor);
    expect(onPage.style.color).toBe(s0.style.color);
    expect(onPage.style.backgroundColor).not.toBe(s0.style.backgroundColor);
  });

  it("kênh tác động lên đúng thuộc tính của nút đang chọn", () => {
    expect(colorPropOf("page")).toBe("backgroundColor");
    expect(colorPropOf("heading")).toBe("headingColor");
    expect(colorPropOf("paragraph")).toBe("color");
  });
});

// ── 3. CSS VÀ XEM TRƯỚC ĐỌC CÙNG MỘT STATE (§2B) ────────────────────────────

describe("W5 §2B — CSS in ra là DẪN XUẤT, không phải giá trị lưu song song", () => {
  it("bảng CSS, dòng rgb() và ô màu cùng nói một màu", () => {
    /* Lỗi #3 và #4 trong danh sách tiêm lỗi: hex cứng, hoặc CSS lệch state. */
    const { config, state } = webState();
    const s = applyChannelChange(state.style, "page", "r", 255)!;
    const next = { ...state, style: s };
    expect(cssTextOf(s)).toContain(s.backgroundColor);
    const out = renderToString(
      <WebWorkspace state={next} config={config} busy={false} dispatch={() => {}} />,
    );
    expect(out).toContain(s.backgroundColor);
    expect(out).toContain(rgbTextOf(s.backgroundColor)!);
  });

  it("ba kênh của nút ĐANG CHỌN hiện ra, không phải của nút khác", () => {
    const { config, state } = webState();
    const out = renderToString(
      <WebWorkspace state={{ ...state, selected: "page" }} config={config}
        busy={false} dispatch={() => {}} />,
    );
    const c = rgbOf(state.style.backgroundColor)!;
    expect(out).toContain(`>${c.r}<`);
    expect(out).toContain(rgbTextOf(state.style.backgroundColor)!);
  });
});
