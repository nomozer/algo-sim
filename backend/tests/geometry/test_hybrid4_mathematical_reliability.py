"""Development regression corpus with independent exact textbook oracles, not a live NLU/holdout claim."""
import importlib.util
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.typed_fact_next_extraction import ReplayExtractor

_PATH = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/axo-final-mathematical-reliability/tools/mathematical_probe.py"
_SPEC = importlib.util.spec_from_file_location("mathematical_reliability", _PATH)
CORPUS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(CORPUS)

REFUSALS = {
    "oblique-prism": ("UNDERDETERMINED_POINT", "insufficient_specification"),
    "pyramid-base-area": ("BRIDGE_UNSUPPORTED_PREMISE", "capability_gap"),
    "contradiction": ("INCONSISTENT_FACTS", "geometry_generation_failed"),
    "exact-domain": ("EXACT_DOMAIN_EXCEEDED", "capability_gap"),
}


@pytest.mark.parametrize("cid,payload,oracle,math_class,derivation", CORPUS.cases(), ids=[c[0] for c in CORPUS.cases()])
def test_source_gate_kernel_and_adapter_agree_with_independent_oracle(cid, payload, oracle, math_class, derivation):
    result = run_typed_fact_next_v2_route(payload)
    response = build_adapter4_response(result, payload["problem_text"])
    replay = run_hybrid_offline(payload["problem_text"], ReplayExtractor({payload["problem_text"]: payload}),
                                policy=hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})).response
    assert replay == response
    route, envelope = response["route_d"], response["envelope"]
    if cid in REFUSALS:
        code, category = REFUSALS[cid]
        assert result.status == route["status"] == "REFUSED"
        assert result.code == envelope["reason_code"] == code
        assert envelope["failure_category"] == category
        assert not result.answer_exact and result.scene3d is None
        assert "scene3d" not in envelope
        assert not route.get("construction_trace") and not route.get("relation_certificates")
        return
    assert math_class == "determined" and oracle is not None and derivation
    assert result.status == route["status"] == "SERVED" and result.code is None
    assert result.kernel_check is True
    assert route["source_verification"] == {"authority": "registry.kiem_nguon"}
    goal_id = payload["math_goals"][0]["goal_id"]
    assert set(result.answer_exact) == {goal_id}
    assert result.answer_exact[goal_id]["coef"] == oracle
    quantity = next(o for o in envelope["scene3d"]["objects"] if o["id"] == f"kq_{goal_id}")
    assert quantity["value"] == oracle
    assert quantity["type"] == "quantity"
    assert str(result.exec_result.final_memory[quantity["id"]]) == oracle
    source_goal = next(c for c in route["source_provenance"] if c["id"] == goal_id)
    assert payload["math_goals"][0]["quote"].rstrip(".") in " ".join(source_goal["quotes"])
    if "solid_id" in payload["math_goals"][0]["target"]:
        solid_id = payload["math_goals"][0]["target"]["solid_id"]
        notation = next(s["notation"] for s in payload["solids"] if s["solid_id"] == solid_id)
        assert source_goal["args"]["solid"] == notation


