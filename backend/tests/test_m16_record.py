# -*- coding: utf-8 -*-
"""M16 Task 2 (W2) — observer accessors + emit đối xứng + budget delta + record
builder (nguồn yêu cầu: .superpowers/sdd/m16-task-2-brief.md).

TDD: viết TRƯỚC khi có app/evaluation/m16_record.py + accessor mới trên
observer.py + nhánh else trong pipeline.py — RED trước, GREEN sau khi cài đặt.

Mock call_gemini dispatch theo SKILL (marker trong user_text), giống
test_pipeline_mechanism_consistency.py — chạy run_pipeline THẬT, 0 network
(conftest guard tự bảo vệ).
"""

from __future__ import annotations

import asyncio
import json

from app.ai import pipeline
from app.ai.gemini import ApiBudget
from app.evaluation import harness
from app.evaluation.dataset import EvalItem
from app.evaluation.observer import AttemptObserver
from app.evaluation.m16_record import M16CaseRecord, build_m16_record, family_of_route
from app.evaluation.m16_schema import M16Archetype, M16Expectation
from app.simulation.descriptor import FamilyId


# ── Mock dispatch theo skill (như test_pipeline_mechanism_consistency.py) ──
def _mock(analysis_json: str, classify_seq: list[str], simulate_seq: list[str] | None = None):
    counts = {"analyze": 0, "classify": 0, "simulate": 0}
    idx = {"c": 0, "s": 0}
    simulate_seq = simulate_seq or []

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2, image=None):
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


def _analysis_find_max():
    a = {
        "objects": ["dãy"], "data": [{"description": "dãy"}], "relations": [],
        "processes": ["tìm max"], "constraints": [], "goal": "Tìm phần tử lớn nhất",
        "input_description": "dãy số", "output_description": "giá trị lớn nhất",
        "result_ownership": "algorithmic",
    }
    return json.dumps(a)


def _classify(sim_id=None, status="ok", reason=None):
    return json.dumps({"status": status, "simulation_id": sim_id, "reason": reason})


def _sort_spec(variant="bubble"):
    return json.dumps({"family_version": "sort-fam-1", "variant": variant, "array": [5, 2, 9], "order": "asc"})


def _findmax_spec():
    return json.dumps({
        "problem": {"summary": "Tìm max", "input": "i", "output": "o"},
        "data": {"array": [7, 9, 6, 10, 8]},
    })


def _run(monkeypatch, mock, observer=None, text="Đề."):
    monkeypatch.setattr(pipeline, "call_gemini", mock)
    return asyncio.run(pipeline.run_pipeline(text, "k", observer=observer))


def _zero_budget_delta() -> dict:
    return {"logical_calls": 0, "http_requests": 0, "retry_requests": 0, "transient_hits": 0}


# ── (a) observer accessors mới ──────────────────────────────────────────

def test_observer_reclassify_accessors_doc_dung_event_pipeline_that(monkeypatch):
    """Chạy case mismatch thật (giống T2 test_pipeline_mechanism_consistency)
    và kiểm accessor MỚI reclassify_attempted()/reclassify_result() đọc đúng
    event mà run_pipeline thật đã phát ra."""
    mock, counts = _mock(
        _analysis(proc="positional_representation.non_binary_base"),
        classify_seq=[_classify("algorithm.binary_search"), _classify("algorithm.binary_search")],
    )
    obs = AttemptObserver()
    env = _run(monkeypatch, mock, obs)

    assert env["status"] == "unsupported"
    ra = obs.reclassify_attempted()
    assert ra is not None
    assert ra["from_simulation_id"] == "algorithm.binary_search"
    assert ra["canonical_prescribed"] == "positional_representation.non_binary_base"
    rr = obs.reclassify_result()
    assert rr is not None
    assert rr["status"] == "ok"
    assert rr["simulation_id"] == "algorithm.binary_search"


def test_observer_reclassify_accessors_none_khi_khong_mismatch(monkeypatch):
    """Case KHÔNG mismatch (proc=None) → cả hai accessor mới trả None (event
    reclassify_* chưa bao giờ được phát)."""
    mock, counts = _mock(
        _analysis_find_max(),
        classify_seq=[_classify("algorithm.find_max")],
        simulate_seq=[_findmax_spec()],
    )
    obs = AttemptObserver()
    env = _run(monkeypatch, mock, obs)

    assert env["status"] == "ok"
    assert obs.reclassify_attempted() is None
    assert obs.reclassify_result() is None


