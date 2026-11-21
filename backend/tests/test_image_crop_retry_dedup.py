"""Crop → full-image Vision retry must not repeat a call that cannot see anything new.

`_process_normalized_visual_page` retries Vision ONCE on the full page when the crop reading reports
`missing_regions` / `MISSING_PROBLEM_TEXT`. When the crop already holds every non-noise ink block of the
page, the full page only adds blank margin: the second call reads the same content (previous run receipt:
`class_09_diagram_only` spent 2 Vision calls). `IMAGE_NOT_READABLE` keeps its retry (different pixels).
Offline: Vision is a mock; 0 network calls.
"""

from __future__ import annotations

import asyncio
import base64
from contextlib import ExitStack
from dataclasses import replace
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from app.ingestion.image import NormalizedImage, normalize_image
from app.ingestion.image_extraction import ExtractionResult, ImageProblemExtraction
from app.ingestion.region_detector import detect_problem_regions
from app.ingestion.unified_input import prepare_unified_input

CORPUS = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene" / "corpus"
PROBLEM = (
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD) "
    "và SA = 3. Tính thể tích khối chóp S.ABCD."
)


def _x(text: str, *, has_diagram: bool, missing: list[str] | None = None,
       confidence: float = 0.95) -> ImageProblemExtraction:
    return ImageProblemExtraction(
        problem_text_verbatim=text, problem_text_normalized=text, math_expressions=[], named_points=[],
        named_lines=[], named_planes=[], named_solids=[], given_relations=[], has_diagram=has_diagram,
        diagram_observations=[], text_diagram_conflicts=[], uncertain_tokens=[], missing_regions=missing or [],
        confidence=confidence,
    )


def _run(raw: bytes, reply, *, region=None):
    calls: list[str] = []

    async def fake(img: NormalizedImage, api_key: str, cache_version: str | None = None) -> ExtractionResult:
        calls.append(img.sha256)
        return ExtractionResult(reply(img, len(calls)), img, {"vision_model_identity": "test-stub"}, cached=False)

    with ExitStack() as st:
        patched_env = {k: v for k, v in os.environ.items() if k not in ("LOCAL_OCR_PYTHON", "ALLOW_LIVE_AI")}
        st.enter_context(patch.dict(os.environ, patched_env, clear=True))
        st.enter_context(patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=fake))
        if region is not None:
            st.enter_context(patch("app.ingestion.unified_input.detect_problem_regions", return_value=region))
        out = asyncio.run(prepare_unified_input(content=base64.b64encode(raw).decode(), api_key="k"))
    return out, calls


def test_diagram_only_crop_holding_all_ink_spends_one_vision_call() -> None:
    raw = (CORPUS / "c11_chi_co_hinh.png").read_bytes()
    reg = detect_problem_regions(normalize_image(raw))
    assert reg.used_crop and reg.prepared_image.sha256 != reg.full_image.sha256
    assert reg.crop_holds_all_content is True

    out, calls = _run(raw, lambda img, n: _x("", has_diagram=True))
    assert out.status == "rejected" and out.reason_code == "MISSING_PROBLEM_TEXT"
    assert len(calls) == 1 and out.metrics["vlm_calls"] == 1
    assert out.provenance["used_fallback_full_image"] is False


def test_missing_regions_on_complete_crop_does_not_retry() -> None:
    raw = (CORPUS / "c01_ro_chop_thiet_dien.png").read_bytes()
    reg = detect_problem_regions(normalize_image(raw))
    assert reg.used_crop and reg.crop_holds_all_content is True
    out, calls = _run(raw, lambda img, n: _x(PROBLEM, has_diagram=False, missing=["mép phải"]))
    assert len(calls) == 1
    assert out.status == "needs_confirmation"  # the missing-region flag still reaches the learner


