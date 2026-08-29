/**
 * ĐÍCH BẤM — A–K. **0 mạng, 0 LLM, 0 WebGL.**
 *
 * Lỗi được đo bằng lưới 625 điểm ảnh trong Chrome thật: mặt trúng 26 lần,
 * đường thẳng 10, đa giác 7 — **điểm 0, cạnh 0**. Cơ chế chọn không hỏng;
 * đích bấm quá nhỏ. Các ca dưới đây khoá phép tách *cỡ nhìn* khỏi *cỡ bấm*.
 */
import { describe, expect, it } from "vitest";
import {
  BAN_KINH_NHIN,
  DICH_CANH_PX,
  DICH_DIEM_PX,
  KHOANG_CAM_MAC_DINH,
  banKinhBamDiem,
  hangCuThe,
  nguongBam,
  nguongBamCanh,
} from "./pick-target";
import { chonCuThe } from "./scene3d-view";

const loai: Record<string, string> = {
  A: "point3", B: "point3",
  "chop::edge:A-B": "edge",
  "chop::face:1": "face",
  chop: "solid",
  SA: "line3",
};
const tra = (id: string) => loai[id];

// ══ A–B · CỠ BẤM > CỠ NHÌN ═══════════════════════════════════════════════
describe("A–B · đích bấm rộng hơn thứ nhìn thấy", () => {
  it("A · bán kính bấm của ĐIỂM lớn hơn bán kính nhìn", () => {
    const bam = banKinhBamDiem(KHOANG_CAM_MAC_DINH);
    expect(bam).toBeGreaterThan(BAN_KINH_NHIN);
    // …và lớn hơn một cách CÓ NGHĨA, không phải nhích một hạt.
    expect(bam).toBeGreaterThan(BAN_KINH_NHIN * 1.8);
  });

  it("B · ngưỡng bấm của CẠNH lớn hơn nét vẽ 1px", () => {
    const n = nguongBamCanh(KHOANG_CAM_MAC_DINH);
    expect(n).toBeGreaterThan(0);
    // Nét vẽ 1px ≈ 0.019 đơn vị thế giới ở góc nhìn mặc định.
    expect(n).toBeGreaterThan(0.019 * 4);
  });

  it("cỡ NHÌN không đổi — đây là điều kiện của cả bản sửa", () => {
    // Phóng to chấm cho dễ bấm thì một điểm hình học thành quả cầu. Hằng số
    // này đổi là bản sửa đã trả sai cái giá.
    expect(BAN_KINH_NHIN).toBe(0.09);
  });

  it("điểm dễ bấm hơn cạnh — đích nhỏ hơn thì cần vùng rộng hơn", () => {
    expect(DICH_DIEM_PX).toBeGreaterThan(DICH_CANH_PX);
  });
});

// ══ J–K · NGƯỠNG THEO CAMERA ════════════════════════════════════════════
describe("J–K · ngưỡng ổn định theo màn hình khi phóng to / thu nhỏ", () => {
  it("K · phóng to (camera lại gần) ⇒ ngưỡng THẾ GIỚI hẹp lại", () => {
    const gan = nguongBamCanh(KHOANG_CAM_MAC_DINH / 3);
    const xa = nguongBamCanh(KHOANG_CAM_MAC_DINH * 3);
    expect(gan).toBeLessThan(nguongBamCanh(KHOANG_CAM_MAC_DINH));
    expect(xa).toBeGreaterThan(nguongBamCanh(KHOANG_CAM_MAC_DINH));
    // …nhưng vùng bấm quy ra ĐIỂM ẢNH thì gần như không đổi: tỉ lệ thuận.
    expect(xa / gan).toBeCloseTo(9, 5);
  });

  it("K2 · mọi mức zoom hợp lý đều cho ngưỡng DƯƠNG, hữu hạn", () => {
    for (const d of [0.5, 1, 5, 11.18, 50, 500]) {
      for (const f of [nguongBamCanh(d), banKinhBamDiem(d)]) {
        expect(Number.isFinite(f)).toBe(true);
        expect(f).toBeGreaterThan(0);
      }
    }
  });

  it("J · đầu vào hỏng ⇒ ngưỡng MẶC ĐỊNH, không NaN/Infinity", () => {
    // Một `NaN` trong `params.Line.threshold` làm raycast im lặng không trúng
    // gì — và một cổng không bao giờ trúng đọc y hệt một cổng không có lỗi.
    for (const x of [NaN, Infinity, -Infinity, 0, -5]) {
      const n = nguongBamCanh(x);
      expect(Number.isFinite(n)).toBe(true);
      expect(n).toBeGreaterThan(0);
      expect(n).toBeCloseTo(nguongBamCanh(KHOANG_CAM_MAC_DINH), 10);
    }
    expect(Number.isFinite(nguongBam(NaN, NaN))).toBe(true);
  });
});

// ══ G–I · LUẬT CHỌN khi nhiều lớp chồng nhau ════════════════════════════
describe("G–I · hạng cụ thể: điểm → cạnh → mặt → khối", () => {
  it("G · điểm THẮNG mặt khi tia trúng cả hai", () => {
    expect(chonCuThe(["chop::face:1", "A", "chop"], tra)).toBe("A");
    expect(chonCuThe(["A", "chop::face:1"], tra)).toBe("A");
  });

  it("I · cạnh THẮNG mặt, và mặt thắng khối", () => {
    expect(chonCuThe(["chop::face:1", "chop::edge:A-B"], tra))
      .toBe("chop::edge:A-B");
    expect(chonCuThe(["chop", "chop::face:1"], tra)).toBe("chop::face:1");
  });

  it("điểm thắng cạnh — hạng nhỏ nhất luôn thắng", () => {
    expect(chonCuThe(["chop::edge:A-B", "A"], tra)).toBe("A");
  });

  it("H · KHÔNG có điểm trong danh sách ⇒ mặt giữ nguyên lựa chọn", () => {
    // Vật chỉ vào danh sách khi tia THẬT SỰ trúng vùng bấm của nó. Nên "ưu
    // tiên điểm" không thể cướp một mặt ở xa con trỏ: điểm ấy đơn giản là
    // không có mặt trong `ids`.
    expect(chonCuThe(["chop::face:1", "chop"], tra)).toBe("chop::face:1");
    expect(chonCuThe(["chop"], tra)).toBe("chop");
  });

  it("cùng hạng ⇒ giữ thứ tự KHOẢNG CÁCH (gần nhất thắng)", () => {
    expect(chonCuThe(["A", "B"], tra)).toBe("A");
    expect(chonCuThe(["B", "A"], tra)).toBe("B");
  });

  it("loại lạ ⇒ hạng giữa, không ném", () => {
    expect(hangCuThe(undefined)).toBe(4);
    expect(hangCuThe("khong-biet")).toBe(4);
    expect(chonCuThe(["la", "A"], tra)).toBe("A");
  });

  it("không có bảng loại ⇒ rơi về luật cũ, vẫn không trả KHỐI", () => {
    expect(chonCuThe(["chop", "chop::face:1"])).toBe("chop::face:1");
    expect(chonCuThe([])).toBeNull();
  });
});
