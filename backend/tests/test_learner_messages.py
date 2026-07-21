# -*- coding: utf-8 -*-
"""M17-Lite W0 — lock learner-facing error mapping (app/learner_messages.py).

Yêu cầu M17: học sinh KHÔNG thấy JSON path, internal id, schema error hay
exception thô — chỉ thấy tiếng Việt thân thiện. Chi tiết kỹ thuật vẫn sống
cho developer (field error_detail / reason kỹ thuật của pipeline giữ nguyên).
"""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.learner_messages import (
    attach_learner_reason,
    learner_error_message,
    learner_reason,
)
from app.main import app

client = TestClient(app)

# Token kỹ thuật CẤM xuất hiện trong văn bản học sinh: snake_case id, JSON
# path, dấu ngoặc nhọn schema, tên exception. (Cho phép chữ thường có gạch
# dưới trong… không — cấm hẳn snake_case.)
_FORBIDDEN = re.compile(r"[a-z]+_[a-z_]+|\$\.|\{|\}|Traceback|Error\b|__")


def _sach(text: str) -> bool:
    return _FORBIDDEN.search(text) is None


# ── unit: learner_reason chọn theo failure_category CÓ CẤU TRÚC ──
def test_learner_reason_capability_gap_sach_token():
    env = {
        "status": "unsupported",
        "reason": "Bài cần cơ chế chưa có engine tất định sở hữu (optimal_pathfinding, numeric_threshold).",
        "failure_category": "capability_gap",
        "error_code": "gate_mechanism_ownership",
    }
    msg = learner_reason(env)
    assert _sach(msg), f"lộ token kỹ thuật: {msg}"
    assert "từ chối trung thực" in msg


def test_learner_reason_ngoai_danh_muc_sach_token():
    env = {"status": "unsupported", "reason": "LLM tự viết lý do kỹ thuật simulation_id=x"}
    msg = learner_reason(env)
    assert _sach(msg), f"lộ token kỹ thuật: {msg}"
    assert "danh mục" in msg


def test_attach_khong_dung_den_envelope_ok():
    ok_env = {"status": "ok", "simulation_id": "algorithm.find_max", "config": {}}
    assert attach_learner_reason(ok_env) is ok_env  # nguyên vẹn, không copy thừa


def test_attach_gan_learner_reason_khong_mutate_goc():
    env = {"status": "unsupported", "reason": "kỹ thuật", "failure_category": "capability_gap"}
    out = attach_learner_reason(env)
    assert "learner_reason" in out and _sach(out["learner_reason"])
    assert "learner_reason" not in env  # bản sao — envelope pipeline không đổi


def test_learner_error_message_khong_nhung_chi_tiet():
    msg = learner_error_message()
    assert _sach(msg), f"lộ token kỹ thuật: {msg}"
    assert "thử lại" in msg


# ── integration qua /api/analyze (monkeypatch run_pipeline — không network) ──
@pytest.fixture()
def co_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")


def _analyze(text: str):
    return client.post("/api/analyze", json={"input": {"type": "text", "content": text}})


def test_api_unsupported_mang_learner_reason(monkeypatch, co_key):
    async def fake_pipeline(text, api_key, pattern_store=None, observer=None):
        return {
            "status": "unsupported",
            "reason": "Bài cần cơ chế chưa có engine tất định sở hữu (arbitrary_algorithm).",
            "failure_category": "capability_gap",
        }

    monkeypatch.setattr(main_module, "run_pipeline", fake_pipeline)
    res = _analyze("Đề bài dài đủ mười ký tự trở lên để qua cổng độ dài.")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "unsupported"
    # reason kỹ thuật GIỮ NGUYÊN (diagnostics), learner_reason sạch token
    assert "arbitrary_algorithm" in body["reason"]
    assert _sach(body["learner_reason"])


def test_api_422_than_thien_va_chi_tiet_tach_rieng(monkeypatch, co_key):
    async def fail_pipeline(text, api_key, pattern_store=None, observer=None):
        raise RuntimeError(
            'Không sinh được cấu hình hợp lệ sau 3 lần thử (lỗi cuối: objects[2].value '
            'thiếu trường "type" theo schema dsl_v1).'
        )

    monkeypatch.setattr(main_module, "run_pipeline", fail_pipeline)
    res = _analyze("Đề bài dài đủ mười ký tự trở lên để qua cổng độ dài.")
    assert res.status_code == 422
    body = res.json()
    # học sinh: thân thiện, không schema error
    assert _sach(body["error"]), f"lộ token kỹ thuật: {body['error']}"
    # developer: chi tiết kỹ thuật vẫn còn, ở field riêng
    assert "objects[2].value" in body["error_detail"]
