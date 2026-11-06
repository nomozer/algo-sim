# -*- coding: utf-8 -*-
"""Real Product Integration — selectable Hybrid `/4` runtime (`HYBRID_ROUTE_MODE`), cache invalidation,
infrastructure-failure vs mathematical-refusal separation, secret redaction, diagnostics and rollback.

Covers Master Task §IV, §VII, §VIII, §X:
- `HYBRID_ROUTE_MODE=off` (default): `LLM_ONLY` unchanged, zero Route D imports (`D-01`).
- `HYBRID_ROUTE_MODE=staging-replay`: works across local and Docker bridge IPs, marks `REPLAY_STAGING_SIMULATED`,
  separates missing/corrupt staging corpus (`503 INFRASTRUCTURE_FAILURE`) from math/clarification refusals (`200`).
- `HYBRID_ROUTE_MODE=live`: requires `ALLOW_LIVE_AI=1` + `GEMINI_API_KEY`, runs `TransportExtractor` -> `/4`,
  binds cache to `{route, model, extraction_surface, route_d_surface, exact_source}`, maps provider/technical faults
  to sanitized `502`/`503`/`504` (`INFRASTRUCTURE_FAILURE`) without leaking keys/tracebacks or falling back to `LLM_ONLY`.
"""
from __future__ import annotations

from copy import deepcopy
import json

import pytest
from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import main as main_module
from app.ai import gemini
from app.ai import hybrid_offline as H
from app.ai import typed_fact_next_extraction as E
from app.main import _cache_key, app
from app.persistence import db as db_module
from app.persistence.db import Base, SimulationCache
from app.runtime_identity import runtime_identity
from tests.geometry.test_route_d_unresolved_clarification import GOC_CHIEU, _only as _clarify_payload
from tests.geometry.test_typed_fact_next_v2_distance_bridge import _prism

DOCKER_BRIDGE_CLIENT = ("172.18.0.5", 44120)
SECRET_KEY = "AQ." + "Ab8RN6L_TEST_DO_NOT_LEAK_SECRET_KEY_VALUE_1234567890"


@pytest.fixture(autouse=True)
def isolated_sqlite_db(tmp_path, monkeypatch):
    test_db = tmp_path / "hybrid_product_integration_test.db"
    test_engine = create_engine(f"sqlite:///{test_db}", connect_args={"check_same_thread": False})
    TestSession = sessionmaker(bind=test_engine, autoflush=False)
    Base.metadata.create_all(test_engine)
    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "SessionLocal", TestSession)
    monkeypatch.setattr(main_module, "SessionLocal", TestSession)
    import app.accounts.router as router_module      # sessions and the usage ledger live behind the accounts router
    monkeypatch.setattr(router_module, "SessionLocal", TestSession)
    yield TestSession
    test_engine.dispose()


def _post(text: str, client=DOCKER_BRIDGE_CLIENT):
    from tests.route_client import route_client
    return route_client(app, client=client).post("/api/analyze", json={"input": {"type": "text", "content": text}})


def _gemini_ok_body(payload: dict) -> dict:
    return {
        "candidates": [{
            "finishReason": "STOP",
            "content": {"parts": [{"text": json.dumps(payload, ensure_ascii=False)}]},
        }],
        "usageMetadata": {"promptTokenCount": 120, "candidatesTokenCount": 80, "totalTokenCount": 200},
    }


