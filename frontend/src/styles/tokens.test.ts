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

/** Cắt một khối `{...}` cân bằng ngoặc, tính từ vị trí `from`. `indexOf("}")`
 *  không dùng được cho `@media` vì bên trong còn khối con. */
function balancedBlock(css: string, from: number): string | null {
  const open = css.indexOf("{", from);
  if (open < 0) return null;
  let depth = 0;
  for (let i = open; i < css.length; i++) {
    if (css[i] === "{") depth++;
    else if (css[i] === "}" && --depth === 0) return css.slice(open, i + 1);
  }
  return null;
}

/**
 * W13-A11Y — HỆ ĐIỀU HÀNH ĐÃ NÓI "GIẢM CHUYỂN ĐỘNG" THÌ SẢN PHẨM PHẢI NGHE.
 *
 * ─── LỖ HỔNG ĐO ĐƯỢC Ở HEAD d7102e1 ──────────────────────────────────────
 *
 * `grep -rc "prefers-reduced-motion" frontend/src` = **0**, trong khi kho có 3
 * `@keyframes`, 3 `animation:`, 25 `transition:`. Không test nào bắt được vì
 * vitest không chạy CSS, và mắt người thì không nhìn ra thứ VẮNG MẶT.
 *
 * ─── VÌ SAO GUARD KHOÁ "BỘ CHỌN PHỔ QUÁT", KHÔNG KHOÁ TỪNG LỚP ───────────
 *
 * Khoá từng lớp là khoá lần đã xảy ra. Bắt buộc khối reduce phải phủ qua `*`
 * thì mọi `transition` viết THÊM sau này tự động nằm trong tầm — kể cả của
 * miền hình học không gian chưa viết. Cùng tinh thần với anti-pattern #13:
 * đặt guard ở chỗ không phụ thuộc thứ đã tồn tại.
 *
 * Đường thoát duy nhất còn lại là một khai báo `animation`/`transition` mang
 * `!important` đặt NGOÀI khối reduce — nó sẽ thắng cả bộ chọn phổ quát. Nên
 * guard cấm đúng đường đó.
 */
describe("(W13-A11Y) prefers-reduced-motion — hoạt cảnh phải xin phép", () => {
  const at = globalCss.indexOf("@media (prefers-reduced-motion: reduce)");
  const block = at < 0 ? null : balancedBlock(globalCss, at);

  it("có khối @media (prefers-reduced-motion: reduce)", () => {
    expect(
      at,
      "không có khối nào — học sinh bật 'Giảm chuyển động' vẫn nhận đủ hoạt cảnh",
    ).toBeGreaterThan(-1);
    expect(block, "khối @media không đóng ngoặc cân bằng").not.toBeNull();
  });

  it("vô hiệu hoá ở tầng PHỔ QUÁT — hoạt cảnh viết sau này cũng bị phủ", () => {
    expect(block, "chưa có khối reduce").not.toBeNull();
    expect(block!, "thiếu bộ chọn `*` ⇒ chỉ phủ được thứ đã liệt kê").toMatch(/(^|[\s,{])\*/);
    for (const prop of ["animation-duration", "transition-duration"]) {
      expect(block!, `khối reduce không đặt ${prop}`).toContain(prop);
    }
    // Không `!important` thì bộ chọn `*` (độ đặc hiệu 0) thua mọi lớp thật.
    expect(
      (block!.match(/!important/g) ?? []).length,
      "thiếu !important ⇒ bộ chọn `*` độ đặc hiệu 0, thua mọi khai báo có lớp",
    ).toBeGreaterThanOrEqual(3);
  });

  /**
   * `.composer-spin` là chỉ báo DUY NHẤT cho "AI đang phân tích" — nằm trong
   * nút gửi, không kèm chữ, `aria-label` không đổi khi chạy. Dừng hẳn nó là
   * lấy mất THÔNG TIN chứ không chỉ lấy mất hoạt cảnh. Nó được quay chậm lại,
   * và dòng này giữ cho ngoại lệ đó không bị ai "dọn cho gọn".
   */
  it("giữ ngoại lệ .composer-spin — quay CHẬM, không TẮT", () => {
    expect(block, "chưa có khối reduce").not.toBeNull();
    const at2 = block!.indexOf(".composer-spin");
    expect(at2, "ngoại lệ biến mất ⇒ chỉ báo tiến trình tắt câm").toBeGreaterThan(-1);
    const spin = balancedBlock(block!, at2);
    expect(spin, "khối .composer-spin hỏng").not.toBeNull();
    expect(spin!, "ngoại lệ mà không lặp ⇒ chỉ báo đứng im").toContain("infinite");
    const dur = /animation-duration:\s*([\d.]+)s/.exec(spin!);
    expect(dur, "ngoại lệ không đặt lại thời lượng").not.toBeNull();
    expect(
      Number(dur![1]),
      "quay nhanh hơn 1.5s thì vẫn là kích thích tiền đình",
    ).toBeGreaterThanOrEqual(1.5);
  });

  it("KHÔNG có animation/transition !important nào NGOÀI khối reduce", () => {
    const ngoai = block ? globalCss.replace(block, "") : globalCss;
    const offenders = [...ngoai.matchAll(/(?:^|[;{}\s])(animation|transition)[a-z-]*:[^;}]*!important/gi)]
      .map((m) => m[0].trim());
    expect(
      offenders,
      "khai báo này thắng cả bộ chọn `*` ⇒ giảm-chuyển-động bị vô hiệu trong im lặng:\n" +
        offenders.join("\n"),
    ).toEqual([]);
  });
});

