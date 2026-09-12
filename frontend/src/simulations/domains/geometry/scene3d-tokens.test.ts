/**
 * scene3d-tokens.test.ts — TOKEN PHẢI KHỚP MOCKUP ĐÃ DUYỆT.
 *
 * ─── VÌ SAO BÀI TEST NÀY ĐỔI HẲN CÁCH HỎI ─────────────────────────────────
 *
 * Bản trước hỏi *"sáu vai có tách nhau bằng MÀU không"* và chốt ngưỡng Δ ≥ 40.
 * Câu hỏi ấy nghe hợp lý, và nó **xanh suốt** — nhưng nó xanh cho một bảng màu
 * mà **không ai duyệt**: để qua được ngưỡng ấy, bảng token đã bị viết lại toàn
 * bộ so với mockup (2,8/1,6/3,5 → 2,4/1,4/3,2; tô 0,07 → 0,035; chấm 8 → 4,4
 * px; thiết diện khuất từ *cam mờ* thành `#e79a84`). Test khoá một thiết kế
 * tự nghĩ ra, nên nó không thể nào bắt được việc thiết kế đã trôi.
 *
 * ⚠️ **Bài học, và là lý do file này tồn tại:** mockup là THẨM QUYỀN, token
 * chỉ là bản chép. Nên test phải khoá **đúng con số của mockup**, không khoá
 * một tính chất suy ra từ chúng. Mọi `toBe` dưới đây đối chiếu trực tiếp với
 * thuộc tính SVG trong bộ `p1`–`p7`; sai một dòng là ĐỎ ngay, kể cả khi bảng
 * mới "đẹp hơn".
 *
 * ─── NỀN ĐỎ ───────────────────────────────────────────────────────────────
 *
 * Mọi assert trong `describe("khoá theo mockup")` ĐỎ trên bảng token của vòng
 * trước — đó là toàn bộ ý nghĩa của chúng.
 */
import { describe, expect, it } from "vitest";
import {
  BE_DAY_D2, DIEM_PX_D2, DIEM_VANH_PX_D2, DO_MO_D2, MAU_D2, MAU_GIAY_D2,
  TI_LE_LAP_KHUNG_D2,
} from "./scene3d-tokens";
import { BE_DAY_PX } from "./scene3d-wide-line";

const rgb = (hex: number): [number, number, number] =>
  [(hex >> 16) & 255, (hex >> 8) & 255, hex & 255];
const cachMau = (a: number, b: number): number => {
  const [r1, g1, b1] = rgb(a), [r2, g2, b2] = rgb(b);
  return Math.hypot(r1 - r2, g1 - g2, b1 - b2);
};

/**
 * Giá trị đọc THẲNG từ SVG mockup đã duyệt. Cột phải là thuộc tính nguyên văn.
 *
 * Sửa bảng này = tuyên bố mockup đã đổi. Không sửa nó để test xanh.
 */
const MOCKUP = {
  nenGiay: 0xfaf9f7,        // <rect fill="#FAF9F7">
  canhThay: { mau: 0x1f1f1f, beDay: 2.8 },   // stroke="#1F1F1F" stroke-width="2.8"
  canhKhuat: { mau: 0x7d7975, beDay: 1.6 },  // stroke="#7D7975" stroke-width="1.6"
  thietDienThay: { mau: 0xd95a43, beDay: 3.5 },
  thietDienKhuat: { mau: 0xd95a43, beDay: 2.2, doMo: 0.55 },
  duongDung: { mau: 0x99948f, beDay: 1.2 },
  matPhang: { mau: 0x77736f, beDay: 1.2, doMo: 0.85, to: 0.07 },
  toKhoi: 0.07,             // <polygon fill="#1F1F1F" fill-opacity="0.07">
  toThietDien: 0.14,        // <polygon fill="#D95A43" fill-opacity="0.14">
  diemBanKinh: 4,           // <circle r="4">
  diemVanh: 1.4,            // stroke="#FAF9F7" stroke-width="1.4"
  diemKhuatDoMo: 0.45,      // <circle fill-opacity="0.45">
} as const;

