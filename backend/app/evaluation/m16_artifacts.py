# -*- coding: utf-8 -*-
"""M16 Task 6 (W6) — builder THUẦN cho 5 artifact máy-đọc (docs/evaluation/m16/),
nguồn yêu cầu: .superpowers/sdd/m16-task-6-brief.md (Phụ lục — kiến trúc +
schema). Mọi hàm ở đây trả dict/list JSON-serializable THUẦN, KHÔNG side-effect
file — `scripts/generate_m16_artifacts.py` (CLI) mới là nơi ghi file + bơm 2
field volatile (`git_commit`, `generated_at`); `tests/test_m16_artifacts.py`
gọi lại CHÍNH các hàm này để sync-lock so khớp artifact đã commit.

Tiền lệ kiến trúc: `scripts/generate_capability_descriptors.py` (M14 §C4) —
builder thuần tách khỏi CLI, sync-lock so khớp file JSON đã commit.

`run_offline_and_build_all()` chạy TOÀN BỘ pool m16 (50 case) qua production
`evaluate_item`/`run_pipeline` (bất biến #22) với provider scripted
(`m16_offline_scripts.SCRIPTS` + `build_scripted_provider` — Task 5, KHÔNG
đổi), monkeypatch THỦ CÔNG `pipeline.call_gemini` (gán attribute + khôi phục
trong `finally` — hàm này chạy được CẢ trong pytest (sync-lock test, guard
mạng conftest vẫn bảo vệ) LẪN ngoài pytest (CLI generator)).
"""

from __future__ import annotations

import asyncio
import dataclasses
from typing import Mapping, Sequence

from app.ai import pipeline
from app.evaluation import m16_metrics as MM
from app.evaluation.datasets.m16_catalog import M16_ITEMS, M16_REFERENCED_CASES
from app.evaluation.harness import evaluate_item
from app.evaluation.m16_metrics import AggregateResult, MetricValue
from app.evaluation.m16_offline_scripts import SCRIPTS, build_scripted_provider
from app.evaluation.m16_record import M16CaseRecord
from app.evaluation.m16_schema import M16Archetype, M16Expectation, frozen_dataset_fingerprint
from app.simulation.descriptor import FamilyId
from app.simulation.families import FAMILY_SELECTORS

# Token selector (bề mặt LLM của một family — KHÔNG BAO GIỜ là envelope id).
_SELECTOR_TOKENS: frozenset[str] = frozenset(sel.selector_token for sel in FAMILY_SELECTORS.values())

# PIN fingerprint DATASET 30 case — khoá ĐỘC LẬP thứ ba (đã có ở
# test_m16_schema.py::_FROZEN_FINGERPRINT_PIN và
# test_m16_offline_eval.py::_FROZEN_PIN — tiền lệ đã chốt trong module đó:
# "Sửa DATASET → CẢ HAI test đỏ"; artifact hard_correctness.frozen_fingerprint_ok
# là khoá thứ ba trên CÙNG một bất biến, không phải giá trị viết tay mới).
_FROZEN_PIN = "86e5a31db6d5a11c677dad95842e5ed6eaafc3b373afea651c49ef5258021dbf"


# ── 1. m16-case-matrix.json ──────────────────────────────────────────────
def build_case_matrix() -> dict:
    """Per case (thứ tự pool M16_ITEMS) + registry tham chiếu case pool cũ."""
    cases = []
    for it in M16_ITEMS:
        m16 = it.m16
        assert isinstance(m16, M16Expectation), f"{it.id}: thiếu m16 expectation"
        cases.append(
            {
                "case_id": it.id,
                "group": it.group,
                "archetype": m16.archetype.value,
                "expected_family": m16.expected_family,
                "curriculum_area": it.curriculum_area,
                "result_mode": it.result_mode,
                "complexity": it.complexity,
                "expected_initial_route": m16.expected_initial_route,
                "expected_final_route": it.expect_simulation_id,
                "expected_gate": m16.expected_gate,
                "expected_error_code": m16.expected_error_code,
                "analyze_mechanism_expected": m16.analyze_mechanism_expected,
                "algorithmic_request": m16.algorithmic_request,
                "recovery_route_exists": m16.recovery_route_exists,
                "live_eligible": m16.live_eligible,
                "tags": list(it.tags),
            }
        )
    return {"cases": cases, "referenced_cases": dict(M16_REFERENCED_CASES)}


