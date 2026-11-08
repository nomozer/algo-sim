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


def test_13_reversed_upload_order_semantic_and_overlap_reordering() -> None:
    """(Situation F) Sắp xếp lại các ảnh thuộc cùng 1 bài khi người dùng chụp/tải ngược thứ tự (§6.F):
    - 13A: `order_index=0` là câu hỏi kết thúc, `order_index=1` là giả thiết trung gian, `order_index=2` là câu mở đầu khối hình.
    - 13B: 2 ảnh cùng vai trò ngữ nghĩa nhưng chụp chồng lấn ngược chiều (`order_index=0` nối sau `order_index=1`).
    """
    img_q = _make_distinct_image_b64(131)
    img_mid = _make_distinct_image_b64(132)
    img_open = _make_distinct_image_b64(133)

    shas_q = _prepared_sha(img_q)
    shas_mid = _prepared_sha(img_mid)

    async def _fake_vlm_reversed(img: NormalizedImage, api_key: str, cache_version: str | None = None) -> ExtractionResult:
        if img.sha256 in shas_q:
            return _make_extraction_result(
                "Tính thể tích khối chóp S.ABCD và khoảng cách từ A đến mặt phẳng (SBC)."
            )
        if img.sha256 in shas_mid:
            return _make_extraction_result(
                "Gọi M là trung điểm của SC, biết SA = a√3."
            )
        return _make_extraction_result(
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng (ABCD)."
        )

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_fake_vlm_reversed):
        out_rev = asyncio.run(
            prepare_unified_input(
                attachments=[
                    {"attachment_id": "img-q", "order_index": 0, "content": img_q},
                    {"attachment_id": "img-mid", "order_index": 1, "content": img_mid},
                    {"attachment_id": "img-open", "order_index": 2, "content": img_open},
                ],
                api_key="fake-key",
            )
        )
        assert out_rev.status == "ready"
        assert out_rev.provenance["semantic_reordered"] is True
        assert out_rev.provenance["upload_order_attachment_ids"] == ["img-q", "img-mid", "img-open"]
        assert out_rev.provenance["source_attachment_ids"] == ["img-open", "img-mid", "img-q"]
        assert out_rev.problem_text.startswith("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a")
        assert "Gọi M là trung điểm của SC" in out_rev.problem_text
        assert out_rev.problem_text.endswith("Tính thể tích khối chóp S.ABCD và khoảng cách từ A đến mặt phẳng (SBC).")

    # 13B: Chồng lấn biên ngược chiều giữa 2 mảnh cùng mở đầu bằng "Cho hình chóp S.ABCD":
    img_ov_tail = _make_distinct_image_b64(134)
    img_ov_head = _make_distinct_image_b64(135)
    shas_tail = _prepared_sha(img_ov_tail)

    async def _fake_vlm_overlap_rev(img: NormalizedImage, api_key: str, cache_version: str | None = None) -> ExtractionResult:
        if img.sha256 in shas_tail:
            return _make_extraction_result(
                "SA vuông góc với mặt phẳng (ABCD) và SA = 2a.\nTính thể tích khối chóp S.ABCD."
            )
        return _make_extraction_result(
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a.\nSA vuông góc với mặt phẳng (ABCD) và SA = 2a."
        )

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_fake_vlm_overlap_rev):
        out_ov = asyncio.run(
            prepare_unified_input(
                attachments=[
                    {"attachment_id": "ov-tail", "order_index": 0, "content": img_ov_tail},
                    {"attachment_id": "ov-head", "order_index": 1, "content": img_ov_head},
                ],
                api_key="fake-key",
            )
        )
        assert out_ov.status == "ready"
        assert out_ov.provenance["semantic_reordered"] is True
        assert out_ov.provenance["deduplicated_overlap"] is True
        assert out_ov.problem_text.count("SA vuông góc với mặt phẳng (ABCD) và SA = 2a.") == 1
        assert out_ov.problem_text.startswith("Cho hình chóp S.ABCD")
        assert out_ov.problem_text.endswith("Tính thể tích khối chóp S.ABCD.")


