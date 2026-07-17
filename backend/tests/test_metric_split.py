"""M14 Task 11 — metric TÁCH BẠCH (§F3): family/variant đo trên classify token +
final envelope, KHÔNG lẫn với classification cũ. Non-family: classify==final."""

from __future__ import annotations

from app.evaluation.harness import EvalReport, ItemResult


def _family_item(ok=True):
    # family-routed: classify = SELECTOR TOKEN, final = CONCRETE (khác nhau)
    return ItemResult(
        id="fam", group="specialized", predicted="algorithm.comparison_sort", classified_ok=ok,
        spec_valid=True, retry_count=0,
        classify_simulation_id="algorithm.comparison_sort",
        final_simulation_id="algorithm.bubble_sort" if ok else "algorithm.insertion_sort",
        variant="bubble", expected_family_routed=True,
        final_route_correct=ok, family_selection_correct=True, variant_selection_correct=ok,
    )


def _plain_item(ok=True):
    # non-family: classify == final (không selector)
    return ItemResult(
        id="plain", group="specialized", predicted="algorithm.find_max", classified_ok=ok,
        spec_valid=True, retry_count=0,
        classify_simulation_id="algorithm.find_max", final_simulation_id="algorithm.find_max",
        expected_family_routed=False, final_route_correct=ok,
    )


def test_family_routed_classify_khac_final():
    r = _family_item()
    assert r.classify_simulation_id != r.final_simulation_id  # token ≠ concrete
    assert r.classify_simulation_id == "algorithm.comparison_sort"
    assert r.final_simulation_id == "algorithm.bubble_sort"


def test_metric_tach_family_va_final():
    rep = EvalReport(results=[_family_item(), _plain_item()])
    m = rep.metrics()
    assert m["family_routed_count"] == 1               # chỉ item family-routed
    assert m["final_route_accuracy"] == 1.0            # cả 2 đúng final
    assert m["family_selection_accuracy"] == 1.0       # trên 1 item routed
    assert m["variant_selection_accuracy"] == 1.0


def test_non_family_final_route_trung_classification():
    # item non-family: classify==final → final_route_accuracy == classification_accuracy
    rep = EvalReport(results=[_plain_item(ok=True), _plain_item(ok=False)])
    m = rep.metrics()
    assert m["final_route_accuracy"] == m["classification_accuracy"] == 0.5
    assert m["family_routed_count"] == 0


def test_variant_sai_final_route_sai():
    # family route nhưng variant resolve SAI concrete → final_route sai
    rep = EvalReport(results=[_family_item(ok=False)])
    m = rep.metrics()
    assert m["final_route_accuracy"] == 0.0
    assert m["variant_selection_accuracy"] == 0.0
    assert m["family_selection_accuracy"] == 1.0  # chọn ĐÚNG family, chỉ variant sai
