# -*- coding: utf-8 -*-
"""AXO HYBRID /9 — Standalone Offline Network Isolation & AST Audit Verifier."""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import sys

import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
RUN_DIR = REPO_ROOT / "docs/evaluation/geometry/runs/axo-hybrid-local-ai-replacement-vietnamese-nlu-offline-cutover"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(BACKEND_DIR / "tests") not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR / "tests"))

# Simulate hostile env where legacy cloud key & toggle ARE present while HYBRID_ROUTE_MODE=local-only-scoped
os.environ["HYBRID_ROUTE_MODE"] = "local-only-scoped"
os.environ["GEMINI_API_KEY"] = "fake-key-unused"
os.environ["ALLOW_LIVE_AI"] = "1"
os.environ["PYTHONUTF8"] = "1"

LOCAL_AI_MODULES = [
    BACKEND_DIR / "app/ai/local_slm_runtime.py",
    BACKEND_DIR / "app/ai/local_slm_extractor.py",
    BACKEND_DIR / "app/ai/adaptive_input_router.py",
    BACKEND_DIR / "app/ai/slm_verified_normalizer.py",
    BACKEND_DIR / "app/ai/local_geometry_parser.py",
]
FORBIDDEN_CLOUD_IMPORTS = ("google.genai", "google.generativeai", "openai", "anthropic", "vertexai")


def _ast_audit() -> dict[str, list[str]]:
    findings: dict[str, list[str]] = {}
    for mod in LOCAL_AI_MODULES:
        tree = ast.parse(mod.read_text(encoding="utf-8"), filename=str(mod))
        hits: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(alias.name == f or alias.name.startswith(f"{f}.") for f in FORBIDDEN_CLOUD_IMPORTS):
                        hits.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod_name = str(node.module or "")
                if any(mod_name == f or mod_name.startswith(f"{f}.") for f in FORBIDDEN_CLOUD_IMPORTS):
                    hits.append(mod_name)
        findings[str(mod.relative_to(REPO_ROOT)).replace("\\", "/")] = hits
    return findings


def main() -> int:
    ast_findings = _ast_audit()
    assert all(len(v) == 0 for v in ast_findings.values()), f"Forbidden cloud imports found: {ast_findings}"

    from app import main as M  # noqa: E402
    from app.ai.local_slm_runtime import shutdown_global_local_slm_runtimes  # noqa: E402
    from route_client import route_client  # noqa: E402

    blocked_targets: list[str] = []
    real_connect = socket.socket.connect
    real_create_conn = socket.create_connection
    real_httpx_req = httpx.Client.request

    def _is_loop(host: str | None) -> bool:
        return str(host or "").strip().lower() in {"127.0.0.1", "::1", "localhost", "testserver"}

    def _guard_connect(self, address):
        host = address[0] if isinstance(address, tuple) and address else str(address)
        if not _is_loop(host):
            blocked_targets.append(f"socket:{address!r}")
            raise RuntimeError(f"Non-loopback socket egress blocked: {address!r}")
        return real_connect(self, address)

    def _guard_create(address, *a, **kw):
        host = address[0] if isinstance(address, tuple) and address else str(address)
        if not _is_loop(host):
            blocked_targets.append(f"create_connection:{address!r}")
            raise RuntimeError(f"Non-loopback create_connection blocked: {address!r}")
        return real_create_conn(address, *a, **kw)

    def _guard_httpx(self, method, url, *a, **kw):
        u = httpx.URL(str(url))
        if u.host and not _is_loop(u.host):
            blocked_targets.append(f"httpx:{method}:{url}")
            raise RuntimeError(f"Non-loopback httpx egress blocked: {url}")
        return real_httpx_req(self, method, url, *a, **kw)

    socket.socket.connect = _guard_connect  # type: ignore[method-assign]
    socket.create_connection = _guard_create  # type: ignore[assignment]
    httpx.Client.request = _guard_httpx  # type: ignore[method-assign]

    prompts = [
        ("fastpath", "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với (ABC) và SA=2a. Tính thể tích khối chóp S.ABC."),
        ("slm_v9", "Cho khối chóp S.ABCD có đáy ABCD là hình chữ nhật với AB=2a, AD=3a. Biết mặt bên SAB là tam giác đều và vuông góc với đáy (ABCD). Tính khoảng cách từ A đến mặt phẳng (SCD)."),
        ("neg_ambig", "Cho hình chóp S.ABC có cạnh bên bằng 2a, đáy ABC là tam giác đều cạnh a. Tính thể tích khối chóp S.ABC."),
        ("oos", "Giải phương trình bậc hai x² - 5x + 6 = 0."),
    ]
    traces: list[dict] = []
    try:
        client = route_client(M.app)
        h = client.get("/api/health").json()
        for label, txt in prompts:
            r = client.post("/api/analyze", json={"input": {"type": "text", "content": txt}})
            body = r.json()
            rd = body.get("route_d") or {}
            tel = rd.get("adaptive_telemetry") or {}
            traces.append({
                "label": label,
                "http_status": r.status_code,
                "route_status": rd.get("status") or body.get("status"),
                "gemini_typed_fact_calls": tel.get("gemini_typed_fact_calls", 0),
                "total_provider_calls": tel.get("total_provider_calls", 0),
                "ux_state": (body.get("local_ai_ux") or {}).get("ux_state"),
            })
    finally:
        socket.socket.connect = real_connect  # type: ignore[method-assign]
        socket.create_connection = real_create_conn  # type: ignore[assignment]
        httpx.Client.request = real_httpx_req  # type: ignore[method-assign]
        shutdown_global_local_slm_runtimes()

    summary = {
        "schema": "offline-network-isolation-audit/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "hostile_env_test": {
            "HYBRID_ROUTE_MODE": "local-only-scoped",
            "GEMINI_API_KEY_SET_TO_FAKE": True,
            "ALLOW_LIVE_AI": "1",
        },
        "ast_cloud_sdk_imports": ast_findings,
        "health_snapshot": {
            "hasKey": h["hasKey"],
            "aiAvailable": h["aiAvailable"],
            "localOnlyMode": h["localOnlyMode"],
            "localSlmReady": h["localSlmReady"],
            "localSlmModel": h["localSlmModel"],
            "extractionBackend": h["extractionBackend"],
        },
        "non_loopback_egress_attempts": blocked_targets,
        "external_ai_calls": sum(int(t["total_provider_calls"] or 0) for t in traces),
        "gemini_invocations": sum(int(t["gemini_typed_fact_calls"] or 0) for t in traces),
        "silent_cloud_fallbacks": len(blocked_targets),
        "traces": traces,
    }
    assert summary["external_ai_calls"] == 0
    assert summary["gemini_invocations"] == 0
    assert summary["silent_cloud_fallbacks"] == 0
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
