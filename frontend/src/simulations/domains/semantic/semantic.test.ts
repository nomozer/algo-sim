import { describe, expect, it } from "vitest";
import { buildSemanticState, validateSemanticConfig } from "./model";

/**
 * Module đọc FRAME TIMELINE của route `generic.semantic_program`.
 *
 * Bất biến #31: khung thứ k suy hoàn toàn từ bước k. Phía frontend chỉ ĐỌC khung, không đánh giá lại biểu thức.
 * (/13) Khung không còn đối tượng 2D (đường container của miền Tin học đã gỡ; hình đi bằng `scene3d`), nên các ca
 * `stack_view`/`graph_view`/`map_view`/`value_box` đã gỡ; timeline, phân nhịp và cổng config thì vẫn phải khoá.
 */

const CONFIG = {
  spec_version: "1.0",
  title: "Thiết diện qua ba trung điểm",
  frames: [
    { step_index: 0, narration: "Khởi tạo các điểm.", objects: [], highlighted_object_ids: [] },
    { step_index: 1, narration: "Dựng trung điểm M của SA.", objects: [], highlighted_object_ids: ["M"] },
    { step_index: 2, narration: "Dựng thiết diện MNPQ.", objects: [], highlighted_object_ids: ["td"] },
  ],
  view_steps: [
    { view_index: 0, frame_lo: 0, frame_hi: 0, narration: "Khởi tạo các điểm." },
    { view_index: 1, frame_lo: 1, frame_hi: 1, narration: "Dựng trung điểm M của SA." },
    { view_index: 2, frame_lo: 2, frame_hi: 2, narration: "Dựng thiết diện MNPQ." },
  ],
  grouping_level: "step",
  presentation_overflow: false,
  execution_truncated: false,
};

describe("semantic route — model", () => {
  it("timeline có đúng số bước xem", () => {
    expect(buildSemanticState(CONFIG).timeline).toHaveLength(3);
  });

  it("KHÔNG đóng băng ở khung 0 — đây là hồi quy cho lỗi E1", () => {
    const s = buildSemanticState(CONFIG);
    expect(s.timeline.map((t) => t.highlighted)).toEqual([[], ["M"], ["td"]]);
  });

  it("bước xem đọc khung CUỐI của đoạn nó phủ", () => {
    const gop = {
      ...CONFIG,
      view_steps: [{ view_index: 0, frame_lo: 0, frame_hi: 2, narration: "Cả lượt." }],
      grouping_level: "iteration",
    };
    const s = buildSemanticState(gop);
    expect(s.timeline).toHaveLength(1);
    expect(s.timeline[0].highlighted).toEqual(["td"]);
  });

  it("khai mức gộp để shell nói cho học sinh biết đang xem ở mức nào", () => {
    expect(buildSemanticState({ ...CONFIG, grouping_level: "iteration" }).groupingLevel).toBe("iteration");
  });

  it("không có định danh kĩ thuật nào lọt lên bề mặt học sinh", () => {
    const beMat = JSON.stringify(buildSemanticState(CONFIG).timeline.map((t) => t.narration));
    expect(beMat).not.toContain("generic.semantic_program");
  });
});

describe("semantic route — validateConfig", () => {
  it("nhận config hợp lệ", () => {
    expect(validateSemanticConfig(CONFIG).ok).toBe(true);
  });

  it("từ chối config không có frames — KHÔNG cố chạy", () => {
    expect(validateSemanticConfig({ ...CONFIG, frames: [] }).ok).toBe(false);
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
