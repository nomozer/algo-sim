/**
 * Khoá các quyết định TRÌNH BÀY ra đời từ ảnh chụp thật của tập trình diễn.
 *
 * Mỗi ca dưới đây tương ứng một lỗi ĐO ĐƯỢC trên ảnh, không phải một sở thích
 * thẩm mỹ. Ghi lỗi ấy vào tên ca để lần sau ai đó đảo lại thì biết mình đang
 * đảo cái gì.
 */
import { describe, expect, it } from "vitest";
import {
  kyHieuNgan,
  laVectoDangDiem,
  locNhanChongNhau,
  uuTienNhan,
  veTrenKhung,
} from "./scene3d-presentation";

describe("nhãn mặc định là KÝ HIỆU, không phải câu mô tả", () => {
  it("câu mô tả dài rút về ký hiệu lấy từ id", () => {
    // Đúng chuỗi đã chồng lên nhau giữa hình trong ảnh chụp.
    expect(kyHieuNgan({ id: "H", label: "Hình chiếu vuông góc H của I lên mặt phẳng (SBC)" }))
      .toBe("H");
    expect(kyHieuNgan({ id: "M", label: "Trung điểm M của AB" })).toBe("M");
  });

  it("nhãn vốn đã ngắn thì giữ nguyên", () => {
    expect(kyHieuNgan({ id: "A", label: "A" })).toBe("A");
    expect(kyHieuNgan({ id: "SAB", label: "SAB" })).toBe("SAB");
  });

  it("`_prime` thành dấu phẩy thật, không phải dấu nháy ASCII", () => {
    expect(kyHieuNgan({ id: "B_prime", label: "B_prime" })).toBe("B′");
  });

  it("không bao giờ trả về một câu — mọi ký hiệu đều ngắn", () => {
    const dai = "Giao điểm I của hai đường chéo AC và BD";
    for (const id of ["I", "vector_AA_prime", "vec_np", "khoang_cach_A_B_prime_I"]) {
      expect(kyHieuNgan({ id, label: dai }).length).toBeLessThanOrEqual(8);
    }
  });
});

describe("vectơ không được vẽ như một điểm của hình", () => {
  // Payload THẬT lấy từ bản ghi thực nghiệm: tầng sinh cảnh phát vectơ với
  // `type: point3`, và `xyz` là thành phần vectơ chứ không phải toạ độ điểm.
  const vecto = { type: "point3", producer: "vector_from_points" };
  const diem = { type: "point3", producer: "construct_point.midpoint" };
  const diemGoc = { type: "point3", producer: null };

  it("nhận diện vectơ qua producer", () => {
    expect(laVectoDangDiem(vecto)).toBe(true);
    expect(laVectoDangDiem(diem)).toBe(false);
    expect(laVectoDangDiem(diemGoc)).toBe(false);
  });

  it("vectơ bị loại khỏi khung mặc định, điểm thật thì không", () => {
    expect(veTrenKhung(vecto)).toBe(false);
    expect(veTrenKhung(diem)).toBe(true);
    expect(veTrenKhung(diemGoc)).toBe(true);
  });

  it("không loại nhầm một vật khác kiểu", () => {
    expect(veTrenKhung({ type: "line3", producer: "vector_from_points" })).toBe(true);
  });
});

describe("nhãn chồng nhau: giữ cái ưu tiên cao", () => {
  it("vật đang chọn luôn đọc được", () => {
    expect(uuTienNhan({ id: "H", origin: "derived" }, "H")).toBeGreaterThan(
      uuTienNhan({ id: "A", origin: "derived" }, "H"));
  });

  it("điểm dẫn xuất hơn điểm gốc", () => {
    expect(uuTienNhan({ id: "H", origin: "derived" }, null)).toBeGreaterThan(
      uuTienNhan({ id: "A", origin: "free" }, null));
  });

  it("hai nhãn trùng chỗ ⇒ chỉ giữ một, và giữ cái ưu tiên cao", () => {
    const giu = locNhanChongNhau([
      { id: "thap", x: 100, y: 100, uuTien: 1 },
      { id: "cao", x: 103, y: 101, uuTien: 3 },
    ]);
    expect(giu.has("cao")).toBe(true);
    expect(giu.has("thap")).toBe(false);
  });

  it("nhãn cách xa nhau thì giữ hết — không ẩn oan", () => {
    const giu = locNhanChongNhau([
      { id: "a", x: 40, y: 40, uuTien: 1 },
      { id: "b", x: 400, y: 300, uuTien: 1 },
      { id: "c", x: 40, y: 300, uuTien: 1 },
    ]);
    expect(giu.size).toBe(3);
  });

  it("tất định: cùng đầu vào cho cùng kết quả bất kể thứ tự truyền vào", () => {
    const a = [
      { id: "x", x: 10, y: 10, uuTien: 1 },
      { id: "y", x: 12, y: 11, uuTien: 1 },
    ];
    expect([...locNhanChongNhau(a)]).toEqual([...locNhanChongNhau([...a].reverse())]);
  });
});
