import { useCallback, useEffect, useRef, useState } from "react";

import { IconCheck } from "./icons";
import {
  detectMobileCameraPreferred,
  PhotoCameraView,
  revokeSessionPhotoUrls,
} from "./PhotoCameraView";
import type { CapturedSessionPhoto } from "./PhotoFanStack";

/**
 * Hộp thoại chụp ảnh đề bài Camera-First & Photo Fan Stack (§4–§12):
 * - Mở thẳng khung ngắm máy ảnh (mobile/tablet: toàn màn hình nền tối `#0b0c0e` + nút chụp tròn trắng ở giữa dưới;
 *   desktop: hộp thoại sáng 576px gọn chuẩn DESIGN.md).
 * - Cho phép chụp liên tiếp nhiều ảnh trong cùng phiên, xem lại độ phân giải gốc trong Photo Viewer,
 *   và chỉ đính kèm vào Composer khi bấm `Xong` hoặc `Giữ ảnh` (0 lượt gọi AI khi bấm `Xong`).
 * - Tách biệt rõ hành vi `Đóng` (hiển thị hộp xác nhận nội tuyến 3 lựa chọn: `Giữ ảnh`, `Bỏ ảnh mới`, `Tiếp tục chụp`)
 *   và `Xong` (đính kèm toàn bộ ảnh phiên vào Composer).
 */
export interface PhotoProblemDialogProps {
  open: boolean;
  onClose(): void;
  onPickFile(): void;
  onNativeCamera(): void;
  onCaptured(file: File): void;
  onCapturedBatch?(files: File[]): void;
}

const FOCUSABLE =
  "button:not([disabled]),textarea:not([disabled]),input:not([disabled]),[tabindex]:not([tabindex='-1'])";

