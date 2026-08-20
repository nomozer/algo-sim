import { describe, expect, it } from "vitest";
import { buildSemanticState, validateSemanticConfig } from "./model";

/**
 * Module render FRAME TIMELINE của route sinh ngữ nghĩa.
 *
 * Bất biến #31 nói khung thứ k suy hoàn toàn từ trạng thái bước k. Ở phía
 * frontend, hệ quả là: renderer chỉ ĐỌC khung, KHÔNG đánh giá lại biểu thức và
 * KHÔNG suy diễn trạng thái ngữ nghĩa. Nội suy PIXEL thì được (§4.1).
 */

const CONFIG = {
  spec_version: "1.0",
  title: "Kiểm tra ngoặc",
  frames: [
    {
      step_index: 0,
      narration: "Bắt đầu duyệt chuỗi.",
      objects: [
        { id: "s", type: "stack_view", label: "Ngăn xếp", items: [] },
        { id: "box", type: "value_box", label: "Kết quả", value: "" },
      ],
      highlighted_object_ids: [],
    },
    {
      step_index: 1,
      narration: "Đẩy '[' vào ngăn xếp.",
      objects: [
        { id: "s", type: "stack_view", label: "Ngăn xếp", items: ["["] },
        { id: "box", type: "value_box", label: "Kết quả", value: "" },
      ],
      highlighted_object_ids: ["s"],
    },
    {
      step_index: 2,
      narration: "Lấy '[' ra, khớp với ']'.",
      objects: [
        { id: "s", type: "stack_view", label: "Ngăn xếp", items: [] },
        { id: "box", type: "value_box", label: "Kết quả", value: "hợp lệ" },
      ],
      highlighted_object_ids: ["s", "box"],
    },
  ],
  view_steps: [
    { view_index: 0, frame_lo: 0, frame_hi: 0, narration: "Bắt đầu duyệt chuỗi." },
    { view_index: 1, frame_lo: 1, frame_hi: 1, narration: "Đẩy '[' vào ngăn xếp." },
    { view_index: 2, frame_lo: 2, frame_hi: 2, narration: "Lấy '[' ra, khớp với ']'." },
  ],
  grouping_level: "step",
  presentation_overflow: false,
  execution_truncated: false,
};

describe("semantic route — model", () => {
  it("timeline có đúng số bước xem", () => {
    const s = buildSemanticState(CONFIG);
    expect(s.timeline).toHaveLength(3);
  });

  it("KHÔNG đóng băng ở khung 0 — đây là hồi quy cho lỗi E1", () => {
    const s = buildSemanticState(CONFIG);
    const stackCuoi = s.timeline[2].objects.find((o) => o.id === "s");
    const boxCuoi = s.timeline[2].objects.find((o) => o.id === "box");
    expect(boxCuoi?.value).toBe("hợp lệ");
    expect(stackCuoi?.items).toEqual([]);
    const stackGiua = s.timeline[1].objects.find((o) => o.id === "s");
    expect(stackGiua?.items).toEqual(["["]);
  });

  it("bước xem đọc khung CUỐI của đoạn nó phủ", () => {
    const gop = {
      ...CONFIG,
      view_steps: [{ view_index: 0, frame_lo: 0, frame_hi: 2, narration: "Cả lượt." }],
      grouping_level: "iteration",
    };
    const s = buildSemanticState(gop);
    expect(s.timeline).toHaveLength(1);
    const box = s.timeline[0].objects.find((o) => o.id === "box");
    expect(box?.value).toBe("hợp lệ");
  });

  it("khai mức gộp để shell nói cho học sinh biết đang xem ở mức nào", () => {
    const s = buildSemanticState({ ...CONFIG, grouping_level: "iteration" });
    expect(s.groupingLevel).toBe("iteration");
  });

  it("không có định danh kĩ thuật nào lọt lên bề mặt học sinh", () => {
    const s = buildSemanticState(CONFIG);
    const beMat = JSON.stringify(s.timeline.map((t) => t.narration));
    expect(beMat).not.toContain("generic.semantic_program");
    expect(beMat).not.toContain("stack_view");
    expect(beMat).not.toContain("value_box");
  });
});

describe("semantic route — validateConfig", () => {
  it("nhận config hợp lệ", () => {
    const r = validateSemanticConfig(CONFIG);
    expect(r.ok).toBe(true);
  });

  it("từ chối config không có frames — KHÔNG cố chạy", () => {
    const r = validateSemanticConfig({ ...CONFIG, frames: [] });
    expect(r.ok).toBe(false);
  });

  it("từ chối khi view_steps không phủ hết dãy khung", () => {
    const r = validateSemanticConfig({
      ...CONFIG,
      view_steps: [{ view_index: 0, frame_lo: 0, frame_hi: 0, narration: "x" }],
    });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toContain("phủ");
  });

  it("từ chối khi các đoạn chồng lấn", () => {
    const r = validateSemanticConfig({
      ...CONFIG,
      view_steps: [
        { view_index: 0, frame_lo: 0, frame_hi: 1, narration: "a" },
        { view_index: 1, frame_lo: 1, frame_hi: 2, narration: "b" },
      ],
    });
    expect(r.ok).toBe(false);
  });

  it("từ chối khung tham chiếu ra ngoài dãy", () => {
    const r = validateSemanticConfig({
      ...CONFIG,
      view_steps: [{ view_index: 0, frame_lo: 0, frame_hi: 99, narration: "x" }],
    });
    expect(r.ok).toBe(false);
  });
});
