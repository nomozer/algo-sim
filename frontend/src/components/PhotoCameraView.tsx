import { useEffect, useRef, useState } from "react";
import { IconCamera, IconImage, IconSwitchCamera } from "./icons";

/**
 * Máy ảnh trực tiếp tối giản (Camera-First UX):
 * - Chỉ khởi động khi người học bấm “Chụp ảnh đề bài”; không bao giờ chạy lúc tải trang.
 * - Mobile: khung ngắm là nội dung chính, nút chụp tròn chính giữa phía dưới, nút mở thư viện ảnh bên trái,
 *   nút đổi máy ảnh bên phải chỉ hiện khi thực sự khả dụng.
 * - Desktop: hộp thoại webcam gọn với nút kích thước chuẩn theo DESIGN.md, không mở màn crop sau khi chụp.
 * - Chụp xong: dừng MediaStream ngay lập tức, trả File ảnh về ô nhập đề để tự đính kèm thành chip và đóng hộp thoại.
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

const IDEAL_SIZE = { width: { ideal: 2560 }, height: { ideal: 1920 } } as const;

export function cameraSupport(env: {
  isSecureContext?: boolean;
  hasGetUserMedia: boolean;
}): CameraSupport {
  if (env.isSecureContext === false) {
    return { ok: false, message: "Máy ảnh chỉ dùng được khi trang mở qua kết nối bảo mật (HTTPS). Em chọn ảnh từ máy nhé." };
  }
  if (!env.hasGetUserMedia) {
    return { ok: false, message: "Trình duyệt này không hỗ trợ mở máy ảnh trực tiếp. Em chọn ảnh từ máy nhé." };
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
  return isMobileCameraPreferred({
    userAgentDataMobile: nav.userAgentData?.mobile,
    userAgent: nav.userAgent,
    maxTouchPoints: nav.maxTouchPoints,
    anyCoarsePointer,
  });
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

/**
 * Nút đổi camera chỉ xuất hiện khi có > 1 thiết bị ghi hình, hoặc trên di động khi danh sách
 * thiết bị chưa liệt kê rõ ID (ẩn danh). Nếu đã liệt kê xong và xác nhận chỉ có <= 1 camera
 * có ID rõ ràng trên desktop/tablet thì ẩn nút đổi camera (§5, §6).
 */
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

export interface PhotoCameraViewProps {
  onCapture(file: File): void;
  onPickFile(): void;
  onNativeCamera(): void;
}

export function PhotoCameraView({ onCapture, onPickFile, onNativeCamera }: PhotoCameraViewProps) {
  const [mobile] = useState(detectMobileCameraPreferred);
  const [target, setTarget] = useState<CameraTarget>(() => initialCameraTarget(mobile));
  const [attempt, setAttempt] = useState(0);
  const [videoIds, setVideoIds] = useState<string[]>([]);
  const [enumeratedCount, setEnumeratedCount] = useState<number | undefined>(undefined);
  const [activeDeviceId, setActiveDeviceId] = useState("");
  const [ready, setReady] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const support = browserCameraSupport();

  function releaseCurrentStream() {
    stopStream(streamRef.current);
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  }

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
    };
  }, [target, attempt]);

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
    const canvas = document.createElement("canvas");
    canvas.width = v.videoWidth;
    canvas.height = v.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(v, 0, 0);
    canvas.toBlob(
      (blob) => {
        canvas.width = 0;
        canvas.height = 0;
        if (!blob) {
          setError("Chưa ghi nhận được khung hình. Em thử lại hoặc chọn ảnh từ máy.");
          return;
        }
        releaseCurrentStream();
        onCapture(new File([blob], `anh-de-${Date.now()}.jpg`, { type: "image/jpeg" }));
      },
      "image/jpeg",
      0.94,
    );
  }

  const showSwitch = canSwitchCamera(videoIds, mobile, enumeratedCount);

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
        </div>
      </div>
    );
  }

  return (
    <div className="photo-camera">
      <div className="photo-camera-stage">
        <video
          ref={videoRef}
          className="photo-camera-video"
          playsInline
          muted
          autoPlay
          aria-label="Khung ngắm máy ảnh đề bài"
          onLoadedMetadata={() => setReady(true)}
          onLoadedData={() => setReady(true)}
        />
        {!ready && (
          <p className="photo-camera-loading" role="status" aria-live="polite">
            Đang mở máy ảnh...
          </p>
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
          {showSwitch ? (
            <button
              type="button"
              id="btn-photo-switch-camera"
              className="btn-utility photo-camera-side-btn"
              onClick={switchCamera}
              disabled={switching}
              aria-label="Đổi máy ảnh"
            >
              <IconSwitchCamera size={16} />
              <span className="photo-camera-side-label">Đổi camera</span>
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