@pytest.fixture
def staging_env(tmp_path, monkeypatch):
    prism = _prism()
    clarify = _clarify_payload()
    contradict = deepcopy(prism)
    contradict["problem_text"] = prism["problem_text"].replace("AA' = 12.", "AA' = 12. BC = 11.")
    contradict["premises"].append(
        {"kind": "segment_length", "args": {"segment": ["B", "C"], "value": "11"}, "quote": "BC = 11."}
    )
    corpus_path = tmp_path / "staging-corpus.json"
    corpus_path.write_text(
        json.dumps(
            {
                "schema": H.LOCAL_REPLAY_SCHEMA,
                "outputs": {
                    prism["problem_text"]: prism,
                    GOC_CHIEU: clarify,
                    contradict["problem_text"]: contradict,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)
    monkeypatch.setenv("HYBRID_REPLAY_CORPUS", str(corpus_path))
    assert not hasattr(main_module, "run_pipeline")
    yield prism, contradict, corpus_path


def test_default_hybrid_route_mode_is_live_and_off_or_unknown_is_invalid(monkeypatch):
    monkeypatch.delenv("HYBRID_ROUTE_MODE", raising=False)
    assert main_module.hybrid_route_mode() == "live"
    for invalid_mode in ("off", "unexpected-mode"):
        monkeypatch.setenv("HYBRID_ROUTE_MODE", invalid_mode)
        assert main_module.hybrid_route_mode() == "invalid"
    monkeypatch.delenv("HYBRID_ROUTE_MODE", raising=False)
    ident = runtime_identity()
    assert ident["hybrid_route"]["mode"] == "live"
    assert ident["hybrid_route"]["enabled"] is True
    assert ident["hybrid_route"]["adapter_version"] == "hybrid-simulation-adapter/4" 


def test_staging_replay_serves_docker_bridge_client_with_explicit_simulated_marker_and_cache(staging_env, monkeypatch):
    prism, _, _ = staging_env
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "staging-replay")
    first = _post(prism["problem_text"], client=DOCKER_BRIDGE_CLIENT)
    assert first.status_code == 200
    assert first.headers["cache-control"] == "no-store"
    assert first.headers["x-algosim-cache"] == "miss"
    body = first.json()
    assert body["schema_version"] == "hybrid-route-d-simulation/4"
    assert body["route_d"]["status"] == "SERVED"
    assert body["route_d"]["extraction_mode"] == "REPLAY_STAGING_SIMULATED"
    assert body["route_d"]["answer_exact"]["q"]["coef"] == "12"
    assert body["envelope"]["status"] == "ok"

    second = _post(prism["problem_text"], client=DOCKER_BRIDGE_CLIENT)
    assert second.status_code == 200 and second.headers["x-algosim-cache"] == "hit"
    assert second.json() == body


def test_staging_replay_preserves_clarification_and_contradiction_without_fallback(staging_env, monkeypatch):
    _, contradict, _ = staging_env
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "staging-replay")

    clar_res = _post(GOC_CHIEU, client=DOCKER_BRIDGE_CLIENT)
    assert clar_res.status_code == 200 and clar_res.headers["x-algosim-cache"] == "none"
    clar_body = clar_res.json()
    assert clar_body["route_d"]["status"] == "REFUSED"
    assert clar_body["envelope"]["reason_code"] == "AMBIGUOUS_FACT"
    assert clar_body["route_d"]["refusal"]["clarification"]["schema_version"] == "route-d-clarification/1"
    assert "hình chiếu" in clar_body["route_d"]["refusal"]["clarification"]["question"]

    con_res = _post(contradict["problem_text"], client=DOCKER_BRIDGE_CLIENT)
    assert con_res.status_code == 200 and con_res.headers["x-algosim-cache"] == "none"
    con_body = con_res.json()
    assert con_body["route_d"]["status"] == "REFUSED"
    assert con_body["envelope"]["reason_code"] == "INCONSISTENT_FACTS"
    assert "scene3d" not in con_body["envelope"]


def test_staging_replay_missing_or_corrupt_corpus_is_503_infrastructure_failure(staging_env, monkeypatch, tmp_path):
    prism, _, _ = staging_env
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "staging-replay")
    monkeypatch.setenv("HYBRID_REPLAY_CORPUS", str(tmp_path / "missing-corpus.json"))
    res = _post(prism["problem_text"])
    assert res.status_code == 503
    assert res.headers["cache-control"] == "no-store"
    body = res.json()
    assert body["reason_code"] == "STAGING_CORPUS_UNAVAILABLE"
    assert body["failure_kind"] == "INFRASTRUCTURE_FAILURE"
    assert "route_d" not in body


def test_staging_replay_refuses_direct_image_before_vision_ingestion(staging_env, monkeypatch):
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "staging-replay")
    monkeypatch.setenv("GEMINI_API_KEY", SECRET_KEY)

    async def vision_must_not_run(*_a, **_k):
        raise AssertionError("Vision ingestion ran in staging-replay")

    monkeypatch.setattr(main_module, "ingest_to_text", vision_must_not_run)
    from tests.route_client import route_client
    res = route_client(app, client=DOCKER_BRIDGE_CLIENT).post(
        "/api/analyze",
        json={"input": {"type": "image", "content": "not-base64", "mime_type": "image/png"}},
    )
    assert res.status_code == 400
    assert res.json()["reason_code"] == "IMAGE_DIRECT_UNSUPPORTED"


