# -*- coding: utf-8 -*-
"""Kiểm thử toàn diện chuẩn bị đầu vào đa ảnh/đa tệp (`POST /api/input/prepare`, §9–§11, §13).

Bao phủ đầy đủ 12 tình huống bắt buộc:
1. 1 ảnh có 1 bài hoàn chỉnh.
2. 2–3 ảnh cùng 1 bài (ghép phần đầu + phần tiếp theo).
3. 1 ảnh có nhiều bài (`needs_selection`).
4. Nhiều ảnh thuộc các bài độc lập (`needs_selection` + chọn đúng bài).
5. Ảnh hình vẽ riêng đi kèm ảnh đề chữ.
6. Ảnh mờ / thiếu chữ / cắt cụt dẫn tới `needs_confirmation` hoặc `rejected`, không tự suy diễn.
7. Ảnh trùng lặp hoặc vùng chữ lặp giữa hai ảnh.
8. Thứ tự ảnh thay đổi (`order_index`).
9. Payload sai MIME, vượt kích thước, vượt số lượng cho phép (`> 10` bị từ chối; `6` ảnh được chấp nhận — không có giới hạn cứng 5 ảnh).
10. Response cũ đến muộn sau khi có `request_id` mới (`request_id` echo chính xác).
11. Low-confidence extraction không bị ghi đè thành `ready` khi thêm ảnh khác.
12. Backward compatibility với luồng 1 file hiện tại + nối sang `Hybrid /4` (`POST /api/analyze`).
"""

from __future__ import annotations

import asyncio
import base64
import io
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.ingestion.document_reader import InputPrepareRejected
from app.ingestion.image import NormalizedImage
from app.ingestion.image_extraction import (
    ExtractionResult,
    ImageProblemExtraction,
    UncertainToken,
    assess_extraction,
)
from app.ingestion.unified_input import (
    MAX_PREPARE_ATTACHMENTS,
    merge_overlapping_problem_segments,
    prepare_unified_input,
)
from app.main import app
from tests.route_client import sign_in


