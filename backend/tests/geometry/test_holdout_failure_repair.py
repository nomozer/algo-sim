# -*- coding: utf-8 -*-
"""Regression and contract tests for `HYBRID_V2_HOLDOUT_FAILURE_REPAIR` (M1–M5 + R2).

Tests the 32-case development corpus (`D001..D016` positive + `N001..N016` negative/adversarial)
against the independent `Fraction` oracle (`new_dev_oracle.py`), plus targeted unit tests for
each repair cluster M1–M5 and R2 Scene3D auxiliary-point label hygiene.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "docs/evaluation/geometry/runs/hybrid-v2-holdout-failure-repair"
CORPUS_PATH = RUN_DIR / "new-development-corpus.json"
sys.path.insert(0, str(RUN_DIR / "oracle"))

from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route  # noqa: E402
from app.simulation.geometry_functions.planner import PLANNER_VERSION, TypedFact  # noqa: E402
from app.simulation.geometry_functions.registry import REGISTRY_VERSION  # noqa: E402
from new_dev_oracle import ORACLE_TABLE  # noqa: E402


LOCKED_TYPED_FACT_SCHEMA_SHA256 = "aa9d93eeac9f1659af8e5acd42af1904b7aaed674a8ab0f56f0c7dd8b2ad4ee8"

_CORPUS = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
_POS_CASES = [c for c in _CORPUS["cases"] if c["expected_status"] == "SERVED"]
_NEG_CASES = [c for c in _CORPUS["cases"] if c["expected_status"] == "REFUSED"]


def _square(v) -> Fraction:
    if hasattr(v, "he") and hasattr(v, "can"):
        return Fraction(v.he) ** 2 * Fraction(v.can)
    return Fraction(v) ** 2


def _eval_case(payload: dict) -> tuple[object, dict, bool, str | None]:
    p = deepcopy(payload)
    r = run_typed_fact_next_v2_route(p)
    resp = build_adapter4_response(r, p["problem_text"])
    rd = resp.get("route_d") or {}
    env = resp.get("envelope") or {}
    served = r.status == "SERVED" and rd.get("status") == "SERVED" and env.get("status") == "ok"
    code = None if served else ((rd.get("refusal") or {}).get("code") or r.code)
    return r, resp, served, code


def test_versions_and_locked_typed_fact_json_schema():
    """M1: Runtime accepts Greek plane_name while TypedFact JSON schema hash stays locked."""
    assert REGISTRY_VERSION == "geometry-functions/18"
    assert PLANNER_VERSION == "geometry-fact-planner/17"
    schema_bytes = json.dumps(TypedFact.model_json_schema(), sort_keys=True, ensure_ascii=False).encode("utf-8")
    assert hashlib.sha256(schema_bytes).hexdigest() == LOCKED_TYPED_FACT_SCHEMA_SHA256

    # Greek plane_name is accepted at runtime
    fact = TypedFact(
        id="sec1",
        kind="section",
        role="premise",
        solid="S.ABC",
        point="M",
        plane_relation="parallel",
        points_b=["A", "B", "C"],
        plane_name="α",
        quotes=["Mặt phẳng (α) qua M và song song với (ABC)"],
    )
    assert fact.plane_name == "α"

    # Greek symbol on point/vertex Label is still rejected
    with pytest.raises(ValidationError):
        TypedFact(
            id="p1",
            kind="point_def",
            role="premise",
            point_kind="midpoint",
            point="α",
            points=["S", "A"],
            quotes=["α là trung điểm của SA"],
        )


@pytest.mark.parametrize("case", _POS_CASES, ids=[c["id"] for c in _POS_CASES])
def test_development_corpus_positive_cases_and_exact_oracle(case: dict):
    cid = case["id"]
    oracle = ORACLE_TABLE[cid]
    r, resp, served, code = _eval_case(case["payload"])
    assert served, f"{cid} refused with {code}: {r.reason}"

    rd = resp["route_d"]
    secs = rd.get("sections") or []
    assert len(secs) == 1
    sec0 = secs[0]
    assert len(sec0["vertices"]) == oracle["polygon_vertices"]
    assert sec0.get("certificate_category", "DINH_CAT_CANH") == oracle["certificate_category"]

    if oracle.get("area_sq") is not None:
        assert r.answers, f"{cid} missing scalar answer"
        goal_id = next(iter(r.answers.keys()))
        got_sq = _square(r.exec_result.final_memory[f"kq_{goal_id}"])
        assert got_sq == oracle["area_sq"]
        assert r.answers[goal_id] == oracle["expected_answer"]


@pytest.mark.parametrize("case", _NEG_CASES, ids=[c["id"] for c in _NEG_CASES])
def test_development_corpus_negative_cases_fail_closed(case: dict):
    cid = case["id"]
    r, resp, served, code = _eval_case(case["payload"])
    assert not served, f"{cid} was unexpectedly SERVED!"
    assert code in case["expected_codes"], f"{cid} got {code}, expected one of {case['expected_codes']} ({r.reason})"


@pytest.mark.parametrize("case", _POS_CASES, ids=[c["id"] for c in _POS_CASES])
def test_scene3d_section_plane_and_polygon_label_hygiene(case: dict):
    """Verify Scene3D section/plane/answer label hygiene and source-point preservation under the locked O4/R1/B contracts."""
    cid = case["id"]
    oracle = ORACLE_TABLE[cid]
    r, resp, served, code = _eval_case(case["payload"])
    assert served, f"{cid} refused with {code}: {r.reason}"

    scene = resp["envelope"]["scene3d"]
    text = case["payload"]["problem_text"]
    objs_by_id = {o["id"]: o for o in scene["objects"]}

    if oracle.get("source_has_H"):
        assert "H" in objs_by_id
        assert objs_by_id["H"].get("notation") == "H"

    aux = set()
    for d in (r.planner or {}).get("auxiliary") or []:
        aux |= set(d.get("labels") or []) | set(d.get("feet") or [])
    unmentioned_aux = {
        a for a in aux
        if isinstance(a, str) and not re.search(rf"(?<![\w']){re.escape(a)}(?![\w'])", text)
    }

    # Unmentioned auxiliary points are never marked 'given'; planes, sections, and quantities never leak auxiliary labels
    leaks = []
    for o in scene.get("objects") or []:
        if o["id"] in unmentioned_aux:
            assert "given" not in (o.get("display_group") or []), f"{cid}: {o['id']} marked as given"
        if o.get("type") in ("plane3", "polygon3", "quantity"):
            for key in ("name", "label", "display_label", "notation", "reference"):
                s = o.get(key)
                if isinstance(s, str):
                    for a in unmentioned_aux:
                        if re.search(rf"(?<![\w']){re.escape(a)}(?![\w'])", s):
                            leaks.append(f"{o.get('id')}.{key}:{a}")
            f_txt = (o.get("formula") or {}).get("text")
            if isinstance(f_txt, str):
                for a in unmentioned_aux:
                    if re.search(rf"(?<![\w']){re.escape(a)}(?![\w'])", f_txt):
                        leaks.append(f"{o.get('id')}.formula.text:{a}")
    assert not leaks, f"{cid} leaked unmentioned auxiliary labels in plane/section/quantity fields: {leaks}"


def test_math_goal_area_solid_id_mismatch_refused():
    from copy import deepcopy
    base_case = next(c for c in _POS_CASES if c["id"] == "D001")
    bad = deepcopy(base_case["payload"])
    bad["math_goals"][0]["solid_id"] = "s99"
    r, resp, served, code = _eval_case(bad)
    assert not served
    assert code == "UNKNOWN_SOLID_ID"
