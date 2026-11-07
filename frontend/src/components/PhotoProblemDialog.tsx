import { useEffect, useRef } from "react";

import { IconClose } from "./icons";
import { PhotoCameraView } from "./PhotoCameraView";

/**
 * Hộp thoại chụp ảnh đề bài tối giản (Camera-First UX, §5–§8):
 * - Mở thẳng khung ngắm máy ảnh (mobile: camera chiếm vùng chính + nút chụp tròn ở giữa dưới;
 *   desktop: hộp thoại webcam gọn đúng DESIGN.md).
 * - Khi chụp xong: dừng MediaStream, đính kèm ảnh thành chip vào ô nhập đề và đóng hộp thoại ngay.
 * - Không có màn khoanh vùng thủ công, xoay ảnh hay xác nhận nhiều bước trung gian.
 */
export interface PhotoProblemDialogProps {
  open: boolean;
  onClose(): void;
  onPickFile(): void;
  onNativeCamera(): void;
  onCaptured(file: File): void;
}

const FOCUSABLE =
  "button:not([disabled]),textarea:not([disabled]),input:not([disabled]),[tabindex]:not([tabindex='-1'])";

export function PhotoProblemDialog({
  open,
  onClose,
  onPickFile,
  onNativeCamera,
  onCaptured,
}: PhotoProblemDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const openerRef = useRef<Element | null>(null);

  useEffect(() => {
    if (!open) return;
    openerRef.current = document.activeElement;
    const t = window.setTimeout(() => {
      const first = dialogRef.current?.querySelector<HTMLElement>(FOCUSABLE);
      (first ?? dialogRef.current)?.focus();
    }, 0);
    return () => {
      window.clearTimeout(t);
      (openerRef.current as HTMLElement | null)?.focus?.();
    };
  }, [open]);

  if (!open) return null;

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") {
      e.stopPropagation();
      onClose();
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
        if (e.target === e.currentTarget) onClose();
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
        data-photo-screen="camera"
      >
        <div className="axo-modal-header">
          <span className="axo-modal-title" id="photo-dialog-title">
            Chụp ảnh đề bài
          </span>
          <button
            type="button"
            id="btn-photo-dialog-close"
            className="axo-modal-close"
            onClick={onClose}
            aria-label="Đóng máy ảnh"
          >
            <IconClose size={18} />
          </button>
        </div>

        <div className="axo-modal-body photo-dialog-body">
          <PhotoCameraView
            onCapture={onCaptured}
            onPickFile={onPickFile}
            onNativeCamera={onNativeCamera}
          />
        </div>
      </div>
    </div>
  );
}
