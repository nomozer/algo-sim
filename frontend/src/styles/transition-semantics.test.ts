import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

/**
 * W10 — HÌNH HỌC DỮ LIỆU (SVG) KHÁC CHUYỂN ĐỘNG BỐ CỤC (HTML).
 *
 * ─── VÌ SAO CẦN MỘT LUẬT NGỮ NGHĨA, KHÔNG PHẢI MỘT DANH SÁCH CẤM ──────────
 *
 * `height` và `width` là hai cái tên mang HAI nghĩa khác hẳn nhau tuỳ phần tử:
 *
 *   <rect height={h}>      h ENCODE giá trị của phần tử mảng. Cho nó chạy mượt
 *                          là làm hiện ra "giá trị vừa đổi bao nhiêu" — đúng
 *                          thứ bài học cần thấy.
 *   <div style="height">   chiều cao của một khối trong dòng chảy tài liệu.
 *                          Cho nó chạy là đẩy mọi thứ bên dưới nhảy theo, và
 *                          học sinh mất chỗ đang nhìn.
 *
 * Một luật cấm theo TÊN THUỘC TÍNH sẽ chặn nhầm `ArrayView` — nơi cột cao lên
 * chính là cách giá trị được kể. Một luật miễn theo TÊN FILE thì mở toang: bản
 * vá HTML sau đó trong cùng file cũng lọt.
 *
 * Nên luật ở đây đọc NGỮ CẢNH PHẦN TỬ: thuộc tính hình học trên phần tử SVG là
 * biểu diễn dữ liệu; thuộc tính bố cục trong CSS trên phần tử HTML là rủi ro và
 * phải khai ngoại lệ kèm lý do.
 */

const SRC = new URL("..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");

/** Thuộc tính HÌNH HỌC của SVG — chúng encode dữ liệu, không đẩy dòng chảy. */
const SVG_GEOMETRY = ["x", "y", "cx", "cy", "r", "rx", "ry", "d", "width", "height",
  "stroke-dashoffset", "stroke-width"];

/** Thuộc tính BỐ CỤC của HTML — chạy chúng là đẩy mọi thứ đứng sau. */
const HTML_LAYOUT = ["width", "height", "padding", "margin", "top", "left", "right",
  "bottom", "flex-basis", "gap", "font-size"];

/** Phần tử SVG mà repo này thật sự vẽ. */
const SVG_TAGS = ["rect", "circle", "ellipse", "line", "polyline", "polygon",
  "path", "g", "text", "tspan", "image", "use"];

/**
 * NGOẠI LỆ CHUYỂN ĐỘNG BỐ CỤC — mỗi dòng phải nói VÌ SAO nó không phá chỗ nhìn.
 *
 * Danh sách này CỐ Ý ngắn. Thêm một dòng = tự khai vừa cho một khối HTML chạy
 * kích thước, nên phải giải trình được.
 */
const LAYOUT_EXCEPTIONS: Record<string, string> = {
  /* HẠNG MỤC THỨ BA, do chính guard này tìm ra: thuộc tính bố cục HTML mà bản
     thân nó LÀ state mô phỏng. `web.style_model` dạy đúng quan hệ "đổi padding
     → hộp giãn ra", nên cho nó chạy mượt là cách kể quan hệ ấy — cùng loại với
     cột SVG cao lên khi giá trị lớn lên, chỉ khác vỏ thẻ. Cấm nó là cấm đúng
     bài học. */
  ".web-page":
    "Trang xem trước là HIỆN VẬT đang được dạy, và `padding` ở đây chính là giá " +
    "trị học sinh vừa đặt — chuyển động là cách quan hệ 'đổi giá trị → hộp đổi' " +
    "hiện ra. Nó nằm trong khung xem trước có biên riêng nên không đẩy nội dung " +
    "học tập nào bên ngoài, và không có gì trong dòng chảy tài liệu đứng sau nó.",
  ".app-nav-shell":
    "Ngăn điều hướng đóng/mở là một CHUYỂN ĐỔI CHẾ ĐỘ do người dùng chủ động " +
    "bấm, không phải hệ quả phụ của dữ liệu đổi. Nó nằm ở rìa màn hình và " +
    "không có nội dung học tập nào đứng sau nó để bị đẩy — sân khấu mô phỏng " +
    "nằm trong lưới riêng và tự căn giữa lại.",
};

function walk(dir: string, out: string[] = []): string[] {
  for (const e of readdirSync(dir)) {
    const p = join(dir, e);
    if (statSync(p).isDirectory()) walk(p, out);
    else if (/\.tsx?$/.test(p) && !/\.test\./.test(p)) out.push(p);
  }
  return out;
}

/** Thẻ mà một dòng `transition` inline đang nằm trong — đọc ngược lên gần nhất. */
function enclosingTag(body: string, index: number): string | null {
  const before = body.slice(Math.max(0, index - 600), index);
  const opens = [...before.matchAll(/<([a-zA-Z][a-zA-Z0-9]*)/g)];
  return opens.length ? opens[opens.length - 1][1] : null;
}

