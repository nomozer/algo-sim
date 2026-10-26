# -*- coding: utf-8 -*-
"""Migration Stage 2 — Hybrid V2 opt-in LOCAL on `/api/analyze` (run `scene3d-to-hybrid-v2-replacement`).

Locked behaviour: the switch (`HYBRID_V2_LOCAL=offline-replay`) only acts for a loopback client; off or remote ⇒ the
default `LLM_ONLY` path runs unchanged. On: the /4 response is returned as is, never cached, and a Hybrid refusal is
never re-run on `LLM_ONLY` (no silent fallback). A cached `LLM_ONLY` envelope for the same text is not served either.
0 model calls: the default path here stops at its missing-key gate, the Hybrid path reads an authored replay corpus.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.ai.hybrid_offline import LOCAL_REPLAY_SCHEMA
from app.main import _cache_key, app
from app.persistence.db import SessionLocal, SimulationCache, init_db
from tests.geometry.test_typed_fact_next_v2_distance_bridge import _prism

LOOPBACK = ("127.0.0.1", 50123)


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    raw = _prism()
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps({"schema": LOCAL_REPLAY_SCHEMA, "outputs": {raw["problem_text"]: raw}},
                               ensure_ascii=False), encoding="utf-8")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("HYBRID_V2_LOCAL_REPLAY_CORPUS", str(path))

    def pipeline_must_not_run(*_a, **_k):
        raise AssertionError("LLM_ONLY pipeline ran on the Hybrid path")

    return raw, pipeline_must_not_run


def _post(text, client=LOOPBACK):
    return TestClient(app, client=client).post("/api/analyze", json={"input": {"type": "text", "content": text}})


def test_switch_off_keeps_the_default_route(corpus, monkeypatch):
    raw, _ = corpus
    monkeypatch.delenv("HYBRID_V2_LOCAL", raising=False)
    r = _post(raw["problem_text"])
    assert r.status_code == 503 and "schema_version" not in r.json()     # default path: missing-key gate


def test_switch_on_but_remote_client_keeps_the_default_route(corpus, monkeypatch):
    raw, _ = corpus
    monkeypatch.setenv("HYBRID_V2_LOCAL", "offline-replay")
    r = _post(raw["problem_text"], client=("203.0.113.7", 4000))
    assert r.status_code == 503 and "schema_version" not in r.json()


@pytest.mark.parametrize("value", ["1", "true", "OFFLINE-REPLAY", "live"])
def test_only_the_exact_switch_value_enables_it(corpus, monkeypatch, value):
    raw, _ = corpus
    monkeypatch.setenv("HYBRID_V2_LOCAL", value)
    assert _post(raw["problem_text"]).status_code == 503


def test_served_from_the_replay_corpus_with_the_v4_contract_and_no_cache(corpus, monkeypatch):
    raw, must_not_run = corpus
    monkeypatch.setenv("HYBRID_V2_LOCAL", "offline-replay")
    monkeypatch.setattr(main_module, "run_pipeline", must_not_run)
    init_db()
    key = _cache_key(raw["problem_text"])
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.commit()
    r = _post(raw["problem_text"])
    body = r.json()
    assert r.status_code == 200 and r.headers["cache-control"] == "no-store"
    assert body["schema_version"] == "hybrid-route-d-simulation/4"
    assert body["route_d"]["status"] == "SERVED" and body["envelope"]["status"] == "ok"
    assert body["route_d"]["answer_exact"]["q"]["coef"] == "12"           # d(A', (ABC)) = AA' = 12
    with SessionLocal() as s:
        assert s.query(SimulationCache).filter_by(key=key).count() == 0


def test_text_outside_the_corpus_is_refused_and_never_falls_back(corpus, monkeypatch):
    raw, must_not_run = corpus
    monkeypatch.setenv("HYBRID_V2_LOCAL", "offline-replay")
    monkeypatch.setattr(main_module, "run_pipeline", must_not_run)
    body = _post(raw["problem_text"] + " Tính thêm thể tích khối lăng trụ.").json()
    assert body["route_d"]["status"] == "REFUSED"
    assert body["envelope"]["status"] == "unsupported" and body["envelope"]["reason_code"] == "NO_RECORDED_EXTRACTION"
    assert "scene3d" not in body["envelope"]


def test_a_cached_llm_only_envelope_is_not_served_on_the_hybrid_path(corpus, monkeypatch):
    raw, must_not_run = corpus
    monkeypatch.setenv("HYBRID_V2_LOCAL", "offline-replay")
    monkeypatch.setattr(main_module, "run_pipeline", must_not_run)
    init_db()
    key = _cache_key(raw["problem_text"])
    ident = main_module._policy_identity(main_module.route_policy_snapshot())
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(key=key, problem_text=raw["problem_text"], simulation_id="x",
                              envelope_json=json.dumps({"status": "ok", "marker": "LLM_ONLY_CACHED"}),
                              dsl_version="1", policy_version=ident))
        s.commit()
    body = _post(raw["problem_text"]).json()
    assert body.get("marker") is None and body["schema_version"] == "hybrid-route-d-simulation/4"
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.commit()


def test_missing_corpus_is_a_refusal_not_a_crash(corpus, monkeypatch, tmp_path):
    raw, must_not_run = corpus
    monkeypatch.setenv("HYBRID_V2_LOCAL", "offline-replay")
    monkeypatch.setenv("HYBRID_V2_LOCAL_REPLAY_CORPUS", str(tmp_path / "absent.json"))
    monkeypatch.setattr(main_module, "run_pipeline", must_not_run)
    body = _post(raw["problem_text"]).json()
    assert (body["route_d"]["status"], body["envelope"]["reason_code"]) == ("REFUSED", "NO_RECORDED_EXTRACTION")


def test_out_of_scope_text_is_refused_by_the_same_domain_gate(corpus, monkeypatch):
    _, must_not_run = corpus
    monkeypatch.setenv("HYBRID_V2_LOCAL", "offline-replay")
    monkeypatch.setattr(main_module, "run_pipeline", must_not_run)
    response = _post("Viết chương trình Python in ra dãy Fibonacci tới số thứ mười.")
    assert response.headers.get("cache-control") == "no-store"
    body = response.json()
    assert body["failure_category"] == "out_of_scope"


def test_local_offline_mode_refuses_images_before_ingestion(corpus, monkeypatch):
    """Image ingestion can use Vision; the offline switch must guard that boundary too."""
    monkeypatch.setenv("HYBRID_V2_LOCAL", "offline-replay")
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")

    async def ingestion_must_not_run(*_args, **_kwargs):
        raise AssertionError("offline replay reached image ingestion")

    monkeypatch.setattr(main_module, "ingest_to_text", ingestion_must_not_run)
    response = TestClient(app, client=LOOPBACK).post("/api/analyze", json={
        "input": {"type": "image", "content": "not-an-image", "mime_type": "image/png"}})
    assert response.status_code == 400
    assert response.headers["cache-control"] == "no-store"
    assert "error" in response.json()
