import { describe, expect, it } from "vitest";

import { arrayChartLayout } from "./ArrayView";

/**
 * W4B-2A §8 — HỢP ĐỒNG BỐ CỤC THÍCH ỨNG của biểu đồ dãy.
 *
 * Bối cảnh đo được (baseline W4B-2A, 1920×1080): đóng panel Quan sát cấp thêm
 * 316px bề rộng sân khấu, và hình vẽ lớn thêm **0px** — trên cả 19 target đo
 * được. `ArrayView` là chủ sở hữu sizing của 9 target họ algorithm nên nó được
 * sửa trước.
 *
 * Hàm dẫn xuất là HÀM THUẦN nên hợp đồng kiểm được ở đây, không cần trình duyệt.
 */

const N7 = 7; // đúng mẫu bubble_sort của ảnh người dùng gửi

describe("arrayChartLayout — phản ứng theo bề rộng khả dụng", () => {
  it("A. bề rộng lớn hơn ⇒ bố cục rộng hơn (khi chưa chạm trần)", () => {
    const narrow = arrayChartLayout(N7, 620);
    const wide = arrayChartLayout(N7, 900);
    expect(narrow.capped).toBe(false);
    expect(wide.width).toBeGreaterThan(narrow.width);
    expect(wide.colW).toBeGreaterThan(narrow.colW);
  });

  it("B. chạm TRẦN NGỮ NGHĨA thì dừng — thêm bề rộng không làm hình phình mãi", () => {
    const atCap = arrayChartLayout(N7, 1306);
    const wider = arrayChartLayout(N7, 1622); // đóng panel Quan sát
    expect(atCap.capped).toBe(true);
    expect(wider.width).toBe(atCap.width);
    // và trần phải THẬT SỰ nhỏ hơn sân khấu: phần dư là lề căn giữa có chủ đích
    expect(atCap.width).toBeLessThan(1306);
  });

  it("bubble_sort 7 cột: rộng hơn hẳn bố cục hằng số cũ (504px)", () => {
    const OLD_FIXED = N7 * 56 + (N7 + 1) * 14; // 504
    expect(OLD_FIXED).toBe(504);
    expect(arrayChartLayout(N7, 1306).width).toBeGreaterThan(OLD_FIXED);
  });

  it("C. số phần tử khác nhau: cột luôn nằm trong biên ngữ nghĩa", () => {
    for (const n of [2, 5, 7, 10, 16, 24]) {
      for (const available of [420, 700, 1000, 1306, 1622]) {
        const l = arrayChartLayout(n, available);
        expect(l.colW).toBeGreaterThanOrEqual(28);
        expect(l.colW).toBeLessThanOrEqual(96);
        expect(l.gap).toBeGreaterThanOrEqual(8);
        expect(l.gap).toBeLessThanOrEqual(28);
        // bố cục phải khớp chính công thức mà renderer dùng để đặt toạ độ
        expect(l.width).toBe(n * l.colW + (n + 1) * l.gap);
      }
    }
  });

  it("dãy dài trong khung hẹp: co lại chứ không tràn vô hạn", () => {
    const many = arrayChartLayout(24, 700);
    expect(many.colW).toBe(28); // chạm sàn
    expect(many.capped).toBe(false);
  });

  it("chưa đo được khung (SSR/jsdom) ⇒ giữ NGUYÊN bố cục hằng số cũ", () => {
    // Điều kiện này giữ mọi test SSR sẵn có không đổi kết quả, và tránh một
    // bước nhảy thị giác ở lần render đầu trước khi ResizeObserver báo về.
    for (const bad of [0, -1, Number.NaN]) {
      const l = arrayChartLayout(N7, bad);
      expect(l.colW).toBe(56);
      expect(l.gap).toBe(14);
      expect(l.width).toBe(504);
    }
  });

  it("tỉ lệ khe/cột giữ đúng tinh thần bản gốc (≈ 0,25)", () => {
    for (const available of [700, 900, 1100, 1306]) {
      const l = arrayChartLayout(N7, available);
      expect(l.gap / l.colW).toBeGreaterThan(0.18);
      expect(l.gap / l.colW).toBeLessThan(0.34);
    }
  });

  it("KHÔNG bao giờ PHÓNG: bố cục không vượt bề rộng khả dụng khi còn co được", () => {
    // Bất biến thật là `scale ≤ 1` (dag-module.tsx §"Cách đúng"): SVG khai
    // `maxWidth = width = viewBox` nên trình duyệt chỉ có thể CO lại, không bao
    // giờ phóng. Khi số phần tử nhiều tới mức cột chạm SÀN, bố cục có thể rộng
    // hơn khung — lúc đó SVG co xuống, và đó là đường đúng đã được ghi.
    for (const n of [2, 5, 7, 12]) {
      for (const available of [700, 1306, 1622]) {
        const l = arrayChartLayout(n, available);
        if (l.colW > 28) expect(l.width).toBeLessThanOrEqual(available);
      }
    }
  });

  it("dãy dài trong khung rất hẹp: co xuống, và vẫn HẸP HƠN bố cục hằng số cũ", () => {
    const n = 12;
    const l = arrayChartLayout(n, 420);
    const OLD_FIXED = n * 56 + (n + 1) * 14; // 854 — bản cũ còn tràn nặng hơn
    expect(l.colW).toBe(28); // chạm sàn
    expect(l.width).toBeLessThan(OLD_FIXED);
  });
});
