import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * BẤT BIẾN M9-UX5 — MỌI `var(--token)` PHẢI TỒN TẠI THẬT.
 *
 * Đã cháy: `global.css` gọi `var(--sp-2xl)` nhưng token thật tên là `--sp-xxl`.
 * CSS KHÔNG BÁO LỖI — trình duyệt lặng lẽ vứt CẢ dòng khai báo chứa var() hỏng.
 * Hậu quả im lìm suốt từ M9-UX1:
 *   - `.home-composer { margin: 0 auto var(--sp-2xl) }` → mất margin → ô nhập
 *     KHÔNG được căn giữa (dính mép trái cột 920px);
 *   - `.home-title { margin: var(--sp-2xl) 0 ... }` → tiêu đề dí sát ô nhập;
 *   - `.app-single { padding: ... var(--sp-2xl) }` → mất padding đáy.
 *
 * Không có test nào bắt được vì CSS không chạy trong vitest, và mắt người thì
 * nhìn ra "hơi lệch" chứ không nhìn ra "token không tồn tại". Test này so tên.
 */

/** Bóc chú thích: các chú thích ở đây CÓ NHẮC TÊN token hỏng để giải thích lịch
 *  sử — quét cả chú thích thì test tự bắt chính nó. */
function stripComments(css: string): string {
  return css.replace(/\/\*[\s\S]*?\*\//g, "");
}

const tokensCss = stripComments(readFileSync(new URL("./tokens.css", import.meta.url), "utf-8"));
const globalCss = stripComments(readFileSync(new URL("./global.css", import.meta.url), "utf-8"));

/** Tên biến được ĐỊNH NGHĨA (`--x: value`) — bỏ qua chỗ chỉ dùng (`var(--x)`). */
function definedTokens(css: string): Set<string> {
  const out = new Set<string>();
  for (const m of css.matchAll(/(--[a-z0-9-]+)\s*:/gi)) out.add(m[1]);
  return out;
}

/** Tên biến được DÙNG qua `var(--x)`. */
function usedTokens(css: string): Set<string> {
  const out = new Set<string>();
  for (const m of css.matchAll(/var\(\s*(--[a-z0-9-]+)/gi)) out.add(m[1]);
  return out;
}

describe("(M9-UX5) token CSS — var() hỏng là lỗi IM LẶNG, phải chặn bằng test", () => {
  /**
   * Biến được COMPONENT set inline lúc chạy (không phải token thiết kế) —
   * `--len`: độ dài đoạn thẳng, do `generic/ui.tsx` gán qua `style` để chạy
   * animation vẽ dần cạnh. Hợp lệ, không phải token ma.
   */
  const RUNTIME_VARS = new Set(["--len"]);

  it("mọi var(--token) trong global.css đều được định nghĩa", () => {
    const defined = new Set([...definedTokens(tokensCss), ...definedTokens(globalCss)]);
    const missing = [...usedTokens(globalCss)].filter(
      (t) => !defined.has(t) && !RUNTIME_VARS.has(t),
    );
    expect(missing, `token không tồn tại (CSS sẽ vứt im lặng cả dòng): ${missing.join(", ")}`).toEqual([]);
  });

  it("thang cách có đủ bậc rộng cho trang chủ (--sp-3xl / --sp-4xl)", () => {
    const defined = definedTokens(tokensCss);
    expect(defined.has("--sp-3xl")).toBe(true);
    expect(defined.has("--sp-4xl")).toBe(true);
    // và bậc cũ vẫn còn — không phá vỡ chỗ đang dùng
    for (const t of ["--sp-xs", "--sp-sm", "--sp-md", "--sp-lg", "--sp-xl", "--sp-xxl"]) {
      expect(defined.has(t), `${t} biến mất`).toBe(true);
    }
  });

  it("KHÔNG còn ai gọi --sp-2xl (token ma đã gây lệch bố cục)", () => {
    const used = usedTokens(globalCss);
    expect(used.has("--sp-2xl")).toBe(false);
  });

  /**
   * M17-VR1 — LỖ HỔNG PHẠM VI ĐÃ CHÁY LẦN HAI. Test trên chỉ quét .css, nên
   * `var(--token)` viết TRONG TSX (thuộc tính SVG `stroke`/`fill`, style inline)
   * KHÔNG được canh. Hậu quả thật, phát hiện khi review browser M17-VR1:
   *   - tree-module.tsx + traverse-module.tsx gọi `var(--border)` — token KHÔNG
   *     tồn tại (tên thật `--hairline`) → stroke không hợp lệ → SVG vẽ NONE →
   *     TOÀN BỘ CẠNH CÂY/ĐỒ THỊ VÔ HÌNH và nút chưa thăm mất viền;
   *   - tree-module.tsx gọi `var(--text-muted)` (tên thật `--ink-muted`).
   * Vitest không chạy CSS và SSR test chỉ so text → không test nào bắt được.
   * Nay quét cả nguồn TSX/TS.
   */
  it("mọi var(--token) trong component TSX/TS đều được định nghĩa", () => {
    const defined = new Set([...definedTokens(tokensCss), ...definedTokens(globalCss)]);
    const srcDir = new URL("..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
    const offenders: string[] = [];
    const walk = (dir: string) => {
      for (const name of readdirSync(dir)) {
        const full = join(dir, name);
        if (statSync(full).isDirectory()) walk(full);
        // Bỏ file test: chúng NHẮC TÊN token ma trong chú thích để giải thích
        // lịch sử (kể cả file này) — quét vào thì test tự bắt chính nó.
        else if (/\.tsx?$/.test(name) && !/\.test\.tsx?$/.test(name)) {
          for (const t of usedTokens(readFileSync(full, "utf-8"))) {
            if (!defined.has(t) && !RUNTIME_VARS.has(t)) {
              offenders.push(`${full.replace(srcDir, "")} → ${t}`);
            }
          }
        }
      }
    };
    walk(srcDir);
    expect(
      [...new Set(offenders)],
      "token ma trong TSX (trình duyệt bỏ im lặng — vd stroke SVG thành none)",
    ).toEqual([]);
  });
});

/**
 * DESIGN.md §Elevation — BÓNG ĐỔ PHẢI LÀ TOKEN, KHÔNG PHẢI TỰ CHẾ.
 *
 * ─── LỖI ĐÃ ĐO ĐƯỢC ───────────────────────────────────────────────────────
 *
 * DESIGN.md khai đúng ba mức: Level 0 "hairline border, NO shadow" cho bề mặt
 * mặc định · Level 1 = chồng BỐN lớp gần trong suốt (`--shadow-soft`) cho thẻ
 * nổi · Level 2 (`--shadow-elevated`) cho modal/popover. Và §Don't nói thẳng:
 * *"Don't drop heavy shadows; elevation is many near-transparent layers, never
 * a hard cast."*
 *
 * Nhưng ba chỗ vẫn tự viết bóng MỘT LỚP ngoài token:
 *   - `.composer-box` `0 1px 3px` **lúc nghỉ** — ô nhập đề nổi lên khỏi trang,
 *     trong khi §Inputs nói bóng chỉ được thêm KHI FOCUS;
 *   - `.starter-card:hover` và `.session-card:hover` `0 2px 10px` — đúng dạng
 *     "hard cast" bị cấm.
 *
 * Không guard nào bắt: `tokens.test.ts` chỉ kiểm `var()` trỏ token có thật, mà
 * bóng tự chế thì KHÔNG dùng `var()` nên nó vô hình với phép kiểm đó.
 *
 * Ngoại lệ ĐƯỢC PHÉP: `box-shadow: 0 0 0 Npx <màu>` — đó là VÒNG VIỀN (ring)
 * để đánh dấu lựa chọn, không phải độ nổi. Nó không có blur nên không đổ bóng.
 */
describe("DESIGN.md §Elevation — không bóng tự chế", () => {
  it("mọi box-shadow CÓ ĐỘ MỜ đều phải đến từ token", () => {
    const offenders: string[] = [];
    for (const line of globalCss.split("\n")) {
      const m = /box-shadow:\s*([^;]+);/.exec(line);
      if (!m) continue;
      const value = m[1].trim();
      if (value.includes("var(--shadow")) continue;   // token: hợp lệ
      if (value === "none" || value.startsWith("inset")) continue;
      // Ring: `0 0 0 Npx màu` — không blur, không phải độ nổi.
      if (/^0\s+0\s+0\s+[\d.]+px\s/.test(value)) continue;
      offenders.push(value);
    }
    expect(
      offenders,
      "dùng `var(--shadow-soft)` / `var(--shadow-elevated)`, hoặc bỏ hẳn " +
        `(Level 0 = hairline, không bóng):\n${offenders.join("\n")}`,
    ).toEqual([]);
  });

  it("ô nhập đề PHẲNG lúc nghỉ, chỉ nổi khi focus (DESIGN.md §Inputs)", () => {
    const at = globalCss.indexOf(".composer-box {");
    expect(at, "không tìm thấy .composer-box").toBeGreaterThan(-1);
    const rest = ".composer-box:focus-within";
    const block = globalCss.slice(at, globalCss.indexOf("}", at));
    expect(block, "ô nhập mang bóng ngay lúc nghỉ").not.toContain("box-shadow:");
    const focusAt = globalCss.indexOf(rest);
    expect(focusAt, "mất trạng thái focus").toBeGreaterThan(-1);
    expect(globalCss.slice(focusAt, globalCss.indexOf("}", focusAt)))
      .toContain("var(--shadow-soft)");
  });
});

/**
 * M18-UI — CỘT TRÁI KHÔNG ĐƯỢC HỞ KHI TRANG DÀI HƠN KHUNG NHÌN.
 *
 * ─── LỖI ĐÃ ĐO ĐƯỢC ───────────────────────────────────────────────────────
 *
 * Bản đầu gộp ba việc vào một phần tử: `.app-nav` vừa `position: sticky`, vừa
 * `height: 100vh`, vừa mang nền. Sticky KHÔNG kéo dài nền được — nó chỉ ghim
 * phần tử trong khung nhìn. Nên trên trang Thư viện (tài liệu cao 2036px, khung
 * nhìn 804px) cột trái chỉ được tô trắng đúng 804px, phần còn lại lộ nền xám
 * `--canvas-soft` của body: một vệt HỞ chạy dọc suốt phần cuộn.
 *
 * Cách chữa là TÁCH VAI: `.app-nav-shell` là flex item nên nó cao bằng cả tài
 * liệu (align-items: stretch mặc định) và mang màu; `.app-nav` bên trong vẫn
 * dính. Guard này khoá đúng sự tách đó.
 *
 * Vì sao không kiểm bằng render: bố cục cột chỉ tồn tại khi CSS chạy thật, mà
 * vitest không có engine bố cục. Bằng chứng thị giác nằm ở lượt đo Chrome
 * (`docs/evaluation/m18/`); dòng này giữ cho cấu trúc không bị gộp lại.
 */
describe("M18-UI — nền thanh bên thuộc về VỎ, không thuộc phần tử dính", () => {
  const rule = (sel: string) => {
    const i = globalCss.indexOf(`${sel} {`);
    return i < 0 ? null : globalCss.slice(i, globalCss.indexOf("}", i));
  };

  it("vỏ mang MÀU + VIỀN, và KHÔNG dính", () => {
    const shell = rule(".app-nav-shell");
    expect(shell, "không tìm thấy .app-nav-shell").not.toBeNull();
    expect(shell!, "vỏ không mang nền").toContain("background:");
    expect(shell!, "vỏ không mang viền phải").toContain("border-right:");
    expect(shell!, "vỏ mà lại dính ⇒ nền hết cao bằng tài liệu")
      .not.toContain("position: sticky");
  });

  it("phần dính KHÔNG mang nền — nếu mang thì nó chỉ tô được 100vh", () => {
    const nav = rule(".app-nav");
    expect(nav, "không tìm thấy .app-nav").not.toBeNull();
    expect(nav!).toContain("position: sticky");
    expect(nav!, "phần dính lại mang nền — đúng cái đã gây hở").not.toContain("background:");
    expect(nav!, "phần dính lại mang viền phải").not.toContain("border-right:");
  });
});
