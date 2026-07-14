import { readFileSync } from "node:fs";
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
});
