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

describe("semantic route — graph_view", () => {
  const withGraph = {
    ...CONFIG,
    frames: [
      {
        step_index: 0,
        narration: "Bắt đầu từ đỉnh 1.",
        objects: [{
          id: "g", type: "graph_view", label: "Đồ thị",
          nodes: ["1", "2", "3"],
          edges: [["1", "2"], ["2", "3"]],
          visited: [], current: "1",
        }],
        highlighted_object_ids: [],
      },
      {
        step_index: 1,
        narration: "Thăm đỉnh 2.",
        objects: [{
          id: "g", type: "graph_view", label: "Đồ thị",
          nodes: ["1", "2", "3"],
          edges: [["1", "2"], ["2", "3"]],
          visited: ["1"], current: "2",
        }],
        highlighted_object_ids: ["g"],
      },
    ],
    view_steps: [
      { view_index: 0, frame_lo: 0, frame_hi: 0, narration: "Bắt đầu từ đỉnh 1." },
      { view_index: 1, frame_lo: 1, frame_hi: 1, narration: "Thăm đỉnh 2." },
    ],
  };

  it("giữ nguyên topology và trạng thái đỉnh do backend gửi", () => {
    const s = buildSemanticState(withGraph);
    const g0 = s.timeline[0].objects[0];
    expect(g0.nodes).toEqual(["1", "2", "3"]);
    expect(g0.edges).toEqual([["1", "2"], ["2", "3"]]);
    expect(g0.current).toBe("1");
    expect(g0.visited).toEqual([]);
  });

  it("trạng thái đỉnh ĐỔI theo bước — không đóng băng ở khung đầu", () => {
    const s = buildSemanticState(withGraph);
    expect(s.timeline[1].objects[0].visited).toEqual(["1"]);
    expect(s.timeline[1].objects[0].current).toBe("2");
  });

  it("config có graph_view vẫn qua validateConfig", () => {
    expect(validateSemanticConfig(withGraph).ok).toBe(true);
  });
});

describe("semantic route — map_view", () => {
  /* `map` là `MemoryType` đã admit từ lâu mà tới 2026-08-23 mới có primitive.
     Hệ quả cũ: mọi bài mà ĐÁP ÁN là một bảng (đếm tần suất, gom nhóm, dựng bảng
     tra) chạy được nhưng không xem được — `learner_surface.py` phơi ra trên
     fixture #18. Ba test dưới khoá đúng ba điều bảng phải làm được. */
  const withMap = {
    ...CONFIG,
    frames: [
      {
        step_index: 0,
        narration: "Bảng còn rỗng.",
        objects: [{ id: "freq", type: "map_view", label: "Bảng tần suất", entries: [] }],
        highlighted_object_ids: [],
      },
      {
        step_index: 1,
        narration: "Đếm được a:2, b:1.",
        objects: [{
          id: "freq", type: "map_view", label: "Bảng tần suất",
          entries: [["a", 2], ["b", 1]],
        }],
        highlighted_object_ids: ["freq"],
      },
    ],
    view_steps: [
      { view_index: 0, frame_lo: 0, frame_hi: 0, narration: "Bảng còn rỗng." },
      { view_index: 1, frame_lo: 1, frame_hi: 1, narration: "Đếm được a:2, b:1." },
    ],
  };

  it("bảng RỖNG THẬT giữ nguyên là rỗng, không bị dựng mục giả", () => {
    expect(buildSemanticState(withMap).timeline[0].objects[0].entries).toEqual([]);
  });

  it("bảng ĐỔI theo bước — đây là thứ bài học đang dạy", () => {
    const s = buildSemanticState(withMap);
    expect(s.timeline[1].objects[0].entries).toEqual([["a", 2], ["b", 1]]);
    expect(s.timeline[0].objects[0].entries).not.toEqual(
      s.timeline[1].objects[0].entries,
    );
  });

  it("config có map_view qua validateConfig", () => {
    expect(validateSemanticConfig(withMap).ok).toBe(true);
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
