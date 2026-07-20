# -*- coding: utf-8 -*-
"""M16 Task 3 (W3) — test module metric (nguồn yêu cầu:
.superpowers/sdd/m16-task-3-brief.md). TDD: viết TRƯỚC `m16_metrics.py`
(RED xác nhận ImportError trước khi cài đặt).

Toàn bộ fixture là `M16CaseRecord` TỔNG HỢP dựng tay (không chạy pipeline) —
mỗi test tính TAY numerator/denominator/value kỳ vọng, ghi rõ trong comment,
rồi so khớp với module. Vì `M16CaseRecord` (Task 2) không phẳng hoá 3 field
chỉ có trên `M16Expectation` (`analyze_mechanism_expected`/`algorithmic_request`/
`recovery_route_exists` — xem docstring `m16_metrics.py`), các test cần field
đó truyền qua `m16_by_case` (map case_id → `M16Expectation`).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.evaluation import m16_metrics
from app.evaluation.m16_record import M16CaseRecord
from app.evaluation.m16_schema import M16Archetype, M16Expectation
from app.simulation.catalog import CATALOG, SimSpec
from app.simulation.descriptor import ReachabilityLevel

# ── factory: record/m16 tổng hợp với default AN TOÀN, test chỉ override field liên quan ──


def _rec(**overrides) -> M16CaseRecord:
    base = dict(
        case_id="case",
        group="specialized",
        archetype=None,
        expected_family=None,
        expected_initial_route=None,
        expected_final_route=None,
        raw_prescribed=None,
        canonical_prescribed=None,
        result_ownership=None,
        initial_route=None,
        initial_family=None,
        reclassify_attempted=False,
        reclassify_result_route=None,
        final_route=None,
        final_family=None,
        selector_token_used=False,
        variant=None,
        gates=[],
        simulate_attempts=[],
        first_attempt_ok=None,
        semantic_ok=None,
        envelope_status=None,
        envelope_error_code=None,
        envelope_failure_category=None,
        source=None,
        budget_delta={"logical_calls": 0, "http_requests": 0, "retry_requests": 0, "transient_hits": 0},
        via_production_pipeline=True,
        infra_error=None,
        detail="",
    )
    base.update(overrides)
    return M16CaseRecord(**base)


def _m16(**overrides) -> M16Expectation:
    base = dict(
        archetype=M16Archetype.EXPLICIT_POSITIVE,
        expected_family="single_pass_scan",
        expected_initial_route=None,
        expected_gate=None,
        expected_error_code=None,
        analyze_mechanism_expected=None,
        algorithmic_request=False,
        recovery_route_exists=False,
        live_eligible=False,
        notes="fixture test",
    )
    base.update(overrides)
    return M16Expectation(**base)


# ═══════════════════════ MetricValue / quality_band ═══════════════════════


def test_metric_value_zero_denominator_la_none_khong_phai_zero():
    mv = m16_metrics.MetricValue.of("x", 0, 0)
    assert mv.numerator == 0
    assert mv.denominator == 0
    assert mv.value is None


def test_metric_value_nonzero_denominator():
    mv = m16_metrics.MetricValue.of("x", 3, 4)
    assert mv.value == 0.75


def test_quality_band_boundaries():
    assert m16_metrics.quality_band(None) == "N/A"
    assert m16_metrics.quality_band(0.899) == "MODERATE"
    assert m16_metrics.quality_band(0.90) == "STRONG"
    assert m16_metrics.quality_band(0.75) == "MODERATE"
    assert m16_metrics.quality_band(0.7499) == "WEAK"
    assert m16_metrics.quality_band(1.0) == "STRONG"
    assert m16_metrics.quality_band(0.0) == "WEAK"


# ═══════════════════════ 16 metric tỉ lệ (per-metric, hand-computed) ═══════


def test_metric_1_analyze_mechanism_accuracy():
    records = [
        _rec(case_id="c1", canonical_prescribed="comparison_sort.adjacent_compare_swap"),
        _rec(case_id="c2", canonical_prescribed="comparison_sort.adjacent_compare_swap"),
        _rec(case_id="c3", canonical_prescribed=None),  # loại: analyze_mechanism_expected=None
    ]
    m16_by_case = {
        "c1": _m16(analyze_mechanism_expected="comparison_sort.adjacent_compare_swap"),
        "c2": _m16(analyze_mechanism_expected="comparison_sort.shift_into_sorted_prefix"),
    }
    mv = m16_metrics.metric_analyze_mechanism_accuracy(records, m16_by_case)
    assert (mv.numerator, mv.denominator, mv.value) == (1, 2, 0.5)


def test_metric_2_family_selection_accuracy():
    records = [
        _rec(case_id="b1", group="specialized", expected_family="single_pass_scan", final_family="single_pass_scan"),
        _rec(case_id="b2", group="generic", expected_family="boolean_composition", final_family="generic_dual"),
        _rec(case_id="b3", group="unsupported", expected_family="graph_traversal", final_family=None),
        _rec(case_id="b4", group="specialized", expected_family=None, final_family="single_pass_scan"),
    ]
    mv = m16_metrics.metric_family_selection_accuracy(records)
    assert (mv.numerator, mv.denominator, mv.value) == (1, 2, 0.5)


def test_metric_3_variant_selection_accuracy():
    records = [
        _rec(
            case_id="c1", group="specialized", expected_initial_route="algorithm.comparison_sort",
            final_route="algorithm.bubble_sort", expected_final_route="algorithm.bubble_sort",
        ),
        _rec(
            case_id="c2", group="specialized", expected_initial_route="algorithm.comparison_sort",
            final_route="algorithm.insertion_sort", expected_final_route="algorithm.bubble_sort",
        ),
        _rec(case_id="c3", group="specialized", expected_initial_route="algorithm.find_max"),  # loại: không phải token sorting
    ]
    mv = m16_metrics.metric_variant_selection_accuracy(records)
    assert (mv.numerator, mv.denominator, mv.value) == (1, 2, 0.5)


def test_metric_4_initial_route_accuracy():
    records = [
        _rec(case_id="d1", group="specialized", initial_route="algorithm.find_max", expected_initial_route="algorithm.find_max"),
        _rec(case_id="d2", group="generic", initial_route=None, expected_initial_route="generic.rule_scene"),
        _rec(case_id="d3", group="unsupported", initial_route="algorithm.find_max", expected_initial_route="algorithm.find_max"),
    ]
    mv = m16_metrics.metric_initial_route_accuracy(records)
    assert (mv.numerator, mv.denominator, mv.value) == (1, 2, 0.5)


def test_metric_5_final_route_accuracy():
    records = [
        _rec(
            case_id="e1", group="specialized", envelope_status="ok",
            final_route="algorithm.find_max", expected_final_route="algorithm.find_max",
        ),
        _rec(
            case_id="e2", group="specialized", envelope_status="unsupported",
            final_route=None, expected_final_route="algorithm.find_min",
        ),
        _rec(case_id="e3", group="unsupported", envelope_status="unsupported"),
    ]
    mv = m16_metrics.metric_final_route_accuracy(records)
    assert (mv.numerator, mv.denominator, mv.value) == (1, 2, 0.5)


def test_metric_6_valid_spec_first_attempt_rate():
    records = [
        _rec(case_id="f1", group="specialized", simulate_attempts=[{"n": 1, "ok": True, "error_code": None}], first_attempt_ok=True),
        _rec(
            case_id="f2", group="generic",
            simulate_attempts=[{"n": 1, "ok": False, "error_code": "structural_invalid"}, {"n": 2, "ok": True, "error_code": None}],
            first_attempt_ok=False,
        ),
        _rec(case_id="f3", group="specialized", simulate_attempts=[], first_attempt_ok=None),
    ]
    mv = m16_metrics.metric_valid_spec_first_attempt_rate(records)
    assert (mv.numerator, mv.denominator, mv.value) == (1, 2, 0.5)


def test_metric_7_semantic_pass_rate():
    """Final review A: mẫu số CHỈ gồm case check_semantic thật sự chạy — đường
    generic (final_route generic.rule_scene). Harness đặt semantic_ok=True cho
    MỌI envelope ok kể cả specialized (nơi check KHÔNG chạy) — record g4 mô
    phỏng đúng thực tế đó và PHẢI bị loại khỏi mẫu số (không pha loãng)."""
    records = [
        _rec(case_id="g1", group="generic", final_route="generic.rule_scene", semantic_ok=True),
        _rec(case_id="g2", group="generic", final_route="generic.rule_scene", semantic_ok=False),
        _rec(case_id="g3", group="specialized", semantic_ok=None),
        _rec(case_id="g4", group="specialized", final_route="algorithm.find_max", semantic_ok=True),
    ]
    mv = m16_metrics.metric_semantic_pass_rate(records)
    assert (mv.numerator, mv.denominator, mv.value) == (1, 2, 0.5)


def test_metric_8_false_refusal_rate():
    records = [
        _rec(case_id="h1", group="specialized", envelope_status="ok"),
        _rec(case_id="h2", group="generic", envelope_status="unsupported"),
        _rec(case_id="h3", group="unsupported", envelope_status="unsupported"),
    ]
    mv = m16_metrics.metric_false_refusal_rate(records)
    assert (mv.numerator, mv.denominator, mv.value) == (1, 2, 0.5)


def test_metric_9_va_10_precision_recall_doc_lap_khong_tron():
    """brief: 'precision/recall không trộn' — chung MỘT fixture, hai mẫu số
    KHÁC NHAU (recall: group==unsupported; precision: mọi case refused) → giá
    trị khác nhau (0.667 vs 0.5), chứng minh không lẫn logic."""
    records = [
        _rec(case_id="pr1", group="unsupported", envelope_status="unsupported"),  # TP
        _rec(case_id="pr2", group="unsupported", envelope_status="unsupported"),  # TP
        _rec(case_id="pr3", group="unsupported", envelope_status="ok"),  # FN (bỏ lọt)
        _rec(case_id="pr4", group="specialized", envelope_status="unsupported"),  # false refusal
        _rec(case_id="pr5", group="generic", envelope_status="unsupported"),  # false refusal
        _rec(case_id="pr6", group="generic", envelope_status="ok"),  # true negative, loại cả hai
    ]
    recall = m16_metrics.metric_unsupported_recall(records)
    precision = m16_metrics.metric_unsupported_precision(records)
    # recall: mẫu số group==unsupported = {pr1,pr2,pr3} = 3; tử số refused = {pr1,pr2} = 2
    assert (recall.numerator, recall.denominator) == (2, 3)
    assert recall.value == pytest.approx(2 / 3)
    # precision: mẫu số refused = {pr1,pr2,pr4,pr5} = 4; tử số group==unsupported = {pr1,pr2} = 2
    assert (precision.numerator, precision.denominator) == (2, 4)
    assert precision.value == 0.5
    assert recall.value != precision.value


def test_metric_11_false_positive_simulation_rate():
    records = [
        _rec(case_id="k1", group="unsupported", envelope_status="ok"),
        _rec(case_id="k2", group="unsupported", envelope_status="unsupported"),
        _rec(case_id="k3", group="specialized", envelope_status="ok"),
    ]
    mv = m16_metrics.metric_false_positive_simulation_rate(records)
    assert (mv.numerator, mv.denominator, mv.value) == (1, 2, 0.5)


def test_metric_12_generic_fallback_leak_rate():
    records = [
        _rec(case_id="l1", group="unsupported", envelope_status="ok", final_route="generic.rule_scene"),
        _rec(case_id="l2", group="unsupported", envelope_status="unsupported"),
        _rec(case_id="l3", group="unsupported", envelope_status="ok", final_route="generic.rule_scene"),
    ]
    m16_by_case = {
        "l1": _m16(algorithmic_request=True),
        "l2": _m16(algorithmic_request=True),
        "l3": _m16(algorithmic_request=False),  # loại khỏi mẫu số
    }
    mv = m16_metrics.metric_generic_fallback_leak_rate(records, m16_by_case)
    assert (mv.numerator, mv.denominator, mv.value) == (1, 2, 0.5)


def test_metric_13_reclassification_rate_loai_infra_error():
    records = [
        _rec(case_id="m1", reclassify_attempted=True, infra_error=None),
        _rec(case_id="m2", reclassify_attempted=False, infra_error=None),
        _rec(case_id="m3", reclassify_attempted=True, infra_error="mock crash"),  # loại: infra_error
    ]
    mv = m16_metrics.metric_reclassification_rate(records)
    assert (mv.numerator, mv.denominator, mv.value) == (1, 2, 0.5)


def test_metric_13_reclassification_rate_loai_internal_fixture_route():
    """rule loại internal-fixture: record chạm route CATALOG reachability
    chứa internal_fixture — CATALOG hiện KHÔNG entry nào mang cờ này nên test
    bằng patch.dict tạm thời (brief §4 preamble)."""
    fixture_id = "algorithm.__m16_test_internal_fixture__"
    fake_spec = SimSpec(
        simulation_id=fixture_id,
        domain="algorithm",
        visual_mode="2d",
        description="",
        config_schema={},
        contract="",
        validate=lambda cfg: (None, "n/a"),
        make_title=lambda c, a: "",
        reachability=(ReachabilityLevel.INTERNAL_FIXTURE,),
    )
    records = [
        _rec(case_id="pf1", final_route=fixture_id, reclassify_attempted=True, infra_error=None),
        _rec(
            case_id="pf2", final_route="algorithm.find_max", envelope_status="ok",
            reclassify_attempted=False, infra_error=None,
        ),
    ]
    assert fixture_id not in CATALOG  # tiền đề: catalog thật không có fixture này
    with patch.dict(CATALOG, {fixture_id: fake_spec}):
        mv = m16_metrics.metric_reclassification_rate(records)
    assert (mv.numerator, mv.denominator, mv.value) == (0, 1, 0.0)


def test_metric_14_route_recovery_success_rate():
    records = [
        _rec(
            case_id="n1", reclassify_attempted=True, envelope_status="ok",
            final_route="binary.decimal_to_binary", expected_final_route="binary.decimal_to_binary",
        ),
        _rec(case_id="n2", reclassify_attempted=True, envelope_status="unsupported", final_route=None, expected_final_route="binary.decimal_to_binary"),
        _rec(case_id="n3", reclassify_attempted=True, envelope_status="ok", final_route="x", expected_final_route="x"),
        _rec(case_id="n4", reclassify_attempted=False),
    ]
    m16_by_case = {
        "n1": _m16(recovery_route_exists=True),
        "n2": _m16(recovery_route_exists=True),
        "n3": _m16(recovery_route_exists=False),  # loại khỏi mẫu số
    }
    mv = m16_metrics.metric_route_recovery_success_rate(records, m16_by_case)
    assert (mv.numerator, mv.denominator, mv.value) == (1, 2, 0.5)


def test_metric_15_retry_channels_ba_kenh_rieng():
    records = [
        _rec(
            case_id="o1", simulate_attempts=[{"n": 1, "ok": True, "error_code": None}],
            budget_delta={"logical_calls": 1, "http_requests": 1, "retry_requests": 0, "transient_hits": 0},
            reclassify_attempted=False,
        ),
        _rec(
            case_id="o2",
            simulate_attempts=[
                {"n": 1, "ok": False, "error_code": "structural_invalid"},
                {"n": 2, "ok": False, "error_code": "structural_invalid"},
                {"n": 3, "ok": True, "error_code": None},
            ],
            budget_delta={"logical_calls": 3, "http_requests": 5, "retry_requests": 2, "transient_hits": 0},
            reclassify_attempted=True,
        ),
        _rec(
            case_id="o3", simulate_attempts=[],
            budget_delta={"logical_calls": 1, "http_requests": 2, "retry_requests": 1, "transient_hits": 1},
            reclassify_attempted=True,
        ),
    ]
    rc = m16_metrics.metric_retry_channels(records)
    # semantic: max(0,1-1)=0 + max(0,3-1)=2 + max(0,0-1)=0 → total=2, avg=2/3
    assert rc.semantic_retries_total == 2
    assert rc.semantic_retries_avg == pytest.approx(2 / 3)
    # transient: 0+2+1=3, avg=1.0 (KHÔNG dùng transient_hits — kênh riêng)
    assert rc.transient_retries_total == 3
    assert rc.transient_retries_avg == pytest.approx(1.0)
    # reclassify: 0+1+1=2, avg=2/3
    assert rc.reclassify_count_total == 2
    assert rc.reclassify_count_avg == pytest.approx(2 / 3)
    # 3 kênh KHÔNG trộn: tổng semantic != tổng transient dù cùng fixture
    assert rc.semantic_retries_total != rc.transient_retries_total


def test_metric_15_retry_channels_zero_case_avg_none():
    rc = m16_metrics.metric_retry_channels([])
    assert rc.semantic_retries_total == 0
    assert rc.semantic_retries_avg is None
    assert rc.transient_retries_avg is None
    assert rc.reclassify_count_avg is None


def test_metric_16_concrete_envelope_integrity():
    records = [
        _rec(case_id="p1", envelope_status="ok", final_route="algorithm.find_max"),
        _rec(case_id="p2", envelope_status="ok", final_route="algorithm.comparison_sort"),  # selector token — VI PHẠM
        _rec(case_id="p3", envelope_status="unsupported"),
    ]
    mv = m16_metrics.metric_concrete_envelope_integrity(records)
    assert (mv.numerator, mv.denominator, mv.value) == (1, 2, 0.5)


def test_metric_16_concrete_envelope_integrity_route_khong_trong_catalog():
    records = [_rec(case_id="p4", envelope_status="ok", final_route="algorithm.__khong_ton_tai__")]
    mv = m16_metrics.metric_concrete_envelope_integrity(records)
    assert (mv.numerator, mv.denominator, mv.value) == (0, 1, 0.0)


def test_metric_17_production_evaluation_parity_khong_loc_product_case():
    """Phân xử review Task 3: #17 đo trên 'MỌI evaluated case' — cố ý KHÔNG
    lọc product-case. Nếu lọc infra_error thì parity tự-triệt-tiêu đúng tín
    hiệu nó phải bắt (record không đi qua production pipeline vì harness
    crash trước pipeline) → làm mù bất biến #22. Record q3 (infra_error +
    via=False) PHẢI kéo parity xuống."""
    records = [
        _rec(case_id="q1", via_production_pipeline=True),
        _rec(case_id="q2", via_production_pipeline=False),
        _rec(case_id="q3", via_production_pipeline=False, infra_error="mock crash"),  # VẪN trong mẫu số
    ]
    mv = m16_metrics.metric_production_evaluation_parity(records)
    assert (mv.numerator, mv.denominator) == (1, 3)
    assert mv.value == pytest.approx(1 / 3)


def test_product_case_filter_ap_dung_cho_nhieu_metric_khong_chi_13():
    """brief §4 câu cuối: 'internal-fixture record bị loại khỏi product
    METRICS' (số nhiều) — kiểm CẢ metric #5 (final_route_accuracy, không
    liên quan #13/#17) cũng loại record chạm route internal-fixture, chứng
    minh cổng product-case là CHUNG cho toàn bộ registry, không riêng #13."""
    fixture_id = "algorithm.__m16_test_cross_cutting_fixture__"
    fake_spec = SimSpec(
        simulation_id=fixture_id,
        domain="algorithm",
        visual_mode="2d",
        description="",
        config_schema={},
        contract="",
        validate=lambda cfg: (None, "n/a"),
        make_title=lambda c, a: "",
        reachability=(ReachabilityLevel.INTERNAL_FIXTURE,),
    )
    records = [
        _rec(
            case_id="cc1", group="specialized", envelope_status="ok",
            final_route=fixture_id, expected_final_route=fixture_id,
        ),
        _rec(
            case_id="cc2", group="specialized", envelope_status="ok",
            final_route="algorithm.find_max", expected_final_route="algorithm.find_max",
        ),
    ]
    with patch.dict(CATALOG, {fixture_id: fake_spec}):
        mv = m16_metrics.metric_final_route_accuracy(records)
    # cc1 (chạm route internal-fixture) bị loại khỏi mẫu số dù group=supported hợp lệ
    assert (mv.numerator, mv.denominator, mv.value) == (1, 1, 1.0)


