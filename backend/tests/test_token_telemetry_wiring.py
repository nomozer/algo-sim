# -*- coding: utf-8 -*-
"""Khoá việc NỐI DÂY telemetry — bộ đếm đúng mà không ai gọi thì vô dụng.

`test_token_telemetry.py` kiểm bản thân bộ đếm. File này kiểm hai thứ khác:
1. `call_gemini` thật sự ghi `usageMetadata` vào đúng stage.
2. Mọi chỗ gọi `call_gemini` đều khai `stage` — thiếu một chỗ là baseline
   khuyết một mảng mà không ai biết.

0 API call thật: thay `httpx.AsyncClient.post`, đúng biên mà conftest bảo vệ.
"""
import ast
import asyncio
from pathlib import Path

import httpx
import pytest

from app.ai import gemini
from app.ai.telemetry import reset_usage, stage_scope, usage_report

APP = Path(__file__).resolve().parents[1] / "app"


class _FakeResponse:
    status_code = 200

    def __init__(self, body: dict):
        self._body = body

    def json(self) -> dict:
        return self._body


def _patch_post(monkeypatch, body: dict) -> None:
    async def fake_post(self, url, **kwargs):
        return _FakeResponse(body)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)


def test_call_gemini_ghi_usage_vao_dung_stage(monkeypatch):
    reset_usage()
    _patch_post(
        monkeypatch,
        {
            "candidates": [{"content": {"parts": [{"text": '{"ok": true}'}]}}],
            "usageMetadata": {
                "promptTokenCount": 999,
                "candidatesTokenCount": 111,
                "totalTokenCount": 1110,
            },
        },
    )

    with stage_scope("analyze"):
        asyncio.run(gemini.call_gemini("k", "sys", "user"))

    rep = usage_report()
    assert "analyze" in rep, "call_gemini không ghi telemetry"
    assert rep["analyze"]["prompt_tokens"] == 999
    assert rep["analyze"]["total_tokens"] == 1110
    assert rep["analyze"]["calls"] == 1
    reset_usage()


def test_luot_tra_ve_rong_van_duoc_tinh_token(monkeypatch):
    """Lượt hỏng vẫn tiêu token — bỏ sót nó làm baseline đẹp hơn sự thật."""
    reset_usage()
    _patch_post(monkeypatch, {"candidates": [], "usageMetadata": {"totalTokenCount": 500}})

    with stage_scope("classify"), pytest.raises(RuntimeError):
        asyncio.run(gemini.call_gemini("k", "sys", "user"))

    assert usage_report()["classify"]["total_tokens"] == 500
    reset_usage()


def _files_goi_call_gemini_thieu_stage_scope() -> list[str]:
    """Mọi file gọi `call_gemini` phải dùng `stage_scope`.

    Kiểm bằng AST chứ không regex: đối số của `call_gemini` có lời gọi lồng
    nhau (`load_skill(skill)`), regex non-greedy sẽ cắt nhầm ở dấu `)` đầu tiên
    — đúng cái bẫy đã làm bản đầu của guard này báo dương tính giả toàn tập.
    """
    thieu: list[str] = []
    for path in sorted(APP.rglob("*.py")):
        if path.name in ("gemini.py", "telemetry.py"):
            continue
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        goi = [
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and (n.func.id if isinstance(n.func, ast.Name) else getattr(n.func, "attr", None))
            == "call_gemini"
        ]
        if goi and "stage_scope" not in src:
            thieu.append(f"{path.relative_to(APP)} ({len(goi)} chỗ gọi)")
    return thieu


def test_moi_file_goi_call_gemini_deu_dung_stage_scope():
    """Thiếu `stage_scope` ⇒ token của stage đó rơi vào 'unknown', baseline khuyết."""
    thieu = _files_goi_call_gemini_thieu_stage_scope()
    assert not thieu, f"File gọi call_gemini mà không dùng stage_scope: {thieu}"
