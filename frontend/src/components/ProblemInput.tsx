import { useEffect, useLayoutEffect, useReducer, useRef, useState } from "react";
import { useAppStore } from "../state/store";
import { displayBrand } from "../branding";
import { useAuthStore } from "../state/auth";
import { newAttemptId } from "../state/history";
import { useToastStore } from "./TopNav";
import {
  IconClose,
  IconSend,
} from "./icons";
import {
  AxoClientError,
  analyzeViaServer,
  fetchHealth,
  prepareUnifiedInputViaServer,
  type ClientFailureContract,
  type ServerHealth,
  type UnifiedInputPrepareResponse,
} from "../llm/client";
import {
  COMPOSER_ACCEPT,
  IMAGE_ACCEPT,
  canPreviewAttachment,
  canSubmitComposer,
  composerAttachmentMimeOf,
  formatAttachmentSize,
  isClearlyInvalidPdf,
  readAsBase64,
  splitAttachmentName,
  validateComposerFile,
  type ComposerAttachmentItem,
} from "../llm/input";
import type { AnalysisUnsupported } from "../core/types";
import type { SimulationEnvelope } from "../simulations/types";
import { PhotoProblemDialog } from "./PhotoProblemDialog";
import { type CameraDeviceSignals } from "./PhotoCameraView";
import {
  captureScreenStillFrame,
  classifyScreenCaptureError,
  classifyScreenCaptureSupportError,
  resolveUploadMenuCapabilities,
  type UploadMenuCapabilitySignals,
} from "./ScreenCaptureDialog";
import { PhotoProblemPanel } from "./PhotoProblemPanel";
import { PdfPreview, renderPdfFirstPageThumbnail } from "./PdfPreview";
import { AxoScrollbar } from "./AxoScrollbar";
import {
  canConfirmAssistText,
  initialUnifiedAssistState,
  photoReadErrorMessage,
  unifiedAssistReducer,
  type UnifiedAssistState,
} from "./photo-problem-flow";

const MISSING_PREMISE_CODES = new Set([
  "GIVEN_VALUE_NOT_IN_SOURCE",
  "ASSUMPTION_DETERMINES_ANSWER",
  "MISSING_CURVED_DIMENSION",
  "UNDERDETERMINED_POINT",
]);

const INCONSISTENT_PREMISE_CODES = new Set([
  "INCONSISTENT_FACTS",
  "SOURCE_SHAPE_CONTRADICTS_COORDINATES",
]);

const SOURCE_CONFLICT_CODES = new Set([
  "NON_POSITIVE_LENGTH",
  "PLANE_DOES_NOT_CUT",
  "PLANE_OVERDETERMINED",
  "COLLINEAR_PLANE",
  "CONCURRENT_BASE",
]);

function normalizeDisplayBrand(text: string): string {
  return displayBrand(text)
    .replace(/^Không xác định được[:\s—–-]*/i, "")
    .trim();
}

function isSafeFallbackReason(text: string): boolean {
  if (!text) return false;
  return !/Traceback|ValidationError|pydantic|_[a-z0-9]+_[a-z0-9]+/i.test(text);
}

export interface HomeRefusalPresentation {
  title: string;
  body: string;
  hint: string;
}

export function describeHomeRefusal(
  unsupported: AnalysisUnsupported,
): HomeRefusalPresentation {
  const rec = unsupported as AnalysisUnsupported & {
    error_code?: string;
    reason_code?: string;
  };
  const cat = rec.failure_category ?? "";
  const errCode = rec.error_code ?? "";
  const reasonCode = rec.reason_code ?? "";
  const cause = rec.refusal_cause;

  const isOutOfScope =
    cat === "out_of_scope" || errCode === "OUT_OF_SCOPE" || reasonCode === "not_geometry";
  const isMissingPremise =
    cat === "insufficient_specification" || MISSING_PREMISE_CODES.has(errCode);
  const isInconsistentPremise =
    INCONSISTENT_PREMISE_CODES.has(errCode) ||
    (cause === "SOURCE" && SOURCE_CONFLICT_CODES.has(errCode));
  const isCapabilityGap =
    cat === "capability_gap" ||
    cat === "not_simulation_suitable" ||
    errCode === "UNSUPPORTED" ||
    reasonCode === "not_simulation_suitable" ||
    reasonCode === "requested_operation_uncovered";

  let title = "Đề bài chưa được hỗ trợ";
  let hint = "Bạn có thể thử các bài về thiết diện, khoảng cách, góc hoặc thể tích.";

  if (isOutOfScope) {
    title = "Đề bài chưa được hỗ trợ";
  } else if (isMissingPremise) {
    title = "Đề bài chưa đủ dữ kiện để dựng hình";
    hint = "Bạn có thể bổ sung dữ kiện còn thiếu ngay trên ô nhập rồi nhấn Dựng hình.";
  } else if (isInconsistentPremise) {
    title = "Dữ kiện đề bài chưa nhất quán";
    hint = "Bạn có thể kiểm tra lại số liệu và quan hệ trong đề ngay trên ô nhập.";
  } else if (isCapabilityGap) {
    title = "Axo chưa hỗ trợ phép dựng này";
  }

  const rawLearner = typeof unsupported.learner_reason === "string"
    ? normalizeDisplayBrand(unsupported.learner_reason)
    : "";
  const rawReason = typeof unsupported.reason === "string"
    ? normalizeDisplayBrand(unsupported.reason)
    : "";

  const body =
    rawLearner ||
    (isOutOfScope
      ? "Axo hiện hỗ trợ mô phỏng hình học không gian. Bạn có thể thử các bài về thiết diện, khoảng cách, góc hoặc thể tích."
      : (isSafeFallbackReason(rawReason) ? rawReason : "") ||
        (isMissingPremise
          ? "Đề bài còn thiếu dữ kiện cần thiết để xác định hình không gian duy nhất."
          : "Hệ thống chưa thể tạo mô phỏng đã kiểm chứng từ nội dung đề hiện tại."));

  return { title, body, hint };
}

export interface ComposerErrorPresentation {
  tone: "info" | "error";
  title: string;
  description: string;
}

export function describeComposerError(
  analysisError: string | null,
  health: ServerHealth | null | "loading",
  clientFailure: ClientFailureContract | null = null,
): ComposerErrorPresentation | null {
  if (clientFailure) {
    switch (clientFailure.code) {
      case "QUOTA_EXCEEDED":
        return {
          tone: "info",
          title: "Đã dùng hết hạn mức dựng hình hôm nay",
          description: normalizeDisplayBrand(clientFailure.message),
        };
      case "MAINTENANCE_MODE":
        return {
          tone: "info",
          title: "Hệ thống đang bảo trì",
          description: normalizeDisplayBrand(clientFailure.message),
        };
      case "ACCOUNT_LOCKED":
        return {
          tone: "error",
          title: "Tài khoản đang tạm khóa",
          description: normalizeDisplayBrand(clientFailure.message),
        };
      case "NETWORK_UNREACHABLE":
        if (health === null || health === "loading" || health.hasKey) {
          return {
            tone: "error",
            title: "Không kết nối được máy chủ",
            description:
              "Vui lòng kiểm tra kết nối mạng rồi nhấn Dựng hình lại. Nội dung đề và tệp đính kèm vẫn được giữ nguyên.",
          };
        }
        return {
          tone: "info",
          title: "Dịch vụ phân tích đề hiện chưa sẵn sàng",
          description:
            "Máy chủ chưa bật kết nối AI cho đề tự nhập. Bạn vẫn có thể mở các mô hình mẫu bên dưới.",
        };
      case "SERVICE_UNAVAILABLE":
        return {
          tone: "info",
          title: "Dịch vụ phân tích đề hiện chưa sẵn sàng",
          description:
            "Máy chủ chưa bật kết nối AI cho đề tự nhập. Bạn vẫn có thể mở các mô hình mẫu bên dưới.",
        };
      case "INVALID_INPUT":
        return {
          tone: "info",
          title: "Chưa đủ thông tin đề bài",
          description: normalizeDisplayBrand(clientFailure.message),
        };
      case "NOT_FOUND":
        return {
          tone: "error",
          title: "Không tìm thấy tài nguyên yêu cầu",
          description: normalizeDisplayBrand(clientFailure.message),
        };
      case "HTTP_ERROR":
        return {
          tone: "error",
          title: "Máy chủ trả về lỗi khi phân tích",
          description: normalizeDisplayBrand(clientFailure.message),
        };
    }
  }

  if (!analysisError || /lượt mô phỏng thử/.test(analysisError)) return null;

  if (/sử dụng hết hạn mức|hết hạn mức.*lượt dựng hình/i.test(analysisError)) {
    return {
      tone: "info",
      title: "Đã dùng hết hạn mức dựng hình hôm nay",
      description: normalizeDisplayBrand(analysisError),
    };
  }

  if (/chế độ bảo trì/i.test(analysisError)) {
    return {
      tone: "info",
      title: "Hệ thống đang bảo trì",
      description: normalizeDisplayBrand(analysisError),
    };
  }

  if (/tạm khóa bởi Quản trị viên/i.test(analysisError)) {
    return {
      tone: "error",
      title: "Tài khoản đang tạm khóa",
      description: normalizeDisplayBrand(analysisError),
    };
  }

  const isNetworkOffline =
    /Không kết nối được máy chủ|Failed to fetch|NetworkError|Load failed/i.test(analysisError);
  const isServiceUnavailable =
    /chưa cấu hình|thiếu khóa|API key|503|chưa sẵn sàng/i.test(analysisError) ||
    (!isNetworkOffline && health !== "loading" && health !== null && !health.hasKey);
  const isInputValidation =
    /Đề bài quá ngắn|tối thiểu 10 ký tự|Chế độ lưu đệm chưa hỗ trợ|Chế độ kiểm chứng không dùng mạng/i.test(
      analysisError,
    );

  if (isNetworkOffline && (health === null || health === "loading" || health.hasKey)) {
    return {
      tone: "error",
      title: "Không kết nối được máy chủ",
      description:
        "Vui lòng kiểm tra kết nối mạng rồi nhấn Dựng hình lại. Nội dung đề và tệp đính kèm vẫn được giữ nguyên.",
    };
  }

  if (isServiceUnavailable) {
    return {
      tone: "info",
      title: "Dịch vụ phân tích đề hiện chưa sẵn sàng",
      description:
        "Máy chủ chưa bật kết nối AI cho đề tự nhập. Bạn vẫn có thể mở các mô hình mẫu bên dưới.",
    };
  }

  if (isInputValidation) {
    return {
      tone: "info",
      title: "Chưa đủ thông tin đề bài",
      description: normalizeDisplayBrand(analysisError),
    };
  }

  return {
    tone: "error",
    title: "Dựng hình chưa thành công",
    description:
      "Máy chủ gặp sự cố tạm thời khi xử lý yêu cầu. Nội dung đề và tệp đính kèm vẫn được giữ nguyên để thử lại.",
  };
}

export interface RunComposerSubmitOptions {
  canSubmit: boolean;
  lockRef: { current: boolean };
  abortRef?: { current: AbortController | null };
  requestIdRef?: { current: string | null };
  problemText: string;
  attachment?: ComposerAttachmentItem | null;
  attachments?: ComposerAttachmentItem[];
  health: ServerHealth | null | "loading";
  analyzeFn?: typeof analyzeViaServer;
  prepareFn?: typeof prepareUnifiedInputViaServer;
  selectedCandidateId?: string;
  overridePreparedText?: string;
  onAssistRequired?: (response: UnifiedInputPrepareResponse) => void;
}

const useIsomorphicLayoutEffect = typeof window !== "undefined" ? useLayoutEffect : useEffect;

