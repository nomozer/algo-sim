# -*- coding: utf-8 -*-
"""CACHE_VERSION 146 -> 147 (run `axo-hybrid-compositional-geometry-language-grounded-simulation`).

Ensures Route D `SimulationCache` rows written under `146:route-d` MISS and are
recomputed under `147:route-d` after compositional parser (`local-geometry-parser/3`),
SLM extractor (`local-slm-extractor/6`, `slm-grounding-validator/6`), compositional Source
Gate, diacritic-free domain gate, and Scene3D camera framing (`V11-VIS-1`) changes.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app import main as M
from app.ai.compositional_clause_analysis import COMPOSITIONAL_CLAUSE_ANALYZER_VERSION
from app.ai.local_geometry_parser import LOCAL_GEOMETRY_PARSER_VERSION
from app.ai.local_slm_extractor import (
    LOCAL_SLM_EXTRACTOR_V9_VERSION,
    SLM_GROUNDING_VALIDATOR_V9_VERSION,
    compute_local_slm_capability_identity,
)
from app.ai.local_slm_runtime import (
    LOCAL_SLM_CACHE_NAMESPACE,
    LOCAL_SLM_RUNTIME_VERSION,
    build_local_slm_cache_identity,
)
from app.persistence.db import SessionLocal, SimulationCache, init_db
from tests.route_client import sign_in

NESTED_SIM_PROMPT = (
    "Hãy mô phỏng hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, "
    "SA vuông góc với (ABCD) và SA = a."
)


def test_v12_version_constants_and_cache_policy_pair() -> None:
    from tests.cache_policy import assert_cache_policy_at_least
    assert_cache_policy_at_least(147)
    assert LOCAL_GEOMETRY_PARSER_VERSION == "local-geometry-parser/3"
    assert LOCAL_SLM_EXTRACTOR_V9_VERSION == "local-slm-extractor/6"
    assert SLM_GROUNDING_VALIDATOR_V9_VERSION == "slm-grounding-validator/6"
    assert COMPOSITIONAL_CLAUSE_ANALYZER_VERSION == "compositional-clause-analyzer/1"


def test_local_slm_cache_identity_bumps_on_parser_and_grounding_v12() -> None:
    common = dict(
        exact_input_text=NESTED_SIM_PROMPT,
        model_key="qwen3-0.6b-axov9",
        model_sha256="0" * 64,
        runtime_version=LOCAL_SLM_RUNTIME_VERSION,
        strategy="compact_clause",
        schema_version="slm-compact-clause/2",
        schema_sha256="1" * 64,
        capability_identity=compute_local_slm_capability_identity(),
        namespace=LOCAL_SLM_CACHE_NAMESPACE,
    )
    k_v11, meta_v11 = build_local_slm_cache_identity(
        **common,
        grounding_policy_version="slm-grounding-validator/5",
        parser_version="local-geometry-parser/2",
    )
    k_v12_parser, _ = build_local_slm_cache_identity(
        **common,
        grounding_policy_version="slm-grounding-validator/5",
        parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
    )
    k_v12_both, meta_v12 = build_local_slm_cache_identity(
        **common,
        grounding_policy_version=SLM_GROUNDING_VALIDATOR_V9_VERSION,
        parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
    )
    assert len(k_v11) == 64 and len(k_v12_both) == 64
    assert k_v11 != k_v12_parser
    assert k_v12_parser != k_v12_both
    assert meta_v11["parser_version"] == "local-geometry-parser/2"
    assert meta_v12["parser_version"] == "local-geometry-parser/3"
    assert meta_v12["grounding_policy_version"] == "slm-grounding-validator/6"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-only-scoped")
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with TestClient(M.app) as c:
        sign_in(c)
        yield c


def test_stale_146_route_d_row_misses_and_recomputes_under_147(client: TestClient) -> None:
    init_db()
    r1 = client.post("/api/analyze", json={"input": {"type": "text", "content": NESTED_SIM_PROMPT}})
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["route_d"]["status"] == "SERVED"

    with SessionLocal() as s:
        rows = (
            s.query(SimulationCache)
            .filter(SimulationCache.problem_text == NESTED_SIM_PROMPT)
            .all()
        )
        assert rows, "Expected SimulationCache row written for NESTED_SIM_PROMPT"
        target_key = rows[-1].key
        stale_payload = json.dumps(
            {
                "route_d": {"status": "REFUSED", "reason_code": "FACT_INCOMPLETE"},
                "stale_146_sentinel": True,
            },
            ensure_ascii=False,
        )
        for row in rows:
            row.policy_version = "146:route-d"
            row.envelope_json = stale_payload
        s.commit()

    try:
        r2 = client.post("/api/analyze", json={"input": {"type": "text", "content": NESTED_SIM_PROMPT}})
        assert r2.status_code == 200
        body2 = r2.json()
        assert body2.get("stale_146_sentinel") is None
        assert body2["route_d"]["status"] == "SERVED"

        with SessionLocal() as s:
            refreshed = s.query(SimulationCache).filter_by(key=target_key).first()
            assert refreshed is not None
            assert refreshed.policy_version == M.ROUTE_D_CACHE_POLICY
            assert "stale_146_sentinel" not in refreshed.envelope_json
    finally:
        with SessionLocal() as s:
            s.query(SimulationCache).filter(SimulationCache.problem_text == NESTED_SIM_PROMPT).delete()
            s.commit()
