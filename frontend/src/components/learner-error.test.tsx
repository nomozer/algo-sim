import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { UnsupportedNotice } from "./SimulationWorkspace";

/**
 * M17-Lite W0 — lock learner-facing error mapping phía FE.
 *
 * Server gắn `learner_reason` (thân thiện) vào envelope unsupported tại biên
 * API; UnsupportedNotice phải ƯU TIÊN nó — `reason` kỹ thuật (có thể chứa
 * token snake_case, tên role nội bộ) chỉ là fallback cho envelope cũ. Học
 * sinh không bao giờ thấy error_code / failure_category / JSON path.
 *
 * Component thuần theo props (như VisualModeToggle) vì zustand trả initial
 * state khi renderToString — không test qua store.
 */

function html(unsupported: {
  reason: string;
  learner_reason?: string;
  failure_category?: string;
}): string {
  return renderToString(<UnsupportedNotice unsupported={unsupported} />).replace(
    /<!--.*?-->/g,
    "",
  );
}

describe("M17 W0 — UnsupportedNotice hiển thị thông điệp học sinh", () => {
  it("có learner_reason → hiển thị NÓ, KHÔNG hiển thị reason kỹ thuật", () => {
    const out = html({
      reason:
        "Bài cần cơ chế chưa có engine sở hữu (optimal_pathfinding, numeric_threshold).",
      learner_reason:
        "Bài này cần một cơ chế mà AlgoSim chưa mô phỏng chính xác được, nên hệ thống từ chối trung thực.",
    });
    expect(out).toContain("từ chối trung thực");
    expect(out).not.toContain("optimal_pathfinding");
    expect(out).not.toContain("numeric_threshold");
  });

  it("envelope cũ không có learner_reason → fallback reason (tương thích ngược)", () => {
    const out = html({ reason: "Bài này chưa có mô phỏng phù hợp trong danh mục." });
    expect(out).toContain("chưa có mô phỏng phù hợp");
  });

  it("(M17-VR1) thiếu dữ kiện → tiêu đề 'CHƯA ĐỦ DỮ KIỆN', KHÔNG nói ngoài danh mục", () => {
    const out = html({
      reason: "kỹ thuật",
      learner_reason: "Đề yêu cầu duyệt cây nhưng chưa cho cấu trúc cây cụ thể.",
      failure_category: "insufficient_specification",
    });
    expect(out).toContain("CHƯA ĐỦ DỮ KIỆN");
    expect(out).not.toContain("NGOÀI DANH MỤC");
    expect(out).toContain("dạng bài này hệ có mô phỏng");
  });

  it("(M17-VR1) gap thật vẫn giữ tiêu đề ngoài danh mục", () => {
    const out = html({ reason: "x", learner_reason: "y", failure_category: "capability_gap" });
    expect(out).toContain("NGOÀI DANH MỤC MÔ PHỎNG");
  });

  it("field máy-đọc đi kèm envelope không bao giờ bị render", () => {
    const out = html({
      reason: "kỹ thuật",
      learner_reason: "Thông điệp thân thiện cho học sinh.",
      // envelope thật có thể mang các field máy-đọc — component không được lộ
      ...({ error_code: "gate_mechanism_ownership", failure_category: "capability_gap" } as object),
    });
    expect(out).toContain("thân thiện");
    expect(out).not.toContain("gate_mechanism_ownership");
    expect(out).not.toContain("capability_gap");
  });
});