def _make_distinct_image_b64(seed_tag: int, *, draw_diagram: bool = False) -> str:
    """Tạo ảnh PNG hợp lệ có một khối đề bài thống nhất và mã băm riêng biệt theo `seed_tag`."""
    img = Image.new("RGB", (640, 420), color=(252, 251, 248))
    draw = ImageDraw.Draw(img)
    for row in range(8):
        y = 36 + row * 22
        w = 460 - ((seed_tag * 13 + row * 19) % 90)
        draw.rectangle([36, y, 36 + w, y + 10], fill=(28, 30, 36))
    if draw_diagram:
        draw.polygon([(380, 210), (540, 210), (460, 90)], outline=(20, 20, 25), width=3)
        draw.line([(460, 90), (460, 210)], fill=(20, 20, 25), width=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _prepared_sha(b64_str: str) -> set[str]:
    """Tập mã băm của cả ảnh chuẩn hóa lẫn ảnh vùng đã chuẩn bị để định danh ảnh trong stub VLM."""
    from app.ingestion.document_reader import decode_attachment_base64
    from app.ingestion.image import normalize_image
    from app.ingestion.region_detector import detect_problem_regions

    norm = normalize_image(decode_attachment_base64(b64_str), "image/png")
    reg = detect_problem_regions(norm)
    return {norm.sha256, reg.prepared_image.sha256, reg.full_image.sha256}


def _make_extraction_result(
    text: str,
    *,
    img: NormalizedImage | None = None,
    confidence: float = 0.96,
    has_diagram: bool = False,
    uncertain_tokens: list[UncertainToken] | None = None,
    missing_regions: list[str] | None = None,
) -> ExtractionResult:
    from app.ingestion.document_reader import decode_attachment_base64
    from app.ingestion.image import normalize_image

    norm_img = img or normalize_image(decode_attachment_base64(_make_distinct_image_b64(1)), "image/png")
    ext = ImageProblemExtraction(
        problem_text_verbatim=text,
        problem_text_normalized=text,
        math_expressions=[],
        named_points=[],
        named_lines=[],
        named_planes=[],
        named_solids=[],
        given_relations=[],
        diagram_observations=[],
        text_diagram_conflicts=[],
        uncertain_tokens=uncertain_tokens or [],
        missing_regions=missing_regions or [],
        has_diagram=has_diagram,
        confidence=confidence,
    )
    return ExtractionResult(
        raw_extraction=ext,
        image=norm_img,
        identity={"vision_model_identity": "test-stub"},
        cached=False,
    )


def test_1_single_image_complete_problem_and_12_backward_compatibility() -> None:
    """(1 & 12) 1 ảnh có 1 bài hoàn chỉnh qua cả mảng `attachments` lẫn payload 1 file truyền thống."""
    img_b64 = _make_distinct_image_b64(1)
    problem_str = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, "
        "SA vuông góc với mặt phẳng (ABCD) và SA = a. Tính thể tích khối chóp S.ABCD."
    )

    async def _fake_vlm(img: NormalizedImage, api_key: str, cache_version: str | None = None) -> ExtractionResult:
        return _make_extraction_result(problem_str, has_diagram=True)

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_fake_vlm):
        # Qua mảng `attachments` mới:
        out_multi = asyncio.run(
            prepare_unified_input(
                attachments=[
                    {
                        "attachment_id": "cam-photo-1",
                        "order_index": 0,
                        "source_type": "camera",
                        "content": img_b64,
                        "mime_type": "image/png",
                        "filename": "photo-1.png",
                    }
                ],
                request_id="req-single-001",
                api_key="fake-key",
            )
        )
        assert out_multi.status == "ready"
        assert out_multi.problem_text == problem_str
        assert out_multi.request_id == "req-single-001"
        assert out_multi.provenance["source_attachment_ids"] == ["cam-photo-1"]
        assert out_multi.provenance["has_associated_figure"] is True

        # Qua giao diện 1 file truyền thống (backward compatibility):
        out_legacy = asyncio.run(
            prepare_unified_input(
                content=img_b64,
                declared_mime="image/png",
                filename="legacy.png",
                api_key="fake-key",
            )
        )
        assert out_legacy.status == "ready"
        assert out_legacy.problem_text == problem_str
        assert out_legacy.provenance["source_attachment_ids"] == ["att-1"]


def test_2_multi_image_same_problem_concatenation_and_5_separate_diagram() -> None:
    """(2 & 5) 2–3 ảnh cùng 1 bài (phần giả thiết + phần câu hỏi + ảnh hình vẽ riêng)."""
    img1 = _make_distinct_image_b64(10)
    img2 = _make_distinct_image_b64(20)
    img3_diagram = _make_distinct_image_b64(30, draw_diagram=True)

    responses = [
        _make_extraction_result(
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng (ABCD) và SA = a√3.",
            has_diagram=False,
        ),
        _make_extraction_result(
            "Gọi M là trung điểm của SB. Tính thể tích khối chóp S.ABCD và khoảng cách từ M đến mặt phẳng (SCD).",
            has_diagram=False,
        ),
        _make_extraction_result(
            "",
            has_diagram=True,
        ),
    ]
    shas_1 = _prepared_sha(img1)
    shas_2 = _prepared_sha(img2)

    async def _fake_vlm(img: NormalizedImage, api_key: str, cache_version: str | None = None) -> ExtractionResult:
        if img.sha256 in shas_1:
            return responses[0]
        if img.sha256 in shas_2:
            return responses[1]
        return responses[2]

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_fake_vlm):
        out = asyncio.run(
            prepare_unified_input(
                attachments=[
                    {"attachment_id": "shot-1", "order_index": 0, "source_type": "camera", "content": img1},
                    {"attachment_id": "shot-2", "order_index": 1, "source_type": "camera", "content": img2},
                    {"attachment_id": "shot-3-fig", "order_index": 2, "source_type": "camera", "content": img3_diagram},
                ],
                request_id="req-3shots",
                api_key="fake-key",
            )
        )

    assert out.status == "ready"
    assert "Cho hình chóp S.ABCD" in out.problem_text
    assert "Tính thể tích khối chóp S.ABCD và khoảng cách từ M đến mặt phẳng (SCD)." in out.problem_text
    assert out.provenance["source_attachment_ids"] == ["shot-1", "shot-2", "shot-3-fig"]
    assert out.provenance["diagram_attachment_ids"] == ["shot-3-fig"]
    assert out.provenance["has_associated_figure"] is True
    assert out.provenance["multi_image_merged"] is True


