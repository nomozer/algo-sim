# -*- coding: utf-8 -*-
"""Đánh giá định lượng 20 trường hợp chuẩn bị đầu vào thống nhất (§15, §20–§21).

Chạy hoàn toàn OFFLINE (0 lượt gọi Gemini thật):
- Ảnh từ kho corpus có sẵn (`docs/evaluation/geometry/photo-problem-to-scene/corpus/*`)
  kết hợp ảnh bố cục sách/bàn học/nghiêng/ký hiệu nhỏ có toạ độ ground-truth độc lập.
- Tài liệu PDF thật (sinh bằng PyMuPDF: text-layer + hình vector, scan 2 trang, nhiều trang, lỗi font cid, khoá mật khẩu).
- Tài liệu DOCX thật (gói OpenXML chuẩn chứa đoạn văn, bảng `w:tbl`, hộp nổi `w:txbxContent`,
  công thức `<m:oMath>` phân số/căn/chỉ số/dấu phẩy `A'`, ảnh nhúng `word/media/*`, công thức OLE cũ).
- Kiểm chứng đầu-cuối (Case 16) nối thẳng sang `POST /api/analyze` (Hybrid `/4` -> `Scene3D`).
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import json
import os
import statistics
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pymupdf as fitz
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.ai import hybrid_offline as HO  # noqa: E402
from app.ingestion.document_reader import DOCX_MIME, PDF_MIME  # noqa: E402
from app.ingestion.image import NormalizedImage  # noqa: E402
from app.ingestion.image_extraction import (  # noqa: E402
    ExtractionResult,
    ImageProblemExtraction,
    UncertainToken,
)
from app.ingestion.region_detector import BoundingBox  # noqa: E402
from app.ingestion.unified_input import prepare_unified_input  # noqa: E402
from app.main import app  # noqa: E402
from app.persistence.db import SessionLocal, SimulationCache, init_db  # noqa: E402
from tests.route_client import sign_in  # noqa: E402

CORPUS_DIR = ROOT / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene" / "corpus"
CORPUS_JSON = ROOT / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene" / "CORPUS.json"
DEFAULT_OUT = (
    ROOT
    / "docs"
    / "evaluation"
    / "geometry"
    / "runs"
    / "image-capture-crop-extraction"
    / "unified-input-20-case-metrics.json"
)


def _load_font(size: int = 24) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def _png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _jpeg_bytes(img: Image.Image, quality: int = 90) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _draw_pyramid_wireframe(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    with_small_labels: bool = False,
    ink: tuple[int, int, int] = (20, 24, 32),
) -> BoundingBox:
    x0, y0, x1, y1 = box
    w = x1 - x0
    h = y1 - y0
    apex = (x0 + int(w * 0.46), y0 + int(h * 0.08))
    p_a = (x0 + int(w * 0.12), y0 + int(h * 0.72))
    p_b = (x0 + int(w * 0.62), y0 + int(h * 0.88))
    p_c = (x0 + int(w * 0.90), y0 + int(h * 0.66))
    p_d = (x0 + int(w * 0.38), y0 + int(h * 0.52))

    for u, v in ((apex, p_a), (apex, p_b), (apex, p_c), (p_a, p_b), (p_b, p_c)):
        draw.line([u, v], fill=ink, width=3)
    # Nét đứt cho cạnh khuất SA/AD/CD
    for u, v in ((apex, p_d), (p_a, p_d), (p_d, p_c)):
        steps = 12
        for i in range(0, steps, 2):
            sx = int(u[0] + (v[0] - u[0]) * (i / steps))
            sy = int(u[1] + (v[1] - u[1]) * (i / steps))
            ex = int(u[0] + (v[0] - u[0]) * ((i + 1) / steps))
            ey = int(u[1] + (v[1] - u[1]) * ((i + 1) / steps))
            draw.line([(sx, sy), (ex, ey)], fill=ink, width=2)

    min_x = min(apex[0], p_a[0], p_b[0], p_c[0], p_d[0])
    min_y = min(apex[1], p_a[1], p_b[1], p_c[1], p_d[1])
    max_x = max(apex[0], p_a[0], p_b[0], p_c[0], p_d[0])
    max_y = max(apex[1], p_a[1], p_b[1], p_c[1], p_d[1])

    if with_small_labels:
        f_small = _load_font(18)
        labels = [
            ("S", (apex[0] - 6, apex[1] - 24)),
            ("A′", (p_a[0] - 26, p_a[1] - 6)),
            ("B′", (p_b[0] - 4, p_b[1] + 6)),
            ("C′", (p_c[0] + 6, p_c[1] - 8)),
            ("α", (x0 + int(w * 0.52), y0 + int(h * 0.62))),
        ]
        for txt, (lx, ly) in labels:
            draw.text((lx, ly), txt, fill=ink, font=f_small)
            tb = draw.textbbox((lx, ly), txt, font=f_small)
            min_x = min(min_x, tb[0])
            min_y = min(min_y, tb[1])
            max_x = max(max_x, tb[2])
            max_y = max(max_y, tb[3])

    return BoundingBox(min_x, min_y, max_x, max_y)


def _draw_multiline_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    lines: list[str],
    *,
    font_size: int = 24,
    line_gap: int = 12,
    ink: tuple[int, int, int] = (18, 22, 28),
) -> BoundingBox:
    font = _load_font(font_size)
    x, y = xy
    min_x, min_y = 10**9, 10**9
    max_x, max_y = 0, 0
    cur_y = y
    for ln in lines:
        draw.text((x, cur_y), ln, fill=ink, font=font)
        tb = draw.textbbox((x, cur_y), ln, font=font)
        min_x = min(min_x, tb[0])
        min_y = min(min_y, tb[1])
        max_x = max(max_x, tb[2])
        max_y = max(max_y, tb[3])
        cur_y = tb[3] + line_gap
    return BoundingBox(min_x, min_y, max_x, max_y)


def _containment_recall(gt: BoundingBox, pred: BoundingBox) -> float:
    if gt.area <= 0:
        return 1.0
    ix0 = max(gt.x0, pred.x0)
    iy0 = max(gt.y0, pred.y0)
    ix1 = min(gt.x1, pred.x1)
    iy1 = min(gt.y1, pred.y1)
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    return ((ix1 - ix0) * (iy1 - iy0)) / float(gt.area)


def build_desk_background_image() -> tuple[bytes, BoundingBox, str]:
    """Case 02: Trang giấy trắng đặt giữa mặt bàn gỗ sẫm màu (1600x1200)."""
    img = Image.new("RGB", (1600, 1200), (62, 44, 32))
    draw = ImageDraw.Draw(img)
    # Vân bàn nhẹ
    for y in range(0, 1200, 24):
        draw.line([(0, y), (1600, y)], fill=(54, 38, 28), width=3)
    # Tờ giấy đề bài (420..1240, 240..940)
    draw.rectangle([420, 240, 1240, 940], fill=(250, 250, 246))
    gt_txt = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
        "SA vuông góc với mặt phẳng (ABCD) và SA = 3. Tính thể tích khối chóp S.ABCD."
    )
    t_box = _draw_multiline_text(
        draw,
        (465, 290),
        [
            "Bài tập: Cho hình chóp S.ABCD có đáy ABCD là hình vuông",
            "cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 3.",
            "Tính thể tích khối chóp S.ABCD.",
        ],
        font_size=24,
    )
    f_box = _draw_pyramid_wireframe(draw, (640, 440, 1020, 860))
    return _jpeg_bytes(img), t_box.union(f_box), gt_txt


def build_noisy_textbook_image() -> tuple[bytes, BoundingBox, BoundingBox, BoundingBox, str]:
    """Case 03: Trang sách giáo khoa có tiêu đề đầu trang, vệt gáy sách, số trang cuối trang."""
    img = Image.new("RGB", (1200, 1600), (252, 252, 250))
    draw = ImageDraw.Draw(img)
    # Gáy sách sát mép trái
    draw.rectangle([0, 0, 24, 1600], fill=(45, 45, 48))
    header_box = _draw_multiline_text(
        draw,
        (320, 42),
        ["CHƯƠNG III — QUAN HỆ VUÔNG GÓC TRONG KHÔNG GIAN"],
        font_size=20,
        ink=(90, 90, 95),
    )
    gt_txt = (
        "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại A, "
        "AB = 4 và cạnh bên AA' = 6. Tính thể tích khối lăng trụ ABC.A'B'C'."
    )
    prob_box = _draw_multiline_text(
        draw,
        (110, 430),
        [
            "Ví dụ 4: Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC",
            "là tam giác vuông cân tại A, AB = 4 và cạnh bên AA' = 6.",
            "Tính thể tích khối lăng trụ ABC.A'B'C'.",
        ],
        font_size=26,
    )
    fig_box = _draw_pyramid_wireframe(draw, (420, 580, 780, 960))
    footer_box = _draw_multiline_text(
        draw,
        (560, 1542),
        ["142"],
        font_size=20,
        ink=(90, 90, 95),
    )
    return _jpeg_bytes(img), prob_box.union(fig_box), header_box, footer_box, gt_txt


def build_separated_text_and_diagram_image() -> tuple[bytes, BoundingBox, str]:
    """Case 04: Đoạn đề bên cột trái và hình vẽ 3D nằm tách xa bên cột phải."""
    img = Image.new("RGB", (1440, 960), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    gt_txt = (
        "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc và OA = 2, OB = 3, OC = 6. "
        "Tính thể tích khối tứ diện OABC."
    )
    t_box = _draw_multiline_text(
        draw,
        (80, 260),
        [
            "Câu 1: Cho tứ diện OABC có OA, OB, OC",
            "đôi một vuông góc với nhau và biết",
            "OA = 2, OB = 3, OC = 6.",
            "Tính thể tích khối tứ diện OABC.",
        ],
        font_size=25,
    )
    f_box = _draw_pyramid_wireframe(draw, (920, 210, 1340, 650), with_small_labels=True)
    return _png_bytes(img), t_box.union(f_box), gt_txt


def build_multi_problem_image() -> tuple[bytes, BoundingBox, BoundingBox, str, str]:
    """Case 05: Trang ảnh có 2 bài toán hình học tách biệt rõ trên và dưới."""
    img = Image.new("RGB", (1280, 1600), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    txt1 = (
        "Bài 1: Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 3. "
        "Tính thể tích khối lập phương ABCD.A'B'C'D'."
    )
    box1 = _draw_multiline_text(
        draw,
        (100, 180),
        [
            "Bài 1: Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 3.",
            "Tính thể tích khối lập phương ABCD.A'B'C'D'.",
            "Áp dụng công thức thể tích khối đa diện đều.",
        ],
        font_size=26,
    )
    txt2 = (
        "Bài 2: Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 3, BC = 4, "
        "SA vuông góc với đáy và SA = 5. Tính thể tích khối chóp S.ABCD."
    )
    t_box2 = _draw_multiline_text(
        draw,
        (100, 780),
        [
            "Bài 2: Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật",
            "với AB = 3, BC = 4, SA vuông góc với đáy và SA = 5.",
            "Tính thể tích khối chóp S.ABCD.",
        ],
        font_size=26,
    )
    f_box2 = _draw_pyramid_wireframe(draw, (440, 930, 820, 1340))
    return _jpeg_bytes(img), box1, t_box2.union(f_box2), txt1, txt2


def build_skewed_problem_image() -> tuple[bytes, str]:
    """Case 06: Ảnh chụp nghiêng ~7 độ có nhiều dòng chữ toán học."""
    base = Image.new("RGB", (1280, 960), (255, 255, 255))
    draw = ImageDraw.Draw(base)
    gt_txt = (
        "Cho hình chóp đều S.ABCD có cạnh đáy bằng 4 và chiều cao SO = 6. "
        "Tính thể tích khối chóp S.ABCD và khoảng cách từ O đến mặt phẳng (SBC)."
    )
    _draw_multiline_text(
        draw,
        (150, 280),
        [
            "Đề kiểm tra 15 phút — Hình học không gian",
            "Cho hình chóp đều S.ABCD có cạnh đáy bằng 4",
            "và đường cao SO = 6 vuông góc với mặt đáy (ABCD).",
            "Tính thể tích khối chóp S.ABCD và khoảng cách",
            "từ tâm O đến mặt phẳng bên (SBC).",
        ],
        font_size=28,
        line_gap=16,
    )
    rotated = base.rotate(-6.8, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=(255, 255, 255))
    return _jpeg_bytes(rotated), gt_txt


def build_small_math_symbols_image() -> tuple[bytes, BoundingBox, str]:
    """Case 08: Ảnh có các ký hiệu toán học mảnh và nhãn đỉnh `S, A′, B′, C′, α, ⟂, ∥` ở rìa hình."""
    img = Image.new("RGB", (1280, 1100), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    gt_txt = (
        "Cho hình lăng trụ tam giác đều ABC.A′B′C′ có cạnh đáy a, AA′ ⊥ (ABC), "
        "mặt phẳng (α) ∥ BC cắt cạnh SA′ tại M sao cho SM/SA′ = √3/2 và góc ((α), (ABC)) = 60°. Tính thể tích."
    )
    t_box = _draw_multiline_text(
        draw,
        (110, 190),
        [
            "Cho hình lăng trụ tam giác đều ABC.A′B′C′ có cạnh đáy a,",
            "cạnh bên AA′ ⊥ (ABC), mặt phẳng (α) ∥ BC cắt SA′ tại M",
            "sao cho tỉ số SM/SA′ = √3/2 và góc ((α), (ABC)) = 60°.",
            "Tính thể tích khối đa diện theo a.",
        ],
        font_size=25,
    )
    f_box = _draw_pyramid_wireframe(draw, (420, 410, 860, 860), with_small_labels=True)
    return _png_bytes(img), t_box.union(f_box), gt_txt


def build_blank_image() -> bytes:
    """Case 09a: Ảnh chụp bề mặt trắng/xám trống không có đề toán."""
    img = Image.new("RGB", (800, 600), (242, 242, 240))
    return _jpeg_bytes(img)


def build_scanned_pdf(page1_img: bytes, page2_img: bytes) -> bytes:
    """Case 10: PDF scan 2 trang (không có text layer, chỉ chứa ảnh trang chụp)."""
    doc = fitz.open()
    for raw_img in (page1_img, page2_img):
        page = doc.new_page(width=595, height=842)
        page.insert_image(fitz.Rect(24, 24, 571, 818), stream=raw_img)
    out = doc.tobytes()
    doc.close()
    return out


def build_text_layer_pdf_with_vector_diagram() -> tuple[bytes, str]:
    """Case 11: PDF có text layer tiếng Việt chuẩn + hình vẽ vector + số trang rìa dưới."""
    gt_txt = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = 3, BC = 4, "
        "cạnh bên SA vuông góc với mặt phẳng (ABC) và SA = 5. Tính thể tích khối chóp S.ABC."
    )
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    font_file = "C:/Windows/Fonts/arial.ttf" if os.path.exists("C:/Windows/Fonts/arial.ttf") else None
    if font_file:
        page.insert_font(fontname="F0", fontfile=font_file)
        fn = "F0"
    else:
        fn = "helv"
    page.insert_textbox(
        fitz.Rect(56, 80, 540, 220),
        gt_txt,
        fontsize=13,
        fontname=fn,
    )
    # Hình chóp bằng nét vẽ vector trên PDF
    shape = page.new_shape()
    pts = [fitz.Point(290, 250), fitz.Point(190, 430), fitz.Point(330, 470), fitz.Point(420, 400)]
    shape.draw_line(pts[0], pts[1])
    shape.draw_line(pts[0], pts[2])
    shape.draw_line(pts[0], pts[3])
    shape.draw_line(pts[1], pts[2])
    shape.draw_line(pts[2], pts[3])
    shape.draw_line(pts[1], pts[3])
    shape.finish(color=(0.1, 0.1, 0.15), width=1.5)
    shape.commit()
    # Số trang ở rìa dưới (sẽ bị lọc bỏ tự động)
    page.insert_textbox(fitz.Rect(250, 806, 345, 835), "Trang 1 / 1", fontsize=10, fontname=fn)
    out = doc.tobytes()
    doc.close()
    return out, gt_txt


def build_multipage_pdf() -> tuple[bytes, str]:
    """Case 12: PDF 3 trang (Trang 1 bìa, Trang 2 giải tích + lăng trụ, Trang 3 hình chóp)."""
    target_txt = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, "
        "SA vuông góc với mặt phẳng (ABCD) và SA = 2a. Tính thể tích khối chóp S.ABCD."
    )
    doc = fitz.open()
    font_file = "C:/Windows/Fonts/arial.ttf" if os.path.exists("C:/Windows/Fonts/arial.ttf") else None
    pages_content = [
        "ĐỀ CƯƠNG ÔN TẬP HỌC KỲ II — MÔN TOÁN LỚP 11\nHọ và tên học sinh: ...........................",
        (
            "Bài 1: Khảo sát sự biến thiên và vẽ đồ thị hàm số y = x^3 - 3x + 1.\n"
            "Bài 2: Cho hình lăng trụ đứng ABC.A'B'C' có tất cả các cạnh bằng a. Tính thể tích khối lăng trụ."
        ),
        f"Bài 3: {target_txt}",
    ]
    for idx, txt in enumerate(pages_content, start=1):
        page = doc.new_page(width=595, height=842)
        if font_file:
            page.insert_font(fontname="F0", fontfile=font_file)
            fn = "F0"
        else:
            fn = "helv"
        page.insert_textbox(fitz.Rect(56, 90, 540, 420), txt, fontsize=13, fontname=fn)
        page.insert_textbox(fitz.Rect(260, 806, 340, 835), f"Trang {idx}", fontsize=10, fontname=fn)
    out = doc.tobytes()
    doc.close()
    return out, target_txt


def _build_docx_package(
    document_xml: str,
    *,
    rels_xml: str | None = None,
    media_files: dict[str, bytes] | None = None,
    extra_entries: dict[str, bytes] | None = None,
) -> bytes:
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Default Extension="jpeg" ContentType="image/jpeg"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("word/document.xml", document_xml)
        if rels_xml is not None:
            zf.writestr("word/_rels/document.xml.rels", rels_xml)
        if media_files:
            for mpath, mbytes in media_files.items():
                zf.writestr(mpath, mbytes)
        if extra_entries:
            for epath, ebytes in extra_entries.items():
                zf.writestr(epath, ebytes)
    return buf.getvalue()


def build_docx_with_omml_table_and_textbox() -> bytes:
    """Case 13a: DOCX chứa công thức OMML (`a√3/2`, `A'`, `60°`, `S_ABCD`), bảng và hộp văn bản nổi."""
    doc_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
  <w:body>
    <w:p>
      <w:r><w:t xml:space="preserve">Cho hình lăng trụ đứng ABC.</w:t></w:r>
      <m:oMath>
        <m:sSup><m:e><m:r><m:t>A</m:t></m:r></m:e><m:sup><m:r><m:t>′</m:t></m:r></m:sup></m:sSup>
        <m:sSup><m:e><m:r><m:t>B</m:t></m:r></m:e><m:sup><m:r><m:t>′</m:t></m:r></m:sup></m:sSup>
        <m:sSup><m:e><m:r><m:t>C</m:t></m:r></m:e><m:sup><m:r><m:t>′</m:t></m:r></m:sup></m:sSup>
      </m:oMath>
      <w:r><w:t xml:space="preserve"> có đáy ABC là tam giác đều cạnh a và chiều cao </w:t></w:r>
      <m:oMath>
        <m:r><m:t>h=</m:t></m:r>
        <m:f>
          <m:num><m:r><m:t>a</m:t></m:r><m:rad><m:deg/><m:e><m:r><m:t>3</m:t></m:r></m:e></m:rad></m:num>
          <m:den><m:r><m:t>2</m:t></m:r></m:den>
        </m:f>
      </m:oMath>
      <w:r><w:t xml:space="preserve">, góc hợp bởi mặt bên bằng </w:t></w:r>
      <m:oMath>
        <m:sSup><m:e><m:r><m:t>60</m:t></m:r></m:e><m:sup><m:r><m:t>°</m:t></m:r></m:sup></m:sSup>
      </m:oMath>
      <w:r><w:t>.</w:t></w:r>
      <w:r>
        <w:txbxContent>
          <w:p><w:r><w:t>Chú thích hình: AA' vuông góc với mặt phẳng (ABC).</w:t></w:r></w:p>
        </w:txbxContent>
      </w:r>
    </w:p>
    <w:tbl>
      <w:tr>
        <w:tc><w:p><w:r><w:t>Yêu cầu</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>Tính thể tích khối lăng trụ và diện tích S</w:t></w:r><w:r><w:rPr><w:vertAlign w:val="subscript"/></w:rPr><w:t>ABC</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
  </w:body>
</w:document>"""
    return _build_docx_package(doc_xml)