def test_observer_gate_events_loc_theo_gate_va_tat_ca():
    """gate_events(gate=None) = mọi gate_checked; gate_events("mechanism") =
    lọc đúng loại — dùng dữ liệu tự nạp (không cần chạy pipeline)."""
    obs = AttemptObserver()
    obs.emit("gate_checked", {"gate": "computation", "fired": True, "reason_code": "x"})
    obs.emit("gate_checked", {"gate": "mechanism", "fired": False, "reason_code": None})
    obs.emit("gate_checked", {"gate": "mechanism", "fired": True, "reason_code": "y"})
    obs.emit("analyze_done", {"result_ownership": "provided"})  # nhiễu, không phải gate

    assert len(obs.gate_events(None)) == 3
    mech = obs.gate_events("mechanism")
    assert len(mech) == 2
    assert all(g["gate"] == "mechanism" for g in mech)
    assert obs.gate_events("computation") == [{"gate": "computation", "fired": True, "reason_code": "x"}]


# ── (b) emit đối xứng direct-entry (verdict None → fired=False) ─────────

def test_direct_entry_pass_emit_gate_mechanism_fired_false(monkeypatch):
    """find_max: không selector, không prescribed_procedure → direct_verdict
    None (thành công) — nhánh else MỚI phải emit gate_checked mechanism
    fired=False reason_code=None (đối xứng với nhánh fired=True hiện có)."""
    mock, counts = _mock(
        _analysis_find_max(),
        classify_seq=[_classify("algorithm.find_max")],
        simulate_seq=[_findmax_spec()],
    )
    obs = AttemptObserver()
    env = _run(monkeypatch, mock, obs)

    assert env["status"] == "ok"
    assert env["simulation_id"] == "algorithm.find_max"
    mech_gates = obs.gate_events("mechanism")
    assert len(mech_gates) == 1
    assert mech_gates[0]["fired"] is False
    assert mech_gates[0]["reason_code"] is None


def test_observer_none_production_khong_doi(monkeypatch):
    """Bất biến cứng: observer=None → run_pipeline chạy y nguyên (không crash
    ở nhánh else mới, không side effect nào lộ ra output)."""
    mock, counts = _mock(
        _analysis_find_max(),
        classify_seq=[_classify("algorithm.find_max")],
        simulate_seq=[_findmax_spec()],
    )
    env = _run(monkeypatch, mock, observer=None)
    assert env["status"] == "ok"
    assert env["simulation_id"] == "algorithm.find_max"


# ── (c) budget_delta + record_sink qua evaluate_item ─────────────────────

def test_budget_delta_dung_khi_budget_tick_gia(monkeypatch):
    """Mock call_gemini TỰ tick budget (giả lập gemini.call_gemini thật) —
    evaluate_item phải snapshot ĐÚNG trước/sau quanh run_pipeline."""
    budget = ApiBudget()

    def _make_ticking_mock():
        async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2, image=None):
            budget.note_call()
            budget.note_request(is_retry=False)
            if "DANH MỤC MÔ PHỎNG" in user_text:
                return _classify("algorithm.find_max")
            if "simulation_id đã chọn" in user_text:
                return _findmax_spec()
            return _analysis_find_max()
        return fake

    monkeypatch.setattr(pipeline, "call_gemini", _make_ticking_mock())
    item = EvalItem("t-budget", "Tìm max.", "specialized", "algorithm.find_max")
    sink: list = []
    res = asyncio.run(harness.evaluate_item(item, "k", budget=budget, record_sink=sink))

    assert res.spec_valid is True
    # 3 logical call thật: analyze + classify + simulate
    assert budget.logical_calls == 3
    assert len(sink) == 1
    assert sink[0].budget_delta == {
        "logical_calls": 3, "http_requests": 3, "retry_requests": 0, "transient_hits": 0,
    }


def test_budget_delta_khong_am_khi_budget_da_co_san_tu_case_truoc(monkeypatch):
    """budget SỐNG XUYÊN nhiều case (như live.py thật) — delta phải là HIỆU
    số, không phải giá trị tuyệt đối luỹ kế."""
    budget = ApiBudget()
    budget.note_call()
    budget.note_request(is_retry=False)  # mô phỏng 1 call đã xảy ra TRƯỚC case này

    def _make_ticking_mock():
        async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2, image=None):
            budget.note_call()
            budget.note_request(is_retry=False)
            if "DANH MỤC MÔ PHỎNG" in user_text:
                return _classify("algorithm.find_max")
            if "simulation_id đã chọn" in user_text:
                return _findmax_spec()
            return _analysis_find_max()
        return fake

    monkeypatch.setattr(pipeline, "call_gemini", _make_ticking_mock())
    item = EvalItem("t-budget2", "Tìm max.", "specialized", "algorithm.find_max")
    sink: list = []
    asyncio.run(harness.evaluate_item(item, "k", budget=budget, record_sink=sink))

    assert budget.logical_calls == 4  # 1 trước + 3 của case này
    assert sink[0].budget_delta["logical_calls"] == 3  # CHỈ phần case này


