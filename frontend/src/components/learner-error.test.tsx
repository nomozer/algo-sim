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
  refusal_cause?: "SOURCE" | "CONSTRUCTION" | "UNKNOWN";
}): string {
  return renderToString(<UnsupportedNotice unsupported={unsupported} />).replace(
    /<!--.*?-->/g,
    "",
  );
}

describe("UnsupportedNotice hiển thị thông điệp học sinh", () => {
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

  it("thiếu dữ kiện → tiêu đề 'CHƯA ĐỦ DỮ KIỆN', KHÔNG nói ngoài danh mục; chỉ SOURCE mới mời bổ sung dữ liệu", () => {
    const outSource = html({
      reason: "kỹ thuật",
      learner_reason: "Đề yêu cầu duyệt cây nhưng chưa cho cấu trúc cây cụ thể.",
      failure_category: "insufficient_specification",
      refusal_cause: "SOURCE",
    });
    expect(outSource).toContain("CHƯA ĐỦ DỮ KIỆN");
    expect(outSource).not.toContain("NGOÀI DANH MỤC");
    expect(outSource).toContain("dạng bài này hệ có mô phỏng");

    const outUnknown = html({
      reason: "kỹ thuật",
      learner_reason: "Đề yêu cầu duyệt cây nhưng chưa cho cấu trúc cây cụ thể.",
      failure_category: "insufficient_specification",
    });
    // HFOI-F6: không có SOURCE ⇒ hệ chưa xác định được, KHÔNG quy cho đề ("CHƯA ĐỦ DỮ KIỆN" chỉ dành cho SOURCE).
    expect(outUnknown).toContain("CHƯA XÁC ĐỊNH ĐỦ DỮ KIỆN");
    expect(outUnknown).not.toContain("đề chưa đủ dữ kiện");
    expect(outUnknown).not.toContain("NGOÀI DANH MỤC");
    expect(outUnknown).not.toContain("Bổ sung dữ liệu còn thiếu vào đề");
    expect(outUnknown).not.toContain("dạng bài này hệ có mô phỏng");
  });

  it("gap thật vẫn giữ tiêu đề ngoài danh mục", () => {
    const out = html({ reason: "x", learner_reason: "y", failure_category: "capability_gap" });
    expect(out).toContain("NGOÀI DANH MỤC MÔ PHỎNG");
  });

  it("đề môn khác → 'THUỘC MÔN HỌC KHÁC', KHÔNG hứa mở rộng danh mục", () => {
    const out = html({
      reason: "kỹ thuật",
      learner_reason: "Bài này thuộc môn học khác.",
      failure_category: "out_of_scope",
    });
    expect(out).toContain("THUỘC MÔN HỌC KHÁC");
    expect(out).not.toContain("NGOÀI DANH MỤC");
    // Lời hứa sai: hệ sẽ không bao giờ thêm hoá học vào danh mục.
    expect(out).not.toContain("mở rộng dần");
  });

  it("chủ đề có trong chương trình nhưng không có cơ chế → tiêu đề riêng", () => {
    const out = html({
      reason: "kỹ thuật",
      learner_reason: "Nội dung này đọc hiểu là đủ.",
      failure_category: "not_simulation_suitable",
    });
    expect(out).toContain("KHÔNG CẦN MÔ PHỎNG");
    // Nói "ngoài danh mục" ở đây làm học sinh ngồi chờ một thứ không có gì để thêm.
    expect(out).not.toContain("NGOÀI DANH MỤC");
    expect(out).not.toContain("mở rộng dần");
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
