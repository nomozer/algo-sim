import { describe, expect, it } from "vitest";
import { danhTinhBai, nhanMoBai } from "./AssignmentsView";

/**
 * HAI BUG ĐÃ THẬT SỰ CHẶN CẢ TÍNH NĂNG — nghiệm thu ba trình duyệt bắt được,
 * không một test API nào thấy. File này giữ chúng ở lại quá khứ.
 *
 *   1. `setActiveAssignment` bỏ rơi `classroomId`. Hậu quả hoàn toàn im lặng:
 *      `LiveClassStrip` hỏi phiên dạy theo lớp, thiếu trường ấy thì
 *      `classId === null` và cả tầng lớp trực tiếp không dựng. Không lỗi,
 *      không cảnh báo — chỉ là một dải điều khiển không bao giờ xuất hiện.
 *
 *   2. Nút mở bài chỉ dựng cho học sinh (`!isTeacher && …`). Giáo viên giao bài
 *      xong thì không vào được chính bài ấy, mà dock điều khiển lớp lại nằm
 *      TRONG xưởng — nên "giáo viên dẫn tiết" không có đường nào chạm tới.
 *
 * Vì sao test HÀM THUẦN chứ không render `AssignmentsView`: component đọc ba
 * store, và zustand ở SSR luôn trả trạng thái đầu (`§8` #13) ⇒ danh sách rỗng ⇒
 * mọi khẳng định xanh vì màn hình trống. Luật phải sống ngoài component mới
 * khoá được.
 */

describe("danhTinhBai — lớp của bài KHÔNG được rơi mất", () => {
  const BAI = {
    id: 7, title: "Thiết diện S.ABCD", instruction: "Dựng thiết diện qua M.",
    classroomId: 3,
  };

  it("giữ đủ bốn trường, `classroomId` có mặt", () => {
    expect(danhTinhBai(BAI)).toEqual({
      id: 7, title: "Thiết diện S.ABCD", instruction: "Dựng thiết diện qua M.",
      classroomId: 3,
    });
  });

  it("`classroomId` là SỐ, không phải undefined", () => {
    // Chính xác cái đã sai: object dựng xong trông đúng, chỉ thiếu một khoá.
    expect(typeof danhTinhBai(BAI).classroomId).toBe("number");
  });

  it("không kéo theo `envelope` vào danh tính phiên", () => {
    // Envelope đi đường riêng (`loadEnvelope`). Nhét cả vào đây là dựng bản
    // sao thứ hai của cùng một sự thật, rồi hai bản trôi khỏi nhau.
    const co = danhTinhBai({ ...BAI, envelope: { lon: true } } as never);
    expect("envelope" in co).toBe(false);
  });
});

describe("nhanMoBai — CẢ HAI vai đều mở được bài", () => {
  it("giáo viên: mở để dạy", () => {
    expect(nhanMoBai(true, null)).toBe("Mở để dạy");
  });

  it("giáo viên: nhãn KHÔNG đổi theo tiến độ (giáo viên không làm bài)", () => {
    expect(nhanMoBai(true, { completed: true })).toBe("Mở để dạy");
    expect(nhanMoBai(true, { completed: false })).toBe("Mở để dạy");
  });

  it("học sinh: ba trạng thái nói ba việc khác nhau", () => {
    expect(nhanMoBai(false, null)).toBe("Bắt đầu");
    expect(nhanMoBai(false, { completed: false })).toBe("Làm tiếp");
    expect(nhanMoBai(false, { completed: true })).toBe("Xem lại");
  });

  it("KHÔNG vai nào bị trả nhãn rỗng — rỗng nghĩa là không mở được", () => {
    for (const vai of [true, false]) {
      for (const p of [null, undefined, { completed: true }, { completed: false }]) {
        expect(nhanMoBai(vai, p).length).toBeGreaterThan(0);
      }
    }
  });
});
