# -*- coding: utf-8 -*-
"""Ngân sách API + suite selection + gap_gate_recall (M7.14T §4, §7, §8-c).

Không mạng: dùng fake httpx client (như test_gemini.py) hoặc mock call_gemini.
"""

import asyncio
import json

import pytest

from app.ai import gemini, pipeline
from app.ai.gemini import ApiBudget, BudgetExceeded
from app.evaluation.dataset import DATASET
from app.evaluation.harness import EvalReport, ItemResult, run_eval, select_suite
from app.evaluation.live import main as live_main


class _Resp:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = ""

    def json(self):
        return self._payload


class _FakeClient:
    """Đếm số POST; trả lần lượt các response đã lên kịch bản."""

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


OK_RESP = _Resp(200, {"candidates": [{"content": {"parts": [{"text": "{}"}]}}]})


@pytest.fixture
def no_sleep(monkeypatch):
    async def instant(_s):
        return None

    monkeypatch.setattr(gemini.asyncio, "sleep", instant)


def _install(monkeypatch, responses) -> _FakeClient:
    client = _FakeClient(responses)
    monkeypatch.setattr(gemini.httpx, "AsyncClient", lambda **kw: client)
    return client


@pytest.fixture(autouse=True)
def clear_budget():
    gemini.set_budget(None)
    yield
    gemini.set_budget(None)


# ── Đếm request ───────────────────────────────────────────────

def test_dem_logical_call_va_http_request(monkeypatch):
    client = _install(monkeypatch, [OK_RESP])
    budget = ApiBudget()
    gemini.set_budget(budget)

    asyncio.run(gemini.call_gemini("k", "sys", "user"))
    asyncio.run(gemini.call_gemini("k", "sys", "user"))

    assert budget.logical_calls == 2
    assert budget.http_requests == 2 == client.calls
    assert budget.retry_requests == 0
    assert budget.transient_hits == 0


def test_retry_transient_duoc_dem_rieng(monkeypatch, no_sleep):
    """1 logical call gặp 503 hai lần rồi 200 → 3 HTTP request, 2 retry, 2 transient."""
    client = _install(monkeypatch, [_Resp(503), _Resp(503), OK_RESP])
    budget = ApiBudget()
    gemini.set_budget(budget)

    asyncio.run(gemini.call_gemini("k", "sys", "user"))

    assert budget.logical_calls == 1
    assert budget.http_requests == 3 == client.calls
    assert budget.retry_requests == 2
    assert budget.transient_hits == 2


def test_max_retries_cat_bot_so_lan_thu(monkeypatch, no_sleep):
    """--max-retries 1 → max_attempts 2: chỉ 2 request rồi báo lỗi, không phải 4."""
    client = _install(monkeypatch, [_Resp(503)])
    gemini.set_budget(ApiBudget(max_attempts=2))

    with pytest.raises(RuntimeError, match="503"):
        asyncio.run(gemini.call_gemini("k", "sys", "user"))
    assert client.calls == 2


def test_cham_tran_api_call_thi_dung_sach(monkeypatch):
    client = _install(monkeypatch, [OK_RESP])
    budget = ApiBudget(max_api_calls=2)
    gemini.set_budget(budget)

    asyncio.run(gemini.call_gemini("k", "s", "u"))
    asyncio.run(gemini.call_gemini("k", "s", "u"))
    with pytest.raises(BudgetExceeded, match="chạm trần 2"):
        asyncio.run(gemini.call_gemini("k", "s", "u"))

    assert budget.aborted is True
    assert client.calls == 2  # request thứ 3 KHÔNG được gửi


def test_budget_none_thi_inert(monkeypatch):
    """Production: không có budget → không đếm, không chặn, hành vi cũ nguyên vẹn."""
    client = _install(monkeypatch, [OK_RESP])
    assert gemini.BUDGET is None
    asyncio.run(gemini.call_gemini("k", "s", "u"))
    assert client.calls == 1


# ── run_eval dừng khi vượt trần ───────────────────────────────

def test_run_eval_abort_khi_vuot_tran(monkeypatch):
    """Chạm trần giữa chừng → dừng cả bộ, report ghi aborted_reason + vẫn in được."""

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2, image=None):
        raise BudgetExceeded("Đã chạm trần 5 API call — dừng để không đốt thêm quota.")

    monkeypatch.setattr(pipeline, "call_gemini", fake)
    items = select_suite("smoke")[:3]
    report = asyncio.run(run_eval(items, "k"))

    assert report.aborted_reason is not None
    assert report.results == []  # dừng ngay item đầu
    assert report.planned == 3


# ── Suite selection ───────────────────────────────────────────

def test_suite_smoke_va_full():
    full = select_suite("full")
    smoke = select_suite("smoke")
    boundary = select_suite("boundary")

    assert len(full) == len(DATASET) == 30
    assert [i.id for i in smoke] == [
        "a-and", "a-packet", "a-sumif", "d-webstatic", "d-webbuild", "d-tridrag",
        "c-threshold", "c-geo-complex",
    ]
    assert set(i.id for i in smoke) <= set(i.id for i in full)
    assert set(i.id for i in boundary) == {"c-threshold", "c-orbit", "c-freealgo", "c-geo-complex"}
    # tags KHÔNG đổi phân nhóm benchmark
    groups = {}
    for it in full:
        groups[it.group] = groups.get(it.group, 0) + 1
    assert groups == {"specialized": 10, "generic": 13, "unsupported": 7}


# ── gap_gate_recall: metric SONG SONG, không đụng metric cũ ────

def test_gap_gate_recall_doc_lap_voi_metric_cu():
    """§8 phương án (c): gate thật (representation plan) được đo riêng; các
    metric cũ (unsupported_recall...) giữ nguyên cách tính từ classify."""
    report = EvalReport(planned=3)
    report.results = [
        # unsupported: classify từ chối ĐÚNG nhưng gate KHÔNG nổ (analyze không gắn role)
        ItemResult("c-x", "unsupported", None, True, gap_gate_fired=False),
        # unsupported: gate nổ đúng
        ItemResult("c-geo", "unsupported", None, True, gap_gate_fired=True),
        # supported: gate KHÔNG được nổ oan
        ItemResult("a-sumif", "specialized", "algorithm.sum_if", True,
                   spec_valid=True, gap_gate_fired=False),
    ]
    m = report.metrics()
    assert m["unsupported_recall"] == 1.0       # metric cũ: classify từ chối cả hai
    assert m["gap_gate_recall"] == 0.5          # metric mới: chỉ 1/2 do gate bắt
    assert m["gap_gate_false_positives"] == []


def test_gap_gate_false_positive_bi_bao():
    report = EvalReport(planned=1)
    report.results = [
        ItemResult("a-sumif", "specialized", "algorithm.sum_if", True,
                   spec_valid=True, gap_gate_fired=True),  # gate nổ OAN
    ]
    assert report.metrics()["gap_gate_false_positives"] == ["a-sumif"]


# ── Opt-in cứng của live.py ───────────────────────────────────

def test_live_khong_co_opt_in_thi_abort(monkeypatch, capsys):
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)

    async def boom(*a, **k):
        raise AssertionError("live.py KHÔNG được gọi API khi thiếu ALLOW_LIVE_AI=1")

    monkeypatch.setattr(pipeline, "call_gemini", boom)
    code = live_main(["--suite", "smoke"])

    assert code == 1
    out = capsys.readouterr().out
    assert "TỪ CHỐI" in out and "ALLOW_LIVE_AI=1" in out
