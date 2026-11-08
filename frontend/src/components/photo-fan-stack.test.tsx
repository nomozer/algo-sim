import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import type { UnifiedInputPrepareRequest, UnifiedInputPrepareResponse } from "../llm/client";
import { formatAttachmentSize, type ComposerAttachmentItem } from "../llm/input";
import { registerAllSimulations } from "../simulations";
import { __resetHistoryForTest } from "../state/history";
import { useAppStore } from "../state/store";
import { PhotoFanStack, FAN_LAYOUTS, MAX_VISIBLE_FAN_CARDS, type CapturedSessionPhoto } from "./PhotoFanStack";
import { PhotoCameraView } from "./PhotoCameraView";
import { PhotoProblemDialog } from "./PhotoProblemDialog";
import { runComposerSubmit } from "./ProblemInput";
import { useToastStore } from "./TopNav";

registerAllSimulations();

const noop = () => {};

function makeSessionPhoto(index: number): CapturedSessionPhoto {
  const file = new File([`image-bytes-${index}`], `chup-de-toan-${index + 1}.jpg`, {
    type: "image/jpeg",
  });
  return {
    id: `photo-${index + 1}`,
    file,
    fullUrl: `blob:full-photo-${index + 1}`,
    thumbUrl: `data:image/jpeg;base64,thumb-${index + 1}`,
    width: 1920,
    height: 1440,
    createdAt: 1700000000000 + index * 1000,
  };
}

function makeFakeAttachment(
  id: string,
  name: string,
  kind: "image" | "pdf" | "document" = "image",
  ext = ".jpg",
  mime = "image/jpeg",
): ComposerAttachmentItem {
  const file = new File([`bytes-${id}`], name, { type: mime });
  return {
    id,
    file,
    name,
    size: file.size,
    sizeFormatted: formatAttachmentSize(file.size),
    ext,
    kind,
    status: "ready",
  };
}

describe("PhotoFanStack (§6): 0 ảnh ẩn, 1 ảnh thẻ đơn, 2..5 ảnh xếp quạt, > 5 ảnh hiện badge +N không thêm nhãn đếm thừa", () => {
  it("0 ảnh: không hiển thị fan stack, không hiển thị chữ 0 ảnh", () => {
    const html = renderToString(
      <PhotoFanStack photos={[]} isMobile={false} onOpenPhoto={noop} onOpenMobileTray={noop} />,
    );
    expect(html).toBe("");
  });

  it("1 ảnh: hiển thị một thẻ ảnh nhỏ duy nhất (#btn-photo-fan-single), không có hiệu ứng quạt và không có chữ đếm ảnh", () => {
    const p1 = makeSessionPhoto(0);
    const html = renderToString(
      <PhotoFanStack photos={[p1]} isMobile={false} onOpenPhoto={noop} onOpenMobileTray={noop} />,
    );
    expect(html).toContain('id="btn-photo-fan-single"');
    expect(html).not.toContain('id="btn-photo-fan-card-1"');
    expect(html).toContain(p1.thumbUrl);
    // Tuyệt đối không có nhãn "1 ảnh", "Đã chụp (1)", "1/3"
    expect(html).not.toMatch(/Đã chụp|\d+\s*ảnh|\d+\/\d+/i);
  });

  it("2..5 ảnh: hiển thị PhotoFanStack (#photo-fan-stack) với đủ thẻ ảnh, dùng FAN_LAYOUTS và không có badge +N khi <= 5 ảnh", () => {
    for (const count of [2, 3, 4, 5]) {
      const photos = Array.from({ length: count }, (_, i) => makeSessionPhoto(i));
      const html = renderToString(
        <PhotoFanStack photos={photos} isMobile={false} onOpenPhoto={noop} onOpenMobileTray={noop} />,
      );
      expect(html).toContain('id="photo-fan-stack"');
      expect(html).toContain(`data-photo-count="${count}"`);
      for (let i = 1; i <= count; i++) {
        expect(html).toContain(`id="btn-photo-fan-card-${i}"`);
      }
      expect(html).not.toContain("photo-fan-overflow-badge");
      expect(html).not.toMatch(/Đã chụp|\d+\s*ảnh|\d+\/\d+/i);
      expect(FAN_LAYOUTS[count]?.open).toHaveLength(count);
      expect(FAN_LAYOUTS[count]?.collapsed).toHaveLength(count);
    }
  });

  it("> 5 ảnh: giữ toàn bộ ảnh trong phiên nhưng quạt hiển thị tối đa 5 thẻ gần nhất và không vẽ badge +N hay số thứ tự đè lên thẻ", () => {
    const photos = Array.from({ length: 7 }, (_, i) => makeSessionPhoto(i));
    const html = renderToString(
      <PhotoFanStack photos={photos} isMobile={false} onOpenPhoto={noop} onOpenMobileTray={noop} />,
    );
    expect(MAX_VISIBLE_FAN_CARDS).toBe(5);
    expect(html).toContain('data-photo-count="7"');
    expect(html).not.toContain('id="btn-photo-fan-card-1"');
    expect(html).not.toContain('id="btn-photo-fan-card-2"');
    expect(html).toContain('id="btn-photo-fan-card-3"');
    expect(html).toContain('id="btn-photo-fan-card-7"');
    expect(html).not.toContain("photo-fan-overflow-badge");
    expect(html).not.toContain("fan-card-order-badge");
    expect(html).not.toContain("+2");
  });
});

