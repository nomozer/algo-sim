"""Locked development corpus through the real fact route, never a direct-IR serve."""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

from app.ai.function_route import run_fact_route

ROOT = Path(__file__).resolve().parents[3]
CORPUS_PATH = ROOT / "docs/evaluation/geometry/runs/goal-directed-planner-generalization-audit/next-slice-corpus.json"
CORPUS = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


def squared(value):
    from app.simulation.geometry.radical import Radical
    return Fraction(value.he) ** 2 * value.can if isinstance(value, Radical) else Fraction(value) ** 2


@pytest.mark.parametrize("case", CORPUS["positive"], ids=lambda c: c["id"])
def test_locked_positive_real_route(case):
    r = run_fact_route(case["text"], case["payload"])
    assert r.status == "SERVED", (r.code, r.reason)
    asks = [f["id"] for f in case["payload"]["facts"] if f["kind"] == "question"]
    assert set(r.answers) == set(asks)
    for q in asks:
        assert squared(r.exec_result.final_memory[f"kq_{q}"]) == Fraction(case["expected_squared"])
    assert r.kernel_check and r.scene3d["objects"]
    statements = r.program["statements"]
    lines = [s for s in statements if s.get("expr", {}).get("kind") == "intersect_plane_plane"]
    feet = [s for s in statements if s.get("expr", {}).get("kind") == "project_onto" and s.get("kind") == "construct_point"]
    assert len(lines) == len(feet) == 1
    assert feet[0]["expr"]["target"] == lines[0]["target_var"]
    assert statements.index(lines[0]) < statements.index(feet[0])


@pytest.mark.parametrize("case", CORPUS["negative"], ids=lambda c: c["id"])
def test_locked_negative_fail_closed(case):
    r = run_fact_route(case["text"], case["payload"])
    assert r.status == "REFUSED", (r.answers, case["id"])
    expected = case["expected_code"]
    if expected == "closed source refusal":
        assert r.code in {"SOURCE_PREMISE_UNREAD", "SOURCE_OBJECT_MISMATCH", "LOCAL_SOURCE_BINDING_UNVERIFIED"}
    elif expected == "dependency cycle refusal":
        assert r.code == "DEPENDENCY_CYCLE"
    else:
        assert r.code == expected
    assert not r.answers and r.scene3d is None
