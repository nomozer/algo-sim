/**
 * scene3d-dpr.test.ts — CHÍNH SÁCH TỈ LỆ ĐIỂM ẢNH.
 *
 * ─── NỀN ĐỎ ĐÃ ĐO ĐƯỢC ────────────────────────────────────────────────────
 *
 * Trước 2026-09-12 `setPixelRatio` không bao giờ được gọi, nên ở DPR 2 khung
 * vẽ vẫn 1318×610 trong khi ảnh chụp là 2636×1220 — sản phẩm vẽ ở 1× rồi để
 * trình duyệt phóng to. Đo bề rộng đoạn chuyển 10→90% qua mép nét: 1,364 px
 * CSS khi phóng to, 0,734 px CSS khi vẽ thẳng ở 2×.
 *
 * Phần kiểm được **không cần WebGL** nằm ở đây. Phần còn lại — cỡ khung vẽ
 * thật, độ sắc, bề dày px CSS bất biến — thuộc cổng trình duyệt, vì chúng chỉ
 * tồn tại khi có GPU.
 */
import { describe, expect, it } from "vitest";
import { DPR_TRAN, tiLeDiemAnh } from "./scene3d-wide-line";

describe("tiLeDiemAnh — trần và sàn", () => {
  it("trần là 2, khai tường minh", () => {
    expect(DPR_TRAN).toBe(2);
  });

  it.each([
    ["màn thường", 1, 1],
    ["retina", 2, 2],
    ["giữa chừng", 1.5, 1.5],
    ["1,25 của Windows", 1.25, 1.25],
    ["3× bị chặn ở trần", 3, 2],
    ["4× bị chặn ở trần", 4, 2],
  ])("%s: %f → %f", (_ten, vao, ra) => {
    expect(tiLeDiemAnh(vao)).toBe(ra);
  });

  it.each([
    ["không có", undefined],
    ["null", null],
    ["số không", 0],
    ["âm", -2],
    ["NaN", Number.NaN],
    ["vô cực", Number.POSITIVE_INFINITY],
  ])("%s ⇒ rơi về 1, không bao giờ trả 0 hay NaN", (_ten, vao) => {
    const r = tiLeDiemAnh(vao as number | null | undefined);
    expect(Number.isFinite(r)).toBe(true);
    expect(r).toBeGreaterThanOrEqual(1);
    expect(r).toBeLessThanOrEqual(DPR_TRAN);
  });

  it("KHÔNG BAO GIỜ trả 0 — khung vẽ 0×0 là một khung trắng câm", () => {
    for (const v of [0, -1, Number.NaN, undefined, null, 0.0001]) {
      expect(tiLeDiemAnh(v as number)).toBeGreaterThanOrEqual(1);
    }
  });

  it("đơn điệu không giảm: DPR cao hơn không bao giờ cho tỉ lệ thấp hơn", () => {
    let truoc = tiLeDiemAnh(0.5);
    for (const v of [1, 1.25, 1.5, 1.75, 2, 2.5, 3, 4]) {
      const nay = tiLeDiemAnh(v);
      expect(nay).toBeGreaterThanOrEqual(truoc);
      truoc = nay;
    }
  });
});