# ═══════════════════════ failure taxonomy (structured-only) ═══════════════


def test_classify_failures_happy_path_rong():
    r = _rec(case_id="happy", group="specialized", envelope_status="ok")
    assert m16_metrics.classify_failures(r) == []


def test_taxonomy_transient_provider_error_khong_doi_outcome():
    r_ok = _rec(
        case_id="t1", group="specialized", envelope_status="ok",
        budget_delta={"logical_calls": 1, "http_requests": 2, "retry_requests": 1, "transient_hits": 1},
    )
    r_none = _rec(case_id="t2", group="specialized", envelope_status="ok")
    assert "TRANSIENT_PROVIDER_ERROR" in m16_metrics.classify_failures(r_ok)
    assert "TRANSIENT_PROVIDER_ERROR" not in m16_metrics.classify_failures(r_none)


def test_taxonomy_evaluation_infrastructure_error():
    r = _rec(case_id="i1", infra_error="mock hỏng")
    assert "EVALUATION_INFRASTRUCTURE_ERROR" in m16_metrics.classify_failures(r)
    r2 = _rec(case_id="i2", infra_error=None)
    assert "EVALUATION_INFRASTRUCTURE_ERROR" not in m16_metrics.classify_failures(r2)


def test_taxonomy_analyze_mechanism_error():
    r = _rec(case_id="am1", canonical_prescribed="comparison_sort.adjacent_compare_swap")
    m16_by_case = {"am1": _m16(analyze_mechanism_expected="comparison_sort.shift_into_sorted_prefix")}
    assert "ANALYZE_MECHANISM_ERROR" in m16_metrics.classify_failures(r, m16_by_case)
    m16_by_case_match = {"am1": _m16(analyze_mechanism_expected="comparison_sort.adjacent_compare_swap")}
    assert "ANALYZE_MECHANISM_ERROR" not in m16_metrics.classify_failures(r, m16_by_case_match)