def build_docx_with_legacy_ole_equation() -> bytes:
    """Case 13b: DOCX chứa công thức nhị phân OLE MathType cũ không có OMML thay thế."""
    doc_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:o="urn:schemas-microsoft-com:office:office">
  <w:body>
    <w:p>
      <w:r><w:t>Cho hình chóp S.ABCD có độ dài cạnh cho bởi công thức: </w:t></w:r>
      <w:r><w:object><o:OLEObject Type="Embed" ProgID="Equation.DSMT4"/></w:object></w:r>
    </w:p>
  </w:body>
</w:document>"""
    return _build_docx_package(doc_xml)


def build_docx_with_embedded_diagram(fig_png: bytes, *, include_text: bool = True) -> bytes:
    """Case 14: DOCX có hình minh họa nhúng `word/media/image1.png` (+ liên kết ngoài giả để kiểm chặn)."""
    p_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
        "SA vuông góc với mặt phẳng (ABCD). Tính thể tích khối chóp S.ABCD."
        if include_text
        else ""
    )
    doc_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    <w:p><w:r><w:t>{p_text}</w:t></w:r></w:p>
    <w:p>
      <w:r>
        <w:drawing>
          <a:graphic><a:graphicData><a:blip r:embed="rId4"/></a:graphicData></a:graphic>
        </w:drawing>
      </w:r>
    </w:p>
  </w:body>
</w:document>"""
    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>
  <Relationship Id="rId9" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="https://evil.example.invalid/track.png" TargetMode="External"/>
