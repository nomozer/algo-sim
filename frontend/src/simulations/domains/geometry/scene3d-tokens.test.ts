/**
 * scene3d-tokens.test.ts — SÁU VAI PHẢI TÁCH ĐƯỢC.
 *
 * ─── NỀN ĐỎ ĐÃ ĐO ĐƯỢC TRÊN BẢNG CŨ ───────────────────────────────────────
 *
 * Bảng trước D2 có hai chỗ mắt không tách nổi:
 *   · thiết diện thấy `#d95a43` và thiết diện khuất — **cùng một màu**, Δ = 0;
 *   · cạnh khuất `#7d7975` và mặt phẳng `#77736f` — Δ = 10,4, dưới ngưỡng
 *     phân biệt trên nền sáng.
 * Mọi assert dưới đây ĐỎ trên bảng ấy.
 */
import { describe, expect, it } from "vitest";
import { BE_DAY_D2, DIEM_PX_D2, DO_MO_D2, MAU_D2, TI_LE_LAP_KHUNG_D2 } from "./scene3d-tokens";
import { BE_DAY_PX } from "./scene3d-wide-line";

const rgb = (hex: number): [number, number, number] =>
  [(hex >> 16) & 255, (hex >> 8) & 255, hex & 255];
const cachMau = (a: number, b: number): number => {
  const [r1, g1, b1] = rgb(a), [r2, g2, b2] = rgb(b);
  return Math.hypot(r1 - r2, g1 - g2, b1 - b2);
};

/** Sáu vai mà học sinh phải phân biệt được trên cùng một hình. */
const SAU_VAI = {
  "cạnh thấy": MAU_D2.mesh,
  "cạnh khuất": MAU_D2.khuat,
  "thiết diện thấy": MAU_D2.section,
  "thiết diện khuất": MAU_D2.sectionKhuat,
  "đường dựng": MAU_D2.line,
  "mặt phẳng": MAU_D2.surface,
} as const;

describe("bảng màu D2 — sáu vai tách được", () => {
  it("khoảng cách màu nhỏ nhất giữa hai vai bất kỳ ≥ 40", () => {
    const ten = Object.keys(SAU_VAI) as (keyof typeof SAU_VAI)[];
    let nhoNhat = Infinity;
    let cap = "";
    for (let i = 0; i < ten.length; i++) {
      for (let j = i + 1; j < ten.length; j++) {
        const d = cachMau(SAU_VAI[ten[i]], SAU_VAI[ten[j]]);
        if (d < nhoNhat) { nhoNhat = d; cap = `${ten[i]} ↔ ${ten[j]}`; }
      }
    }
    expect(nhoNhat, `cặp gần nhất: ${cap} (Δ=${nhoNhat.toFixed(1)})`).toBeGreaterThanOrEqual(40);
  });

  it("thiết diện thấy ≠ thiết diện khuất — Δ = 0 là con bọ của bảng cũ", () => {
    expect(cachMau(MAU_D2.section, MAU_D2.sectionKhuat)).toBeGreaterThan(40);
  });

  it("cạnh khuất ≠ mặt phẳng — Δ = 10,4 của bảng cũ là dưới ngưỡng đọc được", () => {
    expect(cachMau(MAU_D2.khuat, MAU_D2.surface)).toBeGreaterThan(40);
  });

  it("thiết diện khuất vẫn CÙNG SẮC với thiết diện thấy — cùng một vật", () => {
    const [r1, g1, b1] = rgb(MAU_D2.section);
    const [r2, g2, b2] = rgb(MAU_D2.sectionKhuat);
    expect(r1).toBeGreaterThan(g1);        // sắc cam: đỏ trội
    expect(r2).toBeGreaterThan(g2);
    expect(b1).toBeLessThan(r1);
    expect(b2).toBeLessThan(r2);
    /* Nhạt hơn, không phải một màu khác hẳn. */
    const sang = (h: number) => { const [r, g, b] = rgb(h);
      return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
    expect(sang(MAU_D2.sectionKhuat)).toBeGreaterThan(sang(MAU_D2.section));
  });

  it("chỉ `highlight` là màu xanh — không vai ngữ nghĩa nào chạm vào nó", () => {
    for (const [ten, hex] of Object.entries(SAU_VAI)) {
      expect(cachMau(hex, MAU_D2.highlight), `${ten} quá gần màu chọn`)
        .toBeGreaterThan(80);
    }
  });
});

describe("thang bậc bề dày D2", () => {
  it("thiết diện > cạnh thấy > cạnh khuất > đường dựng ≥ viền mặt phẳng", () => {
    expect(BE_DAY_D2.thietDienThay).toBeGreaterThan(BE_DAY_D2.canhThay);
    expect(BE_DAY_D2.canhThay).toBeGreaterThan(BE_DAY_D2.canhKhuat);
    expect(BE_DAY_D2.canhKhuat).toBeGreaterThan(BE_DAY_D2.duongDung);
    expect(BE_DAY_D2.duongDung).toBeGreaterThanOrEqual(BE_DAY_D2.vienMatPhang);
  });

  it("phần khuất luôn mảnh hơn phần thấy, ở cả hai vai có hai lượt", () => {
    expect(BE_DAY_D2.canhKhuat).toBeLessThan(BE_DAY_D2.canhThay);
    expect(BE_DAY_D2.thietDienKhuat).toBeLessThan(BE_DAY_D2.thietDienThay);
  });

  it("renderer đọc ĐÚNG bảng này, không giữ bản sao thứ hai", () => {
    expect(BE_DAY_PX).toBe(BE_DAY_D2);
  });

  it("mọi bề dày nằm trong khoảng vẽ được: 0,5 – 6 px CSS", () => {
    for (const [ten, v] of Object.entries(BE_DAY_D2)) {
      expect(v, ten).toBeGreaterThanOrEqual(0.5);
      expect(v, ten).toBeLessThanOrEqual(6);
    }
  });
});

describe("mảng tô và khớp khung", () => {
  it("thiết diện nổi hơn hẳn hai lớp nền — không còn ba lớp tô cộng dồn", () => {
    expect(DO_MO_D2.thietDien).toBeGreaterThan(DO_MO_D2.khoi * 4);
    expect(DO_MO_D2.thietDien).toBeGreaterThan(DO_MO_D2.matPhang * 4);
    /* Hai lớp nền cộng lại vẫn phải nhạt hơn thiết diện, vì chúng CHỒNG nhau
       đúng ở chỗ mặt phẳng cắt khối. */
    expect(DO_MO_D2.khoi + DO_MO_D2.matPhang).toBeLessThan(DO_MO_D2.thietDien);
  });

  it("bấm chọn thì đậm hẳn lên — nếu không, người học không biết đã bấm trúng", () => {
    expect(DO_MO_D2.daChon).toBeGreaterThan(DO_MO_D2.khoi * 3);
    expect(DO_MO_D2.thietDienDaChon).toBeGreaterThan(DO_MO_D2.thietDien * 2);
  });

  it("chấm điểm là cỡ MÀN HÌNH, trong khoảng bấm được", () => {
    expect(DIEM_PX_D2).toBeGreaterThanOrEqual(3);
    expect(DIEM_PX_D2).toBeLessThanOrEqual(8);
  });

  it("lấp khung 0,84 — cao hơn 0,66 cũ, thấp hơn 0,88 đã làm tràn khung", () => {
    expect(TI_LE_LAP_KHUNG_D2).toBeGreaterThan(0.66);
    expect(TI_LE_LAP_KHUNG_D2).toBeLessThan(0.88);
  });
});
