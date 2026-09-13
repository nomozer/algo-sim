"""Chuẩn hoá ẢNH ĐỀ BÀI trước mọi lượt gọi provider — thẩm quyền DUY NHẤT.

`PHOTO_PROBLEM_TO_SCENE_END_TO_END_IMPLEMENTATION` (2026-09-13).

Trước wave này, ảnh chỉ bị soi **magic bytes** rồi đi nguyên byte sang Gemini:
không giải mã, không xoá EXIF (kể cả toạ độ GPS nơi chụp), không trần số điểm
ảnh, và băm — nếu có — là băm TỆP chứ không phải băm NỘI DUNG. Hai ảnh giống hệt
nhau chỉ khác metadata thì là hai khoá khác nhau.

Mọi đường nhận ảnh (`/api/image/extract` và nhánh `image` cũ của
`ingest_to_text`) đi qua đúng hàm `normalize_image` dưới đây. Đừng dựng bản thứ
hai ở chỗ khác — kho này đã phải đi dọn thẩm quyền trùng ba lần.

Thứ tự có chủ đích:

    base64 → trần BYTE → nhận dạng định dạng bằng NỘI DUNG → so với MIME khai
    → đọc HEADER → trần ĐIỂM ẢNH (trước khi giải nén) → giải mã đầy đủ
    → xoay theo EXIF → xoay theo người dùng → RGB → thu nhỏ nếu quá lớn
    → băm ĐIỂM ẢNH → mã hoá lại từ điểm ảnh thô (không mang theo metadata nào)

⚠️ Ảnh là dữ liệu KHÔNG TIN CẬY. Module này không bao giờ ghi log nội dung ảnh
hay chuỗi base64.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

#: Trần dung lượng tệp gốc (§4 mặc định 10 MB).
MAX_IMAGE_BYTES = 10 * 1024 * 1024
#: Trần số điểm ảnh SAU KHI GIẢI MÃ — chặn "bom giải nén": một PNG vài KB có thể
#: khai 30000×30000 và nuốt vài GB RAM lúc `load()`. Kiểm từ header, trước `load()`.
MAX_IMAGE_PIXELS = 40_000_000
#: Cạnh dài tối đa gửi cho provider. 3072 px vẫn đọc được chỉ số dưới và số mũ
#: cỡ chữ 8 pt trên một trang A4 chụp trọn khung; lớn hơn chỉ tốn băng thông.
MAX_SEND_SIDE = 3072
JPEG_QUALITY = 90

SUPPORTED_IMAGE_MIMES: tuple[str, ...] = ("image/png", "image/jpeg", "image/webp")
_PIL_FORMAT = {"image/png": "PNG", "image/jpeg": "JPEG", "image/webp": "WEBP"}

#: EXIF tag 0x0112 = Orientation, 0x8825 = con trỏ GPS IFD.
_EXIF_ORIENTATION = 0x0112
_EXIF_GPS_IFD = 0x8825

#: Xoay THEO CHIỀU KIM ĐỒNG HỒ. `transpose` là phép hoán vị điểm ảnh chính xác,
#: không nội suy — xoay 4 lần phải ra đúng ảnh ban đầu từng byte.
_XOAY = {
    90: Image.Transpose.ROTATE_270,
    180: Image.Transpose.ROTATE_180,
    270: Image.Transpose.ROTATE_90,
}


class ImageRejected(ValueError):
    """Ảnh bị từ chối TRƯỚC khi chạm provider. `code` máy đọc, thông điệp cho người học."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class NormalizedImage:
    """Ảnh đã chuẩn hoá — thứ DUY NHẤT được phép gửi cho provider."""

    data: bytes
    mime_type: str
    #: SHA-256 trên ĐIỂM ẢNH đã chuẩn hoá (kèm kích thước), không trên byte tệp.
    sha256: str
    width: int
    height: int
    source_mime: str
    exif_orientation: int
    rotation_applied: int
    downscaled: bool
    source_had_exif: bool
    source_had_gps: bool

    def base64(self) -> str:
        return base64.b64encode(self.data).decode("ascii")

    def describe(self) -> dict:
        """Mô tả an toàn để trả về client — không chứa byte ảnh."""
        return {
            "sha256": self.sha256,
            "width": self.width,
            "height": self.height,
            "source_mime": self.source_mime,
            "exif_orientation": self.exif_orientation,
            "rotation_applied": self.rotation_applied,
            "downscaled": self.downscaled,
            "metadata_removed": True,
            "source_had_gps": self.source_had_gps,
        }


def sniff_image_mime(raw: bytes) -> str | None:
    """Định dạng suy từ NỘI DUNG. Đuôi tệp và MIME khai báo không được tin."""
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return None


