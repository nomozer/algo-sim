import {
  classifyCameraDevice,
  readBrowserCameraDeviceSignals,
  type CameraDeviceKind,
  type CameraDeviceSignals,
} from "./PhotoCameraView";

export interface UploadMenuCapabilitySignals {
  deviceSignals?: CameraDeviceSignals;
  isSecureContext?: boolean;
  hasDisplayMedia?: boolean;
  hasUserMedia?: boolean;
}

export interface UploadMenuCapabilities {
  deviceKind: CameraDeviceKind;
  showUploadFile: boolean;
  showScreenCapture: boolean;
  showCamera: boolean;
  canCaptureScreen: boolean;
  canCaptureCamera: boolean;
  visibleActionCount: number;
}

/**
 * Quyết định các hành động hiển thị trong Upload Menu dựa trên phân loại thiết bị
 * kết hợp kiểm tra khả năng thực tế của trình duyệt (không dựa trên CSS breakpoint):
 * - Desktop / Laptop: ưu tiên `1. Tải tệp từ thiết bị`, `2. Chụp màn hình`.
 * - Phone: ưu tiên `1. Tải tệp từ thiết bị`, `2. Chụp ảnh đề bài`.
 * - Tablet: ưu tiên `1. Tải tệp từ thiết bị`, `2. Chụp ảnh đề bài`, và giữ thêm
 *   `Chụp màn hình` khi trình duyệt thực tế có hỗ trợ `getDisplayMedia`.
 */
export function resolveUploadMenuCapabilities(
  input?: UploadMenuCapabilitySignals,
): UploadMenuCapabilities {
  const effectiveDeviceSignals =
    input?.deviceSignals ?? readBrowserCameraDeviceSignals();
  const deviceKind = classifyCameraDevice(effectiveDeviceSignals);

  const isSecure =
    input?.isSecureContext !== undefined
      ? input.isSecureContext
      : typeof window !== "undefined"
        ? Boolean(window.isSecureContext)
        : true;

  const hasDisplayMedia =
    input?.hasDisplayMedia !== undefined
      ? input.hasDisplayMedia
      : typeof navigator !== "undefined" &&
        typeof navigator.mediaDevices?.getDisplayMedia === "function";

  const hasUserMedia =
    input?.hasUserMedia !== undefined
      ? input.hasUserMedia
      : typeof navigator !== "undefined" &&
        typeof navigator.mediaDevices?.getUserMedia === "function";

  const canCaptureScreen = Boolean(isSecure && hasDisplayMedia);
  const canCaptureCamera = Boolean(isSecure && hasUserMedia);

  if (deviceKind === "phone") {
    return {
      deviceKind,
      showUploadFile: true,
      showScreenCapture: false,
      showCamera: true,
      canCaptureScreen,
      canCaptureCamera,
      visibleActionCount: 2,
    };
  }

  if (deviceKind === "tablet") {
    const showScreenOnTablet = canCaptureScreen;
    return {
      deviceKind,
      showUploadFile: true,
      showScreenCapture: showScreenOnTablet,
      showCamera: true,
      canCaptureScreen,
      canCaptureCamera,
      visibleActionCount: showScreenOnTablet ? 3 : 2,
    };
  }

  // Desktop / Laptop (hoặc môi trường mặc định không phải thiết bị di động)
  return {
    deviceKind,
    showUploadFile: true,
    showScreenCapture: true,
    showCamera: false,
    canCaptureScreen,
    canCaptureCamera,
    visibleActionCount: 2,
  };
}

export type ScreenCaptureErrorCode =
  | "cancelled"
  | "unsupported"
  | "permission_denied"
  | "not_found"
  | "unavailable"
  | "unknown";

export interface ScreenCaptureErrorInfo {
  code: ScreenCaptureErrorCode;
  title: string;
  description: string;
  canRetry: boolean;
}

export function classifyScreenCaptureSupportError(env?: {
  isSecureContext?: boolean;
  hasDisplayMedia?: boolean;
}): ScreenCaptureErrorInfo | null {
  const isSecure =
    env?.isSecureContext !== undefined
      ? env.isSecureContext
      : typeof window !== "undefined"
        ? Boolean(window.isSecureContext)
        : false;
  const hasApi =
    env?.hasDisplayMedia !== undefined
      ? env.hasDisplayMedia
      : typeof navigator !== "undefined" &&
        typeof navigator.mediaDevices?.getDisplayMedia === "function";

  if (!isSecure || !hasApi) {
    return {
      code: "unsupported",
      title: "Trình duyệt này chưa hỗ trợ chụp màn hình",
      description:
        "Em có thể chụp màn hình bằng phím tắt trên máy rồi tải tệp ảnh từ thiết bị.",
      canRetry: false,
    };
  }
  return null;
}

