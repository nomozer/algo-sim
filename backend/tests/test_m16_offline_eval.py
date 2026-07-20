# -*- coding: utf-8 -*-
"""M16 Task 5 (W5) — chạy TOÀN BỘ pool m16 (50 case) qua production
`run_pipeline` với provider scripted per-case (offline, mock `call_gemini`),
build record, compute metric, assert HARD CORRECTNESS + fault-injection.

## Bất biến bảo toàn
- KHÔNG dựng pipeline mirror: mọi record đi qua `harness.evaluate_item` →
  `pipeline.run_pipeline` THẬT + observer thụ động (bất biến #22). Executor
  oracle (validator concrete/family) KHÔNG đụng — script chỉ cấp analysis/
  classify/config, validator THẬT chấm.
- 0 network: `conftest.py` autouse guard patch httpx transports + xoá
  GEMINI_API_KEY. Một case quên mock → `call_gemini` chết ở guard thay vì gọi
  thật → green suite = bằng chứng 0 API call. KHÔNG cần test `_khong_network`
  riêng (guard tự chứng minh).

## Kịch bản
Từ `m16_offline_scripts.SCRIPTS` (module DATA THUẦN, Task 6 tái dùng). Provider
`build_scripted_provider` dispatch theo marker user_text (đếm lượt classify để
phục vụ reclassify — extra_note lượt 2 vẫn chứa "DANH MỤC MÔ PHỎNG").
"""

from __future__ import annotations

import asyncio

from app.ai import pipeline
from app.evaluation import m16_metrics as MM
from app.evaluation.dataset import EvalItem
from app.evaluation.datasets.m16_catalog import M16_ITEMS
from app.evaluation.harness import evaluate_item
from app.evaluation.m16_offline_scripts import (
    CaseScript,
    SCRIPTS,
    build_scripted_provider,
)
from app.evaluation.m16_record import M16CaseRecord
from app.evaluation.m16_schema import (
    M16Archetype,
    M16Expectation,
    frozen_dataset_fingerprint,
)
from app.simulation.families import FAMILY_SELECTORS

# PIN fingerprint DATASET 30 case — khoá độc lập ở test_m16_schema.py
# (_FROZEN_FINGERPRINT_PIN). Sửa DATASET → CẢ HAI test đỏ. Dán ở đây để chứng
# minh chạy trọn eval M16 KHÔNG mutate DATASET lịch sử.
_FROZEN_PIN = "86e5a31db6d5a11c677dad95842e5ed6eaafc3b373afea651c49ef5258021dbf"

_SELECTOR_TOKENS = frozenset(s.selector_token for s in FAMILY_SELECTORS.values())


# ── chạy trọn pool → list[M16CaseRecord] (production lifecycle) ──
def _run_pool(monkeypatch) -> list[M16CaseRecord]:
    records: list[M16CaseRecord] = []
    for it in M16_ITEMS:
        assert it.id in SCRIPTS, f"thiếu kịch bản offline cho case {it.id}"
        fake, _counts = build_scripted_provider(SCRIPTS[it.id])
        monkeypatch.setattr(pipeline, "call_gemini", fake)
        sink: list = []
        asyncio.run(evaluate_item(it, "khoa-gia", record_sink=sink))
        assert len(sink) == 1, f"{it.id}: evaluate_item không append đúng 1 record"
        records.append(sink[0])
    return records


def _m16_by_case() -> dict[str, M16Expectation]:
    return {it.id: it.m16 for it in M16_ITEMS if it.m16 is not None}


# ── 1. TOÀN BỘ pool qua production pipeline — không case nào infra_error ──
def test_toan_bo_pool_m16_qua_production_pipeline(monkeypatch):
    records = _run_pool(monkeypatch)
    assert len(records) == len(M16_ITEMS) == 50
    for r in records:
        assert r.infra_error is None, f"{r.case_id}: infra_error={r.infra_error!r}"
        # bất biến #22 — mọi record đi qua production run_pipeline
        assert r.via_production_pipeline is True, f"{r.case_id}: KHÔNG qua production pipeline"
    # số record == số case, id khớp đúng pool (không trùng, không sót)
    assert {r.case_id for r in records} == {it.id for it in M16_ITEMS}