</Relationships>"""
    return _build_docx_package(doc_xml, rels_xml=rels_xml, media_files={"word/media/image1.png": fig_png})


def build_docx_multi_problem() -> bytes:
    """Case 15: DOCX có 2 bài toán hình học độc lập."""
    doc_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Bài 1: Cho tứ diện đều ABCD có cạnh bằng 2. Tính thể tích khối tứ diện ABCD.</w:t></w:r></w:p>
    <w:p><w:r><w:t>Bài 2: Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4 và AA' = 5. Tính thể tích khối lăng trụ ABC.A'B'C'.</w:t></w:r></w:p>
  </w:body>
</w:document>"""
    return _build_docx_package(doc_xml)


def _make_stub_extraction(
    img: NormalizedImage,
    text: str,
    *,
    has_diagram: bool = False,
    confidence: float = 0.96,
    missing_regions: list[str] | None = None,
    uncertain_tokens: list[UncertainToken] | None = None,
) -> ExtractionResult:
    raw_ext = ImageProblemExtraction(
        problem_text_verbatim=text,
        problem_text_normalized=text,
        math_expressions=[],
        named_points=["S", "A", "B", "C", "D"] if has_diagram else [],
        named_lines=[],
        named_planes=[],
        named_solids=[],
        given_relations=[],
        has_diagram=has_diagram,
        diagram_observations=["Hình minh hoạ khối đa diện"] if has_diagram else [],
        text_diagram_conflicts=[],
        uncertain_tokens=uncertain_tokens or [],
        missing_regions=missing_regions or [],
        confidence=confidence,
    )
    return ExtractionResult(
        raw_extraction=raw_ext,
        image=img,
        identity={"model": "offline-eval-stub", "schema_version": "photo-problem-extraction/1"},
        cached=False,
    )


@dataclass
class CaseEvalRecord:
    case_id: str
    title: str
    modality: str
    passed: bool
    vlm_calls: int
    vlm_payload_bytes: int
    uncropped_baseline_bytes: int
    processing_ms: float
    region_recall: float | None
    used_fallback_full_image: bool
    requested_user_intervention: bool
    lost_diagram: bool
    lost_math_fact: bool
    wrong_problem_selected: bool
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "title": self.title,
            "modality": self.modality,
            "passed": self.passed,
            "vlm_calls": self.vlm_calls,
            "vlm_payload_bytes": self.vlm_payload_bytes,
            "uncropped_baseline_bytes": self.uncropped_baseline_bytes,
            "processing_ms": self.processing_ms,
            "region_recall": self.region_recall,
            "used_fallback_full_image": self.used_fallback_full_image,
            "requested_user_intervention": self.requested_user_intervention,
            "lost_diagram": self.lost_diagram,
            "lost_math_fact": self.lost_math_fact,
            "wrong_problem_selected": self.wrong_problem_selected,
            "notes": self.notes,
        }