/**
 * W13-A11Y — TƯƠNG PHẢN CHỮ (WCAG 2.1 AA, 4.5:1).
 *
 * ─── VÌ SAO KHÔNG CHẤM MỌI TOKEN ─────────────────────────────────────────
 *
 * `--hairline` 1.25:1 và `--accent-sky` 2.38:1 "trượt" nếu chấm phẳng cả bảng
 * màu — nhưng chúng là VIỀN và NỀN, ngưỡng của chúng không phải 4.5. Chấm
 * phẳng sinh ra 10 phát hiện giả rồi chôn 4 phát hiện thật. Nên guard chỉ xét
 * token THẬT SỰ đứng sau `color:`.
 *
 * ⚠️ Và `color:` phải khớp ở BIÊN KHAI BÁO. Bản nháp đầu của guard này dùng
 * `/color:\s*var\(/` nên khớp luôn `border-color:` / `outline-color:` —
 * `--hairline` hiện ra như "màu chữ 2 chỗ" trong khi nó chưa bao giờ là chữ.
 * Đó là phát hiện giả sinh ra từ chính công cụ đo.
 *
 * ─── VÌ SAO CÓ DANH SÁCH NỢ, KHÔNG ĐỎ NGAY ───────────────────────────────
 *
 * Bốn token dưới đây đang trượt ở 55 chỗ dùng. Sửa chúng KHÔNG phải việc của
 * một guard: `--ink-faint` (#a39e98) muốn đạt 4.5:1 phải tối tới quãng
 * `#6f6a63`, tức gần trùng `--ink-muted` (#615d59) — thang mực BA BẬC của
 * `DESIGN.md` sập còn hai. Đó là quyết định ngôn ngữ thị giác, thuộc về người
 * làm thiết kế, và anti-pattern #12 cấm agent tự chế.
 *
 * Nên guard làm đúng việc của guard: **ghim con số đo được** và bắt danh sách
 * này chỉ được NGẮN ĐI. Thêm token trượt mới ⇒ ĐỎ. Sửa xong mà quên xoá dòng
 * ⇒ cũng ĐỎ. Cùng khuôn với `KNOWN_GAPS` của code-index-guard.
 */