def test_taxonomy_initial_family_selection_error_ke_ca_initial_route_none():
    r_mismatch = _rec(case_id="if1", group="specialized", expected_family="single_pass_scan", initial_family="comparison_sort")
    assert "INITIAL_FAMILY_SELECTION_ERROR" in m16_metrics.classify_failures(r_mismatch)
    # initial_route None (→ initial_family None) NHƯNG expected_family có → VẪN tính
    r_none = _rec(case_id="if2", group="specialized", expected_family="single_pass_scan", initial_route=None, initial_family=None)
    assert "INITIAL_FAMILY_SELECTION_ERROR" in m16_metrics.classify_failures(r_none)
    r_match = _rec(case_id="if3", group="specialized", expected_family="single_pass_scan", initial_family="single_pass_scan")
    assert "INITIAL_FAMILY_SELECTION_ERROR" not in m16_metrics.classify_failures(r_match)


def test_taxonomy_initial_variant_selection_error():
    r = _rec(
        case_id="iv1", group="specialized",
        simulate_attempts=[{"n": 1, "ok": False, "error_code": "mechanism_variant_mismatch"}],
    )
    assert "INITIAL_VARIANT_SELECTION_ERROR" in m16_metrics.classify_failures(r)
    r2 = _rec(case_id="iv2", group="specialized", simulate_attempts=[{"n": 1, "ok": True, "error_code": None}])
    assert "INITIAL_VARIANT_SELECTION_ERROR" not in m16_metrics.classify_failures(r2)


