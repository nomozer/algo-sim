import { useEffect, useRef, useState } from "react";
import ReactCrop, { type PercentCrop } from "react-image-crop";
import "react-image-crop/dist/ReactCrop.css";

import type { PhotoRotation } from "../llm/client";
import {
  coversWholeImage,
  cropToPixels,
  exceedsPixelLimit,
  loadImage,
  renderPhotoUpload,
  renderRotatedPreview,
  rotatedSize,
  type Size,
} from "./photo-image-tools";
import { PHOTO_MAX_BYTES, type PhotoUpload } from "./photo-problem-flow";

/**
 * KHOANH VÙNG · XOAY ảnh đề bài — thủ công, ở trình duyệt, không AI (run `image-capture-crop-extraction`).
 *
 * Khung chọn BẮT ĐẦU bằng cả ảnh: người học kéo góc/cạnh vào để khoanh đề và hình vẽ (tự do tỉ lệ), kéo giữa khung để
 * di chuyển; các tay nắm nhận bàn phím (mũi tên). "Giữ nguyên ảnh" bỏ qua bước cắt. Toạ độ đi bằng % (xem
 * `photo-image-tools.ts`) nên không lệch khi ảnh thu nhỏ trên màn hình hay khi DPR khác 1.
 *
 * Khi chỉ XOAY mà không cắt, tệp GỐC được gửi kèm `rotation` (máy chủ xoay, như trước); khi cắt, trình duyệt xuất
 * đúng vùng ở độ phân giải gốc (đã xoay, `rotation = 0`).
 */
const FULL: PercentCrop = { unit: "%", x: 0, y: 0, width: 100, height: 100 };

const ARIA = {
  cropArea: "Khung khoanh vùng — dùng phím mũi tên để di chuyển",
  nwDragHandle: "Góc trên trái của khung",
  nDragHandle: "Cạnh trên của khung",
  neDragHandle: "Góc trên phải của khung",
  eDragHandle: "Cạnh phải của khung",
  seDragHandle: "Góc dưới phải của khung",
  sDragHandle: "Cạnh dưới của khung",
  swDragHandle: "Góc dưới trái của khung",
  wDragHandle: "Cạnh trái của khung",
};

export interface PhotoCropEditorProps {
  file: File;
  rotation: PhotoRotation;
  onRotate(direction: "left" | "right"): void;
  onPrepare(upload: PhotoUpload): void;
  onInvalid(message: string): void;
  onChangeImage(): void;
}

