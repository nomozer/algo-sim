import { describe, expect, it } from "vitest";
import { AxoClientError, type UnifiedInputPrepareResponse } from "../llm/client";
import {
  PHOTO_MAX_BYTES,
  assistBlocker,
  canConfirmAssistText,
  clientFileProblem,
  describeUncertainToken,
  initialUnifiedAssistState,
  photoReadErrorMessage,
  unifiedAssistReducer,
} from "./photo-problem-flow";

const SAMPLE_PROBLEM = "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2. Tính thể tích khối chóp.";

function makePrepareResponse(
  overrides: Partial<UnifiedInputPrepareResponse> = {},
): UnifiedInputPrepareResponse {
  return {
    schema: "unified-input-prepare/1",
    status: "ready",
    source_kind: "image",
    problem_text: SAMPLE_PROBLEM,
    learner_message: null,
    reason_code: null,
    flag_messages: [],
    uncertain_tokens: [],
    missing_regions: [],
    candidates: [],
    provenance: {},
    metrics: {
      vlm_calls: 1,
      used_vlm: true,
      raw_input_bytes: 90_000,
      vlm_payload_bytes: 42_000,
      uncropped_baseline_bytes: 90_000,
      processing_ms: 120,
    },
    ...overrides,
  };
}

describe("unifiedAssistReducer — mặc định không có màn xác nhận trung gian (§9, §14, §16, §17)", () => {
  it("đề bài rõ ràng (`ready`) giữ nguyên trạng thái `idle` — 0 bước xác nhận", () => {
    const s = unifiedAssistReducer(initialUnifiedAssistState, {
      type: "from-prepare",
      response: makePrepareResponse({ status: "ready" }),
    });
    expect(s.phase).toBe("idle");
  });

  it("tài liệu có nhiều bài độc lập chưa rõ bài cần dựng (`needs_selection`) ⇒ mở bộ chọn ứng viên", () => {
    const s = unifiedAssistReducer(initialUnifiedAssistState, {
      type: "from-prepare",
      response: makePrepareResponse({
        status: "needs_selection",
        source_kind: "pdf",
        learner_message: "Tài liệu có 2 bài toán độc lập. Em chạm chọn bài muốn dựng nhé.",
        candidates: [
          {
            candidate_id: "prob_1",
            label: "Bài 1 (trang 1)",
            preview_snippet: "Cho hình chóp S.ABC có đáy đều cạnh a...",
            preview_data_url: null,
            page_number: 1,
            has_figure: true,
            problem_text: null,
          },
          {
            candidate_id: "prob_2",
            label: "Bài 2 (trang 2)",
            preview_snippet: "Cho hình lăng trụ đứng ABC.A'B'C'...",
            preview_data_url: null,
            page_number: 2,
            has_figure: true,
            problem_text: null,
          },
        ],
      }),
    });
    expect(s.phase).toBe("needs_selection");
    expect(s.candidates).toHaveLength(2);
    expect(s.candidates[1]?.candidate_id).toBe("prob_2");

    const reset = unifiedAssistReducer(s, { type: "reset" });
    expect(reset).toEqual(initialUnifiedAssistState);
  });

  it("chỉ khi ký hiệu chưa chắc chắn hoặc vùng nghi bị che (`needs_confirmation`) mới yêu cầu kiểm tra trước khi dựng", () => {
    let s = unifiedAssistReducer(initialUnifiedAssistState, {
      type: "from-prepare",
      response: makePrepareResponse({
        status: "needs_confirmation",
        problem_text: SAMPLE_PROBLEM,
        flag_messages: ["Có ký hiệu đọc chưa chắc chắn — em kiểm tra nhanh nội dung."],
        uncertain_tokens: [
          { token: "A'", alternatives: ["A1"], location: "đỉnh A'", reason: "mờ nét phẩy" },
        ],
        missing_regions: ["Góc phải dưới bị ngón tay che một phần."],
      }),
    });
    expect(s.phase).toBe("needs_confirmation");
    expect(canConfirmAssistText(s)).toBe(false);
    expect(assistBlocker(s)).toMatch(/xác nhận/);

    // Cho phép sửa ký hiệu giữ nguyên toán học rồi xác nhận
    const edited = "Cho hình chóp S.ABC có SA ⊥ (ABC), AB = 2, A' là trung điểm SB. Tính thể tích.";
    s = unifiedAssistReducer(s, { type: "edit-draft", text: edited });
    expect(s.draftText).toBe(edited);
    expect(canConfirmAssistText(s)).toBe(false);

    s = unifiedAssistReducer(s, { type: "toggle-confirm", value: true });
    expect(canConfirmAssistText(s)).toBe(true);
    expect(assistBlocker(s)).toBeNull();

    // Nếu xoá còn quá ngắn thì vẫn chặn an toàn
    const tooShort = unifiedAssistReducer(s, { type: "edit-draft", text: "S.ABC" });
    expect(canConfirmAssistText(tooShort)).toBe(false);
    expect(assistBlocker(tooShort)).toMatch(/quá ngắn/);
  });
});

describe("lỗi chuẩn bị đầu vào → lời cho người học (không lộ biến cấu hình kỹ thuật)", () => {
  const http = (status: number, message: string, reasonCode?: string) =>
    new AxoClientError({ kind: "http", code: "SERVICE_UNAVAILABLE", status, message, reasonCode });

  it("huỷ chủ động ⇒ trả null (im lặng)", () => {
    expect(photoReadErrorMessage(Object.assign(new Error("x"), { name: "AbortError" }))).toBeNull();
  });

  it("LIVE_AI_DISABLED và MISSING_API_KEY ⇒ lời người học trung tính, không nhắc tên biến môi trường", () => {
    const tat = photoReadErrorMessage(http(503, "… (ALLOW_LIVE_AI=0).", "LIVE_AI_DISABLED"))!;
    const khoa = photoReadErrorMessage(http(503, "Máy chủ chưa cấu hình GEMINI_API_KEY.", "MISSING_API_KEY"))!;
    for (const m of [tat, khoa]) {
      expect(m).toMatch(/gõ đề vào ô nhập|PDF\/DOCX/);
      expect(m).not.toMatch(/ALLOW_LIVE_AI|GEMINI|API|_KEY/);
    }
  });

  it("trần kích thước tệp & mô tả ký hiệu chưa chắc", () => {
    expect(clientFileProblem({ name: "de.jpg", type: "image/jpeg", size: 120_000 })).toBeNull();
    expect(clientFileProblem({ name: "de.jpg", type: "image/jpeg", size: 0 })).toMatch(/rỗng/);
    expect(clientFileProblem({ name: "de.jpg", type: "image/jpeg", size: PHOTO_MAX_BYTES + 1 })).toMatch(/quá lớn/);
    expect(
      describeUncertainToken({ token: "0", alternatives: ["O"], location: "tâm O(0;0;0)", reason: "mờ" }),
    ).toBe("“0” có thể là “O” — ở “tâm O(0;0;0)”");
  });
});
