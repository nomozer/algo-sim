/**
 * Khoá các quyết định TRÌNH BÀY ra đời từ ảnh chụp thật của tập trình diễn.
 *
 * Mỗi ca dưới đây tương ứng một lỗi ĐO ĐƯỢC trên ảnh, không phải một sở thích
 * thẩm mỹ. Ghi lỗi ấy vào tên ca để lần sau ai đó đảo lại thì biết mình đang
 * đảo cái gì.
 */
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  kyHieu,
  locNhanChongNhau,
  uuTienNhan,
  veTrenKhung,
} from "./scene3d-presentation";

describe("ký hiệu do BACKEND phát, phía này không tự chế", () => {
  it("in đúng thứ backend nói", () => {
    expect(kyHieu({ notation: "A′" })).toBe("A′");
    expect(kyHieu({ notation: "d(H, (SBC))" })).toBe("d(H, (SBC))");
  });

  it.each(["I1", "I12", "AI2", "(HUW)", "(α)"])("giữ nguyên ký hiệu backend %s", (notation) => {
    expect(kyHieu({ notation })).toBe(notation);
  });

  it("không có ký hiệu ⇒ KHÔNG in gì, không đoán tạm", () => {
    // `null` là câu trả lời hợp lệ của backend cho một vật không có ký hiệu
    // toán (`pyramid_S_ABCD`, `section_MNP`). Bịa một chữ cạnh một vật là một
    // mệnh đề sai về hình.
    expect(kyHieu({ notation: null })).toBeNull();
    expect(kyHieu({ notation: undefined })).toBeNull();
    expect(kyHieu({ notation: "   " })).toBeNull();
  });
});

describe("(G1/G2) KHÔNG suy ngữ nghĩa từ định danh hay producer", () => {
  /* Soi MÃ, không soi chú thích. Chú thích của file cố ý còn nhắc `_prime`,
   * `vector_from_points` và `producer` để kể lại vì sao cách cũ sai — xoá lời
   * kể ấy là xoá lý do, nên guard phải bỏ qua nó thay vì ép nó im. */
  const ma = readFileSync(
    new URL("./scene3d-presentation.ts", import.meta.url), "utf8")
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/\/\/.*$/gm, "");

  /* Hai hàm này TỪNG tồn tại ở đây và là hai chỗ duy nhất trong tầng trình bày
   * suy lại một mệnh đề ngữ nghĩa:
   *   `kyHieuNgan`     — đọc ngược `id` để rút ký hiệu;
   *   `laVectoDangDiem` — đọc `producer` để biết một `point3` là vectơ.
   * Cả hai chỉ tồn tại vì backend đang vứt đi siêu dữ liệu nó đã cầm. Sửa gốc
   * thì chúng biến mất — ca này khoá cho chúng không quay lại dưới tên khác. */
  it("không hàm nào bóc tiền tố/hậu tố của `id`", () => {
    for (const dau of ["_prime", "vector_", "point_", "plane_", "solid_"]) {
      expect(ma).not.toContain(`"${dau}`);
    }
    expect(ma).not.toMatch(/\bo\.id\b\s*\.\s*(replace|slice|split|match)/);
  });

  it("không đọc `producer` để quyết bất cứ điều gì", () => {
    expect(ma).not.toContain("producer");
  });
});

describe("vật KHÔNG có hình trên khung — do backend quyết", () => {
  it("`non_visual` (vectơ) và `readout` (số đo) không lên khung", () => {
    expect(veTrenKhung({ render: "non_visual" })).toBe(false);
    expect(veTrenKhung({ render: "readout" })).toBe(false);
  });

  it("mọi loại vẽ thật thì lên khung", () => {
    for (const r of ["point_marker", "line", "surface", "mesh", "polygon"] as const) {
      expect(veTrenKhung({ render: r })).toBe(true);
    }
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
      { id: "thap", x: 100, y: 100, uuTien: 1, w: 20, h: 17 },
      { id: "cao", x: 103, y: 101, uuTien: 3, w: 20, h: 17 },
    ]);
    expect(giu.has("cao")).toBe(true);
    expect(giu.has("thap")).toBe(false);
  });

  it("nhãn cách xa nhau thì giữ hết — không ẩn oan", () => {
    const giu = locNhanChongNhau([
      { id: "a", x: 40, y: 40, uuTien: 1, w: 20, h: 17 },
      { id: "b", x: 400, y: 300, uuTien: 1, w: 20, h: 17 },
      { id: "c", x: 40, y: 300, uuTien: 1, w: 20, h: 17 },
    ]);
    expect(giu.size).toBe(3);
  });

  it("nhãn ngắn gần nhau nhưng hộp THẬT không chạm ⇒ giữ cả hai (S và H1 của chóp, run scene3d-construction-audit)", () => {
    // Đo ở khung cuối chóp S.ABCD: neo S (590.5, 84), H1 (539.8, 101.6); viên nhãn ~15×17 và ~25×17 px.
    // Hộp cố định 68×22 cũ coi chúng chồng nhau và giấu S — đỉnh khối mất tên trong khi lời kể gọi SB, SC.
    const giu = locNhanChongNhau([
      { id: "S", x: 590.5, y: 84, uuTien: 1, w: 15, h: 17 },
      { id: "H1", x: 539.8, y: 101.6, uuTien: 2, w: 25, h: 17 },
    ]);
    expect([...giu].sort()).toEqual(["H1", "S"]);
  });

  it("hộp thật chạm nhau ⇒ vẫn giấu nhãn ưu tiên thấp", () => {
    const giu = locNhanChongNhau([
      { id: "S", x: 560, y: 90, uuTien: 1, w: 15, h: 17 },
      { id: "H1", x: 545, y: 95, uuTien: 2, w: 25, h: 17 },
    ]);
    expect([...giu]).toEqual(["H1"]);
  });

  it("tất định: cùng đầu vào cho cùng kết quả bất kể thứ tự truyền vào", () => {
    const a = [
      { id: "x", x: 10, y: 10, uuTien: 1, w: 20, h: 17 },
      { id: "y", x: 12, y: 11, uuTien: 1, w: 20, h: 17 },
    ];
    expect([...locNhanChongNhau(a)]).toEqual([...locNhanChongNhau([...a].reverse())]);
  });

  it("W3: hai điểm hiện tại cùng toạ độ (`B` đề cho và chân vuông góc `H` tại `(1,0,0)`) gộp ký hiệu thành `B ≡ H` để không mất tên đỉnh", async () => {
    const P = await import("./scene3d-presentation") as unknown as {
      kyHieuDiem?: (
        diem: { id: string; notation?: string | null; origin: "free" | "derived"; xyz?: [string, string, string] }[],
      ) => Map<string, string>;
    };
    expect(typeof P.kyHieuDiem).toBe("function");
    const m = P.kyHieuDiem!([
      { id: "H", notation: "H", origin: "derived", xyz: ["1", "0", "0"] },
      { id: "B", notation: "B", origin: "free", xyz: ["1", "0", "0"] },
      { id: "M", notation: "M", origin: "derived", xyz: ["1/2", "1/2", "0"] },
    ]);
    expect(m.get("B")).toBe("B ≡ H");
    expect(m.get("H")).toBe("B ≡ H");
    expect(m.get("M")).toBe("M");
  });
});