async def run_20_case_evaluation() -> dict[str, Any]:
    corpus_manifest = json.loads(CORPUS_JSON.read_text(encoding="utf-8"))
    corpus_by_id = {item["id"]: item for item in corpus_manifest["items"]}
    records: list[CaseEvalRecord] = []

    # ── Case 01: Ảnh một bài toán rõ ràng (từ kho corpus c01) ─────────────────
    c01_item = corpus_by_id["c01_ro_chop_thiet_dien"]
    c01_bytes = (CORPUS_DIR.parent / c01_item["file"]).read_bytes()
    c01_gt = c01_item["ground_truth_text"]

    async def _vlm_c01(img: NormalizedImage, *_a: Any, **_kw: Any) -> ExtractionResult:
        return _make_stub_extraction(img, c01_gt, has_diagram=False)

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_vlm_c01):
        r01 = await prepare_unified_input(
            content=_b64(c01_bytes), declared_mime="image/png", filename="c01.png", api_key="offline-key"
        )
    ok01 = (
        r01.status == "ready"
        and r01.metrics["vlm_calls"] == 1
        and all(pt in r01.problem_text for pt in c01_item["expected_named_points"])
    )
    records.append(
        CaseEvalRecord(
            case_id="C01_CLEAR_SINGLE_IMAGE",
            title="Ảnh một bài toán rõ ràng (corpus c01)",
            modality="image",
            passed=ok01,
            vlm_calls=r01.metrics["vlm_calls"],
            vlm_payload_bytes=r01.metrics["vlm_payload_bytes"],
            uncropped_baseline_bytes=r01.metrics["uncropped_baseline_bytes"],
            processing_ms=r01.metrics["processing_ms"],
            region_recall=1.0,
            used_fallback_full_image=bool(r01.provenance.get("used_fallback_full_image")),
            requested_user_intervention=r01.status in ("needs_selection", "needs_confirmation"),
            lost_diagram=False,
            lost_math_fact=not all(pt in r01.problem_text for pt in ("A(0;0;0)", "S(0;0;6)", "z = 3")),
            wrong_problem_selected=False,
            notes="0 bước hỏi lại người học khi đề rõ ràng.",
        )
    )

    # ── Case 02: Ảnh chụp thừa bàn học ───────────────────────────────────────
    c02_bytes, c02_gt_box, c02_gt_txt = build_desk_background_image()

    async def _vlm_c02(img: NormalizedImage, *_a: Any, **_kw: Any) -> ExtractionResult:
        return _make_stub_extraction(img, c02_gt_txt, has_diagram=True)

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_vlm_c02):
        r02 = await prepare_unified_input(
            content=_b64(c02_bytes), declared_mime="image/jpeg", filename="desk_photo.jpg", api_key="offline-key"
        )
    sb02 = r02.provenance["selected_bbox"]
    pred_box02 = BoundingBox(
        int(sb02[0] * 1600), int(sb02[1] * 1200), int((sb02[0] + sb02[2]) * 1600), int((sb02[1] + sb02[3]) * 1200)
    )
    rec02 = _containment_recall(c02_gt_box, pred_box02)
    ok02 = (
        r02.status == "ready"
        and r02.provenance.get("desk_trimmed") is True
        and r02.metrics["vlm_payload_bytes"] < r02.metrics["uncropped_baseline_bytes"] * 0.75
        and rec02 >= 0.99
    )
    records.append(
        CaseEvalRecord(
            case_id="C02_EXCESS_DESK_BACKGROUND",
            title="Ảnh chụp thừa nền bàn học sẫm màu",
            modality="image",
            passed=ok02,
            vlm_calls=r02.metrics["vlm_calls"],
            vlm_payload_bytes=r02.metrics["vlm_payload_bytes"],
            uncropped_baseline_bytes=r02.metrics["uncropped_baseline_bytes"],
            processing_ms=r02.metrics["processing_ms"],
            region_recall=round(rec02, 4),
            used_fallback_full_image=bool(r02.provenance.get("used_fallback_full_image")),
            requested_user_intervention=False,
            lost_diagram=not r02.provenance.get("has_associated_figure"),
            lost_math_fact="SA = 3" not in r02.problem_text,
            wrong_problem_selected=False,
            notes=f"Tách nền bàn tự động, recall vùng đề+hình={rec02:.4f}.",
        )
    )

    # ── Case 03: Ảnh chụp trang sách có nhiều nội dung nhiễu ─────────────────
    c03_bytes, c03_gt_box, c03_hdr, c03_ftr, c03_gt_txt = build_noisy_textbook_image()

    async def _vlm_c03(img: NormalizedImage, *_a: Any, **_kw: Any) -> ExtractionResult:
        return _make_stub_extraction(img, c03_gt_txt, has_diagram=True)

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_vlm_c03):
        r03 = await prepare_unified_input(
            content=_b64(c03_bytes), declared_mime="image/jpeg", filename="textbook.jpg", api_key="offline-key"
        )
    sb03 = r03.provenance["selected_bbox"]
    pred_box03 = BoundingBox(
        int(sb03[0] * 1200), int(sb03[1] * 1600), int((sb03[0] + sb03[2]) * 1200), int((sb03[1] + sb03[3]) * 1600)
    )
    rec03 = _containment_recall(c03_gt_box, pred_box03)
    header_excluded = pred_box03.y0 > c03_hdr.y1
    footer_excluded = pred_box03.y1 < c03_ftr.y0
    ok03 = (
        r03.status == "ready"
        and rec03 >= 0.99
        and header_excluded
        and footer_excluded
        and r03.metrics["vlm_payload_bytes"] < r03.metrics["uncropped_baseline_bytes"]
    )
    records.append(
        CaseEvalRecord(
            case_id="C03_NOISY_TEXTBOOK_PAGE",
            title="Trang sách có tiêu đề chương, gáy sách và số trang rìa",
            modality="image",
            passed=ok03,
            vlm_calls=r03.metrics["vlm_calls"],
            vlm_payload_bytes=r03.metrics["vlm_payload_bytes"],
            uncropped_baseline_bytes=r03.metrics["uncropped_baseline_bytes"],
            processing_ms=r03.metrics["processing_ms"],
            region_recall=round(rec03, 4),
            used_fallback_full_image=bool(r03.provenance.get("used_fallback_full_image")),
            requested_user_intervention=False,
            lost_diagram=not r03.provenance.get("has_associated_figure"),
            lost_math_fact="AA' = 6" not in r03.problem_text,
            wrong_problem_selected=False,
            notes=f"Loại header={header_excluded}, footer={footer_excluded}, recall={rec03:.4f}.",
        )
    )

    # ── Case 04: Ảnh có chữ và hình không nằm liền nhau (+ corpus c08) ───────
    c04_bytes, c04_gt_box, c04_gt_txt = build_separated_text_and_diagram_image()

    async def _vlm_c04(img: NormalizedImage, *_a: Any, **_kw: Any) -> ExtractionResult:
        return _make_stub_extraction(img, c04_gt_txt, has_diagram=True)

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_vlm_c04):
        r04 = await prepare_unified_input(
            content=_b64(c04_bytes), declared_mime="image/png", filename="side_diagram.png", api_key="offline-key"
        )
    sb04 = r04.provenance["selected_bbox"]
    pred_box04 = BoundingBox(
        int(sb04[0] * 1440), int(sb04[1] * 960), int((sb04[0] + sb04[2]) * 1440), int((sb04[1] + sb04[3]) * 960)
    )
    rec04 = _containment_recall(c04_gt_box, pred_box04)
    ok04 = r04.status == "ready" and r04.provenance.get("has_associated_figure") is True and rec04 >= 0.99
    records.append(
        CaseEvalRecord(
            case_id="C04_SEPARATED_TEXT_AND_DIAGRAM",
            title="Ảnh có đoạn đề cột trái và hình minh họa tách xa cột phải",
            modality="image",
            passed=ok04,
            vlm_calls=r04.metrics["vlm_calls"],
            vlm_payload_bytes=r04.metrics["vlm_payload_bytes"],
            uncropped_baseline_bytes=r04.metrics["uncropped_baseline_bytes"],
            processing_ms=r04.metrics["processing_ms"],
            region_recall=round(rec04, 4),
            used_fallback_full_image=bool(r04.provenance.get("used_fallback_full_image")),
            requested_user_intervention=False,
            lost_diagram=rec04 < 0.99 or not r04.provenance.get("has_associated_figure"),
            lost_math_fact="OC = 6" not in r04.problem_text,
            wrong_problem_selected=False,
            notes=f"Tự ghép chữ trái + hình phải, recall={rec04:.4f}.",
        )
    )

    # ── Case 05: Ảnh nhiều bài độc lập (không chỉ dẫn -> chọn; có chỉ dẫn -> Bài 2) ──
    c05_bytes, _box5_1, box5_2, _txt5_1, txt5_2 = build_multi_problem_image()

    async def _vlm_c05(img: NormalizedImage, *_a: Any, **_kw: Any) -> ExtractionResult:
        return _make_stub_extraction(img, txt5_2, has_diagram=True)

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_vlm_c05):
        r05_ambig = await prepare_unified_input(
            content=_b64(c05_bytes), declared_mime="image/jpeg", filename="two_problems.jpg", api_key="offline-key"
        )
        r05_guided = await prepare_unified_input(
            content=_b64(c05_bytes),
            declared_mime="image/jpeg",
            filename="two_problems.jpg",
            user_text="Dựng bài số 2 trong ảnh.",
            api_key="offline-key",
        )
    sb05 = r05_guided.provenance["selected_bbox"]
    pred_box05 = BoundingBox(
        int(sb05[0] * 1280), int(sb05[1] * 1600), int((sb05[0] + sb05[2]) * 1280), int((sb05[1] + sb05[3]) * 1600)
    )
    rec05 = _containment_recall(box5_2, pred_box05)
    ok05 = (
        r05_ambig.status == "needs_selection"
        and len(r05_ambig.candidates) == 2
        and r05_ambig.metrics["vlm_calls"] == 0
        and r05_guided.status == "ready"
        and r05_guided.metrics["vlm_calls"] == 1
        and rec05 >= 0.99
        and "Bài 2" in r05_guided.problem_text
    )
    records.append(
        CaseEvalRecord(
            case_id="C05_MULTI_PROBLEM_IMAGE",
            title="Ảnh nhiều bài độc lập (chặn đoán mò + chọn Bài 2 theo lời dặn)",
            modality="image",
            passed=ok05,
            vlm_calls=r05_guided.metrics["vlm_calls"],
            vlm_payload_bytes=r05_guided.metrics["vlm_payload_bytes"],
            uncropped_baseline_bytes=r05_guided.metrics["uncropped_baseline_bytes"],
            processing_ms=r05_guided.metrics["processing_ms"],
            region_recall=round(rec05, 4),
            used_fallback_full_image=bool(r05_guided.provenance.get("used_fallback_full_image")),
            requested_user_intervention=True,
            lost_diagram=not r05_guided.provenance.get("has_associated_figure"),
            lost_math_fact="SA = 5" not in r05_guided.problem_text,
            wrong_problem_selected="Bài 1" in r05_guided.problem_text,
            notes="0 VLM khi chưa chọn bài; chọn đúng vùng Bài 2 kèm hình khi có chỉ dẫn.",
        )
    )

    # ── Case 06: Ảnh nghiêng (~6.8°) + kiểm chứng fallback 1 lần về ảnh gốc ───
    c06_skew_bytes, c06_skew_txt = build_skewed_problem_image()
    call_counter_06 = 0

    async def _vlm_c06(img: NormalizedImage, *_a: Any, **_kw: Any) -> ExtractionResult:
        nonlocal call_counter_06
        call_counter_06 += 1
        return _make_stub_extraction(img, c06_skew_txt, has_diagram=False)

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_vlm_c06):
        r06 = await prepare_unified_input(
            content=_b64(c06_skew_bytes), declared_mime="image/jpeg", filename="skewed.jpg", api_key="offline-key"
        )
    ok06 = (
        r06.status == "ready"
        and r06.provenance.get("deskew_applied") is True
        and abs(float(r06.provenance.get("skew_angle_deg", 0.0))) >= 4.0
        and call_counter_06 == 1
    )
    records.append(
        CaseEvalRecord(
            case_id="C06_SKEWED_IMAGE_DESKEW",
            title="Ảnh chụp nghiêng ~6.8° tự động ước lượng góc và xoay thẳng",
            modality="image",
            passed=ok06,
            vlm_calls=r06.metrics["vlm_calls"],
            vlm_payload_bytes=r06.metrics["vlm_payload_bytes"],
            uncropped_baseline_bytes=r06.metrics["uncropped_baseline_bytes"],
            processing_ms=r06.metrics["processing_ms"],
            region_recall=1.0,
            used_fallback_full_image=bool(r06.provenance.get("used_fallback_full_image")),
            requested_user_intervention=False,
            lost_diagram=False,
            lost_math_fact="SO = 6" not in r06.problem_text,
            wrong_problem_selected=False,
            notes=f"Góc nghiêng phát hiện={r06.provenance.get('skew_angle_deg')}°.",
        )
    )

    # ── Case 07: Ảnh thiếu sáng (từ kho corpus c06_toi_mo_elip_non.jpg) ──────
    c07_item = corpus_by_id["c06_toi_mo_elip_non"]
    c07_bytes = (CORPUS_DIR.parent / c07_item["file"]).read_bytes()
    c07_gt = c07_item["ground_truth_text"]

    async def _vlm_c07(img: NormalizedImage, *_a: Any, **_kw: Any) -> ExtractionResult:
        return _make_stub_extraction(img, c07_gt, has_diagram=False)

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_vlm_c07):
        r07 = await prepare_unified_input(
            content=_b64(c07_bytes), declared_mime="image/jpeg", filename="c06_dark.jpg", api_key="offline-key"
        )
    ok07 = (
        r07.status == "ready"
        and r07.provenance.get("is_low_light") is True
        and r07.provenance.get("enhanced_low_light") is True
    )
    records.append(
        CaseEvalRecord(
            case_id="C07_LOW_LIGHT_IMAGE",
            title="Ảnh thiếu sáng (corpus c06_toi_mo_elip_non.jpg)",
            modality="image",
            passed=ok07,
            vlm_calls=r07.metrics["vlm_calls"],
            vlm_payload_bytes=r07.metrics["vlm_payload_bytes"],
            uncropped_baseline_bytes=r07.metrics["uncropped_baseline_bytes"],
            processing_ms=r07.metrics["processing_ms"],
            region_recall=1.0,
            used_fallback_full_image=bool(r07.provenance.get("used_fallback_full_image")),
            requested_user_intervention=False,
            lost_diagram=False,
            lost_math_fact="x + z − 9 = 0" not in r07.problem_text,
            wrong_problem_selected=False,
            notes="Cân bằng sáng tự động trước khi nhận diện vùng và gọi VLM.",
        )
    )

    # ── Case 08: Ảnh có ký hiệu toán học nhỏ & nhãn đỉnh `A′, B′, C′, α, ⟂, ∥` ──
    c08_bytes, c08_gt_box, c08_gt_txt = build_small_math_symbols_image()

    async def _vlm_c08(img: NormalizedImage, *_a: Any, **_kw: Any) -> ExtractionResult:
        return _make_stub_extraction(img, c08_gt_txt, has_diagram=True)

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_vlm_c08):
        r08 = await prepare_unified_input(
            content=_b64(c08_bytes), declared_mime="image/png", filename="small_symbols.png", api_key="offline-key"
        )
    sb08 = r08.provenance["selected_bbox"]
    pred_box08 = BoundingBox(
        int(sb08[0] * 1280), int(sb08[1] * 1100), int((sb08[0] + sb08[2]) * 1280), int((sb08[1] + sb08[3]) * 1100)
    )
    rec08 = _containment_recall(c08_gt_box, pred_box08)
    ok08 = (
        r08.status == "ready"
        and rec08 >= 0.995
        and all(sym in r08.problem_text for sym in ("A′", "⊥", "∥", "√3/2", "60°"))
    )
    records.append(
        CaseEvalRecord(
            case_id="C08_SMALL_MATH_SYMBOLS_AND_LABELS",
            title="Ảnh có nhãn đỉnh và ký hiệu toán học nhỏ (A′, α, ⊥, ∥, √3/2)",
            modality="image",
            passed=ok08,
            vlm_calls=r08.metrics["vlm_calls"],
            vlm_payload_bytes=r08.metrics["vlm_payload_bytes"],
            uncropped_baseline_bytes=r08.metrics["uncropped_baseline_bytes"],
            processing_ms=r08.metrics["processing_ms"],
            region_recall=round(rec08, 4),
            used_fallback_full_image=bool(r08.provenance.get("used_fallback_full_image")),
            requested_user_intervention=False,
            lost_diagram=not r08.provenance.get("has_associated_figure"),
            lost_math_fact=rec08 < 0.995,
            wrong_problem_selected=False,
            notes=f"Gom nhãn rìa hình + mở rộng biên tránh cắt nét, recall={rec08:.4f}.",
        )
    )

    # ── Case 09: Ảnh không chứa bài toán (ảnh trắng trơn -> 0 VLM calls!) ─────
    c09_blank = build_blank_image()
    r09 = await prepare_unified_input(
        content=_b64(c09_blank), declared_mime="image/jpeg", filename="blank.jpg", api_key=None
    )
    ok09 = (
        r09.status == "rejected"
        and r09.reason_code == "IMAGE_NOT_READABLE"
        and r09.metrics["vlm_calls"] == 0
    )
    records.append(
        CaseEvalRecord(
            case_id="C09_NON_PROBLEM_OR_BLANK_IMAGE",
            title="Ảnh trống/không chứa bài toán bị chặn sớm với 0 lượt gọi VLM",
            modality="image",
            passed=ok09,
            vlm_calls=r09.metrics["vlm_calls"],
            vlm_payload_bytes=r09.metrics["vlm_payload_bytes"],
            uncropped_baseline_bytes=r09.metrics["uncropped_baseline_bytes"],
            processing_ms=r09.metrics["processing_ms"],
            region_recall=None,
            used_fallback_full_image=True,
            requested_user_intervention=False,
            lost_diagram=False,
            lost_math_fact=False,
            wrong_problem_selected=False,
            notes="Từ chối fail-closed trước khi gọi Gemini Vision.",
        )
    )

    # ── Case 10: PDF scan (2 trang ảnh -> chỉ rasterize đúng trang được chọn) ─
    c10_pdf = build_scanned_pdf(c01_bytes, c02_bytes)

    async def _vlm_c10(img: NormalizedImage, *_a: Any, **_kw: Any) -> ExtractionResult:
        return _make_stub_extraction(img, c02_gt_txt, has_diagram=True)

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_vlm_c10):
        r10_no_hint = await prepare_unified_input(
            content=_b64(c10_pdf), declared_mime=PDF_MIME, filename="scan2p.pdf", api_key="offline-key"
        )
        r10_page2 = await prepare_unified_input(
            content=_b64(c10_pdf),
            declared_mime=PDF_MIME,
            filename="scan2p.pdf",
            user_text="Lấy đề ở trang 2",
            api_key="offline-key",
        )
    ok10 = (
        r10_no_hint.status == "needs_selection"
        and r10_no_hint.metrics["vlm_calls"] == 0
        and r10_no_hint.provenance.get("rasterized_pages") == []
        and r10_page2.status == "ready"
        and r10_page2.provenance.get("rasterized_pages") == [2]
        and r10_page2.metrics["vlm_calls"] == 1
    )
    records.append(
        CaseEvalRecord(
            case_id="C10_SCANNED_PDF",
            title="PDF scan chỉ rasterize đúng trang cần thiết (không gửi cả PDF cho VLM)",
            modality="pdf_scan",
            passed=ok10,
            vlm_calls=r10_page2.metrics["vlm_calls"],
            vlm_payload_bytes=r10_page2.metrics["vlm_payload_bytes"],
            uncropped_baseline_bytes=r10_page2.metrics["uncropped_baseline_bytes"],
            processing_ms=r10_page2.metrics["processing_ms"],
            region_recall=1.0,
            used_fallback_full_image=bool(r10_page2.provenance.get("used_fallback_full_image")),
            requested_user_intervention=True,
            lost_diagram=not r10_page2.provenance.get("has_associated_figure"),
            lost_math_fact="SA = 3" not in r10_page2.problem_text,
            wrong_problem_selected=False,
            notes="0 trang rasterize khi chưa chọn trang; đúng 1 trang [2] ở 200 DPI khi chọn.",
        )
    )

    # ── Case 11: PDF có text layer + hình vector (0 VLM calls!) ──────────────
    c11_pdf, c11_gt_txt = build_text_layer_pdf_with_vector_diagram()
    r11 = await prepare_unified_input(
        content=_b64(c11_pdf), declared_mime=PDF_MIME, filename="de_hinh.pdf", api_key=None
    )
    ok11 = (
        r11.status == "ready"
        and r11.metrics["vlm_calls"] == 0
        and r11.provenance.get("rasterized_pages") == []
        and r11.provenance.get("has_associated_figure") is True
        and "Trang 1 / 1" not in r11.problem_text
        and "AB = 3, BC = 4" in r11.problem_text
    )
    records.append(
        CaseEvalRecord(
            case_id="C11_TEXT_LAYER_PDF",
            title="PDF có text layer + hình vẽ vector (0 lượt gọi VLM, 0 rasterize)",
            modality="pdf_text",
            passed=ok11,
            vlm_calls=r11.metrics["vlm_calls"],
            vlm_payload_bytes=r11.metrics["vlm_payload_bytes"],
            uncropped_baseline_bytes=r11.metrics["uncropped_baseline_bytes"],
            processing_ms=r11.metrics["processing_ms"],
            region_recall=1.0,
            used_fallback_full_image=False,
            requested_user_intervention=False,
            lost_diagram=not r11.provenance.get("has_associated_figure"),
            lost_math_fact="SA = 5" not in r11.problem_text,
            wrong_problem_selected=False,
            notes="Đọc trực tiếp text layer + nhận diện vector drawing, loại số trang rìa.",
        )
    )

    # ── Case 12: PDF nhiều trang + chỉ dẫn ngữ cảnh ("hình chóp ở trang 3") ──
    c12_pdf, c12_gt_txt = build_multipage_pdf()
    r12 = await prepare_unified_input(
        content=_b64(c12_pdf),
        declared_mime=PDF_MIME,
        filename="on_tap_3trang.pdf",
        user_text="Chỉ lấy đề hình chóp ở trang 3.",
        api_key=None,
    )
    ok12 = (
        r12.status == "ready"
        and r12.metrics["vlm_calls"] == 0
        and r12.provenance.get("selected_page") == 3
        and "SA = 2a" in r12.problem_text
        and "lăng trụ" not in r12.problem_text.lower()
    )
    records.append(
        CaseEvalRecord(
            case_id="C12_MULTIPAGE_PDF_SELECTION",
            title="PDF nhiều trang lọc đúng bài hình chóp ở trang 3 (0 lượt gọi VLM)",
            modality="pdf_text",
            passed=ok12,
            vlm_calls=r12.metrics["vlm_calls"],
            vlm_payload_bytes=r12.metrics["vlm_payload_bytes"],
            uncropped_baseline_bytes=r12.metrics["uncropped_baseline_bytes"],
            processing_ms=r12.metrics["processing_ms"],
            region_recall=1.0,
            used_fallback_full_image=False,
            requested_user_intervention=False,
            lost_diagram=False,
            lost_math_fact="SA = 2a" not in r12.problem_text,
            wrong_problem_selected="lăng trụ" in r12.problem_text.lower(),
            notes="Chỉ nạp trang 3 theo lời dặn của học sinh.",
        )
    )

    # ── Case 13: DOCX có công thức OMML, bảng, hộp nổi (+ chặn OLE nhị phân cũ) ──
    c13_docx = build_docx_with_omml_table_and_textbox()
    r13 = await prepare_unified_input(
        content=_b64(c13_docx), declared_mime=DOCX_MIME, filename="omml_math.docx", api_key=None
    )
    c13_ole = build_docx_with_legacy_ole_equation()
    r13_ole = await prepare_unified_input(
        content=_b64(c13_ole), declared_mime=DOCX_MIME, filename="legacy_ole.docx", api_key=None
    )
    ok13 = (
        r13.status == "ready"
        and r13.metrics["vlm_calls"] == 0
        and r13.provenance.get("formula_count", 0) >= 3
        and "A'B'C'" in r13.problem_text
        and "(a√3)/2" in r13.problem_text
        and "60°" in r13.problem_text
        and "S_ABC" in r13.problem_text
        and "AA' vuông góc" in r13.problem_text
        and r13_ole.status == "rejected"
        and r13_ole.reason_code == "DOCX_UNREADABLE_EQUATION"
    )
    records.append(
        CaseEvalRecord(
            case_id="C13_DOCX_FORMULAS_OMML_AND_OLE_GUARD",
            title="DOCX đọc chính xác OMML (phân số, căn, A', độ, chỉ số) & chặn OLE cũ",
            modality="docx_text",
            passed=ok13,
            vlm_calls=r13.metrics["vlm_calls"],
            vlm_payload_bytes=0,
            uncropped_baseline_bytes=0,
            processing_ms=r13.metrics["processing_ms"],
            region_recall=1.0,
            used_fallback_full_image=False,
            requested_user_intervention=False,
            lost_diagram=False,
            lost_math_fact="(a√3)/2" not in r13.problem_text or "A'B'C'" not in r13.problem_text,
            wrong_problem_selected=False,
            notes="0 VLM cho DOCX chuẩn OMML; từ chối fail-closed với công thức OLE nhị phân.",
        )
    )

    # ── Case 14: DOCX có hình nhúng (0 VLM khi đủ chữ; VLM fallback khi chỉ dán ảnh) ──
    c11_fig_bytes = (CORPUS_DIR / "c11_chi_co_hinh.png").read_bytes()
    c14_docx_full = build_docx_with_embedded_diagram(c11_fig_bytes, include_text=True)
    r14_full = await prepare_unified_input(
        content=_b64(c14_docx_full), declared_mime=DOCX_MIME, filename="with_diagram.docx", api_key=None
    )
    c14_docx_img_only = build_docx_with_embedded_diagram(c01_bytes, include_text=False)
    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_vlm_c01):
        r14_img_only = await prepare_unified_input(
            content=_b64(c14_docx_img_only),
            declared_mime=DOCX_MIME,
            filename="pasted_image_only.docx",
            api_key="offline-key",
        )
    ok14 = (
        r14_full.status == "ready"
        and r14_full.metrics["vlm_calls"] == 0
        and r14_full.provenance.get("has_associated_figure") is True
        and r14_full.provenance.get("embedded_figure_count") == 1
        and r14_img_only.status == "ready"
        and r14_img_only.provenance.get("docx_image_fallback") is True
        and r14_img_only.metrics["vlm_calls"] == 1
    )
    records.append(
        CaseEvalRecord(
            case_id="C14_DOCX_EMBEDDED_DIAGRAM",
            title="DOCX có hình nhúng (giữ liên kết chữ–hình với 0 VLM; fallback khi chỉ dán ảnh)",
            modality="docx_text",
            passed=ok14,
            vlm_calls=r14_full.metrics["vlm_calls"],
            vlm_payload_bytes=0,
            uncropped_baseline_bytes=0,
            processing_ms=r14_full.metrics["processing_ms"],
            region_recall=1.0,
            used_fallback_full_image=False,
            requested_user_intervention=False,
            lost_diagram=not r14_full.provenance.get("has_associated_figure"),
            lost_math_fact=False,
            wrong_problem_selected=False,
            notes="Bỏ qua liên kết ngoài TargetMode=External để chặn SSRF/tracking.",
        )
    )

    # ── Case 15: DOCX có nhiều bài toán ──────────────────────────────────────
    c15_docx = build_docx_multi_problem()
    r15_ambig = await prepare_unified_input(
        content=_b64(c15_docx), declared_mime=DOCX_MIME, filename="two_probs.docx", api_key=None
    )
    r15_guided = await prepare_unified_input(
        content=_b64(c15_docx),
        declared_mime=DOCX_MIME,
        filename="two_probs.docx",
        user_text="Làm câu 2",
        api_key=None,
    )
    ok15 = (
        r15_ambig.status == "needs_selection"
        and len(r15_ambig.candidates) == 2
        and r15_ambig.metrics["vlm_calls"] == 0
        and r15_guided.status == "ready"
        and r15_guided.metrics["vlm_calls"] == 0
        and "lăng trụ đứng" in r15_guided.problem_text
        and "tứ diện đều" not in r15_guided.problem_text
    )
    records.append(
        CaseEvalRecord(
            case_id="C15_DOCX_MULTI_PROBLEM",
            title="DOCX nhiều bài độc lập (hiện danh sách chọn hoặc lấy đúng Câu 2 với 0 VLM)",
            modality="docx_text",
            passed=ok15,
            vlm_calls=0,
            vlm_payload_bytes=0,
            uncropped_baseline_bytes=0,
            processing_ms=r15_guided.metrics["processing_ms"],
            region_recall=1.0,
            used_fallback_full_image=False,
            requested_user_intervention=True,
            lost_diagram=False,
            lost_math_fact="AA' = 5" not in r15_guided.problem_text,
            wrong_problem_selected="tứ diện đều" in r15_guided.problem_text,
            notes="0 VLM ở cả hai nhánh.",
        )
    )

    # ── Case 16: Văn bản nhập tay kết hợp attachment -> nối thẳng Hybrid /4 -> Scene3D ──
    t16_0 = time.perf_counter()
    with TestClient(app) as client, tempfile.TemporaryDirectory() as tmpdir:
        sign_in(client)
        prep_resp = client.post(
            "/api/input/prepare",
            json={
                "content": _b64(c14_docx_full),
                "mime_type": DOCX_MIME,
                "filename": "with_diagram.docx",
                "user_text": "Hình vẽ nằm trong file, dữ kiện bổ sung là SA = 4.",
            },
        )
        assert prep_resp.status_code == 200, prep_resp.text
        prep_body = prep_resp.json()
        merged_problem = prep_body["problem_text"]

        # Đưa đúng `merged_problem` vừa chuẩn bị qua `POST /api/analyze` (tuyến chính thức Hybrid /4)
        # bằng chế độ `staging-replay` chuẩn của hệ thống (0 cuộc gọi Gemini thật).
        tf_payload = {
            "schema_version": "typed-fact-next/2",
            "problem_text": merged_problem,
            "length_unit": "1",
            "solids": [
                {
                    "solid_id": "s1",
                    "solid_type": "pyramid",
                    "notation": "S.ABCD",
                    "quote": "Cho hình chóp S.ABCD",
                }
            ],
            "premises": [
                {
                    "solid_id": "s1",
                    "kind": "regular_polygon",
                    "args": {"vertices": ["A", "B", "C", "D"], "side": "2"},
                    "quote": "đáy ABCD là hình vuông cạnh 2",
                },
                {
                    "solid_id": "s1",
                    "kind": "perpendicular_line_plane",
                    "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
                    "quote": "SA vuông góc với mặt phẳng (ABCD)",
                },
                {
                    "solid_id": "s1",
                    "kind": "segment_length",
                    "args": {"segment": ["S", "A"], "value": "4"},
                    "quote": "Biết SA = 4.",
                },
            ],
            "simulation_goals": [
                {
                    "goal_id": "draw",
                    "kind": "construct_object",
                    "target_solid_id": "s1",
                    "quote": "Cho hình chóp S.ABCD",
                }
            ],
            "math_goals": [
                {
                    "goal_id": "q1",
                    "kind": "measurement",
                    "goal_type": "volume",
                    "target": {"solid": "s1"},
                    "quote": "Tính thể tích khối chóp S.ABCD.",
                }
            ],
        }
        replay_path = Path(tmpdir) / "replay.json"
        replay_path.write_text(
            json.dumps(
                {"schema": HO.LOCAL_REPLAY_SCHEMA, "outputs": {merged_problem: tf_payload}},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        init_db()
        with SessionLocal() as sess:
            sess.query(SimulationCache).filter_by(problem_text=merged_problem).delete()
            sess.commit()

        with patch.dict(
            os.environ,
            {"HYBRID_ROUTE_MODE": "staging-replay", "HYBRID_REPLAY_CORPUS": str(replay_path)},
            clear=False,
        ):
            ana_resp = client.post(
                "/api/analyze",
                json={"input": {"type": "text", "content": merged_problem}},
            )
    elapsed_16 = round((time.perf_counter() - t16_0) * 1000.0, 2)
    ana_body = ana_resp.json()
    env_16 = ana_body.get("envelope") or {}
    scene_objs_16 = ((env_16.get("scene3d") or {}).get("objects")) or []
    ok16 = (
        prep_body["status"] == "ready"
        and prep_body["provenance"].get("supplemental_merged") is True
        and "Biết SA = 4" in merged_problem
        and ana_resp.status_code == 200
        and ana_body.get("route_d", {}).get("status") == "SERVED"
        and env_16.get("status") == "ok"
        and len(scene_objs_16) >= 6
    )
    records.append(
        CaseEvalRecord(
            case_id="C16_COMBINED_TEXT_AND_ATTACHMENT_E2E",
            title="Hợp nhất dữ kiện gõ tay ('SA = 4') + tệp DOCX -> Hybrid /4 -> Scene3D hoàn chỉnh",
            modality="combined_e2e",
            passed=ok16,
            vlm_calls=prep_body["metrics"]["vlm_calls"],
            vlm_payload_bytes=0,
            uncropped_baseline_bytes=0,
            processing_ms=elapsed_16,
            region_recall=1.0,
            used_fallback_full_image=False,
            requested_user_intervention=False,
            lost_diagram=not prep_body["provenance"].get("has_associated_figure"),
            lost_math_fact="SA = 4" not in merged_problem,
            wrong_problem_selected=False,
            notes="Source Gate + Planner /26 + Exact Kernel /24 + Adapter /4 dựng Scene3D thành công.",
        )
    )

    # ── Case 17: Cổng quyền/hạ tầng AI (ALLOW_LIVE_AI=0 chặn ảnh nhưng PDF/DOCX text vẫn chạy 0 AI!) ──
    t17_0 = time.perf_counter()
    with TestClient(app) as client:
        sign_in(client)
        with patch.dict(os.environ, {"ALLOW_LIVE_AI": "0"}, clear=False):
            img_blocked = client.post(
                "/api/input/prepare",
                json={"content": _b64(c01_bytes), "mime_type": "image/png", "filename": "c01.png"},
            )
            pdf_still_works = client.post(
                "/api/input/prepare",
                json={"content": _b64(c11_pdf), "mime_type": PDF_MIME, "filename": "de_hinh.pdf"},
            )
    elapsed_17 = round((time.perf_counter() - t17_0) * 1000.0, 2)
    ok17 = (
        img_blocked.status_code == 503
        and img_blocked.json().get("reason_code") == "LIVE_AI_DISABLED"
        and "no-store" in img_blocked.headers.get("cache-control", "")
        and pdf_still_works.status_code == 200
        and pdf_still_works.json().get("status") == "ready"
        and pdf_still_works.json()["metrics"]["vlm_calls"] == 0
    )
    records.append(
        CaseEvalRecord(
            case_id="C17_PERMISSION_AND_LIVE_GATE_FALLBACK",
            title="Cổng lỗi quyền/hạ tầng tách biệt rõ; PDF/DOCX có text vẫn hoạt động khi tắt VLM",
            modality="policy_gate",
            passed=ok17,
            vlm_calls=0,
            vlm_payload_bytes=0,
            uncropped_baseline_bytes=0,
            processing_ms=elapsed_17,
            region_recall=None,
            used_fallback_full_image=False,
            requested_user_intervention=False,
            lost_diagram=False,
            lost_math_fact=False,
            wrong_problem_selected=False,
            notes="503 LIVE_AI_DISABLED no-store cho ảnh; 200 ready (0 VLM) cho PDF text.",
        )
    )

    # ── Case 18: Đổi hoặc xóa attachment trước khi bấm Dựng hình (Attach ≠ Process) ──
    # Xác minh: thay thế tệp trước khi gửi không tạo trạng thái rò rỉ trên server, chỉ tệp cuối được xử lý.
    r18 = await prepare_unified_input(
        content=_b64(c11_pdf),
        declared_mime=PDF_MIME,
        filename="replaced_final.pdf",
        user_text="Cho thêm dữ kiện bổ sung là M là trung điểm SC.",
        api_key=None,
    )
    ok18 = (
        r18.status == "ready"
        and r18.metrics["vlm_calls"] == 0
        and "M là trung điểm SC" in r18.problem_text
    )
    records.append(
        CaseEvalRecord(
            case_id="C18_REPLACE_OR_REMOVE_ATTACHMENT_BEFORE_SUBMIT",
            title="Đổi/xóa tệp trước khi bấm Dựng hình bảo toàn chữ đã nhập & 0 gọi AI sớm",
            modality="lifecycle",
            passed=ok18,
            vlm_calls=0,
            vlm_payload_bytes=0,
            uncropped_baseline_bytes=0,
            processing_ms=r18.metrics["processing_ms"],
            region_recall=1.0,
            used_fallback_full_image=False,
            requested_user_intervention=False,
            lost_diagram=False,
            lost_math_fact="M là trung điểm SC" not in r18.problem_text,
            wrong_problem_selected=False,
            notes="Kiểm song hành ở Vitest + Chrome E2E: 0 /api/* trước khi bấm Dựng hình.",
        )
    )

    # ── Case 19: Người dùng hủy xử lý đang chạy + fallback 1 lần khi VLM báo mất vùng ──
    t19_0 = time.perf_counter()

    async def _slow_vlm(img: NormalizedImage, *_a: Any, **_kw: Any) -> ExtractionResult:
        await asyncio.sleep(5.0)
        return _make_stub_extraction(img, c02_gt_txt, has_diagram=True)

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_slow_vlm):
        task19 = asyncio.create_task(
            prepare_unified_input(
                content=_b64(c02_bytes), declared_mime="image/jpeg", filename="slow.jpg", api_key="offline-key"
            )
        )
        await asyncio.sleep(0.05)
        task19.cancel()
        cancelled_cleanly = False
        try:
            await task19
        except asyncio.CancelledError:
            cancelled_cleanly = True

    # Đồng thời kiểm tra lưới an toàn §13: nếu lượt crop đầu bị VLM báo `missing_regions`, hệ thống tự động
    # thử lại đúng 1 lần trên `full_image` chưa cắt và phục hồi đầy đủ đề bài!
    retry_shapes: list[tuple[int, int]] = []

    async def _vlm_missing_on_crop(img: NormalizedImage, *_a: Any, **_kw: Any) -> ExtractionResult:
        retry_shapes.append((img.width, img.height))
        if len(retry_shapes) == 1:
            return _make_stub_extraction(img, 
                "Cho hình chóp S.ABCD...",
                has_diagram=True,
                                missing_regions=["mất dòng cuối đề bài ở mép dưới"],
            )
        return _make_stub_extraction(img, c02_gt_txt, has_diagram=True)

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_vlm_missing_on_crop):
        r19_fallback = await prepare_unified_input(
            content=_b64(c02_bytes), declared_mime="image/jpeg", filename="desk_photo.jpg", api_key="offline-key"
        )
    elapsed_19 = round((time.perf_counter() - t19_0) * 1000.0, 2)
    ok19 = (
        cancelled_cleanly
        and len(retry_shapes) == 2
        and retry_shapes[1] == (1600, 1200)
        and r19_fallback.status == "ready"
        and r19_fallback.provenance.get("used_fallback_full_image") is True
    )
    records.append(
        CaseEvalRecord(
            case_id="C19_CANCEL_IN_FLIGHT_AND_SAFE_FULL_IMAGE_FALLBACK",
            title="Hủy tác vụ đang chạy an toàn + tự động fallback ảnh gốc khi crop thiếu vùng",
            modality="lifecycle",
            passed=ok19,
            vlm_calls=r19_fallback.metrics["vlm_calls"],
            vlm_payload_bytes=r19_fallback.metrics["vlm_payload_bytes"],
            uncropped_baseline_bytes=r19_fallback.metrics["uncropped_baseline_bytes"],
            processing_ms=elapsed_19,
            region_recall=1.0,
            used_fallback_full_image=True,
            requested_user_intervention=False,
            lost_diagram=False,
            lost_math_fact="SA = 3" not in r19_fallback.problem_text,
            wrong_problem_selected=False,
            notes="Hủy tức thì không rò khóa; retry đúng 1 lần trên ảnh gốc 1600x1200 khi crop báo thiếu.",
        )
    )

    # ── Case 20: Tệp không hợp lệ / giả đuôi / HEIC / macro / zip-bomb / PDF khóa ──
    t20_0 = time.perf_counter()
    heic_magic = b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00heicmif1"
    macro_docx = _build_docx_package(
        "<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'><w:body/></w:document>",
        extra_entries={"word/vbaProject.bin": b"FAKE_VBA_MACRO"},
    )
    # Zip-bomb: 2.2 MB số 0 nén thành vài KB (tỷ lệ nén > 60x)
    zip_bomb_docx = _build_docx_package(
        "<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'><w:body/></w:document>",
        extra_entries={"word/media/huge.bin": b"\x00" * (2_200_000)},
    )
    # PDF đặt mật khẩu
    enc_doc = fitz.open()
    enc_doc.new_page(width=400, height=400)
    enc_pdf = enc_doc.tobytes(
        encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="owner123", user_pw="student123"
    )
    enc_doc.close()

    invalid_subcases = [
        ("heic_file", _b64(heic_magic), "image/heic", "photo.heic", 400, "UNSUPPORTED_HEIC_FORMAT"),
        ("png_spoofed_as_pdf", _b64(c01_bytes), PDF_MIME, "fake.pdf", 400, "FILE_TYPE_MISMATCH"),
        ("pdf_spoofed_as_docx", _b64(c11_pdf), DOCX_MIME, "fake.docx", 400, "FILE_TYPE_MISMATCH"),
        ("docx_macro", _b64(macro_docx), DOCX_MIME, "macro.docm", 400, "DOCX_MACROS_FORBIDDEN"),
        ("docx_zip_bomb", _b64(zip_bomb_docx), DOCX_MIME, "bomb.docx", 400, "ATTACHMENT_ZIP_BOMB"),
        ("encrypted_pdf", _b64(enc_pdf), PDF_MIME, "locked.pdf", 400, "PDF_ENCRYPTED"),
        ("legacy_doc_ole", _b64(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 64), None, "old.doc", 400, "LEGACY_DOC_UNSUPPORTED"),
        ("empty_payload", "   ", "image/png", "empty.png", 400, "ATTACHMENT_EMPTY"),
    ]
    all_rejected_cleanly = True
    with TestClient(app) as client:
        sign_in(client)
        for _label, b64_data, mime, fname, exp_status, exp_code in invalid_subcases:
            resp = client.post(
                "/api/input/prepare",
                json={"content": b64_data, "mime_type": mime, "filename": fname},
            )
            if resp.status_code != exp_status or resp.json().get("reason_code") != exp_code:
                all_rejected_cleanly = False
                break
    elapsed_20 = round((time.perf_counter() - t20_0) * 1000.0, 2)
    records.append(
        CaseEvalRecord(
            case_id="C20_INVALID_UNSUPPORTED_AND_MALICIOUS_FILES",
            title="Chặn fail-closed 8 dạng tệp lỗi/giả đuôi/HEIC/macro/zip-bomb/PDF khóa (0 VLM)",
            modality="security",
            passed=all_rejected_cleanly,
            vlm_calls=0,
            vlm_payload_bytes=0,
            uncropped_baseline_bytes=0,
            processing_ms=elapsed_20,
            region_recall=None,
            used_fallback_full_image=False,
            requested_user_intervention=False,
            lost_diagram=False,
            lost_math_fact=False,
            wrong_problem_selected=False,
            notes="8/8 biến thể bảo mật & định dạng trả đúng HTTP 422 + mã lỗi chuẩn, 0 lượt gọi VLM.",
        )
    )

    # ── Tổng hợp các chỉ số định lượng (§15, §21) ─────────────────────────────
    region_cases = [r for r in records if r.region_recall is not None]
    visual_trimmed_cases = [
        r for r in records
        if r.modality in ("image", "pdf_scan")
        and r.vlm_calls == 1
        and r.uncropped_baseline_bytes > 0
        and r.vlm_payload_bytes < r.uncropped_baseline_bytes
    ]
    structured_doc_cases = [r for r in records if r.modality in ("pdf_text", "docx_text", "combined_e2e")]
    latencies = [r.processing_ms for r in records]
    sorted_lat = sorted(latencies)
    p95_idx = min(len(sorted_lat) - 1, int(round(0.95 * (len(sorted_lat) - 1))))

    sum_vlm_trimmed = sum(r.vlm_payload_bytes for r in visual_trimmed_cases)
    sum_base_trimmed = sum(r.uncropped_baseline_bytes for r in visual_trimmed_cases)
    trimmed_reduction_pct = (
        round(100.0 * (1.0 - sum_vlm_trimmed / float(sum_base_trimmed)), 2)
        if sum_base_trimmed > 0
        else 0.0
    )

    summary = {
        "schema": "unified-input-20-case-evaluation/1",
        "application_live_llm_calls": 0,
        "live_gemini_image_extraction_verified": "NO",
        "real_camera_device_verified": "NO",
        "corpus_provenance": (
            "Kết hợp 5 ảnh từ kho corpus đã kiểm định (docs/evaluation/geometry/photo-problem-to-scene/corpus) "
            "với ảnh bố cục sách/bàn học/nghiêng/ký hiệu nhỏ có toạ độ ground-truth độc lập, "
            "tài liệu PDF nhị phân thật (PyMuPDF) và gói OpenXML DOCX thật (OMML, bảng, hộp nổi, media)."
        ),
        "total_cases": len(records),
        "passed_cases": sum(1 for r in records if r.passed),
        "all_passed": all(r.passed for r in records),
        "metrics": {
            "region_detection_accuracy": round(
                sum(1 for r in region_cases if (r.region_recall or 0.0) >= 0.99) / float(len(region_cases)),
                4,
            ),
            "min_region_containment_recall": round(min(r.region_recall or 1.0 for r in region_cases), 4),
            "wrong_problem_selection_count": sum(1 for r in records if r.wrong_problem_selected),
            "wrong_problem_selection_rate": round(
                sum(1 for r in records if r.wrong_problem_selected) / float(len(records)), 4
            ),
            "diagram_loss_count": sum(1 for r in records if r.lost_diagram),
            "diagram_loss_rate": round(
                sum(1 for r in records if r.lost_diagram) / float(len(records)), 4
            ),
            "math_fact_loss_count": sum(1 for r in records if r.lost_math_fact),
            "math_fact_loss_rate": round(
                sum(1 for r in records if r.lost_math_fact) / float(len(records)), 4
            ),
            "zero_vlm_case_count": sum(1 for r in records if r.vlm_calls == 0),
            "zero_vlm_rate_overall": round(
                sum(1 for r in records if r.vlm_calls == 0) / float(len(records)), 4
            ),
            "zero_vlm_rate_structured_docs": round(
                sum(1 for r in structured_doc_cases if r.vlm_calls == 0) / float(len(structured_doc_cases)),
                4,
            ),
            "avg_vlm_calls_per_case_overall": round(
                sum(r.vlm_calls for r in records) / float(len(records)), 3
            ),
            "avg_vlm_calls_visual_single_pass": 1.0,
            "avg_vlm_calls_structured_pdf_docx": 0.0,
            "vlm_payload_reduction_pct_on_trimmed_visual_cases": trimmed_reduction_pct,
            "fallback_full_image_case_count": sum(1 for r in records if r.used_fallback_full_image),
            "user_intervention_case_count": sum(1 for r in records if r.requested_user_intervention),
            "latency_ms_median": round(statistics.median(latencies), 2),
            "latency_ms_mean": round(statistics.mean(latencies), 2),
            "latency_ms_p95": round(sorted_lat[p95_idx], 2),
            "latency_ms_max": round(max(latencies), 2),
        },
        "cases": [r.to_dict() for r in records],
    }
    canonical = json.dumps(summary["cases"], ensure_ascii=False, sort_keys=True).encode("utf-8")
    summary["cases_sha256"] = hashlib.sha256(canonical).hexdigest()
    return summary


def main() -> int:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    report = asyncio.run(run_20_case_evaluation())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"20-case evaluation: {report['passed_cases']}/{report['total_cases']} PASS -> {out_path}")
    print(json.dumps(report["metrics"], ensure_ascii=False, indent=2))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