@pytest.mark.parametrize("holds_all", [False, True])
def test_retry_kept_when_content_lies_outside_crop_or_crop_unreadable(holds_all: bool) -> None:
    raw = (CORPUS / "c11_chi_co_hinh.png").read_bytes()
    reg = replace(detect_problem_regions(normalize_image(raw)), crop_holds_all_content=holds_all)
    if holds_all:
        # Crop unreadable (IMAGE_NOT_READABLE) ⇒ the full page is different pixels: one retry stays allowed.
        def reply(img, n):
            return _x(PROBLEM, has_diagram=True, confidence=0.1 if n == 1 else 0.95)
    else:
        def reply(img, n):
            return _x("" if n == 1 else PROBLEM, has_diagram=True)
    out, calls = _run(raw, reply, region=reg)
    assert len(calls) == 2 and calls[0] == reg.prepared_image.sha256 and calls[1] == reg.full_image.sha256
    assert out.metrics["vlm_calls"] == 2


def test_region_detector_flags_text_left_outside_the_crop() -> None:
    """A running header kept out of the problem cluster is content the crop does not hold."""
    from PIL import Image, ImageDraw, ImageFont
    import io

    # Pillow's bundled font (no OS font path): the detector only sees ink layout, not language.
    img = Image.new("RGB", (1200, 1600), (252, 252, 250))
    d = ImageDraw.Draw(img)
    d.text((300, 40), "CHUONG III - THE TICH KHOI DA DIEN", font=ImageFont.load_default(size=20), fill=(90, 90, 95))
    for i, s in enumerate(["Vi du 4: Cho hinh lang tru dung ABC.A'B'C' co day ABC",
                           "la tam giac vuong can tai A, AB = 4 va canh ben AA' = 6.",
                           "Tinh the tich khoi lang tru ABC.A'B'C'."]):
        d.text((110, 420 + 44 * i), s, font=ImageFont.load_default(size=26), fill=(20, 20, 24))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    reg = detect_problem_regions(normalize_image(buf.getvalue()))
    assert reg.used_crop and not reg.desk_trimmed  # the header is excluded from the cluster, so the page is cropped
    assert reg.crop_holds_all_content is False


def test_multi_image_duplicate_and_diagram_only_spend_one_call_each_distinct_image() -> None:
    """Journey: same problem photographed twice + a diagram-only photo ⇒ 2 Vision calls (dedup + no retry)."""
    text_raw = (CORPUS / "c01_ro_chop_thiet_dien.png").read_bytes()
    diag_raw = (CORPUS / "c11_chi_co_hinh.png").read_bytes()
    n = normalize_image(diag_raw)
    r = detect_problem_regions(n)
    diag_shas = {n.sha256, r.prepared_image.sha256, r.full_image.sha256}
    calls: list[str] = []

    async def fake(img: NormalizedImage, api_key: str, cache_version: str | None = None) -> ExtractionResult:
        calls.append(img.sha256)
        x = _x("", has_diagram=True) if img.sha256 in diag_shas else _x(PROBLEM, has_diagram=False)
        return ExtractionResult(x, img, {"vision_model_identity": "test-stub"}, cached=False)

    att = [{"attachment_id": aid, "order_index": i, "content": base64.b64encode(raw).decode()}
           for i, (aid, raw) in enumerate((("a1", text_raw), ("a2", text_raw), ("d1", diag_raw)))]
    with patch("app.ingestion.unified_input.extract_problem_from_image", side_effect=fake):
        out = asyncio.run(prepare_unified_input(attachments=att, api_key="k"))
    assert len(calls) == 2 and out.metrics["vlm_calls"] == 2
    assert out.provenance["deduplicated_attachment_ids"] == ["a2"]
    assert out.provenance["source_attachment_ids"] == ["a1", "a2", "d1"]
    assert out.problem_text.startswith(PROBLEM)

