"""Authored regressions: a stated skew relation must agree with the exact built lines."""
from copy import deepcopy
from fractions import Fraction
import unicodedata

import pytest

from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route
from app.ai.hybrid_preview import classify_refusal
from tests.geometry.test_typed_fact_next_v2_distance_bridge import _prism


@pytest.mark.parametrize("lines", [(["A", "B"], ["A", "C"]), (["A", "B"], ["A'", "B'"])])
@pytest.mark.parametrize("normalization", ["NFC", "NFD"])
def test_coplanar_lines_cannot_satisfy_a_stated_skew_relation(lines, normalization):
    a, b = lines
    quote = unicodedata.normalize(normalization,
        f"Tính khoảng cách giữa hai đường thẳng chéo nhau {''.join(a)} và {''.join(b)}.")
    payload = _prism(ask=(quote, {"line1": a, "line2": b}))
    original = deepcopy(payload)
    result = run_typed_fact_next_v2_route(payload)
    assert (result.status, result.code) == ("REFUSED", "SKEW_CLAIM_CONTRADICTED")
    assert classify_refusal(result.code).group == "INVALID_DATA"
    response = build_adapter4_response(result, payload["problem_text"])
    assert response["envelope"]["status"] == "unsupported"
    assert response["envelope"]["failure_category"] == "geometry_generation_failed"
    assert "scene3d" not in response["envelope"]
    assert payload == original


@pytest.mark.parametrize("normalization", ["NFC", "NFD"])
def test_true_skew_distance_keeps_the_verbatim_source_quote(normalization):
    quote = unicodedata.normalize(normalization,
        "Tính khoảng cách giữa hai đường thẳng chéo nhau AA' và BC.")
    payload = _prism(ask=(quote, {"line1": ["A", "A'"], "line2": ["B", "C"]}))
    result = run_typed_fact_next_v2_route(payload)
    assert result.status == "SERVED", (result.code, result.reason)
    assert Fraction(result.exec_result.final_memory["kq_q"]) == Fraction(24, 5)
    verified_calls = deepcopy(result.calls)
    response = build_adapter4_response(result, payload["problem_text"])
    provenance = next(p for p in response["route_d"]["source_provenance"] if p["id"] == "q")
    assert provenance["quotes"] == [quote]
    assert result.calls == verified_calls


def test_verbatim_provenance_cannot_replace_the_verified_operands():
    quote = unicodedata.normalize("NFD", "Tính khoảng cách giữa hai đường thẳng chéo nhau AA' và BC.")
    payload = _prism(ask=(quote, {"line1": ["A", "A'"], "line2": ["B", "C"]}))
    result = run_typed_fact_next_v2_route(payload)
    assert result.status == "SERVED"
    call = next(c for c in result.planner["calls"] if c["id"] == "q")
    call["source"]["quotes"] = [quote.replace("BC", "AC")]
    response = build_adapter4_response(result, payload["problem_text"])
    assert response["route_d"]["status"] == "REFUSED"
    assert response["envelope"]["reason_code"] == "QUOTE_NOT_IN_SOURCE"
    assert "scene3d" not in response["envelope"]


def test_parallel_distance_without_a_skew_claim_is_still_defined():
    quote = "Tính khoảng cách giữa hai đường thẳng AB và A'B'."
    result = run_typed_fact_next_v2_route(_prism(ask=(quote,
        {"line1": ["A", "B"], "line2": ["A'", "B'"]})))
    assert result.status == "SERVED", (result.code, result.reason)
    assert Fraction(result.exec_result.final_memory["kq_q"]) == 12


def test_a_shared_quote_does_not_transfer_a_skew_claim_to_another_pair():
    quote = ("Tính khoảng cách giữa hai đường thẳng chéo nhau AA' và BC, "
             "và khoảng cách giữa hai đường thẳng AB và A'B'.")
    payload = _prism(ask=(quote, {"line1": ["A", "A'"], "line2": ["B", "C"]}))
    payload["math_goals"].append({"goal_id": "parallel", "kind": "measurement", "goal_type": "distance",
        "target": {"line1": ["A", "B"], "line2": ["A'", "B'"]}, "quote": quote})
    result = run_typed_fact_next_v2_route(payload)
    assert result.status == "SERVED", (result.code, result.reason)
    assert Fraction(result.exec_result.final_memory["kq_q"]) == Fraction(24, 5)
    assert Fraction(result.exec_result.final_memory["kq_parallel"]) == 12


