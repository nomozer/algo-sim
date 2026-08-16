import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { makeColorModule } from "./index";
import { ColorWorkspace } from "./ui";
import {
  cornerNameOf,
  cssColorOfState,
  dominantChannel,
  hexColorOfState,
  isGray,
  type ColorConfig,
  type ColorState,
} from "./model";
import { channelRamp, readableInkOn } from "../../color-channels";

/**
 * W5A — `color.rgb_model`.
 *
 * ─── ĐIỀU PHẢI CHỨNG MINH ──────────────────────────────────────────────────
 *
 * Không phải "component render được", mà là: BA SỐ → MỘT MÀU, tất định, và mọi
 * cách viết trên màn hình đều dẫn xuất từ đúng ba số ấy. Đó là toàn bộ cơ chế
 * đang dạy — nếu nó sai thì bài dạy sai, còn nếu nó chỉ đúng ở một điểm thì bài
 * chỉ là một bức hình có ba thanh trượt gắn thêm.
 */

function build(red = 220, green = 80, blue = 60) {
  const mod = makeColorModule();
  const r = mod.validateConfig({ red, green, blue, notes: null });
  if (!r.ok) throw new Error(r.error);
  return { mod, config: r.config as ColorConfig, state: mod.init(r.config) as ColorState };
}

const set = (mod: ReturnType<typeof makeColorModule>, s: ColorState, name: string, value: number) =>
  mod.apply!(s, { type: "set_param", name, value }) as ColorState;

/* ══ 1. ĐIỂM MỐC BẮT BUỘC ═════════════════════════════════════════════════ */

describe("W5A · tám đỉnh khối màu là ĐỊNH NGHĨA, không phải ý kiến", () => {
  const CORNERS: [number, number, number, string, string][] = [
    [0, 0, 0, "#000000", "đen"],
    [255, 255, 255, "#ffffff", "trắng"],
    [255, 0, 0, "#ff0000", "đỏ"],
    [0, 255, 0, "#00ff00", "lục"],
    [0, 0, 255, "#0000ff", "lam"],
    [255, 255, 0, "#ffff00", "vàng"],
  ];

  it.each(CORNERS)("(%i, %i, %i) ⇒ %s / %s", (r, g, b, hex, name) => {
    const { state } = build(r, g, b);
    expect(hexColorOfState(state)).toBe(hex);
    expect(cssColorOfState(state)).toBe(`rgb(${r}, ${g}, ${b})`);
    expect(cornerNameOf(state)).toBe(name);
  });

  it("MÀU TRỘN: dẫn xuất đúng, và KHÔNG bị đặt tên bừa", () => {
    const { state } = build(120, 90, 200);
    expect(cssColorOfState(state)).toBe("rgb(120, 90, 200)");
    expect(hexColorOfState(state)).toBe("#785ac8");
    /* Đây là ràng buộc THIẾT KẾ, không phải thiếu sót: gọi màu này là "tím" là
       một phán quyết thẩm mỹ renderer bịa ra, trong khi cả bài học dựng trên
       nguyên tắc mọi thứ hiện ra đều dẫn xuất tất định từ ba con số. */
    expect(cornerNameOf(state), "renderer đang tự đặt tên cho màu trộn").toBeNull();
    expect(dominantChannel(state)).toBe("b");
  });

  it("ba kênh bằng nhau ⇒ mức xám (quan hệ học sinh tự khám phá được)", () => {
    const { state } = build(128, 128, 128);
    expect(isGray(state)).toBe(true);
    expect(hexColorOfState(state)).toBe("#808080");
  });
});

/* ══ 2. ĐỔI MỘT KÊNH ⇒ TÍNH LẠI NGAY ══════════════════════════════════════ */

describe("W5A · công cụ có ràng buộc: đổi đầu vào là tính lại ngay", () => {
  it.each(["red", "green", "blue"])("kênh %s đổi được, và CHỈ nó đổi", (name) => {
    const { mod, state } = build(10, 20, 30);
    const next = set(mod, state, name, 200);

    expect(next, `${name}: apply trả về chính state cũ`).not.toBe(state);
    expect(next[name as keyof ColorState]).toBe(200);
    for (const other of ["red", "green", "blue"].filter((n) => n !== name)) {
      expect(next[other as keyof ColorState], `${name} kéo theo ${other}`)
        .toBe(state[other as keyof ColorState]);
    }
    // Không có Play, không có bước: kết quả có mặt ngay sau một action.
    expect(cssColorOfState(next)).not.toBe(cssColorOfState(state));
  });

  it("KHÔNG timeline, KHÔNG predict — trộn màu không có 'bước tiếp theo' để cam kết", () => {
    const { mod } = build();
    expect(mod.timeline, "mọc timeline cho một quan hệ tức thì").toBeUndefined();
    expect(mod.predict, "gắn quiz vào một công cụ — đúng thứ Phase B vừa gỡ").toBeUndefined();
    expect(mod.explore, "công cụ không có lời mời nào").toBeTruthy();
  });

  it("đặt lại đúng trị đang có ⇒ no-op cùng tham chiếu (không dựng lại vô cớ)", () => {
    const { mod, state } = build(10, 20, 30);
    expect(set(mod, state, "red", 10)).toBe(state);
  });

  it("giá trị/tên NGOÀI hợp đồng ⇒ no-op, không kẹp liều, không ném", () => {
    const { mod, state } = build(10, 20, 30);
    for (const bad of [-1, 256, 3.5, Number.NaN]) {
      expect(set(mod, state, "red", bad), `nhận bừa giá trị ${bad}`).toBe(state);
    }
    expect(set(mod, state, "alpha", 5), "nhận tên kênh không tồn tại").toBe(state);
    expect(mod.apply!(state, { type: "toggle", target: "red" })).toBe(state);
  });
});

