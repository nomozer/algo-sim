# -*- coding: utf-8 -*-
"""AXO HYBRID /9 — P7–P8 Product Local-Only Routing, Keyless UX & Network Isolation Tests."""
from __future__ import annotations

import base64
import io
import os
import socket
from pathlib import Path

import httpx
import pytest
from PIL import Image

from app import main as M
from app.ai import hybrid_offline as HO
from app.ai.local_slm_runtime import V9_LOCAL_SLM_MODEL_KEY, shutdown_global_local_slm_runtimes
from tests.route_client import route_client


def _png_b64() -> str:
    buf = io.BytesIO()
    Image.new("RGB", (64, 32), (255, 255, 255)).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _docx_b64(text: str) -> str:
    from docx import Document

    doc = Document()
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _install_egress_guard(monkeypatch):
    blocked_attempts: list[str] = []
    real_connect = socket.socket.connect
    real_create_conn = socket.create_connection
    real_httpx_req = httpx.Client.request
    real_async_httpx_req = httpx.AsyncClient.request

    def _is_loopback_host(host: str | None) -> bool:
        return str(host or "").strip().lower() in {"127.0.0.1", "::1", "localhost", "testserver"}

    def guarded_connect(self, address):
        host = address[0] if isinstance(address, tuple) and address else str(address)
        if not _is_loopback_host(host):
            blocked_attempts.append(f"socket.connect:{address!r}")
            raise AssertionError(f"Non-loopback socket egress attempted: {address!r}")
        return real_connect(self, address)

    def guarded_create_connection(address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) and address else str(address)
        if not _is_loopback_host(host):
            blocked_attempts.append(f"socket.create_connection:{address!r}")
            raise AssertionError(f"Non-loopback create_connection attempted: {address!r}")
        return real_create_conn(address, *args, **kwargs)

    def guarded_httpx_request(self, method, url, *args, **kwargs):
        parsed = httpx.URL(str(url))
        if parsed.host and not _is_loopback_host(parsed.host):
            blocked_attempts.append(f"httpx.Client:{method}:{url}")
            raise AssertionError(f"External HTTPX request attempted: {url}")
        return real_httpx_req(self, method, url, *args, **kwargs)

    async def guarded_async_httpx_request(self, method, url, *args, **kwargs):
        parsed = httpx.URL(str(url))
        if parsed.host and not _is_loopback_host(parsed.host):
            blocked_attempts.append(f"httpx.AsyncClient:{method}:{url}")
            raise AssertionError(f"External async HTTPX request attempted: {url}")
        return await real_async_httpx_req(self, method, url, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket, "create_connection", guarded_create_connection)
    monkeypatch.setattr(httpx.Client, "request", guarded_httpx_request)
    monkeypatch.setattr(httpx.AsyncClient, "request", guarded_async_httpx_request)
    return blocked_attempts


@pytest.fixture(autouse=True)
def _cleanup_runtime():
    yield
    shutdown_global_local_slm_runtimes()


