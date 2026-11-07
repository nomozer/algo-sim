import { useEffect, useRef, useState } from "react";

import { IconClose } from "./icons";
import { PhotoCameraView } from "./PhotoCameraView";
import { PhotoCropEditor } from "./PhotoCropEditor";
import { PhotoProblemPanel } from "./PhotoProblemPanel";
import {
  canAccept,
  canRead,
  needsReplaceConfirmation,
  photoStatusText,
  type PhotoState,
  type PhotoUpload,
} from "./photo-problem-flow";

/**
 * Hộp thoại ẢNH ĐỀ BÀI (run `image-capture-crop-extraction`): MÁY ẢNH TRỰC TIẾP → CHỈNH ẢNH (khoanh vùng/xoay) →
 * ĐANG ĐỌC → XEM LẠI → (ô nhập đề). Không có màn lựa chọn trung gian trước máy ảnh; ngay trong khung máy ảnh luôn có
 * lối “Chọn ảnh có sẵn” (hoặc “Chọn ảnh từ máy” khi thiết bị không có camera).
 */
export interface PhotoProblemDialogProps {
  open: boolean;
  state: PhotoState;
  composerText: string;
  onClose(): void;
  onPickFile(): void;
  onNativeCamera(): void;
  onCaptured(file: File): void;
  onChangeImage(): void;
  onRotate(direction: "left" | "right"): void;
  onPrepare(upload: PhotoUpload): void;
  onInvalid(message: string): void;
  onEditImage(): void;
  onRead(): void;
  onCancelRead(): void;
  onEdit(text: string): void;
  onConfirm(value: boolean): void;
  onAccept(): void;
}

const TIEU_DE: Record<string, string> = {
  camera: "Chụp ảnh đề bài",
  selected: "Khoanh vùng đề bài",
  prepared: "Ảnh sẽ gửi đi đọc",
  reading: "Đang đọc đề bài",
  review: "Kiểm tra nội dung đề",
  error: "Chưa đọc được ảnh",
};

const FOCUSABLE = "button:not([disabled]),textarea:not([disabled]),input:not([disabled]),[tabindex]:not([tabindex='-1'])";

/** Ảnh SẼ/ĐÃ gửi — để người học đối chiếu khi đọc lại văn bản. URL thu hồi khi đổi ảnh hoặc đóng. */
function SentImage({ upload, compact }: { upload: PhotoUpload; compact?: boolean }) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    const u = URL.createObjectURL(upload.file as unknown as Blob);
    setUrl(u);
    return () => URL.revokeObjectURL(u);
  }, [upload.file]);
  const quay = upload.rotation % 180 !== 0;
  return (
    <figure className={`photo-sent${compact ? " is-compact" : ""}${quay ? " is-turned" : ""}`}>
      {url && (
        <img
          className="photo-sent-image"
          src={url}
          alt={upload.cropped ? "Vùng ảnh đã khoanh" : "Ảnh đề bài"}
          style={upload.rotation ? { transform: `rotate(${upload.rotation}deg)` } : undefined}
        />
      )}
    </figure>
  );
}

