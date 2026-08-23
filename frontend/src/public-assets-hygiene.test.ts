import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * GUARD: `frontend/public/` KHÔNG được chứa artifact test/evaluation.
 *
 * ─── VÌ SAO CẦN ────────────────────────────────────────────────────────────
 *
 * Vite chép **nguyên văn** mọi thứ trong `public/` vào `dist/`. Nên một file
 * đặt nhầm chỗ đó không chỉ "hơi lộn xộn" — nó được **phát cho mọi người dùng
 * thật** ở production.
 *
 * Ba file đã nằm đó nhiều wave: `e2e_semantic_candidates.json`,
 * `live_gemini_unseen_candidates.json`, `semantic_l5a.json` — tổng 192K
 * envelope thu từ Gemini, thuần tuý phục vụ ba script soát thị giác. Và cả ba
 * script đều đọc chúng bằng `fs.readFileSync`, **chưa bao giờ qua HTTP**: đặt
 * trong `public/` không mang lại lợi ích nào, chỉ có cái giá. Đó là dấu hiệu
 * kinh điển của "để tạm cho tiện" rồi không ai quay lại.
 *
 * ─── VÌ SAO KHÔNG CHỈ CHẶN BA TÊN FILE ĐÓ ─────────────────────────────────
 *
 * Chặn theo tên là chặn *lần đã xảy ra*, không chặn *lớp lỗi*. Guard này phát
 * biểu đúng luật ngữ nghĩa: **thứ mang dấu vết của pipeline nội bộ thì không
 * phải asset công khai**. Một JSON trong `public/` chứa `simulation_id` /
 * `envelope` / `semantic_program` là output đã chụp của hệ, không phải tài
 * nguyên sản phẩm — dù nó tên gì.
 *
 * Guard KHÔNG cấm `public/` có file. Favicon, `robots.txt`, ảnh tĩnh đều hợp
 * lệ và đi qua bình thường.
 */

const SRC = new URL(".", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
const FRONTEND = join(SRC, "..");
const PUBLIC = join(FRONTEND, "public");

/** Dấu vết cho biết một JSON là output đã chụp của pipeline, không phải asset. */
const DAU_VET_PIPELINE = ["simulation_id", "visual_mode", "semantic_program", "envelope"];

/** Mọi file dưới `public/`, đường dẫn tương đối, dùng `/`. */
function moiFileCongKhai(): string[] {
  if (!existsSync(PUBLIC)) return [];
  const ra: string[] = [];
  const di = (dir: string) => {
    for (const ten of readdirSync(dir)) {
      const full = join(dir, ten);
      if (statSync(full).isDirectory()) di(full);
      else ra.push(relative(PUBLIC, full).split(sep).join("/"));
    }
  };
  di(PUBLIC);
  return ra;
}

describe("vệ sinh public/ — artifact test không được lọt vào bản dựng sản phẩm", () => {
  it("không có thư mục `fixtures/` nào trong public/", () => {
    const pham = moiFileCongKhai().filter((f) => f.split("/").includes("fixtures"));
    expect(
      pham,
      `fixture phải ở \`frontend/tests/fixtures/\` (script đọc bằng fs), không ở public/ ` +
        `— mọi thứ trong public/ được Vite chép thẳng vào dist/:\n${pham.map((f) => `  - ${f}`).join("\n")}`,
    ).toEqual([]);
  });

  it("không có JSON nào trong public/ mang dấu vết output pipeline", () => {
    const pham: string[] = [];
    for (const f of moiFileCongKhai()) {
      if (!f.endsWith(".json")) continue;
      const noi_dung = readFileSync(join(PUBLIC, f), "utf-8");
      const trung = DAU_VET_PIPELINE.filter((k) => noi_dung.includes(`"${k}"`));
      if (trung.length > 0) pham.push(`${f} (chứa: ${trung.join(", ")})`);
    }
    expect(
      pham,
      `JSON mang dấu vết pipeline là artifact nội bộ, không phải asset công khai. ` +
        `Chuyển sang \`frontend/tests/fixtures/\` hoặc \`docs/evaluation/\`:\n` +
        pham.map((f) => `  - ${f}`).join("\n"),
    ).toEqual([]);
  });
});
