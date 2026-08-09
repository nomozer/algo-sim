import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import descriptorsJson from "./capability-descriptors.json";

/**
 * W4B-2V §25 — GUARD TÍNH TOÀN VẸN CỦA BẢNG AUDIT.
 *
 * `docs/SIMULATION_VISUAL_LANGUAGE_AUDIT.md` là một bản kiểm kê, và một bản kiểm
 * kê THIẾU DÒNG thì tệ hơn không có: nó trả lời "không có vấn đề gì ở đó" một
 * cách tự tin. Lượt đo đầu của wave này chết giữa chừng và trả 0 dòng — nếu lúc
 * đó có ai điền tay cho đủ bảng thì không gì phát hiện được.
 *
 * Nên nguồn 22 id KHÔNG được gõ tay ở đây. Nó đọc từ
 * `capability-descriptors.json`, artifact sinh từ registry backend và đã có
 * sync-lock riêng (`capability-descriptors.test.ts`). Thêm/bớt target ở catalog
 * ⇒ guard này đỏ cho tới khi bảng audit theo kịp.
 *
 * Guard kiểm ĐÚNG những gì §25 liệt, không hơn:
 *  - catalog 22 · bảng 22 · id duy nhất 22 · không thừa · không thiếu;
 *  - mỗi dòng TEXT_DEPENDENT phải NÊU TÊN phụ thuộc prose cụ thể;
 *  - mỗi dòng REPRESENTATION_GAP phải NÊU TÊN ngữ nghĩa engine còn thiếu;
 *  - tổng bốn phân loại = 22.
 * Nó KHÔNG phán một phân loại đúng hay sai — đó là việc của người đọc bằng
 * chứng, không phải của regex.
 */

const CATALOG_IDS = Object.keys(
  (descriptorsJson as unknown as { runtime_targets: Record<string, unknown> }).runtime_targets,
).sort();

const AUDIT_PATH = new URL("../../../docs/SIMULATION_VISUAL_LANGUAGE_AUDIT.md", import.meta.url)
  .pathname.replace(/^\/([A-Za-z]:)/, "$1");

const CLASSES = [
  "VISUAL_SELF_SUFFICIENT",
  "VISUAL_WITH_SHORT_CAPTION",
  "TEXT_DEPENDENT",
  "REPRESENTATION_GAP",
] as const;

interface Row {
  cells: string[];
  id: string;
}

/**
 * Đọc mọi bảng markdown, trả các dòng CÓ CHỨA một target id.
 *
 * Nhận id ở **ô bất kỳ**, không chỉ ô đầu. Bản đầu chỉ đọc `cells[0]` và đã đỏ
 * ngay lượt chạy thật: bảng phân loại có thêm cột số thứ tự nên id nằm ở ô thứ
 * hai, và guard báo "chưa được phân loại" cho cả 22 target. Một guard vỡ vì bố
 * cục bảng là guard sẽ bị người ta chỉnh bảng cho vừa nó — nên chỉnh guard.
 *
 * Lấy id KHỚP ĐẦU TIÊN nên ô "bằng chứng" có nhắc tên target khác cũng không
 * cướp được danh tính của dòng.
 */