export function PhotoCropEditor({
  file,
  rotation,
  onRotate,
  onPrepare,
  onInvalid,
  onChangeImage,
}: PhotoCropEditorProps) {
  const imgRef = useRef<HTMLImageElement | null>(null);
  const [source, setSource] = useState<{ url: string; natural: Size } | null>(null);
  const [display, setDisplay] = useState<string | null>(null);
  const [crop, setCrop] = useState<PercentCrop>(FULL);
  const [busy, setBusy] = useState(false);

  // Giải mã ảnh nguồn MỘT lần cho mỗi tệp; URL thu hồi khi đổi tệp hoặc tháo component.
  useEffect(() => {
    let alive = true;
    let url: string | null = null;
    setSource(null);
    loadImage(file)
      .then(({ img, url: u }) => {
        url = u;
        if (!alive) {
          URL.revokeObjectURL(u);
          return;
        }
        const natural = { width: img.naturalWidth, height: img.naturalHeight };
        if (!natural.width || !natural.height) {
          onInvalid("Không đọc được ảnh này. Em chọn ảnh khác nhé.");
          return;
        }
        if (exceedsPixelLimit(natural)) {
          onInvalid("Ảnh có quá nhiều điểm ảnh (tối đa 40 triệu). Em chụp lại với độ phân giải thấp hơn.");
          return;
        }
        imgRef.current = img;
        setSource({ url: u, natural });
      })
      .catch((e: Error) => alive && onInvalid(e.message));
    return () => {
      alive = false;
      imgRef.current = null;
      if (url) URL.revokeObjectURL(url);
    };
  }, [file, onInvalid]);

  // Ảnh hiển thị theo góc xoay: góc 0 dùng chính ảnh nguồn; góc khác dựng bản xem trước đã xoay (thu hồi khi đổi).
  useEffect(() => {
    setCrop(FULL);                                   // khung của góc cũ vô nghĩa ở góc mới
    if (!source) return;
    if (rotation === 0) {
      setDisplay(source.url);
      return;
    }
    let alive = true;
    let url: string | null = null;
    setDisplay(null);
    renderRotatedPreview(imgRef.current!, rotation)
      .then((blob) => {
        if (!alive) return;
        url = URL.createObjectURL(blob);
        setDisplay(url);
      })
      .catch((e: Error) => alive && onInvalid(e.message));
    return () => {
      alive = false;
      if (url) URL.revokeObjectURL(url);
    };
  }, [source, rotation, onInvalid]);

  const turned = source ? rotatedSize(source.natural, rotation) : null;
  const rect = turned ? cropToPixels(crop, turned) : null;
  const whole = !turned || coversWholeImage(rect, turned);

  function useWhole() {
    onPrepare({ file, rotation, cropped: false });
  }

  async function confirmCrop() {
    if (!imgRef.current || !turned || !rect || whole || busy) return;
    setBusy(true);
    try {
      const out = await renderPhotoUpload(imgRef.current, rotation, rect, file, PHOTO_MAX_BYTES);
      onPrepare({ file: out, rotation: 0, cropped: true });
    } catch (e) {
      onInvalid(e instanceof Error ? e.message : "Chưa cắt được ảnh. Em thử lại nhé.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="photo-editor">
      <div className="photo-crop-stage" data-rotation={rotation}>
        {display && turned ? (
          <ReactCrop
            crop={crop}
            onChange={(_px, pct) => setCrop(pct)}
            keepSelection
            ruleOfThirds={false}
            ariaLabels={ARIA}
            className="photo-crop"
            disabled={busy}
          >
            <img className="photo-crop-image" src={display} alt="Ảnh đề bài để khoanh vùng" draggable={false} />
          </ReactCrop>
        ) : (
          <p className="photo-status" role="status">Đang mở ảnh…</p>
        )}
      </div>

      {turned && (
        <p className="photo-crop-size" aria-live="polite">
          {whole
            ? `Cả ảnh · ${turned.width} × ${turned.height} điểm ảnh`
            : `Vùng chọn · ${rect!.width} × ${rect!.height} điểm ảnh`}
        </p>
      )}

      <div className="photo-dialog-actions photo-editor-tools">
        <button type="button" className="btn-utility" onClick={() => onRotate("left")} disabled={busy || !source}>
          Xoay trái
        </button>
        <button type="button" className="btn-utility" onClick={() => onRotate("right")} disabled={busy || !source}>
          Xoay phải
        </button>
        <button type="button" className="btn-utility" onClick={() => setCrop(FULL)} disabled={busy || whole}>
          Đặt lại khung
        </button>
        <button type="button" className="btn-utility" onClick={onChangeImage} disabled={busy}>
          Đổi ảnh
        </button>
      </div>
      <div className="photo-dialog-actions">
        <button type="button" className="btn-utility" onClick={useWhole} disabled={busy || !source}>
          Giữ nguyên ảnh
        </button>
        <button
          type="button"
          className="btn-primary"
          onClick={() => void confirmCrop()}
          disabled={busy || whole}
          aria-describedby={whole ? "photo-crop-hint" : undefined}
        >
          {busy ? "Đang cắt…" : "Cắt theo khung"}
        </button>
      </div>
      <p id="photo-crop-hint" className="hint">
        Kéo các góc hoặc cạnh khung vào trong để chỉ giữ phần đề bài và hình vẽ.
      </p>
    </div>
  );
}
