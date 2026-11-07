import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import type { UnifiedInputPrepareRequest, UnifiedInputPrepareResponse } from "../llm/client";
import { formatAttachmentSize, type ComposerAttachmentItem } from "../llm/input";
import { registerAllSimulations } from "../simulations";
import { __resetHistoryForTest } from "../state/history";
import { useAppStore } from "../state/store";
import {
  buildCameraConstraints,
  cameraErrorMessage,
  cameraSupport,
  canSwitchCamera,
  fallbackCameraConstraints,
  initialCameraTarget,
  isMobileCameraPreferred,
  nextCameraTarget,
} from "./PhotoCameraView";
import { PhotoProblemDialog } from "./PhotoProblemDialog";
import { PhotoProblemPanel } from "./PhotoProblemPanel";
import { ProblemInput, cancelComposerSubmit, runComposerSubmit } from "./ProblemInput";
import { useToastStore } from "./TopNav";
import { initialUnifiedAssistState, unifiedAssistReducer } from "./photo-problem-flow";

registerAllSimulations();

const noop = () => {};

function makeFakeAttachment(
  name: string,
  kind: "image" | "pdf" | "document",
  ext: string,
  mime: string,
  bytes = "hello-geometry-attachment",
): ComposerAttachmentItem {
  const file = new File([bytes], name, { type: mime });
  return {
    id: `att-${name}`,
    file,
    name,
    size: file.size,
    sizeFormatted: formatAttachmentSize(file.size),
    ext,
    kind,
    status: "ready",
  };
}

describe("Camera-First UX tối giản (§5–§8): không có màn crop/xoay thủ công, 4 lỗi camera phân biệt rõ", () => {
  it("ô nhập đề: menu + có Chụp ảnh đề bài & Tải tệp từ thiết bị; không mở camera lúc tải trang", () => {
    const html = renderToString(<ProblemInput />);
    expect(html).toContain("Chụp ảnh đề bài");
    expect(html).toContain("Tải tệp từ thiết bị");
    expect(html).toMatch(/id="menu-item-camera"[^>]*aria-haspopup="dialog"/);
    expect(html).not.toContain("photo-camera-dialog");
    expect(html).not.toContain("<video");
    expect(html).toContain('accept=".png,.jpg,.jpeg,.webp,.pdf,.docx"');
  });

  it("PhotoProblemDialog mở thẳng khung ngắm máy ảnh tối giản, không có nút crop/xoay thủ công", () => {
    expect(
      renderToString(
        <PhotoProblemDialog
          open={false}
          onClose={noop}
          onPickFile={noop}
          onNativeCamera={noop}
          onCaptured={noop}
        />,
      ),
    ).toBe("");

    const openHtml = renderToString(
      <PhotoProblemDialog
        open={true}
        onClose={noop}
        onPickFile={noop}
        onNativeCamera={noop}
        onCaptured={noop}
      />,
    );
    expect(openHtml).toContain('id="photo-camera-dialog"');
    expect(openHtml).toContain('data-photo-screen="camera"');
    expect(openHtml).toContain('id="btn-photo-capture"');
    expect(openHtml).toContain('id="btn-photo-library"');
    expect(openHtml).toContain('id="btn-photo-dialog-close"');

    // §5 & §6: Tuyệt đối không còn nút crop thủ công, xoay trái/phải, đặt lại khung, giữ nguyên ảnh, cắt theo khung
    for (const removedLabel of [
      "Khoanh vùng đề bài",
      "Xoay trái",
      "Xoay phải",
      "Đặt lại khung",
      "Giữ nguyên ảnh",
      "Cắt theo khung",
      "Đọc đề trong ảnh",
    ]) {
      expect(openHtml).not.toContain(removedLabel);
    }
  });

  it("4 thông báo lỗi máy ảnh trung tính, phân biệt rõ từng nguyên nhân (§7), không dùng câu sai 'đang bận ở ứng dụng khác'", () => {
    const msgDenied = cameraErrorMessage({ name: "NotAllowedError" });
    const msgNotFound = cameraErrorMessage({ name: "NotFoundError" });
    const msgUnavailable = cameraErrorMessage({ name: "NotReadableError" });
    const msgUnknown = cameraErrorMessage({ name: "SomeUnexpectedError" });

    expect(new Set([msgDenied, msgNotFound, msgUnavailable, msgUnknown]).size).toBe(4);
    expect(msgDenied).toMatch(/từ chối.*cấp quyền máy ảnh/i);
    expect(msgNotFound).toMatch(/Không tìm thấy máy ảnh/);
    expect(msgUnavailable).toMatch(/không khả dụng/);
    expect(msgUnknown).toMatch(/lỗi chưa xác định/);

    for (const m of [msgDenied, msgNotFound, msgUnavailable, msgUnknown]) {
      expect(m).not.toContain("đang bận ở ứng dụng khác");
      expect(m).toMatch(/chọn ảnh từ máy/);
    }
  });

  it("ràng buộc camera desktop/mobile, fallback và ẩn nút đổi camera khi chỉ có <= 1 thiết bị (§5, §6)", () => {
    expect(
      isMobileCameraPreferred({
        userAgentDataMobile: false,
        userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        maxTouchPoints: 10,
        anyCoarsePointer: true,
      }),
    ).toBe(false);
    expect(isMobileCameraPreferred({ userAgentDataMobile: true })).toBe(true);

    expect(buildCameraConstraints(initialCameraTarget(false))).toEqual({
      video: { width: { ideal: 2560 }, height: { ideal: 1920 } },
      audio: false,
    });
    expect(buildCameraConstraints(initialCameraTarget(true))).toEqual({
      video: { facingMode: { ideal: "environment" }, width: { ideal: 2560 }, height: { ideal: 1920 } },
      audio: false,
    });

    expect(fallbackCameraConstraints({ name: "OverconstrainedError" }, { kind: "facing", facing: "environment" })).toEqual({
      video: { width: { ideal: 2560 }, height: { ideal: 1920 } },
      audio: false,
    });
    expect(fallbackCameraConstraints({ name: "NotAllowedError" }, { kind: "facing", facing: "environment" })).toBeNull();

    // Chỉ hiện nút đổi camera khi > 1 thiết bị hoặc trên mobile chưa liệt kê rõ ID
    expect(canSwitchCamera(["cam-1"], false, 1)).toBe(false);
    expect(canSwitchCamera(["cam-1"], true, 1)).toBe(false);
    expect(canSwitchCamera(["cam-1", "cam-2"], false, 2)).toBe(true);
    expect(canSwitchCamera([""], true, 2)).toBe(true);

    const t1 = nextCameraTarget({ kind: "default" }, "cam-1", ["cam-1", "cam-2"], false);
    expect(t1).toEqual({ kind: "device", deviceId: "cam-2" });
    expect(cameraSupport({ isSecureContext: true, hasGetUserMedia: true })).toEqual({ ok: true });
    expect(cameraSupport({ isSecureContext: false, hasGetUserMedia: true }).ok).toBe(false);
  });
});