export interface CollisionRect {
  top: number;
  bottom: number;
  left: number;
  right: number;
}

export interface PlusPopoverPosition {
  left: number;
  top: number;
  placement: "bottom" | "top";
  maxHeight?: number;
  collisionFlipped?: boolean;
}

export function computePlusPopoverPosition(params: {
  triggerRect: { top: number; bottom: number; left: number; right: number; width: number; height: number };
  menuWidth: number;
  menuHeight: number;
  viewportWidth: number;
  viewportHeight: number;
  cssZoom?: number;
  gapPx?: number;
  marginPx?: number;
  preferredPlacement?: "top" | "bottom";
  avoidRects?: CollisionRect[];
  avoidClearancePx?: number;
}): PlusPopoverPosition {
  const gap = params.gapPx ?? 8;
  const margin = params.marginPx ?? 12;
  const preferred = params.preferredPlacement ?? "top";
  const zoom = params.cssZoom && Number.isFinite(params.cssZoom) && params.cssZoom > 0 ? params.cssZoom : 1;
  const vw = Math.max(margin * 2 + 40, params.viewportWidth);
  const vh = Math.max(margin * 2 + 40, params.viewportHeight);
  const mw = Math.max(1, params.menuWidth);
  const maxAvailableHeight = Math.max(44, vh - margin * 2);
  const mh = Math.min(Math.max(1, params.menuHeight), maxAvailableHeight);

  const maxLeft = Math.max(margin, vw - mw - margin);
  const rawLeft = Math.max(margin, Math.min(maxLeft, params.triggerRect.left));
  const menuRight = rawLeft + mw;

  const spaceBelow = vh - params.triggerRect.bottom - margin;
  const spaceAbove = params.triggerRect.top - margin;
  const topFitsViewport = spaceAbove >= mh + gap;
  const bottomFitsViewport = spaceBelow >= mh + gap;

  const candidateTopY = Math.max(margin, Math.min(vh - mh - margin, params.triggerRect.top - mh - gap));
  const candidateBottomY = Math.max(margin, Math.min(vh - mh - margin, params.triggerRect.bottom + gap));

  const clearance = (params.avoidClearancePx ?? 8) * zoom;
  const avoidList = params.avoidRects ?? [];
  const calcCollisionArea = (candTop: number): number => {
    const candBottom = candTop + mh;
    let total = 0;
    for (const r of avoidList) {
      if (r.right <= r.left || r.bottom <= r.top) continue;
      const ix = Math.max(0, Math.min(menuRight, r.right) - Math.max(rawLeft, r.left));
      const iy = Math.max(
        0,
        Math.min(candBottom, r.bottom + clearance) - Math.max(candTop, r.top - clearance),
      );
      total += ix * iy;
    }
    return total;
  };

  const topCollision = calcCollisionArea(candidateTopY);
  const bottomCollision = calcCollisionArea(candidateBottomY);

  let placement: "bottom" | "top" = preferred;
  let rawTop: number;
  let collisionFlipped = false;

  if (preferred === "top") {
    if (topFitsViewport) {
      placement = "top";
      rawTop = candidateTopY;
    } else if (bottomFitsViewport && bottomCollision === 0) {
      placement = "bottom";
      rawTop = candidateBottomY;
      collisionFlipped = topFitsViewport && topCollision > 0;
    } else if (topFitsViewport && !bottomFitsViewport) {
      placement = "top";
      rawTop = candidateTopY;
    } else if (bottomFitsViewport && !topFitsViewport) {
      placement = "bottom";
      rawTop = candidateBottomY;
    } else if (bottomCollision < topCollision && spaceBelow >= spaceAbove * 0.6) {
      placement = "bottom";
      rawTop = candidateBottomY;
      collisionFlipped = topCollision > 0;
    } else if (spaceAbove >= spaceBelow) {
      placement = "top";
      rawTop = candidateTopY;
    } else {
      placement = "bottom";
      rawTop = candidateBottomY;
    }
  } else {
    if (bottomFitsViewport && bottomCollision === 0) {
      placement = "bottom";
      rawTop = candidateBottomY;
    } else if (topFitsViewport && topCollision === 0) {
      placement = "top";
      rawTop = candidateTopY;
      collisionFlipped = bottomFitsViewport && bottomCollision > 0;
    } else if (bottomFitsViewport && !topFitsViewport) {
      placement = "bottom";
      rawTop = candidateBottomY;
    } else if (topFitsViewport && !bottomFitsViewport) {
      placement = "top";
      rawTop = candidateTopY;
    } else if (topCollision < bottomCollision && spaceAbove >= spaceBelow * 0.6) {
      placement = "top";
      rawTop = candidateTopY;
      collisionFlipped = bottomCollision > 0;
    } else if (spaceBelow >= spaceAbove) {
      placement = "bottom";
      rawTop = candidateBottomY;
    } else {
      placement = "top";
      rawTop = candidateTopY;
    }
  }

  rawTop = Math.max(margin, Math.min(vh - mh - margin, rawTop));

  const maxHeight =
    params.menuHeight > maxAvailableHeight
      ? Math.round((maxAvailableHeight / zoom) * 10) / 10
      : undefined;

  return {
    left: Math.round((rawLeft / zoom) * 10) / 10,
    top: Math.round((rawTop / zoom) * 10) / 10,
    placement,
    ...(maxHeight !== undefined ? { maxHeight } : {}),
    ...(collisionFlipped ? { collisionFlipped: true } : {}),
  };
}

/** Huỷ chủ động lượt đang trích xuất / dựng hình: giữ nguyên nội dung gõ tay và tệp đính kèm. */
export function cancelComposerSubmit(
  lockRef: { current: boolean },
  abortRef?: { current: AbortController | null },
  requestIdRef?: { current: string | null },
): void {
  const ctl = abortRef?.current ?? null;
  if (abortRef) abortRef.current = null;
  lockRef.current = false;
  ctl?.abort();
  const store = useAppStore.getState();
  if (requestIdRef?.current) {
    store.clearProblemProcessing(requestIdRef.current);
  } else {
    const inFlight = Object.values(store.problemProcessingRecords).find(
      (r) => r.status === "in_progress",
    );
    if (inFlight) {
      store.clearProblemProcessing(inFlight.canonicalId);
    }
  }
  store.setAnalyzing(false);
}

export async function runComposerSubmit({
  canSubmit,
  lockRef,
  abortRef,
  requestIdRef,
  problemText,
  attachment = null,
  attachments,
  health,
  analyzeFn = analyzeViaServer,
  prepareFn = prepareUnifiedInputViaServer,
  selectedCandidateId,
  overridePreparedText,
  onAssistRequired,
}: RunComposerSubmitOptions): Promise<void> {
  if (!canSubmit || lockRef.current) return;
  lockRef.current = true;
  // Một lần bấm gửi = một lần học. Nếu người dùng đang gửi lại ngay lượt vừa thất bại trong cùng khung nhập,
  // giữ nguyên ID ổn định của lượt đó để cập nhật trạng thái mà không nhân bản bản ghi.
  const reusableFailedId =
    requestIdRef?.current &&
    useAppStore.getState().problemProcessingRecords[requestIdRef.current]?.status ===
      "needs_attention"
      ? requestIdRef.current
      : null;
  const attemptId = reusableFailedId ?? newAttemptId();
  if (requestIdRef) {
    requestIdRef.current = attemptId;
  }

  const ctl = typeof AbortController !== "undefined" ? new AbortController() : null;
  if (abortRef) abortRef.current = ctl;

  const targetAttachments =
    attachments && attachments.length > 0
      ? attachments
      : attachment
        ? [attachment]
        : [];

  const initialStatement =
    (typeof overridePreparedText === "string" ? overridePreparedText.trim() : problemText.trim()) ||
    targetAttachments[0]?.name ||
    "Bài toán đang xử lý";

  const store = useAppStore.getState();
  store.setAnalysisError(null);
  store.clearUnsupported();
  useToastStore.getState().dismissToast("composer-refusal");
  store.startProblemProcessing(attemptId, initialStatement);
  store.setAnalyzing(true);

  try {
    let finalProblemText = "";

    if (typeof overridePreparedText === "string") {
      finalProblemText = overridePreparedText.trim();
    } else if (targetAttachments.length === 0) {
      finalProblemText = problemText.trim();
    } else {
      const contents = await Promise.all(
        targetAttachments.map((item) => readAsBase64(item.file)),
      );
      if (ctl?.signal.aborted) {
        useAppStore.getState().clearProblemProcessing(attemptId);
        return;
      }
      if (requestIdRef?.current && requestIdRef.current !== attemptId) {
        useAppStore.getState().clearProblemProcessing(attemptId);
        return;
      }

      const firstAtt = targetAttachments[0]!;
      const attachmentPayloads = targetAttachments.map((item, idx) => ({
        attachment_id: item.id,
        order_index: idx,
        source_type: (item.source ?? (item.kind === "image" ? "upload" : item.kind)) as
          | "camera"
          | "upload"
          | "paste"
          | "pdf"
          | "document",
        content: contents[idx]!,
        mime_type: composerAttachmentMimeOf(item),
        filename: item.name,
      }));

      const prepared = await prepareFn(
        {
          request_id: attemptId,
          content: contents[0]!,
          mime_type: composerAttachmentMimeOf(firstAtt),
          filename: firstAtt.name,
          attachments: attachmentPayloads,
          user_text: problemText.trim() || undefined,
          selected_candidate_id: selectedCandidateId,
        },
        ctl?.signal,
      );
      if (ctl?.signal.aborted) {
        useAppStore.getState().clearProblemProcessing(attemptId);
        return;
      }
      if (requestIdRef?.current && requestIdRef.current !== attemptId) {
        useAppStore.getState().clearProblemProcessing(attemptId);
        return;
      }
      if (prepared.request_id && prepared.request_id !== attemptId) {
        useAppStore.getState().clearProblemProcessing(attemptId);
        return;
      }

      if (prepared.status === "needs_selection" || prepared.status === "needs_confirmation") {
        useAppStore.getState().clearProblemProcessing(attemptId);
        onAssistRequired?.(prepared);
        return;
      }

      if (prepared.status === "rejected") {
        const rejectionTitle =
          prepared.reason_code === "DOCX_UNREADABLE_EQUATION"
            ? "Công thức trong tệp Word chưa đọc được"
            : "Chưa trích xuất được đề bài";
        const rejectionDesc = normalizeDisplayBrand(
          prepared.learner_message ||
            "Tệp đính kèm chưa có nội dung đề toán hình học không gian rõ ràng. Em kiểm tra lại tệp hoặc nhập đề trực tiếp.",
        );
        useAppStore.getState().failProblemProcessing(attemptId, {
          problemStatement: initialStatement,
          reasonCode: prepared.reason_code ?? "ATTACHMENT_REJECTED",
          reasonMessage: rejectionDesc,
        });
        useToastStore.getState().showToast({
          id: "composer-refusal",
          tone: "info",
          title: rejectionTitle,
          description: rejectionDesc,
          durationMs: 8500,
        });
        return;
      }

      finalProblemText = prepared.problem_text.trim();
      useAppStore.getState().updateProblemProcessingStatement(attemptId, finalProblemText);
    }

    const result = await analyzeFn(
      { type: "text", content: finalProblemText },
      ctl?.signal,
      undefined,
      attemptId,
    );
    if (ctl?.signal.aborted) {
      useAppStore.getState().clearProblemProcessing(attemptId);
      return;
    }

    if (result.status === "ok") {
      store.loadEnvelope(
        result as SimulationEnvelope,
        undefined,
        finalProblemText,
        attemptId,
      );
      if (useAuthStore.getState().user !== null) {
        void useAuthStore.getState().refresh();
      }
    } else {
      const unsupportedRes = result as AnalysisUnsupported;
      store.loadUnsupported(unsupportedRes, attemptId, finalProblemText);
      const refusalView = describeHomeRefusal(unsupportedRes);
      const description =
        refusalView.hint && !refusalView.body.includes(refusalView.hint)
          ? `${refusalView.body} ${refusalView.hint}`
          : refusalView.body;
      useToastStore.getState().showToast({
        id: "composer-refusal",
        tone: "info",
        title: refusalView.title,
        description,
        durationMs: 8500,
      });
    }
  } catch (err) {
    if ((err as { name?: string } | null)?.name === "AbortError" || ctl?.signal.aborted) {
      useAppStore.getState().clearProblemProcessing(attemptId);
      return;
    }
    const contract = err instanceof AxoClientError ? err.toContract() : null;
    const rawMsg = err instanceof Error ? err.message : String(err);
    const safeMsg = photoReadErrorMessage(err) ?? rawMsg;
    store.setClientFailure(contract);
    store.setAnalysisError(safeMsg);

    const errView = describeComposerError(safeMsg, health, contract);
    if (errView) {
      useToastStore.getState().showToast({
        tone: errView.tone,
        title: errView.title,
        description: errView.description,
        durationMs: 7000,
      });
    }
  } finally {
    if (!abortRef || abortRef.current === ctl) {
      if (abortRef) abortRef.current = null;
      store.setAnalyzing(false);
      lockRef.current = false;
    }
  }
}

