import { useEffect, useReducer, useRef, useState } from "react";
import { useAppStore } from "../state/store";
import { displayBrand } from "../branding";
import { useAuthStore } from "../state/auth";
import { newAttemptId } from "../state/history";
import { useToastStore } from "./TopNav";
import {
  IconCamera,
  IconClose,
  IconPlus,
  IconUpload,
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
  canSubmitComposer,
  composerAttachmentMimeOf,
  formatAttachmentSize,
  readAsBase64,
  splitAttachmentName,
  validateComposerFile,
  type ComposerAttachmentItem,
} from "../llm/input";
import type { AnalysisUnsupported } from "../core/types";
import type { SimulationEnvelope } from "../simulations/types";
import { PhotoProblemDialog } from "./PhotoProblemDialog";
import {
  readBrowserCameraDeviceSignals,
  shouldShowCameraEntry,
  type CameraDeviceSignals,
} from "./PhotoCameraView";
import { PhotoProblemPanel } from "./PhotoProblemPanel";
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

/** Huỷ chủ động lượt đang trích xuất / dựng hình: giữ nguyên nội dung gõ tay và tệp đính kèm. */
export function cancelComposerSubmit(
  lockRef: { current: boolean },
  abortRef?: { current: AbortController | null },
): void {
  const ctl = abortRef?.current ?? null;
  if (abortRef) abortRef.current = null;
  lockRef.current = false;
  ctl?.abort();
  useAppStore.getState().setAnalyzing(false);
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
  // Một lần bấm gửi = một lần học. Thử lại mạng nằm trong `analyzeFn` nên dùng chung ID này.
  const attemptId = newAttemptId();
  if (requestIdRef) {
    requestIdRef.current = attemptId;
  }

  const ctl = typeof AbortController !== "undefined" ? new AbortController() : null;
  if (abortRef) abortRef.current = ctl;

  const store = useAppStore.getState();
  store.setAnalysisError(null);
  store.clearUnsupported();
  useToastStore.getState().dismissToast("composer-refusal");
  store.setAnalyzing(true);

  const targetAttachments =
    attachments && attachments.length > 0
      ? attachments
      : attachment
        ? [attachment]
        : [];

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
      if (ctl?.signal.aborted) return;
      if (requestIdRef?.current && requestIdRef.current !== attemptId) return;

      const firstAtt = targetAttachments[0]!;
      const attachmentPayloads = targetAttachments.map((item, idx) => ({
        attachment_id: item.id,
        order_index: idx,
        source_type: (item.kind === "image" ? "camera" : item.kind) as
          | "camera"
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
      if (ctl?.signal.aborted) return;
      if (requestIdRef?.current && requestIdRef.current !== attemptId) return;
      if (prepared.request_id && prepared.request_id !== attemptId) return;

      if (prepared.status === "needs_selection" || prepared.status === "needs_confirmation") {
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
    }

    const result = await analyzeFn(
      { type: "text", content: finalProblemText },
      ctl?.signal,
      undefined,
      attemptId,
    );
    if (ctl?.signal.aborted) return;

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
      store.loadUnsupported(unsupportedRes);
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

/** Kích thước chiều cao ô nhập theo V2.7 + yêu cầu co giãn 3 dòng mặc định của chủ dự án (Phase C.4 P2). */
const COMPOSER_MIN_H_DESKTOP = 76;
const COMPOSER_MIN_H_MOBILE = 72;
const COMPOSER_MAX_H = 220;

function getComposerMinHeight(): number {
  if (typeof window !== "undefined" && window.innerWidth <= 640) {
    return COMPOSER_MIN_H_MOBILE;
  }
  return COMPOSER_MIN_H_DESKTOP;
}

let attachmentSeq = 0;

function revokePreviewUrl(url: string | undefined) {
  if (url && typeof URL !== "undefined" && typeof URL.revokeObjectURL === "function") {
    URL.revokeObjectURL(url);
  }
}

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
}

export function ProblemInput({
  initialAttachments = [],
  initialPlusMenuOpen = false,
  initialAllFilesModalOpen = false,
  initialAssistState = initialUnifiedAssistState,
  deviceSignals,
}: ProblemInputProps = {}) {
  const showCameraEntry = shouldShowCameraEntry(
    deviceSignals ?? readBrowserCameraDeviceSignals(),
  );
  const problemText = useAppStore((s) => s.problemText);
  const setProblemText = useAppStore((s) => s.setProblemText);
  const analyzing = useAppStore((s) => s.analyzing);
  const analysisError = useAppStore((s) => s.analysisError);

  const [health, setHealth] = useState<ServerHealth | null | "loading">("loading");
  const [attachments, setAttachments] = useState<ComposerAttachmentItem[]>(
    initialAttachments,
  );
  const [plusMenuOpen, setPlusMenuOpen] = useState(initialPlusMenuOpen);
  const [allFilesModalOpen, setAllFilesModalOpen] = useState(
    initialAllFilesModalOpen,
  );
  const [previewModalFileId, setPreviewModalFileId] = useState<string | null>(
    null,
  );
  const [photoDialogOpen, setPhotoDialogOpen] = useState(false);
  const [assist, dispatchAssist] = useReducer(
    unifiedAssistReducer,
    initialAssistState,
  );

  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadImageRef = useRef<HTMLInputElement>(null);
  const cameraImageRef = useRef<HTMLInputElement>(null);
  const replaceTargetIdRef = useRef<string | null>(null);
  const textRef = useRef<HTMLTextAreaElement>(null);
  const plusMenuAnchorRef = useRef<HTMLDivElement>(null);
  const filesRowRef = useRef<HTMLDivElement>(null);
  const attachmentsRef = useRef<ComposerAttachmentItem[]>([]);
  const submittingRef = useRef(false);
  const analyzeAbortRef = useRef<AbortController | null>(null);
  const activePrepareRequestIdRef = useRef<string | null>(null);
  const allFilesListRef = useRef<HTMLDivElement>(null);
  const [filesOverflow, setFilesOverflow] = useState<{ left: boolean; right: boolean }>({
    left: false,
    right: false,
  });

  useEffect(() => {
    attachmentsRef.current = attachments;
  }, [attachments]);

  function syncFilesOverflow(el: HTMLDivElement | null) {
    if (!el) {
      setFilesOverflow((prev) =>
        prev.left || prev.right ? { left: false, right: false } : prev,
      );
      return;
    }
    const nextLeft = el.scrollLeft > 2;
    const nextRight = el.scrollLeft + el.clientWidth < el.scrollWidth - 2;
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

  // Thu hồi toàn bộ objectURL và huỷ request đang chạy khi tháo component để tránh rò bộ nhớ.
  useEffect(() => {
    return () => {
      analyzeAbortRef.current?.abort();
      for (const item of attachmentsRef.current) {
        revokePreviewUrl(item.previewUrl);
      }
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchHealth().then((h) => {
      if (!cancelled) setHealth(h);
    });
    return () => {
      cancelled = true;
    };
  }, [analyzing]);

  // Tự đóng modal Tất cả tệp hoặc modal xem trước nếu người dùng xóa tệp.
  useEffect(() => {
    if (attachments.length === 0 && allFilesModalOpen) {
      setAllFilesModalOpen(false);
    }
    if (previewModalFileId && !attachments.some((a) => a.id === previewModalFileId)) {
      setPreviewModalFileId(null);
    }
  }, [attachments, allFilesModalOpen, previewModalFileId]);

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
          setPlusMenuOpen(false);
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
  const isUploadingAny = attachments.some((a) => a.status === "loading");
  const canSubmit = canSubmitComposer(
    problemText,
    readyAttachments.length,
    analyzing,
    isUploadingAny,
  );

  function syncTextareaHeight(el: HTMLTextAreaElement | null) {
    if (!el) return;
    const minH = getComposerMinHeight();
    const val = el.value ?? "";
    if (val.length === 0) {
      el.style.height = `${minH}px`;
      el.style.overflowY = "hidden";
      return;
    }
    el.style.height = "0px";
    const measured = el.scrollHeight;
    let targetH = minH;
    if (measured > 0) {
      targetH = Math.min(Math.max(measured, minH), COMPOSER_MAX_H);
      el.style.overflowY = measured > COMPOSER_MAX_H ? "auto" : "hidden";
    } else {
      const explicitLines = val.split("\n").length;
      const approxWrappedLines = Math.ceil(val.length / 72);
      const totalLines = Math.max(explicitLines, approxWrappedLines);
      const lineH = minH === COMPOSER_MIN_H_MOBILE ? 22 : 24;
      const padV = minH === COMPOSER_MIN_H_MOBILE ? 6 : 4;
      const calcH = totalLines <= 3 ? minH : totalLines * lineH + padV;
      targetH = Math.min(Math.max(calcH, minH), COMPOSER_MAX_H);
      el.style.overflowY = calcH > COMPOSER_MAX_H ? "auto" : "hidden";
    }
    el.style.height = `${targetH}px`;
  }

  useEffect(() => {
    syncTextareaHeight(textRef.current);
  }, [problemText]);

  useEffect(() => {
    const el = textRef.current;
    if (!el) return;
    syncTextareaHeight(el);
    const onResize = () => syncTextareaHeight(textRef.current);
    if (typeof window !== "undefined") {
      window.addEventListener("resize", onResize);
    }
    let ro: ResizeObserver | null = null;
    if (typeof ResizeObserver !== "undefined") {
      ro = new ResizeObserver(() => syncTextareaHeight(textRef.current));
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
    setProblemText(e.target.value);
    const st = useAppStore.getState();
    if (st.unsupported) st.clearUnsupported();
    if (st.analysisError && !/lượt mô phỏng thử/.test(st.analysisError)) {
      st.setAnalysisError(null);
    }
    syncTextareaHeight(e.target);
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

    if (e.shiftKey) {
      if (analyzing) e.preventDefault();
      return;
    }

    e.preventDefault();
    if (canSubmit) {
      void onAnalyze();
    }
  }

  function addFilesToComposer(allPicked: File[], opts?: { replaceId?: string | null }) {
    if (allPicked.length === 0) return;

    const replaceId = opts?.replaceId ?? null;
    const baseExisting = replaceId
      ? attachments.filter((a) => a.id !== replaceId)
      : attachments;
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
        status: "ready",
      });
      workingExisting.push({ name: picked.name, size: picked.size });
    }

    if (nextItems.length > 0) {
      dispatchAssist({ type: "reset" });
      setAttachments((prev) => {
        if (!replaceId) {
          return [...prev, ...nextItems];
        }
        const replaced = prev.find((item) => item.id === replaceId);
        revokePreviewUrl(replaced?.previewUrl);
        const idx = prev.findIndex((item) => item.id === replaceId);
        if (idx < 0) return [...prev, ...nextItems];
        const copy = [...prev];
        copy.splice(idx, 1, ...nextItems);
        return copy;
      });
    }
  }

  function onPickFiles(e: React.ChangeEvent<HTMLInputElement>) {
    const list = e.target.files ? Array.from(e.target.files) : [];
    const replaceId = replaceTargetIdRef.current;
    replaceTargetIdRef.current = null;
    addFilesToComposer(list, { replaceId });
    e.target.value = "";
  }

  function onPickImage(e: React.ChangeEvent<HTMLInputElement>) {
    const pickedList = e.target.files ? Array.from(e.target.files) : [];
    const replaceId = replaceTargetIdRef.current;
    replaceTargetIdRef.current = null;
    if (pickedList.length > 0) {
      addFilesToComposer(pickedList, { replaceId });
    }
    e.target.value = "";
  }

  function removeAttachment(id: string) {
    activePrepareRequestIdRef.current = null;
    dispatchAssist({ type: "reset" });
    setAttachments((prev) => {
      const target = prev.find((item) => item.id === id);
      revokePreviewUrl(target?.previewUrl);
      return prev.filter((item) => item.id !== id);
    });
  }

  function triggerReplaceAttachment(id: string) {
    replaceTargetIdRef.current = id;
    setPreviewModalFileId(null);
    fileInputRef.current?.click();
  }

  function closePhotoDialog() {
    setPhotoDialogOpen(false);
  }

  async function onAnalyze(opts?: {
    selectedCandidateId?: string;
    overridePreparedText?: string;
  }) {
    dispatchAssist({ type: "reset" });
    await runComposerSubmit({
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
    <div className="composer-hero">
      <div
        className={`composer-card composer-box${analyzing ? " is-busy" : ""}`}
        id="home-composer-box"
      >
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
              >
                {attachments.map((att) => {
                  const { stem, extWithDot } = splitAttachmentName(att.name);
                  const extBadge = (att.ext.replace(".", "") || att.kind).toUpperCase();
                  const isAttLoading = att.status === "loading";
                  const isAttError = att.status === "error";
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
                    ? `Đang tải lên · ${att.sizeFormatted}`
                    : isAttError
                      ? att.errorMessage || "Lỗi tải tệp"
                      : `${extBadge} · ${att.sizeFormatted}`;
                  return (
                    <div
                      key={att.id}
                      className={`file-preview-card${isAttLoading ? " is-loading" : ""}${isAttError ? " is-error" : ""}`}
                      data-file-id={att.id}
                      role="button"
                      tabIndex={0}
                      title={att.name}
                      aria-label={`Xem chi tiết tệp ${att.name}`}
                      onClick={() => setPreviewModalFileId(att.id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          setPreviewModalFileId(att.id);
                        }
                      }}
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
                        <div className="file-card-sub">{subText}</div>
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
                        <IconClose size={12} />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        <textarea
          ref={textRef}
          id="home-problem-input"
          className="composer-textarea composer-text"
          rows={3}
          placeholder="Nhập đề toán hình học không gian..."
          aria-label="Đề bài hình học không gian"
          aria-describedby="composer-submit-req-hint"
          value={problemText}
          onChange={onChangeText}
          onKeyDown={onKeyDown}
          readOnly={analyzing}
        />

        <div className="composer-footer composer-foot">
          <div className="composer-left-tools composer-tools">
            <div className="plus-menu-anchor" ref={plusMenuAnchorRef}>
              <button
                type="button"
                id="btn-composer-plus"
                className={`btn-plus-trigger${plusMenuOpen ? " is-open" : ""}`}
                onClick={() => setPlusMenuOpen((v) => !v)}
                disabled={analyzing}
                title={
                  showCameraEntry
                    ? "Đính kèm tệp hoặc chụp ảnh đề bài"
                    : "Đính kèm tệp hoặc ảnh đề bài"
                }
                aria-label="Tải tệp đề"
                aria-haspopup="menu"
                aria-expanded={plusMenuOpen}
              >
                <IconPlus size={16} />
              </button>

              <div
                id="plus-popover-menu"
                className={`plus-popover-menu${plusMenuOpen ? " open" : ""}`}
                role="menu"
                aria-label="Tùy chọn đính kèm đề bài"
              >
                <button
                  type="button"
                  id="menu-item-upload-file"
                  className="plus-menu-item"
                  role="menuitem"
                  onClick={() => {
                    setPlusMenuOpen(false);
                    replaceTargetIdRef.current = null;
                    fileInputRef.current?.click();
                  }}
                >
                  <IconUpload size={16} />
                  <span>Tải tệp từ thiết bị</span>
                </button>
                {showCameraEntry && (
                  <button
                    type="button"
                    id="menu-item-camera"
                    className="plus-menu-item"
                    role="menuitem"
                    aria-haspopup="dialog"
                    onClick={() => {
                      setPlusMenuOpen(false);
                      setPhotoDialogOpen(true);
                    }}
                  >
                    <IconCamera size={16} />
                    <span>Chụp ảnh đề bài</span>
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
                replaceTargetIdRef.current = null;
                uploadImageRef.current?.click();
              }}
            >
              Tải ảnh
            </button>

            <span className="composer-hint-lbl">
              Nhập đề bài hoặc chọn mẫu bên dưới
            </span>
          </div>

          {analyzing && (
            <button
              type="button"
              id="btn-composer-cancel"
              className="btn-composer-cancel"
              onClick={() => cancelComposerSubmit(submittingRef, analyzeAbortRef)}
              aria-label="Huỷ quá trình dựng hình đang chạy"
            >
              Huỷ
            </button>
          )}

          <button
            type="button"
            id="btn-composer-send"
            className={`btn-composer-submit${analyzing ? " is-loading" : ""}`}
            onClick={() => void onAnalyze()}
            disabled={!canSubmit}
            aria-busy={analyzing}
            aria-describedby="composer-submit-req-hint"
            title="Dựng hình"
            aria-label="Phân tích đề bằng AI"
          >
            {analyzing ? (
              <span className="composer-submit-layer composer-submit-layer-loading">
                <span className="composer-spin composer-submit-spinner" aria-hidden="true" />
                <span className="composer-submit-label">Đang dựng hình...</span>
              </span>
            ) : (
              <span className="composer-submit-layer composer-submit-layer-idle">
                <span className="composer-submit-label">Dựng hình</span>
                <span className="composer-submit-arrow" aria-hidden="true">→</span>
              </span>
            )}
          </button>

          <span id="composer-submit-req-hint" className="composer-sr-only">
            Cần nhập đề toán hoặc đính kèm ít nhất một tệp đề bài hợp lệ để bật nút Dựng hình.
          </span>
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
        if (!previewAtt) return null;
        const extBadge = (previewAtt.ext.replace(".", "") || previewAtt.kind).toUpperCase();
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
            <div className="axo-modal-dialog axo-att-modal" style={{ maxWidth: 500 }}>
              <div className="axo-modal-head axo-att-modal-head">
                <span className="axo-modal-title axo-att-modal-title" id="file-modal-title">
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
                {previewAtt.previewUrl ? (
                  <div className="file-modal-preview-stage single-file-preview-box">
                    <img
                      className="single-file-preview-img"
                      src={previewAtt.previewUrl}
                      alt={`Xem trước ${previewAtt.name}`}
                    />
                  </div>
                ) : (
                  <div
                    className="file-modal-preview-stage single-file-preview-box"
                    style={{ flexDirection: "column", gap: 8, textAlign: "center", minHeight: 160 }}
                  >
                    <span
                      className={`role-chip ${extBadge === "PDF" ? "locked" : "student"}`}
                      style={{ fontSize: 12.5, padding: "4px 12px" }}
                    >
                      {`Tệp ${extBadge} · ${previewAtt.sizeFormatted}`}
                    </span>
                    <div style={{ maxWidth: 420, color: "var(--ink-secondary)", fontSize: 12.6 }}>
                      {`Nội dung tệp ${extBadge} sẽ được trích xuất tự động khi bấm Dựng hình.`}
                    </div>
                  </div>
                )}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 8,
                    flexWrap: "wrap",
                    fontSize: 12,
                    color: "var(--ink-muted)",
                    textAlign: "left",
                  }}
                >
                  <span>
                    Định dạng: <strong>{extBadge}</strong> · Dung lượng:{" "}
                    <strong>{previewAtt.sizeFormatted}</strong>
                  </span>
                  <span>
                    Tên đầy đủ: <strong>{previewAtt.name}</strong>
                  </span>
                </div>
                <div
                  style={{
                    background: "var(--canvas-soft)",
                    border: "1px solid var(--hairline)",
                    borderRadius: 8,
                    padding: "10px 12px",
                    fontSize: 12.3,
                    color: "var(--ink-secondary)",
                    textAlign: "left",
                  }}
                >
                  <strong>Trạng thái tệp:</strong>{" "}
                  {previewAtt.status === "loading"
                    ? "Đang tải lên..."
                    : previewAtt.status === "error"
                      ? previewAtt.errorMessage || "Lỗi tải tệp"
                      : "Đã đính kèm · Sẵn sàng phân tích khi bấm Dựng hình."}
                </div>
                <div className="all-files-modal-foot">
                  <button
                    type="button"
                    id="btn-replace-file-modal"
                    className="btn-admin-sm"
                    onClick={() => triggerReplaceAttachment(previewAtt.id)}
                    disabled={analyzing}
                  >
                    Đổi tệp
                  </button>
                  <button
                    type="button"
                    className="btn-admin-sm warn"
                    onClick={() => {
                      removeAttachment(previewAtt.id);
                      setPreviewModalFileId(null);
                    }}
                    disabled={analyzing}
                  >
                    Gỡ tệp
                  </button>
                  <button
                    type="button"
                    className="btn-auth-primary"
                    style={{ height: 34, padding: "0 16px" }}
                    onClick={() => setPreviewModalFileId(null)}
                  >
                    Đóng
                  </button>
                </div>
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
                        <button
                          type="button"
                          className="btn-admin-sm"
                          data-modal-preview-file-id={att.id}
                          onClick={() => setPreviewModalFileId(att.id)}
                        >
                          Xem trước
                        </button>
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
          replaceTargetIdRef.current = null;
          uploadImageRef.current?.click();
        }}
        onNativeCamera={() => {
          setPhotoDialogOpen(false);
          replaceTargetIdRef.current = null;
          cameraImageRef.current?.click();
        }}
        onCaptured={(file) => {
          addFilesToComposer([file]);
          setPhotoDialogOpen(false);
        }}
        onCapturedBatch={(files) => {
          addFilesToComposer(files);
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
