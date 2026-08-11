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

/**
 * W4B-3A — TỪ BA CHỦ SỞ HỮU XUỐNG MỘT.
 *
 * W4B-2W gom ba chỗ dựng nút về CÙNG một class, nhưng vẫn là ba chỗ dựng — nên
 * hai trong ba (hai renderer miền) tiếp tục đặt nút của mình NGAY DƯỚI SÂN KHẤU,
 * và bốn lượt đo bố cục đều thấy dải `experimentTrigger`. Cùng một class không
 * cứu được vị trí sai.
 *
 * Nay `SimulationControls` là chủ sở hữu DUY NHẤT: miền chỉ khai CÂU MỜI
 * (`predict.entry` / `explore.entry`), shell quyết chỗ đặt và trạng thái mở.
 */
const OWNER = "../components/SimulationControls.tsx";
/** Renderer miền — được phép dựng công cụ TRÊN sân khấu, cấm dựng LỐI VÀO. */
const DOMAIN_RENDERERS = [
  "./domains/algorithm/ui.tsx",
  "./domains/network/ui.tsx",
] as const;

describe("W4B-2W · một tầng hành động phụ dùng chung", () => {
  it("chủ sở hữu DUY NHẤT dựng lối vào phụ, và dùng `sim-secondary-action`", () => {
    expect(read(OWNER), "shell không dựng lối vào phụ").toContain("sim-secondary-action");
    for (const f of DOMAIN_RENDERERS) {
      expect(read(f), `${f}: renderer miền dựng lại lối vào phụ (dải quay lại)`)
        .not.toContain("sim-secondary-action");
    }
  });

  it("KHÔNG dải `experiment-trigger` nào còn được dựng ở bất kỳ đâu", () => {
    /* Đây là bất biến trung tâm của W4B-3A, và nó phải khoá theo NGUỒN chứ không
       theo CSS: ẩn bằng `display:none` mà vẫn giữ quyền sở hữu cũ thì bố cục
       sạch còn kiến trúc thì không. */
    for (const f of [OWNER, ...DOMAIN_RENDERERS]) {
      expect(read(f), `${f}: dải experimentTrigger quay lại`)
        .not.toContain("experiment-trigger");
    }
  });

  it("KHÔNG chỗ nào còn dựng lối vào phụ như một nút nội dung `btn-utility`", () => {
    /* `btn-utility` là nút của NỘI DUNG (Đặt lại, Về mạng ban đầu…). Dùng nó cho
       Thí nghiệm/Thử thách chính là thứ khiến chúng đọc thành dải nội dung. */
    for (const f of [OWNER, ...DOMAIN_RENDERERS]) {
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
    for (const f of [OWNER]) {
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