def test_taxonomy_route_mechanism_family_mismatch():
    r = _rec(case_id="rm1", gates=[{"gate": "route_mechanism", "fired": True, "reason_code": "route_mechanism_family_mismatch"}])
    assert "ROUTE_MECHANISM_FAMILY_MISMATCH" in m16_metrics.classify_failures(r)
    r2 = _rec(case_id="rm2", gates=[{"gate": "route_mechanism", "fired": False, "reason_code": None}])
    assert "ROUTE_MECHANISM_FAMILY_MISMATCH" not in m16_metrics.classify_failures(r2)


def test_taxonomy_gate_mechanism_ownership_hai_nhanh():
    r_error_code = _rec(case_id="go1", envelope_error_code="gate_mechanism_ownership")
    assert "GATE_MECHANISM_OWNERSHIP" in m16_metrics.classify_failures(r_error_code)
    r_gate = _rec(
        case_id="go2", envelope_error_code=None,
        gates=[{"gate": "mechanism", "fired": True, "reason_code": "gate_mechanism_ownership"}],
    )
    assert "GATE_MECHANISM_OWNERSHIP" in m16_metrics.classify_failures(r_gate)
    r_neither = _rec(case_id="go3", envelope_error_code=None, gates=[{"gate": "mechanism", "fired": False, "reason_code": None}])
    assert "GATE_MECHANISM_OWNERSHIP" not in m16_metrics.classify_failures(r_neither)


