import { describe, expect, it } from "vitest";
import {
  CHUA_THAY,
  NHIP_PHIEN_MS,
  NHIP_THEO_DOI_MS,
  apDungPhien,
  nenGuiTienDo,
  type ClassroomSession,
} from "./classroom-sync";
import { taoTrangThai } from "../simulations/domains/geometry/interaction-state";

/**
 * LUẬT ĐỒNG BỘ LỚP — ba nhánh, và mỗi nhánh sai một kiểu khác nhau.
 *
 * Kiểm bằng HÀM THUẦN, không qua store: zustand SSR luôn trả trạng thái đầu
 * (`§8` #8), nên một test qua store sẽ xanh vì không có gì xảy ra.
 */

const PHIEN = (p: Partial<ClassroomSession> = {}): ClassroomSession => ({
  sessionId: 1, roundId: "r1", cmdId: 1, syncCmdId: 0, mode: "follow",
  assignmentId: 7, simulationId: "generic.semantic_program",
  currentStep: 4, selectedId: "M", isolatedIds: ["chop"], explodedGroups: ["face"],
  updatedAt: null, ...p,
});

const LOCAL = () => ({
  ...taoTrangThai(),
  current_step: 1,
  selected_id: "A",
  isolated_ids: ["chop::face:2"],
});

describe("U/V — BÁM THEO: lệnh mới nào cũng áp", () => {
  it("áp bước, vật đang chọn, tập cô lập và nhóm bung của giáo viên", () => {
    const r = apDungPhien(LOCAL(), PHIEN(), CHUA_THAY);
    expect(r.applied).toBe(true);
    expect(r.reason).toBe("follow");
    expect(r.next.current_step).toBe(4);
    expect(r.next.selected_id).toBe("M");
    expect(r.next.isolated_ids).toEqual(["chop"]);
    expect(r.next.exploded_groups).toEqual(["face"]);
  });

  it("ĐỌC LẠI cùng một lệnh KHÔNG áp lần hai", () => {
    // Đây là lý do `cmd_id` tồn tại: thiếu nó thì mỗi nhịp 1,5 giây lại kéo
    // học sinh về chỗ giáo viên, và em nào đang xem lại bước cũ bị giật liên tục.
    const p = PHIEN();
    const mot = apDungPhien(LOCAL(), p, CHUA_THAY);
    const hai = apDungPhien({ ...mot.next, current_step: 9 }, p, mot.seen);
    expect(hai.applied).toBe(false);
    expect(hai.next.current_step).toBe(9);
  });

  it("lệnh MỚI hơn thì áp tiếp", () => {
    const mot = apDungPhien(LOCAL(), PHIEN(), CHUA_THAY);
    const hai = apDungPhien(mot.next, PHIEN({ cmdId: 2, currentStep: 6 }), mot.seen);
    expect(hai.applied).toBe(true);
    expect(hai.next.current_step).toBe(6);
  });
});

describe("W — TỰ DO: KHÔNG ghi đè thao tác học sinh", () => {
  it("lệnh mới ở chế độ tự do không đụng trạng thái cục bộ", () => {
    const local = LOCAL();
    const r = apDungPhien(local, PHIEN({ mode: "free", cmdId: 5 }), CHUA_THAY);
    expect(r.applied).toBe(false);
    expect(r.next).toBe(local);
    // …nhưng mốc vẫn tiến, nếu không thì lệnh cũ sẽ "mới" mãi mãi.
    expect(r.seen.cmdId).toBe(5);
  });
});

describe("X — GỌI CẢ LỚP VỀ: áp ĐÚNG MỘT LẦN, kể cả khi đang tự do", () => {
  it("sync áp được dù mode = free", () => {
    const r = apDungPhien(LOCAL(), PHIEN({ mode: "free", cmdId: 3, syncCmdId: 3 }),
                          CHUA_THAY);
    expect(r.applied).toBe(true);
    expect(r.reason).toBe("sync");
    expect(r.next.current_step).toBe(4);
  });

  it("sau khi áp, học sinh LẠI TỰ DO — đọc lại không áp nữa", () => {
    const p = PHIEN({ mode: "free", cmdId: 3, syncCmdId: 3 });
    const mot = apDungPhien(LOCAL(), p, CHUA_THAY);
    const tuDo = { ...mot.next, selected_id: "SA" };
    const hai = apDungPhien(tuDo, p, mot.seen);
    expect(hai.applied).toBe(false);
    expect(hai.next.selected_id).toBe("SA");
  });

  it("sync LẦN HAI là một mốc mới, áp lại được", () => {
    const mot = apDungPhien(LOCAL(), PHIEN({ mode: "free", cmdId: 3, syncCmdId: 3 }),
                            CHUA_THAY);
    const hai = apDungPhien({ ...mot.next, selected_id: "SA" },
                            PHIEN({ mode: "free", cmdId: 4, syncCmdId: 4,
                                    selectedId: "H" }), mot.seen);
    expect(hai.applied).toBe(true);
    expect(hai.next.selected_id).toBe("H");
  });
});

