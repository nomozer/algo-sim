import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { HomeWorkStrip, oViec } from "./HomeWorkStrip";

/**
 * DẢI VIỆC TRÊN TRANG CHỦ — luật ở hàm thuần, không ở component.
 *
 * `HomeWorkStrip` đọc ba store, mà zustand ở SSR luôn trả trạng thái đầu
 * (`§8` #13). Dựng component rồi khẳng định nội dung sẽ xanh vì màn hình rỗng
 * — xanh vì lý do sai. Nên `oViec` gánh toàn bộ luật, và SSR chỉ dùng để kiểm
 * đúng MỘT tính chất mà trạng thái rỗng nói được thật: không dữ liệu thì không
 * dựng gì.
 */

const BAI = (n: number, xong = 0) =>
  Array.from({ length: n }, (_, i) => ({ completed: i < xong }));

describe("oViec — rỗng thì KHÔNG dựng gì", () => {
  it("chưa có lớp và chưa có bài ⇒ mảng rỗng", () => {
    expect(oViec(false, 0, [])).toEqual([]);
    expect(oViec(true, 0, [])).toEqual([]);
  });

  it("có lớp nhưng chưa có bài ⇒ vẫn dựng (lớp là câu trả lời có ích)", () => {
    expect(oViec(false, 1, []).length).toBe(2);
  });

  it("SSR trạng thái rỗng ⇒ dựng ra chuỗi rỗng, không ô trống", () => {
    // Đây là điều SSR nói được thật: chưa đăng nhập / chưa có dữ liệu.
    expect(renderToString(<HomeWorkStrip />)).toBe("");
  });
});

describe("oViec — học sinh đếm BÀI CHƯA XONG, không đếm tổng", () => {
  it("5 bài, 2 đã xong ⇒ còn 3", () => {
    const o = oViec(false, 2, BAI(5, 2));
    expect(o.map((x) => [x.nhan, x.so])).toEqual([
      ["lớp của em", 2],
      ["bài chưa xong", 3],
    ]);
  });

  it("xong hết ⇒ 0, KHÔNG ẩn ô (0 là một câu trả lời)", () => {
    // Ẩn ô khi bằng 0 làm học sinh không phân biệt được "xong hết" với "hỏng".
    const o = oViec(false, 1, BAI(3, 3));
    expect(o.find((x) => x.nhan === "bài chưa xong")?.so).toBe(0);
  });
});

describe("oViec — giáo viên đếm BÀI ĐÃ GIAO, không đếm bài chưa xong", () => {
  it("tiến độ của học sinh KHÔNG đổi con số của giáo viên", () => {
    // Giáo viên hỏi "tôi đã giao mấy bài", không hỏi "mấy bài chưa ai làm".
    const a = oViec(true, 2, BAI(5, 0));
    const b = oViec(true, 2, BAI(5, 5));
    expect(a).toEqual(b);
    expect(a.find((x) => x.nhan === "bài đã giao")?.so).toBe(5);
  });

  it("hai vai KHÔNG dùng chung nhãn", () => {
    const hs = oViec(false, 1, BAI(2)).map((x) => x.nhan);
    const gv = oViec(true, 1, BAI(2)).map((x) => x.nhan);
    expect(hs).not.toEqual(gv);
  });
});

describe("đích điều hướng là VIEW hợp lệ, không phải chuỗi tự do", () => {
  it("mỗi ô trỏ tới đúng một trang đang có", () => {
    for (const vai of [true, false]) {
      for (const x of oViec(vai, 1, BAI(1))) {
        expect(["classes", "assignments"]).toContain(x.di);
      }
    }
  });
});
