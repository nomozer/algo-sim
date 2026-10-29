"""Tests for W3-F1 Cross-Sentence Plane Grounding (Registry /20, Planner /18).

Covers:
1. Grounded Cross-Sentence Plane Reference Resolution across all 3 plane families:
   - through_point_parallel_plane
   - through_point_perpendicular_line
   - through_point_parallel_two_lines
2. Question types:
   - section_only
   - area_only
   - section_and_area (compound question grounding across sentences)
3. Latin and Greek plane names ((P), (Q), (α), (β), (γ), (Ω)) and primed prism vertices.
4. All 24 isolated W3-F1 positive cases, 24 newly authored cross-sentence positive cases,
   and 20 mandatory adversarial tamper / fail-closed cases from the W3-F1 development corpus.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

from app.ai.adapter4_route import (
    ADAPTER_V4_VERSION,
    build_adapter4_response,
    run_typed_fact_next_v2_route,
)
from app.simulation.geometry_functions import engine, planner, registry

REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = (
    REPO_ROOT
    / "docs"
    / "evaluation"
    / "geometry"
    / "runs"
    / "hybrid-v2-w3-f1-cross-sentence-plane-grounding"
)


def _load_dev_and_oracle() -> tuple[dict, dict]:
    dev_doc = json.loads((RUN_DIR / "inputs" / "development.json").read_text(encoding="utf-8"))
    oracle_doc = json.loads((RUN_DIR / "inputs" / "oracle.json").read_text(encoding="utf-8"))
    return dev_doc, oracle_doc


def _eval_payload(payload: dict):
    r = run_typed_fact_next_v2_route(payload)
    resp = build_adapter4_response(r, payload["problem_text"])
    rd = resp.get("route_d") or {}
    env = resp.get("envelope") or {}
    served = r.status == "SERVED" and rd.get("status") == "SERVED" and env.get("status") == "ok"
    code = None if served else ((rd.get("refusal") or {}).get("code") or r.code)
    return r, served, code, resp


def _assert_area_matches_oracle(r, resp: dict, payload: dict, ora: dict, stratum: str) -> None:
    sec = resp["route_d"]["sections"][0]
    if stratum == "P-B":
        assert sec["certificate_category"] == "ENGINE_DERIVED_SECTION"
        cert = sec["closure_certificate"]
        assert cert is not None and cert["verified"] is True
        assert Fraction(cert["area_squared"]) == Fraction(ora["area_squared"])
    else:
        assert "certificate_category" not in sec
        assert sec["closure_certificate"] is None
    if payload.get("math_goals"):
        gid = payload["math_goals"][0]["goal_id"]
        val = r.exec_result.final_memory[f"kq_{gid}"]
        area_sq = Fraction(val.he) ** 2 * val.can if hasattr(val, "can") else Fraction(val) ** 2
        assert area_sq == Fraction(ora["area_squared"])


def test_w3_f1_versions_and_engine_unchanged() -> None:
    assert registry.REGISTRY_VERSION == "geometry-functions/21"
    assert planner.PLANNER_VERSION == "geometry-fact-planner/18"
    assert engine.ENGINE_VERSION == "geometry-function-engine/14"
    assert ADAPTER_V4_VERSION == "hybrid-simulation-adapter/4"
    assert engine.PLANE_SECTION_CERTIFICATE_VERSION == "plane-section-certificate/1"


def test_w3_f1_pure_historical_and_isolated_24_positive_cases() -> None:
    dev_doc, oracle_doc = _load_dev_and_oracle()
    oracles = {o["id"]: o for o in oracle_doc["cases"]}

    pure_cases = [
        c
        for c in dev_doc["cases"]
        if c["slice"] == "historical_w3_f1_verbatim" and not c.get("has_secondary_out_of_scope_defect")
    ]
    assert len(pure_cases) == 9
    for c in pure_cases:
        r, served, code, resp = _eval_payload(c["payload"])
        assert served, f"{c['id']} should be SERVED_CORRECT, got {code}"
        _assert_area_matches_oracle(r, resp, c["payload"], oracles[c["id"]], c["stratum"])

    isolated_cases = [c for c in dev_doc["cases"] if c["slice"] == "w3_f1_isolated_24"]
    assert len(isolated_cases) == 24
    for c in isolated_cases:
        r, served, code, resp = _eval_payload(c["payload"])
        assert served, f"{c['id']} should be SERVED_CORRECT, got {code}"
        _assert_area_matches_oracle(r, resp, c["payload"], oracles[c["id"]], c["stratum"])


def test_w3_f1_authored_cross_sentence_positive_24_cases() -> None:
    dev_doc, oracle_doc = _load_dev_and_oracle()
    oracles = {o["id"]: o for o in oracle_doc["cases"]}

    authored_cases = [c for c in dev_doc["cases"] if c["slice"] == "authored_cross_sentence_positive"]
    assert len(authored_cases) == 24
    for c in authored_cases:
        r, served, code, resp = _eval_payload(c["payload"])
        assert served, f"{c['id']} ({c.get('variation')}) should be SERVED_CORRECT, got {code}"
        _assert_area_matches_oracle(r, resp, c["payload"], oracles[c["id"]], c["stratum"])


@pytest.mark.parametrize("neg_index", range(20))
def test_w3_f1_mandatory_20_negative_tamper_cases(neg_index: int) -> None:
    dev_doc, _ = _load_dev_and_oracle()
    neg_cases = [c for c in dev_doc["cases"] if c["slice"] == "mandatory_negative_tamper"]
    assert len(neg_cases) == 20
    c = neg_cases[neg_index]
    _r, served, code, _ = _eval_payload(c["payload"])
    assert not served, f"{c['id']} ({c['negative_class']}) must fail closed, but was SERVED"
    assert code in c["expected_codes"], (
        f"{c['id']} ({c['negative_class']}) expected code in {c['expected_codes']}, got {code}"
    )
