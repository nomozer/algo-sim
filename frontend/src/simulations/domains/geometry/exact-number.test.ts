import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { hienSo, type ExactNumberJson } from "./scene3d-model";

/**
 * SỐ CHÍNH XÁC TRÊN BỀ MẶT HỌC SINH — `√2`, `3√2/5`, không phải `1.414…`.
 *
 * ─── VÌ SAO PHÍA NÀY ĐỊNH DẠNG LẠI, DÙ BACKEND ĐÃ GỬI CHUỖI ──────────────
 *
 * Backend phát cả hai: `exact` (cấu trúc) và `value` (chuỗi đã dựng). Phía này
 * đọc CẤU TRÚC. Trùng lặp có chủ đích: hai bên định dạng độc lập là cách duy
 * nhất phát hiện khi chúng lệch nhau — nếu phía này chỉ in lại `value` thì
 * backend nói gì màn hình tin nấy, và một lỗi định dạng ở đó không bao giờ bị
 * bắt.
 *
 * Bộ ca dưới đây SONG SINH với `tests/geometry/test_radical_domain.py::
 * test_hien_thi_theo_cach_viet_SGK`. Sửa một bên mà quên bên kia thì bên kia đỏ.
 */

const R = (coefficient: string, radicand: number): ExactNumberJson =>
  ({ kind: "radical", coefficient, radicand });
const Q = (value: string): ExactNumberJson => ({ kind: "rational", value });

describe("hienSo — cách viết SGK", () => {
  it.each([
    [Q("2"), "2"],
    [Q("3/5"), "3/5"],
    [R("1", 2), "√2"],
    [R("3", 2), "3√2"],
    [R("3/5", 2), "3√2/5"],
    [R("1/2", 3), "√3/2"],
    [R("-1/2", 3), "-√3/2"],
    [R("-3/4", 5), "-3√5/4"],
  ])("%o → %s", (x, chu) => {
    expect(hienSo(x as ExactNumberJson)).toBe(chu);
  });

  it("hệ số 1 và -1 KHÔNG viết ra — `1√2` không phải cách người ta viết", () => {
    expect(hienSo(R("1", 7))).toBe("√7");
    expect(hienSo(R("-1", 7))).toBe("-√7");
  });

  it("KHÔNG có số thập phân nào lọt ra bề mặt", () => {
    for (const x of [R("1", 2), R("3/5", 2), R("1/2", 3), Q("7/3")]) {
      expect(hienSo(x)).not.toMatch(/\d\.\d/);
    }
  });
});

describe("hienSo — envelope cũ và dữ liệu lạ: nói thẳng, không đoán", () => {
  it("thiếu `exact` ⇒ dùng chuỗi dự phòng (envelope lưu trước wave này)", () => {
    expect(hienSo(undefined, "2")).toBe("2");
    expect(hienSo(undefined)).toBe("");
  });

  it("`kind` lạ ⇒ dự phòng, KHÔNG dựng bừa một chuỗi", () => {
    // Backend mở miền mà phía này chưa biết ⇒ phải lộ ra, không được đoán.
    const la = { kind: "surd_sum", terms: [] } as unknown as ExactNumberJson;
    expect(hienSo(la, "?")).toBe("?");
  });

  it("hệ số hỏng ⇒ dự phòng", () => {
    expect(hienSo(R("abc", 2), "-")).toBe("-");
  });
});

describe("MIRROR — hai bờ khai cùng một hình dạng", () => {
  it("kiểu TS khớp `radical.to_json` bên Python", () => {
    // Không import Python được; soi MÃ NGUỒN để bắt lệch tên trường. Ba tên
    // này là khớp nối giữa hai bờ — gõ lệch là im lặng hỏng.
    const py = readFileSync(
      join(__dirname, "../../../../../backend/app/simulation/geometry/radical.py"),
      "utf-8",
    );
    expect(py).toContain('"kind": "radical"');
    expect(py).toContain('"coefficient"');
    expect(py).toContain('"radicand"');
    expect(py).toContain('"kind": "rational"');
  });

  it("giá trị đo KHÔNG được đẩy qua `toNumber`", () => {
    // `value` nay có thể là `"√2"`. `toNumber` ném khi gặp chuỗi không phải
    // phân số, và một lần ném trong renderer làm sập cả khung 3D — đúng sự cố
    // `visual_transform` đã đo được trong Chrome thật.
    const src = readFileSync(join(__dirname, "scene3d-view.tsx"), "utf-8");
    expect(src).not.toMatch(/toNumber\([^)]*\.value/);
    expect(src).toContain("hienSo(o.exact, o.value)");
  });
});