def test_14_single_image_multiple_problems_preserves_source_bbox() -> None:
    """(Situation G) 1 ảnh có nhiều bài bảo toàn cả `source_attachment_ids` lẫn `source_bbox` cho từng candidate (§6.G)."""
    from app.ingestion.document_reader import decode_attachment_base64
    from app.ingestion.image import normalize_image
    from app.ingestion.region_detector import (
        BoundingBox,
        CandidateProblemRegion,
        ImageQualityReport,
        RegionDetectionResult,
    )

    img_b64 = _make_distinct_image_b64(141)
    norm_img = normalize_image(decode_attachment_base64(img_b64), "image/png")

    fake_reg = RegionDetectionResult(
        full_image=norm_img,
        prepared_image=norm_img,
        quality=ImageQualityReport(
            mean_luma=245.0,
            p5_luma=30,
            p95_luma=252,
            dynamic_range=222,
            edge_energy=18.5,
            is_low_light=False,
            is_blank_or_unreadable=False,
            enhanced_low_light=False,
        ),
        page_bbox=BoundingBox(0, 0, norm_img.width, norm_img.height),
        desk_trimmed=False,
        skew_angle_deg=0.0,
        deskew_applied=False,
        blocks=(),
        candidates=(
            CandidateProblemRegion(
                region_id="region-1",
                index=0,
                label="Bài 1 (nửa trên trang)",
                bbox=BoundingBox(20, 20, 600, 180),
                normalized_bbox=(0.0312, 0.0476, 0.9062, 0.3810),
                has_figure=True,
                text_block_count=1,
                figure_block_count=1,
                completeness_confidence=0.95,
                preview_data_url="data:image/jpeg;base64,AA==",
            ),
            CandidateProblemRegion(
                region_id="region-2",
                index=1,
                label="Bài 2 (nửa dưới trang)",
                bbox=BoundingBox(20, 210, 600, 390),
                normalized_bbox=(0.0312, 0.5000, 0.9062, 0.4286),
                has_figure=False,
                text_block_count=1,
                figure_block_count=0,
                completeness_confidence=0.95,
                preview_data_url="data:image/jpeg;base64,BB==",
            ),
        ),
        selected_bbox=BoundingBox(0, 0, norm_img.width, norm_img.height),
        used_crop=False,
        used_fallback_full_image=False,
        has_associated_figure=True,
        completeness_confidence=0.95,
        ambiguous_multi_problem=True,
    )

    with patch("app.ingestion.unified_input.detect_problem_regions", return_value=fake_reg):
        out = asyncio.run(
            prepare_unified_input(
                attachments=[
                    {"attachment_id": "sheet-multi", "order_index": 0, "source_type": "camera", "content": img_b64}
                ],
                api_key="fake-key",
            )
        )
        assert out.status == "needs_selection"
        assert len(out.candidates) == 2
        assert out.candidates[0].candidate_id == "region-1"
        assert out.candidates[0].source_attachment_ids == ("sheet-multi",)
        assert out.candidates[0].source_bbox == (0.0312, 0.0476, 0.9062, 0.3810)
        assert out.candidates[1].candidate_id == "region-2"
        assert out.candidates[1].source_attachment_ids == ("sheet-multi",)
        assert out.candidates[1].source_bbox == (0.0312, 0.5000, 0.9062, 0.4286)