# ── 2. m16-coverage-report.json ──────────────────────────────────────────
def build_coverage_report() -> dict:
    """ĐẾM từ pool thật (M16_ITEMS) — không hardcode giá trị số; "N/M" là
    chuỗi dựng từ số đếm thật (numerator/denominator đều dẫn xuất)."""
    items = M16_ITEMS

    targets = sorted({it.expect_simulation_id for it in items if it.group != "unsupported"})
    per_target: dict[str, dict] = {}
    for target in targets:
        subset = [it for it in items if it.group != "unsupported" and it.expect_simulation_id == target]
        explicit = sum(1 for it in subset if it.m16.archetype == M16Archetype.EXPLICIT_POSITIVE)
        paraphrase = sum(1 for it in subset if it.m16.archetype == M16Archetype.PARAPHRASE_POSITIVE)
        per_target[target] = {
            "explicit": explicit,
            "paraphrase": paraphrase,
            "total_positive": len(subset),
        }

    families = sorted(f.value for f in FamilyId)
    per_family: dict[str, dict] = {}
    for fam in families:
        valid_boundary = sum(
            1
            for it in items
            if it.m16.expected_family == fam and it.m16.archetype == M16Archetype.VALID_BOUNDARY
        )
        # near_miss = near_miss_gap ĐÚNG family + authority_control case-(a) khi
        # nó là case unsupported (đo cho CẢ hai lock — xem m16_catalog.py notes
        # case m16-ac-computation-leak / m16-task-4-brief.md Phụ lục B§3).
        near_miss = sum(
            1
            for it in items
            if it.m16.expected_family == fam
            and it.group == "unsupported"
            and it.m16.archetype in (M16Archetype.NEAR_MISS_GAP, M16Archetype.AUTHORITY_CONTROL)
        )
        positive = sum(1 for it in items if it.m16.expected_family == fam and it.group != "unsupported")
        per_family[fam] = {
            "valid_boundary": valid_boundary,
            "near_miss": near_miss,
            "positive": positive,
        }

    per_archetype: dict[str, int] = {}
    for it in items:
        key = it.m16.archetype.value
        per_archetype[key] = per_archetype.get(key, 0) + 1

    targets_with_both = sum(1 for t in per_target.values() if t["explicit"] >= 1 and t["paraphrase"] >= 1)
    families_with_vb = sum(1 for f in per_family.values() if f["valid_boundary"] >= 1)
    families_with_nm = sum(1 for f in per_family.values() if f["near_miss"] >= 1)
    live_eligible_count = sum(1 for it in items if it.m16.live_eligible)

    locks = {
        "targets_covered": f"{targets_with_both}/{len(targets)}",
        "families_boundary": f"{families_with_vb}/{len(families)}",
        "families_near_miss": f"{families_with_nm}/{len(families)}",
        "live_eligible_count": live_eligible_count,
        "total_cases": len(items),
    }

    return {
        "per_target": per_target,
        "per_family": per_family,
        "per_archetype": per_archetype,
        "locks": locks,
    }


# ── 3. m16-offline-results.json ──────────────────────────────────────────
def build_offline_results(records: Sequence[M16CaseRecord]) -> list[dict]:
    """List per case (thứ tự chạy == thứ tự pool) — asdict đầy đủ, KHÔNG lọc."""
    return [dataclasses.asdict(r) for r in records]


# ── 4. m16-metrics.json ──────────────────────────────────────────────────
# Final review B: band là nhãn CHẤT LƯỢNG — với metric "càng thấp càng tốt"
# (false_refusal/FP-sim/leak) giá trị 0.0 là lý tưởng nhưng quality_band thô
# trả WEAK, gây hiểu lầm cho người đọc artifact. Artifact khai `direction`
# tường minh và band tính trên điểm hiệu dụng (1 - value) cho nhóm đảo chiều;
# reclassification_rate là số chẩn đoán (không tốt/xấu) → band "N/A".
# `quality_band` trong m16_metrics GIỮ NGUYÊN (đúng công thức design §4).
_LOWER_IS_BETTER = frozenset({
    "false_refusal_rate",
    "false_positive_simulation_rate",
    "generic_fallback_leak_rate",
})
_DIAGNOSTIC = frozenset({"reclassification_rate"})


def _direction(name: str) -> str:
    if name in _LOWER_IS_BETTER:
        return "lower_is_better"
    if name in _DIAGNOSTIC:
        return "diagnostic"
    return "higher_is_better"


