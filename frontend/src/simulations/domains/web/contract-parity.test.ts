import { describe, expect, it } from "vitest";
import descriptors from "../../capability-descriptors.json";
import {
  COLOR_CHOICES, CONTENT_MAX_LENGTH, DEFAULT_STYLE, NUMERIC_RANGE, TEXT_COLOR_CHOICES,
} from "./props";

/**
 * W4B-2Z §4 — SYNC-LOCK MIỀN GIÁ TRỊ WEB, HAI TẦNG PHẢI NÓI GIỐNG NHAU.
 *
 * Vì sao là MIRROR chứ không phải import thẳng: `capability-descriptors.json`
 * là artifact TEST/GENERATED — production FE KHÔNG import nó (quyết định M14
 * §C4 điểm 6), nên `props.ts` phải tự khai. Cái giá của mirror là TRÔI, và đây
 * là chỗ trả giá đó: so TỪNG GIÁ TRỊ với hợp đồng backend đã sinh.
 *
 * Vì sao mặc định cũng phải khớp (không chỉ miền): mẫu offline chỉ đi qua
 * validate FE, còn đề thật đi qua CẢ HAI. Hai bảng mặc định lệch nhau nghĩa là
 * cùng một config cho ra hai khối trông khác nhau tuỳ đường vào — đúng kiểu sai
 * lệch không ai thấy cho tới khi so ảnh chụp.
 *
 * Đây KHÔNG phải kiểm token thiết kế. Các mã màu ở đây là DỮ LIỆU BÀI HỌC
 * (DOMAIN_DATA_LITERAL): bảng màu học sinh chọn để tô khối trong trang mô
 * phỏng. Chúng phải khớp từng byte với validator backend, nên tuyệt đối KHÔNG
 * được token-hoá thành `var(--…)` của giao diện AlgoSim.
 */

const CONTRACT = (descriptors as {
  bounded_domains: Record<string, {
    background_colors: string[];
    text_colors: string[];
    numeric_bounds: Record<string, { min: number; max: number }>;
    defaults: Record<string, string | number>;
    content_max_length: number;
  }>;
}).bounded_domains["web.style_model"];

describe("W4B-2Z · hợp đồng thuộc tính web: FE ≡ BE", () => {
  it("hợp đồng có mặt trong descriptor đã sinh (quên chạy generator ⇒ ĐỎ)", () => {
    expect(CONTRACT, "capability-descriptors.json thiếu bounded_domains").toBeTruthy();
  });

  it("bảng màu NỀN khớp thứ tự và từng giá trị", () => {
    expect(COLOR_CHOICES.map((c) => c.value)).toEqual(CONTRACT.background_colors);
  });

  it("bảng màu CHỮ khớp thứ tự và từng giá trị", () => {
    expect(TEXT_COLOR_CHOICES.map((c) => c.value)).toEqual(CONTRACT.text_colors);
  });

  it("biên số của MỌI thuộc tính số khớp (dẫn xuất từ hợp đồng, không liệt kê tay)", () => {
    const feBounds = Object.fromEntries(
      Object.entries(NUMERIC_RANGE).map(([k, r]) => [k, { min: r.min, max: r.max }]),
    );
    expect(feBounds).toEqual(CONTRACT.numeric_bounds);
  });

  it("mặc định khớp từng thuộc tính", () => {
    expect({ ...DEFAULT_STYLE }).toEqual(CONTRACT.defaults);
  });

  it("giới hạn độ dài nội dung khớp", () => {
    expect(CONTENT_MAX_LENGTH).toBe(CONTRACT.content_max_length);
  });

  it("mọi màu học sinh chọn được đều nằm trong hợp đồng — không có màu lậu", () => {
    const allowed = new Set([...CONTRACT.background_colors, ...CONTRACT.text_colors]);
    for (const c of [...COLOR_CHOICES, ...TEXT_COLOR_CHOICES]) {
      expect(allowed.has(c.value), `${c.value} không có trong hợp đồng BE`).toBe(true);
    }
  });

  it("mỗi lựa chọn đều có NHÃN tiếng Việt — miền là dữ liệu, nhãn là bề mặt học sinh", () => {
    for (const c of [...COLOR_CHOICES, ...TEXT_COLOR_CHOICES]) {
      expect(c.label.trim().length, c.value).toBeGreaterThan(0);
      expect(c.label, "nhãn lộ mã màu cho học sinh").not.toContain("#");
    }
  });
});
