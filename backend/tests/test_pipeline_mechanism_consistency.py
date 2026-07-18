"""M15 Task 6 — route-consistency ordering trong run_pipeline (Global Constraint 15).

Chứng minh THỨ TỰ: analyze → classify lần 1 → classify_with_one_route_recovery
(CHỈ family-mismatch, ≤1 reclassify) → FINAL ROUTE → mọi route-dependent gate
(computation M13, selector tier-1 M14, direct ownership) chạy DƯỚI final route.

Mock call_gemini dispatch theo SKILL (marker trong user_text) + đếm call theo
skill; classify trả KHÁC nhau lần 1 vs lần 2 (closure counter). 0 network."""

from __future__ import annotations

import asyncio
import json

import pytest

from app.ai import pipeline
from app.evaluation.observer import AttemptObserver


# ── Mock dispatch theo skill (marker user_text) + đếm call ─────────
def _mock(analysis_json: str, classify_seq: list[str], simulate_seq: list[str] | None = None):
    """analyze → analysis_json; classify → classify_seq theo thứ tự (giữ giá trị
    cuối nếu vượt); simulate → simulate_seq. counts đếm theo skill name."""
    counts = {"analyze": 0, "classify": 0, "simulate": 0}
    idx = {"c": 0, "s": 0}
    simulate_seq = simulate_seq or []

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2, image=None):
        # LƯU Ý dispatch: prompt reclassify (classify + extra_note) chứa CẢ
        # "DANH MỤC MÔ PHỎNG" LẪN cụm "simulation_id đã chọn" (nằm trong extra_note).
        # → PHẢI khớp classify TRƯỚC simulate, nếu không reclassify bị nhận nhầm.
        if "DANH MỤC MÔ PHỎNG" in user_text:
            counts["classify"] += 1
            r = classify_seq[min(idx["c"], len(classify_seq) - 1)]
            idx["c"] += 1
            return r
        if "simulation_id đã chọn" in user_text:
            counts["simulate"] += 1
            r = simulate_seq[min(idx["s"], len(simulate_seq) - 1)] if simulate_seq else "{}"
            idx["s"] += 1
            return r
        counts["analyze"] += 1
        return analysis_json

    return fake, counts


def _analysis(proc=None, ownership="algorithmic", goal="Sắp xếp dãy"):
    a = {
        "objects": ["dãy"], "data": [{"description": "dãy"}], "relations": [],
        "processes": ["x"], "constraints": [], "goal": goal,
        "input_description": "in", "output_description": "out",
        "result_ownership": ownership,
    }
    if proc is not None:
        a["prescribed_procedure"] = proc
    return json.dumps(a)


def _classify(sim_id=None, status="ok", reason=None):
    return json.dumps({"status": status, "simulation_id": sim_id, "reason": reason})


def _sort_spec(variant="bubble"):
    return json.dumps({"family_version": "sort-fam-1", "variant": variant, "array": [5, 2, 9], "order": "asc"})


def _run(monkeypatch, mock, observer=None, text="Đề."):
    monkeypatch.setattr(pipeline, "call_gemini", mock)
    return asyncio.run(pipeline.run_pipeline(text, "k", observer=observer))


def _gates(obs, gate):
    return [d for (t, d) in obs.events if t == "gate_checked" and d.get("gate") == gate]


def _first_index(obs, pred):
    for i, (t, d) in enumerate(obs.events):
        if pred(t, d):
            return i
    return -1


# ── 1. T2: mismatch → KHÔNG simulate, reclassify ĐÚNG 1 lượt ───────
def test_T2_mismatch_khong_goi_simulate_va_reclassify_dung_1_luot(monkeypatch):
    mock, counts = _mock(
        _analysis(proc="positional_representation.non_binary_base"),
        classify_seq=[_classify("algorithm.binary_search"), _classify("algorithm.binary_search")],
    )
    obs = AttemptObserver()
    env = _run(monkeypatch, mock, obs)

    assert env["status"] == "unsupported"
    assert env["failure_category"] == "capability_gap"
    assert env["error_code"] == "route_mechanism_family_mismatch"
    assert counts["simulate"] == 0
    assert counts["classify"] == 2  # 1 + đúng 1 reclassify
    assert counts["analyze"] == 1   # khóa 3: analyze KHÔNG chạy lại
    rm = _gates(obs, "route_mechanism")
    assert rm and rm[0]["fired"] is True and rm[0]["reason_code"] == "route_mechanism_family_mismatch"
    assert _first_index(obs, lambda t, d: t == "reclassify_attempted") >= 0
    assert _first_index(obs, lambda t, d: t == "reclassify_result") >= 0