# ── 2. HARD CORRECTNESS ──
def test_hard_correctness(monkeypatch):
    records = _run_pool(monkeypatch)
    m16 = _m16_by_case()

    # (a) không mô phỏng dương-tính-giả cho đề đáng lẽ từ chối
    fp = MM.metric_false_positive_simulation_rate(records, m16)
    assert fp.numerator == 0, f"false_positive_simulation numerator={fp.numerator}"
    # (b) không rò rỉ generic-fallback cho đề đòi thuật toán
    leak = MM.metric_generic_fallback_leak_rate(records, m16)
    assert leak.numerator == 0, f"generic_fallback_leak numerator={leak.numerator}"
    # Review Task 5 Minor: mẫu số phải > 0 — nếu pool mất hết case
    # unsupported-algorithmic thì leak=0 chỉ là đúng-rỗng (vacuous), không phải
    # bằng chứng.
    assert leak.denominator > 0, "leak denominator rỗng — hard-correctness thành vacuous"
    # (c) mọi ok-envelope là CONCRETE id trong CATALOG, KHÔNG token selector
    integ = MM.metric_concrete_envelope_integrity(records, m16)
    assert integ.value == 1.0, f"concrete_envelope_integrity={integ}"
    # (d) mọi evaluated case đi qua production pipeline (bất biến #22)
    parity = MM.metric_production_evaluation_parity(records, m16)
    assert parity.value == 1.0, f"production_evaluation_parity={parity}"
    # (e) token selector KHÔNG BAO GIỜ là envelope id
    for r in records:
        if r.envelope_status == "ok":
            assert r.final_route not in _SELECTOR_TOKENS, f"{r.case_id}: token leak {r.final_route}"
    # (f) frozen fingerprint nguyên (chạy eval KHÔNG mutate DATASET)
    assert frozen_dataset_fingerprint() == _FROZEN_PIN

    # ── số HARD CORRECTNESS bổ trợ (không mâu thuẫn, siết chặt hơn) ──
    assert MM.metric_unsupported_recall(records, m16).value == 1.0
    assert MM.metric_false_refusal_rate(records, m16).numerator == 0
    assert MM.metric_final_route_accuracy(records, m16).value == 1.0
    assert MM.metric_family_selection_accuracy(records, m16).value == 1.0
    assert MM.metric_analyze_mechanism_accuracy(records, m16).value == 1.0
    assert MM.metric_route_recovery_success_rate(records, m16).value == 1.0


# ── 3. Báo cáo metric TÁI LẬP (chạy 2 lần cùng kết quả) ──
def test_metric_bao_cao_tai_lap(monkeypatch):
    m16 = _m16_by_case()
    a1 = MM.aggregate(_run_pool(monkeypatch), "offline", m16)
    a2 = MM.aggregate(_run_pool(monkeypatch), "offline", m16)

    assert a1.case_count == a2.case_count == 50
    assert a1.metrics.keys() == a2.metrics.keys()
    for name in a1.metrics:
        assert a1.metrics[name].micro == a2.metrics[name].micro, f"micro lệch: {name}"
        assert a1.metrics[name].macro == a2.metrics[name].macro, f"macro lệch: {name}"
        assert a1.metrics[name].per_family == a2.metrics[name].per_family, f"per_family lệch: {name}"
    assert a1.retry_channels == a2.retry_channels
    assert a1.failure_distribution == a2.failure_distribution
    assert a1.confusion_matrix == a2.confusion_matrix