def test_15_separate_diagram_entity_linking_and_ambiguous_diagram_flag() -> None:
    """(Situation H) Ảnh hình vẽ riêng đi kèm ảnh đề chữ (§6.H):
    - Đối chiếu nhãn đỉnh, đường thẳng, mặt phẳng và quan sát từ hình vẽ với lời đề trong `provenance["diagram_text_link"]`.
    - Nếu lời đề phụ thuộc hình vẽ ("như hình vẽ") khi đi kèm ảnh hình vẽ rời -> trả `needs_confirmation` (`AMBIGUOUS_DIAGRAM`).
    """
    from app.ingestion.document_reader import decode_attachment_base64
    from app.ingestion.image import normalize_image

    img_text = _make_distinct_image_b64(151)
    img_diag = _make_distinct_image_b64(152, draw_diagram=True)
    shas_text = _prepared_sha(img_text)
    norm_diag = normalize_image(decode_attachment_base64(img_diag), "image/png")

    diag_ext = ExtractionResult(
        raw_extraction=ImageProblemExtraction(
            problem_text_verbatim="",
            problem_text_normalized="",
            math_expressions=[],
            named_points=["S", "A", "B", "C", "D", "H"],
            named_lines=["SA", "SB", "AH"],
            named_planes=["(ABCD)", "(SBC)"],
            named_solids=["S.ABCD"],
            given_relations=["SA vuông góc (ABCD)", "AH vuông góc SB"],
            diagram_observations=["Ký hiệu góc vuông tại A và tại H trên SB", "Cạnh AD và AB vẽ nét đứt"],
            text_diagram_conflicts=[],
            uncertain_tokens=[],
            missing_regions=[],
            has_diagram=True,
            confidence=0.95,
        ),
        image=norm_diag,
        identity={"vision_model_identity": "test-stub"},
        cached=False,
    )

    async def _fake_vlm_aligned(img: NormalizedImage, api_key: str, cache_version: str | None = None) -> ExtractionResult:
        if img.sha256 in shas_text:
            return _make_extraction_result(
                "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với (ABCD). "
                "Gọi H là hình chiếu vuông góc của A trên SB. Tính khoảng cách từ H đến mặt phẳng (SCD)."
            )
        return diag_ext

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_fake_vlm_aligned):
        out = asyncio.run(
            prepare_unified_input(
                attachments=[
                    {"attachment_id": "txt-1", "order_index": 0, "content": img_text},
                    {"attachment_id": "fig-1", "order_index": 1, "content": img_diag},
                ],
                api_key="fake-key",
            )
        )
        assert out.status == "ready"
        link = out.provenance["diagram_text_link"]
        assert link["diagram_named_points"] == ["S", "A", "B", "C", "D", "H"]
        assert link["matched_points_in_text"] == ["S", "A", "B", "C", "D", "H"]
        assert link["unreferenced_diagram_points"] == []
        assert link["diagram_vertex_alignment"] == "aligned"
        assert "Ký hiệu góc vuông tại A và tại H trên SB" in link["diagram_observations"]

    # Khi đề chữ ghi "như hình vẽ" đi kèm ảnh hình vẽ rời -> phải trả `needs_confirmation`:
    async def _fake_vlm_ambig(img: NormalizedImage, api_key: str, cache_version: str | None = None) -> ExtractionResult:
        if img.sha256 in shas_text:
            return _make_extraction_result(
                "Cho hình chóp S.ABCD có đáy ABCD là hình vuông và các kích thước như hình vẽ. "
                "Tính thể tích khối chóp S.ABCD."
            )
        return diag_ext

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_fake_vlm_ambig):
        out_ambig = asyncio.run(
            prepare_unified_input(
                attachments=[
                    {"attachment_id": "txt-1", "order_index": 0, "content": img_text},
                    {"attachment_id": "fig-1", "order_index": 1, "content": img_diag},
                ],
                api_key="fake-key",
            )
        )
        assert out_ambig.status == "needs_confirmation"
        assert any("hình vẽ" in msg for msg in out_ambig.flag_messages)