let attachmentSeq = 0;
let savedDraftAttachments: ComposerAttachmentItem[] = [];
const draftAttachmentsResetListeners = new Set<() => void>();

function revokePreviewUrl(url: string | undefined) {
  if (url && url.startsWith("blob:") && typeof URL !== "undefined" && typeof URL.revokeObjectURL === "function") {
    URL.revokeObjectURL(url);
  }
}

export function clearSavedDraftAttachments() {
  for (const item of savedDraftAttachments) {
    revokePreviewUrl(item.previewUrl);
  }
  savedDraftAttachments = [];
  for (const listener of draftAttachmentsResetListeners) {
    listener();
  }
}

export interface ExecuteScreenCaptureFlowParams {
  busyRef: { current: boolean };
  onCaptured: (file: File) => void;
  checkSupport?: typeof classifyScreenCaptureSupportError;
  captureFrame?: typeof captureScreenStillFrame;
  classifyError?: typeof classifyScreenCaptureError;
  revokeUrl?: (url: string | undefined) => void;
}

export async function executeScreenCaptureFlow({
  busyRef,
  onCaptured,
  checkSupport = classifyScreenCaptureSupportError,
  captureFrame = captureScreenStillFrame,
  classifyError = classifyScreenCaptureError,
  revokeUrl = revokePreviewUrl,
}: ExecuteScreenCaptureFlowParams): Promise<
  "busy" | "unsupported" | "cancelled" | "error" | "attached"
> {
  if (busyRef.current) return "busy";
  const supportErr = checkSupport();
  if (supportErr) {
    useToastStore.getState().showToast({
      id: "screen-capture-notice",
      tone: "info",
      title: supportErr.title,
      description: supportErr.description,
      durationMs: 5200,
    });
    return "unsupported";
  }

  busyRef.current = true;
  try {
    const captured = await captureFrame();
    useToastStore.getState().dismissToast("screen-capture-notice");
    try {
      onCaptured(captured.file);
    } finally {
      revokeUrl(captured.previewUrl);
    }
    return "attached";
  } catch (err) {
    const classified = classifyError(err);
    if (classified.code === "cancelled") {
      return "cancelled";
    }
    useToastStore.getState().showToast({
      id: "screen-capture-notice",
      tone: "info",
      title: classified.title,
      description: classified.description,
      durationMs: 5500,
    });
    return "error";
  } finally {
    busyRef.current = false;
  }
}

useAppStore.subscribe((state, prevState) => {
  if (
    !state.hasInAppNavigation &&
    state.workspaceTabs.length === 0 &&
    state.problemText === "" &&
    (prevState.hasInAppNavigation || prevState.workspaceTabs.length > 0)
  ) {
    clearSavedDraftAttachments();
  }
});

/**
 * Axo Unified Problem Input Composer:
 * - Nhập văn bản trực tiếp, chụp ảnh đề bài (Camera-First tối giản) hoặc đính kèm tệp (`.png`, `.jpg`, `.jpeg`, `.webp`, `.pdf`, `.docx`).
 * - Nguyên tắc Đính kèm ≠ Xử lý: trước khi bấm `Dựng hình →`, chỉ kiểm tra cục bộ và tạo chip đính kèm (0 lượt gọi AI).
 * - Khi bấm `Dựng hình →`: tự động tách vùng nội dung, đọc PDF/DOCX/OMML, gộp chỉ dẫn gõ tay và chuyển qua Hybrid `/4` → `Scene3D`.
 */
export interface ProblemInputProps {
  initialAttachments?: ComposerAttachmentItem[];
  initialPlusMenuOpen?: boolean;
  initialAllFilesModalOpen?: boolean;
  initialAssistState?: UnifiedAssistState;
  deviceSignals?: CameraDeviceSignals;
  capabilitySignals?: Omit<UploadMenuCapabilitySignals, "deviceSignals">;
}

