import { useCallback, useEffect, useRef, useState } from "react";
import {
  IconCamera,
  IconCameraOff,
  IconCheck,
  IconClose,
  IconFitContain,
  IconFitCover,
  IconImage,
  IconNext,
  IconPrev,
  IconSwitchCamera,
  IconTrash,
  IconZoomIn,
  IconZoomOut,
} from "./icons";
import { PhotoFanStack, type CapturedSessionPhoto } from "./PhotoFanStack";

/**
 * Máy ảnh trực tiếp Camera-First & Photo Fan Stack (§4–§12):
 * - Chỉ khởi động khi người học bấm “Chụp ảnh đề bài”; không bao giờ chạy lúc tải trang.
 * - Mobile/tablet (<= 820px hoặc cao <= 560px): toàn màn hình nền tối `#0b0c0e`, mặc định `Toàn khung` (`contain`)
 *   và có tùy chọn `Tràn màn` (`cover`), nút chụp tròn trắng chính giữa phía dưới, chụp liên tiếp nhiều ảnh.
 * - Desktop: hộp thoại sáng gọn 576px, nút chụp vòng nhẫn mực + đĩa tròn giữa, Photo Fan Stack xòe mượt khi hover/focus,
 *   nút `Xong` cố định không lặp số lượng ảnh và không bị chồng lấn bởi Fan Stack.
 * - Ảnh chụp luôn lấy từ khung cảm biến đầy đủ (`videoWidth × videoHeight`), tạo thumbnail riêng cho Fan Stack
 *   và giữ nguyên `File` gốc cùng `fullUrl` cho Photo Viewer (Zoom 100%–300%, Pan, Prev/Next, Chụp lại, Xóa + Hoàn tác 5s).
 */

export type CameraSupport = { ok: true } | { ok: false; message: string };

export type CameraErrorCode =
  | "permission_denied"
  | "not_found"
  | "unavailable"
  | "unsupported"
  | "unknown";

export interface CameraErrorInfo {
  code: CameraErrorCode;
  title: string;
  description: string;
  canRetry: boolean;
}

export type CameraDeviceKind = "phone" | "tablet" | "desktop" | "unknown";

export interface CameraDeviceSignals {
  userAgentDataMobile?: boolean;
  userAgentDataPlatform?: string;
  userAgent?: string;
  platform?: string;
  maxTouchPoints?: number;
  anyCoarsePointer?: boolean;
}

export type CameraTarget =
  | { kind: "default" }
  | { kind: "facing"; facing: "environment" | "user" }
  | { kind: "device"; deviceId: string };

export type CameraFitMode = "contain" | "cover";
export type CameraOrientation = "portrait" | "landscape";

const IDEAL_SIZE = { width: { ideal: 2560 }, height: { ideal: 1920 } } as const;
const IDEAL_PORTRAIT_SIZE = {
  width: { ideal: 1920 },
  height: { ideal: 2560 },
  aspectRatio: { ideal: 0.75 },
} as const;
const THUMB_MAX_DIM = 320;
const UNDO_TIMEOUT_MS = 5000;
const ZOOM_STEPS = [100, 125, 150, 175, 200, 250, 300] as const;

export function cameraSupport(env: {
  isSecureContext?: boolean;
  hasGetUserMedia: boolean;
}): CameraSupport {
  if (env.isSecureContext === false) {
    return {
      ok: false,
      message: "Máy ảnh chỉ dùng được khi trang mở qua kết nối bảo mật (HTTPS). Em chọn ảnh từ máy nhé.",
    };
  }
  if (!env.hasGetUserMedia) {
    return {
      ok: false,
      message: "Trình duyệt này không hỗ trợ mở máy ảnh trực tiếp. Em chọn ảnh từ máy nhé.",
    };
  }
  return { ok: true };
}

export function classifySupportError(env: {
  isSecureContext?: boolean;
  hasGetUserMedia: boolean;
}): CameraErrorInfo | null {
  if (env.isSecureContext === false) {
    return {
      code: "unsupported",
      title: "Cần kết nối bảo mật (HTTPS)",
      description:
        "Trình duyệt chỉ cho phép mở camera trực tiếp trên kết nối HTTPS hoặc localhost. Hãy chọn ảnh đề bài có sẵn từ thiết bị.",
      canRetry: false,
    };
  }
  if (!env.hasGetUserMedia) {
    return {
      code: "unsupported",
      title: "Trình duyệt không hỗ trợ chụp trực tiếp",
      description:
        "Trình duyệt hiện tại không cung cấp quyền truy cập camera trực tiếp. Hãy chọn ảnh đề bài có sẵn từ thiết bị.",
      canRetry: false,
    };
  }
  return null;
}

/**
 * Phân loại lỗi camera thành 5 nhóm rõ ràng, tiêu đề và mô tả không lặp ý (§5–§7):
 * 1. `permission_denied`  2. `not_found`  3. `unavailable`  4. `unsupported`  5. `unknown`.
 */
export function classifyCameraError(err: unknown): CameraErrorInfo {
  const name = (err as { name?: string } | null)?.name ?? "";
  switch (name) {
    case "NotAllowedError":
    case "PermissionDeniedError":
    case "SecurityError":
      return {
        code: "permission_denied",
        title: "Chưa có quyền truy cập máy ảnh",
        description:
          "Hãy cho phép quyền sử dụng camera trên trình duyệt rồi thử lại, hoặc chọn ảnh có sẵn.",
        canRetry: true,
      };
    case "NotFoundError":
    case "DevicesNotFoundError":
      return {
        code: "not_found",
        title: "Không tìm thấy máy ảnh",
        description:
          "Không phát hiện thiết bị ghi hình trên máy này. Hãy chọn ảnh đề bài có sẵn từ thiết bị.",
        canRetry: false,
      };
    case "NotReadableError":
    case "TrackStartError":
    case "OverconstrainedError":
    case "AbortError":
      return {
        code: "unavailable",
        title: "Không thể mở máy ảnh",
        description:
          "Không nhận được tín hiệu từ camera. Hãy đóng ứng dụng khác đang dùng camera rồi thử lại, hoặc chọn ảnh có sẵn.",
        canRetry: true,
      };
    default:
      return {
        code: "unknown",
        title: "Không thể mở máy ảnh",
        description:
          "Kiểm tra kết nối thiết bị hoặc quyền truy cập camera, hoặc chọn ảnh đề bài có sẵn.",
        canRetry: true,
      };
  }
}

/**
 * Thông báo lỗi máy ảnh ngắn, trung tính, phân biệt rõ 4 nhóm trạng thái (§7):
 * 1. Từ chối quyền  2. Không tìm thấy camera  3. Thiết bị không khả dụng  4. Lỗi chưa xác định.
 */
export function cameraErrorMessage(err: unknown): string {
  const name = (err as { name?: string } | null)?.name ?? "";
  switch (name) {
    case "NotAllowedError":
    case "PermissionDeniedError":
    case "SecurityError":
      return "Quyền truy cập máy ảnh đã bị từ chối. Em cấp quyền máy ảnh trong trình duyệt hoặc chọn ảnh từ máy.";
    case "NotFoundError":
    case "DevicesNotFoundError":
      return "Không tìm thấy máy ảnh trên thiết bị này. Em chọn ảnh từ máy nhé.";
    case "NotReadableError":
    case "TrackStartError":
    case "OverconstrainedError":
      return "Máy ảnh hiện không khả dụng. Em thử lại hoặc chọn ảnh từ máy.";
    default:
      return "Không mở được máy ảnh do lỗi chưa xác định. Em thử lại hoặc chọn ảnh từ máy.";
  }
}

export function cameraErrorTitle(errMessage: string): string {
  if (/Không tìm thấy máy ảnh/i.test(errMessage)) {
    return "Không tìm thấy máy ảnh";
  }
  if (/từ chối|quyền/i.test(errMessage)) {
    return "Chưa có quyền truy cập máy ảnh";
  }
  if (/không hỗ trợ/i.test(errMessage)) {
    return "Trình duyệt không hỗ trợ chụp trực tiếp";
  }
  return "Không thể mở máy ảnh";
}

