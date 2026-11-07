import { useCallback, useEffect, useRef, useState } from "react";

import { IconClose } from "./icons";
import { PhotoCameraView, revokeSessionPhotoUrls } from "./PhotoCameraView";
import type { CapturedSessionPhoto } from "./PhotoFanStack";

/**
 * Hộp thoại chụp ảnh đề bài Camera-First & Photo Fan Stack (§4–§8, §12):
 * - Mở thẳng khung ngắm máy ảnh (mobile: toàn màn hình + nút chụp tròn ở giữa dưới;
 *   desktop: hộp thoại 576px gọn chuẩn DESIGN.md).
 * - Cho phép chụp liên tiếp nhiều ảnh trong cùng phiên, xem lại độ phân giải gốc trong Photo Viewer,
 *   và chỉ đính kèm vào Composer khi bấm `Xong` (0 lượt gọi AI khi bấm `Xong`).
 * - Tách biệt rõ hành vi `Đóng` (hỏi xác nhận hủy phiên khi có ảnh chưa gắn) và `Xong` (đính kèm toàn bộ ảnh phiên vào Composer).
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

  return (
    <div
      className="axo-modal-backdrop open"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) requestCloseDialog();
      }}
    >
      <div
        ref={dialogRef}
        className="axo-modal-dialog photo-dialog"
        id="photo-camera-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="photo-dialog-title"
        tabIndex={-1}
        onKeyDown={onKeyDown}
        data-photo-screen={screenMode}
      >
        <div className="axo-modal-header">
          <span className="axo-modal-title" id="photo-dialog-title">
            Chụp ảnh đề bài
          </span>
          <button
            type="button"
            id="btn-photo-dialog-close"
            className="axo-modal-close"
            onClick={requestCloseDialog}
            aria-label="Đóng máy ảnh"
          >
            <IconClose size={18} />
          </button>
        </div>

        {confirmDiscardOpen && (
          <div
            id="photo-close-confirm-bar"
            className="photo-close-confirm-bar"
            role="alertdialog"
            aria-label="Xác nhận bỏ ảnh vừa chụp"
          >
            <span className="photo-close-confirm-text">
              Bỏ ảnh vừa chụp trong phiên này?
            </span>
            <div className="photo-close-confirm-actions">
              <button
                type="button"
                id="btn-photo-confirm-keep"
                className="btn-utility"
                onClick={() => setConfirmDiscardOpen(false)}
              >
                Tiếp tục chụp
              </button>
              <button
                type="button"
                id="btn-photo-confirm-discard"
                className="btn-utility photo-btn-danger"
                onClick={confirmDiscardSession}
              >
                Bỏ ảnh vừa chụp
              </button>
            </div>
          </div>
        )}

        <div className="axo-modal-body photo-dialog-body">
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
            photos={sessionPhotos}
            onPhotosChange={(next) => {
              setSessionPhotos(next);
              if (next.length === 0) setConfirmDiscardOpen(false);
            }}
            onScreenModeChange={setScreenMode}
          />
        </div>
      </div>
    </div>
  );
}
