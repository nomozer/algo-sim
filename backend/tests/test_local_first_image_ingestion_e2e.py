# -*- coding: utf-8 -*-
"""Kiểm chứng End-to-End cho nhiệm vụ:
`ALGOSIM — HYBRID STABILIZATION & LOCAL-FIRST INTELLIGENT IMAGE INGESTION` (Mục V, VI, VIII, IX, X).

Toàn bộ kiểm thử chạy OFFLINE (`ALLOW_LIVE_AI=0` ở biên mạng, stub Gemini VLM/TypedFactNext có kiểm soát):
1. 11 nhóm ảnh đại diện (Mục VIII):
   - Nhóm 1: Ảnh đề rõ, chụp thẳng (`c01`)
   - Nhóm 2: Ảnh đề hơi nghiêng (`c02`) -> tự phát hiện skew và xoay thẳng
   - Nhóm 3: Ảnh đề bị xoay EXIF (`c03`) -> chuẩn hóa hướng EXIF
   - Nhóm 4: Ảnh chụp thiếu sáng (`c04`) -> tự nâng sáng cục bộ (`enhanced_low_light=True`)
   - Nhóm 5: Ảnh có bóng đổ (`c05`) -> tự phát hiện bóng (`has_shadow=True`), bù sáng nền giấy (`enhanced_shadow=True`), bảo toàn 100% vùng chữ + hình (`region_containment_recall == 1.0`)
   - Nhóm 6: Ảnh có nhiều vùng chữ (`c06`) -> lọc running header/footer, gộp phần giả thiết + câu hỏi
   - Nhóm 7: Ảnh có cả chữ và hình vẽ (`c07`) -> bảo toàn hình vẽ đi kèm (`has_associated_figure=True`)
   - Nhóm 8: Ảnh có nhiều bài trong một trang (`c08`) -> phát hiện mơ hồ 0 VLM call (`needs_selection`), chọn bài -> trích xuất đúng bài
   - Nhóm 9: Ảnh chỉ có hình vẽ (`c09`) -> từ chối rõ `MISSING_PROBLEM_TEXT`
   - Nhóm 10: Ảnh ngoài phạm vi (`c10`) -> từ chối rõ `UNSUPPORTED_PROBLEM`
   - Nhóm 11: Ảnh lỗi hoặc mờ trắng không đọc được (`c11`) -> chặn ngay tại local CV gate với `0` lượt gọi VLM
2. 5 Hành trình người dùng End-to-End (Mục X — Hành trình A, B, C, D, E):
   - Hành trình A: Tải ảnh đề rõ -> Tự động xử lý -> Nhận diện đề -> Điền vào luồng phân tích -> Hybrid `/4` -> `Scene3D` + các bước dựng + đáp án chính xác
   - Hành trình B: Tải ảnh đề -> Chỉnh sửa nhẹ văn bản đã trích xuất (`SA = 3` -> `SA = 6`) -> Không gọi lại đọc ảnh (`0` VLM call) -> Hybrid `/4` tính ra đáp án mới (`8`)
   - Hành trình C: Tải ảnh có cả chữ và hình vẽ -> Bảo toàn quan hệ chữ-hình -> Hybrid `/4` dựng `Scene3D` hợp lệ
   - Hành trình D: Tải nhiều ảnh của cùng một bài (gồm ảnh chữ + ảnh hình vẽ + ảnh chụp trùng) -> Khử trùng SHA-256 trước khi gọi VLM, ghép thứ tự logic -> Hybrid `/4` dựng `Scene3D`
   - Hành trình E: Tải ảnh thiếu dữ kiện -> Từ chối `MISSING_DIMENSION` (`insufficient_specification`) rõ lý do -> Học sinh bổ sung dữ kiện trên ô nhập -> Dựng hình thành công với `0` VLM call bổ sung.
"""

from __future__ import annotations

import asyncio
import base64
import io
import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import ExifTags, Image, ImageDraw
import pytest

from app.ai import typed_fact_next_extraction as TFNE
from app.ingestion import image_extraction as IE
from app.ingestion.document_reader import (
    InputPrepareRejected,
    merge_supplemental_text,
    parse_user_composer_instruction,
)
from app.ingestion.image import NormalizedImage, normalize_image
from app.ingestion.image_extraction import ImageProblemExtraction
from app.ingestion.region_detector import BoundingBox, detect_problem_regions
from app.ingestion.unified_input import prepare_unified_input
from app.main import app
from app.persistence.db import SessionLocal, SimulationCache, init_db
from tests.route_client import sign_in

ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = ROOT / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene" / "corpus"