describe("Khung hỗ trợ đầu vào thống nhất & luồng gửi kết hợp chữ + tệp (§4, §14, §16, §19)", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
    useToastStore.getState().clearToasts();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    useToastStore.getState().clearToasts();
    useAppStore.getState().reset();
  });

  it("PhotoProblemPanel ẩn khi `idle`, hiện bộ chọn 1 chạm khi `needs_selection`, và thoát ký tự an toàn khi `needs_confirmation`", () => {
    expect(
      renderToString(
        <PhotoProblemPanel
          state={initialUnifiedAssistState}
          onSelectCandidate={noop}
          onEditDraft={noop}
          onToggleConfirm={noop}
          onSubmitConfirmed={noop}
          onDismiss={noop}
        />,
      ),
    ).toBe("");

    const selState = unifiedAssistReducer(initialUnifiedAssistState, {
      type: "from-prepare",
      response: {
        schema: "unified-input-prepare/1",
        status: "needs_selection",
        source_kind: "image",
        problem_text: "",
        learner_message: "Ảnh có 2 bài toán. Em chọn bài muốn dựng nhé.",
        reason_code: "MULTIPLE_PROBLEMS_AMBIGUOUS",
        flag_messages: [],
        uncertain_tokens: [],
        missing_regions: [],
        candidates: [
          {
            candidate_id: "region_1",
            label: "Bài 1",
            preview_snippet: "Cho hình chóp S.ABCD...",
            preview_data_url: null,
            page_number: null,
            has_figure: true,
            problem_text: null,
          },
          {
            candidate_id: "region_2",
            label: "Bài 2",
            preview_snippet: "Cho tứ diện đều ABCD...",
            preview_data_url: null,
            page_number: null,
            has_figure: false,
            problem_text: null,
          },
        ],
        provenance: {},
        metrics: {
          vlm_calls: 0,
          used_vlm: false,
          raw_input_bytes: 50_000,
          vlm_payload_bytes: 0,
          uncropped_baseline_bytes: 50_000,
          processing_ms: 15,
        },
      },
    });
    const selHtml = renderToString(
      <PhotoProblemPanel
        state={selState}
        onSelectCandidate={noop}
        onEditDraft={noop}
        onToggleConfirm={noop}
        onSubmitConfirmed={noop}
        onDismiss={noop}
      />,
    );
    expect(selHtml).toContain('id="composer-candidate-picker"');
    expect(selHtml).toContain('data-candidate-id="region_1"');
    expect(selHtml).toContain('data-candidate-id="region_2"');

    const xssDoc = '<img src=x onerror=alert(1)> Cho hình chóp S.ABC.';
    const confState = unifiedAssistReducer(initialUnifiedAssistState, {
      type: "from-prepare",
      response: {
        schema: "unified-input-prepare/1",
        status: "needs_confirmation",
        source_kind: "image",
        problem_text: xssDoc,
        learner_message: "Kiểm tra nhanh ký hiệu.",
        reason_code: null,
        flag_messages: ["Ký hiệu đỉnh hơi mờ."],
        uncertain_tokens: [{ token: "A'", alternatives: ["A"], location: "đỉnh A'", reason: "mờ" }],
        missing_regions: [],
        candidates: [],
        provenance: {},
        metrics: {
          vlm_calls: 1,
          used_vlm: true,
          raw_input_bytes: 50_000,
          vlm_payload_bytes: 22_000,
          uncropped_baseline_bytes: 50_000,
          processing_ms: 95,
        },
      },
    });
    const confHtml = renderToString(
      <PhotoProblemPanel
        state={confState}
        onSelectCandidate={noop}
        onEditDraft={noop}
        onToggleConfirm={noop}
        onSubmitConfirmed={noop}
        onDismiss={noop}
      />,
    );
    expect(confHtml).toContain('id="composer-extraction-confirm"');
    expect(confHtml).toContain("&lt;img src=x onerror=alert(1)&gt;");
    expect(confHtml).not.toContain("<img src=x");
    expect(confHtml).not.toMatch(/MULTIPLE_PROBLEMS_AMBIGUOUS|UNCERTAIN_TOKENS/);
  });

  it("runComposerSubmit: kết hợp chữ gõ tay + tệp đính kèm qua prepareFn rồi chuyển thẳng sang analyzeFn khi `ready`", async () => {
    const docxAtt = makeFakeAttachment(
      "de-luyen-tap.docx",
      "document",
      ".docx",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    );
    const prepareSpy = vi.fn(async (_req: UnifiedInputPrepareRequest): Promise<UnifiedInputPrepareResponse> => ({
      schema: "unified-input-prepare/1",
      status: "ready",
      source_kind: "docx",
      problem_text: "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2, SA vuông góc đáy và SA = 4. Tính thể tích khối chóp.",
      learner_message: null,
      reason_code: null,
      flag_messages: [],
      uncertain_tokens: [],
      missing_regions: [],
      candidates: [],
      provenance: {},
      metrics: {
        vlm_calls: 0,
        used_vlm: false,
        raw_input_bytes: 1024,
        vlm_payload_bytes: 0,
        uncropped_baseline_bytes: 0,
        processing_ms: 8,
      },
    }));
    const analyzeSpy = vi.fn(async (_payload: unknown) => ({
      status: "unsupported" as const,
      failure_category: "capability_gap",
      error_code: "UNSUPPORTED",
      reason: "Kiểm tra đường truyền văn bản hợp nhất.",
    }));

    await runComposerSubmit({
      canSubmit: true,
      lockRef: { current: false },
      problemText: "Hình vẽ nằm trong file, dữ kiện bổ sung là SA = 4",
      attachment: docxAtt,
      health: { ok: true, hasKey: true, cachedProblems: 0 },
      prepareFn: prepareSpy,
      analyzeFn: analyzeSpy as any,
    });

    expect(prepareSpy).toHaveBeenCalledTimes(1);
    expect(prepareSpy.mock.calls[0]?.[0]).toMatchObject({
      filename: "de-luyen-tap.docx",
      user_text: "Hình vẽ nằm trong file, dữ kiện bổ sung là SA = 4",
    });
    expect(analyzeSpy).toHaveBeenCalledTimes(1);
    expect(analyzeSpy.mock.calls[0]?.[0]).toEqual({
      type: "text",
      content:
        "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2, SA vuông góc đáy và SA = 4. Tính thể tích khối chóp.",
    });
  });

  it("cancelComposerSubmit (Case #19): huỷ request đang chạy bằng AbortController và giữ nguyên dữ liệu người học", async () => {
    const lockRef = { current: false };
    const abortRef = { current: null as AbortController | null };
    let capturedSignal: AbortSignal | undefined;

    useAppStore.getState().setProblemText("Cho hình chóp S.ABCD có SA = 4.");

    const pendingAnalyze = vi.fn((_payload: unknown, signal?: AbortSignal) => {
      capturedSignal = signal;
      return new Promise((_resolve, reject) => {
        signal?.addEventListener("abort", () => {
          reject(Object.assign(new Error("Aborted"), { name: "AbortError" }));
        });
      });
    });

    const p = runComposerSubmit({
      canSubmit: true,
      lockRef,
      abortRef,
      problemText: useAppStore.getState().problemText,
      attachment: null,
      health: { ok: true, hasKey: true, cachedProblems: 0 },
      analyzeFn: pendingAnalyze as any,
    });

    expect(useAppStore.getState().analyzing).toBe(true);
    expect(abortRef.current).not.toBeNull();

    cancelComposerSubmit(lockRef, abortRef);
    await p;

    expect(capturedSignal?.aborted).toBe(true);
    expect(useAppStore.getState().analyzing).toBe(false);
    expect(lockRef.current).toBe(false);
    expect(useAppStore.getState().problemText).toBe("Cho hình chóp S.ABCD có SA = 4.");
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });
});