def test_faint_secondary_block_missed_by_layout_detector_triggers_full_image_retry() -> None:
    """When a faint secondary line (contrast < 20 gray levels after 640px downscale) is missed by
    `_segment_layout_blocks`, a tiny crop (`area_ratio < 0.25`) must NOT vacuously claim `crop_holds_all_content`,
    and `prepare_unified_input` must retry the full page to recover the missed mathematical fact."""
    from PIL import Image, ImageDraw, ImageFont
    import io

    primary_line = "Cau 1. Cho hinh chop S.ABCD co day ABCD la hinh vuong canh 2, SA vuong goc voi mat phang day."
    faint_line = "Biet SA = 3. Tinh the tich khoi chop S.ABCD."
    img = Image.new("RGB", (1200, 1600), (248, 248, 248))
    d = ImageDraw.Draw(img)
    d.text((100, 140), primary_line[:52], font=ImageFont.load_default(size=26), fill=(20, 20, 24))
    d.text((100, 180), primary_line[52:], font=ImageFont.load_default(size=26), fill=(20, 20, 24))
    # Faint secondary annotation (gray=233 on 248 background => contrast 15 < 20 adaptive threshold)
    d.text((100, 360), faint_line, font=ImageFont.load_default(size=22), fill=(233, 233, 233))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()

    reg = detect_problem_regions(normalize_image(raw))
    assert reg.used_crop and not reg.desk_trimmed
    assert all(b.bbox.y1 < 300 for b in reg.blocks) and reg.selected_bbox.y1 < 320
    assert reg.crop_holds_all_content is False

    def reply(img_norm: NormalizedImage, n: int) -> ImageProblemExtraction:
        if n == 1:
            return _x(primary_line, has_diagram=False, missing=["Dong gia thiet SA = 3 va cau hoi o phia duoi bi cat"])
        return _x(PROBLEM, has_diagram=False)

    out, calls = _run(raw, reply)
    assert len(calls) == 2 and calls[0] == reg.prepared_image.sha256 and calls[1] == reg.full_image.sha256
    assert out.metrics["vlm_calls"] == 2
    assert out.provenance["used_fallback_full_image"] is True
    assert out.status == "ready"
    assert "SA = 3" in out.problem_text


def test_missing_regions_on_tight_crop_retries_even_if_holds_all_forced_true() -> None:
    """Defense-in-depth in `unified_input`: if Vision reports non-empty `missing_regions` on a tight crop
    (`crop_area_ratio < 0.35`), full-image retry fires even if `crop_holds_all_content` were True."""
    from app.ingestion.region_detector import BoundingBox

    raw = (CORPUS / "c01_ro_chop_thiet_dien.png").read_bytes()
    base_reg = detect_problem_regions(normalize_image(raw))
    tight_box = BoundingBox(x0=20, y0=40, x1=420, y1=180)  # area = 400*140 = 56,000 / 537,600 = 0.1042 < 0.35
    reg = replace(base_reg, selected_bbox=tight_box, crop_holds_all_content=True)

    def reply(img_norm: NormalizedImage, n: int) -> ImageProblemExtraction:
        if n == 1:
            return _x("Cho hinh chop S.ABCD co day la hinh vuong canh 2.", has_diagram=False, missing=["Thieu phan cuoi"])
        return _x(PROBLEM, has_diagram=False)

    out, calls = _run(raw, reply, region=reg)
    assert len(calls) == 2 and out.metrics["vlm_calls"] == 2
    assert out.provenance["used_fallback_full_image"] is True
    assert out.status == "ready"
    assert "SA = 3" in out.problem_text


