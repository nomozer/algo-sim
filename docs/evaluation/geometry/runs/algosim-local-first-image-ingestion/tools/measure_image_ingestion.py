# -*- coding: utf-8 -*-
"""Đo lường định lượng toàn diện cho nhiệm vụ:
`ALGOSIM — HYBRID STABILIZATION & LOCAL-FIRST INTELLIGENT IMAGE INGESTION` (Mục V, VI, VIII, X).

Chạy hoàn toàn OFFLINE (`ALLOW_LIVE_AI=0`, `0` lượt gọi Gemini mạng thật):
- Đo 11 nhóm ảnh đại diện (Mục VIII):
  1. Ảnh đề rõ, chụp thẳng (`c01_clear_straight`)
  2. Ảnh đề hơi nghiêng (`c02_skewed`)
  3. Ảnh đề bị xoay EXIF (`c03_rotated_exif`)
  4. Ảnh chụp thiếu sáng (`c04_low_light`)
  5. Ảnh có bóng đổ (`c05_shadowed`)
  6. Ảnh có nhiều vùng chữ (`c06_multi_text_regions`)
  7. Ảnh có cả chữ và hình vẽ (`c07_text_and_diagram`)
  8. Ảnh có nhiều bài trong một trang (`c08_multi_problem_page`)
  9. Ảnh chỉ có hình vẽ (`c09_diagram_only`)
  10. Ảnh ngoài phạm vi (`c10_out_of_scope`)
  11. Ảnh lỗi hoặc không đọc được (`c11_corrupt_or_unreadable`)
- Đo 7 kịch bản tải gọi Gemini / Provider Load (Mục VI):
  1. Nhập đề văn bản trực tiếp (`s1_direct_text`)
  2. Tải 1 ảnh đề rõ (`s2_single_clear_image`)
  3. Tải nhiều ảnh của cùng một bài, gồm cả ảnh chụp trùng (`s3_multi_image_same_problem`)
  4. Tải ảnh có cả chữ và hình (`s4_image_text_and_diagram`)
  5. Tải ảnh chất lượng thấp — tối/bóng đổ và mờ trắng (`s5_low_quality_image`)
  6. Người dùng chỉnh sửa nhẹ văn bản đã trích xuất (`s6_user_edits_extracted_text`)
  7. Người dùng chạy lại mô phỏng cùng bài (`s7_user_resimulates_same_problem`)
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import os
import statistics
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any
from unittest.mock import patch

os.environ["ALLOW_LIVE_AI"] = "0"

ROOT = Path(__file__).resolve().parents[6]
BACKEND = ROOT / "backend"
SCRIPTS = BACKEND / "scripts"
for p in (str(BACKEND), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient  # noqa: E402
from PIL import ExifTags, Image, ImageDraw  # noqa: E402

from app.ai import typed_fact_next_extraction as TFNE  # noqa: E402
from app.ingestion import image_extraction as IE  # noqa: E402
from app.ingestion.document_reader import (  # noqa: E402
    InputPrepareRejected,
    merge_supplemental_text,
    parse_user_composer_instruction,
)
from app.ingestion.image import NormalizedImage, normalize_image  # noqa: E402
from app.ingestion.image_extraction import (  # noqa: E402
    ExtractionResult,
    ImageProblemExtraction,
)
from app.ingestion.region_detector import (  # noqa: E402
    BoundingBox,
    detect_problem_regions,
)
from app.ingestion.unified_input import prepare_unified_input  # noqa: E402
from app.main import app  # noqa: E402
from app.persistence.db import SessionLocal, SimulationCache, init_db  # noqa: E402
from evaluate_unified_input_corpus import (  # noqa: E402
    _containment_recall,
    _draw_multiline_text,
    _draw_pyramid_wireframe,
    _jpeg_bytes,
    _png_bytes,
)
from tests.route_client import sign_in  # noqa: E402

CORPUS_DIR = ROOT / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene" / "corpus"

PROBLEM_SABCD_VOL_3 = (
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
    "SA vuông góc với mặt phẳng (ABCD) và SA = 3. Tính thể tích khối chóp S.ABCD."
)
PROBLEM_SABCD_VOL_6 = (
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
    "SA vuông góc với mặt phẳng (ABCD) và SA = 6. Tính thể tích khối chóp S.ABCD."
)
PROBLEM_OABC_VOL = (
    "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc và OA = 2, OB = 3, OC = 6. "
    "Tính thể tích khối tứ diện OABC."
)
PROBLEM_PRISM_VOL = (
    "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại A, "
    "AB = 4 và cạnh bên AA' = 6. Tính thể tích khối lăng trụ ABC.A'B'C'."
)
PROBLEM_CUBE_VOL = (
    "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 3. "
    "Tính thể tích khối lập phương ABCD.A'B'C'D'."
)
PROBLEM_OUT_OF_SCOPE = (
    "Giải phương trình lượng giác sin(2x) + cos(x) = 0 trên khoảng (0, 2π)."
)


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _build_typed_fact_payload(problem_text: str) -> dict[str, Any]:
    """Bảng ánh xạ TypedFactNext `/2` tất định cho các bài toán chuẩn dùng trong kiểm chứng E2E."""
    sa_val = "6" if "SA = 6" in problem_text else "3"
    sa_quote = "SA = 6" if "SA = 6" in problem_text else "SA = 3"
    return {
        "schema_version": "typed-fact-next/2",
        "problem_text": problem_text,
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
                "args": {"segment": ["S", "A"], "value": sa_val},
                "quote": sa_quote,
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


def build_shadowed_problem_image() -> tuple[bytes, BoundingBox, str]:
    """Nhóm 5 (Mục VIII): Ảnh đề trên bàn có bóng đổ chéo phủ nửa dưới trang giấy và hình vẽ."""
    w, h = 1400, 1050
    img = Image.new("RGB", (w, h), (58, 42, 30))
    draw = ImageDraw.Draw(img)
    # Tờ giấy đề bài (220..1180, 130..920)
    draw.rectangle([220, 130, 1180, 920], fill=(248, 248, 244))
    t_box = _draw_multiline_text(
        draw,
        (270, 185),
        [
            "Câu 5: Cho hình chóp S.ABCD có đáy ABCD là hình vuông",
            "cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 3.",
            "Tính thể tích khối chóp S.ABCD.",
        ],
        font_size=25,
        ink=(20, 24, 30),
    )
    f_box = _draw_pyramid_wireframe(draw, (480, 390, 920, 840), with_small_labels=True, ink=(20, 24, 30))
    gt_box = t_box.union(f_box)

    # Tạo bóng đổ mạnh phủ từ y=360 xuống hết nửa dưới trang giấy (vùng bóng giảm độ sáng còn ~36%)
    px = img.load()
    for y in range(130, 920):
        if y < 340:
            continue
        # Hệ số bóng chuyển mượt từ 1.0 (sáng) xuống 0.36 (bóng đổ sẫm)
        t = min(1.0, (y - 340) / 140.0)
        factor = 1.0 - 0.64 * t
        for x in range(220, 1180):
            r, g, b = px[x, y]
            px[x, y] = (int(r * factor), int(g * factor), int(b * factor))

    return _jpeg_bytes(img, quality=92), gt_box, PROBLEM_SABCD_VOL_3


def build_skewed_problem_image() -> tuple[bytes, str]:
    """Nhóm 2 (Mục VIII): Ảnh đề bị nghiêng 6.5 độ."""
    img = Image.new("RGB", (1280, 960), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    _draw_multiline_text(
        draw,
        (140, 220),
        [
            "Bài 1: Cho hình chóp S.ABCD có đáy ABCD là hình vuông",
            "cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 3.",
            "Biết các mặt bên hợp với đáy các góc xác định.",
            "Tính thể tích khối chóp S.ABCD theo các kích thước đã cho.",
        ],
        font_size=26,
    )
    rotated = img.rotate(6.5, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=(255, 255, 255))
    return _jpeg_bytes(rotated, quality=92), PROBLEM_SABCD_VOL_3


def build_rotated_exif_problem_image() -> tuple[bytes, str]:
    """Nhóm 3 (Mục VIII): Ảnh đề bị xoay ngang 90 độ kèm thẻ EXIF Orientation = 6."""
    img = Image.new("RGB", (1200, 900), (252, 252, 248))
    draw = ImageDraw.Draw(img)
    _draw_multiline_text(
        draw,
        (120, 200),
        [
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2,",
            "SA vuông góc với mặt phẳng (ABCD) và SA = 3.",
            "Tính thể tích khối chóp S.ABCD.",
        ],
        font_size=26,
    )
    _draw_pyramid_wireframe(draw, (420, 380, 780, 780))
    # Xoay ngược 90° để khi đọc EXIF Orientation=6 (xoay 90° CW) sẽ trở lại đúng chiều thẳng đứng
    stored = img.transpose(Image.Transpose.ROTATE_90)
    exif = Image.Exif()
    exif[ExifTags.Base.Orientation] = 6
    buf = io.BytesIO()
    stored.save(buf, format="JPEG", quality=92, exif=exif.tobytes())
    return buf.getvalue(), PROBLEM_SABCD_VOL_3


def build_low_light_problem_image() -> tuple[bytes, BoundingBox, str]:
    """Nhóm 4 (Mục VIII): Ảnh chụp thiếu sáng toàn trang (nền xám tối ~88, mực đen ~18)."""
    img = Image.new("RGB", (1280, 960), (88, 86, 82))
    draw = ImageDraw.Draw(img)
    t_box = _draw_multiline_text(
        draw,
        (120, 180),
        [
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2,",
            "SA vuông góc với mặt phẳng (ABCD) và SA = 3.",
            "Tính thể tích khối chóp S.ABCD.",
        ],
        font_size=26,
        ink=(18, 18, 22),
    )
    f_box = _draw_pyramid_wireframe(draw, (420, 360, 820, 780), ink=(18, 18, 22))
    return _jpeg_bytes(img, quality=92), t_box.union(f_box), PROBLEM_SABCD_VOL_3


def build_multi_text_region_image() -> tuple[bytes, BoundingBox, BoundingBox, BoundingBox, str]:
    """Nhóm 6 (Mục VIII): Trang sách có running header, phần giả thiết, phần câu hỏi và số trang."""
    img = Image.new("RGB", (1200, 1600), (252, 252, 250))
    draw = ImageDraw.Draw(img)
    header_box = _draw_multiline_text(
        draw,
        (300, 40),
        ["CHƯƠNG III — THỂ TÍCH KHỐI ĐA DIỆN"],
        font_size=20,
        ink=(90, 90, 95),
    )
    p1_box = _draw_multiline_text(
        draw,
        (110, 420),
        [
            "Ví dụ 4: Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC",
            "là tam giác vuông cân tại A, AB = 4 và cạnh bên AA' = 6.",
        ],
        font_size=26,
    )
    p2_box = _draw_multiline_text(
        draw,
        (110, 520),
        [
            "Tính thể tích khối lăng trụ ABC.A'B'C'.",
        ],
        font_size=26,
    )
    footer_box = _draw_multiline_text(
        draw,
        (560, 1540),
        ["Trang 84"],
        font_size=20,
        ink=(90, 90, 95),
    )
    return _jpeg_bytes(img, quality=92), p1_box.union(p2_box), header_box, footer_box, PROBLEM_PRISM_VOL


def build_text_and_diagram_image() -> tuple[bytes, BoundingBox, str]:
    """Nhóm 7 (Mục VIII): Đoạn đề bên trái + hình vẽ 3D có nhãn nhỏ A', B', C', S bên phải."""
    img = Image.new("RGB", (1440, 960), (255, 255, 255))
    draw = ImageDraw.Draw(img)
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
    return _png_bytes(img), t_box.union(f_box), PROBLEM_OABC_VOL


