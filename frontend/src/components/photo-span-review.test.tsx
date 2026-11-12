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
  it("sửa nhiều span theo vị trí Unicode của Python, kể cả ký hiệu toán ngoài BMP", () => {
    const base = "Đề 𝑎: SA = a√3, A'B = 2/3.";
    const tokens = [
      { token: "a√3", alternatives: [], location: "", reason: "", span_id: "radical", span_start: 11, span_end: 14 },
      { token: "2/3", alternatives: [], location: "", reason: "", span_id: "fraction", span_start: 22, span_end: 25 },
    ];
    expect(applySpanValues(base, tokens, { radical: "2a√2", fraction: "√3/2" }))
      .toBe("Đề 𝑎: SA = 2a√2, A'B = √3/2.");
    expect(applySpanValues(base, tokens, { radical: "a√3", fraction: "2/3" })).toBe(base);
  });

  it.each(["edit-span", "edit-draft"] as const)("%s yêu cầu xác nhận lại nội dung đã đổi", (type) => {
    let s = unifiedAssistReducer(initialUnifiedAssistState, { type: "from-prepare", response: prepare() });
    s = unifiedAssistReducer(s, { type: "confirm-span", spanId: "sp7" });
    s = unifiedAssistReducer(s, { type: "confirm-span", spanId: "diagram" });
    s = unifiedAssistReducer(s, { type: "toggle-confirm", value: true });
    expect(canConfirmAssistText(s)).toBe(true);
    s = unifiedAssistReducer(s, type === "edit-span"
      ? { type, spanId: "sp7", value: "a√2" }
      : { type, text: TEXT.replace("a√3", "a√2") });
    expect(canConfirmAssistText(s)).toBe(false);
    expect(s.confirmed).toBe(false);
  });

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

/* Run `local-semantic-source-gate-reliability`: OCR tách một biểu thức thành nhiều mảnh ("4BCD-" + "A'B'C'D'"),
   khoảng trắng ở giữa không thuộc chỗ nào ⇒ sửa từng chỗ không ghép lại được. Học sinh nối chỗ sửa với chữ kế tiếp. */
