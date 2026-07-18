"""M14 Task 9 — evaluate_item đi QUA production run_pipeline + observer THỤ ĐỘNG
(bất biến #22). Observer không đổi output; harness không gọi _simulate_with_metrics."""

from __future__ import annotations

import asyncio
import json

from app.ai import pipeline
from app.evaluation import harness
from app.evaluation.dataset import EvalItem
from app.evaluation.observer import AttemptObserver


def _fake_gemini(responses):
    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2):
        if not responses:
            raise AssertionError("gọi nhiều hơn số response")
        return responses.pop(0)
    return fake


def _analysis(proc=None):
    a = {
        "objects": ["dãy"], "data": [{"description": "dãy"}], "relations": [],
        "processes": ["sắp xếp"], "constraints": [], "goal": "Sắp xếp dãy",
        "input_description": "Dãy", "output_description": "Dãy đã sắp",
        "result_ownership": "algorithmic",
    }
    if proc:
        a["prescribed_procedure"] = proc
    return json.dumps(a)


def _classify(sim_id):
    return json.dumps({"status": "ok", "simulation_id": sim_id, "reason": None})


def _sort_spec(variant="bubble"):
    return json.dumps({"family_version": "sort-fam-1", "variant": variant, "array": [5, 2, 9], "order": "asc"})


# ── Observer passive: có/không observer → envelope GIỐNG HỆT ────
def test_observer_passive_khong_doi_output(monkeypatch):
    def run():
        return asyncio.run(pipeline.run_pipeline("Sắp xếp nổi bọt 5,2,9.", "k",
                                                 observer=AttemptObserver()))
    def run_no_obs():
        return asyncio.run(pipeline.run_pipeline("Sắp xếp nổi bọt 5,2,9.", "k"))

    monkeypatch.setattr(pipeline, "call_gemini",
                        _fake_gemini([_analysis("adjacent_compare_swap"), _classify("algorithm.comparison_sort"), _sort_spec()]))
    env_obs = run()
    monkeypatch.setattr(pipeline, "call_gemini",
                        _fake_gemini([_analysis("adjacent_compare_swap"), _classify("algorithm.comparison_sort"), _sort_spec()]))
    env_no = run_no_obs()
    assert env_obs == env_no
    assert env_obs["simulation_id"] == "algorithm.bubble_sort"


# ── evaluate_item KHÔNG gọi _simulate_with_metrics (đi qua run_pipeline) ──
def test_evaluate_item_di_qua_run_pipeline(monkeypatch):
    # #22: eval PHẢI đi qua production run_pipeline. _simulate_with_metrics đã
    # retire (Task 10) → không còn hàm tái dựng stage riêng.
    assert not hasattr(harness, "_simulate_with_metrics")
    called = {"pipeline": False}

    real_run = pipeline.run_pipeline

    async def spy_run(*a, **k):
        called["pipeline"] = True
        return await real_run(*a, **k)
    monkeypatch.setattr(pipeline, "run_pipeline", spy_run)

    monkeypatch.setattr(pipeline, "call_gemini",
                        _fake_gemini([_analysis("adjacent_compare_swap"), _classify("algorithm.comparison_sort"), _sort_spec()]))
    item = EvalItem("t-bubble", "Sắp xếp nổi bọt 5,2,9.", "specialized", "algorithm.bubble_sort")
    res = asyncio.run(harness.evaluate_item(item, "k"))

    assert called["pipeline"] is True
    assert res.classified_ok and res.spec_valid
    # metric split: classify = token, final = concrete
    assert res.classify_simulation_id == "algorithm.comparison_sort"
    assert res.final_simulation_id == "algorithm.bubble_sort"
    assert res.variant == "bubble"


def test_evaluate_item_selection_near_miss_la_capability_gap(monkeypatch):
    # analyze phát select_extreme → mechanism gate → capability_gap; nhóm unsupported
    monkeypatch.setattr(pipeline, "call_gemini",
                        _fake_gemini([_analysis("select_extreme_repeated"), _classify("algorithm.comparison_sort")]))
    item = EvalItem("t-selection", "Sắp xếp chọn.", "unsupported")
    res = asyncio.run(harness.evaluate_item(item, "k"))
    assert res.classified_ok is True  # từ chối đúng
    assert res.mechanism_gate_fired is True
    assert res.final_simulation_id is None


# ── M15 Task 4: analyze_done mang cả raw lẫn canonical (khóa 5) ────
def test_analyze_done_event_mang_raw_va_canonical(monkeypatch):
    monkeypatch.setattr(pipeline, "call_gemini",
                        _fake_gemini([_analysis("adjacent_compare_swap"), _classify("algorithm.comparison_sort"), _sort_spec()]))
    obs = AttemptObserver()
    asyncio.run(pipeline.run_pipeline("Sắp xếp nổi bọt 5,2,9.", "k", observer=obs))
    data = obs.analyze()
    assert data is not None
    assert data["prescribed_procedure"] == "adjacent_compare_swap"  # raw, KHÔNG đổi
    assert data["canonical_prescribed"] == "comparison_sort.adjacent_compare_swap"
