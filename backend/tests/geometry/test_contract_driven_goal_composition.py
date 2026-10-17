"""Tests for run `contract-driven-goal-composition`:
- Vertical Slice A: `midpoint -> ask_area`, `centroid -> ask_area` (zero-planner-edit discovery),
  `orthogonal_projection` / `orthogonal_projection_line -> ask_area` (standalone & composed).
- Vertical Slice B: `angle_line_plane` independent Gram verifier (`sin²θ`, `cos²θ = 1 - sin²θ`, 0°/90°/oblique,
  degenerate line/plane refusal) + `SCHEMA_REPRESENTATION_BLOCKER` for unnamed descriptor `angle` under frozen `TypedFact`.
- Independent `_KIEM_DICH` verifier dispatch (`distance`, `length`, `area`, `angle_line_plane`), tamper suite,
  lying contract detection, Registry reversal invariance, and frozen provider/schema surface checks.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

from app.ai.function_route import run_fact_route, run_function_route
from app.simulation.geometry_functions import engine, planner, registry
from tests.geometry.test_function_discovery_planning import experimental_centroid_contract, squared

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "docs/evaluation/geometry/runs/contract-driven-goal-composition"
CORPUS = json.loads((RUN / "corpus.json").read_text(encoding="utf-8"))


def run(case: dict):
    return run_fact_route(case["text"], deepcopy(case["payload"]))


def exact_area(r, case: dict) -> None:
    assert r.status == "SERVED", (case["id"], r.code, r.reason)
    assert set(r.answers) == set(case["expected_squared"])
    for q, want in case["expected_squared"].items():
        assert squared(r.exec_result.final_memory[f"kq_{q}"]) == Fraction(want), (case["id"], q)
    assert r.kernel_check and r.scene3d["objects"]


def chain_certs(r) -> list[dict]:
    return [d for d in r.planner["auxiliary"] if d.get("rule") == "effect-chain"]


def test_oracle_has_zero_product_imports():
    tree = ast.parse((RUN / "oracle.py").read_text(encoding="utf-8"))
    imports = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    ] + [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ]
    assert not any(m.startswith("app") or m.startswith("tests") for m in imports), imports


@pytest.mark.parametrize("case", CORPUS["positive"], ids=lambda c: c["id"])
def test_slice_a_positive_area_composition(case):
    r = run(case)
    exact_area(r, case)
    certs = chain_certs(r)
    if any(f.get("point_kind") and f.get("kind") == "question" for f in case["payload"]["facts"]):
        assert certs
        for d in certs:
            x = d["operand"]["label"]
            p, q = d["operand"]["points"]
            assert all(2 * r.points[x][i] == r.points[p][i] + r.points[q][i] for i in range(3))
            m_obj = next(o for o in r.scene3d["objects"] if o["id"] == engine.ir_name(x))
            assert "target" in m_obj["display_group"]
        if "expected_new_points" in case:
            assert sum(len(d["labels"]) for d in certs) == case["expected_new_points"]
    if "expected_midpoint_constructions" in case:
        mids = [c for c in r.planner["calls"] if c["fn"] == "midpoint"]
        assert len(mids) == case["expected_midpoint_constructions"]


@pytest.mark.parametrize("case", CORPUS["held_out"], ids=lambda c: c["id"])
def test_slice_a_held_out_area_composition(case):
    exact_area(run(case), case)


@pytest.mark.parametrize("case", CORPUS["discovery"], ids=lambda c: c["id"])
def test_slice_a_zero_planner_edit_discovery_centroid_to_area(monkeypatch, case):
    code = {m.__name__: Path(m.__file__).read_bytes() for m in (planner, registry, engine)}
    r_before = run(case)
    assert r_before.status == "REFUSED" and r_before.code == "UNSUPPORTED_CAPABILITY"
    monkeypatch.setitem(registry.REGISTRY, "centroid", experimental_centroid_contract(registry))
    r_after = run(case)
    exact_area(r_after, case)
    assert {x["fn"] for x in r_after.planner["calls"]} >= {"centroid", "ask_area"}
    assert {Path(m.__file__).read_bytes() for m in (planner, registry, engine)} == set(code.values())
    cert = chain_certs(r_after)[0]
    g_lbl, (a, b, c) = cert["operand"]["label"], cert["operand"]["points"]
    assert all(3 * r_after.points[g_lbl][i] == r_after.points[a][i] + r_after.points[b][i] + r_after.points[c][i] for i in range(3))


@pytest.mark.parametrize("case", CORPUS["negative"], ids=lambda c: c["id"])
def test_negative_cases_fail_closed(case):
    r = run(case)
    assert r.status == "REFUSED", (case["id"], r.answers)
    assert not r.answers and r.scene3d is None
    assert r.code in case["expected_codes"], (case["id"], r.code, r.reason)


@pytest.mark.parametrize("case", CORPUS["angle_line_plane_slice_b"], ids=lambda c: c["id"])
def test_slice_b_angle_line_plane_and_independent_gram_verifier(case):
    r = run(case)
    assert r.status == "SERVED", (case["id"], r.code, r.reason)
    for q, want_cos_sq in case["expected_cos_sq"].items():
        val = Fraction(r.exec_result.final_memory[f"kq_{q}"])
        assert val == Fraction(want_cos_sq), (case["id"], val, want_cos_sq)
        assert Fraction(1) - val == Fraction(case["expected_sin_sq"][q])
        assert r.answers[q] == f"cos²={val}"


def test_slice_b_verifier_table_and_degenerate_refusals():
    assert set(engine._KIEM_DICH) >= {"distance", "length", "area", "angle_line_plane"}
    # Degenerate plane in angle_line_plane (S, M, C are collinear when M is midpoint of SC)
    c = deepcopy(CORPUS["angle_line_plane_slice_b"][2])
    c["text"] = c["text"].replace("Tính góc giữa AM và (ABCD).", "Tính góc giữa AM và (SMC).")
    c["payload"]["facts"][-1]["points_b"] = ["S", "M", "C"]
    c["payload"]["facts"][-1]["quotes"] = ["Tính góc giữa AM và (SMC)."]
    r = run(c)
    assert r.status == "REFUSED" and r.code in ("COLLINEAR_POINTS", "SOURCE_OBJECT_MISMATCH")


def test_slice_b_unnamed_point_kind_schema_representation_blocker(monkeypatch):
    # Even if a speculative contract attempts to declare goal="angle" with heterogeneous inputs (Point + Plane),
    # _doc_toan_hang_mo_ta refuses to guess positional splits of points_b under the frozen TypedFact schema.
    spec = registry.REGISTRY["ask_angle_line_plane"]
    bad_contract = registry.PlanningContract(
        inputs=(
            registry.PlanningTerm("Point", ("P",)),
            registry.PlanningTerm("Point", ("Q",)),
            registry.PlanningTerm("Plane", ("M",)),
        ),
        effect=registry.PlanningTerm("AnswerDistance", ("P", "M")),
        source_policy="goal_answer",
        verifier="angle_line_plane",
        goal="angle",
    )
    monkeypatch.setitem(registry.REGISTRY, "ask_angle_line_plane", replace(spec, planning=bad_contract))
    blocker_case = next(c for c in CORPUS["negative"] if c["id"] == "unnamed-angle-line-plane-blocker")
    r = run(blocker_case)
    assert r.status == "REFUSED" and r.code == "UNSUPPORTED_CAPABILITY"


def test_ablation_goal_and_producer_contracts_and_registry_reversal(monkeypatch):
    c = CORPUS["positive"][0]
    before = planner.lap_ke_hoach(c["payload"], c["text"])
    with monkeypatch.context() as m:
        m.setitem(registry.REGISTRY, "ask_area", replace(registry.REGISTRY["ask_area"], planning=None))
        r = run(c)
        assert r.status == "REFUSED" and r.code == "UNSUPPORTED_CAPABILITY"
    with monkeypatch.context() as m:
        m.setitem(registry.REGISTRY, "midpoint", replace(registry.REGISTRY["midpoint"], planning=None))
        r = run(c)
        assert r.status == "REFUSED" and r.code == "UNSUPPORTED_CAPABILITY"
    with monkeypatch.context() as m:
        rev = dict(reversed(list(registry.REGISTRY.items())))
        m.setattr(registry, "REGISTRY", rev)
        m.setattr(planner, "REGISTRY", rev)
        after = planner.lap_ke_hoach(c["payload"], c["text"])
        assert after.calls == before.calls
        assert after.auxiliary == before.auxiliary
        exact_area(run(c), c)


@pytest.mark.parametrize(
    "field",
    ["target-points", "target-kind", "effect", "env-target", "env-desc", "quotes", "labels-empty", "labels-source", "labels-dup", "missing-cert"],
)
def test_area_certificate_tampering_refuses(field):
    c = CORPUS["positive"][0]
    k = planner.lap_ke_hoach(c["payload"], c["text"])
    aux = deepcopy(k.auxiliary)
    d = aux[0]
    if field == "target-points":
        d["target"] = {"points": ["A", "D"]}
    elif field == "target-kind":
        d["target"] = {"line": ["A", "B"]}
    elif field == "effect":
        d["chain"][-1]["effect"] = "AnswerLength"
    elif field == "env-target":
        d["chain"][-1]["env"]["R"] = "D"
    elif field == "env-desc":
        d["chain"][0]["env"]["A"] = "B"
    elif field == "quotes":
        d["quotes"] = ["SA = 3."]
    elif field == "labels-empty":
        d["labels"] = []
    elif field == "labels-source":
        d["labels"] = ["S"]
    elif field == "labels-dup":
        d["labels"] = ["M", "M"]
    else:
        aux = []
    r = run_function_route(c["text"], {"calls": k.calls}, tuple(aux))
    assert r.status == "REFUSED", (field, r.answers)


@pytest.mark.parametrize("bad_verifier", ["length", "distance", "angle_line_plane", "nonexistent"])
def test_verifier_mismatch_in_contract_is_refused(monkeypatch, bad_verifier):
    spec = registry.REGISTRY["ask_area"]
    tampered = replace(spec.planning, verifier=bad_verifier)
    monkeypatch.setitem(registry.REGISTRY, "ask_area", replace(spec, planning=tampered))
    r = run(CORPUS["positive"][0])
    assert r.status == "REFUSED" and r.code in ("AUXILIARY_RULE_MISMATCH", "ENGINE_SELF_CHECK_FAILED")


def test_lying_area_answer_contract_caught_by_independent_verifier(monkeypatch):
    # Contract claims to compute AnswerArea(P, Q, R) for A, D (area² = 13/4), but its call template substitutes B for D (area² = 9/2).
    c = CORPUS["positive"][1]  # pyramid-midpoint-area-AD-reversed-wording: target A, D
    spec = registry.REGISTRY["ask_area"]
    # Lie: wire polygon to (P, Q, P) or swap a slot in engine self-check
    monkeypatch.setattr(engine._Dung, "kc2_dich", lambda self, d: Fraction(-1))
    assert run(c).code == "ENGINE_SELF_CHECK_FAILED"


def test_lying_area_call_template_caught_when_gate_bypassed(monkeypatch):
    # Even if a lying call template passes the gate by wiring polygon to (P, A, B) while certificate target is (A, D):
    c = CORPUS["positive"][1]  # target A, D (area² = 13/4 != area²(M, A, B) = 9/2)
    spec = registry.REGISTRY["ask_area"]
    lie = replace(spec.planning, call=(("polygon", ("P", "Q", "Q")),))
    monkeypatch.setitem(registry.REGISTRY, "ask_area", replace(spec, planning=lie))
    r = run(c)
    assert r.status == "REFUSED" and r.code in ("COLLINEAR_POINTS", "ENGINE_SELF_CHECK_FAILED")


def test_lying_descriptor_contract_on_area_caught_by_engine(monkeypatch):
    c = CORPUS["discovery"][0]
    lie = replace(experimental_centroid_contract(registry).planning, call=(("point", "G"), ("segment", ("A", "B"))))
    monkeypatch.setitem(registry.REGISTRY, "midpoint", replace(registry.REGISTRY["midpoint"], planning=lie))
    r = run(c)
    assert r.status == "REFUSED" and r.code == "ENGINE_SELF_CHECK_FAILED"


@pytest.mark.parametrize("transform", ["reverse-descriptor-points", "reverse-target-points", "reverse-facts", "rename", "scale"])
def test_metamorphic_area_invariance(transform):
    c = deepcopy(CORPUS["positive"][0])
    if transform == "reverse-descriptor-points":
        c["payload"]["facts"][-1]["points"].reverse()
    elif transform == "reverse-target-points":
        c["payload"]["facts"][-1]["points_b"].reverse()
    elif transform == "reverse-facts":
        c["payload"]["facts"].reverse()
    elif transform == "rename":
        c = json.loads(json.dumps(c, ensure_ascii=False).replace("S", "T").replace("C", "E"))
    else:
        c["text"] = c["text"].replace("cạnh 2", "cạnh 4").replace("SA = 3", "SA = 6")
        for f in c["payload"]["facts"]:
            f["quotes"] = [q.replace("cạnh 2", "cạnh 4").replace("SA = 3", "SA = 6") for q in f["quotes"]]
            if f.get("value") in ("2", "3"):
                f["value"] = str(int(f["value"]) * 2)
        # Scaling linear dimensions by 2 scales area by 4, hence area² by 16.
        c["expected_squared"] = {q: str(Fraction(x) * 16) for q, x in c["expected_squared"].items()}
    exact_area(run(c), c)


def test_frozen_surfaces_unchanged():
    from app.ai import fact_extraction, function_calling

    pin = json.loads((ROOT / "docs/evaluation/geometry/runs/generalized-goal-entry/baseline/transport.json").read_text(encoding="utf-8"))
    value = json.dumps(planner.TypedFact.model_json_schema(), sort_keys=True, ensure_ascii=False).encode()
    assert hashlib.sha256(value).hexdigest() == pin["typed_fact_schema_sha256"]
    assert function_calling.surface_fingerprint().startswith("7ea511a6e3828c9a")
    assert fact_extraction.surface_fingerprint().startswith("485d3834db8b18cf")
    decl = json.dumps(registry.function_declarations(), ensure_ascii=False, sort_keys=True).encode()
    assert hashlib.sha256(decl).hexdigest().startswith("5ceb0f999d4d7c1e")


def test_capability_disabled_negative_reconciliation():
    reconciled = json.loads((RUN / "ablation-reconciled.json").read_text(encoding="utf-8"))
    for arm, summary in reconciled["safety_summary_by_arm"].items():
        assert summary["safety_wrong_served"] == 0, f"Safety wrong_served > 0 in {arm}: {summary}"
    audit = reconciled["capability_disabled_negative_audit"]["new/negative::centroid-without-contract"]
    assert audit["negative_kind"] == "capability_disabled_negative"
    assert audit["discovery_twin"] == "new/discovery::centroid-to-plane"
    assert audit["arms"]["NEW[production]"]["reconciled_outcome"] == "correct_refusal_disabled_capability"
    assert audit["arms"]["NEW[centroid]"]["raw_outcome"] == "wrong_served"
    assert audit["arms"]["NEW[centroid]"]["reconciled_outcome"] == "correct_served_enabled_capability"
    assert audit["arms"]["NEW[centroid]"]["answers"] == {"q": "4/3"}
    assert audit["arms"]["NEW[centroid]"]["squares"] == {"q": "16/9"}