describe("ROUND — tiết mới cắt sạch quá khứ", () => {
  it("`cmdId` LỚN của tiết cũ không nuốt lệnh của tiết mới", () => {
    // Nếu không đặt lại mốc theo round, một tiết cũ chạy tới cmdId 99 sẽ làm
    // mọi lệnh của tiết mới (bắt đầu từ 1) trông như "đã thấy rồi".
    const cu = apDungPhien(LOCAL(), PHIEN({ roundId: "r1", cmdId: 99 }), CHUA_THAY);
    expect(cu.seen.cmdId).toBe(99);
    const moi = apDungPhien(cu.next, PHIEN({ roundId: "r2", cmdId: 1, currentStep: 2 }),
                            cu.seen);
    expect(moi.applied).toBe(true);
    expect(moi.next.current_step).toBe(2);
  });
});

describe("O — ID lạc: FAIL-SAFE, không sập phiên", () => {
  it("bỏ ID không có trong cảnh, giữ nguyên phần còn lại", () => {
    const p = PHIEN({ selectedId: "KHONG_CO", isolatedIds: ["chop", "MA"] });
    const r = apDungPhien(LOCAL(), p, CHUA_THAY, (id) => id === "chop");
    expect(r.applied).toBe(true);
    expect(r.next.selected_id).toBeNull();
    expect(r.next.isolated_ids).toEqual(["chop"]);
  });

  it("nhóm bung KHÔNG bị lọc — nó là tên nhóm, không phải id vật", () => {
    const r = apDungPhien(LOCAL(), PHIEN({ explodedGroups: ["face"] }),
                          CHUA_THAY, () => false);
    expect(r.next.exploded_groups).toEqual(["face"]);
  });
});

describe("KẾT THÚC TIẾT — không hoàn nguyên thao tác học sinh", () => {
  it("phiên null giữ nguyên trạng thái cục bộ", () => {
    const local = LOCAL();
    const r = apDungPhien(local, null, { roundId: "r1", cmdId: 9, syncCmdId: 9 });
    expect(r.next).toBe(local);
    expect(r.applied).toBe(false);
    expect(r.seen).toEqual(CHUA_THAY);
  });
});

describe("CHỐNG SPAM — chỉ gửi khi TIÊU ĐIỂM đổi", () => {
  it("lần đầu thì gửi", () => {
    expect(nenGuiTienDo(null, { step: 0, selectedId: null, luc: 0 })).toBe(true);
  });

  it("không đổi gì thì KHÔNG gửi", () => {
    const t = { step: 2, selectedId: "M", luc: 0 };
    expect(nenGuiTienDo(t, { ...t, luc: 5000 })).toBe(false);
  });

  it("đổi vật đang chọn thì gửi", () => {
    expect(nenGuiTienDo({ step: 2, selectedId: "M", luc: 0 },
                        { step: 2, selectedId: "SA", luc: 5000 })).toBe(true);
  });

  it("đổi nhanh hơn nhịp tối thiểu thì KHÔNG gửi", () => {
    // Học sinh xoay hình sinh hàng chục thay đổi mỗi giây — gửi hết là dựng
    // một máy theo dõi thay vì một lớp học.
    expect(nenGuiTienDo({ step: 2, selectedId: "M", luc: 0 },
                        { step: 3, selectedId: "N", luc: 200 })).toBe(false);
  });
});

describe("NHỊP — hai câu hỏi, hai độ trễ chấp nhận được", () => {
  it("lệnh giáo viên nhanh hơn bảng theo dõi", () => {
    expect(NHIP_PHIEN_MS).toBeLessThan(NHIP_THEO_DOI_MS);
    expect(NHIP_PHIEN_MS).toBeGreaterThanOrEqual(1000);
  });
});

describe("AB/AC — không có nguyên thuỷ chiếu màn hình hay điều khiển từ xa", () => {
  it("module đồng bộ chỉ chở ID ngữ nghĩa và số bước", async () => {
    const { readFileSync } = await import("node:fs");
    const src = readFileSync(new URL("classroom-sync.ts", import.meta.url), "utf-8");
    for (const cam of ["screenshot", "captureStream", "getDisplayMedia",
                       "innerHTML", "toDataURL", "RTCPeerConnection",
                       "mousemove", "pointermove"]) {
      expect(src.includes(cam), `${cam} không được có ở tầng này`).toBe(false);
    }
  });
});