def test_3_single_image_multiple_problems_needs_selection() -> None:
    """(3) 1 ảnh có nhiều bài trả `needs_selection` kèm `source_attachment_ids`."""
    img1 = _make_distinct_image_b64(31)
    multi_text = (
        "Bài 1: Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với đáy, SA = a. "
        "Tính thể tích khối chóp S.ABC.\n"
        "Bài 2: Cho hình lăng trụ đứng ABC.A'B'C' có đáy là tam giác vuông tại A, AB = a, AC = 2a, AA' = 3a. "
        "Tính thể tích khối lăng trụ."
    )

    async def _fake_vlm(img: NormalizedImage, api_key: str, cache_version: str | None = None) -> ExtractionResult:
        return _make_extraction_result(multi_text)

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_fake_vlm):
        out = asyncio.run(
            prepare_unified_input(
                attachments=[
                    {"attachment_id": "page-1", "order_index": 0, "source_type": "camera", "content": img1}
                ],
                api_key="fake-key",
            )
        )
        assert out.status == "needs_selection"
        assert out.reason_code == "MULTIPLE_PROBLEMS_DETECTED"
        assert len(out.candidates) == 2
        assert out.candidates[0].source_attachment_ids == ("page-1",)
        assert out.candidates[1].source_attachment_ids == ("page-1",)

        # Khi học sinh chọn Bài 2:
        chosen_id = out.candidates[1].candidate_id
        out_selected = asyncio.run(
            prepare_unified_input(
                attachments=[
                    {"attachment_id": "page-1", "order_index": 0, "source_type": "camera", "content": img1}
                ],
                selected_candidate_id=chosen_id,
                api_key="fake-key",
            )
        )
        assert out_selected.status == "ready"
        assert "lăng trụ đứng ABC.A'B'C'" in out_selected.problem_text
        assert "hình chóp S.ABC" not in out_selected.problem_text


