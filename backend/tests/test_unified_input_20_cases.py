# -*- coding: utf-8 -*-
"""Kiểm thử toàn diện tuyến chuẩn bị đầu vào thống nhất (§9–§18, §20–§21).

Không ghi đè hoặc sửa bất kỳ tệp bằng chứng đông cứng nào trên ổ đĩa.
Mọi kiểm thử chạy hoàn toàn OFFLINE (0 lượt gọi Gemini thật).
"""

from __future__ import annotations

import asyncio
import base64
import io
import sys
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "backend" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from app.ingestion.document_reader import (  # noqa: E402
    DOCX_MIME,
    PDF_MIME,
    InputPrepareRejected,
    extract_docx_structured,
    merge_supplemental_text,
    omml_to_text,
    parse_user_composer_instruction,
    sniff_input_file_kind,
)
from app.ingestion.image import normalize_image  # noqa: E402
from app.ingestion.region_detector import detect_problem_regions  # noqa: E402
from app.main import app  # noqa: E402
from evaluate_unified_input_corpus import run_20_case_evaluation  # noqa: E402
from tests.route_client import sign_in  # noqa: E402

CORPUS_DIR = ROOT / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene" / "corpus"


def test_twenty_case_ground_truth_corpus_passes_without_data_or_diagram_loss() -> None:
    """Bộ 20 mẫu ground-truth độc lập phải đạt 20/20, không mất hình vẽ hay dữ kiện toán học."""
    report = asyncio.run(run_20_case_evaluation())
    failed = [c["case_id"] for c in report["cases"] if not c["passed"]]
    assert report["total_cases"] == 20
    assert report["passed_cases"] == 20, f"Các mẫu chưa đạt: {failed}"
    assert report["all_passed"] is True

    metrics = report["metrics"]
    assert metrics["region_detection_accuracy"] == 1.0
    assert metrics["min_region_containment_recall"] >= 0.99
    assert metrics["wrong_problem_selection_count"] == 0
    assert metrics["diagram_loss_count"] == 0
    assert metrics["math_fact_loss_count"] == 0
    assert metrics["zero_vlm_rate_structured_docs"] == 1.0
    assert metrics["avg_vlm_calls_structured_pdf_docx"] == 0.0


