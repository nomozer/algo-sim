import { useEffect, useRef, useState } from "react";
import { IconCamera, IconImage, IconSwitchCamera } from "./icons";

/**
 * Máy ảnh trực tiếp (Camera-First UX) cho luồng ẢNH ĐỀ BÀI (run `image-capture-crop-extraction`).
 *
 * - Chỉ khởi động khi người học bấm “Chụp ảnh đề bài”; không bao giờ chạy lúc tải trang.
 * - Desktop/laptop mở webcam mặc định của hệ thống (không ép chọn thiết bị trước, không dùng riêng bề rộng màn hình).
 * - Mobile ưu tiên camera sau (`facingMode: { ideal: "environment" }`), tự lùi về camera khả dụng nếu camera sau vắng.
 * - Có đổi máy ảnh khi nhiều camera hoặc thiết bị di động hỗ trợ trước/sau, và luôn có lối chọn ảnh từ máy ngay tại chỗ.
 * - Mọi `MediaStreamTrack` dừng ngay khi chụp, đổi camera, đóng hộp thoại hoặc tháo component.
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
    return { ok: false, message: "Máy ảnh chỉ dùng được khi trang mở qua HTTPS. Em chọn ảnh từ máy nhé." };
  }
  if (!env.hasGetUserMedia) {
    return { ok: false, message: "Trình duyệt này không mở được máy ảnh. Em chọn ảnh từ máy nhé." };
  }
  return { ok: true };
}

/** Lỗi `getUserMedia` → lời ngắn gọn cho người học (DOMException theo đặc tả Media Capture). */
export function cameraErrorMessage(err: unknown): string {
  const name = (err as { name?: string } | null)?.name ?? "";
  switch (name) {
    case "NotAllowedError":
    case "SecurityError":
      return "Trình duyệt chưa cho phép dùng máy ảnh. Em cấp quyền máy ảnh hoặc chọn ảnh từ máy.";
    case "NotFoundError":
    case "OverconstrainedError":
      return "Không tìm thấy máy ảnh khả dụng trên thiết bị này. Em chọn ảnh từ máy nhé.";
    case "NotReadableError":
    case "AbortError":
      return "Máy ảnh đang bận ở ứng dụng khác. Em đóng ứng dụng đó rồi thử lại, hoặc chọn ảnh từ máy.";
    default:
      return "Chưa mở được máy ảnh. Em thử lại hoặc chọn ảnh từ máy.";
  }
}

/** Nhận diện thiết bị di động theo tín hiệu năng lực thiết bị + UA, KHÔNG dựa vào bề rộng màn hình. */
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

export function canSwitchCamera(videoDeviceIds: readonly string[], mobile: boolean): boolean {
  return uniqueIds(videoDeviceIds).length > 1 || mobile;
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
  const [activeDeviceId, setActiveDeviceId] = useState("");
  const [ready, setReady] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const support = browserCameraSupport();

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
      stopStream(streamRef.current);
      streamRef.current = null;
      if (videoRef.current) videoRef.current.srcObject = null;

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
            setVideoIds(list.filter((d) => d.kind === "videoinput").map((d) => d.deviceId));
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
      stopStream(streamRef.current);
      streamRef.current = null;
      if (videoRef.current) videoRef.current.srcObject = null;
    };
  }, [target, attempt]);

  function switchCamera() {
    if (switching) return;
    stopStream(streamRef.current);
    streamRef.current = null;
    setSwitching(true);
    setTarget((cur) => nextCameraTarget(cur, activeDeviceId, videoIds, mobile));
  }

  function retryCamera() {
    stopStream(streamRef.current);
    streamRef.current = null;
    setTarget(initialCameraTarget(mobile));
    setAttempt((n) => n + 1);
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
          setError("Chưa chụp được ảnh. Em thử lại nhé.");
          return;
        }
        stopStream(streamRef.current);
        streamRef.current = null;
        if (videoRef.current) videoRef.current.srcObject = null;
        onCapture(new File([blob], `anh-chup-${Date.now()}.jpg`, { type: "image/jpeg" }));
      },
      "image/jpeg",
      0.95,
    );
  }

  const showSwitch = canSwitchCamera(videoIds, mobile);

  if (error) {
    return (
      <div className="photo-camera">
        <p className="photo-alert" role="alert">
          {error}
        </p>
        <div className="photo-dialog-actions">
          {support.ok && (
            <button type="button" id="btn-photo-retry-camera" className="btn-utility" onClick={retryCamera}>
              Thử lại máy ảnh
            </button>
          )}
          {mobile && (
            <button type="button" id="btn-photo-native-camera" className="btn-utility" onClick={onNativeCamera}>
              <IconCamera size={16} />
              <span>Mở máy ảnh thiết bị</span>
            </button>
          )}
          <button type="button" id="btn-photo-pick-fallback" className="btn-primary" onClick={onPickFile}>
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
            Đang mở máy ảnh…
          </p>
        )}
      </div>

      <p className="photo-camera-hint">
        Canh trọn đề bài và hình vẽ trong khung.
      </p>

      <div className="photo-camera-bar">
        <div className="photo-camera-tools">
          <button type="button" id="btn-photo-library" className="btn-utility" onClick={onPickFile}>
            <IconImage size={16} />
            <span>Chọn ảnh có sẵn</span>
          </button>
          {showSwitch && (
            <button
              type="button"
              id="btn-photo-switch-camera"
              className="btn-utility"
              onClick={switchCamera}
              disabled={switching}
            >
              <IconSwitchCamera size={16} />
              <span>Đổi máy ảnh</span>
            </button>
          )}
        </div>
        <button
          type="button"
          id="btn-photo-capture"
          className="btn-primary photo-camera-shutter"
          onClick={capture}
          disabled={!ready || switching}
        >
          <IconCamera size={18} />
          <span>Chụp ảnh</span>
        </button>
      </div>
    </div>
  );
}
