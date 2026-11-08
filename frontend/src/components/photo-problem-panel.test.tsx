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
  classifyCameraDevice,
  fallbackCameraConstraints,
  initialCameraTarget,
  isMobileCameraPreferred,
  nextCameraTarget,
  shouldShowCameraEntry,
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
  it("ô nhập đề: menu + hiển thị theo loại thiết bị (Desktop ẩn Chụp ảnh đề bài, Phone/Tablet hiện Chụp ảnh đề bài & Tải tệp từ thiết bị); không mở camera lúc tải trang", () => {
    const desktopHtml = renderToString(
      <ProblemInput
        deviceSignals={{
          userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
          platform: "Win32",
          maxTouchPoints: 0,
        }}
      />,
    );
    expect(desktopHtml).not.toContain("Chụp ảnh đề bài");
    expect(desktopHtml).not.toContain('id="menu-item-camera"');
    expect(desktopHtml).toContain("Tải tệp từ thiết bị");
    expect(desktopHtml).toContain('id="menu-item-upload-file"');
    expect(desktopHtml).not.toContain("photo-camera-dialog");
    expect(desktopHtml).not.toContain("<video");

    const mobileHtml = renderToString(
      <ProblemInput
        deviceSignals={{
          userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
          platform: "iPhone",
          maxTouchPoints: 5,
        }}
      />,
    );
    expect(mobileHtml).toContain("Chụp ảnh đề bài");
    expect(mobileHtml).toContain("Tải tệp từ thiết bị");
    expect(mobileHtml).toMatch(/id="menu-item-camera"[^>]*aria-haspopup="dialog"/);
    expect(mobileHtml).not.toContain("photo-camera-dialog");
    expect(mobileHtml).not.toContain("<video");
    expect(mobileHtml).toContain('accept=".png,.jpg,.jpeg,.webp,.pdf,.docx"');
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

describe("Device-Aware Camera Entry (§2–§9): 15 kịch bản phân loại thiết bị thuần & tích hợp menu dấu +", () => {
  it("15 kịch bản unit test phân loại thiết bị (classifyCameraDevice & shouldShowCameraEntry)", () => {
    // 1. iPhone Safari
    const iphoneSafari = {
      userAgent:
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
      platform: "iPhone",
      maxTouchPoints: 5,
      anyCoarsePointer: true,
    };
    expect(classifyCameraDevice(iphoneSafari)).toBe("phone");
    expect(shouldShowCameraEntry(iphoneSafari)).toBe(true);

    // 2. Android Chrome phone
    const androidPhone = {
      userAgentDataMobile: true,
      userAgentDataPlatform: "Android",
      userAgent:
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
      platform: "Linux armv81",
      maxTouchPoints: 5,
      anyCoarsePointer: true,
    };
    expect(classifyCameraDevice(androidPhone)).toBe("phone");
    expect(shouldShowCameraEntry(androidPhone)).toBe(true);

    // 3. iPad Safari (classic iPad UA)
    const ipadSafari = {
      userAgent:
        "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
      platform: "iPad",
      maxTouchPoints: 5,
      anyCoarsePointer: true,
    };
    expect(classifyCameraDevice(ipadSafari)).toBe("tablet");
    expect(shouldShowCameraEntry(ipadSafari)).toBe(true);

    // 4. iPadOS desktop-style UA (`Macintosh` + `maxTouchPoints > 1`)
    const ipadosDesktopStyle = {
      userAgent:
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
      platform: "MacIntel",
      maxTouchPoints: 5,
      anyCoarsePointer: true,
    };
    expect(classifyCameraDevice(ipadosDesktopStyle)).toBe("tablet");
    expect(shouldShowCameraEntry(ipadosDesktopStyle)).toBe(true);

    // 5. Android tablet (không có `Mobile` trong UA)
    const androidTablet = {
      userAgentDataMobile: false,
      userAgentDataPlatform: "Android",
      userAgent:
        "Mozilla/5.0 (Linux; Android 13; SM-X700) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
      platform: "Linux armv81",
      maxTouchPoints: 5,
      anyCoarsePointer: true,
    };
    expect(classifyCameraDevice(androidTablet)).toBe("tablet");
    expect(shouldShowCameraEntry(androidTablet)).toBe(true);

    // 6. Windows Chrome
    const windowsChrome = {
      userAgentDataMobile: false,
      userAgentDataPlatform: "Windows",
      userAgent:
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
      platform: "Win32",
      maxTouchPoints: 0,
      anyCoarsePointer: false,
    };
    expect(classifyCameraDevice(windowsChrome)).toBe("desktop");
    expect(shouldShowCameraEntry(windowsChrome)).toBe(false);

    // 7. Windows touch laptop (`maxTouchPoints > 0`)
    const windowsTouchLaptop = {
      userAgentDataMobile: false,
      userAgentDataPlatform: "Windows",
      userAgent:
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
      platform: "Win32",
      maxTouchPoints: 10,
      anyCoarsePointer: true,
    };
    expect(classifyCameraDevice(windowsTouchLaptop)).toBe("desktop");
    expect(shouldShowCameraEntry(windowsTouchLaptop)).toBe(false);

    // 8. macOS Safari
    const macosSafari = {
      userAgent:
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
      platform: "MacIntel",
      maxTouchPoints: 0,
      anyCoarsePointer: false,
    };
    expect(classifyCameraDevice(macosSafari)).toBe("desktop");
    expect(shouldShowCameraEntry(macosSafari)).toBe(false);

    // 9. Linux Chrome
    const linuxChrome = {
      userAgentDataMobile: false,
      userAgentDataPlatform: "Linux",
      userAgent:
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
      platform: "Linux x86_64",
      maxTouchPoints: 0,
      anyCoarsePointer: false,
    };
    expect(classifyCameraDevice(linuxChrome)).toBe("desktop");
    expect(shouldShowCameraEntry(linuxChrome)).toBe(false);

    // 10. Trường hợp thiếu thông tin nhận diện
    expect(classifyCameraDevice({})).toBe("unknown");
    expect(shouldShowCameraEntry({})).toBe(false);
    expect(classifyCameraDevice(undefined)).toBe("unknown");
    expect(shouldShowCameraEntry(undefined)).toBe(false);

    // 11. Laptop thu nhỏ cửa sổ 390px -> không hiển thị Chụp ảnh đề bài
    // (hàm thuần không phụ thuộc vào window.innerWidth)
    expect(classifyCameraDevice(windowsChrome)).toBe("desktop");
    expect(shouldShowCameraEntry(windowsChrome)).toBe(false);

    // 12. Tablet xoay ngang (1180x820) -> vẫn hiển thị Chụp ảnh đề bài
    expect(classifyCameraDevice(ipadosDesktopStyle)).toBe("tablet");
    expect(shouldShowCameraEntry(ipadosDesktopStyle)).toBe(true);
    expect(classifyCameraDevice(androidTablet)).toBe("tablet");
    expect(shouldShowCameraEntry(androidTablet)).toBe(true);

    // 13. Desktop Chrome Zoom 110% -> không hiển thị Chụp ảnh đề bài
    expect(shouldShowCameraEntry(windowsChrome)).toBe(false);

    // 14. Desktop Chrome Zoom 150% -> không hiển thị Chụp ảnh đề bài
    expect(shouldShowCameraEntry(macosSafari)).toBe(false);

    // 15. Thiết bị không có webcam / thiếu navigator.mediaDevices -> không gọi getUserMedia lúc mở menu
    expect(shouldShowCameraEntry({ userAgent: "", maxTouchPoints: 0 })).toBe(false);
  });

  it("React integration (§9): Desktop chỉ render #menu-item-upload-file (không dòng trống); Mobile/Tablet render cả #menu-item-upload-file và #menu-item-camera", () => {
    const desktopOpenHtml = renderToString(
      <ProblemInput
        initialPlusMenuOpen
        deviceSignals={{
          userAgentDataMobile: false,
          userAgentDataPlatform: "Windows",
          userAgent:
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
          platform: "Win32",
          maxTouchPoints: 10,
        }}
      />,
    );
    expect(desktopOpenHtml).toContain('id="plus-popover-menu"');
    expect(desktopOpenHtml).toContain('id="menu-item-upload-file"');
    expect(desktopOpenHtml).toContain("Tải tệp từ thiết bị");
    expect(desktopOpenHtml).not.toContain('id="menu-item-camera"');
    expect(desktopOpenHtml).not.toContain("Chụp ảnh đề bài");
    // Chỉ có đúng 1 role="menuitem" trong plus-popover-menu trên desktop
    const desktopMenuItems = desktopOpenHtml.match(/role="menuitem"/g) ?? [];
    expect(desktopMenuItems).toHaveLength(1);

    const ipadOpenHtml = renderToString(
      <ProblemInput
        initialPlusMenuOpen
        deviceSignals={{
          userAgent:
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
          platform: "MacIntel",
          maxTouchPoints: 5,
        }}
      />,
    );
    expect(ipadOpenHtml).toContain('id="menu-item-upload-file"');
    expect(ipadOpenHtml).toContain('id="menu-item-camera"');
    expect(ipadOpenHtml).toContain("Chụp ảnh đề bài");
    const ipadMenuItems = ipadOpenHtml.match(/role="menuitem"/g) ?? [];
    expect(ipadMenuItems).toHaveLength(2);
  });
});