/* ══ 3. VALIDATOR — mirror của backend ════════════════════════════════════ */

describe("W5A · hợp đồng config đóng ở CẢ hai tầng", () => {
  it("từ chối kênh ngoài 0..255 và kênh thiếu", () => {
    const mod = makeColorModule();
    for (const raw of [
      { red: 256, green: 0, blue: 0 },
      { red: -1, green: 0, blue: 0 },
      { red: 1.5, green: 0, blue: 0 },
      { red: 0, green: 0 },
      { red: "255", green: 0, blue: 0 },
    ]) {
      expect(mod.validateConfig(raw).ok, `nhận config hỏng: ${JSON.stringify(raw)}`).toBe(false);
    }
  });

  it("KHÔNG nhận `hex` như một cách nói thứ hai về cùng một màu", () => {
    /* Nhận thêm `hex` là mở hai đường cho LLM nói "màu gì", và khi chúng lệch
       nhau thì không ai là nguồn sự thật. Ba số, một sự thật. */
    const mod = makeColorModule();
    const r = mod.validateConfig({ red: 1, green: 2, blue: 3, hex: "#ffffff" });
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(Object.keys(r.config).sort()).toEqual(["blue", "green", "notes", "red"]);
  });
});

/* ══ 4. MÀN HÌNH NÓI ĐÚNG THỨ STATE ĐANG GIỮ ══════════════════════════════ */

describe("W5A · bề mặt không được lệch khỏi ba con số", () => {
  it("sân khấu dựng ba thanh trượt, ba ô số và ô màu mang cả hai cách viết", () => {
    const { config, state } = build(220, 80, 60);
    const html = renderToString(
      <ColorWorkspace config={config} state={state} busy={false} dispatch={() => {}} />,
    );
    for (const label of ["Kênh Đỏ", "Kênh Lục", "Kênh Lam"]) {
      expect(html, `thiếu thanh trượt ${label}`).toContain(label);
    }
    expect((html.match(/type="range"/g) ?? []).length, "không đủ ba thanh trượt").toBe(3);
    expect((html.match(/type="number"/g) ?? []).length, "không đủ ba ô số").toBe(3);
    expect(html, "thiếu cách viết rgb()").toContain("rgb(220, 80, 60)");
    expect(html, "thiếu mã hex").toContain("#dc503c");
  });

  it("ĐỔI STATE ⇒ ĐỔI MÀN HÌNH (không có chuỗi nào đông cứng ở markup)", () => {
    /* Nếu một trong hai cách viết bị viết cứng thì test trên vẫn xanh mà sản
       phẩm nói dối ngay khi học sinh kéo lần đầu. */
    const { mod, config, state } = build(220, 80, 60);
    const moved = set(mod, state, "green", 200);
    const html = renderToString(
      <ColorWorkspace config={config} state={moved} busy={false} dispatch={() => {}} />,
    );
    expect(html).toContain("rgb(220, 200, 60)");
    expect(html).toContain("#dcc83c");
    expect(html, "màn hình còn giữ màu cũ").not.toContain("rgb(220, 80, 60)");
  });

  it("thuyết minh đọc CHÍNH ba số đang giữ, ở cả ba loại trạng thái", () => {
    const mod = makeColorModule();
    const say = (r: number, g: number, b: number) =>
      mod.narrate!({ red: r, green: g, blue: b } as ColorState, {} as ColorConfig)!.text;

    expect(say(255, 0, 0)).toContain("màu đỏ");
    expect(say(128, 128, 128)).toContain("mức xám");
    expect(say(120, 90, 200)).toContain("lam");
    // Ba con số phải có mặt nguyên văn — thuyết minh không được nói vòng.
    expect(say(120, 90, 200)).toContain("120");
    expect(say(120, 90, 200)).toContain("#785ac8");
  });
});

/* ══ 5. HAI CHI TIẾT DỄ TRÔI, VÀ CHÚNG MANG BÀI HỌC ══════════════════════ */

describe("W5A · thanh trượt và nhãn phải nói thật", () => {
  it("vệt màu giữ HAI kênh kia cố định — nếu không nó nói dối về màu sắp nhận", () => {
    const c = { r: 220, g: 80, b: 60 };
    /* Vệt của kênh lục phải chạy từ (220, 0, 60) tới (220, 255, 60): hai đầu
       mang đúng hai kênh còn lại. Một bản cài "cho đẹp" (đen → lục thuần) sẽ
       hứa một màu học sinh không bao giờ nhận được. */
    expect(channelRamp(c, "g")).toBe("linear-gradient(to right, #dc003c, #dcff3c)");
    expect(channelRamp(c, "r")).toBe("linear-gradient(to right, #00503c, #ff503c)");
  });

  it("mực trên ô màu đọc được ở CẢ hai đầu miền độ sáng", () => {
    /* Một màu chữ cố định biến mất ở một đầu — và nó biến mất đúng lúc học sinh
       kéo tới đó, tức đúng lúc đang học. */
    const onWhite = readableInkOn({ r: 255, g: 255, b: 255 });
    const onBlack = readableInkOn({ r: 0, g: 0, b: 0 });
    expect(onWhite).not.toBe(onBlack);
    expect(onWhite, "chữ sáng trên nền trắng").toBe("#111827");
    expect(onBlack, "chữ tối trên nền đen").toBe("#ffffff");
    // Lục thuần rất sáng dù chỉ một kênh bật — đây là chỗ phép tính luma phải
    // khác hẳn "trung bình ba kênh", nên khoá luôn.
    expect(readableInkOn({ r: 0, g: 255, b: 0 }), "luma đang tính như trung bình cộng")
      .toBe("#111827");
  });
});