describe("khoá theo mockup — mọi con số phải chép đúng, không 'cải tiến'", () => {
  it("màu sáu vai khớp từng byte với SVG", () => {
    expect(MAU_D2.mesh).toBe(MOCKUP.canhThay.mau);
    expect(MAU_D2.khuat).toBe(MOCKUP.canhKhuat.mau);
    expect(MAU_D2.section).toBe(MOCKUP.thietDienThay.mau);
    expect(MAU_D2.sectionKhuat).toBe(MOCKUP.thietDienKhuat.mau);
    expect(MAU_D2.line).toBe(MOCKUP.duongDung.mau);
    expect(MAU_D2.surface).toBe(MOCKUP.matPhang.mau);
    expect(MAU_GIAY_D2).toBe(MOCKUP.nenGiay);
  });

  it("bề dày sáu vai khớp từng số với SVG", () => {
    expect(BE_DAY_D2.canhThay).toBe(MOCKUP.canhThay.beDay);
    expect(BE_DAY_D2.canhKhuat).toBe(MOCKUP.canhKhuat.beDay);
    expect(BE_DAY_D2.thietDienThay).toBe(MOCKUP.thietDienThay.beDay);
    expect(BE_DAY_D2.thietDienKhuat).toBe(MOCKUP.thietDienKhuat.beDay);
    expect(BE_DAY_D2.duongDung).toBe(MOCKUP.duongDung.beDay);
    expect(BE_DAY_D2.vienMatPhang).toBe(MOCKUP.matPhang.beDay);
  });

  it("mảng tô và độ mờ khớp với SVG", () => {
    expect(DO_MO_D2.khoi).toBe(MOCKUP.toKhoi);
    expect(DO_MO_D2.matPhang).toBe(MOCKUP.matPhang.to);
    expect(DO_MO_D2.thietDien).toBe(MOCKUP.toThietDien);
    expect(DO_MO_D2.vienMatPhang).toBe(MOCKUP.matPhang.doMo);
    expect(DO_MO_D2.thietDienKhuat).toBe(MOCKUP.thietDienKhuat.doMo);
    expect(DO_MO_D2.diemKhuat).toBe(MOCKUP.diemKhuatDoMo);
  });

  it("chấm điểm: ĐƯỜNG KÍNH 8 px và vành giấy 1,4 px", () => {
    /* `<circle r="4">` là BÁN KÍNH. Vòng trước quy nhầm sang đường kính 4,4 px
       — chấm bé gần một nửa mockup, và không ai thấy vì test chỉ hỏi "trong
       khoảng 3–8 px". */
    expect(DIEM_PX_D2).toBe(MOCKUP.diemBanKinh * 2);
    expect(DIEM_VANH_PX_D2).toBe(MOCKUP.diemVanh);
  });
});