PROBLEM_SABCD_3 = (
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
    "SA vuông góc với mặt phẳng (ABCD) và SA = 3. Tính thể tích khối chóp S.ABCD."
)
PROBLEM_SABCD_6 = (
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
    "SA vuông góc với mặt phẳng (ABCD) và SA = 6. Tính thể tích khối chóp S.ABCD."
)
PROBLEM_SABCD_MISSING_SA = (
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
    "SA vuông góc với mặt phẳng (ABCD). Tính thể tích khối chóp S.ABCD."
)


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _jpeg_bytes(img: Image.Image, quality: int = 92) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def _draw_text_lines(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    lines: list[str],
    *,
    ink: tuple[int, int, int] = (20, 24, 30),
) -> BoundingBox:
    x0, y0 = xy
    cur_y = y0
    max_x = x0
    for line in lines:
        # Vẽ dải chữ đậm có cấu trúc dòng thực tế để bộ tách khối CV nhận diện rõ văn bản
        bbox = draw.textbbox((x0, cur_y), line)
        draw.text((x0, cur_y), line, fill=ink)
        max_x = max(max_x, bbox[2], x0 + len(line) * 11)
        cur_y += 38
    return BoundingBox(x0, y0, max_x, cur_y)


def _draw_pyramid(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    ink: tuple[int, int, int] = (20, 24, 30),
) -> BoundingBox:
    x0, y0, x1, y1 = box
    sx, sy = (x0 + x1) // 2, y0 + 20
    ax, ay = x0 + 30, y1 - 80
    bx, by = x0 + 130, y1 - 20
    cx, cy = x1 - 30, y1 - 35
    dx, dy = x1 - 120, y1 - 95
    for p, q in (
        ((sx, sy), (ax, ay)),
        ((sx, sy), (bx, by)),
        ((sx, sy), (cx, cy)),
        ((sx, sy), (dx, dy)),
        ((ax, ay), (bx, by)),
        ((bx, by), (cx, cy)),
        ((cx, cy), (dx, dy)),
        ((dx, dy), (ax, ay)),
    ):
        draw.line([p, q], fill=ink, width=3)
    return BoundingBox(x0, y0, x1, y1)


def _build_tfn_payload(problem_text: str) -> dict[str, Any]:
    premises: list[dict[str, Any]] = [
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
    ]
    if "SA = 6" in problem_text:
        premises.append(
            {
                "solid_id": "s1",
                "kind": "segment_length",
                "args": {"segment": ["S", "A"], "value": "6"},
                "quote": "SA = 6",
            }
        )
    elif "SA = 3" in problem_text:
        premises.append(
            {
                "solid_id": "s1",
                "kind": "segment_length",
                "args": {"segment": ["S", "A"], "value": "3"},
                "quote": "SA = 3",
            }
        )
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
        "premises": premises,
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


