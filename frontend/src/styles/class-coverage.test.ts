/**
 * class-coverage.test.ts — MỘT `className` KHÔNG CÓ LUẬT CSS LÀ LỖI IM LẶNG.
 *
 * ─── VÌ SAO ───────────────────────────────────────────────────────────────
 *
 * `.data-table` được bốn bảng dùng và **chưa từng có một dòng CSS nào**. Trình
 * duyệt không cảnh báo, TypeScript không biết, không test nào đỏ — nên nó sống
 * qua nhiều milestone và render thành chữ chạy liền: không viền, không đệm,
 * cột không thẳng hàng. Người dùng bắt được bằng mắt, ở `base_conversion`.
 *
 * Đây đúng họ với `var(--token)` trỏ tới token không tồn tại
 * (`ARCHITECTURE_MAP §8` #11) — thứ mà `tokens.test.ts` đã gác. Lớp CSS thì
 * chưa ai gác, nên gác nốt.
 *
 * ─── PHẠM VI ──────────────────────────────────────────────────────────────
 *
 * Chỉ soi `className="chuỗi hằng"`. Lớp dựng động (template literal, clsx,
 * biến) KHÔNG soi được ở mức mã nguồn — nói rõ giới hạn thay vì giả vờ đã phủ.
 */
import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const SRC = fileURLToPath(new URL("../", import.meta.url));
const CSS = readFileSync(fileURLToPath(new URL("./global.css", import.meta.url)), "utf-8");

function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walk(full, out);
    else if (/\.tsx$/.test(name) && !/\.test\.tsx$/.test(name)) out.push(full);
  }
  return out;
}

/**
 * Lớp KHÔNG cần luật riêng — khai kèm lý do, và danh sách chỉ được NGẮN ĐI.
 *
 * Đây là ngoại lệ THẬT, không phải chỗ giấu nợ: chúng lấy kiểu từ nơi khác
 * (thẻ HTML, thư viện, hoặc chỉ làm móc cho test/script đo).
 */
const NO_RULE_NEEDED: Record<string, string> = {
  stack: "lớp bố cục dùng kèm style inline gap — không có luật riêng theo thiết kế",
  notes: "đoạn chú thích, thừa kế kiểu từ thẻ p",
};

/**
 * NỢ ĐÓNG BĂNG lúc dựng cổng — **chỉ được NGẮN ĐI**.
 *
 * Cùng kỉ luật với `KNOWN_GAPS` của `code-index-sync.test.ts`: thêm một dòng ở
 * đây là tự khai vừa tạo nợ mới; trả xong một mục mà quên xoá dòng cũng ĐỎ.
 *
 * Chúng render TRẦN ngay lúc này — không viền, không đệm, không màu. Chưa sửa
 * vì mỗi cái cần một quyết định thiết kế riêng, khác hẳn `.data-table`/`.tq-table`
 * vốn chỉ cần dùng lại luật bảng đã có. Ghi ra để không ai tưởng là đã sạch.
 */
const KNOWN_GAPS: Record<string, string> = {
  "app-nav-account": "khối tài khoản ở đáy thanh bên",
  "app-nav-logout": "nút đăng xuất",
  "page-head": "tiêu đề trang giao bài",
  "page-sub": "phụ đề trang giao bài",
  "home-view": "vỏ ngoài trang chủ",
  "is-accumulator": "biến thể ô tích luỹ ở vùng thao tác scan",
  "control-zone-meta": "dòng phụ trong khay điều khiển",
  "acc-label": "nhãn biến tích luỹ",
  "decision-consideration": "dòng cân nhắc ở điểm quyết định",
  "tq-stages": "dải các chặng của truy vấn bảng",
  muted: "chữ mờ ở miền web",
};

describe("W12 — mọi className hằng phải có luật CSS", () => {
  const files = walk(SRC);
  const used = new Map<string, string>();
  for (const f of files) {
    const src = readFileSync(f, "utf-8");
    for (const m of src.matchAll(/className="([^"{}]+)"/g)) {
      for (const cls of m[1].split(/\s+/).filter(Boolean)) {
        if (!used.has(cls)) used.set(cls, f.slice(SRC.length).replace(/\\/g, "/"));
      }
    }
  }

  it("quét được lớp — tập rỗng nghĩa là regex hỏng, không phải mã sạch", () => {
    /* Cùng cái bẫy đã làm ba guard W8 'đạt' khi chúng khớp rỗng. */
    expect(used.size).toBeGreaterThan(50);
  });

  it("không lớp nào bị dùng mà chưa có luật", () => {
    const missing = [...used.entries()]
      .filter(([cls]) => !(cls in NO_RULE_NEEDED) && !(cls in KNOWN_GAPS))
      .filter(([cls]) => !new RegExp(`\\.${cls.replace(/[-]/g, "\\-")}(?![\\w-])`).test(CSS))
      .map(([cls, file]) => `${cls}  (${file})`);
    expect(missing, "className không có luật CSS ⇒ render trần, không ai báo").toEqual([]);
  });

  it("KNOWN_GAPS chỉ được NGẮN ĐI — mục đã trả mà quên xoá cũng ĐỎ", () => {
    const stillMissing = Object.keys(KNOWN_GAPS).filter(
      (cls) => !new RegExp(`\\.${cls.replace(/[-]/g, "\\-")}(?![\\w-])`).test(CSS));
    expect(stillMissing.sort(), "mục này đã có luật CSS rồi — xoá khỏi KNOWN_GAPS")
      .toEqual(Object.keys(KNOWN_GAPS).sort());
  });

  it("(đối chứng) một lớp bịa ra bị bắt", () => {
    const fake = "khong-ton-tai-lop-nay";
    expect(new RegExp(`\\.${fake}(?![\\w-])`).test(CSS)).toBe(false);
  });
});
