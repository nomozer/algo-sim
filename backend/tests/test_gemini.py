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


# ── NGÂN SÁCH: đếm VÀ chặn, ở đúng chỗ nó phát sinh ──────────────
# Trước 2026-08-22 quan hệ "call_gemini phải báo cho ApiBudget" KHÔNG có gì
# khoá. Gỡ `budget.note_call()` khỏi `call_gemini` là mọi test vẫn xanh, còn
# trần 440/520 của protocol Task 12 thành đồ trang trí — và nó thành đồ trang
# trí một cách CÂM, đúng lúc lượt chạy duy nhất đang tiêu quota thật.
#
# Phát hiện khi chạy thử `main()` của runner: báo cáo ghi `logic_da_dung: 0`
# trong khi 4 case đã chạy xong.


@pytest.fixture()
def budget_sach():
    b = gemini.ApiBudget()
    gemini.set_budget(b)
    try:
        yield b
    finally:
        gemini.set_budget(None)


def test_moi_luot_goi_deu_bao_cho_ngan_sach(monkeypatch, budget_sach):
    _install(monkeypatch, [_FakeResp(200, OK_BODY)])
    asyncio.run(gemini.call_gemini("k", "sys", "user"))
    assert budget_sach.logical_calls == 1
    assert budget_sach.http_requests == 1


def test_retry_transient_tinh_them_HTTP_nhung_KHONG_them_luot_logic(
    monkeypatch, budget_sach
):
    """Hai trục đo hai thứ khác nhau: một lượt logic có thể tốn nhiều request."""
    _install(monkeypatch, [_FakeResp(503), _FakeResp(200, OK_BODY)])
    asyncio.run(gemini.call_gemini("k", "sys", "user"))
    assert budget_sach.logical_calls == 1
    assert budget_sach.http_requests == 2
    assert budget_sach.retry_requests == 1


def test_cham_tran_LOGIC_thi_chan_TRUOC_khi_post(monkeypatch):
    b = gemini.ApiBudget(max_logical_calls=1)
    gemini.set_budget(b)
    try:
        client = _install(monkeypatch, [_FakeResp(200, OK_BODY)])
        asyncio.run(gemini.call_gemini("k", "sys", "user"))
        with pytest.raises(gemini.BudgetExceeded, match="lượt LLM logic"):
            asyncio.run(gemini.call_gemini("k", "sys", "user"))
        assert client.calls == 1, "đã chạm trần mà vẫn gửi request thật"
        assert b.aborted is True
    finally:
        gemini.set_budget(None)


def test_cham_tran_HTTP_thi_chan(monkeypatch):
    b = gemini.ApiBudget(max_api_calls=1)
    gemini.set_budget(b)
    try:
        _install(monkeypatch, [_FakeResp(200, OK_BODY)])
        asyncio.run(gemini.call_gemini("k", "sys", "user"))
        with pytest.raises(gemini.BudgetExceeded, match="API call"):
            asyncio.run(gemini.call_gemini("k", "sys", "user"))
    finally:
        gemini.set_budget(None)


def test_khong_co_budget_thi_khong_dem_khong_chan(monkeypatch):
    """Production/pytest: `BUDGET=None` ⇒ hành vi không đổi một bit."""
    assert gemini.BUDGET is None
    client = _install(monkeypatch, [_FakeResp(200, OK_BODY)])
    out = asyncio.run(gemini.call_gemini("k", "sys", "user"))
    assert out == "kết quả" and client.calls == 1
