import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";

/**
 * W4B-2W §13/§18 — THÍ NGHIỆM VÀ THỬ THÁCH LÀ HÀNH ĐỘNG PHỤ, KHÔNG PHẢI NỘI DUNG.
 *
 * Đo được qua nhiều wave ảnh: dưới sân khấu xếp chồng ba DẢI toàn chiều ngang —
 * "Thí nghiệm: …", khe thuyết minh, "Thử thách: …". Mắt đọc thành
 * MÔ HÌNH → DẢI → DẢI → DẢI, tức mô phỏng tụt xuống thành một mục trong bảng
 * điều khiển.
 *
 * Cả hai đều là hành động học sinh CHỦ ĐỘNG mở, nên chúng thuộc cùng MỘT tầng
 * phụ. Ba chỗ dựng nút (shell + hai domain) phải dùng chung một chủ sở hữu, nếu
 * không "nút phụ" sẽ trôi thành ba định nghĩa khác nhau — đúng thứ đã xảy ra.
 */

const read = (rel: string) =>
  readFileSync(new URL(rel, import.meta.url), "utf-8")
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/^\s*\/\/.*$/gm, "");

/** Ba nơi dựng lối vào hành động phụ — dẫn xuất từ nguồn, không chép tay nhãn.
    W4B-2Z §20/§23: lối vào Thử thách của shell đã rời `SimulationWorkspace`
    sang `SimulationControls` — nó nay nằm CẠNH transport thay vì chiếm một dải
    riêng dưới mô hình. Chủ sở hữu đổi, LUẬT giữ nguyên. */
const OWNERS = [
  "../components/SimulationControls.tsx",
  "./domains/algorithm/ui.tsx",
  "./domains/network/ui.tsx",
] as const;

describe("W4B-2W · một tầng hành động phụ dùng chung", () => {
  it("cả ba chủ sở hữu đều dùng `sim-secondary-action`", () => {
    for (const f of OWNERS) {
      expect(read(f), `${f}: dựng lối vào phụ bằng class riêng`)
        .toContain("sim-secondary-action");
    }
  });

  it("KHÔNG chỗ nào còn dựng lối vào phụ như một nút nội dung `btn-utility`", () => {
    /* `btn-utility` là nút của NỘI DUNG (Đặt lại, Về mạng ban đầu…). Dùng nó cho
       Thí nghiệm/Thử thách chính là thứ khiến chúng đọc thành dải nội dung. */
    for (const f of OWNERS) {
      const src = read(f);
      expect(src, `${f}: Thí nghiệm vẫn là nút nội dung`)
        .not.toMatch(/btn-utility[^"'`]*experiment-trigger/);
      expect(src, `${f}: Thử thách vẫn là nút nội dung`)
        .not.toMatch(/btn-utility\$\{challengeOpen/);
    }
  });

  it("tầng phụ có style riêng, KHÔNG thừa hưởng khối của nút nội dung", () => {
    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf-8");
    expect(css).toContain(".sim-secondary-action");
    const block = css.slice(css.indexOf(".sim-secondary-action {"));
    const decl = block.slice(0, block.indexOf("}"));
    // Không nền, không viền khối ⇒ không đọc thành một dải nội dung nữa.
    expect(decl).toMatch(/background:\s*none/);
    expect(decl).toMatch(/border:\s*none/);
    // Vẫn phải tới được bằng bàn phím — lùi thị giác không được lùi khả dụng.
    expect(css).toContain(".sim-secondary-action:focus-visible");
  });

  it("lối vào phụ vẫn là <button> thật — lùi ưu tiên, không lùi khả dụng", () => {
    for (const f of OWNERS) {
      const src = read(f);
      if (!src.includes("sim-secondary-action")) continue;
      /* Tìm class của NÚT, không phải của khối chứa: `sim-secondary-actions`
         (số nhiều) là `<div>` bao ngoài và nó đứng TRƯỚC trong nguồn, nên
         `indexOf` trần sẽ bắt nhầm rồi kết luận "không phải nút thật". */
      const m = /sim-secondary-action(?!s)/.exec(src);
      if (!m) continue;
      const i = m.index;
      // Tìm ngược tới thẻ mở gần nhất: phải là <button>, không phải <div onClick>.
      const before = src.slice(Math.max(0, i - 400), i);
      expect(before, `${f}: lối vào phụ không phải nút thật`).toContain("<button");
    }
  });
});
