import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { makeWebStyleModule } from "./index";
import { applyStyleChange, cssTextOf, isModified } from "./apply";
import { COLOR_CHOICES, NUMERIC_RANGE, TEXT_COLOR_CHOICES } from "./props";
import type { WebConfig, WebState } from "./model";

/**
 * W4B-2Z — `web.style_model` là MÔ HÌNH CÓ RÀNG BUỘC, KHÔNG phải trình soạn mã.
 *
 * Đây là target duy nhất chạm tới HTML/CSS, nên nó cũng là chỗ dễ trượt nhất
 * thành `code_experiment` (vẫn DEFERRED). Ranh giới phải ĐO ĐƯỢC chứ không phải
 * hứa trong comment:
 *
 *   1. tập thuộc tính ĐÓNG — tên lạ ⇒ từ chối, không im lặng nhận
 *   2. giá trị ngoài miền ⇒ TỪ CHỐI, không kẹp về biên (kẹp = nói dối)
 *   3. spec của LLM đi qua ĐÚNG cổng mà học sinh đi — không có cửa sau
 *   4. KHÔNG có đường nào thực thi mã: eval / new Function / iframe /
 *      dangerouslySetInnerHTML / thẻ <style> / chuỗi style thô
 *   5. chuỗi CSS hiển thị được SINH từ state ⇒ không thể có hai nguồn sự thật
 */

const mod = makeWebStyleModule();

const okConfig = (over: Record<string, unknown> = {}) => ({
  heading: "Chào các bạn",
  paragraph: "Đoạn văn giới thiệu ngắn.",
  style: { backgroundColor: "#fde68a", fontSize: 24 },
  ...over,
});

const initState = (): WebState => {
  const r = mod.validateConfig(okConfig());
  if (!r.ok) throw new Error(r.error);
  return mod.init(r.config as WebConfig);
};

// ── 1. tập thuộc tính đóng ────────────────────────────────────
describe("W4B-2Z · tập thuộc tính ĐÓNG", () => {
  it("thuộc tính ngoài danh sách ⇒ null (fail-closed), không âm thầm bỏ qua", () => {
    const s = initState().style;
    for (const bad of ["position", "heading", "background", "onclick", "__proto__", "src"]) {
      expect(applyStyleChange(s, bad, "absolute"), bad).toBeNull();
    }
  });

  it("màu ngoài bảng ⇒ null, kể cả màu CSS hợp lệ", () => {
    const s = initState().style;
    // `red` là màu CSS THẬT — vẫn phải bị từ chối, vì miền là bảng đã khai
    // chứ không phải "cái gì trình duyệt hiểu được".
    for (const bad of ["red", "#123456", "rgb(0,0,0)", "url(x)", ""]) {
      expect(applyStyleChange(s, "backgroundColor", bad), bad).toBeNull();
    }
    for (const c of COLOR_CHOICES) {
      expect(applyStyleChange(s, "backgroundColor", c.value)?.backgroundColor).toBe(c.value);
    }
    for (const c of TEXT_COLOR_CHOICES) {
      expect(applyStyleChange(s, "color", c.value)?.color).toBe(c.value);
    }
  });

  it("bảng màu nền và bảng màu chữ là hai miền RIÊNG, không dùng lẫn", () => {
    const s = initState().style;
    const bgOnly = COLOR_CHOICES.map((c) => c.value as string)
      .filter((v) => !(TEXT_COLOR_CHOICES as readonly { value: string }[]).some((t) => t.value === v));
    expect(bgOnly.length).toBeGreaterThan(0);
    for (const v of bgOnly) expect(applyStyleChange(s, "color", v), v).toBeNull();
  });
});

// ── 2. biên số: từ chối, không kẹp ────────────────────────────
describe("W4B-2Z · giá trị số ngoài miền bị TỪ CHỐI, không kẹp về biên", () => {
  it("mỗi thuộc tính số: nhận trong [min, max], từ chối ngoài biên", () => {
    const s = initState().style;
    for (const [name, r] of Object.entries(NUMERIC_RANGE)) {
      expect(applyStyleChange(s, name, r.min), name)!.not.toBeNull();
      expect(applyStyleChange(s, name, r.max), name)!.not.toBeNull();
      /* Kẹp im lặng sẽ trả về một style HỢP LỆ với giá trị biên — test này đỏ
         ngay nếu ai đó khôi phục `clamp`. */
      expect(applyStyleChange(s, name, r.max + 1), `${name} > max`).toBeNull();
      expect(applyStyleChange(s, name, r.min - 1), `${name} < min`).toBeNull();
    }
  });

  it("không phải số nguyên hữu hạn ⇒ null", () => {
    const s = initState().style;
    for (const bad of [NaN, Infinity, 16.5, "16", true, null]) {
      expect(applyStyleChange(s, "fontSize", bad as never), String(bad)).toBeNull();
    }
  });
});

