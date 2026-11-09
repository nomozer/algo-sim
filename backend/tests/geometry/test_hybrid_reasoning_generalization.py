# -*- coding: utf-8 -*-
"""Run `hybrid-reasoning-generalization`: gaps found by the development matrix (`tools/reasoning_matrix.py` in the run
directory), each driven through the real offline product path (`run_hybrid_offline`: verbatim quotes → bridge_v2 →
Source Gate → planner → engine → Adapter /4). Expected values are the case's independent-oracle values
(`docs/evaluation/geometry/custodian/geometry_oracle.py`, hand rational coordinates) — never product output.

Fixed here:
- G1a  a triangle base side from Pythagoras over a right angle stated OUTSIDE the base, or stated as two perpendicular
       segments sharing an endpoint (`perpendicular_lines`) — "tứ diện OABC có OA, OB, OC đôi một vuông góc".
- G1b  a pyramid apex fixed by three lateral edge lengths over a placed base (exact trilateration in the affine chart).
- G5   a planner-written foot shared by a `distance(point,line)` decomposition and an `effect-chain` goal: the chain
       verifier now counts the quotes of every certificate that names the construct, as `_kiem_phu` already does.
Reproduced, not fixed (strict xfail): G6 (three defined points: search budget, then the IR memory budget — contract);
G2/G3/G4/G7 (bridge contract — proposal in the run report).
"""
from __future__ import annotations

import copy
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.typed_fact_next_extraction import ReplayExtractor
from app.simulation.geometry_functions import engine, planner, typed_fact_next as TN
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2

_TOOLS = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-reasoning-generalization/tools"
sys.path.insert(0, str(_TOOLS))
import reasoning_matrix as RM  # noqa: E402  (read-only: case payloads + oracle expectations)

POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
CASES = {c["id"]: c for c in RM.build_cases()}


def _run(text, payload):
    out = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
    route, env = out.response["route_d"], out.response["envelope"]
    answers = {k: v["coef"] for k, v in (route.get("answer_exact") or {}).items()} if route["status"] == "SERVED" else {}
    return route, env, answers


def _assert_oracle(cid):
    c = CASES[cid]
    route, env, answers = _run(c["text"], c["payload"])
    assert route["status"] == "SERVED", (cid, env.get("reason_code"))
    for g, (meas, want) in c["expect"][1].items():
        got = Fraction(answers[g]) if meas == "cos2" else RM.coef_square(answers[g])
        assert got == want, (cid, g, answers[g], want)
    assert validate_construction_continuity(env["scene3d"]) == []
    return route, env, answers


def _refused(cid_or_case, codes):
    c = CASES[cid_or_case] if isinstance(cid_or_case, str) else cid_or_case
    route, env, _a = _run(c["text"], c["payload"])
    assert route["status"] == "REFUSED" and env.get("reason_code") in codes, env.get("reason_code")


# ── G1: trirectangular tetrahedron and apex by three lateral edges ───────────────────────────────────────────────────

@pytest.mark.parametrize("cid", ["PE2", "PE3", "PE4", "PE5", "PE6", "RE3"])
def test_g1_trirectangular_tetrahedron_is_served_exactly(cid):
    """`tứ diện OABC, OA, OB, OC đôi một vuông góc, OA = 1, OB = 2, OC = 3` in both apex readings (O.ABC — the extraction
    convention — and A.OBC): distance O→(ABC) (36/49), dihedral, point–line, volume (1), orthocenter of ABC = foot of O."""
    route, _env, _a = _assert_oracle(cid)
    if cid in ("PE2", "PE5"):
        assert route["planner"]["calls"][-1]["fn"] == "ask_distance_point_plane"


@pytest.mark.parametrize("cid", ["PY1", "PY2"])
def test_g1b_pyramid_apex_fixed_by_three_lateral_edges(cid):
    """S.ABC, base right at A (3, 4), SA = SB = SC = 13/2 ⇒ apex over mid(BC) at height 6 (oracle frame asserted)."""
    _assert_oracle(cid)


def test_g1_negatives_stay_fail_closed():
    _refused("N8", {"INCONSISTENT_FACTS"})          # AB = 3 contradicts OA ⊥ OB with OA = 1, OB = 2
    _refused("N9", {"MISSING_DIMENSION", "UNDERDETERMINED_POINT"})   # OC not given
    _refused("N10", {"INCONSISTENT_FACTS"})         # lateral edges shorter than the base circumradius


def test_g1_fault_injection_two_perpendicular_pairs_do_not_fix_the_base():
    """Drop OA ⊥ OC: AC is no longer derivable — the base stays undetermined (never guessed)."""
    c = copy.deepcopy(CASES["PE2"])
    c["payload"]["premises"] = [p for p in c["payload"]["premises"]
                                if p["args"].get("line2") != ["O", "C"] or p["args"].get("line1") != ["O", "A"]]
    assert len(c["payload"]["premises"]) == 5
    _refused(c, {"MISSING_DIMENSION", "UNDERDETERMINED_POINT"})


