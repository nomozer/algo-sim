/**
 * ẢNH ĐỀ BÀI — xoay · khoanh vùng · xuất ảnh, HOÀN TOÀN ở trình duyệt (không AI, không mạng).
 *
 * Toán học thuần (kiểm được trong vitest `node`) + một hàm Canvas `renderPhotoUpload`.
 *
 * ─── VÌ SAO TOẠ ĐỘ ĐI BẰNG PHẦN TRĂM ───────────────────────────────────────
 * `react-image-crop` báo vùng chọn theo CSS pixel của ảnh ĐANG HIỂN THỊ và theo %. Ảnh 4000×3000 hiện trong khung
 * 800 px, màn hình DPR 2, phóng 110 %: CSS pixel đổi theo cả ba, % thì không. Đổi % → pixel GỐC một lần
 * (`cropToPixels`) là cách duy nhất không lệch khi ảnh thu nhỏ hay khi devicePixelRatio khác 1.
 *
 * ─── HƯỚNG ẢNH ───────────────────────────────────────────────────────────
 * Trình duyệt áp EXIF orientation khi hiển thị `<img>`, khi báo `naturalWidth/Height` và khi `drawImage`
 * (`image-orientation: from-image`, mặc định). Nên "ảnh nguồn" ở đây là ảnh ĐÃ đúng hướng như người học thấy;
 * góc xoay thêm (`PhotoRotation`, theo chiều kim đồng hồ) áp sau đó — đúng thứ tự backend dùng (EXIF rồi `rotation`).
 */
import type { PhotoRotation } from "../llm/client";

/** Giới hạn của backend (`backend/app/ingestion/image.py`) — trình duyệt chỉ BÁO SỚM, máy chủ vẫn là thẩm quyền. */
export const PHOTO_MAX_PIXELS = 40_000_000;
/** Máy chủ thu cạnh dài về 3072 px trước khi gửi provider (`MAX_SEND_SIDE`); xuất lớn hơn chỉ tốn băng thông. */
export const PHOTO_SEND_MAX_SIDE = 3072;
/** Vùng chọn nhỏ hơn thế coi như chưa chọn (một cú chạm nhầm). */
export const MIN_CROP_PX = 8;

export interface Size {
  width: number;
  height: number;
}

export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

/** Vùng chọn theo % của ảnh hiển thị (đơn vị `"%"` của react-image-crop). */
export type PercentRect = Rect;

export function rotateLeft(r: PhotoRotation): PhotoRotation {
  return ((r + 270) % 360) as PhotoRotation;
}

export function rotateRight(r: PhotoRotation): PhotoRotation {
  return ((r + 90) % 360) as PhotoRotation;
}

/** Kích thước ảnh sau khi xoay `r` theo chiều kim đồng hồ. */
export function rotatedSize(src: Size, r: PhotoRotation): Size {
  return r % 180 === 0 ? { ...src } : { width: src.height, height: src.width };
}

/**
 * Ma trận Canvas `[a, b, c, d, e, f]` đưa điểm (x, y) của ảnh nguồn W×H sang không gian ảnh đã xoay `r` (chiều kim
 * đồng hồ): x′ = a·x + c·y + e, y′ = b·x + d·y + f.
 */
export function rotationMatrix(r: PhotoRotation, src: Size): [number, number, number, number, number, number] {
  const { width: w, height: h } = src;
  switch (r) {
    case 0:
      return [1, 0, 0, 1, 0, 0];
    case 90:
      return [0, 1, -1, 0, h, 0];          // (x, y) → (h − y, x)
    case 180:
      return [-1, 0, 0, -1, w, h];         // (x, y) → (w − x, h − y)
    case 270:
      return [0, -1, 1, 0, 0, w];          // (x, y) → (y, w − x)
  }
}

export function applyMatrix(m: readonly number[], x: number, y: number): [number, number] {
  return [m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]];
}

/**
 * % của ảnh hiển thị → hình chữ nhật NGUYÊN trong pixel gốc (ảnh đã xoay), bị kẹp trong biên.
 * `null` khi vùng rỗng hoặc nhỏ hơn `MIN_CROP_PX` — không bao giờ xuất một ảnh rỗng hay một vùng ngoài ảnh.
 */
export function cropToPixels(pct: PercentRect | null | undefined, image: Size): Rect | null {
  if (!pct || !(pct.width > 0) || !(pct.height > 0)) return null;
  const x0 = clamp((pct.x / 100) * image.width, 0, image.width);
  const y0 = clamp((pct.y / 100) * image.height, 0, image.height);
  const x1 = clamp(((pct.x + pct.width) / 100) * image.width, 0, image.width);
  const y1 = clamp(((pct.y + pct.height) / 100) * image.height, 0, image.height);
  // ε: % → pixel đi qua phép chia dấu phẩy động (50/600·100%·3000 = 249.999…); không có nó, một biên nằm ĐÚNG trên
  // một pixel bị floor/ceil lệch ra ngoài 1 px.
  const EPS = 1e-6;
  const x = Math.floor(x0 + EPS);
  const y = Math.floor(y0 + EPS);
  const width = Math.ceil(x1 - EPS) - x;
  const height = Math.ceil(y1 - EPS) - y;
  if (width < MIN_CROP_PX || height < MIN_CROP_PX) return null;
  return { x, y, width: Math.min(width, image.width - x), height: Math.min(height, image.height - y) };
}

/** Vùng chọn phủ (gần như) cả ảnh ⇒ không cần cắt. */
export function coversWholeImage(rect: Rect | null, image: Size): boolean {
  return !rect || (rect.x <= 1 && rect.y <= 1 && rect.width >= image.width - 2 && rect.height >= image.height - 2);
}