export function PhotoProblemDialog({
  open,
  onClose,
  onPickFile,
  onNativeCamera,
  onCaptured,
  onCapturedBatch,
}: PhotoProblemDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const openerRef = useRef<Element | null>(null);
  const [sessionPhotos, setSessionPhotos] = useState<CapturedSessionPhoto[]>([]);
  const sessionPhotosRef = useRef<CapturedSessionPhoto[]>(sessionPhotos);
  sessionPhotosRef.current = sessionPhotos;

  const [screenMode, setScreenMode] = useState<"camera" | "viewer">("camera");
  const [isMobileSurface, setIsMobileSurface] = useState(detectMobileCameraPreferred);
  const [confirmDiscardOpen, setConfirmDiscardOpen] = useState(false);

  const discardAndCleanupSession = useCallback(() => {
    sessionPhotosRef.current.forEach((p) => revokeSessionPhotoUrls(p));
    sessionPhotosRef.current = [];
    setSessionPhotos([]);
    setConfirmDiscardOpen(false);
    setScreenMode("camera");
  }, []);

  useEffect(() => {
    if (!open) {
      discardAndCleanupSession();
      return;
    }
    setIsMobileSurface(detectMobileCameraPreferred());
    openerRef.current = document.activeElement;
    const t = window.setTimeout(() => {
      const first = dialogRef.current?.querySelector<HTMLElement>(FOCUSABLE);
      (first ?? dialogRef.current)?.focus();
    }, 0);
    return () => {
      window.clearTimeout(t);
      (openerRef.current as HTMLElement | null)?.focus?.();
    };
  }, [open, discardAndCleanupSession]);

  useEffect(() => {
    return () => {
      sessionPhotosRef.current.forEach((p) => revokeSessionPhotoUrls(p));
    };
  }, []);

  if (!open) return null;

  function requestCloseDialog() {
    if (sessionPhotosRef.current.length > 0) {
      setConfirmDiscardOpen(true);
      return;
    }
    discardAndCleanupSession();
    onClose();
  }

  function confirmDiscardSession() {
    discardAndCleanupSession();
    onClose();
  }

  function confirmAttachAndClose() {
    const current = sessionPhotosRef.current;
    const files = current.map((p) => p.file);
    current.forEach((p) => revokeSessionPhotoUrls(p));
    sessionPhotosRef.current = [];
    setSessionPhotos([]);
    setConfirmDiscardOpen(false);
    setScreenMode("camera");
    if (files.length > 0) {
      if (onCapturedBatch) {
        onCapturedBatch(files);
      } else {
        files.forEach((f) => onCaptured(f));
      }
    }
    onClose();
  }

  function handleBatchCommitted(files: File[]) {
    setConfirmDiscardOpen(false);
    setSessionPhotos([]);
    sessionPhotosRef.current = [];
    if (onCapturedBatch) {
      onCapturedBatch(files);
    } else {
      files.forEach((f) => onCaptured(f));
    }
    onClose();
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") {
      e.stopPropagation();
      if (confirmDiscardOpen) {
        setConfirmDiscardOpen(false);
        return;
      }
      requestCloseDialog();
      return;
    }
    if (e.key !== "Tab" || !dialogRef.current) return;
    const items = Array.from(dialogRef.current.querySelectorAll<HTMLElement>(FOCUSABLE));
    if (items.length === 0) return;
    const first = items[0]!;
    const last = items[items.length - 1]!;
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  const dialogClassName =
    screenMode === "viewer"
      ? "axo-modal-dialog photo-dialog is-viewer-dialog"
      : isMobileSurface
        ? "axo-modal-dialog photo-dialog camera-fullscreen dark-surface"
        : "axo-modal-dialog photo-dialog camera-dialog";

  return (
    <div
      className={
        screenMode === "viewer"
          ? "axo-modal-backdrop open is-lightbox-backdrop"
          : isMobileSurface
            ? "axo-modal-backdrop open is-fullscreen-camera"
            : "axo-modal-backdrop open"
      }
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) requestCloseDialog();
      }}
    >
      <div
        ref={dialogRef}
        className={dialogClassName}
        id="photo-camera-dialog"
        role="dialog"
        aria-modal="true"
        aria-label="Chụp ảnh đề bài"
        tabIndex={-1}
        onKeyDown={onKeyDown}
        data-photo-screen={screenMode}
      >
        <div className="photo-dialog-body">
          <PhotoCameraView
            onCapture={(f) => handleBatchCommitted([f])}
            onCaptureBatch={handleBatchCommitted}
            onPickFile={() => {
              discardAndCleanupSession();
              onPickFile();
            }}
            onNativeCamera={() => {
              discardAndCleanupSession();
              onNativeCamera();
            }}
            onRequestClose={requestCloseDialog}
            photos={sessionPhotos}
            onPhotosChange={(next) => {
              setSessionPhotos(next);
              if (next.length === 0) setConfirmDiscardOpen(false);
            }}
            onScreenModeChange={setScreenMode}
            onMobileModeChange={setIsMobileSurface}
          />
        </div>

        {confirmDiscardOpen && (
          <div
            className="cam-close-confirm-scrim"
            onClick={() => setConfirmDiscardOpen(false)}
          >
            <div
              id="photo-close-confirm-bar"
              className="cam-close-confirm-card photo-close-confirm-bar"
              role="alertdialog"
              aria-modal="true"
              aria-label="Xác nhận trước khi đóng máy ảnh"
              onClick={(e) => e.stopPropagation()}
            >
              <p className="cam-close-confirm-title">
                Giữ ảnh vừa chụp trước khi đóng?
              </p>
              <p className="cam-close-confirm-sub">
                Chọn giữ để đưa ảnh vào ô nhập đề bài, hoặc bỏ ảnh mới chụp trong phiên này.
              </p>
              <div className="cam-close-confirm-actions photo-close-confirm-actions">
                <button
                  type="button"
                  id="btn-photo-confirm-attach"
                  className="confirm-btn keep"
                  onClick={confirmAttachAndClose}
                >
                  <IconCheck size={15} />
                  <span>Giữ ảnh</span>
                </button>
                <button
                  type="button"
                  id="btn-photo-confirm-discard"
                  className="confirm-btn discard"
                  onClick={confirmDiscardSession}
                >
                  Bỏ ảnh mới
                </button>
                <button
                  type="button"
                  id="btn-photo-confirm-keep"
                  className="confirm-btn cancel"
                  onClick={() => setConfirmDiscardOpen(false)}
                >
                  Tiếp tục chụp
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
