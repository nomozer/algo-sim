import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * VỆ SINH UI — QUÉT MÃ NGUỒN, KHÔNG QUÉT HTML ĐÃ RENDER (M9-UX6).
 *
 * VÌ SAO ĐỔI CÁCH QUÉT: guard đầu tiên (M9-UX5) quét `renderToString(<App/>)` —
 * nhưng SSR chỉ đi qua **trạng thái đầu** (Home) nên nó KHÔNG bao giờ chạm tới
 * workspace. Hậu quả: emoji 🔮 trong `PredictionBar` và chuỗi `find_max` trong
 * `AnalysisCard` **lọt qua guard xanh lè**, rồi người dùng chụp màn hình gửi lại.
 *
 * Bài học: guard phải đặt ở chỗ KHÔNG phụ thuộc route nào được test đi qua.
 * Quét thẳng mã nguồn thì mọi component đều bị soi, kể cả component chưa có test.
 */

const SRC = new URL("..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");

function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walk(full, out);
    else if (/\.tsx?$/.test(name) && !/\.test\.tsx?$/.test(name)) out.push(full);
  }
  return out;
}

const FILES = walk(SRC).map((f) => ({ path: f, text: readFileSync(f, "utf-8") }));

/**
 * Bóc chú thích + import: các chú thích ở repo này CỐ Ý nhắc tên ký tự đã cấm để
 * ghi lại lịch sử ("thay ⏮ ◀ ▶"), quét cả chú thích thì test tự bắt chính nó.
 */
function code(text: string): string {
  return text
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/^\s*\/\/.*$/gm, "")
    .replace(/^import .*$/gm, "");
}

describe("(M9-UX6) UI hygiene — quét MÃ NGUỒN, không phụ thuộc route nào được test", () => {
  /**
   * Emoji + ký tự hình khối làm icon. `◧` (U+25E7) từng thành Ô VUÔNG RỖNG trên
   * Windows; emoji thì mỗi OS vẽ một kiểu, không ăn theo màu chữ. Icon = SVG.
   */
  it("KHÔNG emoji / ký tự Unicode làm icon trong bất kỳ component nào", () => {
    const BANNED = ["◧", "◨", "▸", "◀", "▶", "⏮", "⏭", "⏸", "⟳", "↺", "✕", "✓", "✗", "＋", "⌁"];
    const EMOJI = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u;

    const offenders: string[] = [];
    for (const f of FILES) {
      if (f.path.endsWith("icons.tsx")) continue; // nơi ĐỊNH NGHĨA icon
      const body = code(f.text);
      for (const ch of BANNED) {
        if (body.includes(ch)) offenders.push(`${f.path}: ký tự "${ch}"`);
      }
      const m = body.match(EMOJI);
      if (m) offenders.push(`${f.path}: emoji "${m[0]}"`);
    }
    expect(offenders, `dùng components/icons.tsx thay vì:\n${offenders.join("\n")}`).toEqual([]);
  });

  /**
   * Chuỗi định danh kĩ thuật (`simulation_id`, `algorithm_id`) là khoá định tuyến
   * NỘI BỘ. Đã lọt lên UI học sinh BA lần: InputPanel → HistoryView → AnalysisCard.
   * Ba lần đều vá một chỗ mà không vá chỗ kia. Nay chặn ở mã nguồn.
   */
  it("KHÔNG render simulation_id / algorithm_id ra UI học sinh", () => {
    const offenders: string[] = [];
    for (const f of FILES) {
      // renderer/registry/legacy ĐƯỢC PHÉP dùng id (chúng định tuyến, không hiển thị)
      if (!/[/\\]components[/\\]/.test(f.path)) continue;
      const body = code(f.text);
      // Dấu hiệu HIỂN THỊ: id nằm trong biểu thức JSX. Nhưng DÙNG id làm KHOÁ TRA
      // bảng tên tiếng Việt (`ALGORITHM_NAMES[analysis.algorithm_id]`) là hợp lệ —
      // thứ hiện ra màn hình là cái TÊN, không phải cái id.
      const rendersRawId = /\{[^}]*\.algorithm_id[^}]*\}/.test(body) &&
        !/_NAMES\[[^\]]*\.algorithm_id\]/.test(body);
      if (rendersRawId) {
        offenders.push(`${f.path}: render algorithm_id`);
      }
      if (/\{[^}]*\.simulationId[^}]*\}/.test(body) && !/previewKindOf|getSimulation/.test(body)) {
        offenders.push(`${f.path}: render simulationId`);
      }
      if (/\{[^}]*\.simId[^}]*\}/.test(body) && !/previewKindOf/.test(body)) {
        offenders.push(`${f.path}: render simId`);
      }
    }
    expect(offenders, `chuỗi kĩ thuật lọt lên UI:\n${offenders.join("\n")}`).toEqual([]);
  });
});

/**
 * NGÔN NGỮ THIẾT KẾ (DESIGN.md) — hai luật "Don't" quan trọng nhất, khoá bằng code.
 *
 * Đã vi phạm: một bản thiết kế lấy TÍM (sticker palette) tô nút "Có" và nút
 * "Kiểm tra", tô nền thẻ dự đoán, viền trái tím — tức là biến màu TRANG TRÍ thành
 * ACCENT CẤU TRÚC THỨ HAI. DESIGN.md cấm cả hai điều đó.
 */
describe("(M9-UX6) DESIGN.md — sticker palette là TRANG TRÍ, không sơn hành động", () => {
  const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf-8").replace(
    /\/\*[\s\S]*?\*\//g,
    "",
  );

  /** Cắt CSS thành các rule { selector, body }. */
  const rules = [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)].map((m) => ({
    sel: m[1].trim(),
    body: m[2],
  }));

  it('KHÔNG có nút/CTA nào lấy màu sticker làm nền ("never paint an action")', () => {
    const offenders = rules
      .filter((r) => /\.btn-|composer-send|-toggle\b/.test(r.sel))
      .filter((r) => /background[^;]*var\(--accent-/.test(r.body))
      .map((r) => r.sel);
    expect(offenders, `nút sơn bằng màu trang trí: ${offenders.join(", ")}`).toEqual([]);
  });

  it("form field KHÔNG bo tròn viên thuốc (inputs stay tight at rounded-xs)", () => {
    const offenders = rules
      .filter((r) => /-filter|-search|text-input|composer-text/.test(r.sel))
      .filter((r) => /border-radius[^;]*(--rounded-full|9999px|1[6-9]px|[2-9]\dpx)/.test(r.body))
      .map((r) => r.sel);
    expect(offenders, `ô nhập bo tròn quá: ${offenders.join(", ")}`).toEqual([]);
  });

  it("nút primary khi disabled là XÁM TRUNG TÍNH, không phải xanh mờ", () => {
    const disabled = rules.find((r) => r.sel === ".btn-primary:disabled");
    expect(disabled, ".btn-primary:disabled chưa được khai — sẽ rơi vào opacity .4 toàn cục").toBeDefined();
    expect(disabled!.body).toMatch(/background:\s*var\(--canvas-soft\)/);
    expect(disabled!.body).toMatch(/opacity:\s*1/);
  });
});