def test_taxonomy_family_spec_invalid_va_concrete_config_invalid():
    r_family = _rec(
        case_id="fs1",
        simulate_attempts=[
            {"n": 1, "ok": False, "error_code": "structural_invalid"},
            {"n": 2, "ok": False, "error_code": "family_spec_invalid"},
        ],
    )
    cats = m16_metrics.classify_failures(r_family)
    assert "FAMILY_SPEC_INVALID" in cats
    assert "CONCRETE_CONFIG_INVALID" not in cats

    r_concrete = _rec(
        case_id="cc1",
        simulate_attempts=[{"n": 1, "ok": False, "error_code": "structural_invalid"}],
    )
    cats2 = m16_metrics.classify_failures(r_concrete)
    assert "CONCRETE_CONFIG_INVALID" in cats2
    assert "FAMILY_SPEC_INVALID" not in cats2

    # attempt cuối OK → không thuộc "mọi attempt fail" → không category nào
    r_recovered = _rec(
        case_id="rec1",
        simulate_attempts=[{"n": 1, "ok": False, "error_code": "structural_invalid"}, {"n": 2, "ok": True, "error_code": None}],
    )
    cats3 = m16_metrics.classify_failures(r_recovered)
    assert "CONCRETE_CONFIG_INVALID" not in cats3
    assert "FAMILY_SPEC_INVALID" not in cats3