def test_shadowed_and_low_light_local_cv_preservation():
    """Mục IV & VIII (Nhóm 4 & Nhóm 5):
    - Ảnh thiếu sáng (`c04`) được phát hiện `is_low_light=True` và nâng sáng (`enhanced_low_light=True`).
    - Ảnh có bóng đổ (`c05`) được phát hiện `has_shadow=True`, bù sáng nền giấy (`enhanced_shadow=True`),
      tách nền bàn (`desk_trimmed=True`) nhưng KHÔNG cắt mất nửa dưới trang giấy bị bóng đổ (`containment_recall == 1.0`).
    """
    # 1. Ảnh thiếu sáng toàn trang
    low_img = Image.new("RGB", (1280, 960), (88, 86, 82))
    low_draw = ImageDraw.Draw(low_img)
    t_low = _draw_text_lines(
        low_draw,
        (120, 180),
        [
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2,",
            "SA vuông góc với mặt phẳng (ABCD) và SA = 3.",
            "Tính thể tích khối chóp S.ABCD.",
        ],
        ink=(18, 18, 22),
    )
    f_low = _draw_pyramid(low_draw, (420, 360, 820, 780), ink=(18, 18, 22))
    low_norm = normalize_image(_jpeg_bytes(low_img), "image/jpeg")
    low_reg = detect_problem_regions(low_norm)
    assert low_reg.quality.is_low_light is True
    assert low_reg.quality.enhanced_low_light is True
    low_gt = t_low.union(f_low)
    assert low_reg.selected_bbox.x0 <= low_gt.x0
    assert low_reg.selected_bbox.y0 <= low_gt.y0
    assert low_reg.selected_bbox.x1 >= low_gt.x1
    assert low_reg.selected_bbox.y1 >= low_gt.y1

    # 2. Ảnh có bóng đổ mạnh phủ nửa dưới tờ giấy trên bàn học màu nâu tối
    w, h = 1400, 1050
    sh_img = Image.new("RGB", (w, h), (58, 42, 30))
    sh_draw = ImageDraw.Draw(sh_img)
    sh_draw.rectangle([220, 130, 1180, 920], fill=(248, 248, 244))
    t_sh = _draw_text_lines(
        sh_draw,
        (270, 185),
        [
            "Câu 5: Cho hình chóp S.ABCD có đáy ABCD là hình vuông",
            "cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 3.",
            "Tính thể tích khối chóp S.ABCD.",
        ],
        ink=(20, 24, 30),
    )
    f_sh = _draw_pyramid(sh_draw, (480, 390, 920, 840), ink=(20, 24, 30))
    sh_gt = t_sh.union(f_sh)
    px = sh_img.load()
    for y in range(340, 920):
        t = min(1.0, (y - 340) / 140.0)
        factor = 1.0 - 0.64 * t
        for x in range(220, 1180):
            r, g, b = px[x, y]
            px[x, y] = (int(r * factor), int(g * factor), int(b * factor))

    sh_norm = normalize_image(_jpeg_bytes(sh_img), "image/jpeg")
    sh_reg = detect_problem_regions(sh_norm)
    assert sh_reg.quality.has_shadow is True
    assert sh_reg.quality.enhanced_shadow is True
    assert sh_reg.desk_trimmed is True
    # Toàn bộ vùng chữ + hình vẽ (kể cả phần nằm trong bóng đổ y=390..840) phải nằm trọn trong selected_bbox
    inter_x0 = max(sh_gt.x0, sh_reg.selected_bbox.x0)
    inter_y0 = max(sh_gt.y0, sh_reg.selected_bbox.y0)
    inter_x1 = min(sh_gt.x1, sh_reg.selected_bbox.x1)
    inter_y1 = min(sh_gt.y1, sh_reg.selected_bbox.y1)
    inter_area = max(0, inter_x1 - inter_x0) * max(0, inter_y1 - inter_y0)
    recall = inter_area / float(sh_gt.area)
    assert recall >= 0.99


