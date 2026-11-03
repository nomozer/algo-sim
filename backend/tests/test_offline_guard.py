# -*- coding: utf-8 -*-
"""Test cơ chế tự vệ của suite: quên mock Gemini → fail ngay, KHÔNG đi mạng."""

import asyncio

import pytest

from app.ai import function_calling, gemini
from conftest import BLOCK_MESSAGE


def test_quen_mock_call_gemini_bi_chan_tuc_thi():
    """Nếu 1 test vô tình gọi thẳng gemini.call_gemini thật → nổ ngay với hướng dẫn rõ."""
    with pytest.raises(RuntimeError) as exc:
        asyncio.run(gemini.call_gemini("khoa-gia", "transcribe", "noi dung test"))
    assert BLOCK_MESSAGE in str(exc.value)


def test_hybrid_live_transport_quen_mock_cung_bi_chan():
    """Cũng đúng khi đi từ tuyến Hybrid (`function_calling.live_transport`) mà quên mock."""
    send = function_calling.live_transport("khoa-gia", require_allow_live_ai=False)
    with pytest.raises(RuntimeError) as exc:
        send({"contents": []})
    assert BLOCK_MESSAGE in str(exc.value)