function tableRows(md: string): Row[] {
  const out: Row[] = [];
  for (const line of md.split("\n")) {
    if (!line.trimStart().startsWith("|")) continue;
    const cells = line.split("|").slice(1, -1).map((c) => c.trim());
    if (cells.length < 3) continue;
    const id = cells.map((c) => c.replace(/`/g, "").trim()).find((c) => CATALOG_IDS.includes(c));
    if (id) out.push({ cells, id });
  }
  return out;
}

describe("W4B-2V §25 · bảng audit thị giác phải phủ đủ 22 target", () => {
  const md = (() => {
    try {
      return readFileSync(AUDIT_PATH, "utf-8");
    } catch {
      return null;
    }
  })();

  it("catalog có đúng 22 target (nguồn: capability-descriptors.json)", () => {
    expect(CATALOG_IDS.length).toBe(22);
  });

  it("tài liệu audit tồn tại", () => {
    expect(md, `không đọc được ${AUDIT_PATH}`).not.toBeNull();
  });

  it("bảng phân loại có đúng 22 dòng, id duy nhất, khớp catalog", () => {
    if (!md) return;
    const rows = tableRows(md);
    /* Một target có thể xuất hiện ở NHIỀU bảng (bảng phân loại + bảng chi tiết).
       Phép đếm phải theo TẬP id, không theo số dòng. */
    const ids = [...new Set(rows.map((r) => r.id))].sort();

    const missing = CATALOG_IDS.filter((c) => !ids.includes(c));
    expect(missing, `target trong catalog nhưng vắng khỏi audit:\n${missing.join("\n")}`).toEqual([]);
    expect(ids.length, "số target được audit").toBe(22);
  });

  it("mỗi target có đúng MỘT phân loại, và tổng bốn lớp = 22", () => {
    if (!md) return;
    const byId = new Map<string, string[]>();
    for (const r of tableRows(md)) {
      const found = CLASSES.filter((c) => r.cells.some((cell) => cell.includes(c)));
      if (found.length === 0) continue;
      byId.set(r.id, [...new Set([...(byId.get(r.id) ?? []), ...found])]);
    }

    const noClass = CATALOG_IDS.filter((c) => !byId.has(c));
    expect(noClass, `target chưa được phân loại:\n${noClass.join("\n")}`).toEqual([]);

    const multi = [...byId.entries()].filter(([, v]) => v.length > 1);
    expect(multi.map(([k, v]) => `${k}: ${v.join(" + ")}`),
      "target mang hai phân loại — bảng tự mâu thuẫn").toEqual([]);

    const total = [...byId.values()].length;
    expect(total, "tổng phân loại phải bằng 22").toBe(22);
  });

  it("dòng TEXT_DEPENDENT / REPRESENTATION_GAP phải NÊU TÊN thứ còn thiếu", () => {
    if (!md) return;
    /* Vì sao khoá riêng: hai lớp này là CÁO BUỘC. Một cáo buộc không kèm chỗ cụ
       thể thì không sửa được, và cũng không phản bác được — nó chỉ làm bảng
       trông nghiêm túc. Ô cuối phải mang nội dung thật, không phải "—"/"NONE". */
    const bad: string[] = [];
    for (const r of tableRows(md)) {
      const cls = CLASSES.find((c) => r.cells.some((cell) => cell.includes(c)));
      if (cls !== "TEXT_DEPENDENT" && cls !== "REPRESENTATION_GAP") continue;
      const detail = r.cells[r.cells.length - 1];
      const empty = detail.length < 12 || /^(—|-|none|n\/a|tbd|\?)$/i.test(detail.replace(/`/g, ""));
      if (empty) bad.push(`${r.id} (${cls}): ô chi tiết = "${detail}"`);
    }
    expect(bad, `phân loại cáo buộc mà không nêu chỗ cụ thể:\n${bad.join("\n")}`).toEqual([]);
  });

  it("tài liệu công bố bốn con số tổng hợp", () => {
    if (!md) return;
    for (const c of CLASSES) {
      expect(md, `thiếu dòng tổng hợp cho ${c}`).toMatch(new RegExp(`${c}\\s*[=:|]\\s*\\**\\s*\\d+`));
    }
  });

  it("phép dò thật sự dò được (tiêm bảng giả thiếu dòng)", () => {
    /* Guard quét một file và trả 0 lỗi trông y hệt guard có parser hỏng
       (ARCHITECTURE_MAP §8 #14). Bắt nó nhận diện một bảng hai dòng trước đã. */
    const fake = [
      "| target_id | classification | chi tiết |",
      "| --- | --- | --- |",
      "| `algorithm.find_max` | VISUAL_SELF_SUFFICIENT | — |",
      "| `tree.traversal` | TEXT_DEPENDENT | — |",
    ].join("\n");
    const rows = tableRows(fake);
    expect(rows.length, "parser không đọc được bảng markdown").toBe(2);
    expect(new Set(rows.map((r) => r.id)).size).toBe(2);
    expect(rows.some((r) => r.cells.some((c) => c.includes("TEXT_DEPENDENT")))).toBe(true);
  });
});
