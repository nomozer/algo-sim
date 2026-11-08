import { useCallback, useEffect, useRef, useState } from "react";

import {
  detectMobileCameraPreferred,
  PhotoCameraView,
  revokeSessionPhotoUrls,
} from "./PhotoCameraView";
import type { CapturedSessionPhoto } from "./PhotoFanStack";

/**
 * Hộp thoại chụp ảnh đề bài Camera-First & Photo Fan Stack (§2–§11):
 * - Mở thẳng khung ngắm máy ảnh (mobile/tablet: toàn màn hình nền tối `#0b0c0e` + nút chụp tròn trắng ở giữa dưới;
 *   desktop: hộp thoại sáng 576px gọn chuẩn DESIGN.md, thu gọn khi ở trạng thái lỗi).
 * - Cho phép chụp liên tiếp nhiều ảnh trong cùng phiên, xem lại độ phân giải gốc trong Photo Viewer,
 *   và chỉ đính kèm vào Composer khi bấm `Xong` hoặc `Giữ ảnh và đóng` (0 lượt gọi AI khi bấm `Xong`).
 * - Khi bấm `Đóng` lúc đã có ảnh mới:
 *   + Desktop: hiển thị khung xác nhận nhỏ gọn trong phạm vi Camera Dialog với hàng 2 nút quyết định
 *     (`Bỏ ảnh mới` | `Giữ ảnh và đóng`) và nút hủy `Tiếp tục chụp` bên dưới.
 *   + Mobile: hiển thị bottom sheet nền tối đồng bộ Camera-First với touch target >= 44×44px.
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
  const confirmBarRef = useRef<HTMLDivElement>(null);
  const openerRef = useRef<Element | null>(null);
  const committingRef = useRef(false);

  const [sessionPhotos, setSessionPhotos] = useState<CapturedSessionPhoto[]>([]);
  const sessionPhotosRef = useRef<CapturedSessionPhoto[]>(sessionPhotos);
  sessionPhotosRef.current = sessionPhotos;

  const [screenMode, setScreenMode] = useState<"camera" | "viewer">("camera");
  const [isMobileSurface, setIsMobileSurface] = useState(detectMobileCameraPreferred);
  const [hasCameraError, setHasCameraError] = useState(false);
  const [confirmDiscardOpen, setConfirmDiscardOpen] = useState(false);

  const discardAndCleanupSession = useCallback(() => {
    sessionPhotosRef.current.forEach((p) => revokeSessionPhotoUrls(p));
    sessionPhotosRef.current = [];
    setSessionPhotos([]);
    setConfirmDiscardOpen(false);
    setScreenMode("camera");
  }, []);

  useEffect(() => {
    committingRef.current = false;
    if (!open) {
      discardAndCleanupSession();
      setHasCameraError(false);
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
    if (!confirmDiscardOpen) return;
    const t = window.setTimeout(() => {
      const primaryBtn = confirmBarRef.current?.querySelector<HTMLElement>("#btn-photo-confirm-attach");
      (primaryBtn ?? confirmBarRef.current)?.focus();
    }, 0);
    return () => window.clearTimeout(t);
  }, [confirmDiscardOpen]);

  useEffect(() => {
    return () => {
      sessionPhotosRef.current.forEach((p) => revokeSessionPhotoUrls(p));
    };
  }, []);

  if (!open) return null;

  function dismissCloseConfirmation() {
    setConfirmDiscardOpen(false);
    window.setTimeout(() => {
      const target =
        dialogRef.current?.querySelector<HTMLElement>("#btn-photo-capture:not([disabled])") ??
        dialogRef.current?.querySelector<HTMLElement>("#btn-photo-dialog-close");
      target?.focus();
    }, 0);
  }

  function requestCloseDialog() {
    if (sessionPhotosRef.current.length > 0) {
      setConfirmDiscardOpen(true);
      return;
    }
    discardAndCleanupSession();
    onClose();
  }

  function confirmDiscardSession() {
    if (committingRef.current) return;
    committingRef.current = true;
    discardAndCleanupSession();
    onClose();
  }

  function confirmAttachAndClose() {
    if (committingRef.current) return;
    committingRef.current = true;
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
    if (committingRef.current) return;
    committingRef.current = true;
    setConfirmDiscardOpen(false);
    setSessionPhotos([]);
    sessionPhotosRef.current = [];
    if (files.length > 0) {
      if (onCapturedBatch) {
        onCapturedBatch(files);
      } else {
        files.forEach((f) => onCaptured(f));
      }
    }
    onClose();
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") {
      e.stopPropagation();
      if (confirmDiscardOpen) {
        dismissCloseConfirmation();
        return;
      }
      requestCloseDialog();
      return;
    }
    if (e.key !== "Tab") return;
    const scopeEl = confirmDiscardOpen ? confirmBarRef.current : dialogRef.current;
    if (!scopeEl) return;
    const items = Array.from(scopeEl.querySelectorAll<HTMLElement>(FOCUSABLE));
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
        : hasCameraError
          ? "axo-modal-dialog photo-dialog camera-dialog is-error-dialog"
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
            onErrorStateChange={setHasCameraError}
          />
        </div>

        {confirmDiscardOpen && (
          <div
            className="cam-close-confirm-scrim"
            onClick={dismissCloseConfirmation}
          >
            <div
              ref={confirmBarRef}
              id="photo-close-confirm-bar"
              className="cam-close-confirm-card photo-close-confirm-bar"
              role="alertdialog"
              aria-modal="true"
              aria-labelledby="cam-close-confirm-heading"
              aria-describedby="cam-close-confirm-desc"
              data-unattached-count={String(sessionPhotos.length)}
              onClick={(e) => e.stopPropagation()}
            >
              <p id="cam-close-confirm-heading" className="cam-close-confirm-title">
                {`Bạn có ${sessionPhotos.length} ảnh chưa thêm vào đề`}
              </p>
              <p id="cam-close-confirm-desc" className="cam-close-confirm-sub">
                Bạn muốn thêm các ảnh này trước khi đóng máy ảnh không?
              </p>
              <div className="cam-close-confirm-actions photo-close-confirm-actions">
                <div className="cam-close-confirm-row">
                  <button
                    type="button"
                    id="btn-photo-confirm-keep"
                    className="confirm-btn secondary"
                    onClick={dismissCloseConfirmation}
                  >
                    Tiếp tục chụp
                  </button>
                  <button
                    type="button"
                    id="btn-photo-confirm-attach"
                    className="confirm-btn primary"
                    onClick={confirmAttachAndClose}
                  >
                    Thêm ảnh và thoát
                  </button>
                </div>
                <div className="cam-close-confirm-discard-row">
                  <button
                    type="button"
                    id="btn-photo-confirm-discard"
                    className="confirm-btn destructive-text"
                    onClick={confirmDiscardSession}
                  >
                    {`Bỏ ${sessionPhotos.length} ảnh và thoát`}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