describe("W10 §5 — hình học SVG được phép chạy, bố cục HTML thì không", () => {
  it("CONTROL A: chuyển động hình học trên phần tử SVG được CHẤP NHẬN", () => {
    /* ─── CA MẪU NAY NỘI TUYẾN, KHÔNG ĐỌC MỘT TỆP ─────────────────────────
     *
     * Ca mẫu cũ là `components/ArrayView.tsx` (cột cao lên vì giá trị lớn lên).
     * Tệp ấy đã gỡ cùng chín domain Tin học, và mã hiện tại KHÔNG còn chuyển
     * động hình học SVG nào để làm mẫu — nên một control đọc-tệp sẽ hoặc chết,
     * hoặc phải bỏ đi và guard mất chiều CHẤP NHẬN.
     *
     * Mẫu nội tuyến giữ nguyên điều control này chứng minh: **luật không chặn
     * nhầm chuyển động hình học trên SVG**. Nó còn mạnh hơn ở một điểm — nó
     * đúng kể cả khi kho mã tình cờ không có ví dụ nào.
     */
    const mau = '<rect x="0" style={{ transition: "height 0.3s ease" }} />';
    expect(mau).toMatch(/transition:[^;}]*height/);
    const idx = mau.search(/transition:[^;}]*height/);
    expect(enclosingTag(mau, idx), "chuyển động ấy phải nằm trên phần tử SVG")
      .toBe("rect");
    /* Và chiều ngược lại phải KHÁC — nếu không, `enclosingTag` chỉ đang gật. */
    const xau = '<div style={{ transition: "height 0.3s ease" }} />';
    expect(enclosingTag(xau, xau.search(/transition:/))).toBe("div");
  });

  it("mọi chuyển động inline trong TSX đều nằm trên phần tử SVG", () => {
    /* Đây là chiều FLAG: một `transition` trên `<div>` giữa sân khấu là chuyển
       động bố cục trá hình dưới dạng style inline — nơi guard CSS không nhìn tới. */
    const offenders: string[] = [];
    for (const f of walk(SRC)) {
      const body = readFileSync(f, "utf-8");
      for (const m of body.matchAll(/transition:\s*"([^"]+)"/g)) {
        const props = m[1].split(",").map((s) => s.trim().split(/\s+/)[0]);
        const tag = enclosingTag(body, m.index ?? 0);
        const isSvg = tag !== null && SVG_TAGS.includes(tag);
        if (isSvg) {
          for (const p of props) {
            if (!SVG_GEOMETRY.includes(p) && !["fill", "stroke", "opacity", "transform"].includes(p)) {
              offenders.push(`${f}: <${tag}> chạy "${p}" — không phải hình học/màu SVG`);
            }
          }
          continue;
        }
        for (const p of props) {
          if (HTML_LAYOUT.includes(p)) {
            offenders.push(`${f}: <${tag ?? "?"}> chạy thuộc tính BỐ CỤC "${p}" (inline)`);
          }
        }
      }
    }
    expect(offenders, `chuyển động bố cục trong TSX:\n${offenders.join("\n")}`).toEqual([]);
  });

  it("CONTROL B: transform/opacity luôn được phép", () => {
    /* Chúng chạy trên lớp compositing, không đụng dòng chảy tài liệu — nên
       chúng là cách ĐÚNG để làm một chuyển động mượt mà không đẩy ai. */
    for (const p of ["transform", "opacity"]) {
      expect(HTML_LAYOUT).not.toContain(p);
    }
  });

  it("FAULT A/B: chuyển động thuộc tính BỐ CỤC trong CSS phải khai ngoại lệ", () => {
    const css = readFileSync(join(SRC, "styles/global.css"), "utf-8");
    const offenders: string[] = [];
    /* Quét từng khối `selector { … }` để biết chuyển động thuộc về AI. */
    for (const m of css.matchAll(/(^|\n)([^{}\n][^{}]*)\{([^}]*)\}/g)) {
      const selector = m[2].trim().split("\n").pop()!.trim();
      const block = m[3];
      const t = block.match(/transition:\s*([^;]+);/);
      if (!t) continue;
      const props = t[1].split(",").map((s) => s.trim().split(/\s+/)[0]);
      for (const p of props) {
        if (!HTML_LAYOUT.includes(p)) continue;
        /* `stroke-width`/`border-*` trùng tiền tố nhưng không phải bố cục. */
        if (/^(stroke|border|outline)/.test(p)) continue;
        const declared = Object.keys(LAYOUT_EXCEPTIONS).find((s) => selector.includes(s));
        if (!declared) offenders.push(`${selector} chạy "${p}" mà không khai ngoại lệ`);
      }
    }
    expect(offenders, `chuyển động bố cục chưa khai:\n${offenders.join("\n")}`).toEqual([]);
  });

  it("FAULT C: ngoại lệ phải theo BỘ CHỌN, không phải theo file", () => {
    /* Miễn cả file thì một bản vá HTML sau đó trong cùng file cũng lọt — đúng
       kiểu ngoại lệ rộng mà §7 cấm. */
    for (const [sel, why] of Object.entries(LAYOUT_EXCEPTIONS)) {
      expect(sel.startsWith("."), `${sel}: ngoại lệ phải là một BỘ CHỌN`).toBe(true);
      expect(sel).not.toContain("*");
      expect(why.length, `${sel}: lý do quá ngắn để kiểm chứng`).toBeGreaterThan(80);
      expect(why, `${sel}: lý do phải nói vì sao KHÔNG đẩy chỗ nhìn`)
        .toMatch(/đẩy|chỗ nhìn|dòng chảy|nội dung/);
    }
  });
});
