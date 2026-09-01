# -*- coding: utf-8 -*-
"""Hard guard offline (M7.14T §5) — CHỨNG MINH pytest = 0 real API call.

Cơ chế (conftest.py): autouse fixture patch TRANSPORT MẠNG THẬT của httpx →
mọi request thật raise "Real Gemini API call blocked during offline tests.".
Hệ quả: toàn bộ suite xanh ⇔ không test nào chạm mạng. Các test dưới đây là
CANARY: nếu ai đó vô hiệu hóa guard, chúng đỏ ngay.
"""

import asyncio
import os

import pytest

from app.ai import gemini, pipeline
from conftest import BLOCK_MESSAGE


def test_key_that_bi_go_khoi_moi_truong():
    """backend/.env được load_dotenv nạp lúc import db.py → key THẬT nằm trong
    os.environ suốt phiên pytest. Guard phải gỡ nó: test quên mock cũng không
    có gì để xác thực."""
    assert os.getenv("GEMINI_API_KEY") is None


def test_call_gemini_that_bi_chan_truoc_khi_ra_mang():
    """Gọi thẳng call_gemini (không mock) → chết ở biên mạng, KHÔNG có request."""
    with pytest.raises(RuntimeError, match=BLOCK_MESSAGE):
        asyncio.run(gemini.call_gemini("khoa-that-gia", "sys", "user"))


def test_pipeline_quen_mock_cung_bi_chan():
    """Kịch bản thật sự nguy hiểm: một test mới quên monkeypatch call_gemini.
    Guard phải nổ TRƯỚC network, không âm thầm đốt quota."""
    with pytest.raises(RuntimeError, match=BLOCK_MESSAGE):
        # Phải là đề HÌNH HỌC: `run_pipeline` từ chối mọi miền khác TRƯỚC khi
        # chạm biên mạng, nên một đề trung tính không bao giờ tới chỗ guard —
        # test sẽ xanh vì lý do sai (không có call nào, vì không có gì gọi).
        asyncio.run(pipeline.run_pipeline(
            "Cho hình chóp S.ABCD, tính khoảng cách từ A đến mặt phẳng (SBD).",
            "khoa-gia"))


def test_explain_cung_di_qua_cung_bien_mang():
    """`explain` có binding `call_gemini` RIÊNG (`from … import`) — guard ở BIÊN
    MẠNG che nó, không phụ thuộc test nào nhớ mock.

    `edit` từng được kiểm cùng ở đây; module ấy đã gỡ cùng `/api/edit`
    (`LEGACY_INFORMATICS_REMOVAL`) — nó chỉ phục vụ `generic.rule_scene`.
    """
    from app.ai import explain as explain_module

    with pytest.raises(RuntimeError, match=BLOCK_MESSAGE):
        asyncio.run(explain_module.explain_state(
            "generic.semantic_program", {}, "Vì sao?", [], "k"))


def test_guard_khong_chan_asgi_testclient():
    """TestClient của FastAPI chạy in-process (ASGITransport) — guard chỉ chặn
    transport MẠNG THẬT nên endpoint test vẫn chạy bình thường."""
    from fastapi.testclient import TestClient

    from app.main import app

    res = TestClient(app).get("/api/health")
    assert res.status_code == 200
    assert res.json()["hasKey"] is False  # key đã bị gỡ