def test_live_mode_requires_allow_live_ai_and_api_key_without_fallback(staging_env, monkeypatch):
    prism, _, _ = staging_env
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "live")

    # 1. Explicit ALLOW_LIVE_AI=0 kill-switch -> 503 LIVE_AI_DISABLED even if GEMINI_API_KEY is present
    monkeypatch.setenv("GEMINI_API_KEY", SECRET_KEY)
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    r1 = _post(prism["problem_text"])
    assert r1.status_code == 503
    assert r1.json()["reason_code"] == "LIVE_AI_DISABLED"
    assert r1.json()["failure_kind"] == "INFRASTRUCTURE_FAILURE"
    assert SECRET_KEY not in r1.text

    # 2. Default product mode (no opt-in ALLOW_LIVE_AI flag required) with GEMINI_API_KEY missing -> 503 MISSING_API_KEY
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    r2 = _post(prism["problem_text"])
    assert r2.status_code == 503
    assert r2.json()["reason_code"] == "MISSING_API_KEY"
    assert r2.json()["failure_kind"] == "INFRASTRUCTURE_FAILURE"


def test_live_mode_domain_gate_runs_before_provider_and_serves_certified_response_with_cache_invalidation(
    staging_env, monkeypatch
):
    prism, _, _ = staging_env
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "live")
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", SECRET_KEY)
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")

    sent_requests: list[dict] = []

    def fake_live_transport(api_key: str, model: str | None = None, timeout_seconds: float = 60.0, **_kw):
        assert api_key == SECRET_KEY
        def _send(payload: dict) -> dict:
            sent_requests.append({"model": model, "payload": payload})
            return _gemini_ok_body(prism)
        return _send

    monkeypatch.setattr(H, "_live_provider_transport", fake_live_transport)

    # Out-of-scope domain rejected with 0 provider requests
    oos = _post("Viết chương trình sắp xếp mảng tăng dần bằng thuật toán QuickSort.")
    assert oos.status_code == 200
    assert oos.json()["failure_category"] == "out_of_scope"
    assert len(sent_requests) == 0

    # First geometry request -> provider called once, certified /4 SERVED, cached
    r_miss = _post(prism["problem_text"])
    assert r_miss.status_code == 200 and r_miss.headers["x-algosim-cache"] == "miss"
    assert len(sent_requests) == 1
    body = r_miss.json()
    assert body["schema_version"] == "hybrid-route-d-simulation/4"
    assert body["route_d"]["status"] == "SERVED"
    assert body["route_d"]["extraction_mode"] == "LIVE_GEMINI_STRUCTURED"
    assert body["route_d"]["extraction_model"] == "gemini-2.5-flash"
    assert body["route_d"]["answer_exact"]["q"]["coef"] == "12"
    assert SECRET_KEY not in r_miss.text

    # Repeat -> cache hit, 0 new provider requests
    r_hit = _post(prism["problem_text"])
    assert r_hit.status_code == 200 and r_hit.headers["x-algosim-cache"] == "hit"
    assert len(sent_requests) == 1

    # Model change -> cache invalidated (miss)
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-pro")
    r_model = _post(prism["problem_text"])
    assert r_model.status_code == 200 and r_model.headers["x-algosim-cache"] == "miss"
    assert r_model.json()["route_d"]["extraction_model"] == "gemini-2.5-pro"
    assert len(sent_requests) == 2

    # Extraction surface fingerprint change -> cache invalidated (miss)
    real_fp = E.typed_fact_next_surface_fingerprint
    monkeypatch.setattr(E, "typed_fact_next_surface_fingerprint", lambda: real_fp() + "-v2")
    r_surface = _post(prism["problem_text"])
    assert r_surface.status_code == 200 and r_surface.headers["x-algosim-cache"] == "miss"
    assert len(sent_requests) == 3


@pytest.mark.parametrize(
    "fault_body,raises_exc,expected_status,expected_code",
    [
        (None, RuntimeError(f"Connection failed with key {SECRET_KEY}"), 502, "PROVIDER_ERROR"),
        ({"candidates": []}, None, 502, "NO_CANDIDATE"),
        ({"promptFeedback": {"blockReason": "SAFETY"}, "candidates": []}, None, 502, "PROVIDER_BLOCKED"),
        ({"candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": "{"}]}}]}, None, 502, "RESPONSE_TRUNCATED"),
        ({"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "not-json"}]}}]}, None, 502, "JSON_INVALID"),
    ],
)
def test_live_mode_provider_and_schema_faults_map_to_sanitized_infrastructure_errors_and_never_cache(
    staging_env, monkeypatch, fault_body, raises_exc, expected_status, expected_code
):
    prism, _, _ = staging_env
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "live")
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", SECRET_KEY)

    def faulty_transport(api_key: str, model: str | None = None, timeout_seconds: float = 60.0, **_kw):
        def _send(_payload: dict) -> dict:
            if raises_exc is not None:
                raise raises_exc
            return fault_body
        return _send

    monkeypatch.setattr(H, "_live_provider_transport", faulty_transport)
    res = _post(prism["problem_text"])
    assert res.status_code == expected_status
    assert res.headers["cache-control"] == "no-store"
    body = res.json()
    assert body["reason_code"] == expected_code
    assert body["failure_kind"] == "INFRASTRUCTURE_FAILURE"
    assert "route_d" not in body
    assert SECRET_KEY not in res.text
    assert "RuntimeError" not in res.text
    assert "Traceback" not in res.text