const SYSTEM_PERMISSION_BLOCK_PATTERN =
  /by system|system permission|os permission|permissions[- ]policy|feature[- ]policy|disabled by|enterprise|administrator/i;

export function classifyScreenCaptureError(err: unknown): ScreenCaptureErrorInfo {
  const name =
    err && typeof err === "object" && "name" in err
      ? String((err as { name?: unknown }).name ?? "")
      : "";
  const message =
    err && typeof err === "object" && "message" in err
      ? String((err as { message?: unknown }).message ?? "")
      : typeof err === "string"
        ? err
        : "";

  if (
    name === "UnsupportedScreenCaptureError" ||
    name === "NotSupportedError" ||
    name === "TypeError"
  ) {
    return {
      code: "unsupported",
      title: "Trình duyệt này chưa hỗ trợ chụp màn hình",
      description:
        "Em có thể chụp màn hình bằng phím tắt trên máy rồi tải tệp ảnh từ thiết bị.",
      canRetry: false,
    };
  }

  if (name === "AbortError") {
    return {
      code: "cancelled",
      title: "",
      description: "",
      canRetry: false,
    };
  }

  if (name === "SecurityError") {
    return {
      code: "permission_denied",
      title: "Chưa thể truy cập màn hình",
      description:
        "Quyền chia sẻ màn hình đang bị hạn chế trong ngữ cảnh hiện tại. Em có thể tải tệp ảnh từ thiết bị.",
      canRetry: false,
    };
  }

  if (name === "NotAllowedError" || name === "PermissionDeniedError") {
    if (SYSTEM_PERMISSION_BLOCK_PATTERN.test(message)) {
      return {
        code: "permission_denied",
        title: "Chưa có quyền chia sẻ màn hình",
        description:
          "Hệ điều hành hoặc trình duyệt đang giới hạn quyền chụp màn hình. Em có thể kiểm tra quyền hoặc tải tệp ảnh từ thiết bị.",
        canRetry: true,
      };
    }
    return {
      code: "cancelled",
      title: "",
      description: "",
      canRetry: false,
    };
  }

  if (name === "NotFoundError" || name === "OverconstrainedError") {
    return {
      code: "not_found",
      title: "Không tìm thấy nguồn màn hình phù hợp",
      description:
        "Em có thể thử chọn lại cửa sổ cần chụp hoặc tải tệp ảnh từ thiết bị.",
      canRetry: true,
    };
  }

  if (
    name === "NotReadableError" ||
    name === "TrackStartError" ||
    name === "InvalidStateError"
  ) {
    return {
      code: "unavailable",
      title: "Không thể truy cập nguồn đã chọn",
      description:
        "Cửa sổ hoặc màn hình vừa chọn tạm thời không đọc được. Em có thể thử lại hoặc tải tệp ảnh từ thiết bị.",
      canRetry: true,
    };
  }

  return {
    code: "unknown",
    title: "Chưa thể trích xuất ảnh chụp màn hình",
    description:
      "Đã xảy ra lỗi khi tạo ảnh tĩnh. Em có thể thử chụp lại hoặc tải tệp ảnh từ thiết bị.",
    canRetry: true,
  };
}

export function stopAllMediaStreamTracks(
  stream: { getTracks?: () => Array<{ stop: () => void }> } | null | undefined,
): number {
  if (!stream || typeof stream.getTracks !== "function") return 0;
  let stoppedCount = 0;
  for (const track of stream.getTracks()) {
    try {
      track.stop();
      stoppedCount += 1;
    } catch {
      /* ignore individual track stop failure */
    }
  }
  return stoppedCount;
}

export interface CapturedScreenFrame {
  file: File;
  previewUrl: string;
  width: number;
  height: number;
  stoppedTracks: number;
}

export interface ScreenCaptureDeps {
  isSecureContext?: boolean;
  getDisplayMedia?: (constraints: DisplayMediaStreamOptions) => Promise<MediaStream>;
  extractFrameFromStream?: (stream: MediaStream) => Promise<{
    blob: Blob;
    width: number;
    height: number;
  }>;
  createObjectURL?: (blob: Blob) => string;
  now?: () => number;
}

