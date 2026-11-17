# -*- coding: utf-8 -*-
"""Adversarial cache invalidation & no-store regression suite for dimension-aware & verified trigonometric construction.

Verifies:
1. `ROUTE_D_CACHE_POLICY` tracks `f"{M.CACHE_VERSION}:route-d"` cleanly;
2. Stale prior-policy rows (`(int(CACHE_VERSION) - 1):route-d`) for inputs whose verdict changed (underdetermined or
   dimensional-mismatch refusal vs served envelope) ALWAYS miss and never bypass current Route D validation;
3. Stale prior-policy rows carrying a poisoned/outdated scene for a served trigonometric input ALWAYS miss, recomputing
   the exact trigonometric construction and storing under `M.ROUTE_D_CACHE_POLICY`;
4. Refusals and HTTP `503` infrastructure responses return `Cache-Control: no-store` and never write to `SimulationCache`;
5. In-process `_PARSER_CACHE` and `prepare_local_first_hybrid(...).cache_key` both partition by
   `LOCAL_GEOMETRY_PARSER_VERSION`, preventing stale AST/contract reuse across parser version bumps.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app import main as M
from app.ai import local_geometry_parser as LGP
from app.ai.hybrid_offline import prepare_local_first_hybrid, resolve_hybrid_gemini_model
from app.main import SUPPORTED_VERSIONS
from app.persistence.db import SessionLocal, SimulationCache, init_db

SERVED_BASELINE_TEXT = (
    "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3 và diện tích đáy bằng 4. "
    "Tính thể tích khối chóp S.ABCD."
)
SERVED_TRIG_TEXT = (
    "Cho hình chóp S.ABC có SA vuông góc với mặt phẳng (ABC), tam giác ABC vuông tại B, "
    "AB = a, BC = a, góc giữa SB và mặt phẳng (ABC) bằng 45°. Tính thể tích khối chóp S.ABC."
)
REFUSED_UNDERDETERMINED_TEXT = (
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông. Tính thể tích khối chóp S.ABCD."
)
REFUSED_DIM_MISMATCH_TEXT = (
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a^2, SA vuông góc với mặt phẳng đáy và SA = a. "
    "Tính thể tích khối chóp S.ABCD."
)
SERVED_RHOMBUS_PRISM_TRIG_TEXT = (
    "Cho hình lăng trụ đứng ABCD.A'B'C'D' có đáy ABCD là hình thoi, góc BAD = 60°, "
    "AA' = 2a, góc giữa đường thẳng AC' và mặt đáy bằng 30°. Tính thể tích khối lăng trụ ABCD.A'B'C'D'."
)


def _prior_policy() -> str:
    return "139:route-d"


def test_route_d_cache_policy_tracks_cache_version_140_and_lockfile(monkeypatch: pytest.MonkeyPatch) -> None:
    from pathlib import Path
    from app.runtime_identity import semantic_environment_fingerprint, semantic_environment_hash
    from app.simulation.geometry_functions import trig_construction_certificates as TCC

    assert M.CACHE_VERSION == "145"
    assert M.ROUTE_D_CACHE_POLICY == "145:route-d"
    assert _prior_policy() == "139:route-d"

    fp_base = semantic_environment_fingerprint()
    lock_path = Path(M.__file__).resolve().parents[1] / "cache_identity.lock.json"
    lock_doc = json.loads(lock_path.read_text(encoding="utf-8"))
    assert lock_doc["cache_version"] == M.CACHE_VERSION
    assert lock_doc["semantic_environment_hash"] == semantic_environment_hash()
    assert lock_doc["components"]["hybrid_route_surface"] == fp_base["hybrid_route_surface"]

    # Prove hybrid_route_surface hashes local_parser_version and trig_construction_certificate_version
    monkeypatch.setattr(LGP, "LOCAL_GEOMETRY_PARSER_VERSION", "local-geometry-parser/999")
    assert semantic_environment_fingerprint()["hybrid_route_surface"] != fp_base["hybrid_route_surface"]
    monkeypatch.undo()
    monkeypatch.setattr(TCC, "TRIG_CONSTRUCTION_CERTIFICATE_VERSION", "trig-construction-certificate/999")
    assert semantic_environment_fingerprint()["hybrid_route_surface"] != fp_base["hybrid_route_surface"]


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-first")
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    from tests.route_client import sign_in

    with TestClient(M.app) as c:
        sign_in(c)
        yield c


def _put_cache_row(key: str, problem_text: str, body: dict, policy: str) -> None:
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(
            SimulationCache(
                key=key,
                problem_text=problem_text,
                simulation_id="generic.semantic_program",
                envelope_json=json.dumps(body, ensure_ascii=False),
                dsl_version=next(iter(SUPPORTED_VERSIONS)),
                policy_version=policy,
            )
        )
        s.commit()


def _delete_cache_row(key: str) -> None:
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.commit()


def test_stale_prior_policy_served_row_is_ignored_when_current_route_refuses(client: TestClient) -> None:
    r_ok = client.post("/api/analyze", json={"input": {"type": "text", "content": SERVED_BASELINE_TEXT}})
    stale_served = r_ok.json()
    assert r_ok.status_code == 200 and stale_served["route_d"]["status"] == "SERVED"

    refused_key = prepare_local_first_hybrid(
        REFUSED_UNDERDETERMINED_TEXT, model=resolve_hybrid_gemini_model()
    ).cache_key
    init_db()
    try:
        _put_cache_row(refused_key, REFUSED_UNDERDETERMINED_TEXT, stale_served, _prior_policy())
        r = client.post("/api/analyze", json={"input": {"type": "text", "content": REFUSED_UNDERDETERMINED_TEXT}})
        body = r.json()
        assert r.status_code == 200
        assert body["route_d"]["status"] == "REFUSED"
        assert body["envelope"]["status"] == "unsupported"
        assert "no-store" in (r.headers.get("cache-control") or "").lower()
    finally:
        _delete_cache_row(refused_key)


def test_stale_prior_policy_wrong_scene_is_recomputed_for_served_trig_problem(client: TestClient) -> None:
    r_poison = client.post("/api/analyze", json={"input": {"type": "text", "content": SERVED_BASELINE_TEXT}})
    poisoned_served = r_poison.json()
    assert r_poison.status_code == 200 and poisoned_served["route_d"]["status"] == "SERVED"

    trig_key = prepare_local_first_hybrid(SERVED_TRIG_TEXT, model=resolve_hybrid_gemini_model()).cache_key
    init_db()
    try:
        _put_cache_row(trig_key, SERVED_TRIG_TEXT, poisoned_served, _prior_policy())
        r_fresh = client.post("/api/analyze", json={"input": {"type": "text", "content": SERVED_TRIG_TEXT}})
        fresh_body = r_fresh.json()
        assert r_fresh.status_code == 200
        assert fresh_body["route_d"]["status"] == "SERVED"
        # Fresh trig computation yields V = (1/3) * (1/2 * a * a) * a = a³/6, NOT the poisoned pyramid answer.
        assert list(fresh_body["route_d"]["answers"].values()) == ["a³/6"]
        assert fresh_body["route_d"]["answers"] != poisoned_served["route_d"]["answers"]

        with SessionLocal() as s:
            stored = s.query(SimulationCache).filter_by(key=trig_key).one_or_none()
            assert stored is not None
            assert stored.policy_version == M.ROUTE_D_CACHE_POLICY
    finally:
        _delete_cache_row(trig_key)


def test_refusals_and_infrastructure_503_are_never_cached(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    refused_key = prepare_local_first_hybrid(
        REFUSED_UNDERDETERMINED_TEXT, model=resolve_hybrid_gemini_model()
    ).cache_key
    init_db()
    _delete_cache_row(refused_key)

    r_ref = client.post("/api/analyze", json={"input": {"type": "text", "content": REFUSED_UNDERDETERMINED_TEXT}})
    assert r_ref.status_code == 200
    assert r_ref.json()["route_d"]["status"] == "REFUSED"
    assert "no-store" in (r_ref.headers.get("cache-control") or "").lower()
    with SessionLocal() as s:
        assert s.query(SimulationCache).filter_by(key=refused_key).one_or_none() is None

    # Live mode with ALLOW_LIVE_AI=0 -> 503 LIVE_AI_DISABLED, never cached
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "live")
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    r_503 = client.post("/api/analyze", json={"input": {"type": "text", "content": SERVED_TRIG_TEXT}})
    assert r_503.status_code == 503
    assert "no-store" in (r_503.headers.get("cache-control") or "").lower()


def test_local_parser_cache_and_hybrid_key_partition_by_parser_version(monkeypatch: pytest.MonkeyPatch) -> None:
    text = SERVED_TRIG_TEXT
    key_v_cur = prepare_local_first_hybrid(text, model="gemini-2.5-flash").cache_key
    res_cur = LGP.parse_geometry_problem_locally(text, use_cache=True)
    assert (LGP.LOCAL_GEOMETRY_PARSER_VERSION, text) in LGP._PARSER_CACHE

    bumped_version = LGP.LOCAL_GEOMETRY_PARSER_VERSION + "-test-bump"
    monkeypatch.setattr(LGP, "LOCAL_GEOMETRY_PARSER_VERSION", bumped_version)
    key_v_next = prepare_local_first_hybrid(text, model="gemini-2.5-flash").cache_key
    assert key_v_next != key_v_cur
    assert (bumped_version, text) not in LGP._PARSER_CACHE

    res_next = LGP.parse_geometry_problem_locally(text, use_cache=True)
    assert res_next.parser_version == bumped_version
    assert res_next.status == res_cur.status
    LGP._PARSER_CACHE.pop((bumped_version, text), None)


def test_stale_139_served_row_misses_for_dimensional_mismatch_refusal(client: TestClient) -> None:
    r_ok = client.post("/api/analyze", json={"input": {"type": "text", "content": SERVED_BASELINE_TEXT}})
    stale_served = r_ok.json()
    assert r_ok.status_code == 200 and stale_served["route_d"]["status"] == "SERVED"

    mismatch_key = prepare_local_first_hybrid(
        REFUSED_DIM_MISMATCH_TEXT, model=resolve_hybrid_gemini_model()
    ).cache_key
    init_db()
    try:
        _put_cache_row(mismatch_key, REFUSED_DIM_MISMATCH_TEXT, stale_served, "139:route-d")
        r = client.post("/api/analyze", json={"input": {"type": "text", "content": REFUSED_DIM_MISMATCH_TEXT}})
        body = r.json()
        assert r.status_code == 200
        assert body["route_d"]["status"] == "REFUSED"
        assert body["envelope"]["status"] == "unsupported"
        assert "no-store" in (r.headers.get("cache-control") or "").lower()
    finally:
        _delete_cache_row(mismatch_key)


def test_stale_139_row_misses_for_composite_rhombus_prism_trig_construction(client: TestClient) -> None:
    r_poison = client.post("/api/analyze", json={"input": {"type": "text", "content": SERVED_BASELINE_TEXT}})
    poisoned = r_poison.json()
    assert r_poison.status_code == 200 and poisoned["route_d"]["status"] == "SERVED"

    prism_key = prepare_local_first_hybrid(
        SERVED_RHOMBUS_PRISM_TRIG_TEXT, model=resolve_hybrid_gemini_model()
    ).cache_key
    init_db()
    try:
        _put_cache_row(prism_key, SERVED_RHOMBUS_PRISM_TRIG_TEXT, poisoned, "139:route-d")
        r_fresh = client.post("/api/analyze", json={"input": {"type": "text", "content": SERVED_RHOMBUS_PRISM_TRIG_TEXT}})
        fresh = r_fresh.json()
        assert r_fresh.status_code == 200
        assert fresh["route_d"]["status"] == "SERVED"
        assert list(fresh["route_d"]["answers"].values()) == ["4a³√3"]
        assert len(fresh["route_d"]["trig_construction_certificates"]) == 2
        with SessionLocal() as s:
            stored = s.query(SimulationCache).filter_by(key=prism_key).one_or_none()
            assert stored is not None
            assert stored.policy_version == M.ROUTE_D_CACHE_POLICY
    finally:
        _delete_cache_row(prism_key)
