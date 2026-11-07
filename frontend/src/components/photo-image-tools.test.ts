import { describe, expect, it } from "vitest";
import {
  PHOTO_MAX_PIXELS,
  PHOTO_SEND_MAX_SIDE,
  applyMatrix,
  coversWholeImage,
  cropToPixels,
  exceedsPixelLimit,
  exportFormats,
  exportScale,
  rotateLeft,
  rotateRight,
  rotatedSize,
  rotationMatrix,
  uploadFileName,
} from "./photo-image-tools";

/**
 * Khoanh vùng ảnh đề bài phía trình duyệt — toán học thuần (run `image-capture-crop-extraction`).
 * Phần vẽ Canvas thật được kiểm trên Chrome (`frontend/scripts/photo-problem-browser-check.mjs`).
 */

const ANH_LON = { width: 4000, height: 3000 };

/** % mà react-image-crop báo khi người học kéo một khung `px` (CSS pixel) trên ảnh hiển thị `hien` rộng/cao. */
const phanTram = (px: { x: number; y: number; width: number; height: number }, hien: { width: number; height: number }) => ({
  x: (px.x / hien.width) * 100,
  y: (px.y / hien.height) * 100,
  width: (px.width / hien.width) * 100,
  height: (px.height / hien.height) * 100,
});

describe("vùng chọn → pixel GỐC", () => {
  it("ảnh 4000×3000 hiển thị 800×600: khung 200×150 tại (100, 50) ⇒ 1000×750 tại (500, 250) pixel gốc", () => {
    const rect = cropToPixels(phanTram({ x: 100, y: 50, width: 200, height: 150 }, { width: 800, height: 600 }), ANH_LON);
    expect(rect).toEqual({ x: 500, y: 250, width: 1000, height: 750 });
  });

  it("CÙNG một vùng trên ảnh ⇒ CÙNG pixel gốc dù ảnh hiển thị to/nhỏ, DPR hay mức phóng nào", () => {
    const vung = { x: 0.125, y: 1 / 12, width: 0.25, height: 0.25 };          // theo tỉ lệ ảnh
    const ketQua = [[800, 600], [400, 300], [1309, 981.75], [333, 249.75]].map(([w, h]) =>
      cropToPixels(phanTram({ x: vung.x * w, y: vung.y * h, width: vung.width * w, height: vung.height * h },
        { width: w, height: h }), ANH_LON));
    for (const r of ketQua) expect(r).toEqual(ketQua[0]);
    expect(ketQua[0]).toEqual({ x: 500, y: 250, width: 1000, height: 750 });
  });

  it("khung tràn ra ngoài ảnh bị KẸP trong biên — không bao giờ cắt ngoài ảnh", () => {
    const r = cropToPixels({ x: 90, y: -5, width: 30, height: 120 }, ANH_LON)!;
    expect(r.x + r.width).toBeLessThanOrEqual(ANH_LON.width);
    expect(r.y).toBe(0);
    expect(r.y + r.height).toBeLessThanOrEqual(ANH_LON.height);
  });

  it("khung rỗng / nhỏ hơn 8 px / không có ⇒ null — không bao giờ xuất ảnh rỗng", () => {
    expect(cropToPixels(null, ANH_LON)).toBeNull();
    expect(cropToPixels({ x: 10, y: 10, width: 0, height: 20 }, ANH_LON)).toBeNull();
    expect(cropToPixels({ x: 10, y: 10, width: 0.1, height: 0.1 }, ANH_LON)).toBeNull();
  });

  it("khung = cả ảnh ⇒ coi như không cắt", () => {
    expect(coversWholeImage(cropToPixels({ x: 0, y: 0, width: 100, height: 100 }, ANH_LON), ANH_LON)).toBe(true);
    expect(coversWholeImage(cropToPixels({ x: 0, y: 0, width: 50, height: 100 }, ANH_LON), ANH_LON)).toBe(false);
  });
});

