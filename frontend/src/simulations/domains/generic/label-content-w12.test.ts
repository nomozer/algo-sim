import { describe, expect, it } from "vitest";
import { displayLabel } from "./model";
import type { SimulationSpec } from "./model";

/**
 * LỖ HỔNG HỢP ĐỒNG DSL — `label` không khai trường nào mang nội dung.
 *
 * ─── LỖI CÓ THẬT, ĐO TRÊN MỘT ĐỀ THẬT ─────────────────────────────────────
 *
 * Đề "mô phỏng cho tôi hệ màu rgb" sinh ra đặc tả HOÀN TOÀN ĐÚNG:
 *
 *   {"id":"label_red_channel","type":"label","text":"Kênh Đỏ (R)"}
 *   {"id":"label_green_channel","type":"label","text":"Kênh Xanh lá (G)"}
 *   {"id":"label_blue_channel","type":"label","text":"Kênh Xanh dương (B)"}
 *   {"id":"label_result_color","type":"label","text":"Màu sắc kết quả (…)"}
 *
 * Màn hình hiện: "Nhãn 1 · Nhãn 2 · Nhãn 3 · Nhãn 4".
 *
 * Nguyên nhân KHÔNG phải LLM sinh ẩu, cũng KHÔNG phải thiếu năng lực:
 * `manifest.py` khai `label` thuộc họ `textual` cùng `heading`/`paragraph`/
 * `text`, và ba loại kia được nói rõ "text" là nội dung — riêng `label` không
 * nói gì. LLM làm theo ba anh em cùng họ; `displayLabel` chỉ đọc `label`.
 * Hai giả định đều hợp lý, hợp đồng thiếu một câu, và chữ của học sinh bị xoá.
 *
 * ─── VÌ SAO TEST NÀY CHẶN ĐƯỢC HỒI QUY ────────────────────────────────────
 *
 * Lưới an toàn chống lộ định danh kỹ thuật (anti-pattern #10) vẫn phải giữ:
 * `label = id` hay `label` dạng snake_case vẫn phải bị thay. Nên test có CẢ
 * hai chiều — nhận nội dung thật, và vẫn chặn định danh — nếu không, bản vá
 * này sẽ mở lại đúng cái lỗ mà lưới an toàn sinh ra để bịt.
 */

const spec = (objects: unknown[]): SimulationSpec =>
  ({ dsl_version: "1.0", title: "t", objects, rules: [], interactions: [], processes: [] } as unknown as SimulationSpec);

describe("W12 — nội dung nhãn nằm ở `text` cũng phải hiện ra", () => {
  it("ca RGB thật: bốn nhãn đọc từ `text`, KHÔNG rơi về 'Nhãn 1..4'", () => {
    const s = spec([
      { id: "label_red_channel", type: "label", text: "Kênh Đỏ (R)" },
      { id: "label_green_channel", type: "label", text: "Kênh Xanh lá (G)" },
      { id: "label_blue_channel", type: "label", text: "Kênh Xanh dương (B)" },
      { id: "label_result_color", type: "label", text: "Màu sắc kết quả (Giá trị thập phân)" },
    ]);
    expect(displayLabel(s, "label_red_channel")).toBe("Kênh Đỏ (R)");
    expect(displayLabel(s, "label_green_channel")).toBe("Kênh Xanh lá (G)");
    expect(displayLabel(s, "label_blue_channel")).toBe("Kênh Xanh dương (B)");
    expect(displayLabel(s, "label_result_color")).toBe("Màu sắc kết quả (Giá trị thập phân)");
    for (const id of ["label_red_channel", "label_green_channel", "label_blue_channel"]) {
      expect(displayLabel(s, id), "vẫn đang rơi về nhãn dự phòng").not.toMatch(/^Nhãn \d+$/);
    }
  });

  it("`label` thắng `text` khi có cả hai — không đổi ngữ nghĩa đang chạy", () => {
    const s = spec([{ id: "n1", type: "label", label: "Tên hiển thị", text: "phụ" }]);
    expect(displayLabel(s, "n1")).toBe("Tên hiển thị");
  });

  it("LƯỚI AN TOÀN CÒN NGUYÊN — định danh kỹ thuật vẫn không lọt lên UI", () => {
    /* Nếu bản vá làm hỏng vế này thì nó đã đổi một bug lấy một bug tệ hơn:
       học sinh đọc `label_red_channel` thay vì "Nhãn 1". */
    const s = spec([
      { id: "red_switch", type: "switch", label: "red_switch" },
      { id: "green_switch", type: "switch", text: "green_switch" },
      { id: "blue_switch", type: "switch" },
    ]);
    for (const id of ["red_switch", "green_switch", "blue_switch"]) {
      const out = displayLabel(s, id);
      expect(out, `định danh kỹ thuật lọt lên UI ở ${id}`).not.toContain("_");
      expect(out).toMatch(/^Công tắc \d+$/);
    }
  });

  it("nhãn rỗng/khoảng trắng vẫn rơi về dự phòng, không ra chuỗi trống", () => {
    const s = spec([
      { id: "a", type: "label", text: "" },
      { id: "b", type: "label", text: "Có nghĩa" },
    ]);
    expect(displayLabel(s, "a")).toMatch(/^Nhãn \d+$/);
    expect(displayLabel(s, "b")).toBe("Có nghĩa");
  });
});