def test_default_route_remains_live_and_general_cutover_is_gated(monkeypatch):
    monkeypatch.delenv("HYBRID_ROUTE_MODE", raising=False)
    assert M.hybrid_route_mode() == "live"
    assert M.CACHE_VERSION == "145"

    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-only-general")
    monkeypatch.delenv("AXO_ALLOW_GENERAL_LOCAL_CUTOVER", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    client = route_client(M.app)
    r = client.post(
        "/api/analyze",
        json={
            "input": {
                "type": "text",
                "content": "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với (ABC) và SA=2a. Tính thể tích khối chóp S.ABC.",
            }
        },
    )
    assert r.status_code == 503
    body = r.json()
    assert body["reason_code"] == "LOCAL_ONLY_GENERAL_NOT_APPROVED"
    assert body["local_ai_ux"]["ux_state"] == "MODEL_NOT_PROVISIONED"

    monkeypatch.setenv("AXO_ALLOW_GENERAL_LOCAL_CUTOVER", "1")
    r_ok = client.post(
        "/api/analyze",
        json={
            "input": {
                "type": "text",
                "content": "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với (ABC) và SA=3a. Tính thể tích khối chóp S.ABC.",
            }
        },
    )
    assert r_ok.status_code == 200
    assert r_ok.json()["route_d"]["status"] == "SERVED"


def test_health_preserves_has_key_and_exposes_local_only_readiness(monkeypatch, tmp_path):
    client = route_client(M.app)

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-only-scoped")
    r_ready = client.get("/api/health")
    assert r_ready.status_code == 200
    h = r_ready.json()
    assert h["ok"] is True
    assert h["hasKey"] is False  # Truthful: GEMINI_API_KEY is NOT set
    assert h["routeMode"] == "local-only-scoped"
    assert h["localOnlyMode"] is True
    assert h["localSlmReady"] is True
    assert h["localSlmModel"] == V9_LOCAL_SLM_MODEL_KEY
    assert h["extractionBackend"] == "local_slm_v9"
    assert h["aiAvailable"] is True
    assert h["local_ai_ux"]["ux_state"] == "READY_OFFLINE"

    monkeypatch.setenv("LOCAL_SLM_CACHE_DIR", str(tmp_path / "empty_slm_dir"))
    r_missing = client.get("/api/health")
    assert r_missing.status_code == 200
    hm = r_missing.json()
    assert hm["localSlmReady"] is False
    assert hm["aiAvailable"] is False
    assert hm["local_ai_ux"]["ux_state"] == "MODEL_NOT_PROVISIONED"


def test_local_only_scoped_network_isolation_and_cloud_vision_block(monkeypatch):
    blocked = _install_egress_guard(monkeypatch)
    # Deliberately configure a fake key & ALLOW_LIVE_AI=1 to verify local-only-scoped NEVER uses them
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-unused")
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-only-scoped")

    client = route_client(M.app)

    # 1. Text requiring SLM fallback serves cleanly with 0 external calls
    slm_txt = (
        "Cho khối chóp S.ABCD có đáy ABCD là hình chữ nhật với AB=2a, AD=3a. "
        "Biết mặt bên SAB là tam giác đều và vuông góc với đáy (ABCD). "
        "Tính khoảng cách từ A đến mặt phẳng (SCD)."
    )
    r_slm = client.post("/api/analyze", json={"input": {"type": "text", "content": slm_txt}})
    assert r_slm.status_code == 200
    b_slm = r_slm.json()
    assert b_slm["route_d"]["status"] == "SERVED"
    assert b_slm["route_d"]["answers"]["q1"] == "3a/2"
    assert b_slm["route_d"]["adaptive_telemetry"]["gemini_typed_fact_calls"] == 0
    assert b_slm["route_d"]["adaptive_telemetry"]["total_provider_calls"] == 0
    assert b_slm["local_ai_ux"]["ux_state"] == "SERVED_OFFLINE_VERIFIED"

    # 2. offline-lab mode works keyless too
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "offline-lab")
    r_lab = client.post(
        "/api/analyze",
        json={
            "input": {
                "type": "text",
                "content": "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với (ABC) và SA=4a. Tính thể tích khối chóp S.ABC.",
            }
        },
    )
    assert r_lab.status_code == 200
    assert r_lab.json()["route_d"]["status"] == "SERVED"

    # 3. Cloud vision endpoints fail closed cleanly without network calls
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-only-scoped")
    img_b64 = _png_b64()
    r_img_ext = client.post("/api/image/extract", json={"content": img_b64, "mime_type": "image/png"})
    assert r_img_ext.status_code == 503
    assert r_img_ext.json()["reason_code"] == "LOCAL_ONLY_CLOUD_VISION_DISABLED"
    assert r_img_ext.json()["local_ai_ux"]["ux_state"] == "CLOUD_OCR_DISABLED_OFFLINE"

    r_prep_img = client.post(
        "/api/input/prepare",
        json={"content": img_b64, "mime_type": "image/png", "filename": "scan.png"},
    )
    assert r_prep_img.status_code == 503
    assert r_prep_img.json()["reason_code"] == "LOCAL_ONLY_CLOUD_VISION_DISABLED"

    # 4. DOCX preparation succeeds locally with 0 VLM calls
    docx_txt = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2a, "
        "SA vuông góc với (ABC) và SA=2a. Tính thể tích khối chóp S.ABC."
    )
    r_prep_docx = client.post(
        "/api/input/prepare",
        json={
            "content": _docx_b64(docx_txt),
            "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "filename": "de_hinh.docx",
        },
    )
    assert r_prep_docx.status_code == 200
    pd_body = r_prep_docx.json()
    assert pd_body["status"] == "ready"
    assert pd_body["metrics"]["vlm_calls"] == 0
    assert pd_body["metrics"]["used_vlm"] is False
    assert blocked == []