/**
 * Phân loại thiết bị thuần hàm (`phone` | `tablet` | `desktop` | `unknown`) từ các tín hiệu trình duyệt (§2, §3):
 * - Tuyệt đối không dùng kích thước viewport (`window.innerWidth`/`innerHeight`) hay tỷ lệ thu phóng (`devicePixelRatio`).
 * - Hỗ trợ nhận diện iPadOS chạy Safari ở chế độ desktop (`Macintosh`/`MacIntel` + `maxTouchPoints > 1`).
 * - Hỗ trợ nhận diện Android tablet (có `Android` nhưng không có `Mobile` trong User-Agent).
 * - Không nhầm laptop Windows/Linux/ChromeOS có màn hình cảm ứng thành điện thoại hay máy tính bảng.
 */
export function classifyCameraDevice(sig?: CameraDeviceSignals): CameraDeviceKind {
  if (!sig) return "unknown";
  const ua = (sig.userAgent ?? "").trim();
  const plat = (sig.platform ?? "").trim();
  const uaPlat = (sig.userAgentDataPlatform ?? "").trim();
  const touchPoints = sig.maxTouchPoints ?? 0;

  // 1. Điện thoại iOS tường minh (iPhone / iPod): phải kiểm tra trước Macintosh vì UA iPhone chứa "like Mac OS X"
  if (
    /\b(iPhone|iPod|Windows Phone|IEMobile|Opera Mini|BlackBerry|BB10)\b/i.test(ua) ||
    /\b(iPhone|iPod)\b/i.test(plat) ||
    /^iOS$/i.test(uaPlat)
  ) {
    return "phone";
  }

  // 2. iPad tường minh hoặc iPadOS Safari chế độ desktop (Macintosh/MacIntel có cảm ứng đa điểm > 1):
  if (/\biPad\b/i.test(ua) || /\biPad\b/i.test(plat) || /\biPadOS\b/i.test(uaPlat)) {
    return "tablet";
  }
  const isMacLike =
    /\bMacintosh\b/i.test(ua) ||
    /\b(MacIntel|MacPPC|Mac68K|Macintosh)\b/i.test(plat) ||
    /^macOS$/i.test(uaPlat);
  if (isMacLike && touchPoints > 1) {
    return "tablet";
  }

  // 3. Máy tính bảng Android hoặc thiết bị bảng chuyên dụng (Kindle/Silk/PlayBook/Tablet):
  const isAndroid = /\bAndroid\b/i.test(ua) || /^Android$/i.test(uaPlat);
  if (/\b(Tablet|PlayBook|Silk|Kindle)\b/i.test(ua)) {
    return "tablet";
  }
  if (isAndroid) {
    if (/\bMobile\b/i.test(ua) || sig.userAgentDataMobile === true) {
      return "phone";
    }
    return "tablet";
  }

  if (sig.userAgentDataMobile === true) {
    return "phone";
  }

  // 4. Desktop / Laptop (Windows, macOS không cảm ứng đa điểm, Linux desktop, ChromeOS):
  const isWindowsDesktop =
    (/\b(Windows NT|Win64|Win32|WOW64)\b/i.test(ua) && !/\bWindows Phone\b/i.test(ua)) ||
    /\b(Win32|Win64|Windows)\b/i.test(plat) ||
    /^Windows$/i.test(uaPlat);
  if (isWindowsDesktop) {
    return "desktop";
  }
  if (isMacLike) {
    return "desktop";
  }
  const isLinuxOrChromeOsDesktop =
    (/\b(X11|CrOS|Linux)\b/i.test(ua) && !isAndroid) ||
    (/\bLinux\b/i.test(plat) && !isAndroid) ||
    /^(Linux|Chrome OS|Chromium OS)$/i.test(uaPlat);
  if (isLinuxOrChromeOsDesktop) {
    return "desktop";
  }

  // 5. Từ khóa Mobile trên UA di động khác:
  if (/\bMobile\b/i.test(ua)) {
    return "phone";
  }

  return "unknown";
}

/**
 * Quy tắc hiển thị điểm vào máy ảnh `Chụp ảnh đề bài` trong menu dấu `+` của Composer (§3, §4):
 * - `phone` hoặc `tablet` -> `true`
 * - `desktop` hoặc `unknown` -> `false`
 */
export function shouldShowCameraEntry(sig?: CameraDeviceSignals): boolean {
  const kind = classifyCameraDevice(sig);
  return kind === "phone" || kind === "tablet";
}

export function readBrowserCameraDeviceSignals(): CameraDeviceSignals {
  if (typeof navigator === "undefined") return {};
  const nav = navigator as Navigator & {
    userAgentData?: { mobile?: boolean; platform?: string };
  };
  const anyCoarsePointer =
    typeof window !== "undefined" && typeof window.matchMedia === "function"
      ? window.matchMedia("(any-pointer: coarse)").matches
      : false;
  return {
    userAgentDataMobile: nav.userAgentData?.mobile,
    userAgentDataPlatform: nav.userAgentData?.platform,
    userAgent: nav.userAgent,
    platform: nav.platform,
    maxTouchPoints: nav.maxTouchPoints,
    anyCoarsePointer,
  };
}

export function detectShowCameraEntry(): boolean {
  return shouldShowCameraEntry(readBrowserCameraDeviceSignals());
}

/** Nhận diện thiết bị di động / tablet theo tín hiệu năng lực thiết bị + UA, không phụ thuộc riêng bề rộng cửa sổ. */
export function isMobileCameraPreferred(sig: CameraDeviceSignals): boolean {
  const kind = classifyCameraDevice(sig);
  if (kind === "phone" || kind === "tablet") return true;
  if (kind === "desktop") return false;
  if (sig.userAgentDataMobile === false) return false;
  return (sig.maxTouchPoints ?? 0) > 0 && Boolean(sig.anyCoarsePointer);
}

export function detectViewportOrientation(): CameraOrientation {
  if (typeof window !== "undefined" && window.innerWidth > 0 && window.innerHeight > 0) {
    return window.innerHeight > window.innerWidth ? "portrait" : "landscape";
  }
  return "landscape";
}

export function shouldUseFullscreenCamera(
  viewport: { width: number; height: number },
  sig: CameraDeviceSignals,
): boolean {
  const { width: w, height: h } = viewport;
  const devicePrefersMobile = isMobileCameraPreferred(sig);
  if (devicePrefersMobile) return true;
  if (w > 0 && h > 0) {
    // Khung cửa sổ quá hẹp/thấp không đủ chỗ cho hộp thoại Desktop 576×543px -> dùng fullscreen
    if (w <= 640 || h <= 560) return true;
    // Khung dọc điện thoại/tablet (vd: 768×1024, 820×1180) -> dùng fullscreen
    if (w <= 820 && h > w) return true;
    // Thiết bị có cảm ứng / con trỏ thô (iPad / Tablet thật xoay ngang 1024×768) -> dùng fullscreen,
    // nhưng cửa sổ Desktop thu nhỏ (vd: 960×720 hoặc 1024×768 không cảm ứng) vẫn giữ Desktop Dialog.
    const hasTouchOrCoarse = (sig.maxTouchPoints ?? 0) > 0 || Boolean(sig.anyCoarsePointer);
    if (hasTouchOrCoarse && w <= 1024 && h <= 1366 && (h >= w || h <= 820)) {
      return true;
    }
  }
  return false;
}

export function detectMobileCameraPreferred(): boolean {
  const w = typeof window !== "undefined" ? window.innerWidth : 0;
  const h = typeof window !== "undefined" ? window.innerHeight : 0;
  return shouldUseFullscreenCamera(
    { width: w, height: h },
    readBrowserCameraDeviceSignals(),
  );
}

export function initialCameraTarget(mobile: boolean): CameraTarget {
  return mobile ? { kind: "facing", facing: "environment" } : { kind: "default" };
}