export function PhotoProblemDialog(props: PhotoProblemDialogProps) {
  const { open, state } = props;
  const dialogRef = useRef<HTMLDivElement>(null);
  const openerRef = useRef<Element | null>(null);
  const [askReplace, setAskReplace] = useState(false);

  // Mở: nhớ chỗ focus cũ, đưa focus vào hộp thoại. Đóng: trả focus về chỗ cũ.
  useEffect(() => {
    if (!open) return;
    openerRef.current = document.activeElement;
    const t = window.setTimeout(() => {
      const first = dialogRef.current?.querySelector<HTMLElement>(FOCUSABLE);
      (first ?? dialogRef.current)?.focus();
    }, 0);
    return () => {
      window.clearTimeout(t);
      setAskReplace(false);
      (openerRef.current as HTMLElement | null)?.focus?.();
    };
  }, [open]);

  useEffect(() => {
    setAskReplace(false);
  }, [state.phase]);

  if (!open) return null;

  const man = state.phase === "empty" ? "camera" : state.phase;
  const trangThai = photoStatusText(state);

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") {
      e.stopPropagation();
      props.onClose();
      return;
    }
    if (e.key !== "Tab" || !dialogRef.current) return;
    const items = Array.from(dialogRef.current.querySelectorAll<HTMLElement>(FOCUSABLE));
    if (items.length === 0) return;
    const first = items[0];
    const last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  function accept() {
    if (!canAccept(state)) return;
    if (!askReplace && needsReplaceConfirmation(props.composerText, state.text)) {
      setAskReplace(true);
      return;
    }
    props.onAccept();
  }

  return (
    <div
      className="axo-modal-backdrop open"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) props.onClose();
      }}
    >
      <div
        ref={dialogRef}
        className="axo-modal-dialog photo-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="photo-dialog-title"
        tabIndex={-1}
        onKeyDown={onKeyDown}
        data-photo-screen={man}
      >
        <div className="axo-modal-header">
          <span className="axo-modal-title" id="photo-dialog-title">
            {TIEU_DE[man]}
          </span>
          <button
            type="button"
            className="axo-modal-close"
            onClick={props.onClose}
            aria-label="Đóng hộp thoại ảnh đề bài"
          >
            <IconClose size={18} />
          </button>
        </div>

        <div className="axo-modal-body photo-dialog-body">
          {man === "camera" && (
            <PhotoCameraView
              onCapture={props.onCaptured}
              onPickFile={props.onPickFile}
              onNativeCamera={props.onNativeCamera}
            />
          )}

          {man === "selected" && state.file && (
            <PhotoCropEditor
              file={state.file as File}
              rotation={state.rotation}
              onRotate={props.onRotate}
              onPrepare={props.onPrepare}
              onInvalid={props.onInvalid}
              onChangeImage={props.onChangeImage}
            />
          )}

          {(man === "prepared" || man === "reading") && state.upload && (
            <div className="photo-prepared">
              <SentImage upload={state.upload} />
              <p className="photo-status" role="status" aria-live="polite">
                {trangThai}
              </p>
              <div className="photo-dialog-actions">
                {man === "reading" ? (
                  <button type="button" className="btn-utility" onClick={props.onCancelRead}>
                    Huỷ đọc
                  </button>
                ) : (
                  <button type="button" className="btn-utility" onClick={props.onEditImage}>
                    Chỉnh lại ảnh
                  </button>
                )}
                <button
                  type="button"
                  className="btn-primary"
                  onClick={props.onRead}
                  disabled={!canRead(state)}
                  aria-busy={man === "reading"}
                >
                  {man === "reading" ? "Đang đọc…" : "Đọc đề trong ảnh"}
                </button>
              </div>
            </div>
          )}

          {man === "review" && (
            <div className="photo-review-screen">
              {state.upload && (
                <details className="photo-details">
                  <summary>Xem ảnh đã đọc để đối chiếu</summary>
                  <SentImage upload={state.upload} compact />
                </details>
              )}
              <p className="photo-status" role="status" aria-live="polite">
                {trangThai}
              </p>
              <PhotoProblemPanel state={state} onEdit={props.onEdit} onConfirm={props.onConfirm} />
              {askReplace && (
                <div className="photo-alert" role="alert">
                  Ô nhập đề đang có nội dung khác. Thay bằng đề vừa đọc từ ảnh?
                </div>
              )}
              <div className="photo-dialog-actions">
                <button type="button" className="btn-utility" onClick={props.onEditImage}>
                  Chỉnh lại ảnh
                </button>
                <button type="button" className="btn-utility" onClick={props.onClose}>
                  Tự nhập đề
                </button>
                <button
                  type="button"
                  className="btn-primary"
                  onClick={accept}
                  disabled={!canAccept(state)}
                  aria-describedby={canAccept(state) ? undefined : "photo-accept-hint"}
                >
                  {askReplace ? "Thay nội dung" : "Dùng đề này"}
                </button>
              </div>
            </div>
          )}

          {man === "error" && (
            <div className="photo-error">
              <p className="photo-alert" role="alert">
                {state.error ?? "Chưa đọc được ảnh. Em thử lại nhé."}
              </p>
              <div className="photo-dialog-actions">
                {state.file && (
                  <button type="button" className="btn-utility" onClick={props.onEditImage}>
                    Chỉnh lại ảnh
                  </button>
                )}
                <button type="button" className="btn-utility" onClick={props.onChangeImage}>
                  Chụp ảnh khác
                </button>
                <button type="button" className="btn-utility" onClick={props.onPickFile}>
                  Chọn ảnh từ máy
                </button>
                {canRead(state) && (
                  <button type="button" className="btn-primary" onClick={props.onRead}>
                    Thử đọc lại
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