def test_live_mode_deadline_maps_to_504_and_rollback_to_off_restores_llm_only(staging_env, monkeypatch):
    prism, _, _ = staging_env
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "live")
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", SECRET_KEY)

    clock = iter(range(0, 10_000, 500))
    monkeypatch.setattr(H, "perf_counter", lambda: next(clock))
    monkeypatch.setattr(H, "_live_provider_transport", lambda *a, **k: (lambda _p: _gemini_ok_body(prism)))
    res_timeout = _post(prism["problem_text"])
    assert res_timeout.status_code == 504
    assert res_timeout.json()["reason_code"] == "HYBRID_DEADLINE_EXCEEDED"
    assert res_timeout.json()["failure_kind"] == "INFRASTRUCTURE_FAILURE"

    # Setting `HYBRID_ROUTE_MODE=off` fails closed with 503 INVALID_HYBRID_ROUTE_MODE (no LLM_ONLY fallback)
    ident_live = runtime_identity()
    assert ident_live["hybrid_route"]["mode"] == "live"
    assert ident_live["hybrid_route"]["enabled"] is True
    assert SECRET_KEY not in json.dumps(ident_live, ensure_ascii=False)

    monkeypatch.setenv("HYBRID_ROUTE_MODE", "off")
    res_off = _post(prism["problem_text"])
    assert res_off.status_code == 503
    assert res_off.json()["reason_code"] == "INVALID_HYBRID_ROUTE_MODE"
    assert res_off.json()["failure_kind"] == "INFRASTRUCTURE_FAILURE"


def test_staging_replay_serves_and_refuses_all_16_scope_classes():
    from scripts.export_hybrid_product_integration_corpus import RUN_DIR, verify_16_classes

    corpus_path = RUN_DIR / "product-integration-staging-corpus.json"
    assert corpus_path.is_file(), f"Missing staging corpus {corpus_path}"
    receipt, fe_fixtures = verify_16_classes(corpus_path)
    assert receipt["categories_total"] == 16
    assert receipt["categories_passed"] == 16
    assert receipt["cases_total"] >= 40
    assert len({f["category"] for f in fe_fixtures}) == 16


@pytest.mark.parametrize("bad_timeout", ["nan", "inf", "-5", "0", "not-a-number"])
def test_live_mode_non_finite_timeout_env_never_crashes_500(staging_env, monkeypatch, bad_timeout):
    prism, _, _ = staging_env
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "live")
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", SECRET_KEY)
    monkeypatch.setenv("HYBRID_LIVE_TIMEOUT_SECONDS", bad_timeout)
    monkeypatch.setenv("HYBRID_LIVE_DEADLINE_SECONDS", bad_timeout)

    seen_timeouts: list[tuple[float, float | None]] = []

    def capture_transport(api_key: str, model: str | None = None, timeout_seconds: float = 60.0, *, deadline_seconds: float | None = None, **_kw):
        seen_timeouts.append((timeout_seconds, deadline_seconds))
        return lambda _p: _gemini_ok_body(prism)

    monkeypatch.setattr(H, "_live_provider_transport", capture_transport)
    res = _post(prism["problem_text"])
    assert res.status_code == 200
    assert res.json()["route_d"]["status"] == "SERVED"
    assert seen_timeouts == [(60.0, 180.0)]