def _band(name: str, value: float | None) -> str:
    if value is None or name in _DIAGNOSTIC:
        return "N/A"
    if name in _LOWER_IS_BETTER:
        return MM.quality_band(1.0 - value)
    return MM.quality_band(value)


def _mv_dict(name: str, mv: MetricValue) -> dict:
    return {
        "numerator": mv.numerator,
        "denominator": mv.denominator,
        "value": mv.value,
        "direction": _direction(name),
        "band": _band(name, mv.value),
    }


def _frac(mv: MetricValue) -> str:
    return f"{mv.numerator}/{mv.denominator}"


def _has_selector_token_leak(agg: AggregateResult) -> bool:
    """Token selector KHÔNG BAO GIỜ là envelope id — quét confusion_matrix
    (cột = actual outcome, chứa final_route khi ok) — dẫn xuất từ `agg`, KHÔNG
    cần records riêng (giữ chữ ký `build_metrics_artifact(agg)` như brief)."""
    for row in agg.confusion_matrix.values():
        for col in row:
            if col in _SELECTOR_TOKENS:
                return True
    return False


def build_metrics_artifact(agg: AggregateResult) -> dict:
    micro = {name: _mv_dict(name, ma.micro) for name, ma in agg.metrics.items()}
    macro = {
        name: {
            "value": ma.macro,
            "direction": _direction(name),
            "band": _band(name, ma.macro),
            "excluded_families": ma.excluded_families,
        }
        for name, ma in agg.metrics.items()
    }
    per_family = {
        name: {fam: _mv_dict(name, mv) for fam, mv in ma.per_family.items()}
        for name, ma in agg.metrics.items()
    }

    hard_correctness = {
        "false_positive_simulation": _frac(agg.metrics["false_positive_simulation_rate"].micro),
        "generic_fallback_leak": _frac(agg.metrics["generic_fallback_leak_rate"].micro),
        "concrete_envelope_integrity": _frac(agg.metrics["concrete_envelope_integrity"].micro),
        "production_evaluation_parity": _frac(agg.metrics["production_evaluation_parity"].micro),
        "selector_token_in_envelope": _has_selector_token_leak(agg),
        "frozen_fingerprint_ok": frozen_dataset_fingerprint() == _FROZEN_PIN,
    }

    return {
        "micro": micro,
        "macro": macro,
        "per_family": per_family,
        "retry_channels": dataclasses.asdict(agg.retry_channels),
        "confusion_matrix": agg.confusion_matrix,
        "failure_distribution": agg.failure_distribution,
        "applicability_report": agg.applicability_report,
        "hard_correctness": hard_correctness,
    }


# ── 5. m16-failure-ledger.json ───────────────────────────────────────────
def _outcome_matches_expectation(record: M16CaseRecord) -> bool:
    """unsupported ↔ refused; supported ↔ ok + final_route đúng (cùng luật
    `test_expected_outcome_tung_case` trong test_m16_offline_eval.py)."""
    if record.group == "unsupported":
        return record.envelope_status == "unsupported"
    return record.envelope_status == "ok" and record.final_route == record.expected_final_route