const MAX_CAPTURE_SIDE_PX = 3840;

async function defaultExtractFrameFromStream(stream: MediaStream): Promise<{
  blob: Blob;
  width: number;
  height: number;
}> {
  const track = stream.getVideoTracks()[0];
  if (!track || track.readyState !== "live") {
    throw Object.assign(new Error("No active video track"), { name: "NotReadableError" });
  }
  const video = document.createElement("video");
  video.muted = true;
  video.playsInline = true;
  video.autoplay = true;
  video.srcObject = stream;

  try {
    await new Promise<void>((resolve, reject) => {
      let settled = false;
      const timer = window.setTimeout(() => {
        if (settled) return;
        settled = true;
        reject(Object.assign(new Error("Frame timeout"), { name: "NotReadableError" }));
      }, 5000);

      const finish = () => {
        if (settled) return;
        if (video.readyState >= 2 && video.videoWidth > 0 && video.videoHeight > 0 && track.readyState === "live") {
          settled = true;
          window.clearTimeout(timer);
          resolve();
        }
      };
      if (typeof video.requestVideoFrameCallback === "function") {
        video.requestVideoFrameCallback(finish);
      } else {
        video.onloadeddata = finish;
      }
      void video
        .play()
        .then(() => { if (typeof video.requestVideoFrameCallback !== "function") finish(); })
        .catch(() => {
          /* wait for loadedmetadata / loadeddata */
        });
    });

    const rawW = video.videoWidth;
    const rawH = video.videoHeight;
    const scale = Math.min(1, MAX_CAPTURE_SIDE_PX / Math.max(rawW, rawH));
    const width = Math.max(1, Math.round(rawW * scale));
    const height = Math.max(1, Math.round(rawH * scale));

    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      throw Object.assign(new Error("Canvas unavailable"), { name: "NotReadableError" });
    }
    ctx.drawImage(video, 0, 0, width, height);

    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob((b) => {
        if (b && b.size > 0) {
          resolve(b);
        } else {
          reject(Object.assign(new Error("Empty capture blob"), { name: "NotReadableError" }));
        }
      }, "image/png");
    });

    return { blob, width, height };
  } finally {
    try {
      video.pause();
      video.srcObject = null;
    } catch {
      /* ignore cleanup error */
    }
  }
}

/**
 * Thực hiện chụp đúng 1 khung hình tĩnh từ `getDisplayMedia` và dừng ngay lập tức
 * mọi media tracks trong khối `finally` để trình duyệt kết thúc chia sẻ màn hình.
 */
export async function captureScreenStillFrame(
  deps?: ScreenCaptureDeps,
): Promise<CapturedScreenFrame> {
  const isSecure =
    deps?.isSecureContext !== undefined
      ? deps.isSecureContext
      : typeof window !== "undefined"
        ? Boolean(window.isSecureContext)
        : false;

  const getDisplayMediaFn =
    deps?.getDisplayMedia ??
    (typeof navigator !== "undefined" &&
    typeof navigator.mediaDevices?.getDisplayMedia === "function"
      ? navigator.mediaDevices.getDisplayMedia.bind(navigator.mediaDevices)
      : undefined);

  if (!isSecure || !getDisplayMediaFn) {
    throw Object.assign(new Error("Screen capture API unsupported"), {
      name: "UnsupportedScreenCaptureError",
    });
  }

  let stream: MediaStream | null = null;
  let stoppedTracks = 0;

  try {
    stream = await getDisplayMediaFn({
      video: true,
      audio: false,
    });

    const extractFn = deps?.extractFrameFromStream ?? defaultExtractFrameFromStream;
    const { blob, width, height } = await extractFn(stream);

    stoppedTracks = stopAllMediaStreamTracks(stream);
    stream = null;

    const ts = (deps?.now ?? Date.now)();
    const fileName = `chup-man-hinh-de-toan-${ts}.png`;
    const file = new File([blob], fileName, {
      type: "image/png",
      lastModified: ts,
    });
    const makeUrl =
      deps?.createObjectURL ??
      (typeof URL !== "undefined" && typeof URL.createObjectURL === "function"
        ? URL.createObjectURL.bind(URL)
        : () => "");
    const previewUrl = makeUrl(file);

    return {
      file,
      previewUrl,
      width,
      height,
      stoppedTracks,
    };
  } finally {
    if (stream) {
      stoppedTracks += stopAllMediaStreamTracks(stream);
    }
  }
}