def _scene_of(payload):
    result = run_typed_fact_next_v2_route(payload)
    assert result.status == "SERVED", (result.code, result.reason)
    return build_adapter4_response(result, payload["problem_text"])["envelope"]["scene3d"]


def test_skew_distance_carries_the_exact_common_perpendicular():
    """Frame A(0,0,0), A′(0,0,1), B(1,0,0), C(0,1,0), Gram diag(36, 64, 144). Worked by hand (see
    `test_geometry_kernel::test_doan_vuong_goc_chung_theo_metric_khung`): P = A on AA′, Q = (16/25, 9/25, 0) on BC,
    |PQ| = 24/5 = the served answer. Each mark's `u` points to the NEAREST named point of its own line."""
    scene = _scene_of(_prism(ask=("Tính khoảng cách giữa hai đường thẳng chéo nhau AA' và BC.",
                                  {"line1": ["A", "A'"], "line2": ["B", "C"]})))
    kq = next(o for o in scene["objects"] if o["id"] == "kq_q")
    assert not any(d.startswith("ANNOTATION_UNBOUND kq_q") for d in scene.get("diagnostics") or [])
    w = kq["annotation"]["witness"]
    assert kq["annotation"]["anchor"] == "witness" and w["relation"] == "common_perpendicular"
    assert (w["on"], w["from"], w["second"]["on"]) == ("dt1_q", "dt2_q", "dt2_q")
    assert [Fraction(x) for x in w["foot"]] == [0, 0, 0]
    assert [Fraction(x) for x in w["from_point"]] == [Fraction(16, 25), Fraction(9, 25), 0]
    assert w["second"]["foot"] == w["from_point"]
    assert (w["marker"]["u_to"], w["second"]["marker"]["u_to"]) == ("A_prime", "B")
    assert [Fraction(x) for x in w["marker"]["v"]] == [Fraction(16, 25), Fraction(9, 25), 0]
    assert [Fraction(x) for x in w["second"]["marker"]["v"]] == [Fraction(-16, 25), Fraction(-9, 25), 0]


def test_the_default_scene_builder_is_unchanged_without_the_route_d_switch():
    """NO_BUMP evidence for CACHE_VERSION: `pipeline.py` (LLM_ONLY) calls `build_simulation_state` without the switch,
    so the same program keeps exactly the pre-existing ANNOTATION_UNBOUND outcome."""
    from app.simulation.geometry import metric as _metric
    from app.simulation.semantic_program.simulation_state import build_simulation_state

    payload = _prism(ask=("Tính khoảng cách giữa hai đường thẳng chéo nhau AA' và BC.",
                          {"line1": ["A", "A'"], "line2": ["B", "C"]}))
    r = run_typed_fact_next_v2_route(payload)
    with _metric.using(r.chart_metric):
        state = build_simulation_state(r.spec, r.exec_result, r.declared_topology)
    kq = next(o for o in state["scene"]["objects"] if o["id"] == "kq_q")
    assert kq.get("annotation") is None
    assert "ANNOTATION_UNBOUND kq_q: distance between two non-point objects has no registered anchor" in state[
        "annotation_diagnostics"]


def test_a_witness_that_does_not_reproduce_the_measured_distance_is_withheld():
    """Fault injection on the self-check: AB and SD of S(0,0,2) over the unit square have d² = 4/5 (worked by hand in
    `test_geometry_kernel`); a recorded distance that disagrees must not get a drawn common perpendicular."""
    from app.simulation.geometry import Line3, Vec3
    from app.simulation.semantic_program.quantity_annotations import _nhan_chung_hai_duong

    mem = {"ab": Line3.through(Vec3.of(0, 0, 0), Vec3.of(1, 0, 0)),
           "sd": Line3.through(Vec3.of(0, 0, 2), Vec3.of(0, 1, 0))}
    assert isinstance(_nhan_chung_hai_duong("d", "ab", "sd", {**mem, "d": Fraction(1)}), str)
    assert _nhan_chung_hai_duong("d", "ab", "sd", {**mem, "d": None}) == \
        "the common perpendicular does not reproduce the measured distance"


def test_a_distance_between_parallel_lines_gets_no_common_perpendicular():
    scene = _scene_of(_prism(ask=("Tính khoảng cách giữa hai đường thẳng AB và A'B'.",
                                  {"line1": ["A", "B"], "line2": ["A'", "B'"]})))
    kq = next(o for o in scene["objects"] if o["id"] == "kq_q")
    assert kq.get("annotation") is None
