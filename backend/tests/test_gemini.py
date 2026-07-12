# -*- coding: utf-8 -*-
"""Test retry/backoff transient của call_gemini (M7.6 §2).

Chỉ retry 429/500/502/503/504 với backoff mũ; 4xx khác KHÔNG retry.
Dùng fake httpx client + sleep no-op — không cần mạng.
"""

import asyncio

import pytest

from app.ai import gemini


class _FakeResp:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


class _FakeClient:
    """Trả lần lượt các response đã lên kịch bản; đếm số lần post."""

    def __init__(self, responses):
        self._responses = responses
        self.calls = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, json=None):
        i = min(self.calls, len(self._responses) - 1)
        self.calls += 1
        return self._responses[i]


OK_BODY = {"candidates": [{"content": {"parts": [{"text": "kết quả"}]}}]}


async def _noop_sleep(*_a, **_k):
    return None


def _install(monkeypatch, responses):
    client = _FakeClient(responses)
    monkeypatch.setattr(gemini.httpx, "AsyncClient", lambda **kw: client)
    monkeypatch.setattr(gemini.asyncio, "sleep", _noop_sleep)
    return client


def test_transient_roi_thanh_cong(monkeypatch):
    client = _install(monkeypatch, [_FakeResp(503, text="quá tải"), _FakeResp(200, OK_BODY)])
    out = asyncio.run(gemini.call_gemini("k", "sys", "user"))
    assert out == "kết quả"
    assert client.calls == 2  # 1 lần lỗi + 1 lần thành công


def test_4xx_khong_retry(monkeypatch):
    client = _install(monkeypatch, [_FakeResp(400, text="Invalid enum")])
    with pytest.raises(RuntimeError, match="400"):
        asyncio.run(gemini.call_gemini("k", "sys", "user"))
    assert client.calls == 1  # KHÔNG retry lỗi request


def test_transient_het_luot_thi_bao_loi(monkeypatch):
    client = _install(monkeypatch, [_FakeResp(503, text="quá tải")])
    with pytest.raises(RuntimeError, match="503"):
        asyncio.run(gemini.call_gemini("k", "sys", "user"))
    assert client.calls == gemini.MAX_ATTEMPTS  # thử đủ MAX_ATTEMPTS rồi bỏ


def test_429_duoc_retry(monkeypatch):
    client = _install(monkeypatch, [_FakeResp(429), _FakeResp(429), _FakeResp(200, OK_BODY)])
    out = asyncio.run(gemini.call_gemini("k", "sys", "user", response_schema={"type": "OBJECT"}))
    assert out == "kết quả"
    assert client.calls == 3


def test_backoff_tang_dan(monkeypatch):
    """Backoff mũ 1s → 2s → 4s (kiểm thứ tự các khoảng chờ)."""
    delays: list[float] = []

    async def fake_sleep(d):
        delays.append(d)

    client = _FakeClient([_FakeResp(500), _FakeResp(500), _FakeResp(500), _FakeResp(200, OK_BODY)])
    monkeypatch.setattr(gemini.httpx, "AsyncClient", lambda **kw: client)
    monkeypatch.setattr(gemini.asyncio, "sleep", fake_sleep)
    out = asyncio.run(gemini.call_gemini("k", "sys", "user"))
    assert out == "kết quả"
    assert delays == [1.0, 2.0, 4.0]