def test_taxonomy_semantic_validation_failed_hai_nhanh():
    r_flag = _rec(case_id="sv1", semantic_ok=False)
    assert "SEMANTIC_VALIDATION_FAILED" in m16_metrics.classify_failures(r_flag)

    r_all_fail = _rec(
        case_id="sv2", semantic_ok=None,
        simulate_attempts=[
            {"n": 1, "ok": False, "error_code": "scene_mode_mismatch"},
            {"n": 2, "ok": False, "error_code": "semantic_incompat"},
        ],
    )
    assert "SEMANTIC_VALIDATION_FAILED" in m16_metrics.classify_failures(r_all_fail)

    r_pass = _rec(case_id="sv3", semantic_ok=True)
    assert "SEMANTIC_VALIDATION_FAILED" not in m16_metrics.classify_failures(r_pass)


def test_taxonomy_false_refusal():
    r = _rec(case_id="fr1", group="specialized", envelope_status="unsupported")
    assert "FALSE_REFUSAL" in m16_metrics.classify_failures(r)
    r_ok = _rec(case_id="fr2", group="specialized", envelope_status="ok")
    assert "FALSE_REFUSAL" not in m16_metrics.classify_failures(r_ok)
    # unsupported group bị refused là ĐÚNG — không phải false refusal
    r_correct = _rec(case_id="fr3", group="unsupported", envelope_status="unsupported")
    assert "FALSE_REFUSAL" not in m16_metrics.classify_failures(r_correct)


def test_taxonomy_false_positive_simulation():
    r = _rec(case_id="fp1", group="unsupported", envelope_status="ok")
    assert "FALSE_POSITIVE_SIMULATION" in m16_metrics.classify_failures(r)
    r2 = _rec(case_id="fp2", group="unsupported", envelope_status="unsupported")
    assert "FALSE_POSITIVE_SIMULATION" not in m16_metrics.classify_failures(r2)


def test_taxonomy_generic_fallback_leak():
    r = _rec(case_id="gl1", group="unsupported", envelope_status="ok", final_route="generic.rule_scene")
    m16_by_case = {"gl1": _m16(algorithmic_request=True)}
    assert "GENERIC_FALLBACK_LEAK" in m16_metrics.classify_failures(r, m16_by_case)
    # thiếu algorithmic_request → không leak (dù final_route/ok khớp)
    m16_by_case_false = {"gl1": _m16(algorithmic_request=False)}
    assert "GENERIC_FALLBACK_LEAK" not in m16_metrics.classify_failures(r, m16_by_case_false)
    # final_route khác generic.rule_scene → không leak
    r2 = _rec(case_id="gl2", group="unsupported", envelope_status="ok", final_route="algorithm.find_max")
    assert "GENERIC_FALLBACK_LEAK" not in m16_metrics.classify_failures(r2, {"gl2": _m16(algorithmic_request=True)})


def test_taxonomy_executor_oracle_mismatch_reserved():
    r = _rec(case_id="om1")
    assert "EXECUTOR_ORACLE_MISMATCH" not in m16_metrics.classify_failures(r)
    assert "EXECUTOR_ORACLE_MISMATCH" in m16_metrics.classify_failures(r, oracle_mismatch=True)