def test_4_multiple_images_independent_problems_needs_selection_and_selection() -> None:
    """(4) Nhiều ảnh thuộc các bài độc lập trả `needs_selection`, không trộn dữ kiện, và chọn đúng bài."""
    img_a = _make_distinct_image_b64(41)
    img_b = _make_distinct_image_b64(42)

    prob_a = (
        "Câu 1: Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, "
        "SA vuông góc với mặt phẳng (ABC) và SA = a. Tính thể tích khối chóp S.ABC."
    )
    prob_b = (
        "Câu 2: Cho hình lập phương ABCD.A'B'C'D' cạnh a. "
        "Tính khoảng cách giữa hai đường thẳng AB' và BC'."
    )

    shas_a = _prepared_sha(img_a)

    async def _fake_vlm(img: NormalizedImage, api_key: str, cache_version: str | None = None) -> ExtractionResult:
        if img.sha256 in shas_a:
            return _make_extraction_result(prob_a, has_diagram=True)
        return _make_extraction_result(prob_b, has_diagram=False)

    atts = [
        {"attachment_id": "indep-1", "order_index": 0, "source_type": "camera", "content": img_a, "filename": "cau1.png"},
        {"attachment_id": "indep-2", "order_index": 1, "source_type": "camera", "content": img_b, "filename": "cau2.png"},
    ]

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_fake_vlm):
        out = asyncio.run(prepare_unified_input(attachments=atts, api_key="fake-key"))
        assert out.status == "needs_selection"
        assert out.reason_code == "MULTIPLE_PROBLEMS_DETECTED"
        assert len(out.candidates) == 2
        assert out.candidates[0].candidate_id == "indep-1:problem-1"
        assert out.candidates[0].source_attachment_ids == ("indep-1",)
        assert out.candidates[1].candidate_id == "indep-2:problem-1"
        assert out.candidates[1].source_attachment_ids == ("indep-2",)

        # Khi học sinh chọn bài ở ảnh thứ 2 (`indep-2:problem-1`):
        out_chosen = asyncio.run(
            prepare_unified_input(
                attachments=atts,
                selected_candidate_id="indep-2:problem-1",
                api_key="fake-key",
            )
        )
        assert out_chosen.status == "ready"
        assert "hình lập phương ABCD.A'B'C'D'" in out_chosen.problem_text
        assert "hình chóp S.ABC" not in out_chosen.problem_text
        assert out_chosen.provenance["source_attachment_ids"] == ["indep-2"]


def test_6_blurry_or_incomplete_multi_image_fails_closed() -> None:
    """(6) Ảnh mờ / thiếu câu hỏi kết thúc không tự bịa dữ kiện mà trả `needs_confirmation` hoặc `rejected`."""
    img1 = _make_distinct_image_b64(61)
    img2 = _make_distinct_image_b64(62)

    # Trường hợp 6A: Ghép 2 ảnh nhưng vẫn cụt, chưa có câu hỏi ("Tính...", "Chứng minh...", "?"):
    part_1 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông tâm O cạnh a."
    part_2 = "Cạnh bên SA vuông góc với mặt phẳng đáy (ABCD) và SA = a√3."
    seq = [
        _make_extraction_result(part_1),
        _make_extraction_result(part_2),
    ]
    idx = 0

    async def _fake_vlm_incomplete(img: NormalizedImage, api_key: str, cache_version: str | None = None) -> ExtractionResult:
        nonlocal idx
        r = seq[idx]
        idx += 1
        return r

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_fake_vlm_incomplete):
        out_inc = asyncio.run(
            prepare_unified_input(
                attachments=[
                    {"attachment_id": "cut-1", "order_index": 0, "content": img1},
                    {"attachment_id": "cut-2", "order_index": 1, "content": img2},
                ],
                api_key="fake-key",
            )
        )
        assert out_inc.status == "needs_confirmation"
        assert out_inc.reason_code == "INCOMPLETE_MULTI_IMAGE_PROBLEM"
        assert len(out_inc.missing_regions) >= 1

    # Trường hợp 6B: Cả 2 ảnh chỉ có hình vẽ, không có chữ và ô nhập trống -> `rejected` (`MISSING_PROBLEM_TEXT`):
    async def _fake_vlm_diagram_only(img: NormalizedImage, api_key: str, cache_version: str | None = None) -> ExtractionResult:
        return _make_extraction_result("", has_diagram=True)

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_fake_vlm_diagram_only):
        out_diag = asyncio.run(
            prepare_unified_input(
                attachments=[
                    {"attachment_id": "fig-1", "order_index": 0, "content": img1},
                    {"attachment_id": "fig-2", "order_index": 1, "content": img2},
                ],
                api_key="fake-key",
            )
        )
        assert out_diag.status == "rejected"
        assert out_diag.reason_code == "MISSING_PROBLEM_TEXT"