# ── 2. ORDERING PROOF: generic misroute + sorting prescribed → reclassify TRƯỚC computation gate ──
def test_generic_misroute_sorting_prescribed_reclassify_TRUOC_computation_gate(monkeypatch):
    mock, counts = _mock(
        _analysis(proc="adjacent_compare_swap", ownership="algorithmic"),
        classify_seq=[_classify("generic.rule_scene"), _classify("algorithm.comparison_sort")],
        simulate_seq=[_sort_spec("bubble")],
    )
    obs = AttemptObserver()
    env = _run(monkeypatch, mock, obs)

    # reclassify cứu đề sorting bị misroute → envelope ok concrete (KHÔNG bị gate chặn oan)
    assert env["status"] == "ok"
    assert env["simulation_id"] == "algorithm.bubble_sort"
    assert env["source"] == "family_resolved"
    assert env["variant"] == "bubble"
    # computation gate KHÔNG fire trên route TẠM generic (nó không chạy trước recovery)
    assert _gates(obs, "computation") == []


# ── 3. FINAL route = generic + ownership algorithmic → computation gate VẪN fire (M13) ──
def test_final_route_generic_ownership_algorithmic_computation_gate_van_fire(monkeypatch):
    mock, counts = _mock(
        _analysis(proc=None, ownership="algorithmic"),
        classify_seq=[_classify("generic.rule_scene")],
    )
    obs = AttemptObserver()
    env = _run(monkeypatch, mock, obs)

    assert env["status"] == "unsupported"
    assert env["failure_category"] == "capability_gap"
    assert counts["classify"] == 1  # KHÔNG reclassify (không mismatch)
    comp = _gates(obs, "computation")
    assert comp and comp[0]["fired"] is True


# ── 4. reclassify KHÔNG bypass gate M13/M14 — tier-1 fire trên FINAL route ──
def test_reclassification_khong_bypass_gate_M13_M14(monkeypatch):
    mock, counts = _mock(
        _analysis(proc="select_extreme_repeated", ownership="algorithmic"),
        classify_seq=[_classify("binary.decimal_to_binary"), _classify("algorithm.comparison_sort")],
    )
    obs = AttemptObserver()
    env = _run(monkeypatch, mock, obs)

    assert env["status"] == "unsupported"
    assert env["failure_category"] == "capability_gap"
    assert env["error_code"] == "gate_mechanism_ownership"  # tier-1 M14 trên FINAL selector route
    assert counts["simulate"] == 0  # gate chặn TRƯỚC stage_simulate_family
    assert counts["classify"] == 2
    mech = _gates(obs, "mechanism")
    assert any(m["fired"] and m["reason_code"] == "gate_mechanism_ownership" for m in mech)


# ── 5. route-dependent gate CHỈ trên final route (SAU reclassify_result) ──
def test_route_dependent_gates_chi_chay_tren_final_route(monkeypatch):
    # kịch bản có reclassify + có route-dependent gate (tier-1) sau đó
    mock, _ = _mock(
        _analysis(proc="select_extreme_repeated", ownership="algorithmic"),
        classify_seq=[_classify("binary.decimal_to_binary"), _classify("algorithm.comparison_sort")],
    )
    obs = AttemptObserver()
    _run(monkeypatch, mock, obs)

    rr = _first_index(obs, lambda t, d: t == "reclassify_result")
    assert rr >= 0
    for i, (t, d) in enumerate(obs.events):
        if t == "gate_checked" and d.get("gate") in ("computation", "mechanism"):
            assert i > rr, f"gate {d.get('gate')} chạy TRƯỚC reclassify_result (idx {i} ≤ {rr})"