# ── 4. Đối chiếu outcome TỪNG case với M16 expectation ──
def test_expected_outcome_tung_case(monkeypatch):
    records = _run_pool(monkeypatch)
    by = {r.case_id: r for r in records}
    for it in M16_ITEMS:
        r = by[it.id]
        m = it.m16
        if it.group == "unsupported":
            assert r.envelope_status == "unsupported", f"{it.id}: KHÔNG refused (env={r.envelope_status})"
            # recovery-FAILURE (đường (a) cố định trong script)
            if m.archetype == M16Archetype.CROSS_FAMILY_RECOVERY:
                assert r.reclassify_attempted is True, f"{it.id}: recovery-fail thiếu reclassify"
                assert r.envelope_error_code == "route_mechanism_family_mismatch", (
                    f"{it.id}: error_code={r.envelope_error_code}"
                )
        else:  # supported (specialized | generic)
            assert r.envelope_status == "ok", f"{it.id}: envelope không ok (status={r.envelope_status})"
            assert r.final_route == it.expect_simulation_id, (
                f"{it.id}: final_route={r.final_route} != {it.expect_simulation_id}"
            )
            # recovery-SUCCESS: qua reclassify thật rồi tới target đúng
            if m.archetype == M16Archetype.CROSS_FAMILY_RECOVERY:
                assert r.reclassify_attempted is True, f"{it.id}: recovery-success thiếu reclassify"


# ── 5. Đường gate CỤ THỂ cho các case đa-nhánh (đã cố định trong script) ──
def test_gate_paths_cac_case_da_nhanh(monkeypatch):
    records = _run_pool(monkeypatch)
    by = {r.case_id: r for r in records}

    def gate_fired(rec, gate, code=None):
        return any(
            g.get("gate") == gate and g.get("fired") and (code is None or g.get("reason_code") == code)
            for g in rec.gates
        )

    # partition (quicksort) → mechanism gate tầng 1 (comparison_sort không sở hữu)
    p = by["m16-nm-sort-partition"]
    assert p.envelope_error_code == "gate_mechanism_ownership"
    assert gate_fired(p, "mechanism", "gate_mechanism_ownership")
    assert p.simulate_attempts == []  # gate chặn TRƯỚC simulate

    # hex (đường A): classify binary → direct-route ownership gate
    h = by["m16-nm-hex-gap"]
    assert h.initial_route == "binary.decimal_to_binary"
    assert h.envelope_error_code == "gate_mechanism_ownership"
    assert not h.reclassify_attempted  # cùng family → KHÔNG reclassify

    # cr-fail: reclassify thật (2 classify) vẫn generic → fail-closed mismatch
    f = by["m16-cr-positional-fail"]
    assert f.reclassify_attempted is True
    assert f.envelope_error_code == "route_mechanism_family_mismatch"
    assert gate_fired(f, "route_mechanism", "route_mechanism_family_mismatch")

    # computation-leak: chosen generic + algorithmic → computation gate (capability_gap, KHÔNG error_code)
    c = by["m16-ac-computation-leak"]
    assert c.envelope_status == "unsupported"
    assert c.envelope_failure_category == "capability_gap"
    assert c.envelope_error_code is None
    assert gate_fired(c, "computation")

    # recovery-success: reclassify → binary → ok concrete
    rc = by["m16-cr-positional-recover"]
    assert rc.reclassify_attempted is True
    assert rc.final_route == "binary.decimal_to_binary"
    assert gate_fired(rc, "route_mechanism", "route_mechanism_family_mismatch")

    # retry (contract-error control): 300 bị từ chối attempt1 → attempt2 ok
    ov = by["m16-vb-binary-overrange"]
    assert ov.envelope_status == "ok"
    assert ov.first_attempt_ok is False
    assert any(a.get("ok") for a in ov.simulate_attempts)
    assert len(ov.simulate_attempts) >= 2


# ══════════════ FAULT INJECTION (case tổng hợp RIÊNG, ngoài pool) ══════════════

def _ana(*, ownership="provided", prescribed=None, roles=None) -> dict:
    a: dict = {
        "objects": ["x"], "data": [{"description": "d"}], "relations": [], "processes": [],
        "constraints": [], "goal": "g", "input_description": "i", "output_description": "o",
        "result_ownership": ownership,
    }
    if prescribed is not None:
        a["prescribed_procedure"] = prescribed
    if roles:
        a.update(roles)
    return a