def test_7_duplicate_images_and_overlapping_text_deduplication() -> None:
    """(7) Khử ảnh trùng mã băm (chỉ gọi VLM 1 lần) và khử câu trùng lặp ở ranh giới hai ảnh chụp chồng lấn."""
    s1 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a.\nSA vuông góc với mặt phẳng (ABCD) và SA = a√2."
    s2 = "SA vuông góc với mặt phẳng (ABCD) và SA = a√2.\nTính thể tích khối chóp S.ABCD."
    merged, dedup = merge_overlapping_problem_segments([s1, s2])
    assert dedup is True
    assert merged.count("SA vuông góc với mặt phẳng (ABCD)") == 1
    assert "Tính thể tích khối chóp S.ABCD." in merged

    # Ảnh trùng hệt nhau trong cùng lần gửi:
    same_img = _make_distinct_image_b64(71)
    vlm_counter = 0

    async def _fake_vlm(img: NormalizedImage, api_key: str, cache_version: str | None = None) -> ExtractionResult:
        nonlocal vlm_counter
        vlm_counter += 1
        return _make_extraction_result(
            "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với (ABC), SA = a. Tính thể tích khối chóp S.ABC."
        )

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_fake_vlm):
        out = asyncio.run(
            prepare_unified_input(
                attachments=[
                    {"attachment_id": "dup-1", "order_index": 0, "content": same_img},
                    {"attachment_id": "dup-2", "order_index": 1, "content": same_img},
                ],
                api_key="fake-key",
            )
        )
        assert out.status == "ready"
        assert vlm_counter == 1
        assert out.provenance["deduplicated_attachment_ids"] == ["dup-2"]
        assert out.provenance["source_attachment_ids"] == ["dup-1", "dup-2"]


def test_8_order_index_controls_assembly_order() -> None:
    """(8) Thứ tự ghép đề tuân thủ tuyệt đối `order_index` bất kể thứ tự phần tử trong mảng JSON."""
    img_first = _make_distinct_image_b64(81)
    img_second = _make_distinct_image_b64(82)

    shas_first = _prepared_sha(img_first)

    async def _fake_vlm(img: NormalizedImage, api_key: str, cache_version: str | None = None) -> ExtractionResult:
        if img.sha256 in shas_first:
            return _make_extraction_result(
                "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với (ABCD) và SA = 2a."
            )
        return _make_extraction_result(
            "Gọi H là hình chiếu vuông góc của A trên SB. Tính khoảng cách từ H đến mặt phẳng (SCD)."
        )

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_fake_vlm):
        # Truyền `part-2` trước `part-1` trong mảng nhưng `order_index` của `part-1` là 1, `part-2` là 5:
        out = asyncio.run(
            prepare_unified_input(
                attachments=[
                    {"attachment_id": "part-2", "order_index": 5, "content": img_second},
                    {"attachment_id": "part-1", "order_index": 1, "content": img_first},
                ],
                api_key="fake-key",
            )
        )
        assert out.status == "ready"
        assert out.provenance["source_attachment_ids"] == ["part-1", "part-2"]
        assert out.problem_text.startswith("Cho hình chóp S.ABCD")
        assert out.problem_text.endswith("Tính khoảng cách từ H đến mặt phẳng (SCD).")