def _square_pyramid(extra_text, extra_premises, goal_text, goal, *, sa="3", perp_plane=True):
    """S.ABCD, square side 4, SA = sa. Hand frame A=(0,0,0) B=(4,0,0) C=(4,4,0) D=(0,4,0) S=(0,0,sa)."""
    rel = "SA vuông góc với (ABCD)" if perp_plane else "SA vuông góc với BC"
    text = f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, {rel} và SA = {sa}. {extra_text}{goal_text}"
    perp = ({"kind": "line_perp_plane", "args": {"line": ["S", "A"], "plane": list("ABCD")}, "quote": rel} if perp_plane
            else {"kind": "line_perp_line", "args": {"line1": ["S", "A"], "line2": ["B", "C"]}, "quote": rel})
    return {"schema_version": "typed-fact-next/2", "problem_text": text, "length_unit": "1",
            "solids": [{"solid_id": "pyr", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
            "premises": [{"kind": "base_is_square", "args": {"vertices": list("ABCD"), "side": "4"},
                          "quote": "đáy ABCD là hình vuông cạnh 4"}, perp,
                         {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": sa}, "quote": f"SA = {sa}"},
                         *extra_premises],
            "simulation_goals": [{"goal_id": "draw", "kind": "construct_object", "target_solid_id": "pyr",
                                  "quote": "Cho hình chóp S.ABCD"}],
            "math_goals": [{"goal_id": "q", "kind": "measurement", **goal, "quote": goal_text}]}


def _meet(point, l1, l2):
    q = f"Gọi {point} là giao điểm của {l1} và {l2}"
    return q + ". ", {"kind": "intersect_line_line", "args": {"point": point, "line1": list(l1), "line2": list(l2)}, "quote": q}


_MID_TEXT = "Gọi M là trung điểm của AB. "
_MID = {"kind": "midpoint", "args": {"point": "M", "segment": ["A", "B"]}, "quote": "Gọi M là trung điểm của AB"}
_DM_BC = _meet("I", "DM", "BC")
_VOLUME = ("Tính thể tích khối chóp S.ABCD.", {"goal_type": "volume", "target": {"solid_id": "pyr"}})
_DIST = lambda a, b: (f"Tính độ dài {a}{b}.", {"goal_type": "distance", "target": {"segment": [a, b]}})  # noqa: E731

#: Oracles fixed by hand in the frame above before observing the route.
#: DM: (2t, 4-4t, 0) meets line BC (x = 4) at t = 2, I = (4,-4,0): outside segment BC, beyond B.
EDGE_CASES = {
    "exterior-meet-length": (_square_pyramid(_MID_TEXT + _DM_BC[0], [_MID, _DM_BC[1]], *_DIST("B", "I")),
                             ("SERVED", None, None, "4")),                              # |BI| = 4
    "exterior-meet-radical": (_square_pyramid(_MID_TEXT + _DM_BC[0], [_MID, _DM_BC[1]], *_DIST("S", "I")),
                              ("SERVED", None, None, "√41")),                           # 4² + 4² + 3²
    "parallel-lines": (_square_pyramid(_meet("I", "AB", "CD")[0], [_meet("I", "AB", "CD")[1]], *_DIST("S", "I")),
                       ("REFUSED", "PARALLEL_NO_INTERSECTION", "geometry_generation_failed", None)),
    "skew-lines": (_square_pyramid(_meet("I", "SB", "CD")[0], [_meet("I", "SB", "CD")[1]], *_DIST("S", "I")),
                   ("REFUSED", "SKEW_NO_INTERSECTION", "geometry_generation_failed", None)),
    "zero-length": (_square_pyramid("", [], *_VOLUME, sa="0"),
                    ("REFUSED", "NON_POSITIVE_LENGTH", "geometry_generation_failed", None)),
    # "SA ⊥ BC" is not "SA ⊥ (ABCD)": the foot of S stays free, so the volume is not determined.
    "line-perp-line-is-not-height": (_square_pyramid("", [], *_VOLUME, perp_plane=False),
                                     ("REFUSED", "UNDERDETERMINED_POINT", "insufficient_specification", None)),
    "control-volume": (_square_pyramid("", [], *_VOLUME), ("SERVED", None, None, "16")),  # 4² · 3 / 3
}


@pytest.mark.parametrize("cid", EDGE_CASES)
def test_intersection_degeneracy_and_relation_edge_cases_match_hand_oracles(cid):
    payload, (status, code, category, coef) = EDGE_CASES[cid]
    result = run_typed_fact_next_v2_route(payload)
    envelope = build_adapter4_response(result, payload["problem_text"])["envelope"]
    assert (result.status, result.code, envelope.get("failure_category")) == (status, code, category)
    if status == "REFUSED":
        assert not result.answer_exact and "scene3d" not in envelope
        return
    assert result.kernel_check is True and result.answer_exact["q"]["coef"] == coef
    if cid.startswith("exterior"):
        xyz = {o["id"]: [F(c) for c in o["xyz"]] for o in envelope["scene3d"]["objects"] if o["type"] == "point3"}
        b, c, i = xyz["B"], xyz["C"], xyz["I"]
        # Affine parameter (chart-invariant): I = B + t(C − B) with t = −1 ∉ [0, 1].
        t = {(i[k] - b[k]) / (c[k] - b[k]) for k in range(3) if c[k] != b[k]}
        assert t == {F(-1)} and all(i[k] == b[k] for k in range(3) if c[k] == b[k])


def test_one_condition_pair_has_an_independent_non_uniqueness_witness():
    from fractions import Fraction as F

    # Both translations (0,0,5) and (3,0,4) have squared length 25, but heights 5 and 4.
    assert 5**2 == 3**2 + 4**2
    area = F(3 * 4, 2)
    assert (area * 5, area * 4) == (30, 24)
    right, oblique = CORPUS.prism(), CORPUS.prism(right=False)
    assert right["problem_text"].replace("đứng ", "") == oblique["problem_text"]
    assert [p for p in right["premises"] if p["kind"] != "right_prism"] == oblique["premises"]