def decode_image_base64(content: str) -> bytes:
    """Giải base64 có trần. Trần kiểm TRƯỚC khi giải để không cấp phát vô ích."""
    if not isinstance(content, str) or not content:
        raise ImageRejected("IMAGE_EMPTY", "Ảnh rỗng.")
    # 4 ký tự base64 = 3 byte; chuỗi dài hơn mức này chắc chắn vượt trần.
    if len(content) > (MAX_IMAGE_BYTES * 4) // 3 + 8:
        raise ImageRejected(
            "IMAGE_TOO_LARGE", f"Ảnh quá lớn (tối đa {MAX_IMAGE_BYTES // (1024 * 1024)}MB)."
        )
    try:
        raw = base64.b64decode(content, validate=True)
    except (binascii.Error, ValueError):
        raise ImageRejected("IMAGE_INVALID_ENCODING", "Ảnh không phải dữ liệu base64 hợp lệ.")
    if not raw:
        raise ImageRejected("IMAGE_EMPTY", "Ảnh rỗng.")
    if len(raw) > MAX_IMAGE_BYTES:
        raise ImageRejected(
            "IMAGE_TOO_LARGE", f"Ảnh quá lớn (tối đa {MAX_IMAGE_BYTES // (1024 * 1024)}MB)."
        )
    return raw


def _hong() -> ImageRejected:
    return ImageRejected(
        "IMAGE_CORRUPT", "Không đọc được ảnh (tệp hỏng hoặc không đúng định dạng PNG/JPEG/WEBP)."
    )


def _ve_rgb(img: Image.Image) -> Image.Image:
    """RGB phẳng. Vùng trong suốt phủ nền TRẮNG — nền đen làm chữ đen biến mất."""
    co_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
    if co_alpha:
        rgba = img.convert("RGBA")
        nen = Image.new("RGB", rgba.size, (255, 255, 255))
        nen.paste(rgba, mask=rgba.getchannel("A"))
        return nen
    return img.convert("RGB")


def normalize_image(
    raw: bytes, declared_mime: str | None = None, rotation: int = 0
) -> NormalizedImage:
    """Kiểm, chuẩn hoá và mã hoá lại một ảnh đề bài. Ném `ImageRejected`."""
    if declared_mime is not None and declared_mime not in SUPPORTED_IMAGE_MIMES:
        raise ImageRejected(
            "IMAGE_UNSUPPORTED_FORMAT",
            f'Định dạng ảnh "{declared_mime}" không được hỗ trợ. Chỉ nhận PNG, JPEG hoặc WEBP.',
        )
    if len(raw) > MAX_IMAGE_BYTES:
        raise ImageRejected(
            "IMAGE_TOO_LARGE", f"Ảnh quá lớn (tối đa {MAX_IMAGE_BYTES // (1024 * 1024)}MB)."
        )
    thuc = sniff_image_mime(raw)
    if thuc is None:
        if declared_mime is not None:
            raise ImageRejected(
                "IMAGE_TYPE_MISMATCH",
                "Nội dung ảnh không khớp định dạng khai báo (file có thể bị giả đuôi).",
            )
        raise ImageRejected(
            "IMAGE_UNSUPPORTED_FORMAT", "Tệp không phải ảnh PNG, JPEG hoặc WEBP."
        )
    if declared_mime is not None and declared_mime != thuc:
        raise ImageRejected(
            "IMAGE_TYPE_MISMATCH",
            "Nội dung ảnh không khớp định dạng khai báo (file có thể bị giả đuôi).",
        )
    if rotation not in (0, 90, 180, 270):
        raise ImageRejected("IMAGE_BAD_ROTATION", "Góc xoay ảnh không hợp lệ.")

    try:
        img = Image.open(io.BytesIO(raw))
        rong, cao = img.size
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise _hong()
    if img.format != _PIL_FORMAT[thuc]:
        raise _hong()
    if rong <= 0 or cao <= 0 or rong * cao > MAX_IMAGE_PIXELS:
        raise ImageRejected(
            "IMAGE_TOO_MANY_PIXELS",
            f"Ảnh có quá nhiều điểm ảnh (tối đa {MAX_IMAGE_PIXELS // 1_000_000} triệu).",
        )
    try:
        img.load()
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise _hong()

    exif = img.getexif()
    try:
        huong = int(exif.get(_EXIF_ORIENTATION, 1) or 1)
    except (TypeError, ValueError):
        huong = 1
    if huong not in range(1, 9):
        huong = 1
    co_gps = _EXIF_GPS_IFD in exif
    co_exif = len(exif) > 0

    img = ImageOps.exif_transpose(img)
    if rotation:
        img = img.transpose(_XOAY[rotation])
    img = _ve_rgb(img)

    thu_nho = max(img.size) > MAX_SEND_SIDE
    if thu_nho:
        img.thumbnail((MAX_SEND_SIDE, MAX_SEND_SIDE), Image.Resampling.LANCZOS)

    # DỰNG LẠI TỪ ĐIỂM ẢNH THÔ. `convert()` chép `info` (exif, icc_profile…) sang
    # ảnh mới, và tuỳ plugin/phiên bản mà `save()` có mang chúng theo hay không.
    # Ảnh dựng từ `frombytes` không có `info` nào — không có gì để rò.
    diem = img.tobytes()
    sach = Image.frombytes("RGB", img.size, diem)
    bam = hashlib.sha256(b"RGB:%dx%d:" % sach.size + diem).hexdigest()
    buf = io.BytesIO()
    sach.save(buf, format="JPEG", quality=JPEG_QUALITY)

    return NormalizedImage(
        data=buf.getvalue(),
        mime_type="image/jpeg",
        sha256=bam,
        width=sach.size[0],
        height=sach.size[1],
        source_mime=thuc,
        exif_orientation=huong,
        rotation_applied=rotation,
        downscaled=thu_nho,
        source_had_exif=co_exif,
        source_had_gps=co_gps,
    )
