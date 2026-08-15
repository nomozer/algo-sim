import { describe, expect, it } from "vitest";
import { KNOWN_ENGINE_VARS, varLabel, varPhrase } from "./var-label";

/**
 * RANH GIỚI: TÊN BIẾN NÀO ĐƯỢC PHÉP ĐỨNG TRƯỚC MẶT HỌC SINH.
 *
 * Quét 23/23 target trên trình duyệt thật đọc được `algorithm.scan` nói với
 * học sinh: **"Khởi tạo nguong = 4."** — một chuỗi máy không dấu.
 *
 * ─── PHÉP ĐO ĐẦU TIÊN CỦA TÔI SAI, VÀ CONTRACT TEST ĐÃ BẮT ────────────────
 *
 * Bản vá đầu dịch luôn `tong`/`dem`/`max`/`vt` sang tiếng Việt. Nhưng
 * `pseudocode.ts` in ra ĐÚNG những token ấy (`max ← a[1]`, `tong ← tong + a[i]`),
 * nên dịch chúng ở thuyết minh là CẮT cây cầu mã giả ↔ lời giải thích — một hồi
 * quy sư phạm đội lốt bản sửa.
 *
 * Ranh giới đúng, và đó là thứ bài này khoá:
 *   ĐƯỢC MÃ GIẢ NEO   → token hợp lệ, giữ nguyên
 *   DO ĐẶC TẢ CẤP     → không neo vào đâu ⇒ phải nói bằng khái niệm
 */

describe("ranh giới định danh — mã giả neo thì giữ, đặc tả cấp thì không", () => {
  it("bảng nhãn CỐ Ý RỖNG: không biến engine nào bị dịch", () => {
    /* Rỗng ở đây là kết quả MONG MUỐN, nhưng một danh sách rỗng cũng làm mọi
       vòng lặp chạy 0 lần — nên khẳng định riêng rằng nó rỗng có chủ đích. */
    expect(KNOWN_ENGINE_VARS).toEqual([]);
  });

  it("tên do ĐẶC TẢ cấp ⇒ không in định danh ra màn hình", () => {
    expect(varLabel("nguong")).toBeNull();
    const p = varPhrase("nguong", "giá trị so sánh");
    expect(p, "định danh của đặc tả vẫn lọt ra màn hình").not.toContain("nguong");
    expect(p).toBe("giá trị so sánh");
    expect(varPhrase("bien_la")).toBe("giá trị theo dõi");
  });
});