# ── 6. call budget: analyze==1, classify≤2, simulate≤1 trên TỪNG kịch bản ──
@pytest.mark.parametrize("proc,ownership,classify_seq,simulate_seq", [
    # reclassify → gap (không simulate)
    ("positional_representation.non_binary_base", "algorithmic",
     [_classify("algorithm.binary_search"), _classify("algorithm.binary_search")], None),
    # reclassify → comparison_sort → simulate 1 lần
    ("adjacent_compare_swap", "algorithmic",
     [_classify("generic.rule_scene"), _classify("algorithm.comparison_sort")], [_sort_spec("bubble")]),
    # prescribed null → classify 1 lần, simulate 1
    (None, "algorithmic", [_classify("algorithm.comparison_sort")], [_sort_spec("bubble")]),
    # reclassify → tier-1 gap (không simulate)
    ("select_extreme_repeated", "algorithmic",
     [_classify("binary.decimal_to_binary"), _classify("algorithm.comparison_sort")], None),
])
def test_call_budget_analyze_1_classify_max2_simulate_max1(monkeypatch, proc, ownership, classify_seq, simulate_seq):
    mock, counts = _mock(_analysis(proc=proc, ownership=ownership), classify_seq, simulate_seq)
    _run(monkeypatch, mock)
    assert counts["analyze"] == 1
    assert counts["classify"] <= 2
    assert counts["simulate"] <= 1


# ── 7. reclassify → unsupported là TỪ CHỐI TRUNG THỰC (reason của classify) ──
def test_reclassify_ra_unsupported_la_tu_choi_trung_thuc(monkeypatch):
    mock, counts = _mock(
        _analysis(proc="positional_representation.non_binary_base", ownership="rule_derivable"),
        classify_seq=[
            _classify("algorithm.binary_search"),
            _classify(status="unsupported", reason="Bài này chưa khớp mô phỏng nào."),
        ],
    )
    env = _run(monkeypatch, mock)

    assert env["status"] == "unsupported"
    # KHÔNG phải capability_gap — từ chối thường của classify
    assert env.get("failure_category") != "capability_gap"
    assert env.get("error_code") is None
    assert env["reason"] == "Bài này chưa khớp mô phỏng nào."
    assert counts["classify"] == 2
    assert counts["simulate"] == 0


# ── 8. prescribed null → KHÔNG thêm call classify (đề thường) ──
def test_T4_prescribed_null_khong_them_call_classify(monkeypatch):
    mock, counts = _mock(
        _analysis(proc=None, ownership="algorithmic"),
        classify_seq=[_classify("algorithm.comparison_sort")],
        simulate_seq=[_sort_spec("bubble")],
    )
    env = _run(monkeypatch, mock)

    assert env["status"] == "ok"
    assert counts["classify"] == 1  # KHÔNG reclassify
    assert counts["analyze"] == 1
    assert counts["simulate"] == 1  # simulate chạy bình thường


# ── 9. ownership-gap (CÙNG family) → KHÔNG reclassify, gap thẳng ──
def test_ownership_gap_khong_reclassify(monkeypatch):
    mock, counts = _mock(
        _analysis(proc="positional_representation.non_binary_base", ownership="rule_derivable"),
        classify_seq=[_classify("binary.decimal_to_binary")],
    )
    obs = AttemptObserver()
    env = _run(monkeypatch, mock, obs)

    assert env["status"] == "unsupported"
    assert env["failure_category"] == "capability_gap"
    assert env["error_code"] == "gate_mechanism_ownership"
    assert counts["classify"] == 1  # cùng family → KHÔNG mâu thuẫn route → KHÔNG reclassify
    assert counts["simulate"] == 0
    assert _gates(obs, "route_mechanism") == []  # recovery KHÔNG chạy
    mech = _gates(obs, "mechanism")
    assert any(m["fired"] and m["reason_code"] == "gate_mechanism_ownership" for m in mech)


# ── 10. KHÔNG recursion — reclassify vẫn mismatch → KHÔNG lượt 3, gap fail-closed ──
def test_khong_recursion(monkeypatch):
    mock, counts = _mock(
        _analysis(proc="positional_representation.non_binary_base", ownership="algorithmic"),
        classify_seq=[_classify("algorithm.binary_search"), _classify("generic.rule_scene")],
    )
    env = _run(monkeypatch, mock)

    assert env["status"] == "unsupported"
    assert env["failure_category"] == "capability_gap"
    assert env["error_code"] == "route_mechanism_family_mismatch"
    assert counts["classify"] == 2  # KHÔNG lượt 3
    assert counts["simulate"] == 0