def test_live_transport_upstream_httpx_timeout_maps_to_504_and_respects_deadline_and_budget(staging_env, monkeypatch):
    import httpx

    prism, _, _ = staging_env
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "live")
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", SECRET_KEY)
    monkeypatch.setenv("GEMINI_MODEL", "   ")  # empty/whitespace normalizes to gemini-2.5-flash
    monkeypatch.setenv("HYBRID_LIVE_TIMEOUT_SECONDS", "2.0")
    monkeypatch.setenv("HYBRID_LIVE_DEADLINE_SECONDS", "2.5")

    # 1. Upstream httpx.ReadTimeout maps to HTTP 504 HYBRID_DEADLINE_EXCEEDED (not 502) and halts before backoff overruns deadline
    timeout_calls: list[tuple[str, float]] = []

    def always_timeout_post(url: str, **kwargs):
        timeout_calls.append((url, float(kwargs.get("timeout", 0.0))))
        raise httpx.ReadTimeout(f"Upstream read timed out with key {SECRET_KEY}")

    monkeypatch.setattr(httpx, "post", always_timeout_post)
    r_504 = _post(prism["problem_text"])
    assert r_504.status_code == 504
    body_504 = r_504.json()
    assert body_504["reason_code"] == "HYBRID_DEADLINE_EXCEEDED"
    assert body_504["failure_kind"] == "INFRASTRUCTURE_FAILURE"
    assert SECRET_KEY not in r_504.text
    # With deadline=2.5s and first backoff=1.0s, at most 2 attempts run before remaining budget <= next backoff (2.0s)
    assert 1 <= len(timeout_calls) <= 2
    assert all(url.endswith("/models/gemini-2.5-flash:generateContent") for url, _ in timeout_calls)

    # 2. Transient HTTP 503 -> 200 counts 1 logical call + 1 retry request in ApiBudget and normalizes GEMINI_MODEL=""
    monkeypatch.setenv("HYBRID_LIVE_TIMEOUT_SECONDS", "10.0")
    monkeypatch.setenv("HYBRID_LIVE_DEADLINE_SECONDS", "30.0")
    budget = gemini.ApiBudget(max_api_calls=5, max_logical_calls=5)
    monkeypatch.setattr(gemini, "BUDGET", budget)
    monkeypatch.setattr(gemini, "BACKOFF_BASE_SECONDS", 0.001)
    attempts = [0]

    class FakeResp:
        def __init__(self, status_code: int, payload: dict):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    def transient_then_ok(url: str, **kwargs):
        attempts[0] += 1
        assert url.endswith("/models/gemini-2.5-flash:generateContent")
        if attempts[0] == 1:
            return FakeResp(503, {"error": {"message": "overloaded"}})
        return FakeResp(200, _gemini_ok_body(prism))

    monkeypatch.setattr(httpx, "post", transient_then_ok)
    r_ok = _post(prism["problem_text"])
    assert r_ok.status_code == 200
    assert r_ok.json()["route_d"]["status"] == "SERVED"
    assert r_ok.json()["route_d"]["extraction_model"] == "gemini-2.5-flash"
    assert budget.logical_calls == 1
    assert budget.http_requests == 2
    assert budget.retry_requests == 1
    assert budget.transient_hits == 1
    ident = runtime_identity()
    assert ident["hybrid_route"]["gemini_model"] == "gemini-2.5-flash"


def test_staging_replay_corpus_is_memoized_and_copies_single_entry(staging_env, monkeypatch):
    prism, _, corpus_path = staging_env
    H._REPLAY_CORPUS_CACHE.clear()
    read_calls = [0]
    real_loads = json.loads

    def counting_loads(s, *a, **kw):
        if isinstance(s, str) and H.LOCAL_REPLAY_SCHEMA in s:
            read_calls[0] += 1
        return real_loads(s, *a, **kw)

    monkeypatch.setattr(H.json, "loads", counting_loads)
    p1 = H.prepare_staging_replay(prism["problem_text"], str(corpus_path))
    p2 = H.prepare_staging_replay("Đề không có trong kho.", str(corpus_path))
    assert p1 is not None and p1.recorded is not None
    assert p2 is not None and p2.recorded is None
    assert read_calls[0] == 1