# Mô tả 3 fault-injection THẬT trong tests/test_m16_offline_eval.py (§ FAULT
# INJECTION) — tên hàm test + metric bắt được VIẾT TỪ CODE THẬT, không bịa.
_INJECTED_PROOFS: tuple[dict, ...] = (
    {
        "proof": "false_refusal",
        "test_names": ["test_fault_false_refusal_bi_metric_8_bat"],
        "metric_caught": "metric_false_refusal_rate (#8)",
        "categories_caught": ["FALSE_REFUSAL"],
        "injected": True,
        "description": (
            "Case supported (item.m16 explicit_positive) bị script classify trả "
            "unsupported giả ('từ chối oan') — metric_false_refusal_rate bắt "
            "numerator=1/denominator=1; classify_failures gắn FALSE_REFUSAL."
        ),
    },
    {
        "proof": "generic_fallback_leak",
        "test_names": [
            "test_fault_leak_bi_computation_gate_chan",
            "test_fault_leak_metric_12_nhay_khi_gate_hut",
        ],
        "metric_caught": "metric_generic_fallback_leak_rate (#12)",
        "categories_caught": ["GENERIC_FALLBACK_LEAK", "FALSE_POSITIVE_SIMULATION"],
        "injected": True,
        "description": (
            "Nhánh (i): item unsupported-algorithmic script classify→generic.rule_scene "
            "+ analysis result_ownership=algorithmic — computation gate PRODUCTION THẬT "
            "chặn (fired), record bị refused → leak numerator=0 NHỜ GATE, không phải "
            "vacuous (assert gate 'computation' fired). Nhánh (ii): record tổng hợp DỰNG "
            "TAY (không qua pipeline, mô phỏng gate hụt) có envelope ok generic.rule_scene "
            "cho case unsupported-algorithmic → metric_generic_fallback_leak_rate bắt "
            "numerator=1, chứng minh metric NHẠY khi outcome bất thường thật sự xảy ra."
        ),
    },
    {
        "proof": "transient_provider_error",
        "test_names": ["test_fault_transient_tach_kenh_retry"],
        "metric_caught": "metric_retry_channels (#15) + classify_failures",
        "categories_caught": ["TRANSIENT_PROVIDER_ERROR"],
        "injected": True,
        "description": (
            "budget_delta giả {'retry_requests':2,'transient_hits':1} trên record tổng "
            "hợp (2 simulate_attempt = 1 semantic retry) — metric_retry_channels tách "
            "ĐÚNG hai kênh (semantic_retries_total=1, transient_retries_total=2, không "
            "trộn); classify_failures gắn cờ TRANSIENT_PROVIDER_ERROR khi transient_hits>0, "
            "KHÔNG gắn trên record sạch (đối chứng âm cùng test)."
        ),
    },
)


def build_failure_ledger(
    records: Sequence[M16CaseRecord], m16_by_case: Mapping[str, M16Expectation] | None
) -> dict:
    cases = []
    for r in records:
        categories = MM.classify_failures(r, m16_by_case)
        if not categories:
            continue
        cases.append(
            {
                "case_id": r.case_id,
                "categories": categories,
                "outcome_matches_expectation": _outcome_matches_expectation(r),
                "injected": False,
            }
        )
    return {"cases": cases, "injected_proofs": [dict(p) for p in _INJECTED_PROOFS]}


# ── chạy TOÀN pool trong-process (TÁI DÙNG Task 5: SCRIPTS + build_scripted_provider) ──
def _m16_by_case() -> dict[str, M16Expectation]:
    return {it.id: it.m16 for it in M16_ITEMS if it.m16 is not None}


def _run_pool_inprocess() -> list[M16CaseRecord]:
    """Monkeypatch THỦ CÔNG `pipeline.call_gemini` (gán attribute + khôi phục
    trong `finally`) — chạy được cả trong pytest (guard mạng conftest vẫn bảo
    vệ) lẫn ngoài pytest (CLI generator, brief Phụ lục dòng 23–24)."""
    records: list[M16CaseRecord] = []
    original = pipeline.call_gemini
    try:
        for it in M16_ITEMS:
            assert it.id in SCRIPTS, f"thiếu kịch bản offline cho case {it.id}"
            fake, counts = build_scripted_provider(SCRIPTS[it.id])
            pipeline.call_gemini = fake
            sink: list = []
            asyncio.run(evaluate_item(it, "khoa-gia", record_sink=sink))
            assert counts["analyze"] >= 1, (
                f"{it.id}: provider scripted KHÔNG được gọi — call thật có thể đã lọt qua"
            )
            assert len(sink) == 1, f"{it.id}: evaluate_item không append đúng 1 record"
            records.append(sink[0])
    finally:
        pipeline.call_gemini = original
    return records


def run_offline_and_build_all() -> dict[str, object]:
    """Chạy toàn pool m16 (50 case) qua production pipeline (bất biến #22) rồi
    build cả 5 artifact `data` — key khớp tên file (không đuôi .json/tiền tố):
    case_matrix / coverage_report / offline_results / metrics / failure_ledger."""
    records = _run_pool_inprocess()
    m16_by_case = _m16_by_case()
    agg = MM.aggregate(records, "offline", m16_by_case)
    return {
        "case_matrix": build_case_matrix(),
        "coverage_report": build_coverage_report(),
        "offline_results": build_offline_results(records),
        "metrics": build_metrics_artifact(agg),
        "failure_ledger": build_failure_ledger(records, m16_by_case),
    }


__all__ = [
    "build_case_matrix",
    "build_coverage_report",
    "build_offline_results",
    "build_metrics_artifact",
    "build_failure_ledger",
    "run_offline_and_build_all",
]