def _exp(**kw) -> M16Expectation:
    base = dict(
        archetype=M16Archetype.NEAR_MISS_GAP, expected_family="graph_traversal",
        expected_initial_route=None, expected_gate=None, expected_error_code=None,
        analyze_mechanism_expected=None,
    )
    base.update(kw)
    return M16Expectation(**base)


def _run_one(monkeypatch, item: EvalItem, script: CaseScript) -> M16CaseRecord:
    fake, _ = build_scripted_provider(script)
    monkeypatch.setattr(pipeline, "call_gemini", fake)
    sink: list = []
    asyncio.run(evaluate_item(item, "khoa-gia", record_sink=sink))
    return sink[0]


def _mk_record(**over) -> M16CaseRecord:
    """Record tổng hợp DỰNG TAY (không qua pipeline) — để đo độ NHẠY của metric
    khi một outcome bất thường XẢY RA (gate hụt). Mặc định = product case sạch."""
    base = dict(
        case_id="fx-raw", group="unsupported", archetype="near_miss_gap",
        expected_family="graph_traversal", expected_initial_route=None, expected_final_route=None,
        raw_prescribed=None, canonical_prescribed=None, result_ownership="algorithmic",
        initial_route="generic.rule_scene", initial_family="generic_dual", reclassify_attempted=False,
        reclassify_result_route=None, final_route=None, final_family=None, selector_token_used=False,
        variant=None, gates=[], simulate_attempts=[], first_attempt_ok=None, semantic_ok=None,
        envelope_status=None, envelope_error_code=None, envelope_failure_category=None, source=None,
        budget_delta={"logical_calls": 0, "http_requests": 0, "retry_requests": 0, "transient_hits": 0},
        via_production_pipeline=True, infra_error=None, detail="",
    )
    base.update(over)
    return M16CaseRecord(**base)


# ── 5a. false-refusal injected → metric #8 bắt (numerator 1, taxonomy FALSE_REFUSAL) ──
def test_fault_false_refusal_bi_metric_8_bat(monkeypatch):
    item = EvalItem(
        "fx-false-refusal", "tìm phần tử lớn nhất", "specialized", "algorithm.find_max",
        m16=_exp(archetype=M16Archetype.EXPLICIT_POSITIVE, expected_family="single_pass_scan",
                 expected_initial_route="algorithm.find_max"),
    )
    # supported item NHƯNG script classify unsupported → refuse OAN
    script = CaseScript(_ana(ownership="provided"), [{"status": "unsupported", "simulation_id": None, "reason": "giả từ chối"}], [])
    r = _run_one(monkeypatch, item, script)
    m16 = {item.id: item.m16}

    assert r.envelope_status == "unsupported"  # bị từ chối oan
    assert MM.metric_false_refusal_rate([r], m16).numerator == 1
    assert "FALSE_REFUSAL" in MM.classify_failures(r, m16)


# ── 5b(i). leak injected NHƯNG gate production CHẶN → leak=0 NHỜ GATE ──
def test_fault_leak_bi_computation_gate_chan(monkeypatch):
    item = EvalItem(
        "fx-leak-gated", "tìm đường ngắn nhất có trọng số", "unsupported",
        m16=_exp(expected_gate="computation", algorithmic_request=True),
    )
    # classify→generic + analysis algorithmic (KHÔNG bypass gate) → computation gate CHẶN
    script = CaseScript(_ana(ownership="algorithmic"), [{"status": "ok", "simulation_id": "generic.rule_scene", "reason": None}], [])
    r = _run_one(monkeypatch, item, script)
    m16 = {item.id: item.m16}

    # bằng chứng leak=0 DO GATE: refused + computation gate fired
    assert r.envelope_status == "unsupported"
    assert r.final_route is None
    assert any(g.get("gate") == "computation" and g.get("fired") for g in r.gates)
    assert MM.metric_generic_fallback_leak_rate([r], m16).numerator == 0