// ── 3. spec của LLM đi qua ĐÚNG cổng của học sinh ─────────────
describe("W4B-2Z · một cổng, hai lối vào", () => {
  it("config mang giá trị ngoài miền ⇒ validateConfig TỪ CHỐI", () => {
    for (const style of [
      { backgroundColor: "red" },
      { fontSize: 200 },
      { position: "absolute" },
      { borderRadius: -4 },
    ]) {
      const r = mod.validateConfig(okConfig({ style }));
      expect(r.ok, JSON.stringify(style)).toBe(false);
    }
  });

  it("config thiếu khoá ⇒ điền mặc định, config LUÔN đủ bảy thuộc tính", () => {
    const r = mod.validateConfig({ heading: "A" });
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(Object.keys((r.config as WebConfig).style).sort()).toEqual(
      /* W4B-3F: +2 thuộc tính cho `.trang h1`. Trang có cấu trúc thì tiêu đề
         và đoạn văn phải chỉnh được RIÊNG — đó chính là bài học phân cấp. */
      ["backgroundColor", "borderRadius", "color", "fontSize", "headingColor", "headingSize", "padding"],
    );
  });

  it("content rỗng hoặc quá dài ⇒ từ chối (hệ không tự nghĩ ra nội dung)", () => {
    expect(mod.validateConfig({ heading: "   " }).ok).toBe(false);
    expect(mod.validateConfig({ heading: "x".repeat(121) }).ok).toBe(false);
  });

  it("hành động của học sinh cũng bị chặn y hệt — state KHÔNG đổi", () => {
    const s = initState();
    const after = mod.apply!(s, { type: "set_param", name: "fontSize", value: 999 } as never);
    expect(after.style).toEqual(s.style);
  });

  it("Về ban đầu là PHÉP TOÁN trên baseline, không phải nhật ký hoàn tác", () => {
    const s = initState();
    const changed = mod.apply!(s, { type: "set_param", name: "padding", value: 40 } as never);
    expect(isModified(changed)).toBe(true);
    const back = mod.apply!(changed, { type: "toggle", target: "reset" } as never);
    expect(back.style).toEqual(s.baseline);
    expect(isModified(back)).toBe(false);
  });
});