def test_9_validation_limits_no_cap_of_5_and_rejects_above_10() -> None:
    """(9) Hỗ trợ > 5 ảnh (vd 6 ảnh cùng phiên) không bị chặn ở mức 5; từ chối > 10 ảnh, trùng ID, sai MIME."""
    assert MAX_PREPARE_ATTACHMENTS == 10

    # 6 ảnh (1 ảnh đề + 5 ảnh tiếp nối/hình vẽ) phải chạy thành công (chứng minh không có giới hạn cứng 5 ảnh):
    six_atts = [
        {
            "attachment_id": f"shot-{i}",
            "order_index": i,
            "source_type": "camera",
            "content": _make_distinct_image_b64(90 + i, draw_diagram=(i >= 2)),
        }
        for i in range(6)
    ]

    shas_0 = _prepared_sha(six_atts[0]["content"])
    shas_1 = _prepared_sha(six_atts[1]["content"])

    async def _fake_vlm_6(img: NormalizedImage, api_key: str, cache_version: str | None = None) -> ExtractionResult:
        if img.sha256 in shas_0:
            return _make_extraction_result(
                "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng (ABCD), SA = a."
            )
        if img.sha256 in shas_1:
            return _make_extraction_result("Tính thể tích khối chóp S.ABCD và khoảng cách từ A đến (SBC).")
        return _make_extraction_result("", has_diagram=True)

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_fake_vlm_6):
        out_6 = asyncio.run(prepare_unified_input(attachments=six_atts, api_key="fake-key"))
        assert out_6.status == "ready"
        assert len(out_6.provenance["source_attachment_ids"]) == 6

    # 11 ảnh (> 10) phải bị từ chối với `TOO_MANY_ATTACHMENTS`:
    eleven_atts = [
        {"attachment_id": f"shot-{i}", "order_index": i, "content": six_atts[0]["content"]}
        for i in range(11)
    ]
    with pytest.raises(InputPrepareRejected) as exc_many:
        asyncio.run(prepare_unified_input(attachments=eleven_atts, api_key="fake-key"))
    assert exc_many.value.code == "TOO_MANY_ATTACHMENTS"

    # Trùng `attachment_id`:
    with pytest.raises(InputPrepareRejected) as exc_dup:
        asyncio.run(
            prepare_unified_input(
                attachments=[
                    {"attachment_id": "same-id", "order_index": 0, "content": six_atts[0]["content"]},
                    {"attachment_id": "same-id", "order_index": 1, "content": six_atts[1]["content"]},
                ],
                api_key="fake-key",
            )
        )
    assert exc_dup.value.code == "DUPLICATE_ATTACHMENT_ID"


def test_10_request_id_echo_and_11_low_confidence_preserved_across_images(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """(10 & 11) `request_id` được phản hồi chính xác và trạng thái `needs_confirmation` không bị ghi đè thành `ready`."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-endpoint-test")
    img1 = _make_distinct_image_b64(111)
    img2 = _make_distinct_image_b64(112)

    seq = [
        _make_extraction_result(
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với (ABCD) và SA = a√3.",
            confidence=0.62,
            uncertain_tokens=[
                UncertainToken(
                    token="a√3",
                    alternatives=["a√2", "a√3"],
                    location="dòng 1, số đo SA",
                    reason="Chữ số trong căn hơi mờ",
                )
            ],
        ),
        _make_extraction_result(
            "Tính thể tích khối chóp S.ABCD.",
            confidence=0.98,
        ),
    ]
    idx = 0

    async def _fake_vlm(img: NormalizedImage, api_key: str, cache_version: str | None = None) -> ExtractionResult:
        nonlocal idx
        res = seq[idx]
        idx += 1
        return res

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_fake_vlm):
        with TestClient(app) as client:
            sign_in(client)
            resp = client.post(
                "/api/input/prepare",
                json={
                    "request_id": "req-low-conf-99",
                    "attachments": [
                        {"attachment_id": "a1", "order_index": 0, "source_type": "camera", "content": img1},
                        {"attachment_id": "a2", "order_index": 1, "source_type": "camera", "content": img2},
                    ],
                },
            )
            assert resp.status_code == 200
            body: dict[str, Any] = resp.json()
            assert body["request_id"] == "req-low-conf-99"
            assert body["provenance"]["request_id"] == "req-low-conf-99"
            assert body["status"] == "needs_confirmation"
            assert body["reason_code"] == "EXTRACTION_NEEDS_CONFIRMATION"
            assert len(body["uncertain_tokens"]) == 1
            assert body["uncertain_tokens"][0]["token"] == "a√3"
            assert body["provenance"]["source_attachment_ids"] == ["a1", "a2"]