export function buildCameraConstraints(
  target: CameraTarget,
  orientation?: CameraOrientation,
): MediaStreamConstraints {
  const sizeSpec = orientation === "portrait" ? IDEAL_PORTRAIT_SIZE : IDEAL_SIZE;
  switch (target.kind) {
    case "default":
      return { video: { ...sizeSpec }, audio: false };
    case "facing":
      return { video: { facingMode: { ideal: target.facing }, ...sizeSpec }, audio: false };
    case "device":
      return { video: { deviceId: { exact: target.deviceId }, ...sizeSpec }, audio: false };
  }
}

/** Khi camera sau, tỷ lệ dọc hoặc `deviceId` vừa chọn không khả dụng, lùi về luồng ngang tiêu chuẩn hoặc bất kỳ camera nào dùng được. */
export function fallbackCameraConstraints(err: unknown, target: CameraTarget): MediaStreamConstraints | null {
  const name = (err as { name?: string } | null)?.name ?? "";
  if (name !== "OverconstrainedError" && name !== "NotFoundError") return null;
  if (target.kind !== "default") return { video: { ...IDEAL_SIZE }, audio: false };
  if (name === "OverconstrainedError") return { video: true, audio: false };
  return null;
}

function uniqueIds(ids: readonly string[]): string[] {
  return [...new Set(ids.map((id) => id.trim()).filter(Boolean))];
}

export function canSwitchCamera(
  videoDeviceIds: readonly string[],
  mobile: boolean,
  enumeratedCount?: number,
): boolean {
  const distinct = uniqueIds(videoDeviceIds);
  if (distinct.length > 1) return true;
  if (typeof enumeratedCount === "number" && enumeratedCount <= 1 && distinct.length === enumeratedCount) {
    return false;
  }
  return mobile;
}

export function nextCameraTarget(
  current: CameraTarget,
  activeDeviceId: string,
  videoDeviceIds: readonly string[],
  mobile: boolean,
): CameraTarget {
  const ids = uniqueIds(videoDeviceIds);
  if (ids.length > 1) {
    const curId = activeDeviceId || (current.kind === "device" ? current.deviceId : "");
    const idx = ids.indexOf(curId);
    const nextIdx = idx >= 0 ? (idx + 1) % ids.length : 1;
    return { kind: "device", deviceId: ids[nextIdx]! };
  }
  if (mobile) {
    const nextFacing = current.kind === "facing" && current.facing === "environment" ? "user" : "environment";
    return { kind: "facing", facing: nextFacing };
  }
  return { kind: "default" };
}

export function browserCameraSupport(): CameraSupport {
  const md = typeof navigator !== "undefined" ? navigator.mediaDevices : undefined;
  return cameraSupport({
    isSecureContext: typeof window !== "undefined" ? window.isSecureContext : undefined,
    hasGetUserMedia: typeof md?.getUserMedia === "function",
  });
}

function browserSupportErrorInfo(): CameraErrorInfo | null {
  const md = typeof navigator !== "undefined" ? navigator.mediaDevices : undefined;
  return classifySupportError({
    isSecureContext: typeof window !== "undefined" ? window.isSecureContext : undefined,
    hasGetUserMedia: typeof md?.getUserMedia === "function",
  });
}

function stopStream(stream: MediaStream | null) {
  stream?.getTracks().forEach((t) => t.stop());
}

export function revokeSessionPhotoUrls(photo: CapturedSessionPhoto) {
  try {
    if (photo.fullUrl) URL.revokeObjectURL(photo.fullUrl);
    if (photo.thumbUrl && photo.thumbUrl !== photo.fullUrl) {
      URL.revokeObjectURL(photo.thumbUrl);
    }
  } catch {
    /* ignore in non-browser test env */
  }
}

async function createThumbnailUrl(
  sourceCanvas: HTMLCanvasElement,
  fallbackFullUrl: string,
): Promise<string> {
  const sw = sourceCanvas.width;
  const sh = sourceCanvas.height;
  if (!sw || !sh) return fallbackFullUrl;
  const scale = Math.min(1, THUMB_MAX_DIM / Math.max(sw, sh));
  const tw = Math.max(1, Math.round(sw * scale));
  const th = Math.max(1, Math.round(sh * scale));
  const thumbCanvas = document.createElement("canvas");
  thumbCanvas.width = tw;
  thumbCanvas.height = th;
  const tctx = thumbCanvas.getContext("2d");
  if (!tctx) return fallbackFullUrl;
  tctx.drawImage(sourceCanvas, 0, 0, tw, th);
  return new Promise<string>((resolve) => {
    if (typeof thumbCanvas.toBlob !== "function") {
      resolve(fallbackFullUrl);
      return;
    }
    thumbCanvas.toBlob(
      (thumbBlob) => {
        thumbCanvas.width = 0;
        thumbCanvas.height = 0;
        if (!thumbBlob) {
          resolve(fallbackFullUrl);
          return;
        }
        resolve(URL.createObjectURL(thumbBlob));
      },
      "image/jpeg",
      0.84,
    );
  });
}

export interface PhotoCameraViewProps {
  onCapture(file: File): void;
  onCaptureBatch?(files: File[]): void;
  onPickFile(): void;
  onNativeCamera(): void;
  onRequestClose?(): void;
  photos?: CapturedSessionPhoto[];
  onPhotosChange?(next: CapturedSessionPhoto[]): void;
  onScreenModeChange?(screen: "camera" | "viewer"): void;
  onMobileModeChange?(isMobile: boolean): void;
  onErrorStateChange?(hasError: boolean): void;
}

interface DeletedPhotoUndoState {
  photo: CapturedSessionPhoto;
  index: number;
}

