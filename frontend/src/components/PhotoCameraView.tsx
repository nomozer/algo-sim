import { useCallback, useEffect, useRef, useState } from "react";
import {
  IconBack,
  IconCamera,
  IconCheck,
  IconClose,
  IconImage,
  IconNext,
  IconPrev,
  IconReset,
  IconSwitchCamera,
  IconTrash,
  IconZoomIn,
  IconZoomOut,
} from "./icons";
import { PhotoFanStack, type CapturedSessionPhoto } from "./PhotoFanStack";

/**
 * Máy ảnh trực tiếp Camera-First & Photo Fan Stack (§4–§8, §12):
 * - Chỉ khởi động khi người học bấm “Chụp ảnh đề bài”; không bao giờ chạy lúc tải trang.
 * - Mobile/tablet: toàn màn hình, mặc định `Toàn khung` (`contain`) và có tùy chọn `Tràn màn` (`cover`),
 *   nút chụp tròn chính giữa phía dưới, chụp liên tiếp nhiều ảnh trong cùng phiên.
 * - Desktop: hộp thoại gọn 576px, Photo Fan Stack xòe mượt khi hover/focus với hover-bridge 140ms,
 *   nút `Xong` cố định không lặp số lượng ảnh.
 * - Ảnh chụp luôn lấy từ khung cảm biến đầy đủ (`videoWidth × videoHeight`), tạo thumbnail riêng cho Fan Stack
 *   và giữ nguyên `File` gốc cùng `fullUrl` cho Photo Viewer (Zoom 100%–300%, Pan, Prev/Next, Chụp lại, Xóa + Hoàn tác 5s).
 */

export type CameraSupport = { ok: true } | { ok: false; message: string };

export interface CameraDeviceSignals {
  userAgentDataMobile?: boolean;
  userAgent?: string;
  maxTouchPoints?: number;
  anyCoarsePointer?: boolean;
}

export type CameraTarget =
  | { kind: "default" }
  | { kind: "facing"; facing: "environment" | "user" }
  | { kind: "device"; deviceId: string };

export type CameraFitMode = "contain" | "cover";

const IDEAL_SIZE = { width: { ideal: 2560 }, height: { ideal: 1920 } } as const;
const THUMB_MAX_DIM = 320;
const UNDO_TIMEOUT_MS = 5000;
const ZOOM_STEPS = [100, 150, 200, 300] as const;

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

/** Nhận diện thiết bị di động theo tín hiệu năng lực thiết bị + UA, không phụ thuộc riêng bề rộng cửa sổ. */
export function isMobileCameraPreferred(sig: CameraDeviceSignals): boolean {
  if (sig.userAgentDataMobile === true) return true;
  if (sig.userAgentDataMobile === false) return false;
  if (/Android|iPhone|iPad|iPod|Mobile/i.test(sig.userAgent ?? "")) return true;
  return (sig.maxTouchPoints ?? 0) > 0 && Boolean(sig.anyCoarsePointer);
}

export function detectMobileCameraPreferred(): boolean {
  if (typeof navigator === "undefined") return false;
  const nav = navigator as Navigator & { userAgentData?: { mobile?: boolean } };
  const anyCoarsePointer =
    typeof window !== "undefined" && typeof window.matchMedia === "function"
      ? window.matchMedia("(any-pointer: coarse)").matches
      : false;
  const narrowViewport =
    typeof window !== "undefined" && typeof window.innerWidth === "number"
      ? window.innerWidth <= 820
      : false;
  return (
    isMobileCameraPreferred({
      userAgentDataMobile: nav.userAgentData?.mobile,
      userAgent: nav.userAgent,
      maxTouchPoints: nav.maxTouchPoints,
      anyCoarsePointer,
    }) || (narrowViewport && anyCoarsePointer)
  );
}

export function initialCameraTarget(mobile: boolean): CameraTarget {
  return mobile ? { kind: "facing", facing: "environment" } : { kind: "default" };
}

