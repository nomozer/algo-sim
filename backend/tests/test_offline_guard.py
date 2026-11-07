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


# ── `.env` NẠP LẠI KHÔNG ĐƯỢC GỠ BIÊN; tiến trình CON cũng bị chặn (run `gemini-credential-transport`) ──────────
# Không bao giờ thử bằng request thật tới Gemini: đích socket là TEST-NET-3 (203.0.113.0/24, RFC 5737, không định tuyến)
# và TLD `.invalid` (RFC 2606) — kể cả khi guard hỏng cũng không chạm dịch vụ nào.

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

from tests.offline_child.offline_socket_guard import OfflineNetworkBlocked

FAKE_KEY = "AIza" + "FAKE_TEST_ONLY_dotenv_reload_0123456789"
TEST_NET = ("203.0.113.10", 443)


def test_env_nap_lai_khoa_van_khong_mo_duoc_mang(tmp_path, monkeypatch):
    """The incident's shape: a key comes BACK from `.env` after a test removed it. Every layer must still hold."""
    from dotenv import load_dotenv

    monkeypatch.setenv("GEMINI_API_KEY", "")                       # recorded ⇒ monkeypatch restores it afterwards
    (tmp_path / ".env").write_text(f"GEMINI_API_KEY={FAKE_KEY}\n", encoding="utf-8")
    load_dotenv(tmp_path / ".env", override=True)
    assert os.environ["GEMINI_API_KEY"] == FAKE_KEY                 # the reload happened

    with pytest.raises(RuntimeError, match="blocked"):              # image transport (httpx layer)
        asyncio.run(gemini.call_gemini(os.environ["GEMINI_API_KEY"], "s", "u"))
    with pytest.raises(RuntimeError, match="blocked"):              # Hybrid transport (httpx layer)
        function_calling.live_transport(os.environ["GEMINI_API_KEY"], require_allow_live_ai=False)({"contents": []})
    for target in (TEST_NET, ("generativelanguage.googleapis.com", 443)):   # socket layer, any client
        with socket.socket() as s, pytest.raises(OfflineNetworkBlocked):
            s.settimeout(0.5)
            s.connect(target)


def test_loopback_van_duoc_noi():
    """Postgres on 127.0.0.1, asyncio's socketpair and local servers keep working."""
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        with socket.create_connection(server.getsockname(), timeout=2):
            pass


_CHILD = r"""
import json, os, socket, sys
sys.path.insert(0, '.')
import app.persistence.db                                   # runs load_dotenv(backend/.env) — the incident's refill
key = os.environ.get('GEMINI_API_KEY') or ''
s = socket.socket(); s.settimeout(0.5)
try:
    s.connect(('203.0.113.10', 443)); net = 'CONNECTED'
except Exception as e:
    net = type(e).__name__
import httpx
try:
    httpx.post('https://example.invalid/', timeout=0.5); h = 'SENT'
except Exception as e:
    h = 'BLOCKED' if 'OFFLINE' in str(e) or 'blocked' in str(e) else type(e).__name__
print(json.dumps({'key_is_fake': key == os.environ.get('EXPECT_KEY', ''), 'key_present': bool(key), 'socket': net, 'httpx': h}))
"""


@pytest.mark.parametrize("build", ["inherited_without_key", "filtered_GEMINI_prefix", "explicit_fake_key"])
def test_tien_trinh_con_khong_lay_lai_duoc_khoa_that_va_khong_ra_mang(build):
    """A Python child imports `app` (⇒ `load_dotenv`) however the parent built its env; it never sees the real key
    (only the empty one, or a fake one a test passed on purpose) and cannot open an outbound socket or httpx request."""
    base = {k: v for k, v in os.environ.items() if k != "GEMINI_API_KEY"}
    if build == "filtered_GEMINI_prefix":                           # the shape of test_hybrid_preview_fixtures._run
        base = {k: v for k, v in base.items() if not k.startswith("GEMINI")}
    if build == "explicit_fake_key":
        base.update(GEMINI_API_KEY=FAKE_KEY, EXPECT_KEY=FAKE_KEY)
    r = subprocess.run([sys.executable, "-c", _CHILD], cwd=Path(__file__).resolve().parents[1], env=base,
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
    out = json.loads(r.stdout.strip().splitlines()[-1])
    assert out["key_is_fake"] is True, "child picked a key up from backend/.env"
    assert out["socket"] == "OfflineNetworkBlocked" and out["httpx"] == "BLOCKED", out