def test_budget_delta_zero_khi_khong_co_budget(monkeypatch):
    mock, counts = _mock(
        _analysis_find_max(),
        classify_seq=[_classify("algorithm.find_max")],
        simulate_seq=[_findmax_spec()],
    )
    monkeypatch.setattr(pipeline, "call_gemini", mock)
    item = EvalItem("t-nobudget", "Tìm max.", "specialized", "algorithm.find_max")
    sink: list = []
    asyncio.run(harness.evaluate_item(item, "k", record_sink=sink))

    assert sink[0].budget_delta == _zero_budget_delta()


def test_evaluate_item_khong_record_sink_thi_khong_append_gi(monkeypatch):
    """record_sink=None (mặc định) → hành vi cũ nguyên vẹn, KHÔNG side effect."""
    mock, counts = _mock(
        _analysis_find_max(),
        classify_seq=[_classify("algorithm.find_max")],
        simulate_seq=[_findmax_spec()],
    )
    monkeypatch.setattr(pipeline, "call_gemini", mock)
    item = EvalItem("t-norecord", "Tìm max.", "specialized", "algorithm.find_max")
    res = asyncio.run(harness.evaluate_item(item, "k"))
    assert res.spec_valid is True  # ItemResult vẫn như cũ, không lỗi vì thiếu record_sink


# ── (d) fault-injection: observer thiếu event → record KHÔNG đoán ───────

def test_fault_injection_thieu_classify_done_khong_doan():
    """Quan sát viên (giả lập) MẤT event classify_done — record builder KHÔNG
    được suy initial_route/initial_family từ nguồn khác (vd final_route);
    phải trả None và KHÔNG crash."""
    obs = AttemptObserver()
    obs.emit("analyze_done", {
        "result_ownership": "algorithmic", "prescribed_procedure": None, "canonical_prescribed": None,
    })
    obs.emit("plan_built", {"unsupported_capabilities": []})
    # classify_done CỐ Ý bỏ qua (fault injection)
    obs.emit("envelope", {"status": "ok", "simulation_id": "algorithm.find_max", "source": "composed"})

    item = EvalItem("t-fault", "Tìm max.", "specialized", "algorithm.find_max")
    envelope = {"status": "ok", "simulation_id": "algorithm.find_max", "source": "composed"}
    rec = build_m16_record(item, obs, envelope, None, _zero_budget_delta())

    assert rec.initial_route is None
    assert rec.initial_family is None
    assert rec.reclassify_attempted is False
    assert rec.reclassify_result_route is None
    # envelope KHÔNG bị ảnh hưởng bởi event thiếu — vẫn đọc đúng
    assert rec.final_route == "algorithm.find_max"
    assert rec.final_family == "single_pass_scan"
    assert rec.via_production_pipeline is True


def test_fault_injection_observer_rong_hoan_toan_khong_crash():
    """Observer HOÀN TOÀN rỗng (không event nào) + envelope None + pipeline_error
    None (đầu vào ngoài kỳ vọng cho eval script hỏng) — build_m16_record
    KHÔNG được crash, mọi field-phụ-thuộc-event trả None/giá trị rỗng an toàn."""
    obs = AttemptObserver()
    item = EvalItem("t-empty", "?", "specialized", "algorithm.find_max")
    rec = build_m16_record(item, obs, None, None, _zero_budget_delta())

    assert rec.initial_route is None
    assert rec.final_route is None
    assert rec.envelope_status is None
    assert rec.via_production_pipeline is False  # không envelope event, không pipeline_error
    assert rec.gates == []
    assert rec.simulate_attempts == []
    assert rec.first_attempt_ok is None


# ── (e) family_of_route ───────────────────────────────────────────────

def test_family_of_route_none_khi_route_none():
    assert family_of_route(None) is None


def test_family_of_route_selector_token():
    assert family_of_route("algorithm.comparison_sort") == FamilyId.COMPARISON_SORT.value


def test_family_of_route_single_membership():
    assert family_of_route("algorithm.find_max") == FamilyId.SINGLE_PASS_SCAN.value
    assert family_of_route("algorithm.bubble_sort") == FamilyId.COMPARISON_SORT.value


def test_family_of_route_dual_membership_khong_doan_neu_khong_co_expected():
    assert family_of_route("generic.rule_scene") == "generic_dual"


def test_family_of_route_dual_membership_khop_theo_expected_family():
    assert (
        family_of_route("generic.rule_scene", expected_family=FamilyId.BOOLEAN_COMPOSITION.value)
        == FamilyId.BOOLEAN_COMPOSITION.value
    )
    assert (
        family_of_route(
            "generic.rule_scene",
            expected_family=FamilyId.STRUCTURAL_PROGRESSIVE_REPRESENTATION.value,
        )
        == FamilyId.STRUCTURAL_PROGRESSIVE_REPRESENTATION.value
    )
    # expected_family NGOÀI tập membership → vẫn KHÔNG đoán, trả generic_dual
    assert (
        family_of_route("generic.rule_scene", expected_family=FamilyId.GRAPH_TRAVERSAL.value)
        == "generic_dual"
    )


