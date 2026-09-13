# -*- coding: utf-8 -*-
"""Chuẩn hoá ảnh đề bài — `app/ingestion/image.py`. 0 lượt gọi mạng.

PHOTO_PROBLEM_TO_SCENE_END_TO_END §4/§9. Mọi ảnh ở đây DỰNG TẠI CHỖ bằng Pillow
nên test tất định và không phụ thuộc tệp ngoài. Ảnh mang một khối ĐỎ 8×8 ở góc
trên-trái để lần theo mọi phép xoay bằng điểm ảnh, không bằng lời khai.
"""

from __future__ import annotations

import base64
import io
import struct
import zlib

import pytest
from PIL import ExifTags, Image, PngImagePlugin

from app.ingestion.image import (
    MAX_IMAGE_BYTES,
    MAX_SEND_SIDE,
    ImageRejected,
    decode_image_base64,
    normalize_image,
    sniff_image_mime,
)

DO = (255, 0, 0)


def _anh_danh_dau(size=(40, 30)) -> Image.Image:
    img = Image.new("RGB", size, (255, 255, 255))
    img.paste(DO, (0, 0, 8, 8))
    return img


def _ma_hoa(img: Image.Image, fmt: str, **kw) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt, **kw)
    return buf.getvalue()


def _mo(b: bytes) -> Image.Image:
    im = Image.open(io.BytesIO(b))
    im.load()
    return im


