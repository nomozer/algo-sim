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
