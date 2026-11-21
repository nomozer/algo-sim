"""AXO HYBRID /13 (§6.H): Endpoint-level Model 1 replacement audit under `local-only-scoped` offline isolation."""
from __future__ import annotations

import base64
import io
import zipfile
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient

from app.ai import gemini as gemini_mod
from app.main import app
from tests.route_client import sign_in

PNG_SAMPLE = (
    Path(__file__).resolve().parents[2]
    / "docs/evaluation/geometry/photo-problem-to-scene/corpus/c01_ro_chop_thiet_dien.png"
)

PROBLEM_TEXT_BASE = (
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh {side}. "
    "Cạnh bên SA vuông góc với mặt phẳng đáy và SA = 3. Tính thể tích khối chóp S.ABCD."
)


def _make_docx_bytes(text: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>",
        )
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>",
        )
        zf.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body>"
            "</w:document>",
        )
    return buf.getvalue()


def _make_digital_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_htmlbox(fitz.Rect(40, 40, 550, 300), f"<p style='font-size:14pt'>{text}</p>")
    data = doc.tobytes()
    doc.close()
    return data


def test_model1_replacement_across_text_docx_pdf_and_image_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-only-scoped")
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "")

    async def _forbid_gemini(*_a, **_kw):
        raise AssertionError("Gemini provider must NEVER be called under local-only-scoped audit")

    monkeypatch.setattr(gemini_mod, "call_gemini", _forbid_gemini)

    with TestClient(app) as client:
        sign_in(client)

        # 1. /api/health
        r_health = client.get("/api/health")
        assert r_health.status_code == 200
        hb = r_health.json()
        assert hb["ok"] is True
        assert hb["routeMode"] == "local-only-scoped"
        assert hb["localOnlyMode"] is True
        assert hb["hasKey"] is False

        # 2. Direct Vietnamese text -> /api/analyze (0 cloud calls -> SERVED)
        r_text = client.post(
            "/api/analyze",
            json={"input": {"type": "text", "content": PROBLEM_TEXT_BASE.format(side=2)}},
        )
        assert r_text.status_code == 200, r_text.text
        bt = r_text.json()
        assert bt["route_d"]["status"] == "SERVED"
        assert bt["route_d"]["answers"]["q1"] == "4"
        assert bt["envelope"]["status"] == "ok"

        # 3. Digital DOCX -> /api/input/prepare (0 VLM calls) -> /api/analyze (SERVED)
        docx_b64 = base64.b64encode(_make_docx_bytes(PROBLEM_TEXT_BASE.format(side=4))).decode("ascii")
        r_docx = client.post(
            "/api/input/prepare",
            json={
                "content": docx_b64,
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "filename": "de_chop.docx",
            },
        )
        assert r_docx.status_code == 200, r_docx.text
        bdx = r_docx.json()
        assert bdx["status"] == "ready"
        assert bdx["metrics"]["vlm_calls"] == 0
        r_docx_analyze = client.post(
            "/api/analyze",
            json={"input": {"type": "text", "content": bdx["problem_text"]}},
        )
        assert r_docx_analyze.status_code == 200
        assert r_docx_analyze.json()["route_d"]["status"] == "SERVED"
        assert r_docx_analyze.json()["route_d"]["answers"]["q1"] == "16"

        # 4. Digital PDF -> /api/input/prepare (0 VLM calls) -> /api/analyze (SERVED)
        pdf_b64 = base64.b64encode(_make_digital_pdf_bytes(PROBLEM_TEXT_BASE.format(side=6))).decode("ascii")
        r_pdf = client.post(
            "/api/input/prepare",
            json={"content": pdf_b64, "mime_type": "application/pdf", "filename": "de_chop.pdf"},
        )
        assert r_pdf.status_code == 200, r_pdf.text
        bpdf = r_pdf.json()
        assert bpdf["status"] == "ready"
        assert bpdf["metrics"]["vlm_calls"] == 0
        r_pdf_analyze = client.post(
            "/api/analyze",
            json={"input": {"type": "text", "content": bpdf["problem_text"]}},
        )
        assert r_pdf_analyze.status_code == 200
        assert r_pdf_analyze.json()["route_d"]["status"] == "SERVED"
        assert r_pdf_analyze.json()["route_d"]["answers"]["q1"] == "36"

        # 5. Raster PNG image -> /api/input/prepare & /api/image/extract -> fail-closed 503 LOCAL_ONLY_CLOUD_VISION_DISABLED
        assert PNG_SAMPLE.exists()
        png_b64 = base64.b64encode(PNG_SAMPLE.read_bytes()).decode("ascii")
        r_img_prep = client.post(
            "/api/input/prepare",
            json={"content": png_b64, "mime_type": "image/png", "filename": "de_chop.png"},
        )
        assert r_img_prep.status_code == 503, r_img_prep.text
        assert r_img_prep.headers["cache-control"] == "no-store"
        assert r_img_prep.json()["reason_code"] == "LOCAL_ONLY_CLOUD_VISION_DISABLED"

        r_img_ext = client.post(
            "/api/image/extract",
            json={"content": png_b64, "mime_type": "image/png"},
        )
        assert r_img_ext.status_code == 503, r_img_ext.text
        assert r_img_ext.headers["cache-control"] == "no-store"
        assert r_img_ext.json()["reason_code"] == "LOCAL_ONLY_CLOUD_VISION_DISABLED"