/** Hệ số thu nhỏ (≤ 1) để cạnh dài nhất ≤ `maxSide`. Không bao giờ phóng to. */
export function exportScale(region: Size, maxSide = PHOTO_SEND_MAX_SIDE): number {
  const side = Math.max(region.width, region.height);
  return side > maxSide ? maxSide / side : 1;
}

export function exceedsPixelLimit(image: Size): boolean {
  return image.width * image.height > PHOTO_MAX_PIXELS;
}

/**
 * Định dạng xuất: PNG giữ nét chữ/ký hiệu của ảnh chụp màn hình và tài liệu PNG; ảnh chụp (JPEG/WEBP) ra JPEG chất
 * lượng cao. Không nén mạnh: dấu phẩy, dấu căn, ký hiệu ⊥ ∥ và dấu phẩy trên tên đỉnh phải còn đọc được.
 */
export function exportFormats(sourceMime: string | undefined): { mime: "image/png" | "image/jpeg"; quality?: number }[] {
  const jpeg = [{ mime: "image/jpeg" as const, quality: 0.92 }, { mime: "image/jpeg" as const, quality: 0.85 }];
  return sourceMime === "image/png" ? [{ mime: "image/png" }, ...jpeg] : jpeg;
}

export function uploadFileName(original: string, mime: string, cropped: boolean): string {
  const base = original.replace(/\.[^.]+$/, "") || "anh-de-bai";
  return `${base}${cropped ? "-vung-chon" : "-da-xoay"}.${mime === "image/png" ? "png" : "jpg"}`;
}

function clamp(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

/* ── Canvas (trình duyệt) ─────────────────────────────────────────────── */

function toBlob(canvas: HTMLCanvasElement, mime: string, quality?: number): Promise<Blob | null> {
  return new Promise((resolve) => canvas.toBlob(resolve, mime, quality));
}

/**
 * Vẽ đúng vùng `rect` (pixel gốc của ảnh đã xoay `r`) của `img` ra một tệp ảnh để gửi `/api/image/extract`.
 * `rect = null` ⇒ cả ảnh (dùng khi chỉ xoay). Một lần `drawImage` với ma trận xoay + dịch vùng chọn: không có canvas
 * trung gian cỡ cả ảnh. Bộ đệm canvas được giải phóng (`width = height = 0`) ngay sau khi mã hoá.
 */
export async function renderPhotoUpload(
  img: CanvasImageSource & { naturalWidth: number; naturalHeight: number },
  r: PhotoRotation,
  rect: Rect | null,
  source: { name: string; type: string },
  maxBytes: number,
): Promise<File> {
  const src = { width: img.naturalWidth, height: img.naturalHeight };
  const turned = rotatedSize(src, r);
  const region = rect ?? { x: 0, y: 0, ...turned };
  const s = exportScale(region);
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(region.width * s));
  canvas.height = Math.max(1, Math.round(region.height * s));
  try {
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("Trình duyệt không xử lý được ảnh này.");
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.fillStyle = "#ffffff";                       // nền trắng cho PNG trong suốt khi phải ra JPEG
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.scale(s, s);
    ctx.translate(-region.x, -region.y);
    const [a, b, c, d, e, f] = rotationMatrix(r, src);
    ctx.transform(a, b, c, d, e, f);
    ctx.drawImage(img, 0, 0);
    for (const fmt of exportFormats(source.type)) {
      const blob = await toBlob(canvas, fmt.mime, fmt.quality);
      if (blob && blob.size > 0 && blob.size <= maxBytes) {
        return new File([blob], uploadFileName(source.name, fmt.mime, rect !== null), { type: fmt.mime });
      }
    }
    throw new Error("Vùng ảnh quá lớn để gửi. Em khoanh vùng nhỏ hơn hoặc chụp lại gần hơn.");
  } finally {
    canvas.width = 0;
    canvas.height = 0;
  }
}

/** Ảnh xem trước đã xoay (độ phân giải màn hình) cho khung khoanh vùng; % trên nó = % trên ảnh gốc đã xoay. */
export async function renderRotatedPreview(
  img: CanvasImageSource & { naturalWidth: number; naturalHeight: number },
  r: PhotoRotation,
  maxSide = 1600,
): Promise<Blob> {
  const src = { width: img.naturalWidth, height: img.naturalHeight };
  const turned = rotatedSize(src, r);
  const s = exportScale(turned, maxSide);
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(turned.width * s));
  canvas.height = Math.max(1, Math.round(turned.height * s));
  try {
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("Trình duyệt không xử lý được ảnh này.");
    ctx.imageSmoothingQuality = "high";
    ctx.scale(s, s);
    const [a, b, c, d, e, f] = rotationMatrix(r, src);
    ctx.transform(a, b, c, d, e, f);
    ctx.drawImage(img, 0, 0);
    const blob = await toBlob(canvas, "image/jpeg", 0.9);
    if (!blob) throw new Error("Trình duyệt không xử lý được ảnh này.");
    return blob;
  } finally {
    canvas.width = 0;
    canvas.height = 0;
  }
}

/** Giải mã một tệp ảnh thành `<img>` (đã áp EXIF). Trả cả URL để nơi gọi THU HỒI. */
export function loadImage(file: Blob): Promise<{ img: HTMLImageElement; url: string }> {
  const url = URL.createObjectURL(file);
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.decoding = "async";
    img.onload = () => resolve({ img, url });
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Không đọc được ảnh này. Em chọn ảnh PNG, JPEG hoặc WEBP khác."));
    };
    img.src = url;
  });
}