// ── 4. không có đường nào thực thi mã ─────────────────────────
describe("W4B-2Z · KHÔNG phải code_experiment", () => {
  const SOURCES = ["./index.ts", "./apply.ts", "./ui.tsx", "./model.ts", "./props.ts"];
  /* Quét MÃ, không quét chú thích: các file này CÓ NÓI tên những thứ bị cấm để
     giải thích vì sao chúng không có mặt. Quét cả comment thì guard đỏ vì đúng
     đoạn văn khẳng định điều nó muốn kiểm. */
  const read = (rel: string) =>
    readFileSync(new URL(rel, import.meta.url), "utf-8")
      .replace(/\/\*[\s\S]*?\*\//g, "")
      .replace(/^\s*\/\/.*$/gm, "");

  it("không eval / new Function / iframe / innerHTML / thẻ <style>", () => {
    for (const f of SOURCES) {
      const src = read(f);
      for (const bad of [
        "eval(", "new Function", "<iframe", "dangerouslySetInnerHTML",
        "innerHTML", "<style", "document.write", "insertRule", "setAttribute(\"style\"",
      ]) {
        expect(src, `${f}: có ${bad}`).not.toContain(bad);
      }
    }
  });

  it("state KHÔNG mang mã nguồn — chỉ nội dung + bảy thuộc tính đã khai", () => {
    const s = initState();
    /* W4B-4D: +`order`/`baselineOrder` (thứ tự tài liệu — thứ HTML sở hữu) và
       +`selected` (khối đang cầm). Danh sách vẫn KHOÁ CHẶT: thêm khoá nào vào
       state cũng phải đi qua đây, nên không lén nhét được chuỗi mã vào state. */
    expect(Object.keys(s).sort()).toEqual(
      ["baseline", "baselineOrder", "heading", "order", "paragraph", "selected", "style"],
    );
    expect(Object.keys(s.style).sort()).toEqual(
      /* W4B-3F: +2 thuộc tính cho `.trang h1`. Trang có cấu trúc thì tiêu đề
         và đoạn văn phải chỉnh được RIÊNG — đó chính là bài học phân cấp. */
      ["backgroundColor", "borderRadius", "color", "fontSize", "headingColor", "headingSize", "padding"],
    );
  });

  it("bản xem CSS SINH từ state — đổi state thì chuỗi đổi theo, không lưu riêng", () => {
    const s = initState();
    expect(cssTextOf(s.style)).toContain("background-color: #fde68a;");
    const changed = mod.apply!(s, { type: "set_param", name: "backgroundColor", value: "#a7f3d0" } as never);
    expect(cssTextOf(changed.style)).toContain("background-color: #a7f3d0;");
    // Không có khoá nào trong state giữ sẵn chuỗi CSS ⇒ không thể lệch nguồn.
    expect(JSON.stringify(changed)).not.toContain("background-color");
  });
});

// ── 5. EXPLORATION_FIRST: không có tiến trình theo bước ───────
describe("W4B-2Z · không bịa ra trục thời gian", () => {
  it("module KHÔNG khai timeline ⇒ shell không dựng thanh phát", () => {
    expect(mod.timeline).toBeUndefined();
    expect(mod.interactionMode).toBe("exploratory");
  });

  it("Workspace vẽ được và phản ánh state (không rỗng, có nội dung của đề)", () => {
    const s = initState();
    const html = renderToString(
      <mod.Workspace state={s} dispatch={() => {}} config={{} as never} busy={false} />,
    );
    expect(html).toContain("Chào các bạn");
    // thuộc tính hiện tại phải nhìn thấy được ở chính chỗ đang điều khiển
    expect(html).toContain("#fde68a");
  });

  it("XEM TRƯỚC là một TRANG CÓ CẤU TRÚC, không phải một ô chữ", () => {
    /* W4B-3F — ĐÂY LÀ KHIẾU NẠI GỐC, và trước wave này không guard nào canh nó.
     *
     * Bản cũ vẽ đúng MỘT `<div>`: đo được nội dung chỉ lấp 37% bề ngang sân khấu
     * 1622px, và bài "HTML/CSS" không có gì để nói về quan hệ thẻ ↔ hiển thị vì
     * một div không có tổ tiên lẫn anh em.
     *
     * Khoá vào CẤU TRÚC NGỮ NGHĨA, không khoá pixel: phải có tiêu đề `<h1>` và
     * (khi đề có đoạn văn) `<p>`, cả hai NẰM TRONG khung trang. Tiêm lỗi gỡ
     * `<p>` đi phải ĐỎ — nếu không, "trang" tụt lại thành cái ô cũ mà suite vẫn
     * xanh. */
    const s = initState();
    const html = renderToString(
      <mod.Workspace state={s} dispatch={() => {}} config={{} as never} busy={false} />,
    );
    /* Khớp TIỀN TỐ: khung trang mang thêm `is-selected` khi đang được chọn, và
       một phép cắt khớp-chính-xác sẽ trượt về -1 rồi đọc thành "không có h1". */
    const page = html.slice(html.search(/class="web-page[" ]/));
    expect(page, "trang không có tiêu đề").toContain("<h1");
    expect(page, "tiêu đề không mang nội dung của đề").toContain(s.heading);
    expect(s.paragraph.length, "mẫu kiểm phải có đoạn văn").toBeGreaterThan(0);
    expect(page, "trang mất đoạn văn — quay lại thành một khối chữ").toContain("<p");
    expect(page, "đoạn văn không mang nội dung của đề").toContain(s.paragraph);
    // Bảng kiểu phải nói ra CÙNG phân cấp ấy — hai bộ chọn hậu duệ.
    const css = cssTextOf(s.style);
    expect(css).toContain(".trang h1");
    expect(css).toContain(".trang p");
  });

  it("XEM TRƯỚC vẽ ĐÚNG state — renderer không được có nguồn sự thật riêng", () => {
    /* W4B-3F — LỖ HỔNG DO TIÊM LỖI BẮT ĐƯỢC, không phải phòng xa.
     *
     * Hợp đồng authenticity đã khai `artifact_reflects_style_state` từ W4B-2Z,
     * nhưng KHÔNG test nào kiểm nó. Tiêm lỗi một dòng vào renderer —
     *     const s = { ...state.style, headingSize: 40 };
     * — đi lọt trọn vẹn 23 test: học sinh kéo thanh trượt lên 28, trang vẽ 40,
     * và bảng CSS in ra 40 nên hai bản chiếu vẫn "khớp nhau" trong khi cả hai
     * cùng SAI so với state. Đó đúng là ca xấu nhất: sai một cách nhất quán.
     *
     * Nên khoá vào QUAN HỆ state → pixel: mọi giá trị số/màu của state phải xuất
     * hiện trong HTML đã dựng, và giá trị KHÔNG thuộc state thì không được. */
    const s = initState();
    const html = renderToString(
      <mod.Workspace state={s} dispatch={() => {}} config={{} as never} busy={false} />,
    );
    for (const [k, v] of Object.entries(s.style)) {
      const needle = typeof v === "number" ? `${v}px` : String(v);
      expect(html, `xem trước không phản ánh ${k}=${needle}`).toContain(needle);
    }
    /* Đối chứng: một giá trị hợp lệ về miền nhưng KHÔNG phải state hiện tại thì
       không được xuất hiện — nếu không, phép dò trên sẽ xanh với mọi thứ. */
    const unused = s.style.headingSize === 40 ? "44px" : "40px";
    expect(html, `xem trước in ${unused} — giá trị này không có trong state`)
      .not.toContain(unused);
  });
});