def test_family_of_route_unknown_route_none():
    assert family_of_route("khong_ton_tai.nao_ca") is None


# ── (f) record builder map đủ trường từ transcript đầy đủ (so tay) ──────

def test_build_m16_record_map_du_truong_transcript_day_du(monkeypatch):
    m16 = M16Expectation(
        archetype=M16Archetype.EXPLICIT_POSITIVE,
        expected_family=FamilyId.COMPARISON_SORT.value,
        expected_initial_route="algorithm.comparison_sort",
        expected_gate=None,
        expected_error_code=None,
        analyze_mechanism_expected="comparison_sort.adjacent_compare_swap",
        live_eligible=True,
    )
    item = EvalItem(
        "t-full-transcript", "Sắp xếp nổi bọt 5,2,9.", "specialized",
        expect_simulation_id="algorithm.bubble_sort", m16=m16,
    )

    mock, counts = _mock(
        _analysis(proc="adjacent_compare_swap", ownership="algorithmic"),
        classify_seq=[_classify("algorithm.comparison_sort")],
        simulate_seq=[_sort_spec("bubble")],
    )
    obs = AttemptObserver()
    env = _run(monkeypatch, mock, obs, text=item.text)
    assert env["status"] == "ok"  # sanity trước khi so field

    rec = build_m16_record(item, obs, env, None, _zero_budget_delta(), semantic_ok=None)

    assert rec == M16CaseRecord(
        case_id="t-full-transcript",
        group="specialized",
        archetype="explicit_positive",
        expected_family="comparison_sort",
        expected_initial_route="algorithm.comparison_sort",
        expected_final_route="algorithm.bubble_sort",
        raw_prescribed="adjacent_compare_swap",
        canonical_prescribed="comparison_sort.adjacent_compare_swap",
        result_ownership="algorithmic",
        initial_route="algorithm.comparison_sort",
        initial_family="comparison_sort",
        reclassify_attempted=False,
        reclassify_result_route=None,
        final_route="algorithm.bubble_sort",
        final_family="comparison_sort",
        selector_token_used=True,
        variant="bubble",
        gates=[{"gate": "mechanism", "fired": False, "reason_code": None}],
        simulate_attempts=[{"n": 0, "ok": True, "error_code": None}],
        first_attempt_ok=True,
        semantic_ok=None,
        envelope_status="ok",
        envelope_error_code=None,
        envelope_failure_category=None,
        source="family_resolved",
        budget_delta=_zero_budget_delta(),
        via_production_pipeline=True,
        infra_error=None,
        detail="",
    )


def test_build_m16_record_pipeline_runtimeerror_khong_phai_infra_error(monkeypatch):
    """RuntimeError từ run_pipeline (simulate cạn retry) LÀ outcome sản phẩm,
    KHÔNG phải infra error — infra_error PHẢI None trừ khi CALLER tự đặt qua
    tham số riêng."""
    mock, counts = _mock(
        _analysis_find_max(),
        classify_seq=[_classify("algorithm.find_max")],
        simulate_seq=["không phải json hợp lệ"] * 3,
    )
    obs = AttemptObserver()
    pipeline_error = None
    try:
        _run(monkeypatch, mock, obs)
        assert False, "phải raise RuntimeError"
    except RuntimeError as err:
        pipeline_error = str(err)

    item = EvalItem("t-exhausted", "Tìm max.", "specialized", "algorithm.find_max")
    rec = build_m16_record(item, obs, None, pipeline_error, _zero_budget_delta())

    assert rec.envelope_status is None
    assert rec.infra_error is None  # KHÔNG tự gán từ pipeline_error
    assert rec.detail == pipeline_error  # tham khảo, không phân loại
    assert len(rec.simulate_attempts) == 3  # có sẵn — không mất dữ liệu
    assert rec.via_production_pipeline is True  # pipeline_error not None


def test_build_m16_record_infra_error_dat_boi_caller():
    """infra_error CHỈ được set khi CALLER truyền tường minh (lỗi mock/script/
    hạ tầng eval — KHÔNG lẫn với RuntimeError sản phẩm của pipeline)."""
    obs = AttemptObserver()
    item = EvalItem("t-infra", "?", "specialized", "algorithm.find_max")
    rec = build_m16_record(
        item, obs, None, None, _zero_budget_delta(), infra_error="mock script crashed: KeyError('x')"
    )
    assert rec.infra_error == "mock script crashed: KeyError('x')"