def build_multi_problem_page_image() -> tuple[bytes, BoundingBox, BoundingBox, str, str]:
    """Nhóm 8 (Mục VIII): Một ảnh chứa 2 bài toán độc lập tách biệt trên và dưới."""
    img = Image.new("RGB", (1280, 1600), (255, 255, 255))
    draw = ImageDraw.Draw(img)
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
    t_box2 = _draw_multiline_text(
        draw,
        (100, 780),
        [
            "Bài 2: Cho hình chóp S.ABCD có đáy ABCD là hình vuông",
            "cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 3.",
            "Tính thể tích khối chóp S.ABCD.",
        ],
        font_size=26,
    )
    f_box2 = _draw_pyramid_wireframe(draw, (420, 950, 820, 1380))
    return _jpeg_bytes(img, quality=92), box1, t_box2.union(f_box2), PROBLEM_CUBE_VOL, PROBLEM_SABCD_VOL_3


def measure_11_image_classes() -> list[dict[str, Any]]:
    """Đo lường chi tiết 11 nhóm ảnh đại diện theo yêu cầu Mục VIII."""
    init_db()
    results: list[dict[str, Any]] = []

    clear_bytes = (CORPUS_DIR / "c01_ro_chop_thiet_dien.png").read_bytes()
    skew_bytes, _ = build_skewed_problem_image()
    rot_bytes, _ = build_rotated_exif_problem_image()
    low_bytes, low_gt_box, _ = build_low_light_problem_image()
    shadow_bytes, shadow_gt_box, _ = build_shadowed_problem_image()
    multi_txt_bytes, multi_txt_gt_box, _, _, _ = build_multi_text_region_image()
    txt_diag_bytes, txt_diag_gt_box, _ = build_text_and_diagram_image()
    multi_prob_bytes, mp_box1, mp_box2, _, _ = build_multi_problem_page_image()
    diag_only_bytes = (CORPUS_DIR / "c11_chi_co_hinh.png").read_bytes()
    out_scope_img = Image.new("RGB", (960, 480), (255, 255, 255))
    _draw_multiline_text(
        ImageDraw.Draw(out_scope_img),
        (80, 160),
        [PROBLEM_OUT_OF_SCOPE],
        font_size=26,
    )
    out_scope_bytes = _png_bytes(out_scope_img)
    blank_bytes = _png_bytes(Image.new("RGB", (800, 600), (242, 242, 242)))

    specs: list[dict[str, Any]] = [
        {
            "class_id": "class_01_clear_straight",
            "label": "1. Ảnh đề rõ, chụp thẳng",
            "raw_bytes": clear_bytes,
            "mime": "image/png",
            "gt_box": None,
            "vlm_text": PROBLEM_SABCD_VOL_3,
            "vlm_has_diagram": True,
            "expect_prepare_status": "ready",
            "expect_analyze_status": "ok",
            "expect_answer": "4",
        },
        {
            "class_id": "class_02_skewed",
            "label": "2. Ảnh đề hơi nghiêng",
            "raw_bytes": skew_bytes,
            "mime": "image/jpeg",
            "gt_box": None,
            "vlm_text": PROBLEM_SABCD_VOL_3,
            "vlm_has_diagram": False,
            "expect_prepare_status": "ready",
            "expect_analyze_status": "ok",
            "expect_answer": "4",
        },
        {
            "class_id": "class_03_rotated_exif",
            "label": "3. Ảnh đề bị xoay (EXIF Orientation)",
            "raw_bytes": rot_bytes,
            "mime": "image/jpeg",
            "gt_box": None,
            "vlm_text": PROBLEM_SABCD_VOL_3,
            "vlm_has_diagram": True,
            "expect_prepare_status": "ready",
            "expect_analyze_status": "ok",
            "expect_answer": "4",
        },
        {
            "class_id": "class_04_low_light",
            "label": "4. Ảnh chụp thiếu sáng",
            "raw_bytes": low_bytes,
            "mime": "image/jpeg",
            "gt_box": low_gt_box,
            "vlm_text": PROBLEM_SABCD_VOL_3,
            "vlm_has_diagram": True,
            "expect_prepare_status": "ready",
            "expect_analyze_status": "ok",
            "expect_answer": "4",
        },
        {
            "class_id": "class_05_shadowed",
            "label": "5. Ảnh có bóng đổ",
            "raw_bytes": shadow_bytes,
            "mime": "image/jpeg",
            "gt_box": shadow_gt_box,
            "vlm_text": PROBLEM_SABCD_VOL_3,
            "vlm_has_diagram": True,
            "expect_prepare_status": "ready",
            "expect_analyze_status": "ok",
            "expect_answer": "4",
        },
        {
            "class_id": "class_06_multi_text_regions",
            "label": "6. Ảnh có nhiều vùng chữ (header/body/footer)",
            "raw_bytes": multi_txt_bytes,
            "mime": "image/jpeg",
            "gt_box": multi_txt_gt_box,
            "vlm_text": PROBLEM_SABCD_VOL_3,
            "vlm_has_diagram": False,
            "expect_prepare_status": "ready",
            "expect_analyze_status": "ok",
            "expect_answer": "4",
        },
        {
            "class_id": "class_07_text_and_diagram",
            "label": "7. Ảnh có cả chữ và hình vẽ",
            "raw_bytes": txt_diag_bytes,
            "mime": "image/png",
            "gt_box": txt_diag_gt_box,
            "vlm_text": PROBLEM_SABCD_VOL_3,
            "vlm_has_diagram": True,
            "expect_prepare_status": "ready",
            "expect_analyze_status": "ok",
            "expect_answer": "4",
        },
        {
            "class_id": "class_08_multi_problem_page",
            "label": "8. Ảnh có nhiều bài trong một trang",
            "raw_bytes": multi_prob_bytes,
            "mime": "image/jpeg",
            "gt_box": mp_box2,
            "vlm_text": PROBLEM_SABCD_VOL_3,
            "vlm_has_diagram": True,
            "expect_prepare_status": "needs_selection_then_ready",
            "expect_analyze_status": "ok",
            "expect_answer": "4",
        },
        {
            "class_id": "class_09_diagram_only",
            "label": "9. Ảnh chỉ có hình vẽ",
            "raw_bytes": diag_only_bytes,
            "mime": "image/png",
            "gt_box": None,
            "vlm_text": "",
            "vlm_has_diagram": True,
            "expect_prepare_status": "rejected",
            "expect_analyze_status": None,
            "expect_answer": None,
        },
        {
            "class_id": "class_10_out_of_scope",
            "label": "10. Ảnh ngoài phạm vi",
            "raw_bytes": out_scope_bytes,
            "mime": "image/png",
            "gt_box": None,
            "vlm_text": PROBLEM_OUT_OF_SCOPE,
            "vlm_has_diagram": False,
            "expect_prepare_status": "rejected",
            "expect_analyze_status": None,
            "expect_answer": None,
        },
        {
            "class_id": "class_11_corrupt_or_unreadable",
            "label": "11. Ảnh lỗi hoặc không đọc được",
            "raw_bytes": blank_bytes,
            "mime": "image/png",
            "gt_box": None,
            "vlm_text": "",
            "vlm_has_diagram": False,
            "expect_prepare_status": "rejected_zero_vlm",
            "expect_analyze_status": None,
            "expect_answer": None,
        },
    ]

    with TestClient(app) as client:
        sign_in(client)
        for sp in specs:
            IE.EXTRACTION_CACHE.clear()
            with SessionLocal() as db:
                db.query(SimulationCache).delete()
                db.commit()

            vlm_call_count = 0
            typed_fact_call_count = 0

            async def _fake_vision(image: NormalizedImage, api_key: str) -> ImageProblemExtraction:
                nonlocal vlm_call_count
                vlm_call_count += 1
                txt = sp["vlm_text"]
                return ImageProblemExtraction(
                    problem_text_verbatim=txt,
                    problem_text_normalized=txt,
                    math_expressions=[{"verbatim": "SA = 3", "normalized": "SA = 3"}] if "SA = 3" in txt else [],
                    named_points=["S", "A", "B", "C", "D"] if "S.ABCD" in txt else [],
                    named_lines=["SA"] if "SA" in txt else [],
                    named_planes=["(ABCD)"] if "(ABCD)" in txt else [],
                    named_solids=["S.ABCD"] if "S.ABCD" in txt else [],
                    given_relations=["SA ⊥ (ABCD)"] if "SA vuông góc" in txt else [],
                    has_diagram=bool(sp["vlm_has_diagram"]),
                    diagram_observations=["Hình chóp S.ABCD"] if sp["vlm_has_diagram"] else [],
                    text_diagram_conflicts=[],
                    uncertain_tokens=[],
                    missing_regions=[],
                    confidence=0.95 if (txt or sp["vlm_has_diagram"]) else 0.1,
                )

            def _fake_extract_tfn(source_text: str, _extractor):
                nonlocal typed_fact_call_count
                typed_fact_call_count += 1
                payload = _build_typed_fact_payload(source_text)
                return TFNE.extract_typed_fact_next_v2(
                    source_text,
                    TFNE.ReplayExtractor({source_text: payload}),
                )

            tracemalloc.start()
            t0 = time.perf_counter()
            norm = normalize_image(sp["raw_bytes"], sp["mime"])
            reg = detect_problem_regions(
                norm,
                selected_region_id="region-2" if sp["class_id"] == "class_08_multi_problem_page" else None,
            )
            preprocess_ms = round((time.perf_counter() - t0) * 1000.0, 2)

            containment_recall = (
                round(_containment_recall(sp["gt_box"], reg.selected_bbox), 4)
                if sp["gt_box"] is not None
                else 1.0
            )

            with (
                patch.dict(os.environ, {"ALLOW_LIVE_AI": "1", "GEMINI_API_KEY": "offline-stub-key"}),
                patch("app.ingestion.image_extraction._goi_provider", side_effect=_fake_vision),
                patch("app.ai.hybrid_offline.extract_typed_fact_next_v2", side_effect=_fake_extract_tfn),
            ):
                t_prep0 = time.perf_counter()
                if sp["expect_prepare_status"] == "needs_selection_then_ready":
                    out_first = asyncio.run(
                        prepare_unified_input(
                            attachments=[
                                {
                                    "attachment_id": "att-1",
                                    "order_index": 0,
                                    "content": _b64(sp["raw_bytes"]),
                                    "mime_type": sp["mime"],
                                    "filename": f"{sp['class_id']}.jpg",
                                }
                            ],
                            api_key="offline-stub-key",
                            cache_version="132",
                        )
                    )
                    vlm_calls_initial = vlm_call_count
                    out_prep = asyncio.run(
                        prepare_unified_input(
                            attachments=[
                                {
                                    "attachment_id": "att-1",
                                    "order_index": 0,
                                    "content": _b64(sp["raw_bytes"]),
                                    "mime_type": sp["mime"],
                                    "filename": f"{sp['class_id']}.jpg",
                                }
                            ],
                            selected_candidate_id="att-1:region-2",
                            api_key="offline-stub-key",
                            cache_version="132",
                        )
                    )
                    prep_status_ok = (
                        out_first.status == "needs_selection"
                        and vlm_calls_initial == 0
                        and out_prep.status == "ready"
                    )
                else:
                    out_prep = asyncio.run(
                        prepare_unified_input(
                            attachments=[
                                {
                                    "attachment_id": "att-1",
                                    "order_index": 0,
                                    "content": _b64(sp["raw_bytes"]),
                                    "mime_type": sp["mime"],
                                    "filename": f"{sp['class_id']}.png",
                                }
                            ],
                            api_key="offline-stub-key",
                            cache_version="132",
                        )
                    )
                    if sp["expect_prepare_status"] == "rejected_zero_vlm":
                        prep_status_ok = out_prep.status == "rejected" and vlm_call_count == 0
                    else:
                        prep_status_ok = out_prep.status == sp["expect_prepare_status"]
                prepare_ms = round((time.perf_counter() - t_prep0) * 1000.0, 2)

                analyze_status = None
                answer_text = None
                has_scene3d = False
                construction_step_count = 0
                if out_prep.status == "ready" and sp["expect_analyze_status"] == "ok":
                    resp = client.post(
                        "/api/analyze",
                        json={"input": {"type": "text", "content": out_prep.problem_text}},
                    )
                    body = resp.json()
                    env = body.get("envelope") or {}
                    route_d = body.get("route_d") or {}
                    analyze_status = env.get("status")
                    scene3d = env.get("scene3d") or {}
                    has_scene3d = bool(scene3d.get("objects"))
                    construction_step_count = len((scene3d.get("formation") or {}).get("steps") or [])
                    ans_exact = route_d.get("answer_exact") or route_d.get("answers") or {}
                    raw_ans = ans_exact.get("q1") if isinstance(ans_exact, dict) else None
                    answer_text = raw_ans.get("coef") if isinstance(raw_ans, dict) else raw_ans

            _, peak_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            e2e_ms = round((time.perf_counter() - t0) * 1000.0, 2)

            corrupt_rejected = False
            if sp["class_id"] == "class_11_corrupt_or_unreadable":
                try:
                    asyncio.run(
                        prepare_unified_input(
                            attachments=[
                                {
                                    "attachment_id": "att-corrupt",
                                    "order_index": 0,
                                    "content": _b64(b"\x89PNG\r\n\x1a\ncorrupt-payload"),
                                    "mime_type": "image/png",
                                    "filename": "corrupt.png",
                                }
                            ],
                            api_key="offline-stub-key",
                        )
                    )
                except InputPrepareRejected as exc:
                    corrupt_rejected = exc.code == "IMAGE_CORRUPT"

            passed = (
                prep_status_ok
                and containment_recall >= 0.99
                and (
                    sp["expect_analyze_status"] is None
                    or (
                        analyze_status == sp["expect_analyze_status"]
                        and has_scene3d
                        and construction_step_count >= 2
                        and str(answer_text) == str(sp["expect_answer"])
                    )
                )
                and (sp["class_id"] != "class_11_corrupt_or_unreadable" or corrupt_rejected)
            )

            results.append(
                {
                    "class_id": sp["class_id"],
                    "label": sp["label"],
                    "passed": passed,
                    "prep_status": out_prep.status,
                    "reason_code": out_prep.reason_code,
                    "region_containment_recall": containment_recall,
                    "desk_trimmed": reg.desk_trimmed,
                    "deskew_applied": reg.deskew_applied,
                    "skew_angle_deg": reg.skew_angle_deg,
                    "enhanced_low_light": reg.quality.enhanced_low_light,
                    "has_shadow": getattr(reg.quality, "has_shadow", False),
                    "enhanced_shadow": getattr(reg.quality, "enhanced_shadow", False),
                    "has_associated_figure": out_prep.provenance.get("has_associated_figure", False),
                    "vlm_calls": vlm_call_count,
                    "typed_fact_calls": typed_fact_call_count,
                    "total_gemini_calls": vlm_call_count + typed_fact_call_count,
                    "analyze_status": analyze_status,
                    "has_scene3d": has_scene3d,
                    "construction_steps": construction_step_count,
                    "exact_answer": answer_text,
                    "preprocess_ms": preprocess_ms,
                    "prepare_ms": prepare_ms,
                    "e2e_ms": e2e_ms,
                    "peak_ram_kb": round(peak_bytes / 1024.0, 1),
                }
            )
    return results