describe("cách sáu vai tách nhau — KHÔNG phải chỉ bằng màu", () => {
  /**
   * Mockup tách vai bằng BỐN chiều cùng lúc: màu · bề dày · nét đứt · độ mờ.
   * Ép tất cả phải tách bằng riêng màu là đọc sai bản thiết kế, và chính chỗ
   * đọc sai ấy đã đẻ ra bảng token tự chế của vòng trước.
   */
  const VAI = {
    "cạnh thấy": { mau: MAU_D2.mesh, beDay: BE_DAY_D2.canhThay, dut: false, doMo: 1 },
    "cạnh khuất": { mau: MAU_D2.khuat, beDay: BE_DAY_D2.canhKhuat, dut: true, doMo: 1 },
    "thiết diện thấy": {
      mau: MAU_D2.section, beDay: BE_DAY_D2.thietDienThay, dut: false, doMo: 1,
    },
    "thiết diện khuất": {
      mau: MAU_D2.sectionKhuat, beDay: BE_DAY_D2.thietDienKhuat, dut: true,
      doMo: DO_MO_D2.thietDienKhuat,
    },
    "đường dựng": { mau: MAU_D2.line, beDay: BE_DAY_D2.duongDung, dut: true, doMo: 1 },
    "mặt phẳng": {
      mau: MAU_D2.surface, beDay: BE_DAY_D2.vienMatPhang, dut: false,
      doMo: DO_MO_D2.vienMatPhang,
    },
  } as const;

  it("mỗi cặp vai khác nhau ở ÍT NHẤT một chiều đọc được", () => {
    const ten = Object.keys(VAI) as (keyof typeof VAI)[];
    for (let i = 0; i < ten.length; i++) {
      for (let j = i + 1; j < ten.length; j++) {
        const a = VAI[ten[i]], b = VAI[ten[j]];
        const khac = [
          cachMau(a.mau, b.mau) >= 40 && "màu",
          Math.abs(a.beDay - b.beDay) >= 0.4 && "bề dày",
          a.dut !== b.dut && "nét đứt",
          Math.abs(a.doMo - b.doMo) >= 0.15 && "độ mờ",
        ].filter(Boolean);
        expect(khac.length, `${ten[i]} ↔ ${ten[j]} không tách được ở chiều nào`)
          .toBeGreaterThan(0);
      }
    }
  });

  it("thiết diện thấy và khuất CÙNG MỘT MÀU — mockup tách bằng độ mờ + nét đứt", () => {
    /* ⚠️ Đây là chỗ vòng trước làm ngược: nó coi Δ = 0 là con bọ rồi đặt ra một
       màu hồng `#e79a84` cho phần khuất. Mockup cố ý giữ chung màu — mắt phải
       đọc ra *"vẫn là đường thiết diện, đang nằm sau khối"*, chứ không phải
       *"một vật khác"*. */
    expect(MAU_D2.sectionKhuat).toBe(MAU_D2.section);
    expect(DO_MO_D2.thietDienKhuat).toBeLessThan(1);
    expect(BE_DAY_D2.thietDienKhuat).toBeLessThan(BE_DAY_D2.thietDienThay);
  });

  it("cạnh khuất và mặt phẳng gần nhau về màu ⇒ BẮT BUỘC tách ở chiều khác", () => {
    /* Δ ≈ 10,4 — thực sự gần. Mockup chấp nhận, vì cạnh khuất là NÉT ĐỨT không
       mảng tô, còn mặt phẳng là MẢNG TÔ có viền liền. Ghi con số ra đây để lần
       sau ai định đổi thì thấy ngay ràng buộc đi kèm. */
    expect(cachMau(MAU_D2.khuat, MAU_D2.surface)).toBeLessThan(20);
    expect(BE_DAY_D2.canhKhuat).not.toBe(BE_DAY_D2.vienMatPhang);
    expect(DO_MO_D2.matPhang).toBeGreaterThan(0);   // mặt phẳng CÓ mảng tô
  });

  it("chỉ `highlight` là màu xanh — không vai ngữ nghĩa nào chạm vào nó", () => {
    for (const [ten, v] of Object.entries(VAI)) {
      expect(cachMau(v.mau, MAU_D2.highlight), `${ten} quá gần màu chọn`)
        .toBeGreaterThan(80);
    }
  });
});

describe("thang bậc bề dày", () => {
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
  it("thiết diện tô ĐẬM GẤP ĐÔI khối và mặt phẳng", () => {
    expect(DO_MO_D2.thietDien).toBe(DO_MO_D2.khoi * 2);
    expect(DO_MO_D2.thietDien).toBe(DO_MO_D2.matPhang * 2);
  });

  it("chỗ mặt phẳng cắt khối, hai lớp nền cộng lại BẰNG thiết diện — và đó là lý do thiết diện phải có nét riêng", () => {
    /* ⚠️ Vòng trước gọi chỗ này là con bọ (*"ba lớp tô cộng dồn đọc ra như một
       vết bẩn"*) rồi hạ hai lớp nền xuống 0,035/0,022. Cách chữa của mockup
       KHÁC: giữ nguyên 0,07 và để **nét 3,5 px màu cam** làm việc tách — mảng
       tô chỉ gợi ý khối đặc, nó chưa bao giờ là thứ phân định thiết diện.
       Hạ mảng tô là mất luôn cảm giác KHỐI, đổi một vấn đề lấy một vấn đề. */
    expect(DO_MO_D2.khoi + DO_MO_D2.matPhang).toBeCloseTo(DO_MO_D2.thietDien, 5);
    expect(BE_DAY_D2.thietDienThay).toBeGreaterThan(BE_DAY_D2.canhThay);
  });

  it("bấm chọn thì đậm hẳn lên — nếu không, người học không biết đã bấm trúng", () => {
    expect(DO_MO_D2.daChon).toBeGreaterThan(DO_MO_D2.khoi * 3);
    expect(DO_MO_D2.thietDienDaChon).toBeGreaterThan(DO_MO_D2.thietDien * 2);
  });

  it("lấp khung 0,84 — cao hơn 0,66 cũ, thấp hơn 0,88 đã làm tràn khung", () => {
    expect(TI_LE_LAP_KHUNG_D2).toBeGreaterThan(0.66);
    expect(TI_LE_LAP_KHUNG_D2).toBeLessThan(0.88);
  });
});