def test_16_multi_image_to_hybrid_route_d_scene3d_e2e() -> None:
    """(Part C — §7) Kiểm chứng toàn trình từ Multi-Image `prepare_unified_input` -> `TypedFactNext /2` ->
    `Source Gate` -> `Planner /26` -> `Registry /33` -> `Exact Kernel /24` -> `Adapter /4` -> `Scene3D`
    trên 4 họ hình học độc lập (Chóp `S.ABCD`, Lăng trụ đứng `ABC.A'B'C'`, Hình trụ `O.O'`, Mặt cầu `O`).
    """
    from fractions import Fraction as F
    from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route
    from app.simulation.geometry.radical import parse_exact
    from tests.geometry.test_hybrid4_three_point_plane_sections import (
        _payload as _section_payload,
        divide,
        midpoint,
        oracle_section,
        pyramid_edges,
        square_pyramid,
        at,
        mid,
        coef_squared,
    )
    from tests.geometry.test_typed_fact_next_v2_distance_bridge import _prism

    # 1. Bài 1 (Ghép từ 3 ảnh: mở đầu + điểm cắt M, N, P + câu hỏi thiết diện & diện tích chóp S.ABCD):
    solid_pyr, prem_pyr = square_pyramid("S", "ABCD", 2, 4)
    prem_pyr += [
        divide("M", "S", "A", "3/4", "SM = 3MA"),
        divide("N", "S", "B", "3/8", "SN = 3/5 NB"),
        midpoint("P", "S", "C"),
    ]
    pyr_text, pyr_tfn = _section_payload(solid_pyr, prem_pyr, ["M", "N", "P"], area=True)
    # Chia `pyr_text` thành 2 ảnh văn bản + 1 ảnh hình vẽ:
    clauses = pyr_text.split(". ")
    part1_text = ". ".join(clauses[:3]) + "."
    part2_text = ". ".join(clauses[3:])
    img1 = _make_distinct_image_b64(161)
    img2 = _make_distinct_image_b64(162)
    img3 = _make_distinct_image_b64(163, draw_diagram=True)
    s1 = _prepared_sha(img1)
    s2 = _prepared_sha(img2)

    async def _vlm_pyr(img: NormalizedImage, api_key: str, cache_version: str | None = None) -> ExtractionResult:
        if img.sha256 in s1:
            return _make_extraction_result(part1_text)
        if img.sha256 in s2:
            return _make_extraction_result(part2_text)
        return _make_extraction_result("", has_diagram=True)

    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=_vlm_pyr):
        prep_pyr = asyncio.run(
            prepare_unified_input(
                attachments=[
                    {"attachment_id": "pyr-1", "order_index": 0, "content": img1},
                    {"attachment_id": "pyr-2", "order_index": 1, "content": img2},
                    {"attachment_id": "pyr-fig", "order_index": 2, "content": img3},
                ],
                api_key="fake-key",
            )
        )
    assert prep_pyr.status == "ready"
    assert prep_pyr.problem_text.replace("\n", " ") == pyr_text
    pyr_tfn["problem_text"] = prep_pyr.problem_text
    r_pyr = run_typed_fact_next_v2_route(pyr_tfn)
    assert r_pyr.status == "SERVED" and r_pyr.kernel_check is True
    resp_pyr = build_adapter4_response(r_pyr, prep_pyr.problem_text)
    assert resp_pyr["envelope"]["status"] == "ok"
    assert resp_pyr["route_d"]["source_verification"] == {"authority": "registry.kiem_nguon"}
    # Kiểm chứng diện tích thiết diện khớp tuyệt đối với oracle độc lập:
    V_pyr = {"A": (0, 0, 0), "B": (2, 0, 0), "C": (2, 2, 0), "D": (0, 2, 0), "S": (0, 0, 4)}
    plane_pts = (at(V_pyr["S"], V_pyr["A"], F(3, 4)), at(V_pyr["S"], V_pyr["B"], F(3, 8)), mid(V_pyr["S"], V_pyr["C"]))
    expected_pyr = oracle_section(V_pyr, pyramid_edges("S", "ABCD"), plane_pts)
    assert coef_squared(resp_pyr["route_d"]["answer_exact"]["q1"]["coef"]) == expected_pyr["area2"]
    scene_pyr_objs = {o["id"]: o for o in r_pyr.scene3d["objects"]}
    for v_lbl in ("S", "A", "B", "C", "D", "M", "N", "P"):
        assert v_lbl in scene_pyr_objs and scene_pyr_objs[v_lbl]["type"] == "point3"

    # 2. Bài 2 (Lăng trụ đứng `ABC.A'B'C'` vuông tại A, AB=6, AC=8, AA'=12, tính d(A, (BCC'B'))):
    prism_tfn = _prism(
        "ABC",
        6,
        8,
        12,
        ask=("Tính khoảng cách từ A đến mặt phẳng (BCC'B').", {"point": "A", "plane": ["B", "C", "C'"]}),
    )
    r_prism = run_typed_fact_next_v2_route(prism_tfn)
    assert r_prism.status == "SERVED" and r_prism.kernel_check is True
    resp_prism = build_adapter4_response(r_prism, prism_tfn["problem_text"])
    assert resp_prism["envelope"]["status"] == "ok"
    # d(A, (BCC'B')) = (6 * 8) / sqrt(6^2 + 8^2) = 48 / 10 = 24/5
    assert resp_prism["route_d"]["answer_exact"]["q"]["coef"] == "24/5"
    scene_prism_objs = {o["id"]: o for o in r_prism.scene3d["objects"]}
    for v_lbl in ("A", "B", "C", "A_prime", "B_prime", "C_prime"):
        assert v_lbl in scene_prism_objs and scene_prism_objs[v_lbl]["type"] == "point3"

    # 3. Bài 3 (Hình trụ tâm O, O', bán kính 3, chiều cao 5, tính diện tích toàn phần):
    cyl_quote = "Cho hình trụ có tâm hai đáy là O và O', điểm A thuộc đường tròn đáy tâm O, bán kính đáy bằng 3 và chiều cao bằng 5"
    cyl_q = "Tính diện tích toàn phần của hình trụ"
    cyl_tfn = {
        "schema_version": "typed-fact-next/2",
        "problem_text": f"{cyl_quote}. {cyl_q}.",
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "k",
                "solid_type": "cylinder",
                "notation": "O.O'",
                "center": "O",
                "apex_or_top": "O'",
                "rim_point": "A",
                "radius": "3",
                "height": "5",
                "quote": cyl_quote,
            }
        ],
        "premises": [],
        "derived_sections": [],
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "k", "quote": cyl_quote}],
        "math_goals": [{"goal_id": "mg1", "kind": "measurement", "goal_type": "area", "target": {"solid": "O.O'"}, "quote": cyl_q}],
    }
    r_cyl = run_typed_fact_next_v2_route(cyl_tfn)
    assert r_cyl.status == "SERVED" and r_cyl.kernel_check is True
    resp_cyl = build_adapter4_response(r_cyl, cyl_tfn["problem_text"])
    assert resp_cyl["envelope"]["status"] == "ok"
    # S_tp = 2*pi*3*5 + 2*pi*3^2 = 30pi + 18pi = 48pi
    assert parse_exact(resp_cyl["route_d"]["answer_exact"]["mg1"]["coef"]) == parse_exact("48π")

    # 4. Bài 4 (Mặt cầu tâm O, điểm A thuộc mặt cầu, bán kính 3, tính thể tích khối cầu):
    sph_quote = "Cho mặt cầu tâm O, điểm A thuộc mặt cầu, bán kính bằng 3"
    sph_q = "Tính thể tích khối cầu"
    sph_tfn = {
        "schema_version": "typed-fact-next/2",
        "problem_text": f"{sph_quote}. {sph_q}.",
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "k",
                "solid_type": "sphere",
                "notation": "O",
                "center": "O",
                "rim_point": "A",
                "radius": "3",
                "quote": sph_quote,
            }
        ],
        "premises": [],
        "derived_sections": [],
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "k", "quote": sph_quote}],
        "math_goals": [{"goal_id": "mg1", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "k"}, "quote": sph_q}],
    }
    r_sph = run_typed_fact_next_v2_route(sph_tfn)
    assert r_sph.status == "SERVED" and r_sph.kernel_check is True
    resp_sph = build_adapter4_response(r_sph, sph_tfn["problem_text"])
    assert resp_sph["envelope"]["status"] == "ok"
    # V = (4/3)*pi*3^3 = 36pi
    assert parse_exact(resp_sph["route_d"]["answer_exact"]["mg1"]["coef"]) == parse_exact("36π")