def _goc_do(im: Image.Image) -> str:
    """Khối đỏ đang nằm ở góc nào."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    for ten, (x, y) in {
        "tren_trai": (3, 3),
        "tren_phai": (w - 4, 3),
        "duoi_trai": (3, h - 4),
        "duoi_phai": (w - 4, h - 4),
    }.items():
        r, g, b = rgb.getpixel((x, y))
        if r > 200 and g < 80 and b < 80:
            return ten
    return "khong_thay"


def _ma(fn, *a, **kw) -> str:
    with pytest.raises(ImageRejected) as exc:
        fn(*a, **kw)
    return exc.value.code


# ── định dạng ──────────────────────────────────────────────────

@pytest.mark.parametrize(
    "fmt, mime", [("PNG", "image/png"), ("JPEG", "image/jpeg"), ("WEBP", "image/webp")]
)
def test_ba_dinh_dang_hop_le_deu_chuan_hoa_ve_JPEG(fmt, mime):
    raw = _ma_hoa(_anh_danh_dau(), fmt, **({} if fmt == "PNG" else {"quality": 95}))
    assert sniff_image_mime(raw) == mime
    n = normalize_image(raw, mime)
    assert (n.source_mime, n.mime_type) == (mime, "image/jpeg")
    assert (n.width, n.height) == (40, 30)
    ra = _mo(n.data)
    assert ra.format == "JPEG" and ra.size == (40, 30)
    assert _goc_do(ra) == "tren_trai"


def test_khong_khai_mime_thi_dinh_dang_suy_tu_NOI_DUNG():
    assert normalize_image(_ma_hoa(_anh_danh_dau(), "PNG")).source_mime == "image/png"


def test_gia_duoi_noi_dung_JPEG_khai_PNG_bi_tu_choi():
    raw = _ma_hoa(_anh_danh_dau(), "JPEG")
    assert _ma(normalize_image, raw, "image/png") == "IMAGE_TYPE_MISMATCH"
    assert _ma(normalize_image, _ma_hoa(_anh_danh_dau(), "PNG"), "image/webp") == "IMAGE_TYPE_MISMATCH"


def test_mime_ngoai_danh_sach_bi_tu_choi():
    gif = _ma_hoa(_anh_danh_dau(), "GIF")
    assert _ma(normalize_image, gif, "image/gif") == "IMAGE_UNSUPPORTED_FORMAT"
    assert _ma(normalize_image, gif) == "IMAGE_UNSUPPORTED_FORMAT"
    assert _ma(normalize_image, "không phải ảnh".encode()) == "IMAGE_UNSUPPORTED_FORMAT"


def test_tep_hong_co_magic_bytes_bi_tu_choi():
    assert _ma(normalize_image, b"\x89PNG\r\n\x1a\n" + b"rac" * 20, "image/png") == "IMAGE_CORRUPT"


def test_jpeg_bi_cat_ngang_bi_tu_choi():
    nhieu = Image.effect_noise((256, 256), 60).convert("RGB")
    raw = _ma_hoa(nhieu, "JPEG", quality=95)
    assert _ma(normalize_image, raw[: len(raw) // 2], "image/jpeg") == "IMAGE_CORRUPT"


# ── trần ───────────────────────────────────────────────────────

def test_qua_10MB_bi_tu_choi_ca_o_byte_lan_base64():
    raw = b"\x89PNG\r\n\x1a\n" + b"0" * (MAX_IMAGE_BYTES + 1)
    assert _ma(normalize_image, raw) == "IMAGE_TOO_LARGE"
    assert _ma(decode_image_base64, base64.b64encode(raw).decode()) == "IMAGE_TOO_LARGE"


def _png_khai_kich_thuoc(w: int, h: int) -> bytes:
    """PNG 1×1 thật, sửa IHDR để KHAI kích thước lớn — kiểu một quả bom giải nén."""
    raw = bytearray(_ma_hoa(Image.new("RGB", (1, 1)), "PNG"))
    ihdr = bytes(raw[12:29])  # b"IHDR" + 13 byte dữ liệu
    moi = b"IHDR" + struct.pack(">II", w, h) + ihdr[12:]
    raw[12:29] = moi
    raw[29:33] = struct.pack(">I", zlib.crc32(moi) & 0xFFFFFFFF)
    return bytes(raw)


def test_qua_nhieu_diem_anh_bi_chan_TU_HEADER_truoc_khi_giai_nen():
    assert _ma(normalize_image, _png_khai_kich_thuoc(7000, 7000), "image/png") == "IMAGE_TOO_MANY_PIXELS"


def test_anh_qua_rong_duoc_thu_nho_ve_tran_gui_provider():
    n = normalize_image(_ma_hoa(Image.new("RGB", (4000, 100), (255, 255, 255)), "PNG"))
    assert n.downscaled is True
    assert max(n.width, n.height) == MAX_SEND_SIDE


def test_base64_hong_va_rong_bi_tu_choi():
    assert _ma(decode_image_base64, "@@@khong-phai-base64@@@") == "IMAGE_INVALID_ENCODING"
    assert _ma(decode_image_base64, "") == "IMAGE_EMPTY"


# ── EXIF ───────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "huong, goc, kich_thuoc",
    [
        (1, "tren_trai", (40, 30)),
        (3, "duoi_phai", (40, 30)),
        (6, "tren_phai", (30, 40)),
        (8, "duoi_trai", (30, 40)),
    ],
)
def test_xoay_theo_EXIF_orientation(huong, goc, kich_thuoc):
    ex = Image.Exif()
    ex[ExifTags.Base.Orientation] = huong
    raw = _ma_hoa(_anh_danh_dau(), "JPEG", quality=95, exif=ex.tobytes())
    n = normalize_image(raw, "image/jpeg")
    assert n.exif_orientation == huong
    ra = _mo(n.data)
    assert ra.size == kich_thuoc
    assert _goc_do(ra) == goc


def test_GPS_va_moi_metadata_bi_go_khoi_anh_gui_di():
    ex = Image.Exif()
    ex[ExifTags.Base.Make] = "May chup thu"
    ex[ExifTags.IFD.GPSInfo] = {
        ExifTags.GPS.GPSLatitudeRef: "N",
        ExifTags.GPS.GPSLatitude: (21.0, 1.0, 30.0),
    }
    raw = _ma_hoa(_anh_danh_dau(), "JPEG", quality=95, exif=ex.tobytes())
    # TIỀN ĐIỀU KIỆN: ảnh nguồn THẬT SỰ mang GPS — không có thì test không chứng minh gì.
    nguon = Image.open(io.BytesIO(raw)).getexif()
    assert nguon.get_ifd(ExifTags.IFD.GPSInfo), "không dựng được ảnh nguồn có GPS"

    n = normalize_image(raw, "image/jpeg")
    assert n.source_had_gps is True and n.source_had_exif is True
    ra = Image.open(io.BytesIO(n.data))
    assert len(ra.getexif()) == 0
    assert "exif" not in ra.info and "icc_profile" not in ra.info
    assert b"Exif" not in n.data and b"May chup thu" not in n.data
    assert n.describe()["metadata_removed"] is True


# ── băm ────────────────────────────────────────────────────────

def test_cung_diem_anh_khac_metadata_thi_CUNG_bam():
    img = _anh_danh_dau()
    thong_tin = PngImagePlugin.PngInfo()
    thong_tin.add_text("Author", "ai do")
    ex = Image.Exif()
    ex[ExifTags.Base.Make] = "May khac"
    a = _ma_hoa(img, "PNG")
    b = _ma_hoa(img, "PNG", pnginfo=thong_tin, exif=ex.tobytes())
    assert a != b
    assert normalize_image(a).sha256 == normalize_image(b).sha256


def test_khac_mot_diem_anh_thi_khac_bam():
    a = _anh_danh_dau()
    b = _anh_danh_dau()
    b.putpixel((20, 20), (0, 0, 0))
    assert normalize_image(_ma_hoa(a, "PNG")).sha256 != normalize_image(_ma_hoa(b, "PNG")).sha256


def test_xoay_cua_nguoi_hoc_la_HOAN_VI_chinh_xac():
    img = _anh_danh_dau()
    goc = normalize_image(_ma_hoa(img, "PNG"))
    da_xoay = img.transpose(Image.Transpose.ROTATE_270)  # 90° cùng chiều kim đồng hồ
    assert normalize_image(_ma_hoa(da_xoay, "PNG"), rotation=270).sha256 == goc.sha256

    n90 = normalize_image(_ma_hoa(img, "PNG"), rotation=90)
    assert (n90.width, n90.height) == (30, 40)
    assert _goc_do(_mo(n90.data)) == "tren_phai"
    assert n90.sha256 != goc.sha256
    assert _ma(normalize_image, _ma_hoa(img, "PNG"), rotation=45) == "IMAGE_BAD_ROTATION"


def test_nen_trong_suot_thanh_TRANG_khong_thanh_den():
    n = normalize_image(_ma_hoa(Image.new("RGBA", (10, 10), (0, 0, 0, 0)), "PNG"))
    r, g, b = _mo(n.data).getpixel((5, 5))
    assert min(r, g, b) >= 245