describe("OCR local: nối chỗ sửa với chữ kế tiếp", () => {
  const SPLIT = "Cho hình hộp chữ nhật 4BCD- A'B'C'D' có AB = a, BC = 2a. Đề 𝑎: tính BD.";
  const p0 = Array.from(SPLIT).indexOf("4");
  const pAB = Array.from(SPLIT).join("").indexOf("AB = a");
  const cps = (s: string, sub: string) => Array.from(s.slice(0, s.indexOf(sub))).length;
  function prep(): UnifiedInputPrepareResponse {
    const base = prepare();
    return {
      ...base,
      problem_text: SPLIT,
      uncertain_tokens: [
        { token: "4BCD-", alternatives: ["ABCD."], location: "dòng 1", reason: "Tên khối đọc chưa chắc", kind: "math",
          span_id: "spA", span_start: cps(SPLIT, "4BCD-"), span_end: cps(SPLIT, "4BCD-") + 5, source: "local_ocr" },
        { token: "BD", alternatives: [], location: "dòng 1", reason: "Nhãn đọc chưa chắc", kind: "math",
          span_id: "spZ", span_start: cps(SPLIT, "BD."), span_end: cps(SPLIT, "BD.") + 2, source: "local_ocr" },
      ],
    };
  }
  void p0; void pAB;

  it("nối với chữ kế tiếp rồi sửa cả cụm: không còn khoảng trắng thừa, chỗ phía sau không lệch vị trí", () => {
    let s = unifiedAssistReducer(initialUnifiedAssistState, { type: "from-prepare", response: prep() });
    s = unifiedAssistReducer(s, { type: "extend-span", spanId: "spA" });
    expect(s.spanValues.spA).toBe("4BCD- A'B'C'D'");
    expect(s.spanReviewed.spA).toBeFalsy();
    s = unifiedAssistReducer(s, { type: "edit-span", spanId: "spA", value: "ABCD.A'B'C'D'" });
    s = unifiedAssistReducer(s, { type: "edit-span", spanId: "spZ", value: "AC" });
    expect(s.draftText).toBe("Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = a, BC = 2a. Đề 𝑎: tính AC.");
  });

  it("tách lại khôi phục đúng chỗ cũ và giá trị cũ; nối/tách đều huỷ xác nhận", () => {
    let s = unifiedAssistReducer(initialUnifiedAssistState, { type: "from-prepare", response: prep() });
    s = unifiedAssistReducer(s, { type: "confirm-span", spanId: "spA" });
    s = unifiedAssistReducer(s, { type: "confirm-span", spanId: "spZ" });
    s = unifiedAssistReducer(s, { type: "toggle-confirm", value: true });
    expect(canConfirmAssistText(s)).toBe(true);
    s = unifiedAssistReducer(s, { type: "extend-span", spanId: "spA" });
    expect(s.confirmed).toBe(false);
    expect(canConfirmAssistText(s)).toBe(false);
    s = unifiedAssistReducer(s, { type: "restore-span", spanId: "spA" });
    expect(s.spanValues.spA).toBe("4BCD-");
    expect(s.draftText).toBe(SPLIT);
    expect(s.confirmed).toBe(false);
  });

  it("không nối qua ranh giới câu hay chữ cách xa; chỗ kế tiếp được đánh dấu thì gộp luôn vào cụm", () => {
    const end = "Tính BD. Cho AB.";
    const r = { ...prep(), problem_text: end, uncertain_tokens: [
      { token: "BD.", alternatives: [], location: "", reason: "", kind: "math", span_id: "x", span_start: 5, span_end: 8, source: "local_ocr" },
    ] };
    let s = unifiedAssistReducer(initialUnifiedAssistState, { type: "from-prepare", response: r });
    expect(unifiedAssistReducer(s, { type: "extend-span", spanId: "x" })).toBe(s);
    const two = { ...prep(), problem_text: "ab 4BCD- A'B'C'D' cd", uncertain_tokens: [
      { token: "4BCD-", alternatives: [], location: "", reason: "", kind: "math", span_id: "a", span_start: 3, span_end: 8, source: "local_ocr" },
      { token: "A'B'C'D'", alternatives: [], location: "", reason: "", kind: "math", span_id: "b", span_start: 9, span_end: 17, source: "local_ocr" },
    ] };
    s = unifiedAssistReducer(initialUnifiedAssistState, { type: "from-prepare", response: two });
    s = unifiedAssistReducer(s, { type: "extend-span", spanId: "a" });
    expect(s.uncertainTokens.map((t) => t.span_id)).toEqual(["a"]);
    expect(s.spanValues.a).toBe("4BCD- A'B'C'D'");
    s = unifiedAssistReducer(s, { type: "edit-span", spanId: "a", value: "ABCD.A'B'C'D'" });
    expect(s.draftText).toBe("ab ABCD.A'B'C'D' cd");
    s = unifiedAssistReducer(s, { type: "restore-span", spanId: "a" });
    expect(s.uncertainTokens.map((t) => t.span_id)).toEqual(["a", "b"]);
  });

  it("bảng xác nhận có nút nối và nút tách lại, không lộ mã kỹ thuật", () => {
    let s = unifiedAssistReducer(initialUnifiedAssistState, { type: "from-prepare", response: prep() });
    const before = renderToString(<PhotoProblemPanel state={s} busy={false} onEditDraft={() => {}} onToggleConfirm={() => {}}
      onSubmitConfirmed={() => {}} onDismiss={() => {}} onSelectCandidate={() => {}} onExtendSpan={() => {}} onRestoreSpan={() => {}} />);
    expect(before).toContain("data-span-extend=\"spA\"");
    s = unifiedAssistReducer(s, { type: "extend-span", spanId: "spA" });
    const after = renderToString(<PhotoProblemPanel state={s} busy={false} onEditDraft={() => {}} onToggleConfirm={() => {}}
      onSubmitConfirmed={() => {}} onDismiss={() => {}} onSelectCandidate={() => {}} onExtendSpan={() => {}} onRestoreSpan={() => {}} />);
    expect(after).toContain("data-span-restore=\"spA\"");
    expect(after).not.toContain("extend-span");
  });
});
