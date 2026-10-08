/**
 * W12 — BẢNG MÀU VAI TRÒ: mỗi màu MỘT nghĩa, và CSS mang đúng bản của TS.
 *
 * Review người (NEEDS_CHANGES): cam đậm mang hai nghĩa — dữ kiện số trong
 * chuỗi nhân quả và vật đang chọn trên khung. Bảng lời giải (CSS) và khung 3D
 * (three.js) đọc cùng một bảng; test này khoá hai bản sao không trôi nhau.
 */
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import * as THREE from "three";
import { BIEN_CSS_VAI_TRO, MAU_VAI_TRO, hexCss } from "./scene3d-roles";

const hsl = (hex: number) => {
  const x = { h: 0, s: 0, l: 0 };
  new THREE.Color(hex).getHSL(x, THREE.SRGBColorSpace);
  return { h: x.h * 360, s: x.s, l: x.l };
};

describe("mỗi màu một nghĩa", () => {
  it("vật được chọn là XANH, dữ kiện số là CAM ĐẬM — hai màu khác nhau", () => {
    expect(MAU_VAI_TRO.dich).not.toBe(MAU_VAI_TRO.du_kien_so);
    expect(hsl(MAU_VAI_TRO.dich).h).toBeGreaterThan(200);
    expect(hsl(MAU_VAI_TRO.dich).h).toBeLessThan(235);
    expect(hsl(MAU_VAI_TRO.du_kien_so).h).toBeLessThan(35);
  });

  it("trung gian là cam NHẠT — sáng hơn dữ kiện số, cùng họ cam", () => {
    const tg = hsl(MAU_VAI_TRO.trung_gian);
    expect(tg.h).toBeGreaterThan(15);
    expect(tg.h).toBeLessThan(45);
    expect(tg.l).toBeGreaterThan(hsl(MAU_VAI_TRO.du_kien_so).l + 0.1);
  });

  it("ngữ cảnh cấu trúc là trung tính; vật mới dựng dùng xanh 'đang xét'", () => {
    expect(hsl(MAU_VAI_TRO.boi_canh).s).toBeLessThan(0.25);
    expect(hsl(MAU_VAI_TRO.nen_boi_canh).s).toBeLessThan(0.25);
    expect(MAU_VAI_TRO.moi_dung).toBe(MAU_VAI_TRO.dich);
    // Điểm đề cho không còn xanh: xanh chỉ còn nghĩa "đang xét".
    expect(hsl(MAU_VAI_TRO.diem_de_cho).s).toBeLessThan(0.25);
  });

  it("CSS mang ĐÚNG giá trị của bảng TS (bảng lời giải = khung 3D)", () => {
    const css = readFileSync(new URL("../../../styles/tokens.css", import.meta.url), "utf8");
    for (const [vai, bien] of Object.entries(BIEN_CSS_VAI_TRO)) {
      const m = new RegExp(`${bien}\\s*:\\s*(#[0-9a-fA-F]{6})`).exec(css);
      expect(m, `thiếu ${bien} trong tokens.css`).not.toBeNull();
      expect(m![1].toLowerCase()).toBe(hexCss(MAU_VAI_TRO[vai as keyof typeof MAU_VAI_TRO]));
    }
  });
});