def test_sniff_input_file_kind_enforces_magic_bytes_and_safety_guards() -> None:
    """Kiểm magic bytes thật, từ chối HEIC, tệp giả đuôi, .doc cũ, macro VBA và zip-bomb."""
    png_bytes = (CORPUS_DIR / "c01_ro_chop_thiet_dien.png").read_bytes()
    kind, mime = sniff_input_file_kind(png_bytes, filename="de.png", declared_mime="image/png")
    assert (kind, mime) == ("image", "image/png")

    with pytest.raises(InputPrepareRejected) as exc_mismatch:
        sniff_input_file_kind(png_bytes, filename="de.pdf", declared_mime=PDF_MIME)
    assert exc_mismatch.value.code == "FILE_TYPE_MISMATCH"

    heic_header = b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00heicmif1"
    with pytest.raises(InputPrepareRejected) as exc_heic:
        sniff_input_file_kind(heic_header, filename="anh_iphone.heic", declared_mime="image/heic")
    assert exc_heic.value.code == "UNSUPPORTED_HEIC_FORMAT"

    legacy_doc = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 64
    with pytest.raises(InputPrepareRejected) as exc_doc:
        sniff_input_file_kind(legacy_doc, filename="de_cu.doc", declared_mime="application/msword")
    assert exc_doc.value.code == "LEGACY_DOC_UNSUPPORTED"

    macro_buf = io.BytesIO()
    with zipfile.ZipFile(macro_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("word/document.xml", "<document/>")
        zf.writestr("word/vbaProject.bin", b"VBA")
    with pytest.raises(InputPrepareRejected) as exc_macro:
        sniff_input_file_kind(macro_buf.getvalue(), filename="de.docx", declared_mime=DOCX_MIME)
    assert exc_macro.value.code == "DOCX_MACROS_FORBIDDEN"

    bomb_buf = io.BytesIO()
    with zipfile.ZipFile(bomb_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("word/document.xml", b"0" * (3 * 1024 * 1024))
    with pytest.raises(InputPrepareRejected) as exc_bomb:
        sniff_input_file_kind(bomb_buf.getvalue(), filename="bomb.docx", declared_mime=DOCX_MIME)
    assert exc_bomb.value.code == "ATTACHMENT_ZIP_BOMB"


def test_omml_formula_and_docx_external_relationship_safety() -> None:
    """Chuyển đổi OMML giữ nguyên căn thức, phân số, chỉ số trên/dưới, dấu phẩy đỉnh và bỏ qua liên kết ngoài."""
    xml = (
        '<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">'
        "<m:sSup><m:e><m:r><m:t>A'</m:t></m:r></m:e><m:sup><m:r><m:t>2</m:t></m:r></m:sup></m:sSup>"
        "<m:r><m:t>=</m:t></m:r>"
        "<m:f><m:num><m:rad><m:deg/><m:e><m:r><m:t>3</m:t></m:r></m:e></m:rad><m:r><m:t>a</m:t></m:r></m:num>"
        "<m:den><m:r><m:t>2</m:t></m:r></m:den></m:f>"
        "</m:oMath>"
    )
    elem = etree.fromstring(xml.encode("utf-8"))
    rendered = omml_to_text(elem)
    assert "√3" in rendered or "√(3)" in rendered
    assert "/2" in rendered or "/ 2" in rendered
    assert "A'" in rendered

    docx_buf = io.BytesIO()
    with zipfile.ZipFile(docx_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
        )
        zf.writestr(
            "word/_rels/document.xml.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rExt" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
            'Target="https://example.invalid/tracker.png" TargetMode="External"/>'
            "</Relationships>",
        )
        zf.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>Cho hình chóp S.ABC có đáy ABC đều cạnh a = 2.</w:t></w:r></w:p></w:body>"
            "</w:document>",
        )
    res = extract_docx_structured(docx_buf.getvalue())
    assert "Cho hình chóp S.ABC" in res.full_text
    assert len(res.embedded_figures) == 0


def test_region_detector_preserves_wireframe_geometry_and_full_image_baseline() -> None:
    """Ảnh chỉ có hình không gian không bị xoay nghiêng sai; full_image luôn là ảnh chuẩn hoá gốc."""
    wireframe_norm = normalize_image((CORPUS_DIR / "c11_chi_co_hinh.png").read_bytes(), "image/png")
    rep_wire = detect_problem_regions(wireframe_norm)
    assert rep_wire.skew_angle_deg == 0.0
    assert rep_wire.deskew_applied is False
    assert len(rep_wire.candidates) == 1
    assert rep_wire.candidates[0].has_figure is True
    assert (rep_wire.full_image.width, rep_wire.full_image.height) == (wireframe_norm.width, wireframe_norm.height)

    low_norm = normalize_image((CORPUS_DIR / "c06_toi_mo_elip_non.jpg").read_bytes(), "image/jpeg")
    rep_low = detect_problem_regions(low_norm)
    assert rep_low.quality.enhanced_low_light is True
    assert len(rep_low.candidates) == 1


def test_composer_directive_and_supplemental_fact_merging() -> None:
    """Tách đúng chỉ dẫn chọn bài/trang và ghép dữ kiện bổ sung tường minh mà không bịa thêm."""
    d_sel = parse_user_composer_instruction("Dựng bài số 2 ở trang 3 trong file giúp em")
    assert d_sel.target_problem_number == 2
    assert d_sel.target_page == 3

    d_sup = parse_user_composer_instruction("Hình vẽ nằm trong file, dữ kiện bổ sung là SA = 4")
    assert "SA = 4" in d_sup.supplemental_text
    merged = merge_supplemental_text("Cho hình chóp S.ABCD có đáy hình vuông cạnh 2.", d_sup)
    assert "Cho hình chóp S.ABCD" in merged
    assert "Biết SA = 4." in merged


def test_input_prepare_endpoint_requires_session_and_rejects_invalid_format() -> None:
    """POST /api/input/prepare yêu cầu phiên hợp lệ (401 khi thiếu) và từ chối định dạng giả mạo."""
    png_b64 = base64.b64encode((CORPUS_DIR / "c01_ro_chop_thiet_dien.png").read_bytes()).decode("ascii")
    with TestClient(app) as anon_client:
        unauth = anon_client.post(
            "/api/input/prepare",
            json={"content": png_b64, "mime_type": "image/png", "filename": "c01.png"},
        )
        assert unauth.status_code == 401
        assert unauth.json().get("reason_code") == "session_required"

    with TestClient(app) as authed_client:
        sign_in(authed_client)
        bad = authed_client.post(
            "/api/input/prepare",
            json={
                "content": base64.b64encode(b"not-a-valid-file").decode("ascii"),
                "mime_type": "application/pdf",
                "filename": "x.pdf",
            },
        )
        assert bad.status_code == 400
        body = bad.json()
        assert body["reason_code"] == "UNSUPPORTED_FILE_TYPE"