export function ProblemInput({
  initialAttachments,
  initialPlusMenuOpen = false,
  initialAllFilesModalOpen = false,
  initialAssistState = initialUnifiedAssistState,
  deviceSignals,
  capabilitySignals,
}: ProblemInputProps = {}) {
  const hasExplicitInitialAttachments = initialAttachments !== undefined;
  const menuCaps = resolveUploadMenuCapabilities({
    deviceSignals,
    ...capabilitySignals,
  });
  const showScreenCaptureEntry = menuCaps.showScreenCapture;
  const showCameraEntry = menuCaps.showCamera;
  const visibleMenuCount = menuCaps.visibleActionCount;
  const problemText = useAppStore((s) => s.problemText);
  const setProblemText = useAppStore((s) => s.setProblemText);
  const analyzing = useAppStore((s) => s.analyzing);
  const analysisError = useAppStore((s) => s.analysisError);

  const [health, setHealth] = useState<ServerHealth | null | "loading">("loading");
  const [attachments, setAttachmentsState] = useState<ComposerAttachmentItem[]>(
    () => (hasExplicitInitialAttachments ? initialAttachments : savedDraftAttachments),
  );
  const setAttachments: React.Dispatch<React.SetStateAction<ComposerAttachmentItem[]>> = (
    updater,
  ) => {
    setAttachmentsState((prev) => {
      const next = typeof updater === "function" ? updater(prev) : updater;
      if (!hasExplicitInitialAttachments) {
        savedDraftAttachments = next;
      }
      return next;
    });
  };
  const [plusMenuOpen, setPlusMenuOpen] = useState(initialPlusMenuOpen);
  const [plusPopoverPos, setPlusPopoverPos] = useState<PlusPopoverPosition | null>(null);
  const plusPopoverPosRef = useRef<PlusPopoverPosition | null>(null);
  const plusPopoverSizeRef = useRef<{ width: number; height: number } | null>(null);
  const composerBoxRef = useRef<HTMLDivElement>(null);
  const [allFilesModalOpen, setAllFilesModalOpen] = useState(
    initialAllFilesModalOpen,
  );
  const [previewModalFileId, setPreviewModalFileId] = useState<string | null>(
    null,
  );
  const [previewDownloadUrl, setPreviewDownloadUrl] = useState<string | null>(null);
  const [previewImageError, setPreviewImageError] = useState(false);
  const [pdfPreviewCheck, setPdfPreviewCheck] = useState<"checking" | "invalid" | "unknown">("unknown");
  const [photoDialogOpen, setPhotoDialogOpen] = useState(false);
  const screenCaptureBusyRef = useRef(false);
  const [assist, dispatchAssist] = useReducer(
    unifiedAssistReducer,
    initialAssistState,
  );

  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadImageRef = useRef<HTMLInputElement>(null);
  const cameraImageRef = useRef<HTMLInputElement>(null);
  const textRef = useRef<HTMLTextAreaElement>(null);
  const plusMenuAnchorRef = useRef<HTMLDivElement>(null);
  const plusTriggerRef = useRef<HTMLButtonElement>(null);
  const plusPopoverRef = useRef<HTMLDivElement>(null);
  const filesRowRef = useRef<HTMLDivElement>(null);
  const attachmentsRef = useRef<ComposerAttachmentItem[]>([]);
  const submittingRef = useRef(false);
  const analyzeAbortRef = useRef<AbortController | null>(null);
  const activePrepareRequestIdRef = useRef<string | null>(null);
  const activeSubmitPromiseRef = useRef<Promise<void> | null>(null);
  const cancellingRef = useRef(false);
  const [cancelling, setCancelling] = useState(false);
  const filesDragRef = useRef<{ active: boolean; startX: number; startScrollLeft: number; moved: boolean }>({
    active: false,
    startX: 0,
    startScrollLeft: 0,
    moved: false,
  });
  const suppressCardClickRef = useRef(false);
  const modalOriginFocusRef = useRef<HTMLElement | null>(null);
  const pendingFocusAfterRemoveRef = useRef<{ targetId: string | null; fromModal: boolean } | null>(null);
  const allFilesListRef = useRef<HTMLDivElement>(null);
  const [filesOverflow, setFilesOverflow] = useState<{ left: boolean; right: boolean }>({
    left: false,
    right: false,
  });
  const [filesScroll, setFilesScroll] = useState({ value: 0, max: 0, native: false, thumb: 0 });
  const [isMultilineWrapped, setIsMultilineWrapped] = useState(false);
  const [isShiftEnterMultiline, setIsShiftEnterMultiline] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const hasNewline = problemText.includes("\n");
  const composerExpanded = isExpanded;
  const isMultiline =
    attachments.length > 0 ||
    isMultilineWrapped ||
    hasNewline ||
    isShiftEnterMultiline ||
    composerExpanded;
  const composerLineMode = "two-tier" as const;

  useEffect(() => {
    attachmentsRef.current = attachments;
  }, [attachments]);

  useEffect(() => {
    const item = attachments.find((attachment) => attachment.id === previewModalFileId);
    if (!item || !canPreviewAttachment(item) || item.kind === "image" || typeof URL.createObjectURL !== "function") {
      setPreviewDownloadUrl(null);
      return;
    }
    const url = URL.createObjectURL(item.file);
    setPreviewDownloadUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [previewModalFileId, attachments]);

  useEffect(() => {
    const item = attachments.find((attachment) => attachment.id === previewModalFileId);
    if (!item || item.kind !== "pdf") { setPdfPreviewCheck("unknown"); return; }
    let cancelled = false;
    setPdfPreviewCheck("checking");
    void isClearlyInvalidPdf(item.file).then((invalid) => {
      if (!cancelled) setPdfPreviewCheck(invalid ? "invalid" : "unknown");
    }, () => { if (!cancelled) setPdfPreviewCheck("unknown"); });
    return () => { cancelled = true; };
  }, [previewModalFileId, attachments]);

  const isPreviewModalOpen = Boolean(previewModalFileId);

  useEffect(() => {
    setPreviewImageError(false);
  }, [previewModalFileId]);

  useEffect(() => {
    if (!isPreviewModalOpen) return;
    modalOriginFocusRef.current = document.activeElement as HTMLElement | null;
    document.getElementById("btn-close-file-modal")?.focus({ preventScroll: true });
    const onModalKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;
      const modal = document.getElementById("composer-single-file-modal");
      const controls = Array.from(modal?.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], [tabindex="0"]') ?? []);
      if (!controls.length) return;
      const index = controls.indexOf(document.activeElement as HTMLElement);
      if (event.shiftKey && index <= 0) { event.preventDefault(); controls[controls.length - 1]?.focus({ preventScroll: true }); }
      else if (!event.shiftKey && (index < 0 || index === controls.length - 1)) { event.preventDefault(); controls[0]?.focus({ preventScroll: true }); }
    };
    document.addEventListener("keydown", onModalKeyDown);
    return () => {
      document.removeEventListener("keydown", onModalKeyDown);
      const origin = modalOriginFocusRef.current;
      modalOriginFocusRef.current = null;
      if (origin && origin.isConnected && typeof origin.focus === "function") {
        origin.focus({ preventScroll: true });
      }
    };
  }, [isPreviewModalOpen]);

  function syncFilesOverflow(el: HTMLDivElement | null) {
    if (!el) {
      setFilesOverflow((prev) =>
        prev.left || prev.right ? { left: false, right: false } : prev,
      );
      return;
    }
    const nextLeft = el.scrollLeft > 2;
    const nextRight = el.scrollLeft + el.clientWidth < el.scrollWidth - 2;
    const max = Math.max(0, el.scrollWidth - el.clientWidth);
    const native = el.offsetHeight - el.clientHeight > 1;
    const thumb = Math.max(20, Math.round(el.clientWidth * el.clientWidth / el.scrollWidth));
    setFilesScroll((prev) => prev.value === el.scrollLeft && prev.max === max && prev.native === native && prev.thumb === thumb ? prev : { value: el.scrollLeft, max, native, thumb });
    setFilesOverflow((prev) =>
      prev.left === nextLeft && prev.right === nextRight
        ? prev
        : { left: nextLeft, right: nextRight },
    );
  }

  useEffect(() => {
    const el = filesRowRef.current;
    syncFilesOverflow(el);
    if (!el) return;
    let ro: ResizeObserver | null = null;
    if (typeof ResizeObserver !== "undefined") {
      ro = new ResizeObserver(() => syncFilesOverflow(filesRowRef.current));
      ro.observe(el);
    }
    const onWinResize = () => syncFilesOverflow(filesRowRef.current);
    if (typeof window !== "undefined") {
      window.addEventListener("resize", onWinResize);
    }
    return () => {
      ro?.disconnect();
      if (typeof window !== "undefined") {
        window.removeEventListener("resize", onWinResize);
      }
    };
  }, [attachments.length]);

  // Huỷ request đang chạy khi tháo component; chỉ thu hồi objectURL nếu là danh sách đính kèm cục bộ của test (đính kèm nháp của học sinh được giữ nguyên khi chuyển tab).
  useEffect(() => {
    if (hasExplicitInitialAttachments) return;
    const onClearDraft = () => {
      setAttachmentsState([]);
      dispatchAssist({ type: "reset" });
      activePrepareRequestIdRef.current = null;
    };
    draftAttachmentsResetListeners.add(onClearDraft);
    return () => {
      draftAttachmentsResetListeners.delete(onClearDraft);
    };
  }, [hasExplicitInitialAttachments]);

  useEffect(() => {
    return () => {
      analyzeAbortRef.current?.abort();
      if (hasExplicitInitialAttachments) {
        for (const item of attachmentsRef.current) {
          revokePreviewUrl(item.previewUrl);
        }
      }
    };
  }, [hasExplicitInitialAttachments]);

  useEffect(() => {
    let cancelled = false;
    fetchHealth().then((h) => {
      if (!cancelled) setHealth(h);
    });
    return () => {
      cancelled = true;
    };
  }, [analyzing]);

  // Tự đóng modal Tất cả tệp hoặc modal xem trước nếu người dùng xóa tệp hoặc tệp không hỗ trợ xem trước.
  useEffect(() => {
    if (attachments.length === 0 && allFilesModalOpen) {
      setAllFilesModalOpen(false);
    }
    const previewTarget = previewModalFileId
      ? attachments.find((a) => a.id === previewModalFileId) ?? null
      : null;
    if (previewModalFileId && (!previewTarget || !canPreviewAttachment(previewTarget))) {
      setPreviewModalFileId(null);
    }
  }, [attachments, allFilesModalOpen, previewModalFileId]);

  useEffect(() => {
    const pending = pendingFocusAfterRemoveRef.current;
    if (!pending) return;
    pendingFocusAfterRemoveRef.current = null;
    if (typeof document === "undefined") return;
    if (pending.targetId) {
      if (pending.fromModal && allFilesModalOpen) {
        const modalBtn =
          document.querySelector<HTMLElement>(
            `[data-modal-remove-file-id="${pending.targetId}"]`,
          ) ??
          document.querySelector<HTMLElement>(
            `[data-modal-preview-file-id="${pending.targetId}"]`,
          );
        modalBtn?.focus({ preventScroll: true });
        return;
      }
      const stripCard = document.querySelector<HTMLElement>(
        `.file-preview-card[data-file-id="${pending.targetId}"]`,
      );
      const nextRemoveBtn = stripCard?.querySelector<HTMLElement>(".file-card-remove") ?? null;
      if (nextRemoveBtn && stripCard) {
        stripCard.scrollIntoView?.({ block: "nearest", inline: "nearest" });
        if (filesRowRef.current) syncFilesOverflow(filesRowRef.current);
        nextRemoveBtn.focus({ preventScroll: true });
        return;
      }
    }
    textRef.current?.focus({ preventScroll: true });
  }, [attachments, allFilesModalOpen]);

  function readCurrentPlusPopoverPos(): {
    pos: PlusPopoverPosition;
    outOfView: boolean;
  } | null {
    const triggerEl = plusTriggerRef.current;
    if (!triggerEl || typeof window === "undefined") return null;

    const triggerRect = triggerEl.getBoundingClientRect();
    const inlineZoom = document.documentElement.style.zoom;
    const cssZoom = inlineZoom ? parseFloat(inlineZoom) || 1 : 1;
    const vv = window.visualViewport;
    const viewportWidth = vv ? vv.width * (cssZoom !== 1 ? cssZoom : 1) : window.innerWidth;
    const viewportHeight = vv ? vv.height * (cssZoom !== 1 ? cssZoom : 1) : window.innerHeight;

    let minVisibleTop = 0;
    if (triggerRect.top < 80) {
      const navEl = document.querySelector(".nav-bar");
      minVisibleTop = navEl ? Math.max(0, navEl.getBoundingClientRect().bottom) : 0;
    }
    const outOfView = triggerRect.bottom <= minVisibleTop || triggerRect.top >= viewportHeight;

    const popoverEl = plusPopoverRef.current;
    const rawOffsetW = popoverEl ? popoverEl.offsetWidth : 0;
    const rawOffsetH = popoverEl ? popoverEl.offsetHeight : 0;
    if (rawOffsetW > 0 && rawOffsetH > 0) {
      plusPopoverSizeRef.current = { width: rawOffsetW, height: rawOffsetH };
    }
    const baseW =
      plusPopoverSizeRef.current?.width ?? 224;
    const baseH =
      plusPopoverSizeRef.current?.height ??
      (visibleMenuCount >= 3 ? 124 : visibleMenuCount === 2 ? 86 : 48);

    const avoidRects: CollisionRect[] = [];
    const heroTitleEl = document.querySelector(".home-hero-title");
    if (heroTitleEl) {
      const hr = heroTitleEl.getBoundingClientRect();
      if (hr.width > 0 && hr.height > 0) {
        avoidRects.push({ top: hr.top, bottom: hr.bottom, left: hr.left, right: hr.right });
      }
    }
    const filesWrapEl =
      filesRowRef.current ?? document.getElementById("composer-files-wrap");
    if (filesWrapEl) {
      const fr = filesWrapEl.getBoundingClientRect();
      if (fr.width > 0 && fr.height > 0) {
        avoidRects.push({ top: fr.top, bottom: fr.bottom, left: fr.left, right: fr.right });
      }
    }
    const taEl = textRef.current;
    if (taEl) {
      const taRect = taEl.getBoundingClientRect();
      if (taRect.width > 0 && taRect.height > 0) {
        const rawText = taEl.value || problemText || "";
        const trimmed = rawText.trim();
        if (trimmed.length === 0) {
          const placeholderH = Math.min(taRect.height, 26 * cssZoom);
          const placeholderW = Math.min(taRect.width, 280 * cssZoom);
          avoidRects.push({
            top: taRect.top,
            bottom: taRect.top + placeholderH,
            left: taRect.left,
            right: taRect.left + placeholderW,
          });
        } else {
          const charsPerLine = Math.max(
            20,
            Math.floor((taRect.width / cssZoom - 32) / 8.2),
          );
          const visualLines = rawText
            .split("\n")
            .reduce(
              (acc, line) => acc + Math.max(1, Math.ceil(Math.max(1, line.length) / charsPerLine)),
              0,
            );
          const lineHeightPx = 24 * cssZoom;
          const occupiedH = Math.min(
            taRect.height,
            Math.max(28 * cssZoom, visualLines * lineHeightPx + 6 * cssZoom),
          );
          avoidRects.push({
            top: taRect.top,
            bottom: taRect.top + occupiedH,
            left: taRect.left,
            right: taRect.right,
          });
        }
      }
    }

    const pos = computePlusPopoverPosition({
      triggerRect,
      menuWidth: baseW * cssZoom,
      menuHeight: baseH * cssZoom,
      viewportWidth,
      viewportHeight,
      cssZoom,
      preferredPlacement: "top",
      avoidRects,
    });
    return { pos, outOfView };
  }

  function applyPlusPopoverPosIfChanged(next: PlusPopoverPosition) {
    const prev = plusPopoverPosRef.current;
    if (
      prev &&
      prev.placement === next.placement &&
      prev.maxHeight === next.maxHeight &&
      prev.collisionFlipped === next.collisionFlipped &&
      Math.abs(prev.left - next.left) < 0.5 &&
      Math.abs(prev.top - next.top) < 0.5
    ) {
      return;
    }
    plusPopoverPosRef.current = next;
    setPlusPopoverPos(next);
  }

  // Định vị sẵn vị trí nút `+` sau khi mount hoặc khi chuyển trạng thái 1 dòng / nhiều dòng / mở rộng để lần mở đầu tiên đạt tốc độ tức thì (1 DOM mutation) giống hệt các lần mở tiếp theo.
  useEffect(() => {
    const measured = readCurrentPlusPopoverPos();
    if (measured && !measured.outOfView) {
      applyPlusPopoverPosIfChanged(measured.pos);
    }
  }, [visibleMenuCount, isMultiline, isExpanded, problemText, attachments.length]);

  // Định vị menu `+` dựa trên không gian thực tế của viewport và chống va chạm nội dung (ưu tiên mở lên trên khi vùng dưới trống ở chế độ Expand, tự động lật xuống dưới nút `+` khi chạm tiêu đề hoặc chữ trong vùng nhập).
  useIsomorphicLayoutEffect(() => {
    if (!plusMenuOpen) return;

    const syncPopoverPosition = () => {
      const measured = readCurrentPlusPopoverPos();
      if (!measured) return;
      if (measured.outOfView) {
        setPlusMenuOpen(false);
        return;
      }
      applyPlusPopoverPosIfChanged(measured.pos);
    };

    syncPopoverPosition();

    let ro: ResizeObserver | null = null;
    if (typeof ResizeObserver !== "undefined" && composerBoxRef.current) {
      ro = new ResizeObserver(() => syncPopoverPosition());
      ro.observe(composerBoxRef.current);
    }

    window.addEventListener("resize", syncPopoverPosition);
    window.addEventListener("scroll", syncPopoverPosition, { passive: true, capture: true });
    const vv = window.visualViewport;
    vv?.addEventListener("resize", syncPopoverPosition);
    vv?.addEventListener("scroll", syncPopoverPosition);

    return () => {
      ro?.disconnect();
      window.removeEventListener("resize", syncPopoverPosition);
      window.removeEventListener("scroll", syncPopoverPosition, true);
      vv?.removeEventListener("resize", syncPopoverPosition);
      vv?.removeEventListener("scroll", syncPopoverPosition);
    };
  }, [plusMenuOpen, visibleMenuCount, isMultiline, isExpanded, problemText, attachments.length]);

  // Đóng menu `+`, modal Tất cả tệp hoặc modal xem trước tệp khi bấm ra ngoài hoặc nhấn Escape.
  useEffect(() => {
    if (!plusMenuOpen && !allFilesModalOpen && !previewModalFileId) return;

    function handleMouseDown(e: MouseEvent) {
      const target = e.target as Node | null;
      if (
        plusMenuOpen &&
        plusMenuAnchorRef.current &&
        target &&
        !plusMenuAnchorRef.current.contains(target)
      ) {
        setPlusMenuOpen(false);
      }
    }

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        if (previewModalFileId) {
          setPreviewModalFileId(null);
        } else if (allFilesModalOpen) {
          setAllFilesModalOpen(false);
        } else if (plusMenuOpen) {
          e.preventDefault();
          const activeEl = document.activeElement;
          const focusWasInsidePopover =
            activeEl !== null && Boolean(plusPopoverRef.current?.contains(activeEl));
          setPlusMenuOpen(false);
          if (focusWasInsidePopover) {
            plusTriggerRef.current?.focus();
          }
        }
      }
    }

    document.addEventListener("mousedown", handleMouseDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleMouseDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [plusMenuOpen, allFilesModalOpen, previewModalFileId]);

  const readyAttachments = attachments.filter(
    (a) => a.status !== "loading" && a.status !== "error",
  );
  const isUploadingAny = attachments.some((a) => a.status === "loading" || a.status === "error");
  const canSubmit = canSubmitComposer(
    problemText,
    readyAttachments.length,
    analyzing,
    isUploadingAny,
  );

  function syncTextareaHeight(
    el: HTMLTextAreaElement | null,
    opts?: { expanded?: boolean; shiftMultiline?: boolean; hasAttachments?: boolean },
  ) {
    if (!el) return;
    const expandedMode = opts?.expanded ?? composerExpanded;
    const shiftMode = opts?.shiftMultiline ?? isShiftEnterMultiline;
    const val = el.value ?? "";
    const hasNl = val.includes("\n");

    const prevInlineH = parseFloat(el.style.height || "") || 0;

    if (val.length === 0 && !expandedMode && !shiftMode) {
      // V9.4 Two-tier default: 48px (2 × 24px lines) comfortable input space from empty state
      setIsMultilineWrapped(false);
      el.style.overflowY = "hidden";
      if (prevInlineH > 0 && Math.abs(prevInlineH - 48) >= 1) {
        const prevTransition = el.style.transition;
        el.style.transition = "none";
        el.style.height = `${prevInlineH}px`;
        void el.offsetHeight;
        el.style.transition = prevTransition;
        el.style.height = "48px";
      } else {
        el.style.height = "48px";
      }
      return;
    }

    const prevTransition = el.style.transition;
    const prevMinH = el.style.minHeight;
    el.style.transition = "none";
    el.style.minHeight = "0px";
    el.style.height = "0px";
    const rawScrollH = el.scrollHeight;
    el.style.minHeight = prevMinH;

    let wrapped = hasNl;
    let measured = rawScrollH;
    if (rawScrollH > 0) {
      wrapped = hasNl || rawScrollH > 30;
    } else {
      const explicitLines = val.split("\n").length;
      const approxWrappedLines = Math.ceil(val.length / 68);
      const totalLines = Math.max(explicitLines, approxWrappedLines);
      wrapped = totalLines > 1;
      const effectiveLines = Math.max(totalLines, shiftMode ? 2 : 1);
      measured = Math.max(48, effectiveLines * 24);
    }

    setIsMultilineWrapped(wrapped);

    if (!expandedMode) {
      const nextH = Math.min(Math.max(measured, 48), 192);
      el.style.overflowY = measured > 192 ? "auto" : "hidden";
      if (prevInlineH > 0 && Math.abs(prevInlineH - nextH) >= 1) {
        el.style.height = `${prevInlineH}px`;
        void el.offsetHeight;
        el.style.transition = prevTransition;
        el.style.height = `${nextH}px`;
      } else {
        el.style.height = `${nextH}px`;
        void el.offsetHeight;
        el.style.transition = prevTransition;
      }
      return;
    }

    const nextH = Math.min(Math.max(measured, 216), 312);
    el.style.overflowY = measured > 312 ? "auto" : "hidden";
    if (prevInlineH > 0 && Math.abs(prevInlineH - nextH) >= 1) {
      el.style.height = `${prevInlineH}px`;
      void el.offsetHeight;
      el.style.transition = prevTransition;
      el.style.height = `${nextH}px`;
    } else {
      el.style.height = `${nextH}px`;
      void el.offsetHeight;
      el.style.transition = prevTransition;
    }
  }

  useIsomorphicLayoutEffect(() => {
    const isCleanEmpty = problemText.length === 0 && attachments.length === 0;
    if (isCleanEmpty && isShiftEnterMultiline) {
      setIsShiftEnterMultiline(false);
    }
    syncTextareaHeight(textRef.current, {
      expanded: composerExpanded,
      shiftMultiline: isCleanEmpty ? false : isShiftEnterMultiline,
      hasAttachments: attachments.length > 0,
    });
  }, [
    problemText,
    composerLineMode,
    composerExpanded,
    attachments.length,
    isShiftEnterMultiline,
  ]);

  useEffect(() => {
    const el = textRef.current;
    if (!el) return;
    syncTextareaHeight(el);
    const onResize = () => syncTextareaHeight(textRef.current);
    if (typeof window !== "undefined") {
      window.addEventListener("resize", onResize);
    }
    let lastWidth = el.clientWidth;
    let ro: ResizeObserver | null = null;
    if (typeof ResizeObserver !== "undefined") {
      ro = new ResizeObserver(() => {
        const cur = textRef.current;
        if (!cur) return;
        if (cur.clientWidth !== lastWidth) {
          lastWidth = cur.clientWidth;
          syncTextareaHeight(cur);
        }
      });
      ro.observe(el);
    }
    if (typeof document !== "undefined" && document.fonts?.ready) {
      void document.fonts.ready.then(() => syncTextareaHeight(textRef.current));
    }
    return () => {
      if (typeof window !== "undefined") {
        window.removeEventListener("resize", onResize);
      }
      ro?.disconnect();
    };
  }, []);

  function onChangeText(e: React.ChangeEvent<HTMLTextAreaElement>) {
    const nextVal = e.target.value;
    setProblemText(nextVal);
    if (!nextVal.includes("\n") && isShiftEnterMultiline) {
      setIsShiftEnterMultiline(false);
    }
    if (nextVal.length === 0 && attachments.length === 0 && isExpanded) {
      setIsExpanded(false);
    }
    const st = useAppStore.getState();
    if (st.unsupported) st.clearUnsupported();
    if (st.analysisError && !/lượt mô phỏng thử/.test(st.analysisError)) {
      st.setAnalysisError(null);
    }
  }

  function onPasteText(e: React.ClipboardEvent<HTMLTextAreaElement>) {
    const pasted = e.clipboardData?.getData("text/plain") ?? "";
    if (pasted.includes("\n") || pasted.length > 60) {
      setIsMultilineWrapped(true);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key !== "Enter") return;

    const nativeEvt = e.nativeEvent as unknown as {
      isComposing?: boolean;
      keyCode?: number;
    } | null;
    const isComposing =
      Boolean(nativeEvt?.isComposing) ||
      (e as unknown as { isComposing?: boolean }).isComposing === true ||
      nativeEvt?.keyCode === 229 ||
      (e as unknown as { keyCode?: number }).keyCode === 229;

    if (isComposing) return;

    if (e.shiftKey && !analyzing) {
      setIsShiftEnterMultiline(true);
    }

    if (e.shiftKey) {
      if (analyzing) e.preventDefault();
      return;
    }

    e.preventDefault();
    if (canSubmit) {
      if (!cancelling) void onAnalyze();
    }
  }

  function addFilesToComposer(allPicked: File[], opts?: { source?: "camera" | "upload" | "paste" }) {
    if (allPicked.length === 0) return;

    const baseExisting = attachmentsRef.current;
    const workingExisting = baseExisting.map((a) => ({ name: a.name, size: a.size }));
    const nextItems: ComposerAttachmentItem[] = [];

    for (const picked of allPicked) {
      const check = validateComposerFile(picked, workingExisting);
      if (!check.ok) {
        useToastStore.getState().showToast({
          tone: "error",
          title:
            check.code === "heic_unsupported"
              ? "Chưa hỗ trợ định dạng HEIC/HEIF"
              : "Không thể đính kèm tệp",
          description: check.reason,
        });
        continue;
      }

      let previewUrl: string | undefined;
      if (
        check.kind === "image" &&
        typeof URL !== "undefined" &&
        typeof URL.createObjectURL === "function"
      ) {
        try {
          previewUrl = URL.createObjectURL(picked);
        } catch {
          previewUrl = undefined;
        }
      }

      attachmentSeq += 1;
      nextItems.push({
        id: `att-${Date.now()}-${attachmentSeq}`,
        file: picked,
        name: picked.name,
        size: picked.size,
        sizeFormatted: formatAttachmentSize(picked.size),
        ext: check.ext,
        kind: check.kind,
        previewUrl,
        status: check.kind === "pdf" ? "loading" : "ready",
        source: opts?.source ?? "upload",
      });
      workingExisting.push({ name: picked.name, size: picked.size });
    }

    if (nextItems.length > 0) {
      dispatchAssist({ type: "reset" });
      setAttachments((prev) => [...prev, ...nextItems]);
      for (const item of nextItems) {
        if (item.kind !== "pdf") continue;
        void isClearlyInvalidPdf(item.file).then(async (invalid) => {
          setAttachments((prev) => prev.map((current) => current.id === item.id
            ? { ...current, status: invalid ? "error" : "ready", errorMessage: invalid ? "Tệp không có chữ ký PDF hợp lệ." : undefined }
            : current));
          if (invalid) return;
          const thumbUrl = await renderPdfFirstPageThumbnail(item.file);
          if (!thumbUrl) return;
          setAttachments((prev) =>
            prev.some((c) => c.id === item.id)
              ? prev.map((current) => current.id === item.id ? { ...current, previewUrl: thumbUrl } : current)
              : prev,
          );
        }, () => {
          setAttachments((prev) => prev.map((current) => current.id === item.id
            ? { ...current, status: "error", errorMessage: "Không thể đọc tệp PDF." }
            : current));
        });
      }
    }
  }

  function onPickFiles(e: React.ChangeEvent<HTMLInputElement>) {
    const list = e.target.files ? Array.from(e.target.files) : [];
    addFilesToComposer(list);
    e.target.value = "";
  }

  function onPickImage(e: React.ChangeEvent<HTMLInputElement>) {
    const pickedList = e.target.files ? Array.from(e.target.files) : [];
    if (pickedList.length > 0) {
      addFilesToComposer(pickedList, { source: e.currentTarget === cameraImageRef.current ? "camera" : "upload" });
    }
    e.target.value = "";
  }

  function removeAttachment(id: string) {
    activePrepareRequestIdRef.current = null;
    dispatchAssist({ type: "reset" });
    const currentList = attachmentsRef.current;
    const removedIdx = currentList.findIndex((item) => item.id === id);
    if (typeof document !== "undefined" && removedIdx >= 0) {
      const activeEl = document.activeElement as HTMLElement | null;
      const inStripCard = Boolean(
        activeEl && activeEl.closest(`.file-preview-card[data-file-id="${id}"]`),
      );
      const inAllFilesRow = Boolean(
        activeEl &&
          (activeEl.getAttribute("data-modal-remove-file-id") === id ||
            activeEl.closest(`.all-files-modal-item[data-modal-file-id="${id}"]`)),
      );
      let isKeyboardOrigin = true;
      try {
        isKeyboardOrigin = activeEl ? activeEl.matches(":focus-visible") : false;
      } catch {
        isKeyboardOrigin = true;
      }
      if ((inStripCard || inAllFilesRow) && isKeyboardOrigin) {
        const remaining = currentList.filter((item) => item.id !== id);
        const nextTarget =
          remaining.length > 0
            ? remaining[Math.min(removedIdx, remaining.length - 1)]?.id ?? null
            : null;
        pendingFocusAfterRemoveRef.current = { targetId: nextTarget, fromModal: inAllFilesRow };
      }
    }
    setAttachments((prev) => {
      const target = prev.find((item) => item.id === id);
      revokePreviewUrl(target?.previewUrl);
      return prev.filter((item) => item.id !== id);
    });
  }

  function closePhotoDialog() {
    setPhotoDialogOpen(false);
  }

  async function startScreenCapture() {
    await executeScreenCaptureFlow({
      busyRef: screenCaptureBusyRef,
      onCaptured: (file) => addFilesToComposer([file]),
    });
  }

  async function onAnalyze(opts?: {
    selectedCandidateId?: string;
    overridePreparedText?: string;
  }) {
    if (cancellingRef.current) return;
    dispatchAssist({ type: "reset" });
    const runPromise = runComposerSubmit({
      canSubmit: Boolean(opts?.overridePreparedText) || canSubmit,
      lockRef: submittingRef,
      abortRef: analyzeAbortRef,
      requestIdRef: activePrepareRequestIdRef,
      problemText,
      attachment: readyAttachments[0] ?? null,
      attachments: readyAttachments,
      health,
      selectedCandidateId: opts?.selectedCandidateId,
      overridePreparedText: opts?.overridePreparedText,
      onAssistRequired: (response) => {
        dispatchAssist({ type: "from-prepare", response });
      },
    });
    activeSubmitPromiseRef.current = runPromise;
    try {
      await runPromise;
    } finally {
      if (activeSubmitPromiseRef.current === runPromise) {
        activeSubmitPromiseRef.current = null;
        cancellingRef.current = false;
        setCancelling(false);
      }
    }
  }

  function handleStopAnalyze() {
    if (!analyzing || cancellingRef.current) return;
    cancellingRef.current = true;
    setCancelling(true);
    cancelComposerSubmit(submittingRef, analyzeAbortRef, activePrepareRequestIdRef);
    const pending = activeSubmitPromiseRef.current;
    if (pending) {
      void pending.finally(() => {
        cancellingRef.current = false;
        setCancelling(false);
      });
    } else {
      queueMicrotask(() => {
        cancellingRef.current = false;
        setCancelling(false);
      });
    }
  }

  function onSelectAssistCandidate(candidateId: string) {
    void onAnalyze({ selectedCandidateId: candidateId });
  }

  function onSubmitConfirmedAssist() {
    if (!canConfirmAssistText(assist)) return;
    void onAnalyze({ overridePreparedText: assist.draftText });
  }

  const serverStatus =
    health === null ? (
      <span className="composer-sr-only">
        Máy chủ phân tích chưa chạy — vẫn dùng được các mô phỏng mẫu bên dưới
      </span>
    ) : health !== "loading" && !health.hasKey ? (
      <span className="composer-sr-only">
        Máy chủ thiếu khóa AI — vẫn dùng được các mô phỏng mẫu bên dưới
      </span>
    ) : null;

  return (
    <div
      className={`composer-hero${
        showCameraEntry ? " has-camera-item" : ""
      }`}
    >
      <div
        ref={composerBoxRef}
        className={`composer-card composer-box home-composer-box is-two-tier${analyzing ? " is-busy" : ""}${
          attachments.length > 0 ? " has-attachments" : ""
        }${isMultiline ? " is-multiline" : ""}${
          isExpanded ? " is-expanded" : ""
        }`}
        id="home-composer-box"
        data-composer-layout={composerLineMode}
        data-composer-multiline={isMultiline ? "true" : "false"}
        data-composer-expanded={composerExpanded ? "true" : "false"}
      >
        {isMultiline && (
          <button
            type="button"
            id="btn-composer-expand"
            className={`btn-composer-expand${isExpanded ? " is-active" : ""}`}
            onMouseDown={(e) => {
              e.preventDefault();
            }}
            onClick={() => {
              const el = textRef.current;
              const selStart = el?.selectionStart ?? null;
              const selEnd = el?.selectionEnd ?? null;
              const next = !isExpanded;
              setIsExpanded(next);
              const keepShiftMode = next
                ? isShiftEnterMultiline
                : problemText.includes("\n") && isShiftEnterMultiline;
              if (!next && !problemText.includes("\n")) {
                setIsShiftEnterMultiline(false);
              }
              syncTextareaHeight(el, {
                expanded: next,
                shiftMultiline: keepShiftMode,
              });
              requestAnimationFrame(() => {
                syncTextareaHeight(textRef.current, {
                  expanded: next,
                  shiftMultiline: keepShiftMode,
                });
                const measured = readCurrentPlusPopoverPos();
                if (measured && !measured.outOfView) {
                  applyPlusPopoverPosIfChanged(measured.pos);
                }
                if (textRef.current) {
                  textRef.current.focus();
                  if (selStart !== null && selEnd !== null) {
                    try {
                      textRef.current.setSelectionRange(selStart, selEnd);
                    } catch {
                      /* ignore if unsupported */
                    }
                  }
                }
              });
            }}
            disabled={analyzing}
            aria-expanded={isExpanded}
            aria-label={isExpanded ? "Thu gọn khung nhập" : "Mở rộng khung nhập"}
            title={isExpanded ? "Thu gọn khung nhập" : "Mở rộng khung nhập"}
          >
            {isExpanded ? (
              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.85"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ overflow: "visible", display: "block" }}
                data-expand-icon="collapse"
                aria-hidden="true"
              >
                <polyline points="4 14 10 14 10 20" />
                <polyline points="20 10 14 10 14 4" />
                <line x1="14" y1="10" x2="21" y2="3" />
                <line x1="3" y1="21" x2="10" y2="14" />
              </svg>
            ) : (
              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.85"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ overflow: "visible", display: "block" }}
                data-expand-icon="expand"
                aria-hidden="true"
              >
                <polyline points="15 3 21 3 21 9" />
                <polyline points="9 21 3 21 3 15" />
                <line x1="21" y1="3" x2="14" y2="10" />
                <line x1="3" y1="21" x2="10" y2="14" />
              </svg>
            )}
          </button>
        )}
        <input
          ref={fileInputRef}
          id="home-file-input"
          type="file"
          accept={COMPOSER_ACCEPT}
          multiple
          onChange={onPickFiles}
          style={{ display: "none" }}
        />
        <input
          ref={cameraImageRef}
          type="file"
          accept={IMAGE_ACCEPT}
          capture="environment"
          onChange={onPickImage}
          style={{ display: "none" }}
        />
        <input
          ref={uploadImageRef}
          type="file"
          accept={IMAGE_ACCEPT}
          multiple
          onChange={onPickImage}
          style={{ display: "none" }}
        />

        {attachments.length > 0 && (
          <div
            className="composer-files-wrap"
            id="composer-files-wrap"
            aria-label="Danh sách tệp đính kèm"
          >
            <div
              className={`composer-files-scroll-shell${filesOverflow.left ? " has-overflow-left" : ""}${filesOverflow.right ? " has-overflow-right" : ""}`}
              id="composer-files-scroll-shell"
            >
              <div
                ref={filesRowRef}
                className="composer-files-row"
                id="composer-files-row"
                role="region"
                aria-label="Dải tệp đính kèm ngang"
                tabIndex={filesOverflow.left || filesOverflow.right ? 0 : undefined}
                onScroll={(e) => syncFilesOverflow(e.currentTarget)}
                onPointerDown={(e) => {
                  if (e.pointerType !== "mouse" || e.button !== 0) return;
                  if ((e.target as HTMLElement | null)?.closest(".file-card-remove")) return;
                  const el = e.currentTarget;
                  if (el.scrollWidth <= el.clientWidth) return;
                  filesDragRef.current = {
                    active: true,
                    startX: e.clientX,
                    startScrollLeft: el.scrollLeft,
                    moved: false,
                  };
                }}
                onPointerMove={(e) => {
                  const st = filesDragRef.current;
                  if (!st.active) return;
                  const dx = e.clientX - st.startX;
                  if (Math.abs(dx) > 6) {
                    st.moved = true;
                  }
                  if (st.moved) {
                    const el = e.currentTarget;
                    el.scrollLeft = st.startScrollLeft - dx;
                    syncFilesOverflow(el);
                  }
                }}
                onPointerUp={() => {
                  if (filesDragRef.current.moved) {
                    suppressCardClickRef.current = true;
                    setTimeout(() => {
                      suppressCardClickRef.current = false;
                    }, 0);
                  }
                  filesDragRef.current.active = false;
                  filesDragRef.current.moved = false;
                }}
                onPointerCancel={() => {
                  filesDragRef.current.active = false;
                  filesDragRef.current.moved = false;
                }}
                onKeyDown={(e) => {
                  const el = e.currentTarget;
                  if (e.key === "ArrowRight" && el.scrollWidth > el.clientWidth) {
                    e.preventDefault();
                    el.scrollLeft += 140;
                    syncFilesOverflow(el);
                  } else if (e.key === "ArrowLeft" && el.scrollWidth > el.clientWidth) {
                    e.preventDefault();
                    el.scrollLeft -= 140;
                    syncFilesOverflow(el);
                  }
                }}
                onWheel={(e) => {
                  const el = e.currentTarget;
                  if (Math.abs(e.deltaY) > Math.abs(e.deltaX) && el.scrollWidth > el.clientWidth) {
                    el.scrollLeft += e.deltaY;
                    syncFilesOverflow(el);
                  }
                }}
                onFocus={(e) => {
                  const target = e.target as HTMLElement | null;
                  if (!target || target === e.currentTarget) return;
                  let isKeyboardFocus = false;
                  try {
                    isKeyboardFocus = target.matches(":focus-visible");
                  } catch {
                    isKeyboardFocus = false;
                  }
                  if (!isKeyboardFocus) return;
                  const card = target.closest(".file-preview-card") as HTMLElement | null;
                  if (card && typeof card.scrollIntoView === "function") {
                    card.scrollIntoView({ block: "nearest", inline: "nearest" });
                    syncFilesOverflow(e.currentTarget);
                  }
                }}
              >
                {attachments.map((att) => {
                  const { stem, extWithDot } = splitAttachmentName(att.name);
                  const extBadge = (att.ext.replace(".", "") || att.kind).toUpperCase();
                  const isAttLoading = att.status === "loading";
                  const isAttError = att.status === "error";
                  const isPreviewable = canPreviewAttachment(att);
                  const hasCardThumb = Boolean(att.previewUrl) && !isAttLoading && !isAttError;
                  const badgeClass = isAttLoading
                    ? " badge-loading"
                    : isAttError
                      ? " badge-error"
                      : att.kind === "document"
                        ? " badge-docx"
                        : att.kind === "pdf" || att.ext.toLowerCase() === ".pdf"
                          ? " badge-pdf"
                          : att.kind === "code"
                            ? " badge-code"
                            : "";
                  const subText = isAttLoading
                    ? `Đang kiểm tra · ${att.sizeFormatted}`
                    : isAttError
                      ? att.errorMessage || "Lỗi tải tệp"
                      : `${extBadge} · ${att.sizeFormatted}`;
                  return (
                    <div
                      key={att.id}
                      className={`file-preview-card${hasCardThumb ? " has-thumb" : ""}${isAttLoading ? " is-loading" : ""}${isAttError ? " is-error" : ""}`}
                      data-file-id={att.id}
                      data-kind={att.kind}
                      data-previewable={isPreviewable ? "true" : "false"}
                      role={isPreviewable ? "button" : undefined}
                      tabIndex={isPreviewable ? 0 : undefined}
                      title={att.name}
                      aria-label={isPreviewable ? `Xem chi tiết tệp ${att.name}` : undefined}
                      onClick={
                        isPreviewable
                          ? () => {
                              if (suppressCardClickRef.current) return;
                              setPreviewModalFileId(att.id);
                            }
                          : undefined
                      }
                      onKeyDown={
                        isPreviewable
                          ? (e) => {
                              if (e.key === "Enter" || e.key === " ") {
                                e.preventDefault();
                                setPreviewModalFileId(att.id);
                              }
                            }
                          : undefined
                      }
                    >
                      <div className={`file-card-thumb${badgeClass}`}>
                        {isAttLoading ? (
                          <span className="composer-spin" aria-hidden="true" />
                        ) : isAttError ? (
                          <span>!</span>
                        ) : att.previewUrl ? (
                          <img
                            className="composer-file-thumb"
                            src={att.previewUrl}
                            alt={`Xem trước ${att.name}`}
                          />
                        ) : (
                          <span>{extBadge}</span>
                        )}
                      </div>
                      <div className="file-card-meta">
                        <div className="file-card-name-row" title={att.name}>
                          <span className="file-name-stem">{stem}</span>
                          <span className="file-name-ext">{extWithDot}</span>
                        </div>
                        <div className="file-card-format">{isAttLoading || isAttError ? subText : extBadge}</div>
                      </div>
                      <button
                        type="button"
                        className="file-card-remove"
                        onClick={(e) => {
                          e.stopPropagation();
                          removeAttachment(att.id);
                        }}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.stopPropagation();
                          }
                        }}
                        disabled={analyzing}
                        title="Bỏ tệp"
                        aria-label={`Bỏ tệp ${att.name}`}
                      >
                        <IconClose size={10} />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
            {filesScroll.max > 0 && !filesScroll.native && (
              <input
                className="composer-files-scroll-control"
                type="range"
                aria-label="Cuộn danh sách tệp đính kèm"
                min={0}
                max={filesScroll.max}
                step={1}
                value={filesScroll.value}
                style={{ "--thumb-width": `${filesScroll.thumb}px` } as React.CSSProperties}
                onInput={(event) => {
                  const row = filesRowRef.current;
                  if (row) {
                    row.scrollLeft = Number(event.currentTarget.value);
                    syncFilesOverflow(row);
                  }
                }}
                onChange={(event) => {
                  const row = filesRowRef.current;
                  if (row) {
                    row.scrollLeft = Number(event.currentTarget.value);
                    syncFilesOverflow(row);
                  }
                }}
                onKeyDown={(event) => {
                  const row = filesRowRef.current;
                  if (!row) return;
                  if (event.key === "ArrowRight") {
                    event.preventDefault();
                    row.scrollLeft = Math.min(filesScroll.max, row.scrollLeft + 72);
                    syncFilesOverflow(row);
                  } else if (event.key === "ArrowLeft") {
                    event.preventDefault();
                    row.scrollLeft = Math.max(0, row.scrollLeft - 72);
                    syncFilesOverflow(row);
                  }
                }}
              />
            )}
          </div>
        )}

        <div className="composer-main-row" id="composer-main-row">
          <div className="composer-input-tier" id="composer-input-tier">
            <textarea
              ref={textRef}
              id="home-problem-input"
              className="composer-textarea composer-text"
              rows={1}
              placeholder="Nhập đề toán hình học không gian..."
              aria-label="Đề bài hình học không gian"
              aria-describedby="composer-submit-req-hint"
              value={problemText}
              onChange={onChangeText}
              onPaste={onPasteText}
              onKeyDown={onKeyDown}
              readOnly={analyzing || cancelling}
            />
          </div>

          <div className="composer-toolbar" id="composer-toolbar">
            <div className="composer-left-tools composer-tools">
              <div className="plus-menu-anchor" ref={plusMenuAnchorRef}>
                <button
                  ref={plusTriggerRef}
                  type="button"
                  id="btn-composer-plus"
                  className={`btn-plus-trigger${plusMenuOpen ? " is-open" : ""}`}
                  onClick={(e) => {
                    const next = !plusMenuOpen;
                    if (next) {
                      const measured = readCurrentPlusPopoverPos();
                      if (measured && !measured.outOfView) {
                        applyPlusPopoverPosIfChanged(measured.pos);
                      }
                    }
                    setPlusMenuOpen(next);
                    if (next && e.detail === 0) {
                      requestAnimationFrame(() => {
                        plusPopoverRef.current
                          ?.querySelector<HTMLButtonElement>(".plus-menu-item:not(:disabled)")
                          ?.focus();
                      });
                    }
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
                      e.preventDefault();
                      const focusLast = e.key === "ArrowUp";
                      if (!plusMenuOpen) {
                        const measured = readCurrentPlusPopoverPos();
                        if (measured && !measured.outOfView) {
                          applyPlusPopoverPosIfChanged(measured.pos);
                        }
                        setPlusMenuOpen(true);
                      }
                      requestAnimationFrame(() => {
                        const items = plusPopoverRef.current?.querySelectorAll<HTMLButtonElement>(
                          ".plus-menu-item:not(:disabled)",
                        );
                        if (!items || items.length === 0) return;
                        items[focusLast ? items.length - 1 : 0].focus();
                      });
                    }
                  }}
                  disabled={analyzing}
                  title={
                    showCameraEntry
                      ? "Đính kèm tệp hoặc chụp ảnh đề bài"
                      : showScreenCaptureEntry
                        ? "Đính kèm tệp hoặc chụp màn hình"
                        : "Đính kèm tệp hoặc ảnh đề bài"
                  }
                  aria-label="Tải tệp đề"
                  aria-haspopup="menu"
                  aria-expanded={plusMenuOpen}
                >
                  {plusMenuOpen ? (
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      data-icon-state="close"
                      aria-hidden="true"
                    >
                      <path d="M6 6l12 12" />
                      <path d="M18 6L6 18" />
                    </svg>
                  ) : (
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      data-icon-state="plus"
                      aria-hidden="true"
                    >
                      <path d="M12 5v14" />
                      <path d="M5 12h14" />
                    </svg>
                  )}
                </button>

                <div
                  ref={plusPopoverRef}
                  id="plus-popover-menu"
                  className={`plus-popover-menu${
                    showCameraEntry ? " has-camera-item" : ""
                  }${showScreenCaptureEntry ? " has-screen-capture-item" : ""}${
                    plusMenuOpen ? " open" : ""
                  }`}
                  data-placement={plusPopoverPos?.placement ?? "top"}
                  data-collision-flipped={plusPopoverPos?.collisionFlipped ? "true" : "false"}
                  style={
                    plusPopoverPos
                      ? {
                          position: "fixed",
                          left: `${plusPopoverPos.left}px`,
                          top: `${plusPopoverPos.top}px`,
                          bottom: "auto",
                          right: "auto",
                          ...(plusPopoverPos.maxHeight
                            ? { maxHeight: `${plusPopoverPos.maxHeight}px` }
                            : {}),
                        }
                      : undefined
                  }
                  role="menu"
                  aria-label="Tùy chọn đính kèm đề bài"
                  onKeyDown={(e) => {
                    if (
                      e.key !== "ArrowDown" &&
                      e.key !== "ArrowUp" &&
                      e.key !== "Home" &&
                      e.key !== "End"
                    ) {
                      return;
                    }
                    const items = Array.from(
                      plusPopoverRef.current?.querySelectorAll<HTMLButtonElement>(
                        ".plus-menu-item:not(:disabled)",
                      ) ?? [],
                    );
                    if (items.length === 0) return;
                    e.preventDefault();
                    if (e.key === "Home") {
                      items[0].focus();
                      return;
                    }
                    if (e.key === "End") {
                      items[items.length - 1].focus();
                      return;
                    }
                    const cur = items.indexOf(document.activeElement as HTMLButtonElement);
                    const next =
                      e.key === "ArrowDown"
                        ? (cur + 1) % items.length
                        : cur <= 0
                          ? items.length - 1
                          : cur - 1;
                    items[next].focus();
                  }}
                >
                  <button
                    type="button"
                    id="menu-item-upload-file"
                    data-testid="btn-plus-upload-file"
                    className="plus-menu-item"
                    role="menuitem"
                    onClick={() => {
                      setPlusMenuOpen(false);
                      fileInputRef.current?.click();
                    }}
                  >
                    <span className="plus-menu-item-icon" aria-hidden="true">
                      <svg
                        width="18"
                        height="18"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.75"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        data-icon="paperclip"
                        aria-hidden="true"
                      >
                        <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                      </svg>
                    </span>
                    <span id="btn-plus-upload-file">Tải tệp từ thiết bị</span>
                  </button>
                  {showCameraEntry && (
                    <button
                      type="button"
                      id="menu-item-camera"
                      data-testid="btn-plus-camera"
                      className="plus-menu-item"
                      role="menuitem"
                      aria-haspopup="dialog"
                      onClick={() => {
                        setPlusMenuOpen(false);
                        setPhotoDialogOpen(true);
                      }}
                    >
                      <span className="plus-menu-item-icon" aria-hidden="true">
                        <svg
                          width="18"
                          height="18"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.75"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          data-icon="camera"
                          aria-hidden="true"
                        >
                          <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                          <circle cx="12" cy="13" r="3.75" />
                        </svg>
                      </span>
                      <span>Chụp ảnh đề bài</span>
                    </button>
                  )}
                  {showScreenCaptureEntry && (
                    <button
                      type="button"
                      id="menu-item-screen-capture"
                      data-testid="btn-plus-screen-capture"
                      className="plus-menu-item"
                      role="menuitem"
                      aria-haspopup="dialog"
                      onClick={() => {
                        setPlusMenuOpen(false);
                        void startScreenCapture();
                      }}
                    >
                      <span className="plus-menu-item-icon" aria-hidden="true">
                        <svg
                          width="18"
                          height="18"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.75"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          data-icon="screen-capture"
                          aria-hidden="true"
                        >
                          <rect x="3" y="4" width="18" height="13" rx="2" />
                          <path d="M8 21h8" />
                          <path d="M12 17v4" />
                          <path d="M7 8h2.5M7 8v2.5" />
                          <path d="M17 13h-2.5M17 13v-2.5" />
                        </svg>
                      </span>
                      <span>Chụp màn hình</span>
                    </button>
                  )}
                </div>
              </div>

              <button
                type="button"
                className="composer-sr-only"
                aria-label="Tải ảnh đề bài từ máy"
                tabIndex={-1}
                onClick={() => {
                  uploadImageRef.current?.click();
                }}
              >
                Tải ảnh
              </button>

              <span className="composer-hint-lbl composer-sr-only">
                Nhập đề toán, tải tệp hoặc chụp ảnh đề bài
              </span>
            </div>

            <div className="composer-footer composer-foot">
              {(() => {
                const buttonMode = cancelling
                  ? "cancelling"
                  : analyzing
                    ? "processing"
                    : canSubmit
                      ? "ready"
                      : "idle";
                const isStopMode = buttonMode === "processing" || buttonMode === "cancelling";
                const actionLabel =
                  buttonMode === "cancelling"
                    ? "Đang dừng..."
                    : buttonMode === "processing"
                      ? "Dừng dựng hình"
                      : "Dựng hình";
                return (
                  <button
                    type="button"
                    id="btn-composer-send"
                    className={`btn-composer-submit${buttonMode === "processing" ? " is-processing" : ""}${buttonMode === "cancelling" ? " is-cancelling" : ""}`}
                    data-composer-state={buttonMode}
                    onClick={() => {
                      if (buttonMode === "processing") {
                        handleStopAnalyze();
                      } else if (buttonMode === "ready") {
                        void onAnalyze();
                      }
                    }}
                    disabled={buttonMode === "idle" || buttonMode === "cancelling"}
                    aria-busy={isStopMode}
                    aria-describedby="composer-submit-req-hint"
                    title={actionLabel}
                    aria-label={actionLabel}
                  >
                    {isStopMode ? (
                      <span className="composer-submit-layer composer-submit-layer-stop">
                        <svg
                          width="14"
                          height="14"
                          viewBox="0 0 16 16"
                          className="composer-stop-icon"
                          aria-hidden="true"
                          focusable="false"
                        >
                          <rect x="3" y="3" width="10" height="10" rx="2" fill="currentColor" />
                        </svg>
                        <span className="composer-sr-only">{actionLabel}</span>
                      </span>
                    ) : (
                      <span className="composer-submit-layer composer-submit-layer-idle">
                        <IconSend size={18} className="composer-submit-arrow" />
                        <span className="composer-sr-only">Dựng hình</span>
                      </span>
                    )}
                  </button>
                );
              })()}

              <span id="composer-submit-req-hint" className="composer-sr-only">
                Phân tích đề bằng AI: Cần nhập đề toán hoặc đính kèm ít nhất một tệp đề bài hợp lệ để bật nút Dựng hình.
              </span>
            </div>
          </div>
        </div>
      </div>

      <PhotoProblemPanel
        state={assist}
        busy={analyzing}
        onSelectCandidate={onSelectAssistCandidate}
        onEditDraft={(text) => dispatchAssist({ type: "edit-draft", text })}
        onToggleConfirm={(value) => dispatchAssist({ type: "toggle-confirm", value })}
        onSubmitConfirmed={onSubmitConfirmedAssist}
        onDismiss={() => dispatchAssist({ type: "reset" })}
      />

      {(() => {
        const previewAtt = previewModalFileId
          ? attachments.find((a) => a.id === previewModalFileId) ?? null
          : null;
        if (!previewAtt || !canPreviewAttachment(previewAtt)) return null;
        if (previewAtt.kind === "image") {
          return (
            <div
              className="attachment-lightbox"
              id="composer-single-file-modal"
              role="dialog"
              aria-modal="true"
              aria-label={`Xem ảnh ${previewAtt.name}`}
              onClick={(e) => {
                if (e.target === e.currentTarget) setPreviewModalFileId(null);
              }}
            >
              <div className="attachment-lightbox-image">
                <button
                  type="button"
                  id="btn-close-file-modal"
                  className="attachment-lightbox-close"
                  aria-label="Đóng xem trước tệp"
                  onClick={() => setPreviewModalFileId(null)}
                >
                  <IconClose size={14} />
                </button>
                {previewAtt.previewUrl && !previewImageError ? (
                  <img
                    src={previewAtt.previewUrl}
                    alt={`Xem trước ${previewAtt.name}`}
                    onError={() => setPreviewImageError(true)}
                  />
                ) : (
                  <p className="attachment-lightbox-fallback">Không thể xem trước ảnh này.</p>
                )}
              </div>
              <div className="attachment-lightbox-caption">{previewAtt.name}</div>
            </div>
          );
        }
        return (
          <div
            className="axo-modal-backdrop axo-att-modal-backdrop open"
            id="composer-single-file-modal"
            style={{ zIndex: 132 }}
            role="dialog"
            aria-modal="true"
            aria-label={`Chi tiết tệp ${previewAtt.name}`}
            onClick={(e) => {
              if (e.target === e.currentTarget) setPreviewModalFileId(null);
            }}
          >
            <div className="axo-modal-dialog axo-att-modal attachment-pdf-dialog">
              <div className="axo-modal-head axo-att-modal-head">
                <span className="axo-modal-title axo-att-modal-title" id="file-modal-title" title={previewAtt.name}>
                  {previewAtt.name}
                </span>
                <button
                  type="button"
                  className="context-close-icon-btn axo-att-modal-close"
                  id="btn-close-file-modal"
                  onClick={() => setPreviewModalFileId(null)}
                  aria-label="Đóng xem trước tệp"
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
              <div className="axo-modal-body axo-att-modal-body" id="file-modal-body">
                {pdfPreviewCheck === "unknown" ? (
                  <PdfPreview key={previewAtt.id} file={previewAtt.file} downloadUrl={previewDownloadUrl} />
                ) : (
                  <div className="attachment-doc-fallback">
                    <p className="attachment-doc-fallback-text">
                      {pdfPreviewCheck === "checking"
                        ? "Đang kiểm tra tệp PDF…"
                        : "Không thể đọc tệp PDF: tệp bị cắt ngắn hoặc không có chữ ký PDF."}
                    </p>
                    {previewDownloadUrl && (
                      <a
                        className="attachment-doc-download-btn"
                        href={previewDownloadUrl}
                        download={previewAtt.name}
                        aria-label={`Tải tệp ${previewAtt.name} xuống`}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                          <polyline points="7 10 12 15 17 10" />
                          <line x1="12" y1="15" x2="12" y2="3" />
                        </svg>
                        <span>Tải tệp xuống</span>
                      </a>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })()}

      {allFilesModalOpen && attachments.length > 0 && (
        <div
          className="axo-modal-backdrop axo-att-modal-backdrop open"
          id="composer-all-files-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="composer-all-files-modal-title"
          onClick={(e) => {
            if (e.target === e.currentTarget) setAllFilesModalOpen(false);
          }}
        >
          <div className="axo-modal-dialog axo-att-modal" style={{ maxWidth: 520 }}>
            <div className="axo-modal-head axo-att-modal-head">
              <span
                className="axo-modal-title axo-att-modal-title"
                id="composer-all-files-modal-title"
              >
                {`Tất cả tệp đề toán đính kèm (${attachments.length})`}
              </span>
              <button
                type="button"
                className="context-close-icon-btn axo-att-modal-close"
                id="btn-close-composer-all-files-modal"
                onClick={() => setAllFilesModalOpen(false)}
                aria-label="Đóng danh sách tệp đính kèm"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div className="axo-modal-body axo-att-modal-body">
              <div className="axo-att-modal-sub">
                Danh sách các tệp đề bài đã đính kèm. Bạn có thể xem trước nội dung hoặc gỡ từng tệp trước khi bấm <strong>Dựng hình</strong>.
              </div>
              <div
                className="all-files-modal-list axo-custom-scroll"
                id="composer-all-files-modal-list"
                ref={allFilesListRef}
                role="list"
              >
                {attachments.map((att, idx) => {
                  const extBadge = (att.ext.replace(".", "") || att.kind).toUpperCase();
                  const isAttLoading = att.status === "loading";
                  const isAttError = att.status === "error";
                  const badgeClass = isAttLoading
                    ? " badge-loading"
                    : isAttError
                      ? " badge-error"
                      : att.kind === "pdf" || extBadge === "PDF"
                        ? " badge-pdf"
                        : att.kind === "document" || extBadge === "DOCX"
                          ? " badge-docx"
                          : !att.previewUrl
                            ? " badge-txt"
                            : "";
                  const statusLabel = isAttLoading
                    ? "Đang tải lên"
                    : isAttError
                      ? att.errorMessage || "Lỗi tải tệp"
                      : "Đã đính kèm";
                  return (
                    <div
                      key={att.id}
                      className="all-files-modal-item"
                      role="listitem"
                      data-modal-file-id={att.id}
                    >
                      <div className="all-files-modal-item-left">
                        <div className={`file-card-thumb${badgeClass}`}>
                          {isAttLoading ? (
                            <span className="composer-spin" aria-hidden="true" />
                          ) : isAttError ? (
                            <span>!</span>
                          ) : att.previewUrl ? (
                            <img
                              className="composer-file-thumb"
                              src={att.previewUrl}
                              alt={att.name}
                            />
                          ) : (
                            <span>{extBadge}</span>
                          )}
                        </div>
                        <div className="all-files-modal-item-meta">
                          <div className="all-files-modal-item-name" title={att.name}>
                            {`#${idx + 1} · ${att.name}`}
                          </div>
                          <div className="all-files-modal-item-sub">
                            {`${extBadge} · ${att.sizeFormatted} · ${statusLabel}`}
                          </div>
                        </div>
                      </div>
                      <div className="all-files-modal-item-actions">
                        {canPreviewAttachment(att) && (
                          <button
                            type="button"
                            className="btn-admin-sm"
                            data-modal-preview-file-id={att.id}
                            onClick={() => setPreviewModalFileId(att.id)}
                          >
                            Xem trước
                          </button>
                        )}
                        <button
                          type="button"
                          className="file-card-remove"
                          data-modal-remove-file-id={att.id}
                          onClick={() => removeAttachment(att.id)}
                          disabled={analyzing}
                          aria-label={`Gỡ tệp ${att.name}`}
                          title="Gỡ tệp này"
                          style={{ position: "static", width: 28, height: 28 }}
                        >
                          ×
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
              <AxoScrollbar targetRef={allFilesListRef} />
              <div className="all-files-modal-foot">
                <button
                  type="button"
                  className="btn-auth-primary"
                  id="btn-done-composer-all-files-modal"
                  style={{ height: 34, padding: "0 16px" }}
                  onClick={() => setAllFilesModalOpen(false)}
                >
                  Đóng
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <PhotoProblemDialog
        open={photoDialogOpen}
        onClose={closePhotoDialog}
        onPickFile={() => {
          setPhotoDialogOpen(false);
          uploadImageRef.current?.click();
        }}
        onNativeCamera={() => {
          setPhotoDialogOpen(false);
          cameraImageRef.current?.click();
        }}
        onCaptured={(file) => {
          addFilesToComposer([file], { source: "camera" });
          setPhotoDialogOpen(false);
        }}
        onCapturedBatch={(files) => {
          addFilesToComposer(files, { source: "camera" });
          setPhotoDialogOpen(false);
        }}
      />

      {serverStatus}
      {analysisError && /lượt mô phỏng thử/.test(analysisError) ? (
        <div className="trial-gate">
          <strong>Em đã dùng hết lượt mô phỏng thử.</strong>
          <p>Đăng nhập để tiếp tục — tài khoản cho phép:</p>
          <ul>
            <li>lưu lịch sử học tập và mở lại đúng bước dựng</li>
            <li>tiếp tục học các mô hình 3D trên mọi thiết bị</li>
            <li>quản lý danh sách đề toán đã phân tích</li>
          </ul>
          <div className="trial-gate-actions">
            <button
              type="button"
              className="btn-primary"
              onClick={() => useAuthStore.getState().openAuthGate("register")}
            >
              Tạo tài khoản
            </button>
            <button
              type="button"
              className="btn-utility"
              onClick={() => useAuthStore.getState().openAuthGate("login")}
            >
              Đăng nhập
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