def test_local_shadow_mode_keeps_live_authoritative(monkeypatch):
    import json
    from app.ai.local_geometry_parser import parse_geometry_problem_locally
    from app.ai.typed_fact_next_extraction import to_wire_typed_fact_next_v2

    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-shadow")
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-shadow-key")

    txt = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, "
        "SA vuông góc với (ABC) và SA=2a. Tính thể tích khối chóp S.ABC."
    )
    canon = parse_geometry_problem_locally(txt).payload
    assert canon is not None
    wire_dict = to_wire_typed_fact_next_v2(canon)
    gemini_http_envelope = {
        "candidates": [{"content": {"parts": [{"text": json.dumps(wire_dict, ensure_ascii=False)}]}}]
    }
    monkeypatch.setattr(HO, "_live_provider_transport", lambda *a, **kw: (lambda req: gemini_http_envelope))
    client = route_client(M.app)
    r = client.post("/api/analyze", json={"input": {"type": "text", "content": txt}})
    assert r.status_code == 200
    body = r.json()
    assert body["route_d"]["status"] == "SERVED"
    assert body["route_d"]["answers"]["q1"] == "a³√3/6"
    assert body["route_d"]["local_shadow"]["slm_status"] == "SERVED"
    assert body["route_d"]["local_shadow"]["agreed_with_live"] is True


def test_all_10_vietnamese_ux_states_clean():
    forbidden = ("GEMINI_API_KEY", "ALLOW_LIVE_AI", "REASON_CODE", "LOCAL_", "Traceback", ".py", ".gguf", "http://", "503")
    cases = {
        "READY_OFFLINE": (200, {"ok": True, "localOnlyMode": True, "localSlmReady": True}),
        "WARMING_UP_MODEL": (503, {"warming_up": True}),
        "SERVED_OFFLINE_VERIFIED": (200, {"route_d": {"status": "SERVED"}}),
        "CLARIFICATION_NEEDED": (200, {"route_d": {"status": "REFUSED", "refusal": {"code": "AMBIGUOUS_FACT"}}}),
        "MISSING_GEOMETRY_DATA": (200, {"route_d": {"status": "REFUSED", "refusal": {"code": "MISSING_DIMENSION"}}, "envelope": {"failure_category": "insufficient_specification"}}),
        "CONTRADICTORY_GEOMETRY_DATA": (200, {"route_d": {"status": "REFUSED", "refusal": {"code": "INCONSISTENT_FACTS"}}, "envelope": {"failure_category": "geometry_generation_failed"}}),
        "OUT_OF_SUPPORTED_SCOPE": (200, {"status": "unsupported", "failure_category": "out_of_scope", "error_code": "GATE_OUT_OF_SCOPE"}),
        "MODEL_NOT_PROVISIONED": (503, {"reason_code": "MODEL_RUNTIME_UNAVAILABLE"}),
        "RUNTIME_BUSY_OR_TIMEOUT": (504, {"reason_code": "LOCAL_SLM_TIMEOUT"}),
        "CLOUD_OCR_DISABLED_OFFLINE": (503, {"reason_code": "LOCAL_ONLY_CLOUD_VISION_DISABLED"}),
    }
    seen_states: set[str] = set()
    for expected_state, (code, payload) in cases.items():
        desc = HO.build_local_ai_ux_descriptor(status_code=code, body=payload, local_only=True)
        assert desc["ux_state"] == expected_state
        assert desc["learner_title"] and desc["learner_message"]
        seen_states.add(desc["ux_state"])
        combined = f"{desc['learner_title']} {desc['learner_message']}"
        for bad in forbidden:
            assert bad not in combined, f"Leaked {bad!r} into UX state {expected_state}: {combined}"
    assert len(seen_states) == 10
