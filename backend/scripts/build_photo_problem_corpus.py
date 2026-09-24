# -*- coding: utf-8 -*-
"""Bộ ảnh nghiệm thu TỔNG HỢP cho đường ảnh → mô phỏng. **0 API call.**

`PHOTO_PROBLEM_TO_SCENE_END_TO_END_IMPLEMENTATION §10`.

⚠️ ĐÂY KHÔNG PHẢI ẢNH CHỤP THẬT. Phiên triển khai không có máy ảnh hay giấy in:
mọi ảnh ở đây được VẼ bằng Pillow (chữ tiếng Việt, hình minh hoạ đơn giản) rồi
làm xấu đi một cách TẤT ĐỊNH — nghiêng phối cảnh, mờ, thiếu sáng, xoay theo
EXIF. Chúng chứng minh được đường CHUẨN HOÁ và có ground truth chính xác, nhưng
KHÔNG chứng minh được một provider thật đọc được ảnh chụp thật: nền giấy, bóng
tay, nếp gấp, chữ viết tay đều vắng mặt. Mọi báo cáo dẫn bộ này phải mang
`CORPUS_KIND = SYNTHETIC_RENDERED` và `REAL_PHOTO_CORPUS = NOT_ESTABLISHED`.

Ground truth KHÔNG tự viết: văn bản và kỳ vọng cảnh lấy từ fixture đã khoá của
`product-ui-result-rendering` (p1–p7, n1) — cùng đề mà lượt `thesis-final` đã
chạy thật. Không ảnh nào chứa thông tin cá nhân.

Hai chế độ:

    (mặc định)  dựng ảnh + `CORPUS.json` + fixture trình duyệt. ĐÃ CÓ thì TỪ
                CHỐI ghi đè — đó là tính năng: băm ảnh là mốc so sánh.
    --kiem      đọc ảnh ĐÃ COMMIT, chạy lại chuẩn hoá tất định, đối chiếu băm và
                bất biến (EXIF xoay đúng chiều, GPS bị gỡ), ghi
                `OFFLINE_NORMALIZATION.json`. Không cần font.

Font: `C:/Windows/Fonts/arial.ttf` (đủ dấu tiếng Việt). Không có ⇒ chế độ dựng dừng.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
from pathlib import Path

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))
GOC = BE.parent

from PIL import ExifTags, Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont  # noqa: E402

from app.ingestion.image import normalize_image, sniff_image_mime  # noqa: E402
from app.ingestion.image_extraction import (  # noqa: E402
    ExtractionResult,
    ImageProblemExtraction,
    vision_identity,
)

RA = GOC / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene"
ANH_DIR = RA / "corpus"
FIX = GOC / "docs" / "evaluation" / "geometry" / "product-ui-result-rendering" / "fixtures"
FONT = Path("C:/Windows/Fonts/arial.ttf")

NEN_GIAY = (250, 248, 242)
MUC = (28, 28, 30)
NEN_BAN = (92, 90, 96)

#: (id, fixture ground truth | None, định dạng, suy biến, hình minh hoạ, kỳ vọng)
KE_HOACH = [
    ("c01_ro_chop_thiet_dien", "p1_chop_thiet_dien_khoang_cach", "PNG", [], None, "ACCEPT"),
    ("c02_ro_mat_cau", "p3_mat_cau_va_thiet_dien_tron", "JPEG", [], None, "ACCEPT"),
    ("c03_ro_hinh_tru", "p4_hinh_tru_the_tich_va_xung_quanh", "WEBP", [], None, "ACCEPT"),
    ("c04_nghieng_hinh_non", "p5_hinh_non_the_tich_va_xung_quanh", "JPEG", ["phoi_canh"], None, "ACCEPT"),
    ("c05_nghieng_cong_thuc_hinh_tru", "p6_thiet_dien_elip_cua_hinh_tru", "JPEG",
     ["phoi_canh"], "tru", "ACCEPT"),
    ("c06_toi_mo_elip_non", "p7_thiet_dien_elip_cua_hinh_non", "JPEG", ["toi", "mo"], None, "ACCEPT"),
    ("c07_mo_chop_ngu_giac", "p2_chop_day_ngu_giac_lom", "JPEG", ["mo_nhe", "toi_nhe"], None, "ACCEPT"),
    ("c08_de_va_hinh_chop", "p1_chop_thiet_dien_khoang_cach", "PNG", [], "chop", "ACCEPT"),
    ("c09_de_va_hinh_cau", "p3_mat_cau_va_thiet_dien_tron", "WEBP", [], "cau", "ACCEPT"),
    ("c10_exif_xoay_gps", "p4_hinh_tru_the_tich_va_xung_quanh", "PNG", ["exif_6", "gps"], None, "ACCEPT"),
    ("c11_chi_co_hinh", None, "PNG", [], "chop", "REJECT_AT_A:MISSING_PROBLEM_TEXT"),
    ("c12_ngoai_nang_luc", "n1_khoi_tron_xoay_tong_quat", "JPEG", [], None, "REFUSE_AT_B"),
]


def _bam(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _fixture(cid: str) -> dict:
    return json.loads((FIX / f"{cid}.json").read_text(encoding="utf-8"))


def _diem_co_ten(text: str) -> list[str]:
    """Tên điểm có toạ độ trong đề, theo thứ tự — `A(0;0;0)`, `A₁(0;0;10)`."""
    ra: list[str] = []
    for m in re.finditer(r"(?<![\w₀-₉])([A-Z][₀-₉0-9']?)\s*\(\s*-?\d", text):
        if m.group(1) not in ra:
            ra.append(m.group(1))
    return ra


# ── vẽ ─────────────────────────────────────────────────────────

def _ngat_dong(text: str, font, rong: int) -> list[str]:
    dong, hien = [], ""
    for tu in text.split():
        thu = f"{hien} {tu}".strip()
        if font.getlength(thu) <= rong:
            hien = thu
        else:
            dong.append(hien)
            hien = tu
    if hien:
        dong.append(hien)
    return dong


def _net_dut(d: ImageDraw.ImageDraw, a, b, w=3, doan=12):
    (x0, y0), (x1, y1) = a, b
    dai = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    n = max(1, int(dai // doan))
    for i in range(0, n, 2):
        t0, t1 = i / n, min(1.0, (i + 1) / n)
        d.line([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0),
                (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)], fill=MUC, width=w)


def _ve_hinh(d: ImageDraw.ImageDraw, loai: str, ox: int, oy: int, font) -> None:
    if loai == "chop":
        S, A, B, C, D = (ox + 190, oy), (ox, oy + 300), (ox + 250, oy + 340), (ox + 400, oy + 250), (ox + 150, oy + 210)
        for p, q in ((S, A), (S, B), (S, C), (A, B), (B, C)):
            d.line([p, q], fill=MUC, width=3)
        for p, q in ((S, D), (A, D), (D, C)):
            _net_dut(d, p, q)
        for ten, (x, y), (dx, dy) in (("S", S, (-8, -40)), ("A", A, (-34, 0)), ("B", B, (-6, 8)),
                                       ("C", C, (12, -6)), ("D", D, (-36, -30))):
            d.text((x + dx, y + dy), ten, font=font, fill=MUC)
    elif loai == "cau":
        cx, cy, r = ox + 200, oy + 170, 160
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=MUC, width=3)
        d.arc([cx - r, cy - 40, cx + r, cy + 40], 180, 360, fill=MUC, width=2)
        d.arc([cx - r, cy - 40, cx + r, cy + 40], 0, 180, fill=MUC, width=3)
        d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=MUC)
        d.text((cx + 10, cy - 36), "I", font=font, fill=MUC)
    elif loai == "tru":
        cx, top, bot, rx, ry = ox + 200, oy + 30, oy + 320, 150, 40
        d.ellipse([cx - rx, top - ry, cx + rx, top + ry], outline=MUC, width=3)
        d.arc([cx - rx, bot - ry, cx + rx, bot + ry], 0, 180, fill=MUC, width=3)
        d.arc([cx - rx, bot - ry, cx + rx, bot + ry], 180, 360, fill=MUC, width=2)
        d.line([(cx - rx, top), (cx - rx, bot)], fill=MUC, width=3)
        d.line([(cx + rx, top), (cx + rx, bot)], fill=MUC, width=3)
        d.text((cx - 8, bot + 6), "O", font=font, fill=MUC)
        d.text((cx - 8, top - 36), "K", font=font, fill=MUC)


def _trang(text: str | None, hinh: str | None) -> Image.Image:
    font = ImageFont.truetype(str(FONT), 30)
    rong, le = 1120, 64
    dong = _ngat_dong(text, font, rong - 2 * le) if text else []
    cao_dong = 44
    cao_hinh = 400 if hinh else 0
    cao = le * 2 + len(dong) * cao_dong + cao_hinh + (40 if dong else 0)
    img = Image.new("RGB", (rong, max(cao, 480)), NEN_GIAY)
    d = ImageDraw.Draw(img)
    y = le
    if dong:
        d.text((le, y), "Câu 1.", font=font, fill=MUC)
        y += cao_dong
        for s in dong:
            d.text((le, y), s, font=font, fill=MUC)
            y += cao_dong
        y += 20
    if hinh:
        _ve_hinh(d, hinh, (rong - 420) // 2, y + 20, font)
    return img


def _giai(A: list[list[float]], b: list[float]) -> list[float]:
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


def _phoi_canh(img: Image.Image, lech: float = 0.07) -> Image.Image:
    """Hình thang nhẹ + nghiêng 2,5° — kiểu chụp một trang đặt trên bàn."""
    w, h = img.size
    nguon = [(0, 0), (w, 0), (w, h), (0, h)]
    dich = [(w * lech, h * lech * 0.6), (w * (1 - lech * 0.5), 0), (w, h), (0, h * (1 - lech * 0.3))]
    A, b = [], []
    for (x, y), (u, v) in zip(dich, nguon):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        b.append(v)
    ra = img.transform((w, h), Image.Transform.PERSPECTIVE, _giai(A, b),
                       Image.Resampling.BICUBIC, fillcolor=NEN_BAN)
    return ra.rotate(-2.5, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=NEN_BAN)


def _suy_bien(img: Image.Image, cach: list[str]) -> Image.Image:
    for c in cach:
        if c == "phoi_canh":
            img = _phoi_canh(img)
        elif c == "toi":
            img = ImageEnhance.Contrast(ImageEnhance.Brightness(img).enhance(0.55)).enhance(0.8)
        elif c == "toi_nhe":
            img = ImageEnhance.Brightness(img).enhance(0.75)
        elif c == "mo":
            img = img.filter(ImageFilter.GaussianBlur(1.4))
        elif c == "mo_nhe":
            img = img.filter(ImageFilter.GaussianBlur(0.9))
    return img


def _exif(orientation: int | None, gps: bool) -> bytes:
    ex = Image.Exif()
    ex[ExifTags.Base.Make] = "May anh tong hop"
    if orientation:
        ex[ExifTags.Base.Orientation] = orientation
    if gps:
        ex[ExifTags.IFD.GPSInfo] = {
            ExifTags.GPS.GPSLatitudeRef: "N",
            ExifTags.GPS.GPSLatitude: (21.0, 1.0, 30.0),
            ExifTags.GPS.GPSLongitudeRef: "E",
            ExifTags.GPS.GPSLongitude: (105.0, 51.0, 12.0),
        }
    return ex.tobytes()


def _ma_hoa(img: Image.Image, fmt: str, exif: bytes | None = None) -> bytes:
    buf = io.BytesIO()
    kw: dict = {"quality": 88} if fmt in ("JPEG", "WEBP") else {}
    if exif:
        kw["exif"] = exif
    img.save(buf, format=fmt, **kw)
    return buf.getvalue()


_DUOI = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}


def _cache_version() -> str:
    """Đọc `CACHE_VERSION` từ NGUỒN — import `app.main` sẽ dựng DB chỉ để lấy một hằng."""
    m = re.search(r'^CACHE_VERSION = "([^"]+)"', (BE / "app" / "main.py").read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else "?"


def _ban_ghi_gia_lap(text: str, *, hinh: bool, khong_chac: list[dict] | None = None,
                     quan_sat: list[str] | None = None) -> ImageProblemExtraction:
    """Bản ghi DỰNG TAY cho fixture trình duyệt — không phải output của provider."""
    return ImageProblemExtraction.model_validate({
        "problem_text_verbatim": text, "problem_text_normalized": text,
        "math_expressions": [], "named_points": _diem_co_ten(text), "named_lines": [],
        "named_planes": [], "named_solids": [], "given_relations": [], "has_diagram": hinh,
        "diagram_observations": quan_sat or [], "text_diagram_conflicts": [],
        "uncertain_tokens": khong_chac or [], "missing_regions": [], "confidence": 0.86,
    })


def dung() -> int:
    if (RA / "CORPUS.json").exists():
        print(f"TỪ CHỐI: {RA / 'CORPUS.json'} đã tồn tại — bộ ảnh là mốc so sánh, không ghi đè. "
              "Dùng --kiem để đối chiếu.")
        return 2
    if not FONT.exists():
        print(f"Không có font {FONT} — không dựng được chữ tiếng Việt.")
        return 2
    ANH_DIR.mkdir(parents=True, exist_ok=True)
    muc: list[dict] = []
    for cid, nguon, fmt, cach, hinh, ky_vong in KE_HOACH:
        fx = _fixture(nguon) if nguon else None
        text = fx["problem_text"] if fx else None
        thang_dung = _trang(text, hinh)
        exif = None
        mong_doi_dung_chieu = None
        if "exif_6" in cach:
            # Nội dung xoay 90° NGƯỢC chiều kim đồng hồ + Orientation=6 ("xoay 90° cùng
            # chiều để xem") ⇒ sau `exif_transpose` phải trùng TỪNG ĐIỂM ẢNH với trang đứng.
            mong_doi_dung_chieu = normalize_image(_ma_hoa(thang_dung, "PNG")).sha256
            anh = thang_dung.transpose(Image.Transpose.ROTATE_90)
            exif = _exif(6, "gps" in cach)
        else:
            anh = _suy_bien(thang_dung, cach)
        raw = _ma_hoa(anh, fmt, exif)
        ten = f"{cid}{_DUOI[fmt]}"
        (ANH_DIR / ten).write_bytes(raw)
        muc.append({
            "id": cid,
            "file": f"corpus/{ten}",
            "file_sha256": _bam(raw),
            "format": fmt,
            "degradations": cach,
            "diagram": hinh,
            "ground_truth_source": f"docs/evaluation/geometry/product-ui-result-rendering/fixtures/{nguon}.json" if nguon else None,
            "ground_truth_text": text,
            "expected_named_points": _diem_co_ten(text) if text else [],
            "expected_scene_kinds": fx.get("expected_scene_kinds") if fx else [],
            "expected_scene_object_count": fx.get("expected_scene_object_count") if fx else 0,
            "expected_failure_stage_or_code": fx.get("expected_failure_stage_or_code") if fx else None,
            "expected_outcome": ky_vong,
            "expected_upright_normalized_sha256": mong_doi_dung_chieu,
        })
        print(f"  {ten:44s} {len(raw):>8d} byte  {', '.join(cach) or 'rõ'}")

    corpus = {
        "wave": "PHOTO_PROBLEM_TO_SCENE_END_TO_END_IMPLEMENTATION",
        # Đề của mọi ảnh lấy từ corpus lượt đo cuối (qua fixture hiển thị). Khai
        # KIỂM ĐƯỢC để guard chống nhiễm bẩn (`test_A5`) không coi bộ ảnh này là
        # "corpus phát triển" của lượt đo ấy — nó là artifact DẪN XUẤT.
        "source_artifact_path": "docs/evaluation/geometry/thesis-final-acceptance/CORPUS.json",
        "CORPUS_KIND": "SYNTHETIC_RENDERED",
        "REAL_PHOTO_CORPUS": "NOT_ESTABLISHED",
        "PERSONAL_DATA": "NONE",
        "generator": "backend/scripts/build_photo_problem_corpus.py",
        "font": "Arial (C:/Windows/Fonts/arial.ttf)",
        "coverage": {
            "ro_chup_thang": ["c01", "c02", "c03"],
            "nghieng_phoi_canh": ["c04", "c05"],
            "thieu_sang_hoac_mo": ["c06", "c07"],
            "de_va_hinh_minh_hoa": ["c05", "c08", "c09"],
            "xoay_theo_exif": ["c10"],
            "chi_co_hinh_thieu_du_kien": ["c11"],
            "ngoai_nang_luc": ["c12"],
            "ho_hinh": {"chop_da_dien": ["c01", "c07", "c08"], "mat_phang_thiet_dien": ["c01", "c05", "c06"],
                        "cau": ["c02", "c09"], "tru": ["c03", "c05", "c10"], "non": ["c04", "c06"]},
            "ten_diem_de_nham_O_0": ["c03", "c04", "c05", "c06", "c10"],
        },
        "items": muc,
    }
    (RA / "CORPUS.json").write_text(json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8")

    # Fixture trình duyệt: phản hồi `/api/image/extract` do CHÍNH mã backend dựng
    # (`assess_extraction` + `to_response`), để script trình duyệt không chép tay
    # một hình dạng có thể trôi. Bản ghi bên trong là GIẢ LẬP, không phải provider.
    ident = vision_identity(_cache_version())
    c09 = next(m for m in muc if m["id"] == "c09_de_va_hinh_cau")
    anh09 = normalize_image((RA / c09["file"]).read_bytes())
    x09 = _ban_ghi_gia_lap(
        c09["ground_truth_text"], hinh=True,
        khong_chac=[{"token": "0", "alternatives": ["O"], "location": "tâm I(0;0;0)", "reason": "nét số 0 tròn"}],
        quan_sat=["Hình cầu tâm I, một đường tròn cắt ngang."],
    )
    c11 = next(m for m in muc if m["id"] == "c11_chi_co_hinh")
    anh11 = normalize_image((RA / c11["file"]).read_bytes())
    x11 = _ban_ghi_gia_lap("", hinh=True, quan_sat=["Hình chóp tứ giác S.ABCD, không có chữ."])
    for ten, x, anh in (("browser_fixture_review.json", x09, anh09),
                        ("browser_fixture_rejected.json", x11, anh11)):
        phan_hoi = ExtractionResult(x, anh, ident, cached=False).to_response()
        phan_hoi["_nhan"] = "FIXTURE_DUNG_TAY — không phải output của provider"
        phan_hoi["source_artifact_path"] = "docs/evaluation/geometry/thesis-final-acceptance/CORPUS.json"
        (RA / ten).write_text(json.dumps(phan_hoi, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"→ {RA / 'CORPUS.json'}  ({len(muc)} ảnh, SYNTHETIC_RENDERED)")
    return kiem()


def kiem() -> int:
    corpus = json.loads((RA / "CORPUS.json").read_text(encoding="utf-8"))
    ket: list[dict] = []
    for m in corpus["items"]:
        raw = (RA / m["file"]).read_bytes()
        r: dict = {"id": m["id"], "file_sha256_khop": _bam(raw) == m["file_sha256"],
                   "sniffed_mime": sniff_image_mime(raw)}
        n = normalize_image(raw)
        ra = Image.open(io.BytesIO(n.data))
        r.update({
            "normalized_image_sha256": n.sha256,
            "normalized_size": [n.width, n.height],
            "exif_orientation": n.exif_orientation,
            "source_had_gps": n.source_had_gps,
            "output_exif_tags": len(ra.getexif()),
            "metadata_removed": len(ra.getexif()) == 0 and "icc_profile" not in ra.info,
        })
        if m["expected_upright_normalized_sha256"]:
            r["exif_upright_pixel_exact"] = n.sha256 == m["expected_upright_normalized_sha256"]
        r["PASS"] = (r["file_sha256_khop"] and r["metadata_removed"]
                     and r.get("exif_upright_pixel_exact", True)
                     and (not "gps" in m["degradations"] or n.source_had_gps))
        ket.append(r)
    tong = {
        "CORPUS_KIND": corpus["CORPUS_KIND"],
        "REAL_PHOTO_CORPUS": corpus["REAL_PHOTO_CORPUS"],
        "APPLICATION_LLM_CALLS": 0,
        "REAL_PROVIDER_CALLS": 0,
        "items": ket,
        "EXIF_ORIENTATION": "PASS" if all(r.get("exif_upright_pixel_exact", True) for r in ket) else "FAIL",
        "EXIF_GPS_REMOVED": "PASS" if all(r["metadata_removed"] for r in ket) and any(r["source_had_gps"] for r in ket) else "FAIL",
        "PASS": all(r["PASS"] for r in ket),
    }
    (RA / "OFFLINE_NORMALIZATION.json").write_text(json.dumps(tong, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in ket:
        print(f"  {r['id']:34s} {'ĐẠT' if r['PASS'] else 'KHÔNG ĐẠT'}  {r['normalized_size']}  "
              f"exif={r['exif_orientation']} gps_nguon={r['source_had_gps']} gỡ_metadata={r['metadata_removed']}")
    print(f"→ {RA / 'OFFLINE_NORMALIZATION.json'}  EXIF_ORIENTATION={tong['EXIF_ORIENTATION']}  "
          f"EXIF_GPS_REMOVED={tong['EXIF_GPS_REMOVED']}  {'ĐẠT' if tong['PASS'] else 'KHÔNG ĐẠT'}")
    return 0 if tong["PASS"] else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kiem", action="store_true", help="chỉ đối chiếu bộ ảnh đã commit")
    ns = ap.parse_args()
    return kiem() if ns.kiem else dung()


if __name__ == "__main__":
    sys.exit(main())
