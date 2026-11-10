import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import type { UnifiedInputPrepareResponse } from "../llm/client";
import { PhotoProblemPanel } from "./PhotoProblemPanel";
import {
  applySpanValues,
  assistBlocker,
  assistCorrectionCount,
  canConfirmAssistText,
  initialUnifiedAssistState,
  unifiedAssistReducer,
} from "./photo-problem-flow";

/* Run `image-first-ocr-verified-geometry`: học sinh sửa / xác nhận TẠI CHỖ các chỗ OCR local chưa chắc,
   không phải gõ lại cả đề; bản sửa là văn bản mới (giải lại, không tái dùng kết quả cũ). */

const TEXT = "Cho hình chóp S.ABCD có đáy là hình vuông cạnh a, SA = a√3. Tính thể tích khối chóp S.ABCD.";
const sStart = TEXT.indexOf("a√3");

function prepare(): UnifiedInputPrepareResponse {
  return {
    schema: "unified-input-prepare/1",
    status: "needs_confirmation",
    source_kind: "image",
    problem_text: TEXT,
    learner_message: "Máy đã đọc đề từ ảnh; còn 1 chỗ chưa chắc chắn được đánh dấu.",
    reason_code: "LOCAL_OCR_REVIEW_REQUIRED",
    flag_messages: [],
    uncertain_tokens: [
      {
        token: "a√3",
        alternatives: ["aV3", "a3"],
        location: "dòng 1",
        reason: "Dấu căn (√) đọc chưa chắc",
        kind: "math",
        span_id: "sp7",
        span_start: sStart,
        span_end: sStart + 3,
        crop_data_url: "data:image/jpeg;base64,AAAA",
        source: "local_ocr",
      },
      {
        token: "",
        alternatives: [],
        location: "hình vẽ",
        reason: "Hình vẽ có thể chứa dữ kiện chưa đọc được",
        kind: "diagram",
        span_id: "diagram",
        span_start: -1,
        span_end: -1,
        source: "local_ocr",
      },
    ],
    missing_regions: [],
    candidates: [],
    provenance: { input_route: "LOCAL_OCR_NEEDS_CONFIRMATION" },
    metrics: { vlm_calls: 0, used_vlm: false, raw_input_bytes: 1, vlm_payload_bytes: 0, uncropped_baseline_bytes: 1, processing_ms: 1 },
  };
}

describe("OCR local: xác nhận từng chỗ chưa chắc", () => {
  it("sửa một ký hiệu thay đúng khoảng ký tự, phần còn lại của đề giữ nguyên", () => {
    let s = unifiedAssistReducer(initialUnifiedAssistState, { type: "from-prepare", response: prepare() });
    expect(s.draftText).toBe(TEXT);
    s = unifiedAssistReducer(s, { type: "edit-span", spanId: "sp7", value: "a√2" });
    expect(s.draftText).toBe(TEXT.replace("SA = a√3", "SA = a√2"));
    expect(assistCorrectionCount(s)).toBe(1);
    expect(applySpanValues(TEXT, s.uncertainTokens, { sp7: "2a" })).toContain("SA = 2a.");
  });

  it("không tự xác nhận thay học sinh: phải xem mọi chỗ (kể cả hình vẽ) và đánh dấu đã kiểm tra", () => {
    let s = unifiedAssistReducer(initialUnifiedAssistState, { type: "from-prepare", response: prepare() });
    s = unifiedAssistReducer(s, { type: "toggle-confirm", value: true });
    expect(canConfirmAssistText(s)).toBe(false);
    expect(assistBlocker(s)).toContain("Còn 2 chỗ");
    s = unifiedAssistReducer(s, { type: "confirm-span", spanId: "sp7" });
    s = unifiedAssistReducer(s, { type: "confirm-span", spanId: "diagram" });
    expect(canConfirmAssistText(s)).toBe(true);
    expect(assistCorrectionCount(s)).toBe(0);
  });

  it("sửa thẳng cả ô văn bản chuyển sang văn bản tự do, khoá sửa tại chỗ (vị trí không còn đúng)", () => {
    let s = unifiedAssistReducer(initialUnifiedAssistState, { type: "from-prepare", response: prepare() });
    s = unifiedAssistReducer(s, { type: "edit-draft", text: "Cho hình lập phương ABCD.A'B'C'D' cạnh 2. Tính AC'." });
    const before = s.draftText;
    s = unifiedAssistReducer(s, { type: "edit-span", spanId: "sp7", value: "zzz" });
    expect(s.draftText).toBe(before);
    s = unifiedAssistReducer(s, { type: "toggle-confirm", value: true });
    expect(canConfirmAssistText(s)).toBe(true);
  });

  it("bảng hiển thị ảnh cắt, ô sửa, phương án thay thế; không lộ mã kỹ thuật", () => {
    const s = unifiedAssistReducer(initialUnifiedAssistState, { type: "from-prepare", response: prepare() });
    const html = renderToString(
      <PhotoProblemPanel
        state={s}
        onSelectCandidate={() => {}}
        onEditDraft={() => {}}
        onToggleConfirm={() => {}}
        onSubmitConfirmed={() => {}}
        onDismiss={() => {}}
        onEditSpan={() => {}}
        onConfirmSpan={() => {}}
      />,
    );
    expect(html).toContain('id="photo-span-review"');
    expect(html).toContain('data-span-input="sp7"');
    expect(html).toContain("photo-span-crop");
    expect(html).toContain("aV3");
    expect(html).toContain("Hình không có thêm dữ kiện");
    expect(html).not.toContain("LOCAL_OCR");
    expect(html).not.toContain("LIVE_AI_DISABLED");
  });
});