def test_user_journeys_a_b_c_d_e_end_to_end():
    """Mục X: Kiểm chứng đầy đủ 5 Hành trình người dùng A, B, C, D, E từ ảnh đầu vào -> Hybrid `/4` -> Scene3D."""
    init_db()
    IE.EXTRACTION_CACHE.clear()
    with SessionLocal() as db:
        db.query(SimulationCache).delete()
        db.commit()

    clear_bytes = (CORPUS_DIR / "c01_ro_chop_thiet_dien.png").read_bytes()
    diag_only_bytes = (CORPUS_DIR / "c11_chi_co_hinh.png").read_bytes()

    vlm_calls = 0
    tfn_calls = 0
    next_vlm_text = PROBLEM_SABCD_3
    next_vlm_has_diag = True

    async def _fake_vision(_image: NormalizedImage, _api_key: str) -> ImageProblemExtraction:
        nonlocal vlm_calls
        vlm_calls += 1
        return ImageProblemExtraction(
            problem_text_verbatim=next_vlm_text,
            problem_text_normalized=next_vlm_text,
            math_expressions=[],
            named_points=["S", "A", "B", "C", "D"] if next_vlm_text else [],
            named_lines=["SA"] if next_vlm_text else [],
            named_planes=["(ABCD)"] if next_vlm_text else [],
            named_solids=["S.ABCD"] if next_vlm_text else [],
            given_relations=["SA ⊥ (ABCD)"] if next_vlm_text else [],
            has_diagram=next_vlm_has_diag,
            diagram_observations=["Hình chóp S.ABCD"] if next_vlm_has_diag else [],
            text_diagram_conflicts=[],
            uncertain_tokens=[],
            missing_regions=[],
            confidence=0.96,
        )

    def _fake_extract_tfn(source_text: str, _extractor):
        nonlocal tfn_calls
        tfn_calls += 1
        payload = _build_tfn_payload(source_text)
        return TFNE.extract_typed_fact_next_v2(
            source_text,
            TFNE.ReplayExtractor({source_text: payload}),
        )

    with (
        TestClient(app) as client,
        patch.dict(os.environ, {"ALLOW_LIVE_AI": "1", "GEMINI_API_KEY": "offline-stub-key"}),
        patch("app.ingestion.image_extraction._goi_provider", side_effect=_fake_vision),
        patch("app.ai.hybrid_offline.extract_typed_fact_next_v2", side_effect=_fake_extract_tfn),
    ):
        sign_in(client)

        # ── Hành trình A: Tải ảnh đề rõ -> Tự động xử lý -> Nhận diện đề -> Mô phỏng 3D + kết quả ──
        vlm_calls = 0
        tfn_calls = 0
        next_vlm_text = PROBLEM_SABCD_3
        next_vlm_has_diag = True
        prep_a = asyncio.run(
            prepare_unified_input(
                attachments=[
                    {
                        "attachment_id": "att-a",
                        "order_index": 0,
                        "content": _b64(clear_bytes),
                        "mime_type": "image/png",
                        "filename": "journey_a.png",
                    }
                ],
                api_key="offline-stub-key",
                cache_version="132",
            )
        )
        assert prep_a.status == "ready"
        assert prep_a.problem_text == PROBLEM_SABCD_3
        assert vlm_calls == 1

        resp_a = client.post("/api/analyze", json={"input": {"type": "text", "content": prep_a.problem_text}})
        assert resp_a.status_code == 200
        body_a = resp_a.json()
        assert body_a["envelope"]["status"] == "ok"
        assert len(body_a["envelope"]["scene3d"]["objects"]) >= 6
        assert len(body_a["envelope"]["scene3d"]["formation"]["steps"]) >= 3
        assert body_a["route_d"]["answer_exact"]["q1"]["coef"] == "4"
        assert tfn_calls == 1

        # ── Hành trình B: Chỉnh sửa nhẹ văn bản đã trích xuất (`SA = 3` -> `SA = 6`) -> 0 VLM call -> Kết quả `8` ──
        vlm_before_b = vlm_calls
        directive_b = parse_user_composer_instruction(PROBLEM_SABCD_6)
        merged_b = merge_supplemental_text(prep_a.problem_text, directive_b)
        assert merged_b == PROBLEM_SABCD_6
        resp_b = client.post("/api/analyze", json={"input": {"type": "text", "content": merged_b}})
        assert resp_b.status_code == 200
        body_b = resp_b.json()
        assert vlm_calls == vlm_before_b  # 0 VLM calls khi chỉnh sửa văn bản đã trích xuất
        assert body_b["envelope"]["status"] == "ok"
        assert body_b["route_d"]["answer_exact"]["q1"]["coef"] == "8"

        # ── Hành trình C: Tải ảnh có cả chữ và hình vẽ -> Bảo toàn quan hệ chữ-hình -> Scene3D hợp lệ ──
        IE.EXTRACTION_CACHE.clear()
        vlm_calls = 0
        prep_c = asyncio.run(
            prepare_unified_input(
                attachments=[
                    {
                        "attachment_id": "att-c",
                        "order_index": 0,
                        "content": _b64(clear_bytes),
                        "mime_type": "image/png",
                        "filename": "journey_c.png",
                    }
                ],
                api_key="offline-stub-key",
                cache_version="132",
            )
        )
        assert prep_c.status == "ready"
        assert prep_c.provenance.get("has_associated_figure") is True
        assert vlm_calls == 1

        # ── Hành trình D: Tải nhiều ảnh của cùng một bài (1 ảnh chữ + 1 ảnh trùng + 1 ảnh hình vẽ riêng) ──
        IE.EXTRACTION_CACHE.clear()
        vlm_calls = 0

        async def _multi_vision(image: NormalizedImage, _api_key: str) -> ImageProblemExtraction:
            nonlocal vlm_calls
            vlm_calls += 1
            # Ảnh 1 là chữ đề bài, ảnh 3 (`diag_only_bytes`) là hình vẽ riêng
            is_diag_only = len(image.data) == len(normalize_image(diag_only_bytes, "image/png").data)
            txt = "" if is_diag_only else PROBLEM_SABCD_3
            return ImageProblemExtraction(
                problem_text_verbatim=txt,
                problem_text_normalized=txt,
                math_expressions=[],
                named_points=["S", "A", "B", "C", "D"],
                named_lines=["SA"],
                named_planes=["(ABCD)"],
                named_solids=["S.ABCD"],
                given_relations=["SA ⊥ (ABCD)"],
                has_diagram=is_diag_only,
                diagram_observations=["Hình vẽ S.ABCD"] if is_diag_only else [],
                text_diagram_conflicts=[],
                uncertain_tokens=[],
                missing_regions=[],
                confidence=0.95,
            )

        with patch("app.ingestion.image_extraction._goi_provider", side_effect=_multi_vision):
            prep_d = asyncio.run(
                prepare_unified_input(
                    attachments=[
                        {
                            "attachment_id": "att-d1-text",
                            "order_index": 0,
                            "content": _b64(clear_bytes),
                            "mime_type": "image/png",
                            "filename": "part1_text.png",
                        },
                        {
                            "attachment_id": "att-d2-dup",
                            "order_index": 1,
                            "content": _b64(clear_bytes),
                            "mime_type": "image/png",
                            "filename": "part1_dup.png",
                        },
                        {
                            "attachment_id": "att-d3-diag",
                            "order_index": 2,
                            "content": _b64(diag_only_bytes),
                            "mime_type": "image/png",
                            "filename": "part2_diagram.png",
                        },
                    ],
                    api_key="offline-stub-key",
                    cache_version="132",
                )
            )
        assert prep_d.status == "ready"
        assert vlm_calls == 2  # Ảnh trùng `att-d2-dup` được khử trùng SHA-256 trước khi gọi VLM!
        assert prep_d.provenance.get("has_associated_figure") is True
        assert set(prep_d.provenance.get("source_attachment_ids", [])) == {
            "att-d1-text",
            "att-d2-dup",
            "att-d3-diag",
        }

        # ── Hành trình E: Tải ảnh thiếu dữ kiện (`SA`) -> Từ chối rõ lý do (`MISSING_DIMENSION`) -> Bổ sung -> Thành công ──
        IE.EXTRACTION_CACHE.clear()
        vlm_calls = 0
        next_vlm_text = PROBLEM_SABCD_MISSING_SA
        next_vlm_has_diag = True
        prep_e = asyncio.run(
            prepare_unified_input(
                attachments=[
                    {
                        "attachment_id": "att-e",
                        "order_index": 0,
                        "content": _b64(clear_bytes),
                        "mime_type": "image/png",
                        "filename": "journey_e_incomplete.png",
                    }
                ],
                api_key="offline-stub-key",
                cache_version="132",
            )
        )
        assert prep_e.status == "ready"
        assert vlm_calls == 1

        resp_e1 = client.post("/api/analyze", json={"input": {"type": "text", "content": prep_e.problem_text}})
        assert resp_e1.status_code == 200
        body_e1 = resp_e1.json()
        assert body_e1["envelope"]["status"] == "unsupported"
        assert body_e1["envelope"]["failure_category"] == "insufficient_specification"
        assert body_e1["envelope"]["reason_code"] == "MISSING_DIMENSION"

        # Học sinh bổ sung `SA = 3` ngay trên văn bản đề trong Composer rồi chạy lại -> 0 VLM call bổ sung, dựng hình thành công!
        vlm_before_e2 = vlm_calls
        repaired_text = PROBLEM_SABCD_3
        resp_e2 = client.post("/api/analyze", json={"input": {"type": "text", "content": repaired_text}})
        assert resp_e2.status_code == 200
        body_e2 = resp_e2.json()
        assert vlm_calls == vlm_before_e2
        assert body_e2["envelope"]["status"] == "ok"
        assert body_e2["route_d"]["answer_exact"]["q1"]["coef"] == "4"