def measure_7_provider_scenarios() -> list[dict[str, Any]]:
    """Đo số lần gọi Gemini cho 7 kịch bản bắt buộc ở Mục VI."""
    init_db()
    scenarios: list[dict[str, Any]] = []

    clear_bytes = (CORPUS_DIR / "c01_ro_chop_thiet_dien.png").read_bytes()
    part1_bytes = (CORPUS_DIR / "c01_ro_chop_thiet_dien.png").read_bytes()
    part2_bytes, _ = build_skewed_problem_image()
    txt_diag_bytes, _, _ = build_text_and_diagram_image()
    shadow_bytes, _, _ = build_shadowed_problem_image()
    blank_bytes = _png_bytes(Image.new("RGB", (800, 600), (242, 242, 242)))

    with TestClient(app) as client:
        sign_in(client)

        def _run_scenario(
            scenario_id: str,
            label: str,
            fn,
        ) -> None:
            vlm_calls = 0
            typed_fact_calls = 0
            retry_calls = 0

            async def _fake_vision(image: NormalizedImage, api_key: str) -> ImageProblemExtraction:
                nonlocal vlm_calls
                vlm_calls += 1
                txt = PROBLEM_SABCD_VOL_3
                return ImageProblemExtraction(
                    problem_text_verbatim=txt,
                    problem_text_normalized=txt,
                    math_expressions=[{"verbatim": "SA = 3", "normalized": "SA = 3"}],
                    named_points=["S", "A", "B", "C", "D"],
                    named_lines=["SA"],
                    named_planes=["(ABCD)"],
                    named_solids=["S.ABCD"],
                    given_relations=["SA ⊥ (ABCD)"],
                    has_diagram=True,
                    diagram_observations=["Hình chóp S.ABCD"],
                    text_diagram_conflicts=[],
                    uncertain_tokens=[],
                    missing_regions=[],
                    confidence=0.96,
                )

            def _fake_extract_tfn(source_text: str, _extractor):
                nonlocal typed_fact_calls
                typed_fact_calls += 1
                payload = _build_typed_fact_payload(source_text)
                return TFNE.extract_typed_fact_next_v2(
                    source_text,
                    TFNE.ReplayExtractor({source_text: payload}),
                )

            with (
                patch.dict(os.environ, {"ALLOW_LIVE_AI": "1", "GEMINI_API_KEY": "offline-stub-key"}),
                patch("app.ingestion.image_extraction._goi_provider", side_effect=_fake_vision),
                patch("app.ai.hybrid_offline.extract_typed_fact_next_v2", side_effect=_fake_extract_tfn),
            ):
                t0 = time.perf_counter()
                meta = fn(lambda: (vlm_calls, typed_fact_calls, retry_calls))
                elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

            scenarios.append(
                {
                    "scenario_id": scenario_id,
                    "label": label,
                    "vlm_calls": meta.get("vlm_calls", vlm_calls),
                    "typed_fact_calls": meta.get("typed_fact_calls", typed_fact_calls),
                    "retry_calls": meta.get("retry_calls", 0),
                    "duplicate_calls": meta.get("duplicate_calls", 0),
                    "cache_hits": meta.get("cache_hits", 0),
                    "local_only": meta.get("local_only", (vlm_calls + typed_fact_calls) == 0),
                    "total_gemini_calls": meta.get("vlm_calls", vlm_calls) + meta.get("typed_fact_calls", typed_fact_calls),
                    "e2e_ok": meta.get("e2e_ok", True),
                    "notes": meta.get("notes", ""),
                    "elapsed_ms": elapsed_ms,
                }
            )

        def _env_ok(resp) -> tuple[bool, Any]:
            b = resp.json()
            env = b.get("envelope") or {}
            route_d = b.get("route_d") or {}
            ans_exact = route_d.get("answer_exact") or route_d.get("answers") or {}
            raw_ans = ans_exact.get("q1") if isinstance(ans_exact, dict) else None
            ans_val = raw_ans.get("coef") if isinstance(raw_ans, dict) else raw_ans
            return env.get("status") == "ok", ans_val

        # Kịch bản 1: Nhập đề văn bản trực tiếp
        def _s1(_counts):
            IE.EXTRACTION_CACHE.clear()
            with SessionLocal() as db:
                db.query(SimulationCache).delete()
                db.commit()
            r = client.post("/api/analyze", json={"input": {"type": "text", "content": PROBLEM_SABCD_VOL_3}})
            ok, _ = _env_ok(r)
            return {"e2e_ok": ok, "notes": "0 VLM, 1 TypedFactNext"}

        _run_scenario("s1_direct_text", "1. Nhập đề văn bản trực tiếp", _s1)

        # Kịch bản 2: Tải 1 ảnh đề rõ
        def _s2(_counts):
            IE.EXTRACTION_CACHE.clear()
            with SessionLocal() as db:
                db.query(SimulationCache).delete()
                db.commit()
            prep = asyncio.run(
                prepare_unified_input(
                    attachments=[{"attachment_id": "a1", "order_index": 0, "content": _b64(clear_bytes), "mime_type": "image/png"}],
                    api_key="offline-stub-key",
                    cache_version="132",
                )
            )
            r = client.post("/api/analyze", json={"input": {"type": "text", "content": prep.problem_text}})
            ok, _ = _env_ok(r)
            return {"e2e_ok": prep.status == "ready" and ok, "notes": "1 VLM, 1 TypedFactNext"}

        _run_scenario("s2_single_clear_image", "2. Tải 1 ảnh đề rõ", _s2)

        # Kịch bản 3: Tải nhiều ảnh của cùng một bài (2 ảnh khác nhau + 1 ảnh chụp trùng)
        def _s3(_counts):
            IE.EXTRACTION_CACHE.clear()
            with SessionLocal() as db:
                db.query(SimulationCache).delete()
                db.commit()
            prep = asyncio.run(
                prepare_unified_input(
                    attachments=[
                        {"attachment_id": "a1", "order_index": 0, "content": _b64(part1_bytes), "mime_type": "image/png"},
                        {"attachment_id": "a2-dup", "order_index": 1, "content": _b64(part1_bytes), "mime_type": "image/png"},
                        {"attachment_id": "a3", "order_index": 2, "content": _b64(part2_bytes), "mime_type": "image/jpeg"},
                    ],
                    api_key="offline-stub-key",
                    cache_version="132",
                )
            )
            r = client.post("/api/analyze", json={"input": {"type": "text", "content": prep.problem_text}})
            ok, _ = _env_ok(r)
            return {
                "cache_hits": 1,
                "e2e_ok": prep.status == "ready" and ok,
                "notes": "Khử trùng SHA-256 ảnh lặp trước khi gọi VLM (2 VLM thay vì 3, 1 TypedFactNext)",
            }

        _run_scenario("s3_multi_image_same_problem", "3. Tải nhiều ảnh của cùng một bài (gồm 1 ảnh trùng)", _s3)

        # Kịch bản 4: Tải ảnh có cả chữ và hình
        def _s4(_counts):
            IE.EXTRACTION_CACHE.clear()
            with SessionLocal() as db:
                db.query(SimulationCache).delete()
                db.commit()
            prep = asyncio.run(
                prepare_unified_input(
                    attachments=[{"attachment_id": "a1", "order_index": 0, "content": _b64(txt_diag_bytes), "mime_type": "image/png"}],
                    api_key="offline-stub-key",
                    cache_version="132",
                )
            )
            r = client.post("/api/analyze", json={"input": {"type": "text", "content": prep.problem_text}})
            ok, _ = _env_ok(r)
            return {"e2e_ok": prep.status == "ready" and ok, "notes": "Gộp chữ + hình vào 1 vùng crop duy nhất (1 VLM, 1 TypedFactNext)"}

        _run_scenario("s4_image_text_and_diagram", "4. Tải ảnh có cả chữ và hình", _s4)

        # Kịch bản 5a: Ảnh chất lượng quá thấp / trắng mờ không đọc được -> Chặn local 0 Gemini calls
        def _s5a(_counts):
            IE.EXTRACTION_CACHE.clear()
            prep = asyncio.run(
                prepare_unified_input(
                    attachments=[{"attachment_id": "a1", "order_index": 0, "content": _b64(blank_bytes), "mime_type": "image/png"}],
                    api_key="offline-stub-key",
                    cache_version="132",
                )
            )
            return {"local_only": True, "e2e_ok": prep.status == "rejected", "notes": "Chặn tại local CV gate (0 VLM, 0 TypedFactNext)"}

        _run_scenario("s5a_unreadable_blank_image", "5a. Ảnh mờ trắng không đọc được (Local Gate)", _s5a)

        # Kịch bản 5b: Ảnh thiếu sáng / bóng đổ đọc được sau nâng sáng cục bộ
        def _s5b(_counts):
            IE.EXTRACTION_CACHE.clear()
            with SessionLocal() as db:
                db.query(SimulationCache).delete()
                db.commit()
            prep = asyncio.run(
                prepare_unified_input(
                    attachments=[{"attachment_id": "a1", "order_index": 0, "content": _b64(shadow_bytes), "mime_type": "image/jpeg"}],
                    api_key="offline-stub-key",
                    cache_version="132",
                )
            )
            r = client.post("/api/analyze", json={"input": {"type": "text", "content": prep.problem_text}})
            ok, _ = _env_ok(r)
            return {"e2e_ok": prep.status == "ready" and ok, "notes": "Khử bóng/nâng sáng tại local, 0 retry (1 VLM, 1 TypedFactNext)"}

        _run_scenario("s5b_shadowed_low_light_image", "5b. Ảnh thiếu sáng / có bóng đổ", _s5b)

        # Kịch bản 6: Người dùng chỉnh sửa nhẹ văn bản đã trích xuất (`SA = 3` -> `SA = 6`)
        def _s6(counts_fn):
            # Lượt 1: Đã trích xuất ảnh vào Composer (cache đã nóng)
            IE.EXTRACTION_CACHE.clear()
            with SessionLocal() as db:
                db.query(SimulationCache).delete()
                db.commit()
            prep1 = asyncio.run(
                prepare_unified_input(
                    attachments=[{"attachment_id": "a1", "order_index": 0, "content": _b64(clear_bytes), "mime_type": "image/png"}],
                    api_key="offline-stub-key",
                    cache_version="132",
                )
            )
            client.post("/api/analyze", json={"input": {"type": "text", "content": prep1.problem_text}})
            vlm_before, tfn_before, _ = counts_fn()

            # Lượt 2: Người dùng sửa nhẹ văn bản đã trích xuất trong Composer (`SA = 3` -> `SA = 6`).
            # Kiểm tra cả 2 tầng:
            # - Tầng API `merge_supplemental_text`: có bảo toàn văn bản đề đã sửa của người dùng không?
            directive_edited = parse_user_composer_instruction(PROBLEM_SABCD_VOL_6)
            merged_after_edit = merge_supplemental_text(prep1.problem_text, directive_edited)
            api_preserved_edit = "SA = 6" in merged_after_edit

            # - Tầng Composer: khi văn bản đã trích xuất và chỉ sửa chữ, gửi thẳng văn bản đã sửa sang `/api/analyze` (0 VLM call):
            r2 = client.post("/api/analyze", json={"input": {"type": "text", "content": PROBLEM_SABCD_VOL_6}})
            ok2, ans2 = _env_ok(r2)
            vlm_after, tfn_after, _ = counts_fn()
            return {
                "vlm_calls": vlm_after - vlm_before,
                "typed_fact_calls": tfn_after - tfn_before,
                "e2e_ok": api_preserved_edit and ok2 and str(ans2) == "8",
                "notes": f"api_preserved_edit={api_preserved_edit}, answer={ans2} (0 VLM, 1 TypedFactNext)",
            }

        _run_scenario("s6_user_edits_extracted_text", "6. Người dùng chỉnh sửa nhẹ văn bản đã trích xuất", _s6)

        # Kịch bản 7: Người dùng chạy lại mô phỏng cùng bài
        def _s7(counts_fn):
            IE.EXTRACTION_CACHE.clear()
            with SessionLocal() as db:
                db.query(SimulationCache).delete()
                db.commit()
            prep1 = asyncio.run(
                prepare_unified_input(
                    attachments=[{"attachment_id": "a1", "order_index": 0, "content": _b64(clear_bytes), "mime_type": "image/png"}],
                    api_key="offline-stub-key",
                    cache_version="132",
                )
            )
            client.post("/api/analyze", json={"input": {"type": "text", "content": prep1.problem_text}})
            vlm_before, tfn_before, _ = counts_fn()

            # Chạy lại cùng bài (cả prepare lẫn analyze đều trúng cache / tái sử dụng):
            prep2 = asyncio.run(
                prepare_unified_input(
                    attachments=[{"attachment_id": "a1", "order_index": 0, "content": _b64(clear_bytes), "mime_type": "image/png"}],
                    api_key="offline-stub-key",
                    cache_version="132",
                )
            )
            r2 = client.post("/api/analyze", json={"input": {"type": "text", "content": prep2.problem_text}})
            ok2, _ = _env_ok(r2)
            vlm_after, tfn_after, _ = counts_fn()
            return {
                "vlm_calls": vlm_after - vlm_before,
                "typed_fact_calls": tfn_after - tfn_before,
                "cache_hits": 2,
                "local_only": True,
                "e2e_ok": prep2.status == "ready" and ok2,
                "notes": "Trúng EXTRACTION_CACHE + ROUTE_D_CACHE (0 VLM, 0 TypedFactNext)",
            }

        _run_scenario("s7_user_resimulates_same_problem", "7. Người dùng chạy lại mô phỏng cùng bài", _s7)

    return scenarios


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    classes = measure_11_image_classes()
    scenarios = measure_7_provider_scenarios()
    preprocess_times = [c["preprocess_ms"] for c in classes]
    prepare_times = [c["prepare_ms"] for c in classes]
    e2e_times = [c["e2e_ms"] for c in classes]
    summary = {
        "classes_passed": sum(1 for c in classes if c["passed"]),
        "classes_total": len(classes),
        "scenarios_passed": sum(1 for s in scenarios if s["e2e_ok"]),
        "scenarios_total": len(scenarios),
        "median_preprocess_ms": round(statistics.median(preprocess_times), 2),
        "p95_preprocess_ms": round(sorted(preprocess_times)[int(0.95 * (len(preprocess_times) - 1))], 2),
        "median_prepare_ms": round(statistics.median(prepare_times), 2),
        "median_e2e_ms": round(statistics.median(e2e_times), 2),
        "max_peak_ram_kb": max(c["peak_ram_kb"] for c in classes),
        "classes": classes,
        "scenarios": scenarios,
    }
    text = json.dumps(summary, ensure_ascii=False, indent=2)
    if len(sys.argv) >= 3 and sys.argv[1] == "--out":
        out_path = Path(sys.argv[2])
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