def test_taxonomy_recovery_giu_ca_initial_error_lan_final_dung():
    """brief: 'initial-error + recovery-success giữ CẢ hai (INITIAL_FAMILY_
    SELECTION_ERROR vẫn trong failure list khi final đúng)' — case biên
    quan trọng nhất của taxonomy."""
    r = _rec(
        case_id="cr1", group="specialized",
        expected_family="positional_representation", initial_family="interval_elimination",  # sai family lúc đầu
        gates=[{"gate": "route_mechanism", "fired": True, "reason_code": "route_mechanism_family_mismatch"}],
        reclassify_attempted=True,
        envelope_status="ok", final_route="binary.decimal_to_binary", expected_final_route="binary.decimal_to_binary",
    )
    m16_by_case = {"cr1": _m16(expected_family="positional_representation", recovery_route_exists=True)}
    cats = m16_metrics.classify_failures(r, m16_by_case)
    assert "INITIAL_FAMILY_SELECTION_ERROR" in cats
    assert "ROUTE_MECHANISM_FAMILY_MISMATCH" in cats
    assert "ROUTE_RECOVERY_FAILED" not in cats  # recovery THÀNH CÔNG
    assert "FALSE_REFUSAL" not in cats  # envelope ok, không refused

    # metric #14 cũng phải phản ánh THÀNH CÔNG cho case tương tự
    mv14 = m16_metrics.metric_route_recovery_success_rate([r], m16_by_case)
    assert (mv14.numerator, mv14.denominator) == (1, 1)


def test_taxonomy_route_recovery_failed():
    r = _rec(
        case_id="cr2", group="specialized",
        reclassify_attempted=True, envelope_status="unsupported", final_route=None,
        expected_final_route="algorithm.bubble_sort",
    )
    m16_by_case = {"cr2": _m16(recovery_route_exists=True)}
    cats = m16_metrics.classify_failures(r, m16_by_case)
    assert "ROUTE_RECOVERY_FAILED" in cats
    assert "FALSE_REFUSAL" in cats  # supported nhưng bị refused — cả hai đồng thời


# ═══════════════════════ confusion matrix ═════════════════════════════════


def test_confusion_matrix_rows_cols():
    records = [
        _rec(case_id="cm1", expected_final_route="algorithm.find_max", envelope_status="ok", final_route="algorithm.find_max"),
        _rec(case_id="cm2", expected_final_route="algorithm.find_max", envelope_status="ok", final_route="algorithm.find_min"),
        _rec(case_id="cm3", expected_final_route=None, envelope_status="unsupported", final_route=None),
        _rec(case_id="cm4", expected_final_route="generic.rule_scene", envelope_status=None, final_route=None),
    ]
    matrix = m16_metrics.confusion_matrix(records)
    assert matrix == {
        "algorithm.find_max": {"algorithm.find_max": 1, "algorithm.find_min": 1},
        "expected_refusal": {"refused": 1},
        "generic.rule_scene": {"error": 1},
    }


# ═══════════════════════ run_label ════════════════════════════════════════


def test_aggregate_run_label_khong_hop_le_raise():
    with pytest.raises(ValueError):
        m16_metrics.aggregate([], "khong_hop_le")


def test_aggregate_run_label_hop_le_khong_ghi_de_lan_nhau():
    r_offline = m16_metrics.aggregate([], "offline")
    r_live_baseline = m16_metrics.aggregate([], "live_baseline")
    r_live_postfix = m16_metrics.aggregate([], "live_postfix")
    assert r_offline.run_label == "offline"
    assert r_live_baseline.run_label == "live_baseline"
    assert r_live_postfix.run_label == "live_postfix"
    # ba lần gọi độc lập — không có state toàn cục bị chia sẻ/ghi đè
    assert r_offline is not r_live_baseline is not r_live_postfix


# ═══════════════════════ aggregate(): per-family / macro / applicability ══


def _aggregate_fixture() -> list[M16CaseRecord]:
    return [
        _rec(
            case_id="agg-s1", group="specialized", expected_family="single_pass_scan",
            expected_initial_route="algorithm.find_max", initial_route="algorithm.find_max", initial_family="single_pass_scan",
            expected_final_route="algorithm.find_max", final_route="algorithm.find_max", final_family="single_pass_scan",
            envelope_status="ok",
        ),
        _rec(
            case_id="agg-s2", group="specialized", expected_family="single_pass_scan",
            expected_initial_route="algorithm.find_min", initial_route="algorithm.find_min", initial_family="single_pass_scan",
            expected_final_route="algorithm.find_min", final_route="algorithm.find_min", final_family="single_pass_scan",
            envelope_status="ok",
        ),
        _rec(
            case_id="agg-c1", group="specialized", expected_family="comparison_sort",
            expected_initial_route="algorithm.comparison_sort", initial_route="algorithm.comparison_sort", initial_family="comparison_sort",
            expected_final_route="algorithm.bubble_sort", final_route="algorithm.bubble_sort", final_family="comparison_sort",
            envelope_status="ok",
        ),
        _rec(
            # final_family SAI có chủ đích (record tổng hợp, không dẫn từ CATALOG thật) — chỉ để kiểm
            # công thức metric #2 tại biên, không kiểm tính đúng đắn của family_of_route (đã khóa ở Task 2).
            case_id="agg-c2", group="specialized", expected_family="comparison_sort",
            expected_initial_route="algorithm.comparison_sort", initial_route="algorithm.comparison_sort", initial_family="comparison_sort",
            expected_final_route="algorithm.bubble_sort", final_route="algorithm.insertion_sort", final_family="generic_dual",
            envelope_status="ok",
        ),
        _rec(
            case_id="agg-g1", group="unsupported", expected_family="graph_traversal",
            expected_initial_route=None, initial_route=None, initial_family=None,
            expected_final_route=None, final_route=None, final_family=None,
            envelope_status="unsupported",
        ),
        _rec(
            case_id="agg-u1", group="specialized", expected_family=None,
            expected_initial_route="binary.decimal_to_binary", initial_route="binary.decimal_to_binary", initial_family=None,
            expected_final_route="binary.decimal_to_binary", final_route="binary.decimal_to_binary", final_family="positional_representation",
            envelope_status="ok",
        ),
    ]