def test_faint_secondary_line_outside_large_crop_area_above_035_still_triggers_retry() -> None:
    """Section V: Even when the main problem crop covers > 35% of the page (`area_ratio >= 0.35`),
    a faint secondary line (`contrast < 20`) outside the crop is detected by `_has_faint_ink_outside_bbox`,
    keeping `crop_holds_all_content = False` so `need_full_retry` recovers the missed line."""
    from PIL import Image, ImageDraw, ImageFont
    import io

    img = Image.new("RGB", (1200, 1600), (248, 248, 248))
    d = ImageDraw.Draw(img)
    for i in range(14):
        d.text(
            (80, 120 + i * 48),
            "Cho hinh chop S.ABCD co day ABCD la hinh vuong canh 2, SA vuong goc day.",
            font=ImageFont.load_default(size=26),
            fill=(20, 20, 24),
        )
    d.text((80, 980), "Biet SA = 3. Tinh the tich khoi chop S.ABCD.", font=ImageFont.load_default(size=22), fill=(233, 233, 233))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()

    reg = detect_problem_regions(normalize_image(raw))
    area_ratio = reg.selected_bbox.area / float(reg.full_image.width * reg.full_image.height)
    assert reg.used_crop and area_ratio >= 0.35
    assert reg.crop_holds_all_content is False

    def reply(img_norm: NormalizedImage, n: int) -> ImageProblemExtraction:
        if n == 1:
            return _x(
                "Cho hinh chop S.ABCD co day ABCD la hinh vuong canh 2, SA vuong goc day.",
                has_diagram=False,
                missing=["Dong cuoi bi mo"],
            )
        return _x(PROBLEM, has_diagram=False)

    out, calls = _run(raw, reply)
    assert len(calls) == 2
    assert out.provenance["used_fallback_full_image"] is True
    assert out.status == "ready"
    assert "SA = 3" in out.problem_text


def test_fallback_disagreement_preserves_readable_crop_when_full_image_rejected() -> None:
    """Section V: When crop extraction has readable problem text (with `missing_regions`) and the
    full-image fallback fails (`IMAGE_NOT_READABLE`), the readable crop text is preserved with
    `status == "needs_confirmation"` and `fallback_disagreement == True`."""
    from app.ingestion.region_detector import BoundingBox

    raw = (CORPUS / "c01_ro_chop_thiet_dien.png").read_bytes()
    base_reg = detect_problem_regions(normalize_image(raw))
    tight_box = BoundingBox(x0=20, y0=40, x1=420, y1=180)
    reg = replace(base_reg, selected_bbox=tight_box, crop_holds_all_content=False)

    def reply(img_norm: NormalizedImage, n: int) -> ImageProblemExtraction:
        if n == 1:
            return _x(PROBLEM, has_diagram=False, missing=["Mep duoi"])
        return _x("", has_diagram=False, confidence=0.1)

    out, calls = _run(raw, reply, region=reg)
    assert len(calls) == 2
    assert out.status == "needs_confirmation"
    assert out.provenance.get("fallback_disagreement") is True
    assert out.problem_text == PROBLEM


def test_fallback_disagreement_flags_conflicting_measurement_between_crop_and_full_image() -> None:
    """Section V: When crop reads `SA = 5` (with `missing_regions`) and full-image retry reads `SA = 3`
    with high confidence and no `missing_regions`, `fallback_disagreement` forces `needs_confirmation`."""
    from app.ingestion.region_detector import BoundingBox

    raw = (CORPUS / "c01_ro_chop_thiet_dien.png").read_bytes()
    base_reg = detect_problem_regions(normalize_image(raw))
    tight_box = BoundingBox(x0=20, y0=40, x1=420, y1=180)
    reg = replace(base_reg, selected_bbox=tight_box, crop_holds_all_content=False)

    crop_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD) "
        "và SA = 5. Tính thể tích khối chóp S.ABCD."
    )

    def reply(img_norm: NormalizedImage, n: int) -> ImageProblemExtraction:
        if n == 1:
            return _x(crop_text, has_diagram=False, missing=["Cần kiểm tra dòng cuối"])
        return _x(PROBLEM, has_diagram=False, confidence=0.96)

    out, calls = _run(raw, reply, region=reg)
    assert len(calls) == 2
    assert out.status == "needs_confirmation"
    assert out.provenance.get("fallback_disagreement") is True
    assert out.provenance.get("crop_problem_text") == crop_text