def test_g1_fault_injection_perpendicular_lines_without_a_shared_endpoint_are_no_right_angle():
    """Replace the extracted OA ⊥ OB by a stated OA ⊥ BC: two segments without a shared endpoint state no right angle
    of a triangle and must not be read as Pythagoras for AB — the base stays undetermined (fail-closed, never guessed)."""
    c = copy.deepcopy(CASES["PE2"])
    c["text"] = c["text"].replace("OA = 1", "OA vuông góc với BC, OA = 1")
    c["payload"]["problem_text"] = c["text"]
    for p in c["payload"]["premises"]:
        if p["kind"] == "perpendicular_lines" and p["args"]["line1"] == ["O", "A"] and p["args"]["line2"] == ["O", "B"]:
            p["args"]["line2"], p["quote"] = ["B", "C"], "OA vuông góc với BC"
    _refused(c, {"MISSING_DIMENSION", "UNDERDETERMINED_POINT"})


def test_g1_layout_is_unchanged_where_the_base_was_already_determined():
    """Control: the square-pyramid frame (all base sides known before) keeps its layout rules and answers."""
    for cid in ("PP1", "PL1", "AN2", "PR1", "PR4"):
        _assert_oracle(cid)


# ── G5: one foot, two goals (decomposition + effect-chain) ───────────────────────────────────────────────────────────

def test_g5_goal_only_foot_reused_by_a_described_point_goal():
    route, _env, _a = _assert_oracle("MG7")
    assert [c["fn"] for c in route["planner"]["calls"]].count("orthogonal_projection_line") == 1


def _plan_and_check(c, mutate):
    text = c["text"]
    k = planner.lap_ke_hoach(bridge_v2(TN._parse(TN.TypedFactNextPayloadV2, c["payload"])), text)
    aux = mutate(copy.deepcopy(k.auxiliary))
    doc = tuple(q for g in (*k.goals, *k.negated) if g.get("call") for q in g["call"]["source"]["quotes"])
    return engine.dung_tu_loi_goi(text, {"calls": k.calls, "named_planes": k.named_planes}, tuple(aux), doc)


def test_g5_fault_injection_chain_alone_cannot_vouch_for_a_foreign_quote():
    """Remove the decomposition certificate that binds the foot to q1: the chain's own quote must not cover the foot."""
    r = _plan_and_check(CASES["MG7"], lambda aux: [d for d in aux if d.get("rule") != "distance(point,line)"])
    assert r.status == "REFUSED" and r.code == "AUXILIARY_RULE_MISMATCH"


def test_g5_fault_injection_decomposition_certificate_with_a_wrong_quote_is_refused():
    def forge(aux):
        for d in aux:
            if d.get("rule") == "distance(point,line)":
                d["quotes"] = ["Tính độ dài đoạn thẳng nối hình chiếu vuông góc của A lên SC với S"]
        return aux
    r = _plan_and_check(CASES["MG7"], forge)
    assert r.status == "REFUSED"


# ── G6: three property-defined points in one problem — budget, NOT fixed (evidence: a second, contract bound) ───────

@pytest.mark.xfail(strict=True, reason="G6: the effect-search candidate budget (48) is per PROBLEM; three definitions need "
                   "≈54. A per-goal budget was tried and reverted: the plan then needs 34 IR memory declarations > "
                   "semantic_program MAX_MEMORY_DECLARATIONS = 32 (IR_MEMORY_BUDGET_EXCEEDED) — a contract bound")
def test_g6_three_defined_points_in_one_problem():
    _assert_oracle("MG9")


def test_g6_three_defined_points_fail_closed_on_the_search_budget():
    c = CASES["MG9"]
    route, env, _a = _run(c["text"], c["payload"])
    assert route["status"] == "REFUSED" and env["reason_code"] == "PLAN_TOO_LARGE"


@pytest.mark.parametrize("bound,value", [("MAX_EFFECT_CANDIDATES", 8), ("MAX_EFFECT_NEEDS", 20)])
def test_g6_one_goal_over_budget_exhausts(monkeypatch, bound, value):
    """Control: a single orthocenter goal (17 candidates, 24 needs) fails closed under a smaller bound — search is bounded."""
    monkeypatch.setattr(planner, bound, value)
    c = CASES["RE1"]
    route, env, _a = _run(c["text"], c["payload"])
    assert route["status"] == "REFUSED" and env["reason_code"] == "PLAN_TOO_LARGE"


# ── reproduced contract-level gaps (bridge), not fixed in this run ───────────────────────────────────────────────────

_BRIDGE_GAPS = {
    "PL5": "G2: described point inside the `line` operand of a distance goal (bridge has no goal contract for it)",
    "PA3": "G2: described point inside the `line` operand of a line–plane distance",
    "MG5": "G3: two described points in one goal (bridge: no source certificate)",
    "SE3": "G4: three-point plane named by the source '(Q)' is renamed '(MNP)' by the bridge; the gate then rejects '(Q)'",
    "RE10": "G7: a description nested through a property-defined point (bridge: no source certificate)",
}


@pytest.mark.parametrize("cid", [pytest.param(c, marks=pytest.mark.xfail(strict=True, reason=r))
                                 for c, r in _BRIDGE_GAPS.items()])
def test_bridge_level_gap_reproduction(cid):
    _assert_oracle(cid)


@pytest.mark.parametrize("cid", list(_BRIDGE_GAPS))
def test_bridge_level_gaps_fail_closed_with_a_typed_refusal(cid):
    c = CASES[cid]
    route, env, _a = _run(c["text"], c["payload"])
    assert route["status"] == "REFUSED"
    assert env["reason_code"] in {"BRIDGE_UNSUPPORTED_DESCRIBED_POINT", "SOURCE_OBJECT_MISMATCH"}
