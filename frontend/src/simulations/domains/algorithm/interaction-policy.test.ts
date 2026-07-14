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
    expect(p.hint).toContain("so sánh"); // khung: số lần so sánh thay đổi thế nào
  });

  it("(16) binary_search: KHÔNG có swap tự do; chỉ thí nghiệm phá tiền điều kiện có khung", () => {
    const p = whatIfPolicyOf("binary_search");
    expect(p.mode).toBe("challenge");
    expect(p.framing).toContain("sắp thứ tự");
    expect(p.framing).toContain("bỏ sót");
  });

  it("find_max/find_min: ẩn mặc định; chỉ mở như thí nghiệm phá bất biến vùng-đã-duyệt", () => {
    for (const id of ["find_max", "find_min"] as const) {
      const p = whatIfPolicyOf(id);
      expect(p.mode).toBe("challenge");
      expect(p.framing).toContain("đã duyệt");
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