export function buildCameraConstraints(target: CameraTarget): MediaStreamConstraints {
  switch (target.kind) {
    case "default":
      return { video: { ...IDEAL_SIZE }, audio: false };
    case "facing":
      return { video: { facingMode: { ideal: target.facing }, ...IDEAL_SIZE }, audio: false };
    case "device":
      return { video: { deviceId: { exact: target.deviceId }, ...IDEAL_SIZE }, audio: false };
  }
}

/** Khi camera sau hoặc `deviceId` vừa chọn không khả dụng, lùi về bất kỳ camera nào dùng được. */
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
      0.82,
    );
  });
}

export interface PhotoCameraViewProps {
  onCapture(file: File): void;
  onCaptureBatch?(files: File[]): void;
  onPickFile(): void;
  onNativeCamera(): void;
  photos?: CapturedSessionPhoto[];
  onPhotosChange?(next: CapturedSessionPhoto[]): void;
  onScreenModeChange?(screen: "camera" | "viewer"): void;
}

interface DeletedPhotoUndoState {
  photo: CapturedSessionPhoto;
  index: number;
}

export function PhotoCameraView({
  onCapture,
  onCaptureBatch,
  onPickFile,
  onNativeCamera,
  photos: controlledPhotos,
  onPhotosChange,
  onScreenModeChange,
}: PhotoCameraViewProps) {
  const [mobile, setMobile] = useState(detectMobileCameraPreferred);
  const [target, setTarget] = useState<CameraTarget>(() => initialCameraTarget(mobile));
  const [attempt, setAttempt] = useState(0);
  const [videoIds, setVideoIds] = useState<string[]>([]);
  const [enumeratedCount, setEnumeratedCount] = useState<number | undefined>(undefined);
  const [activeDeviceId, setActiveDeviceId] = useState("");
  const [ready, setReady] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fitMode, setFitMode] = useState<CameraFitMode>("contain");
  const [shutterFlash, setShutterFlash] = useState(false);

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

  const support = browserCameraSupport();

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

  function releaseCurrentStream() {
    stopStream(streamRef.current);
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  }

  useEffect(() => {
    if (typeof window === "undefined") return;
    const onResize = () => {
      setMobile(detectMobileCameraPreferred());
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    onScreenModeChange?.(viewerIndex !== null ? "viewer" : "camera");
  }, [onScreenModeChange, viewerIndex]);

  useEffect(() => {
    const check = browserCameraSupport();
    if (!check.ok) {
      setError(check.message);
      setReady(false);
      setSwitching(false);
      return;
    }

    let cancelled = false;
    setError(null);
    setReady(false);

    async function openCamera() {
      releaseCurrentStream();

      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia(buildCameraConstraints(target));
      } catch (firstErr) {
        const fb = fallbackCameraConstraints(firstErr, target);
        if (!fb || cancelled) {
          if (!cancelled) {
            setError(cameraErrorMessage(firstErr));
            setSwitching(false);
          }
          return;
        }
        try {
          stream = await navigator.mediaDevices.getUserMedia(fb);
        } catch (secondErr) {
          if (!cancelled) {
            setError(cameraErrorMessage(secondErr));
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
      const settingsId = track?.getSettings?.()?.deviceId ?? "";
      setActiveDeviceId(settingsId);

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
            if (!cancelled && v.videoWidth > 0) setReady(true);
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

  // Khi quay về từ Viewer, gắn lại stream vào thẻ <video>
  useEffect(() => {
    if (viewerIndex === null && videoRef.current && streamRef.current) {
      if (videoRef.current.srcObject !== streamRef.current) {
        videoRef.current.srcObject = streamRef.current;
        void videoRef.current.play().catch(() => undefined);
      }
    }
  }, [viewerIndex]);

  function switchCamera() {
    if (switching) return;
    releaseCurrentStream();
    setSwitching(true);
    setTarget((cur) => nextCameraTarget(cur, activeDeviceId, videoIds, mobile));
  }

  function retryCamera() {
    releaseCurrentStream();
    setTarget(initialCameraTarget(mobile));
    setAttempt((n) => n + 1);
  }

  function handlePickFile() {
    releaseCurrentStream();
    onPickFile();
  }

  function handleNativeCamera() {
    releaseCurrentStream();
    onNativeCamera();
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
    window.setTimeout(() => setShutterFlash(false), 140);

    canvas.toBlob(
      async (blob) => {
        if (!blob) {
          canvas.width = 0;
          canvas.height = 0;
          setError("Chưa ghi nhận được khung hình. Em thử lại hoặc chọn ảnh từ máy.");
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
            return copy;
          });
        } else {
          updatePhotos((prev) => [...prev, newItem]);
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
    } else if (viewerIndex !== null) {
      setViewerIndex(Math.min(index, nextLength - 1));
      setZoomPercent(100);
      setPanOffset({ x: 0, y: 0 });
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
        next = ZOOM_STEPS[(idx + 1) % ZOOM_STEPS.length] ?? 100;
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

  if (currentViewerPhoto && viewerIndex !== null) {
    const scale = zoomPercent / 100;
    return (
      <div id="photo-viewer-panel" className="photo-viewer" data-photo-screen="viewer">
        <div className="photo-viewer-toolbar">
          <button
            type="button"
            id="btn-viewer-back"
            className="btn-utility photo-viewer-back-btn"
            onClick={closeViewer}
          >
            <IconBack size={16} />
            <span>Quay lại camera</span>
          </button>

          <div className="photo-viewer-meta" aria-live="polite">
            <span id="viewer-photo-indicator" className="photo-viewer-position">
              Ảnh {viewerIndex + 1} / {photos.length}
            </span>
            <span className="photo-viewer-dims">
              {currentViewerPhoto.width}×{currentViewerPhoto.height}
            </span>
          </div>

          <div className="photo-viewer-zoom-group" role="group" aria-label="Thu phóng ảnh">
            <button
              type="button"
              id="btn-viewer-zoom-out"
              className="btn-utility photo-viewer-zoom-btn"
              onClick={() => stepZoom("out")}
              disabled={zoomPercent <= 100}
              aria-label="Thu nhỏ ảnh"
            >
              <IconZoomOut size={15} />
            </button>
            <button
              type="button"
              id="btn-viewer-zoom-reset"
              className="btn-utility photo-viewer-zoom-readout"
              onClick={() => stepZoom("cycle")}
              aria-label="Đổi mức phóng đại"
            >
              {zoomPercent}%
            </button>
            <button
              type="button"
              id="btn-viewer-zoom-in"
              className="btn-utility photo-viewer-zoom-btn"
              onClick={() => stepZoom("in")}
              disabled={zoomPercent >= 300}
              aria-label="Phóng to ảnh"
            >
              <IconZoomIn size={15} />
            </button>
          </div>
        </div>

        <div
          id="photo-viewer-stage"
          className={
            zoomPercent > 100
              ? isDraggingPan
                ? "photo-viewer-stage is-zoomed is-dragging"
                : "photo-viewer-stage is-zoomed"
              : "photo-viewer-stage"
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
              x: Math.max(-260, Math.min(260, dragStartRef.current.origX + dx)),
              y: Math.max(-220, Math.min(220, dragStartRef.current.origY + dy)),
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
              className="btn-utility photo-viewer-nav is-prev"
              disabled={viewerIndex <= 0}
              onClick={() => openViewerAt(viewerIndex - 1)}
              aria-label="Ảnh trước"
            >
              <IconPrev size={18} />
            </button>
          )}

          <img
            id="photo-viewer-full-img"
            className="photo-viewer-img"
            src={currentViewerPhoto.fullUrl}
            alt={`Ảnh đề ${viewerIndex + 1} độ phân giải gốc`}
            data-viewer-src="full"
            draggable={false}
            style={{
              transform: `translate3d(${panOffset.x}px, ${panOffset.y}px, 0) scale(${scale})`,
            }}
          />

          {photos.length > 1 && (
            <button
              type="button"
              id="btn-viewer-next"
              className="btn-utility photo-viewer-nav is-next"
              disabled={viewerIndex >= photos.length - 1}
              onClick={() => openViewerAt(viewerIndex + 1)}
              aria-label="Ảnh tiếp theo"
            >
              <IconNext size={18} />
            </button>
          )}

          {undoState && (
            <div id="photo-undo-bar" className="photo-undo-bar" role="status" aria-live="polite">
              <span>Đã xóa Ảnh {undoState.index + 1}</span>
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

        {photos.length > 1 && (
          <div className="photo-viewer-filmstrip" role="tablist" aria-label="Danh sách ảnh trong phiên">
            {photos.map((item, idx) => (
              <button
                key={item.id}
                id={`btn-viewer-thumb-${idx + 1}`}
                type="button"
                role="tab"
                aria-selected={idx === viewerIndex}
                className={idx === viewerIndex ? "viewer-filmstrip-item is-active" : "viewer-filmstrip-item"}
                onClick={() => openViewerAt(idx)}
                aria-label={`Chuyển tới ảnh ${idx + 1}`}
              >
                <img src={item.thumbUrl} alt={`Ảnh nhỏ ${idx + 1}`} draggable={false} />
                <span className="viewer-filmstrip-index">{idx + 1}</span>
              </button>
            ))}
          </div>
        )}

        <div className="photo-viewer-footer">
          <div className="photo-viewer-actions-left">
            <button
              type="button"
              id="btn-viewer-retake"
              className="btn-utility"
              onClick={() => handleStartRetake(viewerIndex)}
            >
              <IconReset size={15} />
              <span>Chụp lại</span>
            </button>
            <button
              type="button"
              id="btn-viewer-delete"
              className="btn-utility photo-btn-danger"
              onClick={() => handleDeletePhotoAt(viewerIndex)}
            >
              <IconTrash size={15} />
              <span>Xóa ảnh</span>
            </button>
          </div>

          <button
            type="button"
            id="btn-viewer-done"
            className="btn-primary photo-done-btn"
            onClick={handleCommitSession}
          >
            <IconCheck size={16} />
            <span>Xong</span>
          </button>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="photo-camera photo-error">
        <p className="photo-alert" role="alert">
          {error}
        </p>
        <div className="photo-dialog-actions">
          {support.ok && (
            <button type="button" id="btn-photo-retry-camera" className="btn-utility" onClick={retryCamera}>
              Thử lại
            </button>
          )}
          {mobile && (
            <button type="button" id="btn-photo-native-camera" className="btn-utility" onClick={handleNativeCamera}>
              <IconCamera size={16} />
              <span>Máy ảnh thiết bị</span>
            </button>
          )}
          <button type="button" id="btn-photo-pick-fallback" className="btn-primary" onClick={handlePickFile}>
            <IconImage size={16} />
            <span>Chọn ảnh từ máy</span>
          </button>
          {photos.length > 0 && (
            <button
              type="button"
              id="btn-photo-done"
              className="btn-primary photo-done-btn"
              onClick={handleCommitSession}
            >
              <IconCheck size={16} />
              <span>Xong</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  const retakeSlotNumber = retakeTargetId
    ? photos.findIndex((p) => p.id === retakeTargetId) + 1
    : 0;

  return (
    <div className="photo-camera">
      <div className={shutterFlash ? "photo-camera-stage is-flashing" : "photo-camera-stage"}>
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
          onLoadedMetadata={() => setReady(true)}
          onLoadedData={() => setReady(true)}
        />

        <div className="photo-stage-top-bar">
          {retakeSlotNumber > 0 ? (
            <div id="photo-retake-banner" className="photo-retake-pill" role="status">
              <span>Đang chụp lại Ảnh {retakeSlotNumber}</span>
              <button
                type="button"
                id="btn-cancel-retake"
                className="photo-retake-cancel"
                onClick={() => setRetakeTargetId(null)}
                aria-label="Hủy chụp lại"
              >
                <IconClose size={13} />
              </button>
            </div>
          ) : (
            <span className="photo-stage-spacer" />
          )}

          <button
            type="button"
            id="btn-photo-fit-mode"
            className="photo-fit-toggle-btn"
            onClick={() => setFitMode((m) => (m === "contain" ? "cover" : "contain"))}
            aria-label={
              fitMode === "contain"
                ? "Đang ở chế độ Toàn khung. Bấm để chuyển sang Tràn màn"
                : "Đang ở chế độ Tràn màn. Bấm để chuyển sang Toàn khung"
            }
          >
            <span>{fitMode === "contain" ? "Toàn khung" : "Tràn màn"}</span>
          </button>
        </div>

        {!ready && (
          <p className="photo-camera-loading" role="status" aria-live="polite">
            Đang mở máy ảnh...
          </p>
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

        {mobileTrayOpen && photos.length > 0 && (
          <div
            id="photo-mobile-tray"
            className="photo-mobile-tray"
            role="dialog"
            aria-label="Khay ảnh vừa chụp"
          >
            <div className="photo-mobile-tray-header">
              <span className="photo-mobile-tray-title">Ảnh vừa chụp</span>
              <button
                type="button"
                id="btn-mobile-tray-close"
                className="btn-utility photo-mobile-tray-close"
                onClick={() => setMobileTrayOpen(false)}
                aria-label="Đóng khay ảnh"
              >
                <IconClose size={15} />
              </button>
            </div>
            <div className="photo-mobile-tray-list">
              {photos.map((item, idx) => (
                <div key={item.id} className="mobile-tray-card">
                  <button
                    type="button"
                    id={`btn-tray-open-${idx + 1}`}
                    className="mobile-tray-thumb-btn"
                    onClick={() => openViewerAt(idx)}
                    aria-label={`Mở ảnh ${idx + 1}`}
                  >
                    <img src={item.thumbUrl} alt={`Ảnh ${idx + 1}`} draggable={false} />
                    <span className="mobile-tray-index">{idx + 1}</span>
                  </button>
                  <button
                    type="button"
                    id={`btn-tray-delete-${idx + 1}`}
                    className="mobile-tray-delete-btn"
                    onClick={() => handleDeletePhotoAt(idx)}
                    aria-label={`Xóa ảnh ${idx + 1}`}
                  >
                    <IconClose size={12} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="photo-camera-bar">
        <div className="photo-camera-slot-side">
          <button
            type="button"
            id="btn-photo-library"
            className="btn-utility photo-camera-side-btn"
            onClick={handlePickFile}
            aria-label="Mở thư viện ảnh từ thiết bị"
          >
            <IconImage size={16} />
            <span className="photo-camera-side-label">Chọn ảnh từ máy</span>
          </button>
          {showSwitch ? (
            <button
              type="button"
              id="btn-photo-switch-camera"
              className="btn-utility photo-camera-side-btn photo-camera-switch-btn"
              onClick={switchCamera}
              disabled={switching}
              aria-label="Đổi máy ảnh"
              title="Đổi máy ảnh"
            >
              <IconSwitchCamera size={16} />
            </button>
          ) : null}
        </div>

        <div className="photo-camera-slot-center">
          <button
            type="button"
            id="btn-photo-capture"
            className="btn-primary photo-camera-shutter"
            onClick={capture}
            disabled={!ready || switching}
            aria-label="Chụp ảnh đề bài"
            title="Chụp ảnh"
          >
            <span className="photo-shutter-disc" aria-hidden="true" />
            <IconCamera size={16} />
            <span className="photo-shutter-label">Chụp ảnh</span>
          </button>
        </div>

        <div className="photo-camera-slot-side is-end">
          <PhotoFanStack
            photos={photos}
            isMobile={mobile}
            onOpenPhoto={openViewerAt}
            onOpenMobileTray={() => setMobileTrayOpen((v) => !v)}
          />
          {photos.length > 0 && (
            <button
              type="button"
              id="btn-photo-done"
              className="btn-primary photo-done-btn"
              onClick={handleCommitSession}
              aria-label="Hoàn tất và đính kèm ảnh vào ô nhập"
            >
              <IconCheck size={16} />
              <span>Xong</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