describe("PhotoCameraView & PhotoProblemDialog (§5, §7, §8): nút Xong cố định, fitMode mặc định Toàn khung, không lặp số lượng ảnh", () => {
  it("chưa chụp ảnh: không hiển thị nút Xong và không hiển thị PhotoFanStack", () => {
    const html = renderToString(
      <PhotoCameraView
        photos={[]}
        onCapture={noop}
        onCaptureBatch={noop}
        onPickFile={noop}
        onNativeCamera={noop}
      />,
    );
    expect(html).toContain('id="btn-photo-fit-mode"');
    expect(html).toContain("Toàn khung");
    expect(html).toContain('data-fit-mode="contain"');
    expect(html).toContain('id="btn-photo-capture"');
    expect(html).not.toContain('id="btn-photo-done"');
    expect(html).not.toContain('id="photo-fan-stack"');
    expect(html).not.toContain('id="btn-photo-fan-single"');
  });

  it("đã chụp >= 1 ảnh: hiện nút Xong cố định 'Xong' (không kèm số lượng ảnh) và hiện PhotoFanStack", () => {
    const photos = [makeSessionPhoto(0), makeSessionPhoto(1), makeSessionPhoto(2)];
    const html = renderToString(
      <PhotoCameraView
        photos={photos}
        onCapture={noop}
        onCaptureBatch={noop}
        onPickFile={noop}
        onNativeCamera={noop}
      />,
    );
    expect(html).toContain('id="btn-photo-done"');
    expect(html).toContain("<span>Xong</span>");
    expect(html).toContain('id="photo-fan-stack"');
    expect(html).not.toMatch(/Xong\s*\(\d+/i);
    expect(html).not.toMatch(/Dùng\s*\d+\s*ảnh/i);
    expect(html).not.toMatch(/Đã chụp/i);
  });

  it("PhotoProblemDialog render đúng aria-modal và thanh công cụ chụp ảnh", () => {
    const html = renderToString(
      <PhotoProblemDialog
        open={true}
        onClose={noop}
        onPickFile={noop}
        onNativeCamera={noop}
        onCaptured={noop}
        onCapturedBatch={noop}
      />,
    );
    expect(html).toContain('id="photo-camera-dialog"');
    expect(html).toContain('role="dialog"');
    expect(html).toContain('aria-modal="true"');
  });
});

describe("Gửi đa ảnh có thứ tự & chống race condition theo request_id (§3, §8, §9)", () => {
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

  it("runComposerSubmit: gửi nhiều ảnh theo đúng thứ tự (order_index 0, 1, 2) + request_id và gọi analyzeFn khi ready", async () => {
    const att1 = makeFakeAttachment("att-1", "trang-1.jpg");
    const att2 = makeFakeAttachment("att-2", "trang-2.jpg");
    const att3 = makeFakeAttachment("att-3", "hinh-ve-3.jpg");

    const prepareSpy = vi.fn(async (req: UnifiedInputPrepareRequest): Promise<UnifiedInputPrepareResponse> => ({
      schema: "unified-input-prepare/1",
      status: "ready",
      source_kind: "image",
      problem_text: "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc đáy và SA = 2a. Tính thể tích khối chóp.",
      learner_message: null,
      reason_code: null,
      flag_messages: [],
      uncertain_tokens: [],
      missing_regions: [],
      candidates: [],
      provenance: {
        source_attachment_ids: (req.attachments ?? []).map((item) => item.attachment_id),
      },
      request_id: req.request_id,
      metrics: {
        vlm_calls: 3,
        used_vlm: true,
        raw_input_bytes: 3072,
        vlm_payload_bytes: 3072,
        uncropped_baseline_bytes: 3072,
        processing_ms: 42,
      },
    }));

    const analyzeSpy = vi.fn(async (_payload: unknown) => ({
      status: "unsupported" as const,
      failure_category: "capability_gap",
      error_code: "UNSUPPORTED",
      reason: "Kiểm tra gửi 3 ảnh liên tiếp.",
    }));

    await runComposerSubmit({
      canSubmit: true,
      lockRef: { current: false },
      problemText: "Lưu ý lấy điểm M là trung điểm SC",
      attachments: [att1, att2, att3],
      health: { ok: true, hasKey: true, cachedProblems: 0 },
      prepareFn: prepareSpy,
      analyzeFn: analyzeSpy as any,
    });

    expect(prepareSpy).toHaveBeenCalledTimes(1);
    const sentReq = prepareSpy.mock.calls[0]?.[0]!;
    expect(sentReq.request_id).toMatch(/^a[0-9a-f]{32}$/);
    expect(sentReq.attachments).toHaveLength(3);
    expect(sentReq.attachments?.map((a) => ({ id: a.attachment_id, order: a.order_index, name: a.filename }))).toEqual([
      { id: "att-1", order: 0, name: "trang-1.jpg" },
      { id: "att-2", order: 1, name: "trang-2.jpg" },
      { id: "att-3", order: 2, name: "hinh-ve-3.jpg" },
    ]);
    expect(analyzeSpy).toHaveBeenCalledTimes(1);
  });

  it("runComposerSubmit: bỏ qua phản hồi prepare cũ nếu requestIdRef đã chuyển sang request mới", async () => {
    const att1 = makeFakeAttachment("att-old", "de-cu.jpg");
    const requestIdRef = { current: null as string | null };

    const prepareSpy = vi.fn(async (req: UnifiedInputPrepareRequest): Promise<UnifiedInputPrepareResponse> => {
      // Giả lập một request mới hơn đã thay thế requestIdRef trước khi request cũ hoàn tất
      requestIdRef.current = "prep_newer_superseding_request";
      return {
        schema: "unified-input-prepare/1",
        status: "ready",
        source_kind: "image",
        problem_text: "Đề bài cũ không được phép chạy analyze.",
        learner_message: null,
        reason_code: null,
        flag_messages: [],
        uncertain_tokens: [],
        missing_regions: [],
        candidates: [],
        provenance: {},
        request_id: req.request_id,
        metrics: {
          vlm_calls: 1,
          used_vlm: true,
          raw_input_bytes: 512,
          vlm_payload_bytes: 512,
          uncropped_baseline_bytes: 512,
          processing_ms: 10,
        },
      };
    });

    const analyzeSpy = vi.fn();

    await runComposerSubmit({
      canSubmit: true,
      lockRef: { current: false },
      requestIdRef,
      problemText: "",
      attachments: [att1],
      health: { ok: true, hasKey: true, cachedProblems: 0 },
      prepareFn: prepareSpy,
      analyzeFn: analyzeSpy as any,
    });

    expect(prepareSpy).toHaveBeenCalledTimes(1);
    // Vì requestIdRef đã đổi sang request mới hơn nên phản hồi cũ bị chặn, không gọi analyzeSpy
    expect(analyzeSpy).not.toHaveBeenCalled();
  });
});