def test_aggregate_case_count_va_micro_khop_ham_dung():
    records = _aggregate_fixture()
    result = m16_metrics.aggregate(records, "offline")
    assert result.case_count == 6
    assert result.run_label == "offline"
    # micro của aggregate() PHẢI khớp gọi hàm metric độc lập trên cùng tập
    assert result.metrics["family_selection_accuracy"].micro == m16_metrics.metric_family_selection_accuracy(records)
    assert result.metrics["initial_route_accuracy"].micro == m16_metrics.metric_initial_route_accuracy(records)


def test_aggregate_family_selection_accuracy_per_family_va_macro():
    result = m16_metrics.aggregate(_aggregate_fixture(), "offline")
    agg = result.metrics["family_selection_accuracy"]
    assert agg.micro.numerator == 3 and agg.micro.denominator == 4  # (u1,g1 loại khỏi mẫu số)
    assert agg.per_family["single_pass_scan"].value == 1.0
    assert agg.per_family["comparison_sort"].value == 0.5
    assert agg.per_family["graph_traversal"].value is None  # unsupported → mẫu số 0
    assert agg.per_family["unlabeled"].value is None  # expected_family None → mẫu số 0 (case này)
    assert agg.macro == pytest.approx(0.75)  # mean(1.0, 0.5) — graph_traversal + unlabeled LOẠI
    assert set(agg.excluded_families) == {"graph_traversal", "unlabeled"}


def test_aggregate_initial_route_accuracy_unlabeled_loai_du_co_gia_tri():
    """Khác biệt QUAN TRỌNG với test trên: bucket 'unlabeled' ở ĐÂY có giá
    trị XÁC ĐỊNH (1.0, không None) nhưng VẪN bị loại khỏi macro — chứng minh
    rule 'unlabeled KHÔNG vào macro' độc lập với rule 'value None bị loại'."""
    result = m16_metrics.aggregate(_aggregate_fixture(), "offline")
    agg = result.metrics["initial_route_accuracy"]
    assert agg.per_family["unlabeled"].value == 1.0  # agg-u1: initial_route khớp expected
    assert "unlabeled" in agg.excluded_families  # nhưng vẫn bị loại khỏi macro
    assert agg.per_family["graph_traversal"].value is None  # g1 unsupported → mẫu số 0
    assert "graph_traversal" in agg.excluded_families
    assert agg.macro == pytest.approx(1.0)  # mean(1.0 single_pass_scan, 1.0 comparison_sort)


def test_aggregate_failure_distribution_rong_khi_fixture_sach():
    result = m16_metrics.aggregate(_aggregate_fixture(), "offline")
    assert result.failure_distribution == {}


def test_aggregate_retry_channels_toan_zero_khi_khong_retry():
    result = m16_metrics.aggregate(_aggregate_fixture(), "offline")
    rc = result.retry_channels
    assert rc.semantic_retries_total == 0
    assert rc.transient_retries_total == 0
    assert rc.reclassify_count_total == 0
    assert rc.semantic_retries_avg == 0.0
    assert rc.transient_retries_avg == 0.0
    assert rc.reclassify_count_avg == 0.0


def test_aggregate_applicability_report_may_doc():
    records = _aggregate_fixture()
    result = m16_metrics.aggregate(records, "offline")
    report = result.applicability_report
    assert set(report.keys()) == {
        "analyze_mechanism_accuracy", "family_selection_accuracy", "variant_selection_accuracy",
        "initial_route_accuracy", "final_route_accuracy", "valid_spec_first_attempt_rate",
        "semantic_pass_rate", "false_refusal_rate", "unsupported_recall", "unsupported_precision",
        "false_positive_simulation_rate", "generic_fallback_leak_rate", "reclassification_rate",
        "route_recovery_success_rate", "concrete_envelope_integrity", "production_evaluation_parity",
        "retry_channels",
    }
    fam_sel = report["family_selection_accuracy"]
    assert isinstance(fam_sel["rule"], str) and fam_sel["rule"]
    assert fam_sel["excluded_case_ids"] == ["agg-g1", "agg-u1"]
    assert report["retry_channels"]["excluded_case_ids"] == []


def test_aggregate_confusion_matrix_dung_tren_fixture():
    records = _aggregate_fixture()
    result = m16_metrics.aggregate(records, "offline")
    assert result.confusion_matrix["algorithm.find_max"] == {"algorithm.find_max": 1}
    assert result.confusion_matrix["expected_refusal"] == {"refused": 1}
    assert result.confusion_matrix["algorithm.bubble_sort"] == {
        "algorithm.bubble_sort": 1,
        "algorithm.insertion_sort": 1,
    }