describe("xoay 90° theo chiều kim đồng hồ", () => {
  it("trái/phải đủ vòng; kích thước đổi chiều ở 90° và 270°", () => {
    expect([rotateRight(0), rotateRight(90), rotateRight(180), rotateRight(270)]).toEqual([90, 180, 270, 0]);
    expect([rotateLeft(0), rotateLeft(90), rotateLeft(180), rotateLeft(270)]).toEqual([270, 0, 90, 180]);
    expect(rotatedSize(ANH_LON, 90)).toEqual({ width: 3000, height: 4000 });
    expect(rotatedSize(ANH_LON, 180)).toEqual(ANH_LON);
  });

  it("ma trận đưa 4 góc ảnh nguồn đúng vào 4 góc ảnh đã xoay (không lệch, không lật)", () => {
    const { width: w, height: h } = ANH_LON;
    const goc = [[0, 0], [w, 0], [w, h], [0, h]] as const;
    const mong: Record<number, number[][]> = {
      0: [[0, 0], [w, 0], [w, h], [0, h]],
      90: [[h, 0], [h, w], [0, w], [0, 0]],          // góc trên-trái đi sang trên-phải
      180: [[w, h], [0, h], [0, 0], [w, 0]],
      270: [[0, w], [0, 0], [h, 0], [h, w]],          // góc trên-trái đi sang dưới-trái
    };
    for (const r of [0, 90, 180, 270] as const) {
      expect(goc.map(([x, y]) => applyMatrix(rotationMatrix(r, ANH_LON), x, y))).toEqual(mong[r]);
    }
  });

  it("vùng chọn trên ảnh ĐÃ XOAY ứng với đúng vùng của ảnh gốc (nghịch ảnh qua ma trận)", () => {
    // Ảnh 4000×3000 xoay 90° hiển thị 3000×4000; khoanh nửa trên của nó.
    const turned = rotatedSize(ANH_LON, 90);
    const rect = cropToPixels({ x: 0, y: 0, width: 100, height: 50 }, turned)!;
    expect(rect).toEqual({ x: 0, y: 0, width: 3000, height: 2000 });
    // Điểm (x, y) gốc đi tới (h − y, x): nửa trên của ảnh xoay là nửa TRÁI (x < 2000) của ảnh gốc.
    const [, yTrongVung] = applyMatrix(rotationMatrix(90, ANH_LON), 1999, 1500);
    const [, yNgoaiVung] = applyMatrix(rotationMatrix(90, ANH_LON), 2001, 1500);
    expect(yTrongVung).toBeLessThan(2000);
    expect(yNgoaiVung).toBeGreaterThan(2000);
  });
});

describe("xuất ảnh gửi đi — theo giới hạn của máy chủ", () => {
  it("không phóng to; cạnh dài > 3072 px được thu về đúng 3072 (máy chủ cũng thu như thế)", () => {
    expect(exportScale({ width: 1000, height: 750 })).toBe(1);
    const s = exportScale({ width: 6144, height: 2000 });
    expect(Math.round(6144 * s)).toBe(PHOTO_SEND_MAX_SIDE);
  });

  it("trần 40 triệu điểm ảnh như backend", () => {
    expect(exceedsPixelLimit({ width: 6000, height: 4000 })).toBe(false);
    expect(exceedsPixelLimit({ width: 9000, height: 9000 })).toBe(true);
    expect(PHOTO_MAX_PIXELS).toBe(40_000_000);
  });

  it("PNG giữ PNG (nét chữ, ký hiệu); ảnh chụp ra JPEG chất lượng cao, KHÔNG nén mạnh", () => {
    expect(exportFormats("image/png")[0]).toEqual({ mime: "image/png" });
    const jpeg = exportFormats("image/jpeg");
    expect(jpeg.every((f) => f.mime === "image/jpeg" && (f.quality ?? 0) >= 0.85)).toBe(true);
    expect(exportFormats("image/webp")[0].mime).toBe("image/jpeg");
  });

  it("tên tệp gửi đi đổi đuôi theo định dạng THẬT, không chỉ đổi phần mở rộng", () => {
    expect(uploadFileName("de.webp", "image/jpeg", true)).toBe("de-vung-chon.jpg");
    expect(uploadFileName("chup.png", "image/png", false)).toBe("chup-da-xoay.png");
  });
});