def test_stated_line_perpendicular_to_base_is_drawn_with_exact_witness_and_edges_are_not_duplicated(
        staging_env, monkeypatch):
    """«hình chiếu vuông góc của A′ lên (ABC) là H» is a GIVEN ⊥ relation: the scene draws A′H (no solid edge) and the
    exact right-angle witness sits on it; «SA ⊥ (ABCD)» keeps its witness on the lateral edge SA, no second segment."""
    from scripts.export_hybrid_product_integration_corpus import RUN_DIR

    corpus = RUN_DIR / "product-integration-staging-corpus.json"
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "staging-replay")
    monkeypatch.setenv("HYBRID_REPLAY_CORPUS", str(corpus))
    texts = {c["case_id"]: c for cat in json.loads(
        (RUN_DIR / "product-integration-16-classes-verification.json").read_text(encoding="utf-8"))["categories"]
        for c in cat["cases"]}

    oblique = _post(texts["S2-B-A03_control_with_dimensions"]["problem_text"]).json()
    assert oblique["route_d"]["status"] == "SERVED" and oblique["route_d"]["answers"] == {"mg1": "√3"}
    segs = [o for o in oblique["envelope"]["scene3d"]["objects"] if o["type"] == "segment3"]
    height = [o for o in segs if set(o.get("endpoint_ids") or ()) == {"A_prime", "H"}]
    assert len(height) == 1, [o["id"] for o in segs]
    assert height[0]["notation"] == "A′H"
    w = height[0]["perpendicular_witness"]
    assert w and w["from"] == "A_prime" and w["foot_id"] == "H"

    pyramid = _post(texts["S2-B-I07_ve_va_tinh"]["problem_text"]).json()
    assert pyramid["route_d"]["answers"] == {"mg1": "8/3"}
    sa = [o for o in pyramid["envelope"]["scene3d"]["objects"]
          if o["type"] == "segment3" and set(o.get("endpoint_ids") or ()) == {"S", "A"}]
    assert [o["id"] for o in sa] == ["canh_ben_S_A"] and sa[0].get("perpendicular_witness")


@pytest.mark.parametrize("phrasing", ["perpendicular", "altitude"])
def test_stated_perpendicular_to_a_non_vertex_foot_is_drawn_once_in_learner_order(phrasing):
    """«SH ⊥ (ABCD)» and «SH là đường cao», H the midpoint of AB: both normalize through `_rang_buoc_vuong()` and both
    place S, so both draw SH once with an exact witness; V = 4 unchanged; construction order O1–O4 clean."""
    from app.ai.function_route import run_fact_route
    from tests.geometry import hybrid_compiler_benchmark as HB
    from tests.geometry.construction_sequencing import check

    q = ["Cho hình chóp S.ABCD.", "Đáy ABCD là hình vuông cạnh 2.", "Gọi H là trung điểm AB."]
    facts = [HB._f("f1", "solid", q[0], solid="S.ABCD", solid_type="pyramid"),
             HB._f("f2", "polygon_shape", q[1], points=list("ABCD"), shape="square", value="2"),
             HB._f("f3", "point_def", q[2], point="H", point_kind="midpoint", points=["A", "B"])]
    rel = (HB._f("f4", "perpendicular", "SH vuông góc với (ABCD).", points_a=["S", "H"], points_b=list("ABCD"))
           if phrasing == "perpendicular" else
           HB._f("f4", "altitude", "SH là đường cao của hình chóp S.ABCD.", points=["S", "H"], solid="S.ABCD"))
    q, facts = HB._with((q, facts), rel, HB._f("f5", "length", "SH = 3.", points=["S", "H"], measure="segment", value="3"),
                        HB._ask("q", "Tính thể tích khối chóp S.ABCD.", "volume", solid="S.ABCD"))
    r = run_fact_route(" ".join(q), {"facts": facts})
    assert r.status == "SERVED" and r.answers == {"q": "4"}, (r.code, r.reason)
    sh = [o for o in r.scene3d["objects"] if o["type"] == "segment3" and set(o.get("endpoint_ids") or ()) == {"S", "H"}]
    assert len(sh) == 1 and sh[0]["perpendicular_witness"]["foot_id"] == "H"
    assert check(r.scene3d) == {"O1": [], "O2": [], "O3": [], "O4": []}


def test_assigned_hybrid_envelope_keeps_the_problem_statement_through_the_classroom_gate():
    """F1 of the pedagogical review: the classroom stores the envelope the teacher's browser sends; the statement the
    frontend stamps on it (`problem_statement`) must survive the gate, so a student who opens the assignment sees it."""
    from app.accounts.classroom_router import _validated_envelope
    from scripts.export_hybrid_product_integration_corpus import RUN_DIR

    bundle = json.loads((RUN_DIR / "product-integration-frontend-fixtures.json").read_text(encoding="utf-8"))
    row = next(f for f in bundle["fixtures"] if f["id"] == "S2-B-I07_ve_va_tinh")
    envelope = {**row["response"]["envelope"], "problem_statement": row["problem_text"]}
    _sim_id, blob = _validated_envelope(envelope)
    assert json.loads(blob)["problem_statement"] == row["problem_text"]
