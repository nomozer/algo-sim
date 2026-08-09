import { describe, expect, it } from "vitest";
import { ALGORITHM_IDS } from "../../../core/types";
import { whatIfPolicyOf } from "./interaction-policy";

/**
 * M9-S1 — CHÍNH SÁCH TƯƠNG TÁC THEO CƠ CHẾ (chấm dứt "một swap cho cả tám bài").
 *
 * Luật quyết định (khoá bằng test):
 * - "free":      đổi chỗ CHÍNH LÀ cơ chế đang học (sắp xếp) → luôn bật.
 * - "framed":    đổi chỗ có hệ quả thật nhưng cần KHUNG câu hỏi (chi phí tìm kiếm).
 * - "challenge": đổi chỗ chỉ có nghĩa như THÍ NGHIỆM có chủ đích (phá bất biến /
 *                phá tiền điều kiện) → ẨN mặc định, mở qua nút thí nghiệm có khung.
 * - "hidden":    đổi chỗ hầu như không đổi kết quả và không nhắm cơ chế → không bày.
 *
 * Gating theo ĐỊNH DANH NGỮ NGHĨA (algorithm_id trong config) — không theo tiêu đề.
 */


/**
 * W4B-2V/C — KHÁI NIỆM PHẢI SỐNG, KHÔNG PHẢI Ô CHỨA NÓ.
 *
 * Các assert cũ khoá vào ĐÚNG MỘT trường (`framing` hoặc `hint`) và đúng một
 * từ. Khi wave này rút `framing` xuống một câu hỏi hành động và dời nghĩa
 * what-if sang `hint` — chuỗi render ngay cạnh công cụ kéo — chúng đỏ dù học
 * sinh vẫn đọc được đúng ý đó. Test khoá VỊ TRÍ thay vì Ý là test cản đúng loại
 * refactor mà nó lẽ ra phải bảo vệ.
 *
 * Nay khẳng định trên CẶP `framing ∪ hint`: đó là những gì học sinh thấy khi
 * công cụ đã mở. Vẫn chặt — bỏ hẳn khái niệm đi thì vẫn đỏ.
 */
function toolCopy(id: Parameters<typeof whatIfPolicyOf>[0]): string {
  const p = whatIfPolicyOf(id);
  return `${p.framing ?? ""} ${p.hint ?? ""}`;
}

describe("whatIfPolicyOf — gating theo cơ chế", () => {
  it("(15) bubble_sort: giữ swap tự do — đổi chỗ là chính cơ chế", () => {
    expect(whatIfPolicyOf("bubble_sort").mode).toBe("free");
  });

  it("insertion_sort: giữ — hệ quả tất định lên thứ tự chèn", () => {
    expect(whatIfPolicyOf("insertion_sort").mode).toBe("free");
  });

  it("linear_search: chỉ giữ dạng CÓ KHUNG quanh chi phí tìm kiếm", () => {
    const p = whatIfPolicyOf("linear_search");
    expect(p.mode).toBe("framed");
    // khung CHI PHÍ phải còn, và kéo phải được gọi đúng tên là THÍ NGHIỆM
    expect(toolCopy("linear_search")).toContain("chi phí");
    expect(toolCopy("linear_search")).toContain("thí nghiệm");
    expect(toolCopy("linear_search"), "kéo bị trình bày như bước của thuật toán")
      .toContain("không phải bước thuật toán");
  });

  it("(16) binary_search: KHÔNG có swap tự do; chỉ thí nghiệm phá tiền điều kiện có khung", () => {
    const p = whatIfPolicyOf("binary_search");
    expect(p.mode).toBe("challenge");
    // tiền đề bị phá vẫn phải được nói ra ở đâu đó trong bộ chữ của công cụ
    expect(toolCopy("binary_search")).toContain("thứ tự đã sắp");
    expect(toolCopy("binary_search")).toContain("thí nghiệm");
  });

  it("find_max/find_min: ẩn mặc định; chỉ mở như thí nghiệm phá bất biến vùng-đã-duyệt", () => {
    for (const id of ["find_max", "find_min"] as const) {
      const p = whatIfPolicyOf(id);
      expect(p.mode).toBe("challenge");
      expect(toolCopy(id)).toContain("đã duyệt");
    }
  });

  it("(17) sum_if/count_if: ẨN — đổi chỗ không nhắm cơ chế tích luỹ", () => {
    expect(whatIfPolicyOf("sum_if").mode).toBe("hidden");
    expect(whatIfPolicyOf("count_if").mode).toBe("hidden");
  });

  it("(§10) mọi chính sách đều tự khai lý-do-không-trang-trí (rationale)", () => {
    for (const id of ALGORITHM_IDS) {
      const p = whatIfPolicyOf(id);
      expect(p.rationale.length).toBeGreaterThan(20);
    }
  });
});