describe("(W13-A11Y) tương phản chữ — WCAG AA 4.5:1", () => {
  const AA_TEXT = 4.5;

  /** Giá trị hex của một token, đọc từ tokens.css (không hard-code màu). */
  function hexOf(token: string): string | null {
    const m = new RegExp(`${token}\\s*:\\s*(#[0-9a-f]{3,8})`, "i").exec(tokensCss);
    return m ? m[1] : null;
  }

  /** Độ chói tương đối theo WCAG 2.1 §relative luminance. */
  function luminance(hex: string): number {
    const h = hex.replace("#", "");
    const full = h.length === 3 ? [...h].map((c) => c + c).join("") : h;
    const [r, g, b] = [0, 2, 4].map((i) => {
      const c = parseInt(full.slice(i, i + 2), 16) / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }

  function contrast(a: string, b: string): number {
    const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
    return (hi + 0.05) / (lo + 0.05);
  }

  /** Hai nền mà chữ thân bài thực sự nằm lên. */
  const BACKGROUNDS = ["--canvas", "--canvas-soft"];

  /**
   * `--on-primary` (#ffffff) là chữ trên NỀN `--primary`, không phải trên
   * canvas — đo nó với nền trang sẽ ra 1:1 và là phát hiện giả.
   */
  const KHONG_NAM_TREN_CANVAS = new Set(["--on-primary"]);

  /**
   * NỢ ĐÃ ĐO — `token@nền` → tỉ lệ tại thời điểm ghi (HEAD d7102e1).
   * DANH SÁCH NÀY CHỈ ĐƯỢC NGẮN ĐI. Thêm dòng = tự khai vừa tạo nợ mới.
   */
  const NO_TUONG_PHAN: Record<string, number> = {
    /* PHÂN CÔNG GIỮA HAI PHÉP ĐO — đây là lý do cả hai cùng tồn tại.
       Lượt Chrome W13 quét **26 bề mặt · 104 bước · 5431 phần tử có chữ** và
       thấy 0 cặp trượt: mọi chỗ accent tô chữ mà THỰC SỰ hiện ra đã chuyển
       sang bậc `-deep`. Bước qua timeline là thứ tìm ra 5 lỗi cuối
       (`.hold-label`, `.loop-back.is-active`, `.acc-arrow`, nhãn nút mạng) —
       chúng chỉ tồn tại ở TRẠNG THÁI, đo mỗi target một khung thì vô hình.
       Nhưng vẫn còn **5 chỗ `--accent-orange` và 4 chỗ `--accent-green`** đứng
       sau `color:` mà 104 bước đó chưa render tới. Trình duyệt nói được cái ĐÃ
       CHỨNG MINH; dòng nợ này giữ cái CÒN CÓ THỂ XẢY RA — một đoạn chữ accent
       mới đặt lên nền sáng sẽ trượt lại. Xoá chúng chỉ khi số dùng về 0. */
    "--accent-orange@--canvas": 3.77,
    "--accent-orange@--canvas-soft": 3.46,
    "--accent-green@--canvas": 2.93,
    "--accent-green@--canvas-soft": 2.69,
    /* `--primary` ĐẠT trên nền trắng (4.57), chỉ trượt trên thẻ nền xám ấm.
       Chỗ THẬT SỰ trượt mà Chrome bắt được — `.link-btn` "Xem thư viện" — đã
       chuyển sang `--primary-active`. Dòng này ở lại vì luật vẫn đúng: một
       đoạn chữ `--primary` đặt MỚI lên thẻ `--canvas-soft` sẽ lại trượt. */
    "--primary@--canvas-soft": 4.19,
  };

  /** Token đứng sau `color:` — khớp ở BIÊN khai báo, xem cảnh báo phía trên. */
  const textTokens = [
    ...new Set(
      [...globalCss.matchAll(/(?:^|[;{}\s])color:\s*var\(\s*(--[a-z0-9-]+)/gi)].map((m) => m[1]),
    ),
  ].filter((t) => !KHONG_NAM_TREN_CANVAS.has(t));

  it("có tìm ra token màu chữ (guard không rỗng vô nghĩa)", () => {
    expect(textTokens.length, "không khớp token nào ⇒ regex hỏng, guard luôn xanh")
      .toBeGreaterThan(5);
  });

  it("mọi token màu chữ đều là hex đọc được", () => {
    const la = textTokens.filter((t) => hexOf(t) === null);
    expect(la, `guard chỉ hiểu hex — token này không đo được: ${la.join(", ")}`).toEqual([]);
  });

  it("không có token màu chữ TRƯỢT AA nào nằm ngoài danh sách nợ", () => {
    const moi: string[] = [];
    for (const t of textTokens) {
      const fg = hexOf(t);
      if (!fg) continue;
      for (const bgToken of BACKGROUNDS) {
        const bg = hexOf(bgToken);
        if (!bg) continue;
        const r = contrast(fg, bg);
        const key = `${t}@${bgToken}`;
        if (r < AA_TEXT && !(key in NO_TUONG_PHAN)) {
          moi.push(`${key} = ${r.toFixed(2)}:1 (cần ${AA_TEXT})`);
        }
      }
    }
    expect(moi, `nợ tương phản MỚI — chỉ được ngắn đi, không được dài ra:\n${moi.join("\n")}`)
      .toEqual([]);
  });

  /**
   * W13-A11Y — TOKEN ĐƯỜNG KẺ KHÔNG ĐƯỢC QUAY LẠI LÀM CHỮ.
   *
   * `--ink-faint` (2.66:1) từng gánh HAI vai: chữ phụ ở 37 chỗ VÀ đường
   * kẻ/cạnh đồ thị/viền chấm "chưa xét" ở 5 chỗ. Không sửa được giá trị vì mỗi
   * vai đòi một hướng ngược nhau — chữ cần tối đi, còn tối đi thì chấm "nhàn
   * rỗi" trông như đang hoạt động. Đã tách: chữ sang `--ink-quiet` (#74706c),
   * `--ink-faint` giữ nguyên cho nét vẽ.
   *
   * Sự tách vai đó vô hình trong mã — không có gì ngăn bản vá sau viết lại
   * `color: var(--ink-faint)` và mọi test vẫn xanh, vì token ấy CÓ tồn tại và
   * danh sách nợ không còn nhắc tới nó. Dòng này là thứ duy nhất giữ nó.
   */
  it("token dành cho ĐƯỜNG KẺ không được dùng làm màu chữ", () => {
    const CHI_DUONG_KE = ["--ink-faint", "--hairline"];
    const pham = CHI_DUONG_KE.filter((t) => textTokens.includes(t));
    expect(
      pham,
      "token này chỉ dành cho nét vẽ/viền (tương phản dưới 3:1) — chữ phụ dùng " +
        `\`--ink-quiet\`: ${pham.join(", ")}`,
    ).toEqual([]);
  });

  it("mọi dòng nợ vẫn còn trượt thật — sửa xong phải xoá dòng", () => {
    const da_het: string[] = [];
    const lech: string[] = [];
    for (const [key, ghi] of Object.entries(NO_TUONG_PHAN)) {
      const [t, bgToken] = key.split("@");
      const fg = hexOf(t);
      const bg = hexOf(bgToken);
      if (!fg || !bg) {
        da_het.push(`${key} (token không còn tồn tại)`);
        continue;
      }
      const r = contrast(fg, bg);
      if (r >= AA_TEXT) da_het.push(`${key} nay ĐẠT ${r.toFixed(2)}:1`);
      else if (Math.abs(r - ghi) > 0.05) lech.push(`${key}: ghi ${ghi} nhưng đo ${r.toFixed(2)}`);
    }
    expect(da_het, `đã trả nợ mà quên xoá dòng:\n${da_het.join("\n")}`).toEqual([]);
    expect(lech, `màu đã đổi, số ghi trong nợ không còn đúng:\n${lech.join("\n")}`).toEqual([]);
  });
});