export function PhotoCameraView({
  onCapture,
  onCaptureBatch,
  onPickFile,
  onRequestClose,
  photos: controlledPhotos,
  onPhotosChange,
  onScreenModeChange,
  onMobileModeChange,
  onErrorStateChange,
}: PhotoCameraViewProps) {
  const [mobile, setMobile] = useState(detectMobileCameraPreferred);
  const [viewportOrientation, setViewportOrientation] = useState<CameraOrientation>(
    detectViewportOrientation,
  );
  const [target, setTarget] = useState<CameraTarget>(() => initialCameraTarget(mobile));
  const [attempt, setAttempt] = useState(0);
  const [videoIds, setVideoIds] = useState<string[]>([]);
  const [enumeratedCount, setEnumeratedCount] = useState<number | undefined>(undefined);
  const [activeDeviceId, setActiveDeviceId] = useState("");
  const [ready, setReady] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [errorInfo, setErrorInfo] = useState<CameraErrorInfo | null>(null);
  const [fitMode, setFitMode] = useState<CameraFitMode>("contain");
  const [shutterFlash, setShutterFlash] = useState(false);
  const [justShotPulse, setJustShotPulse] = useState(false);
  const [streamAspect, setStreamAspect] = useState<string>(() =>
    detectViewportOrientation() === "portrait" ? "3 / 4" : "4 / 3",
  );
  const [videoDims, setVideoDims] = useState<{ width: number; height: number }>({
    width: 0,
    height: 0,
  });
  const orientationRef = useRef<CameraOrientation>(viewportOrientation);

  const [internalPhotos, setInternalPhotos] = useState<CapturedSessionPhoto[]>([]);
  const photos = controlledPhotos ?? internalPhotos;
  const photosRef = useRef<CapturedSessionPhoto[]>(photos);
  photosRef.current = photos;

  const updatePhotos = useCallback(
    (updater: (prev: CapturedSessionPhoto[]) => CapturedSessionPhoto[]) => {
      const next = updater(photosRef.current);
      photosRef.current = next;
      if (onPhotosChange) {
        onPhotosChange(next);
      } else {
        setInternalPhotos(next);
      }
    },
    [onPhotosChange],
  );

  // Viewer & Mobile Tray state
  const [viewerIndex, setViewerIndex] = useState<number | null>(null);
  const [mobileTrayOpen, setMobileTrayOpen] = useState(false);
  const [traySelectedIndex, setTraySelectedIndex] = useState(0);
  const [retakeTargetId, setRetakeTargetId] = useState<string | null>(null);
  const [zoomPercent, setZoomPercent] = useState<number>(100);
  const [panOffset, setPanOffset] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDraggingPan, setIsDraggingPan] = useState(false);
  const dragStartRef = useRef<{ startX: number; startY: number; origX: number; origY: number } | null>(null);

  // Undo delete state (5s)
  const [undoState, setUndoState] = useState<DeletedPhotoUndoState | null>(null);
  const undoTimerRef = useRef<number | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const shotCounterRef = useRef(0);

  const clearUndoTimer = useCallback(() => {
    if (undoTimerRef.current !== null) {
      window.clearTimeout(undoTimerRef.current);
      undoTimerRef.current = null;
    }
  }, []);

  const finalizePendingUndo = useCallback(() => {
    clearUndoTimer();
    setUndoState((prev) => {
      if (prev) {
        revokeSessionPhotoUrls(prev.photo);
      }
      return null;
    });
  }, [clearUndoTimer]);

  const syncVideoDimensions = useCallback(() => {
    const v = videoRef.current;
    if (v && v.videoWidth > 0 && v.videoHeight > 0) {
      setVideoDims({ width: v.videoWidth, height: v.videoHeight });
      setStreamAspect(`${v.videoWidth} / ${v.videoHeight}`);
      return;
    }
    const track = streamRef.current?.getVideoTracks?.()[0];
    const settings = track?.getSettings?.();
    if (settings?.width && settings?.height && settings.width > 0 && settings.height > 0) {
      setVideoDims({ width: settings.width, height: settings.height });
      setStreamAspect(`${settings.width} / ${settings.height}`);
    }
  }, []);

  function releaseCurrentStream() {
    stopStream(streamRef.current);
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  }

  useEffect(() => {
    onMobileModeChange?.(mobile);
  }, [mobile, onMobileModeChange]);

  useEffect(() => {
    onErrorStateChange?.(Boolean(errorInfo));
  }, [errorInfo, onErrorStateChange]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const onResize = () => {
      const nextMobile = detectMobileCameraPreferred();
      const nextOrientation = detectViewportOrientation();
      setMobile(nextMobile);
      if (nextOrientation !== orientationRef.current) {
        orientationRef.current = nextOrientation;
        setViewportOrientation(nextOrientation);
        const track = streamRef.current?.getVideoTracks?.()[0];
        if (track && typeof track.applyConstraints === "function") {
          const nextSize = nextOrientation === "portrait" ? IDEAL_PORTRAIT_SIZE : IDEAL_SIZE;
          void track.applyConstraints({ ...nextSize }).catch(() => undefined);
        }
      }
      const v = videoRef.current;
      if (v && v.videoWidth > 0 && v.videoHeight > 0) {
        setVideoDims({ width: v.videoWidth, height: v.videoHeight });
        setStreamAspect(`${v.videoWidth} / ${v.videoHeight}`);
      } else {
        setStreamAspect(nextOrientation === "portrait" ? "3 / 4" : "4 / 3");
      }
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    onScreenModeChange?.(viewerIndex !== null ? "viewer" : "camera");
  }, [onScreenModeChange, viewerIndex]);

  useEffect(() => {
    const supportErr = browserSupportErrorInfo();
    if (supportErr) {
      setErrorInfo(supportErr);
      setReady(false);
      setSwitching(false);
      return;
    }

    let cancelled = false;
    setErrorInfo(null);
    setReady(false);

    async function openCamera() {
      releaseCurrentStream();
      const curOrientation = detectViewportOrientation();
      orientationRef.current = curOrientation;
      setViewportOrientation(curOrientation);

      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia(
          buildCameraConstraints(target, curOrientation),
        );
      } catch (firstErr) {
        const fb = fallbackCameraConstraints(firstErr, target);
        if (!fb || cancelled) {
          if (!cancelled) {
            setErrorInfo(classifyCameraError(firstErr));
            setSwitching(false);
          }
          return;
        }
        try {
          stream = await navigator.mediaDevices.getUserMedia(fb);
        } catch (secondErr) {
          if (!cancelled) {
            setErrorInfo(classifyCameraError(secondErr));
            setSwitching(false);
          }
          return;
        }
      }

      if (cancelled) {
        stopStream(stream);
        return;
      }

      streamRef.current = stream;
      const track = stream.getVideoTracks()[0];
      const settings = track?.getSettings?.();
      const settingsId = settings?.deviceId ?? "";
      setActiveDeviceId(settingsId);
      if (settings?.width && settings?.height && settings.width > 0 && settings.height > 0) {
        setVideoDims({ width: settings.width, height: settings.height });
        setStreamAspect(`${settings.width} / ${settings.height}`);
      }

      if (typeof navigator.mediaDevices.enumerateDevices === "function") {
        navigator.mediaDevices
          .enumerateDevices()
          .then((list) => {
            if (cancelled) return;
            const vids = list.filter((d) => d.kind === "videoinput");
            setEnumeratedCount(vids.length);
            setVideoIds(vids.map((d) => d.deviceId));
          })
          .catch(() => undefined);
      }

      const v = videoRef.current;
      if (v) {
        v.srcObject = stream;
        void v
          .play()
          .then(() => {
            if (!cancelled && v.videoWidth > 0 && v.videoHeight > 0) {
              setReady(true);
              setVideoDims({ width: v.videoWidth, height: v.videoHeight });
              setStreamAspect(`${v.videoWidth} / ${v.videoHeight}`);
            }
          })
          .catch(() => undefined);
      }
      setSwitching(false);
    }

    void openCamera();

    return () => {
      cancelled = true;
      releaseCurrentStream();
      clearUndoTimer();
    };
  }, [target, attempt, clearUndoTimer]);

  // Khi quay về từ Viewer, đổi giữa mobile/desktop, hoặc hồi phục sau trạng thái lỗi (errorInfo -> null), gắn lại stream vào thẻ <video>
  useEffect(() => {
    const v = videoRef.current;
    if (viewerIndex === null && errorInfo === null && v && streamRef.current) {
      if (v.srcObject !== streamRef.current) {
        v.srcObject = streamRef.current;
        void v
          .play()
          .then(() => {
            if (v.videoWidth > 0 && v.videoHeight > 0) {
              setReady(true);
              setVideoDims({ width: v.videoWidth, height: v.videoHeight });
              setStreamAspect(`${v.videoWidth} / ${v.videoHeight}`);
            }
          })
          .catch(() => undefined);
      }
    }
  }, [viewerIndex, errorInfo, mobile]);

  function switchCamera() {
    if (switching) return;
    releaseCurrentStream();
    setSwitching(true);
    setTarget((cur) => nextCameraTarget(cur, activeDeviceId, videoIds, mobile));
  }

  function retryCamera() {
    releaseCurrentStream();
    setErrorInfo(null);
    setReady(false);
    setTarget(initialCameraTarget(mobile));
    setAttempt((n) => n + 1);
  }

  function handlePickFile() {
    releaseCurrentStream();
    onPickFile();
  }

  function toggleFitMode() {
    setFitMode((m) => (m === "contain" ? "cover" : "contain"));
  }

  function capture() {
    const v = videoRef.current;
    if (!v || !v.videoWidth || !v.videoHeight) return;
    const width = v.videoWidth;
    const height = v.videoHeight;
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    // Luôn chụp toàn bộ khung cảm biến gốc (`videoWidth × videoHeight`), không cắt theo chế độ hiển thị preview.
    ctx.drawImage(v, 0, 0, width, height);

    setShutterFlash(true);
    setJustShotPulse(true);
    window.setTimeout(() => setShutterFlash(false), 110);
    window.setTimeout(() => setJustShotPulse(false), 260);

    canvas.toBlob(
      async (blob) => {
        if (!blob) {
          canvas.width = 0;
          canvas.height = 0;
          setErrorInfo({
            code: "unknown",
            title: "Không thể chụp khung hình",
            description: "Hãy thử chụp lại hoặc chọn ảnh đề bài có sẵn từ thiết bị.",
            canRetry: true,
          });
          return;
        }
        shotCounterRef.current += 1;
        const seqNum = shotCounterRef.current;
        const ts = Date.now();
        const file = new File([blob], `anh-de-${ts}-${seqNum}.jpg`, { type: "image/jpeg" });
        const fullUrl = URL.createObjectURL(blob);
        const thumbUrl = await createThumbnailUrl(canvas, fullUrl);
        canvas.width = 0;
        canvas.height = 0;

        const newItem: CapturedSessionPhoto = {
          id: `cam-shot-${ts}-${seqNum}`,
          file,
          fullUrl,
          thumbUrl,
          width,
          height,
          createdAt: ts,
        };

        if (retakeTargetId) {
          const targetId = retakeTargetId;
          setRetakeTargetId(null);
          updatePhotos((prev) => {
            const idx = prev.findIndex((p) => p.id === targetId);
            if (idx === -1) return [...prev, newItem];
            const replaced = prev[idx];
            if (replaced) revokeSessionPhotoUrls(replaced);
            const copy = [...prev];
            copy[idx] = newItem;
            setTraySelectedIndex(idx);
            return copy;
          });
        } else {
          updatePhotos((prev) => {
            const next = [...prev, newItem];
            setTraySelectedIndex(next.length - 1);
            return next;
          });
        }
      },
      "image/jpeg",
      0.94,
    );
  }

  function handleCommitSession() {
    const current = photosRef.current;
    if (current.length === 0) return;
    finalizePendingUndo();
    const files = current.map((p) => p.file);
    current.forEach((p) => revokeSessionPhotoUrls(p));
    updatePhotos(() => []);
    releaseCurrentStream();
    if (onCaptureBatch) {
      onCaptureBatch(files);
    } else {
      files.forEach((f) => onCapture(f));
    }
  }

  function openViewerAt(index: number) {
    if (index < 0 || index >= photos.length) return;
    setMobileTrayOpen(false);
    setZoomPercent(100);
    setPanOffset({ x: 0, y: 0 });
    setViewerIndex(index);
  }

  function closeViewer() {
    setViewerIndex(null);
    setZoomPercent(100);
    setPanOffset({ x: 0, y: 0 });
  }

  function handleDeletePhotoAt(index: number) {
    const targetPhoto = photos[index];
    if (!targetPhoto) return;

    finalizePendingUndo();
    setUndoState({ photo: targetPhoto, index });
    undoTimerRef.current = window.setTimeout(() => {
      setUndoState((prev) => {
        if (prev) revokeSessionPhotoUrls(prev.photo);
        return null;
      });
      undoTimerRef.current = null;
    }, UNDO_TIMEOUT_MS);

    const nextLength = photos.length - 1;
    updatePhotos((prev) => prev.filter((_, i) => i !== index));

    if (nextLength <= 0) {
      setViewerIndex(null);
      setMobileTrayOpen(false);
      setTraySelectedIndex(0);
    } else {
      setTraySelectedIndex((cur) => Math.min(cur, nextLength - 1));
      if (viewerIndex !== null) {
        setViewerIndex(Math.min(index, nextLength - 1));
        setZoomPercent(100);
        setPanOffset({ x: 0, y: 0 });
      }
    }
  }

  function handleUndoDelete() {
    if (!undoState) return;
    clearUndoTimer();
    const { photo, index } = undoState;
    setUndoState(null);
    const nextIdx = Math.max(0, Math.min(index, photosRef.current.length));
    updatePhotos((prev) => {
      const clampedIndex = Math.max(0, Math.min(index, prev.length));
      const copy = [...prev];
      copy.splice(clampedIndex, 0, photo);
      return copy;
    });
    setTraySelectedIndex(nextIdx);
    if (viewerIndex !== null) {
      setViewerIndex(nextIdx);
    }
  }

  function handleStartRetake(index: number) {
    const targetPhoto = photos[index];
    if (!targetPhoto) return;
    setRetakeTargetId(targetPhoto.id);
    setViewerIndex(null);
    setMobileTrayOpen(false);
    setZoomPercent(100);
    setPanOffset({ x: 0, y: 0 });
  }

  function stepZoom(direction: "in" | "out" | "cycle") {
    setZoomPercent((cur) => {
      const idx = ZOOM_STEPS.indexOf(cur as (typeof ZOOM_STEPS)[number]);
      let next: number = cur;
      if (direction === "cycle") {
        next = cur === 100 ? 175 : 100;
      } else if (direction === "in") {
        next = ZOOM_STEPS[Math.min(ZOOM_STEPS.length - 1, Math.max(0, idx) + 1)] ?? 300;
      } else {
        next = ZOOM_STEPS[Math.max(0, idx - 1)] ?? 100;
      }
      if (next === 100) {
        setPanOffset({ x: 0, y: 0 });
      }
      return next;
    });
  }

  const showSwitch = canSwitchCamera(videoIds, mobile, enumeratedCount);
  const currentViewerPhoto = viewerIndex !== null ? photos[viewerIndex] ?? null : null;

  /* ── 1. HIGH-RES LIGHTBOX VIEWER (§10) ──────────────────────────────────── */
  if (currentViewerPhoto && viewerIndex !== null) {
    const scale = zoomPercent / 100;
    const positionLabel =
      photos.length === 1
        ? "Ảnh đã chụp"
        : `Ảnh thứ ${viewerIndex + 1} trong ${photos.length} ảnh`;

    return (
      <div
        id="photo-viewer-panel"
        className="photo-viewer lightbox-card"
        data-photo-screen="viewer"
      >
        <div className="lightbox-header">
          <div className="lightbox-title" aria-live="polite">
            <span id="viewer-photo-indicator" className="photo-viewer-position">
              {positionLabel}
            </span>
            <span className="photo-viewer-dims">
              {" · "}
              {currentViewerPhoto.width}×{currentViewerPhoto.height}
            </span>
          </div>

          <div className="lightbox-head-controls">
            <div className="zoom-toolbar photo-viewer-zoom-group" role="group" aria-label="Thu phóng ảnh">
              <button
                type="button"
                id="btn-viewer-zoom-out"
                className="zoom-btn photo-viewer-zoom-btn"
                onClick={() => stepZoom("out")}
                disabled={zoomPercent <= 100}
                aria-label="Thu nhỏ ảnh"
                title="Thu nhỏ"
              >
                <IconZoomOut size={15} />
              </button>
              <button
                type="button"
                id="btn-viewer-zoom-reset"
                className="zoom-readout photo-viewer-zoom-readout"
                onClick={() => stepZoom("cycle")}
                aria-label="Đổi mức phóng đại"
                title="Đặt lại 100% hoặc phóng 175%"
              >
                {zoomPercent}%
              </button>
              <button
                type="button"
                id="btn-viewer-zoom-in"
                className="zoom-btn photo-viewer-zoom-btn"
                onClick={() => stepZoom("in")}
                disabled={zoomPercent >= 300}
                aria-label="Phóng to ảnh"
                title="Phóng to kiểm tra chữ nhỏ"
              >
                <IconZoomIn size={15} />
              </button>
            </div>

            <button
              type="button"
              id="btn-viewer-close"
              className="dialog-close-btn"
              onClick={closeViewer}
              aria-label="Đóng trình xem ảnh"
            >
              <IconClose size={18} />
            </button>
          </div>
        </div>

        <div
          id="photo-viewer-stage"
          className={
            zoomPercent > 100
              ? isDraggingPan
                ? "photo-viewer-stage lightbox-stage is-zoomed is-dragging"
                : "photo-viewer-stage lightbox-stage is-zoomed"
              : "photo-viewer-stage lightbox-stage"
          }
          data-zoom={String(zoomPercent)}
          onDoubleClick={() => stepZoom("cycle")}
          onWheel={(e) => {
            if (e.deltaY < 0) stepZoom("in");
            else if (e.deltaY > 0) stepZoom("out");
          }}
          onPointerDown={(e) => {
            if (zoomPercent <= 100) return;
            setIsDraggingPan(true);
            dragStartRef.current = {
              startX: e.clientX,
              startY: e.clientY,
              origX: panOffset.x,
              origY: panOffset.y,
            };
          }}
          onPointerMove={(e) => {
            if (!isDraggingPan || !dragStartRef.current) return;
            const dx = e.clientX - dragStartRef.current.startX;
            const dy = e.clientY - dragStartRef.current.startY;
            setPanOffset({
              x: Math.max(-280, Math.min(280, dragStartRef.current.origX + dx)),
              y: Math.max(-240, Math.min(240, dragStartRef.current.origY + dy)),
            });
          }}
          onPointerUp={() => {
            setIsDraggingPan(false);
            dragStartRef.current = null;
          }}
          onPointerCancel={() => {
            setIsDraggingPan(false);
            dragStartRef.current = null;
          }}
        >
          {photos.length > 1 && (
            <button
              type="button"
              id="btn-viewer-prev"
              className="lightbox-nav prev photo-viewer-nav is-prev"
              disabled={viewerIndex <= 0}
              onClick={() => openViewerAt(viewerIndex - 1)}
              aria-label="Xem ảnh trước"
            >
              <IconPrev size={18} />
            </button>
          )}

          <div
            className="lightbox-pan-canvas"
            style={{
              transform: `translate3d(${panOffset.x}px, ${panOffset.y}px, 0) scale(${scale})`,
            }}
          >
            <img
              id="photo-viewer-full-img"
              className="photo-viewer-img"
              src={currentViewerPhoto.fullUrl}
              alt={`Ảnh đề ${viewerIndex + 1} độ phân giải gốc`}
              data-viewer-src="full"
              draggable={false}
            />
          </div>

          {photos.length > 1 && (
            <button
              type="button"
              id="btn-viewer-next"
              className="lightbox-nav next photo-viewer-nav is-next"
              disabled={viewerIndex >= photos.length - 1}
              onClick={() => openViewerAt(viewerIndex + 1)}
              aria-label="Xem ảnh tiếp theo"
            >
              <IconNext size={18} />
            </button>
          )}

          {undoState && (
            <div id="photo-undo-bar" className="photo-undo-bar" role="status" aria-live="polite">
              <span>Đã xóa ảnh</span>
              <button
                type="button"
                id="btn-photo-undo-delete"
                className="photo-undo-btn"
                onClick={handleUndoDelete}
              >
                Hoàn tác
              </button>
            </div>
          )}
        </div>

        <div className="lightbox-footer photo-viewer-footer">
          <div className="lightbox-footer-group photo-viewer-actions-left">
            <button
              type="button"
              id="btn-viewer-retake"
              className="secondary-btn"
              onClick={() => handleStartRetake(viewerIndex)}
            >
              <IconCamera size={15} />
              <span>Chụp lại</span>
            </button>
          </div>

          <div className="lightbox-footer-group">
            <button
              type="button"
              id="btn-viewer-delete"
              className="secondary-btn danger-btn"
              onClick={() => handleDeletePhotoAt(viewerIndex)}
            >
              <IconTrash size={15} />
              <span>Xóa ảnh</span>
            </button>
            <button
              type="button"
              id="btn-viewer-back"
              className="primary-pill-btn photo-viewer-back-btn"
              onClick={closeViewer}
            >
              <span>Quay lại máy ảnh</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  const retakeSlotNumber = retakeTargetId
    ? photos.findIndex((p) => p.id === retakeTargetId) + 1
    : 0;
  const safeTrayIdx = Math.max(0, Math.min(traySelectedIndex, Math.max(0, photos.length - 1)));
  const selectedTrayPhoto = photos[safeTrayIdx] ?? photos[photos.length - 1] ?? null;

  /* ── 2. MOBILE & TABLET FULLSCREEN DARK CAMERA (§5, §6, §7, §8) ─────────── */
  if (mobile) {
    if (errorInfo) {
      return (
        <div
          className="photo-camera photo-error mobile-error-screen"
          data-error-code={errorInfo.code}
        >
          <div className="cam-fs-top">
            <button
              type="button"
              id="btn-photo-dialog-close"
              className="cam-glass-btn icon-only"
              onClick={onRequestClose}
              aria-label="Đóng máy ảnh"
            >
              <IconClose size={18} />
            </button>
            <span className="cam-top-spacer" />
          </div>

          <div className="mobile-error-card" role="alert">
            <div className="error-icon-circle">
              <IconCameraOff size={20} />
            </div>
            <h2 className="mobile-error-title">{errorInfo.title}</h2>
            <p className="mobile-error-desc photo-alert">{errorInfo.description}</p>
            <div className="mobile-error-actions">
              <button
                type="button"
                id="btn-photo-pick-fallback"
                className="mobile-error-primary"
                onClick={handlePickFile}
              >
                <IconImage size={16} />
                <span>Chọn ảnh</span>
              </button>
              {errorInfo.canRetry && (
                <button
                  type="button"
                  id="btn-photo-retry-camera"
                  className="mobile-error-secondary"
                  onClick={retryCamera}
                >
                  Thử lại
                </button>
              )}
              {photos.length > 0 && (
                <button
                  type="button"
                  id="btn-photo-done"
                  className="mobile-error-primary"
                  onClick={handleCommitSession}
                >
                  Xong
                </button>
              )}
            </div>
          </div>
          <div className="cam-top-spacer" />
        </div>
      );
    }

    return (
      <div
        className="photo-camera cam-fs-root"
        data-viewport-orientation={viewportOrientation}
        data-stream-aspect={streamAspect}
        data-video-width={videoDims.width || undefined}
        data-video-height={videoDims.height || undefined}
        style={{ "--stream-aspect": streamAspect } as React.CSSProperties}
      >
        <div className="cam-fs-top">
          <button
            type="button"
            id="btn-photo-dialog-close"
            className="cam-glass-btn icon-only"
            onClick={onRequestClose}
            aria-label="Đóng máy ảnh"
          >
            <IconClose size={18} />
          </button>

          {retakeSlotNumber > 0 ? (
            <div id="photo-retake-banner" className="cam-status-pill" role="status">
              <span>Chụp lại ảnh {retakeSlotNumber}</span>
              <button
                type="button"
                id="btn-cancel-retake"
                className="photo-retake-cancel"
                onClick={() => setRetakeTargetId(null)}
                aria-label="Hủy chụp lại"
              >
                <IconClose size={12} />
              </button>
            </div>
          ) : undoState && !mobileTrayOpen ? (
            <div id="photo-undo-bar" className="cam-status-pill" role="status" aria-live="polite">
              <span>Đã xóa ảnh</span>
              <button
                type="button"
                id="btn-photo-undo-delete"
                className="photo-undo-btn"
                onClick={handleUndoDelete}
              >
                Hoàn tác
              </button>
            </div>
          ) : null}

          {photos.length > 0 ? (
            <div className="cam-top-right-tools">
              <button
                type="button"
                id="btn-photo-library"
                className="cam-glass-btn icon-only"
                onClick={handlePickFile}
                aria-label="Chọn ảnh có sẵn từ thiết bị"
                title="Chọn ảnh từ thiết bị"
              >
                <IconImage size={18} />
              </button>
              <button
                type="button"
                id="btn-photo-fit-mode"
                className="cam-glass-btn icon-only"
                data-fit-mode={fitMode}
                onClick={toggleFitMode}
                aria-label={
                  fitMode === "contain"
                    ? "Khung ngắm: Toàn khung. Chạm để đổi sang Tràn màn"
                    : "Khung ngắm: Tràn màn. Chạm để đổi sang Toàn khung"
                }
                title={
                  fitMode === "contain"
                    ? "Đang Toàn khung (không cắt chữ sát mép)"
                    : "Đang Tràn màn"
                }
              >
                {fitMode === "contain" ? <IconFitContain size={16} /> : <IconFitCover size={16} />}
              </button>
              {showSwitch && (
                <button
                  type="button"
                  id="btn-photo-switch-camera"
                  className="cam-glass-btn icon-only"
                  onClick={switchCamera}
                  disabled={switching}
                  aria-label="Đổi máy ảnh trước hoặc sau"
                  title="Đổi máy ảnh"
                >
                  <IconSwitchCamera size={18} />
                </button>
              )}
            </div>
          ) : (
            <button
              type="button"
              id="btn-photo-fit-mode"
              className="cam-glass-btn pill"
              data-fit-mode={fitMode}
              onClick={toggleFitMode}
              aria-label={
                fitMode === "contain"
                  ? "Khung ngắm: Toàn khung. Chạm để đổi sang Tràn màn"
                  : "Khung ngắm: Tràn màn. Chạm để đổi sang Toàn khung"
              }
            >
              {fitMode === "contain" ? <IconFitContain size={16} /> : <IconFitCover size={16} />}
              <span>{fitMode === "contain" ? "Toàn khung" : "Tràn màn"}</span>
            </button>
          )}
        </div>

        <div className="cam-fs-stage photo-camera-stage">
          <div className="camera-sensor-box">
            <video
              ref={videoRef}
              className={
                fitMode === "cover"
                  ? "photo-camera-video is-cover"
                  : "photo-camera-video is-contain"
              }
              data-fit-mode={fitMode}
              playsInline
              muted
              autoPlay
              aria-label="Khung ngắm máy ảnh đề bài"
              onLoadedMetadata={() => {
                setReady(true);
                syncVideoDimensions();
              }}
              onResize={syncVideoDimensions}
              onLoadedData={() => {
                setReady(true);
                syncVideoDimensions();
              }}
            />
            <div className={shutterFlash ? "shutter-flash active" : "shutter-flash"} />
          </div>

          {!ready && (
            <p className="photo-camera-loading" role="status" aria-live="polite">
              Đang mở máy ảnh...
            </p>
          )}
        </div>

        <div className="cam-fs-bottom-wrap">
          <div className="cam-fs-bottom photo-camera-bar">
            <div className="cam-slot-left photo-camera-slot-side">
              {photos.length > 0 ? (
                <PhotoFanStack
                  photos={photos}
                  isMobile={true}
                  justShotPulse={justShotPulse}
                  onOpenPhoto={openViewerAt}
                  onOpenMobileTray={() => {
                    setTraySelectedIndex(photos.length - 1);
                    setMobileTrayOpen((v) => !v);
                  }}
                />
              ) : (
                <button
                  type="button"
                  id="btn-photo-library"
                  className="cam-round-control"
                  onClick={handlePickFile}
                  aria-label="Chọn ảnh có sẵn từ thiết bị"
                  title="Chọn ảnh từ thiết bị"
                >
                  <IconImage size={18} />
                </button>
              )}
            </div>

            <div className="photo-camera-slot-center">
              <button
                type="button"
                id="btn-photo-capture"
                className="shutter-btn"
                onClick={capture}
                disabled={!ready || switching}
                aria-label={
                  retakeSlotNumber > 0
                    ? `Chụp thay ảnh thứ ${retakeSlotNumber}`
                    : "Chụp ảnh đề bài"
                }
              >
                <span className="shutter-disc" aria-hidden="true" />
              </button>
            </div>

            <div className="cam-slot-right photo-camera-slot-side is-end">
              {photos.length > 0 ? (
                <button
                  type="button"
                  id="btn-photo-done"
                  className="cam-done-btn"
                  onClick={handleCommitSession}
                  aria-label="Xong, đính kèm ảnh vào ô nhập đề bài"
                >
                  <span>Xong</span>
                  <IconCheck size={15} />
                </button>
              ) : showSwitch ? (
                <button
                  type="button"
                  id="btn-photo-switch-camera"
                  className="cam-round-control"
                  onClick={switchCamera}
                  disabled={switching}
                  aria-label="Đổi máy ảnh trước hoặc sau"
                  title="Đổi máy ảnh"
                >
                  <IconSwitchCamera size={18} />
                </button>
              ) : (
                <span className="cam-round-spacer" aria-hidden="true" />
              )}
            </div>
          </div>
        </div>

        {/* Mobile Photo Tray Master–Detail Bottom Sheet (§8) */}
        {mobileTrayOpen && photos.length > 0 && selectedTrayPhoto && (
          <>
            <div
              className="cam-session-drawer-scrim"
              onClick={() => setMobileTrayOpen(false)}
            />
            <div
              id="photo-mobile-tray"
              className="cam-session-drawer photo-mobile-tray"
              role="dialog"
              aria-label="Khay ảnh đã chụp"
            >
              <div className="cam-drawer-header">
                <span className="cam-drawer-title">
                  {photos.length === 1
                    ? "Ảnh đã chụp"
                    : `Ảnh thứ ${safeTrayIdx + 1} trong ${photos.length} ảnh`}
                </span>
                <div className="cam-drawer-head-actions">
                  <button
                    type="button"
                    id="btn-tray-zoom"
                    className="cam-drawer-close"
                    onClick={() => openViewerAt(safeTrayIdx)}
                  >
                    <IconZoomIn size={14} />
                    <span>Phóng to</span>
                  </button>
                  <button
                    type="button"
                    id="btn-mobile-tray-close"
                    className="cam-drawer-close"
                    onClick={() => setMobileTrayOpen(false)}
                  >
                    Đóng
                  </button>
                </div>
              </div>

              <div className="tray-selected-stage">
                {photos.length > 1 && (
                  <button
                    type="button"
                    id="btn-tray-prev"
                    className="tray-stage-nav prev"
                    disabled={safeTrayIdx <= 0}
                    onClick={() => setTraySelectedIndex((i) => Math.max(0, i - 1))}
                    aria-label="Xem ảnh trước trong khay"
                  >
                    <IconPrev size={16} />
                  </button>
                )}
                <img
                  id="tray-selected-img"
                  src={selectedTrayPhoto.fullUrl}
                  alt={`Xem trước đề bài ảnh ${safeTrayIdx + 1}`}
                  onClick={() => openViewerAt(safeTrayIdx)}
                />
                {photos.length > 1 && (
                  <button
                    type="button"
                    id="btn-tray-next"
                    className="tray-stage-nav next"
                    disabled={safeTrayIdx >= photos.length - 1}
                    onClick={() =>
                      setTraySelectedIndex((i) => Math.min(photos.length - 1, i + 1))
                    }
                    aria-label="Xem ảnh tiếp theo trong khay"
                  >
                    <IconNext size={16} />
                  </button>
                )}
              </div>

              <div
                className="tray-thumb-strip"
                role="tablist"
                aria-label="Chọn ảnh trong phiên chụp"
              >
                {photos.map((item, idx) => (
                  <button
                    key={item.id}
                    type="button"
                    id={`btn-tray-open-${idx + 1}`}
                    role="tab"
                    className="tray-thumb-btn"
                    aria-selected={idx === safeTrayIdx ? "true" : "false"}
                    aria-label={`Chọn ảnh thứ ${idx + 1}`}
                    onClick={() => setTraySelectedIndex(idx)}
                  >
                    <img src={item.thumbUrl} alt="" draggable={false} />
                  </button>
                ))}
              </div>

              {undoState && (
                <div className="tray-undo-bar" role="status" aria-live="polite">
                  <span>Đã xóa ảnh khỏi phiên chụp.</span>
                  <button
                    type="button"
                    id="btn-photo-undo-delete"
                    onClick={handleUndoDelete}
                  >
                    Hoàn tác
                  </button>
                </div>
              )}

              <div className="tray-shared-actions">
                <button
                  type="button"
                  id="btn-tray-retake"
                  className="tray-action-btn"
                  onClick={() => handleStartRetake(safeTrayIdx)}
                >
                  <IconCamera size={15} />
                  <span>Chụp lại</span>
                </button>
                <button
                  type="button"
                  id="btn-tray-delete"
                  data-testid={`btn-tray-delete-${safeTrayIdx + 1}`}
                  className="tray-action-btn danger"
                  onClick={() => handleDeletePhotoAt(safeTrayIdx)}
                >
                  <IconTrash size={15} />
                  <span>Xóa ảnh</span>
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    );
  }

  /* ── 3. DESKTOP CAMERA DIALOG (§6, §9) ──────────────────────────────────── */
  if (errorInfo) {
    return (
      <div
        className="photo-camera photo-error desktop-camera-root"
        data-error-code={errorInfo.code}
      >
        <div className="dialog-header">
          <div className="dialog-title-wrap">
            <span className="dialog-title" id="photo-dialog-title">
              Chụp ảnh đề bài
            </span>
          </div>
          <button
            type="button"
            id="btn-photo-dialog-close"
            className="dialog-close-btn"
            onClick={onRequestClose}
            aria-label="Đóng hộp thoại máy ảnh"
          >
            <IconClose size={18} />
          </button>
        </div>

        <div className="desktop-error-body" role="alert">
          <div className="desktop-error-lead">
            <div className="error-icon-circle">
              <IconCameraOff size={20} />
            </div>
            <div className="desktop-error-copy">
              <h3 className="desktop-error-title">{errorInfo.title}</h3>
              <p className="desktop-error-desc photo-alert">{errorInfo.description}</p>
            </div>
          </div>
          <div className="desktop-error-actions">
            {errorInfo.canRetry && (
              <button
                type="button"
                id="btn-photo-retry-camera"
                className="secondary-btn"
                onClick={retryCamera}
              >
                Thử lại
              </button>
            )}
            <button
              type="button"
              id="btn-photo-pick-fallback"
              className="primary-pill-btn"
              onClick={handlePickFile}
            >
              <IconImage size={16} />
              <span>Chọn ảnh</span>
            </button>
            {photos.length > 0 && (
              <button
                type="button"
                id="btn-photo-done"
                className="primary-pill-btn"
                onClick={handleCommitSession}
              >
                <span>Xong</span>
                <IconCheck size={15} />
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="photo-camera desktop-camera-root"
      data-viewport-orientation={viewportOrientation}
      data-stream-aspect={streamAspect}
      data-video-width={videoDims.width || undefined}
      data-video-height={videoDims.height || undefined}
      style={{ "--stream-aspect": streamAspect } as React.CSSProperties}
    >
      <div className="dialog-header">
        <div className="dialog-title-wrap">
          <span className="dialog-title" id="photo-dialog-title">
            Chụp ảnh đề bài
          </span>
          {retakeSlotNumber > 0 && (
            <span id="photo-retake-banner" className="dialog-badge photo-retake-pill" role="status">
              <span>Đang chụp lại ảnh</span>
              <button
                type="button"
                id="btn-cancel-retake"
                className="dialog-badge-cancel"
                onClick={() => setRetakeTargetId(null)}
                aria-label="Hủy chụp lại"
              >
                <IconClose size={11} />
              </button>
            </span>
          )}
        </div>
        <button
          type="button"
          id="btn-photo-dialog-close"
          className="dialog-close-btn"
          onClick={onRequestClose}
          aria-label="Đóng hộp thoại máy ảnh"
        >
          <IconClose size={18} />
        </button>
      </div>

      <div className="dialog-stage-wrap">
        <div className="dialog-video-frame photo-camera-stage">
          <div className="camera-sensor-box">
            <video
              ref={videoRef}
              className={
                fitMode === "cover"
                  ? "photo-camera-video is-cover"
                  : "photo-camera-video is-contain"
              }
              data-fit-mode={fitMode}
              playsInline
              muted
              autoPlay
              aria-label="Khung ngắm máy ảnh đề bài"
              onLoadedMetadata={() => {
                setReady(true);
                syncVideoDimensions();
              }}
              onResize={syncVideoDimensions}
              onLoadedData={() => {
                setReady(true);
                syncVideoDimensions();
              }}
            />
            <div className={shutterFlash ? "shutter-flash active" : "shutter-flash"} />
          </div>

          {!ready && (
            <p className="photo-camera-loading" role="status" aria-live="polite">
              Đang mở máy ảnh...
            </p>
          )}
        </div>
      </div>

      <div className="dialog-footer photo-camera-bar">
        <div className="dialog-left-actions photo-camera-slot-side">
          <button
            type="button"
            id="btn-photo-library"
            className="secondary-btn"
            onClick={handlePickFile}
            aria-label="Chọn ảnh từ máy"
          >
            <IconImage size={18} />
            <span>Chọn ảnh</span>
          </button>
          {showSwitch && (
            <button
              type="button"
              id="btn-photo-switch-camera"
              className="secondary-btn icon-only"
              onClick={switchCamera}
              disabled={switching}
              aria-label="Đổi máy ảnh"
              title="Đổi máy ảnh"
            >
              <IconSwitchCamera size={18} />
            </button>
          )}
          {photos.length > 0 && (
            <button
              type="button"
              id="btn-photo-fit-mode"
              className="secondary-btn icon-only"
              data-fit-mode={fitMode}
              onClick={toggleFitMode}
              aria-label={
                fitMode === "contain"
                  ? "Khung ngắm: Toàn khung. Bấm để đổi sang Tràn màn"
                  : "Khung ngắm: Tràn màn. Bấm để đổi sang Toàn khung"
              }
              title={
                fitMode === "contain"
                  ? "Đang Toàn khung (không cắt chữ sát mép)"
                  : "Đang Tràn màn"
              }
            >
              {fitMode === "contain" ? <IconFitContain size={16} /> : <IconFitCover size={16} />}
            </button>
          )}
        </div>

        <div className="desktop-shutter-group photo-camera-slot-center">
          <button
            type="button"
            id="btn-photo-capture"
            className="desktop-shutter-btn"
            onClick={capture}
            disabled={!ready || switching}
            aria-label={retakeSlotNumber > 0 ? "Chụp thay ảnh" : "Chụp ảnh đề bài"}
          >
            <span className="desktop-shutter-disc" aria-hidden="true" />
          </button>
          <span className="desktop-shutter-caption">
            {retakeSlotNumber > 0 ? "Thay ảnh" : "Chụp ảnh"}
          </span>
        </div>

        <div className="dialog-right-actions photo-camera-slot-side is-end">
          {photos.length > 0 ? (
            <>
              {undoState && (
                <button
                  type="button"
                  id="btn-photo-undo-delete"
                  className="secondary-btn"
                  onClick={handleUndoDelete}
                >
                  Hoàn tác
                </button>
              )}
              <PhotoFanStack
                photos={photos}
                isMobile={false}
                justShotPulse={justShotPulse}
                onOpenPhoto={openViewerAt}
                onOpenMobileTray={() => undefined}
              />
              <button
                type="button"
                id="btn-photo-done"
                className="primary-pill-btn"
                onClick={handleCommitSession}
                aria-label="Xong, đính kèm ảnh vào ô nhập đề bài"
              >
                <span>Xong</span>
                <IconCheck size={15} />
              </button>
            </>
          ) : (
            <>
              {undoState && (
                <button
                  type="button"
                  id="btn-photo-undo-delete"
                  className="secondary-btn"
                  onClick={handleUndoDelete}
                >
                  Hoàn tác xóa
                </button>
              )}
              <button
                type="button"
                id="btn-photo-fit-mode"
                className="secondary-btn"
                data-fit-mode={fitMode}
                onClick={toggleFitMode}
                aria-label={
                  fitMode === "contain"
                    ? "Khung ngắm: Toàn khung. Bấm để đổi sang Tràn màn"
                    : "Khung ngắm: Tràn màn. Bấm để đổi sang Toàn khung"
                }
                title="Đổi chế độ khung ngắm"
              >
                {fitMode === "contain" ? <IconFitContain size={16} /> : <IconFitCover size={16} />}
                <span>{fitMode === "contain" ? "Toàn khung" : "Tràn màn"}</span>
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