# ── 5b(ii). record tổng hợp có leak THẬT → metric #12 BẮT (numerator 1) ──
def test_fault_leak_metric_12_nhay_khi_gate_hut(monkeypatch):
    """Chứng minh metric #12 NHẠY: nếu gate production HỤT (envelope ok generic
    cho đề algorithmic-unsupported) thì metric BẮT được — record dựng tay, KHÔNG
    qua pipeline (pipeline KHÔNG thể sinh outcome này, đó chính là điều cần đo)."""
    leaked = _mk_record(
        case_id="fx-leak-raw", final_route="generic.rule_scene", final_family="generic_dual",
        envelope_status="ok", source="composed",
        simulate_attempts=[{"n": 0, "ok": True, "error_code": None}], first_attempt_ok=True, semantic_ok=True,
    )
    m16 = {"fx-leak-raw": _exp(algorithmic_request=True)}

    leak = MM.metric_generic_fallback_leak_rate([leaked], m16)
    assert leak.numerator == 1 and leak.denominator == 1
    cats = MM.classify_failures(leaked, m16)
    assert "GENERIC_FALLBACK_LEAK" in cats
    assert "FALSE_POSITIVE_SIMULATION" in cats  # đề unsupported nhưng envelope ok


# ── 5c. transient separation — budget_delta giả tách đúng kênh + taxonomy TRANSIENT ──
def test_fault_transient_tach_kenh_retry(monkeypatch):
    # 1 semantic retry (2 simulate_attempt) + 2 transient HTTP retry (budget) — TÁCH BẠCH
    rec = _mk_record(
        case_id="fx-transient",
        simulate_attempts=[{"n": 0, "ok": False, "error_code": "structural_invalid"},
                           {"n": 1, "ok": True, "error_code": None}],
        first_attempt_ok=False,
        budget_delta={"logical_calls": 4, "http_requests": 6, "retry_requests": 2, "transient_hits": 1},
        envelope_status="ok", final_route="algorithm.bubble_sort", final_family="comparison_sort",
    )
    chans = MM.metric_retry_channels([rec])
    # KÊNH RIÊNG, không trộn: semantic (simulate retry) vs transient (HTTP retry)
    assert chans.semantic_retries_total == 1
    assert chans.transient_retries_total == 2
    assert chans.reclassify_count_total == 0
    # taxonomy gắn cờ TRANSIENT khi transient_hits > 0
    assert "TRANSIENT_PROVIDER_ERROR" in MM.classify_failures(rec)
    # record KHÔNG có transient → KHÔNG gắn cờ (đối chứng âm)
    clean = _mk_record(budget_delta={"logical_calls": 1, "http_requests": 1, "retry_requests": 0, "transient_hits": 0})
    assert "TRANSIENT_PROVIDER_ERROR" not in MM.classify_failures(clean)


# ── 6. call budget: analyze==1 (khóa 3: KHÔNG analyze lại), classify≤2
#      (1 + ≤1 reclassify), simulate≤3 (bound retry pipeline) — từng case ──
def test_call_budget_tung_case(monkeypatch):
    for it in M16_ITEMS:
        script = SCRIPTS[it.id]
        fake, counts = build_scripted_provider(script)
        monkeypatch.setattr(pipeline, "call_gemini", fake)
        asyncio.run(evaluate_item(it, "khoa-gia"))
        assert counts["analyze"] == 1, f"{it.id}: analyze={counts['analyze']}"
        assert counts["classify"] <= 2, f"{it.id}: classify={counts['classify']}"
        assert counts["simulate"] <= 3, f"{it.id}: simulate={counts['simulate']}"
        # case tới simulate → đúng bằng số attempt trong script (validator THẬT
        # hội tụ đúng chỗ script dự tính); gate chặn trước simulate → 0.
        if script.simulate_seq:
            assert counts["simulate"] == len(script.simulate_seq), (
                f"{it.id}: simulate={counts['simulate']} != {len(script.simulate_seq)}"
            )
